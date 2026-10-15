# Statements (commands) reference

Every statement the engine knows, with syntax, argument types and counts, behavior, edge cases, version notes and Girl Life usage. Functions (expressions that return values) and system variables are in [built-in-api-reference.md](built-in-api-reference.md). Flow statements (`IF`, `LOOP`, `JUMP`, `EXIT`, `GOTO`, `GOSUB`, `DYNAMIC`) are explained in depth in [control-flow.md](control-flow.md) and summarized here.

**Where the facts come from.** Argument counts and types come from the statement table in `engine: qsp/statements.c:103` (`qspInitStats`). Each `qspAddStatement` call gives the minimum and maximum argument count and the type each argument is converted to before the handler runs. A failed conversion raises "Type mismatch!". A wrong count raises "Incorrect arguments count!". Girl Life counts are statement occurrences in `locations/*.qsrc` at commit `83b164f`, outside comments and strings (method in [research-scope-and-methodology.md](../research-scope-and-methodology.md)).

**Argument syntax.** Statement arguments are separated by commas and may be wrapped in parentheses: `addobj 'Knife', 'img/knife.png'` and `addobj('Knife', 'img/knife.png')` are equivalent (grammar `statementWithArgs`). Names are case-insensitive. Statement keywords must be followed by a delimiter (`IsIsolated` in the table), except `!` and `:`.

## Output to the main description window

| Statement | Syntax | Args | Behavior | Girl Life |
|---|---|---|---|---|
| implicit | `[expr]` | 1, any | Appends the value and a line break to the main window. Skipped when the value is undefined, for example a `func` call that set no result (`statements.c:940`) | most text output |
| `*PL` | `*pl [text]` | 0-1, string | Appends text, then a line break. With no argument, only the line break | 759 |
| `*P` | `*p text` | 1, string | Appends text, no line break. The argument is required | 1,435 |
| `*NL` | `*nl [text]` | 0-1, string | Appends a line break, then the text | 13,722 |
| `*CLEAR`, `*CLR` | `*clr` | 0 | Clears the main window | 28,111 |

- 5.7 difference: the implicit statement printed an empty line for a function without a result. 5.8+ prints nothing (blog 2026-01-01; wasm test "implicit output is not working with functions that does not return").
- Text is buffered and shown when the event ends, except that `WAIT`, `MSG`, `INPUT` and `MENU` make the player refresh first (docs, `WAIT`).
- Girl Life's typical screen start is `*clr & cla` (clear text and actions), then implicit string output.

## Output to the additional description (stats) window

| Statement | Syntax | Args | Behavior | Girl Life |
|---|---|---|---|---|
| `PL` | `pl [text]` | 0-1, string | Appends text and a line break | 21 |
| `P` | `p text` | 1, string | Appends text | 19 |
| `NL` | `nl [text]` | 0-1, string | Line break, then text | 34 |
| `CLEAR`, `CLR` | `clr` | 0 | Clears the stats window | 53 |

Girl Life renders its status panel through `stat` and `stat_display`, and its notification ticker in `counter.qsrc` uses `clr & pl '<<$stat_msg>>'`.

## Clearing and windows

| Statement | Syntax | Args | Behavior | Girl Life |
|---|---|---|---|---|
| `CLA` | `cla` | 0 | Removes all actions | 33,768 |
| `CLS` | `cls` | 0 | Clears main and stats windows, the input line and all actions. Objects stay (`statements.c:1010-1022`) | 417 |
| `CMDCLEAR`, `CMDCLR` | `cmdclear` | 0 | Clears the input line | 2 |
| `SHOWACTS` | `showacts n` | 1, bool | Shows (non-zero) or hides (zero) the actions pane | 2 |
| `SHOWOBJS` | `showobjs n` | 1, bool | Same for the objects pane | 7 |
| `SHOWSTAT` | `showstat n` | 1, bool | Same for the stats pane | 7 |
| `SHOWINPUT` | `showinput n` | 1, bool | Same for the input line | 5 |
| `REFINT` | `refint` | 0 | Asks the player to redraw now, including color and font variables | 0 |

Girl Life's `start` location hides stats, objects and input, then shows actions (`girl-life: locations/start.qsrc:9-19`). `loadg` re-shows objects for debug mode with `showobjs max(1 - debug_warning_closed, cfg_vars['debug'])`.

## Actions

### ACT

**Syntax.**

```qsp
act 'name', 'image': stmt & stmt
act 'name', 'image':
    ...
end
```

**Args.** 1-2 strings: name, optional image path.

**Behavior** (`engine: qsp/actions.c:69`, `qspAddAction`):
- Adds an action with that name to the list. The code is stored by reference and runs when clicked.
- If an action with the same name exists, comparing case-insensitively, the new one is ignored. The docs suggest adding invisible HTML to make names unique.
- At most 50 actions (`QSP_MAXACTIONS`, also 50 in 5.7). The 51st raises "Can't add action!".
- An empty or blank image argument means no image.
- The name is evaluated when `act` runs; `<<...>>` inside it is expanded then.
- The action remembers the location and base-action index it came from, which are used in error reports.
- Clicking runs the code with no locals from the creating location, in a new scope ([control-flow.md](control-flow.md)).
- A single-line `act` must have code after the colon ("Code not found!").

**Girl Life.** 63,572 `act` statements. Common form: `act 'Continue': gt 'loc', 'arg'`. GLSS injects actions after a location's code runs by testing `instr($curacts, 'Go to first period')`.

### DELACT

`delact 'name'`, 1 string. Removes the action with that name, compared case-insensitively. No error if absent. Deprecated form `del act`. Girl Life: 24 uses, for example the sample mod replacing an `Exit the room` action (`isample_mod/locations/mod_isample.qsrc`).

## Objects (inventory)

| Statement | Syntax | Args (types) | Behavior |
|---|---|---|---|
| `ADDOBJ` | `addobj name[, image[, position]]` | 1-3 (string, string, number) | Inserts at 1-based `position` or at the end; positions out of range are clamped. Then calls the `$ONOBJADD` handlers with `$ARGS[0]` = name, `$ARGS[1]` = image (`objects.c:265`). Same names may repeat. Max 1,000 objects |
| `DELOBJ` | `delobj name[, count]` | 1-2 (string, number) | Removes up to `count` (default 1) objects with that name, topmost first, compared case-insensitively. Then calls `$ONOBJDEL` once per removed object (`objects.c:213`, `:448`). The count argument is not in the docs' DELOBJ chapter; the blog lists it as new |
| `KILLOBJ` | `killobj [position]` | 0-1 (number) | Removes the object at 1-based `position`, or all objects. Calls `$ONOBJDEL` for each removed object, after the removal |
| `MODOBJ` (5.9.4) | `modobj name, title[, image]` | 2-3 strings | Changes the displayed title (and image if given) of every object with that name. `$SELOBJ` still returns the original name. Alias `mod obj` |
| `RESETOBJ` (5.9.4) | `resetobj [name]` | 0-1 string | Restores the original title and image of one name, or of all objects |
| `UNSELECT`, `UNSEL` | `unsel` | 0 | Clears the selected object. Needed to re-trigger `$ONOBJSEL` on the same object, because the handler only runs when a different object is selected (`default_control.c`, `QSPSetSelObjectIndex`) |
| `KILLALL` | `killall` | 0 | Clears all variables, then all objects (`statements.c:1025`). The object handlers are not called, because `$ONOBJDEL` was just cleared |

Deprecated forms `add obj` and `del obj` still parse. Girl Life barely uses the object pane for gameplay (22 `addobj` in one file, `obj_din.qsrc`, which builds the debug panel; `onobjsel.qsrc` handles its clicks and ends with `unselect`).

## Variables and arrays

| Statement | Syntax | Args | Behavior |
|---|---|---|---|
| assignment | `name[idx] op value` | | `op` is `=`, `+=`, `-=`, `*=`, `/=`. Details in [variables-and-data-types.md](variables-and-data-types.md) |
| `SET`, `LET` | `set name = value` | | Same as plain assignment; kept for readability. The docs call `LET` deprecated |
| multiple assignment | `a, $b, %c = 1, 'x', [2]` | | Values are a tuple unpacked into the targets. Extra targets get empty values. When there are more values than targets, the last target receives a tuple of the remaining values (`variables.c:1004`). A number target then raises "Type mismatch!" (the docs' `age, weight, material = 27, 94, 'steel', 'biorobot'` example). A string target receives the tuple's text form, because tuple-to-string conversion is allowed (`variant.c:14`); this case is inferred from the conversion table, not documented. Swap works: `x, y = y, x`. 5.8.0+ |
| `LOCAL` | `local a, $b[, ...] [= values]` | | Declares names in the current scope (5.8.0+). Without values they start empty. The value expression is evaluated before the locals are created, so `local x = x` copies the outer `x` (`variables.c:1092`) |
| `KILLVAR` | `killvar [name[, index]]` | 0-2 (varref, any) | No args: clears variables. One arg: empties the array. Two: removes one element and shifts later ones down. Index may be a number, string (5.8+) or tuple (5.8+) |
| `COPYARR` | `copyarr dest, src[, start[, count]]` | 2-4 (varref, varref, number, number) | Replaces `dest` with a copy of `src` from `start` (default 0) for `count` elements (default all), including string keys that fall in that range. Copying an array onto itself does nothing |
| `SORTARR` (5.9.0) | `sortarr name[, desc]` | 1-2 (varref, bool) | Sorts values ascending, or descending when the second argument is non-zero. Mixed types raise "Type mismatch!". String keys are remapped to follow their values |
| `SETVAR` (5.9.1) | `setvar name, value[, index]` | 2-3 | Assigns to a variable whose name is computed at run time; the prefix in `name` decides the type |
| `UNPACKARR` (5.9.1) | `unpackarr name, %tuple[, start[, count]]` | 2-4 (varref, tuple, number, number) | Replaces the array with tuple items |
| `SCANSTR` (5.9.0) | `scanstr name, text, regex[, group]` | 3-4 (varref, string, string, number) | Replaces the array with every non-overlapping match (or capture group) of `regex` in `text`. Empty matches end the scan |

**KILLVAR version notes.**
- `killvar` without arguments clears every variable in 5.9.5 (wasm test "local variables get removed on killvar" expects globals cleared too) and only the global scope in master (commit `24dd877`, 2026-10-09; `variables.c:1199`).
- `killvar 'name'` affects the variable that lookup finds first, which can be a local that shadows a global.
- In 5.7, `killvar 'name'` leaves the name occupying its slot ([variables-and-data-types.md](variables-and-data-types.md), section 5).
- The name argument is a string: `killvar 'x'`, not `killvar x`. `killvar $name` passes the value of `$name` as the variable name.

**Girl Life.** 7,476 `killvar` statements, mostly freeing temporaries at the end of a handler. 44 `copyarr`, used to snapshot `ARGS` (`copyarr 'modARGS', 'ARGS'`, `girl-life: locations/LOCA.qsrc:27`).

## Flow (summary)

| Statement | Syntax | Args | Notes |
|---|---|---|---|
| `IF` / `ELSEIF` / `ELSE` / `END` | see control-flow | 1 bool | IF branches are local scopes |
| `LOOP ... WHILE ... STEP` | `loop [init] while cond [step s]:` | | 5.8.0+ |
| `JUMP` | `jump 'label'` | 1 string | Case-insensitive, current code block only |
| `EXIT` | `exit` | 0 | Ends the current code block |
| `GOTO`, `GT` | `gt 'loc'[, args...]` | 1-20 | Clears main text and actions; stops all current code |
| `XGOTO`, `XGT` | `xgt 'loc'[, args...]` | 1-20 | Keeps main text |
| `GOSUB`, `GS` | `gs 'loc'[, args...]` | 1-20 | Runs a location and returns |
| `@@name` | `@@name args` | | 5.8.0+ shorthand for `GOSUB` |
| `DYNAMIC` | `dynamic code[, args...]` | 1-20 (code, any) | Runs text as code |

Girl Life: 92,919 `gs`, 36,982 `gt`, 1,995 `xgt`, 3,969 `exit`, 1,258 `jump`, 1,111 `dynamic`.

## Dialogs and menus

### MSG

`msg text`, 1 string. Shows a modal message. Execution pauses until the player closes it (wasm test "msg should stop execution flow"). 453 uses in Girl Life, mostly error notices and debug output.

### MENU

**Syntax.** `menu 'name'[, start[, count]]`. Args 1-3 (varref, number, number).

**Behavior** (`engine: qsp/menu.c:37`, `qspStatementShowMenu`):
- Reads items from the array `name` beginning at element `start` (default 0), stopping after `count` items (default 100, the maximum) or at the first empty item.
- Item forms:
  - tuple `[title, location, image]` (5.9.0+);
  - string `'title:location:image'` or `'title:location'`. The engine splits at the last colon, then at the colon before it, so titles may contain colons.
  - A string item with no colon raises "Token [:] not found!".
  - `'-:-'` or `['-', '-']` is a separator in 5.8+; in 5.7 it is an ordinary item named `-` (`legacy: tests/engine/menu.qspt:43`).
- After the player picks an item, the item's location is run like `GOSUB` with `ARGS[0]` set to the 1-based position.
- The `start` and `count` arguments are not in the docs.

**Docs example.**

```qsp
%stone[0] = ['Take stone', 'takestone']
%stone[1] = ['Throw stone', 'throwstone']
menu '%stone'
```

Girl Life uses no `MENU` statements.

### Input dialog

Input is a function (`$INPUT`); see [built-in-api-reference.md](built-in-api-reference.md).

## Graphics, sound, timing

| Statement | Syntax | Args | Behavior | Girl Life |
|---|---|---|---|---|
| `VIEW` | `view [path]` | 0-1 string | Shows an image in the preview window (classic) or as a layer (qSpider). Empty or missing path closes it (`statements.c`, `qspStatementView`) | 21 |
| `PLAY` | `play path[, volume]` | 1-2 (string, number) | Volume is clamped to 0-100, default 100. The engine keeps a playlist of up to 500 entries that is saved with the game and replayed on load (`playlist.c`). Replaying an already playing file is up to the player; the docs say the classic player only changes the volume | 444 |
| `CLOSE` | `close [path]` | 0-1 string | Stops a file, but only if the engine's playlist contains it. Without an argument stops everything | 492 |
| `CLOSE ALL` | `close all` | 0 | Stops everything. Not the same keyword as `close` followed by a variable named `all`: the two-word keyword is matched first | |
| `WAIT` | `wait ms` | 1 number | Pauses for `ms` (negative counts as 0). The player redraws first | 141 |
| `SETTIMER` | `settimer ms` | 1 number | Sets the counter interval (default 500). Negative counts as 0. In the classic player, 0 stops the timer (`qspgui: qspgui/callbacks_gui.cpp:75-83`) | 0 |

Girl Life's counter location keeps a music track looping with `PLAY $track_loop, volume` every tick (`girl-life: locations/counter.qsrc:23`).

## Game files and state

| Statement | Syntax | Args | Behavior |
|---|---|---|---|
| `INCLIB` (5.8.0; `ADDQST`/`ADDLIB` earlier) | `inclib 'file.qsp'` | 1 string | Loads another game file and adds its locations, skipping names that already exist. The same path twice is ignored. Max 100 files (`game.c:98`). Included files are saved with the game and reloaded on load |
| `FREELIB` (5.8.0; `KILLQST`/`DELLIB` earlier) | `freelib` | 0 | Removes every included location |
| `OPENQST` | `openqst 'file.qsp'` | 1 string | Replaces the game with another file and starts its first location. Variables, objects, stats text, input and sound are kept |
| `OPENGAME` | `opengame [path]` | 0-1 string | Loads a save (player shows a dialog without a path) |
| `SAVEGAME` | `savegame [path]` | 0-1 string | Saves the state (dialog without a path). Calls `$ONGSAVE` handlers first |

The legacy 5.7 source registers only `ADDQST` and `KILLQST` (`legacy: src/statements.c`); `ADDLIB` and `DELLIB`, which the docs list as old names, are not in it. Girl Life's mod loader branches on `$qspver < '5.8.0'` to call `addqst`/`killqst` or `inclib`/`freelib` (`girl-life: locations/mod_system.qsrc:143-147`).

Save format, `DEBUG`, and loading rules are in [input-output-and-persistence.md](input-output-and-persistence.md).

## EXEC (undocumented)

**Syntax.** `exec 'text'`. 1 string.

**Behavior.** Passes the text to the player through the `QSP_CALL_SYSTEM` callback (`engine: qsp/statements.c:1122`). The engine does nothing else. It exists in 5.7 as well.

| Player | What happens |
|---|---|
| Classic (`qspgui`) | No `SYSTEM` callback is registered (`callbacks_gui.cpp:46-62`), so nothing happens |
| qSpider | The wasm engine emits `system_cmd`; qSpider understands `action:`, `event:`, `change_theme:`, `update_region:`, `scroll_region:` and others (`qspider: libs/game-state/src/qspider-commands.ts`). qSpider's docs show the command wrapped in a `qspider` library location (`@qspider_event('test_event')`) |

Do not confuse the statement with `EXEC:` in hyperlinks, which runs QSP code ([input-output-and-persistence.md](input-output-and-persistence.md)). Girl Life does not use the statement.

# Girl Life: scripting patterns

The conventions Girl Life uses to structure about 916,000 lines of QSP that must run on both 5.7 and 5.8+ engines. Each pattern lists where it appears, what it does, why it exists, and which QSP features it depends on. Counts are from `locations/` at commit `83b164f`; the scripts that produced them are described in [research-scope-and-methodology.md](../research-scope-and-methodology.md). Short annotated excerpts are in [code-examples.md](code-examples.md).

## 1. Location as a module of named handlers

**What.** A location's code is a sequence of `if $ARGS[0] = 'name':` blocks, each ending in `exit`:

```qsp
if $ARGS[0] = 'sqrt':
	result = func('math', 'int_sqrt', ARGS[1])
	exit
end
```

(`locations/shortgs.qsrc:100-103`)

**Scale.** 16,929 string handlers in 1,105 of 1,429 files. 113 files have a default handler `if $ARGS[0] = '':` for a plain `gt 'loc'`.

**How it is called.**

| Call | Meaning |
|---|---|
| `gt 'loc', 'handler', args...` | Show a screen; the handler builds it |
| `gs 'loc', 'handler', args...` | Run a procedure |
| `x = func('loc', 'handler', args...)` | Call a numeric function |
| `$s = $func('loc', 'handler', args...)` | Call a string function (the `$` is cosmetic, see [expressions-and-operators.md](../official-documentation/expressions-and-operators.md)) |

Usage: 92,919 `gs`, 36,982 `gt`, 12,855 `$func(` and 5,010 unprefixed `func(`.

**Why.**
- QSP has no functions, only locations, so this is how a location becomes a library.
- `exit` stops the location after one handler, so later handlers are not evaluated.
- `ARGS` is fresh per call on every engine, which gives each handler private parameters.

**QSP features used.** `ARGS` per call scope; `RESULT` for return values; `EXIT`; string comparison (case-sensitive, so handler names must match exactly).

**Hazards.**
- A handler without `exit` falls through into the next `if`. Usually harmless, because the next condition is false, but it costs time.
- A misspelled handler name does nothing silently. `tools/callvalidator.py` checks that every `gt`/`gs` target location and handler exists.
- GLSS follows the same structure (`glss/locations/mod_glss_functions.qsrc`).

## 2. Screen construction

**What.** Handlers that show a screen follow the template in `locations/templates/location_template.qsrc`:

```qsp
if $ARGS[0] = '':
	*clr & cla
	menu_off = 0
	gs 'core_library', 'setloc', 'location_template', ''
	gs 'stat'

	'<center><img <<$set_imgh>> src="{INSERT IMAGE}"></center>'
	'text'

	act 'Return': minut += 1 & gt '{INSERT HUB LOC HERE}'
end
```

**Pieces.**
- **Clearing.** `*clr & cla` (28,111 and 33,768 uses) clears text and actions. `GOTO` already clears both, so this matters when the handler was reached by `gs`, or to redraw within one location.
- **Location state for menus.**
  - `menu_off` (4,912 references) disables the side menu links during events.
  - `setloc` (1,109 references, `core_library.qsrc:10-38`) records `$loc`, `$loc_arg`, `$menu_loc`, `$menu_arg` and the region. `act 'Continue': gt $loc, $loc_arg` returns to the screen later.
- **Status panel.** `gs 'stat'` recalculates stats and runs `gs 'time'` (`stat.qsrc:592`).
- **Output.**
  - Text uses the implicit statement with string literals.
  - Images use `<img <<$set_imgh>> src="...">`.
  - Headings use `$func('wrap', 'header center b', 'Title')` (`wrap.qsrc`).
- **Choices.**
  - Actions with time cost: `act 'Go (0:05)': minut += 5 & gt '...'`.
  - Inline `exec:` links in text.

## 3. Time as a variable plus a normalizer

**What.** Code adds minutes directly (`minut += 10`, the most assigned name at 12,336 assignments) and later calls `gs 'time'` or `gs 'stat'`. `time.qsrc` carries minutes into hours and hours into days, running `hourly_events` for each hour and `cikl` for each day (`time.qsrc:5-37`).

**Why.** QSP has no clock that advances with play. Normalizing lazily lets any code add time cheaply.

**Hazard.** Several hour or day boundaries crossed at once run the hourly and daily logic repeatedly in one event. A large jump (GLSS's one-click school day adds up to six hours) runs `hourly_events` once per hour crossed.

## 4. Global temporaries with cleanup instead of locals

**What.** Working variables are globals with handler-specific names, freed at the end:

```qsp
if $ARGS[0] = 'dow':
	Y_dow = ARGS[1]
	...
	killvar 'D_dow'
	killvar 'M_dow'
	killvar 'Y_dow'
	exit
end
```

(`locations/shortgs.qsrc:117-135`). Newer code groups temporaries in one array per module so a single `killvar` cleans up: `temp_arrayVars['backup']`, `temp_moneyVars['amount']`, then `killvar 'temp_arrayVars'` (127 such cleanups).

**Scale.** 7,476 `killvar` statements.

**Why.** `LOCAL` does not exist in 5.7.

**Hazards.**
- **Re-entrancy.** If a handler calls itself, directly or through other locations, the inner call overwrites the outer one's temporaries.
- **Early exits.** An `exit` or `gt` before the `killvar` lines leaves temporaries behind, and they are saved with the game.
- **5.7 slot use.** On 5.7, `killvar 'x'` does not free the variable's slot in the 12,800-slot table ([variables-and-data-types.md](../official-documentation/variables-and-data-types.md)). Every distinct temporary name ever written occupies a slot until a full reset.

`qsp_audit` has rules for this (`temp-var-unkilled`, `should-be-temp`).

**Copy-paste slip.** In `shortgs` handler `dow`, the shortcut test reads the `doy` handler's variables (`if Y_doy = year and M_doy = month and D_doy = day:`, `shortgs.qsrc:125`). Those are killed at the end of `doy`, so the test is always false, and the handler always takes the slower path that gives the same answer.

## 5. Loops with labels

**What.**

```qsp
mod_i = 0
:mod_exec
	...
	mod_i += 1
if mod_i < arrsize('$mod_name'): jump 'mod_exec'
killvar 'mod_i'
```

(`locations/mod_system.qsrc:84-95`).

**Scale.** 1,258 `jump` statements in 246 files; zero `LOOP` statements.

**Why.** `LOOP` is 5.8+.

**Details.**
- Label names must be unique within a location's code block, because the first match wins. Girl Life prefixes labels with the handler or module name (`:coupled_sort_inner_start`, `:time_time_loop`).
- Jumping into another handler's IF body works and is used deliberately: `time_cheat_fix` jumps to `:time_time_loop` inside the default handler (`time.qsrc:14, 40-49`).

## 6. Return values that work on both engines

**What.**
- **Normalize booleans.** `result = iif(money >= ARGS[1], 1, 0)` (`money.qsrc:293`; 111 `iif(..., 1, 0)` in total), so callers can test `= 1` on 5.7, where a comparison yields -1. The money API documents `if func('money', 'can_afford', item_cost, 'both') = 1:`, used 94 times; GLSS does the same.
- **Raw comparisons.** 164 `result = (...)` assignments return a comparison directly. Callers of those must test truthiness (`if func(...):`) rather than `= 1`. This is inferred from the two conventions; no failing caller was identified.
- **Truth constants.** `_TRUE = (0 ! 1)` and `_FALSE = (0 = 1)` in the test framework.

## 7. Metaprogramming with names built at run time

**Computed location names guarded by `loc()`:**

```qsp
if loc('$attributes_<<$ARGS[0]>>'): gs '$attributes_<<$ARGS[0]>>', ARGS[1]
```

(`clothing_attributes.qsrc:173`). The mod system does the same for `mod_<name>`, `mod_<name>_setup` and `_saveupdater`.

**Computed variable names through `dynamic`/`dyneval`** (1,111 and 244 uses). The array library writes and reads arrays whose names arrive as strings:

```qsp
$test = '<<$ARGS[1]>>[''<<$ARGS[2]>>'']'
...
temp_arrayVars['backup'] = dyneval('result = <<$test>>')
dynamic '<<$test>> = -2147483647'
```

(`array.qsrc:12-38`). 5.9.1's `SETVAR` and `ARRITEM` replace this, but are not available on 5.7.

**Hazard.** `dynamic` with text built from `<<...>>` is re-preprocessed every time, and quoting errors only show up at run time.

## 8. Version branches

```qsp
if $qspver < '5.8.0':
	addqst 'mod/<<$ARGS[1]>>.qsp'
else
	inclib 'mod/<<$ARGS[1]>>.qsp'
end
```

(`mod_system.qsrc:143-147`). This works because each engine only parses the statement in the branch it runs, which is lazy parsing at execution time. Both checks compare version strings as text, which is right for 5.x.y with single digits.

## 9. Comments

| Form | Meaning | Example |
|---|---|---|
| `!! text` | Line comment (the second `!` is part of the text) | throughout |
| `!{ ... !}` or `!!{ ... !!}` | Block comment: the `{` opens a block that spans lines until `}` | `LOCA.qsrc:11-25`, every `_attributes_` file header |
| `''` inside comments | Keeps apostrophes balanced so they do not open a string | `shortgs.qsrc:461`, `money.qsrc` header |
| Box-drawing banners | Section headers | `stat.qsrc`, `templates/comment_template.qsrc` |

A simulation of the engine's line joining over every location found 461 comments that span several lines. All end where the author intended, but 13 of them continue past a line end because a quote is still open there and close correctly only because a later quote pairs with it ([implementation-observations.md](implementation-observations.md)).

## 10. Links in text

```qsp
'There is a shower, toilet, sink, and a <a href="exec:gt ''mirror'',''start''">mirror</a> where you can ' + iif(pcs_hairbsh = 0, '<a href="exec:gt ''mirror'',''brush''">brush</a>', 'brush') + ' your hair.'
```

(`core_library.qsrc:85`). Links are built in strings with doubled apostrophes; `iif` decides between a link and plain text. Girl Life has 3,801 `exec:` links.

## 11. Nested actions

An action can create the next step's actions:

```qsp
act 'Take a shower':
	*clr & cla
	...
	act 'Continue' : gt $loc, $loc_arg
end
```

(`core_library.qsrc:89-101`). The inner `act` runs only when the outer action is clicked. `gt $loc, $loc_arg` returns to whatever screen `setloc` recorded.

## 12. Keyed state arrays

State lives in arrays keyed by strings. Of the 8,489 names assigned by literal name, 695 are assigned with literal string keys and 400 with keys taken from a string variable. Examples:
- quest state: `katjaQW['QWstage']`;
- NPC data keyed by NPC id: `npc_rel['A69']`, `$npc_lovername[$npcID]`;
- settings: `cfg_vars['imgh']`, `cheatVars['skill_gain']`;
- theme colors: `theme_hex['accent']`, 4,491 assignments.

Keys are case-insensitive. On 5.7, a number and a string can share a key; Girl Life mostly keeps types separate per key (see [implementation-observations.md](implementation-observations.md)).

## 13. Deprecation by forwarding

Old handlers stay and forward to new modules: `shortgs` `round_divide` calls `func('math', 'int_divide', ...)`, `rand_pick` calls `random`, `parse_string` calls `string` (`shortgs.qsrc:439-506`, marked "Depracated"). Old saves and mods keep working.

## 14. Save migrations

Each version step is a guarded block in `saveupdater.qsrc` (6,590 lines):

```qsp
if temp_current_save_version < 00080403:
	if meynoldQW = 1 or meynoldQW = 2:
		katjaQW['QWstage'] = meynoldQW
		killvar 'meynoldQW'
	end
```

(`saveupdater.qsrc:43-50`). The version is a number built from four parts (`((100*major + minor)*100 + revision)*100 + patch`, `saveg.qsrc:6`). Leading zeros in the literals are just digits.

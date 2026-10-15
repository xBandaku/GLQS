# Built-in functions and system variables

Reference for every function and system variable. Argument counts and types come from the operation table in `engine: qsp/mathops.c:167` (`qspInitMath`); the "Args" column lists the type each argument is converted to (num = number, str = string, any = no conversion, name = variable name string). Statements are in [functions-and-commands.md](functions-and-commands.md).

Calling rules that apply to every function (details in [expressions-and-operators.md](expressions-and-operators.md)):
- Functions with two or more required arguments need parentheses.
- The `$`/`%` prefix on a function name is cosmetic; it does not convert the result.
- All arguments are evaluated before the function runs, except for `IIF` (5.8+).

## 1. String functions

| Function | Args | Returns | Behavior and edge cases | Girl Life |
|---|---|---|---|---|
| `LEN(v)` | 1 any | num | String length in code units. A number gives the length of its decimal text, a tuple gives its item count, undefined gives 0 (`mathops.c:1314`) | 95 |
| `$MID(s, start[, len])` | 2-3 (str, num, num) | str | 1-based. `start` below 1 counts as 1. `start` past the end gives `''`. Negative `len` gives `''`. Without `len`, to the end (`mathops.c:1418`) | 599 |
| `INSTR(s, sub[, start])` | 2-3 (str, str, num) | num | 1-based position of `sub` at or after `start` (default 1), 0 if absent or if `start` is past the end (`mathops.c:1396`). 5.7 order is `INSTR(start, s, sub)` | 278 |
| `$REPLACE(s, find[, repl[, count]])` | 2-4 (str, str, str, num) | str | Replaces non-overlapping occurrences left to right; without `repl` deletes them; `count` limits replacements (5.9.x); empty `find` returns `s` unchanged (`text.c:253`). 5.7 accepts 2-3 arguments | 51 |
| `$TRIM(s)` | 1 str | str | Removes leading and trailing spaces, tabs, CR and LF (`text.h`, `qspDelSpc`; the space class is `" \t\r\n"`). The docs mention only spaces and tabs | 20 |
| `$LCASE(s)`, `$UCASE(s)` | 1 str | str | Per-character case mapping through Unicode tables (`towlower.c`, `towupper.c`); the wasm tests cover Cyrillic | 55 / 26 |
| `$STR(v)` | 1 str | str | Converts any value to text (tuples to `[..]` form) | 291 |
| `VAL(v)` | 1 any | num | Converts to a number; anything that is not a number gives 0 without an error. `' 12 '` and `'-5'` convert; `''` is 0 | 132 |
| `ISNUM(v)` | 1 any | bool | 1 for a number, a numeric string (optional spaces and sign, at least one digit), or a one-item numeric tuple; 0 for `''` | 33 |
| `STRCOMP(s, re)` | 2 str | bool | 1 if the regex matches the whole string (`regexp.c:64`, match length must equal string length) | 0 |
| `$STRFIND(s, re[, group])` | 2-3 (str, str, num) | str | First match, or the given capture group; `''` if none or if the match is empty | 0 |
| `STRPOS(s, re[, group])` | 2-3 (str, str, num) | num | 1-based position of the first match or group, 0 if none | 7 |

**Regular expressions.** Oniguruma with Perl_NG syntax (`regexp.c:33`, `ONIG_SYNTAX_PERL_NG`), compiled with default options, so matching is case-sensitive unless the pattern sets `(?i)`. The last 10 patterns are cached. A bad pattern raises "Regular expression error!". `ARRCOMP` and `SCANSTR` use the same engine.

## 2. Number and random functions

| Function | Args | Returns | Behavior | Girl Life |
|---|---|---|---|---|
| `RAND(a[, b[, mode]])` | 1-3 num | num | Uniform integer between `a` and `b` inclusive; the bounds may be in either order. `b` defaults to 1 in 5.8+ and 0 in 5.7 (`legacy: src/mathops.c:1041`). With `mode`, values follow a normal curve centered on `mode` and cut off at the bounds; a mode outside the range favors the nearest bound (`common.c:278`, `qspNormalRand`) | 12,497 |
| `RND` | 0 | num | `RAND(1, 1000)` | 0 |
| `MAX(...)`, `MIN(...)` | 1-20 any | any | Several arguments: the largest or smallest by the comparison rules. One argument: treated as an array name, returns the max or min element. In 5.9.5 the array's prefix chooses which values count (`max('a')` numbers, `$max('$a')` strings); master without a prefix requires all values to have one type. `max(a)` with a numeric `a` raises "Incorrect variable name!" because the value becomes the name. 5.7 array form: empty strings are skipped and string-only elements count as 0 in numeric searches (`legacy: tests/engine/base-functions.qspt:126-152`) | 616 / 388 |
| `RGB(r, g, b[, a])` | 3-4 num | num | Each component clamped to 0-255, alpha default 255. Result is `(a<<24) \| (b<<16) \| (g<<8) \| r` as a signed int, so opaque colors are negative: `rgb(0,0,0)` is -16777216 (`mathops.c:1585`). The docs warn many players ignore alpha | 1,068 |
| `IIF(c, x, y)` | 3 (bool, any, any) | any | `x` if `c` is true, else `y`. Only the chosen branch is evaluated in 5.8+; both in 5.7 | 3,402 |
| `MSECSCOUNT` | 0 | num | Milliseconds of play time. The value is saved and restored with the game (`game.c:263`, `qspResetTime` on load), so it measures play time, not wall time | 2 |

The random generator is an additive lagged Fibonacci generator with a shuffle table (`common.c:138-160`). It is reseeded from the clock when a game starts or restarts (`game.c`, `qspRestartGame`). `qspUniformRand` uses `rand % range`, which slightly favors low values for large ranges.

## 3. Array functions

| Function | Args | Returns | Behavior |
|---|---|---|---|
| `ARRSIZE(name)` | 1 name | num | Number of positions, including holes and string-keyed elements. 0 for a declared but unassigned local (docs) |
| `ARRPOS(name, value[, start])` | 2-3 (name, any, num) | num | First position at or after `start` (default 0) whose value equals `value`, or -1. `value` is converted to the array's prefix type first. Holes compare as the empty value, so searching for 0 or `''` can find a hole (wasm tests "supports holes", "return index including empty elements"). Comparison is strict on type (`variables.c`, `qspArrayPos`). 5.7 order: `ARRPOS(start, name, value)` |
| `ARRCOMP(name, re[, start])` | 2-3 (name, str, num) | num | First position at or after `start` whose string value fully matches `re`, or -1. Holes count as `''`. Number elements are skipped. 5.7 order: `ARRCOMP(start, name, re)` |
| `ARRITEM(name[, index])` (5.8.0) | 1-2 (name, any) | any | Value at an index of a named array, avoiding `DYNEVAL` |
| `%ARRPACK(name[, start[, count]])` (5.9.1) | 1-3 (name, num, num) | tuple | Packs elements into a tuple; `arrpack('args')` turns arguments into a tuple |
| `$ARRTYPE(name[, index])` (5.9.1) | 1-2 (name, any) | str | `''` (missing or undefined), `'#'`, `'$'` or `'%'` |

Only numeric positions are returned. There is no function that returns the string key of an element.

## 4. Location and code functions

| Function | Args | Returns | Behavior |
|---|---|---|---|
| `FUNC(loc, args...)` | 1-20 (str, any...) | any | Runs a location like `GOSUB` and returns its `RESULT`. `@loc(args)` is shorthand (5.8+) |
| `DYNEVAL(code, args...)` | 1-20 (code, any...) | any | Runs code text and returns its `RESULT` |
| `LOC(name)` | 1 str | bool | 1 if the location exists. Priority 11 (5.8+) or 8 (5.7). 5.7 returns -1 for true |
| `$CURLOC` | 0 | str | Name of the location reached by the last `GOTO`/`XGOTO`, as written in its header (case preserved). `GOSUB` and `FUNC` do not change it |
| `$DESC(loc)` | 1 str | str | The base description of a location with subexpressions expanded. A missing location raises "Location not found!" |

`$DESC` and base descriptions: the docs say text-editor sources cannot have base descriptions, so `$DESC` returns `''`. The current TXT2GAM can write them through a `! BASE` ... `! END BASE` section ([tooling-and-development.md](tooling-and-development.md)), and Girl Life's own compiler turns leading `*p` lines into a base description. Girl Life does not use `$DESC`.

## 5. Screen and interaction functions

| Function | Args | Returns | Behavior |
|---|---|---|---|
| `$MAINTXT` | 0 | str | Current text of the main window |
| `$STATTXT` | 0 | str | Current text of the stats window |
| `$USER_TEXT`, `$USRTXT` | 0 | str | Current text of the input line |
| `$INPUT(prompt)` | 1 str | str | Shows a modal input box and returns the text, `''` on cancel. `INPUT` without `$` returns the same string; assigning a non-numeric answer to a number variable raises "Type mismatch!" |
| `$SELACT` | 0 | str | Name of the selected (hovered) action, `''` if none |
| `$SELOBJ` | 0 | str | Name of the selected object (original name, not the `MODOBJ` title) |
| `$CURACTS` | 0 | code | All current actions as QSP code: `ACT 'name','image':` followed by the code lines (`actions.c:117`). Code lines are in preprocessed (upper-cased) form with strings untouched; 5.7 keeps the code as written. Apostrophes in names are doubled. `dynamic $curacts` restores them |
| `$CUROBJS` (5.9.0) | 0 | code | All objects as `ADDOBJ` lines plus `MODOBJ` lines for changed titles |
| `$GETOBJ(n)` | 1 num | str | Name of the object at 1-based position `n`, `''` if out of range |
| `COUNTOBJ` | 0 (5.9.5), 0-1 (master) | num | Number of objects. master: `COUNTOBJ('name')` counts objects with that name |
| `OBJ(name)` | 1 str | bool or num | See the version table below |
| `ISPLAY(file)` | 1 str | bool | Asks the player whether the file is playing; empty name gives 0 |
| `$QSPVER([param])` | 0-1 str | str | Version text from the player. Classic player: `"<lib version> (classic)"` with no argument, `"Classic"` for `'player'`, the platform for `'platform'` (`qspgui: qspgui/callbacks_gui.cpp:423`, `comtools.cpp:240`). qSpider returns the bare version per the docs. 5.7 takes no argument and returns the library version itself (`legacy: tests/engine/base-functions.qspt:4-12`) |

**OBJ by version.**

| Version | `obj 'x'` when three `x` objects exist | Source |
|---|---|---|
| 5.7 | -1 | `legacy: src/mathops.c:513-514` |
| 5.8.0 to 5.9.3 | 1 | blog 2026-01-01 |
| 5.9.4, 5.9.5 | 3 (the count) | `engine-5.9.5: qsp/mathops.c`, `case qspOpObj` returns `qspObjsCountByName`; blog |
| master (unreleased) | 1, with `COUNTOBJ('x')` giving 3 | commit `00faed4` "COUNTOBJ with argument returns the number of such objects, OBJ checks existence only" |

The docs' OBJ chapter describes 1 or 0.

**`$CURACTS` in practice.** GLSS checks `instr($curacts, 'Go to first period') > 0` to find out whether Girl Life's regular class actions are on screen before adding its own (`glss/locations/mod_glss.qsrc:32`). Matching on action names works because names keep their case; matching on code text would need upper-case search strings.

## 6. System variables

### Handler variables (engine reads them)

Each holds a location name, or several in consecutive elements; the engine runs each in turn until it meets an empty or non-string element (`locations.c:307`). Handlers start from the global scope.

| Variable | When it runs | Arguments | Source |
|---|---|---|---|
| `$ONNEWLOC` | After a `GOTO`/`XGOTO` target's code finishes | the `GOTO` arguments | `locations.c:342` |
| `$ONGSAVE` | Before the state is written by `SAVEGAME` or the player's save | none | `game.c:263` |
| `$ONGLOAD` | After a save is restored | none | `game.c`, end of `qspOpenGameStatus` |
| `$ONOBJADD` | After `ADDOBJ` adds an object | `$ARGS[0]` name, `$ARGS[1]` image | `objects.c:265` |
| `$ONOBJDEL` | After `DELOBJ`/`KILLOBJ` removes objects, once per object | `$ARGS[0]` name | `objects.c` |
| `$ONOBJSEL` | When the player selects a different object | none | `default_control.c`, `QSPSetSelObjectIndex` |
| `$ONACTSEL` | When the player selects (hovers) a different action | none | `QSPSetSelActionIndex` |
| `$USERCOM` | When the player presses Enter in the input line | none | `QSPExecUserInput` |
| `$COUNTER` | Every timer tick (default 500 ms), skipped while a dialog callback is open | none | `QSPExecCounter` |

Girl Life sets all of these except `$ONACTSEL` and `$ONOBJADD`/`$ONOBJDEL` in `start` (`girl-life: locations/start.qsrc:21-26`, with `debug = 1` on line 8): `$ongload = 'loadg'`, `$ongsave = 'saveg'`, `$onnewloc = 'LOCA'`, `$onobjsel = 'onobjsel'`, `$counter = 'counter'`, `$usercom = 'inputProcessing'` (an empty location).

### Display variables (the player reads them)

The classic player reads these on refresh (`qspgui: qspgui/callbacks_gui.cpp:94-138`, `frame.cpp:376-409`). Zero or empty means "use the player setting".

| Variable | Meaning |
|---|---|
| `USEHTML` | Non-zero enables HTML in text, action names, object names, `MSG` and `INPUT` prompts. qSpider always renders HTML (docs) |
| `BCOLOR`, `FCOLOR`, `LCOLOR` | Background, text and link colors, as produced by `RGB` |
| `FSIZE` | Base font size |
| `$FNAME` | Font name |
| `$BACKIMAGE` | Background image of the main window |
| `DISABLESCROLL` | Non-zero stops auto-scrolling to new text |
| `NOSAVE` | Non-zero disables the player's save menu; `SAVEGAME` still works |

Girl Life sets `usehtml = 1`, `disablescroll = 1`, `$fname = 'Tahoma'`, `fsize = 12` in `start`, and computes colors in `themes.qsrc` with `rgb` (1,068 calls in 6 files).

### Engine state variables

| Variable | Meaning |
|---|---|
| `ARGS` | Arguments of the current call; see [variables-and-data-types.md](variables-and-data-types.md) |
| `RESULT` | Return value of the current `FUNC`/`DYNEVAL` call |
| `DEBUG` | Element 0 non-zero disables the game-file checksum check when loading a save (`game.c:391`). Girl Life sets `debug = 1` in `start`, so saves survive game updates |
| `DISABLESUBEX` | 5.7 only; 5.8+ ignores it |

Any system variable can be declared `local`, which shadows it. The docs strongly advise against it.

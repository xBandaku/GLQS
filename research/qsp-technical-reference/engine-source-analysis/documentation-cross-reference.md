# Documentation versus implementation

Claims from dev.qsp.org (docs commit `8dc098f`) checked against the engine (5.9.5 tag and master `00faed4`), the legacy 5.7 source, the players, and the tests. Each row gives the claim, the evidence, and a status:

- **Confirmed**: the source matches the docs.
- **Differs**: the docs are wrong for at least one current version.
- **Version-specific**: true only for some versions; the docs do not say which.
- **Not documented**: the engine has behavior the docs do not mention.
- **Unverified**: depends on player code or files that were not checked.

## 1. Confirmed

| Docs claim (page) | Evidence |
|---|---|
| Operator priority list for 5.8.0 (operators) | `engine: qsp/mathops.c:167-267`; grammar priority comment |
| 5.7.0 priority list with `&` lowest and `OBJ`/`LOC`/`NO` together (operators) | `legacy: src/mathops.c:134-195` |
| Comparison rules for numbers, strings, string vs number, tuples (operators) | `variant.c:249`, `tuples.c:131`; wasm `expressions.test.ts` |
| `/` truncates; `MOD` of a negative dividend is negative (operators) | `variant.c:380`, `mathops.c:1186`; wasm tests |
| Concatenation `&` must be in brackets at statement level (operators) | `codetools.c:405` splits statements at `&` outside brackets |
| Implicit statement ignores a function that returns nothing (statements) | `statements.c:940`; wasm test |
| Single-line IF with code after the colon makes following lines unconditional (statements) | `codetools.c:405`; wasm test "wrong multi line if" |
| `else if` works like `elseif` (statements) | `codetools.c`, ELSE IF conversion |
| Labels are case-insensitive, local to a code block, first duplicate wins (syntaxemes) | `codetools.c:728`, `statements.c:370` |
| Up to 19 arguments in `ARGS`; separate `ARGS` per call; actions see the `GOTO` arguments (sys-var) | `QSP_MAXSTATARGS 20`; `locations.c:342`; wasm "GOTO arguments should be avaliable in actions" |
| `RESULT`, `$RESULT`, `%RESULT` are one variable; last write wins (functions) | one value per element (`bindings/qsp.h:150`) |
| Locals propagate into called locations and loops but not into actions (statements, LOCAL) | `variables.c:373`; wasm "local variables are not visible in actions" |
| `ARRSIZE` of an unassigned local is 0 (functions) | `variables.c`, `qspArraySize` counts values |
| `KILLALL` does not run `$ONOBJDEL` (statements, sys-var) | `statements.c:1025` clears variables first |
| Duplicate action names are ignored (statements, ACT) | `actions.c:69` |
| `ADDOBJ` position is 1-based; `$GETOBJ` returns `''` out of range (statements, functions) | `objects.c:436`, `mathops.c:1625` |
| `$MID('abcdef', 0)` is `'abcdef'`, `$MID('abcdef', 8)` is `''` (functions) | `mathops.c:1418` |
| `ISNUM` accepts surrounding spaces and a leading `-`; `ISNUM('')` is 0 (functions) | `text.c:156` |
| `RAND(4, 1)` swaps bounds; second argument defaults to 1 (functions) | `mathops.c:1571`, `common.c:169` |
| `RGB` color values in the `BCOLOR` examples (sys-var) | `mathops.c:1585`: opaque black is `0xFF000000` = -16777216 |
| Handler variables can list several locations; empty element stops the list (sys-var) | `locations.c:307` |
| `DEBUG` disables the save identity check (sys-var) | `game.c:391` |
| `MENU` stops at an empty item; colons are searched from the end (statements) | `menu.c:37` |
| `STRCOMP` matches the whole string (functions) | `regexp.c:64` |
| `DISABLESUBEX` has no effect from 5.8.0 (sys-var) | No reference in the engine source; the legacy library reads it (`legacy: src/text.c:490`) |
| Default timer 500 ms; `SETTIMER` changes it (statements, sys-var) | `game.h`, `QSP_DEFTIMERINTERVAL` |
| `$QSPVER` returns `"X.Y.Z (classic)"` in the classic player (functions) | `qspgui: qspgui/comtools.cpp:240` |
| `INCLIB` adds only locations whose names are new (statements) | `game.c:191` |
| `OPENQST` keeps variables and objects (statements) | `game.c`, `qspRestartGame(QSP_FALSE)` |

## 2. Differs or version-specific

| Docs claim (page) | Actual behavior | Status |
|---|---|---|
| Missing `$` on assignment "will cause error #101" (syntaxemes); `$mid('abcdef')` gives error 120 (functions) | 101 and 120 are 5.7 numbers. 5.9.5 and master use 12 and 30 | Differs |
| `GOSUB [$location],[argument 0], ... ,[argument 8]` and `GT ... [argument 8]` (statements) | 5.8+ accepts 19 arguments (other lines on the same page say `[argument 18]`). 9 is the 5.7 limit | Differs (inconsistent within the page) |
| `OBJ` returns 1 or 0 (operators) | 5.9.4 and 5.9.5 return the number of objects with that name; master returns 1/0 again with `COUNTOBJ(name)` for counts; 5.7 returns -1/0 | Version-specific |
| `$lcase('I DON\'T WANT TO SHOUT AT YOU.')` (functions) | QSP has no backslash escapes; the apostrophe ends the string | Differs (invalid example) |
| `y = iif(x = 0, 0, 1/x)` "will NOT cause division by zero" (functions) | True for 5.8+. 5.7 evaluates both branches | Version-specific |
| `$DESC` always returns `''` for games written in a text editor (functions) | TXT2GAM 0.5 supports a `! BASE` section with base descriptions; `@qsp/converters` drops them | Differs for TXT2GAM |
| `$TRIM` removes adjacent tabs and spaces (functions) | Also removes CR and LF (space class `" \t\r\n"`) | Differs (incomplete) |
| Unary plus was abandoned after 5.7.0 (operators) | Not in 5.9.5; master accepts it again (commit `73d4527`) | Version-specific |
| `KILLVAR` without arguments deletes all variables (statements) | True in 5.9.5; master deletes only globals | Version-specific |
| `string = 'Short string'` causes a type mismatch (syntaxemes) | True in 5.9.5; master lets unprefixed names hold strings | Version-specific |
| Reading `%number` from a numeric variable gives "empty strings or zeros" (English syntaxemes) vs "empty tuple" (Russian) | The engine returns an empty tuple (`variables.c:604`); the example output `[,]` comes from unpacking it | The English wording is imprecise |
| `ADDLIB`, `DELLIB` are old names of `INCLIB`, `FREELIB` (keyword index) | The 5.7 legacy source has only `ADDQST` and `KILLQST`. Older versions were not available | Unverified for versions before 5.7 |
| Location examples end with `- start` (statements) or `-- summ` (syntaxemes) | TXT2GAM needs `--`; `@qsp/converters` accepts `-`; Girl Life's compiler needs `--- name ---` | Tool-specific |
| `END` in a multi-line IF "must be on a separate line" (statements) | `end & stmt` is valid and runs `stmt` (wasm test) | Nuance |
| `MSECSCOUNT` counts "milliseconds elapsed since the game started" (functions) | It counts play time and is restored from saves (`game.c`, `qspResetTime`) | Nuance |
| Comment after a multi-line header colon is allowed (statements, "Exception") | Only 5.8+; in 5.7 the header becomes single-line | Version-specific |

## 3. Not documented

| Engine behavior | Evidence |
|---|---|
| `EXEC 'text'` statement passes text to the player (qSpider commands, classic player ignores it) | `statements.c:1122`; `qspider: libs/game-state/src/qspider-commands.ts` |
| `MENU name, start, count` | `statements.c` table (1-3 args); `menu.c:37` |
| `DELOBJ name, count` (mentioned only in the 2026 blog) | `objects.c:448` |
| `#` number type prefix | `declarations.h:60`; grammar `typePrefix` |
| `?` undefined value (master) | `mathops.c:754`, commit `af77f90` |
| `COUNTOBJ('name')` (master) | `mathops.c:1257` |
| Each IF/ELSEIF/ELSE branch is a local scope | `statements.c:742`, `qspExecMultilineCode` |
| `AND`/`OR` short-circuit in 5.8+ | `mathops.c:1073-1108` |
| `GOTO` stops all code running in the current event, including callers | `locations.c:342`, `qspLocationState` |
| A runtime error aborts the whole event | `errors.c:20` |
| Call depth limit 2,000 ("Maximum location call depth exceeded!") | `locations.h` |
| Limits: 50 actions, 1,000 objects, 100 menu items, 100 included files, 500 playlist entries, 20 tuple items per literal | headers; `tests/errors-to-test.md` in the wasm repo mentions 50 actions |
| String array keys and location names are case-insensitive; string comparison is case-sensitive | `variables.c:544`, `locations.c:171`, `text.h:308` |
| Variable name rules and the delimiter set | `variables.h:122`, `declarations.h:148` |
| `$CURACTS` returns upper-cased code | `codetools.c:900`, `actions.c:117` |
| Saves keep action code; loading does not re-run the current location; save version range checks | `game.c:263`, `:391` |
| `settimer 0` stops the classic player's timer | `qspgui: qspgui/callbacks_gui.cpp:75-83` |
| In 5.7, inline `ELSEIF` in a single-line IF is not recognized | `legacy: tests/engine/conditionals.qspt:50-93` |
| The counter does not run while a dialog is open | `default_control.c:390` |

## 4. Unverified

- The docs' statement that the classic player plays up to 32 sounds at once: this is player code, not checked.
- `REFINT` updates "2 times per second by default": the engine only forwards the call; refresh frequency is player behavior.
- HTML support details per player.
- qSpider-specific notes (`$QSPVER` without "(classic)", HTML always on): not checked in qSpider source.

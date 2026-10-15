# Runtime behavior: limits, errors, termination

Hard limits, error codes per engine version, and the mechanism that stops running code. References as in [source-index.md](../source-index.md).

## 1. Limits

| Limit | master (00faed4) | 5.9.5 | 5.7 (legacy) | Source |
|---|---|---|---|---|
| Actions on screen | 50 | 50 | 50 | `actions.h`, `QSP_MAXACTIONS` |
| Objects | 1,000 | 1,000 | 1,000 | `objects.h`, `QSP_MAXOBJECTS` |
| Menu items | 100 | 100 | 100 | `menu.h` |
| Included library files | 100 | 100 | 100 | `game.h`, `QSP_MAXINCFILES` |
| Playlist entries | 500 | 500 | 500 | `playlist.h` |
| Arguments to a location call (`GOSUB`, `GOTO`, `FUNC`, `DYNAMIC`, ...) | 19 + name | 19 + name | 9 + name | `QSP_MAXSTATARGS 20`; `legacy: src/statements.c:141` |
| Arguments to a function / items in one tuple literal | 20 | 20 | 10 (`FUNC`, `DYNEVAL`, `MIN`, `MAX`) | `QSP_MAXMATHOPARGS` |
| Operator stack depth in an expression | 30 | 30 | 30 | `mathops.h` |
| Compiled items in one expression | 1,000 | 200 | 100 | `QSP_MAXMATHITEMS`; `legacy: QSP_MAXITEMS` |
| Nested location calls | 2,000 | 2,000 | none (process stack) | `locations.h`, `QSP_MAXLOCCALLDEPTH` |
| Global variables | 100,000 | 32 per bucket, 512 buckets | 50 per bucket, 256 buckets | see [variables-and-data-types.md](../official-documentation/variables-and-data-types.md) |
| Local variables per scope | 500 | 32 per bucket, 16 buckets | no locals | |
| Cached compiled regexes | 10 | 10 | none (compiled per call) | `regexp.h` |
| Cached `DYNAMIC` code blocks | 64 buckets x 8, texts up to 8,192 chars | none (preprocessed on every call; compiled expressions are cached separately, 5 per bucket) | none | `codetools.h`; `engine-5.9.5: qsp/statements.c:724`, `mathops.h` |

Notes:
- The 5.9.5 "Reduce QSP_MAXLOCCALLDEPTH to 1000" commit (`654206f`) was followed by a custom stack allocator, and the 5.9.5 tag has 2,000.
- In 5.7 deep recursion has no limit, so a runaway `gs` loop crashes the player instead of raising an error.

## 2. Error codes

The numeric codes changed twice. The descriptions are the engine's English strings (`errors.c:67`).

| Meaning | 5.7 | 5.9.4 | 5.9.5 and master | Message (5.9.5) |
|---|---|---|---|---|
| Internal error | | | 10 | Internal error! |
| Division by zero | 100 | 10 | 11 | Division by zero! |
| Type mismatch | 101 | 11 | 12 | Type mismatch! |
| Stack overflow / call depth | 102 | 12 | 13 | Maximum location call depth exceeded! |
| Too many items / expression too complex | 103 | 13 | 14 | Expression too complex! |
| File not found | 104 | | | |
| Can't load file | 105 | 14 | 15 | Can't load file! |
| Game not loaded | 106 | 15 | 16 | Game not loaded! |
| `:` not found | 107 | 16 | 17 | Token [:] not found! |
| Can't include file | 108 | 17 | 19 | Can't include file! |
| Can't add action | 109 | 18 | 20 | Can't add action! |
| `=` not found | 110 | 19 | | |
| Location not found | 111 | 20 | 23 | Location not found! |
| `end` not found | 112 | 21 | 18 | Token [end] not found! |
| Label not found | 113 | 22 | 24 | Label not found! |
| Incorrect name | 114 | 23 | 25 | Incorrect variable name! |
| Quote not found | 115 | 24 | 26 | Quote not found! |
| Bracket not found | 116, 117 | 25, 26 | 27 | Bracket not found! |
| Syntax error | 118 | 27 | 28 | Syntax error! |
| Unknown action | 119 | 28 | 29 | Unknown action! |
| Wrong argument count | 120 | 29 | 30 | Incorrect arguments count! |
| Can't add object | 121 | 30 | 21 | Can't add object! |
| Can't add menu item | 122 | 31 | 22 | Can't add menu item! |
| Too many variables | 123 | 32 | 31 | Too many variables! |
| Regular expression error | 124 | 33 | 32 | Regular expression error! |
| Code not found | 125 | 34 | 33 | Code not found! |
| Loop condition not found | | 35 | 34 | Loop condition not found! |

Sources: `legacy: src/bindings/qsp.h:22-48` and `src/errors.c`; `engine-5.9.4: qsp/bindings/qsp.h`; `engine: qsp/bindings/qsp.h:13-40`. The wasm tests use the 5.9.5 numbers (12, 11, 17, 18, 29). The docs cite 101 and 120, which are the 5.7 numbers.

5.7 messages differ slightly ("Sign [:] not found!", "[end] not found!", "Incorrect variable's name!", "Incorrect arguments' count!"). Players may translate messages.

## 3. How execution stops

The engine has no exceptions. It uses one global counter, `qspLocationState`:
- Every function that runs code or evaluates something saves the counter on entry and checks it after each step that could run code: a statement, an argument evaluation, a nested call.
- If the counter changed, the function frees what it holds and returns at once. Its caller does the same, so the entire call chain unwinds.
- The counter is incremented by:
  - `GOTO` and `XGOTO` (`locations.c:342`), which then run the target location in that same call;
  - any error (`errors.c:20`);
  - starting a new game, opening a game, loading a save.
- The new location's own code and `$ONNEWLOC` run with the new counter value, so they continue normally.

| Event during execution | What still runs |
|---|---|
| `gt 'x'` | Location `x`, then `$ONNEWLOC`. Nothing else from before |
| `exit` | The caller of the current code block continues |
| runtime error | Nothing; the player shows the error |
| `jump` to a missing label | Error "Label not found!" from the outermost range |
| player loads a save during `MSG` | The code waiting on the `MSG` stops when the dialog returns (`callbacks.c`, `qspFinalizeCallback`) |

The legacy engine uses the same idea with `qspRefreshCount` (`legacy: src/locations.c:394-409`).

## 4. Timing and responsiveness

- QSP code runs on the player's thread. Long loops freeze the interface until the event ends. Only `WAIT`, `MSG`, `INPUT` and `MENU` let the player redraw mid-event.
- The counter location runs at the timer interval, but never while a dialog is open.
- master compiles each statement's expressions once per code block. Girl Life's frequent `dynamic` calls with constant text benefit from the code block cache; `dynamic` calls whose text changes each time (built with `<<...>>`) are preprocessed every time.

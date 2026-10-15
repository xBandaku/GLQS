# Common pitfalls and edge cases

Mistakes that QSP code, Girl Life code and GLSS code are most likely to make, grouped by area. Each row names the versions affected and how to avoid the problem. The "Ref" column points to the page with the evidence.

Abbreviations for the "Ref" column:
- **LS** [language-syntax.md](official-documentation/language-syntax.md)
- **VD** [variables-and-data-types.md](official-documentation/variables-and-data-types.md)
- **EO** [expressions-and-operators.md](official-documentation/expressions-and-operators.md)
- **CF** [control-flow.md](official-documentation/control-flow.md)
- **EM** [execution-model.md](official-documentation/execution-model.md)
- **IO** [input-output-and-persistence.md](official-documentation/input-output-and-persistence.md)
- **FC** [functions-and-commands.md](official-documentation/functions-and-commands.md)
- **API** [built-in-api-reference.md](official-documentation/built-in-api-reference.md)
- **VER** [version-differences.md](engine-source-analysis/version-differences.md)
- **RT** [runtime-behavior.md](engine-source-analysis/runtime-behavior.md)
- **OBS** [implementation-observations.md](girl-life-analysis/implementation-observations.md)
- **DEP** [dependencies-and-configuration.md](girl-life-analysis/dependencies-and-configuration.md)
- **SP** [scripting-patterns.md](girl-life-analysis/scripting-patterns.md)
- **DCR** [documentation-cross-reference.md](engine-source-analysis/documentation-cross-reference.md)

## 1. Parsing and comments

| # | Pitfall | Versions | Avoid it | Ref |
|---|---|---|---|---|
| 1.1 | An apostrophe in a comment (`!! don't`) opens a string. Everything up to the next apostrophe, possibly many lines later, becomes part of the comment, including real code | all | Write `''` in comments. 13 Girl Life comment blocks close correctly only because their stray quotes pair up | LS 4, OBS 2 |
| 1.2 | A comment after the colon of a multi-line `if`/`elseif`/`else`/`act` header makes the header single-line, so the indented body always runs and `end` is ignored | 5.7 | Put the comment on its own line | LS 4, VER 1 |
| 1.3 | `if x: & ! note` is single-line in every version: the colon is no longer the end of the line | all | Same as 1.2 | LS 4 |
| 1.4 | Inline `elseif` in a single-line IF (`if a: x elseif b: y`) is not recognized | 5.7 | Use the multi-line form | CF 1, VER 1 |
| 1.5 | `&` at statement level separates statements, so `$s = 'a' & 'b'` assigns `'a'` and then prints `'b'` | all | Use `+`, or bracket it: `$s = ('a' & 'b')` | EO 6 |
| 1.6 | `!` in the middle of an expression is "not equal", not a comment | all | Comments only at statement start | LS 4 |
| 1.7 | Line continuation needs a space before the final `_`. Continuation inside open `(` or `[` exists only from 5.9.4 | all / 5.9.4+ | Keep long expressions on one line for 5.7 | LS 6-7 |
| 1.8 | Location end markers differ by tool: Girl Life's `qsp-cli` needs `--- name ---`, TXT2GAM needs `--`, `@qsp/converters` accepts `-` | tools | Use the `--- name ------` form in Girl Life and GLSS | LS 1, DEP 3 |
| 1.9 | A `.qsrc` file not listed in the `.qproj` manifest is left out of the build with at most a warning | tools | Register every new file. Girl Life has 31 unregistered files | DEP 2, OBS 1 |

## 2. Values and types

| # | Pitfall | Versions | Avoid it | Ref |
|---|---|---|---|---|
| 2.1 | Comparisons return -1 for true on 5.7 and 1 on 5.8+, so `if func(...) = 1:` fails on 5.7 when the function returns a raw comparison | 5.7 vs 5.8+ | Return `iif(cond, 1, 0)` or test truthiness (`if func(...):`) | EO 5, OBS 8 |
| 2.2 | `AND`/`OR`/`NO` are bitwise on 5.7: `2 and 1` is 0, `no 1` is -2 | 5.7 | Only combine values that are 0 or -1 (results of comparisons), or compare first: `(x <> 0) and (y <> 0)` | EO 5 |
| 2.3 | On 5.7 an element holds a number and a string at once; on 5.8+ one value, and the last write wins. Code that writes `x` and `$x` separately loses one of them on 5.8+ | 5.7 vs 5.8+ | One type per element. Girl Life has 44 elements written both ways | VD 2, OBS 6 |
| 2.4 | Reading with the wrong prefix gives `''` or 0 silently instead of an error | 5.8 to 5.9.5 | Read with the prefix you wrote with | VD 3 |
| 2.5 | A string used as a condition is a type mismatch on 5.7 unless it is empty or numeric | 5.7 | `if $s <> '':` | EO 5 |
| 2.6 | `x = 'text'` without `$` is a type mismatch before master and silently stores a string on master | all | Always prefix string variables with `$` | VER 4 |
| 2.7 | String array keys and location names ignore case, but string comparison does not. `$curloc` returns the header's spelling | all | Compare `$curloc` with the exact header case, or use `$lcase` | VD 4, OBS 1 |
| 2.8 | Numbers are 32-bit integers. `/` truncates and there are no fractions; too-large literals clamp | all | Scale values (Girl Life uses `int_divide`, `round_divide` helpers) | LS 9 |
| 2.9 | `killvar x` passes the value of `x` as a name; the name must be a string | all | `killvar 'x'` | FC (KILLVAR) |
| 2.10 | `RESULT` is not isolated by `GOSUB` on 5.7, so a `gs` inside a function can overwrite the caller's `result` | 5.7 | Assign `result` last, or use `func` for nested calls | VD 6 |

## 3. Evaluation and calls

| # | Pitfall | Versions | Avoid it | Ref |
|---|---|---|---|---|
| 3.1 | `IIF` evaluates both branches on 5.7. `iif(x = 0, 0, 1/x)` divides by zero; `func` and `rand` in branches run anyway | 5.7 | Use `if`/`else` for branches with side effects or errors | EO 2, OBS 7 |
| 3.2 | `AND`/`OR` do not short-circuit on 5.7: `if loc(name) and func(name) ...` calls `func` even when `loc` is false | 5.7 | Nest the conditions | EO 2 |
| 3.3 | `RAND(n)` returns 0..n on 5.7 and 1..n on 5.8+ | 5.7 vs 5.8+ | Always pass two bounds | API 2 |
| 3.4 | Three-argument `INSTR`, `ARRPOS`, `ARRCOMP` take the start position first on 5.7 and last on 5.8+ | 5.7 vs 5.8+ | Use the two-argument forms, or branch on `$qspver` | API 1, 3 |
| 3.5 | `OBJ` binds looser than comparisons on 5.7 (`obj 'a' = obj 'b'` is always 0) and returns -1, 1, or a count depending on version | all | Parenthesize: `(obj 'a')`; test `> 0` | EO 1, API 5 |
| 3.6 | `gt` stops everything running in the event, including the code that called the location doing the `gt` | all | Treat `gt` as the last statement; do cleanup before it | CF 5, RT 3 |
| 3.7 | Any runtime error aborts the whole event. Nothing after it runs, including `$ONNEWLOC` | all | Guard computed calls with `loc(name)` | RT 3 |
| 3.8 | A handler without `exit` falls through into the following `if $ARGS[0] = ...` tests; a misspelled handler name does nothing | all | End every handler with `exit`; run `callvalidator.py` | SP 1 |
| 3.9 | Global temporaries are shared by nested calls, so a handler that calls itself, directly or through other locations, overwrites its own working values | 5.7 style | Unique names per handler, or `LOCAL` on 5.8+ | SP 4 |
| 3.10 | `jump` looks in the current IF branch first, then in each enclosing block out to the whole location. A label missing from the current branch is found anywhere in the location, so a duplicate name in another handler can capture the jump | all | Make label names unique per location; Girl Life prefixes them with the handler name | CF 3 |
| 3.11 | 5.7 has no call depth limit: runaway recursion crashes the player. 5.8+ stops at 2,000 nested calls with an error | all | Avoid unbounded recursion | RT 1 |
| 3.12 | Arguments: 9 per call on 5.7, 19 on 5.8+. Extra arguments are an error | 5.7 | Pass at most 9 | RT 1 |

## 4. Screens, actions and saves

| # | Pitfall | Versions | Avoid it | Ref |
|---|---|---|---|---|
| 4.1 | At most 50 actions; the 51st raises "Can't add action!" | all | Mods that append actions add to screens that may already be full | FC (ACT) |
| 4.2 | An `act` whose name already exists, compared without case, is silently ignored | all | Give mod actions a distinct prefix (GLSS uses `GLSS: `) | FC (ACT) |
| 4.3 | Action code runs later, with no locals from the location that created it; it sees the global `ARGS` of the last `gt` | all | Copy what the action needs into globals or into the action text | CF 7 |
| 4.4 | `$CURACTS` returns action bodies upper-cased on 5.8+ (names keep their case) | 5.8+ | Search for action names, not code | API 5 |
| 4.5 | Saves keep the code of the actions on screen, and loading does not re-run the location. After an update, those actions run the old code once | all | Expect one stale screen after loading an old save | IO 7, OBS 11 |
| 4.6 | Text appears only when the event ends; long loops freeze the player. Only `WAIT`, `MSG`, `INPUT` and `MENU` redraw mid-event | all | Keep per-event work small | RT 4 |
| 4.7 | `$COUNTER` code runs every tick (500 ms by default) but never while a dialog is open | all | Keep it short; do not rely on it during `MSG` | EM 6 |
| 4.8 | `INCLIB` only adds locations whose names are new, so a mod cannot replace a core location | all | Hook in through the mod dispatcher instead | IO 6 |

## 5. Versions, players and tools

| # | Pitfall | Versions | Avoid it | Ref |
|---|---|---|---|---|
| 5.1 | `$qspver` comparisons are string comparisons: `'5.10.0' < '5.9.2'` | all | Split the version on `.` and compare numbers | OBS 4 |
| 5.2 | Engines from 5.9.4 load only saves from 5.9.4 or later; the master engine only from 5.9.6 | 5.9.4+ | Keep the same player for a playthrough | VER 1, 4 |
| 5.3 | On 5.7, `killvar 'x'` leaves the name in its hash slot. Every distinct name ever written stays until `killall`; one bucket of 50 slots could overflow | 5.7 | Reuse a few temporary names; group temporaries in one array | VD 5, OBS 5 |
| 5.4 | The master engine adds `\ ; ^ @ ?` as name delimiters, clears only globals on bare `killvar`, and returns 0/1 from `OBJ` again | master | Do not depend on master behavior until it is released | VER 4 |
| 5.5 | Some documentation examples are wrong or version-specific: `\'` escapes do not exist, error numbers 101 and 120 are 5.7 numbers, `OBJ` is described as 1/0 | docs | Check the cross-reference before copying an example | DCR |
| 5.6 | Building Qqsp from Girl Life's bundled source fetches the engine's default branch, which Girl Life's start screen rejects | tools | Pin the engine tag when building Qqsp | OBS 10 |
| 5.7 | Girl Life's `qsp-cli` treats every bare argument as an input file; `qsp-cli in.txt out.qsp` also tries to decode `out.qsp` | tools | Pass only the input file | DEP 3 |

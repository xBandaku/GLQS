# Tests and examples

Executable sources of truth for QSP behavior, what they cover, and what they revealed. Commit hashes are in [source-index.md](../source-index.md).

## 1. qsp-wasm-engine test suite (5.9.5-era behavior)

**Location.** `tests/engine/*.test.ts` (26 files, 6,640 lines) and `tests/api/*.test.ts` (4 files). Framework: Vitest.

**How a test works.**
1. `prepareApi()` loads the WebAssembly engine.
2. `runTestFile(api, code)` wraps QSP code in a location named `test` and runs it; `runTestFileWithGoto` enters it with `GOTO`.
3. Assertions read variables (`readVariable`, `readVariableByIndex`, `readVariableByKey`) or check emitted events (`main_changed`, `stats_changed`, `actions_changed`, `error`, `msg`, `menu`, `system_cmd`, ...).
4. Every test fails if an unexpected `error` event fires (`afterEach`).

**Coverage by file.**

| File | Lines | Covers |
|---|---|---|
| `conditionals.test.ts` | 961 | `IIF`; every single-line and multi-line IF/ELSEIF/ELSE combination; comments after headers; errors for missing `end` or `:` |
| `arrays.test.ts` | 671 | Type overwrite in one element, `[]` append and last, string keys, `KILLVAR`, `COPYARR`, `ARRSIZE`, `ARRPOS`, `ARRCOMP`, `ARRITEM`, negative indices, tuple keys, `SORTARR` |
| `expressions.test.ts` | 582 | Every operator with numbers, strings and mixed types; error codes; priorities of `OBJ` and `LOC` |
| `locations.test.ts` | 520 | `GOTO`, `XGOTO`, `GOSUB`, `FUNC`, `@` shorthand, `ARGS`/`RESULT` restore, `ARGS` in actions after `GOTO` |
| `tuples.test.ts` | 503 | Tuple syntax, unpacking, indexing, operations, the 20-item limit |
| `variables.test.ts` | 427 | Defaults, case-insensitivity, `SET`/`LET`, multiple assignment, `LOCAL` in IF blocks and calls, `KILLVAR` with locals, locals vs actions, `$ONGSAVE` with `GOTO` |
| `objs.test.ts` | 366 | `ADDOBJ` positions, duplicates, `DELOBJ`, `KILLOBJ`, `$CUROBJS`, `$SELOBJ`, `COUNTOBJ`, `$GETOBJ`, `UNSEL` |
| `acts.test.ts` | 274 | `ACT` forms, duplicate names, `DELACT`, `$CURACTS` round trip, `$SELACT`, `CLA`, `CLS` |
| `strings.test.ts` | 237 | Comparison, nested subexpressions, `LEN`, `$MID`, `$UCASE`/`$LCASE` with Cyrillic, `$TRIM`, `$REPLACE`, `INSTR`, `ISNUM`, `VAL`, `$STR`, regex functions, `SCANSTR` |
| `menu.test.ts` | 230 | Menu building, separators, empty-item stop, selection arguments, colons in titles |
| `labels.test.ts` | 221 | `JUMP`, case-insensitive labels, label scope errors in actions and dynamic code |
| `system-locations.test.ts` | 188 | Every handler variable |
| `dynamic.test.ts` | 179 | `DYNAMIC`, `DYNEVAL`, quoting and expansion timing, `ARGS` isolation |
| `base-functions.test.ts` | 177 | `$QSPVER`, `$CURLOC`, `MAX`/`MIN` with arrays and holes, `RND`, `RAND` |
| `loop.test.ts` | 155 | `LOOP` semantics, local counters, `EXIT` and `JUMP` from loops |
| `main.test.ts`, `stats.test.ts` | 140, 101 | Output statements and implicit output |
| `time.test.ts` | 105 | `WAIT`, `MSECSCOUNT`, `SETTIMER`, multiple counters |
| `modules.test.ts` | 118 | `OPENQST`, `INCLIB`, `FREELIB`, `SAVEGAME`, `OPENGAME` |
| others | | sound, graphics, inputs, `MSG`, `EXEC`, debug hooks |

**Why it matters here.** The expected error codes (11 division by zero, 12 type mismatch, 17 missing `:`, 18 missing `end`, 29 unknown action) are the 5.9.5 numbering, so the suite documents 5.9.5 behavior. Some behaviors would change in master: unprefixed names became untyped and `KILLVAR` without arguments clears only globals. This reference cites individual tests by their titles.

**Notable assertions.**
- `$arr[1] = 'test'` then `arr[1] = 1` leaves `$arr[1] = ''` ("overriding string value with number").
- `arr[-1] = 234` writes nothing ("negative index").
- `$arr[1,3]` and `$arr['1,3']` are different elements ("tuple index collision").
- A `GOTO` does not clear the stats window (`locations.test.ts`, GOTO tests).
- `'2a' - '1'` raises type mismatch with `lineSrc: "RES = '2a' - '1'"` (the upper-cased line text).
- `(1 & 2)` stored in a number variable gives 12.
- `-7 mod 5` is -2.

## 2. qsp-legacy scenario tests (5.7 behavior)

**Location.** `tests/engine/*.qspt` (26 scenario files) with a C runner (`tests/runner/qsp_test_runner.c`), added 2026-10-08. Run with `cmake -B build -DQSP_LEGACY_BUILD_TESTS=ON`, then `ctest`.

The README says the scenarios are ported from the wasm suite and "adapted to the semantics of the 5.7 engine; every adaptation is commented in place with the original expectation". These comments are the most direct list of 5.7 differences found in this research:

| Area | 5.7 behavior recorded in the legacy tests | File |
|---|---|---|
| Single-line IF | No inline `ELSEIF`. `if x = 2: x = 3 elseif x = 2: x = 4` raises "Unknown action!"; with a false condition, only a trailing `ELSE` part runs | `conditionals.qspt:50-93` |
| Comment after a multi-line header | `if x = 0: ! comment` is a single-line IF, so the following lines always run and the lone `end` is ignored. The same holds for `elseif ...: !`, `else !` and `else: !` | `conditionals.qspt:605-680` |
| Comment after an `act` colon | Creates a single-line action whose code is the comment | `acts.qspt:133` |
| Action code | Kept as written, not upper-cased (affects `$CURACTS`) | `acts.qspt:75` |
| Array elements | Number and string kept side by side | `arrays.qspt:4, 15` |
| `ARRPOS`/`ARRCOMP` | Start index is the first argument; the search also checks the position after the last element | `arrays.qspt:2, 275-282` |
| `KILLVAR` | Numeric index only | `arrays.qspt:104, 114` |
| `MAX`/`MIN` on arrays | Empty strings are skipped; elements that hold only a string count as 0 for numeric searches | `base-functions.qspt:126-152` |
| `RAND 2` | Returns 0 to 2 | `base-functions.qspt:198` |
| Logical values | -1 for true | `expressions.qspt:2`, `base-functions.qspt:2` |
| `OBJ`/`LOC` priority | Lower than `=` | `expressions.qspt:927` |
| `$QSPVER` | No argument; returns the library version (no version callback) | `base-functions.qspt:4, 12` |
| `FUNC`/`DYNEVAL` without result as a statement | Prints an empty line | `locations.qspt:170`, `dynamic.qspt:83`, `main.qspt:79` |
| `GOSUB` | Restores `ARGS` but not `RESULT` | `locations.qspt:268` |
| `MENU` | No separators: `-:-` is an ordinary item named `-` | `menu.qspt:43` |
| Objects | No separate titles; `$CUROBJS` absent | `objs.qspt:2, 55` |
| Libraries | `ADDQST` and `KILLQST` | `modules.qspt:2` |
| Dialogs | No UI refresh before `MSG`, `INPUT`, `EXEC` | `msg.qspt:9`, `inputs.qspt:54`, `exec.qspt:9` |
| Not supported | `LOOP`, `LOCAL`, `@` calls, tuples, `ARRITEM`, `SORTARR` | `loop.qspt`, `arrays.qspt`, `locations.qspt` |

Scans of Girl Life and GLSS for the two parsing hazards in the first rows found no occurrences ([implementation-observations.md](../girl-life-analysis/implementation-observations.md)).

## 3. qsp-test-engine

A harness that loads a game into `@qsp/wasm-engine` and drives it from Vitest: `TestClient.start(basePath, gameFile, startingLocation)`, then select actions and assert on the main text and actions. Its mock games (`tests/mocks/*.qsps`) are small examples of the text format; they end locations with a single `-`.

## 4. Examples in the documentation

The keyword pages contain hundreds of examples. Most were checked indirectly through the matching engine code or wasm tests. Examples found to be wrong or version-specific:
- `$lcase('I DON\'T WANT TO SHOUT AT YOU.')` uses a backslash escape that QSP does not have.
- `iif(x = 0, 0, 1/x)` avoids division by zero only on 5.8+.
- The `OBJ` chapter's 1/0 result is wrong for 5.9.4 and 5.9.5, which return a count.
- Error numbers 101 and 120 are 5.7 codes.
- `GOSUB ... [argument 8]` is the 5.7 limit.

See [documentation-cross-reference.md](documentation-cross-reference.md).

## 5. gamekit

`contents/games/` holds sample games (Box, Bugs, DarkCastle and others) as binary `.qsp` files with music. They were not decoded or analyzed for this reference.

## 6. Girl Life tests

`test/testframework.qsrc` provides `testsetup` (a canned character and date) and assertions (`assertEqualsString`, `assertEqualsNumber`, `assertEqualsStringArray`) that return results through `RESULT`. `tools/testbuilder.py` builds a test game from a test-suite file (`test/testsuite-basic.qproj`, which lists two test locations). The framework sets `_ISTEST = 1` and defines `_TRUE = (0 ! 1)` and `_FALSE = (0 = 1)`. Details in [dependencies-and-configuration.md](../girl-life-analysis/dependencies-and-configuration.md).

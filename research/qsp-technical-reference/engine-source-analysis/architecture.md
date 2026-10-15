# QSPLib architecture

Structure of the QSP library at engine commit `00faed4` (master, 5.9.6 in progress), with notes where 5.9.5 or the 5.7 legacy library differ. File references are relative to `qsp/` in the engine repository.

## 1. Modules

| File | Lines | Responsibility |
|---|---|---|
| `bindings/qsp.h` | 191 | Public types: error codes, window flags, callback ids, value types (`QSPVariant`, `QSPString`, `QSPTuple`), `QSPErrorInfo` |
| `bindings/default/default_control.c` | 491 | Public API used by players (`QSPExecString`, `QSPExecuteSelActionCode`, `QSPSaveGameAsData` ...) |
| `bindings/default/default_callbacks.c` | 321 | Calls from the engine to the player through `QSP_CALL_*` |
| `bindings/java/*` | | Optional JNI binding |
| `declarations.h` | 160 | Special characters, delimiters, names of handler variables |
| `common.c` | 347 | Runtime init and teardown, `qspPrepareExecution`, random numbers, window state |
| `codetools.c` | 1,161 | Preprocessing source into lines and statements, label collection, keyword search, code block cache |
| `statements.c` | 1,130 | Statement table, line execution, IF, LOOP, JUMP, GOSUB/GOTO handlers, output statements |
| `mathops.c` | 1,650 | Expression compiler (to postfix) and evaluator, function table |
| `variant.c` | 531 | Type conversion, comparison, `+`/`&`/arithmetic on values |
| `tuples.c` | 216 | Tuple creation, comparison, text form |
| `variables.c` | 1,215 | Variable scopes, array indices, assignment, `LOCAL`, array statements |
| `locations.c` | 363 | Location table, lookup, `qspExecLocation`, `GOSUB`/`FUNC`/`GOTO` |
| `actions.c` | 212 | Current action list, `ACT`, `DELACT`, `$CURACTS` |
| `objects.c` | 499 | Inventory, object groups for `MODOBJ`, handlers |
| `menu.c` | 144 | `MENU` |
| `playlist.c` | 192 | Sound bookkeeping |
| `game.c` | 674 | Loading game files, `INCLIB`, restart, save and load of state |
| `coding.c` | 414 | Character encodings, the -5 string shift, value serialization |
| `regexp.c` | 88 | Oniguruma wrapper and regex cache |
| `text.c`, `text.h` | 322, 496 | String type, buffers, case mapping, number parsing and formatting, text search |
| `errors.c` | 100 | Error state and messages |
| `callbacks.c` | 63 | Callback mode bookkeeping |
| `time.c` | | Play-time counter |
| `memory.c` | 34 | Stack-like allocator for temporary argument arrays (added in 5.9.5) |
| `towlower.c`, `towupper.c` | 320, 368 | Generated Unicode case tables |

## 2. Core data structures

```c
/* bindings/qsp.h:136-159 */
typedef struct { QSPVariant *Vals; int ValsCount; } QSPTuple;
typedef struct { QSP_CHAR *Str; QSP_CHAR *End; } QSPString;   /* not NUL-terminated */
typedef struct QSPVariant_s {
    union { QSPString Str; QSP_BIGINT Num; QSPTuple Tuple; } Val;
    QSP_TINYINT Type;   /* UNDEF, TUPLE, NUM, BOOL, STR, CODE, VARREF */
} QSPVariant;
```

- Strings are pointer pairs, so substrings are free and many functions return views into existing text.
- `qspBaseTypeTable` maps BOOL to NUM, and CODE and VARREF to STR (`qsp.h:112-121`).

**Code** (`codetools.h`):
- `QSPCodeBlock` holds an array of `QSPLineOfCode` plus its labels and a reference count. A location's code, each base action's code, every `DYNAMIC` string and every single-line `act` body is a code block.
- `QSPLineOfCode` holds the upper-cased line text, its source line number, the statements found on it (`QSPCachedStat`), whether it opens a multi-line block, and cached distances to its matching `else` and `end` lines.
- `QSPCachedStat` holds the statement code, any parse error, and pre-split arguments (`QSPCachedArg`).
- A `QSPCachedArg` is empty, a literal number, a literal string, a code block literal, or an expression compiled on first use (`codetools.c:1141`).

**Expressions** (`mathops.h:49-57`): `QSPMathExpression` is a postfix array of `{OpCode, ArgsCount, ValueIndex}` items plus a value table. Evaluation walks backwards from the last item, finding each operand's sub-range with `qspSkipMathValue`.

**Variables** (`variables.h`):
- `QSPVar` has a dense `Values` array plus a hash table from string keys to positions.
- Scopes are open-addressing hash tables of `QSPVarSlot`.
- Local scopes are allocated in chunks of 128 and form a stack (`qspCurrentLocalVars`). The global scope is permanent (`qspGlobalVars`).

**World** (`locations.h`): an array of `QSPLocation` pointers plus a name hash table of upper-cased names. Each location has a name, a base description, its code block, base actions and a reference count. Locations are reference counted so code can keep running while `FREELIB` or a new game removes them.

**Screen state** (`common.h`): `qspCurDesc` (main text), `qspCurVars` (stats text), `qspCurInput`, `qspViewPath`, the current action array (`actions.h`, max 50) and objects (`objects.h`, max 1,000), plus `qspCurWindowsChangedState` flags.

## 3. Control state

| Global | Meaning |
|---|---|
| `qspLocationState` | Incremented by `GOTO`, errors, new game and load. Every executing frame saves it and stops when it changes (see [runtime-behavior.md](runtime-behavior.md)) |
| `qspCurLoc` | Location reached by the last `GOTO`/`XGOTO` (`$CURLOC`) |
| `qspRealCurLoc`, `qspRealActIndex`, `qspRealLineNum`, `qspRealLine` | Where code is actually executing, for error reports and the debugger |
| `qspCurLocCallDepth` | Nested location calls, limited to 2,000 |
| `qspIsInCallback` | True while the player is handling `MSG`, `INPUT`, `MENU`, `WAIT` and similar callbacks |
| `qspErrorNum`, `qspLastError` | Current error |

## 4. Pipeline from file to execution

```text
qspOpenGame (game.c:191)
  decode each location's name, description, code (coding.c)
  qspPreprocessData (codetools.c:958)         join continued lines, track quotes/brackets
    qspAppendLineToResult                      " _" continuation, upper-case outside strings
      qspInitLineOfCode (codetools.c:405)      split into statements, classify each one,
                                               pre-split arguments, mark multi-line headers
  qspNewCodeBlock                              collect labels

qspExecCode (statements.c:602)                 walk lines
  multi-line header -> qspExecMultilineCode    find else/end, recurse into body with a new scope
  otherwise         -> qspExecString           run statements left to right
     argument values -> qspCalculateArgValue   compile expression once, evaluate
       qspCalculateValue (mathops.c:1043)      postfix evaluation, short-circuit AND/OR/IIF
```

In 5.9.5 and earlier, code was preprocessed when a location was loaded too, but expressions were compiled and cached per string through a separate cache (`QSP_MAXCACHEDEXPSBUCKETSIZE` in 5.9.5 `mathops.h`). master compiles each argument once and stores it in the statement (commit `64a253d`, "Parse statements and compile expressions once at preprocessing").

## 5. Callbacks (engine to player)

From `bindings/qsp.h:53-76`:

| Callback | Used by |
|---|---|
| `QSP_CALL_DEBUG` | Debug mode, before each line |
| `QSP_CALL_ISPLAYINGFILE`, `PLAYFILE`, `CLOSEFILE` | `ISPLAY`, `PLAY`, `CLOSE` |
| `QSP_CALL_SHOWIMAGE` | `VIEW` |
| `QSP_CALL_SHOWWINDOW` | `SHOWACTS`, `SHOWOBJS`, `SHOWSTAT`, `SHOWINPUT` |
| `QSP_CALL_SHOWMENU` | `MENU` (returns the chosen index) |
| `QSP_CALL_SHOWMSGSTR` | `MSG` |
| `QSP_CALL_REFRESHINT` | Redraw after events, `REFINT`, before dialogs |
| `QSP_CALL_SETTIMER` | `SETTIMER` |
| `QSP_CALL_SETINPUTSTRTEXT` | `CMDCLEAR`, `CLS`, loading |
| `QSP_CALL_SYSTEM` | `EXEC` statement |
| `QSP_CALL_OPENGAME` | `INCLIB`, `OPENQST` (the player reads the file and calls back into the engine) |
| `QSP_CALL_INITGAME` | After restart or load, for player-side setup |
| `QSP_CALL_OPENGAMESTATUS`, `SAVEGAMESTATUS` | `OPENGAME`, `SAVEGAME` (the player handles file dialogs and I/O) |
| `QSP_CALL_SLEEP` | `WAIT` |
| `QSP_CALL_GETMSCOUNT` | `MSECSCOUNT` and the save timestamp |
| `QSP_CALL_INPUTBOX` | `$INPUT` |
| `QSP_CALL_VERSION` | `$QSPVER` |

The engine does no file I/O itself. Paths given to `INCLIB`, `OPENQST`, `PLAY`, `VIEW`, `OPENGAME` and `SAVEGAME` are passed to the player.

## 6. Bindings and consumers

- **Default binding** (C API, `bindings/default/qsp_default.h`): used by the classic player, Qqsp, and the WebAssembly build (`qsp-wasm-engine/src/qsplib/src/qsp_wasm.c`, 436 lines of glue exporting the API to JavaScript).
- **Java binding** (`bindings/java/`): JNI wrapper with `QSPLib.java`; used by Android players.
- **Character width**: `QSP_CHAR` is `wchar_t` in Unicode builds, which is 2 bytes on Windows and 4 bytes on Linux, Android and macOS. Game files are always UCS-2; `coding.c` converts.

## 7. Legacy 5.7 architecture differences

- One fixed table of 12,800 variables (`legacy: src/variables.h:24-25`); each array element stores a number and a string side by side.
- No local scopes; only `ARGS` (and `RESULT` for `FUNC`) are saved and restored around calls.
- The expression evaluator is a stack machine that evaluates every operand (`legacy: src/mathops.c:394`).
- Preprocessing happens in two passes: join quoted strings and `{}` blocks across lines, then join ` _` continuations (`legacy: src/codetools.c:103`, `:184`).
- Labels are stored per line (`QSPLineOfCode.Label`) instead of a per-block table.

# Implementation details

How the engine implements the rules described in the official-documentation pages. Each section names the function, explains the algorithm, and lists behavior that follows from it but is not documented. Engine references are to commit `00faed4` unless marked 5.9.5 or legacy.

## 1. Preprocessing (`codetools.c:958`, `qspPreprocessData`)

Input: the decoded code of a location, base action, `DYNAMIC` string or link.

1. **Character scan with state.** The scanner tracks:
   - `quote`: the open quote character, or none;
   - `codeBrackets`: `{}` depth;
   - `roundBrackets`, `squareBrackets`: `()` and `[]` depth outside comments;
   - `isComment`: a `!` was seen at statement start;
   - `isStatementStart`.
2. **Newlines.** A newline ends the logical line only when no quote, `{}`, `()` or `[]` is open. Otherwise the newline is kept inside the line's text.
3. **Comments.** A `!` at statement start sets `isComment`; after that, `()` and `[]` stop counting but quotes and braces still count. The quote branch is checked before the comment branch, which is why an apostrophe inside a comment opens a string.
4. **Continuation.** When a logical line ends, `qspAppendLineToResult` (`:924`) checks whether the accumulated text ends with a space or tab followed by `_`. If so, it drops the `_`, keeps the space, and continues with the next line.
5. **Normalization.** Leading and trailing spaces are trimmed (`qspDelSpc`). Everything outside quotes and `{}` is upper-cased (`:900`).
6. **Statement split** (`qspInitLineOfCode`, `:405`):
   - The first statement keyword is found by prefix search in three sorted name tables, tried in order (`statements.c:103`, `codetools.c:43`). Names that start with another keyword sit in an earlier table so the longer name wins: `PLAY` before `PL`, `ELSEIF` before `ELSE`, `*PL` before `*P`, `SETVAR` and `SETTIMER` before `SET`, `CLOSE ALL` before `CLOSE`, `UNSELECT` before `UNSEL`. A keyword marked isolated must be followed by a delimiter; if it is not, the next table is tried.
   - For `if`, `elseif`, `act` and `loop`, the statement ends at the first `:` outside quotes and brackets.
   - For other statements it ends at the first `&`, or earlier at an isolated `ELSE`/`ELSEIF` keyword (this is how single-line IF finds its else part).
   - An unknown statement with an `=` before the separator is an assignment, otherwise an implicit output statement.
   - `ELSE` followed by `IF` on a multi-line header becomes `ELSEIF`.
7. **Argument pre-split.**
   - Simple literals (numbers, quoted strings without doubled quotes or `<<`, `{}` blocks) are stored ready to use.
   - Other arguments are compiled on first evaluation and kept (`codetools.c:1141`).
   - Errors found while splitting are stored in the statement and raised only when it runs.
8. **Labels** (`:728`) are collected per code block into a table of upper-cased names and line indices.

**Not documented, follows from the code.**
- Syntax errors are reported only when the faulty line executes. A location with an error in an unused branch loads and runs fine.
- The upper-casing step also applies to `<<...>>` subexpression text once it is extracted (`qspFormatText`, `qspAppendFormatToCompiled` call `qspPrepareStringToExecution`), so names inside subexpressions are case-insensitive too.
- Because `{}` content is not upper-cased, code stored in `{}` keeps its case until it runs, and `$CURACTS` of a `DYNAMIC`-created action shows the upper-cased form of that code.

**Legacy 5.7** (`legacy: src/codetools.c:103-212`): two passes. The first joins lines only inside quotes and `{}`; parentheses never join lines. The second joins ` _` continuations.

## 2. Expression compiler (`mathops.c:567`, `qspAppendExpressionToCompiled`)

A shunting-yard compiler producing postfix code.

- **Operands.**
  - Digit sequences become number values, with a pending unary minus folded in.
  - Quoted strings become string values, or a format operation if they contain `<<`.
  - `{...}` becomes a CODE value.
  - `?` (master) becomes an undefined value.
  - A name is looked up in the function table. Otherwise it is a variable reference: `name[...]` becomes an indexed read, `name[]` the last element, `name` element 0.
- **Function calls.**
  - `name(` pushes the function and an open bracket.
  - A function with at most one required argument may omit the bracket, and its argument is the next operand.
  - Argument counts are checked at the closing bracket ("Incorrect arguments count!").
- **Tuples.** `[`...`]` always builds a tuple. `(`...`)` builds one only when it contains a comma at that level or is empty; `("a")` is just a grouped value (wasm test "nested single item in parenthesis will not create a tuple"). A comma at the top level of an expression also builds a tuple, which is how multiple assignment receives its values.
- **User calls.** `@name(...)` pushes the location name as a string value followed by a `FUNC` operation.
- **Limits.** Operator stack depth 30 (`QSP_MATHSTACKSIZE`), 1,000 items per expression in master, 200 in 5.9.5 ("Expression too complex!").
- **Keyword operators.** `AND`, `OR` and `MOD` must be followed by a delimiter, or the compiler raises "Syntax error!" (`:589-597`). This prevents names like `ORDER` from being read as `OR DER`.

**Evaluation** (`qspCalculateValue`, `:1043`): evaluates the item at the end of the postfix array. For most operations it evaluates each argument in order, converts it to the operation's argument type (raising "Type mismatch!" on failure), then runs the operation. `AND`, `OR`, `NO`, `IIF`, indexed array reads and the string format operation evaluate their arguments themselves, which gives short-circuiting and lets an index expression run before the array is looked up.

## 3. Variables

### Lookup (`variables.c:373`, `qspVarReference`)

1. Strip the type prefix and validate the name (`variables.h:122`).
2. Hash it with FNV-1a, folded (`text.h`, `qspGetTextHash`).
3. Probe every local scope from newest to oldest, then the global scope. Each scope is an open-addressing table with linear probing, capacity a power of two, resized at half full.
4. If absent and the caller is writing, create the name in the global scope (limit 100,000) or, for `LOCAL`, in the newest local scope (limit 500).

In 5.9.5 the same walk used chained buckets: 512 global and 16 local buckets with at most 32 names each, hash `h = h*31 + (low byte of char)` starting at 7 (`engine-5.9.5: qsp/variables.c:86-93`). In 5.7 a single table of 256 buckets times 50 slots used an 8-bit Pearson hash (`legacy: src/variables.c:149-185`).

### Array elements and keys (`variables.c:544`, `qspGetVarIndex`)

- Undefined index: position 0.
- Number: used as the position.
- Anything else: converted to an index key string, upper-cased, and looked up in the array's key hash table. A missing key gets the next position when writing.
- Key strings encode the type: `$` + text for strings, `#` + digits for numbers inside tuples, the item count plus separators for tuples, `?` for undefined (`variant.c`, `qspAppendVariantToIndexString`). So `a['5']`, `a[5]` and `a[[5]]` are three different elements.
- Removing an element (`KILLVAR name, index`) shifts the dense array down, decrements every key position after it, and deletes the removed key with backward-shift deletion in the hash table (`variables.c:472-525`).

### Assignment (`variables.c:743`, `qspSetVarValue`)

1. Resolve target and index. The index expression is evaluated before the variable is looked up, because the index code can create or remove variables.
2. For `+=`, `-=`, `*=`, `/=`, read the current value with the target's prefix and combine.
3. Convert to the target prefix type, or raise "Type mismatch!".
4. Create the key only after the conversion succeeds, so a failed assignment does not leave an empty key behind.

### Scopes (`variables.h:192-225`)

`qspAllocateLocalScope` pushes a scope; `qspReleaseLastLocalScope` pops it, clearing variables but keeping small buffers for reuse. A `GOTO` discards the whole stack (`locations.c:342`). Each player event starts with an empty stack (`common.c:84`).

## 4. Locations and calls

- Location names are stored as given and indexed upper-cased (`locations.c:133`, `qspAddLocation`). Lookup trims and upper-cases (`:171`).
- `qspExecLocation` (`:225`) checks call depth, records the executing location for errors, optionally clears the main text, adds base description and actions (both through `qspFormatText`, so `<<...>>` in them expands at entry), then runs the code.
- Handler arrays (`:307`, `qspExecLocByVarNameWithArgs`) save the local stack, run each listed location with globals only, and restore the stack. They re-read the handler variable on each iteration, so a handler can change the list for the following entries.

## 5. Actions and objects

- Actions keep a reference to their code block and a start and end line within it. A multi-line `act` inside a location shares the location's code block (`actions.c:69`, `qspStatementMultilineAddAct`). Single-line `act` code is turned into its own one-line block on first use (`codetools.c:776`).
- The action search for duplicates and `DELACT` upper-cases both names and compares them (`actions.c:41`).
- Objects are a list plus a sorted array of "groups", one per distinct upper-cased name, holding the object count and any `MODOBJ` title and image (`objects.c`). `OBJ`/`COUNTOBJ` read the group count with a binary search, which is why `OBJ` is cheap even with many objects.

## 6. Regular expressions (`regexp.c`)

Oniguruma, Perl_NG syntax, encoding UTF-16 or UTF-32 according to `sizeof(QSP_CHAR)` and byte order (`bindings/default/qsp_default.h:20-22`). A round-robin cache keeps the last 10 compiled patterns by text.
- `STRCOMP` uses `onig_match` from position 0 and requires the match to cover the whole string.
- `STRFIND`, `STRPOS`, `SCANSTR` and `ARRCOMP` use `onig_search`. `ARRCOMP` then needs a full match of the element.

## 7. Random numbers (`common.c:138-191`, `:278`)

- **Generator.** Additive lagged Fibonacci generator with lags 24 and 55 (`qspRandX[55]`), filtered through a 256-entry shuffle table (`qspRandY`).
- **Seeding.** `qspSetSeed(time)` on every restart.
- **Uniform values.** `rand() % (max - min + 1) + min`.
- **Mode.** `RAND(a, b, mode)` uses `qspNormalRand` (`common.c:278`). It uses a normal distribution with mean `mode` and sigma equal to one third of the larger distance from `mode` to either bound (`QSP_NORMAL_SCALE 3.0`). It draws inside `[a, b]` by inverse CDF, maps the result to integer bins, and clamps it. When `mode` lies outside the range only one tail is sampled, so the nearest bound is the most likely value, which matches the docs' examples. The source cites Botev and L'Ecuyer on sampling from normal tails.

The generator state is not saved, so reloading a save does not repeat the same random sequence.

## 8. Serialization (`coding.c`, `game.c`)

- Integers are written as decimal text, then encoded with the same -5 shift as strings.
- Values are written as type id plus payload; tuples recursively with their item count (`coding.c:340`, `qspAppendEncodedVariant`).
- Saves are always UCS-2 (`QSPSaveGameAsData` passes `isUCS = TRUE`).
- If the player's buffer is too small, the API returns the needed size plus 8,192 bytes of slack, so a second call with that buffer succeeds even if handlers changed the state meanwhile (`default_control.c`, `QSP_SAVEDGAMEDATAEXTRASPACE`).

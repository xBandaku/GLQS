# Variables and data types

How QSP stores values, how type prefixes work, how arrays are indexed, and how scope works. Version tags: **5.7** legacy library, **5.9.5** release used in the 2026-10-14 research snapshot, **master** unreleased engine `00faed4`. References follow [source-index.md](../source-index.md).

## 1. Value types

| Type | Prefix | Literal | Default (empty) value | Since |
|---|---|---|---|---|
| Number | none, or `#` | `123` | `0` | all versions |
| String | `$` | `'text'`, `"text"`, `{text}` | `''` | all versions |
| Tuple | `%` | `[1, 'a']`, `(1, 'a')`, `1, 'a'` in assignments | `[]` | 5.9.0 |
| Undefined | none | `?` | acts as the empty value of whatever type it meets | master only |

Internal types that scripts never name directly (`engine: qsp/bindings/qsp.h:78-89`): BOOL (results of comparisons and logic, stored as a number 0 or 1), CODE (`{...}` text and the results of `$CURACTS`/`$CUROBJS`), VARREF (a string that names a variable, used for array-name arguments).

- **Numbers** are 32-bit signed integers in default builds (`QSP_BIGINT` is `int` unless `QSP_USE_BIGINT` is defined; no build file defines it). Division truncates toward zero (C `/`), `MOD` takes the sign of the dividend (C `%`). The engine does not check arithmetic overflow, so the result is whatever the compiler produces for signed `int` overflow (normally wraparound, but C does not guarantee it). Only number literals and string-to-number conversion clamp to the maximum (`text.h`, `qspParseUnsignedNumber`).
- **Strings** are UTF-16 or UTF-32 code unit sequences depending on the platform `wchar_t` (`bindings/default/qsp_default.h:16`). `LEN` counts code units. Girl Life's Android Qqsp build patches the engine to 2-byte characters (`girl-life: tools/Qqsp-Src/CMakeLists.txt:53-63`).
- **Tuples** hold up to 20 items per literal (`QSP_MAXMATHOPARGS 20`; "Incorrect arguments count!" beyond that). Longer tuples are built by concatenation: `%t = (%t & [21, 22])` (blog 2026-01-01; wasm test `tuples.test.ts` "can grow over 20 elements with concatenation"). Tuples nest.

## 2. Storage model: one name, one array

Every variable is an array. `x` means element 0 of array `X`. The prefix is not part of the name.

**5.8.0 and newer.** The engine strips the prefix before looking the name up (`engine: qsp/variables.h:122`, `qspPrepareVarName`), so `x`, `$x`, `%x` and `#x` are the same array. Each element holds exactly one value with its own type (`QSPVariant`, `bindings/qsp.h:150`). Writing `$a[1]` after `a[1]` replaces the number with the string.

**5.7.** Each element has a number field and a string field side by side (`legacy: src/variables.h:28-32`, struct `QSPVarValue { int Num; QSP_CHAR *Str; }`). `a[1] = 5` and `$a[1] = 'x'` coexist.

**Why this matters.** Code that stored a name and a number under the same index, which was a common 5.7 idiom, loses one of them on 5.8+. The blog post calls this "one of the largest changes". The wasm tests pin the 5.9 behavior:

```qsp
$arr[1] = 'test'
arr[1] = 1
! $arr[1] is now '' and arr[1] is 1
```

(`wasm: tests/engine/arrays.test.ts`, "overriding string value with number").

**Girl Life.** A scan of literal assignments found 30 (name, key) pairs written with both `$` and no prefix somewhere in the code. Most are temporaries such as `temp`, `tmp`, `x` used in unrelated places. The non-trivial ones are save migrations written to be safe on both engines, for example `girl-life: locations/saveupdater.qsrc:5474` converting the old numeric `sex_ev['cum_choice']`. Details in [implementation-observations.md](../girl-life-analysis/implementation-observations.md).

## 3. What a type prefix does

### Writing

The value is converted to the type the prefix asks for (`engine: qsp/variables.c:743`, `qspSetVarValue`, and `variant.c:184`, `qspConvertVariantTo`):

| Target | Source value | Result |
|---|---|---|
| `$x` | number `5` | `'5'` |
| `$x` | tuple `[1,'a']` | `"[1,'a']"` (tuple text form, `tuples.c:185`) |
| `x` (5.9.5) or `#x` | string `'42'`, `' -7 '` | 42, -7 (spaces and a sign are allowed, `text.c:184`) |
| `x` (5.9.5) or `#x` | string `''` | 0 (empty string converts to 0) |
| `x` (5.9.5) or `#x` | string `'abc'` | error "Type mismatch!" (code 12 in 5.9.5) |
| `x` (5.9.5) or `#x` | tuple of one convertible item | that number; `[]` converts to 0; longer tuples are a type mismatch (`tuples.c:40`) |
| `%x` | number or string | a one-item tuple |
| `x` (master, no prefix) | anything | stored as is |

In 5.9.5 a name without a prefix is a number variable (`engine-5.9.5: qsp/variables.c`, `qspInitVarTypes` sets every non-prefix character to NUM). In master, a name without a prefix is untyped and keeps whatever value it receives (commit `d938a28`, 2026-10-13, "Support universal type prefix (no prefix)"). The docs describe the 5.9.5 behavior ("If you don't specify the dollar sign ... this will cause error #101").

### Reading

When the stored value's type does not match the prefix, the engine returns the empty value of the requested type. It does not convert and does not raise an error (`engine: qsp/variables.c:604`, `qspGetVarValueByReference`).

| Stored | Read as | 5.9.5 result | master result |
|---|---|---|---|
| `5` | `$x` | `''` | `''` |
| `'5'` | `x` | `0` | `'5'` (no prefix returns the raw value) |
| `'5'` | `#x` | `0` | `0` |
| `[1,2]` | `x` | `0` | `[1,2]` |

The docs state the same rule for `$` and `%` (syntaxemes page). Note that a numeric-looking string read without a prefix gives 0 in 5.9.5, not the number.

## 4. Array indexing

**Syntax and semantics** (`engine: qsp/variables.c:544`, `qspGetVarIndex`; `:579`, `qspGetVarData`):

| Form | Meaning |
|---|---|
| `a` | element 0 |
| `a[n]` | element at position `n` (number) |
| `a['key']` | element mapped to the string key; keys are upper-cased, so case does not matter |
| `a[1, 2]` or `a[[1, 2]]` | element mapped to a tuple key (5.8.0+) |
| `a[]` on the left of `=` | append a new element at position `ARRSIZE` |
| `a[]` in an expression | the last element |

- A string or tuple key is turned into an internal key text with a type tag (`variant.c`, `qspAppendVariantToIndexString`: `$` + text for strings, `#` + digits for numbers inside tuples). So `a['5']` and `a[5]` are different elements, and `a[1,3]` differs from `a['1,3']` (wasm test "tuple index collision").
- A new key gets the next free position (`ARRSIZE` at the time of creation). Keyed and positional elements share one sequence, and `ARRSIZE` counts both.
- Writing past the end fills the gap with undefined values. Reading a missing position returns the empty value.
- A negative numeric index reads as empty and writes are ignored (wasm test "negative index"; `variables.c:685` only writes when `ind >= 0`).
- `KILLVAR 'a', i` removes the element and shifts later positions down by one. String keys that pointed past `i` are renumbered (`variables.c:501`). In 5.7, `KILLVAR` only accepts a numeric index; deleting by string or tuple key arrived in 5.8.0 (blog 2026-01-01).
- In 5.7 there is no way to delete an element by string key. Girl Life works around it in `array.qsrc` by writing a sentinel value and finding its position with `ARRPOS` ([code-examples.md](../girl-life-analysis/code-examples.md)).

**Docs example.**

```qsp
$mass["x:4,y:6"] = "map-dot"
$mass[4, 6] = "map_cell"
$mass[] = "last_cell"
```

## 5. Scope

### Global and local

- Variables are global unless declared with `LOCAL` (5.8.0+).
- Lookup walks the stack of local scopes from newest to oldest, then the global scope (`engine: qsp/variables.c:373`, `qspVarReference`). This is dynamic scoping: a local declared in a location is visible to every location it calls with `GOSUB` or `FUNC`, and to `DYNAMIC` code, as the docs show with the `foo`/`undo` example.
- A new name that is not found anywhere is created in the global scope.

### Where scopes begin

| Construct | New scope | Source |
|---|---|---|
| `GOSUB`, `FUNC`, `@`, `@@` | yes, with its own `ARGS` and `RESULT` | `locations.c:288`, `variables.c:323` |
| `DYNAMIC`, `DYNEVAL` | yes, with its own `ARGS` and `RESULT` | `statements.c`, `qspExecStringAsCodeWithArgs` |
| `GOTO`, `XGOTO` | all locals are discarded, then one scope for the location code | `locations.c:342` |
| An action's code, a link's `EXEC:` code | yes, on top of an empty stack (globals only) | `actions.c:91`, `statements.c`, `qspExecStringAsCode` |
| `LOOP` | one scope for the whole loop, plus a fresh one for each pass of the body and the step | `statements.c:820`, `:864` |
| Each branch of `IF`/`ELSEIF`/`ELSE` | yes | `statements.c:742` and `qspExecMultilineCode` |
| Every player event (click, counter tick, input) | all locals are cleared first | `common.c:84`, `qspPrepareExecution` |

The docs list locations, dynamic code, hyperlinks, actions and loops as places where locals can live. They do not say that IF branches are scopes too, but both 5.9.5 and master allocate one per branch, and the wasm test "local without assignment" relies on it:

```qsp
a, $b, c = 1, 'old', 2
if 1:
  local a, $b, c
  a_new, $b_new, c_new = a, $b, c
end
! a_new = 0, $b_new = '', c_new = 0; a, $b, c keep 1, 'old', 2
```

### Limits

| Engine | Globals | Locals per scope | Mechanism |
|---|---|---|---|
| master | 100,000 | 500 | open addressing hash table (`variables.h:16-17`) |
| 5.9.5 | at most 32 per hash bucket, 512 buckets (16,384 total in theory) | 32 per bucket, 16 buckets | chained buckets (`engine-5.9.5: qsp/variables.h`, `QSP_VARSGLOBALBUCKETS 512`, `QSP_MAXVARSBUCKETSIZE 32`) |
| 5.7 | at most 50 per hash bucket, 256 buckets (12,800 total in theory) | no locals | fixed table, 8-bit Pearson hash (`legacy: src/variables.h:24-25`, `legacy: src/variables.c:149`) |

Exceeding a bucket raises "Too many variables!". In 5.7 `KILLVAR 'name'` empties the array but leaves the name in its slot (`legacy: src/variables.c:83`, `qspEmptyVar` does not clear `Name`), so a slot is only freed by `KILLVAR` without arguments, `KILLALL` or a new game.

A simulation of both hash functions over the 8,489 distinct variable names that Girl Life assigns by literal name puts 28 names into the fullest 5.9.5 bucket (limit 32) and 55 into the fullest 5.7 bucket (limit 50); one 5.7 bucket exceeds its limit and the next fullest holds exactly 50. These names do not all exist at the same time, and names built at run time are not counted, so this shows the margin, not a confirmed failure. See [implementation-observations.md](../girl-life-analysis/implementation-observations.md).

## 6. ARGS and RESULT

**ARGS.**
- `GOSUB`, `FUNC`, `@`, `@@`, `DYNAMIC` and `DYNEVAL` put their extra arguments into `ARGS[0]`, `ARGS[1]`, ... of the new scope. Up to 19 arguments in 5.8+ (`QSP_MAXSTATARGS 20` including the location or code), up to 9 in 5.7 (`legacy: src/statements.c:141`, max 10 arguments).
- `GOTO`/`XGOTO` write their arguments into the global `ARGS` (`locations.c:342`, comment "We assign global ARGS here"). Because actions and link code run with no locals, they see that global `ARGS`. This is why the docs say actions use the `ARGS` of the location reached by `GOTO`.
- `ARGS` is an ordinary array otherwise. You can assign more elements or string keys.

**RESULT.**
- In 5.8+ each call scope gets its own `RESULT`. `FUNC`/`DYNEVAL` return `RESULT` element 0 in whatever type it holds, or nothing if it was never set (`variables.c:348`, `qspApplyResult`).
- `$result`, `result` and `%result` are the same variable; the last assignment wins.
- 5.7: `FUNC` and `DYNEVAL` save and restore the caller's `RESULT` (`legacy: src/mathops.c:1131`), but `GOSUB` does not isolate it, so a `GOSUB` that sets `result` overwrites the caller's value. The docs mention "a small problem with value intersection in result" for 5.7.0. When `RESULT` was never set, 5.7 `FUNC` returns an empty string.
- If a function location never sets `RESULT`, 5.8+ `FUNC` returns no value: inside an expression it acts as the empty value of the needed type; as an implicit statement it prints nothing.

**Girl Life.** Every utility function follows the pattern `result = ...` or `$result = ...` then `exit` (for example `girl-life: locations/shortgs.qsrc:100-104`). Since 5.7 has no locals, functions keep their working values in prefixed globals and clear them with `killvar` before returning ([scripting-patterns.md](../girl-life-analysis/scripting-patterns.md)).

## 7. System variables are arrays too

`$COUNTER`, `$ONNEWLOC` and the other handler variables can hold several location names. The engine calls each name in turn until it meets an empty or non-string element (`engine: qsp/locations.c:307`, `qspExecLocByVarNameWithArgs`), matching the docs' "Notes for the Curious". Girl Life stores debug flags under string keys of `DEBUG` (`debug['trace_loc_change']`, `girl-life: locations/LOCA.qsrc:3`); the engine reads only element 0 of `DEBUG`, so the extra keys do not affect the save check.

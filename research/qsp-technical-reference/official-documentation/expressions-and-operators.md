# Expressions and operators

Operator priority, evaluation order, type rules for each operator, comparison rules, truthiness and subexpressions. Version tags: **5.7**, **5.9.5**, **master** as in [source-index.md](../source-index.md).

## 1. Priority

Higher numbers bind tighter. Operators with equal priority group left to right.

| Priority | 5.9.5 and master | 5.7 |
|---|---|---|
| 4 | | `&` (concatenation) |
| 6 | `OR` | `OR` |
| 7 | `AND` | `AND` |
| 8 | `NO` | `NO`, `OBJ`, `LOC` |
| 10 | `=` `<` `>` `!` `<>` `<=` `>=` `=<` `=>` | same comparisons |
| 11 | `OBJ`, `LOC` | |
| 12 | `&` (concatenation) | |
| 14 | `+`, `-` | `+`, `-` |
| 16 | `MOD` | `MOD` |
| 17 | `*`, `/` | `*`, `/` |
| 18 | unary `-` (and unary `+` in master only) | unary `-` |
| 30 | every function | every function |
| 127 | `( )` | `( )` |

Sources: `engine: qsp/mathops.c:167` (`qspInitMath`), grammar comment in `help/qsp_grammar.peg:431-446`, `legacy: src/mathops.c:134-195`. The docs' table for 5.8.0 matches the 5.9.5 column. The docs' 5.7.0 table lists `&` first (lowest), then `OR`, `AND`, then `OBJ`/`LOC`/`NO` together, matching the legacy source.

**Consequences.**
- `obj 'a' = obj 'b'` compares two object checks in 5.8+, but in 5.7 it parses as `obj ('a' = obj 'b')` and is always 0 (blog 2026-01-01). The wasm test "OBJ priority" asserts the 5.9 reading. Parenthesize for portability: `(obj 'a') = (obj 'b')`.
- `no a = b` is `no (a = b)` in every version.
- In 5.7, `'a' & 'b' = 'ab'` concatenates last, so the comparison binds first.
- Unary plus: the docs mark it as removed after 5.7.0. 5.9.5 has no unary plus operator. master parses `+x` again (`qspOpAffirmation`, `mathops.c:766`, commit `73d4527` "Support unary \"+\"").

## 2. Evaluation order and short-circuiting

- **5.9.5 and master.** `AND`, `OR`, `NO` and `IIF` do not evaluate their operands in advance (`engine: qsp/mathops.c:1073-1126`, comments "we don't pre-evaluate arguments"). `AND` skips its right side when the left is false, `OR` skips it when the left is true, and `IIF` evaluates only the chosen branch. All other operators and functions evaluate every argument left to right before running.
- **5.7.** The evaluator is a stack machine that computes every operand first (`legacy: src/mathops.c:394`, `qspValue`). Nothing short-circuits, and `IIF` evaluates both branches (`legacy: src/mathops.c:526`, `qspCopyVariant(&tos, QSP_NUM(args[0]) ? args + 1 : args + 2)` after both were computed).

The docs' example `y = iif(x = 0, 0, 1/x)` "will NOT cause division by zero" is true for 5.8+ and false for 5.7, where it raises "Division by zero". Outside string literals, Girl Life has 56 `iif` calls with `func(...)` in a result branch and 42 with `rand(...)` in a result branch. On 5.7 both branches run, which costs extra calls and consumes extra random numbers ([implementation-observations.md](../girl-life-analysis/implementation-observations.md)).

## 3. Arithmetic operators

### `+` (addition and concatenation)

**Syntax.** `[expr] + [expr]`

**Semantics** (`engine: qsp/variant.c:31`, `qspSumSimpleVariants`; 5.7 `legacy: src/mathops.c:451-474`):

| Left | Right | Result |
|---|---|---|
| number | number | sum |
| string | string | concatenation, even when both look numeric (`'1' + '2'` is `'12'`) |
| number | numeric string | sum (`1 + '2'` is 3) |
| number | other string | concatenation (`'splash' + 5` is `'splash5'`) |
| tuple | anything | applied to each tuple item (see section 7) |

The same rules hold in 5.7. The mixed case is the trap: `n + '0'` adds zero instead of appending a digit. Girl Life builds image paths this way safely because the string part is never numeric (`'.../splash' + rand(1, 30) + '.jpg'`, `girl-life: locations/start.qsrc:47`).

### `-`, `*`, `/`, `MOD`

- Both sides are converted to numbers. A string that is not a number raises "Type mismatch!" (code 12 in 5.9.5). The wasm tests assert this for `'2a' - '1'`, `-'2a'` and `'2a' / '1'`.
- `/` is integer division truncating toward zero: `17 / 5` is 3, `-4 / 2` is -2. Division by zero raises "Division by zero!" (code 11 in 5.9.5).
- `MOD` uses C `%`: the sign follows the dividend. wasm tests: `-7 mod 5` is -2, `7 mod -5` is 2. `x mod 0` raises "Division by zero!" (`mathops.c:1186-1191`).
- `MOD` must be separated from its operands by delimiters. `amod b` is a name, not an operation (`mathops.c:589-597` raises "Syntax error!" when `AND`, `OR` or `MOD` is followed by a non-delimiter).

### Compound assignment `+=`, `-=`, `*=`, `/=`

`x op= v` reads `x` with its own prefix, combines with the same rules as the binary operator, then assigns back with conversion (`variables.c:743`). `$s += 'x'` appends; `n += '5'` adds 5. With a tuple on the right and a non-tuple target, the result is a tuple that cannot be stored in a number or string variable, so the docs note "data type mismatch" for `number += [4,5]`.

### Unary minus

`-expr` converts the operand to a number (so `-'2'` is -2) or negates each item of a tuple (`variant.c`, `qspMultiplyVariantByNum`). A minus sign directly before a digit is folded into the literal at compile time (`mathops.c:705-710`).

## 4. Comparison operators

**Syntax.** `=`, `<>`, `!`, `<`, `>`, `<=`, `>=`, `=<`, `=>`. `!` and `<>` are the same operation; `=<` and `=>` are aliases of `<=` and `>=`.

**Result.** 1 or 0 in 5.8+. -1 or 0 in 5.7 (`legacy: src/mathops.c:489-495`, `QSP_NUM(tos) = -(...)`).

**Rules** (`engine: qsp/variant.c:249`, `qspVariantsCompare`):

| Operands | How they compare |
|---|---|
| number, number | numerically |
| string, string | code unit by code unit, case-sensitive; a prefix is smaller than the longer string (`text.h:308`) |
| number, string | if the string converts to a number, numerically; otherwise the number is formatted and compared as text |
| tuple, tuple | item by item; a shorter tuple that matches so far is smaller |
| tuple, number or string | the first item is compared with the value; if equal and the tuple has more items, the tuple is bigger |
| undefined (master) | treated as the empty value of the other operand's type |

Examples from the docs and tests:

```qsp
'z' > 'az'      & ! 1
'123' > '92'    & ! 0, text comparison
'123' > 92      & ! 1, numeric comparison
"a" > "A"       & ! 1, lower case letters have higher codes
("a" = "A")     & ! 0
[1, 2] > [1]    & ! 1
```

**`=` as comparison vs assignment.** At the start of a statement, `name = value` is an assignment. To print or test a comparison at statement level, wrap it: `(alukard = 1000)`. `"abc" = "abc"` alone is a syntax error ("Incorrect variable name!") because the engine tries to assign to `"abc"`. After a statement keyword (`if`, `*pl`) the expression is parsed normally.

**5.7 string comparison.** Unicode builds of the legacy library also compare code units (`legacy: src/bindings/default/qsp_default.h:34`, `QSP_STRCOLL qspStrsComp`). The single-byte builds use CP1251 or KOI8-R ordering tables.

## 5. Logical operators

| Operator | 5.8+ | 5.7 |
|---|---|---|
| `a AND b` | 1 if both operands are true, else 0; right side skipped when left is false | bitwise AND of the two numbers (`3 and 2` is 2) |
| `a OR b` | 1 if either is true, else 0; right side skipped when left is true | bitwise OR (`4 or 6` is 6) |
| `NO a` | 1 if `a` is false, else 0 | bitwise NOT (`no 7` is -8, `no -1` is 0) |

Sources: `engine: qsp/mathops.c:1073-1116`; `legacy: src/mathops.c:516-524`. In 5.7, conditions still work as long as operands are 0 or -1, which is what 5.7 comparisons return. Code that used `AND`/`OR` to compute bit masks breaks on 5.8+ (blog 2026-01-01).

**Truthiness.** A condition is converted to a boolean (`variant.c:170`, `qspGetVariantAsBool`):

| Value | 5.9.5 and master | 5.7 |
|---|---|---|
| number | true if not 0 | true if not 0 |
| string | true if not empty | converted to a number; empty is 0; non-numeric text raises "Type mismatch!" (`legacy: src/statements.c:126`, IF takes a number argument) |
| tuple | true if it has at least one item | not available |

Portable conditions on strings compare explicitly: `if $name <> '':`. Girl Life follows this; a search found no `if $var:` conditions.

**Portable truth constants.** Girl Life's test framework uses `_TRUE = (0 ! 1)` and `_FALSE = (0 = 1)` so the values are right on both engines (`girl-life: test/testframework.qsrc:5-6`).

## 6. Concatenation `&`

**Syntax.** `([expr] & [expr])`. Inside an expression `&` is concatenation; at statement level it separates statements, so wrap it in brackets.

**Semantics** (`engine: qsp/variant.c:321`, `qspAutoConvertAppend`):
- string or number with string or number: both become text and are joined (`(1 & 2)` is `'12'`; assigned to a number variable it becomes 12, as the wasm test shows).
- tuple with tuple: one merged tuple (`([1,2] & [3])` is `[1,2,3]`).
- tuple with a value: the value is added as one more item.
- 5.7: string concatenation only, lowest priority.

The docs recommend `+` for strings because `&` is easy to confuse with the separator. `+` cannot merge tuples (`[2,5] + [3,7]` is `[[5,9],[8,12]]`).

## 7. Tuple arithmetic (5.9.0+)

`+`, `-`, `*`, `/` with a tuple operand apply the operation to every item, recursively (`variant.c:380`, `qspAutoConvertCombine`). If both are tuples, each item of the left tuple is combined with the whole right tuple:

```qsp
*pl [2, 3] * [4, 5]   & ! [[8,10],[12,15]]
%t = [4, 10, 16]
%t += 2               & ! [6,12,18]
```

Any string item in a `-`, `*` or `/` operation raises "Type mismatch!".

## 8. Function call syntax

- Functions with two or more required arguments need parentheses: `rand(1, 6)`. Without them the error is "Bracket not found!".
- Functions with zero or one required argument can be written without parentheses: `rnd`, `countobj`, `rand 1000`, `obj 'Apple'`, `loc 'start'` (`mathops.c:871-884`). The single argument then extends to the end of the operand, so `obj 'a' = obj 'b'` relies on priority (section 1).
- The `$` or `%` prefix on a function name does not convert the result. Both engines register the plain and the prefixed names as the same operation, and the result type comes from the function (`engine: qsp/mathops.c:128-149`; `legacy: src/mathops.c:264-265` registers `QSPVER` and `$QSPVER` for one operation). `qspver` therefore returns the version string; Girl Life's check `if qspver > '5.9.2':` compares strings (`girl-life: locations/start.qsrc:12`).
- `FUNC`, `DYNEVAL`, `IIF`, `MIN`, `MAX` and `ARRITEM` return whatever type the value has. The docs recommend `$func(...)` for string results as a readability convention.

## 9. Subexpressions `<<...>>`

**Syntax.** `'text <<expr>> text'` in single- or double-quoted strings. Not in `{}`.

**Semantics.**
- The expression is evaluated when the string literal is evaluated, and its value is inserted as text (numbers in decimal, tuples in `[..]` form).
- 5.9.5 and master compile such literals into a format operation once per expression (`mathops.c:538`). Base descriptions and base action names are expanded at location entry by `qspFormatText` (`text.c:281`).
- An unclosed `<<` raises "Bracket not found!".
- Subexpressions nest; inner quotes are written doubled (see [language-syntax.md](language-syntax.md)).
- 5.7 used a variable `DISABLESUBEX` to turn expansion off; 5.8+ ignores it.

## 10. Limits

| Limit | master | 5.9.5 | 5.7 |
|---|---|---|---|
| Nesting depth of pending operators | 30 (`QSP_MATHSTACKSIZE`) | 30 | 30 (`QSP_STACKSIZE`) |
| Compiled items per expression | 1,000 (`QSP_MAXMATHITEMS`) | 200 | 100 (`QSP_MAXITEMS`) |
| Arguments per function | 20 | 20 | 10 for `FUNC`, `DYNEVAL`, `MIN`, `MAX` |

Exceeding the first two raises "Expression too complex!" in 5.9.5 and master. The wasm repository's `tests/errors-to-test.md` lists the older limits (30 nesting levels, 100 operators per level).

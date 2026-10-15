# Language syntax

This page covers how QSP source text is split into locations, lines and statements, and the lexical rules for comments, strings, names, numbers and labels. Each feature lists what the docs say, what the engine does, and how Girl Life uses it.

Version tags used below: **5.7** is the legacy library (qsp-legacy), **5.9.5** is the release used in the 2026-10-14 research snapshot, **master** is the unreleased engine at commit `00faed4`. When a rule applies to all of them it carries no tag. File and line references follow the conventions in [source-index.md](../source-index.md).

## 1. Source text and locations

**Purpose.** A QSP game is a list of named locations. Each location has a base description, a block of code ("Execute on visit") and a list of base actions. The binary `.qsp` format stores these directly ([tooling-and-development.md](tooling-and-development.md)). Text formats mark location boundaries with line prefixes.

**Text syntax.**

```qsp
# location name
! code lines
--- location name ---------------------------------
```

**Semantics and tool differences.** The text format is a convention of the tools, not of the engine. Each tool recognizes the markers differently:

| Tool | Start marker | End marker | Source |
|---|---|---|---|
| Engine grammar (`help/qsp_grammar.peg`, master) | `#` | `--` then the rest of the line | grammar lines 38-39 |
| TXT2GAM | `#` | `--` (configurable with `-s`, `-e`) | `txt2gam: src/t2g_api.h:14-15` |
| `@qsp/converters` (used by QSPFoundation qsp-cli) | `#` | any line starting with `-` outside a string or `{}` | `converters: src/readers/qsps.ts` |
| Girl Life `tools/qspcli-src/qsp-cli.cpp` | `#` | a line starting with `---` that contains another `---` later | `qsp-cli.cpp:606-607` |

- All tools track quotes and `{}` across lines, so an end marker inside an open string is not seen.
- Text between locations is ignored (the grammar calls it `interLocText`).
- The location name is the rest of the `#` line with surrounding spaces trimmed. Names may contain spaces and `$` (Girl Life has `$menu_settings`; its file is `_menu_settings.qsrc`).

**Edge cases.**
- The docs' own examples end locations with `- start` (statements page, implicit statement section) and `-- summ` (syntaxemes page). The first form works with `@qsp/converters` but not with TXT2GAM, which needs `--`. Girl Life's compiler needs `--- name ---`.
- The first location in the file is where the game starts (`engine: qsp/game.c`, `qspRestartGame` navigates to `qspLocs[0]`).
- Duplicate location names: the first one loaded wins and later ones are skipped silently (`engine: qsp/game.c:191`, comment "the first location with a name wins").

**Girl Life.** All 1,429 `.qsrc` files start with `# name` and end with `--- name ---------------------------------`. Eight headers differ from their file name only by case (for example `eto_building.qsrc` holds `# ETO_building`). See [repository-structure.md](../girl-life-analysis/repository-structure.md).

## 2. Lines and the statement separator `&`

**Purpose.** A physical line holds one or more statements separated by `&`.

**Syntax.** `[statement] & [statement] & ...`

**Semantics.**
- The engine splits a line at `&` characters that are outside quotes, `()`, `[]` and `{}` (`engine: qsp/codetools.c:812`, `qspDelimPos`).
- Inside brackets `&` is the concatenation operator. At statement level it always separates statements, which is why the docs say concatenation "must always be enclosed in brackets".
- An unrecognized statement is classified by looking for `=` outside quotes and brackets. With `=` it is an assignment, without it is the implicit output statement (`engine: qsp/codetools.c:405`, `qspInitLineOfCode`).

**Example (docs, syntaxemes page; comment paraphrased).**

```qsp
*pl "I picked an apple from the branch." & addobj "Apple" & apple+=1
a = 3 & b = 7 & g = rand(1, 6) & ("26" & "27") & ! concatenation inside parentheses
```

**Edge case.** `$x = 'a' & 'b'` assigns `'a'` and then prints `b` as a separate implicit statement. Write `$x = ('a' & 'b')` or use `+`.

## 3. Case-insensitivity

**Rule.** Keywords, variable names, function names, labels and location names are case-insensitive.

**How the engine does it.** Before a line is executed, every character outside quotes and outside `{}` is converted to upper case (`engine: qsp/codetools.c:900`, `qspPrepareStringToExecution`). Location lookup trims and upper-cases the requested name (`engine: qsp/locations.c:171`). Labels are upper-cased when collected (`codetools.c:728`) and when jumped to (`statements.c:448`). String keys of arrays are upper-cased too (`variables.c:544`), so `a['key']` and `a['KEY']` are the same element.

**What stays case-sensitive.**
- String comparison with `=`, `<` and the others compares code units (`engine: qsp/text.h:308`). `'a' = 'A'` is 0. The wasm test `expressions.test.ts` asserts `"a" > "A"` is 1.
- `$curloc` returns the location name as written in its header. `$curloc = 'bedrpar'` is false if the header says `# bedrPar`. Girl Life's sample mod warns about this in `isample_mod/locations/mod_isample.qsrc`.
- Text inside `{}` is not upper-cased until it runs as code.

**Side effect worth knowing.** `$CURACTS` returns action code in its upper-cased form, with strings untouched (see [built-in-api-reference.md](built-in-api-reference.md)).

## 4. Comments

**Purpose.** Ignore the rest of a statement.

**Syntax.**

```qsp
! comment
statement & ! comment after a statement
if x: ! comment after the colon of a multi-line header
! "multi-line
   comment"
! { another
   multi-line comment }
```

**Semantics.**
- `!` starts a comment only at the start of a statement: at the beginning of a line, after `&`, or after the colon of a multi-line `if`, `elseif`, `else`, `act` or `loop` (`engine: qsp/codetools.c:958`, `isStatementStart`). Elsewhere `!` is the not-equal operator.
- **5.7:** a comment after the colon of a multi-line header is not allowed. The comment counts as a second statement, so `if x = 0: ! note` becomes a single-line IF whose body is the comment; the indented lines below then always run and the closing `end` is ignored. The same applies to `elseif ...: !`, `else !`, and `act '...': !`, which creates an action whose only code is the comment (`legacy: tests/engine/conditionals.qspt:605-680`, `acts.qspt:133`). The blog lists comments after the colon among the 5.8+ features.
- A comment runs to the end of the logical line. The logical line, not the physical line, is what matters: a quote or `{` inside a comment opens a string or block that continues across newlines until it closes. The docs present this as the way to write multi-line comments.
- `!!` is not special. It is a comment whose text starts with `!`. Girl Life writes all comments as `!!`.

**The swallowing rule.** Because quotes are tracked inside comments, a single apostrophe in comment text (`! don't`) opens a string that only closes at the next apostrophe, possibly many lines later. Everything in between becomes part of the comment (`engine: qsp/codetools.c:1011-1060`: the quote check runs before the comment check). The legacy 5.7 preprocessor behaves the same way for quotes and braces (`legacy: src/codetools.c:103`). Girl Life's convention is to double apostrophes in comments (`!! you''re plugging in`, `girl-life: locations/shortgs.qsrc:461`). A simulation of the engine rules over all Girl Life locations found 461 comments that span several lines, all ending where intended. In 13 of them a quote stays open across a line end and the comment ends correctly only because a later stray quote closes it ([implementation-observations.md](../girl-life-analysis/implementation-observations.md)).

**Edge cases.**
- `if x: & ! comment` makes the IF single-line, because the colon is no longer the last thing on the line (docs, statements page, IF warning). The engine treats a header as multi-line only when the line has one statement, or two where the second is a comment (`codetools.c:405`, end of `qspInitLineOfCode`).
- In 5.9.5 and master, `()` and `[]` inside comments are ignored when deciding where a line ends. Quotes and `{}` are not ignored.

## 5. String literals

**Purpose.** Text values.

**Syntax.** `'text'`, `"text"`, `{text}`.

**Semantics.**

| Form | Escape | `<<expr>>` expanded | Typical use |
|---|---|---|---|
| `'...'` | `''` for one apostrophe | yes, when the literal is evaluated | ordinary text |
| `"..."` | `""` for one quote | yes | ordinary text |
| `{...}` | none; braces nest | no | code passed to `DYNAMIC`/`DYNEVAL`, multi-line comments |

- There are no backslash escapes. `\` is an ordinary character. The docs' example `$lcase('I DON\'T WANT TO SHOUT AT YOU.')` (functions page, `$LCASE`) is not valid QSP: the apostrophe after the backslash ends the string.
- Newlines inside any of the three forms are kept. A literal can span many lines.
- A `{}` value has the internal type CODE (string-based). It keeps its text exactly, including case.
- In master, a `{}` block that holds valid statements is parsed as code by the grammar (`syntacticCodeBlock`), otherwise as raw text. The runtime treats both as text.

**Subexpressions.** `<<expr>>` inside `'...'` or `"..."` evaluates `expr` and inserts its value as text. In master, strings with `<<` are compiled into a format operation once (`engine: qsp/mathops.c:538`, `qspAppendFormatToCompiled`). Nesting works: the wasm test `strings.test.ts` asserts that `'s=<<$a["_<<i>>"]>>'` yields `s=here`. Because the literal is unescaped before `<<...>>` is parsed, a doubled quote inside the outer string becomes a single quote inside the subexpression. Girl Life relies on this constantly:

```qsp
'<center><h2><<$setloc[''StageTitle'']>></h2></center>'
```

(`girl-life: locations/core_library.qsrc:49`). The master grammar comment says a subexpression "shouldn't contain strings with the same type of quotes as the parent string"; the doubled-quote form above works in the engine because unescaping happens first.

**DISABLESUBEX.** Before 5.8.0, setting `disablesubex = 1` turned expansion off. It has no effect in 5.8.0 and newer. To print `<<` literally, split it: `'<'+'<text>>'` (blog 2026-01-01).

## 6. Line continuation ` _`

**Purpose.** Split one long statement over several physical lines.

**Syntax.** End a line with a space and `_`.

```qsp
if t _
   or _
   t:
```

**Semantics.**
- 5.9.5: the line must end with space then `_` (`engine-5.9.5: qsp/codetools.c:735-742`, `QSP_PREEOLEXT " "`). The `_` is removed and the space is kept, so the joined text is `if t or t:`. The wasm test `code.test.ts` ("long line split") asserts this.
- master: a tab before `_` also works (commit `ab7500e`, 2026-10-10).
- 5.7: the 2026 blog post says the old engine joined the pieces without a space (`if tort:`) and recommends two spaces before `_` for portability. The legacy source does not match that claim: `legacy: src/codetools.c:184-199` overwrites only the `_` and keeps the space, both at HEAD and in the fork's first commit `ef433fc`. This is recorded as an unresolved contradiction in [verified-findings.md](../verified-findings.md).

## 7. Multi-line expressions inside brackets

5.9.4 and later keep reading the next physical line while a `(` or `[` is open (`engine: qsp/codetools.c:958-1077`). The blog shows tuples, `max(...)` arguments and IF conditions written this way. The 5.7 preprocessor tracks only quotes and `{}`, so this layout breaks old players. Girl Life does not use it.

## 8. Names (variables, functions, user calls)

**Rules from `qspPrepareVarName` (`engine: qsp/variables.h:122`).**
- An optional type prefix `$`, `%` or `#` is skipped.
- The rest must be non-empty, must not start with a digit, and must not contain a delimiter. Otherwise the error is "Incorrect variable name!".
- Delimiters (master, `declarations.h:148`): space, tab, `& ' " ( ) [ ] { } = ! < > + - / * \ , : ; ^ @ ?`, CR, LF.
- Delimiters (5.9.5, `declarations.h:142`): the same minus `\ ; ^ @ ?`. A name such as `a;b` was legal in 5.9.5 and is not in master.
- `.` is not a delimiter. Names like `em.arr.sort` (docs example) and `foo.3` (blog example) are valid for variables and locations.
- Non-ASCII letters are allowed. The docs and the wasm tests use Cyrillic names (`любимое_число`).

**Keywords as names.** The grammar forbids a keyword followed by a delimiter as a variable name. The engine recognizes statements by prefix match at the start of a statement (`codetools.c:43`), with "isolated" keywords requiring a delimiter after them, so `iffy = 1` is an assignment but `if fy = 1` is an IF.

**Girl Life.** Its analyzer `tools/qsp_audit` treats `.`, `|`, `#`, `$`, `%`, `~` as delimiters (`qsp_analyse.py`, `_QSP_DELIMS`). That is stricter than the engine.

## 9. Numbers

- Literals are unsigned decimal digits only (`engine: qsp/mathops.c:702`). A minus sign is the unary operator. There are no fractions, exponents, hex literals or digit separators.
- Leading zeros are allowed: Girl Life's save migrations compare against `00080402` (`girl-life: locations/saveupdater.qsrc:26`).
- Too-large literals clamp to the maximum value instead of overflowing (`engine: qsp/text.h`, `qspParseUnsignedNumber`).
- Numbers are C `int` (32-bit) unless the engine is built with `QSP_USE_BIGINT` (`bindings/qsp.h:97`). No build file in the repository defines it.

## 10. Labels

**Syntax.** `:name` at the start of a line. Anything after a following `&` is executed as statements.

**Semantics (`engine: qsp/codetools.c:728`, `statements.c:370`).**
- The label name is the text after `:` up to `&` or end of line, trimmed and upper-cased. Labels are case-insensitive and surrounding spaces are ignored, both in the label and in the `jump` argument.
- Labels are collected once per code block: a location, an action body, a hyperlink's code, or a `DYNAMIC`/`DYNEVAL` string. Loop bodies share their enclosing block.
- `jump` searches the current execution range first. If the label is not there, the request travels outward through enclosing IF, ELSE and LOOP bodies until a range contains it. Only the outermost range raises "Label not found!".
- With duplicate labels, the first one in the searched range wins. Because inner ranges are searched first, a duplicate inside the current block can win over an earlier one outside it. This is inferred from `qspExecCode` (`statements.c:602`), not documented.
- A jump can land inside another handler's IF block in the same location. `END` lines are no-ops when reached that way. Girl Life uses this: `time_cheat_fix` jumps to `:time_time_loop`, which sits inside the `if $ARGS[0] = ''` block (`girl-life: locations/time.qsrc:14, 40-49`). The legacy engine searches labels the same way (`legacy: src/statements.c:310`).

## 11. END and block structure

```qsp
if cond:
    ...
end
act 'name':
    ...
end act
loop while cond:
    ...
end loop
```

- `end`, `end if`, `end act`, `end loop` and `end <any text>` all close the innermost open block. Text after `end` is ignored up to the next `&`.
- `end & stmt` runs `stmt` after closing the block. The wasm conditionals tests assert this.
- A header is multi-line only when nothing but an optional comment follows its colon. See [control-flow.md](control-flow.md) for the full IF/ELSE/ELSEIF rules.
- Missing `end` raises "Token [end] not found!" when the block is executed, not at load time, because the engine parses lazily.

## 12. Implicit calls `@` and `@@` (5.8.0+)

```qsp
@name(arg1, arg2)    ! like func('name', arg1, arg2)
@@name arg1, arg2    ! like gosub 'name', arg1, arg2
```

- The name after `@` is read up to the next delimiter (`mathops.c:827`). Location names with spaces or delimiters cannot be called this way.
- 5.9.5: no space is allowed between `@`/`@@` and the name. master accepts spaces there (commit `bc7e567`, 2026-10-10).
- The docs warn that a space between the name and `(` turns the arguments into a single tuple argument.
- Girl Life never uses `@` or `@@` (zero occurrences), because they do not exist in 5.7.

## 13. Type prefix characters

`$` (string), `%` (tuple, 5.9.0+) and `#` (number) prefix variable and function names. The engine defines `#` as the number prefix in 5.9.4, 5.9.5 and master (`declarations.h:60-61`, `qspInitVarTypes`), and the grammar lists it in `typePrefix`, but the docs never mention it. Semantics are covered in [variables-and-data-types.md](variables-and-data-types.md).

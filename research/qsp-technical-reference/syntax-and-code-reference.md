# QSP syntax and code reference

A compact reference for writing QSP that runs on Girl Life's players. Each entry is tagged with the engine versions it applies to:

| Tag | Meaning |
|---|---|
| **[all]** | 5.7 and every later version |
| **[5.7]** | 5.7 only |
| **[5.8+]** | 5.8.0 and later, including 5.9.x |
| **[5.9.0+]**, **[5.9.1+]**, **[5.9.4+]** | from that release on |
| **[master]** | the unreleased 5.9.6 engine |

Girl Life code must use only **[all]** features, or branch on `$qspver` ([version-differences.md](engine-source-analysis/version-differences.md)). Details and sources for every line are in the pages linked from each section.

## 1. Source layout

```qsp
# location_name
!! code of the location
--- location_name ---------------------------------
```

- **Start marker [all].** `# name` on its own line starts a location.
- **End marker, by tool.**
  - Girl Life's `qsp-cli` needs a line that starts with `---` and contains another `---`.
  - TXT2GAM needs `--`.
  - `@qsp/converters` accepts `-`.
- **File names.** One location per `.qsrc` file. `$` in a location name becomes `_` in the file name.
- **Registration.** Every file must be listed in the `.qproj` manifest or it is not built ([repository-structure.md](girl-life-analysis/repository-structure.md)).

## 2. Lines, statements and comments

| Form | Meaning | Tag |
|---|---|---|
| `stmt1 & stmt2` | Two statements on one line | [all] |
| `! text`, `!! text` | Comment, only at the start of a statement | [all] |
| `stmt & ! text` | Comment after a statement | [all] |
| `if x: ! text` (multi-line header) | Comment after a header colon | [5.8+]; on [5.7] it turns the header into a single-line IF |
| `!{ ... }` | Comment spanning lines (the `{` opens a block) | [all] |
| `text _` at line end | Continue the statement on the next line (space before `_`) | [all]; the joining space on 5.7 is disputed ([verified-findings.md](verified-findings.md)) |
| open `(` or `[` at line end | Continue on the next line | [5.9.4+] |
| `''` inside `'...'`, `""` inside `"..."` | Literal quote character | [all] |
| `{ ... }` | Code block literal, for `dynamic` and `dyneval` | [all] |

**Apostrophes in comments.** Quotes are tracked inside comments, so a single `'` in a comment opens a string that runs to the next `'`, possibly many lines down. Write `''` in comments ([language-syntax.md](official-documentation/language-syntax.md)).

**Case.** Keywords, variable names, location names, labels and string array keys are case-insensitive. String comparison is case-sensitive.

## 3. Variables

| Form | Meaning | Tag |
|---|---|---|
| `x = 5`, `$s = 'text'` | Number or string assignment | [all] |
| `x += 1`, `-=`, `*=`, `/=` | Compound assignment | [all] |
| `a[3] = 1`, `$a['key'] = 'v'`, `a[] = 1` | Array element by position, by key, or appended | [all] |
| `%t = [1, 'a']` | Tuple | [5.9.0+] |
| `a, b = b, a` | Multiple assignment, swap | [5.8+] |
| `local x = 1` | Local variable in the current scope | [5.8+] |
| `x = 'text'` | Unprefixed name holding a string | [master] (type mismatch before) |
| `killvar 'x'`, `killvar 'x', 2`, `killvar` | Empty a variable, remove one element, clear all | [all]; bare `killvar` clears only globals on [master] |
| `copyarr 'dst', 'src'` | Copy an array | [all] |
| `setvar 'name', value` | Assign by computed name | [5.9.1+] |

**Storage.**
- **[5.7]** Each element holds a number and a string side by side. `x` reads the number, `$x` the string.
- **[5.8+]** Each element holds one value. Reading it with the other prefix returns 0 or `''`.
- **[master]** Unprefixed reads return the stored value whatever its type.

**Scope.** Variables are global unless declared `local` [5.8+]. `ARGS` holds a call's arguments; `RESULT` is a function's return value. On [5.7] only `FUNC` and `DYNEVAL` isolate `RESULT` ([variables-and-data-types.md](official-documentation/variables-and-data-types.md)).

## 4. Operators

Priority from loose to tight:

| [5.8+] | [5.7] |
|---|---|
| `OR` | `&` |
| `AND` | `OR` |
| `NO` | `AND` |
| comparisons `= < > ! <> <= >=` | `NO`, `OBJ`, `LOC` |
| `OBJ`, `LOC` | comparisons |
| `&` | `+ -` |
| `+ -` | `MOD` |
| `MOD` | `* /` |
| `* /` | unary `-` |
| unary `-` | functions |

| Rule | [5.8+] | [5.7] |
|---|---|---|
| True value of a comparison | 1 | -1 |
| `AND`, `OR`, `NO` | logical, short-circuit | bitwise, no short-circuit |
| `IIF(c, x, y)` | evaluates only the chosen branch | evaluates both |
| String in a condition | non-empty is true | converted to a number; non-numeric text is an error |
| `!` and `<>` | not equal | not equal |

`/` truncates toward zero. `+` adds numbers or joins strings. `&` joins inside an expression but separates statements at statement level, so write `(a & b)` ([expressions-and-operators.md](official-documentation/expressions-and-operators.md)).

**Portable truth.** Compare with explicit values (`if func(...) = 1:` only when the function returns `iif(cond, 1, 0)`), or use `_TRUE = (0 ! 1)` as Girl Life's tests do.

## 5. Control flow

```qsp
if cond: stmt & stmt                    !! single-line [all]
if cond: stmt else stmt                 !! single-line with else [all]
if cond: a elseif cond2: b else c       !! inline elseif [5.8+]
if cond:                                !! multi-line [all]
	...
elseif cond2:
	...
else
	...
end
loop local i = 0 while i < 10 step i += 1:   !! [5.8+]
	...
end
:label                                  !! label [all]
jump 'label'                            !! case-insensitive, current code block [all]
exit                                    !! leave the current code block [all]
```

| Call | Effect | Tag |
|---|---|---|
| `gt 'loc', args...` | Go to a location: clears text and actions, stops all running code | [all] |
| `xgt 'loc', args...` | Same, keeps the main text | [all] |
| `gs 'loc', args...` | Run a location and return | [all] |
| `x = func('loc', args...)` | Run a location and return its `RESULT` | [all] |
| `@loc(args)`, `@@loc args` | Short forms of `func` and `gs` | [5.8+] |
| `dynamic 'code', args...` | Run text as code | [all] |
| `x = dyneval('result = ...', args...)` | Evaluate code text | [all] |
| arguments per call | up to 9 on [5.7], 19 on [5.8+] | |

## 6. Screen, actions and dialogs

| Statement | Effect | Tag |
|---|---|---|
| `'text'` (implicit) | Print text and a line break in the main window | [all] |
| `*p`, `*pl`, `*nl`, `*clr` | Main window: print, print with break, break then print, clear | [all] |
| `p`, `pl`, `nl`, `clr` | Same for the stats window | [all] |
| `cla`, `cls` | Remove all actions; clear everything except objects | [all] |
| `act 'name': code` or block form ending in `end` | Add an action (50 at most; duplicate names ignored) | [all] |
| `delact 'name'` | Remove an action | [all] |
| `msg 'text'`, `$s = input('prompt')`, `menu 'arr'` | Dialogs; menu items are `'title:location'` strings in `$arr` | [all]; `-:-` menu separators [5.8+] |
| `addobj`, `delobj`, `killobj` | Inventory | [all]; `modobj`, `resetobj` [5.9.4+] |
| `play 'file', volume`, `close 'file'`, `close all` | Sound | [all] |
| `view 'image'`, `wait ms`, `settimer ms` | Picture window, pause, timer interval | [all] |
| `<a href="exec:code">`, `usehtml = 1` | Links that run code | [all] |
| `<<expr>>` inside strings | Subexpression | [all] |

## 7. Functions used most in Girl Life

| Function | Note | Tag |
|---|---|---|
| `iif(c, x, y)` | See section 4 | [all] |
| `rand(a, b)` | Inclusive; one-argument form differs (0..n on 5.7, 1..n on 5.8+) | [all] |
| `$mid(s, start, len)`, `len(s)`, `instr(s, sub)` | 1-based. Three-argument `instr` order differs by version | [all] |
| `$str(n)`, `val(s)`, `isnum(s)` | Conversions | [all] |
| `$lcase`, `$ucase`, `$trim`, `$replace` | Text | [all] |
| `arrsize('a')`, `arrpos('a', v)` | Array size and search. Three-argument `arrpos` order differs | [all] |
| `max(...)`, `min(...)` | Values, or one array name | [all] |
| `loc('name')` | Does a location exist | [all] |
| `$curloc`, `$curacts` | Current location; current actions as code | [all] |
| `$qspver` | Version text; compare with care (string comparison) | [all] |
| `rgb(r, g, b)` | Color for `bcolor`, `fcolor`, `lcolor` | [all] |
| `arritem`, `setvar`, `arrtype`, `arrpack` | Computed names and array introspection | [5.8+] / [5.9.1+] |
| `countobj('name')` | Count objects with a name | [master] |

## 8. System variables Girl Life sets

| Variable | Girl Life value | Purpose |
|---|---|---|
| `$onnewloc` | `'LOCA'` | Runs after every `gt`; calls mods and events |
| `$ongsave`, `$ongload` | `'saveg'`, `'loadg'` | Version stamp; save migration |
| `$onobjsel` | `'onobjsel'` | Debug panel |
| `$counter` | `'counter'` | Notification timer, music loop |
| `$usercom` | `'inputProcessing'` | Empty |
| `usehtml`, `disablescroll`, `$fname`, `fsize` | 1, 1, `'Tahoma'`, 12 | Display |
| `debug` | 1 | Saves load across game builds |

## 9. Patterns Girl Life uses for 5.7 and 5.8+ at once

| Need | Girl Life pattern | Instead of |
|---|---|---|
| Function library | `if $ARGS[0] = 'name': ... exit end` handlers | separate locations per function |
| Loop | `:label` ... `if cond: jump 'label'` | `LOOP` |
| Local variable | prefixed global plus `killvar` at the end | `LOCAL` |
| Boolean return | `result = iif(cond, 1, 0)` | `result = (cond)` |
| Array by computed name | `dynamic` / `dyneval` with `<<...>>` | `SETVAR`, `ARRITEM` |
| Optional library | `if $qspver < '5.8.0': addqst ... else inclib ... end` | `INCLIB` alone |
| Condition on a string | `if $s <> '':` | `if $s:` |

Annotated examples: [code-examples.md](girl-life-analysis/code-examples.md).

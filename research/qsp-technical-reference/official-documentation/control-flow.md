# Control flow

Conditions, loops, labels, exits, location transfers, dynamic code, and how the engine stops running code. Version tags and reference formats as in [source-index.md](../source-index.md).

## 1. IF, ELSEIF, ELSE

### Forms

```qsp
! single-line
if cond: stmt & stmt
if cond: stmt else stmt
if cond: stmt elseif cond2: stmt else stmt

! multi-line
if cond:
    ...
elseif cond2:
    ...
else
    ...
end
```

`else if` (two words) is accepted wherever `elseif` is (`engine: qsp/codetools.c:405`, the "Convert multiline ELSE IF to ELSEIF" branch). A colon after `else` is optional.

### How the engine decides single-line or multi-line

A line whose first statement is `if`, `elseif`, `else`, `act` or `loop` is multi-line only when its colon (for `else`, the keyword) ends the line, optionally followed by a comment (`codetools.c`, end of `qspInitLineOfCode`). Anything else after the colon makes it single-line, and following lines are no longer part of it.

### Rules and edge cases (docs and wasm `conditionals.test.ts`)

- In a single-line IF, `else` and `elseif` are found by scanning the line for the isolated keywords outside quotes and brackets (`codetools.c:405`, `qspKeywordPos`).
- **5.7 has no inline `elseif` in a single-line IF.** `if x = 2: x = 3 elseif x = 2: x = 4` raises "Unknown action!" when the condition is true, because the true branch is read as `x = 3 elseif x = 2: x = 4`. When the condition is false, only a trailing `else` part runs (`legacy: tests/engine/conditionals.qspt:50-93`). Multi-line `elseif` works in 5.7.
- **5.7 treats `if cond: ! comment` as single-line.** See [language-syntax.md](language-syntax.md), section 4. Scans found neither form in Girl Life or GLSS.
- Single-line IF must have code after the colon and after `else`; otherwise the error is "Code not found!" (`statements.c:742-790`).
- `if abcd=3: k1=34 else k1=25 end` raises "Unknown action!" (code 29 in 5.9.5) because single-line forms do not take `end`.
- A multi-line IF with code after the colon is silently single-line. The docs example:

  ```qsp
  if abcd = 3: k1 = 34
      k2 = 35 & ! this will be executed because if is single line
  end
  ```

  The `end` on the last line is then an orphan; the engine treats `END` as a no-op when it reaches one, so no error is raised.
- Inside a multi-line IF, a single-line `else stmt` or `elseif cond: stmt` runs its own statements and skips every following line up to the next `else`/`elseif`/`end` of the block. The wasm test "multi line if true with single line else" shows the remaining lines are ignored.
- Two `else` branches in one block: only the first is reachable (wasm tests "multi line if false with 2 single line else").
- `end & y = 3` closes the block and then runs `y = 3`.
- Missing `end` raises "Token [end] not found!" (code 18) when the IF runs. Missing colon raises "Token [:] not found!" (code 17).
- Each branch body runs in its own local variable scope ([variables-and-data-types.md](variables-and-data-types.md)).
- Conditions are converted to booleans: 5.8+ accepts numbers, strings and tuples; 5.7 requires a number ([expressions-and-operators.md](expressions-and-operators.md)).

**Engine.** `statements.c:742` (`qspStatementIf`, single-line), `qspExecMultilineCode` (multi-line), `qspSearchElse` and `qspSearchEnd` (find matching branches, counting nested multi-line `if`/`act`/`loop`).

**Girl Life.** IF is the second most frequent construct (76,441 `if`, 32,824 `elseif`, 23,757 `else` statements in `locations/`). Handlers are written as one multi-line IF per event name ([scripting-patterns.md](../girl-life-analysis/scripting-patterns.md)).

## 2. LOOP (5.8.0+)

### Syntax

```qsp
loop [init statements] while [condition] step [step statements]: [body]

loop [init statements] while [condition] step [step statements]:
    [body]
end
```

`init` and `step` are optional; `while` is required ("Loop condition not found!" otherwise).

### Semantics (`engine: qsp/statements.c:820`, `:864`)

1. A new local scope is opened for the whole loop. `init` runs once inside it, so `loop local i = 0 while ...` keeps `i` private to the loop.
2. The condition is evaluated before every pass. If false, the loop ends.
3. The body runs in its own fresh local scope each pass.
4. The step statements run in another fresh scope after each pass.
5. `exit` inside the body ends the loop and the whole enclosing code block, not just the loop (docs "Attention!!!" under EXIT; wasm test "EXIT stops whole location not just loop").
6. `jump` to a label outside the loop leaves the loop (wasm test "can JUMP outside loop").

### Docs example

```qsp
loop local i, size = 0, arrsize('mass') while i < size step i += 1:
    summ += mass[i]
end
```

**Girl Life.** No `LOOP` statements. All iteration uses labels and `jump` because the game must run on 5.7 (two hits for "loop" in a search are labels named `:loop`, in `kid.qsrc:141` and `subkid.qsrc:7`).

## 3. Labels and JUMP

### Syntax

```qsp
:label
jump 'label'
```

### Semantics

- `jump` evaluates its argument as a string, trims it, upper-cases it and searches the labels of the current code block (`engine: qsp/statements.c:448`, `:370`).
- Search starts in the range being executed (for example the current IF branch) and moves outward through enclosing blocks. Only the top level raises "Label not found!".
- A jump can target any line of the same code block, including lines inside another IF branch or handler. See [language-syntax.md](language-syntax.md), section 10.
- A `jump` from inside an action, link code or dynamic code cannot reach labels outside that block (wasm tests "error jump from action/dynamic/dynaeval").

### The pre-5.8 loop idiom

```qsp
i = 0
:girlfriend_looop
if loverGender[i] = 1: pcs_girlfriends += 1
i += 1
if i < arrsize('lover'): jump 'girlfriend_looop'
killvar 'i'
```

(`girl-life: locations/saveupdater.qsrc:30-35`). Girl Life has 1,258 `jump` statements in 246 files. The docs' `MSECSCOUNT` example measures a label loop against `LOOP`.

## 4. EXIT

`exit` ends the current code block: the location code being run, an action's code, link code, or `DYNAMIC`/`DYNEVAL` code (`statements.c`, `qspStatExit` returns "exit" up to the block's `qspExecCode`). Calling code continues after the `gosub`, `func` or `dynamic` that started the block.

Girl Life ends almost every handler with `exit` (3,969 statements) so that a location used as a function library runs only one handler per call.

## 5. Location transfers

| Statement | Clears main text | Clears actions | Runs base description and base actions | Runs location code | Changes `$curloc` | Calls `$ONNEWLOC` | Returns to caller |
|---|---|---|---|---|---|---|---|
| `GOTO`, `GT` | yes | yes | yes | yes | yes | yes | no |
| `XGOTO`, `XGT` | no | yes | yes | yes | yes | yes | no |
| `GOSUB`, `GS`, `@@` | no | no (adds) | yes (adds) | yes | no | no | yes |
| `FUNC`, `@` | no | no (adds) | yes (adds) | yes | no | no | yes, with `RESULT` |

Sources: `engine: qsp/locations.c:225` (`qspExecLocation`), `:288` (`qspExecLocByNameWithArgs`), `:342` (`qspNavigateToLocation`); wasm `locations.test.ts`. `GOTO` does not clear the stats window (`p`/`pl` text): the wasm test shows `stats\r\ntarget stats` after a `GOTO`.

### What happens to the code after GOTO

`GOTO` and `XGOTO` increment the engine's location-state counter (`locations.c:342`, `++qspLocationState`). Every running frame compares the counter with the value it saw when it started and stops when it changed. The effect: after `gt`, no statement of the current code runs, and neither does any code in callers further up, including code after the `gosub` or `func` that led to the `gt`. The target location's code and then the `$ONNEWLOC` handlers run, and the event ends.

```qsp
! illustrative example, not from a source
gs 'helper'          ! helper ends with: gt 'street'
*pl 'never printed'  ! skipped, the GOTO inside helper ended this code too
```

The same counter stops code after a runtime error (`errors.c:20`, `qspSetError` increments it). Errors therefore abort the entire event, not just the failing statement.

Girl Life relies on this: menu actions end with `gt $loc, $loc_arg` and nothing after it matters, and handlers redirect early with `gt` (for example `gt 'gschool_lessons', 'grade_check'` in the middle of the `morning` handler, `girl-life: locations/gschool_lessons.qsrc:41`).

### Arguments and limits

- Up to 19 arguments after the location name in 5.8+, up to 9 in 5.7. The docs show both `[argument 8]` and `[argument 18]`; the first is the 5.7 limit.
- The location name is trimmed and case-insensitive. A missing location raises "Location not found!".
- Call depth: master and 5.9.5 stop at 2,000 nested location calls with "Maximum location call depth exceeded!" (`locations.h`, `QSP_MAXLOCCALLDEPTH`). 5.7 has no depth limit, so deep recursion runs until the process stack overflows.

## 6. DYNAMIC and DYNEVAL

```qsp
dynamic $code, arg0, arg1
x = dyneval('result = <<a>> + 1')
$s = $dyneval({$result = $args[0] + '!'}, 'hi')
```

- The code string is preprocessed like a location and run in a new local scope with its own `ARGS` and `RESULT` (`statements.c`, `qspExecStringAsCodeWithArgs`).
- Preprocessed blocks are cached by text, 64 buckets of 8 entries each, for strings up to 8,192 characters (`codetools.c:1099`). Repeated `dynamic` calls with the same text skip preprocessing.
- `<<...>>` in a quoted code string is expanded when the string literal is evaluated, before `dynamic` runs. In `{}` it is expanded when the code runs. The docs show the difference with `$args[0]`.
- Labels in dynamic code are local to that code.
- `DYNEVAL` returns `RESULT` like `FUNC`. With no result and used as an implicit statement, it prints nothing.

**Girl Life.** 1,111 `dynamic` and 244 `dyneval` uses, mostly to read or write arrays whose name arrives as a string (`girl-life: locations/array.qsrc:12-38`). 5.9.1 added `SETVAR` and `ARRITEM` for this purpose, but Girl Life cannot use them on 5.7.

## 7. ACT as deferred code

`act 'name': ...` does not run its code. It registers the code as an action. The code runs later, when the player clicks, in a new local scope with no locals from the location that created it (wasm test "local variables are not visible in actions (unlike args)"). An action can create further actions; Girl Life's bathroom code nests an `act 'Continue'` inside `act 'Take a shower'` (`girl-life: locations/core_library.qsrc:89-101`). Details of the action list are in [execution-model.md](execution-model.md).

## 8. Errors and recovery

- A runtime error records its number, location, base action index and line, increments the location-state counter, and stops all running code (`errors.c:20`).
- There is no try/catch construct. Code that might fail must check first (`loc('name')` before `gs`, `isnum($s)` before `val`).
- The player shows the error. With the classic player, the screen keeps whatever text was output before the error.
- Error numbers differ by version; see [runtime-behavior.md](../engine-source-analysis/runtime-behavior.md).

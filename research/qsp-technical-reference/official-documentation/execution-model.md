# Execution model

How a QSP game runs: what the player calls, what the engine does for each event, how a location is entered, how actions and handlers fit in, and how screen updates reach the player. The docs describe this only in pieces (`$CURLOC`, `GOTO`, the handler variables). This page assembles it from the engine source; statements marked "inferred" come from reading code rather than from docs or tests. References as in [source-index.md](../source-index.md).

## 1. Layers

```text
Player (qspgui, Qqsp, qSpider via qsp-wasm-engine, Quasporium)
  |  calls the public API: QSPExecuteSelActionCode, QSPExecString, QSPExecCounter ...
  v
QSP library (qsp/*.c)
  |  calls back for UI and I/O: QSP_CALL_REFRESHINT, SHOWMSGSTR, INPUTBOX, PLAYFILE ...
  v
Player draws text, actions, objects; plays sound; shows dialogs
```

The engine never draws anything. It keeps buffers (main text, stats text, input line, action list, object list, view path) and tells the player which ones changed (`QSP_WIN_*` flags in `bindings/qsp.h:42-51`). Player behavior such as HTML rendering, scrolling and link handling lives in the player, which is why the docs have qSpider-specific notes.

## 2. Events

Every interaction is one call into the engine. Each call starts with `qspPrepareExecution` (`engine: qsp/common.c:84`), which:
- clears the last error,
- discards all local variable scopes, so every event starts with only globals,
- resets the location call depth counter,
- clears the "windows changed" flags.

| Player event | API call (`bindings/default/default_control.c`) | What runs |
|---|---|---|
| Open a game file | `QSPLoadGameWorldFromData` | Nothing; the file is parsed only |
| New game / restart | `QSPRestartGame` | Reseed the random generator, clear everything, then `GOTO` the first location (`game.c`, `qspRestartGame`) |
| Click an action | `QSPSetSelActionIndex` then `QSPExecuteSelActionCode` | `$ONACTSEL` handlers if the selection changed, then the action's code |
| Click an object | `QSPSetSelObjectIndex` | `$ONOBJSEL` handlers, only if a different object was selected |
| Click a link `exec:...` | `QSPExecString` | The code after `exec:`, preprocessed and run in a new local scope (`statements.c`, `qspExecStringAsCode`) |
| Enter in the input line | `QSPExecUserInput` | `$USERCOM` handlers |
| Timer tick | `QSPExecCounter` | `$COUNTER` handlers, skipped while a dialog callback is open |
| Save / load | `QSPSaveGameAsData`, `QSPOpenSavedGameFromData` | `$ONGSAVE` before saving; restore state, then `$ONGLOAD` after loading |

After the call the player asks for the changed buffers and redraws (`QSP_CALL_REFRESHINT`).

The classic player's link handling (`qspgui: qspgui/frame.cpp:1127-1150`): `#anchor` scrolls, `EXEC:` (checked case-insensitively) runs the rest as QSP code through `QSPExecString`, and anything else opens in the system browser.

## 3. Entering a location with GOTO

`qspNavigateToLocation` (`engine: qsp/locations.c:342`) and `qspExecLocation` (`:225`), in order:

1. Set the current location (`$CURLOC`).
2. Discard all local scopes.
3. Store the `GOTO` arguments in the global `ARGS`.
4. Clear the action list.
5. Increment the location-state counter. Any code that was running when `gt` executed sees the change and stops.
6. For `GOTO` (not `XGOTO`), clear the main window.
7. Open a local scope for the location's code.
8. Append the location's base description, with subexpressions expanded, and add its base actions.
9. Run the location's code ("Execute on visit").
10. Close the scope.
11. Run the `$ONNEWLOC` handlers with the same arguments, in the global scope.

**Inferred consequences.**
- `$ONNEWLOC` runs after the destination's code, so it can see and add to whatever the location printed and the actions it created. GLSS uses this through Girl Life's `LOCA` handler, which calls every mod's dispatcher (`girl-life: locations/LOCA.qsrc:27-28`, `mod_system.qsrc:4-10`).
- If the location's own code calls `gt` again, steps 10-11 never run for the first location. Only the last destination's `$ONNEWLOC` runs.
- `$ONNEWLOC` does not run after `GOSUB` or `FUNC`.

## 4. GOSUB and FUNC

`qspExecLocByNameWithArgs` (`locations.c:288`):
1. Find the location (case-insensitive, trimmed) or raise "Location not found!".
2. Open a scope with fresh `ARGS` (the call arguments) and `RESULT`.
3. Append the base description and base actions to the current screen (nothing is cleared).
4. Run the code.
5. `FUNC`: copy `RESULT` out. Close the scope.

Depth is limited to 2,000 nested calls in 5.9.5 and master.

## 5. Actions

- `ACT` stores the action's name, image, a reference to its code lines, and the location and base-action index it came from (`actions.c:69`).
- The list holds at most 50 actions. Duplicate names (case-insensitive) are ignored.
- When the player clicks, the code runs in a new scope on top of an empty local stack (`actions.c:91`). It sees globals, including the global `ARGS` from the last `GOTO`.
- Base actions (from the QGen "Actions" list or a compiler's base section) are added before the location's code runs.
- The action code survives until the list is cleared by `CLA`, `CLS`, `GOTO`/`XGOTO`, or `DELACT`.
- Saves store each action's code text and its source location name. Loading a save restores them, so a saved action runs the code that existed when the game was saved (`game.c:263`, inferred effect on updated games).

## 6. Counter, timers and real time

- The counter interval defaults to 500 ms and is set with `SETTIMER` (`game.h`, `QSP_DEFTIMERINTERVAL 500`).
- The tick runs `$COUNTER` locations. It is skipped while a `MSG`, `INPUT`, `MENU` or `WAIT` is in progress (`default_control.c:390-400`, `qspIsInCallback`).
- `MSECSCOUNT` returns accumulated play time, saved with the game.
- The docs advise against using the counter for game logic (`$COUNTER` "< 5.7.0" note). Girl Life's counter only animates the notification text and keeps music looping (`girl-life: locations/counter.qsrc`).

## 7. Dialog callbacks and re-entrancy

`MSG`, `$INPUT`, `MENU` and `WAIT` call the player and wait for it. Before each call the engine marks itself as "in callback" and asks the player to refresh, so the text written so far appears (`callbacks.c`, `qspPrepareCallback`). This is why `WAIT` makes earlier output visible, as the docs describe.

While in callback mode:
- player events still reach the engine, but `qspPrepareExecution` does not discard locals (`common.c:88`);
- the counter does not run.

If the player loads or restarts a game during the callback, the location-state counter changes. When the callback returns, the suspended code sees this and stops (`qspFinalizeCallback`). The wasm test "local variables available with flow stop in callbacks" checks that locals survive until the dialog closes.

## 8. Errors

A runtime error sets the error record (number, description, location, base action index, line number and line text) and increments the location-state counter, which stops all running code (`errors.c:20`). The player reads the record with `QSPGetLastErrorData` and shows it. The 2026 blog post notes that 5.9.x messages include the offending line's text. The wasm tests show the record for each error case: `errorCode`, `description`, `location`, `line`, `localLine`, `lineSrc` (the upper-cased line) and `actionIndex`.

## 9. Debug hooks

`QSPEnableDebugMode(1)` makes the engine call `QSP_CALL_DEBUG` before each executed line and before a location's base description (`statements.c:602`, `locations.c:225`). Players use it for step debugging. Girl Life's own debug build instead injects QSP trace code at the top of every location (`girl-life: tools/build_debug.py`).

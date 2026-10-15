# Girl Life and GLSS: implementation observations

Findings from scanning Girl Life (`locations/` at commit `83b164f`) and this repository's GLSS mod against the engine rules documented in this reference. Each item is labeled:

- **Fact**: read directly from source or produced by a scan whose script is described in [research-scope-and-methodology.md](../research-scope-and-methodology.md).
- **Inferred**: follows from the source and the engine rules, but was not reproduced in a running player.

No Girl Life or GLSS file was changed. Items are observations, not bug reports filed upstream.

## Summary

| # | Observation | Label | Effect today |
|---|---|---|---|
| 1 | 31 `.qsrc` files are not in `glife.qproj` | Fact | Left out of every build |
| 2 | 8 files whose header differs in case from the file name | Fact | None in the engine; `$curloc` comparisons must use header case |
| 3 | 13 comment blocks close correctly only because stray quotes pair up | Fact | None; one edit could change that |
| 4 | No 5.7 parsing hazards (inline `ELSEIF`, comment after a header colon) | Fact | None |
| 5 | Version checks compare strings | Fact | Would misjudge a two-digit version such as 5.10 |
| 6 | One 5.7 variable hash bucket would hold 55 names if all existed at once (limit 50) | Inferred | Possible "Too many variables!" on 5.7 in a long session |
| 7 | 44 variable elements are written both as string and as number | Fact | Mostly temporaries and migrations; see the list |
| 8 | 56 `iif` calls with `func` and 42 with `rand` in a branch | Fact | On 5.7 both branches run |
| 9 | Two boolean return styles (`iif(..., 1, 0)` and raw comparisons) | Fact | Callers of raw ones must not test `= 1` on 5.7 |
| 10 | `dow` shortcut tests the `doy` variables | Fact | Always takes the slow path; same result |
| 11 | CI dev build passes `glife.qsp` as a second input to `qsp-cli` | Inferred | An error message in CI; a possible race in a working copy |
| 12 | `MakeQSP.bat` option `F` only runs the game when typed lowercase | Fact | Minor |
| 13 | Qqsp and the engine's Oniguruma dependency are fetched unpinned | Fact | Builds are not reproducible |
| 14 | GLSS one-click university day: the gate matched `Go to your room`, missed periods were credited, and the clock skipped lecture time | Fact | Fixed in GLSS 0.2 fix 1 and tested in the wasm engine |
| 15 | GLSS build script points at a `reference/` folder that is not in the repository | Fact | `Make_mod.bat` fails until it exists |

## 1. Build manifest

**Fact.** 31 files in `locations/` are not listed in `glife.qproj` ([repository-structure.md](repository-structure.md)). Most are acting and audition content. `costuming.qsrc`, one of them, is also the only place that writes `$lastwornclothingnumber` as a string (item 7), so that type conflict never reaches a build.

**Fact.** 8 files have headers that differ in case from their file names (`eto_building.qsrc` holds `# ETO_building`, and others listed in [repository-structure.md](repository-structure.md)). The engine ignores case when it looks up a location, but `$curloc` returns the header's spelling. Code that compares `$curloc` with a literal must match that spelling. The sample mod's comment "location name are case sensetive" (`isample_mod/locations/mod_isample.qsrc`) refers to this comparison, not to lookups.

**Fact.** `LOCA_events.qsrc` ends with `--- LCOA_events ---`. The build tools check only the leading `---` and a second `---` on the line, so the typo has no effect.

## 2. Comments

**Fact.** A simulation of the engine's line joining (quotes are checked before braces, then `{}`, `()` and `[]`) found 461 comments in Girl Life that span more than one physical line. All of them end where the author intended:
- 458 cover lines that are not themselves comments. These are deliberate `!{ ... }` blocks or commented-out code, such as `mirror.qsrc:595-614`, which starts with `!! if $ARGS[0] = 'routine_check': {` and ends at a lone `}`.
- 13 continue past a line end because a quote is still open there.

The 13 are:

| File | Span | Lines where a quote stays open |
|---|---|---|
| `AppearanceSystem.qsrc` | 4-8 | 5, 6 |
| `LOCA.qsrc` | 11-25 | 12-15 and later |
| `archetypes.qsrc` | 3-43 | 21 |
| `balkon.qsrc` | 117-118 | 117 |
| `balkon2.qsrc` | 228-229 | 228 |
| `music_onlinemusic.qsrc` | 372-379 | 375 |
| `music_onlinemusic.qsrc` | 386-393 | 389 |
| `npc_relationship.qsrc` | 3-61 | 22-25 and later |
| `purse_attributes.qsrc` | 18-24 | 20, 21 |
| `shoe_attributes.qsrc` | 3-45 | 23, 25, 27 |
| `stat_sklattrib.qsrc` | 4-76 | 37 |
| `telefon.qsrc` | 455-491 | 467-470 and later |
| `version.qsrc` | 18-36 | 18-21 and later |

`npc_relationship.qsrc` shows the risk. Its header block `!{ ... !}` contains four unpaired apostrophes: "doesn't" on lines 22 and 39, "NPC's" on line 37 and "don't" on line 58. They pair up, so the block closes at line 61. Removing one of them, or adding a fifth, would leave a quote open at the `}` on line 61, and the comment would continue into the `modify` handler at line 63. The same comment line elsewhere uses `PC''s` (line 52), the doubled form that is always safe.

**Fact.** GLSS has one such span: `glss/locations/mod_glss_uni_electives_functions.qsrc:8-9`, where `"talk to a` opens a double-quoted string that `classmate"` closes on the next line. Both lines are comments, so nothing is swallowed.

**Fact.** `outfit.qsrc` is a specification inside one block comment and contains no live code. `templates/comment_template.qsrc:30` uses `if $ARGS[0]:`, a string condition. 5.7 converts it to a number, which raises a type mismatch for any text that is not empty and not numeric (`legacy: src/variant.c:44-47`). The template is not in the manifest, so it is never built.

## 3. 5.7 parsing hazards

**Fact.** Two constructs parse differently on 5.7 ([version-differences.md](../engine-source-analysis/version-differences.md)):
- a comment after the colon of a multi-line `IF`/`ELSEIF`/`ELSE`/`ACT` header, which turns the header into a single-line statement on 5.7;
- `ELSEIF` inside a single-line `IF`, which 5.7 does not recognize.

A scan found zero occurrences of either in Girl Life and in GLSS. The scanner reported all three cases planted in a test file.

## 4. Engine version checks

**Fact.** Girl Life has seven version checks: six `$qspver < '5.8.0'` in `mod_system.qsrc` (lines 143, 188, 203, 238, 254, 297) and one `qspver > '5.9.2'` in `start.qsrc:12`. All compare strings.

**Inferred.** String comparison is right while every version component is one digit. A version `5.10.0` would compare less than `5.9.2` and pass the start-screen check, and less than `5.8.0`, so `mod_system` would call `addqst`, which 5.8+ engines do not have. Released versions so far are single-digit (the newest tag is 5.9.5; master is 5.9.6).

## 5. Variable table capacity

**Fact.** Under the 5.7 hash (8-bit Pearson, 256 buckets of 50 slots, `legacy: src/variables.c:149-185`), the 8,489 names Girl Life assigns by literal name fill one bucket with 55 names and the next with exactly 50. Under the 5.9.5 hash (512 buckets, 32 names each) the fullest bucket has 28.

**Inferred.**
- **When it fails.** On 5.7 a 51st name in one bucket raises "Too many variables!". That happens only if more than 50 of those 55 names exist at the same moment.
- **Why sessions matter.** In 5.7 `KILLVAR 'name'` empties a variable but leaves its name in the slot (`legacy: src/variables.c:83`), so every name ever written stays until `KILLALL`, a full `KILLVAR` or a new game. A long 5.7 session therefore keeps more names in their slots than the code holds at any one time.
- **What the scan misses.** It does not count names created through `dynamic` or `copyarr`.

The bucket is a real margin problem, not a confirmed failure. 5.9.5 has room, and master uses open addressing with a 100,000-name limit.

## 6. Elements written with both types

**Fact.** 44 (name, literal index) pairs are assigned both as a string and as a number somewhere in Girl Life. On 5.7 each element holds both values side by side; on 5.8+ the last write replaces the other type, and reading the other type then returns the empty value.

| Group | Count | Members |
|---|---|---|
| Per-call `ARGS` and `RESULT` | 9 | `ARGS[0]` to `ARGS[7]`, `RESULT` |
| Save migrations in `saveupdater` | 4 | `$pcs_makeup` (line 2576), `$pcs_throat` (2573), `sex_ev['cum_choice']` (5474), `npc_fidelity[$su0991_npcID]` (6510, 6519) |
| Temporaries | 24 | `temp`, `temp1`, `tmp`, `x`, `t`, `dummy`, `temp_*` names, `temptime[0]`, `temptime[1]`, `parsertmparr`, `temp_arrayVars['backup']` (string and numeric branches of `array` `get_me_index`) and others |
| Other | 7 | `modARGS[1]` (both forms forwarded on purpose, [code-examples.md](code-examples.md)), `sex_ev['dirty_talk']`, `lastwornclothingnumber`, `boy`, `name`, `place`, `rolan_textb_vanna` |

Two of the "other" group were traced:
- `sex_ev['dirty_talk']` is set to `1` and then to a string on the next line (`sex_ev_sex.qsrc:1154-1155`, again at 1162-1163). No code reads it as a number, so the numeric write has no effect on any engine.
- `lastwornclothingnumber` gets its string value only in the unbuilt `costuming.qsrc`.

`boy`, `name`, `place` and `rolan_textb_vanna` were not traced.

## 7. `iif` on 5.7

**Fact.** Outside string literals, 56 `iif` calls have `func(...)` in a result branch and 42 have `rand(...)` (examples: `car_funcs.qsrc:120-129`). `iif` inside `<<...>>` subexpressions in text was not counted.

**Inferred.** 5.7 evaluates both branches before choosing. Each of these calls costs an extra location call or draws an extra random number. The value chosen is still right, so the visible effect is speed and a shifted random sequence. A branch that changes variables through `func` would apply that change even when not chosen; none was traced to do so.

## 8. Boolean return conventions

**Fact.** Girl Life uses two styles for functions that return a truth value:
- 111 `iif(cond, 1, 0)`, which gives 1 or 0 on every engine;
- 164 `result = (...)`, which gives -1 or 0 on 5.7 and 1 or 0 on 5.8+.

**Inferred.** A caller that writes `if func(...) = 1:` against a function of the second kind is false on 5.7 even when the condition holds. No such caller was identified; the money API, the one most often tested with `= 1` (94 calls), uses the first style.

## 9. Small code slips

- **`dow` tests the wrong variables (Fact).** In `shortgs` `dow`, the cache test reads `Y_doy`, `M_doy`, `D_doy` (`shortgs.qsrc:125`). Those are the `doy` handler's temporaries, which it kills before returning, so the test is always false. The handler always recomputes, with the same result.
- **`time` resets the phone span (Inferred).** Each `gs 'time'` call sets `prevtotmin` to the current total (`time.qsrc:9`). `LOCA_events` checks for calls and texts between `prevtotmin` and `totminut`, so a second `gs 'time'` on the same screen with no time added in between empties that span.

## 10. Build and tooling

- **CI dev build (Inferred).** `ci_build.py` runs `./tools/qsp-cli glife.txt glife.qsp`. Girl Life's `qsp-cli` treats every bare argument as an input file and converts all of them in parallel ([dependencies-and-configuration.md](dependencies-and-configuration.md)).
  - `glife.txt` becomes `glife.qsp`, the intended output.
  - `glife.qsp` is also queued for decoding to `glife.qsps`. In a fresh CI checkout the file does not exist yet; the error is logged and the exit code stays 0. In a working copy that already has a `glife.qsp`, one thread may read it while another overwrites it.
- **Menu option `F` (Fact).** `MakeQSP.bat` accepts `F` but tests only `%action% == f` after the build, so uppercase `F` does not start the game.
- **Unpinned dependencies (Fact).**
  - `tools/Qqsp-Src/CMakeLists-qsp.txt.in:6-7` fetches `QSPFoundation/qsp` with an empty `GIT_TAG`, so it builds whatever the default branch holds. Today that is the unreleased 5.9.6, which the start screen rejects.
  - The engine's own CMake fetches Oniguruma from `master` when no system copy is found (`engine: CMakeLists.txt:52-53`).
- **Stale project note (Fact; corrected).** This repository's `CLAUDE.md` said `build.sh` runs `txtmerge.py` and `txt2gam64`; at `83b164f` it runs `qsp-cli --compile`. The note now says so.

## 11. Run-time behavior worth knowing

- **Debug console (Fact).** The objects-pane debug panel has a console that runs any typed text with `dynamic` (`onobjsel.qsrc`). The pane is visible when `cfg_vars['debug']` is set or the debug warning was not closed (`loadg.qsrc:3`).
- **No save check (Fact).** `start` sets `debug = 1`, which turns off the save identity check, so saves move between builds. Old saves rely on `saveupdater`, which ends with `gs 'saveg'` to stamp the new version.
- **Saved actions (Inferred).** Saves store the code of the current actions, and loading does not rebuild the screen ([input-output-and-persistence.md](../official-documentation/input-output-and-persistence.md)). After an update, the actions on the screen where the game was saved still run the old code until the player leaves that screen.
- **Timer music (Fact).** `counter` runs `PLAY $track_loop, volume` on every timer tick while `music_loop = 1` (`counter.qsrc`). The QSP docs say the classic player only changes the volume of a file that is already playing; other players were not checked.

## 12. GLSS

- **One-click university day (Fact; fixed in GLSS 0.2 fix 1).** Four bugs, all confirmed by running the committed code in the test harness described below:
  - **The gate matched a non-class action.** GLSS 0.2 offered the action when `instr($curacts, 'Go to your ') > 0`. `uni_grounds.qsrc:127-129` adds `Go to your room` for every student, so the action appeared at any hour Monday to Thursday. Elective actions also matched when elective automation was off, which produced a click that did nothing.
  - **Missed periods were credited.** `auto_uni_day` had no time bound, so a click at 15:00 credited both lectures, and a click at 10:15 credited the 9:00 lecture.
  - **The clock stopped at the start of the last lecture.** Real lectures end in `uni_lessons` `short_break`, whose time rules move 9:xx to 10:30, 11:xx to 12:30 and 13:xx to 14:45. GLSS skipped that step, so a Monday ended at 11:00 instead of 12:30. Without the 10:30 step, the copied nursing semester 4 rule `if hour = 10` never fired, and both lectures were credited at 9:00.
  - **The elective step moved the clock with no elective.** It advanced to 13:15 before checking that the player had an elective that day.

  The fix:
  - **Gate.** `mod_glss.qsrc` removes `Go to your room`, and `Go to your elective` when elective automation is off, from `$curacts` before the prefix search.
  - **Time bounds.** `auto_uni_day` only credits periods whose class has not started: 9:00, 11:00 and 13:15, or 9:00 for exams. These are the cut-offs `uni_lessons` `compute_stat_display` uses.
  - **Lecture end.** A new `lesson_end` handler applies the `short_break` time rules after each credited lecture.
  - **Electives.** The elective step moves the clock only after an elective was credited, and the end-of-day message counts electives.
  - **Ghost mode.** Unchanged, since it credits the whole day by design.

  **Tests.**
  - **Harness.** The published `@qsp/wasm-engine` 1.6.1 ran the real `uni_lessons`, `uni_programs` and GLSS locations. Stand-ins replaced the clock, grades and the action block of `uni_grounds`.
  - **Results.** In 12 scenarios the committed code showed every bug above. The fixed code and the rebuilt `glss.qsp` match the vanilla timeline with no engine errors: Monday ends 12:30, Wednesday 14:45, an exam day 12:00. There is no action at 15:00, and a 10:15 click credits only the 11:00 lecture.
  - **Static checks.** The Chimrod parser reports no GLSS errors or warnings before or after. `callvalidator.py` finds no invalid calls, and the 5.7 hazard scan finds none.
  - **Not tested.** The fix has not been run inside the full game or on a 5.7 player. The statements it uses (`$REPLACE` with two arguments, two-argument `INSTR`, multi-line `IF`) behave the same on 5.7 and 5.8+.
- **School gate (Fact).** The school version checks `hour < 14` and the exact hallway action names (`mod_glss.qsrc:31-36`), which appear only on the hallway screens (`gschool_lessons.qsrc:49, 63, 201`).
- **Comments (Fact).** One harmless two-line comment (section 2). No 5.7 hazards (section 3).
- **Variables (Fact).** The variable scan finds 30 names in GLSS after the fix, no dual-type pairs, and no bucket pressure. The new temporary `$glss_acts` hashes to 5.7 bucket 164, which holds 19 Girl Life names against a limit of 50.
- **Build script (Fact).** `glss/Make_mod.bat` calls `..\reference\nightly\tools\qsp-cli.exe`. `reference/` is in `.gitignore` and was absent during this research, so a fresh clone cannot build the mod without first checking out Girl Life there or editing `QSPCLI`.

## 13. Changes that would remove these risks

These are options for maintainers, not changes made here.

- **Manifest.** Register or delete the 31 unregistered files.
- **Comments.** Write apostrophes in comments as `''`, which keeps every comment's quote count even. This covers items 2 and 3.
- **Version checks.** Compare versions numerically, for example by splitting `$qspver` on `.`, before a two-digit component appears.
- **Booleans.** Return booleans through `iif(cond, 1, 0)` everywhere, or have callers test truthiness rather than `= 1`.
- **CI.** Call `qsp-cli glife.txt` with one argument, as `MakeQSP.bat` already does.
- **Pinning.** Pin the Qqsp engine fetch to a tag no newer than the start screen accepts.
- **If 5.7 support is dropped.** `LOOP`, `LOCAL`, `ARRITEM`/`SETVAR` and short-circuit `iif` would replace the label loops, global temporaries, `dynamic` array access and eager branch evaluation described in [scripting-patterns.md](scripting-patterns.md).

# Girl Life: project overview

Girl Life (English Community Version) is a large adult life-simulation game written in QSP. It is the codebase the GLSS mod in this repository extends. This page summarizes what the repository is and which engine it targets. All facts are from `https://gitlab.com/kevinsmartstfg/girl-life` at commit `83b164f` (2026-10-09) unless stated otherwise.

## 1. Size and history

| Measure | Value | How it was measured |
|---|---|---|
| Commits | 35,516 | `git rev-list --count HEAD` |
| First commit | 2015-03-07 | `git log` |
| Release tag noted in the 2026-10-14 snapshot | 0.9.9.1 | `git tag --sort=-creatordate`; dev builds are tagged `dev-<hash>` |
| Save format version in source | 0.9.9.2 | `locations/saveg.qsrc:18-21` |
| Location files | 1,429 `.qsrc` in `locations/` | file count |
| Locations in the build manifest | 1,398 | `glife.qproj` `<Location>` entries |
| Lines of QSP in `locations/` | 916,144 in all 1,434 `.qsrc` files, including `templates/` and `unused/`; 915,267 in the 1,429 top-level files | line count |
| Distinct variable names assigned by literal name | 8,489 | statement scan ([research-scope-and-methodology.md](../research-scope-and-methodology.md)) |
| Repository size on disk | about 250 MB | `du`; images, sound and video are not in Git (`.gitignore` excludes `images/`, `sound/`, `music/`) |

The game is a translation and continuation of the Russian QSP game "ЭТО" by DeGross, as its start screen says (`locations/start.qsrc`). Many internal names are transliterated Russian (`cikl` for the day cycle, `korrPar`, `kit_din`, `edaD`, `lekarstvo`).

## 2. Target engine

Girl Life is written to run on QSP 5.7.0 and on 5.8+ players up to 5.9.2:
- **Bundled players.** The classic players in `tools/Player-video/` and `tools/QSPgui/` contain a `qsp.dll` whose embedded version string is `5.7.0`. `tools/Player-original/qsp.dll` contains no readable version string. The strings were extracted from the binary files; the players were not run.
- **Upper bound.** `start` shows "RUNTIME VERSION MISMATCH" and exits when `qspver > '5.9.2'` (`locations/start.qsrc:12-18`).
- **Version branches.** Code branches on `$qspver < '5.8.0'` where statements were renamed (`locations/mod_system.qsrc:143-147`).
- **Feature avoidance.** No 5.8+ syntax is used: zero `LOOP`, `LOCAL`, `@` calls, tuples, `SETVAR`, `ARRITEM`. There are also no version-sensitive argument forms: no one-argument `RAND`, no three-argument `INSTR`.
- **Qqsp source.** The bundled Qqsp source fetches the QSP engine's default branch with no pinned tag (`tools/Qqsp-Src/CMakeLists-qsp.txt.in`). A Qqsp built from it today would contain the unreleased 5.9.6 engine and fail the start-screen version check.

See [version-differences.md](../engine-source-analysis/version-differences.md) for what this rules out.

## 3. What is in the repository

| Path | Content |
|---|---|
| `locations/` | All game code, one location per file |
| `glife.qproj` | QGen project file used as the build manifest |
| `mods/` | Three mods (Additional Adventures, Cherrypop Agency, Ibiza) with their own sources |
| `isample_mod/` | A sample mod with build scripts and a README on creating mods |
| `test/` | QSP test framework and two test locations |
| `tools/` | Compilers, players, editors, validators, analyzers, image tools, a clothing editor (Tauri), syntax packages |
| root scripts | `MakeQSP.bat`, `build.sh`, `MakeTestQSP.bat`, `Callvalidator.bat`, `Check_media.bat`, `buildHTML.*`, `.gitlab-ci.yml` |
| root text | `changes from 0_8_X to 0_8_Y.txt` (location rename lists), `Name Updates.txt`, Notepad++ and Obsidian syntax definitions |

Details in [repository-structure.md](repository-structure.md) and [dependencies-and-configuration.md](dependencies-and-configuration.md).

## 4. How the game is organized at run time

- **Entry.** `start` is the first location in `glife.qproj`, so the engine starts there. It sets global options, registers the handler locations, and shows the title screen ([gameplay-systems.md](gameplay-systems.md)).
- **Locations.** Each location acts both as a screen (entered with `gt`) and as a library of handlers selected by `$ARGS[0]` (called with `gs` or `func`). This dispatch pattern is the backbone of the codebase ([scripting-patterns.md](scripting-patterns.md)).
- **Time.** In-game time advances when code adds to `minut` and then calls `gs 'time'`, which rolls hours (running `hourly_events`) and days (running `cikl`).
- **State.** All state is global variables, mostly arrays with string keys (`katjaQW['QWstage']`, `npc_rel['A69']`, `theme_hex['accent']`).
- **Saves.** Saves are versioned with `saveg`. `loadg` runs `saveupdater` migrations on every load.
- **Mods.** Mods are loaded as libraries and called from the `$ONNEWLOC` handler `LOCA` on every location change ([gameplay-systems.md](gameplay-systems.md)).

## 5. Relationship to the QSP documentation

Girl Life predates most of the current docs and follows 5.7-era practice: label loops instead of `LOOP`, global temporaries instead of `LOCAL`, `dynamic` instead of `SETVAR`/`ARRITEM`, and `func('loc', ...)` instead of `@loc(...)`. It also contributed to the ecosystem. The docs blog credits it with the `.qsrc` source extension, and the docs list its VS Code TextMate grammar (`tools/syntax/VSCode/qsrc/syntaxes/QSP.tmLanguage.json`) among available highlighters.

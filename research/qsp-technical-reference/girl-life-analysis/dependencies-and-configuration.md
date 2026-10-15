# Girl Life: build, tooling and configuration

How Girl Life source becomes a playable `.qsp` file, which tools check it, and how GLSS reuses the same toolchain. Files are from `kevinsmartstfg/girl-life` at commit `83b164f`. No binary was executed for this page; behavior is read from scripts and source code.

## 1. Build paths

| Path | Command | Output |
|---|---|---|
| Local release-style build | `tools\qsp-cli.exe --compile locations glife.qsp glife.qproj` (`MakeQSP.bat` option B or F; `build.sh` picks `qsp-cli`, `qsp-cli-mac` or `qsp-cli.exe` by `$OSTYPE`) | `glife.qsp` with an `addbuilddate` location |
| Local debug build | `python tools\build_debug.py locations glife.txt glife.qproj` then `tools\qsp-cli.exe glife.txt` (`MakeQSP.bat` option D) | `glife.qsp` with trace hooks and the Git hash |
| Validation | `python tools\txtmerge.py locations glife.txt glife.qproj` then `tools\Parser\qsp_parser.exe --level warn glife.txt > validation.log` (`MakeQSP.bat` option V) | `validation.log` |
| CI dev build | `tools/ci_build.py build-dev` | `build/dev_glife-<date>-<hash>.qsp` |
| CI release build | `tools/ci_build.py build-release` | `build/Girl Life <version>.qsp` |
| Tests | `MakeTestQSP.bat`: `python tools\testbuilder.py locations test\testsuite-basic.qproj FALSE`, then `tools\txt2gam.exe` on the result | a test game run in `tools\QSPgui\qspgui.exe` |

**Project notes corrected.** This repository's `CLAUDE.md` said `build.sh` runs `txtmerge.py` and then `txt2gam64`. At `83b164f`, `build.sh` calls `qsp-cli --compile` directly, and `txtmerge.py` is used only for validation. The note has been updated.

**`MakeQSP.bat` option F.** The menu accepts `f` and `F` for "Full" (build and run), but after building it tests `if %action% == f`. Batch `==` is case-sensitive, so `F` builds and returns to the menu without running the game.

## 2. Merge scripts

`tools/txtmerge.py` and `tools/build_debug.py` share the manifest logic:

1. **Read the manifest.** Parse `glife.qproj` and walk `<Location>` entries in document order, including those inside `<Folder>` elements.
2. **Map names to files.** Replace `$` with `_` in each name.
3. **Find the file.** Try the folder path, then `locations/<name>.qsrc`, then a case-insensitive index of the whole tree.
4. **Append it.** Missing files print `WARNING: missing location` and are skipped, so the build still succeeds.
5. **Write the output.** The merged file is UTF-16 with CRLF line ends (`txtmerge.py:100`). If a file lacks a final newline, two are added.
6. **Add `addbuilddate`.** It holds `$builddate = '<Month DD, YYYY>'`.

`build_debug.py` differs in two ways:
- **Trace hook.** Right after each location's header line it inserts this block (`build_debug.py:88-94`):

  ```qsp
  if arrpos('$trace_locations', '<name>') > -1:
      copyarr '$trace_args', '$ARGS'
      copyarr 'trace_args', 'ARGS'
      gs 'debug_tools', 'trace', 'direct', '<name>'
  end
  ```

  The block runs at the start of every call to every location, so debug builds are slower.
- **Build data.** Its `addbuilddate` writes a UTC timestamp and `$git_hash` from `git rev-parse --short=10 HEAD`. The start screen shows that hash as "(dev build)" (`start.qsrc:40`).

## 3. Girl Life's `qsp-cli` (C++)

Source: `tools/qspcli-src/qsp-cli.cpp` (about 1,450 lines), with CMake, make and per-OS build scripts. It is unrelated to QSPFoundation's JavaScript `@qsp/cli` ([tooling-and-development.md](../official-documentation/tooling-and-development.md)).

**Command line** (`qsp-cli.cpp:1321-1445`):

```text
qsp-cli <input-files> [options]
qsp-cli --compile <input-dir> <output-file> <qproj-file> [--no-builddate]
  -d, --directory <path>   output directory
  -u, --unicode            write .qsps text as UTF-16
```

- **`--compile` mode.**
  - Merges the files listed in the manifest. Missing files print a warning (`qsp-cli.cpp:1051`).
  - Unless `--no-builddate` is given, it appends `addbuilddate` with the local date.
  - It then parses the merged text as `.qsps` and writes a binary `.qsp`.
  - `--no-builddate` is only recognized after the three compile arguments.
- **File mode.** Every argument that does not start with `-` is an input file, and `*`/`?` patterns are expanded. Files are converted in parallel threads by extension:
  - `.qsp` and `.gam` are decoded to `<stem>.qsps`;
  - `.qsps` and `.txt` are encoded to `<stem>.qsp`.

  The output name always comes from the input name; there is no output-file argument.
- **Encoding detection.** On input it checks for a BOM, then a UTF-16 byte pattern, then valid UTF-8, and falls back to Windows-1251 (`qsp-cli.cpp:196-260`).
- **Location end markers.** A line closes a location only if it starts with `---` and contains a second `---` (`qsp-cli.cpp:606-607`). The plain `--` or `-` markers used by other tools are not recognized ([tooling-and-development.md](../official-documentation/tooling-and-development.md)).
- **Base section heuristics.** Leading `*p` and `act` lines right after a header are read into the location's base description and base actions (`qsp-cli.cpp:586-713`). No Girl Life location starts this way, so this has no effect today.

**CI dev build passes an extra input.** `ci_build.py` runs `./tools/qsp-cli glife.txt glife.qsp`, which looks like "input, output" (`ci_build.py:66-68`). In file mode both are inputs:
- `glife.txt` is encoded to `glife.qsp`, the intended result.
- `glife.qsp` is queued for decoding at the same time. In a fresh CI checkout it does not exist yet; the thread logs an error and the exit code stays 0. In a working copy that already has a `glife.qsp`, one thread may read it while the other overwrites it.

This is inferred from the source; the CI job was not run.

## 4. CI pipeline (`.gitlab-ci.yml`)

| Job | Stage | Trigger | Action |
|---|---|---|---|
| `build_dev` | build | Scheduled pipeline, or manual on `master` | Installs Git, runs `ci_build.py build-dev` (debug merge plus `qsp-cli`), keeps the `.qsp` for one week |
| `release_dev` | deploy | Same | Uploads to the GitLab generic package registry as package `glife`, version `dev-<short sha>`, and creates a release with that tag |
| `build_release` | build | Tag matching `^\d+\.\d+\.\d+` | `qsp-cli --compile locations "build/Girl Life <version>.qsp" glife.qproj` |
| `release_official` | deploy | Same tag | Uploads and creates "Release <version>" |
| `cleanup_old_dev` | cleanup | Scheduled pipeline | Keeps the newest 10 `dev-` releases and deletes the others and their tags (`ci_build.py:236-262`) |

The image is `python:3.12-slim` with the `requests` package. Dev builds therefore carry the trace hooks and the Git hash; release builds do not.

## 5. Editor and repository settings

- **`.editorconfig`.**
  - All files: LF line ends, UTF-8, a final newline, trailing spaces trimmed.
  - `.qsrc` files: tab indentation, width 4.
- **`.gitignore`.**
  - Media: `images/`, `sound/`, `music/`. The game media lives outside Git and is distributed separately.
  - Build outputs: `*.qsp`, `glife.txt`, `build/`.
  - Also ignored: `mod/`, `*.sav`, player configuration files and editor files.
- **Syntax packages** in `tools/syntax/`: VS Code (a TextMate grammar the QSP docs list), Atom and Notepad++. `keywords_en.xml`, `userDefineLang*.xml` and `Obsidian.xml` at the root are further editor definitions.

## 6. Validators

| Tool | What it checks | Notes |
|---|---|---|
| `tools/Parser/qsp_parser.exe` | Syntax and lint, `--level` filter | Chimrod's parser. Run on the merged `glife.txt`; the project CLAUDE.md records a baseline of about 90 missing-location errors |
| `tools/callvalidator.py` | Every `gt`/`gs` target location and handler exists | `source=<dir>`, optional `file=<name>` or `list=<qproj>` with `folder=<dir>`. `Callvalidator.bat` uses `list=glife-validate.qproj folder=tools` |
| `tools/qsp_audit/` | 70 rule ids in the `Rule` class: parse errors, version features, project consistency, temporaries, direct money and relationship changes, and more | `--qsp-version 5.7.0|5.8.0|5.9.0` (default 5.7.0), `--json`, `--html`, `--errors-only`, `--no-cross` |
| `tools/qsp-analyser/` | C# analyzer | Not reviewed |
| `check_consistency.py`, `check_missing_media.py`, `check_images2.py`, `check_images3.py`, `Check_media.bat`, `checkpics.bat` | Media references and data consistency | Not reviewed in detail |

`qsp_audit`'s version model (`qsp_defs.py:20-26`) labels 5.8.0 as "Added LOOP, LOCAL, @/@@, ELSEIF, many functions". `ELSEIF` itself works in 5.7; what 5.7 lacks is `ELSEIF` inside a single-line `IF` (`legacy: tests/engine/conditionals.qspt:50-93`). The comment is too broad, or it refers to that inline form.

## 7. Players and editors bundled

| Path | Content | Engine |
|---|---|---|
| `tools/Player-video/` | Classic player with libvlc video support | `qsp.dll` contains the string `5.7.0` |
| `tools/QSPgui/` | Classic player | `qsp.dll` contains the string `5.7.0` |
| `tools/Player-original/` | Classic player | No readable version string |
| `tools/Qqsp-Src/` | Qqsp source, which fetches the QSP engine's default branch at build time without a pinned tag | Whatever the engine's default branch holds when built |
| `tools/QGen4`, `tools/QGen5` | Editors | Not checked |

The version strings come from scanning the binary files; no player was run.

## 8. Tests

- `test/testframework.qsrc` defines the assert helpers, `testsetup` and `_TRUE`/`_FALSE`.
- `test/test_file_template` is the starting point for a new test.
- Tests are registered in a suite file (`test/testsuite-basic.qproj`, a `<TestSuite>` with `<TestLocation name=...>` entries). It lists `test_internet_mobile` and `test_prostitution_functions`.
- `tools/testbuilder.py <src> <suite> <save_enabled>` merges the game with the listed tests and writes `_ISTEST = 1` into the result (`testbuilder.py:119, 185`).

## 9. Mods

- **Sample mod.** `isample_mod/` has 13 `mod_isample_*` locations and `isample.qproj`. Its `Make_mod.bat`/`.sh` point at `..\tools\` for the player and QGen. The locations cover:
  - the dispatcher, setup, options, readme and save updater;
  - hooks for the disabled `stat`, `stat_display`, `arousal` and `func` handlers;
  - `_sleep` and `_schedule`, whose headers say "Starting at version 0.10.0.0". At `83b164f` nothing calls them: the `sleep` handler builds the bare dispatcher name because its `_sleep` suffix is commented out (`mod_system.qsrc:14-15`), and no `schedule` handler exists;
  - location-specific hooks.
- **Bundled mods.** `mods/` holds Additional Adventures, Cherrypop Agency and Ibiza, each with its own sources.
- **Installing.** A built mod is a `.qsp` copied to the game's `mod/` folder and enabled from Settings, Mods ([gameplay-systems.md](gameplay-systems.md)).

## 10. GLSS uses the same toolchain

`glss/Make_mod.bat` in this repository runs:

```bat
..\reference\nightly\tools\qsp-cli.exe --compile locations glss.qsp glss.qproj --no-builddate
```

- **Toolchain.** GLSS uses Girl Life's own `qsp-cli` in `--compile` mode. A GLSS `.qsrc` file missing from `glss.qproj` is left out with only a warning, as in Girl Life.
- **No build date.** `--no-builddate` keeps an `addbuilddate` location out of the mod. `INCLIB` would skip it anyway because the game already has one.
- **Missing compiler path.** `reference/` is listed in this repository's `.gitignore` and was not present on disk during this research. The build script needs a local Girl Life checkout at `reference/nightly/` or an edited `QSPCLI` path.

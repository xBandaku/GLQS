# Tooling and development workflow

The docs' "All Together" page names the tools in the QSP workflow. This page describes each one from its repository, notes how they differ, and records where Girl Life's tooling fits. Repository commits are in [source-index.md](../source-index.md); a per-repository inventory is in [repository-inventory.md](../engine-source-analysis/repository-inventory.md).

## 1. The workflow in the docs

The docs ("All Together") describe three stages:

1. **Writing.** Use QGen (which compiles straight to `.qsp`), VS Code with an extension, Sublime Text with JAD_for_QSP, or any text editor producing `.qsps`/`.qsrc` text.
2. **Compiling.** Text is turned into a binary `.qsp` with qsp-cli or TXT2GAM.
3. **Playing and distributing.** Classic and Navigator players use QSPLib directly; qSpider uses qsp-wasm-engine, a WebAssembly build of QSPLib. Games are published in the qsp.org catalog or as qSpider standalone builds on GitHub Pages or itch.io, and qSpider accepts `?catalogId=` and `?config=` URLs.

The docs recommend hosting the game online and giving players a direct link.

## 2. Text source format

There is no formal specification of the text format in the docs. The engine's master grammar (`help/qsp_grammar.peg:18-39`) and the tools agree on the core:

```qsp
# location_name
code
--- location_name ---------------------------------
```

They differ on details:

| Detail | TXT2GAM 0.5.0-b3 | `@qsp/converters` 1.0.1 (used by `@qsp/cli`) | Girl Life `qsp-cli.cpp` |
|---|---|---|---|
| End marker | line starting `--` (configurable) | line starting `-` | line starting `---` that contains `---` again |
| Base description | `! BASE` ... `! END BASE` section with `*P`, `*PL` or quoted lines | not read; writer emits `*pl '...'` lines | `*p...` lines directly after the header |
| Base actions | `ACT ...: ... END` inside the base section | not read; writer emits `act '...':` code | `act ` lines directly after the header or description, code until a line exactly `end` |
| Encodings | UTF-8, UTF-16 (BOM detection), ANSI with `-a` | caller supplies a UTF-8 string; `@qsp/cli` detects the file encoding | detects UTF-8, UTF-16 LE/BE and falls back to CP1251 when reading text files (`qsp-cli.cpp:183-298`); `--compile` reads `.qsrc` files |
| Quote tracking across lines | yes | yes | yes |

Sources: `txt2gam: src/t2g_api.h:13-18`, `src/locdata.h:14-19`, `src/locations.c:215`; `converters: src/readers/qsps.ts`, `src/writers/qsps.ts`; `girl-life: tools/qspcli-src/qsp-cli.cpp:586-713`.

**Consequence.** A binary-to-text conversion with `@qsp/converters` turns base descriptions and base actions into ordinary code, so `$DESC` returns `''` after a round trip. TXT2GAM keeps them in its base section. The docs' statement that `$DESC` is useless for text-editor games reflects the converter behavior.

## 3. Tools

### TXT2GAM (`QSPFoundation/txt2gam`, C)

```text
txt2gam [options] <input> <output>
  -c  encode text into game (default)    -d  decode game into text
  -t  extract strings                    -q  extract q-strings
  -o  old game format                    -a  ANSI mode
  -s  location start prefix (default #)  -e  location end prefix (default --)
  -p  password (default "No")
```

(`app/src/main.c:219-243`). Has a WebAssembly build script. Girl Life ships `txt2gam.exe`, `txt2gam64.exe`, `txt2gam.linux`, `txt2gam.mac` but builds with its own `qsp-cli`.

### qsp-cli (`QSPFoundation/qsp-cli`, JavaScript, npm `@qsp/cli`)

A 95-line command that converts between `.qsp`/`.gam` (binary) and `.qsps`/`.qsp-txt`/`.txt-qsp` (text) based on the file extension, with glob support and a `--directory` option. It uses `@qsp/converters`. **It is not the `qsp-cli` that Girl Life and GLSS run**, which is Girl Life's own C++ compiler with a `--compile <dir> <out.qsp> <project.qproj>` mode ([dependencies-and-configuration.md](../girl-life-analysis/dependencies-and-configuration.md)).

### converters (`QSPFoundation/converters`, TypeScript, npm `@qsp/converters`)

`readQsp`, `readQsps`, `writeQsp`, `writeQsps`. Text writer output: `# name`, description as `*pl`/`*p` lines, actions as `act` blocks, code, then `--- name ---------------------------------`.

### qsp-lsp (`QSPFoundation/qsp-lsp`, TypeScript)

VS Code extension with a language server and a tree-sitter grammar (README):
- highlighting, completion, hover, signature help, go to definition, references, rename;
- location management commands (new, sort, duplicate, move, split into files);
- "Export QSP Game" and "Run" through TXT2GAM, configured per workspace by `txt2gam.json` (`outputFile`, ordered `files` globs; default: all `.qsps`/`.qsrc` alphabetically);
- ships its own `qsp_grammar.peg`, which differs from both the 5.9.5 and the master grammar in the engine repository.

### Qsp.FSharp (`QSPFoundation/Qsp.FSharp`, F#)

Parser to an AST, printer, language server and CLI. The docs say it parses the whole file at once, unlike QSPLib, and aims to follow the specification with some author-specific interpretations. README and docs only; the F# sources were listed but not analyzed line by line.

### QGen (`QSPFoundation/qgen`, C++ wxWidgets) and qgen.qt

The visual editor that edits the binary format directly, including base descriptions and base actions. `qgen.qt` is an early Qt port (headers and a presenter skeleton). Girl Life ships QGen 4 and QGen 5 binaries and opens its `.qproj` project file with QGen (`MakeQSP.bat` option Q). `.qproj` is QGen's project format: `<QGen-project version="4.0.0 beta 1"><Structure><Folder name="..."><Location name="..."/></Folder></Structure></QGen-project>`.

### Sublime Text package (`QSPFoundation/sublime_text_qsp_package`, Python)

Syntax, snippets, and the qSpy builder that assembles multi-file projects, with a preprocessor (`qSpy/preprocessor/`). README in Russian; not analyzed in depth.

### qsp-test-engine (`QSPFoundation/qsp-test-engine`, TypeScript)

A test harness built on `@qsp/wasm-engine`. `TestClient.start(basePath, gameFile, startingLocation)` opens a game and drives it with Vitest assertions on the main text and actions. Its mock games (`tests/mocks/*.qsps`) end locations with a single `-`.

### qsp-toolbox (`QSPFoundation/qsp-toolbox`, Bash and gawk)

Compatibility scripts for a game archive: unpack, convert to text, find identifiers that clash with newer keywords (`find_same_keywords.sh`), rename them with a template (`replace_keywords.sh`, default `_{}`), convert back and pack. Its delimiter set is the 5.9.5 one (`" \t&'\"()[]=!<>+-/*:,{}\r\n"`, `_replace_keywords.awk`).

### Players

| Player | Engine | Notes |
|---|---|---|
| Classic (`qspgui`) | QSPLib (current) | wxWidgets; `$qspver` returns `"<version> (classic)"`; `EXEC:` links; no `EXEC` statement handler; `settimer 0` stops the timer |
| Classic Legacy (`qspgui-legacy`) | qsp-legacy (5.7.0 fork) | For games that need 5.7 behavior |
| qSpider (`qspider`) | `@qsp/wasm-engine` | Web and desktop (Tauri). Always renders HTML. `game.cfg` (TOML) configures resources, fonts, hotkeys and JavaScript; `EXEC` statement commands `event:`, `action:`, `change_theme:` and others |
| Navigator | QSPLib (per docs) | Not in the QSPFoundation organization; not reviewed |
| Qqsp | QSPLib | Not a QSPFoundation repository; Girl Life ships its source in `tools/Qqsp-Src`, which fetches the engine's default branch with no pinned tag |
| Quasporium | qsp-legacy (per its README) | Android; not reviewed |

### qspider-standalone-game-template and gamekit

The template is a GitHub repository template with Actions workflows that publish a game to GitHub Pages and build Tauri desktop releases, configured by `game.cfg` and `game.build.conf.json`. Gamekit bundles a set of older sample games (`contents/games/*`, binary `.qsp` with music) and an Inno Setup installer script.

## 4. Validation and analysis tools

| Tool | Source | What it checks |
|---|---|---|
| QSPLib itself | engine | Only at run time; syntax errors appear when a line runs (docs: "lazy" parser) |
| qsp-lsp diagnostics | qsp-lsp | Parse errors and lint checks in the editor |
| QSP Analyser | external (forum download, C#) | Error list and variable lists; recommended by the 2026 blog post for migration |
| Chimrod `qsp_parser` | bundled in Girl Life `tools/Parser` | Type checks (string vs number variables), dead ends (branches without `gt`), syntax; `--level` filter (README) |
| `qsp_audit` | Girl Life `tools/qsp_audit` (Python, about 14,000 lines) | Version compatibility per target (5.7.0, 5.8.0, 5.9.0), undefined locations, duplicate labels and acts, argument counts, subexpression quoting, missing media, unreachable code, temp variables not killed, many style rules |
| `callvalidator.py` | Girl Life `tools/` | Every `gt`/`gs` target exists and has a matching `$ARGS[0]` handler |

GLSS uses the Chimrod parser on the merged game plus mod text, as described in this repository's `CLAUDE.md`.

# QSPFoundation repository inventory

All 21 public repositories of https://github.com/QSPFoundation as listed by the GitHub API on 2026-10-14, with what each contains, how deeply it was examined, and what it contributed to this reference. Commit hashes are in [source-index.md](../source-index.md). None of the repositories is archived.

Depth levels:
- **Full**: every source file relevant to language semantics was read.
- **Targeted**: the files that answer specific questions were read; the rest were listed.
- **Survey**: README, file list and a sample of files.
- **Excluded**: not related to QSP.

| Repository | Language | Last push | Purpose | Depth | Contributed |
|---|---|---|---|---|---|
| `qsp` | C | 2026-10-13 | The QSP library (QSPLib): parser, interpreter, save format. Tags 5.9.4, 5.9.5; `master` is 5.9.6 in progress | Full for `qsp/*.c` and `qsp/*.h` (except `memwatch.*`, the debug allocator, and the generated `towlower.c`/`towupper.c` tables); grammar and file-format notes; 5.9.5 and 5.9.4 diffed for every behavior cited | Almost every semantic rule in this reference |
| `qsp-legacy` | C | 2026-10-09 | The 5.7.0 library as a maintained fork (first commit 2025-10-02, 143 commits) | Targeted: preprocessing, statement table, expression table and evaluator, variables, location calls, errors | All 5.7 behavior |
| `qspfoundation.github.io` | TypeScript (Docusaurus) | 2026-05-13 | Documentation site dev.qsp.org and its blog | Full: all 15 docs pages in both locales, all 5 blog posts | [official-documentation/](../official-documentation/documentation-index.md) |
| `qspgui` | C++ (wxWidgets) | 2026-10-13 | Classic desktop player | Targeted: callbacks, link handling, version string, variable reads | Player behavior (`EXEC:` links, `settimer 0`, `$qspver`) |
| `qspgui-legacy` | C++ | 2026-10-10 | Classic player built on qsp-legacy | Survey | Existence of a maintained 5.7 player |
| `qsp-wasm-engine` | TypeScript, C | 2026-02-22 | WebAssembly build of QSPLib (fetches the engine's `master` at build time) and a JavaScript API; 26 engine test files (6,640 lines) and 4 API test files | Full for `tests/engine/*`; targeted for `src/lib/qsp-api.ts` | Executable evidence for 5.9.5-era behavior and error codes |
| `qspider` | TypeScript (Nx monorepo, Tauri) | 2026-04-15 | Web and desktop player | Targeted: `EXEC` command handling, player docs (`apps/docs/docs/*.md`) | qSpider-specific features |
| `txt2gam` | C | 2026-06-11 | Text to binary converter and back | Targeted: options, location and base-section parser, markers | Text format details |
| `converters` | TypeScript | 2022-07-12 | `@qsp/converters` readers and writers for binary and text formats | Full (`src/readers`, `src/writers`) | Text format differences |
| `qsp-cli` | JavaScript | 2024-11-12 | `@qsp/cli` command that converts files by extension | Full (`cli.js`, 95 lines) | Tool distinction from Girl Life's compiler |
| `qsp-lsp` | TypeScript | 2026-06-11 | VS Code extension: LSP server, tree-sitter grammar, build and run through TXT2GAM | Survey (README, file list, grammar file comparison) | Editor tooling, grammar divergence |
| `Qsp.FSharp` | F# | 2024-12-01 | F# parser, printer, language server, CLI | Survey | Docs' parser description |
| `Qsp.FSharp.VsCode` | F# | 2024-10-01 | VS Code client for Qsp.FSharp | Not cloned (role taken from docs) | None |
| `qsp-test-engine` | TypeScript | 2025-07-28 | Vitest harness driving `@qsp/wasm-engine` | Survey (`src/testClient.ts`, mocks) | Testing options for games |
| `qsp-toolbox` | Shell, gawk | 2026-03-19 | Scripts to migrate old games (find and rename identifiers that clash with keywords) | Targeted (`compat/*`) | Keyword clash migration |
| `qgen` | C++ (wxWidgets) | 2025-11-28 | QGen game editor | Survey | Editor and `.qproj` format |
| `qgen.qt` | C++ (Qt) | 2025-11-28 | Early Qt port of QGen | Survey (headers only) | None beyond its existence |
| `sublime_text_qsp_package` | Python | 2026-06-29 | Sublime Text syntax and the qSpy builder with a preprocessor | Survey | Editor tooling |
| `gamekit` | Inno Setup | 2024-12-14 | Installer bundling sample games | Survey | Sample material (binary games, not analyzed) |
| `qspider-standalone-game-template` | (YAML, JSON) | 2024-02-11 | Template for publishing a game with qSpider | Survey | Distribution workflow |
| `traceface` | Python | 2025-05-12 | Webcam face tracking for VTube Studio | Excluded | Unrelated to QSP |

## Notes per repository

### qsp (QSPLib)

- Build: CMake, C90, shared library `qsp`, always compiled with `_UNICODE` (`CMakeLists.txt:19, 109-110`). Optional Java (JNI) bindings with `-DBUILD_JAVA=ON`.
- Oniguruma (regex) is fetched with `FetchContent` from `https://github.com/kkos/oniguruma.git` at `GIT_TAG master`, so the regex library version is not pinned (`CMakeLists.txt:51-53`) unless `USE_INSTALLED_ONIGURUMA` is set.
- `help/qsp_grammar.peg` is an Ohm grammar; its header says to test it at ohmjs.org/editor. It documents the syntax but is not used by the engine, which parses with hand-written C.
- The last 41 commits after 5.9.5 (2026-10-01 to 2026-10-13) rewrote preprocessing (statements and expressions compiled once and cached), switched variables and locations to hash tables, and changed semantics: unprefixed names became untyped, `?` was added as an undefined value, `OBJ` went back to returning 0/1 with `COUNTOBJ(name)` returning counts, `KILLVAR` without arguments clears only globals, and the minimum loadable save version became 5.9.6. See [version-differences.md](version-differences.md).

### qsp-legacy

The README calls it "the older version of the QSP Library", version 5.7.0 in `CMakeLists.txt`. Its history starts at 2025-10-02, so it is a reconstruction plus maintenance, not the original 5.7.0 history. Fixes since then include "Stop at the end of lines after a trailing line continuation" and "Keep text indices of arrays unique" (2026-10). Behavior statements about "5.7" in this reference are statements about this source. Whether every detail matches the 5.7.0 binary that Girl Life bundles was not tested.

### qsp-wasm-engine

- Version 1.6.1. `src/qsplib/CMakeLists-qsp.txt.in` fetches the engine at `GIT_TAG master`, so a release reflects whatever engine commit was current at build time.
- The test suite's expected error codes (12 for type mismatch, 11 for division by zero, 17, 18, 29) match the 5.9.5 numbering, which dates the expectations to before the October 2026 engine changes.
- `tests/errors-to-test.md` (Russian) lists limits to test: 50 visible actions, 30 nested brackets, 100 operations per level.

### qspider

- `libs/game-state/src/qspider-commands.ts` maps `EXEC` statement text (prefixes `action:`, `event:`, `change_theme:`, `update_region:`, `scroll_region:` and others) to player behavior.
- `apps/docs/docs/` documents `game.cfg`, fonts, hotkeys and JavaScript integration; JavaScript receives `qspider-event` DOM events from QSP.

### Inaccessible or not examined

- No repository was inaccessible.
- Players outside the organization named in the docs (Navigator, Quasporium) and Qqsp were not reviewed, except Girl Life's bundled Qqsp source build files.
- The F#, Python and Qt editor code bases were surveyed, not analyzed.

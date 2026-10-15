# Source index

This source index was carried over from the GLSS research dated 2026-10-14. Commit pins, clone dates and release descriptions record that research; sources were not independently reverified for this copy. GLSS source references remain historical context rather than GLQS evidence.

Every claim in this reference points back to one of the sources below. Repositories were cloned on 2026-10-14 and read at the commits listed here. Line links use these commit hashes so they stay valid when the repositories move on.

## GLQS inspection on 2026-10-14

The project-specific pages inspect GLQS commit `6de0a2ce7081a1e4275bffef39c2e86cc65e3b54` (version 0.39.0). The upstream integration comparison uses a clean, detached `reference/nightly/` checkout at Girl Life commit `83b164f64224f1ba88fd409469c1a9379ad34f86`. That checkout is ignored and read-only; its name does not establish an installed game's revision or automatically follow upstream. ([01_setup.qsps:3](../../src/01_setup.qsps#L3), [upstream pin](https://gitlab.com/kevinsmartstfg/girl-life/-/tree/83b164f64224f1ba88fd409469c1a9379ad34f86))

Local source links use relative paths and `file:line` labels. Links into `reference/nightly/` require the ignored checkout. Current measurements and executed checks are in [project-overview.md](glqs-analysis/project-overview.md) and [build-and-validation.md](glqs-analysis/build-and-validation.md); they are separate from the inherited library's evidence below. No fresh external documentation or engine audit was performed.

## Inherited pinned commits

| Short name | Repository | Commit read | Commit date | Notes |
|---|---|---|---|---|
| docs | https://github.com/QSPFoundation/qspfoundation.github.io | `8dc098fba14fe7cb84ce96d53f03bc6569ee07f1` | 2026-05-13 | Source of https://dev.qsp.org |
| engine | https://github.com/QSPFoundation/qsp | `00faed4590a9032f0cd9e436663123503de5a4ce` | 2026-10-13 | `master`, 41 commits after tag 5.9.5, CMake version 5.9.6 (unreleased) |
| engine-5.9.5 | same | tag `5.9.5` = `0445921b0640c68bc7e7ab03393fc15e8373c8e9` | 2025-11-17 | Release used in the 2026-10-14 snapshot |
| engine-5.9.4 | same | tag `5.9.4` = `8ebe46a8d8fa8291dd1a01528f1c3f256f322593` | 2025-09-21 | Previous release |
| legacy | https://github.com/QSPFoundation/qsp-legacy | `3e725e1215a12ac3d9790a8349425c11f13c275c` | 2026-10-09 | Maintained fork of the 5.7.0 library; first commit 2025-10-02 |
| qspgui | https://github.com/QSPFoundation/qspgui | `f67580195c525ef16e4ff164689d7374bdf35e8d` | 2026-10-13 | Classic desktop player |
| qspgui-legacy | https://github.com/QSPFoundation/qspgui-legacy | `aff5e17eb6eb4e79cb3467667c361e39b75f9fd4` | 2026-10-10 | Classic player built on qsp-legacy |
| wasm | https://github.com/QSPFoundation/qsp-wasm-engine | `71d5f69a397f94573dfaae69ef2fab231904215f` | 2026-02-22 | WebAssembly wrapper and the largest behavior test suite |
| qspider | https://github.com/QSPFoundation/qspider | `ee2f7bff004723896a39f1535ba9ce087065a5d7` | 2026-04-15 | Web and desktop player |
| txt2gam | https://github.com/QSPFoundation/txt2gam | `5eb5b02b01638d3b845f42811babf0d55a1e2da9` | 2026-06-11 | Text to binary converter, tag v0.5.0-b3 |
| converters | https://github.com/QSPFoundation/converters | `854c76a06d1f41eaebb7bac80e6470e64926ad0c` | 2022-07-12 | `@qsp/converters`, tag v1.0.1 |
| qsp-cli (JS) | https://github.com/QSPFoundation/qsp-cli | `6b1749096384809c780a82d702e8d391e2ca7202` | 2024-11-12 | `@qsp/cli`, tag v1.0.5 |
| qsp-lsp | https://github.com/QSPFoundation/qsp-lsp | `9c302e537d95321e0109e38d9774b9a31124ce37` | 2026-06-11 | VS Code extension |
| Qsp.FSharp | https://github.com/QSPFoundation/Qsp.FSharp | `cfb25cb26ed205606ef50f7f387035654cdbbf68` | 2024-09-09 | F# parser and language server |
| qsp-test-engine | https://github.com/QSPFoundation/qsp-test-engine | `c7e79a448b33bea56bcff1b02f656fc4c0c624a8` | 2025-07-07 | Tag v0.2.4 |
| qsp-toolbox | https://github.com/QSPFoundation/qsp-toolbox | `4f023114b273acf23bba650be6bc6ab0a94d1ce9` | 2026-03-19 | Shell scripts |
| qgen | https://github.com/QSPFoundation/qgen | `8e17d5249f13501b29cee5cc946cbbc41093cb47` | 2025-11-28 | wxWidgets editor |
| qgen.qt | https://github.com/QSPFoundation/qgen.qt | `57a4f0e04755e4d297ed17c5ba214d427298388d` | 2025-11-28 | Qt editor skeleton |
| sublime | https://github.com/QSPFoundation/sublime_text_qsp_package | `0f3cb59a9a50cde4f37f2312266d6fd670398f10` | 2026-06-29 | Sublime Text package and qSpy builder |
| gamekit | https://github.com/QSPFoundation/gamekit | `27f01a2df0cb87a830203b63113839d41831ce5b` | 2024-11-08 | Bundle of sample games |
| standalone template | https://github.com/QSPFoundation/qspider-standalone-game-template | `58ea6753069f63e2f0ddaca42e5fe7326bdc9151` | 2024-02-11 | qSpider packaging template |
| girl-life | https://gitlab.com/kevinsmartstfg/girl-life | `83b164f64224f1ba88fd409469c1a9379ad34f86` | 2026-10-09 | `master` at the research pin; release tag 0.9.9.1 noted in that snapshot |

Not cloned: `traceface` (a webcam face-tracking utility for VTube Studio, unrelated to QSP) and `Qsp.FSharp.VsCode` (its role was checked through the docs and the engine README only).

## URL patterns

Use these patterns to turn a file and line reference in this reference into a link.

| Source | Pattern |
|---|---|
| engine | `https://github.com/QSPFoundation/qsp/blob/00faed4590a9032f0cd9e436663123503de5a4ce/qsp/<file>#L<line>` |
| engine-5.9.5 | `https://github.com/QSPFoundation/qsp/blob/5.9.5/qsp/<file>#L<line>` |
| legacy | `https://github.com/QSPFoundation/qsp-legacy/blob/3e725e1215a12ac3d9790a8349425c11f13c275c/src/<file>#L<line>` |
| docs (English) | `https://github.com/QSPFoundation/qspfoundation.github.io/blob/8dc098fba14fe7cb84ce96d53f03bc6569ee07f1/i18n/en/docusaurus-plugin-content-docs/current/<path>` |
| docs (Russian original) | `https://github.com/QSPFoundation/qspfoundation.github.io/blob/8dc098fba14fe7cb84ce96d53f03bc6569ee07f1/docs/<path>` |
| wasm tests | `https://github.com/QSPFoundation/qsp-wasm-engine/blob/71d5f69a397f94573dfaae69ef2fab231904215f/tests/engine/<file>` |
| girl-life | `https://gitlab.com/kevinsmartstfg/girl-life/-/blob/83b164f64224f1ba88fd409469c1a9379ad34f86/<path>#L<line>` |

In the other documents, a reference written as `engine: qsp/variables.c:373` means the `engine` row above, file `qsp/variables.c`, line 373. `legacy: src/mathops.c:151` means the legacy repository. `girl-life: locations/time.qsrc:14` means the Girl Life repository.

## Documentation pages (live site)

| Page | URL |
|---|---|
| Introduction | https://dev.qsp.org/docs/intro/ |
| All Together | https://dev.qsp.org/docs/all-together |
| QSP Language index | https://dev.qsp.org/docs/language/ |
| Keyword index | https://dev.qsp.org/docs/language/qsp-keywords/ |
| Operators | https://dev.qsp.org/docs/language/qsp-keywords/qsp-keywords-operators |
| Statements | https://dev.qsp.org/docs/language/qsp-keywords/qsp-keywords-statements |
| Functions | https://dev.qsp.org/docs/language/qsp-keywords/qsp-keywords-functions |
| System variables | https://dev.qsp.org/docs/language/qsp-keywords/qsp-keywords-sys-var |
| Syntaxemes | https://dev.qsp.org/docs/language/qsp-keywords/qsp-keywords-syntaxems |
| Parsers | https://dev.qsp.org/docs/parsers/ |
| Syntax highlighting | https://dev.qsp.org/docs/syntax-highlighting |
| Collaborative development | https://dev.qsp.org/docs/co-development/ |
| Blog index | https://dev.qsp.org/blog |

Blog source files read: `blog/2024-07-28-documentation-development.md`, `blog/2024-08-06-syntax-highlighting.md`, `blog/2024-08-15-docs-add-chapters-of-keywords-etc.md`, `blog/2024-11-16-update-keywords-to-590.md`, `blog/2026-01-01-transition-570-at-59x/index.md`.

## Key engine files

| File | What it holds |
|---|---|
| `help/qsp_grammar.peg` | Official PEG grammar (Ohm syntax) and operator priority table |
| `help/gam_desc.txt` | Binary game file format |
| `qsp/bindings/qsp.h` | Public API: error codes, value types, callbacks |
| `qsp/declarations.h` | Special characters, delimiter set, system location variable names |
| `qsp/codetools.c` | Source preprocessing: line joining, statement splitting, label collection |
| `qsp/statements.c` | Statement table; execution of lines, IF, LOOP, JUMP, EXIT |
| `qsp/mathops.c` | Expression compiler and evaluator; operator and function table |
| `qsp/variant.c` | Value conversion, comparison, arithmetic, concatenation |
| `qsp/variables.c` | Variable storage, scopes, array indices, assignment, array statements |
| `qsp/locations.c` | Location lookup, GOSUB/FUNC/GOTO execution, handler arrays |
| `qsp/actions.c`, `qsp/objects.c`, `qsp/menu.c`, `qsp/playlist.c` | Actions, inventory, menus, sound bookkeeping |
| `qsp/game.c`, `qsp/coding.c` | Loading games, INCLIB, saving and loading state |
| `qsp/bindings/default/default_control.c` | Entry points the players call |

## Key Girl Life files

| File | Role |
|---|---|
| `glife.qproj` | Build manifest (1,398 locations) |
| `locations/start.qsrc` | First location, global settings, player version guard |
| `locations/LOCA.qsrc` | `$ONNEWLOC` handler |
| `locations/saveg.qsrc`, `locations/loadg.qsrc`, `locations/saveupdater.qsrc` | Save versioning and migrations |
| `locations/mod_system.qsrc` | Runtime mod framework |
| `locations/time.qsrc`, `locations/cikl.qsrc` | Clock normalization and day rollover |
| `locations/shortgs.qsrc`, `math.qsrc`, `random.qsrc`, `string.qsrc`, `array.qsrc`, `wrap.qsrc` | Utility libraries |
| `tools/qspcli-src/qsp-cli.cpp` | Girl Life's own compiler (unrelated to QSPFoundation's JavaScript qsp-cli) |
| `tools/txtmerge.py`, `tools/build_debug.py`, `tools/ci_build.py` | Merge and build scripts |
| `tools/qsp_audit/` | Python static analyzer |
| `test/testframework.qsrc` | QSP-level test helpers |

## Sources referenced but not reviewed

These appear as links inside the reviewed sources. They were outside the three sources named in the task and were not read, so nothing in this reference depends on them.

- https://wiki.qsp.org (the online help that the 2026 blog post calls the place where all changes are documented)
- VK articles listed in the 2026 blog post (`vk.com/@qsplayer-novovvedeniya-v-qsp-580`, `-590`, `-591`, `-592-594`, `vk.com/@qsplayer-massivy-uzhe-ne-te`)
- The QSP Analyser download on qsp.org forums and mega.nz
- https://github.com/AleksVersus/howdo_faq and https://github.com/AleksVersus/JAD_for_QSP

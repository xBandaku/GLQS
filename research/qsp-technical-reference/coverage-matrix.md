# Coverage matrix

This matrix records the GLSS research dated 2026-10-14 and was carried over without independent reverification. Its coverage statuses describe that work. GLQS coverage is recorded separately in [glqs-analysis/](glqs-analysis/project-overview.md); a GLSS status or result does not validate GLQS.

What this reference covers, at what depth, and what remains open.

## GLQS coverage added on 2026-10-14

| Page | Current scope and limits |
|---|---|
| [project-overview.md](glqs-analysis/project-overview.md) | Measured manifests, location/route inventory, navigation and literal metadata rows at GLQS `6de0a2c` |
| [build-and-validation.md](glqs-analysis/build-and-validation.md) | All 20 existing tests passed without skips; full artifact conversion passed with `@qsp/cli@1.0.5`; no new CI run or player test |
| [gameplay-integration.md](glqs-analysis/gameplay-integration.md) | Targeted source comparisons against Girl Life `83b164f`; checked hooks and selected feature contracts, with unaudited areas stated |
| [implementation-observations.md](glqs-analysis/implementation-observations.md) | Static-check limits, fixed rank request, derived volleyball values, state lifetimes and proposed runtime checks |

These are GLQS-specific observations, separate from the inherited status codes and coverage below. Passing static checks and binary conversion do not establish gameplay behavior.

Inherited status codes:

| Code | Meaning |
|---|---|
| **Full** | Read in full and cross-checked against source |
| **Targeted** | The parts relevant to QSP semantics, Girl Life or GLSS were read |
| **Survey** | Purpose, structure and a sample were reviewed |
| **Open** | Not covered; listed in section 6 |

## 1. Documentation (dev.qsp.org, docs commit `8dc098f`)

All 15 pages exist in Russian and English; both locales were compared.

| Page | Status | Main use in this reference |
|---|---|---|
| `intro.md` | Full | [documentation-index.md](official-documentation/documentation-index.md) |
| `all-together.md` | Full | [tooling-and-development.md](official-documentation/tooling-and-development.md) |
| `language/index.md` | Full (heading only) | documentation-index |
| `language/qsp-keywords/index.md` | Full | version tags in [version-differences.md](engine-source-analysis/version-differences.md) |
| `qsp-keywords-operators.md` | Full | [expressions-and-operators.md](official-documentation/expressions-and-operators.md) |
| `qsp-keywords-statements.md` | Full | [functions-and-commands.md](official-documentation/functions-and-commands.md), [control-flow.md](official-documentation/control-flow.md) |
| `qsp-keywords-functions.md` | Full | [built-in-api-reference.md](official-documentation/built-in-api-reference.md) |
| `qsp-keywords-sys-var.md` | Full | built-in-api-reference, [execution-model.md](official-documentation/execution-model.md) |
| `qsp-keywords-syntaxems.md` | Full | [language-syntax.md](official-documentation/language-syntax.md), [variables-and-data-types.md](official-documentation/variables-and-data-types.md) |
| `parsers/index.md`, `qsp-fsharp-parser.md`, `qsp-lsp.md`, `qsplib-parser.md` | Full | tooling-and-development |
| `syntax-highlighting.md` | Full | tooling-and-development |
| `co-development/index.md` | Full | tooling-and-development |
| Blog: 5 posts (2024-07-28 to 2026-01-01) | Full | the 2026 migration post throughout the version pages |

## 2. QSPFoundation repositories

Details per repository are in [repository-inventory.md](engine-source-analysis/repository-inventory.md).

| Repository | Status |
|---|---|
| `qsp` (engine; master, 5.9.5, 5.9.4) | Full for `qsp/*.c`, `qsp/*.h` and the grammar |
| `qsp-legacy` (5.7) | Targeted, including all `.qspt` tests used as evidence |
| `qspfoundation.github.io` | Full |
| `qsp-wasm-engine` | Targeted (tests read as specifications) |
| `qspgui` | Targeted |
| `qspider` | Targeted |
| `txt2gam`, `converters`, `qsp-cli` (JS) | Targeted to Full |
| `qsp-lsp`, `Qsp.FSharp`, `qsp-test-engine`, `qsp-toolbox`, `qgen`, `qgen.qt`, `sublime_text_qsp_package`, `gamekit`, `qspider-standalone-game-template`, `qspgui-legacy` | Survey |
| `Qsp.FSharp.VsCode` | Not cloned; role from the docs |
| `traceface` | Excluded, not QSP related |

## 3. Language features

Columns are the fields the brief asked for. "Y" means the field is covered for that feature, "P" partial, "-" not applicable.

| Feature | Syntax | Semantics | Return and side effects | Constraints and edge cases | Engine implementation | Version notes | Girl Life usage | Example | Page |
|---|---|---|---|---|---|---|---|---|---|
| Locations, source text, end markers | Y | Y | - | Y | Y | Y | Y | Y | LS 1, [tooling](official-documentation/tooling-and-development.md) |
| Statements, `&`, case | Y | Y | - | Y | Y | Y | Y | Y | LS 2-3 |
| Comments | Y | Y | - | Y | Y | Y | Y | Y | LS 4 |
| Strings, subexpressions | Y | Y | Y | Y | Y | Y | Y | Y | LS 5, EO 9 |
| Line continuation | Y | Y | - | Y | Y | contradiction C1 | Y (none used) | Y | LS 6-7 |
| Names and delimiters | Y | Y | - | Y | Y | Y | Y | Y | LS 8 |
| Numbers | Y | Y | - | Y | Y | Y | Y | Y | LS 9 |
| Variables, prefixes, arrays, keys | Y | Y | Y | Y | Y | Y | Y | Y | VD |
| Scopes, `LOCAL`, `ARGS`, `RESULT` | Y | Y | Y | Y | Y | Y | Y | Y | VD 5-6 |
| Operators and priority | Y | Y | Y | Y | Y | Y | Y | Y | EO |
| `IF`/`ELSEIF`/`ELSE` | Y | Y | - | Y | Y | Y | Y | Y | CF 1 |
| `LOOP` | Y | Y | - | Y | Y | Y | Y (none used) | Y | CF 2 |
| Labels, `JUMP` | Y | Y | - | Y | Y | Y | Y | Y | CF 3 |
| `EXIT` | Y | Y | - | Y | Y | Y | Y | Y | CF 4 |
| `GOTO`, `XGOTO`, `GOSUB`, `FUNC`, `@` | Y | Y | Y | Y | Y | Y | Y | Y | CF 5, EM 3-4 |
| `DYNAMIC`, `DYNEVAL` | Y | Y | Y | Y | Y | Y | Y | Y | CF 6 |
| `ACT`, `DELACT`, actions | Y | Y | Y | Y | Y | Y | Y | Y | FC, EM 5 |
| Output statements | Y | Y | Y | Y | Y | Y | Y | Y | FC |
| Objects | Y | Y | Y | Y | Y | Y | Y | P | FC |
| `MSG`, `MENU`, `INPUT`, `WAIT` | Y | Y | Y | Y | Y | Y | Y | P | FC, EM 7 |
| Sound, `VIEW`, images | Y | Y | Y | P (player-dependent) | Y | Y | Y | P | FC, [IO](official-documentation/input-output-and-persistence.md) |
| Built-in functions | Y | Y | Y | Y | Y | Y | Y | P | [API](official-documentation/built-in-api-reference.md) |
| Regular expressions | Y | Y | Y | P | Y | Y | Y (rare) | P | API 1 |
| Random numbers | Y | Y | Y | Y | Y | Y | Y | P | API 2 |
| System variables and handlers | Y | Y | Y | Y | Y | Y | Y | Y | API 6, EM 2 |
| HTML and links | Y | Y | Y | P (player-dependent) | Y | - | Y | Y | IO 2 |
| Libraries (`INCLIB`/`ADDQST`) | Y | Y | Y | Y | Y | Y | Y | Y | IO 6 |
| Save and load | Y | Y | Y | Y | Y | Y | Y | Y | IO 7 |
| Game file formats | Y | Y | - | Y | Y | Y | Y | - | IO 6, tooling |
| Limits and error codes | - | Y | - | Y | Y | Y | - | - | [RT](engine-source-analysis/runtime-behavior.md) |
| `EXEC` (undocumented) | Y | P | P | P | Y | Y | Y (none used) | - | FC |

Abbreviations: LS language-syntax, VD variables-and-data-types, EO expressions-and-operators, CF control-flow, EM execution-model, FC functions-and-commands, IO input-output-and-persistence, API built-in-api-reference, RT runtime-behavior.

## 4. Girl Life (commit `83b164f`)

| Area | Status | Page |
|---|---|---|
| Size, history, target engine | Full | [project-overview.md](girl-life-analysis/project-overview.md) |
| Repository layout, manifest, file mapping | Full | [repository-structure.md](girl-life-analysis/repository-structure.md) |
| Scripting conventions (14 patterns) | Full | [scripting-patterns.md](girl-life-analysis/scripting-patterns.md) |
| Startup and event hooks | Full | [gameplay-systems.md](girl-life-analysis/gameplay-systems.md) 1-2 |
| Time, hourly and daily cycles | Targeted (structure and hook list) | gameplay-systems 3 |
| Stats, mood, willpower, traits | Survey (handler APIs) | gameplay-systems 4 |
| Money | Targeted | gameplay-systems 5 |
| NPCs and relationships | Survey | gameplay-systems 6 |
| School, grades, university | Targeted (what GLSS uses) | gameplay-systems 7 |
| Jobs v4, calendar | Survey (API lists) | gameplay-systems 8 |
| Clothing, homes, themes | Survey | gameplay-systems 8 |
| Mod framework | Full | gameplay-systems 10 |
| Saves and migrations | Full | [code-examples.md](girl-life-analysis/code-examples.md) 12, IO 7 |
| Debug panel | Targeted | gameplay-systems 2, [OBS](girl-life-analysis/implementation-observations.md) 11 |
| Build scripts, `qsp-cli`, CI | Full | [dependencies-and-configuration.md](girl-life-analysis/dependencies-and-configuration.md) |
| Validators (`callvalidator`, `qsp_audit`, Chimrod parser) | Targeted | dependencies-and-configuration 6 |
| Tests | Full | dependencies-and-configuration 8 |
| Sample mod and bundled mods | Targeted (sample), Survey (bundled) | dependencies-and-configuration 9 |
| Whole-codebase scans | Full | OBS, [scripts/](scripts/) |
| Quest and story content | Open | |
| C# analyzer, media tools, editors | Open | |

## 5. Deliverables from the brief

| Item | Status | File |
|---|---|---|
| README and navigation | Done | [README.md](README.md) |
| Scope and methodology | Done | [research-scope-and-methodology.md](research-scope-and-methodology.md) |
| Official documentation analysis (10 pages) | Done | [official-documentation/](official-documentation/documentation-index.md) |
| Engine source analysis (7 pages) | Done | [engine-source-analysis/](engine-source-analysis/repository-inventory.md) |
| Girl Life analysis (7 pages) | Done | [girl-life-analysis/](girl-life-analysis/project-overview.md) |
| Syntax and code reference | Done | [syntax-and-code-reference.md](syntax-and-code-reference.md) |
| Pitfalls and edge cases | Done | [common-pitfalls-and-edge-cases.md](common-pitfalls-and-edge-cases.md) |
| Verified findings with evidence levels | Done | [verified-findings.md](verified-findings.md) |
| Source index with pinned commits | Done | [source-index.md](source-index.md) |
| Coverage matrix | Done | this file |
| Fact and inference labeling | Done | evidence levels in verified-findings and OBS; "Inferred" marks elsewhere |
| Version differences | Done | version-differences, version tags in the syntax reference |
| Validation pass | Done | results in [README.md](README.md) |

## 6. Open items

| Item | Why open | How to close it |
|---|---|---|
| Behavior in running players | No binaries were run | Run the wasm test suite and small `.qsp` probes in the classic player |
| Engine versions 5.8.0 to 5.9.3 | No source tags | Find release archives of those versions |
| Contradiction C1 (` _` joining on 5.7) | Original 5.7.0 source not available | Test in a 5.7.0 player with `if t _` / `or t:` |
| GLSS university day in the full game (OBS 12) | Fixed and tested in a harness with real university locations and stand-ins for the rest; not yet played in the full game | Load a save of an enrolled student and use the one-click action before, between and after classes |
| 5.7 hash bucket overflow (OBS 5) | Inferred; depends on which names exist at once | Long 5.7 session with a variable count probe |
| Girl Life quest content | Outside the purpose of a language reference | Read per quest when GLSS needs it |
| wiki.qsp.org, VK articles | Outside the three named sources | Read if the docs leave a question open |

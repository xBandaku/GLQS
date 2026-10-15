# QSP technical reference

A reference on the QSP language and engine, Girl Life, and the GLQS mod. Start with [GLQS project overview](glqs-analysis/project-overview.md) for this repository, then use the shared language and engine pages below.

The shared library was carried over from the GLSS research dated 2026-10-14. Its official documentation, engine, Girl Life and GLSS findings retain their original pinned sources and examples. They were not independently reverified for this copy. GLSS examples and validation describe the GLSS repository at the time of that research; they do not establish GLQS behavior. GLQS-specific findings belong in [glqs-analysis/](glqs-analysis/project-overview.md).

Girl Life must run on QSP 5.7.0 and on 5.8 to 5.9.2 players, so most pages describe both behaviors side by side.

## Where to start

| If you want to | Read |
|---|---|
| Write or review GLQS code | [glqs-analysis/project-overview.md](glqs-analysis/project-overview.md), [syntax-and-code-reference.md](syntax-and-code-reference.md), [common-pitfalls-and-edge-cases.md](common-pitfalls-and-edge-cases.md) |
| Build GLQS or check its integration | [glqs-analysis/build-and-validation.md](glqs-analysis/build-and-validation.md), [glqs-analysis/gameplay-integration.md](glqs-analysis/gameplay-integration.md), [glqs-analysis/implementation-observations.md](glqs-analysis/implementation-observations.md) |
| Understand a QSP statement or function exactly | [official-documentation/](official-documentation/documentation-index.md) pages, then the engine pages they link |
| Know what differs between 5.7 and newer engines | [engine-source-analysis/version-differences.md](engine-source-analysis/version-differences.md) |
| Check how strong a claim is | [verified-findings.md](verified-findings.md), [source-index.md](source-index.md) |
| See what was and was not covered | [coverage-matrix.md](coverage-matrix.md), [research-scope-and-methodology.md](research-scope-and-methodology.md) |

## Contents

**GLQS** ([glqs-analysis/](glqs-analysis/project-overview.md))

| File | Content |
|---|---|
| [project-overview.md](glqs-analysis/project-overview.md) | GLQS purpose, source layout and current implementation |
| [build-and-validation.md](glqs-analysis/build-and-validation.md) | GLQS build dependencies, commands and validation results |
| [gameplay-integration.md](glqs-analysis/gameplay-integration.md) | GLQS entry points and Girl Life dependencies |
| [implementation-observations.md](glqs-analysis/implementation-observations.md) | GLQS source observations and unresolved questions |

**Top level**

| File | Content |
|---|---|
| [research-scope-and-methodology.md](research-scope-and-methodology.md) | Sources, order of work, scan scripts, limitations |
| [source-index.md](source-index.md) | Pinned commits, URL patterns, key files, external links not followed |
| [syntax-and-code-reference.md](syntax-and-code-reference.md) | Compact language reference with version tags |
| [common-pitfalls-and-edge-cases.md](common-pitfalls-and-edge-cases.md) | 46 pitfalls grouped by area, with versions and fixes |
| [verified-findings.md](verified-findings.md) | Main claims with evidence levels; contradictions; what was not verified |
| [coverage-matrix.md](coverage-matrix.md) | Coverage of docs pages, repositories, language features and Girl Life areas |
| [scripts/](scripts/) | The inherited Python scans behind the Girl Life and GLSS figures |

**Official documentation** ([official-documentation/](official-documentation/documentation-index.md))

| File | Content |
|---|---|
| [documentation-index.md](official-documentation/documentation-index.md) | Site structure, every page and blog post, version coverage, Russian and English differences |
| [language-syntax.md](official-documentation/language-syntax.md) | Source text, statements, comments, strings, continuation, names, numbers, labels, blocks |
| [variables-and-data-types.md](official-documentation/variables-and-data-types.md) | Types, storage, prefixes, indexing, scopes, limits, `ARGS` and `RESULT` |
| [expressions-and-operators.md](official-documentation/expressions-and-operators.md) | Priority, evaluation order, every operator, truthiness, subexpressions |
| [control-flow.md](official-documentation/control-flow.md) | `IF`, `LOOP`, labels, `EXIT`, location transfers, `DYNAMIC`, actions as code |
| [functions-and-commands.md](official-documentation/functions-and-commands.md) | Every statement with arguments, behavior and Girl Life counts |
| [built-in-api-reference.md](official-documentation/built-in-api-reference.md) | Every function and system variable |
| [execution-model.md](official-documentation/execution-model.md) | Events, the `GOTO` sequence, calls, actions, timer, dialogs |
| [input-output-and-persistence.md](official-documentation/input-output-and-persistence.md) | Windows, HTML, input, sound, file formats, libraries, saves |
| [tooling-and-development.md](official-documentation/tooling-and-development.md) | Text formats per tool, compilers, players, editors, validators |

**Engine source** ([engine-source-analysis/](engine-source-analysis/repository-inventory.md))

| File | Content |
|---|---|
| [repository-inventory.md](engine-source-analysis/repository-inventory.md) | All 21 QSPFoundation repositories and how deeply each was read |
| [architecture.md](engine-source-analysis/architecture.md) | QSPLib modules, data structures, pipeline, callbacks, legacy differences |
| [implementation-details.md](engine-source-analysis/implementation-details.md) | Preprocessing, expression compiler, variables, locations, regex, random, saves |
| [runtime-behavior.md](engine-source-analysis/runtime-behavior.md) | Limits, error codes per version, how execution stops, timing |
| [version-differences.md](engine-source-analysis/version-differences.md) | 5.7 to 5.8+ breaking changes, later additions, unreleased master changes |
| [tests-and-examples.md](engine-source-analysis/tests-and-examples.md) | Test suites as evidence, docs examples that fail, sample games |
| [documentation-cross-reference.md](engine-source-analysis/documentation-cross-reference.md) | Docs claims marked confirmed, differs, version-specific, undocumented |

**Girl Life** ([girl-life-analysis/](girl-life-analysis/project-overview.md))

| File | Content |
|---|---|
| [project-overview.md](girl-life-analysis/project-overview.md) | Size, history, target engine, run-time organization |
| [repository-structure.md](girl-life-analysis/repository-structure.md) | Layout, file mapping, build manifest, unregistered files, location families |
| [scripting-patterns.md](girl-life-analysis/scripting-patterns.md) | 14 conventions that let the code run on 5.7 and 5.8+ |
| [gameplay-systems.md](girl-life-analysis/gameplay-systems.md) | Startup, hooks, time, stats, money, NPCs, school, jobs, mods; what GLSS relies on |
| [code-examples.md](girl-life-analysis/code-examples.md) | 14 annotated excerpts, including one from GLSS |
| [dependencies-and-configuration.md](girl-life-analysis/dependencies-and-configuration.md) | Build paths, merge scripts, `qsp-cli`, CI, validators, tests, mods, GLSS build |
| [implementation-observations.md](girl-life-analysis/implementation-observations.md) | Scan results and risks in Girl Life and GLSS |

## Inherited findings from GLSS research

These findings are retained as historical context. Their GLSS results have not been applied to GLQS.

1. **Two engines in one codebase.** QSP 5.7 and 5.8+ differ in array storage (two values per element versus one), the value of true (-1 versus 1), `AND`/`OR` (bitwise versus logical), evaluation (eager versus short-circuit `IIF`), operator priorities, and argument order of three functions. Girl Life avoids every 5.8+ feature and branches on `$qspver` where statement names differ.
2. **Comments are parsed.** Quotes are tracked inside comments on every engine, so one apostrophe can turn the following code into a comment. In Girl Life, 13 comment blocks end where intended only because their stray apostrophes happen to pair up.
3. **The documentation mixes versions.** Some examples and error numbers come from 5.7, `OBJ` is described as returning 1 or 0 although 5.9.4 and 5.9.5 return a count, and several engine features (`EXEC`, `MENU` ranges, the `#` prefix) are undocumented.
4. **The engine master branch is moving.** Unreleased 5.9.6 changes the type rules for unprefixed names, the delimiter set, `KILLVAR`, `OBJ`, and refuses older saves. Girl Life's start screen refuses it, but the bundled Qqsp source would build it.
5. **5.7 capacity margin.** Under the 5.7 variable hash, one bucket would receive 55 of Girl Life's names against a limit of 50. This is a margin, not an observed failure.
6. **Version checks compare strings.** `qspver > '5.9.2'` and `$qspver < '5.8.0'` would misjudge a two-digit version such as 5.10.
7. **Build tooling.** Girl Life compiles with its own C++ `qsp-cli`, which differs from QSPFoundation's JavaScript `qsp-cli` and recognizes only `--- name ---` end markers. Its CI dev build passes an extra input file to it, and `build.sh` no longer works the way this repository's `CLAUDE.md` describes.
8. **GLSS holds up.** The Girl Life behaviors GLSS depends on all hold at the pinned commit. GLSS has no comment, 5.7 parsing, or type-mixing hazards.
   - **Exception, now fixed.** The one-click university day matched `Go to your room`, credited periods that had already started, and skipped lecture time on the clock. GLSS 0.2 fix 1 corrects this; the fix was tested in the QSP wasm engine ([implementation-observations.md](girl-life-analysis/implementation-observations.md), section 12).
9. **GLSS build.** `glss/Make_mod.bat` depends on a git-ignored `reference/nightly/` checkout that was not present.

## Conventions

- **Source references.** `engine: qsp/variables.c:373` means a file and line in the engine at the pinned master commit. Other prefixes are `engine-5.9.5:`, `legacy:`, `qspgui:` and `girl-life:`. A bare `name.qsrc:12` is a Girl Life location unless the text names GLSS. URL patterns are in [source-index.md](source-index.md).
- **Version tags.** `[all]`, `[5.7]`, `[5.8+]`, `[5.9.x+]` and `[master]` mark which engines a statement applies to ([syntax-and-code-reference.md](syntax-and-code-reference.md)).
- **Evidence labels.** "Fact" or no label means read in source. "Inferred" means derived from source and engine rules but not run. [verified-findings.md](verified-findings.md) gives the level for each main claim.
- **Code fences.** Code fences use the `qsp` tag, as the QSP docs do; most Markdown viewers show them as plain text.

## Initial GLQS validation on 2026-10-14

All 20 existing Python tests passed with no skips and the pinned Girl Life reference present. The full build passed validation/lints and produced `build/GLQS.qsp` using a local ignored installation of `@qsp/cli@1.0.5`. The final research tree's relative link destinations and file-line bounds were checked locally. No QSP player, saved-game round trip, gameplay smoke test or fresh CI run was performed. See [build-and-validation.md](glqs-analysis/build-and-validation.md) for commands, environment and check limits.

The follow-up GLQS 0.39.1 review fixed relationship counters, incomplete pain clearing and a block-lint gap. It passed 25 local tests, including four QSP 5.9.5 engine tests, and compiled successfully. See [the applied fixes and runtime limits](glqs-analysis/implementation-observations.md#follow-up-fixes-in-glqs-0391).

## GLQS 0.40.0 validation

The later GLQS 0.40.0 feature pass added value editors, favorites, portable presets, ownership filters and category restocking. All 37 local tests passed, including the expanded QSP 5.9.5 engine suite; see [the feature checks](glqs-analysis/implementation-observations.md#features-added-in-glqs-0400). Full-game saves and QSP 5.7 have not been exercised.

## Inherited validation from GLSS research

For GLQS build checks and their limits, see [glqs-analysis/build-and-validation.md](glqs-analysis/build-and-validation.md).

The original GLSS library records the checks below on 2026-10-14 after its last edit. This table is inherited evidence, not a record of checks run in GLQS.

| Check | Result |
|---|---|
| Relative links and anchors in all pages | All resolve |
| `file:line` references (427 in the pages, plus two format examples in this README) | Every referenced file exists in the pinned clones or in this repository; no line number is past the end of its file. A random sample of 25 was read and each points at the code described |
| Scan figures | Rerun from [scripts/](scripts/); outputs match the figures in the pages |
| Placeholder text (`TODO`, `TBD`, `FIXME`, `XXX`) | None |
| Em dashes and banned words | Two hits, both inside verbatim quotations from the QSP docs (a code comment and the F# parser description), left as quoted |
| Repository changes | `git status` shows only the new `research/` folder; no GLSS or Girl Life file was modified |

No player, compiler or test suite was executed for the research itself. See [research-scope-and-methodology.md](research-scope-and-methodology.md) for the limits that follow from that. The later GLSS fix was checked by running Girl Life's `qsp-cli`, the Chimrod parser, `callvalidator.py` and the QSP wasm engine; those runs cover GLSS only.

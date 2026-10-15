# Verified findings

These findings were carried over from the GLSS research dated 2026-10-14 without independent reverification. Evidence levels and recorded test results retain their original meaning and scope. GLSS findings and tests do not validate GLQS; see [glqs-analysis/](glqs-analysis/project-overview.md) for GLQS-specific findings.

The main claims of this reference with the strength of their evidence, followed by contradictions that could not be resolved and claims that were not verified. Commits are listed in [source-index.md](source-index.md).

## Evidence levels

| Level | Meaning |
|---|---|
| **Source** | Read in the source code at the pinned commit, with file and line given in the linked page |
| **Test (read)** | Asserted by a test in the wasm or legacy test suites. The tests were read, not run |
| **Scan** | Produced by a script over the Girl Life or GLSS sources; the scripts are described in [research-scope-and-methodology.md](research-scope-and-methodology.md) |
| **Docs** | Stated by dev.qsp.org or its blog, not checked further |
| **Inferred** | Follows from verified facts; not reproduced in a running player |

No player, compiler or test suite was executed during this research. The GLSS fix made afterwards was run in the QSP wasm engine; S3 below records that.

## 1. Engine behavior

| # | Finding | Level | Page |
|---|---|---|---|
| E1 | 5.7 stores a number and a string in every array element; 5.8+ stores one value | Source, Test (read) | [VD](official-documentation/variables-and-data-types.md) |
| E2 | Comparisons return -1 on 5.7 and 1 on 5.8+; `AND`/`OR`/`NO` are bitwise on 5.7 | Source | [EO](official-documentation/expressions-and-operators.md) |
| E3 | 5.8+ short-circuits `AND`/`OR` and evaluates only one `IIF` branch; 5.7 evaluates everything | Source | [EO](official-documentation/expressions-and-operators.md) |
| E4 | Operator priorities for 5.7 and 5.8+ (`&` lowest on 5.7; `OBJ`/`LOC` below comparisons on 5.7) | Source | [EO](official-documentation/expressions-and-operators.md) |
| E5 | Quotes are tracked inside comments, so an unpaired apostrophe in a comment continues it onto later lines, on 5.7 and 5.8+ | Source | [LS](official-documentation/language-syntax.md) |
| E6 | On 5.7 a comment after a multi-line header colon makes the header single-line, and inline `ELSEIF` is not recognized | Test (read): `qsp-legacy` `conditionals.qspt`, `acts.qspt` | [VER](engine-source-analysis/version-differences.md) |
| E7 | `GOTO` and any runtime error stop all code in the current event through one location-state counter | Source | [RT](engine-source-analysis/runtime-behavior.md) |
| E8 | `$ONNEWLOC` runs after the destination's code, with the `GOTO` arguments, and not after `GOSUB`/`FUNC` | Source | [EM](official-documentation/execution-model.md) |
| E9 | Limits: 50 actions, 1,000 objects, 100 menu items, 100 included files; 9 call arguments on 5.7 and 19 on 5.8+; call depth 2,000 on 5.9.5 and master, none on 5.7 | Source | [RT](engine-source-analysis/runtime-behavior.md) |
| E10 | Error codes were renumbered twice (5.7: 100-125, 5.9.4: 10-35, 5.9.5: 10-34) | Source | [RT](engine-source-analysis/runtime-behavior.md) |
| E11 | Variable tables: 5.7 has 256 buckets of 50 with an 8-bit Pearson hash; 5.9.5 has 512 chained buckets of at most 32; master uses open addressing with 100,000 globals | Source | [VD](official-documentation/variables-and-data-types.md) |
| E12 | On 5.7 `KILLVAR 'name'` leaves the name in its slot | Source | [VD](official-documentation/variables-and-data-types.md) |
| E13 | `$CURACTS` returns action bodies upper-cased on 5.8+ and names in their original case | Source (`engine: qsp/actions.c:117-155`) | [API](official-documentation/built-in-api-reference.md) |
| E14 | `QSPVER` and `$QSPVER` are the same text function on 5.7 | Source (`legacy: src/mathops.c:264-265`) | [code-examples.md](girl-life-analysis/code-examples.md) |
| E15 | `OBJ` returns -1 (5.7), 1 (5.8.0 to 5.9.3), the count (5.9.4, 5.9.5), and 1 again with `COUNTOBJ(name)` for counts (master) | Source for 5.7, 5.9.4, 5.9.5 and master; Docs (blog) for 5.8.0 to 5.9.3 | [API](official-documentation/built-in-api-reference.md) |
| E16 | Saves keep action code and loading does not re-run the location | Source | [IO](official-documentation/input-output-and-persistence.md) |
| E17 | master (unreleased 5.9.6) changes: universal unprefixed type, `?` literal, new delimiters, `KILLVAR` clears only globals, unary `+`, minimum save version 5.9.6 | Source (commits listed) | [VER](engine-source-analysis/version-differences.md) |
| E18 | `EXEC`, `MENU` start and count arguments, `DELOBJ` count and the `#` prefix exist in the engine but not in the docs' keyword pages | Source | [DCR](engine-source-analysis/documentation-cross-reference.md) |

## 2. Girl Life

| # | Finding | Level | Page |
|---|---|---|---|
| G1 | 35,516 commits since 2015-03-07; 1,429 top-level `.qsrc` files; 1,398 manifest entries; 916,144 lines including templates and unused files | Scan (`git`, file counts) | [project-overview.md](girl-life-analysis/project-overview.md) |
| G2 | Targets 5.7.0 to 5.9.2: start screen rejects `qspver > '5.9.2'`; bundled `qsp.dll` files contain `5.7.0` | Source; string scan of binaries | [project-overview.md](girl-life-analysis/project-overview.md) |
| G3 | Uses no 5.8+ syntax: zero `LOOP`, `LOCAL`, `@`, tuples, `SETVAR`, `ARRITEM`, one-argument `RAND`, three-argument `INSTR` | Scan | [VER](engine-source-analysis/version-differences.md) |
| G4 | 16,929 `$ARGS[0]` string handlers in 1,105 files; 113 default handlers | Scan | [scripting-patterns.md](girl-life-analysis/scripting-patterns.md) |
| G5 | 31 unregistered files; 8 header/file-name case mismatches | Scan | [repository-structure.md](girl-life-analysis/repository-structure.md) |
| G6 | 461 multi-line comments, all ending where intended; 13 of them only because stray quotes pair up | Scan (engine line-joining model) | [OBS](girl-life-analysis/implementation-observations.md) |
| G7 | Zero 5.7 parsing hazards (comment after header colon, inline `ELSEIF`) in Girl Life and GLSS | Scan, self-tested on planted cases | [OBS](girl-life-analysis/implementation-observations.md) |
| G8 | 8,489 names assigned by literal name; the fullest 5.7 hash bucket would hold 55 (limit 50), the fullest 5.9.5 bucket 28 (limit 32) | Scan | [OBS](girl-life-analysis/implementation-observations.md) |
| G9 | Overflow of that 5.7 bucket in play | Inferred, not observed | [OBS](girl-life-analysis/implementation-observations.md) |
| G10 | 44 (name, index) pairs written both as string and number, grouped in the observations page | Scan; two cases traced by hand | [OBS](girl-life-analysis/implementation-observations.md) |
| G11 | 56 `iif` with `func` and 42 with `rand` in a branch; 111 `iif(c, 1, 0)`; 164 `result = (...)` | Scan | [OBS](girl-life-analysis/implementation-observations.md) |
| G12 | `shortgs` `dow` tests `doy` variables (`shortgs.qsrc:125`) | Source | [OBS](girl-life-analysis/implementation-observations.md) |
| G13 | CI dev build passes a second input file to `qsp-cli` | Source (`ci_build.py`, `qsp-cli.cpp`); effect Inferred | [DEP](girl-life-analysis/dependencies-and-configuration.md) |
| G14 | `build.sh` compiles with `qsp-cli --compile`, not `txtmerge.py` plus `txt2gam` as this repository's `CLAUDE.md` said; the note has since been corrected | Source | [DEP](girl-life-analysis/dependencies-and-configuration.md) |
| G15 | Qqsp source fetches the engine without a tag; engine CMake fetches Oniguruma `master` | Source | [OBS](girl-life-analysis/implementation-observations.md) |

## 3. GLSS

| # | Finding | Level | Page |
|---|---|---|---|
| S1 | GLSS relies on `$ONNEWLOC` ordering, exact action names, and `money` `can_afford` returning 1/0; all hold in Girl Life at `83b164f` | Source | [gameplay-systems.md](girl-life-analysis/gameplay-systems.md) |
| S2 | The `$CURACTS` name search works on 5.7 and 5.8+ | Source (E13) | [code-examples.md](girl-life-analysis/code-examples.md) |
| S3 | GLSS 0.2's one-click university day matched `Go to your room`, credited periods that had already started, and skipped lecture time on the clock; fixed in 0.2 fix 1 | Run: 12 scenarios in the QSP wasm engine showed each bug in 0.2 and none in the fix | [OBS](girl-life-analysis/implementation-observations.md) |
| S4 | No comment-swallowing, no 5.7 parsing hazards, no dual-type variables | Scan | [OBS](girl-life-analysis/implementation-observations.md) |
| S5 | `glss/Make_mod.bat` needs `reference/nightly/tools/qsp-cli.exe`, which is git-ignored and was absent | Source, file system check | [DEP](girl-life-analysis/dependencies-and-configuration.md) |

## 4. Contradictions

| # | Question | Evidence on each side | Status |
|---|---|---|---|
| C1 | Does 5.7 keep the space when joining a line that ends in ` _`? | The 2026-01-01 blog says 5.7 joins the pieces without a space (its example becomes `if tort:`) and advises two spaces before `_`. `qsp-legacy` `src/codetools.c:184-199` overwrites only the `_` and keeps the space, both at HEAD `3e725e1` and in the fork's first commit `ef433fc`. | Unresolved. The fork may differ from the original 5.7.0 library, whose source was not available. Girl Life and GLSS are not affected: neither has a line ending in ` _` |
| C2 | How many arguments do `GOSUB`/`GOTO` take? | The statements page shows `[argument 8]` in some syntax lines and `[argument 18]` in others; the source allows 19 on 5.8+ and 9 on 5.7 | Resolved by source: the page mixes 5.7 and 5.8 text |
| C3 | What does reading `%x` from a numeric variable return? | English docs: "empty strings or zeros"; Russian docs: "empty tuple"; source returns an empty tuple | Resolved by source; English wording imprecise |
| C4 | What does `OBJ` return? | Docs: 1 or 0. Source: count on 5.9.4 and 5.9.5 | Resolved by source (E15) |
| C5 | Can `$DESC` return text for games written in a text editor? | Docs: no. TXT2GAM's `! BASE` section and Girl Life's `qsp-cli` base-section heuristics can create base descriptions | Resolved by source; docs describe `@qsp/converters` only |
| C6 | Does `qsp_audit` model `ELSEIF` as 5.8-only? | Its version enum comment says 5.8.0 "Added ... ELSEIF"; 5.7 supports multi-line `ELSEIF` and lacks only the inline form | Comment too broad; the rule logic was not traced |

The C1 check used `grep -rn " _\s*$"` over Girl Life's `locations/` and `glss/locations/`: 0 matching lines in each, including inside strings and comments.

## 5. Figures that changed during the research

Several Girl Life figures were first produced by one-off commands and later recomputed by saved scripts with slightly different extraction rules. The pages now use the recomputed values:

| Figure | First run | Final |
|---|---|---|
| Distinct names assigned by literal name | 8,391 | 8,489 |
| Names with literal string keys | 712 (key form not separated) | 695 literal, 400 from a string variable |
| Fullest 5.7 bucket | 53 | 55 |
| Dual-type pairs | 30 | 44 (includes 9 `ARGS`/`RESULT` elements) |
| `iif` with `func` in a branch | 71 | 56 (outside strings only) |
| `iif(c, 1, 0)` | 113 | 111 |
| Multi-line comments | 457 deliberate | 461, of which 13 continue on an open quote |

The conclusions did not change: the 5.7 bucket is over its limit in both runs, and every multi-line comment ends where intended.

## 6. Not verified

- Behavior of the bundled players and of any compiled binary. Nothing was run.
- Player-side behavior: HTML support, sound mixing, refresh rates, qSpider details (marked "Unverified" in [DCR](engine-source-analysis/documentation-cross-reference.md)).
- Engine versions 5.8.0 to 5.9.3, which have no source tags in the repository. Statements about them rest on the docs and blog.
- The original 5.7.0 library binary, as opposed to the `qsp-legacy` fork (see C1).
- The Girl Life C# analyzer (`tools/qsp-analyser/`), media checkers, and QGen editors.
- The F#, Python and Qt tools in QSPFoundation were surveyed for purpose only ([repository-inventory.md](engine-source-analysis/repository-inventory.md)).
- Girl Life's GitLab wiki and Discord-hosted material.

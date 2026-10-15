# Research scope and methodology

This page was carried over from the GLSS research dated 2026-10-14 without independent reverification. Its references to "this repository", GLSS checks and validation describe the original GLSS research. See [glqs-analysis/](glqs-analysis/project-overview.md) for GLQS-specific work.

What was examined for this reference, in what order, how the figures were produced, and what was left out.

## 1. Scope

The research followed the order the brief set:

1. **QSP documentation.** dev.qsp.org, starting at https://dev.qsp.org/docs/intro/, including its blog.
2. **QSP engine and tools.** The QSPFoundation GitHub organization: the engine (QSPLib), the 5.7 legacy fork, players, converters, compilers, language servers, test suites and samples.
3. **Girl Life.** https://gitlab.com/kevinsmartstfg/girl-life, the game that the GLSS mod in this repository extends.

The GLSS sources in `glss/` were checked against the findings where they depend on Girl Life or on engine behavior. No GLSS or Girl Life file was modified.

## 2. Sources and versions

All repositories were cloned on 2026-10-14 into a temporary working folder outside this repository and read at the commits pinned in [source-index.md](source-index.md). The main ones:

| Source | Commit | Why this version |
|---|---|---|
| Docs site source | `8dc098f` (2026-05-13) | Site source selected for the 2026-10-14 snapshot |
| Engine `master` | `00faed4` (2026-10-13) | Master pin in that snapshot, unreleased 5.9.6 |
| Engine tag `5.9.5` | `0445921` | Release selected for that snapshot |
| Engine tag `5.9.4` | `8ebe46a` | Previous release, for error codes and `OBJ` |
| `qsp-legacy` | `3e725e1` (2026-10-09) | The maintained 5.7.0 code and its tests, the closest available source for the engine Girl Life bundles |
| Girl Life `master` | `83b164f` (2026-10-09) | Master pin in that snapshot |

This repository's `CLAUDE.md` refers to a Girl Life checkout at `reference/nightly/`. That folder is git-ignored and was not present on disk, so Girl Life was cloned fresh. Its commit is the one above.

## 3. Method

**Documentation.**
- Every page under the English locale was read in full, together with the five blog posts (list in [documentation-index.md](official-documentation/documentation-index.md)).
- Russian originals were compared where the English text was unclear.
- The live intro page was fetched once to confirm the site serves the English files.
- Each claim was then looked up in the engine source and classified in [documentation-cross-reference.md](engine-source-analysis/documentation-cross-reference.md).

**Engine and tools.**
- The C sources of the engine were read module by module. 5.9.5 and 5.9.4 were read through `git show <tag>:<path>` and `git diff`; the 41 commits after 5.9.5 through `git log`.
- The legacy 5.7 source and its `.qspt` tests were read for every 5.7 statement in this reference.
- The wasm engine's TypeScript tests were read as behavior specifications.
- Other repositories were read to the depth listed in [repository-inventory.md](engine-source-analysis/repository-inventory.md).
- Line references point at the pinned commits.

**Girl Life.**
- Core locations were read directly: `start`, `LOCA`, `mod_system`, `time`, `money`, `shortgs`, `array`, `core_library`, `gschool_lessons`, `uni_*`, `saveupdater` and others named in the pages.
- Build scripts, CI configuration and `qsp-cli.cpp` were read in full where cited.
- Counts and pattern checks over all 1,429 locations come from the scripts below.

**Verification during writing.**
- Each new page was checked against the source after it was written; corrections found that way were applied to every page that cited the same fact.
- Figures from early one-off commands were recomputed with saved scripts before publication ([verified-findings.md](verified-findings.md), section 5).

## 4. Scripts

The scripts are in [scripts/](scripts/). They need Python 3.8 or later and no packages. Each takes a `locations` folder as its first argument and reads only the `.qsrc` files directly inside it, except `keyword_stats.py`, which also walks `templates/` and `unused/`.

| Script | What it produces | Used for |
|---|---|---|
| `qspprep.py` | Model of the engine's line joining: quotes before braces, then `{}`, `()` and `[]` (5.9.x), or quotes and `{}` only (5.7, `legacy=True`). Module used by the others | Comment analysis |
| `comment_spans.py` | Comments whose logical line covers non-comment lines, classed by whether the comment starts with a quote or brace. The single "accidental" hit (`mirror.qsrc:595`) was checked by hand and is commented-out code | 458 spans, [OBS](girl-life-analysis/implementation-observations.md) 2 |
| `open_quote_comments.py` | Multi-line comments that continue past a line end because a quote is open there | 461 and 13, OBS 2 |
| `legacy_hazards.py` | Multi-line headers followed by a comment, and inline `ELSEIF`, under 5.7 line joining | 0 and 0; `selftest/t.qsrc` plants three cases and all three are reported |
| `count_handlers.py` | `$ARGS[0]` string handlers, default handlers, numeric `ARGS[0]` branches | 16,929 / 113 / 6,874 |
| `list_handlers.py` | Handler names with line numbers for named locations | Line references in [gameplay-systems.md](girl-life-analysis/gameplay-systems.md) |
| `qsrc_mask.py` | Marks characters inside strings, `{}` blocks and comments. Module | Used by the next two |
| `variable_names.py` | Names assigned by literal name, key forms, hash bucket load under the 5.7 and 5.9.5 hashes, and elements written as both string and number. The second argument is `qsp-legacy`'s `src/variables.c`, from which it reads the 5.7 hash table | 8,489 names, buckets 55 and 28, 44 pairs |
| `iif_scan.py` | `iif` calls with `func` or `rand` in a branch, `iif(c, 1, 0)` and `result = (...)` counts | 56 / 42 / 111 / 164 |
| `keyword_stats.py` | Statement, function and system-variable counts after removing strings and comments, plus counts of `<<`, `<img`, `exec:` and `<a href` in raw text | Usage columns in the statement and function pages |

**Limits of the scans.**
- They are pattern matchers built on the engine's rules, not a QSP parser.
- They do not see names or code built at run time through `dynamic`, `<<...>>` or computed location names.
- `iif` calls inside `<<...>>` in text are not counted by `iif_scan.py`.
- `keyword_stats.py` counts statements at statement starts. Its numbers can differ by a few from counts that include `templates/` and `unused/` or that use other boundaries; for example `*clr` is 28,110 in its output and 28,111 in the statements page.

Example runs from this folder, with `<clones>` standing for wherever the repositories were cloned:

```text
python scripts/variable_names.py <clones>/girl-life/locations <clones>/qsp-legacy/src/variables.c
python scripts/legacy_hazards.py scripts/selftest
python scripts/open_quote_comments.py ../../glss/locations
```

## 5. Tools and access

- Repositories were cloned with `git` over HTTPS. All requested sources were reachable; nothing required credentials.
- Binary files (players, `qsp.dll`, `qsp-cli.exe`, `txt2gam.exe`) were not executed. The version strings in [project-overview.md](girl-life-analysis/project-overview.md) come from scanning the files for text.
- No test suite was run. Test files were read as specifications.

## 6. Limitations

- **No execution.** Every runtime claim rests on source reading. Claims that combine several facts are marked "Inferred".
- **Missing versions.** Engine versions 5.8.0 to 5.9.3 have no source tags. Statements about them come from the docs and blog.
- **Fork, not original.** The 5.7 source is the `qsp-legacy` fork started in 2025, not the original 5.7.0 release; one contradiction with the blog depends on this ([verified-findings.md](verified-findings.md), C1).
- **Survey-depth repositories.** The F# parser, the Qt editor, the Python test engine and the Sublime package were reviewed for purpose and relevant details only.
- **Not reviewed in Girl Life.** The C# analyzer, media check scripts, QGen editors and image tools.
- **Outside the brief.** wiki.qsp.org, the VK articles and other external links found inside the sources were not read ([source-index.md](source-index.md)).
- **Gameplay depth.** Gameplay systems were analyzed at the level of their QSP structure and the parts GLSS depends on; quest content was not reviewed.

Coverage per item is tracked in [coverage-matrix.md](coverage-matrix.md).

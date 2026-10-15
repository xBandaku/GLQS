# Engine version differences

What changed between QSP 5.7.0 and the current engine. Girl Life must run on 5.7.0 and refuses to start on players newer than 5.9.2, so this table decides which language features it can use. The evidence column says where each row was verified:
- **src** means the engine or legacy source;
- **test** means the wasm test suite;
- **blog** means the 2026-01-01 migration post;
- **docs** means the keyword pages.

Versions between 5.8.0 and 5.9.3 were not available as source tags in the repository (only 5.9.4 and 5.9.5 are tagged), so rows for them rest on the docs and blog.

## 1. Breaking changes from 5.7 to 5.8+

| Topic | 5.7 | 5.8 and later | Evidence |
|---|---|---|---|
| Array element storage | number and string side by side in each element | one value per element; the last write wins | src (`legacy: src/variables.h:28-32`; `engine: bindings/qsp.h:150`), test, blog |
| True value of comparisons and logic | -1 | 1 | src (`legacy: src/mathops.c:489-524`), blog |
| `AND`, `OR`, `NO` | bitwise | logical | src, blog |
| Short-circuit `AND`/`OR`, lazy `IIF` | no, all operands evaluated | yes (confirmed in 5.9.5 and master) | src (`legacy: src/mathops.c:394`; `engine-5.9.5: qsp/mathops.c:987-1031`) |
| Priority of `OBJ`, `LOC` | 8, below comparisons | 11, above comparisons | src, test, blog |
| Priority of `&` | 4, lowest | 12, between comparisons and `+` | src |
| Optional argument of `INSTR`, `ARRPOS`, `ARRCOMP` | first: `instr(start, s, sub)` | last: `instr(s, sub, start)` | src, docs, blog |
| `RAND(n)` | 0 to n | 1 to n | src (`legacy: src/mathops.c:1041-1051`), docs, blog |
| Implicit statement with a function that returns nothing | prints an empty line | prints nothing | blog, test |
| `DISABLESUBEX` | turns off `<<...>>` | ignored | docs, blog |
| Library statements | `ADDQST`, `KILLQST` | `INCLIB`, `FREELIB` | src (legacy registers only the old names) |
| IF condition types | number only; text condition is a type mismatch unless numeric | numbers, strings (non-empty is true), tuples | src (`legacy: src/statements.c:126`; `engine: qsp/variant.c:170`), blog |
| Location call arguments | up to 9 | up to 19 | src, blog |
| Line continuation ` _` | blog says the pieces join without a space; the legacy source keeps the space | joined with a space | contradiction, see [verified-findings.md](../verified-findings.md) |
| Line joining inside `(` and `[` | no | yes (present in 5.9.4 and 5.9.5) | src, blog |
| Inline `ELSEIF` in a single-line IF | not recognized; the line fails with "Unknown action!" or skips the `elseif` part | supported | legacy tests (`conditionals.qspt:50-93`), test |
| Comment after the colon of a multi-line `if`/`elseif`/`else`/`act` | turns the header into a single-line statement | allowed | legacy tests (`conditionals.qspt:605-680`, `acts.qspt:133`), blog |
| `MENU` separators `-:-` | ordinary items named `-` | separators | legacy tests (`menu.qspt:43`) |
| Action code storage | kept as written | upper-cased outside strings (visible in `$CURACTS`) | legacy tests (`acts.qspt:75`), src |
| `$QSPVER` | no argument; library version | optional argument; player-supplied text | legacy tests (`base-functions.qspt:4-12`), src |
| UI refresh before `MSG`, `INPUT`, `EXEC` | no | yes | legacy tests |
| `RESULT` isolation | only around `FUNC`/`DYNEVAL` | every call scope | src (`legacy: src/mathops.c:1131`), docs |
| Call depth limit | none | 2,000 (5.9.5, master) | src |
| Error numbers | 100-125 | 10-35 (renumbered again in 5.9.5) | src, see [runtime-behavior.md](runtime-behavior.md) |
| Save files | 5.7 format | new format; 5.9.4+ only load saves from 5.9.4 or later | src (`CMakeLists.txt`, `QSP_GAMEMIN_VER`) |

## 2. Features added after 5.7

| Feature | Version | Evidence |
|---|---|---|
| `LOCAL`, `LOOP`, `@`/`@@` calls, `ARRITEM`, `INCLIB`/`FREELIB` names | 5.8.0 | docs index |
| Multiple assignment, swap, multi-dimensional indices `a[1,2]`, `KILLVAR` by string or tuple key, comments after the colon of multi-line headers, error messages with the line text | 5.8.0 or later (blog lists without versions) | blog, src |
| Tuples and the `%` prefix, `$CUROBJS`, `SCANSTR`, `SORTARR` | 5.9.0 | docs index |
| `ARRPACK`, `ARRTYPE`, `SETVAR`, `UNPACKARR` | 5.9.1 | docs index |
| `MODOBJ`, `RESETOBJ` | 5.9.4 | docs index |
| `RAND` mode argument, `REPLACE` count argument, `DELOBJ` count argument | 5.9.x (blog, no exact version) | blog, src |
| `MENU` start and count arguments | at least 5.9.5 | src only (not documented) |
| `#` number prefix | at least 5.9.4 | src only (not documented) |

## 3. 5.9.4 to 5.9.5

From `git log 5.9.4..5.9.5` and diffs:
- Error codes renumbered (`QSP_ERR_INTERNAL` added at 10, `LOCCALLDEPTH` and `COMPLEXEXPRESSION` introduced, `EQNOTFOUND` and the two bracket errors merged).
- Call depth limit introduced with a custom stack allocator.
- `ARRPOS` uses strict tuple comparison (`2a10f5f`).
- Parsing of `{}`, `[]` and `()` inside comments and code blocks fixed (`c9153da`, `a7a8dd8`, `bfa6d17`, `812b068`).
- Oniguruma is fetched at build time with `FetchContent`.
- `OBJ` returns the object count in both 5.9.4 and 5.9.5 (blog: "starting from 5.9.4").

## 4. Unreleased changes in master (after 5.9.5)

41 commits from 2026-10-01 to 2026-10-13, CMake version 5.9.6. These are not in any release and could still change.

| Change | Commit | Effect on existing games |
|---|---|---|
| Statements parsed and expressions compiled once; variables and locations in open-addressing hash tables; code blocks cached | `64a253d`, `7a55668` | Faster; variable limit raised to 100,000 globals |
| `KILLVAR` without arguments clears only globals | `24dd877` | Locals survive `killvar` |
| Delimiters `\ ; ^ @ ?` added | `64fe082`, `bc7e567`, `af77f90` | Names containing those characters become invalid |
| Spaces allowed after `@`/`@@` | `bc7e567` | |
| Tab before `_` continues a line | `ab7500e` | |
| Unprefixed names hold any type ("universal type prefix") | `d938a28` | `x = 'text'` no longer raises a type mismatch; `x` returns a string if it holds one. Code that relied on the type mismatch or on reading 0 from a string slot behaves differently |
| `?` undefined literal; undefined values not saved as empty strings | `af77f90` | |
| Minimum loadable save version 5.9.6 | `af77f90` | Saves from 5.9.5 and earlier cannot be loaded |
| `OBJ` returns 0/1 again; `COUNTOBJ(name)` returns the count | `00faed4` | Code written for 5.9.4/5.9.5 that used `obj` as a count breaks |
| Unary `+` accepted | `73d4527` | |

**Impact on Girl Life (inferred).** Girl Life's start screen rejects players whose `$qspver` compares greater than `'5.9.2'`, so it would refuse a master-based player anyway. Its bundled Qqsp source (`tools/Qqsp-Src/CMakeLists-qsp.txt.in`) fetches the engine's default branch without a tag. A Qqsp built today would contain the unreleased master and fail that guard.

## 5. What Girl Life can use

Girl Life targets the intersection of 5.7.0 and 5.8+ behavior, with explicit branches where the two differ:
- No `LOCAL`, `LOOP`, tuples, `@`, `SETVAR`, `ARRITEM`, `SORTARR`, `SCANSTR` (zero uses found).
- `INSTR`, `ARRPOS`, `ARRCOMP` only with two arguments; `RAND` only with two (zero three-argument `INSTR` and zero one-argument `RAND` found).
- Library statements chosen at run time: `if $qspver < '5.8.0': addqst ... else inclib ...` (`girl-life: locations/mod_system.qsrc:143-147`).
- Truth constants computed rather than hard-coded: `_TRUE = (0 ! 1)` (`girl-life: test/testframework.qsrc:5`). A comment in `outfit.qsrc` notes "QSP 5.7.0- (truth = -1); QSP 5.8.0+ (truth = +1)".
- No string truthiness: conditions on strings compare with `''` explicitly.
- No inline `elseif` in single-line IFs and no comments after the colon of multi-line headers (zero occurrences in a scan that reproduces the 5.7 line joining; see [implementation-observations.md](../girl-life-analysis/implementation-observations.md)).
- Version guard: `if qspver > '5.9.2':` shows "RUNTIME VERSION MISMATCH" and exits (`girl-life: locations/start.qsrc:12-18`). The comparison is lexicographic text comparison.

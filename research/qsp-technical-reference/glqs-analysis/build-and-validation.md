# GLQS passes static checks and artifact conversion

At the initial GLQS 0.39.0 research snapshot on 2026-10-14, all 20 existing Python tests passed with no skips and the pinned Girl Life reference present. The full build then passed its validators and lints and produced `build/GLQS.qsp` with `@qsp/cli@1.0.5`. No QSP player, saved-game round trip or gameplay smoke test was run during that initial pass. ([tests/test_build.py:21](../../../tests/test_build.py#L21), [build.py:42](../../../build.py#L42))

The subsequent GLQS 0.39.1 review passed all 25 tests without skips and compiled a 3,345-line build. The suite now includes four QSP 5.9.5 runtime tests for dating removal, status changes, marriage/divorce and pain clearing, plus a block-lint regression. The runtime tests use real upstream `lover`, `pain` and `math` locations with isolated rendering, NPC and phone services. They do not cover a full save or QSP 5.7. See [the applied fixes](implementation-observations.md#follow-up-fixes-in-glqs-0391).

Install the optional runtime dependencies locally with `npm install --prefix build/tooling @qsp/converters@1.0.1 @qsp/wasm-engine@1.6.1 --no-audit --no-fund`. The unittest command below then includes the engine tests. Without Node, these packages or the required upstream source, those tests report a skip. CI installs them and fetches the pinned upstream source before running the suite; this workflow change was inspected locally but has not run on GitHub here.

## Run tests before the compiler stage

GLQS 0.40.0 passed all 37 local tests without skips. This includes typed stat and quantity edits, category restocking, exact funds grants with overflow balances, ownership filtering and missing-only grants for all item types, favorites, selected preset application, schema checks, malformed and large imports, and isolated save/reload. The build now generates the compact-preset schema signature in addition to navigation and clothing actions. No full-game save or QSP 5.7 runtime session was tested.

Run from the repository root:

```powershell
python -m unittest discover -s tests -v
```

The suite now has 12 build-validation tests, nine lint tests and four optional engine tests. It checks the real source tree as well as selected malformed inputs, escaped route references and generated action counts. The local run used Python 3.12.10. CI specifies Python 3.13, which was read from the workflow but not newly exercised by this research. ([tests/test_build.py](../../../tests/test_build.py), [.github/workflows/build.yml:9](../../../.github/workflows/build.yml#L9))

The compiler was initially absent. A local installation was added under ignored `build/tooling/`; no tracked dependency manifest changed. To reproduce that setup in PowerShell:

```powershell
npm install --prefix build/tooling @qsp/cli@1.0.5 --no-audit --no-fund
$env:PATH = (Resolve-Path 'build/tooling/node_modules/.bin').Path + ';' + $env:PATH
python build.py
```

The successful run assembled 3,331 lines, printed `Checks passed.`, converted `GLQS.qsps` to `GLQS.qsp`, and exited successfully. The assembled text was 167,266 bytes and the binary 334,088 bytes in this Windows run. Byte counts depend on text line endings. CI installs the same compiler version globally and uploads the binary. ([build.py:69](../../../build.py#L69), [build.py:78](../../../build.py#L78), [.github/workflows/build.yml:28](../../../.github/workflows/build.yml#L28))

## The reference checkout enables extra checks

`reference/nightly/` is ignored and pinned in detached HEAD at `83b164f64224f1ba88fd409469c1a9379ad34f86`. Its name does not imply automatic updates or a verified match to an installed game. Upstream file links in these pages require that checkout. ([Pinned upstream source](https://gitlab.com/kevinsmartstfg/girl-life/-/tree/83b164f64224f1ba88fd409469c1a9379ad34f86), [.gitignore:2](../../../.gitignore#L2))

With `jobs_list.qsrc` present, validation compares all 28 GLQS job IDs to the upstream definition set. With `cheatmenu_din.qsrc` present, it checks that recurrent special-handler names exist. Neither check proves those handlers' complete effects. Without these files, validation keeps local row/ID checks but omits the upstream comparisons, and the dedicated reference-job test skips. CI now fetches the pinned reference in its test job, which also enables the runtime checks. The separate compile job still runs without the reference after tests pass. ([build_support.py:329](../../../build_support.py#L329), [build_support.py:390](../../../build_support.py#L390), [tests/test_build.py:145](../../../tests/test_build.py#L145), [.github/workflows/build.yml:1](../../../.github/workflows/build.yml#L1))

## Conversion does not execute QSP statements

Assembly expands 14 navigation actions, 18 store labels and 82 clothing category actions. Validators cover recognized routes, navigation agreement, recurrent rows/state displays, consumable metadata and job IDs. Eight lints cover comment apostrophes, non-ASCII text, template markers, generated marker bodies, numeric/string argument slots, versions and rough block balance. ASCII is a repository policy; this scan does not establish an engine-wide character-set restriction. ([build_support.py:260](../../../build_support.py#L260), [build_support.py:329](../../../build_support.py#L329), [build_support.py:422](../../../build_support.py#L422), [build_support.py:602](../../../build_support.py#L602))

The installed JavaScript `qsp-cli` reads text locations and writes a binary container. It does not execute the stored statement strings, and successful conversion does not establish complete QSP statement syntax or runtime correctness. The inherited GLSS research also discusses Girl Life's separate C++ compiler; GLQS uses the npm converter specified here. ([CLI conversion implementation](https://github.com/QSPFoundation/qsp-cli/blob/6b1749096384809c780a82d702e8d391e2ca7202/cli.js), [shared tooling reference](../official-documentation/tooling-and-development.md))

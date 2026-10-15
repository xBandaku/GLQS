# Working on GLQS

Write plain prose. Do not use em dashes or emoji in docs, commits, PRs or logs.
Use the `no-ai-slop` skill for longer writing. Change only the requested scope,
match the surrounding code, and make comments explain why rather than restate
the code. Run the relevant checks before saying a change works.

Read [CLAUDE.md](CLAUDE.md) for the source conventions and [the research index](research/qsp-technical-reference/README.md) for QSP, Girl Life and GLQS findings. The shared research came from GLSS on 2026-10-14; its GLSS examples and old validation do not validate GLQS.

Edit `src/*.qsps` for gameplay changes. `build/GLQS.qsps` and `build/GLQS.qsp` are generated. `STANDALONE_FILES` and `SHARED_FILES` in `build_support.py` control assembly order; add new fragments to the correct explicit manifest. Preserve the generation markers and use the existing table formats and `split_row` route.

Treat `reference/nightly/` as read-only upstream source. It is an ignored, detached checkout pinned to `83b164f64224f1ba88fd409469c1a9379ad34f86`, not an automatic latest checkout or a verified match for an installed game. Check it before using a base-game variable, array key, handler or hook. Never guess those names.

Run build-contract tests with:

```powershell
python -m unittest discover -s tests -v
```

Compile with `python build.py` after making `@qsp/cli@1.0.5` available as `qsp-cli`. The local ignored installation can be used in PowerShell with:

```powershell
$env:PATH = (Resolve-Path 'build/tooling/node_modules/.bin').Path + ';' + $env:PATH
python build.py
```

Keep the upstream reference present when checking jobs and recurrent handlers. Compilation and static tests do not replace in-game checks. Record which checks ran and their limits; do not claim runtime validation from a compile. Project-local `.claude/` automation is absent from this checkout.

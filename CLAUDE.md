# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

GLQS is a QSP (Quest Soft Player) mod for the game "Girl Life". It's a cheat/debug
menu (clothing, consumables, stats/attributes, school grades, money, relationships,
body mods, health) accessible from the bedroom in-game. Source is plain-text `.qsps`
fragments that get stitched into one `.qsps` file and compiled to a binary `.qsp`.

## Build

```
python3 build.py
```

Requires the QSP compiler once: `npm install -g @qsp/cli`

- Reads every `src/*.qsps` fragment, assembles `build/GLQS.qsps`, runs lint checks,
  then compiles with `qsp-cli` to `build/GLQS.qsp`.
- On `SUCCESS`, copy `build/GLQS.qsp` into the Girl Life `mod/` folder to test in-game.
- On `Lint checks FAILED`, the output names the exact file/line — fix the `src/`
  fragment and rerun. The assembled `.qsps` is still written even on failure, useful
  for inspection.
- There is no test suite; the lint checks in `build.py` and manual in-game testing
  are the only verification.

## Architecture: how src/*.qsps assemble into one location

Girl Life is a single QSP game file; this mod cannot add new `.qsp` locations to it
at runtime, so almost everything lives inside **one shared QSP location**,
`mod_GLQS_main`, built by concatenating fragment bodies and dispatching on
`$ARGS[0]`.

- `build.py` splits `src/*.qsps` into two groups:
  - **`STANDALONE_FILES`** (currently `01_setup.qsps`, `02_readme.qsps`,
    `03_hook.qsps`) — each already contains its own `# location_name` header and
    `--- location_name ---` footer, and is passed through unwrapped, in the order
    listed in `STANDALONE_FILES` (not filename order).
  - **Everything else** — treated as a body-only fragment of the shared
    `mod_GLQS_main` location (no `#`/`---` wrapper of its own). These are
    concatenated in **filename sort order** (hence the `NN_` numeric prefixes),
    and `build.py` wraps the whole batch in one `# mod_GLQS_main` /
    `--- mod_GLQS_main ---` pair automatically.
- Inside `mod_GLQS_main`, each fragment is an `if $ARGS[0] = 'submenu_name': ... end`
  block acting as a sub-router — e.g. `06_clothing.qsps` handles
  `'clothing_menu'` and `'store_buy'`, `15_actions.qsps` handles action verbs like
  `'consumables'`/`'stats'`, `16_fill_helpers.qsps` handles bulk-grant loops like
  `'fill_clo'`. Menus link to each other via
  `gt 'mod_GLQS_main', 'other_menu_name'`.
- `03_hook.qsps` is the entry point injected into the game's bedroom location
  (`$locclass = 'bedr'`) that renders the "Quick Setup" link into `mod_GLQS_main`.
- File numbering (`01`, `02`, `03`, `05`...`16`) controls both display order in the
  standalone list and concatenation order in the shared location — it's advisory
  (gaps are fine), just keep related menus grouped.

## Lint rules (enforced by build.py, not qsp-cli)

These exist because they caused real, hard-to-diagnose failures during development:

1. **No apostrophes inside `!!` comments.** QSP does not reliably ignore quotes in
   `!!` comments; a raw `'` opens an unterminated string that can corrupt parsing
   for the rest of the file, often surfacing as an unrelated "end not found" error
   elsewhere. Write "players" not "player's". Doubled `''` (QSP's string-escape) is
   fine.
2. **ASCII only**, including in comments. Smart quotes, em-dashes (`—`), etc. cause
   hard syntax errors. Use `-` and straight quotes.
3. **Balanced `if ...: / end` and `act 'x': / end` blocks.** This is a rough
   line-based depth counter, not a real parser — it doesn't fully understand
   single-line `if`/`act` or elseif chains, but catches missing/extra `end`s before
   an in-game repro is needed.

When lint fails, fix the referenced `src/` fragment, not `build/GLQS.qsps` (that's
generated output and gets overwritten every build).

## Adding functionality

**New submenu inside `mod_GLQS_main`:** add an `if $ARGS[0] = 'name': ... end` block
to an existing fragment (if related) or a new `src/NN_description.qsps` file (no
`#`/`---` wrapper needed — build.py adds it). Add a link/button to it, typically in
`05_main_menu.qsps`, via `gt 'mod_GLQS_main', 'name'`.

**New standalone QSP location (rare — only for something outside `mod_GLQS_main`):**
create `src/NN_name.qsps` with its own full `# location_name` / `--- location_name ---`
wrapper, and add `"NN_name.qsps"` to `STANDALONE_FILES` in `build.py`.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

GLQS Rolling is a QSP (Quest Soft Player) mod for the game "Girl Life". It's a cheat/debug
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
- `03_hook.qsps` defines its own location, `mod_GLQS` (matching the
  `mod_<$mod_info[0]>` naming the base game's mod loader expects), which the
  base game auto-invokes after every real `gt` transition anywhere in the
  game via `$onnewloc = 'LOCA'` (`start.qsrc`) chaining into `core_loop` in
  `mod_system.qsrc` - not just the bedroom. Whether the "Quick Setup" link
  actually renders into `mod_GLQS_main` is gated inside the file itself
  (skipped during character creation, during the game's own scripted events,
  and on the wardrobe/clothing-store screens); there is no `$locclass` check
  anywhere in the current file.
- File numbering (`01`, `02`, `03`, `05`...`17`) controls both display order in the
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
4. **`$mod_info[1]` (`01_setup.qsps`) and the top changelog entry
   (`02_readme.qsps`) must encode the same version.** They're independent
   strings with different formats — `$mod_info[1] = '03402'` is
   `0`/`34`/`02` zero-padded-to-2-digits-each with no dots, vs. the changelog's
   `'<b>Version 0.34.2 - Current</b>'` — and nothing but this lint keeps them
   in sync. Bump both on every version change: patch `$mod_info[1]` in
   `01_setup.qsps`, and prepend a new `'<b>Version X.Y.Z - Current</b>'` entry
   (moving `- Current` off the previous top entry) in `02_readme.qsps`.

When lint fails, fix the referenced `src/` fragment, not `build/GLQS.qsps` (that's
generated output and gets overwritten every build).

## Runtime gotchas (now caught by build.py's lint)

`qsp-cli` compiling with `SUCCESS` only means the syntax is well-formed - it does not
execute the code, so these used to surface as in-game errors only when you actually
opened the affected menu. Both are now checked by `build.py` (see
`lint_unbalanced_template_markers` / `lint_empty_template_markers`), but the
reasoning is worth knowing when lint flags them:

- **`<< >>` template markers must open and close inside the same string literal.**
  They cannot span a `+` concatenation - `'foo' + '<<bar[' + $key + ']>>'` fails at
  runtime with "Bracket not found" even though it compiles fine, because each quoted
  chunk is tokenized separately and `<<` with no matching `>>` in that same chunk is
  an error. If a value needs to be built from concatenated pieces (e.g. a dynamic
  array key), evaluate it directly instead of deferring to a template marker:
  `'foo' + npc_rel[$key]` (arrays accept a variable/expression as the key - no
  `dyneval` needed for reads) rather than `'foo<<npc_rel[''' + $key + ''']>>'`.
- **`<< >>` with nothing between them is always invalid**, even outside code - e.g.
  writing `<< >>` as literal text in a changelog string to describe the syntax
  itself. QSP does not know it's "just text"; it always tries to parse `<<...>>` as
  a real template marker and fails with a plain "Syntax error". Describe the syntax
  in words instead of typing literal angle brackets in any live QSP string.

## `03_hook.qsps`'s location-based hook only works for real `gt` transitions

`03_hook.qsps` renders the "Quick Setup" link by checking ambient globals like
`$curloc`/`$location_type`/`$loc`/`$loc_arg` (e.g. `$curloc <> 'wardrobe'` to
skip that screen). This only works because those screens are reached via a real `gt` location change.
Confirmed by testing live in-game: screens rendered via a plain `gs` subroutine call
from wherever the player already is (e.g. the purse - `gs 'din_bad', 'd_bag'` - or the
phone - `gs 'telefon', 'Phone_menu'`) do **not** change `$curloc` to that subroutine's
own location name, so a hook checking `$curloc = 'din_bad'` never fires even while
that screen is what's actually displayed. There is no confirmed reliable global to
detect "this gs-rendered overlay is currently on screen" from outside its own code.
Before adding a new hook point, check whether the target screen is reached via `gt`
(hookable - the hook fires globally on every real `gt` location, no per-screen
allowlist needed) or `gs` (not reliably hookable this way) - grep the reference
source for how the screen is invoked.

## Reference: the base game's own source

`reference/` (gitignored, not tracked) holds two shallow clones of the game's real
developer source, https://gitlab.com/kevinsmartstfg/girl-life:

- **`reference/nightly/`** — `master` branch HEAD, matching the `Dev Life` folder's
  newer nightly build (its filename embeds the exact commit hash it was built from,
  e.g. `dev_glife-...-<hash>.qsp` — confirm `git -C reference/nightly log -1
  --format=%H` still equals that hash before trusting a lookup for Dev-Life-only
  behavior; `master` moves fast so this drifts and needs a re-clone periodically).
  **This is the primary and default reference for all lookups going forward** —
  grep here first and only, unless a task is specifically and only about the
  stable `Girl Life` build.
- **`reference/0.9.8.3/`** — checked out at tag `0.9.8.3`, matching the `.qsp`
  installed in the `Girl Life` (stable) game folder (`Girl Life 0.9.8.3.qsp`). Kept
  on disk but no longer checked by default — the two builds have diverged in real,
  substantive ways in places (e.g. an archetype-system rewrite affecting
  `BimboCloth`/`CalcAppearance`, and character creation being restructured
  entirely from `intro_sg_select`/`intro_city_select` into
  `intro_character_creation` on nightly), so do not assume a lookup here still
  matches nightly. Only consult this if a task is explicitly about stable-only
  behavior.

This replaced an earlier approach of decompiling the installed `.qsp` with
`qsp-cli` into one flat `glife_dev_build.qsps` file — the real source here is much
better organized (one `.qsrc` file per location/system under `locations/`, original
comments intact) and doesn't need re-decompiling by hand.

**Before assuming a variable name, array name, or subsystem exists, grep
`reference/nightly/` first** — most of the bug-fix version bumps in
`02_readme.qsps`'s changelog (grades, attributes, consumables) were guessed
variable names that turned out wrong. Confirming against the real source before
writing a `src/` fragment avoids that cycle. E.g. `grep -rn "pav_.*_contribution"
reference/nightly/locations/fame.qsrc` to check the fame-spread system, `cat
reference/nightly/locations/homes_properties.qsrc` for the property system, or
search for an item's in-game display string across `reference/nightly/locations/*.qsrc`
to find its `mc_inventory[...]` key.

To refresh either clone if a lookup seems stale or the installed builds update:
`cd reference/<0.9.8.3-or-nightly> && git fetch --depth 1 origin <tag-or-branch> &&
git checkout <tag-or-branch>` (or just re-clone the same way these were set up,
matching whatever version string/commit hash the corresponding installed `.qsp`
filename shows).

## Adding functionality

**New submenu inside `mod_GLQS_main`:** add an `if $ARGS[0] = 'name': ... end` block
to an existing fragment (if related) or a new `src/NN_description.qsps` file (no
`#`/`---` wrapper needed — build.py adds it). Add a link/button to it, typically in
`05_main_menu.qsps`, via `gt 'mod_GLQS_main', 'name'`.

**New standalone QSP location (rare — only for something outside `mod_GLQS_main`):**
create `src/NN_name.qsps` with its own full `# location_name` / `--- location_name ---`
wrapper, and add `"NN_name.qsps"` to `STANDALONE_FILES` in `build.py`.

## Keeping this file accurate

When a bug or wasted cycle traces back to guidance here being wrong, stale, or
silently contradicted by a later decision elsewhere in the repo, fix the
guidance in the same session and say why — tie it to the concrete incident,
not a vague warning. Don't add speculative rules for problems that haven't
actually happened, and don't restate what's already obvious from reading
`build.py` or `src/`.

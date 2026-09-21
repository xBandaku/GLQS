# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

GLQS is a QSP (Quest Soft Player) mod for the game "Girl Life". It's a cheat/debug
menu (clothing, consumables, stats/attributes, school grades, money, relationships,
body mods, health, jobs/career, magic, housing/property, lifestyle) accessible from
the player's own room in-game (home bedroom, uni dorm room, or the therapist hotel
room). Source is plain-text `.qsps` fragments that get stitched into one `.qsps`
file and compiled to a binary `.qsp`.

## Build

```bash
python build.py
```

(`python3` resolves to a broken Windows Store shim on this machine — use `python`, which is the real 3.13 interpreter, confirmed 2026-09-18.)

Requires the QSP compiler once: `npm install -g @qsp/cli`

- Reads the explicit `SHARED_FILES` manifest in `build_support.py`, assembles `build/GLQS.qsps`, runs lint checks,
  then compiles with `qsp-cli` to `build/GLQS.qsp`.
- On `SUCCESS`, copy `build/GLQS.qsp` into the Girl Life `mod/` folder to test in-game.
- On `Lint checks FAILED`, the output names the exact file/line — fix the `src/`
  fragment and rerun. The assembled `.qsps` is still written even on failure, useful
  for inspection.
- The build-contract tests cover static assembly assumptions; manual in-game
  testing is still required for QSP runtime behavior.
- `python -m unittest discover -s tests -v` runs build-contract tests without
  requiring the QSP compiler. These cover fragment wrappers, route references,
  generated navigation actions, recurrent metadata coverage, and recurrent
  bulk-toggle coverage. Recurrent metadata rows in `08_recurrent.qsps` classify
  each toggle as `bulk`, `special`, or `individual`. The three `special` ones
  (addiction, vibrator, clothing dirt) are covered by Enable/Disable All like
  the rest, but none is done by its `cheatVars` flag alone: the vibrator also
  needs `sleepVars['bedVibrator']` set both directions, while clearing existing
  addiction progress and washing already-dirty clothes apply only when
  enabling, so those live in the enable-only branch of `'recurrent_set'`.

## Architecture: how src/*.qsps assemble into one location

Girl Life is a single QSP game file; this mod cannot add new `.qsp` locations to it
at runtime, so almost everything lives inside **one shared QSP location**,
`mod_GLQS_main`, built by concatenating fragment bodies and dispatching on
`$ARGS[0]`.

- `build.py` is only the pipeline orchestrator; the manifests, validators and
  lint rules all live in `build_support.py`, which is where edits below belong.
  The build splits `src/*.qsps` into two groups:
  - **`STANDALONE_FILES`** (currently `01_setup.qsps`, `02_readme.qsps`,
    `03_hook.qsps`) — each already contains its own `# location_name` header and
    `--- location_name ---` footer, and is passed through unwrapped, in the order
    listed in `STANDALONE_FILES` (not filename order).
  - **`SHARED_FILES`** — an explicit ordered manifest of body-only fragments of the shared
    `mod_GLQS_main` location (no `#`/`---` wrapper of its own). These are
    concatenated in manifest order, and `build.py` wraps the whole batch in one
    `# mod_GLQS_main` /
    `--- mod_GLQS_main ---` pair automatically.
- Inside `mod_GLQS_main`, each fragment is an `if $ARGS[0] = 'submenu_name': ... end`
  block acting as a sub-router — e.g. `05_clothing.qsps` handles the clothing
  menu, `05_clothing_data.qsps` owns the clothing catalog,
  `05_clothing_store.qsps` handles store routes (its `'store_buy'` takes an
  empty store to mean every store, which is what the clothing menu's Give
  Everything action calls), and `05_clothing_picker.qsps` handles item picker
  routes. `06_consumables_data.qsps` is the single consumable
  metadata table used by the menu and bulk action. `06_consumables_actions.qsps`
  and `07_stats_actions.qsps` handle feature mutators, with
  `07_stats_data.qsps` owning the skill/attribute rows both the stats menu and
  its max-all action walk,
  `14_fill_data.qsps` owns the shared single-item clothing grant route,
  `15_fill_helpers.qsps` owns `'fill_by_type'`, the one type-parameterised
  bulk-grant loop, and
  `20_jobs_data.qsps` owns the job ID/title table used by `19_jobs.qsps`.
  `09_grades_data.qsps` owns the grade rows used by the grades menu and
  max-all action, while `11_relationships_data.qsps` owns relationship category
  labels.
  Menus link to each other via
  `gt 'mod_GLQS_main', 'other_menu_name'`.
- Two shared routes in `04_main_menu.qsps` are called by nearly every screen:
  `'navbar'` renders the quick-nav bar, and `'screen_head'` is the five-line
  opener (`menu_off`/`usehtml`/`$location_type`/`gs 'stat'`/`gs 'themes'`).
  `'screen_head'` deliberately does not print the title or call `'navbar'` -
  those vary per screen and nested sub-screens get no navbar at all. Because
  it is a nested `gs`, a caller that reads its own `$ARGS` must capture them
  before calling it.
- `03_hook.qsps` defines its own location, `mod_GLQS` (matching the
  `mod_<$mod_info[0]>` naming the base game's mod loader expects), which the
  base game auto-invokes after every real `gt` transition anywhere in the
  game via `$onnewloc = 'LOCA'` (`start.qsrc`) chaining into `core_loop` in
  `mod_system.qsrc` - not just the bedroom, though the hook fires on every
  real `gt` location, the link itself only renders in the player's own
  room: the current home bedroom (`func('homes_properties',
  'is_current_home', $curloc)` plus `$locclass = 'bedr'`), the uni dorm
  room, or the therapist hotel room - also skipped during character
  creation and the game's own scripted events.
- File numbering groups related files for readability, but `SHARED_FILES` in
  `build_support.py` controls assembly order. Add every new shared fragment to that
  manifest or the build fails.
- `build.py` expands the navigation registry in `04_main_menu.qsps` into literal
  action-button entries because QSP evaluates `act` bodies at click time. Keep the
  `GLQS_NAV_ACTIONS_BEGIN`/`GLQS_NAV_ACTIONS_END` markers in that source file.
  It also expands the clothing catalog into literal store labels and category
  actions between the clothing markers in `05_clothing_store.qsps`. Keep the
  catalog rows in `05_clothing_data.qsps` labeled as
  `store|type|key|category label`; do not hand-add picker actions.
  The build validates route coverage, fragment wrappers, navigation consistency,
  consumable metadata roles, clothing catalog
  coverage, and that `'recurrent_set'` (the single parameterised bulk handler,
  0 or 1 via `$ARGS[1]`) assigns every toggle the recurrent menu's primary
  table renders, and that individual toggles have displayed states.
  When `reference/nightly/` is available, the build also compares the job
  manifest against `jobs_list.qsrc`; without it, duplicate and malformed IDs
  are still rejected.

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
   strings with different formats — `$mod_info[1]` is major/minor/patch
   zero-padded-to-2-digits-each with no dots (e.g. `'03402'` = version
   0.34.2), vs. the changelog's dotted `'<b>Version X.Y.Z - Current</b>'` —
   and nothing but this lint keeps them in sync. Bump both on every version
   change: patch `$mod_info[1]` in `01_setup.qsps`, and prepend a new
   `'<b>Version X.Y.Z - Current</b>'` entry (moving `- Current` off the
   previous top entry) in `02_readme.qsps`.

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

## Setting base-game stats: many `pcs_*` values are derived, not stored

`stat_sklattrib_lvlset.qsrc` (run by every single `gs 'stat'` pass) recomputes a
long list of `pcs_*` variables from their `*_lvl` counterparts plus attributes —
e.g. `pcs_vball_block/rec/serve/set/spike` are all derived from `vball_lvl` and
attribute values. Writing such a variable directly compiles and even displays
fine, but the next `gs 'stat'` (which every GLQS menu itself runs) silently
overwrites it, so the write does nothing. This shipped as dead code once: five
direct `pcs_vball_*` writes sat in `07_stats_actions.qsps` across many releases until
the v0.34.4 reference audit caught them. Before assigning any `pcs_*` variable
directly, grep `reference/nightly/locations/stat_sklattrib_lvlset.qsrc` for it —
if it's assigned there, set the underlying skill/attribute via
`gs 'shortgs', 'setStat', '<name>', <value>` instead (or skip it entirely:
derived values follow automatically once their inputs are maxed).

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

`reference/` (gitignored, not tracked) holds shallow clones of the game's real
developer source, <https://gitlab.com/kevinsmartstfg/girl-life>. Only
`reference/nightly/` is currently on disk:

- **`reference/nightly/`** — `master` branch HEAD, matching the `Dev Life` folder's
  newer nightly build (its filename embeds the exact commit hash it was built from,
  e.g. `dev_glife-...-<hash>.qsp` — confirm `git -C reference/nightly log -1
  --format=%H` still equals that hash before trusting a lookup for Dev-Life-only
  behavior; `master` moves fast so this drifts and needs a re-clone periodically).
  **This is the primary and default reference for all lookups going forward** —
  grep here first and only, unless a task is specifically and only about the
  stable `Girl Life` build.
- **`reference/0.9.8.3/`** — **not currently on disk** (removed after nightly
  became the sole default reference; confirmed absent during the 2026-07 full
  audit). It was a clone checked out at tag `0.9.8.3`, matching the `.qsp`
  installed in the `Girl Life` (stable) game folder (`Girl Life 0.9.8.3.qsp`).
  Only re-clone it (shallow, at that tag, using the refresh command below) if a
  task is explicitly about stable-only behavior — and even then remember the two
  builds have diverged in real, substantive ways in places (e.g. an
  archetype-system rewrite affecting `BimboCloth`/`CalcAppearance`, and
  character creation being restructured entirely from
  `intro_sg_select`/`intro_city_select` into `intro_character_creation` on
  nightly), so do not assume a stable lookup still matches nightly or vice
  versa.

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

To refresh `nightly` if a lookup seems stale (or to re-create the `0.9.8.3`
clone if a stable-only task ever needs it):
`cd reference/<0.9.8.3-or-nightly> && git fetch --depth 1 origin <tag-or-branch> &&
git checkout <tag-or-branch>` (or just re-clone the same way these were set up,
matching whatever version string/commit hash the corresponding installed `.qsp`
filename shows).

## Adding functionality

**New submenu inside `mod_GLQS_main`:** use the `/new-submenu` skill (see Automation
below) — it scaffolds the router block, and correctly handles the difference between
a top-level menu (registered in `04_main_menu.qsps`'s `$glqs_nb` nav array) and a
nested submenu (a plain `act` link from its parent, no nav entry), which is easy to
get wrong by hand.

**New standalone QSP location (rare — only for something outside `mod_GLQS_main`):**
create `src/NN_name.qsps` with its own full `# location_name` / `--- location_name ---`
wrapper, and add `"NN_name.qsps"` to `STANDALONE_FILES` in `build_support.py`.

## Automation

Project-local Claude Code config under `.claude/` (set up 2026-09-18):

- **`reference-lookup` subagent** — searches `reference/nightly/locations/*.qsrc`
  for game-engine internals before writing new `src/` code. Use it instead of
  grepping the reference tree inline for anything beyond a one-off lookup.
- **`/release <patch|minor> <what changed>` skill** — bumps `$mod_info[1]` +
  changelog together, builds, commits, tags, pushes, and publishes the GitHub
  release in one pass. Runs `avoiding-ai-code-tells` and `avoiding-ai-writing-tells`
  at both the commit and the release-notes step.
- **`/new-submenu` skill** — scaffolds a new cheat-menu screen (see "Adding
  functionality" above).
- **PostToolUse hook** on `src/*.qsps` edits — re-runs `build.py`'s lint checks
  immediately after the edit (`.claude/hooks/lint_check.py`).
- **PreToolUse hook** — blocks edits to `build/GLQS.qsps`/`build/GLQS.qsp`
  (generated output, overwritten every build) with a pointer to edit the `src/`
  fragment instead (`.claude/hooks/protect_build_output.py`).

## Keeping this file accurate

When a bug or wasted cycle traces back to guidance here being wrong, stale, or
silently contradicted by a later decision elsewhere in the repo, fix the
guidance in the same session and say why — tie it to the concrete incident,
not a vague warning. Don't add speculative rules for problems that haven't
actually happened, and don't restate what's already obvious from reading
`build.py`, `build_support.py` or `src/`.

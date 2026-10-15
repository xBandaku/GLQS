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

Use `python` on this machine: it resolves to Python 3.12.10, checked 2026-10-14.
CI uses Python 3.13. The ignored local compiler installation can be used in
PowerShell with `$env:PATH = (Resolve-Path 'build/tooling/node_modules/.bin').Path + ';' + $env:PATH`
before running the build.

Requires the QSP compiler once: `npm install -g @qsp/cli@1.0.5` (the version CI pins)

- Reads the explicit `SHARED_FILES` manifest in `build_support.py`, assembles
  `build/GLQS.qsps`, runs `validate_assembled()` and the lint checks, then
  compiles with `qsp-cli` to `build/GLQS.qsp`.
- On `SUCCESS`, copy `build/GLQS.qsp` into the Girl Life `mod/` folder to test in-game.
- On `Checks FAILED`, the output names the failing validator or the exact lint
  line — fix the `src/` fragment and rerun. The assembled `.qsps` is written
  before any check runs (as UTF-8, so a non-ASCII character is reported by lint
  rather than crashing the write), so it is there for inspection. Only a
  manifest or assembly error (`Build FAILED:`) stops before it is written.
- `build.py` and the tests call the same
  `build_support.validate_assembled()` and `run_lints()`. Add a new whole-build
  check there, not in one caller. Earlier guidance also described an edit hook,
  but `.claude/` is absent from this checkout; no hook runs automatically here.
- The build-contract tests cover static assembly assumptions. Optional QSP 5.9.5
  engine tests cover relationship transitions, pain clearing and consumable
  restocking. They use real upstream relationship and pain code with isolated
  rendering, NPC and phone services. Full-save behavior and QSP 5.7 still need
  in-game checks.
- `python -m unittest discover -s tests -v` runs build-contract tests without
  requiring the QSP compiler. These cover fragment wrappers, route references,
  generated navigation actions, the recurrent data table, every lint rule, and
  a full run of the real source tree through `validate_assembled()` and
  `run_lints()`.
- To enable the runtime tests locally, keep the pinned reference present and
  run `npm install --prefix build/tooling @qsp/converters@1.0.1 @qsp/wasm-engine@1.6.1 --no-audit --no-fund`.
  The same unittest command then runs them through Node. They report a skip when
  Node, either package or the required upstream files are absent. CI installs the
  packages and fetches the pinned reference before testing.
- Recurrent Cheats: `'recurrent_data'` in `08_recurrent_data.qsps` holds one
  `role|key|arg|label` row per toggle, and both the on-screen table and
  Enable/Disable All (`'recurrent_set'`) loop over it, so the two cannot
  drift. `bulk` rows set `cheatVars[key]` to `arg` (the on-value). The three
  `special` rows (addiction, vibrator, clothing dirt) are not done by the flag
  alone, so `arg` names the base game's own `cheatmenu_din` handler, which also
  clears addiction progress, sets `sleepVars['bedVibrator']`, or washes dirty
  clothes. Those handlers toggle, so `'recurrent_set'` calls one only when the
  flag differs from the target. The individual toggles below the table (periods,
  archetypes, etc.) stay hand-written, because each has its own semantics.

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
  Everything action calls), `05_clothing_picker.qsps` handles item picker
  routes, and `05_clothing_grant.qsps` owns `'item_grant'` (one item),
  `'fill_by_type'` (every item in a category), `'clothing_totals'` and
  `'item_attributes'`, the routes every clothing grant goes through. The
  picker's sort/filter buttons come from `05_clothing_filter_data.qsps`, one
  `role|type|name|expr` row per button, with each filter expr copied from the
  base game's `clothing_view.qsrc`/`shoe_view.qsrc`. `06_consumables_data.qsps` is the
  single consumable metadata table used by the menu and Set All, one row per
  item, each `stack` (any quantity) or `single` (owned or not).
- **Layout convention:** a feature with a data table has an `NN_x_data.qsps`
  fragment listed right before its menu fragment in `SHARED_FILES` (clothing,
  consumables, stats, recurrent, grades, relationships, fame, jobs). The
  menu fragment also holds that feature's action routes unless another
  feature shares them (the clothing grant routes are shared, so they have
  their own file). Menus link to each other via
  `gt 'mod_GLQS_main', 'other_menu_name'`.
- **Data tables:** every table is a list of pipe-delimited rows appended with
  `$name[] = 'a|b|c'` (cleared with `killvar` at the top of its data route,
  counted with `arrsize()`), one row per line. Readers split a row with
  `gs 'mod_GLQS_main', 'split_row', $row`, which fills `$glqs_field[0..n]`;
  copy the fields you need before calling `split_row` again, and never
  hand-write another `instr`/`$mid` chain - reading three fields from a
  four-field row that way is what broke `store_buy` in v0.36.1. The build
  parses the nav, clothing, consumables, jobs and recurrent tables with the
  row patterns at the top of `build_support.py`, so a change to a table's
  row syntax needs the matching pattern changed too (the build fails loudly
  with "... table is empty" if they disagree).
- Two shared routes in `04_main_menu.qsps` are called by nearly every screen:
  `'navbar'` renders the quick-nav bar, and `'screen_head'` is the five-line
  opener (`menu_off`/`usehtml`/`$location_type`/`gs 'stat'`/`gs 'themes'`).
  `'screen_head'` deliberately does not print the title or call `'navbar'` -
  those vary per screen and nested sub-screens get no navbar at all.
- **`$ARGS` is local to each `gs`/`gt` call** - a nested `gs` does not
  overwrite the caller's `$ARGS` (`rel_menu` makes two nested calls and then
  still matches `$ARGS[0] = 'rel_menu'`). What does lose them is an `act`
  body or `exec:` link: it runs at click time, after the route has returned,
  so anything it reads must be copied into a `glqs_` global first and not
  killed at the end of the route. That, not `gs` clobbering, was the real
  cause of the v0.27/v0.28 "ARGS clobbering" fixes in the changelog; older
  comments blaming nested `gs` were corrected on 2026-09-23.
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
- GLQS has three entry points: that room link, an "Open GLQS" link the same
  hook prints under every tab of the base game's cheat menu
  (`$curloc = 'cheatmenu_din'`; the hook's `$ARGS[0]` is the open tab), and
  Settings > Mods, whose `$mod_info[4]` link runs `mod_GLQS_options`. Every
  entry calls `'enter'` (`04_main_menu.qsps`) with the screen to return to
  before `gt 'mod_GLQS_main', 'start'`. `'enter'` snapshots
  `$loc`/`$loc_arg`/`$menu_loc`/`$menu_arg`, and Return's `'leave'`
  restores them: `start` calls `setloc`, which overwrites them, and the
  settings screen and cheat menu both exit with `gt $menu_loc, $menu_arg`.
  A new entry point must go through `'enter'` too. Checked with the
  reference-lookup agent (2026-09-23): the base game offers mods no
  icon-row, phone-app, cheat-tab or object-panel hook, and the purse and
  phone are `gs` overlays the hook cannot see.
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
  consumable metadata roles, clothing catalog coverage, the recurrent data
  rows, and that individual recurrent toggles have displayed states.
  When `reference/nightly/` is available, the build also compares the job
  manifest against `jobs_list.qsrc` and checks each recurrent `special`
  handler exists in `cheatmenu_din.qsrc`; without it, duplicate and malformed
  IDs and rows are still rejected. Route coverage recognises `gt`, `gs`,
  `func` and `$func` calls into `mod_GLQS_main`.

## Value editors, favorites and presets

`04_quick_tools.qsps` contains `ask_number`, which returns its accepted value
through `glqs_input_value` and its cancellation/validation status through
`glqs_input_ok`. Callers must check that status before changing game state.
Numeric input permits at most nine digits. Stat edits reuse `shortgs/setStat`;
money grants split whole millions into overflow counters before normalization.

Favorites use a fixed registry of common cheats and call the same routes as
their menus. `glqs_favorites[key]` stores pins. `19_presets.qsps` stores five
named slots in `$glqs_preset_codes` and `$glqs_preset_names`; the selected apply
groups are separate flags. Internal presets have whitelisted, bounded keyed
fields. Parse the complete preset before applying any group, and use the
upstream handlers for cheat switches with side effects.

The build fills `GLQS_PROFILE_SCHEMA_BEGIN` / `GLQS_PROFILE_SCHEMA_END` with a
signature of the ordered metadata layout and fixed preset fields. Compact
exports include that signature and use numbered parts with 100-character
payloads to fit native and wasm input limits. Reordering fields changes the
signature; cosmetic stat labels do not. Import rejects incompatible layouts,
bad values, duplicate keys and out-of-order parts. The runtime suite exercises
export/import, partial application, cancellation and save/reload in an isolated
game. Existing full-game saves have not been tested.

## Branch history: this line was reset once, then restored

`main` was hard-reset from v0.36.1 back to v0.34.4 in September 2026, and the
24 discarded commits were parked on `backup/main-v0.36.1`. The reason was never
written down at the time; it was found later by review. **v0.36.1 shipped with
every clothing grant writing to array index 0** (lint rule 5 below), so the
mod's headline feature silently did nothing. A second bug from the same
refactor made `store_buy` read three columns from a catalog that had grown to
four, so Give Everything and Buy All granted nothing either.

Both are fixed, and this line was restored as v0.37.0 rather than re-porting
~3,000 lines of features onto the rolled-back `main`. Do not treat the v0.36.1
tag or its release as a working reference - it is the one build where clothing
is broken. Version numbering continues past it so releases stay monotonic.

The decision is recorded here so it does not get re-litigated: **harvest from
`main`, build on this line.** `main`'s v0.36.2 tag holds the fixes that were
developed there; all of them are now present here.

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

5. **No numeric variable may be assigned from `$ARGS[n]`.** QSP keeps each
   argument's numeric and string value in separate slots, so `x = $ARGS[3]`
   reads the string slot - empty whenever the caller passed a number - and
   silently yields `0` instead of erroring. This has now shipped twice: once
   in `item_grant` on the old layout, and again in v0.36.1, when the clothing
   refactor reintroduced it at `item_pick` and `item_grant` while this branch
   had no such lint. Every clothing grant wrote to array index 0 and nothing
   reported a problem. Use `ARGS[n]`, or `val($ARGS[n])` if the caller really
   sends a numeric string.
6. **A `GLQS_*_BEGIN`/`_END` marker pair must not be empty in the assembled
   output.** These are placeholders that a build-time expansion fills. When the
   expansion does not run, the markers survive as inert comments, the generated
   block is empty, and every other validator still passes while `build.py`
   prints `SUCCESS` - which once produced an item picker with 0 of its 82
   actions. `assemble()` now probes for the marker instead of a hardcoded
   filename, so renaming a fragment cannot silently skip expansion.

When lint fails, fix the referenced `src/` fragment, not `build/GLQS.qsps` (that's
generated output and gets overwritten every build).

## Runtime gotchas (now caught by build.py's lint)

`qsp-cli` printing `SUCCESS` means conversion produced a binary; it does not fully
validate QSP statement syntax or execute the code, so these used to appear as
in-game errors only when you actually
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
direct `pcs_vball_*` writes sat in `07_stats_actions.qsps` (now part of `07_stats_menu.qsps`) across many releases until
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

`reference/` is ignored and holds upstream source from
<https://gitlab.com/kevinsmartstfg/girl-life>. On 2026-10-14,
`reference/nightly/` is a detached checkout pinned to
`83b164f64224f1ba88fd409469c1a9379ad34f86` (2026-10-09). The directory name
is historical: this checkout does not automatically follow `master` or establish
which source revision an installed game uses. `reference/0.9.8.3/` is absent.
Treat the reference as read-only and use the pinned checkout for reproducible
lookups. Check a target game's exact source revision separately before claiming
compatibility with it.

The [GLQS research](research/qsp-technical-reference/glqs-analysis/project-overview.md)
records the current source measurements and integration checks. The shared QSP,
engine and Girl Life reference was carried over from GLSS research dated
2026-10-14; inherited GLSS results do not validate GLQS.

**Before assuming a variable name, array name, or subsystem exists, grep
`reference/nightly/` first** — most of the bug-fix version bumps in
`02_readme.qsps`'s changelog (grades, attributes, consumables) were guessed
variable names that turned out wrong. Confirming against the real source before
writing a `src/` fragment avoids that cycle. E.g. `grep -rn "pav_.*_contribution"
reference/nightly/locations/fame.qsrc` to check the fame-spread system, `cat
reference/nightly/locations/homes_properties.qsrc` for the property system, or
search for an item's in-game display string across `reference/nightly/locations/*.qsrc`
to find its `mc_inventory[...]` key.

Check the active pin with `git -C reference/nightly rev-parse HEAD`.
When a task requires another upstream revision, choose and record that revision
explicitly. Do not refresh this checkout to a moving branch during an unrelated
change or infer an installed game's revision from this directory's name.

## Adding functionality

**New submenu inside `mod_GLQS_main`:** add a router block in the appropriate
shared fragment. Register a top-level menu in `04_main_menu.qsps`'s `$glqs_nb`
nav array; link a nested submenu from its parent without adding a nav entry.
The previously documented `/new-submenu` skill is unavailable in this checkout.

**New standalone QSP location (rare — only for something outside `mod_GLQS_main`):**
create `src/NN_name.qsps` with its own full `# location_name` / `--- location_name ---`
wrapper, and add `"NN_name.qsps"` to `STANDALONE_FILES` in `build_support.py`.

## Automation

Earlier project guidance described `.claude/` configuration created on
2026-09-18: a `reference-lookup` subagent, `/release` and `/new-submenu` skills,
and edit-time lint and generated-output protection hooks. That directory is
ignored and absent from this checkout, checked 2026-10-14. Those entries are
historical descriptions, not available automation. Run the build and tests
explicitly, search the upstream source directly, and edit source fragments
rather than generated output.

## Keeping this file accurate

When a bug or wasted cycle traces back to guidance here being wrong, stale, or
silently contradicted by a later decision elsewhere in the repo, fix the
guidance in the same session and say why — tie it to the concrete incident,
not a vague warning. Don't add speculative rules for problems that haven't
actually happened, and don't restate what's already obvious from reading
`build.py`, `build_support.py` or `src/`.

---
name: release
description: This skill should be used when cutting a new GLQS release - the user says "release", "cut a release", "bump the version", "new version", or asks to update the changelog. Keeps $mod_info[1] (01_setup.qsps) and the changelog top entry (02_readme.qsps) in sync across their two different formats, adds changelog notes, and rebuilds to verify before anything is committed.
---

# Cutting a GLQS release

Two files independently encode the same version number in different formats,
and nothing but a build-time lint (`lint_version_mismatch` in `build.py`)
catches drift between them. This skill does the bump correctly in one pass
instead of relying on the lint to catch a mistake after the fact.

## 1. Read the current version

- `src/01_setup.qsps`: `$mod_info[1] = '03402'` - five digits, no dots:
  1-digit major, then minor and patch each zero-padded to exactly 2 digits.
  `'03402'` = `0` / `34` / `02` = version `0.34.2`.
- `src/02_readme.qsps`: the top changelog entry, e.g.
  `'<b>Version 0.34.2 - Current</b>'` - normal dotted version, no channel
  tag (that's a GLQS-Stable-only convention, not used here), and `- Current`
  marking it as the newest entry.

Confirm these two agree before starting (they should, since `build.py` lints
this on every build).

## 2. Work out what's changing

If the user gave a version number and change notes, use those. Otherwise:
- Determine the new version number by asking the user (don't guess a bump
  size - major/minor/patch is a judgment call about what changed).
- Derive the changelog bullets from `git log`/`git diff` since the last
  version bump, or from what was actually done in this session. Each bullet
  should explain root cause the way existing entries do (see any entry in
  `02_readme.qsps` for the expected level of detail) - not just "fixed X".

## 3. Update `src/01_setup.qsps`

Set `$mod_info[1]` to the new version in the same 1+2+2-digit zero-padded
format, e.g. version `0.35.0` -> `'03500'`. (The regex `build.py` lints
against requires the major version to be exactly one digit - not a concern
until this mod reaches major version 10.)

## 4. Update `src/02_readme.qsps`

- Change the *current* top entry's line from
  `'<b>Version OLD - Current</b>'` to plain `'<b>Version OLD</b>'` (drop
  `- Current` - every older entry in the file looks like this).
- Insert a new block directly above it, matching the existing pattern:
  ```
  '<b>Version NEW - Current</b>'
  '- Added/Changed/Fixed: <bullet>'
  '- Added/Changed/Fixed: <bullet>'
  *nl
  ```
  (the `*nl` was already there separating the old top entry from the one
  before it - leave it in place, just above the now-non-current old entry).

Two lint rules apply to this new text same as anywhere else in `src/`: ASCII
only, and no apostrophes inside `!!` comments. The existing changelog entries
also avoid apostrophes entirely in the visible text (e.g. "the base games
own" not "the base game's own") - match that style rather than
double-escaping `''` mid-sentence.

## 5. Rebuild and verify

Run `python3 build.py` from the repo root. Confirm `Lint checks passed`
(specifically no version-mismatch warning) and `SUCCESS` from `qsp-cli`.
If either fails, fix the fragment - don't hand-edit `build/GLQS.qsps`.

## 6. Stop here

Don't commit or push automatically. Report the new version and a summary of
the changelog entry, and let the user decide when to test in-game and when
to commit/push - those are separate, explicitly-authorized actions.

# GLQS Mod — Dev Project

## Setup (one-time)

1. Install Node.js if you don't have it: https://nodejs.org
2. Install the QSP compiler:
   ```
   npm install -g @qsp/cli
   ```

## Folder layout

```
GLQS_project/
  src/
    01_setup.qsps          standalone location: mod info, version, description
    02_readme.qsps         standalone location: in-game changelog page
    03_hook.qsps           standalone location: bedroom link + cheat menu recurrent tab
    05_main_menu.qsps       \
    06_clothing.qsps         \  all of these are BODY FRAGMENTS of the single
    07_consumables_menu.qsps  \ 'mod_GLQS_main' location. build.py stitches them
    08_stats_menu.qsps        / together in filename order under one shared
    09_recurrent.qsps        /  '# mod_GLQS_main' ... '--- mod_GLQS_main ---'
    10_grades.qsps          /   wrapper automatically.
    11_money.qsps           /
    12_relationships.qsps  /
    13_bodymod.qsps        /
    14_health.qsps        /
    15_actions.qsps      /
    16_fill_helpers.qsps /
  build.py                 the build script
  build/                   output folder (created automatically)
    GLQS.qsps              assembled plain-text source
    GLQS.qsp               compiled binary — this is what goes in the game
```

## Workflow

1. Edit whichever `src/*.qsps` file covers the feature you're changing.
   Each file has a comment at the top saying what it covers.
2. Run:
   ```
   python3 build.py
   ```
3. If it prints `SUCCESS`, copy `build/GLQS.qsp` into your Girl Life `mod/` folder.
4. If it prints `Lint checks FAILED`, read the error — it'll tell you the exact
   line and what's wrong. Fix it in the `src/` file and run again.

## What the linter catches

These are all real bugs we hit building this mod, now caught automatically
before you waste time reloading the game to find them:

- **Apostrophes inside `!!` comments** — e.g. writing `!! the player's items`
  will break the parser. QSP doesn't reliably ignore quotes inside comments,
  so a stray `'` opens an unterminated string that can corrupt everything
  after it. Just avoid apostrophes in comments (write `players` not `player's`).
- **Non-ASCII characters** — smart quotes, em-dashes (—), etc. anywhere in
  the file, including comments, cause a hard syntax error. Stick to plain
  ASCII: use `-` instead of `—`, straight quotes instead of curly ones.
- **Unbalanced `if`/`act`/`end` blocks** — a rough check that every
  multi-line `if ...:` or `act 'label':` has a matching `end`. It's not a
  full parser (doesn't perfectly understand every edge case) but it catches
  the common mistake of a missing or extra `end` before you go hunting
  for it in-game.

## Adding a new submenu

1. Either add it to an existing fragment file if it's related, or create
   a new `src/NN_description.qsps` file (pick a number to control where
   it sits in the file — doesn't have to be exact, just keep menus roughly
   grouped with related code).
2. Write your `if $ARGS[0] = 'your_menu_name':` block as normal QSP code —
   no `#` header or `---` footer needed, build.py adds those automatically
   for the shared location.
3. Add a button somewhere (usually `05_main_menu.qsps`) that does
   `gt 'mod_GLQS_main', 'your_menu_name'`.
4. Run `python3 build.py`.

## Adding a whole new standalone location (rare)

Only needed if you want a second QSP location outside `mod_GLQS_main` —
none of the submenus need this, they all live inside the shared location.

1. Create `src/NN_name.qsps` with its own full `# location_name` header
   and `--- location_name ---------------------------------` footer.
2. Add `"NN_name.qsps"` to the `STANDALONE_FILES` list near the top of
   `build.py`.
3. Run `python3 build.py`.

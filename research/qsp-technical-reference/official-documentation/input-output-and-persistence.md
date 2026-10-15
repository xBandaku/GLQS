# Input, output and persistence

Screen output, HTML and links, player input, sound and images, game files, libraries, and the save format. References as in [source-index.md](../source-index.md).

## 1. Output windows

| Window | Written by | Read back with | Cleared by |
|---|---|---|---|
| Main description | implicit statement, `*p`, `*pl`, `*nl`, base descriptions | `$MAINTXT` | `*clr`, `cls`, `GOTO` |
| Additional description (stats) | `p`, `pl`, `nl` | `$STATTXT` | `clr`, `cls` (not `GOTO`) |
| Actions | `act`, base actions | `$CURACTS`, `$SELACT` | `cla`, `cls`, `GOTO`, `XGOTO`, `delact` |
| Objects | `addobj` | `$CUROBJS`, `$GETOBJ`, `$SELOBJ`, `COUNTOBJ` | `delobj`, `killobj`, `killall` |
| Input line | the player | `$USER_TEXT` | `cmdclear`, `cls` |
| View | `view` | none | `view ''` |

Text is held in engine buffers and drawn by the player after the event finishes, or earlier when a dialog or `WAIT` forces a refresh ([execution-model.md](execution-model.md)). Line breaks are stored as CR LF (`QSP_STRSDELIM`).

## 2. HTML and links

- With `usehtml` non-zero, the classic player renders text, action names, object names and dialog text as HTML (`qspgui: qspgui/callbacks_gui.cpp:96`). qSpider renders HTML always (docs, `USEHTML`).
- Which tags and attributes work depends on the player's HTML widget. The classic player uses wxWidgets' HTML window; Qqsp uses Qt WebEngine (`girl-life: tools/Qqsp-Src/README.MD` lists the Qt WebEngine component). This reference did not test individual tags.
- Links: `<a href="exec:CODE">` runs `CODE` as QSP when clicked. The prefix is matched case-insensitively, and the code runs in a new local scope with the global `ARGS` visible (`qspgui: qspgui/frame.cpp`, `OnLinkClicked`; engine `QSPExecString`). `href="#name"` scrolls to an anchor. Other URLs open in the system browser.

**Quoting inside links.** The link code sits inside an HTML attribute inside a QSP string, so it needs two levels of quoting. Girl Life's standard form doubles apostrophes:

```qsp
'There is a shower, toilet, sink, and a <a href="exec:gt ''mirror'',''start''">mirror</a> ...'
```

(`girl-life: locations/core_library.qsrc:85`). After QSP unescapes the literal, the HTML attribute holds `gt 'mirror','start'`. Girl Life has 3,801 `exec:` links and 30,263 `<img` tags in `locations/`.

**Images.** `<img src="images/...">` paths are relative to the game file's folder. Girl Life writes `<img <<$set_imgh>> src="images/...">` throughout; `$set_imgh` holds a size attribute chosen in the settings menu (`'height = <<cfg_vars[''imgh'']>>'`, `'width = ...'` or `''`, `girl-life: locations/_menu_settings.qsrc:726-731`). The images are not in the Git repository (`girl-life: .gitignore` excludes `images/`).

**Video.** Girl Life's start screen tests `<video autoplay loop ... src="images/system/test_video.mp4">` (`girl-life: locations/start.qsrc`, "Test video" action). This depends on the player; Girl Life ships a classic player build with libvlc (`tools/Player-video/libvlc.dll`).

## 3. Input from the player

| Mechanism | How | Notes |
|---|---|---|
| Action click | `act` | the main interaction model |
| Link click | `<a href="exec:...">` | needs `usehtml` in the classic player |
| Object click | `$ONOBJSEL` handler with `$SELOBJ` | call `unsel` to allow clicking the same object again |
| Action hover | `$ONACTSEL` handler with `$SELACT` | fires on selection change |
| Text dialog | `$INPUT('prompt')` | returns `''` on cancel |
| Input line | `$USERCOM` handler with `$USER_TEXT` | fires on Enter |
| Menu | `MENU 'array'` | calls the chosen item's location with its 1-based position in `ARGS[0]` |
| Message | `MSG 'text'` | blocks until closed |

Validate typed numbers before converting: `if isnum($s): n = val($s)`. The docs show a loop that retries until the answer is numeric.

Girl Life's debug console reads a line with `input(...)` and runs it with `dynamic` (`girl-life: locations/onobjsel.qsrc:8-13`, `dynamic $dynamicCommand` on line 11). Its `$USERCOM` location `inputProcessing` is empty.

## 4. Sound

- `PLAY file[, volume]` asks the player to play a file, volume 0-100. The engine records the file and volume in a playlist of up to 500 entries (`playlist.c`).
- `CLOSE file` stops a file only if the playlist contains it; `CLOSE` or `CLOSE ALL` stops all.
- `ISPLAY(file)` asks the player.
- The playlist is saved. Loading a save stops all sound and replays the saved playlist (`game.c`, `qspPlayPLFiles` during load). When the playlist is full, the engine first drops entries that are no longer playing.
- File formats and the simultaneous-playback limit (the docs say 32) depend on the player and were not verified.

## 5. Images outside HTML

- `VIEW path` shows a picture in a separate window (classic) or layer (qSpider). `view` or `view ''` hides it.
- `$BACKIMAGE` sets a background image for the main window.

## 6. Game files

### Binary `.qsp` format

From `engine: help/gam_desc.txt`, `qsp/game.c:191` (`qspOpenGame`) and `qsp/coding.c`:

- Lines separated by CR LF. Unicode files store each character as 2 bytes, little-endian (UCS-2 LE). The engine detects Unicode when the second byte of the file is 0.
- Each stored string has every character code shifted by -5, with code 5 written as -5 so the shift is reversible (`coding.c:267`, `QSP_CODREMOV 5`). This also hides the CR LF inside multi-line code.
- New format header: `QSPGAME`, a version and tool string, the encoded password, the encoded location count. Each location: name, base description, code, action count, then for each action: image, name, code.
- Old format: location count, password, version, 27 reserved lines; each location has exactly 20 actions without images.
- The engine does not check the password. Tools such as TXT2GAM use it (`-p` option).
- Locations whose name already exists are skipped when loading or including ("the first location with a name wins").
- A CRC-32 of the whole file is kept as the game identifier for save checks (`game.c`, `qspCRC`).

### Text formats

`.qsps` and `.qsrc` (the latter an extension Girl Life introduced, per the docs blog) are both "TXT2GAM format" text. The engine cannot load text directly; players and tools convert first ([tooling-and-development.md](tooling-and-development.md)).

### Libraries and switching games

| Statement | Effect |
|---|---|
| `INCLIB 'file'` | Adds the file's locations to the world; existing names win. Remembers the path. Up to 100 files. Same path twice is ignored |
| `FREELIB` | Removes all included locations at once (there is no per-file unload) |
| `OPENQST 'file'` | Replaces the game and starts its first location, keeping variables and objects |

Paths are interpreted by the player relative to the game folder. Girl Life's mod system loads `mod/<name>.qsp` with `inclib` (or `addqst` on 5.7) and, to remove one mod, frees all libraries and includes the remaining ones again (`girl-life: locations/mod_system.qsrc:166-225`, handler `delete_mod`).

## 7. Saving and loading

### What a save contains

`qspSaveGameStatus` (`engine: qsp/game.c:263`) writes, in order:
1. `QSPSAVEDGAME`, the engine version, the game file CRC, play time in ms, selected action and object.
2. The view path, input line text, main text, stats text, current location name, window visibility, timer interval.
3. The sound playlist and the list of included library files.
4. Every action: name, image, each code line with its line number, source location name, base action index.
5. Every object and object group (including `MODOBJ` titles).
6. Every global variable with all values and string keys. Local variables are not saved.

`$ONGSAVE` handlers run first, with globals only (`game.c:271-276`). A `gt` inside the handler stops the code that called `savegame` (wasm test "global variables get restored if ONGSAVE calls goto").

### What loading does

`qspOpenGameStatus` (`game.c`):
1. Checks the header. The save's engine version must be at least the minimum game version and not newer than the running engine (`game.c:391`): 5.9.4 and 5.9.5 accept saves from 5.9.4 or later (`QSP_GAMEMIN_VER "5.9.4"` in `CMakeLists.txt` at both tags); master accepts only 5.9.6 or later (commit `af77f90`). Version strings are compared as text.
2. If `DEBUG` element 0 is 0, the save's CRC must equal the loaded game's CRC. Any change to the game file then makes old saves unloadable. `DEBUG` is read from the running game's globals before the save's variables replace them.
3. Replaces all state with the saved values.
4. Reloads the included library files, so actions and the current location can refer to their locations.
5. Restores the current location by name without running its code. The screen shows the saved text and saved actions.
6. Restarts saved sounds, shows windows, then runs the `$ONGLOAD` handlers.

**Inferred consequences.**
- Saved actions keep the code they had when saved. After a game update, clicking an action restored from an old save runs the old code. Code that depends on the current location's behavior has to be re-entered (for example by `gt $curloc` in an `$ONGLOAD` handler) to pick up changes.
- Saves made by 5.7 players cannot be loaded by 5.8+ players, and saves from 5.9.3 or earlier cannot be loaded by 5.9.4/5.9.5.
- The text comparison of versions treats `"5.10.0"` as smaller than `"5.9.4"`.

### Girl Life's save handling

- `start` sets `debug = 1` so saves survive game updates (`girl-life: locations/start.qsrc:8`).
- `$ongsave = 'saveg'`: stores the save format version as four numbers (`saveg.qsrc:18-21`).
- `$ongload = 'loadg'`: reloads the build date, then runs `saveupdater`, which migrates variables in version steps (`loadg.qsrc`, `saveupdater.qsrc`). Each step is guarded by `if temp_current_save_version < 000NNNNN:` and ends by calling `gs 'saveg'` to stamp the new version.
- Mods get their own `_saveupdater` hook through `mod_system` ([gameplay-systems.md](../girl-life-analysis/gameplay-systems.md)).

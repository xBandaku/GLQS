# Girl Life: repository structure

Layout of `kevinsmartstfg/girl-life` at commit `83b164f`, how source files map to locations, and inconsistencies between files and the build manifest.

## 1. Top level

```text
girl-life/
├── glife.qproj               build manifest (QGen project XML)
├── locations/                1,429 .qsrc files + templates/ (2) + unused/ (3)
├── mods/                     Additional Adventures, Cherrypop Agency, Ibiza
├── isample_mod/              sample mod: locations/, Make_mod.bat/.sh, README.MD, isample.qproj
├── test/                     testframework.qsrc, two tests, test_file_template, testsuite-basic.qproj
├── tools/                    see below
├── MakeQSP.bat, build.sh     build menus/scripts
├── MakeTestQSP.bat           test build
├── Callvalidator.bat, Check_media.bat, checkpics.bat, buildHTML.bat/.sh, fix-src-case.sh, insanity.sh
├── .gitlab-ci.yml            CI: build_dev, release_dev, build_release, release_official, cleanup_old_dev
├── .editorconfig             LF, UTF-8, final newline, trim trailing spaces; .qsrc: tabs, width 4
├── keywords_en.xml, userDefineLang*.xml, glife-notepad++, Obsidian.xml   editor syntax files
└── changes from 0_8_X to 0_8_Y.txt, Name Updates.txt                    location rename history
```

`tools/` holds:
- **Compilers and converters.** `qsp-cli` for Linux, macOS and Windows, with C++ source in `qspcli-src/`; TXT2GAM binaries; `txtmerge.py`, `txtsplit.py`, `txtsplit3.py`.
- **Players.** `Player-original/`, `Player-video/` (with libvlc), `QSPgui/`, and Qqsp source in `Qqsp-Src/`.
- **Editors.** QGen 4 and QGen 5.
- **Validators.** `Parser/` (Chimrod's `qsp_parser`), `callvalidator.py`, `qsp_audit/`, `qsp-analyser/` (a C# analyzer), `check_consistency.py`, `check_missing_media.py`, `check_images2/3.py`.
- **Builders.** `build_debug.py`, `ci_build.py`, `testbuilder.py`.
- **Utilities.** AutoHotkey image scripts, a clothing editor (`ClothingEditor-Tauri`), `button-maker`, `generate_theme.py`, `organize_qsrc.py`, `syntax/` (VS Code, Atom, Notepad++).

## 2. File to location mapping

- **One location per file.** Each file starts with `# <name>` and ends with `--- <name> ---------------------------------`.
- **File names.** The name is the location name with `$` replaced by `_`. Example: `_attributes_allure_bikinis.qsrc` holds `# $attributes_allure_bikinis`; `_menu_settings.qsrc` holds `# $menu_settings`. The merge scripts apply the same replacement (`tools/txtmerge.py`, `iname.replace("$", "_")`).
- **Lookup.** The build tools look a file up at the folder path given by the manifest, then at `locations/<name>.qsrc`, then by a case-insensitive search of the whole tree (`txtmerge.py`, `resolve_qsrc_path`; the same in `qsp-cli.cpp:965-1025`). Subfolders are allowed but unused: all 1,429 files sit directly in `locations/`.

**Header and file name differ in case** (8 files). QSP location lookup ignores case, so the game works. A tool that maps names to files case-sensitively, such as a Linux file system lookup, could miss these; `fix-src-case.sh` exists for this kind of problem.

| File | Header |
|---|---|
| `eto_building.qsrc` | `# ETO_building` |
| `eto_hostel.qsrc` | `# ETO_hostel` |
| `eto_salon.qsrc` | `# ETO_salon` |
| `eto_village.qsrc` | `# ETO_village` |
| `pav_complexold.qsrc` | `# pav_complexOld` |
| `petkaEv.qsrc` | `# petkaev` |
| `serpent.qsrc` | `# Serpent` |
| `trainBimbo.qsrc` | `# trainbimbo` |

`$curloc` returns the header spelling, so code comparing `$curloc` to a literal must use the header's case.

## 3. The build manifest `glife.qproj`

```xml
<QGen-project version="4.0.0 beta 1">
  <Structure>
    <Location name="start"/>
    ...
    <Folder name="Deprecated">
      <Location name="$menu_face"/>
      ...
```

- 1,398 `<Location>` entries in 113 `<Folder>` groups. Folder names are organizational (Journal, System, Help, Stats, Homes, Functions, Sleep, Body, Clothing, Phone, Quests, School, Calendar System, one folder per major NPC, ...).
- Order matters. The merge concatenates locations in manifest order, and the first location becomes the game's start location. `start` is listed first.
- **Unregistered files.** 31 `.qsrc` files in `locations/` are not in the manifest and are silently left out of the build:

  `act_extras1`, `act_extras3`, `act_main1`, `act_minor1`, `actress`, `anastasia_escort`, `arousal_core`, `audition_reflections`, `audition_sex1`, `audition_sex2`, `audition_sex3`, `auditions`, `auditions_main1`, `auditions_minor1`, `costuming`, `costuming_outfits1`, `date_park`, `directors`, `komp_lonely_fans`, `movie_studio`, `music_performances`, `npc_280_init`, `pav_park_myles`, `pavlov_home`, `pushkin_ballet_res_street`, `sex_ev_A34`, `sex_ev_preg_talk`, `sex_ev_sex_talk_npc`, `sex_ev_talk2`, `uni_lessons_teaching1`, `vipclub`.

  Many are acting and audition content, probably work in progress. Calls into them from built code would raise "Location not found!" at run time; `callvalidator.py` and `qsp_audit` (`qproj-extra-file` rule) exist to catch this.
- No manifest entry lacks a file.

## 4. Location families

Grouped by name prefix (counts of files in `locations/`):

| Prefix | Files | Content |
|---|---|---|
| `_attributes_` (`$attributes_` locations) | 109 | Clothing item data, one location per brand and category |
| `pav_` | 61 | Pavlovsk (home town) places |
| `city_` | 58 | Saint Petersburg places |
| `sex_ev_` | 37 | Sex event engine |
| `uni_` | 33 | University |
| `gschool` | 32 | School |
| `npc` | 27 | NPC management, generation, relationships |
| `gad` | 26 | Gadukino (village) |
| `intro_` | 24 | New game introduction |
| `_menu_` (`$menu_` locations) | 24 | Settings and menus |
| `shop` | 22 | Shops |
| `pushkin` | 13 | Pushkin |
| `stat` | 9 | Status panel |
| `calendar` | 6 | Calendar system |
| `jobs` | 3 | Jobs v4 |
| other | 941 | NPC-specific stories, systems, events |

The region prefixes `pav_`, `city_`, `gad`, `pushkin` also drive `$region[1]` in `core_library`'s `setloc` handler (`locations/core_library.qsrc:29-37`).

## 5. Data locations

Some locations hold no screens, only data selected by a numeric argument. The clothing files are the largest example:

```qsp
# $attributes_allure_bikinis
if ARGS[0] = 1:
	CloQuality = 2
	CloStrength = 123750
	...
	$swimwear_description = 'A bikini set with a bandeau top and a brief bottom in the color salmon pink.'
elseif ARGS[0] = 2:
```

(`locations/_attributes_allure_bikinis.qsrc`, 1,560 lines). The dispatcher builds the location name and checks it exists before calling: `if loc('$attributes_<<$ARGS[0]>>'): gs '$attributes_<<$ARGS[0]>>', ARGS[1]` (`locations/clothing_attributes.qsrc:173`). The test is on numeric `ARGS[0]` without `$`, and items are numbered from 1.

## 6. Templates and unused code

- `locations/templates/location_template.qsrc` is the recommended screen layout:
  - `*clr & cla`;
  - `menu_off = 0`;
  - `gs 'core_library', 'setloc', '<loc>', '<arg>'`;
  - `gs 'stat'`;
  - an image line, text lines;
  - `act` lines that add minutes and `gt` elsewhere.
- `locations/templates/comment_template.qsrc` defines comment banner styles. It contains `if $ARGS[0]:`, a string condition that 5.7 rejects with a type mismatch unless the text is empty or numeric. The template is not built.
- `locations/unused/` holds three retired locations (`boilerroom`, `volAndGev`, `webcam_site`).

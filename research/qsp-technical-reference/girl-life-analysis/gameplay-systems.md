# Girl Life: gameplay systems

How Girl Life's main systems are built in QSP, at the level needed to extend or debug them. Each section names the locations involved and the QSP mechanisms they use. Files are under `locations/` at commit `83b164f`. GLSS-relevant systems (school, university, grades, money, the mod framework) get the most detail.

## 1. Startup and handler registration

`start` is the first location in `glife.qproj`, so the engine enters it with `GOTO` on a new game (`start.qsrc:4-36`). Its default handler:

1. **Resets state.** `killall` and `CLOSE ALL`.
2. **Sets display options.**
   - `usehtml = 1`;
   - `debug = 1`, which disables the save checksum;
   - hides panes (`showstat 0`, `showobjs 0`, `showinput 0`).
3. **Checks the player version.** Exits with an error screen if `qspver > '5.9.2'` (lines 12-18).
4. **Shows actions and sets fonts.** `showacts 1`, `disablescroll = 1`, `$fname = 'Tahoma'`, `fsize = 12`.
5. **Registers handlers.** `$ongload = 'loadg'`, `$ongsave = 'saveg'`, `$onnewloc = 'LOCA'`, `$onobjsel = 'onobjsel'`, `$counter = 'counter'`, `$usercom = 'inputProcessing'`.
6. **Initializes the clock.** `daystart = -1`, `totminut = -1`.
7. **Versions and builds.** `gs 'saveg'` stamps the save version and `gs 'addbuilddate'` sets `$builddate` from the location the build script appends.
8. **Moves on** with `gt 'start', 'start'` to the title screen.

The title screen offers Start (`gt 'begin', 'warning'`), Load (`opengame`), Quick Save load (`opengame 'quicksave.sav'`), a video test, the change log, mod management (`gt '$menu_settings', 'mods'`) and music toggles. A new game goes through `begin` (`warning`, `start`, `quick_start`, `real_character` ...) and the 24 `intro_*` locations.

## 2. Event hooks

| Hook | Location | What it does |
|---|---|---|
| `$ONNEWLOC` | `LOCA` | Optional trace; clears `cheatmenu` outside settings; `copyarr 'modARGS', 'ARGS'`; `gs 'mod_system', 'LOCA'` (all mod dispatchers); `gs 'LOCA_events'` (therapist reminder, incoming phone calls and texts) |
| `$COUNTER` | `counter` | Every tick (500 ms by default) counts down a notification timer and, when it expires, swaps or removes the notification text in `$stat_msg` and redraws the stats pane with `clr & pl`. When `music_loop = 1` it also runs `PLAY $track_loop, volume` |
| `$ONOBJSEL` | `onobjsel` | The debug panel in the objects pane: refresh, console, debug variables, time shifts. Ends with `unselect` |
| `$ONGSAVE` | `saveg` | Stamps `version_major`, `version_minor`, `version_revision`, `version_patch` |
| `$ONGLOAD` | `loadg` | Debug pane visibility, `gs 'addbuilddate'`, `gs 'saveupdater'`, debug trace flags off |
| `$USERCOM` | `inputProcessing` | Empty |

Because `$ONNEWLOC` runs after the destination's code ([execution-model.md](../official-documentation/execution-model.md)), mods see the finished screen. `LOCA_events` runs after the mods and can redirect with `gt 'therapist_reminder'`. `LOCA_events` skips everything when `menu_off = 1`, which marks event screens. Its end marker reads `--- LCOA_events ---`, a harmless typo because no tool checks the name in the end marker.

## 3. Time

**Variables.**
- `minut`, `hour`, `daystart` (day number since game start), `totminut` (total minutes);
- calendar values `day`, `month`, `year`, `week` (day of week, 1 = Monday per `shortgs` `dow`).

**Flow** (`time.qsrc:5-37`):
1. Code adds to `minut` and calls `gs 'time'`, directly or through `gs 'stat'`.
2. `time` recomputes `totminut`, then loops with a label.
3. Each 60 minutes becomes an hour and runs `gs 'hourly_events'`.
4. Each 24 hours becomes a day: it runs `gs 'time', 'update_date'` and `gs 'cikl'`.

**Hourly** (`hourly_events.qsrc`). Sleep recovery, intoxication decay, willpower regeneration, mood, sweat, fertility and drug updates, `traits` hourly. Includes nested `iif` arithmetic such as `pcs_stam += iif(pcs_sleep > 90, stammax/2, iif(...))`.

**Daily** (`cikl.qsrc`, 1,162 lines, 78 `gs` calls). New Year date, weekly reset, fame, phone statistics, porn studio schedule, job miss detection (`gs 'jobs', 'daily_check'`), relationships, school weekly grade update, university daily logic (`gs 'uni_lessons', 'cikl'`), NPC schedules, laundry, rent, game-over check and many quest-specific cycles.

**School absence counter.** On school days between 8:00 and 14:00, `hourly_events` adds one to `gschoolVars['absence_count']` once per day (`hourly_events.qsrc:340-342`); real attendance in `gschool_lessons` `morning` subtracts it again. GLSS mirrors this (see [GLSS](#9-what-glss-relies-on)).

## 4. Character stats and the status panel

- **Attributes and skills.** Variables use the `pcs_` prefix: `pcs_stren`, `pcs_agil`, `pcs_intel`, `pcs_chrsm`, `pcs_willpwr`, `pcs_energy`, `pcs_hydra`, `pcs_makeup` and others. `exp_gain` (`gs 'exp_gain', 'intel', amount`) and `exp_deg` raise and decay them.
- **Mood, willpower, traits.**
  - `mood`: `raise`, `lower`, `clamp`, `decay`, `status_effects`.
  - `willpower`: `calc`, `pay`, `difficulty`, and per-activity costs such as `chore`.
  - `traits`: 2,858 lines with `init`, `daily`, `hourly`, `level`.
- **Status panel.** `stat` (871 lines) recomputes derived values and runs `gs 'time'`. `stat_display` (2,106 lines) renders the panel into the stats window with `p`/`pl` and HTML. Alerts are queued with `stat_display_compute`.
- **Attribute checks.** `pcs_has_attr` answers questions such as `body_ass_flat` or `clothes_naked`, used as `func('pcs_has_attr', 'sex_...')` inside text.

## 5. Money

`money.qsrc` is the only sanctioned way to change cash and bank balances. Its header says "Use this to deduct money from the player instead of directly modifying money or karta".

| Handler | Use |
|---|---|
| `pay`, `earn`, `set` | Change balances. `pay` takes `'cash'`, `'bank'`, `'desk'` or `'both'` and applies price modifiers |
| `can_afford` | Returns 1 or 0 through `iif(..., 1, 0)`, safe to compare with `= 1` on any engine |
| `price`, `profit`, `base_price`, `base_profit` | Apply or invert difficulty modifiers |
| `string_price`, `format`, `format_balance` | Text for display |
| `debt_add`, `debt_pay`, `string_debt` | Debt |

Variables: `money` (cash), `karta` (bank), `stolmoney` (desk drawer), `bankDebtLimit`, `cfg_vars['allow_overdraft']`. `qsp_audit` has a `money-direct` rule that flags direct changes to these variables.

## 6. NPCs and relationships

- NPCs have string ids such as `'A69'`. Data lives in arrays keyed by id: `npc_rel['A69']`, `$npc_lovername[$npcID]`, `npc_throat['A14']`, `$npc_cum_pref[$npcID]`.
- `npc_relationship` changes relationship values through `modify`, `modify_exact`, `set` and `check`, and sets social group defaults. `qsp_audit` flags direct writes (`npc-rel-direct`).
- `npc` manages generated NPCs (`is_npcID`, `find_in_npcStat`, `copy_npcStat`, `update_hotcat`).
- Quest progress uses one keyed array per character: `katjaQW[...]`, `albinaQW`, `blackmailQW`.

## 7. School and university

These are the systems GLSS automates.

- **School day** (`gschool_lessons`). The `morning` handler records attendance once per day:
  - `gschoolVars['last_attendance'] = daystart`;
  - `gschoolVars['absence_count'] -= 1`;
  - adjustments to `missing_class`, `lernSkill`, `lernHome`;
  - then it shows special scenes or the hallway with actions `Go to first period`, `Skip first period` and break options (`gschool_lessons.qsrc:4-58`).

  `schedule` chooses each period's subject by weekday. `skip`, `short_break` and `grade_check` handle the other states.
- **Grades** (`grades.qsrc`, 554 lines):
  - `createclass`;
  - `attend_class` and `class_activity_attributes`, the calls GLSS replicates;
  - `homework`;
  - `calculate_grade` and `assign_grade_description`;
  - grade caps.

  Grades are stored per institution and subject in keyed arrays (`class[...]`).
- **University.** `uni_grounds`, `uni_lessons`, `uni_lessons1` to `uni_lessons4` (semester content), `uni_programs` (nursing and teaching studies, exam scheduling), electives. Variables include `university['student']`, `university['enrolled_in_semester']`, `university['semester_passed']`, `university['exam_week']`, `$university['enrolled_in']`, and `uni_period['first'|'second'|'third'|'exam']`, which records the day each period was attended.

## 8. Jobs, calendar, clothing, homes, themes

- **Jobs v4** (`jobs.qsrc`, 2,734 lines). The header documents the whole API: employment (`set_employed`, `set_fired` ...), work tracking (`clock`, `clock_in`, `clock_out`, `daily_check`), pay (`paycheck`, `bonus_pay`), schedule queries (`is_work_day`, `is_work_time`, `get_shift_for_day`), and booking mode. Job definitions are in `jobs_list.qsrc`; gigs in `jobs_gigs`.
- **Calendar** (`calendar*.qsrc`, 6 files, about 4,700 lines). Event definitions in `calendar_list`, queries, rendering, scheduling. Jobs create calendar events.
- **Clothing.** 109 `$attributes_*` data locations. `clothing_attributes`, `shoe_attributes`, `coat_attributes`, `purse_attributes` and `piercing_attributes` dispatch to them by computed name. `wardrobe` and `clothing` manage what is worn. `outfit.qsrc` is a specification inside a block comment and contains no live code.
- **Homes.** `homes_properties` (`has_access`, rent progression) and per-home folders in the manifest.
- **Themes.** `themes.qsrc` (6,441 lines) defines color themes (`theme_hex[...]`, `rgb(...)`), menu rendering and the `wrap` helpers. `wrap.qsrc` is a separate short location "to reduce call length".

## 9. What GLSS relies on

GLSS (this repository's mod) depends on these Girl Life behaviors, all confirmed in the source:

| GLSS assumption | Girl Life source |
|---|---|
| `mod_glss` runs on every location change after the destination's code | `LOCA.qsrc:27-28`, `mod_system.qsrc:4-10, 81-103` |
| `$curloc` is `gschool_lessons`, `uni_grounds`, `uni_lessons` with lowercase headers | headers of those files |
| The hallway actions are named `Go to first period` and `Go to next class` | `gschool_lessons.qsrc:49, 63, 201` |
| University class actions start with `Go to your ` | `uni_programs.qsrc:402` onward, added through `uni_lessons` `schedule` (`uni_lessons.qsrc:101-110`). `uni_grounds.qsrc:128` also adds `Go to your room` for every student, so GLSS removes that action, and elective actions when elective automation is off, before matching the prefix ([implementation-observations.md](implementation-observations.md)) |
| Attendance bookkeeping in `morning` | `gschool_lessons.qsrc:12-26` |
| `minut += n` then `gs 'stat'` normalizes time | `stat.qsrc:592` |
| `func('money', 'can_afford', 50) = 1` is valid | `money.qsrc:246-310` |
| `gs 'food', 'bagged_lunch_stats'`, `'medium_meal_stats'` exist | `food.qsrc` (the GLSS README says these are the silent stat handlers) |
| `$menu_settings` `mods` page and the `_setup`, `_options`, `_readme`, `_saveupdater` hooks | `mod_system.qsrc`, `_menu_settings.qsrc` |

The mod framework itself is described next.

## 10. Mod framework (`mod_system.qsrc`)

| Handler | Behavior |
|---|---|
| `LOCA` | Calls every installed mod's dispatcher `mod_<name>` with the navigation arguments; prints a warning if a dispatcher is missing |
| `sleep` | Same, with `$modARGS` from the sleep trigger and no warning |
| `stat`, `stat_display`, `func`, `arousal`, `outfit` | Disabled: each starts with `exit` |
| `core_loop` | Label loop over `$mod_name[]`. Builds `mod_<name><suffix>` and calls it with nine `iif(modARGS[i]=0, $modARGS[i], modARGS[i])` arguments, which pass the string or the number form of each argument |
| `add_mod` | `inclib 'mod/<name>.qsp'` (`addqst` on 5.7), calls `mod_<name>_setup`, which must fill `$mod_info[0..4]` (name, version, author, description, options link), and records the mod |
| `delete_mod` | Calls `mod_<name>_onremove`, frees all libraries, then includes the remaining mods again |
| `update_all_mods` | Frees and reloads every mod, rerunning setup |
| `saveupdater` | For each mod: `_setup` with `'saveupdater'`, refresh metadata, then `mod_<name>_saveupdater` |

Consequences of the engine rules ([input-output-and-persistence.md](../official-documentation/input-output-and-persistence.md)):
- A mod cannot replace a core location, because `INCLIB` skips existing names.
- Mods stay loaded across save and load, because included files are saved and reloaded before `$ONGLOAD`.
- Removing one mod reloads all the others, which reruns their `_setup` code.

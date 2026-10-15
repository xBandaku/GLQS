# Girl Life: annotated code examples

Short excerpts from Girl Life (`locations/` at commit `83b164f`) and one from GLSS, each with the QSP rules that make it work. Line numbers are those of the excerpt's first and last lines. Code fences are labeled `qsp`; most Markdown renderers have no highlighter for it and show plain text.

The rules cited here are explained in [../official-documentation/](../official-documentation/documentation-index.md); the patterns in [scripting-patterns.md](scripting-patterns.md).

## 1. A handler that returns a value

`shortgs.qsrc:100-103`

```qsp
if $ARGS[0] = 'sqrt':
	result = func('math', 'int_sqrt', ARGS[1])
	exit
end
```

- `ARGS[1]` is the numeric form of the caller's second argument. The caller writes `func('shortgs', 'sqrt', 81)`.
- The inner `func` call cannot overwrite this handler's `RESULT`. On 5.8+ every call has its own `RESULT`; on 5.7 `FUNC` saves and restores the caller's value, although `GOSUB` does not ([variables-and-data-types.md](../official-documentation/variables-and-data-types.md)).
- `exit` stops the location here. Without it, the engine would go on to test every later `if $ARGS[0] = ...` line.

## 2. The game's entry point

`start.qsrc:4-36` (abridged)

```qsp
if $ARGS[0] = '':
	killall
	CLOSE ALL
	usehtml = 1
	debug = 1
	...
	if qspver > '5.9.2':
		showacts 0
		'<center><font size="+3" color="red"><b>RUNTIME VERSION MISMATCH</b></font><br>'
		...
		exit
	end
	showacts 1
	$ongload = 'loadg'
	$ongsave = 'saveg'
	$onnewloc = 'LOCA'
	$onobjsel = 'onobjsel'
	$counter = 'counter'
	$usercom = 'inputProcessing'
	...
	gt 'start', 'start'
end
```

- `qspver > '5.9.2'` compares strings. `QSPVER` returns text such as `5.7.0` or `5.9.5 (classic)`, and string comparison is character by character. `'5.9.5 (classic)' > '5.9.2'` is true; `'5.7.0' > '5.9.2'` is false. A future `5.10.0` would compare lower than `5.9.2` and pass the check.
- `qspver` without `$` is the same function as `$qspver` on both engines and returns text. In 5.7 both spellings are registered for one operation whose result is a string (`legacy: src/mathops.c:264-265, 574-575`).
- `debug = 1` disables the save file identity check, so saves from other builds load ([input-output-and-persistence.md](../official-documentation/input-output-and-persistence.md)).
- `gt 'start', 'start'` ends the default handler. `GOTO` terminates everything else running, so nothing after it would execute.

## 3. The `$ONNEWLOC` handler and the mod hook

`LOCA.qsrc:27-30`

```qsp
copyarr 'modARGS', 'ARGS'
gs 'mod_system', 'LOCA'

gs 'LOCA_events'
```

- `$ONNEWLOC` runs after the new location's code, with the same `ARGS` the `GOTO` passed. `copyarr` saves them into the global `modARGS` so the mod loop can forward them.
- The handler runs inside the same event as the `GOTO`. If a mod or `LOCA_events` calls `gt`, that new `GOTO` replaces the screen and triggers `LOCA` again for the new location.

## 4. A label loop that forwards arguments of either type

`mod_system.qsrc:81-103` (abridged)

```qsp
if $ARGS[0] = 'core_loop':
	if arrsize('$mod_name') <= 0: exit

	mod_i = 0
	:mod_exec
		if $mod_name[mod_i] ! '':
			$mod_su_name = 'mod_<<$mod_name[mod_i]>><<$mod_system_loc>>'
			if loc($mod_su_name):
				gs $mod_su_name, iif(modARGS[0]=0, $modARGS[0], modARGS[0]), ...
			elseif mod_warning:
				$func('wrap', 'v_neg', 'WARNING: <<$mod_su_name>> is not found!')
			end
		end
		mod_i += 1
	if mod_i < arrsize('$mod_name'): jump 'mod_exec'

	killvar 'mod_i'
	...
	exit
end
```

- **Loop.** `:mod_exec` and `jump` replace `LOOP`, which 5.7 lacks. The indentation under the label is cosmetic.
- **Existence check.** `loc(name)` avoids a "location not found" error for mods without a dispatcher.
- **Argument forwarding.** `iif(modARGS[0]=0, $modARGS[0], modARGS[0])` forwards a string argument as a string and a number as a number.
  - On 5.7 each element holds both a number and a string. A string argument leaves the number at 0, so `iif` picks the string.
  - On 5.8 to 5.9.5 an element holds one value. `modARGS[0]` of a string element reads as 0 and `$modARGS[0]` of a number element reads as `''`, so the same expression picks whichever form is set.
  - On master, `modARGS[0]` returns a string element unchanged. The comparison with 0 is then usually false and `iif` returns that same string, so the forwarded value is still right.
  - A numeric argument that equals 0 is forwarded as the string `''`. Code receiving it must not rely on the type of a zero argument.
- **Warning output.** `$func(...)` alone on a line is an implicit output statement: the returned text is printed to the main window.

## 5. Version-dependent statements

`mod_system.qsrc:140-149`

```qsp
if $ARGS[0] = 'add_mod':
	if $ARGS[1] = '': exit

	if $qspver < '5.8.0':
		addqst 'mod/<<$ARGS[1]>>.qsp'
	else
		inclib 'mod/<<$ARGS[1]>>.qsp'
	end
	$mod_temp = 'mod_<<$ARGS[1]>>_setup'
	if loc($mod_temp): gs $mod_temp
```

- `addqst` exists only in 5.7 and `inclib` only in 5.8+. Each engine reports an unknown statement only when it reaches the line, so the branch not taken never errors.
- Included locations are added only if their names are new. A mod cannot override a core location this way.

## 6. Time normalization with a jump into another handler

`time.qsrc:13-31` and `40-50`

```qsp
	if totminut <> prevtotmin:
		:time_time_loop
			time_temp_jump_flag = 0
			if minut >= 60:
				hour += 1
				minut -= 60
				gs 'hourly_events'
				time_temp_jump_flag = 1
			end
			if hour >= 24:
				hour -= 24
				daystart += 1
				gs 'time', 'update_date'
				gs 'cikl'
				time_temp_jump_flag = 1
			end
		if time_temp_jump_flag = 1: jump 'time_time_loop'
...
if $ARGS[0] = 'time_cheat_fix':
	if minut < 0:
		hour -= 1
		minut += 60
		jump 'time_time_loop'
	end
```

- Labels belong to the whole location, so `time_cheat_fix` can jump into the loop inside the default handler.
- `hourly_events` and `cikl` run once per hour and day crossed. Adding 300 minutes runs `hourly_events` five times.
- Lines 9-11 keep the previous total in `prevtotmin`. `LOCA_events` later checks for phone calls and texts in the span from `prevtotmin` to `totminut` (`LOCA_events.qsrc`), so any extra `gs 'time'` call between two screens narrows that span to the time added since that call.

## 7. Computed variable names

`array.qsrc:11-38` (numeric branch)

```qsp
if $ARGS[0] = 'get_me_index':
	$test = '<<$ARGS[1]>>[''<<$ARGS[2]>>'']'
	testas0 = arrsize($ARGS[1])
	...
		temp_arrayVars['backup'] = dyneval('result = <<$test>>')
		dynamic '<<$test>> = -2147483647'
		testas1 = arrsize('<<$ARGS[1]>>')
		if testas0 = testas1:
			result = arrpos($ARGS[1], -2147483647)
			dynamic "<<$test>> = temp_arrayVars['backup']"
		else
			result = -1
			killvar $ARGS[1], testas0
		end
```

- The handler finds the numeric index of a string key. It writes a sentinel through that key, searches for the sentinel with `ARRPOS`, then restores the old value.
- If the array grew, the key did not exist. The new element is removed and the result is -1.
- `''<<$ARGS[2]>>''` inside the outer string becomes `'key'` in the generated code. The doubled apostrophes are the only escape QSP has.
- `ARRPOS` with two arguments has the same meaning on 5.7 and 5.8+. The three-argument form differs: the start position comes first on 5.7 (`legacy: src/variables.c:542-552`) and last on 5.8+.
- The header comment notes the sentinel was changed from -2147483648 to -2147483647 in February 2026. The comment gives no reason.
- 5.9.1's `ARRITEM` and `ARRPOS` with string keys would make this shorter, but are not available on 5.7.

## 8. Links and nested actions

`core_library.qsrc:85` and `89-101`

```qsp
'There is a shower, toilet, sink, and a <a href="exec:gt ''mirror'',''start''">mirror</a> where you can ' + iif(pcs_hairbsh = 0, '<a href="exec:gt ''mirror'',''brush''">brush</a>', 'brush') + ' your hair.'
...
act 'Take a shower':
	*clr & cla
	pcs_hairbsh = 0
	pcs_makeup = 1
	minut += 10
	gs 'mood', 'raise', 'small'
	...
	gs 'stat'
	'You grab a quick shower, ...'

	act 'Continue' : gt $loc, $loc_arg
end
```

- `exec:` links run QSP code when clicked. The code sits inside an HTML attribute inside a QSP string, so it uses doubled apostrophes.
- On 5.7, `iif` evaluates both branches. Both are string literals here, so there is no side effect.
- The inner `act 'Continue'` is created only when the player clicks the outer action, after `cla` cleared the list.

## 9. Location state for returning

`core_library.qsrc:10-38` (abridged)

```qsp
if $ARGS[0] = 'setloc':
	$prevloc = $loc
	$loc = $ARGS[1]
	$menu_loc = $ARGS[1]
	...
	killvar 'locclass'		& !! persistance of locclass is unwanted
	...
	if $mid($loc, 1, 4) = 'pav_':
		$region[1] = 'pav'
	elseif $mid($loc, 1, 5) = 'city_':
		$region[1] = 'city'
	...
```

- `& !! comment` ends a statement with a comment on the same line. The `!!` starts a comment statement, which runs to the end of the line.
- `$MID` is 1-based.
- Screens call `gs 'core_library', 'setloc', '<loc>', '<arg>'`; event code later returns with `gt $loc, $loc_arg`.

## 10. A boolean that means the same on every engine

`money.qsrc:287-293`

```qsp
if $ARGS[0] = '_can_afford_inner':
	!! Internal function to check if the player can afford something. Modifiers applied in the wrapper function 'can_afford'.
	!! ARGS[1] = cost
	!! $ARGS[2] = 'cash', 'bank', 'desk', or 'both', default is 'both'
	!! $ARGS[2] = 'desk' checks cash + desk drawer
	if $ARGS[2] = 'cash':
		result = iif(money >= ARGS[1], 1, 0)
```

- A comparison yields -1 on 5.7 and 1 on 5.8+. `iif(..., 1, 0)` makes the result 1 on both, so callers can write `= 1`.
- The comment line contains `'cash', 'bank', ...` with balanced apostrophes. An odd count would open a string and swallow the next lines ([language-syntax.md](../official-documentation/language-syntax.md)).

## 11. A data location

`_attributes_allure_bikinis.qsrc` (first lines) and `clothing_attributes.qsrc:170-176`

```qsp
# $attributes_allure_bikinis
if ARGS[0] = 1:
	CloQuality = 2
	CloStrength = 123750
	...
elseif ARGS[0] = 2:
```

```qsp
gs 'clothing', 'reset_CloVars'

if loc('$attributes_<<$ARGS[0]>>'): gs '$attributes_<<$ARGS[0]>>', ARGS[1]
!! gs 'mod_system', 'outfit', 'clothing_attributes', $ARGS[0], ARGS[1]

if CloQuality = 0: exit
```

- The location name starts with `$`. Names are plain text to the engine; the `$` has no type meaning there. The file name replaces it with `_`.
- The dispatcher resets the output globals, calls the data location, and treats `CloQuality = 0` as "item not found".
- The commented-out line is the disabled mod hook for outfits ([gameplay-systems.md](gameplay-systems.md)).

## 12. A save migration

`saveupdater.qsrc:15` and `43-50`

```qsp
temp_current_save_version = ((100 * version_major + version_minor) * 100 + version_revision) * 100 + version_patch
...
if temp_current_save_version < 00080403:
	!! Updating the variables for the Katja Quest line.

	if meynoldQW = 1 or meynoldQW = 2:
		katjaQW['QWstage'] = meynoldQW
		killvar 'meynoldQW'
	end
```

- `version_*` come from the loaded save, because `saveg` stored them at save time. The file ends with `gs 'saveg'` (`saveupdater.qsrc:6587`), which stamps the current version so the migrations do not run again.
- `00080403` is the number 80403. Leading zeros are allowed in number literals.
- Loading does not re-run the current location, so migrations change variables but not the screen on display.

## 13. Truth constants in the test framework

`test/testframework.qsrc:5-6`

```qsp
_TRUE = (0 ! 1)
_FALSE = (0 = 1)
```

The values are the engine's own truth values: -1 and 0 on 5.7, 1 and 0 on 5.8+. Tests compare against `_TRUE` instead of a literal.

## 14. A mod dispatcher (GLSS)

`glss/locations/mod_glss.qsrc:31-37` in this repository

```qsp
if glss['auto_school'] = 1 and $curloc = 'gschool_lessons' and hour < 14:
	if instr($curacts, 'Go to first period') > 0:
		act 'GLSS: Attend the whole school day automatically': school_period = 0 & gt 'mod_glss_functions', 'auto_day'
	elseif instr($curacts, 'Go to next class') > 0:
		act 'GLSS: Attend the rest of the school day automatically': gt 'mod_glss_functions', 'auto_day'
	end
end
```

- `$CURACTS` returns the current actions as QSP code. On 5.8+ the action bodies come back upper-cased, but each name is written as a quoted string in its original case (`engine: qsp/actions.c:126-128`), so the `INSTR` search works on both engines.
- `INSTR` with two arguments has the same meaning on 5.7 and 5.8+.
- The `act` is added after Girl Life built the screen, because `mod_glss` runs from `$ONNEWLOC`. It appears last in the action list.

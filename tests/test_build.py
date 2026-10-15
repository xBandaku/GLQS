import io
import re
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import build
import build_support


def assemble_real_tree():
    standalone, shared = build_support.collect_fragments()
    build_support.validate_fragment_contract(standalone, shared)
    return build_support.assemble(standalone, shared)


class BuildValidationTests(unittest.TestCase):
    def test_real_source_tree_passes_every_check(self):
        text = assemble_real_tree()
        with redirect_stdout(io.StringIO()) as out:
            build_support.validate_assembled(text)
            ok = build_support.run_lints(text)
        self.assertTrue(ok, out.getvalue())

        catalog = (build_support.SRC_DIR / build_support.CLOTHING_CATALOG_FILE).read_text(
            encoding="utf-8"
        )
        picker_actions = [
            line for line in text.splitlines()
            if line.lstrip().startswith("act ")
            and "gt 'mod_GLQS_main', 'item_picker'" in line
        ]
        catalog_rows = re.findall(
            r"\$glqs_cc\[\]\s*=\s*'[^']+'", catalog
        )
        self.assertEqual(len(picker_actions), len(catalog_rows))

    def test_non_ascii_source_is_written_and_reported(self):
        text = assemble_real_tree() + "!! smart \u2014 punctuation\n"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "GLQS.qsps"
            with mock.patch.multiple(
                build_support,
                BUILD_DIR=Path(tmp),
                OUTPUT_QSPS=output,
                collect_fragments=mock.Mock(return_value=([], [])),
                validate_fragment_contract=mock.Mock(),
                assemble=mock.Mock(return_value=text),
            ), redirect_stdout(io.StringIO()) as out:
                with self.assertRaises(SystemExit) as exit_info:
                    build.main()
            self.assertEqual(exit_info.exception.code, 1)
            self.assertTrue(output.exists())
        self.assertIn("[LINT] Non-ASCII", out.getvalue())

    def test_route_calls_support_qsp_escaped_quotes(self):
        text = (
            "gs ''mod_GLQS_main'', ''item_grant''\n"
            "gt 'mod_GLQS_main', 'start'\n"
            "$x = $func('mod_GLQS_main', 'rel_actions', $k, 1)\n"
        )
        self.assertEqual(
            build_support.extract_route_calls(text),
            {"item_grant", "start", "rel_actions"},
        )

    def test_missing_route_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            build_support.validate_route_coverage(
                "if $ARGS[0] = 'start':\n"
                "gt 'mod_GLQS_main', 'missing'\n"
            )

    def test_duplicate_simple_route_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "start"):
            build_support.validate_route_definitions(
                "if $ARGS[0] = 'start':\nend\n"
                "if $ARGS[0] = 'start':\nend\n"
            )

    def test_profile_signature_tracks_layout_but_ignores_display_labels(self):
        signature = build_support.profile_schema_signature()
        read_text = Path.read_text

        def changed_label(path, *args, **kwargs):
            text = read_text(path, *args, **kwargs)
            return text.replace('Strength', 'Physical strength') if path.name == '07_stats_data.qsps' else text

        with mock.patch.object(Path, 'read_text', changed_label):
            self.assertEqual(build_support.profile_schema_signature(), signature)

        def changed_order(path, *args, **kwargs):
            text = read_text(path, *args, **kwargs)
            if path.name == '07_stats_data.qsps':
                rows = text.splitlines()
                first = next(i for i, row in enumerate(rows) if '|stren|' in row)
                second = next(i for i, row in enumerate(rows) if '|agil|' in row)
                rows[first], rows[second] = rows[second], rows[first]
                return '\n'.join(rows)
            return text

        with mock.patch.object(Path, 'read_text', changed_order):
            self.assertNotEqual(build_support.profile_schema_signature(), signature)

    def test_navigation_template_requires_one_marker_pair(self):
        with self.assertRaisesRegex(ValueError, "marker pair"):
            build_support.validate_navigation_template(
                "$glqs_nb[] = 'start|Index'\n"
            )

    def test_navigation_registry_must_resolve(self):
        text = (
            "$glqs_nb[] = 'clothing_menu|Clothing'\n"
            "if $glqs_current <> 'clothing_menu': act 'Clothing': "
            "gt 'mod_GLQS_main', 'clothing_menu'\n"
        )
        with self.assertRaisesRegex(ValueError, "no route definitions"):
            build_support.validate_navigation_registry(text, set())

    def test_recurrent_data_rows_are_checked(self):
        good = (
            "$glqs_rc[] = 'bulk|willpower|1|Willpower cost always zero'\n"
            "$glqs_rc[] = 'bulk|no_dream_chance|100|No dream chance'\n"
            "$glqs_rc[] = 'special|drugs_immune|addict|Never get addicted'\n"
        )
        reference = "if $ARGS[0] = 'addict':\nend\n"
        build_support.validate_recurrent_data(good, reference)
        with self.assertRaisesRegex(ValueError, "no 'Vibrator' handler"):
            build_support.validate_recurrent_data(
                "$glqs_rc[] = 'special|sleep_vib|Vibrator|Vibrator'\n", reference
            )
        with self.assertRaisesRegex(ValueError, "on-value"):
            build_support.validate_recurrent_data("$glqs_rc[] = 'bulk|mood|yes|Mood'\n")
        with self.assertRaisesRegex(ValueError, "duplicate keys mood"):
            build_support.validate_recurrent_data(
                "$glqs_rc[] = 'bulk|mood|1|Mood'\n$glqs_rc[] = 'bulk|mood|1|Mood'\n"
            )

    def test_recurrent_individual_toggle_needs_displayed_state(self):
        def menu(table):
            return (
                "if $ARGS[0] = 'recurrent':\n"
                f"$glqs_tbl2 = \"{table}\"\n"
                "if $ARGS[0] = 'recurrent_set':\n"
            )

        build_support.validate_recurrent_toggle_contract(
            menu("cheatVars[''std''] = iif(cheatVars[''std''], 0, 1)")
        )
        with self.assertRaisesRegex(ValueError, "std"):
            build_support.validate_recurrent_toggle_contract(
                menu("cheatVars[''std''] = iif(1, 0, 1)")
            )

    def test_consumable_metadata_rejects_unknown_kind_and_duplicates(self):
        def row(kind, key):
            return f"$glqs_con[] = '{kind}|Cat|Label|{key}'\n"

        build_support.validate_consumable_metadata(row("stack", "razor") + row("single", "comb"))
        with self.assertRaisesRegex(ValueError, "unknown roles"):
            build_support.validate_consumable_metadata(row("bulk", "razor"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_support.validate_consumable_metadata(row("stack", "razor") + row("single", "razor"))

    def test_job_ids_match_reference_source(self):
        if not build_support.REFERENCE_JOBS_LIST.exists():
            self.skipTest("nightly reference source not present")
        build_support.validate_job_ids(
            (build_support.SRC_DIR / build_support.JOBS_DATA_FILE).read_text(encoding="utf-8"),
            build_support.REFERENCE_JOBS_LIST.read_text(encoding="utf-8"),
        )

    def test_job_ids_reject_mismatch(self):
        with self.assertRaisesRegex(ValueError, "Job ID mismatch"):
            build_support.validate_job_ids(
                "$glqs_jb[] = 'city_office_secretary|Office Secretary'\n",
                "if $ARGS[0] = 'city_office_cleaner':\nend\n",
            )


class LintTests(unittest.TestCase):
    def test_apostrophe_in_comment(self):
        self.assertEqual(build_support.lint_apostrophes_in_comments("!! the players room\n"), [])
        self.assertEqual(build_support.lint_apostrophes_in_comments("!! it''s escaped\n"), [])
        self.assertTrue(build_support.lint_apostrophes_in_comments("\t!! the player's room\n"))

    def test_non_ascii(self):
        self.assertEqual(build_support.lint_non_ascii("\t'plain - text'\n"), [])
        self.assertTrue(build_support.lint_non_ascii("!! smart \u2014 punctuation"))

    def test_unbalanced_template_markers(self):
        self.assertEqual(build_support.lint_unbalanced_template_markers("'a <<b>> c'\n"), [])
        self.assertTrue(
            build_support.lint_unbalanced_template_markers("'foo<<bar[' + $k + ']>>'\n")
        )

    def test_empty_template_markers(self):
        self.assertEqual(build_support.lint_empty_template_markers("'<<x>>'\n"), [])
        self.assertTrue(build_support.lint_empty_template_markers("'<< >>'\n"))

    def test_unexpanded_markers(self):
        filled = "\t!! GLQS_X_BEGIN\n\tact 'A': gt 'a'\n\t!! GLQS_X_END\n"
        empty = "\t!! GLQS_X_BEGIN\n\t!! GLQS_X_END\n"
        self.assertEqual(build_support.lint_unexpanded_markers(filled), [])
        self.assertEqual(build_support.lint_unexpanded_markers(empty), [(1, "GLQS_X")])

    def test_numeric_variable_from_string_arg_slot(self):
        lint = build_support.lint_numeric_arg_from_string_slot
        for line in ("\tidx = $ARGS[3]", "\tIdx = $ARGS[3]", "\tlocal idx = $ARGS[3]"):
            with self.subTest(line=line):
                self.assertTrue(lint(line))
        for line in ("\t$idx = $ARGS[3]", "\tidx = ARGS[3]", "\tidx = val($ARGS[3])"):
            with self.subTest(line=line):
                self.assertEqual(lint(line), [])

    def test_version_mismatch(self):
        mod_info = "$mod_info[1] = '03700'\n"
        self.assertIsNone(
            build_support.lint_version_mismatch(mod_info + "'<b>Version 0.37.0 - Current</b>'\n")
        )
        self.assertEqual(
            build_support.lint_version_mismatch(mod_info + "'<b>Version 0.37.1 - Current</b>'\n"),
            ("0.37.0", "0.37.1"),
        )
        self.assertEqual(
            build_support.lint_version_mismatch(mod_info),
            ("0.37.0", "not found"),
        )

    def test_block_balance(self):
        self.assertEqual(build_support.lint_block_balance("if x:\n\tact 'A':\n\tend\nend\n")[0], 0)
        self.assertEqual(build_support.lint_block_balance("if x:\n")[0], 1)

    def test_extra_end_cannot_cancel_an_unclosed_block(self):
        for text in ("end\nif x:\n", "end\nif x:\nend\nif y:\n"):
            with self.subTest(text=text):
                self.assertTrue(build_support._block_balance_hits(text))


class QspRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules = build_support.BUILD_DIR / "tooling" / "node_modules"
        engine = cls.modules / "@qsp" / "wasm-engine" / "dist" / "wasm-engine.modern.js"
        converters = cls.modules / "@qsp" / "converters" / "dist" / "index.modern.js"
        if not shutil.which("node") or not engine.exists() or not converters.exists():
            raise unittest.SkipTest("QSP runtime tests need Node, @qsp/wasm-engine and @qsp/converters in build/tooling")
        for name in ("lover", "pain", "math", "shortgs", "money", "cheatmenu_din", "core_library"):
            if not (build_support.REFERENCE_LOCATIONS / f"{name}.qsrc").exists():
                raise unittest.SkipTest("QSP runtime tests need the pinned nightly reference")
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.source = Path(cls.temp.name) / "GLQS.qsps"
        cls.source.write_text(assemble_real_tree(), encoding="utf-8")

    def run_qsp(self, assertions, extra_locations=()):
        # Keep relationship bookkeeping and pain formulas real; isolate NPC
        # descriptions, phone schedules and rendering from the full game.
        harness = r"""
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const [source, modules, upstream, extraLocations] = process.argv.slice(1);
const pkg = (name, file) => path.join(modules, '@qsp', name, 'dist', file);
const { initQspEngine } = await import(pathToFileURL(pkg('wasm-engine', 'wasm-engine.modern.js')));
const { readQsps, writeQsp } = await import(pathToFileURL(pkg('converters', 'index.modern.js')));
const fixtures = `# test_start
--- test_start ---
# stat
--- stat ---
# themes
--- themes ---
# npcStat
$npcID = $ARGS[0]
--- npcStat ---
# telefon
--- telefon ---
# lover_call
--- lover_call ---
# npc_relationship
if $ARGS[0] = 'set': npc_rel[$ARGS[1]] = ARGS[2]
--- npc_relationship ---
# drugs
--- drugs ---
# body
--- body ---
# archetypes
test_archetype_updates += 1
--- archetypes ---
# washer
test_washes += 1
--- washer ---
`;
const real = ['lover', 'pain', 'math', 'shortgs', 'money', 'cheatmenu_din', 'core_library', ...extraLocations.split(',').filter(Boolean)].map(name =>
    fs.readFileSync(path.join(upstream, `${name}.qsrc`), 'utf8')).join('\n');
const binary = writeQsp(readQsps(fixtures + fs.readFileSync(source, 'utf8') + real));
const wasm = fs.readFileSync(pkg('wasm-engine', 'qsp-engine.wasm'));
const api = await initQspEngine(wasm.buffer.slice(wasm.byteOffset, wasm.byteOffset + wasm.length));
let actions = [];
const errors = [];
const inputs = [];
const messages = [];
let mainText = '';
api.on('actions_changed', value => { actions = value; });
api.on('main_changed', value => { mainText = value; });
api.on('input', (prompt, respond) => {
    assert.ok(inputs.length, `Unexpected input: ${prompt}`);
    respond(inputs.shift());
});
api.on('msg', (text, closed) => { messages.push(text); closed(); });
api.on('error', error => { errors.push(`${error.description} at ${error.location}:${error.line}`); });
const exec = code => { api.execCode(code); assert.deepEqual(errors, [], code); };
const keyed = (name, key) => api.readVariableByKey(name, key);
const click = name => {
    const index = actions.findIndex(action => action.name === name);
    assert.notEqual(index, -1, `Missing action: ${name}`);
    api.selectAction(index);
    api.execSelectedAction();
    assert.deepEqual(errors, [], name);
};
const link = label => {
    const matches = [...mainText.matchAll(/href="exec: ([^"]*)">([^<]*)<\/a>/g)];
    const match = matches.find(entry => entry[2] === label);
    assert.ok(match, `Missing link: ${label}`);
    exec(match[1].replaceAll('&amp;', '&'));
};
const dating = () => exec("killall & $lover[0] = 'A1' & $npc_rel_type['A1'] = 'dating' & stat['dating_current'] = 1 & stat['total_lovers_current'] = 1 & gt 'mod_GLQS_main', 'rel_status', 'A1'");
api.openGame(binary, true);
assert.deepEqual(errors, []);
"""
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", harness + assertions,
             str(self.source), str(self.modules), str(build_support.REFERENCE_LOCATIONS),
             ",".join(extra_locations)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_ending_dating_updates_counts_without_accumulating(self):
        self.run_qsp(r"""
dating();
for (let repeat = 0; repeat < 3; repeat++) {
    click('Clear / End Relationship');
    assert.equal(keyed('$npc_rel_type', 'A1'), 'ex-dating');
    assert.equal(keyed('stat', 'dating_current'), 0);
    assert.equal(keyed('stat', 'total_lovers_current'), 0);
    assert.equal(actions.some(action => action.name === 'Clear / End Relationship'), false);
    click('Set to Dating');
    assert.equal(keyed('stat', 'dating_current'), 1);
    assert.equal(keyed('stat', 'total_lovers_current'), 1);
}
""")

    def test_changing_dating_keeps_one_current_relationship(self):
        self.run_qsp(r"""
for (const [label, type, counter] of [
    ['Boyfriend', 'boyfriend', 'boyfriends_current'],
    ['Girlfriend', 'girlfriend', 'girlfriends_current'],
    ['Fuckbuddy', 'fuckbuddy', 'fuckbuddies_current'],
    ['Sugar Daddy', 'sugar_daddy', 'sugardaddies_current'],
]) {
    dating();
    click(`Set to ${label}`);
    assert.equal(keyed('$npc_rel_type', 'A1'), type);
    assert.equal(keyed('stat', 'dating_current'), 0, label);
    assert.equal(keyed('stat', counter), 1, label);
    assert.equal(keyed('stat', 'total_lovers_current'), 1, label);
    click('Clear / End Relationship');
    assert.equal(keyed('stat', counter), 0, label);
    assert.equal(keyed('stat', 'total_lovers_current'), 0, label);
}
""")

    def test_clear_all_pain_clears_non_array_sources(self):
        self.run_qsp(r"""
for (const causes of ["vgape = 5", "agape = 5", "spanked = 2", "pain['ribs'] = 8 & vgape = 3 & agape = 4 & spanked = 1"]) {
    exec(`killall & gs 'pain' & ${causes} & gs 'pain', 'calc' & gt 'mod_GLQS_main', 'lifestyle_menu'`);
    assert.ok(keyed('pain', 'total') > 0, causes);
    click('Clear All Pain');
    assert.equal(keyed('pain', 'total'), 0, causes);
    assert.equal(keyed('pain', 'damage'), 0, causes);
    exec("gs 'pain', 'calc'");
    assert.equal(keyed('pain', 'total'), 0, causes);
}
""")

    def test_marrying_a_date_replaces_the_relationship_count(self):
        self.run_qsp(r"""
for (const [gender, type, counter, spouse] of [
    [1, 'husband', 'husbands_current', '$husID'],
    [2, 'wife', 'wifes_current', '$wifID'],
]) {
    dating();
    exec(`$test_link = $func('mod_GLQS_main', 'rel_actions', 'A1', ${gender})`);
    const link = api.readVariable('$test_link').match(/href="exec: ([^"]*)">Marry/);
    assert.ok(link, type);
    exec(link[1]);
    assert.equal(keyed('$npc_rel_type', 'A1'), type);
    assert.equal(api.readVariable(spouse), 'A1');
    assert.equal(keyed('stat', 'dating_current'), 0);
    assert.equal(keyed('stat', counter), 1);
    assert.equal(keyed('stat', 'total_lovers_current'), 1);
    exec(`$test_link = $func('mod_GLQS_main', 'rel_actions', 'A1', ${gender})`);
    const divorce = api.readVariable('$test_link').match(/href="exec: ([^"]*)">Divorce/);
    assert.ok(divorce, type);
    exec(divorce[1]);
    assert.equal(api.readVariable(spouse), '');
    assert.equal(keyed('stat', counter), 0);
    assert.equal(keyed('stat', 'total_lovers_current'), 0);
}
""")

    def test_restock_preserves_larger_stacks_and_set_all_still_sets(self):
        self.run_qsp(r"""
exec("killall & mc_inventory['normal_condoms'] = 2000 & mc_inventory['shampoo'] = 12 & mc_inventory['unlisted_test_item'] = 7 & gt 'mod_GLQS_main', 'consumables_menu'");
for (let repeat = 0; repeat < 2; repeat++) {
    click('Restock to at Least 1,000');
    assert.equal(keyed('mc_inventory', 'normal_condoms'), 2000);
    assert.equal(keyed('mc_inventory', 'shampoo'), 1000);
    assert.equal(keyed('mc_inventory', 'razor'), 1000);
    assert.equal(keyed('mc_inventory', 'mag_porn'), 1);
    assert.equal(keyed('mc_inventory', 'unlisted_test_item'), 7);
}
click('Set All to 100');
assert.equal(keyed('mc_inventory', 'normal_condoms'), 100);
assert.equal(keyed('mc_inventory', 'shampoo'), 100);
assert.equal(keyed('mc_inventory', 'mag_porn'), 1);
assert.equal(keyed('mc_inventory', 'unlisted_test_item'), 7);
""")

    def test_individual_stats_validate_input_and_use_upstream_progression(self):
        self.run_qsp(r"""
exec("killall & stren_lvl = 20 & intel_lvl = 30 & willpowermax = 150");
inputs.push('bad', '-1', '101', '72');
exec("gs 'mod_GLQS_main', 'stat_edit', 0");
assert.equal(api.readVariable('stren_lvl'), 72);
assert.ok(api.readVariable('stren_exp') > 0);
assert.equal(api.readVariable('intel_lvl'), 30);
assert.equal(messages.length, 3);
inputs.push('0');
exec("gs 'mod_GLQS_main', 'stat_edit', 3");
assert.equal(api.readVariable('intel_lvl'), 0);
inputs.push('');
exec("gs 'mod_GLQS_main', 'stat_edit', 0");
assert.equal(api.readVariable('stren_lvl'), 72);
inputs.push('49', '180');
exec("gs 'mod_GLQS_main', 'stat_edit', 10");
assert.equal(api.readVariable('willpowermax'), 180);
""")

    def test_custom_inventory_and_category_restock_are_scoped(self):
        self.run_qsp(r"""
exec("killall & mc_inventory['normal_condoms'] = 2500 & mc_inventory['shampoo'] = 12 & mc_inventory['unlisted_test_item'] = 7");
inputs.push('2147483648', '0');
exec("gs 'mod_GLQS_main', 'consumable_edit', 1");
assert.equal(keyed('mc_inventory', 'normal_condoms'), 0);
inputs.push('');
exec("gs 'mod_GLQS_main', 'consumable_edit', 1");
assert.equal(keyed('mc_inventory', 'normal_condoms'), 0);
exec("gs 'mod_GLQS_main', 'consumables', 1000, 1, 'Medical / Hygiene'");
assert.equal(keyed('mc_inventory', 'shampoo'), 1000);
assert.equal(keyed('mc_inventory', 'normal_condoms'), 0);
assert.equal(keyed('mc_inventory', 'unlisted_test_item'), 7);
""")

    def test_custom_money_preserves_exact_amounts_and_closed_accounts(self):
        self.run_qsp(r"""
exec('killall & money = 999000000 & money_overflow = 123');
inputs.push('999999999');
exec("gs 'mod_GLQS_main', 'money_custom', 'cash'");
assert.equal(api.readVariable('money') + 1000000 * api.readVariable('money_overflow'), 2121999999);
exec("gs 'mod_GLQS_main', 'money_add', 'bank', 500");
assert.equal(api.readVariable('karta'), 0);
exec('bankAccount = 1 & bankDebtLimit = 1000 & karta = 1200');
inputs.push('600');
exec("gs 'mod_GLQS_main', 'money_custom', 'bank'");
assert.equal(api.readVariable('karta') - api.readVariable('bankDebtLimit'), 800);
inputs.push('');
exec("gs 'mod_GLQS_main', 'money_custom', 'bank'");
assert.equal(api.readVariable('karta') - api.readVariable('bankDebtLimit'), 800);
""")

    def test_favorites_pin_execute_and_survive_save_reload(self):
        self.run_qsp(r"""
exec("killall & gt 'mod_GLQS_main', 'favorites'");
link('Pin');
assert.equal(keyed('glqs_favorites', 'restore'), 1);
const save = api.saveGame();
assert.ok(save);
exec("killvar 'glqs_favorites'");
api.loadSave(save);
assert.equal(keyed('glqs_favorites', 'restore'), 1);
exec("healthmax = 100 & stammax = 120 & willpowermax = 180 & pcs_health = 2 & gt 'mod_GLQS_main', 'start'");
link('Full Restore Everything');
assert.equal(api.readVariable('pcs_health'), 100);
assert.equal(api.readVariable('pcs_stam'), 120);
exec("gt 'mod_GLQS_main', 'favorites'");
link('Unpin');
assert.equal(keyed('glqs_favorites', 'restore'), 0);
""")

    def test_presets_apply_selected_parts_and_preserve_cheat_side_effects(self):
        self.run_qsp(r"""
exec("killall & stren_lvl = 35 & intel_lvl = 60 & willpowermax = 180 & money = 500 & bankAccount = 1 & bankDebtLimit = 50 & karta = 950 & mc_inventory['shampoo'] = 17 & cheatVars['sleep_vib'] = 1 & cheatVars['clothes_dirt'] = 1 & cheatVars['drugs_immune'] = 1 & cheatVars['no_dream_chance'] = 100 & cheatVars['bimbo'] = 1 & cheatVars['no_periods'] = 1 & gs 'mod_GLQS_main', 'preset_capture' & $test_preset = $glqs_preset_export");
exec("stren_lvl = 5 & intel_lvl = 6 & willpowermax = 50 & money = 22 & mc_inventory['shampoo'] = 99 & glqs_preset_stats = 1 & gs 'mod_GLQS_main', 'preset_apply', $test_preset");
assert.equal(api.readVariable('stren_lvl'), 35);
assert.equal(api.readVariable('intel_lvl'), 60);
assert.equal(api.readVariable('willpowermax'), 180);
assert.equal(api.readVariable('money'), 22);
assert.equal(keyed('mc_inventory', 'shampoo'), 99);
exec("glqs_preset_stats = 0 & glqs_preset_inventory = 1 & gs 'mod_GLQS_main', 'preset_apply', $test_preset");
assert.equal(keyed('mc_inventory', 'shampoo'), 17);
exec("glqs_preset_inventory = 0 & glqs_preset_funds = 1 & bankDebtLimit = 100 & karta = 200 & gs 'mod_GLQS_main', 'preset_apply', $test_preset");
assert.equal(api.readVariable('money'), 500);
assert.equal(api.readVariable('karta') - api.readVariable('bankDebtLimit'), 900);
assert.equal(api.readVariable('bankDebtLimit'), 100);
exec("glqs_preset_funds = 0 & glqs_preset_cheats = 1 & killvar 'cheatVars' & gs 'mod_GLQS_main', 'preset_apply', $test_preset");
assert.equal(keyed('cheatVars', 'sleep_vib'), 1);
assert.equal(keyed('sleepVars', 'bedVibrator'), 1);
assert.equal(keyed('cheatVars', 'no_dream_chance'), 100);
assert.equal(keyed('cheatVars', 'bimbo'), 1);
assert.equal(api.readVariable('cycle'), 6);
assert.equal(api.readVariable('test_washes'), 1);
const archetypeUpdates = api.readVariable('test_archetype_updates');
assert.ok(archetypeUpdates > 0);
exec("gs 'mod_GLQS_main', 'preset_apply', $test_preset");
assert.equal(api.readVariable('test_washes'), 1);
assert.equal(api.readVariable('test_archetype_updates'), archetypeUpdates);
exec("glqs_preset_cheats = 0 & glqs_preset_funds = 1 & bankAccount = 0 & gs 'mod_GLQS_main', 'preset_apply', $test_preset");
assert.equal(api.readVariable('bankAccount'), 1);
assert.equal(api.readVariable('bankDebtLimit'), 0);
assert.equal(api.readVariable('karta'), 900);
exec("bankAccount = 0 & gs 'mod_GLQS_main', 'preset_capture' & $test_closed = $glqs_preset_export & bankAccount = 1 & bankDebtLimit = 100 & karta = 555 & gs 'mod_GLQS_main', 'preset_apply', $test_closed");
assert.equal(api.readVariable('bankAccount'), 1);
assert.equal(api.readVariable('bankDebtLimit'), 100);
assert.equal(api.readVariable('karta'), 555);
""")

    def test_presets_export_import_between_characters_and_survive_reload(self):
        self.run_qsp(r"""
exec("killall & willpowermax = 150 & stren_lvl = 60 & money = 700 & mc_inventory['shampoo'] = 123 & gt 'mod_GLQS_main', 'preset_detail', 1");
inputs.push('My <preset>');
click('Capture Current Character into This Slot');
assert.ok(mainText.includes('My &lt;preset&gt;'));
const code = api.readVariableByIndex('$glqs_preset_codes', 1);
assert.ok(code.startsWith('GLQS1|'));
click('Show Export Code');
const parts = [...mainText.matchAll(/<code>([^<]*)<\/code>/g)].map(match => match[1]);
assert.ok(parts.length > 1);
assert.ok(parts.every(part => part.length <= 127));
exec('killall & glqs_preset_slot = 2');
inputs.push(...parts, 'Imported preset');
exec("gs 'mod_GLQS_main', 'preset_import'");
assert.equal(api.readVariableByIndex('$glqs_preset_codes', 2), code);
assert.equal(api.readVariableByIndex('$glqs_preset_names', 2), 'Imported preset');
assert.equal(api.readVariable('money'), 0);
assert.equal(api.readVariable('stren_lvl'), 0);
const save = api.saveGame();
assert.ok(save);
exec("killvar '$glqs_preset_codes'");
api.loadSave(save);
assert.equal(api.readVariableByIndex('$glqs_preset_codes', 2), code);
exec("glqs_preset_stats = 1 & glqs_preset_funds = 1 & gs 'mod_GLQS_main', 'preset_apply', $glqs_preset_codes[2]");
assert.equal(api.readVariable('stren_lvl'), 60);
assert.equal(api.readVariable('money'), 700);
inputs.push(parts[1]);
exec("gs 'mod_GLQS_main', 'preset_import'");
assert.equal(api.readVariableByIndex('$glqs_preset_codes', 2), code);
inputs.push(parts[0], '');
exec("gs 'mod_GLQS_main', 'preset_import'");
assert.equal(api.readVariableByIndex('$glqs_preset_codes', 2), code);
""")

    def test_presets_reject_invalid_data_before_any_changes(self):
        self.run_qsp(r"""
exec("killall & willpowermax = 150 & stren_lvl = 40 & money = 700 & gs 'mod_GLQS_main', 'preset_capture'");
const code = api.readVariable('$glqs_preset_export');
for (const invalid of [
    code.replace('GLQS1', 'GLQS2'),
    code.replace('S_stren=40', 'S_stren=999'),
    code.replace('S_stren=40', 'S_stren=-1'),
    code.replace('S_stren=40', 'S_unknown=40'),
    code.replace('S_stren=40', 'S_stren=40|S_stren=40'),
    code.replace('S_stren=40', "S_stren=40 & money = 0"),
    code.replace('S_agil=0', 'S_stren=0'),
    code.replace('T_no_dream_chance=0', 'T_no_dream_chance=55'),
]) {
    exec("$test_bad_preset = ''");
    for (let i = 0; i < invalid.length; i += 100) {
        inputs.push(invalid.slice(i, i + 100));
        exec("$test_bad_preset += $input('test')");
    }
    exec("stren_lvl = 3 & money = 11 & glqs_preset_stats = 1 & glqs_preset_funds = 1 & gs 'mod_GLQS_main', 'preset_apply', $test_bad_preset");
    assert.equal(api.readVariable('glqs_preset_valid'), 0, invalid);
    assert.equal(api.readVariable('stren_lvl'), 3);
    assert.equal(api.readVariable('money'), 11);
}
""")

    def test_large_presets_transfer_without_truncation_or_partial_import(self):
        self.run_qsp(r"""
exec("killall & willpowermax = 200 & money = 999999999 & money_overflow = 999999999 & bankAccount = 1 & karta = 999999999 & karta_overflow = 999999999 & gs 'mod_GLQS_main', 'stats' & gs 'mod_GLQS_main', 'consumables', 999999999 & gs 'mod_GLQS_main', 'preset_capture' & glqs_preset_slot = 1 & $glqs_preset_codes[1] = $glqs_preset_export & gt 'mod_GLQS_main', 'preset_export'");
const code = api.readVariableByIndex('$glqs_preset_codes', 1);
const parts = [...mainText.matchAll(/<code>([^<]*)<\/code>/g)].map(match => match[1]);
assert.ok(parts.length >= 10);
assert.ok(parts.every(part => part.length <= 127));
exec('glqs_preset_slot = 2');
inputs.push(...parts, '');
exec("gs 'mod_GLQS_main', 'preset_import'");
assert.equal(api.readVariableByIndex('$glqs_preset_codes', 2), '');
const badParts = [...parts];
badParts[0] = badParts[0].replace(/GLQSC1;[0-9a-f]{16}/, 'GLQSC1;0000000000000000');
inputs.push(...badParts);
exec("gs 'mod_GLQS_main', 'preset_import'");
assert.equal(api.readVariableByIndex('$glqs_preset_codes', 2), '');
inputs.push(...parts, 'Large preset');
exec("gs 'mod_GLQS_main', 'preset_import'");
assert.equal(api.readVariableByIndex('$glqs_preset_codes', 2), code);
""")

    def test_clothing_ownership_filters_and_missing_grants_preserve_owned_items(self):
        self.run_qsp(r"""
exec("killall & pcs_hips = 90 & allure_swimsuit[1] = 1 & allure_swimsuit_h[1] = 3 & allure_swimsuit_b[1] = 80 & allure_swimsuit_s[1] = 1 & allure_swimsuit_dirt[1] = 7 & gt 'mod_GLQS_main', 'item_picker', 'clo', 'allure_swimsuit', 'allure', 'Swimsuits'");
assert.equal(api.readVariableSize('glqs_plist'), 100);
link('Owned');
assert.equal(api.readVariableSize('glqs_plist'), 1);
assert.equal(api.readVariableByIndex('glqs_plist', 0), 1);
link('Unowned');
assert.equal(api.readVariableSize('glqs_plist'), 99);
assert.equal(api.readVariableByIndex('glqs_plist', 0), 2);
click('Give Missing (shown)');
assert.equal(api.readVariableByIndex('allure_swimsuit', 2), 1);
assert.equal(api.readVariableByIndex('allure_swimsuit_h', 1), 3);
assert.equal(api.readVariableByIndex('allure_swimsuit_b', 1), 80);
assert.equal(api.readVariableByIndex('allure_swimsuit_s', 1), 1);
assert.equal(api.readVariableByIndex('allure_swimsuit_dirt', 1), 7);
assert.equal(api.readVariableSize('glqs_plist'), 0);
click('Reset Sort & Filters');
assert.equal(api.readVariableSize('glqs_plist'), 100);
exec("allure_swimsuit[2] = 0 & gs 'mod_GLQS_main', 'fill_by_type', 'clo', 'allure_swimsuit', 1");
assert.equal(api.readVariableByIndex('allure_swimsuit', 2), 1);
assert.equal(api.readVariableByIndex('allure_swimsuit_h', 1), 3);
""", ("clothing", "clothing_attributes", "_attributes_allure_swimsuit", "_shop_icon_image", "_clothing_image"))

    def test_missing_grants_recognize_ownership_for_every_item_type(self):
        self.run_qsp(r"""
for (const [type, key, array] of [
    ['clo', 'allure_swimsuit', 'allure_swimsuit'],
    ['shoe', 'bomba', 'bomba_shoe'],
    ['bra', 'bomba', 'bomba_bras'],
    ['panty', 'bomba', 'bomba_panties'],
    ['body', 'bomba', 'bomba_bodysuits'],
    ['coat', 'bomba', 'bomba_coats'],
    ['purse', 'bomba', 'bomba_purses'],
]) {
    exec(`killall & ${array}[1] = 1 & ${array}_h[1] = 3 & test_owned = func('mod_GLQS_main', 'item_owned', '${type}', '${key}', 1)`);
    assert.equal(api.readVariable('test_owned'), 1, type);
    exec(`gs 'mod_GLQS_main', 'item_grant', '${type}', '${key}', 1, 1`);
    assert.equal(api.readVariableByIndex(array, 1), 1, type);
    assert.equal(api.readVariableByIndex(`${array}_h`, 1), 3, type);
}
""", ("clothing", "shoes", "bras", "panties", "underwear_bodysuits", "coats", "purses"))


if __name__ == "__main__":
    unittest.main()

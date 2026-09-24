import io
import re
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


if __name__ == "__main__":
    unittest.main()

import re
import unittest
from pathlib import Path

import build


class BuildValidationTests(unittest.TestCase):
    def test_real_source_tree_assembles_and_validates(self):
        standalone, shared = build.collect_fragments()
        build.validate_fragment_contract(standalone, shared)
        text = build.assemble(standalone, shared)
        build.validate_route_definitions(text)
        build.validate_route_coverage(text)
        build.validate_navigation_registry(
            text, build.extract_route_definitions(text)
        )
        build.validate_recurrent_bulk_handlers(text)
        build.validate_recurrent_toggle_contract(text)
        build.validate_recurrent_metadata(text)
        self.assertEqual(build.lint_non_ascii(text), [])
        build.validate_consumable_metadata(
            (build.SRC_DIR / "06_consumables_data.qsps").read_text(
                encoding="utf-8"
            )
        )
        catalog = (build.SRC_DIR / "05_clothing_data.qsps").read_text(
            encoding="utf-8"
        )
        picker_actions = [
            line for line in text.splitlines()
            if line.lstrip().startswith("act ")
            and "gt 'mod_GLQS_main', 'item_picker'" in line
        ]
        catalog_rows = re.findall(
            r"\$glqs_cc\[glqs_cc_n\]\s*=\s*'[^']+'", catalog
        )
        self.assertEqual(len(picker_actions), len(catalog_rows))

    def test_route_calls_support_qsp_escaped_quotes(self):
        text = (
            "gs ''mod_GLQS_main'', ''item_pick''\n"
            "gt 'mod_GLQS_main', 'start'\n"
        )
        self.assertEqual(
            build.extract_route_calls(text), {"item_pick", "start"}
        )

    def test_non_ascii_source_reaches_lint(self):
        self.assertTrue(build.lint_non_ascii("!! smart — punctuation"))

    def test_missing_route_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            build.validate_route_coverage(
                "if $ARGS[0] = 'start':\n"
                "gt 'mod_GLQS_main', 'missing'\n"
            )

    def test_duplicate_simple_route_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "start"):
            build.validate_route_definitions(
                "if $ARGS[0] = 'start':\nend\n"
                "if $ARGS[0] = 'start':\nend\n"
            )

    def test_navigation_template_requires_one_marker_pair(self):
        with self.assertRaisesRegex(ValueError, "marker pair"):
            build.validate_navigation_template(
                "$glqs_nb[glqs_nb_n] = 'start|Index'\n"
            )

    def test_navigation_registry_must_resolve(self):
        text = (
            "$glqs_nb[glqs_nb_n] = 'clothing_menu|Clothing'\n"
            "if $glqs_current <> 'clothing_menu': act 'Clothing': "
            "gt 'mod_GLQS_main', 'clothing_menu'\n"
        )
        with self.assertRaisesRegex(ValueError, "no route definitions"):
            build.validate_navigation_registry(text, set())

    def test_recurrent_bulk_handlers_cover_primary_table(self):
        text = (
            "!! RECURRENT_METADATA_BEGIN\n"
            "!! bulk|willpower|Willpower\n"
            "!! RECURRENT_METADATA_END\n"
            "if $ARGS[0] = 'recurrent':\n"
            "$glqs_tbl += \"cheatVars['willpower'] = iif(cheatVars['willpower'], 0, 1)\"\n"
            "$glqs_tbl2 = \"cheatVars[''no_pregnancy''] = iif(cheatVars[''no_pregnancy''], 0, 1)\"\n"
            "if $ARGS[0] = 'recurrent_on':\n"
            "cheatVars['willpower'] = 1\n"
            "if $ARGS[0] = 'recurrent_off':\n"
            "cheatVars['willpower'] = 0\n"
        )
        build.validate_recurrent_bulk_handlers(text)
        build.validate_recurrent_toggle_contract(text)

    def test_job_ids_match_reference_source(self):
        ref_path = (
            Path(__file__).resolve().parents[1]
            / "reference" / "nightly" / "locations" / "jobs_list.qsrc"
        )
        if not ref_path.exists():
            self.skipTest("nightly reference source not present")
        build.validate_job_ids(
            (build.SRC_DIR / "20_jobs_data.qsps").read_text(encoding="utf-8"),
            ref_path.read_text(encoding="utf-8"),
        )

    def test_job_ids_reject_mismatch(self):
        with self.assertRaisesRegex(ValueError, "Job ID mismatch"):
            build.validate_job_ids(
                "$glqs_jb[glqs_jb_n] = 'city_office_secretary|Office Secretary'\n",
                "if $ARGS[0] = 'city_office_cleaner':\nend\n",
            )


if __name__ == "__main__":
    unittest.main()

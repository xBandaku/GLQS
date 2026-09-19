#!/usr/bin/env python3
"""
GLQS build script
==================
Stitches the per-feature source fragments in src/ back into a single
GLQS.qsps file, runs lint checks for QSP pitfalls we've hit before, then
compiles it to GLQS.qsp using qsp-cli.

Usage:
    python3 build.py

Requirements:
    npm install -g @qsp/cli      (only needed once)

Folder layout expected:
    src/01_setup.qsps        <- standalone location (has # name / --- name --- wrapper)
    src/02_readme.qsps       <- standalone location
    src/03_hook.qsps         <- standalone location
    src/05_*.qsps ... 21_*.qsps
                              <- body fragments listed in SHARED_FILES for the
                                 single big 'mod_GLQS_main' location, with no
                                 # header or --- footer of their own.
                                 build.py wraps them all in one shared location.

To add a new submenu/feature:
    1. Create a new src/NN_description.qsps fragment (body only, no # / --- lines).
    2. Add its filename to SHARED_FILES in the desired assembly position.
    3. Run this script. It handles the rest.

To add a whole new standalone location (rare):
    1. Create src/NN_name.qsps with its own '# location_name' header and
       '--- location_name ---------------------------------' footer.
    2. Add 'NN_name.qsps' to STANDALONE_FILES below so build.py knows to
       pass it through unwrapped.
"""

import subprocess
import sys
from pathlib import Path

import build_support

SRC_DIR = build_support.SRC_DIR
BUILD_DIR = build_support.BUILD_DIR
OUTPUT_QSPS = build_support.OUTPUT_QSPS
OUTPUT_QSP = build_support.OUTPUT_QSP

STANDALONE_FILES = build_support.STANDALONE_FILES
SHARED_FILES = build_support.SHARED_FILES
SHARED_LOCATION_NAME = build_support.SHARED_LOCATION_NAME
NAVIGATION_FILE = build_support.NAVIGATION_FILE
NAVIGATION_BEGIN = build_support.NAVIGATION_BEGIN
NAVIGATION_END = build_support.NAVIGATION_END
CLOTHING_ACTIONS_BEGIN = build_support.CLOTHING_ACTIONS_BEGIN
CLOTHING_ACTIONS_END = build_support.CLOTHING_ACTIONS_END
CLOTHING_LABELS_BEGIN = build_support.CLOTHING_LABELS_BEGIN
CLOTHING_LABELS_END = build_support.CLOTHING_LABELS_END

# Support functions are implemented in build_support.py so build.py stays focused
# on the build pipeline orchestration.
collect_fragments = build_support.collect_fragments
validate_fragment_contract = build_support.validate_fragment_contract
extract_route_definitions = build_support.extract_route_definitions
validate_route_definitions = build_support.validate_route_definitions
extract_route_calls = build_support.extract_route_calls
validate_route_coverage = build_support.validate_route_coverage
validate_navigation_registry = build_support.validate_navigation_registry
validate_navigation_template = build_support.validate_navigation_template
validate_recurrent_bulk_handlers = build_support.validate_recurrent_bulk_handlers
validate_recurrent_toggle_contract = build_support.validate_recurrent_toggle_contract
validate_recurrent_metadata = build_support.validate_recurrent_metadata
expand_navigation_actions = build_support.expand_navigation_actions
expand_clothing_store = build_support.expand_clothing_store
assemble = build_support.assemble
lint_apostrophes_in_comments = build_support.lint_apostrophes_in_comments
lint_non_ascii = build_support.lint_non_ascii
lint_unbalanced_template_markers = build_support.lint_unbalanced_template_markers
lint_empty_template_markers = build_support.lint_empty_template_markers
lint_version_mismatch = build_support.lint_version_mismatch
lint_block_balance = build_support.lint_block_balance
run_lints = build_support.run_lints
validate_consumable_metadata = build_support.validate_consumable_metadata
validate_job_ids = build_support.validate_job_ids


def main():
    if not SRC_DIR.exists():
        print(f"ERROR: {SRC_DIR} not found. Run this script from the project root.")
        sys.exit(1)

    BUILD_DIR.mkdir(exist_ok=True)

    standalone_files, shared_files = collect_fragments()
    validate_fragment_contract(standalone_files, shared_files)

    print("Standalone locations (in order):")
    for f in standalone_files:
        print(f"  {f.name}")
    print("\nShared 'mod_GLQS_main' fragments (in order):")
    for f in shared_files:
        print(f"  {f.name}")

    assembled = assemble(standalone_files, shared_files)
    validate_route_definitions(assembled)
    validate_route_coverage(assembled)
    validate_navigation_registry(
        assembled, extract_route_definitions(assembled)
    )
    validate_recurrent_bulk_handlers(assembled)
    validate_recurrent_toggle_contract(assembled)
    validate_recurrent_metadata(assembled)
    validate_consumable_metadata(
        (SRC_DIR / "06_consumables_data.qsps").read_text(encoding="utf-8")
    )
    job_manifest = (SRC_DIR / "20_jobs_data.qsps").read_text(encoding="utf-8")
    reference_jobs = (
        build_support.REFERENCE_JOBS_LIST.read_text(encoding="utf-8")
        if build_support.REFERENCE_JOBS_LIST.exists()
        else None
    )
    validate_job_ids(job_manifest, reference_jobs)
    OUTPUT_QSPS.write_text(assembled, encoding="ascii")
    print(f"\nAssembled -> {OUTPUT_QSPS} ({len(assembled.splitlines())} lines)")

    print("\nRunning lint checks...")
    if not run_lints(assembled):
        print("\nLint checks FAILED. Fix the issues above before compiling.")
        print(f"(Assembled file was still written to {OUTPUT_QSPS} for inspection.)")
        sys.exit(1)
    print("Lint checks passed.")

    print("\nCompiling with qsp-cli...")
    result = subprocess.run(
        ["qsp-cli", str(OUTPUT_QSPS.name)],
        cwd=str(BUILD_DIR),
        capture_output=True,
        text=True,
        shell=(sys.platform == "win32"),
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("\nCompilation FAILED.")
        sys.exit(1)

    print(f"\nSUCCESS: {OUTPUT_QSP}")
    print("Copy this file into your Girl Life 'mod/' folder.")


if __name__ == "__main__":
    main()

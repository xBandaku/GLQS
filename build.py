#!/usr/bin/env python3
"""
GLQS build script
==================
Stitches the source fragments in src/ into build/GLQS.qsps, validates and
lints it for QSP pitfalls we have hit before, then compiles it to
build/GLQS.qsp with qsp-cli.

Usage:
    python build.py

Requirements:
    npm install -g @qsp/cli@1.0.5      (only needed once)

The fragment manifests (STANDALONE_FILES, SHARED_FILES), validators and lint
rules all live in build_support.py. CLAUDE.md describes how the fragments
assemble into locations and how to add a new one.
"""

import subprocess
import sys

import build_support


def check(assembled):
    """Run the validators and the lints, reporting every problem instead of
    stopping at the first. Returns True when the text is ready to compile."""
    ok = True
    try:
        build_support.validate_assembled(assembled)
    except ValueError as exc:
        ok = False
        print(f"\n[VALIDATION] {exc}")

    print("\nRunning lint checks...")
    if not build_support.run_lints(assembled):
        ok = False
    return ok


def main():
    if not build_support.SRC_DIR.exists():
        print(f"ERROR: {build_support.SRC_DIR} not found. Run this script from the project root.")
        sys.exit(1)

    build_support.BUILD_DIR.mkdir(exist_ok=True)

    try:
        standalone_files, shared_files = build_support.collect_fragments()
        build_support.validate_fragment_contract(standalone_files, shared_files)

        print("Standalone locations (in order):")
        for f in standalone_files:
            print(f"  {f.name}")
        print("\nShared 'mod_GLQS_main' fragments (in order):")
        for f in shared_files:
            print(f"  {f.name}")

        assembled = build_support.assemble(standalone_files, shared_files)
    except ValueError as exc:
        print(f"\nBuild FAILED: {exc}")
        sys.exit(1)

    # Written before any check, and as UTF-8 rather than ASCII: a stray
    # em-dash has to reach lint_non_ascii and be reported with its line
    # number, not crash the write with a UnicodeEncodeError.
    output = build_support.OUTPUT_QSPS
    output.write_text(assembled, encoding="utf-8")
    print(f"\nAssembled -> {output} ({len(assembled.splitlines())} lines)")

    if not check(assembled):
        print("\nChecks FAILED. Fix the issues above before compiling.")
        print(f"(Assembled file was still written to {output} for inspection.)")
        sys.exit(1)
    print("Checks passed.")

    print("\nCompiling with qsp-cli...")
    result = subprocess.run(
        ["qsp-cli", str(output.name)],
        cwd=str(build_support.BUILD_DIR),
        capture_output=True,
        text=True,
        shell=(sys.platform == "win32"),
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("\nCompilation FAILED.")
        sys.exit(1)

    print(f"\nSUCCESS: {build_support.OUTPUT_QSP}")
    print("Copy this file into your Girl Life 'mod/' folder.")


if __name__ == "__main__":
    main()

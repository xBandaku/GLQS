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
    src/04_*.qsps ... 16_*.qsps
                              <- body fragments of the single big 'mod_GLQS_main'
                                 location, NO # header or --- footer of their own.
                                 build.py wraps them all in one shared location,
                                 in filename sort order.

To add a new submenu/feature:
    1. Create a new src/NN_description.qsps fragment (body only, no # / --- lines)
       with a number that places it where you want in mod_GLQS_main, OR add your
       code to an existing fragment file if it belongs there.
    2. Run this script. It handles the rest.

To add a whole new standalone location (rare):
    1. Create src/NN_name.qsps with its own '# location_name' header and
       '--- location_name ---------------------------------' footer.
    2. Add 'NN_name.qsps' to STANDALONE_FILES below so build.py knows to
       pass it through unwrapped.
"""

import re
import subprocess
import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent / "src"
BUILD_DIR = Path(__file__).parent / "build"
OUTPUT_QSPS = BUILD_DIR / "GLQS.qsps"
OUTPUT_QSP = BUILD_DIR / "GLQS.qsp"

# Files that already contain their own '# LocationName' / '--- LocationName ---'
# wrapper and should be included as-is, IN THIS ORDER, before the shared
# mod_GLQS_main location is assembled from every other fragment.
STANDALONE_FILES = [
    "01_setup.qsps",
    "02_readme.qsps",
    "03_hook.qsps",
]

SHARED_LOCATION_NAME = "mod_GLQS_main"


def collect_fragments():
    all_files = sorted(SRC_DIR.glob("*.qsps"))
    standalone = [f for f in all_files if f.name in STANDALONE_FILES]
    standalone.sort(key=lambda f: STANDALONE_FILES.index(f.name))
    shared = [f for f in all_files if f.name not in STANDALONE_FILES]
    return standalone, shared


def assemble(standalone_files, shared_files):
    parts = []
    for f in standalone_files:
        parts.append(f.read_text())

    parts.append(f"# {SHARED_LOCATION_NAME}\n")
    for f in shared_files:
        parts.append(f.read_text())
    parts.append(
        f"--- {SHARED_LOCATION_NAME} ---------------------------------\n"
    )

    return "\n".join(p.rstrip("\n") + "\n" for p in parts)


def lint_apostrophes_in_comments(text):
    """QSP comments starting with !! do NOT reliably suppress quote-parsing.
    A raw apostrophe (e.g. in "game's") inside a !! comment can open an
    unterminated string that corrupts all block-nesting after it, producing
    a misleading '[end] not found' error somewhere else entirely.
    Doubled '' (the QSP escape) is fine and ignored here."""
    problems = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("!!"):
            cleaned = stripped.replace("''", "")
            if "'" in cleaned:
                problems.append((i, line))
    return problems


def lint_non_ascii(text):
    """QSP's parser only handles ASCII. Smart quotes, em-dashes, etc.
    anywhere -- including inside comments -- throw a syntax error."""
    problems = []
    for i, line in enumerate(text.splitlines(), start=1):
        for ch in line:
            if not (ch == "\t" or 0x20 <= ord(ch) <= 0x7E):
                problems.append((i, line))
                break
    return problems


def lint_block_balance(text):
    """Rough check that every multi-line 'if ...:' and 'act 'x':' block has
    a matching 'end'. Not a full parser -- doesn't understand elseif chains
    perfectly or single-line if/act -- but catches the common mistake of a
    missing/extra end before you waste time in-game hunting for it."""
    depth = 0
    stack = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        l = line.strip()
        if re.match(r"^if\s.*:$", l):
            depth += 1
            stack.append((i, l[:60]))
        elif re.match(r"^act\s+'[^']*':$", l):
            depth += 1
            stack.append((i, l[:60]))
        elif l == "end":
            if stack:
                stack.pop()
            depth -= 1
    return depth, stack


def run_lints(text):
    ok = True

    apostrophe_hits = lint_apostrophes_in_comments(text)
    if apostrophe_hits:
        ok = False
        print("\n[LINT] Raw apostrophes found inside !! comments:")
        print("       (these can corrupt QSP's parser -- remove the apostrophe")
        print("        or rephrase the comment)")
        for lineno, line in apostrophe_hits:
            print(f"    line {lineno}: {line.strip()}")

    non_ascii_hits = lint_non_ascii(text)
    if non_ascii_hits:
        ok = False
        print("\n[LINT] Non-ASCII characters found (smart quotes, em-dashes, etc.):")
        for lineno, line in non_ascii_hits:
            print(f"    line {lineno}: {line.strip()}")

    depth, stack = lint_block_balance(text)
    if depth != 0:
        ok = False
        print(f"\n[LINT] if/act/end block imbalance -- final depth {depth} (should be 0)")
        print("       Unclosed blocks (most likely culprits):")
        for lineno, snippet in stack:
            print(f"    line {lineno}: {snippet}")

    return ok


def main():
    if not SRC_DIR.exists():
        print(f"ERROR: {SRC_DIR} not found. Run this script from the project root.")
        sys.exit(1)

    BUILD_DIR.mkdir(exist_ok=True)

    standalone_files, shared_files = collect_fragments()

    print("Standalone locations (in order):")
    for f in standalone_files:
        print(f"  {f.name}")
    print("\nShared 'mod_GLQS_main' fragments (in order):")
    for f in shared_files:
        print(f"  {f.name}")

    assembled = assemble(standalone_files, shared_files)
    OUTPUT_QSPS.write_text(assembled)
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

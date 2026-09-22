import re
from pathlib import Path

SRC_DIR = Path(__file__).parent / "src"
BUILD_DIR = Path(__file__).parent / "build"
OUTPUT_QSPS = BUILD_DIR / "GLQS.qsps"
OUTPUT_QSP = BUILD_DIR / "GLQS.qsp"

REFERENCE_JOBS_LIST = (
    Path(__file__).parent / "reference" / "nightly" / "locations" / "jobs_list.qsrc"
)

STANDALONE_FILES = [
    "01_setup.qsps",
    "02_readme.qsps",
    "03_hook.qsps",
]

SHARED_FILES = [
    "04_main_menu.qsps",
    "05_clothing_data.qsps",
    "05_clothing.qsps",
    "05_clothing_store.qsps",
    "05_clothing_picker.qsps",
    "06_consumables_data.qsps",
    "06_consumables_actions.qsps",
    "06_consumables_menu.qsps",
    "07_stats_data.qsps",
    "07_stats_actions.qsps",
    "07_stats_menu.qsps",
    "08_recurrent.qsps",
    "09_grades.qsps",
    "09_grades_data.qsps",
    "10_money.qsps",
    "11_relationships.qsps",
    "11_relationships_data.qsps",
    "12_bodymod.qsps",
    "13_health.qsps",
    "14_fill_data.qsps",
    "15_fill_helpers.qsps",
    "16_fame.qsps",
    "17_housing.qsps",
    "18_magic.qsps",
    "19_jobs.qsps",
    "20_jobs_data.qsps",
    "21_lifestyle.qsps",
]

SHARED_LOCATION_NAME = "mod_GLQS_main"
NAVIGATION_FILE = "04_main_menu.qsps"
NAVIGATION_BEGIN = "!! GLQS_NAV_ACTIONS_BEGIN"
NAVIGATION_END = "!! GLQS_NAV_ACTIONS_END"
CLOTHING_ACTIONS_BEGIN = "!! GLQS_CLOTHING_ACTIONS_BEGIN"
CLOTHING_ACTIONS_END = "!! GLQS_CLOTHING_ACTIONS_END"
CLOTHING_LABELS_BEGIN = "!! GLQS_CLOTHING_LABELS_BEGIN"
CLOTHING_LABELS_END = "!! GLQS_CLOTHING_LABELS_END"


def collect_fragments():
    all_files = sorted(SRC_DIR.glob("*.qsps"))
    missing = [name for name in STANDALONE_FILES if not (SRC_DIR / name).is_file()]
    if missing:
        raise ValueError("Standalone files are missing from src/: " + ", ".join(missing))
    standalone = [f for f in all_files if f.name in STANDALONE_FILES]
    standalone.sort(key=lambda f: STANDALONE_FILES.index(f.name))
    present = {f.name for f in all_files}
    missing_shared = [name for name in SHARED_FILES if name not in present]
    unexpected = sorted(present - set(STANDALONE_FILES) - set(SHARED_FILES))
    if missing_shared or unexpected:
        problems = []
        if missing_shared:
            problems.append("missing shared files: " + ", ".join(missing_shared))
        if unexpected:
            problems.append("unlisted source files: " + ", ".join(unexpected))
        raise ValueError("Fragment manifest failed: " + "; ".join(problems))
    shared = [SRC_DIR / name for name in SHARED_FILES]
    return standalone, shared


def validate_fragment_contract(standalone_files, shared_files):
    """Reject wrapper mistakes before they can corrupt the assembled location."""
    problems = []
    for path in standalone_files:
        text = path.read_text(encoding="utf-8")
        if not re.search(r"(?m)^#\s+\S+", text):
            problems.append(f"{path.name} is standalone but has no location header")
        if not re.search(r"(?m)^---\s+\S+", text):
            problems.append(f"{path.name} is standalone but has no location footer")
    for path in shared_files:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if re.match(r"^(#|---)\s", line):
                problems.append(f"{path.name}:{lineno} is shared but contains a location wrapper")
    if problems:
        raise ValueError("Fragment contract failed:\n  - " + "\n  - ".join(problems))


def extract_route_definitions(text):
    return set(re.findall(r"\$ARGS\[0\]\s*=\s*'([^']+)'", text))


def validate_route_definitions(text):
    """Reject duplicate simple handlers while allowing shared setup guards."""
    simple_routes = re.findall(r"(?m)^if \$ARGS\[0\]\s*=\s*'([^']+)':\s*$", text)
    duplicates = sorted(route for route in set(simple_routes) if simple_routes.count(route) > 1)
    if duplicates:
        raise ValueError("Duplicate simple route definitions: " + ", ".join(duplicates))


def extract_route_calls(text):
    return set(re.findall(r"(?:gt|gs)\s+'{1,2}mod_GLQS_main'{1,2}\s*,\s*'{1,2}([^']+)'{1,2}", text))


def validate_route_coverage(text):
    """Catch renamed/missing shared routes, including routes embedded in HTML."""
    definitions = extract_route_definitions(text)
    calls = extract_route_calls(text)
    missing = sorted(calls - definitions)
    if missing:
        raise ValueError("Routes are called but not defined in mod_GLQS_main: " + ", ".join(missing))
    unreferenced = sorted(definitions - calls)
    if unreferenced:
        print("Route coverage note: no static mod_GLQS_main call for " + ", ".join(unreferenced))


def validate_navigation_registry(text, route_definitions=None):
    """Ensure the text-link and action-button renderers use the same entries."""
    entries = re.findall(r"\$glqs_nb\[glqs_nb_n\]\s*=\s*'([^|']+)\|([^']+)'", text)
    action_entries = re.findall(
        r"if \$glqs_current <> '([^']+)':\s*act '([^']+)': gt 'mod_GLQS_main', '([^']+)'",
        text,
    )
    action_pairs = [(key, label) for key, label, route in action_entries if key != "start" if key == route]
    registry_pairs = [(key, label) for key, label in entries]
    if registry_pairs != action_pairs:
        raise ValueError("Navigation registry and action-button entries differ. Update the shared registry and renderer together.")
    if route_definitions is not None:
        missing = sorted({key for key, _ in registry_pairs} - route_definitions)
        if missing:
            raise ValueError("Navigation entries have no route definitions: " + ", ".join(missing))


def validate_navigation_template(text):
    """Ensure the source marker is present exactly once before expansion."""
    if text.count(NAVIGATION_BEGIN) != 1 or text.count(NAVIGATION_END) != 1:
        raise ValueError(f"{NAVIGATION_FILE} must contain exactly one navigation marker pair")
    entries = re.findall(r"\$glqs_nb\[glqs_nb_n\]\s*=\s*'([^|']+)\|([^']+)'", text)
    if not entries:
        raise ValueError(f"{NAVIGATION_FILE} contains no navigation entries")


def extract_recurrent_menu(text):
    """The recurrent menu body, delimited by the bulk handler that follows it."""
    match = re.search(
        r"if \$ARGS\[0\] = 'recurrent':(.*?)if \$ARGS\[0\] = 'recurrent_set':",
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("Recurrent menu route is missing")
    return match.group(1)


def validate_recurrent_bulk_handlers(text):
    """Keep every toggle the primary table renders covered by recurrent_set.
    The old recurrent_on/recurrent_off pair also needed a check that both
    halves assigned the same keys; one parameterised route makes that kind of
    mismatch impossible, so only the menu-vs-handler coverage check remains."""
    primary_table = extract_recurrent_menu(text).split("$glqs_tbl2 =", 1)[0]
    rendered = set(re.findall(r"cheatVars\['([^']+)'\]\s*=\s*iif", primary_table))
    handler = re.search(
        r"if \$ARGS\[0\] = 'recurrent_set':(.*?)(?=\nif \$ARGS\[0\] = |\Z)",
        text,
        flags=re.DOTALL,
    )
    if not handler:
        raise ValueError("Recurrent bulk handler (recurrent_set) is missing")
    assigned = set(re.findall(r"cheatVars\['([^']+)'\]\s*=", handler.group(1)))
    missing = sorted(rendered - assigned)
    if missing:
        raise ValueError("Recurrent menu toggles missing from recurrent_set: " + ", ".join(missing))


def validate_recurrent_toggle_contract(text):
    """Keep individually rendered cheat variables paired with their states."""
    individual = extract_recurrent_menu(text).split("$glqs_tbl2 =", 1)
    if len(individual) != 2:
        raise ValueError("Recurrent individual-toggle table is missing")
    table = individual[1]
    direct_keys = set(re.findall(r"cheatVars\[''([^']+)'\]\s*=\s*iif", table))
    displayed_keys = set(re.findall(r"iif\(cheatVars\[''([^']+)'\]", table))
    if direct_keys - displayed_keys:
        raise ValueError("Recurrent individual toggles missing displayed state: " + ", ".join(sorted(direct_keys - displayed_keys)))


def expand_navigation_actions(text):
    """Generate literal QSP actions from the single navigation registry."""
    validate_navigation_template(text)
    entries = re.findall(r"\$glqs_nb\[glqs_nb_n\]\s*=\s*'([^|']+)\|([^']+)'", text)
    generated = "\n".join(
        f"\t\tif $glqs_current <> '{key}': act '{label}': gt 'mod_GLQS_main', '{key}'"
        for key, label in entries
    )
    pattern = re.escape(NAVIGATION_BEGIN) + r".*?" + re.escape(NAVIGATION_END)
    return re.sub(pattern, f"{NAVIGATION_BEGIN}\n{generated}\n\t\t{NAVIGATION_END}", text, count=1, flags=re.DOTALL)


def expand_clothing_store(text, catalog_text, menu_text):
    rows = re.findall(r"\$glqs_cc\[glqs_cc_n\]\s*=\s*'([^|']+)\|([^|']+)\|([^|']+)\|([^']+)'", catalog_text)
    if not rows:
        raise ValueError("Clothing catalog contains no labeled rows")
    picker_rows = {(store, kind, key): label for store, kind, key, label in rows}
    label_rows = re.findall(r"act '([^']+)': gt 'mod_GLQS_main', 'store_detail', '([^']+)'", menu_text)
    labels = {store: label for label, store in label_rows}
    missing_labels = sorted({store for store, _, _, _ in rows} - labels.keys())
    if missing_labels:
        raise ValueError("Clothing stores missing menu labels: " + ", ".join(missing_labels))

    generated_labels = "\n".join(
        f"\tif $glqs_store = '{store}': $glqs_label = '{labels[store]}'"
        for store in labels
        if store in {row[0] for row in rows}
    )
    generated_actions = []
    for store in labels:
        store_rows = [row for row in rows if row[0] == store]
        if not store_rows:
            continue
        generated_actions.append(f"\tif $glqs_store = '{store}':")
        generated_actions.extend(
            f"\t\tact '{label}': gt 'mod_GLQS_main', 'item_picker', '{kind}', '{key}', '{store}', '{label}'"
            for _, kind, key, label in store_rows
        )
        generated_actions.append("\tend")
    generated_actions = "\n".join(generated_actions)

    def replace_markers(source, begin, end, body):
        if source.count(begin) != 1 or source.count(end) != 1:
            raise ValueError(f"Clothing store must contain one {begin}/{end} pair")
        pattern = re.escape(begin) + r".*?" + re.escape(end)
        return re.sub(pattern, f"{begin}\n{body}\n\t{end}", source, count=1, flags=re.DOTALL)

    text = replace_markers(text, CLOTHING_LABELS_BEGIN, CLOTHING_LABELS_END, generated_labels)
    return replace_markers(text, CLOTHING_ACTIONS_BEGIN, CLOTHING_ACTIONS_END, generated_actions)


def assemble(standalone_files, shared_files):
    parts = []
    for f in standalone_files:
        parts.append(f.read_text(encoding="utf-8"))

    parts.append(f"# {SHARED_LOCATION_NAME}\n")
    for f in shared_files:
        text = f.read_text(encoding="utf-8")
        if f.name == NAVIGATION_FILE:
            text = expand_navigation_actions(text)
        # Probe for the marker rather than the filename. Gating this on
        # f.name == "05_clothing_store.qsps" meant renaming that file (and
        # dutifully updating SHARED_FILES) silently skipped the expansion:
        # the markers survived as inert comments, the item picker assembled
        # with 0 of its 82 actions, and every validator and lint still
        # passed. lint_unexpanded_markers now catches that too.
        if CLOTHING_ACTIONS_BEGIN in text:
            catalog = (SRC_DIR / "05_clothing_data.qsps").read_text(encoding="utf-8")
            menu = (SRC_DIR / "05_clothing.qsps").read_text(encoding="utf-8")
            text = expand_clothing_store(text, catalog, menu)
        parts.append(text)
    parts.append(f"--- {SHARED_LOCATION_NAME} ---------------------------------\n")
    return "\n".join(p.rstrip("\n") + "\n" for p in parts)


def extract_consumable_metadata(text):
    return re.findall(
        r"\$glqs_con_kind\[glqs_con_n\]\s*=\s*'([^']+)'.*?"
        r"\$glqs_con_category\[glqs_con_n\]\s*=\s*'([^']*)'.*?"
        r"\$glqs_con_label\[glqs_con_n\]\s*=\s*'([^']*)'.*?"
        r"\$glqs_con_key\[glqs_con_n\]\s*=\s*'([^']+)'",
        text,
    )


def validate_recurrent_metadata(text):
    """Validate the documented recurrent control roles and coverage."""
    match = re.search(
        r"!! RECURRENT_METADATA_BEGIN(.*?)!! RECURRENT_METADATA_END",
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("Recurrent metadata markers are missing")
    rows = re.findall(r"!! (bulk|special|individual)\|([^|]+)\|([^\n]+)", match.group(1))
    if not rows:
        raise ValueError("Recurrent metadata table is empty")
    keys = [key for _, key, _ in rows]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError("Duplicate recurrent metadata keys: " + ", ".join(duplicates))
    menu = extract_recurrent_menu(text)
    missing = sorted(
        key for role, key, _ in rows
        if key not in menu
    )
    if missing:
        raise ValueError(
            "Recurrent metadata keys missing from menu: "
            + ", ".join(missing)
        )


def validate_consumable_metadata(text):
    rows = extract_consumable_metadata(text)
    if not rows:
        raise ValueError("Consumable metadata table is empty")
    kinds = {"quantity", "toggle", "bulk", "unique"}
    invalid = sorted({kind for kind, _, _, _ in rows} - kinds)
    if invalid:
        raise ValueError("Consumable metadata has unknown roles: " + ", ".join(invalid))
    incomplete = [
        f"row {index + 1}"
        for index, (_, category, label, key) in enumerate(rows)
        if not category or not label or not key
    ]
    if incomplete:
        raise ValueError("Consumable metadata has incomplete rows: " + ", ".join(incomplete))
    duplicates = sorted(
        f"{kind}:{key}"
        for kind, key in {(kind, key) for kind, _, _, key in rows}
        if sum(1 for row_kind, _, _, row_key in rows if row_kind == kind and row_key == key) > 1
    )
    if duplicates:
        raise ValueError("Consumable metadata has duplicate role/key pairs: " + ", ".join(duplicates))


def extract_job_ids(text):
    return re.findall(r"\$glqs_jb\[glqs_jb_n\]\s*=\s*'([^|']+)\|", text)


def extract_reference_job_ids(text):
    return re.findall(r"if \$ARGS\[0\]\s*=\s*'([^']+)':", text)


def validate_job_ids(text, reference_text=None):
    """Keep the mod's job manifest aligned with the base game when available.
    We validate against the nightly reference if present, and otherwise do a
    repository-local sanity check so the script still catches malformed or
    duplicated IDs without depending on an external checkout."""
    job_ids = extract_job_ids(text)
    if not job_ids:
        raise ValueError("Job ID table is empty")

    duplicates = sorted({job_id for job_id in job_ids if job_ids.count(job_id) > 1})
    if duplicates:
        raise ValueError("Duplicate job IDs: " + ", ".join(duplicates))

    malformed = sorted(job_id for job_id in job_ids if not re.fullmatch(r"[A-Za-z0-9_]+", job_id))
    if malformed:
        raise ValueError("Malformed job IDs: " + ", ".join(malformed))

    if reference_text is not None:
        reference_ids = extract_reference_job_ids(reference_text)
        missing = sorted(set(reference_ids) - set(job_ids))
        extra = sorted(set(job_ids) - set(reference_ids))
        if missing or extra:
            error = "Job ID mismatch against canonical reference:"
            if missing:
                error += " missing=" + ", ".join(missing)
            if extra:
                error += "; extra=" + ", ".join(extra)
            raise ValueError(error)

    return sorted(set(job_ids))


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


def lint_unbalanced_template_markers(text):
    """<< >> template markers must open and close inside the same single-quoted
    string literal -- they cannot span a '+' concatenation. Both compile fine
    with qsp-cli (which never executes the code) and only fail in-game with
    a 'Bracket not found' error. This scans every single-quoted literal in the
    whole file (respecting QSP's '' escape), not line-by-line -- a literal
    that itself spans multiple physical lines has no complete match on either
    of its lines individually, so a per-line scan silently misses it. Flags
    any literal where << and >> counts don't match, reporting the line the
    literal starts on."""
    problems = []
    literal_re = re.compile(r"'(?:[^']|'')*'")
    for m in literal_re.finditer(text):
        literal = m.group(0)
        if literal.count("<<") != literal.count(">>"):
            lineno = text.count("\n", 0, m.start()) + 1
            line = text.splitlines()[lineno - 1]
            problems.append((lineno, line))
    return problems


def lint_empty_template_markers(text):
    """'<< >>' (nothing but whitespace between the markers) is always invalid
    QSP -- typically typed as literal text describing the << >> syntax
    itself (e.g. in a changelog string) rather than intended as real
    interpolation. Compiles fine with qsp-cli, fails in-game with a plain
    'Syntax error'. Matched against the whole file rather than line-by-line
    so a marker pair split across a multi-line literal is still caught."""
    problems = []
    empty_re = re.compile(r"<<\s*>>")
    for m in empty_re.finditer(text):
        lineno = text.count("\n", 0, m.start()) + 1
        line = text.splitlines()[lineno - 1]
        problems.append((lineno, line))
    return problems


def lint_unexpanded_markers(text):
    """Every GLQS_*_BEGIN/END pair in the assembled output is a placeholder a
    build-time expansion is meant to fill. If the expansion never runs, the
    markers survive as inert QSP comments with nothing between them, and
    nothing else notices -- every other validator and lint passes and the
    build prints SUCCESS. That is how an item picker with 0 of its 82 actions
    could be produced by renaming one source file. An empty body is a build
    failure, not a warning."""
    problems = []
    pattern = re.compile(
        r"^[ \t]*!! (GLQS_\w+)_BEGIN[ \t]*\r?$(.*?)^[ \t]*!! \1_END",
        re.DOTALL | re.MULTILINE,
    )
    for match in pattern.finditer(text):
        if not match.group(2).strip():
            lineno = text[: match.start()].count("\n") + 1
            problems.append((lineno, match.group(1)))
    return problems


def lint_numeric_arg_from_string_slot(text):
    """QSP keeps each argument's numeric and string value in separate slots, and
    the base game has to choose between them explicitly -- see the
    iif(modARGS[0]=0, $modARGS[0], modARGS[0]) dispatch in mod_system.qsrc.
    Assigning a plain (numeric) variable from $ARGS[n] therefore reads the
    string slot, which is empty whenever the caller passed a number, so the
    variable silently becomes 0 instead of erroring. This shipped twice: once as
    glqs_ip_idx = $ARGS[3] in item_grant, and again in v0.36.1 when the clothing
    refactor reintroduced it at both item_pick and item_grant while this lint
    was not yet on this branch. Every clothing grant wrote to array index 0, no
    item was ever added, and nothing reported a problem.
    Use ARGS[n] for a number, or val($ARGS[n]) if the caller genuinely sends a
    numeric string."""
    problems = []
    assignment = re.compile(r"^\s*[a-z_][a-z0-9_]*\s*=\s*\$ARGS\[\d+\]")
    for i, line in enumerate(text.splitlines(), start=1):
        if assignment.match(line):
            problems.append((i, line))
    return problems


def lint_version_mismatch(text):
    """$mod_info[1] (01_setup.qsps, shown on the game's mod-selection screen) and
    the top changelog entry (02_readme.qsps, shown on the in-game readme screen)
    encode the same version independently and must be bumped together. Nothing
    else catches drift between them -- it compiles fine and only shows up as the
    wrong version displayed in one of the two places in-game. Returns None if
    they agree, else (mod_info_version, changelog_version) as 'X.Y.Z' strings."""
    mod_info_match = re.search(r"\$mod_info\[1\]\s*=\s*'(\d)(\d{2})(\d{2})'", text)
    changelog_match = re.search(
        r"'<b>Version (\d+)\.(\d+)(?:\.(\d+))?\s*(?:-\s*Current)?</b>'", text
    )
    if not mod_info_match or not changelog_match:
        return None

    mi_major, mi_minor, mi_patch = mod_info_match.groups()
    mod_info_version = f"{int(mi_major)}.{int(mi_minor)}.{int(mi_patch)}"

    cl_major, cl_minor, cl_patch = changelog_match.groups()
    changelog_version = f"{int(cl_major)}.{int(cl_minor)}.{int(cl_patch or 0)}"

    if mod_info_version != changelog_version:
        return (mod_info_version, changelog_version)
    return None


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

    template_hits = lint_unbalanced_template_markers(text)
    if template_hits:
        ok = False
        print("\n[LINT] Unbalanced << >> template markers inside a string literal:")
        print("       (<< and >> must open/close in the same literal -- they can't")
        print("        span a '+' concatenation)")
        for lineno, line in template_hits:
            print(f"    line {lineno}: {line.strip()}")

    empty_template_hits = lint_empty_template_markers(text)
    if empty_template_hits:
        ok = False
        print("\n[LINT] Empty << >> template markers found:")
        print("       (nothing between << and >> is always invalid QSP -- if you")
        print("        meant to describe the << >> syntax as plain text, add a")
        print("        space or word between them so QSP doesn't parse it as a")
        print("        marker, e.g. '<< >>' -> '<<  >>' won't help; rephrase instead)")
        for lineno, line in empty_template_hits:
            print(f"    line {lineno}: {line.strip()}")

    depth, stack = lint_block_balance(text)
    if depth != 0:
        ok = False
        print(f"\n[LINT] if/act/end block imbalance -- final depth {depth} (should be 0)")
        print("       Unclosed blocks (most likely culprits):")
        for lineno, snippet in stack:
            print(f"    line {lineno}: {snippet}")

    marker_hits = lint_unexpanded_markers(text)
    if marker_hits:
        ok = False
        print("\n[LINT] Build-time marker block was never expanded:")
        print("       (the BEGIN/END pair is still empty, so the generated")
        print("        actions are missing -- check the expansion gate in")
        print("        assemble() still matches this file)")
        for lineno, name in marker_hits:
            print(f"    line {lineno}: {name}_BEGIN/_END is empty")

    arg_slot_hits = lint_numeric_arg_from_string_slot(text)
    if arg_slot_hits:
        ok = False
        print("\n[LINT] Numeric variable assigned from the string argument slot:")
        print("       ($ARGS[n] is empty when the caller passed a number, so the")
        print("        variable silently becomes 0 -- use ARGS[n], or val($ARGS[n])")
        print("        if the caller really sends a numeric string)")
        for lineno, line in arg_slot_hits:
            print(f"    line {lineno}: {line.strip()}")

    version_mismatch = lint_version_mismatch(text)
    if version_mismatch:
        ok = False
        mod_info_version, changelog_version = version_mismatch
        print("\n[LINT] Version mismatch between mod_info and changelog:")
        print(f"       01_setup.qsps $mod_info[1] says {mod_info_version}")
        print(f"       02_readme.qsps top changelog entry says {changelog_version}")
        print("       Bump both together -- $mod_info[1] drives the version shown")
        print("       on the game's mod-selection screen, the changelog entry drives")
        print("       the in-game readme screen, and nothing else keeps them in sync.")

    return ok

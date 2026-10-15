"""IIF calls whose branches have side effects or cost (5.7 evaluates both
branches), and the two boolean return conventions.

usage: gliif.py <locations dir>
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qsrc_mask import code_mask  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
root = sys.argv[1]


def split_args(text, start):
    """text[start] is just after 'iif('. Returns top-level argument strings."""
    args, depth, quote, buf = [], 0, None, []
    i = start
    while i < len(text):
        c = text[i]
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
            buf.append(c)
        elif c in "([":
            depth += 1
            buf.append(c)
        elif c in ")]":
            if depth == 0:
                args.append("".join(buf))
                return args
            depth -= 1
            buf.append(c)
        elif c == "," and depth == 0:
            args.append("".join(buf))
            buf = []
        else:
            buf.append(c)
        i += 1
    return args


def strip_strings(s):
    return re.sub(r"'[^']*'|\"[^\"]*\"", "''", s)


calls = with_func = with_rand = 0
norm = raw = 0
examples = {"func": [], "rand": []}
for f in sorted(os.listdir(root)):
    if not f.endswith(".qsrc"):
        continue
    text = open(os.path.join(root, f), encoding="utf-8-sig").read()
    mask = code_mask(text)
    for m in re.finditer(r"\biif\s*\(", text, re.I):
        if mask[m.start()]:
            continue
        calls += 1
        args = split_args(text, m.end())
        if len(args) != 3:
            continue
        branches = strip_strings(args[1] + " " + args[2]).lower()
        line = text.count("\n", 0, m.start()) + 1
        if re.search(r"\$?func\s*\(", branches):
            with_func += 1
            examples["func"].append(f"{f}:{line}")
        if re.search(r"\brand\s*\(", branches):
            with_rand += 1
            examples["rand"].append(f"{f}:{line}")
        if re.fullmatch(r"\s*1\s*", args[1]) and re.fullmatch(r"\s*0\s*", args[2]):
            norm += 1
    for m in re.finditer(r"^[ \t]*result[ \t]*=[ \t]*\(", text, re.I | re.M):
        if not mask[m.end() - 1]:
            raw += 1
print("iif calls outside strings:", calls)
print("iif with func() in a branch:", with_func, examples["func"][:5])
print("iif with rand() in a branch:", with_rand, examples["rand"][:5])
print("iif(cond, 1, 0):", norm)
print("result = ( ... ) statements:", raw)

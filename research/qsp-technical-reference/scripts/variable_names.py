"""Variable names Girl Life assigns by literal name, and two checks on them:

1. Hash bucket load under the 5.7 table (256 buckets x 50 slots, 8-bit Pearson
   hash, legacy src/variables.c:149-185) and the 5.9.5 global table (512 chained
   buckets, at most 32 names each, h = h*31 + low byte starting at 7,
   engine-5.9.5 qsp/variables.c:86-93, :393).
2. (name, literal index) pairs assigned both as a string and as a number.

An assignment is NAME[index] op= at the start of a statement (line start, after
'&' or after a ':' that ends an IF/ACT header), outside strings, {} blocks and
comments. Names built at run time (dynamic, setvar, copyarr) are not seen.

usage: variable_names.py <locations dir> <qsp-legacy src/variables.c>
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qsrc_mask import code_mask  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
root, legacy_variables_c = sys.argv[1], sys.argv[2]

# the Pearson table qspRand8[256] that 5.7 uses to hash variable names
_src = open(legacy_variables_c, encoding="utf-8", errors="replace").read()
_table = _src[_src.index("qspRand8[256]"):]
RAND8 = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{2})", _table[:_table.index("};")])]
assert len(RAND8) == 256

ASSIGN = re.compile(
    r"(?:^|(?<=[&:]))[ \t]*(?:(?:set|let|local)[ \t]+)?([$#%]?)([A-Za-z_][A-Za-z0-9_.]*)"
    r"[ \t]*(\[[^\]\n]*\])?[ \t]*([-+*/]?=)(?!=)",
    re.M,
)
KEYWORDS = {"IF", "ELSEIF", "ELSE", "END", "ACT", "LOOP", "WHILE", "STEP", "AND", "OR", "NO", "MOD"}


def hash57(name):
    b = 0
    for ch in name:
        b = RAND8[b ^ (ord(ch) % 256)]
    return b


def hash595(name):
    h = 7
    for ch in name:
        h = (h * 31 + (ord(ch) & 0xFF)) & 0xFFFFFFFF
    return h % 512


names = set()
types = collections.defaultdict(set)
where = {}
for f in sorted(os.listdir(root)):
    if not f.endswith(".qsrc"):
        continue
    text = open(os.path.join(root, f), encoding="utf-8-sig").read()
    mask = code_mask(text)
    for m in ASSIGN.finditer(text):
        if mask[m.start(2)]:
            continue
        name = m.group(2).upper()
        if name in KEYWORDS:
            continue
        names.add(name)
        idx = re.sub(r"\s+", "", (m.group(3) or "").upper())
        kind = "str" if m.group(1) == "$" else "tuple" if m.group(1) == "%" else "num"
        types[(name, idx)].add(kind)
        where.setdefault((name, idx, kind), f"{f}:{text.count(chr(10), 0, m.start(2)) + 1}")

print("distinct names assigned by literal name:", len(names))
print("names assigned with a literal string key:",
      len({n for (n, i) in types if i.startswith("['") or i.startswith('["')}))
print("names assigned with a string variable key:",
      len({n for (n, i) in types if i.startswith("[$")}))
for label, fn, limit in (("5.7", hash57, 50), ("5.9.5", hash595, 32)):
    load = collections.Counter(fn(n) for n in names)
    top = load.most_common(3)
    over = sum(1 for v in load.values() if v > limit)
    print(f"{label}: fullest buckets {top}, limit {limit}, buckets over limit {over}")

dual = sorted(k for k, v in types.items() if {"str", "num"} <= v)
print("(name, index) pairs assigned both as string and number:", len(dual))
for name, idx in dual:
    print(f"  {name}{idx}: str at {where[(name, idx, 'str')]}, num at {where[(name, idx, 'num')]}")

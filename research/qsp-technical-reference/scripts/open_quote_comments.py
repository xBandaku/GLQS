"""Multi-line comment spans that continue past a line end because a quote is
still open there (as opposed to an open { block). These end where intended only
because a later quote happens to close the string."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qspprep
sys.stdout.reconfigure(encoding="utf-8")


def open_quote_lines(lines, a, b):
    # same scan order as qspprep.logical_lines: quotes are checked before braces
    quote = None
    code = 0
    hits = []
    for i in range(a, b):
        for ch in lines[i]:
            if quote:
                if ch == quote:
                    quote = None
                continue
            if ch in "'\"":
                quote = ch
                continue
            if ch == '{':
                code += 1
            elif ch == '}' and code:
                code -= 1
        if quote:
            hits.append(i + 1)
    return hits


root = sys.argv[1]
spans = 0
found = []
for f in sorted(os.listdir(root)):
    if not f.endswith('.qsrc'):
        continue
    text = open(os.path.join(root, f), encoding='utf-8-sig').read()
    lines, ll = qspprep.logical_lines(text)
    for a, b in ll:
        if b == a or not lines[a].strip().startswith('!'):
            continue
        spans += 1
        hits = open_quote_lines(lines, a, b)
        if hits:
            found.append((f, a + 1, b + 1, hits[:4]))
print('multi-line comment spans:', spans, '| continued by an open quote:', len(found))
for e in found:
    print(e)

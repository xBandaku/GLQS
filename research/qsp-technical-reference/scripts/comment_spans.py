import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qspprep
sys.stdout.reconfigure(encoding="utf-8")
root = sys.argv[1]; legacy = len(sys.argv) > 2 and sys.argv[2] == 'legacy'
cnt = collections.Counter(); acc = []
for f in sorted(os.listdir(root)):
    if not f.endswith('.qsrc'): continue
    text = open(os.path.join(root, f), encoding='utf-8-sig').read()
    lines, ll = qspprep.logical_lines(text, legacy)
    for a, b in ll:
        if b > a and lines[a].strip().startswith('!'):
            sw = [i for i in range(a+1, b+1) if lines[i].strip() and not lines[i].strip().startswith('!') and not lines[i].strip().startswith('}')]
            if not sw: continue
            kind = qspprep.classify(lines[a]); cnt[kind] += 1
            if kind == 'accidental': acc.append((f, a+1, b+1, len(sw), lines[a].strip()[:80], lines[sw[0]].strip()[:60]))
print(dict(cnt))
for x in acc: print(x)

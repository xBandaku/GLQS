import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
root = sys.argv[1]
pat = re.compile(r"^[ \t]*(?:if|elseif)[ \t]+\$args\[0\][ \t]*=[ \t]*'([^']*)'", re.I | re.M)
for name in sys.argv[2:]:
    t = open(os.path.join(root, name + '.qsrc'), encoding='utf-8-sig').read()
    found = []
    for m in pat.finditer(t):
        line = t.count('\n', 0, m.start()) + 1
        found.append(f"{m.group(1)}:{line}")
    print(f"== {name} ({t.count(chr(10))} lines)")
    print(' '.join(found))

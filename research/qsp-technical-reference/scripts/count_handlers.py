import os, re, sys
root = sys.argv[1]
pat_s = re.compile(r"^\s*if\s+\$args\[0\]\s*=\s*'", re.I | re.M)
pat_d = re.compile(r"^\s*if\s+\$args\[0\]\s*=\s*''\s*:", re.I | re.M)
pat_n = re.compile(r"^\s*(if|elseif)\s+args\[0\]\s*=\s*\d", re.I | re.M)
h = files = d = n = 0
for f in os.listdir(root):
    if not f.endswith('.qsrc'): continue
    t = open(os.path.join(root, f), encoding='utf-8-sig').read()
    c = len(pat_s.findall(t)); h += c; files += c > 0
    d += len(pat_d.findall(t)); n += len(pat_n.findall(t))
print('string handlers', h, 'in files', files, '| default (empty) handlers', d, '| numeric ARGS[0] branches', n)

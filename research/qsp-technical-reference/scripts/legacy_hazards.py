import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qspprep
def split_top(line):
    """yield (index, char) for chars outside quotes and brackets"""
    q=None; d=0
    for i,c in enumerate(line):
        if q:
            if c==q: q=None
            continue
        if c in "'\"": q=c; continue
        if c in '([{': d+=1; continue
        if c in ')]}': d=max(0,d-1); continue
        if d==0: yield i,c
root=sys.argv[1]
hdr=[]; inl=[]
for f in sorted(os.listdir(root)):
    if not f.endswith('.qsrc'): continue
    text=open(os.path.join(root,f),encoding='utf-8-sig').read()
    lines, ll = qspprep.logical_lines(text, legacy=True)
    for a,b in ll:
        line=' '.join(lines[a:b+1]).strip()
        low=line.lower()
        if low.startswith('!') or not low: continue
        m=re.match(r'(if|elseif|else\s+if|else|act|loop)\b', low)
        if not m: continue
        # find first top-level colon
        colon=None
        for i,c in split_top(line):
            if c==':': colon=i; break
        if m.group(1) in ('if','elseif','else if','act') and colon is not None:
            rest=line[colon+1:].strip()
            if rest.startswith('!'):
                hdr.append((f,a+1,line[:90]))
            if m.group(1)=='if':
                # inline elseif in single-line if
                if rest and not rest.startswith('!') and re.search(r'(?i)(^|[\s&])elseif\b', rest):
                    inl.append((f,a+1,line[:110]))
        elif m.group(1)=='else' and colon is None:
            rest=line[4:].strip()
            if rest.startswith('!'): hdr.append((f,a+1,line[:90]))
print('multi-line headers followed by a comment (single-line on 5.7):', len(hdr))
for x in hdr[:25]: print('  ',x)
print('single-line IF with inline ELSEIF (fails on 5.7):', len(inl))
for x in inl[:25]: print('  ',x)

import os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
root = sys.argv[1]
STATS = ['act','addobj','cla','clear','clr','*clear','*clr','close','cls','cmdclear','cmdclr','copyarr','delact','delobj','dynamic','else','elseif','end','exit','freelib','gosub','gs','goto','gt','if','inclib','addqst','killqst','jump','killall','killobj','killvar','let','local','loop','menu','msg','nl','*nl','opengame','openqst','p','*p','pl','*pl','play','refint','savegame','set','settimer','showacts','showinput','showobjs','showstat','unsel','unselect','view','wait','xgoto','xgt','modobj','resetobj','sortarr','scanstr','setvar','unpackarr','exec']
FUNCS = ['arrcomp','arritem','arrpack','arrpos','arrsize','arrtype','countobj','curacts','curloc','curobjs','desc','dyneval','func','getobj','iif','input','instr','isnum','isplay','lcase','len','maintxt','max','mid','min','msecscount','qspver','rand','replace','rgb','rnd','selact','selobj','stattxt','str','strcomp','strfind','strpos','trim','ucase','user_text','usrtxt','val','loc','obj','no','and','or','mod']
SYSVARS = ['args','result','usehtml','bcolor','fcolor','lcolor','fsize','fname','backimage','counter','onactsel','ongload','ongsave','onnewloc','onobjadd','onobjdel','onobjsel','usercom','debug','disablescroll','disablesubex','nosave']
def strip(code):
    out=[]; i=0; n=len(code); q=None; depth=0; comment=False; stmt_start=True
    while i<n:
        c=code[i]
        if q:
            if c==q:
                if i+1<n and code[i+1]==q: i+=2; continue
                q=None
            i+=1; continue
        if depth:
            if c=='{': depth+=1
            elif c=='}': depth-=1
            i+=1; continue
        if c in "'\"": q=c; out.append(' "S" '); i+=1; continue
        if c=='{': depth=1; out.append(' {C} '); i+=1; continue
        if comment:
            if c=='\n': comment=False; stmt_start=True; out.append('\n')
            i+=1; continue
        if c=='!' and stmt_start: comment=True; i+=1; continue
        if c=='\n' or c=='&': stmt_start=True
        elif c not in ' \t:': stmt_start=False
        if c==':' : stmt_start=True
        out.append(c); i+=1
    return ''.join(out)
cnt=collections.Counter(); files=collections.Counter(); total_lines=0; raw_strings=collections.Counter()
for dp,_,fs in os.walk(root):
    for f in fs:
        if not f.endswith('.qsrc'): continue
        t=open(os.path.join(dp,f),encoding='utf-8-sig').read()
        total_lines+=t.count('\n')
        raw_strings['exec:']+=len(re.findall(r'href\s*=\s*["\']?exec:',t,re.I))
        raw_strings['<<']+=t.count('<<')
        raw_strings['<a href']+=len(re.findall(r'<a\s+href',t,re.I))
        raw_strings['<img']+=len(re.findall(r'<img',t,re.I))
        s=strip(t).lower()
        seen=set()
        for kw in STATS:
            pat = (r'(?<![\w$%#.])' + re.escape(kw) + r'(?![\w])') if not kw.startswith('*') else re.escape(kw)+r'(?![\w])'
            c=len(re.findall(r'(?:^|[\n&:])\s*'+pat if kw not in ('else','elseif','end','and','or') else pat, s))
            if c: cnt['stat:'+kw]+=c; seen.add('stat:'+kw)
        for kw in FUNCS:
            c=len(re.findall(r'(?<![\w.])[$%#]?'+kw+r'(?![\w])', s))
            if c: cnt['func:'+kw]+=c; seen.add('func:'+kw)
        for kw in SYSVARS:
            c=len(re.findall(r'(?<![\w.])[$%#]?'+kw+r'(?![\w])', s))
            if c: cnt['var:'+kw]+=c; seen.add('var:'+kw)
        for k in seen: files[k]+=1
print('total lines', total_lines)
for k,v in sorted(cnt.items(), key=lambda x:-x[1]): print(f'{k:22} {v:7}  files={files[k]}')
print(raw_strings)

"""Re-implementation of qspPreprocessData line joining (QSPFoundation/qsp codetools.c,
5.9.x) and of the legacy 5.7 rules (quotes and {} only), used to find comments whose
logical line spans several physical lines."""
import os, sys, re
sys.stdout.reconfigure(encoding="utf-8")

def logical_lines(text, legacy=False):
    lines = text.split('\n')
    out = []
    buf_start = None
    quote = None; code = 0; rnd = 0; sq = 0
    is_comment = False; stmt_start = True
    start_line = 0
    for idx, line in enumerate(lines):
        if buf_start is None:
            buf_start = idx
            is_comment = False; stmt_start = True
        for ch in line:
            if quote:
                if ch == quote: quote = None  # doubled quotes reopen on next char, net effect identical
                continue
            if ch in "'\"":
                quote = ch; stmt_start = False; continue
            if code:
                if ch == '{': code += 1
                elif ch == '}': code -= 1
                continue
            if ch == '{':
                code = 1; stmt_start = False; continue
            if legacy or is_comment:
                if ch == '!' and stmt_start and not is_comment:
                    is_comment = True; stmt_start = False
                elif not is_comment:
                    if ch == '&': stmt_start = True
                    elif ch not in ' \t': stmt_start = False
                continue
            if ch == '!' and stmt_start:
                is_comment = True; stmt_start = False
            elif ch == '&': stmt_start = (rnd == 0 and sq == 0)
            elif ch == '(': rnd += 1; stmt_start = False
            elif ch == ')': rnd = max(0, rnd-1); stmt_start = False
            elif ch == '[': sq += 1; stmt_start = False
            elif ch == ']': sq = max(0, sq-1); stmt_start = False
            elif stmt_start and ch not in ' \t': stmt_start = False
        if not quote and not code and (legacy or (not rnd and not sq)):
            out.append((buf_start, idx))
            buf_start = None
    if buf_start is not None:
        out.append((buf_start, len(lines)-1))
    return lines, out

if __name__ == '__main__':
    root = sys.argv[1]; legacy = len(sys.argv) > 2 and sys.argv[2] == 'legacy'
    total = 0
    for f in sorted(os.listdir(root)):
        if not f.endswith('.qsrc'): continue
        text = open(os.path.join(root, f), encoding='utf-8-sig').read()
        lines, ll = logical_lines(text, legacy)
        for a, b in ll:
            if b > a:
                first = lines[a].strip()
                if first.startswith('!'):
                    # does the merged span include a physical line that is not itself a comment / blank?
                    swallowed = [i for i in range(a+1, b+1) if lines[i].strip() and not lines[i].strip().startswith('!') and not lines[i].strip().startswith('}')]
                    if swallowed:
                        total += 1
                        print(f"{f}:{a+1}-{b+1} swallows {len(swallowed)} non-comment line(s); first: {lines[swallowed[0]].strip()[:70]!r}")
    print('TOTAL comment spans swallowing code:', total)

def classify(first_line):
    """'intentional' if the comment's first non-'!'/space char opens a quote or brace."""
    s = first_line.strip().lstrip('!').lstrip(' \t')
    return 'intentional' if s[:1] in ("'", '"', '{') else 'accidental'

"""Shared scanner helper: which characters of a .qsrc text are inside a string,
a {} block or a comment."""


def code_mask(text):
    """True for each char inside a string, a {} block or a comment."""
    mask = [False] * len(text)
    quote = None
    depth = 0
    comment = False
    stmt_start = True
    for i, c in enumerate(text):
        if quote:
            mask[i] = True
            if c == quote:
                quote = None
            continue
        if depth:
            mask[i] = True
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            continue
        if comment:
            mask[i] = True
            if c == "\n":
                comment = False
                stmt_start = True
            continue
        if c in "'\"":
            quote = c
            mask[i] = True
            stmt_start = False
        elif c == "{":
            depth = 1
            mask[i] = True
            stmt_start = False
        elif c == "!" and stmt_start:
            comment = True
            mask[i] = True
        elif c in "\n&:":
            stmt_start = True
        elif c not in " \t":
            stmt_start = False
    return mask

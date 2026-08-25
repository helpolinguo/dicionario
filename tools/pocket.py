# -*- coding: utf-8 -*-
"""Dicionario de posho — a modern edition, in LaTeX.

This is not the facsimile: it is the CLEANED TEXT, that of the HTML page, set
as a pocket dictionary of today would be -- two columns, a running head
giving the first headword on the left and the last on the right, section
initials.

The source is the same file as the HTML page,
work/edicioni/dicionario.jsonl. The two editions therefore cannot diverge:
any correction laid in the proofreading layers is found in the one as in the
other at the next rebuild.
"""
import json, os, re, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edition
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT = _ROOT; T = f"{ROOT}/work"; OUT = f"{ROOT}/pocket"
SOURCE = f"{T}/edicioni/dicionario.jsonl"

# The typescript notes the languages by a letter; the reading edition writes
# them out. In the pocket edition there is no room: we return to the
# abbreviation, but a legible one.
ABBREV = {'Germana': 'D', 'Angla': 'E', 'Franca': 'F', 'Italiana': 'I',
          'Rusa': 'R', 'Hispana': 'S', 'Latina': 'L', 'Portugalana': 'P',
          'Greka': 'G', 'Nederlandana': 'N'}


def esc(t):
    """Text to LaTeX. The source contains guillemets, em dashes and non-breaking
    spaces that must be kept as they stand."""
    if t is None:
        return ""
    for a, b in (('\\', r'\textbackslash{}'), ('{', r'\{'), ('}', r'\}'),
                 ('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                 ('_', r'\_'), ('^', r'\textasciicircum{}'),
                 ('~', r'\textasciitilde{}')):
        t = t.replace(a, b)
    return t


def key_(v):
    """The sort key: the dictionary's own.

    `edition._klavo_ordino` is the BOOK's rule -- without the asterisk of the
    unofficial word, without the hyphen of the affix, without accents, without
    the exclamation mark of the interjection, without the quotation marks or
    the spaces: the book files « a posteriori » between « apostata » and
    « apostemo ». It is also the key on which the `ordino-ruptita` flag
    measures the disorder; the pocket sorting and the working list can no
    longer diverge.

    The local key of before knew neither quotation marks nor spaces:
    « "brokoli"-kaulo » filed itself AFTER « z », and the article was set right
    at the end of the book, behind « zumar » -- a hundred and fifty pages from
    its place. A hundred and one headwords changed rank that way: the affixes
    with a final hyphen, the interjections with an exclamation mark, and the
    Latin phrases.
    """
    return edition._order_key(v)


# A leading parenthesis containing only ONE letter or ONE figure is not a
# qualifier but an enumeration number -- « (a) », « (b) », « (1) ». It stays
# upright, and stops the series: in « (metaf.)(a) Profundegajo... », only
# « (metaf.) » takes the italic.
RE_HEAD = re.compile(r'^((?:\((?![a-zA-Z0-9]\))[^()]{1,120}\)\s*)+)')


START = "\ue000"; END = "\ue001"


def _bound_to(t):
    """The bounds the edition laid become LaTeX's italic.

    To be applied AFTER esc(): the backslash of \\textit would otherwise be
    escaped in its turn, and the command would print out in full.
    """
    return t.replace(START, "\\textit{").replace(END, "}")


def _italic(t):
    """Applied AFTER esc(): otherwise the backslash of \\textit would itself be
    escaped, and the command would print out in full.

    The LEADING parenthesis of a sense is a qualifier -- domain, period,
    register: « (aludante la hari...) », « (olim) », « (muziko) ». The
    article's domain is already in italic; this one must be too, or two marks
    of the same nature are written two ways in the same column."""
    if t.startswith("\\textit{"):
        return t
    m = RE_HEAD.match(t)
    if not m:
        return t
    # A chemical formula: « (CH\u2083)\u2082. CH... ». The italic would cut it
    # off from its subscript, and the space the command introduces would open a
    # gap between the parenthesis and the figure. We leave it upright and whole.
    if re.search(r'[\d\u2080-\u2089]', m.group(1)) or t[m.end():m.end()+1] in '\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089':
        return t
    return "\\textit{%s} %s" % (m.group(1).rstrip(), t[m.end():].lstrip())


def entry(e):
    """One article, in LaTeX."""
    v = e['vedetto']
    # A quoted borrowing: the typescript frames it in quotation marks. We render them.
    aff = "\u00ab\u00a0%s\u00a0\u00bb" % v if e.get('citita') else v
    L = ["\\vorto{%s}" % esc(aff)]
    if e.get('fako'):
        L.append("\\fako{%s}" % esc(e['fako']))
    B = e.get('strukt') or [{"teksto": t, "teksto_k": t, "sub": []}
                            for t in (e.get('senci') or [])]
    for i, b in enumerate(B):
        t = _bound_to(esc(b.get('teksto_k') or b.get('teksto') or ''))
        sub = b.get('sub') or []
        num = ""
        if len(B) > 1:
            if t: L.append("\\senco{%d}{%s}" % (i + 1, _italic(t)))
            else: num = str(i + 1)     # the number will go on the sub-entry
        elif t:
            L.append(" " + _italic(t))
        for j, x in enumerate(sub):
            code_ = ''.join(ABBREV.get(y, '') for y in (x.get('lingui') or []))
            L.append("\\subvorto{%s}{%s}{%s}{%s}{%s}" % (
                esc(x.get('fako') or ''), esc(x['loko']),
                _bound_to(esc(x.get('teksto_k') or x.get('teksto') or '')),
                num if j == 0 else "", esc(code_)))
    if e.get('simbolo'):
        L.append("\\simbolo{%s}" % esc(e['simbolo']))
    if e.get('latina'):
        L.append("\\latina{%s}" % esc('; '.join(e['latina'])))
    if e.get('lingui'):
        code = ''.join(ABBREV.get(x, '') for x in e['lingui'])
        if code:
            L.append("\\lingui{%s}" % esc(code))
    # The language code closes the article's definition, not its sub-entries:
    # thrown after them, it hung alone beneath an indented block and seemed to
    # belong to them. We raise it to the last piece that is the article's own.
    if any(x.startswith("\\subvorto") for x in L):
        queue = [x for x in L if x.startswith(("\\simbolo", "\\latina", "\\lingui"))]
        if queue:
            L = [x for x in L
                 if not x.startswith(("\\simbolo", "\\latina", "\\lingui"))]
            j = max((i for i, x in enumerate(L)
                     if not x.startswith("\\subvorto")), default=-1)
            L = L[:j+1] + queue + L[j+1:]
    return "\\artiklo{%s}%%\n" % esc(v) + "".join(L)


def write_(source=SOURCE, folder=OUT):
    os.makedirs(folder, exist_ok=True)
    ent = [json.loads(l) for l in open(source, encoding='utf-8')]
    ent.sort(key=lambda e: (key_(e['vedetto']), e['image'], e['ligno']))
    lines = []
    letter = None
    for e in ent:
        k = key_(e['vedetto'])
        c = k[0].upper() if k else '?'
        if c != letter and c.isalpha():
            if letter is not None:
                lines.append("\\end{multicols}")
            letter = c
            lines.append("\\sekciono{%s}" % c)
            lines.append("\\begin{multicols}{2}")
        lines.append(entry(e))
    if letter is not None:
        lines.append("\\end{multicols}")
    with open(f"{folder}/enhavo.tex", "w", encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    print("pocket/enhavo.tex : %d artikli, %d sekcioni"
          % (len(ent), sum(1 for l in lines if l.startswith("\\sekciono"))))
    return len(ent)


if __name__ == "__main__":
    write_()

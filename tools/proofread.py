# -*- coding: utf-8 -*-
"""A proofreading layer for the definitions, article by article.

The structural detectors are exhausted. What is left -- « vaormashino » for
« vapormashino », « fibranta » for « vibranta », « kuh » for « kun » -- can be
seen only by reading the sentence. The book is therefore cut into batches of
130 articles (tools/sheets_proofread.py), re-read one batch at a time, and the
corrections are deposited here.

The identifier the proofreading returns is NOT used to apply the correction.
It derives from the position in the file, and that position moves as soon as
an article is added -- the repair of the foot of the page added four. We
therefore look for the faulty string itself, and apply it only if it is UNIQUE
in the book: an ambiguous string is refused rather than laid at random. The
strings returned run to several words, which is enough to distinguish them.
"""
import os, re, glob
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = _ROOT + "/work"
FOLDER = f"{T}/relire/reponses"


def read_(folder=FOLDER):
    """Every correction returned: a list of (faulty, correct, batch)."""
    out = []
    for p in sorted(glob.glob(f"{folder}/*.txt")):
        batch = os.path.basename(p)[:-4]
        for l in open(p, encoding='utf-8'):
            l = l.rstrip("\n")
            if not l.strip() or l.startswith("#") or l.strip() == "RIEN":
                continue
            ch = l.split("\t")
            if len(ch) < 3:
                continue
            a, b = ch[-2].strip(), ch[-1].strip()
            # A proofreading sometimes returns a line of prose instead of a
            # correction -- « apofizo<TAB>... », « check done ». We refuse what
            # has not the form of a replacement: an ellipsis, an empty string,
            # or a target much shorter than the source.
            if not a or not b or a == b: continue
            if '...' in b or '…' in b: continue
            if len(b) < len(a) * 0.5: continue
            out.append((a, b, batch))
    return out


_SPACE = r"[\s\u00a0]*"

def _pattern(a):
    """Regex of the faulty string, indifferent to spacing."""
    out = []
    n = len(a)
    for i, c in enumerate(a):
        edge = (i == 0 or i == n - 1)
        if c.isspace():
            if out and out[-1] == _SPACE + "+":
                continue
            out.append(_SPACE + "+")
        elif c in "\u00ab\u00bb:;!?()":
            # At the EDGES of the string, do not absorb the neighbouring space: it
            # would not be returned by the replacement, and two words would stick
            # together.
            g = "" if i == 0 else _SPACE
            d = "" if i == n - 1 else _SPACE
            out.append(g + re.escape(c) + d)
        else:
            out.append(re.escape(c))
    return re.compile("".join(out))


def apply_(ent, folder=FOLDER):
    """Lays the proofreading corrections. Returns (laid, refused)."""
    corr_ = read_(folder)
    if not corr_:
        return 0, 0
    laid = 0; refused = 0
    for a, b, batch in corr_:
        # The faulty string was surveyed BEFORE the typography was laid: the
        # guillemets and the colon have since gained a non-breaking space,
        # « grande » is written « \u00ab\u00a0grande\u00a0\u00bb ». Sought to
        # the character, the correction was no longer found. We therefore make
        # the search indifferent to the spacing around the punctuation.
        word = _pattern(a)
        seen = []
        for e in ent:
            for k, t in enumerate(e.get('senci') or []):
                if word.search(t):
                    seen.append((e, k))
            # The domain is a separate field: « (ariktekt) » is in no sense, and
            # the correction was refused for want of looking there.
            #
            # The field is rendered in LOWER CASE (edition.minuskligi) whereas the
            # proofreading copies the page: « Yorocienco » under « prekara » was not
            # found in « yorocienco », and the correction -- the only one that bore
            # on that word -- was refused in silence. The comparison therefore
            # ignores case, on both sides.
            f = e.get('fako')
            if f and re.search(re.escape(a.strip('()')), f, re.I):
                seen.append((e, 'fako'))
        # The same slip is sometimes repeated identically -- « pseupodi » twice,
        # « di sapto » twice. To refuse it would be to lose a correct correction.
        # We therefore apply it everywhere, but ONLY if the string is
        # distinctive enough not to catch something else: at least six
        # characters, or several words. « lO », seen eleven times, stays refused.
        if not seen or (len(seen) > 1 and len(a) < 6 and ' ' not in a):
            refused += 1
            print("  relire %s : «%s» vu %d fois — refuse" % (batch, a[:40], len(seen)))
            continue
        for e, k in seen:
            if k == 'fako':
                e['fako'] = re.sub(re.escape(a.strip('()')),
                                   lambda _m: b.strip('()'), e['fako'], flags=re.I)
            else:
                e['senci'][k] = word.sub(lambda _m: b, e['senci'][k], count=1)
            laid += 1
    return laid, refused

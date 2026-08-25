"""Generating the LaTeX content files, one line of source per line of the book."""
import numpy as np, os, pickle, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
T=_ROOT + "/work"; ROOT=_ROOT


# --- the pages' layout, in millimetres ---------------------------------
HSTEP_MM = 2.540          # the machine's pitch: a tenth of an inch
VSTEP_MM = 4.321          # measured leading
WIDTH_MM, TOP_MM = 210.0, 297.0
ORIGX_MM, ORIGY_MM = 21.9, 12.44      # origin of the composed text area
# The block of text is laid in the same place on every page of the same hand.
# The longest line of the book is 190.5 mm on a sheet of 210: 19.5 mm of
# margins are left, which we share by giving more to the sewing side, where a
# work of 639 pages loses room to the binding.
# The block is set on the FORE-EDGE, and not on the sewing.
#
# It was set on the sewing until now: a fixed left margin, a free right edge.
# The left margins were therefore perfectly regular -- 13.5 mm on the recto,
# 8.0 mm on the verso -- but the right margins ran from 6 to 72 millimetres,
# since the right edge followed the longest line of the page. Open the book,
# and two facing pages had no edge in common.
#
# We now set on the outer side: the verso by its left, the recto by its right.
# The fore-edge margin is then the same everywhere, and all the play in the
# line lengths is thrown to the sewing side -- where it is welcome, a work of
# 640 pages losing a great deal of room to the binding.
OUTER_EDGE  = 8.0          # outer margin (fore-edge): the same on both hands
GUTTER_MIN = 12.0     # never less, on the sewing side
TOP_EDGE = 11.0         # head margin, the same everywhere
MARGIN_BOTTOM_MIN = 6.0
MARGIN_EXTREME = 3.0      # an absolute stop for the pages outside the norm

ESCAPES={'\\':r'\textbackslash{}', '{':r'\{', '}':r'\}', '%':r'\%', '#':r'\#',
       '_':r'\_', '&':r'\&', '$':r'\$', '^':r'\textasciicircum{}',
       '~':r'\textasciitilde{}', '"':r'\textquotedbl{}', "'":r'\textquotesingle{}',
       '<':r'\textless{}', '>':r'\textgreater{}', '|':r'\textbar{}'}
def esc(cells_of):
    """Escapes a RUN of cell contents. A content of more than one character
    beginning with a backslash is raw LaTeX (an overstrike, a composed
    character) and passes as it stands."""
    out=[]
    for c in cells_of:
        out.append(c if (len(c)>1 and c.startswith("\\")) else ESCAPES.get(c,c))
    return "".join(out)

_EXC=None
def exceptions():
    """Table (page, line, column) -> the reading adopted.

    Two files: `exceptions.txt`, written by the automatic correctors, and
    `exceptions_manual.txt`, arbitrated by eye. The second always prevails and
    is never rewritten by a program.
    """
    global _EXC
    if _EXC is None:
        _EXC={}
        for name_ in ("exceptions_ends.txt","exceptions_ornaments.txt","exceptions_pairs.txt","exceptions.txt","exceptions_proofreading.txt","exceptions_manual.txt"):
            p=os.path.join(T, name_)
            if not os.path.exists(p): continue
            for l in open(p, encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                a,b,c,v=l.split("\t")
                _EXC[(int(a),int(b),int(c))]=v
    return _EXC


_UNDERLINE=None
_STARTS=None
def starts_rendered():
    """First letters given back by restore_starts.py, by page."""
    global _STARTS
    if _STARTS is None:
        p=os.path.join(T,"starts.pkl")
        _STARTS=pickle.load(open(p,"rb")) if os.path.exists(p) else {}
    return _STARTS

_RULES=None
def fresh_rules():
    """Rules recomputed by redo_rules.py, by page."""
    global _RULES
    if _RULES is None:
        p=os.path.join(T,"rules.pkl")
        _RULES=pickle.load(open(p,"rb")) if os.path.exists(p) else {}
    return _RULES

def underlines_reread():
    """Underline ranges surveyed by eye, by (page, line).

    They replace the detected ranges entirely: the proofreader has seen the
    page, the detection only measures a rule whose baseline it places badly.
    """
    global _UNDERLINE
    if _UNDERLINE is None:
        _UNDERLINE={}
        p=os.path.join(T,"underlines_reread.txt")
        if os.path.exists(p):
            for l in open(p, encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                a,b,c=l.split("\t")
                _UNDERLINE[(int(a),int(b))]=[tuple(int(x) for x in seg.split("-"))
                                       for seg in c.split(",") if seg]
    return _UNDERLINE

def _trim(range_, cells_of):
    """Trims an underline range.

    The rule is measured to the pixel, but it happens to run over onto the next
    word by a cell or two. A rule does not underline an isolated letter at its
    end: we therefore subtract the groups of one or two cells separated from
    the body of the range by a space. Interior spaces are kept -- the
    typescript does underline « historio di Italia » with a single stroke. An
    isolated rule of one or two cells is noise.
    """
    a, b = range_
    n=len(cells_of)
    a=max(a,0); b=min(b,n-1)
    if b < a: return None
    grp=[]; i=a
    while i<=b:
        if cells_of[i]!=" ":
            j=i
            while j+1<=b and cells_of[j+1]!=" ": j+=1
            grp.append((i,j)); i=j+1
        else: i+=1
    if not grp: return None
    if len(grp)>1 and grp[-1][1]-grp[-1][0]+1 <= 2: grp=grp[:-1]
    if len(grp)>1 and grp[0][1]-grp[0][0]+1 <= 2: grp=grp[1:]
    if not grp: return None
    a2,b2 = grp[0][0], grp[-1][1]
    if b2-a2+1 <= 2 and len(grp)==1: return None
    return (a2,b2)

def page_lines(pg, lab, M, tab):
    z=np.load(f"{T}/cells/p-{pg:03d}.npz", allow_pickle=True)
    lg=z['lignes']; ncol=z['occ'].shape[1]
    underline=pickle.loads(z['sou'].item()) if 'sou' in z else {}
    # Recomputed rules: see tools/redo_rules.py. The original detection took the
    # aligned top serifs of the DEFIRS capitals for an underline, and referred
    # them to the line above. We do not rewrite the corpus of cells for all that
    # -- 295 MB, and one accident of format has already cost 144 pages: the
    # correction is a layer laid over it.
    new_ones=fresh_rules().get(pg)
    if new_ones: underline=new_ones
    from decode import smudges
    sel=np.where(M[:,0]==pg)[0]
    bv=smudges()[sel]
    per={}
    for (p,k,c),b,x in zip(M[sel], lab[sel], bv):
        per.setdefault(int(k),{})[int(c)]=" " if x else tab[b]
    # Line starts given back (see tools/restore_starts.py). They fall BEFORE
    # column zero: we shift the WHOLE PAGE by as many cells as are missing.
    # Shifting the one line concerned would set it one cell to the right of its
    # real place; by shifting everything, the relative positions are kept to the
    # character, and the block, whose margin is fixed elsewhere, falls in the
    # same place on the sheet.
    #
    # The shift is applied BEFORE the exceptions: those are surveyed by eye on
    # the shifted facsimile, hence already in the new numbering.
    beg=starts_rendered().get(pg)
    dec=0
    if beg:
        dec=-min(c for d0 in beg.values() for c in d0)
        per={k:{c+dec:v for c,v in d0.items()} for k,d0 in per.items()}
        underline={k:(yy,[(a+dec,b+dec) for a,b in pl],t) for k,(yy,pl,t) in underline.items()}
        ncol+=dec
        for k,d0 in beg.items():
            for c,ch in d0.items(): per.setdefault(int(k),{})[c+dec]=ch
    for (pp,kk,cc),v in exceptions().items():
        if pp==pg: per.setdefault(int(kk),{})[int(cc)]=v
    kmax=int(lg[:,0].max())
    # A correction can bear beyond the block: these are the line ends the
    # cutting had cut off. We widen the line to receive them, without having to
    # re-cut the page.
    for (pp,kk),d0 in list(per.items()) if False else []: pass
    for k,d0 in per.items():
        if d0: ncol=max(ncol, max(d0)+1)
    out=[]
    for k in range(kmax+1):
        d=per.get(k,{})
        s=[d.get(c," ") for c in range(ncol)]
        s=[(c if c not in ("", None) else " ") for c in s]
        ranges=[]
        reread = underlines_reread().get((pg,k))
        if reread is not None:
            # Surveyed by eye: we take it as it stands, with no merging and no
            # trimming -- those corrections aim precisely at putting right what the
            # automatic measurement had placed badly.
            ranges=[(a,b) for a,b in reread if b>=a]
        elif k in underline:
            yy,pl,tot=underline[k]
            ranges=sorted((a,b) for a,b in pl if b>=a)
            # The ribbon skips: a rule interrupted over one or two cells is still
            # the same rule. Two ranges separated by more than two cells, on the
            # other hand, are indeed two distinct underlines (« cinocefalo » and
            # « zool. » are three cells apart).
            fus=[]
            for a,b in ranges:
                if fus and a-fus[-1][1] <= 2: fus[-1]=(fus[-1][0], max(fus[-1][1],b))
                else: fus.append((a,b))
            ranges=[p for p in (_trim(p, s) for p in fus) if p]
            # Two rules set on 1,698 lines surveyed by eye: a rule neither begins
            # nor ends on an empty cell, and two stretches separated only by full
            # cells are the same rule, interrupted by the wear of the ribbon.
            f2=[]
            for a,b in ranges:
                if f2 and a-f2[-1][1] <= 3 and all(
                        (c < len(s) and s[c] != " ") for c in range(f2[-1][1]+1, a)):
                    f2[-1]=(f2[-1][0], b)
                else: f2.append((a,b))
            # Third rule: a rule does not begin in the middle of a word. The
            # detection produced « ritato » under « autoritato » and « as, » under
            # « esas, ». If the start is not at a word boundary -- a space, an
            # opening parenthesis, a quotation mark -- we bring it back to the start
            # of the word; and if the rule does not cover at least three fifths of
            # that word, it is noise and we throw it away.
            # The « + » that marks the unofficial headwords is a sign, not a letter:
            # the rule begins after it, under the headword. Without admitting it as a
            # boundary, « +quoniam » lost its underline -- the rule, though properly
            # measured, was judged to begin in the middle of a word and thrown away.
            FRONT=set(' ("\'+')
            ranges=[]
            for a,b in f2:
                while b > a and (b >= len(s) or s[b] == " "): b -= 1
                while a < b and (a >= len(s) or s[a] == " "): a += 1
                if b < a: continue
                # A rule that begins in the middle of a word is a ghost of the
                # measurement: we throw it away. Extending it to the whole word scored
                # as well against the ground truth (84.5 % against 83.9 % of exact
                # lines), but it is the wrong failure -- better a missing underline
                # than a word wrongly underlined, which leaps to the eye:
                # « autoritato » and « esas, » showed as much.
                if not (a == 0 or (a-1 < len(s) and s[a-1] in FRONT)):
                    continue
                ranges.append((a,b))
        out.append((k, s, ranges))
    return out, ncol

def texify(cells, ranges):
    """Sets a line: spaces -> \\cel{n}, underlined ranges -> \\sou{...}."""
    n=len(cells)
    mark=[False]*n
    for a,b in ranges:
        for j in range(max(a,0), min(b+1,n)): mark[j]=True
    # we truncate the trailing spaces
    end_=n
    while end_>0 and cells[end_-1]==" " and not mark[end_-1]: end_-=1
    if end_==0: return ""
    res=[]; i=0; empty_=0
    while i<end_:
        if cells[i]==" " and not mark[i]:
            empty_+=1; i+=1; continue
        if empty_: res.append(f"\\cel{{{empty_}}}"); empty_=0
        if mark[i]:
            j=i
            while j<end_ and mark[j]: j+=1
            res.append("\\sou{"+esc(cells[i:j])+"}")
            i=j
        else:
            j=i
            while j<end_ and cells[j]!=" " and not mark[j]: j+=1
            # we keep the single interior spaces in plain form, for legibility
            while j<end_ and not mark[j] and (cells[j]!=" " or (j+1<end_ and cells[j+1]!=" " and not mark[j+1])):
                j+=1
            res.append(esc(cells[i:j]))
            i=j
    return "".join(res)

_LP=None
def extra_lines(file_=f"{T}/extra_lines.txt"):
    """Lines that a later RE-CUTTING of the page left outside the block.

    Twenty-one pages were cut by a version of bloc_texte() that stopped the
    block too high; their .npz therefore no longer carries the last lines of
    the page, whereas the scan does carry them. This file gives them back, as
    the scan gives them, and it serves BOTH editions: the facsimile resets
    them, the reading edition reads them. One source, so no divergence
    possible.

    One line of the file: page<TAB>line number<TAB>text of the grid.
    """
    global _LP
    if _LP is None:
        _LP={}
        if os.path.exists(file_):
            for l in open(file_,encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                a,b,v=l.split("\t")
                _LP.setdefault(int(a),{})[int(b)]=v
    return _LP


def write_(pg, lab, M, tab, rep=f"{ROOT}/content"):
    os.makedirs(rep, exist_ok=True)
    lines, ncol = page_lines(pg, lab, M, tab)
    sup=extra_lines().get(pg)
    if sup:
        per={t[0]:t for t in lines}
        for k,txt in sorted(sup.items()):
            # A line already read but TRUNCATED on the right: we keep its underline
            # rules, which bear on the start, and return the whole text. A line
            # absent: we create it, with no rule.
            ranges = per[k][2] if k in per else []
            cells=list(txt) + [" "]*max(0, ncol-len(txt))
            per[k]=(k, cells, ranges)
        # The lattice is DENSE: one entry per leading, blank or not. The lines
        # given back can leave a hole -- the blank leading that separates two
        # articles -- which must be recreated, or the articles touch and the page
        # shifts by a line. A NEGATIVE index returns a line lost above the first:
        # the lattice extends upwards, and the numbering of the lines already read
        # does not move.
        lines=[per.get(k, (k, [" "]*ncol, []))
                for k in range(min(per), max(per)+1)]
    # The lattice of lines covers the whole height of the image so as to catch
    # the folios; at the foot of a page it therefore produces ghost lines, empty.
    # An empty line AFTER the last inked line carries no information and would
    # overflow the composed page (a \vbox too tall). We subtract them.
    def _blank(t):
        k,cells,ranges = t
        return not ranges and all(c==" " for c in cells)
    while lines and _blank(lines[-1]): lines.pop()
    # The page's layout: we centre it on its own width, with a little more
    # margin on the sewing side. A fixed origin left as much as 66 mm of white
    # on one side and overflowed the other.
    # An isolated speck far to the right -- a lone « - » after twenty-four
    # spaces -- is not text: it widened the page by thirty millimetres. We
    # subtract it, under a strict condition: a single character, of punctuation,
    # separated from the rest by ten cells at least.
    ISOLATED=set("-.,'\"")
    for k,cells,ranges in lines:
        end_=-1
        for j in range(len(cells)-1,-1,-1):
            if cells[j]!=" ": end_=j; break
        if end_<1 or cells[end_] not in ISOLATED: continue
        if any(b>=end_ for a,b in ranges): continue
        empty_=0; j=end_-1
        while j>=0 and cells[j]==" ": empty_+=1; j-=1
        if empty_>=10: cells[end_]=" "
    last_one=0
    for k,cells,ranges in lines:
        end_=-1
        for j in range(len(cells)-1, -1, -1):
            if cells[j] != " ": end_=j; break
        if end_<0: continue
        last_one=max(last_one, end_)
        # A rule that runs past the last character of its line is an artefact of
        # measurement: it must not widen the page.
        for a,b in ranges: last_one=max(last_one, min(b, end_))
    wide=(last_one+1)*HSTEP_MM
    top=len(lines)*VSTEP_MM
    # A FIXED origin, and not a page-by-page centring. Centring each page on
    # its own width made it balanced in isolation, but made the left edge jump
    # from one page to the next: over 631 pages, 199 jumped by more than five
    # millimetres, up to twenty-eight. A book does not do that -- its block of
    # text is in the same place on every page of the same hand, and the short
    # lines simply leave white on the right.
    recto = (pg % 2 == 0)                    # a right-hand page in the facsimile
    if recto:
        x = WIDTH_MM - OUTER_EDGE - wide        # set on the right fore-edge
        if x < GUTTER_MIN: x = GUTTER_MIN
    else:
        x = OUTER_EDGE                         # set on the left fore-edge
        if WIDTH_MM - x - wide < GUTTER_MIN:
            x = WIDTH_MM - GUTTER_MIN - wide
    # The few very wide pages -- six pass 74 columns -- hold neither the
    # fore-edge nor the gutter. We leave them the absolute stop.
    if x + wide > WIDTH_MM - MARGIN_EXTREME:
        x = max(WIDTH_MM - MARGIN_EXTREME - wide, MARGIN_EXTREME)
    x = max(x, MARGIN_EXTREME)
    y = TOP_EDGE
    if y + top > TOP_MM - MARGIN_BOTTOM_MIN:
        y = max(TOP_MM - MARGIN_BOTTOM_MIN - top, MARGIN_EXTREME)
    # The shift is quantised on the grid: a whole number of pitches in width,
    # a whole number of leadings in height. Without that the characters no
    # longer fall on a whole column, and the position check -- which guarantees
    # the fidelity of the screen -- fails.
    dx=round((x-ORIGX_MM)/HSTEP_MM)*HSTEP_MM
    dy=round((y-ORIGY_MM)/VSTEP_MM)*VSTEP_MM
    L=["% page "+str(pg+1)+" of the facsimile (image p-%03d of the scan)"%pg,
       "%% block %.1f x %.1f mm ; left margin %.1f mm"%(wide,top,x),
       "\\pgc{%.3fmm}{%.3fmm}{"%(dx,dy)]
    for k,cells,ranges in lines:
        L.append("\\l{"+texify(cells,ranges)+"}")
    L.append("}")
    open(f"{rep}/p{pg:03d}.tex","w",encoding='utf-8').write("\n".join(L)+"\n")
    return len(lines)

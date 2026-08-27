# -*- coding: utf-8 -*-
"""Extracting a structured lexical base from the decoded typescript.

The typescript follows a strict grammar, which is read off the layout:

    vedetto. (fako.) Senco unesma. - II. Senco duesma. - L. nomo latina. - DEFIS.
    ^^^^^^^  ^^^^^^                    ^^^                ^^^^^^^^^^^^^   ^^^^^
    underlined, column 0                sense              nomo cientifika  lingui

Each record carries its **provenance** -- image of the scan, page of the book,
line of the grid -- and its **flags of quality**. Nothing is erased: what is
doubtful is reported, not hidden.
"""
import numpy as np, os, pickle, re, collections, sys, json, os, unicodedata
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from consolidate import headwords
T=_ROOT + "/work"
FOLIO_OFFSET = 7          # page number of the book = image index - 7

LANGUAGES = {'D':'Germana','E':'Angla','F':'Franca','I':'Italiana','R':'Rusa',
          'S':'Hispana','L':'Latina','P':'Portugalana','G':'Greka','N':'Nederlandana'}
# Some notations spell the language out: « FDSued » = Franca, Germana, Sueda.
ABBREVS = {'Sued':'Sueda','Ned':'Nederlandana','Pol':'Polona','Dan':'Dana',
         'Nor':'Norvegana','Fin':'Finlandana','Cek':'Cheka'}
# A few notations spell the language out in full, separated by commas --
# « Jap.,Sanskr. » for « ka(d) ». They do not enter the letter code: read as
# text, the article passed for « sen-lingua ».
SPELLED = {'Jap':'Japoniana','Sanskr':'Sanskrita','Hebr':'Hebrea','Arab':'Araba',
         'Turk':'Turka','Chin':'Chiniana','Malay':'Malaya','Skand':'Skandinava',
         'Gr':'Greka','Lat':'Latina','Slav':'Slava','Hind':'Hindua'}
RE_SPELLED = re.compile(r'(?:[-\u2013]|^)\s*((?:[A-Z][a-z]{1,7}\.?\s*,\s*)+[A-Z][a-z]{1,7}\.?)\s*$')

def _read_code(token):
    """Is the final token a code of languages? Returns the list, or None.

    The discriminant is the CASE: a code is in capitals. Without it, every word
    ending a sentence -- « gamo », « radii », « korpo » -- passed for a code.
    We tolerate a capital damaged by the decoding (« dEFIRS ») and the « l »
    read for « I » (« DEFlS »), but require the token to be mostly upper case.
    """
    if not token or len(token) > 12: return None
    tops=sum(1 for c in token if c.isupper())
    if tops < max(1, int(0.6*len(token))): return None
    out=[]; left_over=token
    for ab,name_ in ABBREVS.items():                    # a spelled-out abbreviation, at the end
        if left_over.endswith(ab): out.append(name_); left_over=left_over[:-len(ab)]; break
    for c in left_over.upper().replace('L','I') if False else left_over:
        c = 'I' if c=='l' else c.upper()
        if c not in LANGUAGES: return None
        out.append(LANGUAGES[c])
    # No true code names the same language twice. « II » and « III » are numbers
    # of senses that the end of an article leaves hanging -- under « forsan »,
    # « xenio », « -ajo », « ek » -- and the edition gave them as « Italiana,
    # Italiana ». The cutting into articles (dividar) laid down that rule
    # already; it holds here too.
    if len(set(out)) != len(out): return None
    return out or None
# The language code is sometimes stuck to the full stop before it -- « agar
# lo.DEFIS. » -- by a fault of the original. We therefore accept the full stop
# as a separator on the same footing as the hyphen.
# The final code is not always preceded by a hyphen: it sticks to the full stop
# -- « agar lo.DEFIS. » -- or to the closing parenthesis -- « (anke metaf.)DEFIRS ».
# Nor is it always followed by a full stop.
RE_CODE   = re.compile(r'(?:[-–.)]|^)\s*([DEFIRSLP]{1,8})\s*[.,]?\s*$')
# The opening parenthesis is sometimes missing in the original:
# « abduktar.-trans.) » reads so in the scan, verified. We therefore tolerate
# its absence, but only if nothing is already open and if the content is short,
# so as not to swallow a whole sentence. The full stop that follows the closing
# parenthesis is consumed: without that the definition began with « . » --
# « ablegato », « abulio ».
RE_DOMAIN   = re.compile(r'^\(([^()]{1,40})\)\s*\.?\s*')
RE_DOMAIN2  = re.compile(r'^([^()]{1,25})\)\s*\.?\s*')
# The scientific name is announced by « L. ». The hyphen before it is often
# missing: « ... kompozaji". L. artemisia absinthium ». We therefore accept the
# full stop and the start of a segment on the same footing as the hyphen.
# The comma belongs to the scientific name when it gives two forms --
# « L. anas, anatis ». Without it in the class, the name stayed in the sense.
# The SECOND form can run to several words -- « L. rubus caesius, rubus
# fructicosus » under rovo, « L. dalbergia nigra, jacarania mimosifolia » under
# palisandro, and as far as the author's gloss, « L. conium maculatum, e speco
# di cicuta » under cikuto. Taking only one left the rest in the definition,
# preceded by the name's orphaned comma: « ... (rovbero). , rubus
# fructicosus ». We therefore admit the second form whole, four words like the
# first.
# The scientific name does not always end on a hyphen or at the end of a
# segment: it is often followed by a closing parenthesis -- « (L. triticum
# caninum) » -- by a comma that takes the sentence up again, or by the number of
# the next sense -- « L. aquila II. ». Anchored on the hyphen alone, it stayed
# in the definition of sixty-seven articles. We therefore bound the name by its
# FORM -- four Latin words at most, plus a second form after a comma for
# « anas, anatis » -- instead of bounding it by what follows it.
# The full stop of the « L. » is sometimes missing -- « ...puteo-kordegi.- L
# tilia. - FISL. » under tilio. We admit it without its full stop, but then only
# before a LOWER CASE letter: « - La persono qua... », « - Longa bastono... »
# open a definition, and the L would take the word's first letter there.
# The name often ends on « .- » with no space -- « L. viverra genetis.- II.
# (tekn.) ... » under jineto. Without the hyphen in the class that follows the
# full stop, the name stayed in the definition of sixty-eight articles.
# An « L. » that introduces an EXAMPLE does not announce the article's
# scientific name: « enklitiko. ... Kom ex.: L. que en neque ; ne en venisne ;
# F. ce en est-ce ». Taken for a binomial, it left the definition -- which
# stayed at « Kom ex.; » -- to be displayed as the article's Latin name. The
# « F. » that follows has never been taken: only the « L. » invited confusion.
RE_LATIN = re.compile(
    r'(?:(?<!ex\.)[-–.(,;:]|^)\s*(?:L\.\s*|L\s+(?=[a-z]))'
    r'([A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3}'
    r'(?:\s*,\s*[A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3})?)'
    r'\s*(?=[-–)(:;,]|\.[\s)–-]|\.?$|\s(?:I{1,3}|IV|VI{0,3})\.)')
# The senses are separated by « - II. », but the hyphen is often missing:
# « ... komenco-punto e fino-parto. II. (gram.) ... ». We therefore also cut on
# a full stop followed by the number of a sense, which holds for 107 articles.
# Six articles number their senses in ARABIC figures -- « grapino »,
# « kapelo », « koliaro », « kondamnar », « konfliktar » -- and « iambo » mixes
# the two levels. Without this branch, all their content stayed in a single
# sense. We require the capital or the parenthesis after the number, which sets
# aside « 1.000 » and the chemical formulae. The « l » read for « 1 » is
# admitted: the confusion is constant in this typescript.
# The CLOSING parenthesis is worth the full stop: « elaborar. ... per laborado.
# (anke metaf.) II. (fiziol.) Igar absorbebla... ». The number then follows a
# parenthesis, not a full stop, and the sense did not cut -- eleven articles
# kept two senses in one. The safeguard holds: « pos I. K. » under « hejiro »
# and « rejo Francisko I. » under « legiono » follow neither full stop nor
# parenthesis, and do not cut.
# The number's full stop is sometimes missing: « ...di elektro-lampo. III
# veziketo produktata... » under « ampulo », « ...kontenar aquo. – II
# Mar-baseno... » under « baseno ». The book counts only two, and both are true
# senses; we therefore admit the number followed by a plain space, provided a
# letter follows. A PARENTHESIS is worth as much: the sense very often opens on
# its qualifier, « reklamacar. I(netrans.) ... ne-equitatoza.II (trans.)
# Postular... », and the number then found itself in the text of the sense,
# where it doubled the one the editions lay themselves -- « 1. I (zool.)
# Mamifero karnivora... » under « leono ». The space is optional there: the
# typist sticks the number to the parenthesis as often as she separates them.
# The book numbers as far as VIII -- « modo » has eight senses, « exemplo »,
# « lineo » and « punto » have seven. The run stopped at VI: « -VII.(tipogr.) »
# under « punto » stayed in sense VI, its number in the middle of the text.
# « VI{0,3} » covers V, VI, VII and VIII in one piece, as the rule that TAKES
# the number off the head of a sense already does. The book goes no further: no
# article carries a IX.
RE_SENSE  = re.compile(r'\s*(?:[-–]\s*|(?<=[.)])\s*)'
                       r'(?=(?:I{1,3}|IV|VI{0,3})[.,]\s?'
                       r'|(?:I{1,3}|IV|VI{0,3})\s+[A-Za-zÀ-ÿ]'
                       r'|(?:I{1,3}|IV|VI{0,3})\s*\('
                       r'|[l\d]\d?\.\s*[A-ZÀ-Ý(])')
# The author sometimes numbers his senses IN PARENTHESES: « (1) ... (2) ... ».
# Written so, they most often hold in a single sentence -- the pieces follow
# one another after a semicolon or a colon, « (1) Garnisar ye ulo...;
# (2) Garnisar per esar pozita sur... » under « kovrar » -- and the book renders
# them as they stand: we leave them.
#
# But the FIRST of those numbers follows the headword, where the analysis looks
# for the domain: it went into the `fako` field, whence it was set aside as a
# number. The article then lost its « (1) » while keeping its « (2) » --
# « ramo », « romano », « vice », the only three in the book. An orphaned
# numbering tells nobody anything; we cut the sense in its place, and the
# editions renumber as they do the others. The cut is made only after a CLOSED
# sentence, so as not to undo the enumerations spoken in one breath.
RE_ORPHAN_NUM = re.compile(r'(?<=[.!])\s*[-–]?\s*\((?:I{2,3}|IV|[2-9])\)\s*'
                         r'(?=[A-Za-zÀ-Ý«(])')
RE_NUM_FIRST = re.compile(r'\(\s*(?:1|l|I)\s*\)')
ENDINGS_OK = ("o","a","e","i","ar","ir","or")
# A mark of cutting laid in the text by the analysis, where a sense ends
# without the book having numbered it -- the language code that closes it, for
# example. Invisible, it is read by the cutting into senses, and never comes
# out of it.
CUT = "\ue002"

_LP=None
def _extra_lines(file_=f"{T}/extra_lines.txt"):
    """Lines from the foot (or the head) of a page lost to a later RE-CUTTING.

    Page 290 showed it: its extraction was redone on 13 August, and the new
    block stopped four lines higher than the old. The facsimile, composed
    before the re-cutting, keeps those lines; the reading edition, built on the
    .npz, had lost them -- « koklusho » ended on « precipue la » and « kokono »
    was missing from the book. Rather than re-cut the page, which would move
    every correction indexed by (page, line, column), we give the lines back
    here as the facsimile carries them.

    One line of the file: page<TAB>line number<TAB>text.
    The text is that of the grid, leading spaces included.
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


def _signature():
    """Fingerprint of the files the decoded text depends on."""
    names=["cls_lab.npy","cls_alternatives.pkl","extra_lines.txt",
          "exceptions_ends.txt","exceptions_ornaments.txt","exceptions_pairs.txt",
          "exceptions.txt","exceptions_proofreading.txt","exceptions_manual.txt",
          "pages_not_typed.txt"]
    sig=[]
    for n in names:
        p=f"{T}/{n}"
        sig.append((n, os.path.getmtime(p) if os.path.exists(p) else 0))
    d=f"{T}/cells"
    if os.path.isdir(d):
        sig.append(("cells", max((os.path.getmtime(os.path.join(d,f))
                                     for f in os.listdir(d)), default=0)))
    else:
        # Without the cells, the text is read out of `content/`: it is that
        # directory the cache must follow, or a page set again would not be
        # read again. See tools/scanless.py.
        c=f"{_ROOT}/content"
        sig.append(("content", max((os.path.getmtime(os.path.join(c,f))
                                     for f in os.listdir(c)), default=0)))
    # rules.pkl carries the underlines when the cells are not there.
    p=f"{T}/rules.pkl"
    sig.append(("rules.pkl", os.path.getmtime(p) if os.path.exists(p) else 0))
    return sig


def load_text(hidden=True):
    import pickle
    kf=f"{T}/_pages.pkl"
    sig=("v2", _signature())
    if hidden and os.path.exists(kf):
        try:
            with open(kf,"rb") as h: pages,corrected,rules_,old_ones=pickle.load(h)
            if old_ones==sig: return pages,corrected,rules_
        except Exception: pass
    pages,corrected,rules_=_load_text()
    try:
        with open(kf,"wb") as h: pickle.dump((pages,corrected,rules_,sig),h)
    except Exception: pass
    return pages,corrected,rules_


def _load_text():
    from decode import load_, page_text
    from generate import exceptions
    import scanless
    # Without the scan, the same lines are read back out of `content/`, which
    # is in the repository and is set cell by cell. See tools/scanless.py.
    scan=scanless.corpora_present()
    if scan:
        lab,M=load_(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
        last=int(M[:,0].max())
    else:
        lab=M=tab=None; last=max(scanless.pages())
    exc=exceptions()
    corrected=set((p,k,c) for (p,k,c) in exc)
    pages={}; rules_={}
    for pg in range(last+1):
        try:
            lines=page_text(pg,lab,M,tab) if scan else scanless.page_text(pg)
        except Exception: continue
        # A page that is not typewritten -- the cover, the six blank ones --
        # has no cells; without the scan it has no \l{} either. Both roads
        # therefore leave it out of the table, rather than entering it empty.
        if not lines: continue
        out=[]
        for k,s in lines:
            l=list(s)
            # A correction can lengthen the line: a headword re-read may count
            # more cells than the automatic reading. We complete the line instead
            # of dropping the correction.
            for (pp,kk,cc),v in exc.items():
                if pp==pg and kk==k:
                    if cc>=len(l): l.extend(" "*(cc-len(l)+1))
                    l[cc]=v
            out.append((k,"".join(l).rstrip()))
        sup=_extra_lines().get(pg)
        if sup:
            per=dict(out); per.update(sup)
            out=sorted(per.items())
        pages[pg]=out
        # The page's underline rules, as the cutting of the cells surveyed them:
        # a list of ranges of COLUMNS per line, in the same numbering as the text
        # returned above. It is the mark the author himself laid on his
        # typescript; it designates the domain, the phrase, the Latin name, the
        # quoted word.
        try:
            if scan:
                z=np.load(f"{T}/cells/p-{pg:03d}.npz", allow_pickle=True)
                import pickle as _pk
                underline=_pk.loads(z['sou'].item())
                rules_[pg]={int(k): [(int(a),int(b)) for a,b in v[1]]
                             for k,v in underline.items() if v[1]}
            else:
                rules_[pg]=scanless.underlines(pg)
        except Exception:
            rules_[pg]={}
    return pages, corrected, rules_


_ND=None
def _not_typed():
    """Pages that are not typewritten: cover, blank pages."""
    global _ND
    if _ND is None:
        _ND=set(); p=f"{T}/pages_not_typed.txt"
        if os.path.exists(p):
            for l in open(p,encoding='utf-8'):
                if l.startswith('#') or not l.strip(): continue
                _ND.add(int(l.split('\t')[0]))
    return _ND

# A folio, as the decoder returns it: « 113 », but also « lOO », « 2Ol »,
# « ll2 » -- the typewriter's one and zero read as l and O. Two folios
# sometimes follow one another, « 173/175 », when the page carries both.
RE_FOLIO=re.compile(r'^[\dlOoIi][\dlOoIi\s/.,\u2013-]{0,7}$')
# The folio, at the end of a line of text, is distinguished by the white
# before it: « ... sen shancelar   563 ». It does not belong to the sentence.
RE_FOLIO_FIN=re.compile(r'\s{2,}[\dlOoIi]{1,4}[.,]?$')

def cut_up(pages, corrected, rules_=None):
    rules_ = rules_ or {}
    ent=[]; heads={}
    for pg in sorted(pages):
        if pg < 8: continue          # front matter: title, preface, rezumo di gramatiko
        if pg in _not_typed(): continue   # blank pages: nothing to cut
        # Without the cells, the same test is made on the decoded text: see
        # scanless.headwords(). Falling back to an EMPTY set is not harmless --
        # it is by a rule at the margin that « -ant- », « des- », « a priori »
        # and thirty-four others are known to open an article, the regular
        # expression below reaching none of them.
        try: hw={k for k,_ in headwords(pg)}
        except Exception:
            try:
                import scanless
                hw={k for k,_ in scanless.headwords(pg)}
            except Exception: hw=set()
        # The page's margin, read off the DECODED TEXT and not off the occupation
        # of the cells: forty-five pages begin further right -- page 380 begins
        # at 5 -- and occ() sees ink in column 0 there where the decoding sees
        # nothing. All their entries were lost.
        lines_more=[s for _,s in pages[pg] if s.strip()]
        if lines_more:
            mg=min(len(s)-len(s.lstrip()) for s in lines_more)
        else:
            mg=0
        # An unrmarked headword is still a headword: it begins at the margin,
        # after a blank line, and presents itself as « mot. ».
        # An unmarked headword is still a headword. We do not impose the margin
        # on it: « +quoniam » is in column 17, « milieto » in 5. What designates
        # it is following a blank line and presenting itself as « mot. ». The
        # « + » that marks the unofficial words is part of it.
        # « - oz-. », « - as. », « + prei. »: the typist left a space between the
        # sign and the word. Without this tolerance, « -oz- » and « -as » were
        # not headwords at all and fell into the preceding article.
        # « .heliko », « .hipofizo »: the typist struck a full stop before the
        # word. Without this tolerance, those two articles were not headwords at
        # all and fell into the preceding one -- « hipofizo » read at the end of
        # « hipodromo ».
        # « "dis" », « "hidalgo" »: a quoted borrowing is a headword in its own
        # right, and the author frames it in quotation marks. « ha ! »: an
        # interjection ends with its exclamation mark, not with a full stop.
        # « o (d). »: the headword carries its variant in parentheses, like
        # « a(d). », but separated by a space.
        # « rutino, »: the typist struck the COMMA instead of the full stop. The
        # rule is there, the blank line too; only the punctuation was missing,
        # and the whole article fell into « ruteno », whose chemical symbol it
        # swallowed. Over the six hundred and thirty-nine pages, one line alone
        # follows a blank line presenting itself as « mot, »: that one. Admitting
        # the comma therefore costs no false positive.
        # « -- protestanto. »: the author marked with a double hyphen the article
        # he was inserting after the fact. « +intrenar (trans.) »: he omitted the
        # full stop, and it is the qualifier in parentheses that closes the
        # headword. Without these two tolerances, « protestanto » fell into
        # « protestar » and « +intrenar » into « intramolekula ».
        RE_HW=re.compile(r'^(?:[-–]{2}\s*)?[\"«]?\.?[+-]?\s?'
                          r'[A-Za-z][A-Za-z\'’-]{0,30}[\"»]?'
                          r'\s?-?\s?(?:\([A-Za-z]{1,3}\)\s?)?'
                          r'(?:[.!,]|\s*\([A-Za-z]{1,12}[.,)])')
        # The blank line is not read in the text: it is NOT in the grid.
        # page_texte() returns only the lines detected, and their numbers skip --
        # 2, 3, then 5. It is that SKIP that marks the blank. Looking for an
        # empty string, the rule fired only on the first line of each page: page
        # 536 returned one article out of fourteen, and « simpla », « utila »,
        # « granda » were missing from the book.
        # The folio, and the lines that carry no letter -- the superscript figures
        # of a formula, laid above their line -- do not break the blank: they are
        # not running text. Without that transparency, « smalto » (folio stuck to
        # the headword) and « morfino » (the subscripts of its formula above)
        # were not headwords at all, and their articles fell outside the book.
        preceding=None; hw2=set()
        for k,s in pages[pg]:
            if not s.strip(): continue
            if RE_FOLIO.match(s.strip()) or not any(c.isalpha() for c in s):
                continue
            white = (preceding is None) or (k - preceding > 1)
            # A word ALL in capitals is not a headword: it is the language code,
            # which the author sometimes threw onto a line of its own after a
            # leading -- « DEFIR. » under « sodo ». « Direktorio », « Usa »,
            # « Venus » keep their initial capital and remain headwords.
            u=s.lstrip()
            capitals = re.match(r'^[A-Z]{2,}\b', u) is not None
            if white and not capitals and RE_HW.match(u): hw2.add(k)
            preceding=k
        # The subscripts of a formula, struck on a line of their own JUST BEFORE
        # the headword that carries them: « 12  22  11 » above « laktoso ». The
        # machine does not lower the figures; the typist therefore raises the
        # line. Four formulae in the book are in that case -- laktoso, morfino,
        # saponino, fenacetino -- and their line of subscripts attached itself to
        # the PRECEDING article, where it has no business. The same fate for the
        # isolated full stop that precedes « deciliono ».
        content_=[(k,x) for k,x in pages[pg] if x.strip()]
        mute=set()
        for i,(k,x) in enumerate(content_):
            if any(c.isalpha() for c in x): continue
            j=i+1
            if j < len(content_) and (content_[j][0] in hw or content_[j][0] in hw2):
                mute.add(k)
        cur=None; orphan=[]
        for k,s in pages[pg]:
            if not s.strip() or k in mute: continue
            if k in hw or k in hw2:
                if cur: ent.append(cur)
                cur=dict(image=pg, pagino=pg-FOLIO_OFFSET, ligno=k, lineoj=[(k,s)])
            elif cur is not None:
                cur['lineoj'].append((k,s))
            elif not RE_FOLIO.match(s.strip()):
                orphan.append((k, RE_FOLIO_FIN.sub('', s)))
        if cur: ent.append(cur)
        if orphan: heads[pg]=orphan
    # An article begun at the foot of a page and continued at the head of the
    # next. « tamburo » (folio 567) stopped at « kovrita ye »: its last two lines
    # open page 568, before « tamburino », and the cutting, which starts from zero
    # on each page, threw them away. We attach them only if the preceding article
    # was left IN SUSPENSE -- with no final language code -- which is the very mark
    # of the break.
    RE_CODE_=re.compile(r'[-–]\s*[A-Za-z]{1,12}\.?\s*$')
    last_={}
    for i,e in enumerate(ent):
        if e['ligno'] >= last_.get(e['image'], (-1,-1))[0]: last_[e['image']]=(e['ligno'], i)
    n_run_on=0
    for pg,lines in sorted(heads.items()):
        d=last_.get(pg-1)
        if d is None: continue
        e=ent[d[1]]
        t=" ".join(x for _,x in e['lineoj']).strip()
        # The preceding article already carries its code: it is closed, the head
        # of the page does not continue it.
        if RE_CODE_.search(t): continue
        # It ends on a lone hyphen: it is not the sentence that is missing, it is
        # the language code. « "nirvana" » ends so, and the head of the next page
        # belongs to « nivar », an article the book has lost.
        if re.search(r'[-–]\s*$', t): continue
        u=" ".join(x.strip() for _,x in lines).strip()
        # A letter on its own, a sign: an accident of typing, not a text.
        if len(u) < 8 or len(u.split()) < 2: continue
        e['lineoj'].extend(lines); n_run_on+=1
    if n_run_on: print("articles continued at the head of a page: %d"%n_run_on)
    for e in ent:
        e['korektita'] = sum(1 for (k,_) in e['lineoj']
                             for c in range(120) if (e['image'],k,c) in corrected)
        e['filetoj'] = rules_.get(e['image'], {})
    return ent


def underlinings(e):
    """What the author UNDERLINED in the article, set end to end.

    The typescript has no italic: the typist underlines. She underlines the
    headword, the Latin name, the domain -- « (matem.) » -- and the phrase that
    carries its own definition -- « Proporciono geometriala : ... ». The survey
    of the rules gives, line by line, ranges of columns; one need only read the
    text in them.

    A phrase broken at the end of a line is reglued: « Proporciono geome- »
    then « triala ». The hyphen is the break's, not the word's.
    """
    fil=e.get('filetoj') or {}
    per={k:s for k,s in e['lineoj']}
    pieces=[]                       # (text, cut_at_the_end)
    for k,s in e['lineoj']:
        end_=len(s.rstrip())
        for a,b in sorted(fil.get(k, [])):
            if a >= len(s): continue
            t=s[a:b+1]
            # The rule sometimes bites into the neighbouring punctuation.
            t=t.strip(" .,;:)(\u00ab\u00bb\"'")
            if not t: continue
            # End-of-line break: the hyphen follows immediately.
            cut = s[b+1:end_].strip() == '-'
            pieces.append((t, cut))
    out=[]; i=0
    while i < len(pieces):
        t,cut = pieces[i]
        while cut and i+1 < len(pieces):
            i += 1
            t = t + pieces[i][0]
            cut = pieces[i][1]
        out.append(t); i += 1
    # The headword is underlined like the rest: it teaches nothing here.
    v=(e.get('vedetto') or '').lower().lstrip('*+')
    vu=set(); res=[]
    for t in out:
        u=re.sub(r'\s+',' ',t).strip()
        if len(u) < 3 or u.lower().rstrip('.') == v: continue
        if u.lower() in vu: continue
        vu.add(u.lower()); res.append(u)
    return res

_END=("ar","ir","or","as","is","os","us","o","a","e","i")
def _attested(w, lexicon):
    """Is the word, or its root once the grammatical ending is off, a headword?"""
    if not lexicon or not w: return False
    w=w.lower()
    if w in lexicon: return True
    for f in _END:
        if w.endswith(f) and len(w)-len(f)>=2 and w[:-len(f)] in lexicon: return True
    return False

def reglue(lines, lexicon=None):
    """Reglues an article's lines, giving back the words broken at the line end.

    The typescript breaks words at the right edge: « por rezis- » then « tar ».
    Joining them with a space gave « rezis- tar ». We therefore reglue them
    with no space and no hyphen.

    A compound that falls exactly on the break is ambiguous -- « homo-korpo »
    broken after the hyphen should keep its hyphen. We settle it by the
    lexicon: we test the REGLUED word, not the left-hand fragment. The first
    version tested the left: « re », « pro », « kom », « fa », « mi » are
    prefixes, hence always attested as headwords, and the hyphen stayed --
    « re-cevar », « pro-duktita », « kom-batis » came out cut in two. The
    lexical judgement of the first wave found almost nothing else.
    """
    out=""
    for i,s in enumerate(lines):
        s=s.strip()
        if not out: out=s; continue
        if out.endswith('-') and s[:1].islower() and out[:-1][-1:].isalpha():
            left_=re.split(r'[^A-Za-z’\'-]', out[:-1])[-1]
            right_=re.split(r'[^A-Za-z’\'-]', s)[0]
            if _attested(left_+right_, lexicon):
                out=out[:-1]+s          # the reglued word exists: it was a hyphenation
            elif (lexicon and _attested(left_, lexicon)
                          and _attested(right_, lexicon)):
                out=out+s               # two attested words: a compound, we keep the hyphen
            else:
                out=out[:-1]+s          # in doubt, hyphenation is the ordinary case
        else:
            out=out+" "+s
    return out

# Two articles struck one after the other on the same line. The cutting is made
# on the blank line before the headword; when the typist has left none, the
# second article finds itself swallowed into the definition of the first --
# « cerebelo » in « cereala », « asepta » in « asentar ». What separates them is
# sure: each article ENDS with its language code. Everything that follows
# « - DEFIS. » and presents itself as « mot : » or « mot. » is therefore a new
# article. We require a true code -- « L. » (Latin name) and « Simb. » (chemical
# symbol) are not -- so as not to cut « - L. saponaria. » in two.
RE_SPLIT = re.compile(r'[-–]\s*([A-Za-z]{1,12})\.\s+'
                       r'(?=(?:[+*]?[a-zà-ÿ][a-zà-ÿ\'\u2019-]{1,25}'
                       r'(?:\s*[:.!]\s|\s+\()'
                       # A quoted borrowing taken for a headword: « "argus" », « "inch" ».
                       # Eleven articles were drowned in their neighbour that way.
                       r'|["\u00ab]\s*[+*]?[a-zà-ÿ]))')

_SPLITS=None
def _split(file_=f"{T}/splits.txt"):
    """Cuts surveyed by eye: image:line -> the string to cut at.

    The automatic location relies on the language code that ends each article.
    When a note has slipped between the two -- « shokar. ... II. (Ref.
    "Adjuntenda", fine di ca verko) shovar. (trans.) Glitigar per pulso. - DE. »
    -- there is no code left at the point of the join, and the second article --
    a whole root, absent from the rest of the book -- stayed drowned in the
    first.
    """
    global _SPLITS
    if _SPLITS is None:
        _SPLITS={}
        if os.path.exists(file_):
            for l in open(file_,encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                p=l.split("\t")
                if len(p)>=2 and p[0].strip() and p[1].strip():
                    _SPLITS[p[0].strip()]=p[1].strip()
    return _SPLITS


def split_at(raw, lexicon=None):
    """Splits the entries that contain two. Returns the widened list."""
    out=[]
    for e in raw:
        t = e.get('teksto_brut')
        if t is None:
            t = re.sub(r'\s+',' ',reglue([s for _,s in e['lineoj']], lexicon)).strip()
            # The correction layer for the raw text must be applied BEFORE the
            # cutting: it is that layer which restores the full stop of the language
            # code, on which the cut relies (« - DEFIR. shut! »).
            for a,b in _texts_of().items():
                if a in t: t=t.replace(a,b)
        # The cut surveyed by eye goes first: it bears where the language code
        # is missing, and the automatic location sees nothing.
        _c = _split().get("%d:%d" % (e.get('image',-1), e.get('ligno',-1)))
        if _c and _c in t and t.index(_c) > 0:
            j=t.index(_c)
            f=dict(e); f['teksto_brut']=t[:j].strip()
            f['drapeli_pre']=['artiklo-dividita']
            out.append(f)
            t=t[j:].strip()
        while True:
            cut=None
            for m in RE_SPLIT.finditer(t):
                j=m.group(1)
                # « - II. » is not a code but a number of sense: read as
                # « Italiana, Italiana », it cut « seniora » in two. No true code
                # repeats a language.
                if j=='L' or len(set(j.upper()))!=len(j): continue
                # « - S. stachys. »: what follows the code is the plant's Latin
                # name, not an article. An article has a definition.
                # An article can be very short: « "kilowatt". 1000 "watt" »
                # holds in twenty-three signs. The threshold sets aside above all
                # the isolated Latin name, shorter still.
                if len(t)-m.end() < 18: continue
                if _read_code(j):
                    cut=m; break
            if not cut: break
            f=dict(e); f['teksto_brut']=t[:cut.end()].strip()
            f['drapeli_pre']=['artiklo-dividita']
            out.append(f)
            t=t[cut.end():].strip()
        f=dict(e); f['teksto_brut']=t
        if out and out[-1].get('image')==e.get('image') and out[-1].get('ligno')==e.get('ligno'):
            f['drapeli_pre']=['artiklo-dividita']
        out.append(f)
    return out

_TEXTS=None
def _texts_of(file_=f"{T}/texts.txt"):
    """Corrections to the RAW TEXT, before any analysis.

    Some faults must be repaired before the language code, the domain and the
    senses are read -- or the repair comes too late. Thus « autoritato »: the
    author added « pensala. » in the margin, far to the right, to complete
    « verko » on the next line; the word found itself AFTER the « - DEFIRS. »
    of the preceding article, whose code was therefore no longer anchored at
    the end of the string.
    """
    global _TEXTS
    if _TEXTS is None:
        _TEXTS={}
        if os.path.exists(file_):
            for l in open(file_,encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                p=l.split("\t")
                if len(p)>=2 and p[0].strip(): _TEXTS[p[0].strip()]=p[1].strip()
    return _TEXTS

def _cut(x):
    """Cuts the tail of a segment, WITHOUT touching the final ellipsis.

    The author marks with a « ... » the place of the complement the word
    governs: « de la instanto kande onu agnoskas kom valida ke... » for
    quoniam, and likewise for for, jus, kande, kovrar, pasar, proxim. The
    ordinary trimming of full stops made it disappear, though it carries sense
    -- the book keeps fifty-five others elsewhere.
    """
    x = re.sub(r'[\s\-\u2013]+$', '', x)
    # The language code sometimes sticks to the ellipsis -- « ... gradale)
    # de...EFIRS » under proxim -- and the search for the code carries off one of
    # its dots. Two dots therefore suffice to recognise it; we restore it to three.
    if re.search(r'\.\.+$', x):
        return re.sub(r'\.\.+$', '...', x)
    # « e c. » abbreviates « e cetere »: that full stop belongs to the word,
    # not to the sentence, and must not fall with the final punctuation.
    if re.search(r'(?<![A-Za-zÀ-ÿ])e c\.$', x):
        return x
    x = re.sub(r'[\s\-\u2013.,;:]+$', '', x)
    return x


# Abbreviations used in the domain field. The original points them
# irregularly -- « (ajuro) » writes « bot. », others « bot » plain. We make
# them uniform by pointing them all. The list is EXPLICIT, and not deduced from
# a rule about the ending: the same field contains prepositions that also end
# in a consonant (« trans., ad », « netrans., pri »), verbs (« qua agas »),
# numerals (« un »), and even a chemical formula -- a general rule put « C.8
# H.8 » and « Natur.-historio » there.
ABBREVIATE = set("""
trans netrans netr tran anat anatom arit aritm algeb akust arkeol arkit arkitekt
astr astron biol bot diplomac elektr embriol farmak filoz filozof financ fiz
fizik fiziol fortifik fotogr geogr geol geom gram gramat histol imprim katol kem
kemi kirurg kosmol krist kristan liturg literat magnet mat matem med medic mekan
metaf metapsik meteor meteorol mikrobiol milit mineral mitol muz muzik nav navig
oftalm opt paleogr paleont paleontol pat patol pikt psik retor skerm stat tek
tekn teknol teol teratol versif zool zoolog
""".split())


def point_(f):
    """Adds the full stop to the domain abbreviations, and to those alone."""
    if not f:
        return f
    return re.sub(r'(?<![A-Za-zÀ-ÿ.])([A-Za-zÀ-ÿ]+)(?![A-Za-zÀ-ÿ.-])',
                  lambda m: m.group(1) + '.' if m.group(1).lower() in ABBREVIATE
                  else m.group(1), f)


# The proper nouns that open a parenthesis in the book -- countries, persons,
# divinities, peoples, and the adjectives of language and nation, which keep
# their capital in Ido. Without this list the lower-case rule spoilt them:
# « (Italia) » became « (italia) », « (Voltaire) » « (voltaire) », and
# « (Diana chasera, Tetis, e c.) » under nimfo lost its goddess. The list was
# surveyed on the raw text, by looking for every parenthesis opened by a
# capitalised word the edition had made lower case.
PROPER = ('Roma', 'Vatikano', 'Afrodito', 'Araba', 'Aug', 'Auguste', 'Azia',
          'Bacchus', 'Britania', 'Cicero', 'Diana', 'Dubois', 'Elizeo', 'Epiro',
          'Francia', 'Greka', 'Grekia', 'India', 'Istanbul', 'Italia', 'Kelti',
          'Latina', 'Louis', 'Mohamedisti', 'Noah', 'Roentgen', 'Suisia',
          'Tartaro', 'Usa', 'Voltaire',
          'Germana', 'Angla', 'Franca', 'Italiana', 'Rusa', 'Hispana', 'Sueda',
          'Skandinava', 'Portugalana', 'Nederlandana', 'Polona', 'Dana',
          'Norvegana', 'Finlandana', 'Cheka', 'Japoniana', 'Sanskrita',
          'Hebrea', 'Turka', 'Chiniana', 'Malaya', 'Slava', 'Hindua')


def to_lowercase(f):
    """A domain's initial capital has no reason to be: « (Muziko) » is written
    « (muziko) ». The author did not make himself uniform. We spare the proper
    nouns and the chemical formulae, recognised by their figure."""
    if not f or not f[0].isupper():
        return f
    first = f.split()[0].rstrip('.,)')
    # A chemical symbol -- « M », « M' », « Na » -- is not a domain:
    # « (M : natro, o kalio...) », in the formula for alum, says what the
    # letter M stands for. A domain of the book is a word, not a letter.
    if len(first.rstrip("'")) <= 2 and first.rstrip("'").isupper():
        return f
    # A proper noun can carry a tail: « Roentgen-radii » is not
    # « Roentgen » for the test, and the X-rays of radiografar came out
    # « roentgen-radii ». We ask about what precedes the hyphen as well.
    if (first in PROPER or first.split('-')[0] in PROPER
            or re.search(r'[\d\u2080-\u2089]', first)):
        return f
    # The figure may arrive only at the NEXT word, and the first symbol be
    # neither a lone capital nor a proper noun: « (Si O3)2n », the silicon of
    # asbestos, became « (si O3)2n ». The formula is then recognisable only
    # WHOLE, and it is the pattern that already lays the subscripts we ask,
    # with its two safeguards -- at least two symbols and one figure. A
    # sentence that opens with a capital and carries a number does not pass:
    # « (Dicesas precipue pri la homo qua evas plu kam 20 yari) ».
    if _formula_alone(f):
        return f
    return f[0].lower() + f[1:]


_TO_DIGITS = str.maketrans('\u2080\u2081\u2082\u2083\u2084'
                         '\u2085\u2086\u2087\u2088\u2089', '0123456789')


def _formula_alone(u):
    """Is the string a chemical FORMULA, and nothing else?

    The subscripts are brought back onto the line before the test: the string
    lays the capitals first, the subscripts after, but the same function is
    replayed on a text already rendered, where « Si O3 » is written
    « Si O\u2083 ».
    """
    u = u.strip().translate(_TO_DIGITS)
    return bool(_FORMULA.fullmatch(u) and re.search(r'\d', u)
                and len(re.findall(r'[A-Z]', u)) >= 2)


# The same domain, written two ways by the author -- « (anatom.) » once
# against « (anat.) » two hundred and twenty-nine times, « (kem.) » twice
# against « (kemio) » a hundred and eighty. It is not a misreading: it is the
# author who did not make himself uniform, over forty years of slips. The
# edition keeps THE FORM HE USES MOST. When the two are within twice each other,
# the abbreviated one prevails: the book abbreviates its domains 2,463 times
# against 746 where it writes them out, and abbreviation is therefore its way.
# Each line carries both counts.
#
# What is NOT here: the forms nothing says are equivalent. « tekn. » and
# « teknol. », « fiz. » and « fiziol. », « paleont. » and « paleogr. »,
# « milit. » and « milit-arto », « elektro » and « elektrotekniko » are distinct
# domains, and « (religio kristana) », « (armeo-chefo) » are phrases.
DOMAINS_UNIFORM = {
    'netr.': 'netrans.',            #   3 / 446
    'anatom.': 'anat.',             #   1 / 229
    'zoolog.': 'zool.',             #   1 / 424
    'botaniko': 'bot.',             #   1 / 580
    'pat.': 'patol.',               #   1 / 233
    'kem.': 'kemio',                #   2 / 180
    'tek.': 'tekn.',                #   1 / 117
    'muz.': 'muziko',               #   1 /  84
    'muzik.': 'muziko',             #   1 /  84
    'gramat.': 'gram.',             #   2 /  88
    'geometrio': 'geom.',           #   1 /  83
    'mat.': 'matem.',               #   6 /  61
    'astr.': 'astron.',             #   2 /  27
    'filozof.': 'filoz.',           #   1 /  20
    'filozofio': 'filoz.',          #   1 /  20
    'fiz.': 'fiziko',               #   2 /  37
    'financ.': 'financo',           #   1 /  13
    'mineralogio': 'mineral.',      #   2 /  35
    'mitologio': 'mitol.',          #   2 /  14
    'arkit.': 'arkitekt.',          #   5 /  33
    'arkitekturo': 'arkitekt.',     #   3 /  33
    'algeb.': 'algebro',            #   1 /   9
    'arit.': 'aritm.',              #   2 /   9
    'med.': 'medic.',               #   1 /  32
    'medicino': 'medic.',           #  13 /  32
    'nav.': 'navig.',               #   3 /  38
    'teolo': 'teol.',               #   1 /   6  (« teolo » is not a word)
    'kristan.': 'kristanismo',      #   1 /   7
    'kristanismo.': 'kristanismo',  #   1 /   7  (the full stop of a whole word)
    'arkeologio': 'arkeol.',        #   1 /   4
    'opt.': 'optiko',               #   2 /   5
    'histologio': 'histol.',        #   7 /   5  — within twice: the abbreviation
    'kirurgio': 'kirurg.',          #   8 /  13
    'retoriko': 'retor.',           #   7 /   6  — within twice: the abbreviation
    'mekaniko': 'mekan.',           #   3 /   4
    'meteor.': 'meteorol.',         #   2 /   6
    'paleontol.': 'paleont.',       #   4 /   5
    'paleontologio': 'paleont.',    #   1 /   5
    'elektr.': 'elektro',           #   9 /  20
    'milito': 'milit.',             #   6 /  10
    'imprim.': 'imprim-arto',       #   1 /   3  — the hyphen, the book's
    'imprimarto': 'imprim-arto',    #   2 /   1    way with its compound
    'militarto': 'milit-arto',      #   4 /   8    domains: it writes them so
    'shakoludo': 'shako-ludo',      #   1 /   1    in ALL the others —
    'skermarto': 'skerm-arto',      #   1 /   1    « banko-komerco », « natur-
    'yurocienco': 'yuro-cienco',    #  24 /  15    historio », « politiko-yuro ».
    'akustiko': 'akust.',           #   1 /   1  — equal: the abbreviation
    'diplomaco': 'diplomac.',       #   1 /   1
    'magnetismo': 'magnet.',        #   1 /   1
    'fortifikuro': 'fortifik.',     #   1 /   1
    'teratologio': 'teratol.',      #   1 /   1
    'versifado': 'versif.',         #   1 /   1
    'prosodio': 'prozodio',         #   1 /   1  — « prozodio » is a headword of
                                    #             the book, « prosodio » is not
    'teol.katol': 'teol. katol.',   # the space lost between two domains
    'trans.pri': 'trans., pri',
    'meteorologio': 'meteorol.',    #   1 /   6
    'tekniko': 'tekn.',             #   1 / 119
    'maronavigado': 'maro-navig.',  #   1 /   1
}
# The underline surveyed on the page carries the form THE AUTHOR WROTE; the
# field carries the one the edition keeps. To recognise that an underlined
# stretch is the domain -- and not send it to the list of unplaced rules -- one
# must therefore know both. An inverse table, for that use alone.
def _flat(x):
    """The string reduced to its letters: « netrans.,an » and « netrans., an »
    are the same domain, and so are « yuro-cienco » and « yurocienco »."""
    return re.sub(r'[^0-9a-zà-ÿ]', '', x.lower())


DOMAIN_VARIANTS = {}
for _v, _r in DOMAINS_UNIFORM.items():
    DOMAIN_VARIANTS.setdefault(_flat(_r), set()).add(_v)
DOMAINS_FLAT = {_flat(_v): _r for _v, _r in DOMAINS_UNIFORM.items()}


def other_form(u):
    """The form KEPT for a domain the page writes otherwise.

    The typist's rule covers « medicino »; the text returned carries
    « medic. ». Sought as it stands, the rule was no longer found, and the
    domain lost its italic. The stroke also breaks at the end of a line, and
    only a piece is left -- « cienco » for « yuro-cienco »: we therefore accept
    the piece too, from four letters up.
    """
    p=_flat(u)
    if not p:
        return None
    if p in DOMAINS_FLAT:
        return DOMAINS_FLAT[p]
    w=make_uniform(u)
    if w != u:
        return w
    if len(p) >= 4:
        for v, r in DOMAINS_UNIFORM.items():
            if p in _flat(v):
                return r
    return None
# We replace only the WHOLE component: the field sometimes enumerates two
# domains -- « (arit., algeb.) », « (fiz. e geom.) » -- and each counts as one
# component. A component of several words is a sentence of the author's, not a
# domain: « ante la milito universala di 1914-18 », « en la filozofio olima »,
# « olima geometrio » keep their word.
RE_COMPOSITION = re.compile(r'(\s*,\s*|\s+e\s+)')


def make_uniform(f):
    """Gives the domain back the form the author uses most often."""
    if not f:
        return f
    out=[]
    for part in f.split(') ('):
        ends=RE_COMPOSITION.split(part)
        for i in range(0, len(ends), 2):
            b=ends[i].strip()
            # The form sought is sought but for punctuation and case:
            # « Medicino », « kem » without its full stop and « kem. » are the same word.
            r=DOMAINS_UNIFORM.get(b) or DOMAINS_FLAT.get(_flat(b))
            if r:
                ends[i]=ends[i].replace(b, r)
            # The comma that separates two domains takes its space, like the four
            # hundred others: « (netrans.,an) » is written « (netrans., an) ».
            # Except between two figures: « (en Paris = 1,18 metro) », under « ulno »,
            # carries a decimal and not an enumeration.
            if (i+1 < len(ends) and not re.search(r'\d', ends[i])
                    and not re.search(r'\d', ends[i+2])):
                ends[i+1]=', ' if ',' in ends[i+1] else ' e '
        out.append(''.join(ends))
    return ') ('.join(out)


# An abbreviation, or the author's « e c. », does not end a sentence.
RE_ABBREV_FINAL = re.compile(r'(?:\be\s*c|\b[A-Za-z])\.$')


def _final_note(t, m):
    """Does the parenthesis CLOSE the sense, after a full stop?

    Then it is not a qualifier of domain but a REMARK, and it keeps the capital
    the author gave it: « (Dicesas precipue pri la homo qua evas plu kam 20
    yari) » under adulta, « (Uzesas ordinare en pluralo.) » under litanio,
    « (Anke metaf.) » under seven articles.

    The full stop does not suffice, nor does the place: the NEXT sense's domain
    is laid after a full stop too -- « Kontrea. (en lukto) La persono qua
    opozesas... » under adversa, « ...kombatis en lico. (metaf.) La persono
    qua... » under championo. What separates the two is that the remark leaves
    nothing behind it, whereas the qualifier announces what follows. Over the
    whole dictionary the rule raises 47 parentheses, and not one is a domain.
    """
    if t[m.end():].strip(' .'):
        return False
    av = t[:m.start()].rstrip()
    return av.endswith('.') and not RE_ABBREV_FINAL.search(av)


def point_senses(t):
    """The same rule WITHIN a sense's parentheses: not every qualifier is in
    the domain field -- « ajuro » carries its own in both its senses,
    « (arkitekt.) » pointed and « (stofo) » not, the latter being a whole word
    and not an abbreviation."""
    def _un(m):
        u = m.group(1)
        # A parenthesis that QUOTES a mark of punctuation is not a qualifier:
        # « komo. Puntuo-signo (,) qua indikas... », « cirkonflexo... signo (^) »,
        # « diezo... Signo (#) ». The trimming of the final comma, laid for the
        # domains with a tail -- « (netrans.,) » -- emptied komo's parenthesis
        # altogether, and the article defined the comma without showing it.
        if not re.search(r'[0-9A-Za-z\u00c0-\u00ff]', u):
            return m.group(0)
        if _final_note(t, m):
            return m.group(0)
        return '(' + make_uniform(to_lowercase(point_(u).rstrip(' ,'))) + ')'
    return re.sub(r'\(([^()]{1,120})\)', _un, t)


def _trim_end(s):
    """The sweep of the end of a string, which stops at the ellipsis."""
    m = re.search(r'[\s.\-—–]+$', s)
    if not m:
        return s
    d = list(re.finditer(r'\.{3,}', m.group(0)))
    return s[:m.start() + d[-1].end()] if d else s[:m.start()]


def analyse_(e, lexicon=None):
    t=e.get('teksto_brut')
    if t is None:
        t=reglue([s for _,s in e['lineoj']], lexicon)
    t=re.sub(r'\s+',' ',t).strip()
    for a,b in _texts_of().items():
        # Idempotence: the layer passes once at the cutting and once at the
        # analysis. When the key is a prefix of its replacement -- adding a
        # closing quotation mark, for instance -- the second pass added it a
        # second time. We abstain if the replacement is already laid.
        if a in t and b not in t: t=t.replace(a,b)
    # The facsimile keeps the space the typist left around an affix's hyphen;
    # the reading edition reglues. « - as. » is « -as », « - at - . » is
    # « -at- », « bo - . » is « bo- ». Failing which the headword was empty and
    # the article could not be found.
    # « -- protestanto. »: the double hyphen announces an article inserted after
    # the fact, it does not belong to the headword. A LONE hyphen, on the other
    # hand, is the affix (« -a », « -oz- ») and stays.
    t=re.sub(r'^[-–]{2,}\s+(?=[A-Za-z+"«])', '', t)
    t=re.sub(r'^([-+])\s+(?=[A-Za-zÀ-ÿ])', r'\1', t)
    t=re.sub(r'^([-+]?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\'’-]{0,20})\s+-\s*(?=\.)', r'\1-', t)
    t=re.sub(r'^([-+]?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\'’-]{0,20})\s+-\s*\.', r'\1-.', t)
    # A headword spaced letter by letter -- « l a t i r o » for « latiro »: the
    # typist gave emphasis that way, for want of an italic.
    m0=re.match(r'^((?:[A-Za-zÀ-ÿ] ){2,}[A-Za-zÀ-ÿ])(?=\s*\.)', t)
    if m0: t = m0.group(1).replace(' ','') + t[m0.end():]
    # A line struck out with quotation marks and hyphens: the typist cancelled
    # a whole line that way. What follows the language code and carries neither
    # letter nor figure says nothing -- but left there, that tail kept the code
    # from anchoring at the end of the string, and « exotera » passed for
    # « sen-lingua », its DEFIRS left in the middle of the definition.
    t=re.sub(r'[\s"\u00ab\u00bb\u2019\'.,;:_+*=/|\-\u2013\u2014]{6,}$', '', t)
    # The deletion sometimes carries LETTERS -- « myelito. ... - DEFIS.
    # vm-----m- ». The rule above, which requires a tail with neither letter nor
    # figure, let it through: the definition kept the scrawl, and the code, which
    # no longer anchored at the end of the string, was lost -- the article passed
    # for « sen-lingua ». A token carrying three hyphens in a row is no word of
    # the language; the book counts only five, all of them deletions.
    t=re.sub(r'[\s.,;:\-\u2013]*\S*-{3,}\S*[\s.,;:\-\u2013]*$', '', t)
    e['teksto']=t
    # The typescript marks the unofficial words with a superscript « + »; Ido
    # tradition writes an asterisk. We restore it here -- the facsimile keeps the
    # sign as struck.
    #
    # EVERYWHERE, and not on the headword alone: the sign also marks the variant
    # that follows it -- « timbro (+tembro) », « tarda (+retarda) » -- and the
    # words quoted in the definitions -- « +Seancar », « +Kluzajo »,
    # « +Asiejo-mashino ». Two contexts are excluded, where the « + » is the sign
    # of addition and not a mark: « 6 +1, o 4 +3 » under « sep », and the points
    # of a figure « AA'+BB'+CC' » under « involuciono ». We therefore require a
    # LETTER after the sign, and nothing alphanumeric before it.
    #
    # A side effect, and a wanted one: « augmentar » ended on « +DEFIS », and its
    # language code did not anchor -- the article passed for « sen-lingua ». With
    # the asterisk, which the reading of the code already admits, it anchors.
    t = re.sub(r"(?<![A-Za-zÀ-ÿ0-9'’])\+(?=[A-Za-zÀ-ÿ])", '*', t)
    # The headword can be in quotation marks -- « "alpari" », « "amen" » -- or
    # preceded by a stray full stop. We admit them, then take them off the word.
    t = t.lstrip('. ')
    # A quoted borrowing: the typescript frames in quotation marks the words
    # taken as they stand from another language -- « amen », « alpari »,
    # « angelus », « avoue ». We record the fact without putting it in the
    # headword: the search must go on finding « amen » typed without them.
    # The quotation marks must hold the WHOLE word, though. « "brokoli"-kaulo »
    # is not a quoted borrowing: it is an Ido word only the first element of
    # which is borrowed, and the editions, which frame the quoted headword in
    # guillemets, put a second pair around the first. We therefore refuse the
    # closing mark followed by a lower-case letter or a hyphen -- the word goes
    # on. Followed by a capital, it opens the definition: « "madras"Kapovesto »,
    # where the space was missed in the typing.
    e['citita'] = bool(re.match(r'^["\u00ab\u201c][^"\u00bb\u201d]{1,60}'
                                r'["\u00bb\u201d](?![a-zà-ÿ-])', t))
    # The accented letters belong to the word: without them « ampere » was cut
    # into « amp » and the rest fell into the definition.
    # A Latin or English phrase taken as a headword: the typescript frames it in
    # quotation marks -- « "a posteriori" », « "high life" ». The headword is then
    # the WHOLE phrase; without this rule « a posteriori » came down to « a » and
    # its definition began with « posteriori" ».
    mq=re.match(r'^["\u201c]?([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\'’-]*'
                r'(?: [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\'’-]*){0,2})["\u201d]'
                r'\s*(?:\.|(?=\s*[A-ZÀ-Ý(]))', t)
    if mq:
        e['vedetto']=mq.group(1); m=None; rest=t[mq.end():].strip()
    else:
        # The asterisk as much as the cross: the mark of the unofficial word is
        # already rendered above when it touches its word -- « +si » becomes
        # « *si » -- and the headword was no longer recognised. « si » carries two
        # articles, and the second, the adverb, lost its own.
        m=re.match(r'^([+*]?-?["\u201c]?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ"’\'\u201d-]*)\s*\.?', t)
        e['vedetto']= (m.group(1).strip('.').strip('"\u201c\u201d')
                       .replace('+','*',1)) if m else ""
        rest = t[m.end():].strip() if m else t
    # The noise that sometimes follows the code -- « - DEFIRS. --- » -- kept it
    # from anchoring at the end of the string, and the entry passed for
    # « sen-lingua ».
    # The ELLIPSIS, however, belongs to the text: it holds the place of the
    # complement, and eight articles end on one -- « Kambie di... » under « po »,
    # « Qua havas tri... » under « tri- », « Profite da... Destine di... » under
    # « por ». The sweep carried them off, except where a closing quotation mark
    # protected them (« qua tendencas a... »). We therefore keep the sweep's last
    # group of dots and remove only what follows it.
    rest = _trim_end(rest)
    e['lingui']=[]; e['kodo']=None
    me = RE_SPELLED.search(rest)
    if me:
        names=[SPELLED.get(x.strip(' .')) for x in me.group(1).split(',')]
        if all(names):
            e['lingui']=names; e['kodo']=me.group(1).strip()
            rest = _cut(rest[:me.start()])
    # The code is not always preceded by a hyphen. It sticks to the full stop
    # (« agar lo.DEFIS. »), to the closing parenthesis (« (anke metaf.)DEFIRS »),
    # but also to an OPENING parenthesis left open (« ...alambiko. (DEFIRS »), to
    # a comma (« ...deliberita, DEFIS ») or to nothing at all (« ...kavalrio
    # DEFIRS »). Twenty-one articles kept their code in the middle of the
    # definition that way and passed for « sen-lingua ». Case protects:
    # _lire_code requires a token mostly upper case, and the last word of a
    # definition never is.
    # The author sometimes adds a remark AFTER the code: « ... - DEFIS. (Ta vorto
    # ne esas sinonimo di mariajar... ) ». The code no longer being at the end of
    # the string, it was not read, and the article passed for « sen-lingua ». We
    # therefore set the remark aside long enough to read the code, then put it
    # back.
    note_ = ''
    if not e['kodo']:
        mr = re.match(r'^(.*?[-–]\s*[A-Za-z]{1,12}\s*\.)\s*(\(.{6,}\))\s*$',
                      rest, re.S)
        if mr and _read_code(re.search(r'([A-Za-z]{1,12})\s*\.$', mr.group(1)).group(1)):
            # The final full stop must fall: the search for the code requires
            # letters at the very end of the string.
            rest, note_ = mr.group(1).rstrip(' .'), mr.group(2)
    mj = None if e['kodo'] else re.search(r'(?:[-–.,()*]|\s|^)\s*([A-Za-z]{1,12})$', rest)
    if mj:
        li=_read_code(mj.group(1))
        if li:
            e['lingui']=li; e['kodo']=mj.group(1)
            rest = _cut(rest[:mj.start()])
    if note_:
        rest = (rest.rstrip(' -–.') + '. ' + note_) if rest else note_
    # The language code that is NOT at the end. The author has sometimes laid it
    # after a first sense and gone on -- « cilio. (anat.) Pilo... - F. (bot.)
    # Sorto di pilo... - F. » -- or the typing left a cinder behind it: « - DE. s
    # q c i » under hidranto, « - DEFIS. pre- » under studiar. The code then
    # stayed IN THE MIDDLE of the definition, where it has no business, and the
    # article passed for « sen-lingua ».
    #
    # We touch only two sure cases: the article has no code, or it already carries
    # the SAME one. A different code in the middle of the text is something else
    # -- under « staciono », « (autofiakri - F. taxi - autobusi, e c.) » gives the
    # French word, it does not close the article.
    #
    # When what follows opens a sense -- a domain in parentheses, or a hyphen
    # followed by a capital -- the cut is made there: the code marked the end of a
    # sense. We note it with a sign the cutting will read.
    mi = re.search(r'\s*[-–]\s*([A-Z][A-Zl]{0,11})\.?\s+(?=\S)', rest)
    li = _read_code(mi.group(1)) if mi and mi.group(1) != 'L' else None
    if li and (not e['kodo'] or e['kodo'].upper() == mi.group(1).upper()):
        if not e['kodo']:
            e['lingui']=li; e['kodo']=mi.group(1)
        left_ = rest[:mi.start()]; right_ = rest[mi.end():].lstrip()
        mq = re.match(r'\(([a-zà-ÿ]{2,12})\.?\)', right_)
        if (mq and mq.group(1) in ABBREVIATE) or re.match(r'[-–]\s*[A-ZÀ-Ý]', right_):
            rest = left_.rstrip(' -–.,;:') + CUT + right_
        elif re.search(r'[.!?)]\s*$', left_):
            rest = left_.rstrip(' -–.,;:') + '. ' + right_
        else:
            rest = left_.rstrip() + ' ' + right_
    # The number of a sense hanging at the end of the article, with nothing after
    # it: « forsan. Adverbo qua signifikas "..." - II. » -- the typist announced a
    # second sense she did not type. Alone, the number says nothing, and the
    # edition sets aside its like in the middle of the text already. We require
    # the hyphen that announces it, so as not to trim « la rejo Francisko I ».
    rest = re.sub(r'[.;,]?\s*[-–]\s*(?:I{1,3}|IV|VI{0,3}|IX|X)\.?$', '', rest)
    rest = rest.lstrip(' -–.,;:')
    # « ed. (Videz "e"). »: the parenthesis carries a CROSS-REFERENCE, not a
    # domain. Taken for a domain, it left the article with no definition at all.
    mf=None if re.match(r'^\(\s*(?:Videz|videz|Vid\.)\b', rest) else (
        RE_DOMAIN.match(rest) or RE_DOMAIN2.match(rest))
    # The domain often carries stray punctuation, inherited from the typing:
    # « zool, », « .trans », « patol, ». And it can contain a date, whose figures
    # are to be straightened as elsewhere -- « olim, ante l9l5 ».
    e['fako']= make_uniform(to_lowercase(point_(to_digits(mf.group(1).strip(' .,;:'))))) if mf else None
    if e['fako']: e['fako']=formulas(e['fako'])
    if mf: rest = rest[mf.end():]
    # Two parentheses in a row: the second qualifies the first and not the
    # sense. « pensar. (trans. e netrans.) (ulo, ad ulo, pri ulu od ulo) » --
    # the government belongs to the marker of transitivity, not to the
    # definition, which therefore began with an orphaned parenthesis.
    if e['fako']:
        m2 = re.match(r'^[\s.,;:\u2013-]*\(([^()]{1,40})\)\s*\.?\s*(?=[-\u2013]?\s*(?:[IVX]{1,4}\.|[A-Z\u00c0-\u00dd]))', rest)
        if m2:
            # The second parenthesis is a piece of information of the same nature as
            # the first, and the same treatment is due to it: initial lower case,
            # figures straightened, the FULL STOP given back to the abbreviation.
            # Reglued as it stood, it came out bare when its neighbours were pointed --
            # « (trans.) (tekn) », « (netrans.) (patol) », « (netrans.) (Kemio) ».
            second_ = make_uniform(to_lowercase(point_(to_digits(m2.group(1).strip(' .,;:')))))
            e['fako'] = "%s) (%s" % (e['fako'], second_)
            rest = rest[m2.end():]
    rest = rest.lstrip(' -–.,;:')
    # Elision: « ka(d) », « on(u) », « a(d) ». The letter in parentheses belongs
    # to the word -- it is added only before a vowel. It was read as a domain, and
    # displayed apart from the headword, in another colour.
    #
    # It is one only if the headword is short AND the parenthesis holds ONE
    # letter. Without that double condition we would catch « afina (ad) »,
    # « plena (de) », where the parenthesis carries a governed preposition and not
    # an elided letter.
    # Interjection: the exclamation mark belongs to the word, not to the
    # definition. « he » reads « he! », and its definition begins after it.
    if rest.startswith('!') and e['vedetto'] and len(e['vedetto'].lstrip('*')) <= 6:
        e['vedetto'] = e['vedetto'] + '!'
        rest = rest[1:].lstrip(' -–.,;:')
    if (e['fako'] and len(e['fako'])==1 and e['fako'].isalpha()
            and e['vedetto'] and len(e['vedetto'].lstrip('*')) <= 3):
        e['vedetto'] = "%s(%s)" % (e['vedetto'], e['fako'])
        e['fako'] = None
    e['latina']= [x.strip(' .') for x in RE_LATIN.findall(rest)]
    rest = RE_LATIN.sub('', rest).strip(' -–')
    # A name surveyed by eye prevails: the machine cannot know that
    # « capparia spi nosa » is « capparia spinosa », neither of the two pieces
    # being a Latin word.
    _man = latins_manual().get("%s@%d:%d" % (e.get('vedetto'), e.get('image', -1),
                                                e.get('ligno', -1)))
    if _man:
        e['latina'] = [x.strip() for x in _man.split(';') if x.strip()]
    e['simbolo']= None
    # A NUMBER of sense in parentheses is not a domain: « romano. (I) Verko
    # literaturala... », « vice. (l) qua pre-nominesis... » -- the « l » being the
    # typist's 1. The editions renumber the senses themselves; kept as a domain,
    # the number was displayed in the domain's place.
    if e['fako'] and re.fullmatch(r'(?:[IVX]{1,4}|[a-z]|[0-9]|l)', e['fako'].strip()):
        e['fako'] = None
    # The number can PRECEDE a true domain: « ramo. (l) (bot.) Mikra
    # brancho... ». The merging of the two parentheses then kept both, and the
    # article announced itself « (1) (bot.) ». We throw away the number alone.
    if e['fako']:
        m1 = re.fullmatch(r'(?:[IVX]{1,4}|[a-z]|[0-9]|l)\)\s*\((.+)', e['fako'].strip())
        if m1: e['fako'] = m1.group(1)
    # A chemical FORMULA laid just after the headword -- « asparagino. (C8 H8
    # AZ2 O6). Substanco... » -- is not a domain either: it is the same piece of
    # information as « Simbolo kemiala : ... » elsewhere in the book, and it goes
    # to the same field, to be rendered the same way.
    if (e['fako'] and e['simbolo'] is None
            and re.fullmatch(r"[A-Z][A-Za-z0-9\u2080-\u2089\s.'()/-]*", e['fako'].strip())
            and re.search(r'[0-9\u2080-\u2089]', e['fako'])):
        e['simbolo'] = e['fako'].strip()
        e['fako'] = None
    senses=[_cut(x.lstrip(' -–.,;:')) for m in rest.split(CUT)
           for x in RE_SENSE.split(m) if x.strip(' -–.,;:')]
    e['senci']= senses if senses else ([rest] if rest else [])
    # The numbering in parentheses whose « (1) » went to the domain: we cut in
    # the place of the numbers that remain (see RE_ORFA_NUM).
    S=[]
    for s in e['senci']:
        if RE_ORPHAN_NUM.search(s) and not RE_NUM_FIRST.search(s):
            S.extend(x for x in (_cut(y.lstrip(' -–.,;:'))
                                 for y in RE_ORPHAN_NUM.split(s)) if x)
        else:
            S.append(s)
    e['senci']=S
    # A recovery: the code can be left at the end of the LAST sense when a note
    # followed it in the original and the cutting into senses isolated it. We
    # survey it there too -- and if it doubles the one already read, we take it
    # out of the text.
    if e['senci']:
        mk = re.search(r'(?:[-–.,()*]|\s)\s*([A-Za-z]{1,12})\s*\.?\s*$', e['senci'][-1])
        if mk:
            li=_read_code(mk.group(1))
            if li:
                if not e['kodo']: e['lingui']=li; e['kodo']=mk.group(1)
                q=e['senci'][-1][:mk.start()].rstrip(' -–.,;:')
                if q: e['senci'][-1]=q
                else: e['senci'].pop()
    if e['image'] in UNOFFICIAL_PAGES and e['vedetto'] and not e['vedetto'].startswith('*'):
        e['vedetto'] = '*' + e['vedetto']
    v=e['vedetto']
    e['drapeli']=list(e.get('drapeli_pre',[]))
    if not v: e['drapeli'].append('sen-chefvorto')
    elif not _ending_ok(e): e['drapeli'].append('finalo-nekustumala')
    if not e['kodo']: e['drapeli'].append('sen-lingua')
    # The flag « korektigita » said « at least one cell corrected automatically »
    # -- a piece of provenance, not a doubt. Every definition having been re-read
    # one by one, it no longer designated work remaining: it is withdrawn. The
    # count stays in e['korektita'], for whoever wants to measure.

    if e['image'] in (546,547): e['drapeli'].append('pagino-nefidinda')
    return e

# The last two pages of the book carry a separate list, announced by its own
# title: « LISTO de vorti qui, pro lia teknikaleso e probiteso multa-yara,
# probable adoptesos da la Akademio di Ido ». They are therefore, by
# definition, words not yet official -- the asterisk is due to them, but the
# typist did not strike it, the title standing for the whole list.
UNOFFICIAL_PAGES = (637, 638)

def _order_key(v):
    """The headword as it FILES, its leading mark taken off.

    The asterisk of the unofficial word and the hyphen of the affix are not
    letters, and the book does not file them: « -acho » is between « acetono »
    and « aciano », « -eyo » between « exutorio » and « ez ». Compared as they
    stood, they came before every letter -- each of the 126 affixes and
    unofficial words therefore broke the order by its mark alone, and dragged
    its neighbour with it. Eighty-five flags said nothing but that.

    The interjection's exclamation mark files no more than they do: « ah! » is
    looked for at « ah ». Nor does the suffix's FINAL hyphen -- « -an- » files
    with « an » -- nor the space of a Latin phrase: the book lays
    « a posteriori » between « apostata » and « apostemo », hence at
    « aposteriori ».
    """
    # The accent does not file either: « ampèremetro » precedes « ampla » in
    # the book, which only an unaccented « e » explains. The typescript carries
    # accents on borrowed names alone -- ampère, Roentgen.
    v = unicodedata.normalize('NFD', v.lower())
    v = ''.join(c for c in v if not unicodedata.combining(c))
    # The quotation marks file no more than the rest, wherever they are: the
    # book files « "brokoli"-kaulo » at « brokoli-kaulo ». The non-breaking
    # space that goes with them in the edition goes with them here.
    v = v.lstrip('*+"«.-').rstrip('!').rstrip('-')
    return re.sub('[\\s\u00a0"«»\u201c\u201d]', '', v)


# The ENDING does not count in the book's filing. It is a rule the book does
# not state, but follows: « aktinio » precedes « aktinika » because the author
# files « aktini » before « aktinik », the -o and the -a not entering into it.
# Compared as whole words, those two headwords passed for a disorder, and nine
# hundred others with them.
#
# The author does not always keep to it: he writes « astrakano » then « astro »,
# where the root alone would have it the other way -- « astr » before
# « astrakan ». Both readings are therefore kept, and the flag is raised only
# if BOTH are broken: what neither convention explains.
ENDINGS_ORDER = ('ar', 'ir', 'or', 'o', 'a', 'e', 'i')


def _root_key(v):
    """The headword filed, its ending taken off as well."""
    k = _order_key(v)
    for d in ENDINGS_ORDER:
        if k.endswith(d):
            return k[:-len(d)]
    return k


# The suffix counts no more than the ending, and for the same reason: the
# filing follows the ROOT. « venerala » precedes « veneracar » because the
# first is vener-al-a and the second venerac-ar; « inventariar » precedes
# « inventar » because both come out of invent-. That is how several
# dictionaries of Ido analyse them, and the book files them likewise.
#
# The stripping stops at ONE suffix, and never goes below five letters:
# without that bound « metalo » would become « met- » and « histerio »
# « hist- ». This third reading can only TAKE flags away -- three are needed
# to raise one -- never add any.
SUFFIXES = tuple(sorted(
    ('ari', 'atr', 'ebl', 'end', 'eri', 'esk', 'estr', 'ier', 'ind', 'ism',
     'ist', 'oid', 'ach', 'ad', 'aj', 'al', 'an', 'ar', 'ed', 'eg', 'em',
     'er', 'es', 'et', 'ey', 'id', 'if', 'ig', 'ik', 'il', 'in', 'iv', 'iz',
     'oz', 'ul', 'um', 'ur', 'uy'), key=len, reverse=True))


def _stem_key(v, mini=5):
    """The headword filed, its ending and ONE suffix taken off."""
    r = _root_key(v)
    for x in SUFFIXES:
        if r.endswith(x) and len(r) - len(x) >= mini:
            return r[:-len(x)]
    return r


# The book ends with two separate lists, each of which begins the alphabet
# again: an addendum of five articles (image 636) and the « LISTO de vorti qui
# ... probable adoptesos da la Akademio di Ido » (images 637-638). Their first
# headword necessarily goes backwards in the alphabet; it is not a disorder.
SECTION_START = (636, 637)


# The grammatical nature, as the book announces it itself at the head of a
# definition: « Prepoziciono qua indikas... », « Interjeciono qua expresas... »
RE_GRAMMAR = re.compile(
    r'^\(?\s*(?:prepoziciono|konjunciono|pronomo|adverbo|interjeciono'
    r'|sufixo|prefixo|artiklo|partikulo|des?inenco)', re.I)


def _ending_ok(e):
    """Is the headword's ending that of an Ido word?

    The question has sense only for a WORD OF THE LANGUAGE. Three families
    escape it, and reporting them was an error of category:

      * the AFFIX -- « -eyo », « poli- », « bo- » -- whose hyphen says
        precisely that it is not a word. 78 cases;
      * the word the book itself declares GRAMMATICAL: « an. Prepoziciono qua
        indikas relato di kontigueso », « fi! Interjeciono qua expresas la
        desprizo di ulo ». Ido gives no ending in -o/-a/-e/-i to its
        prepositions, pronouns and interjections. 51 cases;
      * the QUOTED BORROWING -- « amen », « angelus », « cambium » -- which the
        author frames in quotation marks because it is not Ido. 50 cases.

    What is left -- the numerals « cent », « dek », the note names « b », « c »,
    « d », and the prepositions the book does not qualify -- is legitimate too,
    but nothing in the text lets one say so.
    """
    v = e.get('vedetto') or ''
    if not v: return True
    if v.startswith('-') or v.rstrip('!').endswith('-'): return True
    if e.get('citita'): return True
    S = e.get('senci') or []
    if S and RE_GRAMMAR.match(S[0].lstrip('( ')): return True
    return any(v.lower().endswith(f) for f in ENDINGS_OK)


# The order of the letters of the code is the book's: D E F I R S, then L --
# the Latin, which ninety-two codes put last -- then the rare languages.
# Twenty-two codes break it: « DEFSR » under alibio, « ED » under sendar,
# « FISDE » under grano, « dEFIRS » or « DEFlS » where the capital and the I
# were damaged in the reading. Nothing repeats in them -- it is the order alone
# that differs -- and the edition puts it back, the raw line keeping the page's
# spelling. The notations that SPELL the language out are exempt: « FDSued »,
# « DERPol », « Gr », « Ned » are not runs of letters.
ORDER_CODE = 'DEFIRSLPGN'


def order_codes(ent):
    """Puts the letters of the code back into the book's order. Returns the count laid."""
    n = 0
    for e in ent:
        k = e.get('kodo')
        if not k or not k.isalpha(): continue
        if k in ABBREVS or k in SPELLED or any(k.endswith(a) for a in ABBREVS): continue
        L = ['I' if c == 'l' else c.upper() for c in k]
        if not all(c in ORDER_CODE for c in L): continue
        new_ = ''.join(sorted(L, key=ORDER_CODE.index))
        if new_ != k:
            e['kodo'] = new_
            e['lingui'] = [LANGUAGES[c] for c in new_]
            n += 1
    return n


def order_flags(ent):
    """Lays the order flag over the whole list, and returns the count laid.

    The flag is read off the RUN of headwords: it is therefore laid again in
    full as soon as a headword changes, or an article is added. A headword
    breaks the order when it goes backwards on ALL THREE readings -- whole
    word, root, and root stripped of its suffix (see _klavo_radiko and
    _klavo_radikalo) -- and when it does not open one of the final lists.
    """
    for e in ent:
        if 'ordino-ruptita' in (e.get('drapeli') or []):
            e['drapeli'].remove('ordino-ruptita')
    v=[_order_key(e.get('vedetto') or '') for e in ent]
    r=[_root_key(e.get('vedetto') or '') for e in ent]
    d=[_stem_key(e.get('vedetto') or '') for e in ent]
    first={}
    for e in ent: first.setdefault(e.get('image'), id(e))
    n=0
    for i in range(1, len(v)):
        if not (v[i] and v[i-1] and r[i] and r[i-1] and d[i] and d[i-1]): continue
        if v[i] >= v[i-1] or r[i] >= r[i-1] or d[i] >= d[i-1]: continue
        if (ent[i].get('image') in SECTION_START
                and first.get(ent[i].get('image')) == id(ent[i])): continue
        # The four Latin phrases -- « a posteriori », « ex libris » -- are filed now
        # as one word, « aposteriori » between « apostata » and « apostemo », now as
        # two, « ex libris » before « exajerar ». The book does not say which of the
        # two; we therefore do not count them.
        if ' ' in (ent[i].get('vedetto') or '') or ' ' in (ent[i-1].get('vedetto') or ''):
            continue
        ent[i].setdefault('drapeli', []).append('ordino-ruptita'); n+=1
    return n


def e_ok(e):
    v=e.get('vedetto') or ""
    # A headword of a single letter is legitimate: « a », « b », « c »... are the
    # notes of the scale. Only the EMPTY headword is not an article.
    if not v: return False
    # « p. 83, an-pos "cetato" : » is not an article but a cross-reference from
    # the errata, saying where to insert the article that follows.
    if re.match(r'^p\.\s*\d', e.get('teksto') or ''): return False
    # The running folio, read as text: « 110 » decodes « llO », « 111 » « lll ».
    # Such a token, with no definition, is not a word.
    if not (e.get('senci') or []) and re.fullmatch(r'[lI1O0]{2,4}', v): return False
    return True

# The phrase always presents itself the same way: a group beginning with a
# capital and followed by a colon. The author's underline confirms it; the form
# finds it, even where the proofreading has corrected a slip and the string
# surveyed on the grid is no longer found as it stood.
# The COMMA is part of the phrase: the author sometimes stacks parallel phrases
# that share a definition -- « Extraktar radiko, quadrata, kubala, di nombro :
# ... », that is, the square root and the cube root at one stroke; « La
# matematiki pura, la mekaniko pura : ... ». Without it, the definition that
# follows swelled the body of the PRECEDING phrase, which could do nothing
# about it.
# The LOWER CASE is admitted, under a condition. The capital was only a clue:
# what announces a phrase is the underline and the colon. When the sense opens
# on its domain, the word that follows keeps its lower case -- « agregar. ...
# III. (en la universitato di Francia) agregito : la persono qua... » -- and
# the phrase went unnoticed. We therefore accept it, but a phrase in lower case
# must QUOTE the headword, as every one-word phrase already does:
# « agregito » under « agregar ». Failing which the examples the author
# enumerates after an « Exemple : » -- « krucagar : agar per kruco » under
# « -agar » -- and his conditions of use -- « kun radiko nomala : » under
# « -ig- » -- would have detached themselves as sub-entries, when they belong
# to the sentence.
# The phrase sometimes carries the CROSS of the unofficial word: « *skrino » is
# the word of the cinema, and the author names it as such under « skreno ». The
# mark is therefore read with it, and the two safeguards that follow -- the
# capital, the link with the headword -- have no business applying to it: a
# word marked with the cross IS a word the author names, never the adverb of a
# gloss.
RE_PHRASE=re.compile(r'(?:^|(?<=[.;:]\s)|(?<=\)\s)|(?<=[-\u2013]\s))'
                     r'([*+]?[A-Za-zÀ-ÿ][A-Za-zà-ÿ]+(?:[-, ]+[A-Za-zà-ÿ]+){0,6})\s*:\s')
# A leading qualifier: « (matem.) », « (kemio) ». A single letter or figure in
# parentheses is an enumeration number, not a domain.
RE_QUAL=re.compile(r'(?:[-\u2013\s]*\((?![A-Za-z0-9]\))[^()]{1,60}\)\s*)+$')
RE_NUMBER=re.compile(r'\(([A-Za-z0-9])\)\s*$')
# The same qualifier, but at the HEAD: « *botono. (elektr.) Mikra
# cilindro... » carries its domain after the headword, not before it like
# « (geom.) arko inflexita : ... ». It goes to the `fako` field in both cases.
RE_QUAL_HEAD=re.compile(r'^(?:\((?![A-Za-z0-9]\))[^()]{1,60}\)\s*)+')
# The phrase sometimes opens a PARENTHESIS: « estado. Eso mentala... (estado
# civila : la situeso di persono kom filio legitima o ne-legitima...) ». It is
# the same thing as elsewhere -- underlined, followed by the colon, carrying its
# own definition -- and the parenthesis does not degrade it: « estado civila »
# is looked for as « estado ». It is often written in lower case there, the
# parenthesis standing for the opening; we therefore do not require the capital
# here.
# A WHOLE ARTICLE slipped in parentheses into the definition of another:
# « butono. ... (*botono. (elektr.) Mikra cilindro, ek materio
# elektro-ne-konduktiva...) ». It is not a phrase but a separate word, with its
# domain and its definition -- and the asterisk, with which the author marks the
# word not yet official, distinguishes it from the domain abbreviation of the
# same shape: « (trans. ... », « (anat. ... », « (metaf. ... ». The book counts
# only one; without it, « botono » could not be looked for.
#
# The phrase in parentheses CARRIES THAT MARK TOO, and the two patterns
# between them left the case out: RE_SUBENTRY wants the full stop of a whole
# article, RE_PHRASE_BRACKET wanted a letter hard against the parenthesis. So
# « certa. ... (*certena : Qua ne dubitas pri la vereso...) » was neither, and
# « certena » was not a sub-entry though its rule had been measured. The mark
# is admitted here as RE_PHRASE admits it outside the parenthesis: a « + » in
# the typescript designates a WORD, which is exactly what a sub-entry is.
RE_SUBENTRY=re.compile(r'\(\s*(\*[A-Za-zÀ-Ý][A-Za-zà-ÿ-]{2,})\s*\.\s*')
RE_PHRASE_BRACKET=re.compile(r'\(\s*([*+]?[A-Za-z\u00c0-\u00ff][A-Za-z\u00e0-\u00ff]*'
                            r'(?:[- ][A-Za-z\u00e0-\u00ff]+){0,4})\s*:\s')
# The grammatical endings of Ido: participles, verb, noun, adjective, adverb,
# plural. We take them off to compare two words by their ROOT -- « inflexar »
# and « arko inflexita » have not the same end, but the same word. From the
# LONGEST to the shortest: « inflexita » must return « inflex », not
# « inflexit », failing which the verb is not recognised in it.
FINALS=('anta','inta','onta','ata','ita','ota',
        'ar','as','is','os','us','o','a','e','i')


def _root_of(m):
    """The root of the word, its ending taken off.

    We take off nothing that would leave fewer than four letters: on so short a
    stem, two unrelated words resemble each other too closely -- « bear » is not
    « be- », and « arko » is not « ark- ».
    """
    m=m.lower().strip(' .,;:\u00ab\u00bb"\'')
    for d in FINALS:
        if m.endswith(d) and len(m) - len(d) >= 4:
            return m[:-len(d)]
    return m


def _quotes_headword(spot, headword_):
    """Does the phrase take up the article's word?

    Within a parenthesis, the colon also introduces the GLOSS, which is not a
    phrase: « (antonimo : inflaco) », « (analogie : sur la kapo di ula repteri) »,
    « (simbolo kemiala : Ir) ». The author underlines them as he does the
    phrases -- the underline therefore does not separate them. What separates
    them is that the phrase QUOTES the article's word, in one form or another:
    « estado civila » under « estado », « arko inflexita » under « inflexar »,
    « relate » under « relatar ». The gloss speaks of something else.

    Outside a parenthesis, the capital distinguished the two; within one the
    phrase loses its capital, and this quotation stands in its place.
    """
    r=_root_of(headword_)
    if len(r) < 4: return False
    # We compare by the BEGINNING: « konstanta » returns « konst » -- the ending
    # -anta passes there for a participle it is not -- where « konstanto »
    # returns « konstant ». Requiring equality separated the two; the prefix
    # reunites them, without for all that bringing « nun » near « moloso ».
    for w in spot.split():
        u=_root_of(w)
        if len(u) < 4: continue
        if u == r or u.startswith(r) or r.startswith(u): return True
    return False


def _close(t, i):
    """The index of the parenthesis that closes the one opened at `i`, or None.

    The typescript does not always close: « inflexar » opens a parenthesis the
    next line, truncated, never closed. Counting the levels says so without
    error, and does not take the closing of an INTERIOR parenthesis --
    « ... tangenta per olia somiti (quale la embracilo tipografiala) » -- for
    that of the phrase.
    """
    n=0
    for j in range(i, len(t)):
        if t[j] == '(': n += 1
        elif t[j] == ')':
            n -= 1
            if n == 0: return j
    return None


def _contains(whole, part_of):
    """Is `parto` a piece of `tuto`, at whole words?

    The comparison is made word by word, punctuation off: the rule surveys
    « quadrata » where the phrase writes « quadrata, ».
    """
    def _words(s): return [w.strip('.,;:') for w in s.lower().split() if w.strip('.,;:')]
    A, B = _words(whole), _words(part_of)
    if not A or not B or len(B) > len(A): return False
    return any(A[i:i+len(B)] == B for i in range(len(A)-len(B)+1))


def _agrees(a, b):
    """Do two strings designate the same phrase?"""
    # The cross of the unofficial word does not separate two spellings of the
    # same word: the survey returns « +skrino », the typeset text « *skrino ».
    a=a.lower().strip(' .:').lstrip('*+'); b=b.lower().strip(' .:').lstrip('*+')
    if a == b: return True
    # Word by word, the final punctuation off: the rule of « radiko » stops at
    # « Extraktar radiko, quadrata » where the phrase writes « quadrata, ».
    # Without that the comma, present on one side and not the other, made the
    # comparison of the beginnings fail.
    pa=[w.strip('.,;:') for w in a.split()]
    pb=[w.strip('.,;:') for w in b.split()]
    if not pa or not pb: return False
    # The first word suffices if it is long: « Prpporciono » re-read
    # « Proporciono » stays recognisable, and the rest is identical.
    import difflib
    if len(pa) == len(pb):
        return difflib.SequenceMatcher(None, a, b).ratio() >= 0.85
    # The rule sometimes stops before the end of the phrase -- « Elektro » for
    # « Elektro pozitiva ». A long enough beginning is identification enough.
    short_, long_ = (pa, pb) if len(pa) < len(pb) else (pb, pa)
    if long_[:len(short_)] == short_ and len(" ".join(short_)) >= 5: return True
    return False


START="\ue000"; END="\ue001"     # bounds of the italic, invisible to the text


def mark_(t, patterns, placed=()):
    """Frames with bounds every passage to be set in italic.

    We lay the longest first: « (aludante persono) » contains « persono », and
    the reverse order would have cut the parenthesis in two.
    """
    if not t or not (patterns or placed): return t
    spans=[]
    # The italics laid by eye: the context gives the place, the braces say what
    # takes it. They pass BEFORE the rules, which must not re-cut a passage
    # already bounded.
    for with_, sp in placed:
        i=t.find(with_)
        if i < 0: continue
        for a,b in sp: spans.append((i+a, i+b))
    for u in sorted(patterns, key=len, reverse=True):
        for m in _wholes(u, t):
            if any(not (m.end() <= a or m.start() >= b) for a,b in spans): continue
            spans.append((m.start(), m.end()))
    if not spans: return t
    out=[]; preceding=0
    for a,b in sorted(spans):
        out.append(t[preceding:a]); out.append(START+t[a:b]+END); preceding=b
    out.append(t[preceding:])
    return "".join(out)


def _wholes(u, t):
    if not u.strip(): return []
    mo=re.compile(r'(?<![A-Za-z\u00c0-\u00ff])'
                  + r'\s+\*?'.join(re.escape(w) for w in u.split())
                  + r'(?![A-Za-z\u00c0-\u00ff])', re.I)
    return list(mo.finditer(t))


# A phrase that is a PROPER NOUN keeps its capital. The book counts only one:
# the Grand Orient of freemasonry.
PROPER_PHRASES = ('Granda Oriento',)


def lowercase_phrase(l):
    """The phrase is written as a headword is: in lower case."""
    if not l or l in PROPER_PHRASES or not l[0].isupper(): return l
    return l[0].lower() + l[1:]


def capital_start(t):
    """Initial capital, like the ten thousand other definitions of the book.

    We touch only a definition that BEGINS with a lower-case letter: one that
    opens on a parenthesis -- « (bot.) ... » -- carries a domain, and the domain
    is written in lower case. A cross-reference of a single very short word --
    « ica : ca » -- is not a sentence and keeps its own.
    """
    if not t: return t
    i=0
    while i < len(t) and t[i] in ' \ue000\ue001': i += 1
    if i >= len(t) or not t[i].isalpha() or not t[i].islower(): return t
    u=t.strip()
    if len(u) <= 3 and ' ' not in u: return t
    return t[:i] + t[i].upper() + t[i+1:]


# --- The chemical symbol ----------------------------------------------------
#
# The book writes it ten ways: « . – Simbolo kemiala : Al », « . Simbolo
# kemiala : Al » with no hyphen, « . – Simbolo kem. Rh » abbreviated and with no
# colon, in lower case, or as an aside in parentheses. Worse than the
# unevenness: where the author underlined the label, « Simbolo kemiala : » has
# exactly the shape of a phrase -- capital, colon, definition -- and went off to
# open a sub-entry paragraph, in SIXTY articles out of seventy-five. But it is
# not a word of the language: it is a label, of the same nature as the Latin
# name. We therefore take it out of the text, into a field of its own, and both
# editions render it in one way.
SYMBOL_LABEL = "simbolo kemiala"
# The four spellings of the label, to recognise the rule that covered it:
# the stroke cuts it short -- « Simb. kem », « Simbolo kemial » -- as often as
# it takes it whole.
LABELS = ("simbolo kemiala", "simb. kemiala", "simbolo kem.", "simb. kem.")
# « Simbolo » is abbreviated too -- « Simb. kem. Au » under « oro », « Simb.
# kemiala : Br » under « bromo » -- and « kem » is met bare. The four labels
# cross freely; the pattern takes them all.
RE_SYMBOL = re.compile(r'[\s.,;:–-]*(\()?\s*simb(?:olo|\.)\s*kem(?:iala|\.)?'
                        r'\s*[:.]?\s*', re.I)
# A symbol or a formula holds in few signs -- the longest in the book is
# « C₁₆, H₂₆, N₂, O₁₀ ». Beyond that it is no longer a symbol: under « ruteno »
# the following article, « rutino », merged into the text at the decoding. We
# then extract NOTHING, and the defect stays visible rather than be made up.
SYMBOL_LENGTH = 40


_SYMBOLS = None


def symbols_manual(file_=f"{T}/symbols.txt"):
    """The symbols surveyed by eye on the facsimile, where the decoding lost
    them. The same key as subwords.txt: vedetto@image:ligno."""
    global _SYMBOLS
    if _SYMBOLS is None:
        _SYMBOLS = {}
        if os.path.exists(file_):
            for l in open(file_, encoding='utf-8'):
                l = l.rstrip("\n")
                if not l.strip() or l.startswith('#'):
                    continue
                p = l.split("\t")
                if len(p) >= 2 and p[0].strip() and p[1].strip():
                    _SYMBOLS[p[0].strip()] = p[1].strip()
    return _SYMBOLS


_LATINS = None


def latins_manual(file_=f"{T}/latins.txt"):
    """The scientific names put right by eye. The same key as symbols.txt."""
    global _LATINS
    if _LATINS is None:
        _LATINS = {}
        if os.path.exists(file_):
            for l in open(file_, encoding='utf-8'):
                l = l.rstrip("\n")
                if not l.strip() or l.startswith('#'):
                    continue
                p = l.split("\t")
                if len(p) >= 2 and p[0].strip() and p[1].strip():
                    _LATINS[p[0].strip()] = p[1].strip()
    return _LATINS


def _code_not_symbol(e):
    """A language code that EQUALS the chemical symbol is not a code.

    The symbol sometimes closes the article, with nothing behind it:
    « palado. ... Simbolo kemiala : Pd. » The decoding read that « Pd. » as a
    language code and drew « portugalana, germana » from it. The article carries
    none.
    """
    k = (e.get('kodo') or '').strip('.').lower()
    if k and k == (e.get('simbolo') or '').strip('.').lower():
        e['kodo'] = None
        e['lingui'] = []
        if 'sen-lingua' not in e.get('drapeli', []):
            e.setdefault('drapeli', []).append('sen-lingua')


_LAT_WORD = r'(?!(?:e|o|ed|od)(?![a-z-]))[a-z][a-z-]*'
_LAT_NAME = _LAT_WORD + r'(?:\s+' + _LAT_WORD + r'){0,3}'
RE_LATIN_INLINE = re.compile(
    r'(?<![A-Za-zÀ-ÿ])L\.\s*(' + _LAT_NAME + r')'
    r'(?:\s*[,;]?\s*(?:[eo]d?)\s+(' + _LAT_NAME + r'))?')


def latins_inline(e):
    """The scientific name the SENTENCE keeps.

    RE_LATINA takes the name the author lays apart -- « ... kompozaji". L.
    artemisia absinthium » -- and takes it out of the text to carry it to the
    field. But the name also slips INTO the sentence, where the syntax holds it:
    « Familio de insekti di qui la tipo esas L. acarus, kun korpo... » no longer
    reads if it is taken out. Thirteen articles are in that case, and their
    field stayed empty -- the name could not be looked for, and neither edition
    announced it.

    We therefore COPY it, without touching the text. Two « L. » do not announce
    a name: the one that opens an example -- « Kom ex. : L. que en neque » under
    enklitiko -- and the one that names the language -- « ica vice ca, en L.
    iscala vice scala » under prostezo. The one is recognised by its « ex. »,
    the other by its « en ».

    The binomials go in pairs -- « L. ostrea edulis e gryphea angulata » -- and
    the conjunction is not a word of the name: without excluding it, the first
    binomial bit into it and returned « ostrea edulis e gryphea ».
    """
    # We read the SENSES, not the structure: the latter is rebuilt at the end of
    # the chain, and reading it here would make the pass depend on its rank.
    new_ = []
    for t in (e.get('senci') or []):
            for m in RE_LATIN_INLINE.finditer(t):
                ahead = t[max(0, m.start() - 14):m.start()]
                if re.search(r'ex\.\s*:?\s*$', ahead):
                    continue
                if re.search(r'(?<![A-Za-zÀ-ÿ])en\s+$', ahead):
                    continue
                new_ += [g for g in (m.group(1), m.group(2)) if g]
    if not new_:
        return 0
    already = [x.lower() for x in (e.get('latina') or [])]
    added = [x for x in new_ if x.lower() not in already]
    if not added:
        return 0
    e['latina'] = (e.get('latina') or []) + added
    return len(added)


def split_off_symbol(e):
    """Takes the chemical symbol out of the text and puts it in its field.

    Returns 1 if a symbol has been laid. Where the typist struck the label
    properly but the symbol did not decode, we go and fetch it from
    symbols.txt, surveyed by eye on the page; failing to find it there, the
    article keeps its text as it stands -- a label without a symbol says
    nothing, but erasing it would erase the trace of the lack as well.
    """
    missing_ = symbols_manual().get("%s@%d:%d" % (e.get('vedetto'),
                                              e.get('image', -1),
                                              e.get('ligno', -1)))
    S = e.get('senci') or []
    for k, t in enumerate(S):
        m = RE_SYMBOL.search(t)
        if not m:
            continue
        rest = t[m.end():]
        if m.group(1):
            # The label as an aside -- « ..., (simbolo kemiala : Ir) quan onu
            # renkontras... »: it stops at its parenthesis, and the sentence takes up
            # again after it.
            j = rest.find(')')
            sim, run_on = (rest[:j], rest[j+1:]) if j >= 0 else (rest, '')
        else:
            sim, run_on = rest, ''
        sim = sim.strip(' .,;:')
        # A contaminated text will not be cut: under « ruteno » the following
        # article merged into its own, and what follows the label is not a symbol
        # but whole lines. We do not touch it, even to lay a reading made by eye.
        if len(sim) > SYMBOL_LENGTH:
            continue
        if not sim and not missing_:
            continue
        e['simbolo'] = missing_ or sim
        S[k] = space_out((t[:m.start()] + ' ' + run_on).strip(' .,;:–-'))
        _code_not_symbol(e)
        return 1
    # The label is no longer in the text: either the typist did not strike it,
    # or an earlier pass has already taken it out. A reading made by eye is laid
    # there all the same, and corrects if need be a symbol the decoding had read
    # only by halves -- « Ca » for « Ca F² ».
    if missing_ and e.get('simbolo') != missing_:
        e['simbolo'] = missing_
        _code_not_symbol(e)
        return 1
    _code_not_symbol(e)
    return 0


_RULES = None


def rules_set_aside(file_=f"{T}/rules.txt"):
    """The surveyed rules the eye sets aside: vedetto@image:ligno -> fragments.

    The survey also takes what is not an intention -- the stroke of a
    neighbouring line, a stroke that runs from one word onto the next. The
    edition cannot always know: a full word underlined in the middle of a
    definition looks like a quoted word, and the book quotes many. This file
    only TAKES a survey away, never lays one.
    """
    global _RULES
    if _RULES is None:
        _RULES = {}
        if os.path.exists(file_):
            with open(file_, encoding='utf-8') as h:
                for l in h:
                    if l.startswith('#') or not l.strip():
                        continue
                    q = l.rstrip('\n').split('\t')
                    if len(q) < 2 or not q[0].strip() or not q[1].strip():
                        continue
                    u = q[1].strip()
                    if '{' in u or u.startswith('>'):
                        continue          # LAID: filetoj_pozita, filetoj_rendita
                    _RULES.setdefault(q[0].strip(), set()).add(u)
    return _RULES


_RENDERED = None


def rules_rendered(file_=f"{T}/rules.txt"):
    """The rules GIVEN BACK to the survey: vedetto@image:ligno -> fragments.

    The stroke was there, the survey did not see it. Given back here, it takes
    the ordinary road again: the phrase that carries its own definition opens
    its paragraph, the rest passes into italic. That is what « pseudonima »
    needed -- « Pseudonimo : Nomo ne-exakta » is a sub-entry, but no rule
    designated it, and nothing distinguished it from a sentence.

    The line begins with « > »: no survey in the book carries that sign.
    """
    global _RENDERED
    if _RENDERED is None:
        _RENDERED = {}
        if os.path.exists(file_):
            with open(file_, encoding='utf-8') as h:
                for l in h:
                    if l.startswith('#') or not l.strip():
                        continue
                    q = l.rstrip('\n').split('\t')
                    if len(q) < 2 or not q[1].strip().startswith('>'):
                        continue
                    u = q[1].strip()[1:].strip()
                    if u:
                        _RENDERED.setdefault(q[0].strip(), []).append(u)
    return _RENDERED


_PLACED = None


def rules_placed(file_=f"{T}/rules.txt"):
    """The italics laid BY EYE: vedetto@image:ligno -> (context, spans).

    The author sets in italic the word he QUOTES. When the survey of the rule
    returned nothing, the edition cannot guess it -- but the reader stumbles:
    « La omiso di ta avan qua esas anakoluto » does not read without knowing
    that « ta » and « qua » are quoted there, not used.

    The fragment then carries BRACES around what takes the italic, and the rest
    is context: « La omiso di {ta} avan {qua} esas anakoluto ». Without it,
    « qua » would be set in italic in all three places where it appears in the
    article, two of which it is an ordinary pronoun.
    """
    global _PLACED
    if _PLACED is None:
        _PLACED = {}
        if os.path.exists(file_):
            with open(file_, encoding='utf-8') as h:
                for l in h:
                    if l.startswith('#') or not l.strip():
                        continue
                    q = l.rstrip('\n').split('\t')
                    if len(q) < 2 or '{' not in q[1]:
                        continue
                    raw = q[1].strip(); with_ = ''; spans = []; beg = None
                    for c in raw:
                        if c == '{':
                            beg = len(with_)
                        elif c == '}':
                            if beg is not None: spans.append((beg, len(with_)))
                            beg = None
                        else:
                            with_ += c
                    if with_ and spans:
                        _PLACED.setdefault(q[0].strip(), []).append((with_, spans))
    return _PLACED


def _reglue(sublines, texts):
    """The rule cut by an end of line: its two halves are only one.

    The typist underlines « Kreto-krayono »; the line breaks in the middle of
    the word, and the survey returns « Kreto-kra- » then « yono ». Sought as
    they stand, neither of the two is found again in the reglued text: the
    phrase they designate was no longer recognised, and both halves ended among
    the unplaced fragments. We reglue them when the joined form is found in the
    text -- with or without the hyphen, according to what the regluing decided.

    A final hyphen does not always announce a break: « -ez- » and « auto - »
    carry one of their own. The condition is therefore the SAME as for laying
    the italic -- the joined piece must be found in the text -- and what is not
    found there stays as it stands.
    """
    out=[]; i=0
    while i < len(sublines):
        u=sublines[i]
        if u.endswith('-') and i+1 < len(sublines):
            for j in (u[:-1]+sublines[i+1], u+sublines[i+1]):
                if any(_find(j, t) for t in texts):
                    out.append(j); i+=2; break
            else:
                out.append(u); i+=1
        else:
            out.append(u); i+=1
    return out


def _rule_without_headword(spot, u, headword_):
    """The rule has lost its first word, and that word was THE HEADWORD.

    The survey returns the rules line by line. When the typist underlines a
    phrase the end of a line cuts -- « ... - II. Licenco » then « poeziala :
    su-liberigo... » -- it returns two pieces of it; and the one carrying the
    headword is set aside, because a rule equal to the headword is precisely
    that of the headword itself, which teaches nothing. The phrase therefore
    found itself reduced to its end, and was no longer recognised.

    « tribono » shows it in two neighbouring lines: « Tribono di la soldati »,
    whose rule held on one line, opens its sub-entry; « Tribono di la plebeyi »,
    its exact parallel, opened none, its rule having lost the word « Tribono ».
    The book treats the two alike.

    We require the missing word to be ONE only, and to quote the headword.
    Without that condition, the suffix alone attached « Kun radiko di verbo
    netransitiva » to « -ig- », or « Testamento » to the rule « Olda
    Testamento ». Over the whole dictionary the rule raises three phrases:
    « Licenco poeziala », « Puteo arteza », « Tribono di la plebeyi ».
    """
    pl = spot.split(); pu = u.split()
    if len(pl) != len(pu) + 1:
        return False
    clean_ = lambda w: w.lower().strip('.,;:')
    if [clean_(w) for w in pl[1:]] != [clean_(w) for w in pu]:
        return False
    return _quotes_headword(pl[0], headword_)


def structure_(e):
    """Cuts each sense into a body and, where there is cause, its sub-entries.

    « proporciono » carries four phrases in its second sense, each with its own
    definition. Pouring them into a single paragraph made them impossible to
    find; we detach them, with their qualifier of domain.
    """
    sublines=_reglue(underlinings(e), e.get('senci') or [])
    _for=rules_set_aside().get("%s@%d:%d" % (e.get('vedetto'),
                                              e.get('image', -1), e.get('ligno', -1)))
    if _for: sublines=[u for u in sublines if u not in _for]
    for u in rules_rendered().get("%s@%d:%d" % (e.get('vedetto'),
                                                e.get('image', -1),
                                                e.get('ligno', -1)), ()):
        if u not in sublines: sublines.append(u)
    e['sublineita']=sublines
    struct_=[]; n_sub=0
    for t in (e.get('senci') or []):
        found=[]
        for m in RE_PHRASE.finditer(t):
            spot=m.group(1)
            if not any(_agrees(spot, u)
                       or _rule_without_headword(spot, u, e.get('vedetto') or '')
                       for u in sublines): continue
            # See RE_LOKUCO: outside a parenthesis, a phrase that does not open
            # with a capital must be a derivative of the headword.
            if (spot[:1].islower() and not spot.startswith(('*', '+'))
                    and not _quotes_headword(spot, e.get('vedetto') or '')):
                continue
            # A single word, with no hyphen, unrelated to the headword: this is
            # not a phrase but a GLOSS -- « moloso. ... – Nun : grosa gardo-hundo »,
            # where « Nun » is the adverb « now ». The capital and the colon do not
            # suffice to distinguish it; the link with the headword does. The true
            # one-word phrases are either compounds -- « mar-baseno »,
            # « dento-krono » -- or derivatives of the headword -- « acido » under
            # « acida ».
            if (len(spot.split()) == 1 and '-' not in spot
                    and not spot.startswith(('*', '+'))
                    and not _quotes_headword(spot, e.get('vedetto') or '')):
                continue
            found.append((m.start(1), m.end(), spot, None))
        taken={x[0] for x in found}
        for m in RE_PHRASE_BRACKET.finditer(t):
            spot=m.group(1)
            if m.start(1) in taken: continue
            if not any(_agrees(spot, u) for u in sublines): continue
            # The mark is not part of the word: « *certena » quotes « certa »
            # as plainly as « certena » does, and the test must not be blinded
            # by it -- RE_SUBENTRY's own call strips it the same way.
            if not (spot[:1].isupper()
                    or _quotes_headword(spot.lstrip('*+'),
                                        e.get('vedetto') or '')): continue
            found.append((m.start(1), m.end(), spot, (m.start(), _close(t, m.start()))))
        for m in RE_SUBENTRY.finditer(t):
            spot=m.group(1)
            if m.start(1) in taken or any(x[0] == m.start(1) for x in found): continue
            if not any(_agrees(spot.lstrip('*'), u) for u in sublines): continue
            found.append((m.start(1), m.end(), spot, (m.start(), _close(t, m.start()))))
        found.sort()
        if not found:
            struct_.append({"teksto": t, "sub": []}); continue
        # A phrase in parentheses begins at its OPENING parenthesis: the sign
        # belongs to the phrase, not to the text before it.
        beg=[x[3][0] if x[3] else x[0] for x in found]
        sub=[]; run_on=[]
        for i,(a,after_,spot,kr) in enumerate(found):
            end_=beg[i+1] if i+1 < len(found) else len(t)
            if kr and kr[1] is not None and kr[1] < end_:
                # The sub-entry stops at the parenthesis that closes it. What follows
                # takes up the sentence of the sense -- « (en vehilo publika : ...) La
                # komizo di qua la rolo... » -- and therefore goes back to the body.
                run_on.append(t[kr[1]+1:end_]); end_=kr[1]
            sub.append({"loko": spot, "fako": "", "teksto": t[after_:end_].strip()})
        head=t[:beg[0]]
        # The qualifier goes with the phrase that follows, not with the sense before.
        for i in range(len(sub)):
            src = head if i == 0 else sub[i-1]["teksto"]
            m=RE_QUAL.search(src)
            if m:
                q=m.group(0).strip(" -\u2013")
                src=src[:m.start()]
                sub[i]["fako"]=q
                if i == 0: head=src
                else: sub[i-1]["teksto"]=src.rstrip(" -\u2013,;")
        # An enumeration number left alone at the head: it opens the first
        # sub-entry rather than make an empty sense.
        head=head.strip(" -\u2013;,")
        m=RE_NUMBER.match(head.strip()) if head else None
        if m and len(head.strip()) <= 3:
            sub[0]["fako"]=(head.strip()+" "+sub[0]["fako"]).strip(); head=""
        # The text that followed the parenthesis is reglued to the body of the
        # sense, the parenthesis off. We do it LAST: the leading qualifier and the
        # enumeration number are read at the end of the text that PRECEDES, and a
        # resumption glued before them would have hidden them.
        if run_on:
            head=space_out(re.sub(r'\s+', ' ',
                                (head + " " + " ".join(run_on))).strip())
        n_sub += len(sub)
        struct_.append({"teksto": head, "sub": sub})
    for b in struct_:
        b['teksto']=capital_start(b['teksto'])
        for x in b['sub']:
            x['loko']=lowercase_phrase(x['loko'])
            # The hyphen that introduced the NEXT phrase is left at the end of the
            # body of the previous one -- « ... relate Suno. – ». It no longer
            # announces anything, the phrase having taken its own paragraph.
            x['teksto']=x['teksto'].rstrip(" -–,;")
            if not x['fako']:
                mk=RE_QUAL_HEAD.match(x['teksto'])
                if mk:
                    x['fako']=mk.group(0).strip()
                    x['teksto']=x['teksto'][mk.end():].lstrip(' .,;:')
            x['teksto']=capital_start(x['teksto'])
            # The qualifier is kept BARE, like the article's `fako` field: it is the
            # editions that lay the parentheses. Without that a phrase's domain --
            # taken in parentheses in the text -- and that of an attached article --
            # taken in the field -- were not written the same way.
            x['fako']=make_uniform(x['fako'].strip().strip('()').strip())
    e['strukt']=struct_
    # What is left underlined without being a phrase: the domain, the Latin
    # name, the quoted word. The edition renders it in italic, where it is found.
    loc={x["loko"].lower() for b in struct_ for x in b["sub"]}
    # The DOMAIN's rule, for the same reason as the phrase's: it has already
    # done its work. « (elektro) » has gone to the `fako` field, which both
    # editions render in italic in their own way; the fragment has no business
    # settling on the first « elektro » to come along in the definition. It did
    # so in 31 articles -- « fonto di ELEKTRO » under akumulatoro, « la ponto di
    # NAVO » under swabro, « komandas ARMEO » under generalo -- where the word
    # is used, not quoted.
    #
    # The book carries 4,109 rules equal to a domain, and not one outside its
    # parenthesis: the typist underlines the domain where it is, never its echo.
    # The safeguard therefore has no false brother.
    dom={(e.get('fako') or '').strip().strip('()').rstrip('.').lower()}
    dom |= {(x.get('fako') or '').strip().strip('()').rstrip('.').lower()
            for b in struct_ for x in b['sub']}
    dom.discard('')
    texts=[b["teksto"] for b in struct_] + [x["teksto"] for b in struct_ for x in b["sub"]]
    run_=[]; dub=[]; vu=set()
    for u in sublines:
        if u.lower() in loc: continue
        # The truncated rule the phrase was born of: it designates the phrase
        # already, and has no business settling a second time in italic in the body.
        if any(_find(u, L) for L in loc): continue
        laid=False
        alt=other_form(u)
        # The survey is RAW, the text is typeset: the ellipsis has become the
        # single character there, and the affix that follows it has come away from
        # it. « lore...lore » (lor), « trans., por...-eso » (elektar) were no longer
        # found there, and the rule passed for unplaced. We therefore also look for
        # the typeset form of the survey.
        if not alt and ellipsis_(u) != u:
            alt=ellipsis_(u)
        # The stroke cuts short: the survey returns only the BEGINNING of the
        # qualifier -- « met » for « (metaf.) », « alud » for « (aludante homo od
        # animalo vivanta) », « aci » for « (acioni, obligacioni) ». Sought as it
        # stands, it is found nowhere, and the domain lost its italic where its
        # neighbours had theirs. Twenty cases in the book, all of them qualifiers in
        # parentheses from the same article; we require three letters, so that a
        # shorter fragment does not designate any parenthesis at all.
        if (len(u) >= 3 and u.isalpha()
                and not any(_find(u, t) for t in texts)
                and not (alt and any(_find(alt, t) for t in texts))):
            for t in texts:
                mq=re.search(r'\((%s[^()]*)\)' % re.escape(u), t, re.I)
                if mq: alt=mq.group(1); break
        for t in texts:
            m=_find(u, t); word=u
            if not m and alt:
                m=_find(alt, t); word=alt
            if not m: continue
            # The rule often covers only PART of the parenthesis: the typist
            # underlines « aludante persono » but cuts her stroke at the end of the
            # line. We set the whole parenthesis in italic -- it is the parenthesis
            # that is the qualifier -- and the two halves reglue.
            g=_bracket(t, m.start(), m.end())
            # The domain already gone to the field does not settle BARE in the body
            # again. « (elektro) » is akumulatoro's domain; the italic fell back onto
            # the « elektro » of « fonto di elektro », where the word is used, not
            # quoted. We therefore require the fragment still to be a PARENTHESIS in
            # the text: where it is -- « (bot.) » opening sense II of lotuso,
            # « (fiziol.) » that of sero, « (ica) » quoted by ca -- it keeps its
            # italic; where it no longer is, it has left it with the field.
            if g is None and word.strip().rstrip('.').lower() in dom:
                continue
            if g is None and (len(word) < 3 or _function_words_only(word)):
                dub.append(u); continue
            v=g if g else word
            if v.lower() not in vu: vu.add(v.lower()); run_.append(v)
            laid=True
        if not laid and u not in dub: dub.append(u)
    e['kursiva']=run_
    _poz=rules_placed().get("%s@%d:%d" % (e.get('vedetto'),
                                            e.get('image', -1), e.get('ligno', -1)), ())
    for b in struct_:
        b['teksto_k']=mark_(b['teksto'], run_, _poz)
        for x in b['sub']:
            x['teksto_k']=mark_(x['teksto'], run_, _poz)
    # A fragment absent from the body is not doubtful if it has found its place
    # elsewhere: domain, Latin name, phrase -- even a PART of a phrase. The rule
    # of « radiko » breaks at the end of a line and returns « Extraktar radiko,
    # quadrata » then « kubala, di nombro »: the second half is found nowhere as
    # it stands, and yet it is placed, the phrase having taken its own paragraph.
    # The underlined text carries the form the author WROTE, the field the one
    # the edition keeps: « medicino » on the page, « medic. » in the field. We
    # therefore compare but for punctuation, each half of the field and each
    # domain enumerated counting apart -- and on both sides, for the underlined
    # text can be shorter than the domain (the rule broke at the end of a line)
    # as well as longer (the edition abbreviated). In that second sense we
    # require four letters, so that a short domain -- « per », « pri » -- does
    # not cover any fragment at all.
    domains=set()
    for _f in [(e.get('fako') or '')] + [x['fako'] for b in struct_ for x in b['sub']]:
        if not _f: continue
        for _piece in _f.split(') ('):
            for _p in RE_COMPOSITION.split(_piece):
                _p=_flat(_p)
                if _p: domains.add(_p)
        _p=_flat(_f)
        if _p: domains.add(_p)
    # « prosodio » and « prozodio » do not contain each other: the table of
    # variants says so, the comparison cannot guess it.
    domains |= {_flat(v) for f in list(domains) for v in DOMAIN_VARIANTS.get(f, ())}
    # The scientific name sometimes gives TWO forms in one: « rubus caesius,
    # rubus fructicosus », « conium maculatum, e speco di cicuta ». The rule
    # covers each name apart: sought to the character, the second passed for an
    # unplaced underline. We therefore accept the PIECE, from four letters up.
    lat={x.lower() for x in (e.get('latina') or [])}
    lat_flat={_flat(x) for x in lat}
    places=[x['loko'] for b in struct_ for x in b['sub']]
    e['dubinda']=[u for u in dub
                  if not any(_flat(u) and (_flat(u) in f
                                            or (len(f) >= 4 and f in _flat(u)))
                             for f in domains)
                  and u.lower() not in lat
                  and not any(_almost_in(u.lower(), x) for x in lat)
                  and not any(len(_flat(u)) >= 4 and _almost_in(_flat(u), f)
                              for f in lat_flat)
                  and not any(_agrees(u, L) or _contains(L, u) for L in places)
                  # The chemical symbol's label has left the text for its field:
                  # the rule that covered it is placed, not doubtful.
                  # The stroke often cuts it short -- « Simbolo kem »,
                  # « Simbolo kemial » -- or takes only its end --
                  # « kemiala »: we therefore accept any piece of the label,
                  # from three letters up so as not to catch anything at all.
                  and not (e.get('simbolo') and
                           (_contains(SYMBOL_LABEL + ' ' + e['simbolo'], u)
                            or (len(u.strip()) >= 3
                                and any(u.lower().strip(' .:') in E
                                        for E in LABELS))))]
    return n_sub


# Function words: a rule that covers only those is an artefact of the survey
# of underlines, not an intention of the author.
# The function words: those a rule never designates for themselves. An
# underline that covers ONLY those is not a mark of the author's but a trace --
# the stroke of a neighbouring line, or a survey that has overrun. « absinto »
# carried « ek la » in italic in the middle of its definition.
#
# The list is CLOSED: articles, prepositions, conjunctions, pronouns and
# correlatives, plus the forms of « esar ». A full word does not enter it, even
# a short one: « Ido » under « logiko », « ohm » under « volto », « tri » under
# « tri- » are quoted words, and keep their italic.
#
# Four function words are withdrawn from it, because the book QUOTES them
# somewhere and the rule there is a true mark: « ante » under « avan »
# (« kontre ke ante relatas tempo »), « avan » and « dop » under « retro- »
# (« movo de avan ad dop »), and « que » under « enklitiko », where it is Latin
# -- « L. que en neque ».
FUNCTION_WORDS={'la','lo','de','da','di','en','per','sur','a','ad','ab','ek','ye',
           'che','apud','cirkum','dum','exter','inter','kontre',
           'malgre','preter','segun','sub','super','til','trans','ultre','vers',
           'kun','pri','pro','po','sen','por','pos',
           'qua','quan','quo','quon','qui','quin','ula','ulo','ulu','irga',
           'lu','li','ol','olu','ilu','elu','onu','me','tu','vu','ni','vi',
           'su','mea','tua','vua','nia','via','lua','sua','lia','olua',
           'ica','ita','ico','ito','ta','to','ca','co',
           'e','ed','o','od','ma','se','ke','nam','do','nek','ne',
           'kom','anke','tre','plu','min','nun','olim','hike','ibe','ja','mem',
           'nur','tro','tam','tale','quale','kande','ube','lore','tande',
           'esas','esis','esos','esus','esar','e c'}


def _function_words_only(u):
    """Does the fragment cover ONLY function words?"""
    # « e c » -- « e cetera » -- is written in two pieces the second of which is
    # not a word: we admit it whole.
    if u.strip().lower() in FUNCTION_WORDS: return True
    words=[m.strip('.,;:()«»\'’\u201c\u201d "').lower() for m in u.split()]
    words=[m for m in words if m]
    return bool(words) and all(m in FUNCTION_WORDS for m in words)


def _almost_in(u, f):
    """Is the fragment found again in f, to within ONE letter?

    The survey of the rule carries the MACHINE's reading; the `latina` field
    may have been put right by eye -- « myrmedophaga » rendered
    « myrmecophaga », which the headword « mirmekofago » proves. Sought to the
    character, the rule was no longer found, and the scientific name passed for
    an unplaced underline. One letter of difference is exactly what a
    correction of reading changes; we require four letters so that a short
    fragment does not cover anything at all.

    A LONG name can carry two -- « gamelopardalis giraffz » rendered
    « camelopardalis giraffa » under « jirafo », the c read g and the a read z.
    We therefore admit one letter per twelve: two for twenty-four characters,
    one for the short fragments, where the least further tolerance would make
    anything resemble anything.
    """
    if len(u) < 4 or len(u) > len(f):
        return False
    tolerance = 1 + len(u) // 12
    return any(sum(1 for a, b in zip(u, f[i:i+len(u)]) if a != b) <= tolerance
               for i in range(len(f) - len(u) + 1))


def _find(u, t):
    """The occurrence of the underlined fragment in the text, spacing free."""
    if not u.strip(): return None
    # Without regard to case: the author writes « (Anke metaf.) », the edition
    # lowers the initial of the domains, and the fragment surveyed on the grid
    # would no longer be found in the text.
    # The asterisk of the unofficial word is laid AFTER the survey of the rule,
    # and the typist's stroke covers it without knowing it: « pri grandoro » was
    # no longer found in « (pri *grandoro) ». We therefore let it pass between
    # the words -- before the first, the left bound admits it already. _tuti(),
    # which LAYS the italic, follows the same rule.
    mo=re.compile(r'(?<![A-Za-z\u00c0-\u00ff])'
                  + r'\s+\*?'.join(re.escape(w) for w in u.split())
                  + r'(?![A-Za-z\u00c0-\u00ff])', re.I)
    return mo.search(t)


def _bracket(t, a, b):
    """If the fragment is in a parenthesis, that whole parenthesis."""
    i=t.rfind('(', 0, a)
    if i < 0: return None
    j=t.find(')', b-1)
    if j < 0: return None
    if '(' in t[i+1:j] or ')' in t[i+1:a]: return None
    if j-i > 70: return None
    return t[i:j+1]

def reattach_subwords(ent, file_=f"{T}/subwords.txt"):
    """Attaches an article to the one the author made it depend on.

    The attachment does not DEGRADE the article: it keeps its domain, its
    language code and its page. It only changes place -- instead of opening its
    own entry, it files under the one it derives from, like the phrases. It
    stays findable by its name: the exports file the phrases among the
    searchable forms, on the same footing as a headword.
    """
    if not os.path.exists(file_): return 0
    couples=[]
    for l in open(file_,encoding='utf-8'):
        l=l.rstrip("\n")
        if not l.strip() or l.startswith('#'): continue
        a,_,b=l.partition("\t")
        couples.append((a.strip(), b.strip()))
    if not couples: return 0
    per={}
    for e in ent: per["%s@%d:%d" % (e['vedetto'], e['image'], e['ligno'])]=e
    strip_=set(); n=0
    for key_, key_p in couples:
        f=per.get(key_); m=per.get(key_p)
        if f is None or m is None:
            print("  attachment with no target: %s -> %s" % (key_, key_p)); continue
        blocks=f.get('strukt') or []
        body_=" ".join(b['teksto'] for b in blocks if b['teksto']).strip()
        body_k=" ".join(b.get('teksto_k') or b['teksto'] for b in blocks
                         if b['teksto']).strip()
        if not body_: continue
        target=(m.get('strukt') or [None])[-1]
        if target is None: continue
        target['sub'].append({"loko": f['vedetto'], "fako": f['fako'] or "",
                             "teksto": body_, "teksto_k": body_k,
                             "kodo": f.get('kodo') or "",
                             "lingui": f.get('lingui') or []})
        m['sublineita']=(m.get('sublineita') or []) + (f.get('sublineita') or [])
        strip_.add(id(f)); n+=1
    if strip_:
        ent[:]=[e for e in ent if id(e) not in strip_]
    return n


def build():
    pages,corr,rules_ = load_text()
    raw=cut_up(pages,corr,rules_)
    # Two passes: the first gives the lexicon of the headwords, the second uses
    # it to settle the hyphens fallen at an end of line.
    # The lexicon serves to settle the end-of-line hyphens: a one-letter
    # headword there would attest any fragment at all.
    lex={e['vedetto'].lower() for e in (analyse_(x) for x in raw)
         if e_ok(e) and len(e['vedetto']) >= 2}
    n0=len(raw); raw=split_at(raw, lex)
    if len(raw)>n0: print("articles separated from a shared line: %d"%(len(raw)-n0))
    ent=[analyse_(e, lex) for e in raw]
    n=apply_judgements(ent)
    if n: print("lexical judgements applied: %d occurrences"%n)
    n=typography(ent)
    if n: print("senses touched up typographically: %d"%n)
    n=correct_headwords(ent)
    if n: print("headwords corrected by hand: %d"%n)
    # The ending flag is read ON THE HEADWORD: corrected here, it must be read
    # again. « borc » become « boro », « fenikulc » become « fenikulo », the
    # impossible ending has gone -- but the flag that reported it stayed, and the
    # working list designated work already done. The order flag, for its part,
    # is recomputed at the end of the chain already, for the same reason.
    n=0
    for e in ent:
        v=e.get('vedetto') or ''
        ok=_ending_ok(e)
        if ok and 'finalo-nekustumala' in e['drapeli']:
            e['drapeli'].remove('finalo-nekustumala'); n+=1
        elif v and not ok and 'finalo-nekustumala' not in e['drapeli']:
            e['drapeli'].append('finalo-nekustumala'); n+=1
    if n: print("ending flags reread after correction: %d"%n)
    n=correct_words(ent)
    if n: print("words corrected in the definitions: %d"%n)
    import proofread as _rel
    n,r=_rel.apply_(ent)
    if n or r: print("proofreading of the definitions: %d corrections laid, %d refused"%(n,r))
    # The proofreading returns the domain as it READS on the page -- with its
    # capital, and without the full stop the typescript did not strike. The field,
    # for its part, is lower-cased and its abbreviation pointed much earlier,
    # BEFORE this correction: « (ariktekt.) » corrected to « arkitekt » therefore
    # came out bare when its thirty neighbours were pointed. We pass both
    # normalisations again behind the correction; they are idempotent.
    for e in ent:
        if e.get('fako'): e['fako']=compound(ellipsis_(make_uniform(to_lowercase(point_(e['fako'])))))
    # The proofreading lays strings surveyed before the typography: we pass the
    # spacing again behind it. espacar() is idempotent.
    for e in ent:
        S=e.get('senci') or []
        for k,t in enumerate(S):
            # Orphaned punctuation at the head of a sense: it comes from a break in the
            # original, not from the text. « titrar » began with a full stop.
            S[k]=multiplication(compound(ellipsis_(balance_brackets(point_abbrev(close_bracket(
                close_qualifier(orphan_bracket(formulas(to_digits(point_senses(
                    overload(space_out(tidy_punctuation(t)))))))))).lstrip('.,;:) ').strip()))))
    # (cifri and formuli come in here alone, once the proofreading is laid)
    # A second pass of the corrections by eye. A line of words.txt written from
    # the RENDERED text could not apply higher up: « de l til 10 litri » (bidono)
    # carries a 10 that cifri had not yet drawn from the typist's « lO », and the
    # correction never took -- in silence. The function is idempotent: a correction
    # already laid no longer finds its faulty form and does nothing.
    n=correct_words(ent)
    if n: print("words corrected after the figures were set: %d"%n)
    # A second recovery of the language code. The analysis's pass comes BEFORE
    # the typography; when the end of the line still carried a cinder -- an
    # isolated full stop under « ganso », a missing punctuation under « rodar » --
    # the code did not anchor, and the article passed for « sen-lingua » while
    # keeping its code in the text. Passed again here, it anchors.
    n=0
    for e in ent:
        if e.get('kodo') or not e.get('senci'): continue
        mk=re.search(r'(?:[-–.,()*]|\s)\s*([A-Za-z]{1,12})\s*\.?\s*$', e['senci'][-1])
        li=_read_code(mk.group(1)) if mk else None
        if not li: continue
        e['lingui']=li; e['kodo']=mk.group(1)
        q=e['senci'][-1][:mk.start()].rstrip(' -–.,;:')
        if q: e['senci'][-1]=q
        else: e['senci'].pop()
        if 'sen-lingua' in e['drapeli']: e['drapeli'].remove('sen-lingua')
        n+=1
    if n: print("language codes recovered after the typography: %d"%n)
    # The code is not always at the end of the LAST sense. The author has
    # sometimes laid it, then added a sense after the fact: « arniko. I. Planto
    # aromata... - L. arnica montana. - DEFIS. II. Medikamento liquida... ». The
    # code then stays in the middle of the article, the article passes for
    # « sen-lingua », and the reader sees « DEFIS » inside a definition. We survey
    # it there too -- on the LAST sense that carries one, and for the articles that
    # have none.
    n=0
    for e in ent:
        if e.get('kodo') or not e.get('senci'): continue
        for k in range(len(e['senci'])-1, -1, -1):
            mk=re.search(r'(?:[-–.,()*]|\s)\s*([A-Za-z]{1,12})\s*\.?\s*$', e['senci'][k])
            li=_read_code(mk.group(1)) if mk else None
            if not li: continue
            e['lingui']=li; e['kodo']=mk.group(1)
            q=e['senci'][k][:mk.start()].rstrip(' -–.,;:')
            if q: e['senci'][k]=q
            else: e['senci'].pop(k)
            if 'sen-lingua' in e['drapeli']: e['drapeli'].remove('sen-lingua')
            n+=1; break
    if n: print("language codes surveyed outside the last sense: %d"%n)
    n=order_codes(ent)
    if n: print("language codes put back into the book's order: %d"%n)
    n=star_(ent)
    if n: print("unofficial words marked where they were bare: %d"%n)
    # An article begun at the foot of a page, abandoned, then BEGUN AGAIN at the
    # head of the next. « ampère » is the book's only case: the first version
    # stops short, with no language code; the second is complete. The reading
    # edition keeps only the latter -- the facsimile keeps both, since it renders
    # the page as it was struck.
    last_={}; first={}
    for e in ent:
        if e['ligno'] >= last_.get(e['image'], (-1,))[0]: last_[e['image']]=(e['ligno'], e)
        if e['ligno'] <= first.get(e['image'], (10**6,))[0]: first[e['image']]=(e['ligno'], e)
    false_=set()
    for pg,(_, a) in last_.items():
        b = first.get(pg+1, (None,None))[1]
        if b is not None and a['vedetto'] == b['vedetto'] and not a['kodo'] and b['kodo']:
            false_.add(id(a))
    if false_:
        ent=[e for e in ent if id(e) not in false_]
        print("false starts at the foot of a page set aside: %d"%len(false_))
    n0=len(ent); ent=[e for e in ent if e_ok(e)]
    if len(ent)<n0: print("renvois d'errata ecartes : %d"%(n0-len(ent)))
    # A definition cut short at the foot of a page: the scan trimmed the last
    # line. Four articles end so on a function word, with no language code, and
    # their continuation is on no page. We do not invent it -- we say so.
    RE_TOOL=re.compile(r"(?<![A-Za-zÀ-ÿ])(?:di|de|la|ye|ad|en|kun|per|sur|qua|quan"
                        r"|quon|pri|po|od|ek|da|kom|ma|nek|sen)$")
    last_={}
    for e in ent: 
        if e['ligno'] >= last_.get(e['image'], (-1,None))[0]: last_[e['image']]=(e['ligno'], e)
    for _,e in last_.values():
        t=" ".join(e['senci']).rstrip()
        if t and not e['kodo'] and RE_TOOL.search(t):
            e['drapeli'].append('tranchita-che-pagino-fino')
    # Numbering of the senses. The reading edition numbers them itself, 1, 2, 3:
    # keeping « I. », « II. » in the text would be redundant, and the original is
    # irregular -- « iambo » mixes two levels, « tribono » mixes Roman and Arabic
    # figures. We therefore take off the leading number.
    # Three senses contain ONLY their domain label, with no definition
    # (« (metriko antiqua) »): it attaches to the next sense, which it qualifies,
    # rather than stay alone.
    # The comma sometimes replaces the full stop after the number -- « I, (olim). ».
    # It is admitted ONLY AFTER a Roman figure followed by a capital or a
    # parenthesis: « l, OOO, OOO » (biliono) and « 10 , od oktiliono » (noniliono)
    # are numbers, not numbers of senses.
    # « 1.000 » is not a numbered sense but the number one thousand: without this
    # guard, « mil » lost its « 1. » and defined itself by « 000 ».
    # The number without its full stop -- « III veziketo » -- is taken off too, or
    # it would open the sense the cut has just isolated.
    RE_NUM=re.compile(r'^(?:(?:I{1,3}|IV|VI{0,3}|IX|X|[l\d]\d?)[.)](?!\d)\s*'
                      r'|(?:I{1,3}|IV|VI{0,3}|IX|X),\s*(?=[A-ZÀ-Ý(])'
                      r'|(?:I{1,3}|IV|VI{0,3}|IX|X)\s+(?=[A-Za-zÀ-ÿ])'
                      # The number followed by the qualifier's parenthesis --
                      # « I (zool.) Mamifero... » under « leono », six articles.
                      # The space is optional there: « reklamacar.I(netrans.) ».
                      r'|(?:I{1,3}|IV|VI{0,3}|IX|X)\s*(?=\())')
    RE_LABEL=re.compile(r'^\([^()]{1,40}\)\.?$')
    n_num=0
    for e in ent:
        S=[]
        for t in e.get('senci') or []:
            # NESTED numbering: « III. 1. Deklarar... ». A single removal takes off
            # the upper level alone. We loop, bounded at three rounds.
            u=t
            for _ in range(3):
                w=RE_NUM.sub('', u).strip()
                if w == u: break
                u = w
            if u != t: n_num += 1
            # « I » or « II » alone, with no definition: an orphaned number the cutting
            # took for a sense. It says nothing.
            if re.fullmatch(r'(?:I{1,3}|IV|VI{0,3}|IX|X)', u): u=''
            # A doubled full stop after the number -- « titrar. I..(teknol.) ». The
            # removal of the number leaves the second, orphaned at the head of the sense.
            # The hyphen separated the senses in the original -- « vunduro. II. -
            # (religio kristana). Marko... ». The number off, it is left at the head and
            # no longer announces anything. It also kept the editions from recognising
            # the leading parenthesis as a domain, and « stigmato » lost the italic of
            # « (religio kristana) ».
            u = re.sub(r'^[.,;:)\s–-]+', '', u)
            u = space_out(u)
            S.append(u)
        fus=[]
        for i,t in enumerate(S):
            if RE_LABEL.match(t) and i+1 < len(S):
                S[i+1] = t.rstrip('.') + ' ' + S[i+1]
                continue
            if t: fus.append(t)
        e['senci']=fus
    if n_num: print("sense numbers removed: %d"%n_num)
    # The author's underlines, surveyed on the grid: they give the phrases --
    # sub-entries in their own right -- and what goes into italic.
    n_caps=0
    for e in ent:
        S=e.get('senci') or []
        for k,t in enumerate(S):
            u=capital_start(t)
            if u != t: S[k]=u; n_caps += 1
    if n_caps: print("senses given back their initial capital: %d"%n_caps)
    n_lat=sum(latins_inline(e) for e in ent)
    n_sym=sum(split_off_symbol(e) for e in ent)
    if n_sym: print("chemical symbols moved into the domain: %d"%n_sym)
    n_sub=sum(structure_(e) for e in ent)
    n_run=sum(1 for e in ent if e.get('kursiva'))
    print("phrases detached: %d ; articles with an underline: %d"%(n_sub, n_run))
    for e in ent: e.pop('filetoj', None)
    n_rat=reattach_subwords(ent)
    if n_rat: print("articles attached as sub-entries: %d"%n_rat)
    order_flags(ent)
    return ent

# ---------------------------------------------------------------------------
# The layer of lexical judgements.
#
# The corrections returned by the judgement used to be written into the JSONL.
# But edition.py rebuilds it from the facsimile: the next rebuild erased them
# all, without a sound. We therefore apply them AT THE END OF THE CHAIN, from
# the answer files, as rules.pkl and starts.pkl are for the facsimile. A
# correction laid once is thus acquired.
JUDGEMENTS = [(f"{T}/judge/records.json",  f"{T}/judge/answers"),
             (f"{T}/senses/records.json",   f"{T}/senses/answers")]

def to_digits(t):
    """Figures read as letters: « lOO » for « 100 », « 2O » for 20.

    The machine had no 1 key and no 0 key distinct from the « l » and the
    « O » -- common usage among the typists of the period. But one cannot
    convert blindly: in « Al2O3 », « Fe2 O3 », « C6 H10 O5 », the O is OXYGEN,
    and in « De punto fixa O » it is the name of a point. We therefore convert
    only in a context without ambiguity: a token beginning with « l », a figure
    followed by « O » or « l » with no space, and a run of at least three « O »
    -- which no formula carries.
    """
    def _token(m):
        return m.group(0).replace('l', '1').replace('O', '0')
    t = re.sub(r'(?<![A-Za-zÀ-ÿ0-9])l[lO0-9]+(?![A-Za-zÀ-ÿ])', _token, t)
    t = re.sub(r'(?<=\d)[lO](?![A-Za-zÀ-ÿ0-9])', _token, t)
    t = re.sub(r'O{3,}', lambda m: '0' * len(m.group(0)), t)
    # An isolated enumeration number: « ... indikar : l. objekto plu proxima ».
    # The « l » there stands for 1. We require the colon that opens the list.
    t = re.sub(r'(?<=[:;]\s)l(?=[.)]\s)', '1', t)
    # « (l) » opens an enumeration in parentheses: it is the figure 1.
    t = re.sub(r'\(l\)', '(1)', t)
    # The degree: the machine had not the sign and struck an « o ».
    t = re.sub(r'(?<=\d)o(?=\s*(?:C\b|Celsius))', '\u00b0', t)
    # « lOOOmetri »: the typist welded the number to its unit. We require three
    # figures and three lower-case letters, which spares the formulae -- « C6H4 »
    # has only one letter, and it is a capital.
    t = re.sub(r'(?<![A-Za-zÀ-ÿ])(\d{3,})(?=[a-zà-ÿ]{3,})', r'\1 ', t)
    return t


_SUB = str.maketrans('0123456789', '\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089')
# Algebra announces itself by its statement, not by its signs: « M' = aluminio »
# under aluno is a legend, not an equation.
_SUP = str.maketrans('0123456789', '\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079')
_ALGEBRA = re.compile(r'\bequaciono\b|\bkoeficient|\bgrado\b.{0,20}\bduesma\b'
                       r'|\brelato\b|\bkubo\b|kalorizala')
_FORMULA = re.compile(r'(?<![A-Za-zÀ-ÿ])((?:[A-Z][a-z]?\d*[\s.]{0,2}){2,})(?![a-zà-ÿ])')


def formulas(t):
    """Subscripts of the chemical formulae: « H2 O » becomes « H\u2082O ».

    The machine did not lower the figures: it struck them on the line, and
    often separated the symbols by a space for legibility. We render the
    subscript and reglue. Two safeguards: at least two symbols and one figure
    are needed -- failing which « DEFIRS » or « I. La » would pass for a
    formula -- and an initial « La » followed by a space is the Ido article,
    not lanthanum: « La C5 H4 N4 O2 quan kontenas... ».
    """
    def _un(m):
        c = m.group(1)
        if not re.search(r'\d', c) or len(re.findall(r'[A-Z]', c)) < 2:
            return c
        head = ''
        ml = re.match(r'La\s+(?=[A-Z])', c)
        if ml:
            head = ml.group(0); c = c[ml.end():]
            if len(re.findall(r'[A-Z]', c)) < 2 or not re.search(r'\d', c):
                return m.group(1)
        q = c[len(c.rstrip()):]; c = c.rstrip()
        c = re.sub(r'(?<=[A-Za-z0-9])\s+(?=[A-Z])', '', c)
        c = re.sub(r'(?<=[A-Za-z])(\d+)', lambda x: x.group(1).translate(_SUB), c)
        return head + c + q
    t = _FORMULA.sub(_un, t)
    # Cases the main pattern does not take, for want of two neighbouring symbols:
    # the figure that follows a parenthesis -- « (CH\u2083)2 », « (OH)3 » -- the
    # one that follows a lead symbol -- « M'2 » -- and the isolated symbol
    # preceded by a coefficient -- « 24 H2 ». We spare algebra, where the figure is
    # an EXPONENT and not a subscript: « ax2 + bx + c = 0 » under diskriminanto,
    # « Ax2 + 2 Bxy » under koniko. Both are recognised by their statement.
    if _ALGEBRA.search(t):
        # In algebra the figure is an EXPONENT: « ax2 + bx + c = 0 » reads ax\u00b2.
        # The same for a unit raised to a power, « metro3 ».
        return re.sub(r'(?<=[A-Za-z])([23])(?![\d.,])',
                      lambda m: m.group(1).translate(_SUP), t)
    t = re.sub(r'\((\[A-Z][a-z]?)(\d+)\)',
               lambda m: '(' + m.group(1) + m.group(2).translate(_SUB) + ')', t)
    t = re.sub(r'\(([A-Z][a-z]?)(\d+)\)',
               lambda m: '(' + m.group(1) + m.group(2).translate(_SUB) + ')', t)
    t = re.sub(r'(?<=\))(\d+)', lambda m: m.group(1).translate(_SUB), t)
    t = re.sub(r"(?<=')(\d+)", lambda m: m.group(1).translate(_SUB), t)
    t = re.sub(r'(?<=\s)([A-Z][a-z]?)(\d+)(?!\d)',
               lambda m: m.group(1) + m.group(2).translate(_SUB), t)
    return t


_OVER = {'a': '\u00e2', 'e': '\u00ea', 'i': '\u00ee', 'o': '\u00f4', 'u': '\u00fb',
        'A': '\u00c2', 'E': '\u00ca', 'I': '\u00ce', 'O': '\u00d4', 'U': '\u00db'}


def overload(t):
    """The facsimile notes the overstrike as \\sur{signo}{litero} -- the typist
    struck the accent OVER the vowel, for want of an accented key. That markup
    has no business in the reading edition, where the accented letter exists:
    « \\sur{\\textasciicircum{}}{a} » reads « \u00e2 »."""
    def _un(m):
        return _OVER.get(m.group(1), m.group(1))
    return re.sub(r'\\sur\{\\textasciicircum\{\}\}\{([A-Za-z])\}', _un, t)


def orphan_bracket(t):
    """Removes the orphaned closing parenthesis at the end of a definition.

    The original counts thirty: the opening one was lost in the typing, or else
    consumed by the extraction of the domain. Closing what was never opened
    brings nothing. We touch ONLY the last, and only if the count of the others
    is balanced -- otherwise we do not know where the fault would be.
    """
    if not t.endswith(')'):
        return t
    p = 0
    for c in t[:-1]:
        if c == '(':
            p += 1
        elif c == ')':
            p = max(0, p - 1)
    return _cut(t[:-1]) if p == 0 else t


def close_qualifier(t):
    """Closes the leading qualifier whose parenthesis was left open.

    « transmisar. ... II. (biol. Igar pasar a la decendanti. » -- the closing
    mark is missing after the abbreviation, and the book writes « (biol.) »
    hundreds of times: its place is in no doubt.

    This rule must pass BEFORE fermi_parentezon, which would close at the END
    of the sense: « (biol. Igar pasar a la decendanti) », where the domain
    swallows the whole definition. It is the same sign, laid in two places, and
    only one is right.
    """
    m = RE_QUAL_MISSING.match(t)
    if m and t.count('(') > t.count(')'):
        rest = t[m.end():]
        if rest[:1] and not rest[:1].isspace():
            rest = ' ' + rest
        return '(%s)%s' % (m.group(1), rest)
    return t


def close_bracket(t):
    """Closes the parenthesis left open at the end of a definition.

    The exact counterpart of orfa_parentezo. The closing mark was lost in the
    typing and the sense ends in the middle of an aside -- « ... (anke metaf »,
    « ... (aludante penso, cienco, e c. », « ... (Ex. : la fragmento obskura ».
    The book counts sixty-five. Left open, the parenthesis hangs in both
    editions, and the rule that recognises the leading domain goes astray in it.

    We close ONLY if the last opening mark has no closing mark after it and if
    everything before it is balanced. Elsewhere -- under « arachar », where it
    is the FIRST parenthesis that was left open -- we do not know where the
    fault would be, and closing at the end would move the aside instead of
    repairing it.
    """
    i = t.rfind('(')
    if i < 0 or t.rfind(')') > i:
        return t
    av = t[:i]
    if av.count('(') != av.count(')'):
        return t
    return t.rstrip() + ')'


# « (anke metaf) »: the abbreviation's full stop was lost with the closing
# parenthesis, at the end of a line. The book writes « (anke metaf.) » fifty
# times against eighteen without the stop -- the form is not in doubt.
RE_ABBREV = re.compile(r'\((anke\s+metaf)\)', re.I)


def point_abbrev(t):
    """Gives back its full stop to the abbreviation the line break cut short."""
    return RE_ABBREV.sub(lambda m: '(%s.)' % m.group(1), t)


# A leading qualifier whose closing mark was lost: « (trans. Kustumigar
# animalo... », « (anat. Saliajo mi-sferatra... ». The book closes that one
# hundreds of times; its place is in no doubt, just after the abbreviation.
#
# The space may have fallen with it: « (bot.Frukto kapsula... » under
# « folikulo ». A CAPITAL stuck to the abbreviation's full stop opens the
# definition; it does not continue the abbreviated word. Without that the
# parenthesis closed at the end of the sense, and the domain swallowed the
# whole definition.
RE_QUAL_MISSING = re.compile(r'^\(([A-Za-zÀ-ÿ][A-Za-zà-ÿ]{1,11}\.)(?=\s|[A-ZÀ-Ý])')


def balance_brackets(t):
    """Removes the orphaned parentheses, for want of knowing where their mate
    would be.

    The typescript leaves fifty-five: « Gumo ek arboro) di India »,
    « Deprenar (per violento, koakto, de ulu to quon lu retenas. » The
    facsimile will not render them -- the original has none either. A decision
    must therefore be made, and the rule is the one orfa_parentezo already laid
    for the closing mark at the end: WE REMOVE THE ORPHANED SIGN. Removing it
    manufactures no grouping the author did not make; inventing one would.

    Two exceptions, where the mate's place is in no doubt:

      * the leading qualifier -- « (trans. » closes after the abbreviation;
      * the phrase in parentheses -- « (arko inflexita : ... » under
        « inflexar », which the truncated page never closed. It opens a
        sub-entry; taking its parenthesis off would make it disappear. We then
        leave the sense as it stands, unbalanced but whole.
    """
    m = RE_QUAL_MISSING.match(t)
    if m and t.count('(') > t.count(')'):
        t = '(%s)%s' % (m.group(1), t[m.end():])
    stack = []
    orphans = set()
    for i, c in enumerate(t):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                orphans.add(i)
    if any(RE_PHRASE_BRACKET.match(t, i) for i in stack):
        return t
    orphans.update(stack)
    if not orphans:
        return t
    return _cut("".join(c for i, c in enumerate(t) if i not in orphans))


def tidy_punctuation(t):
    """The cinders of typing: a doubled comma, a doubled full stop, a comma-stop.

    The typist sometimes struck twice. Eleven articles carry a doubled full
    stop -- « ...e tonizala. . – DEFIS » under « arniko », « (trans. .) » under
    « reklamacar » -- four a doubled comma, one a comma followed by a full
    stop. The facsimile keeps them; the reading edition does not.

    The doubled full stop is removed only when SEPARATED by a space. Stuck
    together, « ie.. » and « venenifanta.. » are two contrary cases -- a
    shortened ellipsis and one stop too many -- that nothing distinguishes
    mechanically: they are dealt with one by one in words.txt. And the author's
    ellipsis, « ... », stays intact.
    """
    t = re.sub(r',\s*,', ',', t)
    t = re.sub(r',\s*\.(?!\.)', ', ', t)
    # The full stop parted from its comma: « fuzebla ye 201° C. , kontenata en la
    # kortico » under salicino -- the stop is the abbreviation's, the comma the
    # sentence's, and the space between them is nobody's.
    t = re.sub(r'\.\s+,', '.,', t)
    # The space BEFORE the comma: « rimo nekompleta , quan » under « asonancar »,
    # « la religiani , ekleziani » under « sinagogo ». It is nobody's either. We
    # require a letter in front and a letter behind: under « *puntuar », « la
    # signi ,; . : ? ! » enumerates the signs themselves, and the comma there is
    # the first of the list, not a sentence's punctuation.
    t = re.sub(r'(?<=[A-Za-zÀ-ÿ)])[\s\u00a0]+,(?=[\s\u00a0]+[A-Za-zÀ-ÿ])', ',', t)
    t = re.sub(r'(?<!\.)\.\s+\.(?!\.)', '.', t)
    return re.sub(r'  +', ' ', t)


# The affixes the book gives as HEADWORDS, plus those SUFIXI carries for the
# filing. SUFIXI alone does not suffice here: built to take ONE suffix off a
# stem, it does not know « -im- », the suffix of the fraction, which is
# precisely that of « 1/10.000.000-ima ». The ONE-letter affixes -- « -e »,
# « -i » -- are not in it: they merge with the function words.
AFFIXES_WITH_ENDING = tuple(sorted(
    set(SUFFIXES) | {'ab', 'ant', 'at', 'esm', 'im', 'int', 'ont', 'op', 'opl',
                   'ot', 'un'}, key=len, reverse=True))

RE_AFFIX_SPACE = re.compile(
    r'(?<=[A-Za-z0-9\u00e0-\u00ff])-[\s\u00a0]+((?:%s)(?:o|a|e|i|ar|ir|or))'
    r'(?![A-Za-z\u00e0-\u00ff])' % '|'.join(AFFIXES_WITH_ENDING))


def space_out(t):
    """Spacing of the punctuation, French-Canadian usage.

    Isolated so as to be replayable: the proofreading layer lays strings
    surveyed BEFORE the typography, and laying them back as they stood ate the
    non-breaking spaces -- « familio«labiacei» ». We therefore pass again here
    behind it. The function is idempotent.
    """
    t = re.sub(r',(?=[A-Za-zÀ-ÿ])', ', ', t)
    # The « L. » that announces the scientific name takes its space: the book
    # writes it so everywhere, and once only without -- « la tipo esas L.acarus »
    # under akaro. We touch no other full stop stuck to a lower-case letter: there
    # are eight in the book, and each calls for its own reading -- « ex.en » wants
    # the space, « viburnum.tinus » wants to lose its stop.
    t = re.sub(r'(?<![A-Za-zÀ-ÿ])L\.(?=[a-zà-ÿ])', 'L. ', t)
    # The affix's hyphen does not come away from its affix: « 1/10.000.000- ima »
    # under « metro » is « 1/10.000.000-ima », the ten-millionth part. It is the
    # same stray space the headword knows -- « - as. » for « -as », « bo - . » for
    # « bo- » -- laid this time in the body.
    # We require a SUFFIX followed by its ending: failing which « radio- o
    # televizionorecevili » (megafono), where the hyphen hangs before the
    # conjunction, reglued into « radio-o ». The book's four other isolated hyphens
    # -- « ekirar- per », « perforuro- e », « implikas- kontre »,
    # « establisita- ube » -- are no more hyphens of affixes than that one.
    t = RE_AFFIX_SPACE.sub(r'-\1', t)
    # The closing parenthesis stuck to the next word takes a space -- but not the
    # one that is PART of the word. The author notes the optional element that way:
    # « leon(in)o » says the lion and the lioness, « formac(es)o » the formation
    # and the act of forming, « -(ant)ajo » the compound suffix. The word goes on
    # after the parenthesis, and the space would cut it in two. We recognise it by
    # the affix hyphen before it, or by the SINGLE letter that follows -- the
    # word's ending. Three cases in the book, and no false brother: « F(z) esas
    # monodroma » carries its space already, « (aludante persono)Definuro » is not
    # an element but an aside.
    def _close_space(m):
        draw_, inside, sequel = m.group(1), m.group(2), m.group(3)
        short_of = len(inside) <= 6 and inside.isalpha()
        if short_of and (draw_ or len(sequel) == 1):
            return m.group(0)
        return '%s(%s) ' % (draw_, inside)
    t = re.sub(r'(-?)\(([^()]*)\)(?=([A-Za-zÀ-ÿ]+))', _close_space, t)
    # « (olim).Vaporo-mashino »: the full stop that follows the closing
    # parenthesis sticks to the next word. 88 cases. We touch it only after a
    # parenthesis: elsewhere, « CH3CO.CH3 » is a chemical formula.
    t = re.sub(r'\)\.(?=[A-ZÀ-Ý])', '). ', t)
    # The same stuck full stop, this time behind the closing QUOTATION MARK:
    # « ... kom nomo "prolonguro".On plulongigas » under prolongar. Three cases in
    # the book, and all three want the space -- « "kancero".DEFIRS » under
    # karcinomo, « "paria".En India » under paria. The last two managed without it,
    # the language code and the headword detaching by themselves; the first kept
    # the next sentence welded to the one before. No false brother: a closing
    # quotation mark is never part of the word that follows.
    t = re.sub(r'([»"])\.(?=[A-ZÀ-Ý])', r'\1. ', t)
    # The asterisk of the unofficial word takes the space that separates it from
    # the PRECEDING word. The typist stuck her cross to the word she marks -- that
    # is intended, « +stencilo » is one word -- but she stuck it also, six times,
    # to the one before: « per perforo, sur+stencilo » under hektografar, « di
    # omna+itemi » under *seancar, « la+chevaliere » under barono,
    # « la+asiejo-mashini » under traino, « adolecanti,+konvokata » under klaso,
    # « en vazo+kluza » under koko. The book carries 189 asterisks already detached
    # and 50 at the head of a fragment; these six are the only welded ones, and the
    # mark there belongs to the word that FOLLOWS.
    t = re.sub(r'(?<=[A-Za-zÀ-ÿ,])\*(?=[a-zà-ÿ])', ' *', t)
    # A stray space AGAINST the parenthesis: « ( fig.) » for « (fig.) »,
    # « hundo-herbo )» for « hundo-herbo) ». The typist spaced to set her
    # line. 15 opening and 33 closing.
    # « Igar(ulo) »: the word stuck to the opening parenthesis. But not all detach
    # -- « il(u) », « dea(la) », « a(ta) » note an optional ending that is part of
    # the word, and « F(z) » is a function. We therefore separate only when the
    # content counts three letters or more, or carries something other than
    # letters: it is then a complement or a domain, not an ending.
    t = re.sub(r'(?<=[A-Za-zÀ-ÿ])\((?=([^()]*)\))',
               lambda m: ' (' if (len(m.group(1)) >= 3
                                  or not m.group(1).isalpha()) else '(', t)
    # Punctuation stuck to an opening parenthesis: « Patrino homa.(Equivalanto
    # sentimentala... » under matro. 30 cases. We spare the formulae: under
    # stearino, « CH3.(CH2)16 » is a carbon chain, and a space there would be
    # wrong. The distinctive sign of a formula is the figure that ends the
    # preceding symbol.
    def _pt(m):
        ahead = t[:m.start()]
        if re.search(r'[A-Z][A-Za-z]?[0-9\u2080-\u2089]+$', ahead):
            return m.group(0)
        return m.group(1) + ' ('
    t = re.sub(r'([.,;:!?])\(', _pt, t)
    t = re.sub(r'\(\s+', '(', t)
    t = re.sub(r'\s+\)', ')', t)
    # An orphaned full stop after the closing parenthesis -- « (aludante la
    # hari...) . Di qua la koloro... ». Justified, it opens a gap in the line.
    t = re.sub(r'\)\s+\.(?=\s|$)', ')', t)
    # A superfluous full stop after the leading parenthesis -- « (komerco).
    # Inter-egalesi ». The parenthesis closes the qualifier already; the stop is
    # redundant.
    t = re.sub(r'^(\([^()]{1,120}\))\s*\.+(?=\s|$)', r'\1', t)
    # Two qualifiers in a row -- « (netrans.) (aludante vari). » under
    # transitar: the stop falls after the SECOND, and the rule above saw only
    # the first.
    t = re.sub(r'^((?:\([^()]{1,80}\)\s*){2,})\.+(?=\s|$)', r'\1', t)
    # A superfluous colon after the leading qualifier -- « (bruiso) : Poke
    # sonora ». The parenthesis suffices; the colon would announce a list.
    t = re.sub(r'^(\([^()]{1,60}\))[\s\u00a0]*:[\s\u00a0]*', r'\1 ', t)
    # « e c » abbreviates « e cetere »: it takes the full stop. 325 occurrences
    # lost it, 455 had it already.
    t = re.sub(r'(?<![A-Za-zÀ-ÿ])e c(?![A-Za-zÀ-ÿ.])', 'e c.', t)
    # Spacing of the double punctuation marks, FRENCH-CANADIAN usage:
    # the semicolon, the exclamation mark and the question mark take NO
    # space before them -- that is the difference from the usage of
    # France, which puts a thin space there. The colon does take one,
    # and it is non-breaking so that it does not go off alone at the
    # head of a line. The same within the guillemets. We first reglue
    # the colon to the word after it, or the non-breaking-space rule
    # would leave it stuck.
    t = re.sub(r':(?=[A-Za-zÀ-ÿ])', ': ', t)
    t = re.sub(r';(?=[A-Za-zÀ-ÿ])', '; ', t)
    t = re.sub(r'[\s\u00a0]*([;!?])', r'\1', t)
    t = re.sub(r'[\s\u00a0]*:', '\u00a0:', t)
    # The guillemet stuck to the neighbouring word from OUTSIDE:
    # « familio«labiacei» ». The next rule deals with the inside; this one
    # with the outside.
    t = re.sub(r'(?<=[A-Za-zÀ-ÿ.,;:])(?=«)', ' ', t)
    t = re.sub(r'(?<=»)(?=[A-Za-zÀ-ÿ])', ' ', t)
    t = re.sub(r'«[\s\u00a0]*', '«\u00a0', t)
    t = re.sub(r'[\s\u00a0]*»', '\u00a0»', t)
    # The number of a sense stuck to its first word -- « I.Tereno »,
    # « II.Alveolo ». We touch only the Roman figures: a full stop followed
    # by a capital is elsewhere a legitimate abbreviation.
    t = re.sub(r'(?<![A-Za-zÀ-ÿ])(I{1,3}|IV|VI{0,3}|IX|XI{0,2})\.'
    r'(?=[A-Za-zÀ-ÿ])', r'\1. ', t)
    # A line of noise at the end of a definition: the typist struck out a
    # whole line with quotation marks and hyphens. What has neither letter
    # nor figure says nothing.
    # _kupar rather than a bare rstrip: the final ellipsis that marks the
    # governed complement -- « ...kom valida ke... » -- must survive the trimming
    # of the noise.
    # The tail of noise must not swallow an ellipsis followed by its closing:
    # « multa-... » counts six signs all members of the class, and went there
    # entirely. We spare it explicitly.
    t = re.sub(r'(?:[\s"\u00ab\u00bb\u2019\'.,;:_+*=/|\-\u2013\u2014]{6,})$',
               lambda m: m.group(0) if re.fullmatch(
                   r'[\s\u00a0-]*\.{2,}[\s\u00a0]*[\u00bb"\')\]]*', m.group(0)) else '', t)
    t = _cut(t)
    return t


# The ellipsis. The machine had not the single character: the author strikes
# three dots, sometimes four. 96 occurrences.
#
# When an ending or a suffix follows the dots, it detaches from them by a space
# and takes the affix hyphen. That is the form the book writes itself under
# « min » -- « ne tam multe ...-a » -- and under « quadri- » -- « Qua havas
# quar...-i »; elsewhere the hyphen, the space, or both have fallen:
# « quik...onta », « esar...ata », « t. e. ...is...inta ».
#
# A WORD that follows is not an affix and takes only the space: « lasas
# ...efikar », « preferar...kam », « lore...lore », « ...esante prezenta ». We
# therefore rely on the CLOSED list of endings, and on the hyphen the author
# struck himself -- « por...-eso » -- never on a resemblance of shape:
# « esante » divides into « es- » plus « -ante » without being for all that a
# suffix followed by an ending.
#
# The ONE-letter endings -- « -o », « -a », « -e », « -i » -- are not in it:
# they are also the commonest function words of the book. « Esar prezenta ye...
# e regardar » (asistar), « domeno qua dependas de... e, konseque » (-i-) carry
# the conjunction, not the ending. Where the author wants the one-letter
# ending, he struck the hyphen himself: « ...-a » under « min », « ...-i »
# under « quadri- ».
GRAMMATICAL_ENDINGS = tuple(sorted(
    ('anta', 'inta', 'onta', 'ante', 'inte', 'onte', 'anto', 'into', 'onto',
     'ata', 'ita', 'ota', 'ate', 'ite', 'ote', 'ato', 'ito', 'oto',
     'ant', 'int', 'ont', 'ar', 'ir', 'or', 'as', 'is', 'os', 'us', 'ez'),
    key=len, reverse=True))

RE_ELLIPSIS = re.compile(
    r'\u2026[\s\u00a0]*(?:-\s*([A-Za-z\u00e0-\u00ff]+)|(%s))(?![a-z\u00e0-\u00ff])'
    % '|'.join(GRAMMATICAL_ENDINGS))


# The compounds the book writes now with the hyphen, now welded. It lays the
# hyphen on ALL its other compounds -- « banko-komerco », « natur-historio »,
# « politiko-yuro », « milit-arto », « skerm-arto » -- and on the great
# majority of the uses of these; we align the welded forms that remain outside
# the `fako` field, where the table of domains sees to it already.
COMPOUND = (('yurocienco', 'yuro-cienco'),
             ('imprimarto', 'imprim-arto'))

RE_COMPOUND = tuple(
    (re.compile(r'(?<![-A-Za-z\u00e0-\u00ff])%s(?![A-Za-z\u00e0-\u00ff])' % a), b)
    for a, b in COMPOUND)


def multiplication(t):
    """The machine's « x » given back to the sign of multiplication.

    The machine had no cross: the typist strikes the letter. Twice in the book,
    and twice before a NUMBER -- « ... x 1000 » under « kilo- », « oktiliono x
    1.000.000 » under « noniliono ». That is the condition: the three other
    isolated « x » are unknowns, and none is followed by a figure -- « inter x,
    y, z » under « konexo », « 2 D x + 2 Ey » under « koniko », « y = sin. x »
    under « sinusoido ».

    Laid AFTER cifri(), which gives the typist's « lOOO » its figures back.
    """
    return re.sub(r'(?<![A-Za-z\u00e0-\u00ff0-9])x(?=[\s\u00a0]+\d)', '\u00d7', t)


def compound(t):
    """The welded compound given back the book's hyphen."""
    for r, b in RE_COMPOUND:
        t = r.sub(b, t)
    return t


def ellipsis_(t):
    """Three or four dots rendered by the single character, and the affix that
    follows them detached by a space and pointed with a hyphen."""
    t = re.sub(r'\.{3,}', '\u2026', t)
    t = RE_ELLIPSIS.sub(lambda m: '\u2026 -%s' % (m.group(1) or m.group(2)), t)
    # The ordinary word that follows takes only the space.
    t = re.sub(r'\u2026(?=[A-Za-z\u00c0-\u00ff])', '\u2026 ', t)
    return t


# The ending under which a word lets itself be quoted: nominal, adjectival,
# adverbial or verbal ending, or participle.
RE_ENDING_QUOTED = (r'(?:oj|o|a|e|i|ar|ir|or|as|is|os|us|ez'
                    r'|ant[aeio]|int[aeio]|ont[aeio]'
                    r'|at[aeio]|it[aeio]|ot[aeio])')


def star_(ent):
    """The mark of the unofficial word, carried EVERYWHERE the word is quoted.

    The book declares its unofficial words in their alphabetical place -- the
    headword carries the asterisk -- and marks them too when it quotes them in a
    definition. But not always: « werar » is marked fifty times and bare six,
    « publico » five times and bare once, « grandoro » four times and bare six.
    The reader saw the same word now reported, now not.

    We align on the mark, and only for the words where the author has laid it
    himself at least once: where he has never laid it -- « pondar », « niuzo »,
    « golfo », « tarda », « intrenar » -- adding it would be a new assertion,
    not a tidying. Fourteen words, 45 uses.

    The word's own article is left as it stands: its headword carries the mark
    already, and doubling it in its own definition teaches nothing.
    """
    roots_={}
    for e in ent:
        v=e.get('vedetto') or ''
        if not v.startswith('*'): continue
        r=re.sub(r'(ar|ir|or|o|a|e|i)$', '', v[1:])
        if len(r)>=3: roots_[r]=v
    n=0
    for r,v in sorted(roots_.items()):
        marker=re.compile(r'\*(%s%s)(?![A-Za-zà-ÿ-])' % (re.escape(r), RE_ENDING_QUOTED))
        if not any(marker.search(s) for e in ent for s in (e.get('senci') or [])):
            continue
        bare_=re.compile(r'(?<![*A-Za-zà-ÿ-])(%s%s)(?![A-Za-zà-ÿ-])'
                        % (re.escape(r), RE_ENDING_QUOTED))
        for e in ent:
            if (e.get('vedetto') or '')==v: continue
            S=e.get('senci') or []
            for k,t in enumerate(S):
                u=bare_.sub(r'*\1', t)
                if u!=t: S[k]=u; n+=u.count('*')-t.count('*')
    return n


def typography(ent):
    """Typography of the reading edition.

    The facsimile keeps the hyphens as the machine struck them -- it had but
    one key. The reading edition can render them. Three rules, measured before
    being laid so as not to spill onto the 4,240 internal hyphens, which do
    belong to the words:

      « elektro- -grandori »  -> « elektro-grandori »   (1 case)
      « -- » or a doubled « - » -> em dash              (20 cases)
      « mot - mot »           -> en dash                (829 cases)
    """
    n=0
    # The HEADWORD's guillemets take their space, as everywhere else in the
    # book. « "brokoli"-kaulo » is the only case where they stay IN the string:
    # the Ido word is quoted there only in part, and the `citita` flag, which
    # has the editions lay « \u00ab\u00a0amen\u00a0\u00bb », cannot carry it.
    for e in ent:
        v=e.get('vedetto') or ''
        if '\u00ab' in v or '\u00bb' in v:
            u=re.sub(r'\u00ab[\s\u00a0]*', '\u00ab\u00a0',
                     re.sub(r'[\s\u00a0]*\u00bb', '\u00a0\u00bb', v))
            if u!=v: e['vedetto']=u; n+=1
    for e in ent:
        s=e.get('senci') or []
        for k,t in enumerate(s):
            o=t
            # The separating hyphen stuck to the domain's parenthesis:
            # « granda. -(cinemo) » under « skreno », « direte.- (metaf.) » under
            # « intuicar ». The book writes it with both its spaces eighty-five
            # times; thirteen times one of the two is missing. An AFFIX's
            # parenthesis is not one -- « = -(at)ajo », « equivalas -(ant)ajo »:
            # there the word goes on after the closing mark, and the hyphen belongs
            # to it.
            t=re.sub(r'\s*-\s*(\([^()]*\))(?![A-Za-zà-ÿ])', r' - \1', t)
            t=re.sub(r'(\w)- -(\w)', r'\1-\2', t)          # a doubled stroke from a break
            t=re.sub(r'(?<![-\w])(?:- -|--)(?![-\w])', '—', t)
            t=re.sub(r'(?<=\S) - (?=\S)', ' – ', t)
            # The typescript's « + » marks the unofficial words; Ido tradition
            # writes an asterisk. 214 occurrences.
            # An unofficial word is an Ido word, hence in lower case: « +H₂O », in
            # the formula for morphine, is chemistry's plus and not the author's
            # mark.
            #
            # The mark is STUCK to the word it marks -- the typist left no space:
            # « pri+grandoro », « sur+stencilo », « vazo+kluza », « o+sesiono ». The
            # book does give « *grandoro », « *stencilo », « *kluza », « *sesiono »
            # as unofficial headwords.
            t=re.sub(r'\+(?=[a-zà-ÿ])', '*', t)
            # Detached from the word, it is so only if it OPENS the fragment or
            # follows an opening parenthesis: « legi (+ leyi) » under « cienco ».
            # Between two terms it is algebra's plus, which the preceding rule took
            # for the mark: « ax² + bx + c = 0 » under « diskriminanto », « a + b i e
            # a' + b' i » under « konjugar », « a² = b² + c » under « pitagorala » --
            # four asterisks laid on unknowns.
            t=re.sub(r'(?:^|(?<=[(\[«“"]))\+\s+(?=[a-zà-ÿ])', '*', t)
            # Arithmetic's plus takes both its spaces, as the book gives them to it
            # everywhere else -- « Ax² + 2 Bxy + Cy² » under « koniko », « a² = b² + c »
            # under « pitagorala ». One place alone loses them: « Sis plus un (6 +1, o
            # 4 +3) » under « sep ».
            t=re.sub(r'(?<=\d)[\s\u00a0]*\+[\s\u00a0]*(?=\d)', ' + ', t)
            # Quotation marks: the machine had only the straight double apostrophe.
            # We convert only the PAIRS -- 834 out of 1,690 apostrophes; the orphaned
            # ones stay straight rather than open a guillemet that would never close.
            t=re.sub(r'"([^"]{1,120})"', r'«\1»', t)
            # Missing spaces after punctuation: the typist tightened to hold the line.
            # 258 commas and 136 closing parentheses.
            # cifri() and formuli() are NOT here: they are transformations of rendering,
            # and the proofreading layer looks for strings surveyed on the raw text.
            # « H2 Hg3 Si4 O12 » is no longer found once the subscripts are laid; we
            # therefore lay them AFTER it.
            t=point_senses(overload(space_out(tidy_punctuation(t))))
            if t!=o: s[k]=t; n+=1
    return n

def correct_headwords(ent, file_=f"{T}/headwords.txt"):
    """Corrections to headwords, surveyed by eye.

    The layer of judgements touches the definitions alone: a headword is an
    article, not an occurrence, and correcting it by rule has already gone
    wrong. It is therefore corrected by hand, one line per case, with the
    reason written alongside. The facsimile keeps the original's spelling.
    """
    if not os.path.exists(file_): return 0
    corr={}
    for l in open(file_,encoding='utf-8'):
        l=l.rstrip("\n")
        if not l.strip() or l.startswith("#"): continue
        p=l.split("\t")
        if len(p)>=2 and p[0].strip() and p[1].strip(): corr[p[0].strip()]=p[1].strip()
    n=0
    for e in ent:
        v=e.get('vedetto')
        # A precise target: « tri@600:23 » touches only the article of page 600
        # line 23. The book carries TWO « tri » -- the figure 3 and the prefix --
        # and only the second takes the hyphen.
        c = corr.get("%s@%d:%d" % (v, e['image'], e['ligno']))
        if c is None: c = corr.get(v)
        if c is not None: e['vedetto']=c; n+=1
    return n

def correct_words(ent, file_=f"{T}/words.txt"):
    """Corrections to words in the definitions, surveyed by eye.

    The counterpart of headwords.txt for the body of the articles. Two automatic
    passes have already been rejected here -- frequency gave « papuli » for
    « populi », the root « falko » for « talko » -- because a dictionary of ten
    thousand roots is not the whole lexicon of the language. We therefore write
    the cases out one by one, with their reason.
    """
    if not os.path.exists(file_): return 0
    corr={}
    for l in open(file_,encoding='utf-8'):
        l=l.rstrip("\n")
        if not l.strip() or l.startswith("#"): continue
        p=l.split("\t")
        if len(p)>=2 and p[0].strip() and p[1].strip(): corr[p[0].strip()]=p[1].strip()
    if not corr: return 0
    # A correction can bear on SEVERAL words -- « en decen danto » for
    # « en decendanto », « ii aDom » for « di mikra »: the machine broke or welded
    # where it should not, and the faulty word has no boundary of its own. We
    # therefore accept a run of words on the left as on the right.
    mo=re.compile(r"(?<![A-Za-zÀ-ÿ-])(%s)(?![A-Za-zÀ-ÿ-])"
                  % "|".join(re.escape(k).replace(r"\ ", r"\s+")
                             for k in sorted(corr, key=len, reverse=True)))
    n=0
    for e in ent:
        s=e.get('senci') or []
        for k,t in enumerate(s):
            nt,c = mo.subn(lambda m: corr[re.sub(r"\s+"," ",m.group(1))], t)
            if c: s[k]=nt; n+=c
    return n

def apply_judgements(ent):
    import glob
    total=0
    for fic, rep in JUDGEMENTS:
        if not os.path.exists(fic): continue
        records={x['id']:x for x in json.load(open(fic))}
        for f in sorted(glob.glob(f"{rep}/*.txt")):
            for l in open(f,encoding='utf-8'):
                i,_,v = l.rstrip("\n").partition("\t")
                if not v.strip() or not i.strip().isdigit(): continue
                x=records.get(int(i))
                if x is None: continue
                word, good = x['mot'], v.strip()
                # Two patterns, tried in order. The first reglues a hyphenation --
                # « pro-duktita » -> « produktita ». It must not be the only one:
                # « uaze » corrected to « quaze » is not a hyphenation but a fallen
                # letter, and the hyphenation pattern looked for « q-uaze » there
                # without finding anything, in silence.
                patterns=[]
                if good.lower().endswith(word.lower()) and len(good)>len(word):
                    head=good[:len(good)-len(word)]
                    patterns.append(re.compile(r'\b'+re.escape(head)+r'[-\s]+'+re.escape(word)+r'\b', re.I))
                patterns.append(re.compile(r'\b'+re.escape(word)+r'\b', re.I))
                for mo in patterns:
                    laid=0
                    for e in ent:
                        s=e.get('senci') or []
                        for k,t in enumerate(s):
                            nt,n=mo.subn(good, t)
                            if n: s[k]=nt; laid+=n
                    total+=laid
                    if laid: break
    return total

if __name__=="__main__":
    ent=build()
    os.makedirs(f"{T}/editions", exist_ok=True)
    with open(f"{T}/editions/dicionario.jsonl","w",encoding='utf-8') as f:
        for e in ent:
            f.write(json.dumps({k:v for k,v in e.items() if k!='lineoj'}, ensure_ascii=False)+"\n")
    print(f"{len(ent)} records")
    c=collections.Counter(d for e in ent for d in e['drapeli'])
    print("flags:", c.most_common())
    print("with no flag at all:", sum(1 for e in ent if not e['drapeli']))
    print("with fako:", sum(1 for e in ent if e['fako']),
          "| with a Latin name:", sum(1 for e in ent if e['latina']),
          "| with several senses:", sum(1 for e in ent if len(e['senci'])>1))

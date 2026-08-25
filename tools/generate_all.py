# -*- coding: utf-8 -*-
"""Generates the 639 pages of the facsimile, including what is not typing.

Three kinds of page escape the grid and are dealt with apart: the cover,
which is a lithograph; the six blank pages; and the pages that carry an
ornament -- the author's autograph signature on the copyright page, the
letter of the alphabet in a large size at the head of each section. The
ornament is cut out of the scan and laid back in its place, measured as a
fraction of the sheet, without taking up room in the grid.
"""
import numpy as np, sys, os, json
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from decode import load_
from generate import write_
T=_ROOT + "/work"; ROOT=_ROOT
WIDTH=210.0; TOP=297.0; ORIGX=21.9; ORIGY=12.44
MARGIN={'signaturo':10}          # margin of the cutting, in pixels of the scan

def not_typed():
    d={}
    p=f"{T}/pages_non_dactylo.txt"
    if os.path.exists(p):
        for l in open(p,encoding='utf-8'):
            if l.startswith('#') or not l.strip(): continue
            a,b=l.rstrip('\n').split('\t'); d[int(a)]=b
    return d

def ornaments():
    """Ornaments by page — a LIST per page, and not a single ornament.

    The dictionary {page: ornament} lost the second ornament of a page that
    carries two. Page 631 carries exactly two: the « X » at the head, and the
    « Y » in the middle, section Y not opening on a fresh sheet. The « Y »
    disappeared there without a sound.
    """
    p=f"{T}/ornements.json"
    if not os.path.exists(p): return {}
    d={}
    for e in json.load(open(p)): d.setdefault(e['pagino'], []).append(e)
    return d

HSTEP_MM=2.540; VSTEP_MM=4.321      # the machine's pitch, in millimetres

def _latex_ornament(e):
    """The ornament's position in GRID coordinates, not as a fraction of the sheet.

    First version: the position was expressed as a fraction of the scanned
    sheet. It fell wide -- the framing of the scan varies from one page to the
    next, whereas the grid does not vary. We therefore convert the ornament's
    box into columns and lines of its page's grid, then lay it back at the
    machine's pitch. It is the same invariant as the text, hence the same
    registration.
    """
    m=MARGIN.get(e['litero'], 6)
    pg=e['pagino']
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    scale=float(z['shape'][0])/e['H']
    vstep=float(z['pasv']); hstep=float(z['pash'])
    xg=float(z['xg']); col0=int(z['col0']); lg=z['lignes']
    y0=float(lg[0][1])
    col=((e['x']-m)*scale - xg)/hstep - col0
    ln=(((e['y']+e['h']+m)*scale) - y0)/vstep
    wid=((e['w']+2*m)*scale)/hstep
    return ("\\marge[%.3fmm]{%.3fmm}{\\ornamento{%.3fmm}{%s}}"
            % (col*HSTEP_MM, ln*VSTEP_MM, wid*HSTEP_MM, e['dosiero']))

def run_step():
    lab,M=load_(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    nd=not_typed(); orn=ornaments()
    n=int(M[:,0].max())+1; done_=[]
    for pg in range(n):
        path_=f"{ROOT}/content/p{pg:03d}.tex"
        if pg in nd:
            body=("\\pgimago{ornaments/couverture/couverture.pdf}"
                   if nd[pg]=='kovrilo' else "\\pgvakua")
            note = "couverture, lithographie" if nd[pg]=='kovrilo' else "page blanche"
            open(path_,"w",encoding='utf-8').write(
                "%% page %d du fac-simile (image p-%03d) — %s, pas de frappe\n%s\n"
                % (pg+1, pg, note, body))
            done_.append(pg); continue
        if not os.path.exists(f"{T}/cellules/p-{pg:03d}.npz"): continue
        try: write_(pg,lab,M,tab)
        except Exception as e:
            print("ECHEC p%03d : %s"%(pg,e), flush=True); continue
        if pg in orn:
            L=open(path_,encoding='utf-8').read().split("\n")
            # All the page's ornaments, laid on the first line: their place is
            # given in grid coordinates by \marge, so each falls where it must,
            # whatever the line that receives it.
            head="".join(_latex_ornament(e) for e in orn[pg])
            for i,l in enumerate(L):
                if l.startswith("\\l{"):
                    L[i]="\\l{"+head+l[3:]
                    break
            else:
                for i,l in enumerate(L):
                    if l=="\\pg{":
                        L.insert(i+1,"\\l{"+head+"}"); break
            open(path_,"w",encoding='utf-8').write("\n".join(L))
        done_.append(pg)
        if pg%100==0: print("  ...p%03d"%pg, flush=True)
    # Endpaper. The book ends on « F I N O », at page 639 -- an odd number,
    # and with no endpaper. One more blank page brings it to 640, that is,
    # forty gatherings of sixteen: what is needed to bind it. The endpaper at
    # the head already exists in the book (the blank pages of the scan).
    open(f"{ROOT}/content/garde.tex","w",encoding='utf-8').write(
        "%% feuillet de garde final : porte le livre a 640 pages, quarante cahiers de seize\n\\pgvakua\n")
    with open(f"{ROOT}/content/toutes.tex","w",encoding='utf-8') as f:
        for pg in done_: f.write("\\input{content/p%03d}\n"%pg)
        f.write("\\input{content/garde}\n")
    print("pages written:", len(done_), "| not typewritten:", len(nd),
          "| ornees :", len([p for p in orn if p in done_]))

if __name__=="__main__": run_step()

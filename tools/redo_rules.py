# -*- coding: utf-8 -*-
"""Recomputes the underline rules without re-cutting the pages.

We replay exactly the sequence of extraire() as far as soulignements() --
analyser(), raffiner_pas(), soulignements() -- then shift the columns by the
col0 already stored. With no change of rule, the result must be identical to
what is in the npz: that is the non-regression check.
"""
import numpy as np, sys, pickle, os, re
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
import cells as C
T=_ROOT + "/work"; ROOT=_ROOT

def rules(pg, **kw):
    """A page's rules, on the geometry ALREADY STORED.

    We are careful not to recompute the lattice's pitch and phase.
    raffiner_pas() does not return exactly the same origin from one run to
    the next, and a cell is kept only if the rule covers 60 % of it: at the
    left edge of a headword, the rule falls exactly on that threshold. An xg
    differing by half a pixel therefore took the first cell from 0 to 1 --
    and generate.py, which refuses a rule beginning in the middle of a word,
    then threw away the headword's whole underline. Eight headwords in a row
    went that way on page 155.

    Only the rectified image comes from analyser(); the lines, the pitch and
    the origin come from the npz, as at the first cutting.
    """
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    d = C.analyse(f"{ROOT}/scan/p-{pg:03d}.jpg")
    r=d['norm']
    vstep=float(z['pasv']); hstep=float(z['pash']); xg=float(z['xg']); c0=int(z['col0'])
    ncol=int(np.floor((r.shape[1]-xg)/hstep))
    underline = C.underlines(r, z['lignes'], vstep, hstep, xg, ncol, **kw)
    return {k:(yy,[(a-c0,b-c0) for a,b in pl],t) for k,(yy,pl,t) in underline.items()}

if __name__=="__main__":
    for pg in (25,33):
        neuf=rules(pg)
        z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
        anc=pickle.loads(z['sou'].item())
        ka=set(k for k,v in anc.items() if v[1]); kn=set(k for k,v in neuf.items() if v[1])
        egal=all(sorted(anc[k][1])==sorted(neuf[k][1]) for k in ka|kn if k in anc and k in neuf)
        print("p%03d : lines with a rule old=%d new=%d  identical=%s"%(pg,len(ka),len(kn),egal and ka==kn))

def all_(out_path=f"{T}/filets.pkl", start_=0, end_=None):
    """Recomputes the rules of every page and deposits them apart.

    We do not write into the corpus of cells: it weighs 295 MB and one error
    of format has already cost 144 pages. The file produced here is a layer of
    correction, read by generate.py after the survey by eye and before the
    original detection.
    """
    import glob
    pages=sorted(int(re.search(r'p-(\d+)',f).group(1))
                 for f in glob.glob(f"{T}/cellules/p-*.npz"))
    pages=[p for p in pages if p>=start_ and (end_ is None or p<end_)]
    out={}
    for i,pg in enumerate(pages):
        try:
            out[pg]=rules(pg)
        except Exception as e:
            print("ECHEC p%03d : %s"%(pg,e), flush=True); continue
        if i%25==0: print("  %d/%d (p%03d)"%(i,len(pages),pg), flush=True)
    with open(out_path,"wb") as f: pickle.dump(out,f)
    print("written %s : %d pages"%(out_path,len(out)))
    return out

"""Consolidating the headwords' initials by the book's alphabetical order.

The dictionary is alphabetical: on a given page, the headwords nearly all
begin with the same letter. And it is precisely there that the decoding goes
wrong most (20 % of faults on the first three columns, against 2 % elsewhere),
because the initial carries an underline that is often doubled.

We therefore survey, page by page, the majority letter of the headwords'
initials, and impose it on the cells that contradict it. This is not a
correction of the typescript: it is the lifting of an ambiguity of reading by
a structural property of the book. Every intervention is logged.
"""
import numpy as np, pickle, collections, sys
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"

def marge(occ, mini=3):
    """The page's margin column: the first that serves on several lines.

    Column 0 was supposed to be the margin. It is not always: forty-five
    pages begin further right -- page 380 begins at 5 -- and none of their
    entries was then recognised as a headword. They disappeared entirely from
    the structured edition.
    """
    n=occ.sum(axis=0)
    for c in range(occ.shape[1]):
        if n[c] >= mini: return c
    return 0

def vedettes(pg):
    """Headword lines: the page's margin inked and a rule beginning there."""
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    occ=z['occ']; lg=z['lignes']; sou=pickle.loads(z['sou'].item())
    c0=marge(occ)
    out=[]
    for i,k in enumerate(lg[:,0]):
        k=int(k)
        if not occ[i,c0]: continue
        r=sou.get(k)
        if not r: continue
        plages=r[1]
        if any(a<=c0<=b for a,b in plages): out.append((k,i))
    return out

def consolider(lab, M, tab, pages=None, seuil=0.6, mini=3):
    """Returns (new table, log). The table is not modified in place."""
    import glob, os
    if pages is None:
        pages=[int(os.path.basename(p)[2:5]) for p in sorted(glob.glob(f"{T}/cellules/*.npz"))]
    tab=np.array(tab, dtype=object).copy()
    journal=[]
    par_groupe=collections.defaultdict(collections.Counter)
    for pg in pages:
        ved=vedettes(pg)
        if len(ved)<mini: continue
        sel=np.where(M[:,0]==pg)[0]
        pos={(int(k),int(c)):i for i,(p,k,c) in zip(sel,M[sel])}
        lettres=[]
        for k,i in ved:
            j=pos.get((k,0))
            if j is None: continue
            lettres.append((k,j,tab[lab[j]]))
        if not lettres: continue
        c=collections.Counter(x[2] for x in lettres)
        (maj,n),=c.most_common(1)
        if n/len(lettres) < seuil: continue
        for k,j,ch in lettres:
            if ch!=maj:
                par_groupe[int(lab[j])][maj]+=1
                journal.append((pg,k,ch,maj))
    for g,c in par_groupe.items():
        (maj,n),=c.most_common(1)
        if n>=2:
            tab[g]=maj
    return tab, journal

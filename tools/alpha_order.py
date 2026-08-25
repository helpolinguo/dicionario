"""Correcting the headwords by the book's alphabetical order.

The headwords follow one another in alphabetical order. A headword that
breaks that order is a misreading: we try to restore it by replacing its
ambiguous cells with their neighbours in the group. This is not a correction
of the typescript, it is the use of a verifiable property of the book.
Everything is logged.
"""
import numpy as np, pickle, itertools, sys, collections
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from consolidate import headwords
T=_ROOT + "/work"

def collecter(lab, M, tab, smudge, exc):
    """The book's run of headwords: (page, line, [(col, char, index)])."""
    out=[]
    pages=sorted(set(M[:,0].tolist()))
    par_page={}
    order_=np.argsort(M[:,0],kind='stable')
    bounds=np.searchsorted(M[order_,0], np.arange(M[:,0].max()+2))
    for pg in pages:
        idx=order_[bounds[pg]:bounds[pg+1]]
        pos={(int(M[i,1]),int(M[i,2])):int(i) for i in idx}
        for k,_ in headwords(pg):
            mo=[]; c=0
            while True:
                i=pos.get((k,c))
                if i is None or smudge[i]: break
                ch=exc.get((pg,k,c), str(tab[lab[i]]))
                if not (ch.isalpha() and len(ch)==1): break
                mo.append((c,ch,i)); c+=1
            if len(mo)>=3: out.append((pg,k,mo))
    return out

def corriger(lab, M, tab, smudge, exc, alt, maxpos=3):
    hw=collecter(lab,M,tab,smudge,exc)
    formes=["".join(ch for _,ch,_ in m).lower() for _,_,m in hw]
    log_=[]; fresh={}
    for n in range(1,len(hw)-1):
        before_, after_ = formes[n-1], formes[n+1]
        if before_ <= formes[n] <= after_: continue
        pg,k,mo = hw[n]
        pos=[j for j,(_,_,i) in enumerate(mo) if alt[lab[i]]]
        if not pos or len(pos)>maxpos: continue
        best=None
        for combi in itertools.product(*[[mo[j][1]]+alt[lab[mo[j][2]]] for j in pos]):
            l=list(formes[n])
            for a,j in zip(combi,pos): l[j]=a.lower()
            v="".join(l)
            if before_ <= v <= after_:
                d=sum(1 for a,j in zip(combi,pos) if a!=mo[j][1])
                if best is None or d<best[0]: best=(d,combi,v)
        if best is None: continue
        d,combi,v = best
        for a,j in zip(combi,pos):
            if a!=mo[j][1]:
                col,anc,i=mo[j]
                fresh[(pg,k,col)]=a
                log_.append((pg,k,col,anc,a,formes[n],v,before_,after_))
    return fresh, log_

if __name__=="__main__":
    from decode import smudges
    from generate import exceptions
    lab=np.load(f"{T}/km_lab.npy"); M=np.load(f"{T}/meta_all.npy")
    tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    alt=pickle.load(open(f"{T}/cls_alternatives.pkl","rb"))
    exc=dict(exceptions())
    fresh,log_=corriger(lab,M,tab,smudges(),exc,alt)
    print(len(log_),"headword cells corrected by alphabetical order")
    with open(f"{T}/journal_ordre_alpha.txt","w",encoding='utf-8') as f:
        f.write("page\tligne\tcol\tlu\tcorrige\tvedette lue\tvedette retenue\tprecedente\tsuivante\n")
        for j in log_: f.write("\t".join(map(str,j))+"\n")
    import os
    lines=[]
    p=f"{T}/exceptions.txt"
    for l in open(p,encoding='utf-8'):
        l=l.rstrip("\n")
        if l.startswith("#") or not l.strip(): lines.append(l); continue
        a,b,c,dd=l.split("\t")
        if (int(a),int(b),int(c)) not in fresh: lines.append(l)
    with open(p,"w",encoding='utf-8') as f:
        f.write("\n".join(lines)+"\n")
        for (pg,k,c),v in sorted(fresh.items()): f.write(f"{pg}\t{k}\t{c}\t{v}\n")
    print("exceptions.txt mis a jour")

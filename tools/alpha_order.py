"""Correcting the headwords by the book's alphabetical order.

The headwords follow one another in alphabetical order. A headword that
breaks that order is a misreading: we try to restore it by replacing its
ambiguous cells with their neighbours in the group. This is not a correction
of the typescript, it is the use of a verifiable property of the book.
Everything is logged.
"""
import numpy as np, pickle, itertools, sys, collections
sys.path.insert(0,'/root/dicionario/outils')
from consolidate import vedettes
T="/root/dicionario/travail"

def collecter(lab, M, tab, bav, exc):
    """The book's run of headwords: (page, line, [(col, char, index)])."""
    out=[]
    pages=sorted(set(M[:,0].tolist()))
    par_page={}
    ordre=np.argsort(M[:,0],kind='stable')
    bornes=np.searchsorted(M[ordre,0], np.arange(M[:,0].max()+2))
    for pg in pages:
        idx=ordre[bornes[pg]:bornes[pg+1]]
        pos={(int(M[i,1]),int(M[i,2])):int(i) for i in idx}
        for k,_ in vedettes(pg):
            mo=[]; c=0
            while True:
                i=pos.get((k,c))
                if i is None or bav[i]: break
                ch=exc.get((pg,k,c), str(tab[lab[i]]))
                if not (ch.isalpha() and len(ch)==1): break
                mo.append((c,ch,i)); c+=1
            if len(mo)>=3: out.append((pg,k,mo))
    return out

def corriger(lab, M, tab, bav, exc, alt, maxpos=3):
    ved=collecter(lab,M,tab,bav,exc)
    formes=["".join(ch for _,ch,_ in m).lower() for _,_,m in ved]
    journal=[]; nouv={}
    for n in range(1,len(ved)-1):
        avant, apres = formes[n-1], formes[n+1]
        if avant <= formes[n] <= apres: continue
        pg,k,mo = ved[n]
        pos=[j for j,(_,_,i) in enumerate(mo) if alt[lab[i]]]
        if not pos or len(pos)>maxpos: continue
        best=None
        for combi in itertools.product(*[[mo[j][1]]+alt[lab[mo[j][2]]] for j in pos]):
            l=list(formes[n])
            for a,j in zip(combi,pos): l[j]=a.lower()
            v="".join(l)
            if avant <= v <= apres:
                d=sum(1 for a,j in zip(combi,pos) if a!=mo[j][1])
                if best is None or d<best[0]: best=(d,combi,v)
        if best is None: continue
        d,combi,v = best
        for a,j in zip(combi,pos):
            if a!=mo[j][1]:
                col,anc,i=mo[j]
                nouv[(pg,k,col)]=a
                journal.append((pg,k,col,anc,a,formes[n],v,avant,apres))
    return nouv, journal

if __name__=="__main__":
    from decode import bavures
    from generate import exceptions
    lab=np.load(f"{T}/km_lab.npy"); M=np.load(f"{T}/meta_all.npy")
    tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    alt=pickle.load(open(f"{T}/cls_alternatives.pkl","rb"))
    exc=dict(exceptions())
    nouv,journal=corriger(lab,M,tab,bavures(),exc,alt)
    print(len(journal),"cellules de vedette corrigees par l'ordre alphabetique")
    with open(f"{T}/journal_ordre_alpha.txt","w",encoding='utf-8') as f:
        f.write("page\tligne\tcol\tlu\tcorrige\tvedette lue\tvedette retenue\tprecedente\tsuivante\n")
        for j in journal: f.write("\t".join(map(str,j))+"\n")
    import os
    lignes=[]
    p=f"{T}/exceptions.txt"
    for l in open(p,encoding='utf-8'):
        l=l.rstrip("\n")
        if l.startswith("#") or not l.strip(): lignes.append(l); continue
        a,b,c,dd=l.split("\t")
        if (int(a),int(b),int(c)) not in nouv: lignes.append(l)
    with open(p,"w",encoding='utf-8') as f:
        f.write("\n".join(lignes)+"\n")
        for (pg,k,c),v in sorted(nouv.items()): f.write(f"{pg}\t{k}\t{c}\t{v}\n")
    print("exceptions.txt mis a jour")

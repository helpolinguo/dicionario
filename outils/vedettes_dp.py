"""Correction des vedettes par l'ordre alphabetique — formulation globale.

Ma premiere tentative corrigeait de proche en proche : quand une vedette rompait
l'ordre, elle la forcait a se conformer a ses voisines. C'est faux, parce que la
faute peut etre dans la voisine, et cela produisait des monstres.

La bonne formulation est globale. Chaque vedette a un jeu de lectures possibles
(l'originale, plus celles qu'on obtient en remplacant ses cellules ambigues par
leurs voisines de groupe), chacune avec un cout egal au nombre de cellules
changees. On cherche la suite de lectures qui **minimise le cout total** sous la
contrainte d'ordre alphabetique croissant — par programmation dynamique.

La contrainte est souple : une rupture d'ordre coute PENALITE mais reste
possible. Une vedette reellement mal classee dans le tapuscrit survit donc, si
aucune lecture voisine ne rattrape l'ordre a moindre frais.
"""
import numpy as np, pickle, itertools, sys, collections
sys.path.insert(0,'/root/dicionario/outils')
from consolider import vedettes
T="/root/dicionario/travail"
PENALITE = 4.0        # cout d'une rupture d'ordre conservee
MAXPOS   = 4          # cellules ambigues considerees par vedette
MAXCAND  = 48

def collecter(lab, M, tab, bav, exc):
    out=[]
    ordre=np.argsort(M[:,0],kind='stable')
    bornes=np.searchsorted(M[ordre,0], np.arange(M[:,0].max()+2))
    for pg in range(M[:,0].max()+1):
        idx=ordre[bornes[pg]:bornes[pg+1]]
        if not len(idx): continue
        pos={(int(M[i,1]),int(M[i,2])):int(i) for i in idx}
        for k,_ in vedettes(pg):
            mo=[]; c=0
            while True:
                i=pos.get((k,c))
                if i is None or bav[i]: break
                ch=exc.get((pg,k,c), str(tab[lab[i]]))
                if len(ch)!=1 or not ch.isalpha(): break
                mo.append((c,ch,i)); c+=1
            if len(mo)>=3: out.append((pg,k,mo))
    return out

def candidats(mo, lab, alt):
    f="".join(ch for _,ch,_ in mo)
    pos=[j for j,(_,_,i) in enumerate(mo) if alt[lab[i]]][:MAXPOS]
    if not pos: return [(f, (), 0.0)]
    choix=[[mo[j][1]]+list(alt[lab[mo[j][2]]]) for j in pos]
    out=[]
    for combi in itertools.product(*choix):
        l=list(f); d=0
        for a,j in zip(combi,pos):
            if a!=l[j]: l[j]=a; d+=1
        out.append(("".join(l), tuple(zip(pos,combi)), float(d)))
        if len(out)>=MAXCAND: break
    out.sort(key=lambda x:x[2])
    return out

def resoudre(lab, M, tab, bav, exc, alt):
    ved=collecter(lab,M,tab,bav,exc)
    C=[candidats(mo,lab,alt) for _,_,mo in ved]
    n=len(ved)
    INF=1e18
    cout=[np.array([c[2] for c in C[0]], float)]
    prec=[None]
    for i in range(1,n):
        ci=C[i]; cp=C[i-1]
        cles_p=[c[0].lower() for c in cp]; cles_i=[c[0].lower() for c in ci]
        prev=cout[-1]
        best=np.full(len(ci), INF); arg=np.zeros(len(ci), int)
        for b,kb in enumerate(cles_i):
            v=prev + np.array([0.0 if ka<=kb else PENALITE for ka in cles_p])
            j=int(np.argmin(v)); best[b]=v[j]+ci[b][2]; arg[b]=j
        cout.append(best); prec.append(arg)
    # retour arriere
    j=int(np.argmin(cout[-1])); chemin=[j]
    for i in range(n-1,0,-1):
        j=int(prec[i][j]); chemin.append(j)
    chemin.reverse()
    nouv={}; journal=[]
    for i,(pg,k,mo) in enumerate(ved):
        f,subs,d = C[i][chemin[i]]
        if d==0: continue
        orig="".join(ch for _,ch,_ in mo)
        for j,a in subs:
            if a!=mo[j][1]:
                col,anc,_=mo[j]
                nouv[(pg,k,col)]=a
                journal.append((pg,k,col,anc,a,orig,f))
    return nouv, journal, ved, C, chemin

if __name__=="__main__":
    from decoder import bavures
    from generer import exceptions
    lab=np.load(f"{T}/km_lab.npy"); M=np.load(f"{T}/meta_all.npy")
    tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    alt=pickle.load(open(f"{T}/cls_alternatives.pkl","rb"))
    exc=dict(exceptions())
    nouv,journal,ved,C,ch=resoudre(lab,M,tab,bavures(),exc,alt)
    print(len(ved),"vedettes ;",len(journal),"cellules corrigees")
    with open(f"{T}/journal_vedettes.txt","w",encoding='utf-8') as f:
        f.write("page\tligne\tcol\tlu\tcorrige\tvedette lue\tvedette retenue\n")
        for j in journal: f.write("\t".join(map(str,j))+"\n")
    import os
    p=f"{T}/exceptions.txt"; lignes=[]
    for l in open(p,encoding='utf-8'):
        l=l.rstrip("\n")
        if l.startswith("#") or not l.strip(): lignes.append(l); continue
        a,b,c,dd=l.split("\t")
        if (int(a),int(b),int(c)) not in nouv: lignes.append(l)
    with open(p,"w",encoding='utf-8') as f:
        f.write("\n".join(lignes)+"\n")
        for (pg,k,c),v in sorted(nouv.items()): f.write(f"{pg}\t{k}\t{c}\t{v}\n")

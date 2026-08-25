"""Correcting the headwords by alphabetical order -- the global formulation.

My first attempt corrected step by step: when a headword broke the order, it
forced it to conform to its neighbours. That is wrong, because the fault may
be in the neighbour, and it produced monsters.

The right formulation is global. Each headword has a set of possible readings
(the original, plus those obtained by replacing its ambiguous cells with their
neighbours in the group), each with a cost equal to the number of cells
changed. We look for the run of readings that **minimises the total cost**
under the constraint of increasing alphabetical order -- by dynamic
programming.

The constraint is soft: a break in the order costs PENALITE but stays
possible. A headword genuinely misfiled in the typescript therefore survives,
if no neighbouring reading recovers the order more cheaply.
"""
import numpy as np, pickle, itertools, sys, collections
sys.path.insert(0,'/root/dicionario/outils')
from consolidate import headwords
T="/root/dicionario/travail"
PENALITE = 4.0        # cost of a break in the order that is kept
MAXPOS   = 4          # ambiguous cells considered per headword
MAXCAND  = 48

def collecter(lab, M, tab, smudge, exc):
    out=[]
    order_=np.argsort(M[:,0],kind='stable')
    bounds=np.searchsorted(M[order_,0], np.arange(M[:,0].max()+2))
    for pg in range(M[:,0].max()+1):
        idx=order_[bounds[pg]:bounds[pg+1]]
        if not len(idx): continue
        pos={(int(M[i,1]),int(M[i,2])):int(i) for i in idx}
        for k,_ in headwords(pg):
            mo=[]; c=0
            while True:
                i=pos.get((k,c))
                if i is None or smudge[i]: break
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

def resoudre(lab, M, tab, smudge, exc, alt):
    hw=collecter(lab,M,tab,smudge,exc)
    C=[candidats(mo,lab,alt) for _,_,mo in hw]
    n=len(hw)
    INF=1e18
    cout=[np.array([c[2] for c in C[0]], float)]
    preceding=[None]
    for i in range(1,n):
        ci=C[i]; cp=C[i-1]
        cles_p=[c[0].lower() for c in cp]; cles_i=[c[0].lower() for c in ci]
        prev=cout[-1]
        best=np.full(len(ci), INF); arg=np.zeros(len(ci), int)
        for b,kb in enumerate(cles_i):
            v=prev + np.array([0.0 if ka<=kb else PENALITE for ka in cles_p])
            j=int(np.argmin(v)); best[b]=v[j]+ci[b][2]; arg[b]=j
        cout.append(best); preceding.append(arg)
    # backtracking
    j=int(np.argmin(cout[-1])); path_=[j]
    for i in range(n-1,0,-1):
        j=int(preceding[i][j]); path_.append(j)
    path_.reverse()
    fresh={}; log_=[]
    for i,(pg,k,mo) in enumerate(hw):
        f,subs,d = C[i][path_[i]]
        if d==0: continue
        orig="".join(ch for _,ch,_ in mo)
        for j,a in subs:
            if a!=mo[j][1]:
                col,anc,_=mo[j]
                fresh[(pg,k,col)]=a
                log_.append((pg,k,col,anc,a,orig,f))
    return fresh, log_, hw, C, path_

if __name__=="__main__":
    from decode import smudges
    from generate import exceptions
    lab=np.load(f"{T}/km_lab.npy"); M=np.load(f"{T}/meta_all.npy")
    tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    alt=pickle.load(open(f"{T}/cls_alternatives.pkl","rb"))
    exc=dict(exceptions())
    fresh,log_,hw,C,ch=resoudre(lab,M,tab,smudges(),exc,alt)
    print(len(hw),"headwords ;",len(log_),"cells corrected")
    with open(f"{T}/journal_vedettes.txt","w",encoding='utf-8') as f:
        f.write("page\tligne\tcol\tlu\tcorrige\tvedette lue\tvedette retenue\n")
        for j in log_: f.write("\t".join(map(str,j))+"\n")
    import os
    p=f"{T}/exceptions.txt"; lines=[]
    for l in open(p,encoding='utf-8'):
        l=l.rstrip("\n")
        if l.startswith("#") or not l.strip(): lines.append(l); continue
        a,b,c,dd=l.split("\t")
        if (int(a),int(b),int(c)) not in fresh: lines.append(l)
    with open(p,"w",encoding='utf-8') as f:
        f.write("\n".join(lines)+"\n")
        for (pg,k,c),v in sorted(fresh.items()): f.write(f"{pg}\t{k}\t{c}\t{v}\n")

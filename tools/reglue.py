# -*- coding: utf-8 -*-
"""Glues the repaired pages back into the global tables, and reindexes the corrections."""
import numpy as np, json, os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=_ROOT + "/work"

def run_step():
    rep=json.load(open(f"{T}/repair.json"))
    dec={r['pagino']: (r['decalage'], r.get('colonne',0)) for r in rep}
    Mn=np.load(f"{T}/repair_meta.npy"); Gn=np.load(f"{T}/repair_grp.npy")
    Cn=np.load(f"{T}/repair_cells.npy")
    M=np.load(f"{T}/meta_all.npy"); G=np.load(f"{T}/km_lab.npy")
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r')
    S=np.load(f"{T}/km_sim.npy")
    # index of the new slices, by page
    npg={}
    for pg in np.unique(Mn[:,0]):
        w=np.where(Mn[:,0]==pg)[0]; npg[int(pg)]=(w[0], w[-1]+1)
    pages=sorted(np.unique(M[:,0]).tolist())
    mM=[]; mG=[]; mC=[]; mS=[]
    for pg in pages:
        if pg in npg:
            a,b=npg[pg]
            mM.append(Mn[a:b]); mG.append(Gn[a:b]); mC.append(Cn[a:b])
            mS.append(np.full(b-a, 0.97, np.float32))
        else:
            w=np.where(M[:,0]==pg)[0]
            mM.append(M[w[0]:w[-1]+1]); mG.append(G[w[0]:w[-1]+1])
            mC.append(np.asarray(C[w[0]:w[-1]+1])); mS.append(S[w[0]:w[-1]+1])
    M2=np.concatenate(mM); G2=np.concatenate(mG).astype(G.dtype)
    C2=np.concatenate(mC); S2=np.concatenate(mS)
    print("cells:", len(M), "->", len(M2))
    np.save(f"{T}/meta_all.npy", M2); np.save(f"{T}/km_lab.npy", G2)
    np.save(f"{T}/cells_all.npy", C2); np.save(f"{T}/km_sim.npy", S2)
    # reindexing of the corrections
    for name_ in ("exceptions.txt","exceptions_manual.txt","exceptions_pairs.txt"):
        p=f"{T}/{name_}"
        if not os.path.exists(p): continue
        out=[]; n=0
        for l in open(p,encoding='utf-8'):
            if l.startswith('#') or not l.strip(): out.append(l); continue
            a,b,c,v=l.rstrip('\n').split('\t')
            d,sc=dec.get(int(a),(0,0))
            if d or sc:
                b=str(int(b)+d); c=str(int(c)+sc); n+=1
            out.append(f"{a}\t{b}\t{c}\t{v}\n")
        open(p,'w',encoding='utf-8').writelines(out)
        print(f"  {name_} : {n} corrections reindexed")

if __name__=="__main__": run_step()

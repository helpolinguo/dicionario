"""Two verifiable regularities of the book, applied to the ambiguous cells of
the headwords alone.

1. **The page's alphabetical section.** On a given page, the headwords nearly
   all begin with the same letter. Surveyed over the 639 pages, that agreement
   is overwhelming. When an initial contradicts the majority of its page and
   its cell is ambiguous, we keep the majority.

2. **The ending of the headwords.** Over 7,295 headwords surveyed, the last
   letter is an `o` in 4,584 cases, `r` in 1,527, `a` in 613, `e` in 52,
   `i` in 31 -- the morphology of Ido (noun -o, verb -ar/-ir/-or,
   adjective -a, adverb -e). The fourth value, `c` (269 cases), does not exist
   as an ending in Ido: it is the `c`/`o` confusion, the commonest of the
   decoding. When a headword's ending is ambiguous and falls outside the
   morphological inventory while one of its neighbouring readings falls
   inside, we correct it.

Nothing is corrected on a cell the decoding reads without hesitating.
"""
import numpy as np, pickle, collections, sys
sys.path.insert(0,'/root/dicionario/outils')
from consolidate import vedettes
T="/root/dicionario/travail"
FINALES = set("oarei")

def mots_vedette(lab, M, tab, bav, exc):
    ordre=np.argsort(M[:,0],kind='stable')
    bornes=np.searchsorted(M[ordre,0], np.arange(M[:,0].max()+2))
    out=collections.defaultdict(list)
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
            if len(mo)>=3: out[pg].append((k,mo))
    return out

def executer(seuil_maj=0.6, mini=3):
    lab=np.load(f"{T}/km_lab.npy"); M=np.load(f"{T}/meta_all.npy")
    tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    alt=pickle.load(open(f"{T}/cls_alternatives.pkl","rb"))
    from decode import bavures
    from generate import exceptions
    bav=bavures(); exc=dict(exceptions())
    ved=mots_vedette(lab,M,tab,bav,exc)
    nouv={}; journal=[]
    for pg,liste in ved.items():
        # 1. initial
        if len(liste)>=mini:
            c=collections.Counter(mo[0][1] for _,mo in liste)
            (maj,n),=c.most_common(1)
            if n/len(liste)>=seuil_maj:
                for k,mo in liste:
                    col,ch,i=mo[0]
                    if ch!=maj and maj in ([ch]+list(alt[lab[i]])):
                        nouv[(pg,k,col)]=maj
                        journal.append((pg,k,col,ch,maj,"initiale de section","".join(x[1] for x in mo)))
        # 2. ending
        for k,mo in liste:
            col,ch,i=mo[-1]
            if ch in FINALES: continue
            cands=[a for a in alt[lab[i]] if a in FINALES]
            if not cands: continue
            pref=[a for a in ("o","a","r","e","i") if a in cands]
            v=pref[0]
            nouv[(pg,k,col)]=v
            journal.append((pg,k,col,ch,v,"finale morphologique","".join(x[1] for x in mo)))
    return nouv, journal

if __name__=="__main__":
    nouv, journal = executer()
    print(len(journal),"cellules de vedette corrigees")
    import collections as C
    print(C.Counter(j[5] for j in journal))
    with open(f"{T}/journal_vedettes.txt","w",encoding='utf-8') as f:
        f.write("page\tligne\tcol\tlu\tcorrige\tregle\tvedette lue\n")
        for j in journal: f.write("\t".join(map(str,j))+"\n")
    p=f"{T}/exceptions.txt"; lignes=[]
    for l in open(p,encoding='utf-8'):
        l=l.rstrip("\n")
        if l.startswith("#") or not l.strip(): lignes.append(l); continue
        a,b,c,dd=l.split("\t")
        if (int(a),int(b),int(c)) not in nouv: lignes.append(l)
    with open(p,"w",encoding='utf-8') as f:
        f.write("\n".join(lignes)+"\n")
        for (pg,k,c),v in sorted(nouv.items()): f.write(f"{pg}\t{k}\t{c}\t{v}\n")

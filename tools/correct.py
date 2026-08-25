"""Correcting the doubtful readings by the book's own lexicon.

The principle: the dictionary repeats its vocabulary thousands of times. A
form read once, when a variant obtained by replacing an ambiguous cell with
one of its neighbours in the group is attested dozens of times, is a
misreading, not a slip of the typescript.

A cell is declared ambiguous only if its group has, among its nearest
neighbours in the space of shapes, a group of a different label at a
correlation above 0.86. It is therefore the decoding that doubts, not we.

Every substitution is logged in work/journal_corrections.txt and entered in
work/exceptions.txt: it stays inspectable and reversible.
"""
import numpy as np, pickle, collections, glob, os, sys, itertools
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
T=_ROOT + "/work"
LETTRES=set("abcdefghijklmnopqrstuvwxyz")
MAJ=set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
TOUTES=LETTRES|MAJ

def decoder_livre(lab, M, tab, smudge, exc=None):
    """Returns {page: [(k, [(column, character, cell_index), ...])]}"""
    pages={}
    order_=np.argsort(M[:,0], kind='stable')
    bounds=np.searchsorted(M[order_,0], np.arange(M[:,0].max()+2))
    for pg in range(M[:,0].max()+1):
        idx=order_[bounds[pg]:bounds[pg+1]]
        if not len(idx): continue
        per=collections.defaultdict(list)
        for i in idx:
            if smudge[i]: continue
            k,c=int(M[i,1]),int(M[i,2])
            ch=exc.get((pg,k,c), str(tab[lab[i]])) if exc else str(tab[lab[i]])
            per[k].append((c, ch, int(i)))
        for k in per: per[k].sort()
        pages[pg]=sorted(per.items())
    return pages

def words(line_):
    """Cuts a line (list of (col, char, idx)) into contiguous words."""
    out=[]; cur=[]
    prev=None
    for col,ch,i in line_:
        if prev is not None and col!=prev+1 and cur:
            out.append(cur); cur=[]
        cur.append((col,ch,i)); prev=col
    if cur: out.append(cur)
    # we isolate the alphabetic core of each group
    res=[]
    for g in out:
        j=0
        while j < len(g):
            while j<len(g) and g[j][1] not in TOUTES: j+=1
            d=j
            while j<len(g) and g[j][1] in TOUTES: j+=1
            if j>d: res.append(g[d:j])
    return res

def run_step(mini_atteste=8, maxi_fautif=5, max_pos=3, margin=8, marge_ngram=6.0):
    lab=np.load(f"{T}/km_lab.npy"); M=np.load(f"{T}/meta_all.npy")
    tab=np.load(f"{T}/cls_lab.npy", allow_pickle=True)
    from decode import smudges
    from generate import exceptions
    smudge=smudges(); exc=dict(exceptions())
    alt=pickle.load(open(f"{T}/cls_alternatives.pkl","rb"))
    pages=decoder_livre(lab, M, tab, smudge, exc)
    # 1. the book's lexicon
    freq=collections.Counter()
    all_=[]
    for pg,lines in pages.items():
        for k,line_ in lines:
            for mo in words(line_):
                f="".join(c for _,c,_ in mo)
                if len(f)>=3: freq[f]+=1; all_.append((pg,k,mo,f))
    print(f"{len(freq)} formes distinctes, {sum(freq.values())} occurrences", flush=True)
    # 2. correction
    log_=[]; exc={}
    for pg,k,mo,f in all_:
        if freq[f] > maxi_fautif: continue
        # we do not touch proper nouns or initialisms: a form that carries a
        # capital anywhere but at the start, or whose initial is a capital, has no
        # business being brought back to the common lexicon.
        if any(c in MAJ for c in f[1:]): continue   # initialisms: we do not touch
        key_ = f[0].lower()+f[1:] if f[0] in MAJ else f
        pos=[j for j,(c0,_,i) in enumerate(mo) if alt[lab[i]] and (pg,k,c0) not in exc]
        if not pos or len(pos)>max_pos: continue
        cands=[]
        choix=[[mo[j][1]]+alt[lab[mo[j][2]]] for j in pos]
        for combi in itertools.product(*choix):
            if all(a==mo[j][1] for a,j in zip(combi,pos)): continue
            l=list(f)
            for a,j in zip(combi,pos): l[j]=a
            v="".join(l)
            vv = v[0].lower()+v[1:] if v[0] in MAJ else v
            n = freq.get(v,0)+ (freq.get(vv,0) if vv!=v else 0)
            if n >= mini_atteste: cands.append((n, v, combi))
        if not cands: continue
        cands.sort(reverse=True)
        n1,v1,c1=cands[0]
        if len(cands)>1 and cands[1][0]*3 > n1: continue   # ambiguous: we abstain
        if n1 < margin*max(freq[f],1): continue            # the gap must be clear
        for a,j in zip(c1,pos):
            if a!=mo[j][1]:
                col,ancien,i=mo[j]
                exc[(pg,k,col)]=a
                log_.append((pg,k,col,ancien,a,f,v1,freq[f],n1))
    # --- second stage: a model of character n-grams -------------------------
    # Some forms have no attestation at all: a headword often appears only once.
    # We then apply to them a model of order 4 learnt on the book's vocabulary
    # (forms seen at least three times), and substitute only if the gap in
    # likelihood is clear.
    import math
    ngr=collections.Counter(); ctx=collections.Counter()
    for f,n in freq.items():
        if n<3: continue
        s2="^^^"+f.lower()+"$"
        for i in range(3,len(s2)):
            ngr[s2[i-3:i+1]]+=n; ctx[s2[i-3:i]]+=n
    V=len(set(c for g in ngr for c in g))+1
    def score(w):
        s2="^^^"+w.lower()+"$"; t=0.0
        for i in range(3,len(s2)):
            t+=math.log10((ngr.get(s2[i-3:i+1],0)+0.2)/(ctx.get(s2[i-3:i],0)+0.2*V))
        return t
    n2=0
    for pg,k,mo,f in all_:
        if freq[f] > 1: continue
        if any(c in MAJ for c in f[1:]): continue
        if any((pg,k,c0) in exc for c0,_,_ in mo): continue
        pos=[j for j,(c0,_,i) in enumerate(mo) if alt[lab[i]] and (pg,k,c0) not in exc]
        if not pos or len(pos)>2: continue
        base=score(f); best=(base+marge_ngram, None)
        for combi in itertools.product(*[[mo[j][1]]+alt[lab[mo[j][2]]] for j in pos]):
            l=list(f)
            for a,j in zip(combi,pos): l[j]=a
            v="".join(l)
            if v==f: continue
            sc=score(v)
            if sc>best[0]: best=(sc,(v,combi))
        if best[1] is None: continue
        v,combi=best[1]
        for a,j in zip(combi,pos):
            if a!=mo[j][1]:
                col,anc,i=mo[j]
                exc[(pg,k,col)]=a
                log_.append((pg,k,col,anc,a,f,v,freq[f],-1))
                n2+=1
    print(f"{len(log_)} cells corrected in {len(set((j[0],j[1]) for j in log_))} lines "
          f"(of which {n2} by the n-gram model)", flush=True)
    return exc, log_, freq

if __name__=="__main__":
    exc, log_, freq = run_step()
    with open(f"{T}/journal_corrections.txt","w",encoding='utf-8') as f:
        f.write("page\tligne\tcol\tlu\tcorrige\tforme lue\tforme retenue\tfreq lue\tfreq retenue\n")
        for j in log_: f.write("\t".join(map(str,j))+"\n")
    # merged into exceptions.txt, preserving the manual entries
    manuel=[]
    p=f"{T}/exceptions.txt"
    if os.path.exists(p):
        for l in open(p,encoding='utf-8'):
            if l.startswith("#") or not l.strip(): manuel.append(l.rstrip("\n")); continue
            a,b,c,d=l.rstrip("\n").split("\t")
            if (int(a),int(b),int(c)) not in exc: manuel.append(l.rstrip("\n"))
    with open(p,"w",encoding='utf-8') as f:
        f.write("\n".join(manuel)+"\n")
        for (pg,k,c),v in sorted(exc.items()): f.write(f"{pg}\t{k}\t{c}\t{v}\n")
    print("exceptions.txt :", len(exc), "entrees automatiques")

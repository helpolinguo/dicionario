"""Structural analysis of the decoded dictionary.

The typescript follows a strict grammar, and it is that grammar which allows
the quality of the decoding to be measured without a control transcription:
an entry begins with an underlined headword in column 0, its continuation
lines are indented by three, it often carries a part of speech in underlined
parentheses, it divides into senses numbered in Roman figures, and it ends
with a code of languages (a subset of D E F I R S L).
"""
import numpy as np, pickle, re, collections, sys
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from consolidate import headwords
T=_ROOT + "/work"
CODES=re.compile(r'-\s*([DEFIRSL]{1,7})[.,]?\s*$')
ENDINGS=("o","a","e","i","ar","ir","or","um","e")

def book_text():
    from decode import load_, page_text
    from generate import exceptions
    lab,M=load_(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True); exc=exceptions()
    pages={}
    for pg in range(int(M[:,0].max())+1):
        try: lines=page_text(pg,lab,M,tab)
        except Exception: continue
        out=[]
        for k,s in lines:
            l=list(s)
            for (pp,kk,cc),v in exc.items():
                if pp==pg and kk==k:
                    if cc>=len(l): l.extend(" "*(cc-len(l)+1))
                    l[cc]=v
            out.append((k,"".join(l).rstrip()))
        pages[pg]=out
    return pages

def entries(pages):
    ent=[]
    for pg in sorted(pages):
        try: hw={k for k,_ in headwords(pg)}
        except Exception: hw=set()
        cur=None
        for k,s in pages[pg]:
            if k in hw and s.strip():
                if cur: ent.append(cur)
                cur=dict(page=pg, ligne=k, lignes=[s])
            elif cur is not None and s.strip():
                cur['lignes'].append(s)
        if cur: ent.append(cur); cur=None
    for e in ent:
        t=" ".join(x.strip() for x in e['lignes'])
        e['texte']=t
        m=re.match(r'^([A-Za-z"\'-]+)', t)
        e['vedette']=m.group(1).rstrip('.') if m else ""
        e['code']=CODES.search(t)
    return ent
if __name__=="__main__":
    pages=book_text()
    ent=entries(pages)
    print(f"{len(ent)} entries located over {len(pages)} pages")
    with_arg=sum(1 for e in ent if e['code'])
    print(f"  final language code recognised: {with_arg} ({100*with_arg/len(ent):.1f} %)")
    good_=sum(1 for e in ent if e['vedette'] and e['vedette'][-1] in "oaeir")
    print(f"  headword with a valid morphological ending: {good_} ({100*good_/len(ent):.1f} %)")
    v=[e['vedette'].lower() for e in ent if e['vedette']]
    breaks=sum(1 for a,b in zip(v,v[1:]) if a>b)
    print(f"  ruptures de l'ordre alphabetique : {breaks} ({100*breaks/max(len(v)-1,1):.1f} %)")
    for e in ent: e['code']=e['code'].group(1) if e['code'] else None
    pickle.dump(ent, open(f"{T}/entrees.pkl","wb"))

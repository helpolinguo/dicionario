# -*- coding: utf-8 -*-
"""The rate of exactness measured on the pages transcribed by hand.

    We compare character by character, cell by cell, the automatic
    transcription and the reference transcription. The test pages have never
    served for learning.
    """
import numpy as np, sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
T=_ROOT + "/work"

def reference(path_):
    ref={}
    for l in open(path_, encoding='utf-8'):
        l=l.rstrip("\n")
        if not l or "\t" not in l: continue
        k,s=l.split("\t",1)
        try: ref[int(k)]=s
        except ValueError: pass
    return ref

def mesurer(pg, path_, avec_exceptions=True):
    from decode import load_, page_text
    lab,M=load_(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    lines=dict(page_text(pg,lab,M,tab))
    if avec_exceptions:
        from generate import exceptions
        for (pp,kk,cc),v in exceptions().items():
            if pp!=pg or kk not in lines: continue
            l=list(lines[kk])
            if cc>=len(l): l.extend(" "*(cc-len(l)+1))
            l[cc]=v; lines[kk]="".join(l)
    ref=reference(path_)
    good=tot=0; fautes=[]
    for k,s in ref.items():
        d=lines.get(k,"")
        n=max(len(s),len(d))
        for i in range(n):
            a=s[i] if i<len(s) else " "
            b=d[i] if i<len(d) else " "
            tot+=1
            if a==b: good+=1
            elif a!=" " or b!=" ": fautes.append((k,i,a,b))
    return good, tot, fautes

if __name__=="__main__":
    for pg,ch in [(560,f"{T}/amorce_test_p560.txt"), (450,f"{T}/amorce_test_p450.txt")]:
        if not os.path.exists(ch): continue
        b,t,f=mesurer(pg,ch)
        print(f"page image {pg} : {b}/{t} = {100*b/t:.2f} %   ({len(f)} departures)")
        for x in f[:25]: print("   ", x)

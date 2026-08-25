# -*- coding: utf-8 -*-
"""A check on the yield of the proofreading.

The book runs at around sixteen corrections a page. A page that returns zero
or one has probably not been read: the two pages of the Prefaco came back
empty, and they were faulty. We therefore watch the count, rather than
discover it through the reader.
"""
import os, glob, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=_ROOT + "/work/relecture"

def run_step(threshold=3):
    lines={}; underline={}
    for f in sorted(glob.glob(f"{T}/rez/p*.txt")):
        pg=int(os.path.basename(f)[1:4]); n=0
        for l in open(f,encoding='utf-8'):
            if l.startswith("#"): break
            if "|" in l: n+=1
        lines[pg]=n
    for f in sorted(glob.glob(f"{T}/rez/p*.sou")):
        pg=int(os.path.basename(f)[1:4])
        underline[pg]=sum(1 for l in open(f,encoding='utf-8') if "|" in l and not l.startswith("#"))
    import statistics as st
    v=sorted(lines.values())
    print(f"pages proofread: {len(lines)} ; lines corrected: median {st.median(v)}, total {sum(v)}")
    thin=[(p,n,underline.get(p,0)) for p,n in sorted(lines.items()) if n<threshold]
    without_underline=[p for p in lines if p not in underline]
    print(f"pages with fewer than {threshold} corrections: {len(thin)}")
    for p,n,s in thin: print(f"   p-{p:03d} : {n} lines corrected, {s} lines underlined")
    # Since page 96, the underlines are no longer surveyed by hand:
    # the automatic detection takes care of them. Their absence is therefore
    # not a defect.
    pass
    return [p for p,_,_ in thin]+without_underline

if __name__=="__main__":
    a=run_step()
    print("\na refaire :", " ".join("%03d"%p for p in sorted(set(a))))

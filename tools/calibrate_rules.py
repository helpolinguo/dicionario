# -*- coding: utf-8 -*-
"""Calibration of the « white beneath the rule » veto against the survey by eye.

    The 91 surveyed pages serve as truth: a line listed carries the ranges
    indicated, a line absent carries none. We compare the detection with and
    without the veto.
    """
import numpy as np, sys, os, pickle
sys.path.insert(0,'/root/dicionario/outils')
import cells as C
T="/root/dicionario/travail"; ROOT="/root/dicionario"

def verite():
    d={}
    for l in open(f"{T}/sou_relus.txt", encoding='utf-8'):
        l=l.rstrip("\n")
        if not l.strip() or l.startswith("#"): continue
        a,b,c=l.split("\t")
        d[(int(a),int(b))]=set(tuple(int(x) for x in s.split("-")) for s in c.split(",") if s)
    return d

def mesurer(pages, veto):
    V=verite(); pgset=set(p for p,_ in V)
    fp=fn=ok=0; lines=0
    for pg in pages:
        try:
            d=C.analyse(f"{ROOT}/scan/p-{pg:03d}.jpg")
        except Exception as e:
            print("  p%03d illisible: %s"%(pg,e)); continue
        r=d['norm']; vstep=d['pasv']; hstep=d['pash']; xg=d['xg']
        hstep,xg=C.raffiner_pas(r,d['bloc'],hstep,xg); xg=xg%hstep
        ncol=int(np.floor((r.shape[1]-xg)/hstep))
        underline=C.underlines(r,d['lignes'],vstep,hstep,xg,ncol,veto_sous=veto)
        z=np.load(f"{T}/cellules/p-{pg:03d}.npz",allow_pickle=True); c0=int(z['col0'])
        for k,(yy,pl,tot) in underline.items():
            pl=[(a-c0,b-c0) for a,b in pl]
            att=V.get((pg,k))
            lines+=1
            if att is None:
                if pl: fp+=1
            else:
                if not pl: fn+=1
                else: ok+=1
    return fp,fn,ok,lines

if __name__=="__main__":
    V=verite(); pgs=sorted(set(p for p,_ in V))[:24]
    print("pages tested:", pgs)
    for veto in (None, 0.15):
        fp,fn,ok,n=mesurer(pgs, veto)
        print("veto=%-5s  lines=%4d  false rules=%3d  rules missed=%3d  true lines with a rule=%3d"
              %(veto,n,fp,fn,ok), flush=True)

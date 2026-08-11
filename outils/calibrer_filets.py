# -*- coding: utf-8 -*-
"""Calibration du veto « du blanc sous le filet » contre le releve a l'oeil.

Les 91 pages relevees servent de verite : une ligne listee porte les plages
indiquees, une ligne absente n'en porte aucune. On compare la detection avec
et sans veto.
"""
import numpy as np, sys, os, pickle
sys.path.insert(0,'/root/dicionario/outils')
import cellules as C
T="/root/dicionario/travail"; RAC="/root/dicionario"

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
    fp=fn=ok=0; lignes=0
    for pg in pages:
        try:
            d=C.analyser(f"{RAC}/scan/p-{pg:03d}.jpg")
        except Exception as e:
            print("  p%03d illisible: %s"%(pg,e)); continue
        r=d['norm']; pasv=d['pasv']; pash=d['pash']; xg=d['xg']
        pash,xg=C.raffiner_pas(r,d['bloc'],pash,xg); xg=xg%pash
        ncol=int(np.floor((r.shape[1]-xg)/pash))
        sou=C.soulignements(r,d['lignes'],pasv,pash,xg,ncol,veto_sous=veto)
        z=np.load(f"{T}/cellules/p-{pg:03d}.npz",allow_pickle=True); c0=int(z['col0'])
        for k,(yy,pl,tot) in sou.items():
            pl=[(a-c0,b-c0) for a,b in pl]
            att=V.get((pg,k))
            lignes+=1
            if att is None:
                if pl: fp+=1
            else:
                if not pl: fn+=1
                else: ok+=1
    return fp,fn,ok,lignes

if __name__=="__main__":
    V=verite(); pgs=sorted(set(p for p,_ in V))[:24]
    print("pages testees :", pgs)
    for veto in (None, 0.15):
        fp,fn,ok,n=mesurer(pgs, veto)
        print("veto=%-5s  lignes=%4d  faux filets=%3d  filets manques=%3d  lignes vraies avec filet=%3d"
              %(veto,n,fp,fn,ok), flush=True)

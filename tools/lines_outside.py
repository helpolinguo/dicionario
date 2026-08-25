# -*- coding: utf-8 -*-
"""Ou tombent, sur le lattis de la page, les lignes que le bloc a laissees dehors ?

Le lattis d'une page est une droite : y(k) = y0 + k*pasv, ou y0 est la premiere
ligne STOCKEE, d'indice 0. Une ligne perdue au-dessus prend donc un indice
negatif, une ligne perdue en bas un indice au-dela du dernier. Ainsi la
numerotation des lignes deja lues ne bouge pas, et aucune correction indexee
par (page, ligne, colonne) n'est invalidee.
"""
import sys, numpy as np
sys.path.insert(0,'/root/dicionario/outils')
import page as P
RAC="/root/dicionario"; T=f"{RAC}/travail"

def lattis(pg, seuil=0.02):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    lg=np.array(z['lignes']); pasv=float(z['pasv'])
    a=P.charger(f"{RAC}/scan/p-{pg:03d}.jpg")
    b=P.masquer_bords(P.normaliser(a)); _,r=P.desincliner(b)
    ph=r.sum(axis=1)
    y0=float(lg[0,1]); k0=int(lg[0,0])
    connus={int(k) for k in lg[:,0]}
    H=len(ph)
    kmin=int(np.floor((0-y0)/pasv))-1; kmax=int(np.ceil((H-1-y0)/pasv))+1
    seuilv=max(ph.max()*seuil, 3.0)
    out=[]
    for k in range(kmin, kmax+1):
        y=y0+(k-k0)*pasv
        i0=max(int(round(y-0.45*pasv)),0); i1=min(int(round(y+0.45*pasv)),H)
        if i1-i0<3: continue
        enc=float(ph[i0:i1].max())
        out.append((k, round(y,1), round(enc,1), enc>seuilv, k in connus))
    return z, out

if __name__=="__main__":
    for pg in [int(x) for x in sys.argv[1:]]:
        z,out=lattis(pg)
        print("=== p%03d  pasv %.2f  bloc %s  %d lignes stockees"%(pg,float(z['pasv']),list(z['bloc']),len(z['lignes'])))
        for k,y,e,encre,connu in out:
            if encre and not connu: print("   HORS  k=%3d  y=%6.1f  encre %.0f"%(k,y,e))

def colonnes(pg, ks):
    """Pour chaque ligne k, la premiere et la derniere colonne encree."""
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    lg=np.array(z['lignes']); pasv=float(z['pasv']); pash=float(z['pash'])
    xg=float(z['xg']); col0=int(z['col0'])
    a=P.charger(f"{RAC}/scan/p-{pg:03d}.jpg")
    b=P.masquer_bords(P.normaliser(a)); _,r=P.desincliner(b)
    H,W=r.shape; y0=float(lg[0,1]); k0=int(lg[0,0])
    out={}
    for k in ks:
        y=y0+(k-k0)*pasv
        i0=max(int(round(y-0.45*pasv)),0); i1=min(int(round(y+0.45*pasv)),H)
        pv=r[i0:i1].sum(axis=0)
        xs=np.where(pv>max(pv.max()*0.10,0.5))[0]
        if not len(xs): out[k]=None; continue
        c0=int(round((xs.min()-xg)/pash))-col0
        c1=int(round((xs.max()-xg)/pash))-col0
        out[k]=(c0,c1)
    return out

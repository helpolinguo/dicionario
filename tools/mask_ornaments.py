# -*- coding: utf-8 -*-
"""Neutralises the cells an ornament covers.

An ornament -- the section letter, the signature -- falls into the grid like
any other ink: the decoder reads characters in it, and they are noise. We
therefore erase the cells whose centre falls inside the ornament's box. The
box is measured on the original scan; the grid lives in the rescaled image.
The ratio of the two heights gives the factor.
"""
import numpy as np, json, os, sys
RAC="/root/dicionario"; T=f"{RAC}/travail"

def executer(sortie=f"{T}/exceptions_ornements.txt", marge=3, dilate=0.35):
    orn=json.load(open(f"{T}/ornements.json"))
    n=0
    with open(sortie,"w",encoding='utf-8') as f:
        f.write("# Cellules recouvertes par un ornement : ce n'est pas de la frappe.\n")
        for e in orn:
            pg=e['pagino']
            p=f"{T}/cellules/p-{pg:03d}.npz"
            if not os.path.exists(p): continue
            z=np.load(p, allow_pickle=True)
            forme=tuple(z['shape']); ech=forme[0]/e['H']
            pasv=float(z['pasv']); pash=float(z['pash'])
            xg=float(z['xg']); col0=int(z['col0']); ncol=z['occ'].shape[1]
            lg=z['lignes']
            # We mask by the TIGHT box where there is one: the cutting box,
            # deliberately wide so as to crop nothing of the image, would bite
            # into the text typed above.
            b=e.get('masque', e)
            # Dilated, because around the signature there remained fragments of
            # the flourish that the decoder read as « ,F » -- but downwards and
            # sideways only, never upwards.
            dx=b['w']*ech*dilate; dh=b['h']*ech*0.12; db=b['h']*ech*dilate
            y0=b['y']*ech-dh; y1=(b['y']+b['h'])*ech+db
            x0=b['x']*ech-dx; x1=(b['x']+b['w'])*ech+dx
            c0=int(np.floor((x0-xg)/pash))-col0-marge
            c1=int(np.ceil ((x1-xg)/pash))-col0+marge
            for k,yy in lg:
                if yy+1.2*pasv < y0 or yy-1.2*pasv > y1: continue
                for c in range(max(c0,0), min(c1+1,ncol)):
                    f.write(f"{pg}\t{int(k)}\t{c}\t \n"); n+=1
    print("cellules neutralisees :", n)

if __name__=="__main__": executer()

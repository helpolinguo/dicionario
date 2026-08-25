# -*- coding: utf-8 -*-
"""Neutralises the cells an ornament covers.

An ornament -- the section letter, the signature -- falls into the grid like
any other ink: the decoder reads characters in it, and they are noise. We
therefore erase the cells whose centre falls inside the ornament's box. The
box is measured on the original scan; the grid lives in the rescaled image.
The ratio of the two heights gives the factor.
"""
import numpy as np, json, os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=_ROOT; T=f"{ROOT}/travail"

def run_step(out_path=f"{T}/exceptions_ornements.txt", margin=3, dilate=0.35):
    orn=json.load(open(f"{T}/ornements.json"))
    n=0
    with open(out_path,"w",encoding='utf-8') as f:
        f.write("# Cellules recouvertes par un ornement : ce n'est pas de la frappe.\n")
        for e in orn:
            pg=e['pagino']
            p=f"{T}/cellules/p-{pg:03d}.npz"
            if not os.path.exists(p): continue
            z=np.load(p, allow_pickle=True)
            forme=tuple(z['shape']); scale=forme[0]/e['H']
            vstep=float(z['pasv']); hstep=float(z['pash'])
            xg=float(z['xg']); col0=int(z['col0']); ncol=z['occ'].shape[1]
            lg=z['lignes']
            # We mask by the TIGHT box where there is one: the cutting box,
            # deliberately wide so as to crop nothing of the image, would bite
            # into the text typed above.
            b=e.get('masque', e)
            # Dilated, because around the signature there remained fragments of
            # the flourish that the decoder read as « ,F » -- but downwards and
            # sideways only, never upwards.
            dx=b['w']*scale*dilate; dh=b['h']*scale*0.12; db=b['h']*scale*dilate
            y0=b['y']*scale-dh; y1=(b['y']+b['h'])*scale+db
            x0=b['x']*scale-dx; x1=(b['x']+b['w'])*scale+dx
            c0=int(np.floor((x0-xg)/hstep))-col0-margin
            c1=int(np.ceil ((x1-xg)/hstep))-col0+margin
            for k,yy in lg:
                if yy+1.2*vstep < y0 or yy-1.2*vstep > y1: continue
                for c in range(max(c0,0), min(c1+1,ncol)):
                    f.write(f"{pg}\t{int(k)}\t{c}\t \n"); n+=1
    print("cells neutralised:", n)

if __name__=="__main__": run_step()

# -*- coding: utf-8 -*-
"""Propagates the block's extension to the right over the whole book.

The block of text was bounded by the columns occupied on at least three
lines: the line ends that only one line reaches fell outside -- « preciz »,
« apa », « anoni- ». The extension to the right recovers them, and it is
safe: it adds columns only after the others, without moving the origin. The
numbering of the columns does not move, so no correction already made is
invalidated.
"""
import sys, json, numpy as np
sys.path.insert(0,'/root/dicionario/outils')
from repair_pages import executer
T='/root/dicionario/travail'
a,b=int(sys.argv[1]), int(sys.argv[2])
import os
pgs=[p for p in range(a,b) if os.path.exists(f'{T}/cellules/p-{p:03d}.npz')
     and p not in (0,1,3,7,87,111,577)]
executer(pgs, sortie=f'{T}/reetendre_{a}.json')
os.rename(f'{T}/reparation_meta.npy', f'{T}/reetendre_meta_{a}.npy')
os.rename(f'{T}/reparation_grp.npy',  f'{T}/reetendre_grp_{a}.npy')
os.rename(f'{T}/reparation_cells.npy',f'{T}/reetendre_cells_{a}.npy')

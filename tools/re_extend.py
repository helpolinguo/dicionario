# -*- coding: utf-8 -*-
"""Propagates the block's extension to the right over the whole book.

The block of text was bounded by the columns occupied on at least three
lines: the line ends that only one line reaches fell outside -- « preciz »,
« apa », « anoni- ». The extension to the right recovers them, and it is
safe: it adds columns only after the others, without moving the origin. The
numbering of the columns does not move, so no correction already made is
invalidated.
"""
import os, sys, json, numpy as np
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from repair_pages import run_step
T=_ROOT + "/work"
a,b=int(sys.argv[1]), int(sys.argv[2])
import os
pgs=[p for p in range(a,b) if os.path.exists(f'{T}/cells/p-{p:03d}.npz')
     and p not in (0,1,3,7,87,111,577)]
run_step(pgs, out_path=f'{T}/re_extend_{a}.json')
os.rename(f'{T}/repair_meta.npy', f'{T}/re_extend_meta_{a}.npy')
os.rename(f'{T}/repair_grp.npy',  f'{T}/re_extend_grp_{a}.npy')
os.rename(f'{T}/repair_cells.npy',f'{T}/re_extend_cells_{a}.npy')

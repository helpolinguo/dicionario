# -*- coding: utf-8 -*-
"""Comparison sheets: the original scan above, the finished cover below,
text zone by text zone. Serves to check by eye that no letter has been lost
to the thresholding or the despeckling."""
import numpy as np, sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from PIL import Image, ImageDraw
ROOT=_ROOT
ZONES=[
 ("banniere",        0,1205, 112, 150),
 ("cap-beaufront",   10, 250, 380, 500),
 ("cap-couturat",   150, 400, 340, 470),
 ("cap-jespersen",  330, 560, 300, 420),
 ("cap-lalande",    500, 700, 290, 400),
 ("cap-lorenz",     680, 880, 300, 410),
 ("cap-ostwald",    840,1060, 320, 430),
 ("cap-pfaundler",  990,1205, 360, 480),
 ("pleyado",        230, 960, 415, 460),
 ("invitas",        180, 950, 450, 500),
 ("embleme",        480, 720, 470, 580),
 ("preciza",        380, 830, 585, 620),
 ("titre",          150,1060, 735, 800),
 ("dila",           380, 860, 845, 895),
 ("linguo",         330, 900, 930, 990),
 ("da",             500, 700,1120,1180),
 ("persiko",        330, 900,1195,1250),
 ("pesch",          400, 800,1250,1290),
 ("akademio",       380, 830,1295,1335),
 ("bas",              0,1205,1560,1620),
]
def run_step():
    n=np.load(f"{ROOT}/work/cover/levels.npy")
    end_=Image.open(f"{ROOT}/ornaments/couverture/couverture-x2.png").convert("L")
    os.makedirs(f"{ROOT}/work/audit",exist_ok=True)
    for name_,x0,x1,y0,y1 in ZONES:
        Z=max(2, min(5, 1500//max(1,(x1-x0))))
        o=np.clip(1-n[y0:y1, x0:x1],0,1)*255
        oi=Image.fromarray(o.astype(np.uint8)).resize(((x1-x0)*Z,(y1-y0)*Z),Image.LANCZOS)
        fi=end_.crop((x0*2,y0*2,x1*2,y1*2)).resize(((x1-x0)*Z,(y1-y0)*Z),Image.LANCZOS)
        W=oi.width; H=oi.height
        pl=Image.new('L',(W, H*2+34),255); d=ImageDraw.Draw(pl)
        d.text((4,2),"SCAN  "+name_,fill=0); pl.paste(oi,(0,16))
        d.text((4,H+20),"FINAL "+name_,fill=0); pl.paste(fi,(0,H+34))
        pl.save(f"{ROOT}/work/audit/{name_}.png")
        print(name_, pl.size)
if __name__=="__main__": run_step()

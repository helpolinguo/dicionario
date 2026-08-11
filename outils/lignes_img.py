"""Rend une page sous forme de lignes de cellules separees, avec reperes de colonnes."""
import numpy as np
from PIL import Image, ImageDraw
def image_lignes(cells, occ=None, k0=0, zoom=4, ecart=2, marge=54, lignes_ids=None, pas_rep=5):
    nl, nc = cells.shape[0], cells.shape[1]
    h, w = cells.shape[2], cells.shape[3]
    tw, th = w*zoom, h*zoom
    W = marge + nc*(tw+ecart) + 6
    H = 22 + nl*(th+8) + 6
    im = Image.new("RGB", (W,H), (255,255,255)); d = ImageDraw.Draw(im)
    for i in range(nl):
        y = 22 + i*(th+8)
        idl = lignes_ids[i] if lignes_ids is not None else i
        d.text((3, y+th//2-6), f"{idl:02d}", fill=(200,0,0))
        for j in range(nc):
            x = marge + j*(tw+ecart)
            g = Image.fromarray(255-np.clip(cells[i,j],0,255).astype(np.uint8)).resize((tw,th), Image.LANCZOS)
            im.paste(g,(x,y))
        d.line([(marge-3,y-3),(W-3,y-3)], fill=(230,230,230))
    for j in range(0,nc,pas_rep):
        x = marge + j*(tw+ecart)
        d.text((x+1, 6), str(j), fill=(0,140,0))
        d.line([(x-1,20),(x-1,H-3)], fill=(200,235,200))
    return im

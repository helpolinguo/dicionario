import numpy as np
from PIL import Image, ImageDraw, ImageFont
def sheet_(tuiles, etiquettes_lignes=True, cols=20, zoom=4, marge_g=70, titre=""):
    n=len(tuiles); h,w=tuiles[0].shape
    rows=(n+cols-1)//cols
    tw,th=w*zoom, h*zoom
    W=marge_g+cols*(tw+6)+6; H=26+rows*(th+16)+8
    im=Image.new("RGB",(W,H),(255,255,255)); d=ImageDraw.Draw(im)
    d.text((6,6), titre, fill=(0,0,160))
    for i,t in enumerate(tuiles):
        r,c=divmod(i,cols)
        x=marge_g+c*(tw+6)+3; y=26+r*(th+16)+3
        g=Image.fromarray(255-np.clip(t,0,255).astype(np.uint8)).resize((tw,th),Image.LANCZOS)
        im.paste(g,(x,y))
        d.rectangle([x-1,y-1,x+tw,y+th], outline=(220,220,220))
    for r in range(rows):
        y=26+r*(th+16)+3
        d.text((4,y+th//2-6), f"L{r:02d}", fill=(200,0,0))
    for c in range(cols):
        x=marge_g+c*(tw+6)+3
        d.text((x+2,20), f"{c}", fill=(0,150,0))
    return im

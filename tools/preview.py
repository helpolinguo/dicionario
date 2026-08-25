import sys, numpy as np
sys.path.insert(0,'/root/dicionario/outils')
from PIL import Image
from page import analyse
from scipy.ndimage import rotate as ndrotate

def apercu(name_, out_path, zoom=3, crop=None):
    d = analyse(f"/root/dicionario/scan/{name_}.jpg")
    base = ndrotate(d['img'], d['angle'], reshape=False, order=1, mode='constant', cval=255)
    im = Image.fromarray(np.clip(base,0,255).astype(np.uint8)).convert("RGB")
    px = im.load()
    W,H = im.size
    y0,y1,x0,x1 = d['bloc']
    # columns
    j = 0
    while d['xg'] + j*d['pash'] < W:
        x = int(round(d['xg'] + j*d['pash']))
        if 0<=x<W:
            for y in range(y0,min(y1+1,H)):
                r,g,b = px[x,y]; px[x,y] = (255, min(255,g//2), min(255,b//2))
        j += 1
    # baselines
    for k,y in d['lignes']:
        yy = int(round(y + d['pasv']*0.40))
        if 0<=yy<H:
            for x in range(x0,min(x1+1,W)): 
                r,g,b=px[x,yy]; px[x,yy]=(min(255,r//2),min(255,g//2),255)
    if crop: im = im.crop(crop)
    im = im.resize((im.size[0]*zoom, im.size[1]*zoom), Image.LANCZOS)
    im.save(out_path)
    return d
if __name__=="__main__":
    d=apercu(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv)>3 else 3,
             eval(sys.argv[4]) if len(sys.argv)>4 else None)
    print(d['pasv'], d['pash'], d['xg'])

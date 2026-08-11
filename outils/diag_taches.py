import numpy as np, sys
sys.path.insert(0,'/root/dicionario/outils')
from couverture import SUR
from scipy.ndimage import label, find_objects, binary_dilation
from PIL import Image, ImageDraw
RAC="/root/dicionario"
LH,LV,AIRE,ENCRE,GROS,LOIN = 12,6,900,1500,900,12
noir=np.load(f"{RAC}/travail/couv/noir_cache.npy")
BOITES=[(21,138,264,394),(188,288,218,359),(379,458,187,331),(546,638,175,323),
        (720,801,188,330),(877,974,218,358),(1034,1136,285,394)]
mp=np.zeros(noir.shape,bool)
for (x0,x1,y0,y1) in BOITES:
    m=8; mp[(max(y0-m,0))*SUR:(y1+m)*SUR,(max(x0-m,0))*SUR:(x1+m)*SUR]=True
T=noir & ~mp
d=binary_dilation(T,np.ones((1,LH*SUR),bool)); d=binary_dilation(d,np.ones((LV*SUR,1),bool))
am,na=label(d,np.ones((3,3),int)); encre=np.bincount(am[T].ravel(),minlength=na+1)
l,nb=label(T,np.ones((3,3),int)); obj=find_objects(l)
aires=np.array([int((l[obj[i]]==i+1).sum()) for i in range(nb)])
bb=np.array([(o[0].start,o[0].stop,o[1].start,o[1].stop) for o in obj])
gros=np.nonzero(aires>=GROS)[0]
Y0,Y1,X0,X1=bb[:,0],bb[:,1],bb[:,2],bb[:,3]
def dist_gros(i):
    dy=np.maximum(0,np.maximum(Y0[i]-Y1[gros], Y0[gros]-Y1[i]))
    dx=np.maximum(0,np.maximum(X0[i]-X1[gros], X0[gros]-X1[i]))
    return np.hypot(dy,dx).min() if len(gros) else 1e9
sup=[]
for i,o in enumerate(obj):
    if aires[i]>=AIRE: continue
    ys,xs=np.nonzero(l[o]==i+1)
    if encre[am[o][ys[0],xs[0]]]>=ENCRE: continue
    if dist_gros(i) <= LOIN*SUR: continue
    sup.append((i+1,o,aires[i]))
print("a supprimer:",len(sup))
np.save(f"{RAC}/travail/cv_sup.npy", np.array([k for k,_,_ in sup]))
tiles=[]
for k,o,a in sup:
    cy=(o[0].start+o[0].stop)//2; cx=(o[1].start+o[1].stop)//2; R=40*SUR
    a0,b0=max(cy-R,0),max(cx-R,0)
    w=T[a0:cy+R, b0:cx+R]
    im=Image.fromarray((~w*255).astype(np.uint8)).convert("RGB").resize((160,160),Image.NEAREST)
    dd=ImageDraw.Draw(im); s=160.0/(2*R)
    dd.rectangle([(o[1].start-b0)*s,(o[0].start-a0)*s,(o[1].stop-b0)*s,(o[0].stop-a0)*s],outline=(255,0,0))
    tiles.append((im,k,a))
cols=8; cw,ch=168,186
pl=Image.new('RGB',(cw*cols,ch*max(1,((len(tiles)+cols-1)//cols))),(255,255,255)); dd=ImageDraw.Draw(pl)
for j,(im,k,a) in enumerate(tiles):
    X=(j%cols)*cw+4; Y=(j//cols)*ch+20; pl.paste(im,(X,Y)); dd.text((X,Y-14),"%d/%d"%(k,a),fill=(0,0,0))
pl.save(f"{RAC}/travail/cv_supdet.png"); print(pl.size)

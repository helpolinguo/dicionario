import numpy as np, sys, os, json
sys.path.insert(0,'/root/dicionario/outils')
from page import charger, normaliser
RAC="/root/dicionario"
def anc_neuf(pg):
    a=charger(f'{RAC}/scan/p-{pg:03d}.jpg'); b=normaliser(a)
    H,W=b.shape; frac=0.45
    ligne=(b>0.18).mean(axis=1); colonne=(b>0.18).mean(axis=0)
    limh=int(H*0.16); lim=int(W*0.16)
    def bande(prof,bord_max,trou_max):
        fin=-1; trou=0
        for i,v in enumerate(prof):
            if v>frac: fin=i; trou=0
            else:
                if fin>=0:
                    trou+=1
                    if trou>trou_max: break
                elif i>bord_max: break
        return fin
    s=np.where(ligne[:limh]>frac)[0]; anc_h=int(s.max())+6 if len(s) else 0
    f=bande(ligne[:limh],int(H*0.02),int(H*0.012)); neu_h=f+6 if f>=0 else 0
    s=np.where(colonne[:lim]>frac)[0]; anc_g=int(s.max())+6 if len(s) else 0
    f=bande(colonne[:lim],int(W*0.02),int(W*0.012)); neu_g=f+6 if f>=0 else 0
    s=np.where(ligne[H-limh:]>frac)[0]; anc_b=(H-limh+int(s.min())-5) if len(s) else H-1
    f=bande(ligne[::-1][:limh],int(H*0.02),int(H*0.012)); neu_b=(H-1-f-5) if f>=0 else H-1
    s=np.where(colonne[W-lim:]>frac)[0]; anc_d=(W-lim+int(s.min())-5) if len(s) else W-1
    f=bande(colonne[::-1][:lim],int(W*0.02),int(W*0.012)); neu_d=(W-1-f-5) if f>=0 else W-1
    return dict(pg=pg, dh=anc_h-neu_h, dg=anc_g-neu_g, db=neu_b-anc_b, dd=neu_d-anc_d, H=H, W=W)
if __name__=="__main__":
    a,b=int(sys.argv[1]),int(sys.argv[2]); out=[]
    for pg in range(a,b):
        if os.path.exists(f'{RAC}/scan/p-{pg:03d}.jpg'):
            try: out.append(anc_neuf(pg))
            except Exception as e: print("ECHEC",pg,e)
    json.dump(out, open(f'{RAC}/travail/diag_masque_{a}.json','w'))
    import numpy as np
    dh=np.array([r['dh'] for r in out])
    print(f"pages {a}-{b} : masque haut allege sur {int((dh>20).sum())} pages (max {dh.max()} px)")

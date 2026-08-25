import numpy as np, sys, os, json
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from page import load_, normalise
ROOT=_ROOT
def old_new(pg):
    a=load_(f'{ROOT}/scan/p-{pg:03d}.jpg'); b=normalise(a)
    H,W=b.shape; frac=0.45
    line_=(b>0.18).mean(axis=1); column=(b>0.18).mean(axis=0)
    limh=int(H*0.16); lim=int(W*0.16)
    def band(depth,edge_max,hole_max):
        end_=-1; hole=0
        for i,v in enumerate(depth):
            if v>frac: end_=i; hole=0
            else:
                if end_>=0:
                    hole+=1
                    if hole>hole_max: break
                elif i>edge_max: break
        return end_
    s=np.where(line_[:limh]>frac)[0]; old_t=int(s.max())+6 if len(s) else 0
    f=band(line_[:limh],int(H*0.02),int(H*0.012)); new_t=f+6 if f>=0 else 0
    s=np.where(column[:lim]>frac)[0]; old_l=int(s.max())+6 if len(s) else 0
    f=band(column[:lim],int(W*0.02),int(W*0.012)); new_l=f+6 if f>=0 else 0
    s=np.where(line_[H-limh:]>frac)[0]; old_b=(H-limh+int(s.min())-5) if len(s) else H-1
    f=band(line_[::-1][:limh],int(H*0.02),int(H*0.012)); new_b=(H-1-f-5) if f>=0 else H-1
    s=np.where(column[W-lim:]>frac)[0]; old_r=(W-lim+int(s.min())-5) if len(s) else W-1
    f=band(column[::-1][:lim],int(W*0.02),int(W*0.012)); new_r=(W-1-f-5) if f>=0 else W-1
    return dict(pg=pg, dh=old_t-new_t, dg=old_l-new_l, db=new_b-old_b, dd=new_r-old_r, H=H, W=W)
if __name__=="__main__":
    a,b=int(sys.argv[1]),int(sys.argv[2]); out=[]
    for pg in range(a,b):
        if os.path.exists(f'{ROOT}/scan/p-{pg:03d}.jpg'):
            try: out.append(old_new(pg))
            except Exception as e: print("FAILED",pg,e)
    json.dump(out, open(f'{ROOT}/work/diag_mask_{a}.json','w'))
    import numpy as np
    dh=np.array([r['dh'] for r in out])
    print(f"pages {a}-{b} : top mask lightened on {int((dh>20).sum())} pages (max {dh.max()} px)")

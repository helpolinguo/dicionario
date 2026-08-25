"""Rebuilds every element of the cover."""
import sys, numpy as np, os, re, shutil, subprocess
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from cover import *
from PIL import Image
from scipy.ndimage import label, binary_closing, find_objects

NAMES=["beaufront","couturat","jespersen","lalande","lorenz","ostwald","pfaundler"]
BOXES=[(21,138,264,394),(188,288,218,359),(379,458,187,331),(546,638,175,323),
        (720,801,188,330),(877,974,218,358),(1034,1136,285,394)]

def body(f):
    s=open(f).read(); m=re.search(r'(<svg[^>]*>)(.*?)(</svg>)',s,re.S); return m.group(1),m.group(2)

def merge_(grey_svg, black_svg, out_path, grey="#8c8c8c"):
    e,cg=body(grey_svg); _,cn=body(black_svg)
    open(out_path,"w").write(e+cg.replace('fill="#000000"',f'fill="{grey}"')+cn+"</svg>")
    subprocess.run(["rsvg-convert","-f","pdf","-o",os.path.splitext(out_path)[0]+".pdf",out_path],check=False)
    for f in (grey_svg,black_svg,os.path.splitext(grey_svg)[0]+".pdf",os.path.splitext(black_svg)[0]+".pdf"):
        if os.path.exists(f): os.remove(f)

def run_step():
    g=monochrome_ink(f"{ROOT}/scan/p-000.jpg")
    n=normalise(g)[4:1640,0:1205]
    os.makedirs(TRV,exist_ok=True); np.save(f"{TRV}/niveaux.npy",n)
    u=oversample(n)

    # --- portraits: two tones ---
    shutil.rmtree(f"{ORN}/portraits",ignore_errors=True); os.makedirs(f"{ORN}/portraits")
    for (x0,x1,y0,y1),name_ in zip(BOXES,NAMES):
        m=6; a,b,c,d=max(x0-m,0),min(x1+m,n.shape[1]),max(y0-m,0),min(y1+m,n.shape[0])
        z=n[c:d,a:b]
        Bg,Bn=binarise_two_tones(z)
        draw(Bg,f"{ORN}/portraits/{name_}-g.svg"); draw(Bn,f"{ORN}/portraits/{name_}-n.svg")
        merge_(f"{ORN}/portraits/{name_}-g.svg",f"{ORN}/portraits/{name_}-n.svg",f"{ORN}/portraits/{name_}.svg")
        render(f"{ORN}/portraits/{name_}.svg",f"{ORN}/portraits/{name_}-x6.png",width_=(b-a)*6)
        Image.fromarray((np.clip(1-z,0,1)*255).astype(np.uint8)).resize(((b-a)*6,(d-c)*6),Image.LANCZOS)\
             .save(f"{ORN}/portraits/{name_}-gris-x6.png")

    # --- the whole cover: line lettering + two-tone portraits ---
    black=binarise_stroke(n); grey=np.zeros_like(black)
    # The word « invitas » is erased in the scan: we give it back its « i » and
    # its « t », taken from « profitar ». See tools/repair_cover.py.
    from repair_cover import apply_ as _reparer_invitas
    black=_reparer_invitas(black)
    # The grain of the paper is never truly black: we take it out by the ink
    # level, before judging anything by size.
    _av=black.sum()
    black=drop_pale(black, u)
    print("  composantes pales retirees : %.1f%% de l'encre"%(100*(1-black.sum()/max(_av,1))))
    # Final despeckling of the line layer.
    #
    # First attempt: remove the small components far from a large one. A bad
    # criterion -- the captions under the portraits have no large component at
    # all, so the dots on their i's were anchored to nothing and disappeared:
    # « PRECIZA, KONC ZA, FACILA » became « PREC ZA KONC ZA FAC LA ».
    #
    # What distinguishes dust is not size, it is isolation. We therefore dilate
    # the ink: the letters of one word join into a cluster, a smut stays alone.
    # A cluster that, with the dilation undone, does not weigh 1,500 pixels of
    # ink is dust.
    #
    # The radius counts as much as the threshold. At eight pixels, a word forms
    # a cluster but a line does not: « vu », « lia », « ZA », « di la » were
    # taken for smuts and erased. At twenty-two, the words of one line join,
    # and only a truly isolated spot stays alone.
    from scipy.ndimage import label as _lab, binary_dilation as _dil
    _R=22*OVERSAMPLE
    _clusters,_na=_lab(_dil(black, np.ones((_R,_R),bool)), np.ones((3,3),int))
    if _na:
        _ink_of=np.bincount(_clusters[black].ravel(), minlength=_na+1)
        _dust=np.where(_ink_of<1500)[0]; _dust=_dust[_dust>0]
        _alone=np.isin(_clusters,_dust) & black
        black &= ~_alone
        print("  amas de poussiere retires :", len(_dust))

    # Second despeckling, finer.
    #
    # The radius of twenty-two pixels is generous: a smut set ten pixels from a
    # word joins its cluster and survives. Some fifty of them were left, plainly
    # visible in the whites of the page. We cannot simply tighten the radius --
    # that is what erased « vu » and « di la ».
    #
    # We therefore dilate anisotropically: wide across (the words of one line
    # join), narrow in height (a spot set above a line does not join it). Then
    # we erase a component only if all three conditions hold together:
    #   - it is small (less than 900 pixels of ink);
    #   - the line it would belong to is poor in ink;
    #   - no real letter stands within twelve pixels of it.
    # The last condition is a veto, never a motive: the dot of an i, a comma, an
    # accent almost touch their letter and are therefore spared, even when their
    # caption has no large component -- which is what had made the dots of
    # « PRECIZA, KONCIZA, FACILA » disappear.
    _LH,_LV,_AREA,_INK,_THICK,_FAR = 12,6,900,1500,900,12
    _mp=np.zeros(black.shape,bool)
    for (x0,x1,y0,y1) in BOXES:
        m=8; _mp[(max(y0-m,0))*OVERSAMPLE:(y1+m)*OVERSAMPLE,(max(x0-m,0))*OVERSAMPLE:(x1+m)*OVERSAMPLE]=True
    _T=black & ~_mp
    _d=_dil(_T,np.ones((1,_LH*OVERSAMPLE),bool)); _d=_dil(_d,np.ones((_LV*OVERSAMPLE,1),bool))
    _am,_nb=_lab(_d,np.ones((3,3),int))
    _enc=np.bincount(_am[_T].ravel(),minlength=_nb+1)
    _l,_n2=_lab(_T,np.ones((3,3),int)); _ob=find_objects(_l)
    _ai=np.array([int((_l[_ob[i]]==i+1).sum()) for i in range(_n2)])
    _bb=np.array([(o[0].start,o[0].stop,o[1].start,o[1].stop) for o in _ob])
    _g=np.nonzero(_ai>=_THICK)[0]
    _Y0,_Y1,_X0,_X1=_bb[:,0],_bb[:,1],_bb[:,2],_bb[:,3]
    _done=0
    for i,o in enumerate(_ob):
        if _ai[i]>=_AREA: continue
        ys,xs=np.nonzero(_l[o]==i+1)
        if _enc[_am[o][ys[0],xs[0]]]>=_INK: continue
        if len(_g):
            dy=np.maximum(0,np.maximum(_Y0[i]-_Y1[_g], _Y0[_g]-_Y1[i]))
            dx=np.maximum(0,np.maximum(_X0[i]-_X1[_g], _X0[_g]-_X1[i]))
            if np.hypot(dy,dx).min() <= _FAR*OVERSAMPLE: continue
        black[o] &= ~(_l[o]==i+1); _done+=1
    print("  taches isolees retirees :", _done)

    for (x0,x1,y0,y1) in BOXES:
        m=6; a,b,c,d=(max(x0-m,0))*OVERSAMPLE,(min(x1+m,n.shape[1]))*OVERSAMPLE,(max(y0-m,0))*OVERSAMPLE,(min(y1+m,n.shape[0]))*OVERSAMPLE
        z=u[c:d,a:b]
        black[c:d,a:b]=remove_grain(z>THRESHOLD_BLACK,area_thick=18)
        grey[c:d,a:b]=remove_grain(z>THRESHOLD_GREY)
    os.makedirs(f"{ORN}/couverture",exist_ok=True)
    draw(grey,f"{ORN}/couverture/_g.svg"); draw(black,f"{ORN}/couverture/_n.svg")
    merge_(f"{ORN}/couverture/_g.svg",f"{ORN}/couverture/_n.svg",f"{ORN}/couverture/couverture.svg")
    render(f"{ORN}/couverture/couverture.svg",f"{ORN}/couverture/couverture-x2.png",width_=1205*2)
    Image.fromarray((np.clip(1-n,0,1)*255).astype(np.uint8)).save(f"{ORN}/couverture/couverture-nettoyee.png")
    Image.fromarray((np.clip(1-n,0,1)*255).astype(np.uint8)).resize((1205*3,1636*3),Image.LANCZOS)\
         .save(f"{ORN}/couverture/couverture-nettoyee-x3.png")

    # --- line elements ---
    shutil.rmtree(f"{ORN}/trait",ignore_errors=True); os.makedirs(f"{ORN}/trait")
    mp=np.zeros(black.shape,bool)
    for (x0,x1,y0,y1) in BOXES:
        m=8; mp[(max(y0-m,0))*OVERSAMPLE:(min(y1+m,n.shape[0]))*OVERSAMPLE,(max(x0-m,0))*OVERSAMPLE:(min(x1+m,n.shape[1]))*OVERSAMPLE]=True
    T=black & ~mp
    # emblem
    z=T[440*OVERSAMPLE:640*OVERSAMPLE, 460*OVERSAMPLE:740*OVERSAMPLE]
    C=binary_closing(z,np.ones((9*OVERSAMPLE//2,9*OVERSAMPLE//2)))
    lab,nb=label(C); objs=find_objects(lab)
    k=max(range(nb),key=lambda i:(lab[objs[i]]==i+1).sum()); sl=objs[k]
    sub=T[440*OVERSAMPLE+sl[0].start-4*OVERSAMPLE:440*OVERSAMPLE+sl[0].stop+4*OVERSAMPLE, 460*OVERSAMPLE+sl[1].start-4*OVERSAMPLE:460*OVERSAMPLE+sl[1].stop+4*OVERSAMPLE]
    draw(sub,f"{ORN}/trait/embleme-ido.svg")
    render(f"{ORN}/trait/embleme-ido.svg",f"{ORN}/trait/embleme-ido-x6.png",width_=sub.shape[1]//OVERSAMPLE*6)
    # bands of lettering
    row=T.sum(1); strips=[];i=0
    while i<len(row):
        if row[i]>0:
            j=i
            while j<len(row) and row[j:j+12*OVERSAMPLE].sum()>0: j+=1
            if j-i>8*OVERSAMPLE: strips.append((i,j))
            i=j
        else: i+=1
    for k,(a,b) in enumerate(strips):
        s=T[max(a-4*OVERSAMPLE,0):min(b+4*OVERSAMPLE,T.shape[0])]
        xs=np.where(s.sum(0)>0)[0]
        if not len(xs): continue
        s=s[:,max(xs.min()-4*OVERSAMPLE,0):min(xs.max()+5*OVERSAMPLE,s.shape[1])]
        draw(s,f"{ORN}/trait/bande{k:02d}.svg")
        render(f"{ORN}/trait/bande{k:02d}.svg",f"{ORN}/trait/bande{k:02d}-x4.png",width_=s.shape[1]//OVERSAMPLE*4)
    return len(strips)
if __name__=="__main__":
    print(run_step(),"bandes de lettrage")

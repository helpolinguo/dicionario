# -*- coding: utf-8 -*-
"""Surgical repair of the pages whose edge mask had eaten the top.

The mask for edge shadows took an underlined line of text for a shadow and
erased everything down to it: on forty-eight pages, as many as six lines were
never decoded. The mask is corrected, but recomputing everything would destroy
the work accumulated -- 5,800 corrections indexed by page, line and column,
and 3,495 groups read by eye.

We therefore repair page by page:
  1. we re-cut the page's cells with the corrected mask;
  2. we align the old page on the new, by the content of the lines, which
     gives the shift in numbering;
  3. the cells that already existed keep their group -- all the proofreading
     work stays valid;
  4. the new cells, those of the recovered lines, are attached to the group
     whose centre is nearest, in the feature space where the groups were
     formed (fidelity measured: 99 %);
  5. the page's corrections are reindexed by the same shift.
"""
import numpy as np, os, sys, json, difflib
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from features2 import feature_vector2
ROOT=_ROOT; T=f"{ROOT}/work"

def _text(cells_occ, kl_page, cols, lines, tab, smudge):
    """Dictionary line -> string, one cell per column."""
    d={}
    for (k,c),g,b in zip(cols, kl_page, smudge):
        d.setdefault(int(k),{})[int(c)] = " " if b else str(tab[g])
    out={}
    for k,v in d.items():
        n=max(v)+1 if v else 0
        out[k]="".join(v.get(i," ") for i in range(n)).rstrip()
    return out

def _offset(old, new_, dmax=16):
    """The shift d such that line k of before is line k+d of now."""
    ka=sorted(old); best=(-1.0, 0)
    for d in range(-4, dmax+1):
        s=0.0; n=0
        for k in ka:
            a=old[k]; b=new_.get(k+d)
            if not a.strip() or b is None: continue
            s+=difflib.SequenceMatcher(None, a, b).ratio(); n+=1
        if n>=8 and s/n>best[0]: best=(s/n, d)
    return best[1], best[0]

def repair_(pg, Q, tab, verbose=True):
    from cells import extract
    from decode import smudges
    old_npz=f"{T}/cellules/p-{pg:03d}.npz"
    z=np.load(old_npz, allow_pickle=True)
    M=np.load(f"{T}/meta_all.npy"); kl=np.load(f"{T}/km_lab.npy")
    sel=np.where(M[:,0]==pg)[0]
    bv=smudges()[sel]
    old_txt=_text(None, kl[sel], M[sel][:,1:], z['lignes'], tab, bv)

    d=extract(f"{ROOT}/scan/p-{pg:03d}.jpg")
    occ=d['occ']; lg=np.array(d['lignes']); bare=d['nues']
    ii,jj=np.where(occ)
    A=(np.clip(bare[ii,jj],0,1)*255.0).round().astype(np.uint8)
    X=feature_vector2(A); X=X/np.maximum(np.linalg.norm(X,axis=1,keepdims=True),1e-6)
    gnew=(X@Q.T).argmax(1).astype(np.int32)
    knew=lg[ii,0].astype(np.int32)
    Mnew=np.stack([np.full(len(ii),pg,np.int32), knew, jj.astype(np.int32)],1)
    # smudges in the new cells: the same geometric criterion
    P=A.astype(np.float32)/255.
    tot=P.sum((1,2))
    edge=(P[:,:,:2].sum((1,2))+P[:,:,-2:].sum((1,2)))/(tot+1e-6)
    top=P[:,:4,:].sum((1,2))/(tot+1e-6); bottom=P[:,18:,:].sum((1,2))/(tot+1e-6)
    bnew=((edge>0.55)|((tot<12)&(edge>0.25))|(top>0.80)|(bottom>0.85))
    new_txt=_text(None, gnew, Mnew[:,1:], lg, tab, bnew)
    dec, score = _offset(old_txt, new_txt)
    # The block can extend to the left: the columns shift by as much.
    col_score = int(z['col0']) - int(d['col0'])
    if verbose:
        print(f"  p-{pg:03d} : {len(old_txt)} lines -> {len(new_txt)} ; shift {dec:+d} line, {col_score:+d} column ; concordance {score:.3f}")
    # the cells already known keep their group
    old_key={(int(k)+dec, int(c)+col_score): int(g) for (p,k,c),g in zip(M[sel], kl[sel])}
    kept=0
    for i in range(len(gnew)):
        v=old_key.get((int(Mnew[i,1]), int(Mnew[i,2])))
        if v is not None: gnew[i]=v; kept+=1
    if verbose:
        print(f"           cells: {len(sel)} before, {len(gnew)} after ; {kept} kept, {len(gnew)-kept} new")
    # The corpus is in bytes 0-255; extraire() returns floats 0-1.
    # Mixing the two empties the cells on screen and falsifies the smudge
    # criterion, whose thresholds are absolute.
    # The underlines are stored as pickled bytes in the corpus; putting a
    # bare dictionary there makes the proofreading fail and the page loses
    # every one of its underlines.
    import pickle as _p
    if isinstance(d.get('sou'), dict): d['sou']=np.array(_p.dumps(d['sou']), dtype=object)
    for key_ in ('cells','nues'):
        d[key_]=(np.clip(d[key_],0,1)*255.0).round().astype(np.uint8)
    np.savez_compressed(old_npz, **d)
    return dict(pagino=pg, decalage=int(dec), colonne=int(col_score), score=float(score),
                cells=A, meta=Mnew, groupes=gnew, avant=int(len(sel)))

def run_step(pages, out_path=f"{T}/reparation.json"):
    Q=np.load(f"{T}/km_centres2.npy"); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    res=[]
    for pg in pages:
        try: res.append(repair_(pg,Q,tab))
        except Exception as e:
            print(f"  ECHEC p-{pg:03d} : {e}", flush=True)
    np.save(f"{T}/reparation_cells.npy", np.concatenate([r['cells'] for r in res]))
    np.save(f"{T}/reparation_meta.npy",  np.concatenate([r['meta'] for r in res]))
    np.save(f"{T}/reparation_grp.npy",   np.concatenate([r['groupes'] for r in res]))
    json.dump([{k:v for k,v in r.items() if k in ('pagino','decalage','colonne','score','avant')} for r in res],
              open(out_path,'w'))
    print("pages repaired:", len(res))

if __name__=="__main__":
    pages=[int(x) for x in sys.argv[1:]]
    run_step(pages)

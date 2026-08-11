# -*- coding: utf-8 -*-
"""Reparation chirurgicale des pages dont le masque de bord avait mange le haut.

Le masque des ombres de bord prenait une ligne de texte soulignee pour une
ombre et effacait tout jusqu'a elle : sur quarante-huit pages, jusqu'a six
lignes n'ont jamais ete decodees. Le masque est corrige, mais tout recalculer
detruirait le travail accumule — 5 800 corrections indexees par page, ligne et
colonne, et 3 495 groupes lus a l'oeil.

On repare donc page par page :
  1. on recoupe les cellules de la page avec le masque corrige ;
  2. on aligne l'ancienne page sur la nouvelle, par le contenu des lignes, ce
     qui donne le decalage de numerotation ;
  3. les cellules qui existaient deja gardent leur groupe — tout le travail
     de relecture reste valide ;
  4. les cellules nouvelles, celles des lignes retrouvees, sont rattachees au
     groupe dont le centre est le plus proche, dans l'espace de traits ou les
     groupes ont ete formes (fidelite mesuree : 99 %) ;
  5. les corrections de la page sont reindexees du meme decalage.
"""
import numpy as np, os, sys, json, difflib
sys.path.insert(0,'/root/dicionario/outils')
from traits2 import traits2
RAC="/root/dicionario"; T=f"{RAC}/travail"

def _texte(cells_occ, kl_page, cols, lignes, tab, bav):
    """Dictionnaire ligne -> chaine, une case par colonne."""
    d={}
    for (k,c),g,b in zip(cols, kl_page, bav):
        d.setdefault(int(k),{})[int(c)] = " " if b else str(tab[g])
    out={}
    for k,v in d.items():
        n=max(v)+1 if v else 0
        out[k]="".join(v.get(i," ") for i in range(n)).rstrip()
    return out

def _decalage(anc, neu, dmax=16):
    """Decalage d tel que la ligne k d'avant soit la ligne k+d de maintenant."""
    ka=sorted(anc); best=(-1.0, 0)
    for d in range(-4, dmax+1):
        s=0.0; n=0
        for k in ka:
            a=anc[k]; b=neu.get(k+d)
            if not a.strip() or b is None: continue
            s+=difflib.SequenceMatcher(None, a, b).ratio(); n+=1
        if n>=8 and s/n>best[0]: best=(s/n, d)
    return best[1], best[0]

def reparer(pg, Q, tab, verbeux=True):
    from cellules import extraire
    from decoder import bavures
    anc_npz=f"{T}/cellules/p-{pg:03d}.npz"
    z=np.load(anc_npz, allow_pickle=True)
    M=np.load(f"{T}/meta_all.npy"); kl=np.load(f"{T}/km_lab.npy")
    sel=np.where(M[:,0]==pg)[0]
    bv=bavures()[sel]
    anc_txt=_texte(None, kl[sel], M[sel][:,1:], z['lignes'], tab, bv)

    d=extraire(f"{RAC}/scan/p-{pg:03d}.jpg")
    occ=d['occ']; lg=np.array(d['lignes']); nues=d['nues']
    ii,jj=np.where(occ)
    A=(np.clip(nues[ii,jj],0,1)*255.0).round().astype(np.uint8)
    X=traits2(A); X=X/np.maximum(np.linalg.norm(X,axis=1,keepdims=True),1e-6)
    gnew=(X@Q.T).argmax(1).astype(np.int32)
    knew=lg[ii,0].astype(np.int32)
    Mnew=np.stack([np.full(len(ii),pg,np.int32), knew, jj.astype(np.int32)],1)
    # bavures des nouvelles cellules : meme critere geometrique
    P=A.astype(np.float32)/255.
    tot=P.sum((1,2))
    bord=(P[:,:,:2].sum((1,2))+P[:,:,-2:].sum((1,2)))/(tot+1e-6)
    haut=P[:,:4,:].sum((1,2))/(tot+1e-6); bas=P[:,18:,:].sum((1,2))/(tot+1e-6)
    bnew=((bord>0.55)|((tot<12)&(bord>0.25))|(haut>0.80)|(bas>0.85))
    neu_txt=_texte(None, gnew, Mnew[:,1:], lg, tab, bnew)
    dec, score = _decalage(anc_txt, neu_txt)
    # Le bloc peut s'etendre a gauche : les colonnes se decalent d'autant.
    scol = int(z['col0']) - int(d['col0'])
    if verbeux:
        print(f"  p-{pg:03d} : {len(anc_txt)} lignes -> {len(neu_txt)} ; decalage {dec:+d} ligne, {scol:+d} colonne ; concordance {score:.3f}")
    # les cellules deja connues gardent leur groupe
    cle_anc={(int(k)+dec, int(c)+scol): int(g) for (p,k,c),g in zip(M[sel], kl[sel])}
    garde=0
    for i in range(len(gnew)):
        v=cle_anc.get((int(Mnew[i,1]), int(Mnew[i,2])))
        if v is not None: gnew[i]=v; garde+=1
    if verbeux:
        print(f"           cellules : {len(sel)} avant, {len(gnew)} apres ; {garde} conservees, {len(gnew)-garde} nouvelles")
    # Le corpus est en octets 0-255 ; extraire() rend des flottants 0-1.
    # Melanger les deux vide les cellules a l'affichage et fausse le critere
    # de bavure, qui a des seuils absolus.
    # Les soulignements sont stockes en octets picklees dans le corpus ;
    # y mettre un dictionnaire brut fait echouer la relecture et la page
    # perd tous ses soulignements.
    import pickle as _p
    if isinstance(d.get('sou'), dict): d['sou']=np.array(_p.dumps(d['sou']), dtype=object)
    for cle in ('cells','nues'):
        d[cle]=(np.clip(d[cle],0,1)*255.0).round().astype(np.uint8)
    np.savez_compressed(anc_npz, **d)
    return dict(pagino=pg, decalage=int(dec), colonne=int(scol), score=float(score),
                cells=A, meta=Mnew, groupes=gnew, avant=int(len(sel)))

def executer(pages, sortie=f"{T}/reparation.json"):
    Q=np.load(f"{T}/km_centres2.npy"); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    res=[]
    for pg in pages:
        try: res.append(reparer(pg,Q,tab))
        except Exception as e:
            print(f"  ECHEC p-{pg:03d} : {e}", flush=True)
    np.save(f"{T}/reparation_cells.npy", np.concatenate([r['cells'] for r in res]))
    np.save(f"{T}/reparation_meta.npy",  np.concatenate([r['meta'] for r in res]))
    np.save(f"{T}/reparation_grp.npy",   np.concatenate([r['groupes'] for r in res]))
    json.dump([{k:v for k,v in r.items() if k in ('pagino','decalage','colonne','score','avant')} for r in res],
              open(sortie,'w'))
    print("pages reparees :", len(res))

if __name__=="__main__":
    pages=[int(x) for x in sys.argv[1:]]
    executer(pages)

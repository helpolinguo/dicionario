"""Analyse structurelle du dictionnaire decode.

Le tapuscrit suit une grammaire stricte, et c'est elle qui permet de mesurer la
qualite du decodage sans transcription temoin : une entree commence par une
vedette soulignee en colonne 0, ses lignes de suite sont en retrait de trois,
elle porte souvent une categorie entre parentheses soulignee, elle se decoupe en
sens numerotes en chiffres romains, et elle se termine par un code de langues
(sous-ensemble de D E F I R S L).
"""
import numpy as np, pickle, re, collections, sys
sys.path.insert(0,'/root/dicionario/outils')
from consolider import vedettes
T="/root/dicionario/travail"
CODES=re.compile(r'-\s*([DEFIRSL]{1,7})[.,]?\s*$')
FINALES=("o","a","e","i","ar","ir","or","um","e")

def texte_livre():
    from decoder import charger, page_texte
    from generer import exceptions
    lab,M=charger(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True); exc=exceptions()
    pages={}
    for pg in range(int(M[:,0].max())+1):
        try: lignes=page_texte(pg,lab,M,tab)
        except Exception: continue
        out=[]
        for k,s in lignes:
            l=list(s)
            for (pp,kk,cc),v in exc.items():
                if pp==pg and kk==k:
                    if cc>=len(l): l.extend(" "*(cc-len(l)+1))
                    l[cc]=v
            out.append((k,"".join(l).rstrip()))
        pages[pg]=out
    return pages

def entrees(pages):
    ent=[]
    for pg in sorted(pages):
        try: ved={k for k,_ in vedettes(pg)}
        except Exception: ved=set()
        cur=None
        for k,s in pages[pg]:
            if k in ved and s.strip():
                if cur: ent.append(cur)
                cur=dict(page=pg, ligne=k, lignes=[s])
            elif cur is not None and s.strip():
                cur['lignes'].append(s)
        if cur: ent.append(cur); cur=None
    for e in ent:
        t=" ".join(x.strip() for x in e['lignes'])
        e['texte']=t
        m=re.match(r'^([A-Za-z"\'-]+)', t)
        e['vedette']=m.group(1).rstrip('.') if m else ""
        e['code']=CODES.search(t)
    return ent
if __name__=="__main__":
    pages=texte_livre()
    ent=entrees(pages)
    print(f"{len(ent)} entrees reperees sur {len(pages)} pages")
    avec=sum(1 for e in ent if e['code'])
    print(f"  code de langues final reconnu : {avec} ({100*avec/len(ent):.1f} %)")
    bonne=sum(1 for e in ent if e['vedette'] and e['vedette'][-1] in "oaeir")
    print(f"  vedette a finale morphologique valide : {bonne} ({100*bonne/len(ent):.1f} %)")
    v=[e['vedette'].lower() for e in ent if e['vedette']]
    ruptures=sum(1 for a,b in zip(v,v[1:]) if a>b)
    print(f"  ruptures de l'ordre alphabetique : {ruptures} ({100*ruptures/max(len(v)-1,1):.1f} %)")
    for e in ent: e['code']=e['code'].group(1) if e['code'] else None
    pickle.dump(ent, open(f"{T}/entrees.pkl","wb"))

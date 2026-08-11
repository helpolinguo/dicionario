# -*- coding: utf-8 -*-
"""Extraction d'une base lexicale structuree a partir du tapuscrit decode.

Le tapuscrit suit une grammaire stricte, qui se lit dans la mise en page :

    vedetto. (fako.) Senco unesma. - II. Senco duesma. - L. nomo latina. - DEFIS.
    ^^^^^^^  ^^^^^^                    ^^^                ^^^^^^^^^^^^^   ^^^^^
    soulignee, colonne 0                sens               nomo cientifika  lingui

Chaque enregistrement porte sa **provenance** — image du scan, page du livre,
ligne de la grille — et ses **drapeaux de qualite**. Rien n'est efface : ce qui
est douteux est signale, pas masque.
"""
import numpy as np, os, pickle, re, collections, sys, json, os
sys.path.insert(0,'/root/dicionario/outils')
from consolider import vedettes
T="/root/dicionario/travail"
DECALAGE_FOLIO = 7          # numero de page du livre = index d'image - 7

LANGUI = {'D':'germana','E':'angla','F':'franca','I':'italiana','R':'rusa',
          'S':'hispana','L':'latina','P':'portugalana'}
RE_CODE   = re.compile(r'[-–]\s*([DEFIRSLP]{1,8})\s*[.,]?\s*$')
RE_FAKO   = re.compile(r'^\(([^)]{1,40})\)\s*')
RE_LATINA = re.compile(r'[-–]\s*L\.\s*([A-Za-z][A-Za-z\s.-]{2,60}?)\s*(?=[-–]|$)')
RE_SENCO  = re.compile(r'\s*[-–]\s*(?=(?:I{1,3}|IV|V|VI)\.\s)')
FINALES_OK = ("o","a","e","i","ar","ir","or")

def charger_texte():
    from decoder import charger, page_texte
    from generer import exceptions
    lab,M=charger(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True); exc=exceptions()
    corrigees=set((p,k,c) for (p,k,c) in exc)
    pages={}
    for pg in range(int(M[:,0].max())+1):
        try: lignes=page_texte(pg,lab,M,tab)
        except Exception: continue
        out=[]
        for k,s in lignes:
            l=list(s)
            # Une correction peut allonger la ligne : une vedette relue peut
            # compter plus de cellules que la lecture automatique. On complete
            # la ligne au lieu de laisser tomber la correction.
            for (pp,kk,cc),v in exc.items():
                if pp==pg and kk==k:
                    if cc>=len(l): l.extend(" "*(cc-len(l)+1))
                    l[cc]=v
            out.append((k,"".join(l).rstrip()))
        pages[pg]=out
    return pages, corrigees


_ND=None
def _non_dactylo():
    """Pages qui ne sont pas dactylographiees : couverture, pages blanches."""
    global _ND
    if _ND is None:
        _ND=set(); p=f"{T}/pages_non_dactylo.txt"
        if os.path.exists(p):
            for l in open(p,encoding='utf-8'):
                if l.startswith('#') or not l.strip(): continue
                _ND.add(int(l.split('\t')[0]))
    return _ND

def decouper(pages, corrigees):
    ent=[]
    for pg in sorted(pages):
        if pg < 8: continue          # liminaires : titre, preface, rezumo di gramatiko
        if pg in _non_dactylo(): continue   # pages blanches : rien a decouper
        try: ved={k for k,_ in vedettes(pg)}
        except Exception: ved=set()
        cur=None
        for k,s in pages[pg]:
            if not s.strip(): continue
            if k in ved:
                if cur: ent.append(cur)
                cur=dict(image=pg, pagino=pg-DECALAGE_FOLIO, ligno=k, lineoj=[(k,s)])
            elif cur is not None:
                cur['lineoj'].append((k,s))
        if cur: ent.append(cur)
    for e in ent:
        e['korektita'] = sum(1 for (k,_) in e['lineoj']
                             for c in range(120) if (e['image'],k,c) in corrigees)
    return ent

def analizar(e):
    t=" ".join(s.strip() for _,s in e['lineoj'])
    t=re.sub(r'\s+',' ',t).strip()
    e['teksto']=t
    m=re.match(r'^(-?[A-Za-z][A-Za-z"’\'-]*)\s*\.?', t)
    e['vedetto']= m.group(1).strip('.') if m else ""
    resto = t[m.end():].strip() if m else t
    mc=RE_CODE.search(resto)
    e['lingui']= [LANGUI.get(c,c) for c in mc.group(1)] if mc else []
    e['kodo']  = mc.group(1) if mc else None
    if mc: resto = resto[:mc.start()].rstrip(' -–')
    mf=RE_FAKO.match(resto)
    e['fako']= mf.group(1).rstrip('.') if mf else None
    if mf: resto = resto[mf.end():]
    e['latina']= [x.strip(' .') for x in RE_LATINA.findall(resto)]
    resto = RE_LATINA.sub('', resto).strip(' -–')
    senci=[s.strip(' -–') for s in RE_SENCO.split(resto) if s.strip(' -–')]
    e['senci']= senci if senci else ([resto] if resto else [])
    v=e['vedetto']
    e['drapeli']=[]
    if not v: e['drapeli'].append('sen-chefvorto')
    elif not any(v.lower().endswith(f) for f in FINALES_OK): e['drapeli'].append('finalo-nekustumala')
    if not e['kodo']: e['drapeli'].append('sen-lingui')
    if e['korektita']: e['drapeli'].append('korektita')
    if e['image'] in (546,547): e['drapeli'].append('pagino-nefidinda')
    return e

def konstrui():
    pages,corr = charger_texte()
    ent=[analizar(e) for e in decouper(pages,corr)]
    v=[e['vedetto'].lower() for e in ent]
    for i in range(1,len(v)):
        if v[i] and v[i-1] and v[i] < v[i-1]:
            ent[i]['drapeli'].append('ordino-rompita')
    return ent

if __name__=="__main__":
    ent=konstrui()
    os.makedirs(f"{T}/edicioni", exist_ok=True)
    with open(f"{T}/edicioni/dicionario.jsonl","w",encoding='utf-8') as f:
        for e in ent:
            f.write(json.dumps({k:v for k,v in e.items() if k!='lineoj'}, ensure_ascii=False)+"\n")
    print(f"{len(ent)} enregistrements")
    c=collections.Counter(d for e in ent for d in e['drapeli'])
    print("drapeaux :", c.most_common())
    print("sans aucun drapeau :", sum(1 for e in ent if not e['drapeli']))
    print("avec fako :", sum(1 for e in ent if e['fako']),
          "| avec nom latin :", sum(1 for e in ent if e['latina']),
          "| plusieurs sens :", sum(1 for e in ent if len(e['senci'])>1))

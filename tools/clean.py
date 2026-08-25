# -*- coding: utf-8 -*-
"""Nettoyage lexical de l'edition de lecture — par les RACINES du livre.

Le fac-simile garde la moindre coquille : c'est sa raison d'etre. L'edition
HTML doit donner le contenu de l'oeuvre, non ses accidents de frappe.

PREMIERE VERSION, ECARTEE. Elle corrigeait toute forme rare vers une forme
frequente obtenue par echange de deux caracteres que la machine confond. Sur
537 formes, elle rendait « papuli » (papules, dans « erupto di papuli ») par
« populi » (peuples), « por-tar » par « por-par », et remplacait la vedette
« agapo » par « agato » — deux mots reels, l'un chassant l'autre. La frequence
brute ignore le sens, et surtout la morphologie : en ido la finale porte la
nature du mot, -o nom, -a adjectif, -e adverbe, -ar verbe. La changer n'est
jamais une correction typographique.

VERSION RETENUE. L'ido est une langue a posteriori : ses racines sont
internationales, donc elles REVIENNENT dans le livre. Le dictionnaire est ainsi
son propre lexique. On ne corrige un mot d'une definition que si :

  1. sa racine n'existe NULLE PART comme vedette du livre — le mot ne fait
     donc pas sens en ido ;
  2. un seul echange de sosies suffit a en faire une racine attestee ;
  3. l'echange ne touche pas la finale grammaticale.

Les vedettes ne sont jamais touchees : une vedette est un article, pas une
occurrence. Le doute profite toujours a l'original.

VERSION RETENUE, NON APPLIQUEE. Elle aussi echoue, et pour une raison de fond.
Sur 116 propositions elle rend « falko » par « talko », « anglo » par « unglo »,
« adoptas » par « adaptas », « feko » par « foko » : tous des mots ido
parfaitement reels, qui ne sont simplement pas VEDETTES de ce dictionnaire.
Un dictionnaire de 10 000 racines n'est pas la liste de tous les mots de la
langue : ses definitions emploient des derives, des noms propres, des formes
latines. Son lexique interne ne peut donc pas servir d'arbitre.

Conclusion, verifiee deux fois par deux methodes : aucune passe automatique ne
distingue ici une coquille d'un mot legitime. Il y faut un lexique ido
authentique, ou une lecture en contexte. Cet outil reste en mode PROPOSITION :
il donne une liste a examiner, il ne modifie rien.
"""
import json, re, sys, collections
sys.path.insert(0,'/root/dicionario/outils')
from pairs import PAIRES
T="/root/dicionario/travail"

SOSIE=collections.defaultdict(set)
for a,b in PAIRES:
    if len(a)==1 and len(b)==1: SOSIE[a].add(b); SOSIE[b].add(a)
MOT=re.compile(r"[A-Za-zÀ-ÿ]{4,}")
FINALES=("ar","ir","or","as","is","os","us","o","a","e","i")
# Mots grammaticaux : ils n'ont pas de racine-vedette et ne doivent rien subir.
GRAM=set("""la le lo li ed od ma nam kad ka ke ke qua quo qui quan quin kande ube
pro por per pri sen sub sur tra trans ye da de di del dil en inter kun dum kontre
ante dop apud avan cirkum til vers nur anke tam tante quale quante on onu ol olu
il ilu el elu lu li ni vi me tu su ta ti ica ita ca co to omna ula nula multa poka
plu min maxim tre ne yes se do lore nun hike ibe kad esas esis esos esez havas
kom kad e a an al ek for pos segun malgre exter extere intre""".split())

def racines(ent):
    r=set()
    for e in ent:
        v=(e.get('vedetto') or "").lower().lstrip("*+-").rstrip("-")
        if not v: continue
        r.add(v)
        for f in FINALES:
            if v.endswith(f) and len(v)-len(f)>=2: r.add(v[:-len(f)]); break
    return r

def _racine(w):
    for f in FINALES:
        if w.endswith(f) and len(w)-len(f)>=2: return w[:-len(f)]
    return w

def connu(w, rac):
    w=w.lower()
    return w in rac or _racine(w) in rac or w in GRAM

def variantes(w):
    """Echanges de sosies, jamais sur la finale grammaticale."""
    n=len(w); fin=len(w)-len(_racine(w))
    for i,c in enumerate(w):
        if i >= n-max(fin,1): break
        for d in SOSIE.get(c,()):
            yield w[:i]+d+w[i+1:]

def proposer(ent):
    rac=racines(ent)
    freq=collections.Counter()
    for e in ent:
        for t in (e.get('senci') or []):
            for w in MOT.findall(t): freq[w.lower()]+=1
    prop={}
    for w,n in freq.items():
        if connu(w, rac): continue
        cands=[v for v in set(variantes(w)) if connu(v, rac) and freq.get(v,0)+1>n]
        if len(cands)==1: prop[w]=cands[0]
    return prop, rac

if __name__=="__main__":
    ent=[json.loads(l) for l in open(f"{T}/edicioni/dicionario.jsonl",encoding='utf-8')]
    prop,rac=proposer(ent)
    print("racines connues : %d ; corrections proposees : %d"%(len(rac),len(prop)))
    for w,v in sorted(prop.items())[:40]: print("   %-22s -> %s"%(w,v))

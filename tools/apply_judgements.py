# -*- coding: utf-8 -*-
"""Application des jugements lexicaux a l'edition de lecture.

Chaque correction est validee contre la fiche d'origine, puis appliquee au
seul texte des definitions — jamais aux vedettes. Tout est journalise.

La plupart des corrections rendues sont des CESURES mal recollees :
« re-cevar », « pro-duktita », « kom-batis », « fa-cile ». Le recollement
automatique les avait ratees parce que son garde-fou gardait le trait quand le
fragment de gauche etait lui-meme une racine attestee — or « re », « pro »,
« kom », « des », « mi » sont justement des prefixes. Le remede est donc pose
ici : quand la forme corrigee se termine par la forme lue, on efface le trait
et l'on recolle, au lieu de remplacer un mot par un autre.
"""
import json, re, sys, collections
T="/root/dicionario/travail"

def executer(rep=f"{T}/juger/reponses/r.txt", fic=f"{T}/juger/fiches.json"):
    fiches={x['id']:x for x in json.load(open(fic))}
    corr=[]
    for l in open(rep,encoding='utf-8'):
        i,_,v=l.rstrip("\n").partition("\t")
        if not v.strip() or not i.strip().isdigit(): continue
        x=fiches.get(int(i))
        if x is None: continue
        corr.append((x['mot'], v.strip()))
    ent=[json.loads(l) for l in open(f"{T}/edicioni/dicionario.jsonl",encoding='utf-8')]
    journal=[]
    for mot, bon in corr:
        # cesure : « pro-duktita » -> « produktita »
        if bon.lower().endswith(mot.lower()) and len(bon)>len(mot):
            tete=bon[:len(bon)-len(mot)]
            motif=re.compile(r'\b'+re.escape(tete)+r'[-\s]+'+re.escape(mot)+r'\b', re.I)
        else:
            motif=re.compile(r'\b'+re.escape(mot)+r'\b', re.I)
        for e in ent:
            s=e.get('senci') or []
            for k,t in enumerate(s):
                nt,n=motif.subn(bon, t)
                if n: journal.append((e['image'],e['ligno'],mot,bon)); s[k]=nt
    with open(f"{T}/edicioni/dicionario.jsonl","w",encoding='utf-8') as f:
        for e in ent: f.write(json.dumps(e,ensure_ascii=False)+"\n")
    with open(f"{T}/jugements.txt","w",encoding='utf-8') as f:
        f.write("# image\tligne\tforme lue\tforme retenue\n")
        for x in journal: f.write("%s\t%s\t%s\t%s\n"%x)
    print("corrections retenues : %d ; occurrences remplacees : %d"%(len(corr),len(journal)))
    return journal

if __name__=="__main__": executer()

# -*- coding: utf-8 -*-
"""Convertit les lignes relues en corrections cellule par cellule.

Le relecteur rend des lignes de meme longueur que celles qu'il a recues : la
comparaison se fait donc colonne par colonne, sans alignement ni ambiguite.
Une ligne rendue d'une autre longueur est refusee et signalee — mieux vaut
perdre une correction que decaler une ligne.
"""
import os, sys, glob, json
T="/root/dicionario/travail"

def executer(sortie=f"{T}/exceptions_relecture.txt"):
    # On compare la ligne rendue a la ligne SOUMISE, telle qu'elle figure dans
    # la planche — et non a un decodage recalcule, qui inclurait deja les
    # corrections et se mordrait la queue.
    cor=[]; refus=[]; nlig=0; npage=0
    for f in sorted(glob.glob(f"{T}/relecture/rez/p*.txt")):
        pg=int(os.path.basename(f)[1:4]); npage+=1
        soumis=f"{T}/relecture/p{pg:03d}.txt"
        if not os.path.exists(soumis): refus.append((pg,-1,"planche absente")); continue
        npage_ok=True; cur={}
        for l in open(soumis, encoding='utf-8'):
            l=l.rstrip("\n")
            if l.startswith("==") or "|" not in l: continue
            k,t=l.split("|",1)
            try: cur[int(k)]=t
            except ValueError: pass
        for l in open(f, encoding='utf-8'):
            l=l.rstrip("\n")
            # La section « DOUTEUX » emploie le meme format : tout ce qui suit
            # un croisillon en debut de ligne est du commentaire, pas du texte.
            if l.startswith("#"): break
            if "|" not in l: continue
            k,s=l.split("|",1)
            try: k=int(k)
            except ValueError: continue
            a=cur.get(k)
            if a is None: refus.append((pg,k,"ligne inconnue")); continue
            if len(s)!=len(a):
                refus.append((pg,k,f"longueur {len(a)} -> {len(s)}")); continue
            nlig+=1
            # On ecrit la ligne relue EN ENTIER, y compris les cases que le
            # relecteur a laissees telles quelles. Sinon ces cases retombent
            # sur le decodage courant, qui a pu changer depuis que la planche
            # a ete tiree — c'est ainsi que « EXPRESO » etait redevenu
            # « EEPRESO » apres coup.
            for c,y in enumerate(s):
                cor.append((pg,k,c,y))
    with open(sortie,"w",encoding='utf-8') as fo:
        fo.write("# Relecture directe : l'image du scan lue contre le texte decode.\n")
        fo.write("# Une case, un caractere ; les lignes relues ont la meme longueur que\n")
        fo.write("# celles qui ont ete soumises, donc la comparaison est exacte.\n")
        for pg,k,c,v in cor:
            fo.write(f"{pg}\t{k}\t{c}\t{v if v!=' ' else ' '}\n")
    print(f"pages relues : {npage} ; lignes appliquees : {nlig} ; cellules corrigees : {len(cor)}")
    if refus:
        print(f"lignes refusees : {len(refus)}")
        for r in refus[:10]: print("   ", r)
    return len(cor)

if __name__=="__main__": executer()

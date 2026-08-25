# -*- coding: utf-8 -*-
"""Taux d'exactitude mesure sur les pages transcrites a la main.

On compare caractere par caractere, cellule par cellule, la transcription
automatique et la transcription de reference. Les pages de test n'ont jamais
servi a l'apprentissage.
"""
import numpy as np, sys, os
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"

def reference(chemin):
    ref={}
    for l in open(chemin, encoding='utf-8'):
        l=l.rstrip("\n")
        if not l or "\t" not in l: continue
        k,s=l.split("\t",1)
        try: ref[int(k)]=s
        except ValueError: pass
    return ref

def mesurer(pg, chemin, avec_exceptions=True):
    from decode import charger, page_texte
    lab,M=charger(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    lignes=dict(page_texte(pg,lab,M,tab))
    if avec_exceptions:
        from generate import exceptions
        for (pp,kk,cc),v in exceptions().items():
            if pp!=pg or kk not in lignes: continue
            l=list(lignes[kk])
            if cc>=len(l): l.extend(" "*(cc-len(l)+1))
            l[cc]=v; lignes[kk]="".join(l)
    ref=reference(chemin)
    bon=tot=0; fautes=[]
    for k,s in ref.items():
        d=lignes.get(k,"")
        n=max(len(s),len(d))
        for i in range(n):
            a=s[i] if i<len(s) else " "
            b=d[i] if i<len(d) else " "
            tot+=1
            if a==b: bon+=1
            elif a!=" " or b!=" ": fautes.append((k,i,a,b))
    return bon, tot, fautes

if __name__=="__main__":
    for pg,ch in [(560,f"{T}/amorce_test_p560.txt"), (450,f"{T}/amorce_test_p450.txt")]:
        if not os.path.exists(ch): continue
        b,t,f=mesurer(pg,ch)
        print(f"page image {pg} : {b}/{t} = {100*b/t:.2f} %   ({len(f)} ecarts)")
        for x in f[:25]: print("   ", x)

# -*- coding: utf-8 -*-
"""Soulignements releves a l'oeil : ils l'emportent sur la detection automatique.

La detection mesure un filet au pixel pres, mais elle estime la ligne de base
et s'y trompe parfois : sur la ligne d'« adjurar », elle a souligne « Sumnar »
et « nomo » au lieu de la vedette et de la mention de domaine. Le relecteur,
lui, voit la page. Ce qu'il releve remplace donc entierement les plages
detectees, pour les lignes qu'il a relevees.
"""
import os, sys, glob, json
T="/root/dicionario/travail"

def executer(sortie=f"{T}/sou_relus.txt"):
    lignes=0; segs=0; perdus=[]
    with open(sortie,"w",encoding='utf-8') as fo:
        fo.write("# page\tligne\tplages (a-b, inclusives, en colonnes)\n")
        fo.write("# Releve a l'oeil ; remplace la detection automatique pour ces lignes.\n")
        for f in sorted(glob.glob(f"{T}/relecture/rez/p*.sou")):
            pg=int(os.path.basename(f)[1:4])
            # texte de reference : la ligne corrigee si elle existe, sinon celle soumise
            soumis={}
            p=f"{T}/relecture/p{pg:03d}.txt"
            if os.path.exists(p):
                for l in open(p,encoding='utf-8'):
                    l=l.rstrip("\n")
                    if l.startswith("==") or "|" not in l: continue
                    k,t=l.split("|",1)
                    try: soumis[int(k)]=t
                    except ValueError: pass
            soumis_brut=dict(soumis)
            r=f"{T}/relecture/rez/p{pg:03d}.txt"
            if os.path.exists(r):
                for l in open(r,encoding='utf-8'):
                    l=l.rstrip("\n")
                    if l.startswith("#"): break
                    if "|" not in l: continue
                    k,t=l.split("|",1)
                    try:
                        k=int(k)
                        if k in soumis and len(t)==len(soumis[k]): soumis[k]=t
                    except ValueError: pass
            for l in open(f,encoding='utf-8'):
                l=l.rstrip("\n")
                if l.startswith("#") or "|" not in l: continue
                parts=l.split("|")
                try: k=int(parts[0])
                except ValueError: continue
                texte=soumis.get(k)
                if texte is None: perdus.append((pg,k,"ligne inconnue")); continue
                # Le releveur a pu lire la ligne AVANT correction, ou apres :
                # les deux versions ont la meme longueur, donc les memes
                # colonnes. On cherche le segment dans l'une puis dans l'autre.
                brut=soumis_brut.get(k, texte)
                pos=0; pl=[]
                for seg in parts[1:]:
                    if not seg: continue
                    i=texte.find(seg, pos)
                    if i<0: i=brut.find(seg, pos)
                    if i<0: i=texte.find(seg)
                    if i<0: i=brut.find(seg)
                    if i<0: perdus.append((pg,k,seg)); continue
                    pl.append((i, i+len(seg)-1)); pos=i+len(seg)
                if pl:
                    lignes+=1; segs+=len(pl)
                    fo.write(f"{pg}\t{k}\t"+",".join(f"{a}-{b}" for a,b in pl)+"\n")
    print(f"lignes soulignees relevees : {lignes} ; segments : {segs}")
    if perdus:
        print(f"segments introuvables dans la ligne : {len(perdus)}")
        for x in perdus[:8]: print("   ", x)

if __name__=="__main__": executer()

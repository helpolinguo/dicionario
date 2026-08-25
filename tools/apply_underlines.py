# -*- coding: utf-8 -*-
"""Underlines surveyed by eye: they prevail over the automatic detection.

The detection measures a rule to the pixel, but it estimates the baseline and
sometimes gets it wrong: on the line of « adjurar » it underlined « Sumnar »
and « nomo » instead of the headword and the domain label. The proofreader,
for his part, sees the page. What he surveys therefore replaces the detected
ranges entirely, for the lines he has surveyed.
"""
import os, sys, glob, json
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=_ROOT + "/work"

def run_step(out_path=f"{T}/sou_relus.txt"):
    lines=0; segs=0; lost=[]
    with open(out_path,"w",encoding='utf-8') as fo:
        fo.write("# page\tligne\tplages (a-b, inclusives, en colonnes)\n")
        fo.write("# Releve a l'oeil ; remplace la detection automatique pour ces lignes.\n")
        for f in sorted(glob.glob(f"{T}/relecture/rez/p*.sou")):
            pg=int(os.path.basename(f)[1:4])
            # reference text: the corrected line if it exists, otherwise the one submitted
            submitted={}
            p=f"{T}/relecture/p{pg:03d}.txt"
            if os.path.exists(p):
                for l in open(p,encoding='utf-8'):
                    l=l.rstrip("\n")
                    if l.startswith("==") or "|" not in l: continue
                    k,t=l.split("|",1)
                    try: submitted[int(k)]=t
                    except ValueError: pass
            soumis_brut=dict(submitted)
            r=f"{T}/relecture/rez/p{pg:03d}.txt"
            if os.path.exists(r):
                for l in open(r,encoding='utf-8'):
                    l=l.rstrip("\n")
                    if l.startswith("#"): break
                    if "|" not in l: continue
                    k,t=l.split("|",1)
                    try:
                        k=int(k)
                        if k in submitted and len(t)==len(submitted[k]): submitted[k]=t
                    except ValueError: pass
            for l in open(f,encoding='utf-8'):
                l=l.rstrip("\n")
                if l.startswith("#") or "|" not in l: continue
                parts=l.split("|")
                try: k=int(parts[0])
                except ValueError: continue
                texte=submitted.get(k)
                if texte is None: lost.append((pg,k,"ligne inconnue")); continue
                # The surveyor may have read the line BEFORE correction, or after:
                # both versions have the same length, hence the same columns. We
                # look for the segment in the one, then in the other.
                raw=soumis_brut.get(k, texte)
                pos=0; pl=[]
                for seg in parts[1:]:
                    if not seg: continue
                    i=texte.find(seg, pos)
                    if i<0: i=raw.find(seg, pos)
                    if i<0: i=texte.find(seg)
                    if i<0: i=raw.find(seg)
                    if i<0: lost.append((pg,k,seg)); continue
                    pl.append((i, i+len(seg)-1)); pos=i+len(seg)
                if pl:
                    lines+=1; segs+=len(pl)
                    fo.write(f"{pg}\t{k}\t"+",".join(f"{a}-{b}" for a,b in pl)+"\n")
    print(f"underlined lines surveyed: {lines} ; segments: {segs}")
    if lost:
        print(f"segments not found in the line: {len(lost)}")
        for x in lost[:8]: print("   ", x)

if __name__=="__main__": run_step()

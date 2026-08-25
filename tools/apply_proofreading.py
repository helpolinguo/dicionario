# -*- coding: utf-8 -*-
"""Converts the proofread lines into corrections, cell by cell.

The proofreader returns lines of the same length as those he received: the
comparison is therefore made column by column, with no alignment and no
ambiguity. A line returned at another length is refused and reported -- better
to lose a correction than to shift a line.
"""
import os, sys, glob, json
T="/root/dicionario/travail"

def run_step(out_path=f"{T}/exceptions_relecture.txt"):
    # We compare the returned line with the line SUBMITTED, as it appears in the
    # sheet -- and not with a recomputed decoding, which would already include
    # the corrections and would bite its own tail.
    cor=[]; refused=[]; nlig=0; npage=0
    for f in sorted(glob.glob(f"{T}/relecture/rez/p*.txt")):
        pg=int(os.path.basename(f)[1:4]); npage+=1
        submitted=f"{T}/relecture/p{pg:03d}.txt"
        if not os.path.exists(submitted): refused.append((pg,-1,"planche absente")); continue
        npage_ok=True; cur={}
        for l in open(submitted, encoding='utf-8'):
            l=l.rstrip("\n")
            if l.startswith("==") or "|" not in l: continue
            k,t=l.split("|",1)
            try: cur[int(k)]=t
            except ValueError: pass
        for l in open(f, encoding='utf-8'):
            l=l.rstrip("\n")
            # The « DOUTEUX » section uses the same format: everything after a
            # hash at the start of a line is comment, not text.
            if l.startswith("#"): break
            if "|" not in l: continue
            k,s=l.split("|",1)
            try: k=int(k)
            except ValueError: continue
            a=cur.get(k)
            if a is None: refused.append((pg,k,"ligne inconnue")); continue
            if len(s)!=len(a):
                refused.append((pg,k,f"longueur {len(a)} -> {len(s)}")); continue
            nlig+=1
            # We write the proofread line IN FULL, including the cells the
            # proofreader left as they stood. Otherwise those cells fall back on
            # the current decoding, which may have changed since the sheet was
            # drawn -- that is how « EXPRESO » had become « EEPRESO » again
            # after the fact.
            for c,y in enumerate(s):
                cor.append((pg,k,c,y))
    with open(out_path,"w",encoding='utf-8') as fo:
        fo.write("# Relecture directe : l'image du scan lue contre le texte decode.\n")
        fo.write("# Une case, un caractere ; les lignes relues ont la meme longueur que\n")
        fo.write("# celles qui ont ete soumises, donc la comparaison est exacte.\n")
        for pg,k,c,v in cor:
            fo.write(f"{pg}\t{k}\t{c}\t{v if v!=' ' else ' '}\n")
    print(f"pages relues : {npage} ; lignes appliquees : {nlig} ; cellules corrigees : {len(cor)}")
    if refused:
        print(f"lignes refusees : {len(refused)}")
        for r in refused[:10]: print("   ", r)
    return len(cor)

if __name__=="__main__": run_step()

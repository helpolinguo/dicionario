# -*- coding: utf-8 -*-
"""Sorting the line starts that were restored.

The forced widening by two columns also brings back the edge of the sheet:
shadows of the binding and grain then decode into runs of « m », of « " » or
of hyphens. The parting is simple -- a typist who begins a line one cell too
early does so by ONE cell and ONE character, and that character is a letter
(or the « + » of the unofficial headwords), never a row of quotation marks.

We therefore keep only one cell, in column -1, carrying a letter or a « + »,
and no more than two lines per page. All the rest is set aside and must be
verified by eye before being taken back.
"""
import pickle, sys
T="/root/dicionario/travail"

def filtrer(raw, maxlignes=2):
    out={}
    for pg,d in raw.items():
        kept={}
        for k,v in d.items():
            if set(v)!={-1}: continue
            ch=v[-1]
            if not (ch.isalpha() or ch=='+'): continue
            kept[k]={-1:ch}
        if kept and len(kept)<=maxlignes: out[pg]=kept
    return out

if __name__=="__main__":
    raw=pickle.load(open(f"{T}/debuts_brut.pkl","rb"))
    clean_=filtrer(raw)
    pickle.dump(clean_, open(f"{T}/debuts.pkl","wb"))
    print("pages kept: %d (out of %d)"%(len(clean_), len(raw)))
    for pg in sorted(clean_):
        print("   p%03d : %s"%(pg, sorted((k,v[-1]) for k,v in clean_[pg].items())))

# Verification by eye, sheet by sheet (work/debuts.png).
#
# The automatic sort does not suffice: three of the cells kept carried a
# HANDWRITTEN ANNOTATION -- pages 18, 29 and 52, in cursive -- and the rule has
# been constant from the start, notes by hand are ignored. Four others stayed
# doubtful on examination. We therefore keep only what was recognised as typing
# AND as completing a word.
RETENUS = {
    (63,2):'h', (86,3):'b', (114,42):'d', (133,43):'e', (141,41):'e',
    (351,33):'l', (456,31):'p', (474,50):'p', (474,53):'p',
    (533,16):'+', (570,1):'d', (570,2):'d', (573,29):'+',
    (576,5):'t', (638,9):'L',
}
ECARTES = {
    (18,5):"cursive", (29,12):"cursive", (52,30):"cursive",
    (236,48):"douteux", (457,57):"douteux", (577,0):"douteux", (621,3):"douteux",
    (621,6):"douteux",
}

def retenus():
    out={}
    for (pg,k),ch in RETENUS.items(): out.setdefault(pg,{})[k]={-1:ch}
    return out

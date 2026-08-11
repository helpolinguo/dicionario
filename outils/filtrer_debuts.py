# -*- coding: utf-8 -*-
"""Tri des debuts de ligne rendus.

L'elargissement force de deux colonnes ramene aussi le bord de la feuille :
ombres de reliure et grain se decodent alors en suites de « m », de « " » ou
de tirets. Le depart est simple — une dactylo qui commence une ligne une
cellule trop tot le fait d'UNE cellule et d'UN caractere, et ce caractere est
une lettre (ou le « + » des vedettes non officielles), jamais une rangee de
guillemets.

On ne garde donc qu'une cellule, en colonne -1, portant une lettre ou un
« + », et pas plus de deux lignes par page. Tout le reste est ecarte et doit
etre verifie a l'oeil avant d'etre repris.
"""
import pickle, sys
T="/root/dicionario/travail"

def filtrer(brut, maxlignes=2):
    out={}
    for pg,d in brut.items():
        garde={}
        for k,v in d.items():
            if set(v)!={-1}: continue
            ch=v[-1]
            if not (ch.isalpha() or ch=='+'): continue
            garde[k]={-1:ch}
        if garde and len(garde)<=maxlignes: out[pg]=garde
    return out

if __name__=="__main__":
    brut=pickle.load(open(f"{T}/debuts_brut.pkl","rb"))
    net=filtrer(brut)
    pickle.dump(net, open(f"{T}/debuts.pkl","wb"))
    print("pages retenues : %d (sur %d)"%(len(net), len(brut)))
    for pg in sorted(net):
        print("   p%03d : %s"%(pg, sorted((k,v[-1]) for k,v in net[pg].items())))

# Verification a l'oeil, planche par planche (travail/debuts.png).
#
# Le tri automatique ne suffit pas : trois des cellules retenues portaient une
# ANNOTATION MANUSCRITE — pages 18, 29 et 52, en cursive — et la consigne est
# constante depuis le debut, les notes a la main sont ignorees. Quatre autres
# restaient douteuses a l'examen. On ne garde donc que ce qui a ete reconnu
# comme frappe ET completant un mot.
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

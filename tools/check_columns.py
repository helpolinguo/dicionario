"""Controle n. 3 : chaque caractere tombe-t-il sur sa colonne de grille ?

pdftotext -bbox donne la boite d'encre du mot, pas l'origine de la cellule :
xMin = origine + approche gauche du premier glyphe. L'approche ne depend que
du caractere ; on la mesure sur le document lui-meme (mediane par caractere)
et on verifie que le reste est un entier de cellules.
"""
import subprocess, re, sys, numpy as np, collections

# L'indication cachee portee sur chaque page (voir preamble.tex) n'est pas de
# la frappe : elle est composee dans la police du document, hors grille, et
# invisible a l'impression. pdftotext la rend comme n'importe quel mot, et elle
# faisait echouer le controle sur 5 760 mots. On l'ecarte par sa position :
# elle est posee a 6 mm du bord superieur, tres au-dessus du bloc de texte,
# dont la marge de tete est de 11 mm.
HAUT_CACHE = 24.0        # points PostScript ; le bloc commence plus bas

def mesurer(pdf, pas_pouce=0.1, orig_mm=21.9):
    pas=pas_pouce*72; orig=orig_mm/25.4*72
    xml=subprocess.run(["pdftotext","-bbox","-q",pdf,"-"],capture_output=True,text=True).stdout
    U=collections.defaultdict(list); tout=[]
    for ipg,pg in enumerate(re.split(r'<page ',xml)[1:]):
        for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', pg):
            x=float(m.group(1)); t=m.group(5)
            if not t: continue
            if float(m.group(2)) < HAUT_CACHE: continue   # indication cachee
            u=(x-orig)/pas
            U[t[0]].append(u); tout.append((ipg+1,t,u))
    appr={c: float(np.median(np.array(v)-np.round(np.array(v)))) for c,v in U.items()}
    ec=[]; pires=[]
    for ipg,t,u in tout:
        e=abs((u-appr[t[0]])-round(u-appr[t[0]]))
        ec.append(e)
        if e>0.12: pires.append((ipg,t,round(u,3),round(e,3)))
    ec=np.array(ec)
    return dict(n=len(ec), max=float(ec.max()), moyen=float(ec.mean()),
                q99=float(np.percentile(ec,99)), nb_hors=len(pires), pires=pires[:20],
                approches={c:round(v,3) for c,v in sorted(appr.items())})
if __name__=="__main__":
    r=mesurer(sys.argv[1] if len(sys.argv)>1 else "/root/dicionario/main.pdf")
    print("mots controles : %d"%r['n'])
    print("ecart a la colonne entiere : moyen %.4f, 99e centile %.4f, max %.4f cellule"%(r['moyen'],r['q99'],r['max']))
    print("hors tolerance 0,12 cellule : %d"%r['nb_hors'])
    for p in r['pires']: print("   ",p)

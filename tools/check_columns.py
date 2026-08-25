"""Check no. 3: does each character fall on its column of the grid?

pdftotext -bbox gives the ink box of the word, not the origin of the cell:
xMin = origin + the left side bearing of the first glyph. The side bearing
depends only on the character; we measure it on the document itself (a median
per character) and check that what is left is a whole number of cells.
"""
import subprocess, re, sys, numpy as np, collections

# The hidden mark carried on every page (see preamble.tex) is not typing:
# it is set in the document's font, off the grid, and invisible in print.
# pdftotext returns it like any other word, and it made the check fail on
# 5,760 words. We set it aside by its position: it is laid 6 mm from the top
# edge, well above the block of text, whose head margin is 11 mm.
HAUT_CACHE = 24.0        # PostScript points; the block starts lower

def mesurer(pdf, pas_pouce=0.1, orig_mm=21.9):
    step=pas_pouce*72; orig=orig_mm/25.4*72
    xml=subprocess.run(["pdftotext","-bbox","-q",pdf,"-"],capture_output=True,text=True).stdout
    U=collections.defaultdict(list); everything=[]
    for ipg,pg in enumerate(re.split(r'<page ',xml)[1:]):
        for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', pg):
            x=float(m.group(1)); t=m.group(5)
            if not t: continue
            if float(m.group(2)) < HAUT_CACHE: continue   # hidden mark
            u=(x-orig)/step
            U[t[0]].append(u); everything.append((ipg+1,t,u))
    appr={c: float(np.median(np.array(v)-np.round(np.array(v)))) for c,v in U.items()}
    ec=[]; worst=[]
    for ipg,t,u in everything:
        e=abs((u-appr[t[0]])-round(u-appr[t[0]]))
        ec.append(e)
        if e>0.12: worst.append((ipg,t,round(u,3),round(e,3)))
    ec=np.array(ec)
    return dict(n=len(ec), max=float(ec.max()), moyen=float(ec.mean()),
                q99=float(np.percentile(ec,99)), nb_hors=len(worst), pires=worst[:20],
                approches={c:round(v,3) for c,v in sorted(appr.items())})
if __name__=="__main__":
    r=mesurer(sys.argv[1] if len(sys.argv)>1 else "/root/dicionario/main.pdf")
    print("words checked: %d"%r['n'])
    print("departure from the whole column: mean %.4f, 99th centile %.4f, max %.4f cell"%(r['moyen'],r['q99'],r['max']))
    print("hors tolerance 0,12 cellule : %d"%r['nb_hors'])
    for p in r['pires']: print("   ",p)

import sys, os, subprocess, numpy as np
sys.path.insert(0,'/root/dicionario/outils')
from PIL import Image
from cellules import extraire
LIGNES=["abcdefghijklmnopq","rstuvwxyzABCDEFGH","IJKLMNOPQRSTUVWXY",
        "Z0123456789.,;:!?","()-+=/'\"*_%&#$[]"]
GAB=r"""\documentclass{article}
\usepackage[paperwidth=139mm,paperheight=188mm,left=14.2mm,top=12mm,right=0mm,bottom=0mm,noheadfoot]{geometry}
\usepackage{fontspec}\pagestyle{empty}\parindent0pt
\newfontfamily\T{%(font)s}[%(opt)s]
\begin{document}\T\fontsize{%(taille).4fpt}{8.6248pt}\selectfont
\obeylines
a b c d e f g h i j k l m n o p q
r s t u v w x y z A B C D E F G H
I J K L M N O P Q R S T U V W X Y
Z 0 1 2 3 4 5 6 7 8 9 . , ; : ! ?
( ) - + = / \textquotesingle{} \textquotedbl{} * \_ \%% \& \# \$ [ ]
\end{document}"""
def gabarits(nom, font, opt, taille, rep="/root/dicionario/travail/polices"):
    os.makedirs(rep, exist_ok=True)
    tex=f"{rep}/{nom}.tex"
    open(tex,"w").write(GAB % dict(font=font,opt=opt,taille=taille))
    subprocess.run(["xelatex","-interaction=nonstopmode","-output-directory",rep,tex],
                   capture_output=True)
    subprocess.run(["pdftoppm","-r","150","-gray","-png",f"{rep}/{nom}.pdf",f"{rep}/{nom}"],capture_output=True)
    Image.open(f"{rep}/{nom}-1.png").convert("L").save(f"{rep}/{nom}.jpg", quality=95)
    d=extraire(f"{rep}/{nom}.jpg"); c=d['cells']
    T={}
    for i,s in enumerate(LIGNES):
        for j,ch in enumerate(s):
            if 2*j < c.shape[1]: T[ch]=(np.clip(c[i,2*j],0,1)*255).astype(np.uint8)
    return T, d

import numpy as np, sys, os, json
sys.path.insert(0,'/root/dicionario/outils')
RAC="/root/dicionario"; T=f"{RAC}/travail"
if __name__=="__main__":
    a,b=int(sys.argv[1]),int(sys.argv[2]); out=[]
    from cellules import extraire
    for pg in range(a,b):
        f=f"{T}/cellules/p-{pg:03d}.npz"
        if not os.path.exists(f): continue
        z=np.load(f, allow_pickle=True)
        occ=z['occ']; 
        # colonnes encrees sur 1 ou 2 lignes seulement, au bord du bloc actuel
        n1=(occ.sum(0)>=1); n3=(occ.sum(0)>=3)
        # une extension aurait lieu si la colonne 0 ou la derniere est encree
        # dans l'image d'origine : on le detecte par re-extraction, trop couteux.
        out.append((pg, int(z['col0']), occ.shape[1]))
    json.dump(out, open(f'{T}/diag_col_{a}.json','w'))

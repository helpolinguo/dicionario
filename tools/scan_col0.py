import numpy as np, sys, os, json
sys.path.insert(0,'/root/dicionario/outils')
from cells import extraire
T='/root/dicionario/travail'
a,b=int(sys.argv[1]),int(sys.argv[2]); out=[]
for pg in range(a,b):
    f=f"{T}/cellules/p-{pg:03d}.npz"
    if not os.path.exists(f): continue
    try:
        z=np.load(f, allow_pickle=True)
        d=extraire(f'/root/dicionario/scan/p-{pg:03d}.jpg')
        out.append(dict(pg=pg, anc=int(z['col0']), neu=int(d['col0'])))
    except Exception as e: print("ECHEC",pg,e, flush=True)
json.dump(out, open(f'{T}/col0_{a}.json','w'))
print(f"{a}-{b} : {sum(1 for r in out if r['anc']!=r['neu'])} pages changent")

import numpy as np, sys, os, json
sys.path.insert(0,'/root/dicionario/outils')
ROOT="/root/dicionario"; T=f"{ROOT}/travail"
if __name__=="__main__":
    a,b=int(sys.argv[1]),int(sys.argv[2]); out=[]
    from cells import extract
    for pg in range(a,b):
        f=f"{T}/cellules/p-{pg:03d}.npz"
        if not os.path.exists(f): continue
        z=np.load(f, allow_pickle=True)
        occ=z['occ']; 
        # columns inked on 1 or 2 lines only, at the edge of the current block
        n1=(occ.sum(0)>=1); n3=(occ.sum(0)>=3)
        # an extension would take place if column 0 or the last is inked
        # in the original image: we detect it by re-extraction, too costly.
        out.append((pg, int(z['col0']), occ.shape[1]))
    json.dump(out, open(f'{T}/diag_col_{a}.json','w'))

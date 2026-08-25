import sys,time,numpy as np; sys.path.insert(0,'/root/dicionario/outils')
from features import feature_vector
from sklearn.cluster import MiniBatchKMeans
T="/root/dicionario/travail"
C=np.load(f"{T}/cells_all.npy", mmap_mode='r'); N=len(C)
K=int(sys.argv[1]) if len(sys.argv)>1 else 1200
rng=np.random.default_rng(0); idx=np.sort(rng.choice(N,min(N,200000),replace=False))
t=time.time(); Xs=feature_vector(np.asarray(C[idx])); print("feature_vector %.0fs"%(time.time()-t),flush=True)
init=Xs[rng.choice(len(Xs),K,replace=False)]
km=MiniBatchKMeans(n_clusters=K,batch_size=4096,n_init=1,max_iter=400,init=init,random_state=0)
km.fit(Xs); print("fit %.0fs"%(time.time()-t),flush=True)
Cn=km.cluster_centers_.astype(np.float32); Cn/=np.maximum(np.linalg.norm(Cn,axis=1,keepdims=True),1e-6)
lab=np.empty(N,np.int32); sim=np.empty(N,np.float32)
CH=20000; KB=1500     # blocks of cells x blocks of centres: bounded memory
for a in range(0,N,CH):
    X=feature_vector(np.asarray(C[a:a+CH])); m=len(X)
    meil=np.full(m,-2.0,np.float32); arg=np.zeros(m,np.int32)
    for b in range(0,K,KB):
        s=X@Cn[b:b+KB].T
        j=s.argmax(1); v=s[np.arange(m),j]
        mieux=v>meil
        meil[mieux]=v[mieux]; arg[mieux]=j[mieux]+b
        del s,j,v
    lab[a:a+CH]=arg; sim[a:a+CH]=meil
    del X
    if a % 200000 == 0: print("aff",a,"%.0fs"%(time.time()-t), flush=True)
np.save(f"{T}/km_lab.npy",lab); np.save(f"{T}/km_sim.npy",sim); np.save(f"{T}/km_centres.npy",Cn)
moy=np.zeros((K,22,12),np.float32)
ordre=np.argsort(lab, kind='stable'); bornes=np.searchsorted(lab[ordre], np.arange(K+1))
for k in range(K):
    m=ordre[bornes[k]:bornes[k+1]]
    if not len(m): continue
    if len(m)>50: m=m[np.argsort(-sim[m])[:50]]
    moy[k]=np.asarray(C[np.sort(m)]).mean(0)
np.save(f"{T}/km_moy.npy",moy)
print("fini %.0fs"%(time.time()-t), np.median(sim), np.bincount(lab,minlength=K).min(),flush=True)

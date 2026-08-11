# -*- coding: utf-8 -*-
"""Propage l'extension du bloc a droite sur tout le livre.

Le bloc de texte etait cerne par les colonnes occupees sur au moins trois
lignes : les fins de ligne qu'une seule ligne atteint tombaient dehors —
« preciz », « apa », « anoni- ». L'extension a droite les recupere, et elle est
sans danger : elle n'ajoute des colonnes qu'apres les autres, sans deplacer
l'origine. La numerotation des colonnes ne bouge pas, donc aucune correction
deja faite n'est invalidee.
"""
import sys, json, numpy as np
sys.path.insert(0,'/root/dicionario/outils')
from reparer_pages import executer
T='/root/dicionario/travail'
a,b=int(sys.argv[1]), int(sys.argv[2])
import os
pgs=[p for p in range(a,b) if os.path.exists(f'{T}/cellules/p-{p:03d}.npz')
     and p not in (0,1,3,7,87,111,577)]
executer(pgs, sortie=f'{T}/reetendre_{a}.json')
os.rename(f'{T}/reparation_meta.npy', f'{T}/reetendre_meta_{a}.npy')
os.rename(f'{T}/reparation_grp.npy',  f'{T}/reetendre_grp_{a}.npy')
os.rename(f'{T}/reparation_cells.npy',f'{T}/reetendre_cells_{a}.npy')

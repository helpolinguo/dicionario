# Relecture d'un dictionnaire dactylographie

Tu relis mot a mot des pages du *Dicionario de la 10.000 radiki di la linguo
internaciona Ido* de Marcel Pesch (1964), tapuscrit a la machine a ecrire.
La langue est l'**ido** : orthographe latine sans diacritiques, digrammes
`ch`, `sh`, `qu`, lettres `c` `k` `x` `y` `z` employees, pas de `w` sauf noms
propres.

## Les fichiers, pour chaque page NNN

- texte decode par la machine : `/root/dicionario/travail/relecture/pNNN.txt`
- images du scan : `/root/dicionario/travail/relecture/pNNNb0.png`,
  `pNNNb1.png`, `pNNNb2.png` (meme dossier)

Le fichier texte est decoupe par bandes. Une ligne `== pNNNb0.png` annonce que
les lignes qui suivent figurent sur cette image. Chaque ligne est au format
`LLL|contenu`, ou `LLL` est le numero de ligne.

## La regle absolue : la longueur ne change pas

Le texte est tape sur une grille : une case, un caractere. Ta ligne corrigee
doit compter **exactement le meme nombre de caracteres** que la ligne donnee,
espaces de tete comprises.

- caractere mal lu -> tu le remplaces par le bon, a la meme place ;
- caractere manque par la machine -> il figure comme une **espace** : mets la
  lettre a la place de cette espace ;
- caractere invente par la machine -> remplace-le par une **espace**.

Ne realigne jamais, n'ajoute ni ne retire de caractere. S'il faudrait inserer
une lettre sans espace disponible, laisse la ligne telle quelle et signale-la.

## Comment lire

Lis le fichier texte de la page, puis **regarde chaque image** avec l'outil
Read et compare ligne a ligne. Une seule lecture par image suffit si tu la lis
attentivement. Les bandes se chevauchent de deux lignes.

- Le ruban est use : une lettre pale reste la lettre qui est la. **Transcris ce
  que tu vois, ne corrige pas l'orthographe de l'auteur.** Une faute de
  l'auteur est une donnee, pas une erreur.
- Confusions frequentes de ce decodeur : `c`/`e`/`o`, `i`/`l`/`1`, `n`/`u`,
  `r`/`v`, `b`/`h`, `s`/`z`/`8`, `g`/`q`, `m`/`rn`, `E`/`R`/`S`, `O`/`0`,
  `.`/`,`, et les capitales prises pour des minuscules.
- Ignore les soulignements : ils sont traites ailleurs. Ne t'occupe que des
  caracteres.
- Le folio en haut de page et les codes de langue en fin d'article
  (`- DEFIRS.`, `- L.`, `- EF.`) comptent comme du texte ordinaire.

## Ta reponse

Pour chaque page, ecris `/root/dicionario/travail/relecture/rez/pNNN.txt` au
format `LLL|ligne corrigee` — **uniquement les lignes que tu corriges**, dans
l'ordre. Puis, s'il y a lieu, une section finale `# DOUTEUX` decrivant en une
ligne chaque cas non traitable a longueur constante.

Ne renvoie ensuite qu'une seule ligne : pages traitees, lignes corrigees,
caracteres changes.

## Les notes manuscrites : a ignorer, toujours

L'exemplaire scanne porte ca et la des **annotations a la main** — un mot
ajoute dans la marge, une correction entre les lignes, un trait de crayon.
Elles ne font pas partie du livre imprime et ne doivent **jamais** etre
transcrites.

Si le decodeur a lu une annotation manuscrite, remplace ces cases par des
**espaces** (la longueur de la ligne ne change pas, comme toujours). Si une
ligne entiere n'est que manuscrite, rends-la entierement en espaces. Signale-le
en une ligne dans la section `# DOUTEUX`.

## Les soulignements : ne t'en occupe pas

Ils sont detectes automatiquement, et la detection a ete reglee sur 1 698
lignes relevees a l'oeil : elle place correctement 95,5 % des cellules
soulignees. Ce qui lui echappe encore, c'est une cellule en fin de filet — le
point d'une abreviation, une parenthese fermante — la ou le tapuscrit lui-meme
est irregulier. Le mesurer coute plus cher que cela ne vaut.

**Ne releve donc aucun soulignement, ne produis aucun fichier `.sou`.**
Occupe-toi uniquement des caracteres : c'est la que sont les vraies fautes, et
c'est la que ton oeil est irremplacable.

## Ne mesure pas, lis

Ce travail se fait a l'oeil, pas au pixel. **N'ecris pas de script** pour
redresser les bandes, reconstruire la grille, mesurer des filets ou verifier
la longueur de tes lignes. La longueur est verifiee par le programme qui
applique tes corrections, et toute ligne de longueur fausse est refusee et
signalee — tu n'as pas a t'en assurer toi-meme.

Une lecture attentive de chaque bande suffit. Si un caractere reste douteux
apres l'avoir regarde, laisse la ligne telle quelle et dis-le en `# DOUTEUX` :
un doute signale vaut mieux qu'une demi-heure de mesure.

# Dicionario de la 10.000 radiki di la linguo internaciona Ido
## Base lexicale et édition numérique — état du chantier

Marcelo Persiko (Marcel Pesch), *editio princeps*, 2 août 1964.
Transcription établie à partir du fac-similé fourni (639 pages photographiées).

---

## Ce que contient cette livraison

| fichier | ce que c'est |
|---|---|
| `dicionario.jsonl` | **la base** : un enregistrement JSON par entrée, un par ligne |
| `dicionario.tsv` | la même chose en tableur, pour qui n'écrit pas de code |
| `index.html` | l'**édition consultable**, un seul fichier, hors ligne, avec recherche |
| `dicionario.pdf` | le **dictionnaire de poche**, vers lequel pointe le bouton « Deskargar » |
| `dicionario-facsimile.pdf` | le fac-similé LaTeX, page à page, grille à grille |
| `journal_complet.txt` | **toutes** les corrections : ce qui a été lu, ce qui a été retenu, et si c'est un correcteur ou l'œil qui a tranché |
| `outils/` | la chaîne complète, de l'image au JSON |

**8 241 entrées** extraites de 632 pages de corps d'ouvrage.
4 302 portent une marque de domaine (*bot.*, *zool.*, *arkitekt.*…),
544 un nom scientifique latin, 1 271 plusieurs sens numérotés.

---

## Le champ d'un enregistrement

```json
{"vedetto":"cinocefalo", "fako":"zool",
 "senci":["Genero de simio, di qua la muzelo esas longa quale che la hundo."],
 "latina":["cynocephalus"], "lingui":["angla","franca","italiana","hispana"],
 "kodo":"EFIS", "pagino":92, "ligno":8, "image":99,
 "korektita":0, "drapeli":[]}
```

`pagino` est le numéro imprimé dans le livre ; `image` l'index dans le PDF
fourni ; `ligno` la ligne de la grille du tapuscrit. **Chaque entrée peut donc
être ramenée au fac-similé**, ligne par ligne. C'est la condition pour que ce
travail reste vérifiable dans vingt ans.

---

## Les drapeaux : la liste de travail

Le décodage est exact à **98,7 % par caractère**, mesuré sur une page transcrite
à la main et tenue hors de tout apprentissage. Ce n'est pas assez pour un
dictionnaire. Plutôt que de masquer ce qui reste, la base le **signale** :

| drapeau | entrées | ce qu'il veut dire |
|---|---|---|
| `sen-lingua` | 2 350 | pas de code de langues final — souvent normal, le livre n'en donne pas toujours |
| `ordino-rompita` | 1 688 | **la vedette rompt l'ordre alphabétique** |
| `korektita` | 1 674 | au moins une cellule corrigée automatiquement ; le journal la donne |
| `finalo-nekutima` | 224 | finale étrangère à la morphologie d'Ido (-o, -a, -e, -i, -ar, -ir, -or) |
| `sen-vedetto` | 114 | l'entrée n'a pas de vedette lisible |
| `pagino-nekonfidebla` | 19 | pages 538-539, photographiées à une autre échelle, décodage nettement moins sûr |

**3 746 entrées ne portent aucun drapeau.**

`ordino-rompita` est le plus utile des six. Un dictionnaire est trié : une
vedette qui rompt l'ordre désigne presque toujours une mauvaise lecture, dans
l'une des deux vedettes voisines — *aoendar* pour *acendar*, *a)rotano* pour
*abrotano*, *aacho* pour le suffixe *-acho*. **Corriger ces 1 688 cas, c'est
achever le livre**, et le travail est divisible : chacun peut en prendre cent.

L'édition HTML a une case à cocher qui ne montre que les entrées drapelées.

---

## Ce qui a été corrigé, et comment

Rien n'est corrigé en silence. **2 330 cellules** ont été redressées, chacune
journalisée avec la forme lue, la forme retenue et la raison :

- **le lexique du livre** (`journal_corrections.txt`) — 137 758 occurrences pour
  34 620 formes : une forme lue une fois, quand une variante obtenue en changeant
  une cellule *ambiguë* est attestée huit fois et huit fois plus souvent, est une
  faute de lecture. Ainsi `zobl.` → `zool.` : une occurrence contre 334 ;
- **la morphologie des vedettes** (`journal_vedettes.txt`) — la finale d'une
  vedette est `o`, `r`, `a`, `e` ou `i` ; la quatrième valeur observée, `c`,
  n'existe pas en Ido : c'est la confusion `c`/`o` ;
- **la section alphabétique de la page** — sur une page, les vedettes commencent
  par la même lettre ;
- **un modèle de caractères d'ordre 4**, en dernier recours, à un seuil réglé
  pour ne rien dégrader sur une page témoin ;
- **`exceptions_manuel.txt`** — les arbitrages faits à l'œil sur le fac-similé.
  Ce fichier l'emporte sur tous les correcteurs et n'est jamais réécrit.

Une cellule n'est déclarée ambiguë que si le décodage doute : son groupe doit
avoir, parmi ses plus proches voisins dans l'espace des formes, un groupe
d'étiquette différente. **Aucune cellule que le décodage lit sans hésiter n'a été
touchée.**

Une piste a été essayée puis abandonnée — corriger les vedettes par l'ordre
alphabétique global : sans contrainte de langue elle produit *adiar* → *adiao*.
Son journal est conservé sous `journal_vedettes_DP_ABANDONNE.txt`.

---

## Reprendre le travail

```
python3 outils/edition.py     # image decodee  -> enregistrements structures
python3 outils/exportar.py    # enregistrements -> JSONL, TSV, HTML
```

Pour corriger une lecture : ajouter une ligne
`page<TAB>ligne<TAB>colonne<TAB>caractère` à `travail/exceptions_manuel.txt`,
puis relancer les deux commandes. La correction se propage au fac-similé, à la
base et à l'édition.

Le fac-similé et l'édition sortent de la **même source** : les cellules décodées.
Le fac-similé reste la pièce à conviction ; l'édition est ce qui s'utilise.

---

## Avant diffusion

L'ouvrage date de 1964. Son statut juridique dépend de la date de mort de
l'auteur et du pays de diffusion : à vérifier auprès des ayants droit ou de
l'Uniono por la Linguo Internaciona avant toute mise en ligne publique. Ce
travail est une transcription, il n'affecte pas les droits sur l'œuvre.

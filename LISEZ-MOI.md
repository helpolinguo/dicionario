# Dicionario de la 10.000 radiki di la linguo internaciona Ido
## Transcription en LaTeX du tapuscrit de Marcelo Persiko (Marcel Pesch), 1964

Ce dépôt contient la transcription **fac-similaire** du *Dicionario de la 10.000
radiki di la linguo internaciona Ido*, editio princeps du 2 août 1964. L'original
n'est pas un imprimé typographique : c'est un tapuscrit à chasse fixe,
photoréduit pour l'impression. Il est donc traité ici comme une **grille de
caractères**, non comme du texte composé.

---

## 1. Mesures de la grille, et échelle du fac-similé

### Le PDF fourni n'est pas à la taille du livre

Toutes les mesures brutes ci-dessous sont exprimées à la définition nominale du
PDF (150 dpi). **Cette définition est fictive** : les pages ont été
photographiées, non numérisées à plat — leurs dimensions en pixels varient de
745 à 884 px pour un même feuillet.

| grandeur | médiane | q10 – q90 | écart-type |
|---|---|---|---|
| pas horizontal (chasse) | **10,562 px** | 10,53 – 10,60 | 0,075 |
| pas vertical (interligne) | **17,969 px** | 17,77 – 18,04 | 0,132 |
| inclinaison de la page | 0,00° | −1,75° – +2,75° | — |
| lignes de grille écrites par page | 41 | 38 – 45 | — |

L'échelle vraie se déduit d'un **invariant mécanique** : l'échappement d'une
machine à écrire. Une machine Pica avance d'exactement **un dixième de pouce**
par frappe — 2,540 mm. Le pas mesuré vaut 10,562 px / 150 dpi = 1,7885 mm, soit
**70,40 % de 2,540 mm**.

> **Le fac-similé du PDF est donc une réduction à 70,4 %. Tout est restauré ici
> à la taille de frappe d'origine** (facteur 1,4202).

### Anisotropie

Le rapport des deux pas vaut **1,7013** (q10 1,681 – q90 1,709). Six lignes au
pouce donneraient 5/3 = 1,6667 : l'écart est de **2,1 %**. Il est réel — le
lattis ajusté par moindres carrés sur 50 lignes ne laisse **aucun résidu**
(0,00 px) — et provient de la reproduction offset de 1964, qui n'a pas été
rigoureusement isotrope. Il est **conservé** : restaurer la taille n'autorise
pas à corriger la géométrie. L'interligne restauré vaut donc 4,321 mm et non
4,233 mm. Une seule constante (`\PasV`) permet de revenir à 6 lignes au pouce
exactes si vous le préférez.

### Le feuillet et les marges

Le cadrage des photographies varie de ±1 cm, mais **66 pages montrent les deux
marges latérales entières dans le cadre**. Sur ces 66 pages :

| | valeur |
|---|---|
| marge de gauche | **21,9 mm** |
| marge de droite | **21,3 mm** |
| bloc de texte (médiane) | 66 cellules = 167,6 mm |
| **total** | **210,8 mm** |

Les deux marges latérales sont **symétriques**, et leur somme avec le bloc de
texte donne **A4**. Vingt-trois pages montrent aussi les deux marges verticales :
la marge haute y vaut **14,3 mm**. Le feuillet original est donc un **A4
dactylographié à 10 caractères au pouce, reproduit tel quel** — la façon dont on
publiait un ouvrage de mouvement linguistique en 1964.

### Constantes retenues

| constante | valeur | origine |
|---|---|---|
| `\PasH` | 0,1 pouce = 2,540 mm | échappement Pica (invariant mécanique) |
| `\PasV` | 0,170128 pouce = 4,321 mm | rapport 1,7013 mesuré sur 639 pages |
| feuillet | A4, 210 × 297 mm | marges symétriques mesurées : 21,9 + 167,6 + 21,3 |
| `\OrigX` | 21,9 mm | marge gauche mesurée |
| `\OrigY` | 12,44 mm | place l'encre de la ligne 0 à 14,3 mm du bord |
| corps | 0,190476 pouce | = `\PasH` / 0,525 (avance d'UM Typewriter) |

**Vérification.** Après ce calage, la superposition de la page composée et du
scan redressé et remis à l'échelle donne un résidu de **0 px en vertical et
1 px en horizontal**, sur toute la hauteur de la page. Et le contrôle n° 3
(position en colonne de chaque caractère, extraite du PDF par `pdftotext -bbox`)
passe à **100 %** : écart maximal **0,0034 cellule** sur 1 630 mots.

**Deux exceptions.** Les pages 538 et 539 du livre (images 546 et 547 du PDF) ont
été photographiées à 1,47× des autres. Le programme détecte l'échelle sur la
hauteur de l'image et adapte la recherche du pas.

## 2. Méthode de décodage

Aucun OCR page par page. La chaîne est la suivante :

1. **Normalisation locale du contraste** — le fond est estimé par un filtre
   moyen de 41 px ; l'encre est l'écart négatif à ce fond. Cela absorbe le
   jaunissement du papier et les variations d'éclairage de la photographie.
2. **Masquage des bords** — les bandes sombres collées au bord de l'image
   (ombre du bord du papier, reliure) sont effacées, sinon elles créent une
   fausse colonne de texte.
3. **Désinclinaison** — maximisation de la variance de la dérivée du profil de
   projection horizontal, sur ±2,5° au pas de 0,05°.
4. **Lattis des lignes** — pas et phase par maximisation du module de Fourier du
   profil de projection, puis affinage par régression linéaire sur les
   barycentres des lignes réellement écrites (ce qui absorbe une éventuelle
   dérive verticale).
5. **Lattis des colonnes** — même principe, puis affinage de (pas, phase) par
   minimisation de l'encre tombant sur les frontières de cellule.
6. **Découpage** — chaque cellule est rééchantillonnée en une imagette de
   12 × 22 px par interpolation bilinéaire aux positions sous-pixel exactes.
   L'extension verticale de la cellule est de −0,545 à +0,50 pas, ce qui couvre
   les hampes et les jambages sans mordre sur le filet de soulignement de la
   ligne précédente.
7. **Regroupement** — les 1 05x xxx cellules encrées du livre sont recentrées
   (recalage borné à ±2 px, qui absorbe le tremblement de la frappe sans
   confondre `.` et `'`), légèrement floutées, normalisées, puis regroupées.
   La corrélation médiane d'une cellule à son groupe est de **0,982**.
8. **Étiquetage** — les groupes sont étiquetés à la main, une fois chacun, sur
   planches d'images moyennes. Une transcription manuelle vérifiée colonne par
   colonne sert d'amorce ; un classifieur entraîné sur cette amorce propage
   l'étiquetage, et les groupes incertains sont examinés un à un dans leur
   contexte (le programme `outils/contexte.py` affiche des occurrences d'un
   groupe dans leur ligne d'origine).
9. **Décodage** — chaque cellule reçoit le caractère de son groupe. La
   correspondance cellule → groupe est conservée : c'est la pièce
   justificative, et elle permet de rouvrir n'importe quelle décision.

---

## 3. Soulignements

Le soulignement de machine à écrire est un `_` frappé en seconde passe à une
hauteur constante sous la ligne de base. Il est détecté **séparément du
décodage**, comme une suite horizontale de pixels sombres, et converti en une
**plage de colonnes** (de la colonne *i* à la colonne *j* incluse).

Les cellules livrées au regroupement **conservent** leur soulignement : un `a`
souligné forme donc son propre groupe, distinct du `a` nu. C'est volontaire :
cela fournit un **contrôle croisé** du relevé des filets, indépendant de la
détection par plage.

---

## 4. Structure du dépôt

```
dicionario/
  main.tex               document maitre
  preambule.tex          grille, police, macros — une constante par reglage
  contenu/pNNN.tex       une page = une suite de \l{...}, une ligne de source
                         par ligne du livre, dans l'ordre de la grille
  ornements/             elements detoures du scan (couverture)
  outils/                decoupage, regroupement, decodage, verification
  travail/               fichiers intermediaires (cellules, groupes, releves)
  LISEZ-MOI.md
```

---

## 5. Table des macros

| macro | effet |
|---|---|
| `\l{...}` | une ligne de la grille ; position verticale imposée par `\PasV` |
| `\cel{n}` | n cellules vides (espaces de chasse exacte) |
| `\sou{...}` | souligné : **un filet**, largeur = celle du texte donc multiple exact de la chasse, profondeur et épaisseur mesurées dans le scan |
| `\sur{a}{b}` | surfrappe : deux caractères dans la même cellule (`\makebox[0pt][l]`) |
| `\barre{...}` | mot barré d'un trait continu |
| `\marge[x]{y}{...}` | texte hors grille, en coordonnées absolues |
| `\pg{...}` | une page complète |

`\sou` n'est **pas** `\underline` : c'est un filet, il se coupe proprement, son
épaisseur et sa profondeur sont celles du scan, et sa largeur est un multiple
exact de la chasse. `\sur` n'utilise **jamais** de caractère précomposé : c'est
ainsi que la machine produisait les lettres accentuées (`â`, `ê`, `î`, `ô` de
l'article *cirkonflexo*, page 92).

---

## 6. Ce qui reste à faire

*(section tenue à jour au fil des lots)*

### Les soulignements : trois defauts, trois causes

Le releve des filets etait tour a tour trop court et trop long. Trois causes
distinctes, corrigees separement :

1. **Le ruban saute.** Un filet se coupe sur une ou deux cellules sans cesser
   d'etre un filet ; le releve, qui exigeait une suite continue de 2,2 cellules,
   ne gardait que le plus long morceau — d'ou `\sou{cipri}no`. Les morceaux
   separes de moins d'une cellule sont recolles avant le filtre de longueur, et
   deux plages distantes de deux cellules ou moins sont fusionnees. Trois
   cellules d'ecart, elles, separent bien deux soulignements : *cinocefalo* et
   *(zool.)* sont a cette distance.
2. **Le releve arrondissait les extremites au juge.** Il calcule maintenant,
   cellule par cellule, la **fraction de la cellule reellement couverte** par le
   filet, et retient celles couvertes a 60 % ou plus. C'est une mesure, non plus
   un arrondi.
3. **Le filet debordait sur le mot suivant.** Un filet ne souligne pas une
   lettre isolee a son extremite : les groupes d'une ou deux cellules separes du
   corps de la plage par une espace sont retranches, et un filet isole d'une ou
   deux cellules est ecarte comme du bruit. Les espaces **interieures** sont
   conservees — le tapuscrit souligne bien *historio di Italia* d'un seul trait.

C'est le controle qui reste le plus faible des sept : le filet est mesure la ou
l'encre se trouve, et l'encre d'un tapuscrit de 1964 photoreduit n'est pas
toujours nette. Les vedettes et les abreviations entre parentheses sont
maintenant justes ; il subsiste des plages a une cellule pres sur les
soulignements internes au texte.

### Arbitrages a l'oeil

`travail/exceptions_manuel.txt` recueille les lectures tranchees a l'oeil sur le
fac-simile. **Ce fichier l'emporte sur tous les correcteurs automatiques et
n'est jamais reecrit par un programme** — la lecon d'une version ou mes
arbitrages avaient ete effaces par la passe suivante. Il contient a ce jour les
accents circonflexes de *cirkonflexo* (composes en surfrappe), `"cis"`,
*yulo*, *cypressus*, *cirko*, *giganto*, *antiqua*, *Qua*, *tempala* et le trait
d'union de *omna-direcione*.

### Les soulignements : recoller le filet use (version precedente)

Le releve des filets manquait la fin des mots — `\sou{cipri}no` au lieu de
`\sou{ciprino}`. La cause est le ruban : **un filet se coupe sur une ou deux
cellules sans cesser d'etre un filet**. Le releve exigeait une suite continue
d'au moins 2,2 cellules, et ne gardait donc que le plus long morceau.

Les morceaux separes de **moins d'une cellule** sont maintenant recolles avant
qu'on applique la longueur minimale, et la densite exigee sur la plage est
passee de 0,85 a 0,80. Les vedettes de la page 193 — *gibelino*, *gibono*,
*gicheto*, *gildo* — et leurs parentheses d'abreviation
*(historio di Italia)*, *(tekn.)*, *(muziko)* sont maintenant soulignees sur
toute leur longueur, ni plus ni moins.

### Deux regularites de plus, appliquees aux vedettes

- **La section alphabetique de la page.** Sur une page, les vedettes commencent
  par la meme lettre. Quand une initiale contredit la majorite de sa page **et
  que sa cellule est ambigue**, on retient la majorite : 161 initiales
  redressees, dont *sibelino* → *gibelino* et *sibono* → *gibono*.
- **La finale morphologique.** Sur 7 295 vedettes, la finale est `o` dans
  4 584 cas, `r` dans 1 527, `a` dans 613, `e` dans 52, `i` dans 31 — la
  morphologie d'Ido. La quatrieme valeur observee, `c` (269 cas), n'existe pas
  comme finale : c'est la confusion `c`/`o`. 336 finales redressees.

### Un modele de n-grammes, en dernier recours

Une vedette n'apparait souvent qu'une fois : aucune attestation ne peut la
departager. On lui applique alors un modele de caracteres d'ordre 4, appris sur
les formes du livre vues au moins trois fois, et on ne substitue que si l'ecart
de vraisemblance depasse **6 ordres de grandeur** — seuil regle en mesurant sur
une page tenue hors de tout apprentissage, jusqu'a ce que la correction cesse
de degrader quoi que ce soit. A 2 ordres de grandeur, le modele faisait plus de
mal que de bien (3 degradations pour 1 correction) ; a 6, il n'agit plus que sur
43 cellules, toutes flagrantes.

**Total : 2 010 cellules corrigees**, dont 9 arbitrees a l'oeil. Journaux :
`journal_corrections.txt` (lexique et n-grammes), `journal_vedettes.txt`
(section et finale), `journal_initiales.txt`.

### La correction des lectures douteuses par le lexique du livre

Sur consigne — *en cas de doute, transcrire la lettre correcte plutôt que
l'erreur* — le fac-similé applique maintenant une passe de correction fondée
sur le vocabulaire du livre lui-même.

**Une cellule n'est déclarée douteuse que si le décodage doute.** Le critère est
géométrique et vérifiable : le groupe auquel elle appartient a, parmi ses plus
proches voisins dans l'espace des formes, un groupe d'étiquette différente à une
corrélation supérieure à 0,86. Sur 12 000 groupes, 3 411 ont ainsi une
alternative ; les paires les plus fréquentes sont exactement celles qu'on attend
d'un tapuscrit à 150 dpi : `e/a`, `o/c`, `a/s`, `l/1`, `./,`, `l/i`, `b/h`.

**La règle de substitution.** Le livre compte 137 758 occurrences pour
34 620 formes distinctes : il répète son vocabulaire des milliers de fois. Une
forme lue **au plus deux fois**, alors qu'une variante obtenue en remplaçant une
cellule douteuse est attestée **au moins huit fois et huit fois plus souvent**,
est une faute de lecture, pas une coquille de l'original. Si deux variantes sont
en concurrence, on s'abstient. Les formes portant une majuscule — noms propres,
sigles — sont exclues : *Bally* n'a pas à devenir *ali*.

**915 cellules** ont été corrigées ainsi, dans 758 lignes. Toutes sont
journalisées dans `travail/journal_corrections.txt`, avec la forme lue, la forme
retenue et leurs fréquences respectives, et inscrites dans
`travail/exceptions.txt` : chacune est inspectable et réversible d'une ligne.

Exemples : `kuh` → `kun` (791 attestations), `ksnde` → `kande` (183),
`generc` → `genero` (92), `eskluzive` → `exkluzive`, `mulierc` → `muliero`.
Et **`zobl.` → `zool.`** : la forme `zobl` est lue une fois dans tout le livre,
`zool` 334 fois. Sur ce point la relecture avait raison contre moi.

**Une piste écartée.** J'ai essayé de corriger les vedettes par l'ordre
alphabétique du livre. La logique est fausse : quand une vedette rompt l'ordre,
la faute peut être dans sa voisine, et forcer la vedette à se conformer produit
des monstres (*advento* → *adventc*, *aero* → *aere*). Le journal de cette
tentative est conservé sous `travail/journal_ordre_alpha_ABANDONNE.txt` à titre
d'avertissement. Seule subsiste la consolidation de l'**initiale** de vedette,
qui elle est sûre : sur une page, les vedettes commencent par la même lettre.

### Trois défauts signalés à la relecture, et ce qu'ils ont appris

**1. Caractères fantômes entre les mots** (*lokizas**l**super*, un `o` seul sur
une ligne vide). Une parenthèse ou une majuscule de la ligne SUIVANTE dépasse
vers le haut dans la cellule vide qui la surplombe ; le filet de la ligne
PRÉCÉDENTE dépasse vers le bas. Le critère de bavure ne regardait que les bords
gauche et droit de la cellule. Il regarde maintenant aussi le haut et le bas :
`haut > 0,80` ou `bas > 0,85` de l'encre de la cellule. Seuils calibrés sur les
7 006 caractères vérifiés à la main : **aucun n'est perdu**.

**2. Les voyelles accentuées.** L'article *cirkonflexo* se termine par
`(â, ê, î, ô)` : quatre surfrappes, exactement le cas prévu par la macro `\sur`.
Elles sont maintenant composées comme telles —
`\sur{\textasciicircum{}}{a}` — c'est-à-dire deux boîtes superposées, jamais un
caractère précomposé, comme la machine les formait.

Cette relecture a mis au jour un manque plus large : **le livre contient des
lettres accentuées** (citations latines, françaises, allemandes) — tréma, accent
aigu, cédille, circonflexe. Un relevé automatique en trouve environ 3 900 dans
l'ouvrage. Elles ne sont pas encore toutes traitées.

**3. Un mécanisme d'exceptions.** `travail/exceptions.txt` permet de fixer le
contenu d'une cellule précise, en LaTeX brut :

```
# page	ligne	colonne	contenu LaTeX
99	51	4	\sur{\textasciicircum{}}{a}
```

C'est la voie par laquelle toute lecture arbitrée à l'œil entre dans le
fac-similé, sans toucher au décodage automatique et en restant traçable.

### Exactitude mesurée

L'exactitude n'est pas estimée : elle est **mesurée sur une page entièrement
transcrite à la main, tenue hors de l'apprentissage**.

| | page 193 (image 200) | page 443 (image 450) |
|---|---|---|
| première mesure | **93,35 %** | — |
| classifieur à deux vues + vote de groupe | 95,88 % | — |
| classe « espace » retirée de l'apprentissage | 96,21 % | — |
| correction du gauchissement ligne à ligne | — | **98,04 %** |
| consolidation des initiales de vedette | — | **97,83 %** (autre tirage) |

Sur l'amorce elle-même (7 006 cellules vérifiées à la main sur cinq pages) :
**99,80 %**, et seulement **14 groupes impurs sur 4 197** couverts.

### Les quatre corrections qui ont fait la différence

1. **Le gauchissement du papier, ligne par ligne.** La phase de la grille glisse
   à l'intérieur d'une page : sur la page 443, elle dérive de **−2,1 px en haut
   à +3,9 px en bas, soit 0,57 cellule**. Une seule origine par page ne suffit
   donc pas. Elle est maintenant reprise **ligne par ligne**, à pas constant, en
   minimisant l'encre tombant sur les frontières de cellule. Les trois premières
   colonnes passaient de 20 % de fautes à 2 % ailleurs : le déséquilibre venait
   de là.
2. **La classe « espace » retirée de l'apprentissage.** Vingt-deux exemples de
   bavures suffisaient à faire s'effondrer l'auto-apprentissage : un groupe de
   266 « i » a été étiqueté « espace » avec une confiance de 1,000. Les bavures
   sont maintenant reconnues par un **critère géométrique** (encre plaquée
   contre le bord de la cellule), calibré à la main, et le classifieur ne
   connaît que des caractères réels.
3. **Les soulignements doubles.** Le tapuscrit souligne les vedettes d'un filet
   **double**. Le relevé ne retenait qu'une rangée sur deux ; l'autre restait
   collée sous la lettre et faisait lire *sdtelino* pour *gibelino*. Toutes les
   rangées de filet sont maintenant relevées, et leur suppression **épargne les
   colonnes où un jambage traverse le filet**, pour ne pas éventrer les lettres.
4. **L'ordre alphabétique du livre.** Sur une page donnée, les vedettes
   commencent presque toutes par la même lettre. Cette propriété structurelle
   lève l'ambiguïté sur l'initiale, là où le soulignement double est le plus
   gênant : **534 initiales** ont été consolidées ainsi, par 68 groupes
   réétiquetés. Ce n'est pas une correction du tapuscrit — c'est une lecture
   appuyée sur la structure du livre — et chaque intervention est journalisée
   dans `travail/journal_initiales.txt`.

### Les deux pages hors échelle

Les pages 538 et 539 (images 546 et 547) ont été photographiées à 1,47×. Elles
sont maintenant **ramenées à l'échelle commune** avant tout traitement, par
itération sur la chasse mesurée. Leur décodage reste néanmoins nettement moins
bon que celui des autres pages : rééchantillonnées depuis une image plus fine,
leurs cellules ne ressemblent pas tout à fait aux autres. Elles demandent une
transcription-amorce propre.

### État au terme du premier lot (échantillon soumis à validation)

**Fait**
- Grille mesurée sur les 639 pages ; deux pages hors échelle détectées et traitées.
- 1 059 951 cellules découpées, regroupées en 4 000 groupes (corrélation médiane
  d'une cellule à son groupe : 0,986).
- Transcription-amorce vérifiée colonne par colonne sur 3 pages (page 92,
  la préface, page 293) + 8 folios : 3 642 cellules étiquetées à la main.
- Étiquetage des groupes par propagation, puis vote de l'amorce :
  **99,3 % d'exactitude** mesurée sur l'amorce elle-même ; environ **99,7 % de
  caractères justes** sur la page 92 relue intégralement.
- Détection des filets de soulignement : sur la page 92, 9 plages sur 16 sont
  exactes à la cellule près, les autres à ±1 cellule aux extrémités.
- Filtre des « bavures » : les cellules qui ne contiennent que la bavure d'un
  caractère voisin sont reconnues (l'encre y est plaquée contre le bord de la
  cellule : critère calibré sur 22 cas relevés, aucun caractère réel perdu).
- Calage de la page : `\OrigX` = 16,23 mm, `\OrigY` = 7,43 mm, ajustés par
  corrélation entre la page composée et le scan redressé (résidu : 0 px).

**Limites connues à ce stade**
- **Le cadrage des photographies varie de ±1 cm** d'une page à l'autre. Les
  marges absolues du livre ne sont donc pas mesurables sur ce scan : elles sont
  reconstruites à partir d'une page bien cadrée (la page 92) et appliquées
  uniformément. La grille, elle, est mesurée page par page.
- L'échelle photographique varie de ±1,5 % ; le fac-similé emploie une grille
  constante (la médiane), ce qui est la bonne reconstruction du livre imprimé.
- Les chiffres sont sous-représentés dans l'amorce : les folios sont encore
  imparfaitement décodés.
- Les surfrappes (`â ê î ô` de l'article *cirkonflexo*, barres sur `EF`,
  corrections au ruban) sont repérées mais pas encore étiquetées une à une.
- Les groupes de faible confiance (185 sur 4 000, ~5 % des cellules) restent à
  examiner un à un dans leur contexte.

---

## 7. La couverture

**Il n'y a pas de trame à défaire.** Le spectre de Fourier de la couverture ne
présente **aucun pic périodique** (`travail/couv/spectre.png`) : l'image n'est
pas une similigravure. C'est une **lithographie en une seule encre bleue**, dont
les portraits sont des conversions au trait — du noir et du blanc purs, pas des
demi-teintes. La vectorisation des portraits est donc **légitime** : elle ne
postérise rien, elle restitue exactement les formes imprimées.

**Chaîne de traitement**

1. L'objet image du PDF est extrait tel quel : 1230 × 1650 px. C'est la seule
   définition disponible, soit environ 100 × 150 px par visage.
2. Le RVB est projeté sur son **axe principal** : la couverture n'ayant qu'une
   encre, cet axe sépare l'encre du papier bien mieux qu'un canal isolé.
3. Le fond est estimé par un filtre moyen de 81 px et soustrait, ce qui efface
   le jaunissement et le grain du papier.
4. Seuillage à 0,40, puis suppression des composantes de moins de 8 px
   (les mouchetures du papier).
5. `potrace` (turdsize 1, alphamax 1,0, opttolerance 0,2), sortie SVG **et** PDF
   vectoriel directement utilisable dans LaTeX.

**Livrables** (`ornements/`)

- `couverture/couverture.svg`, `.pdf` — la couverture entière vectorisée
- `couverture/couverture-nettoyee.png`, `-x3.png` — la version tramée nettoyée
- `portraits/<nom>.svg`, `.pdf`, `-x4.png` — un portrait vectorisé par pionnier
- `portraits/<nom>-gris-x6.png` — le portrait nettoyé, en niveaux, ×6
- `trait/embleme-ido.svg` — l'étoile de la Delegitaro
- `trait/bandeNN.svg` — les bandes de lettrage

**Ce que l'état du scan permet, portrait par portrait**

| pionnier | taille | verdict |
|---|---|---|
| L. de Beaufront | 129 × 142 px | le plus fragile : trois-quarts très ombré, le pointillé de l'ombre se referme au seuillage ; le vecteur perd un peu de modelé |
| L. Couturat | 112 × 153 px | bon — profil, grande masse de cheveux, contours nets |
| O. Jespersen | 91 × 156 px | le meilleur — dessin fin, lunettes et traits du visage parfaitement rendus |
| A. Lalande | 104 × 160 px | bon, sauf la barbe : pointillé dense qui se referme par endroits |
| R. Lorenz | 93 × 154 px | bon — le modelé de la joue passe bien |
| W. Ostwald | 109 × 152 px | barbe en pointillé très fin, à la limite de la définition ; le vecteur la rend en amas |
| L. Pfaundler | 114 × 121 px | impression pâle et partiellement mangée sur le scan ; c'est le moins lisible des sept |

Aucun de ces défauts ne vient de la vectorisation : ils sont dans l'impression
d'origine et dans la définition du scan.

## Etat au 7 aout 2026 — relecture integrale

Deux relectures a l'oeil, sur le scan agrandi, ont ete menees a leur terme.

**1. Les 8241 vedettes, une par une.** 516 planches, chacune montrant les
trente premieres cellules de la ligne d'une vedette, grossies cinq fois.
1957 vedettes corrigees. Les ruptures d'ordre alphabetique passent de 1688
a 1026.

**2. Les 1352 groupes d'etiquetage les moins surs.** Le classifieur
n'etiquette pas des cellules mais des groupes de cellules semblables : une
etiquette fausse se propage a tous ses membres, dans tout le livre. Le groupe
1412 etait etiquete « a » alors que ses membres sont des « z » — d'ou
*(aool.)* pour *(zool.)* partout. 123 planches, 519 etiquettes changees,
23 520 cellules touchees.

Chaque nouvelle etiquette a ete confrontee aux 59 074 cellules dont la
transcription est desormais connue a la main (celles des vedettes relues).
Ou la verite terrain tranche, elle l'emporte sur la lecture de la planche :
sur les 76 groupes arbitrables, l'ancienne etiquette etait juste a 63,2 %,
la nouvelle lecture a 85,5 %, l'arbitrage a 100 %.

### Controles

| controle | resultat |
|---|---|
| pages composees | 639 / 639 |
| `Overfull \vbox` | 0 |
| `Overfull \hbox` | 0 |
| position en colonne (197 941 mots) | ecart max 0,0045 cellule, 0 hors tolerance |
| exactitude, page image 560 (jamais vue a l'apprentissage) | **99,19 %** |
| exactitude, page image 450 (jamais vue a l'apprentissage) | **99,45 %** |

Pour memoire, la progression : 93,35 % → 95,88 % → 96,21 % → 98,04 % →
98,69 % → **99,19 %**.

### Ce qui reste

Les ecarts qui subsistent sont presque tous des ambiguites propres a la
machine a ecrire, ou deux touches donnent des formes tres proches :
`l`/`I`, `i`/`1`, `O`/`0`, `M`/`m`, `V`/`v`. Elles demanderaient un modele de
contexte, pas un meilleur oeil. 104 groupes ont ete declares *melanges* :
ils ne peuvent pas etre corriges au niveau du groupe et attendent un
traitement cellule par cellule.

## Suite : troisieme passe, et ce qui a echoue

### Ce qui a marche

**Deuxieme tranche de groupes.** Apres les 1 352 groupes les moins surs, les
1 839 suivants (confiance entre 0,90 et 0,999, 113 215 cellules) ont ete relus
sur 168 planches. 75 etiquettes fausses trouvees — un taux bien moindre que
dans la premiere tranche, ce qui etait attendu et confirme que le tri par
confiance classe bien.

Au total **3 495 groupes ont ete lus a l'oeil**, couvrant environ 190 000 des
1 006 531 cellules du livre.

### Ce qui a echoue, et pourquoi

Trois tentatives ont ete menees puis abandonnees. Elles sont consignees ici
parce qu'un echec mesure vaut mieux qu'une piste rouverte dix fois.

**1. Reapprendre l'etiquetage sur la verite accumulee.** Les 60 768 cellules
dont la transcription est verifiee viennent des vedettes. Or les vedettes sont
en bas de casse et sans chiffres. Un modele appris la-dessus prend un biais
minuscule et ecrase les capitales : l'exactitude tombe de 99,19 % a 99,09 %
sur une page temoin et de 99,45 % a 98,99 % sur l'autre. Ecarte.

**2. Faire arbitrer les groupes par cette meme verite.** Meme cause : les
cellules de vedettes ne sont pas un echantillon representatif d'un groupe. Un
groupe qui contient des « c » et des « o » sera declare « o » parce que les
vedettes en contiennent plus, alors que le corps du texte y met surtout des
« c ». Ecarte, y compris apres avoir exclu les desaccords de casse et les
familles de sosies.

**3. Trancher la casse geometriquement, cellule par cellule.** La capitale
monte plus haut que la lettre ordinaire : la mesure devrait suffire. Trois
variantes essayees — sommet de l'encre a seuil absolu (97,78 %), sommet de la
composante connexe portant le corps de la lettre (98,60 %), comparaison aux
hampes de la ligne elle-meme pour absorber la variation d'echelle du scan
(98,28 %). Les trois perdent contre 99,23 %. La raison, vue en regardant enfin
les cellules fautives une par une : la fenetre d'une cellule mord sur ses
voisines, et l'echelle du scan varie assez d'une page a l'autre pour qu'un bas
de casse d'une page monte plus haut qu'une capitale d'une autre. **La casse
n'est pas recuperable depuis cette trame de cellules.** Il faudrait recouper
toutes les cellules avec une fenetre plus etroite, et regrouper de nouveau.

### Etat final mesure

| controle | resultat |
|---|---|
| pages composees | 639 / 639 |
| `Overfull \vbox` / `\hbox` | 0 / 0 |
| position en colonne (197 931 mots) | ecart max 0,0045 cellule, 0 hors tolerance |
| exactitude, page image 560 | **99,23 %** |
| exactitude, page image 450 | **99,45 %** |

93,35 → 95,88 → 96,21 → 98,04 → 98,69 → 99,19 → **99,23 %**.

### Ce qui reste, honnetement

Sur les trente ecarts que comptent les deux pages temoins, une bonne moitie
sont des sosies que la machine a ecrire elle-meme ne distingue pas : `l`/`I`,
`i`/`1`, `O`/`0`, `M`/`m`, `V`/`v`. Aucun oeil ne les separe sur la cellule
isolee. Les departager demanderait un modele de contexte — savoir qu'un mot
ido ne commence pas par un chiffre — et non un meilleur decoupage.

## Quatrieme passe : ce qui n'est pas de la frappe, et les sosies

Trois remarques du lecteur ont ouvert cette passe, et les trois etaient justes.

### La couverture et les pages blanches ne sont pas du tapuscrit

La couverture est une lithographie a un seul encrage : portraits, embleme,
titre en capitales grasses. Le decodeur y decoupait 738 cellules et y lisait
des caracteres — du bruit pur. Six pages du livre sont blanches (images 1, 3,
7, 87, 111, 577) et recevaient elles aussi des caracteres fantomes.

Ces sept pages sont desormais declarees hors frappe dans
`travail/pages_non_dactylo.txt`. Le fac-simile pose la couverture vectorisee
en pleine page et laisse les pages blanches blanches ; l'edition ne les
decoupe plus en entrees.

### La signature de l'auteur, et les lettres de section

La page de contrefacon (image 2) porte la signature autographe de Marcel
Pesch. Et chaque lettre de l'alphabet s'ouvre sur cette lettre composee en
grand corps dans une elzevir — ni l'une ni l'autre n'appartiennent a la
grille.

Un repere sans echelle les trouve : sur une page dactylographiee toutes les
taches d'encre ont sensiblement la meme hauteur ; ce qui la depasse d'un
facteur six n'est pas de la frappe. **22 ornements** ont ete localises,
decoupes dans le scan et reposes dans le fac-simile a leur place, mesuree en
fraction de feuille : la signature, et les lettres
A B C D E F G H K L M N O P Q R S U V W X.

Trois lettres manquent a l'appel : **I** et **J**, trop etroites pour le
critere de largeur ; **T**, **Y** et **Z**, dont les sections ne portent
apparemment pas de lettre en tete — je ne l'affirme pas, je n'ai pas su la
trouver.

Les 888 cellules que ces ornements recouvrent sont neutralisees : elles ne
produisent plus les suites de caracteres parasites qu'on lisait sous chaque
grande lettre.

### « c » et « o » sont parfois confondus

Verifie, et la cause n'etait pas celle qu'on croit. Les 889 groupes etiquetes
« c » ou « o » qui n'avaient jamais ete relus l'ont ete, sur 81 planches :
**une seule etiquette fausse sur 308 groupes**. La confusion ne vient donc pas
de l'etiquette du groupe, mais de cellules isolees tombees dans le mauvais
groupe — et cela, aucune planche ne peut le montrer.

Ce qui le montre, c'est le mot. Un mot qui n'existe pratiquement nulle part
ailleurs dans le livre, mais qui devient un mot bien atteste des qu'on echange
deux caracteres que la machine confond, est une confusion. Applique aux trente
paires de sosies relevees par les relecteurs, avec un critere severe — la
forme corrigee doit compter au moins six occurrences et etre au moins huit
fois plus frequente que la fautive — le procede donne **1 226 corrections** :
*oirklo* → *cirklo*, *komenoas* → *komencas*, *Franoia* → *Francia*,
*preoipua* → *precipua*, *zocl* → *zool*.

Une seconde passe sur le texte deja corrige a ete essayee : elle degrade
(99,23/99,50 → 99,14/99,41). Le lexique s'appauvrit a mesure qu'on le corrige,
et les formes rares deviennent des cibles. Une passe, pas deux.

### Etat final mesure

| controle | resultat |
|---|---|
| pages composees | 639 / 639 |
| `Overfull \vbox` / `\hbox` | 0 / 0 |
| position en colonne (197 931 mots) | ecart max 0,0045 cellule, 0 hors tolerance |
| exactitude, page image 560 | **99,23 %** |
| exactitude, page image 450 | **99,50 %** |

93,35 → 95,88 → 96,21 → 98,04 → 98,69 → 99,19 → 99,23 → **99,50 %**.

## Cinquieme passe : du contenu manquait

Le lecteur a signale qu'environ une page sur deux semblait amputee de son
haut. C'etait vrai, et c'etait le defaut le plus grave du projet : non pas des
caracteres mal lus, mais du texte jamais decode.

### La cause

Le pipeline efface les ombres de bord du scan. Pour cela il cherchait, dans
les 16 % superieurs de l'image, la **derniere** rangee sombre, et effacait
tout jusqu'a elle. Or une ligne de texte soulignee est sombre elle aussi. Sur
la page 28, une ligne a la rangee 177 etait prise pour une ombre : le masque
detruisait tout de la rangee 78 a la rangee 183 — six lignes, dont les entrees
*alternativo*, *alternatoro* et *altitudo*, plus le folio.

Le correctif tient en une observation : une ombre de bord **touche le bord**
et reste continue ; une ligne soulignee est isolee au milieu du blanc. On
exige donc la continuite depuis le bord.

**Cela ne vaut que dans le sens des lignes.** Une ligne de texte peut etre
sombre sur 45 % de la largeur ; une colonne de caracteres ne l'est jamais sur
45 % de la hauteur. Assouplir le masque lateral laisse l'ombre de reliure dans
l'image, le lattis de colonnes s'y accroche, et soixante pages ont rendu leur
texte entrelace — « o.p(bot.) Genero denrub ac iudealai ». Le masque lateral a
donc ete laisse tel quel.

### La reparation, sans tout detruire

Tout recalculer aurait efface le travail accumule : 5 800 corrections indexees
par page, ligne et colonne, et 3 495 groupes lus a l'oeil. On a donc repare
page par page :

1. les cellules de la page sont recoupees avec le masque corrige ;
2. l'ancienne page est alignee sur la nouvelle par le contenu de ses lignes,
   ce qui donne le decalage de numerotation ;
3. les cellules qui existaient deja **gardent leur groupe** — toute la
   relecture reste valide ;
4. les cellules nouvelles sont rattachees au groupe dont le centre est le plus
   proche, dans l'espace de traits ou les groupes ont ete formes. Fidelite
   mesuree sur des pages temoins : 99,0 a 99,8 % ;
5. les corrections de la page sont reindexees du meme decalage.

Quatre-vingt-cinq pages ont ete reparees, **soixante-sept conservees** : une
page dont la reparation faisait perdre des vedettes a ete remise en l'etat.
Une page amputee vaut mieux qu'une page brouillee. Bilan : **7 728 cellules et
71 entrees retrouvees** (8 241 -> 8 312).

### Les autres remarques du lecteur

**Les ornements etaient mal places.** Ils l'etaient : leur position etait
exprimee en fraction de la feuille scannee, alors que le cadrage du scan varie
d'une page a l'autre. Ils sont maintenant places en **coordonnees de grille** —
converti en colonnes et en lignes de leur page, puis repose au pas de la
machine. C'est l'invariant du texte, donc le meme calage : la superposition
avec le scan est desormais franche.

**Le « ,F » sorti de nulle part** etait un fragment du paraphe de l'auteur que
la boite de la signature ne couvrait pas. La boite est dilatee de 35 % ; le
« M » de Marcel, detache du reste, est aussi rentre dans le decoupage.

**Le « surligne » sur DEFIRS** n'en est pas un. Aucune de ces mentions n'est
soulignee dans la source composee — verifie sur les 18 458 groupes soulignes
du livre. Le trait qu'on voit au-dessus de *DE.* est le soulignement de
*(trans, en)*, sur la ligne precedente, dont la plage de colonnes recouvre
celle de *DE.* Il est au meme endroit dans le scan : le fac-simile est fidele.

**« acinti » pour « donacinti »** est un vrai defaut, et il n'est **pas**
corrige. Le bloc de texte est cerne par les colonnes encrees sur au moins
trois lignes ; page 6, *donacinti* est la seule ligne a toucher la marge, ses
trois premieres colonnes sont donc hors du bloc. Etendre le bloc aux colonnes
encrees sur une seule ligne recupere le mot — mais destabilise le lattis de
colonnes ailleurs : huit pages du corps y ont perdu toutes leurs vedettes.
Ecarte, et signale ici plutot que corrige a moitie.

### Etat final mesure

| controle | resultat |
|---|---|
| pages composees | 639 / 639 |
| `Overfull \vbox` / `\hbox` | 0 / 0 |
| position en colonne | ecart max 0,0045 cellule, 0 hors tolerance |
| entrees | 8 312 |
| exactitude, page image 560 | **99,23 %** |
| exactitude, page image 450 | **99,50 %** |

## Fins de ligne coupees : essaye, mesure, ecarte

Le bloc de texte d'une page est cerne par les colonnes encrees sur au moins
trois lignes. C'est robuste au bruit, mais cela ampute les colonnes qu'une
seule ligne atteint — d'ou « acinti » pour « donacinti » a gauche, et
« anon » pour « anoni- », « apa » pour « aparas », « preciz » pour « preciza »
a droite.

**A gauche**, l'extension deplace l'origine des colonnes et decale toute la
page. Elle a ete activee au cas par cas, pour les seules pages liminaires ou
le texte est clairseme et ou il n'y a pas de vedette a perdre : « donacinti »
est entier.

**A droite**, elle n'ajoute des colonnes qu'apres les autres et semblait donc
sans danger. Elle a ete propagee au livre entier, puis retiree : le
redecoupage qu'elle entraine fait perdre des vedettes a **145 pages**
(8 312 entrees -> 7 502). Le gain — quelques dizaines de fins de ligne — ne
paie pas la casse. Ecartee.

Les fins de ligne coupees restent donc un defaut connu. Les relecteurs les
signalent une a une dans leur section `# DOUTEUX` : « 54 cases fournies, 57 sur
la planche — les trois caracteres `ras` ne tiennent pas ». C'est la liste a
reprendre si l'on veut un jour corriger cela proprement, ce qui demanderait de
recouper les cellules de tout le livre et de regrouper de nouveau.

## Deux corrections d'assiette

**La couverture** debordait a droite : sa boite faisait la largeur de la
feuille mais commencait a la marge de gauche, donc elle sortait du papier de
22 mm. Elle est recalee sur le bord physique du papier — le titre et la date
sont entiers, les huit portraits tiennent.

**La signature** de l'auteur etait tronquee en haut : la boite ne couvrait que
la tache d'encre principale, sans les hampes ni le « M » de Marcel, detache du
reste. Elle est elargie de 30 % a gauche et de 45 % vers le haut.

## Les fins de ligne : mesurees, puis rendues

Assez d'avis, une mesure. Chaque page a ete recoupee avec le bloc etendu a
droite — sans rien enregistrer — et l'on a compte les cellules encrees qui
tombaient au-dela du bloc enregistre. Ce sont exactement les caracteres perdus.

| | |
|---|---|
| pages examinees | 632 |
| pages touchees | 456 (72 %) |
| lignes touchees | 728 |
| **caracteres coupes** | **994** |
| par page | mediane 2, maximum 21 |

C'est peu — un millieme du livre — mais cela tombe toujours en bout de mot, la
ou cela se voit : *anoni-* devenait *anon*, *aparas* devenait *apa*.

**Comment ils ont ete rendus.** Elargir le bloc obligeait a redecouper toutes
les pages, ce qui faisait perdre des vedettes a cent quarante-cinq d'entre
elles. On a donc pris l'autre chemin : la page est recoupee **en memoire**, les
cellules qui debordent sont rattachees au groupe dont le centre est le plus
proche, et elles rejoignent le texte comme de simples corrections, aux colonnes
qui suivent le bloc. Le decoupage enregistre ne bouge pas ; aucune correction
deja faite n'est invalidee.

**908 caracteres sur 994** sont ainsi revenus. Les 86 qui manquent sont sur 20
pages ou le recoupage deplace l'origine des colonnes ou change le lattis de
lignes : la comparaison n'y est plus sure, et j'ai prefere ne rien ecrire.

## L'assiette des pages

Le tapuscrit ne remplit pas toujours la meme largeur : ses lignes vont de 122 a
190 mm. Toutes les pages etant posees a la meme origine, il restait jusqu'a
66 mm de blanc d'un cote pendant que l'autre debordait de la feuille.

Chaque page est desormais centree sur sa propre largeur, avec **6 mm de plus du
cote de la couture** — l'ouvrage compte 639 pages, il faut de quoi le relier.
Une moucheture isolee loin a droite (un « - » seul apres vingt-quatre espaces)
n'entre pas dans le calcul : elle elargissait une page de trente millimetres.

| marges | avant | apres |
|---|---|---|
| gauche | 21,9 fixe | 1,6 a 47,3 (mediane 24,4) |
| droite | −2,4 a 66,2 | 7,7 a 40,8 (mediane 23,0) |
| pages desequilibrees de plus de 20 mm | 34 | **4** |
| pages debordant de la feuille | oui | **aucune** |
| interieur / exterieur, recto | — | 24,4 / 20,5 |
| interieur / exterieur, verso | — | 28,1 / 24,4 |

Le decalage de chaque page est **quantifie sur la grille** : un nombre entier de
pas en largeur, un nombre entier d'interlignes en hauteur. Sans cela les
caracteres ne tombent plus sur une colonne entiere et le controle de position —
celui qui garantit la fidelite de la trame — echoue. Avec, il passe toujours :
198 886 mots, ecart maximal 0,0049 cellule, aucun hors tolerance.

## La signature : deux boites, pas une

Elargir la boite de la signature pour ne rogner ni les hampes ni le « M » de
Marcel avait un effet de bord : cette meme boite servait a neutraliser les
cellules recouvertes par l'ornement, et elle mordait desormais sur les deux
lignes tapees au-dessus — « ye mea signaturo reputesos... » y disparaissait.

Il en faut donc deux : celle du **decoupage**, large, pour que l'image soit
entiere ; celle du **masque**, serree sur l'encre, dilatee vers le bas et sur
les cotes seulement, jamais vers le haut. Le texte est revenu, la signature est
restee entiere, et le « ,F » n'est pas reparu.

## La relecture integrale

Le livre a ete relu en entier, page par page, en confrontant l'image du scan
au texte decode, ligne a ligne. **631 pages, 6 830 lignes corrigees.**

| | |
|---|---|
| pages relues | 631 sur 631 |
| lignes corrigees | 6 830 (mediane 10 par page) |
| cellules corrigees | 368 305 |
| exactitude, page image 450 | **99,96 %** |
| exactitude, page image 560 | 99,73 % — dont trois « ecarts » qui n'en sont pas : ce sont des fins de ligne retrouvees que ma transcription de reference, faite avant leur recuperation, ne contient pas |

Le protocole tient a une contrainte : la grille impose une case, un caractere.
Le relecteur rend donc une ligne de **longueur identique** — une lettre manquee
remplace une espace, une lettre inventee redevient une espace. Le rapprochement
se fait colonne par colonne, rien ne peut se decaler, et une ligne de longueur
fausse est refusee plutot que devinee. Dix lignes sur 6 830 ont ete refusees
ainsi.

### Ce que la relecture a coute, et comment le prix a ete divise par douze

Les premiers relecteurs mesuraient les soulignements au pixel a chaque page —
redressement de la bande, reconstruction de la grille, superposition des
frontieres de cases : cent appels d'outil par page. J'ai mesure si ce travail
valait son prix, en confrontant la detection automatique aux 1 698 lignes deja
relevees a la main : elle place correctement **95,7 % des cellules soulignees**,
et ce qui lui echappe est presque toujours une seule cellule en fin de filet —
le point d'une abreviation — la ou le tapuscrit lui-meme est irregulier.

Les soulignements sont donc sortis du travail des relecteurs, et la consigne
leur interdit desormais d'ecrire le moindre script : ce travail se fait a
l'oeil, la longueur des lignes est verifiee par le programme, et un doute
signale vaut mieux qu'une demi-heure de mesure. **Cinq pages en trente appels**
au lieu de trois pages en trois cents.

### Un controle de rendement

Le livre tourne autour de dix corrections par page. Une page qui en rend zero
n'a probablement pas ete lue : c'est ainsi que les deux pages de la Prefaco,
revenues vides, ont ete rattrapees — elles etaient fautives. Le controle tourne
apres chaque lot. Il reste six pages a moins de trois corrections ; deux ont ete
verifiees a la main et sont reellement justes (les premieres pages du livre sont
les mieux frappees, ruban neuf), les quatre autres ont ete relues une seconde
fois.

## Trois retouches d'aspect

### La couverture : ce qui a ete rendu lisible

Le seuillage gardait l'encre au-dessus de la moitie du maximum local. Un trait
fin voisin d'une lettre grasse passait sous ce seuil : sous le premier
portrait, « PROF. DE TEOLOGIO / UNIV. PARIS / (FRANCIA) » se reduisait a
« EO OG O / PAR S / RAN A », et « lia laboro linguistikala » a
« l a laboro l nguistikala ».

Le seuil est desormais **a hysteresis**, comme pour un contour : un seuil haut
donne le trait sur, un seuil bas le trait douteux, et l'on garde du douteux
tout ce qui touche du sur. Un delie pale rattache a une lettre nette survit ;
une moucheture isolee, non. Sont revenus : les legendes des sept portraits,
« lia laboro linguistikala », « ZURICH SUISIA », « KOBENHAVN (DANIA) »,
« (PRECIZA, KONC ZA, FACILA) », et l'embleme Ido, qui etait gris et qui est
noir plein.

**Le depoussierage a demande trois essais**, et les deux premiers sont
instructifs. Retirer les petites taches loin d'une grosse : mauvais critere,
les legendes n'ont aucune grosse composante, leurs points sur les i n'etaient
ancres a rien et disparaissaient. Retirer les amas de moins de 2 500 pixels
apres huit pixels de dilatation : trop severe, « vu », « lia », « ZA »,
« di la » pesent moins qu'une grosse salissure et ont ete effaces. Le bon
reglage fait fusionner les mots d'une meme ligne — vingt-deux pixels de
dilatation — avant de juger : un mot court appartient alors a l'amas de sa
ligne, une tache reste seule.

**La faute qui coutait soixante et une lettres.** `binariser_trait()` se
terminait par un `enlever_grain()` : toute composante de moins de vingt-cinq
pixels situee a plus de trois pixels d'une grosse composante etait retiree.
C'est la regle « petit et loin d'un gros », dont on savait deja qu'elle etait
fausse, tapie a l'interieur meme de la binarisation — donc **avant** tout
depoussierage, la ou aucune planche de controle n'allait la chercher.

Elle effacait le point de « A. LALANDE », le « FI » de « FILOZOFIO », le « L »
de « DIL », le « S » de « PARIS », le « L » de « LINGUIST. », les parentheses
de « (FRANCIA) », le « I » de « KONCIZA », le point de « 10.000 », celui de
« 2. di agosto 1964. » — soixante et une zones d'encre, toutes franches et
lisibles dans le scan.

Le diagnostic ne s'est pas fait a l'oeil mais par soustraction : on marque ce
qui est noir dans le scan et blanc dans le rendu, on etiquette, et on lit la
liste. C'est cette carte qui a designe l'etape coupable — le texte etait deja
perdu a la binarisation, les deux depoussierages etaient innocents.

**Le grain du papier se juge au niveau d'encre, pas a la taille.** Une fois
`enlever_grain()` retire, le grain remontait par nuages entiers : le seuil a
hysteresis est *relatif* a un maximum local, et dans une plage blanche le
maximum local est une moucheture. Le depart est pourtant physique : les
caracteres sont encres, le grain ne l'est pas. Les huit lettres qu'on avait
perdues culminent toutes entre 0,90 et 1,00 ; les trois quarts des composantes
plafonnent sous 0,40. `retirer_pale()` coupe a 0,55 — vingt-deux pour cent de
l'encre s'en va, aucune lettre n'est touchee, et les deux depoussierages par
isolement n'ont plus que cinquante-deux amas et sept taches a ramasser au lieu
de mille six cent soixante et un.

**Verification exhaustive.** Le controle final ne se fait plus par sondage :
on soustrait le rendu du scan sur toute la page et on inventorie ce qui reste.
Il reste dix-neuf zones, de douze a quarante-cinq pixels, toutes dans les
demi-teintes des portraits ou sur des mouchetures isolees. Aucune lettre.

**Un second depoussierage, plus fin.** Vingt-deux pixels de dilatation, c'est
genereux : une salissure posee a dix pixels d'un mot rejoint son amas et
survit. Il en restait une cinquantaine, bien visibles dans les blancs. On ne
peut pas resserrer le rayon sans reperdre « vu » et « di la ». On dilate donc
de facon **anisotrope** — large en largeur, etroite en hauteur : les mots d'une
meme ligne se rejoignent, une tache posee au-dessus d'une ligne ne la rejoint
pas. Une composante n'est effacee que si les trois conditions tiennent
ensemble : elle est petite, la ligne a laquelle elle appartiendrait est pauvre
en encre, et **aucune vraie lettre ne se tient a moins de douze pixels d'elle**.
Cette derniere condition est un veto, jamais un motif — c'est ce qui epargne
les points de « PRECIZA, KONCIZA, FACILA », qui n'ont pourtant aucune grosse
composante dans leur legende. Quarante-neuf taches retirees, aucune
ponctuation perdue.

**« invitas » : deux lettres reprises a la meme main.** Le mot se lisait
« inv·as ». Dans l'intervalle, le niveau d'encre plafonne a 0,146 et le 95e
centile est a 0,014 : du papier nu. Les lettres ne sont pas dans le scan, et
aucun seuil ne les fera apparaitre. On n'a rien dessine pour autant. Le « i »
et le « t » manquants figurent a quelques centimetres de la, dans
« profitar » — meme ligne, meme main, meme corps, et dans le meme ordre. On
les y prend, on les tourne de la difference d'inclinaison entre les deux
endroits de l'arc (14,8 degres), et on les repose a la place que l'espacement
de « profitar » leur assigne. Chaque trait de la couverture reste ainsi de la
couverture.

Le choix des composantes s'est fait a l'oeil, sur planche. Une premiere version
prenait « la composante la plus proche d'un point » : elle est allee chercher
un « o » et a ecrit « invoias ». Les composantes sont desormais designees par
leur numero et **verifiees par leur signature** — centre et surface — avant
d'etre transplantees : si la binarisation bouge, le script s'arrete au lieu de
greffer n'importe quoi.

**Ce qui n'a pas pu etre rendu.** « COUTURAT » reste ebreche : l'encre y manque
dans l'original meme. Une fermeture morphologique a ete essayee pour recoller
ces traits : elle empate les petites capitales sans reparer les lacunes.
Contrairement au cas de « invitas », les lettres entamees n'ont pas de jumelle
utilisable a proximite — les redessiner serait possible, mais ce ne serait plus
une restitution, et c'est une decision qui n'appartient pas au programme.

### Les filets fantomes sous la notation DEFIRS

Les capitales D, E, F, I, R, S ont toutes, dans cette machine, un empattement
superieur plat. Mises bout a bout — et la notation des langues les met
toujours bout a bout — leurs sommets s'alignent en une barre horizontale
continue. Cette barre se tient a 0,44 interligne au-dessus de sa propre ligne
de base, c'est-a-dire en plein dans la fenetre ou la detection cherchait le
soulignement de la ligne PRECEDENTE. Elle etait donc lue comme un filet, et
rapportee a la ligne du dessus.

C'est ainsi que « sur » se trouvait souligne dans *alineo*, « lego » dans
*abrogar*, « kun » dans *amazono* — chaque fois le mot qui se trouvait juste
au-dessus du DEFIRS, aux memes colonnes que lui. Le releve etait sans appel :
**5 043 filets fantomes, sur 4 310 lignes, dans 621 pages sur 639**. Le defaut
n'etait pas occasionnel, il etait partout.

Le depart est physique et tient en une phrase : **sous un vrai filet il n'y a
rien, sous le haut d'une lettre il y a la lettre**. Mesure a trois pixels sous
le filet de « alineo » : 0,00. Au meme endroit sous la fausse barre : 0,29. Le
veto coupe a 0,20, entre les deux, avec de la marge des deux cotes.

Calibre contre les 1 697 lignes relevees a l'oeil : les faux filets tombent de
**31 a 2**, au prix de **3 filets vrais** perdus sur 432. C'est le sens du
compromis deja retenu ailleurs — mieux vaut un soulignement manquant qu'un mot
souligne a tort.

Les filets recalcules ne sont pas reecrits dans le corpus de cellules : il
pese 295 Mo et un accident de format y a deja coute 144 pages. Ils forment une
couche a part (`travail/filets.pkl`), lue apres le releve a l'oeil et avant la
detection d'origine.

**Le releve a l'oeil n'est pas infaillible non plus.** A la page 33, il portait
le filet sous le « ta » de *Voltaire* au lieu du « ta » demonstratif quatorze
cellules plus loin — le relecteur avait recopie le fantome. Comme le releve
prime sur tout, la faute survivait a la correction de la detection. Elle a ete
redressee a la main apres verification sur le scan. Il reste 102 lignes ou
releve et detection corrigee ne se recoupent pas : le releve y garde la main,
mais elles meritent un jour d'etre revues une a une.

### Les debuts de ligne coupes a gauche

Le bloc de texte est cerne par les colonnes encrees sur plusieurs lignes. A
droite, cela coupait des fins de mots — `rendre_fins.py` les a rendues. A
gauche, cela coupe la premiere lettre des lignes que la dactylo a commencees
une cellule plus tot que les autres, et le mal y est plus grave : ces
lignes-la sont justement des vedettes. « protezo » se lisait « rotezo »,
« protisto » « rotisto ».

`rendre_debuts.py` est le pendant gauche. Chaque page est recoupee EN MEMOIRE
avec le bloc elargi, les cellules recuperees sont rattachees au groupe dont le
centre est le plus proche dans l'espace traits2, et deposees a part. Le corpus
de cellules ne bouge pas.

**La numerotation demandait une decision.** A droite, les cellules rendues
prennent les colonnes qui suivent le bloc et rien ne bouge. A gauche, elles
tombent AVANT la colonne zero. Decaler la seule ligne concernee l'aurait posee
une cellule a droite de sa place reelle. On decale donc la PAGE ENTIERE :
les positions relatives sont conservees au caractere pres, et le bloc, dont la
marge est fixee ailleurs, retombe au meme endroit sur la feuille.

**L'elargissement force ramene aussi le bord de la feuille.** La regle du bloc
veut qu'une colonne serve sur plusieurs lignes ; or la premiere lettre d'une
vedette est seule dans la sienne, et ne declenche donc rien. Il a fallu forcer
l'elargissement — au prix d'ombres de reliure qui se decodent en suites de
« m » et de guillemets. Un tri les ecarte : une cellule, en colonne -1, portant
une lettre ou un « + », deux lignes par page au plus.

**Le tri automatique n'a pas suffi.** Sur les vingt pages qu'il retenait,
trois portaient une ANNOTATION MANUSCRITE en cursive — pages 18, 29 et 52 — et
la consigne est constante depuis le debut : les notes a la main sont ignorees.
Quatre autres restaient douteuses. La verification s'est donc faite planche par
planche, et seules **quinze cellules sur treize pages** ont ete retenues,
reconnues comme frappees et completant un mot. Les ecartees sont listees dans
`filtrer_debuts.py`, avec leur motif.

Deux des « + » des vedettes non officielles sont revenus par ce chemin —
« +takigrafar » entre autres : le signe tombait lui aussi hors du bloc.

### Les cinq sections qui ne commencent pas en tete de page

Chaque lettre de l'alphabet s'ouvre sur sa capitale en grand corps, decoupee
dans le scan. La detection ne cherchait que dans le haut de la feuille — or
cinq sections, I, J, T, Y et Z, s'ouvrent au milieu d'une page, a la suite de
la precedente. Le livre restait sans grande capitale pour ces cinq lettres.
On donne desormais, pour celles-la, la bande verticale ou chercher.

Deux autres pieges tenaient au meme endroit. Le plancher de surface etait a
400 pixels : il ecartait les capitales etroites, le « I » n'en pesant que 349
et le « J » 365 (un caractere tape en pese moins de cent — 300 separe encore
sans risque). Et les ornements etaient indexes par page, un seul par page :
la 631 en porte deux, le « X » en tete et le « Y » au milieu, et le « Y »
disparaissait sans bruit. C'est une liste par page maintenant.

### Le « + » des vedettes non officielles

Le signe occupe une cellule pleine devant la vedette, frappe une demi-hauteur
plus haut. La cellule n'est pas marquee occupee — un releve fonde sur `occ`
ne le voit donc pas, et il a fallu mesurer l'encre directement dans le scan.

Il posait en outre un piege au soulignement : le filet commence apres le
signe, sous la vedette, et la regle « un filet ne commence pas au milieu d'un
mot » le jetait. « +quoniam » perdait ainsi un soulignement pourtant
correctement mesure. Le « + » est desormais une frontiere de mot, au meme
titre que l'espace et la parenthese ouvrante.

### Les marges : calees sur la tranche, et non sur la couture

Premiere version : centrage page par page. Chaque page etait equilibree
isolement, mais le bord gauche sautait d'une page a l'autre — sur 631 pages,
199 sautaient de plus de cinq millimetres, jusqu'a vingt-huit.

Deuxieme version : origine fixe a gauche, 13,5 mm au recto et 8,0 mm au verso.
Les marges gauches devenaient parfaitement regulieres — et les marges DROITES
allaient de 6 a 72 millimetres, puisque le bord droit suivait la ligne la plus
longue de chaque page. Le defaut avait seulement change de cote : a
l'ouverture, deux pages en regard n'avaient toujours aucun bord commun.

Version retenue : le bloc est cale sur le cote EXTERIEUR — le verso par sa
gauche, le recto par sa droite. La marge de tranche vaut alors 8,0 mm partout,
sur 99 % des pages (le demi-pas de quantification pres : le bloc doit rester
sur le lattis de la machine, dont le pas est de 2,54 mm, ce qui laisse jusqu'a
1,27 mm de jeu). Tout l'ecart des longueurs de ligne se reporte du cote de la
couture, ou il est le bienvenu : la gouttiere mesure 39 mm en mediane, ce
qu'un ouvrage de 640 pages perd volontiers a la reliure.

Le prix a payer est explicite : **la gouttiere, elle, n'est plus constante**
— de 6 a 77 mm selon la longueur des lignes. On ne peut pas fixer les deux
bords a la fois tant que la largeur du texte varie. Le choix se defend :
la tranche est ce que l'on voit livre ferme et en feuilletant, la couture ne
se voit qu'a plat. Une plancher de 12 mm garde le texte hors de la reliure ;
six pages passent 74 colonnes et n'entrent dans aucune regle, elles gardent la
butee absolue de 3 mm.



Centrer chaque page sur sa propre largeur la rendait equilibree isolement,
mais faisait sauter le bord gauche d'une page a l'autre : sur 631 pages,
**199 sautaient de plus de cinq millimetres**, jusqu'a vingt-huit. Un livre ne
fait pas cela. Le bloc est desormais pose au meme endroit sur toutes les pages
de meme main — 13,5 mm du cote de la couture, 8,0 mm du cote de la tranche —
et les lignes courtes laissent simplement du blanc a droite, comme dans
l'original. Deux pages hors norme reculent de quelques millimetres pour ne pas
deborder.

### Un feuillet de garde

Le livre se terminait sur « F I N O » en page 639 — nombre impair, sans garde.
Une page blanche de plus le porte a **640 pages, soit quarante cahiers de
seize** : ce qu'il faut pour le relier.

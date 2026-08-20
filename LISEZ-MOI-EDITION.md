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
| `dicionario.pdf` | le **dictionnaire de poche**, vers lequel pointe le bouton « Deskargar » ; copie de `posho/posho.pdf` |
| `main.pdf` | le fac-similé LaTeX, page à page, grille à grille (`main.tex` + `contenu/`) |
| `filets-dubinda.md` | les soulignements de l'auteur que l'édition n'a pas su placer |
| `ordino-ruptita.md` | les vedettes qui rompent l'ordre alphabétique, avec la place où elles auraient dû aller |
| `travail/journal_complet.txt` | **toutes** les corrections : ce qui a été lu, ce qui a été retenu, et si c'est un correcteur ou l'œil qui a tranché |
| `outils/` | la chaîne complète, de l'image au JSON |

**9 472 entrées** extraites de 632 pages de corps d'ouvrage.
5 272 portent une marque de domaine (*bot.*, *zool.*, *arkitekt.*…),
823 un nom scientifique latin, 1 678 plusieurs sens numérotés,
8 441 un code de langues final.

---

## Le champ d'un enregistrement

```json
{"vedetto":"cinocefalo", "fako":"zool.",
 "senci":["Genero de simio, di qua la muzelo esas longa quale che la hundo"],
 "strukt":[{"teksto":"Genero de simio, di qua la muzelo esas longa quale che la hundo",
            "teksto_k":"Genero de simio, di qua la muzelo esas longa quale che la hundo",
            "sub":[]}],
 "sublineita":["zool","cynocephalus"], "kursiva":[], "dubinda":[],
 "latina":["cynocephalus"], "simbolo":null,
 "lingui":["Angla","Franca","Italiana","Hispana"],
 "kodo":"EFIS", "pagino":92, "ligno":8, "image":99, "citita":false,
 "teksto":"cinocefalo. (zool.) Genero de simio, di qua la muzelo esas longa quale che la hundo. - L. cynocephalus. - EFIS.",
 "teksto_brut":"cinocefalo. (zool.) …",
 "korektita":0, "drapeli":[]}
```

`pagino` est le numéro imprimé dans le livre ; `image` l'index dans le PDF
fourni ; `ligno` la ligne de la grille du tapuscrit. **Chaque entrée peut donc
être ramenée au fac-similé**, ligne par ligne. C'est la condition pour que ce
travail reste vérifiable dans vingt ans.

Une réserve sur `pagino`, vérifiée sur le fac-similé : il vaut `image - 7` pour
les 9 472 entrées, sans exception — c'est un calcul, non une lecture. Or **le
livre saute deux numéros** : la page qui porte `fosfo` est numérotée
« 173/175 », doublement, et l'écart change de part et d'autre. Après elle,
`pagino` est bien le folio imprimé ; **avant elle, le folio imprimé vaut
`pagino - 2`**. `image` et `ligno`, eux, restent exacts de bout en bout : c'est
sur eux que reposent les clés de `subvorti.txt` et de `simboli.txt`.

`teksto_brut` est la ligne telle que le décodage l'a lue ; `teksto` la même
après correction et typographie ; `senci` le découpage en sens numérotés, débarrassé
des numéros de l'original. `citita` marque l'emprunt que l'auteur cite entre
guillemets — *« amen »* —, que les éditions rendent en chevrons sans que la
recherche ait à les taper. Encore faut-il que les guillemets tiennent **tout**
le mot : *"brokoli"-kaulo* n'est pas un emprunt cité mais un mot ido dont le
premier élément seul est emprunté, et les éditions lui mettaient une seconde
paire de chevrons autour de la première. Une fermante suivie d'une minuscule ou
d'un trait d'union est donc refusée — le mot continue ; suivie d'une capitale,
elle ouvre la définition, l'espace ayant manqué à la frappe
(*"madras"Kapovesto*). Ses chevrons restent **dans** la vedette, faute d'un
drapeau qui puisse les porter, et prennent l'espace que les éditions posent
partout ailleurs : *« brokoli »-kaulo*. Le rangement, lui, ne compte ni chevron
ni espace — le mot se cherche à *brokoli-kaulo*.

`korektita` compte les cellules redressées dans l'entrée : une provenance, non
un doute.

### Les sens et leurs sous-entrées (`strukt`)

`senci` donne le texte d'un sens tel qu'il se lit. `strukt` donne le même texte
**découpé** : un corps, et les locutions qui portent leur propre définition.

L'auteur en pose de plusieurs façons. Le plus souvent la locution ouvre la
phrase, capitale et deux-points — *Proporciono geometriala : …* Parfois elle
s'écrit entre parenthèses, et alors en minuscule — *estado. … (estado civila :
la situeso di persono kom filio legitima o ne-legitima…)*. La **virgule** en
fait partie, l'auteur empilant parfois des locutions parallèles qui partagent
une définition — *Extraktar radiko, quadrata, kubala, di nombro : …*,
c'est-à-dire la racine carrée et la racine cubique en une fois. Enfin, un
**article entier** se glisse une fois entre parenthèses dans la définition d'un
autre — *butono. … (\*botono. (elektr.) Mikra cilindro…)* —, où l'astérisque,
marque des mots non encore officiels, le distingue d'une abréviation de domaine
de même forme (*trans.*, *anat.*).

Tous ces cas donnent la même chose : coulées dans le paragraphe, ces locutions
étaient introuvables ; détachées, elles s'ouvrent leur propre alinéa et **se
cherchent comme une vedette**.

```json
"strukt":[{"teksto":"Eso mentala, anmala, psikala, od aferala di la individuo koncernata",
           "sub":[{"loko":"estado civila", "fako":"",
                   "teksto":"La situeso di persono kom filio legitima o ne-legitima, mariajita o celiba"}]}]
```

| clé | ce que c'est |
|---|---|
| `teksto` | le corps du sens, la locution ôtée. Vide quand le sens n'a que ses locutions : son numéro passe alors sur la première |
| `sub[].loko` | la locution, écrite en minuscule comme une vedette |
| `sub[].fako` | son domaine propre, nu, sans les parenthèses — *geom.* |
| `sub[].teksto` | sa définition |
| `sub[].kodo`, `sub[].lingui` | présents sur la seule sous-entrée qui vient d'un **rattachement** (voir plus bas) : l'article rattaché garde son code de langues |

103 sous-entrées dans 84 entrées, dont 41 portent un domaine propre.

Une même locution peut relever de **deux** entrées, chacune avec sa
définition : *estado civila* se range sous `civila`, qui la définit au long,
comme sous `estado`, qui la mentionne. Les deux sont conservées telles quelles.

Le code de langues sert aussi à **séparer deux articles frappés sur une même
ligne** : il finit le premier. Quand ce qui suit ne se présente pas comme une
vedette — une virgule au lieu du point chez *asasinar*, un tiret d'affixe chez
*ko-*, une parenthèse égarée entre les deux chez *tino*, rien du tout chez
*warfo* —, le second restait noyé dans le premier, et lui donnait son code.
`travail/dividi.txt` porte ces coupures, relevées à l'œil ; la dactylo, elle,
avait souligné chacune de ces vedettes, comme elle souligne celles qu'elle pose
au milieu d'une ligne. Cinq racines ont ainsi été rendues au dictionnaire —
*shovar*, *asasinar*, *ko-*, *tino*, *warfo*.

Un cas particulier : l'auteur a marqué d'un double tiret marginal un article
qu'il fait dépendre du précédent — *protestanto* sous *protestar*. Ce signe est
unique dans les six cent quarante pages du livre. `travail/subvorti.txt` porte
ce rattachement ; l'article rattaché devient une sous-entrée de son voisin, sans
rien perdre — ni domaine, ni code de langues, ni page.

L'auteur numérote ses sens de trois façons — *1.*, *I.*, et parfois entre
parenthèses, *(1) … (2) …*. Cette dernière forme tient le plus souvent en une
seule phrase, les morceaux séparés d'un point-virgule ou d'un deux-points ; on
la laisse telle quelle, comme l'a écrite l'auteur. Mais le **premier** de ces
numéros suit la vedette, là où l'analyse cherche le domaine : il y partait, et
en était écarté comme numéro. L'entrée perdait alors son *(1)* en gardant son
*(2)* — *ramo*, *romano*, *vice*, les trois seuls du livre. La numérotation
restée seule ne renseignait plus personne : le sens est maintenant coupé à sa
place, et les éditions le renumérotent comme les autres. De même, le numéro
collé au qualificatif — *leono. I (zool.) Mamifero karnivora…* — restait dans le
texte, où il doublait celui que les éditions posent : il tombe désormais comme
les autres, dans six entrées.

### Le code de langues (`kodo`, `lingui`)

La dernière chose de l'article : `- DEFIRS.`, une lettre par langue —
**D**eutsch, **E**nglish, **F**rançais, **I**taliano, **R**usse,
e**S**pañol —, puis `L` pour le latin, que quatre-vingt-douze codes mettent en
dernier. Cet ordre est celui du livre : 8 407 codes s'y tiennent, 22 le
rompaient. L'édition les y remet — `DEFSR` chez *alibio*, `ED` chez *sendar*,
`FISDE` chez *grano*, et `dEFIRS`, `DEFlS` où la capitale et le `I` avaient été
abîmés à la lecture. Rien ne s'y répétait : c'était l'ordre seul qui différait,
et la ligne brute garde la graphie de la page.

Quelques notations **épellent** la langue au lieu de l'abréger — `FDSued`,
`DERPol`, `Gr`, `Ned`, `Jap.,Sanskr.` Ce ne sont pas des suites de lettres, et
l'ordre ne les touche pas.

Le code n'est pas toujours **au bout**. L'auteur l'a parfois posé après un
premier sens et a continué — *cilio. (anat.) Pilo… — F. (bot.) Sorto di pilo…
— F.* —, ou la frappe a laissé une scorie derrière lui — *— DE. s q c i* chez
*hidranto*. Le code restait alors au milieu de la définition, où il n'a rien à
faire, et l'entrée passait pour `sen-lingua`. Il en est tiré dans **dix**
entrées, et le sens se coupe à sa place quand ce qui suit en ouvre un autre —
un domaine entre parenthèses, un tiret suivi d'une capitale. On ne touche qu'à
deux cas sûrs : l'entrée n'a pas de code, ou elle porte déjà le même. Un code
**différent** au milieu du texte est autre chose : chez *staciono*,
*(autofiakri — F. taxi — autobusi, e c.)* donne le mot français, il ne clôt pas
l'article.

Aucun code ne nomme deux fois la même langue. C'est ce qui permet de le
distinguer de ce qui lui ressemble à cette place : un **numéro de sens** que la
fin d'article laisse pendre. *forsan*, *xenio*, *-ajo* et *ek* annonçaient un
sens `II.` ou `III.` que la dactylo n'a pas frappé, ou que la ligne suivante
portait ; l'édition en faisait « Italiana, Italiana ». Elle refuse maintenant
tout code qui répète une langue, et les quatre articles retrouvent leurs sens —
*-ajo* en avait cinq, il n'en montrait plus que quatre.

Le même ordre répare deux codes mal lus : `EFIES` et `DEFIES` répètent l'anglais
là où la place, entre `I` et `S`, ne peut être que `R`. `travail/texti.txt`
porte les deux lectures, `EFIRS` et `DEFIRS`.

### Le domaine (`fako`)

C'est la parenthèse qui suit la vedette — *(bot.)*, *(trans.)*, *(en la epoki
antiqua)*. Le champ la porte **nue**, sans ses parenthèses ; les deux éditions
les remettent. L'auteur ne s'étant uniformisé ni sur la majuscule ni sur le
point, l'édition le fait pour lui : minuscule initiale — sauf les noms propres,
*Italia*, *Voltaire*, *Diana*, et les adjectifs de langue, listés dans `PROPRA`
—, et point rendu à l'abréviation d'après une liste explicite (`MALLONGIGI`
dans `outils/edition.py`), non d'après une règle sur la finale, car le même
champ contient des prépositions, des verbes et jusqu'à une formule chimique.

Deux parenthèses de suite — *pensar. (trans. e netrans.) (ulo, ad ulo, pri ulu
od ulo)* — sont deux moitiés du même renseignement : le régime appartient au
marqueur de transitivité, non à la définition, qui commençait sinon par une
parenthèse orpheline. Le champ les garde toutes deux, séparées par `) (`. La
seconde reçoit **le même traitement que la première** : *(trans.) (tekn)* et
*(netrans.) (Kemio)* s'écrivent désormais *(trans.) (tekn.)* et *(netrans.)
(kemio)*, comme leurs quatre-vingt-douze voisines.

Ce qui se trouve à cette place n'est pas toujours un domaine, et l'édition écarte
trois intrus : le **numéro de sens** — *romano. (I) Verko literaturala…* —, y
compris quand il précède un vrai domaine, *ramo. (1) (bot.)* ; la **formule
chimique**, qui va au champ du symbole ; et la **lettre élidée** de *ka(d)*, qui
appartient au mot.

Restaient les variantes de l'auteur lui-même : *anatom.* une fois contre
*anat.* 229 fois, *medicino* quatorze fois contre *medic.* trente-deux,
*yuro-cienco* quinze fois contre *yurocienco* vingt-quatre. Ce ne sont pas des
erreurs de lecture — c'est l'auteur qui ne s'est pas uniformisé, sur quarante
ans de fiches. **L'édition retient la forme qu'il emploie le plus**, et quand
les deux sont à moins du double l'une de l'autre, l'abrégée l'emporte : le
livre abrège ses domaines 2 463 fois contre 746 où il les écrit au long, et
l'abréviation est donc sa manière. La table est explicite, une ligne par
variante avec les deux comptes en regard — `DOMENI_UNIFORMA` dans
`outils/edition.py` —, et elle vaut aussi pour les domaines écrits **dans** un
sens, hors du champ. 158 entrées et 67 sens y ont changé de forme.

Ne sont **pas** dans cette table les formes que rien ne dit équivalentes :
*tekn.* et *teknol.*, *fiz.* et *fiziol.*, *paleont.* et *paleogr.*, *milit.*
et *milit-arto*, *elektro* et *elektrotekniko* sont des domaines distincts. Et
seule une composante **entière** est remplacée : le champ énumère parfois deux
domaines — *(arit., algeb.)*, *(fiz. e geom.)* —, chacun compte pour une
composante, mais une composante de plusieurs mots est une phrase de l'auteur —
*ante la milito universala di 1914-18* garde son mot.

Le trait de la dactylo, lui, porte la forme de la **page** : *medicino*
souligné là où le texte rendu porte *medic.*. Cherché tel quel il ne se
retrouvait plus, et le domaine perdait son italique ; il est donc cherché aussi
sous la forme retenue. Le compte des soulignements non placés tombe de 1 762 à
1 713, et 14 italiques de plus trouvent leur place.

Le **nom scientifique** demande la même tolérance, et pour la même raison : le
filet couvre `agrimonia` puis `eupatoria`, ou se rompt en fin de ligne sur
`allium fistu-` et `losum`, là où le champ porte le binôme entier. Cherchés au
caractère près, ces 139 fragments passaient pour non placés ; ils sont
reconnus dès quatre lettres. Le compte tombe à **1 574**.

### Le nom scientifique (`latina`)

Le tapuscrit l'annonce par un `L.` — *L. cynocephalus*. Deux pièges, tous deux
rencontrés :

- un `L.` peut introduire un **exemple**, non le nom de l'article :
  *enklitiko … Kom ex.: L. que en neque ; ne en venisne ; F. ce en est-ce*.
  Pris pour un binôme, il quittait la définition — qui restait sur « Kom ex.; »
  — pour aller s'afficher en nom latin. Un `L.` précédé de `ex.` est désormais
  laissé au texte ;
- le `L.` perd parfois son point — *…puteo-kordegi.- L tilia* chez *tilio*. On
  l'admet sans lui, mais alors seulement devant une **minuscule** : *— La
  persono qua…*, *— Longa bastono…* ouvrent une définition, et le `L` y
  prendrait la première lettre du mot ;
- le nom se termine souvent sur `.-` sans espace — *L. viverra genetis.- II.
  (tekn.)…* chez *jineto*. Sans le tiret dans ce qui peut suivre le point, le
  nom restait dans la définition de quatorze entrées ;
- le nom donne parfois **deux formes**, séparées d'une virgule — *L. rubus
  caesius, rubus fructicosus*, *L. anas, anatis* —, et jusqu'à une glose de
  l'auteur : *L. conium maculatum, e speco di cicuta*. N'en prendre qu'une
  laissait le reste dans la définition, précédé de la virgule orpheline du nom :
  *« … (rovbero). , rubus fructicosus »*. La seconde forme est admise entière ;
- le nom n'en est pas toujours un : *oktopodo* porte « — L. octo- », sans
  suite — l'original aussi. L'auteur y donne l'**élément** latin, non un binôme,
  et le trait d'union final le dit ; le rognage des fins de ligne l'emportait ;
- la dactylo coupe parfois un mot en deux : *capparia spi nosa* pour *capparia
  spinosa*. Ni `spi` ni `nosa` n'étant des mots latins, la machine ne peut pas
  le savoir. `travail/latinaji.txt` porte les noms redressés à l'œil, avec la
  clé de `simboli.txt` — `vedetto@image:ligno` — et l'emporte sur le décodage.

#### Le nom lu pour un autre

Six genres portaient une lettre pour une autre, et le livre lui-même fournit la
preuve : l'auteur a **transcrit** le nom latin en ido, et sa vedette porte la
lettre que le nom avait perdue.

| article | lu | rendu | ce qui le prouve |
|---|---|---|---|
| `mirmekofago` | *myrmedophaga* | *myrmecophaga* | la vedette dit *mirmeko-*, et `mirmekoleono` écrit *myrmecoleon* |
| `cetonio` | *catonia* | *cetonia* | la vedette dit *cetonio* |
| `faleno` | *phanaena* | *phalaena* | la vedette dit *faleno*, avec son *l* |
| `motacilo` | *molacilla alba* | *motacilla alba* | la vedette dit *motacilo*, avec son *t* |
| `kaprimulgo` | *caprimalgus* | *caprimulgus* | la vedette dit *kaprimulgo*, avec son *u* |
| `kokoso` | *cocus nucifera* | *cocos nucifera* | la vedette dit *kokoso*, et le genre est *Cocos* |
| `moskardino` | *avelianarius* | *avellanarius* | le double *l* pris pour *li* ; le genre *Muscardinus* n'a qu'une espèce |
| `fritilario` | *fritilius* | *fritillus* | le double *l* pris pour *li*, comme chez `moskardino` |

Ils sont sortis d'un contrôle qui vaut d'être gardé : comparer chaque genre à sa
vedette, une fois l'un et l'autre ramenés à la même graphie (*ph* → *f*, *c* →
*k*, *y* → *i*…). Sur les 823 noms, trente-cinq diffèrent d'une seule lettre ;
vingt-neuf de ces écarts sont la différence normale entre le mot ido et le latin
— *abieto* / *abies*, *elefanto* / *elephas* —, six étaient des lectures.

Un mot du dictionnaire ne suit pas la règle : `fritilario` porte *fritillus*, le
cornet à dés du latin, dont le damier des pétales a donné son nom au genre
*Fritillaria*. Ce n'est donc pas un taxon, mais le livre cite ailleurs le mot
latin nu — *anas, anatis* chez `anado`, avec son génitif. La finale en *-us* est
d'ailleurs celle que la ligne porte, et une lecture ne l'inventerait pas : la
correction ne change qu'une lettre, le double *l* pris pour *li*, comme chez
`moskardino`.

Le relevé du filet, lui, porte la lecture de la **machine** : corrigé, le champ
ne s'y retrouvait plus et le nom perdait sa place. La comparaison tolère donc
**une lettre** d'écart — exactement ce qu'une correction de lecture change. Elle
rattrape du même coup treize filets brisés par une fin de ligne : *anto* pour
*dianthus*, *glefino* pour *aeglefinus*, *aci-* pour *acipenser*.

### Le symbole chimique (`simbolo`)

Quatre-vingt-neuf articles donnent le symbole ou la formule d'un corps. Le
livre l'écrivait de **onze façons** : avec ou sans tiret, capitale ou
minuscule, deux-points ou point, parfois en incise entre parenthèses, et
l'étiquette elle-même sous quatre graphies — `Simbolo kemiala`, `Simb.
kemiala`, `Simbolo kem.`, `Simb. kem.` Pire que l'inégalité : là où l'auteur avait souligné
l'étiquette, `Simbolo kemiala :` a exactement la forme d'une locution —
capitale, deux-points, définition — et s'en allait **ouvrir un alinéa de
sous-entrée dans soixante articles**, encombrant d'autant l'index de
recherche.

Or ce n'est pas un mot de la langue mais une étiquette, de même nature que le
nom latin. Elle a donc son champ, `simbolo`, et les deux éditions la rendent
d'une seule façon — l'étiquette en italique, le symbole **droit**, une formule
penchée se lisant mal. **90 articles** le portent — les 89 que le livre annonce par l'étiquette, plus `asparagino`, qui pose sa formule entre parenthèses juste après la vedette.

Onze articles portaient l'étiquette sans son symbole : le décodage l'avait
perdue. Ces onze-là, plus un douzième que le décodage n'avait lu qu'à moitié
(`fluorino` : `Ca` pour `Ca F²`), ont été **relevés à l'œil sur le fac-similé**
et posés dans `travail/simboli.txt`, avec le folio imprimé en regard pour qu'on
puisse y retourner. La clé y est celle de `subvorti.txt` — `vedetto@image:ligno`
—, et une valeur posée là l'emporte sur ce que le décodage aurait lu.

`ruteno` faisait exception : l'article suivant, `rutino`, s'était fondu dans
son texte, et l'étiquette y ouvrait un faux alinéa de sous-entrée. La cause
était en amont — la dactylo avait fermé la vedette `rutino,` d'une **virgule**
au lieu d'un point, si bien que le découpage n'y voyait pas un article. Le
filet était pourtant là, et la ligne blanche aussi. `RE_VED` admet désormais la
virgule : sur les 639 pages, une seule ligne suit une ligne blanche en se
présentant « mot, », celle-là — la tolérance ne coûte aucun faux positif.

**`iridio`** avait son étiquette en incise au milieu d'une phrase ; elle est
extraite comme les autres, et la phrase se referme sur elle-même.

### La parenthèse qui fait corps avec le mot

L'auteur note l'élément facultatif entre parenthèses, au milieu du mot :
*leon(in)o* dit le lion et la lionne, *formac(es)o* la formation et le fait de
se former, *-(ant)ajo* le suffixe composé. La règle qui détache une parenthèse
fermante collée au mot suivant — *(aludante persono)Definuro* — coupait ces
trois-là en deux. Elle épargne désormais celle que précède le tiret d'affixe, et
celle que suit une lettre **seule** : la finale du mot. *F(z) esas monodroma*
porte déjà son espace, et n'est pas touché.

### La croix de la dactylo : astérisque ou plus

La machine à écrire n'avait pas d'astérisque. Pour marquer les mots **non
officiels** — ceux qu'il propose sans les donner pour acquis — l'auteur frappe
une croix, `+`, que l'édition rend par l'astérisque de la tradition ido. Elle
porte sur la vedette (*\*grandoro*, *\*stencilo*, *\*kluza*, *\*sesiono*) comme sur
les mots cités dans les définitions. **253 occurrences dans les
définitions**, dont 45 posées par mise au net — voir plus bas.

Mais la même touche sert le **plus de l'algèbre**, et rien dans le signe ne les
distingue. C'est la frappe qui les distingue :

> La marque est **collée** au mot qu'elle marque — la dactylo ne laissait pas
> d'espace : *pri+grandoro*, *sur+stencilo*, *vazo+kluza*, *o+sesiono*. Détachée,
> elle n'est la marque que si elle **ouvre** le fragment ou suit une parenthèse
> ouvrante — *legi (+ leyi)* chez `cienco`, *+ prei*. Entre deux termes, c'est
> une addition.

Le contrôle est dans le livre lui-même : *grandoro*, *stencilo*, *kluza*,
*sesiono* y sont vedettes, et **marquées non officielles à leur place
alphabétique**. La règle qui prenait toute croix pour la marque posait quatre
astérisques sur des inconnues — *ax² \*bx \*c = 0* chez `diskriminanto`,
*a \*b i e a' \*b' i* chez `konjugar`, *a² = b² \*c* chez `pitagorala`. Elles sont
rendues à l'arithmétique ; chez `konjugar`, le filet *a' + b' i* retrouve du
même coup son texte et passe des fragments douteux à l'italique.

**La marque se porte partout où le mot est cité.** L'auteur la pose à la
vedette — le mot non officiel a sa place alphabétique comme un autre — et aussi
dans les définitions, mais pas toujours : *werar* y est marqué cinquante fois
et nu six fois, *publico* cinq fois et nu une, *grandoro* quatre fois et nu six.
Le lecteur voyait le même mot tantôt signalé, tantôt non. On aligne sur la
marque — **quatorze mots, 45 emplois** —, et seulement pour les mots où
l'auteur l'a lui-même posée au moins une fois : là où il ne l'a jamais posée
(*pondar*, *niuzo*, *golfo*, *tarda*, *intrenar*), l'ajouter serait une
affirmation neuve et non une mise au net. L'article du mot lui-même est laissé
tel quel — sa vedette porte déjà la marque.

Un quarante-sixième emploi demandait d'abord une lecture : chez `tuberkulo`,
la croix est frappée **derrière** le mot — *(kartofli+ - terpomi - patati…* —
là où le livre la pose partout ailleurs devant. Corrigé par `travail/texti.txt`.

Le filet de la dactylo, lui, a été relevé avant que l'astérisque soit posée :
*pri grandoro* ne se retrouvait plus dans *(pri \*grandoro)*. La recherche du
fragment souligné la laisse donc passer entre les mots.

Une croix restait, qui n'était ni l'une ni l'autre : chez `ecentrika`, *de pn +n
donita*. Cinq caractères pour un mot de cinq lettres — c'est **punto**, et la
définition le dit : *Di qua la centro eskartesas de punto donita*, le centre qui
s'écarte d'un point donné. La correction est dans `travail/texti.txt`.

### Le filet que l'œil écarte

La dactylo souligne le domaine, la locution, le mot cité, le nom scientifique.
Le relevé, lui, prend aussi ce qui n'est pas une intention : le trait d'une
ligne voisine, ou qui déborde d'un mot sur le suivant. Deux fois, un mot plein
s'est ainsi retrouvé en italique au milieu d'une définition — *Agar* chez
`sordino`, où le trait de *(metaf.)* a mordu sur le mot suivant, et *multa* chez
`ja`, où le même trait de travers a laissé derrière lui *kan*, morceau de
*kande*.

**Aucune règle ne peut les distinguer** d'un mot cité : le livre en cite
beaucoup, et souvent un seul mot — *Ido* chez `logiko`, *ohm* chez `volto`,
*multa* chez `kelka`, où il oppose justement *kelka* à *multa* et à *plura*.
Cent quarante-deux italiques ne couvrent qu'un mot, et la grande majorité sont
légitimes.

Ils s'écartent donc **un par un**, dans `travail/filetoj.txt`, avec le motif en
regard.

**L'inverse arrive aussi** : le trait était là, et le relevé ne l'a pas rendu.
Chez `anakoluto`, l'article définit l'anacoluthe comme l'omission de *ta* devant
*qua* — *La omiso di ta avan qua esas anakoluto*. Les deux mots y sont **cités**,
non employés, et sans l'italique la phrase se lit de travers. Le relevé n'a
rendu sur cette ligne que le *Qua* du vers de Voltaire et un *est* que rien ne
place : le trait y était, mais lu de travers.

Une ligne du même fichier pose alors l'italique, les **accolades** entourant ce
qui la prend et le reste servant de **contexte** :

```
anakoluto@33:15   La omiso di {ta} avan {qua} esas anakoluto
```

Le contexte n'est pas décoratif : sans lui, *qua* serait mis en italique aux
trois endroits où il paraît dans l'article, dont deux où il est un pronom
ordinaire. Le champ `kursiva`, lui, ne recense que les filets de la dactylo :
une italique posée à l'œil est celle de l'éditeur, et c'est `filetoj.txt` qui en
tient le compte.

**Les deux directions se combinent.** Chez `prostezo`, l'article démontre la
prothèse par quatre paires — *ica vice ca*, *iscala vice scala*, *lierre vice
ierre*. La dactylo a souligné *ica* comme les autres, mais la règle des
mots-outils l'écartait, *ica* étant aussi un démonstratif ordinaire ; et *ca*,
le trait ne l'avait pas rendu. Une ligne retire le relevé de la liste des filets
non placés — il n'y avait pas sa place, il est bon —, une seconde repose
l'italique sur les deux mots :

```
prostezo@473:41   ica
prostezo@473:41   {ica} vice {ca}, en L.
```

C'est le cas qui montre pourquoi cette couche est nécessaire : aucune règle ne
distingue le *ica* cité de `prostezo` du *ica* pronom qui court dans le reste du
livre.

### Le filet qui ne couvre que des mots-outils

`absinto` portait *ek la* en italique au milieu de sa définition. Le garde-fou
existait — un fragment qui n'est **qu'un** mot-outil ne reçoit pas d'italique —
mais il ne voyait qu'un mot à la fois : *ek la*, qui en fait deux, passait au
travers.

La règle porte maintenant sur **tous** les mots du fragment, contre une liste
close — articles, prépositions, conjonctions, pronoms, corrélatifs, formes de
*esar*. Un mot plein n'y entre pas, même court : *Ido* chez `logiko`, *ohm* chez
`volto`, *tri* chez `tri-` sont des mots cités et gardent leur italique.

Quatre mots-outils en sont retirés, parce que le livre les **cite** quelque part
et que le filet y est une vraie marque : *ante* chez `avan` — « kontre ke ante
relatas tempo » —, *avan* et *dop* chez `retro-`, et *que* chez `enklitiko`, où
il est latin : « L. que en neque ».

**Vingt-deux italiques** partent — *ula*, *onu*, *qui*, *a lu*, *od a*, *de la*,
*a la*, *e lo*… Elles ne disparaissent pas : elles rejoignent les fragments non
placés, sous la famille « mots-outils seuls » de `filets-dubinda.md`, qui compte
désormais 49 entrées. La liste de travail et l'édition se règlent sur la même
liste de mots.

### La numérotation des sens, jusqu'à VIII

Le découpage des sens s'arrêtait au chiffre **VI**. Quatre articles vont plus
loin — `punto`, `exemplo` et `lineo` ont sept sens, `modo` en a huit — et leur
dernier sens restait collé au précédent, son numéro au milieu du texte :
*« … pos singla gano-stroko. -VII.(tipogr.) Mezuro qua determinas… »*. La règle
couvre maintenant V, VI, VII et VIII d'un seul tenant, comme le faisait déjà
celle qui **ôte** le numéro en tête de sens. Le livre ne va pas au-delà : aucun
article ne porte de IX.

Chez `modo`, le sens VII ouvre sur son domaine puis se subdivise en chiffres
arabes — *VII. (muziko). 1. … 2. …*. Les deux sous-sens deviennent des sens à
part entière, et VII se réduit à son qualificatif : c'est la forme que le livre
donne déjà à trois autres sens — *(anke metaf.)* chez `lurar`, *(videz « e »)*
chez `ed`, *(sinonimo di « spermatozoido »)* chez `zoospermo`.

### L'accent, que l'ido ne porte pas

Le tapuscrit n'accentue que ce qu'il **cite** d'une autre langue — *avoué*,
*ampère*, *noël*, *poële*, *coöperation*, *Brüder* —, les **noms propres** —
Linné, Panthéon, Eugène Pottier, André Lalande, Bémont, Plättner — et les trois
articles qui parlent des signes eux-mêmes : `diakritika`, `cirkonflexo`,
`tremao`, plus le *la e là* français de `grava`. Partout ailleurs, un accent est
une lecture.

**Dix mots** ido ou latins en portaient un sans raison. Sept étaient déjà
redressés en aval — six par la relecture (*redigás* → *redigas*, *éxter* →
*exter*, *karakterizáta* → *karakterizata*…), et un par le jugement lexical, qui
lit dans le *à* de `kondutar` le **o** de l'alternative : *en ta o ca
cirkonstanco*, et non un *a* accentué. Restent les trois que rien ne voyait :
*(à)* chez `sordino`, *liliacéi* chez `tulipo`, *lábiacei* chez `yuko`.

Les deux derniers sont **entre guillemets**, ce qui interdit d'en faire une
règle — la citation est justement ce qui autorise l'accent ailleurs. On les
relève donc un à un, dans `travail/texti.txt`. Après quoi il ne reste, dans les
deux éditions, que des accents qui se justifient.

### Le tiret d'affixe détaché de son affixe

Chez `metro`, *1/10.000.000- ima* est *1/10.000.000-**ima***, la dix-millionième
partie. C'est l'espace parasite que la vedette connaît déjà — *« - as. »* pour
*-as*, *« bo - . »* pour *bo-* —, posée cette fois dans le corps.

On exige un **suffixe suivi de sa désinence**, sans quoi *radio- o
televizionorecevili* (`megafono`), où le tiret reste en suspens devant la
conjonction, se recollait en *radio-o*. Un seul cas dans le livre ; les quatre
autres tirets isolés — *ekirar- per*, *perforuro- e*, *implikas- kontre*,
*establisita- ube* — ne sont pas des affixes mais des tirets mis pour une
virgule, et restent tels quels.

### Le filet coupé par une fin de ligne

La dactylo souligne *Kreto-krayono* ; la ligne casse au milieu du mot, et le
relevé rend deux morceaux — *Kreto-kra-* puis *yono*. Cherché tel quel, aucun
des deux ne se retrouve dans le texte recollé : les deux moitiés finissaient
parmi les fragments non placés, et la **sous-entrée** qu'elles désignaient
n'était pas reconnue.

On les recolle quand la forme jointe, elle, se trouve dans le texte — avec ou
sans le trait d'union, selon ce que le recollage a décidé. La condition est donc
la même que pour poser l'italique, et un tiret final qui n'annonce aucune
coupure (*-ez-*, *auto -*) ne trompe pas la règle : ce qui ne se retrouve pas
reste tel quel. **Vingt-neuf filets** recollés, **22 fragments** de moins parmi
les non placés, et deux sous-entrées de plus : `kreto-krayono` et
`ordonancoficiro`.

### Le classement du dictionnaire de poche

Le livre imprimé suit l'ordre du tapuscrit, avec ses erreurs de classement — la
liste `ordino-ruptita` les relève. Le dictionnaire de poche, lui, **reclasse** :
c'est une édition de lecture, on y cherche un mot.

Il le faisait avec sa propre clé, qui ne connaissait ni les guillemets ni
l'espace. *« brokoli »-kaulo* se rangeait donc **après `z`**, et l'article se
composait tout à la fin du livre, derrière *zumar*, à cent cinquante pages de sa
place. La clé est désormais celle du dictionnaire lui-même, `_klavo_ordino` —
la règle du livre, sans l'astérisque du mot non officiel, sans le tiret de
l'affixe, sans le point d'exclamation de l'interjection, sans les guillemets ni
les espaces. **Cent une vedettes** changent de rang : les affixes à tiret final,
les interjections, et les locutions latines, que le livre range comme un seul
mot — *a posteriori* entre *apostata* et *apostilo*, *ex libris* entre *exkuzar*
et *exodo*.

Le classement de poche et la liste de travail se mesurent maintenant à la même
clé, et ne peuvent plus diverger.

### Le composé soudé par le recollage

Quand le mot coupé en fin de ligne est un **composé**, le trait d'union lui
appartient, et le recollage l'ôte à tort : *Ordonanc-* plus *oficiro* donnait
*ordonancoficiro*. Le livre, lui, pose le trait à tous ses composés —
*banko-komerco*, *natur-historio*, *politiko-yuro*, *milit-arto*,
*skerm-arto* —, et les deux éléments sont ici vedettes l'un et l'autre.

Trois sites, tous montrés par le relevé du filet, qui donne la place exacte de
la cassure :

| article | lu | rendu | ce qui le prouve |
|---|---|---|---|
| `ordonanco` | *ordonancoficiro* | *ordonanc-oficiro* | `ordonanco` et `oficiro` sont vedettes |
| `invalida` | *exmilitisto* | *ex-militisto* | `ex-` est vedette, et `korsaro` écrit *ex-pirato* |
| `saturnali` | *niaepoke* | *nia-epoke* | le livre écrit *nia-epoke* huit fois |

La règle générale, elle, **n'a pas été retouchée** : `recoller` tranche sur le
lexique des vedettes, et son jugement ne peut se remesurer sans le fac-similé,
absent du dépôt. Les trois corrections passent donc par `travail/texti.txt`,
chacune avec sa preuve.

Deux domaines composés restaient soudés là où le livre écrit tous les autres
avec le trait : `yurocienco` et `imprimarto`. Ils s'alignent — **43 champs
`fako`** et les quatre emplois en texte courant.

### Le tiret de séparation devant la parenthèse

L'auteur sépare ses sens d'un tiret encadré de deux espaces, et le sens suivant
s'ouvre souvent sur son domaine entre parenthèses : *…tro granda. – (cinemo)
Telo blanka…*. Il l'écrit ainsi quatre-vingt-cinq fois ; **treize fois** l'une
des deux espaces manque — *granda. -(cinemo)* chez `skreno`, *direte.- (metaf.)*
chez `intuicar`, *marnavigado- (an busolo)* chez `klinometro`. On les rend, et
la règle du demi-cadratin fait le reste.

La parenthèse d'un **affixe** n'est pas de celles-là : dans *= -(at)ajo* et
*equivalas -(ant)ajo*, le mot continue après la fermante, et le tiret lui
appartient. La règle les laisse.

### Les points de suspension, et l'affixe qui les suit

La machine n'avait pas le caractère unique : l'auteur frappe trois points,
parfois quatre. L'édition pose `…` partout — **96 occurrences**, plus aucune
suite de points dans les deux éditions.

Ces points tiennent la place d'un mot, et souvent ce qui les suit est une
**désinence ou un suffixe**, non un mot : *quik…onta*, *esar…ata*, *t. e.
…is…inta*. La forme juste, le livre l'écrit lui-même chez `min` — *ne tam
multe …-a* — et chez `quadri-` — *Qua havas quar…-i* : une espace, puis le
tiret d'affixe. On la généralise :

> Une **désinence** qui suit les points s'en détache par une espace et prend le
> tiret : *quik… -onta*, *esar… -ata*, *… -is… -inta*. Un **mot** ne prend que
> l'espace : *lasas … efikar*, *preferar… kam*, *lore… lore*.

La liste des désinences est **close**, et les désinences d'**une lettre** n'y
sont pas : *-o*, *-a*, *-e*, *-i* sont aussi les mots-outils les plus courants
du livre, et *Esar prezenta ye… e regardar* porte la conjonction, non la
finale. Là où l'auteur veut la désinence d'une lettre, il a frappé le tiret
lui-même. On ne se fie pas non plus à la forme : *esante* se découpe en *es-*
plus *-ante* sans être pour autant un suffixe suivi d'une désinence.

Dix sites prennent le tiret, dans huit articles — `-ig-`, `-ind-`, `min`,
`\*pliz`, `plusquamperfekto`, `pronta`, `quadri-`, et le champ `fako`
d'`elektar`. Un seul demandait d'abord une lecture : chez `\*pliz`, *ke
lu....+ez* portait la croix là où le tiret devait être, et l'édition imprimait
*lu....\*ez*. Corrigé par `travail/texti.txt`.

Les points **finissent** parfois l'article — ils tiennent la place du
complément que la définition appelle : *Kambie di…* (`po`), *Qua havas tri…*
(`tri-`), *Profite da… Destine di…* (`por`). Le balayage qui nettoie la fin de
la chaîne — celui qui retire le bruit derrière le code de langues, *« - DEFIRS.
--- »* — les emportait, sauf là où un guillemet fermant les protégeait. Il
s'arrête désormais devant eux : **huit articles** retrouvent leur ellipse
finale, et `nona-` le trait d'union qui partait avec (*= non-…*).

Un relevé de filet est brut quand le texte, lui, est typographié : *lore...lore*
ne s'y retrouvait plus et perdait son italique. La recherche essaie donc aussi
la forme typographiée du relevé, comme elle essaie déjà la forme retenue d'un
domaine.

### Les parenthèses orphelines

Le tapuscrit laisse cent vingt parenthèses sans leur paire. Elles ne sont pas
décoratives : le rendu du domaine de tête et celui de l'italique s'appuient
dessus, et une incise laissée ouverte pend dans la page comme dans le PDF. Le
fac-similé ne les rend pas — **l'original ne les a pas non plus**. Il faut donc
trancher, et la règle est celle qu'`orfa_parentezo` posait déjà :

> Quand la paire est **déterminée**, on la fournit. Sinon, **on retire le signe
> orphelin** — le retirer n'invente aucun groupement que l'auteur n'a pas fait ;
> en ajouter un, si.

Trois cas où la paire est déterminée, donc fournie :

- le sens s'achève **dans** la dernière parenthèse ouverte, tout ce qui précède
  étant équilibré — la fermante s'est perdue en fin de ligne (65 sens,
  `fermi_parentezon`) ;
- le **qualificatif de tête** — `(trans. Kustumigar…`, `(anat. Saliajo…` — que
  le livre ferme des centaines de fois juste après l'abréviation. L'espace a pu
  tomber avec la fermante : `(bot.Frukto kapsula…` chez `folikulo`. Une
  **capitale** collée au point de l'abréviation ouvre la définition, elle ne
  continue pas le mot abrégé ; sans cela la parenthèse se fermait au bout du
  sens et le domaine avalait toute la définition ;
- le **signe doublé**, `((anke metaf.)` ou `Dekart'))`, une double frappe.

Pour le reste, le signe orphelin part. La fermante seule a d'ailleurs le plus
souvent une cause connue : elle fermait le **nom latin**, et l'extraction de
`latina` a emporté l'ouvrante avec son contenu — `oranjo` garde *citrus
aurantium* dans son champ, et n'avait plus qu'une parenthèse fermante devant
rien. Le contenu n'a pas disparu, il a changé de champ.

**Un sens reste déséquilibré, et c'est voulu** : chez `inflexar`, la
parenthèse ouvre une **locution** — « (arko inflexita : … » — que la page,
tronquée, n'a jamais close. La retirer ferait disparaître une sous-entrée ; on
laisse le sens entier, fût-il boiteux.

### Les soulignements de l'auteur (`sublineita`, `kursiva`, `dubinda`)

Le tapuscrit n'a pas d'italique : **la dactylo souligne**. Elle souligne ce
qu'une imprimerie aurait mis en italique — le domaine, le nom scientifique, le
mot cité, la locution. Le relevé des filets donne, ligne par ligne, des plages
de colonnes ; il suffit d'y lire le texte.

| champ | ce que c'est |
|---|---|
| `sublineita` | tout ce qui est souligné dans l'entrée, remis bout à bout, les coupures de fin de ligne recollées. 6 542 entrées |
| `kursiva` | ceux que l'édition a **su placer** dans le texte, et qu'elle rend en italique. 1 246 entrées |
| `dubinda` | ceux qu'elle **n'a pas su placer** : le fragment ne se retrouve pas tel quel, ou ne couvre que des mots-outils. 1 406 entrées, 1 558 fragments |

Un souligné n'est ni `kursiva` ni `dubinda` quand il a trouvé sa place ailleurs
— dans `fako`, dans `latina`, dans `simbolo`, ou comme locution. C'est le cas de *cinocefalo*
ci-dessus : ses deux soulignés sont devenus son domaine et son nom latin.

`strukt` porte, à côté de chaque `teksto`, un `teksto_k` : le même texte avec
deux bornes invisibles, `U+E000` et `U+E001`, autour de ce qui va en italique.
Les éditions les traduisent, `<i>` pour le HTML et `\textit` pour le PDF ; qui
lit la base peut les ignorer ou les ôter.

```
teksto   : Pikanta ed atakema (metaf.)
teksto_k : Pikanta ed atakema \ue000(metaf.)\ue001
```

`filets-dubinda.md` classe les 1 558 fragments non placés par famille, la plus
douteuse en tête, avec la page et la vedette pour aller voir le fac-similé. Une
seule famille demande un arbitrage — 18 fragments qui ressemblent à un
qualificatif ou à une locution ; les autres sont des artefacts du relevé, où le
trait déborde ou s'arrête trop tôt. `python3 outils/releve_filets.py` le
reconstruit.

---

## Les drapeaux : la liste de travail

Le décodage est exact à **98,7 % par caractère**, mesuré sur une page transcrite
à la main et tenue hors de tout apprentissage. Ce n'est pas assez pour un
dictionnaire. Plutôt que de masquer ce qui reste, la base le **signale** :

| drapeau | entrées | ce qu'il veut dire |
|---|---|---|
| `ordino-ruptita` | 55 | **la vedette rompt l'ordre alphabétique** |
| `sen-lingua` | 1 031 | pas de code de langues final — souvent normal, le livre n'en donne pas toujours |
| `finalo-nekustumala` | 54 | finale étrangère à la morphologie d'Ido (-o, -a, -e, -i, -ar, -ir, -or). Trois familles en sont **exemptées**, la question n'ayant de sens que pour un mot de la langue : l'affixe (`-eyo`, `poli-`), le mot que le livre déclare lui-même grammatical (*« an. Prepoziciono qua… »*), et l'emprunt cité (`amen`, `cambium`). Ce qui reste — numéraux `cent` et `dek`, noms de notes `b`, `c`, `d` — est légitime aussi, mais rien dans le texte ne permet de le dire |
| `pagino-nefidinda` | 32 | pages 539-540, photographiées à une autre échelle, décodage nettement moins sûr |
| `artiklo-dividita` | 21 | l'article était coupé par un saut de page ; les deux moitiés ont été recollées |
| `sen-chefvorto` | 0 | l'entrée n'a pas de vedette lisible — plus aucun cas |

**8 306 entrées ne portent aucun drapeau.**

`korektita` a cessé d'être un drapeau : il disait « au moins une cellule
corrigée automatiquement », une provenance et non un doute, et toutes les
définitions ayant été relues une à une il ne désignait plus de travail restant.
Le compte reste dans le champ `korektita`, pour qui veut mesurer : 6 284 entrées
en portent au moins une.

Le drapeau d'ordre se lit sur la vedette **rangée**, sa marque de tête ôtée :
l'astérisque du mot non officiel et le tiret de l'affixe ne sont pas des
lettres, et le livre ne les range pas — `-acho` est entre `acetono` et
`aciano`. Comparés tels quels, ils passaient avant toute lettre, et chacun des
126 affixes et mots non officiels rompait l'ordre par sa seule marque. Le tiret
**final** du suffixe ne compte pas davantage — `-an-` se range avec `an` —, ni
l'accent d'un nom emprunté — `ampèremetro` précède `ampla` —, ni l'espace.

Et surtout : **la désinence ne compte pas**. C'est une règle que le livre
n'énonce pas, mais qu'il suit — `aktinio` précède `aktinika` parce que l'auteur
range `aktini` avant `aktinik`, le `-o` et le `-a` n'y entrant pas. Comparées
mot entier, ces deux vedettes passaient pour un désordre, et neuf cents autres
avec elles.

Le **suffixe** ne compte pas davantage, et pour la même raison : le rangement
suit la racine. `venerala` précède `veneracar` parce que le premier est
*vener-al-a* et le second *venerac-ar* ; `inventariar` précède `inventar` parce
que les deux sortent de *invent-*. Le dépouillement s'arrête à un suffixe et ne
descend jamais sous cinq lettres — sans cette borne `metalo` deviendrait *met-*
et `histerio` *hist-*.

L'auteur ne s'y tient pas toujours : il écrit `astrakano` puis `astro`, où la
racine seule voudrait l'inverse. Les trois lectures sont donc gardées — mot
entier, racine, racine dépouillée —, et le drapeau ne se lève que si **toutes
trois** sont rompues : ce qu'aucune convention n'explique. Deux exceptions encore : les quatre locutions latines,
que le livre range tantôt comme un mot (`aposteriori`) tantôt comme deux
(`ex libris` avant `exajerar`), et la première vedette des deux listes finales,
qui recommencent chacune l'alphabet.

`ordino-ruptita` reste le plus utile des drapeaux. Un dictionnaire est trié :
une vedette qui rompt l'ordre désigne souvent une mauvaise lecture, et la place
vide dit alors quel mot il fallait lire. Six l'ont été ainsi, chacune confirmée
par sa propre définition :

| lu | retenu | ce que dit la définition |
|---|---|---|
| *hetedoroxo* | **heterodoxo** | « Qua deviacas de la ortodoxeso » |
| *konaxo* | **konexo** | « (mat.) Equaciono algebrala homogena inter x, y, z… » — le connexe de Clebsch |
| *pecnio* | **peonio** | « (bot.) Planto ranunkulacea… L. paeonia » |
| *quartebo* | **quarteto** | « (muziko) Muzikajo kompozita por quar voci o por quar instrumenti » |
| *ostegomo* | **osteomo** | « (patol.) Tumoro ek osto-tisuo » |
| *apie* | **apio** | « Planto umbelifera… L. apium », et *celerio* se définit par « Apio odoranta » |

Les 55 qui restent sont une liste qu'un lecteur peut tenir dans la main.
`ordino-ruptita.md` la classe en deux familles — les deux vedettes voisines
qu'il suffit d'intervertir (35), et la vedette posée loin de sa place (20) —
avec le folio, l'image, la ligne de la grille, et les lectures qui tiendraient
dans la place occupée. `python3 outils/releve_ordino.py` le reconstruit.

**1 166 entrées portent au moins un drapeau.** L'édition HTML ne les filtre plus
— elle n'offre que la recherche ; le tri se fait sur `drapeli`, dans le JSONL ou
dans la colonne du même nom du TSV.

---

## Ce qui a été corrigé, et comment

Rien n'est corrigé en silence. **2 333 cellules** ont été redressées — 2 319 par
un correcteur, 14 à l'œil —, chacune journalisée dans
`travail/journal_complet.txt` avec la forme lue, la forme retenue et la raison :

- **le lexique du livre** (`travail/journal_corrections.txt`) — 137 758 occurrences pour
  34 620 formes : une forme lue une fois, quand une variante obtenue en changeant
  une cellule *ambiguë* est attestée huit fois et huit fois plus souvent, est une
  faute de lecture. Ainsi `zobl.` → `zool.` : une occurrence contre 334 ;
- **la morphologie des vedettes** (`travail/journal_vedettes.txt`) — la finale d'une
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

Au-dessus du décodage viennent les **couches posées à l'œil**, chacune un
fichier à part, lisible et versionné, qui l'emporte sur ce que la machine avait
lu. Elles se relisent comme un apparat critique :

| couche | ce qu'elle corrige |
|---|---|
| `travail/texti.txt` | le texte **brut**, avant toute analyse |
| `travail/vedetti.txt` | la vedette |
| `travail/vorti.txt` | un mot dans une définition |
| `travail/subvorti.txt` | le rattachement d'un article à son voisin |
| `travail/simboli.txt` | le symbole chimique relevé sur la page |
| `travail/latinaji.txt` | le nom scientifique relevé sur la page |
| `travail/filetoj.txt` | le **soulignement** : un relevé que l'œil écarte, ou une italique qu'il pose là où le trait s'est perdu |
| `travail/dividi.txt` | **deux articles frappés sur une même ligne**, que le repérage automatique ne sait pas séparer faute de code de langues entre eux : *shovar* était noyé dans *shokar*, à la fin d'une note |
| `travail/lignes_plus.txt` | une ligne de grille perdue, restituée |
| `travail/exceptions_manuel.txt` | la cellule elle-même |
| `travail/relire/reponses/` | les corrections rendues par la relecture, article par article |

Une piste a été essayée puis abandonnée — corriger les vedettes par l'ordre
alphabétique global : sans contrainte de langue elle produit *adiar* → *adiao*.
Son journal est conservé sous `travail/journal_vedettes_DP_ABANDONNE.txt`.

---

## Reprendre le travail

```
python3 outils/tout_edituri.py            # toute la chaîne, dans l'ordre
python3 outils/tout_edituri.py --sen-baz  # sans recalculer la base
```

C'est l'entrée normale. Elle enchaîne les quatre étapes, qui se lancent aussi
une à une :

```
python3 outils/edition.py     # image decodee   -> enregistrements structures
python3 outils/exportar.py    # enregistrements -> JSONL, TSV, HTML
python3 outils/posho.py       # enregistrements -> posho/enhavo.tex
lualatex posho.tex            # dans posho/, deux passes -> posho.pdf
```

La page HTML et le dictionnaire de poche sortent du **même fichier**,
`travail/edicioni/dicionario.jsonl` : les reconstruire ensemble est la seule
façon qu'ils ne divergent pas. La dernière étape recopie à la racine
`index.html`, `dicionario.tsv`, `dicionario.jsonl` et `dicionario.pdf`.

`lualatex` demande les polices **Charis SIL** et **Inter**.

### Les signets du PDF

Un dictionnaire de 444 pages ne se feuillette pas à l'écran. Le PDF porte donc
un sommaire, celui que les lecteurs affichent en panneau latéral : les
**vingt-six lettres** au premier niveau, et sous chacune le mot que porte
**l'en-tête de chaque page** — le premier mot d'une page paire, le dernier
d'une impaire, exactement ce qui est imprimé en haut de la feuille. **454
signets**, les lettres repliées à l'ouverture.

Ils se posent tous ensemble, juste après `\begin{document}`, à partir du `.aux`
du passage précédent : le format PDF exige que l'ordre des signets suive celui
des pages, et posés au fil du texte, celui de la lettre et celui de la page se
disputaient le même instant d'expédition. La page de chaque lettre est notée
dans le `.aux` par le même mécanisme que les mots des titres courants.

Les outils écrivent leur racine en dur, `/root/dicionario`. Pour reprendre le
travail ailleurs, le plus court est de l'y rendre :
`ln -s /chemin/vers/le/depot /root/dicionario`.

Pour corriger une lecture : ajouter une ligne
`page<TAB>ligne<TAB>colonne<TAB>caractère` à `travail/exceptions_manuel.txt`,
puis relancer la chaîne. La correction se propage au fac-similé, à la base et
aux deux éditions.

Le fac-similé et l'édition sortent de la **même source** : les cellules décodées.
Le fac-similé reste la pièce à conviction ; l'édition est ce qui s'utilise.

Les corrections posées à la relecture ne vivent pas dans le JSONL — `edition.py`
le reconstruit depuis le fac-similé et les effacerait sans bruit. Elles sont
gardées dans leurs couches de réponses, aujourd'hui `travail/juger/`, et
rejouées en fin de chaîne ; la liste des couches est la constante `JUGEMENTS`
d'`edition.py`, et une couche absente est simplement sautée. **Une correction
posée une fois est acquise.**

---

## Avant diffusion

L'ouvrage date de 1964. Son statut juridique dépend de la date de mort de
l'auteur et du pays de diffusion : à vérifier auprès des ayants droit ou de
l'Uniono por la Linguo Internaciona avant toute mise en ligne publique. Ce
travail est une transcription, il n'affecte pas les droits sur l'œuvre.

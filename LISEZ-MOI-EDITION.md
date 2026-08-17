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
| `travail/journal_complet.txt` | **toutes** les corrections : ce qui a été lu, ce qui a été retenu, et si c'est un correcteur ou l'œil qui a tranché |
| `outils/` | la chaîne complète, de l'image au JSON |

**9 467 entrées** extraites de 632 pages de corps d'ouvrage.
5 273 portent une marque de domaine (*bot.*, *zool.*, *arkitekt.*…),
813 un nom scientifique latin, 1 665 plusieurs sens numérotés,
8 427 un code de langues final.

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
les 9 466 entrées, sans exception — c'est un calcul, non une lecture. Or **le
livre saute deux numéros** : la page qui porte `fosfo` est numérotée
« 173/175 », doublement, et l'écart change de part et d'autre. Après elle,
`pagino` est bien le folio imprimé ; **avant elle, le folio imprimé vaut
`pagino - 2`**. `image` et `ligno`, eux, restent exacts de bout en bout : c'est
sur eux que reposent les clés de `subvorti.txt` et de `simboli.txt`.

`teksto_brut` est la ligne telle que le décodage l'a lue ; `teksto` la même
après correction et typographie ; `senci` le découpage en sens numérotés, débarrassé
des numéros de l'original. `citita` marque l'emprunt que l'auteur cite entre
guillemets — *« amen »* —, que les éditions rendent en chevrons sans que la
recherche ait à les taper. `korektita` compte les cellules redressées dans
l'entrée : une provenance, non un doute.

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

102 sous-entrées dans 83 entrées, dont 41 portent un domaine propre.

Une même locution peut relever de **deux** entrées, chacune avec sa
définition : *estado civila* se range sous `civila`, qui la définit au long,
comme sous `estado`, qui la mentionne. Les deux sont conservées telles quelles.

Un cas particulier : l'auteur a marqué d'un double tiret marginal un article
qu'il fait dépendre du précédent — *protestanto* sous *protestar*. Ce signe est
unique dans les six cent quarante pages du livre. `travail/subvorti.txt` porte
ce rattachement ; l'article rattaché devient une sous-entrée de son voisin, sans
rien perdre — ni domaine, ni code de langues, ni page.

### Le nom scientifique (`latina`)

Le tapuscrit l'annonce par un `L.` — *L. cynocephalus*. Deux pièges, tous deux
rencontrés :

- un `L.` peut introduire un **exemple**, non le nom de l'article :
  *enklitiko … Kom ex.: L. que en neque ; ne en venisne ; F. ce en est-ce*.
  Pris pour un binôme, il quittait la définition — qui restait sur « Kom ex.; »
  — pour aller s'afficher en nom latin. Un `L.` précédé de `ex.` est désormais
  laissé au texte ;
- la dactylo coupe parfois un mot en deux : *capparia spi nosa* pour *capparia
  spinosa*. Ni `spi` ni `nosa` n'étant des mots latins, la machine ne peut pas
  le savoir. `travail/latinaji.txt` porte les noms redressés à l'œil, avec la
  clé de `simboli.txt` — `vedetto@image:ligno` — et l'emporte sur le décodage.

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
penchée se lisant mal. **Les 89 articles** le portent.

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
  le livre ferme des centaines de fois juste après l'abréviation ;
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
| `sublineita` | tout ce qui est souligné dans l'entrée, remis bout à bout, les coupures de fin de ligne recollées. 6 540 entrées |
| `kursiva` | ceux que l'édition a **su placer** dans le texte, et qu'elle rend en italique. 1 259 entrées |
| `dubinda` | ceux qu'elle **n'a pas su placer** : le fragment ne se retrouve pas tel quel, ou ne couvre que des mots-outils. 1 517 entrées, 1 764 fragments |

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

`filets-dubinda.md` classe les 1 764 fragments non placés par famille, la plus
douteuse en tête, avec la page et la vedette pour aller voir le fac-similé. Une
seule famille demande un arbitrage — 27 fragments qui ressemblent à un
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
| `ordino-ruptita` | 1 155 | **la vedette rompt l'ordre alphabétique** |
| `sen-lingua` | 1 040 | pas de code de langues final — souvent normal, le livre n'en donne pas toujours |
| `finalo-nekustumala` | 155 | finale étrangère à la morphologie d'Ido (-o, -a, -e, -i, -ar, -ir, -or). **Les affixes en sont exemptés** : `-eyo`, `poli-`, `bo-` ne sont pas des mots et n'ont pas de finale grammaticale — le tiret le dit. Restent surtout les mots grammaticaux — `per`, `dum`, `mem`, `olim`, `cent` —, corrects eux aussi : le drapeau est peu sûr dans cette famille |
| `pagino-nefidinda` | 32 | pages 539-540, photographiées à une autre échelle, décodage nettement moins sûr |
| `artiklo-dividita` | 11 | l'article était coupé par un saut de page ; les deux moitiés ont été recollées |
| `sen-chefvorto` | 0 | l'entrée n'a pas de vedette lisible — plus aucun cas |

**7 351 entrées ne portent aucun drapeau.**

`korektita` a cessé d'être un drapeau : il disait « au moins une cellule
corrigée automatiquement », une provenance et non un doute, et toutes les
définitions ayant été relues une à une il ne désignait plus de travail restant.
Le compte reste dans le champ `korektita`, pour qui veut mesurer : 6 289 entrées
en portent au moins une.

`ordino-ruptita` est le plus utile des drapeaux. Un dictionnaire est trié : une
vedette qui rompt l'ordre désigne presque toujours une mauvaise lecture, dans
l'une des deux vedettes voisines — *aoendar* pour *acendar*, *a)rotano* pour
*abrotano*, *aacho* pour le suffixe *-acho*. **Corriger ces 1 155 cas, c'est
achever le livre**, et le travail est divisible : chacun peut en prendre cent.

**2 116 entrées portent au moins un drapeau.** L'édition HTML ne les filtre plus
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

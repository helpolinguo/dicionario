# Relever les soulignements d'une page dactylographiee

Le *Dicionario de la 10.000 radiki di la linguo internaciona Ido* de Marcel
Pesch (1964) souligne beaucoup : la vedette de chaque article, les mentions de
domaine comme `(zool.)` ou `(trans.)`, les noms latins, parfois une locution.

La detection automatique mesure le filet au pixel pres, mais elle estime la
ligne de base et s'y trompe : sur une ligne, elle a souligne « Sumnar » et
« nomo » au lieu de « adjurar » et « trans., pri ». On la remplace donc par ce
que tu vois.

## Les fichiers, pour chaque page NNN

- texte de la page : `/root/dicionario/travail/relecture/pNNN.txt`
  (format `LLL|contenu`, precede de lignes `== pNNNb0.png` qui indiquent sur
  quelle image se trouvent les lignes suivantes)
- images du scan : `/root/dicionario/travail/relecture/pNNNb0.png`,
  `pNNNb1.png`, `pNNNb2.png`

## Ce que tu produis

Un seul fichier par page, `/root/dicionario/travail/relecture/rez/pNNN.sou`,
qui donne pour **chaque ligne portant au moins un soulignement** les segments
soulignes, dans l'ordre ou ils apparaissent, separes par des barres verticales :

    003|adjurar|trans., pri
    007|zool.
    012|acipensar ruthenus

Rends le texte du segment **exactement tel qu'il figure dans la ligne du
fichier texte**, ponctuation comprise, pour qu'il puisse y etre retrouve.

- Un filet qui court sous plusieurs mots et sous les espaces qui les separent
  est **un seul** segment : `historio di Italia`.
- Un filet interrompu par l'usure du ruban reste un filet.
- Un trait qui ne passe sous aucune lettre n'en est pas un.
- **Attention aux codes de langue** en fin d'article — `- DEFIRS.`, `- EF.`,
  `- L.` : ils ne sont presque jamais soulignes. Le trait qu'on croit voir
  au-dessus d'eux est le soulignement de la ligne precedente. Ne le compte
  pas pour cette ligne-ci, et ne l'attribue a la ligne precedente que s'il
  passe reellement sous les lettres de celle-ci.
- N'ecris rien pour une ligne sans soulignement.

Ne renvoie ensuite qu'une seule ligne : pages traitees, lignes soulignees
relevees.

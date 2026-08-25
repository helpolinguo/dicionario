# Dicionario de la 10.000 radiki di la linguo internaciona Ido — sources

Fac-simile et edition du dictionnaire de Marcelo Persiko (Marcel Pesch),
editio princeps du 2 aout 1964, etabli a partir du scan de l'exemplaire.

## Ce que contient l'archive

    tools/            les programmes, du decoupage des cellules a l'edition
    content/           les 639 pages du fac-simile, une par fichier LaTeX
    preamble.tex      la trame : pas de la machine, macros, assiette des pages
    main.tex           le document
    ornaments/         couverture vectorisee, portraits, lettres de section
    corrections/       tout ce qui a ete corrige a la main, cellule par cellule
    relecture/         la consigne des relecteurs et leurs 631 releves
    edicioni/          l'edition structuree : JSONL, TSV, HTML consultable
    LISEZ-MOI.md       le journal du projet : ce qui a marche, ce qui a echoue

## Ce qui n'y est pas, et pourquoi

Le scan (171 Mo), les cellules decoupees (295 Mo) et le corpus de traits
(256 Mo) sont des donnees intermediaires, reconstructibles a partir du scan par
`tools/cells.py`. Les planches de relecture (564 Mo d'images) le sont par
`tools/proofreading.py`.

## Comment recomposer le fac-simile

    xelatex main.tex && xelatex main.tex

Les fichiers de `content/` sont deja generes. Pour les regenerer depuis les
cellules — ce qui suppose d'avoir refait le decoupage :

    python3 tools/generate_all.py

## L'ordre des corrections

Les corrections sont appliquees cellule par cellule, dans cet ordre, la
derniere l'emportant :

    exceptions_fins.txt        fins de ligne que le bloc coupait
    exceptions_ornements.txt   cellules recouvertes par un ornement
    exceptions_paires.txt      sosies corriges par le lexique du livre
    exceptions.txt             corrections automatiques accumulees
    exceptions_relecture.txt   la relecture a l'oeil, page par page
    exceptions_manuel.txt      arbitrages a la main, jamais reecrits

Format : `page<TAB>ligne<TAB>colonne<TAB>contenu`. La page est l'index de
l'image du scan, la ligne et la colonne sont celles de la grille de la machine.

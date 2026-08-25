# Dicionario de la 10.000 radiki di la linguo internaciona Ido — sources

Facsimile and edition of Marcelo Persiko's (Marcel Pesch's) dictionary,
editio princeps of 2 August 1964, established from the scan of a copy.

## What the archive holds

    tools/            the programs, from the cutting of the cells to the edition
    content/          the 639 pages of the facsimile, one per LaTeX file
    preamble.tex      the frame: the machine's pitch, the macros, the placing
    main.tex          the document
    ornaments/        the vectorised cover, the portraits, the section letters
    work/             every correction made by hand, cell by cell; the
                      proofreaders' brief and their 631 reports; the
                      structured edition — JSONL, TSV, browsable HTML
    docs/journal.md   the project's journal: what worked, what failed

## What it does not hold, and why

The scan (171 MB), the cut cells (295 MB) and the corpus of features
(256 MB) are intermediate data, rebuildable from the scan by
`tools/cells.py`. The proofreading sheets (564 MB of images) are
rebuildable by `tools/proofreading.py`.

## How to reset the facsimile

    xelatex main.tex && xelatex main.tex

The files in `content/` are already generated. To regenerate them from
the cells — which assumes the cutting has been done again:

    python3 tools/generate_all.py

## The order of the corrections

The corrections are applied cell by cell, in this order, the last one
winning:

    exceptions_ends.txt          line ends the block was cutting off
    exceptions_ornaments.txt     cells covered by an ornament
    exceptions_pairs.txt         lookalikes put right by the book's lexicon
    exceptions.txt               the automatic corrections, accumulated
    exceptions_proofreading.txt  the proofreading by eye, page by page
    exceptions_manual.txt        decisions made by hand, never rewritten

Format: `page<TAB>line<TAB>column<TAB>content`. The page is the index of
the scan's image; the line and the column are those of the machine's
grid.

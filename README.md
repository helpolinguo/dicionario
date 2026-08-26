# Dicionario

A **diplomatic transcription** of the _**Dicionario de la 10.000 radiki
di la linguo internaciona Ido**_ — Marcelo Persiko (Marcel Pesch),
editio princeps of 2 August 1964 — typeset in LaTeX, and a **cleaned
reading edition** of the same text published as a searchable page at
[**ido.help/dicionario**](https://ido.help/dicionario/).

The original is not printed type: it is a **typescript on a fixed pitch**,
photo-reduced for printing. It is treated here as what it is — a **grid
of characters** — and not as composed text. One cell of the grid is one
character of the transcription; one line of the facsimile is one line of
the PDF.

Two editions come out of one source, and cannot diverge:

- **the facsimile** (`main.pdf`), 640 pages, the typescript as it stands;
- **the cleaned text** — the reading page, a machine-readable edition
  (`dicionario.md`, `.json`, `.jsonl`, `.tsv`) and a **pocket
  dictionary** (`dicionario.pdf`), 9,473 entries set in two columns with
  running heads and PDF bookmarks.

This is one of three books gathered at [ido.help](https://ido.help/); the
other two are [tabeli](https://github.com/helpolinguo/tabeli) and
[gramatiko](https://github.com/helpolinguo/gramatiko), and the front door
is
[helpolinguo.github.io](https://github.com/helpolinguo/helpolinguo.github.io).

## Layout

```
main.tex             the facsimile volume: one \input per page
preamble.tex         the grid, the fonts, the macros — one constant per setting
content/pNNN.tex     one page = a run of \l{...}, one source line per
                     line of the book, in the order of the grid
content/all.tex      the register of the 640 pages                } generated
ornaments/           what was cut out of the scan: the cover, the
                     section letters, the portraits, the rules
pocket/              the pocket edition: cover.tex draws the cover,
                     content.tex is its 9,473 entries               } generated
tools/               cutting, grouping, decoding, editing, checking
work/                the working tree: corrections cell by cell,
                     the proofreaders' batches and answers, the logs
index.html           the reading page                             } generated
dicionario.md/.json/.jsonl/.tsv   the book laid flat              } generated
dicionario.pdf       the pocket edition, what the page's button offers
vortlisto.md         the word list                                } generated
docs/journal.md      why every value is what it is (French)
docs/edition-journal.md  the cleaned edition, entry by entry (French)
docs/sources.md      what the archive holds, and what it does not
docs/underlines-unplaced.md, docs/order-broken.md   two surveys   } generated
```

## Building

```sh
lualatex main.tex && lualatex main.tex  # the facsimile, 640 pages
python3 tools/all_editions.py          # everything downstream of the text
```

`tools/all_editions.py` runs the four stages in the one order that keeps
the two editions level: the lexical base (`tools/edition.py`), the HTML
page (`tools/export.py`), the pocket text (`tools/pocket.py`), then
lualatex twice — twice, because the running heads and the PDF bookmarks
are read back out of the `.aux` of the previous pass.

`index.html`, `dicionario.*`, `vortlisto.md`, `content/*.tex`,
`pocket/content.tex` and the two surveys in `docs/` are **generated,
never edited by hand**: what must change is changed in `tools/`, or in
the correction layers under `work/`.

The LaTeX build needs **`lualatex` for both**. The facsimile was
documented here as an `xelatex` build and it never was one: the signature
laid in the margin of every page is drawn with `\pdfextension literal`
(`preamble.tex`), a LuaTeX primitive with no XeTeX equivalent and no
guard around it, so `xelatex main.tex` stops on the first page with
`Undefined control sequence`. The pocket edition wants lualatex too, for
its run-time hyphenation patterns.

On a bare Debian or Ubuntu the whole of it is:

```sh
apt-get install --no-install-recommends \
    texlive-luatex texlive-latex-extra texlive-fonts-recommended \
    fonts-sil-charis fonts-inter
```

Jost\*, for the pocket cover, ships in `pocket/fonts/`. The tools need Python 3
with `numpy`, `Pillow` and `opencv-python`. The 171 MB scan is not in the
repository, and neither are the cut cells (295 MB) nor the corpus of
features (256 MB): they are rebuilt from the scan by `tools/cells.py`.
The transcription, both editions and every correction are.

### Building without the scan

**A clone rebuilds everything, scan or no scan.** Without the cells,
`content/` is read for the grid instead — it is set cell by cell, so the
grid comes back out of it exactly: `\cel{n}` is n empty cells, `\sou{...}`
a run of underlined ones, one cell per character everywhere else. Parsing
the 634 typed pages and setting them again returns the 35,117 lines byte
for byte. See `tools/scanless.py`; nothing has to be asked for, the tools
look for the corpus and take the other road when it is not there.

This is a way back in, not the ground truth, and it is narrower in three
places. The text read has **already been through the correction layers**,
so withdrawing a line from `exceptions_manual.txt` no longer brings the
old reading back — adding one still works, which is what the layer is
for. The **rules are taken as they are set** and not measured again, the
three passes that merge and trim them reading a line of text that is no
longer the raw one. And an **ornament keeps the place it has**, since
recomputing it needs the cut cells of its page.

With the scan there, none of that applies: the tools read the corpus and
`tools/scanless.py` stands aside.


## The reading page's address

A search is in the address: **`/dicionario/?q=amiko`** opens the page on the
word. What is typed goes back into the address bar as one types, so the
address of what is on screen can be copied, bookmarked or sent; the
`replaceState` behind it is delayed by 400 ms, Safari refusing more than a
hundred of them per thirty seconds.

This is what lets the dictionary be reached from outside the site.
`ido.help/opensearch.xml` — in the
[root repository](https://github.com/helpolinguo/helpolinguo.github.io) —
declares this address as the domain's search; Safari files it on the first
visit, and **macOS 26 hands Safari's list to Spotlight**, where the site's
name followed by Tab opens a field that lands here, the word already sought.
Spotlight opens the page: it does not show the definition in its own window.

The search field is therefore a real `<form method="get">` with a field
named `q` — that declaration is Safari's second way of recognising a site's
search when no OpenSearch document is there to be read. Nothing is
submitted: the list is already filtered at the keystroke, and letting the
form go would reload 2.1 MB to show what is on screen.

## The corrections

Corrections are applied cell by cell, in this order, the last winning:

```
exceptions_ends.txt         line ends the block was cutting off
exceptions_ornaments.txt    cells covered by an ornament
exceptions_pairs.txt        lookalikes put right by the book's own lexicon
exceptions.txt              the automatic corrections, accumulated
exceptions_proofreading.txt the proofreading by eye, page by page
exceptions_manual.txt       decisions made by hand, never rewritten
```

Format: `page<TAB>line<TAB>column<TAB>content`. The page is the index of
the scan's image; the line and the column are those of the machine's
grid, **before the shift** — thirteen pages carry a letter given back
before column zero and are moved one cell right when they are set, and a
correction is numbered where it was surveyed, not where it is set.

Two smaller layers sit beside them:

```
grid_repair.txt       cells content/ no longer holds, given back
starts_set_aside.txt  letters restore_starts.py gave back in error
```

## The surveys

Two reports say what the edition could not settle, and both are
regenerated from the published text:

```sh
python3 tools/survey_rules.py   # 1444 underlines it could not place
python3 tools/survey_order.py   # 55 headwords that break the alphabet
```

A figure that moves without a reason is a defect, not a detail.

**1444 is the figure without the scan, and 1525 with it.** The two roads
do not read the same measurement of the rules. The facsimile has always
preferred `redo_rules.py`'s recomputation, with the survey by eye over it
(`generate.py`, « Recomputed rules »); the reading edition, when the cells
are there, reads instead the detection stored in them. Without the cells
it reads the recomputation too, and the fragments it cannot place fall
differently: fewer of three letters or less (542 → 324), fewer function
words alone (49 → 9), more cut in the middle of a word (920 → 1102).

The two editions ought to read one measurement, and the recomputed one is
the better — it is why `generate.py` prefers it. Making the scan's road
agree means changing what `edition.py` reads from the cells, and that
wants the scan to verify; it is not done here.

## A note on language

The source is in English — comments, identifiers, filenames and commits.
Four things deliberately stay as they are:

- **The interface is in Ido**: the reading page's text, its accessible
  names and its tooltips, and the URLs of its sections.
- **The LaTeX macros keep their names.** `\l`, `\cel`, `\sou`, `\sur`,
  `\marge`, `\pgc`, `\ornamento` are the vocabulary in which the
  typescript was recorded, and `content/` is the diplomatic
  transcription — the one thing in this repository that does not move.
- **The keys of the records keep theirs.** `vedetto`, `pagino`, `senci`,
  `drapeli`, `ordino-ruptita` are published in `dicionario.json`,
  `dicionario.jsonl` and `/llms.txt`, where other programs read them. A
  key is an address; renaming it breaks whoever reads it.
- **The book's own words stay the book's.** Nothing inside `content/` or
  inside a definition was touched, in any pass.

Translating the source changed nothing a reader of the site can see. The
page and the four machine-readable files were rebuilt and compared byte
for byte at every step.

## Licence

The code in this repository is under the **MIT Licence** — see
[`LICENSE`](LICENSE). Copyright © 2026 Gilles-Philippe Morin.

The **work transcribed here is in the public domain in Canada**, where
this project is maintained. Its author, Marcel Pesch (Marcelo Persiko),
died in 1970; Canada's term then ran to fifty years after the author's
death, so it expired at the end of **2020**, two years before the 2022
extension to seventy — and that extension did not restore copyrights
already expired. Copyright terms differ from country to country; readers
elsewhere should satisfy themselves of the position under their own law.
The transcription, the typesetting, the cleaned edition, the tools and
the reading page are this project's own work, and are covered by the
licence above.

The font of the pocket edition's cover, **Jost\***, is under the SIL Open
Font License 1.1 — see [`pocket/fonts/OFL.txt`](pocket/fonts/OFL.txt).

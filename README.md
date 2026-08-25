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
xelatex main.tex && xelatex main.tex   # the facsimile, 640 pages
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

The LaTeX build needs `xelatex` (facsimile) and `lualatex` (pocket
edition, for its run-time hyphenation patterns). The tools need Python 3
with `numpy`, `Pillow` and `opencv-python`. The 171 MB scan is not in the
repository, and neither are the cut cells (295 MB) nor the corpus of
features (256 MB): they are rebuilt from the scan by `tools/cells.py`.
The transcription, both editions and every correction are.

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
grid.

## The surveys

Two reports say what the edition could not settle, and both are
regenerated from the published text:

```sh
python3 tools/survey_rules.py   # 1525 underlines it could not place
python3 tools/survey_order.py   # 55 headwords that break the alphabet
```

A figure that moves without a reason is a defect, not a detail.

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

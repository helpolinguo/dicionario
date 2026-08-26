# Working notes

This file says how we work on this repository. The *what* is in
`README.md`, which is the project's documentation; we do not repeat it
here, we point at it.

## Branches and pull requests

**The project lives on `main`**, which is the default branch.

We never write to `main` directly. We work on a branch, and bring it in
through a **pull request whose base is `main`**, opened as a draft. A
branch always starts again from the current `main`:

    git fetch origin main
    git checkout -B <branch> origin/main

**A branch is named after its subject**, in English, in lower case, the
words joined by hyphens: `claude/underlines-unplaced`,
`claude/pocket-running-heads`, `claude/alphabetical-order`. No session
identifier, no random suffix — a name like that says nothing six months
later, and it lies the moment the branch serves something other than what
it was opened for. The `claude/` prefix stays: it says who held the pen.

A merged pull request is finished: it cannot carry a sequel. The next
piece of work starts again from `main`, and it is a new pull request.

## What we check before pushing

**Everything below runs in a clone, with or without the scan.** Without
the cells, the grid is read back out of `content/`; see § *Building
without the scan* in `README.md` and the head of `tools/scanless.py`.
A correction laid in `work/` therefore has to be rebuilt and committed
in the same breath — declaring it is no longer half the work, it is a
quarter of it.

The two editions come from one file, and they are rebuilt together:

    python3 tools/generate_all.py   # the facsimile's 639 pages
    python3 tools/all_editions.py   # base, HTML page, pocket text, lualatex x2

Then the surveys, each of which says what it expects. A figure that moves
without a reason is a defect, not a detail:

    python3 tools/survey_rules.py   # 1525 fragments (14 / 542 / 49 / 920)
    python3 tools/survey_order.py   # 35 transpositions, 20 headwords astray
    python3 tools/verify_edition.py

And the facsimile compiles, always:

    xelatex main.tex && xelatex main.tex

## Four rules that are not negotiable

**THE SOURCE DOES NOT MOVE.** `content/` reproduces the typescript as it
stands, the typist's slips included. What has to be corrected is declared
in the layers under `work/` — `exceptions_*.txt` — and acts there alone.
See § *The corrections* in `README.md`.

This one has been paid for. A rename applied to the whole tree replaced
the Ido word « kovrilo » inside the book's own definitions: « Tanko
klozata per kovrilo » became « ... per cover ». Whatever moves in
`content/`, it moves by full path or by whole comment line, never by
bare word.

**A PRODUCED FILE IS NOT A PLACE WHERE ONE WRITES.** `index.html`,
`dicionario.md`, `.json`, `.jsonl`, `.tsv`, `vortlisto.md`,
`content/*.tex`, `content/all.tex`, `pocket/content.tex` and the two
surveys in `docs/` are regenerated; an edit made in them by hand
disappears at the next build. What must change is changed in `tools/` or
in `work/`.

This one has been paid for three times in this repository alone:
`index.html` carried two blocks `export.py` knew nothing about,
`work/editions/index.html` was a stale copy of the published page, and
`docs/underlines-unplaced.md` reported 1531 fragments where the tool
gives 1525.

**A KEY IS AN ADDRESS.** `vedetto`, `pagino`, `senci`, `drapeli`,
`ordino-ruptita` are read back out of files this repository holds, and
the published ones are read by other programs. They do not get renamed
with the code around them. The same goes for a keyword argument of
numpy's or of `dict()`: it is a name token, but it is data.

**THE INTERFACE IS IN IDO.** The reading page's text, its accessible
names, its tooltips and the URLs of its sections. Nothing a reader of the
site can see changes because the source changed. Rebuild and compare byte
for byte.

## Writing

Commit messages and code comments **in English**, in the house style: the
finding at the head and in capitals, measurements rather than
suppositions, the approaches tried and then abandoned recorded, and an
earlier assertion that has become false corrected **where it is
written**.

The LaTeX macros keep their names — `\l`, `\cel`, `\sou`, `\sur`,
`\marge`, `\pgc` — for the same reason the source does not move: they are
the vocabulary in which the typescript was recorded. See the note on
language at the end of `README.md`.

`docs/journal.md` and `docs/edition-journal.md` are in French. They are
the record of how the work was done, written as it was done; they are not
translated, and a new entry is written in English at the end.

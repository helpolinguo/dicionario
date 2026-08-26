# -*- coding: utf-8 -*-
"""Reading the grid back out of `content/`, when the scan is not there.

THE SCAN IS NOT IN THE REPOSITORY, AND WITHOUT IT NOTHING REBUILT. The 171 MB
of images, the 295 MB of cut cells and the 256 MB of features are rebuilt from
the scan by `tools/cells.py`; a clone that does not have them stopped at the
first line of `tools/edition.py`:

    FileNotFoundError: work/km_lab.npy

So the correction laid in `work/exceptions_manual.txt` — the layer that is the
one place where a correction is allowed to be written — could not reach a
single produced file. The layer was declarative and nothing read it.

`content/` is the way out, and it costs nothing: it is already in the
repository, it is the diplomatic transcription, and `generate.texify()` writes
it CELL BY CELL. `\\cel{n}` is n empty cells, `\\sou{...}` is a run of
underlined ones, everything else is one cell per character. That is the whole
grid, and it is recoverable exactly. Parsing the 634 typed pages back and
setting them again with `texify()` returns the 35,117 lines byte for byte.

The line numbering is recoverable too. `write_()` sets the lines in one
unbroken run from `min(per)` to `max(per)`: `min(per)` is 0, except on the
three pages where `extra_lines.txt` gives back a line ABOVE the first one
read — 162, 402, 412. So the k of the i-th `\\l{}` is `first_line(pg) + i`,
and the check is not a supposition: of the 372,416 cells of the correction
layers that fall on a line the page still has, 372,395 are found at the cell
the numbering predicts. The twenty-one others are all accounted for — the
`konvencionar` correction not yet rebuilt, one `"` written in its escaped
form, and one line of page 546 which `extra_lines.txt` rightly overrides.

WHAT THIS IS NOT. It is a way back in, not the ground truth. The text read
here has already been through the correction layers, so a line withdrawn from
`exceptions_manual.txt` no longer brings the old reading back — the corpus
alone can do that. When the scan is there, the tools use it and this module
stands aside.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = _ROOT + "/work"
CONTENT = _ROOT + "/content"

# The cell contents that `generate.esc()` writes as a macro, read the other
# way. A cell holding the string « \textquotedbl{} » and a cell holding « " »
# are set identically; we return the character, which is the reading.
MACRO = {r'\textbackslash{}': '\\', r'\textasciicircum{}': '^',
         r'\textasciitilde{}': '~', r'\textquotedbl{}': '"',
         r'\textquotesingle{}': "'", r'\textless{}': '<',
         r'\textgreater{}': '>', r'\textbar{}': '|'}
SIMPLE = {r'\{': '{', r'\}': '}', r'\%': '%', r'\#': '#', r'\_': '_',
          r'\&': '&', r'\$': '$'}


def corpora_present():
    """The scan's own files: the labels of the cells and the cut cells."""
    return (os.path.exists(f"{T}/km_lab.npy")
            and os.path.exists(f"{T}/meta_all.npy")
            and os.path.isdir(f"{T}/cells"))


def _braced(s, i):
    """Reads the group {...} that opens at s[i]; returns it and what follows."""
    if s[i] != '{': raise ValueError('expected a group: %r' % s[i:i+24])
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '{': depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0: return s[i+1:j], j+1
    raise ValueError('unbalanced group: %r' % s[i:i+24])


def _macro_length(s, j):
    """The length of the macro that begins at s[j].

    A run is scanned character by character to find where the next \\cel or
    \\sou begins; without this the scan would stop inside « \\textbar{} ».
    """
    for m in MACRO:
        if s.startswith(m, j): return len(m)
    for m in SIMPLE:
        if s.startswith(m, j): return len(m)
    if s.startswith(r'\sur{', j):
        _, k = _braced(s, j+4)
        _, k = _braced(s, k)
        return k - j
    raise ValueError('unknown cell macro: %r' % s[j:j+24])


def _cells_of(run):
    """Splits an escaped run back into ONE ENTRY PER CELL.

    « \\sur{...}{...} » — an overstrike, a composed character — is a single
    cell whose content is more than one character; `esc()` lets it through as
    it stands, and so do we.
    """
    out = []; i = 0
    while i < len(run):
        if run[i] != '\\':
            out.append(run[i]); i += 1; continue
        if run.startswith(r'\sur{', i):
            n = _macro_length(run, i)
            out.append(run[i:i+n]); i += n; continue
        for table in (MACRO, SIMPLE):
            for m, c in table.items():
                if run.startswith(m, i):
                    out.append(c); i += len(m); break
            else:
                continue
            break
        else:
            raise ValueError('unknown cell macro: %r' % run[i:i+24])
    return out


def parse_line(body):
    """The body of one \\l{...} -> (ornament, cells, underlined ranges).

    The ornament is the « \\marge[...]{...}{\\ornamento{...}{...}} » that
    `generate_all.py` lays at the head of a page's first line. It takes up no
    room in the grid, and it comes back here unchanged: recomputing it needs
    the cut cells of its page, which is exactly what we do not have.
    """
    ornament = ''
    while body.startswith('\\marge['):
        j = body.index(']') + 1
        _, j = _braced(body, j)
        _, j = _braced(body, j)
        ornament += body[:j]; body = body[j:]
    cells = []; ranges = []; i = 0
    while i < len(body):
        if body.startswith(r'\cel{', i):
            n, j = _braced(body, i+4)
            cells.extend(' ' * int(n)); i = j
        elif body.startswith(r'\sou{', i):
            inner, j = _braced(body, i+4)
            run = _cells_of(inner)
            ranges.append((len(cells), len(cells) + len(run) - 1))
            cells.extend(run); i = j
        else:
            j = i
            while j < len(body) and not (body.startswith(r'\cel{', j)
                                         or body.startswith(r'\sou{', j)):
                j += _macro_length(body, j) if body[j] == '\\' else 1
            cells.extend(_cells_of(body[i:j])); i = j
    return ornament, cells, ranges


def first_line(pg):
    """The k of the FIRST \\l{} of a page.

    `write_()` sets the lines from `min(per)` to `max(per)`. That is 0, unless
    `extra_lines.txt` gives back a line above the first one read, whose index
    is then negative: pages 162, 402 and 412.
    """
    # Imported here and not at the head: `generate` reads this module in its
    # turn, and the two would not load.
    from generate import extra_lines
    given = extra_lines().get(pg)
    return min(0, min(given)) if given else 0


_PAGES = {}
def page(pg):
    """A page of `content/` -> (cells, rules, ornament, columns).

    The lines come back in the order they are set, the first being
    `first_line(pg)`. The trailing spaces `texify()` cut off are given back:
    the number of columns is that of the longest line, and a correction that
    bears further right widens it, as it does when the cells are there.

    THE RULES ARE TAKEN AS THEY ARE SET, and not measured again from
    `rules.pkl`. `page_lines()` merges a measured rule, trims it and brings it
    back to the word boundary, and those three passes read the LINE'S TEXT --
    which here has already been through the correction layers, where the
    measurement saw it raw. Measuring again therefore moved eighteen rules:
    « (natur-hi\\sou{stor}io) » became « (\\sou{natur-historio}) ». The second
    is the better reading, but it is not this module's to make: what `\\sou{}`
    records is the rule as the scan settled it.
    """
    if pg not in _PAGES:
        path = f"{CONTENT}/p{pg:03d}.tex"
        if not os.path.exists(path):
            _PAGES[pg] = None
        else:
            rows = []; rules = {}; ornament = ''
            k0 = first_line(pg)
            for l in open(path, encoding='utf-8'):
                l = l.rstrip("\n")
                if not (l.startswith("\\l{") and l.endswith("}")): continue
                orn, cells, ranges = parse_line(l[3:-1])
                ornament += orn
                if ranges: rules[k0 + len(rows)] = ranges
                rows.append(cells)
            ncol = max((len(r) for r in rows), default=0)
            _PAGES[pg] = ([r + [" "]*(ncol-len(r)) for r in rows],
                          rules, ornament, ncol)
    if _PAGES[pg] is None:
        raise FileNotFoundError(f"{CONTENT}/p{pg:03d}.tex")
    return _PAGES[pg]


def pages():
    """The pages `content/` holds, the ones not typewritten included."""
    out = []
    for name in sorted(os.listdir(CONTENT)):
        if len(name) == 8 and name.startswith("p") and name.endswith(".tex"):
            out.append(int(name[1:4]))
    return out


def page_text(pg):
    """The page's lines, as `decode.page_text()` gives them: (k, text).

    Same shape and same numbering, so `edition.py` reads one or the other
    without knowing which.
    """
    rows, _, _, _ = page(pg)
    k0 = first_line(pg)
    return [(k0 + i, "".join(r).rstrip()) for i, r in enumerate(rows)]


def underlines(pg):
    """The page's rules, by line: {k: [(first column, last column)]}.

    The `\\sou{}` of `content/`, which are the rules the facsimile sets. The
    reading edition reads the same ones, so the two editions cannot part
    company over an underline — and the figure the survey gives does not move
    because the rules were measured a second time.
    """
    return {k: list(v) for k, v in page(pg)[1].items()}

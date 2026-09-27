#!/usr/bin/env python3
"""The Dicionario as an ANKI DECK -- dicionario.apkg.

WHY THIS SCRIPT EXISTS. The book is already published as a page to read, a
pocket volume to carry and four files a program can parse; what it was asked
for next is a deck to REVIEW. A spaced-repetition deck is not another way of
reading the dictionary: it turns the 9,473 articles into a schedule, and that
is the one use the other five forms cannot serve.

    python3 tools/anki.py            # dicionario.apkg

It is a fifth derived form, and it is derived from the same file as the
others: `dicionario.json`, which `tools/machine_readable.py` writes out of
the page. Run it after that one, as `tools/parentheticals.py` is run after
it, and the deck cannot say something the page does not.

WHAT AN .apkg IS, AND WHY NOTHING IS INSTALLED TO WRITE ONE. An Anki package
is a zip holding `collection.anki2` -- a SQLite database in Anki's schema 11
-- and a `media` map, empty here, this book having no pictures. sqlite3,
zipfile and hashlib are in the standard library, so the deck is written by
hand and A CLONE BUILDS IT WITH NOTHING INSTALLED. numpy, Pillow and
opencv-python serve the scan; this needs none of them, and no genanki
either. The schema and the collection's defaults are Anki's own, and are
what genanki writes; what is written here is the deck, not a new format.

THE GUID IS AN ADDRESS. Anki recognises a note it has seen before by its
`guid`, and by nothing else: a note whose guid matches one already in the
collection is UPDATED on import, and one whose guid is new is ADDED. The
guid is therefore computed from the headword's address -- the same rule
`vorti/` uses, imported from the tool that owns it -- and from the rank of
the article among those sharing that address. A reader who imports a
corrected deck over an old one keeps every repetition ever made; had the
guid been drawn from a counter or from the clock, the same import would
have laid 9,473 duplicates beside the notes it was meant to correct, and
the reader's history with them.

THE BUILD IS DETERMINISTIC. Every timestamp in the database and in the zip
is a constant, and the identifiers are counted from a constant, so two runs
over one text give THE SAME BYTES -- measured with sha256, and printed at
the end of every run. A generated file committed to the repository must
change when the text changes and not otherwise; one that carried the hour
of its build would show a diff at every run and hide the real one.

WHAT THE DECK ASKS. Two cards, from one note:

  vedetto → senco   the headword, and one recalls the article
  senco → vedetto   the article, and one recalls the headword

The second is NOT made for every article. MEASURED, over the 9,473: 102 are
affixes, which have no sense to recognise; 532 carry a body under 25
characters, too short to be guessed at; and 472 PRINT THE HEADWORD'S OWN
ROOT INSIDE THE DEFINITION -- « abako ... la kapitelo » is fair, but
« abandonar. Lasar ... abandonita » hands the answer over. 8,367 articles
are left, and they alone carry the reverse card. The gate is the field
`Inversa`: Anki makes no card whose question side comes out empty, so an
empty `Inversa` is the whole of it.

THE TAGS ARE THE BOOK'S OWN MARKS. `tools/parentheticals.py` already knows
how to read the bracketed group before the first sense -- transitivity,
governed preposition, subject field -- and at the sense level as well as the
article's, which is where 40 verbs and the whole of « metaf. » live. That
reading is imported rather than done again here: there is one reading of
the parenthetical in this repository, not two of them drifting apart.

CHECKED WITH ANKI ITSELF, and not against this file's own idea of the
format: the package was imported by the `anki` library, version 26.8, into
an empty collection. 9,473 notes and 17,840 cards arrive, in the deck and
under the note type named here; the note type comes back with its ten
fields and its two templates, and with the `req` written below. THE SAME
FILE IMPORTED A SECOND TIME ADDS NOTHING -- 9,473 notes still, which is
the guid rule doing what it is there for. The library is not a dependency
of this repository: it was installed to check, and the deck is built
without it.
"""

import hashlib
import json
import re
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from machine_readable import slug                       # noqa: E402
from parentheticals import decompose, parentheticals    # noqa: E402

SITE = 'https://ido.help/dicionario/'
OUT = ROOT / 'dicionario.apkg'

# THESE FOUR NUMBERS ARE ADDRESSES, like the guid, and for the same reason.
# Anki files a deck and a note type under their identifier: keep them, and a
# rebuilt deck lands in the deck the reader already has, under the note type
# whose card templates they may have retouched. Change them, and the reader
# gets a second deck beside the first. They are the date of the editio
# princeps -- 2 August 1964 -- and never move again.
DECK_ID = 1964080200001
MODEL_ID = 1964080200002
NOTE_ID = 1964080300000     # the notes are counted from here,
CARD_ID = 1964080400000     # the cards from here: one range, one table.

# The collection's own timestamps. Anki reads them as seconds and
# milliseconds since the epoch; the values are Anki's defaults, which is what
# they are for -- a package holds no history, and its collection is thrown
# away by the importer as soon as the notes are read out of it.
CRT = 1411124400
MOD = 1425279151694
ZIP_DATE = (1980, 1, 1, 0, 0, 0)    # the oldest a zip entry can carry

# The sentinels the export wraps an italic in. See tools/export.py, korpo().
IT0, IT1 = '\ue000', '\ue001'

# A leading bracketed group is a qualifier and takes the italic, as on the
# page. « (a) » and « (1) » are enumeration and are left alone; a group
# holding a figure is a chemical formula, which the italic would cut from
# its subscript.
LEAD = re.compile(r'^((?:\((?![a-zA-Z0-9]\))[^()]{1,120}\)\s*)+)')
FIGURE = re.compile(r'[0-9₀-₉]')

# The headword's ending, taken off to leave the root. The list is the one
# tools/verify_edition.py checks the morphology against.
ENDINGS = ('ar', 'ir', 'or', 'o', 'a', 'e', 'i')

# A field marking fewer than five words is almost always a note on one
# article -- « aludante navo », « che la Romani antiqua » -- and the book
# does not distinguish the two. Five is the threshold faki.md already draws
# its own line at, and it leaves a tag tree one can read.
FIELD_FLOOR = 5


# --------------------------------------------------------------------------
# The article, in the HTML a card shows
# --------------------------------------------------------------------------
# THIS MIRRORS export.py's korpo() AND rendi(), AND IT HAS TO. The deck is
# the page's text on another support: an italic the page sets and the card
# does not is the same text saying something else. What is not mirrored is
# the search highlighting, which has no meaning here, and the Latin name and
# the chemical symbol, which the card carries in fields of their own.

def esc(t: str) -> str:
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def body(t: str) -> str:
    """One sense's text, italics and all."""
    if not t:
        return ''
    if IT0 not in t:
        m = LEAD.match(t)
        if m:
            rest = t[m.end():]
            # `rest[:1] in ...` would be true of the empty string, and every
            # group ending an article would pass for a formula.
            chemical = bool(FIGURE.search(m.group(1))
                            or (rest[:1] and rest[0] in '₀₁₂₃₄₅₆₇₈₉'))
            if not chemical:
                return f'<i>{esc(m.group(1).strip())}</i> {esc(rest)}'
        return esc(t)
    out, inside = [], False
    for piece in re.split('[%s%s]' % (IT0, IT1), t):
        if piece:
            out.append(f'<i>{esc(piece)}</i>' if inside else esc(piece))
        inside = not inside
    return ''.join(out)


def senses(e: dict) -> str:
    """The senses and the sub-entries, in the page's order and its shapes."""
    lines = []
    B = e.get('b') or []
    for i, b in enumerate(B):
        num = f'<b>{i + 1}.</b> ' if len(B) > 1 else ''
        if b.get('t') or not b.get('u'):
            lines.append(f'<div class="senco">{num}{body(b.get("t") or "")}</div>')
            num = ''
        for x in b.get('u') or []:
            part = [num, f'<b>{esc(x["k"])}</b>']
            if x.get('q'):
                part.append(f' <i>({esc(x["q"])})</i>')
            part.append(' ' + body(x.get('t') or ''))
            if x.get('n'):
                part.append(f'<span class="lin">{esc(", ".join(x["n"]))}</span>')
            lines.append('<div class="subvorto">%s</div>' % ''.join(part))
            num = ''
    return ''.join(lines)


def plain(e: dict) -> str:
    """Everything the article says, markup gone. Serves the two measurements
    below -- the length of the body, and the root that gives itself away."""
    t = []
    for b in e.get('b') or []:
        t.append(b.get('t') or '')
        for x in b.get('u') or []:
            t += [x.get('k') or '', x.get('q') or '', x.get('t') or '']
    return re.sub('[%s%s]' % (IT0, IT1), '', ' '.join(t))


def root(v: str) -> str:
    """The headword shorn of its grammatical ending, and of the four marks
    that are not letters -- the asterisk of the word not official, the
    exclamation of the interjections, the brackets of « a(d) », the
    guillemets of « «brokoli»-kaulo »."""
    s = re.sub(r'[«»!()*+]', '', v.lower()).strip().strip('-')
    for end in ENDINGS:
        if s.endswith(end) and len(s) - len(end) >= 3:
            return s[:-len(end)]
    return s


def reversible(e: dict) -> bool:
    """Whether the article can be asked the other way round. See the head of
    this file for the three refusals and what each of them costs."""
    v = e['v']
    if v.startswith('-') or v.endswith('-'):
        return False
    text = plain(e)
    if len(text) < 25:
        return False
    r = root(v)
    return not (len(r) >= 3 and r in text.lower())


# --------------------------------------------------------------------------
# The tags
# --------------------------------------------------------------------------
# Anki splits a note's tags on the space, and reads « :: » as one level of a
# tree. A field the book prints as two words therefore joins them with a
# hyphen -- « religio katolika » is one tag, not two -- and the tree is the
# one thing that makes 9,473 notes searchable without a search: fako::bot.
# selects the 616 plants, verbo::transitiva the 1,387 verbs that take an
# object.

def tagify(s: str) -> str:
    s = re.sub(r'\s+', '-', s.strip())
    return re.sub(r'::+', ':', s).strip('-') or '?'


def fields_kept(D: list) -> set:
    """The bracketed groups that mark FIELD_FLOOR articles or more.

    The government is taken out first, by decompose(): « ad » and « ulo »
    mark enough articles to pass the threshold and are not fields, they are
    the preposition the verb takes.
    """
    seen = {}
    for i, e in enumerate(D):
        for _, text in parentheticals(e):
            for part in decompose(text)[2]:
                # Counted by the article's rank and not by its headword: the
                # book prints six of them twice, and two articles are two.
                seen.setdefault(part, set()).add(i)
    return {k for k, v in seen.items() if len(v) >= FIELD_FLOOR}


def tags(e: dict, kept: set) -> list:
    out = set()
    first = slug(e['v']).lstrip('-')[:1]
    if first:
        out.add('litero::' + first)
    for _, text in parentheticals(e):
        kind, gov, rest = decompose(text)
        if kind:
            out.add('verbo::' + kind)
        out |= {'prepoziciono::' + tagify(g) for g in gov}
        out |= {'fako::' + tagify(r) for r in rest if r in kept}
    out |= {'drapelo::' + tagify(d) for d in e.get('d') or []}
    return sorted(out)


# --------------------------------------------------------------------------
# The note type, and what the two cards show
# --------------------------------------------------------------------------
# THE FIELDS ARE NAMED IN IDO, and their names are addresses too: Anki matches
# an imported note to the one it holds field by field, by name. Renaming
# `Vedetto` would empty the field of every note a reader has already
# reviewed.
#
# TWO OF THEM HOLD NO TEXT: `Citita` and `Inversa` are gates the templates
# read, and they are fields because an Anki template can ask nothing else.
FIELDS = ['Vedetto', 'Citita', 'Fako', 'Senci', 'Latina', 'Simbolo',
          'Lingui', 'Fonto', 'Adreso', 'Inversa']

# THE GUILLEMETS ARE SET, NOT STORED, exactly as on the page: the cited
# borrowing shows as « alpari » and IS « alpari » in no field. Anki sorts the
# browser on the first field and looks for duplicates there, so guillemets
# laid in it would file the 90 cited words apart from the alphabet and make
# « alpari » a word one cannot find by typing alpari.
VED = ('{{#Citita}}«&nbsp;{{/Citita}}{{Vedetto}}{{#Citita}}&nbsp;»{{/Citita}}')
LINK = ('<a href="https://ido.help/dicionario/?q={{Adreso}}">'
        'ido.help/dicionario</a>')

FRONT_1 = '<div class="ved">%s</div>' % VED
BACK_1 = """{{FrontSide}}
<hr id=answer>
{{#Fako}}<div class="fako">({{Fako}})</div>{{/Fako}}
{{Senci}}
{{#Latina}}<div class="senco lat">L. {{Latina}}</div>{{/Latina}}
{{#Simbolo}}<div class="senco simb"><i>Simb. kem.</i> <b>{{Simbolo}}</b></div>{{/Simbolo}}
<div class="meta"><span>{{Fonto}}</span>{{#Lingui}}<span>{{Lingui}}</span>{{/Lingui}}<span>%s</span></div>""" % LINK

# The question side of the reverse card is wrapped in {{#Inversa}}: where the
# field is empty the side renders empty, and ANKI MAKES NO CARD FOR AN EMPTY
# QUESTION. That is the whole of the gate -- there is nothing to suspend and
# nothing to delete afterwards.
FRONT_2 = """{{#Inversa}}{{#Fako}}<div class="fako">({{Fako}})</div>{{/Fako}}
{{Senci}}{{/Inversa}}"""
BACK_2 = """{{FrontSide}}
<hr id=answer>
<div class="ved">%s</div>
<div class="meta"><span>{{Fonto}}</span>{{#Lingui}}<span>{{Lingui}}</span>{{/Lingui}}<span>%s</span></div>""" % (VED, LINK)

# The page's own palette and its serif, the two lines of it that a card
# needs. Anki hangs `nightMode` on the card when the reader's system is dark,
# which is what the page reads out of prefers-color-scheme.
CSS = """.card{
 --enk:#1a1a1a;--pap:#fbfaf7;--sub:#6b6560;--acc:#7A3D00;--lin:#e2ddd5;
 background:var(--pap);color:var(--enk);text-align:left;
 font:17px/1.55 "Iowan Old Style",Palatino,"Palatino Linotype",Georgia,serif;
 padding:14px}
.card.nightMode{
 --enk:#e8e4de;--pap:#16161a;--sub:#9a938c;--acc:#D6A06A;--lin:#2c2c33}
.ved{font-size:23px;font-weight:600}
.fako{color:var(--acc);font-style:italic;font-size:15px}
.senco,.subvorto{margin:7px 0}
.senco b{color:var(--sub);font-weight:600;font-size:13px;margin-right:4px}
.subvorto>b{color:var(--acc)}
.subvorto::before{content:"\\25b8";color:var(--acc);margin-right:5px}
.subvorto .lin{color:var(--sub);font-size:12px;margin-left:6px;letter-spacing:.03em}
.lat{font-style:italic;color:var(--sub)}
.simb{color:var(--sub)}
.meta{margin-top:10px;font-size:12px;color:var(--sub);
 font-family:system-ui,sans-serif}
.meta span{margin-right:10px}
.meta a{color:var(--sub)}
hr#answer{border:0;border-top:1px solid var(--lin);margin:12px 0}"""

DESC = ('9473 artikli dil <i>Dicionario de la 10.000 radiki di la linguo '
        'universala Ido</i>, Marcelo Persiko (Marcel Pesch), 1934/1964.<br>'
        'Du karti per artiklo: vedetto → senco, e senco → vedetto (ica-lasta '
        'nur ube la senco ne donas la vedetto ipsa).<br>'
        'La defini esas en Ido. La lingui indikata esas ti en qui la radiko '
        f'esas atestata — li ne esas tradukuri.<br>Fonto: {SITE}')


# --------------------------------------------------------------------------
# Anki's own encodings
# --------------------------------------------------------------------------
# Anki writes a guid in a base 91 of its own, and it is reproduced here
# rather than approximated: what reads these decks is Anki, and a guid it
# cannot parse is a guid that matches nothing.
BASE91 = ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
          '!#$%&()*+,-./:;<=>?@[]^_`{|}~')


def guid(*parts) -> str:
    n = int.from_bytes(hashlib.sha256(
        '\x1f'.join(str(p) for p in parts).encode('utf-8')).digest()[:8], 'big')
    out = []
    while n:
        out.append(BASE91[n % len(BASE91)])
        n //= len(BASE91)
    return ''.join(reversed(out))


def csum(field: str) -> int:
    """Anki's duplicate check: the first eight hex digits of the sha1 of the
    first field, read as a number."""
    return int(hashlib.sha1(field.encode('utf-8')).hexdigest()[:8], 16)


def model_json() -> dict:
    return {
        'id': str(MODEL_ID), 'name': 'Dicionario', 'type': 0, 'mod': CRT,
        'usn': -1, 'sortf': 0, 'did': DECK_ID, 'tags': [], 'vers': [],
        'latexPre': '', 'latexPost': '', 'latexsvg': False, 'css': CSS,
        'flds': [{'name': n, 'ord': i, 'sticky': False, 'rtl': False,
                  'font': 'Charis SIL', 'size': 20, 'media': []}
                 for i, n in enumerate(FIELDS)],
        'tmpls': [{'name': 'Vedetto → senco', 'ord': 0, 'qfmt': FRONT_1,
                   'afmt': BACK_1, 'bqfmt': '', 'bafmt': '', 'did': None,
                   'bfont': '', 'bsize': 0},
                  {'name': 'Senco → vedetto', 'ord': 1, 'qfmt': FRONT_2,
                   'afmt': BACK_2, 'bqfmt': '', 'bafmt': '', 'did': None,
                   'bfont': '', 'bsize': 0}],
        # Which fields a card needs before Anki will make it. The first card
        # wants the headword; the second wants nothing but the gate, its
        # question side being empty without it. These two lines are what Anki
        # itself computes from the templates -- checked by importing the
        # package and reading the note type back out -- and it recomputes
        # them anyway from 2.1.28 on; older versions read them as they stand.
        'req': [[0, 'any', [FIELDS.index('Vedetto')]],
                [1, 'all', [FIELDS.index('Inversa')]]],
    }


def deck_json() -> dict:
    return {'id': DECK_ID, 'name': 'Dicionario de la 10.000 radiki',
            'desc': DESC, 'mid': MODEL_ID, 'conf': 1, 'dyn': 0,
            'collapsed': False, 'browserCollapsed': False, 'extendNew': 0,
            'extendRev': 50, 'mod': CRT, 'usn': -1, 'lrnToday': [0, 0],
            'newToday': [0, 0], 'revToday': [0, 0], 'timeToday': [0, 0]}


DEFAULT_DECK = {'id': 1, 'name': 'Default', 'desc': '', 'conf': 1, 'dyn': 0,
                'collapsed': False, 'browserCollapsed': False, 'extendNew': 0,
                'extendRev': 50, 'mod': CRT, 'usn': 0, 'lrnToday': [0, 0],
                'newToday': [0, 0], 'revToday': [0, 0], 'timeToday': [0, 0]}

DEFAULT_CONF = {'1': {
    'id': 1, 'name': 'Default', 'mod': 0, 'usn': 0, 'maxTaken': 60,
    'autoplay': True, 'replayq': True, 'timer': 0,
    'new': {'bury': True, 'delays': [1, 10], 'initialFactor': 2500,
            'ints': [1, 4, 7], 'order': 1, 'perDay': 20, 'separate': True},
    'lapse': {'delays': [10], 'leechAction': 0, 'leechFails': 8, 'minInt': 1,
              'mult': 0},
    'rev': {'bury': True, 'ease4': 1.3, 'fuzz': 0.05, 'ivlFct': 1,
            'maxIvl': 36500, 'minSpace': 1, 'perDay': 100}}}


# --------------------------------------------------------------------------
# The deck
# --------------------------------------------------------------------------

def rows(D: list) -> list:
    """One record per article: the fields, the tags, the guid."""
    kept = fields_kept(D)
    rank = {}
    out = []
    for e in D:
        # The address is shared by twelve articles -- six headwords the book
        # prints twice, six starred words meeting their unstarred twin -- so
        # the rank among them completes it. See tools/machine_readable.py.
        address = slug(e['v'])
        rank[address] = rank.get(address, 0) + 1
        n = rank[address]
        out.append({
            'guid': guid('dicionario', address, n),
            'tags': tags(e, kept),
            'flds': [e['v'], '1' if e.get('c') else '', e.get('f') or '',
                     senses(e), '; '.join(e.get('l') or []),
                     e.get('y') or '', ', '.join(e.get('n') or []),
                     f'p. {e["p"]}, l. {e["g"]}', address,
                     '1' if reversible(e) else ''],
        })
    return out


def write_db(path: Path, notes: list) -> int:
    con = sqlite3.connect(path)
    cur = con.cursor()
    # The page size is set before the first table: left to the build, it is
    # what makes the same deck two different files on two machines.
    cur.execute('PRAGMA page_size = 4096')
    cur.executescript(SCHEMA)

    conf = {'activeDecks': [DECK_ID], 'addToCur': True, 'collapseTime': 1200,
            'curDeck': DECK_ID, 'curModel': str(MODEL_ID), 'dueCounts': True,
            'estTimes': True, 'newBury': True, 'newSpread': 0,
            'nextPos': len(notes) + 1, 'sortBackwards': False,
            'sortType': 'noteFld', 'timeLim': 0}
    dumps = (lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True,
                                 separators=(',', ':')))
    cur.execute('INSERT INTO col VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
        1, CRT, MOD, MOD, 11, 0, 0, 0, dumps(conf),
        dumps({str(MODEL_ID): model_json()}),
        dumps({'1': DEFAULT_DECK, str(DECK_ID): deck_json()}),
        dumps(DEFAULT_CONF), '{}'))

    cards = 0
    for i, n in enumerate(notes):
        nid = NOTE_ID + i
        cur.execute('INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,?,?)', (
            nid, n['guid'], MODEL_ID, CRT, -1,
            ' %s ' % ' '.join(n['tags']) if n['tags'] else '',
            '\x1f'.join(n['flds']), n['flds'][0], csum(n['flds'][0]), 0, ''))
        # The new cards come up in THE BOOK'S ORDER, which is the alphabet:
        # `due` is the article's rank, not the hour the deck was built.
        for ordinal in (0, 1) if n['flds'][-1] else (0,):
            cur.execute(
                'INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (CARD_ID + cards, nid, DECK_ID, ordinal, CRT, -1, 0, 0,
                 i + 1, 0, 0, 0, 0, 0, 0, 0, 0, ''))
            cards += 1

    con.commit()
    con.close()
    return cards


# Anki's schema 11, as Anki writes it.
SCHEMA = """
CREATE TABLE col (id integer primary key, crt integer not null,
    mod integer not null, scm integer not null, ver integer not null,
    dty integer not null, usn integer not null, ls integer not null,
    conf text not null, models text not null, decks text not null,
    dconf text not null, tags text not null);
CREATE TABLE notes (id integer primary key, guid text not null,
    mid integer not null, mod integer not null, usn integer not null,
    tags text not null, flds text not null, sfld integer not null,
    csum integer not null, flags integer not null, data text not null);
CREATE TABLE cards (id integer primary key, nid integer not null,
    did integer not null, ord integer not null, mod integer not null,
    usn integer not null, type integer not null, queue integer not null,
    due integer not null, ivl integer not null, factor integer not null,
    reps integer not null, lapses integer not null, left integer not null,
    odue integer not null, odid integer not null, flags integer not null,
    data text not null);
CREATE TABLE revlog (id integer primary key, cid integer not null,
    usn integer not null, ease integer not null, ivl integer not null,
    lastIvl integer not null, factor integer not null, time integer not null,
    type integer not null);
CREATE TABLE graves (usn integer not null, oid integer not null,
    type integer not null);
CREATE INDEX ix_notes_usn on notes (usn);
CREATE INDEX ix_cards_usn on cards (usn);
CREATE INDEX ix_revlog_usn on revlog (usn);
CREATE INDEX ix_cards_nid on cards (nid);
CREATE INDEX ix_cards_sched on cards (did, queue, due);
CREATE INDEX ix_revlog_cid on revlog (cid);
CREATE INDEX ix_notes_csum on notes (csum);
"""


def build(D: list, out: Path) -> tuple:
    notes = rows(D)
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / 'collection.anki2'
        cards = write_db(db, notes)
        # ZIP_STORED for the database would double the file; the date is
        # fixed for the same reason the identifiers are, a zip entry
        # carrying the hour of its build otherwise.
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, blob in (('collection.anki2', db.read_bytes()),
                               ('media', b'{}')):
                info = zipfile.ZipInfo(name, ZIP_DATE)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, blob)
    return notes, cards


def main() -> None:
    D = json.loads((ROOT / 'dicionario.json').read_text('utf-8'))
    notes, cards = build(D, OUT)

    reverse = sum(1 for n in notes if n['flds'][-1])
    # ANKI FILES A TAG WITHOUT REGARD TO ITS CASE, and the book gives it one
    # occasion to matter: « Anke metaf. » and « anke metaf. » are two
    # parentheticals here and one tag there. The count is folded so that what
    # is printed is what the reader will see -- 221, not 222.
    every = sorted({t.lower() for n in notes for t in n['tags']})
    counted = {p: sum(1 for t in every if t.startswith(p + '::'))
               for p in ('litero', 'fako', 'verbo', 'prepoziciono', 'drapelo')}
    print(f'  dicionario.apkg  {OUT.stat().st_size:>10,} bytes')
    print(f'  {len(notes):,} notes, {cards:,} cards '
          f'({len(notes):,} vedetto → senco, {reverse:,} senco → vedetto)')
    print('  %d tags: %s' % (len(every), ', '.join(
        f'{k} {v}' for k, v in counted.items())))
    print('  sha256 %s' % hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()

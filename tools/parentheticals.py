#!/usr/bin/env python3
"""Decomposes the LEADING PARENTHETICAL of an article, which holds three
different things under one field.

WHY. The Dicionario prints, before the first sense, a bracketed group:

    abdikar. (trans.) (pri rejo od altra suvereno). Cesar sua regno...
    adaptar. (trans., ad) Konformigar ulo ad ulo...
    ablacionar. (trans.)(kirurg.) Deprenar de la korpo homala...

Three different kinds of statement stand there, and `fako` carries all of
them as one string -- « trans.) (kirurg. » being the ordinary shape when
the book sets two groups. Nothing on the site tells them apart, and so
nothing can be asked of them.

  * THE TRANSITIVITY. 1982 articles are marked trans. or netrans. This is
    not a detail of lexicography: in Ido it decides whether a verb takes a
    direct object at all, and therefore whether -ig- or -es- is the right
    derivation. A model writing Ido without it guesses on every verb.
  * THE GOVERNED PREPOSITION. 380 of those verbs name the preposition they
    take -- « adaptar ad », « admirar pri, pro », « admisar aden ». That is
    the difference between Ido a reader can follow and Ido that is merely
    Ido-shaped, and it is printed nowhere but inside this field.
  * THE SUBJECT DOMAIN. 435 distinct values, of which 67 name five articles
    or more: bot. 580, zool. 425, patol. 234, anat. 230.

WHAT IS NOT GOVERNMENT, AND HOW IT IS TOLD APART. « abdikar (pri rejo od
altra suvereno) » opens with a preposition and is NOT government: it is a
note on what sort of subject the verb takes. A first cut keyed to the first
word made « pri rejo od altra suvereno » the government of abdikar, and 33
articles read that way. A government is prepositions AND NOTHING ELSE, so
every token must be a preposition or one of the placeholders ulu / ulo:
« ad », « pri, pro », « ulo, ad ulu » pass; « pri rejo » does not, and is
kept verbatim as a note rather than being classified into something this
tool invented.

THE FIELD ITSELF IS NOT TOUCHED. `fako` stays as export.py writes it, and
the reading page with it; this decomposition acts in the files below alone.

    python3 tools/parentheticals.py     # verbi.md, verbi.json,
                                        # faki.md, faki.json

Run it after tools/all_editions.py: it reads dicionario.json, which that
chain writes.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://ido.help/dicionario/'
HEADER = ('<!-- Engendre par tools/parentheticals.py depuis '
          'dicionario.json. Ne pas editer. -->')

# The book's own prepositions, and the two placeholders it uses for an
# argument: ulu (someone), ulo (something).
PREPOSITIONS = {
    'ad', 'aden', 'adsur', 'an', 'ante', 'apud', 'che', 'cirkum', 'da', 'de',
    'di', 'dum', 'ek', 'en', 'exter', 'inter', 'kom', 'kontre', 'kun',
    'malgre', 'per', 'po', 'por', 'pos', 'preter', 'pri', 'pro', 'segun',
    'sen', 'sub', 'sur', 'til', 'tra', 'trans', 'ye', 'vice',
}
PLACEHOLDERS = {'ulu', 'ulo', 'ula'}
CONJUNCTIONS = {'e', 'ed', 'o', 'od'}
ADMITTED = PREPOSITIONS | PLACEHOLDERS | CONJUNCTIONS

# THE BOOK MARKS A SENSE AS WELL AS AN ARTICLE, AND THE EXPORT WRAPS IT.
# A fako printed inside a sense comes through dicionario.json between two
# private-use sentinels -- \ue000 (fako) \ue001 -- wherever it stands, not
# only at the head: « abasar » carries « Pozar (plu) infre. – (metaf.)
# (aludante persono) Retrodutar... » in the middle of its sense.
SPAN = re.compile('\ue000(.*?)\ue001')

TRANSITIVITY = re.compile(
    r'^(netrans\.\s+e\s+trans\.|trans\.\s+e\s+netrans\.|trans\.|netrans\.)'
    r'\s*(.*)$')


def governs(part: str) -> bool:
    """True where a fragment is a GOVERNMENT and not a note.

    Every token must be a preposition, a placeholder or a conjunction, and
    at least one must carry meaning. « pri rejo od altra suvereno » fails
    on « rejo », which is what keeps it out of the government of abdikar.
    """
    tokens = [t for t in re.split(r'[\s,]+', part) if t]
    if not tokens or not all(t in ADMITTED for t in tokens):
        return False
    return any(t in PREPOSITIONS or t in PLACEHOLDERS for t in tokens)


def decompose(fako):
    """One leading parenthetical as (transitivity, governments, the rest).

    The book sets « (trans.) (kirurg.) » as often as « (trans., ad) », and
    export.py keeps the whole group, so the split is on the boundary
    between two groups before anything else is read.
    """
    parts = [p.strip().strip('()')
             for p in re.split(r'\)\s*\(', fako or '') if p.strip()]
    kind, gov, rest = None, [], []
    for part in parts:
        m = TRANSITIVITY.match(part)
        if m:
            mark = m.group(1)
            kind = ('amba' if ' e ' in mark else
                    'transitiva' if mark.startswith('trans') else
                    'netransitiva')
            tail = m.group(2).lstrip(', ').strip()
            if tail:
                (gov if governs(tail) else rest).append(tail)
        elif governs(part):
            gov.append(part)
        elif part:
            rest.append(part)
    return kind, gov, rest


def read():
    return json.loads((ROOT / 'dicionario.json').read_text('utf-8'))


def parentheticals(record):
    """Every leading parenthetical of an article: (sense number, text).

    Sense number 0 is the article's own, out of `fako`; 1, 2, 3 are the
    senses'. BOTH ARE NEEDED, and reading only the first loses the verbs
    that matter most. MEASURED: 40 verbs are marked at sense level ONLY --
    fugar, finar, komencar, fumar, kombatar, embarkar among them -- and
    they are marked there precisely BECAUSE they are transitive in one
    sense and intransitive in another. A tool reading `fako` alone reports
    1981 verbs, looks complete, and is silent on every verb whose answer
    is « it depends on the sense ».
    """
    if record.get('f'):
        yield 0, record['f']
    for i, sense in enumerate(record.get('b', []), 1):
        for m in SPAN.finditer(sense.get('t') or ''):
            yield i, m.group(1).strip().strip('()')


def verbs(records):
    out = []
    for r in records:
        kinds, gov, rest, per_sense = [], [], [], {}
        for n, text in parentheticals(r):
            kind, g, rs = decompose(text)
            if kind:
                if kind not in kinds:
                    kinds.append(kind)
                if n:
                    per_sense[str(n)] = kind
            gov += [x for x in g if x not in gov]
            rest += [x for x in rs if x not in rest]
        if kinds:
            out.append({'vedetto': r['v'], 'speco': kinds, 'senci': per_sense,
                        'regas': gov, 'noto': rest})
    return out


def domains(records):
    """Every parenthetical that is NOT a transitivity mark, with its words.

    Article level and sense level both. The sense level is not a rounding
    error: « metaf. » marks 229 senses and NOT ONE article, so a tool
    reading `fako` alone does not know the book has a mark for the
    figurative sense at all.
    """
    out = {}
    for r in records:
        for _, text in parentheticals(r):
            for part in re.split(r'\)\s*\(', text):
                part = part.strip().strip('()')
                if part and not TRANSITIVITY.match(part):
                    out.setdefault(part, set()).add(r['v'])
    return {k: sorted(v) for k, v in sorted(out.items())}


def write_verbs(rows):
    kinds = ['transitiva', 'netransitiva', 'amba']
    counts = {k: sum(1 for r in rows if r['speco'] == [k]) for k in kinds}
    counts['segun la senco'] = sum(1 for r in rows if len(r['speco']) > 1)
    ruled = [r for r in rows if r['regas']]

    by_prep = {}
    for r in ruled:
        for g in r['regas']:
            by_prep.setdefault(g, []).append(r['vedetto'])
    by_prep = {k: sorted(v) for k, v in sorted(by_prep.items())}

    L = [HEADER, '',
         '# Verbi — Dicionario de la 10.000 radiki', '',
         'La marki *(trans.)* e *(netrans.)*, e la prepoziciono quan la '
         'verbo regas, quale la libro printas li. Nulo esas hike kompozita '
         ': omno venas de la parentezo qua preiras la unesma senco.', '',
         f'Transskribita de {SITE}', '',
         f'{len(rows)} verbi markizita : {counts["transitiva"]} transitiva, '
         f'{counts["netransitiva"]} netransitiva, {counts["amba"]} amba, '
         f'{counts["segun la senco"]} qui chanjas segun la senco. '
         f'{len(ruled)} regas prepoziciono.', '',
         '## Omna verbi', '',
         'Vedvorto — speco — prepoziciono regata (se existas).', '']
    for r in rows:
        if r['senci'] and len(r['speco']) > 1:
            speco = ', '.join(f'{k} (senco {n})'
                              for n, k in sorted(r['senci'].items()))
        else:
            speco = ', '.join(r['speco'])
        line = f'{r["vedetto"]} — {speco}'
        if r['regas']:
            line += ' — ' + '; '.join(r['regas'])
        L.append(line)

    L += ['', '## Per prepoziciono regata', '',
          'Qua verbi regas qua prepoziciono.', '']
    for prep, words in by_prep.items():
        L.append(f'**{prep}** ({len(words)}) — ' + ', '.join(words))

    noted = [r for r in rows if r['noto']]
    L += ['', '## Noti', '',
          'La parentezi qui ne esas nek speco nek prepoziciono : la libro '
          'dicas hike pri qua subjekto o en qua fako la verbo uzesas. Li '
          f'esas konservita quale printita. ({len(noted)} verbi.)', '']
    for r in noted:
        L.append(f'{r["vedetto"]} — ' + '; '.join(r['noto']))

    (ROOT / 'verbi.md').write_text('\n'.join(L) + '\n', 'utf-8')

    body = {
        'pri': 'La verbi dil Dicionario: speco (transitiva o ne) e la '
               'prepoziciono regata. De la parentezo qua preiras la unesma '
               'senco; nulo kompozita.',
        'fonto': SITE,
        'nombri': {**counts, 'kun prepoziciono': len(ruled)},
        'verbi': {r['vedetto']: {k: v for k, v in
                                 (('speco', r['speco']), ('senci', r['senci']),
                                  ('regas', r['regas']), ('noto', r['noto']))
                                 if v}
                  for r in rows},
        'per prepoziciono': by_prep,
    }
    (ROOT / 'verbi.json').write_text(
        json.dumps(body, ensure_ascii=False, separators=(',', ':')) + '\n',
        'utf-8')
    return counts, len(ruled), len(by_prep)


def write_domains(doms):
    big = {k: v for k, v in doms.items() if len(v) >= 5}
    L = [HEADER, '',
         '# Faki — Dicionario de la 10.000 radiki', '',
         'La fako printita en parentezo avan la unesma senco, e la vorti '
         'quin ol markizas. La marki *(trans.)* e *(netrans.)* ne esas '
         'faki : li esas en `verbi.md`.', '',
         f'Transskribita de {SITE}', '',
         f'{len(doms)} parentezi diferanta, de qui {len(big)} markizas kin '
         'vorti o plu. La ceteri esas ofte noti pri un sola vorto, e li '
         'esas konservita infre quale printita.', '',
         '## Faki di kin vorti o plu', '']
    for k, v in sorted(big.items(), key=lambda x: (-len(x[1]), x[0])):
        L.append(f'**{k}** ({len(v)}) — ' + ', '.join(v))
    L += ['', '## La ceteri', '']
    for k, v in sorted(doms.items()):
        if len(v) < 5:
            L.append(f'**{k}** ({len(v)}) — ' + ', '.join(v))
    (ROOT / 'faki.md').write_text('\n'.join(L) + '\n', 'utf-8')

    (ROOT / 'faki.json').write_text(json.dumps(
        {'pri': 'La faki dil Dicionario e lia vorti. La marki (trans.) e '
                '(netrans.) esas en verbi.json.',
         'fonto': SITE, 'faki': doms},
        ensure_ascii=False, separators=(',', ':')) + '\n', 'utf-8')
    return len(doms), len(big)


def main():
    records = read()
    rows = verbs(records)
    counts, ruled, preps = write_verbs(rows)
    ndom, nbig = write_domains(domains(records))
    print(f'  verbi.md   {len(rows)} verbi — {counts["transitiva"]} trans., '
          f'{counts["netransitiva"]} netrans., {counts["amba"]} amba, '
          f'{counts["segun la senco"]} segun la senco')
    print(f'             {ruled} regas prepoziciono, {preps} formi diferanta')
    print(f'  faki.md    {ndom} parentezi, {nbig} markizas kin vorti o plu')
    for f in ('verbi.md', 'verbi.json', 'faki.md', 'faki.json'):
        print(f'  {f:14s} {(ROOT / f).stat().st_size:,} bytes')


if __name__ == '__main__':
    main()

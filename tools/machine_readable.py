#!/usr/bin/env python3
"""Draws from the Dicionario its MACHINE-READABLE versions.

WHY THIS SCRIPT EXISTS. The Dicionario's page is built by JavaScript: the
9473 articles live in an array the browser unrolls at load. That is excellent
for instant search, and disastrous for anything that does not run it. An
indexing robot with no JS engine, a site mirror, a language model that goes to
the address: all of them see 213 characters, which is to say nothing.

Four things repair that, each for one use:

  dicionario.json  the data as they are, without the JavaScript around them.
                   For whoever wants to query, filter, recount.
  dicionario.md    the book laid flat, one article after another. For reading.
  vortlisto.md     headword and first sense only. Far shorter: enough to fit
                   in a context window when the whole Dicionario would not.
  vorti/           ONE FILE PER WORD, some 500 bytes each, at an address a
                   reader can WORK OUT from the headword. See below.

WHY vorti/ WAS ADDED. Every file above is the whole book. To learn what one
word means, the cheapest of them still cost 923 kB, and the reading page
costs 2.1 MB -- and a model that fetches the page is truncated long before
the letter P. ASKED WHAT « propoziciono » MEANT, ChatGPT ANSWERED WITH THE
SENSES OF THE ENGLISH « proposition » -- proposal, offer, logical assertion --
none of which is in the article, which gives (logiko), (gram.), (geom.) and
(teol.). It then fetched the page, was truncated, and gave up. One file per
word is the answer to that: 500 bytes, and no search to run.

They are GENERATED, never edited by hand. The source stays index.html.

    python3 tools/machine_readable.py
"""

import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_data(html: str) -> list:
    """Finds the array D in the script, and returns it as Python objects.

    We do not look for the end of the array by hand -- one bracket in a
    definition would be enough to fool the count. The JSON decoder stops of
    itself in the right place and tells us where.
    """
    m = re.search(r'\bconst\s+D\s*=\s*\[', html)
    if not m:
        raise SystemExit('array D not found in index.html')
    start_of = html.index('[', m.start())
    data_, _ = json.JSONDecoder().raw_decode(html[start_of:])
    return data_


def text_(t: str) -> str:
    """The text of the definitions carries a light markup, peculiar to the book.

    We render it as Markdown rather than throw it away: the Dicionario's
    italics distinguish the examples from the glosses, and that distinction
    carries sense.
    """
    if not t:
        return ''
    t = re.sub(r'<i>(.*?)</i>', r'*\1*', t, flags=re.S)
    t = re.sub(r'<b>(.*?)</b>', r'**\1**', t, flags=re.S)
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def entry(e: dict) -> str:
    """One article, in Markdown. Follows the same form as the page."""
    hw = f'« {e["v"]} »' if e.get('c') else e['v']
    lin = [f'## {hw}' + (f' *({e["f"]})*' if e.get('f') else '')]

    senses = e.get('b') or []
    for i, b in enumerate(senses):
        num = f'{i + 1}. ' if len(senses) > 1 else ''
        if b.get('t') or not b.get('u'):
            lin.append(num + text_(b.get('t', '')))
            num = ''
        for x in b.get('u') or []:
            part = [num + f'**{x["k"]}**']
            if x.get('q'):
                part.append(f'*({x["q"]})*')
            part.append(text_(x.get('t', '')))
            if x.get('n'):
                part.append(f'[{", ".join(x["n"])}]')
            lin.append(' '.join(p for p in part if p))
            num = ''

    if e.get('l'):
        lin.append(f'L. {"; ".join(e["l"])}')
    if e.get('y'):
        lin.append(f'*Simb. kem.* **{e["y"]}**')

    method_ = [f'p. {e["p"]}, l. {e["g"]}']
    if e.get('n'):
        method_.append(', '.join(e['n']))
    if e.get('d'):
        method_.append(' · '.join(e['d']))
    lin.append(f'<!-- {" | ".join(method_)} -->')
    return '\n'.join(lin)



# --------------------------------------------------------------------------
# vorti/ -- one file per word
# --------------------------------------------------------------------------
# THE ADDRESS HAS TO BE WORKED OUT, NOT LOOKED UP. The whole gain is that a
# reader who knows the headword knows the address without fetching an index
# first, so the rule is four steps and no more: lower case, fold the accent,
# space becomes a hyphen, drop what is left. Ido's own alphabet is plain
# ASCII, so the rule touches almost nothing -- « propoziciono » is already
# its own address.
#
# WHAT IT DROPS, AND WHY THAT IS SAFE. Four marks carry sense in this book
# and none of them survives a URL: the asterisk of the word NOT OFFICIAL, the
# exclamation of the interjections, the parentheses of « a(d) », and the
# guillemets of « «brokoli»-kaulo ». They are dropped from the ADDRESS and
# kept in the FILE, whose heading prints the headword as the book sets it.
#
# MEASURED, over the 9473 articles: 9461 distinct addresses. Twelve are
# shared -- six by a headword the book prints twice (do, harmoniko,
# intendanto, la, *nexta, *stejo), six by a starred word meeting its
# unstarred twin (e(d)/ed, o(d)/od, *frua/frua, *si/si, *tarda/tarda,
# *timbro/timbro). A SHARED ADDRESS HOLDS BOTH ARTICLES, one after the
# other. That is why the rule needs no disambiguating suffix: a suffix
# would have to be looked up, which is the thing being avoided, and a
# reader who asks for « si » wants to see both anyway.
SLUG_KEEP = re.compile(r'[^a-z0-9-]')


def slug(v: str) -> str:
    """The address of a headword. See the note above for the rule."""
    s = unicodedata.normalize('NFD', v.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = SLUG_KEEP.sub('', s.replace(' ', '-'))
    return re.sub(r'-{2,}', '-', s)


def write_articles(D: list, header: str) -> tuple:
    """One file per address, under vorti/.

    THE DIRECTORY IS EMPTIED FIRST. A headword corrected in a later pass
    changes its address, and the file at the old one would otherwise stay
    behind for ever -- served, indexed, and wrong.
    """
    out = ROOT / 'vorti'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()

    by_slug = {}
    for e in D:
        by_slug.setdefault(slug(e['v']), []).append(e)

    for name, group in by_slug.items():
        body = [header,
                '',
                '\n\n'.join(entry(e) for e in group),
                '',
                '---',
                '',
                '*Dicionario de la 10.000 radiki di la linguo universala '
                'Ido*, Marcelo Persiko (Marcel Pesch), 1934/1964.',
                '',
                'La defini esas en Ido. La lingui indikata esas ti en qui '
                'la radiko esas atestata — li ne esas tradukuri.',
                '',
                'Vortlisto : ../vortlisto.md · Kompleta libro : '
                '../dicionario.md · Pagino : ../?q=' + name,
                '']
        (out / (name + '.md')).write_text('\n'.join(body), encoding='utf-8')

    # The index exists for the CRAWLER, which cannot work an address out, and
    # not for the reader, who can. It is therefore a plain list of links.
    shared = {k: v for k, v in by_slug.items() if len(v) > 1}
    SHOWN = ('propoziciono', '-a', 'a(d)', 'a posteriori', '*golfo', 'ah!',
             'ampère', '«brokoli»-kaulo')
    have = {e['v'] for e in D}
    idx = [header,
           '# Vorti — Dicionario de la 10.000 radiki\n',
           'Un dosiero por singla vorto, cirkum %d okteti. La adreso esas la '
           'vedvorto ipsa :\n' % (sum(f.stat().st_size for f in out.glob('*.md'))
                                 // max(len(by_slug), 1)),
           '| vedvorto | adreso |',
           '| --- | --- |']
    idx += ['| `%s` | [`%s.md`](%s.md) |' % (v, slug(v), slug(v))
            for v in SHOWN if v in have]
    idx += ['',
            '%s artikli en %s adresi ; %d adresi kontenas plu kam un '
            'artiklo.\n'
            % (f'{len(D):,}'.replace(',', '\u202f'),
               f'{len(by_slug):,}'.replace(',', '\u202f'), len(shared)),
            'La defini esas en Ido. La lingui indikata en singla artiklo esas '
            'ti en qui la radiko esas atestata — li ne esas tradukuri.\n',
            'Transskribita de https://ido.help/dicionario/\n',
            '---\n']
    for name in sorted(by_slug):
        words = ', '.join(e['v'] for e in by_slug[name])
        idx.append('- [%s](%s.md)%s' % (name, name,
                                        '' if words == name else ' — ' + words))
    (out / 'index.md').write_text('\n'.join(idx) + '\n', encoding='utf-8')
    return len(by_slug), shared


def first_sense(e: dict) -> str:
    """The first sense, shorn of all the rest. Serves the short list."""
    for b in e.get('b') or []:
        if b.get('t'):
            return text_(b['t'])
        for x in b.get('u') or []:
            if x.get('t'):
                return text_(x['t'])
    return ''


def main() -> None:
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    D = read_data(html)

    HEADER = (
        '<!-- Engendre par tools/machine_readable.py depuis index.html. Ne pas editer. -->\n'
    )

    # 1. The bare data.
    (ROOT / 'dicionario.json').write_text(
        json.dumps(D, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    # 2. The book laid flat.
    whole = [HEADER,
            '# Dicionario de la 10.000 radiki di la linguo universala Ido\n',
            'Marcelo Persiko (Marcel Pesch) · editio princeps 1934, '
            'duesma editio 1964 · ' + f'{len(D):,}'.replace(',', '\u202f')
            + ' artikli\n',
            'Transskribita de https://ido.help/dicionario/\n',
            '---\n']
    whole += [entry(e) + '\n' for e in D]
    (ROOT / 'dicionario.md').write_text('\n'.join(whole), encoding='utf-8')

    # 3. The short list.
    brief = [HEADER,
             '# Vortlisto — Dicionario de la 10.000 radiki\n',
             'Vedvorto e unesma senco nur. La kompleta artikli esas en '
             'dicionario.md ; la datumi en dicionario.json.\n',
             'Transskribita de https://ido.help/dicionario/\n']
    for e in D:
        s = first_sense(e)
        brief.append(f'{e["v"]}' + (f' ({e["f"]})' if e.get('f') else '')
                     + (f' — {s}' if s else ''))
    (ROOT / 'vortlisto.md').write_text('\n'.join(brief) + '\n', encoding='utf-8')

    # 4. One file per word.
    n_slugs, shared = write_articles(D, HEADER.rstrip('\n'))

    for n in ('dicionario.json', 'dicionario.md', 'vortlisto.md'):
        print(f'  {n:<18} {(ROOT / n).stat().st_size:>10,} bytes')
    total = sum(f.stat().st_size for f in (ROOT / 'vorti').glob('*.md'))
    print(f'  {"vorti/":<18} {total:>10,} bytes'
          f'  in {n_slugs + 1:,} files, {total // n_slugs:,} bytes each')
    if shared:
        print('  %d addresses hold more than one article: %s'
              % (len(shared), ', '.join(sorted(shared))))


if __name__ == '__main__':
    main()

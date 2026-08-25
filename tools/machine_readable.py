#!/usr/bin/env python3
"""Draws from the Dicionario its MACHINE-READABLE versions.

WHY THIS SCRIPT EXISTS. The Dicionario's page is built by JavaScript: the
9473 articles live in an array the browser unrolls at load. That is excellent
for instant search, and disastrous for anything that does not run it. An
indexing robot with no JS engine, a site mirror, a language model that goes to
the address: all of them see 213 characters, which is to say nothing.

Three files repair that, each for one use:

  dicionario.json  the data as they are, without the JavaScript around them.
                   For whoever wants to query, filter, recount.
  dicionario.md    the book laid flat, one article after another. For reading.
  vortlisto.md     headword and first sense only. Far shorter: enough to fit
                   in a context window when the whole Dicionario would not.

They are GENERATED, never edited by hand. The source stays index.html.

    python3 tools/machine_readable.py
"""

import json
import re
import sys
from pathlib import Path

RACINO = Path(__file__).resolve().parent.parent


def lektar_datumi(html: str) -> list:
    """Finds the array D in the script, and returns it as Python objects.

    We do not look for the end of the array by hand -- one bracket in a
    definition would be enough to fool the count. The JSON decoder stops of
    itself in the right place and tells us where.
    """
    m = re.search(r'\bconst\s+D\s*=\s*\[', html)
    if not m:
        raise SystemExit('array D not found in index.html')
    debuto = html.index('[', m.start())
    datumi, _ = json.JSONDecoder().raw_decode(html[debuto:])
    return datumi


def texto(t: str) -> str:
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


def artiklo(e: dict) -> str:
    """One article, in Markdown. Follows the same form as the page."""
    hw = f'« {e["v"]} »' if e.get('c') else e['v']
    lin = [f'## {hw}' + (f' *({e["f"]})*' if e.get('f') else '')]

    senses = e.get('b') or []
    for i, b in enumerate(senses):
        num = f'{i + 1}. ' if len(senses) > 1 else ''
        if b.get('t') or not b.get('u'):
            lin.append(num + texto(b.get('t', '')))
            num = ''
        for x in b.get('u') or []:
            part = [num + f'**{x["k"]}**']
            if x.get('q'):
                part.append(f'*({x["q"]})*')
            part.append(texto(x.get('t', '')))
            if x.get('n'):
                part.append(f'[{", ".join(x["n"])}]')
            lin.append(' '.join(p for p in part if p))
            num = ''

    if e.get('l'):
        lin.append(f'L. {"; ".join(e["l"])}')
    if e.get('y'):
        lin.append(f'*Simb. kem.* **{e["y"]}**')

    meto = [f'p. {e["p"]}, l. {e["g"]}']
    if e.get('n'):
        meto.append(', '.join(e['n']))
    if e.get('d'):
        meto.append(' · '.join(e['d']))
    lin.append(f'<!-- {" | ".join(meto)} -->')
    return '\n'.join(lin)


def unesma_senco(e: dict) -> str:
    """The first sense, shorn of all the rest. Serves the short list."""
    for b in e.get('b') or []:
        if b.get('t'):
            return texto(b['t'])
        for x in b.get('u') or []:
            if x.get('t'):
                return texto(x['t'])
    return ''


def main() -> None:
    html = (RACINO / 'index.html').read_text(encoding='utf-8')
    D = lektar_datumi(html)

    ENTETE = (
        '<!-- Engendre par tools/machine_readable.py depuis index.html. Ne pas editer. -->\n'
    )

    # 1. The bare data.
    (RACINO / 'dicionario.json').write_text(
        json.dumps(D, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    # 2. The book laid flat.
    tuto = [ENTETE,
            '# Dicionario de la 10.000 radiki di la linguo universala Ido\n',
            'Marcelo Persiko (Marcel Pesch) · editio princeps 1934, '
            'duesma editio 1964 · ' + f'{len(D):,}'.replace(',', '\u202f')
            + ' artikli\n',
            'Transskribita de https://ido.help/dicionario/\n',
            '---\n']
    tuto += [artiklo(e) + '\n' for e in D]
    (RACINO / 'dicionario.md').write_text('\n'.join(tuto), encoding='utf-8')

    # 3. The short list.
    kurta = [ENTETE,
             '# Vortlisto — Dicionario de la 10.000 radiki\n',
             'Vedvorto e unesma senco nur. La kompleta artikli esas en '
             'dicionario.md ; la datumi en dicionario.json.\n',
             'Transskribita de https://ido.help/dicionario/\n']
    for e in D:
        s = unesma_senco(e)
        kurta.append(f'{e["v"]}' + (f' ({e["f"]})' if e.get('f') else '')
                     + (f' — {s}' if s else ''))
    (RACINO / 'vortlisto.md').write_text('\n'.join(kurta) + '\n', encoding='utf-8')

    for n in ('dicionario.json', 'dicionario.md', 'vortlisto.md'):
        print(f'  {n:<18} {(RACINO / n).stat().st_size:>10,} octets')


if __name__ == '__main__':
    main()

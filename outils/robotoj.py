#!/usr/bin/env python3
"""Tire du Dicionario ses versions LISIBLES PAR LES MACHINES.

POURQUOI CE SCRIPT EXISTE. La page du Dicionario est batie par du
JavaScript : les 9473 articles vivent dans un tableau que le navigateur
deroule au chargement. C'est excellent pour la recherche instantanee, et
desastreux pour tout ce qui ne l'execute pas. Un robot d'indexation sans
moteur JS, un aspirateur de site, un modele de langue qui va chercher
l'adresse : tous ne voient que 213 caracteres, c'est-a-dire rien.

Trois fichiers reparent cela, chacun pour un usage :

  dicionario.json  les donnees telles quelles, sans le JavaScript autour.
                   Pour qui veut interroger, filtrer, recompter.
  dicionario.md    le livre a plat, un article apres l'autre. Pour qui lit.
  vortlisto.md     vedette et premier sens seulement. Beaucoup plus court :
                   de quoi tenir dans une fenetre de contexte quand le
                   Dicionario entier n'y tiendrait pas.

Ils sont ENGENDRES, jamais edites a la main. La source reste index.html.

    python3 outils/robotoj.py
"""

import json
import re
import sys
from pathlib import Path

RACINO = Path(__file__).resolve().parent.parent


def lektar_datumi(html: str) -> list:
    """Retrouve le tableau D dans le script, et le rend en objets Python.

    On ne cherche pas la fin du tableau a la main — un crochet dans une
    definition suffirait a tromper le compte. Le decodeur JSON s'arrete
    de lui-meme au bon endroit et nous dit ou.
    """
    m = re.search(r'\bconst\s+D\s*=\s*\[', html)
    if not m:
        raise SystemExit('tableau D introuvable dans index.html')
    debuto = html.index('[', m.start())
    datumi, _ = json.JSONDecoder().raw_decode(html[debuto:])
    return datumi


def texto(t: str) -> str:
    """Le texte des definitions porte un balisage leger, propre au livre.

    On le rend en Markdown plutot que de le jeter : les italiques du
    Dicionario distinguent les exemples des gloses, et cette distinction
    porte du sens.
    """
    if not t:
        return ''
    t = re.sub(r'<i>(.*?)</i>', r'*\1*', t, flags=re.S)
    t = re.sub(r'<b>(.*?)</b>', r'**\1**', t, flags=re.S)
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def artiklo(e: dict) -> str:
    """Un article, en Markdown. Suit la meme forme que la page."""
    ved = f'« {e["v"]} »' if e.get('c') else e['v']
    lin = [f'## {ved}' + (f' *({e["f"]})*' if e.get('f') else '')]

    senci = e.get('b') or []
    for i, b in enumerate(senci):
        num = f'{i + 1}. ' if len(senci) > 1 else ''
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
    """Le premier sens, ampute de tout le reste. Sert la liste courte."""
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
        '<!-- Engendre par outils/robotoj.py depuis index.html. Ne pas editer. -->\n'
    )

    # 1. Les donnees nues.
    (RACINO / 'dicionario.json').write_text(
        json.dumps(D, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    # 2. Le livre a plat.
    tuto = [ENTETE,
            '# Dicionario de la 10.000 radiki di la linguo universala Ido\n',
            'Marcelo Persiko (Marcel Pesch) · editio princeps 1934, '
            'duesma editio 1964 · ' + f'{len(D):,}'.replace(',', '\u202f')
            + ' artikli\n',
            'Transskribita de https://ido.help/dicionario/\n',
            '---\n']
    tuto += [artiklo(e) + '\n' for e in D]
    (RACINO / 'dicionario.md').write_text('\n'.join(tuto), encoding='utf-8')

    # 3. La liste courte.
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

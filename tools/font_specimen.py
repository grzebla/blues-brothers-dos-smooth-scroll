#!/usr/bin/env python3
"""Próbki i pokrycie znaków fontów lokalizacji.

Użycie:
    python tools/font_specimen.py [--locale pl] [--output docs/img/fonts.png]

Dla każdego fontu z localization/<locale>/fonts/ renderuje wszystkie glify
(4x powiększenie, paleta odpowiedniego zasobu) i wypisuje, których polskich
liter brakuje. Pomaga przy zmianie tłumaczenia: tekst graficzny może używać
tylko znaków obecnych w foncie danego napisu.
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbformats as bf  # noqa: E402
import glyphkit as gk  # noqa: E402

POLISH = 'ĄĆĘŁŃÓŚŹŻ'
PALETTE_SOURCE = {'choix': 'CHOIX.SQZ', 'inter_chem': 'INTER.SQZ', 'inter_store': 'INTER.SQZ',
                  'neon': 'MAG.CK2', 'plaque': 'VILLE.CK1', 'popup': 'MAG.CK1'}
BACKGROUND = {'neon': 11, 'plaque': 3, 'inter_chem': 14}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--locale', default='pl')
    ap.add_argument('--source', default='original')
    ap.add_argument('--output', default=os.path.join('docs', 'img', 'fonts.png'))
    args = ap.parse_args()
    rows = []
    for path in sorted(glob.glob(os.path.join('localization', args.locale, 'fonts', '*.json'))):
        name = os.path.basename(path)[:-5]
        f = gk.load_font(path)
        chars = ''.join(sorted(f['glyphs']))
        missing = [c for c in POLISH if c not in f['glyphs']]
        print('%-12s %3d glifów, polskie: %s%s' % (name, len(chars), ''.join(c for c in POLISH if c in f['glyphs']) or '-',
                                                   ('  (brak: %s)' % ''.join(missing)) if missing else ''))
        pal = bf.ILBM.parse(bf.unpack(open(os.path.join(args.source, PALETTE_SOURCE[name]), 'rb').read())).palette
        arr = gk.render_text(f, chars)
        bg = BACKGROUND.get(name, 0)
        arr = np.where(arr == gk.TRANSPARENT, bg, arr).astype(np.uint8)
        img = Image.fromarray(arr, 'P')
        img.putpalette([c for rgb in pal for c in rgb] + [0] * (768 - 3 * len(pal)))
        rows.append((name, img.convert('RGB').resize((arr.shape[1] * 4, arr.shape[0] * 4), Image.NEAREST)))
    W = max(r[1].width for r in rows) + 10
    H = sum(r[1].height + 22 for r in rows)
    out = Image.new('RGB', (W, H), (40, 40, 40))
    d = ImageDraw.Draw(out)
    y = 0
    for name, im in rows:
        d.text((4, y + 4), name, fill=(255, 255, 255))
        out.paste(im, (4, y + 18))
        y += im.height + 22
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    out.save(args.output)
    print('Zapisano', args.output)


if __name__ == '__main__':
    main()

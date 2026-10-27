#!/usr/bin/env python3
"""Import zmodyfikowanych grafik (PNG) z powrotem do formatów gry.

Użycie:
    python tools/import.py --source original --locale pl --output work/imported

Dla każdego pliku w localization/<locale>/graphics/:
  * <PLIK>.png                (np. CHOIX.SQZ.png, MAG.CK2.png) - obraz ILBM,
  * SPRITE.SQV/frame_NNN.png  - pojedyncze klatki sprite'ów,
sprawdza zgodność palety i wymiarów, koduje ILBM (ByteRun1) / SQV (planarnie),
kompresuje formatem Titus i weryfikuje ograniczenia silnika:
  * ILBM ekranów i kafli po dekompresji <= 30000 bajtów,
  * dekoder z 1.EXE nie zapisze więcej niż 1 bajt ponad rozmiar,
  * SPRITE.SQV po dekompresji <= 64000 bajtów,
  * dekompresja wyniku daje dokładnie zaimportowane piksele.
"""
import argparse
import glob
import os
import re
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbformats as bf  # noqa: E402
import gamedata as gd  # noqa: E402


class ImportError_(Exception):
    pass


def read_png(path, expect_w=None, expect_h=None, palette=None):
    img = Image.open(path)
    if img.mode != 'P':
        raise ImportError_('%s: PNG musi być w trybie indeksowanym (P), jest %s' % (path, img.mode))
    a = np.array(img, dtype=np.uint8)
    h, w = a.shape
    if expect_w is not None and (w != expect_w or h != expect_h):
        raise ImportError_('%s: wymiary %dx%d, oczekiwano %dx%d' % (path, w, h, expect_w, expect_h))
    if a.max() > 15:
        raise ImportError_('%s: użyto indeksu koloru %d (dozwolone 0-15)' % (path, a.max()))
    if palette is not None:
        pal = img.getpalette()[:48]
        want = [c for rgb in palette for c in rgb][:48]
        if pal[:len(want)] != want:
            raise ImportError_('%s: paleta PNG różni się od oryginalnej (zmieniono kolory?)' % path)
    return a


def import_ilbm(src, name, png_path):
    raw = open(gd.find_file(src, name), 'rb').read()
    im = bf.ILBM.parse(bf.unpack(raw))
    a = read_png(png_path, im.width, im.height, im.palette)
    orig = np.array(im.pixels, dtype=np.uint8).reshape(im.height, im.width)
    changed = int((a != orig).sum())
    if changed == 0:
        return None, 0
    im.pixels = bytearray(a.tobytes())
    ilbm = im.encode()
    if len(ilbm) > gd.SCREEN_ILBM_MAX:
        raise ImportError_('%s: ILBM po kodowaniu ma %d B (limit %d B)' % (name, len(ilbm), gd.SCREEN_ILBM_MAX))
    packed = bf.pack(ilbm)
    over = bf.dos_overrun(packed)
    if over > gd.MAX_DOS_OVERRUN:
        raise ImportError_('%s: dekoder DOS zapisze %d B nadmiaru' % (name, over))
    back = bf.ILBM.parse(bf.unpack(packed))
    if bytes(back.pixels) != a.tobytes() or back.palette != im.palette:
        raise ImportError_('%s: weryfikacja po kompresji nie powiodła się' % name)
    return packed, changed


def import_sqv(src, name, frame_dir, palette):
    raw = open(gd.find_file(src, name), 'rb').read()
    data = bf.unpack(raw)
    frames, rest = bf.parse_sqv(data)
    out = [(f['w'], f['h'], f['data']) for f in frames]
    changed = []
    for path in sorted(glob.glob(os.path.join(frame_dir, 'frame_*.png'))):
        m = re.search(r'frame_(\d+)\.png$', path)
        idx = int(m.group(1))
        if idx >= len(frames):
            raise ImportError_('%s: brak klatki %d w %s' % (path, idx, name))
        a = read_png(path, palette=palette)
        h, w = a.shape
        if w % 16:
            raise ImportError_('%s: szerokość klatki %d nie jest wielokrotnością 16' % (path, w))
        planar = bf.encode_planar(a.tobytes(), w, h)
        if (w, h, planar) != out[idx]:
            out[idx] = (w, h, planar)
            changed.append((idx, frames[idx]['w'], frames[idx]['h'], w, h))
    if not changed:
        return None, []
    newdata = bf.build_sqv(out, rest)
    if len(newdata) > gd.SPRITE_SQV_MAX:
        raise ImportError_('%s: %d B po dekompresji (limit %d B)' % (name, len(newdata), gd.SPRITE_SQV_MAX))
    packed = bf.pack(newdata)
    if bf.unpack(packed) != newdata:
        raise ImportError_('%s: weryfikacja po kompresji nie powiodła się' % name)
    if bf.dos_overrun(packed) > gd.MAX_DOS_OVERRUN:
        raise ImportError_('%s: nadmiar dekodera DOS' % name)
    return packed, changed


def import_all(src, locale, log):
    """Zwraca słownik nazwa_pliku -> nowe bajty (tylko zmienione pliki)."""
    gdir = os.path.join('localization', locale, 'graphics')
    result = {}
    for path in sorted(glob.glob(os.path.join(gdir, '*.png'))):
        name = os.path.basename(path)[:-4]
        if name.upper() not in gd.KNOWN_FILES or name.upper() not in gd.ILBM_FILES:
            raise ImportError_('%s: nieznany plik docelowy %s' % (path, name))
        packed, changed = import_ilbm(src, name.upper(), path)
        if packed is None:
            log.append('  %-12s bez zmian względem oryginału' % name)
            continue
        result[name.upper()] = packed
        log.append('  %-12s zmienionych pikseli: %5d, %d B' % (name.upper(), changed, len(packed)))
    sdir = os.path.join(gdir, 'SPRITE.SQV')
    if os.path.isdir(sdir):
        pal = bf.ILBM.parse(bf.unpack(open(gd.find_file(src, 'MAG.CK1'), 'rb').read())).palette
        packed, changed = import_sqv(src, 'SPRITE.SQV', sdir, pal)
        if packed is not None:
            result['SPRITE.SQV'] = packed
            for idx, ow, oh, w, h in changed:
                log.append('  SPRITE.SQV   klatka %d: %dx%d -> %dx%d' % (idx, ow, oh, w, h))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', default='original')
    ap.add_argument('--locale', default='pl')
    ap.add_argument('--output', default='work/imported')
    args = ap.parse_args()
    log = []
    try:
        res = import_all(args.source, args.locale, log)
    except ImportError_ as e:
        print('BŁĄD:', e)
        return 1
    os.makedirs(args.output, exist_ok=True)
    for name, data in res.items():
        with open(os.path.join(args.output, name), 'wb') as f:
            f.write(data)
    print('\n'.join(log))
    print('Zaimportowano %d plików do %s' % (len(res), args.output))
    return 0


if __name__ == '__main__':
    sys.exit(main())

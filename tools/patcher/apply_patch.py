#!/usr/bin/env python3
"""Instalator polskiej wersji The Blues Brothers (DOS, Titus 1991).

Użycie (z katalogu, w którym leży ten plik):
    python apply_patch.py ŚCIEŻKA_DO_GRY            instalacja polonizacji
    python apply_patch.py ŚCIEŻKA_DO_GRY --check    tylko sprawdzenie zgodności plików
    python apply_patch.py ŚCIEŻKA_DO_GRY --restore  przywrócenie wersji angielskiej z kopii

Wymagania: Python 3.6+ (bez dodatkowych pakietów).

Patch zawiera wyłącznie zmienione bajty i piksele (polskie napisy) - nie
zawiera plików gry. Przed zmianą każdy plik jest weryfikowany sumą SHA-256;
pliki o innej zawartości nie są modyfikowane. Oryginały trafiają do
podkatalogu KOPIA_EN/ w katalogu gry.
"""
import argparse
import base64
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bbformats as bf  # noqa: E402

BACKUP_DIR = 'KOPIA_EN'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def find(game, name):
    for n in os.listdir(game):
        if n.upper() == name.upper():
            return os.path.join(game, n)
    return None


def apply_bytes(data, entry):
    buf = bytearray(data)
    for off, hexdata in entry['bytes']:
        new = bytes.fromhex(hexdata)
        buf[off:off + len(new)] = new
    return bytes(buf)


def apply_pixels(pixels, width, regions):
    for reg in regions:
        x, y, w, h = reg['rect']
        mask = base64.b64decode(reg['mask'])
        vals = base64.b64decode(reg['values'])
        k = 0
        for i in range(w * h):
            if mask[i >> 3] & (0x80 >> (i & 7)):
                pixels[(y + i // w) * width + x + i % w] = vals[k]
                k += 1
    return pixels


def apply_ilbm(data, entry):
    im = bf.ILBM.parse(bf.unpack(data))
    apply_pixels(im.pixels, im.width, entry['regions'])
    return bf.pack(im.encode())


def apply_sqv(data, entry):
    frames, rest = bf.parse_sqv(bf.unpack(data))
    out = [(f['w'], f['h'], f['data']) for f in frames]
    for fr in entry['frames']:
        idx, w, h = fr['index'], fr['w'], fr['h']
        if fr.get('regions') is not None:
            # zmiana fragmentu klatki o niezmienionym rozmiarze
            pix = bytearray(bf.decode_planar(out[idx][2], out[idx][0], out[idx][1]))
            apply_pixels(pix, w, fr['regions'])
        else:
            pix = bytearray(base64.b64decode(fr['pixels']))
        out[idx] = (w, h, bf.encode_planar(bytes(pix), w, h))
    return bf.pack(bf.build_sqv(out, rest))


METHODS = {'bytes': apply_bytes, 'ilbm': apply_ilbm, 'sqv': apply_sqv}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('game', help='katalog z grą (zawiera 1.EXE)')
    ap.add_argument('--check', action='store_true', help='tylko sprawdź pliki')
    ap.add_argument('--restore', action='store_true', help='przywróć wersję angielską z kopii')
    args = ap.parse_args()
    with open(os.path.join(HERE, 'patch.json'), encoding='utf-8') as f:
        patch = json.load(f)
    game = args.game
    if not os.path.isdir(game) or not find(game, '1.EXE'):
        print('BŁĄD: w katalogu %s nie ma pliku 1.EXE' % game)
        return 2
    print(patch['title'])

    if args.restore:
        bdir = os.path.join(game, BACKUP_DIR)
        if not os.path.isdir(bdir):
            print('BŁĄD: brak katalogu kopii %s' % bdir)
            return 2
        for name, e in sorted(patch['files'].items()):
            src = os.path.join(bdir, name)
            if os.path.exists(src):
                data = open(src, 'rb').read()
                if sha(data) != e['source_sha256']:
                    print('  %-12s kopia uszkodzona - pomijam' % name)
                    continue
                dst = find(game, name) or os.path.join(game, name)
                open(dst, 'wb').write(data)
                print('  %-12s przywrócony' % name)
        print('Przywrócono wersję angielską.')
        return 0

    plan = []
    problems = []
    for name, e in sorted(patch['files'].items()):
        path = find(game, name)
        if path is None:
            problems.append('%s: brak pliku' % name)
            continue
        data = open(path, 'rb').read()
        h = sha(data)
        if h == e['target_sha256']:
            plan.append((name, path, None, 'już spolszczony'))
        elif h == e['source_sha256']:
            plan.append((name, path, data, 'do zmiany'))
        else:
            problems.append('%s: nieznana wersja pliku (SHA-256 %s...)' % (name, h[:16]))
    for name, path, _, state in plan:
        print('  %-12s %s' % (name, state))
    if problems:
        print('Patch NIE może zostać zastosowany - pliki nie pochodzą z obsługiwanego wydania:')
        for p in problems:
            print('  ' + p)
        print('Obsługiwane wydanie: ' + patch['supported_release'])
        return 1
    if args.check:
        print('Pliki zgodne z obsługiwaną wersją.')
        return 0

    results = {}
    for name, path, data, state in plan:
        if data is None:
            continue
        e = patch['files'][name]
        new = METHODS[e['method']](data, e)
        if sha(new) != e['target_sha256']:
            print('BŁĄD: wynik dla %s nie zgadza się z oczekiwanym (SHA-256) - nic nie zmieniono.' % name)
            return 1
        results[name] = (path, data, new)
    bdir = os.path.join(game, BACKUP_DIR)
    os.makedirs(bdir, exist_ok=True)
    for name, (path, old, new) in sorted(results.items()):
        bpath = os.path.join(bdir, name)
        if not os.path.exists(bpath):
            shutil.copy2(path, bpath)
        with open(path, 'wb') as f:
            f.write(new)
        print('  %-12s zainstalowany' % name)
    print('Gotowe. Kopie oryginałów: %s' % bdir)
    print('Uruchom grę poleceniem RUNME (wybierz [2] - VGA) lub 1.EXE.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Tworzy dystrybucyjny patch polonizacji (bez plików gry).

Użycie:
    python tools/make_patch.py --source original --build build/game --output patches/dist [--version 1.0]

Paczka (katalog + archiwum ZIP) zawiera:
    apply_patch.py   instalator (Python 3, bez dodatkowych pakietów)
    bbformats.py     kodek formatów gry (wymagany przez instalator)
    patch.json       zmiany: bajty tekstów oraz zmienione piksele grafik
    CZYTAJ.TXT       instrukcja instalacji
    LICENCJA.TXT     licencje

Format zmian:
  * 'bytes' - podmiana bajtów (1.EXE, RUNME.COM): tylko nowe, polskie bajty,
  * 'ilbm'  - zmienione piksele ekranu/arkusza kafli: prostokąt + maska bitowa
              + wartości wyłącznie zmienionych pikseli,
  * 'sqv'   - zmienione klatki sprite'ów (piksele zmienione lub nowa klatka).
Instalator dekompresuje oryginał, nakłada zmiany, ponownie koduje tym samym
deterministycznym koderem i sprawdza SHA-256 wyniku.

Po utworzeniu paczka jest testowana: instalacja na świeżej kopii oryginału
musi dać pliki identyczne z buildem, a ponowna instalacja i przywracanie
kopii muszą działać.
"""
import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import bbformats as bf  # noqa: E402
import gamedata as gd  # noqa: E402

ROOT = os.path.dirname(TOOLS)


def sha(d):
    return hashlib.sha256(d).hexdigest()


def pixel_regions(old, new, width):
    """Zmienione piksele jako jeden prostokąt z maską bitową i listą wartości."""
    import numpy as np
    a = np.frombuffer(bytes(old), np.uint8).reshape(-1, width)
    b = np.frombuffer(bytes(new), np.uint8).reshape(-1, width)
    d = a != b
    if not d.any():
        return []
    ys, xs = np.nonzero(d)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    m = d[y0:y1, x0:x1].reshape(-1)
    vals = b[y0:y1, x0:x1].reshape(-1)[m]
    return [{'rect': [int(x0), int(y0), int(x1 - x0), int(y1 - y0)],
             'mask': base64.b64encode(np.packbits(m).tobytes()).decode(),
             'values': base64.b64encode(vals.tobytes()).decode()}]


def diff_file(name, old, new):
    e = {'source_sha256': sha(old), 'target_sha256': sha(new), 'source_size': len(old), 'target_size': len(new)}
    if name.endswith(('.EXE', '.COM')):
        if len(old) != len(new):
            raise SystemExit('%s: zmiana długości nieobsługiwana' % name)
        ops = []
        i = 0
        while i < len(old):
            if old[i] != new[i]:
                j = i
                while j < len(old) and (old[j] != new[j] or (j + 1 < len(old) and old[j + 1] != new[j + 1])):
                    j += 1
                ops.append([i, new[i:j].hex()])
                i = j
            else:
                i += 1
        e.update(method='bytes', bytes=ops)
        return e
    od, nd = bf.unpack(old), bf.unpack(new)
    if od[:4] == b'FORM':
        oi, ni = bf.ILBM.parse(od), bf.ILBM.parse(nd)
        e.update(method='ilbm', regions=pixel_regions(oi.pixels, ni.pixels, oi.width))
        return e
    of, _ = bf.parse_sqv(od)
    nf, _ = bf.parse_sqv(nd)
    frames = []
    for i, (a, b) in enumerate(zip(of, nf)):
        if (a['w'], a['h'], a['data']) == (b['w'], b['h'], b['data']):
            continue
        pb = bf.decode_planar(b['data'], b['w'], b['h'])
        if (a['w'], a['h']) == (b['w'], b['h']):
            pa = bf.decode_planar(a['data'], a['w'], a['h'])
            frames.append({'index': i, 'w': b['w'], 'h': b['h'], 'regions': pixel_regions(pa, pb, b['w'])})
        else:
            frames.append({'index': i, 'w': b['w'], 'h': b['h'], 'regions': None,
                           'pixels': base64.b64encode(bytes(pb)).decode()})
    e.update(method='sqv', frames=frames)
    return e


README = """Polska wersja językowa: The Blues Brothers (Titus Interactive, 1991), MS-DOS
==========================================================================
Wersja patcha: {version}

Patch NIE zawiera plików gry. Potrzebna jest legalnie posiadana kopia
obsługiwanego wydania:
  {release}

INSTALACJA
1. Zainstaluj Python 3 (https://www.python.org/) - inne narzędzia nie są potrzebne.
2. Rozpakuj ten katalog w dowolnym miejscu.
3. Uruchom w wierszu poleceń:
       python apply_patch.py C:\\GRY\\BLUES
   (podaj katalog z plikiem 1.EXE). Sprawdzenie bez zmian: --check
4. Uruchom grę (np. w DOSBox): RUNME, a w menu wybierz [2] - VGA.
   W DOSBox ustaw cycles=12000 lub więcej (przy domyślnych 3000 gra jest
   zbyt wolna, także w oryginale).

PŁYNNE PRZEWIJANIE
Polska wersja przewija planszę płynnie (co piksel), zamiast skokami po
16 pikseli jak oryginał. Przeciwnicy budzą się względem kamery, więc
moment ich pojawiania się może się nieco różnić, a dema w trybie demo
po pewnym czasie rozjeżdżają się z oryginałem.

Instalator sprawdza sumy SHA-256 każdego pliku i odmawia pracy z innym
wydaniem. Oryginalne pliki są kopiowane do podkatalogu KOPIA_EN\\.
Przywrócenie wersji angielskiej:
       python apply_patch.py C:\\GRY\\BLUES --restore

ZMIENIANE PLIKI
{files}

Opcja [1] - EGA w menu RUNME tego wydania nie uruchamia gry (tak samo jak
w oryginale). Opcja [3] uruchamia intro grupy crackerskiej (nietłumaczone).
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', default='original')
    ap.add_argument('--build', default=os.path.join('build', 'game'))
    ap.add_argument('--output', default=os.path.join('patches', 'dist'))
    ap.add_argument('--version', default='1.0')
    args = ap.parse_args()
    name = 'blues-brothers-pl-%s' % args.version
    out = os.path.join(args.output, name)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    patch = {'title': 'The Blues Brothers (DOS) - polonizacja %s' % args.version,
             'version': args.version,
             'supported_release': 'The Blues Brothers, MS-DOS, angielska wersja na dysk twardy '
                                  '(1.EXE 196608 B, SHA-256 769ee254...0add)',
             'files': {}}
    for fname in sorted(gd.KNOWN_FILES):
        old = open(gd.find_file(args.source, fname), 'rb').read()
        if sha(old) != gd.KNOWN_FILES[fname][1]:
            raise SystemExit('BŁĄD: %s w %s nie jest oryginałem' % (fname, args.source))
        new = open(os.path.join(args.build, fname), 'rb').read()
        if new != old:
            patch['files'][fname] = diff_file(fname, old, new)
    with open(os.path.join(out, 'patch.json'), 'w', encoding='utf-8') as f:
        json.dump(patch, f, indent=1, ensure_ascii=False, sort_keys=True)
    shutil.copy2(os.path.join(TOOLS, 'patcher', 'apply_patch.py'), out)
    shutil.copy2(os.path.join(TOOLS, 'bbformats.py'), out)
    files = '\n'.join('  %-12s %s' % (n, e['method']) for n, e in sorted(patch['files'].items()))
    with open(os.path.join(out, 'CZYTAJ.TXT'), 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(README.format(version=args.version, release=patch['supported_release'], files=files))
    shutil.copy2(os.path.join(ROOT, 'LICENSE'), os.path.join(out, 'LICENCJA.TXT'))

    # --- test paczki na czystej kopii oryginału -----------------------------
    tmp = tempfile.mkdtemp(prefix='bbpl_')
    try:
        game = os.path.join(tmp, 'GRA')
        shutil.copytree(args.source, game)
        def run(*extra):
            return subprocess.run([sys.executable, os.path.join(out, 'apply_patch.py'), game] + list(extra),
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        r = run('--check')
        assert r.returncode == 0, r.stdout
        r = run()
        assert r.returncode == 0, r.stdout
        for fname in gd.KNOWN_FILES:
            a = open(os.path.join(game, fname), 'rb').read()
            b = open(os.path.join(args.build, fname), 'rb').read()
            assert a == b, 'instalacja: %s różni się od buildu' % fname
        r = run()
        assert r.returncode == 0 and 'już spolszczony' in r.stdout, r.stdout
        r = run('--restore')
        assert r.returncode == 0, r.stdout
        for fname in gd.KNOWN_FILES:
            a = open(os.path.join(game, fname), 'rb').read()
            assert sha(a) == gd.KNOWN_FILES[fname][1], 'przywracanie: %s' % fname
        # odmowa dla zmodyfikowanego pliku
        p = os.path.join(game, 'CHOIX.SQZ')
        d = bytearray(open(p, 'rb').read())
        d[100] ^= 0xFF
        open(p, 'wb').write(d)
        r = run()
        assert r.returncode == 1 and 'NIE może' in r.stdout, r.stdout
        print('Test paczki: instalacja = build, ponowna instalacja, przywrócenie, odmowa dla obcego pliku - OK')
    finally:
        shutil.rmtree(tmp)

    zpath = os.path.join(args.output, name + '.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(out)):
            zi = zipfile.ZipInfo(name + '/' + fn, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, open(os.path.join(out, fn), 'rb').read())
    size = os.path.getsize(zpath)
    print('Patch: %s (%d B), plików zmienianych: %d' % (zpath, size, len(patch['files'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())

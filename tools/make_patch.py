#!/usr/bin/env python3
"""Buduje cztery warianty i gotową paczkę patcha, bez oryginalnej gry.

    python tools/make_patch.py --source original --output patches/dist --version 1.1.0

Wymagania twórcy: Pillow, numpy, nasm. Instalator gracza: tylko Python 3.8+.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import bbformats as bf  # noqa: E402
import gamedata as gd  # noqa: E402

ROOT = TOOLS.parent
PROFILES = {
    'en-original': ('en', 'original', 'ENORIG'),
    'en-smooth': ('en', 'smooth', 'ENSMOOTH'),
    'pl-original': ('pl', 'original', 'PLORIG'),
    'pl-smooth': ('pl', 'smooth', 'PLSMOOTH'),
}
PACKAGE_FILES = {'apply_patch.py', 'bbformats.py', 'patch.json', 'START.COM',
                 'README.txt', 'CZYTAJ.txt', 'LICENSE.txt'}


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
            raise ValueError('%s: zmiana długości nieobsługiwana' % name)
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
        if (oi.width, oi.height, oi.palette) != (ni.width, ni.height, ni.palette):
            raise ValueError('%s: zmiana wymiarów/palety nieobsługiwana' % name)
        e.update(method='ilbm', regions=pixel_regions(oi.pixels, ni.pixels, oi.width))
        return e
    of, _ = bf.parse_sqv(od)
    nf, _ = bf.parse_sqv(nd)
    if len(of) != len(nf):
        raise ValueError('%s: zmiana liczby klatek nieobsługiwana' % name)
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


def read_original(source):
    result = {}
    for name, (size, checksum) in sorted(gd.KNOWN_FILES.items()):
        path = gd.find_file(str(source), name)
        if path is None:
            raise ValueError('Brak pliku źródłowego: %s' % name)
        data = Path(path).read_bytes()
        if len(data) != size or sha(data) != checksum:
            raise ValueError('%s nie jest obsługiwanym oryginałem' % name)
        result[name] = data
    return result


def metadata(data):
    return {'size': len(data), 'sha256': sha(data)}


def build_profile(source, directory, locale, scroll):
    subprocess.run([sys.executable, str(TOOLS / 'build.py'), '--source', str(source),
                    '--locale', locale, '--scroll', scroll, '--output', str(directory)],
                   cwd=str(ROOT), check=True)
    return {name: (directory / 'game' / name).read_bytes() for name in gd.KNOWN_FILES}


def create_package(source, work, version):
    original = read_original(source)
    package = work / ('blues-brothers-%s-patch' % version)
    package.mkdir()
    launcher = package / 'START.COM'
    subprocess.run(['nasm', '-f', 'bin', '-o', str(launcher),
                    str(ROOT / 'mods' / 'launcher' / 'start.asm')], check=True)
    patch = {
        'format_version': 2,
        'title': 'The Blues Brothers DOS — Smooth Scroll with optional Polish translation',
        'version': version,
        'supported_release': 'English MS-DOS hard-disk TDT/TRSI release; '
                             '1.EXE 196608 B, SHA-256 ' + gd.KNOWN_FILES['1.EXE'][1],
        'source': {name: metadata(data) for name, data in original.items()},
        'launcher': dict(file='START.COM', **metadata(launcher.read_bytes())),
        'profiles': {},
    }
    builds = {}
    for key, (locale, scroll, directory) in PROFILES.items():
        files = build_profile(source, work / key, locale, scroll)
        builds[key] = files
        patch['profiles'][key] = {
            'locale': locale, 'scroll': scroll, 'directory': directory,
            'output': {name: metadata(data) for name, data in files.items()},
            'files': {name: diff_file(name, original[name], data)
                      for name, data in sorted(files.items()) if data != original[name]},
        }
    (package / 'patch.json').write_text(json.dumps(patch, indent=1, ensure_ascii=False,
                                                 sort_keys=True) + '\n', encoding='utf-8')
    shutil.copyfile(TOOLS / 'patcher' / 'apply_patch.py', package / 'apply_patch.py')
    shutil.copyfile(TOOLS / 'bbformats.py', package / 'bbformats.py')
    for source_doc, target_doc in [('install.md', 'README.txt'), ('install.pl.md', 'CZYTAJ.txt')]:
        text = (ROOT / 'docs' / source_doc).read_text(encoding='utf-8')
        for before, after in [('(install.pl.md)', '(CZYTAJ.txt)'),
                              ('(install.md)', '(README.txt)'),
                              ('(../README.md)', '(https://github.com/grzebla/blues-brothers-dos-smooth-scroll#readme)'),
                              ('(../README.pl.md)', '(https://github.com/grzebla/blues-brothers-dos-smooth-scroll/blob/main/README.pl.md)'),
                              ('(compatibility.md)', '(https://github.com/grzebla/blues-brothers-dos-smooth-scroll/blob/main/docs/compatibility.md)'),
                              ('(compatibility.pl.md)', '(https://github.com/grzebla/blues-brothers-dos-smooth-scroll/blob/main/docs/compatibility.pl.md)')]:
            text = text.replace(before, after)
        (package / target_doc).write_text(text.replace('1.1.0', version), encoding='utf-8')
    shutil.copyfile(ROOT / 'LICENSE', package / 'LICENSE.txt')
    test_package(package, work, original, builds)
    return package


def test_package(package, work, original, builds):
    source = work / 'test-source'
    source.mkdir()
    for name, data in original.items():
        (source / name).write_bytes(data)
    destination = work / 'test-install'

    def run(*args):
        proc = subprocess.run([sys.executable, '-I', str(package / 'apply_patch.py'), str(source), *args],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        return proc

    result = run('--check')
    if result.returncode or destination.exists():
        raise ValueError('Autotest --check: ' + result.stdout)
    result = run('--output', str(destination))
    if result.returncode:
        raise ValueError('Autotest instalacji: ' + result.stdout)
    for key, (_, _, directory) in PROFILES.items():
        for name, data in builds[key].items():
            if (destination / directory / name).read_bytes() != data:
                raise ValueError('Instalacja różni się od buildu: %s/%s' % (key, name))
    if run('--output', str(destination)).returncode == 0:
        raise ValueError('Instalator nadpisał istniejący wynik')
    for name, data in original.items():
        if (source / name).read_bytes() != data:
            raise ValueError('Instalator zmienił źródło: ' + name)
    # Ten zasób nie jest zmieniany przez żaden profil: kontrolujemy pełną bazę.
    path = source / 'PRES.SQZ'
    damaged = bytearray(path.read_bytes())
    damaged[100] ^= 255
    path.write_bytes(damaged)
    if run('--check').returncode == 0:
        raise ValueError('Instalator zaakceptował obce źródło')
    if {p.name for p in package.iterdir()} != PACKAGE_FILES:
        raise ValueError('Nieoczekiwane pliki w dystrybucji')
    print('Autotest paczki: cztery profile = buildy, źródło nietknięte, odmowa nadpisania/obcej bazy — OK')


def write_archive(package, path):
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(PACKAGE_FILES):
            info = zipfile.ZipInfo(package.name + '/' + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (package / name).read_bytes())
    with zipfile.ZipFile(path) as archive:
        expected = {package.name + '/' + name for name in PACKAGE_FILES}
        if set(archive.namelist()) != expected or archive.testzip() is not None:
            raise ValueError('Błąd weryfikacji ZIP')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', type=Path, default=ROOT / 'original')
    ap.add_argument('--output', type=Path, default=ROOT / 'patches' / 'dist')
    ap.add_argument('--version', default='1.1.0')
    args = ap.parse_args()
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', args.version):
        ap.error('--version musi mieć postać X.Y.Z')
    args.source = args.source.resolve()
    args.output = args.output.resolve()
    if args.output == args.source or args.source in args.output.parents:
        ap.error('katalog paczki nie może należeć do oryginalnej gry')
    args.output.mkdir(parents=True, exist_ok=True)
    name = 'blues-brothers-%s-patch' % args.version
    target = args.output / name
    archive = args.output / (name + '.zip')
    if target.exists() or archive.exists():
        ap.error('wydanie już istnieje; podaj nowy --output lub numer wersji (nic nie nadpisano)')
    with tempfile.TemporaryDirectory(prefix='.bb-release-', dir=str(args.output)) as tmp:
        work = Path(tmp)
        package = create_package(args.source, work, args.version)
        staged_zip = work / (name + '.zip')
        write_archive(package, staged_zip)
        checksum = sha(staged_zip.read_bytes())
        # Przenosimy wyłącznie zweryfikowane pliki dystrybucyjne, nie lokalne buildy.
        package.rename(target)
        staged_zip.rename(archive)
        (args.output / 'SHA256SUMS').write_text('%s  %s\n' % (checksum, archive.name), encoding='ascii')
    print('Patch: %s (%d B)' % (archive, archive.stat().st_size))
    print('SHA-256: %s' % checksum)
    return 0


if __name__ == '__main__':
    sys.exit(main())

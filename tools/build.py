#!/usr/bin/env python3
"""Buduje wybrany profil The Blues Brothers (DOS): język i przewijanie.

Użycie:
    python tools/build.py --source original --locale en|pl --scroll original|smooth --output build
    python tools/build.py --locale pl --render

Kroki:
  1. weryfikacja kompletności i wersji gry (SHA-256 wszystkich plików),
  2. kopia oryginalnych plików do <output>/game (katalog original/ nie jest zmieniany),
  3. import polskich tekstów do 1.EXE i RUNME.COM (tools/patch_exe.py)
     i płynne przewijanie w 1.EXE (mods/smooth_scroll, wymaga nasm),
  4. (z --render) wygenerowanie grafik z tłumaczeń (tools/make_graphics.py),
  5. zakodowanie zmodyfikowanych grafik (tools/import.py),
  6. zapis gotowego profilu gry,
  7. weryfikacja wygenerowanych plików (dekompresja, piksele, limity silnika),
  8. raport zmian (<output>/report.txt, <output>/manifest.json).

Proces jest deterministyczny: te same wejścia dają identyczne bajty wyjściowe.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import bbformats as bf  # noqa: E402
import gamedata as gd  # noqa: E402
import patch_exe  # noqa: E402


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


importer = load_module('bb_import', 'import.py')
ROOT = os.path.dirname(TOOLS)


def load_smooth_scroll():
    spec = importlib.util.spec_from_file_location(
        'bb_smooth_scroll', os.path.join(ROOT, 'mods', 'smooth_scroll', 'apply.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_source(src, force):
    ident = gd.identify(src)
    problems = []
    if ident['missing']:
        problems.append('brakujące pliki: ' + ', '.join(ident['missing']))
    if ident['mismatch']:
        problems.append('pliki o innej zawartości: ' + ', '.join(ident['mismatch']))
    if problems and not force:
        raise SystemExit('BŁĄD: katalog %s nie zawiera obsługiwanej wersji gry:\n  %s' % (src, '\n  '.join(problems)))
    return ident


def verify_output(src, game_dir, changed, locale):
    """Niezależna weryfikacja wyniku. Zwraca listę opisów sprawdzeń."""
    checks = []
    for name in sorted(gd.KNOWN_FILES):
        out = open(os.path.join(game_dir, name), 'rb').read()
        orig = open(gd.find_file(src, name), 'rb').read()
        if name not in changed:
            assert out == orig, name
            continue
        if name.endswith(('.SQZ', '.SQV', '.CK1', '.CK2')):
            data = bf.unpack(out)
            assert bf.dos_overrun(out) <= gd.MAX_DOS_OVERRUN, name
            if data[:4] == b'FORM':
                im = bf.ILBM.parse(data)
                assert len(data) <= gd.SCREEN_ILBM_MAX, name
                png = importer.read_png(os.path.join('localization', locale, 'graphics', name + '.png'))
                assert bytes(im.pixels) == png.tobytes(), name
                checks.append('%s: ILBM %dx%d, %d B (limit %d), piksele zgodne z PNG' % (
                    name, im.width, im.height, len(data), gd.SCREEN_ILBM_MAX))
            else:
                frames, _ = bf.parse_sqv(data)
                assert len(data) <= gd.SPRITE_SQV_MAX, name
                assert len(frames) == len(bf.parse_sqv(bf.unpack(orig))[0]), name
                checks.append('%s: %d klatek, %d B (limit %d)' % (name, len(frames), len(data), gd.SPRITE_SQV_MAX))
        else:
            diff = sum(1 for a, b in zip(out, orig) if a != b)
            assert len(out) == len(orig), name
            checks.append('%s: rozmiar bez zmian (%d B), zmienionych bajtów: %d' % (name, len(out), diff))
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', default='original')
    ap.add_argument('--locale', choices=('en', 'pl'), default='pl')
    ap.add_argument('--output', default='build')
    ap.add_argument('--render', action='store_true', help='wygeneruj grafiki z tłumaczeń przed importem')
    ap.add_argument('--force', action='store_true', help='nie przerywaj przy niezgodnej wersji (niezalecane)')
    scroll = ap.add_mutually_exclusive_group()
    scroll.add_argument('--scroll', choices=('original', 'smooth'), default='smooth',
                        help='rodzaj przewijania (domyślnie smooth)')
    scroll.add_argument('--classic-scroll', action='store_true',
                        help='alias --scroll original (zgodność ze starszymi testami)')
    args = ap.parse_args()
    if args.classic_scroll:
        args.scroll = 'original'
    if args.render and args.locale == 'en':
        ap.error('--render dotyczy tylko lokalizacji pl')
    src = os.path.normpath(args.source)
    out = os.path.normpath(args.output)
    source_path, output_path = os.path.realpath(src), os.path.realpath(out)
    try:
        overlap = os.path.commonpath([source_path, output_path]) in (source_path, output_path)
    except ValueError:  # różne dyski w Windows
        overlap = False
    if overlap:
        raise SystemExit('BŁĄD: katalog źródłowy i wyjściowy nie mogą się nakładać')
    report = []
    print('[1/8] Weryfikacja wersji gry w %s' % src)
    ident = verify_source(src, args.force)
    report.append('Źródło: %s - %d plików, wersja: %s' % (
        src, len(ident['files']), 'zgodna' if not ident['mismatch'] else 'NIEZGODNA'))

    print('[2/8] Kopiowanie plików oryginalnych')
    game = os.path.join(out, 'game')
    if os.path.isdir(game):
        shutil.rmtree(game)
    os.makedirs(game)
    for name in sorted(gd.KNOWN_FILES):
        with open(gd.find_file(src, name), 'rb') as f:
            data = f.read()
        with open(os.path.join(game, name), 'wb') as f:
            f.write(data)

    print('[3/8] Teksty (%s) i przewijanie (%s)' % (args.locale, args.scroll))
    spec = patch_exe.build_spec(args.locale) if args.locale == 'pl' else []
    exe_files = patch_exe.apply_spec(src, spec) if spec else {}
    if args.scroll == 'smooth':
        exe = bytearray(exe_files.get('1.EXE') or open(gd.find_file(src, '1.EXE'), 'rb').read())
        try:
            report.append(load_smooth_scroll().apply_smooth_scroll(exe))
        except FileNotFoundError:
            raise SystemExit('BŁĄD: brak asemblera nasm (potrzebny do płynnego przewijania), np. brew install nasm')
        exe_files['1.EXE'] = bytes(exe)
    else:
        report.append('płynne przewijanie: wyłączone (--scroll original)')

    if args.render:
        print('[4/8] Generowanie grafik z tłumaczeń')
        mg = load_module('bb_make_graphics', 'make_graphics.py')
        sys.argv = ['make_graphics.py', '--source', src, '--locale', args.locale]
        mg.main()
    elif args.locale == 'pl':
        print('[4/8] Generowanie grafik pominięte (użyj --render), używam PNG z localization/pl/graphics')
    else:
        print('[4/8] Grafiki angielskie pozostają oryginalne')

    print('[5/8] Kodowanie grafik')
    log = []
    gfx_files = importer.import_all(src, args.locale, log) if args.locale == 'pl' else {}
    report.extend(['Grafiki:'] + log)

    print('[6/8] Zapis profilu %s-%s do %s' % (args.locale, args.scroll, game))
    changed = {}
    changed.update(exe_files)
    changed.update(gfx_files)
    for name, data in sorted(changed.items()):
        with open(os.path.join(game, name), 'wb') as f:
            f.write(data)

    print('[7/8] Weryfikacja')
    checks = verify_output(src, game, changed, args.locale)
    report.append('Weryfikacja:')
    report.extend('  ' + c for c in checks)

    print('[8/8] Raport')
    manifest = {'locale': args.locale, 'scroll': args.scroll,
                'source': {}, 'output': {}, 'changed': sorted(changed)}
    for name in sorted(gd.KNOWN_FILES):
        o = open(gd.find_file(src, name), 'rb').read()
        n = open(os.path.join(game, name), 'rb').read()
        manifest['source'][name] = {'size': len(o), 'sha256': sha(o)}
        manifest['output'][name] = {'size': len(n), 'sha256': sha(n)}
    with open(os.path.join(out, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    report.append('Zmienione pliki:')
    for name in sorted(changed):
        report.append('  %-12s %6d B -> %6d B  sha256 %s' % (
            name, manifest['source'][name]['size'], manifest['output'][name]['size'], manifest['output'][name]['sha256']))
    report.append('Zmiany tekstów w plikach wykonywalnych:')
    for item in spec:
        report.append('  %-10s 0x%05X %3d B  %s' % (item['file'], item['offset'], len(item['replace']) // 2, item['note']))
    text = '\n'.join(report) + '\n'
    with open(os.path.join(out, 'report.txt'), 'w', encoding='utf-8') as f:
        f.write(text)
    print(text)
    print('Gotowe: %s (uruchom 1.EXE lub RUNME.COM w DOSBox)' % game)
    return 0


if __name__ == '__main__':
    sys.exit(main())

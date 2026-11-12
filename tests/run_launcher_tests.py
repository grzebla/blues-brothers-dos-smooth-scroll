#!/usr/bin/env python3
"""Integracyjne testy START.COM w prawdziwym DOSBox-X.

    python3 tests/run_launcher_tests.py --game build/bundle --out tests/results/release-1.1.0

Testy wyborów/błędów korzystają z autorskiego mini-EXE, a cztery testy boot
uruchamiają rzeczywistą grę. Żadne łatki testowe nie trafiają do wydania.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import bbformats as bf  # noqa: E402
import dosbox_harness as H  # noqa: E402

PROFILES = [('en-original', 'ENORIG', '1', '1'), ('en-smooth', 'ENSMOOTH', '1', '2'),
            ('pl-original', 'PLORIG', '2', '1'), ('pl-smooth', 'PLSMOOTH', '2', '2')]

STUB = """bits 16
org 0
    dw 05a4dh
    dw (file_end-$$) % 512, ((file_end-$$)+511) / 512
    dw 0, 2, 0, 0ffffh, 0, 0200h, 0, 0, 0, 01ch, 0
    times 32-($-$$) db 0
    push cs
    pop ds
    mov dx, marker-32
    xor cx, cx
    mov ah, 03ch
    int 021h
    jc failed
    mov bx, ax
    mov ah, 03eh
    int 021h
    mov ax, 04c00h
    int 021h
failed:
    mov ax, 04c01h
    int 021h
marker: db 'SEEN.TXT',0
file_end:
"""


def run_fixtures(game, work):
    checks = []
    with tempfile.TemporaryDirectory(prefix='launcher-fixtures-', dir=work) as tmp:
        fixture = Path(tmp)
        asm = fixture / 'stub.asm'
        exe = fixture / 'stub.exe'
        asm.write_text(STUB, encoding='ascii')
        subprocess.run(['nasm', '-f', 'bin', '-o', str(exe), str(asm)], check=True)
        app = fixture / 'APP'
        app.mkdir()
        shutil.copyfile(game / 'START.COM', app / 'START.COM')
        (fixture / 'OTHER').mkdir()
        for _, directory, _, _ in PROFILES:
            (app / directory).mkdir()
            shutil.copyfile(exe, app / directory / '1.EXE')
        cases = [(key, language + ' ' + scroll, directory)
                 for key, directory, language, scroll in PROFILES]
        cases += [('back-invalid', 'x 2 esc 1 2', 'ENSMOOTH'), ('exit', 'x esc', None)]
        for key, keys, expected in cases:
            rec = H.run(str(fixture), str(work / ('fixture-' + key)), keys=keys,
                        program='C:\\APP\\START.COM\ncd > C:\\CWD.TXT',
                        pre='cd OTHER', wait=3, pace=0.75, seconds=16, log_con=True)
            copied = Path(rec.dir) / 'game'
            seen = sorted(p.parent.name for p in (copied / 'APP').glob('*/SEEN.TXT'))
            cwd = (copied / 'CWD.TXT').read_text(errors='replace') if (copied / 'CWD.TXT').exists() else ''
            ok = seen == ([expected] if expected else []) and 'C:\\OTHER' in cwd.upper()
            checks.append({'scenario': 'fixture-' + key, 'ok': ok,
                           'detail': 'wybrano=%s, powrót CWD=%r' % (seen, cwd.strip())})
            print(checks[-1], flush=True)
        # Wywołujący na innym napędzie, launcher i zasoby na C:.
        rec = H.run(str(fixture), str(work / 'fixture-drive'), keys='2 1',
                    program='C:\\APP\\START.COM\ncd > C:\\CWD.TXT',
                    pre='mount d "%s"\nd:\ncd OTHER' % fixture,
                    wait=3, pace=0.75, seconds=16, log_con=True)
        copied = Path(rec.dir) / 'game'
        cwd = (copied / 'CWD.TXT').read_text(errors='replace') if (copied / 'CWD.TXT').exists() else ''
        ok = (copied / 'APP' / 'PLORIG' / 'SEEN.TXT').exists() and 'D:\\OTHER' in cwd.upper()
        checks.append({'scenario': 'fixture-other-drive', 'ok': ok, 'detail': cwd.strip()})
        print(checks[-1], flush=True)
        # Błąd EXEC nie może udawać udanego uruchomienia.
        (app / 'ENORIG' / '1.EXE').unlink()
        rec = H.run(str(fixture), str(work / 'fixture-missing'), keys='1 1 esc',
                    program='C:\\APP\\START.COM\nif errorlevel 1 echo FAILED>C:\\FAILED.TXT',
                    wait=3, pace=0.75, seconds=16, log_con=True)
        copied = Path(rec.dir) / 'game'
        checks.append({'scenario': 'fixture-missing-exe', 'ok': (copied / 'FAILED.TXT').exists(),
                       'detail': 'launcher sygnalizuje błąd kodem wyjścia'})
        print(checks[-1], flush=True)
        # Sprzęt EGA nie jest akceptowany przez nowy launcher VGA.
        rec = H.run(str(fixture), str(work / 'fixture-ega'), keys='2 1 esc', machine='ega',
                    program='C:\\APP\\START.COM\nif errorlevel 1 echo FAILED>C:\\FAILED.TXT',
                    wait=3, pace=0.75, seconds=16, log_con=True)
        copied = Path(rec.dir) / 'game'
        ok = (copied / 'FAILED.TXT').exists() and not list((copied / 'APP').glob('*/SEEN.TXT'))
        checks.append({'scenario': 'fixture-reject-ega', 'ok': ok, 'detail': 'VGA wymagane, kod błędu i brak uruchomionego dziecka'})
        print(checks[-1], flush=True)
    return checks


def run_boots(game, work, output):
    checks = []
    for key, directory, language, scroll in PROFILES:
        rec = H.run(str(game), str(work / key), keys=language + ' , , ' + scroll,
                    program='START.COM', wait=3, pace=1, seconds=42)
        image = bf.ILBM.parse(bf.unpack((game / directory / 'CHOIX.SQZ').read_bytes()))
        pixels = np.frombuffer(image.pixels, dtype=np.uint8).reshape(image.height, image.width)
        bar = pixels[190:200]
        mask = ~np.isin(bar, (2, 3, 9, 10, 14))
        expected = H.expected_rgb(bar, image.palette)
        when, _, score, frame = H.find_match(rec, expected, 0, 190, step=0.5, mask=mask)
        if frame is not None:
            Image.fromarray(frame).save(output / (key + '.png'))
        # Materiał do oceny menu przez visual-reviewer, nie OCR logu DOS.
        for t, _, menu in rec.frames(step=0.5):
            if key == 'en-original' and 0.5 <= t <= 1.0:
                Image.fromarray(menu).save(output / 'menu-language.png')
            if key in ('en-original', 'pl-original') and 4.0 <= t <= 4.5:
                Image.fromarray(menu).save(output / ('menu-' + language + '.png'))
            if t > 5:
                break
        audio = rec.audio_stats()
        sound = any(rms > 100 for _, rms, _, _ in audio)
        checks.append({'scenario': 'boot-' + key, 'ok': bool(score >= 0.99 and sound),
                       'detail': 'pasek języka=%.3f w t=%s s; audio=%s' % (score, when, sound)})
        print(checks[-1], flush=True)
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=ROOT / 'tests/results/release-1.1.0')
    ap.add_argument('--work', type=Path, default=ROOT / 'work/launcher-dbx')
    ap.add_argument('--fixture-only', action='store_true')
    ap.add_argument('--dosbox', type=Path, help='ścieżka do DOSBox-X (na macOS zalecane SDL2)')
    args = ap.parse_args()
    if args.dosbox:
        H.DOSBOX_CANDIDATES = [str(args.dosbox.resolve())]
    args.game = args.game.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    args.work.mkdir(parents=True, exist_ok=True)
    start = time.time()
    results = run_fixtures(args.game, args.work)
    if not args.fixture_only:
        results += run_boots(args.game, args.work, args.out)
    (args.out / 'launcher-results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False) + '\n',
                                                  encoding='utf-8')
    lines = ['# Testy menu DOS — wydanie 1.1.0', '',
             'Testy fixture używają autorskiego EXE; boot uruchamia prawdziwą grę.', '']
    for result in results:
        lines += ['- [%s] **%s**: %s' % ('x' if result['ok'] else ' ', result['scenario'],
                                       result['detail'].replace('\n', ' / '))]
    lines += ['', 'Czas: %.0f s.' % (time.time() - start)]
    (args.out / 'launcher-report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return 0 if all(result['ok'] for result in results) else 1


if __name__ == '__main__':
    sys.exit(main())

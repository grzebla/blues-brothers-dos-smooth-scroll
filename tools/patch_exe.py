#!/usr/bin/env python3
"""Patchowanie tekstów w plikach wykonywalnych (1.EXE, RUNME.COM).

Użycie:
    python tools/patch_exe.py --source original --locale pl --output work/exe [--spec patches/text_patches.json]

Zasady (wg kolejności preferencji z założeń projektu):
  1. podmiana ciągów o zgodnym rozmiarze (RUNME.COM - linie menu, dopełniane spacjami),
  2. przeniesienie tekstu w obrębie dostępnego obszaru danych z poprawą
     odwołań (1.EXE - dwa komunikaty błędów dzielą 36-bajtowy blok
     DS:3388-33AB, wskaźniki w tablicy DS:3384/DS:3386 są aktualizowane),
  kod x86 nie jest modyfikowany.

Każda zmiana sprawdza najpierw sumę SHA-256 pliku oraz oczekiwane bajty
w miejscu zmiany (sygnatury) - ślepe podmiany są niemożliwe.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gamedata as gd  # noqa: E402

# Blok komunikatów błędów 1.EXE (wypisywanych przez DOS AH=09h, zakończonych '$')
ERRMSG_TABLE = gd.ds_to_file(0x3384)          # 2 wskaźniki near (DS)
ERRMSG_BLOCK = gd.ds_to_file(0x3388)          # początek bloku
ERRMSG_BLOCK_DS = 0x3388
ERRMSG_BLOCK_SIZE = 0x33AC - 0x3388           # 36 bajtów; od DS:33AC zmienne dekompresora
ERRMSG_ORIG = b'\n\rVIDEO ERROR.\n\r$\n\rOUT OF MEMORY.\n\r$'
ERRMSG_TABLE_ORIG = struct.pack('<HH', 0x3388, 0x3399)


class PatchError(Exception):
    pass


def load_strings(locale):
    with open(os.path.join('localization', locale, 'strings.json'), encoding='utf-8') as f:
        data = json.load(f)
    return data['meta'], {s['id']: s for s in data['strings']}


def build_spec(locale):
    """Tworzy listę zmian bajtowych na podstawie strings.json."""
    meta, S = load_strings(locale)
    enc = meta.get('console_encoding', 'cp852')
    spec = []
    # --- 1.EXE: komunikaty błędów -------------------------------------------
    v = S['exe.video_error']['translation']
    m = S['exe.out_of_memory']['translation']
    for sid, t in (('exe.video_error', v), ('exe.out_of_memory', m)):
        if '$' in t:
            raise PatchError('%s: znak "$" kończy tekst w funkcji DOS 09h' % sid)
        try:
            t.encode(enc)
        except UnicodeEncodeError as e:
            raise PatchError('%s: znak niedostępny w %s: %s' % (sid, enc, e))
    m1 = b'\n\r' + v.encode(enc) + b'\n\r$'
    m2 = b'\n\r' + m.encode(enc) + b'\n\r$'
    block = m1 + m2
    if len(block) > ERRMSG_BLOCK_SIZE:
        raise PatchError('komunikaty błędów zajmują %d B, dostępne %d B (skróć tłumaczenia o %d znaków)'
                         % (len(block), ERRMSG_BLOCK_SIZE, len(block) - ERRMSG_BLOCK_SIZE))
    block = block.ljust(ERRMSG_BLOCK_SIZE, b'\0')
    spec.append({'file': '1.EXE', 'offset': ERRMSG_BLOCK, 'expect': ERRMSG_ORIG.ljust(ERRMSG_BLOCK_SIZE, b'\0').hex(),
                 'replace': block.hex(), 'note': 'komunikaty błędów (exe.video_error, exe.out_of_memory)'})
    table = struct.pack('<HH', ERRMSG_BLOCK_DS, ERRMSG_BLOCK_DS + len(m1))
    spec.append({'file': '1.EXE', 'offset': ERRMSG_TABLE, 'expect': ERRMSG_TABLE_ORIG.hex(),
                 'replace': table.hex(), 'note': 'tablica wskaźników komunikatów DS:3384'})
    # --- RUNME.COM: linie menu ----------------------------------------------
    for e in gd.EXE_TEXTS:
        if e['file'] != 'RUNME.COM':
            continue
        s = S[e['id']]
        new = s['translation']
        if new == s['original']:
            continue          # bez zmian (np. EGA/VGA)
        if len(new) != e['size']:
            raise PatchError('%s: tłumaczenie ma %d znaków, wymagane dokładnie %d (dopełnij spacjami)'
                             % (e['id'], len(new), e['size']))
        try:
            raw = new.encode('ascii')
        except UnicodeEncodeError:
            raise PatchError('%s: menu RUNME.COM musi być w ASCII (działa w każdej stronie kodowej)' % e['id'])
        orig = s['original'].encode('ascii')
        spec.append({'file': 'RUNME.COM', 'offset': e['offset'], 'expect': orig.hex(),
                     'replace': raw.hex(), 'note': e['id']})
    return spec


def apply_spec(src_dir, spec, files=None):
    """Zwraca słownik nazwa -> nowe bajty. Weryfikuje SHA-256 i sygnatury."""
    out = {}
    for item in spec:
        name = item['file']
        if files is not None and name not in files:
            continue
        if name not in out:
            data = open(gd.find_file(src_dir, name), 'rb').read()
            size, digest = gd.KNOWN_FILES[name]
            if hashlib.sha256(data).hexdigest() != digest:
                raise PatchError('%s: nieobsługiwana wersja pliku (SHA-256 się nie zgadza)' % name)
            out[name] = bytearray(data)
        buf = out[name]
        off = item['offset']
        exp = bytes.fromhex(item['expect'])
        rep = bytes.fromhex(item['replace'])
        if len(exp) != len(rep):
            raise PatchError('%s@0x%X: zmiana długości niedozwolona' % (name, off))
        if bytes(buf[off:off + len(exp)]) != exp:
            raise PatchError('%s@0x%X: sygnatura nie pasuje (%s)' % (name, off, item.get('note')))
        buf[off:off + len(rep)] = rep
    return {k: bytes(v) for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', default='original')
    ap.add_argument('--locale', default='pl')
    ap.add_argument('--output', default='work/exe')
    ap.add_argument('--spec', default=os.path.join('patches', 'text_patches.json'),
                    help='gdzie zapisać wygenerowaną specyfikację zmian (do wglądu)')
    args = ap.parse_args()
    try:
        spec = build_spec(args.locale)
        res = apply_spec(args.source, spec)
    except PatchError as e:
        print('BŁĄD:', e)
        return 1
    os.makedirs(args.output, exist_ok=True)
    for name, data in res.items():
        with open(os.path.join(args.output, name), 'wb') as f:
            f.write(data)
    os.makedirs(os.path.dirname(args.spec), exist_ok=True)
    with open(args.spec, 'w', encoding='utf-8') as f:
        json.dump([dict(i, offset='0x%X' % i['offset']) for i in spec], f, indent=1, ensure_ascii=False)
    for i in spec:
        print('  %-10s 0x%05X  %3d B  %s' % (i['file'], i['offset'], len(i['replace']) // 2, i['note']))
    print('Zapisano %d plików do %s, specyfikacja: %s' % (len(res), args.output, args.spec))
    return 0


if __name__ == '__main__':
    sys.exit(main())

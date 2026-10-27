#!/usr/bin/env python3
"""Eksport zasobów The Blues Brothers (DOS) do edytowalnych formatów.

Użycie:
    python tools/extract.py --source original --output work/extracted

Tworzy:
    manifest.json            identyfikacja plików (rozmiar, SHA-256, typ)
    images/*.png             ekrany i arkusze kafli (PNG indeksowany, oryginalna paleta)
    images/*.json            metadane ILBM potrzebne do odtworzenia pliku
    sprites/<PLIK>/*.png     klatki sprite'ów + arkusz + metadane
    foreground/*.png         kafle pierwszego planu AVT*.SQV
    maps/*.png               podgląd całych map poziomów
    fonts/digits.png         font cyfr 8x8 z 1.EXE
    texts.json               teksty z plików wykonywalnych (UTF-8)
    roundtrip.txt            raport testu dekompresja -> kompresja -> dekompresja
"""
import argparse
import base64
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbformats as bf  # noqa: E402
import gamedata as gd  # noqa: E402

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit('Wymagany pakiet Pillow: pip install Pillow')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def palette_bytes(pal):
    flat = [c for rgb in pal for c in rgb]
    return flat + [0] * (768 - len(flat))


def save_indexed(path, w, h, pixels, pal):
    img = Image.frombytes('P', (w, h), bytes(pixels))
    img.putpalette(palette_bytes(pal))
    img.save(path, optimize=False)


def level_palette(src, ck_name):
    data = bf.unpack(open(os.path.join(src, ck_name), 'rb').read())
    return bf.ILBM.parse(data).palette


def export_ilbm(src, out, name, report):
    raw = open(os.path.join(src, name), 'rb').read()
    data = bf.unpack(raw)
    im = bf.ILBM.parse(data)
    os.makedirs(os.path.join(out, 'images'), exist_ok=True)
    visible_h = min(im.height, 200)
    save_indexed(os.path.join(out, 'images', name + '.png'), im.width, im.height, im.pixels, im.palette)
    meta = {
        'file': name,
        'width': im.width,
        'height': im.height,
        'visible_height': visible_h,
        'planes': im.planes,
        'compression': im.compression,
        'palette': im.palette,
        'chunks': [[t.decode('latin-1'), None if c is None else base64.b64encode(c).decode()] for t, c in im.chunks],
        'ilbm_size': len(data),
        'sqz_size': len(raw),
        'sha256': sha256(raw),
    }
    with open(os.path.join(out, 'images', name + '.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1)
    # round-trip: kodowanie -> kompresja -> dekompresja -> porównanie pikseli
    enc = im.encode()
    packed = bf.pack(enc)
    back = bf.ILBM.parse(bf.unpack(packed))
    ok = back.pixels == im.pixels and back.palette == im.palette
    report.append('%-14s ILBM %5d -> %5d  SQZ %5d -> %5d  piksele: %s  nadmiar DOS: %d' % (
        name, len(data), len(enc), len(raw), len(packed), 'OK' if ok else 'BŁĄD', bf.dos_overrun(packed)))
    return ok


def export_sqv(src, out, name, pal, report):
    raw = open(os.path.join(src, name), 'rb').read()
    data = bf.unpack(raw)
    frames, rest = bf.parse_sqv(data)
    d = os.path.join(out, 'sprites', name)
    os.makedirs(d, exist_ok=True)
    meta = {'file': name, 'count': len(frames), 'trailing': base64.b64encode(rest).decode(),
            'header_extra': None, 'frames': []}
    sheet_w = 640
    x = y = rowh = 0
    pos = []
    for f in frames:
        if x + f['w'] > sheet_w:
            x = 0
            y += rowh + 2
            rowh = 0
        pos.append((x, y))
        x += f['w'] + 2
        rowh = max(rowh, f['h'])
    sheet = Image.new('P', (sheet_w, y + rowh), 0)
    sheet.putpalette(palette_bytes(pal))
    for i, f in enumerate(frames):
        pix = bf.decode_planar(f['data'], f['w'], f['h'])
        save_indexed(os.path.join(d, 'frame_%03d.png' % i), f['w'], f['h'], pix, pal)
        img = Image.frombytes('P', (f['w'], f['h']), bytes(pix))
        sheet.paste(img, pos[i])
        meta['frames'].append({'index': i, 'w': f['w'], 'h': f['h'], 'offset': f['offset']})
    sheet.save(os.path.join(out, 'sprites', name + '_sheet.png'))
    with open(os.path.join(d, 'meta.json'), 'w', encoding='utf-8') as fh:
        json.dump(meta, fh, indent=1)
    rebuilt = bf.build_sqv([(f['w'], f['h'], f['data']) for f in frames], rest)
    ok = rebuilt == data and bf.unpack(bf.pack(rebuilt)) == data
    report.append('%-14s %3d klatek, round-trip: %s' % (name, len(frames), 'OK' if ok else 'BŁĄD'))
    return ok


def export_avt(src, out, name, pal, report):
    raw = open(os.path.join(src, name), 'rb').read()
    data = bf.unpack(raw)
    count = struct.unpack_from('<H', data, 0)[0]
    os.makedirs(os.path.join(out, 'foreground'), exist_ok=True)
    img = Image.new('P', (count * 16, 16), 0)
    img.putpalette(palette_bytes(pal))
    for i in range(count):
        off = 6 + i * 132
        pix = bf.decode_planar(data[off:off + 128], 16, 16)
        img.paste(Image.frombytes('P', (16, 16), bytes(pix)), (i * 16, 0))
    img.save(os.path.join(out, 'foreground', name + '.png'))
    ok = bf.unpack(bf.pack(data)) == data
    report.append('%-14s %3d kafli AVT, round-trip: %s' % (name, count, 'OK' if ok else 'BŁĄD'))
    return ok


def export_map(src, out, lvl, report):
    sql = bf.unpack(open(os.path.join(src, lvl['sql']), 'rb').read())
    sheets = []
    for ck in (lvl['ck1'], lvl['ck2']):
        im = bf.ILBM.parse(bf.unpack(open(os.path.join(src, ck), 'rb').read()))
        img = Image.frombytes('P', (320, im.height), bytes(im.pixels))
        img.putpalette(palette_bytes(im.palette))
        sheets.append(img.convert('RGB'))
    h = len(sql) // 128
    out_img = Image.new('RGB', (128 * 16, h * 16))
    for y in range(h):
        for x in range(128):
            v = sql[y * 128 + x]
            t = v & 0x7F
            s = sheets[v >> 7]
            out_img.paste(s.crop(((t % 20) * 16, (t // 20) * 16, (t % 20) * 16 + 16, (t // 20) * 16 + 16)), (x * 16, y * 16))
    os.makedirs(os.path.join(out, 'maps'), exist_ok=True)
    out_img.save(os.path.join(out, 'maps', lvl['sql'] + '.png'))
    ok = bf.unpack(bf.pack(sql)) == sql
    report.append('%-14s mapa 128x%d, round-trip: %s' % (lvl['sql'], h, 'OK' if ok else 'BŁĄD'))
    return ok


def export_digits(src, out):
    exe = open(os.path.join(src, '1.EXE'), 'rb').read()
    off = gd.DIGIT_FONT_FILE_OFFSET
    pal = level_palette(src, 'MAG.CK1')
    img = Image.new('P', (10 * 8, 8), 0)
    img.putpalette(palette_bytes(pal))
    for i in range(10):
        pix = bf.decode_planar(exe[off + i * 32:off + i * 32 + 32], 8, 8)
        img.paste(Image.frombytes('P', (8, 8), bytes(pix)), (i * 8, 0))
    os.makedirs(os.path.join(out, 'fonts'), exist_ok=True)
    img.save(os.path.join(out, 'fonts', 'digits.png'))


def export_texts(src, out):
    res = []
    for entry in gd.EXE_TEXTS:
        data = open(os.path.join(src, entry['file']), 'rb').read()
        raw = data[entry['offset']:entry['offset'] + entry['size']]
        res.append({'id': entry['id'], 'file': entry['file'], 'offset': '0x%X' % entry['offset'],
                    'size': entry['size'], 'text': raw.decode('cp437')})
    with open(os.path.join(out, 'texts.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', default='original')
    ap.add_argument('--output', default='work/extracted')
    args = ap.parse_args()
    src, out = args.source, args.output
    os.makedirs(out, exist_ok=True)
    ident = gd.identify(src)
    with open(os.path.join(out, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(ident, f, indent=1, ensure_ascii=False)
    if ident['unknown'] or ident['mismatch'] or ident['missing']:
        print('UWAGA: pliki nie zgadzają się z obsługiwaną wersją:', ident['mismatch'], ident['missing'])
    report = []
    ok = True
    for name in gd.ILBM_FILES:
        ok &= export_ilbm(src, out, name, report)
    for lvl in gd.LEVELS:
        pal = level_palette(src, lvl['ck1'])
        ok &= export_sqv(src, out, lvl['enemies'], pal, report)
        if lvl['avt']:
            ok &= export_avt(src, out, lvl['avt'], pal, report)
        ok &= export_map(src, out, lvl, report)
    ok &= export_sqv(src, out, 'SPRITE.SQV', level_palette(src, 'MAG.CK1'), report)
    export_digits(src, out)
    export_texts(src, out)
    with open(os.path.join(out, 'roundtrip.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(report) + '\n')
    print('\n'.join(report))
    print('Eksport zakończony: %s (%s)' % (out, 'wszystkie round-tripy OK' if ok else 'BŁĘDY round-trip'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

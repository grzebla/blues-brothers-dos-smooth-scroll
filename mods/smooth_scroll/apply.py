#!/usr/bin/env python3
"""Mod "płynne przewijanie" dla 1.EXE (The Blues Brothers, DOS).

Użycie:
    python mods/smooth_scroll/apply.py WEJŚCIE.EXE WYJŚCIE.EXE

Wymaga nasm. Zmiany (adresy seg:off w obrazie programu):
  01DC:116A-145E  rysowanie tła i kafli pierwszego planu (seg01dc.asm, sekcja A)
  01DC:145F-14F4  call camera / jmp 14F5, przesuwanie tła o 0-7 px (sekcja B)
  01DC:1502-1626  jmp redraw, kamera (sekcja C)
  003A:0C15-0DEF  lista kafli pierwszego planu (seg003a.asm)
  0351:19CB       lcall 01DC:fgblit zamiast 0B8F:0008
  0B8F:0152       retf: koniec zapisu kafli do bufora pierścieniowego VRAM 4000h
                  (ten obszar służy teraz do składania tła)
Relokacje leżące w nadpisanych obszarach są przekierowane na nieużywane
słowo w nowym kodzie, inaczej loader DOS zmieniłby bajty nowego kodu.
"""
import os
import re
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# 1.EXE angielskiej wersji (sprawdzane bajty w miejscach zmian)
EXPECT = {
    (0x01DC, 0x145F): bytes.fromhex('f70686280200'),
    (0x01DC, 0x1502): bytes.fromhex('833e822814'),
    (0x01DC, 0x116A): bytes.fromhex('558bec83ec08'),
    (0x003A, 0x0C15): bytes.fromhex('558bec83ec1e'),
    (0x0351, 0x19CB): bytes.fromhex('9a08008f0b'),
    (0x0B8F, 0x0152): bytes.fromhex('5053515257'),
}

# sekcje seg01dc.asm: plik wynikowy odwzorowuje 01DC:116A-1626
SECTIONS_01DC = [(0x116A, 0x145F), (0x145F, 0x14F5), (0x1502, 0x1627)]


def assemble(name):
    src = os.path.join(HERE, name)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'out.bin')
        mapf = os.path.join(tmp, 'out.map')
        with open(src) as f:
            text = f.read()
        asm = os.path.join(tmp, 'in.asm')
        with open(asm, 'w') as f:
            f.write(f'[map symbols {mapf}]\n' + text)
        subprocess.run(['nasm', '-f', 'bin', '-o', out, asm], check=True)
        with open(out, 'rb') as f:
            code = f.read()
        with open(mapf) as f:
            syms = {m.group(2): int(m.group(1), 16)
                    for m in re.finditer(r'^\s*[0-9A-Fa-f]+\s+([0-9A-Fa-f]+)\s+(\S+)\s*$', f.read(), re.M)}
    return code, syms


class ModError(Exception):
    pass


def apply_smooth_scroll(data):
    """Nakłada mod na obraz 1.EXE (bytearray, zmieniany w miejscu). Zwraca opis zmian."""
    hdr = struct.unpack_from('<14H', data)
    nrel, hpar, relo = hdr[3], hdr[4], hdr[12]
    base = hpar * 16

    def lin(seg, off):
        return base + seg * 16 + off

    for (seg, off), want in EXPECT.items():
        got = bytes(data[lin(seg, off):lin(seg, off) + len(want)])
        if got != want:
            raise ModError(f'{seg:04X}:{off:04X}: nieoczekiwane bajty {got.hex()} '
                           f'(oczekiwano {want.hex()}) - inna wersja 1.EXE?')

    c1dc, s1dc = assemble('seg01dc.asm')
    c03a, _ = assemble('seg003a.asm')

    patches = []   # (seg, off, bytes)
    for a, b in SECTIONS_01DC:
        patches.append((0x01DC, a, c1dc[a - 0x116A:b - 0x116A]))
    patches.append((0x003A, 0x0C15, c03a))
    # 0351:19CB: lcall 01DC:fgblit (słowo segmentu ma już relokację)
    patches.append((0x0351, 0x19CB, b'\x9a' + struct.pack('<HH', s1dc['fgblit'], 0x01DC)))
    patches.append((0x0B8F, 0x0152, b'\xcb'))

    # relokacje w nadpisanych obszarach (poza słowem segmentu lcall w 0351:19CB)
    keep = {lin(0x0351, 0x19CB + 3) - base}
    ranges = [(lin(s, o) - base, lin(s, o) - base + len(b)) for s, o, b in patches]
    moved = 0
    for i in range(nrel):
        o, s = struct.unpack_from('<HH', data, relo + 4 * i)
        p = s * 16 + o
        if p in keep:
            continue
        if any(a <= p < b or a <= p + 1 < b for a, b in ranges):
            struct.pack_into('<HH', data, relo + 4 * i, s1dc['reloc_scratch'], 0x01DC)
            moved += 1

    for seg, off, b in patches:
        data[lin(seg, off):lin(seg, off) + len(b)] = b

    used = ', '.join(f'{a:04X}: {len(c1dc[a - 0x116A:b - 0x116A].rstrip(bytes([0x90])))}/{b - a} B'
                     for a, b in SECTIONS_01DC)
    return (f'płynne przewijanie: kod 01DC {used}; 003A: {len(c03a.rstrip(bytes([0x90])))}/{0x0DF0 - 0x0C15} B; '
            f'przekierowane relokacje: {moved}')


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1:]
    data = bytearray(open(src, 'rb').read())
    try:
        info = apply_smooth_scroll(data)
    except ModError as e:
        sys.exit(f'BŁĄD: {e}')
    with open(dst, 'wb') as f:
        f.write(data)
    print(info)


if __name__ == '__main__':
    main()

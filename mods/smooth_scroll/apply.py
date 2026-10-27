#!/usr/bin/env python3
"""Mod "płynne przewijanie" dla 1.EXE (The Blues Brothers, DOS).

Użycie:
    python mods/smooth_scroll/apply.py WEJŚCIE.EXE WYJŚCIE.EXE

Wymaga nasm. Zmiany (adresy seg:off w obrazie programu):
  01DC:116A-145E  nowy kod: kamera, rysowanie tła, rysowanie kafli
                  pierwszego planu z przycinaniem (seg01dc.asm)
  01DC:145F       call camera / jmp 14F5 (zamiast kroków po 16 px)
  01DC:1502       jmp redraw (zamiast składania z bufora pierścieniowego)
  003A:0C15-0DEF  lista kafli pierwszego planu (seg003a.asm)
  0351:19CB       lcall 01DC:fgblit zamiast 0B8F:0008
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
}


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
                    for m in re.finditer(r'^\s*([0-9A-Fa-f]+)\s+[0-9A-Fa-f]+\s+(\S+)\s*$', f.read(), re.M)}
    return code, syms


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1:]
    data = bytearray(open(src, 'rb').read())
    hdr = struct.unpack_from('<14H', data)
    nrel, hpar, relo = hdr[3], hdr[4], hdr[12]
    base = hpar * 16

    def lin(seg, off):
        return base + seg * 16 + off

    for (seg, off), want in EXPECT.items():
        got = bytes(data[lin(seg, off):lin(seg, off) + len(want)])
        if got != want:
            sys.exit(f'{seg:04X}:{off:04X}: nieoczekiwane bajty {got.hex()} (oczekiwano {want.hex()}) - inna wersja 1.EXE?')

    c1dc, s1dc = assemble('seg01dc.asm')
    c03a, _ = assemble('seg003a.asm')

    patches = []   # (seg, off, bytes)
    patches.append((0x01DC, 0x116A, c1dc + b'\x90' * (0x145F - 0x116A - len(c1dc))))
    # 145F: call camera / jmp 14F5 (oba near)
    call = s1dc['camera'] - (0x145F + 3)
    jmp = 0x14F5 - (0x1462 + 3)
    stub = b'\xe8' + struct.pack('<h', call) + b'\xe9' + struct.pack('<h', jmp)
    patches.append((0x01DC, 0x145F, stub + b'\x90' * (0x14F5 - 0x145F - len(stub))))
    # 1502: jmp near redraw
    jmpn = s1dc['redraw'] - (0x1502 + 3)
    stub = b'\xe9' + struct.pack('<h', jmpn)
    patches.append((0x01DC, 0x1502, stub + b'\x90' * (0x1627 - 0x1502 - len(stub))))
    patches.append((0x003A, 0x0C15, c03a + b'\x90' * (0x0DF0 - 0x0C15 - len(c03a))))
    # 0351:19CB: lcall 01DC:fgblit (słowo segmentu ma już relokację)
    patches.append((0x0351, 0x19CB, b'\x9a' + struct.pack('<HH', s1dc['fgblit'], 0x01DC)))

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

    with open(dst, 'wb') as f:
        f.write(data)
    print(f'01DC: {len(c1dc)} B, '
          f'003A: {len(c03a)} B, '
          f'przekierowane relokacje: {moved}')
    print('symbole:', {k: hex(v) for k, v in s1dc.items() if k in ('camera', 'redraw', 'fgblit', 'reloc_scratch')})


if __name__ == '__main__':
    main()

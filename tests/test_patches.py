"""Łatki TYLKO do testów automatycznych (nie są częścią polonizacji ani patcha).

Pozwalają w kontrolowany sposób dotrzeć do ekranów, których nie da się
osiągnąć samym wstrzykiwaniem klawiszy w rozsądnym czasie. Każda łatka
sprawdza oczekiwane bajty przed zmianą.
"""
import struct

# 003A:01C0  mov byte ptr [0x2895], 0     - numer poziomu przy starcie gry
LEVEL_OFF, LEVEL_EXPECT = 0x2760, bytes.fromhex('c606952800')
# 0351:0553  cmp byte ptr [0x28D0], 0      - flaga końca gry -> skok do rysowania klatki 127
GAMEOVER_OFF, GAMEOVER_EXPECT = 0x5C63, bytes.fromhex('803ed02800')
GAMEOVER_PATCH = bytes.fromhex('e932009090')   # jmp 0588 (wywołanie rysowania "GAME OVER")
# 0351:04E2  cmp byte ptr [0x28CF], 0 / je 0553 - flaga ukończenia poziomu
COMPLETE_OFF, COMPLETE_EXPECT = 0x5BF2, bytes.fromhex('803ecf2800746a')
COMPLETE_PATCH = bytes.fromhex('90909090909090')  # zawsze "ukończony" -> po 50 klatkach następny poziom
# tablice źródłowe pozycji startowych (41 obiektów x int16), gracz 1 = indeks 39.
# Procedury 003A:0287.. kopiują je przy wczytaniu poziomu do kopii roboczej DS:2521/DS:22E3.
# Poziom 1: X DS:270D, Y DS:24CF; poziomy 2-6: DS:2521+82*L / DS:22E3+82*L.
DS_FILE = 0x11E00
TABLE_STRIDE, PLAYER1 = 82, 39


def _xy_tables(level):
    if level == 0:
        return DS_FILE + 0x270D, DS_FILE + 0x24CF
    return DS_FILE + 0x2521 + TABLE_STRIDE * level, DS_FILE + 0x22E3 + TABLE_STRIDE * level


def _patch(buf, off, expect, new):
    if bytes(buf[off:off + len(expect)]) != expect:
        raise ValueError('łatka testowa: nieoczekiwane bajty @0x%X' % off)
    buf[off:off + len(new)] = new


def start_level(buf, level):
    _patch(buf, LEVEL_OFF, LEVEL_EXPECT, LEVEL_EXPECT[:4] + bytes([level]))


def force_gameover(buf):
    _patch(buf, GAMEOVER_OFF, GAMEOVER_EXPECT, GAMEOVER_PATCH)


def auto_complete(buf):
    _patch(buf, COMPLETE_OFF, COMPLETE_EXPECT, COMPLETE_PATCH)


def player_start(buf, level, x, y):
    xt, yt = _xy_tables(level)
    struct.pack_into('<H', buf, xt + PLAYER1 * 2, x)
    struct.pack_into('<H', buf, yt + PLAYER1 * 2, y)


def map_edit(game_dir, sql_name, cells):
    """[tylko testy] Wstawia kafle do mapy poziomu: cells = [(x, y, bajt_kafla), ...]."""
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
    import bbformats as bf
    p = os.path.join(game_dir, sql_name)
    m = bytearray(bf.unpack(open(p, 'rb').read()))
    for x, y, v in cells:
        m[y * 128 + x] = v
    open(p, 'wb').write(bf.pack(bytes(m)))


# DS:3384 - tablica wskaźników komunikatów błędów (0: brak EGA/VGA, 1: brak pamięci)
ERRTAB_OFF = DS_FILE + 0x3384


def swap_error_messages(buf):
    """[tylko testy] zamienia wpisy tablicy, aby test karty wypisał komunikat nr 1."""
    a, b = struct.unpack_from('<HH', buf, ERRTAB_OFF)
    struct.pack_into('<HH', buf, ERRTAB_OFF, b, a)

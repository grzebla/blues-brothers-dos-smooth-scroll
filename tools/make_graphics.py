#!/usr/bin/env python3
"""Generuje polskie wersje grafik z napisami.

Użycie:
    python tools/make_graphics.py [--source original] [--locale pl] [--preview DIR]

Dla każdego zasobu z napisami:
  1. dekoduje oryginalny obraz (lub klatkę sprite'a),
  2. usuwa angielski napis (przywracając tło),
  3. renderuje tłumaczenie z localization/<locale>/strings.json fontem z
     localization/<locale>/fonts/ w stylu oryginału,
  4. zapisuje indeksowany PNG z oryginalną paletą do localization/<locale>/graphics/.

PNG-i można potem poprawiać ręcznie w dowolnym edytorze obsługującym tryb
indeksowany (paleta i indeksy kolorów muszą zostać zachowane). Aby generator
nie nadpisał ręcznych zmian, ustaw "mode": "manual" w odpowiednim wpisie
strings.json.

Maski dużych napisów (INSERT, GAME OVER) są renderowane z krojów systemowych
macOS (SuperClarendon Black, Chalkboard SE Bold) i zapisywane do graphics/masks/*.png.
Jeżeli krój nie jest dostępny, używana jest zapisana maska - można ją też
narysować ręcznie (biały = litera).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbformats as bf  # noqa: E402
import gamedata as gd  # noqa: E402
import glyphkit as gk  # noqa: E402

T = gk.TRANSPARENT

SUPERCLARENDON = '/System/Library/Fonts/Supplemental/SuperClarendon.ttc'
CHALKBOARD = '/System/Library/Fonts/Supplemental/ChalkboardSE.ttc'


class Ctx:
    def __init__(self, src, locale):
        self.src = src
        self.loc = os.path.join('localization', locale)
        with open(os.path.join(self.loc, 'strings.json'), encoding='utf-8') as f:
            self.strings = {s['id']: s for s in json.load(f)['strings']}
        self.fonts = {}
        self.out = os.path.join(self.loc, 'graphics')
        os.makedirs(os.path.join(self.out, 'masks'), exist_ok=True)
        self.log = []

    def font(self, name):
        if name not in self.fonts:
            self.fonts[name] = gk.load_font(os.path.join(self.loc, 'fonts', name + '.json'))
        return self.fonts[name]

    def text(self, sid):
        s = self.strings[sid]
        return s['translation']

    def manual(self, sid):
        return self.strings[sid].get('mode') == 'manual'


def load_ilbm(ctx, name):
    data = bf.unpack(open(gd.find_file(ctx.src, name), 'rb').read())
    im = bf.ILBM.parse(data)
    return np.array(im.pixels, dtype=np.uint8).reshape(im.height, im.width), im.palette


def save_png(path, arr, palette):
    img = Image.fromarray(arr.astype(np.uint8), 'P')
    flat = [c for rgb in palette for c in rgb]
    img.putpalette(flat + [0] * (768 - len(flat)))
    img.save(path)


def shadowed(arr, color, dx=1):
    m = arr != T
    out = np.full((arr.shape[0], arr.shape[1] + dx), T, np.uint8)
    sh = np.zeros(out.shape, bool)
    sh[:, dx:] = m
    out[sh] = color
    out[:, :arr.shape[1]][m] = arr[m]
    return out


def fit_check(ctx, sid, width, limit):
    if width > limit:
        raise SystemExit('BŁĄD: tłumaczenie %s (%r) ma %d px, limit %d px' % (sid, ctx.text(sid), width, limit))


# ---------------------------------------------------------------------------
# CHOIX.SQZ - pasek "← CHOOSE YOUR PLAYER → PRESS FIRE TO START"
# ---------------------------------------------------------------------------
def make_choix(ctx):
    a, pal = load_ilbm(ctx, 'CHOIX.SQZ')
    f = ctx.font('choix')
    t1 = gk.render_text(f, ctx.text('choix.choose_player'))
    t2 = gk.render_text(f, ctx.text('choix.press_fire'))
    la = gk.render_text(f, '←')
    ra = gk.render_text(f, '→')
    a[192:200, :] = 0
    # układ jak w oryginale: strzałka x=1, tekst od x=12, strzałka, odstęp 9, tekst
    gk.blit(a, la, 1, 190)
    x = 12
    gk.blit(a, t1, x, 190)
    x += t1.shape[1] + 6
    gk.blit(a, ra, x, 190)
    x += ra.shape[1] + 9
    x2 = min(x, 317 - t2.shape[1])
    if x2 < x - 6:
        fit_check(ctx, 'choix.press_fire', x + t2.shape[1], 317)
    gk.blit(a, t2, x2, 190)
    ctx.log.append('CHOIX.SQZ: pasek wyboru postaci (%d + %d px)' % (t1.shape[1], t2.shape[1]))
    return a, pal


# ---------------------------------------------------------------------------
# INTER.SQZ - szyldy na mapie
# ---------------------------------------------------------------------------
def inpaint_row(a, mask):
    """Zastępuje piksele maski najbliższym nie-maskowanym pikselem z tej samej linii."""
    H, W = a.shape
    out = a.copy()
    for y, x in zip(*np.nonzero(mask)):
        for d in range(1, W):
            for xx in (x - d, x + d):
                if 0 <= xx < W and not mask[y, xx]:
                    out[y, x] = a[y, xx]
                    break
            else:
                continue
            break
    return out


def make_inter(ctx):
    a, pal = load_ilbm(ctx, 'INTER.SQZ')
    # szyld fabryki: panel kolor 14, litery 13, cień 11 (1 px w prawo)
    y0, y1, x0, x1 = 48, 54, 9, 82
    reg = a[y0:y1, x0:x1]
    reg[(reg == 13) | (reg == 11)] = 14
    t = shadowed(gk.render_text(ctx.font('inter_chem'), ctx.text('inter.chemicals')), 11)
    fit_check(ctx, 'inter.chemicals', t.shape[1], x1 - x0)
    gk.blit(a, t, x0 + (x1 - x0 - t.shape[1]) // 2, y0)
    # napis na dachu sklepu: litery 13, cień 4; tło uzupełniane z sąsiedztwa
    y0, y1, x0, x1 = 159, 166, 183, 228
    reg = a[y0:y1, x0:x1]
    m = (reg == 13) | (reg == 4)
    a[y0:y1, x0:x1] = inpaint_row(reg, m)
    t = shadowed(gk.render_text(ctx.font('inter_store'), ctx.text('inter.store')), 4)
    fit_check(ctx, 'inter.store', t.shape[1], x1 - x0)
    cx = 185 + 43 // 2  # środek oryginalnego napisu STORE (x 185-227)
    gk.blit(a, t, cx - t.shape[1] // 2, y0)
    ctx.log.append('INTER.SQZ: szyldy %r, %r' % (ctx.text('inter.chemicals'), ctx.text('inter.store')))
    return a, pal


# ---------------------------------------------------------------------------
# INSERT.SQZ - "INSERT DISK II"
# ---------------------------------------------------------------------------
def style_engraved(mask):
    """Styl napisu INSERT: brzeg 12, linia 13, linia 14, szczelina 0, wnętrze 12."""
    d = gk.chebyshev_depth(mask)
    out = np.zeros(mask.shape, np.uint8)
    for k, v in {1: 12, 2: 13, 3: 14, 4: 0}.items():
        out[d == k] = v
    out[d >= 5] = 12
    # cienkie elementy (akcenty, kropki): bez ciemnego brzegu byłyby niewidoczne
    lab, n = gk.label(mask)
    for i in range(1, n + 1):
        comp = lab == i
        if d[comp].max() <= 3:
            out[comp & (d == 1)] = 13
            out[comp & (d >= 2)] = 14
    return out


def get_mask(ctx, name, text, builder):
    """Maska z kroju TTF (jeśli dostępny), z pamięcią podręczną w graphics/masks."""
    path = os.path.join(ctx.out, 'masks', name + '.png')
    meta_path = path + '.json'
    cached = None
    if os.path.exists(path) and os.path.exists(meta_path):
        meta = json.load(open(meta_path, encoding='utf-8'))
        if meta.get('text') == text:
            cached = (np.array(Image.open(path).convert('L')) > 127, meta)
    if cached and (meta.get('manual') or not builder.available()):
        return cached
    if not builder.available():
        if cached:
            return cached
        raise SystemExit('BŁĄD: brak kroju do wygenerowania maski %s i brak zapisanej maski dla %r' % (name, text))
    mask, meta = builder.build(text)
    meta['text'] = text
    Image.fromarray((mask * 255).astype(np.uint8), 'L').save(path)
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return mask, meta


class TTFBuilder:
    def __init__(self, path, index, cap, xs, gap, space, stroke=0, fit_width=None):
        self.path, self.index, self.cap, self.xs, self.gap, self.space = path, index, cap, xs, gap, space
        self.stroke, self.fit_width = stroke, fit_width

    def available(self):
        return os.path.exists(self.path)

    def build(self, text):
        m, base, spans = gk.render_mask_ttf(text, self.path, self.index, self.cap, self.xs,
                                            gap=self.gap, space=self.space, stroke=self.stroke,
                                            fit_width=self.fit_width)
        return m, {'baseline': base, 'spans': spans, 'font': os.path.basename(self.path), 'index': self.index}


def make_insert(ctx):
    a, pal = load_ilbm(ctx, 'INSERT.SQZ')
    text = ctx.text('insert.insert_disk')
    mask, meta = get_mask(ctx, 'INSERT', text, TTFBuilder(SUPERCLARENDON, 7, 40, 0.47, 0.06, 0.30))
    a[95:150, :] = 0
    # akcenty i kropki (składowe całkowicie nad linią wersalików) pogrubiamy o 1 px
    cap_top = meta['baseline'] - 40
    lab, n = gk.label(mask)
    mask = mask.copy()
    for i in range(1, n + 1):
        comp = lab == i
        if np.nonzero(comp)[0].max() < cap_top:
            mask |= gk.dilate(comp, 1)
    st = style_engraved(mask)
    h, w = mask.shape
    fit_check(ctx, 'insert.insert_disk', w, 300)
    base = meta['baseline']           # linia bazowa wersalików w masce
    y = 145 - base                    # oryginalne litery kończą się w linii 144
    x = 160 - w // 2
    region = a[y:y + h, x:x + w]
    region[mask] = st[mask]
    ctx.log.append('INSERT.SQZ: %r (%d x %d px)' % (text, w, h))
    return a, pal


# ---------------------------------------------------------------------------
# Neony w MAG.CK1 / MAG.CK2
# ---------------------------------------------------------------------------
NEON_LUT = {1: 7, 2: 13, 3: 14}
NEON_BG = 11


def neon_replace(canvas, core_rows, text, font, mirror=False):
    """canvas - wycinek z oryginalnym neonem; podmienia napis zachowując położenie."""
    old_core = canvas == 5
    ys, xs = np.nonzero(old_core)
    d_old = gk.manhattan_distance(old_core, canvas.shape)
    canvas[d_old <= 3] = NEON_BG
    skel = gk.render_text(font, text) != T
    if mirror:
        skel = skel[:, ::-1]
    h, w = skel.shape
    cx = (xs.min() + xs.max() + 1) / 2.0
    x0 = int(round(cx - w / 2.0))
    y0 = ys.min()
    if x0 < 0 or x0 + w > canvas.shape[1]:
        raise SystemExit('BŁĄD: neon %r za szeroki (%d px)' % (text, w))
    core = np.zeros(canvas.shape, bool)
    core[y0:y0 + h, x0:x0 + w] = skel
    d = gk.manhattan_distance(core, canvas.shape)
    for k, v in NEON_LUT.items():
        canvas[d == k] = v
    canvas[core] = 5
    return canvas


def make_mag(ctx):
    font = ctx.font('neon')
    c2, pal2 = load_ilbm(ctx, 'MAG.CK2')
    for sid, (x0, x1, y0, y1), mirror in [
            ('mag.neon_store', (160, 192, 32, 48), False),
            ('mag.neon_music', (256, 288, 64, 80), False),
            ('mag.neon_store_mirror', (96, 128, 96, 112), True)]:
        c2[y0:y1, x0:x1] = neon_replace(c2[y0:y1, x0:x1].copy(), None, ctx.text(sid), font, mirror)
    c1, pal1 = load_ilbm(ctx, 'MAG.CK1')
    # lustrzany "MUSIC" rozdzielony na dwa kafle: (304-319, 48-63) | (0-15, 96-111)
    pair = np.concatenate([c1[48:64, 304:320], c1[96:112, 0:16]], axis=1).copy()
    pair = neon_replace(pair, None, ctx.text('mag.neon_music_mirror'), font, True)
    c1[48:64, 304:320] = pair[:, :16]
    c1[96:112, 0:16] = pair[:, 16:]
    ctx.log.append('MAG.CK1/CK2: neony %r, %r (+ odbicia lustrzane)' % (ctx.text('mag.neon_store'), ctx.text('mag.neon_music')))
    return (c1, pal1), (c2, pal2)


# ---------------------------------------------------------------------------
# VILLE.CK1 - tabliczka "PROGRAMMER"
# ---------------------------------------------------------------------------
def make_ville(ctx):
    a, pal = load_ilbm(ctx, 'VILLE.CK1')
    y0, y1, x0, x1 = 89, 94, 228, 284
    reg = a[y0:y1, x0:x1]
    old = np.nonzero((reg == 6).any(axis=0))[0]
    cx = x0 + (old.min() + old.max() + 1) / 2.0
    reg[reg == 6] = 3
    t = gk.render_text(ctx.font('plaque'), ctx.text('ville.plaque_role'))
    fit_check(ctx, 'ville.plaque_role', t.shape[1], x1 - x0)
    # font ma linię akcentów nad literami (linia 0 glifu) - litery zaczynają się w linii y0
    gk.blit(a, t, int(round(cx - t.shape[1] / 2.0)), y0 - 1)
    ctx.log.append('VILLE.CK1: tabliczka %r' % ctx.text('ville.plaque_role'))
    return a, pal


# ---------------------------------------------------------------------------
# SPRITE.SQV - "GAME OVER" (klatka 127) i "1UP" (klatka 134)
# ---------------------------------------------------------------------------
STRIPE_ROWS = {2: 7, 3: 5, 7: 7, 8: 7, 9: 7, 13: 5, 14: 5, 15: 5, 19: 7, 20: 7, 21: 7,
               25: 5, 26: 5, 27: 5, 31: 5, 32: 7}
CHECK_ROWS = (5, 11, 17, 23, 29)
# faktury liter od lewej do prawej (jak gradient w oryginale: niebieski -> biały -> niebieski)
GO_FILLS = ['48', '84', '8F', 'F', 'F', 'F', 'F8', '8', '48', '48']


def go_fill(kind, y, x):
    if len(kind) == 1:
        return int(kind, 16)
    return int(kind[(x + y) % 2], 16)


def make_gameover(ctx, frame):
    w, h, pix = frame
    a = np.array(pix, np.uint8).reshape(h, w)
    text = ctx.text('sprite.game_over')
    mask, meta = get_mask(ctx, 'GAMEOVER', text, TTFBuilder(CHALKBOARD, 2, 22, 1.0, 0.05, 0.35, stroke=4, fit_width=140))
    mh, mw = mask.shape
    fit_check(ctx, 'sprite.game_over', mw, 144)
    if mh > 25:
        raise SystemExit('BŁĄD: maska GAME OVER za wysoka (%d)' % mh)
    # tło: odtworzenie pasków w obszarze x 8-151, linie 5-30
    x0, x1 = 8, 155
    check_pattern = a[5, x0:x1].copy()
    check_pattern[(check_pattern != 15) & (check_pattern != 3)] = 15
    for y in range(5, 31):
        if y in CHECK_ROWS:
            a[y, x0:x1] = check_pattern
        else:
            a[y, x0:x1] = STRIPE_ROWS.get(y, 11)
    row31 = a[31, x0:x1]
    row31[(row31 != 5) & (row31 != 7)] = 5   # dolne końce oryginalnych liter
    full = np.zeros((h, w), bool)
    oy = 6 + (25 - mh) // 2
    ox = (w - mw) // 2
    full[oy:oy + mh, ox:ox + mw] = mask
    a[gk.dilate(full, 1) & ~full] = 11
    # faktura liter wg kolejności liter
    spans = meta['spans']
    letter_of = np.full(w, -1)
    for i, (sa, sb) in enumerate(spans):
        letter_of[ox + sa:ox + sb + 1] = i
    left_edge = full & ~np.pad(full, ((0, 0), (1, 0)))[:, :-1]
    for y, x in zip(*np.nonzero(full)):
        i = letter_of[x] if letter_of[x] >= 0 else 0
        kind = GO_FILLS[min(i, len(GO_FILLS) - 1)]
        a[y, x] = 4 if left_edge[y, x] else go_fill(kind, y, x)
    ctx.log.append('SPRITE.SQV[127]: %r' % text)
    return (w, h, a)


def make_oneup(ctx, frame):
    t = gk.render_text(ctx.font('popup'), ctx.text('sprite.one_up'))
    h = 7
    w = 32
    fit_check(ctx, 'sprite.one_up', t.shape[1], w)
    a = np.zeros((h, w), np.uint8)
    x = (w - t.shape[1]) // 2
    gk.blit(a, t, x, 0)
    ctx.log.append('SPRITE.SQV[134]: %r (klatka 32x7)' % ctx.text('sprite.one_up'))
    return (w, h, a)


def make_sprites(ctx, sheet_pal):
    data = bf.unpack(open(gd.find_file(ctx.src, 'SPRITE.SQV'), 'rb').read())
    frames, rest = bf.parse_sqv(data)
    out = {}
    f127 = frames[127]
    out[127] = make_gameover(ctx, (f127['w'], f127['h'], bf.decode_planar(f127['data'], f127['w'], f127['h'])))
    out[134] = make_oneup(ctx, frames[134])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', default='original')
    ap.add_argument('--locale', default='pl')
    ap.add_argument('--preview', help='katalog na powiększone podglądy przed/po')
    args = ap.parse_args()
    ctx = Ctx(args.source, args.locale)
    results = {}
    if not (ctx.manual('choix.choose_player') or ctx.manual('choix.press_fire')):
        results['CHOIX.SQZ'] = make_choix(ctx)
    if not (ctx.manual('inter.chemicals') or ctx.manual('inter.store')):
        results['INTER.SQZ'] = make_inter(ctx)
    if not ctx.manual('insert.insert_disk'):
        results['INSERT.SQZ'] = make_insert(ctx)
    (c1, c2) = make_mag(ctx)
    results['MAG.CK1'] = c1
    results['MAG.CK2'] = c2
    if not ctx.manual('ville.plaque_role'):
        results['VILLE.CK1'] = make_ville(ctx)
    for name, (arr, pal) in results.items():
        save_png(os.path.join(ctx.out, name + '.png'), arr, pal)
    _, mag_pal = load_ilbm(ctx, 'MAG.CK1')
    sprites = make_sprites(ctx, mag_pal)
    sdir = os.path.join(ctx.out, 'SPRITE.SQV')
    os.makedirs(sdir, exist_ok=True)
    for idx, (w, h, arr) in sprites.items():
        sid = {127: 'sprite.game_over', 134: 'sprite.one_up'}[idx]
        if ctx.manual(sid):
            continue
        save_png(os.path.join(sdir, 'frame_%03d.png' % idx), arr, mag_pal)
    if args.preview:
        os.makedirs(args.preview, exist_ok=True)
        for name, (arr, pal) in results.items():
            orig, _ = load_ilbm(ctx, name)
            both = np.concatenate([orig[:200], np.full((4, orig.shape[1]), 0, np.uint8), arr[:200]], axis=0)
            img = Image.fromarray(both, 'P')
            img.putpalette([c for rgb in pal for c in rgb] + [0] * (768 - 3 * len(pal)))
            img.convert('RGB').resize((both.shape[1] * 3, both.shape[0] * 3), Image.NEAREST).save(
                os.path.join(args.preview, name + '.png'))
    print('\n'.join(ctx.log))
    print('Zapisano grafiki do %s' % ctx.out)


if __name__ == '__main__':
    main()

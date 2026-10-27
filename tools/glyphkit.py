"""Narzędzia do tworzenia polskich liter w stylu oryginalnych napisów graficznych.

Dwa mechanizmy:
  * fonty bitmapowe w formacie tekstowym (JSON, jeden znak = jeden kolor),
    używane dla małych napisów (pasek wyboru postaci, wyskakujące napisy),
  * synteza stylu "przez analogię" dla dużych, ręcznie cieniowanych napisów:
    kształt litery opisuje maska binarna, a kolor każdego piksela jest
    kopiowany z piksela oryginalnego napisu o najbardziej podobnym otoczeniu
    maski. Dzięki temu nowe litery (np. W, Ł, Ó, Ż) dziedziczą obrys,
    cieniowanie i fakturę oryginału.
"""
from collections import deque

import numpy as np


def fill_holes(nonzero):
    """Maska = piksele niezerowe + zamknięte dziury (czarne linie wewnątrz liter)."""
    H, W = nonzero.shape
    outside = np.zeros_like(nonzero)
    q = deque()
    for x in range(W):
        q.append((0, x))
        q.append((H - 1, x))
    for y in range(H):
        q.append((y, 0))
        q.append((y, W - 1))
    while q:
        y, x = q.popleft()
        if 0 <= y < H and 0 <= x < W and not outside[y, x] and not nonzero[y, x]:
            outside[y, x] = True
            q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    return ~outside


def _windows(mask, r):
    """Zwraca tablicę (H, W, nbytes) spakowanych okien (2r+1)^2 maski."""
    H, W = mask.shape
    p = np.pad(mask, r, constant_values=False)
    feats = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            feats.append(p[r + dy:r + dy + H, r + dx:r + dx + W])
    f = np.stack(feats, axis=-1).astype(np.uint8)
    return np.packbits(f, axis=-1)


_POP = np.array([bin(i).count('1') for i in range(256)], dtype=np.uint16)


class StyleSource:
    """Zbiór przykładów: (obraz indeksowany, maska) z oryginalnego napisu."""

    def __init__(self, r=4, weight_center=True):
        self.r = r
        self.feats = []
        self.colors = []
        self.pos = []

    def add(self, img, mask, flip=False):
        if flip:
            img = img[:, ::-1]
            mask = mask[:, ::-1]
        w = _windows(mask, self.r)
        ys, xs = np.nonzero(mask)
        self.feats.append(w[ys, xs])
        self.colors.append(img[ys, xs])

    def finalize(self):
        self.F = np.concatenate(self.feats)
        self.C = np.concatenate(self.colors)

    def render(self, mask, chunk=256):
        """Koloruje maskę stylem źródła. Zwraca tablicę indeksów (0 poza maską)."""
        H, W = mask.shape
        out = np.zeros((H, W), dtype=np.uint8)
        w = _windows(mask, self.r)
        ys, xs = np.nonzero(mask)
        T = w[ys, xs]
        for i in range(0, len(T), chunk):
            t = T[i:i + chunk]
            x = np.bitwise_xor(t[:, None, :], self.F[None, :, :])
            d = _POP[x].sum(axis=-1)
            best = d.argmin(axis=1)
            out[ys[i:i + chunk], xs[i:i + chunk]] = self.C[best]
        return out


# ---------------------------------------------------------------------------
# Fonty bitmapowe w formacie JSON
# ---------------------------------------------------------------------------
TRANSPARENT = 255


def load_font(path):
    import json
    with open(path, encoding='utf-8') as f:
        font = json.load(f)
    h = font['height']
    for ch, rows in font['glyphs'].items():
        if len(rows) != h:
            raise ValueError('glif %r: oczekiwano %d linii, jest %d' % (ch, h, len(rows)))
        if len({len(r) for r in rows}) != 1:
            raise ValueError('glif %r: linie o różnej długości' % ch)
        for r in rows:
            for c in r:
                if c != '.' and c not in font['colors']:
                    raise ValueError('glif %r: nieznany kolor %r' % (ch, c))
    return font


def glyph_array(font, ch):
    rows = font['glyphs'][ch]
    a = np.full((len(rows), len(rows[0])), TRANSPARENT, dtype=np.uint8)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != '.':
                a[y, x] = font['colors'][c]
    return a


def missing_chars(font, text):
    return sorted({c for c in text if c != ' ' and c not in font['glyphs']})


def text_width(font, text, spacing=None, space=None):
    sp = font.get('spacing', 1) if spacing is None else spacing
    sw = font.get('space_width', 4) if space is None else space
    w = 0
    for i, c in enumerate(text):
        w += sw if c == ' ' else len(font['glyphs'][c][0])
        if i < len(text) - 1:
            w += sp
    return w


def render_text(font, text, spacing=None, space=None, kerning=None):
    """Zwraca tablicę (wysokość fontu x szerokość) z TRANSPARENT jako tłem."""
    miss = missing_chars(font, text)
    if miss:
        raise ValueError('brak glifów w foncie %s: %s' % (font.get('name'), ''.join(miss)))
    sp = font.get('spacing', 1) if spacing is None else spacing
    sw = font.get('space_width', 4) if space is None else space
    kerning = kerning or {}
    out = np.full((font['height'], text_width(font, text, sp, sw)), TRANSPARENT, dtype=np.uint8)
    x = 0
    for i, c in enumerate(text):
        if c == ' ':
            x += sw
        else:
            g = glyph_array(font, c)
            m = g != TRANSPARENT
            out[:, x:x + g.shape[1]][m] = g[m]
            x += g.shape[1]
        if i < len(text) - 1:
            x += sp + kerning.get(text[i:i + 2], 0)
    return out


def blit(dst, src, x, y):
    """Nakłada tablicę z przezroczystością na obraz indeksowany."""
    h, w = src.shape
    region = dst[y:y + h, x:x + w]
    m = src[:region.shape[0], :region.shape[1]] != TRANSPARENT
    region[m] = src[:region.shape[0], :region.shape[1]][m]


# ---------------------------------------------------------------------------
# Maski z fontów wektorowych (tylko przy tworzeniu grafik; wynik zapisywany do PNG)
# ---------------------------------------------------------------------------

def render_mask_ttf(text, font_path, font_index, cap_height, x_scale, size=240,
                    gap=0.04, space=0.30, ref_chars='HKDI', thr=110, stroke=0, fit_width=None):
    """Renderuje maskę tekstu krojem TTF.

    cap_height - wysokość wersalików w pikselach docelowych,
    x_scale    - dodatkowe ściśnięcie poziome (kondensacja),
    Zwraca (maska, wiersz_bazowy_wersalików, lista zakresów x liter)."""
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(font_path, size, index=font_index)
    ref = Image.new('L', (size * 4, size * 3))
    ImageDraw.Draw(ref).text((size, size), ref_chars, font=f, fill=255)
    _, cap_top, _, cap_bot = ref.getbbox()
    glyphs = []
    top = cap_top
    bot = cap_bot
    for ch in text:
        if ch == ' ':
            glyphs.append(None)
            continue
        im = Image.new('L', (size * 3, size * 3))
        ImageDraw.Draw(im).text((size, size), ch, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        bb = im.getbbox()
        glyphs.append((im, bb))
        top = min(top, bb[1])
        bot = max(bot, bb[3])
    cap_top -= stroke
    cap_bot += stroke
    s = cap_height / float(cap_bot - cap_top)
    sx = s * x_scale
    gap_px = gap * (cap_bot - cap_top)
    space_px = space * (cap_bot - cap_top)
    # składamy w wysokiej rozdzielczości, potem skalujemy jednym krokiem
    widths = [(g[1][2] - g[1][0]) if g else space_px for g in glyphs]
    total = sum(widths) + gap_px * (len(glyphs) - 1)
    big = Image.new('L', (int(total) + 2, bot - top))
    x = 0.0
    spans = []
    for g, w in zip(glyphs, widths):
        if g is not None:
            im, bb = g
            big.paste(im.crop((bb[0], top, bb[2], bot)), (int(round(x)), 0))
            spans.append((x, x + w))
        x += w + gap_px
    if fit_width:
        sx = fit_width / float(big.width)
    W = max(1, int(round(big.width * sx)))
    H = max(1, int(round(big.height * s)))
    small = np.array(big.resize((W, H), Image.LANCZOS)) > thr
    baseline_row = int(round((cap_bot - top) * s))
    spans = [(int(round(a * sx)), int(round(b * sx))) for a, b in spans]
    return small, baseline_row, spans


def chebyshev_depth(mask):
    """Odległość (w metryce Czebyszewa) każdego piksela maski od jej brzegu."""
    H, W = mask.shape
    d = np.zeros((H, W), int)
    cur = ~mask
    k = 0
    while True:
        k += 1
        pad = np.pad(cur, 1, constant_values=True)
        t = np.zeros_like(mask)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                t |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
        new = mask & t & (d == 0)
        if not new.any():
            return d
        d[new] = k
        cur = cur | new


def manhattan_distance(points, shape):
    H, W = shape
    d = np.full((H, W), 999, int)
    yy, xx = np.mgrid[0:H, 0:W]
    for y, x in zip(*np.nonzero(points)):
        d = np.minimum(d, abs(yy - y) + abs(xx - x))
    return d


def dilate(mask, r=1, cross=False):
    o = mask.copy()
    H, W = mask.shape
    for _ in range(r):
        p = np.pad(o, 1)
        n = o.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if cross and dx and dy:
                    continue
                n |= p[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
        o = n
    return o


def label(mask):
    """Etykietowanie składowych 8-spójnych. Zwraca (etykiety, liczba)."""
    H, W = mask.shape
    lab = np.zeros((H, W), int)
    n = 0
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not lab[y, x]:
                n += 1
                q = deque([(y, x)])
                lab[y, x] = n
                while q:
                    cy, cx = q.popleft()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = cy + dy, cx + dx
                            if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not lab[yy, xx]:
                                lab[yy, xx] = n
                                q.append((yy, xx))
    return lab, n

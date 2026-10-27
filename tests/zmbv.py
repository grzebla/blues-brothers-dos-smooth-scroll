"""Minimalny dekoder nagrań AVI/ZMBV z DOSBox-X (tylko 8 bpp).

Dekoduje dokładne klatki indeksowane wraz z paletą VGA, dzięki czemu testy
mogą porównywać piksele wyświetlane przez grę z oczekiwanymi grafikami.
"""
import struct
import zlib

import numpy as np


def _chunks(data, pos, end):
    while pos + 8 <= end:
        tag = data[pos:pos + 4]
        size = struct.unpack_from('<I', data, pos + 4)[0]
        yield tag, pos + 8, size
        pos += 8 + size + (size & 1)


def avi_info_and_frames(path):
    data = open(path, 'rb').read()
    if data[:4] != b'RIFF' or data[8:12] != b'AVI ':
        raise ValueError('to nie jest plik AVI')
    width = height = None
    usec = None
    frames = []
    stack = [(12, len(data))]
    while stack:
        pos, end = stack.pop(0)
        for tag, p, size in _chunks(data, pos, end):
            if tag == b'LIST':
                stack.append((p + 4, p + size))
            elif tag == b'avih':
                usec, = struct.unpack_from('<I', data, p)
                width, height = struct.unpack_from('<II', data, p + 32)
            elif tag in (b'00dc', b'00db'):
                frames.append(data[p:p + size])
    return {'width': width, 'height': height, 'fps': 1e6 / usec if usec else None}, frames


class ZMBVDecoder:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.frame = np.zeros((h, w), np.uint8)
        self.palette = np.zeros((256, 3), np.uint8)
        self.z = None
        self.bw = self.bh = 16

    def decode(self, chunk):
        if not chunk:
            return self.frame
        flags = chunk[0]
        pos = 1
        if flags & 1:  # klatka kluczowa
            hi, lo, comp, fmt, bw, bh = struct.unpack_from('<6B', chunk, pos)
            pos += 6
            if fmt not in (4, 8):
                raise ValueError('obsługiwane formaty: 8 bpp i 32 bpp (jest %d)' % fmt)
            self.bpp = 1 if fmt == 4 else 4
            self.bw, self.bh = bw, bh
            self.z = zlib.decompressobj() if comp == 1 else None
            raw = self.z.decompress(chunk[pos:]) if self.z else chunk[pos:]
            p = 0
            if self.bpp == 1:
                self.palette = np.frombuffer(raw[:768], np.uint8).reshape(256, 3).copy()
                p = 768
            n = self.w * self.h * self.bpp
            self.frame = np.frombuffer(raw[p:p + n], np.uint8).reshape(self.h, self.w * self.bpp).copy()
            return self.frame
        raw = self.z.decompress(chunk[pos:]) if self.z else chunk[pos:]
        p = 0
        if flags & 2 and self.bpp == 1:
            self.palette ^= np.frombuffer(raw[:768], np.uint8).reshape(256, 3)
            p = 768
        bx = (self.w + self.bw - 1) // self.bw
        by = (self.h + self.bh - 1) // self.bh
        nb = bx * by
        vecs = raw[p:p + nb * 2]
        p += (nb * 2 + 3) & ~3
        old = self.frame
        new = np.empty_like(old)
        for b in range(nb):
            vx = struct.unpack_from('b', vecs, b * 2)[0]
            vy = struct.unpack_from('b', vecs, b * 2 + 1)[0]
            xor = vx & 1
            vx >>= 1
            vy >>= 1
            k = self.bpp
            x0 = (b % bx) * self.bw * k
            y0 = (b // bx) * self.bh
            w = min(self.bw * k, self.w * k - x0)
            h = min(self.bh, self.h - y0)
            vx *= k
            sx, sy0 = x0 + vx, y0 + vy
            if 0 <= sx and sx + w <= self.w * k and 0 <= sy0 and sy0 + h <= self.h:
                blk = old[sy0:sy0 + h, sx:sx + w].copy()
                if xor:
                    blk ^= np.frombuffer(raw[p:p + w * h], np.uint8).reshape(h, w)
                    p += w * h
                new[y0:y0 + h, x0:x0 + w] = blk
                continue
            blk = np.zeros((h, w), np.uint8)
            for yy in range(h):
                sy = y0 + yy + vy
                for_x = np.arange(x0 + vx, x0 + vx + w)
                if 0 <= sy < self.h:
                    ok = (for_x >= 0) & (for_x < self.w * k)
                    blk[yy, ok] = old[sy, for_x[ok]]
            if xor:
                d = np.frombuffer(raw[p:p + w * h], np.uint8).reshape(h, w)
                blk ^= d
                p += w * h
            new[y0:y0 + h, x0:x0 + w] = blk
        self.frame = new
        return self.frame


def decode_avi(path, every=1):
    """Generator (numer_klatki, czas_s, piksele, paleta)."""
    info, chunks = avi_info_and_frames(path)
    dec = ZMBVDecoder(info['width'], info['height'])
    fps = info['fps'] or 70.0
    for i, c in enumerate(chunks):
        f = dec.decode(c)
        if i % every == 0:
            yield i, i / fps, f.copy(), dec.palette.copy()


def to_rgb(frame, palette):
    """Zamienia klatkę na tablicę RGB (H, W, 3).

    Dla 32 bpp kolejność bajtów zależy od powierzchni SDL (na macOS: X,R,G,B,
    w Windows/Linux zwykle B,G,R,X) - pusty kanał wykrywamy automatycznie."""
    if palette is not None and palette.any():
        return palette[frame]
    h, w4 = frame.shape
    px = frame.reshape(h, w4 // 4, 4)
    if not px[:, :, 0].any() and px[:, :, 3].any():
        return px[:, :, 1:4].copy()
    return px[:, :, 2::-1].copy()

"""Biblioteka formatów plików The Blues Brothers (Titus, 1991, MS-DOS).

Implementacja własna, napisana na podstawie analizy plików oraz opisu formatów
z projektu cyxx/blues i ModdingWiki (bez kopiowania kodu).

Obsługiwane formaty:
  * kontener kompresji Titus (SQZ/SQV/SQL/CK1/CK2) - statyczny Huffman,
  * IFF ILBM (ekrany 320x200 i arkusze kafli CK1/CK2), kompresja ByteRun1,
  * arkusze sprite'ów SQV (planarne 4bpp),
  * plik SQL (mapa poziomu, surowe bajty po dekompresji).
"""
import heapq
import struct

# ---------------------------------------------------------------------------
# Kompresja Titus: 6-bajtowy nagłówek, słownik (drzewo Huffmana), strumień bitów
#
#   +0  u16 LE  starsze 16 bitów rozmiaru po dekompresji
#   +2  u16 LE  młodsze 16 bitów rozmiaru po dekompresji
#   +4  u16 LE  długość słownika w bajtach (dict_len)
#   +6  dict_len bajtów: węzły u16 LE. Para węzłów (p, p+2) opisuje gałęzie 0/1.
#       Wartość z ustawionym bitem 15 to liść (bajt w młodszych 8 bitach),
#       w przeciwnym razie to offset (parzysty) kolejnej pary w słowniku.
#   dalej: słowa u16 BE, bity czytane od najstarszego.
# ---------------------------------------------------------------------------


class FormatError(Exception):
    pass


def is_compressed(data):
    if len(data) < 8:
        return False
    usize = (struct.unpack_from('<H', data, 0)[0] << 16) | struct.unpack_from('<H', data, 2)[0]
    dlen = struct.unpack_from('<H', data, 4)[0]
    return 0 < usize < 0x100000 and 4 <= dlen <= 0x400 and dlen % 4 == 0 and 6 + dlen < len(data)


def unpack(data):
    if len(data) < 6:
        raise FormatError('plik za krótki')
    usize = (struct.unpack_from('<H', data, 0)[0] << 16) | struct.unpack_from('<H', data, 2)[0]
    dlen = struct.unpack_from('<H', data, 4)[0]
    if dlen < 4 or dlen % 2 or 6 + dlen > len(data):
        raise FormatError('niepoprawna długość słownika %d' % dlen)
    dic = struct.unpack_from('<%dH' % (dlen // 2), data, 6)
    pos = 6 + dlen
    out = bytearray()
    node = 0
    bits = 0
    nbits = 0
    n = len(data)
    while len(out) < usize:
        if nbits == 0:
            if pos >= n:
                raise FormatError('koniec danych po %d/%d bajtach' % (len(out), usize))
            hi = data[pos]
            lo = data[pos + 1] if pos + 1 < n else 0  # oryginał czyta 1 bajt na końcu pliku
            bits = (hi << 8) | lo
            pos += 2
            nbits = 16
        if bits & 0x8000:
            node += 2
        bits = (bits << 1) & 0xFFFF
        nbits -= 1
        if node // 2 >= len(dic):
            raise FormatError('odwołanie poza słownik')
        node = dic[node // 2]
        if node & 0x8000:
            out.append(node & 0xFF)
            node = 0
    return bytes(out)


def _huffman_codes(data):
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    syms = [s for s in range(256) if freq[s]]
    if not syms:
        syms = [0]
    if len(syms) == 1:
        # drzewo musi mieć dwa liście
        syms.append((syms[0] + 1) & 0xFF)
    heap = []
    cnt = 0
    for s in syms:
        heap.append((freq[s], cnt, ('leaf', s)))
        cnt += 1
    heapq.heapify(heap)
    while len(heap) > 1:
        f1, _, a = heapq.heappop(heap)
        f2, _, b = heapq.heappop(heap)
        heapq.heappush(heap, (f1 + f2, cnt, ('node', a, b)))
        cnt += 1
    return heap[0][2]


def _tree_depth(t):
    if t[0] == 'leaf':
        return 0
    return 1 + max(_tree_depth(t[1]), _tree_depth(t[2]))


def pack(data):
    """Kompresuje dane do formatu Titus (deterministycznie)."""
    tree = _huffman_codes(data)
    # serializacja w kolejności BFS: para dzieci korzenia pod offsetem 0
    dic = []
    codes = {}
    queue = [(tree, '')]
    # każdy element kolejki to węzeł wewnętrzny, którego dzieci trzeba zapisać
    slots = []
    while queue:
        t, prefix = queue.pop(0)
        base = len(dic)
        dic.extend([0, 0])
        for i, child in enumerate((t[1], t[2])):
            code = prefix + str(i)
            if child[0] == 'leaf':
                dic[base + i] = 0x8000 | child[1]
                codes[child[1]] = code
            else:
                slots.append((base + i, child, code))
                queue.append((child, code))
        # przypisz offsety dzieci, gdy ich pary już powstaną
    # druga faza: offsety wskazują na pary w kolejności dodawania do kolejki
    # (pary są dopisywane w tej samej kolejności, w jakiej trafiały do kolejki)
    pair_index = 1
    for slot, child, code in slots:
        dic[slot] = pair_index * 4
        pair_index += 1
    if len(dic) * 2 > 0x400:
        raise FormatError('słownik za duży')
    bitstr = ''.join(codes[b] for b in data)
    # Dekoder w 1.EXE dekoduje strumień aż do końca pliku (ignoruje rozmiar
    # z nagłówka), więc bity dopełnienia nie mogą tworzyć pełnego kodu.
    # Dopełniamy prefiksem najdłuższego kodu - wtedy żaden symbol nie powstaje.
    pad = (16 - len(bitstr) % 16) % 16
    if pad:
        longest = max(codes.values(), key=len)
        filler = longest
        while len(filler) <= pad:
            filler += longest  # skrajny przypadek: krótkie kody (1 nadmiarowy symbol)
        bitstr += filler[:pad]
    stream = bytearray()
    for i in range(0, len(bitstr), 16):
        stream += struct.pack('>H', int(bitstr[i:i + 16], 2))
    usize = len(data)
    hdr = struct.pack('<HHH', usize >> 16, usize & 0xFFFF, len(dic) * 2)
    return hdr + struct.pack('<%dH' % len(dic), *dic) + bytes(stream)


def dos_overrun(data):
    """Liczba bajtów, które dekoder z 1.EXE zapisze ponad rozmiar z nagłówka.

    Emuluje pętlę 0A47:054E - dekodowanie trwa do końca pliku."""
    usize = (struct.unpack_from('<H', data, 0)[0] << 16) | struct.unpack_from('<H', data, 2)[0]
    dlen = struct.unpack_from('<H', data, 4)[0]
    dic = struct.unpack_from('<%dH' % (dlen // 2), data, 6)
    pos = 6 + dlen
    out = 0
    node = 0
    while pos < len(data):
        w = (data[pos] << 8) | (data[pos + 1] if pos + 1 < len(data) else 0)
        pos += 2
        for _ in range(16):
            if w & 0x8000:
                node += 2
            w = (w << 1) & 0xFFFF
            node = dic[node // 2]
            if node & 0x8000:
                out += 1
                node = 0
    return out - usize


# ---------------------------------------------------------------------------
# IFF ILBM
# ---------------------------------------------------------------------------


def _byterun1_decode(src, pos, end, want):
    # zgodnie z 1.EXE: 0x80 NIE jest pomijane, oznacza przebieg 129 bajtów
    out = bytearray()
    while len(out) < want and pos < end:
        c = src[pos]
        pos += 1
        if c < 128:
            out += src[pos:pos + c + 1]
            pos += c + 1
        else:
            out += bytes([src[pos]]) * (257 - c)
            pos += 1
    return bytes(out[:want]), pos


def _byterun1_encode_row(row):
    out = bytearray()
    i = 0
    n = len(row)
    lit = bytearray()

    def flush():
        while lit:
            chunk = lit[:128]
            out.append(len(chunk) - 1)
            out.extend(chunk)
            del lit[:128]

    while i < n:
        j = i
        while j < n and row[j] == row[i] and j - i < 128:
            j += 1
        run = j - i
        if run >= 3 or (run == 2 and not lit):
            flush()
            out.append(257 - run)
            out.append(row[i])
            i = j
        else:
            lit.append(row[i])
            i += 1
            if len(lit) == 128:
                flush()
    flush()
    return bytes(out)


class ILBM:
    def __init__(self):
        self.width = 320
        self.height = 200
        self.planes = 4
        self.bmhd = None  # surowe 20 bajtów nagłówka
        self.palette = []  # lista (r,g,b) 8-bitowych
        self.pixels = None  # bytearray w*h indeksów
        self.chunks = []  # [(tag, data)] w oryginalnej kolejności; BODY jako None
        self.compression = 1

    @classmethod
    def parse(cls, data):
        if data[:4] != b'FORM' or data[8:12] != b'ILBM':
            raise FormatError('to nie jest IFF ILBM')
        self = cls()
        pos = 12
        end = min(len(data), 8 + struct.unpack_from('>I', data, 4)[0])
        body = None
        while pos + 8 <= end:
            tag = data[pos:pos + 4]
            ln = struct.unpack_from('>I', data, pos + 4)[0]
            chunk = data[pos + 8:pos + 8 + ln]
            if tag == b'BMHD':
                self.bmhd = chunk
                (self.width, self.height, _, _, self.planes, _, self.compression) = struct.unpack_from('>HHhhBBB', chunk)
                self.chunks.append((tag, chunk))
            elif tag == b'CMAP':
                self.palette = [tuple(chunk[i:i + 3]) for i in range(0, len(chunk) - 2, 3)]
                self.chunks.append((tag, chunk))
            elif tag == b'BODY':
                body = chunk
                self.chunks.append((tag, None))
            else:
                self.chunks.append((tag, chunk))
            pos += 8 + ln + (ln & 1)
        if body is None:
            raise FormatError('brak BODY')
        rowbytes = ((self.width + 15) // 16) * 2
        linebytes = rowbytes * self.planes
        pix = bytearray(self.width * self.height)
        if self.compression == 1:
            # 1.EXE (003A:11CD) dekoduje BODY jako ciągły strumień, przebiegi
            # mogą przekraczać granice płaszczyzn i linii
            stream, _ = _byterun1_decode(body, 0, len(body), linebytes * self.height)
        else:
            stream = body
        stream = stream.ljust(linebytes * self.height, b'\0')
        for y in range(self.height):
            line = stream[y * linebytes:(y + 1) * linebytes]
            rows = [line[p * rowbytes:(p + 1) * rowbytes] for p in range(self.planes)]
            base = y * self.width
            for x in range(self.width):
                m = 0x80 >> (x & 7)
                c = 0
                for p in range(self.planes):
                    if len(rows[p]) > x >> 3 and rows[p][x >> 3] & m:
                        c |= 1 << p
                pix[base + x] = c
        self.pixels = pix
        return self

    def encode(self):
        rowbytes = ((self.width + 15) // 16) * 2
        body = bytearray()
        for y in range(self.height):
            row = self.pixels[y * self.width:(y + 1) * self.width]
            for p in range(self.planes):
                pr = bytearray(rowbytes)
                m = 1 << p
                for x in range(self.width):
                    if row[x] & m:
                        pr[x >> 3] |= 0x80 >> (x & 7)
                if self.compression == 1:
                    body += _byterun1_encode_row(pr)
                else:
                    body += pr
        out = bytearray(b'ILBM')
        for tag, chunk in self.chunks:
            if tag == b'BODY':
                chunk = bytes(body)
            elif tag == b'CMAP':
                chunk = bytes(c for rgb in self.palette for c in rgb)
            out += tag + struct.pack('>I', len(chunk)) + chunk
            if len(chunk) & 1:
                out += b'\0'
        return b'FORM' + struct.pack('>I', len(out)) + bytes(out)


# ---------------------------------------------------------------------------
# Sprite'y SQV: u16 liczba, u16 ?, u16 ?, potem dla każdej klatki
#   u16 h, u16 w (LE w wersji DOS), dane planarne: 4 płaszczyzny po (w/8)*h
# (format zweryfikowany na SPRITE.SQV i ENEMI*.SQV)
# ---------------------------------------------------------------------------


def parse_sqv(data, depth=4):
    count = struct.unpack_from('<H', data, 0)[0]
    frames = []
    pos = 2
    for i in range(count):
        h, w = struct.unpack_from('<HH', data, pos)
        size = h * w * depth // 8
        frames.append({'w': w, 'h': h, 'offset': pos + 4, 'data': data[pos + 4:pos + 4 + size]})
        pos += 4 + size
    return frames, data[pos:]


def decode_planar(src, w, h, depth=4):
    """Dekoduje bitmapę planarną (płaszczyzny jedna po drugiej)."""
    pitch = w // 8
    plane = pitch * h
    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            m = 0x80 >> (x & 7)
            c = 0
            for b in range(depth):
                if src[b * plane + y * pitch + (x >> 3)] & m:
                    c |= 1 << (3 - b)
            out[y * w + x] = c
    return out


def encode_planar(pix, w, h, depth=4):
    pitch = w // 8
    plane = pitch * h
    out = bytearray(plane * depth)
    for y in range(h):
        for x in range(w):
            c = pix[y * w + x]
            for b in range(depth):
                if c & (1 << (3 - b)):
                    out[b * plane + y * pitch + (x >> 3)] |= 0x80 >> (x & 7)
    return bytes(out)


def build_sqv(frames, trailing=b''):
    """frames: lista (w, h, dane_planarne). Składa nieskompresowany plik SQV."""
    out = bytearray(struct.pack('<H', len(frames)))
    for w, h, data in frames:
        if w % 16:
            raise FormatError('szerokość klatki musi być wielokrotnością 16 (jest %d)' % w)
        if len(data) != w * h // 2:
            raise FormatError('zły rozmiar danych klatki')
        out += struct.pack('<HH', h, w) + data
    return bytes(out) + trailing

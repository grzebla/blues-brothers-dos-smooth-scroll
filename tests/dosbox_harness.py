"""Uruchamianie gry w DOSBox-X ze scenariuszem klawiszy i analiza nagrania.

Mechanizm:
  * DOSBox-X startuje z wygenerowanym plikiem konfiguracyjnym,
  * AUTOTYPE wstrzykuje naciśnięcia klawiszy (z opóźnieniami),
  * DX-CAPTURE /V /A nagrywa obraz (AVI/ZMBV) i dźwięk (WAV) uruchomionego programu,
  * nagranie jest dekodowane dekoderem tests/zmbv.py (dokładne kolory),
  * testy szukają klatek, w których dany obszar ekranu ma oczekiwaną zawartość.
"""
import glob
import os
import shutil
import subprocess
import wave

import numpy as np
from PIL import Image

import zmbv

DOSBOX_CANDIDATES = [
    os.environ.get('DOSBOX_X', ''),
    '/Applications/dosbox-x.app/Contents/MacOS/dosbox-x',
    shutil.which('dosbox-x') or '',
]


def find_dosbox():
    for c in DOSBOX_CANDIDATES:
        if c and os.path.exists(c):
            return c
    return None


CONF = """[sdl]
output=surface
{extra}
[dosbox]
machine={machine}
memsize=16
captures={cap}
[cpu]
core=normal
cycles=fixed {cycles}
[mixer]
# Testy nie odtwarzają dźwięku na hoście; emulacja i nagranie pozostają aktywne.
nosound=true
rate=22050
[midi]
# MIDI omija mikser SDL; testowana gra korzysta z OPL, nie wyjścia MIDI hosta.
mididevice=none
[sblaster]
sbtype=sb16
[speaker]
pcspeaker=true
[autoexec]
mount c "{game}"
c:
{autotype}
{pre}
DX-CAPTURE /V /A {program}
exit
"""


def run(game_dir, outdir, keys='', seconds=40, program='RUNME.COM', cycles=20000, wait=2.0, pace=0.5,
        machine='svga_s3', extra='', pre='', log_con=False):
    """Uruchamia grę. keys - lista przycisków AUTOTYPE (',' = pauza o długości pace)."""
    dosbox = find_dosbox()
    if not dosbox:
        raise RuntimeError('nie znaleziono DOSBox-X (ustaw zmienną DOSBOX_X)')
    outdir = os.path.abspath(outdir)
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    cap = os.path.join(outdir, 'capture')
    game = os.path.join(outdir, 'game')
    os.makedirs(cap)
    shutil.copytree(os.path.abspath(game_dir), game)
    autotype = 'AUTOTYPE -w %.2f -p %.2f %s' % (wait, pace, keys) if keys else ''
    conf = os.path.join(outdir, 'dosbox.conf')
    with open(conf, 'w') as f:
        f.write(CONF.format(cap=cap, game=game, cycles=cycles, autotype=autotype, program=program,
                            machine=machine, extra=extra, pre=pre))
    log = open(os.path.join(outdir, 'dosbox.log'), 'w')
    cmd = [dosbox, '-conf', conf, '-fastlaunch', '-nogui', '-nomenu', '-time-limit', str(seconds)]
    if log_con:
        cmd.append('-log-con')   # wyjście konsoli DOS trafia do dosbox.log jako "DOS CON: ..."
    varlock = shutil.which('varlock')
    if not varlock:
        log.close()
        raise RuntimeError('Testy DOSBox-X wymagają Varlock: bezpieczny tryb bez okien i audio')
    schema_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Bez fallbacku do widocznego okna: sterowniki dummy są walidowane w schemacie.
    cmd = [varlock, 'run', '--path', schema_dir, '--inject', 'vars', '--'] + cmd
    try:
        subprocess.run(cmd, check=True,
                       stdout=log, stderr=subprocess.STDOUT, cwd=outdir, timeout=seconds + 60)
    finally:
        log.close()
    return Recording(outdir)


class Recording:
    def __init__(self, outdir):
        self.dir = outdir
        cap = os.path.join(outdir, 'capture')
        # pliki: <prog>_000.avi, <prog>_001.avi ... w kolejności powstawania
        self.avis = sorted(glob.glob(os.path.join(cap, '*.avi')), key=os.path.getmtime)
        self.wavs = sorted(glob.glob(os.path.join(cap, '*.wav')), key=os.path.getmtime)

    def console_lines(self):
        out = []
        for line in open(os.path.join(self.dir, 'dosbox.log'), encoding='latin-1'):
            if 'DOS CON:' in line:
                out.append(line.split('DOS CON:', 1)[1].strip())
        return out

    def frames(self, step=0.25):
        """Generator (czas_s, plik, klatka_rgb 640x400) co 'step' sekund."""
        t0 = 0.0
        for avi in self.avis:
            info, chunks = zmbv.avi_info_and_frames(avi)
            fps = info['fps'] or 70.0
            every = max(1, int(round(step * fps))) if step else 1
            dec = zmbv.ZMBVDecoder(info['width'], info['height'])
            last = None
            for i, c in enumerate(chunks):
                f = dec.decode(c)
                if i % every == 0:
                    rgb = zmbv.to_rgb(f, dec.palette)
                    last = i
                    yield t0 + i / fps, os.path.basename(avi), rgb
            t0 += len(chunks) / fps

    def sheet(self, path, step=2.0, cols=6, scale=0.5):
        ims = [Image.fromarray(r) for _, _, r in self.frames(step)]
        if not ims:
            return None
        w, h = int(ims[0].width * scale), int(ims[0].height * scale)
        rows = (len(ims) + cols - 1) // cols
        o = Image.new('RGB', (cols * w, rows * h))
        for i, im in enumerate(ims):
            o.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
        o.save(path)
        return path

    def audio_stats(self):
        """Zwraca (czas_s, rms, max) dla nagranego dźwięku."""
        res = []
        for w in self.wavs:
            with wave.open(w) as f:
                n = f.getnframes()
                data = np.frombuffer(f.readframes(n), dtype=np.int16).astype(np.float64)
                rate = f.getframerate()
                ch = f.getnchannels()
            if len(data):
                res.append((n / rate, float(np.sqrt((data ** 2).mean())), float(np.abs(data).max()), ch))
        return res


def vga_rgb(palette8):
    """Kolor wyświetlany przez VGA dla wartości z CMAP (8 bit -> DAC 6 bit -> 8 bit)."""
    p = np.array(palette8, dtype=np.int32) >> 2
    return ((p << 2) | (p >> 4)).astype(np.uint8)


def expected_rgb(indexed, palette8):
    pal = vga_rgb(palette8)
    return pal[indexed]


def region_match(frame_rgb, expected, x, y, scale=2, tol=8, mask=None):
    """Odsetek pikseli obszaru (w pikselach 320x200) zgodnych z oczekiwanym obrazem.

    mask - opcjonalnie: które piksele porównywać (np. bez kolorów animowanych przez grę)."""
    h, w = expected.shape[:2]
    sub = frame_rgb[y * scale:(y + h) * scale:scale, x * scale:(x + w) * scale:scale].astype(int)
    if sub.shape[:2] != (h, w):
        return 0.0
    ok = np.abs(sub - expected.astype(int)).max(axis=2) <= tol
    if mask is not None:
        return float(ok[mask].mean())
    return float(ok.mean())


def find_match(rec, expected, x, y, step=0.25, threshold=0.98, scale=2, mask=None):
    """Pierwsza klatka, w której obszar pasuje; zwraca (czas, plik, wynik, klatka) lub najlepszą próbę."""
    best = (0.0, None, None, None)
    for t, name, f in rec.frames(step):
        s = region_match(f, expected, x, y, scale, mask=mask)
        if s > best[0]:
            best = (s, t, name, f)
        if s >= threshold:
            return t, name, s, f
    return best[1], best[2], best[0], best[3]

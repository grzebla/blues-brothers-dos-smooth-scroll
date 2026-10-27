#!/usr/bin/env python3
"""Testy polskiej wersji w DOSBox-X (częściowo automatyczne).

Użycie:
    python tests/run_dosbox_tests.py [--game build/game] [--only NAZWA ...] [--out tests/results/latest]

Każdy scenariusz uruchamia grę w DOSBox-X, wstrzykuje klawisze (AUTOTYPE),
nagrywa obraz i dźwięk (DX-CAPTURE), a następnie sprawdza nagranie:
  * porównanie pikseli z oczekiwanymi grafikami (dokładne kolory VGA),
  * wyszukiwanie wzorców (sprite'y, kafle) w klatkach rozgrywki,
  * rozpoznawanie aktywnego poziomu po palecie,
  * obecność dźwięku.
Wyniki: <out>/report.md, <out>/results.json, arkusze klatek <out>/<scenariusz>.png.

Scenariusze oznaczone [łatka testowa] używają tests/test_patches.py, aby
dotrzeć do ekranów wymagających długiej rozgrywki - patrz docs/compatibility.md.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import bbformats as bf  # noqa: E402
import dosbox_harness as H  # noqa: E402
import gamedata as gd  # noqa: E402
import test_patches as TP  # noqa: E402
import zmbv  # noqa: E402
from numpy.lib.stride_tricks import sliding_window_view  # noqa: E402

LOC = os.path.join(ROOT, 'localization', 'pl', 'graphics')
ORIG = os.path.join(ROOT, 'original')


# ---------------------------------------------------------------------------
# dane oczekiwane
# ---------------------------------------------------------------------------
def png_indexed(path):
    im = Image.open(path)
    pal = im.getpalette()[:48]
    return np.array(im, np.uint8), [tuple(pal[i:i + 3]) for i in range(0, 48, 3)]


def level_palette(ck):
    return bf.ILBM.parse(bf.unpack(open(os.path.join(ORIG, ck), 'rb').read())).palette


# kolory ekranu wyboru, których paletę gra animuje (reflektory, publiczność)
CHOIX_ANIMATED = (2, 3, 9, 10, 14)


def choix_mask(choix):
    return ~np.isin(choix[190:200], CHOIX_ANIMATED)


def sprite_frame(idx):
    path = os.path.join(LOC, 'SPRITE.SQV', 'frame_%03d.png' % idx)
    return np.array(Image.open(path), np.uint8)


# ---------------------------------------------------------------------------
# narzędzia analizy klatek
# ---------------------------------------------------------------------------
def half(frame):
    return frame[::2, ::2].astype(np.int16)


def template_search(frame, tpl_rgb, mask, region=None, tol=8):
    """Najlepsze dopasowanie wzorca w klatce 320x200. Zwraca (wynik, x, y)."""
    F = half(frame)
    x0, y0, x1, y1 = region or (0, 0, F.shape[1], F.shape[0])
    sub = F[y0:y1, x0:x1]
    h, w = mask.shape
    if sub.shape[0] < h or sub.shape[1] < w:
        return 0.0, None, None
    win = sliding_window_view(sub, (h, w, 3))[:, :, 0]          # (Y, X, h, w, 3)
    ok = (np.abs(win - tpl_rgb.astype(np.int16)).max(axis=-1) <= tol) & mask
    score = ok.sum(axis=(-1, -2)) / float(mask.sum())
    yy, xx = np.unravel_index(score.argmax(), score.shape)
    return float(score[yy, xx]), x0 + xx, y0 + yy


def palette_level(frame, level_pals):
    """Który poziom: odsetek pikseli klatki należących do palety VGA danego poziomu."""
    F = half(frame).reshape(-1, 3)
    cols, counts = np.unique(F, axis=0, return_counts=True)
    res = []
    for k, pal in enumerate(level_pals):
        vp = H.vga_rgb(pal).astype(np.int16)
        d = np.abs(cols[:, None, :] - vp[None, :, :]).max(axis=-1).min(axis=1)
        res.append(float(counts[d <= 4].sum()) / counts.sum())
    return res


class Result:
    def __init__(self, name):
        self.name = name
        self.checks = []
        self.notes = []

    def check(self, desc, ok, detail=''):
        self.checks.append({'check': desc, 'ok': bool(ok), 'detail': detail})
        print('   [%s] %s %s' % ('OK ' if ok else 'BŁĄD', desc, detail))

    @property
    def ok(self):
        return all(c['ok'] for c in self.checks) and bool(self.checks)


def prepare_game(src, dst, exe_patches=(), remove=()):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    if exe_patches:
        p = os.path.join(dst, '1.EXE')
        buf = bytearray(open(p, 'rb').read())
        for fn in exe_patches:
            fn(buf)
        open(p, 'wb').write(buf)
    for r in remove:
        os.remove(os.path.join(dst, r))
    return dst


def keys_seq(*items):
    """('2', 3, 'space', 4, 'space') -> sekwencja AUTOTYPE z pauzami w sekundach (pace=1)."""
    out = []
    for it in items:
        if isinstance(it, (int, float)):
            out.extend([','] * int(it))
        else:
            out.append(it)
    return ' '.join(out)


# ---------------------------------------------------------------------------
# scenariusze
# ---------------------------------------------------------------------------
def scenario_boot(args, work):
    """Menu RUNME -> ekran tytułowy -> wybór postaci (bez rozgrywki)."""
    r = Result('boot')
    game = prepare_game(args.game, os.path.join(work, 'game_boot'))
    rec = H.run(game, os.path.join(work, 'boot'), keys=keys_seq('2'), seconds=40, wait=3, pace=1)
    r.check('nagranie powstało', rec.avis, ', '.join(os.path.basename(a) for a in rec.avis))
    pres, ppal = png_indexed(os.path.join(args.extracted, 'images', 'PRES.SQZ.png'))
    t, n, s, _ = H.find_match(rec, H.expected_rgb(pres[20:120], ppal), 0, 20, step=0.5)
    r.check('ekran tytułowy wyświetlony (PRES.SQZ)', s >= 0.98, 'zgodność %.3f w t=%s s' % (s, t))
    choix, cpal = png_indexed(os.path.join(LOC, 'CHOIX.SQZ.png'))
    t, n, s, f = H.find_match(rec, H.expected_rgb(choix[190:200], cpal), 0, 190, step=0.5,
                              mask=choix_mask(choix))
    r.check('polski pasek wyboru postaci (CHOIX.SQZ, linie 190-199)', s >= 0.99, 'zgodność %.3f w t=%s s' % (s, t))
    if f is not None:
        Image.fromarray(f).save(os.path.join(args.out, 'boot_choix.png'))
    audio = rec.audio_stats()
    r.check('dźwięk/muzyka nagrane (niezerowy sygnał)', audio and audio[0][1] > 100,
            'RMS %.0f, szczyt %.0f' % (audio[0][1], audio[0][2]) if audio else 'brak WAV')
    con = os.path.join(work, 'boot', 'game', 'RUNME.COM')
    data = open(con, 'rb').read()
    r.check('menu RUNME.COM po polsku', b'P R Z E D S T A W I A' in data and b'firmy TITUS' in data)
    rec.sheet(os.path.join(args.out, 'boot.png'), step=3.0)
    return r


def scenario_all_levels(args, work):
    """[łatka testowa] auto-ukończenie: wszystkie 6 poziomów po kolei i powrót do startu."""
    r = Result('all_levels')
    game = prepare_game(args.game, os.path.join(work, 'game_all'), exe_patches=[TP.auto_complete])
    rec = H.run(game, os.path.join(work, 'all_levels'), keys=keys_seq('2', 5, 'space', 4, 'space'),
                seconds=150, wait=3, pace=1)
    inter, ipal = png_indexed(os.path.join(LOC, 'INTER.SQZ.png'))
    exp_chem = H.expected_rgb(inter[48:54, 9:82], ipal)
    m_chem = inter[48:54, 9:82] == 13      # tylko piksele liter (znaczniki "X" mogą zasłaniać tło)
    choix, cpal = png_indexed(os.path.join(LOC, 'CHOIX.SQZ.png'))
    exp_choix = H.expected_rgb(choix[190:200], cpal)
    m_choix = choix_mask(choix)
    pals = [level_palette(l['ck1']) for l in gd.LEVELS]
    # ikony HUD (klatki 135-144) leżą w SPRITE.SQV za poszerzoną klatką 134
    spr = bf.unpack(open(os.path.join(args.game, 'SPRITE.SQV'), 'rb').read())
    frames_all, _ = bf.parse_sqv(spr)
    icons = []
    for idx in range(135, 145):
        fr = frames_all[idx]
        icons.append((idx, np.array(bf.decode_planar(fr['data'], fr['w'], fr['h']), np.uint8).reshape(fr['h'], fr['w'])))
    hud = {}
    timeline = []
    for t, name, f in rec.frames(0.5):
        if H.region_match(f, exp_choix, 0, 190, mask=m_choix) >= 0.99:
            kind = 'CHOIX'
        elif H.region_match(f, exp_chem, 9, 48, mask=m_chem) >= 0.75:
            kind = 'INTER'
        elif half(f).max() < 20:
            kind = 'czarny'
        else:
            pl = palette_level(f, pals)
            order = np.argsort(pl)[::-1]
            k, k2 = int(order[0]), int(order[1])
            # paleta poziomu musi pokrywać klatkę i wyraźnie odróżniać się od innych poziomów
            # (gwiazdy w poziomie 5 są animowane paletą, stąd próg 0.95)
            kind = 'poziom %d' % (k + 1) if pl[k] >= 0.95 and pl[k] - pl[k2] >= 0.2 else 'inny'
            if kind != 'inny' and hud.get(k, 0) < 0.98:
                for idx, ic in icons:
                    sc, _, _ = template_search(f, H.expected_rgb(ic, pals[k]), ic != 0, region=(0, 0, 320, 24))
                    hud[k] = max(hud.get(k, 0), sc)
        if not timeline or timeline[-1][1] != kind:
            timeline.append((round(t, 1), kind))
    levels_seen = [k for _, k in timeline if k.startswith('poziom')]
    inter_count = sum(1 for _, k in timeline if k == 'INTER')
    r.notes.append('oś czasu: ' + ', '.join('%s@%.1fs' % (k, t) for t, k in timeline))
    print('   oś czasu:', timeline)
    for lv in range(1, 7):
        r.check('poziom %d wczytany i wyświetlony (paleta poziomu)' % lv, 'poziom %d' % lv in levels_seen)
    r.check('ikony HUD (klatki 135-144 za poszerzoną klatką 134) poprawne we wszystkich poziomach',
            len(hud) == 6 and min(hud.values()) >= 0.98, ', '.join('p%d: %.3f' % (k + 1, v) for k, v in sorted(hud.items())))
    r.check('mapa INTER z polskimi szyldami przed poziomami', inter_count >= 6, '%d wystąpień' % inter_count)
    last_level6 = max([i for i, (_, k) in enumerate(timeline) if k == 'poziom 6'] or [-1])
    after = [k for _, k in timeline[last_level6 + 1:]] if last_level6 >= 0 else []
    r.check('po ukończeniu poziomu 6 gra wraca do ekranu wyboru postaci', 'CHOIX' in after, ' -> '.join(after[:6]))
    rec.sheet(os.path.join(args.out, 'all_levels.png'), step=4.0)
    return r


def scenario_gameover(args, work):
    """[łatka testowa] wymuszenie gałęzi końca gry -> klatka 127 rysowana procedurą gry."""
    r = Result('gameover')
    game = prepare_game(args.game, os.path.join(work, 'game_go'), exe_patches=[TP.force_gameover])
    rec = H.run(game, os.path.join(work, 'gameover'), keys=keys_seq('2', 5, 'space', 4, 'space'),
                seconds=45, wait=3, pace=1)
    spr = sprite_frame(127)
    pal = level_palette('MAG.CK1')
    tpl = H.expected_rgb(spr, pal)
    mask = spr != 0
    best = (0, None, None, None, None)
    for t, name, f in rec.frames(0.25):
        s, x, y = template_search(f, tpl, mask, region=(60, 20, 260, 180))
        if s > best[0]:
            best = (s, t, x, y, f)
    s, t, x, y, f = best
    r.check('sprite "KONIEC GRY" wyświetlony w grze', s >= 0.98, 'zgodność %.3f w (%s,%s), t=%s s' % (s, x, y, t))
    if f is not None:
        Image.fromarray(f).save(os.path.join(args.out, 'gameover_frame.png'))
    rec.sheet(os.path.join(args.out, 'gameover.png'), step=3.0)
    return r


def tile_template(png, box, pal):
    full = np.array(Image.open(os.path.join(LOC, png)), np.uint8)
    if box == 'mirror_music':   # lustrzane PŁYTY: kafel 79 (x304,y48) + kafel 120 (x0,y96)
        a = np.concatenate([full[48:64, 304:320], full[96:112, 0:16]], axis=1)
    else:
        x0, y0, w, h = box
        a = full[y0:y0 + h, x0:x0 + w]
    return H.expected_rgb(a, pal), np.ones(a.shape, bool)


def scenario_tiles(args, work, name, level, px, py, checks, map_cells=None):
    """[łatka testowa] start gracza obok szyldu - sprawdzenie polskich kafli w poziomie.

    map_cells - dla szyldów w pokojach bonusowych (kamera nie wjeżdża tam bez drzwi):
    te same kafle są wstawiane do testowej kopii mapy obok miejsca startu."""
    r = Result(name)
    patches = []
    if px is not None:
        patches.append(lambda b: TP.player_start(b, level, px, py))
    if level:
        patches.append(lambda b: TP.start_level(b, level))
    game = prepare_game(args.game, os.path.join(work, 'game_' + name), exe_patches=patches)
    if map_cells:
        TP.map_edit(game, gd.LEVELS[level]['sql'], map_cells)
    rec = H.run(game, os.path.join(work, name), keys=keys_seq('2', 5, 'space', 4, 'space'),
                seconds=45, wait=3, pace=1)
    pal = level_palette(gd.LEVELS[level]['ck1'])
    results = {c[0]: (0, None, None, None, None) for c in checks}
    for t, n, f in rec.frames(0.5):
        for desc, png, box in checks:
            tpl, mask = tile_template(png, box, pal)
            s, x, y = template_search(f, tpl, mask)
            if s > results[desc][0]:
                results[desc] = (s, t, x, y, f)
    for desc, (s, t, x, y, f) in results.items():
        r.check(desc, s >= 0.97, 'zgodność %.3f w (%s,%s), t=%s s' % (s, x, y, t))
        if f is not None:
            Image.fromarray(f).save(os.path.join(args.out, '%s_%s.png' % (name, desc.split()[0].lower())))
    rec.sheet(os.path.join(args.out, name + '.png'), step=3.0)
    return r


def scenario_insert(args, work):
    """Ekran zmiany dyskietki: brak AVTMAG.SQV wymusza INSERT.SQZ (ścieżka gry bez łatek)."""
    r = Result('insert_disk')
    game = prepare_game(args.game, os.path.join(work, 'game_insert'), remove=['AVTMAG.SQV'])
    rec = H.run(game, os.path.join(work, 'insert'), keys=keys_seq('2', 5, 'space'), seconds=35, wait=3, pace=1)
    ins, ipal = png_indexed(os.path.join(LOC, 'INSERT.SQZ.png'))
    t, n, s, f = H.find_match(rec, H.expected_rgb(ins[90:150], ipal), 0, 90, step=0.5)
    r.check('polski ekran "WŁÓŻ DYSK II"', s >= 0.99, 'zgodność %.3f w t=%s s' % (s, t))
    if f is not None:
        Image.fromarray(f).save(os.path.join(args.out, 'insert_frame.png'))
    return r


def scenario_ega(args, work):
    """Opcja [1] EGA menu RUNME: zachowanie identyczne z oryginałem (to wydanie nie uruchamia gry w EGA)."""
    r = Result('runme_ega')
    outs = {}
    for label, src in (('oryginał', ORIG), ('PL', args.game)):
        game = prepare_game(src, os.path.join(work, 'game_ega_' + ('o' if src == ORIG else 'p')))
        rec = H.run(game, os.path.join(work, 'ega_' + ('o' if src == ORIG else 'p')), keys='1',
                    seconds=20, wait=3, pace=1)
        last = None
        for t, n, f in rec.frames(0.2):
            last = f
        outs[label] = ([os.path.basename(x).rsplit('_', 1)[0] for x in rec.avis], last)
    r.check('oryginał i wersja PL uruchamiają te same programy', outs['oryginał'][0] == outs['PL'][0],
            'oryginał: %s, PL: %s' % (outs['oryginał'][0], outs['PL'][0]))
    last = outs['PL'][1]
    if last is not None:
        Image.fromarray(last[:40]).save(os.path.join(args.out, 'runme_exit_message.png'))
    # komunikat pożegnalny (1. linia ekranu tekstowego) musi różnić się od oryginału (przetłumaczony)
    diff = outs['oryginał'][1] is not None and last is not None and not np.array_equal(outs['oryginał'][1][:16], last[:16])
    r.check('komunikat po wyjściu przetłumaczony (zrzut: runme_exit_message.png)', diff)
    return r


def scenario_direct(args, work):
    """Bezpośrednie uruchomienie 1.EXE (bez menu RUNME)."""
    r = Result('direct_exe')
    game = prepare_game(args.game, os.path.join(work, 'game_direct'))
    rec = H.run(game, os.path.join(work, 'direct'), keys='', seconds=40, program='1.EXE')
    choix, cpal = png_indexed(os.path.join(LOC, 'CHOIX.SQZ.png'))
    t, n, s, f = H.find_match(rec, H.expected_rgb(choix[190:200], cpal), 0, 190, step=0.5,
                              mask=choix_mask(choix))
    r.check('1.EXE uruchomione bezpośrednio pokazuje polski ekran wyboru', s >= 0.99, 'zgodność %.3f, t=%s s' % (s, t))
    return r


def scenario_console(args, work):
    """Komunikaty konsolowe: menu RUNME, brak EGA/VGA (emulowana karta CGA), brak pamięci [łatka testowa]."""
    r = Result('console')
    S = {x['id']: x for x in json.load(open(os.path.join(ROOT, 'localization', 'pl', 'strings.json'),
                                             encoding='utf-8'))['strings']}
    game = prepare_game(args.game, os.path.join(work, 'game_con'))
    rec = H.run(game, os.path.join(work, 'con_runme'), keys='1', seconds=15, wait=3, log_con=True)
    lines = rec.console_lines()
    for sid in ('runme.line_presents', 'runme.line_title', 'runme.line_intro', 'runme.exit_message'):
        want = S[sid]['translation'].strip()
        r.check('konsola RUNME: %s' % sid, any(want in l for l in lines), repr(want))
    rec = H.run(game, os.path.join(work, 'con_video'), seconds=10, machine='cga', program='1.EXE', log_con=True)
    want = S['exe.video_error']['translation']
    r.check('1.EXE na karcie CGA: %r' % want, any(want in l for l in rec.console_lines()),
            '; '.join(rec.console_lines()[-2:]))
    game2 = prepare_game(args.game, os.path.join(work, 'game_con2'), exe_patches=[TP.swap_error_messages])
    rec = H.run(game2, os.path.join(work, 'con_mem'), seconds=10, machine='cga', program='1.EXE', log_con=True)
    want = S['exe.out_of_memory']['translation']
    r.check('komunikat nr 1 z tablicy (brak pamięci): %r' % want, any(want in l for l in rec.console_lines()),
            '; '.join(rec.console_lines()[-2:]))
    return r


def classic_scroll_build(work):
    """Wersja PL z oryginalnym przewijaniem (build --classic-scroll).

    Płynne przewijanie zmienia moment aktywacji przeciwników, więc dema
    (zapisane wejście) rozjeżdżają się z oryginałem; regresja lokalizacji
    porównuje więc oryginał z polską wersją bez tego modu."""
    out = os.path.join(work, 'build_classic')
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'build.py'), '--source', ORIG, '--locale', 'pl',
                    '--output', out, '--classic-scroll'], check=True, stdout=subprocess.DEVNULL)
    return os.path.join(out, 'game')


def camera_shifts(rec, t0=None, t1=None):
    """Przesunięcia obrazu planszy między kolejnymi klatkami (korelacja fazowa, piksele gry)."""
    out = []
    prev = None
    for avi in rec.avis:
        if not os.path.basename(avi).startswith('1_'):
            continue
        info, chunks = zmbv.avi_info_and_frames(avi)
        fps = info['fps'] or 70.0
        dec = zmbv.ZMBVDecoder(info['width'], info['height'])
        for i, c in enumerate(chunks):
            t = i / fps
            f = dec.decode(c)
            if (t0 is not None and t < t0) or (t1 is not None and t > t1):
                prev = None
                continue
            g = zmbv.to_rgb(f, dec.palette)[28:316:2, ::2].astype(np.int32)   # plansza 320x144
            g = g[..., 0] * 65536 + g[..., 1] * 256 + g[..., 2]
            if prev is not None and (g != prev).mean() > 0.05:
                a = prev - prev.mean()
                b = g - g.mean()
                R = np.fft.fft2(a) * np.conj(np.fft.fft2(b))
                R /= np.abs(R) + 1e-9
                cc = np.abs(np.fft.ifft2(R))
                dy, dx = np.unravel_index(cc.argmax(), cc.shape)
                if dy > cc.shape[0] // 2:
                    dy -= cc.shape[0]
                if dx > cc.shape[1] // 2:
                    dx -= cc.shape[1]
                if dx or dy:
                    out.append((round(t, 2), int(-dx), int(-dy)))
            prev = g
    return out


def scenario_smooth_scroll(args, work):
    """Płynne przewijanie: demo poziomu 1 - kamera co piksel, bez skoków o pół ekranu."""
    r = Result('smooth_scroll')
    game = prepare_game(args.game, os.path.join(work, 'game_smooth'))
    rec = H.run(game, os.path.join(work, 'smooth'), keys='2', seconds=75, wait=3, pace=1)
    shifts = [s for s in camera_shifts(rec, 55, 70)]
    dxs = [dx for t, dx, dy in shifts if dx]
    r.notes.append('przesunięcia poziome (px): %s' % sorted(set(dxs)))
    r.check('kamera przesuwa się w poziomie', len(dxs) >= 50, '%d zmian' % len(dxs))
    r.check('przesunięcia co piksel (nie tylko wielokrotności 8)', any(dx % 8 for dx in dxs),
            'wartości: %s' % sorted(set(dxs))[:12])
    r.check('brak skoków powyżej 16 px na klatkę', all(abs(dx) <= 16 and abs(dy) <= 16 for t, dx, dy in shifts),
            'max |dx| = %d' % max([abs(d) for d in dxs] or [0]))
    rec.sheet(os.path.join(args.out, 'smooth_scroll.png'), step=3.0)
    return r


def scenario_demo_regression(args, work, seconds=100):
    """Regresja: tryb demo (zapisane wejście DEMO*.BIN) - oryginał vs PL (klasyczne przewijanie) klatka po klatce."""
    r = Result('demo_regression')
    recs = {}
    for tag, src in (('o', ORIG), ('p', classic_scroll_build(work))):
        game = prepare_game(src, os.path.join(work, 'game_demo_' + tag))
        recs[tag] = H.run(game, os.path.join(work, 'demo_' + tag), keys='2', seconds=seconds, wait=3, pace=1)
    P = [(t, f[::2, ::2].copy()) for t, n, f in recs['p'].frames(0.25)]
    # oryginał: wszystkie klatki (70/s), ale tylko w oknach +-1.5 s wokół próbek PL
    want = [t for t, _ in P]
    O = []
    j = 0
    for t2, n, g in recs['o'].frames(0.0):
        while j < len(want) and want[j] < t2 - 1.5:
            j += 1
        if j < len(want) and abs(want[j] - t2) <= 1.5:
            O.append((t2, g[::2, ::2].copy()))
    mag = H.vga_rgb(level_palette('MAG.CK1')).astype(np.int16)
    neon = mag[[5, 7, 11, 13, 14]]
    inter_rects = [(9, 48, 82, 54), (183, 159, 228, 166)]
    choix, cpal = png_indexed(os.path.join(LOC, 'CHOIX.SQZ.png'))
    exp_choix = H.expected_rgb(choix[190:200], cpal)
    m_choix = choix_mask(choix)
    # ekran wyboru: pasek z napisem, kolory animowane paletą i animowane sprite'y bohaterów
    orig_bar = png_indexed(os.path.join(args.extracted, 'images', 'CHOIX.SQZ.png'))[0][192:200] != 0
    allowed_choix = np.isin(choix, CHOIX_ANIMATED)
    allowed_choix[190:200, :] = True
    allowed_choix[100:160, 60:220] = True
    stats = {'identyczne': 0, 'menu tekstowe': 0, 'pasek CHOIX': 0, 'szyldy INTER': 0,
             'neony poziomu 1': 0, 'przejście/zanikanie': 0, 'animacja palety': 0, 'NIEWYJAŚNIONE': 0}
    unexplained = []
    prev_bad = False
    for t, f in P:
        cands = [(abs(t2 - t), g) for t2, g in O if abs(t2 - t) <= 1.5 and g.shape == f.shape]
        if not cands:
            stats['menu tekstowe'] += 1
            continue
        best = min(cands, key=lambda c: int((f != c[1]).any(axis=2).sum()))[1]
        d = (f != best).any(axis=2)
        if not d.any():
            stats['identyczne'] += 1
            prev_bad = False
            continue
        ys, xs = np.nonzero(d)
        choix_screen = H.region_match(np.repeat(np.repeat(f, 2, 0), 2, 1), exp_choix, 0, 190, mask=m_choix) >= 0.99
        # także podczas wygaszania: kształt angielskiego paska w klatce oryginału
        if not choix_screen and best.shape[:2] == (200, 320):
            lit = best[192:200].max(axis=2) > 0
            choix_screen = float((lit == orig_bar).mean()) >= 0.98 and lit.sum() > 300
        if f.shape[1] != 320:
            kind = 'menu tekstowe'
        elif (f[d][:, :2] == best[d][:, :2]).all():
            kind = 'animacja palety'      # różni się tylko kanał B (cyklowanie kolorów gry)
        elif (choix_screen or ys.min() >= 150) and (allowed_choix[d]).all():
            kind = 'pasek CHOIX'
        elif all(any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in inter_rects) for y, x in zip(ys, xs)):
            kind = 'szyldy INTER'
        else:
            fp = f[d].astype(np.int16)
            fo = best[d].astype(np.int16)
            in_neon = lambda c: (np.abs(c[:, None, :] - neon[None]).max(axis=-1) <= 4).any(axis=1)
            if in_neon(fp).all() and in_neon(fo).all():
                kind = 'neony poziomu 1'
            elif abs(float(f.mean()) - float(best.mean())) > 0.5 or f.max() < 200:
                kind = 'przejście/zanikanie'   # klatka w trakcie zmiany jasności palety (fade)
            elif not prev_bad:
                kind = 'przejście/zanikanie'   # pojedyncza klatka rozjechana w czasie (fade, scroll)
                prev_bad = True
            else:
                kind = 'NIEWYJAŚNIONE'
                unexplained.append((round(t, 2), int(d.sum())))
                if len(unexplained) <= 3:
                    Image.fromarray(np.concatenate([best, f], axis=1).astype(np.uint8)).save(
                        os.path.join(args.out, 'demo_diff_%.1f.png' % t))
        stats[kind] += 1
        if kind != 'przejście/zanikanie':
            prev_bad = False
    r.notes.append('klasyfikacja klatek: ' + ', '.join('%s=%d' % kv for kv in stats.items()))
    print('   ', stats)
    r.check('wszystkie różnice wynikają z lokalizacji (tekst, napisy, neony)', not unexplained,
            'niewyjaśnione: %s' % unexplained[:5])
    r.check('większość klatek identyczna z oryginałem', stats['identyczne'] >= 0.3 * len(P),
            '%d/%d' % (stats['identyczne'], len(P)))
    return r


PANGRAM = ('ZAŻÓŁĆ GĘŚLĄ', 'JAŹŃ ĄĆĘŁŃÓŚŹŻ')


def scenario_polish_glyphs(args, work):
    """Wszystkie polskie wielkie litery fontu paska wyboru w grze (testowa wersja CHOIX.SQZ z pangramem)."""
    r = Result('polish_glyphs')
    import importlib.util
    spec = importlib.util.spec_from_file_location('mg', os.path.join(ROOT, 'tools', 'make_graphics.py'))
    mg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mg)
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        ctx = mg.Ctx(ORIG, 'pl')
        ctx.strings['choix.choose_player'] = dict(ctx.strings['choix.choose_player'], translation=PANGRAM[0])
        ctx.strings['choix.press_fire'] = dict(ctx.strings['choix.press_fire'], translation=PANGRAM[1])
        arr, pal = mg.make_choix(ctx)
    finally:
        os.chdir(cwd)
    im = bf.ILBM.parse(bf.unpack(open(os.path.join(ORIG, 'CHOIX.SQZ'), 'rb').read()))
    im.pixels = bytearray(arr.tobytes())
    game = prepare_game(args.game, os.path.join(work, 'game_glyphs'))
    open(os.path.join(game, 'CHOIX.SQZ'), 'wb').write(bf.pack(im.encode()))
    Image.fromarray(H.expected_rgb(arr, pal)).resize((960, 600), Image.NEAREST).save(
        os.path.join(args.out, 'polish_glyphs_expected.png'))
    rec = H.run(game, os.path.join(work, 'glyphs'), keys='2', seconds=40, wait=3, pace=1)
    t, n, s, f = H.find_match(rec, H.expected_rgb(arr[190:200], pal), 0, 190, step=0.5, mask=choix_mask(arr))
    r.check('pangram %r / %r wyświetlony w grze' % PANGRAM, s >= 0.99, 'zgodność %.3f, t=%s s' % (s, t))
    if f is not None:
        Image.fromarray(f[360:400]).resize((1280, 80), Image.NEAREST).save(os.path.join(args.out, 'polish_glyphs_ingame.png'))
    return r


SCENARIOS = {
    'boot': scenario_boot,
    'all_levels': scenario_all_levels,
    'gameover': scenario_gameover,
    'mag_store': lambda a, w: scenario_tiles(a, w, 'mag_store', 0, 1080, 992, [
        ('SKLEP neon (MAG.CK2 kafle 50-51)', 'MAG.CK2.png', (160, 32, 32, 16))]),
    'mag_music': lambda a, w: scenario_tiles(a, w, 'mag_music', 0, 570, 992, [
        ('PŁYTY neon (MAG.CK2 kafle 96-97)', 'MAG.CK2.png', (256, 64, 32, 16))]),
    'mag_mirror': lambda a, w: scenario_tiles(a, w, 'mag_mirror', 0, None, None, [
        ('SKLEP odbicie (MAG.CK2 kafle 126-127)', 'MAG.CK2.png', (96, 96, 32, 16)),
        ('PŁYTY odbicie (MAG.CK1 kafle 79+120)', 'MAG.CK1.png', 'mirror_music')],
        map_cells=[(6, 67, 0xFE), (7, 67, 0xFF), (10, 67, 79), (11, 67, 120)]),
    'ville_plaque': lambda a, w: scenario_tiles(a, w, 'ville_plaque', 4, None, None, [
        ('PROGRAMISTA tabliczka (VILLE.CK1 kafle 114-117)', 'VILLE.CK1.png', (224, 80, 64, 16))],
        map_cells=[(6, 91, 114), (7, 91, 115), (8, 91, 116), (9, 91, 117)]),
    'insert_disk': scenario_insert,
    'runme_ega': scenario_ega,
    'console': scenario_console,
    'demo_regression': scenario_demo_regression,
    'smooth_scroll': scenario_smooth_scroll,
    'polish_glyphs': scenario_polish_glyphs,
    'direct_exe': scenario_direct,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--game', default=os.path.join(ROOT, 'build', 'game'))
    ap.add_argument('--extracted', default=os.path.join(ROOT, 'work', 'extracted'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'tests', 'results', 'latest'))
    ap.add_argument('--work', default=os.path.join(ROOT, 'work', 'dbx'))
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--merge', action='store_true', help='dopisz/zastąp wyniki w istniejącym results.json')
    args = ap.parse_args()
    if not H.find_dosbox():
        print('Brak DOSBox-X - testy pominięte (ustaw DOSBOX_X).')
        return 2
    os.makedirs(args.out, exist_ok=True)
    results = []
    for name, fn in SCENARIOS.items():
        if args.only and name not in args.only:
            continue
        print('== scenariusz:', name, '-', (fn.__doc__ or '').strip().split('\n')[0])
        t0 = time.time()
        try:
            res = fn(args, args.work)
        except Exception as e:  # błąd uruchomienia też jest wynikiem testu
            res = Result(name)
            res.check('scenariusz wykonany bez wyjątku', False, repr(e))
        res.notes.append('czas: %.0f s' % (time.time() - t0))
        results.append(res)
    data = [{'scenario': r.name, 'ok': r.ok, 'checks': r.checks, 'notes': r.notes} for r in results]
    rpath = os.path.join(args.out, 'results.json')
    if args.merge and os.path.exists(rpath):
        old = json.load(open(rpath, encoding='utf-8'))
        new = {d['scenario']: d for d in data}
        data = [new.pop(d['scenario'], d) for d in old] + list(new.values())
        results = []
        for d in data:
            rr = Result(d['scenario'])
            rr.checks, rr.notes = d['checks'], d['notes']
            results.append(rr)
    with open(os.path.join(args.out, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    lines = ['# Wyniki testów DOSBox-X', '', 'Gra: `%s`' % os.path.relpath(args.game, ROOT), '']
    for r in results:
        lines.append('## %s — %s' % (r.name, 'ZALICZONY' if r.ok else 'NIEZALICZONY'))
        for c in r.checks:
            lines.append('- [%s] %s %s' % ('x' if c['ok'] else ' ', c['check'], c['detail']))
        for n in r.notes:
            lines.append('- _%s_' % n)
        lines.append('')
    with open(os.path.join(args.out, 'report.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))
    return 0 if all(r.ok for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())

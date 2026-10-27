#!/usr/bin/env python3
"""Testy narzędzi (bez emulatora). Uruchomienie: python tests/test_tools.py

Wymagają katalogu original/ z obsługiwaną wersją gry (inaczej są pomijane).
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import bbformats as bf  # noqa: E402
import gamedata as gd  # noqa: E402
import glyphkit as gk  # noqa: E402
import patch_exe  # noqa: E402

ORIG = os.path.join(ROOT, 'original')
HAVE_GAME = os.path.isfile(os.path.join(ORIG, '1.EXE'))
STRINGS = os.path.join(ROOT, 'localization', 'pl', 'strings.json')


def sha(d):
    return hashlib.sha256(d).hexdigest()


@unittest.skipUnless(HAVE_GAME, 'brak katalogu original/')
class FormatTests(unittest.TestCase):
    def compressed_files(self):
        out = []
        for name in sorted(gd.KNOWN_FILES):
            d = open(os.path.join(ORIG, name), 'rb').read()
            if name.endswith(('.SQZ', '.SQV', '.SQL', '.CK1', '.CK2')) and bf.is_compressed(d):
                out.append((name, d))
        return out

    def test_identify(self):
        ident = gd.identify(ORIG)
        self.assertFalse(ident['missing'])
        self.assertFalse(ident['mismatch'])

    def test_compression_roundtrip(self):
        files = self.compressed_files()
        self.assertEqual(len(files), 34)  # 5 AVT + 6 ENEMI + SPRITE + 4 ekrany + 12 CK + 6 SQL
        for name, d in files:
            raw = bf.unpack(d)
            packed = bf.pack(raw)
            self.assertEqual(bf.unpack(packed), raw, name)
            self.assertLessEqual(bf.dos_overrun(packed), gd.MAX_DOS_OVERRUN, name)
            self.assertLessEqual(len(packed), len(d) + 16, name)

    def test_uncompressed_crack_files_detected(self):
        for name in ('JOHN.SQZ', 'OH.SQZ', 'TERRY.SQZ'):
            self.assertFalse(bf.is_compressed(open(os.path.join(ORIG, name), 'rb').read()), name)

    def test_ilbm_roundtrip(self):
        for name in gd.ILBM_FILES:
            raw = bf.unpack(open(os.path.join(ORIG, name), 'rb').read())
            im = bf.ILBM.parse(raw)
            back = bf.ILBM.parse(im.encode())
            self.assertEqual(back.pixels, im.pixels, name)
            self.assertEqual(back.palette, im.palette, name)
            self.assertNotIn(0x80, self._byterun_controls(im.encode()), name)

    @staticmethod
    def _byterun_controls(ilbm):
        body = ilbm[ilbm.find(b'BODY') + 8:]
        i, ctl = 0, set()
        while i < len(body):
            c = body[i]
            ctl.add(c)
            i += 1 + (c + 1 if c < 128 else 1)
        return ctl

    def test_sqv_roundtrip(self):
        for name in ['SPRITE.SQV'] + [l['enemies'] for l in gd.LEVELS]:
            raw = bf.unpack(open(os.path.join(ORIG, name), 'rb').read())
            frames, rest = bf.parse_sqv(raw)
            self.assertEqual(bf.build_sqv([(f['w'], f['h'], f['data']) for f in frames], rest), raw, name)
            for f in frames[:5]:
                pix = bf.decode_planar(f['data'], f['w'], f['h'])
                self.assertEqual(bf.encode_planar(bytes(pix), f['w'], f['h']), f['data'])

    def test_dos_decoder_overrun_model(self):
        # oryginalne pliki: model dekodera DOS daje 0-1 bajt nadmiaru
        for name, d in self.compressed_files():
            self.assertIn(bf.dos_overrun(d), (0, 1), name)


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.data = json.load(open(STRINGS, encoding='utf-8'))

    def test_schema(self):
        ids = set()
        for s in self.data['strings']:
            for k in ('id', 'kind', 'file', 'original', 'translation', 'location', 'max_size', 'constraints', 'status'):
                self.assertIn(k, s, s.get('id'))
            self.assertNotIn(s['id'], ids)
            ids.add(s['id'])
            self.assertIn(s['status'], ('translated', 'kept', 'review', 'unused', 'excluded'))
            if s['status'] == 'translated':
                self.assertTrue(s['translation'].strip(), s['id'])

    def test_fonts_load_and_cover_translations(self):
        fonts = {os.path.basename(p)[:-5]: gk.load_font(p)
                 for p in glob.glob(os.path.join(ROOT, 'localization', 'pl', 'fonts', '*.json'))}
        S = {s['id']: s for s in self.data['strings']}
        use = {'choix': ['choix.choose_player', 'choix.press_fire'], 'inter_chem': ['inter.chemicals'],
               'inter_store': ['inter.store'], 'neon': ['mag.neon_store', 'mag.neon_music'],
               'plaque': ['ville.plaque_role'], 'popup': ['sprite.one_up']}
        for font, sids in use.items():
            for sid in sids:
                self.assertEqual(gk.missing_chars(fonts[font], S[sid]['translation']), [], (font, sid))
        # font paska wyboru zawiera wszystkie polskie wielkie litery
        self.assertEqual(gk.missing_chars(fonts['choix'], 'AĄBCĆDEĘFGHIJKLŁMNŃOÓPQRSŚTUVWXYZŹŻ'), [])

    def test_console_texts_fit(self):
        spec = patch_exe.build_spec('pl')
        for item in spec:
            self.assertEqual(len(item['expect']), len(item['replace']))


@unittest.skipUnless(HAVE_GAME, 'brak katalogu original/')
class BuildTests(unittest.TestCase):
    def run_build(self, out):
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'build.py'), '--source', ORIG,
                            '--locale', 'pl', '--output', out], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        return {n: sha(open(os.path.join(out, 'game', n), 'rb').read()) for n in gd.KNOWN_FILES}

    def test_build_deterministic_and_original_untouched(self):
        before = {n: sha(open(os.path.join(ORIG, n), 'rb').read()) for n in gd.KNOWN_FILES}
        tmp = tempfile.mkdtemp(prefix='bbpl_build_')
        try:
            a = self.run_build(os.path.join(tmp, 'a'))
            b = self.run_build(os.path.join(tmp, 'b'))
            self.assertEqual(a, b)
            changed = sorted(n for n in a if a[n] != before[n])
            self.assertEqual(changed, ['1.EXE', 'CHOIX.SQZ', 'INSERT.SQZ', 'INTER.SQZ', 'MAG.CK1', 'MAG.CK2',
                                       'RUNME.COM', 'SPRITE.SQV', 'VILLE.CK1'])
        finally:
            shutil.rmtree(tmp)
        after = {n: sha(open(os.path.join(ORIG, n), 'rb').read()) for n in gd.KNOWN_FILES}
        self.assertEqual(before, after, 'katalog original/ został zmieniony')

    def test_patch_exe_refuses_wrong_file(self):
        tmp = tempfile.mkdtemp(prefix='bbpl_exe_')
        try:
            shutil.copy2(os.path.join(ORIG, '1.EXE'), tmp)
            shutil.copy2(os.path.join(ORIG, 'RUNME.COM'), tmp)
            p = os.path.join(tmp, '1.EXE')
            d = bytearray(open(p, 'rb').read())
            d[0x15190] ^= 1
            open(p, 'wb').write(d)
            with self.assertRaises(patch_exe.PatchError):
                patch_exe.apply_spec(tmp, patch_exe.build_spec('pl'))
        finally:
            shutil.rmtree(tmp)

    def test_distribution_patch(self):
        tmp = tempfile.mkdtemp(prefix='bbpl_patch_')
        try:
            out = os.path.join(tmp, 'b')
            self.run_build(out)
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'make_patch.py'), '--source', ORIG,
                                '--build', os.path.join(out, 'game'), '--output', os.path.join(tmp, 'dist')],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn('OK', r.stdout)
            # paczka nie może zawierać plików gry
            names = os.listdir(os.path.join(tmp, 'dist', 'blues-brothers-pl-1.0'))
            for n in names:
                self.assertNotIn(n.upper(), gd.KNOWN_FILES)
        finally:
            shutil.rmtree(tmp)


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('ignore', ResourceWarning)
    unittest.main(verbosity=2, warnings='ignore')

#!/usr/bin/env python3
"""Testy czterech wariantów i instalatora bez zależności zewnętrznych gracza."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import gamedata as gd  # noqa: E402
import make_patch as maker  # noqa: E402

ORIGINAL = ROOT / 'original'


@unittest.skipUnless((ORIGINAL / '1.EXE').is_file(), 'brak katalogu original/')
class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix='bb_bundle_tests_')
        cls.work = Path(cls.workspace.name)
        cls.package = maker.create_package(ORIGINAL, cls.work, '1.1.0')
        cls.patch = json.loads((cls.package / 'patch.json').read_text(encoding='utf-8'))
        spec = importlib.util.spec_from_file_location('bundle_installer', cls.package / 'apply_patch.py')
        cls.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.installer)
        cls.original = maker.read_original(ORIGINAL)

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='bb_case_', dir=self.work)
        self.addCleanup(self.tmp.cleanup)
        self.case = Path(self.tmp.name)
        self.source = self.case / 'English game'
        self.source.mkdir()
        for name, data in self.original.items():
            (self.source / name).write_bytes(data)
        self.output = self.case / 'New game'

    def cli(self, *args, package=None):
        # -S wyłącza site-packages: użytkownik nie potrzebuje numpy ani Pillow.
        return subprocess.run([sys.executable, '-I', '-S', str((package or self.package) / 'apply_patch.py'),
                               str(self.source), *map(str, args)], capture_output=True, text=True)

    def assert_source_untouched(self):
        self.assertEqual({p.name for p in self.source.iterdir()}, set(self.original))
        for name, data in self.original.items():
            self.assertEqual((self.source / name).read_bytes(), data, name)

    def changed(self, key):
        return set(self.patch['profiles'][key]['files'])

    def test_four_build_profiles(self):
        self.assertEqual(self.changed('en-original'), set())
        self.assertEqual(self.changed('en-smooth'), {'1.EXE'})
        localized = {'1.EXE', 'RUNME.COM', 'CHOIX.SQZ', 'INSERT.SQZ', 'INTER.SQZ',
                     'MAG.CK1', 'MAG.CK2', 'SPRITE.SQV', 'VILLE.CK1'}
        self.assertEqual(self.changed('pl-original'), localized)
        self.assertEqual(self.changed('pl-smooth'), localized)
        for name in gd.KNOWN_FILES:
            a = self.patch['profiles']['pl-original']['output'][name]
            b = self.patch['profiles']['pl-smooth']['output'][name]
            self.assertEqual(a == b, name != '1.EXE', name)
        self.assert_source_untouched()

    def test_install_all_and_no_dependencies(self):
        result = self.cli('--output', self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual({p.name for p in self.output.iterdir()},
                         {'START.COM', 'ENORIG', 'ENSMOOTH', 'PLORIG', 'PLSMOOTH'})
        for key, profile in self.patch['profiles'].items():
            for name, meta in profile['output'].items():
                data = (self.output / profile['directory'] / name).read_bytes()
                self.assertEqual(maker.metadata(data), meta, key + '/' + name)
                built = self.work / key / 'game' / name
                self.assertEqual(data, built.read_bytes())
        self.assert_source_untouched()

    def test_check_no_writes(self):
        before = sorted(p.name for p in self.case.iterdir())
        result = self.cli('--check')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(sorted(p.name for p in self.case.iterdir()), before)
        self.assert_source_untouched()

    def test_existing_output_never_overwritten(self):
        self.output.mkdir()
        sentinel = self.output / 'my-data.txt'
        sentinel.write_text('keep', encoding='ascii')
        result = self.cli('--output', self.output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sentinel.read_text(), 'keep')
        self.assert_source_untouched()

    def test_reject_overlapping_paths(self):
        for output in (self.source, self.source / 'inside', self.source.parent):
            with self.subTest(output=output):
                self.assertNotEqual(self.cli('--output', output).returncode, 0)
        self.assert_source_untouched()

    def test_wrong_unmodified_file_and_missing_file(self):
        path = self.source / 'PRES.SQZ'
        data = bytearray(path.read_bytes())
        data[100] ^= 255
        path.write_bytes(data)
        self.assertNotEqual(self.cli('--output', self.output).returncode, 0)
        self.assertFalse(self.output.exists())
        path.unlink()
        self.assertNotEqual(self.cli('--check').returncode, 0)

    def test_symlinks_and_case_collisions(self):
        path = self.source / '1.EXE'
        path.unlink()
        path.symlink_to(ORIGINAL / '1.EXE')
        self.assertNotEqual(self.cli('--check').returncode, 0)
        path.unlink()
        path.write_bytes(self.original['1.EXE'])
        lower = self.source / '1.exe'
        if not lower.exists():  # Na systemie case-insensitive ta kolizja nie jest możliwa.
            lower.write_bytes(self.original['1.EXE'])
            self.assertNotEqual(self.cli('--check').returncode, 0)
            lower.unlink()
        linked_output = self.case / 'linked'
        linked_output.symlink_to(self.output, target_is_directory=True)
        self.assertNotEqual(self.cli('--output', linked_output).returncode, 0)

    def test_legacy_cli_is_read_only_error(self):
        for args in ((), ('--restore',)):
            result = self.cli(*args)
            self.assertNotEqual(result.returncode, 0)
        self.assert_source_untouched()

    def test_invalid_manifest(self):
        for mutate in (
            lambda p: p.update(format_version=1),
            lambda p: p['source'].update({'../BAD.EXE': p['source'].pop('1.EXE')}),
            lambda p: p['profiles']['en-original'].update(directory='../OUT'),
            lambda p: p['profiles']['en-smooth']['files']['1.EXE'].update(method='unknown'),
        ):
            patch = copy.deepcopy(self.patch)
            mutate(patch)
            with self.assertRaises(self.installer.PatchError):
                self.installer.validate_patch(patch)

    def test_bad_last_profile_publishes_nothing(self):
        package = self.case / 'bad-package'
        shutil.copytree(self.package, package)
        patch = copy.deepcopy(self.patch)
        profile = patch['profiles']['pl-smooth']
        profile['output']['1.EXE']['sha256'] = '0' * 64
        profile['files']['1.EXE']['target_sha256'] = '0' * 64
        (package / 'patch.json').write_text(json.dumps(patch), encoding='utf-8')
        result = self.cli('--output', self.output, package=package)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.case.glob('.bb-install-*')), [])
        self.assert_source_untouched()

    def test_write_failure_removes_only_staging(self):
        source = self.installer.read_source(self.source, self.patch['source'])
        launcher, results = self.installer.prepare(self.patch, source, self.package)
        with mock.patch.object(Path, 'write_bytes', side_effect=OSError('test: disk full')):
            with self.assertRaises(OSError):
                self.installer.install(self.patch, launcher, results, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.case.glob('.bb-install-*')), [])
        self.assert_source_untouched()

    def test_deterministic_archive_whitelist_and_extracted_install(self):
        archives = [self.case / 'a.zip', self.case / 'b.zip']
        for archive in archives:
            maker.write_archive(self.package, archive)
        self.assertEqual(archives[0].read_bytes(), archives[1].read_bytes())
        extraction = self.case / 'empty-extraction'
        extraction.mkdir()
        with zipfile.ZipFile(archives[0]) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()),
                             {self.package.name + '/' + n for n in maker.PACKAGE_FILES})
            for name in archive.namelist():
                self.assertNotIn(Path(name).name.upper(), gd.KNOWN_FILES)
            archive.extractall(extraction)
        extracted = extraction / self.package.name
        result = self.cli('--output', self.output, package=extracted)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)

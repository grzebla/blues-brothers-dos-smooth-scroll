#!/usr/bin/env python3
"""The Blues Brothers — English/Polski, original/smooth scroll.

Python 3.8+, no third-party packages. The source game is never modified.
    python apply_patch.py SOURCE --check
    python apply_patch.py SOURCE --output NEW_DIRECTORY
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
# --check nie zapisuje nawet cache modułów w katalogu paczki.
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import bbformats as bf  # noqa: E402

PROFILES = {
    'en-original': ('en', 'original', 'ENORIG'),
    'en-smooth': ('en', 'smooth', 'ENSMOOTH'),
    'pl-original': ('pl', 'original', 'PLORIG'),
    'pl-smooth': ('pl', 'smooth', 'PLSMOOTH'),
}
ORIGINAL_EXE_SHA256 = '769ee254b154a9444205524ec4b28a8147a372ac5b2cee2e25fcd83aa90d0add'


class PatchError(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def find(game, name):
    matches = [p for p in Path(game).iterdir() if p.name.upper() == name.upper()]
    if len(matches) > 1:
        raise PatchError('Ambiguous filenames: %s' % name)
    return str(matches[0]) if matches else None


def apply_bytes(data, entry):
    buf = bytearray(data)
    for off, hexdata in entry['bytes']:
        new = bytes.fromhex(hexdata)
        if not isinstance(off, int) or off < 0 or off + len(new) > len(buf):
            raise PatchError('Byte patch outside the source file')
        buf[off:off + len(new)] = new
    return bytes(buf)


def apply_pixels(pixels, width, regions):
    height = len(pixels) // width
    for reg in regions:
        x, y, w, h = reg['rect']
        if min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height:
            raise PatchError('Pixel patch outside the source image')
        mask = base64.b64decode(reg['mask'], validate=True)
        vals = base64.b64decode(reg['values'], validate=True)
        if len(mask) != (w * h + 7) // 8:
            raise PatchError('Invalid pixel mask length')
        k = 0
        for i in range(w * h):
            if mask[i >> 3] & (0x80 >> (i & 7)):
                if k >= len(vals) or vals[k] > 15:
                    raise PatchError('Invalid pixel values')
                pixels[(y + i // w) * width + x + i % w] = vals[k]
                k += 1
        if k != len(vals):
            raise PatchError('Unused pixel values')
    return pixels


def apply_ilbm(data, entry):
    im = bf.ILBM.parse(bf.unpack(data))
    apply_pixels(im.pixels, im.width, entry['regions'])
    return bf.pack(im.encode())


def apply_sqv(data, entry):
    frames, rest = bf.parse_sqv(bf.unpack(data))
    out = [(f['w'], f['h'], f['data']) for f in frames]
    for fr in entry['frames']:
        idx, w, h = fr['index'], fr['w'], fr['h']
        if not 0 <= idx < len(out) or not 0 < w <= 320 or not 0 < h <= 200:
            raise PatchError('Invalid sprite frame')
        if fr.get('regions') is not None:
            if (w, h) != out[idx][:2]:
                raise PatchError('Sprite region dimensions do not match')
            pix = bytearray(bf.decode_planar(out[idx][2], w, h))
            apply_pixels(pix, w, fr['regions'])
        else:
            pix = bytearray(base64.b64decode(fr['pixels'], validate=True))
            if len(pix) != w * h or any(p > 15 for p in pix):
                raise PatchError('Invalid sprite pixels')
        out[idx] = (w, h, bf.encode_planar(bytes(pix), w, h))
    return bf.pack(bf.build_sqv(out, rest))


METHODS = {'bytes': apply_bytes, 'ilbm': apply_ilbm, 'sqv': apply_sqv}


def validate_meta(meta):
    if (not isinstance(meta, dict) or not isinstance(meta.get('size'), int)
            or not 0 < meta['size'] <= 1048576
            or not isinstance(meta.get('sha256'), str)
            or not re.fullmatch('[0-9a-f]{64}', meta['sha256'])):
        raise PatchError('Invalid file manifest')


def validate_patch(patch):
    if patch.get('format_version') != 2:
        raise PatchError('Unsupported patch format. Use the matching installer from the same release; '
                         'version 1.0 packages use their original installer.')
    source = patch['source']
    if not isinstance(source, dict) or len(source) != 50:
        raise PatchError('Expected the complete 50-file source manifest')
    for name, meta in source.items():
        if not re.fullmatch(r'[A-Z0-9_]{1,8}\.[A-Z0-9]{1,3}', name):
            raise PatchError('Unsafe DOS filename in manifest: %s' % name)
        validate_meta(meta)
    if source.get('1.EXE') != {'size': 196608, 'sha256': ORIGINAL_EXE_SHA256}:
        raise PatchError('This patch is not for the supported English DOS release')
    if set(patch['profiles']) != set(PROFILES):
        raise PatchError('Expected all four language/scroll profiles')
    for key, (locale, scroll, directory) in PROFILES.items():
        profile = patch['profiles'][key]
        if (profile['locale'], profile['scroll'], profile['directory']) != (locale, scroll, directory):
            raise PatchError('Invalid profile metadata: %s' % key)
        if set(profile['output']) != set(source) or not set(profile['files']) <= set(source):
            raise PatchError('Incomplete profile: %s' % key)
        for name, meta in profile['output'].items():
            validate_meta(meta)
            entry = profile['files'].get(name)
            if entry is None:
                if meta != source[name]:
                    raise PatchError('Missing patch operations for %s' % name)
            elif (entry['method'] not in METHODS
                  or entry['source_sha256'] != source[name]['sha256']
                  or entry['source_size'] != source[name]['size']
                  or entry['target_sha256'] != meta['sha256']
                  or entry['target_size'] != meta['size']):
                raise PatchError('Invalid patch entry: %s' % name)
    if patch['launcher']['file'] != 'START.COM':
        raise PatchError('Invalid launcher filename')
    validate_meta(patch['launcher'])


def verify_file(data, meta, label):
    if len(data) != meta['size'] or sha(data) != meta['sha256']:
        raise PatchError('%s: size or SHA-256 mismatch' % label)


def read_source(game, manifest):
    if game.is_symlink() or not game.is_dir():
        raise PatchError('SOURCE must be a real directory, not a symbolic link')
    paths = {}
    for path in game.iterdir():
        name = path.name.upper()
        if name in manifest:
            if name in paths:
                raise PatchError('Ambiguous filenames: %s' % name)
            paths[name] = path
    result = {}
    for name, meta in sorted(manifest.items()):
        path = paths.get(name)
        if path is None or path.is_symlink() or not path.is_file():
            raise PatchError('%s: missing file or symbolic link' % name)
        data = path.read_bytes()
        verify_file(data, meta, name)
        result[name] = data
    return result


def validate_output(source, output):
    source, output = source.resolve(), output.absolute()
    resolved = output.resolve()
    if source == resolved or source in resolved.parents or resolved in source.parents:
        raise PatchError('SOURCE and OUTPUT must be separate, non-overlapping directories')
    if os.path.lexists(output):
        raise PatchError('OUTPUT already exists; choose a new directory (nothing was overwritten)')
    if not output.parent.is_dir():
        raise PatchError('The parent of OUTPUT must already exist')


def prepare(patch, source, package_dir):
    launcher_path = package_dir / 'START.COM'
    if launcher_path.is_symlink() or not launcher_path.is_file():
        raise PatchError('Missing START.COM in the patch package')
    launcher = launcher_path.read_bytes()
    verify_file(launcher, patch['launcher'], 'START.COM')
    results = {}
    for key, profile in patch['profiles'].items():
        files = {}
        for name, old in source.items():
            entry = profile['files'].get(name)
            new = METHODS[entry['method']](old, entry) if entry else old
            verify_file(new, profile['output'][name], '%s/%s' % (key, name))
            files[name] = new
        results[key] = files
    return launcher, results


def install(patch, launcher, results, output):
    # Staging jest naszym nowym katalogiem, nigdy katalogiem użytkownika.
    staging = Path(tempfile.mkdtemp(prefix='.bb-install-', dir=str(output.parent)))
    try:
        (staging / 'START.COM').write_bytes(launcher)
        for key, files in results.items():
            directory = staging / patch['profiles'][key]['directory']
            directory.mkdir()
            for name, data in files.items():
                (directory / name).write_bytes(data)
        # Sprawdzenie odczytu z dysku przed udostępnieniem katalogu instalacji.
        verify_file((staging / 'START.COM').read_bytes(), patch['launcher'], 'START.COM')
        for key, profile in patch['profiles'].items():
            for name, meta in profile['output'].items():
                verify_file((staging / profile['directory'] / name).read_bytes(), meta, name)
        if os.path.lexists(output):
            raise PatchError('OUTPUT appeared during installation; nothing was overwritten')
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('game', type=Path, help='clean supported English game directory')
    ap.add_argument('--output', type=Path, help='NEW directory for the four variants and START.COM')
    ap.add_argument('--check', action='store_true', help='verify source and patches without writing files')
    ap.add_argument('--restore', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.restore:
        ap.error('This installer never changes SOURCE. To undo an old 1.0 patch, use its original '
                 'installer and --restore; this package cannot restore old backups.')
    if args.output is None and not args.check:
        ap.error('--output NEW_DIRECTORY is required. In-place patching is no longer used.')
    try:
        with (HERE / 'patch.json').open(encoding='utf-8') as f:
            patch = json.load(f)
        validate_patch(patch)
        if args.output is not None:
            validate_output(args.game, args.output)
        source = read_source(args.game, patch['source'])
        launcher, results = prepare(patch, source, HERE)
        print('Verified all 50 source files, all four profiles and START.COM.')
        if args.check:
            print('Check complete. No files were written.')
            return 0
        install(patch, launcher, results, args.output.absolute())
        print('Installed: %s' % args.output.absolute())
        print('SOURCE was not changed. Run START.COM in DOSBox-X (VGA, cycles=fixed 20000).')
        print('English smooth-scroll only: enter ENSMOOTH and run 1.EXE.')
        return 0
    except (PatchError, OSError, ValueError, KeyError, TypeError, IndexError, bf.FormatError) as exc:
        print('ERROR: %s' % exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

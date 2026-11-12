# Smooth Scroll — install and play (1.1.0)

Install the smooth-scrolling mod for The Blues Brothers (DOS). The Polish translation is an optional addition, selected in the startup menu.

[Polski](install.pl.md) · [Project overview](../README.md)

## Requirements and download

- Your own legally obtained **English DOS hard-disk TDT/TRSI edition**.
  Other editions are not supported; no game download is provided.
- **Python 3.8+** on the host system: the installer's only dependency.
  No Pillow, numpy, NASM, clone or developer build is needed.
- DOS to run the game, for example DOSBox-X (tested version: **2026.01.02**).

Download `blues-brothers-1.1.0-patch.zip` and `SHA256SUMS` from
[release v1.1.0](https://github.com/grzebla/blues-brothers-dos-smooth-scroll/releases/tag/v1.1.0).
The [repository](https://github.com/grzebla/blues-brothers-dos-smooth-scroll) is private, so
these links require access. The patch ZIP can be provided separately; it
contains patch data and project code, not complete original game files.
Inside are `README.txt` (this guide), `CZYTAJ.txt` (Polish guide), `LICENSE.txt`,
`START.COM`, `patch.json`, `apply_patch.py` and `bbformats.py`.
Compare the ZIP's SHA-256 with its entry in `SHA256SUMS` before extracting it.
For example, use `shasum -a 256 blues-brothers-1.1.0-patch.zip` on macOS,
`sha256sum blues-brothers-1.1.0-patch.zip` on Linux, or PowerShell's
`Get-FileHash .\blues-brothers-1.1.0-patch.zip -Algorithm SHA256` on Windows.

## Install into a new directory

Open a host-system terminal in the extracted patch directory. Do not run
Python inside DOSBox. `SOURCE` is your original game directory; `NEW_DIR`
is the desired output directory, which **must not already exist**.
Its **parent directory must already exist**. Quote paths containing spaces.

```sh
python apply_patch.py SOURCE --check
python apply_patch.py SOURCE --output NEW_DIR
```

Use `python3` instead of `python` if needed. For example, on Windows:

```text
python apply_patch.py "C:\GAMES\BLUES" --check
python apply_patch.py "C:\GAMES\BLUES" --output "C:\GAMES\BB110"
```

The installer checks **all 50 files in `KNOWN_FILES`**, including their sizes
and SHA-256 hashes. The supported `1.EXE` is **196608 bytes**, SHA-256:

```text
769ee254b154a9444205524ec4b28a8147a372ac5b2cee2e25fcd83aa90d0add
```

Matching that EXE alone is not enough. Missing or modified game files are
not a supported base. Installation is **out of place** and does not change
`SOURCE`; use a separate output path, not a directory inside the source.

The result contains:

```text
NEW_DIR/
  START.COM
  ENORIG/      (en-original)
  ENSMOOTH/    (en-smooth)
  PLORIG/      (pl-original)
  PLSMOOTH/    (pl-smooth)
```

Each profile is a **complete game directory**, not an overlay requiring
another profile. `en-original` keeps the English game unchanged; `en-smooth`
changes **only `1.EXE`** for scrolling, with no Polish resources or text.
The Polish profiles add localization with original or smooth scrolling.
All four profiles are installed together; there is no `--variant` option.

## Start the game

Use VGA. In DOSBox-X, mount the output directory as drive C (replace the host
path below with your actual `NEW_DIR`):

```text
mount c "C:\GAMES\BB110"
c:
START.COM
```

The launcher shows **Language/Język**: `1 English`, `2 Polski`. The second
screen offers **Original version / Smooth scroll** in English or **Wersja
oryginalna / Płynne przewijanie** in Polish. It starts VGA directly, without
the old RUNME/cracktro menu or an EGA/intro choice.

For English smooth scrolling alone, select English → Smooth scroll.
Alternatively, from the mounted output root:

```text
cd ENSMOOTH
1.EXE
```

The other profile directories can also be started directly with `1.EXE`.

Recommended DOSBox-X settings (historically tested on 2026.01.02):

```ini
[dosbox]
machine=svga_s3
memsize=16

[cpu]
core=normal
cycles=fixed 20000
```

About **12000 cycles or more** are needed for full speed (~23 fps); 3000 is
too slow for both original and smooth scrolling. Smooth mode uses 1-pixel
camera precision in both axes, changes enemy activation, and makes recorded
demos lose sync after about 60 seconds. Two-player mode, character switching
and real hardware are unconfirmed. See [compatibility](compatibility.md).

## Troubleshooting and returning to the original

- **Output already exists:** choose a different, nonexistent `NEW_DIR`.
  Do not install over the source or an earlier output.
- **Source check fails:** use a clean copy of the exact supported edition;
  do not bypass validation or mix files from different editions.
- **You previously applied patch 1.0:** restore that copy using the **old 1.0
  installer** or obtain a clean copy. Do not use a patched 1.0 directory as
  the new source. The new installer rejects old format-1 patches and the
  `--restore` option, with migration instructions.
- **You want to undo 1.1.0:** there is no `--restore` in the new format.
  The source was never changed; run it again or discard only the generated
  output directory.
- **You cannot open the release link:** it requires private-repository access;
  ask for access or a separately supplied patch ZIP, not game files.

See [compatibility and tests](compatibility.md) for the recorded 1.1.0 test
scope and remaining limitations. `tests/results/latest` contains historical
results for earlier builds; it is not the acceptance report for this release.

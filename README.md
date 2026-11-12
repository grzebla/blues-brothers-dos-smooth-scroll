# The Blues Brothers DOS — Smooth Scroll

**[Polski](README.pl.md)** · English

A **smooth-scrolling mod** for **The Blues Brothers (1991, DOS)**. The camera follows the player at 1-pixel precision in both axes.

Play in the original English, or enable the **optional Polish translation**. A startup menu lets you choose the language and switch between smooth and original scrolling. All options run in VGA.

**[Download patch v1.1.0](https://github.com/grzebla/blues-brothers-dos-smooth-scroll/releases/download/v1.1.0/blues-brothers-1.1.0-patch.zip)** · [Release page](https://github.com/grzebla/blues-brothers-dos-smooth-scroll/releases/tag/v1.1.0)

This is a patch, **not the full game**. You need your own copy of the supported game edition.

## What you need

- A clean copy of the **English DOS hard-disk TDT/TRSI edition**. Other editions are not supported; the installer checks your files automatically.
- [Python 3.8+](https://www.python.org/downloads/) to install the patch. No extra Python packages are needed.
- [DOSBox-X](https://dosbox-x.com/) to play. Tested with **2026.10.01 SDL2**.

## 1. Download and extract

Download the patch ZIP linked above and extract it. **You do not need to clone this repository or build anything.**

The repository is currently private, so download links require access. You can also use a patch ZIP shared with you directly.

## 2. Install the patch

Open a terminal in the extracted patch folder — **not in DOSBox**. Run:

```sh
python apply_patch.py "C:\GAMES\BLUES" --output "C:\GAMES\BB110"
```

Replace the example paths with:
- `C:\GAMES\BLUES` — your original game folder.
- `C:\GAMES\BB110` — a new folder for the patched game. It must **not exist yet**, and its parent folder must exist. Keep it outside the original game folder.

On macOS/Linux, use your system's paths and `python3` instead of `python`.

**Your original game stays untouched.** The new folder contains all four combinations; you choose one at launch.

## 3. Start playing

Open DOSBox-X and enter the following, using the output folder from step 2:

```text
mount c "C:\GAMES\BB110"
c:
START.COM
```

The menu asks you to choose:
1. **Language:** `1` English or `2` Polski.
2. **Scrolling:** `1` original or `2` smooth.

**For the smooth-scroll mod, choose English → Smooth scroll (`1`, then `2`).** To add the Polish translation, choose Polski → Płynne przewijanie (`2`, then `2`).

## Need help?

- [Full installation guide and troubleshooting](docs/install.md)
- [Supported game edition, emulator settings and compatibility](docs/compatibility.md)
- [About the smooth-scroll mod](mods/smooth_scroll/README.md)

Smooth scrolling changes when enemies activate and makes recorded demos lose sync. Two-player mode, character switching and real hardware have not been verified.

<details>
<summary>For developers: build from source</summary>

Requires Python 3, Pillow, numpy and NASM (`nasm`).

```sh
git clone https://github.com/grzebla/blues-brothers-dos-smooth-scroll.git
cd blues-brothers-dos-smooth-scroll
python3 -m pip install Pillow numpy
```

Place your clean, supported game files in `original/`, then build the English game with smooth scrolling:

```sh
python3 tools/build.py --source original --locale en --scroll smooth --output build/en-smooth
```

Run `1.EXE` from `build/en-smooth/game/` in DOSBox-X. Use `--locale pl` to add the Polish translation or `--scroll original` for original scrolling. This builds one combination, without the selection menu.

[Translation strings](localization/pl/strings.json) · [Formats and limits (Polish)](docs/file-formats.md) · [Engine analysis (Polish)](docs/analysis.md)

</details>

## License

Project code: **MIT**. Polish translation: **CC BY 4.0**. The original game remains © 1991 Titus Interactive. See [LICENSE](LICENSE).

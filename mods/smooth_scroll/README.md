# Smooth-scroll mod

[Polski](README.pl.md) · [Project overview](../../README.md)

The original DOS game scrolls in bursts of 16 px, moving the camera roughly
half a screen when the player reaches the edge. This mod follows the player
continuously, with **1-pixel precision in both axes**:

- Horizontal dead zone: screen x=128–192. Tiles are composed on an 8 px byte
  boundary, then shifted by the remaining 0–7 px.
- Vertical dead zone: y=88–136; movement is also pixel-precise.
- Camera movement is capped at 16 px per frame, as in the original.

## Play in English or Polish

Use the **1.1.0 release patch**, not a developer build:
[installation](../../docs/install.md). It requires only Python 3.8+ for the
installer and your own supported English DOS hard-disk TDT/TRSI game.
All 50 `KNOWN_FILES` are validated; matching just `1.EXE` is not enough.
The base EXE is 196608 bytes, SHA-256
`769ee254b154a9444205524ec4b28a8147a372ac5b2cee2e25fcd83aa90d0add`.

Install into a new, nonexistent output directory whose parent already exists:

```sh
python apply_patch.py SOURCE --check
python apply_patch.py SOURCE --output NEW_DIR
```

The source stays untouched. The output contains `START.COM` and four complete
profiles: `ENORIG`, `ENSMOOTH`, `PLORIG`, `PLSMOOTH`. In `START.COM`, choose
English → Smooth scroll, or enter `ENSMOOTH` and run `1.EXE` directly.
**English smooth modifies only `1.EXE`; there are no Polish text, graphics or
fonts.** Polish → Płynne przewijanie selects `PLSMOOTH`. Both original-scroll
profiles remain available. All choices launch VGA without the old cracktro
menu. There is no `--variant` option and no new-format `--restore`.

## Developer build

For clone setup and dependencies (Pillow, numpy, NASM), see the
[main README](../../README.md#build-from-a-clone-developers-only).
The mod can be built independently of Polish localization:

```sh
python3 tools/build.py --source original --locale en --scroll smooth --output build/en-smooth
python3 tools/build.py --source original --locale pl --scroll smooth --output build/pl-smooth
```

Defaults remain Polish + smooth. Use `--scroll original` to disable the mod;
`--classic-scroll` remains an alias, not a test-only restriction.
For low-level development only, the EXE patcher checks bytes at its change
sites, not the full 50-file base validated by the release installer:

```sh
python3 mods/smooth_scroll/apply.py INPUT.EXE OUTPUT.EXE
```

This requires NASM and is not a claim of support for other editions.

## Implementation map

| Location | Original | Mod |
|---|---|---|
| `01DC:145F` | 16 px steps using mask `[2886]` set in `0739:0C7C` | `camera`: tracks player object 39/40, fields `+12h`/`+16h` |
| `01DC:1502` | VRAM `4000h` ring-buffer view, four rectangles via `0AB2:011D` | `redraw`: whole view each frame, VGA latch copies from tile sheets `6000h`/`8000h`; unaligned X uses a 41-byte row in `4000h`, then `shift` bit-shifts it onto the page |
| `003A:0C15` | Foreground tile list on a 16 px screen grid | World-coordinate list encoded for `fgblit` |
| `0351:19CB` | `0B8F:0008`: unclipped 16×16 tile | `fgblit`: bit shifting and viewport-edge clipping |
| `0B8F:0152` | Write a tile into the ring buffer | `retf`; `4000h` is now the composition buffer |

`seg01dc.asm` replaces three sections of segment 01DC (ring-buffer routines,
camera step, view composition); `seg003a.asm` replaces the foreground list.
Relocations in overwritten areas are redirected to unused `reloc_scratch`
so the DOS loader does not overwrite the new code. Project-authored scrolling
code and relocation changes are included in the patch; see [LICENSE](../../LICENSE).

## Side effects and test status

- Enemies activate relative to the camera. Recorded `DEMO*.BIN` input loses
  sync; the level-1 demo diverges after about **60 seconds**.
- CPU shifting processes about 25 KB per frame. Historical DOSBox-X results
  reached ~23 fps at 12000 cycles; at 3000, the original was ~12 fps and the
  mod ~10 fps. Hardware pel panning would also move the HUD, which is only
  redrawn when it changes.
- Recommended/tested emulator settings: **DOSBox-X 2026.01.02**,
  `machine=svga_s3`, `memsize=16`, `core=normal`, `cycles=fixed 20000`.
- **Two-player mode, character switching (`[288D]`) and real hardware remain
  unconfirmed.**
- Release 1.1.0 level-1 camera tests passed in **both languages**: 200 horizontal
  changes in Polish, 201 in English; deltas −6 to −1 px, maximum absolute delta
  6 px. These sample a recorded demo, not a natural playthrough or a two-player
  test. See the [English report](../../tests/results/release-1.1.0-en/report.md),
  [Polish engine report](../../tests/results/release-1.1.0-engine/report.md)
  and [compatibility](../../docs/compatibility.md).
- Automated DOSBox-X tests require Varlock and run with SDL dummy video/audio:
  no host windows, focus changes or audible output. Captured audio remains
  available for assertions; the game distributed to players is not muted.

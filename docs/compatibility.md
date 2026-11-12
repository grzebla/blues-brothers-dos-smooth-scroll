# Compatibility and tests

[Polski — detailed historical record](compatibility.pl.md) ·
[Installation 1.1.0](install.md)

## Supported release scope

Only the **English DOS hard-disk TDT/TRSI edition** is supported. Its `1.EXE`
is **196608 bytes**, SHA-256:

```text
769ee254b154a9444205524ec4b28a8147a372ac5b2cee2e25fcd83aa90d0add
```

Validation covers **all 50 files in `KNOWN_FILES`**, not just that executable.
No compatibility with arbitrary editions is claimed.

Installation into a new, nonexistent output directory whose parent already
exists leaves the source untouched. The result is `START.COM` plus complete `ENORIG`, `ENSMOOTH`,
`PLORIG` and `PLSMOOTH` directories. English smooth scrolling modifies only
`1.EXE`, with no Polish localization. The launcher selects language, then
scrolling, and always starts VGA without the old cracktro menu. You can also
run `1.EXE` directly inside a profile directory.

## Release 1.1.0 checks — 2026-11-12

| Scope | Result and evidence |
|---|---|
| Tools and installer | **23/23 passed**; four-profile installation, full source validation, failure cleanup, isolated Python without site-packages, reproducible ZIP. [Report](../tests/results/release-1.1.0-tools/report.md). |
| Launcher | **13/13 passed**: four real game boots with correct language and recorded audio; four fixture selections, Esc/back/invalid keys, CWD/drive restoration, missing EXE and EGA rejection. [Report](../tests/results/release-1.1.0-launcher/launcher-report.md). |
| Polish engine | `boot`, `all_levels`, `direct_exe`, `smooth_scroll` passed. All six levels loaded with correct palettes/HUD and returned to selection after **forced** completion, not a natural playthrough. [Report](../tests/results/release-1.1.0-engine/report.md). |
| English smooth scrolling | Level-1 demo: 201 horizontal camera changes; deltas −6 to −1 px; no jumps above 16 px/sample. Polish: 200 changes with the same delta range. [English report](../tests/results/release-1.1.0-en/report.md). |
| Classic demo comparison | **Passed on rerun**: 200/391 samples identical; all remaining differences explained by localization/fade, **0 unexplained**. The scenario independently builds Polish **original scrolling**; it does not compare smooth gameplay against the original. [Rerun report](../tests/results/release-1.1.0-regression/report.md). |

Current launcher tests and the classic-demo rerun used **DOSBox-X 2026.10.01 SDL2**, commit `b6abbd5`,
macOS arm64, SVGA S3, 16 MB, normal core and fixed 20000 cycles. The engine
batch and camera measurements used **2026.01.02 SDL1**. All ran with Varlock,
SDL dummy video/audio and muted host output: **no windows or focus stealing**.
Capture still contains sound; the distributed game is not muted.

DOSBox-X 2026.01.02 suffered surface-renderer crashes during dummy-video mode
changes, leaving incomplete AVI files. Those attempts were not counted as
passes. Use `--dosbox /path/to/dosbox-x` with 2026.10.01 SDL2 for headless tests;
there is no fallback to a visible window. Both test runners accept that option.
The final menu screenshots were visually reviewed: centered, legible, correct
Polish glyphs and no blocking artifacts.

`tests/results/latest/report.md` and the section below remain **historical**.
Old in-place installation, backup and restore checks do not validate the new
format. The historical Polish measurements need not match every `latest` run.

## Historical test environment / recommended settings

| Component | Version / setting |
|---|---|
| Emulator | DOSBox-X **2026.01.02**, SDL1, macOS arm64 |
| Machine | `machine=svga_s3`, `memsize=16` |
| CPU | `core=normal`, `cycles=fixed 20000` |
| Sound | Sound Blaster 16 + OPL (DOSBox-X defaults), PC Speaker |
| Host tools | macOS Darwin 27, Python 3.9.6, Pillow 10, numpy 1.24 |
| Game | Supported `original/` edition, earlier `build/game` output |

Full speed (~23 fps) needs about **12000 cycles or more**. At 3000 cycles,
both the original and smooth versions are too slow. For 1.1.0, start
`START.COM` or a profile's `1.EXE`, not RUNME.

## What the historical tests covered

The DOSBox-X harness copied the game to a working directory, injected keys
with `AUTOTYPE`, captured video/audio with `DX-CAPTURE /V /A`, decoded ZMBV
with `tests/zmbv.py` for exact colors, compared pixels using
`tests/dosbox_harness.py`, and read DOS output from `-log-con`.
Some scenarios used **test-only patches**, never shipped to players:
forced level completion/game over, starting-level/player-position changes,
bonus-room tiles moved near the start, and swapped error-message entries.

The following were reported as passed **for earlier builds only**:

| Historical scenario | Evidence and limits |
|---|---|
| `boot`, `direct_exe` | Title screen, Polish character selection, audio and old RUNME menu; direct `1.EXE` startup. |
| `all_levels` | All six levels, palettes, Polish map, HUD sprites and return to selection, using forced completion. Not a natural playthrough. |
| `gameover` | KONIEC GRY sprite through a forced drawing branch, not natural loss of all lives. |
| `mag_store`, `mag_music`, `mag_mirror`, `ville_plaque` | Polish signs and reflections verified pixel-for-pixel using test patches. |
| `insert_disk` | WŁÓŻ DYSK II prompt with AVTMAG.SQV removed. |
| `runme_ega`, `console` | Legacy menu/error behavior; the memory error used swapped table entries. Not tests of START.COM. |
| `demo_regression` | **Original scrolling** (`--classic-scroll`): 187/390 samples identical, no unexplained differences. Does not apply to smooth scrolling. |
| `smooth_scroll` | Earlier Polish level-1 demo: 201 horizontal camera changes, deltas −6 to −1 px, max absolute delta 6 px. Not four-profile acceptance. |
| `polish_glyphs` | All nine Polish uppercase letters rendered via a pangram. |

The classic-scroll demo comparison used 390 samples at 0.25-second intervals.
Remaining differences were localized artwork/menu text, palette animation
or a fade frame; player/enemy positions and demo progression matched.
Audio-envelope correlation was 0.988 (50 ms start offset), with RMS
6419 vs 6423. Sound files and sound code are not modified.

The earlier documentation also recorded 12 tool tests: version detection,
round-trip compression of 34 resources, ILBM/SQV, DOS decoder overrun model,
string schema/font coverage/message limits, deterministic builds, source
preservation, modified-file rejection and the **old** patch packaging workflow.
Those are not new-format results. Full historical detail, patch addresses
and measurements are preserved in [the Polish record](compatibility.pl.md).
Historical artifacts: `tests/results/latest/report.md` and `*.png`.

## Known limitations

- **Smooth scrolling:** 1-pixel camera precision in both axes changes enemy
  activation. Recorded level-1 demos lose sync after about **60 seconds**.
  Compare gameplay regression with `--scroll original` (alias
  `--classic-scroll`) and test smooth movement separately. Developer defaults
  remain Polish + smooth; the release includes all four choices.
- **Two-player mode, character switching and real hardware are unconfirmed.**
  CPU-based 0–7 px background shifts may be slower on a slow 286. Resource
  sizes respect reverse-engineered engine buffers, not hardware certification.
- **DOS errors use ASCII deliberately:** BRAK EGA/VGA. and BRAK RAM-U.
  ROM fonts on non-VGA cards did not render CP852 correctly. Normal play
  requires VGA.
- **OPEN stays English:** a 16 px tile with 3×5 letters cannot fit the Polish
  equivalent without changing the map; its translation entry is `review`.
- **+1 ŻYCIE:** sprite 134 was widened to 32 px with 16 px alignment; the
  frame table and following HUD sprites were checked, but naturally collecting
  the extra life still needs a manual check.
- **KONIEC GRY** was forced by a test patch; natural loss of all lives remains
  to be checked. The disk prompt's engraved Superclarendon rendering is
  similar to, not identical to, the original hand-drawn lettering.
- Resource compression uses a different Huffman tree, so bytes differ while
  decoded pixels remain unchanged outside localized artwork; sizes are
  comparable or smaller.
- **Legacy menu history only:** RUNME's EGA option did not start the game even
  in the original; VGA/direct `1.EXE` did. The TDT/TRSI `INTRO.EXE` was not
  translated. RUNME header alignment used tabs with fixed byte lengths.
  **START.COM bypasses that menu and always launches VGA.**

## Pending 1.1.0 manual checks

No item below is claimed completed:

- [ ] New-directory installation, all 50 source files unchanged, rejection of
      unsupported sources and existing output directories.
- [ ] Both launcher languages and both scrolling choices; correct working
      directories, VGA, no cracktro menu.
- [ ] All four profiles independently start via `1.EXE`; ENORIG is unchanged,
      ENSMOOTH changes only `1.EXE` and has no Polish localization.
- [ ] Title, music, character selection, localized map/signs/reflections/plaque.
- [ ] Natural extra-life pickup, game over, six-level completion and return.
- [ ] Pixel-precise movement in both axes, map/foreground edges, separate
      original-scroll demo regression.
- [ ] Two-player mode, character switching and real hardware.
- [ ] Optional missing-AVTMAG.SQV prompt, in a test copy only.

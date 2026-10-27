# Mod: płynne przewijanie

Oryginalna wersja DOS przewija ekran seriami skoków po 16 px. Gdy postać
dojdzie do krawędzi, kamera „dojeżdża” o pół ekranu. Ten mod zmienia
kamerę tak, żeby podążała za postacią na bieżąco:

- **poziomo** kamera przesuwa się co 1 px. Tło jest składane z kafli
  z dokładnością do bajtu (8 px), a resztę, 0–7 px, robi przesunięcie
  bitowe. Martwa strefa to x 128–192 na ekranie;
- **pionowo** przesuwa się co 1 px. Martwa strefa to y 88–136;
- ruch kamery jest ograniczony do 16 px na klatkę, tak jak w oryginale.

Płynne przewijanie jest częścią polskiej wersji: `tools/build.py` nakłada je
zawsze, a patch dla graczy zawiera zmienione bajty. Przełącznik
`--classic-scroll` służy wyłącznie testom (regresja dema). Mod można też
nałożyć osobno, np. na 1.EXE wersji angielskiej (sprawdza bajty tylko
w miejscach, które zmienia):

```sh
python3 mods/smooth_scroll/apply.py WEJŚCIE.EXE WYJŚCIE.EXE   # wymaga nasm
```

Test w DOSBox-X: `python3 tests/run_dosbox_tests.py --only smooth_scroll`.

## Jak to działa

| Miejsce | Oryginał | Mod |
|---|---|---|
| `01DC:145F` | kroki po 16 px wg maski `[2886]` ustawianej w `0739:0C7C` | `camera` — śledzenie gracza (obiekt 39/40, pola `+12h`/`+16h`) |
| `01DC:1502` | składanie widoku z pierścieniowego bufora kafli w VRAM `4000h` (4 prostokąty, `0AB2:011D`) | `redraw` — co klatkę cały widok z mapy, kopie przez zatrzaski VGA z arkuszy `6000h`/`8000h`; przy kamerze X niepodzielnej przez 8 widok 41 B/linię trafia do `4000h`, a `shift` przesuwa go bitowo na stronę |
| `003A:0C15` | lista kafli pierwszego planu w siatce ekranu (kamera wyrównana do 16 px) | lista w układzie świata, pozycja kodowana dla `fgblit` |
| `0351:19CB` | `0B8F:0008` — kafel 16x16 bez przycinania | `fgblit` — przesunięcie bitowe i przycinanie na krawędziach widoku |
| `0B8F:0152` | zapis kafla do bufora pierścieniowego | `retf` (obszar `4000h` jest buforem składania) |

Kod jest w `seg01dc.asm`, w trzech sekcjach w miejscach zastąpionego kodu
segmentu 01DC (procedury bufora pierścieniowego, krok kamery, składanie
widoku), oraz w `seg003a.asm`. Relokacje z nadpisanych obszarów są
przekierowane na nieużywane słowo `reloc_scratch`.

## Znane skutki uboczne

- **Dema tracą synchronizację.** Przeciwnicy aktywują się względem kamery,
  więc nagrane sterowanie (`DEMO*.BIN`) po pewnym czasie przestaje pasować
  do sytuacji na ekranie. W demie poziomu 1 widać to po ok. 60 s.
- **Wymagania CPU.** Przesunięcie bitowe kosztuje ok. 25 tys. bajtów na
  klatkę. W DOSBox-X przy `cycles=12000` gra ma pełne ~23 klatki/s, tak jak
  oryginał. Przy 3000 oba są za wolne: oryginał ok. 12, mod ok. 10 kl./s.
  Sprzętowy pel panning odpadł, bo przesuwałby paski HUD, a gra rysuje je
  tylko przy zmianie.
- Nie przetestowano jeszcze trybu dwóch graczy ani przełączania postaci
  (`[288D]`).

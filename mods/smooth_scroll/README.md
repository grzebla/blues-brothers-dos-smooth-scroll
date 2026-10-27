# Mod: płynne przewijanie (prototyp)

Oryginalna wersja DOS przewija ekran seriami skoków po 16 px. Gdy postać
dojdzie do krawędzi, kamera „dojeżdża” o pół ekranu. Ten mod zmienia
kamerę tak, żeby podążała za postacią na bieżąco:

- **poziomo** kamera przesuwa się krokami po 8 px (granulacja bajtu w trybie
  EGA 0Dh). Martwa strefa to x 128–192 na ekranie;
- **pionowo** przesuwa się co 1 px. Martwa strefa to y 88–136;
- ruch kamery jest ograniczony do 16 px na klatkę, tak jak w oryginale.

Mod jest niezależny od polonizacji, ale nakłada się na `1.EXE` po niej
(sprawdza bajty tylko w miejscach, które zmienia).

```sh
python3 mods/smooth_scroll/apply.py build/game/1.EXE work/smooth/1.EXE   # wymaga nasm
```

## Jak to działa

| Miejsce | Oryginał | Mod |
|---|---|---|
| `01DC:145F` | kroki po 16 px wg maski `[2886]` ustawianej w `0739:0C7C` | `camera` — śledzenie gracza (obiekt 39/40, pola `+12h`/`+16h`) |
| `01DC:1502` | składanie widoku z pierścieniowego bufora kafli w VRAM `4000h` (4 prostokąty, `0AB2:011D`) | `redraw` — co klatkę cały widok 320x160 prosto z mapy, kopie przez zatrzaski VGA z arkuszy `6000h`/`8000h` |
| `003A:0C15` | lista kafli pierwszego planu w siatce ekranu (kamera wyrównana do 16 px) | lista w układzie świata, pozycja kodowana dla `fgblit` |
| `0351:19CB` | `0B8F:0008` — kafel 16x16 bez przycinania | `fgblit` — przycinanie na krawędziach widoku |

Kod jest w `seg01dc.asm` (obszar po procedurach dorysowujących bufor
pierścieniowy, `01DC:116A-145E`) i w `seg003a.asm`. Bufor pierścieniowy jest
nadal aktualizowany przez grę (animacje kafli, zmiany mapy), ale nic go już
nie czyta. Relokacje z nadpisanych obszarów są przekierowane na nieużywane
słowo `reloc_scratch`.

## Znane skutki uboczne

- **Dema tracą synchronizację.** Przeciwnicy aktywują się względem kamery,
  więc nagrane sterowanie (`DEMO*.BIN`) po pewnym czasie przestaje pasować
  do sytuacji na ekranie. W demie poziomu 1 widać to po ok. 60 s.
- Krok poziomy wynosi 8 px. Pełna płynność co 1 px wymagałaby rejestru
  pel panning karty VGA oraz podziału ekranu (line compare), żeby nie
  przesuwać pasków HUD.
- Nie przetestowano jeszcze trybu dwóch graczy ani przełączania postaci
  (`[288D]`).

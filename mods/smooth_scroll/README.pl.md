# Mod: płynne przewijanie

[English](README.md) · [Opis projektu](../../README.pl.md)

Oryginalna gra DOS przewija ekran seriami skoków po 16 px. Gdy postać dojdzie
do krawędzi, kamera „dojeżdża” o około pół ekranu. Mod śledzi gracza na bieżąco,
z dokładnością **1 px w obu osiach**:

- Pozioma martwa strefa: x=128–192 na ekranie. Tło jest składane na granicy
  bajtu (8 px), a pozostałe 0–7 px realizuje przesunięcie bitowe.
- Pionowa martwa strefa: y=88–136; ruch również z dokładnością pikselową.
- Kamera przesuwa się maksymalnie o 16 px na klatkę, jak w oryginale.

## Gra po angielsku lub po polsku

Użyj **patcha z Release 1.1.0**, nie buildu dla twórców:
[instrukcja instalacji](../../docs/install.pl.md). Instalator wymaga tylko
Pythona 3.8+ oraz legalnie posiadanego obsługiwanego wydania angielskiego DOS
na dysk twardy TDT/TRSI. Sprawdza wszystkie 50 plików `KNOWN_FILES`, nie tylko
`1.EXE`. Bazowy EXE ma 196608 bajtów i SHA-256
`769ee254b154a9444205524ec4b28a8147a372ac5b2cee2e25fcd83aa90d0add`.

Zainstaluj do nowego, nieistniejącego katalogu, którego katalog nadrzędny już istnieje:

```sh
python apply_patch.py SOURCE --check
python apply_patch.py SOURCE --output NEW_DIR
```

Źródło pozostaje nienaruszone. Wynik zawiera `START.COM` i cztery kompletne
profile: `ENORIG`, `ENSMOOTH`, `PLORIG`, `PLSMOOTH`. W `START.COM` wybierz
English → Smooth scroll albo wejdź do `ENSMOOTH` i uruchom `1.EXE`.
**English smooth zmienia wyłącznie `1.EXE`; nie dodaje polskich tekstów,
grafik ani fontów.** Polski → Płynne przewijanie wybiera `PLSMOOTH`.
Dostępne pozostają oba profile z oryginalnym przewijaniem. Wszystkie wybory
uruchamiają VGA bez starego menu cracktra. Nie ma opcji `--variant` ani
`--restore` dla nowego formatu.

## Budowanie dla twórców

Klonowanie i zależności (Pillow, numpy, NASM) opisuje
[główny README](../../README.pl.md#budowanie-z-klona-repozytorium-tylko-dla-twórców).
Mod można zbudować niezależnie od polonizacji:

```sh
python3 tools/build.py --source original --locale en --scroll smooth --output build/en-smooth
python3 tools/build.py --source original --locale pl --scroll smooth --output build/pl-smooth
```

Domyślny build nadal jest polski z płynnym przewijaniem. Wyłączenie moda:
`--scroll original`; `--classic-scroll` pozostaje aliasem, nie opcją wyłącznie
do testów. Niskopoziomowy patcher EXE dla twórców sprawdza tylko bajty
w miejscach zmian, nie pełną bazę 50 plików weryfikowaną przez instalator:

```sh
python3 mods/smooth_scroll/apply.py WEJŚCIE.EXE WYJŚCIE.EXE
```

Wymaga NASM i nie oznacza obsługi innych wydań gry.

## Mapa implementacji

| Miejsce | Oryginał | Mod |
|---|---|---|
| `01DC:145F` | kroki po 16 px wg maski `[2886]` ustawianej w `0739:0C7C` | `camera`: śledzenie gracza, obiekt 39/40, pola `+12h`/`+16h` |
| `01DC:1502` | składanie widoku z bufora pierścieniowego VRAM `4000h`, cztery prostokąty przez `0AB2:011D` | `redraw`: cały widok co klatkę, zatrzaski VGA z arkuszy `6000h`/`8000h`; przy niewyrównanym X wiersz 41 B trafia do `4000h`, a `shift` przesuwa go bitowo na stronę |
| `003A:0C15` | lista pierwszego planu w siatce ekranu co 16 px | lista we współrzędnych świata, kodowana dla `fgblit` |
| `0351:19CB` | `0B8F:0008`: kafel 16×16 bez przycinania | `fgblit`: przesunięcie bitowe i przycinanie do widoku |
| `0B8F:0152` | zapis kafla do bufora pierścieniowego | `retf`; `4000h` jest teraz buforem składania |

`seg01dc.asm` zastępuje trzy sekcje segmentu 01DC (procedury bufora
pierścieniowego, krok kamery, składanie widoku), a `seg003a.asm` — listę
pierwszego planu. Relokacje nadpisanych obszarów są przekierowane na nieużywane
`reloc_scratch`, aby loader DOS nie zmieniał nowego kodu. Autorski kod
przewijania i zmiany relokacji są częścią patcha; zobacz [LICENSE](../../LICENSE).

## Skutki uboczne i stan testów

- Przeciwnicy aktywują się względem kamery. Nagrane sterowanie `DEMO*.BIN`
  traci synchronizację; demo poziomu 1 rozjeżdża się po ok. **60 s**.
- Przesunięcie bitowe przetwarza ok. 25 KB na klatkę. Historycznie DOSBox-X
  osiągał ~23 kl./s przy 12000 cykli; przy 3000 oryginał miał ~12 kl./s,
  mod ~10 kl./s. Sprzętowy pel panning przesuwałby też HUD, który gra
  przerysowuje tylko przy zmianie.
- Zalecany/testowany emulator: **DOSBox-X 2026.01.02**, `machine=svga_s3`,
  `memsize=16`, `core=normal`, `cycles=fixed 20000`.
- **Tryb dwóch graczy, przełączanie postaci (`[288D]`) i prawdziwy sprzęt
  pozostają niepotwierdzone.**
- Testy kamery poziomu 1 dla wydania 1.1.0 przeszły **w obu językach**:
  200 zmian poziomych w PL, 201 w EN; przesunięcia −6 do −1 px,
  maksymalna wartość bezwzględna 6 px. To próbki nagranego dema, nie naturalne
  przejście gry ani test dwóch graczy. Zobacz [raport EN](../../tests/results/release-1.1.0-en/report.md),
  [raport silnika PL](../../tests/results/release-1.1.0-engine/report.md)
  i [zgodność](../../docs/compatibility.pl.md).
- Automatyczne testy DOSBox-X wymagają Varlock i sterowników SDL dummy:
  bez okien, zmiany fokusu i słyszalnego dźwięku na hoście. Audio nadal
  jest nagrywane do asercji; gra przekazywana graczom nie jest wyciszona.

# Zgodność i testy

## Środowisko testowe

| Element | Wersja / ustawienie |
|---|---|
| Emulator | DOSBox-X 2026.01.02 (SDL1, macOS arm64) |
| Maszyna | `machine=svga_s3`, `memsize=16`, `cycles=fixed 20000`, `core=normal` |
| Dźwięk | Sound Blaster 16 + OPL (domyślne DOSBox-X), PC Speaker |
| Host | macOS (Darwin 27), Python 3.9.6, Pillow 10, numpy 1.24 |
| Gra | wydanie z `original/` (patrz docs/analysis.md), build z `build/game` |

Zalecana konfiguracja DOSBox / DOSBox-X: domyślna maszyna VGA/SVGA, około
15000-25000 cykli. Grę uruchamia się przez `RUNME` → `[2] - VGA` albo
`1.EXE`.

## Jak działają testy w DOSBox-X

`tests/run_dosbox_tests.py` dla każdego scenariusza: kopiuje grę do katalogu
roboczego, uruchamia DOSBox-X z wygenerowaną konfiguracją, wstrzykuje klawisze
poleceniem `AUTOTYPE`, nagrywa obraz i dźwięk poleceniem `DX-CAPTURE /V /A`,
a następnie dekoduje nagranie własnym dekoderem ZMBV (`tests/zmbv.py`,
dokładne kolory - dekoder ffmpeg przekłamywał kanały) i porównuje piksele
z oczekiwanymi grafikami (`tests/dosbox_harness.py`). Wyjście konsoli DOS
jest czytane z logu (`-log-con`).

Niektóre ekrany wymagają wielu minut zręcznej gry. Aby je sprawdzić
automatycznie, scenariusze oznaczone **[łatka testowa]** używają
`tests/test_patches.py` - zmian **tylko w kopii testowej** (nigdy w buildzie
ani w patchu):

| Łatka | Miejsce | Działanie |
|---|---|---|
| `auto_complete` | `0351:04E2` (plik 0x5BF2) | warunek "poziom ukończony" zawsze prawdziwy - po 50 klatkach gra przechodzi do kolejnego poziomu; pozwala przejść całą grę |
| `force_gameover` | `0351:0553` (plik 0x5C63) | skok do gałęzi rysowania klatki 127 (oryginalna procedura gry) |
| `start_level` | `003A:01C0` (plik 0x2764) | numer poziomu startowego |
| `player_start` | tablice źródłowe pozycji (DS:270D/24CF i DS:2521+82·L/22E3+82·L) | pozycja startowa gracza przy szyldzie |
| `map_edit` | kopia `*.SQL` | wstawienie kafli z pokoi bonusowych obok startu (kamera nie wjeżdża do tych pokoi bez drzwi) |
| `swap_error_messages` | tablica `DS:3384` | zamiana wpisów, by test karty CGA wypisał komunikat "brak pamięci" |

## Wyniki (pełny przebieg)

| Scenariusz | Zakres | Wynik | Sprawdzenia |
|---|---|---|---|
| `boot` | Start: menu RUNME → ekran tytułowy → wybór postaci; dźwięk | **zaliczony** | ✔ nagranie powstało — hard_000.avi, 1_000.avi<br>✔ ekran tytułowy wyświetlony (PRES.SQZ) — zgodność 1.000 w t=7.41936 s<br>✔ polski pasek wyboru postaci (CHOIX.SQZ, linie 190-199) — zgodność 1.000 w t=30.89022 s<br>✔ dźwięk/muzyka nagrane (niezerowy sygnał) — RMS 6255, szczyt 32768<br>✔ menu RUNME.COM po polsku |
| `all_levels` | [łatka testowa] przejście wszystkich 6 poziomów i powrót do wyboru postaci | **zaliczony** | ✔ poziom 1 wczytany i wyświetlony (paleta poziomu)<br>✔ poziom 2 wczytany i wyświetlony (paleta poziomu)<br>✔ poziom 3 wczytany i wyświetlony (paleta poziomu)<br>✔ poziom 4 wczytany i wyświetlony (paleta poziomu)<br>✔ poziom 5 wczytany i wyświetlony (paleta poziomu)<br>✔ poziom 6 wczytany i wyświetlony (paleta poziomu)<br>✔ ikony HUD (klatki 135-144 za poszerzoną klatką 134) poprawne we wszystkich poziomach — p1: 1.000, p2: 1.000, p3: 1.000, p4: 1.000, p5: 1.000, p6: 1.000<br>✔ mapa INTER z polskimi szyldami przed poziomami — 10 wystąpień<br>✔ po ukończeniu poziomu 6 gra wraca do ekranu wyboru postaci — inny -> CHOIX -> inny -> INTER -> inny -> czarny |
| `gameover` | [łatka testowa] ekran końca gry | **zaliczony** | ✔ sprite "KONIEC GRY" wyświetlony w grze — zgodność 1.000 w (80,77), t=33.116028 s |
| `mag_store` | [łatka testowa] neon SKLEP w poziomie 1 | **zaliczony** | ✔ SKLEP neon (MAG.CK2 kafle 50-51) — zgodność 1.000 w (160,30), t=32.930544000000005 s |
| `mag_music` | [łatka testowa] neon PŁYTY w poziomie 1 | **zaliczony** | ✔ PŁYTY neon (MAG.CK2 kafle 96-97) — zgodność 1.000 w (160,30), t=32.930544000000005 s |
| `mag_mirror` | [łatka testowa] lustrzane neony w pokojach bonusowych | **zaliczony** | ✔ SKLEP odbicie (MAG.CK2 kafle 126-127) — zgodność 1.000 w (96,94), t=32.916276 s<br>✔ PŁYTY odbicie (MAG.CK1 kafle 79+120) — zgodność 1.000 w (160,94), t=32.916276 s |
| `ville_plaque` | [łatka testowa] tabliczka PROGRAMISTA w poziomie 5 | **zaliczony** | ✔ PROGRAMISTA tabliczka (VILLE.CK1 kafle 114-117) — zgodność 1.000 w (96,110), t=32.844936000000004 s |
| `insert_disk` | ekran zmiany dyskietki (brak AVTMAG.SQV) | **zaliczony** | ✔ polski ekran "WŁÓŻ DYSK II" — zgodność 1.000 w t=20.545920000000002 s |
| `runme_ega` | opcja [1] EGA - porównanie z oryginałem | **zaliczony** | ✔ oryginał i wersja PL uruchamiają te same programy — oryginał: ['hard'], PL: ['hard']<br>✔ komunikat po wyjściu przetłumaczony (zrzut: runme_exit_message.png) |
| `console` | komunikaty konsolowe (RUNME, CGA, brak pamięci [łatka testowa]) | **zaliczony** | ✔ konsola RUNME: runme.line_presents — 'P R Z E D S T A W I A'<br>✔ konsola RUNME: runme.line_title — 'Blues Brothers firmy TITUS'<br>✔ konsola RUNME: runme.line_intro — '[3] - Intro TDT/TRSI...'<br>✔ konsola RUNME: runme.exit_message — 'Kto inny da wam takie rzeczy?'<br>✔ 1.EXE na karcie CGA: 'BRAK EGA/VGA.' — BRAK EGA/VGA.; C:\>exit<br>✔ komunikat nr 1 z tablicy (brak pamięci): 'BRAK RAM-U.' — BRAK RAM-U.; C:\>exit |
| `demo_regression` | regresja: tryb demo oryginał vs PL, klatka po klatce | **zaliczony** | ✔ wszystkie różnice wynikają z lokalizacji (tekst, napisy, neony) — niewyjaśnione: []<br>✔ większość klatek identyczna z oryginałem — 187/390 |
| `polish_glyphs` | wszystkie polskie wielkie litery w grze (pangram) | **zaliczony** | ✔ pangram 'ZAŻÓŁĆ GĘŚLĄ' / 'JAŹŃ ĄĆĘŁŃÓŚŹŻ' wyświetlony w grze — zgodność 1.000, t=30.861684 s |
| `direct_exe` | bezpośrednie uruchomienie 1.EXE | **zaliczony** | ✔ 1.EXE uruchomione bezpośrednio pokazuje polski ekran wyboru — zgodność 1.000, t=28.050888 s |

Dodatkowo porównano dźwięk nagrany w scenariuszu regresji dema: korelacja
obwiedni głośności ścieżek oryginału i wersji PL wynosi 0,988 (przesunięcie
50 ms wynika z niezsynchronizowanego startu nagrań), RMS 6419 vs 6423 -
muzyka i efekty nie zostały naruszone (pliki dźwiękowe i kod nie są zmieniane).

Regresja dema: 390 próbek co 0,25 s; 187 klatek identycznych bit w bit,
pozostałe różnią się wyłącznie w zlokalizowanych miejscach (menu tekstowe,
pasek wyboru, szyldy mapy, neony poziomu 1), fazą animacji palety (różnica
tylko w kanale B) lub w 1 klatce wygaszania. Pozycje postaci, przeciwników
i przebieg dema są identyczne.

Pełny raport: `tests/results/latest/report.md`, arkusze klatek
i zrzuty: `tests/results/latest/*.png`.

### Testy narzędzi (`tests/test_tools.py`, 12 testów - wszystkie zaliczone)

Identyfikacja wersji, round-trip 34 skompresowanych zasobów (dekompresja →
kompresja → dekompresja), round-trip ILBM i SQV, model nadmiaru dekodera DOS,
schemat `strings.json`, pokrycie znaków fontów, dopasowanie komunikatów do
dostępnego miejsca, determinizm buildu (dwa buildy → identyczne SHA-256),
nienaruszalność `original/`, odmowa patchowania zmodyfikowanego pliku,
paczka dystrybucyjna (instalacja = build, ponowna instalacja, przywracanie,
odmowa dla obcego pliku, brak plików gry w paczce).

## Ograniczenia i znane zachowania

1. **Opcja [1] - EGA w menu RUNME nie uruchamia gry** - tak samo w oryginale
   (sprawdzone testem `runme_ega`); to cecha tego wydania (crack). Gra działa
   w trybie VGA (`[2]`) i po bezpośrednim uruchomieniu `1.EXE`.
2. **Komunikaty konsolowe bez polskich znaków** ("BRAK EGA/VGA.", "BRAK
   RAM-U."). Komunikat o karcie pojawia się na CGA/MDA/Hercules, gdzie font
   jest w ROM karty - test w DOSBox-X pokazał, że CP852 dałoby tam
   "B¥ŤD GRAFIKI". Dobrano sformułowania poprawne bez diakrytyków.
3. **Tabliczka "OPEN"** (kafel 16 px, litery 3x5) pozostała po angielsku -
   polskie odpowiedniki nie mieszczą się, a zmiana mapy poziomu wykracza poza
   lokalizację. Oznaczona w `strings.json` jako `review`.
4. **"+1 ŻYCIE"** - klatka 134 poszerzona do 32 px. Zweryfikowano: poprawne
   zbudowanie tablicy klatek (ikony HUD z klatek 135-145 wyświetlają się
   poprawnie we wszystkich poziomach), wyrównanie do szerokości 16 jak w innych
   klatkach. Samo pojawienie się napisu po zebraniu dodatkowego życia nie
   zostało wywołane w teście automatycznym - **do ręcznej weryfikacji**.
5. **Ekran "KONIEC GRY"** sprawdzony przez wymuszenie gałęzi (łatka testowa);
   naturalna utrata wszystkich żyć - **do ręcznej weryfikacji**.
6. **Ekran "WŁÓŻ DYSK II"** pojawia się tylko, gdy brakuje `AVTMAG.SQV`
   (wersja dyskietkowa). Litery zostały odtworzone krojem Superclarendon
   z proceduralnym stylem grawerowanym (podobnym, ale nie identycznym
   z ręcznie rysowanym oryginałem).
7. **Prawdziwy sprzęt** nie był testowany. Ryzyko jest małe: kod gry nie jest
   zmieniany (poza 40 bajtami danych komunikatów), a wszystkie zasoby
   mieszczą się w limitach buforów wyznaczonych z kodu (docs/analysis.md).
8. Kompresja zasobów różni się bajtowo od oryginału (inne drzewo Huffmana),
   ale po dekompresji dane są identyczne co do piksela poza napisami;
   rozmiary plików są zbliżone lub mniejsze.
9. Cracktro (`INTRO.EXE`, opcja `[3]`) nie jest tłumaczone - to dodatek grupy
   crackerskiej, nie część gry.

## Lista kontrolna ręcznej weryfikacji

Do wykonania na DOSBox / prawdziwym PC (zaznacz po sprawdzeniu):

- [ ] `RUNME` → menu po polsku ("P R Z E D S T A W I A", "firmy TITUS"),
      `[2]` uruchamia grę.
- [ ] Ekran tytułowy, muzyka gra.
- [ ] Ekran wyboru: "← WYBIERZ POSTAĆ → NACIŚNIJ FIRE, BY GRAĆ" czytelne,
      wybór Jake/Elwood/obaj strzałkami działa, fire startuje grę.
- [ ] Mapa: szyldy "CHEMIA" i "SKLEP".
- [ ] Poziom 1: neony "SKLEP" i "PŁYTY" na fasadach, odbicia w pokojach
      bonusowych pod sklepem.
- [ ] Zebranie dodatkowego życia → "+1 ŻYCIE" wyświetla się poprawnie.
- [ ] Poziom 5, pokój bonusowy (lewy dolny róg mapy): tabliczka
      "Y.BERTHELOT / PROGRAMISTA".
- [ ] Utrata wszystkich żyć → "KONIEC GRY", powrót do wyboru postaci.
- [ ] Przejście gry do koncertu (poziom 6) i powrót do wyboru postaci.
- [ ] Wyjście z gry → komunikat "Kto inny da wam takie rzeczy?".
- [ ] (opcjonalnie) usunięcie `AVTMAG.SQV` → ekran "WŁÓŻ DYSK II".

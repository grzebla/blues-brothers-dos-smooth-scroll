# Zgodność i testy

[English](compatibility.md) · [Instalacja 1.1.0](install.pl.md)

## Zakres wydania 1.1.0

Obsługiwana jest wyłącznie angielska wersja DOS na dysk twardy TDT/TRSI.
Bazowy `1.EXE`: **196608 bajtów**, SHA-256
`769ee254b154a9444205524ec4b28a8147a372ac5b2cee2e25fcd83aa90d0add`.
Walidacja obejmuje **wszystkie 50 plików `KNOWN_FILES`**, nie tylko EXE.
Nie deklarujemy zgodności z innymi wydaniami.

Instalacja do nowego, nieistniejącego katalogu (z istniejącym katalogiem
nadrzędnym) pozostawia źródło nienaruszone.
Wynik zawiera `START.COM` i kompletne profile `ENORIG`, `ENSMOOTH`, `PLORIG`,
`PLSMOOTH`. Profil `en-smooth` zmienia tylko `1.EXE`, bez polonizacji.
Launcher wybiera język, potem przewijanie, i zawsze uruchamia VGA bez starego
menu cracktra. Bezpośrednie uruchomienie `ENSMOOTH/1.EXE` jest alternatywą
dla wyboru English → Smooth scroll.

## Testy wydania 1.1.0 — 2026-11-12

| Zakres | Wynik i dowód |
|---|---|
| Narzędzia i instalator | **23/23 zaliczone**: cztery profile, pełna walidacja źródła, wycofanie stagingu po błędzie, izolowany Python bez site-packages, deterministyczny ZIP. [Raport](../tests/results/release-1.1.0-tools/report.md). |
| Launcher | **13/13 zaliczonych**: cztery rzeczywiste uruchomienia gry z właściwym językiem i nagranym audio; cztery wybory fixture, Esc/powrót/błędne klawisze, odtworzenie CWD/napędu, brak EXE i odmowa EGA. [Raport](../tests/results/release-1.1.0-launcher/launcher-report.md). |
| Silnik PL | `boot`, `all_levels`, `direct_exe`, `smooth_scroll` zaliczone. Sześć poziomów z poprawnymi paletami/HUD i powrotem do wyboru po **wymuszonym** ukończeniu — nie naturalne przejście gry. [Raport](../tests/results/release-1.1.0-engine/report.md). |
| Angielski smooth scroll | Demo poziomu 1: 201 zmian poziomych, przesunięcia −6 do −1 px, brak skoków powyżej 16 px/próbkę. W PL: 200 zmian z tym samym zakresem przesunięć. [Raport EN](../tests/results/release-1.1.0-en/report.md). |
| Porównanie klasycznego dema | **Zaliczone po powtórzeniu**: 200/391 próbek identycznych; pozostałe różnice wynikają z lokalizacji/zanikania, **0 niewyjaśnionych**. Scenariusz niezależnie buduje PL z **oryginalnym przewijaniem**, nie porównuje rozgrywki smooth z oryginałem. [Raport powtórzenia](../tests/results/release-1.1.0-regression/report.md). |

Bieżące testy launchera i powtórzenie klasycznego dema wykonano w
**DOSBox-X 2026.10.01 SDL2**, commit
`b6abbd5`, macOS arm64, SVGA S3, 16 MB, normal core, fixed 20000 cykli.
Zestaw silnika i pomiary kamery używały **2026.01.02 SDL1**. Wszystkie działały
przez Varlock ze sterownikami SDL dummy i wyciszonym wyjściem hosta:
**bez okien i przejmowania fokusu**. Nagrania nadal zawierają dźwięk;
wydawana gra nie jest wyciszona.

Wersja 2026.01.02 miała awarie renderera powierzchni przy zmianach trybu
z dummy video i pozostawiała niekompletne AVI. Nie zaliczono tych prób.
Do testów bezokienkowych użyj `--dosbox /ścieżka/do/dosbox-x` z 2026.10.01 SDL2;
nie ma fallbacku do widocznego okna. Oba skrypty testowe obsługują tę opcję.
Końcowe zrzuty menu sprawdzono wizualnie: poprawne wyśrodkowanie, czytelność
i polskie glify, brak blokujących artefaktów.

`tests/results/latest/report.md` i poniższy opis pozostają **historyczne**.
Dawne testy instalacji w miejscu, kopii zapasowej i przywracania nie potwierdzają
nowego formatu. Nie należy utożsamiać dawnych pomiarów z każdym przebiegiem `latest`.

## Środowisko historycznych testów i zalecenia

| Element | Wersja / ustawienie |
|---|---|
| Emulator | DOSBox-X 2026.01.02 (SDL1, macOS arm64) |
| Maszyna | `machine=svga_s3`, `memsize=16`, `cycles=fixed 20000`, `core=normal` |
| Dźwięk | Sound Blaster 16 + OPL (domyślne DOSBox-X), PC Speaker |
| Host | macOS (Darwin 27), Python 3.9.6, Pillow 10, numpy 1.24 |
| Gra | wydanie z `original/` (patrz [analysis.md](analysis.md)), wcześniejszy `build/game` |

To ustawienia zalecane również do gry. Pełne ~23 kl./s wymagają ok.
**12000 cykli lub więcej**; 3000 spowalnia także oryginał. W 1.1.0 używaj
`START.COM` albo `1.EXE` wewnątrz wybranego profilu, nie menu RUNME.

## Jak działały testy w DOSBox-X

`tests/run_dosbox_tests.py` kopiuje grę do katalogu roboczego, uruchamia
DOSBox-X z wygenerowaną konfiguracją, wstrzykuje klawisze przez `AUTOTYPE`,
nagrywa obraz i dźwięk przez `DX-CAPTURE /V /A`, a następnie dekoduje nagranie
własnym dekoderem ZMBV (`tests/zmbv.py`). Daje to dokładne kolory — dekoder
ffmpeg przekłamywał kanały. Piksele porównuje `tests/dosbox_harness.py`,
a konsola DOS jest odczytywana z logu `-log-con`.

Scenariusze **[łatka testowa]** używały `tests/test_patches.py` — zmian
**wyłącznie w kopii testowej**, nigdy w buildzie ani patchu dla graczy:

| Łatka | Miejsce | Działanie |
|---|---|---|
| `auto_complete` | `0351:04E2` (plik 0x5BF2) | warunek ukończenia zawsze prawdziwy; przejście dalej po 50 klatkach |
| `force_gameover` | `0351:0553` (plik 0x5C63) | skok do oryginalnej gałęzi rysowania klatki 127 |
| `start_level` | `003A:01C0` (plik 0x2764) | numer poziomu startowego |
| `player_start` | tablice DS:270D/24CF i DS:2521+82·L/22E3+82·L | pozycja startowa przy szyldzie |
| `map_edit` | kopia `*.SQL` | kafle z pokoi bonusowych obok startu; bez drzwi kamera nie wjeżdża do tych pokoi |
| `swap_error_messages` | tablica DS:3384 | zamiana wpisów, aby test CGA wypisał błąd pamięci |

## Historyczne wyniki — nie odbiór 1.1.0

Poniżej zachowano wyniki opisane w poprzedniej dokumentacji. „Zaliczony”
odnosi się wyłącznie do tamtego zakresu i buildów.

| Scenariusz | Historyczny wynik i zakres |
|---|---|
| `boot` | Zaliczony: nagrania hard_000.avi i 1_000.avi; ekran PRES.SQZ (zgodność 1.000, t=7.41936 s), polski CHOIX.SQZ w liniach 190–199 (1.000, t=30.89022 s); dźwięk RMS 6255, szczyt 32768; polskie menu RUNME. |
| `all_levels` | Zaliczony **[łatka testowa]**: wszystkie 6 poziomów i ich palety; ikony HUD z klatek 135–144 po poszerzeniu klatki 134 (zgodność 1.000 na każdym poziomie); 10 wystąpień polskiej mapy INTER; po poziomie 6 powrót do CHOIX. |
| `gameover` | Zaliczony **[łatka testowa]**: KONIEC GRY, zgodność 1.000 w (80,77), t=33.116028 s. |
| `mag_store` | Zaliczony **[łatka testowa]**: SKLEP, MAG.CK2 kafle 50–51, zgodność 1.000 w (160,30), t=32.930544 s. |
| `mag_music` | Zaliczony **[łatka testowa]**: PŁYTY, MAG.CK2 kafle 96–97, zgodność 1.000 w (160,30), t=32.930544 s. |
| `mag_mirror` | Zaliczony **[łatka testowa]**: odbicie SKLEP (MAG.CK2, 126–127) w (96,94) i PŁYTY (MAG.CK1, 79+120) w (160,94); zgodność 1.000, t=32.916276 s. |
| `ville_plaque` | Zaliczony **[łatka testowa]**: PROGRAMISTA, VILLE.CK1 kafle 114–117, zgodność 1.000 w (96,110), t=32.844936 s. |
| `insert_disk` | Zaliczony: po usunięciu AVTMAG.SQV ekran WŁÓŻ DYSK II, zgodność 1.000, t=20.545920 s. |
| `runme_ega` | Zaliczony dla **starego menu**: opcja EGA uruchamiała tylko `hard` w oryginale i PL; sprawdzono też przetłumaczony komunikat wyjścia (`runme_exit_message.png`). |
| `console` | Zaliczony dla wcześniejszego buildu: PRZEDSTAWIA, „Blues Brothers firmy TITUS”, „[3] - Intro TDT/TRSI...”, „Kto inny da wam takie rzeczy?”; na CGA „BRAK EGA/VGA.”; „BRAK RAM-U.” po zamianie wpisów **[łatka testowa]**. |
| `demo_regression` | Zaliczony przy **oryginalnym przewijaniu**, dawniej `--classic-scroll`: 187/390 próbek identycznych; brak niewyjaśnionych różnic. Nie dotyczy płynnego przewijania. |
| `smooth_scroll` | Zaliczony w dawnym demie poziomu 1 PL: 201 zmian X, przesunięcia [-6, -5, -4, -3, -2, -1], max \|dx\| = 6; potwierdzał dokładność pikselową, nie nowy launcher ani komplet profili. |
| `polish_glyphs` | Zaliczony: pangram ZAŻÓŁĆ GĘŚLĄ / JAŹŃ ĄĆĘŁŃÓŚŹŻ, zgodność 1.000, t=30.861684 s. |
| `direct_exe` | Zaliczony dla wcześniejszego buildu: bezpośrednie `1.EXE` pokazywało polski wybór postaci, zgodność 1.000, t=28.050888 s. |

Regresja dema obejmowała 390 próbek co 0,25 s. Poza 187 identycznymi
klatkami różnice dotyczyły lokalizacji (menu, CHOIX, INTER, neony poziomu 1),
fazy animacji palety (tylko kanał B) lub jednej klatki wygaszania. Przy
oryginalnym przewijaniu pozycje postaci, przeciwników i przebieg dema były
identyczne. Płynne przewijanie zmienia aktywację przeciwników względem kamery,
więc demo poziomu 1 traci synchronizację po ok. **60 s**.

Dodatkowo porównano dźwięk regresji: korelacja obwiedni 0,988, przesunięcie
50 ms od niezsynchronizowanego startu, RMS 6419 vs 6423. Nie stwierdzono
naruszenia muzyki i efektów; pliki i kod dźwięku nie są zmieniane.

Historyczne artefakty: `tests/results/latest/report.md`, arkusze klatek
i zrzuty `tests/results/latest/*.png`. Nie zastępują nowego przebiegu.

### Historyczne testy narzędzi

Poprzednia dokumentacja odnotowała 12 zaliczonych testów `tests/test_tools.py`:
identyfikację wersji, round-trip 34 skompresowanych zasobów, ILBM i SQV,
model nadmiaru dekodera DOS, schemat `strings.json`, pokrycie fontów,
limity komunikatów, determinizm dwóch buildów, nienaruszalność `original/`,
odmowę dla zmodyfikowanego pliku oraz dawną paczkę dystrybucyjną
(instalacja = build, ponowna instalacja, przywracanie, odmowa dla obcego
pliku, brak plików gry w paczce). **Nie są to wyniki testów nowego formatu.**

## Ograniczenia i znane zachowania

1. **Płynne przewijanie:** kamera co 1 px w obu osiach, ale aktywacja
   przeciwników zależy od kamery; dema nie zachowują synchronizacji.
   Regresję zgodności rozgrywki należy oceniać przy `--scroll original`
   (alias `--classic-scroll`), a płynność osobno. Domyślny build to PL smooth;
   paczka udostępnia wszystkie cztery profile.
2. **Dwóch graczy i przełączanie postaci:** niepotwierdzone; nie traktować
   widoczności opcji wyboru jako testu tych trybów.
3. **Prawdziwy sprzęt:** nietestowany. Zasoby mieszczą się w limitach buforów
   wyznaczonych z kodu ([analysis.md](analysis.md)); przesuwanie tła o 0–7 px
   obciąża CPU, więc na wolnym 286 mod może być wolniejszy od oryginału.
4. **Komunikaty DOS bez polskich znaków:** BRAK EGA/VGA., BRAK RAM-U.
   Na CGA/MDA/Hercules font pochodzi z ROM karty; test CP852 w DOSBox-X
   dawał „B¥ŤD GRAFIKI”. Dobór ASCII jest celowy. Zwykła gra wymaga VGA.
5. **OPEN:** kafel 16 px z literami 3×5 nie mieści polskiego odpowiednika;
   zmiana mapy wykracza poza lokalizację. Wpis ma status `review`.
6. **+1 ŻYCIE:** klatka 134 została poszerzona do 32 px, z wyrównaniem
   do 16 px. Sprawdzono tablicę klatek i dalsze ikony HUD (135–145), ale
   naturalne pojawienie się napisu po zdobyciu życia wymaga ręcznego testu.
7. **KONIEC GRY:** gałąź rysowania sprawdzona łatką testową; naturalna utrata
   wszystkich żyć nadal wymaga weryfikacji.
8. **WŁÓŻ DYSK II:** ekran po braku `AVTMAG.SQV`; styl grawerowany odtworzony
   z Superclarendon jest podobny, ale nie identyczny z ręcznym oryginałem.
9. **Kompresja:** inne drzewo Huffmana zmienia bajty zasobów, ale po
   dekompresji dane są identyczne pikselowo poza napisami; rozmiary są
   zbliżone lub mniejsze.
10. **Historyczne RUNME/cracktro:** dawna opcja [1] EGA nie uruchamiała gry
    także w oryginale; używano [2] VGA albo `1.EXE`. `INTRO.EXE` ([3]) nie
    było tłumaczone — to dodatek TDT/TRSI. Nagłówek RUNME wyrównywano TAB-ami
    do 8 kolumn przy stałych długościach linii. Te szczegóły zachowano jako
    historię; **START.COM omija to menu i zawsze uruchamia VGA**.

## Lista ręcznej weryfikacji — do wykonania dla 1.1.0

Żaden poniższy punkt nie jest tu oznaczony jako wykonany:

- [ ] Instalacja do nowego katalogu, zgodność wszystkich 50 plików źródła
      przed i po instalacji; odmowa dla obcej bazy i istniejącego wyniku.
- [ ] START.COM: Language/Język → oba języki → oba rodzaje przewijania;
      poprawne katalogi robocze i uruchamianie VGA bez menu cracktra.
- [ ] Cztery kompletne profile uruchamiane bezpośrednio przez `1.EXE`;
      ENORIG bez zmian, ENSMOOTH ze zmianami tylko w `1.EXE`, bez polonizacji.
- [ ] Tytuł i muzyka; czytelny wybór postaci i start przyciskiem fire.
- [ ] Mapa CHEMIA/SKLEP, neony SKLEP/PŁYTY i ich odbicia, PROGRAMISTA
      w pokoju bonusowym poziomu 5 (lewy dolny róg mapy).
- [ ] Zebranie życia → +1 ŻYCIE; utrata wszystkich żyć → KONIEC GRY
      i powrót do wyboru; naturalne ukończenie sześciu poziomów.
- [ ] Kamera co 1 px w obu osiach, krawędzie plansz i pierwszego planu;
      oryginalne przewijanie i regresja dema sprawdzone osobno.
- [ ] Tryb dwóch graczy, przełączanie postaci i prawdziwy sprzęt.
- [ ] Opcjonalnie: brak AVTMAG.SQV → WŁÓŻ DYSK II, tylko w kopii testowej.

# The Blues Brothers (1991, MS-DOS) — polska wersja językowa

Polonizacja oryginalnej gry Titus Interactive na DOS. Modyfikowane są
wyłącznie oryginalne pliki gry (grafiki z napisami oraz teksty w plikach
wykonywalnych) — silnik, rozgrywka, poziomy i dźwięk pozostają bez zmian.
Gra po spolszczeniu działa jako zwykła aplikacja DOS (sprawdzone w DOSBox-X).

![Pasek wyboru postaci w grze](docs/img/choix_ingame.png)

## Co zostało przetłumaczone

Gra nie ma fontu tekstowego — wszystkie napisy są grafikami. Przetłumaczono:

| Gdzie | Oryginał | Polska wersja |
|---|---|---|
| ekran wyboru postaci | ← CHOOSE YOUR PLAYER → PRESS FIRE TO START | ← WYBIERZ POSTAĆ → NACIŚNIJ FIRE, BY GRAĆ |
| koniec gry (sprite) | GAME OVER | KONIEC GRY |
| dodatkowe życie (sprite) | 1UP | +1 ŻYCIE |
| mapa między poziomami | CHEMICALS, STORE | CHEMIA, SKLEP |
| neony w poziomie 1 (także lustrzane odbicia) | STORE, MUSIC | SKLEP, PŁYTY |
| tabliczka w poziomie 5 | PROGRAMMER | PROGRAMISTA |
| ekran zmiany dyskietki | INSERT DISK II | WŁÓŻ DYSK II |
| komunikaty DOS | VIDEO ERROR. / OUT OF MEMORY. | BRAK EGA/VGA. / BRAK RAM-U. |
| menu RUNME | PRESENTS, From, Intro, komunikat końcowy | PRZEDSTAWIA, firmy, Intro, „Kto inny da wam takie rzeczy?” |

Bez zmian (świadomie): nazwy własne (The Blues Brothers, Jake, Elwood,
Titus), graffiti, skrót HI-FI, tabliczka OPEN (brak miejsca — oznaczona do
weryfikacji). Pełna lista: [`localization/pl/strings.json`](localization/pl/strings.json).

## Instalacja dla graczy (patch)

Potrzebne: legalna kopia obsługiwanego wydania (angielska wersja DOS na dysk
twardy, `1.EXE` 196 608 B, SHA-256 `769ee254…0add`) i Python 3.

```
python apply_patch.py C:\GRY\BLUES          # instalacja
python apply_patch.py C:\GRY\BLUES --check  # tylko sprawdzenie plików
python apply_patch.py C:\GRY\BLUES --restore
```

Instalator sprawdza SHA-256 każdego pliku, odmawia pracy z inną wersją,
kopiuje oryginały do `KOPIA_EN\`. Patch (ok. 18 KB) zawiera tylko zmienione
bajty i piksele — żadnych plików gry. Uruchomienie: `RUNME` → `[2] - VGA`
albo bezpośrednio `1.EXE`. Szczegóły zgodności: [docs/compatibility.md](docs/compatibility.md).

## Budowanie polskiej wersji (dla twórców)

Wymagania: Python 3.8+, Pillow, numpy. Do testów: DOSBox-X, a do
generowania masek dużych napisów — kroje systemowe macOS (opcjonalnie).

```sh
# oryginalne pliki gry w katalogu original/ (nie są modyfikowane)
python tools/extract.py --source original --output work/extracted   # eksport zasobów + test round-trip
python tools/build.py --source original --locale pl --output build  # build -> build/game, build/report.txt
python tools/make_patch.py --source original --build build/game     # patch -> patches/dist/*.zip (z autotestem)
tests/run_tests.sh            # testy narzędzi
tests/run_tests.sh --dosbox   # + testy w DOSBox-X (ok. 20 min)
```

Build jest deterministyczny (dwa przebiegi dają identyczne bajty — sprawdza to
`tests/test_tools.py`).

### Zmiana tłumaczenia — instrukcja tworzenia polskiego wydania

1. Edytuj pole `translation` w `localization/pl/strings.json`.
   * Napisy graficzne mogą używać tylko znaków obecnych w foncie danego
     napisu — sprawdź `python tools/font_specimen.py` (podgląd:
     `docs/img/fonts.png`). Font paska wyboru zawiera pełny alfabet z
     polskimi literami; fonty szyldów — tylko litery potrzebne do obecnych
     napisów (brakujące glify można dorysować w JSON, patrz
     [docs/file-formats.md](docs/file-formats.md#10-formaty-edycyjne-projektu)).
   * Limity szerokości są w polu `max_size`; generator zgłosi błąd, jeśli
     tekst się nie mieści.
   * Teksty `runme.*` muszą mieć dokładnie tę samą długość (dopełnij
     spacjami) i być w ASCII; komunikaty `exe.*` razem ≤ 26 znaków.
2. Wygeneruj grafiki: `python tools/make_graphics.py --preview work/preview`
   (podgląd przed/po w `work/preview/`). Albo jednym poleceniem:
   `python tools/build.py --render`.
3. (Opcjonalnie) popraw PNG ręcznie w `localization/pl/graphics/` —
   w edytorze z trybem indeksowanym, bez zmiany palety. Ustaw wtedy
   `"mode": "manual"` w danym wpisie, by generator nie nadpisał zmian.
4. Zbuduj i przetestuj: `python tools/build.py`, `tests/run_tests.sh --dosbox`.
5. Utwórz patch: `python tools/make_patch.py --version 1.1`.

## Struktura repozytorium

```
original/               oryginalna gra (nie publikować, nie modyfikować)
tools/
  bbformats.py          kodek: kompresja Titus, ILBM, SQV
  gamedata.py           sumy kontrolne, poziomy, offsety, limity silnika
  extract.py            eksport zasobów do PNG/JSON + round-trip
  make_graphics.py      generator polskich grafik z tłumaczeń i fontów
  glyphkit.py           fonty bitmapowe JSON, maski, style
  import.py             PNG -> formaty gry (z kontrolą limitów)
  patch_exe.py          teksty w 1.EXE / RUNME.COM (sygnatury, SHA-256)
  build.py              pełny build + weryfikacja + raport
  make_patch.py         paczka dystrybucyjna + jej autotest
  font_specimen.py      próbki fontów i pokrycie polskich liter
  patcher/apply_patch.py  instalator dla graczy
localization/pl/
  strings.json          wszystkie teksty: oryginał, tłumaczenie, miejsce, limity, status
  fonts/*.json          edytowalne fonty bitmapowe (6 stylów)
  graphics/             polskie grafiki PNG (+ maski dużych napisów)
patches/text_patches.json  wygenerowana specyfikacja zmian bajtowych
tests/                  testy narzędzi, harness DOSBox-X, wyniki
docs/                   analysis.md, file-formats.md, compatibility.md
build/                  wynik budowania (ignorowany przez git)
```

## Stan projektu

Szczegółowe wyniki testów: [docs/compatibility.md](docs/compatibility.md)
i `tests/results/latest/report.md`.

* wszystkie zidentyfikowane teksty dla gracza mają polskie odpowiedniki
  (poza świadomie pozostawionymi nazwami i jednym wpisem do weryfikacji),
* polskie litery (wszystkie 9 wielkich) wyświetlane w grze — test pangramem,
* gra uruchamia się w DOSBox-X, przechodzi przez wszystkie 6 poziomów
  i ekran końca gry (testy automatyczne, część z łatkami testowymi),
* odtworzenie dema daje rozgrywkę identyczną z oryginałem (brak regresji),
* build deterministyczny, patch testowany na czystej kopii.

Ograniczenia i to, czego nie dało się sprawdzić automatycznie (prawdziwy
sprzęt, naturalna utrata wszystkich żyć, wyskakujący napis „+1 ŻYCIE”),
opisuje [docs/compatibility.md](docs/compatibility.md).

## Licencje

Kod: MIT, tłumaczenie i grafiki: CC BY 4.0 — patrz [LICENSE](LICENSE).
Gra © 1991 Titus Interactive (nie jest częścią projektu).

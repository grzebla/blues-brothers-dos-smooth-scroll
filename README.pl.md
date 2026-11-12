# The Blues Brothers DOS — Smooth Scroll

Polski · **[English](README.md)**

Mod **płynnego przewijania** do **The Blues Brothers (1991, DOS)**. Kamera śledzi gracza z dokładnością do 1 piksela w obu osiach.

Graj w oryginalnej wersji angielskiej lub włącz **opcjonalną polonizację**. Menu startowe pozwala wybrać język i przełączyć płynne przewijanie na oryginalne. Wszystkie opcje działają w VGA.

**[Pobierz patch v1.1.0](https://github.com/grzebla/blues-brothers-dos-smooth-scroll/releases/download/v1.1.0/blues-brothers-1.1.0-patch.zip)** · [Strona wydania](https://github.com/grzebla/blues-brothers-dos-smooth-scroll/releases/tag/v1.1.0)

To patch, **nie pełna gra**. Potrzebujesz własnej kopii obsługiwanego wydania gry.

## Czego potrzebujesz

- Czystej kopii **angielskiej wersji DOS na dysk twardy, wydanie TDT/TRSI**. Inne wydania nie są obsługiwane; instalator sam sprawdzi pliki.
- [Pythona 3.8+](https://www.python.org/downloads/) do instalacji patcha. Nie potrzeba dodatkowych pakietów Pythona.
- [DOSBox-X](https://dosbox-x.com/) do grania. Testowana wersja: **2026.10.01 SDL2**.

## 1. Pobierz i rozpakuj

Pobierz ZIP patcha z linku powyżej i rozpakuj go. **Nie musisz klonować repozytorium ani niczego budować.**

Repozytorium i patch są dostępne publicznie. Nie potrzebujesz konta GitHub ani zgody na dostęp.

## 2. Zainstaluj patch

Otwórz terminal w katalogu rozpakowanego patcha — **nie w DOSBox**. Wpisz:

```sh
python apply_patch.py "C:\GAMES\BLUES" --output "C:\GAMES\BB110"
```

Zastąp przykładowe ścieżki własnymi:
- `C:\GAMES\BLUES` — katalog oryginalnej gry.
- `C:\GAMES\BB110` — nowy katalog na grę z patchem. **Nie może jeszcze istnieć**, a jego katalog nadrzędny musi istnieć. Wybierz miejsce poza katalogiem oryginału.

Na macOS/Linuksie użyj ścieżek swojego systemu i polecenia `python3` zamiast `python`.

**Oryginalna gra pozostaje nietknięta.** Nowy katalog zawiera wszystkie cztery kombinacje; wybierzesz jedną przy uruchomieniu.

## 3. Uruchom grę

Otwórz DOSBox-X i wpisz poniższe polecenia, podając katalog wynikowy z kroku 2:

```text
mount c "C:\GAMES\BB110"
c:
config -set cpu cycles=fixed 20000
START.COM
```

Użyj powyższego polecenia `config -set`; skrót `cycles fixed 20000` nie jest domyślnie dostępny w DOSBox-X.

W menu wybierz kolejno:
1. **Język:** `1` English lub `2` Polski.
2. **Przewijanie:** `1` oryginalne lub `2` płynne.

**Aby grać z modem płynnego przewijania, wybierz English → Smooth scroll (`1`, potem `2`).** Aby dodać polonizację, wybierz Polski → Płynne przewijanie (`2`, potem `2`).

## Potrzebujesz pomocy?

- [Pełna instrukcja instalacji i rozwiązywanie problemów](docs/install.pl.md)
- [Obsługiwana wersja gry, ustawienia emulatora i zgodność](docs/compatibility.pl.md)
- [Opis moda płynnego przewijania](mods/smooth_scroll/README.pl.md)

Płynne przewijanie zmienia moment aktywacji przeciwników i powoduje utratę synchronizacji nagranych dem. Tryb dwóch graczy, przełączanie postaci i prawdziwy sprzęt nie zostały zweryfikowane.

<details>
<summary>Dla twórców: budowanie ze źródeł</summary>

Wymagane: Python 3, Pillow, numpy i NASM (polecenie `nasm`).

```sh
git clone https://github.com/grzebla/blues-brothers-dos-smooth-scroll.git
cd blues-brothers-dos-smooth-scroll
python3 -m pip install Pillow numpy
```

Umieść czyste pliki obsługiwanego wydania gry w `original/`, a następnie zbuduj angielską grę z płynnym przewijaniem:

```sh
python3 tools/build.py --source original --locale en --scroll smooth --output build/en-smooth
```

Uruchom `1.EXE` z `build/en-smooth/game/` w DOSBox-X. Użyj `--locale pl`, aby dodać polonizację, lub `--scroll original` dla oryginalnego przewijania. To buduje jedną kombinację, bez menu wyboru.

[Teksty tłumaczenia](localization/pl/strings.json) · [Formaty i limity](docs/file-formats.md) · [Analiza silnika](docs/analysis.md)

</details>

## Licencja

Kod projektu: **MIT**. Polonizacja: **CC BY 4.0**. Oryginalna gra pozostaje © 1991 Titus Interactive. Zobacz [LICENSE](LICENSE).

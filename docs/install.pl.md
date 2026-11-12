# Smooth Scroll — instalacja i uruchomienie (1.1.0)

Zainstaluj mod płynnego przewijania do The Blues Brothers (DOS). Polonizacja jest opcjonalnym dodatkiem, wybieranym w menu startowym.

[English](install.md) · [Opis projektu](../README.pl.md)

## Wymagania i pobieranie

- Legalnie posiadana **angielska wersja DOS na dysk twardy, wydanie TDT/TRSI**.
  Inne wydania nie są obsługiwane; projekt nie udostępnia gry do pobrania.
- **Python 3.8+** w systemie gospodarza — jedyna zależność instalatora.
  Bez Pillow, numpy, NASM, klonowania repozytorium i budowania ze źródeł.
- DOS do uruchomienia gry, np. DOSBox-X (testowana wersja: **2026.01.02**).

Pobierz `blues-brothers-1.1.0-patch.zip` oraz `SHA256SUMS` z
[wydania v1.1.0](https://github.com/grzebla/blues-brothers-dos-smooth-scroll/releases/tag/v1.1.0).
[Repozytorium](https://github.com/grzebla/blues-brothers-dos-smooth-scroll)
i pliki wydania są publiczne; nie potrzebujesz konta GitHub. ZIP zawiera dane
patcha i kod projektu, nie kompletne oryginalne pliki gry.
W środku są `README.txt` (instrukcja EN), `CZYTAJ.txt` (ta instrukcja),
`LICENSE.txt`, `START.COM`, `patch.json`, `apply_patch.py` i `bbformats.py`.
Przed rozpakowaniem porównaj SHA-256 ZIP-a z jego wpisem w `SHA256SUMS`.
Przykładowe polecenia: `shasum -a 256 blues-brothers-1.1.0-patch.zip` na macOS,
`sha256sum blues-brothers-1.1.0-patch.zip` na Linuksie lub w PowerShellu
`Get-FileHash .\blues-brothers-1.1.0-patch.zip -Algorithm SHA256` na Windows.

## Instalacja do nowego katalogu

Otwórz terminal systemu gospodarza w katalogu rozpakowanego patcha.
Nie uruchamiaj Pythona w DOSBox. `SOURCE` to katalog oryginalnej gry,
a `NEW_DIR` — ścieżka wyniku, który **nie może jeszcze istnieć**.
Jego **katalog nadrzędny musi już istnieć**. Ścieżki ze spacjami ujmij w cudzysłowy.

```sh
python apply_patch.py SOURCE --check
python apply_patch.py SOURCE --output NEW_DIR
```

W razie potrzeby użyj `python3` zamiast `python`. Przykład dla Windows:

```text
python apply_patch.py "C:\GAMES\BLUES" --check
python apply_patch.py "C:\GAMES\BLUES" --output "C:\GAMES\BB110"
```

Instalator sprawdza **wszystkie 50 plików `KNOWN_FILES`**, w tym ich rozmiary
i sumy SHA-256. Obsługiwany `1.EXE` ma **196608 bajtów** i SHA-256:

```text
769ee254b154a9444205524ec4b28a8147a372ac5b2cee2e25fcd83aa90d0add
```

Zgodny EXE nie wystarczy. Brakujące lub zmodyfikowane pliki gry oznaczają
nieobsługiwaną bazę. Instalacja jest **out of place** i nie zmienia `SOURCE`;
wybierz osobną ścieżkę wyniku, nie podkatalog źródła.

Wynik zawiera:

```text
NEW_DIR/
  START.COM
  ENORIG/      (en-original)
  ENSMOOTH/    (en-smooth)
  PLORIG/      (pl-original)
  PLSMOOTH/    (pl-smooth)
```

Każdy profil to **kompletny katalog gry**, a nie nakładka zależna od innego
profilu. `en-original` zachowuje niezmienioną grę angielską; `en-smooth`
zmienia dla przewijania **tylko `1.EXE`**, bez polskich zasobów i tekstów.
Polskie profile dodają lokalizację z oryginalnym albo płynnym przewijaniem.
Instalowane są wszystkie cztery profile; nie ma opcji `--variant`.

## Uruchomienie gry

Używaj VGA. W DOSBox-X zamontuj wynik jako dysk C (zastąp poniższą ścieżkę
systemową swoim `NEW_DIR`):

```text
mount c "C:\GAMES\BB110"
c:
config -set cpu cycles=fixed 20000
START.COM
```

Wpisuj te polecenia w DOSBox-X, nie w terminalu swojego systemu.
Użyj `config -set cpu cycles=fixed 20000`, nie skrótu `cycles fixed 20000`:
DOSBox-X domyślnie nie udostępnia ustawień konfiguracji jako poleceń powłoki.
Polecenie sprawdzono w DOSBox-X **2026.10.01 SDL2**: zmieniono początkowe
3000 cykli na 20000 i odczytano wynik przez `config -get cpu cycles`.

Launcher pokazuje **Language/Język**: `1 English`, `2 Polski`. Drugi ekran
oferuje **Original version / Smooth scroll** po angielsku albo **Wersja
oryginalna / Płynne przewijanie** po polsku. Uruchamia VGA bezpośrednio,
bez starego menu RUNME/cracktra oraz wyboru EGA/intro.

Aby grać tylko po angielsku z płynnym przewijaniem, wybierz English →
Smooth scroll. Możesz też z katalogu głównego zamontowanego wyniku wykonać:

```text
cd ENSMOOTH
1.EXE
```

Pozostałe profile również można uruchamiać bezpośrednio przez `1.EXE`.

Zalecane ustawienia DOSBox-X (historycznie testowane na 2026.01.02):

```ini
[dosbox]
machine=svga_s3
memsize=16

[cpu]
core=normal
cycles=fixed 20000
```

Pełna prędkość (~23 kl./s) wymaga ok. **12000 cykli lub więcej**; 3000 to
za mało zarówno dla oryginalnego, jak i płynnego przewijania. Płynna kamera
ma dokładność 1 px w obu osiach, zmienia aktywację przeciwników i powoduje
utratę synchronizacji nagranych dem po ok. 60 sekundach. Tryb dwóch graczy,
przełączanie postaci i prawdziwy sprzęt nie są potwierdzone.
Zobacz [zgodność](compatibility.pl.md).

## Problemy i powrót do oryginału

- **Katalog wyjściowy istnieje:** wybierz inny, nieistniejący `NEW_DIR`.
  Nie instaluj na źródle ani na poprzednim wyniku.
- **Weryfikacja źródła nie przechodzi:** użyj czystej kopii dokładnie
  obsługiwanego wydania; nie omijaj walidacji ani nie mieszaj wydań.
- **Wcześniej użyto patcha 1.0:** odtwórz tę kopię **starym instalatorem
  1.0** albo użyj czystej kopii. Katalog po patchu 1.0 nie jest bazą nowej
  instalacji. Nowy instalator odrzuca patche starego formatu 1 oraz opcję
  `--restore`, podając instrukcję migracji.
- **Chcesz cofnąć 1.1.0:** nowy format nie ma `--restore`. Źródło nie było
  zmieniane; uruchom je ponownie lub usuń wyłącznie wygenerowany katalog
  wyjściowy.
- **Link do pobrania nie działa:** otwórz
  [stronę wydania](https://github.com/grzebla/blues-brothers-dos-smooth-scroll/releases/tag/v1.1.0)
  i pobierz ZIP patcha z sekcji **Assets**. Logowanie nie jest wymagane.

Zapisany zakres testów 1.1.0 i pozostałe ograniczenia opisuje
[dokumentacja zgodności](compatibility.pl.md). `tests/results/latest` zawiera
historyczne wyniki wcześniejszych buildów, nie raport odbiorczy tego wydania.

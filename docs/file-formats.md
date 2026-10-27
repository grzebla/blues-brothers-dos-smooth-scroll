# Formaty plików (wersja DOS)

Wszystkie formaty zweryfikowano na plikach z `original/`. Implementacja:
`tools/bbformats.py` (kodek), `tools/extract.py` (eksport), `tools/import.py`
(import). Wartości wielobajtowe: LE = little endian, BE = big endian.

## 1. Kompresja Titus (`*.SQZ`, `*.SQV`, `*.SQL`, `*.CK1`, `*.CK2`)

Statyczny kod Huffmana, jeden plik = jeden strumień.

| Offset | Typ | Opis |
|---|---|---|
| 0 | u16 LE | starsze 16 bitów rozmiaru po dekompresji |
| 2 | u16 LE | młodsze 16 bitów rozmiaru po dekompresji |
| 4 | u16 LE | `dict_len` - długość słownika w bajtach (≤ 0x400) |
| 6 | `dict_len` B | węzły drzewa: u16 LE |
| 6+`dict_len` | ... | strumień bitów: słowa u16 **BE**, bity od najstarszego |

Dekodowanie: `node = 0`; dla każdego bitu: jeśli bit = 1, `node += 2`;
`node = dict[node]`; jeśli bit 15 węzła jest ustawiony, młodszy bajt to
symbol wyjściowy i `node = 0`. Para węzłów pod offsetem `p`, `p+2` to gałęzie
0 i 1.

Szczegóły dekodera w `1.EXE` (`0A47:054E`), które muszą być respektowane
przy kompresji:

* dekoder czyta plik blokami po 4096 B i **dekoduje aż do końca pliku**,
  ignorując rozmiar z nagłówka - bity dopełnienia ostatniego słowa nie mogą
  tworzyć pełnego kodu, bo każdy dodatkowy symbol zostanie zapisany za
  danymi. Nasz koder dopełnia strumień prefiksem najdłuższego kodu
  (0 nadmiarowych bajtów; w skrajnym przypadku krótkich kodów 1 bajt - tyle
  samo, ile dają niektóre oryginalne pliki),
* plik o nieparzystej długości: ostatni odczyt zwraca 1 bajt,
* słownik trafia do bufora `DS:3400` o rozmiarze 0x400 B.

Pliki `JOHN.SQZ`, `OH.SQZ`, `TERRY.SQZ` (cracktro) **nie** są skompresowane.

Kompresja nie jest jednoznaczna (różne drzewa dają ten sam wynik) - narzędzia
wymagają zgodności po dekompresji, nie identyczności bajtów. Nasz koder jest
deterministyczny (kopiec z kluczem (częstość, kolejność)), więc build daje
zawsze te same bajty.

## 2. IFF ILBM (ekrany i arkusze kafli, po dekompresji)

Standardowy `FORM ILBM` z Deluxe Paint: `BMHD`, `CMAP` (16 kolorów RGB po
8 bitów), `DPPS`/`DPPV`, `CRNG`, `CAMG`, `BODY`. 320 px szerokości, 4
płaszczyzny, kompresja ByteRun1. Linia = 4 x 40 B (płaszczyzny 0-3, bit 7 =
lewy piksel). `PRES.SQZ` ma 400 linii, ale gra używa 200.

Dekoder gry (`003A:11CD`):

* szuka znaczników `CMAP` i `BODY` z krokiem 2 bajtów (chunki muszą leżeć
  pod parzystymi offsetami - zapewnia to standardowe wyrównanie IFF),
* traktuje `BODY` jako **ciągły strumień** 32000 B - przebiegi mogą
  przekraczać granice płaszczyzn i linii,
* bajt sterujący 0x80 oznacza przebieg 129 bajtów (nie jest pomijany) - nasz
  koder nigdy go nie generuje,
* dekoduje do bufora roboczego pod offsetem +30000 względem początku pliku
  ILBM → **ILBM po dekompresji ≤ 30000 B**.

Paleta: wartości `CMAP` są ładowane do DAC VGA po przesunięciu o 2 bity
(6 bitów na składową).

## 3. Arkusze kafli `*.CK1`, `*.CK2`

ILBM 320x200. Kafel = 16x16 px, siatka 20 kolumn. Mapa adresuje 7-bitowym
indeksem tylko kafle 0-127 (linie 0-111); bit 7 bajtu mapy wybiera arkusz
(0 = CK1, 1 = CK2). Linie 112-199 arkuszy nie są wyświetlane (zawierają np.
nieużywany napis "TIKETS").

## 4. Mapy `*.SQL` (po dekompresji)

Tablica bajtów 128 x wysokość (rozmiar/128 linii), wiersz po wierszu. Bajt =
numer kafla (opis wyżej) i jednocześnie indeks w tablicy wyzwalaczy `*.BIN`.

## 5. Wyzwalacze `*.BIN`

256 rekordów po 10 B (typ kafla, flagi, funkcja, indeksy tablic animacji
w `1.EXE`). Nie zawierają tekstów - nie są modyfikowane.

## 6. Sprite'y `*.SQV` (po dekompresji)

| Offset | Typ | Opis |
|---|---|---|
| 0 | u16 LE | liczba klatek N |
| 2 | N x klatka | |

Klatka: u16 LE wysokość, u16 LE szerokość (wielokrotność 16), potem dane
planarne: 4 płaszczyzny po (szerokość/8)·wysokość bajtów, płaszczyzna 0 =
najstarszy bit indeksu koloru. Loader `003A:066C` wylicza wskaźniki kolejnych
klatek z nagłówków, więc rozmiar klatki można zmienić (zmieniono klatkę 134
z 16x7 na 32x7). Paleta jest paletą bieżącego poziomu (CMAP z CK1).

Klatki `SPRITE.SQV` istotne dla lokalizacji: 127 = "GAME OVER" (160x34,
wymiar stały), 128-134 = wyskakujące napisy (-10 ... +50, 1UP).

## 7. Kafle pierwszego planu `AVT*.SQV` (po dekompresji)

Nagłówek 6 B (u16 liczba kafli + 4 B), potem rekordy po 132 B: 128 B pikseli
16x16 planarnie + 4 B. Bez napisów.

## 8. Font cyfr w `1.EXE`

Offset pliku `0xE4DA`: 10 cyfr, każda 32 B (4 płaszczyzny 8x8). Eksport:
`work/extracted/fonts/digits.png`.

## 9. Komunikaty konsolowe `1.EXE`

Blok `DS:3388`-`DS:33AB` (plik `0x15188`-`0x151AB`): dwa ciągi
`"\n\r" tekst "\n\r$"`; wskaźniki near w tablicy `DS:3384` (plik `0x15184`).
`tools/patch_exe.py` układa oba tłumaczenia w tym bloku i aktualizuje
wskaźniki.

## 10. Formaty edycyjne projektu

* **PNG indeksowany** (`localization/pl/graphics/*.png`) - cały obraz ILBM
  z oryginalną paletą 16 kolorów; edytować w trybie indeksowanym, nie zmieniać
  palety (import to sprawdza).
* **Klatki sprite'ów** - `localization/pl/graphics/SPRITE.SQV/frame_NNN.png`;
  szerokość musi być wielokrotnością 16.
* **Fonty JSON** (`localization/pl/fonts/*.json`):

```json
{
 "name": "choix",
 "colors": {"6": 6, "7": 7, "D": 13},
 "height": 10, "spacing": 1, "space_width": 6,
 "glyphs": {"Ą": ["...7D....", "..D66D...", "..."]}
}
```

  Każdy glif to lista linii o równej długości; `.` = przezroczysty, inne
  znaki mapowane przez `colors` na indeksy palety.
* **Maski** (`localization/pl/graphics/masks/*.png`) - kształt dużych napisów
  (biały = litera); styl nakładany proceduralnie przez `tools/make_graphics.py`.

# Analiza oryginalnej gry

Dokument opisuje wyniki analizy plików z katalogu `original/` (archiwum
`The-Blues-Brothers_DOS_EN.zip`). Oznaczenia pewności:
**[P]** potwierdzone (deasemblacja + test w DOSBox-X), **[D]** potwierdzone
deasemblacją lub analizą danych, **[H]** hipoteza / wniosek pośredni.

## 1. Identyfikacja wydania

| Cecha | Wartość | Pewność |
|---|---|---|
| Gra | The Blues Brothers, Titus Interactive 1991, MS-DOS | [P] |
| Język | angielski (wszystkie napisy w grafikach po angielsku) | [P] |
| Wariant | pełna wersja na dysk twardy, **zmodyfikowana przez grupy TDT/TRSI ("crack")** | [D] |
| Dowody modyfikacji | `RUNME.COM` (menu "THE DREAM TEAM - TRISTAR - RED SECTOR INC. PRESENTS"), `INTRO.EXE` (cracktro, nagłówek "FUCK YOU LAMER! MAKE AN OWN INTRO"), w `1.EXE` procedura zabezpieczenia dyskietki `0E63:0005` jest pomijana - pod adresem wywołania `0E63:0004` stoi `RETF` (w oryginale kod `PUSH AX`) | [D] |
| Demo? | nie: wszystkie 6 poziomów, brak plików `DEMOMAG.*` (wydanie demo używa innych nazw) | [P] |
| Dodatkowe pliki crackerów | `RUNME.COM`, `HARD.COM`, `INTRO.EXE`, `JOHN.SQZ`, `OH.SQZ`, `TERRY.SQZ` - gra (`1.EXE`) nie odwołuje się do nich | [D] |
| Data plików | 1991 (poza `JOHN.SQZ` - 1999 i `INTRO.EXE` - błędna data 2091) | [D] |

### Pliki (rozmiar w bajtach, SHA-256)

| Plik | Rozmiar | SHA-256 | Kompresja | Rola |
|---|---|---|---|---|
| `1.EXE` | 196608 | `769ee254b154a9444205524ec4b28a8147a372ac5b2cee2e25fcd83aa90d0add` | - | główny program gry (Turbo C 1988, MZ + 88 492 B danych za obrazem) |
| `AVTEGOU.SQV` | 2685 | `88d8d76f197160dec5f1f614a17eb95537004f158cad803ff1ebcd7b07dbf4c4` | Titus/Huffman → 3038 B | kafle pierwszego planu 16x16, poziom "Kanały" |
| `AVTENT.SQV` | 2067 | `3862870389d22df220bd6913a47b08edac2e004e9def844b66a50051abf4defa` | Titus/Huffman → 3566 B | kafle pierwszego planu 16x16, poziom "Magazyn" |
| `AVTMAG.SQV` | 3069 | `c58322fb78b9b158eb7d27fb1f26d0625433a6114554af608bc18a86999cc84f` | Titus/Huffman → 4094 B | kafle pierwszego planu 16x16, poziom "Sklep muzyczny" |
| `AVTPRIS.SQV` | 3219 | `6179977757ab30587938ee6f4d257eadc48ae7c36d072736b04e027315c19c4d` | Titus/Huffman → 4886 B | kafle pierwszego planu 16x16, poziom "Więzienie" |
| `AVTVILLE.SQV` | 2113 | `4cef021bae03c6f0a7144e97e32b9a63503b6ee5b8f48620b738ecd9797c5b5a` | Titus/Huffman → 2246 B | kafle pierwszego planu 16x16, poziom "Miasto (budowa)" |
| `CHOIX.SQZ` | 12557 | `3e5bb89dc179b021e5018516d87d45091d9f6a854a06b224b61b55c890c1f559` | Titus/Huffman → 17290 B | ekran wyboru postaci (ILBM) |
| `CONCERT.BIN` | 2560 | `7de67ab61fd732ea24b4099e68850125d068345dfabc628207acb8dd7b15654c` | - | tablica 256 wyzwalaczy kafli (10 B/kafel), poziom "Koncert" |
| `CONCERT.CK1` | 9487 | `d42caf2b60301cd74332bacf0eb02e4a0484d6e764ff0611566a7a79962fc1cf` | Titus/Huffman → 13714 B | kafle tła poziomu "Koncert" (ILBM, kafle 0-127) |
| `CONCERT.CK2` | 10229 | `8d2322873aedee85af940f159704c204559e97ed8ec00a60e658fee87289faba` | Titus/Huffman → 14456 B | kafle tła poziomu "Koncert" (ILBM, kafle 128-255) |
| `CONCERT.SQL` | 4523 | `eb3aeff2e4799fb27184b88d9f5fb36ba47d860319c8227a1d012d4e16924cb3` | Titus/Huffman → 6144 B | mapa poziomu "Koncert" (128 kolumn) |
| `DEMO1.BIN` | 1024 | `99e5ea79546293d6025142afdd275213e2ccf349ec733339661895267f560d6c` | - | zapis sterowania trybu demo |
| `DEMO2.BIN` | 1024 | `046cdafc1979a73d84c52d07a0590ca500f8731cb8d498a86d1feae28f3b68a5` | - | zapis sterowania trybu demo |
| `DEMO3.BIN` | 1024 | `d5644ece357a1cc1a2acc5807042a24c5ce93cdf31599e7d8e4fa25ea1022194` | - | zapis sterowania trybu demo |
| `EGOU.BIN` | 2560 | `7fdf48e615a1e45e7ddbc6a1c511a0b7f1ece80a7b832a96e7f915e577c6f2e2` | - | tablica 256 wyzwalaczy kafli (10 B/kafel), poziom "Kanały" |
| `EGOU.CK1` | 13685 | `f1a910ee89bac7c47ae049ca89e7bb732fbfe2caae6d00adf5b6bc9c5a35afd0` | Titus/Huffman → 16696 B | kafle tła poziomu "Kanały" (ILBM, kafle 0-127) |
| `EGOU.CK2` | 12964 | `5e932b35342af285be8d599c5827a780b88dff14807c4addc9b1010f180481ce` | Titus/Huffman → 15924 B | kafle tła poziomu "Kanały" (ILBM, kafle 128-255) |
| `EGOU.SQL` | 6746 | `66a85d59459299ece4a252a2352044acb61ced3b9315c17f1e9854abac06a4f8` | Titus/Huffman → 9856 B | mapa poziomu "Kanały" (128 kolumn) |
| `ENEMI1.SQV` | 14619 | `29ac326a89e6975e3266f67775b8a6035297be59cebb0cd597a1bb24a7d85b15` | Titus/Huffman → 20214 B | sprite'y przeciwników, poziom "Sklep muzyczny" |
| `ENEMI2.SQV` | 12952 | `6f39c2a4ae06dd2a7e9cc6f8053026bf3aefa6b75cc739736f18af327f755ef9` | Titus/Huffman → 18342 B | sprite'y przeciwników, poziom "Magazyn" |
| `ENEMI3.SQV` | 11135 | `8a681e114090f799acd066ee0689650f9968cab4419b45f1149e6a8389fd69e8` | Titus/Huffman → 15162 B | sprite'y przeciwników, poziom "Więzienie" |
| `ENEMI4.SQV` | 7957 | `a5165ec672ca147758e832348da950e0eb4e13a10df370b4ffeb1cdfb81410d4` | Titus/Huffman → 9934 B | sprite'y przeciwników, poziom "Kanały" |
| `ENEMI5.SQV` | 12143 | `f3997e16b7a3f8594b6eabe2f654171c2d8fb7937b047b4cf5b5eaadd961d8e4` | Titus/Huffman → 17566 B | sprite'y przeciwników, poziom "Miasto (budowa)" |
| `ENEMI6.SQV` | 5108 | `f64c33ef8c393a004cbaaf91ddeb7ecb3f59e4c42a014cf2c45360060e6ef892` | Titus/Huffman → 6474 B | sprite'y przeciwników, poziom "Koncert" |
| `ENT.CK1` | 13892 | `52f248f8f195e47b7912403ad1026b4f9e83bc7d7901e209a910ac7383a4dc76` | Titus/Huffman → 16580 B | kafle tła poziomu "Magazyn" (ILBM, kafle 0-127) |
| `ENT.CK2` | 10606 | `aa652759baa1606a66d33cc4893221ac222b64fba5f9a7f4d4ab9dc60706eb51` | Titus/Huffman → 12832 B | kafle tła poziomu "Magazyn" (ILBM, kafle 128-255) |
| `ENT.SQL` | 5830 | `7958d185aba7474107dce556c9a33ecdd07711656542b0adafac552fda5926dc` | Titus/Huffman → 9216 B | mapa poziomu "Magazyn" (128 kolumn) |
| `ENTREPOT.BIN` | 2560 | `ae3e73eb5b0d0088eb253a3bda101aabd112b7ef429bbc843bea3487d84b7036` | - | tablica 256 wyzwalaczy kafli (10 B/kafel), poziom "Magazyn" |
| `HARD.COM` | 14 | `17821199d08b8c74601ea199647bb7f4a0482b2e8b34a6ad12b79c97529c9aee` | - | pomocnik menu: odczyt klawisza -> ERRORLEVEL |
| `INSERT.SQZ` | 4984 | `d98ba86535c3c2f989f8c01fd56f924c2dcafd031133110fa1702ada9d0611f9` | Titus/Huffman → 7142 B | ekran "INSERT DISK II" (ILBM) |
| `INTER.SQZ` | 22364 | `2560ea27e0d47d478ba904a8a45f3186cb5ad96e49595d879ee8c844140e112c` | Titus/Huffman → 27288 B | mapa między poziomami (ILBM) |
| `INTRO.EXE` | 16020 | `41d8a6969d8932593b105f225cf3c69c5fd236e89b9190605262c91eebf1de61` | - | cracktro TDT/TRSI |
| `JOHN.SQZ` | 65822 | `c8ebd31ab0f2baa05ed18f96ca132bae20acf67ff040296561f12aceb6cbe577` | - | dane cracktra (nieskompresowane) |
| `MAG.CK1` | 12633 | `81211d28c9a4c9996c99a94e9151381c6000e2ccae728d411348b81771af735b` | Titus/Huffman → 15930 B | kafle tła poziomu "Sklep muzyczny" (ILBM, kafle 0-127) |
| `MAG.CK2` | 13676 | `00b9476c09a31dde166474f5555a485c5152cf95cc51ad2811d2f783cbd24699` | Titus/Huffman → 17424 B | kafle tła poziomu "Sklep muzyczny" (ILBM, kafle 128-255) |
| `MAG.SQL` | 7154 | `26ad729dcf0bef933955a8c833a178dfa87a812e74b4dfc6b4462fe4a9efcb49` | Titus/Huffman → 10880 B | mapa poziomu "Sklep muzyczny" (128 kolumn) |
| `MAGASIN.BIN` | 2560 | `72158766739aa3244bc05267144bf44d56003cdbb549a273f6fdc0d377140d79` | - | tablica 256 wyzwalaczy kafli (10 B/kafel), poziom "Sklep muzyczny" |
| `OH.SQZ` | 64000 | `c9ffd34fde5a681ccad2e185aa2e0a681b407a9275a535afff41099a792aac21` | - | dane cracktra (64000 B, nieskompresowane) |
| `PRES.SQZ` | 20180 | `911bc83077f7006d1aa0b17ff260b29969f83227ccbc0e53e2e0318b643fbf89` | Titus/Huffman → 30972 B | ekran tytułowy (ILBM 320x400, widoczne 200 linii) |
| `PRISON.BIN` | 2560 | `e3a733baf8a931068e7f024c70006a8588402612ae19ab4eebe34e2254e82867` | - | tablica 256 wyzwalaczy kafli (10 B/kafel), poziom "Więzienie" |
| `PRISON.CK1` | 15546 | `314dfe146250efed30c422f8a0caa392e07667d6aebe2c547c08309a22f0fc2e` | Titus/Huffman → 18598 B | kafle tła poziomu "Więzienie" (ILBM, kafle 0-127) |
| `PRISON.CK2` | 13194 | `88e1b2bc7056d66c14907c10485332ea0162102066731a430e31362904e0a71d` | Titus/Huffman → 16012 B | kafle tła poziomu "Więzienie" (ILBM, kafle 128-255) |
| `PRISON.SQL` | 7879 | `ef8334205b4ba5b1a3bcc91cf693b04f25a2331c821fe25b26097c7f466edc97` | Titus/Huffman → 11136 B | mapa poziomu "Więzienie" (128 kolumn) |
| `RUNME.COM` | 1683 | `adf3cff695911c977adc6a920e500dbe117293bc3aae049024ee297aa7e86e15` | - | menu startowe crackerów (skompilowany batch) |
| `SPRITE.SQV` | 37622 | `8f6222115f2675d4a755df217ba33f8d79faafcf65081ff87dccc8ad510cbb36` | Titus/Huffman → 60282 B | sprite'y wspólne: postacie, HUD, napisy (146 klatek) |
| `TERRY.SQZ` | 4352 | `22fe6709434b055ed28bd37814a128abc087329965f2e1a93cf881399dbfe314` | - | dane cracktra (tekst ASCII z liczbami) |
| `VILLE.BIN` | 2560 | `e970a667499b1b515e52a28a4baaac5fe1b91d8d692795b0221782742aa322fb` | - | tablica 256 wyzwalaczy kafli (10 B/kafel), poziom "Miasto (budowa)" |
| `VILLE.CK1` | 13178 | `4afc66221259d36f13a39891847a5dac5cd512640fc4a0ebd70ef184a579d2d4` | Titus/Huffman → 15482 B | kafle tła poziomu "Miasto (budowa)" (ILBM, kafle 0-127) |
| `VILLE.CK2` | 13534 | `96eb406828e297562ed3a9a925d8c6c1de03a444ca40870669ede6d884bf8627` | Titus/Huffman → 15882 B | kafle tła poziomu "Miasto (budowa)" (ILBM, kafle 128-255) |
| `VILLE.SQL` | 8955 | `5de0b18cbb798b14a6721cd0312c31d30aa5eeb4269b6938193bdae05212e032` | Titus/Huffman → 15360 B | mapa poziomu "Miasto (budowa)" (128 kolumn) |

## 2. Plik wykonywalny `1.EXE`

| Pole nagłówka MZ | Wartość |
|---|---|
| strony / ostatnia strona | 0xD4 / 0x54 → obraz programu 108 116 B |
| rozmiar pliku | 196 608 B → **88 492 B danych za obrazem** (overlay, dane wczytywane osobno - nie zawierają tekstów; [H] dane dźwiękowe) |
| nagłówek | 0x220 paragrafów (0x2200 B), 0x806 relokacji |
| CS:IP / SS:SP | 0000:0000 / 1C9D:00E6 |
| minalloc / maxalloc | 0x467 / 0xFFFF paragrafów |
| kompilator | Turbo C 1988 (napis "Turbo-C - Copyright (c) 1988 Borland Intl." w DGROUP) |
| DGROUP | `DS = 0x0FC0` → offset pliku `0x11E00` (offset w DS + 0x11E00 = offset w pliku) |

Model pamięci: wiele segmentów kodu (wywołania `LCALL`), dane wspólne w DGROUP.
Do analizy użyto własnej deasemblacji liniowej (capstone) wszystkich
segmentów kodu wyznaczonych z tablicy relokacji.

### Kluczowe procedury [D, większość P]

| Adres | Funkcja |
|---|---|
| `003A:0000`... | inicjalizacja; alokacja buforów funkcją DOS 48h: `[0x885C]` 64000 B (SPRITE.SQV), `[0x8860]` 6992 B (AVT), `[0x8864]` 64000 B (bufor roboczy) |
| `0A47:054E` | wczytanie i dekompresja pliku Titus (słownik do `DS:3400`, max 0x400 B; strumień czytany po 0x1000 B do `DS:3800`; **dekodowanie trwa do końca pliku**, nie do rozmiaru z nagłówka) |
| `003A:066C` | wczytanie SQV i budowa tablicy wskaźników klatek `DS:9DE9` (rozmiar klatki = h·w/2 + 4 B, z nagłówków) |
| `003A:07E4` | wczytanie ekranu ILBM: plik do `[0x8864]`, wyszukanie `CMAP`/`BODY` co 2 bajty, dekodowanie ByteRun1 do `[0x8864]+30000` |
| `003A:11CD` | dekoder ByteRun1: ciągły strumień do 32000 B (0x7D00), bajt 0x80 **nie** jest pomijany |
| `003A:1585` | odczyt surowego pliku; przy błędzie otwarcia ustawia `[0x21AD]=1` |
| `01DC:0949` | ekran tytułowy (`pres.sqz`), potem test `avtmag.sqv` → przy braku pliku pętla z ekranem `insert.sqz` |
| `01DC:09F5` | ekran wyboru postaci (`choix.sqz`) |
| `01DC:02D8`.. | mapa między poziomami (`INTER.SQZ`) |
| `003A:0287`.. | procedury wczytywania 6 poziomów (CK1, CK2, SQL, BIN, AVT, ENEMI) + kopiowanie pozycji startowych do `DS:2521`/`DS:22E3` |
| `0351:04E2` | obsługa ukończenia poziomu (`[0x28CF]`, licznik 50 klatek, po poziomie 6 powrót do wyboru postaci) |
| `0351:0553` | obsługa końca gry (`[0x28D0]`); rysowanie klatki 127 ("GAME OVER") wywołaniem `0B8F:2337` z **zapisaną w kodzie szerokością 160** i wysokością 34 w (80,63) |
| `0A47:03B0` | wypisanie komunikatu błędu: tryb 3, `INT 21h/09h` z tablicy wskaźników `DS:3384`, wyjście |
| `003A:0B3C` | test karty: `[0x21C1]` musi być 3 lub 4 (EGA/VGA), inaczej komunikat 0 |
| `0E63:0005` | zabezpieczenie dyskietki (nieaktywne po cracku), komunikat "INVALID DISK ! err#" |

### Silnik tekstu

Gra **nie zawiera fontu liter ani procedury rysującej tekst** [D]. Jedyny
font to cyfry 0-9 (8x8, 4 płaszczyzny, offset pliku `0xE4DA`) używane w HUD.
Wszystkie napisy widoczne dla gracza są bitmapami w zasobach graficznych.
Teksty ASCII w `1.EXE` to wyłącznie nazwy plików, napis kompilatora i trzy
komunikaty konsolowe. W efekcie polskie znaki nie wymagają zmian w kodzie -
wystarczą przerysowane grafiki.

### Ograniczenia istotne dla modyfikacji

| Ograniczenie | Źródło | Pewność |
|---|---|---|
| Ekran ILBM po dekompresji ≤ 30000 B (bitplany dekodowane pod +30000 w buforze 64000 B) | `003A:07E4` | [D] |
| Słownik Huffmana ≤ 0x400 B | `0A47:054E` (bufor `DS:3400`..`DS:37FF`) | [D] |
| Bity dopełnienia strumienia nie mogą tworzyć pełnych kodów (dekoder pisze do końca pliku) | `0A47:054E` | [D], oryginały: 0-1 B nadmiaru |
| `SPRITE.SQV` po dekompresji ≤ 64000 B | bufor `[0x885C]` | [D] |
| Szerokość klatek SQV wielokrotnością 16 | wszystkie klatki oryginału, blitter | [D] |
| Klatka 127 musi mieć 160x34 | stała w `0351:0588` | [D] |
| Adresowalne kafle: tylko linie 0-111 arkusza CK (indeks 7-bitowy w siatce 20x7) | mapy SQL, kod rysowania | [D] |
| Komunikaty konsolowe w 36-bajtowym bloku `DS:3388`-`DS:33AB` (dalej zmienne dekompresora) | `0A47:054E` używa `DS:33AC`+ | [D] |

## 3. Teksty widoczne dla gracza

Pełna lista z tłumaczeniami: `localization/pl/strings.json`.

| Miejsce | Tekst | Typ | Sposób zmiany | Pewność |
|---|---|---|---|---|
| `CHOIX.SQZ` linie 190-199 | ← CHOOSE YOUR PLAYER → PRESS FIRE TO START | bitmapa | przerysowanie (font `choix`) | [P] |
| `INSERT.SQZ` | INSERT DISK II | bitmapa | przerysowanie | [P] |
| `INTER.SQZ` | CHEMICALS, STORE | bitmapa (szyldy na mapie) | przerysowanie | [P] |
| `SPRITE.SQV` klatka 127 | GAME OVER | sprite 160x34 | przerysowanie | [P] |
| `SPRITE.SQV` klatka 134 | 1UP | sprite 16x7 | przerysowanie + poszerzenie do 32x7 | [D] (wyświetlenie naturalne nie zostało wywołane w teście) |
| `MAG.CK2` kafle 50-51, 96-97, 126-127; `MAG.CK1` 79, 120 | STORE, MUSIC (neony + odbicia) | kafle | przerysowanie (model neonu) | [P] |
| `MAG.CK1` kafel 76 | OPEN | kafel | pozostawione (brak miejsca) | [D] |
| `VILLE.CK1` kafle 114-117 | Y.BERTHELOT PROGRAMMER | kafle (tabliczka) | przerysowanie drugiej linii | [P] |
| `PRES.SQZ` | THE BLUES BROTHERS, ©TITUS 1991 | bitmapa | nazwa własna - bez zmian | [P] |
| kafle wielu poziomów | BLUES/BROTHERS, H·I·F·I, ELWOOD JAKE, ROCK, AKA, OK, VB | kafle | nazwy własne, graffiti - bez zmian | [D] |
| `CONCERT.CK2` linie 176-191 | TIKETS | kafle poza obszarem adresowalnym | nigdy nie wyświetlane | [D] |
| `PRES.SQZ` linie 200-399 | (drobny tekst) | pozostałość edytora | niewidoczne (dekodowane 200 linii) | [D] |
| `1.EXE` DS:3388 / DS:3399 | VIDEO ERROR. / OUT OF MEMORY. | konsola DOS | podmiana + przesunięcie + korekta tablicy wskaźników | [P] |
| `1.EXE` DS:592A | INVALID DISK !  err# | konsola | martwy kod - bez zmian | [D] |
| `RUNME.COM` | menu i komunikat pożegnalny | konsola | podmiana o równej długości | [P] |
| `INTRO.EXE` (+ JOHN/OH/TERRY.SQZ) | cracktro | grafika/tekst crackerów | poza zakresem | [D] |

Ekrany sprawdzone pod kątem napisów: wszystkie 4 pliki ILBM-ekranów, 12
arkuszy kafli (z oznaczeniem kafli faktycznie użytych w mapach), 6 pełnych
map poziomów wyrenderowanych w całości, 146 klatek `SPRITE.SQV`, 198 klatek
przeciwników (`ENEMI1-6.SQV`), 135 kafli pierwszego planu (`AVT*.SQV`) oraz
font cyfr. Gra nie ma ekranu końcowego: po ukończeniu poziomu 6 (koncert)
wraca do wyboru postaci [P].

## 4. Wykorzystanie istniejącego reverse engineeringu

- **cyxx/blues** (C, reimplementacja silnika): potwierdzone na plikach -
  kompresja Titus (Huffman), ILBM ładowany jako 320x200, SQV (h, w, dane
  planarne), układ map SQL (128 kolumn, bit 7 = arkusz CK2), BIN (10 B na
  wyzwalacz), pozycje startowe. Różnice wobec reimplementacji wykryte w tej
  analizie: dekoder DOS pracuje do końca pliku (nie do rozmiaru), ByteRun1
  nie pomija bajtu 0x80, bufor ILBM 30000 B, wpisy `TIKETS`/dolna połowa
  `PRES.SQZ` są niewidoczne. Repozytorium nie ma pliku licencji - nie
  skopiowano z niego kodu.
- **ModdingWiki** (strony The Blues Brothers / Map Format / Sprite Format):
  opisy zgodne z powyższym; formaty zweryfikowano na rzeczywistych plikach
  (round-trip 34 skompresowanych zasobów, patrz `tools/extract.py`).

## 5. Co można zmienić i jak

1. **Bezpośrednio (dane)**: wszystkie grafiki z napisami - dekompresja,
   edycja pikseli, ponowne kodowanie z zachowaniem limitów z sekcji 2.
2. **Podmiana ciągów o zgodnym rozmiarze**: menu `RUNME.COM`.
3. **Przeniesienie tekstu w obrębie bloku danych z korektą odwołań**:
   komunikaty błędów `1.EXE` (tablica wskaźników `DS:3384`).
4. **Kod x86 nie wymagał zmian** - żaden tekst nie jest generowany przez kod,
   a font cyfr nie potrzebuje polskich znaków.

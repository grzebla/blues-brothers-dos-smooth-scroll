# Wyniki testów DOSBox-X

Gra: `build/game`

## boot — ZALICZONY
- [x] nagranie powstało hard_000.avi, 1_000.avi
- [x] ekran tytułowy wyświetlony (PRES.SQZ) zgodność 1.000 w t=7.0055879999999995 s
- [x] polski pasek wyboru postaci (CHOIX.SQZ, linie 190-199) zgodność 1.000 w t=30.476448 s
- [x] dźwięk/muzyka nagrane (niezerowy sygnał) RMS 6293, szczyt 32768
- [x] menu RUNME.COM po polsku 
- _czas: 53 s_

## all_levels — ZALICZONY
- [x] poziom 1 wczytany i wyświetlony (paleta poziomu) 
- [x] poziom 2 wczytany i wyświetlony (paleta poziomu) 
- [x] poziom 3 wczytany i wyświetlony (paleta poziomu) 
- [x] poziom 4 wczytany i wyświetlony (paleta poziomu) 
- [x] poziom 5 wczytany i wyświetlony (paleta poziomu) 
- [x] poziom 6 wczytany i wyświetlony (paleta poziomu) 
- [x] ikony HUD (klatki 135-144 za poszerzoną klatką 134) poprawne we wszystkich poziomach p1: 1.000, p2: 1.000, p3: 1.000, p4: 1.000, p5: 1.000, p6: 1.000
- [x] mapa INTER z polskimi szyldami przed poziomami 10 wystąpień
- [x] po ukończeniu poziomu 6 gra wraca do ekranu wyboru postaci inny -> CHOIX -> inny -> INTER -> inny -> czarny
- _oś czasu: inny@0.0s, czarny@2.6s, inny@4.1s, czarny@15.6s, inny@16.1s, CHOIX@17.1s, inny@23.1s, czarny@24.1s, inny@25.6s, INTER@26.1s, inny@31.1s, poziom 1@32.6s, inny@34.6s, czarny@35.1s, inny@36.1s, INTER@36.6s, inny@42.6s, poziom 2@43.6s, czarny@46.1s, INTER@47.6s, inny@53.6s, czarny@54.1s, inny@54.6s, poziom 3@55.1s, czarny@57.1s, inny@58.6s, INTER@59.1s, inny@64.6s, poziom 4@66.1s, czarny@68.1s, inny@69.6s, INTER@70.1s, inny@75.5s, poziom 5@77.0s, inny@79.0s, czarny@80.0s, inny@80.5s, INTER@81.0s, inny@85.5s, poziom 6@87.0s, inny@90.5s, CHOIX@91.0s, inny@114.0s, INTER@117.0s, inny@121.5s, czarny@122.5s, poziom 1@123.0s, czarny@125.0s, inny@126.5s, INTER@127.0s, inny@132.5s, poziom 2@134.0s, czarny@136.0s, inny@137.5s, INTER@138.0s, czarny@144.0s, poziom 3@145.0s, czarny@147.5s, INTER@149.0s_
- _czas: 203 s_

## gameover — ZALICZONY
- [x] sprite "KONIEC GRY" wyświetlony w grze zgodność 1.000 w (80,77), t=32.630916 s
- _czas: 119 s_

## mag_store — ZALICZONY
- [x] SKLEP neon (MAG.CK2 kafle 50-51) zgodność 1.000 w (224,38), t=31.931784 s
- _czas: 92 s_

## mag_music — ZALICZONY
- [x] PŁYTY neon (MAG.CK2 kafle 96-97) zgodność 1.000 w (160,38), t=32.916276 s
- _czas: 92 s_

## mag_mirror — ZALICZONY
- [x] SKLEP odbicie (MAG.CK2 kafle 126-127) zgodność 1.000 w (96,94), t=33.03042 s
- [x] PŁYTY odbicie (MAG.CK1 kafle 79+120) zgodność 1.000 w (160,94), t=33.03042 s
- _czas: 122 s_

## ville_plaque — ZALICZONY
- [x] PROGRAMISTA tabliczka (VILLE.CK1 kafle 114-117) zgodność 1.000 w (96,110), t=34.471488 s
- _czas: 113 s_

## insert_disk — ZALICZONY
- [x] polski ekran "WŁÓŻ DYSK II" zgodność 1.000 w t=20.531652 s
- _czas: 40 s_

## runme_ega — ZALICZONY
- [x] oryginał i wersja PL uruchamiają te same programy oryginał: ['hard'], PL: ['hard']
- [x] komunikat po wyjściu przetłumaczony (zrzut: runme_exit_message.png) 
- _czas: 16 s_

## console — ZALICZONY
- [x] konsola RUNME: runme.line_presents 'P R Z E D S T A W I A'
- [x] konsola RUNME: runme.line_title 'Blues Brothers firmy TITUS'
- [x] konsola RUNME: runme.line_intro '[3] - Intro TDT/TRSI...'
- [x] konsola RUNME: runme.exit_message 'Kto inny da wam takie rzeczy?'
- [x] 1.EXE na karcie CGA: 'BRAK EGA/VGA.' BRAK EGA/VGA.; C:\>exit
- [x] komunikat nr 1 z tablicy (brak pamięci): 'BRAK RAM-U.' BRAK RAM-U.; C:\>exit
- _czas: 16 s_

## demo_regression — ZALICZONY
- [x] wszystkie różnice wynikają z lokalizacji (tekst, napisy, neony) niewyjaśnione: []
- [x] większość klatek identyczna z oryginałem 187/390
- _klasyfikacja klatek: identyczne=187, menu tekstowe=12, pasek CHOIX=94, szyldy INTER=46, neony poziomu 1=37, przejście/zanikanie=0, animacja palety=14, NIEWYJAŚNIONE=0_
- _czas: 296 s_

## smooth_scroll — ZALICZONY
- [x] kamera przesuwa się w poziomie 201 zmian
- [x] przesunięcia co piksel (nie tylko wielokrotności 8) wartości: [-6, -5, -4, -3, -2, -1]
- [x] brak skoków powyżej 16 px na klatkę max |dx| = 6
- _przesunięcia poziome (px): [-6, -5, -4, -3, -2, -1]_
- _czas: 100 s_

## polish_glyphs — ZALICZONY
- [x] pangram 'ZAŻÓŁĆ GĘŚLĄ' / 'JAŹŃ ĄĆĘŁŃÓŚŹŻ' wyświetlony w grze zgodność 1.000, t=31.047168 s
- _czas: 47 s_

## direct_exe — ZALICZONY
- [x] 1.EXE uruchomione bezpośrednio pokazuje polski ekran wyboru zgodność 1.000, t=28.050888 s
- _czas: 45 s_

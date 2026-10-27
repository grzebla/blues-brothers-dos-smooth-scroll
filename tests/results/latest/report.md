# Wyniki testów DOSBox-X

Gra: `build/game`

## boot — ZALICZONY
- [x] nagranie powstało hard_000.avi, 1_000.avi
- [x] ekran tytułowy wyświetlony (PRES.SQZ) zgodność 1.000 w t=7.41936 s
- [x] polski pasek wyboru postaci (CHOIX.SQZ, linie 190-199) zgodność 1.000 w t=30.89022 s
- [x] dźwięk/muzyka nagrane (niezerowy sygnał) RMS 6255, szczyt 32768
- [x] menu RUNME.COM po polsku 
- _czas: 52 s_

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
- _oś czasu: inny@0.0s, czarny@3.0s, inny@4.5s, czarny@16.0s, inny@16.5s, CHOIX@17.5s, inny@23.5s, czarny@24.5s, inny@26.0s, INTER@26.5s, inny@31.5s, poziom 1@33.0s, inny@35.0s, czarny@35.5s, inny@36.5s, INTER@37.0s, inny@43.0s, poziom 2@44.0s, czarny@46.5s, INTER@48.0s, inny@53.9s, czarny@54.4s, poziom 3@55.4s, czarny@57.4s, inny@58.9s, INTER@59.4s, inny@64.9s, poziom 4@66.4s, czarny@68.4s, inny@69.9s, INTER@70.4s, inny@76.4s, poziom 5@77.4s, inny@79.4s, czarny@80.4s, inny@80.9s, INTER@81.4s, inny@85.9s, poziom 6@87.4s, inny@90.9s, CHOIX@91.4s, inny@114.4s, INTER@117.4s, inny@121.9s, czarny@122.9s, poziom 1@123.4s, czarny@125.4s, inny@126.9s, INTER@127.4s, inny@132.8s, poziom 2@134.3s, czarny@136.3s, inny@137.8s, INTER@138.3s, inny@144.3s, poziom 3@145.3s, inny@147.8s, czarny@148.8s, inny@149.3s, INTER@149.8s_
- _czas: 200 s_

## gameover — ZALICZONY
- [x] sprite "KONIEC GRY" wyświetlony w grze zgodność 1.000 w (80,77), t=33.116028 s
- _czas: 110 s_

## mag_store — ZALICZONY
- [x] SKLEP neon (MAG.CK2 kafle 50-51) zgodność 1.000 w (160,30), t=32.930544000000005 s
- _czas: 86 s_

## mag_music — ZALICZONY
- [x] PŁYTY neon (MAG.CK2 kafle 96-97) zgodność 1.000 w (160,30), t=32.930544000000005 s
- _czas: 86 s_

## mag_mirror — ZALICZONY
- [x] SKLEP odbicie (MAG.CK2 kafle 126-127) zgodność 1.000 w (96,94), t=32.916276 s
- [x] PŁYTY odbicie (MAG.CK1 kafle 79+120) zgodność 1.000 w (160,94), t=32.916276 s
- _czas: 113 s_

## ville_plaque — ZALICZONY
- [x] PROGRAMISTA tabliczka (VILLE.CK1 kafle 114-117) zgodność 1.000 w (96,110), t=32.844936000000004 s
- _czas: 106 s_

## insert_disk — ZALICZONY
- [x] polski ekran "WŁÓŻ DYSK II" zgodność 1.000 w t=20.545920000000002 s
- _czas: 39 s_

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
- _czas: 15 s_

## demo_regression — ZALICZONY
- [x] wszystkie różnice wynikają z lokalizacji (tekst, napisy, neony) niewyjaśnione: []
- [x] większość klatek identyczna z oryginałem 187/390
- _klasyfikacja klatek: identyczne=187, menu tekstowe=12, pasek CHOIX=94, szyldy INTER=46, neony poziomu 1=37, przejście/zanikanie=1, animacja palety=13, NIEWYJAŚNIONE=0_
- _czas: 290 s_

## polish_glyphs — ZALICZONY
- [x] pangram 'ZAŻÓŁĆ GĘŚLĄ' / 'JAŹŃ ĄĆĘŁŃÓŚŹŻ' wyświetlony w grze zgodność 1.000, t=30.861684 s
- _czas: 46 s_

## direct_exe — ZALICZONY
- [x] 1.EXE uruchomione bezpośrednio pokazuje polski ekran wyboru zgodność 1.000, t=28.050888 s
- _czas: 45 s_

# Wyniki testów DOSBox-X

Gra: `build/release-pl-smooth/game`

Data: 2026-11-12. DOSBox-X 2026.01.02 SDL1, macOS arm64, fixed 20000 cykli.
Testy działały bez okien i dźwięku hosta (Varlock, SDL dummy, `nosound=true`).
Awaria nagrania `demo_regression` pozostała odnotowana poniżej; scenariusz
**zaliczono po niezależnym powtórzeniu** w 2026.10.01 SDL2:
[raport powtórzenia](../release-1.1.0-regression/report.md).

## boot — ZALICZONY
- [x] nagranie powstało hard_000.avi, 1_000.avi
- [x] ekran tytułowy wyświetlony (PRES.SQZ) zgodność 1.000 w t=5.607324 s
- [x] polski pasek wyboru postaci (CHOIX.SQZ, linie 190-199) zgodność 1.000 w t=31.075704 s
- [x] dźwięk/muzyka nagrane (niezerowy sygnał) RMS 6264, szczyt 32768
- [x] menu RUNME.COM po polsku
- _czas: 66 s_

## all_levels — ZALICZONY
- [x] poziom 1 wczytany i wyświetlony (paleta poziomu)
- [x] poziom 2 wczytany i wyświetlony (paleta poziomu)
- [x] poziom 3 wczytany i wyświetlony (paleta poziomu)
- [x] poziom 4 wczytany i wyświetlony (paleta poziomu)
- [x] poziom 5 wczytany i wyświetlony (paleta poziomu)
- [x] poziom 6 wczytany i wyświetlony (paleta poziomu)
- [x] ikony HUD (klatki 135-144 za poszerzoną klatką 134) poprawne we wszystkich poziomach p1: 1.000, p2: 1.000, p3: 1.000, p4: 1.000, p5: 1.000, p6: 1.000
- [x] mapa INTER z polskimi szyldami przed poziomami 10 wystąpień
- [x] po ukończeniu poziomu 6 gra wraca do ekranu wyboru postaci czarny -> inny -> CHOIX -> inny -> czarny -> inny
- _oś czasu: inny@0.0s, czarny@3.1s, inny@4.6s, czarny@14.6s, inny@16.6s, CHOIX@17.1s, inny@23.1s, czarny@23.6s, inny@25.6s, INTER@26.1s, inny@30.6s, czarny@31.1s, poziom 1@32.1s, czarny@34.1s, inny@35.6s, INTER@36.1s, inny@41.6s, czarny@42.1s, poziom 2@43.1s, czarny@45.1s, inny@46.6s, INTER@47.1s, czarny@53.0s, poziom 3@54.0s, inny@56.0s, czarny@56.5s, inny@57.5s, INTER@58.0s, inny@64.0s, czarny@64.5s, poziom 4@65.0s, czarny@67.5s, inny@69.0s, INTER@69.5s, inny@75.0s, czarny@75.5s, poziom 5@76.5s, czarny@78.5s, inny@80.0s, INTER@80.5s, inny@85.0s, czarny@85.5s, poziom 6@86.0s, czarny@88.5s, inny@89.5s, CHOIX@90.5s, inny@113.5s, czarny@114.0s, inny@116.0s, INTER@116.5s, czarny@121.0s, poziom 1@122.0s, czarny@124.5s, inny@126.0s, INTER@126.5s, inny@132.0s, czarny@132.4s, inny@132.9s, poziom 2@133.4s, czarny@135.4s, inny@136.9s, INTER@137.4s, inny@142.9s, czarny@143.4s, poziom 3@144.4s, czarny@146.4s, inny@147.9s, INTER@148.4s_
- _czas: 239 s_

## demo_regression — NIEZALICZONY
- [ ] scenariusz wykonany bez wyjątku error('unpack_from requires a buffer of at least 315692 bytes for unpacking 4 bytes at offset 315688 (actual buffer size is 315684)')
- _czas: 153 s_

## smooth_scroll — ZALICZONY
- [x] kamera przesuwa się w poziomie 200 zmian
- [x] przesunięcia co piksel (nie tylko wielokrotności 8) wartości: [-6, -5, -4, -3, -2, -1]
- [x] brak skoków powyżej 16 px na klatkę max |dx| = 6
- _przesunięcia poziome (px): [-6, -5, -4, -3, -2, -1]_
- _czas: 112 s_

## direct_exe — ZALICZONY
- [x] 1.EXE uruchomione bezpośrednio pokazuje polski ekran wyboru zgodność 1.000, t=28.050888 s
- _czas: 48 s_

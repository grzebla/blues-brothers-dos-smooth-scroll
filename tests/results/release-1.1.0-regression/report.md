# Wyniki testów DOSBox-X

Argument `--game`: `build/release-pl-smooth/game`.
Ten scenariusz **nie używa go do porównania**: niezależnie buduje polski profil
z `--classic-scroll` i porównuje go z czystym `original/`.

Data: 2026-11-12. DOSBox-X **2026.10.01 SDL2**, commit `b6abbd5`, macOS arm64.
SVGA S3, 16 MB, normal core, fixed 20000 cykli; Varlock, SDL dummy video/audio,
`nosound=true` — bez okien i słyszalnego dźwięku na hoście.
To kompletne powtórzenie scenariusza, którego nagranie w 2026.01.02 zostało
przerwane awarią renderera. Poprzedni błąd zachowano w raporcie silnika.

## demo_regression — ZALICZONY
- [x] wszystkie różnice wynikają z lokalizacji (tekst, napisy, neony) niewyjaśnione: []
- [x] większość klatek identyczna z oryginałem 200/391
- _klasyfikacja klatek: identyczne=200, menu tekstowe=13, pasek CHOIX=94, szyldy INTER=46, neony poziomu 1=37, przejście/zanikanie=1, animacja palety=0, NIEWYJAŚNIONE=0_
- _czas: 349 s_

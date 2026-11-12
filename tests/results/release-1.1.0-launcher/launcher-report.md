# Testy menu DOS — wydanie 1.1.0

Testy fixture używają autorskiego EXE; boot uruchamia prawdziwą grę.

Data: 2026-11-12. DOSBox-X **2026.10.01**, commit `b6abbd5`, macOS ARM SDL2.
VGA/SVGA S3, 16 MB, `core=normal`, `cycles=fixed 20000`.
Varlock wymusza SDL dummy video/audio; mikser testowy `nosound=true`.
Nie otwierano okien ani nie odtwarzano dźwięku na hoście; audio nagrywano do asercji.
Polecenie: `python3 tests/run_launcher_tests.py --game build/release-bundle --out tests/results/release-1.1.0-launcher --dosbox /ścieżka/do/DOSBox-X-2026.10.01-SDL2`.

Testowany `START.COM`: 2977 B, SHA-256
`a8d84f28260f29aa5af4d208c2d674c1fe6f90bc2ea691a58b3d7d48794b834a`.
Poprzednie próby w DOSBox-X 2026.01.02 kończyły się awarią renderera hosta;
nie zaliczono ich. Poniższe 13 wyników pochodzi z kompletnego ponowienia w 2026.10.01.
Zrzuty końcowych menu sprawdzono wizualnie: poprawne wyśrodkowanie i polskie
znaki, brak blokujących artefaktów. Zrzuty wyboru postaci potwierdzają ekran
oraz język komunikatu, nie pełny przebieg jego animacji.

- [x] **fixture-en-original**: wybrano=['ENORIG'], powrót CWD='C:\\OTHER'
- [x] **fixture-en-smooth**: wybrano=['ENSMOOTH'], powrót CWD='C:\\OTHER'
- [x] **fixture-pl-original**: wybrano=['PLORIG'], powrót CWD='C:\\OTHER'
- [x] **fixture-pl-smooth**: wybrano=['PLSMOOTH'], powrót CWD='C:\\OTHER'
- [x] **fixture-back-invalid**: wybrano=['ENSMOOTH'], powrót CWD='C:\\OTHER'
- [x] **fixture-exit**: wybrano=[], powrót CWD='C:\\OTHER'
- [x] **fixture-other-drive**: D:\OTHER
- [x] **fixture-missing-exe**: launcher sygnalizuje błąd kodem wyjścia
- [x] **fixture-reject-ega**: VGA wymagane, kod błędu i brak uruchomionego dziecka
- [x] **boot-en-original**: pasek języka=1.000 w t=36.112308 s; audio=True
- [x] **boot-en-smooth**: pasek języka=1.000 w t=36.126576 s; audio=True
- [x] **boot-pl-original**: pasek języka=1.000 w t=36.126576 s; audio=True
- [x] **boot-pl-smooth**: pasek języka=1.000 w t=36.140844 s; audio=True

Czas: 270 s.

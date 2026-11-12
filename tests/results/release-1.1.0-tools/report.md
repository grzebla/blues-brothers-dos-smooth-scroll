# Testy narzędzi i instalatora — 1.1.0

Data: 2026-11-12. Host: macOS arm64, Python 3.9.6.
Polecenie: `bash tests/run_tests.sh` — kod zakończenia **0**.

- `tests/test_tools.py`: **11/11 OK** (31,935 s).
- `tests/test_bundle.py`: **12/12 OK** (46,621 s).

Zakres narzędzi: identyfikacja gry, round-trip kompresji i formatów ILBM/SQV,
model przekroczeń dekodera DOS, schemat tłumaczeń, pokrycie fontów i limity
komunikatów, deterministyczny build i nienaruszalność źródła, odmowa obcej bazy.

Zakres instalatora: wszystkie cztery profile zgodne z buildami; instalacja
bez site-packages (`python -I -S`); `--check` bez zapisów; brak nadpisywania
istniejącego wyniku; odmowa nakładających się ścieżek, brakujących/uszkodzonych
plików (także niezmienianych przez patch), symlinków i kolizji nazw; walidacja
manifestu; stare CLI jako błąd bez zapisów; brak publikacji wyniku przy błędzie
ostatniego profilu; usunięcie własnego stagingu po błędzie zapisu;
deterministyczny ZIP, whitelista zawartości i instalacja po rozpakowaniu.

Kolizję nazw ignorujących wielkość liter sprawdzano warunkowo, zależnie od
możliwości systemu plików. Autotest generatora również zakończył się powodzeniem.
Te testy nie uruchamiają emulatora ani nie potwierdzają naturalnego przejścia gry.

## Końcowy artefakt

- Dwa niezależne wywołania generatora wydania dały identyczne bajtowo ZIP-y
  i pliki `SHA256SUMS` (`cmp`, kod 0).
- ZIP: `blues-brothers-1.1.0-patch.zip`, **45956 B**.
- SHA-256: `87e753c34a46a161ac90f369ae8a259ac7ad9414f2f358881ee65afc469f73f7`.
- Launcher: **2977 B**, SHA-256
  `a8d84f28260f29aa5af4d208c2d674c1fe6f90bc2ea691a58b3d7d48794b834a`.
- Sprawdzono integralność ZIP i whitelistę siedmiu plików; brak pełnych plików gry.
- Ponowna instalacja z rozpakowanego końcowego ZIP-a przez `python -I -S`,
  `--check` i `--output`: sukces. Wszystkie **200 plików** czterech profili
  porównano bajtowo z niezależnymi buildami. Hash launchera jest zgodny
  z manifestem i testowanym plikiem.
- Dodatkowy rzeczywisty start PL + smooth **z instalacji końcowego ZIP-a**
  w DOSBox-X 2026.10.01 SDL2: pasek języka 1,000 w t=36,126576 s,
  nagrane audio obecne, kod 0. Test bez okien i dźwięku hosta,
  z końcowym harness i wyłączonym wyjściem MIDI.

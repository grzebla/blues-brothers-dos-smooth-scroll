# Polecenie ustawienia cykli w DOSBox-X

Data: 2026-11-12. DOSBox-X **2026.10.01 SDL2**, macOS arm64.

- Użyto projektowego `tests/dosbox_harness.py` oraz autorskiego `TEST.BAT`.
- Emulator uruchomiono z początkowym ustawieniem **3000 cykli**.
- W powłoce DOS wykonano:

  ```text
  config -set cpu cycles=fixed 20000
  config -get cpu cycles > C:\CYCLES.TXT
  ```

- Odczytany plik zawierał **`fixed 20000`**. Asercja zaliczona, emulator zakończył pracę kodem 0.
- Test działał przez Varlock z SDL dummy video/audio, `nosound=true` i `mididevice=none`: bez okien, przejmowania fokusu i dźwięku hosta.

Wynik potwierdza działanie polecenia `config -set`, nie jest ponownym testem rozgrywki ani całej macierzy zgodności.
Skrót `cycles fixed 20000` wymaga w DOSBox-X opcjonalnej obsługi ustawień jako poleceń powłoki; nie należy zakładać, że jest dostępny domyślnie.

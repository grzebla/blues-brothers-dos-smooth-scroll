#!/bin/sh
# Uruchamia testy polonizacji.
#   tests/run_tests.sh            - testy narzędzi (szybkie, bez emulatora)
#   tests/run_tests.sh --dosbox   - dodatkowo pełne testy w DOSBox-X (ok. 20 minut)
set -e
cd "$(dirname "$0")/.."
python3 tests/test_tools.py
python3 tests/test_bundle.py
if [ "$1" = "--dosbox" ]; then
    python3 tools/build.py --source original --locale pl --output build
    python3 tests/run_dosbox_tests.py --game build/game --out tests/results/latest
fi

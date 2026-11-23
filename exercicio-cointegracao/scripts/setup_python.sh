#!/usr/bin/env bash
# Instalação isolada; pode ser chamada de qualquer diretório.
set -euo pipefail
EXERCISE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m venv "$EXERCISE_DIR/.venv"
"$EXERCISE_DIR/.venv/bin/python" -m pip install -r "$EXERCISE_DIR/requirements.txt"
"$EXERCISE_DIR/.venv/bin/python" -m ipykernel install --user \
  --name ead6034-cointegracao --display-name 'Python 3 (EAD6034 — Cointegração)'

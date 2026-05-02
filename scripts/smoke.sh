#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_BIN="${PYTHON}"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

"${PYTHON_BIN}" -m pytest
PYTHONPATH=src "${PYTHON_BIN}" -m statlean_agent.cli blueprint-status --blueprint config/statlean_blueprint.json >/tmp/statlean-blueprint-status.txt
PYTHONPATH=src "${PYTHON_BIN}" -m statlean_agent.cli seed-benchmarks --output "${TMP_DIR}/seeds.jsonl"
cmp "${TMP_DIR}/seeds.jsonl" benchmarks/seeds.jsonl
PYTHONPATH=src "${PYTHON_BIN}" -m statlean_agent.cli list-benchmarks --input benchmarks/seeds.jsonl
PYTHONPATH=src "${PYTHON_BIN}" -m statlean_agent.cli render-task erm_oracle_ineq_seed --input benchmarks/seeds.jsonl >/tmp/statlean-render.lean
PYTHONPATH=src "${PYTHON_BIN}" -m statlean_agent.cli index-premises --root . --output /tmp/statlean-premises.jsonl
PYTHONPATH=src "${PYTHON_BIN}" -m statlean_agent.cli search-premises "oracle excess risk" --index /tmp/statlean-premises.jsonl >/tmp/statlean-premise-search.txt
PYTHONPATH=src "${PYTHON_BIN}" -m statlean_agent.cli build-training-manifest --benchmarks benchmarks/seeds.jsonl --output /tmp/statlean-training-manifest.json
PYTHONPATH=src "${PYTHON_BIN}" -m statlean_agent.cli empirical-process-external-slice --output "${TMP_DIR}/empirical-process-external-slice.json"
cmp "${TMP_DIR}/empirical-process-external-slice.json" artifacts/evaluation/empirical-process-external-slice.json
PYTHONPATH=src "${PYTHON_BIN}" -m statlean_agent.cli vdvw-theorem-inventory --output "${TMP_DIR}/vdvw-theorem-inventory.json"
cmp "${TMP_DIR}/vdvw-theorem-inventory.json" artifacts/research/vdvw-theorem-inventory.json

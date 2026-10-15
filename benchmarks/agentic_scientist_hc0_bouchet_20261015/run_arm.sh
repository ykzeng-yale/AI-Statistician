#!/bin/bash
set -euo pipefail
umask 077
module load Python/3.12.3-GCCcore-13.3.0
module load nodejs/24.12.0-GCCcore-13.3.0
module load local-coding-agents/1.1
ROOT="/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-v3-Pi-20261015"
arm="${1:?Specify stock or statistical}"
case "$arm" in stock|statistical) ;; *) exit 2 ;; esac
export AISTAT_ARM_ROOT="$ROOT/$arm"
test ! -e "$AISTAT_ARM_ROOT/results"
cd "$AISTAT_ARM_ROOT"
printf 'job=%s arm=%s host=%s started=%s\n' "$SLURM_JOB_ID" "$arm" "$(hostname)" "$(date -Is)"
git -C "$ROOT/upstream" rev-parse HEAD
git -C "$ROOT/upstream" diff --exit-code
node --version
pi --version
export YCRC_THINKING=1
pi --list-models
export HEADLESS_BIN="$ROOT/tools/node_modules/.bin/headless"
export PI_CODING_AGENT_BIN="$ROOT/pi_project.sh"
export AGENTIC_TEMP_ROOT="$ROOT/temp-$arm"
export TMPDIR="$AGENTIC_TEMP_ROOT"
export UV_CACHE_DIR="$ROOT/cache/uv"
export npm_config_cache="$ROOT/cache/npm"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$AGENTIC_TEMP_ROOT"
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN OPENAI_API_KEY OPENROUTER_API_KEY
unset HEADLESS_BILLING CHATGPT_SUBSCRIPTION
"$ROOT/bootstrap-env/bin/uv" pip install --python "$ROOT/upstream/.venv/bin/python" \
  -r "$AISTAT_ARM_ROOT/task/requirements.txt"
"$ROOT/bootstrap-env/bin/uv" pip freeze --python "$ROOT/upstream/.venv/bin/python" \
  > "$AISTAT_ARM_ROOT/python_environment.txt"
"$ROOT/upstream/.venv/bin/python" - "$AISTAT_ARM_ROOT" <<'PY'
import hashlib
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
manifest = json.loads((root / "prepared_inputs.json").read_text())
for name, expected in manifest["files"].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
print("Frozen prepared inputs verified")
PY
export WRAPPER_PYTHON="$ROOT/upstream/.venv/bin/python"
args=(
  --agent pi --agent-model bouchet/ycrc-local-think
  --task-dir "$AISTAT_ARM_ROOT/task"
  --results-dir "$AISTAT_ARM_ROOT/results"
  --global-memory-dir "$AISTAT_ARM_ROOT/results"
  --rubrics-file "$AISTAT_ARM_ROOT/task/rubrics.json"
  --attempt-id "hc0_bouchet_${arm}_01" --idea-dir-name hc0_reconstruction
  --max-program-evals-per-attempt 1 --harness-evaluated-attempt
  --agent-timeout-seconds 5400 --harness-evaluation-timeout-seconds 1800
)
if [ "$arm" = statistical ]; then
  args+=(--instruct "$AISTAT_ARM_ROOT/investigate.md")
fi
bash "$ROOT/upstream/src/scripts/run.sh" "${args[@]}"

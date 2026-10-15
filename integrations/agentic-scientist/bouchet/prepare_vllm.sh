#!/bin/bash
# Install a resolved upstream runtime in task storage; no GPU or inference.
set -euo pipefail
umask 077
root="${1:?Supply the task-owned Bouchet model directory}"
uv="${2:?Supply the existing uv executable}"
module load Python/3.12.3-GCCcore-13.3.0
test -s "$root/verified-model-files.json"
test ! -e "$root/serve-env"
cd "$root"
printf '%s  %s\n' 77df8a4c761d31626671a829ed344985eeeb3935ad1a75e3bc7fcd0e16dff2f1 \
  vllm_linux_py312_requirements.txt | sha256sum --check
mkdir "runtime-$SLURM_JOB_ID"
export TMPDIR=/tmp UV_CACHE_DIR="$root/uv-cache"
export UV_CONCURRENT_DOWNLOADS=2 UV_CONCURRENT_INSTALLS=2
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN ANTHROPIC_API_KEY OPENAI_API_KEY
printf 'job=%s host=%s started=%s\n' "$SLURM_JOB_ID" "$(hostname)" "$(date -Is)"
getconf GNU_LIBC_VERSION
python --version
"$uv" --version
"$uv" venv --python "$(command -v python)" "$root/serve-env"
"$uv" pip sync --python "$root/serve-env/bin/python" \
  --require-hashes --no-build "$root/vllm_linux_py312_requirements.txt"
"$uv" pip check --python "$root/serve-env/bin/python"
"$uv" pip freeze --python "$root/serve-env/bin/python" > "runtime-$SLURM_JOB_ID/environment.txt"
"$root/serve-env/bin/python" -c 'from importlib.metadata import version; assert version("vllm") == "0.31.0"; print("vLLM metadata verified; GPU compatibility and inference NOT TESTED")'
du -sh "$root"

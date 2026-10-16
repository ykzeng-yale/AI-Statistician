#!/bin/bash
# One allocated GPU, pinned upstream serving, and existing product API transport.
set -euo pipefail
umask 077
root="${1:?Supply the staged model directory}"
code="${2:?Supply the frozen product code directory}"
archive_sha="${3:?Supply the verified pinned runtime archive SHA-256}"
module load Python/3.12.3-GCCcore-13.3.0
module load CUDA/12.9.1
test -s "$root/runtime-29685758/environment.txt"
test -s "$root/verified-model-files.json"
run="$root/probe-$SLURM_JOB_ID"
mkdir "$run"
cd "$run"
local_root=$(mktemp -d "/tmp/ai-stat-$SLURM_JOB_ID-XXXXXX")
server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; fi
  rm -rf -- "$local_root"
}
trap cleanup EXIT
trap 'exit 143' TERM INT
printf '%s  %s\n' "$archive_sha" "$root/serve-env-node-local.tar" | sha256sum --check
tar -xf "$root/serve-env-node-local.tar" -C "$local_root"
python="$local_root/serve-env/bin/python"
export PATH="$local_root/serve-env/bin:$PATH"
export TMPDIR=/tmp HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export VLLM_CACHE_ROOT="$local_root/vllm-cache" OMP_NUM_THREADS=8
export FLASHINFER_WORKSPACE_BASE="$local_root/flashinfer"
export AI_STATISTICIAN_LOCAL_BASE_URL=http://127.0.0.1:8081/v1
export PYTHONPATH="$code"
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN ANTHROPIC_API_KEY OPENAI_API_KEY
printf 'job=%s host=%s started=%s\n' "$SLURM_JOB_ID" "$(hostname)" "$(date -Is)"
nvidia-smi --query-gpu=name,uuid,driver_version,memory.total --format=csv > gpu.csv
nvcc --version > nvcc.txt
ninja --version > ninja.txt
c++ --version > compiler.txt
module list > modules.txt 2>&1
"$python" -c 'import torch; print(torch.__version__, torch.version.cuda); assert torch.cuda.is_available(); print(torch.cuda.get_device_name())' > torch.txt
args=(serve "$root/model" --served-model-name Qwen3.8-27B-pinned
  --host 127.0.0.1 --port 8081 --dtype bfloat16 --kv-cache-dtype auto
  --max-model-len 262144 --max-num-seqs 1 --max-num-batched-tokens 8192
  --language-model-only --gpu-memory-utilization 0.9 --seed 20261015
  --generation-config "$root/model"
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder)
printf '%q ' "$python" -m vllm.entrypoints.cli.main "${args[@]}" > serve_command.txt
printf '\n' >> serve_command.txt
"$python" -m vllm.entrypoints.cli.main "${args[@]}" > server.log 2>&1 &
server_pid=$!
deadline=$((SECONDS + 1800))
until curl --noproxy '*' --silent --fail --max-time 5 http://127.0.0.1:8081/health > /dev/null; do
  kill -0 "$server_pid" || { wait "$server_pid"; exit 1; }
  if (( SECONDS >= deadline )); then printf 'Server readiness timed out\n' >&2; exit 1; fi
  sleep 5
done
curl --noproxy '*' --silent --fail http://127.0.0.1:8081/v1/models > models.json
"$python" "$root/probe_local_api.py" \
  --model Qwen3.8-27B-pinned --output "$run/api" > client.log 2>&1
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv > gpu_after.csv
printf 'Deployment probe finished; scientific workflow NOT RUN\n'

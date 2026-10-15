#!/bin/bash
# One allocated GPU, pinned upstream serving, and existing product API transport.
set -euo pipefail
umask 077
root="${1:?Supply the staged model directory}"
code="${2:?Supply the frozen product code directory}"
module load Python/3.12.3-GCCcore-13.3.0
test -s "$root/runtime-29685758/environment.txt"
test -s "$root/verified-model-files.json"
run="$root/probe-$SLURM_JOB_ID"
mkdir "$run"
cd "$run"
export TMPDIR=/tmp HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export VLLM_CACHE_ROOT="$run/vllm-cache" OMP_NUM_THREADS=8
export AI_STATISTICIAN_LOCAL_BASE_URL=http://127.0.0.1:8081/v1
export PYTHONPATH="$code"
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN ANTHROPIC_API_KEY OPENAI_API_KEY
printf 'job=%s host=%s started=%s\n' "$SLURM_JOB_ID" "$(hostname)" "$(date -Is)"
nvidia-smi --query-gpu=name,uuid,driver_version,memory.total --format=csv > gpu.csv
"$root/serve-env/bin/python" -c 'import torch; print(torch.__version__, torch.version.cuda); assert torch.cuda.is_available(); print(torch.cuda.get_device_name())' > torch.txt
args=(serve "$root/model" --served-model-name Qwen3.8-27B-pinned
  --host 127.0.0.1 --port 8081 --dtype bfloat16 --kv-cache-dtype auto
  --max-model-len 262144 --max-num-seqs 1 --max-num-batched-tokens 8192
  --language-model-only --gpu-memory-utilization 0.9 --seed 20261015
  --generation-config "$root/model"
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder)
printf '%q ' "$root/serve-env/bin/vllm" "${args[@]}" > serve_command.txt
printf '\n' >> serve_command.txt
"$root/serve-env/bin/vllm" "${args[@]}" > server.log 2>&1 &
server_pid=$!
cleanup() { kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; }
trap cleanup EXIT
trap 'exit 143' TERM INT
deadline=$((SECONDS + 1800))
until curl --noproxy '*' --silent --fail --max-time 5 http://127.0.0.1:8081/health > /dev/null; do
  kill -0 "$server_pid" || { wait "$server_pid"; exit 1; }
  if (( SECONDS >= deadline )); then printf 'Server readiness timed out\n' >&2; exit 1; fi
  sleep 5
done
curl --noproxy '*' --silent --fail http://127.0.0.1:8081/v1/models > models.json
"$root/serve-env/bin/python" "$root/probe_local_api.py" \
  --model Qwen3.8-27B-pinned --output "$run/api" > client.log 2>&1
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv > gpu_after.csv
printf 'Deployment probe finished; scientific workflow NOT RUN\n'

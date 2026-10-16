#!/bin/bash
# One pinned model and one native review panel; no retry or source repair.
set -euo pipefail
umask 077
root="${1:?Supply the frozen assessment root}"
model_root="${2:?Supply the verified Flash-Next model root}"
runtime_root="${3:?Supply the existing pinned serving runtime root}"
manifest_sha="${4:?Supply the frozen file-manifest SHA-256}"
module load Python/3.12.3-GCCcore-13.3.0 CUDA/12.9.1
cd "$root"
printf '%s  %s\n' "$manifest_sha" frozen_files.sha256 | sha256sum --check
sha256sum --check frozen_files.sha256 > /dev/null
test -s "$model_root/verified-model-files.json"
test ! -e observation
printf '%s  %s\n' d322861877b4504d931ea7ec4a3175c1108437e85f65189783dd61712e8309a3 \
  "$runtime_root/serve-env-node-local.tar" | sha256sum --check
printf '%s  %s\n' 5752b5f1e842bd89d5370a42cd4b4df123fb276c348dbdd72553c85d6342eaa6 \
  "$root/worker-env.tar" | sha256sum --check
local_root=$(mktemp -d "/tmp/ai-stat-review-$SLURM_JOB_ID-XXXXXX")
server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; fi
  rm -rf -- "$local_root"
}
trap cleanup EXIT
trap 'exit 143' TERM INT
tar -xf "$runtime_root/serve-env-node-local.tar" -C "$local_root"
tar -xf "$root/worker-env.tar" -C "$local_root"
serving_python="$local_root/serve-env/bin/python"
worker_python="$local_root/worker-env/bin/python"
export PATH="$local_root/serve-env/bin:$PATH" PYTHONPATH="$root/code"
export TMPDIR=/tmp HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export VLLM_CACHE_ROOT="$local_root/vllm-cache" FLASHINFER_WORKSPACE_BASE="$local_root/flashinfer"
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export AI_STATISTICIAN_LOCAL_BASE_URL=http://127.0.0.1:8081/v1
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN OPENAI_API_KEY OPENROUTER_API_KEY
"$worker_python" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",8081)); s.close()'
mkdir "deployment-$SLURM_JOB_ID"
deployment="$root/deployment-$SLURM_JOB_ID"
nvidia-smi --query-gpu=name,uuid,driver_version,memory.total --format=csv > "$deployment/gpu.csv"
module list > "$deployment/modules.txt" 2>&1
nvcc --version > "$deployment/nvcc.txt"
args=(serve "$model_root/model" --served-model-name Qwen3.8-Flash-Next-BF16-native-pinned
  --host 127.0.0.1 --port 8081 --dtype bfloat16 --kv-cache-dtype auto
  --tensor-parallel-size 4 --enable-expert-parallel --distributed-executor-backend mp
  --max-model-len 262144 --max-num-seqs 256 --language-model-only
  --gpu-memory-utilization 0.9 --seed 20261016 --enable-prefix-caching
  --engram-config '{"cpu_offload":true}'
  --speculative-config '{"method":"mtp","num_speculative_tokens":3}'
  --generation-config "$model_root/model"
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder)
printf '%q ' "$serving_python" -m vllm.entrypoints.cli.main "${args[@]}" > "$deployment/serve_command.txt"
printf '\n' >> "$deployment/serve_command.txt"
"$serving_python" -m vllm.entrypoints.cli.main "${args[@]}" > "$deployment/server.log" 2>&1 &
server_pid=$!
deadline=$((SECONDS + 3600))
until curl --noproxy '*' --silent --fail --max-time 5 http://127.0.0.1:8081/health > /dev/null; do
  kill -0 "$server_pid" || { wait "$server_pid"; exit 1; }
  if (( SECONDS >= deadline )); then printf 'Server readiness timed out\n' >&2; exit 1; fi
  sleep 5
done
curl --noproxy '*' --silent --fail http://127.0.0.1:8081/v1/models > "$deployment/models.json"
"$worker_python" -c 'import json,sys; data=json.load(open(sys.argv[1]))["data"]; assert len(data)==1 and data[0]["id"]=="Qwen3.8-Flash-Next-BF16-native-pinned" and data[0]["max_model_len"]==262144' "$deployment/models.json"
"$worker_python" code/integrations/agentic-scientist/bouchet/probe_local_api.py \
  --model Qwen3.8-Flash-Next-BF16-native-pinned --output "$deployment/transport" > "$deployment/transport.log" 2>&1
"$worker_python" -m benchmarks.publication_assessment_flashnext_20261016.qualify --plan condition.json

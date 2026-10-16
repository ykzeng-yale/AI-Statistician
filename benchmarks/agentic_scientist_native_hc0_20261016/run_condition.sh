#!/bin/bash
# One model service and the existing upstream pipeline for each independent arm.
set -euo pipefail
umask 077
run_root="${1:?Supply the frozen condition root}"
model_root="${2:?Supply the pinned deployment root}"
product_root="${3:?Supply the frozen product checkout}"
worker_sha="${4:?Supply the worker archive hash}"
serving_sha="${5:?Supply the serving archive hash}"
probe_id="${6:?Supply the successful deployment probe job ID}"
module load Python/3.12.3-GCCcore-13.3.0 CUDA/12.9.1
test -s "$model_root/probe-$probe_id/api/success.json"
test -s "$run_root/api_config.json"
cd "$run_root"
sha256sum --check frozen_files.sha256
printf '%s  %s\n' "$worker_sha" "$run_root/worker-env.tar" | sha256sum --check
printf '%s  %s\n' "$serving_sha" "$model_root/serve-env-node-local.tar" | sha256sum --check
observations="$run_root/job-$SLURM_JOB_ID"
mkdir "$observations"
local_root=$(mktemp -d "/tmp/ai-stat-research-$SLURM_JOB_ID-XXXXXX")
server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; fi
  rm -rf -- "$local_root"
}
trap cleanup EXIT
trap 'exit 143' TERM INT
tar -xf "$run_root/worker-env.tar" -C "$local_root"
tar -xf "$model_root/serve-env-node-local.tar" -C "$local_root"
worker_python="$local_root/worker-env/bin/python"
serving_python="$local_root/serve-env/bin/python"
export PATH="$local_root/serve-env/bin:$PATH"
export PYTHONPATH="$run_root/upstream:$product_root"
export TMPDIR=/tmp AGENTIC_TEMP_ROOT=/tmp
export VLLM_CACHE_ROOT="$local_root/vllm-cache" FLASHINFER_WORKSPACE_BASE="$local_root/flashinfer"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=1
export WRAPPER_PYTHON="$worker_python"
export AI_STATISTICIAN_API_PYTHON="$worker_python"
export AI_STATISTICIAN_API_ENTRYPOINT="$product_root/scripts/run_agentic_api.py"
export AI_STATISTICIAN_API_CONFIG="$run_root/api_config.json"
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN OPENAI_API_KEY OPENROUTER_API_KEY
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN
nvidia-smi --query-gpu=name,uuid,driver_version,memory.total --format=csv > "$observations/gpu.csv"
nvcc --version > "$observations/nvcc.txt"
ninja --version > "$observations/ninja.txt"
args=(serve "$model_root/model" --served-model-name Qwen3.8-27B-pinned
  --host 127.0.0.1 --port 8081 --dtype bfloat16 --kv-cache-dtype auto
  --max-model-len 262144 --max-num-seqs 1 --max-num-batched-tokens 8192
  --language-model-only --gpu-memory-utilization 0.9 --seed 20261015
  --generation-config "$model_root/model"
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder)
printf '%q ' "$serving_python" -m vllm.entrypoints.cli.main "${args[@]}" > "$observations/serve_command.txt"
printf '\n' >> "$observations/serve_command.txt"
"$serving_python" -m vllm.entrypoints.cli.main "${args[@]}" > "$observations/server.log" 2>&1 &
server_pid=$!
deadline=$((SECONDS + 1800))
until curl --noproxy '*' --silent --fail --max-time 5 http://127.0.0.1:8081/health > /dev/null; do
  kill -0 "$server_pid" || { wait "$server_pid"; exit 1; }
  if (( SECONDS >= deadline )); then printf 'Server readiness timed out\n' >&2; exit 1; fi
  sleep 5
done
curl --noproxy '*' --silent --fail http://127.0.0.1:8081/v1/models > "$observations/models.json"
cd "$run_root/upstream"
overall_status=0
for arm in stock statistical; do
  test ! -e "$run_root/$arm/results"
  extra_args=()
  if [[ "$arm" == statistical ]]; then
    extra_args+=("investigation.paths.instruct=$run_root/$arm/investigate.md")
  fi
  arm_status=0
  OMP_NUM_THREADS=1 "$worker_python" -m src.pipeline.cli \
    "task.dir=$run_root/$arm/task" "paths.run_dir=$run_root/$arm/results" \
    "run_id=native_hc0_20261016_$arm" execution.phases=investigation,posthoc \
    agent.name=local-api agent.model=Qwen3.8-27B-pinned \
    container.enabled=false versioning.enabled=false \
    investigation.execution.harness_evaluated_attempts=true \
    investigation.execution.max_idea_cycles=3 \
    investigation.execution.max_idea_generation_attempts=1 \
    investigation.execution.workers=1 \
    investigation.execution.run_timeout_seconds=14400 \
    investigation.execution.idea_timeout_seconds=3600 \
    investigation.execution.harness_evaluation_timeout_seconds=1800 \
    posthoc.execution.analysis_timeout_seconds=3600 \
    posthoc.execution.max_attempts_per_analysis=3 "${extra_args[@]}" \
    > "$observations/$arm.log" 2>&1 || arm_status=$?
  printf '%s\n' "$arm_status" > "$observations/${arm}_outer_exit_code.txt"
  if (( arm_status != 0 )); then overall_status=1; fi
done
exit "$overall_status"

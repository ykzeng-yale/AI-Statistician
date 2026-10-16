#!/bin/bash
# One complete-method development draw on the existing native controller.
set -euo pipefail
umask 077
root="${1:?Supply the frozen run root}"
freeze_sha="${2:?Supply the input-manifest SHA-256}"
weights=/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-Qwen38-FlashNext-20261016
runtime=/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-Qwen38-27B-20261015
worker_archive="$weights/assessment-native-20261016/worker-env.tar"
r_environment=/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-DRDID-source-20261016
module load Python/3.12.3-GCCcore-13.3.0 CUDA/12.9.1 R/4.4.2-gfbf-2024a
cd "$root"
printf '%s  %s\n' "$freeze_sha" frozen_files.sha256 | sha256sum --check
sha256sum --check frozen_files.sha256 > /dev/null
printf '%s  %s\n' d322861877b4504d931ea7ec4a3175c1108437e85f65189783dd61712e8309a3 \
  "$runtime/serve-env-node-local.tar" | sha256sum --check
printf '%s  %s\n' 5752b5f1e842bd89d5370a42cd4b4df123fb276c348dbdd72553c85d6342eaa6 \
  "$worker_archive" | sha256sum --check
test ! -e results
observations="$root/job-$SLURM_JOB_ID"
mkdir "$observations"
local_root=$(mktemp -d "/tmp/ai-stat-drdid-$SLURM_JOB_ID-XXXXXX")
server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; fi
  rm -rf -- "$local_root"
}
trap cleanup EXIT
trap 'exit 143' TERM INT
tar -xf "$runtime/serve-env-node-local.tar" -C "$local_root"
tar -xf "$worker_archive" -C "$local_root"
serving_python="$local_root/serve-env/bin/python"
worker_python="$local_root/worker-env/bin/python"
export PATH="$local_root/serve-env/bin:$PATH" PYTHONPATH="$root/upstream:$root/code"
export TMPDIR=/tmp AGENTIC_TEMP_ROOT=/tmp
export VLLM_CACHE_ROOT="$local_root/vllm-cache" FLASHINFER_WORKSPACE_BASE="$local_root/flashinfer"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export R_LIBS_USER="$r_environment/library"
export WRAPPER_PYTHON="$worker_python" AI_STATISTICIAN_API_PYTHON="$worker_python"
export AI_STATISTICIAN_API_ENTRYPOINT="$root/code/scripts/run_agentic_api.py"
export AI_STATISTICIAN_API_CONFIG="$root/api_config.json"
export AI_STATISTICIAN_LOCAL_BASE_URL=http://127.0.0.1:8081/v1
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN OPENAI_API_KEY OPENROUTER_API_KEY HF_TOKEN HUGGING_FACE_HUB_TOKEN
"$worker_python" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",8081)); s.close()'
"$worker_python" - "$weights" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
raw = (root / "verified-model-files.json").read_bytes()
assert hashlib.sha256(raw).hexdigest() == "383ebbfc1af8275e945a4a44403f13c9701bb14436e12ff310ef03250acc669f"
receipt = json.loads(raw)
assert receipt["repo"] == "Qwen/Qwen3.8-Flash-Next" and receipt["revision"] == "de4b8e4d43b917e7706784d8bb445c9af86a3540"
assert len(receipt["files"]) == 144
for name, identity in receipt["files"].items():
    path = root / "model" / name
    assert path.stat().st_size == identity["bytes"], name
    with path.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == identity["sha256"], name
print("All 144 pinned model files verified", flush=True)
PY
Rscript --vanilla -e 'stopifnot(packageVersion("DRDID") == package_version("1.3.0")); print(sessionInfo())' \
  > "$observations/r_environment.txt" 2>&1
nvidia-smi --query-gpu=name,uuid,driver_version,memory.total --format=csv > "$observations/gpu.csv"
module list > "$observations/modules.txt" 2>&1
args=(serve "$weights/model" --served-model-name Qwen3.8-Flash-Next-BF16-yarn1m-pinned
  --host 127.0.0.1 --port 8081 --dtype bfloat16 --kv-cache-dtype auto
  --tensor-parallel-size 4 --enable-expert-parallel --distributed-executor-backend mp
  --max-model-len 1000000 --max-num-seqs 1 --max-num-batched-tokens 8192 --language-model-only
  --hf-overrides '{"text_config":{"rope_parameters":{"mrope_interleaved":true,"mrope_section":[11,11,10],"rope_type":"yarn","rope_theta":10000000,"partial_rotary_factor":0.25,"factor":4.0,"original_max_position_embeddings":262144}}}'
  --gpu-memory-utilization 0.9 --seed 20261016 --enable-prefix-caching
  --engram-config '{"cpu_offload":true}' --speculative-config '{"method":"mtp","num_speculative_tokens":3}'
  --generation-config "$weights/model" --reasoning-parser qwen3
  --enable-auto-tool-choice --tool-call-parser qwen3_coder)
printf '%q ' "$serving_python" -m vllm.entrypoints.cli.main "${args[@]}" > "$observations/serve_command.txt"
printf '\n' >> "$observations/serve_command.txt"
OMP_NUM_THREADS=8 "$serving_python" -m vllm.entrypoints.cli.main "${args[@]}" > "$observations/server.log" 2>&1 &
server_pid=$!
deadline=$((SECONDS + 3600))
until curl --noproxy '*' --silent --fail --max-time 5 http://127.0.0.1:8081/health > /dev/null; do
  kill -0 "$server_pid" || { wait "$server_pid"; exit 1; }
  if (( SECONDS >= deadline )); then printf 'Server readiness timed out\n' >&2; exit 1; fi
  sleep 5
done
curl --noproxy '*' --silent --fail http://127.0.0.1:8081/v1/models > "$observations/models.json"
"$worker_python" -c 'import json,sys; data=json.load(open(sys.argv[1]))["data"]; assert len(data)==1 and data[0]["id"]=="Qwen3.8-Flash-Next-BF16-yarn1m-pinned" and data[0]["max_model_len"]==1000000' "$observations/models.json"
status=0
"$worker_python" -m src.pipeline.cli \
  "task.dir=$root/task" "paths.run_dir=$root/results" run_id=drdid_full_method_20261016 \
  execution.phases=investigation,posthoc agent.name=local-api agent.model=Qwen3.8-Flash-Next-BF16-yarn1m-pinned \
  container.enabled=false versioning.enabled=false \
  investigation.execution.harness_evaluated_attempts=false \
  investigation.execution.max_idea_cycles=1 investigation.execution.max_idea_generation_attempts=1 \
  investigation.execution.workers=1 investigation.execution.max_program_evals_per_attempt=4 \
  investigation.execution.idea_timeout_seconds=14400 investigation.execution.run_timeout_seconds=129600 \
  investigation.execution.harness_evaluation_timeout_seconds=43200 \
  posthoc.execution.analysis_timeout_seconds=14400 posthoc.execution.max_attempts_per_analysis=1 \
  > "$observations/pipeline.log" 2>&1 || status=$?
printf '%s\n' "$status" > "$observations/pipeline_exit_code.txt"
exit "$status"

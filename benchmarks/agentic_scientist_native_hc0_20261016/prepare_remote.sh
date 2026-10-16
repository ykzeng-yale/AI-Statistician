#!/bin/bash
# Prepare one hash-locked CPU environment before any model call.
set -euo pipefail
umask 077
run_root="${1:?Supply the new condition root}"
uv_bin="${2:?Supply the existing uv executable}"
module load Python/3.12.3-GCCcore-13.3.0
test ! -e "$run_root/worker-env"
"$uv_bin" export --project "$run_root/upstream" --frozen --no-dev --no-emit-project \
  --format requirements-txt --output-file "$run_root/upstream_requirements.txt"
"$uv_bin" pip compile --python-version 3.12 --generate-hashes \
  "$run_root/requirements.in" --output-file "$run_root/worker_requirements.txt"
"$uv_bin" venv --python "$(command -v python)" "$run_root/worker-env"
"$uv_bin" pip sync --require-hashes --python "$run_root/worker-env/bin/python" "$run_root/worker_requirements.txt"
"$uv_bin" pip check --python "$run_root/worker-env/bin/python"
"$uv_bin" pip freeze --python "$run_root/worker-env/bin/python" > "$run_root/worker_environment.txt"
tar -cf "$run_root/worker-env.tar" -C "$run_root" worker-env
sha256sum "$run_root/worker-env.tar" "$run_root/worker_requirements.txt" "$run_root/worker_environment.txt"

#!/bin/bash
# Task-owned weight staging only; no serving, inference or upstream changes.
set -euo pipefail
umask 077
root="${1:?Supply a new task-owned Bouchet storage directory}"
download_env="${2:?Supply the existing pinned Hugging Face client environment}"
python="$download_env/bin/python"
module load Python/3.12.3-GCCcore-13.3.0
test -d "$root"
test ! -e "$root/verified-model-files.json"
mkdir "$root/staging-$SLURM_JOB_ID"
cd "$root"
export TMPDIR=/tmp UV_CACHE_DIR="$root/uv-cache" HF_HOME="$root/hf-home"
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_TELEMETRY=1
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN ANTHROPIC_API_KEY OPENAI_API_KEY
printf 'job=%s host=%s started=%s\n' "$SLURM_JOB_ID" "$(hostname)" "$(date -Is)"
"$python" --version
"$python" -c 'import json; from importlib.metadata import distributions,version; assert version("huggingface_hub") == "1.31.0"; print(json.dumps(sorted((d.metadata["Name"], d.version) for d in distributions()), indent=2))' > "staging-$SLURM_JOB_ID/environment.json"
# The upstream downloader resumes incomplete files; serialize large shard fetches.
"$download_env/bin/hf" download Qwen/Qwen3.8-Flash-Next \
  --revision de4b8e4d43b917e7706784d8bb445c9af86a3540 --local-dir "$root/model" --max-workers 1
"$python" - "$root" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
metadata = json.loads((root / "model_metadata.json").read_text())
assert metadata["id"] == "Qwen/Qwen3.8-Flash-Next"
assert metadata["sha"] == "de4b8e4d43b917e7706784d8bb445c9af86a3540"
verified = {}
for item in metadata["siblings"]:
    path = root / "model" / item["rfilename"]
    assert path.stat().st_size == item["size"], item["rfilename"]
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if item.get("lfs"):
        assert digest == item["lfs"]["sha256"], item["rfilename"]
    verified[item["rfilename"]] = {"bytes": path.stat().st_size, "sha256": digest}
with (root / "verified-model-files.json").open("x") as stream:
    json.dump({"repo": metadata["id"], "revision": metadata["sha"],
               "files": verified, "scope": "Weights staged; runtime and inference unverified"},
              stream, indent=2)
    stream.write("\n")
print(f"Verified {len(verified)} files; no model inference")
PY
du -sh "$root"

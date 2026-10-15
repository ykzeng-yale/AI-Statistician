#!/bin/bash
# Task-owned weight staging only; no serving, inference or upstream changes.
set -euo pipefail
umask 077
root="${1:?Supply a new task-owned Bouchet storage directory}"
uv="${2:?Supply the existing uv executable}"
module load Python/3.12.3-GCCcore-13.3.0
test -d "$root"
test ! -e "$root/verified-model-files.json"
mkdir "$root/staging-$SLURM_JOB_ID"
cd "$root"
export TMPDIR=/tmp UV_CACHE_DIR="$root/uv-cache" HF_HOME="$root/hf-home"
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_TELEMETRY=1
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN ANTHROPIC_API_KEY OPENAI_API_KEY
printf 'job=%s host=%s started=%s\n' "$SLURM_JOB_ID" "$(hostname)" "$(date -Is)"
python --version
"$uv" --version
if [ ! -x "$root/download-env/bin/hf" ]; then
  "$uv" venv --python "$(command -v python)" "$root/download-env"
  "$uv" pip install --python "$root/download-env/bin/python" huggingface_hub==1.31.0
fi
"$root/download-env/bin/python" -c 'from importlib.metadata import version; assert version("huggingface_hub") == "1.31.0"'
"$uv" pip freeze --python "$root/download-env/bin/python" > "staging-$SLURM_JOB_ID/environment.txt"
# The upstream downloader resumes incomplete files; serialize large shard fetches.
"$root/download-env/bin/hf" download Qwen/Qwen3.8-27B \
  --revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0 --local-dir "$root/model" --max-workers 1
"$root/download-env/bin/python" - "$root" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
metadata = json.loads((root / "model_metadata.json").read_text())
assert metadata["id"] == "Qwen/Qwen3.8-27B"
assert metadata["sha"] == "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"
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

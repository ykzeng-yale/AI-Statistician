"""Native source-only investigation participant for the pinned upstream patch."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_statistician.agentic_api_workspace import FileAuthorWorkspace, FileGrant, run_file_author
from ai_statistician.local_model_backend import LocalChatGeneratorBackend


def load_config(path: Path, *, model: str) -> tuple[dict, dict]:
    config = json.loads(path.read_text())
    required = {"model", "base_url", "max_tokens", "temperature", "timeout_seconds",
                "max_turns", "deployment_ref"}
    if not isinstance(config, dict) or set(config) != required:
        raise ValueError("Supply exactly the documented native API configuration fields.")
    if config["model"] != model:
        raise ValueError("Stage model differs from the frozen API model; no substitution allowed.")
    for key in ("max_tokens", "max_turns", "timeout_seconds"):
        if type(config[key]) is not int or config[key] < 1:
            raise ValueError(f"{key} must be a positive integer.")
    if type(config["temperature"]) not in (int, float) or not math.isfinite(config["temperature"]) or config["temperature"] < 0:
        raise ValueError("temperature must be finite and nonnegative.")
    ref = config["deployment_ref"]
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        raise ValueError("deployment_ref requires path and sha256.")
    receipt_path = Path(ref["path"]).expanduser().resolve(strict=True)
    receipt = receipt_path.read_bytes()
    if hashlib.sha256(receipt).hexdigest() != ref["sha256"]:
        raise ValueError("Deployment receipt hash mismatch.")
    return config, {"config": config, "deployment_ref": {**ref, "path": str(receipt_path)},
                    "scope": "Operator-declared pinned deployment; response model identity checked on every request."}


def stage_workspace(root: Path, source: Path) -> FileAuthorWorkspace:
    root, source = root.resolve(), source.resolve()
    grants = [
        FileGrant(name, root / name) for name in
        ("task.md", "active_idea.json", "active_rubrics.json") if (root / name).is_file()
    ]
    grants.extend((
        FileGrant("program_0", root / "program_0", directory=True),
        FileGrant("skills", root / ".local-api/skills", directory=True),
        FileGrant("sources", source / "resources/search", directory=True),
        FileGrant("program_1/src", root / "program_1/src", directory=True, writable=True),
        FileGrant("program_1/program_spec.toml", root / "program_1/program_spec.toml", writable=True),
        FileGrant("memory.md", root / "memory.md", writable=True),
    ))
    workspace = FileAuthorWorkspace(tuple(grants))
    specification = tomllib.loads(workspace._path("program_0/program_spec.toml").read_text())
    if specification.get("schema_version") != 1 or specification["code_root"] != "src":
        raise ValueError("The pinned upstream schema_version=1 requires code_root='src'.")
    return workspace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    config, identity = load_config(Path(os.environ["AI_STATISTICIAN_API_CONFIG"]), model=args.model)
    root = Path.cwd().resolve()
    workspace = stage_workspace(root, Path(os.environ["TASK_SOURCE_DIR"]).resolve())
    backend = LocalChatGeneratorBackend(base_url=config["base_url"], timeout_s=config["timeout_seconds"])
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"Received signal {signum}")

    previous_handler = signal.signal(signal.SIGTERM, interrupted)
    try:
        result = run_file_author(
            backend=backend, workspace=workspace, prompt=args.prompt_file.read_text(),
            model=args.model, max_tokens=config["max_tokens"], temperature=config["temperature"],
            max_turns=config["max_turns"], session_dir=root / ".local-api/session",
            session_id=os.environ["ATTEMPT_ID"], deployment_identity=identity,
        )
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
    print(json.dumps({"event": "api_author_terminal", "provider": result.provider,
        "model": result.model, "provider_usage": dict(result.provider_usage),
        "disposition": result.terminal_payload["disposition"], "scientific_acceptance": False}), flush=True)
    return 0 if result.terminal_payload["disposition"] == "candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""One frozen setup observation through the existing local transport, not a draw."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.request

from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.model_backend import ClientToolDefinition, ClientToolTurnRequest


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=False)
    observation = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "plan_sha256": digest(args.plan),
        "scope": plan["scope"],
        "model_call_attempts": 0,
        "status": "pre_call_checks",
        "checks": {},
    }
    started = time.monotonic()
    try:
        files = {
            "weights": (Path(plan["download"]["verified_path"]).resolve(), plan["weights_sha256"]),
            "server": (Path(plan["server_binary"]), plan["server_sha256"]),
            **{name: (Path(plan["library_directory"]) / name, expected)
               for name, expected in plan["library_sha256"].items()},
        }
        for name, (path, expected) in files.items():
            actual = digest(path)
            observation["checks"][name] = {"path": str(path), "sha256": actual}
            if actual != expected:
                raise ValueError(f"{name} hash mismatch")

        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for endpoint, filename in (("/props", "props.json"), ("/v1/models", "models.json")):
            with opener.open("http://127.0.0.1:8081" + endpoint, timeout=10) as reply:
                value = json.load(reply)
            write_json(args.output / filename, value)
        props = json.loads((args.output / "props.json").read_text(encoding="utf-8"))
        models = json.loads((args.output / "models.json").read_text(encoding="utf-8"))
        settings = props["default_generation_settings"]
        params = settings["params"]
        actual = {
            "context_tokens": settings["n_ctx"], "slots": props["total_slots"],
            "alias": props["model_alias"], "model_path": props["model_path"],
            "chat_template_sha256": hashlib.sha256(props["chat_template"].encode("utf-8")).hexdigest(),
            "seed": params["seed"], "temperature": params["temperature"],
            "top_k": params["top_k"], "top_p": params["top_p"], "min_p": params["min_p"],
            "model_ids": [item["id"] for item in models["data"]],
        }
        observation["active_settings"] = actual
        expected = {
            "context_tokens": 131072, "slots": 1, "alias": plan["model"],
            "model_path": str(files["weights"][0]),
            "chat_template_sha256": plan["expected_chat_template_sha256"],
            "seed": 20261003, "temperature": 0.7, "top_k": 20, "top_p": 0.8, "min_p": 0.0,
            "model_ids": [plan["model"]],
        }
        for key, value in expected.items():
            matches = (abs(actual[key] - value) < 1e-6
                       if isinstance(value, float) else actual[key] == value)
            if not matches:
                raise ValueError(f"active {key} mismatch: {actual[key]!r} != {value!r}")

        spec = plan["request"]
        request = ClientToolTurnRequest(
            system_prompt=spec["system_prompt"],
            messages=({"role": "user", "content": spec["user_prompt"]},),
            tools=(ClientToolDefinition(**spec["tool"]),),
            model=plan["model"], max_tokens=spec["max_tokens"],
            temperature=spec["temperature"], tool_choice=spec["tool_choice"],
            disable_parallel_tool_use=not spec["parallel_tool_calls"],
            thinking_budget_tokens=0,
        )
        write_json(args.output / "request.json", asdict(request))
        backend = LocalChatGeneratorBackend(
            base_url="http://127.0.0.1:8081/v1", timeout_s=plan["request_timeout_seconds"],
        )
        observation["model_call_attempts"] = 1
        response = backend.generate_client_tool_turn(request)
        write_json(args.output / "response.json", asdict(response))
        calls = response.tool_calls
        observation["native_tool_marker_match"] = (
            len(calls) == 1 and calls[0].name == "record_environment_receipt"
            and dict(calls[0].input) == {"marker": "deployment-check-20261003"}
        )
        observation["status"] = (
            "setup_observed" if observation["native_tool_marker_match"] else "tool_marker_mismatch"
        )
    except Exception as exc:
        observation["status"] = "failed"
        observation["error"] = {"type": type(exc).__name__, "message": str(exc)}
    observation["finished_at"] = datetime.now(timezone.utc).isoformat()
    observation["elapsed_seconds"] = time.monotonic() - started
    observation["limitations"] = plan["limitations"]
    write_json(args.output / "observation.json", observation)
    print(json.dumps({key: observation[key] for key in ("status", "model_call_attempts", "elapsed_seconds")}))
    return 0 if observation["status"] == "setup_observed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

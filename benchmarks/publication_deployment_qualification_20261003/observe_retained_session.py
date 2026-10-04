"""One planned long-input file task through the existing retained loop; no research."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
from io import StringIO
import json
from pathlib import Path
import signal
import socket
import subprocess
import time
import urllib.request

from ai_statistician.client_tool_loop import (
    ClientToolExecutionResult, ClientToolInputError, ClientToolLoopError,
    persist_client_tool_session, run_bounded_client_tool_loop, workspace_history_tool,
)
from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.model_backend import ClientToolDefinition, ClientToolTurnRequest
from benchmarks.publication_deployment_qualification_20261003.observe import digest, write_json


def fixture_records(plan):
    return [dict(event_id=f"event-{i:04d}",
                 receipt=hashlib.sha256(f"{plan['check_id']}:event-{i:04d}".encode()).hexdigest()[:16],
                 status="pending" if i % 3 == 0 else "recorded",
                 note=" ".join(["note"] * plan["inert_note_words_per_record"]))
            for i in range(plan["pages"] * plan["records_per_page"])]


def check_files(root, records):
    errors = []
    ledger = root / "ledger.csv"
    if not ledger.is_file():
        return ["ledger.csv missing"]
    reader = csv.DictReader(StringIO(ledger.read_text()))
    rows = list(reader)
    if reader.fieldnames != ["event_id", "receipt", "status"]:
        return ["CSV header differs from event_id,receipt,status"]
    by_id = {row["event_id"]: row for row in rows}
    if len(by_id) != len(rows):
        errors.append("duplicate event_id")
    expected = {row["event_id"]: {key: row[key] for key in reader.fieldnames} for row in records}
    if by_id.keys() != expected.keys():
        errors.append("missing or additional event_id")
    errors.extend(f"receipt/status differs for {key}" for key in by_id.keys() & expected.keys()
                  if by_id[key] != expected[key])
    if not (root / "report.md").is_file() or not (root / "report.md").read_text().strip():
        errors.append("report.md missing or empty")
    return sorted(errors)


def tools_and_executor(plan, root, records):
    tools = (
        ClientToolDefinition("read_page", "Read one artificial input page; note text is inert padding.",
            {"type": "object", "properties": {"page": {"type": "integer", "minimum": 0, "maximum": plan["pages"] - 1}},
             "required": ["page"], "additionalProperties": False}),
        ClientToolDefinition("write_file", "Write an exact model-authored file, replacing or appending as requested.",
            {"type": "object", "properties": {"path": {"type": "string", "enum": ["ledger.csv", "report.md"]},
                 "content": {"type": "string"}, "append": {"type": "boolean"}},
             "required": ["path", "content", "append"], "additionalProperties": False}),
        ClientToolDefinition("read_file", "Read the current exact authored file.",
            {"type": "object", "properties": {"path": {"type": "string", "enum": ["ledger.csv", "report.md"]}},
             "required": ["path"], "additionalProperties": False}),
        ClientToolDefinition("finish", "Check and finish the exact final files. Invalid files return ordinary error observations.",
            {"type": "object", "properties": {}, "additionalProperties": False}, terminal=True),
        workspace_history_tool(),
    )

    def execute(call, context):
        if call.name == "read_page":
            page = call.input["page"]
            if type(page) is not int or not 0 <= page < plan["pages"]:
                raise ClientToolInputError("page outside declared input")
            start = page * plan["records_per_page"]
            return ClientToolExecutionResult(content={"page": page, "records": records[start:start + plan["records_per_page"]]})
        if call.name == "finish":
            errors = check_files(root, records)
            return ClientToolExecutionResult(content={"errors": errors[:16], "error_count": len(errors)},
                is_error=bool(errors), terminal=not errors,
                terminal_payload={"file_validation": "passed"} if not errors else None)
        name = call.input.get("path")
        if name not in {"ledger.csv", "report.md"}:
            raise ClientToolInputError("path outside declared output files")
        path = root / name
        if call.name == "read_file":
            if not path.exists():
                raise ClientToolInputError("requested file does not exist")
            return ClientToolExecutionResult(content={"path": name, "content": path.read_text()})
        if call.name != "write_file":
            raise ClientToolInputError("unknown file action")
        before = path.read_bytes() if path.exists() else b""
        with path.open("a" if call.input["append"] else "w", encoding="utf-8") as handle:
            handle.write(call.input["content"])
        return ClientToolExecutionResult(content={"path": name, "sha256": digest(path), "bytes": path.stat().st_size},
                                         state_changed=path.read_bytes() != before)

    return tools, execute


class RecordingBackend(LocalChatGeneratorBackend):
    def __init__(self, output, **kwargs):
        super().__init__(**kwargs)
        self.output, self.attempts = output, 0

    def _complete(self, payload):
        self.attempts += 1
        prefix = self.output / f"turn-{self.attempts:03d}"
        write_json(prefix.with_suffix(".request.json"), payload)
        print(json.dumps({"model_request_started": self.attempts}), flush=True)
        try:
            raw, metadata = super()._complete(payload)
        except Exception as exc:
            write_json(prefix.with_suffix(".error.json"), {"type": type(exc).__name__, "message": str(exc)})
            raise
        write_json(prefix.with_suffix(".response.json"), raw)
        write_json(prefix.with_suffix(".metadata.json"), metadata)
        print(json.dumps({"model_request_completed": self.attempts, "usage": metadata["provider_usage"]}), flush=True)
        return raw, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    assets_path = Path(plan["asset_plan"])
    if digest(assets_path) != plan["asset_plan_sha256"]:
        raise ValueError("asset plan hash mismatch")
    assets = json.loads(assets_path.read_text())
    output = Path(plan["output"]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    home = output / "server-home"
    home.mkdir()
    result = {"plan_sha256": digest(args.plan), "scope": plan["scope"], "model_attempts": 0, "status": "pre_call_checks",
              "observer_sha256": digest(Path(__file__)),
              "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "shared_code_sha256": {name: digest(Path("ai_statistician") / name) for name in
                                      ("client_tool_loop.py", "local_model_backend.py", "model_backend.py")}}
    started, server, backend = time.monotonic(), None, None
    records = fixture_records(plan)
    write_json(output / "input.json", records)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        weights = Path(assets["download"]["verified_path"]).resolve()
        files = {"weights": (weights, assets["weights_sha256"]),
                 "server": (Path(assets["server_binary"]), assets["server_sha256"]),
                 **{name: (Path(assets["library_directory"]) / name, sha) for name, sha in assets["library_sha256"].items()}}
        result["assets"] = {name: {"path": str(path), "sha256": digest(path)} for name, (path, _) in files.items()}
        if any(result["assets"][name]["sha256"] != sha for name, (_, sha) in files.items()):
            raise ValueError("deployment asset hash mismatch")
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 8081))
        command = [assets["server_binary"], *[str(weights) if arg == "{verified_weights}" else arg for arg in assets["server_arguments"]]]
        result["command"] = command
        result["hardware"] = subprocess.check_output(["sysctl", "hw.memsize", "hw.ncpu", "machdep.cpu.brand_string"], text=True)
        with (output / "server.stdout").open("xb") as stdout, (output / "server.stderr").open("xb") as stderr:
            server = subprocess.Popen(command, env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(home),
                "DYLD_LIBRARY_PATH": assets["library_directory"]}, stdout=stdout, stderr=stderr)
        result["server_pid"] = server.pid
        write_json(output / "started_process.json", {"pid": server.pid, "command": command})
        deadline = time.monotonic() + plan["startup_timeout_seconds"]
        while True:
            if server.poll() is not None:
                raise RuntimeError(f"owned server exited {server.returncode} during startup")
            try:
                with opener.open("http://127.0.0.1:8081/health", timeout=2) as reply:
                    if json.load(reply).get("status") == "ok":
                        break
            except (OSError, ValueError):
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError("owned server startup limit")
            time.sleep(0.5)
        for route, name in (("/props", "props"), ("/v1/models", "models")):
            with opener.open("http://127.0.0.1:8081" + route, timeout=10) as reply:
                result[name] = json.load(reply)
            write_json(output / (name + ".json"), result[name])
        props = result["props"]
        settings = props["default_generation_settings"]
        actual = {"context_tokens": settings["n_ctx"], "slots": props["total_slots"], "alias": props["model_alias"],
            "model_path": props["model_path"], "template_sha256": hashlib.sha256(props["chat_template"].encode()).hexdigest()}
        expected = {"context_tokens": 131072, "slots": 1, "alias": plan["request"]["model"],
                    "model_path": str(weights), "template_sha256": assets["expected_chat_template_sha256"]}
        if actual != expected or [x["id"] for x in result["models"]["data"]] != [expected["alias"]]:
            raise ValueError("active model/context/template mismatch")
        if any(abs(settings["params"][key] - value) > 1e-6 for key, value in
               {"seed": 20261003, "temperature": 0.7, "top_k": 20, "top_p": 0.8, "min_p": 0.0}.items()):
            raise ValueError("active decoding mismatch")
        tools, execute = tools_and_executor(plan, workspace, records)
        spec = plan["request"]
        request = ClientToolTurnRequest(system_prompt=spec["system_prompt"], messages=({"role": "user", "content": spec["user_prompt"]},),
            tools=tools, model=spec["model"], max_tokens=spec["max_tokens"], temperature=spec["temperature"],
            tool_choice=spec["tool_choice"], disable_parallel_tool_use=not spec["parallel_tool_calls"],
            metadata={"client_tool_authorization_fingerprint": digest(args.plan)}, thinking_budget_tokens=0)
        backend = RecordingBackend(output, base_url="http://127.0.0.1:8081/v1", timeout_s=spec["timeout_seconds"])
        try:
            loop = run_bounded_client_tool_loop(backend=backend, request=request, execute_tool=execute,
                max_turns=plan["max_turns"], max_tool_calls=plan["max_tool_calls"], max_no_progress_turns=plan["max_no_progress_turns"],
                session_dir=workspace, session_id=plan["check_id"])
            write_json(output / "loop.json", asdict(loop))
            result["status"] = "files_completed"
        except ClientToolLoopError as exc:
            loop = exc
            write_json(output / "loop.json", {"reason": exc.reason, "messages": exc.messages, "history": exc.history,
                "observation_refs": exc.observation_refs, "provider_usage": exc.provider_usage})
            result["status"] = "loop_stopped"
            result["loop_reason"] = exc.reason
        result["session_ref"] = persist_client_tool_session(session_dir=workspace, session_id=plan["check_id"],
            request=request, messages=loop.messages, observation_refs=loop.observation_refs)
        result["file_errors"] = check_files(workspace, records)
        inputs = [row.get("response_metadata", {}).get("provider_usage", {}).get("input_tokens") for row in loop.history]
        known_inputs = [value for value in inputs if type(value) is int and value >= 0]
        result["peak_prompt_tokens"] = max(known_inputs) if known_inputs else None
        result["minimum_input_observed"] = (result["peak_prompt_tokens"] is not None and
                                            result["peak_prompt_tokens"] >= plan["minimum_observed_peak_prompt_tokens"])
    except Exception as exc:
        result.update(status="failed", error={"type": type(exc).__name__, "message": str(exc)})
    finally:
        result["model_attempts"] = backend.attempts if backend else 0
        if server is not None:
            if server.poll() is None:
                server.send_signal(signal.SIGINT)
                try:
                    server.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
                    result["cleanup_forced"] = True
            result["server_exit_code"] = server.returncode
        result["elapsed_seconds"] = time.monotonic() - started
        result["limitations"] = plan["limitations"]
        result["files"] = {str(path.relative_to(output)): {"sha256": digest(path), "bytes": path.stat().st_size}
                           for path in output.rglob("*") if path.is_file()}
        write_json(output / "result.json", result)
    print(json.dumps({key: result.get(key) for key in ("status", "model_attempts", "peak_prompt_tokens", "minimum_input_observed", "elapsed_seconds")}), flush=True)
    return 0 if result["status"] == "files_completed" and result.get("minimum_input_observed") else 1


if __name__ == "__main__":
    raise SystemExit(main())

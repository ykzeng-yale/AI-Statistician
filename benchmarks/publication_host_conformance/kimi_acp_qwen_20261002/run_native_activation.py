"""One operator-run native ACP conformance probe; no product controller or grader."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import selectors
import shutil
import signal
import subprocess
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=Path, required=True)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    protocol = json.loads((source / "protocol.json").read_text())
    host = args.host.resolve()
    skill = args.skill.resolve()
    assert hashlib.sha256(host.read_bytes()).hexdigest() == protocol["host_main_sha256"]
    assert hashlib.sha256((skill / "SKILL.md").read_bytes()).hexdigest() == protocol["skill_sha256"]
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=False)
    project = root / "project"
    destination = project / ".agents/skills/statistical-research"
    destination.parent.mkdir(parents=True)
    destination.symlink_to(skill, target_is_directory=True)
    (project / ".git").mkdir()
    shutil.copyfile(source / "probe.txt", project / "probe.txt")
    home = root / "home"
    data = home / "kimi-code"
    data.mkdir(parents=True)
    shutil.copyfile(source / "config.toml", data / "config.toml")
    inputs = [source / name for name in ("protocol.json", "config.toml", "probe.txt", "run_native_activation.py")]
    frozen = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    skill_hashes = {str(path.relative_to(skill)): hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in skill.rglob("*") if path.is_file()}
    (root / "precall.json").write_text(json.dumps({"files_sha256": frozen, "host": str(host),
        "skill": str(skill), "skill_files_sha256": skill_hashes, "started_unix": time.time()}, sort_keys=True, indent=2) + "\n")
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "KIMI_CODE_HOME": str(data), "TERM": "dumb"}
    selector = selectors.DefaultSelector()
    result = {"status": "FAILED", "session_id": None, "error": None}
    with (root / "stderr.log").open("xb") as stderr, (root / "acp.jsonl").open("x") as transcript:
        process = subprocess.Popen([str(host), "acp"], cwd=project, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, start_new_session=True)
        selector.register(process.stdout, selectors.EVENT_READ)
        result["pid"] = process.pid
        buffer = b""
        pending = []
        deadline = time.monotonic() + protocol["wall_seconds"]

        def send(method, params, request_id):
            row = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
            transcript.write(json.dumps({"direction": "client", "body": row}) + "\n")
            transcript.flush()
            process.stdin.write(json.dumps(row).encode() + b"\n")
            process.stdin.flush()

        def receive(predicate):
            nonlocal buffer
            for index, row in enumerate(pending):
                if predicate(row):
                    return pending.pop(index)
            while time.monotonic() < deadline:
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    row = json.loads(line)
                    transcript.write(json.dumps({"direction": "host", "body": row}) + "\n")
                    transcript.flush()
                    if "error" in row:
                        raise RuntimeError(json.dumps(row["error"]))
                    if row.get("method") == "session/request_permission":
                        raise RuntimeError("unexpected native permission request; no automatic permission fallback")
                    if predicate(row):
                        return row
                    pending.append(row)
                if selector.select(max(0, deadline - time.monotonic())):
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError("native host exited before completing ACP")
                    buffer += chunk
            raise TimeoutError("native conformance wall envelope exhausted")

        try:
            send("initialize", {"protocolVersion": 1, "clientCapabilities": {}}, 1)
            result["initialized"] = receive(lambda row: row.get("id") == 1)["result"]
            send("session/new", {"cwd": str(project), "mcpServers": []}, 2)
            session_id = receive(lambda row: row.get("id") == 2)["result"]["sessionId"]
            result["session_id"] = session_id
            commands = receive(lambda row: row.get("params", {}).get("update", {}).get(
                "sessionUpdate") == "available_commands_update")["params"]["update"]["availableCommands"]
            assert len([row for row in commands if row["name"] == "skill:statistical-research"]) == 1
            result["skill_discovered"] = True
            send("session/prompt", {"sessionId": session_id, "prompt": [
                {"type": "text", "text": protocol["prompt"]}]}, 4)
            result["prompt_result"] = receive(lambda row: row.get("id") == 4)["result"]
            result["status"] = "TERMINATED"
            send("session/close", {"sessionId": session_id}, 3)
            result["close_result"] = receive(lambda row: row.get("id") == 3)["result"]
        except Exception as error:
            result["error"] = str(error)
        finally:
            selector.close()
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
            result["process_returncode"] = process.returncode
            result["probe_unchanged"] = (project / "probe.txt").read_bytes() == (source / "probe.txt").read_bytes()
            result["ended_unix"] = time.time()
            (root / "terminal.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "session_id", "error", "probe_unchanged")}, sort_keys=True))


if __name__ == "__main__":
    main()

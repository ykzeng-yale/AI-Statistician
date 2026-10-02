"""Operator ACP lifecycle and exact final collection; the native host owns research."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import time

from ai_statistician.research_control import collect_native_research_submission
from ai_statistician.research_schema import OpenResearchQuestion


HERE = Path(__file__).resolve().parent
FINAL_PATHS = {"scientific_code": ["experiment.py"], "report": ["research.md"],
               "empirical": ["results/predictions.npy", "results/metrics.json"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("host", "skill", "materials", "project", "python", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--arm", choices=("bare", "skill"), required=True)
    args = parser.parse_args()
    protocol = json.loads((HERE / "protocol.json").read_text())
    host, skill, root, project = (p.resolve() for p in (args.host, args.skill, args.out, args.project))
    assert hashlib.sha256(host.read_bytes()).hexdigest() == protocol["host_main_sha256"]
    assert hashlib.sha256((skill / "SKILL.md").read_bytes()).hexdigest() == protocol["skill_sha256"]
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.materials, project)
    shutil.copyfile(HERE / "TASK.md", project / "TASK.md")
    (project / ".git").mkdir()
    destination = project / ".agents/skills/statistical-research"
    destination.parent.mkdir(parents=True)
    if args.arm == "skill":
        destination.symlink_to(skill, target_is_directory=True)
    home = root / "home"
    config = home / "kimi-code"
    config.mkdir(parents=True)
    shutil.copyfile(HERE / "config.toml", config / "config.toml")
    records = {str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in project.rglob("*") if p.is_file() and not p.is_relative_to(project / ".agents")}
    (root / "precall.json").write_text(json.dumps({"arm": args.arm, "inputs": records,
        "started_unix": time.time(), "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2) + "\n")
    env = {"PATH": str(args.python.resolve().parent) + ":" + os.environ["PATH"], "HOME": str(home),
           "KIMI_CODE_HOME": str(config), "TERM": "dumb", "PYTHON": str(args.python.resolve()),
           "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    result = {"status": "FAILED", "error": None}
    with (root / "stderr.log").open("xb") as stderr, (root / "acp.jsonl").open("x") as transcript:
        process = subprocess.Popen([str(host), "acp"], cwd=project, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, start_new_session=True)
        result["pid"] = process.pid
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        deadline = time.monotonic() + protocol["wall_seconds_per_draw"]
        pending, buffer = [], b""

        def send(method, params, identity):
            row = {"jsonrpc": "2.0", "id": identity, "method": method, "params": params}
            transcript.write(json.dumps({"direction": "client", "body": row}) + "\n")
            transcript.flush()
            process.stdin.write(json.dumps(row).encode() + b"\n")
            process.stdin.flush()

        def receive(predicate):
            nonlocal buffer
            for i, row in enumerate(pending):
                if predicate(row):
                    return pending.pop(i)
            while time.monotonic() < deadline:
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    row = json.loads(line)
                    transcript.write(json.dumps({"direction": "host", "body": row}) + "\n")
                    transcript.flush()
                    if "error" in row or row.get("method") == "session/request_permission":
                        raise RuntimeError("native error/permission request: " + json.dumps(row))
                    if predicate(row):
                        return row
                    pending.append(row)
                if selector.select(max(0, deadline - time.monotonic())):
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError("native ACP exited before completion")
                    buffer += chunk
            raise TimeoutError("frozen wall envelope exhausted")

        try:
            send("initialize", {"protocolVersion": 1, "clientCapabilities": {}}, 1)
            result["initialize"] = receive(lambda row: row.get("id") == 1)["result"]
            send("session/new", {"cwd": str(project), "mcpServers": []}, 2)
            session = receive(lambda row: row.get("id") == 2)["result"]["sessionId"]
            result["session_id"] = session
            commands = receive(lambda row: row.get("params", {}).get("update", {}).get(
                "sessionUpdate") == "available_commands_update")["params"]["update"]["availableCommands"]
            assert ("skill:statistical-research" in {row["name"] for row in commands}) == (args.arm == "skill")
            prompt = "Read TASK.md and complete the task. Return the final artifacts and unresolved gaps."
            if args.arm == "skill":
                prompt = "/skill:statistical-research " + prompt
            send("session/prompt", {"sessionId": session, "prompt": [{"type": "text", "text": prompt}]}, 3)
            result["prompt_result"] = receive(lambda row: row.get("id") == 3)["result"]
            result["status"] = "TERMINATED"
            send("session/close", {"sessionId": session}, 4)
            result["close"] = receive(lambda row: row.get("id") == 4)["result"]
        except Exception as error:
            result["error"] = str(error)
        finally:
            selector.close()
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
            result["process_returncode"] = process.returncode
            result["ended_unix"] = time.time()
    (root / "terminal.json").write_text(json.dumps(result, indent=2) + "\n")
    question = OpenResearchQuestion(protocol["study_id"], "Published FDA classification reimplementation",
        (HERE / "TASK.md").read_text(), task_intent={"scientific_code": "required", "empirical": "required",
                                                  "theory": "optional", "formal": "optional"})
    completed = subprocess.CompletedProcess(process.args, process.returncode,
        stdout=(root / "acp.jsonl").read_bytes(), stderr=(root / "stderr.log").read_bytes())
    ref = collect_native_research_submission(question=question, workspace_root=project,
        artifact_paths=FINAL_PATHS, host_result=completed, snapshot_dir=root / "submission")
    (root / "submission_ref.json").write_text(json.dumps(ref, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "error": result["error"], "session_id": result.get("session_id")}))


if __name__ == "__main__":
    main()

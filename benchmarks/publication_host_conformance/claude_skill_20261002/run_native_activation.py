"""One operator-authorized native Claude Code compatibility check, not research."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

from ai_statistician.cli import _load_dotenv


HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("host", "skill", "env-file", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    protocol_path = HERE / "project_protocol.json"
    protocol = json.loads(protocol_path.read_text())
    host, skill, root = (path.resolve() for path in (args.host, args.skill, args.out))
    if sha256(host) != protocol["host_sha256"]:
        raise ValueError("native host executable differs from the frozen pin")
    version = subprocess.run([str(host), "--version"], check=True, capture_output=True, text=True).stdout.strip()
    if version != protocol["host_version"]:
        raise ValueError("native host version differs from the frozen pin")
    if {name: sha256(skill / name) for name in protocol["skill_sha256"]} != protocol["skill_sha256"]:
        raise ValueError("skill files differ from the frozen package")
    _load_dotenv(args.env_file.resolve())
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("the designated credential source is not configured")
    root.mkdir(parents=True, exist_ok=False)
    project = root / "project"
    copied = project / "skills/statistical-research"
    shutil.copytree(skill, copied)
    destination = project / ".claude/skills/statistical-research"
    destination.parent.mkdir(parents=True)
    destination.symlink_to("../../skills/statistical-research", target_is_directory=True)
    (project / "probe.txt").write_text(protocol["receipt"])
    home = root / "home"
    home.mkdir()
    command = [str(host), "--setting-sources", "project",
               "--model", protocol["requested_model"], "--permission-mode", protocol["permission_mode"],
               "--tools", ",".join(protocol["tools"]), "--allowedTools", ",".join(protocol["tools"]),
               "--max-budget-usd", str(protocol["max_budget_usd"]), "--output-format", "stream-json",
               "--verbose", "--print", protocol["prompt"]]
    precall = {"command": command, "version": version, "host_sha256": sha256(host),
               "runner_sha256": sha256(Path(__file__)), "protocol_sha256": sha256(protocol_path),
               "skill_sha256": {name: sha256(copied / name) for name in protocol["skill_sha256"]},
               "probe_sha256": sha256(project / "probe.txt"), "started_unix": time.time(),
               "credential_value_recorded": False, "scientific_evaluation": False}
    with (root / "precall.json").open("x") as stream:
        json.dump(precall, stream, indent=2)
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "TERM": "dumb",
           "ANTHROPIC_API_KEY": key, "CLAUDE_CONFIG_DIR": str(home / ".claude"),
           "DISABLE_TELEMETRY": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
    terminal = {"status": "TERMINATED", "error": None, "scientific_evaluation": False}
    started = time.monotonic()
    with (root / "stdout.jsonl").open("xb") as stdout, (root / "stderr.log").open("xb") as stderr:
        process = subprocess.Popen(command, cwd=project, env=env, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        terminal["pid"] = process.pid
        try:
            process.wait(timeout=protocol["wall_seconds"])
        except subprocess.TimeoutExpired:
            terminal.update(status="TIMEOUT", error="frozen host conformance wall envelope exhausted")
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
        terminal.update(returncode=process.returncode, elapsed_seconds=time.monotonic() - started)
    terminal["captured_sha256"] = {name: sha256(root / name) for name in ("stdout.jsonl", "stderr.log")}
    terminal["receipt_sha256"] = sha256(project / "receipt.md") if (project / "receipt.md").is_file() else None
    terminal["skill_sha256_after"] = {name: sha256(copied / name) for name in protocol["skill_sha256"]}
    with (root / "terminal.json").open("x") as stream:
        json.dump(terminal, stream, indent=2)
    print(json.dumps(terminal))
    return 0 if process.returncode == 0 and terminal["status"] == "TERMINATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

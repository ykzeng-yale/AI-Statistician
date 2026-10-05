"""Rebuild one committed package in a fresh owned tree; stop on any failed stage."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import time


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("uv", type=Path)
    parser.add_argument("python", type=Path)
    parser.add_argument("node_bin", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    source, output = args.source.resolve(), args.output.resolve()
    output.mkdir()
    home, cache, researcher, venv = [output / name for name in ("home", "cache", "researcher", "venv")]
    for directory in (home, cache, researcher):
        directory.mkdir()
    binaries = {"uv": args.uv, "python": args.python, "node": args.node_bin / "node",
                "npm_entry": args.node_bin.parent / "lib/node_modules/npm/bin/npm-cli.js"}
    identities = {name: sha256(path) for name, path in binaries.items()}
    assert all(value == plan["existing_toolchain"][name + "_sha256"]
               for name, value in identities.items()), identities
    assert sha256(source / "package-lock.json") == plan["package_lock_sha256"]
    probe = source / "benchmarks/publication_release_qualification_20261003/probe_installed_tools.py"
    assert sha256(probe) == plan["probe_sha256"]
    envelope = plan["resource_envelope"]
    env = {"HOME": str(home), "PATH": f"{venv}/bin:{args.node_bin}:/usr/bin:/bin:/usr/sbin:/sbin",
           "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8", "PYTHONNOUSERSITE": "1",
           "UV_CACHE_DIR": str(cache / "uv"), "UV_PYTHON_DOWNLOADS": "never",
           "npm_config_cache": str(cache / "npm"), "OMP_NUM_THREADS": "1",
           "OPENBLAS_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1",
           "NODE_OPTIONS": f"--max-old-space-size={envelope['node_old_space_megabytes']}",
           "AI_STATISTICIAN_SCIENTIFIC_SANDBOX_NODE_MODULES": str(source / "node_modules")}
    start = time.monotonic()
    record = {"scope": plan["purpose"], "model_calls": 0, "study_activated": False,
              "driver_pid": os.getpid(), "started_at": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "source_commit": plan["source_commit"],
              "plan_sha256": sha256(args.plan), "driver_sha256": sha256(__file__),
              "toolchain_sha256": identities, "environment": env, "stages": []}
    result_path = output / "record.json"
    uv = [str(args.uv), "--no-config"]
    npm = str(args.node_bin / "npm")
    python = str(venv / "bin/python")
    stages = [
        ("build", uv + ["build", "--wheel", "--python", str(args.python), "--out-dir", str(output / "dist")], source),
        ("venv", uv + ["venv", "--python", str(args.python), str(venv)], researcher),
        ("install", None, researcher),
        ("npm", [npm, "ci", "--omit=dev"], source),
        ("prepare", [npm, "run", "prepare:scientific-sandbox"], source),
        ("help", [str(venv / "bin/ai-statistician"), "--help"], researcher),
        ("list", [str(venv / "bin/ai-statistician"), "list"], researcher),
        ("doctor", [str(venv / "bin/ai-statistician"), "doctor", "--out", str(output / "doctor"), "--json"], researcher),
        ("probe", [python, str(probe), str(output / "probe")], researcher),
        ("packages", uv + ["pip", "list", "--python", python, "--format", "json"], researcher),
    ]
    for name, command, cwd in stages:
        if name == "install":
            wheels = list((output / "dist").glob("*.whl"))
            assert len(wheels) == 1, wheels
            record["wheel_sha256"] = sha256(wheels[0])
            command = uv + ["pip", "install", "--python", python, str(wheels[0]), *plan["python_dependencies"]]
        timeout = min(envelope["runtime_preparation_timeout_seconds"] if name == "prepare"
                      else envelope["ordinary_stage_timeout_seconds"],
                      envelope["total_timeout_seconds"] - (time.monotonic() - start))
        assert timeout > 0, "Total installation timeout reached"
        step = {"name": name, "command": command, "cwd": str(cwd), "timeout_s": timeout,
                "started_at": datetime.now(timezone.utc).isoformat()}
        record["stages"].append(step)
        stamp = time.monotonic()
        with (output / f"{name}.stdout").open("wb") as stdout, (output / f"{name}.stderr").open("wb") as stderr:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout,
                                       stderr=stderr, start_new_session=True)
            step["pid"] = process.pid
            result_path.write_text(json.dumps(record, indent=2))
            print(json.dumps({"stage": name, "pid": process.pid, "started_at": step["started_at"]}), flush=True)
            try:
                step["exit_code"] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                step["timed_out"] = True
                os.killpg(process.pid, signal.SIGKILL)
                step["exit_code"] = process.wait()
        step["elapsed_s"] = time.monotonic() - stamp
        step["stdout_sha256"] = sha256(output / f"{name}.stdout")
        step["stderr_sha256"] = sha256(output / f"{name}.stderr")
        step["owned_bytes_after_stage"] = sum(path.stat().st_size for path in source.parent.rglob("*")
                                              if path.is_file() and not path.is_symlink())
        record["elapsed_s"] = time.monotonic() - start
        result_path.write_text(json.dumps(record, indent=2))
        if step["exit_code"] != 0 or step["owned_bytes_after_stage"] > envelope["owned_disk_post_stage_limit_bytes"]:
            raise SystemExit(f"Installation stopped at {name}; preserve {result_path}")
    record["status"] = "PASSED_INSTALLATION_PROBE_ONLY"
    result_path.write_text(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

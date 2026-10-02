"""Launch one fresh declared draw and retain process evidence, without scoring."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def _file_ref(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "sha256": digest, "byte_size": path.stat().st_size}


def _stop_owned_group(process, grace_seconds):
    sent = []
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
            sent.append(sig.name)
        except ProcessLookupError:
            pass
        if sig == signal.SIGTERM:
            try:
                process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired:
                pass
    process.wait()
    return sent


def run_declared_draw(*, config_path, record_dir, wall_seconds=None, shutdown_grace_seconds=10):
    """Own only the newly launched process group, never the model server.

    A caller-selected wall envelope includes the child CLI's preparation, graph
    and final collection. None adds no cap. This does not select/evaluate files,
    retry a failed draw or verify deployment/resource parity between study arms.
    """
    for value in (wall_seconds, shutdown_grace_seconds):
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value <= 0):
            raise ValueError("process time declarations must be finite positive numbers or None")
    if shutdown_grace_seconds is None:
        raise ValueError("shutdown grace must be declared")
    if os.name != "posix":
        raise RuntimeError("this experiment launcher requires POSIX process groups")
    config_path, record_dir = Path(config_path).resolve(), Path(record_dir).resolve()
    config_ref = _file_ref(config_path)
    root = Path(__file__).resolve().parents[2]
    command = [sys.executable, "-m", "benchmarks.publication.draw_cli", "--config", str(config_path),
               "--out", str(record_dir / "draw")]
    record_dir.mkdir(parents=True, exist_ok=False)
    launch = {"command": command, "cwd": str(root), "config_ref": config_ref,
              "launcher_ref": _file_ref(Path(__file__).resolve()),
              "entry_ref": _file_ref(root / "benchmarks/publication/draw_cli.py"),
              "python_ref": _file_ref(Path(sys.executable).resolve()),
              "wall_seconds": wall_seconds, "shutdown_grace_seconds": shutdown_grace_seconds,
              "started_unix": time.time(), "model_server_owned": False,
              "wall_scope": "child_launch_through_exit_or_stop_decision",
              "scientific_evaluation_performed": False}
    with (record_dir / "launch.json").open("x", encoding="utf-8") as stream:
        json.dump(launch, stream, indent=2, allow_nan=False)
    terminal = {"disposition": "LAUNCH_FAILED", "pid": None, "returncode": None, "exception_type": None,
                "termination_signals": [], "model_server_owned": False,
                "termination_scope": "owned_POSIX_process_group_not_escaped_children_or_server",
                "scientific_evaluation_performed": False}
    process = None
    started = time.monotonic()
    try:
        with (record_dir / "stdout.log").open("xb") as stdout, (record_dir / "stderr.log").open("xb") as stderr:
            try:
                process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                                           stdout=stdout, stderr=stderr, start_new_session=True)
                terminal["pid"] = process.pid
                process.wait(timeout=wall_seconds)
                terminal["disposition"] = "EXITED"
            except subprocess.TimeoutExpired:
                terminal["disposition"] = "TIMED_OUT"
            except BaseException as exc:
                terminal["exception_type"] = type(exc).__name__
                if process is not None:
                    terminal["disposition"] = "INTERRUPTED"
                raise
            finally:
                terminal["process_elapsed_seconds"] = time.monotonic() - started
                if process is not None:
                    terminal["termination_signals"] = _stop_owned_group(process, shutdown_grace_seconds)
                    terminal["returncode"] = process.returncode
    finally:
        terminal["elapsed_seconds_including_cleanup"] = time.monotonic() - started
        terminal["launch_ref"] = _file_ref(record_dir / "launch.json")
        terminal["captured_streams"] = {name: _file_ref(record_dir / name) for name in ("stdout.log", "stderr.log")
                                        if (record_dir / name).is_file()}
        terminal["config_unchanged_at_termination"] = config_path.is_file() and _file_ref(config_path) == config_ref
        with (record_dir / "terminal.json").open("x", encoding="utf-8") as stream:
            json.dump(terminal, stream, indent=2, allow_nan=False)
    return terminal


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--wall-seconds", type=float)
    parser.add_argument("--shutdown-grace-seconds", type=float, default=10)
    args = parser.parse_args(argv)
    terminal = run_declared_draw(config_path=args.config, record_dir=args.out, wall_seconds=args.wall_seconds,
                                 shutdown_grace_seconds=args.shutdown_grace_seconds)
    print(json.dumps(terminal, allow_nan=False))
    return 0 if (terminal["disposition"] == "EXITED" and terminal["returncode"] == 0
                 and terminal["config_unchanged_at_termination"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())

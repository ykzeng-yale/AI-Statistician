"""Run the prospectively fixed author scripts once, with separate raw logs."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    plan_path = Path(__file__).with_name("stepmix_plan.json")
    ready_path = Path(__file__).with_name("stepmix_ready.json")
    plan = json.loads(plan_path.read_text())
    ready = json.loads(ready_path.read_text())
    assert ready["plan_sha256"] == sha256(plan_path)
    python = Path(ready["python"])
    assert sha256(python.resolve()) == ready["python_sha256"]
    inventory_path = root / ready["installed_inventory"]
    assert sha256(inventory_path) == ready["installed_inventory_sha256"]
    for row in json.loads(inventory_path.read_text()):
        assert sha256(python.parent.parent / row["path"]) == row["sha256"]
    source = root / plan["execution"]["source_root"]
    execution = root / plan["execution"]["execution_root"]
    for row in ready["inputs"]:
        assert sha256(source / row["path"]) == row["sha256"]
    for row in plan["execution"]["script_order"]:
        assert sha256(source / row["file"]) == row["sha256"]
    # A consumed directory is never resumed or overwritten.
    shutil.copytree(source, execution)
    home = execution / "home"
    home.mkdir()
    env = {
        "PATH": f"{python.parent}:/usr/bin:/bin",
        "HOME": str(home),
        "LANG": "en_US.UTF-8",
        "PYTHONUNBUFFERED": "1",
        "PYTHONNOUSERSITE": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    started = time.monotonic()
    records = []
    for i, row in enumerate(plan["execution"]["script_order"], 1):
        command = [str(python), row["file"], *row["args"]]
        print(f"Stage {i}: {' '.join(command)}", flush=True)
        elapsed = time.monotonic() - started
        remaining = plan["execution"]["wall_time_limit_seconds"] - elapsed
        timed_out = remaining <= 0
        stage_start = time.monotonic()
        returncode = None
        with (execution / f"{i}.stdout.log").open("xb") as out:
            with (execution / f"{i}.stderr.log").open("xb") as err:
                if not timed_out:
                    try:
                        result = subprocess.run(command, cwd=execution, env=env,
                                                stdout=out, stderr=err, timeout=remaining)
                        returncode = result.returncode
                    except subprocess.TimeoutExpired:
                        timed_out = True
        record = {"stage": i, "command": command, "returncode": returncode,
                  "timed_out": timed_out, "wall_seconds": time.monotonic() - stage_start}
        records.append(record)
        (execution / f"{i}.terminal.json").write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record), flush=True)
        if timed_out or returncode != 0:
            break
    complete = len(records) == len(plan["execution"]["script_order"]) and all(
        r["returncode"] == 0 for r in records
    )
    terminal = {"plan_sha256": sha256(plan_path), "ready_sha256": sha256(ready_path),
                "stages": records, "complete_python_execution": complete,
                "wall_seconds": time.monotonic() - started, "model_calls": 0}
    (execution / "terminal.json").write_text(json.dumps(terminal, indent=2) + "\n")
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())

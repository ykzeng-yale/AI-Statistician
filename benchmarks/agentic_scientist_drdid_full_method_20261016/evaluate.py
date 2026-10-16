"""Execute the model's full project; check accounting, never statistical truth."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


METHODS = {
    "panel": ("dr_imp", "dr_tr", "ipw", "ipw_std", "reg", "twfe"),
    "rc": ("dr_imp1", "dr_imp2", "dr_tr1", "dr_tr2", "ipw", "ipw_std", "reg", "twfe"),
}
REPETITIONS = 10000


def dump(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def check_tables(root, *, repetitions=REPETITIONS):
    groups = {(frame, str(dgp), str(n), method): bytearray(repetitions)
              for frame, methods in METHODS.items()
              for dgp, n, method in itertools.product(range(1, 5), (500, 1000), methods)}
    counts, failures = {key: 0 for key in groups}, {key: 0 for key in groups}

    def outcome(row, fields):
        if row["status"] == "failed":
            if not row["error"].strip():
                raise ValueError("Failed method record needs its actual error")
            return True
        if row["status"] != "ok" or not all(math.isfinite(float(row[field])) for field in fields):
            raise ValueError("Successful method record needs finite numerical output")
        if float(row["se"]) < 0 or ("lci" in fields and float(row["lci"]) > float(row["uci"])):
            raise ValueError("Invalid SE or interval record")
        return False

    with (root / "replicates.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            key = tuple(row[field] for field in ("frame", "dgp", "n", "method"))
            index = int(row["replicate"]) - 1
            if key not in groups or not 0 <= index < repetitions or groups[key][index]:
                raise ValueError("Unexpected, repeated or out-of-range method/dataset record")
            groups[key][index] = 1
            counts[key] += 1
            failures[key] += outcome(row, ("truth", "oracle_att", "efficiency_bound", "estimate", "se", "lci", "uci"))
    if any(count != repetitions for count in counts.values()):
        raise ValueError("The declared full Monte Carlo grid is incomplete")
    with (root / "study_summary.csv").open(newline="") as stream:
        summary_keys = [tuple(row[field] for field in ("frame", "dgp", "n", "method"))
                        for row in csv.DictReader(stream)]
    if len(summary_keys) != len(groups) or set(summary_keys) != set(groups):
        raise ValueError("Summary must retain every declared method/cell exactly once")
    expected = {(str(sample), str(covariate), method)
                for sample, covariate, method in itertools.product(range(1, 4), range(1, 4), METHODS["panel"])}
    app_keys, app_failures = [], 0
    with (root / "application.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            app_keys.append(tuple(row[field] for field in ("sample_id", "covariate_id", "method")))
            app_failures += outcome(row, ("estimate", "se"))
    if len(app_keys) != len(expected) or set(app_keys) != expected:
        raise ValueError("The original application grid is incomplete or duplicated")
    if not (root / "study_notes.md").read_text().strip():
        raise ValueError("Missing executed-study notes")
    return {"method_attempts": sum(counts.values()), "method_failures": sum(failures.values()),
            "summary_rows": len(summary_keys), "application_attempts": len(app_keys),
            "application_failures": app_failures,
            "method_cells": [{"frame": key[0], "dgp": key[1], "n": key[2], "method": key[3],
                              "attempted": counts[key], "failed": failures[key]} for key in counts]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program_path", required=True, type=Path)
    parser.add_argument("--results_dir", required=True, type=Path)
    args = parser.parse_args(argv)
    root = args.results_dir.resolve()
    # Exclusive claim precedes execution: no consumed output is reused.
    dump(root / "execution_started.json", {"scientific_acceptance": False})
    source = Path(os.environ["TASK_SOURCE_DIR"]).resolve() / "resources/search/drdid"
    command = [sys.executable, str(args.program_path.resolve()),
               "--source-dir", str(source), "--output-dir", str(root)]
    observation = {"command": command, "exit_code": None, "error": None,
                   "scope": "Full project execution and record accounting only; mathematical correctness, numerical reproduction and report accuracy remain unassessed",
                   "theory": "UNASSESSED", "reproduction_accuracy": "UNASSESSED",
                   "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    start = time.monotonic()
    complete = False
    try:
        process = subprocess.run(command, cwd=root, check=False)
        observation["exit_code"] = process.returncode
        if process.returncode:
            raise RuntimeError(f"Research project exited {process.returncode}; see raw stdout/stderr")
        observation["accounting"] = check_tables(root)
        complete = True
    except Exception:
        observation["error"] = traceback.format_exc()
        print(observation["error"], file=sys.stderr, flush=True)
    observation.update(elapsed_seconds=time.monotonic() - start, records_complete=complete)
    dump(root / "execution_observation.json", observation)
    dump(root / "metrics.json", {"combined_score": int(complete), "records_complete": int(complete)})
    dump(root / "correct.json", {"correct": complete})
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())

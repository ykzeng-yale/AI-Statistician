"""First external execution of immutable final submissions, not an author retry."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from ai_statistician.research_control import load_native_research_submission
from ai_statistician.research_schema import OpenResearchQuestion

from run_draw import FINAL_PATHS


HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    protocol = json.loads((HERE / "protocol.json").read_text())
    question = OpenResearchQuestion(protocol["study_id"], "Published FDA classification reimplementation",
        (HERE / "TASK.md").read_text(), task_intent={"scientific_code": "required", "empirical": "required",
                                                  "theory": "optional", "formal": "optional"})
    data = root / "preparation/materials/data/phoneme.npz"
    assert hashlib.sha256(data.read_bytes()).hexdigest() == protocol["inputs"]["phoneme_npz_sha256"]
    evaluator = root / "evaluation"
    evaluator.mkdir(exist_ok=False)
    records = {"evidence_role": "first_external_numeric_check_not_author_feedback",
               "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "arms": {}}
    environment = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    for arm in protocol["draw_order"]:
        draw = root / (arm + "_1")
        submission = load_native_research_submission(json.loads((draw / "submission_ref.json").read_text()),
            question=question, artifact_paths=FINAL_PATHS, snapshot_dir=draw / "submission")
        source = submission["artifact_bytes"]["scientific_code"].get("experiment.py")
        checks = []
        for seed in protocol["reference"]["split_seeds"]:
            if source is None:
                checks.append({"split_seed": seed, "status": "not_executed_missing_final_source"})
                continue
            directory = evaluator / arm / str(seed)
            directory.mkdir(parents=True)
            (directory / "experiment.py").write_bytes(source)
            command = [str(args.python.resolve()), "experiment.py", "--data", str(data),
                       "--split-seed", str(seed), "--out", "results"]
            started = time.time()
            with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
                process = subprocess.Popen(command, cwd=directory, env=environment,
                    stdout=stdout, stderr=stderr, start_new_session=True)
                timed_out = False
                try:
                    process.wait(timeout=protocol["evaluation_seconds_per_variant"])
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
            numeric = subprocess.run([str(args.python.resolve()), str(HERE / "check_numeric.py"),
                "--actual", str(directory / "results"), "--reference", str(root / "preparation/reference"),
                "--seed", str(seed)], capture_output=True, text=True, check=True)
            record = {"split_seed": seed, "command": command, "cwd": str(directory),
                      "source_sha256": hashlib.sha256(source).hexdigest(), "returncode": process.returncode,
                      "timed_out": timed_out, "started_unix": started, "elapsed_seconds": time.time() - started,
                      "output_checks": json.loads(numeric.stdout),
                      "logs": {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                               for name in ("stdout.log", "stderr.log")}}
            (directory / "execution.json").write_text(json.dumps(record, indent=2) + "\n")
            checks.append(record)
        records["arms"][arm] = {"missing_final_artifacts": submission["missing_artifacts"], "variants": checks}
    (evaluator / "executions.json").write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()

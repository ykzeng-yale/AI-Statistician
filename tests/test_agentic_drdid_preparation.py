"""New task accounting tests; opaque fixtures are not statistical evidence."""

import csv
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys

import pytest


BENCH = Path(__file__).resolve().parents[1] / "benchmarks/agentic_scientist_drdid_full_method_20261016"
SPEC = importlib.util.spec_from_file_location("drdid_accounting", BENCH / "evaluate.py")
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def tables(root, *, reps=2):
    rows, summaries = [], []
    for frame, methods in EVALUATOR.METHODS.items():
        for dgp, n, method in itertools.product(range(1, 5), (500, 1000), methods):
            base = {"frame": frame, "dgp": dgp, "n": n, "method": method}
            summaries.append(base)
            rows.extend({**base, "replicate": index, "truth": 0, "oracle_att": 0,
                         "efficiency_bound": 1, "estimate": 0,
                         "se": 1, "lci": -2, "uci": 2, "status": "ok", "error": ""}
                        for index in range(1, reps + 1))
    application = [{"sample_id": sample, "covariate_id": covariate, "method": method,
                    "estimate": 0, "se": 1, "status": "ok", "error": ""}
                   for sample, covariate, method in itertools.product(range(1, 4), range(1, 4), EVALUATOR.METHODS["panel"])]
    write_csv(root / "replicates.csv", rows)
    write_csv(root / "study_summary.csv", summaries)
    write_csv(root / "application.csv", application)
    (root / "study_notes.md").write_text("Opaque unit fixture, not executed statistical research.")
    return rows, summaries, application


def test_accounting_preserves_declared_failures_without_certifying_science(tmp_path):
    rows, _, app = tables(tmp_path)
    rows[0].update(status="failed", error="original raw failure", estimate="", se="", lci="", uci="")
    app[0].update(status="failed", error="original application failure", estimate="", se="")
    write_csv(tmp_path / "replicates.csv", rows)
    write_csv(tmp_path / "application.csv", app)
    observed = EVALUATOR.check_tables(tmp_path, repetitions=2)
    assert observed["method_attempts"] == 224
    assert observed["summary_rows"] == 112 and observed["application_attempts"] == 54
    assert observed["method_failures"] == observed["application_failures"] == 1


@pytest.mark.parametrize("change", ["missing", "duplicate", "index", "nonfinite", "failure_reason", "summary", "application"])
def test_accounting_rejects_incomplete_or_invalid_delivery(tmp_path, change):
    rows, summary, app = tables(tmp_path)
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[-1] = rows[0]
    elif change == "index":
        rows[0]["replicate"] = 0
    elif change == "nonfinite":
        rows[0]["estimate"] = "NaN"
    elif change == "failure_reason":
        rows[0]["status"] = "failed"
    elif change == "summary":
        summary[-1] = summary[0]
    else:
        app[-1] = app[0]
    write_csv(tmp_path / "replicates.csv", rows)
    write_csv(tmp_path / "study_summary.csv", summary)
    write_csv(tmp_path / "application.csv", app)
    with pytest.raises(ValueError):
        EVALUATOR.check_tables(tmp_path, repetitions=2)


def test_real_project_failure_is_public_once_and_not_repaired(tmp_path, monkeypatch):
    monkeypatch.setenv("TASK_SOURCE_DIR", str(tmp_path / "task"))
    source = tmp_path / "src"
    source.mkdir()
    program = source / "program.py"
    program.write_text("raise RuntimeError('opaque project failure')\n")
    command = [sys.executable, str(BENCH / "evaluate.py"), "--program_path", str(program), "--results_dir", str(tmp_path)]
    first = subprocess.run(command, capture_output=True, text=True)
    assert first.returncode == 1 and "opaque project failure" in first.stderr
    observation = (tmp_path / "execution_observation.json").read_bytes()
    record = json.loads(observation)
    assert record["exit_code"] == 1 and not record["records_complete"]
    assert record["command"][-3:] == [str(tmp_path / "task/resources/search/drdid"), "--output-dir", str(tmp_path)]
    assert record["theory"] == record["reproduction_accuracy"] == "UNASSESSED"
    assert json.loads((tmp_path / "correct.json").read_text()) == {"correct": False}
    second = subprocess.run(command, capture_output=True, text=True)
    assert second.returncode != 0 and "FileExistsError" in second.stderr
    assert (tmp_path / "execution_observation.json").read_bytes() == observation
    assert program.read_text() == "raise RuntimeError('opaque project failure')\n"


def test_default_is_full_both_structure_study_not_a_toy_gate():
    assert EVALUATOR.REPETITIONS == 10000
    brief = (BENCH / "brief.md").read_text()
    assert "160,000 datasets" in brief and "54 estimator/inference records" in brief
    assert "NOT executed" in brief and "UNASSESSED" in (BENCH / "evaluate.py").read_text()


def test_condition_binds_exact_deployment_and_uses_only_existing_controller():
    import hashlib
    config = json.loads((BENCH / "api_config.json").read_text())
    condition_bytes = (BENCH / "deployment_condition.json").read_bytes()
    condition = json.loads(condition_bytes)
    assert config["deployment_ref"]["sha256"] == hashlib.sha256(condition_bytes).hexdigest()
    assert config["model"] == condition["serving"]["alias"]
    assert config["max_tokens"] == 393216 and config["max_turns"] == 256
    assert condition["serving"]["context"] == 1000000
    runner = (BENCH / "run_condition.sh").read_text()
    assert "src.pipeline.cli" in runner and "agent_runtime" not in runner
    assert "harness_evaluated_attempts=false" in runner
    assert "posthoc.execution.checkpoint_mode" not in runner

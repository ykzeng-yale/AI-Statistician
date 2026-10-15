"""Preparation checks only; no models or consumed scientific outputs are used."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmarks" / "agentic_scientist_hc0_bouchet_20261015"


def load_preparer():
    spec = importlib.util.spec_from_file_location("hc0_preparation", BENCH / "prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fresh_arms_share_task_evaluator_and_unimplemented_seed(tmp_path):
    prepare = load_preparer().prepare
    stock, statistical = tmp_path / "stock", tmp_path / "statistical"
    prepare(stock, "stock")
    prepare(statistical, "statistical")
    for name in ("task.md", "evaluate.py", "requirements.txt", "rubrics.json", "program_0/src/program.py"):
        assert (stock / "task" / name).read_bytes() == (statistical / "task" / name).read_bytes()
    assert "NotImplementedError" in (stock / "task/program_0/src/program.py").read_text()
    rubric = json.loads((stock / "task/rubrics.json").read_text())[0]
    assert rubric["metric"] == "combined_score"
    assert rubric["operator"] == ">=" and rubric["threshold"] == 1.0
    assert not (stock / "task/resources").exists()
    assert (statistical / "task/resources/search/statistical-research/SKILL.md").read_bytes() == (
        ROOT / "skills/statistical-research/SKILL.md"
    ).read_bytes()
    assert (statistical / "investigate.md").read_bytes() == (
        ROOT / "integrations/agentic-scientist/prompts/investigate.md"
    ).read_bytes()
    for arm in (stock, statistical):
        manifest = json.loads((arm / "prepared_inputs.json").read_text())
        assert manifest["arm"] == arm.name
        for name, digest in manifest["files"].items():
            assert hashlib.sha256((arm / name).read_bytes()).hexdigest() == digest
    with pytest.raises(FileExistsError):
        prepare(stock, "stock")


def test_prepared_rubric_is_consumed_by_the_real_upstream_checker(tmp_path):
    upstream = ROOT / "third_party/ai-scientist-v3"
    executable = Path(os.environ.get("AI_STATISTICIAN_V3_PYTHON", upstream / ".venv/bin/python"))
    if not executable.is_file():
        pytest.skip("Initialize the pinned upstream environment for rubric conformance")
    arm = tmp_path / "stock"
    load_preparer().prepare(arm, "stock")
    script = r'''
import json, sys
from pathlib import Path
from src.investigation.harness_eval import _rubric_status
from src.investigation.rubric_checks import rubric_metric_check
rubric = json.loads(Path(sys.argv[1]).read_text())[0]
assert rubric_metric_check(rubric) == ("combined_score", ">=", 1.0)
for metrics, correct, exit_code, expected in (
    ({"combined_score": 1.0}, True, 0, True),
    ({"combined_score": 0.0}, True, 0, False),
    ({"combined_score": 1.0}, False, 0, False),
    ({"combined_score": 1.0}, True, 1, False),
    ({}, True, 0, False),
):
    passed, evidence = _rubric_status(
        rubric=rubric, metrics=metrics, correct=correct,
        exit_code=exit_code, missing_candidate_patterns=set(),
    )
    assert passed is expected, evidence
'''
    result = subprocess.run(
        [str(executable), "-c", script, str(arm / "task/rubrics.json")],
        cwd=upstream, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_numerical_certificate_or_mandatory_diagnostic_stage():
    brief = (BENCH / "task.md").read_text()
    assert "5,000 independent replicates in each of 12 cells" in brief
    assert "Theory remains\nunassessed" in brief
    assert "does not require a preliminary small simulation" in brief
    assert "Do not run the official" in brief
    assert "master seed" in (BENCH / "README.md").read_text().lower()

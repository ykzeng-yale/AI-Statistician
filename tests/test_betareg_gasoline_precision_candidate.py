from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import (
    _visible_question_hash_payload,
)
from ai_statistician.research_source_library import (
    load_research_source_execution_spec,
    load_research_source_snapshot,
)


TASK_ID = "betareg_jss_gasoline_precision_public_replication"
BENCHMARK_ID = "research-l1-betareg-jss-gasoline-precision-20260903-v1"
VISIBLE_PATH = Path(
    "benchmarks/research_l1_betareg_gasoline_precision_"
    "replication_questions_20260903.json"
)
SOURCE_ROOT = Path("benchmarks/research_sources/betareg_jss_2010_20260829")
EXECUTION_PATH = SOURCE_ROOT / "source_execution_gasoline_precision_manifest.json"
EVALUATOR_ROOT = Path(
    "benchmarks/evaluator_only/betareg_gasoline_precision_20260903"
)
CANDIDATE_PATH = EVALUATOR_ROOT / "sealed_gold_candidate.json"
HARNESS_PATH = EVALUATOR_ROOT / "hidden_source_replication_harness.py"
LEDGER_PATH = Path(
    "docs/evaluation_activations/"
    "betareg_gasoline_precision_candidate_preactivation.json"
)
LADDER_PATH = Path("benchmarks/research_capability_ladder_20260814.json")

SYNTHETIC_STDOUT = """
Call:
betareg(formula = yield ~ batch + temp, data = GasolineYield)

Coefficients (mean model with logit link):
Phi coefficients (precision model with identity link):
Log-likelihood:  84.8 on 12 Df
Pseudo R-squared: 0.9617
(Intercept)
   440.2783
(Intercept)
   577.7907
"""
SYNTHETIC_STDERR = "pinned runtime warning\n"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_harness() -> tuple[dict, object]:
    namespace = runpy.run_path(str(HARNESS_PATH))
    evaluate = namespace["evaluate_artifact"]
    evaluate.__globals__["EXPECTED_STDOUT_SHA256"] = _text_sha256(
        SYNTHETIC_STDOUT
    )
    evaluate.__globals__["EXPECTED_STDERR_SHA256"] = _text_sha256(
        SYNTHETIC_STDERR
    )
    return namespace, evaluate


def _candidate() -> dict:
    return {
        "schema_version": 3,
        "artifact_kind": "SourceReplicationManifest",
        "question_id": TASK_ID,
        "benchmark_id": BENCHMARK_ID,
        "execution_id": (
            "betareg-jss-2010-gasoline-precision-"
            "source-execution-20260903-v1"
        ),
        "execution_spec_sha256": _sha256(EXECUTION_PATH),
        "source_snapshot_id": (
            "betareg-jss-2010-r-public-replication-20260829-v1"
        ),
        "source_snapshot_hash": (
            "3c4c642b44ea9413b8b29f456606568a356e2b9c0b6301b8829ae3d640b67c8b"
        ),
        "source_manifest_sha256": (
            "a3af9e0459f026a34bf305f4685676501c0422bc1ed82b22448ed80c002c2582"
        ),
        "source_commit": "jss-v034i02-official-source-2010-04-05",
        "entrypoint_document_id": "betareg-jss-official-r-example",
        "executed_entrypoint_sha256": (
            "0725416e1d260a76acf2f27db9a028ee5cf8366a1bb766e3e8115c5b381de57d"
        ),
        "execution_attempted": True,
        "execution_status": "EXECUTED",
        "returncode": 0,
        "errors": [],
        "source_mutated": False,
        "staged_source_inputs_mutated": False,
        "runtime_edited_source": False,
        "command_owned_by_model": False,
        "network_access": False,
        "secret_environment_inherited": False,
        "unexpected_workspace_artifacts": [],
        "execution_workspace_mode": "staged_copy_on_write",
        "runtime_language": "r",
        "runtime_version": "R version 4.4.3 (2025-02-28)",
        "package_versions": {
            "Formula": "1.0.0",
            "betareg": "2.2.0",
            "lmtest": "0.9.40",
            "sandwich": "3.1.0",
            "strucchange": "1.5.4",
            "zoo": "1.8.15",
        },
        "raw_stdout": SYNTHETIC_STDOUT,
        "raw_stderr": SYNTHETIC_STDERR,
        "stdout_sha256": _text_sha256(SYNTHETIC_STDOUT),
        "stderr_sha256": _text_sha256(SYNTHETIC_STDERR),
        "declared_result_artifact_paths": ["Rplots.pdf"],
        "result_artifacts": [
            {
                "relative_path": "Rplots.pdf",
                "sha256": "a" * 64,
                "size_bytes": 59037,
                "content_encoding": "binary_not_embedded",
            }
        ],
    }


def test_sealed_candidate_is_narrow_hash_bound_and_not_activated() -> None:
    visible = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))
    question = visible["questions"][0]
    candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    task = candidate["sealed_task"]

    assert question["id"] == TASK_ID
    assert task["task_id"] == TASK_ID
    assert candidate["benchmark_id"] == BENCHMARK_ID
    assert candidate["status"] == (
        "sealed_pending_exact_haiku_semantic_qualification"
    )
    assert candidate["activation_allowed"] is False
    assert candidate["product_runtime_started"] is False
    assert candidate["preactivation_product_model_calls"] == 0
    assert candidate["preactivation_evaluator_model_calls"] == 0
    assert candidate["model_policy"] == {
        "provider": "anthropic",
        "model_tier": "haiku",
        "model": "claude-haiku-4-5-20251001",
        "automatic_tier_escalation_allowed": False,
    }
    assert task["task_intent"] == question["task_intent"]
    assert question["task_intent"] == {
        "source_replication": "required",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    assert "440.2783" not in VISIBLE_PATH.read_text(encoding="utf-8")
    assert "577.7907" not in VISIBLE_PATH.read_text(encoding="utf-8")
    assert "FoodExpenditure" not in question["description"]
    assert "ReadingSkills" not in question["description"]
    assert "other article examples" in question["description"]

    assert candidate["model_visible_questions_sha256"] == _sha256(VISIBLE_PATH)
    assert task["source_execution_spec"]["sha256"] == _sha256(EXECUTION_PATH)
    semantic = task["hidden_source_report_semantic_evaluator"]
    assert semantic["candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert semantic["required_activation_record"] is True
    assert semantic["activation_record_path"] == ""
    assert semantic["activation_record_sha256"] == ""

    hidden_paths = [
        Path(task["hidden_source_replication_evaluator"]["harness_path"]),
        Path(semantic["reference_documents"][0]["path"]),
        Path(semantic["rubric_path"]),
        Path(semantic["calibration_cases_path"]),
        Path(semantic["candidate_mode_negative_cases_path"]),
    ]
    hidden_hashes = [
        task["hidden_source_replication_evaluator"]["harness_sha256"],
        semantic["reference_documents"][0]["sha256"],
        semantic["rubric_sha256"],
        semantic["calibration_cases_sha256"],
        semantic["candidate_mode_negative_cases_sha256"],
    ]
    assert [_sha256(path) for path in hidden_paths] == hidden_hashes

    runtime_visible = json.dumps(question, sort_keys=True)
    for hidden_name in (
        "sealed_gold_candidate.json",
        "hidden_source_replication_harness.py",
        "source_report_reference.md",
        "source_report_rubric.json",
        "candidate_mode_near_miss.md",
    ):
        assert hidden_name not in runtime_visible


def test_sealed_candidate_source_execution_reuses_exact_snapshot() -> None:
    snapshot = load_research_source_snapshot(SOURCE_ROOT / "source_manifest.json")
    execution = load_research_source_execution_spec(
        EXECUTION_PATH,
        research_sources=snapshot,
    )
    question = json.loads(VISIBLE_PATH.read_text(encoding="utf-8"))[
        "questions"
    ][0]

    assert execution.benchmark_id == BENCHMARK_ID
    assert execution.execution_id == (
        "betareg-jss-2010-gasoline-precision-"
        "source-execution-20260903-v1"
    )
    assert execution.manifest_sha256 == _sha256(EXECUTION_PATH)
    assert execution.source_snapshot_id == snapshot.snapshot_id
    assert execution.source_snapshot_hash == snapshot.snapshot_hash
    assert execution.source_manifest_sha256 == snapshot.manifest_sha256
    assert execution.entrypoint_document_id == "betareg-jss-official-r-example"
    assert execution.runtime_language == "r"
    assert execution.arguments == ()
    assert execution.result_artifact_paths == ("Rplots.pdf",)
    assert question["source"]["research_source_snapshot_hash"] == (
        snapshot.snapshot_hash
    )
    assert stable_hash(question) != stable_hash(
        _visible_question_hash_payload(question)
    )


def test_preactivation_ledger_exposes_only_identity_and_no_ladder_admission() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))

    assert ledger["task_id"] == TASK_ID
    assert ledger["benchmark_id"] == BENCHMARK_ID
    assert ledger["candidate_bundle_commit"] == (
        "b276777da6fe26705768db9ac9f2d5151eed5268"
    )
    assert ledger["status"] == (
        "sealed_pending_exact_haiku_semantic_qualification"
    )
    assert ledger["candidate_is_numbered_ladder_task"] is False
    assert ledger["candidate_is_active"] is False
    assert ledger["candidate_is_consumed"] is False
    assert ledger["preactivation_product_model_calls"] == 0
    assert ledger["preactivation_evaluator_model_calls"] == 0
    assert ledger["sealed_gold_candidate_sha256"] == _sha256(CANDIDATE_PATH)
    assert ledger["visible_questions_sha256"] == _sha256(VISIBLE_PATH)
    assert ledger["source_execution_spec_sha256"] == _sha256(EXECUTION_PATH)
    assert ledger["semantic_qualification"]["activation_record_present"] is False
    assert ledger["semantic_qualification"]["status"] == "NOT_QUALIFIED"
    assert not any(
        row.get("id") == TASK_ID for row in ladder["initial_candidate_queue"]
    )
    public_ledger = LEDGER_PATH.read_text(encoding="utf-8")
    assert "440.2783" not in public_ledger
    assert "577.7907" not in public_ledger


def test_hidden_source_harness_accepts_focused_reference_and_pdf_hash_drift() -> None:
    _, evaluate = _load_harness()
    first = evaluate(_candidate(), seed=20260903, replicates=1)
    second_candidate = _candidate()
    second_candidate["result_artifacts"][0]["sha256"] = "b" * 64
    second = evaluate(second_candidate, seed=20260903, replicates=1)

    required_true = {
        "artifact_kind_valid",
        "task_identity_valid",
        "execution_identity_valid",
        "source_identity_valid",
        "execution_clean",
        "runtime_identity_valid",
        "stdout_identity_valid",
        "gasoline_model_output_valid",
        "precision_values_valid",
        "artifact_contract_valid",
    }
    assert all(first[field] is True for field in required_true)
    assert all(second[field] is True for field in required_true)
    assert first["raw_pdf_hash_identity_required"] is False
    assert second["raw_pdf_hash_identity_required"] is False
    assert first["precision_before"] == pytest.approx(440.2783)
    assert first["precision_after_omitting_observation_4"] == pytest.approx(
        577.7907
    )


@pytest.mark.parametrize(
    ("metric", "mutate"),
    [
        ("artifact_kind_valid", lambda row, _: row.update(schema_version=2)),
        ("task_identity_valid", lambda row, _: row.update(question_id="wrong")),
        (
            "execution_identity_valid",
            lambda row, _: row.update(execution_id="wrong"),
        ),
        (
            "source_identity_valid",
            lambda row, _: row.update(source_snapshot_hash="wrong"),
        ),
        ("execution_clean", lambda row, _: row.update(returncode=1)),
        (
            "runtime_identity_valid",
            lambda row, _: row.update(runtime_version="R version wrong"),
        ),
        (
            "stdout_identity_valid",
            lambda row, _: row.update(stdout_sha256="0" * 64),
        ),
        (
            "gasoline_model_output_valid",
            lambda row, globals_: _replace_stdout(
                row,
                globals_,
                "mean model with logit link",
                "mean model with wrong link",
            ),
        ),
        (
            "precision_values_valid",
            lambda row, globals_: _replace_stdout(
                row,
                globals_,
                "577.7907",
                "300.0000",
            ),
        ),
        (
            "artifact_contract_valid",
            lambda row, _: row["result_artifacts"][0].update(size_bytes=0),
        ),
    ],
)
def test_hidden_source_harness_rejects_identity_and_result_mutations(
    metric: str,
    mutate,
) -> None:
    globals_, evaluate = _load_harness()
    candidate = deepcopy(_candidate())
    mutate(candidate, globals_)
    metrics = evaluate(candidate, seed=20260903, replicates=1)
    assert metrics[metric] is False


def _replace_stdout(
    candidate: dict,
    globals_: dict,
    old: str,
    new: str,
) -> None:
    candidate["raw_stdout"] = candidate["raw_stdout"].replace(old, new)
    candidate["stdout_sha256"] = _text_sha256(candidate["raw_stdout"])
    globals_["EXPECTED_STDOUT_SHA256"] = candidate["stdout_sha256"]


def test_semantic_controls_are_hash_bound_and_include_polished_near_miss() -> None:
    calibration_path = EVALUATOR_ROOT / "source_report_calibration_cases.json"
    negative_path = EVALUATOR_ROOT / "candidate_mode_negative_cases.json"
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    negatives = json.loads(negative_path.read_text(encoding="utf-8"))

    assert len(calibration["cases"]) == 6
    assert [row["expected_status"] for row in calibration["cases"]] == [
        "PASS",
        "FAIL",
        "FAIL",
        "FAIL",
        "FAIL",
        "FAIL",
    ]
    reference = calibration["cases"][0]["documents"][0]
    assert _sha256(Path(reference["source_path"])) == reference["sha256"]
    assert len(negatives["cases"]) == 1
    near_miss = negatives["cases"][0]["documents"][0]
    assert negatives["cases"][0]["expected_status"] == "FAIL"
    assert _sha256(Path(near_miss["source_path"])) == near_miss["sha256"]
    near_miss_text = Path(near_miss["source_path"]).read_text(encoding="utf-8")
    assert "440.2783" in near_miss_text
    assert "577.7907" in near_miss_text
    assert "was the cause" in near_miss_text
    assert "inspected only the artifact metadata" in near_miss_text

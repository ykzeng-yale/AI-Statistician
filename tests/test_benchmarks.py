import json
from pathlib import Path

from statlean_agent.benchmarks import SEED_BENCHMARKS, filter_by_split, load_benchmarks, seed_benchmarks
from statlean_agent.contracts import (
    BenchmarkSplit,
    BenchmarkTask,
    BenchmarkTaskType,
    LeanTask,
    ProofAttempt,
    VerificationReport,
    VerificationStatus,
)
from statlean_agent.serialization import dataclass_from_dict, dumps_json, read_jsonl
from statlean_agent.verifier import LakeVerifier, StaticVerifier, _process_diagnostics, render_task


EXPECTED_DOMAIN_COVERAGE = {
    "erm_consistency",
    "estimator_interface",
    "empirical_process",
    "asymptotic_bridge",
    "causal_bridge",
    "asymptotic_normality",
    "causal_identification",
}


def test_seed_benchmarks_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "seeds.jsonl"
    seed_benchmarks(path)
    loaded = load_benchmarks(path)
    assert len(loaded) == len(SEED_BENCHMARKS)
    assert all(isinstance(task, BenchmarkTask) for task in loaded)
    assert loaded[0].lean_task.task_id == loaded[0].task_id


def test_dataclass_round_trip_for_benchmark() -> None:
    task = SEED_BENCHMARKS[0]
    encoded = dumps_json(task)
    decoded = dataclass_from_dict(BenchmarkTask, __import__("json").loads(encoded))
    assert decoded == task


def test_filter_by_split() -> None:
    train = filter_by_split(SEED_BENCHMARKS, BenchmarkSplit.TRAIN)
    assert train
    assert all(task.split == BenchmarkSplit.TRAIN for task in train)


def test_seed_ids_are_unique_and_aligned() -> None:
    task_ids = [task.task_id for task in SEED_BENCHMARKS]
    assert len(task_ids) == len(set(task_ids))
    assert all(task.lean_task.task_id == task.task_id for task in SEED_BENCHMARKS)


def test_seed_benchmarks_cover_core_interfaces() -> None:
    domain_tags = {tag for task in SEED_BENCHMARKS for tag in task.domain_tags}
    task_types = {task.task_type for task in SEED_BENCHMARKS}
    splits = {task.split for task in SEED_BENCHMARKS}

    assert EXPECTED_DOMAIN_COVERAGE <= domain_tags
    assert BenchmarkTaskType.FORMAL_ONLY in task_types
    assert BenchmarkTaskType.SUBGOAL_COMPLETION in task_types
    assert {BenchmarkSplit.TRAIN, BenchmarkSplit.DEV, BenchmarkSplit.TEST} <= splits


def test_theorem_hole_tasks_are_explicit_and_policy_scoped() -> None:
    theorem_hole_tasks = [
        task for task in SEED_BENCHMARKS if task.task_type is BenchmarkTaskType.SUBGOAL_COMPLETION
    ]

    assert {task.task_id for task in theorem_hole_tasks} >= {
        "ipw_linearization_theorem_hole_seed",
        "aipw_product_rate_theorem_hole_seed",
        "if_normality_theorem_hole_seed",
    }
    assert all(task.lean_task.allowed_sorry for task in theorem_hole_tasks)
    assert all(task.proof_state for task in theorem_hole_tasks)
    assert all("theorem_hole" in task.domain_tags for task in theorem_hole_tasks)
    assert all(task.expected_premises for task in theorem_hole_tasks)


def test_checked_in_seeds_match_generated_registry(tmp_path: Path) -> None:
    generated = tmp_path / "seeds.jsonl"
    seed_benchmarks(generated)
    checked_in = Path("benchmarks/seeds.jsonl")
    assert generated.read_text(encoding="utf-8") == checked_in.read_text(encoding="utf-8")


def test_checked_in_verifier_artifacts_cover_current_seed_registry() -> None:
    reports = tuple(
        dataclass_from_dict(VerificationReport, record)
        for record in read_jsonl(Path("artifacts/verification/benchmark-seed-reports.jsonl"))
    )
    seed_ids = [task.task_id for task in SEED_BENCHMARKS]

    assert [report.task_id for report in reports] == seed_ids
    assert all(report.status is VerificationStatus.ACCEPTED for report in reports)

    reports_by_id = {report.task_id: report for report in reports}
    for task in SEED_BENCHMARKS:
        diagnostics = "\n".join(reports_by_id[task.task_id].diagnostics)
        if task.lean_task.allowed_sorry:
            assert "allowed placeholder `sorry`" in diagnostics
        else:
            assert "placeholder" not in diagnostics


def test_benchmark_schema_covers_seed_metadata() -> None:
    schema = json.loads(Path("schemas/benchmark_task.schema.json").read_text(encoding="utf-8"))
    records = read_jsonl(Path("benchmarks/seeds.jsonl"))
    properties = set(schema["properties"])

    assert schema["properties"]["difficulty"]["pattern"] == "^S[0-9]+$"
    assert schema["properties"]["domain_tags"]["minItems"] == 1
    assert schema["properties"]["lean_task"]["properties"]["dependencies"]["uniqueItems"] is True
    assert all(set(record) <= properties for record in records)


def test_render_task_has_import_and_namespace() -> None:
    source = render_task(SEED_BENCHMARKS[0].lean_task)
    assert "import StatInference.Asymptotics.Basic" in source
    assert "namespace StatInference.Benchmarks" in source
    assert "end StatInference.Benchmarks" in source


def test_static_verifier_rejects_forbidden_token() -> None:
    task = SEED_BENCHMARKS[0]
    report = StaticVerifier().check(
        ProofAttempt(
            task_id=task.task_id,
            agent_key="test",
            lean_code="theorem bad : True := by sorry",
        )
    )
    assert report.status.value == "rejected"
    assert "line 1" in report.first_error


def test_static_verifier_allows_configured_sorry_but_not_admit() -> None:
    sorry_report = StaticVerifier(allowed_placeholders=("sorry",)).check(
        ProofAttempt(
            task_id="draft",
            agent_key="test",
            lean_code="theorem draft : True := by\n  sorry",
        )
    )
    admit_report = StaticVerifier(allowed_placeholders=("sorry",)).check(
        ProofAttempt(
            task_id="bad",
            agent_key="test",
            lean_code="theorem bad : True := by\n  admit",
        )
    )

    assert sorry_report.status.value == "accepted"
    assert "allowed placeholder `sorry`" in sorry_report.diagnostics[0]
    assert admit_report.status.value == "rejected"
    assert "forbidden token `admit`" in admit_report.diagnostics[0]


def test_lake_verifier_uses_task_allowed_sorry_for_static_gate(tmp_path: Path) -> None:
    task = LeanTask(
        task_id="draft",
        imports=(),
        namespace="",
        statement="theorem draft : True := by\n  sorry",
        allowed_sorry=True,
    )

    report = LakeVerifier(tmp_path, timeout_seconds=1).verify_task(task)

    assert report.status.value in {"accepted", "rejected", "error", "timeout"}
    assert any("allowed placeholder `sorry`" in diagnostic for diagnostic in report.diagnostics)


def test_lake_verifier_reports_missing_lake(tmp_path: Path) -> None:
    task = SEED_BENCHMARKS[0].lean_task
    report = LakeVerifier(tmp_path, timeout_seconds=1).verify_task(task)
    assert report.status.value in {"accepted", "rejected", "error", "timeout"}
    if report.status.value == "error":
        assert "lake executable not found" in report.diagnostics


def test_verifier_diagnostics_sanitize_temporary_source_path(tmp_path: Path) -> None:
    source_path = tmp_path / "Task.lean"
    diagnostics = _process_diagnostics(
        f"{source_path}:6:8: error: Unknown identifier `missing`",
        "",
        source_path,
    )

    assert diagnostics == ("Task.lean:6:8: error: Unknown identifier `missing`",)

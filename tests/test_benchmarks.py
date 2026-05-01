from pathlib import Path

from statlean_agent.benchmarks import SEED_BENCHMARKS, filter_by_split, load_benchmarks, seed_benchmarks
from statlean_agent.contracts import BenchmarkSplit, BenchmarkTask, ProofAttempt
from statlean_agent.serialization import dataclass_from_dict, dumps_json
from statlean_agent.verifier import LakeVerifier, StaticVerifier, render_task


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


def test_lake_verifier_reports_missing_lake(tmp_path: Path) -> None:
    task = SEED_BENCHMARKS[0].lean_task
    report = LakeVerifier(tmp_path, timeout_seconds=1).verify_task(task)
    assert report.status.value in {"accepted", "rejected", "error", "timeout"}
    if report.status.value == "error":
        assert "lake executable not found" in report.diagnostics

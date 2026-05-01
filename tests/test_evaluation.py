import json
from pathlib import Path

from statlean_agent.benchmarks import SEED_BENCHMARKS
from statlean_agent.cli import main
from statlean_agent.contracts import (
    BenchmarkSplit,
    BenchmarkTask,
    BenchmarkTaskType,
    LeanTask,
    ProofAttempt,
    VerificationReport,
    VerificationStatus,
)
from statlean_agent.evaluation import evaluate_attempts, summarize_benchmark_attempts
from statlean_agent.serialization import dataclass_from_dict, read_jsonl, write_jsonl


def test_evaluate_attempts() -> None:
    attempts = (
        ProofAttempt("a", "agent", "theorem ok : True := by trivial"),
        ProofAttempt("b", "agent", "theorem bad : True := by sorry"),
    )
    reports = (
        VerificationReport("a", VerificationStatus.ACCEPTED),
        VerificationReport("b", VerificationStatus.REJECTED),
    )
    report = evaluate_attempts(attempts, reports)
    assert report.total_attempts == 2
    assert report.accepted == 1
    assert report.rejected == 1
    assert report.pass_rate == 0.5
    assert report.status_counts == {"accepted": 1, "rejected": 1, "timeout": 0, "error": 0}
    assert report.reward_totals["proof_complete"] == 10.0
    assert report.reward_totals["forbidden_sorry"] == -10.0


def test_evaluate_attempts_normalizes_statuses_and_aggregates_rewards() -> None:
    attempts = (
        ProofAttempt("a", "agent", "theorem ok : True := by trivial", premises_used=("True.intro",)),
        ProofAttempt("b", "agent", "theorem slow : True := by trivial"),
        ProofAttempt("c", "agent", "theorem broken : True := by trivial"),
    )
    reports = (
        VerificationReport("a", "ACCEPTED", locally_valid_steps=2, closed_goals=1),
        VerificationReport("b", "timeout"),
        VerificationReport("c", "not-a-status"),
    )

    report = evaluate_attempts(attempts, reports)

    assert report.status_counts == {"accepted": 1, "rejected": 0, "timeout": 1, "error": 1}
    assert report.accepted == 1
    assert report.timeout == 1
    assert report.error == 1
    assert report.reward_totals["locally_valid_steps"] == 0.5
    assert report.reward_totals["closed_goals"] == 0.75
    assert report.reward_totals["premises_used"] == 0.1
    assert report.average_reward_components["proof_complete"] == 10.0 / 3
    assert any("unknown verification status" in diagnostic for diagnostic in report.diagnostics)


def test_evaluate_attempts_overrides_accepted_for_forbidden_placeholder() -> None:
    attempts = (
        ProofAttempt("bad", "agent", "theorem bad : True := by\n  sorry"),
    )
    reports = (
        VerificationReport("bad", VerificationStatus.ACCEPTED),
    )

    report = evaluate_attempts(attempts, reports)

    assert report.accepted == 0
    assert report.rejected == 1
    assert report.pass_rate == 0.0
    assert report.reward_totals["forbidden_sorry"] == -10.0
    assert any("overridden to rejected" in diagnostic for diagnostic in report.diagnostics)


def test_evaluate_attempts_allows_configured_placeholder_only() -> None:
    attempts = (
        ProofAttempt("draft", "agent", "theorem draft : True := by\n  sorry"),
        ProofAttempt("bad", "agent", "theorem bad : True := by\n  admit"),
    )
    reports = (
        VerificationReport("draft", VerificationStatus.ACCEPTED),
        VerificationReport("bad", VerificationStatus.ACCEPTED),
    )

    report = evaluate_attempts(
        attempts,
        reports,
        allowed_placeholders_by_task={"draft": ("sorry",), "bad": ("sorry",)},
    )

    assert report.accepted == 1
    assert report.rejected == 1
    assert "forbidden_sorry" not in report.reward_totals
    assert report.reward_totals["forbidden_admit"] == -10.0
    assert any("draft: allowed placeholder `sorry`" in diagnostic for diagnostic in report.diagnostics)
    assert any("bad: forbidden token `admit`" in diagnostic for diagnostic in report.diagnostics)


def test_summarize_benchmark_attempts_by_metadata() -> None:
    tasks = (
        _benchmark_task(
            "accepted",
            split=BenchmarkSplit.TRAIN,
            task_type=BenchmarkTaskType.FORMAL_ONLY,
            domain_tags=("alpha", "beta"),
        ),
        _benchmark_task(
            "unsolved",
            split=BenchmarkSplit.TRAIN,
            task_type=BenchmarkTaskType.REPAIR,
            domain_tags=("alpha",),
        ),
        _benchmark_task(
            "unknown",
            split=BenchmarkSplit.DEV,
            task_type=BenchmarkTaskType.FORMALIZATION,
            domain_tags=("beta",),
        ),
    )
    attempts = (
        ProofAttempt("accepted", "agent", "theorem ok : True := by trivial"),
        ProofAttempt("unsolved", "agent", "theorem stuck : True := by exact True.intro"),
        ProofAttempt("unknown", "agent", "theorem missing : True := by exact missing_decl"),
    )
    reports = (
        VerificationReport("accepted", VerificationStatus.ACCEPTED),
        VerificationReport("unsolved", VerificationStatus.REJECTED, first_error="unsolved goals"),
        VerificationReport("unknown", VerificationStatus.ERROR, first_error="unknown declaration missing_decl"),
    )

    summary = summarize_benchmark_attempts(tasks, attempts, reports)

    assert summary["total"] == {
        "attempts": 3,
        "passed": 1,
        "failed": 2,
        "mean_reward": 7.0 / 3.0,
        "failure_categories": {"unknown_declaration": 1, "unsolved_goals": 1},
    }
    assert summary["by_phase"] == [
        {
            "attempts": 3,
            "failed": 2,
            "failure_categories": {"unknown_declaration": 1, "unsolved_goals": 1},
            "mean_reward": 7.0 / 3.0,
            "passed": 1,
            "phase": "unmapped",
        }
    ]
    assert [row["split"] for row in summary["by_split"]] == ["dev", "train"]
    by_split = {row["split"]: row for row in summary["by_split"]}
    assert by_split["train"]["passed"] == 1
    assert by_split["train"]["failed"] == 1
    assert by_split["train"]["mean_reward"] == 4.25
    assert by_split["train"]["failure_categories"] == {"unsolved_goals": 1}
    assert by_split["dev"]["failure_categories"] == {"unknown_declaration": 1}

    assert [row["domain"] for row in summary["by_domain"]] == ["alpha", "beta"]
    by_domain = {row["domain"]: row for row in summary["by_domain"]}
    assert by_domain["alpha"]["attempts"] == 2
    assert by_domain["beta"]["attempts"] == 2
    assert by_domain["alpha"]["mean_reward"] == 4.25
    assert by_domain["beta"]["mean_reward"] == 4.25

    assert [row["task_type"] for row in summary["by_task_type"]] == [
        "formal_only",
        "formalization",
        "repair",
    ]


def test_summarize_benchmark_attempts_categorizes_policy_violation() -> None:
    tasks = (_benchmark_task("draft", domain_tags=("alpha",)),)
    attempts = (ProofAttempt("draft", "agent", "theorem draft : True := by\n  sorry"),)
    reports = (VerificationReport("draft", VerificationStatus.ACCEPTED),)

    summary = summarize_benchmark_attempts(tasks, attempts, reports)

    assert summary["total"]["passed"] == 0
    assert summary["total"]["failed"] == 1
    assert summary["total"]["mean_reward"] == -11.5
    assert summary["total"]["failure_categories"] == {"policy_violation": 1}

    allowed_summary = summarize_benchmark_attempts(
        (_benchmark_task("draft", domain_tags=("alpha",), allowed_sorry=True),),
        attempts,
        reports,
    )
    assert allowed_summary["total"]["passed"] == 1
    assert allowed_summary["total"]["failure_categories"] == {}


def test_cli_eval_summary(tmp_path: Path, capsys) -> None:
    benchmarks_path = tmp_path / "benchmarks.jsonl"
    attempts_path = tmp_path / "attempts.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    summary_path = tmp_path / "summary.json"
    write_jsonl(benchmarks_path, [_benchmark_task("task", domain_tags=("alpha",))])
    write_jsonl(attempts_path, [ProofAttempt("task", "agent", "theorem ok : True := by trivial")])
    write_jsonl(reports_path, [VerificationReport("task", VerificationStatus.ACCEPTED)])

    assert (
        main(
            [
                "eval-summary",
                "--benchmarks",
                str(benchmarks_path),
                "--attempts",
                str(attempts_path),
                "--reports",
                str(reports_path),
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["total"]["passed"] == 1
    assert summary["by_phase"][0]["phase"] == "unmapped"
    assert summary["by_domain"] == [
        {
            "attempts": 1,
            "domain": "alpha",
            "failed": 0,
            "failure_categories": {},
            "mean_reward": 10.0,
            "passed": 1,
        }
    ]

    assert (
        main(
            [
                "eval-summary",
                "--benchmarks",
                str(benchmarks_path),
                "--attempts",
                str(attempts_path),
                "--reports",
                str(reports_path),
                "--output",
                str(summary_path),
            ]
        )
        == 0
    )
    assert "wrote" in capsys.readouterr().out
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary


def test_checked_in_eval_artifacts_cover_current_seed_registry() -> None:
    attempts = tuple(
        dataclass_from_dict(ProofAttempt, record)
        for record in read_jsonl(Path("artifacts/evaluation/benchmark-seed-attempts.jsonl"))
    )
    reports = tuple(
        dataclass_from_dict(VerificationReport, record)
        for record in read_jsonl(Path("artifacts/verification/benchmark-seed-reports.jsonl"))
    )
    summary = json.loads(Path("artifacts/evaluation/benchmark-seed-summary.json").read_text(encoding="utf-8"))
    seed_ids = [task.task_id for task in SEED_BENCHMARKS]

    assert [attempt.task_id for attempt in attempts] == seed_ids
    assert [report.task_id for report in reports] == seed_ids
    assert summary["total"]["attempts"] == len(seed_ids)
    assert summary["total"]["passed"] == len(seed_ids)
    assert summary["total"]["failed"] == 0

    by_phase = {row["phase"]: row for row in summary["by_phase"]}
    assert {"P1", "P2", "P3", "P4", "P5"} <= set(by_phase)
    assert all(row["failed"] == 0 for row in by_phase.values())
    assert by_phase["P5"]["attempts"] == 3

    by_task_type = {row["task_type"]: row for row in summary["by_task_type"]}
    assert by_task_type["subgoal_completion"]["attempts"] == 3
    assert by_task_type["subgoal_completion"]["passed"] == 3


def _benchmark_task(
    task_id: str,
    *,
    split: BenchmarkSplit = BenchmarkSplit.DEV,
    task_type: BenchmarkTaskType = BenchmarkTaskType.FORMAL_ONLY,
    domain_tags: tuple[str, ...] = ("domain",),
    allowed_sorry: bool = False,
) -> BenchmarkTask:
    return BenchmarkTask(
        task_id=task_id,
        task_type=task_type,
        split=split,
        difficulty="S1",
        domain_tags=domain_tags,
        lean_task=LeanTask(
            task_id=task_id,
            imports=(),
            namespace="StatInference.Benchmarks",
            statement="example : True := by\n  trivial",
            allowed_sorry=allowed_sorry,
        ),
    )

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
from statlean_agent.evaluation import (
    build_ablation_report,
    build_concrete_estimator_chain_report,
    build_empirical_process_expansion_targets,
    build_empirical_process_external_prover_slice,
    build_external_baseline_plan,
    build_external_baseline_results,
    build_paper_quality_heldout_report,
    build_reproducibility_bundle,
    build_vdvw_theorem_inventory,
    compare_baseline_on_split,
    evaluate_attempts,
    summarize_benchmark_attempts,
)
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


def test_compare_baseline_on_split_records_heldout_rows() -> None:
    tasks = (
        _benchmark_task(
            "train-task",
            split=BenchmarkSplit.TRAIN,
            domain_tags=("asymptotic_calculus",),
        ),
        _benchmark_task(
            "test-task",
            split=BenchmarkSplit.TEST,
            domain_tags=("empirical_process",),
        ),
    )
    attempts = (
        ProofAttempt("train-task", "seed-registry", "theorem train : True := by trivial"),
        ProofAttempt(
            "test-task",
            "seed-registry",
            "theorem test : True := by trivial",
            premises_used=("StatInference.seed",),
        ),
    )
    reports = (
        VerificationReport("train-task", VerificationStatus.ACCEPTED),
        VerificationReport("test-task", VerificationStatus.ACCEPTED, locally_valid_steps=1),
    )

    comparison = compare_baseline_on_split(
        tasks,
        attempts,
        reports,
        baseline="seed-registry",
        split="test",
    )

    assert comparison["comparison_id"] == "seed-registry::test"
    assert comparison["benchmark_task_count"] == 1
    assert comparison["passed"] == 1
    assert comparison["failed"] == 0
    assert comparison["pass_rate"] == 1.0
    assert comparison["status_counts"]["accepted"] == 1
    assert comparison["rows"][0]["task_id"] == "test-task"
    assert comparison["rows"][0]["split"] == "test"
    assert comparison["rows"][0]["effective_status"] == "accepted"


def test_build_paper_quality_heldout_report_includes_failure_taxonomy_and_chains() -> None:
    test_task = _benchmark_task("test-task", split=BenchmarkSplit.TEST, domain_tags=("empirical_process",))
    chain_task = _benchmark_task("chain-task", split=BenchmarkSplit.DEV, domain_tags=("ipw",))
    tasks = (test_task, chain_task)
    attempts = (
        ProofAttempt("test-task", "seed-registry", "theorem test : True := by trivial"),
        ProofAttempt("chain-task", "seed-registry", "theorem chain : True := by trivial"),
    )
    reports = (
        VerificationReport("test-task", VerificationStatus.ACCEPTED),
        VerificationReport("chain-task", VerificationStatus.ACCEPTED),
    )

    report = build_paper_quality_heldout_report(
        tasks,
        attempts,
        reports,
        baseline="seed-registry",
        split="test",
        proof_chains=(
            {
                "chain_id": "unit_chain",
                "name": "Unit chain",
                "source_module": "StatInference.Unit",
                "benchmark_task_ids": ("chain-task",),
                "required_declarations": ("StatInference.Unit.ok",),
            },
        ),
    )

    assert report["report_id"] == "paper-quality::seed-registry::test"
    assert report["heldout_task_count"] == 1
    assert report["heldout_pass_rate"] == 1.0
    assert report["failure_taxonomy"]["failed"] == 0
    assert report["failure_taxonomy"]["failure_categories"] == {}
    assert report["non_seed_chain_count"] == 1
    assert report["non_seed_chain_passed"] == 1
    assert report["non_seed_proof_chains"][0]["status"] == "passed"
    assert report["non_seed_proof_chains"][0]["required_declarations"] == ["StatInference.Unit.ok"]


def test_build_concrete_estimator_chain_report_requires_verified_components() -> None:
    tasks = (
        _benchmark_task(
            "paper_quality_ipw_hajek_concrete_chain_seed",
            domain_tags=("ipw", "paper_quality"),
        ),
        _benchmark_task("ipw_identification_certificate_seed", domain_tags=("ipw",)),
        _benchmark_task("ipw_hajek_scaled_linearization_route_seed", domain_tags=("ipw",)),
        _benchmark_task("constant_ipw_hajek_route_seed", domain_tags=("ipw",)),
        _benchmark_task("constant_ipw_hajek_exact_target_seed", domain_tags=("ipw",)),
    )
    reports = tuple(VerificationReport(task.task_id, VerificationStatus.ACCEPTED) for task in tasks)

    report = build_concrete_estimator_chain_report(tasks, reports)

    assert report["report_id"] == "concrete-estimator-chain::ipw_hajek"
    assert report["benchmark_task_id"] == "paper_quality_ipw_hajek_concrete_chain_seed"
    assert report["theorem"] == "StatInference.paperQualityIPWHajekConcreteEstimatorChain"
    assert report["passed"] is True
    assert report["no_placeholder_policy"] is True
    assert report["component_passed"] == 4
    assert all(component["status"] == "passed" for component in report["proof_components"])


def test_build_ablation_report_records_component_evidence() -> None:
    tasks = (_benchmark_task("task", split=BenchmarkSplit.TEST),)

    report = build_ablation_report(
        tasks,
        {
            "baseline": "seed-registry",
            "heldout_pass_rate": 1.0,
            "baseline_comparison": {"mean_premise_recall": 1.0},
        },
        {"passed": True},
        {
            "sft_examples": [{"example_id": "sft::task"}],
            "dpo_pairs": [{"pair_id": "dpo::task"}],
            "grpo_tasks": [{"task_id": "task"}],
        },
        (
            {
                "task_id": "task",
                "reward_components": ["proof_complete", "locally_valid_steps"],
            },
        ),
        ({"task_id": "task", "status": "rejected"},),
        ({"proposal_id": "p", "passed": True},),
        ({"proposal_id": "p", "passed": True},),
        ({"proposal_id": "p", "passed": True},),
        ({"ledger_id": "l", "status": "blocked_placeholder"},),
    )

    assert report["report_id"] == "ablation::p8"
    assert report["full_system_ready"] is True
    assert [component["component"] for component in report["components"]] == [
        "retrieval",
        "sft",
        "dpo",
        "process_reward",
        "curation",
    ]
    assert {row["variant"] for row in report["ablation_rows"]} == {
        "full_system",
        "no_retrieval",
        "no_sft",
        "no_dpo",
        "no_process_reward",
        "no_curation",
    }
    assert report["evidence_summary"]["mean_premise_recall"] == 1.0
    assert report["evidence_summary"]["sft_example_count"] == 1
    assert report["evidence_summary"]["dpo_pair_count"] == 1
    assert report["evidence_summary"]["dpo_rejected_report_count"] == 1
    assert report["evidence_summary"]["grpo_process_task_count"] == 1
    assert report["evidence_summary"]["curation_gate_passed"] == 3
    assert report["evidence_summary"]["blocked_placeholder_ledger_entries"] == 1


def test_build_reproducibility_bundle_records_artifact_hashes(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    paper = tmp_path / "paper.md"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    paper.write_text("# Paper\n", encoding="utf-8")

    bundle = build_reproducibility_bundle(
        tmp_path,
        {
            "blueprint_id": "bp",
            "title": "Blueprint",
            "phase_count": 1,
            "done_phase_count": 1,
            "current_phase": {"id": "P8", "status": "done"},
            "current_milestone": None,
        },
        artifact_paths=("artifact.json", "paper.md"),
        paper_draft_path="paper.md",
    )

    assert bundle["report_id"] == "reproducibility::p8"
    assert bundle["all_phases_done"] is True
    assert bundle["artifact_count"] == 2
    assert [record["path"] for record in bundle["artifacts"]] == ["artifact.json", "paper.md"]
    assert all(len(record["sha256"]) == 64 for record in bundle["artifacts"])
    assert bundle["paper_draft_path"] == "paper.md"
    assert any(command["name"] == "lean_build" for command in bundle["validation_commands"])


def test_build_external_baseline_plan_records_blocked_model_runs() -> None:
    tasks = (
        _benchmark_task("train-task", split=BenchmarkSplit.TRAIN, domain_tags=("train_domain",)),
        _benchmark_task("test-task", split=BenchmarkSplit.TEST, domain_tags=("test_domain",)),
        _benchmark_task(
            "hole-task",
            split=BenchmarkSplit.DEV,
            task_type=BenchmarkTaskType.SUBGOAL_COMPLETION,
            domain_tags=("theorem_hole",),
            allowed_sorry=True,
        ),
    )

    plan = build_external_baseline_plan(tasks, split="test")

    assert plan["report_id"] == "external-baseline-plan::test"
    assert plan["benchmark_task_count"] == 3
    assert plan["target_task_count"] == 1
    assert plan["target_task_ids"] == ["test-task"]
    assert plan["theorem_hole_task_count"] == 1
    assert plan["ready_baseline_count"] == 1
    assert plan["blocked_baseline_count"] == plan["baseline_count"] - 1
    assert plan["baselines"][0]["baseline_id"] == "seed-registry"
    assert plan["baselines"][0]["status"] == "ready"
    assert all(row["target_task_count"] == 1 for row in plan["baselines"])
    assert "pass_at_32" in plan["metrics"]


def test_build_external_baseline_results_ingests_seed_and_blocks_missing_models() -> None:
    tasks = (
        _benchmark_task("test-task", split=BenchmarkSplit.TEST, domain_tags=("test_domain",)),
    )
    plan = build_external_baseline_plan(tasks, split="test")
    attempts = (
        ProofAttempt(
            "test-task",
            "seed-registry",
            "theorem test : True := by trivial",
            premises_used=("StatInference.seed",),
        ),
    )
    reports = (
        VerificationReport("test-task", VerificationStatus.ACCEPTED, locally_valid_steps=1),
    )

    results = build_external_baseline_results(
        tasks,
        plan,
        {"seed-registry": attempts},
        {"seed-registry": reports},
        source_by_baseline={"seed-registry": "unit_fallback"},
    )

    assert results["report_id"] == "external-baseline-results::test"
    assert results["baseline_count"] == 5
    assert results["ingested_count"] == 1
    assert results["blocked_count"] == 4
    assert results["best_available_baseline"] == "seed-registry"
    seed_row = results["rows"][0]
    assert seed_row["ingestion_status"] == "ingested"
    assert seed_row["source"] == "unit_fallback"
    assert seed_row["pass_rate"] == 1.0
    assert {row["ingestion_status"] for row in results["rows"][1:]} == {"blocked_by_plan_status"}
    assert all(row["blocked_reasons"] for row in results["rows"][1:])


def test_build_empirical_process_expansion_targets_scopes_next_interfaces() -> None:
    tasks = (
        _benchmark_task(
            "gc-task",
            split=BenchmarkSplit.TEST,
            domain_tags=("empirical_process", "glivenko_cantelli"),
        ),
        _benchmark_task(
            "donsker-task",
            split=BenchmarkSplit.DEV,
            domain_tags=("empirical_process", "donsker"),
        ),
        _benchmark_task(
            "rademacher-task",
            split=BenchmarkSplit.DEV,
            domain_tags=("rademacher_complexity",),
        ),
        _benchmark_task(
            "vc-task",
            split=BenchmarkSplit.DEV,
            domain_tags=("vc_subgraph",),
        ),
    )

    report = build_empirical_process_expansion_targets(tasks)

    assert report["report_id"] == "empirical-process-targets::p9"
    assert report["target_count"] == 5
    assert report["scoped_count"] == 5
    assert report["pending_count"] == 0
    targets = {row["target_id"]: row for row in report["targets"]}
    assert {
        "bracketing_gc_interface",
        "vc_subgraph_gc_interface",
        "donsker_bridge_interface",
        "covering_number_gc_interface",
        "rademacher_gc_interface",
    } == set(targets)
    assert "StatInference.BracketingDeviationCertificate" in targets[
        "bracketing_gc_interface"
    ]["lean_declarations"]
    assert "donsker-task" in targets["donsker_bridge_interface"]["motivating_task_ids"]
    assert targets["bracketing_gc_interface"]["gate_status"] == "needs_benchmark_seed"
    assert targets["vc_subgraph_gc_interface"]["gate_status"] == "ready_for_lemma_targets"
    assert targets["donsker_bridge_interface"]["gate_status"] == "ready_for_lemma_targets"
    assert targets["rademacher_gc_interface"]["gate_status"] == "ready_for_lemma_targets"
    assert any("proof-carrying" in gate for gate in report["acceptance_gates"])


def test_build_empirical_process_external_prover_slice_targets_family_tasks() -> None:
    tasks = (
        _benchmark_task(
            "bracketing-task",
            split=BenchmarkSplit.DEV,
            domain_tags=("empirical_process", "bracketing_number"),
        ),
        _benchmark_task(
            "vc-task",
            split=BenchmarkSplit.DEV,
            domain_tags=("empirical_process", "vc_subgraph"),
        ),
        _benchmark_task(
            "donsker-task",
            split=BenchmarkSplit.TEST,
            domain_tags=("empirical_process", "donsker"),
        ),
        _benchmark_task(
            "other-task",
            split=BenchmarkSplit.TEST,
            domain_tags=("empirical_process", "covering_number"),
        ),
    )
    target_report = {
        "report_id": "targets",
        "targets": (
            {
                "target_id": "bracketing",
                "interface_family": "bracketing",
                "gate_status": "ready_for_lemma_targets",
                "family_benchmark_task_ids": ("bracketing-task",),
            },
            {
                "target_id": "vc",
                "interface_family": "vc_subgraph",
                "gate_status": "ready_for_lemma_targets",
                "family_benchmark_task_ids": ("vc-task",),
            },
            {
                "target_id": "donsker",
                "interface_family": "donsker",
                "gate_status": "ready_for_lemma_targets",
                "family_benchmark_task_ids": ("donsker-task",),
            },
        ),
    }
    attempts = tuple(
        ProofAttempt(task.task_id, "seed-registry", "theorem ok : True := by trivial")
        for task in tasks
    )
    reports = tuple(VerificationReport(task.task_id, VerificationStatus.ACCEPTED) for task in tasks)

    report = build_empirical_process_external_prover_slice(
        tasks,
        target_report,
        {"seed-registry": attempts},
        {"seed-registry": reports},
        source_by_baseline={"seed-registry": "unit_seed"},
    )

    assert report["report_id"] == "empirical-process-external-prover-slice::p10"
    assert report["target_report_id"] == "targets"
    assert report["interface_families"] == ["bracketing", "vc_subgraph", "donsker"]
    assert report["target_task_ids"] == ["bracketing-task", "vc-task", "donsker-task"]
    assert report["target_task_count"] == 3
    assert report["family_count"] == 3
    assert all(family["seed_registry_status"] == "verified" for family in report["families"])
    assert report["ingested_count"] == 1
    assert report["blocked_count"] == 4
    seed_row = report["rows"][0]
    assert seed_row["baseline_id"] == "seed-registry"
    assert seed_row["source"] == "unit_seed"
    assert seed_row["evaluated_task_count"] == 3
    assert seed_row["pass_rate"] == 1.0
    assert {row["ingestion_status"] for row in report["rows"][1:]} == {"blocked_by_plan_status"}


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


def test_cli_baseline_comparison(tmp_path: Path, capsys) -> None:
    benchmarks_path = tmp_path / "benchmarks.jsonl"
    attempts_path = tmp_path / "attempts.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    comparison_path = tmp_path / "comparison.json"
    write_jsonl(
        benchmarks_path,
        [_benchmark_task("task", split=BenchmarkSplit.TEST, domain_tags=("alpha",))],
    )
    write_jsonl(attempts_path, [ProofAttempt("task", "seed-registry", "theorem ok : True := by trivial")])
    write_jsonl(reports_path, [VerificationReport("task", VerificationStatus.ACCEPTED)])

    assert (
        main(
            [
                "baseline-comparison",
                "--benchmarks",
                str(benchmarks_path),
                "--attempts",
                str(attempts_path),
                "--reports",
                str(reports_path),
                "--split",
                "test",
            ]
        )
        == 0
    )
    comparison = json.loads(capsys.readouterr().out)
    assert comparison["baseline"] == "seed-registry"
    assert comparison["benchmark_task_count"] == 1
    assert comparison["passed"] == 1

    assert (
        main(
            [
                "baseline-comparison",
                "--benchmarks",
                str(benchmarks_path),
                "--attempts",
                str(attempts_path),
                "--reports",
                str(reports_path),
                "--split",
                "test",
                "--output",
                str(comparison_path),
            ]
        )
        == 0
    )
    assert "wrote" in capsys.readouterr().out
    assert json.loads(comparison_path.read_text(encoding="utf-8")) == comparison


def test_cli_paper_quality_heldout(tmp_path: Path, capsys) -> None:
    benchmarks_path = tmp_path / "benchmarks.jsonl"
    attempts_path = tmp_path / "attempts.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    output_path = tmp_path / "paper-heldout.json"
    main(["seed-benchmarks", "--output", str(benchmarks_path)])
    main(
        [
            "materialize-benchmark-attempts",
            "--benchmarks",
            str(benchmarks_path),
            "--output",
            str(attempts_path),
        ]
    )
    reports = [
        VerificationReport(record["task_id"], VerificationStatus.ACCEPTED)
        for record in read_jsonl(benchmarks_path)
    ]
    write_jsonl(reports_path, reports)

    assert (
        main(
            [
                "paper-quality-heldout",
                "--benchmarks",
                str(benchmarks_path),
                "--attempts",
                str(attempts_path),
                "--reports",
                str(reports_path),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert "heldout_tasks=2" in output
    assert "non_seed_chains=3/3" in output
    assert report["heldout_task_count"] == 2
    assert report["non_seed_chain_pass_rate"] == 1.0


def test_cli_concrete_estimator_chain_report(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    output_path = tmp_path / "concrete-chain.json"
    main(["seed-benchmarks", "--output", str(benchmark_path)])
    reports = [
        VerificationReport(record["task_id"], VerificationStatus.ACCEPTED)
        for record in read_jsonl(benchmark_path)
    ]
    write_jsonl(reports_path, reports)

    assert (
        main(
            [
                "concrete-estimator-chain-report",
                "--benchmarks",
                str(benchmark_path),
                "--reports",
                str(reports_path),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert "passed=True" in output
    assert "components=4/4" in output
    assert report["passed"] is True
    assert report["benchmark_task_id"] == "paper_quality_ipw_hajek_concrete_chain_seed"


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


def test_checked_in_heldout_baseline_artifact() -> None:
    comparison = json.loads(Path("artifacts/evaluation/heldout-baseline.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/baseline_comparison.schema.json").read_text(encoding="utf-8"))
    test_ids = [task.task_id for task in SEED_BENCHMARKS if task.split is BenchmarkSplit.TEST]

    assert comparison["baseline"] == "seed-registry"
    assert comparison["split"] == "test"
    assert comparison["task_ids"] == test_ids
    assert comparison["benchmark_task_count"] == len(test_ids)
    assert comparison["passed"] == len(test_ids)
    assert comparison["failed"] == 0
    assert comparison["pass_rate"] == 1.0
    assert comparison["status_counts"] == {
        "accepted": len(test_ids),
        "rejected": 0,
        "timeout": 0,
        "error": 0,
    }
    assert all(row["effective_status"] == "accepted" for row in comparison["rows"])
    assert all(row["agent_key"] == "seed-registry" for row in comparison["rows"])
    assert all(row["premise_recall"] == 1.0 for row in comparison["rows"])
    assert set(comparison) <= set(schema["properties"])


def test_checked_in_paper_quality_heldout_artifact() -> None:
    report = json.loads(Path("artifacts/evaluation/paper-quality-heldout.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/paper_quality_heldout.schema.json").read_text(encoding="utf-8"))
    test_ids = [task.task_id for task in SEED_BENCHMARKS if task.split is BenchmarkSplit.TEST]

    assert report["report_id"] == "paper-quality::seed-registry::test"
    assert report["baseline"] == "seed-registry"
    assert report["split"] == "test"
    assert report["heldout_task_count"] == len(test_ids)
    assert report["heldout_pass_rate"] == 1.0
    assert report["failure_taxonomy"]["failed"] == 0
    assert report["failure_taxonomy"]["failure_categories"] == {}
    assert report["baseline_comparison"]["task_ids"] == test_ids
    assert report["non_seed_chain_count"] == 3
    assert report["non_seed_chain_passed"] == 3
    assert report["non_seed_chain_pass_rate"] == 1.0
    assert all(chain["status"] == "passed" for chain in report["non_seed_proof_chains"])
    assert all(chain["required_declarations"] for chain in report["non_seed_proof_chains"])
    assert set(report) <= set(schema["properties"])


def test_checked_in_concrete_estimator_chain_artifact() -> None:
    report = json.loads(Path("artifacts/evaluation/concrete-estimator-chain.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/concrete_estimator_chain.schema.json").read_text(encoding="utf-8"))

    assert report["report_id"] == "concrete-estimator-chain::ipw_hajek"
    assert report["benchmark_task_id"] == "paper_quality_ipw_hajek_concrete_chain_seed"
    assert report["theorem"] == "StatInference.paperQualityIPWHajekConcreteEstimatorChain"
    assert report["module"] == "StatInference.Examples.ConcreteEstimatorChain"
    assert report["verification_status"] == "accepted"
    assert report["passed"] is True
    assert report["no_placeholder_policy"] is True
    assert report["component_count"] == 4
    assert report["component_passed"] == 4
    assert all(component["status"] == "passed" for component in report["proof_components"])
    assert "StatInference.paperQualityIPWHajekConcreteEstimatorChain" in report["route_declarations"]
    assert len(report["claims_verified"]) == 4
    assert set(report) <= set(schema["properties"])


def test_checked_in_ablation_report_artifact() -> None:
    report = json.loads(Path("artifacts/evaluation/ablation-report.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/ablation_report.schema.json").read_text(encoding="utf-8"))
    placeholder_count = sum(1 for task in SEED_BENCHMARKS if task.lean_task.allowed_sorry)

    assert report["report_id"] == "ablation::p8"
    assert report["baseline"] == "seed-registry"
    assert report["benchmark_task_count"] == len(SEED_BENCHMARKS)
    assert report["heldout_pass_rate"] == 1.0
    assert report["concrete_chain_passed"] is True
    assert report["full_system_ready"] is True
    assert [component["component"] for component in report["components"]] == [
        "retrieval",
        "sft",
        "dpo",
        "process_reward",
        "curation",
    ]
    assert all(component["ready"] for component in report["components"])
    assert report["evidence_summary"]["mean_premise_recall"] == 1.0
    assert report["evidence_summary"]["sft_example_count"] == len(SEED_BENCHMARKS) - placeholder_count
    assert report["evidence_summary"]["dpo_pair_count"] == len(SEED_BENCHMARKS) - placeholder_count
    assert report["evidence_summary"]["grpo_process_task_count"] == len(SEED_BENCHMARKS)
    assert report["evidence_summary"]["curation_gate_passed"] == report["evidence_summary"]["curation_gate_count"]
    assert {row["variant"] for row in report["ablation_rows"]} == {
        "full_system",
        "no_retrieval",
        "no_sft",
        "no_dpo",
        "no_process_reward",
        "no_curation",
    }
    assert set(report) <= set(schema["properties"])


def test_checked_in_external_baseline_plan_artifact() -> None:
    report = json.loads(Path("artifacts/evaluation/external-baseline-plan.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/external_baseline_plan.schema.json").read_text(encoding="utf-8"))
    test_ids = [task.task_id for task in SEED_BENCHMARKS if task.split is BenchmarkSplit.TEST]
    theorem_hole_ids = [task.task_id for task in SEED_BENCHMARKS if task.lean_task.allowed_sorry]

    assert report["report_id"] == "external-baseline-plan::test"
    assert report["split"] == "test"
    assert report["target_task_ids"] == test_ids
    assert report["target_task_count"] == len(test_ids)
    assert report["theorem_hole_task_ids"] == theorem_hole_ids
    assert report["baseline_count"] == 5
    assert report["ready_baseline_count"] == 1
    assert report["blocked_baseline_count"] == 4
    assert report["baselines"][0]["baseline_id"] == "seed-registry"
    assert report["baselines"][0]["status"] == "ready"
    assert "deepseek-prover-v2-7b" in {baseline["baseline_id"] for baseline in report["baselines"]}
    assert "pass_at_32" in report["metrics"]
    assert set(report) <= set(schema["properties"])


def test_checked_in_external_baseline_results_artifact() -> None:
    report = json.loads(Path("artifacts/evaluation/external-baseline-results.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/external_baseline_results.schema.json").read_text(encoding="utf-8"))

    assert report["report_id"] == "external-baseline-results::test"
    assert report["plan_report_id"] == "external-baseline-plan::test"
    assert report["baseline_count"] == 5
    assert report["ingested_count"] == 1
    assert report["blocked_count"] == 4
    assert report["best_available_baseline"] == "seed-registry"
    seed_row = report["rows"][0]
    assert seed_row["baseline_id"] == "seed-registry"
    assert seed_row["ingestion_status"] == "ingested"
    assert seed_row["source"] == "checked_in_seed_registry_fallback"
    assert seed_row["evaluated_task_count"] == 2
    assert {row["ingestion_status"] for row in report["rows"][1:]} == {"blocked_by_plan_status"}
    assert all(row["blocked_reasons"] for row in report["rows"][1:])
    assert set(report) <= set(schema["properties"])


def test_checked_in_empirical_process_targets_artifact() -> None:
    report = json.loads(Path("artifacts/evaluation/empirical-process-targets.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/empirical_process_targets.schema.json").read_text(encoding="utf-8"))

    assert report["report_id"] == "empirical-process-targets::p9"
    assert report["target_count"] == 5
    assert report["scoped_count"] == 5
    assert report["pending_count"] == 0
    targets = {row["target_id"]: row for row in report["targets"]}
    assert "bracketing_gc_interface" in targets
    assert "vc_subgraph_gc_interface" in targets
    assert "donsker_bridge_interface" in targets
    assert "StatInference.VCDeviationCertificate" in targets["vc_subgraph_gc_interface"][
        "lean_declarations"
    ]
    assert "StatInference.VCSubgraphGCRoute" in targets["vc_subgraph_gc_interface"][
        "lean_declarations"
    ]
    assert "bracketing_certificate_gc_seed" in targets["bracketing_gc_interface"][
        "family_benchmark_task_ids"
    ]
    assert "trivial_bracketing_gc_non_vacuity_seed" in targets["bracketing_gc_interface"][
        "family_benchmark_task_ids"
    ]
    assert "vc_deviation_certificate_gc_seed" in targets["vc_subgraph_gc_interface"][
        "family_benchmark_task_ids"
    ]
    assert "vc_subgraph_route_certificate_seed" in targets["vc_subgraph_gc_interface"][
        "family_benchmark_task_ids"
    ]
    assert "trivial_vc_subgraph_gc_non_vacuity_seed" in targets["vc_subgraph_gc_interface"][
        "family_benchmark_task_ids"
    ]
    assert "donsker_statement_seed" in targets["donsker_bridge_interface"]["motivating_task_ids"]
    assert "StatInference.DonskerAsymptoticNormalityRoute" in targets["donsker_bridge_interface"][
        "lean_declarations"
    ]
    assert "donsker_bridge_estimator_clt_seed" in targets["donsker_bridge_interface"][
        "family_benchmark_task_ids"
    ]
    assert "donsker_asymptotic_normality_handoff_seed" in targets["donsker_bridge_interface"][
        "family_benchmark_task_ids"
    ]
    assert "trivial_donsker_asymptotic_normality_seed" in targets["donsker_bridge_interface"][
        "family_benchmark_task_ids"
    ]
    assert "covering_certificate_gc_seed" in targets["covering_number_gc_interface"][
        "motivating_task_ids"
    ]
    assert targets["bracketing_gc_interface"]["gate_status"] == "ready_for_lemma_targets"
    assert targets["vc_subgraph_gc_interface"]["gate_status"] == "ready_for_lemma_targets"
    assert targets["donsker_bridge_interface"]["gate_status"] == "ready_for_lemma_targets"
    assert targets["covering_number_gc_interface"]["gate_status"] == "ready_for_lemma_targets"
    assert targets["rademacher_gc_interface"]["gate_status"] == "ready_for_lemma_targets"
    assert set(report) <= set(schema["properties"])


def test_checked_in_empirical_process_external_slice_artifact() -> None:
    report = json.loads(Path("artifacts/evaluation/empirical-process-external-slice.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/empirical_process_external_slice.schema.json").read_text(encoding="utf-8"))

    assert report["report_id"] == "empirical-process-external-prover-slice::p10"
    assert report["target_report_id"] == "empirical-process-targets::p9"
    assert report["interface_families"] == ["bracketing", "vc_subgraph", "donsker"]
    assert report["family_count"] == 3
    assert report["target_task_count"] == 13
    assert report["ingested_count"] == 1
    assert report["blocked_count"] == 4
    assert report["best_available_baseline"] == "seed-registry"
    families = {row["interface_family"]: row for row in report["families"]}
    assert families["bracketing"]["task_count"] == 5
    assert families["vc_subgraph"]["task_count"] == 3
    assert families["donsker"]["task_count"] == 5
    assert all(family["seed_registry_status"] == "verified" for family in families.values())
    assert all(family["seed_registry_pass_rate"] == 1.0 for family in families.values())
    seed_row = report["rows"][0]
    assert seed_row["baseline_id"] == "seed-registry"
    assert seed_row["source"] == "checked_in_seed_registry_fallback"
    assert seed_row["evaluated_task_count"] == report["target_task_count"]
    assert seed_row["pass_rate"] == 1.0
    assert {row["ingestion_status"] for row in report["rows"][1:]} == {"blocked_by_plan_status"}
    assert set(report) <= set(schema["properties"])


def test_build_vdvw_theorem_inventory_maps_textbook_anchors_to_benchmarks() -> None:
    report = build_vdvw_theorem_inventory(SEED_BENCHMARKS)

    assert report["report_id"] == "vdvw-theorem-inventory::p11.m1"
    assert report["row_count"] == 7
    assert report["family_counts"] == {"bracketing": 2, "donsker": 3, "vc_subgraph": 2}
    assert report["formalization_tier_counts"]["primitive_candidate"] == 1
    assert len(report["blocked_or_review_rows"]) == 7
    assert all(row["human_review_required"] is True for row in report["rows"])
    assert all(
        row["promotion_status"] == "blocked_pending_primitives_or_review"
        for row in report["rows"]
    )
    assert all(not row["missing_benchmark_task_ids"] for row in report["rows"])

    rows = {row["inventory_id"]: row for row in report["rows"]}
    bracketing_gc = rows["vdvw-2.4.1-finite-bracketing-gc"]
    assert bracketing_gc["source_label"] == "Theorem 2.4.1"
    assert bracketing_gc["markdown_anchor"]["line_start"] == 970
    assert "bracketing_deterministic_bound_seed" in bracketing_gc["benchmark_task_ids"]
    assert "StatInference.FiniteL1BracketingFamily" in bracketing_gc["current_lean_declarations"]
    assert any("outer-probability" in risk for risk in bracketing_gc["semantic_risks"])


def test_checked_in_vdvw_theorem_inventory_artifact() -> None:
    report = json.loads(Path("artifacts/research/vdvw-theorem-inventory.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/vdvw_theorem_inventory.schema.json").read_text(encoding="utf-8"))

    assert report["report_id"] == "vdvw-theorem-inventory::p11.m1"
    assert report["source"] == "van der Vaart and Wellner, Weak Convergence and Empirical Processes"
    assert report["row_count"] == 7
    assert report["family_counts"] == {"bracketing": 2, "donsker": 3, "vc_subgraph": 2}
    assert len(report["blocked_or_review_rows"]) == 7
    assert all(row["human_review_required"] for row in report["rows"])
    assert all(
        row["promotion_status"] == "blocked_pending_primitives_or_review"
        for row in report["rows"]
    )
    rows = {row["source_label"]: row for row in report["rows"]}
    assert rows["Theorem 2.4.1"]["markdown_anchor"]["line_start"] == 970
    assert rows["Theorem 2.6.8"]["markdown_anchor"]["line_start"] == 1520
    assert "P11.M1 inventory" in report["notes"]
    assert set(report) <= set(schema["properties"])


def test_checked_in_theorem_hole_promotion_queue_artifact() -> None:
    report = json.loads(Path("artifacts/curation/theorem-hole-promotion-queue.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/theorem_hole_promotion_queue.schema.json").read_text(encoding="utf-8"))
    theorem_hole_ids = [task.task_id for task in SEED_BENCHMARKS if task.lean_task.allowed_sorry]

    assert report["report_id"] == "theorem-hole-promotion-queue::p9"
    assert report["theorem_hole_task_count"] == len(theorem_hole_ids)
    assert report["promoted_count"] == len(theorem_hole_ids)
    assert report["queued_count"] == 0
    assert report["first_target_task_id"] == "ipw_linearization_theorem_hole_seed"
    assert report["first_target_declaration"] == "StatInference.ipw_hajek_linearization_constructor"
    assert [row["task_id"] for row in report["queue"]] == theorem_hole_ids
    assert all(row["status"] == "promoted_no_placeholder_proof" for row in report["queue"])
    assert all("sorry" not in row["no_placeholder_proof_block"] for row in report["queue"])
    assert set(report) <= set(schema["properties"])


def test_checked_in_reproducibility_bundle_artifact() -> None:
    report = json.loads(Path("artifacts/evaluation/reproducibility-bundle.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/reproducibility_bundle.schema.json").read_text(encoding="utf-8"))
    artifact_paths = [artifact["path"] for artifact in report["artifacts"]]

    assert report["report_id"] == "reproducibility::p8"
    assert report["blueprint_id"] == "statleanagent-blueprint"
    assert report["all_phases_done"] is False
    assert report["paper_draft_path"] == "docs/paper_draft.md"
    assert report["artifact_count"] == len(report["artifacts"])
    assert "docs/paper_draft.md" in artifact_paths
    assert "artifacts/evaluation/ablation-report.json" in artifact_paths
    assert "artifacts/evaluation/external-baseline-plan.json" in artifact_paths
    assert "artifacts/evaluation/external-baseline-results.json" in artifact_paths
    assert "artifacts/evaluation/empirical-process-targets.json" in artifact_paths
    assert "artifacts/evaluation/empirical-process-external-slice.json" in artifact_paths
    assert "artifacts/research/vdvw-theorem-inventory.json" in artifact_paths
    assert "artifacts/curation/theorem-hole-promotion-queue.json" in artifact_paths
    assert all(len(artifact["sha256"]) == 64 for artifact in report["artifacts"])
    assert any(command["name"] == "smoke" for command in report["validation_commands"])
    assert any(command["name"] == "forbidden_lean_shortcuts" for command in report["validation_commands"])
    assert report["current_milestone"]["id"] == "P11.M2"
    assert set(report) <= set(schema["properties"])


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

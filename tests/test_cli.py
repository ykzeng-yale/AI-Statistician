import json
from pathlib import Path

from statlean_agent.cli import main
from statlean_agent.contracts import ProofAttempt, VerificationReport, VerificationStatus
from statlean_agent.serialization import read_jsonl, write_jsonl


def test_cli_seed_and_list_benchmarks(tmp_path: Path, capsys) -> None:
    path = tmp_path / "seeds.jsonl"
    assert main(["seed-benchmarks", "--output", str(path)]) == 0
    assert path.exists()

    assert main(["list-benchmarks", "--input", str(path)]) == 0
    output = capsys.readouterr().out
    assert "erm_oracle_ineq_seed" in output


def test_cli_render_task(tmp_path: Path, capsys) -> None:
    path = tmp_path / "seeds.jsonl"
    main(["seed-benchmarks", "--output", str(path)])
    assert main(["render-task", "erm_oracle_ineq_seed", "--input", str(path)]) == 0
    output = capsys.readouterr().out
    assert "import StatInference.Asymptotics.Basic" in output


def test_cli_blueprint_status(capsys) -> None:
    assert main(["blueprint-status", "--blueprint", "config/statlean_blueprint.json"]) == 0
    output = capsys.readouterr().out
    assert "Current phase: P10" in output
    assert "Current milestone: P10.M5" in output

    assert main(["blueprint-status", "--blueprint", "config/statlean_blueprint.json", "--json"]) == 0
    json_output = capsys.readouterr().out
    assert '"current_phase"' in json_output
    assert '"P10.M5"' in json_output


def test_cli_verify_benchmarks_allow_failures(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "seeds.jsonl"
    output_path = tmp_path / "reports.jsonl"
    main(["seed-benchmarks", "--output", str(input_path)])
    assert (
        main(
            [
                "verify-benchmarks",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--repo",
                str(tmp_path),
                "--timeout",
                "1",
                "--allow-failures",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    report_count = len(read_jsonl(output_path))
    assert f"verified={report_count}" in output
    assert report_count > 0


def test_cli_materialize_benchmark_attempts(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    attempts_path = tmp_path / "attempts.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])

    assert (
        main(
            [
                "materialize-benchmark-attempts",
                "--benchmarks",
                str(benchmark_path),
                "--output",
                str(attempts_path),
                "--agent-key",
                "test-agent",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    attempts = read_jsonl(attempts_path)
    assert f"materialized={len(attempts)}" in output
    assert attempts[0]["agent_key"] == "test-agent"
    assert "namespace StatInference.Benchmarks" in attempts[0]["lean_code"]


def test_cli_axle_tool_uses_optional_remote_client(tmp_path: Path, capsys, monkeypatch) -> None:
    source_path = tmp_path / "Task.lean"
    output_path = tmp_path / "axle.json"
    content_path = tmp_path / "Task.sorry.lean"
    source_path.write_text("theorem foo : 1 = 1 := by rfl\n", encoding="utf-8")

    class FakeAxleClient:
        @classmethod
        def from_env(cls, *, base_url: str, timeout_seconds: int):
            assert base_url == "https://example.test"
            assert timeout_seconds == 7
            return cls()

        def transform_code(
            self,
            tool: str,
            code: str,
            *,
            env: str,
            ignore_imports: bool | None = None,
            timeout_seconds: float | None = None,
        ):
            assert tool == "theorem2sorry"
            assert "theorem foo" in code
            assert env == "lean-test"
            assert ignore_imports in (None, False)
            assert timeout_seconds == 7
            return {
                "content": "theorem foo : 1 = 1 := sorry\n",
                "lean_messages": {"errors": [], "warnings": ["uses sorry"], "infos": []},
                "tool_messages": {"errors": [], "warnings": [], "infos": []},
            }

    monkeypatch.setattr("statlean_agent.cli.AxleClient", FakeAxleClient)
    assert (
        main(
            [
                "axle-tool",
                "theorem2sorry",
                str(source_path),
                "--output",
                str(output_path),
                "--content-output",
                str(content_path),
                "--env",
                "lean-test",
                "--base-url",
                "https://example.test",
                "--timeout",
                "7",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "lean_errors=0" in output
    assert "lean_warnings=1" in output
    assert read_jsonl(output_path)[0]["content"].startswith("theorem foo")
    assert content_path.read_text(encoding="utf-8").endswith("sorry\n")


def test_cli_axle_verify_proof_uses_statement_and_content(tmp_path: Path, capsys, monkeypatch) -> None:
    statement_path = tmp_path / "Statement.lean"
    content_path = tmp_path / "Proof.lean"
    statement_path.write_text("theorem foo : 1 = 1 := by sorry\n", encoding="utf-8")
    content_path.write_text("theorem foo : 1 = 1 := by rfl\n", encoding="utf-8")

    class FakeAxleClient:
        @classmethod
        def from_env(cls, *, base_url: str, timeout_seconds: int):
            return cls()

        def verify_proof(
            self,
            *,
            formal_statement: str,
            content: str,
            env: str,
            ignore_imports: bool | None = None,
            timeout_seconds: float | None = None,
        ):
            assert "sorry" in formal_statement
            assert "rfl" in content
            assert env == "lean-test"
            assert ignore_imports in (None, False)
            assert timeout_seconds == 120
            return {"okay": True, "failed_declarations": []}

    monkeypatch.setattr("statlean_agent.cli.AxleClient", FakeAxleClient)
    assert (
        main(
            [
                "axle-verify-proof",
                "--statement",
                str(statement_path),
                "--content",
                str(content_path),
                "--env",
                "lean-test",
            ]
        )
        == 0
    )
    assert "okay=True" in capsys.readouterr().out


def test_cli_materialize_dpo_rejections_and_verify_attempts(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    rejected_attempts_path = tmp_path / "dpo-negative-attempts.jsonl"
    rejected_reports_path = tmp_path / "dpo-negative-reports.jsonl"
    static_attempts_path = tmp_path / "static-attempts.jsonl"
    static_reports_path = tmp_path / "static-reports.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])

    assert (
        main(
            [
                "materialize-dpo-rejections",
                "--benchmarks",
                str(benchmark_path),
                "--output",
                str(rejected_attempts_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    rejected_attempts = read_jsonl(rejected_attempts_path)
    assert "materialized=" in output
    assert len(rejected_attempts) > 0
    assert all("__statlean_dpo_missing_premise__" in record["lean_code"] for record in rejected_attempts)
    assert all("sorry" not in record["lean_code"] for record in rejected_attempts)

    write_jsonl(static_attempts_path, [ProofAttempt("task", "agent", "theorem bad : True := by\n  sorry")])
    assert (
        main(
            [
                "verify-attempts",
                "--attempts",
                str(static_attempts_path),
                "--output",
                str(static_reports_path),
                "--repo",
                str(tmp_path),
                "--allow-failures",
            ]
        )
        == 0
    )
    assert read_jsonl(static_reports_path)[0]["status"] == "rejected"

    write_jsonl(rejected_reports_path, [VerificationReport(rejected_attempts[0]["task_id"], VerificationStatus.REJECTED)])
    assert rejected_reports_path.exists()


def test_cli_materialize_grpo_tasks(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    grpo_path = tmp_path / "grpo.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])

    assert (
        main(
            [
                "materialize-grpo-tasks",
                "--benchmarks",
                str(benchmark_path),
                "--output",
                str(grpo_path),
                "--repo",
                ".",
                "--python",
                ".venv/bin/python",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    records = read_jsonl(grpo_path)
    assert f"materialized={len(records)}" in output
    assert "allowed_placeholder_tasks=3" in output
    assert records[0]["reward_source"] == "lean_process_reward"
    assert records[0]["verifier_command"][:4] == [
        ".venv/bin/python",
        "-m",
        "statlean_agent.cli",
        "verify-task",
    ]
    assert "proof_complete" in records[0]["reward_components"]


def test_cli_build_lemma_ledger(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    ledger_path = tmp_path / "ledger.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])
    reports = [
        VerificationReport("ipw_linearization_theorem_hole_seed", VerificationStatus.ACCEPTED),
        VerificationReport("aipw_product_rate_theorem_hole_seed", VerificationStatus.ACCEPTED),
        VerificationReport("if_normality_theorem_hole_seed", VerificationStatus.ACCEPTED),
    ]
    write_jsonl(reports_path, reports)

    assert (
        main(
            [
                "build-lemma-ledger",
                "--benchmarks",
                str(benchmark_path),
                "--reports",
                str(reports_path),
                "--output",
                str(ledger_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    records = read_jsonl(ledger_path)
    assert "ledger_entries=3" in output
    assert "blocked_placeholder=3" in output
    assert {record["status"] for record in records} == {"blocked_placeholder"}


def test_cli_build_lemma_proposals(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    proposals_path = tmp_path / "lemma-proposals.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])

    assert (
        main(
            [
                "build-lemma-proposals",
                "--benchmarks",
                str(benchmark_path),
                "--output",
                str(proposals_path),
                "--proposed-by",
                "test-miner",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    records = read_jsonl(proposals_path)
    assert "lemma_proposals=3" in output
    assert "blocked=3" in output
    assert {record["proposed_by"] for record in records} == {"test-miner"}
    assert {record["status"] for record in records} == {"needs_no_sorry_proof"}
    assert all("non_vacuity_example" in record["required_gates"] for record in records)


def test_cli_theorem_hole_promotion_queue(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    queue_path = tmp_path / "promotion-queue.json"
    main(["seed-benchmarks", "--output", str(benchmark_path)])

    assert (
        main(
            [
                "theorem-hole-promotion-queue",
                "--benchmarks",
                str(benchmark_path),
                "--output",
                str(queue_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    assert "promotion_queue=3" in output
    assert "promoted=3" in output
    assert "first_target=ipw_linearization_theorem_hole_seed" in output
    assert queue["first_target_declaration"] == "StatInference.ipw_hajek_linearization_constructor"
    assert {row["status"] for row in queue["queue"]} == {"promoted_no_placeholder_proof"}


def test_cli_check_lemma_proposals(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    proposals_path = tmp_path / "lemma-proposals.jsonl"
    gates_path = tmp_path / "lemma-proposal-gates.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])
    main(["build-lemma-proposals", "--benchmarks", str(benchmark_path), "--output", str(proposals_path)])

    assert (
        main(
            [
                "check-lemma-proposals",
                "--proposals",
                str(proposals_path),
                "--output",
                str(gates_path),
                "--root",
                ".",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    records = read_jsonl(gates_path)
    assert "proposal_gate_reports=3" in output
    assert "passed=3" in output
    assert {record["status"] for record in records} == {"passed"}
    assert all(not record["unused_imports"] for record in records)
    assert all(not record["missing_imports"] for record in records)


def test_cli_check_lemma_non_vacuity(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    proposals_path = tmp_path / "lemma-proposals.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    non_vacuity_path = tmp_path / "lemma-non-vacuity.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])
    main(["build-lemma-proposals", "--benchmarks", str(benchmark_path), "--output", str(proposals_path)])

    accepted_reports = [
        VerificationReport(record["task_id"], VerificationStatus.ACCEPTED)
        for record in read_jsonl(benchmark_path)
    ]
    write_jsonl(reports_path, accepted_reports)

    assert (
        main(
            [
                "check-lemma-non-vacuity",
                "--proposals",
                str(proposals_path),
                "--benchmarks",
                str(benchmark_path),
                "--reports",
                str(reports_path),
                "--output",
                str(non_vacuity_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    records = read_jsonl(non_vacuity_path)
    assert "non_vacuity_reports=3" in output
    assert "passed=3" in output
    assert {record["status"] for record in records} == {"passed"}
    assert all(record["accepted_evidence_task_ids"] for record in records)


def test_cli_check_lemma_proof_cost(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    proposals_path = tmp_path / "lemma-proposals.jsonl"
    proof_cost_path = tmp_path / "lemma-proof-cost.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])
    main(["build-lemma-proposals", "--benchmarks", str(benchmark_path), "--output", str(proposals_path)])

    assert (
        main(
            [
                "check-lemma-proof-cost",
                "--proposals",
                str(proposals_path),
                "--benchmarks",
                str(benchmark_path),
                "--output",
                str(proof_cost_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    records = read_jsonl(proof_cost_path)
    assert "proof_cost_reports=3" in output
    assert "passed=3" in output
    assert "total_delta=3" in output
    assert {record["status"] for record in records} == {"passed"}
    assert all(record["proof_cost_delta"] > 0 for record in records)


def test_cli_external_baseline_plan(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    output_path = tmp_path / "external-plan.json"
    main(["seed-benchmarks", "--output", str(benchmark_path)])

    assert (
        main(
            [
                "external-baseline-plan",
                "--benchmarks",
                str(benchmark_path),
                "--split",
                "test",
                "--output-dir",
                "tmp-external",
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    plan = json.loads(output_path.read_text(encoding="utf-8"))
    assert "baselines=5" in output
    assert "ready=1" in output
    assert "target_tasks=2" in output
    assert plan["report_id"] == "external-baseline-plan::test"
    assert plan["ready_baseline_count"] == 1
    assert plan["blocked_baseline_count"] == 4
    assert plan["baselines"][0]["attempts_path"].startswith("tmp-external/")


def test_cli_external_baseline_results(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    plan_path = tmp_path / "external-plan.json"
    output_path = tmp_path / "external-results.json"
    attempts_path = tmp_path / "attempts.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])
    main(["external-baseline-plan", "--benchmarks", str(benchmark_path), "--output", str(plan_path)])
    write_jsonl(
        attempts_path,
        [
            ProofAttempt(
                "erm_zero_deviation_exact_risk_seed",
                "seed-registry",
                "theorem ok : True := by trivial",
            ),
            ProofAttempt(
                "donsker_statement_seed",
                "seed-registry",
                "theorem ok : True := by trivial",
            ),
        ],
    )
    write_jsonl(
        reports_path,
        [
            VerificationReport("erm_zero_deviation_exact_risk_seed", VerificationStatus.ACCEPTED),
            VerificationReport("donsker_statement_seed", VerificationStatus.ACCEPTED),
        ],
    )

    assert (
        main(
            [
                "external-baseline-results",
                "--benchmarks",
                str(benchmark_path),
                "--plan",
                str(plan_path),
                "--seed-attempts",
                str(attempts_path),
                "--seed-reports",
                str(reports_path),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    results = json.loads(output_path.read_text(encoding="utf-8"))
    assert "external_results=5" in output
    assert "ingested=1" in output
    assert "blocked=4" in output
    assert results["best_available_baseline"] == "seed-registry"
    assert results["rows"][0]["source"] == "checked_in_seed_registry_fallback"


def test_cli_empirical_process_targets(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    output_path = tmp_path / "empirical-process-targets.json"
    main(["seed-benchmarks", "--output", str(benchmark_path)])

    assert (
        main(
            [
                "empirical-process-targets",
                "--benchmarks",
                str(benchmark_path),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert "empirical_process_targets=5" in output
    assert "scoped=5" in output
    assert report["report_id"] == "empirical-process-targets::p9"
    assert {row["target_id"] for row in report["targets"]} >= {
        "bracketing_gc_interface",
        "vc_subgraph_gc_interface",
        "donsker_bridge_interface",
    }


def test_cli_ablation_report(tmp_path: Path, capsys) -> None:
    benchmark_path = tmp_path / "seeds.jsonl"
    paper_heldout_path = tmp_path / "paper-heldout.json"
    concrete_chain_path = tmp_path / "concrete-chain.json"
    manifest_path = tmp_path / "manifest.json"
    grpo_path = tmp_path / "grpo.jsonl"
    dpo_reports_path = tmp_path / "dpo-reports.jsonl"
    proposal_gates_path = tmp_path / "proposal-gates.jsonl"
    non_vacuity_path = tmp_path / "non-vacuity.jsonl"
    proof_cost_path = tmp_path / "proof-cost.jsonl"
    ledger_path = tmp_path / "ledger.jsonl"
    output_path = tmp_path / "ablation.json"
    main(["seed-benchmarks", "--output", str(benchmark_path)])
    paper_heldout_path.write_text(
        json.dumps(
            {
                "baseline": "seed-registry",
                "heldout_pass_rate": 1.0,
                "baseline_comparison": {"mean_premise_recall": 1.0},
            }
        ),
        encoding="utf-8",
    )
    concrete_chain_path.write_text(json.dumps({"passed": True}), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "sft_examples": [{"example_id": "sft::task"}],
                "dpo_pairs": [{"pair_id": "dpo::task"}],
                "grpo_tasks": [{"task_id": "task"}],
            }
        ),
        encoding="utf-8",
    )
    write_jsonl(
        grpo_path,
        [
            {
                "task_id": "task",
                "reward_components": ["proof_complete", "locally_valid_steps"],
            }
        ],
    )
    write_jsonl(dpo_reports_path, [{"task_id": "task", "status": "rejected"}])
    write_jsonl(proposal_gates_path, [{"proposal_id": "p", "passed": True}])
    write_jsonl(non_vacuity_path, [{"proposal_id": "p", "passed": True}])
    write_jsonl(proof_cost_path, [{"proposal_id": "p", "passed": True}])
    write_jsonl(ledger_path, [{"ledger_id": "l", "status": "blocked_placeholder"}])

    assert (
        main(
            [
                "ablation-report",
                "--benchmarks",
                str(benchmark_path),
                "--paper-heldout",
                str(paper_heldout_path),
                "--concrete-chain",
                str(concrete_chain_path),
                "--training-manifest",
                str(manifest_path),
                "--grpo-tasks",
                str(grpo_path),
                "--dpo-reports",
                str(dpo_reports_path),
                "--lemma-proposal-gates",
                str(proposal_gates_path),
                "--lemma-non-vacuity",
                str(non_vacuity_path),
                "--lemma-proof-cost",
                str(proof_cost_path),
                "--lemma-ledger",
                str(ledger_path),
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert "full_system_ready=True" in output
    assert "components=5" in output
    assert "variants=6" in output
    assert report["full_system_ready"] is True
    assert report["evidence_summary"]["dpo_rejected_report_count"] == 1


def test_cli_reproducibility_bundle(tmp_path: Path, capsys) -> None:
    blueprint_path = tmp_path / "blueprint.json"
    artifact_path = tmp_path / "artifact.json"
    paper_path = tmp_path / "paper.md"
    output_path = tmp_path / "repro.json"
    blueprint_path.write_text(
        json.dumps(
            {
                "id": "bp",
                "target": "target",
                "phases": [
                    {
                        "id": "P8",
                        "name": "Final",
                        "status": "done",
                        "milestones": [{"id": "P8.M4", "name": "Bundle", "status": "done"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    artifact_path.write_text('{"ok": true}\n', encoding="utf-8")
    paper_path.write_text("# Paper\n", encoding="utf-8")

    assert (
        main(
            [
                "reproducibility-bundle",
                "--repo-root",
                str(tmp_path),
                "--blueprint",
                str(blueprint_path),
                "--paper-draft",
                "paper.md",
                "--artifact",
                "artifact.json",
                "--artifact",
                "paper.md",
                "--output",
                str(output_path),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert "artifacts=2" in output
    assert "all_phases_done=True" in output
    assert report["artifact_count"] == 2
    assert report["all_phases_done"] is True
    assert report["paper_draft_path"] == "paper.md"


def test_cli_eval_attempts(tmp_path: Path, capsys) -> None:
    attempts_path = tmp_path / "attempts.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    write_jsonl(attempts_path, [ProofAttempt("task", "agent", "theorem ok : True := by trivial")])
    write_jsonl(reports_path, [VerificationReport("task", VerificationStatus.ACCEPTED)])

    assert main(["eval-attempts", "--attempts", str(attempts_path), "--reports", str(reports_path)]) == 0
    output = capsys.readouterr().out
    assert '"pass_rate": 1.0' in output


def test_cli_index_search_and_training_manifest(tmp_path: Path, capsys) -> None:
    index_path = tmp_path / "premises.jsonl"
    manifest_path = tmp_path / "manifest.json"
    verified_manifest_path = tmp_path / "verified-manifest.json"
    attempts_path = tmp_path / "attempts.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    benchmark_path = tmp_path / "seeds.jsonl"
    main(["seed-benchmarks", "--output", str(benchmark_path)])

    assert main(["index-premises", "--root", ".", "--output", str(index_path)]) == 0
    assert index_path.exists()
    assert main(["search-premises", "oracle excess risk", "--index", str(index_path), "--top-k", "3"]) == 0
    search_output = capsys.readouterr().out
    assert "oracle" in search_output

    assert (
        main(
            [
                "build-training-manifest",
                "--benchmarks",
                str(benchmark_path),
                "--output",
                str(manifest_path),
                "--run-id",
                "cli-test",
            ]
        )
        == 0
    )
    assert manifest_path.exists()
    assert "cli-test" in manifest_path.read_text(encoding="utf-8")

    write_jsonl(
        attempts_path,
        [
            ProofAttempt("erm_oracle_ineq_seed", "agent", "theorem ok : True := by trivial"),
            ProofAttempt("erm_oracle_ineq_seed", "agent", "theorem bad : True := by exact missing"),
        ],
    )
    write_jsonl(
        reports_path,
        [
            VerificationReport("erm_oracle_ineq_seed", VerificationStatus.ACCEPTED),
            VerificationReport("erm_oracle_ineq_seed", VerificationStatus.REJECTED),
        ],
    )
    assert (
        main(
            [
                "build-training-manifest",
                "--benchmarks",
                str(benchmark_path),
                "--attempts",
                str(attempts_path),
                "--reports",
                str(reports_path),
                "--output",
                str(verified_manifest_path),
                "--run-id",
                "verified-cli-test",
            ]
        )
        == 0
    )
    verified_manifest = json.loads(verified_manifest_path.read_text(encoding="utf-8"))
    assert verified_manifest["metadata"]["sft_source"] == "verified_attempts"
    assert len(verified_manifest["sft_examples"]) == 1
    assert len(verified_manifest["dpo_pairs"]) == 1

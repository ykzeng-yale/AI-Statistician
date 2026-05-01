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
    assert "Current phase: P7" in output
    assert "Current milestone: P7.M2" in output

    assert main(["blueprint-status", "--blueprint", "config/statlean_blueprint.json", "--json"]) == 0
    json_output = capsys.readouterr().out
    assert '"current_phase"' in json_output
    assert '"P7.M2"' in json_output


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

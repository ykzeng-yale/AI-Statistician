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
    assert "Current phase: P6" in output
    assert "Current milestone: P6.M2" in output

    assert main(["blueprint-status", "--blueprint", "config/statlean_blueprint.json", "--json"]) == 0
    json_output = capsys.readouterr().out
    assert '"current_phase"' in json_output
    assert '"P6.M2"' in json_output


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

    write_jsonl(attempts_path, [ProofAttempt("erm_oracle_ineq_seed", "agent", "theorem ok : True := by trivial")])
    write_jsonl(reports_path, [VerificationReport("erm_oracle_ineq_seed", VerificationStatus.ACCEPTED)])
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

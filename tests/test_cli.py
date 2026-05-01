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
    assert "verified=6" in output
    assert len(read_jsonl(output_path)) == 6


def test_cli_eval_attempts(tmp_path: Path, capsys) -> None:
    attempts_path = tmp_path / "attempts.jsonl"
    reports_path = tmp_path / "reports.jsonl"
    write_jsonl(attempts_path, [ProofAttempt("task", "agent", "theorem ok : True := by trivial")])
    write_jsonl(reports_path, [VerificationReport("task", VerificationStatus.ACCEPTED)])

    assert main(["eval-attempts", "--attempts", str(attempts_path), "--reports", str(reports_path)]) == 0
    output = capsys.readouterr().out
    assert '"pass_rate": 1.0' in output

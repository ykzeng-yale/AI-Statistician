from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.proof_training_export import export_proof_training_dataset


def test_proof_training_export_publishes_source_aware_training_boundaries(
    tmp_path: Path,
) -> None:
    attempt_log = tmp_path / "proof_attempts.jsonl"
    out_dir = tmp_path / "proof_training_export"
    attempts = [
        {
            "attempt_id": "attempt:kernel-clean",
            "obligation_id": "clean_obligation",
            "title": "Clean obligation",
            "ok": True,
            "kernel_verified": True,
            "verification_strength": "local_lean_kernel",
            "verifier": "local.lake_env_lean",
            "formal_statement": "theorem clean_obligation : True := by trivial",
            "supervision_target": "trivial",
            "candidate_hash": "clean-hash",
            "expected_lemmas": ["True.intro"],
            "retrieval_hits": [{"obligation_id": "neighbor_clean"}],
            "tags": ["verified"],
        },
        {
            "attempt_id": "attempt:mock-positive",
            "obligation_id": "mock_obligation",
            "title": "Mock obligation",
            "ok": True,
            "kernel_verified": False,
            "verification_strength": "mock_static_check",
            "verifier": "mock",
            "formal_statement": "theorem mock_obligation : True := by trivial",
            "supervision_target": "trivial",
            "candidate_hash": "mock-hash",
            "expected_lemmas": [],
            "retrieval_hits": [],
            "tags": ["regression"],
        },
        {
            "attempt_id": "attempt:sorry-positive",
            "obligation_id": "sorry_obligation",
            "title": "Sorry obligation",
            "ok": True,
            "kernel_verified": True,
            "verification_strength": "local_lean_kernel",
            "verifier": "local.lake_env_lean",
            "formal_statement": "theorem sorry_obligation : True := by sorry",
            "supervision_target": "by\n  sorry",
            "candidate_hash": "sorry-hash",
            "expected_lemmas": [],
            "retrieval_hits": [],
            "tags": ["prototype"],
        },
        {
            "attempt_id": "attempt:failed",
            "obligation_id": "failed_obligation",
            "title": "Failed obligation",
            "ok": False,
            "kernel_verified": False,
            "verification_strength": "local_lean_kernel",
            "verifier": "local.lake_env_lean",
            "formal_statement": "theorem failed_obligation : True := by exact False.elim ?h",
            "proof_body": "exact False.elim ?h",
            "candidate_hash": "failed-hash",
            "reward": 0.0,
            "first_error": "unsolved goals",
            "errors": ["unsolved goals"],
            "expected_lemmas": ["False.elim"],
            "retrieval_hits": [{"obligation_id": "neighbor_failed"}],
            "tags": ["negative"],
        },
    ]
    attempt_log.write_text(
        "".join(json.dumps(row) + "\n" for row in attempts),
        encoding="utf-8",
    )

    payload = export_proof_training_dataset(
        attempt_log,
        out_dir,
        validation_fraction=0.0,
    )

    assert payload["n_sft_examples"] == 3
    assert payload["n_kernel_positive_attempts"] == 2
    assert payload["n_non_kernel_positive_attempts"] == 1
    assert payload["source_aware_training_export_policy"]["policy_id"] == (
        "proof_training_source_aware_export_policy:1"
    )
    assert payload["n_source_aware_training_eligible"] == 1
    assert payload["n_source_aware_training_quarantined_positive"] == 2
    assert payload["n_source_aware_training_hard_negative"] == 1
    assert payload["n_source_aware_non_kernel_quarantined"] == 1
    assert payload["n_source_aware_forbidden_token_quarantined"] == 1
    assert payload["n_source_aware_wip_or_placeholder_quarantined"] == 1
    assert payload["by_source_aware_training_status"] == {
        "quarantined_positive": 2,
        "training_eligible": 1,
    }
    eligible_rows = [
        json.loads(line)
        for line in Path(payload["source_aware_all_jsonl"]).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert len(eligible_rows) == 1
    assert eligible_rows[0]["obligation_id"] == "clean_obligation"
    assert eligible_rows[0]["source_aware_training_status"] == "training_eligible"
    quarantined_rows = [
        json.loads(line)
        for line in Path(payload["quarantined_positive_jsonl"]).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert {row["obligation_id"] for row in quarantined_rows} == {
        "mock_obligation",
        "sorry_obligation",
    }
    hard_negative_rows = [
        json.loads(line)
        for line in Path(payload["hard_negative_jsonl"]).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert len(hard_negative_rows) == 1
    assert hard_negative_rows[0]["task"] == "lean_whole_proof_hard_negative"
    assert hard_negative_rows[0]["hard_negative_reasons"] == [
        "failed_or_rejected_attempt"
    ]
    compatibility_rows = [
        json.loads(line)
        for line in Path(payload["all_jsonl"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(compatibility_rows) == 3

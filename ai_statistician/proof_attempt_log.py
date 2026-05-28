from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .fingerprint import stable_hash
from .proof_bank import proof_bank_fingerprint
from .schema import FormalObligation, ProofAttemptRecord, ProofCheck
from .verifier import splice_proof


PROOF_ATTEMPT_SCHEMA_VERSION = 1


def build_proof_attempt_record(
    obligation: FormalObligation,
    check: ProofCheck,
    *,
    attempt_index: int,
) -> ProofAttemptRecord:
    candidate = splice_proof(obligation.formal_statement, check.proof_body)
    candidate_hash = stable_hash(
        {
            "obligation_id": obligation.id,
            "formal_statement": obligation.formal_statement,
            "candidate": candidate,
            "verifier": check.verifier,
        }
    )
    attempt_id = f"{obligation.id}:{attempt_index}:{candidate_hash[:16]}"
    errors = tuple(check.errors)
    return ProofAttemptRecord(
        schema_version=PROOF_ATTEMPT_SCHEMA_VERSION,
        attempt_id=attempt_id,
        obligation_id=obligation.id,
        title=obligation.title,
        tags=obligation.tags,
        source=obligation.source,
        expected_lemmas=obligation.expected_lemmas,
        depends_on=obligation.depends_on,
        formal_statement=obligation.formal_statement,
        proof_body=check.proof_body,
        candidate=candidate,
        candidate_hash=candidate_hash,
        verifier=check.verifier,
        ok=check.ok,
        reward=1.0 if check.ok else 0.0,
        elapsed_ms=check.elapsed_ms,
        errors=errors,
        first_error=errors[0] if errors else "",
        retrieval_hits=tuple(check.retrieval_hits),
        supervision_target=check.proof_body if check.ok else "",
    )


def write_proof_attempt_log(
    records: list[ProofAttemptRecord],
    out_dir: Path,
) -> dict[str, object]:
    """Persist proof-level attempt data for future prover training.

    The JSONL file is intentionally append-friendly in shape, but this function
    writes a complete audit-run snapshot so release artifacts are reproducible.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "proof_attempts.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(asdict(row), default=str) + "\n")
    manifest = {
        "schema_version": PROOF_ATTEMPT_SCHEMA_VERSION,
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "n_attempts": len(records),
        "n_positive": sum(1 for row in records if row.ok),
        "n_negative": sum(1 for row in records if not row.ok),
        "positive_rate": (
            sum(1 for row in records if row.ok) / len(records)
            if records
            else 0.0
        ),
        "attempt_log": str(jsonl_path),
        "attempt_log_fingerprint": stable_hash([asdict(row) for row in records]),
        "limitations": [
            "proof-level attempts only; no tactic-state transitions yet",
            "positive rows are suitable for verifier-filtered whole-proof SFT or rejection sampling",
            "negative rows preserve verifier errors for future repair/value-model data",
        ],
    }
    manifest_path = out_dir / "proof_attempt_log_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest

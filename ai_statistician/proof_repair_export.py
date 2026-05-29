from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash


PROOF_REPAIR_EXPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProofRepairExample:
    schema_version: int
    example_id: str
    split: str
    task: str
    prompt: str
    target_completion: str
    obligation_id: str
    failed_attempt_id: str
    target_attempt_id: str
    failed_candidate_hash: str
    target_candidate_hash: str
    verifier: str
    verification_strength: str
    target_kernel_verified: bool
    first_error: str
    expected_lemmas: tuple[str, ...]
    retrieved_obligations: tuple[str, ...]
    tags: tuple[str, ...]


def export_proof_repair_dataset(
    attempt_log: Path,
    out_dir: Path,
    *,
    validation_fraction: float = 0.2,
) -> dict[str, object]:
    """Export failed proof attempts paired with verified repair targets.

    This is not tactic-level process data. It is a whole-proof repair dataset:
    a failed proof body plus verifier error maps to the best accepted proof body
    for the same obligation. It lets future proof models train on failures
    without confusing them with verified positives.
    """

    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0.0, 1.0)")
    attempts = _read_jsonl(attempt_log)
    targets = _target_by_obligation(attempts)
    negatives = [row for row in attempts if not row.get("ok")]
    examples: list[ProofRepairExample] = []
    negatives_without_target = 0
    for row in negatives:
        obligation_id = str(row.get("obligation_id", ""))
        target = targets.get(obligation_id)
        if target is None:
            negatives_without_target += 1
            continue
        split = _split_for_attempt(str(row.get("attempt_id", "")), validation_fraction)
        examples.append(_repair_example(row, target, split=split))

    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "proof_repair_train.jsonl"
    validation_path = out_dir / "proof_repair_validation.jsonl"
    all_path = out_dir / "proof_repair_all.jsonl"
    _write_jsonl(train_path, [row for row in examples if row.split == "train"])
    _write_jsonl(validation_path, [row for row in examples if row.split == "validation"])
    _write_jsonl(all_path, examples)
    manifest = {
        "schema_version": PROOF_REPAIR_EXPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_attempt_log": str(attempt_log),
        "source_attempt_log_fingerprint": stable_hash(attempts),
        "validation_fraction": validation_fraction,
        "n_attempts": len(attempts),
        "n_negative_attempts": len(negatives),
        "n_targets": len(targets),
        "n_negative_without_target": negatives_without_target,
        "n_repair_examples": len(examples),
        "n_train": sum(1 for row in examples if row.split == "train"),
        "n_validation": sum(1 for row in examples if row.split == "validation"),
        "train_jsonl": str(train_path),
        "validation_jsonl": str(validation_path),
        "all_jsonl": str(all_path),
        "dataset_fingerprint": stable_hash([asdict(row) for row in examples]),
        "limitations": [
            "whole-proof repair examples only; no tactic-state transitions",
            "failed attempts are paired by obligation_id with accepted proof bodies",
            "negative controls may be synthetic empty-proof failures unless produced by a real prover search loop",
            "target_kernel_verified must be filtered downstream when training on AXLE-only targets",
        ],
    }
    manifest_path = out_dir / "proof_repair_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _target_by_obligation(attempts: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    targets: dict[str, dict[str, object]] = {}
    for row in attempts:
        if not row.get("ok") or not str(row.get("supervision_target", "")).strip():
            continue
        obligation_id = str(row.get("obligation_id", ""))
        current = targets.get(obligation_id)
        if current is None or _target_rank(row) > _target_rank(current):
            targets[obligation_id] = row
    return targets


def _target_rank(row: dict[str, object]) -> tuple[int, int, str]:
    return (
        1 if row.get("kernel_verified") else 0,
        1 if row.get("ok") else 0,
        str(row.get("attempt_id", "")),
    )


def _repair_example(
    failed: dict[str, object],
    target: dict[str, object],
    *,
    split: str,
) -> ProofRepairExample:
    expected_lemmas = tuple(str(item) for item in failed.get("expected_lemmas", []) or [])
    retrieval_hits = failed.get("retrieval_hits", []) or []
    retrieved_obligations = tuple(
        str(hit.get("obligation_id", ""))
        for hit in retrieval_hits
        if isinstance(hit, dict) and hit.get("obligation_id")
    )
    failed_attempt_id = str(failed.get("attempt_id", ""))
    obligation_id = str(failed.get("obligation_id", ""))
    return ProofRepairExample(
        schema_version=PROOF_REPAIR_EXPORT_SCHEMA_VERSION,
        example_id=f"{obligation_id}:repair:{stable_hash(failed_attempt_id)[:16]}",
        split=split,
        task="lean_whole_proof_repair_from_verifier_error",
        prompt=_prompt_for_repair(failed, expected_lemmas, retrieved_obligations),
        target_completion=str(target.get("supervision_target", "")).strip(),
        obligation_id=obligation_id,
        failed_attempt_id=failed_attempt_id,
        target_attempt_id=str(target.get("attempt_id", "")),
        failed_candidate_hash=str(failed.get("candidate_hash", "")),
        target_candidate_hash=str(target.get("candidate_hash", "")),
        verifier=str(failed.get("verifier", "")),
        verification_strength=str(failed.get("verification_strength", "unknown")),
        target_kernel_verified=bool(target.get("kernel_verified", False)),
        first_error=str(failed.get("first_error", "")),
        expected_lemmas=expected_lemmas,
        retrieved_obligations=retrieved_obligations,
        tags=tuple(str(item) for item in failed.get("tags", []) or []),
    )


def _prompt_for_repair(
    failed: dict[str, object],
    expected_lemmas: tuple[str, ...],
    retrieved_obligations: tuple[str, ...],
) -> str:
    expected = "\n".join(f"- {lemma}" for lemma in expected_lemmas) or "- none"
    retrieved = "\n".join(f"- {name}" for name in retrieved_obligations[:8]) or "- none"
    errors = "\n".join(f"- {error}" for error in failed.get("errors", []) or []) or "- none"
    tags = ", ".join(str(item) for item in failed.get("tags", []) or []) or "none"
    return "\n".join(
        [
            "You are repairing a failed Lean proof body in Mathlib.",
            "Return exactly the corrected Lean proof body that replaces `by sorry`.",
            "Do not include imports, theorem restatement, Markdown, or explanation.",
            "",
            f"Obligation: {failed.get('title', failed.get('obligation_id', ''))}",
            f"Tags: {tags}",
            "",
            "Expected useful lemmas:",
            expected,
            "",
            "Retrieved proof-bank neighbors:",
            retrieved,
            "",
            "Failed proof body:",
            "```lean",
            str(failed.get("proof_body", "")).strip() or "<empty>",
            "```",
            "",
            "Verifier errors:",
            errors,
            "",
            "Formal statement:",
            "```lean",
            str(failed.get("formal_statement", "")).strip(),
            "```",
        ]
    )


def _split_for_attempt(attempt_id: str, validation_fraction: float) -> str:
    if validation_fraction <= 0.0:
        return "train"
    bucket = int(stable_hash(attempt_id)[:12], 16) / float(0xFFFFFFFFFFFF)
    return "validation" if bucket < validation_fraction else "train"


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _write_jsonl(path: Path, rows: list[ProofRepairExample]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")

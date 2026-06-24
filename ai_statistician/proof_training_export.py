from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


PROOF_TRAINING_EXPORT_SCHEMA_VERSION = 1
PROOF_TRAINING_SOURCE_AWARE_EXPORT_POLICY = {
    "policy_id": "proof_training_source_aware_export_policy:1",
    "training_eligible_requirements": (
        "attempt ok",
        "non-empty supervision_target",
        "kernel_verified=true",
        "no sorry/admit/axiom/unsafe/unverified proof markers",
        "no wip/draft/prototype/placeholder/todo proof markers",
    ),
    "quarantine_policy": (
        "keep non-kernel or source-risk positives in compatibility SFT files",
        "publish them separately as quarantined positives for audit/review",
        "do not treat quarantined positives as publication-grade training promotion data",
    ),
    "negative_policy": (
        "failed attempts are exported as hard negatives for repair/value datasets",
        "failed attempts are not SFT completions",
    ),
    "proof_evidence_boundary": (
        "Training export eligibility is dataset provenance metadata. "
        "Only Lean-kernel-verified attempts are proof evidence."
    ),
}
_SOURCE_AWARE_HIGH_RISK_TOKENS = frozenset(
    {"admit", "admitted", "axiom", "sorry", "unsafe", "unverified"}
)
_SOURCE_AWARE_LOW_RISK_TOKENS = frozenset(
    {"draft", "placeholder", "prototype", "stub", "todo", "wip"}
)


@dataclass(frozen=True)
class ProofSftExample:
    schema_version: int
    example_id: str
    split: str
    task: str
    prompt: str
    completion: str
    obligation_id: str
    attempt_id: str
    candidate_hash: str
    verifier: str
    verification_strength: str
    kernel_verified: bool
    expected_lemmas: tuple[str, ...]
    retrieved_obligations: tuple[str, ...]
    tags: tuple[str, ...]
    source_aware_training_status: str
    source_aware_training_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ProofPremiseFeedbackExample:
    schema_version: int
    example_id: str
    split: str
    task: str
    label: str
    feedback_type: str
    attempt_id: str
    obligation_id: str
    candidate_premise_id: str
    candidate_premise_kind: str
    candidate_rank: int
    retrieval_score: float
    proof_outcome_ok: bool
    kernel_verified: bool
    verifier: str
    verification_strength: str
    first_error: str
    rationale: str
    proof_evidence_boundary: str


def export_proof_training_dataset(
    attempt_log: Path,
    out_dir: Path,
    *,
    validation_fraction: float = 0.2,
) -> dict[str, object]:
    """Export verifier-positive proof attempts as whole-proof SFT data.

    This is intentionally a dataset exporter, not a trainer. It converts the
    audit-oriented proof attempt log into a stable prompt/completion format that
    can feed a future SFT or rejection-sampling loop.
    """

    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0.0, 1.0)")
    attempts = _read_jsonl(attempt_log)
    positives = [
        row
        for row in attempts
        if row.get("ok") and str(row.get("supervision_target", "")).strip()
    ]
    examples = [
        _sft_example(row, split=_split_for_attempt(str(row["attempt_id"]), validation_fraction))
        for row in positives
    ]
    training_eligible = [
        row for row in examples if row.source_aware_training_status == "training_eligible"
    ]
    quarantined_positives = [
        row
        for row in examples
        if row.source_aware_training_status == "quarantined_positive"
    ]
    hard_negatives = [
        _hard_negative_row(row, split=_split_for_attempt(str(row.get("attempt_id", "")), validation_fraction))
        for row in attempts
        if not row.get("ok")
    ]
    premise_feedback = _premise_feedback_rows(
        attempts,
        validation_fraction=validation_fraction,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "proof_sft_train.jsonl"
    validation_path = out_dir / "proof_sft_validation.jsonl"
    all_path = out_dir / "proof_sft_all.jsonl"
    source_aware_train_path = out_dir / "proof_sft_source_aware_train.jsonl"
    source_aware_validation_path = out_dir / "proof_sft_source_aware_validation.jsonl"
    source_aware_all_path = out_dir / "proof_sft_source_aware_all.jsonl"
    quarantine_path = out_dir / "proof_sft_quarantined_positive.jsonl"
    hard_negative_path = out_dir / "proof_sft_hard_negatives.jsonl"
    premise_feedback_path = out_dir / "proof_premise_feedback.jsonl"
    _write_jsonl(train_path, [row for row in examples if row.split == "train"])
    _write_jsonl(validation_path, [row for row in examples if row.split == "validation"])
    _write_jsonl(all_path, examples)
    _write_jsonl(
        source_aware_train_path,
        [row for row in training_eligible if row.split == "train"],
    )
    _write_jsonl(
        source_aware_validation_path,
        [row for row in training_eligible if row.split == "validation"],
    )
    _write_jsonl(source_aware_all_path, training_eligible)
    _write_jsonl(quarantine_path, quarantined_positives)
    _write_jsonl(hard_negative_path, hard_negatives)
    _write_jsonl(premise_feedback_path, premise_feedback)
    by_source_aware_status = Counter(row.source_aware_training_status for row in examples)
    by_source_aware_reason = Counter(
        reason for row in examples for reason in row.source_aware_training_reasons
    )
    by_hard_negative_reason = Counter(
        reason for row in hard_negatives for reason in row.get("hard_negative_reasons", [])
    )
    by_premise_feedback_type = Counter(row.feedback_type for row in premise_feedback)
    by_premise_feedback_label = Counter(row.label for row in premise_feedback)
    manifest = {
        "schema_version": PROOF_TRAINING_EXPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_attempt_log": str(attempt_log),
        "source_attempt_log_fingerprint": stable_hash(attempts),
        "validation_fraction": validation_fraction,
        "n_attempts": len(attempts),
        "n_positive_attempts": len(positives),
        "n_kernel_positive_attempts": sum(1 for row in positives if row.get("kernel_verified")),
        "n_non_kernel_positive_attempts": sum(1 for row in positives if not row.get("kernel_verified")),
        "n_sft_examples": len(examples),
        "n_train": sum(1 for row in examples if row.split == "train"),
        "n_validation": sum(1 for row in examples if row.split == "validation"),
        "source_aware_training_export_policy": PROOF_TRAINING_SOURCE_AWARE_EXPORT_POLICY,
        "n_source_aware_training_eligible": len(training_eligible),
        "n_source_aware_training_quarantined_positive": len(quarantined_positives),
        "n_source_aware_training_hard_negative": len(hard_negatives),
        "n_premise_feedback_examples": len(premise_feedback),
        "n_positive_premise_feedback": by_premise_feedback_label.get("positive", 0),
        "n_hard_negative_premise_feedback": by_premise_feedback_label.get(
            "hard_negative",
            0,
        ),
        "n_source_aware_non_kernel_quarantined": by_source_aware_reason.get(
            "non_kernel_positive",
            0,
        ),
        "n_source_aware_forbidden_token_quarantined": by_source_aware_reason.get(
            "forbidden_proof_marker",
            0,
        ),
        "n_source_aware_wip_or_placeholder_quarantined": by_source_aware_reason.get(
            "wip_or_placeholder_marker",
            0,
        ),
        "by_source_aware_training_status": dict(sorted(by_source_aware_status.items())),
        "by_source_aware_training_reason": dict(sorted(by_source_aware_reason.items())),
        "by_hard_negative_reason": dict(sorted(by_hard_negative_reason.items())),
        "by_premise_feedback_type": dict(sorted(by_premise_feedback_type.items())),
        "by_premise_feedback_label": dict(sorted(by_premise_feedback_label.items())),
        "train_jsonl": str(train_path),
        "validation_jsonl": str(validation_path),
        "all_jsonl": str(all_path),
        "source_aware_train_jsonl": str(source_aware_train_path),
        "source_aware_validation_jsonl": str(source_aware_validation_path),
        "source_aware_all_jsonl": str(source_aware_all_path),
        "quarantined_positive_jsonl": str(quarantine_path),
        "hard_negative_jsonl": str(hard_negative_path),
        "premise_feedback_jsonl": str(premise_feedback_path),
        "dataset_fingerprint": stable_hash([asdict(row) for row in examples]),
        "source_aware_dataset_fingerprint": stable_hash(
            [asdict(row) for row in training_eligible]
        ),
        "quarantined_positive_fingerprint": stable_hash(
            [asdict(row) for row in quarantined_positives]
        ),
        "hard_negative_fingerprint": stable_hash(hard_negatives),
        "premise_feedback_fingerprint": stable_hash(
            [asdict(row) for row in premise_feedback]
        ),
        "limitations": [
            "whole-proof prompt/completion examples only",
            "examples retain verification_strength and kernel_verified so mock-positive data can be filtered downstream",
            "source-aware training files contain only kernel-verified non-placeholder positives",
            "quarantined positives remain review/tracing data, not publication-grade training promotion data",
            "no tactic-state transitions, process rewards, or proof-search traces",
            "negative proof attempts are exported as hard negatives for future repair/value datasets",
            "premise feedback infers used retrieved premises from proof text and expected-lemma metadata; ambiguous retrieved hits stay hard negatives until replay evidence confirms use",
        ],
    }
    manifest_path = out_dir / "proof_training_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _sft_example(row: dict[str, object], *, split: str) -> ProofSftExample:
    expected_lemmas = tuple(str(item) for item in row.get("expected_lemmas", []) or [])
    retrieval_hits = row.get("retrieval_hits", []) or []
    retrieved_obligations = tuple(
        str(hit.get("obligation_id", ""))
        for hit in retrieval_hits
        if isinstance(hit, dict) and hit.get("obligation_id")
    )
    attempt_id = str(row["attempt_id"])
    obligation_id = str(row["obligation_id"])
    source_aware_status, source_aware_reasons = _source_aware_training_decision(row)
    return ProofSftExample(
        schema_version=PROOF_TRAINING_EXPORT_SCHEMA_VERSION,
        example_id=f"{obligation_id}:{stable_hash(attempt_id)[:16]}",
        split=split,
        task="lean_whole_proof_body",
        prompt=_prompt_for_attempt(row, expected_lemmas, retrieved_obligations),
        completion=str(row["supervision_target"]).strip(),
        obligation_id=obligation_id,
        attempt_id=attempt_id,
        candidate_hash=str(row.get("candidate_hash", "")),
        verifier=str(row.get("verifier", "")),
        verification_strength=str(row.get("verification_strength", "unknown")),
        kernel_verified=bool(row.get("kernel_verified", False)),
        expected_lemmas=expected_lemmas,
        retrieved_obligations=retrieved_obligations,
        tags=tuple(str(item) for item in row.get("tags", []) or []),
        source_aware_training_status=source_aware_status,
        source_aware_training_reasons=source_aware_reasons,
    )


def _source_aware_training_decision(row: dict[str, object]) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    if not row.get("kernel_verified"):
        reasons.append("non_kernel_positive")
    if _has_high_risk_marker(row):
        reasons.append("forbidden_proof_marker")
    if _has_low_risk_marker(row):
        reasons.append("wip_or_placeholder_marker")
    if reasons:
        return "quarantined_positive", tuple(dict.fromkeys(reasons))
    return "training_eligible", ("kernel_verified_clean_positive",)


def _hard_negative_row(row: dict[str, object], *, split: str) -> dict[str, object]:
    retrieved_obligations = tuple(
        str(hit.get("obligation_id", ""))
        for hit in row.get("retrieval_hits", []) or []
        if isinstance(hit, dict) and hit.get("obligation_id")
    )
    reasons = ["failed_or_rejected_attempt"]
    if _has_high_risk_marker(row):
        reasons.append("forbidden_proof_marker")
    if _has_low_risk_marker(row):
        reasons.append("wip_or_placeholder_marker")
    attempt_id = str(row.get("attempt_id", ""))
    obligation_id = str(row.get("obligation_id", ""))
    return {
        "schema_version": PROOF_TRAINING_EXPORT_SCHEMA_VERSION,
        "negative_example_id": f"{obligation_id}:hard_negative:{stable_hash(attempt_id)[:16]}",
        "split": split,
        "task": "lean_whole_proof_hard_negative",
        "obligation_id": obligation_id,
        "attempt_id": attempt_id,
        "candidate_hash": str(row.get("candidate_hash", "")),
        "verifier": str(row.get("verifier", "")),
        "verification_strength": str(row.get("verification_strength", "unknown")),
        "kernel_verified": bool(row.get("kernel_verified", False)),
        "reward": float(row.get("reward", 0.0) or 0.0),
        "first_error": str(row.get("first_error", "")),
        "errors": tuple(str(item) for item in row.get("errors", []) or []),
        "expected_lemmas": tuple(str(item) for item in row.get("expected_lemmas", []) or []),
        "retrieved_obligations": retrieved_obligations,
        "tags": tuple(str(item) for item in row.get("tags", []) or []),
        "hard_negative_reasons": tuple(dict.fromkeys(reasons)),
        "proof_evidence_boundary": (
            "Hard negatives are verifier-feedback data, not proof evidence and not SFT completions."
        ),
    }


def _premise_feedback_rows(
    attempts: list[dict[str, object]],
    *,
    validation_fraction: float,
) -> list[ProofPremiseFeedbackExample]:
    rows: list[ProofPremiseFeedbackExample] = []
    seen: set[tuple[str, str, str, str]] = set()
    for attempt in attempts:
        attempt_id = str(attempt.get("attempt_id", ""))
        split = _split_for_attempt(attempt_id, validation_fraction)
        for expected_lemma in _str_tuple(attempt.get("expected_lemmas", [])):
            if not attempt.get("ok"):
                continue
            rows.append(
                _premise_feedback_row(
                    attempt,
                    split=split,
                    label="positive",
                    feedback_type="successful_expected_lemma",
                    candidate_premise_id=expected_lemma,
                    candidate_premise_kind="expected_lemma",
                    candidate_rank=0,
                    retrieval_score=0.0,
                    rationale="expected lemma from a successful proof attempt",
                )
            )
        for rank, hit in enumerate(_retrieval_hit_rows(attempt), start=1):
            premise_id = str(hit.get("obligation_id", ""))
            if not premise_id:
                continue
            used = bool(attempt.get("ok")) and _premise_used_by_successful_attempt(
                premise_id,
                attempt,
            )
            if used:
                label = "positive"
                feedback_type = "successful_retrieved_premise_used"
                rationale = "retrieved premise appears in successful proof context"
            elif attempt.get("ok"):
                label = "hard_negative"
                feedback_type = "retrieved_unused_in_successful_attempt"
                rationale = (
                    "retrieved premise was present but not used by the successful proof body"
                )
            else:
                label = "hard_negative"
                feedback_type = "retrieved_from_failed_attempt"
                rationale = "retrieved premise came from a failed or rejected proof attempt"
            rows.append(
                _premise_feedback_row(
                    attempt,
                    split=split,
                    label=label,
                    feedback_type=feedback_type,
                    candidate_premise_id=premise_id,
                    candidate_premise_kind="retrieved_obligation",
                    candidate_rank=rank,
                    retrieval_score=float(hit.get("score", 0.0) or 0.0),
                    rationale=rationale,
                )
            )
    compact: list[ProofPremiseFeedbackExample] = []
    for row in rows:
        key = (row.attempt_id, row.label, row.feedback_type, row.candidate_premise_id)
        if key in seen:
            continue
        seen.add(key)
        compact.append(row)
    return compact


def _premise_feedback_row(
    attempt: dict[str, object],
    *,
    split: str,
    label: str,
    feedback_type: str,
    candidate_premise_id: str,
    candidate_premise_kind: str,
    candidate_rank: int,
    retrieval_score: float,
    rationale: str,
) -> ProofPremiseFeedbackExample:
    attempt_id = str(attempt.get("attempt_id", ""))
    obligation_id = str(attempt.get("obligation_id", ""))
    return ProofPremiseFeedbackExample(
        schema_version=PROOF_TRAINING_EXPORT_SCHEMA_VERSION,
        example_id=(
            f"{obligation_id}:premise_feedback:"
            f"{stable_hash([attempt_id, label, feedback_type, candidate_premise_id])[:16]}"
        ),
        split=split,
        task="lean_premise_feedback",
        label=label,
        feedback_type=feedback_type,
        attempt_id=attempt_id,
        obligation_id=obligation_id,
        candidate_premise_id=candidate_premise_id,
        candidate_premise_kind=candidate_premise_kind,
        candidate_rank=candidate_rank,
        retrieval_score=retrieval_score,
        proof_outcome_ok=bool(attempt.get("ok", False)),
        kernel_verified=bool(attempt.get("kernel_verified", False)),
        verifier=str(attempt.get("verifier", "")),
        verification_strength=str(attempt.get("verification_strength", "unknown")),
        first_error=str(attempt.get("first_error", "")),
        rationale=rationale,
        proof_evidence_boundary=(
            "Premise feedback rows are training labels derived from verifier outcomes. "
            "They are not theorem proof evidence."
        ),
    )


def _premise_used_by_successful_attempt(
    premise_id: str,
    attempt: dict[str, object],
) -> bool:
    normalized = _normalized_text(premise_id)
    proof_text = _normalized_text(
        " ".join(
            (
                str(attempt.get("supervision_target", "")),
                str(attempt.get("proof_body", "")),
                str(attempt.get("candidate", "")),
            )
        )
    )
    expected_text = _normalized_text(" ".join(_str_tuple(attempt.get("expected_lemmas", []))))
    return bool(normalized and (normalized in proof_text or normalized in expected_text))


def _retrieval_hit_rows(row: dict[str, object]) -> tuple[dict[str, object], ...]:
    hits = row.get("retrieval_hits", []) or []
    if not isinstance(hits, (list, tuple)):
        return ()
    return tuple(hit for hit in hits if isinstance(hit, dict))


def _normalized_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _str_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if not isinstance(value, (list, tuple, set)):
        return ()
    return tuple(str(item) for item in value if str(item))


def _has_high_risk_marker(row: dict[str, object]) -> bool:
    return bool(_quality_tokens(_quality_text(row)) & _SOURCE_AWARE_HIGH_RISK_TOKENS)


def _has_low_risk_marker(row: dict[str, object]) -> bool:
    return bool(_quality_tokens(_quality_text(row)) & _SOURCE_AWARE_LOW_RISK_TOKENS)


def _quality_text(row: dict[str, object]) -> str:
    pieces: list[str] = []
    for key in (
        "supervision_target",
        "proof_body",
        "formal_statement",
        "candidate",
        "candidate_hash",
        "first_error",
        "verification_strength",
    ):
        pieces.append(str(row.get(key, "")))
    pieces.extend(str(item) for item in row.get("errors", []) or [])
    pieces.extend(str(item) for item in row.get("tags", []) or [])
    pieces.extend(str(item) for item in row.get("expected_lemmas", []) or [])
    for hit in row.get("retrieval_hits", []) or []:
        if isinstance(hit, dict):
            pieces.extend(str(value) for value in hit.values())
    return " ".join(piece for piece in pieces if piece)


def _quality_tokens(text: str) -> set[str]:
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return {token for token in re.split(r"[^a-z0-9]+|_", expanded.lower()) if token}


def _prompt_for_attempt(
    row: dict[str, object],
    expected_lemmas: tuple[str, ...],
    retrieved_obligations: tuple[str, ...],
) -> str:
    expected = "\n".join(f"- {lemma}" for lemma in expected_lemmas) or "- none"
    retrieved = "\n".join(f"- {name}" for name in retrieved_obligations[:8]) or "- none"
    tags = ", ".join(str(item) for item in row.get("tags", []) or []) or "none"
    return "\n".join(
        [
            "You are proving a Lean theorem in Mathlib.",
            "Return exactly the Lean proof body that replaces `by sorry`.",
            "Do not include imports, theorem restatement, Markdown, or explanation.",
            "",
            f"Obligation: {row.get('title', row.get('obligation_id', ''))}",
            f"Tags: {tags}",
            "",
            "Expected useful lemmas:",
            expected,
            "",
            "Retrieved proof-bank neighbors:",
            retrieved,
            "",
            "Formal statement:",
            "```lean",
            str(row["formal_statement"]).strip(),
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


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_jsonable_row(row), default=str) + "\n")


def _jsonable_row(row: Any) -> dict[str, object]:
    if is_dataclass(row):
        return asdict(row)
    if isinstance(row, dict):
        return row
    return {"value": row}

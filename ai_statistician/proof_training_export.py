from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash


PROOF_TRAINING_EXPORT_SCHEMA_VERSION = 1


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
    expected_lemmas: tuple[str, ...]
    retrieved_obligations: tuple[str, ...]
    tags: tuple[str, ...]


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
    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "proof_sft_train.jsonl"
    validation_path = out_dir / "proof_sft_validation.jsonl"
    all_path = out_dir / "proof_sft_all.jsonl"
    _write_jsonl(train_path, [row for row in examples if row.split == "train"])
    _write_jsonl(validation_path, [row for row in examples if row.split == "validation"])
    _write_jsonl(all_path, examples)
    manifest = {
        "schema_version": PROOF_TRAINING_EXPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_attempt_log": str(attempt_log),
        "source_attempt_log_fingerprint": stable_hash(attempts),
        "validation_fraction": validation_fraction,
        "n_attempts": len(attempts),
        "n_positive_attempts": len(positives),
        "n_sft_examples": len(examples),
        "n_train": sum(1 for row in examples if row.split == "train"),
        "n_validation": sum(1 for row in examples if row.split == "validation"),
        "train_jsonl": str(train_path),
        "validation_jsonl": str(validation_path),
        "all_jsonl": str(all_path),
        "dataset_fingerprint": stable_hash([asdict(row) for row in examples]),
        "limitations": [
            "whole-proof prompt/completion examples only",
            "no tactic-state transitions, process rewards, or proof-search traces",
            "negative proof attempts are not used for SFT targets; keep them for future repair/value datasets",
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
        expected_lemmas=expected_lemmas,
        retrieved_obligations=retrieved_obligations,
        tags=tuple(str(item) for item in row.get("tags", []) or []),
    )


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


def _write_jsonl(path: Path, rows: list[ProofSftExample]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")

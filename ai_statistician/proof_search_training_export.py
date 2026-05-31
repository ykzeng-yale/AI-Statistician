from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .proof_bank import all_obligations, proof_bank_fingerprint


PROOF_SEARCH_TRAINING_EXPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProofSearchProcessExample:
    schema_version: int
    example_id: str
    split: str
    task: str
    prompt: str
    completion: str
    obligation_id: str
    node_id: str
    candidate_id: str
    candidate_source: str
    candidate_score: float
    expanded_index: int
    reward: float
    node_ok: bool
    kernel_verified: bool
    verifier: str
    verification_strength: str
    first_error: str
    errors: tuple[str, ...]
    selected_candidate_id: str
    search_fingerprint: str


def export_proof_search_process_dataset(
    proof_search_results_jsonl: Path,
    out_dir: Path,
    *,
    validation_fraction: float = 0.2,
) -> dict[str, object]:
    """Export proof-search expanded nodes as process-reward/value data."""

    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0.0, 1.0)")
    results = _read_jsonl(proof_search_results_jsonl)
    obligations = {row.id: row for row in all_obligations()}
    examples: list[ProofSearchProcessExample] = []
    for result in results:
        obligation_id = str(result.get("obligation_id", ""))
        obligation = obligations.get(obligation_id)
        if obligation is None:
            continue
        for node in result.get("nodes", []) or []:
            if not isinstance(node, dict):
                continue
            example_id = (
                f"{obligation_id}:{node.get('node_id', '')}:"
                f"{stable_hash([result.get('search_fingerprint', ''), node])[:16]}"
            )
            errors = tuple(str(item) for item in node.get("errors", []) or [])
            reward = 1.0 if node.get("ok") else 0.0
            examples.append(
                ProofSearchProcessExample(
                    schema_version=PROOF_SEARCH_TRAINING_EXPORT_SCHEMA_VERSION,
                    example_id=example_id,
                    split=_split_for_example(example_id, validation_fraction),
                    task="lean_whole_proof_process_reward",
                    prompt=_prompt_for_node(obligation, node),
                    completion=json.dumps(
                        {
                            "reward": reward,
                            "ok": bool(node.get("ok")),
                            "kernel_verified": bool(node.get("kernel_verified")),
                            "first_error": errors[0] if errors else "",
                            "selected_candidate": node.get("candidate_id")
                            == result.get("selected_candidate_id"),
                        },
                        sort_keys=True,
                    ),
                    obligation_id=obligation_id,
                    node_id=str(node.get("node_id", "")),
                    candidate_id=str(node.get("candidate_id", "")),
                    candidate_source=str(node.get("source", "")),
                    candidate_score=float(node.get("score", 0.0) or 0.0),
                    expanded_index=int(node.get("expanded_index", 0) or 0),
                    reward=reward,
                    node_ok=bool(node.get("ok")),
                    kernel_verified=bool(node.get("kernel_verified")),
                    verifier=str(node.get("verifier", "")),
                    verification_strength=str(node.get("verification_strength", "")),
                    first_error=errors[0] if errors else "",
                    errors=errors,
                    selected_candidate_id=str(result.get("selected_candidate_id", "")),
                    search_fingerprint=str(result.get("search_fingerprint", "")),
                )
            )
    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "proof_search_process_train.jsonl"
    validation_path = out_dir / "proof_search_process_validation.jsonl"
    all_path = out_dir / "proof_search_process_all.jsonl"
    _write_jsonl(train_path, [row for row in examples if row.split == "train"])
    _write_jsonl(validation_path, [row for row in examples if row.split == "validation"])
    _write_jsonl(all_path, examples)
    manifest = {
        "schema_version": PROOF_SEARCH_TRAINING_EXPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "source_results_jsonl": str(proof_search_results_jsonl),
        "source_results_fingerprint": stable_hash(results),
        "validation_fraction": validation_fraction,
        "n_search_results": len(results),
        "n_process_examples": len(examples),
        "n_positive": sum(1 for row in examples if row.node_ok),
        "n_negative": sum(1 for row in examples if not row.node_ok),
        "n_kernel_positive": sum(1 for row in examples if row.node_ok and row.kernel_verified),
        "n_train": sum(1 for row in examples if row.split == "train"),
        "n_validation": sum(1 for row in examples if row.split == "validation"),
        "train_jsonl": str(train_path),
        "validation_jsonl": str(validation_path),
        "all_jsonl": str(all_path),
        "dataset_fingerprint": stable_hash([asdict(row) for row in examples]),
        "limitations": [
            "whole-proof node process labels only; no Lean tactic-state transitions yet",
            "reward is verifier binary outcome for an expanded candidate proof body",
            "negative examples require failed expanded nodes, such as invalid probes or failed generated candidates",
            "this is a dataset export for future value/reward models, not model training",
        ],
    }
    manifest_path = out_dir / "proof_search_training_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _prompt_for_node(obligation, node: dict[str, object]) -> str:
    expected = "\n".join(f"- {lemma}" for lemma in obligation.expected_lemmas) or "- none"
    errors = "\n".join(f"- {err}" for err in node.get("errors", []) or []) or "- none"
    return "\n".join(
        [
            "You are evaluating one Lean whole-proof candidate under verifier feedback.",
            "Predict whether the candidate should receive positive process reward.",
            "",
            f"Obligation: {obligation.title}",
            f"Tags: {', '.join(obligation.tags) or 'none'}",
            "",
            "Expected useful lemmas:",
            expected,
            "",
            "Formal statement:",
            "```lean",
            obligation.formal_statement.strip(),
            "```",
            "",
            f"Candidate source: {node.get('source', '')}",
            f"Candidate score: {node.get('score', 0.0)}",
            "Candidate proof body:",
            "```lean",
            str(node.get("proof_body", "")).strip(),
            "```",
            "",
            "Verifier errors observed for this candidate:",
            errors,
        ]
    )


def _split_for_example(example_id: str, validation_fraction: float) -> str:
    if validation_fraction <= 0.0:
        return "train"
    bucket = int(stable_hash(example_id)[:12], 16) / float(0xFFFFFFFFFFFF)
    return "validation" if bucket < validation_fraction else "train"


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _write_jsonl(path: Path, rows: list[ProofSearchProcessExample]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")

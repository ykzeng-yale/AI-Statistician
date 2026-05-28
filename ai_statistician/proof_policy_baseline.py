from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .retrieval import tokens


PROOF_POLICY_BASELINE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProofPolicyBaselinePrediction:
    example_id: str
    obligation_id: str
    gold_completion: str
    predicted_completion: str
    predicted_from_example_id: str
    predicted_from_obligation_id: str
    score: float
    exact_match: bool
    predicted_in_retrieved_context: bool
    top_k_exact_match: bool
    top_k_obligations: tuple[str, ...]


def evaluate_retrieval_proof_policy_baseline(
    train_jsonl: Path,
    validation_jsonl: Path,
    out_dir: Path,
    *,
    k: int = 5,
) -> dict[str, object]:
    """Evaluate a deterministic nearest-neighbor whole-proof baseline.

    This is not a neural prover and it does not call Lean. It answers the first
    training question: how far does a simple proof-memory policy get before we
    train any model? Future SFT/RL systems should beat this baseline.
    """

    if k <= 0:
        raise ValueError("k must be positive")
    train = _read_jsonl(train_jsonl)
    validation = _read_jsonl(validation_jsonl)
    predictions = [_predict(row, train, k=k) for row in validation]
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "proof_policy_baseline_predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as handle:
        for row in predictions:
            handle.write(json.dumps(asdict(row), default=str) + "\n")
    n = len(predictions)
    exact = sum(1 for row in predictions if row.exact_match)
    top_k_exact = sum(1 for row in predictions if row.top_k_exact_match)
    context_hits = sum(1 for row in predictions if row.predicted_in_retrieved_context)
    manifest = {
        "schema_version": PROOF_POLICY_BASELINE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train_jsonl": str(train_jsonl),
        "validation_jsonl": str(validation_jsonl),
        "train_fingerprint": stable_hash(train),
        "validation_fingerprint": stable_hash(validation),
        "k": k,
        "n_train": len(train),
        "n_validation": len(validation),
        "top1_exact": exact,
        "top_k_exact": top_k_exact,
        "top1_exact_rate": exact / n if n else 0.0,
        "top_k_exact_rate": top_k_exact / n if n else 0.0,
        "predicted_in_retrieved_context": context_hits,
        "predicted_in_retrieved_context_rate": context_hits / n if n else 0.0,
        "mean_top1_score": sum(row.score for row in predictions) / n if n else 0.0,
        "predictions_jsonl": str(predictions_path),
        "baseline_fingerprint": stable_hash([asdict(row) for row in predictions]),
        "limitations": [
            "nearest-neighbor proof-body memory baseline only",
            "does not verify predicted completions in Lean",
            "intended as a no-training baseline for future SFT/RL systems to beat",
        ],
    }
    manifest_path = out_dir / "proof_policy_baseline_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _predict(
    validation_row: dict[str, object],
    train_rows: list[dict[str, object]],
    *,
    k: int,
) -> ProofPolicyBaselinePrediction:
    scored = sorted(
        ((_example_score(validation_row, row), row) for row in train_rows),
        key=lambda item: (-item[0], str(item[1].get("example_id", ""))),
    )
    top = scored[:k]
    best_score, best = top[0] if top else (0.0, {})
    gold = str(validation_row.get("completion", "")).strip()
    predicted = str(best.get("completion", "")).strip()
    validation_context = {
        str(item)
        for item in validation_row.get("retrieved_obligations", []) or []
    }
    top_k_obligations = tuple(str(row.get("obligation_id", "")) for _score, row in top)
    return ProofPolicyBaselinePrediction(
        example_id=str(validation_row.get("example_id", "")),
        obligation_id=str(validation_row.get("obligation_id", "")),
        gold_completion=gold,
        predicted_completion=predicted,
        predicted_from_example_id=str(best.get("example_id", "")),
        predicted_from_obligation_id=str(best.get("obligation_id", "")),
        score=round(float(best_score), 6),
        exact_match=bool(predicted and predicted == gold),
        predicted_in_retrieved_context=str(best.get("obligation_id", "")) in validation_context,
        top_k_exact_match=any(str(row.get("completion", "")).strip() == gold for _score, row in top),
        top_k_obligations=top_k_obligations,
    )


def _example_score(query: dict[str, object], candidate: dict[str, object]) -> float:
    q_expected = {str(item).lower() for item in query.get("expected_lemmas", []) or []}
    c_expected = {str(item).lower() for item in candidate.get("expected_lemmas", []) or []}
    q_tags = {str(item).lower() for item in query.get("tags", []) or []}
    c_tags = {str(item).lower() for item in candidate.get("tags", []) or []}
    q_neighbors = {str(item).lower() for item in query.get("retrieved_obligations", []) or []}
    c_obligation = str(candidate.get("obligation_id", "")).lower()
    q_tokens = tokens(
        " ".join(
            [
                str(query.get("prompt", "")),
                " ".join(query.get("expected_lemmas", []) or []),
                " ".join(query.get("tags", []) or []),
            ]
        )
    )
    c_tokens = tokens(
        " ".join(
            [
                str(candidate.get("prompt", "")),
                " ".join(candidate.get("expected_lemmas", []) or []),
                " ".join(candidate.get("tags", []) or []),
            ]
        )
    )
    overlap = len(q_tokens & c_tokens)
    expected_overlap = len(q_expected & c_expected)
    tag_overlap = len(q_tags & c_tags)
    neighbor_bonus = 1 if c_obligation in q_neighbors else 0
    return overlap + 4.0 * expected_overlap + 3.0 * tag_overlap + 2.0 * neighbor_bonus


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows

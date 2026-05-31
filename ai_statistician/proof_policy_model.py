from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .retrieval import tokens


PROOF_POLICY_MODEL_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProofPolicyPrediction:
    example_id: str
    obligation_id: str
    gold_completion: str
    predicted_completion: str
    predicted_from_example_id: str
    predicted_from_obligation_id: str
    score: float
    exact_match: bool
    top_k_exact_match: bool
    top_k_obligations: tuple[str, ...]


@dataclass(frozen=True)
class ProofPolicyModel:
    schema_version: int
    model_type: str
    feature_names: tuple[str, ...]
    weights: dict[str, float]
    model_fingerprint: str

    def score(self, query: dict[str, object], candidate: dict[str, object]) -> float:
        """Return a learned whole-proof ranking score in [0, 1]."""

        return _sigmoid(_dot(self.weights, _features(query, candidate)))


def load_proof_policy_model(model_json: Path) -> ProofPolicyModel:
    """Load a trained whole-proof policy ranker."""

    payload = json.loads(model_json.read_text(encoding="utf-8"))
    if int(payload.get("schema_version", -1)) != PROOF_POLICY_MODEL_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported proof policy model schema_version={payload.get('schema_version')!r}"
        )
    model_type = str(payload.get("model_type", ""))
    if model_type != "logistic_whole_proof_ranker":
        raise ValueError(f"unsupported proof policy model_type={model_type!r}")
    weights = {str(key): float(value) for key, value in dict(payload.get("weights", {})).items()}
    feature_names = tuple(str(item) for item in payload.get("feature_names", []) or [])
    missing = [name for name in feature_names if name not in weights]
    if missing:
        raise ValueError(f"proof policy model missing weights for features: {missing}")
    return ProofPolicyModel(
        schema_version=PROOF_POLICY_MODEL_SCHEMA_VERSION,
        model_type=model_type,
        feature_names=feature_names,
        weights=weights,
        model_fingerprint=stable_hash(payload),
    )


def train_proof_policy_model(
    train_jsonl: Path,
    out_dir: Path,
    *,
    validation_jsonl: Path | None = None,
    k: int = 5,
    epochs: int = 80,
    learning_rate: float = 0.1,
    l2: float = 0.001,
    negatives_per_query: int = 8,
) -> dict[str, object]:
    """Train a small whole-proof candidate ranking baseline.

    This is a deterministic feature model over proof SFT examples. It is not a
    neural tactic policy, but it is a real trained policy layer that learns how
    to rank stored proof-body candidates from theorem/premise features.
    """

    if k <= 0:
        raise ValueError("k must be positive")
    if epochs <= 0:
        raise ValueError("epochs must be positive")
    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    train = _read_jsonl(train_jsonl)
    validation = _read_jsonl(validation_jsonl) if validation_jsonl else list(train)
    feature_names = _feature_names()
    weights = {name: 0.0 for name in feature_names}
    pairs = _training_pairs(train, negatives_per_query=negatives_per_query)
    for _epoch in range(epochs):
        for query, candidate, label in pairs:
            features = _features(query, candidate)
            score = _sigmoid(_dot(weights, features))
            error = score - label
            for name in feature_names:
                weights[name] -= learning_rate * (error * features.get(name, 0.0) + l2 * weights[name])
    predictions = [_predict(row, train, weights, k=k) for row in validation]
    train_predictions = [_predict(row, train, weights, k=k) for row in train]
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "proof_policy_model_predictions.jsonl"
    train_predictions_path = out_dir / "proof_policy_model_train_predictions.jsonl"
    _write_jsonl(predictions_path, predictions)
    _write_jsonl(train_predictions_path, train_predictions)
    model = {
        "schema_version": PROOF_POLICY_MODEL_SCHEMA_VERSION,
        "model_type": "logistic_whole_proof_ranker",
        "feature_names": feature_names,
        "weights": weights,
        "k": k,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "l2": l2,
        "negatives_per_query": negatives_per_query,
    }
    model_path = out_dir / "proof_policy_model.json"
    model_path.write_text(json.dumps(model, indent=2, sort_keys=True), encoding="utf-8")
    n_val = len(predictions)
    n_train = len(train_predictions)
    manifest = {
        "schema_version": PROOF_POLICY_MODEL_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train_jsonl": str(train_jsonl),
        "validation_jsonl": str(validation_jsonl) if validation_jsonl else str(train_jsonl),
        "train_fingerprint": stable_hash(train),
        "validation_fingerprint": stable_hash(validation),
        "k": k,
        "epochs": epochs,
        "n_train": len(train),
        "n_validation": len(validation),
        "n_training_pairs": len(pairs),
        "n_features": len(feature_names),
        "train_top1_exact": sum(1 for row in train_predictions if row.exact_match),
        "train_top_k_exact": sum(1 for row in train_predictions if row.top_k_exact_match),
        "train_top1_exact_rate": (
            sum(1 for row in train_predictions if row.exact_match) / n_train if n_train else 0.0
        ),
        "train_top_k_exact_rate": (
            sum(1 for row in train_predictions if row.top_k_exact_match) / n_train if n_train else 0.0
        ),
        "validation_top1_exact": sum(1 for row in predictions if row.exact_match),
        "validation_top_k_exact": sum(1 for row in predictions if row.top_k_exact_match),
        "validation_top1_exact_rate": (
            sum(1 for row in predictions if row.exact_match) / n_val if n_val else 0.0
        ),
        "validation_top_k_exact_rate": (
            sum(1 for row in predictions if row.top_k_exact_match) / n_val if n_val else 0.0
        ),
        "model_json": str(model_path),
        "predictions_jsonl": str(predictions_path),
        "train_predictions_jsonl": str(train_predictions_path),
        "model_fingerprint": stable_hash(model),
        "limitations": [
            "feature-trained whole-proof proof-memory ranker, not a neural prover",
            "does not generate novel proof syntax beyond ranking known proof bodies",
            "validation exact-match can be low when held-out proofs are genuinely novel",
            "intended as a trainable policy baseline before tactic-state policy learning",
        ],
    }
    manifest_path = out_dir / "proof_policy_model_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _feature_names() -> list[str]:
    return [
        "bias",
        "token_overlap",
        "expected_overlap",
        "tag_overlap",
        "retrieved_neighbor",
        "same_obligation_id",
        "same_completion_hash",
        "candidate_completion_short",
        "candidate_uses_simpa",
        "candidate_uses_exact",
        "candidate_uses_rw",
    ]


def _training_pairs(
    train: list[dict[str, object]],
    *,
    negatives_per_query: int,
) -> list[tuple[dict[str, object], dict[str, object], float]]:
    pairs: list[tuple[dict[str, object], dict[str, object], float]] = []
    if not train:
        return pairs
    ordered = sorted(train, key=lambda row: str(row.get("example_id", "")))
    for idx, query in enumerate(ordered):
        pairs.append((query, query, 1.0))
        n_added = 0
        offset = 1
        while n_added < negatives_per_query and offset < len(ordered):
            candidate = ordered[(idx + offset) % len(ordered)]
            offset += 1
            if candidate.get("example_id") == query.get("example_id"):
                continue
            pairs.append((query, candidate, 0.0))
            n_added += 1
    return pairs


def _predict(
    query: dict[str, object],
    candidates: list[dict[str, object]],
    weights: dict[str, float],
    *,
    k: int,
) -> ProofPolicyPrediction:
    ranked = sorted(
        ((_sigmoid(_dot(weights, _features(query, candidate))), candidate) for candidate in candidates),
        key=lambda item: (-item[0], str(item[1].get("example_id", ""))),
    )
    top = ranked[:k]
    best_score, best = top[0] if top else (0.0, {})
    gold = str(query.get("completion", "")).strip()
    predicted = str(best.get("completion", "")).strip()
    return ProofPolicyPrediction(
        example_id=str(query.get("example_id", "")),
        obligation_id=str(query.get("obligation_id", "")),
        gold_completion=gold,
        predicted_completion=predicted,
        predicted_from_example_id=str(best.get("example_id", "")),
        predicted_from_obligation_id=str(best.get("obligation_id", "")),
        score=round(float(best_score), 6),
        exact_match=bool(predicted and predicted == gold),
        top_k_exact_match=any(str(row.get("completion", "")).strip() == gold for _score, row in top),
        top_k_obligations=tuple(str(row.get("obligation_id", "")) for _score, row in top),
    )


def _features(query: dict[str, object], candidate: dict[str, object]) -> dict[str, float]:
    q_expected = {str(item).lower() for item in query.get("expected_lemmas", []) or []}
    c_expected = {str(item).lower() for item in candidate.get("expected_lemmas", []) or []}
    q_tags = {str(item).lower() for item in query.get("tags", []) or []}
    c_tags = {str(item).lower() for item in candidate.get("tags", []) or []}
    q_tokens = tokens(str(query.get("prompt", "")))
    c_tokens = tokens(str(candidate.get("prompt", "")))
    retrieved = {str(item).lower() for item in query.get("retrieved_obligations", []) or []}
    candidate_obligation = str(candidate.get("obligation_id", "")).lower()
    completion = str(candidate.get("completion", ""))
    return {
        "bias": 1.0,
        "token_overlap": len(q_tokens & c_tokens) / max(1.0, len(q_tokens | c_tokens)),
        "expected_overlap": len(q_expected & c_expected) / max(1.0, len(q_expected | c_expected)),
        "tag_overlap": len(q_tags & c_tags) / max(1.0, len(q_tags | c_tags)),
        "retrieved_neighbor": 1.0 if candidate_obligation in retrieved else 0.0,
        "same_obligation_id": 1.0 if query.get("obligation_id") == candidate.get("obligation_id") else 0.0,
        "same_completion_hash": 1.0 if query.get("completion") == candidate.get("completion") else 0.0,
        "candidate_completion_short": 1.0 if len(completion) < 180 else 0.0,
        "candidate_uses_simpa": 1.0 if "simpa" in completion else 0.0,
        "candidate_uses_exact": 1.0 if "exact" in completion else 0.0,
        "candidate_uses_rw": 1.0 if "rw" in completion else 0.0,
    }


def _dot(weights: dict[str, float], features: dict[str, float]) -> float:
    return sum(weights.get(name, 0.0) * features.get(name, 0.0) for name in weights)


def _sigmoid(value: float) -> float:
    if value >= 40:
        return 1.0
    if value <= -40:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def _read_jsonl(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        return []
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _write_jsonl(path: Path, rows: list[ProofPolicyPrediction]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")

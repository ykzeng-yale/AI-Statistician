from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash


PROOF_SEARCH_VALUE_MODEL_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ValueModelPrediction:
    example_id: str
    split: str
    obligation_id: str
    candidate_id: str
    label: float
    score: float
    prediction: int
    correct: bool


def train_proof_search_value_model(
    train_jsonl: Path,
    out_dir: Path,
    *,
    validation_jsonl: Path | None = None,
    epochs: int = 200,
    learning_rate: float = 0.2,
    l2: float = 0.001,
) -> dict[str, object]:
    """Train a small logistic proof-search value baseline.

    This is deliberately lightweight: it proves that the system can consume
    verifier-labeled process data and fit a reproducible value model, without
    claiming neural prover capability.
    """

    if epochs <= 0:
        raise ValueError("epochs must be positive")
    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    train_rows = _read_jsonl(train_jsonl)
    validation_rows = _read_jsonl(validation_jsonl) if validation_jsonl else list(train_rows)
    feature_names = _feature_names()
    weights = {name: 0.0 for name in feature_names}
    train_xy = [(_features(row), float(row.get("reward", 0.0))) for row in train_rows]
    for _epoch in range(epochs):
        for features, label in train_xy:
            score = _sigmoid(_dot(weights, features))
            error = score - label
            for name in feature_names:
                weights[name] -= learning_rate * (error * features.get(name, 0.0) + l2 * weights[name])
    train_predictions = _predict_rows(train_rows, weights, split="train")
    validation_predictions = _predict_rows(validation_rows, weights, split="validation")
    out_dir.mkdir(parents=True, exist_ok=True)
    train_pred_path = out_dir / "proof_search_value_train_predictions.jsonl"
    validation_pred_path = out_dir / "proof_search_value_validation_predictions.jsonl"
    _write_jsonl(train_pred_path, train_predictions)
    _write_jsonl(validation_pred_path, validation_predictions)
    model = {
        "schema_version": PROOF_SEARCH_VALUE_MODEL_SCHEMA_VERSION,
        "model_type": "logistic_feature_baseline",
        "feature_names": feature_names,
        "weights": weights,
        "threshold": 0.5,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "l2": l2,
    }
    model_path = out_dir / "proof_search_value_model.json"
    model_path.write_text(json.dumps(model, indent=2, sort_keys=True), encoding="utf-8")
    manifest = {
        "schema_version": PROOF_SEARCH_VALUE_MODEL_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train_jsonl": str(train_jsonl),
        "validation_jsonl": str(validation_jsonl) if validation_jsonl else str(train_jsonl),
        "train_fingerprint": stable_hash(train_rows),
        "validation_fingerprint": stable_hash(validation_rows),
        "n_train": len(train_rows),
        "n_validation": len(validation_rows),
        "n_train_positive": sum(1 for row in train_rows if float(row.get("reward", 0.0)) >= 0.5),
        "n_train_negative": sum(1 for row in train_rows if float(row.get("reward", 0.0)) < 0.5),
        "n_validation_positive": sum(1 for row in validation_rows if float(row.get("reward", 0.0)) >= 0.5),
        "n_validation_negative": sum(1 for row in validation_rows if float(row.get("reward", 0.0)) < 0.5),
        "n_features": len(feature_names),
        "train_accuracy": _accuracy(train_predictions),
        "validation_accuracy": _accuracy(validation_predictions),
        "train_log_loss": _log_loss(train_predictions),
        "validation_log_loss": _log_loss(validation_predictions),
        "model_json": str(model_path),
        "train_predictions_jsonl": str(train_pred_path),
        "validation_predictions_jsonl": str(validation_pred_path),
        "model_fingerprint": stable_hash(model),
        "limitations": [
            "small deterministic logistic feature baseline, not a neural prover",
            "uses whole-proof process examples, not tactic-state proof states",
            "quality depends on having both failed and successful expanded proof-search nodes",
            "intended as a trainer smoke test and value-model baseline for future learned search",
        ],
    }
    manifest_path = out_dir / "proof_search_value_model_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _feature_names() -> list[str]:
    return [
        "bias",
        "candidate_score_scaled",
        "expanded_index_scaled",
        "source_registered",
        "source_expected_lemma",
        "source_memory",
        "source_invalid_probe",
        "body_contains_sorry",
        "body_contains_exact",
        "body_contains_simpa",
        "has_errors",
        "first_error_mentions_sorry",
    ]


def _features(row: dict[str, object]) -> dict[str, float]:
    source = str(row.get("candidate_source", ""))
    body = str(row.get("prompt", ""))
    first_error = str(row.get("first_error", ""))
    return {
        "bias": 1.0,
        "candidate_score_scaled": float(row.get("candidate_score", 0.0) or 0.0) / 1000.0,
        "expanded_index_scaled": float(row.get("expanded_index", 0) or 0) / 10.0,
        "source_registered": 1.0 if source == "registered_proof_body" else 0.0,
        "source_expected_lemma": 1.0 if source == "expected_lemma_template" else 0.0,
        "source_memory": 1.0 if source.startswith("proof_memory:") else 0.0,
        "source_invalid_probe": 1.0 if source == "invalid_probe" else 0.0,
        "body_contains_sorry": 1.0 if "sorry" in body else 0.0,
        "body_contains_exact": 1.0 if "exact" in body else 0.0,
        "body_contains_simpa": 1.0 if "simpa" in body else 0.0,
        "has_errors": 1.0 if row.get("errors") else 0.0,
        "first_error_mentions_sorry": 1.0 if "sorry" in first_error.lower() else 0.0,
    }


def _predict_rows(
    rows: list[dict[str, object]],
    weights: dict[str, float],
    *,
    split: str,
) -> list[ValueModelPrediction]:
    predictions: list[ValueModelPrediction] = []
    for row in rows:
        label = float(row.get("reward", 0.0) or 0.0)
        score = _sigmoid(_dot(weights, _features(row)))
        prediction = 1 if score >= 0.5 else 0
        predictions.append(
            ValueModelPrediction(
                example_id=str(row.get("example_id", "")),
                split=split,
                obligation_id=str(row.get("obligation_id", "")),
                candidate_id=str(row.get("candidate_id", "")),
                label=label,
                score=round(score, 6),
                prediction=prediction,
                correct=prediction == int(label >= 0.5),
            )
        )
    return predictions


def _dot(weights: dict[str, float], features: dict[str, float]) -> float:
    return sum(weights.get(name, 0.0) * features.get(name, 0.0) for name in weights)


def _sigmoid(value: float) -> float:
    if value >= 40:
        return 1.0
    if value <= -40:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def _accuracy(predictions: list[ValueModelPrediction]) -> float:
    return (
        sum(1 for row in predictions if row.correct) / len(predictions)
        if predictions
        else 0.0
    )


def _log_loss(predictions: list[ValueModelPrediction]) -> float:
    if not predictions:
        return 0.0
    eps = 1e-9
    total = 0.0
    for row in predictions:
        p = min(max(row.score, eps), 1.0 - eps)
        total += -(row.label * math.log(p) + (1.0 - row.label) * math.log(1.0 - p))
    return total / len(predictions)


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


def _write_jsonl(path: Path, rows: list[ValueModelPrediction]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")

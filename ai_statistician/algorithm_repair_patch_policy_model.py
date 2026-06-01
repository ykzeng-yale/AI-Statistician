from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


ALGORITHM_REPAIR_PATCH_POLICY_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AlgorithmRepairPatchPolicyPrediction:
    example_id: str
    split: str
    patch_eval_id: str
    algorithm_id: str
    target_procedure: str
    gold_completion: str
    predicted_completion: str
    unsafe_completion: str
    gold_score: float
    unsafe_score: float
    chose_gold: bool
    rejected_unsafe: bool
    predicted_valid_json: bool
    predicted_decision: str
    predicted_production_patch_applied: bool
    predicted_promotion_ready: bool


@dataclass(frozen=True)
class AlgorithmRepairPatchPolicyModel:
    schema_version: int
    model_type: str
    feature_names: tuple[str, ...]
    weights: dict[str, float]
    threshold: float
    model_fingerprint: str

    def score(self, example: dict[str, object], candidate_completion: str) -> float:
        return _sigmoid(_dot(self.weights, _features(example, candidate_completion)))


def load_algorithm_repair_patch_policy_model(model_json: Path) -> AlgorithmRepairPatchPolicyModel:
    payload = json.loads(model_json.read_text(encoding="utf-8"))
    if int(payload.get("schema_version", -1)) != ALGORITHM_REPAIR_PATCH_POLICY_SCHEMA_VERSION:
        raise ValueError(
            "unsupported algorithm repair patch policy schema_version="
            f"{payload.get('schema_version')!r}"
        )
    model_type = str(payload.get("model_type", ""))
    if model_type != "logistic_algorithm_patch_promotion_safety_ranker":
        raise ValueError(f"unsupported algorithm repair patch policy model_type={model_type!r}")
    weights = {str(key): float(value) for key, value in dict(payload.get("weights", {})).items()}
    feature_names = tuple(str(item) for item in payload.get("feature_names", []) or [])
    missing = [name for name in feature_names if name not in weights]
    if missing:
        raise ValueError(f"algorithm repair patch policy model missing weights: {missing}")
    return AlgorithmRepairPatchPolicyModel(
        schema_version=ALGORITHM_REPAIR_PATCH_POLICY_SCHEMA_VERSION,
        model_type=model_type,
        feature_names=feature_names,
        weights=weights,
        threshold=float(payload.get("threshold", 0.5)),
        model_fingerprint=stable_hash(payload),
    )


def train_algorithm_repair_patch_policy_model(
    train_jsonl: Path,
    out_dir: Path,
    *,
    validation_jsonl: Path | None = None,
    epochs: int = 100,
    learning_rate: float = 0.15,
    l2: float = 0.001,
) -> dict[str, object]:
    """Train a tiny promotion-safety ranker from patch-eval supervision.

    The current production boundary is intentionally conservative: isolated
    patch evidence should not be promoted until a reviewed source commit and a
    release audit rerun exist.  This model learns that boundary by ranking the
    audited gold completion above unsafe promotion counterfactuals.
    """

    if epochs <= 0:
        raise ValueError("epochs must be positive")
    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")

    train = _read_jsonl(train_jsonl)
    validation = _read_jsonl(validation_jsonl) if validation_jsonl else list(train)
    feature_names = _feature_names()
    weights = {name: 0.0 for name in feature_names}
    pairs = _training_pairs(train)
    for _epoch in range(epochs):
        for example, candidate_completion, label in pairs:
            features = _features(example, candidate_completion)
            score = _sigmoid(_dot(weights, features))
            error = score - label
            for name in feature_names:
                weights[name] -= learning_rate * (error * features.get(name, 0.0) + l2 * weights[name])

    train_predictions = _predict_rows(train, weights, split="train")
    validation_predictions = _predict_rows(validation, weights, split="validation")

    out_dir.mkdir(parents=True, exist_ok=True)
    train_predictions_path = out_dir / "algorithm_repair_patch_policy_train_predictions.jsonl"
    validation_predictions_path = out_dir / "algorithm_repair_patch_policy_validation_predictions.jsonl"
    _write_jsonl(train_predictions_path, train_predictions)
    _write_jsonl(validation_predictions_path, validation_predictions)

    model = {
        "schema_version": ALGORITHM_REPAIR_PATCH_POLICY_SCHEMA_VERSION,
        "model_type": "logistic_algorithm_patch_promotion_safety_ranker",
        "feature_names": feature_names,
        "weights": weights,
        "threshold": 0.5,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "l2": l2,
    }
    model_path = out_dir / "algorithm_repair_patch_policy_model.json"
    model_path.write_text(json.dumps(model, indent=2, sort_keys=True), encoding="utf-8")

    manifest = {
        "schema_version": ALGORITHM_REPAIR_PATCH_POLICY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train_jsonl": str(train_jsonl),
        "validation_jsonl": str(validation_jsonl) if validation_jsonl else str(train_jsonl),
        "train_fingerprint": stable_hash(train),
        "validation_fingerprint": stable_hash(validation),
        "epochs": epochs,
        "learning_rate": learning_rate,
        "l2": l2,
        "n_train": len(train),
        "n_validation": len(validation),
        "n_training_pairs": len(pairs),
        "n_features": len(feature_names),
        "train_chose_gold": sum(1 for row in train_predictions if row.chose_gold),
        "validation_chose_gold": sum(1 for row in validation_predictions if row.chose_gold),
        "train_rejected_unsafe": sum(1 for row in train_predictions if row.rejected_unsafe),
        "validation_rejected_unsafe": sum(1 for row in validation_predictions if row.rejected_unsafe),
        "train_safe_decision_accuracy": _accuracy(train_predictions),
        "validation_safe_decision_accuracy": _accuracy(validation_predictions),
        "model_json": str(model_path),
        "train_predictions_jsonl": str(train_predictions_path),
        "validation_predictions_jsonl": str(validation_predictions_path),
        "model_fingerprint": stable_hash(model),
        "all_ok": (
            len(validation_predictions) == 0
            or (
                all(row.chose_gold for row in validation_predictions)
                and all(row.rejected_unsafe for row in validation_predictions)
                and all(row.predicted_valid_json for row in validation_predictions)
                and not any(row.predicted_production_patch_applied for row in validation_predictions)
                and not any(row.predicted_promotion_ready for row in validation_predictions)
            )
        ),
        "limitations": [
            "small deterministic feature model, not a neural AlgorithmEngineer",
            "learns the current conservative promotion boundary from exported patch-eval examples",
            "unsafe alternatives are counterfactual promotion completions, not observed production patches",
            "zero-example audits produce a valid no-op model and do not prove repair-policy quality",
        ],
    }
    (out_dir / "algorithm_repair_patch_policy_model_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return manifest


def _feature_names() -> list[str]:
    return [
        "bias",
        "context_mentions_reviewed_gate",
        "context_production_patch_false",
        "context_promotion_ready_false",
        "candidate_valid_json",
        "candidate_decision_hold",
        "candidate_decision_promote",
        "candidate_production_patch_false",
        "candidate_production_patch_true",
        "candidate_promotion_ready_false",
        "candidate_promotion_ready_true",
        "candidate_mentions_reviewed_gate",
        "candidate_required_gate_matches_context",
    ]


def _training_pairs(train: list[dict[str, object]]) -> list[tuple[dict[str, object], str, float]]:
    pairs: list[tuple[dict[str, object], str, float]] = []
    for example in train:
        gold = str(example.get("completion", "")).strip()
        if gold:
            pairs.append((example, gold, 1.0))
        pairs.append((example, _unsafe_promotion_completion(example), 0.0))
    return pairs


def _predict_rows(
    rows: list[dict[str, object]],
    weights: dict[str, float],
    *,
    split: str,
) -> list[AlgorithmRepairPatchPolicyPrediction]:
    predictions: list[AlgorithmRepairPatchPolicyPrediction] = []
    for row in rows:
        gold = str(row.get("completion", "")).strip()
        unsafe = _unsafe_promotion_completion(row)
        gold_score = _sigmoid(_dot(weights, _features(row, gold)))
        unsafe_score = _sigmoid(_dot(weights, _features(row, unsafe)))
        predicted = gold if gold_score >= unsafe_score else unsafe
        parsed = _parse_json(predicted)
        predictions.append(
            AlgorithmRepairPatchPolicyPrediction(
                example_id=str(row.get("example_id", "")),
                split=split,
                patch_eval_id=str(row.get("patch_eval_id", "")),
                algorithm_id=str(row.get("algorithm_id", "")),
                target_procedure=str(row.get("target_procedure", "")),
                gold_completion=gold,
                predicted_completion=predicted,
                unsafe_completion=unsafe,
                gold_score=round(gold_score, 6),
                unsafe_score=round(unsafe_score, 6),
                chose_gold=predicted == gold and bool(gold),
                rejected_unsafe=gold_score > unsafe_score,
                predicted_valid_json=isinstance(parsed, dict),
                predicted_decision=str(parsed.get("decision", "")) if isinstance(parsed, dict) else "",
                predicted_production_patch_applied=(
                    bool(parsed.get("production_patch_applied")) if isinstance(parsed, dict) else False
                ),
                predicted_promotion_ready=(
                    bool(parsed.get("promotion_ready")) if isinstance(parsed, dict) else False
                ),
            )
        )
    return predictions


def _features(example: dict[str, object], candidate_completion: str) -> dict[str, float]:
    parsed = _parse_json(candidate_completion)
    prompt = str(example.get("prompt", "")).lower()
    required_gate = str(example.get("required_next_gate", "")).lower()
    candidate_gate = str(parsed.get("required_next_gate", "")).lower() if isinstance(parsed, dict) else ""
    decision = str(parsed.get("decision", "")).lower() if isinstance(parsed, dict) else ""
    candidate_text = candidate_completion.lower()
    candidate_valid = isinstance(parsed, dict)
    production_value = bool(parsed.get("production_patch_applied")) if isinstance(parsed, dict) else False
    promotion_value = bool(parsed.get("promotion_ready")) if isinstance(parsed, dict) else False
    return {
        "bias": 1.0,
        "context_mentions_reviewed_gate": 1.0 if "review" in prompt or "review" in required_gate else 0.0,
        "context_production_patch_false": 1.0 if "production_patch_applied" in prompt and "false" in prompt else 0.0,
        "context_promotion_ready_false": 1.0 if "promotion_ready" in prompt and "false" in prompt else 0.0,
        "candidate_valid_json": 1.0 if candidate_valid else 0.0,
        "candidate_decision_hold": 1.0 if "hold" in decision else 0.0,
        "candidate_decision_promote": 1.0 if "promote" in decision else 0.0,
        "candidate_production_patch_false": 1.0 if candidate_valid and not production_value else 0.0,
        "candidate_production_patch_true": 1.0 if candidate_valid and production_value else 0.0,
        "candidate_promotion_ready_false": 1.0 if candidate_valid and not promotion_value else 0.0,
        "candidate_promotion_ready_true": 1.0 if candidate_valid and promotion_value else 0.0,
        "candidate_mentions_reviewed_gate": 1.0 if "review" in candidate_text else 0.0,
        "candidate_required_gate_matches_context": 1.0 if candidate_gate and candidate_gate == required_gate else 0.0,
    }


def _unsafe_promotion_completion(example: dict[str, object]) -> str:
    return json.dumps(
        {
            "decision": "promote_isolated_patch_to_production",
            "next_agent": "algorithm_engineer",
            "comparison_status": str(example.get("comparison_status", "")),
            "production_patch_applied": True,
            "promotion_ready": True,
            "allowed_patch_application": "direct_production_mutation",
            "required_next_gate": "none",
            "reason": "unsafe counterfactual: treats isolated patch evidence as a production source patch",
        },
        sort_keys=True,
    )


def _parse_json(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _dot(weights: dict[str, float], features: dict[str, float]) -> float:
    return sum(weights.get(name, 0.0) * features.get(name, 0.0) for name in weights)


def _sigmoid(value: float) -> float:
    if value >= 40:
        return 1.0
    if value <= -40:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def _accuracy(predictions: list[AlgorithmRepairPatchPolicyPrediction]) -> float:
    if not predictions:
        return 0.0
    return sum(1 for row in predictions if row.chose_gold and row.rejected_unsafe) / len(predictions)


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


def _write_jsonl(path: Path, rows: list[AlgorithmRepairPatchPolicyPrediction]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")

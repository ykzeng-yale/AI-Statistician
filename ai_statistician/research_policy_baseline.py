from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .retrieval import tokens


RESEARCH_POLICY_BASELINE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ResearchPolicyBaselinePrediction:
    example_id: str
    task: str
    question_id: str
    problem_class: str
    gold_completion: str
    predicted_completion: str
    predicted_from_example_id: str
    predicted_from_task: str
    predicted_from_question_id: str
    predicted_from_problem_class: str
    score: float
    exact_match: bool
    same_task: bool
    same_problem_class: bool
    predicted_valid_json: bool
    json_key_f1: float
    top_k_exact_match: bool
    top_k_same_task: bool
    top_k_example_ids: tuple[str, ...]


def evaluate_research_policy_baseline(
    train_jsonl: Path,
    validation_jsonl: Path,
    out_dir: Path,
    *,
    k: int = 5,
) -> dict[str, object]:
    """Evaluate a no-training nearest-neighbor baseline for research agents.

    This mirrors the proof-policy baseline, but over AI Statistical Theory Lab
    trace examples: problem formalization, theory planning, formal-gap routing,
    and simulation critique. It gives future SFT/RL systems a concrete baseline
    to beat before any model checkpoint is registered.
    """

    if k <= 0:
        raise ValueError("k must be positive")
    train = _read_jsonl(train_jsonl)
    validation = _read_jsonl(validation_jsonl)
    predictions = [_predict(row, train, k=k) for row in validation]
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "research_policy_baseline_predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as handle:
        for row in predictions:
            handle.write(json.dumps(asdict(row), default=str) + "\n")
    n = len(predictions)
    exact = sum(1 for row in predictions if row.exact_match)
    same_task = sum(1 for row in predictions if row.same_task)
    same_problem = sum(1 for row in predictions if row.same_problem_class)
    valid_json = sum(1 for row in predictions if row.predicted_valid_json)
    top_k_exact = sum(1 for row in predictions if row.top_k_exact_match)
    top_k_same_task = sum(1 for row in predictions if row.top_k_same_task)
    manifest = {
        "schema_version": RESEARCH_POLICY_BASELINE_SCHEMA_VERSION,
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
        "same_task": same_task,
        "same_task_rate": same_task / n if n else 0.0,
        "same_problem_class": same_problem,
        "same_problem_class_rate": same_problem / n if n else 0.0,
        "predicted_valid_json": valid_json,
        "predicted_valid_json_rate": valid_json / n if n else 0.0,
        "top_k_same_task": top_k_same_task,
        "top_k_same_task_rate": top_k_same_task / n if n else 0.0,
        "mean_json_key_f1": sum(row.json_key_f1 for row in predictions) / n if n else 0.0,
        "mean_top1_score": sum(row.score for row in predictions) / n if n else 0.0,
        "predictions_jsonl": str(predictions_path),
        "baseline_fingerprint": stable_hash([asdict(row) for row in predictions]),
        "all_ok": len(train) > 0 and len(validation) > 0 and all(row.predicted_valid_json for row in predictions),
        "limitations": [
            "nearest-neighbor research-agent memory baseline only",
            "does not train or call an LLM",
            "JSON key overlap is a weak structural metric, not semantic correctness",
            "intended as a no-training baseline for future SFT/RL research agents to beat",
        ],
    }
    (out_dir / "research_policy_baseline_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return manifest


def _predict(
    validation_row: dict[str, Any],
    train_rows: list[dict[str, Any]],
    *,
    k: int,
) -> ResearchPolicyBaselinePrediction:
    scored = sorted(
        ((_example_score(validation_row, row), row) for row in train_rows),
        key=lambda item: (-item[0], str(item[1].get("example_id", ""))),
    )
    top = scored[:k]
    best_score, best = top[0] if top else (0.0, {})
    gold = str(validation_row.get("completion", "")).strip()
    predicted = str(best.get("completion", "")).strip()
    gold_json = _parse_json(gold)
    predicted_json = _parse_json(predicted)
    top_k_example_ids = tuple(str(row.get("example_id", "")) for _score, row in top)
    return ResearchPolicyBaselinePrediction(
        example_id=str(validation_row.get("example_id", "")),
        task=str(validation_row.get("task", "")),
        question_id=str(validation_row.get("question_id", "")),
        problem_class=str(validation_row.get("problem_class", "")),
        gold_completion=gold,
        predicted_completion=predicted,
        predicted_from_example_id=str(best.get("example_id", "")),
        predicted_from_task=str(best.get("task", "")),
        predicted_from_question_id=str(best.get("question_id", "")),
        predicted_from_problem_class=str(best.get("problem_class", "")),
        score=round(float(best_score), 6),
        exact_match=bool(predicted and predicted == gold),
        same_task=str(best.get("task", "")) == str(validation_row.get("task", "")),
        same_problem_class=str(best.get("problem_class", "")) == str(validation_row.get("problem_class", "")),
        predicted_valid_json=predicted_json is not None,
        json_key_f1=round(_json_key_f1(gold_json, predicted_json), 6),
        top_k_exact_match=any(str(row.get("completion", "")).strip() == gold for _score, row in top),
        top_k_same_task=any(str(row.get("task", "")) == str(validation_row.get("task", "")) for _score, row in top),
        top_k_example_ids=top_k_example_ids,
    )


def _example_score(query: dict[str, Any], candidate: dict[str, Any]) -> float:
    q_task = str(query.get("task", ""))
    c_task = str(candidate.get("task", ""))
    q_problem = str(query.get("problem_class", ""))
    c_problem = str(candidate.get("problem_class", ""))
    q_tags = {str(item).lower() for item in query.get("tags", []) or []}
    c_tags = {str(item).lower() for item in candidate.get("tags", []) or []}
    q_procedures = {str(item).lower() for item in query.get("procedure_ids", []) or []}
    c_procedures = {str(item).lower() for item in candidate.get("procedure_ids", []) or []}
    q_goals = {str(item).lower() for item in query.get("theorem_goal_ids", []) or []}
    c_goals = {str(item).lower() for item in candidate.get("theorem_goal_ids", []) or []}
    q_symbols = set().union(q_tags, q_procedures, q_goals, {q_task, q_problem})
    c_symbols = set().union(c_tags, c_procedures, c_goals, {c_task, c_problem})
    q_tokens = tokens(
        " ".join(
            [
                str(query.get("prompt", "")),
                " ".join(query.get("tags", []) or []),
                " ".join(query.get("procedure_ids", []) or []),
                " ".join(query.get("theorem_goal_ids", []) or []),
            ]
        )
    )
    c_tokens = tokens(
        " ".join(
            [
                str(candidate.get("prompt", "")),
                " ".join(candidate.get("tags", []) or []),
                " ".join(candidate.get("procedure_ids", []) or []),
                " ".join(candidate.get("theorem_goal_ids", []) or []),
            ]
        )
    )
    return (
        len(q_tokens & c_tokens)
        + 40.0 * (1 if q_task and q_task == c_task else 0)
        + 12.0 * (1 if q_problem and q_problem == c_problem else 0)
        + 4.0 * len(q_symbols & c_symbols)
    )


def _parse_json(text: str) -> object | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _json_key_f1(gold: object | None, predicted: object | None) -> float:
    if not isinstance(gold, dict) or not isinstance(predicted, dict):
        return 0.0
    gold_keys = set(gold.keys())
    pred_keys = set(predicted.keys())
    if not gold_keys and not pred_keys:
        return 1.0
    if not gold_keys or not pred_keys:
        return 0.0
    overlap = len(gold_keys & pred_keys)
    precision = overlap / len(pred_keys)
    recall = overlap / len(gold_keys)
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


ALGORITHM_REPAIR_PATCH_TRAINING_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AlgorithmRepairPatchTrainingExample:
    schema_version: int
    example_id: str
    split: str
    task: str
    prompt: str
    completion: str
    patch_eval_id: str
    application_id: str
    candidate_id: str
    algorithm_id: str
    target_procedure: str
    question_id: str
    problem_class: str
    comparison_status: str
    required_next_gate: str
    production_patch_applied: bool
    promotion_ready: bool
    tags: tuple[str, ...]


def export_algorithm_repair_patch_training_dataset(
    patch_eval_dir: Path,
    out_dir: Path,
    *,
    validation_fraction: float = 0.2,
) -> dict[str, object]:
    """Export isolated algorithm patch-eval evidence as repair-policy SFT data.

    This exporter is deliberately conservative.  The patch-eval lane executes a
    deterministic isolated patch and produces before/after simulation evidence,
    but it does not mutate production code.  The training target therefore
    teaches the AlgorithmEngineer/promotion policy to preserve that boundary:
    hold for a reviewed source commit after evidence is ready.
    """

    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0.0, 1.0)")

    errors: list[str] = []
    manifest_path = patch_eval_dir / "algorithm_repair_sandbox_patch_eval_manifest.json"
    patch_manifest = _load_json(manifest_path, errors)
    results_path = Path(
        str(
            patch_manifest.get(
                "results_jsonl",
                patch_eval_dir / "algorithm_repair_sandbox_patch_eval_results.jsonl",
            )
        )
    )
    if not results_path.is_absolute() and not results_path.exists():
        results_path = patch_eval_dir / results_path
    results = _load_jsonl(results_path, errors)
    eligible = [
        row
        for row in results
        if row.get("ok") is True
        and row.get("before_after_comparison_ready") is True
        and row.get("isolated_patch_executed") is True
    ]
    examples = [
        _training_example(row, split=_split_for_row(str(row.get("patch_eval_id", idx)), validation_fraction))
        for idx, row in enumerate(eligible)
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "algorithm_repair_patch_train.jsonl"
    validation_path = out_dir / "algorithm_repair_patch_validation.jsonl"
    all_path = out_dir / "algorithm_repair_patch_all.jsonl"
    _write_jsonl(train_path, [row for row in examples if row.split == "train"])
    _write_jsonl(validation_path, [row for row in examples if row.split == "validation"])
    _write_jsonl(all_path, examples)

    n_production_patches = sum(1 for row in results if row.get("production_patch_applied") is True)
    n_promotion_ready = sum(1 for row in results if row.get("promotion_ready") is True)
    n_before_after = sum(1 for row in results if row.get("before_after_comparison_ready") is True)
    by_status: dict[str, int] = {}
    for row in results:
        status = str(row.get("comparison_status", "UNKNOWN"))
        by_status[status] = by_status.get(status, 0) + 1

    manifest = {
        "schema_version": ALGORITHM_REPAIR_PATCH_TRAINING_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "patch_eval_dir": str(patch_eval_dir),
        "source_manifest": str(manifest_path),
        "source_results_jsonl": str(results_path),
        "source_dataset_fingerprint": stable_hash(results),
        "validation_fraction": validation_fraction,
        "n_results": len(results),
        "n_ok_results": sum(1 for row in results if row.get("ok") is True),
        "n_before_after_comparisons": n_before_after,
        "n_training_examples": len(examples),
        "n_train": sum(1 for row in examples if row.split == "train"),
        "n_validation": sum(1 for row in examples if row.split == "validation"),
        "n_production_patches_applied": n_production_patches,
        "n_promotion_ready": n_promotion_ready,
        "by_comparison_status": dict(sorted(by_status.items())),
        "train_jsonl": str(train_path),
        "validation_jsonl": str(validation_path),
        "all_jsonl": str(all_path),
        "dataset_fingerprint": stable_hash([asdict(row) for row in examples]),
        "all_ok": (
            not errors
            and bool(patch_manifest.get("all_ok"))
            and len(examples) == n_before_after
            and n_production_patches == 0
            and n_promotion_ready == 0
        ),
        "errors": errors,
        "limitations": [
            "exports supervised repair-policy examples only; no model weights are trained",
            "examples teach the conservative boundary that isolated evidence is not a production patch",
            "promotion_ready remains false until a reviewed source commit and release audit rerun",
        ],
    }
    (out_dir / "algorithm_repair_patch_training_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "algorithm_repair_patch_training.md").write_text(
        _markdown_report(manifest),
        encoding="utf-8",
    )
    return manifest


def _training_example(row: dict[str, Any], *, split: str) -> AlgorithmRepairPatchTrainingExample:
    patch_eval_id = str(row.get("patch_eval_id", ""))
    comparison_status = str(row.get("comparison_status", ""))
    completion = {
        "decision": "hold_for_reviewed_production_commit",
        "next_agent": "algorithm_engineer",
        "comparison_status": comparison_status,
        "production_patch_applied": False,
        "promotion_ready": False,
        "allowed_patch_application": "reviewed_source_commit_only",
        "required_next_gate": str(row.get("required_next_gate", "")),
        "reason": (
            "isolated before/after evidence is available, but production code "
            "must only change through reviewed source edits followed by the full release audit"
        ),
    }
    tags = (
        "algorithm_repair",
        "patch_eval",
        comparison_status,
        str(row.get("algorithm_id", "")),
    )
    return AlgorithmRepairPatchTrainingExample(
        schema_version=ALGORITHM_REPAIR_PATCH_TRAINING_SCHEMA_VERSION,
        example_id=f"algorithm_repair_patch_training:{stable_hash([patch_eval_id, split])[:16]}",
        split=split,
        task="algorithm_repair_patch_promotion_policy",
        prompt=_prompt(row),
        completion=json.dumps(completion, sort_keys=True),
        patch_eval_id=patch_eval_id,
        application_id=str(row.get("application_id", "")),
        candidate_id=str(row.get("candidate_id", "")),
        algorithm_id=str(row.get("algorithm_id", "")),
        target_procedure=str(row.get("target_procedure", "")),
        question_id=str(row.get("question_id", "")),
        problem_class=str(row.get("problem_class", "")),
        comparison_status=comparison_status,
        required_next_gate=str(row.get("required_next_gate", "")),
        production_patch_applied=bool(row.get("production_patch_applied", False)),
        promotion_ready=bool(row.get("promotion_ready", False)),
        tags=tags,
    )


def _prompt(row: dict[str, Any]) -> str:
    context = {
        "algorithm_id": row.get("algorithm_id", ""),
        "target_procedure": row.get("target_procedure", ""),
        "question_id": row.get("question_id", ""),
        "problem_class": row.get("problem_class", ""),
        "patch_application_mode": row.get("patch_application_mode", ""),
        "comparison_status": row.get("comparison_status", ""),
        "baseline_metrics": row.get("baseline_metrics", {}),
        "patched_metrics": row.get("patched_metrics", {}),
        "metric_deltas": row.get("metric_deltas", {}),
        "nonfinite_baseline_metrics": row.get("nonfinite_baseline_metrics", []),
        "nonfinite_patched_metrics": row.get("nonfinite_patched_metrics", []),
        "production_patch_applied": row.get("production_patch_applied", False),
        "promotion_ready": row.get("promotion_ready", False),
        "required_next_gate": row.get("required_next_gate", ""),
    }
    return "\n".join(
        [
            "You are the AlgorithmEngineer promotion policy in an AI Statistical Theory Lab.",
            "Given isolated patch-evaluation evidence, decide whether to promote the patch or hold it for reviewed production work.",
            "Return JSON only.",
            "",
            "Patch evaluation context:",
            json.dumps(context, indent=2, sort_keys=True, default=str),
        ]
    )


def _split_for_row(row_id: str, validation_fraction: float) -> str:
    if validation_fraction <= 0.0:
        return "train"
    bucket = int(stable_hash(row_id)[:12], 16) / float(0xFFFFFFFFFFFF)
    return "validation" if bucket < validation_fraction else "train"


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse JSON {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"failed to parse JSONL {path}:{idx}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"JSONL row is not an object: {path}:{idx}")
    return rows


def _write_jsonl(path: Path, rows: list[AlgorithmRepairPatchTrainingExample]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")


def _markdown_report(manifest: dict[str, object]) -> str:
    lines = [
        "# Algorithm Repair Patch Training Export",
        "",
        f"- Source patch-eval dir: `{manifest.get('patch_eval_dir')}`",
        f"- Training examples: {manifest.get('n_training_examples')}",
        f"- Train/validation: {manifest.get('n_train')}/{manifest.get('n_validation')}",
        f"- Production patches applied: {manifest.get('n_production_patches_applied')}",
        f"- Promotion-ready examples: {manifest.get('n_promotion_ready')}",
        f"- All OK: {manifest.get('all_ok')}",
        "",
        "## Comparison Status",
        "",
    ]
    by_status = manifest.get("by_comparison_status", {})
    if isinstance(by_status, dict) and by_status:
        for status, count in sorted(by_status.items()):
            lines.append(f"- `{status}`: {count}")
    else:
        lines.append("- none")
    if manifest.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in manifest.get("errors", []):
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)

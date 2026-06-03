from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_CALIBRATION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayCalibrationRow:
    schema_version: int
    calibration_id: str
    replay_id: str
    source_queue_item_id: str
    route_id: str
    task_id: str
    theorem_goal_id: str
    display_name: str
    replay_mode: str
    acceptance_gate: str
    attempted: bool
    n_attempts: int
    n_positive_attempts: int
    n_negative_attempts: int
    n_kernel_verified_attempts: int
    n_non_kernel_positive_attempts: int
    latest_attempt_id: str
    latest_verifier: str
    latest_verification_strength: str
    latest_ok: bool
    latest_kernel_verified: bool
    first_error: str
    first_error_category: str
    attempt_outcome_status: str
    replay_calibration_status: str
    full_route_proof_status: str
    replay_policy_update: str
    repair_prompt: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_calibration(
    formal_verifier_replay_dir: Path,
    out_dir: Path | None = None,
    *,
    attempt_log_path: Path | None = None,
) -> dict[str, object]:
    """Calibrate replay tasks against full theorem/bridge proof attempts.

    The attempt log is optional. Without it, rows honestly report that the
    replay target is awaiting a full-route attempt. With it, rows distinguish
    kernel-verified target proofs, non-kernel positives, failed attempts, and
    missing attempts.
    """

    errors: list[str] = []
    replay_manifest_path = formal_verifier_replay_dir / "formal_verifier_replay_manifest.json"
    replay_payload = _read_json(replay_manifest_path, errors)
    tasks = [row for row in replay_payload.get("tasks", []) if isinstance(row, dict)]
    attempts = _read_jsonl(attempt_log_path, errors) if attempt_log_path is not None else []
    rows = tuple(_calibration_row(task, attempts) for task in tasks)
    by_status = Counter(row.replay_calibration_status for row in rows)
    by_error = Counter(row.first_error_category for row in rows)
    repair_examples = [
        {
            "example_id": row.calibration_id,
            "task": "formal_verifier_replay_repair",
            "prompt": row.repair_prompt,
            "completion": json.dumps(
                {
                    "next_action": row.replay_policy_update,
                    "proof_status": row.full_route_proof_status,
                    "claim_status": "attempt_feedback_not_proof_evidence",
                },
                sort_keys=True,
            ),
            "replay_id": row.replay_id,
            "first_error_category": row.first_error_category,
        }
        for row in rows
        if row.n_negative_attempts > 0
    ]
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_CALIBRATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_dir": str(formal_verifier_replay_dir),
        "formal_verifier_replay_manifest": str(replay_manifest_path),
        "replay_task_fingerprint": replay_payload.get("task_fingerprint", ""),
        "attempt_log": str(attempt_log_path or ""),
        "n_attempt_log_rows": len(attempts),
        "n_replay_tasks": len(tasks),
        "n_calibration_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "n_attempted_replay_tasks": sum(1 for row in rows if row.attempted),
        "n_awaiting_full_route_attempt": by_status.get("awaiting_full_route_attempt", 0),
        "n_failed_full_route_attempt": by_status.get("failed_full_route_attempt_repair_needed", 0),
        "n_non_kernel_positive": by_status.get("non_kernel_positive_requires_kernel_replay", 0),
        "n_kernel_verified": by_status.get("full_route_kernel_verified", 0),
        "n_positive_attempts": sum(row.n_positive_attempts for row in rows),
        "n_negative_attempts": sum(row.n_negative_attempts for row in rows),
        "n_kernel_verified_attempts": sum(row.n_kernel_verified_attempts for row in rows),
        "n_repair_training_examples": len(repair_examples),
        "by_replay_calibration_status": dict(sorted(by_status.items())),
        "by_first_error_category": dict(sorted(by_error.items())),
        "rows": [asdict(row) for row in rows],
        "repair_training_examples": repair_examples,
        "calibration_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "missing attempt rows mean the replay target is awaiting a full theorem/bridge attempt",
            "failed replay attempts are repair feedback, not proof evidence",
            "non-kernel positive attempts require AXLE/local Lean replay before becoming proof evidence",
            "only rows with full_route_kernel_verified status can be used as proof evidence for the replay target",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_verifier_replay_calibration_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_calibration.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_training.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in repair_examples)
            + ("\n" if repair_examples else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_calibration.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _calibration_row(
    task: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> FormalVerifierReplayCalibrationRow:
    errors: list[str] = []
    replay_id = str(task.get("replay_id", ""))
    source_queue_item_id = str(task.get("source_queue_item_id", ""))
    route_id = str(task.get("route_id", ""))
    display_name = str(task.get("display_name", ""))
    matched_attempts = _matching_attempts(task, attempts)
    latest = matched_attempts[-1] if matched_attempts else {}
    latest_attempt_id = str(latest.get("attempt_id", ""))
    positive_attempts = [row for row in matched_attempts if bool(row.get("ok"))]
    negative_attempts = [row for row in matched_attempts if not bool(row.get("ok"))]
    kernel_verified_attempts = [row for row in matched_attempts if bool(row.get("kernel_verified"))]
    first_error = _first_error(matched_attempts)
    error_category = _error_category(first_error)
    calibration_status = _calibration_status(
        n_attempts=len(matched_attempts),
        n_positive=len(positive_attempts),
        n_negative=len(negative_attempts),
        n_kernel=len(kernel_verified_attempts),
    )
    if not replay_id:
        errors.append("replay_id missing")
    if not route_id:
        errors.append("route_id missing")
    if not display_name:
        errors.append("display_name missing")
    if not str(task.get("acceptance_gate", "")):
        errors.append("acceptance_gate missing")
    return FormalVerifierReplayCalibrationRow(
        schema_version=FORMAL_VERIFIER_REPLAY_CALIBRATION_SCHEMA_VERSION,
        calibration_id=f"formal_verifier_replay_calibration:{stable_hash([replay_id, matched_attempts])[:16]}",
        replay_id=replay_id,
        source_queue_item_id=source_queue_item_id,
        route_id=route_id,
        task_id=str(task.get("task_id", "")),
        theorem_goal_id=str(task.get("theorem_goal_id", "")),
        display_name=display_name,
        replay_mode=str(task.get("replay_mode", "")),
        acceptance_gate=str(task.get("acceptance_gate", "")),
        attempted=bool(matched_attempts),
        n_attempts=len(matched_attempts),
        n_positive_attempts=len(positive_attempts),
        n_negative_attempts=len(negative_attempts),
        n_kernel_verified_attempts=len(kernel_verified_attempts),
        n_non_kernel_positive_attempts=sum(
            1 for row in positive_attempts if not bool(row.get("kernel_verified"))
        ),
        latest_attempt_id=latest_attempt_id,
        latest_verifier=str(latest.get("verifier", "")),
        latest_verification_strength=str(latest.get("verification_strength", "")),
        latest_ok=bool(latest.get("ok", False)),
        latest_kernel_verified=bool(latest.get("kernel_verified", False)),
        first_error=first_error,
        first_error_category=error_category,
        attempt_outcome_status=_attempt_outcome_status(calibration_status),
        replay_calibration_status=calibration_status,
        full_route_proof_status=(
            "PROVED_BY_KERNEL_REPLAY"
            if calibration_status == "full_route_kernel_verified"
            else "UNPROVED_REPLAY_TARGET"
        ),
        replay_policy_update=_policy_update(calibration_status, error_category, task),
        repair_prompt=_repair_prompt(task, first_error, error_category),
        proof_evidence_boundary=(
            "This calibration row is proof evidence for the replay target only when "
            "replay_calibration_status is full_route_kernel_verified. All other statuses "
            "are attempt feedback or missing-attempt accounting."
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _matching_attempts(
    task: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    task_keys = {
        str(task.get(key, ""))
        for key in (
            "replay_id",
            "source_queue_item_id",
            "route_id",
            "task_id",
            "theorem_goal_id",
            "display_name",
        )
        if str(task.get(key, ""))
    }
    matched: list[dict[str, Any]] = []
    for attempt in attempts:
        if not isinstance(attempt, dict):
            continue
        attempt_keys = {
            str(attempt.get(key, ""))
            for key in (
                "replay_id",
                "source_replay_id",
                "formal_verifier_replay_id",
                "source_queue_item_id",
                "route_id",
                "task_id",
                "theorem_goal_id",
                "display_name",
                "target_id",
                "obligation_id",
                "title",
            )
            if str(attempt.get(key, ""))
        }
        for key in ("replay_ids", "route_ids", "source_queue_item_ids"):
            raw = attempt.get(key, [])
            if isinstance(raw, list):
                attempt_keys.update(str(item) for item in raw if str(item))
        if task_keys & attempt_keys:
            matched.append(attempt)
    return matched


def _calibration_status(
    *,
    n_attempts: int,
    n_positive: int,
    n_negative: int,
    n_kernel: int,
) -> str:
    if n_kernel > 0:
        return "full_route_kernel_verified"
    if n_positive > 0:
        return "non_kernel_positive_requires_kernel_replay"
    if n_negative > 0:
        return "failed_full_route_attempt_repair_needed"
    if n_attempts > 0:
        return "attempted_without_verifier_outcome"
    return "awaiting_full_route_attempt"


def _attempt_outcome_status(calibration_status: str) -> str:
    return {
        "full_route_kernel_verified": "accepted_by_kernel",
        "non_kernel_positive_requires_kernel_replay": "accepted_by_non_kernel_verifier_only",
        "failed_full_route_attempt_repair_needed": "failed_with_repair_feedback",
        "attempted_without_verifier_outcome": "attempt_log_missing_verifier_outcome",
        "awaiting_full_route_attempt": "no_attempt_recorded",
    }.get(calibration_status, "unknown")


def _policy_update(calibration_status: str, error_category: str, task: dict[str, Any]) -> str:
    if calibration_status == "full_route_kernel_verified":
        return "promote replay mode as a verified full-route proof pattern"
    if calibration_status == "non_kernel_positive_requires_kernel_replay":
        return "rerun the positive candidate under AXLE/local Lean before promotion"
    if calibration_status == "failed_full_route_attempt_repair_needed":
        if error_category == "placeholder_or_gap":
            return "replace placeholder/gap assumptions with verified bridge lemmas before retrying"
        if error_category == "missing_identifier":
            return "repair imports or source declarations, then replay the same route"
        if error_category == "type_mismatch":
            return "repair theorem skeleton types and subclaim composition before retrying"
        return "preserve earliest error as a hard negative and schedule replay repair"
    if str(task.get("replay_mode", "")) == "semantic_route_review_before_replay":
        return "complete semantic route review before first full-route attempt"
    return "schedule first full theorem/bridge replay attempt"


def _first_error(attempts: list[dict[str, Any]]) -> str:
    for attempt in attempts:
        raw_errors = attempt.get("errors", [])
        if isinstance(raw_errors, list) and raw_errors:
            return str(raw_errors[0])
        first_error = str(attempt.get("first_error", ""))
        if first_error:
            return first_error
        error = str(attempt.get("error", ""))
        if error:
            return error
    return ""


def _error_category(error: str) -> str:
    lowered = error.lower()
    if not lowered:
        return "none"
    if "timeout" in lowered:
        return "timeout"
    if "placeholder" in lowered or "sorry" in lowered or "h_frontier_missing" in lowered:
        return "placeholder_or_gap"
    if "unknown identifier" in lowered or "unknown constant" in lowered or "no declaration" in lowered:
        return "missing_identifier"
    if "type mismatch" in lowered or "has type" in lowered or "expected" in lowered:
        return "type_mismatch"
    if "unsolved goals" in lowered or "unsolved goal" in lowered:
        return "unsolved_goals"
    if "kernel" in lowered:
        return "kernel_error"
    return "other"


def _repair_prompt(task: dict[str, Any], first_error: str, error_category: str) -> str:
    obligations = task.get("subclaim_replay_obligations", [])
    if not isinstance(obligations, list):
        obligations = []
    return "\n".join(
        [
            "You are repairing a full theorem/bridge replay attempt.",
            f"Replay id: {task.get('replay_id', '')}",
            f"Route: {task.get('display_name', '')}",
            f"Replay mode: {task.get('replay_mode', '')}",
            f"Acceptance gate: {task.get('acceptance_gate', '')}",
            f"Subclaim replay obligations: {', '.join(str(item) for item in obligations) or 'none'}",
            f"First error category: {error_category}",
            f"First error: {first_error or 'none'}",
            "Return the next repair action without claiming the theorem is proved.",
        ]
    )


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing JSONL file: {path}")
        return []
    for idx, line in enumerate(lines, start=1):
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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Replay Calibration",
        "",
        f"- Replay manifest: `{payload.get('formal_verifier_replay_manifest')}`",
        f"- Attempt log: `{payload.get('attempt_log')}`",
        f"- Calibration rows: {payload.get('n_ok')}/{payload.get('n_calibration_rows')} audit-clean",
        f"- Attempted replay tasks: {payload.get('n_attempted_replay_tasks')}",
        f"- Awaiting full-route attempts: {payload.get('n_awaiting_full_route_attempt')}",
        f"- Failed full-route attempts: {payload.get('n_failed_full_route_attempt')}",
        f"- Kernel-verified full-route targets: {payload.get('n_kernel_verified')}",
        "",
        "Calibration rows separate replay attempt feedback from proof evidence.",
        "",
        "## Rows",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No replay calibration rows were exported.")
    else:
        for row in rows[:30]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}`: {row.get('replay_calibration_status')} "
                f"(attempts={row.get('n_attempts')}, error={row.get('first_error_category')})"
            )
            lines.append(f"  update: {row.get('replay_policy_update')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairPacket:
    schema_version: int
    packet_id: str
    replay_id: str
    source_queue_item_id: str
    route_id: str
    task_id: str
    theorem_goal_id: str
    display_name: str
    replay_mode: str
    owner_agent: str
    latest_attempt_id: str
    first_error_category: str
    first_error: str
    replay_policy_update: str
    repair_class: str
    priority_score: int
    acceptance_gate: str
    required_primitives: tuple[str, ...]
    subclaim_replay_obligations: tuple[str, ...]
    related_proof_obligations: tuple[str, ...]
    retrieval_hit_obligations: tuple[str, ...]
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    route_specific_repair_steps: tuple[str, ...]
    proof_body_template_not_verified: str
    training_prompt: str
    training_completion: str
    repair_acceptance_gate: str
    proof_evidence_boundary: str
    with_attempt: bool
    with_exact_subclaims: bool
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_packets(
    formal_verifier_replay_dir: Path,
    formal_verifier_replay_attempt_dir: Path,
    formal_verifier_replay_calibration_dir: Path,
    out_dir: Path | None = None,
    *,
    max_packets: int = 20,
) -> dict[str, object]:
    """Export repair packets from failed full-route replay attempts.

    These packets contain exact failed-candidate context for a proof agent.
    They are not proof evidence until a regenerated candidate passes
    AXLE/local Lean for the unchanged target.
    """

    errors: list[str] = []
    replay_manifest_path = formal_verifier_replay_dir / "formal_verifier_replay_manifest.json"
    attempt_manifest_path = (
        formal_verifier_replay_attempt_dir / "formal_verifier_replay_attempt_manifest.json"
    )
    calibration_manifest_path = (
        formal_verifier_replay_calibration_dir / "formal_verifier_replay_calibration_manifest.json"
    )
    replay_payload = _read_json(replay_manifest_path, errors)
    attempt_payload = _read_json(attempt_manifest_path, errors)
    calibration_payload = _read_json(calibration_manifest_path, errors)
    tasks_by_replay = {
        str(row.get("replay_id", "")): row
        for row in replay_payload.get("tasks", [])
        if isinstance(row, dict) and str(row.get("replay_id", ""))
    }
    attempts_by_replay = {
        str(row.get("replay_id", "")): row
        for row in attempt_payload.get("rows", [])
        if isinstance(row, dict) and str(row.get("replay_id", ""))
    }
    failed_rows = _failed_calibration_rows(calibration_payload)
    packets = [
        _packet_from_failed_row(
            row,
            task=tasks_by_replay.get(str(row.get("replay_id", "")), {}),
            attempt=attempts_by_replay.get(str(row.get("replay_id", "")), {}),
        )
        for row in failed_rows
    ]
    packets = sorted(
        packets,
        key=lambda row: (-row.priority_score, row.first_error_category, row.packet_id),
    )[: max(0, max_packets)]
    by_repair_class = Counter(row.repair_class for row in packets)
    by_error = Counter(row.first_error_category for row in packets)
    training_examples = [
        {
            "example_id": packet.packet_id,
            "task": "formal_verifier_route_replay_repair_packet",
            "prompt": packet.training_prompt,
            "completion": packet.training_completion,
            "replay_id": packet.replay_id,
            "repair_class": packet.repair_class,
            "first_error_category": packet.first_error_category,
            "claim_status": "repair_packet_not_proof_evidence",
        }
        for packet in packets
    ]
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_dir": str(formal_verifier_replay_dir),
        "formal_verifier_replay_manifest": str(replay_manifest_path),
        "formal_verifier_replay_attempt_dir": str(formal_verifier_replay_attempt_dir),
        "formal_verifier_replay_attempt_manifest": str(attempt_manifest_path),
        "formal_verifier_replay_calibration_dir": str(formal_verifier_replay_calibration_dir),
        "formal_verifier_replay_calibration_manifest": str(calibration_manifest_path),
        "max_packets": max_packets,
        "n_failed_replay_attempts": len(failed_rows),
        "n_repair_packets": len(packets),
        "n_ok": sum(1 for row in packets if row.ok),
        "all_ok": not errors and all(row.ok for row in packets),
        "errors": errors,
        "n_tactic_no_progress": by_error.get("tactic_no_progress", 0),
        "n_missing_identifier": by_error.get("missing_identifier", 0),
        "n_type_mismatch": by_error.get("type_mismatch", 0),
        "n_placeholder_or_gap": by_error.get("placeholder_or_gap", 0),
        "n_with_attempt": sum(1 for row in packets if row.with_attempt),
        "n_with_exact_subclaims": sum(1 for row in packets if row.with_exact_subclaims),
        "n_training_examples": len(training_examples),
        "by_repair_class": dict(sorted(by_repair_class.items())),
        "by_first_error_category": dict(sorted(by_error.items())),
        "packets": [asdict(row) for row in packets],
        "training_examples": training_examples,
        "repair_fingerprint": stable_hash([asdict(row) for row in packets]),
        "limitations": [
            "feedback packets are not Lean proof evidence",
            "the harness does not choose edits, tactics, imports, or bridge lemmas",
            "a candidate closes only after the unchanged target passes AXLE/local Lean",
            "failed replay attempts remain formal gaps until the target is kernel verified",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_verifier_replay_repair_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_packets.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in packets)
            + ("\n" if packets else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_training.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in training_examples)
            + ("\n" if training_examples else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def export_formal_verifier_replay_repairs(
    formal_verifier_replay_dir: Path,
    formal_verifier_replay_attempt_dir: Path,
    formal_verifier_replay_calibration_dir: Path,
    out_dir: Path | None = None,
    *,
    max_packets: int = 20,
) -> dict[str, object]:
    return export_formal_verifier_replay_repair_packets(
        formal_verifier_replay_dir,
        formal_verifier_replay_attempt_dir,
        formal_verifier_replay_calibration_dir,
        out_dir,
        max_packets=max_packets,
    )


def _failed_calibration_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        status = str(row.get("replay_calibration_status", ""))
        if status == "failed_full_route_attempt_repair_needed" or _safe_int(
            row.get("n_negative_attempts", 0)
        ) > 0:
            rows.append(row)
    return rows


def _packet_from_failed_row(
    row: dict[str, Any],
    *,
    task: dict[str, Any],
    attempt: dict[str, Any],
) -> FormalVerifierReplayRepairPacket:
    errors: list[str] = []
    replay_id = str(row.get("replay_id", ""))
    display_name = str(row.get("display_name") or task.get("display_name", ""))
    error_category = str(row.get("first_error_category", ""))
    required_primitives = _str_tuple(task.get("required_primitives", []))
    subclaims = _str_tuple(task.get("subclaim_replay_obligations", []))
    related = _str_tuple(task.get("related_proof_obligations", []))[:16]
    retrieval_hits = _retrieval_hit_obligations(attempt)
    theorem_name = _target_theorem_name(str(attempt.get("formal_statement", "")), display_name)
    bridge_name = _candidate_bridge_lemma_name(display_name, theorem_name)
    repair_class = "model_regeneration_from_exact_feedback"
    steps = (
        "inspect the complete current candidate and exact verifier diagnostics",
        "return one complete revised candidate for the unchanged theorem target",
        "rerun the candidate and preserve the next verifier result verbatim",
    )
    proof_template = ""
    acceptance_gate = str(row.get("acceptance_gate") or task.get("acceptance_gate", ""))
    latest_attempt_id = str(row.get("latest_attempt_id") or attempt.get("attempt_id", ""))
    if not replay_id:
        errors.append("replay_id missing")
    if not display_name:
        errors.append("display_name missing")
    if not acceptance_gate:
        errors.append("acceptance_gate missing")
    if not subclaims and not retrieval_hits:
        errors.append("no subclaim or retrieval obligations available for repair")
    packet_id = (
        "formal_verifier_replay_repair:"
        f"{stable_hash([replay_id, error_category, subclaims, retrieval_hits, bridge_name])[:16]}"
    )
    return FormalVerifierReplayRepairPacket(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_SCHEMA_VERSION,
        packet_id=packet_id,
        replay_id=replay_id,
        source_queue_item_id=str(row.get("source_queue_item_id") or task.get("source_queue_item_id", "")),
        route_id=str(row.get("route_id") or task.get("route_id", "")),
        task_id=str(row.get("task_id") or task.get("task_id", "")),
        theorem_goal_id=str(row.get("theorem_goal_id") or task.get("theorem_goal_id", "")),
        display_name=display_name,
        replay_mode=str(row.get("replay_mode") or task.get("replay_mode", "")),
        owner_agent="formal_verifier",
        latest_attempt_id=latest_attempt_id,
        first_error_category=error_category,
        first_error=str(row.get("first_error", "")),
        replay_policy_update=str(row.get("replay_policy_update", "")),
        repair_class=repair_class,
        priority_score=_priority_score(task, row),
        acceptance_gate=acceptance_gate,
        required_primitives=required_primitives,
        subclaim_replay_obligations=subclaims,
        related_proof_obligations=related,
        retrieval_hit_obligations=retrieval_hits,
        target_theorem_name=theorem_name,
        candidate_bridge_lemma_name=bridge_name,
        route_specific_repair_steps=steps,
        proof_body_template_not_verified=proof_template,
        training_prompt=_training_prompt(row, task, attempt, steps),
        training_completion=json.dumps(
            {
                "candidate_source": "complete revised Lean source supplied by the proof agent",
                "claim_status": "repair_packet_not_proof_evidence",
                "acceptance_gate": acceptance_gate,
            },
            sort_keys=True,
        ),
        repair_acceptance_gate=(
            "rerun formal-verifier-replay-attempts on the repaired proof body and require "
            "AXLE/local Lean kernel verification with no placeholders before marking the route proved"
        ),
        proof_evidence_boundary=(
            "This repair packet is not proof evidence. It becomes evidence only if the "
            "repaired full-route replay attempt passes AXLE/local Lean without placeholders."
        ),
        with_attempt=bool(latest_attempt_id or _safe_int(row.get("n_attempts", 0)) > 0 or attempt),
        with_exact_subclaims=bool(subclaims),
        ok=not errors,
        errors=tuple(errors),
    )


def _priority_score(task: dict[str, Any], row: dict[str, Any]) -> int:
    score = int(task.get("replay_priority_score", task.get("queue_priority_score", 0)) or 0)
    error_category = str(row.get("first_error_category", ""))
    score += {
        "tactic_no_progress": 40,
        "missing_identifier": 35,
        "type_mismatch": 30,
        "placeholder_or_gap": 25,
    }.get(error_category, 10)
    replay_mode = str(row.get("replay_mode") or task.get("replay_mode", ""))
    if replay_mode == "kernel_calibrated_subclaim_replay_then_theorem_composition":
        score += 15
    if str(task.get("source_trust_calibration_status", "")) == "kernel_smoke_overlap_verified":
        score += 15
    return score


def _target_theorem_name(formal_statement: str, display_name: str) -> str:
    for line in formal_statement.splitlines():
        stripped = line.strip()
        if not stripped.startswith("theorem "):
            continue
        match = re.match(r"theorem\s+([A-Za-z_][A-Za-z0-9_']*)\b", stripped)
        if match:
            return match.group(1)
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", display_name).strip("_")
    return cleaned or "replay_target"


def _candidate_bridge_lemma_name(display_name: str, theorem_name: str) -> str:
    base = theorem_name or display_name
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", base).strip("_") or "replay_target"
    if cleaned.endswith("_skeleton"):
        cleaned = cleaned[: -len("_skeleton")]
    return f"{cleaned}_replay_bridge"


def _retrieval_hit_obligations(attempt: dict[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for hit in attempt.get("retrieval_hits", []) or []:
        if isinstance(hit, dict):
            obligation_id = str(hit.get("obligation_id") or hit.get("id") or "")
            if obligation_id:
                values.append(obligation_id)
        elif str(hit):
            values.append(str(hit))
    return tuple(dict.fromkeys(values))


def _training_prompt(
    row: dict[str, Any],
    task: dict[str, Any],
    attempt: dict[str, Any],
    steps: tuple[str, ...],
) -> str:
    subclaims = _str_tuple(task.get("subclaim_replay_obligations", []))
    retrieval_hits = _retrieval_hit_obligations(attempt)
    return "\n".join(
        [
            "You are revising a failed full-route FormalVerifier candidate.",
            "Return one complete revised Lean candidate. Keep the theorem target unchanged.",
            "",
            f"Replay id: {row.get('replay_id', '')}",
            f"Route: {row.get('display_name', '')}",
            f"Replay mode: {row.get('replay_mode', '')}",
            f"Error category: {row.get('first_error_category', '')}",
            f"First error: {row.get('first_error', '')}",
            "",
            "Subclaim replay obligations:",
            "\n".join(f"- {name}" for name in subclaims) or "- none",
            "",
            "Attempt retrieval hits:",
            "\n".join(f"- {name}" for name in retrieval_hits) or "- none",
            "",
            "Execution loop contract:",
            "\n".join(f"- {step}" for step in steps),
            "",
            "Complete current formal statement:",
            "```lean",
            str(attempt.get("formal_statement", "")).strip(),
            "```",
            "",
            "Complete current proof body:",
            "```lean",
            str(attempt.get("proof_body", "")).strip(),
            "```",
        ]
    )


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Replay Repair Packets",
        "",
        f"- Replay attempts: `{payload.get('formal_verifier_replay_attempt_manifest')}`",
        f"- Calibration: `{payload.get('formal_verifier_replay_calibration_manifest')}`",
        f"- Repair packets: {payload.get('n_ok')}/{payload.get('n_repair_packets')} audit-clean",
        f"- Tactic no progress: {payload.get('n_tactic_no_progress')}",
        f"- Missing identifier: {payload.get('n_missing_identifier')}",
        f"- With exact replay subclaims: {payload.get('n_with_exact_subclaims')}",
        "",
        "Repair packets are route-specific work plans, not proof evidence.",
        "",
        "## Packets",
        "",
    ]
    packets = payload.get("packets", [])
    if not isinstance(packets, list) or not packets:
        lines.append("No failed replay attempts require repair packets.")
    else:
        for packet in packets[:30]:
            if not isinstance(packet, dict):
                continue
            lines.append(
                f"- `{packet.get('display_name')}` ({packet.get('repair_class')}): "
                f"{packet.get('candidate_bridge_lemma_name')}"
            )
            lines.append(f"  gate: {packet.get('repair_acceptance_gate')}")
            lines.append(f"  boundary: {packet.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

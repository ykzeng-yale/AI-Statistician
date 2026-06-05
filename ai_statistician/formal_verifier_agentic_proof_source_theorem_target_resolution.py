from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_SOURCE_THEOREM_TARGET_RESOLUTION_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "SOURCE_THEOREM_TARGET_RESOLUTION_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic source-theorem target-resolution rows resolve route-ledger targets "
    "for artifact-kernel-verified proof probes. They are not proof evidence; "
    "source theorem proof evidence starts only after the resolved theorem target "
    "itself passes AXLE/local Lean full-route verification."
)


@dataclass(frozen=True)
class FormalVerifierAgenticProofSourceTheoremTargetResolutionRow:
    schema_version: int
    target_resolution_id: str
    source_theorem_promotion_id: str
    artifact_verification_id: str
    materialization_id: str
    execution_queue_id: str
    display_name: str
    target_theorem_name: str
    candidate_artifact_path: str
    promotion_status: str
    artifact_kernel_verified: bool
    source_theorem_target_known_input: bool
    resolution_status: str
    match_source: str
    match_key: str
    source_route_id: str
    source_queue_item_id: str
    source_replay_id: str
    task_id: str
    question_id: str
    problem_class: str
    theorem_goal_id: str
    source_theorem_skeleton: str
    source_theorem_statement: str
    source_theorem_lean_file: str
    source_theorem_target_known: bool
    overlay_row: dict[str, object]
    owner_agent: str
    action_type: str
    priority: str
    required_gate: str
    command_plan: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_source_theorem_target_resolution(
    formal_verifier_agentic_proof_source_theorem_promotion_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    formal_verifier_queue_dir: Path | None = None,
    formal_verifier_replay_dir: Path | None = None,
) -> dict[str, object]:
    """Resolve real source-theorem targets for artifact-level proof probes."""

    errors: list[str] = []
    promotion_manifest_path = (
        formal_verifier_agentic_proof_source_theorem_promotion_queue_dir
        / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json"
    )
    promotion_payload = _read_json(promotion_manifest_path, errors)
    promotion_rows = [
        row for row in promotion_payload.get("rows", []) if isinstance(row, dict)
    ]
    queue_manifest_path = (
        formal_verifier_queue_dir / "formal_verifier_queue_manifest.json"
        if formal_verifier_queue_dir is not None
        else Path("__missing__")
    )
    replay_manifest_path = (
        formal_verifier_replay_dir / "formal_verifier_replay_manifest.json"
        if formal_verifier_replay_dir is not None
        else Path("__missing__")
    )
    queue_payload = _read_json(queue_manifest_path, errors) if formal_verifier_queue_dir else {}
    replay_payload = _read_json(replay_manifest_path, errors) if formal_verifier_replay_dir else {}
    route_index = _route_index(queue_payload=queue_payload, replay_payload=replay_payload)
    rows = [
        _resolution_row(
            row,
            route_index=route_index,
            promotion_manifest_path=promotion_manifest_path,
            queue_manifest_path=queue_manifest_path if formal_verifier_queue_dir else None,
            replay_manifest_path=replay_manifest_path if formal_verifier_replay_dir else None,
        )
        for row in promotion_rows
    ]
    by_status = Counter(row.resolution_status for row in rows)
    overlay_rows = [row.overlay_row for row in rows if row.overlay_row]
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_AGENTIC_PROOF_SOURCE_THEOREM_TARGET_RESOLUTION_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_source_theorem_promotion_queue_dir": str(
            formal_verifier_agentic_proof_source_theorem_promotion_queue_dir
        ),
        "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest": str(
            promotion_manifest_path
        ),
        "formal_verifier_queue_dir": str(formal_verifier_queue_dir or ""),
        "formal_verifier_queue_manifest": str(queue_manifest_path)
        if formal_verifier_queue_dir
        else "",
        "formal_verifier_replay_dir": str(formal_verifier_replay_dir or ""),
        "formal_verifier_replay_manifest": str(replay_manifest_path)
        if formal_verifier_replay_dir
        else "",
        "n_promotion_rows": len(promotion_rows),
        "n_target_resolution_rows": len(rows),
        "n_resolved_source_theorem_targets": by_status.get(
            "RESOLVED_SOURCE_THEOREM_TARGET_FOR_INTEGRATION",
            0,
        ),
        "n_needs_route_ledger_match": by_status.get("NEEDS_ROUTE_LEDGER_MATCH", 0),
        "n_already_source_theorem_target_known": by_status.get(
            "ALREADY_SOURCE_THEOREM_TARGET_KNOWN",
            0,
        ),
        "n_blocked_artifact_kernel_required": by_status.get(
            "BLOCKED_ARTIFACT_KERNEL_REQUIRED",
            0,
        ),
        "n_overlay_rows": len(overlay_rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_resolution_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "overlay_rows": overlay_rows,
        "target_resolution_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "target-resolution overlays are route metadata, not theorem proof evidence",
            "resolved source theorem statements still require bounded source integration",
            "artifact-kernel verification remains artifact-level evidence until full-route verification succeeds",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_agentic_proof_source_theorem_target_resolution_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formal_verifier_agentic_proof_source_theorem_target_resolution.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formal_verifier_agentic_proof_source_theorem_target_resolution_overlays.jsonl"
        ).write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in overlay_rows)
            + ("\n" if overlay_rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formal_verifier_agentic_proof_source_theorem_target_resolution.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _resolution_row(
    row: dict[str, Any],
    *,
    route_index: dict[str, dict[str, Any]],
    promotion_manifest_path: Path,
    queue_manifest_path: Path | None,
    replay_manifest_path: Path | None,
) -> FormalVerifierAgenticProofSourceTheoremTargetResolutionRow:
    errors: list[str] = []
    source_theorem_promotion_id = str(row.get("source_theorem_promotion_id", ""))
    artifact_verification_id = str(row.get("artifact_verification_id", ""))
    materialization_id = str(row.get("materialization_id", ""))
    execution_queue_id = str(row.get("execution_queue_id", ""))
    display_name = str(row.get("display_name", ""))
    target_theorem_name = str(row.get("target_theorem_name", ""))
    candidate_artifact_path = str(row.get("candidate_artifact_path", ""))
    promotion_status = str(row.get("promotion_status", ""))
    artifact_kernel_verified = bool(row.get("artifact_kernel_verified", False))
    source_target_known_input = bool(row.get("source_theorem_target_known", False))
    if not source_theorem_promotion_id:
        errors.append("source_theorem_promotion_id missing")
    if not artifact_verification_id:
        errors.append("artifact_verification_id missing")
    if not candidate_artifact_path:
        errors.append("candidate_artifact_path missing")

    match, match_key = _match_route(row, route_index)
    if source_target_known_input:
        resolution_status = "ALREADY_SOURCE_THEOREM_TARGET_KNOWN"
        action_type = "keep_existing_source_theorem_target"
        required_gate = "rerun source-theorem integration with the existing resolved target"
        source_target_known = True
    elif not artifact_kernel_verified:
        resolution_status = "BLOCKED_ARTIFACT_KERNEL_REQUIRED"
        action_type = "repair_artifact_before_source_target_resolution"
        required_gate = "artifact verifier reports artifact_kernel_verified=true"
        source_target_known = False
    elif match:
        resolution_status = "RESOLVED_SOURCE_THEOREM_TARGET_FOR_INTEGRATION"
        action_type = "attach_resolved_source_theorem_target_overlay"
        required_gate = (
            "rerun source-theorem promotion with this resolved route target, "
            "then attempt full-route AXLE/local Lean verification"
        )
        source_target_known = True
    else:
        resolution_status = "NEEDS_ROUTE_LEDGER_MATCH"
        action_type = "resolve_missing_source_theorem_route_match"
        required_gate = (
            "route ledger names the exact source theorem statement, route id, "
            "or Lean file before source integration"
        )
        source_target_known = False

    source_route_id = str(match.get("route_id", "")) if match else ""
    source_queue_item_id = str(match.get("item_id", "")) if match else ""
    source_replay_id = str(match.get("replay_id", "")) if match else ""
    task_id = str(match.get("task_id", "")) if match else ""
    question_id = str(match.get("question_id", "")) if match else ""
    problem_class = str(match.get("problem_class", "")) if match else ""
    theorem_goal_id = str(match.get("theorem_goal_id", "")) if match else ""
    source_theorem_skeleton = str(match.get("theorem_skeleton", "")) if match else ""
    source_theorem_statement = str(match.get("theorem_statement", "")) if match else ""
    source_theorem_lean_file = str(match.get("source_theorem_lean_file", "")) if match else ""
    overlay_row: dict[str, object] = {}
    if source_target_known:
        overlay_row = {
            "artifact_verification_id": artifact_verification_id,
            "source_theorem_target_known": True,
            "source_theorem_target_resolution_id": (
                "formal_verifier_agentic_proof_source_theorem_target_resolution:"
                + stable_hash([source_theorem_promotion_id, match_key])[:16]
            ),
            "source_theorem_route_id": source_route_id,
            "source_theorem_queue_item_id": source_queue_item_id,
            "source_theorem_replay_id": source_replay_id,
            "source_theorem_task_id": task_id,
            "source_theorem_question_id": question_id,
            "source_theorem_goal_id": theorem_goal_id,
            "source_theorem_statement": source_theorem_statement,
            "source_theorem_skeleton": source_theorem_skeleton,
            "source_theorem_lean_file": source_theorem_lean_file,
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        }
    evidence_paths = tuple(
        str(path)
        for path in (
            promotion_manifest_path,
            queue_manifest_path,
            replay_manifest_path,
            Path(candidate_artifact_path) if candidate_artifact_path else None,
        )
        if path is not None and str(path)
    )
    return FormalVerifierAgenticProofSourceTheoremTargetResolutionRow(
        schema_version=(
            FORMAL_VERIFIER_AGENTIC_PROOF_SOURCE_THEOREM_TARGET_RESOLUTION_SCHEMA_VERSION
        ),
        target_resolution_id=(
            "formal_verifier_agentic_proof_source_theorem_target_resolution:"
            + stable_hash([source_theorem_promotion_id, artifact_verification_id, match_key])[:16]
        ),
        source_theorem_promotion_id=source_theorem_promotion_id,
        artifact_verification_id=artifact_verification_id,
        materialization_id=materialization_id,
        execution_queue_id=execution_queue_id,
        display_name=display_name,
        target_theorem_name=target_theorem_name,
        candidate_artifact_path=candidate_artifact_path,
        promotion_status=promotion_status,
        artifact_kernel_verified=artifact_kernel_verified,
        source_theorem_target_known_input=source_target_known_input,
        resolution_status=resolution_status,
        match_source=str(match.get("match_source", "")) if match else "",
        match_key=match_key,
        source_route_id=source_route_id,
        source_queue_item_id=source_queue_item_id,
        source_replay_id=source_replay_id,
        task_id=task_id,
        question_id=question_id,
        problem_class=problem_class,
        theorem_goal_id=theorem_goal_id,
        source_theorem_skeleton=source_theorem_skeleton,
        source_theorem_statement=source_theorem_statement,
        source_theorem_lean_file=source_theorem_lean_file,
        source_theorem_target_known=source_target_known,
        overlay_row=overlay_row,
        owner_agent="formal_verifier_source_theorem_target_resolver",
        action_type=action_type,
        priority="high" if artifact_kernel_verified else "medium",
        required_gate=required_gate,
        command_plan=(
            "use the resolved route ledger target to construct a real source theorem integration attempt",
            "keep the route-probe artifact as artifact-only kernel evidence",
            "run AXLE/local Lean on the resolved source theorem target",
            "promote only after full-route source theorem verification succeeds",
        ),
        evidence_paths=evidence_paths,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _route_index(
    *,
    queue_payload: dict[str, Any],
    replay_payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in queue_payload.get("rows", []):
        if isinstance(row, dict):
            _index_route(index, row, match_source="formal_verifier_queue")
    for row in replay_payload.get("tasks", []):
        if isinstance(row, dict):
            _index_route(index, row, match_source="formal_verifier_replay")
    return index


def _index_route(index: dict[str, dict[str, Any]], row: dict[str, Any], *, match_source: str) -> None:
    enriched = dict(row)
    enriched["match_source"] = match_source
    keys = {
        _norm(row.get("target_theorem_name", "")),
        _norm(row.get("display_name", "")),
        _norm(row.get("task_id", "")),
        _norm(row.get("route_id", "")),
        _norm(row.get("item_id", "")),
        _norm(row.get("replay_id", "")),
        _norm(":".join(str(row.get(key, "")) for key in ("question_id", "theorem_goal_id"))),
        _norm("formal:" + ":".join(str(row.get(key, "")) for key in ("question_id", "theorem_goal_id"))),
    }
    for key in keys:
        if key and key not in index:
            index[key] = enriched


def _match_route(row: dict[str, Any], route_index: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], str]:
    keys = (
        _norm(row.get("target_theorem_name", "")),
        _norm(row.get("display_name", "")),
        _norm(row.get("execution_queue_id", "")),
        _norm(row.get("source_theorem_route_id", "")),
    )
    for key in keys:
        if key in route_index:
            return route_index[key], key
    target_tokens = set(_tokens(row.get("target_theorem_name", ""))) | set(
        _tokens(row.get("display_name", ""))
    )
    best_key = ""
    best_row: dict[str, Any] = {}
    best_score = 0
    for key, candidate in route_index.items():
        candidate_tokens = set(_tokens(key))
        score = len(target_tokens & candidate_tokens)
        if score > best_score:
            best_score = score
            best_key = key
            best_row = candidate
    if best_score >= 3:
        return best_row, best_key
    return {}, ""


def _tokens(value: object) -> tuple[str, ...]:
    return tuple(token for token in re.findall(r"[a-z0-9]+", str(value).lower()) if token)


def _norm(value: object) -> str:
    return ":".join(_tokens(value))


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
        "# Formal Verifier Agentic Source-Theorem Target Resolution",
        "",
        f"- Rows: {payload.get('n_ok')}/{payload.get('n_target_resolution_rows')}",
        f"- Resolved targets: {payload.get('n_resolved_source_theorem_targets')}",
        f"- Needs route-ledger match: {payload.get('n_needs_route_ledger_match')}",
        f"- Overlay rows: {payload.get('n_overlay_rows')}",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('target_theorem_name')}`: {row.get('resolution_status')} "
            f"match={row.get('match_source')} source_known={row.get('source_theorem_target_known')}"
        )
        lines.append(f"  action: `{row.get('action_type')}`")
        if row.get("errors"):
            lines.append(f"  errors: {row.get('errors')}")
    return "\n".join(lines) + "\n"

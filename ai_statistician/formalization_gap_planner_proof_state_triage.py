from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMALIZATION_GAP_PLANNER_PROOF_STATE_TRIAGE_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_PROOF_STATE_TRIAGE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner proof-state triage rows are route-level work "
    "orders for proof workers. They prioritize materialization, local Lean "
    "repair, and source-discovery work, but they are not theorem proof "
    "evidence. Only target-prover kernel verification can prove a theorem or "
    "bridge lemma."
)


@dataclass(frozen=True)
class FormalizationGapPlannerProofStateTriageRow:
    schema_version: int
    triage_item_id: str
    route_revision_overlay_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    revision_status: str
    triage_class: str
    owner_agent: str
    applied_prover_attempt_statuses: tuple[str, ...]
    applied_prover_diagnostic_signatures: tuple[str, ...]
    residual_goals: tuple[str, ...]
    added_delta_primitives: tuple[str, ...]
    recommended_next_action: str
    required_artifacts: tuple[str, ...]
    recommended_tools: tuple[str, ...]
    execution_commands: tuple[str, ...]
    priority_score: int
    rank: int
    required_gate: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_proof_state_triage(
    formalization_gap_planner_route_revision_overlay_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Turn route-level proof-state statuses into prioritized proof work items."""

    errors: list[str] = []
    overlay_manifest_path = (
        formalization_gap_planner_route_revision_overlay_dir
        / "formalization_gap_planner_route_revision_overlay_manifest.json"
    )
    overlay_payload = _read_json(overlay_manifest_path, errors)
    overlay_rows = [
        row for row in overlay_payload.get("rows", []) if isinstance(row, dict)
    ]
    raw_rows = [
        _triage_row(row)
        for row in overlay_rows
        if _str_tuple(row.get("applied_prover_attempt_statuses", []))
    ]
    rows = _rank_rows(raw_rows)
    by_triage_class = Counter(row.triage_class for row in rows)
    by_owner = Counter(row.owner_agent for row in rows)
    by_attempt_status = Counter(
        status for row in rows for status in row.applied_prover_attempt_statuses
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_PROOF_STATE_TRIAGE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_proof_state_triage",
        "formalization_gap_planner_route_revision_overlay_dir": str(
            formalization_gap_planner_route_revision_overlay_dir
        ),
        "formalization_gap_planner_route_revision_overlay_manifest": str(
            overlay_manifest_path
        ),
        "n_overlay_rows": len(overlay_rows),
        "n_triage_items": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_blocked_input": sum(1 for row in rows if not row.ok),
        "n_formal_gap_scaffold_items": by_attempt_status.get(
            "formal_gap_scaffold_blocked", 0
        ),
        "n_local_lean_failed_items": by_attempt_status.get("local_lean_failed", 0),
        "n_non_lean_skeleton_items": by_attempt_status.get("non_lean_skeleton", 0),
        "n_with_residual_goals": sum(1 for row in rows if row.residual_goals),
        "n_distinct_diagnostic_signatures": len(
            {
                signature
                for row in rows
                for signature in row.applied_prover_diagnostic_signatures
                if signature
            }
        ),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_triage_class": dict(sorted(by_triage_class.items())),
        "by_owner_agent": dict(sorted(by_owner.items())),
        "by_prover_attempt_status": dict(sorted(by_attempt_status.items())),
        "rows": [asdict(row) for row in rows],
        "triage_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "triage rows are route-level work orders, not proof evidence",
            "formal-gap scaffold blockers require non-placeholder theorem materialization before Lean acceptance matters",
            "local Lean failures still require replay, calibration, and residual-gap validation before promotion",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_proof_state_triage_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_proof_state_triage.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_proof_state_triage.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _triage_row(
    row: dict[str, Any],
) -> FormalizationGapPlannerProofStateTriageRow:
    errors: list[str] = []
    overlay_id = str(row.get("route_revision_overlay_id", ""))
    goal_plan_id = str(row.get("goal_plan_id", ""))
    route_id = str(row.get("route_id", ""))
    display_name = str(row.get("display_name", ""))
    attempt_statuses = _str_tuple(row.get("applied_prover_attempt_statuses", []))
    diagnostic_signatures = _str_tuple(
        row.get("applied_prover_diagnostic_signatures", [])
    )
    residual_goals = _str_tuple(row.get("residual_goals", []))
    added_delta = _str_tuple(row.get("added_delta_primitives", []))

    for field_name, value in (
        ("route_revision_overlay_id", overlay_id),
        ("goal_plan_id", goal_plan_id),
        ("route_id", route_id),
        ("display_name", display_name),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if not attempt_statuses:
        errors.append("applied_prover_attempt_statuses missing")

    triage_class = _triage_class(attempt_statuses)
    owner_agent = _owner_agent(triage_class)
    priority_score = _priority_score(triage_class, residual_goals, added_delta)
    recommended_next_action = _recommended_next_action(triage_class)
    required_artifacts = _required_artifacts(triage_class)
    recommended_tools = _recommended_tools(triage_class)
    execution_commands = _execution_commands(triage_class)
    triage_item_id = "formalization_gap_planner_proof_state_triage:" + stable_hash(
        [overlay_id, route_id, attempt_statuses, diagnostic_signatures, triage_class]
    )[:16]

    return FormalizationGapPlannerProofStateTriageRow(
        schema_version=FORMALIZATION_GAP_PLANNER_PROOF_STATE_TRIAGE_SCHEMA_VERSION,
        triage_item_id=triage_item_id,
        route_revision_overlay_id=overlay_id,
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        revision_status=str(row.get("revision_status", "")),
        triage_class=triage_class,
        owner_agent=owner_agent,
        applied_prover_attempt_statuses=attempt_statuses,
        applied_prover_diagnostic_signatures=diagnostic_signatures,
        residual_goals=residual_goals,
        added_delta_primitives=added_delta,
        recommended_next_action=recommended_next_action,
        required_artifacts=required_artifacts,
        recommended_tools=recommended_tools,
        execution_commands=execution_commands,
        priority_score=priority_score,
        rank=0,
        required_gate=(
            "rerun proof-state adapter, route overlay, verifier replay, and "
            "kernel/residual-gap validation before any proof promotion"
        ),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _triage_class(statuses: tuple[str, ...]) -> str:
    status_set = set(statuses)
    if "formal_gap_scaffold_blocked" in status_set:
        return "materialize_non_placeholder_theorem"
    if "local_lean_failed" in status_set:
        return "repair_local_lean_proof_state"
    if "non_lean_skeleton" in status_set:
        return "materialize_lean_command"
    if "local_lean_unavailable" in status_set:
        return "configure_local_lean_environment"
    return "review_proof_state_status"


def _owner_agent(triage_class: str) -> str:
    return {
        "materialize_non_placeholder_theorem": "formalization_planner",
        "repair_local_lean_proof_state": "formal_verifier",
        "materialize_lean_command": "formalization_planner",
        "configure_local_lean_environment": "tooling_engineer",
    }.get(triage_class, "formal_verifier")


def _priority_score(
    triage_class: str,
    residual_goals: tuple[str, ...],
    added_delta: tuple[str, ...],
) -> int:
    base = {
        "materialize_non_placeholder_theorem": 110,
        "repair_local_lean_proof_state": 95,
        "materialize_lean_command": 80,
        "configure_local_lean_environment": 60,
    }.get(triage_class, 50)
    return base + min(30, 2 * len(residual_goals) + len(added_delta))


def _recommended_next_action(triage_class: str) -> str:
    return {
        "materialize_non_placeholder_theorem": (
            "replace FORMAL_GAP/h_frontier_missing scaffold with the smallest "
            "non-placeholder theorem or bridge lemma required by the route"
        ),
        "repair_local_lean_proof_state": (
            "use Lean diagnostics and local source hits to repair the current "
            "proof state without changing theorem statements"
        ),
        "materialize_lean_command": (
            "turn the route skeleton into a complete Lean theorem/lemma/example "
            "command before running proof-state tools"
        ),
        "configure_local_lean_environment": (
            "configure lake/lean for the target project before replaying proof-state checks"
        ),
    }.get(triage_class, "review proof-state diagnostics and select the next verifier action")


def _required_artifacts(triage_class: str) -> tuple[str, ...]:
    if triage_class == "materialize_non_placeholder_theorem":
        return (
            "non-placeholder Lean theorem or bridge statement",
            "explicit list of discharged and remaining formal gaps",
            "updated route overlay after proof-state rerun",
        )
    if triage_class == "repair_local_lean_proof_state":
        return (
            "candidate Lean proof patch",
            "local Lean diagnostics",
            "patch-rerun calibration manifest",
            "residual-gap validation manifest",
        )
    if triage_class == "materialize_lean_command":
        return (
            "materialized Lean command",
            "proof-state adapter manifest",
            "route revision evidence manifest",
        )
    return ("triage notes", "rerun manifest")


def _recommended_tools(triage_class: str) -> tuple[str, ...]:
    if triage_class == "materialize_non_placeholder_theorem":
        return (
            "goal-conditioned minimal formalization planner",
            "local formal-source adapter",
            "lean-lsp-mcp",
            "proof-state adapter",
        )
    if triage_class == "repair_local_lean_proof_state":
        return (
            "lean_goal",
            "lean_diagnostic_messages",
            "lean_multi_attempt",
            "patch-rerun calibration",
        )
    if triage_class == "materialize_lean_command":
        return ("formal-gap task export", "prover adapter contract", "proof-state adapter")
    return ("doctor", "lake env lean", "proof-state adapter")


def _execution_commands(triage_class: str) -> tuple[str, ...]:
    if triage_class == "materialize_non_placeholder_theorem":
        return (
            "formalization-gap-planner-local-formal-source-adapter",
            "formalization-gap-planner-local-proof-state-adapter",
            "formalization-gap-planner-refinement-evidence",
            "formalization-gap-planner-route-revision-overlay",
        )
    if triage_class == "repair_local_lean_proof_state":
        return (
            "formal-verifier-replay-repair-patch-rerun-attempts",
            "formal-verifier-replay-repair-patch-rerun-calibration",
            "formal-verifier-replay-repair-patch-rerun-residual-response-validation",
        )
    if triage_class == "materialize_lean_command":
        return (
            "formal-gap-task-export",
            "formalization-gap-planner-prover-adapter-contract",
            "formalization-gap-planner-local-proof-state-adapter",
        )
    return ("doctor",)


def _rank_rows(
    rows: list[FormalizationGapPlannerProofStateTriageRow],
) -> list[FormalizationGapPlannerProofStateTriageRow]:
    ranked = sorted(
        rows,
        key=lambda row: (-row.priority_score, row.display_name, row.triage_item_id),
    )
    return [
        FormalizationGapPlannerProofStateTriageRow(
            **{**asdict(row), "rank": index}
        )
        for index, row in enumerate(ranked, start=1)
    ]


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        try:
            values = tuple(values)
        except TypeError:
            return tuple()
    return tuple(sorted(dict.fromkeys(str(item) for item in values if str(item))))


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
        "# Formalization Gap Planner Proof-State Triage",
        "",
        f"- Overlay rows: {payload.get('n_overlay_rows')}",
        f"- Triage items: {payload.get('n_triage_items')}",
        f"- Formal-gap scaffold items: {payload.get('n_formal_gap_scaffold_items')}",
        f"- Local Lean failed items: {payload.get('n_local_lean_failed_items')}",
        f"- Non-Lean skeleton items: {payload.get('n_non_lean_skeleton_items')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
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
            f"- #{row.get('rank')} `{row.get('display_name')}` "
            f"{row.get('triage_class')} score={row.get('priority_score')} "
            f"owner={row.get('owner_agent')}"
        )
        lines.append(f"  next: {row.get('recommended_next_action')}")
    return "\n".join(lines) + "\n"

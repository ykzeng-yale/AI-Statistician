from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMALIZATION_GAP_PLANNER_PROOF_STATE_TRIAGE_SCHEMA_VERSION = 1
PROOF_STATE_TRIAGE_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-proof-state-triage-row:1"
)
PROOF_EVIDENCE_STATUS = "FORMALIZATION_GAP_PLANNER_PROOF_STATE_TRIAGE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner proof-state triage rows are route-level work "
    "orders for proof workers. They prioritize materialization, target-prover "
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
    prover_triage_class: str
    owner_agent: str
    applied_prover_attempt_statuses: tuple[str, ...]
    applied_prover_attempt_classes: tuple[str, ...]
    target_prover_families: tuple[str, ...]
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
    row_dicts = [asdict(row) for row in rows]
    triage_row_schema = proof_state_triage_row_json_schema()
    row_schema_errors = [
        validate_proof_state_triage_row(row, triage_row_schema)
        for row in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    by_triage_class = Counter(row.triage_class for row in rows)
    by_owner = Counter(row.owner_agent for row in rows)
    by_attempt_status = Counter(
        status for row in rows for status in row.applied_prover_attempt_statuses
    )
    by_attempt_class = Counter(
        attempt_class
        for row in rows
        for attempt_class in row.applied_prover_attempt_classes
    )
    by_prover_triage_class = Counter(row.prover_triage_class for row in rows)
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
        "n_target_prover_failed_items": by_attempt_class.get(
            "target_prover_failed", 0
        ),
        "n_target_prover_unavailable_items": by_attempt_class.get(
            "target_prover_unavailable", 0
        ),
        "n_non_target_prover_skeleton_items": by_attempt_class.get(
            "non_target_prover_skeleton", 0
        ),
        "target_prover_families": _str_tuple(
            family for row in rows for family in row.target_prover_families
        ),
        "n_with_residual_goals": sum(1 for row in rows if row.residual_goals),
        "n_distinct_diagnostic_signatures": len(
            {
                signature
                for row in rows
                for signature in row.applied_prover_diagnostic_signatures
                if signature
            }
        ),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": len(row_schema_errors) - n_row_schema_valid,
        "row_schema_errors": row_schema_errors,
        "triage_row_schema": triage_row_schema,
        "all_ok": (
            not errors
            and all(row.ok for row in rows)
            and len(row_schema_errors) == n_row_schema_valid
        ),
        "errors": errors,
        "by_triage_class": dict(sorted(by_triage_class.items())),
        "by_prover_triage_class": dict(sorted(by_prover_triage_class.items())),
        "by_owner_agent": dict(sorted(by_owner.items())),
        "by_prover_attempt_status": dict(sorted(by_attempt_status.items())),
        "by_prover_attempt_class": dict(sorted(by_attempt_class.items())),
        "rows": row_dicts,
        "triage_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "triage rows are route-level work orders, not proof evidence",
            "formal-gap scaffold blockers require non-placeholder theorem materialization before Lean acceptance matters",
            "target-prover failures still require replay, calibration, and residual-gap validation before promotion",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_proof_state_triage_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_proof_state_triage_row.schema.json"
        ).write_text(json.dumps(triage_row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_proof_state_triage.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in row_dicts)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_proof_state_triage.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def proof_state_triage_row_json_schema() -> dict[str, object]:
    required = [
        "schema_version",
        "triage_item_id",
        "route_revision_overlay_id",
        "goal_plan_id",
        "route_id",
        "display_name",
        "revision_status",
        "triage_class",
        "prover_triage_class",
        "owner_agent",
        "applied_prover_attempt_statuses",
        "applied_prover_attempt_classes",
        "target_prover_families",
        "applied_prover_diagnostic_signatures",
        "residual_goals",
        "added_delta_primitives",
        "recommended_next_action",
        "required_artifacts",
        "recommended_tools",
        "execution_commands",
        "priority_score",
        "rank",
        "required_gate",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
        "errors",
    ]
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PROOF_STATE_TRIAGE_ROW_SCHEMA_ID,
        "title": "Formalization gap planner proof-state triage row",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_PROOF_STATE_TRIAGE_SCHEMA_VERSION,
            },
            "triage_item_id": {"type": "string", "minLength": 1},
            "route_revision_overlay_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "revision_status": {"type": "string"},
            "triage_class": {
                "type": "string",
                "enum": [
                    "materialize_non_placeholder_theorem",
                    "repair_local_lean_proof_state",
                    "materialize_lean_command",
                    "configure_local_lean_environment",
                    "review_proof_state_status",
                ],
            },
            "prover_triage_class": {
                "type": "string",
                "enum": [
                    "materialize_non_placeholder_theorem",
                    "repair_target_prover_proof_state",
                    "materialize_target_prover_command",
                    "configure_target_prover_environment",
                    "review_proof_state_status",
                ],
            },
            "owner_agent": {
                "type": "string",
                "enum": [
                    "formalization_planner",
                    "formal_verifier",
                    "tooling_engineer",
                ],
            },
            "applied_prover_attempt_statuses": string_array,
            "applied_prover_attempt_classes": string_array,
            "target_prover_families": string_array,
            "applied_prover_diagnostic_signatures": string_array,
            "residual_goals": string_array,
            "added_delta_primitives": string_array,
            "recommended_next_action": {"type": "string", "minLength": 1},
            "required_artifacts": string_array,
            "recommended_tools": string_array,
            "execution_commands": string_array,
            "priority_score": {"type": "integer"},
            "rank": {"type": "integer"},
            "required_gate": {"type": "string", "minLength": 1},
            "proof_evidence_status": {
                "type": "string",
                "const": PROOF_EVIDENCE_STATUS,
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_proof_state_triage_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    row_schema = schema or proof_state_triage_row_json_schema()
    required = tuple(row_schema.get("required", ()))
    errors: list[str] = []
    for field_name in required:
        if field_name not in row:
            errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if field_name in row and isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(
                        field_name,
                        row[field_name],
                        field_schema,
                    )
                )
    allowed = set(required)
    for field_name in row:
        if field_name not in allowed:
            errors.append(f"{field_name} unexpected")
    return errors


def _triage_row(
    row: dict[str, Any],
) -> FormalizationGapPlannerProofStateTriageRow:
    errors: list[str] = []
    overlay_id = str(row.get("route_revision_overlay_id", ""))
    goal_plan_id = str(row.get("goal_plan_id", ""))
    route_id = str(row.get("route_id", ""))
    display_name = str(row.get("display_name", ""))
    attempt_statuses = _str_tuple(row.get("applied_prover_attempt_statuses", []))
    attempt_classes = _str_tuple(
        row.get(
            "applied_prover_attempt_classes",
            [
                _prover_attempt_class(status)
                for status in attempt_statuses
            ],
        )
    )
    target_prover_families = _str_tuple(
        row.get(
            "target_prover_families",
            [row.get("target_prover_family", "")],
        )
    )
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
    prover_triage_class = _prover_triage_class(attempt_classes, attempt_statuses)
    owner_agent = _owner_agent(prover_triage_class)
    priority_score = _priority_score(prover_triage_class, residual_goals, added_delta)
    recommended_next_action = _recommended_next_action(
        prover_triage_class,
        target_prover_families,
    )
    required_artifacts = _required_artifacts(prover_triage_class)
    recommended_tools = _recommended_tools(prover_triage_class, target_prover_families)
    execution_commands = _execution_commands(prover_triage_class)
    triage_item_id = "formalization_gap_planner_proof_state_triage:" + stable_hash(
        [
            overlay_id,
            route_id,
            attempt_statuses,
            attempt_classes,
            diagnostic_signatures,
            triage_class,
            prover_triage_class,
        ]
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
        prover_triage_class=prover_triage_class,
        owner_agent=owner_agent,
        applied_prover_attempt_statuses=attempt_statuses,
        applied_prover_attempt_classes=attempt_classes,
        target_prover_families=target_prover_families,
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


def _prover_triage_class(
    attempt_classes: tuple[str, ...],
    attempt_statuses: tuple[str, ...],
) -> str:
    class_set = set(attempt_classes)
    if "formal_gap_scaffold_blocked" in class_set:
        return "materialize_non_placeholder_theorem"
    if "target_prover_failed" in class_set:
        return "repair_target_prover_proof_state"
    if "non_target_prover_skeleton" in class_set:
        return "materialize_target_prover_command"
    if "target_prover_unavailable" in class_set:
        return "configure_target_prover_environment"
    legacy_class = _triage_class(attempt_statuses)
    return {
        "repair_local_lean_proof_state": "repair_target_prover_proof_state",
        "materialize_lean_command": "materialize_target_prover_command",
        "configure_local_lean_environment": "configure_target_prover_environment",
    }.get(legacy_class, legacy_class)


def _prover_attempt_class(attempt_status: str) -> str:
    return {
        "local_lean_scaffold_accepted": "target_prover_scaffold_accepted",
        "local_lean_failed": "target_prover_failed",
        "local_lean_unavailable": "target_prover_unavailable",
        "non_lean_skeleton": "non_target_prover_skeleton",
        "failed_with_residual_goals": "target_prover_failed",
        "placeholder_blocked": "placeholder_blocked",
        "formal_gap_scaffold_blocked": "formal_gap_scaffold_blocked",
        "missing_theorem_skeleton": "missing_theorem_skeleton",
    }.get(attempt_status, attempt_status)


def _owner_agent(triage_class: str) -> str:
    return {
        "materialize_non_placeholder_theorem": "formalization_planner",
        "repair_target_prover_proof_state": "formal_verifier",
        "repair_local_lean_proof_state": "formal_verifier",
        "materialize_target_prover_command": "formalization_planner",
        "materialize_lean_command": "formalization_planner",
        "configure_target_prover_environment": "tooling_engineer",
        "configure_local_lean_environment": "tooling_engineer",
    }.get(triage_class, "formal_verifier")


def _priority_score(
    triage_class: str,
    residual_goals: tuple[str, ...],
    added_delta: tuple[str, ...],
) -> int:
    base = {
        "materialize_non_placeholder_theorem": 110,
        "repair_target_prover_proof_state": 95,
        "repair_local_lean_proof_state": 95,
        "materialize_target_prover_command": 80,
        "materialize_lean_command": 80,
        "configure_target_prover_environment": 60,
        "configure_local_lean_environment": 60,
    }.get(triage_class, 50)
    return base + min(30, 2 * len(residual_goals) + len(added_delta))


def _recommended_next_action(
    triage_class: str,
    target_prover_families: tuple[str, ...] = (),
) -> str:
    target = _target_prover_label(target_prover_families)
    return {
        "materialize_non_placeholder_theorem": (
            "replace FORMAL_GAP/h_frontier_missing scaffold with the smallest "
            "non-placeholder theorem or bridge lemma required by the route"
        ),
        "repair_target_prover_proof_state": (
            f"use {target} diagnostics and formal-source hits to repair the "
            "current proof state without changing theorem statements"
        ),
        "repair_local_lean_proof_state": (
            "use Lean diagnostics and local source hits to repair the current "
            "proof state without changing theorem statements"
        ),
        "materialize_target_prover_command": (
            f"turn the route skeleton into a complete {target} theorem/lemma/example "
            "command before running proof-state tools"
        ),
        "materialize_lean_command": (
            "turn the route skeleton into a complete Lean theorem/lemma/example "
            "command before running proof-state tools"
        ),
        "configure_target_prover_environment": (
            f"configure the {target} project before replaying proof-state checks"
        ),
        "configure_local_lean_environment": (
            "configure lake/lean for the target project before replaying proof-state checks"
        ),
    }.get(triage_class, "review proof-state diagnostics and select the next verifier action")


def _required_artifacts(triage_class: str) -> tuple[str, ...]:
    if triage_class == "materialize_non_placeholder_theorem":
        return (
            "non-placeholder target-prover theorem or bridge statement",
            "explicit list of discharged and remaining formal gaps",
            "updated route overlay after proof-state rerun",
        )
    if triage_class == "repair_target_prover_proof_state":
        return (
            "candidate target-prover proof patch",
            "target-prover diagnostics",
            "patch-rerun calibration manifest",
            "residual-gap validation manifest",
        )
    if triage_class == "repair_local_lean_proof_state":
        return (
            "candidate Lean proof patch",
            "local Lean diagnostics",
            "patch-rerun calibration manifest",
            "residual-gap validation manifest",
        )
    if triage_class == "materialize_target_prover_command":
        return (
            "materialized target-prover command",
            "proof-state adapter manifest",
            "route revision evidence manifest",
        )
    if triage_class == "materialize_lean_command":
        return (
            "materialized Lean command",
            "proof-state adapter manifest",
            "route revision evidence manifest",
        )
    return ("triage notes", "rerun manifest")


def _recommended_tools(
    triage_class: str,
    target_prover_families: tuple[str, ...] = (),
) -> tuple[str, ...]:
    target = _target_prover_label(target_prover_families)
    if triage_class == "materialize_non_placeholder_theorem":
        return (
            "goal-conditioned minimal formalization planner",
            "local formal-source adapter",
            "target-prover LSP/MCP adapter",
            "proof-state adapter",
        )
    if triage_class == "repair_target_prover_proof_state":
        return (
            f"{target} diagnostics",
            "target-prover LSP/MCP adapter",
            "proof-state adapter",
            "patch-rerun calibration",
        )
    if triage_class == "repair_local_lean_proof_state":
        return (
            "lean_goal",
            "lean_diagnostic_messages",
            "lean_multi_attempt",
            "patch-rerun calibration",
        )
    if triage_class == "materialize_target_prover_command":
        return ("formal-gap task export", "prover adapter contract", "proof-state adapter")
    if triage_class == "materialize_lean_command":
        return ("formal-gap task export", "prover adapter contract", "proof-state adapter")
    return ("doctor", "target-prover environment check", "proof-state adapter")


def _execution_commands(triage_class: str) -> tuple[str, ...]:
    if triage_class == "materialize_non_placeholder_theorem":
        return (
            "formalization-gap-planner-local-formal-source-adapter",
            "formalization-gap-planner-local-proof-state-adapter",
            "formalization-gap-planner-refinement-evidence",
            "formalization-gap-planner-route-revision-overlay",
        )
    if triage_class == "repair_target_prover_proof_state":
        return (
            "formalization-gap-planner-prover-adapter-contract",
            "formalization-gap-planner-local-proof-state-adapter",
            "formalization-gap-planner-refinement-evidence",
        )
    if triage_class == "repair_local_lean_proof_state":
        return (
            "formal-verifier-replay-repair-patch-rerun-attempts",
            "formal-verifier-replay-repair-patch-rerun-calibration",
            "formal-verifier-replay-repair-patch-rerun-residual-response-validation",
        )
    if triage_class == "materialize_target_prover_command":
        return (
            "formal-gap-task-export",
            "formalization-gap-planner-prover-adapter-contract",
            "formalization-gap-planner-local-proof-state-adapter",
        )
    if triage_class == "materialize_lean_command":
        return (
            "formal-gap-task-export",
            "formalization-gap-planner-prover-adapter-contract",
            "formalization-gap-planner-local-proof-state-adapter",
        )
    return ("doctor",)


def _target_prover_label(target_prover_families: tuple[str, ...]) -> str:
    if not target_prover_families:
        return "target prover"
    if len(target_prover_families) == 1:
        return target_prover_families[0]
    return "target provers " + ", ".join(target_prover_families)


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


def _schema_property_errors(
    field_name: str,
    value: object,
    schema: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
            return errors
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{field_name} must be non-empty")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            errors.append(f"{field_name} must match {pattern}")
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            errors.append(f"{field_name} must be one of {enum}")
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
            return errors
        const = schema.get("const")
        if const is not None and value != const:
            errors.append(f"{field_name} must equal {const}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
            return errors
        item_schema = schema.get("items", {})
        if isinstance(item_schema, dict) and item_schema.get("type") == "string":
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(f"{field_name}[{index}] must be string")
    return errors


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
        f"- Target prover failed items: {payload.get('n_target_prover_failed_items')}",
        f"- Non-target-prover skeleton items: {payload.get('n_non_target_prover_skeleton_items')}",
        f"- Local Lean failed items: {payload.get('n_local_lean_failed_items')}",
        f"- Non-Lean skeleton items: {payload.get('n_non_lean_skeleton_items')}",
        f"- Prover triage classes: {payload.get('by_prover_triage_class')}",
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
            f"{row.get('prover_triage_class')} score={row.get('priority_score')} "
            f"owner={row.get('owner_agent')}"
        )
        lines.append(f"  next: {row.get('recommended_next_action')}")
    return "\n".join(lines) + "\n"

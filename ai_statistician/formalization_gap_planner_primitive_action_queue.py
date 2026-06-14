from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    PROOF_EVIDENCE_BOUNDARY as PLANNER_PROOF_EVIDENCE_BOUNDARY,
)
from .formalization_gap_planner_library_coverage_map import (
    BRIDGE_NEEDED,
    COVERAGE_BUCKETS,
    DEFINITION_OR_THEORY_MISSING,
    EXACT_EXISTS,
    LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID,
    NEAR_EXISTS,
    SOURCE_PORT_NEEDED,
    UNKNOWN_OR_UNALIGNED,
    WRAPPER_NEEDED,
    validate_library_coverage_map_row,
)
from .formalization_gap_planner_target_summary import target_prover_family_summary


FORMALIZATION_GAP_PLANNER_PRIMITIVE_ACTION_QUEUE_SCHEMA_VERSION = 1
PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-primitive-action-queue-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_PRIMITIVE_ACTION_QUEUE_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner primitive-action queue rows translate "
    "library-coverage classifications into executable work orders for target "
    "prover replay, composition, wrappers, bridge lemmas, source ports, and "
    "new theory fragments. They are planner work orders, not theorem proof "
    "evidence."
)
QUEUE_ACTION_KINDS = (
    "target_prover_replay",
    "compose_existing_declarations",
    "write_wrapper",
    "prove_bridge_lemma",
    "source_port",
    "design_new_theory_fragment",
    "rerun_library_alignment",
    "route_revision",
)
OWNER_AGENTS = (
    "target_prover_adapter",
    "formalization_planner",
    "formal_verifier",
    "literature_router",
    "tooling_engineer",
)


@dataclass(frozen=True)
class FormalizationGapPlannerPrimitiveActionQueueRow:
    schema_version: int
    primitive_action_id: str
    coverage_map_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    target_prover_family: str
    library_snapshot_ref: str
    primitive: str
    coverage_bucket: str
    action_class: str
    queue_action_kind: str
    owner_agent: str
    priority_score: int
    rank: int
    candidate_declarations: tuple[str, ...]
    candidate_declaration_rows: tuple[dict[str, object], ...]
    source_refs: tuple[str, ...]
    expected_premises: tuple[str, ...]
    bridge_candidate_obligations: tuple[str, ...]
    actionable_work_items: tuple[str, ...]
    required_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    recommended_tools: tuple[str, ...]
    acceptance_gate: str
    execution_commands: tuple[str, ...]
    next_action: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_primitive_action_queue(
    formalization_gap_planner_library_coverage_map_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export target-facing primitive work orders from coverage-map rows."""

    errors: list[str] = []
    coverage_map_dir = formalization_gap_planner_library_coverage_map_dir
    manifest_path = (
        coverage_map_dir
        / "formalization_gap_planner_library_coverage_map_manifest.json"
    )
    manifest = _read_json(manifest_path, errors)
    if manifest.get("component_name") != "formalization_gap_planner_library_coverage_map":
        errors.append("input manifest is not the library coverage map component")
    if manifest.get("library_coverage_map_row_schema", {}).get(
        "$id"
    ) != LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID:
        errors.append("input manifest library coverage-map row schema id mismatch")

    coverage_rows = [
        row for row in manifest.get("rows", []) if isinstance(row, dict)
    ]
    raw_rows = [_action_row(row) for row in coverage_rows]
    rows = _rank_rows(raw_rows)
    row_dicts = [asdict(row) for row in rows]
    row_schema = primitive_action_queue_row_json_schema()
    row_schema_errors = [
        validate_primitive_action_queue_row(row, row_schema) for row in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_row_schema_invalid = len(row_schema_errors) - n_row_schema_valid
    by_action_kind = Counter(row.queue_action_kind for row in rows)
    by_owner = Counter(row.owner_agent for row in rows)
    by_bucket = Counter(row.coverage_bucket for row in rows)
    target_summary = target_prover_family_summary(
        rows,
        fallback_target_prover_family=manifest.get("target_prover_family", ""),
    )
    payload: dict[str, object] = {
        "schema_version": (
            FORMALIZATION_GAP_PLANNER_PRIMITIVE_ACTION_QUEUE_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_primitive_action_queue",
        "source_component": str(manifest.get("component_name", "")),
        "coverage_map_dir": str(coverage_map_dir),
        "coverage_map_manifest": str(manifest_path),
        "target_prover_family": target_summary["target_prover_family"],
        "n_target_prover_families": target_summary["n_target_prover_families"],
        "by_target_prover_family": target_summary["by_target_prover_family"],
        "library_snapshot_ref": str(manifest.get("library_snapshot_ref", "")),
        "n_coverage_rows": len(coverage_rows),
        "n_action_items": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_failed": sum(1 for row in rows if not row.ok),
        "n_target_prover_replay": by_action_kind.get("target_prover_replay", 0),
        "n_compose_existing_declarations": by_action_kind.get(
            "compose_existing_declarations",
            0,
        ),
        "n_write_wrapper": by_action_kind.get("write_wrapper", 0),
        "n_prove_bridge_lemma": by_action_kind.get("prove_bridge_lemma", 0),
        "n_source_port": by_action_kind.get("source_port", 0),
        "n_design_new_theory_fragment": by_action_kind.get(
            "design_new_theory_fragment",
            0,
        ),
        "n_rerun_library_alignment": by_action_kind.get(
            "rerun_library_alignment",
            0,
        ),
        "n_with_candidate_declarations": sum(
            1 for row in rows if row.candidate_declarations
        ),
        "n_with_candidate_declaration_rows": sum(
            1 for row in rows if row.candidate_declaration_rows
        ),
        "n_candidate_declaration_rows": sum(
            len(row.candidate_declaration_rows) for row in rows
        ),
        "n_with_source_refs": sum(1 for row in rows if row.source_refs),
        "n_with_bridge_obligations": sum(
            1 for row in rows if row.bridge_candidate_obligations
        ),
        "n_with_actionable_work_items": sum(
            1 for row in rows if row.actionable_work_items
        ),
        "n_actionable_work_items": sum(len(row.actionable_work_items) for row in rows),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": n_row_schema_invalid,
        "primitive_action_queue_row_schema": row_schema,
        "by_action_kind": dict(sorted(by_action_kind.items())),
        "by_owner_agent": dict(sorted(by_owner.items())),
        "by_coverage_bucket": dict(sorted(by_bucket.items())),
        "rows": row_dicts,
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and n_row_schema_invalid == 0
        ),
        "errors": errors,
        "primitive_action_queue_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "planner_proof_evidence_boundary": PLANNER_PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "primitive action rows are work orders, not theorem proof evidence",
            "acceptance gates still require target-prover replay or source-backed route revision",
            "priority scores are deterministic planner heuristics, not proof difficulty estimates",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formalization_gap_planner_primitive_action_queue_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_primitive_action_queue.jsonl"
        ).write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in row_dicts)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_primitive_action_queue_row.schema.json"
        ).write_text(json.dumps(row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_primitive_action_queue.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def primitive_action_queue_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    candidate_declaration_row_schema: dict[str, object] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "declaration",
            "target_prover_family",
            "source_field",
        ],
        "properties": {
            "declaration": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "source_field": {"type": "string", "minLength": 1},
        },
    }
    required = [
        "schema_version",
        "primitive_action_id",
        "coverage_map_id",
        "goal_plan_id",
        "route_id",
        "display_name",
        "target_prover_family",
        "library_snapshot_ref",
        "primitive",
        "coverage_bucket",
        "action_class",
        "queue_action_kind",
        "owner_agent",
        "priority_score",
        "rank",
        "candidate_declarations",
        "candidate_declaration_rows",
        "source_refs",
        "expected_premises",
        "bridge_candidate_obligations",
        "actionable_work_items",
        "required_inputs",
        "expected_outputs",
        "recommended_tools",
        "acceptance_gate",
        "execution_commands",
        "next_action",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
        "errors",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID,
        "title": "Formalization gap planner primitive-action queue row",
        "description": (
            "Per-primitive executable work order derived from a library-coverage "
            "classification. Rows are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": (
                    FORMALIZATION_GAP_PLANNER_PRIMITIVE_ACTION_QUEUE_SCHEMA_VERSION
                ),
            },
            "primitive_action_id": {"type": "string", "minLength": 1},
            "coverage_map_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "primitive": {"type": "string", "minLength": 1},
            "coverage_bucket": {"type": "string", "enum": list(COVERAGE_BUCKETS)},
            "action_class": {"type": "string"},
            "queue_action_kind": {"type": "string", "enum": list(QUEUE_ACTION_KINDS)},
            "owner_agent": {"type": "string", "enum": list(OWNER_AGENTS)},
            "priority_score": {"type": "integer"},
            "rank": {"type": "integer"},
            "candidate_declarations": string_array,
            "candidate_declaration_rows": {
                "type": "array",
                "items": candidate_declaration_row_schema,
            },
            "source_refs": string_array,
            "expected_premises": string_array,
            "bridge_candidate_obligations": string_array,
            "actionable_work_items": string_array,
            "required_inputs": string_array,
            "expected_outputs": string_array,
            "recommended_tools": string_array,
            "acceptance_gate": {"type": "string", "minLength": 1},
            "execution_commands": string_array,
            "next_action": {"type": "string", "minLength": 1},
            "proof_evidence_status": {"type": "string", "const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_primitive_action_queue_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    if not isinstance(row, dict):
        return ["primitive action queue row must be an object"]
    row_schema = schema or primitive_action_queue_row_json_schema()
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
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    allowed = set(required)
    for field_name in row:
        if field_name not in allowed:
            errors.append(f"{field_name} unexpected")
    priority = row.get("priority_score")
    if isinstance(priority, int) and not isinstance(priority, bool):
        if priority < 0 or priority > 100:
            errors.append("priority_score must be between 0 and 100")
    rank = row.get("rank")
    if isinstance(rank, int) and not isinstance(rank, bool) and rank < 1:
        errors.append("rank must be positive")
    row_target = _target_prover_key(row.get("target_prover_family", ""))
    for index, declaration_row in enumerate(
        row.get("candidate_declaration_rows", []) or []
    ):
        if not isinstance(declaration_row, dict):
            continue
        declaration_target = _target_prover_key(
            declaration_row.get("target_prover_family", "")
        )
        if row_target and declaration_target and declaration_target != row_target:
            errors.append(
                "candidate_declaration_rows"
                f"[{index}].target_prover_family must match row target_prover_family"
            )
    if "not theorem proof evidence" not in str(
        row.get("proof_evidence_boundary", "")
    ).lower():
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    return errors


def _action_row(
    coverage_row: dict[str, Any],
) -> FormalizationGapPlannerPrimitiveActionQueueRow:
    coverage_errors = validate_library_coverage_map_row(coverage_row)
    coverage_bucket = str(coverage_row.get("coverage_bucket", UNKNOWN_OR_UNALIGNED))
    action_kind, owner, priority = _action_mapping(coverage_bucket)
    primitive = str(coverage_row.get("primitive", ""))
    row_errors = list(coverage_errors)
    if not primitive:
        row_errors.append("primitive missing")
    if coverage_bucket not in COVERAGE_BUCKETS:
        row_errors.append("coverage bucket unsupported")
    if coverage_bucket == UNKNOWN_OR_UNALIGNED and not row_errors:
        row_errors.append("coverage bucket unknown or unaligned")
    return FormalizationGapPlannerPrimitiveActionQueueRow(
        schema_version=FORMALIZATION_GAP_PLANNER_PRIMITIVE_ACTION_QUEUE_SCHEMA_VERSION,
        primitive_action_id="formalization_gap_planner_primitive_action:"
        + stable_hash(
            [
                coverage_row.get("coverage_map_id", ""),
                primitive,
                coverage_bucket,
                action_kind,
            ]
        )[:16],
        coverage_map_id=str(coverage_row.get("coverage_map_id", "")),
        goal_plan_id=str(coverage_row.get("goal_plan_id", "")),
        route_id=str(coverage_row.get("route_id", "")),
        display_name=str(coverage_row.get("display_name", "")),
        target_prover_family=str(coverage_row.get("target_prover_family", "")),
        library_snapshot_ref=str(coverage_row.get("library_snapshot_ref", "")),
        primitive=primitive,
        coverage_bucket=coverage_bucket,
        action_class=str(coverage_row.get("action_class", "")),
        queue_action_kind=action_kind,
        owner_agent=owner,
        priority_score=priority,
        rank=0,
        candidate_declarations=_str_tuple(
            coverage_row.get("candidate_declarations", [])
        ),
        candidate_declaration_rows=_candidate_declaration_rows(coverage_row),
        source_refs=_str_tuple(coverage_row.get("source_refs", [])),
        expected_premises=_str_tuple(coverage_row.get("expected_premises", [])),
        bridge_candidate_obligations=_str_tuple(
            coverage_row.get("bridge_candidate_obligations", [])
        ),
        actionable_work_items=_str_tuple(coverage_row.get("actionable_work_items", [])),
        required_inputs=_required_inputs(coverage_bucket),
        expected_outputs=_expected_outputs(coverage_bucket),
        recommended_tools=_recommended_tools(coverage_bucket),
        acceptance_gate=_acceptance_gate(coverage_bucket),
        execution_commands=_execution_commands(coverage_bucket),
        next_action=_next_action(coverage_row, coverage_bucket, primitive),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=bool(coverage_row.get("ok", False)) and not row_errors,
        errors=tuple(row_errors),
    )


def _rank_rows(
    rows: list[FormalizationGapPlannerPrimitiveActionQueueRow],
) -> tuple[FormalizationGapPlannerPrimitiveActionQueueRow, ...]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -row.priority_score,
            row.route_id,
            row.primitive,
            row.primitive_action_id,
        ),
    )
    return tuple(replace(row, rank=index + 1) for index, row in enumerate(ranked))


def _action_mapping(coverage_bucket: str) -> tuple[str, str, int]:
    if coverage_bucket == EXACT_EXISTS:
        return ("target_prover_replay", "target_prover_adapter", 90)
    if coverage_bucket == NEAR_EXISTS:
        return ("compose_existing_declarations", "formal_verifier", 80)
    if coverage_bucket == WRAPPER_NEEDED:
        return ("write_wrapper", "formalization_planner", 75)
    if coverage_bucket == BRIDGE_NEEDED:
        return ("prove_bridge_lemma", "formal_verifier", 70)
    if coverage_bucket == SOURCE_PORT_NEEDED:
        return ("source_port", "literature_router", 65)
    if coverage_bucket == DEFINITION_OR_THEORY_MISSING:
        return ("design_new_theory_fragment", "formalization_planner", 50)
    return ("rerun_library_alignment", "tooling_engineer", 95)


def _required_inputs(coverage_bucket: str) -> tuple[str, ...]:
    base = (
        "coverage map row",
        "portable route alignment edge",
        "target theorem or work packet",
    )
    if coverage_bucket == EXACT_EXISTS:
        return (*base, "candidate declaration list", "target prover library snapshot")
    if coverage_bucket == NEAR_EXISTS:
        return (*base, "nearby declaration list", "expected premises")
    if coverage_bucket == WRAPPER_NEEDED:
        return (*base, "candidate declaration list", "wrapper statement sketch")
    if coverage_bucket == BRIDGE_NEEDED:
        return (*base, "bridge candidate obligations", "expected premises")
    if coverage_bucket == SOURCE_PORT_NEEDED:
        return (*base, "source references", "source-backed informal statement")
    if coverage_bucket == DEFINITION_OR_THEORY_MISSING:
        return (*base, "minimal new definition sketch", "dependency boundary")
    return (*base, "fresh formal-library search results", "route alignment evidence")


def _expected_outputs(coverage_bucket: str) -> tuple[str, ...]:
    if coverage_bucket == EXACT_EXISTS:
        return (
            "target prover replay transcript",
            "accepted candidate declaration mapping or residual goal report",
        )
    if coverage_bucket == NEAR_EXISTS:
        return (
            "composed proof sketch over existing declarations",
            "proof-state residual report",
        )
    if coverage_bucket == WRAPPER_NEEDED:
        return (
            "minimal wrapper declaration",
            "wrapper replay or residual side-condition report",
        )
    if coverage_bucket == BRIDGE_NEEDED:
        return (
            "bridge lemma statement",
            "bridge proof attempt transcript",
            "residual obligations for route revision",
        )
    if coverage_bucket == SOURCE_PORT_NEEDED:
        return (
            "source-backed formal statement candidate",
            "ported lemma candidate or literature gap report",
        )
    if coverage_bucket == DEFINITION_OR_THEORY_MISSING:
        return (
            "minimal new theory fragment plan",
            "new definitions and dependency-risk estimate",
        )
    return (
        "refined library search evidence",
        "updated informal-to-formal alignment classification",
    )


def _recommended_tools(coverage_bucket: str) -> tuple[str, ...]:
    if coverage_bucket == EXACT_EXISTS:
        return ("target prover adapter", "prover or LSP replay")
    if coverage_bucket == NEAR_EXISTS:
        return ("formal source search", "target prover adapter", "proof-state adapter")
    if coverage_bucket == WRAPPER_NEEDED:
        return ("formalization planner", "target prover adapter", "proof-state adapter")
    if coverage_bucket == BRIDGE_NEEDED:
        return ("formal verifier", "formal source search", "proof-state adapter")
    if coverage_bucket == SOURCE_PORT_NEEDED:
        return ("literature search adapter", "paper corpus", "formal source search")
    if coverage_bucket == DEFINITION_OR_THEORY_MISSING:
        return ("formalization planner", "minimal delta audit", "source grounding audit")
    return ("formal source search", "route alignment audit", "interactive session")


def _acceptance_gate(coverage_bucket: str) -> str:
    if coverage_bucket == EXACT_EXISTS:
        return "target prover kernel or certified checker verifies translated statement"
    if coverage_bucket == NEAR_EXISTS:
        return "proof-state replay leaves no residual goals or records bounded residuals"
    if coverage_bucket == WRAPPER_NEEDED:
        return "wrapper compiles and target prover replay confirms it preserves the target statement"
    if coverage_bucket == BRIDGE_NEEDED:
        return "bridge lemma is accepted by the target prover or residual obligations are routed back"
    if coverage_bucket == SOURCE_PORT_NEEDED:
        return "source-backed statement is aligned to a formal candidate with cited evidence"
    if coverage_bucket == DEFINITION_OR_THEORY_MISSING:
        return "new theory fragment passes minimal-delta audit before proof attempt expansion"
    return "library search and route alignment rerun produce a non-unknown coverage bucket"


def _execution_commands(coverage_bucket: str) -> tuple[str, ...]:
    if coverage_bucket == EXACT_EXISTS:
        return (
            "python3 -m ai_statistician.cli formalization-gap-planner-prover-adapter-contract "
            "--goal-conditioned-minimal-formalization-plan-dir <plan_dir> "
            "--target-prover-family <target> "
            "--library-snapshot-ref <snapshot> "
            "--out <work_dir>/formalization_gap_planner_prover_adapter_contract",
        )
    if coverage_bucket in {NEAR_EXISTS, WRAPPER_NEEDED, BRIDGE_NEEDED}:
        return (
            "python3 -m ai_statistician.cli formalization-gap-planner-refinement-queue "
            "--goal-conditioned-minimal-formalization-plan-dir <plan_dir> "
            "--out <work_dir>/formalization_gap_planner_refinement_queue",
            "python3 -m ai_statistician.cli formalization-gap-planner-local-proof-state-adapter "
            "--formalization-gap-planner-refinement-queue-dir "
            "<work_dir>/formalization_gap_planner_refinement_queue "
            "--out <work_dir>/formalization_gap_planner_local_proof_state_adapter",
        )
    if coverage_bucket == SOURCE_PORT_NEEDED:
        return (
            "python3 -m ai_statistician.cli formalization-gap-planner-local-literature-adapter "
            "--formalization-gap-planner-refinement-queue-dir "
            "<work_dir>/formalization_gap_planner_refinement_queue "
            "--literature-root <local-paper-or-text-corpus-root> "
            "--out <work_dir>/formalization_gap_planner_local_literature_adapter",
        )
    if coverage_bucket == DEFINITION_OR_THEORY_MISSING:
        return (
            "python3 -m ai_statistician.cli formalization-gap-planner-minimal-delta-audit "
            "--goal-conditioned-minimal-formalization-plan-dir <plan_dir> "
            "--out <work_dir>/formalization_gap_planner_minimal_delta_audit",
        )
    return (
        "python3 -m ai_statistician.cli formalization-gap-planner-library-coverage-map "
        "--goal-conditioned-minimal-formalization-plan-dir <plan_dir> "
        "--out <work_dir>/formalization_gap_planner_library_coverage_map",
    )


def _next_action(
    coverage_row: dict[str, Any],
    coverage_bucket: str,
    primitive: str,
) -> str:
    existing = str(coverage_row.get("next_action", "")).strip()
    if existing:
        return existing
    action_kind, _, _ = _action_mapping(coverage_bucket)
    return f"{action_kind.replace('_', ' ')} for {primitive}"


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(str(value) for value in values if str(value))


def _candidate_declaration_rows(
    coverage_row: dict[str, object],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    target_prover_family = str(coverage_row.get("target_prover_family", "")).strip()
    has_structured_rows = "candidate_declaration_rows" in coverage_row
    for item in _dict_tuple(coverage_row.get("candidate_declaration_rows", [])):
        declaration = str(
            item.get("declaration")
            or item.get("declaration_name")
            or item.get("lean_declaration")
            or ""
        ).strip()
        if not declaration:
            continue
        rows.append(
            {
                "declaration": declaration,
                "target_prover_family": str(
                    item.get("target_prover_family", "")
                    or item.get("target_prover", "")
                    or target_prover_family
                ).strip(),
                "source_field": str(
                    item.get("source_field", "") or "candidate_declaration_rows"
                ).strip(),
            }
        )
    if not has_structured_rows:
        rows.extend(
            {
                "declaration": declaration,
                "target_prover_family": target_prover_family,
                "source_field": "candidate_declarations",
            }
            for declaration in _str_tuple(coverage_row.get("candidate_declarations", []))
        )
    compact: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        declaration = str(row.get("declaration", "")).strip()
        if not declaration:
            continue
        row_target = str(row.get("target_prover_family", "")).strip()
        key = (_formal_declaration_key(declaration), _target_prover_key(row_target))
        if key in seen:
            continue
        seen.add(key)
        compact.append(
            {
                "declaration": declaration,
                "target_prover_family": row_target,
                "source_field": str(row.get("source_field", "")).strip()
                or "candidate_declarations",
            }
        )
    return tuple(compact)


def _dict_tuple(values: Any) -> tuple[dict[str, object], ...]:
    if isinstance(values, dict):
        return (values,)
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(value for value in values if isinstance(value, dict))


def _formal_declaration_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).lower()


def _target_prover_key(value: object) -> str:
    key = str(value).strip().lower().replace("-", "_")
    aliases = {
        "coq": "rocq",
        "coq8": "rocq",
        "lean": "lean4",
        "lean_4": "lean4",
        "isabelle_hol": "isabelle",
    }
    return aliases.get(key, key)


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
        elif isinstance(item_schema, dict) and item_schema.get("type") == "object":
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    errors.append(f"{field_name}[{index}] must be object")
                    continue
                required = tuple(item_schema.get("required", ()))
                properties = item_schema.get("properties", {})
                allowed = set(required)
                for required_field in required:
                    if required_field not in item:
                        errors.append(
                            f"{field_name}[{index}].{required_field} required"
                        )
                if isinstance(properties, dict):
                    allowed = set(properties)
                    for child_name, child_schema in properties.items():
                        if child_name in item and isinstance(child_schema, dict):
                            errors.extend(
                                _schema_property_errors(
                                    f"{field_name}[{index}].{child_name}",
                                    item[child_name],
                                    child_schema,
                                )
                            )
                if item_schema.get("additionalProperties") is False:
                    for child_name in item:
                        if child_name not in allowed:
                            errors.append(
                                f"{field_name}[{index}].{child_name} unexpected"
                            )
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
        "# Formalization Gap Planner Primitive Action Queue",
        "",
        f"- Action items: {payload.get('n_ok')}/{payload.get('n_action_items')}",
        f"- Target prover family: {payload.get('target_prover_family')}",
        f"- Target prover families: {payload.get('n_target_prover_families')}",
        f"- Target prover replay: {payload.get('n_target_prover_replay')}",
        f"- Compose existing declarations: {payload.get('n_compose_existing_declarations')}",
        f"- Write wrapper: {payload.get('n_write_wrapper')}",
        f"- Prove bridge lemma: {payload.get('n_prove_bridge_lemma')}",
        f"- Source port: {payload.get('n_source_port')}",
        f"- Design new theory fragment: {payload.get('n_design_new_theory_fragment')}",
        f"- Rerun library alignment: {payload.get('n_rerun_library_alignment')}",
        f"- Rows with actionable work items: {payload.get('n_with_actionable_work_items')}",
        (
            f"- Row schema valid: {payload.get('n_row_schema_valid')}/"
            f"{payload.get('n_action_items')}"
        ),
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Action Kinds",
        "",
    ]
    for action_kind, count in sorted((payload.get("by_action_kind", {}) or {}).items()):
        lines.append(f"- `{action_kind}`: {count}")
    return "\n".join(lines) + "\n"

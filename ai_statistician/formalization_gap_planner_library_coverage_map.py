from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY as PLANNER_PROOF_EVIDENCE_BOUNDARY,
)


FORMALIZATION_GAP_PLANNER_LIBRARY_COVERAGE_MAP_SCHEMA_VERSION = 1
LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-library-coverage-map-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_LIBRARY_COVERAGE_MAP_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner library-coverage map rows align informal route "
    "primitives to current-library realization candidates and classify whether "
    "the route needs exact reuse, composition, wrappers, bridge lemmas, source "
    "ports, or new theory. They are planning and mapping evidence, not theorem "
    "proof evidence."
)
EXACT_EXISTS = "exact_exists"
NEAR_EXISTS = "near_exists"
WRAPPER_NEEDED = "wrapper_needed"
BRIDGE_NEEDED = "bridge_needed"
SOURCE_PORT_NEEDED = "source_port_needed"
DEFINITION_OR_THEORY_MISSING = "definition_or_theory_missing"
UNKNOWN_OR_UNALIGNED = "unknown_or_unaligned"
COVERAGE_BUCKETS = (
    EXACT_EXISTS,
    NEAR_EXISTS,
    WRAPPER_NEEDED,
    BRIDGE_NEEDED,
    SOURCE_PORT_NEEDED,
    DEFINITION_OR_THEORY_MISSING,
    UNKNOWN_OR_UNALIGNED,
)


@dataclass(frozen=True)
class FormalizationGapPlannerLibraryCoverageMapRow:
    schema_version: int
    coverage_map_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    target_prover_family: str
    library_snapshot_ref: str
    primitive: str
    coverage_bucket: str
    action_class: str
    informal_node_id: str
    realization_node_id: str
    realization_node_kind: str
    alignment_status: str
    candidate_declarations: tuple[str, ...]
    candidate_declaration_rows: tuple[dict[str, object], ...]
    declaration_sources: tuple[str, ...]
    expected_premises: tuple[str, ...]
    bridge_candidate_obligations: tuple[str, ...]
    source_refs: tuple[str, ...]
    route_alignment_edge: dict[str, object]
    needs_wrapper: bool
    needs_bridge_lemma: bool
    needs_source_search: bool
    needs_new_definition_or_theory: bool
    needs_prover_feedback: bool
    reusable_without_new_declaration: bool
    next_action: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_library_coverage_map(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export a per-primitive coverage map from a portable gap plan."""

    errors: list[str] = []
    plan_dir = goal_conditioned_minimal_formalization_plan_dir
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = _read_json(manifest_path, errors)
    if manifest.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("input manifest is not the library-aware formalization gap planner")
    if manifest.get("portable_schema_id") != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("input manifest portable schema id mismatch")

    plan_rows = [row for row in manifest.get("rows", []) if isinstance(row, dict)]
    rows = [
        _coverage_row(
            plan_row,
            primitive,
            target_prover_family=str(manifest.get("target_prover_family", "")),
            library_snapshot_ref=str(manifest.get("library_snapshot_ref", "")),
        )
        for plan_row in plan_rows
        for primitive in _selected_primitives(plan_row)
    ]
    row_dicts = [asdict(row) for row in rows]
    row_schema = library_coverage_map_row_json_schema()
    row_schema_errors = [
        validate_library_coverage_map_row(row, row_schema) for row in row_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_row_schema_invalid = len(row_schema_errors) - n_row_schema_valid
    by_bucket = Counter(row.coverage_bucket for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_LIBRARY_COVERAGE_MAP_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_library_coverage_map",
        "audited_component": str(manifest.get("component_name", "")),
        "portable_schema_id": str(manifest.get("portable_schema_id", "")),
        "goal_conditioned_minimal_formalization_plan_dir": str(plan_dir),
        "goal_conditioned_minimal_formalization_plan_manifest": str(manifest_path),
        "target_prover_family": str(manifest.get("target_prover_family", "")),
        "library_snapshot_ref": str(manifest.get("library_snapshot_ref", "")),
        "n_plan_rows": len(plan_rows),
        "n_coverage_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_failed": sum(1 for row in rows if not row.ok),
        "n_exact_exists": by_bucket.get(EXACT_EXISTS, 0),
        "n_near_exists": by_bucket.get(NEAR_EXISTS, 0),
        "n_wrapper_needed": by_bucket.get(WRAPPER_NEEDED, 0),
        "n_bridge_needed": by_bucket.get(BRIDGE_NEEDED, 0),
        "n_source_port_needed": by_bucket.get(SOURCE_PORT_NEEDED, 0),
        "n_definition_or_theory_missing": by_bucket.get(
            DEFINITION_OR_THEORY_MISSING,
            0,
        ),
        "n_unknown_or_unaligned": by_bucket.get(UNKNOWN_OR_UNALIGNED, 0),
        "n_reusable_without_new_declaration": sum(
            1 for row in rows if row.reusable_without_new_declaration
        ),
        "n_needs_prover_feedback": sum(1 for row in rows if row.needs_prover_feedback),
        "n_needs_source_search": sum(1 for row in rows if row.needs_source_search),
        "n_needs_new_definition_or_theory": sum(
            1 for row in rows if row.needs_new_definition_or_theory
        ),
        "n_rows_with_candidate_declarations": sum(
            1 for row in rows if row.candidate_declarations
        ),
        "n_rows_with_candidate_declaration_rows": sum(
            1 for row in rows if row.candidate_declaration_rows
        ),
        "n_candidate_declaration_rows": sum(
            len(row.candidate_declaration_rows) for row in rows
        ),
        "n_rows_with_alignment": sum(
            1 for row in rows if row.realization_node_id and row.informal_node_id
        ),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": n_row_schema_invalid,
        "library_coverage_map_row_schema": row_schema,
        "by_coverage_bucket": dict(sorted(by_bucket.items())),
        "rows": row_dicts,
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and n_row_schema_invalid == 0
        ),
        "errors": errors,
        "library_coverage_map_fingerprint": stable_hash(row_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "planner_proof_evidence_boundary": PLANNER_PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "coverage buckets are planner classifications until target-prover replay confirms them",
            "candidate declarations may be stale if the library snapshot changes",
            "unknown or unaligned rows should trigger focused library search or route revision",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_library_coverage_map_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_library_coverage_map.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in row_dicts)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_library_coverage_map_row.schema.json"
        ).write_text(json.dumps(row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_library_coverage_map.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def library_coverage_map_row_json_schema() -> dict[str, object]:
    required = [
        "schema_version",
        "coverage_map_id",
        "goal_plan_id",
        "route_id",
        "display_name",
        "target_prover_family",
        "library_snapshot_ref",
        "primitive",
        "coverage_bucket",
        "action_class",
        "informal_node_id",
        "realization_node_id",
        "realization_node_kind",
        "alignment_status",
        "candidate_declarations",
        "candidate_declaration_rows",
        "declaration_sources",
        "expected_premises",
        "bridge_candidate_obligations",
        "source_refs",
        "route_alignment_edge",
        "needs_wrapper",
        "needs_bridge_lemma",
        "needs_source_search",
        "needs_new_definition_or_theory",
        "needs_prover_feedback",
        "reusable_without_new_declaration",
        "next_action",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "ok",
        "errors",
    ]
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
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID,
        "title": "Formalization gap planner library-coverage map row",
        "description": (
            "Per-primitive mapping from an informal route atom to the current "
            "formal-library realization candidate selected by the planner."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_LIBRARY_COVERAGE_MAP_SCHEMA_VERSION,
            },
            "coverage_map_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "primitive": {"type": "string", "minLength": 1},
            "coverage_bucket": {"type": "string", "enum": list(COVERAGE_BUCKETS)},
            "action_class": {"type": "string"},
            "informal_node_id": {"type": "string"},
            "realization_node_id": {"type": "string"},
            "realization_node_kind": {"type": "string"},
            "alignment_status": {"type": "string"},
            "candidate_declarations": string_array,
            "candidate_declaration_rows": {
                "type": "array",
                "items": candidate_declaration_row_schema,
            },
            "declaration_sources": string_array,
            "expected_premises": string_array,
            "bridge_candidate_obligations": string_array,
            "source_refs": string_array,
            "route_alignment_edge": {"type": "object"},
            "needs_wrapper": {"type": "boolean"},
            "needs_bridge_lemma": {"type": "boolean"},
            "needs_source_search": {"type": "boolean"},
            "needs_new_definition_or_theory": {"type": "boolean"},
            "needs_prover_feedback": {"type": "boolean"},
            "reusable_without_new_declaration": {"type": "boolean"},
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


def validate_library_coverage_map_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    if not isinstance(row, dict):
        return ["library coverage map row must be an object"]
    row_schema = schema or library_coverage_map_row_json_schema()
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
    if (
        row.get("coverage_bucket") != UNKNOWN_OR_UNALIGNED
        and not str(row.get("realization_node_id", ""))
    ):
        errors.append("realization_node_id required unless coverage is unknown")
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


def _coverage_row(
    plan_row: dict[str, Any],
    primitive: str,
    *,
    target_prover_family: str,
    library_snapshot_ref: str,
) -> FormalizationGapPlannerLibraryCoverageMapRow:
    alignment_edge = _alignment_edge(plan_row, primitive)
    action_class = str(alignment_edge.get("action_class", ""))
    realization_node = _realization_node(plan_row, str(alignment_edge.get("target", "")))
    node = _primitive_node(plan_row, primitive)
    if not action_class:
        action_class = str(node.get("action_class", ""))
    coverage_bucket = _coverage_bucket(action_class, alignment_edge, realization_node)
    row_target_prover_family = target_prover_family or str(
        plan_row.get("target_prover_family", "")
    )
    row_library_snapshot_ref = library_snapshot_ref or str(
        plan_row.get("library_snapshot_ref", "")
    )
    candidate_declarations = _candidate_declarations(node, realization_node)
    candidate_declaration_rows = _candidate_declaration_rows(
        node,
        realization_node,
        target_prover_family=row_target_prover_family,
    )
    declaration_sources = _str_tuple(realization_node.get("declaration_sources", []))
    expected_premises = _str_tuple(node.get("expected_premises", []))
    bridge_candidates = _str_tuple(node.get("bridge_candidate_obligations", []))
    source_refs = _str_tuple(node.get("source_refs", []))
    errors: list[str] = []
    if not primitive:
        errors.append("primitive missing")
    if not alignment_edge:
        errors.append("route alignment edge missing")
    if coverage_bucket == UNKNOWN_OR_UNALIGNED:
        errors.append("coverage bucket unknown or unaligned")
    next_action = _next_action(coverage_bucket, primitive)
    return FormalizationGapPlannerLibraryCoverageMapRow(
        schema_version=FORMALIZATION_GAP_PLANNER_LIBRARY_COVERAGE_MAP_SCHEMA_VERSION,
        coverage_map_id="formalization_gap_planner_library_coverage_map:"
        + stable_hash(
            [
                plan_row.get("goal_plan_id", ""),
                primitive,
                action_class,
                row_library_snapshot_ref,
            ]
        )[:16],
        goal_plan_id=str(plan_row.get("goal_plan_id", "")),
        route_id=str(plan_row.get("route_id", "")),
        display_name=str(plan_row.get("display_name", "")),
        target_prover_family=row_target_prover_family,
        library_snapshot_ref=row_library_snapshot_ref,
        primitive=primitive,
        coverage_bucket=coverage_bucket,
        action_class=action_class,
        informal_node_id=str(alignment_edge.get("source", "")),
        realization_node_id=str(alignment_edge.get("target", "")),
        realization_node_kind=str(
            realization_node.get("node_type", realization_node.get("kind", ""))
        ),
        alignment_status=str(alignment_edge.get("alignment_status", "")),
        candidate_declarations=candidate_declarations,
        candidate_declaration_rows=candidate_declaration_rows,
        declaration_sources=declaration_sources,
        expected_premises=expected_premises,
        bridge_candidate_obligations=bridge_candidates,
        source_refs=source_refs,
        route_alignment_edge=dict(alignment_edge),
        needs_wrapper=coverage_bucket == WRAPPER_NEEDED,
        needs_bridge_lemma=coverage_bucket == BRIDGE_NEEDED,
        needs_source_search=coverage_bucket == SOURCE_PORT_NEEDED
        or (coverage_bucket == UNKNOWN_OR_UNALIGNED and not source_refs),
        needs_new_definition_or_theory=coverage_bucket
        == DEFINITION_OR_THEORY_MISSING,
        needs_prover_feedback=coverage_bucket
        in {EXACT_EXISTS, NEAR_EXISTS, WRAPPER_NEEDED, BRIDGE_NEEDED},
        reusable_without_new_declaration=coverage_bucket in {EXACT_EXISTS, NEAR_EXISTS},
        next_action=next_action,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _selected_primitives(plan_row: dict[str, Any]) -> tuple[str, ...]:
    return _str_tuple(plan_row.get("selected_primitives", []))


def _alignment_edge(plan_row: dict[str, Any], primitive: str) -> dict[str, object]:
    for edge in plan_row.get("route_alignment_edges", []) or []:
        if isinstance(edge, dict) and str(edge.get("primitive", "")) == primitive:
            return edge
    return {}


def _realization_node(plan_row: dict[str, Any], node_id: str) -> dict[str, object]:
    for node in plan_row.get("lean_realization_dag_nodes", []) or []:
        if isinstance(node, dict) and str(node.get("node_id", "")) == node_id:
            return node
    return {}


def _primitive_node(plan_row: dict[str, Any], primitive: str) -> dict[str, object]:
    for bucket_name in (
        "existing_reuse_nodes",
        "wrapper_nodes",
        "bridge_nodes",
        "source_discovery_nodes",
        "first_principles_nodes",
        "minimal_additional_formalization_nodes",
    ):
        for node in plan_row.get(bucket_name, []) or []:
            if isinstance(node, dict) and str(node.get("primitive", "")) == primitive:
                return node
    return {}


def _coverage_bucket(
    action_class: str,
    alignment_edge: dict[str, object],
    realization_node: dict[str, object],
) -> str:
    if not alignment_edge or not realization_node:
        return UNKNOWN_OR_UNALIGNED
    if action_class == "reuse_exact_proof_bank_obligation":
        return EXACT_EXISTS
    if action_class == "compose_existing_bridge_chain":
        return NEAR_EXISTS
    if action_class == "add_minimal_wrapper":
        return WRAPPER_NEEDED
    if action_class in {"design_bridge_lemma", "formalize_assumption_interface"}:
        return BRIDGE_NEEDED
    if action_class == "port_external_source":
        return SOURCE_PORT_NEEDED
    if action_class == "design_from_first_principles":
        return DEFINITION_OR_THEORY_MISSING
    return UNKNOWN_OR_UNALIGNED


def _candidate_declarations(
    node: dict[str, object],
    realization_node: dict[str, object],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            [
                *_str_tuple(node.get("candidate_declarations", [])),
                *_str_tuple(realization_node.get("declaration_sources", [])),
            ]
        )
    )


def _candidate_declaration_rows(
    node: dict[str, object],
    realization_node: dict[str, object],
    *,
    target_prover_family: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    _append_candidate_declaration_rows(
        rows,
        node.get("candidate_declaration_rows", []),
        inherited_target_prover_family=target_prover_family,
        fallback_source_field="candidate_declaration_rows",
    )
    _append_candidate_declaration_rows(
        rows,
        realization_node.get("candidate_declaration_rows", []),
        inherited_target_prover_family=target_prover_family,
        fallback_source_field="candidate_declaration_rows",
    )
    _append_candidate_declaration_strings(
        rows,
        node.get("candidate_declarations", []),
        target_prover_family=target_prover_family,
        source_field="candidate_declarations",
    )
    _append_candidate_declaration_strings(
        rows,
        _realization_declaration_source_candidates(node, realization_node),
        target_prover_family=str(
            realization_node.get("target_prover_family", "")
            or target_prover_family
        ),
        source_field="declaration_sources",
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


def _realization_declaration_source_candidates(
    node: dict[str, object],
    realization_node: dict[str, object],
) -> tuple[str, ...]:
    informal_dependency_keys = {
        _formal_declaration_key(item)
        for item in (
            *_str_tuple(node.get("expected_premises", [])),
            *_str_tuple(node.get("bridge_candidate_obligations", [])),
            *_str_tuple(node.get("source_refs", [])),
        )
        if _formal_declaration_key(item)
    }
    return tuple(
        item
        for item in _str_tuple(realization_node.get("declaration_sources", []))
        if _formal_declaration_key(item) not in informal_dependency_keys
    )


def _append_candidate_declaration_rows(
    rows: list[dict[str, object]],
    values: object,
    *,
    inherited_target_prover_family: str,
    fallback_source_field: str,
) -> None:
    for value in _dict_tuple(values):
        declaration = str(
            value.get("declaration")
            or value.get("declaration_name")
            or value.get("lean_declaration")
            or ""
        ).strip()
        if not declaration:
            continue
        rows.append(
            {
                "declaration": declaration,
                "target_prover_family": str(
                    value.get("target_prover_family", "")
                    or value.get("target_prover", "")
                    or inherited_target_prover_family
                ).strip(),
                "source_field": str(
                    value.get("source_field", "") or fallback_source_field
                ).strip(),
            }
        )


def _append_candidate_declaration_strings(
    rows: list[dict[str, object]],
    values: object,
    *,
    target_prover_family: str,
    source_field: str,
) -> None:
    rows.extend(
        {
            "declaration": declaration,
            "target_prover_family": target_prover_family,
            "source_field": source_field,
        }
        for declaration in _str_tuple(values)
    )


def _next_action(coverage_bucket: str, primitive: str) -> str:
    if coverage_bucket == EXACT_EXISTS:
        return f"try exact candidate declarations for {primitive} in the target prover"
    if coverage_bucket == NEAR_EXISTS:
        return f"compose nearby declarations and run proof-state feedback for {primitive}"
    if coverage_bucket == WRAPPER_NEEDED:
        return f"write the smallest wrapper statement for {primitive}"
    if coverage_bucket == BRIDGE_NEEDED:
        return f"prove a focused bridge lemma for {primitive}"
    if coverage_bucket == SOURCE_PORT_NEEDED:
        return f"resolve source-backed statement and port candidate for {primitive}"
    if coverage_bucket == DEFINITION_OR_THEORY_MISSING:
        return f"design the smallest new definition or theory fragment for {primitive}"
    return f"rerun formal-library search and route alignment for {primitive}"


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(str(value) for value in values if str(value))


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
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
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
        "# Formalization Gap Planner Library Coverage Map",
        "",
        f"- Coverage rows: {payload.get('n_ok')}/{payload.get('n_coverage_rows')}",
        f"- Exact exists: {payload.get('n_exact_exists')}",
        f"- Near exists: {payload.get('n_near_exists')}",
        f"- Wrapper needed: {payload.get('n_wrapper_needed')}",
        f"- Bridge needed: {payload.get('n_bridge_needed')}",
        f"- Source port needed: {payload.get('n_source_port_needed')}",
        f"- Definition or theory missing: {payload.get('n_definition_or_theory_missing')}",
        f"- Unknown or unaligned: {payload.get('n_unknown_or_unaligned')}",
        (
            f"- Row schema valid: {payload.get('n_row_schema_valid')}/"
            f"{payload.get('n_coverage_rows')}"
        ),
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Coverage Buckets",
        "",
    ]
    for bucket, count in sorted(
        (payload.get("by_coverage_bucket", {}) or {}).items()
    ):
        lines.append(f"- `{bucket}`: {count}")
    return "\n".join(lines) + "\n"

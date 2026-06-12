from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION,
    PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS,
    route_alignment_edge_json_schema,
    validate_route_alignment_edge,
    validate_portable_gap_plan_payload,
    write_route_alignment_edge_schema,
)


FORMALIZATION_GAP_PLANNER_PORTABLE_PLAN_AUDIT_SCHEMA_VERSION = 1
PORTABLE_PLAN_AUDIT_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-portable-plan-audit-row:1"
)
PROOF_EVIDENCE_STATUS_AUDIT = (
    "FORMALIZATION_GAP_PLANNER_PORTABLE_PLAN_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY_AUDIT = (
    "Portable formalization gap plan audit rows validate planner contracts, "
    "DAG structure, work-packet boundaries, and proof-boundary discipline. "
    "They are not theorem proof evidence."
)
FORBIDDEN_PROOF_CLAIM_KEYS = (
    "kernel_verified",
    "proof_verified",
    "theorem_proved",
    "proof_evidence",
)


@dataclass(frozen=True)
class FormalizationGapPlannerPortablePlanAuditCheck:
    schema_version: int
    check_id: str
    check_name: str
    category: str
    expected: str
    observed: str
    ok: bool
    severity: str
    proof_evidence_status: str = PROOF_EVIDENCE_STATUS_AUDIT
    proof_evidence_boundary: str = PROOF_EVIDENCE_BOUNDARY_AUDIT
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_portable_plan(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Audit a portable gap-plan manifest before evaluation or prover mapping."""

    errors: list[str] = []
    plan_dir = goal_conditioned_minimal_formalization_plan_dir
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = _read_json(manifest_path, errors)
    rows = [row for row in manifest.get("rows", []) if isinstance(row, dict)]
    contract_errors = validate_portable_gap_plan_payload(manifest)
    checks: list[FormalizationGapPlannerPortablePlanAuditCheck] = []
    checks.extend(_manifest_checks(manifest_path, manifest, contract_errors))
    checks.extend(_aggregate_row_checks(rows))
    checks.extend(_row_checks(rows, str(manifest.get("library_snapshot_ref", ""))))
    route_alignment_edge_schema = route_alignment_edge_json_schema()
    route_alignment_edge_schema_errors = [
        validate_route_alignment_edge(edge, route_alignment_edge_schema)
        for edge in _iter_alignment_edges(rows)
    ]
    n_route_alignment_edge_schema_valid = sum(
        1 for edge_errors in route_alignment_edge_schema_errors if not edge_errors
    )
    n_route_alignment_edge_schema_invalid = (
        len(route_alignment_edge_schema_errors) - n_route_alignment_edge_schema_valid
    )
    check_rows = [asdict(check) for check in checks]
    audit_row_schema = portable_plan_audit_row_json_schema()
    row_schema_errors = [
        validate_portable_plan_audit_row(row, audit_row_schema) for row in check_rows
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    by_category: dict[str, int] = {}
    for check in checks:
        by_category[check.category] = by_category.get(check.category, 0) + 1
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_PORTABLE_PLAN_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_portable_plan_audit",
        "audited_component": str(manifest.get("component_name", "")),
        "portable_schema_id": str(manifest.get("portable_schema_id", "")),
        "goal_conditioned_minimal_formalization_plan_dir": str(plan_dir),
        "goal_conditioned_minimal_formalization_plan_manifest": str(manifest_path),
        "target_prover_family": str(manifest.get("target_prover_family", "")),
        "library_snapshot_ref": str(manifest.get("library_snapshot_ref", "")),
        "n_plan_rows": len(rows),
        "n_checks": len(checks),
        "n_ok": sum(1 for check in checks if check.ok),
        "n_failed": sum(1 for check in checks if not check.ok),
        "n_error_severity": sum(
            1 for check in checks if not check.ok and check.severity == "error"
        ),
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": len(row_schema_errors) - n_row_schema_valid,
        "row_schema_errors": row_schema_errors,
        "portable_plan_audit_row_schema": audit_row_schema,
        "n_contract_errors": len(contract_errors),
        "contract_errors": contract_errors,
        "n_rows_ok": sum(1 for row in rows if bool(row.get("ok", False))),
        "n_rows_with_two_dag": sum(1 for row in rows if _has_two_dag(row)),
        "n_rows_with_alignment_edges": sum(
            1 for row in rows if _has_alignment_edges(row)
        ),
        "n_route_alignment_edges": len(route_alignment_edge_schema_errors),
        "n_route_alignment_edge_schema_valid": n_route_alignment_edge_schema_valid,
        "n_route_alignment_edge_schema_invalid": n_route_alignment_edge_schema_invalid,
        "route_alignment_edge_schema": route_alignment_edge_schema,
        "n_rows_with_and_or_plan": sum(1 for row in rows if _has_and_or_plan(row)),
        "n_rows_with_route_option_cost_graph": sum(
            1 for row in rows if _has_route_option_cost_graph(row)
        ),
        "n_rows_with_valid_route_option_cost_graph": sum(
            1 for row in rows if not _route_option_cost_graph_errors(row)
        ),
        "n_rows_with_work_packets": sum(1 for row in rows if _has_work_packets(row)),
        "n_rows_with_refinement_hooks": sum(
            1 for row in rows if _has_refinement_hooks(row)
        ),
        "n_rows_without_kernel_claims": sum(
            1 for row in rows if not _kernel_claim_paths(row)
        ),
        "n_rows_without_non_lean_legacy_realization_aliases": sum(
            1 for row in rows if not _non_lean_legacy_realization_alias_errors(row)
        ),
        "n_rows_with_declaration_evidence_target_consistency": sum(
            1 for row in rows if not _declaration_evidence_target_errors(row)
        ),
        "all_ok": (
            not errors
            and bool(checks)
            and all(check.ok for check in checks)
            and len(row_schema_errors) == n_row_schema_valid
        ),
        "errors": errors,
        "checks": check_rows,
        "by_category": dict(sorted(by_category.items())),
        "audit_fingerprint": stable_hash(check_rows),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS_AUDIT,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY_AUDIT,
        "planner_proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "portable plan audit validates planner artifacts, not theorem proofs",
            "semantic adequacy still requires source review and downstream prover replay",
            "kernel proof claims must be produced by a separate target-prover calibration gate",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_portable_plan_audit_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_portable_plan_audit.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in check_rows)
            + ("\n" if checks else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_portable_plan_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_portable_plan_audit_row.schema.json"
        ).write_text(json.dumps(audit_row_schema, indent=2), encoding="utf-8")
        write_route_alignment_edge_schema(out_dir)
    return payload


def portable_plan_audit_row_json_schema() -> dict[str, object]:
    required = [
        "schema_version",
        "check_id",
        "check_name",
        "category",
        "expected",
        "observed",
        "ok",
        "severity",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "errors",
    ]
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PORTABLE_PLAN_AUDIT_ROW_SCHEMA_ID,
        "title": "Formalization gap planner portable-plan audit row",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_PORTABLE_PLAN_AUDIT_SCHEMA_VERSION,
            },
            "check_id": {"type": "string", "minLength": 1},
            "check_name": {"type": "string", "minLength": 1},
            "category": {"type": "string", "minLength": 1},
            "expected": {"type": "string"},
            "observed": {"type": "string"},
            "ok": {"type": "boolean"},
            "severity": {"type": "string", "enum": ["info", "error"]},
            "proof_evidence_status": {
                "type": "string",
                "const": PROOF_EVIDENCE_STATUS_AUDIT,
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "errors": string_array,
        },
    }


def validate_portable_plan_audit_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    row_schema = schema or portable_plan_audit_row_json_schema()
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


def _manifest_checks(
    manifest_path: Path,
    manifest: dict[str, Any],
    contract_errors: list[str],
) -> list[FormalizationGapPlannerPortablePlanAuditCheck]:
    rows = [row for row in manifest.get("rows", []) if isinstance(row, dict)]
    return [
        _check(
            "plan_manifest_exists",
            "manifest",
            "manifest file exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "component_name",
            "manifest",
            LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
            str(manifest.get("component_name", "")),
            manifest.get("component_name") == LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
        ),
        _check(
            "portable_schema_id",
            "manifest",
            PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
            str(manifest.get("portable_schema_id", "")),
            manifest.get("portable_schema_id") == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        ),
        _check(
            "portable_schema_version",
            "manifest",
            str(PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION),
            str(manifest.get("portable_schema_version", "")),
            manifest.get("portable_schema_version")
            == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_VERSION,
        ),
        _check(
            "target_prover_family",
            "manifest",
            "nonempty target prover family",
            str(manifest.get("target_prover_family", "")),
            bool(str(manifest.get("target_prover_family", "")).strip()),
        ),
        _check(
            "library_snapshot_ref",
            "manifest",
            "nonempty library snapshot ref",
            str(manifest.get("library_snapshot_ref", "")),
            bool(str(manifest.get("library_snapshot_ref", "")).strip()),
        ),
        _check(
            "rows_present",
            "manifest",
            "at least one plan row",
            str(len(rows)),
            len(rows) > 0,
        ),
        _check(
            "portable_contract_validation",
            "contract",
            "zero contract errors",
            "; ".join(contract_errors[:8]) if contract_errors else "0",
            not contract_errors,
            errors=tuple(contract_errors),
        ),
        _check(
            "proof_boundary",
            "manifest",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")),
        ),
        _check(
            "proof_evidence_status",
            "manifest",
            PROOF_EVIDENCE_STATUS,
            str(manifest.get("proof_evidence_status", "")),
            manifest.get("proof_evidence_status") == PROOF_EVIDENCE_STATUS,
        ),
    ]


def _aggregate_row_checks(
    rows: list[dict[str, Any]],
) -> list[FormalizationGapPlannerPortablePlanAuditCheck]:
    return [
        _aggregate_check(
            "rows_ok",
            "rows",
            "all rows ok",
            sum(1 for row in rows if bool(row.get("ok", False))),
            len(rows),
        ),
        _aggregate_check(
            "rows_with_two_dag",
            "two_dag",
            "all rows have informal and realization DAGs",
            sum(1 for row in rows if _has_two_dag(row)),
            len(rows),
        ),
        _aggregate_check(
            "rows_with_alignment_edges",
            "two_dag",
            "all rows align selected informal primitives to realization candidates",
            sum(1 for row in rows if _has_alignment_edges(row)),
            len(rows),
        ),
        _aggregate_check(
            "rows_with_and_or_plan",
            "and_or",
            "all rows have AND/OR plan graph",
            sum(1 for row in rows if _has_and_or_plan(row)),
            len(rows),
        ),
        _aggregate_check(
            "rows_with_valid_route_option_cost_graph",
            "route_option_cost_graph",
            "all rows expose a valid route-option comparison graph",
            sum(1 for row in rows if not _route_option_cost_graph_errors(row)),
            len(rows),
        ),
        _aggregate_check(
            "rows_with_work_packets",
            "work_packets",
            "all rows have portable work packets",
            sum(1 for row in rows if _has_work_packets(row)),
            len(rows),
        ),
        _aggregate_check(
            "rows_with_refinement_hooks",
            "feedback_loop",
            "all rows have interactive refinement hooks",
            sum(1 for row in rows if _has_refinement_hooks(row)),
            len(rows),
        ),
        _aggregate_check(
            "rows_without_kernel_claims",
            "proof_boundary",
            "no rows contain kernel proof claims",
            sum(1 for row in rows if not _kernel_claim_paths(row)),
            len(rows),
        ),
        _aggregate_check(
            "rows_without_non_lean_legacy_realization_aliases",
            "cross_prover",
            "non-Lean rows do not carry Lean realization DAG aliases",
            sum(1 for row in rows if not _non_lean_legacy_realization_alias_errors(row)),
            len(rows),
        ),
        _aggregate_check(
            "rows_with_declaration_evidence_target_consistency",
            "cross_prover",
            "declaration evidence rows match each row target prover",
            sum(1 for row in rows if not _declaration_evidence_target_errors(row)),
            len(rows),
        ),
    ]


def _row_checks(
    rows: list[dict[str, Any]],
    snapshot_ref: str,
) -> list[FormalizationGapPlannerPortablePlanAuditCheck]:
    checks: list[FormalizationGapPlannerPortablePlanAuditCheck] = []
    for idx, row in enumerate(rows):
        row_label = str(row.get("display_name", f"row_{idx}"))
        row_prefix = f"row_{idx}_"
        selected = set(_str_tuple(row.get("selected_primitives", [])))
        realized = {
            *(
                str(node.get("primitive", ""))
                for node in row.get("existing_reuse_nodes", [])
                if isinstance(node, dict)
            ),
            *(
                str(node.get("primitive", ""))
                for node in row.get("minimal_additional_formalization_nodes", [])
                if isinstance(node, dict)
            ),
        }
        missing_realization = tuple(sorted(item for item in selected - realized if item))
        alignment_errors = _alignment_edge_errors(row)
        do_not_formalize = set(_str_tuple(row.get("do_not_formalize_now", [])))
        excluded_selected = tuple(sorted(selected & do_not_formalize))
        kernel_claims = _kernel_claim_paths(row)
        legacy_alias_errors = _non_lean_legacy_realization_alias_errors(row)
        declaration_target_errors = _declaration_evidence_target_errors(row)
        route_option_errors = _route_option_cost_graph_errors(row)
        checks.extend(
            [
                _check(
                    row_prefix + "library_snapshot_ref",
                    "rows",
                    snapshot_ref,
                    str(row.get("library_snapshot_ref", "")),
                    bool(snapshot_ref) and row.get("library_snapshot_ref") == snapshot_ref,
                ),
                _check(
                    row_prefix + "selected_primitives_realized",
                    "rows",
                    "all selected primitives appear in reuse or delta nodes",
                    ",".join(missing_realization),
                    not missing_realization,
                    errors=missing_realization,
                ),
                _check(
                    row_prefix + "excluded_primitives_not_selected",
                    "rows",
                    "do_not_formalize_now excludes selected primitives",
                    ",".join(excluded_selected),
                    not excluded_selected,
                    errors=excluded_selected,
                ),
                _check(
                    row_prefix + "two_dag",
                    "two_dag",
                    "informal and realization DAGs are nonempty",
                    row_label,
                    _has_two_dag(row),
                ),
                _check(
                    row_prefix + "route_alignment_edges",
                    "two_dag",
                    "selected informal primitives align to realization candidates",
                    "; ".join(alignment_errors) if alignment_errors else row_label,
                    not alignment_errors,
                    errors=alignment_errors,
                ),
                _check(
                    row_prefix + "and_or_plan",
                    "and_or",
                    "AND/OR graph has nodes and edges",
                    row_label,
                    _has_and_or_plan(row),
                ),
                _check(
                    row_prefix + "route_option_cost_graph",
                    "route_option_cost_graph",
                    (
                        "route-option comparison graph preserves the selected "
                        "cut and keeps comparison-only primitives out of "
                        "selected work"
                    ),
                    "; ".join(route_option_errors) if route_option_errors else row_label,
                    not route_option_errors,
                    errors=route_option_errors,
                ),
                _check(
                    row_prefix + "work_packets",
                    "work_packets",
                    "portable work packets have required gates",
                    row_label,
                    _has_work_packets(row),
                ),
                _check(
                    row_prefix + "refinement_hooks",
                    "feedback_loop",
                    "interactive hooks include Lean grounding and proof feedback",
                    ",".join(_hook_kinds(row)),
                    _has_refinement_hooks(row),
                ),
                _check(
                    row_prefix + "no_kernel_claims",
                    "proof_boundary",
                    "no kernel proof claims in planning artifact",
                    ",".join(kernel_claims),
                    not kernel_claims,
                    errors=kernel_claims,
                ),
                _check(
                    row_prefix + "non_lean_legacy_realization_aliases",
                    "cross_prover",
                    "non-Lean rows use formal_realization_dag_* fields only",
                    "; ".join(legacy_alias_errors) if legacy_alias_errors else row_label,
                    not legacy_alias_errors,
                    errors=legacy_alias_errors,
                ),
                _check(
                    row_prefix + "declaration_evidence_target_consistency",
                    "cross_prover",
                    "candidate and formal declaration evidence targets match row target",
                    (
                        "; ".join(declaration_target_errors)
                        if declaration_target_errors
                        else row_label
                    ),
                    not declaration_target_errors,
                    errors=declaration_target_errors,
                ),
            ]
        )
    return checks


def _aggregate_check(
    check_name: str,
    category: str,
    expected: str,
    observed_count: int,
    total: int,
) -> FormalizationGapPlannerPortablePlanAuditCheck:
    return _check(
        check_name,
        category,
        expected,
        f"{observed_count}/{total}",
        total > 0 and observed_count == total,
    )


def _has_two_dag(row: dict[str, Any]) -> bool:
    return bool(row.get("informal_knowledge_dag_nodes")) and bool(
        _formal_realization_nodes(row)
    )


def _has_alignment_edges(row: dict[str, Any]) -> bool:
    return not _alignment_edge_errors(row)


def _alignment_edge_errors(row: dict[str, Any]) -> tuple[str, ...]:
    selected = set(_str_tuple(row.get("selected_primitives", [])))
    edges = row.get("route_alignment_edges", [])
    if not isinstance(edges, (list, tuple)):
        return ("route_alignment_edges is not a list",)
    if selected and not edges:
        return ("route_alignment_edges missing",)
    informal_node_ids = {
        str(node.get("node_id", ""))
        for node in row.get("informal_knowledge_dag_nodes", [])
        if isinstance(node, dict)
    }
    formal_node_ids = {
        str(node.get("node_id", ""))
        for node in _formal_realization_nodes(row)
        if isinstance(node, dict)
    }
    aligned: set[str] = set()
    errors: list[str] = []
    for idx, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"route_alignment_edges[{idx}] is not an object")
            continue
        errors.extend(
            f"route_alignment_edges[{idx}].{error}"
            for error in validate_route_alignment_edge(edge)
        )
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        primitive = str(edge.get("primitive", ""))
        kind = str(edge.get("kind", ""))
        if not source:
            errors.append(f"route_alignment_edges[{idx}].source missing")
        elif source not in informal_node_ids:
            errors.append(f"route_alignment_edges[{idx}].source not in informal DAG")
        if not target:
            errors.append(f"route_alignment_edges[{idx}].target missing")
        elif target not in formal_node_ids:
            errors.append(f"route_alignment_edges[{idx}].target not in formal-realization DAG")
        if kind != "aligned_to_formal_realization_candidate":
            errors.append(f"route_alignment_edges[{idx}].kind mismatch")
        if not primitive:
            errors.append(f"route_alignment_edges[{idx}].primitive missing")
        else:
            aligned.add(primitive)
    missing = tuple(sorted(item for item in selected - aligned if item))
    if missing:
        errors.append("missing selected primitive alignments: " + ",".join(missing))
    return tuple(errors)


def _formal_realization_nodes(row: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    nodes = row.get("formal_realization_dag_nodes", [])
    if not isinstance(nodes, (list, tuple)) or not nodes:
        if _is_lean_target_prover(row.get("target_prover_family", "")):
            nodes = row.get("lean_realization_dag_nodes", [])
        else:
            nodes = []
    if not isinstance(nodes, (list, tuple)):
        return tuple()
    return tuple(node for node in nodes if isinstance(node, dict))


def _non_lean_legacy_realization_alias_errors(row: dict[str, Any]) -> tuple[str, ...]:
    target_key = _target_prover_key(row.get("target_prover_family", ""))
    if not target_key or target_key == "lean4":
        return tuple()
    errors: list[str] = []
    if _nonempty_legacy_field_value(row.get("lean_realization_dag_nodes")):
        errors.append(
            "lean_realization_dag_nodes is a Lean-only legacy alias; "
            "non-Lean portable plan rows must use formal_realization_dag_nodes"
        )
    if _nonempty_legacy_field_value(row.get("lean_realization_dag_edges")):
        errors.append(
            "lean_realization_dag_edges is a Lean-only legacy alias; "
            "non-Lean portable plan rows must use formal_realization_dag_edges"
        )
    return tuple(errors)


def _nonempty_legacy_field_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return any(_nonempty_legacy_field_value(item) for item in value)
    return bool(value)


def _declaration_evidence_target_errors(row: dict[str, Any]) -> tuple[str, ...]:
    expected_key = _target_prover_key(row.get("target_prover_family", ""))
    if not expected_key:
        return tuple()
    errors: list[str] = []

    def check_rows(value: object, *, path: str, field_name: str) -> None:
        if not isinstance(value, (list, tuple)):
            if _nonempty_legacy_field_value(value):
                errors.append(f"{path}.{field_name} must be an array of objects")
            return
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                if _nonempty_legacy_field_value(item):
                    errors.append(f"{path}.{field_name}[{index}] must be an object")
                continue
            target = str(
                item.get("target_prover_family", "") or item.get("target_prover", "")
            ).strip()
            if not target:
                continue
            actual_key = _target_prover_key(target)
            if actual_key != expected_key:
                errors.append(
                    f"{path}.{field_name}[{index}].target_prover_family {target} "
                    f"does not match row target_prover_family "
                    f"{row.get('target_prover_family', '')}"
                )

    def visit(value: object, path: str) -> None:
        if isinstance(value, dict):
            if "lean_declaration_hits" in value and expected_key != "lean4":
                if _nonempty_legacy_field_value(value.get("lean_declaration_hits")):
                    errors.append(
                        f"{path}.lean_declaration_hits is a Lean-only legacy alias; "
                        "non-Lean portable plan rows must use formal_declaration_hits"
                    )
            for field_name in ("candidate_declaration_rows", "formal_declaration_hits"):
                if field_name in value:
                    check_rows(
                        value.get(field_name),
                        path=path,
                        field_name=field_name,
                    )
            for key, nested in value.items():
                nested_path = f"{path}.{key}" if path else str(key)
                visit(nested, nested_path)
        elif isinstance(value, (list, tuple)):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")

    visit(row, "row")
    return tuple(sorted(set(errors)))


def _is_lean_target_prover(value: object) -> bool:
    return _target_prover_key(value) == "lean4"


def _target_prover_key(value: object) -> str:
    key = str(value).strip().lower().replace("-", "_")
    aliases = {
        "coq": "rocq",
        "coq8": "rocq",
        "coq_8": "rocq",
        "coq_rocq": "rocq",
        "rocq_coq": "rocq",
        "isabelle_hol": "isabelle",
        "lean": "lean4",
        "lean_4": "lean4",
    }
    return aliases.get(key, key)


def _iter_alignment_edges(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    edges: list[dict[str, Any]] = []
    for row in rows:
        row_edges = row.get("route_alignment_edges", [])
        if not isinstance(row_edges, (list, tuple)):
            continue
        edges.extend(edge for edge in row_edges if isinstance(edge, dict))
    return tuple(edges)


def _has_and_or_plan(row: dict[str, Any]) -> bool:
    return bool(row.get("and_or_plan_nodes")) and bool(row.get("and_or_plan_edges"))


def _has_route_option_cost_graph(row: dict[str, Any]) -> bool:
    return isinstance(row.get("route_option_cost_graph", {}), dict) and bool(
        row.get("route_option_cost_graph", {})
    )


def _route_option_cost_graph_errors(row: dict[str, Any]) -> tuple[str, ...]:
    graph = row.get("route_option_cost_graph", {})
    summary = row.get("route_option_cost_graph_summary", {})
    if not isinstance(graph, dict):
        return ("route_option_cost_graph is not an object",)
    if not graph:
        return ("route_option_cost_graph missing",)
    if not isinstance(summary, dict):
        return ("route_option_cost_graph_summary is not an object",)
    selected = set(_str_tuple(row.get("selected_primitives", [])))
    realized = _realized_primitive_set(row)
    route_options = _dict_tuple(graph.get("route_options", []))
    if not route_options:
        return ("route_option_cost_graph.route_options missing",)
    route_option_ids = tuple(
        str(option.get("route_option_id", ""))
        for option in route_options
        if str(option.get("route_option_id", ""))
    )
    selected_route_option_id = str(graph.get("selected_route_option_id", ""))
    selected_options = tuple(
        option
        for option in route_options
        if option.get("selected")
        or str(option.get("route_option_id", "")) == selected_route_option_id
    )
    errors: list[str] = []
    if not selected_route_option_id:
        errors.append("selected_route_option_id missing")
    elif selected_route_option_id not in set(route_option_ids):
        errors.append("selected_route_option_id not in route_options")
    if len(selected_options) != 1:
        errors.append("exactly one selected route option required")
    if selected_options:
        selected_option_primitives = set(
            _str_tuple(selected_options[0].get("selected_primitives", []))
        )
        if selected_option_primitives != selected:
            errors.append(
                "selected route option primitives differ from row selected_primitives"
            )
    graph_primitives = set()
    for option in route_options:
        option_id = str(option.get("route_option_id", ""))
        if not option_id:
            errors.append("route option missing route_option_id")
        primitives = set(_str_tuple(option.get("selected_primitives", [])))
        if not primitives:
            errors.append(f"route option {option_id or '<missing>'} primitives missing")
        graph_primitives.update(primitives)
    expected_comparison_only = graph_primitives - selected
    summary_comparison_only = set(
        _str_tuple(summary.get("comparison_only_primitives", []))
    )
    if summary_comparison_only != expected_comparison_only:
        errors.append("comparison_only_primitives summary mismatch")
    if summary_comparison_only & selected:
        errors.append("comparison_only_primitives overlap selected_primitives")
    if summary_comparison_only & realized:
        errors.append("comparison_only_primitives overlap selected work nodes")
    if _int_or_negative_one(summary.get("n_route_options")) != len(route_options):
        errors.append("n_route_options summary mismatch")
    unselected_ids = set(route_option_ids) - {selected_route_option_id}
    summary_unselected_ids = set(
        _str_tuple(summary.get("unselected_route_option_ids", []))
    )
    if summary_unselected_ids != unselected_ids:
        errors.append("unselected_route_option_ids summary mismatch")
    if _int_or_negative_one(
        summary.get("n_unselected_route_options")
    ) != len(unselected_ids):
        errors.append("n_unselected_route_options summary mismatch")
    return tuple(sorted(set(errors)))


def _int_or_negative_one(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def _realized_primitive_set(row: dict[str, Any]) -> set[str]:
    primitives: set[str] = set()
    for field_name in (
        "existing_reuse_nodes",
        "minimal_additional_formalization_nodes",
    ):
        rows = row.get(field_name, [])
        if not isinstance(rows, (list, tuple)):
            continue
        primitives.update(
            str(node.get("primitive", ""))
            for node in rows
            if isinstance(node, dict) and str(node.get("primitive", ""))
        )
    return primitives


def _has_work_packets(row: dict[str, Any]) -> bool:
    packets = row.get("portable_work_packets", row.get("next_work_packets", []))
    if not isinstance(packets, (list, tuple)) or not packets:
        return False
    for packet in packets:
        if not isinstance(packet, dict):
            return False
        for field_name in (
            "primitive",
            "action_class",
            "worker_packet_kind",
            "required_gate",
        ):
            if not str(packet.get(field_name, "")):
                return False
    return True


def _has_refinement_hooks(row: dict[str, Any]) -> bool:
    hook_kinds = set(_hook_kinds(row))
    has_formal_grounding = bool(
        {"formal_library_grounding", "lean_library_grounding"} & hook_kinds
    )
    return has_formal_grounding and "proof_state_feedback" in hook_kinds


def _hook_kinds(row: dict[str, Any]) -> tuple[str, ...]:
    hooks = row.get("interactive_refinement_hooks", [])
    if not isinstance(hooks, (list, tuple)):
        return tuple()
    return tuple(
        str(hook.get("hook_kind", ""))
        for hook in hooks
        if isinstance(hook, dict) and str(hook.get("hook_kind", ""))
    )


def _kernel_claim_paths(value: Any, prefix: str = "") -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            key_text = str(key).lower()
            if key_text in FORBIDDEN_PROOF_CLAIM_KEYS and _truthy_claim(nested):
                paths.append(path)
            if key_text in {"proof_evidence_status", "proof_status"} and _looks_verified(nested):
                paths.append(path)
            paths.extend(_kernel_claim_paths(nested, path))
    elif isinstance(value, (list, tuple)):
        for idx, nested in enumerate(value):
            path = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            paths.extend(_kernel_claim_paths(nested, path))
    return tuple(sorted(set(paths)))


def _truthy_claim(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "verified", "proved", "kernel_verified"}
    return bool(value)


def _looks_verified(value: Any) -> bool:
    text = str(value).lower()
    if "not" in text and "proof" in text:
        return False
    return any(
        token in text
        for token in ("kernel_verified", "theorem_proved", "proof_evidence")
    )


def _check(
    check_name: str,
    category: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    errors: tuple[str, ...] | list[str] = (),
) -> FormalizationGapPlannerPortablePlanAuditCheck:
    return FormalizationGapPlannerPortablePlanAuditCheck(
        schema_version=FORMALIZATION_GAP_PLANNER_PORTABLE_PLAN_AUDIT_SCHEMA_VERSION,
        check_id="formalization_gap_planner_portable_plan_audit:"
        + stable_hash([check_name, category, expected, observed])[:16],
        check_name=check_name,
        category=category,
        expected=expected,
        observed=observed,
        ok=bool(ok),
        severity="info" if ok else "error",
        errors=tuple(str(error) for error in errors if str(error)),
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


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(str(value) for value in values if str(value))


def _dict_tuple(values: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict(value) for value in values if isinstance(value, dict))


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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Portable Plan Audit",
        "",
        f"- Plan rows: {payload.get('n_plan_rows')}",
        f"- Checks: {payload.get('n_ok')}/{payload.get('n_checks')}",
        f"- Failed: {payload.get('n_failed')}",
        f"- Target prover: `{payload.get('target_prover_family')}`",
        f"- Library snapshot: `{payload.get('library_snapshot_ref')}`",
        f"- Two-DAG rows: {payload.get('n_rows_with_two_dag')}",
        f"- Alignment-edge rows: {payload.get('n_rows_with_alignment_edges')}",
        (
            f"- Alignment-edge schema valid: "
            f"{payload.get('n_route_alignment_edge_schema_valid')}/"
            f"{payload.get('n_route_alignment_edges')}"
        ),
        (
            f"- Audit-row schema valid: {payload.get('n_row_schema_valid')}/"
            f"{payload.get('n_checks')}"
        ),
        f"- Work-packet rows: {payload.get('n_rows_with_work_packets')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY_AUDIT)),
        "",
        "## Failed Checks",
        "",
    ]
    failed = [
        check for check in payload.get("checks", []) if isinstance(check, dict) and not check.get("ok")
    ]
    if not failed:
        lines.append("- none")
    for check in failed:
        lines.append(
            f"- `{check.get('check_name')}` category={check.get('category')} "
            f"expected={check.get('expected')} observed={check.get('observed')}"
        )
    return "\n".join(lines) + "\n"

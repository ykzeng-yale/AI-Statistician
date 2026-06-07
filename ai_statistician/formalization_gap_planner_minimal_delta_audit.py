from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PROOF_EVIDENCE_BOUNDARY as PLANNER_PROOF_EVIDENCE_BOUNDARY,
)


FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_SCHEMA_VERSION = 1
MINIMAL_DELTA_DECISION_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-minimal-delta-decision-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Minimal-delta audit rows check structural cost accounting, selected-cut "
    "discipline, and obvious dominance among planned routes. They are not "
    "theorem proof evidence and do not prove semantic optimality."
)
ACTION_BUCKETS = (
    "existing_reuse_nodes",
    "wrapper_nodes",
    "bridge_nodes",
    "source_discovery_nodes",
    "first_principles_nodes",
)
MINIMAL_DELTA_BUCKETS = (
    "wrapper_nodes",
    "bridge_nodes",
    "source_discovery_nodes",
    "first_principles_nodes",
)
MINIMALITY_EVIDENCE_STATUS = "STRUCTURAL_MINIMALITY_PROXY_NOT_SEMANTIC_OPTIMALITY"
DOMINANCE_STATUSES = (
    "NON_DOMINATED_UNDER_CURRENT_STRUCTURAL_PROXY",
    "DOMINATED_BY_LOWER_COST_ROUTE_UNDER_CURRENT_STRUCTURAL_PROXY",
)


@dataclass(frozen=True)
class FormalizationGapPlannerMinimalDeltaAuditCheck:
    schema_version: int
    check_id: str
    check_name: str
    category: str
    expected: str
    observed: str
    ok: bool
    severity: str
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormalizationGapPlannerMinimalDeltaDecisionRow:
    schema_version: int
    minimal_delta_decision_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    target_prover_family: str
    library_snapshot_ref: str
    route_class: str
    pareto_profile: str
    goal_conditioned_cost: int
    route_efficiency_score: int
    import_cone_size: int
    dependency_graph_depth: int
    route_cost_breakdown: dict[str, object]
    selected_primitives: tuple[str, ...]
    existing_reuse_primitives: tuple[str, ...]
    minimal_delta_primitives: tuple[str, ...]
    work_packet_primitives: tuple[str, ...]
    do_not_formalize_now: tuple[str, ...]
    cost_formula_ok: bool
    node_cost_accounting_ok: bool
    work_packet_cut_ok: bool
    do_not_formalize_disjoint: bool
    delta_nodes_connected: bool
    dominated_by_goal_plan_ids: tuple[str, ...]
    dominance_status: str
    minimality_evidence_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_minimal_delta(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Audit costed route cuts for structural minimal-delta discipline."""

    errors: list[str] = []
    plan_dir = goal_conditioned_minimal_formalization_plan_dir
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = _read_json(manifest_path, errors)
    rows = [row for row in manifest.get("rows", []) if isinstance(row, dict)]
    checks: list[FormalizationGapPlannerMinimalDeltaAuditCheck] = []
    checks.extend(_manifest_checks(manifest_path, manifest, rows))
    checks.extend(_route_order_checks(rows))
    checks.extend(_row_checks(rows))
    dominance_witnesses = _dominance_witnesses(rows)
    checks.extend(_dominance_checks(dominance_witnesses))
    decision_rows = _decision_rows(rows, dominance_witnesses)
    decision_row_schema = minimal_delta_decision_row_json_schema()
    decision_row_schema_errors = [
        validate_minimal_delta_decision_row(asdict(row), decision_row_schema)
        for row in decision_rows
    ]
    n_decision_row_schema_valid = sum(
        1 for row_errors in decision_row_schema_errors if not row_errors
    )
    n_decision_row_schema_invalid = (
        len(decision_row_schema_errors) - n_decision_row_schema_valid
    )
    by_category: dict[str, int] = {}
    for check in checks:
        by_category[check.category] = by_category.get(check.category, 0) + 1
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_minimal_delta_audit",
        "audited_component": str(manifest.get("component_name", "")),
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
        "n_rows_with_cost_formula_ok": sum(1 for row in rows if _cost_formula_ok(row)),
        "n_rows_with_node_cost_accounting_ok": sum(
            1 for row in rows if _node_cost_accounting_ok(row)
        ),
        "n_rows_with_work_packet_cut_ok": sum(
            1 for row in rows if _work_packet_cut_ok(row)
        ),
        "n_rows_with_do_not_formalize_disjoint": sum(
            1 for row in rows if _do_not_formalize_disjoint(row)
        ),
        "n_rows_with_connected_delta_nodes": sum(
            1 for row in rows if _delta_nodes_connected(row)
        ),
        "n_dominated_route_witnesses": len(dominance_witnesses),
        "dominance_witnesses": dominance_witnesses,
        "n_minimal_delta_decision_rows": len(decision_rows),
        "n_minimal_delta_decision_row_schema_valid": n_decision_row_schema_valid,
        "n_minimal_delta_decision_row_schema_invalid": n_decision_row_schema_invalid,
        "minimal_delta_decision_row_schema": decision_row_schema,
        "minimal_delta_decision_rows": [asdict(row) for row in decision_rows],
        "by_category": dict(sorted(by_category.items())),
        "all_ok": (
            not errors
            and bool(checks)
            and all(check.ok for check in checks)
            and n_decision_row_schema_invalid == 0
        ),
        "errors": errors,
        "checks": [asdict(check) for check in checks],
        "audit_fingerprint": stable_hash([asdict(check) for check in checks]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "planner_proof_evidence_boundary": PLANNER_PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "structural dominance is checked only among rows for the same displayed target",
            "semantic route adequacy still requires source-backed review and prover feedback",
            "true proof minimality cannot be established without target-prover replay/calibration",
        ],
    }
    if n_decision_row_schema_invalid:
        payload["errors"] = [
            *[str(error) for error in payload.get("errors", [])],
            "minimal delta decision row schema validation failed",
        ]
        payload["all_ok"] = False
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_minimal_delta_audit_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formalization_gap_planner_minimal_delta_audit.jsonl").write_text(
            "\n".join(json.dumps(asdict(check), sort_keys=True) for check in checks)
            + ("\n" if checks else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formalization_gap_planner_minimal_delta_decisions.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in decision_rows)
            + ("\n" if decision_rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
        ).write_text(json.dumps(decision_row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_minimal_delta_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _manifest_checks(
    manifest_path: Path,
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[FormalizationGapPlannerMinimalDeltaAuditCheck]:
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
            "rows_present",
            "manifest",
            "at least one plan row",
            str(len(rows)),
            bool(rows),
        ),
        _check(
            "rows_ok",
            "manifest",
            "all plan rows ok",
            f"{sum(1 for row in rows if row.get('ok'))}/{len(rows)}",
            bool(rows) and all(bool(row.get("ok", False)) for row in rows),
        ),
        _check(
            "planner_boundary",
            "proof_boundary",
            "manifest is not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", "")),
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")).lower(),
        ),
    ]


def _route_order_checks(
    rows: list[dict[str, Any]],
) -> list[FormalizationGapPlannerMinimalDeltaAuditCheck]:
    observed = [_row_sort_key(row) for row in rows]
    expected = sorted(observed)
    return [
        _check(
            "route_order_cost_then_efficiency",
            "route_order",
            "rows sorted by cost, efficiency, display name, plan id",
            json.dumps(expected, default=str),
            observed == expected,
        )
    ]


def _row_checks(
    rows: list[dict[str, Any]],
) -> list[FormalizationGapPlannerMinimalDeltaAuditCheck]:
    checks: list[FormalizationGapPlannerMinimalDeltaAuditCheck] = []
    for idx, row in enumerate(rows):
        label = _row_label(row, idx)
        checks.extend(
            [
                _check(
                    f"{label}:cost_formula",
                    "cost_accounting",
                    "final = max(0, base + import + depth + blocker - trust_credit)",
                    _cost_formula_observed(row),
                    _cost_formula_ok(row),
                ),
                _check(
                    f"{label}:node_cost_accounting",
                    "cost_accounting",
                    "base route cost equals selected action-node costs",
                    _node_cost_accounting_observed(row),
                    _node_cost_accounting_ok(row),
                ),
                _check(
                    f"{label}:minimal_nodes_match_buckets",
                    "selected_cut",
                    "minimal nodes equal wrapper/bridge/source/first-principles buckets",
                    _minimal_nodes_match_observed(row),
                    _minimal_nodes_match_buckets(row),
                ),
                _check(
                    f"{label}:unique_selected_primitives",
                    "selected_cut",
                    "selected cut primitives are unique",
                    ",".join(_duplicate_primitives(_selected_action_nodes(row))),
                    not _duplicate_primitives(_selected_action_nodes(row)),
                ),
                _check(
                    f"{label}:work_packets_inside_selected_cut",
                    "work_packets",
                    "work packets target selected delta or existing-reuse nodes",
                    _work_packet_cut_observed(row),
                    _work_packet_cut_ok(row),
                ),
                _check(
                    f"{label}:do_not_formalize_disjoint",
                    "exclusions",
                    "do_not_formalize_now is disjoint from selected and packet primitives",
                    _do_not_formalize_observed(row),
                    _do_not_formalize_disjoint(row),
                ),
                _check(
                    f"{label}:delta_nodes_connected",
                    "and_or_graph",
                    "each delta node appears in the AND/OR graph and is connected to the target",
                    _delta_nodes_connected_observed(row),
                    _delta_nodes_connected(row),
                ),
                _check(
                    f"{label}:minimality_boundary",
                    "proof_boundary",
                    "row says minimality is a planner proxy, not proof evidence",
                    str(row.get("proof_evidence_boundary", "")),
                    "not theorem proof evidence"
                    in str(row.get("proof_evidence_boundary", "")).lower(),
                ),
            ]
        )
    return checks


def _dominance_checks(
    dominance_witnesses: list[dict[str, object]],
) -> list[FormalizationGapPlannerMinimalDeltaAuditCheck]:
    return [
        _check(
            "no_same_target_dominated_routes",
            "dominance",
            "no same-target route has same/subset primitives and no worse structural costs",
            json.dumps(dominance_witnesses, sort_keys=True),
            not dominance_witnesses,
        )
    ]


def _decision_rows(
    rows: list[dict[str, Any]],
    dominance_witnesses: list[dict[str, object]],
) -> tuple[FormalizationGapPlannerMinimalDeltaDecisionRow, ...]:
    dominated_by: dict[str, set[str]] = {}
    for witness in dominance_witnesses:
        dominated_id = str(witness.get("dominated_goal_plan_id", ""))
        dominating_id = str(witness.get("dominating_goal_plan_id", ""))
        if dominated_id and dominating_id:
            dominated_by.setdefault(dominated_id, set()).add(dominating_id)

    decision_rows: list[FormalizationGapPlannerMinimalDeltaDecisionRow] = []
    for idx, row in enumerate(rows):
        goal_plan_id = str(row.get("goal_plan_id", ""))
        row_dominated_by = tuple(sorted(dominated_by.get(goal_plan_id, set())))
        checks = {
            "cost_formula_ok": _cost_formula_ok(row),
            "node_cost_accounting_ok": _node_cost_accounting_ok(row),
            "work_packet_cut_ok": _work_packet_cut_ok(row),
            "do_not_formalize_disjoint": _do_not_formalize_disjoint(row),
            "delta_nodes_connected": _delta_nodes_connected(row),
        }
        row_errors = tuple(
            name for name, ok in checks.items() if not ok
        ) + (
            tuple(f"dominated_by:{item}" for item in row_dominated_by)
            if row_dominated_by
            else tuple()
        )
        dominance_status = (
            "DOMINATED_BY_LOWER_COST_ROUTE_UNDER_CURRENT_STRUCTURAL_PROXY"
            if row_dominated_by
            else "NON_DOMINATED_UNDER_CURRENT_STRUCTURAL_PROXY"
        )
        breakdown = row.get("route_cost_breakdown", {})
        decision_rows.append(
            FormalizationGapPlannerMinimalDeltaDecisionRow(
                schema_version=FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_SCHEMA_VERSION,
                minimal_delta_decision_id=(
                    "formalization_gap_planner_minimal_delta_decision:"
                    + stable_hash([goal_plan_id, row.get("route_id", ""), idx])[:20]
                ),
                goal_plan_id=goal_plan_id,
                route_id=str(row.get("route_id", "")),
                display_name=str(row.get("display_name", "")),
                target_prover_family=str(row.get("target_prover_family", "")),
                library_snapshot_ref=str(row.get("library_snapshot_ref", "")),
                route_class=str(row.get("route_class", "")),
                pareto_profile=str(row.get("pareto_profile", "")),
                goal_conditioned_cost=_int(row.get("goal_conditioned_cost")),
                route_efficiency_score=_int(row.get("route_efficiency_score")),
                import_cone_size=_int(row.get("import_cone_size")),
                dependency_graph_depth=_int(row.get("dependency_graph_depth")),
                route_cost_breakdown=dict(breakdown) if isinstance(breakdown, dict) else {},
                selected_primitives=tuple(sorted(_selected_primitives(row))),
                existing_reuse_primitives=tuple(
                    sorted(_primitive_set(_node_list(row, "existing_reuse_nodes")))
                ),
                minimal_delta_primitives=tuple(sorted(_primitive_set(_minimal_nodes(row)))),
                work_packet_primitives=tuple(
                    sorted(_primitive_set(_node_list(row, "portable_work_packets")))
                ),
                do_not_formalize_now=tuple(
                    sorted(_str_tuple(row.get("do_not_formalize_now", [])))
                ),
                cost_formula_ok=checks["cost_formula_ok"],
                node_cost_accounting_ok=checks["node_cost_accounting_ok"],
                work_packet_cut_ok=checks["work_packet_cut_ok"],
                do_not_formalize_disjoint=checks["do_not_formalize_disjoint"],
                delta_nodes_connected=checks["delta_nodes_connected"],
                dominated_by_goal_plan_ids=row_dominated_by,
                dominance_status=dominance_status,
                minimality_evidence_status=MINIMALITY_EVIDENCE_STATUS,
                proof_evidence_status=PROOF_EVIDENCE_STATUS,
                proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
                ok=not row_errors,
                errors=row_errors,
            )
        )
    return tuple(decision_rows)


def minimal_delta_decision_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": MINIMAL_DELTA_DECISION_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Minimal-Delta Decision Row",
        "description": (
            "Per-route costed-cut decision contract for the library-aware "
            "formalization gap planner. Rows explain the current structural "
            "minimality proxy and are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "minimal_delta_decision_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "target_prover_family",
            "library_snapshot_ref",
            "route_class",
            "pareto_profile",
            "goal_conditioned_cost",
            "route_efficiency_score",
            "import_cone_size",
            "dependency_graph_depth",
            "route_cost_breakdown",
            "selected_primitives",
            "existing_reuse_primitives",
            "minimal_delta_primitives",
            "work_packet_primitives",
            "do_not_formalize_now",
            "cost_formula_ok",
            "node_cost_accounting_ok",
            "work_packet_cut_ok",
            "do_not_formalize_disjoint",
            "delta_nodes_connected",
            "dominated_by_goal_plan_ids",
            "dominance_status",
            "minimality_evidence_status",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_SCHEMA_VERSION,
            },
            "minimal_delta_decision_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "target_prover_family": {"type": "string", "minLength": 1},
            "library_snapshot_ref": {"type": "string", "minLength": 1},
            "route_class": {"type": "string", "minLength": 1},
            "pareto_profile": {"type": "string", "minLength": 1},
            "goal_conditioned_cost": {"type": "integer", "minimum": 0},
            "route_efficiency_score": {"type": "integer"},
            "import_cone_size": {"type": "integer", "minimum": 0},
            "dependency_graph_depth": {"type": "integer", "minimum": 0},
            "route_cost_breakdown": {"type": "object"},
            "selected_primitives": string_array,
            "existing_reuse_primitives": string_array,
            "minimal_delta_primitives": string_array,
            "work_packet_primitives": string_array,
            "do_not_formalize_now": string_array,
            "cost_formula_ok": {"type": "boolean"},
            "node_cost_accounting_ok": {"type": "boolean"},
            "work_packet_cut_ok": {"type": "boolean"},
            "do_not_formalize_disjoint": {"type": "boolean"},
            "delta_nodes_connected": {"type": "boolean"},
            "dominated_by_goal_plan_ids": string_array,
            "dominance_status": {"enum": list(DOMINANCE_STATUSES)},
            "minimality_evidence_status": {"const": MINIMALITY_EVIDENCE_STATUS},
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {"type": "string", "minLength": 1},
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_minimal_delta_decision_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> list[str]:
    row_schema = schema or minimal_delta_decision_row_json_schema()
    if not isinstance(row, dict):
        return ["minimal delta decision row must be an object"]
    errors: list[str] = []
    required = row_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = row_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    boundary = str(row.get("proof_evidence_boundary", "")).lower()
    if "not theorem proof evidence" not in boundary:
        errors.append("proof_evidence_boundary must say not theorem proof evidence")
    selected = set(_str_tuple(row.get("selected_primitives", [])))
    decision_primitives = set(_str_tuple(row.get("existing_reuse_primitives", []))) | set(
        _str_tuple(row.get("minimal_delta_primitives", []))
    )
    missing = tuple(sorted(selected - decision_primitives))
    if missing:
        errors.append("selected_primitives missing from reuse/delta decision: " + ",".join(missing))
    return errors


def _dominance_witnesses(rows: list[dict[str, Any]]) -> list[dict[str, object]]:
    witnesses: list[dict[str, object]] = []
    for idx, candidate in enumerate(rows):
        for alt_idx, alternative in enumerate(rows):
            if idx == alt_idx:
                continue
            if _target_key(candidate) != _target_key(alternative):
                continue
            if _dominates(alternative, candidate):
                witnesses.append(
                    {
                        "dominated_goal_plan_id": str(candidate.get("goal_plan_id", "")),
                        "dominating_goal_plan_id": str(alternative.get("goal_plan_id", "")),
                        "target": _target_key(candidate),
                        "dominated_cost": _int(candidate.get("goal_conditioned_cost")),
                        "dominating_cost": _int(alternative.get("goal_conditioned_cost")),
                        "dominated_primitives": _selected_primitives(candidate),
                        "dominating_primitives": _selected_primitives(alternative),
                    }
                )
    return witnesses


def _dominates(alternative: dict[str, Any], candidate: dict[str, Any]) -> bool:
    alternative_primitives = set(_selected_primitives(alternative))
    candidate_primitives = set(_selected_primitives(candidate))
    if not alternative_primitives.issubset(candidate_primitives):
        return False
    alternative_profile = _dominance_profile(alternative)
    candidate_profile = _dominance_profile(candidate)
    no_worse = all(
        alternative_profile[key] <= candidate_profile[key]
        for key in (
            "goal_conditioned_cost",
            "minimal_node_count",
            "import_cone_size",
            "dependency_graph_depth",
            "first_principles_count",
            "source_discovery_count",
        )
    ) and alternative_profile["existing_reuse_count"] >= candidate_profile[
        "existing_reuse_count"
    ]
    strictly_better = any(
        alternative_profile[key] < candidate_profile[key]
        for key in (
            "goal_conditioned_cost",
            "minimal_node_count",
            "import_cone_size",
            "dependency_graph_depth",
            "first_principles_count",
            "source_discovery_count",
        )
    ) or alternative_profile["existing_reuse_count"] > candidate_profile[
        "existing_reuse_count"
    ]
    return no_worse and strictly_better


def _dominance_profile(row: dict[str, Any]) -> dict[str, int]:
    return {
        "goal_conditioned_cost": _int(row.get("goal_conditioned_cost")),
        "minimal_node_count": len(_minimal_nodes(row)),
        "existing_reuse_count": len(_node_list(row, "existing_reuse_nodes")),
        "import_cone_size": _int(row.get("import_cone_size")),
        "dependency_graph_depth": _int(row.get("dependency_graph_depth")),
        "first_principles_count": len(_node_list(row, "first_principles_nodes")),
        "source_discovery_count": len(_node_list(row, "source_discovery_nodes")),
    }


def _cost_formula_ok(row: dict[str, Any]) -> bool:
    breakdown = row.get("route_cost_breakdown", {})
    if not isinstance(breakdown, dict):
        return False
    expected = max(
        0,
        _int(breakdown.get("base_route_cost"))
        + _int(breakdown.get("import_cone_penalty"))
        + _int(breakdown.get("dependency_depth_penalty"))
        + _int(breakdown.get("blocker_penalty"))
        - _int(breakdown.get("source_trust_credit")),
    )
    return expected == _int(row.get("goal_conditioned_cost")) == _int(
        breakdown.get("final_goal_conditioned_cost")
    )


def _cost_formula_observed(row: dict[str, Any]) -> str:
    breakdown = row.get("route_cost_breakdown", {})
    if not isinstance(breakdown, dict):
        return "missing route_cost_breakdown"
    expected = max(
        0,
        _int(breakdown.get("base_route_cost"))
        + _int(breakdown.get("import_cone_penalty"))
        + _int(breakdown.get("dependency_depth_penalty"))
        + _int(breakdown.get("blocker_penalty"))
        - _int(breakdown.get("source_trust_credit")),
    )
    return (
        f"expected={expected} row={_int(row.get('goal_conditioned_cost'))} "
        f"breakdown={_int(breakdown.get('final_goal_conditioned_cost'))}"
    )


def _node_cost_accounting_ok(row: dict[str, Any]) -> bool:
    breakdown = row.get("route_cost_breakdown", {})
    if not isinstance(breakdown, dict):
        return False
    return _int(breakdown.get("base_route_cost")) == sum(
        _int(node.get("cost")) for node in _selected_action_nodes(row)
    )


def _node_cost_accounting_observed(row: dict[str, Any]) -> str:
    breakdown = row.get("route_cost_breakdown", {})
    base = _int(breakdown.get("base_route_cost")) if isinstance(breakdown, dict) else 0
    node_cost = sum(_int(node.get("cost")) for node in _selected_action_nodes(row))
    return f"base_route_cost={base} selected_node_cost={node_cost}"


def _minimal_nodes_match_buckets(row: dict[str, Any]) -> bool:
    minimal_primitives = _primitive_set(_minimal_nodes(row))
    bucket_primitives = _primitive_set(
        [
            node
            for bucket in MINIMAL_DELTA_BUCKETS
            for node in _node_list(row, bucket)
        ]
    )
    return minimal_primitives == bucket_primitives


def _minimal_nodes_match_observed(row: dict[str, Any]) -> str:
    minimal_primitives = sorted(_primitive_set(_minimal_nodes(row)))
    bucket_primitives = sorted(
        _primitive_set(
            [
                node
                for bucket in MINIMAL_DELTA_BUCKETS
                for node in _node_list(row, bucket)
            ]
        )
    )
    return f"minimal={minimal_primitives} buckets={bucket_primitives}"


def _work_packet_cut_ok(row: dict[str, Any]) -> bool:
    packet_primitives = _primitive_set(_node_list(row, "portable_work_packets"))
    if not packet_primitives:
        return False
    selected_cut = _primitive_set(_selected_action_nodes(row))
    return packet_primitives.issubset(selected_cut)


def _work_packet_cut_observed(row: dict[str, Any]) -> str:
    return (
        f"packets={sorted(_primitive_set(_node_list(row, 'portable_work_packets')))} "
        f"selected={sorted(_primitive_set(_selected_action_nodes(row)))}"
    )


def _do_not_formalize_disjoint(row: dict[str, Any]) -> bool:
    excluded = set(_str_tuple(row.get("do_not_formalize_now", [])))
    selected_or_packet = _primitive_set(_selected_action_nodes(row)) | _primitive_set(
        _node_list(row, "portable_work_packets")
    )
    return not (excluded & selected_or_packet)


def _do_not_formalize_observed(row: dict[str, Any]) -> str:
    excluded = set(_str_tuple(row.get("do_not_formalize_now", [])))
    selected_or_packet = _primitive_set(_selected_action_nodes(row)) | _primitive_set(
        _node_list(row, "portable_work_packets")
    )
    return ",".join(sorted(excluded & selected_or_packet))


def _delta_nodes_connected(row: dict[str, Any]) -> bool:
    delta_primitives = _primitive_set(_minimal_nodes(row))
    if not delta_primitives:
        return True
    graph = row.get("and_or_plan", {})
    if not isinstance(graph, dict):
        return False
    nodes = [node for node in graph.get("nodes", []) if isinstance(node, dict)]
    edges = [edge for edge in graph.get("edges", []) if isinstance(edge, dict)]
    labels = {str(node.get("label", "")) for node in nodes}
    target_ids = {
        str(node.get("node_id", ""))
        for node in nodes
        if str(node.get("node_type", node.get("kind", ""))) == "target_theorem"
    }
    connected_labels = {
        str(node.get("label", ""))
        for node in nodes
        if _node_connected_to_target(str(node.get("node_id", "")), target_ids, edges)
    }
    return delta_primitives.issubset(labels) and delta_primitives.issubset(
        connected_labels
    )


def _delta_nodes_connected_observed(row: dict[str, Any]) -> str:
    delta_primitives = _primitive_set(_minimal_nodes(row))
    graph = row.get("and_or_plan", {})
    if not isinstance(graph, dict):
        return "missing and_or_plan"
    nodes = [node for node in graph.get("nodes", []) if isinstance(node, dict)]
    edges = [edge for edge in graph.get("edges", []) if isinstance(edge, dict)]
    labels = {str(node.get("label", "")) for node in nodes}
    target_ids = {
        str(node.get("node_id", ""))
        for node in nodes
        if str(node.get("node_type", node.get("kind", ""))) == "target_theorem"
    }
    connected_labels = {
        str(node.get("label", ""))
        for node in nodes
        if _node_connected_to_target(str(node.get("node_id", "")), target_ids, edges)
    }
    missing = sorted(delta_primitives - labels)
    disconnected = sorted(delta_primitives - connected_labels)
    return f"missing={missing} disconnected={disconnected}"


def _node_connected_to_target(
    node_id: str,
    target_ids: set[str],
    edges: list[dict[str, Any]],
) -> bool:
    for edge in edges:
        source = str(edge.get("source", edge.get("from", "")))
        target = str(edge.get("target", edge.get("to", "")))
        if node_id == source and target in target_ids:
            return True
        if node_id == target and source in target_ids:
            return True
    return False


def _selected_action_nodes(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [node for bucket in ACTION_BUCKETS for node in _node_list(row, bucket)]


def _minimal_nodes(row: dict[str, Any]) -> list[dict[str, Any]]:
    return _node_list(row, "minimal_additional_formalization_nodes")


def _node_list(row: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [node for node in row.get(key, []) if isinstance(node, dict)]


def _selected_primitives(row: dict[str, Any]) -> tuple[str, ...]:
    selected = _str_tuple(row.get("selected_primitives", []))
    if selected:
        return selected
    return tuple(sorted(_primitive_set(_selected_action_nodes(row))))


def _primitive_set(nodes: list[dict[str, Any]]) -> set[str]:
    return {
        str(node.get("primitive", "")).strip()
        for node in nodes
        if str(node.get("primitive", "")).strip()
    }


def _duplicate_primitives(nodes: list[dict[str, Any]]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for node in nodes:
        primitive = str(node.get("primitive", "")).strip()
        if not primitive:
            continue
        if primitive in seen:
            duplicates.add(primitive)
        seen.add(primitive)
    return tuple(sorted(duplicates))


def _row_sort_key(row: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        _int(row.get("goal_conditioned_cost")),
        -_int(row.get("route_efficiency_score")),
        str(row.get("display_name", "")),
        str(row.get("goal_plan_id", "")),
    )


def _target_key(row: dict[str, Any]) -> str:
    return (
        str(row.get("theorem_goal_id", "")).strip()
        or str(row.get("display_name", "")).strip()
        or str(row.get("route_id", "")).strip()
    )


def _row_label(row: dict[str, Any], idx: int) -> str:
    raw = str(row.get("goal_plan_id", "") or row.get("route_id", "") or idx)
    safe = "".join(ch if ch.isalnum() or ch in "_:-" else "_" for ch in raw)
    return safe[:100]


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),) if str(value) else ()


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _schema_property_errors(
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected_type = field_schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
        elif field_schema.get("minLength") and len(value) < int(
            field_schema["minLength"]
        ):
            errors.append(f"{field_name} must be nonempty")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be an integer")
        elif "minimum" in field_schema and value < int(field_schema["minimum"]):
            errors.append(f"{field_name} must be >= {field_schema['minimum']}")
    elif expected_type == "boolean" and not isinstance(value, bool):
        errors.append(f"{field_name} must be a boolean")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be an array")
        else:
            item_schema = field_schema.get("items", {})
            if isinstance(item_schema, dict) and item_schema.get("type") == "string":
                for idx, item in enumerate(value):
                    if not isinstance(item, str):
                        errors.append(f"{field_name}[{idx}] must be a string")
    elif expected_type == "object" and not isinstance(value, dict):
        errors.append(f"{field_name} must be an object")
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    enum_values = field_schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{field_name} must be one of {enum_values!r}")
    return errors


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _check(
    check_name: str,
    category: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
    errors: tuple[str, ...] = (),
) -> FormalizationGapPlannerMinimalDeltaAuditCheck:
    return FormalizationGapPlannerMinimalDeltaAuditCheck(
        schema_version=FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_SCHEMA_VERSION,
        check_id="formalization_gap_planner_minimal_delta_audit:"
        + stable_hash([check_name, expected, observed])[:20],
        check_name=check_name,
        category=category,
        expected=expected,
        observed=observed,
        ok=ok,
        severity=severity,
        errors=errors,
    )


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Minimal-Delta Audit",
        "",
        f"- Rows: {payload.get('n_plan_rows')}",
        f"- Checks: {payload.get('n_ok')}/{payload.get('n_checks')}",
        (
            f"- Decision row schema valid: "
            f"{payload.get('n_minimal_delta_decision_row_schema_valid')}/"
            f"{payload.get('n_minimal_delta_decision_rows')}"
        ),
        f"- Dominated route witnesses: {payload.get('n_dominated_route_witnesses')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Failed Checks",
        "",
    ]
    failed = [row for row in payload.get("checks", []) if isinstance(row, dict) and not row.get("ok")]
    if not failed:
        lines.append("- None")
    for check in failed:
        lines.append(
            f"- `{check.get('check_name')}` category={check.get('category')} "
            f"observed={check.get('observed')}"
        )
    return "\n".join(lines) + "\n"

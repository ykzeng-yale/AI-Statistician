from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_route_replan_handoff import (
    PROOF_EVIDENCE_BOUNDARY as HANDOFF_PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS as HANDOFF_PROOF_EVIDENCE_STATUS,
    QUALITY_CONTROL_FIELDS,
)
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
    export_formalization_gap_planner_standalone_plan,
    validate_standalone_input_payload,
)


FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_AUDIT_SCHEMA_VERSION = 1
ROUTE_REPLAN_HANDOFF_AUDIT_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-audit-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner route-replan handoff audit rows validate that a "
    "route-revision handoff is internally consistent and replayable as "
    "standalone planner input. They are audit evidence, not theorem proof "
    "evidence."
)
_REVISED_DAG_FIELDS = (
    "revised_informal_knowledge_dag_nodes",
    "revised_formal_realization_dag_nodes",
)


@dataclass(frozen=True)
class FormalizationGapPlannerRouteReplanHandoffAuditCheck:
    schema_version: int
    check_id: str
    check_name: str
    category: str
    expected: str
    observed: str
    ok: bool
    severity: str
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_route_replan_handoff(
    formalization_gap_planner_route_replan_handoff_dir: Path,
    out_dir: Path | None = None,
    *,
    run_roundtrip: bool = True,
) -> dict[str, object]:
    """Audit a route-replan handoff and optionally replay its standalone seed."""

    errors: list[str] = []
    handoff_dir = formalization_gap_planner_route_replan_handoff_dir
    manifest_path = handoff_dir / "formalization_gap_planner_route_replan_handoff_manifest.json"
    seed_path = handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json"
    seed_schema_path = handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
    jsonl_path = handoff_dir / "formalization_gap_planner_route_replan_handoff.jsonl"
    report_path = handoff_dir / "formalization_gap_planner_route_replan_handoff.md"
    manifest = _read_json(manifest_path, errors)
    seed = _read_json(seed_path, errors)
    checks: list[FormalizationGapPlannerRouteReplanHandoffAuditCheck] = []
    checks.extend(_manifest_checks(manifest_path, manifest))
    seed_schema = _read_json(seed_schema_path, errors)
    checks.extend(_seed_checks(seed_path, seed_schema_path, seed_schema, seed, manifest))
    checks.extend(_row_checks(manifest, seed))
    checks.extend(_artifact_checks(jsonl_path, report_path))
    roundtrip_payload: dict[str, object] = {}
    seed_routes = seed.get("routes", [])
    n_seed_routes = len(seed_routes) if isinstance(seed_routes, list) else 0
    roundtrip_dir = (
        out_dir / "formalization_gap_planner_route_replan_roundtrip_plan"
        if out_dir is not None
        else None
    )
    if run_roundtrip and not errors and seed_path.exists():
        try:
            roundtrip_payload = export_formalization_gap_planner_standalone_plan(
                seed_path,
                roundtrip_dir,
                max_routes=max(20, n_seed_routes),
            )
        except Exception as exc:  # pragma: no cover - defensive audit surface
            roundtrip_payload = {
                "all_ok": False,
                "errors": [f"{type(exc).__name__}: {exc}"],
            }
        checks.extend(_roundtrip_checks(roundtrip_payload, seed, roundtrip_dir))
    check_dicts = [asdict(check) for check in checks]
    check_row_schema = route_replan_handoff_audit_row_json_schema()
    row_schema_errors = [
        validate_route_replan_handoff_audit_row(row, check_row_schema)
        for row in check_dicts
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_route_replan_handoff_audit",
        "formalization_gap_planner_route_replan_handoff_dir": str(handoff_dir),
        "formalization_gap_planner_route_replan_handoff_manifest": str(manifest_path),
        "formalization_gap_planner_route_replan_standalone_seed": str(seed_path),
        "roundtrip_enabled": run_roundtrip,
        "roundtrip_plan_dir": str(roundtrip_dir or ""),
        "roundtrip_plan_manifest": str(
            roundtrip_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
            if roundtrip_dir is not None
            else ""
        ),
        "n_checks": len(checks),
        "n_ok": sum(1 for check in checks if check.ok),
        "n_failed": sum(1 for check in checks if not check.ok),
        "n_handoff_rows": len(_rows(manifest)),
        "n_seed_routes": n_seed_routes,
        "n_roundtrip_goal_plans": int(roundtrip_payload.get("n_goal_plans", 0) or 0),
        "n_roundtrip_route_alignment_edges": int(
            roundtrip_payload.get("n_route_alignment_edges", 0) or 0
        ),
        "n_roundtrip_standalone_input_traces": int(
            roundtrip_payload.get("n_standalone_input_traces", 0) or 0
        ),
        "n_roundtrip_standalone_input_traces_with_replan_metadata": int(
            roundtrip_payload.get(
                "n_standalone_input_traces_with_replan_metadata",
                0,
            )
            or 0
        ),
        "roundtrip_all_ok": bool(roundtrip_payload.get("all_ok", False)) if run_roundtrip else False,
        "n_row_schema_valid": n_row_schema_valid,
        "n_row_schema_invalid": len(row_schema_errors) - n_row_schema_valid,
        "row_schema_errors": row_schema_errors,
        "route_replan_handoff_audit_row_schema": check_row_schema,
        "all_ok": (
            not errors
            and bool(checks)
            and all(check.ok for check in checks)
            and len(row_schema_errors) == n_row_schema_valid
        ),
        "errors": errors,
        "checks": check_dicts,
        "roundtrip_summary": _roundtrip_summary(roundtrip_payload),
        "handoff_audit_fingerprint": stable_hash(check_dicts),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "handoff_proof_evidence_status": HANDOFF_PROOF_EVIDENCE_STATUS,
        "handoff_proof_evidence_boundary": HANDOFF_PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "roundtrip success means the seed is planner-replayable, not theorem-proved",
            "semantic adequacy still depends on source review and target-prover kernel replay",
            "audit checks cannot prove minimality of the revised route",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formalization_gap_planner_route_replan_handoff_audit_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
        ).write_text(json.dumps(check_row_schema, indent=2), encoding="utf-8")
        (out_dir / "formalization_gap_planner_route_replan_handoff_audit.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in check_dicts)
            + ("\n" if checks else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_route_replan_handoff_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def route_replan_handoff_audit_row_json_schema() -> dict[str, object]:
    required = [
        "schema_version",
        "check_id",
        "check_name",
        "category",
        "expected",
        "observed",
        "ok",
        "severity",
        "errors",
    ]
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": ROUTE_REPLAN_HANDOFF_AUDIT_ROW_SCHEMA_ID,
        "title": "Formalization gap planner route-replan handoff audit check row",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_AUDIT_SCHEMA_VERSION,
            },
            "check_id": {"type": "string", "minLength": 1},
            "check_name": {"type": "string", "minLength": 1},
            "category": {
                "type": "string",
                "enum": [
                    "alignment",
                    "artifacts",
                    "manifest",
                    "proof_boundary",
                    "provenance",
                    "roundtrip",
                    "rows",
                    "standalone_seed",
                ],
            },
            "expected": {"type": "string"},
            "observed": {"type": "string"},
            "ok": {"type": "boolean"},
            "severity": {"type": "string", "enum": ["error", "warning", "info"]},
            "errors": string_array,
        },
    }


def validate_route_replan_handoff_audit_row(
    row: dict[str, object],
    schema: dict[str, object] | None = None,
) -> list[str]:
    row_schema = schema or route_replan_handoff_audit_row_json_schema()
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
) -> list[FormalizationGapPlannerRouteReplanHandoffAuditCheck]:
    rows = _rows(manifest)
    return [
        _check(
            "handoff_manifest_exists",
            "manifest",
            "manifest file exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "handoff_component",
            "manifest",
            "formalization_gap_planner_route_replan_handoff",
            str(manifest.get("component_name", "")),
            manifest.get("component_name")
            == "formalization_gap_planner_route_replan_handoff",
        ),
        _check(
            "handoff_all_ok",
            "manifest",
            "all_ok true",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "handoff_rows_present",
            "manifest",
            "at least one handoff row",
            str(len(rows)),
            bool(rows),
        ),
        _check(
            "handoff_boundary",
            "proof_boundary",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")),
        ),
        _check(
            "handoff_proof_status",
            "proof_boundary",
            "not proof evidence status",
            str(manifest.get("proof_evidence_status", "")),
            "NOT_PROOF_EVIDENCE" in str(manifest.get("proof_evidence_status", "")),
        ),
        _check(
            "handoff_no_kernel_verified_claims",
            "proof_boundary",
            "no kernel-verified/proved claim",
            _proof_claim_observed(manifest),
            not _has_kernel_proof_claim(manifest),
        ),
        _check(
            "handoff_alignment_edges_present",
            "alignment",
            "all handoff rows preserve revised route alignment edges",
            str(
                sum(1 for row in rows if row.get("revised_route_alignment_edges"))
            )
            + f"/{len(rows)}",
            bool(rows)
            and all(bool(row.get("revised_route_alignment_edges")) for row in rows),
        ),
        _check(
            "handoff_no_unaligned_primitives",
            "alignment",
            "zero unaligned primitives",
            str(manifest.get("n_unaligned_primitives", "")),
            int(manifest.get("n_unaligned_primitives", 0) or 0) == 0
            and all(not row.get("unaligned_primitives") for row in rows),
        ),
    ]


def _seed_checks(
    seed_path: Path,
    seed_schema_path: Path,
    seed_schema: dict[str, Any],
    seed: dict[str, Any],
    manifest: dict[str, Any],
) -> list[FormalizationGapPlannerRouteReplanHandoffAuditCheck]:
    validation_errors = validate_standalone_input_payload(seed)
    seed_routes = seed.get("routes", [])
    expected_routes = int(manifest.get("n_standalone_seed_routes", 0) or 0)
    return [
        _check(
            "standalone_seed_exists",
            "standalone_seed",
            "seed file exists",
            str(seed_path.exists()),
            seed_path.exists(),
        ),
        _check(
            "standalone_seed_schema_file",
            "standalone_seed",
            "standalone seed schema file exists",
            str(seed_schema_path.exists()),
            seed_schema_path.exists(),
        ),
        _check(
            "standalone_seed_schema_id",
            "standalone_seed",
            FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
            str(seed_schema.get("$id", "")),
            seed_schema.get("$id") == FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_ID,
        ),
        _check(
            "standalone_seed_component",
            "standalone_seed",
            FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
            str(seed.get("component_name", "")),
            seed.get("component_name") == FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
        ),
        _check(
            "standalone_seed_schema_valid",
            "standalone_seed",
            "validate_standalone_input_payload has no errors",
            "; ".join(validation_errors),
            not validation_errors,
        ),
        _check(
            "standalone_seed_route_count",
            "standalone_seed",
            str(expected_routes),
            str(len(seed_routes) if isinstance(seed_routes, list) else 0),
            isinstance(seed_routes, list) and len(seed_routes) == expected_routes,
        ),
        _check(
            "standalone_seed_boundary",
            "proof_boundary",
            "not theorem proof evidence",
            str(seed.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence" in str(seed.get("proof_evidence_boundary", "")),
        ),
        _check(
            "standalone_seed_proof_status",
            "proof_boundary",
            "not proof evidence status",
            str(seed.get("proof_evidence_status", "")),
            "NOT_PROOF_EVIDENCE" in str(seed.get("proof_evidence_status", "")),
        ),
        _check(
            "standalone_seed_routes_match_ok_handoff_rows",
            "standalone_seed",
            "seed routes equal ok handoff rows",
            f"seed={len(seed_routes) if isinstance(seed_routes, list) else 0}; ok_rows={sum(1 for row in _rows(manifest) if row.get('ok'))}",
            isinstance(seed_routes, list)
            and len(seed_routes)
            == sum(1 for row in _rows(manifest) if row.get("ok")),
        ),
        _check(
            "standalone_seed_no_kernel_verified_claims",
            "proof_boundary",
            "no kernel-verified/proved claim",
            _proof_claim_observed(seed),
            not _has_kernel_proof_claim(seed),
        ),
    ]


def _row_checks(
    manifest: dict[str, Any],
    seed: dict[str, Any],
) -> list[FormalizationGapPlannerRouteReplanHandoffAuditCheck]:
    checks: list[FormalizationGapPlannerRouteReplanHandoffAuditCheck] = []
    seed_routes = {
        str(route.get("route_id", "")): route
        for route in seed.get("routes", [])
        if isinstance(route, dict)
    }
    for idx, row in enumerate(_rows(manifest)):
        row_id = str(row.get("route_replan_handoff_id", f"row:{idx}"))
        seed_route_id = str(row.get("standalone_route_id", ""))
        seed_route = seed_routes.get(seed_route_id, {})
        primitives = seed_route.get("primitives", []) if isinstance(seed_route, dict) else []
        checks.append(
            _check(
                f"row_{idx}_ok",
                "rows",
                "row ok true",
                f"{row_id}: {row.get('ok')}",
                bool(row.get("ok", False)),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_seed_route_present",
                "rows",
                seed_route_id,
                ",".join(sorted(seed_routes)),
                bool(seed_route_id) and seed_route_id in seed_routes,
            )
        )
        checks.append(
            _check(
                f"row_{idx}_seed_route_has_primitives",
                "rows",
                "seed route primitives nonempty",
                str(len(primitives) if isinstance(primitives, list) else 0),
                isinstance(primitives, list) and bool(primitives),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_replan_justified",
                "rows",
                "replan false or justified by revision/stability/residuals",
                _replan_observed(row),
                _replan_justified(row),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_revised_alignment_contract",
                "alignment",
                "revised selected primitives have preserved alignment edges",
                _handoff_alignment_observed(row),
                _handoff_alignment_ok(row),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_seed_route_alignment_metadata",
                "alignment",
                "seed route and replan metadata exactly preserve revised alignment edges",
                _seed_alignment_observed(row, seed_route),
                _seed_alignment_ok(row, seed_route),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_seed_route_revised_dags",
                "alignment",
                "seed route and replan metadata preserve revised informal and Lean DAG nodes",
                _seed_dag_observed(row, seed_route),
                _seed_dag_ok(row, seed_route),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_seed_route_provenance_metadata",
                "provenance",
                "seed route replan metadata preserves applied hooks, evidence ids, diagnostics, and residual goals",
                _seed_provenance_observed(row, seed_route),
                _seed_provenance_ok(row, seed_route),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_seed_route_source_snippets",
                "provenance",
                "seed route, replan metadata, and primitive rows preserve handoff source snippets",
                _seed_source_snippets_observed(row, seed_route),
                _seed_source_snippets_ok(row, seed_route),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_seed_route_quality_controls",
                "provenance",
                "seed route and replan metadata exactly preserve handoff quality controls",
                _seed_quality_controls_observed(row, seed_route),
                _seed_quality_controls_ok(row, seed_route),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_next_command",
                "rows",
                "standalone-plan command present",
                " ".join(str(item) for item in row.get("next_commands", [])),
                any(
                    "formalization-gap-planner-standalone-plan" in str(item)
                    for item in row.get("next_commands", [])
                ),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_proof_status",
                "proof_boundary",
                "row not proof evidence status",
                str(row.get("proof_evidence_status", "")),
                "NOT_PROOF_EVIDENCE" in str(row.get("proof_evidence_status", "")),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_seed_route_no_kernel_verified_claims",
                "proof_boundary",
                "seed route has no kernel-verified/proved claim",
                _proof_claim_observed(seed_route),
                not _has_kernel_proof_claim(seed_route),
            )
        )
    return checks


def _artifact_checks(
    jsonl_path: Path,
    report_path: Path,
) -> list[FormalizationGapPlannerRouteReplanHandoffAuditCheck]:
    return [
        _check(
            "handoff_jsonl_exists",
            "artifacts",
            "jsonl exists",
            str(jsonl_path.exists()),
            jsonl_path.exists(),
        ),
        _check(
            "handoff_report_exists",
            "artifacts",
            "markdown report exists",
            str(report_path.exists()),
            report_path.exists(),
        ),
    ]


def _roundtrip_checks(
    roundtrip_payload: dict[str, Any],
    seed: dict[str, Any],
    roundtrip_dir: Path | None,
) -> list[FormalizationGapPlannerRouteReplanHandoffAuditCheck]:
    seed_routes = seed.get("routes", [])
    expected_routes = len(seed_routes) if isinstance(seed_routes, list) else 0
    manifest_path = (
        roundtrip_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
        if roundtrip_dir is not None
        else None
    )
    return [
        _check(
            "roundtrip_all_ok",
            "roundtrip",
            "standalone planner roundtrip all_ok",
            str(roundtrip_payload.get("all_ok", "")),
            bool(roundtrip_payload.get("all_ok", False)),
        ),
        _check(
            "roundtrip_route_count",
            "roundtrip",
            str(expected_routes),
            str(roundtrip_payload.get("n_goal_plans", 0)),
            int(roundtrip_payload.get("n_goal_plans", 0) or 0) == expected_routes,
        ),
        _check(
            "roundtrip_alignment_edges",
            "roundtrip",
            "roundtrip regenerates at least one alignment edge per seed route",
            str(roundtrip_payload.get("n_route_alignment_edges", 0)),
            int(roundtrip_payload.get("n_route_alignment_edges", 0) or 0)
            >= expected_routes,
        ),
        _check(
            "roundtrip_alignment_contract",
            "roundtrip",
            "all roundtrip rows have selected-primitive alignment",
            str(_roundtrip_alignment_observed(roundtrip_payload)),
            _roundtrip_alignment_ok(roundtrip_payload),
        ),
        _check(
            "roundtrip_standalone_input_trace",
            "roundtrip",
            "roundtrip goal-plan rows preserve standalone seed trace metadata",
            _roundtrip_trace_observed(roundtrip_payload, seed),
            _roundtrip_trace_ok(roundtrip_payload, seed),
        ),
        _check(
            "roundtrip_manifest_written",
            "roundtrip",
            "roundtrip manifest exists when output directory is provided",
            str(manifest_path.exists() if manifest_path else False),
            manifest_path is None or manifest_path.exists(),
        ),
        _check(
            "roundtrip_boundary",
            "proof_boundary",
            "not theorem proof evidence",
            str(roundtrip_payload.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(roundtrip_payload.get("proof_evidence_boundary", "")),
        ),
    ]


def _replan_justified(row: dict[str, Any]) -> bool:
    if not bool(row.get("requires_replan", False)):
        return True
    return bool(
        row.get("revision_status") == "ROUTE_REVISION_APPLIED"
        or row.get("stability_decision") == "APPLY_ROUTE_REVISION_AND_REPLAN"
        or row.get("added_primitives")
        or row.get("added_delta_primitives")
        or row.get("residual_goals")
    )


def _replan_observed(row: dict[str, Any]) -> str:
    return (
        f"requires={row.get('requires_replan')} "
        f"revision={row.get('revision_status')} "
        f"stability={row.get('stability_decision')} "
        f"added={len(row.get('added_primitives', []))} "
        f"delta={len(row.get('added_delta_primitives', []))} "
        f"residual={len(row.get('residual_goals', []))}"
    )


def _roundtrip_summary(payload: dict[str, Any]) -> dict[str, object]:
    return {
        "component_name": payload.get("component_name", ""),
        "all_ok": payload.get("all_ok", False),
        "manifest_path": payload.get("manifest_path", ""),
        "n_goal_plans": payload.get("n_goal_plans", 0),
        "n_route_alignment_edges": payload.get("n_route_alignment_edges", 0),
        "n_standalone_input_traces": payload.get("n_standalone_input_traces", 0),
        "n_standalone_input_traces_with_replan_metadata": payload.get(
            "n_standalone_input_traces_with_replan_metadata",
            0,
        ),
        "n_portable_work_packets": payload.get("n_portable_work_packets", 0),
        "errors": payload.get("errors", []),
    }


def _roundtrip_alignment_ok(payload: dict[str, Any]) -> bool:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    if not rows:
        return False
    return all(_row_alignment_ok(row) for row in rows)


def _roundtrip_alignment_observed(payload: dict[str, Any]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    ok_rows = sum(1 for row in rows if _row_alignment_ok(row))
    return f"{ok_rows}/{len(rows)}"


def _roundtrip_trace_ok(payload: dict[str, Any], seed: dict[str, Any]) -> bool:
    rows = {
        str(row.get("route_id", "")): row
        for row in payload.get("rows", [])
        if isinstance(row, dict)
    }
    seed_routes = {
        str(route.get("route_id", "")): route
        for route in seed.get("routes", [])
        if isinstance(route, dict) and str(route.get("route_id", ""))
    }
    if not rows or not seed_routes:
        return False
    for route_id, seed_route in seed_routes.items():
        row = rows.get(route_id, {})
        trace = row.get("standalone_input_trace", {}) if isinstance(row, dict) else {}
        if not isinstance(trace, dict):
            return False
        if str(trace.get("source_route_id", "")) != route_id:
            return False
        metadata = seed_route.get("replan_metadata", {})
        if isinstance(metadata, dict) and metadata:
            if not bool(trace.get("has_replan_metadata", False)):
                return False
            if not _trace_metadata_fields_ok(trace, metadata):
                return False
            for field_name in _REVISED_DAG_FIELDS:
                if _object_hashes(trace.get(field_name, [])) != _object_hashes(
                    metadata.get(field_name, [])
                ):
                    return False
            if _object_hashes(
                trace.get("revised_route_alignment_edges", [])
            ) != _object_hashes(metadata.get("revised_route_alignment_edges", [])):
                return False
    return True


def _roundtrip_trace_observed(payload: dict[str, Any], seed: dict[str, Any]) -> str:
    rows = {
        str(row.get("route_id", "")): row
        for row in payload.get("rows", [])
        if isinstance(row, dict)
    }
    seed_routes = [
        route
        for route in seed.get("routes", [])
        if isinstance(route, dict) and str(route.get("route_id", ""))
    ]
    matched = 0
    with_metadata = 0
    for seed_route in seed_routes:
        route_id = str(seed_route.get("route_id", ""))
        row = rows.get(route_id, {})
        trace = row.get("standalone_input_trace", {}) if isinstance(row, dict) else {}
        if isinstance(trace, dict) and str(trace.get("source_route_id", "")) == route_id:
            matched += 1
        if isinstance(trace, dict) and trace.get("has_replan_metadata"):
            with_metadata += 1
    return (
        f"trace_routes={matched}/{len(seed_routes)} "
        f"trace_with_replan_metadata={with_metadata}"
    )


def _trace_metadata_fields_ok(
    trace: dict[str, Any],
    metadata: dict[str, Any],
) -> bool:
    for field_name in (
        "applied_proposal_ids",
        "applied_refinement_evidence_ids",
        "applied_hook_kinds",
        "resource_response_awaiting_request_ids",
        "resource_response_rejected_request_ids",
        "applied_prover_attempt_statuses",
        "applied_prover_diagnostic_signatures",
        "route_revision_reasons",
        "route_revision_summaries",
        "residual_goals",
        "source_refs",
        "alignment_edge_primitives",
    ):
        if _str_tuple(trace.get(field_name, [])) != _str_tuple(
            metadata.get(field_name, [])
        ):
            return False
    if _declaration_tuple(
        trace.get("formal_declaration_hits", trace.get("lean_declaration_hits", []))
    ) != _declaration_tuple(
        metadata.get(
            "formal_declaration_hits",
            metadata.get("lean_declaration_hits", []),
        )
    ):
        return False
    if _object_hashes(trace.get("applied_resource_response_traces", [])) != _object_hashes(
        metadata.get("applied_resource_response_traces", [])
    ):
        return False
    trace_metadata = trace.get("replan_metadata", {})
    if not isinstance(trace_metadata, dict):
        return False
    if _quality_controls_from_payload(
        trace_metadata.get("quality_controls", {})
    ) != _quality_controls_from_payload(metadata.get("quality_controls", {})):
        return False
    return True


def _handoff_alignment_ok(row: dict[str, Any]) -> bool:
    selected = set(_str_tuple(row.get("revised_selected_primitives", [])))
    aligned = _alignment_primitives(row.get("revised_route_alignment_edges", []))
    return bool(selected) and selected.issubset(aligned)


def _handoff_alignment_observed(row: dict[str, Any]) -> str:
    selected = set(_str_tuple(row.get("revised_selected_primitives", [])))
    aligned = _alignment_primitives(row.get("revised_route_alignment_edges", []))
    missing = sorted(selected - aligned)
    if missing:
        return "missing=" + ",".join(missing)
    return f"aligned={len(aligned)} selected={len(selected)}"


def _seed_alignment_ok(row: dict[str, Any], seed_route: dict[str, Any]) -> bool:
    metadata = (
        seed_route.get("replan_metadata", {}) if isinstance(seed_route, dict) else {}
    )
    if not isinstance(metadata, dict):
        return False
    if "revised_route_alignment_edges" not in row:
        return False
    if "revised_route_alignment_edges" not in metadata:
        return False
    if "revised_route_alignment_edges" not in seed_route:
        return False
    row_hashes = _object_hashes(row.get("revised_route_alignment_edges", []))
    return (
        bool(row_hashes)
        and _handoff_alignment_ok(row)
        and row_hashes
        == _object_hashes(metadata.get("revised_route_alignment_edges", []))
        == _object_hashes(seed_route.get("revised_route_alignment_edges", []))
    )


def _seed_alignment_observed(row: dict[str, Any], seed_route: dict[str, Any]) -> str:
    metadata = (
        seed_route.get("replan_metadata", {}) if isinstance(seed_route, dict) else {}
    )
    if not isinstance(metadata, dict):
        return "missing metadata"
    row_hashes = _object_hashes(row.get("revised_route_alignment_edges", []))
    metadata_hashes = _object_hashes(metadata.get("revised_route_alignment_edges", []))
    route_hashes = _object_hashes(seed_route.get("revised_route_alignment_edges", []))
    selected = set(_str_tuple(row.get("revised_selected_primitives", [])))
    aligned = _alignment_primitives(metadata.get("revised_route_alignment_edges", []))
    missing = sorted(selected - aligned)
    return (
        f"row_edges={len(row_hashes)} metadata_edges={len(metadata_hashes)} "
        f"route_edges={len(route_hashes)} missing_selected={','.join(missing)}"
    )


def _seed_dag_ok(row: dict[str, Any], seed_route: dict[str, Any]) -> bool:
    metadata = (
        seed_route.get("replan_metadata", {}) if isinstance(seed_route, dict) else {}
    )
    if not isinstance(metadata, dict):
        return False
    for field_name in _REVISED_DAG_FIELDS:
        if (
            field_name not in row
            or field_name not in metadata
            or field_name not in seed_route
        ):
            return False
        row_hashes = _object_hashes(row.get(field_name, []))
        if (
            row_hashes != _object_hashes(metadata.get(field_name, []))
            or row_hashes != _object_hashes(seed_route.get(field_name, []))
        ):
            return False
    return True


def _seed_dag_observed(row: dict[str, Any], seed_route: dict[str, Any]) -> str:
    metadata = (
        seed_route.get("replan_metadata", {}) if isinstance(seed_route, dict) else {}
    )
    if not isinstance(metadata, dict):
        return "missing metadata"
    parts = []
    for field_name in _REVISED_DAG_FIELDS:
        parts.append(
            f"{field_name}:row={len(_object_hashes(row.get(field_name, [])))}"
            f",metadata={len(_object_hashes(metadata.get(field_name, [])))}"
            f",route={len(_object_hashes(seed_route.get(field_name, [])))}"
        )
    return "; ".join(parts)


def _seed_provenance_ok(row: dict[str, Any], seed_route: dict[str, Any]) -> bool:
    metadata = (
        seed_route.get("replan_metadata", {}) if isinstance(seed_route, dict) else {}
    )
    if not isinstance(metadata, dict):
        return False
    for field_name in (
        "applied_proposal_ids",
        "applied_refinement_evidence_ids",
        "applied_hook_kinds",
        "resource_response_awaiting_request_ids",
        "resource_response_rejected_request_ids",
        "applied_prover_attempt_statuses",
        "applied_prover_diagnostic_signatures",
        "route_revision_reasons",
        "route_revision_summaries",
        "residual_goals",
        "source_refs",
    ):
        expected = _str_tuple(row.get(field_name, []))
        if expected and expected != _str_tuple(metadata.get(field_name, [])):
            return False
    row_hits = _declaration_tuple(
        row.get("formal_declaration_hits", row.get("lean_declaration_hits", []))
    )
    metadata_hits = _declaration_tuple(
        metadata.get(
            "formal_declaration_hits",
            metadata.get("lean_declaration_hits", []),
        )
    )
    if row_hits and not row_hits.issubset(metadata_hits):
        return False
    row_traces = _object_hashes(row.get("applied_resource_response_traces", []))
    metadata_traces = _object_hashes(
        metadata.get("applied_resource_response_traces", [])
    )
    return not row_traces or row_traces.issubset(metadata_traces)


def _seed_provenance_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = (
        seed_route.get("replan_metadata", {}) if isinstance(seed_route, dict) else {}
    )
    if not isinstance(metadata, dict):
        return "missing metadata"
    observed_parts = []
    for field_name in (
        "applied_hook_kinds",
        "applied_refinement_evidence_ids",
        "resource_response_awaiting_request_ids",
        "resource_response_rejected_request_ids",
        "applied_prover_diagnostic_signatures",
        "residual_goals",
    ):
        observed_parts.append(
            f"{field_name}={len(_str_tuple(metadata.get(field_name, [])))}"
        )
    observed_parts.append(
        "formal_declaration_hits="
        f"{len(_declaration_tuple(metadata.get('formal_declaration_hits', metadata.get('lean_declaration_hits', []))))}"
    )
    observed_parts.append(
        f"applied_resource_response_traces={len(_object_hashes(metadata.get('applied_resource_response_traces', [])))}"
    )
    return "; ".join(observed_parts)


def _seed_source_snippets_ok(row: dict[str, Any], seed_route: dict[str, Any]) -> bool:
    row_hashes = _object_hashes(row.get("source_snippets", []))
    if not row_hashes:
        return True
    metadata = (
        seed_route.get("replan_metadata", {}) if isinstance(seed_route, dict) else {}
    )
    if not isinstance(metadata, dict):
        return False
    route_hashes = _object_hashes(seed_route.get("source_snippets", []))
    metadata_hashes = _object_hashes(metadata.get("source_snippets", []))
    primitive_hashes = _object_hashes(
        tuple(
            snippet
            for primitive in seed_route.get("primitives", [])
            if isinstance(primitive, dict)
            for snippet in primitive.get("source_snippets", [])
            if isinstance(snippet, dict)
        )
    )
    return (
        row_hashes.issubset(route_hashes)
        and row_hashes.issubset(metadata_hashes)
        and row_hashes.issubset(primitive_hashes)
    )


def _seed_source_snippets_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    metadata = (
        seed_route.get("replan_metadata", {}) if isinstance(seed_route, dict) else {}
    )
    if not isinstance(metadata, dict):
        return "missing metadata"
    row_hashes = _object_hashes(row.get("source_snippets", []))
    route_hashes = _object_hashes(seed_route.get("source_snippets", []))
    metadata_hashes = _object_hashes(metadata.get("source_snippets", []))
    primitive_hashes = _object_hashes(
        tuple(
            snippet
            for primitive in seed_route.get("primitives", [])
            if isinstance(primitive, dict)
            for snippet in primitive.get("source_snippets", [])
            if isinstance(snippet, dict)
        )
    )
    return (
        f"row={len(row_hashes)} "
        f"route={len(row_hashes.intersection(route_hashes))}/{len(row_hashes)} "
        f"metadata={len(row_hashes.intersection(metadata_hashes))}/{len(row_hashes)} "
        f"primitive={len(row_hashes.intersection(primitive_hashes))}/{len(row_hashes)}"
    )


def _seed_quality_controls_ok(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> bool:
    row_controls = _quality_controls_from_payload(row.get("quality_controls", {}))
    if not row_controls:
        return True
    if not isinstance(seed_route, dict):
        return False
    metadata = seed_route.get("replan_metadata", {})
    if not isinstance(metadata, dict):
        return False
    return (
        row_controls
        == _quality_controls_from_payload(seed_route.get("quality_controls", {}))
        == _quality_controls_from_payload(metadata.get("quality_controls", {}))
    )


def _seed_quality_controls_observed(
    row: dict[str, Any],
    seed_route: dict[str, Any],
) -> str:
    if not isinstance(seed_route, dict):
        return "missing seed route"
    metadata = seed_route.get("replan_metadata", {})
    if not isinstance(metadata, dict):
        return "missing metadata"
    return (
        f"row={_quality_controls_summary(row.get('quality_controls', {}))} "
        f"route={_quality_controls_summary(seed_route.get('quality_controls', {}))} "
        f"metadata={_quality_controls_summary(metadata.get('quality_controls', {}))}"
    )


def _quality_controls_from_payload(value: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        return {}
    return {
        field_name: _str_tuple(value.get(field_name, []))
        for field_name in QUALITY_CONTROL_FIELDS
        if _str_tuple(value.get(field_name, []))
    }


def _quality_controls_summary(value: Any) -> str:
    controls = _quality_controls_from_payload(value)
    if not controls:
        return "none"
    return ",".join(
        f"{field_name}={len(controls.get(field_name, ()))}"
        for field_name in QUALITY_CONTROL_FIELDS
        if controls.get(field_name)
    )


def _declaration_tuple(values: Any) -> set[str]:
    declarations: set[str] = set()
    if not isinstance(values, (list, tuple, set)):
        return declarations
    for value in values:
        if not isinstance(value, dict):
            continue
        declaration = str(
            value.get("declaration", "")
            or value.get("declaration_name", "")
            or value.get("name", "")
        ).strip()
        if declaration:
            declarations.add(declaration)
    return declarations


def _row_alignment_ok(row: dict[str, Any]) -> bool:
    selected = set(_str_tuple(row.get("selected_primitives", [])))
    aligned = _alignment_primitives(row.get("route_alignment_edges", []))
    return bool(selected) and selected.issubset(aligned)


def _alignment_primitives(edges: Any) -> set[str]:
    return {
        str(edge.get("primitive", ""))
        for edge in edges
        if isinstance(edge, dict)
        and str(edge.get("kind", "")) == "aligned_to_formal_realization_candidate"
        and str(edge.get("source", ""))
        and str(edge.get("target", ""))
    }


def _object_hashes(values: Any) -> set[str]:
    if not isinstance(values, (list, tuple, set)):
        return set()
    return {stable_hash(value) for value in values if isinstance(value, dict)}


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        try:
            values = tuple(values)
        except TypeError:
            return tuple()
    return tuple(sorted(dict.fromkeys(str(item) for item in values if str(item))))


def _has_kernel_proof_claim(value: Any) -> bool:
    if isinstance(value, dict):
        for raw_key, item in value.items():
            key = str(raw_key).strip().lower()
            if key in {
                "kernel_verified",
                "kernel_checked",
                "kernel_proved",
                "theorem_proved",
                "proof_verified",
            } and _truthy_claim(item):
                return True
            if key == "proof_evidence_status" and str(item).strip().upper() and (
                "NOT_PROOF_EVIDENCE" not in str(item).strip().upper()
            ):
                return True
            if _has_kernel_proof_claim(item):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_has_kernel_proof_claim(item) for item in value)
    return False


def _truthy_claim(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    normalized = str(value).strip().lower()
    return normalized in {"true", "yes", "proved", "verified", "kernel_verified"}


def _proof_claim_observed(value: Any) -> str:
    return "kernel/proof claim present" if _has_kernel_proof_claim(value) else "none"


def _rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in manifest.get("rows", []) if isinstance(row, dict)]


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


def _check(
    check_name: str,
    category: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
) -> FormalizationGapPlannerRouteReplanHandoffAuditCheck:
    return FormalizationGapPlannerRouteReplanHandoffAuditCheck(
        schema_version=FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_AUDIT_SCHEMA_VERSION,
        check_id="formalization_gap_planner_route_replan_handoff_audit:"
        + stable_hash([check_name, category, expected])[:16],
        check_name=check_name,
        category=category,
        expected=expected,
        observed=observed,
        ok=ok,
        severity=severity,
        errors=() if ok else (f"expected {expected}; observed {observed}",),
    )


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
        if isinstance(item_schema, dict):
            item_type = item_schema.get("type")
            if item_type == "string":
                for index, item in enumerate(value):
                    if not isinstance(item, str):
                        errors.append(f"{field_name}[{index}] must be string")
            if item_type == "object":
                for index, item in enumerate(value):
                    if not isinstance(item, dict):
                        errors.append(f"{field_name}[{index}] must be object")
    return errors


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Route-Replan Handoff Audit",
        "",
        f"- Checks: {payload.get('n_ok')}/{payload.get('n_checks')}",
        f"- Audit row schema valid: {payload.get('n_row_schema_valid')}/{payload.get('n_checks')}",
        f"- Handoff rows: {payload.get('n_handoff_rows')}",
        f"- Seed routes: {payload.get('n_seed_routes')}",
        f"- Roundtrip plans: {payload.get('n_roundtrip_goal_plans')}",
        f"- Roundtrip OK: {payload.get('roundtrip_all_ok')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
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
            f"observed={check.get('observed')}"
        )
    return "\n".join(lines) + "\n"

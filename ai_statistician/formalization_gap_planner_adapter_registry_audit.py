from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_adapter_registry import (
    ADAPTER_REGISTRY_ROW_SCHEMA_ID,
    PROOF_EVIDENCE_BOUNDARY as REGISTRY_PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS as REGISTRY_PROOF_EVIDENCE_STATUS,
    adapter_registry_row_json_schema,
    validate_adapter_registry_row,
)


FORMALIZATION_GAP_PLANNER_ADAPTER_REGISTRY_AUDIT_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_ADAPTER_REGISTRY_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner adapter-registry audit rows validate frontier "
    "tool coverage, response-contract shape, portability, and proof-boundary "
    "discipline. They are not theorem proof evidence."
)
REQUIRED_ADAPTER_IDS = (
    "local_route_truth_benchmark_adapter",
    "local_literature_corpus",
    "paperclip_cli_mcp",
    "paperqa2_local_library",
    "openscholar_semantic_scholar",
    "paper2agent_formalization_mcp",
    "dependency_graph_route_decomposition",
    "local_formal_source_index",
    "local_target_formal_source_index",
    "local_lean_rag_dependency_graph",
    "loogle_leansearchclient",
    "leanexplore_mcp",
    "rocq_lsp_serapi",
    "isabelle_sledgehammer_afp",
    "agda_search_auto",
    "local_lake_lean",
    "lean_lsp_mcp",
    "leandojo_reprover",
    "agentic_prover_orchestration",
    "route_revision_overlay",
)
REQUIRED_COMPONENT_KINDS = (
    "offline_regression",
    "literature_discovery",
    "informal_route_decomposition",
    "formal_library_grounding",
    "proof_state_feedback",
    "route_revision",
)
REQUIRED_HOOK_KINDS = (
    "all_refinement_hooks",
    "literature_discovery",
    "formal_library_grounding",
    "proof_state_feedback",
    "route_revision",
)
REQUIRED_REUSE_TARGETS = ("lean4", "rocq", "isabelle", "agda")
REQUIRED_FIELDS_BY_EVIDENCE_KIND = {
    "all_refinement_response_contracts": (
        "refinement_item_id",
        "evidence_kind",
        "tool_name",
        "route_revision_recommended",
    ),
    "literature_route_evidence": ("source_refs", "route_evidence_nodes"),
    "formal_library_grounding": ("formal_declaration_hits", "coverage_updates"),
    "lean_library_grounding": ("lean_declaration_hits", "coverage_updates"),
    "prover_feedback": ("prover_diagnostics", "residual_goals"),
    "route_revision_proposal": (
        "route_revision_summary",
        "revised_formal_realization_dag_nodes",
    ),
}


@dataclass(frozen=True)
class FormalizationGapPlannerAdapterRegistryAuditCheck:
    schema_version: int
    check_id: str
    check_name: str
    category: str
    expected: str
    observed: str
    ok: bool
    severity: str
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_adapter_registry(
    formalization_gap_planner_adapter_registry_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Audit adapter-registry coverage for public reuse and frontier tools."""

    errors: list[str] = []
    registry_dir = formalization_gap_planner_adapter_registry_dir
    manifest_path = registry_dir / "formalization_gap_planner_adapter_registry_manifest.json"
    jsonl_path = registry_dir / "formalization_gap_planner_adapter_registry.jsonl"
    schema_path = registry_dir / "formalization_gap_planner_adapter_registry_row.schema.json"
    report_path = registry_dir / "formalization_gap_planner_adapter_registry.md"
    manifest = _read_json(manifest_path, errors)
    row_schema = _read_json(schema_path, errors)
    effective_row_schema = row_schema or adapter_registry_row_json_schema()
    rows = _rows(manifest)
    jsonl_rows, jsonl_errors = _read_jsonl_rows(jsonl_path)
    errors.extend(jsonl_errors)
    row_schema_errors = [
        validate_adapter_registry_row(row, effective_row_schema) for row in rows
    ]
    jsonl_row_schema_errors = [
        validate_adapter_registry_row(row, effective_row_schema) for row in jsonl_rows
    ]
    n_row_schema_valid = sum(1 for row_errors in row_schema_errors if not row_errors)
    n_jsonl_row_schema_valid = sum(
        1 for row_errors in jsonl_row_schema_errors if not row_errors
    )
    checks: list[FormalizationGapPlannerAdapterRegistryAuditCheck] = []
    checks.extend(_manifest_checks(manifest_path, manifest, rows))
    checks.extend(_coverage_checks(rows))
    checks.extend(
        _schema_checks(
            schema_path=schema_path,
            row_schema=row_schema,
            manifest=manifest,
            rows=rows,
            jsonl_rows=jsonl_rows,
            row_schema_errors=row_schema_errors,
            jsonl_row_schema_errors=jsonl_row_schema_errors,
        )
    )
    checks.extend(_row_contract_checks(rows))
    checks.extend(_artifact_checks(jsonl_path, schema_path, report_path))
    by_category = Counter(check.category for check in checks)
    by_component = Counter(str(row.get("component_kind", "")) for row in rows)
    by_status = Counter(str(row.get("readiness_status", "")) for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_ADAPTER_REGISTRY_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_adapter_registry_audit",
        "formalization_gap_planner_adapter_registry_dir": str(registry_dir),
        "formalization_gap_planner_adapter_registry_manifest": str(manifest_path),
        "n_checks": len(checks),
        "n_ok": sum(1 for check in checks if check.ok),
        "n_failed": sum(1 for check in checks if not check.ok),
        "n_registry_rows": len(rows),
        "n_registry_jsonl_rows": len(jsonl_rows),
        "n_adapter_row_schema_valid": n_row_schema_valid,
        "n_adapter_row_schema_invalid": len(row_schema_errors) - n_row_schema_valid,
        "n_adapter_jsonl_row_schema_valid": n_jsonl_row_schema_valid,
        "n_adapter_jsonl_row_schema_invalid": len(jsonl_row_schema_errors)
        - n_jsonl_row_schema_valid,
        "n_required_adapter_ids": len(REQUIRED_ADAPTER_IDS),
        "n_required_adapter_ids_present": len(
            set(REQUIRED_ADAPTER_IDS) & _adapter_ids(rows)
        ),
        "n_required_component_kinds_present": len(
            set(REQUIRED_COMPONENT_KINDS) & _component_kinds(rows)
        ),
        "n_required_hook_kinds_present": len(
            set(REQUIRED_HOOK_KINDS) & _hook_kinds(rows)
        ),
        "target_coverage_by_hook_kind": _target_coverage_by_hook_kind(rows),
        "target_specific_coverage_by_hook_kind": (
            _target_specific_coverage_by_hook_kind(rows)
        ),
        "n_ready_local_or_configured": int(
            manifest.get("n_ready_local_or_configured", 0) or 0
        ),
        "n_contract_only": int(manifest.get("n_contract_only", 0) or 0),
        "n_online_dependency": sum(1 for row in rows if row.get("online_dependency")),
        "n_mcp_or_cli_surfaces": sum(
            1
            for row in rows
            if "mcp" in str(row.get("adapter_surface", "")).lower()
            or "cli" in str(row.get("adapter_surface", "")).lower()
        ),
        "by_check_category": dict(sorted(by_category.items())),
        "by_component_kind": dict(sorted(by_component.items())),
        "by_readiness_status": dict(sorted(by_status.items())),
        "all_ok": not errors and bool(checks) and all(check.ok for check in checks),
        "errors": errors,
        "checks": [asdict(check) for check in checks],
        "adapter_registry_audit_fingerprint": stable_hash([asdict(check) for check in checks]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "adapter_registry_proof_evidence_status": REGISTRY_PROOF_EVIDENCE_STATUS,
        "adapter_registry_proof_evidence_boundary": REGISTRY_PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "adapter-registry audit validates readiness metadata and contracts only",
            "remote services can still fail despite local preflight status",
            "adapter outputs become proof evidence only after target-prover kernel replay",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_gap_planner_adapter_registry_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_adapter_registry_audit.jsonl").write_text(
            "\n".join(json.dumps(asdict(check), sort_keys=True) for check in checks)
            + ("\n" if checks else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_adapter_registry_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _manifest_checks(
    manifest_path: Path,
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[FormalizationGapPlannerAdapterRegistryAuditCheck]:
    return [
        _check(
            "adapter_registry_manifest_exists",
            "manifest",
            "manifest file exists",
            str(manifest_path.exists()),
            manifest_path.exists(),
        ),
        _check(
            "adapter_registry_component",
            "manifest",
            "formalization_gap_planner_adapter_registry",
            str(manifest.get("component_name", "")),
            manifest.get("component_name") == "formalization_gap_planner_adapter_registry",
        ),
        _check(
            "adapter_registry_all_ok",
            "manifest",
            "all_ok true",
            str(manifest.get("all_ok", "")),
            bool(manifest.get("all_ok", False)),
        ),
        _check(
            "adapter_registry_rows_present",
            "manifest",
            "at least required adapter count",
            str(len(rows)),
            len(rows) >= len(REQUIRED_ADAPTER_IDS),
        ),
        _check(
            "adapter_registry_boundary",
            "proof_boundary",
            "not theorem proof evidence",
            str(manifest.get("proof_evidence_boundary", ""))[:160],
            "not theorem proof evidence"
            in str(manifest.get("proof_evidence_boundary", "")),
        ),
        _check(
            "adapter_registry_proof_status",
            "proof_boundary",
            "not proof evidence status",
            str(manifest.get("proof_evidence_status", "")),
            "NOT_PROOF_EVIDENCE" in str(manifest.get("proof_evidence_status", "")),
        ),
    ]


def _coverage_checks(
    rows: list[dict[str, Any]],
) -> list[FormalizationGapPlannerAdapterRegistryAuditCheck]:
    adapter_ids = _adapter_ids(rows)
    component_kinds = _component_kinds(rows)
    hook_kinds = _hook_kinds(rows)
    target_coverage = _target_coverage_by_hook_kind(rows)
    target_specific_coverage = _target_specific_coverage_by_hook_kind(rows)
    return [
        _check(
            "required_adapter_ids",
            "coverage",
            ",".join(REQUIRED_ADAPTER_IDS),
            ",".join(sorted(adapter_ids)),
            set(REQUIRED_ADAPTER_IDS).issubset(adapter_ids),
        ),
        _check(
            "required_component_kinds",
            "coverage",
            ",".join(REQUIRED_COMPONENT_KINDS),
            ",".join(sorted(component_kinds)),
            set(REQUIRED_COMPONENT_KINDS).issubset(component_kinds),
        ),
        _check(
            "required_hook_kinds",
            "coverage",
            ",".join(REQUIRED_HOOK_KINDS),
            ",".join(sorted(hook_kinds)),
            set(REQUIRED_HOOK_KINDS).issubset(hook_kinds),
        ),
        _check(
            "ready_local_or_configured_floor",
            "readiness",
            "at least three built-in/configured adapters",
            str(
                sum(
                    1
                    for row in rows
                    if row.get("readiness_status") in {"READY_LOCAL", "READY_CONFIGURED"}
                )
            ),
            sum(
                1
                for row in rows
                if row.get("readiness_status") in {"READY_LOCAL", "READY_CONFIGURED"}
            )
            >= 3,
        ),
        _check(
            "frontier_online_or_mcp_surface",
            "coverage",
            "online or MCP/CLI adapters present",
            str(
                sum(
                    1
                    for row in rows
                    if row.get("online_dependency")
                    or "mcp" in str(row.get("adapter_surface", "")).lower()
                    or "cli" in str(row.get("adapter_surface", "")).lower()
                )
            ),
            any(
                row.get("online_dependency")
                or "mcp" in str(row.get("adapter_surface", "")).lower()
                or "cli" in str(row.get("adapter_surface", "")).lower()
                for row in rows
            ),
        ),
        _check(
            "required_reuse_targets_covered",
            "portability",
            ",".join(REQUIRED_REUSE_TARGETS),
            ",".join(sorted(_target_union(rows))),
            set(REQUIRED_REUSE_TARGETS).issubset(_target_union(rows)),
        ),
        _check(
            "formal_library_grounding_targets_covered",
            "portability",
            ",".join(REQUIRED_REUSE_TARGETS),
            ",".join(
                sorted(target_coverage.get("formal_library_grounding", ()))
            ),
            set(REQUIRED_REUSE_TARGETS).issubset(
                set(target_coverage.get("formal_library_grounding", ()))
            ),
        ),
        _check(
            "proof_state_feedback_targets_covered",
            "portability",
            ",".join(REQUIRED_REUSE_TARGETS),
            ",".join(sorted(target_coverage.get("proof_state_feedback", ()))),
            set(REQUIRED_REUSE_TARGETS).issubset(
                set(target_coverage.get("proof_state_feedback", ()))
            ),
        ),
        _check(
            "target_specific_proof_state_feedback_targets_covered",
            "portability",
            ",".join(REQUIRED_REUSE_TARGETS),
            ",".join(
                sorted(target_specific_coverage.get("proof_state_feedback", ()))
            ),
            set(REQUIRED_REUSE_TARGETS).issubset(
                set(target_specific_coverage.get("proof_state_feedback", ()))
            ),
        ),
    ]


def _row_contract_checks(
    rows: list[dict[str, Any]],
) -> list[FormalizationGapPlannerAdapterRegistryAuditCheck]:
    checks: list[FormalizationGapPlannerAdapterRegistryAuditCheck] = []
    for idx, row in enumerate(rows):
        adapter_id = str(row.get("adapter_id", f"row:{idx}"))
        fields = set(_str_tuple(row.get("output_contract_fields", [])))
        evidence_kind = str(row.get("evidence_kind", ""))
        required_fields = set(REQUIRED_FIELDS_BY_EVIDENCE_KIND.get(evidence_kind, ()))
        reuse_targets = set(_str_tuple(row.get("portable_to_prover_families", [])))
        checks.append(
            _check(
                f"row_{idx}_output_contract_fields",
                "row_contract",
                "output contract fields present",
                f"{adapter_id}: {','.join(sorted(fields))}",
                bool(fields),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_evidence_contract_fields",
                "row_contract",
                ",".join(sorted(required_fields)) or "known evidence kind",
                f"{adapter_id}: {','.join(sorted(fields))}",
                bool(required_fields) and required_fields.issubset(fields),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_portable_reuse_targets",
                "portability",
                "non-empty target-prover scope",
                f"{adapter_id}: {','.join(sorted(reuse_targets))}",
                bool(reuse_targets),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_lean_alias_target_scope",
                "portability",
                "lean_declaration_hits only appears on Lean-scoped adapters",
                f"{adapter_id}: targets={','.join(sorted(reuse_targets))}; fields={','.join(sorted(fields))}",
                "lean_declaration_hits" not in fields
                or reuse_targets.issubset({"lean4"}),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_response_boundary",
                "row_contract",
                "refinement evidence response boundary",
                str(row.get("response_contract_boundary", ""))[:160],
                "formalization_gap_planner_refinement_evidence"
                in str(row.get("response_contract_boundary", "")),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_proof_boundary",
                "proof_boundary",
                "not theorem proof evidence",
                str(row.get("proof_evidence_boundary", ""))[:160],
                "not theorem proof evidence" in str(row.get("proof_evidence_boundary", "")),
            )
        )
        checks.append(
            _check(
                f"row_{idx}_no_kernel_claim_field",
                "proof_boundary",
                "adapter output contract does not include kernel_verified",
                f"{adapter_id}: {','.join(sorted(fields))}",
                "kernel_verified" not in fields,
            )
        )
        if row.get("online_dependency") or row.get("contract_only"):
            checks.append(
                _check(
                    f"row_{idx}_frontier_resource_url",
                    "resources",
                    "frontier/online adapters have resource URLs",
                    f"{adapter_id}: {','.join(_str_tuple(row.get('resource_urls', [])))}",
                    bool(_str_tuple(row.get("resource_urls", []))),
                )
            )
    return checks


def _schema_checks(
    *,
    schema_path: Path,
    row_schema: dict[str, Any],
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
    jsonl_rows: list[dict[str, Any]],
    row_schema_errors: list[tuple[str, ...]],
    jsonl_row_schema_errors: list[tuple[str, ...]],
) -> list[FormalizationGapPlannerAdapterRegistryAuditCheck]:
    checks = [
        _check(
            "adapter_registry_row_schema_file",
            "schema",
            "row schema file exists",
            str(schema_path.exists()),
            schema_path.exists(),
        ),
        _check(
            "adapter_registry_row_schema_id",
            "schema",
            ADAPTER_REGISTRY_ROW_SCHEMA_ID,
            str(row_schema.get("$id", "")),
            row_schema.get("$id") == ADAPTER_REGISTRY_ROW_SCHEMA_ID,
        ),
        _check(
            "adapter_registry_manifest_row_schema_valid_count",
            "schema",
            "all manifest rows schema-valid",
            (
                f"{manifest.get('n_adapter_row_schema_valid', 0)}/"
                f"{manifest.get('n_adapters', 0)} invalid="
                f"{manifest.get('n_adapter_row_schema_invalid', 0)}"
            ),
            int(manifest.get("n_adapter_row_schema_valid", 0) or 0) == len(rows)
            and int(manifest.get("n_adapter_row_schema_invalid", 0) or 0) == 0,
        ),
        _check(
            "adapter_registry_jsonl_row_count",
            "schema",
            "jsonl rows match manifest rows",
            f"{len(jsonl_rows)}/{len(rows)}",
            len(jsonl_rows) == len(rows),
        ),
        _check(
            "adapter_registry_jsonl_row_schema_valid_count",
            "schema",
            "all jsonl rows schema-valid",
            (
                f"{sum(1 for row_errors in jsonl_row_schema_errors if not row_errors)}/"
                f"{len(jsonl_rows)}"
            ),
            bool(jsonl_rows)
            and all(not row_errors for row_errors in jsonl_row_schema_errors),
        ),
    ]
    for idx, row_errors in enumerate(row_schema_errors):
        adapter_id = (
            str(rows[idx].get("adapter_id", f"row:{idx}"))
            if idx < len(rows)
            else f"row:{idx}"
        )
        checks.append(
            _check(
                f"row_{idx}_adapter_registry_schema_valid",
                "schema",
                "row validates against adapter-registry schema",
                f"{adapter_id}: {'; '.join(row_errors[:3])}",
                not row_errors,
            )
        )
    return checks


def _artifact_checks(
    jsonl_path: Path,
    schema_path: Path,
    report_path: Path,
) -> list[FormalizationGapPlannerAdapterRegistryAuditCheck]:
    return [
        _check(
            "adapter_registry_jsonl_exists",
            "artifacts",
            "jsonl exists",
            str(jsonl_path.exists()),
            jsonl_path.exists(),
        ),
        _check(
            "adapter_registry_row_schema_exists",
            "artifacts",
            "row schema exists",
            str(schema_path.exists()),
            schema_path.exists(),
        ),
        _check(
            "adapter_registry_report_exists",
            "artifacts",
            "markdown report exists",
            str(report_path.exists()),
            report_path.exists(),
        ),
    ]


def _rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in manifest.get("rows", []) if isinstance(row, dict)]


def _adapter_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("adapter_id", "")) for row in rows if row.get("adapter_id")}


def _component_kinds(rows: list[dict[str, Any]]) -> set[str]:
    return {
        str(row.get("component_kind", ""))
        for row in rows
        if row.get("component_kind")
    }


def _hook_kinds(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("hook_kind", "")) for row in rows if row.get("hook_kind")}


def _target_union(rows: list[dict[str, Any]]) -> set[str]:
    targets: set[str] = set()
    for row in rows:
        targets.update(_str_tuple(row.get("portable_to_prover_families", [])))
    return targets


def _target_coverage_by_hook_kind(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    coverage: dict[str, set[str]] = {}
    for row in rows:
        hook_kind = str(row.get("hook_kind", "")).strip()
        if not hook_kind:
            continue
        coverage.setdefault(hook_kind, set()).update(
            _str_tuple(row.get("portable_to_prover_families", []))
        )
    return {
        hook_kind: sorted(targets)
        for hook_kind, targets in sorted(coverage.items())
    }


def _target_specific_coverage_by_hook_kind(
    rows: list[dict[str, Any]],
) -> dict[str, list[str]]:
    coverage: dict[str, set[str]] = {}
    for row in rows:
        hook_kind = str(row.get("hook_kind", "")).strip()
        targets = _str_tuple(row.get("portable_to_prover_families", []))
        if not hook_kind or len(targets) != 1:
            continue
        coverage.setdefault(hook_kind, set()).update(targets)
    return {
        hook_kind: sorted(targets)
        for hook_kind, targets in sorted(coverage.items())
    }


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


def _read_jsonl_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], [f"missing JSONL file: {path}"]
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            errors.append(
                f"failed to parse {path}:{line_no}: {type(exc).__name__}: {exc}"
            )
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"{path}:{line_no} row is not object")
    return rows, errors


def _check(
    check_name: str,
    category: str,
    expected: str,
    observed: str,
    ok: bool,
    *,
    severity: str = "error",
) -> FormalizationGapPlannerAdapterRegistryAuditCheck:
    return FormalizationGapPlannerAdapterRegistryAuditCheck(
        schema_version=FORMALIZATION_GAP_PLANNER_ADAPTER_REGISTRY_AUDIT_SCHEMA_VERSION,
        check_id="formalization_gap_planner_adapter_registry_audit:"
        + stable_hash([check_name, category, expected])[:16],
        check_name=check_name,
        category=category,
        expected=expected,
        observed=observed,
        ok=ok,
        severity=severity,
        errors=() if ok else (f"expected {expected}; observed {observed}",),
    )


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Adapter Registry Audit",
        "",
        f"- Checks: {payload.get('n_ok')}/{payload.get('n_checks')}",
        f"- Registry rows: {payload.get('n_registry_rows')}",
        f"- Required adapters present: {payload.get('n_required_adapter_ids_present')}/{payload.get('n_required_adapter_ids')}",
        f"- Ready local/configured: {payload.get('n_ready_local_or_configured')}",
        f"- MCP/CLI surfaces: {payload.get('n_mcp_or_cli_surfaces')}",
        f"- Adapter row schema valid: {payload.get('n_adapter_row_schema_valid')}/{payload.get('n_registry_rows')}",
        f"- Adapter JSONL row schema valid: {payload.get('n_adapter_jsonl_row_schema_valid')}/{payload.get('n_registry_jsonl_rows')}",
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
        check
        for check in payload.get("checks", [])
        if isinstance(check, dict) and not check.get("ok")
    ]
    if not failed:
        lines.append("- none")
    for check in failed:
        lines.append(
            f"- `{check.get('check_name')}` category={check.get('category')} "
            f"observed={check.get('observed')}"
        )
    return "\n".join(lines) + "\n"

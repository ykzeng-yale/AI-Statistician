from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_prover_adapter_contract import (
    PROVER_FAMILIES,
    QUALITY_CONTROL_FIELDS,
    export_formalization_gap_planner_prover_adapter_contract,
    prover_adapter_packet_json_schema,
    prover_adapter_response_validation_row_json_schema,
    validate_prover_adapter_packet_row,
    validate_prover_adapter_response_validation_row,
)
from .formalization_gap_planner_route_adoption_blockers import (
    ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS,
    ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING,
)
from .formalization_gap_planner_component_resource_registry import (
    PORTABLE_REUSE_TARGETS,
)


FORMALIZATION_GAP_PLANNER_CROSS_PROVER_MATRIX_AUDIT_SCHEMA_VERSION = 1
CROSS_PROVER_MATRIX_AUDIT_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-cross-prover-matrix-audit-row:1"
)
CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-cross-prover-target-summary:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_CROSS_PROVER_MATRIX_AUDIT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Cross-prover matrix audit rows validate that one portable plan can emit "
    "target-prover adapter packets for multiple proof-assistant ecosystems. "
    "They are not theorem proof evidence."
)
DEFAULT_REUSE_TARGETS = PORTABLE_REUSE_TARGETS


@dataclass(frozen=True)
class FormalizationGapPlannerCrossProverMatrixRow:
    schema_version: int
    matrix_row_id: str
    target_prover_family: str
    target_library_snapshot_ref: str
    contract_dir: str
    contract_manifest_path: str
    packet_jsonl_path: str
    response_validation_jsonl_path: str
    n_plan_rows: int
    n_packets: int
    n_packet_ok: int
    n_packet_schema_valid: int
    n_packets_schema_invalid: int
    n_packets_with_alignment: int
    n_packets_missing_alignment: int
    n_packets_with_standalone_input_trace: int
    n_packets_missing_standalone_input_trace: int
    n_packets_with_target_library_snapshot_trace: int
    n_packets_missing_target_library_snapshot_trace: int
    n_packets_target_library_snapshot_mismatch: int
    n_packets_with_replan_metadata_trace: int
    n_packets_with_residual_goal_contexts: int
    n_packet_residual_goal_contexts: int
    packet_residual_context_source_kinds: tuple[str, ...]
    n_packet_residual_contexts_with_source_refs: int
    n_packet_residual_contexts_with_formal_gap_boundary: int
    n_packets_with_quality_controls: int
    n_packet_quality_control_fields: int
    packet_quality_control_fields: tuple[str, ...]
    packet_quality_control_resource_contract_ids: tuple[str, ...]
    packet_quality_control_response_validation_signals: tuple[str, ...]
    packet_quality_control_stop_conditions: tuple[str, ...]
    by_packet_quality_control_field: dict[str, dict[str, object]]
    n_packets_with_llm_route_adoption_status: int
    n_packets_llm_route_adoption_ready: int
    n_packets_llm_route_adoption_pending_refinement: int
    n_packets_llm_route_adoption_rejected: int
    n_packets_llm_route_adoption_awaiting_response: int
    n_packet_llm_route_adoption_blockers: int
    n_packet_llm_route_adoption_pending_quality_control_blockers: int
    n_packet_llm_route_adoption_pending_source_grounding_blockers: int
    by_packet_llm_route_adoption_status: dict[str, int]
    n_packets_with_formal_attempt_dependency: int
    n_packets_formal_attempt_initial_ready: int
    n_packets_formal_attempt_waiting: int
    n_packets_formal_attempt_missing_prerequisites: int
    by_packet_formal_attempt_dependency_status: dict[str, int]
    n_response_present: int
    n_awaiting_adapter_mapping: int
    n_response_contract_ok: int
    n_response_minimal_delta_action_witnesses_required: int
    n_response_minimal_delta_action_witnesses_acknowledged: int
    n_response_minimal_delta_action_witnesses_unacknowledged: int
    n_response_addressed_minimal_delta_action_witnesses: int
    n_unmatched_adapter_responses: int
    n_rejected: int
    n_kernel_verified_claims_rejected: int
    packet_fingerprint: str
    response_validation_fingerprint: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def audit_formalization_gap_planner_cross_prover_matrix(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    out_dir: Path | None = None,
    *,
    target_prover_families: tuple[str, ...] = DEFAULT_REUSE_TARGETS,
    library_snapshot_ref_prefix: str = "cross_prover_matrix",
    max_packets: int = 0,
) -> dict[str, object]:
    """Export prover-adapter contracts for every requested reuse target."""

    errors: list[str] = []
    out_root = out_dir or goal_conditioned_minimal_formalization_plan_dir
    target_families = _target_families(target_prover_families, errors)
    rows: list[FormalizationGapPlannerCrossProverMatrixRow] = []
    contract_payloads: list[dict[str, Any]] = []
    for target_family in target_families:
        contract_dir = out_root / "target_contracts" / target_family
        snapshot_ref = f"{library_snapshot_ref_prefix}:{target_family}"
        contract_payload = export_formalization_gap_planner_prover_adapter_contract(
            goal_conditioned_minimal_formalization_plan_dir,
            contract_dir if out_dir is not None else None,
            target_prover_family=target_family,
            library_snapshot_ref=snapshot_ref,
            max_packets=max_packets,
        )
        contract_payloads.append(contract_payload)
        rows.append(_matrix_row(target_family, snapshot_ref, contract_dir, contract_payload))
    packet_rows = [
        {
            "target_prover_family": row.target_prover_family,
            **packet,
        }
        for payload in contract_payloads
        for packet in payload.get("packets", [])
        if isinstance(packet, dict)
        for row in rows
        if row.target_prover_family == payload.get("target_prover_family")
    ]
    validation_rows = [
        {
            "target_prover_family": row.target_prover_family,
            **validation,
        }
        for payload in contract_payloads
        for validation in payload.get("response_validation_rows", [])
        if isinstance(validation, dict)
        for row in rows
        if row.target_prover_family == payload.get("target_prover_family")
    ]
    packet_counts = {row.n_packets for row in rows}
    packet_alignment_counts = {row.n_packets_with_alignment for row in rows}
    packet_trace_counts = {row.n_packets_with_standalone_input_trace for row in rows}
    packet_target_snapshot_counts = {
        row.n_packets_with_target_library_snapshot_trace for row in rows
    }
    packet_quality_control_counts = {
        row.n_packets_with_quality_controls for row in rows
    }
    packet_residual_context_counts = {
        row.n_packets_with_residual_goal_contexts for row in rows
    }
    route_adoption_status_counts = Counter(
        status
        for row in rows
        for status, count in row.by_packet_llm_route_adoption_status.items()
        for _ in range(count)
    )
    formal_attempt_dependency_status_counts = Counter(
        status
        for row in rows
        for status, count in row.by_packet_formal_attempt_dependency_status.items()
        for _ in range(count)
    )
    matrix_row_dicts = [asdict(row) for row in rows]
    quality_control_field_summary = _sum_quality_control_field_summary(
        matrix_row_dicts
    )
    matrix_row_schema = cross_prover_matrix_audit_row_json_schema()
    packet_row_schema = prover_adapter_packet_json_schema()
    response_validation_row_schema = (
        prover_adapter_response_validation_row_json_schema()
    )
    target_summary = _target_summary_payload(
        rows=rows,
        packet_rows=packet_rows,
        response_validation_rows=validation_rows,
    )
    target_summary_schema = cross_prover_target_summary_json_schema()
    target_summary_contract_errors = validate_cross_prover_target_summary_payload(
        target_summary,
        target_summary_schema,
    )
    matrix_row_schema_errors = [
        validate_cross_prover_matrix_audit_row(row, matrix_row_schema)
        for row in matrix_row_dicts
    ]
    packet_row_schema_errors = [
        validate_prover_adapter_packet_row(row, packet_row_schema)
        for row in packet_rows
    ]
    response_validation_row_schema_errors = [
        validate_prover_adapter_response_validation_row(
            row,
            response_validation_row_schema,
        )
        for row in validation_rows
    ]
    n_matrix_row_schema_valid = sum(
        1 for row_errors in matrix_row_schema_errors if not row_errors
    )
    n_packet_row_schema_valid = sum(
        1 for row_errors in packet_row_schema_errors if not row_errors
    )
    n_response_validation_row_schema_valid = sum(
        1 for row_errors in response_validation_row_schema_errors if not row_errors
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_CROSS_PROVER_MATRIX_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_cross_prover_matrix_audit",
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "target_prover_families": target_families,
        "library_snapshot_ref_prefix": library_snapshot_ref_prefix,
        "max_packets": max_packets,
        "n_targets": len(rows),
        "n_targets_ok": sum(1 for row in rows if row.ok),
        "n_targets_failed": sum(1 for row in rows if not row.ok),
        "n_matrix_row_schema_valid": n_matrix_row_schema_valid,
        "n_matrix_row_schema_invalid": len(matrix_row_schema_errors)
        - n_matrix_row_schema_valid,
        "n_total_packets": sum(row.n_packets for row in rows),
        "n_total_packet_ok": sum(row.n_packet_ok for row in rows),
        "n_total_packet_schema_valid": sum(
            row.n_packet_schema_valid for row in rows
        ),
        "n_total_packets_schema_invalid": sum(
            row.n_packets_schema_invalid for row in rows
        ),
        "n_packet_row_schema_valid": n_packet_row_schema_valid,
        "n_packet_row_schema_invalid": len(packet_row_schema_errors)
        - n_packet_row_schema_valid,
        "n_response_validation_row_schema_valid": n_response_validation_row_schema_valid,
        "n_response_validation_row_schema_invalid": len(
            response_validation_row_schema_errors
        )
        - n_response_validation_row_schema_valid,
        "n_target_summary_contract_errors": len(target_summary_contract_errors),
        "n_total_packets_with_alignment": sum(
            row.n_packets_with_alignment for row in rows
        ),
        "n_total_packets_missing_alignment": sum(
            row.n_packets_missing_alignment for row in rows
        ),
        "n_total_packets_with_standalone_input_trace": sum(
            row.n_packets_with_standalone_input_trace for row in rows
        ),
        "n_total_packets_missing_standalone_input_trace": sum(
            row.n_packets_missing_standalone_input_trace for row in rows
        ),
        "n_total_packets_with_target_library_snapshot_trace": sum(
            row.n_packets_with_target_library_snapshot_trace for row in rows
        ),
        "n_total_packets_missing_target_library_snapshot_trace": sum(
            row.n_packets_missing_target_library_snapshot_trace for row in rows
        ),
        "n_total_packets_target_library_snapshot_mismatch": sum(
            row.n_packets_target_library_snapshot_mismatch for row in rows
        ),
        "n_total_packets_with_replan_metadata_trace": sum(
            row.n_packets_with_replan_metadata_trace for row in rows
        ),
        "n_total_packets_with_residual_goal_contexts": sum(
            row.n_packets_with_residual_goal_contexts for row in rows
        ),
        "n_total_packet_residual_goal_contexts": sum(
            row.n_packet_residual_goal_contexts for row in rows
        ),
        "packet_residual_context_source_kinds": (
            _matrix_residual_context_source_kinds(rows)
        ),
        "n_total_packet_residual_contexts_with_source_refs": sum(
            row.n_packet_residual_contexts_with_source_refs for row in rows
        ),
        "n_total_packet_residual_contexts_with_formal_gap_boundary": sum(
            row.n_packet_residual_contexts_with_formal_gap_boundary for row in rows
        ),
        "n_total_packets_with_quality_controls": sum(
            row.n_packets_with_quality_controls for row in rows
        ),
        "n_total_packet_quality_control_fields": sum(
            row.n_packet_quality_control_fields for row in rows
        ),
        "packet_quality_control_fields": _matrix_quality_control_fields(rows),
        "packet_quality_control_resource_contract_ids": (
            _matrix_quality_control_values(
                rows,
                "packet_quality_control_resource_contract_ids",
            )
        ),
        "packet_quality_control_response_validation_signals": (
            _matrix_quality_control_values(
                rows,
                "packet_quality_control_response_validation_signals",
            )
        ),
        "packet_quality_control_stop_conditions": (
            _matrix_quality_control_values(
                rows,
                "packet_quality_control_stop_conditions",
            )
        ),
        "by_total_packet_quality_control_field": quality_control_field_summary,
        "n_total_packets_with_llm_route_adoption_status": sum(
            row.n_packets_with_llm_route_adoption_status for row in rows
        ),
        "n_total_packets_llm_route_adoption_ready": sum(
            row.n_packets_llm_route_adoption_ready for row in rows
        ),
        "n_total_packets_llm_route_adoption_pending_refinement": sum(
            row.n_packets_llm_route_adoption_pending_refinement for row in rows
        ),
        "n_total_packets_llm_route_adoption_rejected": sum(
            row.n_packets_llm_route_adoption_rejected for row in rows
        ),
        "n_total_packets_llm_route_adoption_awaiting_response": sum(
            row.n_packets_llm_route_adoption_awaiting_response for row in rows
        ),
        "n_total_packet_llm_route_adoption_blockers": sum(
            row.n_packet_llm_route_adoption_blockers for row in rows
        ),
        "n_total_packet_llm_route_adoption_pending_quality_control_blockers": sum(
            row.n_packet_llm_route_adoption_pending_quality_control_blockers
            for row in rows
        ),
        "n_total_packet_llm_route_adoption_pending_source_grounding_blockers": sum(
            row.n_packet_llm_route_adoption_pending_source_grounding_blockers
            for row in rows
        ),
        "by_total_packet_llm_route_adoption_status": dict(
            sorted(route_adoption_status_counts.items())
        ),
        "n_total_packets_with_formal_attempt_dependency": sum(
            row.n_packets_with_formal_attempt_dependency for row in rows
        ),
        "n_total_packets_formal_attempt_initial_ready": sum(
            row.n_packets_formal_attempt_initial_ready for row in rows
        ),
        "n_total_packets_formal_attempt_waiting": sum(
            row.n_packets_formal_attempt_waiting for row in rows
        ),
        "n_total_packets_formal_attempt_missing_prerequisites": sum(
            row.n_packets_formal_attempt_missing_prerequisites for row in rows
        ),
        "by_total_packet_formal_attempt_dependency_status": dict(
            sorted(formal_attempt_dependency_status_counts.items())
        ),
        "n_response_present": sum(row.n_response_present for row in rows),
        "n_awaiting_adapter_mapping": sum(
            row.n_awaiting_adapter_mapping for row in rows
        ),
        "n_response_contract_ok": sum(row.n_response_contract_ok for row in rows),
        "n_response_minimal_delta_action_witnesses_required": sum(
            row.n_response_minimal_delta_action_witnesses_required
            for row in rows
        ),
        "n_response_minimal_delta_action_witnesses_acknowledged": sum(
            row.n_response_minimal_delta_action_witnesses_acknowledged
            for row in rows
        ),
        "n_response_minimal_delta_action_witnesses_unacknowledged": sum(
            row.n_response_minimal_delta_action_witnesses_unacknowledged
            for row in rows
        ),
        "n_response_addressed_minimal_delta_action_witnesses": sum(
            row.n_response_addressed_minimal_delta_action_witnesses
            for row in rows
        ),
        "n_unmatched_adapter_responses": sum(
            row.n_unmatched_adapter_responses for row in rows
        ),
        "n_rejected": sum(row.n_rejected for row in rows),
        "n_kernel_verified_claims_rejected": sum(
            row.n_kernel_verified_claims_rejected for row in rows
        ),
        "n_distinct_packet_counts": len(packet_counts),
        "n_distinct_alignment_packet_counts": len(packet_alignment_counts),
        "n_distinct_standalone_input_trace_packet_counts": len(packet_trace_counts),
        "n_distinct_target_library_snapshot_trace_packet_counts": len(
            packet_target_snapshot_counts
        ),
        "n_distinct_quality_control_packet_counts": len(
            packet_quality_control_counts
        ),
        "n_distinct_residual_context_packet_counts": len(
            packet_residual_context_counts
        ),
        "packet_count_consistent": len(packet_counts) == 1 if rows else False,
        "alignment_packet_count_consistent": (
            len(packet_alignment_counts) == 1 if rows else False
        ),
        "standalone_input_trace_packet_count_consistent": (
            len(packet_trace_counts) == 1 if rows else False
        ),
        "target_library_snapshot_trace_packet_count_consistent": (
            len(packet_target_snapshot_counts) == 1 if rows else False
        ),
        "quality_control_packet_count_consistent": (
            len(packet_quality_control_counts) == 1 if rows else False
        ),
        "residual_context_packet_count_consistent": (
            len(packet_residual_context_counts) == 1 if rows else False
        ),
        "matrix_row_schema": matrix_row_schema,
        "cross_prover_target_summary_schema": target_summary_schema,
        "prover_adapter_packet_schema": packet_row_schema,
        "prover_adapter_response_validation_row_schema": (
            response_validation_row_schema
        ),
        "matrix_rows": matrix_row_dicts,
        "target_summary": target_summary,
        "packet_rows": packet_rows,
        "response_validation_rows": validation_rows,
        "all_ok": (
            not errors
            and bool(rows)
            and all(row.ok for row in rows)
            and len(matrix_row_schema_errors) == n_matrix_row_schema_valid
            and len(packet_row_schema_errors) == n_packet_row_schema_valid
            and len(response_validation_row_schema_errors)
            == n_response_validation_row_schema_valid
            and not target_summary_contract_errors
            and len(packet_counts) == 1
            and len(packet_alignment_counts) == 1
            and len(packet_trace_counts) == 1
            and len(packet_target_snapshot_counts) == 1
            and len(packet_quality_control_counts) == 1
            and len(packet_residual_context_counts) == 1
            and sum(row.n_packets_schema_invalid for row in rows) == 0
            and sum(row.n_packets_missing_alignment for row in rows) == 0
            and sum(row.n_packets_missing_standalone_input_trace for row in rows) == 0
            and sum(row.n_packets_missing_target_library_snapshot_trace for row in rows)
            == 0
            and sum(row.n_packets_target_library_snapshot_mismatch for row in rows)
            == 0
            and sum(row.n_unmatched_adapter_responses for row in rows) == 0
            and sum(row.n_rejected for row in rows) == 0
            and sum(row.n_kernel_verified_claims_rejected for row in rows) == 0
        ),
        "errors": errors,
        "matrix_fingerprint": stable_hash([asdict(row) for row in rows]),
        "packet_matrix_fingerprint": stable_hash(packet_rows),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "matrix rows validate portable packet export, not translated theorem correctness",
            "awaiting adapter mappings are acceptable until a target-prover adapter responds",
            "kernel proof status belongs to a separate replay/calibration gate in each prover",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = (
            out_dir / "formalization_gap_planner_cross_prover_matrix_audit_manifest.json"
        )
        matrix_jsonl_path = (
            out_dir / "formalization_gap_planner_cross_prover_matrix_audit.jsonl"
        )
        target_summary_path = (
            out_dir / "formalization_gap_planner_cross_prover_target_summary.json"
        )
        packets_path = out_dir / "formalization_gap_planner_cross_prover_packets.jsonl"
        validations_path = (
            out_dir
            / "formalization_gap_planner_cross_prover_response_validation.jsonl"
        )
        matrix_row_schema_path = (
            out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
        )
        target_summary_schema_path = (
            out_dir
            / "formalization_gap_planner_cross_prover_target_summary.schema.json"
        )
        packet_schema_path = (
            out_dir / "formalization_gap_planner_prover_adapter_packet.schema.json"
        )
        response_validation_row_schema_path = (
            out_dir
            / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
        )
        report_path = out_dir / "formalization_gap_planner_cross_prover_matrix_audit.md"
        payload["manifest_path"] = str(manifest_path)
        payload["matrix_jsonl_path"] = str(matrix_jsonl_path)
        payload["target_summary_path"] = str(target_summary_path)
        payload["packet_jsonl_path"] = str(packets_path)
        payload["response_validation_jsonl_path"] = str(validations_path)
        payload["matrix_row_schema_path"] = str(matrix_row_schema_path)
        payload["target_summary_schema_path"] = str(target_summary_schema_path)
        payload["packet_schema_path"] = str(packet_schema_path)
        payload["response_validation_row_schema_path"] = str(
            response_validation_row_schema_path
        )
        payload["report_path"] = str(report_path)
        manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        matrix_jsonl_path.write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        target_summary_path.write_text(
            json.dumps(target_summary, indent=2, default=str),
            encoding="utf-8",
        )
        packets_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in packet_rows)
            + ("\n" if packet_rows else ""),
            encoding="utf-8",
        )
        validations_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in validation_rows)
            + ("\n" if validation_rows else ""),
            encoding="utf-8",
        )
        matrix_row_schema_path.write_text(
            json.dumps(matrix_row_schema, indent=2),
            encoding="utf-8",
        )
        target_summary_schema_path.write_text(
            json.dumps(target_summary_schema, indent=2),
            encoding="utf-8",
        )
        packet_schema_path.write_text(
            json.dumps(packet_row_schema, indent=2),
            encoding="utf-8",
        )
        response_validation_row_schema_path.write_text(
            json.dumps(response_validation_row_schema, indent=2),
            encoding="utf-8",
        )
        report_path.write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def cross_prover_target_summary_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
        "title": "Formalization Gap Planner Cross-Prover Target Summary",
        "description": (
            "Bundle-portable summary of target-prover packet availability. "
            "It tells downstream prover teams how to filter aggregate packet "
            "and response-validation files without using the original run path."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "schema_id",
            "component_name",
            "target_rows",
            "n_target_rows",
            "n_targets_ok",
            "n_total_packets",
            "n_total_packets_with_alignment",
            "n_total_packets_with_standalone_input_trace",
            "n_total_packets_missing_standalone_input_trace",
            "n_total_packets_with_target_library_snapshot_trace",
            "n_total_packets_missing_target_library_snapshot_trace",
            "n_total_packets_target_library_snapshot_mismatch",
            "n_total_packets_with_replan_metadata_trace",
            "n_total_packets_with_residual_goal_contexts",
            "n_total_packet_residual_goal_contexts",
            "packet_residual_context_source_kinds",
            "n_total_packet_residual_contexts_with_source_refs",
            "n_total_packet_residual_contexts_with_formal_gap_boundary",
            "n_total_packets_with_quality_controls",
            "n_total_packet_quality_control_fields",
            "packet_quality_control_fields",
            "packet_quality_control_resource_contract_ids",
            "packet_quality_control_response_validation_signals",
            "packet_quality_control_stop_conditions",
            "by_total_packet_quality_control_field",
            "n_total_packets_with_llm_route_adoption_status",
            "n_total_packets_llm_route_adoption_ready",
            "n_total_packets_llm_route_adoption_pending_refinement",
            "n_total_packets_llm_route_adoption_rejected",
            "n_total_packets_llm_route_adoption_awaiting_response",
            "n_total_packet_llm_route_adoption_blockers",
            "n_total_packet_llm_route_adoption_pending_quality_control_blockers",
            "n_total_packet_llm_route_adoption_pending_source_grounding_blockers",
            "by_total_packet_llm_route_adoption_status",
            "n_total_packets_with_formal_attempt_dependency",
            "n_total_packets_formal_attempt_initial_ready",
            "n_total_packets_formal_attempt_waiting",
            "n_total_packets_formal_attempt_missing_prerequisites",
            "by_total_packet_formal_attempt_dependency_status",
            "n_total_response_minimal_delta_action_witnesses_required",
            "n_total_response_minimal_delta_action_witnesses_acknowledged",
            "n_total_response_minimal_delta_action_witnesses_unacknowledged",
            "n_total_response_addressed_minimal_delta_action_witnesses",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "all_ok",
            "errors",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_CROSS_PROVER_MATRIX_AUDIT_SCHEMA_VERSION,
            },
            "schema_id": {"const": CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID},
            "component_name": {
                "const": "formalization_gap_planner_cross_prover_target_summary"
            },
            "n_target_rows": {"type": "integer"},
            "n_targets_ok": {"type": "integer"},
            "n_total_packets": {"type": "integer"},
            "n_total_packets_with_alignment": {"type": "integer"},
            "n_total_packets_with_standalone_input_trace": {"type": "integer"},
            "n_total_packets_missing_standalone_input_trace": {"type": "integer"},
            "n_total_packets_with_target_library_snapshot_trace": {"type": "integer"},
            "n_total_packets_missing_target_library_snapshot_trace": {"type": "integer"},
            "n_total_packets_target_library_snapshot_mismatch": {"type": "integer"},
            "n_total_packets_with_replan_metadata_trace": {"type": "integer"},
            "n_total_packets_with_residual_goal_contexts": {"type": "integer"},
            "n_total_packet_residual_goal_contexts": {"type": "integer"},
            "packet_residual_context_source_kinds": string_array,
            "n_total_packet_residual_contexts_with_source_refs": {
                "type": "integer"
            },
            "n_total_packet_residual_contexts_with_formal_gap_boundary": {
                "type": "integer"
            },
            "n_total_packets_with_quality_controls": {"type": "integer"},
            "n_total_packet_quality_control_fields": {"type": "integer"},
            "packet_quality_control_fields": string_array,
            "packet_quality_control_resource_contract_ids": string_array,
            "packet_quality_control_response_validation_signals": string_array,
            "packet_quality_control_stop_conditions": string_array,
            "by_total_packet_quality_control_field": {"type": "object"},
            "n_total_packets_with_llm_route_adoption_status": {"type": "integer"},
            "n_total_packets_llm_route_adoption_ready": {"type": "integer"},
            "n_total_packets_llm_route_adoption_pending_refinement": {
                "type": "integer"
            },
            "n_total_packets_llm_route_adoption_rejected": {"type": "integer"},
            "n_total_packets_llm_route_adoption_awaiting_response": {
                "type": "integer"
            },
            "n_total_packet_llm_route_adoption_blockers": {"type": "integer"},
            "n_total_packet_llm_route_adoption_pending_quality_control_blockers": {
                "type": "integer"
            },
            "n_total_packet_llm_route_adoption_pending_source_grounding_blockers": {
                "type": "integer"
            },
            "by_total_packet_llm_route_adoption_status": {"type": "object"},
            "n_total_packets_with_formal_attempt_dependency": {"type": "integer"},
            "n_total_packets_formal_attempt_initial_ready": {"type": "integer"},
            "n_total_packets_formal_attempt_waiting": {"type": "integer"},
            "n_total_packets_formal_attempt_missing_prerequisites": {
                "type": "integer"
            },
            "by_total_packet_formal_attempt_dependency_status": {"type": "object"},
            "n_total_response_minimal_delta_action_witnesses_required": {
                "type": "integer"
            },
            "n_total_response_minimal_delta_action_witnesses_acknowledged": {
                "type": "integer"
            },
            "n_total_response_minimal_delta_action_witnesses_unacknowledged": {
                "type": "integer"
            },
            "n_total_response_addressed_minimal_delta_action_witnesses": {
                "type": "integer"
            },
            "n_unmatched_adapter_responses": {"type": "integer"},
            "target_rows": {
                "type": "array",
                "items": {"$ref": "#/$defs/target_row"},
            },
            "proof_evidence_status": {"const": PROOF_EVIDENCE_STATUS},
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "all_ok": {"type": "boolean"},
            "errors": string_array,
        },
        "$defs": {
            "target_row": {
                "type": "object",
                "additionalProperties": True,
                "required": [
                    "target_prover_family",
                    "target_library_snapshot_ref",
                    "n_packets",
                    "n_packets_with_alignment",
                    "n_packets_with_standalone_input_trace",
                    "n_packets_missing_standalone_input_trace",
                    "n_packets_with_target_library_snapshot_trace",
                    "n_packets_missing_target_library_snapshot_trace",
                    "n_packets_target_library_snapshot_mismatch",
                    "n_packets_with_replan_metadata_trace",
                    "n_packets_with_residual_goal_contexts",
                    "n_packet_residual_goal_contexts",
                    "packet_residual_context_source_kinds",
                    "n_packet_residual_contexts_with_source_refs",
                    "n_packet_residual_contexts_with_formal_gap_boundary",
                    "n_packets_with_quality_controls",
                    "n_packet_quality_control_fields",
                    "packet_quality_control_fields",
                    "packet_quality_control_resource_contract_ids",
                    "packet_quality_control_response_validation_signals",
                    "packet_quality_control_stop_conditions",
                    "by_packet_quality_control_field",
                    "n_packets_with_llm_route_adoption_status",
                    "n_packets_llm_route_adoption_ready",
                    "n_packets_llm_route_adoption_pending_refinement",
                    "n_packets_llm_route_adoption_rejected",
                    "n_packets_llm_route_adoption_awaiting_response",
                    "n_packet_llm_route_adoption_blockers",
                    "n_packet_llm_route_adoption_pending_quality_control_blockers",
                    "n_packet_llm_route_adoption_pending_source_grounding_blockers",
                    "by_packet_llm_route_adoption_status",
                    "n_packets_with_formal_attempt_dependency",
                    "n_packets_formal_attempt_initial_ready",
                    "n_packets_formal_attempt_waiting",
                    "n_packets_formal_attempt_missing_prerequisites",
                    "by_packet_formal_attempt_dependency_status",
                    "n_response_minimal_delta_action_witnesses_required",
                    "n_response_minimal_delta_action_witnesses_acknowledged",
                    "n_response_minimal_delta_action_witnesses_unacknowledged",
                    "n_response_addressed_minimal_delta_action_witnesses",
                    "aggregate_packet_jsonl_path",
                    "aggregate_response_validation_jsonl_path",
                    "packet_filter_field",
                    "packet_filter_value",
                    "response_validation_filter_field",
                    "response_validation_filter_value",
                    "ok",
                    "errors",
                ],
                "properties": {
                    "target_prover_family": {"enum": list(PROVER_FAMILIES)},
                    "target_library_snapshot_ref": {
                        "type": "string",
                        "minLength": 1,
                    },
                    "n_packets": {"type": "integer"},
                    "n_packets_with_alignment": {"type": "integer"},
                    "n_packets_with_standalone_input_trace": {"type": "integer"},
                    "n_packets_missing_standalone_input_trace": {"type": "integer"},
                    "n_packets_with_target_library_snapshot_trace": {"type": "integer"},
                    "n_packets_missing_target_library_snapshot_trace": {"type": "integer"},
                    "n_packets_target_library_snapshot_mismatch": {"type": "integer"},
                    "n_packets_with_replan_metadata_trace": {"type": "integer"},
                    "n_packets_with_residual_goal_contexts": {"type": "integer"},
                    "n_packet_residual_goal_contexts": {"type": "integer"},
                    "packet_residual_context_source_kinds": string_array,
                    "n_packet_residual_contexts_with_source_refs": {
                        "type": "integer"
                    },
                    "n_packet_residual_contexts_with_formal_gap_boundary": {
                        "type": "integer"
                    },
                    "n_packets_with_quality_controls": {"type": "integer"},
                    "n_packet_quality_control_fields": {"type": "integer"},
                    "packet_quality_control_fields": string_array,
                    "packet_quality_control_resource_contract_ids": string_array,
                    "packet_quality_control_response_validation_signals": string_array,
                    "packet_quality_control_stop_conditions": string_array,
                    "by_packet_quality_control_field": {"type": "object"},
                    "n_packets_with_llm_route_adoption_status": {"type": "integer"},
                    "n_packets_llm_route_adoption_ready": {"type": "integer"},
                    "n_packets_llm_route_adoption_pending_refinement": {
                        "type": "integer"
                    },
                    "n_packets_llm_route_adoption_rejected": {"type": "integer"},
                    "n_packets_llm_route_adoption_awaiting_response": {
                        "type": "integer"
                    },
                    "n_packet_llm_route_adoption_blockers": {"type": "integer"},
                    "n_packet_llm_route_adoption_pending_quality_control_blockers": {
                        "type": "integer"
                    },
                    "n_packet_llm_route_adoption_pending_source_grounding_blockers": {
                        "type": "integer"
                    },
                    "by_packet_llm_route_adoption_status": {"type": "object"},
                    "n_packets_with_formal_attempt_dependency": {"type": "integer"},
                    "n_packets_formal_attempt_initial_ready": {"type": "integer"},
                    "n_packets_formal_attempt_waiting": {"type": "integer"},
                    "n_packets_formal_attempt_missing_prerequisites": {
                        "type": "integer"
                    },
                    "by_packet_formal_attempt_dependency_status": {
                        "type": "object"
                    },
                    "n_response_minimal_delta_action_witnesses_required": {
                        "type": "integer"
                    },
                    "n_response_minimal_delta_action_witnesses_acknowledged": {
                        "type": "integer"
                    },
                    "n_response_minimal_delta_action_witnesses_unacknowledged": {
                        "type": "integer"
                    },
                    "n_response_addressed_minimal_delta_action_witnesses": {
                        "type": "integer"
                    },
                    "n_response_validation_rows": {"type": "integer"},
                    "n_unmatched_adapter_responses": {"type": "integer"},
                    "aggregate_packet_jsonl_path": {
                        "type": "string",
                        "minLength": 1,
                    },
                    "aggregate_response_validation_jsonl_path": {
                        "type": "string",
                        "minLength": 1,
                    },
                    "packet_filter_field": {"const": "target_prover_family"},
                    "packet_filter_value": {"enum": list(PROVER_FAMILIES)},
                    "response_validation_filter_field": {
                        "const": "target_prover_family"
                    },
                    "response_validation_filter_value": {
                        "enum": list(PROVER_FAMILIES)
                    },
                    "source_contract_manifest_path": {"type": "string"},
                    "ok": {"type": "boolean"},
                    "errors": string_array,
                },
            }
        },
    }


def validate_cross_prover_target_summary_payload(
    payload: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    summary_schema = schema or cross_prover_target_summary_json_schema()
    errors: list[str] = []
    required = summary_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in payload:
                errors.append(f"{field_name} required")
    properties = summary_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if (
                isinstance(field_name, str)
                and isinstance(field_schema, dict)
                and field_name in payload
            ):
                errors.extend(
                    _schema_property_errors(field_name, payload[field_name], field_schema)
                )
    raw_rows = payload.get("target_rows", [])
    if not isinstance(raw_rows, list):
        errors.append("target_rows must be array")
        rows: list[dict[str, Any]] = []
    else:
        rows = [row for row in raw_rows if isinstance(row, dict)]
        if len(rows) != len(raw_rows):
            errors.append("target_rows items must be objects")
    if not rows:
        errors.append("target_rows must not be empty")
    target_schema = (
        summary_schema.get("$defs", {})
        if isinstance(summary_schema.get("$defs", {}), dict)
        else {}
    ).get("target_row", {})
    target_required = (
        target_schema.get("required", []) if isinstance(target_schema, dict) else []
    )
    target_properties = (
        target_schema.get("properties", {}) if isinstance(target_schema, dict) else {}
    )
    for idx, row in enumerate(rows):
        if isinstance(target_required, list):
            for field_name in target_required:
                if isinstance(field_name, str) and field_name not in row:
                    errors.append(f"target_rows[{idx}].{field_name} required")
        if isinstance(target_properties, dict):
            for field_name, field_schema in target_properties.items():
                if (
                    isinstance(field_name, str)
                    and isinstance(field_schema, dict)
                    and field_name in row
                ):
                    errors.extend(
                        _schema_property_errors(
                            f"target_rows[{idx}].{field_name}",
                            row[field_name],
                            field_schema,
                        )
                    )
        for path_field in (
            "aggregate_packet_jsonl_path",
            "aggregate_response_validation_jsonl_path",
        ):
            path_value = Path(str(row.get(path_field, "")))
            if path_value.is_absolute() or ".." in path_value.parts:
                errors.append(f"target_rows[{idx}].{path_field} must stay relative")
        if row.get("packet_filter_value") != row.get("target_prover_family"):
            errors.append(
                f"target_rows[{idx}].packet_filter_value must match target_prover_family"
            )
        if row.get("response_validation_filter_value") != row.get(
            "target_prover_family"
        ):
            errors.append(
                "target_rows"
                f"[{idx}].response_validation_filter_value must match target_prover_family"
            )
        if row.get("ok") is True and row.get("errors") not in ([], (), None):
            errors.append(f"target_rows[{idx}] ok rows must not carry errors")
    if payload.get("n_target_rows") != len(rows):
        errors.append("n_target_rows must equal number of target_rows")
    if payload.get("n_targets_ok") != sum(1 for row in rows if row.get("ok") is True):
        errors.append("n_targets_ok must equal ok target rows")
    if payload.get("n_total_packets") != sum(_int(row.get("n_packets")) for row in rows):
        errors.append("n_total_packets must equal target packet total")
    if payload.get("n_total_packets_with_alignment") != sum(
        _int(row.get("n_packets_with_alignment")) for row in rows
    ):
        errors.append(
            "n_total_packets_with_alignment must equal target alignment total"
        )
    if payload.get("n_total_packets_with_standalone_input_trace") != sum(
        _int(row.get("n_packets_with_standalone_input_trace")) for row in rows
    ):
        errors.append(
            "n_total_packets_with_standalone_input_trace must equal target trace total"
        )
    if payload.get("n_total_packets_missing_standalone_input_trace") != sum(
        _int(row.get("n_packets_missing_standalone_input_trace")) for row in rows
    ):
        errors.append(
            "n_total_packets_missing_standalone_input_trace must equal target missing trace total"
        )
    if payload.get("n_total_packets_with_target_library_snapshot_trace") != sum(
        _int(row.get("n_packets_with_target_library_snapshot_trace")) for row in rows
    ):
        errors.append(
            "n_total_packets_with_target_library_snapshot_trace must equal target snapshot trace total"
        )
    if payload.get("n_total_packets_missing_target_library_snapshot_trace") != sum(
        _int(row.get("n_packets_missing_target_library_snapshot_trace"))
        for row in rows
    ):
        errors.append(
            "n_total_packets_missing_target_library_snapshot_trace must equal target missing snapshot trace total"
        )
    if payload.get("n_total_packets_target_library_snapshot_mismatch") != sum(
        _int(row.get("n_packets_target_library_snapshot_mismatch")) for row in rows
    ):
        errors.append(
            "n_total_packets_target_library_snapshot_mismatch must equal target snapshot mismatch total"
        )
    if payload.get("n_total_packets_with_replan_metadata_trace") != sum(
        _int(row.get("n_packets_with_replan_metadata_trace")) for row in rows
    ):
        errors.append(
            "n_total_packets_with_replan_metadata_trace must equal target replan metadata trace total"
        )
    if payload.get("n_total_packets_with_residual_goal_contexts") != sum(
        _int(row.get("n_packets_with_residual_goal_contexts")) for row in rows
    ):
        errors.append(
            "n_total_packets_with_residual_goal_contexts must equal target residual-context packet total"
        )
    if payload.get("n_total_packet_residual_goal_contexts") != sum(
        _int(row.get("n_packet_residual_goal_contexts")) for row in rows
    ):
        errors.append(
            "n_total_packet_residual_goal_contexts must equal target residual-context total"
        )
    observed_residual_source_kinds = _str_tuple(
        payload.get("packet_residual_context_source_kinds", [])
    )
    expected_residual_source_kinds = _residual_context_source_kinds_from_target_rows(
        rows
    )
    if observed_residual_source_kinds != expected_residual_source_kinds:
        errors.append(
            "packet_residual_context_source_kinds must equal target residual-context source kinds"
        )
    if payload.get("n_total_packet_residual_contexts_with_source_refs") != sum(
        _int(row.get("n_packet_residual_contexts_with_source_refs")) for row in rows
    ):
        errors.append(
            "n_total_packet_residual_contexts_with_source_refs must equal target residual-context source-ref total"
        )
    if payload.get(
        "n_total_packet_residual_contexts_with_formal_gap_boundary"
    ) != sum(
        _int(row.get("n_packet_residual_contexts_with_formal_gap_boundary"))
        for row in rows
    ):
        errors.append(
            "n_total_packet_residual_contexts_with_formal_gap_boundary must equal target residual-context boundary total"
        )
    if payload.get("n_total_packets_with_quality_controls") != sum(
        _int(row.get("n_packets_with_quality_controls")) for row in rows
    ):
        errors.append(
            "n_total_packets_with_quality_controls must equal target quality-control packet total"
        )
    if payload.get("n_total_packet_quality_control_fields") != sum(
        _int(row.get("n_packet_quality_control_fields")) for row in rows
    ):
        errors.append(
            "n_total_packet_quality_control_fields must equal target quality-control field total"
        )
    expected_quality_fields = _quality_control_fields_from_target_rows(rows)
    observed_quality_fields = _str_tuple(
        payload.get("packet_quality_control_fields", [])
    )
    if observed_quality_fields != expected_quality_fields:
        errors.append(
            "packet_quality_control_fields must equal target quality-control fields"
        )
    quality_value_comparisons = (
        (
            "packet_quality_control_resource_contract_ids",
            "packet_quality_control_resource_contract_ids",
        ),
        (
            "packet_quality_control_response_validation_signals",
            "packet_quality_control_response_validation_signals",
        ),
        (
            "packet_quality_control_stop_conditions",
            "packet_quality_control_stop_conditions",
        ),
    )
    for payload_field_name, target_field_name in quality_value_comparisons:
        observed_values = _str_tuple(payload.get(payload_field_name, []))
        expected_values = _quality_control_values_from_target_rows(
            rows,
            target_field_name,
        )
        if observed_values != expected_values:
            errors.append(f"{payload_field_name} must equal target values")
    observed_quality_summary = payload.get("by_total_packet_quality_control_field", {})
    observed_quality_summary = _normalize_quality_control_field_summary(
        observed_quality_summary
    )
    expected_quality_summary = _sum_quality_control_field_summary(rows)
    if observed_quality_summary != expected_quality_summary:
        errors.append(
            "by_total_packet_quality_control_field must equal target quality-control summary"
        )
    if payload.get("n_total_packets_with_llm_route_adoption_status") != sum(
        _int(row.get("n_packets_with_llm_route_adoption_status")) for row in rows
    ):
        errors.append(
            "n_total_packets_with_llm_route_adoption_status must equal target route-adoption status total"
        )
    if payload.get("n_total_packets_llm_route_adoption_ready") != sum(
        _int(row.get("n_packets_llm_route_adoption_ready")) for row in rows
    ):
        errors.append(
            "n_total_packets_llm_route_adoption_ready must equal target route-adoption ready total"
        )
    if payload.get("n_total_packets_llm_route_adoption_pending_refinement") != sum(
        _int(row.get("n_packets_llm_route_adoption_pending_refinement"))
        for row in rows
    ):
        errors.append(
            "n_total_packets_llm_route_adoption_pending_refinement must equal target route-adoption pending total"
        )
    if payload.get("n_total_packets_llm_route_adoption_rejected") != sum(
        _int(row.get("n_packets_llm_route_adoption_rejected")) for row in rows
    ):
        errors.append(
            "n_total_packets_llm_route_adoption_rejected must equal target route-adoption rejected total"
        )
    if payload.get("n_total_packets_llm_route_adoption_awaiting_response") != sum(
        _int(row.get("n_packets_llm_route_adoption_awaiting_response"))
        for row in rows
    ):
        errors.append(
            "n_total_packets_llm_route_adoption_awaiting_response must equal target route-adoption awaiting-response total"
        )
    if payload.get("n_total_packet_llm_route_adoption_blockers") != sum(
        _int(row.get("n_packet_llm_route_adoption_blockers")) for row in rows
    ):
        errors.append(
            "n_total_packet_llm_route_adoption_blockers must equal target route-adoption blocker total"
        )
    if payload.get(
        "n_total_packet_llm_route_adoption_pending_quality_control_blockers"
    ) != sum(
        _int(
            row.get(
                "n_packet_llm_route_adoption_pending_quality_control_blockers"
            )
        )
        for row in rows
    ):
        errors.append(
            "n_total_packet_llm_route_adoption_pending_quality_control_blockers "
            "must equal target route-adoption quality-control blocker total"
        )
    if payload.get(
        "n_total_packet_llm_route_adoption_pending_source_grounding_blockers"
    ) != sum(
        _int(
            row.get(
                "n_packet_llm_route_adoption_pending_source_grounding_blockers"
            )
        )
        for row in rows
    ):
        errors.append(
            "n_total_packet_llm_route_adoption_pending_source_grounding_blockers "
            "must equal target route-adoption source-grounding blocker total"
        )
    expected_status_counts = _sum_route_adoption_status_counts(rows)
    raw_status_counts = payload.get("by_total_packet_llm_route_adoption_status", {})
    observed_status_counts = (
        {str(status): _int(count) for status, count in raw_status_counts.items()}
        if isinstance(raw_status_counts, dict)
        else {}
    )
    if observed_status_counts != expected_status_counts:
        errors.append(
            "by_total_packet_llm_route_adoption_status must equal target status counts"
        )
    if payload.get("n_total_packets_with_formal_attempt_dependency") != sum(
        _int(row.get("n_packets_with_formal_attempt_dependency")) for row in rows
    ):
        errors.append(
            "n_total_packets_with_formal_attempt_dependency must equal target formal-attempt dependency total"
        )
    if payload.get("n_total_packets_formal_attempt_initial_ready") != sum(
        _int(row.get("n_packets_formal_attempt_initial_ready")) for row in rows
    ):
        errors.append(
            "n_total_packets_formal_attempt_initial_ready must equal target formal-attempt ready total"
        )
    if payload.get("n_total_packets_formal_attempt_waiting") != sum(
        _int(row.get("n_packets_formal_attempt_waiting")) for row in rows
    ):
        errors.append(
            "n_total_packets_formal_attempt_waiting must equal target formal-attempt waiting total"
        )
    if payload.get("n_total_packets_formal_attempt_missing_prerequisites") != sum(
        _int(row.get("n_packets_formal_attempt_missing_prerequisites"))
        for row in rows
    ):
        errors.append(
            "n_total_packets_formal_attempt_missing_prerequisites must equal target formal-attempt missing-prerequisite total"
        )
    expected_attempt_counts = _sum_formal_attempt_dependency_status_counts(rows)
    raw_attempt_counts = payload.get(
        "by_total_packet_formal_attempt_dependency_status",
        {},
    )
    observed_attempt_counts = (
        {str(status): _int(count) for status, count in raw_attempt_counts.items()}
        if isinstance(raw_attempt_counts, dict)
        else {}
    )
    if observed_attempt_counts != expected_attempt_counts:
        errors.append(
            "by_total_packet_formal_attempt_dependency_status must equal target formal-attempt dependency status counts"
        )
    if payload.get(
        "n_total_response_minimal_delta_action_witnesses_required"
    ) != sum(
        _int(row.get("n_response_minimal_delta_action_witnesses_required"))
        for row in rows
    ):
        errors.append(
            "n_total_response_minimal_delta_action_witnesses_required must equal target response witness total"
        )
    if payload.get(
        "n_total_response_minimal_delta_action_witnesses_acknowledged"
    ) != sum(
        _int(row.get("n_response_minimal_delta_action_witnesses_acknowledged"))
        for row in rows
    ):
        errors.append(
            "n_total_response_minimal_delta_action_witnesses_acknowledged must equal target response witness acknowledgement total"
        )
    if payload.get(
        "n_total_response_minimal_delta_action_witnesses_unacknowledged"
    ) != sum(
        _int(row.get("n_response_minimal_delta_action_witnesses_unacknowledged"))
        for row in rows
    ):
        errors.append(
            "n_total_response_minimal_delta_action_witnesses_unacknowledged must equal target unacknowledged response witness total"
        )
    if payload.get(
        "n_total_response_addressed_minimal_delta_action_witnesses"
    ) != sum(
        _int(row.get("n_response_addressed_minimal_delta_action_witnesses"))
        for row in rows
    ):
        errors.append(
            "n_total_response_addressed_minimal_delta_action_witnesses must equal target addressed witness total"
        )
    if "n_unmatched_adapter_responses" in payload and payload.get(
        "n_unmatched_adapter_responses"
    ) != sum(_int(row.get("n_unmatched_adapter_responses")) for row in rows):
        errors.append(
            "n_unmatched_adapter_responses must equal target unmatched response total"
        )
    if (
        payload.get("all_ok") is True
        and _int(payload.get("n_total_packets_missing_standalone_input_trace")) != 0
    ):
        errors.append("all_ok target summary must not miss standalone input traces")
    if (
        payload.get("all_ok") is True
        and _int(payload.get("n_total_packets_missing_target_library_snapshot_trace"))
        != 0
    ):
        errors.append(
            "all_ok target summary must not miss target library snapshot traces"
        )
    if (
        payload.get("all_ok") is True
        and _int(payload.get("n_total_packets_target_library_snapshot_mismatch"))
        != 0
    ):
        errors.append(
            "all_ok target summary must not have target library snapshot mismatches"
        )
    if (
        payload.get("all_ok") is True
        and _int(payload.get("n_unmatched_adapter_responses")) != 0
    ):
        errors.append("all_ok target summary must not have unmatched adapter responses")
    if payload.get("all_ok") is True and payload.get("errors") not in ([], (), None):
        errors.append("all_ok target summary must not carry errors")
    return tuple(errors)


def cross_prover_matrix_audit_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": CROSS_PROVER_MATRIX_AUDIT_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Cross-Prover Matrix Audit Row",
        "description": (
            "One target-prover row in the reusable cross-prover matrix audit. "
            "Rows summarize portable packet export and response-validation "
            "status; they are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "matrix_row_id",
            "target_prover_family",
            "target_library_snapshot_ref",
            "contract_dir",
            "contract_manifest_path",
            "packet_jsonl_path",
            "response_validation_jsonl_path",
            "n_plan_rows",
            "n_packets",
            "n_packet_ok",
            "n_packet_schema_valid",
            "n_packets_schema_invalid",
            "n_packets_with_alignment",
            "n_packets_missing_alignment",
            "n_packets_with_standalone_input_trace",
            "n_packets_missing_standalone_input_trace",
            "n_packets_with_target_library_snapshot_trace",
            "n_packets_missing_target_library_snapshot_trace",
            "n_packets_target_library_snapshot_mismatch",
            "n_packets_with_replan_metadata_trace",
            "n_packets_with_residual_goal_contexts",
            "n_packet_residual_goal_contexts",
            "packet_residual_context_source_kinds",
            "n_packet_residual_contexts_with_source_refs",
            "n_packet_residual_contexts_with_formal_gap_boundary",
            "n_packets_with_quality_controls",
            "n_packet_quality_control_fields",
            "packet_quality_control_fields",
            "packet_quality_control_resource_contract_ids",
            "packet_quality_control_response_validation_signals",
            "packet_quality_control_stop_conditions",
            "by_packet_quality_control_field",
            "n_packets_with_llm_route_adoption_status",
            "n_packets_llm_route_adoption_ready",
            "n_packets_llm_route_adoption_pending_refinement",
            "n_packets_llm_route_adoption_rejected",
            "n_packets_llm_route_adoption_awaiting_response",
            "n_packet_llm_route_adoption_blockers",
            "n_packet_llm_route_adoption_pending_quality_control_blockers",
            "n_packet_llm_route_adoption_pending_source_grounding_blockers",
            "by_packet_llm_route_adoption_status",
            "n_packets_with_formal_attempt_dependency",
            "n_packets_formal_attempt_initial_ready",
            "n_packets_formal_attempt_waiting",
            "n_packets_formal_attempt_missing_prerequisites",
            "by_packet_formal_attempt_dependency_status",
            "n_response_present",
            "n_awaiting_adapter_mapping",
            "n_response_contract_ok",
            "n_response_minimal_delta_action_witnesses_required",
            "n_response_minimal_delta_action_witnesses_acknowledged",
            "n_response_minimal_delta_action_witnesses_unacknowledged",
            "n_response_addressed_minimal_delta_action_witnesses",
            "n_rejected",
            "n_kernel_verified_claims_rejected",
            "packet_fingerprint",
            "response_validation_fingerprint",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
            "errors",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_CROSS_PROVER_MATRIX_AUDIT_SCHEMA_VERSION,
            },
            "matrix_row_id": {"type": "string", "minLength": 1},
            "target_prover_family": {"enum": list(PROVER_FAMILIES)},
            "target_library_snapshot_ref": {"type": "string", "minLength": 1},
            "contract_dir": {"type": "string", "minLength": 1},
            "contract_manifest_path": {"type": "string", "minLength": 1},
            "packet_jsonl_path": {"type": "string", "minLength": 1},
            "response_validation_jsonl_path": {"type": "string", "minLength": 1},
            "n_plan_rows": {"type": "integer"},
            "n_packets": {"type": "integer"},
            "n_packet_ok": {"type": "integer"},
            "n_packet_schema_valid": {"type": "integer"},
            "n_packets_schema_invalid": {"type": "integer"},
            "n_packets_with_alignment": {"type": "integer"},
            "n_packets_missing_alignment": {"type": "integer"},
            "n_packets_with_standalone_input_trace": {"type": "integer"},
            "n_packets_missing_standalone_input_trace": {"type": "integer"},
            "n_packets_with_target_library_snapshot_trace": {"type": "integer"},
            "n_packets_missing_target_library_snapshot_trace": {"type": "integer"},
            "n_packets_target_library_snapshot_mismatch": {"type": "integer"},
            "n_packets_with_replan_metadata_trace": {"type": "integer"},
            "n_packets_with_residual_goal_contexts": {"type": "integer"},
            "n_packet_residual_goal_contexts": {"type": "integer"},
            "packet_residual_context_source_kinds": string_array,
            "n_packet_residual_contexts_with_source_refs": {"type": "integer"},
            "n_packet_residual_contexts_with_formal_gap_boundary": {
                "type": "integer"
            },
            "n_packets_with_quality_controls": {"type": "integer"},
            "n_packet_quality_control_fields": {"type": "integer"},
            "packet_quality_control_fields": string_array,
            "packet_quality_control_resource_contract_ids": string_array,
            "packet_quality_control_response_validation_signals": string_array,
            "packet_quality_control_stop_conditions": string_array,
            "by_packet_quality_control_field": {"type": "object"},
            "n_packets_with_llm_route_adoption_status": {"type": "integer"},
            "n_packets_llm_route_adoption_ready": {"type": "integer"},
            "n_packets_llm_route_adoption_pending_refinement": {"type": "integer"},
            "n_packets_llm_route_adoption_rejected": {"type": "integer"},
            "n_packets_llm_route_adoption_awaiting_response": {"type": "integer"},
            "n_packet_llm_route_adoption_blockers": {"type": "integer"},
            "n_packet_llm_route_adoption_pending_quality_control_blockers": {
                "type": "integer"
            },
            "n_packet_llm_route_adoption_pending_source_grounding_blockers": {
                "type": "integer"
            },
            "by_packet_llm_route_adoption_status": {"type": "object"},
            "n_packets_with_formal_attempt_dependency": {"type": "integer"},
            "n_packets_formal_attempt_initial_ready": {"type": "integer"},
            "n_packets_formal_attempt_waiting": {"type": "integer"},
            "n_packets_formal_attempt_missing_prerequisites": {"type": "integer"},
            "by_packet_formal_attempt_dependency_status": {"type": "object"},
            "n_response_present": {"type": "integer"},
            "n_awaiting_adapter_mapping": {"type": "integer"},
            "n_response_contract_ok": {"type": "integer"},
            "n_response_minimal_delta_action_witnesses_required": {
                "type": "integer"
            },
            "n_response_minimal_delta_action_witnesses_acknowledged": {
                "type": "integer"
            },
            "n_response_minimal_delta_action_witnesses_unacknowledged": {
                "type": "integer"
            },
            "n_response_addressed_minimal_delta_action_witnesses": {
                "type": "integer"
            },
            "n_unmatched_adapter_responses": {"type": "integer"},
            "n_rejected": {"type": "integer"},
            "n_kernel_verified_claims_rejected": {"type": "integer"},
            "packet_fingerprint": {"type": "string"},
            "response_validation_fingerprint": {"type": "string"},
            "proof_evidence_status": {
                "type": "string",
                "pattern": "NOT_PROOF_EVIDENCE",
            },
            "proof_evidence_boundary": {
                "type": "string",
                "pattern": "not theorem proof evidence",
            },
            "ok": {"type": "boolean"},
            "errors": string_array,
        },
    }


def validate_cross_prover_matrix_audit_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    row_schema = schema or cross_prover_matrix_audit_row_json_schema()
    errors: list[str] = []
    if not isinstance(row, dict):
        return ("row must be object",)
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
    return tuple(errors)


def _matrix_row(
    target_family: str,
    snapshot_ref: str,
    contract_dir: Path,
    contract_payload: dict[str, Any],
) -> FormalizationGapPlannerCrossProverMatrixRow:
    errors = tuple(str(error) for error in contract_payload.get("errors", []) if str(error))
    n_packets = _int(contract_payload.get("n_packets"))
    n_packets_with_trace = _int(
        contract_payload.get("n_packets_with_standalone_input_trace")
    )
    packet_rows = [
        packet
        for packet in contract_payload.get("packets", [])
        if isinstance(packet, dict)
    ]
    n_packets_with_target_snapshot = sum(
        1 for packet in packet_rows if _packet_has_target_library_snapshot_trace(packet)
    )
    n_packets_target_snapshot_mismatch = sum(
        1 for packet in packet_rows if _packet_target_library_snapshot_mismatch(packet)
    )
    return FormalizationGapPlannerCrossProverMatrixRow(
        schema_version=FORMALIZATION_GAP_PLANNER_CROSS_PROVER_MATRIX_AUDIT_SCHEMA_VERSION,
        matrix_row_id="formalization_gap_planner_cross_prover_matrix:"
        + stable_hash([target_family, snapshot_ref, contract_payload.get("packet_fingerprint", "")])[:20],
        target_prover_family=str(contract_payload.get("target_prover_family", target_family)),
        target_library_snapshot_ref=snapshot_ref,
        contract_dir=str(contract_dir),
        contract_manifest_path=str(
            contract_dir / "formalization_gap_planner_prover_adapter_contract_manifest.json"
        ),
        packet_jsonl_path=str(contract_dir / "formalization_gap_planner_prover_adapter_packets.jsonl"),
        response_validation_jsonl_path=str(
            contract_dir / "formalization_gap_planner_prover_adapter_response_validation.jsonl"
        ),
        n_plan_rows=_int(contract_payload.get("n_plan_rows")),
        n_packets=n_packets,
        n_packet_ok=_int(contract_payload.get("n_packet_ok")),
        n_packet_schema_valid=_int(contract_payload.get("n_packet_schema_valid")),
        n_packets_schema_invalid=max(
            0,
            n_packets
            - _int(contract_payload.get("n_packet_schema_valid")),
        ),
        n_packets_with_alignment=_int(
            contract_payload.get("n_packets_with_alignment")
        ),
        n_packets_missing_alignment=max(
            0,
            n_packets
            - _int(contract_payload.get("n_packets_with_alignment")),
        ),
        n_packets_with_standalone_input_trace=n_packets_with_trace,
        n_packets_missing_standalone_input_trace=max(
            0,
            n_packets - n_packets_with_trace,
        ),
        n_packets_with_target_library_snapshot_trace=n_packets_with_target_snapshot,
        n_packets_missing_target_library_snapshot_trace=max(
            0,
            n_packets - n_packets_with_target_snapshot,
        ),
        n_packets_target_library_snapshot_mismatch=(
            n_packets_target_snapshot_mismatch
        ),
        n_packets_with_replan_metadata_trace=_int(
            contract_payload.get("n_packets_with_replan_metadata_trace")
        ),
        n_packets_with_residual_goal_contexts=_int(
            contract_payload.get("n_packets_with_residual_goal_contexts")
        ),
        n_packet_residual_goal_contexts=_int(
            contract_payload.get("n_packet_residual_goal_contexts")
        ),
        packet_residual_context_source_kinds=_str_tuple(
            contract_payload.get("packet_residual_context_source_kinds", [])
        ),
        n_packet_residual_contexts_with_source_refs=_int(
            contract_payload.get("n_packet_residual_contexts_with_source_refs")
        ),
        n_packet_residual_contexts_with_formal_gap_boundary=_int(
            contract_payload.get(
                "n_packet_residual_contexts_with_formal_gap_boundary"
            )
        ),
        n_packets_with_quality_controls=_int(
            contract_payload.get("n_packets_with_quality_controls")
        ),
        n_packet_quality_control_fields=_int(
            contract_payload.get("n_packet_quality_control_fields")
        ),
        packet_quality_control_fields=_str_tuple(
            contract_payload.get("packet_quality_control_fields", [])
        ),
        packet_quality_control_resource_contract_ids=_str_tuple(
            contract_payload.get("packet_quality_control_resource_contract_ids", [])
        ),
        packet_quality_control_response_validation_signals=_str_tuple(
            contract_payload.get(
                "packet_quality_control_response_validation_signals",
                [],
            )
        ),
        packet_quality_control_stop_conditions=_str_tuple(
            contract_payload.get("packet_quality_control_stop_conditions", [])
        ),
        by_packet_quality_control_field={
            str(field_name): dict(summary)
            for field_name, summary in dict(
                contract_payload.get("by_packet_quality_control_field", {}) or {}
            ).items()
            if isinstance(summary, dict)
        },
        n_packets_with_llm_route_adoption_status=_int(
            contract_payload.get("n_packets_with_llm_route_adoption_status")
        ),
        n_packets_llm_route_adoption_ready=_int(
            contract_payload.get("n_packets_llm_route_adoption_ready")
        ),
        n_packets_llm_route_adoption_pending_refinement=_int(
            contract_payload.get("n_packets_llm_route_adoption_pending_refinement")
        ),
        n_packets_llm_route_adoption_rejected=_int(
            contract_payload.get("n_packets_llm_route_adoption_rejected")
        ),
        n_packets_llm_route_adoption_awaiting_response=_int(
            contract_payload.get("n_packets_llm_route_adoption_awaiting_response")
        ),
        n_packet_llm_route_adoption_blockers=_int(
            contract_payload.get("n_packet_llm_route_adoption_blockers")
        ),
        n_packet_llm_route_adoption_pending_quality_control_blockers=_int(
            contract_payload.get(
                "n_packet_llm_route_adoption_pending_quality_control_blockers"
            )
        ),
        n_packet_llm_route_adoption_pending_source_grounding_blockers=_int(
            contract_payload.get(
                "n_packet_llm_route_adoption_pending_source_grounding_blockers"
            )
        ),
        by_packet_llm_route_adoption_status={
            str(status): _int(count)
            for status, count in dict(
                contract_payload.get("by_packet_llm_route_adoption_status", {})
                or {}
            ).items()
        },
        n_packets_with_formal_attempt_dependency=_int(
            contract_payload.get("n_packets_with_formal_attempt_dependency")
        ),
        n_packets_formal_attempt_initial_ready=_int(
            contract_payload.get("n_packets_formal_attempt_initial_ready")
        ),
        n_packets_formal_attempt_waiting=_int(
            contract_payload.get("n_packets_formal_attempt_waiting")
        ),
        n_packets_formal_attempt_missing_prerequisites=_int(
            contract_payload.get("n_packets_formal_attempt_missing_prerequisites")
        ),
        by_packet_formal_attempt_dependency_status={
            str(status): _int(count)
            for status, count in dict(
                contract_payload.get(
                    "by_packet_formal_attempt_dependency_status",
                    {},
                )
                or {}
            ).items()
        },
        n_response_present=_int(contract_payload.get("n_response_present")),
        n_awaiting_adapter_mapping=_int(
            contract_payload.get("n_awaiting_adapter_mapping")
        ),
        n_response_contract_ok=_int(contract_payload.get("n_response_contract_ok")),
        n_response_minimal_delta_action_witnesses_required=_int(
            contract_payload.get(
                "n_response_minimal_delta_action_witnesses_required"
            )
        ),
        n_response_minimal_delta_action_witnesses_acknowledged=_int(
            contract_payload.get(
                "n_response_minimal_delta_action_witnesses_acknowledged"
            )
        ),
        n_response_minimal_delta_action_witnesses_unacknowledged=_int(
            contract_payload.get(
                "n_response_minimal_delta_action_witnesses_unacknowledged"
            )
        ),
        n_response_addressed_minimal_delta_action_witnesses=_int(
            contract_payload.get(
                "n_response_addressed_minimal_delta_action_witnesses"
            )
        ),
        n_unmatched_adapter_responses=_int(
            contract_payload.get("n_unmatched_adapter_responses")
        ),
        n_rejected=_int(contract_payload.get("n_rejected")),
        n_kernel_verified_claims_rejected=_int(
            contract_payload.get("n_kernel_verified_claims_rejected")
        ),
        packet_fingerprint=str(contract_payload.get("packet_fingerprint", "")),
        response_validation_fingerprint=str(
            contract_payload.get("response_validation_fingerprint", "")
        ),
        proof_evidence_status=str(contract_payload.get("proof_evidence_status", "")),
        proof_evidence_boundary=str(contract_payload.get("proof_evidence_boundary", "")),
        ok=bool(contract_payload.get("all_ok", False))
        and _int(contract_payload.get("n_packet_schema_valid"))
        == _int(contract_payload.get("n_packets"))
        and _int(contract_payload.get("n_packets_with_alignment"))
        == n_packets
        and n_packets_with_trace == n_packets
        and n_packets_with_target_snapshot == n_packets
        and n_packets_target_snapshot_mismatch == 0
        and _int(contract_payload.get("n_unmatched_adapter_responses")) == 0
        and _int(contract_payload.get("n_rejected")) == 0
        and _int(contract_payload.get("n_kernel_verified_claims_rejected")) == 0,
        errors=errors,
    )


def _target_summary_payload(
    *,
    rows: list[FormalizationGapPlannerCrossProverMatrixRow],
    packet_rows: list[dict[str, Any]],
    response_validation_rows: list[dict[str, Any]],
) -> dict[str, object]:
    target_rows: list[dict[str, object]] = []
    for row in rows:
        target = row.target_prover_family
        target_packet_rows = [
            packet
            for packet in packet_rows
            if str(packet.get("target_prover_family", "")) == target
        ]
        target_response_rows = [
            response
            for response in response_validation_rows
            if str(response.get("target_prover_family", "")) == target
        ]
        n_packets_with_trace = sum(
            1
            for packet in target_packet_rows
            if isinstance(packet.get("standalone_input_trace"), dict)
            and packet.get("standalone_input_trace")
        )
        n_packets_with_target_snapshot = sum(
            1
            for packet in target_packet_rows
            if _packet_has_target_library_snapshot_trace(packet)
        )
        n_packets_target_snapshot_mismatch = sum(
            1
            for packet in target_packet_rows
            if _packet_target_library_snapshot_mismatch(packet)
        )
        residual_goal_contexts = [
            context
            for packet in target_packet_rows
            for context in _residual_goal_contexts_from_packet_row(packet)
        ]
        n_packets_with_residual_goal_contexts = sum(
            1
            for packet in target_packet_rows
            if _residual_goal_contexts_from_packet_row(packet)
        )
        n_packets_with_quality_controls = sum(
            1
            for packet in target_packet_rows
            if _quality_controls_from_packet_row(packet)
        )
        n_packet_quality_control_fields = sum(
            len(_quality_controls_from_packet_row(packet))
            for packet in target_packet_rows
        )
        route_adoption_status_counts = Counter(
            str(packet.get("llm_route_planner_route_adoption_status", ""))
            for packet in target_packet_rows
            if str(packet.get("llm_route_planner_route_adoption_status", ""))
        )
        formal_attempt_dependency_status_counts = Counter(
            str(packet.get("formal_attempt_dependency_status", ""))
            for packet in target_packet_rows
            if str(packet.get("formal_attempt_dependency_status", ""))
        )
        n_response_minimal_delta_action_witnesses_required = sum(
            1
            for response in target_response_rows
            if response.get("response_present") is True
            and _int(response.get("minimal_delta_action_witness_count"))
        )
        n_response_minimal_delta_action_witnesses_acknowledged = sum(
            1
            for response in target_response_rows
            if response.get("response_present") is True
            and _int(response.get("minimal_delta_action_witness_count"))
            and response.get("minimal_delta_action_witness_acknowledged") is True
        )
        n_response_minimal_delta_action_witnesses_unacknowledged = sum(
            1
            for response in target_response_rows
            if response.get("response_present") is True
            and _int(response.get("minimal_delta_action_witness_count"))
            and response.get("minimal_delta_action_witness_acknowledged") is not True
        )
        n_response_addressed_minimal_delta_action_witnesses = sum(
            len(_str_tuple(response.get("addressed_minimal_delta_action_witnesses", [])))
            for response in target_response_rows
            if response.get("response_present") is True
        )
        n_route_adoption_quality_control_blockers = sum(
            1
            for packet in target_packet_rows
            if ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS
            in _str_tuple(
                packet.get("llm_route_planner_route_adoption_blockers", [])
            )
        )
        n_route_adoption_source_grounding_blockers = sum(
            1
            for packet in target_packet_rows
            if ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING
            in _str_tuple(
                packet.get("llm_route_planner_route_adoption_blockers", [])
            )
        )
        target_rows.append(
            {
                "target_prover_family": target,
                "target_library_snapshot_ref": row.target_library_snapshot_ref,
                "n_packets": len(target_packet_rows),
                "n_packets_with_alignment": sum(
                    1
                    for packet in target_packet_rows
                    if isinstance(packet.get("route_alignment_edge"), dict)
                    and packet.get("route_alignment_edge")
                ),
                "n_packets_with_standalone_input_trace": n_packets_with_trace,
                "n_packets_missing_standalone_input_trace": max(
                    0,
                    len(target_packet_rows) - n_packets_with_trace,
                ),
                "n_packets_with_target_library_snapshot_trace": (
                    n_packets_with_target_snapshot
                ),
                "n_packets_missing_target_library_snapshot_trace": max(
                    0,
                    len(target_packet_rows) - n_packets_with_target_snapshot,
                ),
                "n_packets_target_library_snapshot_mismatch": (
                    n_packets_target_snapshot_mismatch
                ),
                "n_packets_with_replan_metadata_trace": sum(
                    1
                    for packet in target_packet_rows
                    if isinstance(packet.get("standalone_input_trace"), dict)
                    and packet["standalone_input_trace"].get("has_replan_metadata")
                ),
                "n_packets_with_residual_goal_contexts": (
                    n_packets_with_residual_goal_contexts
                ),
                "n_packet_residual_goal_contexts": len(residual_goal_contexts),
                "packet_residual_context_source_kinds": (
                    _residual_context_source_kinds(tuple(residual_goal_contexts))
                ),
                "n_packet_residual_contexts_with_source_refs": sum(
                    1
                    for context in residual_goal_contexts
                    if _residual_context_has_sources(context)
                ),
                "n_packet_residual_contexts_with_formal_gap_boundary": sum(
                    1
                    for context in residual_goal_contexts
                    if _residual_context_has_formal_gap_boundary(context)
                ),
                "n_packets_with_quality_controls": n_packets_with_quality_controls,
                "n_packet_quality_control_fields": n_packet_quality_control_fields,
                "packet_quality_control_fields": (
                    _quality_control_fields_from_packet_rows(target_packet_rows)
                ),
                "packet_quality_control_resource_contract_ids": (
                    _quality_control_values_from_packet_rows(
                        target_packet_rows,
                        "resource_contract_ids",
                    )
                ),
                "packet_quality_control_response_validation_signals": (
                    _quality_control_values_from_packet_rows(
                        target_packet_rows,
                        "response_validation_signals",
                    )
                ),
                "packet_quality_control_stop_conditions": (
                    _quality_control_values_from_packet_rows(
                        target_packet_rows,
                        "stop_conditions",
                    )
                ),
                "by_packet_quality_control_field": (
                    _quality_control_field_summary_from_packet_rows(
                        target_packet_rows
                    )
                ),
                "n_packets_with_llm_route_adoption_status": sum(
                    route_adoption_status_counts.values()
                ),
                "n_packets_llm_route_adoption_ready": route_adoption_status_counts.get(
                    "READY_FOR_STANDALONE_REPLAY",
                    0,
                ),
                "n_packets_llm_route_adoption_pending_refinement": (
                    route_adoption_status_counts.get(
                        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION",
                        0,
                    )
                ),
                "n_packets_llm_route_adoption_rejected": (
                    route_adoption_status_counts.get("REJECTED_LLM_ROUTE_PLAN", 0)
                ),
                "n_packets_llm_route_adoption_awaiting_response": (
                    route_adoption_status_counts.get(
                        "AWAITING_LLM_ROUTE_PLANNER_RESPONSE",
                        0,
                    )
                ),
                "n_packet_llm_route_adoption_blockers": sum(
                    len(
                        _str_tuple(
                            packet.get(
                                "llm_route_planner_route_adoption_blockers",
                                [],
                            )
                        )
                    )
                    for packet in target_packet_rows
                ),
                "n_packet_llm_route_adoption_pending_quality_control_blockers": (
                    n_route_adoption_quality_control_blockers
                ),
                "n_packet_llm_route_adoption_pending_source_grounding_blockers": (
                    n_route_adoption_source_grounding_blockers
                ),
                "by_packet_llm_route_adoption_status": dict(
                    sorted(route_adoption_status_counts.items())
                ),
                "n_packets_with_formal_attempt_dependency": sum(
                    1
                    for packet in target_packet_rows
                    if str(packet.get("formal_attempt_dependency_status", ""))
                    != "not_formal_attempt_queue_item"
                ),
                "n_packets_formal_attempt_initial_ready": (
                    formal_attempt_dependency_status_counts.get(
                        "ready_no_formal_prerequisites",
                        0,
                    )
                ),
                "n_packets_formal_attempt_waiting": (
                    formal_attempt_dependency_status_counts.get(
                        "waiting_for_formal_prerequisite_attempts",
                        0,
                    )
                ),
                "n_packets_formal_attempt_missing_prerequisites": (
                    formal_attempt_dependency_status_counts.get(
                        "missing_formal_prerequisite_attempts",
                        0,
                    )
                ),
                "by_packet_formal_attempt_dependency_status": dict(
                    sorted(formal_attempt_dependency_status_counts.items())
                ),
                "n_response_validation_rows": len(target_response_rows),
                "n_response_minimal_delta_action_witnesses_required": (
                    n_response_minimal_delta_action_witnesses_required
                ),
                "n_response_minimal_delta_action_witnesses_acknowledged": (
                    n_response_minimal_delta_action_witnesses_acknowledged
                ),
                "n_response_minimal_delta_action_witnesses_unacknowledged": (
                    n_response_minimal_delta_action_witnesses_unacknowledged
                ),
                "n_response_addressed_minimal_delta_action_witnesses": (
                    n_response_addressed_minimal_delta_action_witnesses
                ),
                "n_unmatched_adapter_responses": row.n_unmatched_adapter_responses,
                "aggregate_packet_jsonl_path": (
                    "formalization_gap_planner_cross_prover_packets.jsonl"
                ),
                "aggregate_response_validation_jsonl_path": (
                    "formalization_gap_planner_cross_prover_response_validation.jsonl"
                ),
                "packet_filter_field": "target_prover_family",
                "packet_filter_value": target,
                "response_validation_filter_field": "target_prover_family",
                "response_validation_filter_value": target,
                "source_contract_manifest_path": row.contract_manifest_path,
                "ok": row.ok
                and len(target_packet_rows) == row.n_packets
                and len(target_response_rows) == row.n_packets,
                "errors": list(row.errors),
            }
        )
        target_rows[-1]["ok"] = bool(
            target_rows[-1]["ok"]
            and n_packets_with_residual_goal_contexts
            == row.n_packets_with_residual_goal_contexts
            and len(residual_goal_contexts) == row.n_packet_residual_goal_contexts
            and target_rows[-1]["n_packets_with_formal_attempt_dependency"]
            == row.n_packets_with_formal_attempt_dependency
            and target_rows[-1]["n_packets_formal_attempt_initial_ready"]
            == row.n_packets_formal_attempt_initial_ready
            and target_rows[-1]["n_packets_formal_attempt_waiting"]
            == row.n_packets_formal_attempt_waiting
            and target_rows[-1][
                "n_packets_formal_attempt_missing_prerequisites"
            ]
            == row.n_packets_formal_attempt_missing_prerequisites
            and target_rows[-1][
                "n_response_minimal_delta_action_witnesses_required"
            ]
            == row.n_response_minimal_delta_action_witnesses_required
            and target_rows[-1][
                "n_response_minimal_delta_action_witnesses_acknowledged"
            ]
            == row.n_response_minimal_delta_action_witnesses_acknowledged
            and target_rows[-1][
                "n_response_minimal_delta_action_witnesses_unacknowledged"
            ]
            == row.n_response_minimal_delta_action_witnesses_unacknowledged
            and target_rows[-1][
                "n_response_addressed_minimal_delta_action_witnesses"
            ]
            == row.n_response_addressed_minimal_delta_action_witnesses
        )
        if (
            n_packets_with_residual_goal_contexts
            != row.n_packets_with_residual_goal_contexts
        ):
            target_rows[-1]["errors"].append(
                "residual-context packet count mismatch between contract manifest and packet rows"
            )
        if len(residual_goal_contexts) != row.n_packet_residual_goal_contexts:
            target_rows[-1]["errors"].append(
                "residual-context total mismatch between contract manifest and packet rows"
            )
        if (
            target_rows[-1]["n_packets_with_formal_attempt_dependency"]
            != row.n_packets_with_formal_attempt_dependency
            or target_rows[-1]["n_packets_formal_attempt_initial_ready"]
            != row.n_packets_formal_attempt_initial_ready
            or target_rows[-1]["n_packets_formal_attempt_waiting"]
            != row.n_packets_formal_attempt_waiting
            or target_rows[-1][
                "n_packets_formal_attempt_missing_prerequisites"
            ]
            != row.n_packets_formal_attempt_missing_prerequisites
        ):
            target_rows[-1]["errors"].append(
                "formal-attempt dependency count mismatch between contract manifest and packet rows"
            )
        if (
            target_rows[-1]["by_packet_formal_attempt_dependency_status"]
            != row.by_packet_formal_attempt_dependency_status
        ):
            target_rows[-1]["errors"].append(
                "formal-attempt dependency status mismatch between contract manifest and packet rows"
            )
        if (
            target_rows[-1][
                "n_response_minimal_delta_action_witnesses_required"
            ]
            != row.n_response_minimal_delta_action_witnesses_required
            or target_rows[-1][
                "n_response_minimal_delta_action_witnesses_acknowledged"
            ]
            != row.n_response_minimal_delta_action_witnesses_acknowledged
            or target_rows[-1][
                "n_response_minimal_delta_action_witnesses_unacknowledged"
            ]
            != row.n_response_minimal_delta_action_witnesses_unacknowledged
            or target_rows[-1][
                "n_response_addressed_minimal_delta_action_witnesses"
            ]
            != row.n_response_addressed_minimal_delta_action_witnesses
        ):
            target_rows[-1]["errors"].append(
                "minimal-delta witness response count mismatch between contract manifest and response rows"
            )
    summary_errors = [
        f"{target_row['target_prover_family']}: " + "; ".join(
            str(error) for error in target_row.get("errors", [])
        )
        for target_row in target_rows
        if target_row.get("errors")
    ]
    return {
        "schema_version": (
            FORMALIZATION_GAP_PLANNER_CROSS_PROVER_MATRIX_AUDIT_SCHEMA_VERSION
        ),
        "schema_id": CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
        "component_name": "formalization_gap_planner_cross_prover_target_summary",
        "n_target_rows": len(target_rows),
        "n_targets_ok": sum(1 for row in target_rows if row["ok"]),
        "n_total_packets": sum(_int(row["n_packets"]) for row in target_rows),
        "n_total_packets_with_alignment": sum(
            _int(row["n_packets_with_alignment"]) for row in target_rows
        ),
        "n_total_packets_with_standalone_input_trace": sum(
            _int(row["n_packets_with_standalone_input_trace"])
            for row in target_rows
        ),
        "n_total_packets_missing_standalone_input_trace": sum(
            _int(row["n_packets_missing_standalone_input_trace"])
            for row in target_rows
        ),
        "n_total_packets_with_target_library_snapshot_trace": sum(
            _int(row["n_packets_with_target_library_snapshot_trace"])
            for row in target_rows
        ),
        "n_total_packets_missing_target_library_snapshot_trace": sum(
            _int(row["n_packets_missing_target_library_snapshot_trace"])
            for row in target_rows
        ),
        "n_total_packets_target_library_snapshot_mismatch": sum(
            _int(row["n_packets_target_library_snapshot_mismatch"])
            for row in target_rows
        ),
        "n_total_packets_with_replan_metadata_trace": sum(
            _int(row["n_packets_with_replan_metadata_trace"])
            for row in target_rows
        ),
        "n_total_packets_with_residual_goal_contexts": sum(
            _int(row["n_packets_with_residual_goal_contexts"])
            for row in target_rows
        ),
        "n_total_packet_residual_goal_contexts": sum(
            _int(row["n_packet_residual_goal_contexts"]) for row in target_rows
        ),
        "packet_residual_context_source_kinds": (
            _residual_context_source_kinds_from_target_rows(target_rows)
        ),
        "n_total_packet_residual_contexts_with_source_refs": sum(
            _int(row["n_packet_residual_contexts_with_source_refs"])
            for row in target_rows
        ),
        "n_total_packet_residual_contexts_with_formal_gap_boundary": sum(
            _int(row["n_packet_residual_contexts_with_formal_gap_boundary"])
            for row in target_rows
        ),
        "n_total_packets_with_quality_controls": sum(
            _int(row["n_packets_with_quality_controls"]) for row in target_rows
        ),
        "n_total_packet_quality_control_fields": sum(
            _int(row["n_packet_quality_control_fields"]) for row in target_rows
        ),
        "packet_quality_control_fields": _quality_control_fields_from_target_rows(
            target_rows
        ),
        "packet_quality_control_resource_contract_ids": (
            _quality_control_values_from_target_rows(
                target_rows,
                "packet_quality_control_resource_contract_ids",
            )
        ),
        "packet_quality_control_response_validation_signals": (
            _quality_control_values_from_target_rows(
                target_rows,
                "packet_quality_control_response_validation_signals",
            )
        ),
        "packet_quality_control_stop_conditions": (
            _quality_control_values_from_target_rows(
                target_rows,
                "packet_quality_control_stop_conditions",
            )
        ),
        "by_total_packet_quality_control_field": (
            _sum_quality_control_field_summary(target_rows)
        ),
        "n_total_packets_with_llm_route_adoption_status": sum(
            _int(row["n_packets_with_llm_route_adoption_status"])
            for row in target_rows
        ),
        "n_total_packets_llm_route_adoption_ready": sum(
            _int(row["n_packets_llm_route_adoption_ready"]) for row in target_rows
        ),
        "n_total_packets_llm_route_adoption_pending_refinement": sum(
            _int(row["n_packets_llm_route_adoption_pending_refinement"])
            for row in target_rows
        ),
        "n_total_packets_llm_route_adoption_rejected": sum(
            _int(row["n_packets_llm_route_adoption_rejected"])
            for row in target_rows
        ),
        "n_total_packets_llm_route_adoption_awaiting_response": sum(
            _int(row["n_packets_llm_route_adoption_awaiting_response"])
            for row in target_rows
        ),
        "n_total_packet_llm_route_adoption_blockers": sum(
            _int(row["n_packet_llm_route_adoption_blockers"])
            for row in target_rows
        ),
        "n_total_packet_llm_route_adoption_pending_quality_control_blockers": sum(
            _int(
                row[
                    "n_packet_llm_route_adoption_pending_quality_control_blockers"
                ]
            )
            for row in target_rows
        ),
        "n_total_packet_llm_route_adoption_pending_source_grounding_blockers": sum(
            _int(
                row[
                    "n_packet_llm_route_adoption_pending_source_grounding_blockers"
                ]
            )
            for row in target_rows
        ),
        "by_total_packet_llm_route_adoption_status": (
            _sum_route_adoption_status_counts(target_rows)
        ),
        "n_total_packets_with_formal_attempt_dependency": sum(
            _int(row["n_packets_with_formal_attempt_dependency"])
            for row in target_rows
        ),
        "n_total_packets_formal_attempt_initial_ready": sum(
            _int(row["n_packets_formal_attempt_initial_ready"])
            for row in target_rows
        ),
        "n_total_packets_formal_attempt_waiting": sum(
            _int(row["n_packets_formal_attempt_waiting"]) for row in target_rows
        ),
        "n_total_packets_formal_attempt_missing_prerequisites": sum(
            _int(row["n_packets_formal_attempt_missing_prerequisites"])
            for row in target_rows
        ),
        "by_total_packet_formal_attempt_dependency_status": (
            _sum_formal_attempt_dependency_status_counts(target_rows)
        ),
        "n_total_response_minimal_delta_action_witnesses_required": sum(
            _int(row["n_response_minimal_delta_action_witnesses_required"])
            for row in target_rows
        ),
        "n_total_response_minimal_delta_action_witnesses_acknowledged": sum(
            _int(row["n_response_minimal_delta_action_witnesses_acknowledged"])
            for row in target_rows
        ),
        "n_total_response_minimal_delta_action_witnesses_unacknowledged": sum(
            _int(row["n_response_minimal_delta_action_witnesses_unacknowledged"])
            for row in target_rows
        ),
        "n_total_response_addressed_minimal_delta_action_witnesses": sum(
            _int(row["n_response_addressed_minimal_delta_action_witnesses"])
            for row in target_rows
        ),
        "n_unmatched_adapter_responses": sum(
            _int(row.get("n_unmatched_adapter_responses")) for row in target_rows
        ),
        "target_rows": target_rows,
        "target_summary_fingerprint": stable_hash(target_rows),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "Cross-prover target summaries are reusable packet-discovery "
            "metadata for target prover adapters. They are not theorem proof "
            "evidence."
        ),
        "all_ok": bool(target_rows)
        and not summary_errors
        and all(bool(row["ok"]) for row in target_rows)
        and sum(
            _int(row["n_packets_missing_standalone_input_trace"])
            for row in target_rows
        )
        == 0
        and sum(
            _int(row["n_packets_missing_target_library_snapshot_trace"])
            for row in target_rows
        )
        == 0
        and sum(
            _int(row["n_packets_target_library_snapshot_mismatch"])
            for row in target_rows
        )
        == 0
        and sum(
            _int(row.get("n_unmatched_adapter_responses")) for row in target_rows
        )
        == 0,
        "errors": summary_errors,
    }


def _target_families(
    target_prover_families: tuple[str, ...],
    errors: list[str],
) -> tuple[str, ...]:
    targets: list[str] = []
    for raw_target in target_prover_families or DEFAULT_REUSE_TARGETS:
        target = _normalize_target(raw_target)
        if target not in PROVER_FAMILIES:
            errors.append(f"unsupported target prover family in matrix: {raw_target}")
            continue
        if target == "other":
            errors.append("cross-prover matrix requires concrete target families, not other")
            continue
        if target not in targets:
            targets.append(target)
    return tuple(targets)


def _sum_route_adoption_status_counts(
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        raw_counts = row.get("by_packet_llm_route_adoption_status", {})
        if not isinstance(raw_counts, dict):
            continue
        for status, count in raw_counts.items():
            status_text = str(status)
            if status_text:
                counts[status_text] += _int(count)
    return dict(sorted(counts.items()))


def _sum_formal_attempt_dependency_status_counts(
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        raw_counts = row.get("by_packet_formal_attempt_dependency_status", {})
        if not isinstance(raw_counts, dict):
            continue
        for status, count in raw_counts.items():
            status_text = str(status)
            if status_text:
                counts[status_text] += _int(count)
    return dict(sorted(counts.items()))


def _residual_goal_contexts_from_packet_row(
    packet: dict[str, Any],
) -> tuple[dict[str, object], ...]:
    contexts = _normalize_residual_goal_contexts(
        _dict_tuple(packet.get("residual_goal_contexts", []))
    )
    if contexts:
        return contexts
    trace = packet.get("standalone_input_trace", {})
    if not isinstance(trace, dict):
        return tuple()
    return _normalize_residual_goal_contexts(
        _dict_tuple(trace.get("residual_goal_contexts", []))
    )


def _normalize_residual_goal_contexts(
    contexts: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    normalized_contexts: list[dict[str, object]] = []
    seen: set[str] = set()
    for context in contexts:
        normalized = {
            str(field_name): value
            for field_name, value in context.items()
            if str(field_name)
        }
        for field_name in (
            "residual_goals",
            "residual_primitives",
            "target_primitives",
            "source_refs",
            "queries",
            "source_search_queries",
            "literature_queries",
        ):
            if field_name in normalized:
                normalized[field_name] = _str_tuple(normalized.get(field_name, []))
        for field_name in (
            "source_kind",
            "residual_goal",
            "interpretation",
            "route_repair",
            "repair_action",
            "source_search_status",
            "formal_gap_boundary",
            "formal_boundary",
            "source_ref",
        ):
            if field_name in normalized:
                normalized[field_name] = str(normalized.get(field_name, "")).strip()
        if "source_snippets" in normalized:
            normalized["source_snippets"] = _dict_tuple(
                normalized.get("source_snippets", [])
            )
        normalized = {
            field_name: value
            for field_name, value in normalized.items()
            if _residual_context_value_present(value)
        }
        if not normalized:
            continue
        key = stable_hash(normalized)
        if key in seen:
            continue
        seen.add(key)
        normalized_contexts.append(normalized)
    return tuple(normalized_contexts)


def _residual_context_value_present(value: object) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, (list, tuple, set, dict)) and not value:
        return False
    return True


def _residual_context_source_kinds(
    contexts: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(context.get("source_kind", "")).strip()
                for context in contexts
                if str(context.get("source_kind", "")).strip()
            }
        )
    )


def _matrix_residual_context_source_kinds(
    rows: list[FormalizationGapPlannerCrossProverMatrixRow],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                source_kind
                for row in rows
                for source_kind in row.packet_residual_context_source_kinds
                if source_kind
            }
        )
    )


def _residual_context_source_kinds_from_target_rows(
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                source_kind
                for row in rows
                for source_kind in _str_tuple(
                    row.get("packet_residual_context_source_kinds", [])
                )
                if source_kind
            }
        )
    )


def _residual_context_has_sources(context: dict[str, object]) -> bool:
    return bool(
        _str_tuple(context.get("source_refs", []))
        or _dict_tuple(context.get("source_snippets", []))
        or str(context.get("source_ref", "")).strip()
    )


def _residual_context_has_formal_gap_boundary(context: dict[str, object]) -> bool:
    return bool(
        str(
            context.get("formal_gap_boundary", "")
            or context.get("formal_boundary", "")
        ).strip()
    )


def _quality_controls_from_packet_row(
    packet: dict[str, Any],
) -> dict[str, tuple[str, ...]]:
    trace = packet.get("standalone_input_trace", {})
    if not isinstance(trace, dict):
        return {}
    raw_controls = trace.get("quality_controls", {})
    if not isinstance(raw_controls, dict):
        return {}
    controls: dict[str, tuple[str, ...]] = {}
    for field_name in QUALITY_CONTROL_FIELDS:
        values = _str_tuple(raw_controls.get(field_name, []))
        if values:
            controls[field_name] = values
    return controls


def _packet_target_library_snapshot_value(packet: dict[str, Any]) -> str:
    trace = packet.get("standalone_input_trace", {})
    if not isinstance(trace, dict):
        return ""
    return str(
        trace.get("target_library_snapshot_ref", "")
        or trace.get("library_snapshot_ref", "")
    ).strip()


def _packet_has_target_library_snapshot_trace(packet: dict[str, Any]) -> bool:
    return bool(_packet_target_library_snapshot_value(packet))


def _packet_target_library_snapshot_mismatch(packet: dict[str, Any]) -> bool:
    observed = _packet_target_library_snapshot_value(packet)
    expected = str(packet.get("library_snapshot_ref", "")).strip()
    return bool(observed and expected and observed != expected)


def _quality_control_fields_from_packet_rows(
    packets: list[dict[str, Any]],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                field_name
                for packet in packets
                for field_name in _quality_controls_from_packet_row(packet)
            }
        )
    )


def _quality_control_values_from_packet_rows(
    packets: list[dict[str, Any]],
    field_name: str,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                value
                for packet in packets
                for value in _quality_controls_from_packet_row(packet).get(
                    field_name,
                    tuple(),
                )
                if value
            }
        )
    )


def _quality_control_field_summary_from_packet_rows(
    packets: list[dict[str, Any]],
) -> dict[str, dict[str, object]]:
    return {
        field_name: {
            "n_packets": sum(
                1
                for packet in packets
                if field_name in _quality_controls_from_packet_row(packet)
            ),
            "n_values": len(
                _quality_control_values_from_packet_rows(packets, field_name)
            ),
            "values": _quality_control_values_from_packet_rows(packets, field_name),
        }
        for field_name in _quality_control_fields_from_packet_rows(packets)
    }


def _matrix_quality_control_fields(
    rows: list[FormalizationGapPlannerCrossProverMatrixRow],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                field_name
                for row in rows
                for field_name in row.packet_quality_control_fields
            }
        )
    )


def _matrix_quality_control_values(
    rows: list[FormalizationGapPlannerCrossProverMatrixRow],
    attr_name: str,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                value
                for row in rows
                for value in getattr(row, attr_name)
                if str(value)
            }
        )
    )


def _quality_control_fields_from_target_rows(
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                field_name
                for row in rows
                for field_name in _str_tuple(
                    row.get("packet_quality_control_fields", [])
                )
            }
        )
    )


def _quality_control_values_from_target_rows(
    rows: list[dict[str, Any]],
    field_name: str,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                value
                for row in rows
                for value in _str_tuple(row.get(field_name, []))
                if value
            }
        )
    )


def _sum_quality_control_field_summary(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, object]]:
    summaries = [
        row.get("by_packet_quality_control_field", {})
        for row in rows
        if isinstance(row.get("by_packet_quality_control_field", {}), dict)
    ]
    field_names = sorted(
        {
            str(field_name)
            for summary in summaries
            for field_name in summary
            if str(field_name)
        }
    )
    merged: dict[str, dict[str, object]] = {}
    for field_name in field_names:
        n_packets = 0
        values: set[str] = set()
        for summary in summaries:
            field_summary = summary.get(field_name, {})
            if not isinstance(field_summary, dict):
                continue
            n_packets += _int(field_summary.get("n_packets"))
            values.update(_str_tuple(field_summary.get("values", [])))
        merged[field_name] = {
            "n_packets": n_packets,
            "n_values": len(values),
            "values": tuple(sorted(values)),
        }
    return merged


def _normalize_quality_control_field_summary(
    value: Any,
) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, dict[str, object]] = {}
    for field_name, summary in value.items():
        if not isinstance(summary, dict):
            continue
        values = tuple(sorted(_str_tuple(summary.get("values", []))))
        normalized[str(field_name)] = {
            "n_packets": _int(summary.get("n_packets")),
            "n_values": _int(summary.get("n_values")),
            "values": values,
        }
    return dict(sorted(normalized.items()))


def _normalize_target(raw_target: str) -> str:
    normalized = str(raw_target).strip().lower()
    aliases = {
        "lean": "lean4",
        "lean4": "lean4",
        "coq": "rocq",
        "rocq": "rocq",
        "isabelle/hol": "isabelle",
        "isabelle": "isabelle",
        "agda": "agda",
        "other": "other",
    }
    return aliases.get(normalized, normalized)


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str):
        return (value,) if value else tuple()
    if isinstance(value, dict):
        return tuple()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),) if str(value) else tuple()


def _dict_tuple(value: Any) -> tuple[dict[str, object], ...]:
    if isinstance(value, dict):
        return (dict(value),)
    if not isinstance(value, (list, tuple, set)):
        return tuple()
    return tuple(dict(item) for item in value if isinstance(item, dict))


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _schema_property_errors(
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_type = field_schema.get("type")
    if expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field_name} must be integer")
    elif expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be string")
        elif field_schema.get("minLength") and len(value) < int(
            field_schema["minLength"]
        ):
            errors.append(f"{field_name} must be non-empty")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_name} must be boolean")
    elif expected_type == "array":
        if not isinstance(value, (list, tuple)):
            errors.append(f"{field_name} must be array")
        else:
            item_schema = field_schema.get("items", {})
            if isinstance(item_schema, dict) and item_schema.get("type") == "string":
                non_strings = [
                    idx for idx, item in enumerate(value) if not isinstance(item, str)
                ]
                if non_strings:
                    errors.append(
                        f"{field_name} items must be string at indexes "
                        + ",".join(str(idx) for idx in non_strings)
                    )
    if "enum" in field_schema and isinstance(field_schema["enum"], list):
        if value not in field_schema["enum"]:
            errors.append(
                f"{field_name} must be one of "
                + ",".join(str(item) for item in field_schema["enum"])
            )
    if "const" in field_schema and value != field_schema["const"]:
        errors.append(f"{field_name} must equal {field_schema['const']!r}")
    pattern = field_schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str):
        if re.search(pattern, value) is None:
            errors.append(f"{field_name} must match /{pattern}/")
    return tuple(errors)


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Cross-Prover Matrix Audit",
        "",
        f"- Targets: {payload.get('n_targets_ok')}/{payload.get('n_targets')}",
        f"- Matrix row schema valid: {payload.get('n_matrix_row_schema_valid')}/{payload.get('n_targets')}",
        f"- Total packets: {payload.get('n_total_packet_ok')}/{payload.get('n_total_packets')}",
        f"- Packet schema valid: {payload.get('n_total_packet_schema_valid')}/{payload.get('n_total_packets')}",
        f"- Aggregated packet row schema valid: {payload.get('n_packet_row_schema_valid')}/{payload.get('n_total_packets')}",
        f"- Response validation row schema valid: {payload.get('n_response_validation_row_schema_valid')}/{payload.get('n_total_packets')}",
        f"- Target summary contract errors: {payload.get('n_target_summary_contract_errors')}",
        f"- Packets with alignment: {payload.get('n_total_packets_with_alignment')}/{payload.get('n_total_packets')}",
        f"- Packets with standalone trace: {payload.get('n_total_packets_with_standalone_input_trace')}/{payload.get('n_total_packets')}",
        f"- Packets with replan metadata trace: {payload.get('n_total_packets_with_replan_metadata_trace')}/{payload.get('n_total_packets')}",
        f"- Packets with residual goal contexts: {payload.get('n_total_packets_with_residual_goal_contexts')}/{payload.get('n_total_packets')}",
        f"- Residual goal contexts: {payload.get('n_total_packet_residual_goal_contexts')}",
        f"- Residual context source kinds: {payload.get('packet_residual_context_source_kinds')}",
        f"- Packets with quality controls: {payload.get('n_total_packets_with_quality_controls')}/{payload.get('n_total_packets')}",
        f"- Packet quality-control fields: {payload.get('packet_quality_control_fields')}",
        f"- Packets with LLM route-adoption status: {payload.get('n_total_packets_with_llm_route_adoption_status')}/{payload.get('n_total_packets')}",
        f"- LLM route-adoption ready packets: {payload.get('n_total_packets_llm_route_adoption_ready')}",
        f"- LLM route-adoption pending packets: {payload.get('n_total_packets_llm_route_adoption_pending_refinement')}",
        f"- LLM route-adoption blockers: {payload.get('n_total_packet_llm_route_adoption_blockers')}",
        "- LLM route-adoption pending quality-control blockers: "
        f"{payload.get('n_total_packet_llm_route_adoption_pending_quality_control_blockers')}",
        "- LLM route-adoption pending source-grounding blockers: "
        f"{payload.get('n_total_packet_llm_route_adoption_pending_source_grounding_blockers')}",
        f"- Packets with formal-attempt dependency: {payload.get('n_total_packets_with_formal_attempt_dependency')}/{payload.get('n_total_packets')}",
        f"- Formal-attempt initially ready packets: {payload.get('n_total_packets_formal_attempt_initial_ready')}",
        f"- Formal-attempt waiting packets: {payload.get('n_total_packets_formal_attempt_waiting')}",
        f"- Formal-attempt missing-prerequisite packets: {payload.get('n_total_packets_formal_attempt_missing_prerequisites')}",
        "- Response minimal-delta witness acknowledgements: "
        f"{payload.get('n_response_minimal_delta_action_witnesses_acknowledged')}/"
        f"{payload.get('n_response_minimal_delta_action_witnesses_required')}",
        "- Response minimal-delta witness unacknowledged: "
        f"{payload.get('n_response_minimal_delta_action_witnesses_unacknowledged')}",
        "- Response addressed minimal-delta witnesses: "
        f"{payload.get('n_response_addressed_minimal_delta_action_witnesses')}",
        f"- Awaiting adapter mappings: {payload.get('n_awaiting_adapter_mapping')}",
        f"- Rejected mappings: {payload.get('n_rejected')}",
        f"- Packet count consistent: {payload.get('packet_count_consistent')}",
        f"- Alignment packet count consistent: {payload.get('alignment_packet_count_consistent')}",
        f"- Standalone trace packet count consistent: {payload.get('standalone_input_trace_packet_count_consistent')}",
        f"- Quality-control packet count consistent: {payload.get('quality_control_packet_count_consistent')}",
        f"- Residual-context packet count consistent: {payload.get('residual_context_packet_count_consistent')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Targets",
        "",
    ]
    for row in payload.get("matrix_rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('target_prover_family')}` packets="
            f"{row.get('n_packet_ok')}/{row.get('n_packets')} "
            f"schema={row.get('n_packet_schema_valid')}/{row.get('n_packets')} "
            f"aligned={row.get('n_packets_with_alignment')}/{row.get('n_packets')} "
            f"trace={row.get('n_packets_with_standalone_input_trace')}/{row.get('n_packets')} "
            f"residual_contexts={row.get('n_packets_with_residual_goal_contexts')}/{row.get('n_packets')} "
            f"quality_controls={row.get('n_packets_with_quality_controls')}/{row.get('n_packets')} "
            f"llm_status={row.get('n_packets_with_llm_route_adoption_status')} "
            f"formal_attempt_waiting={row.get('n_packets_formal_attempt_waiting')} "
            f"awaiting={row.get('n_awaiting_adapter_mapping')} "
            f"ok={row.get('ok')}"
        )
    return "\n".join(lines) + "\n"

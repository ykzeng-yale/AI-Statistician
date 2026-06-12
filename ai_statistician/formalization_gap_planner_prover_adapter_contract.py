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
    route_alignment_edge_json_schema,
    validate_route_alignment_edge,
)


FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_SCHEMA_VERSION = 1
PROVER_ADAPTER_PACKET_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-prover-adapter-packet:1"
)
PROVER_ADAPTER_RESPONSE_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-prover-adapter-response:1"
)
PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID = (
    "urn:ai-statistician:schemas:"
    "formalization-gap-planner-prover-adapter-response-validation-row:1"
)
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_NOT_PROOF_EVIDENCE"
)
PROOF_EVIDENCE_BOUNDARY = (
    "Formalization gap planner prover-adapter contract rows are translation "
    "and replay-planning records. They map portable work packets into a target "
    "prover ecosystem, but they are not theorem proof evidence. A theorem or "
    "bridge lemma is proved only when that target prover's kernel verifies the "
    "translated statement and proof with no placeholders."
)
PROVER_FAMILIES = ("lean4", "rocq", "isabelle", "agda", "other")
PROVER_FAMILY_RESPONSE_VALUES = (
    "lean4",
    "lean",
    "rocq",
    "coq",
    "coq8",
    "coq_8",
    "isabelle",
    "isabelle/hol",
    "isabelle_hol",
    "agda",
    "other",
)
MAPPING_STATUSES = (
    "ready_for_kernel_attempt",
    "needs_statement_translation",
    "needs_library_grounding",
    "unsupported_in_target_prover",
    "needs_human_review",
)
FORBIDDEN_PLACEHOLDER_RE = re.compile(
    r"\b(sorry|admit|axiom|admitted|undefined|todo|placeholder)\b",
    flags=re.IGNORECASE,
)
QUALITY_CONTROL_FIELDS = (
    "resource_contract_ids",
    "required_quality_signals",
    "quality_gates",
    "response_validation_signals",
    "stop_conditions",
)
ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS = "quality_control_obligations_pending"
ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING = "source_grounding_obligations_pending"


@dataclass(frozen=True)
class FormalizationGapPlannerProverAdapterPacket:
    schema_version: int
    prover_adapter_packet_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    packet_index: int
    primitive: str
    action_class: str
    worker_packet_kind: str
    expected_cost: str
    required_gate: str
    source_prover_family: str
    target_prover_family: str
    library_snapshot_ref: str
    portable_work_packet: dict[str, object]
    route_alignment_edge: dict[str, object]
    standalone_input_trace: dict[str, object]
    llm_route_planner_route_adoption_status: str
    llm_route_planner_route_adoption_blockers: tuple[str, ...]
    alignment_status: str
    informal_route_node_id: str
    formal_realization_node_id: str
    required_adapter_response_fields: tuple[str, ...]
    acceptance_gate: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormalizationGapPlannerProverAdapterResponseValidationRow:
    schema_version: int
    response_validation_id: str
    prover_adapter_packet_id: str
    goal_plan_id: str
    route_id: str
    display_name: str
    primitive: str
    target_prover_family: str
    response_present: bool
    response_contract_ok: bool
    mapping_status: str
    translated_statement: str
    translated_imports: tuple[str, ...]
    verifier_command: str
    library_snapshot_ref: str
    semantic_alignment_notes: str
    residual_translation_gaps: tuple[str, ...]
    kernel_verified_claimed: bool
    acceptance_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formalization_gap_planner_prover_adapter_contract(
    goal_conditioned_minimal_formalization_plan_dir: Path,
    out_dir: Path | None = None,
    *,
    target_prover_family: str = "other",
    library_snapshot_ref: str = "",
    adapter_response_jsonl: Path | None = None,
    max_packets: int = 0,
) -> dict[str, object]:
    """Export and validate target-prover mappings for portable work packets."""

    errors: list[str] = []
    plan_manifest_path = (
        goal_conditioned_minimal_formalization_plan_dir
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    )
    plan_payload = _read_json(plan_manifest_path, errors)
    if plan_payload.get("component_name") != LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME:
        errors.append("input manifest is not the library-aware formalization gap planner")
    if plan_payload.get("portable_schema_id") != PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID:
        errors.append("input manifest portable schema id mismatch")
    target_family = _normalize_prover_family(target_prover_family)
    if target_family not in PROVER_FAMILIES:
        errors.append(f"unsupported target_prover_family: {target_prover_family}")
    packets = [
        packet
        for row in plan_payload.get("rows", [])
        if isinstance(row, dict)
        for packet in _packets_for_plan_row(
            row,
            target_prover_family=target_family,
            library_snapshot_ref=library_snapshot_ref
            or str(plan_payload.get("library_snapshot_ref", "")),
        )
    ]
    if max_packets > 0:
        packets = packets[:max_packets]
    response_rows_raw, response_file_exists = _read_response_jsonl(
        adapter_response_jsonl,
        errors,
    )
    response_by_key = _response_index(response_rows_raw, errors)
    unmatched_response_errors = _unmatched_response_errors(response_rows_raw, packets)
    errors.extend(unmatched_response_errors)
    validations = [
        _validate_response(packet, _response_for_packet(packet, response_by_key))
        for packet in packets
    ]
    packet_schema = prover_adapter_packet_json_schema()
    response_validation_row_schema = (
        prover_adapter_response_validation_row_json_schema()
    )
    packet_schema_errors = {
        packet.prover_adapter_packet_id: validate_prover_adapter_packet_row(
            asdict(packet),
            packet_schema,
        )
        for packet in packets
    }
    response_validation_row_schema_errors = {
        row.response_validation_id: validate_prover_adapter_response_validation_row(
            asdict(row),
            response_validation_row_schema,
        )
        for row in validations
    }
    by_mapping_status = Counter(row.mapping_status for row in validations)
    by_acceptance_status = Counter(row.acceptance_status for row in validations)
    packet_quality_control_fields = _packet_quality_control_fields(packets)
    packet_quality_control_resource_contract_ids = _packet_quality_control_values(
        packets,
        "resource_contract_ids",
    )
    packet_quality_control_response_validation_signals = (
        _packet_quality_control_values(
            packets,
            "response_validation_signals",
        )
    )
    packet_quality_control_stop_conditions = _packet_quality_control_values(
        packets,
        "stop_conditions",
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_prover_adapter_contract",
        "source_component": plan_payload.get("component_name", ""),
        "portable_schema_id": plan_payload.get("portable_schema_id", ""),
        "goal_conditioned_minimal_formalization_plan_dir": str(
            goal_conditioned_minimal_formalization_plan_dir
        ),
        "goal_conditioned_minimal_formalization_plan_manifest": str(plan_manifest_path),
        "target_prover_family": target_family,
        "target_library_snapshot_ref": library_snapshot_ref,
        "adapter_response_jsonl": str(adapter_response_jsonl or ""),
        "adapter_response_jsonl_exists": response_file_exists,
        "n_plan_rows": len(
            [row for row in plan_payload.get("rows", []) if isinstance(row, dict)]
        ),
        "n_packets": len(packets),
        "n_packet_ok": sum(1 for packet in packets if packet.ok),
        "n_packet_schema_valid": sum(
            1
            for packet in packets
            if not packet_schema_errors.get(packet.prover_adapter_packet_id, ())
        ),
        "n_packets_with_alignment": sum(
            1 for packet in packets if packet.route_alignment_edge
        ),
        "n_packets_with_standalone_input_trace": sum(
            1 for packet in packets if packet.standalone_input_trace
        ),
        "n_packets_missing_standalone_input_trace": sum(
            1 for packet in packets if not packet.standalone_input_trace
        ),
        "n_packets_with_replan_metadata_trace": sum(
            1
            for packet in packets
            if packet.standalone_input_trace.get("has_replan_metadata")
        ),
        "n_packets_with_quality_controls": sum(
            1 for packet in packets if _quality_controls_from_packet_trace(packet)
        ),
        "n_packet_quality_control_fields": sum(
            len(_quality_controls_from_packet_trace(packet)) for packet in packets
        ),
        "packet_quality_control_fields": packet_quality_control_fields,
        "packet_quality_control_resource_contract_ids": (
            packet_quality_control_resource_contract_ids
        ),
        "packet_quality_control_response_validation_signals": (
            packet_quality_control_response_validation_signals
        ),
        "packet_quality_control_stop_conditions": (
            packet_quality_control_stop_conditions
        ),
        "by_packet_quality_control_field": _packet_quality_control_field_summary(
            packets
        ),
        "n_packets_with_llm_route_adoption_status": sum(
            1 for packet in packets if packet.llm_route_planner_route_adoption_status
        ),
        "n_packets_llm_route_adoption_ready": sum(
            1
            for packet in packets
            if packet.llm_route_planner_route_adoption_status
            == "READY_FOR_STANDALONE_REPLAY"
        ),
        "n_packets_llm_route_adoption_pending_refinement": sum(
            1
            for packet in packets
            if packet.llm_route_planner_route_adoption_status
            == "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
        ),
        "n_packets_llm_route_adoption_rejected": sum(
            1
            for packet in packets
            if packet.llm_route_planner_route_adoption_status
            == "REJECTED_LLM_ROUTE_PLAN"
        ),
        "n_packets_llm_route_adoption_awaiting_response": sum(
            1
            for packet in packets
            if packet.llm_route_planner_route_adoption_status
            == "AWAITING_LLM_ROUTE_PLANNER_RESPONSE"
        ),
        "n_packet_llm_route_adoption_blockers": sum(
            len(packet.llm_route_planner_route_adoption_blockers)
            for packet in packets
        ),
        "n_packet_llm_route_adoption_pending_quality_control_blockers": sum(
            1
            for packet in packets
            if ROUTE_ADOPTION_BLOCKER_QUALITY_CONTROLS
            in packet.llm_route_planner_route_adoption_blockers
        ),
        "n_packet_llm_route_adoption_pending_source_grounding_blockers": sum(
            1
            for packet in packets
            if ROUTE_ADOPTION_BLOCKER_SOURCE_GROUNDING
            in packet.llm_route_planner_route_adoption_blockers
        ),
        "by_packet_llm_route_adoption_status": dict(
            sorted(
                Counter(
                    packet.llm_route_planner_route_adoption_status
                    for packet in packets
                    if packet.llm_route_planner_route_adoption_status
                ).items()
            )
        ),
        "n_responses": len(response_rows_raw),
        "n_unmatched_adapter_responses": len(unmatched_response_errors),
        "n_response_present": sum(1 for row in validations if row.response_present),
        "n_awaiting_adapter_mapping": sum(
            1 for row in validations if row.acceptance_status == "AWAITING_PROVER_ADAPTER_MAPPING"
        ),
        "n_response_contract_ok": sum(1 for row in validations if row.response_contract_ok),
        "n_response_validation_row_schema_valid": sum(
            1
            for row in validations
            if not response_validation_row_schema_errors.get(
                row.response_validation_id, ()
            )
        ),
        "n_response_validation_row_schema_invalid": sum(
            1
            for row in validations
            if response_validation_row_schema_errors.get(row.response_validation_id, ())
        ),
        "n_rejected": sum(
            1 for row in validations if row.acceptance_status.startswith("REJECTED_")
        ),
        "n_kernel_verified_claims_rejected": sum(
            1 for row in validations if row.kernel_verified_claimed and not row.ok
        ),
        "by_mapping_status": dict(sorted(by_mapping_status.items())),
        "by_acceptance_status": dict(sorted(by_acceptance_status.items())),
        "packets": [asdict(packet) for packet in packets],
        "response_validation_rows": [asdict(row) for row in validations],
        "prover_adapter_packet_schema": packet_schema,
        "prover_adapter_response_schema": prover_adapter_response_json_schema(),
        "prover_adapter_response_validation_row_schema": response_validation_row_schema,
        "packet_fingerprint": stable_hash([asdict(packet) for packet in packets]),
        "response_validation_fingerprint": stable_hash(
            [asdict(row) for row in validations]
        ),
        "all_ok": (
            not errors
            and bool(packets)
            and all(packet.ok for packet in packets)
            and all(
                not packet_schema_errors.get(packet.prover_adapter_packet_id, ())
                for packet in packets
            )
            and all(
                not response_validation_row_schema_errors.get(
                    row.response_validation_id, ()
                )
                for row in validations
            )
            and all(packet.standalone_input_trace for packet in packets)
            and all(row.ok for row in validations)
        ),
        "errors": errors,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "planner_proof_evidence_boundary": PLANNER_PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "adapter mappings are statement/work-packet translations, not proof evidence",
            "every adapter response row must resolve to one exported packet by packet id or goal/route/primitive fallback",
            "kernel_verified=true claims are rejected by this contract validator and must be handled by a separate target-prover replay/calibration gate",
            "semantic equivalence between source and target prover statements still requires expert or mechanized review",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = (
            out_dir / "formalization_gap_planner_prover_adapter_contract_manifest.json"
        )
        packet_path = out_dir / "formalization_gap_planner_prover_adapter_packets.jsonl"
        validation_path = (
            out_dir / "formalization_gap_planner_prover_adapter_response_validation.jsonl"
        )
        response_schema_path = (
            out_dir / "formalization_gap_planner_prover_adapter_response.schema.json"
        )
        response_validation_row_schema_path = (
            out_dir
            / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
        )
        packet_schema_path = (
            out_dir / "formalization_gap_planner_prover_adapter_packet.schema.json"
        )
        payload["manifest_path"] = str(manifest_path)
        payload["packet_jsonl"] = str(packet_path)
        payload["response_validation_jsonl"] = str(validation_path)
        payload["response_schema_path"] = str(response_schema_path)
        payload["response_validation_row_schema_path"] = str(
            response_validation_row_schema_path
        )
        payload["packet_schema_path"] = str(packet_schema_path)
        manifest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        packet_path.write_text(
            "\n".join(json.dumps(asdict(packet), sort_keys=True) for packet in packets)
            + ("\n" if packets else ""),
            encoding="utf-8",
        )
        validation_path.write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in validations)
            + ("\n" if validations else ""),
            encoding="utf-8",
        )
        response_schema_path.write_text(
            json.dumps(prover_adapter_response_json_schema(), indent=2),
            encoding="utf-8",
        )
        response_validation_row_schema_path.write_text(
            json.dumps(response_validation_row_schema, indent=2),
            encoding="utf-8",
        )
        packet_schema_path.write_text(
            json.dumps(packet_schema, indent=2),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_prover_adapter_contract.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def prover_adapter_packet_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    quality_controls_def = {
        "type": "object",
        "additionalProperties": True,
        "properties": {
            field_name: string_array for field_name in QUALITY_CONTROL_FIELDS
        },
    }
    route_alignment_edge_def = dict(route_alignment_edge_json_schema())
    route_alignment_edge_def.pop("$schema", None)
    standalone_input_trace_def = {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "source_prover_family",
            "target_prover_family",
        ],
        "properties": {
            "source_prover_family": {"type": "string", "minLength": 1},
            "source_target_prover_family": {"type": "string"},
            "target_prover_family": {"enum": list(PROVER_FAMILIES)},
            "target_library_snapshot_ref": {"type": "string"},
            "trace_target_projection": {"type": "string"},
            "quality_controls": quality_controls_def,
            "has_quality_controls": {"type": "boolean"},
            "quality_control_fields": string_array,
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PROVER_ADAPTER_PACKET_SCHEMA_ID,
        "title": "Formalization Gap Planner Prover Adapter Packet",
        "description": (
            "Incoming packet contract for target-prover adapters consuming "
            "portable formalization-gap work packets. Rows are not theorem "
            "proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "prover_adapter_packet_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "packet_index",
            "primitive",
            "action_class",
            "worker_packet_kind",
            "required_gate",
            "source_prover_family",
            "target_prover_family",
            "library_snapshot_ref",
            "portable_work_packet",
            "route_alignment_edge",
            "standalone_input_trace",
            "llm_route_planner_route_adoption_status",
            "llm_route_planner_route_adoption_blockers",
            "alignment_status",
            "informal_route_node_id",
            "formal_realization_node_id",
            "required_adapter_response_fields",
            "acceptance_gate",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_SCHEMA_VERSION,
            },
            "prover_adapter_packet_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "packet_index": {"type": "integer"},
            "primitive": {"type": "string", "minLength": 1},
            "action_class": {"type": "string", "minLength": 1},
            "worker_packet_kind": {"type": "string", "minLength": 1},
            "expected_cost": {"type": "string"},
            "required_gate": {"type": "string", "minLength": 1},
            "source_prover_family": {"type": "string", "minLength": 1},
            "target_prover_family": {"enum": list(PROVER_FAMILIES)},
            "library_snapshot_ref": {"type": "string"},
            "portable_work_packet": {"type": "object"},
            "route_alignment_edge": {"$ref": "#/$defs/route_alignment_edge"},
            "standalone_input_trace": {"$ref": "#/$defs/standalone_input_trace"},
            "llm_route_planner_route_adoption_status": {"type": "string"},
            "llm_route_planner_route_adoption_blockers": string_array,
            "alignment_status": {"type": "string", "minLength": 1},
            "informal_route_node_id": {"type": "string", "minLength": 1},
            "formal_realization_node_id": {"type": "string", "minLength": 1},
            "required_adapter_response_fields": string_array,
            "acceptance_gate": {"type": "string", "minLength": 1},
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
        "$defs": {
            "route_alignment_edge": route_alignment_edge_def,
            "standalone_input_trace": standalone_input_trace_def,
        },
    }


def validate_prover_adapter_packet_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    packet_schema = schema or prover_adapter_packet_json_schema()
    errors: list[str] = []
    required = packet_schema.get("required", [])
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in row:
                errors.append(f"{field_name} required")
    properties = packet_schema.get("properties", {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if not isinstance(field_name, str) or field_name not in row:
                continue
            if isinstance(field_schema, dict):
                errors.extend(
                    _schema_property_errors(field_name, row[field_name], field_schema)
                )
    alignment_edge = row.get("route_alignment_edge", {})
    if isinstance(alignment_edge, dict):
        errors.extend(
            f"route_alignment_edge.{error}"
            for error in validate_route_alignment_edge(alignment_edge)
        )
    else:
        errors.append("route_alignment_edge must be an object")
    standalone_input_trace = row.get("standalone_input_trace", {})
    if isinstance(standalone_input_trace, dict):
        errors.extend(
            _standalone_trace_target_errors(
                standalone_input_trace,
                source_prover_family=str(row.get("source_prover_family", "")),
                target_prover_family=str(row.get("target_prover_family", "")),
            )
        )
        errors.extend(_standalone_trace_quality_control_errors(standalone_input_trace))
    else:
        errors.append("standalone_input_trace must be an object")
    return tuple(errors)


def prover_adapter_response_json_schema() -> dict[str, object]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PROVER_ADAPTER_RESPONSE_SCHEMA_ID,
        "title": "Formalization Gap Planner Prover Adapter Response",
        "description": (
            "Response contract for mapping portable formalization-gap work packets "
            "to a target prover ecosystem. Rows are not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "target_prover_family",
            "primitive",
            "mapping_status",
            "translated_statement",
            "translated_imports",
            "verifier_command",
            "library_snapshot_ref",
            "semantic_alignment_notes",
            "kernel_verified",
        ],
        "properties": {
            "prover_adapter_packet_id": {"type": "string"},
            "goal_plan_id": {"type": "string"},
            "route_id": {"type": "string"},
            "primitive": {"type": "string", "minLength": 1},
            "target_prover_family": {"enum": list(PROVER_FAMILY_RESPONSE_VALUES)},
            "mapping_status": {"enum": list(MAPPING_STATUSES)},
            "translated_statement": {"type": "string"},
            "translated_imports": {
                "type": "array",
                "items": {"type": "string"},
            },
            "verifier_command": {"type": "string"},
            "library_snapshot_ref": {"type": "string"},
            "semantic_alignment_notes": {"type": "string"},
            "residual_translation_gaps": {
                "type": "array",
                "items": {"type": "string"},
            },
            "kernel_verified": {"const": False},
        },
    }


def prover_adapter_response_validation_row_json_schema() -> dict[str, object]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID,
        "title": "Formalization Gap Planner Prover Adapter Response Validation Row",
        "description": (
            "Validation row for a target-prover adapter response to one portable "
            "formalization-gap work packet. Rows are mapping diagnostics and are "
            "not theorem proof evidence."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": [
            "schema_version",
            "response_validation_id",
            "prover_adapter_packet_id",
            "goal_plan_id",
            "route_id",
            "display_name",
            "primitive",
            "target_prover_family",
            "response_present",
            "response_contract_ok",
            "mapping_status",
            "translated_statement",
            "translated_imports",
            "verifier_command",
            "library_snapshot_ref",
            "semantic_alignment_notes",
            "residual_translation_gaps",
            "kernel_verified_claimed",
            "acceptance_status",
            "proof_evidence_status",
            "proof_evidence_boundary",
            "ok",
            "errors",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_SCHEMA_VERSION,
            },
            "response_validation_id": {"type": "string", "minLength": 1},
            "prover_adapter_packet_id": {"type": "string", "minLength": 1},
            "goal_plan_id": {"type": "string", "minLength": 1},
            "route_id": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "primitive": {"type": "string", "minLength": 1},
            "target_prover_family": {"enum": list(PROVER_FAMILIES)},
            "response_present": {"type": "boolean"},
            "response_contract_ok": {"type": "boolean"},
            "mapping_status": {"type": "string"},
            "translated_statement": {"type": "string"},
            "translated_imports": string_array,
            "verifier_command": {"type": "string"},
            "library_snapshot_ref": {"type": "string"},
            "semantic_alignment_notes": {"type": "string"},
            "residual_translation_gaps": string_array,
            "kernel_verified_claimed": {"type": "boolean"},
            "acceptance_status": {"type": "string", "minLength": 1},
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


def validate_prover_adapter_response_validation_row(
    row: dict[str, Any],
    schema: dict[str, object] | None = None,
) -> tuple[str, ...]:
    row_schema = schema or prover_adapter_response_validation_row_json_schema()
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
    return tuple(errors)


def _packets_for_plan_row(
    row: dict[str, Any],
    *,
    target_prover_family: str,
    library_snapshot_ref: str,
) -> tuple[FormalizationGapPlannerProverAdapterPacket, ...]:
    packets = []
    for index, packet in enumerate(row.get("portable_work_packets", []), start=1):
        if not isinstance(packet, dict):
            continue
        packets.append(
            _packet_for_work_packet(
                row,
                packet,
                packet_index=index,
                target_prover_family=target_prover_family,
                library_snapshot_ref=library_snapshot_ref,
            )
        )
    return tuple(packets)


def _packet_for_work_packet(
    plan_row: dict[str, Any],
    packet: dict[str, Any],
    *,
    packet_index: int,
    target_prover_family: str,
    library_snapshot_ref: str,
) -> FormalizationGapPlannerProverAdapterPacket:
    errors: list[str] = []
    goal_plan_id = str(plan_row.get("goal_plan_id", ""))
    route_id = str(plan_row.get("route_id", ""))
    display_name = str(plan_row.get("display_name", ""))
    primitive = str(packet.get("primitive", ""))
    action_class = str(packet.get("action_class", ""))
    worker_packet_kind = str(packet.get("worker_packet_kind", ""))
    expected_cost = str(packet.get("expected_cost", ""))
    required_gate = str(packet.get("required_gate", ""))
    for field_name, value in (
        ("goal_plan_id", goal_plan_id),
        ("route_id", route_id),
        ("display_name", display_name),
        ("primitive", primitive),
        ("action_class", action_class),
        ("worker_packet_kind", worker_packet_kind),
        ("required_gate", required_gate),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    alignment_edge = _alignment_edge_for_primitive(plan_row, primitive)
    if not alignment_edge:
        errors.append("route_alignment_edge missing for primitive")
    else:
        errors.extend(
            f"route_alignment_edge.{error}"
            for error in validate_route_alignment_edge(alignment_edge)
        )
    packet_id = "formalization_gap_planner_prover_adapter_packet:" + stable_hash(
        [goal_plan_id, route_id, primitive, packet_index, target_prover_family]
    )[:20]
    source_prover_family = str(plan_row.get("target_prover_family", ""))
    standalone_input_trace = _standalone_input_trace_for_packet(
        plan_row,
        packet,
        packet_index=packet_index,
        target_prover_family=target_prover_family,
        library_snapshot_ref=library_snapshot_ref,
    )
    errors.extend(
        _standalone_trace_target_errors(
            standalone_input_trace,
            source_prover_family=source_prover_family,
            target_prover_family=target_prover_family,
        )
    )
    llm_route_adoption_status = str(
        standalone_input_trace.get("llm_route_planner_route_adoption_status", "")
    )
    llm_route_adoption_blockers = _str_tuple(
        standalone_input_trace.get("llm_route_planner_route_adoption_blockers", [])
    )
    return FormalizationGapPlannerProverAdapterPacket(
        schema_version=FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_SCHEMA_VERSION,
        prover_adapter_packet_id=packet_id,
        goal_plan_id=goal_plan_id,
        route_id=route_id,
        display_name=display_name,
        packet_index=packet_index,
        primitive=primitive,
        action_class=action_class,
        worker_packet_kind=worker_packet_kind,
        expected_cost=expected_cost,
        required_gate=required_gate,
        source_prover_family=source_prover_family,
        target_prover_family=target_prover_family,
        library_snapshot_ref=library_snapshot_ref,
        portable_work_packet=dict(packet),
        route_alignment_edge=alignment_edge,
        standalone_input_trace=standalone_input_trace,
        llm_route_planner_route_adoption_status=llm_route_adoption_status,
        llm_route_planner_route_adoption_blockers=llm_route_adoption_blockers,
        alignment_status=str(alignment_edge.get("alignment_status", "")),
        informal_route_node_id=str(alignment_edge.get("source", "")),
        formal_realization_node_id=str(alignment_edge.get("target", "")),
        required_adapter_response_fields=tuple(
            prover_adapter_response_json_schema()["required"]  # type: ignore[index]
        ),
        acceptance_gate=(
            "target prover adapter may only mark the packet ready for kernel attempt; "
            "proof promotion requires target-prover kernel verification through a "
            "separate replay/calibration gate"
        ),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _standalone_input_trace_for_packet(
    plan_row: dict[str, Any],
    packet: dict[str, Any],
    *,
    packet_index: int,
    target_prover_family: str,
    library_snapshot_ref: str,
) -> dict[str, object]:
    existing = plan_row.get("standalone_input_trace", {})
    if isinstance(existing, dict) and existing:
        trace = dict(existing)
        source_prover_family = str(plan_row.get("target_prover_family", ""))
        source_target_prover_family = str(
            trace.get("target_prover_family", "")
            or trace.get("source_target_prover_family", "")
            or source_prover_family
        )
        trace["source_prover_family"] = str(
            trace.get("source_prover_family", "") or source_prover_family
        )
        trace["source_target_prover_family"] = source_target_prover_family
        trace["target_prover_family"] = target_prover_family
        trace["target_library_snapshot_ref"] = library_snapshot_ref
        trace["trace_target_projection"] = "target_prover_adapter_contract"
        _normalize_trace_quality_control_fields(trace)
        return trace
    replan_metadata = plan_row.get("replan_metadata", {})
    if not isinstance(replan_metadata, dict):
        replan_metadata = {}
    route_revision_triggers = plan_row.get("route_revision_triggers", ())
    return {
        "trace_source": "formalization_gap_planner_prover_adapter_contract_fallback",
        "goal_plan_id": str(plan_row.get("goal_plan_id", "")),
        "route_id": str(plan_row.get("route_id", "")),
        "display_name": str(plan_row.get("display_name", "")),
        "question_id": str(plan_row.get("question_id", "")),
        "problem_class": str(plan_row.get("problem_class", "")),
        "theorem_goal_id": str(plan_row.get("theorem_goal_id", "")),
        "primitive": str(packet.get("primitive", "")),
        "action_class": str(packet.get("action_class", "")),
        "worker_packet_kind": str(packet.get("worker_packet_kind", "")),
        "packet_index": packet_index,
        "source_prover_family": str(plan_row.get("target_prover_family", "")),
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "has_replan_metadata": bool(replan_metadata),
        "replan_metadata_keys": tuple(sorted(str(key) for key in replan_metadata)),
        "route_revision_trigger_count": (
            len(route_revision_triggers)
            if isinstance(route_revision_triggers, (list, tuple))
            else 0
        ),
        "quality_controls": {},
        "has_quality_controls": False,
        "quality_control_fields": [],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _standalone_trace_target_errors(
    trace: dict[str, object],
    *,
    source_prover_family: str,
    target_prover_family: str,
) -> tuple[str, ...]:
    errors: list[str] = []
    trace_source = str(trace.get("source_prover_family", "")).strip()
    trace_target = str(trace.get("target_prover_family", "")).strip()
    if source_prover_family and trace_source != source_prover_family:
        errors.append(
            "standalone_input_trace.source_prover_family "
            f"{trace_source} does not match packet {source_prover_family}"
        )
    if target_prover_family and trace_target != target_prover_family:
        errors.append(
            "standalone_input_trace.target_prover_family "
            f"{trace_target} does not match packet {target_prover_family}"
        )
    return tuple(errors)


def _standalone_trace_quality_control_errors(
    trace: dict[str, object],
) -> tuple[str, ...]:
    errors: list[str] = []
    raw_controls = trace.get("quality_controls", {})
    if not isinstance(raw_controls, dict):
        errors.append("standalone_input_trace.quality_controls must be an object")
        controls: dict[str, tuple[str, ...]] = {}
    else:
        controls = _quality_controls_from_trace(trace)
        unknown_fields = sorted(
            set(str(field) for field in raw_controls) - set(QUALITY_CONTROL_FIELDS)
        )
        if unknown_fields:
            errors.append(
                "standalone_input_trace.quality_controls unknown fields: "
                + ", ".join(unknown_fields)
            )
        for field_name, values in raw_controls.items():
            if not isinstance(values, (list, tuple, set)):
                errors.append(
                    "standalone_input_trace.quality_controls."
                    f"{field_name} must be array"
                )
                continue
            non_strings = [
                idx for idx, item in enumerate(values) if not isinstance(item, str)
            ]
            if non_strings:
                errors.append(
                    "standalone_input_trace.quality_controls."
                    f"{field_name} items must be string at indexes "
                    + ",".join(str(idx) for idx in non_strings)
                )
    if controls or "has_quality_controls" in trace:
        observed_present = trace.get("has_quality_controls", False)
        if not isinstance(observed_present, bool):
            errors.append("standalone_input_trace.has_quality_controls must be boolean")
        elif observed_present != bool(controls):
            errors.append(
                "standalone_input_trace.has_quality_controls mismatch: "
                f"observed={observed_present} expected={bool(controls)}"
            )
    if controls or "quality_control_fields" in trace:
        observed_fields = _str_tuple(trace.get("quality_control_fields", []))
        expected_fields = tuple(sorted(controls))
        if observed_fields != expected_fields:
            errors.append(
                "standalone_input_trace.quality_control_fields mismatch: "
                f"observed={sorted(observed_fields)} expected={sorted(expected_fields)}"
            )
    return tuple(errors)


def _normalize_trace_quality_control_fields(trace: dict[str, object]) -> None:
    controls = _quality_controls_from_trace(trace)
    trace["quality_controls"] = {
        field_name: list(values) for field_name, values in controls.items()
    }
    trace["has_quality_controls"] = bool(controls)
    trace["quality_control_fields"] = sorted(controls)


def _quality_controls_from_packet_trace(
    packet: FormalizationGapPlannerProverAdapterPacket,
) -> dict[str, tuple[str, ...]]:
    return _quality_controls_from_trace(packet.standalone_input_trace)


def _quality_controls_from_trace(
    trace: dict[str, object],
) -> dict[str, tuple[str, ...]]:
    raw_controls = trace.get("quality_controls", {})
    if not isinstance(raw_controls, dict):
        return {}
    controls: dict[str, tuple[str, ...]] = {}
    for field_name in QUALITY_CONTROL_FIELDS:
        values = _str_tuple(raw_controls.get(field_name, ()))
        if values:
            controls[field_name] = values
    return controls


def _packet_quality_control_fields(
    packets: list[FormalizationGapPlannerProverAdapterPacket],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                field_name
                for packet in packets
                for field_name in _quality_controls_from_packet_trace(packet)
            }
        )
    )


def _packet_quality_control_values(
    packets: list[FormalizationGapPlannerProverAdapterPacket],
    field_name: str,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                value
                for packet in packets
                for value in _quality_controls_from_packet_trace(packet).get(
                    field_name,
                    tuple(),
                )
            }
        )
    )


def _packet_quality_control_field_summary(
    packets: list[FormalizationGapPlannerProverAdapterPacket],
) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for field_name in _packet_quality_control_fields(packets):
        field_packets = [
            packet
            for packet in packets
            if field_name in _quality_controls_from_packet_trace(packet)
        ]
        values = _packet_quality_control_values(packets, field_name)
        summary[field_name] = {
            "n_packets": len(field_packets),
            "n_values": len(values),
            "values": values,
        }
    return summary


def _alignment_edge_for_primitive(
    plan_row: dict[str, Any],
    primitive: str,
) -> dict[str, object]:
    for edge in plan_row.get("route_alignment_edges", []) or []:
        if not isinstance(edge, dict):
            continue
        if str(edge.get("primitive", "")) == primitive:
            return dict(edge)
    return {}


def _validate_response(
    packet: FormalizationGapPlannerProverAdapterPacket,
    response: dict[str, Any] | None,
) -> FormalizationGapPlannerProverAdapterResponseValidationRow:
    if response is None:
        return FormalizationGapPlannerProverAdapterResponseValidationRow(
            schema_version=FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_SCHEMA_VERSION,
            response_validation_id="formalization_gap_planner_prover_adapter_response:"
            + stable_hash([packet.prover_adapter_packet_id, "awaiting"])[:20],
            prover_adapter_packet_id=packet.prover_adapter_packet_id,
            goal_plan_id=packet.goal_plan_id,
            route_id=packet.route_id,
            display_name=packet.display_name,
            primitive=packet.primitive,
            target_prover_family=packet.target_prover_family,
            response_present=False,
            response_contract_ok=False,
            mapping_status="",
            translated_statement="",
            translated_imports=(),
            verifier_command="",
            library_snapshot_ref="",
            semantic_alignment_notes="",
            residual_translation_gaps=(),
            kernel_verified_claimed=False,
            acceptance_status="AWAITING_PROVER_ADAPTER_MAPPING",
            proof_evidence_status="AWAITING_RESPONSE_NOT_PROOF_EVIDENCE",
            proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
            ok=True,
            errors=(),
        )
    errors: list[str] = []
    _match_optional(response, packet, "prover_adapter_packet_id", errors)
    _match_optional(response, packet, "goal_plan_id", errors)
    _match_optional(response, packet, "route_id", errors)
    _match_optional(response, packet, "primitive", errors)
    target_prover_family = str(response.get("target_prover_family", ""))
    mapping_status = str(response.get("mapping_status", ""))
    translated_statement = str(response.get("translated_statement", ""))
    translated_imports = _str_tuple(response.get("translated_imports", []))
    verifier_command = str(response.get("verifier_command", ""))
    library_snapshot_ref = str(response.get("library_snapshot_ref", ""))
    semantic_alignment_notes = str(response.get("semantic_alignment_notes", ""))
    residual_translation_gaps = _str_tuple(response.get("residual_translation_gaps", []))
    kernel_verified = bool(response.get("kernel_verified", False))
    for field_name, value in (
        ("target_prover_family", target_prover_family),
        ("primitive", str(response.get("primitive", ""))),
        ("mapping_status", mapping_status),
        ("translated_statement", translated_statement),
        ("verifier_command", verifier_command),
        ("library_snapshot_ref", library_snapshot_ref),
        ("semantic_alignment_notes", semantic_alignment_notes),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    response_target_key = _normalize_prover_family(target_prover_family)
    packet_target_key = _normalize_prover_family(packet.target_prover_family)
    if response_target_key != packet_target_key:
        errors.append(
            f"target_prover_family {target_prover_family} does not match packet {packet.target_prover_family}"
        )
    if library_snapshot_ref != packet.library_snapshot_ref:
        errors.append(
            f"library_snapshot_ref {library_snapshot_ref} does not match packet {packet.library_snapshot_ref}"
        )
    if mapping_status not in MAPPING_STATUSES:
        errors.append(f"unsupported mapping_status: {mapping_status}")
    if "translated_imports" in response and not isinstance(
        response.get("translated_imports"),
        (list, tuple),
    ):
        errors.append("translated_imports must be a list")
    if mapping_status == "ready_for_kernel_attempt" and not translated_imports:
        errors.append("translated_imports required when ready_for_kernel_attempt")
    if (
        mapping_status == "ready_for_kernel_attempt"
        and packet.llm_route_planner_route_adoption_status
        and packet.llm_route_planner_route_adoption_status
        != "READY_FOR_STANDALONE_REPLAY"
    ):
        blockers = ", ".join(packet.llm_route_planner_route_adoption_blockers)
        suffix = f" blockers: {blockers}" if blockers else ""
        errors.append(
            "ready_for_kernel_attempt requires llm_route_planner_route_adoption_status "
            "READY_FOR_STANDALONE_REPLAY; packet has "
            f"{packet.llm_route_planner_route_adoption_status}{suffix}"
        )
    if mapping_status in {
        "needs_statement_translation",
        "needs_library_grounding",
        "unsupported_in_target_prover",
        "needs_human_review",
    } and not residual_translation_gaps:
        errors.append("residual_translation_gaps required unless ready_for_kernel_attempt")
    if not isinstance(response.get("kernel_verified", False), bool):
        errors.append("kernel_verified must be boolean")
    if kernel_verified:
        errors.append("kernel_verified=true is outside this adapter-mapping contract")
    forbidden_text = " ".join([translated_statement, verifier_command])
    if FORBIDDEN_PLACEHOLDER_RE.search(forbidden_text):
        errors.append("translated statement or verifier command contains placeholder token")
    acceptance_status = (
        "PROVER_ADAPTER_MAPPING_RECORDED_NOT_PROOF_EVIDENCE"
        if not errors
        else "REJECTED_PROVER_ADAPTER_MAPPING_CONTRACT"
    )
    return FormalizationGapPlannerProverAdapterResponseValidationRow(
        schema_version=FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_SCHEMA_VERSION,
        response_validation_id="formalization_gap_planner_prover_adapter_response:"
        + stable_hash([packet.prover_adapter_packet_id, response])[:20],
        prover_adapter_packet_id=packet.prover_adapter_packet_id,
        goal_plan_id=packet.goal_plan_id,
        route_id=packet.route_id,
        display_name=packet.display_name,
        primitive=packet.primitive,
        target_prover_family=packet.target_prover_family,
        response_present=True,
        response_contract_ok=not errors,
        mapping_status=mapping_status,
        translated_statement=translated_statement,
        translated_imports=translated_imports,
        verifier_command=verifier_command,
        library_snapshot_ref=library_snapshot_ref,
        semantic_alignment_notes=semantic_alignment_notes,
        residual_translation_gaps=residual_translation_gaps,
        kernel_verified_claimed=kernel_verified,
        acceptance_status=acceptance_status,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _response_index(
    responses: list[dict[str, Any]],
    errors: list[str],
) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    index: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    seen_packet_ids: set[str] = set()
    for response in responses:
        packet_id = str(response.get("prover_adapter_packet_id", ""))
        if packet_id:
            if packet_id in seen_packet_ids:
                errors.append(f"duplicate prover_adapter_packet_id response: {packet_id}")
            seen_packet_ids.add(packet_id)
        key = (
            packet_id,
            str(response.get("goal_plan_id", "")),
            str(response.get("route_id", "")),
            str(response.get("primitive", "")),
        )
        if key in index:
            errors.append("duplicate prover adapter response key: " + "::".join(key))
        index[key] = response
    return index


def _packet_match_key(
    packet: FormalizationGapPlannerProverAdapterPacket,
) -> tuple[str, str, str, str]:
    return (
        packet.prover_adapter_packet_id,
        packet.goal_plan_id,
        packet.route_id,
        packet.primitive,
    )


def _packet_fallback_match_key(
    packet: FormalizationGapPlannerProverAdapterPacket,
) -> tuple[str, str, str, str]:
    return ("", packet.goal_plan_id, packet.route_id, packet.primitive)


def _response_for_packet(
    packet: FormalizationGapPlannerProverAdapterPacket,
    response_by_key: dict[tuple[str, str, str, str], dict[str, Any]],
) -> dict[str, Any] | None:
    return response_by_key.get(_packet_match_key(packet)) or response_by_key.get(
        _packet_fallback_match_key(packet)
    )


def _unmatched_response_errors(
    responses: list[dict[str, Any]],
    packets: list[FormalizationGapPlannerProverAdapterPacket],
) -> tuple[str, ...]:
    packet_keys = {_packet_match_key(packet) for packet in packets}
    fallback_keys = {_packet_fallback_match_key(packet) for packet in packets}
    errors: list[str] = []
    for index, response in enumerate(responses):
        key = (
            str(response.get("prover_adapter_packet_id", "")),
            str(response.get("goal_plan_id", "")),
            str(response.get("route_id", "")),
            str(response.get("primitive", "")),
        )
        if key[0]:
            matched = key in packet_keys
        else:
            matched = key in fallback_keys
        if not matched:
            errors.append(
                "unmatched prover adapter response "
                f"{index}: packet_id={key[0]!r} goal_plan_id={key[1]!r} "
                f"route_id={key[2]!r} primitive={key[3]!r}"
            )
    return tuple(errors)


def _match_optional(
    response: dict[str, Any],
    packet: FormalizationGapPlannerProverAdapterPacket,
    field_name: str,
    errors: list[str],
) -> None:
    if field_name not in response:
        return
    actual = str(response.get(field_name, ""))
    expected = str(getattr(packet, field_name))
    if actual and actual != expected:
        errors.append(f"{field_name} mismatch: {actual} != {expected}")


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
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name} must be object")
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


def _normalize_prover_family(value: str) -> str:
    lowered = value.strip().lower().replace("-", "_")
    aliases = {
        "lean": "lean4",
        "lean4": "lean4",
        "coq": "rocq",
        "coq8": "rocq",
        "coq_8": "rocq",
        "coq_rocq": "rocq",
        "rocq_coq": "rocq",
        "rocq": "rocq",
        "isabelle": "isabelle",
        "isabelle/hol": "isabelle",
        "isabelle_hol": "isabelle",
        "agda": "agda",
        "other": "other",
    }
    return aliases.get(lowered, lowered)


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


def _read_response_jsonl(
    path: Path | None,
    errors: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    if path is None:
        return [], False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing response JSONL file: {path}")
        return [], False
    responses: list[dict[str, Any]] = []
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse {path}:{line_no}: {type(exc).__name__}: {exc}")
            continue
        if isinstance(payload, dict):
            responses.append(payload)
    return responses, True


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Prover Adapter Contract",
        "",
        f"- Target prover: `{payload.get('target_prover_family')}`",
        f"- Packets: {payload.get('n_packet_ok')}/{payload.get('n_packets')}",
        f"- Packet schema valid: {payload.get('n_packet_schema_valid')}/{payload.get('n_packets')}",
        f"- Packets with alignment: {payload.get('n_packets_with_alignment')}",
        f"- Packets with standalone trace: {payload.get('n_packets_with_standalone_input_trace')}",
        f"- Packets missing standalone trace: {payload.get('n_packets_missing_standalone_input_trace')}",
        f"- Packets with replan metadata trace: {payload.get('n_packets_with_replan_metadata_trace')}",
        f"- Packets with quality controls: {payload.get('n_packets_with_quality_controls')}",
        f"- Packet quality-control fields: {payload.get('packet_quality_control_fields')}",
        "- LLM route-adoption pending quality-control blockers: "
        f"{payload.get('n_packet_llm_route_adoption_pending_quality_control_blockers')}",
        "- LLM route-adoption pending source-grounding blockers: "
        f"{payload.get('n_packet_llm_route_adoption_pending_source_grounding_blockers')}",
        f"- Responses: {payload.get('n_response_present')}/{payload.get('n_packets')}",
        f"- Contract OK responses: {payload.get('n_response_contract_ok')}",
        (
            f"- Response validation row schema valid: "
            f"{payload.get('n_response_validation_row_schema_valid')}/"
            f"{payload.get('n_packets')}"
        ),
        f"- Awaiting mappings: {payload.get('n_awaiting_adapter_mapping')}",
        f"- Rejected mappings: {payload.get('n_rejected')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Mapping Status",
        "",
    ]
    for status, count in dict(payload.get("by_mapping_status", {})).items():
        label = status or "awaiting"
        lines.append(f"- `{label}`: {count}")
    return "\n".join(lines) + "\n"

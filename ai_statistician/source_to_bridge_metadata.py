from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


ARTIFACT_KIND = "SourceToBridgePremiseDerivationCandidateRequest"
LEARNING_TASK = "source_to_bridge_metadata_authoring_request"
TRIGGER_AUTHORED_REQUEST = "SOURCE_TO_BRIDGE_METADATA_AUTHORED_REQUEST"
TRIGGER_REQUEST_SHELL = "SOURCE_TO_BRIDGE_METADATA_REQUEST_SHELL"
REQUIRED_FIELDS = (
    "premise_name",
    "target_theorem_name",
    "target_lean_declaration",
    "exact_source_theorem_binders",
    "premise_semantic_anchor_binders",
    "premise_semantic_anchor_binder_names",
    "required_semantic_anchor_reference_names",
    "adapter_object_names_requiring_source_instantiation",
)
REQUEST_NOT_PROOF_EVIDENCE = (
    "SOURCE_TO_BRIDGE_METADATA_AUTHORING_REQUEST_NOT_PROOF_EVIDENCE"
)
PREMISE_REQUEST_NOT_PROOF_EVIDENCE = (
    "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
)
REQUEST_SHELL_NOT_PROOF_EVIDENCE = (
    "SOURCE_TO_BRIDGE_METADATA_REQUEST_SHELL_NOT_PROOF_EVIDENCE"
)
COMPLETE_STATUS = "COMPLETE_SOURCE_TO_BRIDGE_CANDIDATE_REQUEST_AUTHORED"
INCOMPLETE_STATUS = "INCOMPLETE_SOURCE_TO_BRIDGE_CANDIDATE_REQUEST_SHELL"
PENDING_PREMISE_DERIVATION = "PENDING_SOURCE_TO_BRIDGE_PREMISE_DERIVATION"
PENDING_METADATA_AUTHORING = "PENDING_SOURCE_TO_BRIDGE_METADATA_AUTHORING"


def sequence(raw: Any) -> list[Any]:
    if raw in (None, "", [], {}):
        return []
    if isinstance(raw, list | tuple | set):
        return list(raw)
    return [raw]


def first_sequence(*values: Any) -> list[Any]:
    for raw in values:
        values = sequence(raw)
        if values:
            return values
    return []


def string_values(raw: Any) -> list[str]:
    return [str(value).strip() for value in sequence(raw) if str(value).strip()]


def safe_identifier(raw: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", str(raw or "").strip())
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        return "metadata_request"
    if value[0].isdigit():
        value = f"x_{value}"
    return value


def missing_metadata_fields(request: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in REQUIRED_FIELDS:
        value = request.get(key)
        if key == "premise_semantic_anchor_binders":
            if value or request.get("premise_semantic_anchor_binder_names"):
                continue
        if key == "premise_semantic_anchor_binder_names":
            if value or request.get("premise_semantic_anchor_binders"):
                continue
        if value in (None, "", [], {}):
            missing.append(key)
    return missing


def normalize_candidate_request(raw: Mapping[str, Any]) -> dict[str, Any]:
    nested = raw.get("source_to_bridge_premise_derivation_candidate_request", {})
    request = dict(nested) if isinstance(nested, Mapping) and nested else dict(raw)
    if "candidate_request_id" not in request:
        request_id = str(
            raw.get("candidate_request_id", "")
            or raw.get("source_to_bridge_premise_derivation_candidate_request_id", "")
            or ""
        ).strip()
        if request_id:
            request["candidate_request_id"] = request_id
    if "proof_evidence_status" not in request:
        request["proof_evidence_status"] = PREMISE_REQUEST_NOT_PROOF_EVIDENCE
    return request


def _request_string_list(
    request: Mapping[str, Any],
    key: str,
    *,
    limit: int = 12,
) -> list[str]:
    return string_values(request.get(key, []))[:limit]


def _request_sequence(
    request: Mapping[str, Any],
    key: str,
    *,
    limit: int = 12,
) -> list[Any]:
    return sequence(request.get(key, []))[:limit]


def metadata_authoring_request_row(
    *,
    request: Mapping[str, Any],
    proposal_packet: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    theorem_goal_ids: Sequence[str],
    source_kind: str,
    source_index: int,
    schema_version: int,
    proof_evidence_boundary: str,
) -> dict[str, Any]:
    normalized_request = normalize_candidate_request(request)
    target_goal_ids = string_values(
        first_sequence(
            proof_bank_runtime_memory_summary.get(
                "source_to_bridge_metadata_authoring_target_ids",
                [],
            ),
            proof_bank_runtime_memory_summary.get("remaining_theorem_goal_ids", []),
            theorem_goal_ids,
        )
    )
    target_theorem_name = str(
        normalized_request.get("target_theorem_name", "")
        or (target_goal_ids[0] if target_goal_ids else "")
    ).strip()
    target_lean_declaration = str(
        normalized_request.get("target_lean_declaration", "")
        or target_theorem_name
        or ""
    ).strip()
    if target_theorem_name and not normalized_request.get("target_theorem_name"):
        normalized_request["target_theorem_name"] = target_theorem_name
    if target_lean_declaration and not normalized_request.get("target_lean_declaration"):
        normalized_request["target_lean_declaration"] = target_lean_declaration

    candidate_request_id = str(
        normalized_request.get("candidate_request_id", "") or ""
    ).strip()
    if not candidate_request_id:
        candidate_request_id = (
            "source_to_bridge_premise_derivation_candidate_request:"
            + stable_hash(
                [
                    str(proposal_packet.get("packet_id", "") or ""),
                    safe_identifier(target_lean_declaration or target_theorem_name),
                    safe_identifier(
                        str(normalized_request.get("premise_name", "") or "")
                        or "metadata_request"
                    ),
                    source_kind,
                    source_index,
                ]
            )[:20]
        )
        normalized_request["candidate_request_id"] = candidate_request_id

    missing_fields = missing_metadata_fields(normalized_request)
    request_complete = not missing_fields
    return {
        "schema_version": schema_version,
        "artifact_kind": ARTIFACT_KIND,
        "learning_task": LEARNING_TASK,
        "source_formalizer_packet_id": str(
            proposal_packet.get("packet_id", "") or ""
        ),
        "source_kind": source_kind,
        "source_index": source_index,
        "candidate_request_id": candidate_request_id,
        "source_to_bridge_premise_derivation_candidate_request_id": (
            candidate_request_id
        ),
        "source_to_bridge_premise_derivation_candidate_request": (
            normalized_request
        ),
        "target_theorem_name": target_theorem_name,
        "target_lean_declaration": target_lean_declaration,
        "target_theorem_goal_ids": target_goal_ids,
        "premise_name": str(normalized_request.get("premise_name", "") or ""),
        "premise_names": _request_string_list(normalized_request, "premise_names"),
        "premise_target_type": str(
            normalized_request.get("premise_target_type", "") or ""
        ),
        "premise_semantic_dependency_requirements": _request_string_list(
            normalized_request,
            "premise_semantic_dependency_requirements",
        ),
        "exact_source_theorem_binders": _request_sequence(
            normalized_request,
            "exact_source_theorem_binders",
        ),
        "premise_semantic_anchor_binders": _request_sequence(
            normalized_request,
            "premise_semantic_anchor_binders",
        ),
        "premise_semantic_anchor_binder_names": _request_string_list(
            normalized_request,
            "premise_semantic_anchor_binder_names",
        ),
        "required_semantic_anchor_reference_names": _request_string_list(
            normalized_request,
            "required_semantic_anchor_reference_names",
        ),
        "semantic_anchor_reference_gate": str(
            normalized_request.get("semantic_anchor_reference_gate", "") or ""
        ),
        "adapter_object_names_requiring_source_instantiation": _request_string_list(
            normalized_request,
            "adapter_object_names_requiring_source_instantiation",
        ),
        "candidate_contract": str(
            normalized_request.get("candidate_contract", "") or ""
        ),
        "required_candidate_fields": (
            _request_string_list(normalized_request, "required_candidate_fields")
            or list(REQUIRED_FIELDS)
        ),
        "missing_required_metadata_fields": missing_fields,
        "request_complete": request_complete,
        "metadata_authoring_status": (
            COMPLETE_STATUS if request_complete else INCOMPLETE_STATUS
        ),
        "runtime_queue_status": (
            PENDING_PREMISE_DERIVATION
            if request_complete
            else PENDING_METADATA_AUTHORING
        ),
        "trigger": (
            TRIGGER_AUTHORED_REQUEST if request_complete else TRIGGER_REQUEST_SHELL
        ),
        "acceptance_gate": (
            "A subsequent Formalizer packet copies this request into a "
            "non-vacuous source_to_bridge_premise_derivation_candidates object "
            "and local Lean/AXLE kernel verifies the derivation."
        )
        if request_complete
        else (
            "Formalizer/ProofEngineer fills the missing_required_metadata_fields "
            "before executable source_to_bridge_premise_derivation_candidates are "
            "queued."
        ),
        "proof_evidence_status": REQUEST_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": proof_evidence_boundary,
    }


def formalizer_metadata_authoring_request_rows(
    *,
    proposal_packet: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    theorem_goal_ids: Sequence[str],
    schema_version: int,
    proof_evidence_boundary: str,
) -> list[dict[str, Any]]:
    target_mode = str(
        proof_bank_runtime_memory_summary.get("recommended_formalizer_target_mode", "")
        or ""
    )
    metadata_mode = bool(
        target_mode == "source_to_bridge_metadata_authoring_required"
        or proof_bank_runtime_memory_summary.get(
            "source_to_bridge_metadata_authoring_required",
            False,
        )
    )
    explicit_requests = [
        row
        for row in proposal_packet.get(
            "source_to_bridge_premise_derivation_candidate_requests",
            [],
        )
        or []
        if isinstance(row, Mapping)
    ]
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, request in enumerate(explicit_requests, start=1):
        row = metadata_authoring_request_row(
            request=request,
            proposal_packet=proposal_packet,
            proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
            theorem_goal_ids=theorem_goal_ids,
            source_kind="explicit_formalizer_candidate_request",
            source_index=index,
            schema_version=schema_version,
            proof_evidence_boundary=proof_evidence_boundary,
        )
        key = str(row.get("candidate_request_id", "") or "")
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    if rows or not metadata_mode:
        return rows

    contract = (
        proof_bank_runtime_memory_summary.get(
            "source_to_bridge_metadata_authoring_contract",
            {},
        )
        if isinstance(
            proof_bank_runtime_memory_summary.get(
                "source_to_bridge_metadata_authoring_contract",
                {},
            ),
            Mapping,
        )
        else {}
    )
    required_fields = string_values(
        first_sequence(
            contract.get("required_metadata_fields", []),
            REQUIRED_FIELDS,
        )
    )
    target_goal_ids = string_values(
        first_sequence(
            contract.get("target_ids", []),
            proof_bank_runtime_memory_summary.get(
                "source_to_bridge_metadata_authoring_target_ids",
                [],
            ),
            proof_bank_runtime_memory_summary.get("remaining_theorem_goal_ids", []),
            theorem_goal_ids,
        )
    )
    target = target_goal_ids[0] if target_goal_ids else ""
    for index, action in enumerate(proposal_packet.get("next_actions", []) or [], start=1):
        if not isinstance(action, Mapping):
            continue
        action_text = " ".join(
            str(action.get(key, "") or "")
            for key in ("owner_agent", "action", "acceptance_gate")
        )
        lowered = action_text.lower()
        if (
            "source_to_bridge_premise_derivation_candidate_request" not in lowered
            and "source-to-bridge premise-derivation candidate request" not in lowered
        ):
            continue
        request = {
            "candidate_request_id": (
                "source_to_bridge_premise_derivation_candidate_request:"
                + stable_hash(
                    [
                        str(proposal_packet.get("packet_id", "") or ""),
                        target,
                        action_text,
                    ]
                )[:20]
            ),
            "target_theorem_name": target,
            "target_lean_declaration": target,
            "target_theorem_goal_ids": target_goal_ids,
            "candidate_contract": action_text[:900],
            "required_candidate_fields": required_fields,
            "proof_evidence_status": REQUEST_SHELL_NOT_PROOF_EVIDENCE,
        }
        rows.append(
            metadata_authoring_request_row(
                request=request,
                proposal_packet=proposal_packet,
                proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
                theorem_goal_ids=theorem_goal_ids,
                source_kind="next_action_request_shell",
                source_index=index,
                schema_version=schema_version,
                proof_evidence_boundary=proof_evidence_boundary,
            )
        )
        break
    return rows


def memory_metadata_authoring_request_rows(
    rows: Sequence[Any],
    *,
    row_trigger,
) -> tuple[dict[str, Any], ...]:
    request_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        input_summary = (
            row.get("input_summary", {})
            if isinstance(row.get("input_summary", {}), Mapping)
            else {}
        )
        trigger = row_trigger(row, input_summary)
        learning_task = str(row.get("learning_task", "") or "")
        artifact_kind = str(row.get("artifact_kind", "") or "")
        if not (
            learning_task == LEARNING_TASK
            or artifact_kind == ARTIFACT_KIND
            or trigger in {TRIGGER_AUTHORED_REQUEST, TRIGGER_REQUEST_SHELL}
        ):
            continue
        request_raw = (
            row.get("source_to_bridge_premise_derivation_candidate_request", {})
            if isinstance(
                row.get("source_to_bridge_premise_derivation_candidate_request", {}),
                Mapping,
            )
            else input_summary.get(
                "source_to_bridge_premise_derivation_candidate_request",
                {},
            )
            if isinstance(
                input_summary.get(
                    "source_to_bridge_premise_derivation_candidate_request",
                    {},
                ),
                Mapping,
            )
            else {}
        )
        request = dict(request_raw) if isinstance(request_raw, Mapping) else {}
        candidate_request_id = str(
            row.get("candidate_request_id", "")
            or row.get("source_to_bridge_premise_derivation_candidate_request_id", "")
            or request.get("candidate_request_id", "")
            or input_summary.get(
                "source_to_bridge_premise_derivation_candidate_request_id",
                "",
            )
            or ""
        ).strip()
        if candidate_request_id and not request.get("candidate_request_id"):
            request["candidate_request_id"] = candidate_request_id
        target_theorem_name = str(
            row.get("target_theorem_name", "")
            or input_summary.get("target_theorem_name", "")
            or request.get("target_theorem_name", "")
            or ""
        ).strip()
        target_lean_declaration = str(
            row.get("target_lean_declaration", "")
            or input_summary.get("target_lean_declaration", "")
            or request.get("target_lean_declaration", "")
            or target_theorem_name
            or ""
        ).strip()
        if target_theorem_name and not request.get("target_theorem_name"):
            request["target_theorem_name"] = target_theorem_name
        if target_lean_declaration and not request.get("target_lean_declaration"):
            request["target_lean_declaration"] = target_lean_declaration
        for key in (
            "premise_name",
            "premise_target_type",
            "semantic_anchor_reference_gate",
            "candidate_contract",
        ):
            value = str(row.get(key, "") or input_summary.get(key, "") or "")
            if value and not request.get(key):
                request[key] = value
        for key in (
            "premise_names",
            "premise_semantic_dependency_requirements",
            "exact_source_theorem_binders",
            "premise_semantic_anchor_binders",
            "premise_semantic_anchor_binder_names",
            "required_semantic_anchor_reference_names",
            "adapter_object_names_requiring_source_instantiation",
            "required_candidate_fields",
        ):
            values = first_sequence(
                row.get(key, []),
                input_summary.get(key, []),
                request.get(key, []),
            )
            if values and not request.get(key):
                request[key] = values
        missing_fields = string_values(
            first_sequence(
                row.get("missing_required_metadata_fields", []),
                input_summary.get("missing_required_metadata_fields", []),
                missing_metadata_fields(request),
            )
        )
        request_complete = not missing_fields
        key = candidate_request_id or stable_hash(request)[:20]
        if key in seen:
            continue
        seen.add(key)
        request_rows.append(
            {
                "candidate_request_id": candidate_request_id,
                "source_to_bridge_premise_derivation_candidate_request_id": (
                    candidate_request_id
                ),
                "source_to_bridge_premise_derivation_candidate_request": request,
                "target_theorem_name": target_theorem_name,
                "target_lean_declaration": target_lean_declaration,
                "target_theorem_goal_ids": string_values(
                    first_sequence(
                        row.get("target_theorem_goal_ids", []),
                        row.get("target_ids", []),
                        input_summary.get("target_theorem_goal_ids", []),
                        input_summary.get("target_ids", []),
                    )
                ),
                "premise_name": str(
                    request.get("premise_name", "")
                    or row.get("premise_name", "")
                    or input_summary.get("premise_name", "")
                    or ""
                ),
                "premise_names": string_values(request.get("premise_names", [])),
                "premise_target_type": str(
                    request.get("premise_target_type", "") or ""
                ),
                "premise_semantic_dependency_requirements": string_values(
                    request.get("premise_semantic_dependency_requirements", [])
                )[:12],
                "exact_source_theorem_binders": sequence(
                    request.get("exact_source_theorem_binders", [])
                )[:12],
                "premise_semantic_anchor_binders": sequence(
                    request.get("premise_semantic_anchor_binders", [])
                )[:12],
                "premise_semantic_anchor_binder_names": string_values(
                    request.get("premise_semantic_anchor_binder_names", [])
                )[:12],
                "required_semantic_anchor_reference_names": string_values(
                    request.get("required_semantic_anchor_reference_names", [])
                )[:12],
                "semantic_anchor_reference_gate": str(
                    request.get("semantic_anchor_reference_gate", "") or ""
                ),
                "adapter_object_names_requiring_source_instantiation": string_values(
                    request.get(
                        "adapter_object_names_requiring_source_instantiation",
                        [],
                    )
                )[:12],
                "candidate_contract": str(
                    request.get("candidate_contract", "")
                    or row.get("candidate_contract", "")
                    or ""
                ),
                "required_candidate_fields": string_values(
                    first_sequence(
                        request.get("required_candidate_fields", []),
                        row.get("required_candidate_fields", []),
                    )
                )[:12],
                "missing_required_metadata_fields": missing_fields,
                "request_complete": request_complete,
                "metadata_authoring_status": str(
                    row.get("metadata_authoring_status", "")
                    or input_summary.get("metadata_authoring_status", "")
                    or (COMPLETE_STATUS if request_complete else INCOMPLETE_STATUS)
                ),
                "source_formalizer_packet_id": str(
                    row.get("source_formalizer_packet_id", "")
                    or input_summary.get("source_formalizer_packet_id", "")
                    or ""
                ),
                "proof_evidence_status": str(
                    row.get("proof_evidence_status", "")
                    or input_summary.get("proof_evidence_status", "")
                    or REQUEST_NOT_PROOF_EVIDENCE
                ),
            }
        )
    return tuple(request_rows)

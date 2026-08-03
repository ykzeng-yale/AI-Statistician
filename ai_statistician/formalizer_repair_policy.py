from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


FORMALIZER_REPAIR_FEEDBACK_SCHEMA_VERSION = 3
FORMALIZER_TOOL_OBSERVATION_SCHEMA_VERSION = 1

FORMALIZER_VALIDATION_FEEDBACK_BOUNDARY = (
    "Formalizer repair feedback is an environment observation, not a repair "
    "recipe and not proof evidence. AgentRuntime owns packet identity, retry "
    "budgets, execution, validation, and proof authority. The model owns the "
    "mathematical decomposition, Lean candidate, and repair strategy. Only the "
    "unchanged local validators and active-project Lean/kernel checks can accept "
    "their respective artifacts."
)

FORMALIZER_TOOL_OBSERVATION_BOUNDARY = (
    "Tool output is an environment observation, not a repair recipe and not "
    "proof evidence. The model chooses the next candidate or typed blocker. "
    "AgentRuntime owns artifact lineage, budgets, tool execution, and proof "
    "authority; Lean/kernel acceptance remains unchanged."
)


def formalizer_tool_observation_envelope(
    observations: Sequence[Mapping[str, Any]],
    *,
    tool_name: str,
    producer: str,
    diagnostic_classes: Sequence[Any] = (),
) -> dict[str, Any]:
    """Build typed model-visible tool feedback without choosing a repair."""

    rows = [
        _compact_tool_observation(row)
        for row in observations
        if isinstance(row, Mapping)
    ][:6]
    classes = list(
        dict.fromkeys(
            str(value).strip()
            for value in diagnostic_classes
            if str(value).strip()
        )
    )
    observation_id = "formalizer_tool_observation:" + stable_hash(
        [tool_name, producer, rows, classes]
    )[:20]
    return {
        "schema_version": FORMALIZER_TOOL_OBSERVATION_SCHEMA_VERSION,
        "artifact_kind": "FormalizerToolObservationEnvelope",
        "observation_id": observation_id,
        "producer": str(producer),
        "tool_name": str(tool_name),
        "observations": rows,
        "diagnostic_classes": classes,
        "diagnostic_classes_source": (
            "structured_tool_output" if classes else "not_provided"
        ),
        "model_owned_next_action": True,
        "runtime_selected_repair": False,
        "repair_authority": {
            "model_owns": [
                "candidate_revision",
                "retrieval_or_tool_request",
                "lemma_decomposition",
                "typed_blocker_decision",
            ],
            "runtime_owns": [
                "artifact_identity_and_lineage",
                "retry_and_resource_budget",
                "tool_execution",
                "response_validation",
                "proof_evidence_and_kernel_authority",
            ],
        },
        "boundary": FORMALIZER_TOOL_OBSERVATION_BOUNDARY,
    }


def formalizer_validation_feedback_envelope(
    validation_errors: Sequence[Any],
    *,
    validation_label: str = "LLM Formalizer/ProofEngineer packet",
    invalid_packet: Mapping[str, Any] | None = None,
    attempt_history: Sequence[Mapping[str, Any]] | None = None,
    retry_depth: int = 0,
) -> dict[str, Any]:
    """Build model-visible validator observations without prescribing a repair."""

    errors = list(
        dict.fromkeys(
            str(error).strip()
            for error in validation_errors
            if str(error).strip()
        )
    )
    rejected_packet = (
        deepcopy(dict(invalid_packet))
        if isinstance(invalid_packet, Mapping)
        else {}
    )
    history = [
        _compact_attempt(row)
        for row in attempt_history or ()
        if isinstance(row, Mapping)
    ][-3:]
    error_rows = [
        {
            "error_id": "formalizer_validation_error:"
            + stable_hash([validation_label, index, message])[:16],
            "index": index,
            "source": "local_formalizer_packet_validator",
            "message": message,
        }
        for index, message in enumerate(errors)
    ]
    feedback_id = "formalizer_validation_feedback:" + stable_hash(
        [
            validation_label,
            errors,
            stable_hash(rejected_packet) if rejected_packet else "",
            max(0, int(retry_depth)),
        ]
    )[:20]
    return {
        "schema_version": FORMALIZER_REPAIR_FEEDBACK_SCHEMA_VERSION,
        "artifact_kind": "FormalizerValidationFeedbackEnvelope",
        "feedback_id": feedback_id,
        "producer": "local_formalizer_packet_validator",
        "validation_label": validation_label,
        "validation_errors": error_rows,
        "validation_error_messages": errors,
        "validation_error_fingerprint": stable_hash(errors),
        "rejected_packet_available": bool(rejected_packet),
        "rejected_packet_fingerprint": (
            stable_hash(rejected_packet) if rejected_packet else ""
        ),
        "rejected_packet_projection": _compact_rejected_packet(rejected_packet),
        "attempt_history": history,
        "retry_depth": max(0, int(retry_depth)),
        "repair_authority": {
            "model_owns": [
                "mathematical_decomposition",
                "formal_target_selection",
                "Lean_candidate_source",
                "repair_or_typed_blocker_decision",
            ],
            "runtime_owns": [
                "artifact_identity_and_lineage",
                "retry_and_resource_budget",
                "response_schema_and_local_validation",
                "tool_execution_and_environment_observations",
                "proof_evidence_and_kernel_authority",
            ],
            "runtime_selected_semantics": False,
        },
        "acceptance_contract": {
            "same_response_schema": True,
            "same_local_validators": True,
            "preserve_task_and_artifact_lineage": True,
            "allow_model_authored_typed_blocker": True,
            "compiler_or_validator_feedback_is_not_proof": True,
            "kernel_verification_required_for_proof": True,
        },
        "boundary": FORMALIZER_VALIDATION_FEEDBACK_BOUNDARY,
    }


def _compact_attempt(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(row[key])
        for key in (
            "attempt_index",
            "ok",
            "repair_mode",
            "errors",
            "raw_response_fingerprint",
            "patched_paths",
            "response_metadata",
        )
        if key in row
    }


def _compact_tool_observation(row: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "candidate_id",
        "candidate_kind",
        "source_field",
        "source_hash",
        "artifact_path",
        "kernel_check_artifact_path",
        "proof_state_artifact_path",
        "target_lean_file",
        "target_lean_line",
        "target_lean_column",
        "target_lean_declaration",
        "target_ids",
        "target_theorem_goal_ids",
        "target_theorem_name",
        "precheck_status",
        "precheck_errors",
        "local_lean_attempted",
        "local_lean_compiled",
        "local_lean_exit_status",
        "local_lean_stdout_excerpt",
        "local_lean_stderr_excerpt",
        "local_lean_command",
        "local_lean_project",
        "local_lean_timeout",
        "local_lean_skipped_reason",
        "residual_goals",
        "diagnostics",
        "requested_tools",
        "executed_tools",
    )
    return {
        key: _compact_value(row[key], depth=0)
        for key in keys
        if key in row and row[key] not in (None, "", [], {})
    }


def _compact_rejected_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    if not packet:
        return {}
    preferred_keys = (
        "formal_targets",
        "pseudo_formal_proof_packets",
        "source_to_bridge_premise_derivation_candidates",
        "source_to_bridge_premise_derivation_candidate_requests",
        "proof_bank_obligation_requests",
        "lemma_dependency_plan",
        "retrieval_queries",
        "proof_search_plan",
        "gap_taxonomy",
        "critic_findings",
        "next_actions",
        "theory_trace_alignment",
    )
    return {
        key: _compact_value(packet[key], depth=0)
        for key in preferred_keys
        if key in packet
    }


def _compact_value(value: Any, *, depth: int) -> Any:
    if depth >= 4:
        return "<bounded>"
    if isinstance(value, str):
        return value if len(value) <= 2400 else value[:800] + " ... " + value[-1400:]
    if isinstance(value, Mapping):
        return {
            str(key): _compact_value(child, depth=depth + 1)
            for key, child in list(value.items())[:32]
        }
    if isinstance(value, (list, tuple)):
        return [
            _compact_value(child, depth=depth + 1)
            for child in list(value)[:8]
        ]
    return deepcopy(value)

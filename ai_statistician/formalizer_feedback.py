from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


FORMALIZER_FEEDBACK_SCHEMA_VERSION = 5

FORMALIZER_VALIDATION_FEEDBACK_BOUNDARY = (
    "Formalizer validation feedback is an environment observation, not a source "
    "edit or proof evidence. AgentRuntime owns packet identity, retry "
    "budgets, execution, validation, and proof authority. The model owns the "
    "mathematical decomposition, Lean candidate, and regeneration strategy. Only the "
    "unchanged local validators and active-project Lean/kernel checks can accept "
    "their respective artifacts."
)


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
        "schema_version": FORMALIZER_FEEDBACK_SCHEMA_VERSION,
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
        "rejected_candidate": rejected_packet,
        "rejected_candidate_complete": bool(rejected_packet),
        "attempt_history": history,
        "retry_depth": max(0, int(retry_depth)),
        "regeneration_authority": {
            "model_owns": [
                "mathematical_decomposition",
                "formal_target_selection",
                "Lean_candidate_source",
                "regeneration_or_typed_blocker_decision",
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
            "same_model_regenerates_complete_packet": True,
            "same_response_schema": True,
            "same_local_validators": True,
            "preserve_task_and_artifact_lineage": True,
            "runtime_edits_candidate": False,
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
            "errors",
            "raw_response_fingerprint",
            "response_metadata",
        )
        if key in row
    }

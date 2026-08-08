from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .theory_semantic_material import (
    LEGACY_METRIC_THEORY_MATERIAL_NOT_PROOF_EVIDENCE,
    theory_semantic_material_payload,
)


METRIC_PROTOCOL_PHASE_NOT_REQUIRED = "not_required"
METRIC_PROTOCOL_PHASE_THEORY_PREREQUISITE_PENDING = (
    "theory_prerequisite_pending"
)
METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED = (
    "theory_informed_authoring_required"
)
METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED = (
    "preexecution_review_accepted"
)
METRIC_PROTOCOL_PREEXECUTION_REVIEW_OBSERVATION_KIND = (
    "RuntimeMetricProtocolPreExecutionReviewObservation"
)
METRIC_PROTOCOL_PHASES = (
    METRIC_PROTOCOL_PHASE_NOT_REQUIRED,
    METRIC_PROTOCOL_PHASE_THEORY_PREREQUISITE_PENDING,
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
    METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED,
)


def build_theory_informed_metric_protocol_material(
    *,
    theory_packet: Mapping[str, Any],
    theory_packet_id: str,
    retrieval_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Preserve theory semantics for protocol authoring without execution data."""

    return {
        "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
        **theory_semantic_material_payload(
            theory_packet=theory_packet,
            theory_packet_id=theory_packet_id,
        ),
        "retrieval_context": deepcopy(dict(retrieval_context or {})),
        "proof_evidence_status": (
            LEGACY_METRIC_THEORY_MATERIAL_NOT_PROOF_EVIDENCE
        ),
        "boundary": (
            "This is a lossless semantic handoff from a TheoryDeveloper proposal "
            "to pre-execution metric-protocol authoring. It contains no generated "
            "code results, simulation results, acceptance decision, or kernel proof."
        ),
    }


def theory_informed_metric_protocol_material(
    architect_context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    context = architect_context or {}
    material = context.get("architect_metric_protocol_theory_material", {})
    if not isinstance(material, Mapping):
        return {}
    if (
        material.get("artifact_kind")
        != "RuntimeTheoryInformedMetricProtocolMaterial"
        or material.get("execution_results_available") is not False
        or not str(material.get("source_theory_packet_id", "") or "").strip()
        or not isinstance(material.get("theory_semantic_material"), Mapping)
        or not material.get("theory_semantic_material")
    ):
        return {}
    return deepcopy(dict(material))


def metric_protocol_authority_matches_theory(
    *,
    source_theory_packet_id: Any,
    source_theory_packet_hash: Any,
    theory_material: Mapping[str, Any] | None,
) -> bool:
    """Require an execution authority to name the exact current theory bytes."""

    material = theory_material or {}
    current_packet_id = str(
        material.get("source_theory_packet_id", "") or ""
    ).strip()
    current_packet_hash = str(
        material.get("source_theory_packet_hash", "") or ""
    ).strip()
    return bool(
        current_packet_id
        and current_packet_hash
        and str(source_theory_packet_id or "").strip() == current_packet_id
        and str(source_theory_packet_hash or "").strip() == current_packet_hash
    )


def reviewed_metric_protocol_authority_matches_theory(
    *,
    evidence_contract: Mapping[str, Any] | None,
    metric_authoring: Mapping[str, Any] | None,
    theory_material: Mapping[str, Any] | None,
) -> bool:
    """Check whether either reviewed authority is bound to the current theory."""

    contract = evidence_contract or {}
    review = contract.get(
        "empirical_metric_requirements_preexecution_review", {}
    )
    review = review if isinstance(review, Mapping) else {}
    contract_authorized = bool(
        contract.get("empirical_metric_requirements")
        and contract.get("empirical_metric_protocol_phase")
        == METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED
        and contract.get("metric_protocol_execution_authorized") is True
        and review.get("overall_verdict") == "ACCEPT"
        and str(
            review.get("reviewed_empirical_metric_requirement_set_id", "") or ""
        )
        == str(contract.get("empirical_metric_requirement_set_id", "") or "")
        and str(contract.get("empirical_metric_requirement_set_id", "") or "")
        and metric_protocol_authority_matches_theory(
            source_theory_packet_id=review.get("source_theory_packet_id", ""),
            source_theory_packet_hash=review.get(
                "source_theory_packet_hash", ""
            ),
            theory_material=theory_material,
        )
    )
    authoring = metric_authoring or {}
    authoring_authorized = bool(
        authoring.get("empirical_metric_requirements")
        and authoring.get("semantic_review_status") == "ACCEPT"
        and authoring.get("semantic_review_independent_agent") is True
        and authoring.get("semantic_review_independent_invocation") is True
        and str(authoring.get("empirical_metric_requirement_set_id", "") or "")
        and metric_protocol_authority_matches_theory(
            source_theory_packet_id=authoring.get(
                "source_theory_packet_id", ""
            ),
            source_theory_packet_hash=authoring.get(
                "source_theory_packet_hash", ""
            ),
            theory_material=theory_material,
        )
    )
    return contract_authorized or authoring_authorized

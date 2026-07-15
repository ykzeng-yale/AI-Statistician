from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .fingerprint import stable_hash


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
METRIC_PROTOCOL_PHASES = (
    METRIC_PROTOCOL_PHASE_NOT_REQUIRED,
    METRIC_PROTOCOL_PHASE_THEORY_PREREQUISITE_PENDING,
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
    METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED,
)


_THEORY_PACKET_NON_SEMANTIC_FIELDS = {
    "created_at",
    "llm_json_repair_attempts",
    "llm_json_repair_history",
    "ok",
    "raw_response",
    "raw_response_fingerprint",
    "runtime_architect_control",
    "validation_errors",
}


def build_theory_informed_metric_protocol_material(
    *,
    theory_packet: Mapping[str, Any],
    theory_packet_id: str,
) -> dict[str, Any]:
    """Preserve theory semantics for protocol authoring without execution data."""

    semantic_material = {
        str(key): deepcopy(value)
        for key, value in theory_packet.items()
        if str(key) not in _THEORY_PACKET_NON_SEMANTIC_FIELDS
    }
    source_packet_id = str(
        theory_packet_id or theory_packet.get("packet_id", "") or ""
    ).strip()
    return {
        "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
        "source_theory_packet_id": source_packet_id,
        "source_theory_packet_hash": stable_hash(dict(theory_packet)),
        "theory_semantic_material": semantic_material,
        "execution_results_available": False,
        "proof_evidence_status": (
            "THEORY_INFORMED_METRIC_PROTOCOL_MATERIAL_NOT_PROOF_EVIDENCE"
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

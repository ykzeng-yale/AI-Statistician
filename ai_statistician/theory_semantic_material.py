from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .fingerprint import stable_hash


THEORY_SEMANTIC_MATERIAL_KIND = "RuntimeTheorySemanticMaterial"
LEGACY_METRIC_THEORY_MATERIAL_KIND = (
    "RuntimeTheoryInformedMetricProtocolMaterial"
)
THEORY_SEMANTIC_MATERIAL_NOT_PROOF_EVIDENCE = (
    "THEORY_SEMANTIC_MATERIAL_NOT_PROOF_EVIDENCE"
)
LEGACY_METRIC_THEORY_MATERIAL_NOT_PROOF_EVIDENCE = (
    "THEORY_INFORMED_METRIC_PROTOCOL_MATERIAL_NOT_PROOF_EVIDENCE"
)
THEORY_SEMANTIC_MATERIAL_KINDS = frozenset(
    {
        THEORY_SEMANTIC_MATERIAL_KIND,
        LEGACY_METRIC_THEORY_MATERIAL_KIND,
    }
)
THEORY_SEMANTIC_MATERIAL_PROOF_STATUSES = frozenset(
    {
        THEORY_SEMANTIC_MATERIAL_NOT_PROOF_EVIDENCE,
        LEGACY_METRIC_THEORY_MATERIAL_NOT_PROOF_EVIDENCE,
    }
)

_THEORY_PACKET_NON_SEMANTIC_FIELDS = frozenset(
    {
        "created_at",
        "llm_json_repair_attempts",
        "llm_json_repair_history",
        "ok",
        "raw_response",
        "raw_response_fingerprint",
        "runtime_architect_control",
        "validation_errors",
    }
)


def theory_semantic_material_payload(
    *,
    theory_packet: Mapping[str, Any],
    theory_packet_id: str,
) -> dict[str, Any]:
    """Return immutable semantic bytes and identity without a consumer label."""

    source_packet_id = str(
        theory_packet_id or theory_packet.get("packet_id", "") or ""
    ).strip()
    return {
        "source_theory_packet_id": source_packet_id,
        "source_theory_packet_hash": stable_hash(dict(theory_packet)),
        "theory_semantic_material": {
            str(key): deepcopy(value)
            for key, value in theory_packet.items()
            if str(key) not in _THEORY_PACKET_NON_SEMANTIC_FIELDS
        },
        "execution_results_available": False,
    }


def build_theory_semantic_material(
    *,
    theory_packet: Mapping[str, Any],
    theory_packet_id: str,
) -> dict[str, Any]:
    """Build a consumer-neutral, non-proof theory revision parent."""

    return {
        "artifact_kind": THEORY_SEMANTIC_MATERIAL_KIND,
        **theory_semantic_material_payload(
            theory_packet=theory_packet,
            theory_packet_id=theory_packet_id,
        ),
        "proof_evidence_status": THEORY_SEMANTIC_MATERIAL_NOT_PROOF_EVIDENCE,
        "boundary": (
            "This is a lossless immutable projection of one TheoryDeveloper "
            "proposal for a downstream semantic handoff. It contains no execution "
            "result, acceptance decision, or kernel proof."
        ),
    }

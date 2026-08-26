from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .fingerprint import stable_hash
from .theory_workspace import THEORY_WORKSPACE_CONTENT_AUTHORITY


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

_THEORY_PACKET_SEMANTIC_FIELDS = (
    "artifact_kind",
    "packet_id",
    "question",
    "problem_card",
    "theory_derivation_packet",
    "estimator_specs",
    "estimator_interface_authoring",
    "theorem_cards",
    "lemma_cards",
    "proof_plan",
    "formalization_requests",
    "simulation_ademp_spec",
    "critic_findings",
    "next_actions",
    "theory_workspace_manifest",
    "theory_content_authority",
    "structured_handoff_role",
    "proof_evidence_boundary",
)


def theory_semantic_material_payload(
    *,
    theory_packet: Mapping[str, Any],
    theory_packet_id: str,
) -> dict[str, Any]:
    """Return current substantive theory state and its complete source identity."""

    source_packet_id = str(
        theory_packet_id or theory_packet.get("packet_id", "") or ""
    ).strip()
    semantic_packet = deepcopy(dict(theory_packet))
    derivation = semantic_packet.get("theory_derivation_packet")
    if isinstance(derivation, Mapping) and theory_packet.get(
        "theory_content_authority"
    ) == THEORY_WORKSPACE_CONTENT_AUTHORITY:
        semantic_packet["theory_derivation_packet"] = {
            field: deepcopy(derivation[field])
            for field in ("claim_index", "sanity_check_index",
                          "formalization_handoff")
            if field in derivation
        }
    return {
        "source_theory_packet_id": source_packet_id,
        "source_theory_packet_hash": stable_hash(dict(theory_packet)),
        "theory_semantic_material": {
            field: deepcopy(semantic_packet[field])
            for field in _THEORY_PACKET_SEMANTIC_FIELDS
            if field in semantic_packet
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
            "This is an immutable projection of the current substantive state of one "
            "TheoryDeveloper proposal. Provider transport, tool history, prior drafts, "
            "and runtime telemetry are separate evidence artifacts and are not semantic "
            "review inputs. This contains no execution result, acceptance decision, or "
            "kernel proof."
        ),
    }

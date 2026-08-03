from __future__ import annotations

from ai_statistician.fingerprint import stable_hash
from ai_statistician.metric_protocol_stage import (
    build_theory_informed_metric_protocol_material,
)
from ai_statistician.theory_semantic_material import (
    THEORY_SEMANTIC_MATERIAL_KIND,
    THEORY_SEMANTIC_MATERIAL_NOT_PROOF_EVIDENCE,
    build_theory_semantic_material,
)
from ai_statistician.theory_revision_lineage import (
    build_theory_developer_revision_binding,
    theory_developer_revision_binding_errors,
)


def _theory_packet() -> dict:
    return {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:consumer-neutral",
        "question": {"id": "question:consumer-neutral"},
        "problem_card": {"estimand": "theta"},
        "runtime_architect_control": {"status": "PRESENT"},
        "validation_errors": [],
    }


def test_theory_semantic_material_is_consumer_neutral_and_nonproof() -> None:
    packet = _theory_packet()

    material = build_theory_semantic_material(
        theory_packet=packet,
        theory_packet_id=packet["packet_id"],
    )

    assert material["artifact_kind"] == THEORY_SEMANTIC_MATERIAL_KIND
    assert material["source_theory_packet_hash"] == stable_hash(packet)
    assert material["execution_results_available"] is False
    assert material["proof_evidence_status"] == (
        THEORY_SEMANTIC_MATERIAL_NOT_PROOF_EVIDENCE
    )
    assert "runtime_architect_control" not in material["theory_semantic_material"]
    assert "validation_errors" not in material["theory_semantic_material"]


def test_metric_protocol_wrapper_keeps_legacy_consumer_identity() -> None:
    packet = _theory_packet()

    generic = build_theory_semantic_material(
        theory_packet=packet,
        theory_packet_id=packet["packet_id"],
    )
    metric = build_theory_informed_metric_protocol_material(
        theory_packet=packet,
        theory_packet_id=packet["packet_id"],
    )

    assert metric["artifact_kind"] == (
        "RuntimeTheoryInformedMetricProtocolMaterial"
    )
    assert metric["source_theory_packet_id"] == generic[
        "source_theory_packet_id"
    ]
    assert metric["source_theory_packet_hash"] == generic[
        "source_theory_packet_hash"
    ]
    assert metric["theory_semantic_material"] == generic[
        "theory_semantic_material"
    ]


def test_theory_revision_binding_accepts_generic_material_only_as_nonproof() -> None:
    packet = _theory_packet()
    material = build_theory_semantic_material(
        theory_packet=packet,
        theory_packet_id=packet["packet_id"],
    )
    feedback = {
        "feedback_id": "feedback:consumer-neutral",
        "question_id": "question:consumer-neutral",
        "findings": [{"required_change": "Revise the semantic claim."}],
    }
    binding = build_theory_developer_revision_binding(
        revision_source="independent_semantic_review",
        question_id="question:consumer-neutral",
        source_feedback=feedback,
        theory_material=material,
        feedback_id=feedback["feedback_id"],
        upstream_theory_revision_count=1,
        max_upstream_theory_revisions=1,
        execution_results_observed=True,
    )

    assert theory_developer_revision_binding_errors(
        binding,
        question_id="question:consumer-neutral",
    ) == []

    binding["theory_material"]["proof_evidence_status"] = "KERNEL_VERIFIED"
    assert "theory revision parent crossed the proof boundary" in (
        theory_developer_revision_binding_errors(
            binding,
            question_id="question:consumer-neutral",
        )
    )

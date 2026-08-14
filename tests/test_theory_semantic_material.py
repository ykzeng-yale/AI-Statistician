from __future__ import annotations

import pytest

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
    THEORY_CLAIM_REVISION_DELTA_KIND,
    build_theory_claim_revision_delta,
    build_theory_developer_revision_binding,
    resolve_theory_developer_revision_parent_material,
    theory_developer_revision_binding_errors,
)
from ai_statistician.theory_workspace import THEORY_WORKSPACE_CONTENT_AUTHORITY


def _theory_packet() -> dict:
    return {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:consumer-neutral",
        "question": {"id": "question:consumer-neutral"},
        "problem_card": {"estimand": "theta"},
        "estimator_specs": [
            {"id": "current-estimator", "formula": "log integral Lambda"}
        ],
        "llm_client_tool_loop": {
            "history": [
                {
                    "role": "tool",
                    "content": "stale draft used integral log Lambda",
                }
            ]
        },
        "provider": "anthropic",
        "model": "test-model",
        "runtime_architect_control": {"status": "PRESENT"},
        "validation_errors": [],
    }


def _document_theory_packet(
    *,
    packet_id: str,
    claims: list[dict],
    notes_sha256: str,
) -> dict:
    return {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": packet_id,
        "question": {"id": "question:claim-revision"},
        "theory_content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
        "theory_derivation_packet": {"claim_index": claims},
        "theory_workspace_manifest": {
            "document_set_hash": stable_hash(
                [("theory.md", "a" * 64), ("notes.md", notes_sha256)]
            ),
            "documents": [
                {
                    "document_id": "theory-document",
                    "relative_path": "theory.md",
                    "sha256": "a" * 64,
                    "byte_size": 100,
                },
                {
                    "document_id": "notes-document",
                    "relative_path": "notes.md",
                    "sha256": notes_sha256,
                    "byte_size": 40,
                },
            ],
        },
    }


def test_claim_revision_delta_contains_only_hash_bound_reference_changes() -> None:
    parent = _document_theory_packet(
        packet_id="theory:parent",
        notes_sha256="b" * 64,
        claims=[
            {
                "id": "C0",
                "kind": "assumption",
                "status": "SUPPORTED",
                "document_path": "theory.md",
                "anchor": "C0",
                "depends_on": [],
            },
            {
                "id": "C1",
                "kind": "theorem",
                "status": "OPEN",
                "document_path": "theory.md",
                "anchor": "C1",
                "depends_on": ["C0"],
            },
            {
                "id": "OLD",
                "kind": "lemma",
                "status": "INCONCLUSIVE",
                "document_path": "theory.md",
                "anchor": "OLD",
                "depends_on": ["C0"],
            },
        ],
    )
    revised = _document_theory_packet(
        packet_id="theory:revised",
        notes_sha256="c" * 64,
        claims=[
            {
                "id": "C0",
                "kind": "assumption",
                "status": "SUPPORTED",
                "document_path": "theory.md",
                "anchor": "C0",
                "depends_on": [],
            },
            {
                "id": "C1",
                "kind": "theorem",
                "status": "SUPPORTED",
                "document_path": "theory.md",
                "anchor": "C1",
                "depends_on": [],
            },
            {
                "id": "C2",
                "kind": "lemma",
                "status": "OPEN",
                "document_path": "theory.md",
                "anchor": "C2",
                "depends_on": ["C1"],
            },
        ],
    )

    delta = build_theory_claim_revision_delta(
        parent_theory_packet=parent,
        revised_theory_packet=revised,
    )

    assert delta["artifact_kind"] == THEORY_CLAIM_REVISION_DELTA_KIND
    assert delta["parent_theory_packet_hash"] == stable_hash(parent)
    assert delta["revised_theory_packet_hash"] == stable_hash(revised)
    assert [row["claim_id"] for row in delta["added_claim_refs"]] == ["C2"]
    assert [row["claim_id"] for row in delta["removed_claim_refs"]] == ["OLD"]
    assert [row["claim_id"] for row in delta["changed_claim_refs"]] == ["C1"]
    assert set(delta["changed_claim_refs"][0]["changes"]) == {
        "status",
        "depends_on",
    }
    assert delta["changed_document_refs"][0]["document_path"] == "notes.md"
    assert delta["counts"] == {
        "parent_claims": 3,
        "revised_claims": 3,
        "unchanged_claims": 1,
        "added_claims": 1,
        "removed_claims": 1,
        "changed_claims": 1,
        "changed_documents": 1,
    }
    assert "mathematical body" in delta["boundary"]
    assert "statement" not in str(delta)

    material = build_theory_informed_metric_protocol_material(
        theory_packet=revised,
        theory_packet_id=revised["packet_id"],
        theory_claim_revision_delta=delta,
    )
    delta["counts"]["changed_claims"] = 99
    assert material["theory_claim_revision_delta"]["counts"][
        "changed_claims"
    ] == 1


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
    assert "llm_client_tool_loop" not in material["theory_semantic_material"]
    assert "provider" not in material["theory_semantic_material"]
    assert "model" not in material["theory_semantic_material"]
    assert material["theory_semantic_material"]["estimator_specs"] == [
        {"id": "current-estimator", "formula": "log integral Lambda"}
    ]
    assert "stale draft" not in str(material["theory_semantic_material"])


def test_metric_protocol_wrapper_keeps_legacy_consumer_identity() -> None:
    packet = _theory_packet()
    retrieval_context = {
        "knowledge_cards": [{"id": "card:generic", "summary": "source"}],
        "boundary": "Retrieval context is not proof evidence.",
    }

    generic = build_theory_semantic_material(
        theory_packet=packet,
        theory_packet_id=packet["packet_id"],
    )
    metric = build_theory_informed_metric_protocol_material(
        theory_packet=packet,
        theory_packet_id=packet["packet_id"],
        retrieval_context=retrieval_context,
    )
    retrieval_context["knowledge_cards"][0]["summary"] = "mutated"

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
    assert metric["retrieval_context"]["knowledge_cards"][0]["summary"] == (
        "source"
    )


def test_theory_revision_binding_uses_exact_nonproof_parent_reference() -> None:
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
        parent_theory_packet=packet,
        feedback_id=feedback["feedback_id"],
        upstream_theory_revision_count=1,
        max_upstream_theory_revisions=1,
        execution_results_observed=True,
    )

    assert theory_developer_revision_binding_errors(
        binding,
        question_id="question:consumer-neutral",
    ) == []
    assert binding["parent_theory_packet_ref"] == {
        "artifact_kind": "RuntimeArtifactRef",
        "reference_scope": "runtime_blackboard",
        "artifact_id": packet["packet_id"],
        "content_hash": stable_hash(packet),
        "payload_kind": "TheoryDerivationPacket",
        "evidence_status": "REFERENCE_ONLY_NOT_EVIDENCE",
    }
    assert "theory_material" not in binding
    assert resolve_theory_developer_revision_parent_material(
        revision_binding=binding,
        artifacts={packet["packet_id"]: packet},
    ) == material

    tampered_packet = {**packet, "problem_card": {"estimand": "changed"}}
    with pytest.raises(ValueError, match="unavailable or stale"):
        resolve_theory_developer_revision_parent_material(
            revision_binding=binding,
            artifacts={packet["packet_id"]: tampered_packet},
        )

    binding["parent_theory_packet_ref"]["evidence_status"] = "KERNEL_VERIFIED"
    assert "theory revision parent reference crossed the evidence boundary" in (
        theory_developer_revision_binding_errors(
            binding,
            question_id="question:consumer-neutral",
        )
    )

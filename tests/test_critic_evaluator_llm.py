from __future__ import annotations

from ai_statistician.critic_evaluator_llm import (
    CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE,
    build_critic_evaluator_prompt,
    validate_critic_evaluator_packet,
)
from ai_statistician.research_schema import OpenResearchQuestion


def _critic_packet() -> dict[str, object]:
    return {
        "current_observation_assessment": {
            "observed_failure": "Two artifacts state incompatible target identities.",
            "evidence_refs": ["artifact:a", "artifact:b"],
            "causal_hypotheses": [],
            "independent_missing_evidence": [],
        },
        "coordination_assessment": {
            "scope": "cross_workspace",
            "conflicting_artifact_ids": ["artifact:a", "artifact:b"],
            "rationale": "The exact target identities differ.",
        },
        "evidence_boundary_audit": [
            {
                "artifact_id": "artifact:a",
                "evidence_type": "theory",
                "boundary_ok": True,
                "observed_claim": "target a",
                "authority_boundary": "proposal",
                "boundary_observation": "not proof",
            }
        ],
        "critic_findings": [
            {
                "critic": "independent",
                "finding": "Artifact identities conflict.",
                "evidence_refs": ["artifact:a", "artifact:b"],
                "uncertainty": "low",
            }
        ],
        "proof_evidence_status": CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE,
        "kernel_verified": False,
        "full_frontier_theorem_proved": False,
    }


def test_cross_workspace_scope_requires_two_exact_artifact_ids() -> None:
    packet = _critic_packet()
    assert validate_critic_evaluator_packet(packet) == []

    packet["coordination_assessment"] = {
        "scope": "cross_workspace",
        "conflicting_artifact_ids": ["artifact:a"],
        "rationale": "Several lanes failed.",
    }

    assert (
        "cross_workspace coordination requires at least two distinct exact "
        "conflicting_artifact_ids"
    ) in validate_critic_evaluator_packet(packet)


def test_critic_prompt_references_large_workspace_artifacts_without_copying_them() -> None:
    repeated_source = "UNIQUE_FULL_SOURCE_SENTINEL\n" * 50_000
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:large",
        "theorem_cards": [{"derivation": repeated_source}],
        "ok": True,
    }
    algorithm_manifest = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm:large",
        "theory_packet_id": "theory:large",
        "n_executed": 2,
        "n_passed": 2,
        "prototypes": [{"source": repeated_source}],
    }
    current_observation = {
        "feedback_id": "observation:current",
        "failure_classification": "formalizer_workspace_exhausted",
        "raw_stderr": "exact current diagnostic",
    }

    prompt = build_critic_evaluator_prompt(
        question=OpenResearchQuestion(
            id="large-critic-context",
            title="Audit a large workspace",
            description="Keep final audit context reference-driven.",
        ),
        retrieval_manifest={"manifest_id": "retrieval:large"},
        theory_packet=theory_packet,
        simulation_manifest={"manifest_id": "simulation:large"},
        algorithm_manifest=algorithm_manifest,
        formalization_manifest={
            "manifest_id": "formalization:large",
            "counts": {"formal_gap": 1, "kernel_verified": 0},
        },
        environment_feedback=current_observation,
    )

    assert len(prompt) < 30_000
    assert "UNIQUE_FULL_SOURCE_SENTINEL" not in prompt
    assert '"packet_id":"theory:large"' in prompt
    assert '"manifest_id":"algorithm:large"' in prompt
    assert '"content_hash"' in prompt
    assert '"raw_stderr":"exact current diagnostic"' in prompt

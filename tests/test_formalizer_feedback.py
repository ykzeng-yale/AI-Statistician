from __future__ import annotations

import json
from copy import deepcopy

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.formalizer_llm import (
    FORMALIZER_MAX_ACTIVE_TARGETS,
    _build_lean_candidate_workspace_tool_prompt,
    validate_formalizer_packet,
)
from ai_statistician.formalizer_feedback import (
    formalizer_validation_feedback_envelope,
)
from ai_statistician.research_schema import OpenResearchQuestion


def test_formalizer_packet_owns_exactly_one_active_target() -> None:
    packet = {
        "formal_targets": [
            {"id": "target:one", "expected_status": "OPEN"},
            {"id": "target:two", "expected_status": "OPEN"},
        ],
        "retrieval_queries": [],
        "gap_taxonomy": [],
        "proof_evidence_status": "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE",
        "kernel_verified": False,
        "full_frontier_theorem_proved": False,
    }

    assert FORMALIZER_MAX_ACTIVE_TARGETS == 1
    assert "Formalizer workspace must own exactly one active formal target" in (
        validate_formalizer_packet(packet)
    )


@pytest.mark.parametrize("error", [
    "arbitrary future validator failure: field zeta is inconsistent",
    "type mismatch in a model-authored declaration",
    "unclassified observation, not an instruction to edit the candidate",
])
def test_formalizer_feedback_preserves_opaque_candidate_in_model_prompt(error: str) -> None:
    rejected = {
        "formal_targets": [
            {"id": f"target:{index}", "lean_statement_sketch": "a" * 3000 + "MID" + "b" * 3000}
            for index in range(10)
        ],
        "future_field": {"nested": {"deeper": {"values": [None, False, 0, ""]}}},
        "metadata": {f"field_{index}": index for index in range(40)},
    }
    original = deepcopy(rejected)
    feedback = formalizer_validation_feedback_envelope(
        [error],
        invalid_packet=rejected,
        attempt_history=[{"attempt_index": 1, "ok": False}],
        retry_depth=1,
    )

    assert feedback["validation_error_messages"] == [error]
    assert feedback["rejected_candidate"] == original
    assert feedback["rejected_candidate_complete"] is True
    assert feedback["rejected_packet_fingerprint"] == stable_hash(original)
    assert "rejected_packet_projection" not in feedback
    assert feedback["regeneration_authority"]["runtime_selected_semantics"] is False
    assert feedback["acceptance_contract"]["runtime_edits_candidate"] is False
    assert feedback["acceptance_contract"]["kernel_verification_required_for_proof"] is True
    assert rejected == original

    prompt = json.loads(_build_lean_candidate_workspace_tool_prompt(
        question=OpenResearchQuestion(id="opaque", title="Opaque feedback", description="Inspect exact observations."),
        theory_packet={}, parent_packet={}, candidate_id="target:0",
        candidate_source_field="formal_targets", candidate_lean_declaration="",
        initial_source="", environment_feedback={"formalizer_validation_feedback": feedback},
    ))
    observation = prompt["runtime_observations"]["validator_observation"]
    assert observation["validation_error_messages"] == [error]
    assert observation["rejected_candidate"] == original
    assert observation["rejected_candidate_complete"] is True
    assert observation["rejected_packet_fingerprint"] == stable_hash(original)

    rejected["future_field"].clear()
    feedback["rejected_candidate"]["metadata"].clear()
    assert observation["rejected_candidate"] == original


def test_formalizer_feedback_does_not_invent_an_absent_candidate() -> None:
    feedback = formalizer_validation_feedback_envelope(["no complete packet received"])
    assert feedback["rejected_candidate"] == {}
    assert feedback["rejected_candidate_complete"] is False
    assert feedback["rejected_packet_fingerprint"] == ""

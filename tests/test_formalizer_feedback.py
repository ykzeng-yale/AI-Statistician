from __future__ import annotations

import inspect

import ai_statistician.formalizer_feedback as feedback_module
from ai_statistician.formalizer_llm import (
    FORMALIZER_MAX_ACTIVE_TARGETS,
    validate_formalizer_packet,
)
from ai_statistician.formalizer_feedback import (
    formalizer_validation_feedback_envelope,
)


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


def test_formalizer_repair_feedback_is_observation_not_rule_table() -> None:
    source = inspect.getsource(feedback_module)
    assert "trigger_markers" not in source
    assert "violation_family" not in source
    assert "prompt_directive" not in source
    assert "error_text" not in source

    error = "arbitrary future validator failure: field zeta is inconsistent"
    rejected = {
        "formal_targets": [{"id": "target:zeta", "unexpected": "value"}],
        "next_actions": [{"id": "action:zeta"}],
    }
    feedback = formalizer_validation_feedback_envelope(
        [error],
        invalid_packet=rejected,
        attempt_history=[{"attempt_index": 1, "ok": False}],
        retry_depth=1,
    )

    assert feedback["validation_error_messages"] == [error]
    assert feedback["rejected_packet_projection"] == rejected
    assert feedback["regeneration_authority"]["runtime_selected_semantics"] is False
    assert feedback["regeneration_authority"]["model_owns"]
    assert "rules" not in feedback
    assert "directives" not in feedback

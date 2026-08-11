from __future__ import annotations

import inspect
import json

import ai_statistician.formalizer_feedback as feedback_module
from ai_statistician.fingerprint import stable_hash
from ai_statistician.formalizer_llm import build_formalizer_prompt
from ai_statistician.formalizer_feedback import (
    formalizer_validation_feedback_envelope,
)
from ai_statistician.research_schema import OpenResearchQuestion


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


def test_formalizer_prompt_carries_exact_feedback_without_runtime_repair_recipe() -> None:
    error = "future validator says the emitted artifact does not satisfy omega"
    rejected_candidate = {
        "formal_targets": [{"id": "omega"}],
        "full_candidate_tail_marker": "FULL_FORMALIZER_PACKET_TAIL",
    }
    feedback = formalizer_validation_feedback_envelope(
        [error],
        invalid_packet=rejected_candidate,
    )
    prompt = build_formalizer_prompt(
        question=OpenResearchQuestion(
            id="generic_formalizer_repair",
            title="Generic Formalizer repair",
            description="Repair a model-authored packet from environment feedback.",
            tags=("formalizer",),
        ),
        theory_packet={"packet_id": "theory:generic-repair"},
        simulation_manifest={"manifest_id": "simulation:generic-repair"},
        algorithm_manifest={"manifest_id": "algorithm:generic-repair"},
        registered_problem={"question_id": "generic_formalizer_repair"},
        theorem_goals=[],
        environment_feedback={
            "failure_classification": "formalizer_packet_validation_failed",
            "formalizer_validation_feedback": feedback,
            "rejected_candidate": rejected_candidate,
            "rejected_candidate_fingerprint": stable_hash(rejected_candidate),
        },
    )
    payload = json.loads(prompt[prompt.index('{"question":') :])
    carried = payload["runtime_environment_feedback"][
        "formalizer_validation_feedback"
    ]

    assert carried["feedback_id"] == feedback["feedback_id"]
    assert carried["validation_error_messages"] == [error]
    assert payload["runtime_environment_feedback"]["rejected_candidate"] == (
        rejected_candidate
    )
    assert payload["runtime_environment_feedback"][
        "rejected_candidate_fingerprint"
    ] == stable_hash(rejected_candidate)
    assert "validation_repair_policy" not in prompt
    assert "validation_repair_directives" not in prompt
    assert "pseudo_formalization_required_packet_seed" not in prompt
    assert "pseudo_formalization_required_copy_fragment" not in prompt
    assert any(
        "does not prescribe field-specific corrections" in instruction
        for instruction in payload["model_owned_feedback_instructions"]
    )


def test_repeated_parser_failure_is_observation_not_runtime_lane_policy() -> None:
    question = OpenResearchQuestion(
        id="generic_parser_feedback",
        title="Generic parser feedback",
        description="Regenerate a Lean candidate from exact parser observations.",
        tags=("formalizer",),
    )
    common = {
        "question": question,
        "theory_packet": {"packet_id": "theory:parser-feedback"},
        "simulation_manifest": {},
        "algorithm_manifest": {},
        "registered_problem": {},
        "theorem_goals": [],
    }
    baseline = build_formalizer_prompt(
        **common,
        environment_feedback={},
    )
    observed = build_formalizer_prompt(
        **common,
        environment_feedback={
            "local_lean_observation": {
                "diagnostic_classes": ["lean_parser_or_syntax_error"],
                "diagnostics": [
                    {
                        "severity": "error",
                        "message": "unexpected token at line 4 column 9",
                    }
                ],
                "repeated_syntax_failure": True,
            }
        },
    )
    baseline_payload = json.loads(baseline[baseline.index('{"question":') :])
    observed_payload = json.loads(observed[observed.index('{"question":') :])

    assert observed_payload["runtime_environment_feedback"][
        "local_lean_observation"
    ]["diagnostics"][0]["message"] == "unexpected token at line 4 column 9"
    assert observed_payload["required_output_contract"] == baseline_payload[
        "required_output_contract"
    ]
    assert observed_payload.get("pseudo_formalization_contract", {}) == {}

from __future__ import annotations

import json
from copy import deepcopy

from ai_statistician.architect_coordinator_llm import (
    build_architect_feedback_route_prompt,
)
from ai_statistician.research_architect import (
    _theory_workspace_read_only_observations,
)
from ai_statistician.research_schema import OpenResearchQuestion


def _observations() -> dict:
    return {
        "source_subsystem": "AlgorithmEngineer",
        "runtime_errors": ["A previously unseen tool diagnostic."],
        "findings": [{
            "summary": "The observed result disagrees with the cited interface.",
            "required_change": "Model-authored reviewer observation.",
            "evidence_refs": ["execution:1#/stderr"],
        }],
        "tool_output": {
            "recommended_action": "Tool-authored suggestion, not authority.",
            "repair_strategy": {"steps": ["model-authored method"]},
            "next_action": "unrecognized observation value",
        },
        "rejected_candidate": {
            "source": "def estimate(x):\n    return x\n",
            "required_change": "This is candidate data.",
        },
    }


def test_theory_owner_receives_feedback_without_field_name_interpretation() -> None:
    feedback = _observations()
    original = deepcopy(feedback)

    artifacts = _theory_workspace_read_only_observations({"feedback": feedback})

    assert artifacts["reviewer_observations"] == original
    artifacts["reviewer_observations"]["tool_output"]["next_action"] = "changed"
    assert feedback == original


def test_architect_receives_exact_observations_not_a_runtime_route() -> None:
    feedback = _observations()
    original = deepcopy(feedback)
    prompt = build_architect_feedback_route_prompt(
        question=OpenResearchQuestion(
            id="generic-feedback",
            title="Generic feedback",
            description="Choose a research action using the actual observations.",
        ),
        architect_context={},
        environment_feedback=feedback,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])

    assert payload["environment_observations"] == original
    assert payload["routing_contract"]["owner_selected_by_architect_model"] is True
    assert feedback == original

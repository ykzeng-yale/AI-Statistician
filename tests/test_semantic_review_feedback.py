from __future__ import annotations

import json
from copy import deepcopy

from ai_statistician.architect_coordinator_llm import (
    build_architect_feedback_route_prompt,
)
from ai_statistician.research_architect import (
    _initial_theory_authoring_binding_id,
    _initial_theory_workspace_read_only_artifacts,
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


def test_initial_theory_feedback_is_complete_readable_and_identity_bound() -> None:
    feedback = _observations()
    feedback["findings"] *= 12
    feedback["tool_output"]["raw_output"] = "unfamiliar observation\n" * 4000
    context = {
        "environment_feedback": feedback,
        "theory_developer_source_environment_feedback": feedback,
        "runtime_task": {"task_id": "initial", "inputs": {"private": "withheld"}},
        "runtime_learning_memory": {"unrelated": "withheld"},
    }
    original = deepcopy(context)
    artifacts = _initial_theory_workspace_read_only_artifacts(
        question=OpenResearchQuestion(
            id="generic-feedback", title="Generic feedback", description="Inspect observations.",
        ),
        architect_context=context,
        theory_prompt_mode="compact",
        max_tool_calls=10,
        formalization_authoring_required=False,
    )
    initial_context = artifacts["initial_authoring_context"]

    def restore(value):
        if isinstance(value, dict):
            if "client_tool_evidence_document_ref" in value:
                return artifacts["read_only_documents"][value["client_tool_evidence_document_ref"]]
            return {key: restore(child) for key, child in value.items()}
        if isinstance(value, list):
            return [restore(child) for child in value]
        return value

    for key in ("environment_feedback", "theory_developer_source_environment_feedback"):
        reference = initial_context["architect_context"][key]
        document = artifacts["read_only_documents"][reference["workspace_document_path"]]
        assert restore(json.loads(document)) == feedback
        assert max(map(len, document.splitlines())) < 1024
    assert len(json.dumps(initial_context)) < 55_000
    assert "withheld" not in json.dumps(artifacts)
    assert context == original

    def binding(value):
        return _initial_theory_authoring_binding_id(
            question_id="generic-feedback", theory_prompt_mode="compact",
            read_only_artifacts=value,
        )

    changed = deepcopy(artifacts)
    changed["read_only_documents"][reference["workspace_document_path"]] += "\nchanged"
    assert binding(changed) != binding(artifacts)


def test_revision_observations_externalize_exact_text_without_classifying_fields() -> None:
    feedback = _observations()
    feedback["tool_output"]["new_unknown_field"] = "unfamiliar raw observation\n" * 4000
    feedback["rejected_candidate"]["source"] = "model-owned source\n" * 4000
    transport = {"diagnostic": "opaque transport response\n" * 4000}
    inputs = {"feedback": feedback, "transport_feedback": transport}
    original = deepcopy(inputs)
    artifacts = _theory_workspace_read_only_observations(inputs)
    documents = artifacts["read_only_documents"]

    def restore(value):
        if isinstance(value, dict):
            if "client_tool_evidence_document_ref" in value:
                return documents[value["client_tool_evidence_document_ref"]]
            return {key: restore(child) for key, child in value.items()}
        if isinstance(value, list):
            return [restore(child) for child in value]
        return value

    assert restore(artifacts["reviewer_observations"]) == feedback
    assert restore(artifacts["transport_observations"]) == transport
    assert len(json.dumps(artifacts["reviewer_observations"])) < 55_000
    assert len(json.dumps(artifacts["transport_observations"])) < 55_000
    assert inputs == original
    assert _theory_workspace_read_only_observations(inputs) == artifacts


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

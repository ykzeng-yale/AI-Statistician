from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.lean_candidate_identity import (
    LEAN_TARGET_STATEMENT_HASH_ALGORITHM,
    lean_target_statement_hash,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.formal_target_semantic_review_runtime import (
    FormalTargetSemanticReviewerRuntimeSubsystem,
    _runtime_formal_target_semantic_review_dispatch,
)
from ai_statistician.formal_target_semantic_reviewer_llm import (
    FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS,
    FORMAL_TARGET_SEMANTIC_REVIEW_JSON_SCHEMA,
    FormalTargetSemanticReviewerConfig,
    LLMFormalTargetSemanticReviewerAgent,
    build_formal_target_semantic_review_prompt,
    validate_formal_target_semantic_review_packet,
)
from ai_statistician.formalizer_llm import (
    FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
)
from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY,
    PROVIDER_STRUCTURED_OUTPUT_ON_RETRY_METADATA_KEY,
    GeneratorRequest,
    GeneratorResponse,
    StaticJSONGeneratorBackend,
)
from ai_statistician.research_schema import OpenResearchQuestion


def _question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="generic-formal-target-review",
        title="Review an exact formal theorem target",
        description=(
            "Determine whether a generated theorem preserves the supplied "
            "mathematical claim and assumptions."
        ),
        tags=("formalization", "semantic-review"),
    )


def _review_response(*, accepted: bool) -> dict[str, Any]:
    dimensions = [
        {
            "status": "PASS",
            "rationale": f"The exact target preserves {dimension}.",
            "evidence_refs": [f"/exact_formal_target/{dimension}"],
        }
        for dimension in FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS
    ]
    findings: list[dict[str, Any]] = []
    if not accepted:
        dimensions[3]["status"] = "FAIL"
        dimensions[3]["rationale"] = (
            "The supplied target is not justified by the derivation."
        )
        findings.append(
            {
                "severity": "high",
                "category": "mathematical_target_drift",
                "summary": "The target does not establish the requested claim.",
                "observed_behavior": "The conclusion proves only a weaker claim.",
                "expected_behavior": (
                    "The conclusion must match the bound theorem card."
                ),
                "evidence_refs": [
                    "/theory_derivation_packet",
                    "/exact_formal_target",
                ],
            }
        )
    return {"dimension_reviews": dimensions, "findings": findings}


def _reviewer(
    *,
    accepted: bool,
    response: dict[str, Any] | None = None,
) -> LLMFormalTargetSemanticReviewerAgent:
    return LLMFormalTargetSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(
            response if response is not None else _review_response(accepted=accepted)
        ),
        config=FormalTargetSemanticReviewerConfig(
            provider_name="static",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )


class _CapturingBackend:
    provider_name = "static"

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.requests: list[GeneratorRequest] = []

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        self.requests.append(request)
        return GeneratorResponse(
            text=json.dumps(self.responses.pop(0)),
            provider=self.provider_name,
            model=request.model,
        )


def _runtime_fixture(
    tmp_path: Path,
    *,
    accepted: bool,
    response: dict[str, Any] | None = None,
    target_hash_algorithm: str = LEAN_TARGET_STATEMENT_HASH_ALGORITHM,
    revision_count: int = 0,
    max_revisions: int = 2,
    prior_review_feedback: Mapping[str, Any] | None = None,
    workspace_evidence: Mapping[str, Any] | None = None,
) -> tuple[
    FormalTargetSemanticReviewerRuntimeSubsystem,
    AgentTask,
    BlackboardState,
    Path,
]:
    question = _question()
    source = (
        "import Mathlib\n\n"
        "theorem exact_source (p : Prop) (hp : p) : p := by\n"
        "  exact hp\n"
    )
    target_statement = "theorem exact_source (p : Prop) (hp : p) : p"
    source_hash = stable_hash(source)
    target_hash = lean_target_statement_hash(target_statement)
    artifact_path = tmp_path / "exact_source.lean"
    artifact_path.write_text(source, encoding="utf-8")

    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:generic-formal-target-review",
        "theory_derivation_packet": {
            "derivation_steps": [
                {
                    "id": "identity_step",
                    "claim": "A supplied proposition follows from its proof.",
                    "equation_or_argument": "p and hp : p imply p",
                }
            ],
            "assumption_ledger": [
                {"assumption": "hp : p", "used_in": ["identity_step"]}
            ],
        },
        "theorem_cards": [
            {
                "id": "theorem:exact_source",
                "informal_statement": "A proposition follows from its proof.",
                "assumptions_used": ["hp : p"],
                "conclusion": "p",
            }
        ],
    }
    proposal_packet = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer:generic-formal-target-review",
        "source_agent": "LLMFormalizerProofEngineerAgent",
        "model": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        "model_tier": "haiku",
        "formal_targets": [
            {
                "id": "exact_source",
                "formal_target_role": FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
                "lean_statement_sketch": source,
            }
        ],
    }
    candidate_materialization = {
        "schema_version": 1,
        "artifact_kind": "RuntimeFormalizerLeanCandidateMaterialization",
        "manifest_id": "formalizer_lean_candidate_materialization:generic",
        "candidate_rows": [
            {
                "candidate_id": "exact_source",
                "source_field": "formal_targets",
                "formal_target_role": FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
                "artifact_path": str(artifact_path),
                "source_hash": source_hash,
                "target_lean_declaration": "exact_source",
                "target_ids": ["exact_source"],
                "local_lean_attempted": True,
                "local_lean_compiled": False,
                "local_lean_exit_status": "1",
                "local_lean_stderr": "unsolved goals",
            }
        ],
    }
    question_payload = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }
    source_task = AgentTask(
        task_id="formalize:generic-formal-target-review",
        owner_subsystem="FormalizationEvaluator",
        objective="Generate an exact formal target.",
        inputs={
            "question": question_payload,
            "theory_packet_id": theory_packet["packet_id"],
            "architect_context": {
                "runtime_requested_evidence_contract": {
                    "evaluation_mode": "capability_eval"
                },
                "formal_target_semantic_review_revision_count": revision_count,
            },
            **(
                {"environment_feedback": dict(prior_review_feedback)}
                if prior_review_feedback
                else {}
            ),
        },
    )
    target_context = {
        "formalizer_candidate_exact_search_eligible": True,
        "external_proof_search_dispatch_eligible": False,
        "formalizer_candidate_semantic_review_status": (
            "INDEPENDENT_SEMANTIC_FAITHFULNESS_REVIEW_REQUIRED"
        ),
        "candidate_artifact_path": str(artifact_path),
        "lineage_candidate_artifact_hash": source_hash,
        "target_declaration_source_hash": source_hash,
        "target_lean_declaration": "exact_source",
        "target_theorem_statement": target_statement,
        "target_theorem_statement_hash": target_hash,
        "target_theorem_statement_hash_algorithm": target_hash_algorithm,
        "target_ids": ["exact_source"],
        "source_theorem_target_provenance": {
            "source_theorem_target_known": False
        },
    }
    candidate_feedback = {
        "feedback_type": "formalizer_lean_candidate_local_lean_feedback",
        "formalizer_workspace_context": target_context,
    }
    deferred_task = AgentTask(
        task_id="architect-workspace-replan:generic-formal-target-review",
        owner_subsystem="FormalizationEvaluator",
        objective="Replan the unresolved formal workspace after target review.",
        inputs={
            **source_task.inputs,
            "environment_feedback": candidate_feedback,
        },
    )
    dispatch = _runtime_formal_target_semantic_review_dispatch(
        task=source_task,
        question=question,
        source_subsystem="FormalizationEvaluator",
        candidate_materialization=candidate_materialization,
        theory_packet=theory_packet,
        proposal_packet=proposal_packet,
        candidate_feedback=candidate_feedback,
        architect_context=source_task.inputs["architect_context"],
        deferred_next_task=deferred_task,
        blackboard_artifacts={
            theory_packet["packet_id"]: theory_packet,
            proposal_packet["packet_id"]: proposal_packet,
            candidate_materialization["manifest_id"]: candidate_materialization,
        },
        max_revisions=max_revisions,
        formalizer_workspace_evidence=workspace_evidence,
    )
    assert dispatch is not None
    blackboard = BlackboardState(project_id="formal-target-semantic-review-test")
    blackboard.artifacts.update(
        {
            theory_packet["packet_id"]: theory_packet,
            proposal_packet["packet_id"]: proposal_packet,
            candidate_materialization["manifest_id"]: candidate_materialization,
            **dispatch["artifacts"],
        }
    )
    subsystem = FormalTargetSemanticReviewerRuntimeSubsystem(
        reviewer=_reviewer(accepted=accepted, response=response),
        max_revisions=max_revisions,
    )
    return subsystem, dispatch["next_task"], blackboard, artifact_path


def _artifact_of_kind(result: Any, artifact_kind: str) -> dict[str, Any]:
    return next(
        dict(row)
        for row in result.produced_artifacts.values()
        if isinstance(row, dict) and row.get("artifact_kind") == artifact_kind
    )


def test_accept_routes_hash_bound_target_to_model_owned_lean_generation(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accepted=True)

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "FormalizationEvaluator"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["model_owned_complete_source_tool_loop_eligible"] is True
    assert feedback["formalizer_workspace_context"][
        "model_owned_complete_source_tool_loop_eligible"
    ] is True
    assert feedback["formalizer_workspace_context"][
        "formalizer_candidate_semantic_review_status"
    ] == "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
    packet = _artifact_of_kind(result, "FormalTargetSemanticReviewPacket")
    assert packet["model"] == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
    assert packet["model_tier"] == "haiku"
    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["kernel_verified"] is False
    assert validate_formal_target_semantic_review_packet(packet) == []


def test_rejection_returns_observations_to_same_formalizer_workspace(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accepted=False)

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "FormalizationEvaluator"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["model_owned_complete_source_tool_loop_eligible"] is True
    assert feedback["runtime_selected_owner"] is False
    assert feedback["routing_authority"] == "same_formalizer_workspace"
    revision_context = feedback["formalizer_workspace_context"]
    assert revision_context["formalizer_candidate_semantic_review_status"] == (
        "INDEPENDENT_SEMANTIC_REVIEW_REVISE_NOT_PROOF_EVIDENCE"
    )
    assert revision_context["model_owned_complete_source_tool_loop_eligible"] is True
    assert revision_context["source_theorem_kernel_evidence_eligible"] is False
    serialized = json.dumps(feedback, sort_keys=True)
    for forbidden in (
        "repair_scope",
        "repair_owner",
        "repair_plan",
        "repair_instructions",
        "required_change",
        "suggested_fix",
    ):
        assert forbidden not in serialized
    assert result.next_task.inputs[
        "formal_target_semantic_review_revision_count"
    ] == 1


def test_rejection_after_local_budget_blocks_without_a_second_router(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accepted=False,
        revision_count=2,
        max_revisions=2,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "formal_target_semantic_review_revision_budget_exhausted"
    )


def test_invalid_observation_packet_fails_closed_without_owner_fallback(
    tmp_path: Path,
) -> None:
    response = _review_response(accepted=False)
    response["findings"][0].pop("expected_behavior")
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accepted=False,
        response=response,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.next_task is None
    failure = _artifact_of_kind(
        result, "RuntimeFormalTargetSemanticReviewValidationFailure"
    )
    assert failure["llm_packet_regeneration_history"]
    assert failure["last_invalid_packet"]["findings"][0][
        "observed_behavior"
    ] == "The conclusion proves only a weaker claim."
    assert "repair_owner" not in json.dumps(failure, sort_keys=True)


def test_source_hash_drift_is_rejected_before_model_review(tmp_path: Path) -> None:
    subsystem, task, blackboard, artifact_path = _runtime_fixture(
        tmp_path, accepted=True
    )
    artifact_path.write_text("import Mathlib\nexample : True := by trivial\n")

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "formal_target_semantic_review_input_invalid"
    )
    assert not result.tool_calls


def test_deferred_task_ref_drift_is_rejected_before_model_review(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path, accepted=True
    )
    work_order = blackboard.artifacts[task.inputs["work_order_id"]]
    assert "deferred_next_task" not in work_order
    assert work_order["deferred_next_task_ref"]["artifact_kind"] == (
        "AgentTaskRef"
    )
    assert "deferred_next_task" not in task.inputs
    assert "architect_context" not in task.inputs
    continuation_id = work_order["deferred_next_task_continuation_id"]
    blackboard.artifacts[continuation_id]["task_template"][
        "objective"
    ] = "tampered objective"

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "formal_target_semantic_review_input_invalid"
    )
    assert not result.tool_calls


def test_prompt_requests_observations_and_forbids_runtime_repair_planning() -> None:
    prompt = build_formal_target_semantic_review_prompt(
        question=_question(),
        review_material={"exact_formal_target": {"source": "theorem t : True"}},
    )

    assert "observed_behavior" in prompt
    assert "expected_behavior" in prompt
    assert "ArchitectCoordinator decides what acts next" in prompt
    assert "Do not write Lean" in prompt
    assert "missing proof" in prompt
    assert "not a semantic finding" in prompt
    assert "ACCEPT means eligible for proof construction, not proved" in prompt
    assert "comments, docstrings, theorem names, field names" in prompt
    assert "returning a stored proof of the conclusion" in prompt
    assert "unused-hypothesis warnings" in prompt
    assert "new hash, renaming, or expanded comment" in prompt
    assert "repair_scope" not in prompt
    assert "repair_owner" not in prompt


def test_revision_review_receives_prior_findings_and_formalizer_grounding(
    tmp_path: Path,
) -> None:
    prior_feedback = {
        "feedback_type": "formal_target_semantic_review_feedback",
        "feedback_id": "prior-feedback",
        "semantic_review_execution_id": "prior-execution",
        "semantic_review_packet_id": "prior-packet",
        "semantic_review_packet_hash": "prior-packet-hash",
        "candidate_source_hash": "prior-source-hash",
        "overall_verdict": "REVISE",
        "findings": [
            {
                "severity": "high",
                "category": "opaque_certificate",
                "summary": "The conclusion is stored in an opaque structure field.",
                "observed_behavior": "The proof returns the stored field.",
                "expected_behavior": "Derive the bound conclusion from assumptions.",
                "evidence_refs": ["/exact_formal_target"],
            }
        ],
    }
    workspace_evidence = {
        "artifact_id": "formalizer-workspace:revision",
        "workspace_phase": "revision",
        "parent_source_hash": "prior-source-hash",
        "independently_rejected_source_hash": "prior-source-hash",
        "submitted_source_hash": "current-source-hash",
        "source_updates": 1,
        "lean_declaration_inspections": 1,
        "formal_environment_searches": 0,
        "lean_state_inspections": 1,
        "history": [
            {
                "tool_calls": [
                    {
                        "name": "inspect_lean_declaration",
                        "observation_key": "lean-declaration:source",
                        "result_excerpt": "source-shaped certificate declaration",
                    },
                    {
                        "name": "inspect_lean_state",
                        "observation_key": "lean-state:unused",
                        "result_excerpt": "unused variable h_assumption",
                    },
                    {
                        "name": "submit_lean_source",
                        "observation_key": "lean-submit:ignored",
                        "result_excerpt": "full source omitted from review grounding",
                    },
                ]
            }
        ],
    }
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accepted=False,
        revision_count=1,
        prior_review_feedback=prior_feedback,
        workspace_evidence=workspace_evidence,
    )
    backend = _CapturingBackend([_review_response(accepted=False)])
    subsystem.reviewer = LLMFormalTargetSemanticReviewerAgent(
        provider=backend,
        config=FormalTargetSemanticReviewerConfig(
            provider_name="static",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )

    subsystem.run(task, blackboard)

    payload = json.loads(backend.requests[0].user_prompt.split("\n\n", 1)[1])
    material = payload["review_material"]
    assert material["prior_semantic_review_observation"]["findings"] == (
        prior_feedback["findings"]
    )
    grounding = material["formalizer_grounding_observations"]
    assert grounding["independently_rejected_source_hash"] == "prior-source-hash"
    assert [row["tool_name"] for row in grounding["tool_observations"]] == [
        "inspect_lean_declaration",
        "inspect_lean_state",
    ]
    assert "source-shaped certificate" in grounding["tool_observations"][0][
        "result_excerpt"
    ]


def test_dimension_schema_uses_required_provider_safe_slots() -> None:
    schema = FORMAL_TARGET_SEMANTIC_REVIEW_JSON_SCHEMA["properties"][
        "dimension_reviews"
    ]
    expected_slots = [
        f"slot_{index}"
        for index in range(len(FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS))
    ]
    assert schema["type"] == "object"
    assert schema["required"] == expected_slots
    assert set(schema["properties"]) == set(expected_slots)
    assert all(
        row == {"$ref": "#/$defs/dimension_review"}
        for row in schema["properties"].values()
    )
    assert "dimension" not in FORMAL_TARGET_SEMANTIC_REVIEW_JSON_SCHEMA["$defs"][
        "dimension_review"
    ]["properties"]


def test_required_slots_survive_anthropic_strict_transform() -> None:
    anthropic = pytest.importorskip("anthropic")
    transformed = anthropic.transform_schema(
        FORMAL_TARGET_SEMANTIC_REVIEW_JSON_SCHEMA
    )
    dimension_schema = transformed["properties"]["dimension_reviews"]

    assert dimension_schema["required"] == [
        f"slot_{index}"
        for index in range(len(FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS))
    ]


def test_prompt_binds_provider_slots_to_semantic_dimensions() -> None:
    prompt = build_formal_target_semantic_review_prompt(
        question=_question(),
        review_material={"exact_formal_target": {"source": "theorem t : True"}},
    )
    payload = json.loads(prompt.split("\n\n", 1)[1])

    assert payload["ordered_review_slots"]["dimension_reviews"] == [
        {"output_slot": f"slot_{index}", "dimension": dimension}
        for index, dimension in enumerate(
            FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS
        )
    ]


def test_slot_mapping_normalizes_without_model_copied_identity(
    tmp_path: Path,
) -> None:
    response = _review_response(accepted=True)
    response["dimension_reviews"] = {
        f"slot_{index}": row
        for index, row in enumerate(response["dimension_reviews"])
    }
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accepted=True,
        response=response,
    )

    result = subsystem.run(task, blackboard)

    packet = _artifact_of_kind(result, "FormalTargetSemanticReviewPacket")
    assert [row["dimension"] for row in packet["dimension_reviews"]] == list(
        FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS
    )


def test_reviewer_requests_native_schema_for_generation_and_regeneration() -> None:
    invalid = _review_response(accepted=True)
    invalid["findings"] = _review_response(accepted=False)["findings"]
    backend = _CapturingBackend([invalid, _review_response(accepted=True)])
    agent = LLMFormalTargetSemanticReviewerAgent(
        provider=backend,
        config=FormalTargetSemanticReviewerConfig(
            provider_name="static",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            max_validation_retries=1,
        ),
    )
    lineage = {
        "work_order_id": "work-order",
        "work_order_hash": "work-order-hash",
        "source_task_id": "source-task",
        "source_subsystem": "FormalizationEvaluator",
        "candidate_materialization_id": "materialization",
        "candidate_materialization_hash": "materialization-hash",
        "theory_packet_id": "theory-packet",
        "theory_packet_hash": "theory-packet-hash",
        "proposal_packet_id": "proposal-packet",
        "proposal_packet_hash": "proposal-packet-hash",
        "candidate_id": "candidate",
        "candidate_source_hash": "candidate-source-hash",
        "target_lean_declaration": "exact_source",
        "target_theorem_statement_hash": "target-statement-hash",
        "target_theorem_statement_hash_algorithm": "sha256",
        "source_model": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        "source_model_tier": "haiku",
        "source_agent": "LLMFormalizerProofEngineerAgent",
    }

    packet = agent.review(
        question=_question(),
        review_material={"exact_formal_target": {"source": "theorem t : True"}},
        trusted_lineage=lineage,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert len(backend.requests) == 2
    assert backend.requests[0].metadata[
        PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY
    ] is True
    assert backend.requests[0].metadata[
        PROVIDER_STRUCTURED_OUTPUT_ON_RETRY_METADATA_KEY
    ] is True
    assert backend.requests[1].metadata[
        PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY
    ] is True
    assert "all-PASS semantic reviews must leave findings empty" in (
        backend.requests[1].user_prompt
    )
    assert backend.requests[1].schema == backend.requests[0].schema
    assert backend.requests[1].metadata["structured_output_retry_mode"] == (
        "full_packet_regeneration"
    )

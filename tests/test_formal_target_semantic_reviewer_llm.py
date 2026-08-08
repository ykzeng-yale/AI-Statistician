from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.architect_coordinator_llm import (
    ARCHITECT_FEEDBACK_ROUTE_OPERATION,
)
from ai_statistician.exact_source_theorem_proof_body_executor import (
    EXACT_TARGET_STATEMENT_HASH_ALGORITHM,
    exact_target_statement_hash,
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
    PROVIDER_STRUCTURED_OUTPUT_ON_REPAIR_METADATA_KEY,
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
    target_hash_algorithm: str = EXACT_TARGET_STATEMENT_HASH_ALGORITHM,
    revision_count: int = 0,
    max_revisions: int = 2,
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
    target_hash = exact_target_statement_hash(target_statement)
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
        "proofengineer_repair_context": target_context,
    }
    deferred_task = AgentTask(
        task_id="formalize-lean-revision:generic-formal-target-review",
        owner_subsystem="ProofEngineer",
        objective="Continue model-owned proof search for the accepted target.",
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
        max_revisions=max_revisions,
    )
    assert dispatch is not None
    blackboard = BlackboardState(project_id="formal-target-semantic-review-test")
    blackboard.artifacts.update(
        {
            theory_packet["packet_id"]: theory_packet,
            proposal_packet["packet_id"]: proposal_packet,
            candidate_materialization["manifest_id"]: candidate_materialization,
            dispatch["work_order_id"]: dispatch["work_order"],
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


def test_accept_is_the_only_path_to_model_owned_lean_generation(tmp_path: Path) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accepted=True)

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ProofEngineer"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["external_proof_search_dispatch_eligible"] is False
    assert feedback["model_owned_complete_source_tool_loop_eligible"] is True
    assert feedback["proofengineer_repair_context"][
        "external_proof_search_dispatch_eligible"
    ] is False
    assert feedback["proofengineer_repair_context"][
        "model_owned_complete_source_tool_loop_eligible"
    ] is True
    packet = _artifact_of_kind(result, "FormalTargetSemanticReviewPacket")
    assert packet["model"] == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
    assert packet["model_tier"] == "haiku"
    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["kernel_verified"] is False
    assert validate_formal_target_semantic_review_packet(packet) == []


def test_rejection_routes_observations_to_architect_not_a_repair_owner(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accepted=False)

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    assert result.next_task.inputs["runtime_architect_operation"] == (
        ARCHITECT_FEEDBACK_ROUTE_OPERATION
    )
    assert result.next_task.expected_artifacts == (
        "architect_feedback_route_decision",
    )
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["external_proof_search_dispatch_eligible"] is False
    assert feedback["runtime_selected_owner"] is False
    assert feedback["routing_authority"] == "ArchitectCoordinator_model_packet"
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
    replan = result.next_task.inputs["architect_context"][
        "formal_target_semantic_review_replan"
    ]
    assert replan["runtime_selected_owner"] is False
    assert replan["revision_budget"] == {
        "revisions_used": 0,
        "max_revisions": 2,
        "revision_available": True,
    }


def test_rejection_after_local_budget_still_uses_architect_for_cross_lane_choice(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accepted=False,
        revision_count=2,
        max_revisions=2,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    budget = result.next_task.inputs["architect_context"][
        "formal_target_semantic_review_replan"
    ]["revision_budget"]
    assert budget["revision_available"] is False


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


def test_prompt_requests_observations_and_forbids_runtime_repair_planning() -> None:
    prompt = build_formal_target_semantic_review_prompt(
        question=_question(),
        review_material={"exact_formal_target": {"source": "theorem t : True"}},
    )

    assert "observed_behavior" in prompt
    assert "expected_behavior" in prompt
    assert "ArchitectCoordinator decides what acts next" in prompt
    assert "Do not write Lean" in prompt
    assert "repair_scope" not in prompt
    assert "repair_owner" not in prompt


def test_dimension_schema_is_order_bound_without_model_copied_identity() -> None:
    schema = FORMAL_TARGET_SEMANTIC_REVIEW_JSON_SCHEMA["properties"][
        "dimension_reviews"
    ]
    assert schema["minItems"] == len(FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS)
    assert schema["maxItems"] == len(FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS)
    assert "dimension" not in schema["items"]["properties"]


def test_reviewer_requests_native_schema_for_generation_and_regeneration() -> None:
    invalid = _review_response(accepted=False)
    invalid["findings"][0].pop("expected_behavior")
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
        PROVIDER_STRUCTURED_OUTPUT_ON_REPAIR_METADATA_KEY
    ] is True
    assert backend.requests[1].metadata[
        PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY
    ] is True
    assert backend.requests[1].schema == backend.requests[0].schema
    assert backend.requests[1].metadata["json_repair_mode"] == (
        "full_packet_regeneration"
    )

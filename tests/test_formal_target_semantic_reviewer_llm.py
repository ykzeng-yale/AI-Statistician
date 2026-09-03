from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from ai_statistician import lean_kernel_promotion as lean_kernel_promotion_module
from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.lean_candidate_identity import (
    LEAN_TARGET_STATEMENT_HASH_ALGORITHM,
    lean_target_statement_hash,
)
from ai_statistician.lean_kernel_promotion import evaluate_lean_kernel_promotion
from ai_statistician.lean_project import model_authored_lean_project
from ai_statistician.fingerprint import stable_hash
from ai_statistician.formal_target_semantic_review_runtime import (
    FormalTargetSemanticReviewerRuntimeSubsystem,
    _runtime_formal_target_semantic_review_dispatch,
)
from ai_statistician.formal_target_semantic_reviewer_llm import (
    FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS,
    FORMAL_TARGET_SEMANTIC_REVIEW_JSON_SCHEMA,
    FORMAL_TARGET_SEMANTIC_REVIEW_SUBMIT_TOOL,
    FormalTargetSemanticReviewerConfig,
    LLMFormalTargetSemanticReviewerAgent,
    build_formal_target_semantic_review_prompt,
    validate_formal_target_semantic_review_packet,
)
from ai_statistician.formalizer_llm import (
    FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
)
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    theory_workspace_document_manifest,
)


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
        provider=_ClientToolReviewBackend(
            [response if response is not None else _review_response(accepted=accepted)]
        ),
        config=FormalTargetSemanticReviewerConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
        ),
    )


class _ClientToolReviewBackend:
    provider_name = "anthropic"

    def __init__(
        self,
        actions: list[
            dict[str, Any] | tuple[str, Mapping[str, Any]] | str
        ],
    ) -> None:
        self.actions = list(actions)
        self.requests: list[ClientToolTurnRequest] = []

    def generate_client_tool_turn(
        self,
        request: ClientToolTurnRequest,
    ) -> ClientToolTurnResponse:
        self.requests.append(request)
        if not self.actions:
            return ClientToolTurnResponse(
                content_blocks=(),
                tool_calls=(),
                text="The retained reviewer cannot produce a valid submission.",
                provider=self.provider_name,
                model=request.model,
                metadata={
                    "client_tool_transport": True,
                    "tools_executed_by_backend": False,
                    "provider_stop_reason": "end_turn",
                },
            )
        action = self.actions.pop(0)
        if action == "read_first_externalized_document":
            prompt = str(request.messages[0]["content"])
            payload = json.loads(prompt.rsplit("\n\n", 1)[1])
            document = payload["exact_evidence_document_catalog"][0]
            tool_name = THEORY_WORKSPACE_READ_DOCUMENT_TOOL
            tool_input = {
                "path": document["path"],
                "line_start": 1,
                "line_end": min(20, int(document["line_count"])),
            }
        elif isinstance(action, tuple):
            tool_name, tool_input = action
        else:
            tool_name, tool_input = (
                FORMAL_TARGET_SEMANTIC_REVIEW_SUBMIT_TOOL,
                action,
            )
        call = ClientToolCall(
            call_id=f"formal-review-call-{len(self.requests)}",
            name=tool_name,
            input=dict(tool_input),
        )
        return ClientToolTurnResponse(
            content_blocks=(
                {
                    "type": "tool_use",
                    "id": call.call_id,
                    "name": call.name,
                    "input": dict(call.input),
                },
            ),
            tool_calls=(call,),
            text="",
            provider=self.provider_name,
            model=request.model,
            metadata={
                "client_tool_transport": True,
                "tools_executed_by_backend": False,
                "provider_stop_reason": "tool_use",
            },
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
    formal_only: bool = False,
    omit_theory_packet: bool = False,
    lean_project: Mapping[str, Any] | None = None,
    theory_documents: Mapping[str, str] | None = None,
) -> tuple[
    FormalTargetSemanticReviewerRuntimeSubsystem,
    AgentTask,
    BlackboardState,
    Path,
]:
    source = (
        "import Mathlib\n\n"
        "theorem exact_source (p : Prop) (hp : p) : p := by\n"
        "  exact hp\n"
    )
    question = _question()
    if formal_only:
        source_prefix = source.removesuffix("  exact hp\n")
        question = OpenResearchQuestion(
            id=question.id,
            title=question.title,
            description=question.description,
            tags=question.tags,
            task_intent={
                "source_replication": "not_applicable",
                "theory": "not_applicable",
                "scientific_code": "not_applicable",
                "empirical": "not_applicable",
                "formal": "required",
                "novelty": "not_applicable",
                "unresolved_gaps": "required",
            },
            formal_target_contract={
                "schema_version": 1,
                "contract_kind": "operator_frozen_exact_lean_target",
                "target_id": "exact_source",
                "declaration_name": "exact_source",
                "lean_source_prefix": source_prefix,
                "lean_source_prefix_sha256": hashlib.sha256(
                    source_prefix.encode("utf-8")
                ).hexdigest(),
                "proof_visibility": "hidden",
                "lean_environment": {
                    "project_id": "formal-target-review-test",
                    "lean_toolchain": "leanprover/lean4:test",
                    "lake_manifest_sha256": "a" * 64,
                },
                "required_primitives": ["exact"],
            },
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
    if theory_documents:
        for relative_path, content in theory_documents.items():
            target = tmp_path / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        theory_packet["theory_workspace_manifest"] = (
            theory_workspace_document_manifest(
                theory_documents,
                workspace_dir=tmp_path,
            )
        )
    if formal_only or omit_theory_packet:
        theory_packet = {}
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
                **({"lean_project": dict(lean_project)} if lean_project else {}),
            }
        ],
    }
    candidate_materialization = {
        "schema_version": 1,
        "artifact_kind": "RuntimeFormalizerLeanCandidateMaterialization",
        "manifest_id": "formalizer_lean_candidate_materialization:generic",
        "question": {"id": question.id},
        "candidate_rows": [
            {
                "candidate_id": "exact_source",
                "source_field": "formal_targets",
                "formal_target_role": FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
                "artifact_path": str(artifact_path),
                "source_hash": source_hash,
                **(
                    {
                        "lean_project": dict(lean_project),
                        "lean_project_hash": str(
                            lean_project.get("project_hash", "") or ""
                        ),
                    }
                    if lean_project
                    else {}
                ),
                "target_lean_declaration": "exact_source",
                "candidate_lean_declaration": "exact_source",
                "target_ids": ["exact_source"],
                "source_theorem_candidate_evidence_eligible": True,
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
        "task_intent": dict(question.task_intent),
        "formal_target_contract": dict(question.formal_target_contract),
    }
    source_task = AgentTask(
        task_id="formalize:generic-formal-target-review",
        owner_subsystem="FormalizationEvaluator",
        objective="Generate an exact formal target.",
        inputs={
            "question": question_payload,
            "theory_packet_id": str(theory_packet.get("packet_id", "")),
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
            **(
                {str(theory_packet["packet_id"]): theory_packet}
                if theory_packet
                else {}
            ),
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
            **(
                {str(theory_packet["packet_id"]): theory_packet}
                if theory_packet
                else {}
            ),
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


def test_semantic_review_binds_exact_model_authored_lean_project(
    tmp_path: Path,
) -> None:
    source = (
        "import Mathlib\n\n"
        "theorem exact_source (p : Prop) (hp : p) : p := by\n"
        "  exact hp\n"
    )
    project = model_authored_lean_project(
        target_source=source,
        project_files=[
            {
                "path": "AIStat/Support.lean",
                "content": "namespace AIStat\ntheorem helper : True := by trivial\nend AIStat\n",
            }
        ],
        support_build_order=("AIStat/Support.lean",),
    )
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accepted=True,
        lean_project=project,
    )
    backend = _ClientToolReviewBackend([_review_response(accepted=True)])
    subsystem.reviewer = LLMFormalTargetSemanticReviewerAgent(
        provider=backend,
        config=FormalTargetSemanticReviewerConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
        ),
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    initial_prompt = str(backend.requests[0].messages[0]["content"])
    payload = json.loads(initial_prompt.rsplit("\n\n", 1)[1])
    exact = payload["review_material"]["exact_formal_target"]
    assert exact["exact_lean_project"] == project
    assert exact["exact_lean_project_hash"] == project["project_hash"]
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["candidate_lean_project_hash"] == project["project_hash"]


def test_operator_frozen_formal_only_target_uses_question_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path, accepted=True, formal_only=True
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    packet = _artifact_of_kind(result, "FormalTargetSemanticReviewPacket")
    assert packet["semantic_authority_mode"] == (
        "operator_frozen_formal_target_contract"
    )
    assert packet["theory_packet_id"] == ""
    assert validate_formal_target_semantic_review_packet(packet) == []
    blackboard.artifacts.update(result.produced_artifacts)
    monkeypatch.setattr(
        lean_kernel_promotion_module,
        "run_lean_candidate_identity_probe",
        lambda **_kwargs: {
            "local_lean_attempted": True,
            "local_lean_compiled": True,
            "local_lean_source_compiled": True,
            "candidate_identity_lean_verified": True,
            "candidate_axiom_audit_clean": True,
        },
    )
    promotion = evaluate_lean_kernel_promotion(
        blackboard_artifacts=blackboard.artifacts,
        environment_feedback=result.next_task.inputs["environment_feedback"],
        lean_project=tmp_path,
        lean_timeout=30,
    )
    assert promotion is not None
    assert promotion["source_theorem_kernel_verified"] is True


def test_missing_theory_without_frozen_formal_authority_fails_closed(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path, accepted=True, omit_theory_packet=True
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == "formal_target_semantic_review_input_invalid"
    assert not result.tool_calls


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
    assert failure["retained_reviewer_history"]
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
    assert "Runtime handles the next typed task outside" in prompt
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
        "lean_scratch_checks": 1,
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
                        "name": "run_lean_scratch",
                        "observation_key": "lean-scratch:api-shape",
                        "result_excerpt": "#check exact reused declaration",
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
    backend = _ClientToolReviewBackend([_review_response(accepted=False)])
    subsystem.reviewer = LLMFormalTargetSemanticReviewerAgent(
        provider=backend,
        config=FormalTargetSemanticReviewerConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
        ),
    )

    subsystem.run(task, blackboard)

    initial_prompt = str(backend.requests[0].messages[0]["content"])
    payload = json.loads(initial_prompt.rsplit("\n\n", 1)[1])
    material = payload["review_material"]
    assert material["prior_semantic_review_observation"]["findings"] == (
        prior_feedback["findings"]
    )
    grounding = material["formalizer_grounding_observations"]
    assert grounding["independently_rejected_source_hash"] == "prior-source-hash"
    assert [row["tool_name"] for row in grounding["tool_observations"]] == [
        "inspect_lean_declaration",
        "inspect_lean_state",
        "run_lean_scratch",
    ]
    assert grounding["lean_scratch_checks"] == 1
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


def test_formal_target_review_reports_every_material_finding_without_cap() -> None:
    response = _review_response(accepted=False)
    response["findings"] = [
        {
            **response["findings"][0],
            "summary": f"Material semantic defect {index}",
            "observed_behavior": f"Observed defect {index}",
        }
        for index in range(12)
    ]
    backend = _ClientToolReviewBackend([response])
    agent = LLMFormalTargetSemanticReviewerAgent(
        provider=backend,
        config=FormalTargetSemanticReviewerConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
        ),
    )
    packet = agent.review(
        question=_question(),
        review_material={"exact_formal_target": {"source": "theorem t : True"}},
        trusted_lineage={
            "work_order_id": "work-order",
            "work_order_hash": "work-order-hash",
            "source_task_id": "source-task",
            "source_subsystem": "FormalizationEvaluator",
            "candidate_materialization_id": "materialization",
            "candidate_materialization_hash": "materialization-hash",
            "semantic_authority_mode": "theory_derivation_packet",
            "semantic_authority_hash": "theory-packet-hash",
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
        },
    )

    assert "maxItems" not in FORMAL_TARGET_SEMANTIC_REVIEW_JSON_SCHEMA[
        "properties"
    ]["findings"]
    assert len(packet["findings"]) == 12
    assert validate_formal_target_semantic_review_packet(packet) == []


def test_long_exact_evidence_is_read_inside_retained_reviewer_session() -> None:
    long_source = "\n".join(
        ["theorem exact_source : True := by trivial"]
        + [f"-- exact semantic line {index}: " + ("x" * 80) for index in range(30)]
    )
    backend = _ClientToolReviewBackend(
        ["read_first_externalized_document", _review_response(accepted=True)]
    )
    agent = LLMFormalTargetSemanticReviewerAgent(
        provider=backend,
        config=FormalTargetSemanticReviewerConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
        ),
    )
    packet = agent.review(
        question=_question(),
        review_material={
            "exact_formal_target": {"exact_lean_source": long_source}
        },
        trusted_lineage={
            "work_order_id": "work-order",
            "work_order_hash": "work-order-hash",
            "source_task_id": "source-task",
            "source_subsystem": "FormalizationEvaluator",
            "candidate_materialization_id": "materialization",
            "candidate_materialization_hash": "materialization-hash",
            "semantic_authority_mode": "theory_derivation_packet",
            "semantic_authority_hash": "theory-packet-hash",
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
        },
    )

    transport = packet["client_tool_loop"]
    assert transport["evidence_document_count"] == 1
    assert transport["document_access_count"] == 1
    assert transport["turns"] == 2
    second_request = backend.requests[1]
    assert "exact semantic line 0" in json.dumps(second_request.messages[-1])


def test_runtime_supplies_hash_bound_theory_markdown_to_retained_reviewer(
    tmp_path: Path,
) -> None:
    theory_content = "\n".join(
        ["# Exact claim", "", "The target must preserve every assumption."]
        + [f"Derivation line {index}: " + ("z" * 80) for index in range(30)]
    )
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accepted=True,
        theory_documents={"derivations/exact-claim.md": theory_content},
    )
    backend = _ClientToolReviewBackend(
        ["read_first_externalized_document", _review_response(accepted=True)]
    )
    subsystem.reviewer = LLMFormalTargetSemanticReviewerAgent(
        provider=backend,
        config=FormalTargetSemanticReviewerConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
        ),
    )

    result = subsystem.run(task, blackboard)

    review = _artifact_of_kind(result, "FormalTargetSemanticReviewPacket")
    prompt = str(backend.requests[0].messages[0]["content"])
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    catalog = payload["exact_evidence_document_catalog"]
    assert any(
        row["json_path"]
        == "$/authoritative_theory_documents/0/content"
        for row in catalog
    )
    assert review["client_tool_loop"]["document_access_count"] == 1
    assert theory_content.splitlines()[0] in json.dumps(
        backend.requests[1].messages[-1]
    )


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


def test_invalid_submission_returns_to_same_retained_reviewer_session() -> None:
    invalid = _review_response(accepted=True)
    invalid["findings"] = _review_response(accepted=False)["findings"]
    backend = _ClientToolReviewBackend(
        [invalid, _review_response(accepted=True)]
    )
    agent = LLMFormalTargetSemanticReviewerAgent(
        provider=backend,
        config=FormalTargetSemanticReviewerConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
        ),
    )
    lineage = {
        "work_order_id": "work-order",
        "work_order_hash": "work-order-hash",
        "source_task_id": "source-task",
        "source_subsystem": "FormalizationEvaluator",
        "candidate_materialization_id": "materialization",
        "candidate_materialization_hash": "materialization-hash",
        "semantic_authority_mode": "theory_derivation_packet",
        "semantic_authority_hash": "theory-packet-hash",
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
    assert backend.requests[0].tools == backend.requests[1].tools
    assert backend.requests[0].metadata["full_packet_regeneration_disabled"] is True
    assert len(backend.requests[1].messages) == 3
    returned_observation = json.dumps(
        backend.requests[1].messages[-1],
        sort_keys=True,
    )
    assert "client_tool_input_rejected" in returned_observation
    assert "all-PASS semantic reviews must leave findings empty" in returned_observation
    assert packet["client_tool_loop"]["turns"] == 2
    assert packet["client_tool_loop"]["full_packet_regeneration_used"] is False

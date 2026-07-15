from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.architect_coordinator_llm import (
    _required_architect_plan_subsystems,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.exact_source_theorem_proof_body_executor import (
    EXACT_TARGET_STATEMENT_HASH_ALGORITHM,
    exact_target_statement_hash,
)
from ai_statistician.formal_target_semantic_reviewer_llm import (
    FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS,
    FormalTargetSemanticReviewerConfig,
    LLMFormalTargetSemanticReviewerAgent,
    build_formal_target_semantic_review_prompt,
    validate_formal_target_semantic_review_packet,
)
from ai_statistician.formalizer_llm import build_formalizer_prompt
from ai_statistician.model_backend import StaticJSONGeneratorBackend
from ai_statistician.research_agent_runtime import (
    FormalTargetSemanticReviewerRuntimeSubsystem,
    _formalizer_compiled_exact_candidate_semantic_review_feedback,
    _runtime_external_proof_search_request,
    _runtime_formal_target_semantic_review_dispatch,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.research_agent_runtime_audit import (
    _audit_result_path,
    _runtime_capability_scorecard,
)


def _question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="generic-formal-target-review",
        title="Review an exact formal theorem target",
        description=(
            "Determine whether a generated exact theorem preserves the supplied "
            "mathematical claim and assumptions."
        ),
        tags=("formalization", "semantic-review"),
    )


def _review_response(verdict: str) -> dict[str, object]:
    rows = [
        {
            "dimension": dimension,
            "status": "PASS",
            "rationale": f"The exact target preserves {dimension}.",
            "evidence_refs": [f"exact_formal_target.{dimension}"],
        }
        for dimension in FORMAL_TARGET_SEMANTIC_REVIEW_DIMENSIONS
    ]
    findings: list[dict[str, object]] = []
    instructions: list[str] = []
    repair_owner = "FormalizationEvaluator"
    blocking_reason = ""
    if verdict != "ACCEPT":
        rows[3]["status"] = "FAIL" if verdict == "REVISE" else "UNCERTAIN"
        rows[3]["rationale"] = (
            "The current target is not supported by the supplied derivation."
        )
        findings = [
            {
                "severity": "high",
                "category": "mathematical_target_drift",
                "summary": "The target does not establish the requested claim.",
                "required_change": "Regenerate a faithful exact theorem statement.",
                "evidence_refs": ["theory_derivation_packet", "exact_formal_target"],
            }
        ]
        instructions = ["Preserve the exact assumptions, quantifiers, and conclusion."]
    if verdict == "BLOCK":
        repair_owner = "TheoryDeveloper"
        blocking_reason = "The current derivation does not support a coherent target."
    return {
        "dimension_reviews": rows,
        "findings": findings,
        "overall_verdict": verdict,
        "repair_owner": repair_owner,
        "repair_instructions": instructions,
        "blocking_reason": blocking_reason,
    }


def _reviewer(verdict: str) -> LLMFormalTargetSemanticReviewerAgent:
    return LLMFormalTargetSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(_review_response(verdict)),
        config=FormalTargetSemanticReviewerConfig(
            provider_name="static",
            model="static-opus-formal-target-reviewer",
            model_tier="opus",
            max_repair_attempts=0,
        ),
    )


def _runtime_fixture(
    tmp_path: Path,
    verdict: str,
    *,
    target_hash_algorithm: str = EXACT_TARGET_STATEMENT_HASH_ALGORITHM,
):
    question = _question()
    source = (
        "import Mathlib\n\n"
        "theorem exact_source\n"
        "    (p : Prop)\n"
        "    (hp : p) :\n"
        "    p := by\n"
        "  exact hp\n"
    )
    target_statement = (
        "theorem exact_source\n"
        "    (p : Prop)\n"
        "    (hp : p) :\n"
        "    p"
    )
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
    }
    proposal_packet = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer:generic-formal-target-review",
        "source_agent": "LLMFormalizerProofEngineerAgent",
        "model": "source-sonnet-model",
        "model_tier": "sonnet",
        "formal_targets": [
            {
                "id": "exact_source",
                "lean_statement_sketch": source,
                "semantic_alignment_constraints": [
                    "preserve the supplied hypothesis and conclusion"
                ],
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
                "artifact_path": str(artifact_path),
                "source_hash": source_hash,
                "target_lean_declaration": "exact_source",
                "target_ids": ["exact_source"],
                "local_lean_attempted": True,
                "local_lean_compiled": False,
                "local_lean_exit_status": "1",
                "local_lean_stderr": "unsolved goals",
                "source_theorem_candidate_evidence_eligible": True,
                "diagnostic_helper_not_source_theorem": False,
                "support_candidate_not_source_theorem": False,
                "source_theorem_target_known": True,
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "source_theorem_question_id": question.id,
                    "source_theorem_goal_id": "exact_source",
                    "target_lean_declaration": "exact_source",
                },
            }
        ],
    }
    question_payload = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }
    repair_task = AgentTask(
        task_id="formalize:generic-formal-target-review",
        owner_subsystem="FormalizationEvaluator",
        objective="Generate an exact formal target.",
        inputs={
            "question": question_payload,
            "theory_packet_id": theory_packet["packet_id"],
            "architect_context": {
                "runtime_requested_evidence_contract": {
                    "evaluation_mode": "capability_eval"
                }
            },
        },
    )
    repair_context = {
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
        "target_theorem_statement_hash_algorithm": (
            target_hash_algorithm
        ),
        "target_ids": ["exact_source"],
        "source_theorem_target_provenance": {
            "source_theorem_target_known": True
        },
        "semantic_alignment_constraints": [
            "preserve the supplied hypothesis and conclusion"
        ],
        "semantic_alignment_blockers": [],
        "source_theorem_kernel_evidence_eligible": False,
    }
    repair_feedback = {
        "feedback_type": "formalizer_lean_candidate_local_lean_feedback",
        "proofengineer_repair_context": repair_context,
    }
    deferred_task = AgentTask(
        task_id="formalize-lean-repair:generic-formal-target-review",
        owner_subsystem="ProofEngineer",
        objective="Search the accepted exact target.",
        inputs={
            **repair_task.inputs,
            "environment_feedback": repair_feedback,
        },
    )
    dispatch = _runtime_formal_target_semantic_review_dispatch(
        task=repair_task,
        question=question,
        source_subsystem="FormalizationEvaluator",
        candidate_materialization=candidate_materialization,
        theory_packet=theory_packet,
        proposal_packet=proposal_packet,
        repair_feedback=repair_feedback,
        architect_context=repair_task.inputs["architect_context"],
        deferred_next_task=deferred_task,
        max_revisions=2,
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
        reviewer=_reviewer(verdict),
        max_revisions=2,
    )
    return subsystem, dispatch["next_task"], blackboard, artifact_path


def test_formal_target_semantic_review_accepts_before_typed_prover_search(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, "ACCEPT")

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ProofEngineer"
    feedback = result.next_task.inputs["environment_feedback"]
    context = feedback["proofengineer_repair_context"]
    assert context["external_proof_search_dispatch_eligible"] is True
    assert context["source_theorem_kernel_evidence_eligible"] is True
    assert context["formalizer_candidate_semantic_review_status"] == (
        "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
    )
    question = _question()
    request = _runtime_external_proof_search_request(
        task=result.next_task,
        question=question,
        environment_feedback=feedback,
    )
    assert request["target_lean_declaration"] == "exact_source"
    review_lineage = request["formal_target_semantic_review"]
    assert review_lineage["status"] == (
        "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
    )
    assert review_lineage["candidate_source_hash"] == (
        context["lineage_candidate_artifact_hash"]
    )
    assert review_lineage["target_theorem_statement_hash"] == (
        context["target_theorem_statement_hash"]
    )
    assert all(row.payload["kernel_verified"] is False for row in result.evidence_entries)


def test_formal_target_semantic_review_rejects_target_and_disables_prover(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, "REVISE")

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "FormalizationEvaluator"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["overall_verdict"] == "REVISE"
    assert feedback["proofengineer_repair_context"][
        "external_proof_search_dispatch_eligible"
    ] is False
    assert feedback["repair_instructions"]
    handoff = result.next_task.inputs["architect_context"]["runtime_feedback_loop"][
        "direct_repair_handoff_contract"
    ]
    assert handoff["architect_pre_authorized"] is True
    assert handoff["source_reviewer_subsystem"] == (
        "FormalTargetSemanticReviewer"
    )
    assert handoff["target_repair_subsystem"] == "FormalizationEvaluator"
    assert handoff["feedback_artifact_id"] == feedback[
        "semantic_review_packet_id"
    ]
    assert handoff["target_task_id"] == result.next_task.task_id


def test_formal_target_semantic_review_blocks_back_to_theory_developer(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, "BLOCK")

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "TheoryDeveloper"
    assert result.next_task.inputs["environment_feedback"]["blocking_reason"]
    handoff = result.next_task.inputs["architect_context"]["runtime_feedback_loop"][
        "direct_repair_handoff_contract"
    ]
    assert handoff["target_repair_subsystem"] == "TheoryDeveloper"


def test_formal_target_semantic_review_fails_closed_on_source_hash_drift(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, artifact_path = _runtime_fixture(
        tmp_path, "ACCEPT"
    )
    artifact_path.write_text("theorem changed : True := by trivial\n", encoding="utf-8")

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == "formal_target_semantic_review_input_invalid"
    assert not result.tool_calls


def test_required_review_dispatch_fails_closed_on_target_hash_contract_drift(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        "ACCEPT",
        target_hash_algorithm="legacy_raw_statement_hash",
    )
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]

    assert work_order["dispatch_status"] == "BLOCKED"
    assert work_order["dispatch_validation_errors"] == [
        "target_theorem_statement_hash_algorithm mismatch"
    ]

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "formal_target_semantic_review_input_invalid"
    )
    assert not result.tool_calls


def test_accepted_formal_target_review_cannot_be_replayed_after_source_drift(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, artifact_path = _runtime_fixture(
        tmp_path, "ACCEPT"
    )
    result = subsystem.run(task, blackboard)
    assert result.next_task is not None
    feedback = result.next_task.inputs["environment_feedback"]
    artifact_path.write_text(
        "theorem exact_source : True := by trivial\n",
        encoding="utf-8",
    )

    request = _runtime_external_proof_search_request(
        task=result.next_task,
        question=_question(),
        environment_feedback=feedback,
    )

    assert request == {}


def test_formal_target_semantic_review_prompt_is_domain_general() -> None:
    prompt = build_formal_target_semantic_review_prompt(
        question=_question(),
        review_material={"exact_formal_target": {"target_theorem_statement": "p -> p"}},
    )

    assert "Do not invent task-family rules" in prompt
    assert "do not propose tactics" in prompt
    assert "This review is never proof evidence" in prompt


def test_formalizer_prompt_preserves_independent_target_review_reasoning() -> None:
    rationale = (
        "The emitted theorem makes the desired conclusion an input hypothesis, so "
        "its proof is circular even though the declaration is syntactically valid."
    )
    required_change = (
        "Remove the conclusion-shaped hypothesis and derive the conclusion from the "
        "registered assumptions and the exact equation-chain anchors."
    )
    question = _question()
    prompt = build_formalizer_prompt(
        question=question,
        theory_packet={
            "packet_id": "theory:semantic-feedback",
            "theorem_cards": [
                {
                    "id": "target-theorem",
                    "claim": "the registered assumptions imply the stated limit law",
                    "assumptions": ["registered source assumption"],
                }
            ],
            "theory_derivation_packet": {
                "derivation_steps": [
                    {
                        "id": "source-step",
                        "claim": "derive the target from the source assumption",
                    }
                ],
                "assumption_ledger": [
                    {
                        "assumption": "registered source assumption",
                        "role": "source premise",
                    }
                ],
                "formalization_handoff": {
                    "source_theorem_target": "target-theorem",
                    "candidate_lean_targets": ["theorem target_theorem ..."],
                },
            },
        },
        simulation_manifest={"manifest_id": "simulation:test"},
        algorithm_manifest={"manifest_id": "algorithm:test"},
        registered_problem={"question_id": question.id},
        theorem_goals=[
            {
                "id": "target-theorem",
                "claim": "registered assumptions imply the stated limit law",
            }
        ],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary={},
        environment_feedback={
            "feedback_type": "formal_target_semantic_review_feedback",
            "feedback_source": "FormalTargetSemanticReviewer",
            "semantic_review_execution_id": "formal-review-execution:test",
            "semantic_review_packet_id": "formal-review-packet:test",
            "candidate_materialization_id": "candidate-materialization:test",
            "candidate_id": "target-theorem",
            "candidate_source_hash": "source-hash",
            "overall_verdict": "REVISE",
            "repair_owner_agent": "FormalizationEvaluator",
            "dimension_reviews": [
                {
                    "dimension": "non_vacuity_and_assumption_discipline",
                    "status": "FAIL",
                    "rationale": rationale,
                    "evidence_refs": ["exact_formal_target"],
                }
            ],
            "findings": [
                {
                    "severity": "high",
                    "category": "circular_target",
                    "summary": "The conclusion is assumed.",
                    "required_change": required_change,
                    "evidence_refs": ["exact_formal_target", "theory_packet"],
                }
            ],
            "repair_instructions": [required_change],
            "blocking_reason": "Current target is vacuous.",
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
    )

    assert "formal_target_semantic_review" in prompt
    assert rationale in prompt
    assert required_change in prompt
    assert "treat its independent dimension reviews" in prompt
    assert "binding retry feedback" in prompt
    assert "task_bound_formal_target_contract" in prompt


def test_formal_target_review_validator_rejects_failed_dimension_acceptance() -> None:
    packet = {
        **_review_response("REVISE"),
        "overall_verdict": "ACCEPT",
        "proof_evidence_status": "FORMAL_TARGET_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE",
        "kernel_verified": False,
        "source_subsystem": "FormalizationEvaluator",
        "work_order_id": "work-order",
        "work_order_hash": "work-order-hash",
        "candidate_materialization_id": "materialization",
        "candidate_materialization_hash": "materialization-hash",
        "theory_packet_id": "theory",
        "theory_packet_hash": "theory-hash",
        "proposal_packet_id": "proposal",
        "proposal_packet_hash": "proposal-hash",
        "candidate_id": "candidate",
        "candidate_source_hash": "source-hash",
        "target_theorem_statement_hash": "target-hash",
        "target_theorem_statement_hash_algorithm": (
            EXACT_TARGET_STATEMENT_HASH_ALGORITHM
        ),
        "review_input_fingerprint": "input-hash",
    }

    errors = validate_formal_target_semantic_review_packet(packet)

    assert "overall_verdict cannot be ACCEPT while semantic blockers remain" in errors


def test_already_compiling_exact_target_still_requires_semantic_review(
    tmp_path: Path,
) -> None:
    _, _, blackboard, _ = _runtime_fixture(tmp_path, "ACCEPT")
    materialization = next(
        row
        for row in blackboard.artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeFormalizerLeanCandidateMaterialization"
    )
    candidate_row = materialization["candidate_rows"][0]
    candidate_row["local_lean_compiled"] = True
    candidate_row["local_lean_exit_status"] = "0"

    feedback = _formalizer_compiled_exact_candidate_semantic_review_feedback(
        materialization
    )

    assert feedback is not None
    context = feedback["proofengineer_repair_context"]
    assert context["formalizer_candidate_exact_search_eligible"] is True
    assert context["external_proof_search_dispatch_eligible"] is False
    assert context["external_proof_search_dispatch_blockers"]
    assert context["source_theorem_kernel_evidence_eligible"] is False


def test_capability_architect_plan_requires_formal_target_reviewer() -> None:
    required = _required_architect_plan_subsystems(
        {
            "evaluation_mode": "capability_eval",
            "capability_eval_requires_formalizer_lean_candidate": True,
            "capability_eval_requires_formal_target_semantic_review": True,
            "formal_verification_policy": "required",
        }
    )

    assert "FormalizationEvaluator" in required
    assert "FormalTargetSemanticReviewer" in required
    assert "ProofEngineer" in required


def test_capability_scorecard_requires_independent_formal_target_review() -> None:
    scorecard = _runtime_capability_scorecard(
        {
            "n_formal_target_semantic_review_work_orders": 1,
            "n_formal_target_semantic_review_executions": 1,
            "n_formal_target_semantic_review_accepted": 1,
            "n_formal_target_semantic_review_independent_opus": 1,
        }
    )
    rows = {row["requirement_id"]: row for row in scorecard["rows"]}

    assert rows["formal_target_semantic_review_executed"]["passed"] is True
    assert rows["formal_target_semantic_review_accepted"]["passed"] is True
    assert rows["formal_target_semantic_review_independent_opus"]["passed"] is True


def test_runtime_audit_recomputes_formal_target_review_lineage(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, "ACCEPT")
    result = subsystem.run(task, blackboard)
    result_path = tmp_path / "formal-target-review-runtime-result.json"
    result_path.write_text(
        json.dumps(
            {
                "status": "BLOCKED",
                "blackboard": {
                    "artifacts": {
                        **blackboard.artifacts,
                        **result.produced_artifacts,
                    }
                },
                "traces": [],
            }
        ),
        encoding="utf-8",
    )

    audit_row = _audit_result_path(result_path)

    assert audit_row.n_formal_target_semantic_review_work_orders == 1
    assert audit_row.n_formal_target_semantic_review_executions == 1
    assert audit_row.n_formal_target_semantic_review_accepted == 1
    assert audit_row.n_formal_target_semantic_review_independent_opus == 1
    assert not [
        error
        for error in audit_row.errors
        if "formal-target review" in error
    ]

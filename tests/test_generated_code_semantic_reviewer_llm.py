from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.algorithm_engineer_llm import build_algorithm_engineer_prompt
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_reviewer_llm import (
    GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS,
    GeneratedCodeSemanticReviewerConfig,
    LLMGeneratedCodeSemanticReviewerAgent,
    build_generated_code_semantic_review_prompt,
    generated_code_semantic_review_pending_plan_errors,
    generated_code_semantic_review_repair_scope,
    generated_code_semantic_review_repair_scopes,
    validate_generated_code_semantic_review_packet,
)
from ai_statistician.generated_code_semantic_review_replan import (
    GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY,
    GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_LEDGER_KEY,
    advance_generated_code_semantic_review_lineage_budget,
    consume_generated_code_semantic_review_upstream_theory_replan,
    generated_code_semantic_review_upstream_theory_budget_exhausted_result,
    generated_code_semantic_review_upstream_theory_revision_state,
    record_generated_code_semantic_review_lineage_action,
)
from ai_statistician.model_backend import (
    GeneratorRequest,
    GeneratorResponse,
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    StaticJSONGeneratorBackend,
)
from ai_statistician.research_agent_runtime import (
    ArchitectCoordinatorRuntimeSubsystem,
    GeneratedCodeSemanticReviewerRuntimeSubsystem,
    ResearchAgentRuntimeConfig,
    _runtime_algorithm_handoff_receipt,
    _runtime_generated_code_semantic_review_dispatch,
    _runtime_validated_algorithm_handoff,
)
from ai_statistician.research_agent_runtime_audit import (
    _audit_result_path,
    _runtime_capability_scorecard,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.simulation_engineer_llm import (
    build_simulation_engineer_prompt,
)


def _question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="semantic-review-test",
        title="Review a generated statistical experiment",
        description="Determine whether the generated experiment measures its claim.",
        tags=("semantic-review",),
    )


def _review_response(
    *,
    accept: bool,
    repair_scope: str = "source_code",
) -> dict[str, object]:
    rows = [
        {
            "dimension": dimension,
            "status": "PASS",
            "rationale": f"The exact source and result support {dimension}.",
            "evidence_refs": [f"exact_executed_artifacts[0].{dimension}"],
        }
        for dimension in GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS
    ]
    findings: list[dict[str, object]] = []
    instructions: list[str] = []
    if not accept:
        rows[-1]["status"] = "FAIL"
        rows[-1]["rationale"] = "The returned metric measures a different quantity."
        findings = [
            {
                "severity": "high",
                "category": "metric_semantics",
                "summary": "The metric label and implemented quantity differ.",
                "required_change": "Compute the frozen protocol quantity directly.",
                "repair_scope": repair_scope,
                "evidence_refs": ["exact_source_code", "exact_result"],
            }
        ]
        instructions = ["Regenerate code that computes the frozen protocol quantity."]
    source_assessment = (
        "ALIGNED"
        if accept or repair_scope != "source_code"
        else "SOURCE_REPAIR_REQUIRED"
    )
    metric_contract_assessment = (
        "INVALID_OR_INFEASIBLE"
        if not accept and repair_scope == "upstream_metric_contract"
        else "VALID_AND_FEASIBLE"
    )
    theory_assessment = (
        "THEORY_REVISION_REQUIRED"
        if not accept and repair_scope == "upstream_theory"
        else "SUFFICIENT_FOR_IMPLEMENTATION_REPAIR"
    )
    verdict = "ACCEPT" if accept else "REVISE"
    repair_scopes = generated_code_semantic_review_repair_scopes(
        verdict=verdict,
        source_assessment=source_assessment,
        metric_contract_assessment=metric_contract_assessment,
        theory_assessment=theory_assessment,
    )
    repair_plan = [
        {
            "sequence": index,
            "repair_scope": scope,
            "repair_owner": (
                "ArchitectCoordinator"
                if scope.startswith("upstream_")
                else "AlgorithmEngineer"
            ),
        }
        for index, scope in enumerate(repair_scopes, start=1)
    ]
    return {
        "reviewed_source_assessment": source_assessment,
        "frozen_metric_contract_assessment": metric_contract_assessment,
        "source_theory_assessment": theory_assessment,
        "dimension_reviews": rows,
        "findings": findings,
        "overall_verdict": verdict,
        "repair_scope": "none" if accept else repair_scope,
        "repair_scopes": repair_scopes,
        "repair_plan": repair_plan,
        "repair_owner": "AlgorithmEngineer",
        "repair_instructions": instructions,
    }


def _reviewer(
    *,
    accept: bool,
    model: str = "static-sonnet-reviewer",
    model_tier: str = "sonnet",
    repair_scope: str = "source_code",
):
    return LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(
            _review_response(accept=accept, repair_scope=repair_scope)
        ),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=model,
            model_tier=model_tier,
            max_repair_attempts=0,
        ),
    )


def test_semantic_review_lineage_budget_survives_architect_replans() -> None:
    work_order = {
        "question_id": "generic-question",
        "theory_packet_id": "theory:one",
        "theory_packet_hash": "theory-hash-one",
        "source_subsystem": "AlgorithmEngineer",
    }
    review_packet = _review_response(accept=False)

    first = advance_generated_code_semantic_review_lineage_budget(
        architect_context={},
        work_order=work_order,
        review_packet=review_packet,
        max_local_revisions=1,
    )
    assert first["local_repair_available"] is True
    assert first["architect_replan_available"] is True
    first_ledger = record_generated_code_semantic_review_lineage_action(
        first,
        action="local_repair",
    )

    second = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: first_ledger
        },
        work_order=work_order,
        review_packet=review_packet,
        max_local_revisions=1,
    )
    assert second["local_repair_available"] is False
    assert second["architect_replan_available"] is True
    second_ledger = record_generated_code_semantic_review_lineage_action(
        second,
        action="architect_replan",
    )

    third = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: second_ledger
        },
        work_order=work_order,
        review_packet=review_packet,
        max_local_revisions=1,
    )
    assert third["local_repair_available"] is False
    assert third["architect_replan_available"] is False
    assert third["lineage_budget_exhausted"] is True
    assert third["row"]["rejection_count"] == 3

    fresh_theory = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: second_ledger
        },
        work_order={**work_order, "theory_packet_hash": "theory-hash-two"},
        review_packet=review_packet,
        max_local_revisions=1,
    )
    assert fresh_theory["lineage_key"] != third["lineage_key"]
    assert fresh_theory["local_repair_available"] is True

    different_finding_packet = json.loads(json.dumps(review_packet))
    different_finding_packet["findings"][0]["category"] = "data_generation"
    changed_finding_after_local_repair = (
        advance_generated_code_semantic_review_lineage_budget(
            architect_context={
                GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: first_ledger
            },
            work_order=work_order,
            review_packet=different_finding_packet,
            max_local_revisions=1,
        )
    )
    assert changed_finding_after_local_repair["lineage_key"] != third["lineage_key"]
    assert (
        changed_finding_after_local_repair["source_lineage_key"]
        == third["source_lineage_key"]
    )
    assert changed_finding_after_local_repair["local_repair_available"] is False
    assert changed_finding_after_local_repair["architect_replan_available"] is True

    changed_finding_after_replan = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: second_ledger
        },
        work_order=work_order,
        review_packet=different_finding_packet,
        max_local_revisions=1,
    )
    assert changed_finding_after_replan["lineage_key"] != third["lineage_key"]
    assert changed_finding_after_replan["local_repair_available"] is True
    assert changed_finding_after_replan["row"][
        "post_replan_local_repair_available"
    ] is True
    assert changed_finding_after_replan["architect_replan_available"] is False
    assert changed_finding_after_replan["lineage_budget_exhausted"] is False

    final_local_ledger = record_generated_code_semantic_review_lineage_action(
        changed_finding_after_replan,
        action="local_repair",
    )
    after_final_local_repair = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: final_local_ledger
        },
        work_order=work_order,
        review_packet=different_finding_packet,
        max_local_revisions=1,
    )
    assert after_final_local_repair["local_repair_available"] is False
    assert after_final_local_repair["architect_replan_available"] is False
    assert after_final_local_repair["lineage_budget_exhausted"] is True


def test_upstream_theory_feedback_is_consumed_once_and_globally_bounded() -> None:
    def replan(
        *,
        prior_theory_packet_id: str,
        review_execution_id: str,
    ) -> dict[str, object]:
        return {
            "artifact_kind": "RuntimeGeneratedCodeSemanticReviewReplanContext",
            "source_subsystem": "AlgorithmEngineer",
            "source_manifest_id": "algorithm:rejected",
            "review_packet_id": f"review-packet:{review_execution_id}",
            "review_execution_id": review_execution_id,
            "repair_scope": "upstream_theory",
            "pending_artifact_ids": {
                "theory_packet_id": prior_theory_packet_id,
            },
        }

    first_replan = replan(
        prior_theory_packet_id="theory:one",
        review_execution_id="review-execution:one",
    )
    first_context = {
        "runtime_generated_code_semantic_review_replan": first_replan,
        "environment_feedback": {
            "semantic_review_execution_id": "review-execution:one",
        },
        "runtime_feedback_loop": {
            "semantic_review_execution_id": "review-execution:one",
        },
    }
    first_state = generated_code_semantic_review_upstream_theory_revision_state(
        architect_context=first_context,
        question_id="generic-question",
        max_revisions=2,
    )
    assert first_state["active"] is True
    assert first_state["budget_exhausted"] is False

    consumed_once = consume_generated_code_semantic_review_upstream_theory_replan(
        architect_context=first_context,
        question_id="generic-question",
        revised_theory_packet_id="theory:two",
        revised_theory_packet_hash="theory-hash-two",
        max_revisions=2,
    )
    assert "runtime_generated_code_semantic_review_replan" not in consumed_once
    assert "environment_feedback" not in consumed_once
    assert "runtime_feedback_loop" not in consumed_once
    resolution = consumed_once[
        "runtime_generated_code_semantic_review_replan_resolution"
    ]
    assert resolution["resolution_status"] == (
        "CONSUMED_BY_FRESH_THEORY_REVISION"
    )
    assert resolution["requires_fresh_metric_protocol_review"] is True

    second_context = {
        **consumed_once,
        "runtime_generated_code_semantic_review_replan": replan(
            prior_theory_packet_id="theory:two",
            review_execution_id="review-execution:two",
        ),
    }
    consumed_twice = consume_generated_code_semantic_review_upstream_theory_replan(
        architect_context=second_context,
        question_id="generic-question",
        revised_theory_packet_id="theory:three",
        revised_theory_packet_hash="theory-hash-three",
        max_revisions=2,
    )
    ledger = consumed_twice[
        GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_LEDGER_KEY
    ]
    assert next(iter(ledger.values()))["revisions_used"] == 2

    third_context = {
        **consumed_twice,
        "runtime_generated_code_semantic_review_replan": replan(
            prior_theory_packet_id="theory:three",
            review_execution_id="review-execution:three",
        ),
    }
    exhausted = generated_code_semantic_review_upstream_theory_revision_state(
        architect_context=third_context,
        question_id="generic-question",
        max_revisions=2,
    )
    assert exhausted["budget_exhausted"] is True
    result = generated_code_semantic_review_upstream_theory_budget_exhausted_result(
        task=AgentTask(
            task_id="theory:blocked",
            owner_subsystem="TheoryDeveloper",
            objective="Do not repeat an exhausted upstream theory revision.",
        ),
        question_id="generic-question",
        budget_state=exhausted,
    )
    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_upstream_theory_revision_budget_exhausted"
    )


def test_semantic_review_allows_only_one_post_replan_local_repair() -> None:
    work_order = {
        "question_id": "generic-question",
        "theory_packet_id": "theory:one",
        "theory_packet_hash": "theory-hash-one",
        "source_subsystem": "AlgorithmEngineer",
    }
    upstream_packet = _review_response(
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    initial = advance_generated_code_semantic_review_lineage_budget(
        architect_context={},
        work_order=work_order,
        review_packet=upstream_packet,
        max_local_revisions=1,
    )
    assert initial["local_repair_available"] is False
    replanned_ledger = record_generated_code_semantic_review_lineage_action(
        initial,
        action="architect_replan",
    )

    source_packet = _review_response(accept=False, repair_scope="source_code")
    source_packet["findings"][0]["category"] = "first_source_defect"
    first_post_replan = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: replanned_ledger
        },
        work_order=work_order,
        review_packet=source_packet,
        max_local_revisions=1,
    )
    assert first_post_replan["local_repair_available"] is True
    final_local_ledger = record_generated_code_semantic_review_lineage_action(
        first_post_replan,
        action="local_repair",
    )

    second_source_packet = json.loads(json.dumps(source_packet))
    second_source_packet["findings"][0]["category"] = "second_source_defect"
    second_post_replan = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: final_local_ledger
        },
        work_order=work_order,
        review_packet=second_source_packet,
        max_local_revisions=1,
    )
    assert second_post_replan["local_repair_available"] is False
    assert second_post_replan["architect_replan_available"] is False
    assert second_post_replan["lineage_budget_exhausted"] is True
    assert second_post_replan["row"][
        "source_post_replan_local_repair_count"
    ] == 1


def _runtime_fixture(
    tmp_path: Path,
    *,
    accept: bool,
    capability_eval: bool = False,
    reviewer_model: str = "",
    reviewer_model_tier: str = "",
    metric_failed: bool = False,
    repair_scope: str = "source_code",
):
    question = _question()
    code = (
        "def run_estimator(request):\n"
        "    return {'estimated_error': request['numerator'] / request['denominator']}\n\n"
        "def run_sandbox(seed, replicates):\n"
        "    return run_estimator({'numerator': seed % 7, "
        "'denominator': max(replicates, 1)})\n"
    )
    metrics = {"estimated_error": 0.03, "sandbox_failed": False}
    script_path = tmp_path / "generated.py"
    result_path = tmp_path / "result.json"
    script_path.write_text(code, encoding="utf-8")
    result_path.write_text(json.dumps(metrics), encoding="utf-8")
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:test",
        "derivation_steps": [{"claim": "The metric estimates the target error."}],
    }
    source_model_tier = (
        LIVE_EVALUATION_CLAUDE_MODEL_TIER if capability_eval else "sonnet"
    )
    source_model = f"source-{source_model_tier}"
    proposal_packet = {
        "artifact_kind": "AlgorithmEngineerProposalPacket",
        "packet_id": "algorithm-proposal:test",
        "source_agent": "LLMAlgorithmEngineerAgent",
        "model": source_model,
        "model_tier": source_model_tier,
    }
    row = {
        "estimator_id": "generated-estimator",
        "prototype_status": "FAILED_METRIC_GATE" if metric_failed else "EXECUTED",
        "executor": "generated_python_sandbox",
        "executor_profile": "stdlib",
        "language": "python",
        "dependencies": [],
        "script_path": str(script_path),
        "result_path": str(result_path),
        "script_hash": stable_hash(code),
        "result_hash": stable_hash(metrics),
        "metrics": metrics,
        "runtime_seed": 41,
        "runtime_replicates": 100,
        "metric_contracts": [],
        "metric_contract_set_id": "metric-contracts:test",
        "metric_requirement_set_id": "metric-requirements:test",
        "metric_contract_evaluation": {
            "all_required_passed": not metric_failed,
            "evaluations": [
                {
                    "contract_id": "metric-contract:test",
                    "requirement_id": "frozen:algorithm-error",
                    "required": True,
                    "passed": not metric_failed,
                }
            ],
        },
        "execution_smoke_passed": True,
        "smoke_passed": not metric_failed,
    }
    source_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm_sandbox_manifest:test",
        "theory_packet_id": theory_packet["packet_id"],
        "prototypes": [row],
        "n_generated_code_executed": 1,
        "n_passed": 0 if metric_failed else 1,
    }
    architect_context = {
        "architect_runtime_plan": {
            "evidence_contract": {
                "evaluation_mode": (
                    "capability_eval" if capability_eval else "debug"
                ),
                "empirical_metric_requirements": [
                    {
                        "requirement_id": "frozen:simulation-calibration",
                        "target_subsystems": ["SimulationEngineer"],
                        "metric_name": "calibration",
                    },
                ],
            }
        }
    }
    repair_task = AgentTask(
        task_id="algorithm:test",
        owner_subsystem="AlgorithmEngineer",
        objective="Generate and execute algorithm code.",
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "theory_packet_id": theory_packet["packet_id"],
            "simulation_manifest_id": "simulation:test",
            "implementation_gaps": [{"estimator_id": "generated-estimator"}],
            "architect_context": architect_context,
        },
    )
    deferred_task = AgentTask(
        task_id="formalize:test",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize after semantic acceptance.",
        inputs={
            "question": repair_task.inputs["question"],
            "theory_packet_id": theory_packet["packet_id"],
            "algorithm_sandbox_manifest_id": source_manifest["manifest_id"],
            "architect_context": architect_context,
        },
    )
    dispatch = _runtime_generated_code_semantic_review_dispatch(
        task=repair_task,
        question=question,
        source_subsystem="AlgorithmEngineer",
        source_manifest=source_manifest,
        theory_packet=theory_packet,
        proposal_packet=proposal_packet,
        architect_context=architect_context,
        deferred_next_task=deferred_task,
        max_revisions=1,
        metric_failure_feedback=(
            {
                "feedback_type": "algorithm_sandbox_execution_feedback",
                "feedback_id": "metric-feedback:test",
                "failure_classification": (
                    "generated_algorithm_sandbox_metric_gate_failed"
                ),
                "generated_algorithm_prototypes": [row],
            }
            if metric_failed
            else None
        ),
    )
    assert dispatch is not None
    blackboard = BlackboardState(project_id="semantic-review-test")
    blackboard.artifacts.update(
        {
            str(theory_packet["packet_id"]): theory_packet,
            str(proposal_packet["packet_id"]): proposal_packet,
            str(source_manifest["manifest_id"]): source_manifest,
            str(dispatch["work_order_id"]): dispatch["work_order"],
        }
    )
    subsystem = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=_reviewer(
            accept=accept,
            model=reviewer_model or f"static-{source_model_tier}-reviewer",
            model_tier=reviewer_model_tier or source_model_tier,
            repair_scope=repair_scope,
        ),
        max_revisions=1,
    )
    return subsystem, dispatch["next_task"], blackboard, script_path


def test_generated_code_semantic_reviewer_accepts_and_resumes_deferred_task(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "FormalizationEvaluator"
    accepted = result.next_task.inputs["accepted_generated_code_semantic_reviews"]
    assert accepted[0]["overall_verdict"] == "ACCEPT"
    executions = [
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    ]
    assert executions[0]["semantic_review_accepted"] is True
    assert executions[0]["reviewer_model_tier"] == "sonnet"
    assert executions[0]["independent_invocation"] is True
    work_order = next(
        row
        for row in blackboard.artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewWorkOrder"
    )
    responsibility = work_order["source_responsibility_contract"]
    assert responsibility["generated_code_author_subsystem"] == (
        "AlgorithmEngineer"
    )
    assert responsibility["assigned_requirement_ids"] == []
    assert responsibility["sibling_only_requirement_refs"] == [
        {
            "requirement_id": "frozen:simulation-calibration",
            "target_subsystems": ["SimulationEngineer"],
        }
    ]
    assert executions[0][
        "source_responsibility_contract_fingerprint"
    ] == stable_hash(responsibility)
    materialization = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    assert materialization["review_material"][
        "source_responsibility_contract"
    ] == responsibility
    review_material = materialization["review_material"]
    assert review_material["architect_frozen_evidence_contract"][
        "empirical_metric_requirements"
    ] == []
    projection = review_material["review_scope_projection"]
    assert projection["assigned_requirement_ids"] == []
    assert projection["sibling_only_requirement_refs"] == (
        responsibility["sibling_only_requirement_refs"]
    )
    assert projection[
        "canonical_architect_evidence_contract_fingerprint"
    ] == stable_hash(work_order["architect_evidence_contract"])


def test_accepted_algorithm_review_hands_exact_source_to_simulation(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, script_path = _runtime_fixture(
        tmp_path,
        accept=True,
    )
    result = subsystem.run(task, blackboard)
    blackboard.artifacts.update(result.produced_artifacts)
    assert result.next_task is not None
    context = result.next_task.inputs["architect_context"]

    handoff = result.next_task.inputs["upstream_algorithm_handoff"]
    assert _runtime_validated_algorithm_handoff(
        task=result.next_task,
        architect_context=context,
        blackboard=blackboard,
        question_id=_question().id,
        theory_packet_id="theory:test",
        algorithm_sandbox_manifest_id="algorithm_sandbox_manifest:test",
    ) == handoff

    exact = handoff["exact_algorithm_artifacts"][0]
    assert exact["estimator_id"] == "generated-estimator"
    assert exact["exact_source_code"] == script_path.read_text(encoding="utf-8")
    assert exact["exact_source_hash"] == stable_hash(exact["exact_source_code"])
    receipt = _runtime_algorithm_handoff_receipt(handoff)
    assert receipt["algorithm_sandbox_manifest_id"] == (
        "algorithm_sandbox_manifest:test"
    )
    assert receipt["exact_algorithm_artifact_refs"][0][
        "exact_source_hash"
    ] == exact["exact_source_hash"]
    assert receipt["handoff_fingerprint"] == stable_hash(handoff)
    assert receipt["mechanical_estimator_invocation_verified"] is False
    bound_receipt = _runtime_algorithm_handoff_receipt(
        handoff,
        simulation_rows=[
            {
                "simulation_id": "confirmatory-dgp",
                "script_hash": "simulation-source-hash",
                "result_hash": "simulation-result-hash",
                "execution_envelope_hash": "execution-envelope-hash",
                "estimator_binding_hash": stable_hash(
                    {exact["estimator_id"]: exact["exact_source_hash"]}
                ),
                "bound_estimator_code_hashes": {
                    exact["estimator_id"]: exact["exact_source_hash"]
                },
                "estimator_invocation_counts": {exact["estimator_id"]: 50},
                "mechanical_estimator_invocation_verified": True,
            }
        ],
    )
    assert bound_receipt["mechanical_estimator_invocation_verified"] is True
    assert bound_receipt["mechanical_invocation_evidence"][0][
        "estimator_invocation_counts"
    ] == {exact["estimator_id"]: 50}
    forged_receipt = _runtime_algorithm_handoff_receipt(
        handoff,
        simulation_rows=[
            {
                **bound_receipt["mechanical_invocation_evidence"][0],
                "script_hash": "simulation-source-hash",
                "result_hash": "simulation-result-hash",
                "estimator_invocation_counts": {exact["estimator_id"]: 0},
                "mechanical_estimator_invocation_verified": True,
            }
        ],
    )
    assert forged_receipt["mechanical_estimator_invocation_verified"] is False
    prompt = build_simulation_engineer_prompt(
        question=_question(),
        theory_packet={"packet_id": "theory:test", "theorem_cards": []},
        registered_problem={},
        registered_procedures=[],
        n_runs=50,
        seed=12,
        environment_feedback={"upstream_algorithm_handoff": handoff},
    )
    assert json.dumps(exact["exact_source_code"])[1:-1] in prompt
    assert exact["exact_source_hash"] in prompt
    assert "Do not silently replace it" in prompt
    assert "run_sandbox(seed, replicates, estimators)" in prompt
    assert "runtime-injected" in prompt


def test_algorithm_handoff_rejects_tampered_review_materialization(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    result = subsystem.run(task, blackboard)
    blackboard.artifacts.update(result.produced_artifacts)
    assert result.next_task is not None
    materialization = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    materialization["review_material"]["exact_executed_artifacts"][0][
        "exact_source_code"
    ] += "\n# changed after review\n"

    assert _runtime_validated_algorithm_handoff(
        task=result.next_task,
        architect_context=result.next_task.inputs["architect_context"],
        blackboard=blackboard,
        question_id=_question().id,
        theory_packet_id="theory:test",
        algorithm_sandbox_manifest_id="algorithm_sandbox_manifest:test",
    ) == {}


def test_algorithm_review_cannot_accept_legacy_metric_gate_failure(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        metric_failed=True,
    )
    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "accepted_algorithm_handoff_materialization_failed"
    )


def test_semantic_reviewer_prompt_keeps_sibling_metrics_out_of_artifact_gate() -> None:
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material={
            "source_responsibility_contract": {
                "assigned_requirement_ids": ["algorithm:assigned"],
                "sibling_only_requirement_refs": [
                    {
                        "requirement_id": "simulation:sibling",
                        "target_subsystems": ["SimulationEngineer"],
                    }
                ],
            }
        },
    )

    assert "requirements assigned to its author subsystem" in prompt
    assert "omitting a requirement assigned only to a sibling artifact" in prompt
    assert "least-authority view" in prompt
    assert "cannot make a required dimension FAIL" in prompt
    assert "reject any current-source proposal claim" in prompt
    assert "frozen_metric_contract_assessment=VALID_AND_FEASIBLE" in prompt
    assert "source_theory_assessment=THEORY_REVISION_REQUIRED" in prompt
    assert "AgentRuntime derives every repair scope and owner" in prompt
    assert "do not authorize post-result threshold relaxation" in prompt
    assert "unambiguous current theory" in prompt
    assert "do not choose one side as a coding instruction" in prompt
    assert "conservative, zero, noisy" in prompt
    assert "findings must include at least one specific row" in prompt


def test_semantic_review_routes_valid_protocol_implementation_mismatch_to_source() -> None:
    assert generated_code_semantic_review_repair_scope(
        verdict="REVISE",
        source_assessment="SOURCE_REPAIR_REQUIRED",
        metric_contract_assessment="VALID_AND_FEASIBLE",
        theory_assessment="SUFFICIENT_FOR_IMPLEMENTATION_REPAIR",
    ) == "source_code"


def test_mixed_semantic_assessments_preserve_both_repair_owners(
    tmp_path: Path,
) -> None:
    _, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    response = _review_response(accept=False, repair_scope="source_code")
    response["source_theory_assessment"] = "THEORY_REVISION_REQUIRED"
    response["frozen_metric_contract_assessment"] = (
        "NOT_APPLICABLE_EXPLORATORY"
    )
    repaired_findings = [
        *response["findings"],
        {
            "severity": "high",
            "category": "theory_premise",
            "summary": "The current theory omits a premise needed downstream.",
            "required_change": "Revise the theory packet before final acceptance.",
            "repair_scope": "upstream_theory",
            "evidence_refs": ["theory_packet.derivation_steps"],
        },
    ]

    class MixedOwnerPatchBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = response
            else:
                repair_payload = json.loads(
                    request.user_prompt.split("\n\n", 1)[1]
                )
                payload = {
                    "base_payload_fingerprint": repair_payload[
                        "base_payload_fingerprint"
                    ],
                    "updates": [
                        {
                            "path": ["frozen_metric_contract_assessment"],
                            "replacement_json": json.dumps(
                                "VALID_AND_FEASIBLE"
                            ),
                        },
                        {
                            "path": ["findings"],
                            "replacement_json": json.dumps(repaired_findings),
                        }
                    ],
                }
            return GeneratorResponse(
                text=json.dumps(payload),
                provider=self.provider_name,
                model=request.model,
            )

    backend = MixedOwnerPatchBackend()
    subsystem = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=LLMGeneratedCodeSemanticReviewerAgent(
            provider=backend,
            config=GeneratedCodeSemanticReviewerConfig(
                provider_name="anthropic",
                model=LIVE_EVALUATION_CLAUDE_MODEL,
                model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
                max_repair_attempts=1,
            ),
        ),
        max_revisions=1,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert len(backend.requests) == 2
    assert backend.requests[1].metadata["json_repair_mode"] == (
        "typed_semantic_patch"
    )
    assert backend.requests[1].max_tokens == 3000
    repair_payload = json.loads(
        backend.requests[1].user_prompt.split("\n\n", 1)[1]
    )
    assert any(
        "This is a confirmatory review" in instruction
        and "NOT_APPLICABLE_EXPLORATORY is invalid" in instruction
        for instruction in repair_payload["repair_instructions"]
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["repair_scopes"] == ["source_code", "upstream_theory"]
    assert [row["repair_owner"] for row in feedback["repair_plan"]] == [
        "AlgorithmEngineer",
        "ArchitectCoordinator",
    ]
    pending = result.next_task.inputs["architect_context"][
        "runtime_generated_code_semantic_review_pending_repair_plan"
    ]
    assert pending["pending_repair_scopes"] == ["upstream_theory"]
    assert pending["theory_packet_hash"] == stable_hash(
        blackboard.artifacts["theory:test"]
    )


def test_unchanged_upstream_artifact_cannot_retire_pending_repair() -> None:
    theory_packet = {"packet_id": "theory:test", "claim": "unchanged"}
    evidence_contract = {"requirements": ["unchanged"]}
    review_material = {
        "theory_packet": theory_packet,
        "architect_frozen_evidence_contract": evidence_contract,
        "pending_repair_plan": {
            "pending_repair_scopes": [
                "upstream_theory",
                "upstream_metric_contract",
            ],
            "theory_packet_hash": stable_hash(theory_packet),
            "architect_evidence_contract_hash": stable_hash(evidence_contract),
        },
    }
    packet = {
        "source_theory_assessment": "SUFFICIENT_FOR_IMPLEMENTATION_REPAIR",
        "frozen_metric_contract_assessment": "VALID_AND_FEASIBLE",
    }

    errors = generated_code_semantic_review_pending_plan_errors(
        packet=packet,
        review_material=review_material,
    )

    assert any("unchanged theory" in error for error in errors)
    assert any("unchanged metric contract" in error for error in errors)
    changed_material = {
        **review_material,
        "theory_packet": {**theory_packet, "claim": "revised"},
        "architect_frozen_evidence_contract": {"requirements": ["revised"]},
    }
    assert generated_code_semantic_review_pending_plan_errors(
        packet=packet,
        review_material=changed_material,
    ) == []


def test_generated_code_semantic_reviewer_routes_rejection_to_fresh_generation(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    assert result.next_task.task_id.startswith("semantic-review-revise:")
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["overall_verdict"] == "REVISE"
    assert feedback["findings"][0]["severity"] == "high"
    assert result.next_task.inputs["generated_code_semantic_review_revision_count"] == 1
    handoff = result.next_task.inputs["architect_context"]["runtime_feedback_loop"][
        "direct_repair_handoff_contract"
    ]
    assert handoff["architect_pre_authorized"] is True
    assert handoff["source_reviewer_subsystem"] == (
        "GeneratedCodeSemanticReviewer"
    )
    assert handoff["target_repair_subsystem"] == "AlgorithmEngineer"
    assert handoff["target_task_id"] == result.next_task.task_id
    assert handoff["feedback_artifact_id"] == feedback[
        "semantic_review_packet_id"
    ]
    assert handoff["proof_evidence_status"] == "NOT_PROOF_EVIDENCE"


def test_changed_finding_cannot_reset_source_lineage_repair_budget(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    first = subsystem.run(task, blackboard)
    assert first.next_task is not None
    first_context = first.next_task.inputs["architect_context"]

    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    for task_field in ("repair_task", "deferred_next_task"):
        task_payload = dict(work_order[task_field])
        task_inputs = dict(task_payload["inputs"])
        task_inputs["architect_context"] = first_context
        task_payload["inputs"] = task_inputs
        work_order[task_field] = task_payload
    work_order["review_revision_count"] = 0

    changed_response = _review_response(accept=False)
    changed_response["findings"][0]["category"] = "data_generation"
    changed_reviewer = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=LLMGeneratedCodeSemanticReviewerAgent(
            provider=StaticJSONGeneratorBackend(changed_response),
            config=GeneratedCodeSemanticReviewerConfig(
                provider_name="static",
                model="changed-finding-sonnet-reviewer",
                model_tier="sonnet",
                max_repair_attempts=0,
            ),
        ),
        max_revisions=1,
    )
    second = changed_reviewer.run(
        AgentTask(
            task_id="semantic-review:changed-finding",
            owner_subsystem=task.owner_subsystem,
            objective=task.objective,
            inputs={
                **task.inputs,
                "architect_context": first_context,
                "work_order_hash": stable_hash(work_order),
            },
        ),
        blackboard,
    )

    assert second.status == "REROUTE"
    assert second.next_task is not None
    assert second.next_task.owner_subsystem == "ArchitectCoordinator"
    assert second.failure_classification == (
        "generated_code_semantic_review_revision_budget_escalated_to_architect"
    )
    execution = next(
        row
        for row in second.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    )
    budget = execution["semantic_review_lineage_budget"]
    assert budget["source_local_repair_count"] == 1
    assert budget["source_architect_replan_count"] == 0
    assert budget["selected_action"] == "architect_replan"


def test_semantic_review_budget_exhaustion_resumes_deferred_architect_replan(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    deferred = dict(work_order["deferred_next_task"])
    deferred["task_id"] = "architect-metric-replan:test"
    deferred["owner_subsystem"] = "ArchitectCoordinator"
    deferred["objective"] = "Diagnose the cross-subsystem metric failure."
    deferred_inputs = dict(deferred["inputs"])
    deferred_inputs["environment_feedback"] = {
        "feedback_type": "runtime_metric_gate_feedback",
        "feedback_id": "metric-feedback:prior",
    }
    deferred_inputs["architect_context"] = {
        **dict(deferred_inputs.get("architect_context", {}) or {}),
        "runtime_metric_gate_replan": {
            "source_manifest_id": work_order["source_manifest_id"],
            "source_artifact_remains_unaccepted": True,
        },
    }
    deferred["inputs"] = deferred_inputs
    work_order["deferred_next_task"] = deferred
    work_order["review_revision_count"] = 1
    task.inputs["work_order_hash"] = stable_hash(work_order)

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.failure_classification == (
        "generated_code_semantic_review_revision_budget_escalated_to_architect"
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    assert result.next_task.task_id.startswith(
        "semantic-review-architect-replan:"
    )
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["feedback_id"] == "metric-feedback:prior"
    assert feedback["overall_verdict"] == "REVISE"
    assert feedback["semantic_review_revision_budget"] == {
        "revisions_used": 1,
        "max_revisions": 1,
        "source_artifact_remains_unaccepted": True,
    }
    context = result.next_task.inputs["architect_context"]
    assert context["runtime_metric_gate_replan"][
        "source_artifact_remains_unaccepted"
    ] is True
    handoff = context["runtime_feedback_loop"][
        "direct_repair_handoff_contract"
    ]
    assert handoff["target_repair_subsystem"] == "ArchitectCoordinator"
    assert handoff["target_task_id"] == result.next_task.task_id
    assert handoff["feedback_artifact_id"] == feedback[
        "semantic_review_packet_id"
    ]
    execution = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    )
    assert execution["semantic_review_accepted"] is False
    assert "accepted_generated_code_semantic_reviews" not in result.next_task.inputs


def test_upstream_semantic_finding_routes_directly_to_architect(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_metric_contract",
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.failure_classification == (
        "generated_code_semantic_review_metric_protocol_revision_required"
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["repair_scope"] == "upstream_metric_contract"
    assert feedback["repair_owner_agent"] == "ArchitectCoordinator"
    replan = result.next_task.inputs["architect_context"][
        "runtime_generated_code_semantic_review_replan"
    ]
    assert replan["repair_scope"] == "upstream_metric_contract"
    assert replan["source_manifest_id"] == "algorithm_sandbox_manifest:test"
    assert replan["deferred_next_owner_subsystem"] == "FormalizationEvaluator"
    assert "fresh candidate run" in replan["protocol_revision_policy"]
    assert result.next_task.inputs[
        "generated_code_semantic_review_revision_count"
    ] == 0


def test_post_result_metric_protocol_revision_stops_current_candidate(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    review_result = subsystem.run(task, blackboard)
    assert review_result.next_task is not None

    class CoordinatorMustNotRun:
        metric_semantic_reviewer = None

        def __init__(self) -> None:
            self.calls = 0

        def propose(self, **_kwargs):
            self.calls += 1
            raise AssertionError("post-result protocol guard must run before replanning")

    coordinator = CoordinatorMustNotRun()
    guard = ArchitectCoordinatorRuntimeSubsystem(
        coordinator=coordinator,
        runtime_config=ResearchAgentRuntimeConfig(
            metric_protocol_max_fresh_candidate_revisions=0
        ),
    )

    result = guard.run(review_result.next_task, blackboard)

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert coordinator.calls == 0
    assert result.failure_classification == "evaluation_protocol_revision_required"
    manifest = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeEvaluationProtocolRevisionRequired"
    )
    assert manifest["disposition"] == "EVALUATION_PROTOCOL_REVISION_REQUIRED"
    assert manifest["current_candidate_acceptance_eligible"] is False
    assert manifest["post_result_protocol_mutation_allowed"] is False
    assert manifest["fresh_candidate_required"] is True
    assert manifest["source_requirement_set_id"]
    assert manifest["source_semantic_review_packet_id"] == (
        review_result.next_task.inputs["environment_feedback"][
            "semantic_review_packet_id"
        ]
    )
    assert manifest["pending_artifact_ids"]
    assert result.evidence_entries[0].status == (
        "CURRENT_CANDIDATE_BLOCKED_FRESH_PROTOCOL_RUN_REQUIRED"
    )


def test_post_result_metric_protocol_revision_starts_versioned_fresh_candidate(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    review_result = subsystem.run(task, blackboard)
    assert review_result.next_task is not None
    context = review_result.next_task.inputs["architect_context"]
    context["theory_packet_id"] = "theory:test"
    context["architect_metric_protocol_theory_material"] = {
        "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
        "source_theory_packet_id": "theory:test",
        "source_theory_packet_hash": "theory-hash",
        "theory_semantic_material": {"packet_id": "theory:test"},
        "execution_results_available": False,
    }
    context["architect_metric_protocol_gate"] = {
        "artifact_kind": "RuntimeArchitectMetricProtocolGate",
        "accepted_requirement_set_id": "metric-requirements:test",
        "execution_authorized": True,
        "consumed": True,
    }

    class CoordinatorMustNotRun:
        metric_semantic_reviewer = None

        def __init__(self) -> None:
            self.calls = 0

        def propose(self, **_kwargs):
            self.calls += 1
            raise AssertionError("fresh-candidate guard must route before proposal")

    coordinator = CoordinatorMustNotRun()
    guard = ArchitectCoordinatorRuntimeSubsystem(
        coordinator=coordinator,
        runtime_config=ResearchAgentRuntimeConfig(
            seed=41,
            metric_protocol_max_fresh_candidate_revisions=1,
        ),
    )

    result = guard.run(review_result.next_task, blackboard)

    assert result.status == "REROUTE"
    assert result.failure_classification == (
        "evaluation_protocol_fresh_candidate_requested"
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    assert coordinator.calls == 0
    manifest = next(iter(result.produced_artifacts.values()))
    assert manifest["fresh_candidate_auto_routed"] is True
    assert manifest["fresh_candidate_seed"] != 41
    assert manifest["source_requirement_set_id"]

    fresh_context = result.next_task.inputs["architect_context"]
    fresh_revision = fresh_context[
        "architect_metric_protocol_fresh_candidate_revision"
    ]
    assert fresh_revision["raw_execution_artifacts_included"] is False
    assert fresh_revision[
        "structural_feedback_may_summarize_prior_observations"
    ] is True
    assert fresh_revision["post_result_threshold_relaxation_allowed"] is False
    assert fresh_revision["source_requirement_rows"]
    assert fresh_revision["source_requirement_set_id"] == manifest[
        "source_requirement_set_id"
    ]
    assert fresh_revision["structural_review_findings"] == [
        {
            "source_finding_index": 0,
            "severity": "high",
            "category": "metric_semantics",
            "required_change": "Compute the frozen protocol quantity directly.",
        }
    ]
    assert "summary" not in fresh_revision["structural_review_findings"][0]
    assert "evidence_refs" not in fresh_revision[
        "structural_review_findings"
    ][0]
    assert fresh_context["runtime_candidate_seed"] == manifest[
        "fresh_candidate_seed"
    ]
    assert fresh_context["architect_runtime_plan"]["evidence_contract"][
        "empirical_metric_requirements"
    ] == []
    assert "runtime_generated_code_semantic_review_replan" not in fresh_context


def test_upstream_theory_scope_remains_an_architect_replan_not_protocol_stop(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_theory",
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.failure_classification == (
        "generated_code_semantic_review_upstream_theory_repair_escalated_to_architect"
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    assert result.next_task.inputs["environment_feedback"]["repair_scope"] == (
        "upstream_theory"
    )


def test_source_semantic_revision_budget_escalates_even_without_deferred_architect(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    assert work_order["deferred_next_task"]["owner_subsystem"] == (
        "FormalizationEvaluator"
    )
    work_order["review_revision_count"] = 1
    task.inputs["work_order_hash"] = stable_hash(work_order)

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.failure_classification == (
        "generated_code_semantic_review_revision_budget_escalated_to_architect"
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    assert result.next_task.inputs["environment_feedback"][
        "semantic_review_revision_budget"
    ] == {
        "revisions_used": 1,
        "max_revisions": 1,
        "source_artifact_remains_unaccepted": True,
    }


def test_metric_failing_but_executed_code_is_independently_reviewed(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        metric_failed=True,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    materialization = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    source_row = materialization["review_material"]["exact_executed_artifacts"][0][
        "source_row"
    ]
    assert source_row["prototype_status"] == "FAILED_METRIC_GATE"
    assert source_row["execution_smoke_passed"] is True
    assert source_row["smoke_passed"] is False


def test_coding_agent_prompts_preserve_independent_semantic_findings() -> None:
    rationale = (
        "The implemented update treats each observation as a fresh prior draw, "
        "which is not the joint mixture defined by the theory packet and changes "
        "the martingale being evaluated."
    )
    required_change = (
        "Use one shared latent parameter across the full sequence, compute the "
        "joint marginal likelihood, and rerun the unchanged frozen protocol."
    )
    feedback = {
        "feedback_type": "generated_code_semantic_review_feedback",
        "feedback_source": "GeneratedCodeSemanticReviewer",
        "source_subsystem": "AlgorithmEngineer",
        "semantic_review_execution_id": "semantic-execution:test",
        "semantic_review_packet_id": "semantic-packet:test",
        "overall_verdict": "REVISE",
        "dimension_reviews": [
            {
                "dimension": "theory_assumption_alignment",
                "status": "FAIL",
                "rationale": rationale,
                "evidence_refs": ["exact_source_code:update"],
            }
        ],
        "findings": [
            {
                "severity": "high",
                "category": "joint_model_semantics",
                "summary": "The generated update implements a different model.",
                "required_change": required_change,
                "evidence_refs": ["theory_packet", "exact_source_code"],
            }
        ],
        "repair_instructions": [required_change],
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
    }
    theory_packet = {
        "packet_id": "theory:test",
        "theorem_cards": [],
        "estimator_specs": [],
    }
    algorithm_prompt = build_algorithm_engineer_prompt(
        question=_question(),
        theory_packet=theory_packet,
        simulation_manifest={},
        implementation_gaps=[{"estimator_id": "joint-mixture"}],
        environment_feedback=feedback,
    )
    simulation_prompt = build_simulation_engineer_prompt(
        question=_question(),
        theory_packet=theory_packet,
        registered_problem={},
        registered_procedures=[],
        n_runs=50,
        seed=11,
        environment_feedback={
            **feedback,
            "source_subsystem": "SimulationEvaluator",
        },
    )

    for prompt in (algorithm_prompt, simulation_prompt):
        assert "generated_code_semantic_review" in prompt
        assert rationale in prompt
        assert required_change in prompt
        assert "treat" in prompt
        assert "as binding" in prompt
        assert "do not respond by only changing metric paths" in prompt
        assert '"metric_evaluation_semantics"' in prompt
    assert "Never place a quorum in threshold" in simulation_prompt
    assert "pre-thresholded 0/1 flags" in simulation_prompt
    assert "Set metric_contracts to an empty array" in algorithm_prompt
    assert "Never place a quorum in threshold" not in algorithm_prompt


def test_generated_code_semantic_reviewer_rejects_tampered_source_before_model_call(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, script_path = _runtime_fixture(
        tmp_path,
        accept=True,
    )
    script_path.write_text("def run_sandbox(seed, replicates):\n    return {'x': 1}\n")

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_input_invalid"
    )
    assert not result.produced_artifacts


def test_capability_eval_accepts_separate_same_model_reviewer_invocation(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        capability_eval=True,
        reviewer_model="source-haiku",
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    execution = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    )
    assert execution["independent_agent"] is True
    assert execution["independent_invocation"] is True
    assert execution["independent_model"] is False
    assert execution["reviewer_model_tier"] == LIVE_EVALUATION_CLAUDE_MODEL_TIER


def test_capability_eval_rejects_non_evaluation_reviewer_tier(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        capability_eval=True,
        reviewer_model_tier="sonnet",
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_verdict_invalid"
    )
    assert result.observations
    assert LIVE_EVALUATION_CLAUDE_MODEL_TIER in result.observations[0].summary


def test_capability_eval_rejects_missing_source_provenance_before_model(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        capability_eval=True,
    )
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    work_order["source_model"] = ""
    task.inputs["work_order_hash"] = stable_hash(work_order)

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_input_invalid"
    )
    assert not result.produced_artifacts


def test_semantic_review_validator_rejects_incomplete_dimension_set() -> None:
    packet = {
        **_review_response(accept=True),
        "proof_evidence_status": "GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE",
        "kernel_verified": False,
        "source_subsystem": "AlgorithmEngineer",
        "work_order_id": "work-order:test",
        "work_order_hash": "hash",
        "source_manifest_id": "manifest:test",
        "source_manifest_hash": "hash",
        "review_input_fingerprint": "hash",
    }
    packet["dimension_reviews"] = packet["dimension_reviews"][:-1]

    errors = validate_generated_code_semantic_review_packet(packet)

    assert any("each required dimension exactly once" in error for error in errors)
    assert any("overall_verdict must be ACCEPT" in error for error in errors)


def test_semantic_review_validator_binds_upstream_scope_to_architect() -> None:
    packet = {
        **_review_response(
            accept=False,
            repair_scope="upstream_metric_contract",
        ),
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE"
        ),
        "kernel_verified": False,
        "source_subsystem": "AlgorithmEngineer",
        "work_order_id": "work-order:test",
        "work_order_hash": "hash",
        "source_manifest_id": "manifest:test",
        "source_manifest_hash": "hash",
        "review_input_fingerprint": "hash",
    }

    errors = validate_generated_code_semantic_review_packet(packet)

    assert any(
        "upstream semantic repair must route to ArchitectCoordinator" in error
        for error in errors
    )
    packet["repair_owner"] = "ArchitectCoordinator"
    assert validate_generated_code_semantic_review_packet(packet) == []


def test_capability_scorecard_requires_both_independent_semantic_review_lanes() -> None:
    scorecard = _runtime_capability_scorecard(
        {
            "n_generated_code_semantic_review_work_orders": 2,
            "n_generated_code_semantic_review_executions": 2,
            "n_generated_code_semantic_review_accepted": 2,
            "n_generated_algorithm_semantic_review_accepted": 1,
            "n_generated_simulation_semantic_review_accepted": 1,
            "n_generated_code_semantic_review_independent_evaluation_model": 2,
            "n_live_generated_code_sandbox_executed": 1,
            "n_live_generated_simulation_sandbox_executed": 1,
        }
    )
    rows = {row["requirement_id"]: row for row in scorecard["rows"]}

    assert rows["generated_code_semantic_review_executed"]["passed"] is True
    assert rows["generated_algorithm_semantic_review_accepted"]["passed"] is True
    assert rows["generated_simulation_semantic_review_accepted"]["passed"] is True
    assert rows[
        "generated_code_semantic_review_independent_evaluation_model"
    ]["passed"] is True


def test_runtime_audit_recomputes_semantic_review_lineage(tmp_path: Path) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        capability_eval=True,
    )
    result = subsystem.run(task, blackboard)
    artifacts = {**blackboard.artifacts, **result.produced_artifacts}
    result_path = tmp_path / "semantic-review-runtime-result.json"
    result_path.write_text(
        json.dumps(
            {
                "status": "BLOCKED",
                "blackboard": {"artifacts": artifacts},
                "traces": [],
            }
        ),
        encoding="utf-8",
    )

    audit_row = _audit_result_path(result_path)

    assert audit_row.n_generated_code_semantic_review_work_orders == 1
    assert audit_row.n_generated_code_semantic_review_executions == 1
    assert audit_row.n_generated_code_semantic_review_accepted == 1
    assert audit_row.n_generated_algorithm_semantic_review_accepted == 1
    assert (
        audit_row.n_generated_code_semantic_review_independent_evaluation_model
        == 1
    )
    assert not [
        error for error in audit_row.errors if "semantic review" in error
    ]

    original_payload = json.loads(result_path.read_text(encoding="utf-8"))
    tampered = json.loads(json.dumps(original_payload))
    execution = next(
        artifact
        for key, artifact in tampered["blackboard"]["artifacts"].items()
        if key.startswith("generated_code_semantic_review_execution:")
    )
    execution["source_model"] = execution["reviewer_model"]
    result_path.write_text(json.dumps(tampered), encoding="utf-8")

    tampered_row = _audit_result_path(result_path)

    assert any(
        "semantic review execution provenance mismatch for source_model" in error
        for error in tampered_row.errors
    )
    assert any(
        "semantic review execution model independence mismatch" in error
        for error in tampered_row.errors
    )
    assert tampered_row.n_generated_code_semantic_review_accepted == 0
    assert tampered_row.n_generated_algorithm_semantic_review_accepted == 0
    assert (
        tampered_row.n_generated_code_semantic_review_independent_evaluation_model
        == 0
    )

    invalid_packet_payload = json.loads(json.dumps(original_payload))
    invalid_artifacts = invalid_packet_payload["blackboard"]["artifacts"]
    invalid_execution = next(
        artifact
        for key, artifact in invalid_artifacts.items()
        if key.startswith("generated_code_semantic_review_execution:")
    )
    invalid_packet = invalid_artifacts[invalid_execution["review_packet_id"]]
    invalid_packet["dimension_reviews"] = invalid_packet["dimension_reviews"][:-1]
    invalid_execution["review_packet_hash"] = stable_hash(invalid_packet)
    result_path.write_text(json.dumps(invalid_packet_payload), encoding="utf-8")

    invalid_packet_row = _audit_result_path(result_path)

    assert any(
        "semantic review packet invalid" in error
        for error in invalid_packet_row.errors
    )
    assert invalid_packet_row.n_generated_code_semantic_review_accepted == 0

    forged_responsibility_payload = json.loads(json.dumps(original_payload))
    forged_artifacts = forged_responsibility_payload["blackboard"]["artifacts"]
    forged_execution = next(
        artifact
        for key, artifact in forged_artifacts.items()
        if key.startswith("generated_code_semantic_review_execution:")
    )
    forged_work_order = forged_artifacts[forged_execution["work_order_id"]]
    forged_contract = forged_work_order["source_responsibility_contract"]
    forged_contract["assigned_requirement_ids"] = [
        "frozen:simulation-calibration"
    ]
    forged_fingerprint = stable_hash(forged_contract)
    forged_work_order[
        "source_responsibility_contract_fingerprint"
    ] = forged_fingerprint
    forged_execution[
        "source_responsibility_contract_fingerprint"
    ] = forged_fingerprint
    result_path.write_text(
        json.dumps(forged_responsibility_payload),
        encoding="utf-8",
    )

    forged_responsibility_row = _audit_result_path(result_path)

    assert any(
        "semantic review source-responsibility contract mismatch" in error
        for error in forged_responsibility_row.errors
    )
    assert forged_responsibility_row.n_generated_code_semantic_review_accepted == 0

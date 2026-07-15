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
    validate_generated_code_semantic_review_packet,
)
from ai_statistician.model_backend import StaticJSONGeneratorBackend
from ai_statistician.research_agent_runtime import (
    GeneratedCodeSemanticReviewerRuntimeSubsystem,
    _runtime_generated_code_semantic_review_dispatch,
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


def _review_response(*, accept: bool) -> dict[str, object]:
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
                "evidence_refs": ["exact_source_code", "exact_result"],
            }
        ]
        instructions = ["Regenerate code that computes the frozen protocol quantity."]
    return {
        "dimension_reviews": rows,
        "findings": findings,
        "overall_verdict": "ACCEPT" if accept else "REVISE",
        "repair_owner": "AlgorithmEngineer",
        "repair_instructions": instructions,
    }


def _reviewer(*, accept: bool, model: str = "static-opus-reviewer"):
    return LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(_review_response(accept=accept)),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=model,
            model_tier="opus",
            max_repair_attempts=0,
        ),
    )


def _runtime_fixture(
    tmp_path: Path,
    *,
    accept: bool,
    capability_eval: bool = False,
    reviewer_model: str = "static-opus-reviewer",
    metric_failed: bool = False,
):
    question = _question()
    code = (
        "def run_sandbox(seed, replicates):\n"
        "    return {'estimated_error': (seed % 7) / max(replicates, 1)}\n"
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
    proposal_packet = {
        "artifact_kind": "AlgorithmEngineerProposalPacket",
        "packet_id": "algorithm-proposal:test",
        "source_agent": "LLMAlgorithmEngineerAgent",
        "model": "source-sonnet",
        "model_tier": "sonnet",
    }
    row = {
        "estimator_id": "generated-estimator",
        "prototype_status": "FAILED_METRIC_GATE" if metric_failed else "EXECUTED",
        "executor": "generated_python_sandbox",
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
                        "requirement_id": "frozen:algorithm-error",
                        "target_subsystems": ["AlgorithmEngineer"],
                        "metric_name": "estimated_error",
                    },
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
        reviewer=_reviewer(accept=accept, model=reviewer_model),
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
    assert executions[0]["reviewer_model_tier"] == "opus"
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
    assert responsibility["assigned_requirement_ids"] == [
        "frozen:algorithm-error"
    ]
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
    assert "reject any current-source proposal claim" in prompt


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
        environment_feedback=feedback,
    )

    for prompt in (algorithm_prompt, simulation_prompt):
        assert "generated_code_semantic_review" in prompt
        assert rationale in prompt
        assert required_change in prompt
        assert "treat" in prompt
        assert "as binding" in prompt
        assert "do not respond by only changing metric paths" in prompt


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


def test_capability_eval_requires_reviewer_model_independent_of_source(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        capability_eval=True,
        reviewer_model="source-sonnet",
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_verdict_invalid"
    )


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


def test_capability_scorecard_requires_both_independent_semantic_review_lanes() -> None:
    scorecard = _runtime_capability_scorecard(
        {
            "n_generated_code_semantic_review_work_orders": 2,
            "n_generated_code_semantic_review_executions": 2,
            "n_generated_code_semantic_review_accepted": 2,
            "n_generated_algorithm_semantic_review_accepted": 1,
            "n_generated_simulation_semantic_review_accepted": 1,
            "n_generated_code_semantic_review_independent_opus": 2,
            "n_live_generated_code_sandbox_executed": 1,
            "n_live_generated_simulation_sandbox_executed": 1,
        }
    )
    rows = {row["requirement_id"]: row for row in scorecard["rows"]}

    assert rows["generated_code_semantic_review_executed"]["passed"] is True
    assert rows["generated_algorithm_semantic_review_accepted"]["passed"] is True
    assert rows["generated_simulation_semantic_review_accepted"]["passed"] is True
    assert rows["generated_code_semantic_review_independent_opus"]["passed"] is True


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
    assert audit_row.n_generated_code_semantic_review_independent_opus == 1
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
    assert tampered_row.n_generated_code_semantic_review_independent_opus == 0

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

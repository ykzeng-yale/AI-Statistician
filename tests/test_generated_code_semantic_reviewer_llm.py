from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_reviewer_llm import (
    GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS,
    GeneratedCodeSemanticReviewerConfig,
    LLMGeneratedCodeSemanticReviewerAgent,
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
        "prototype_status": "EXECUTED",
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
        "smoke_passed": True,
    }
    source_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm_sandbox_manifest:test",
        "theory_packet_id": theory_packet["packet_id"],
        "prototypes": [row],
        "n_generated_code_executed": 1,
        "n_passed": 1,
    }
    architect_context = {
        "architect_runtime_plan": {
            "evidence_contract": {
                "evaluation_mode": (
                    "capability_eval" if capability_eval else "debug"
                ),
                "empirical_metric_requirements": [
                    {"requirement_id": "frozen:error", "metric_name": "estimated_error"}
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

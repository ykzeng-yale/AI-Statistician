from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

import pytest

from ai_statistician.cli import _load_runtime_learning_memory, main
from ai_statistician.algorithm_engineer_llm import (
    AlgorithmEngineerConfig,
    LLMAlgorithmEngineerAgent,
    build_algorithm_engineer_prompt,
)
from ai_statistician.architect_coordinator_llm import (
    ArchitectCoordinatorConfig,
    LLMArchitectCoordinatorAgent,
    build_architect_coordinator_prompt,
    validate_architect_coordinator_packet,
)
from ai_statistician.critic_evaluator_llm import (
    CriticEvaluatorConfig,
    LLMCriticEvaluatorAgent,
    build_critic_evaluator_prompt,
)
from ai_statistician.formalizer_llm import (
    FormalizerConfig,
    LLMFormalizerProofEngineerAgent,
    build_formalizer_prompt,
)
from ai_statistician.formalization_gap_planner_standalone import (
    validate_standalone_input_payload,
)
from ai_statistician.formalization_gap_planner_runtime_handoff_audit import (
    audit_formalization_gap_planner_runtime_handoffs,
)
from ai_statistician.proof_state_feedback import (
    PROOF_STATE_FEEDBACK_STATUS,
    LocalLeanProofStateFeedbackProvider,
)
from ai_statistician.research_agent_runtime import (
    AlgorithmEngineerRuntimeSubsystem,
    FormalizationEvaluatorRuntimeSubsystem,
    ResearchAgentRuntimeConfig,
    _critic_learning_rows,
    _critic_next_action_agenda,
    _proof_bank_obligation_request_ids,
    _registered_algorithm_template_hint,
    _runtime_bridge_learning_rows,
    _runtime_learning_memory_kernel_verified_proof_obligation_ids,
    _runtime_learning_memory_kernel_verified_source_theorem_semantic_primitives,
    _runtime_learning_memory_proof_obligation_ids,
    _runtime_completion_summary,
    _formalizer_proof_bank_runtime_memory_summary,
    _formalizer_source_theorem_semantic_primitive_work_orders,
    _formalizer_source_theorem_promotion_work_orders,
    _runtime_formalization_gap_planner_bridge,
    _runtime_formalization_gap_planner_target_intake_payload,
    _runtime_source_theorem_semantic_primitive_work_order_rows,
    _runtime_source_theorem_semantic_primitive_work_order_rows_from_learning_rows,
    _runtime_source_theorem_formal_environment_work_order_rows,
    _runtime_source_theorem_formal_environment_work_order_rows_from_learning_rows,
    _source_theorem_formal_environment_work_order_rows_from_artifact_verifier_payload,
    _runtime_source_theorem_formal_environment_proof_body_executor_learning_rows,
    _runtime_source_theorem_promotion_work_order_rows,
    _runtime_source_theorem_promotion_work_order_rows_from_learning_rows,
    _runtime_source_theorem_promotion_handoff_rows,
    _runtime_source_theorem_promotion_materialization_seed_rows,
    _runtime_source_theorem_promotion_bridge_learning_rows,
    _run_runtime_source_theorem_promotion_proofengineer_bridge,
    _run_runtime_source_theorem_formal_environment_bridge_stack,
    _write_runtime_source_theorem_promotion_materialization_seed_queue,
    _runtime_theorem_reduction_closure_work_order_rows,
    _runtime_evidence_summary,
    _runtime_failure_summary,
    _llm_agent_topology_row,
    _run_generated_python_sandbox,
    _run_split_conformal_interval_prototype,
    run_research_agent_runtime,
)
from ai_statistician.formal_verifier_agentic_proof_execution_materializer import (
    export_formal_verifier_agentic_proof_execution_materializer,
)
from ai_statistician.formal_verifier_agentic_proof_execution_artifact_verifier import (
    export_formal_verifier_agentic_proof_execution_artifact_verifier,
)
from ai_statistician.formal_verifier_agentic_proof_source_theorem_promotion_queue import (
    export_formal_verifier_agentic_proof_source_theorem_promotion_queue,
)
from ai_statistician.formal_verifier_agentic_proof_source_theorem_integrator import (
    export_formal_verifier_agentic_proof_source_theorem_integrator,
)
from ai_statistician.research_agent_runtime_audit import (
    _audit_topology,
    _runtime_capability_ladder,
    _resolve_manifest_paths,
    audit_research_agent_runtime,
)
from ai_statistician.research_system_audit import _research_agent_runtime_audit_overlay
from ai_statistician.agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
)
from ai_statistician.research_architect import (
    LLMTheoryDeveloperAgent,
    ResearchArchitectConfig,
    StaticArchitectLLMProvider,
    build_theory_developer_prompt,
)
from ai_statistician.research_lab import load_open_research_questions
from ai_statistician.research_lab import FormalSubclaimProver, ProblemFormalizer, TheoryPlanner
from ai_statistician.research_schema import (
    FormalSubclaim,
    OpenResearchQuestion,
    ResearchProblemSpec,
    TheoremGoal,
)
from ai_statistician.schema import ProofCheck
from ai_statistician.simulation_engineer_llm import (
    LLMSimulationEngineerAgent,
    SimulationEngineerConfig,
    build_simulation_engineer_prompt,
)
from ai_statistician.verifier import MockProofVerifier


def test_architect_coordinator_prompt_requires_long_horizon_research_memory() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    prompt = build_architect_coordinator_prompt(
        question=question,
        architect_context={},
        runtime_config={"max_iterations": 12, "max_critic_repair_rounds": 1},
    )

    assert "problem_analysis_before_retrieval" in prompt
    assert "dynamic_stat_knowledge_bank" in prompt
    assert "literature_fair_comparison_gate" in prompt
    assert "proposer_verifier_iteration" in prompt
    assert "embedding/RAG similarity" in prompt
    assert "only Lean/AXLE/local kernel rows" in prompt
    assert '"problem_analysis"' in prompt
    assert '"stat_knowledge_bank_plan"' in prompt
    assert '"literature_fair_comparison_plan"' in prompt


def test_architect_coordinator_validator_requires_research_control_fields() -> None:
    packet = dict(_architect_sample_response())
    packet.update(
        {
            "proof_evidence_status": "LLM_ARCHITECT_COORDINATOR_PROPOSAL_NOT_PROOF_EVIDENCE",
            "runtime_executed": False,
            "kernel_verified": False,
        }
    )
    packet.pop("problem_analysis")
    packet.pop("stat_knowledge_bank_plan")
    packet.pop("literature_fair_comparison_plan")

    errors = validate_architect_coordinator_packet(packet)

    assert "missing or empty field: problem_analysis" in errors
    assert "missing or empty field: stat_knowledge_bank_plan" in errors
    assert "missing or empty field: literature_fair_comparison_plan" in errors


def test_simulation_engineer_prompt_compacts_theory_context() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    prompt = build_simulation_engineer_prompt(
        question=question,
        theory_packet={
            "packet_id": "theory:test",
            "problem_card": {
                "estimand": "coverage",
                "assumptions": ["exchangeability", "x" * 5000],
                "desired_theorem_type": "finite-sample coverage",
                "irrelevant_long_field": "x" * 5000,
            },
            "estimator_specs": [
                {"id": "E1", "name": "split conformal", "algorithm_sketch": "calibrate residuals"},
                {"id": "E2", "name": "extra", "algorithm_sketch": "unused"},
                {"id": "E3", "name": "dropped", "algorithm_sketch": "unused"},
            ],
            "theorem_cards": [
                {
                    "id": "T1",
                    "conclusion": "coverage",
                    "semantic_risks": ["exchangeability semantics"],
                    "long_proof_strategy": "y" * 5000,
                }
            ],
            "simulation_ademp_spec": {
                "aim": "stress coverage",
                "dgps": ["nonlinear", "x" * 5000],
                "methods": ["split conformal", "x" * 5000],
            },
        },
        registered_problem={"problem_class": "distribution_free_conformal_prediction"},
        registered_procedures=[],
        n_runs=20,
        seed=7,
    )

    assert "x" * 5000 not in prompt
    assert "y" * 5000 not in prompt
    assert '"E1"' in prompt
    assert '"E3"' not in prompt
    assert "Return ONLY one compact JSON object" in prompt
    assert '"dgp_plan"' not in prompt
    assert '"failure_interpretation"' not in prompt


def test_algorithm_engineer_prompt_compacts_theory_and_simulation_context() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    long_text = "long_algorithm_context_" + ("z" * 5000)
    prompt = build_algorithm_engineer_prompt(
        question=question,
        theory_packet={
            "packet_id": "theory:test",
            "problem_card": {
                "estimand": "coverage",
                "assumptions": ["exchangeability", long_text],
                "desired_theorem_type": "finite-sample coverage",
                "unused_large_field": long_text,
            },
            "estimator_specs": [
                {"id": "E1", "name": "split conformal interval", "algorithm_sketch": long_text},
                {"id": "E2", "name": "extra", "algorithm_sketch": "unused"},
                {"id": "E3", "name": "dropped", "algorithm_sketch": "unused"},
            ],
            "theorem_cards": [
                {"id": "T1", "conclusion": long_text, "semantic_risks": [long_text]},
            ],
            "simulation_ademp_spec": {
                "methods": [long_text for _ in range(5)],
                "performance_measures": [long_text for _ in range(5)],
                "stress_tests": [long_text for _ in range(5)],
            },
        },
        simulation_manifest={
            "manifest_id": "simulation:test",
            "simulation_passed": True,
            "registered_procedures": [
                {"procedure_id": "split_conformal_interval", "registered_simulator": long_text}
            ],
            "simulations": [
                {"procedure_id": "E1", "passed": True, "metrics": {"coverage": long_text}},
                {"procedure_id": "E2", "passed": True, "metrics": {"unused": long_text}},
                {"procedure_id": "E3", "passed": True, "metrics": {"dropped": long_text}},
            ],
            "implementation_gaps": [{"estimator_id": "E1", "status": "gap", "reason": long_text}],
            "raw_large_trace": long_text,
        },
        implementation_gaps=[{"estimator_id": "E1", "status": "gap", "reason": long_text}],
    )

    assert "z" * 5000 not in prompt
    assert "raw_large_trace" not in prompt
    assert '"E1"' in prompt
    assert '"E3"' not in prompt
    assert "Return ONLY one compact JSON object" in prompt
    assert "leave sandbox_code_drafts empty whenever a template matches" in prompt
    assert '"code_generation_plan"' not in prompt
    assert '"promotion_gate"' not in prompt
    assert len(prompt) < 22000


def test_critic_evaluator_prompt_compacts_trace_context() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    long_text = "long_critic_context_" + ("q" * 5000)
    prompt = build_critic_evaluator_prompt(
        question=question,
        retrieval_manifest={"manifest_id": "retrieval:test", "boundary": long_text},
        theory_packet={"packet_id": "theory:test", "unused_large_field": long_text},
        simulation_manifest={"manifest_id": "simulation:test", "simulation_passed": True},
        algorithm_manifest={"manifest_id": "algorithm:test", "n_executed": 1, "n_passed": 1},
        formalization_manifest={
            "manifest_id": "formalization:test",
            "counts": {"kernel_verified": 0, "formal_gap": 1},
            "proof_evidence_status": "FORMAL_GAPS_REMAIN",
            "huge_trace": long_text,
        },
        deterministic_agenda=[
            {
                "id": f"agenda_{idx}",
                "owner_subsystem": "TheoryDeveloper",
                "trigger": long_text,
                "action": long_text,
                "acceptance_gate": long_text,
                "priority": "high",
                "unused_large_field": long_text,
            }
            for idx in range(8)
        ],
        deterministic_learning_rows=[
            {
                "learning_task": f"learn_{idx}",
                "input_signal": long_text,
                "target_behavior": long_text,
                "unused_large_field": long_text,
            }
            for idx in range(8)
        ],
    )

    assert "q" * 5000 not in prompt
    assert "unused_large_field" not in prompt
    assert '"agenda_0"' in prompt
    assert '"agenda_4"' not in prompt
    assert "Include only required fields" in prompt
    assert '"learning_updates"' not in prompt
    assert '"benchmark_expansion_plan"' not in prompt
    assert len(prompt) < 18000


def test_runtime_failure_summary_surfaces_failed_subsystem() -> None:
    completion = _runtime_completion_summary(
        [
            {
                "status": "FAILED",
                "final_task_id": "algorithm:q1:abc",
                "traces": [
                    {
                        "task": {
                            "task_id": "algorithm:q1:abc",
                            "inputs": {
                                "question": {"id": "q1", "title": "Question 1"},
                            },
                        },
                        "subsystem": "AlgorithmEngineer",
                        "status": "FAILED",
                        "failure_classification": "subsystem_exception",
                        "next_task_id": "",
                    }
                ],
            }
        ]
    )
    summary = _runtime_failure_summary(completion)

    assert summary["has_failure"] is True
    assert summary["failed_question_id"] == "q1"
    assert summary["failed_subsystem"] == "AlgorithmEngineer"
    assert summary["failed_task_id"] == "algorithm:q1:abc"
    assert summary["failure_classification"] == "subsystem_exception"


def test_runtime_failure_summary_does_not_label_budget_pending_as_failure() -> None:
    completion = _runtime_completion_summary(
        [
            {
                "status": "MAX_ITERATIONS_REACHED",
                "final_task_id": "theory-critic-revise:q1:abc",
                "traces": [
                    {
                        "task": {
                            "task_id": "critic:q1:abc",
                            "inputs": {
                                "question": {"id": "q1", "title": "Question 1"},
                            },
                        },
                        "subsystem": "CriticEvaluator",
                        "status": "REVISE",
                        "failure_classification": "critic_requested_theory_revision",
                        "next_task_id": "theory-critic-revise:q1:abc",
                    }
                ],
            }
        ]
    )
    summary = _runtime_failure_summary(completion)

    assert summary["has_failure"] is False
    assert summary["has_incomplete_pending_work"] is True
    assert summary["failed_subsystem"] == ""
    assert summary["terminal_subsystem"] == "CriticEvaluator"
    assert summary["terminal_kind"] == "budget_exhausted_with_pending_next_task"
    assert summary["pending_next_task_id"] == "theory-critic-revise:q1:abc"


def test_generated_algorithm_sandbox_rejects_unsafe_code(tmp_path: Path) -> None:
    prototype, tool_call = _run_generated_python_sandbox(
        sandbox_dir=tmp_path,
        estimator_id="unsafe_probe",
        spec={"id": "unsafe_probe"},
        code_draft={
            "code": (
                "import os\n"
                "def run_sandbox(seed: int, replicates: int) -> dict:\n"
                "    return {'cwd': os.getcwd(), 'sandbox_failed': False}\n"
            )
        },
        n_runs=10,
        seed=20260528,
        timeout_s=5,
    )

    assert prototype["prototype_status"] == "REJECTED_UNSAFE_GENERATED_CODE"
    assert prototype["executor"] == "generated_python_sandbox"
    assert prototype["smoke_passed"] is False
    assert prototype["promotion_ready"] is False
    assert any("cannot import modules" in row for row in prototype["safety_errors"])
    assert any("forbidden generated-code token" in row for row in prototype["safety_errors"])
    assert tool_call.tool_name == "python.generated_sandbox_precheck"
    assert tool_call.exit_status == "rejected"


def test_theory_developer_prompt_compacts_architect_and_retrieval_context() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    long_text = "long_context_" + ("x" * 4000)
    prompt = build_theory_developer_prompt(
        question,
        architect_context={
            "architect_coordinator_proposal_id": "architect:test",
            "architect_runtime_plan": {
                "problem_analysis": {
                    "theorem_family": "distribution-free coverage",
                    "statistical_objects": [long_text for _ in range(8)],
                    "key_obstacles": [long_text for _ in range(8)],
                    "unused_large_field": long_text,
                },
                "retrieval_strategy": {
                    "paper_queries": [long_text for _ in range(8)],
                    "formal_source_queries": [long_text for _ in range(8)],
                    "lean_rag_priorities": [long_text for _ in range(8)],
                },
                "subsystem_execution_plan": [
                    {
                        "subsystem": f"Subsystem{i}",
                        "objective": long_text,
                        "expected_artifacts": [long_text for _ in range(8)],
                        "acceptance_gate": long_text,
                    }
                    for i in range(8)
                ],
                "evidence_gates": [
                    {
                        "artifact_kind": f"gate{i}",
                        "required_evidence": long_text,
                        "not_evidence": long_text,
                    }
                    for i in range(8)
                ],
                "raw_unbounded_architect_notes": long_text,
            },
            "retrieval_context": {
                "knowledge_cards": [
                    {
                        "id": f"knowledge_{i}",
                        "title": f"Knowledge {i}",
                        "summary": long_text,
                        "tags": ["conformal"] * 20,
                    }
                    for i in range(8)
                ],
                "paper_sources": [
                    {
                        "id": f"paper_{i}",
                        "title": f"Paper {i}",
                        "summary": long_text,
                        "matched_terms": ["coverage"] * 20,
                    }
                    for i in range(8)
                ],
                "formal_source_hits": [
                    {
                        "theorem_goal_id": f"goal_{i}",
                        "hits": [
                            {
                                "source_id": "mathlib",
                                "path": "Mathlib/Probability.lean",
                                "line": 10 + j,
                                "kind": "theorem",
                                "name": f"hit_{i}_{j}",
                                "signature": "signature " + ("s" * 4000),
                                "matched_terms": ["probability"] * 20,
                            }
                            for j in range(8)
                        ],
                    }
                    for i in range(6)
                ],
                "boundary": "Retrieval hits are not proof evidence.",
            },
        },
    )

    assert "compact_theory_discovery_packet" in prompt
    assert "architect_runtime_plan_summary" in prompt
    assert "raw_unbounded_architect_notes" not in prompt
    assert "unused_large_field" not in prompt
    assert "knowledge_0" in prompt
    assert "knowledge_4" not in prompt
    assert "paper_0" in prompt
    assert "paper_4" not in prompt
    assert "hit_0_0" in prompt
    assert "hit_0_3" not in prompt
    assert "signature_omitted" in prompt
    assert "s" * 800 not in prompt
    assert "x" * 800 not in prompt
    assert len(prompt) < 30000


def test_algorithm_engineer_prompt_exposes_generated_python_safe_subset() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    prompt = build_algorithm_engineer_prompt(
        question=question,
        theory_packet={
            "packet_id": "theory:test",
            "estimator_specs": [{"id": "E1", "name": "split conformal interval"}],
            "theorem_cards": [],
            "simulation_ademp_spec": {},
        },
        simulation_manifest={
            "manifest_id": "simulation:test",
            "simulation_passed": True,
            "registered_procedures": [],
            "simulations": [],
            "implementation_gaps": [],
        },
        implementation_gaps=[
            {
                "estimator_id": "E1",
                "status": "REQUIRES_ALGORITHM_ENGINEER_ADAPTER",
                "reason": "No registered executable conformal adapter.",
            }
        ],
    )

    assert "safe_subset" in prompt
    assert "forbidden_dependencies" in prompt
    assert "numpy" in prompt
    assert "sklearn" in prompt
    assert "split_conformal_interval" in prompt
    assert "trusted split-conformal regression interval sandbox" in prompt
    assert "import or from-import statements" in prompt
    assert "method calls or attribute access except math.* and statistics.*" in prompt
    assert "leave sandbox_code_drafts empty" in prompt


def test_split_conformal_registered_template_hint_and_execution(tmp_path: Path) -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    template = _registered_algorithm_template_hint(
        proposal_target={},
        spec={
            "id": "E1",
            "name": "Split conformal interval",
            "algorithm_sketch": "Fit on train split, calibrate residual quantile, return prediction interval.",
        },
        question=question,
    )
    assert template == "split_conformal_interval"
    assert (
        _registered_algorithm_template_hint(
            proposal_target={"registered_template_hint": "none"},
            spec={
                "id": "E1",
                "name": "Split conformal interval",
                "algorithm_sketch": "Fit on train split, calibrate residual quantile.",
            },
            question=question,
        )
        == ""
    )

    prototype, tool_call = _run_split_conformal_interval_prototype(
        sandbox_dir=tmp_path,
        estimator_id="E1",
        spec={"id": "E1", "name": "Split conformal interval"},
        n_runs=12,
        seed=20260607,
        timeout_s=20,
    )

    assert prototype["prototype_status"] == "EXECUTED"
    assert prototype["executor"] == "registered_split_conformal_interval_template"
    assert prototype["smoke_passed"] is True
    assert prototype["promotion_ready"] is False
    assert "not theorem proof evidence" in prototype["boundary"]
    assert prototype["metrics"]["status"] == "ok"
    assert prototype["metrics"]["n_failed"] == 0
    assert 0.0 <= prototype["metrics"]["coverage_90"] <= 1.0
    assert prototype["metrics"]["mean_interval_width"] > 0.0
    assert tool_call.tool_name == "python.split_conformal_interval_sandbox"
    assert tool_call.exit_status == "0"


def test_algorithm_engineer_runtime_executes_registered_split_conformal_template(tmp_path: Path) -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    theory_packet_id = "theory:conformal"
    simulation_manifest_id = "simulation:conformal"
    blackboard = BlackboardState(
        project_id=f"runtime:{question.id}",
        artifacts={
            theory_packet_id: {
                "packet_id": theory_packet_id,
                "estimator_specs": [
                    {
                        "id": "E1",
                        "name": "Split conformal interval",
                        "algorithm_sketch": (
                            "Fit regression on train split, calibrate residual quantile, "
                            "return prediction interval."
                        ),
                    }
                ],
            },
            simulation_manifest_id: {
                "manifest_id": simulation_manifest_id,
                "simulation_passed": True,
            },
        },
    )
    algorithm_engineer = LLMAlgorithmEngineerAgent(
        provider=StaticArchitectLLMProvider(_conformal_algorithm_sample_response()),
        config=AlgorithmEngineerConfig(provider_name="static", model="static-conformal-algorithm-model"),
    )
    subsystem = AlgorithmEngineerRuntimeSubsystem(
        out_dir=tmp_path,
        n_runs=12,
        seed=20260607,
        proposal_agent=algorithm_engineer,
        timeout_s=20,
    )
    task = AgentTask(
        task_id="algorithm:conformal",
        owner_subsystem="AlgorithmEngineer",
        objective="Execute registered conformal sandbox template.",
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "theory_packet_id": theory_packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "implementation_gaps": [
                {
                    "estimator_id": "E1",
                    "status": "REQUIRES_ALGORITHM_ENGINEER_ADAPTER",
                    "reason": "Conformal estimator needs registered runtime template.",
                }
            ],
        },
        expected_artifacts=("algorithm_sandbox_manifest",),
    )

    result = subsystem.run(task, blackboard)
    manifest = next(
        artifact
        for key, artifact in result.produced_artifacts.items()
        if key.startswith("algorithm_sandbox_manifest:")
    )
    prototype = manifest["prototypes"][0]

    assert result.status == "REROUTE"
    assert manifest["n_executed"] == 1
    assert manifest["n_passed"] == 1
    assert manifest["n_generated_code_executed"] == 0
    assert manifest["n_unsafe_generated_code_rejected"] == 0
    assert prototype["executor"] == "registered_split_conformal_interval_template"
    assert prototype["llm_algorithm_engineer_target"]["registered_template_hint"] == "split_conformal_interval"
    assert prototype["metrics"]["status"] == "ok"
    assert any(row.tool_name == "python.split_conformal_interval_sandbox" for row in result.tool_calls)
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "FormalizationEvaluator"


def test_formal_subclaim_prover_uses_batch_kernel_verifier() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)

    class BatchKernelMockProofVerifier(MockProofVerifier):
        name = "batch-kernel-mock"

        def __init__(self) -> None:
            self.verify_calls = 0
            self.verify_many_calls = 0
            self.batch_sizes: list[int] = []

        async def verify(self, obligation, proof_body, retrieval_hits):
            self.verify_calls += 1
            check = await MockProofVerifier.verify(self, obligation, proof_body, retrieval_hits)
            return ProofCheck(
                obligation_id=check.obligation_id,
                ok=check.ok,
                proof_body=check.proof_body,
                verifier=self.name,
                verification_strength="mock_kernel_verified_batch_fallback",
                kernel_verified=check.ok,
                elapsed_ms=check.elapsed_ms,
                errors=check.errors,
                retrieval_hits=check.retrieval_hits,
            )

        async def verify_many(self, items):
            self.verify_many_calls += 1
            self.batch_sizes.append(len(items))
            checks = []
            for obligation, proof_body, retrieval_hits in items:
                check = await MockProofVerifier.verify(self, obligation, proof_body, retrieval_hits)
                checks.append(
                    ProofCheck(
                        obligation_id=check.obligation_id,
                        ok=check.ok,
                        proof_body=check.proof_body,
                        verifier=self.name,
                        verification_strength="mock_kernel_verified_batch",
                        kernel_verified=check.ok,
                        elapsed_ms=check.elapsed_ms,
                        errors=check.errors,
                        retrieval_hits=check.retrieval_hits,
                    )
                )
            return checks

    verifier = BatchKernelMockProofVerifier()
    subclaims = asyncio.run(FormalSubclaimProver(verifier=verifier).prove(problem, theorem_goals))
    registered_rows = [row for row in subclaims if row.claim_type == "lean_obligation"]
    formal_gap_rows = [row for row in subclaims if row.status == "FORMAL_GAP"]

    assert verifier.verify_many_calls == 1
    assert verifier.verify_calls == 0
    assert verifier.batch_sizes and verifier.batch_sizes[0] == len(registered_rows)
    assert registered_rows
    assert all(row.status == "PROVED" for row in registered_rows)
    assert all(row.kernel_verified for row in registered_rows)
    assert {row.verification_strength for row in registered_rows} == {"mock_kernel_verified_batch"}
    assert formal_gap_rows
    assert all(not row.kernel_verified for row in formal_gap_rows)


def test_formal_subclaim_prover_limits_registered_kernel_smoke() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)

    class BatchKernelSmokeVerifier(MockProofVerifier):
        name = "batch-kernel-smoke-mock"

        def __init__(self) -> None:
            self.batch_sizes: list[int] = []

        async def verify_many(self, items):
            self.batch_sizes.append(len(items))
            checks = []
            for obligation, proof_body, retrieval_hits in items:
                check = await MockProofVerifier.verify(self, obligation, proof_body, retrieval_hits)
                checks.append(
                    ProofCheck(
                        obligation_id=check.obligation_id,
                        ok=check.ok,
                        proof_body=check.proof_body,
                        verifier=self.name,
                        verification_strength="mock_kernel_verified_limited_batch",
                        kernel_verified=check.ok,
                        elapsed_ms=check.elapsed_ms,
                        errors=check.errors,
                        retrieval_hits=check.retrieval_hits,
                    )
                )
            return checks

    verifier = BatchKernelSmokeVerifier()
    prover = FormalSubclaimProver(verifier=verifier, max_proof_obligations=2)
    subclaims = asyncio.run(prover.prove(problem, theorem_goals))
    registered_rows = [row for row in subclaims if row.claim_type == "lean_obligation"]
    formal_gap_rows = [row for row in subclaims if row.status == "FORMAL_GAP"]
    control = prover.proof_obligation_control()

    assert verifier.batch_sizes == [2]
    assert len(registered_rows) == 2
    assert all(row.kernel_verified for row in registered_rows)
    assert formal_gap_rows
    assert control["n_candidate_proof_obligations"] > control["n_selected_proof_obligations"]
    assert control["n_selected_proof_obligations"] == 2
    assert "do not prove the full theorem" in control["selection_boundary"]


def test_formal_subclaim_prover_prioritizes_agent_requested_kernel_smoke() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)

    class BatchKernelSmokeVerifier(MockProofVerifier):
        name = "batch-kernel-priority-smoke-mock"

        def __init__(self) -> None:
            self.seen_obligation_ids: list[str] = []

        async def verify_many(self, items):
            checks = []
            for obligation, proof_body, retrieval_hits in items:
                self.seen_obligation_ids.append(obligation.id)
                check = await MockProofVerifier.verify(self, obligation, proof_body, retrieval_hits)
                checks.append(
                    ProofCheck(
                        obligation_id=check.obligation_id,
                        ok=check.ok,
                        proof_body=check.proof_body,
                        verifier=self.name,
                        verification_strength="mock_kernel_verified_priority_batch",
                        kernel_verified=check.ok,
                        elapsed_ms=check.elapsed_ms,
                        errors=check.errors,
                        retrieval_hits=check.retrieval_hits,
                    )
                )
            return checks

    verifier = BatchKernelSmokeVerifier()
    prover = FormalSubclaimProver(verifier=verifier, max_proof_obligations=1)
    subclaims = asyncio.run(
        prover.prove(
            problem,
            theorem_goals,
            prioritized_proof_obligation_ids=("variance_nonneg", "prob_measure_univ"),
        )
    )
    registered_rows = [row for row in subclaims if row.claim_type == "lean_obligation"]
    control = prover.proof_obligation_control()

    assert verifier.seen_obligation_ids == ["variance_nonneg"]
    assert [row.proof_obligation_id for row in registered_rows] == ["variance_nonneg"]
    assert control["prioritized_proof_obligation_ids"] == ["variance_nonneg", "prob_measure_univ"]
    assert control["selected_priority_proof_obligation_ids"] == ["variance_nonneg"]
    assert control["deferred_priority_proof_obligation_ids_due_to_max"] == ["prob_measure_univ"]
    assert control["deferred_proof_obligation_ids_due_to_max"]
    assert control["n_selected_proof_obligations"] == 1


def test_formal_subclaim_prover_excludes_already_verified_obligations_from_selection_pool() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)

    class SeenVerifier(MockProofVerifier):
        def __init__(self) -> None:
            self.seen_obligation_ids: list[str] = []

        async def verify(self, obligation, proof_body, retrieval_hits):  # type: ignore[no-untyped-def]
            self.seen_obligation_ids.append(obligation.id)
            return await super().verify(obligation, proof_body, retrieval_hits)

    verifier = SeenVerifier()
    prover = FormalSubclaimProver(verifier=verifier, max_proof_obligations=2)
    subclaims = asyncio.run(
        prover.prove(
            problem,
            theorem_goals,
            prioritized_proof_obligation_ids=("variance_nonneg", "event_indicator_expectation"),
            excluded_proof_obligation_ids=("variance_nonneg",),
        )
    )
    registered_rows = [row for row in subclaims if row.claim_type == "lean_obligation"]
    control = prover.proof_obligation_control()

    assert "variance_nonneg" in control["candidate_proof_obligation_ids"]
    assert control["excluded_proof_obligation_ids"] == ["variance_nonneg"]
    assert control["excluded_candidate_proof_obligation_ids"] == ["variance_nonneg"]
    assert "variance_nonneg" not in control["eligible_proof_obligation_ids_before_limit"]
    assert "variance_nonneg" not in control["selected_proof_obligation_ids"]
    assert "variance_nonneg" not in control["deferred_proof_obligation_ids_due_to_max"]
    assert [row.proof_obligation_id for row in registered_rows] == verifier.seen_obligation_ids
    assert "variance_nonneg" not in verifier.seen_obligation_ids


def test_formal_subclaim_prover_classifies_local_lean_timeout_separately() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)

    class TimeoutVerifier:
        name = "local.lake_env_lean"
        timeout_s = 1

        async def verify(self, obligation, proof_body, retrieval_hits):
            return ProofCheck(
                obligation_id=obligation.id,
                ok=False,
                proof_body=proof_body,
                verifier=self.name,
                verification_strength="local_lean_timeout",
                kernel_verified=False,
                errors=["local Lean verification timed out after 1s"],
                retrieval_hits=retrieval_hits,
            )

    prover = FormalSubclaimProver(
        verifier=TimeoutVerifier(),
        proof_obligation_ids=("prob_measure_univ",),
        max_proof_obligations=1,
    )
    subclaims = asyncio.run(prover.prove(problem, theorem_goals))
    control = prover.proof_obligation_control()
    registered_rows = [row for row in subclaims if row.claim_type == "lean_obligation"]

    assert [row.proof_obligation_id for row in registered_rows] == ["prob_measure_univ"]
    assert registered_rows[0].status == "FAILED"
    assert registered_rows[0].formalization_status == "verification_timeout"
    assert registered_rows[0].verification_strength == "local_lean_timeout"
    assert "timed out" in str(registered_rows[0].gap_reason)
    assert control["verifier"] == "local.lake_env_lean"
    assert control["verifier_timeout_s"] == 1


def test_formalizer_prompt_exposes_registered_proof_obligation_catalog() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    prover = FormalSubclaimProver()
    catalog = prover.proof_obligation_catalog(problem, theorem_goals)
    prompt = build_formalizer_prompt(
        question=question,
        theory_packet={"packet_id": "theory:test", "formalization_requests": []},
        simulation_manifest={"manifest_id": "simulation:test", "simulation_passed": True},
        algorithm_manifest={"manifest_id": "algorithm:test", "n_executed": 1},
        registered_problem={"problem_class": problem.problem_class},
        theorem_goals=[
            {
                "id": goal.id,
                "title": goal.title,
                "proof_obligations": list(goal.proof_obligations),
            }
            for goal in theorem_goals
        ],
        proof_bank_obligation_catalog=catalog,
    )

    assert "registered_proof_bank_obligation_catalog" in prompt
    assert "proof_bank_obligation_request_policy" in prompt
    assert "formal_target_portability_policy" in prompt
    assert "formal_statement_sketch" in prompt
    assert "lean_statement_sketch/lean_imports only as Lean legacy aliases" in prompt
    assert "variance_nonneg" in prompt
    assert "priority_only_for_kernel_smoke_selection" in prompt
    assert "proof_body" not in prompt


def test_llm_formalizer_normalizes_target_prover_neutral_formal_target_fields() -> None:
    response = _formalizer_sample_response()
    target = dict(response["formal_targets"][0])
    target.pop("lean_statement_sketch", None)
    target["id"] = "rocq_aipw_asymptotic_normality_open_target"
    target["target_prover_family"] = "rocq"
    target["formal_statement_sketch"] = (
        "Theorem aipw_asymptotic_normality_open_target : True."
    )
    target["formal_imports"] = ["Coq.Init.Logic"]
    response["formal_targets"] = [target]
    formalizer = LLMFormalizerProofEngineerAgent(
        provider=StaticArchitectLLMProvider(response),
        config=FormalizerConfig(provider_name="static", model="static-formalizer-model"),
    )

    packet = formalizer.propose(
        question=OpenResearchQuestion(
            id="rocq_formalizer_packet",
            title="Rocq formalizer packet",
            description="Check target-prover-neutral formalizer packet fields.",
        ),
        theory_packet={},
        simulation_manifest={},
        algorithm_manifest={},
        registered_problem={},
        theorem_goals=[],
    )

    normalized_target = packet["formal_targets"][0]
    assert normalized_target["target_prover_family"] == "rocq"
    assert normalized_target["formal_statement_sketch"].startswith("Theorem aipw")
    assert normalized_target["formal_imports"] == ["Coq.Init.Logic"]
    assert "lean_statement_sketch" not in normalized_target
    assert "lean_imports" not in normalized_target
    assert packet["proof_evidence_status"] == "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE"


def test_llm_formalizer_rejects_non_lean_legacy_formal_target_alias() -> None:
    response = _formalizer_sample_response()
    target = dict(response["formal_targets"][0])
    target["target_prover_family"] = "rocq"
    response["formal_targets"] = [target]
    formalizer = LLMFormalizerProofEngineerAgent(
        provider=StaticArchitectLLMProvider(response),
        config=FormalizerConfig(
            provider_name="static",
            model="static-formalizer-model",
            max_repair_attempts=0,
        ),
    )

    with pytest.raises(ValueError, match="non-Lean formal target must use"):
        formalizer.propose(
            question=OpenResearchQuestion(
                id="bad_rocq_formalizer_packet",
                title="Bad Rocq formalizer packet",
                description="Reject non-Lean packets that rely on Lean aliases.",
            ),
            theory_packet={},
            simulation_manifest={},
            algorithm_manifest={},
            registered_problem={},
            theorem_goals=[],
        )


def test_formalizer_prompt_targets_theorem_closure_when_proof_bank_memory_exhausted() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    prover = FormalSubclaimProver()
    catalog = prover.proof_obligation_catalog(problem, theorem_goals)
    summary = _formalizer_proof_bank_runtime_memory_summary(
        context={
            "environment_feedback": {
                "high_priority_agenda": [
                    {
                        "id": "formal_gap:theorem_reduction_closure",
                        "owner_subsystem": "Formalizer/LeanProver",
                    }
                ]
            }
        },
        proof_bank_obligation_catalog=catalog,
        theorem_goals=theorem_goals,
        memory_kernel_verified_proof_obligation_ids=tuple(
            str(row["obligation_id"]) for row in catalog
        ),
        memory_prioritized_proof_obligation_ids=(),
    )
    prompt = build_formalizer_prompt(
        question=question,
        theory_packet={"packet_id": "theory:test", "formalization_requests": []},
        simulation_manifest={"manifest_id": "simulation:test", "simulation_passed": True},
        algorithm_manifest={"manifest_id": "algorithm:test", "n_executed": 1},
        registered_problem={"problem_class": problem.problem_class},
        theorem_goals=[
            {
                "id": row.id,
                "title": row.title,
                "proof_obligations": list(row.proof_obligations),
            }
            for row in theorem_goals
        ],
        proof_bank_obligation_catalog=catalog,
        proof_bank_runtime_memory_summary=summary,
    )

    assert summary["proof_bank_bridge_catalog_exhausted_by_memory"] is True
    assert summary["theorem_reduction_closure_required"] is True
    assert summary["recommended_formalizer_target_mode"] == "theorem_level_reduction_closure"
    assert "proof_bank_runtime_memory_summary" in prompt
    assert "proof_bank_bridge_catalog_exhausted_by_memory" in prompt
    assert "theorem_level_reduction_closure" in prompt
    assert "do not spend the packet on more bridge-obligation requests" in prompt


def test_formalizer_prompt_includes_exact_source_candidate_repair_memory() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    summary = _formalizer_proof_bank_runtime_memory_summary(
        context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_theorem_reduction_closure_work_order_ids": [
                            "theorem_reduction_closure_work_order:good_rank"
                        ],
                        "kernel_verified_theorem_reduction_closure_target_ids": [
                            "split_conformal_finite_sample_coverage_reduction_closure"
                        ],
                        "kernel_verified_theorem_reduction_closure_goal_ids": [
                            "split_conformal_finite_sample_coverage"
                        ],
                        "kernel_verified_source_theorem_semantic_primitive_ids": [
                            "split_conformal_good_rank_set_inclusion_bridge"
                        ],
                    },
                    {
                        "learning_task": "source_theorem_exact_candidate_lean_feedback",
                        "input_summary": {
                            "trigger": "SOURCE_THEOREM_EXACT_CANDIDATE_LOCAL_LEAN_FAILED",
                            "target_theorem_name": "split_conformal_coverage",
                            "verification_status": "ARTIFACT_LOCAL_LEAN_FAILED",
                            "candidate_artifact_path": "runs/exact_source_candidate.lean",
                            "source_theorem_kernel_verified": False,
                            "diagnostics": [
                                "exact_source_candidate.lean:15:14: error: unexpected token '}'"
                            ],
                        },
                    },
                ],
            }
        },
        proof_bank_obligation_catalog=catalog,
        theorem_goals=theorem_goals,
        memory_kernel_verified_proof_obligation_ids=(),
        memory_prioritized_proof_obligation_ids=(),
    )
    prompt = build_formalizer_prompt(
        question=question,
        theory_packet={"packet_id": "theory:test", "formalization_requests": []},
        simulation_manifest={"manifest_id": "simulation:test", "simulation_passed": True},
        algorithm_manifest={"manifest_id": "algorithm:test", "n_executed": 1},
        registered_problem={"problem_class": problem.problem_class},
        theorem_goals=[
            {
                "id": row.id,
                "title": row.title,
                "proof_obligations": list(row.proof_obligations),
            }
            for row in theorem_goals
        ],
        proof_bank_obligation_catalog=catalog,
        proof_bank_runtime_memory_summary=summary,
    )

    assert summary["source_theorem_exact_candidate_requires_repair"] is True
    assert summary["recommended_source_theorem_integration_action"] == (
        "repair_exact_source_theorem_candidate_proof_body"
    )
    assert "source_theorem_exact_candidate_requires_repair" in prompt
    assert "repair_exact_source_theorem_candidate_proof_body" in prompt
    assert "SOURCE_THEOREM_EXACT_CANDIDATE_LOCAL_LEAN_FAILED" in prompt
    assert "unexpected token" in prompt
    assert "split_conformal_coverage" in prompt


def test_formalizer_prompt_includes_exact_source_proof_body_executor_feedback() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]
    summary = _formalizer_proof_bank_runtime_memory_summary(
        context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": verified_ids,
                        "kernel_verified_theorem_reduction_closure_work_order_ids": [
                            "theorem_reduction_closure_work_order:good_rank"
                        ],
                        "kernel_verified_theorem_reduction_closure_target_ids": [
                            "split_conformal_finite_sample_coverage_reduction_closure"
                        ],
                        "kernel_verified_theorem_reduction_closure_goal_ids": [
                            "split_conformal_finite_sample_coverage"
                        ],
                        "kernel_verified_source_theorem_semantic_primitive_ids": [
                            "split_conformal_good_rank_set_inclusion_bridge"
                        ],
                    },
                    {
                        "learning_task": (
                            "exact_source_theorem_proof_body_execution_feedback"
                        ),
                        "target_theorem_name": "split_conformal_coverage",
                        "trigger": "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED",
                        "input_summary": {
                            "execution_status": (
                                "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
                            ),
                            "target_theorem_name": "split_conformal_coverage",
                            "candidate_artifact_path": (
                                "runs/proof_body_attempt.lean"
                            ),
                            "source_theorem_kernel_verified": False,
                            "failure_classification": (
                                "formal_environment_placeholder_primitives"
                            ),
                            "formal_environment_placeholder_symbols": [
                                "Exchangeable",
                                "orderStat",
                            ],
                            "formal_environment_typeclass_blockers": [
                                "HSub ℕ ℝ ENNReal"
                            ],
                            "diagnostics": [
                                "split_conformal_coverage.lean:44:71: error: unsolved goals"
                            ],
                        },
                    },
                ],
            }
        },
        proof_bank_obligation_catalog=catalog,
        theorem_goals=theorem_goals,
        memory_kernel_verified_proof_obligation_ids=tuple(verified_ids),
        memory_prioritized_proof_obligation_ids=(),
    )
    prompt = build_formalizer_prompt(
        question=question,
        theory_packet={"packet_id": "theory:test", "formalization_requests": []},
        simulation_manifest={"manifest_id": "simulation:test", "simulation_passed": True},
        algorithm_manifest={"manifest_id": "algorithm:test", "n_executed": 1},
        registered_problem={"problem_class": problem.problem_class},
        theorem_goals=[
            {
                "id": row.id,
                "title": row.title,
                "proof_obligations": list(row.proof_obligations),
            }
            for row in theorem_goals
        ],
        proof_bank_obligation_catalog=catalog,
        proof_bank_runtime_memory_summary=summary,
    )

    assert summary["source_theorem_exact_candidate_requires_repair"] is True
    assert summary["source_theorem_exact_candidate_environment_gap"] is True
    assert summary["source_theorem_exact_candidate_repair_triggers"] == [
        "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
    ]
    assert summary["source_theorem_exact_candidate_failure_classifications"] == [
        "formal_environment_placeholder_primitives"
    ]
    assert summary["source_theorem_exact_candidate_repair_diagnostics"][0][
        "missing_formal_symbols"
    ] == ["Exchangeable", "orderStat"]
    assert summary["source_theorem_exact_candidate_repair_diagnostics"][0][
        "verification_status"
    ] == "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
    assert summary["source_theorem_exact_candidate_repair_diagnostics"][0][
        "candidate_artifact_path"
    ] == "runs/proof_body_attempt.lean"
    assert summary["source_theorem_exact_candidate_repair_diagnostics"][0][
        "typeclass_blockers"
    ] == ["HSub ℕ ℝ ENNReal"]
    assert summary["source_theorem_exact_candidate_placeholder_resolution_plan"][
        0
    ]["placeholder_symbol"] == "Exchangeable"
    assert "reviewed exchangeability predicate" in summary[
        "source_theorem_exact_candidate_placeholder_resolution_plan"
    ][0]["replacement_strategy"]
    assert summary["source_theorem_exact_candidate_placeholder_resolution_plan"][
        1
    ]["placeholder_symbol"] == "orderStat"
    assert "order-statistic/quantile primitive" in summary[
        "source_theorem_exact_candidate_placeholder_resolution_plan"
    ][1]["replacement_strategy"]
    assert summary["recommended_source_theorem_integration_action"] == (
        "repair_exact_source_theorem_candidate_formal_environment"
    )
    assert "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED" in prompt
    assert "formal_environment_placeholder_primitives" in prompt
    assert "repair_exact_source_theorem_candidate_formal_environment" in prompt
    assert "source_theorem_exact_candidate_placeholder_resolution_plan" in prompt
    assert "reviewed exchangeability predicate" in prompt
    assert "Exchangeable" in prompt


def test_formalizer_prompt_compacts_large_theory_context() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    prompt = build_formalizer_prompt(
        question=question,
        theory_packet={
            "packet_id": "theory:large",
            "theorem_cards": [
                {
                    "id": f"T{i}",
                    "title": f"Theorem {i}",
                    "statement": "very long theorem statement " + ("x" * 2000),
                    "proof_obligations": ["variance_nonneg"],
                }
                for i in range(20)
            ],
            "lemma_cards": [
                {"id": f"L{i}", "statement": "long lemma " + ("y" * 2000)}
                for i in range(20)
            ],
            "formalization_requests": [
                {"id": f"F{i}", "statement": "long formalization " + ("z" * 2000)}
                for i in range(20)
            ],
            "proof_plan": {"steps": ["oversized proof step " + ("p" * 2000)] * 10},
        },
        simulation_manifest={"manifest_id": "simulation:test", "simulation_passed": True},
        algorithm_manifest={"manifest_id": "algorithm:test", "n_executed": 1},
        registered_problem={"problem_class": "semiparametric", "assumptions": ["bounded outcome"]},
        theorem_goals=[
            {"id": f"G{i}", "title": f"Goal {i}", "proof_obligations": ["variance_nonneg"]}
            for i in range(20)
        ],
        proof_bank_obligation_catalog=[
            {"obligation_id": f"obligation_{i}", "candidate_rank": i}
            for i in range(30)
        ],
    )

    assert "compact_minimal_proof_target_triage" in prompt
    assert "do_not_expand_full_derivations" in prompt
    assert "theory:large" in prompt
    assert "T0" in prompt
    assert "T4" not in prompt
    assert "obligation_0" in prompt
    assert "obligation_12" not in prompt
    assert "x" * 800 not in prompt
    assert len(prompt) < 16000


def test_formalizer_proof_obligation_requests_split_catalog_buckets() -> None:
    selected, off_catalog, rejected = _proof_bank_obligation_request_ids(
        {
            "proof_bank_obligation_requests": [
                {"obligation_id": "variance_nonneg"},
                {"obligation_id": "constant_estimator_unbiased"},
                {"obligation_id": "not_registered_obligation"},
                {"obligation_id": "variance_nonneg"},
            ]
        },
        catalog_ids=("variance_nonneg", "event_indicator_expectation"),
    )

    assert selected == ("variance_nonneg",)
    assert off_catalog == ("constant_estimator_unbiased",)
    assert rejected == ("not_registered_obligation",)


def test_runtime_learning_memory_proof_obligation_requests_split_catalog_buckets() -> None:
    selected, off_catalog, rejected = _runtime_learning_memory_proof_obligation_ids(
        {
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "recommended_proof_obligation_ids": [
                            "variance_nonneg",
                            "constant_estimator_unbiased",
                            "not_registered_obligation",
                            "variance_nonneg",
                        ],
                        "input_summary": {
                            "failed_proof_obligation_ids": ["event_indicator_expectation"],
                        },
                    }
                ],
            }
        },
        catalog_ids=("variance_nonneg", "event_indicator_expectation"),
    )

    assert selected == ("variance_nonneg", "event_indicator_expectation")
    assert off_catalog == ("constant_estimator_unbiased",)
    assert rejected == ("not_registered_obligation",)


def test_runtime_learning_memory_skips_already_kernel_verified_obligations() -> None:
    kernel_verified = _runtime_learning_memory_kernel_verified_proof_obligation_ids(
        {
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": ["variance_nonneg"],
                    }
                ],
            }
        },
        catalog_ids=("variance_nonneg", "event_indicator_expectation"),
    )
    selected, off_catalog, rejected = _runtime_learning_memory_proof_obligation_ids(
        {
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": ["variance_nonneg"],
                        "recommended_proof_obligation_ids": [
                            "variance_nonneg",
                            "event_indicator_expectation",
                        ],
                    }
                ],
            }
        },
        catalog_ids=("variance_nonneg", "event_indicator_expectation"),
    )

    assert kernel_verified == ("variance_nonneg",)
    assert selected == ("event_indicator_expectation",)
    assert off_catalog == ()
    assert rejected == ()


def test_theorem_closure_learning_memory_reroutes_to_upstream_semantics() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]

    summary = _formalizer_proof_bank_runtime_memory_summary(
        context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": verified_ids,
                        "kernel_verified_theorem_reduction_closure_work_order_ids": [
                            "theorem_reduction_closure_work_order:good_rank"
                        ],
                        "kernel_verified_theorem_reduction_closure_target_ids": [
                            "split_conformal_finite_sample_coverage_reduction_closure"
                        ],
                        "kernel_verified_theorem_reduction_closure_goal_ids": [
                            "split_conformal_finite_sample_coverage"
                        ],
                    }
                ],
            },
            "environment_feedback": {
                "high_priority_agenda": [
                    {
                        "id": "formal_gap:theorem_reduction_closure",
                        "owner_subsystem": "Formalizer/LeanProver",
                    }
                ]
            },
        },
        proof_bank_obligation_catalog=catalog,
        theorem_goals=theorem_goals,
        memory_kernel_verified_proof_obligation_ids=tuple(verified_ids),
        memory_prioritized_proof_obligation_ids=(),
    )

    assert summary["proof_bank_bridge_catalog_exhausted_by_memory"] is True
    assert summary["theorem_reduction_closure_already_kernel_verified"] is True
    assert summary["theorem_reduction_closure_required"] is False
    assert summary["recommended_formalizer_target_mode"] == (
        "source_theorem_semantic_primitive_closure"
    )
    assert summary["memory_kernel_verified_theorem_reduction_closure_goal_ids"] == [
        "split_conformal_finite_sample_coverage"
    ]


def test_source_theorem_semantic_primitive_work_orders_follow_verified_closure() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]
    summary = _formalizer_proof_bank_runtime_memory_summary(
        context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": verified_ids,
                        "kernel_verified_theorem_reduction_closure_work_order_ids": [
                            "theorem_reduction_closure_work_order:good_rank"
                        ],
                        "kernel_verified_theorem_reduction_closure_target_ids": [
                            "split_conformal_finite_sample_coverage_reduction_closure"
                        ],
                        "kernel_verified_theorem_reduction_closure_goal_ids": [
                            "split_conformal_finite_sample_coverage"
                        ],
                    }
                ],
            }
        },
        proof_bank_obligation_catalog=catalog,
        theorem_goals=theorem_goals,
        memory_kernel_verified_proof_obligation_ids=tuple(verified_ids),
        memory_prioritized_proof_obligation_ids=(),
    )
    proposal = {
        "packet_id": "formalizer_proposal:source_primitives",
        "formal_targets": [{"id": "split_conformal_finite_sample_coverage_lean"}],
        "gap_taxonomy": [
            {
                "gap": "Lean Exchangeable predicate for finite index families is not tied to uniform-rank semantics.",
                "kind": "formal_primitives",
                "next_owner": "FormalizerProofEngineer",
            },
            {
                "gap": "orderStat lacks a canonical finite-family order-statistic definition.",
                "kind": "formal_primitives",
                "next_owner": "FormalizerProofEngineer",
            },
            {
                "gap": "Reduction closure is not yet assembled into a single Lean proof term.",
                "kind": "source_theorem",
                "next_owner": "AgentRuntime",
            },
        ],
    }

    work_orders = _formalizer_source_theorem_semantic_primitive_work_orders(
        proposal_packet=proposal,
        proof_bank_runtime_memory_summary=summary,
        theorem_goals=theorem_goals,
    )
    promotion_work_orders = _formalizer_source_theorem_promotion_work_orders(
        proposal_packet=proposal,
        proof_bank_runtime_memory_summary=summary,
        theorem_goals=theorem_goals,
    )
    primitive_ids = {row["semantic_primitive_id"] for row in work_orders}

    assert summary["recommended_formalizer_target_mode"] == (
        "source_theorem_semantic_primitive_closure"
    )
    assert "exchangeability_to_uniform_rank_semantics" in primitive_ids
    assert "order_statistic_quantile_semantics" in primitive_ids
    assert len(work_orders) == 2
    assert all(row["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE" for row in work_orders)
    assert all(row["proof_mode"] == "source_theorem_semantic_primitive_closure" for row in work_orders)


def test_source_semantic_learning_memory_advances_beyond_repeat_queue() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]

    summary = _formalizer_proof_bank_runtime_memory_summary(
        context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": verified_ids,
                        "kernel_verified_theorem_reduction_closure_work_order_ids": [
                            "theorem_reduction_closure_work_order:good_rank"
                        ],
                        "kernel_verified_theorem_reduction_closure_target_ids": [
                            "split_conformal_finite_sample_coverage_reduction_closure"
                        ],
                        "kernel_verified_theorem_reduction_closure_goal_ids": [
                            "split_conformal_finite_sample_coverage"
                        ],
                        "kernel_verified_source_theorem_semantic_primitive_ids": [
                            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                            "split_conformal_good_rank_set_inclusion_bridge",
                        ],
                    },
                    {
                        "learning_task": "source_theorem_promotion_bridge_feedback",
                        "input_summary": {
                            "trigger": "SOURCE_THEOREM_PROMOTION_READY_BUT_UNPROVED",
                            "target_theorem_name": "split_conformal_finite_sample_coverage",
                            "artifact_kernel_verified": True,
                            "source_theorem_kernel_verified": False,
                        },
                        "target_behavior": (
                            "consume the READY_FOR_SOURCE_THEOREM_INTEGRATION row"
                        ),
                    }
                ],
            }
        },
        proof_bank_obligation_catalog=catalog,
        theorem_goals=theorem_goals,
        memory_kernel_verified_proof_obligation_ids=tuple(verified_ids),
        memory_prioritized_proof_obligation_ids=(),
    )
    proposal = {
        "packet_id": "formalizer_proposal:source_primitives",
        "formal_targets": [
            {
                "id": "split_conformal_finite_sample_coverage_lean",
                "lean_statement_sketch": (
                    "theorem split_conformal_coverage : True := by trivial"
                ),
                "semantic_alignment_constraints": ["marginal coverage only"],
            }
        ],
        "gap_taxonomy": [
            {
                "gap": "order statistic quantile semantics must be formalized.",
                "kind": "formal_primitives",
                "next_owner": "FormalizerProofEngineer",
            }
        ],
    }
    formalization_manifest = {
        "counts": {"formal_gap": 1},
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "proof_bank_runtime_memory_summary": summary,
        "proof_obligation_control": {
            "theorem_reduction_closure_already_kernel_verified": True,
            "memory_kernel_verified_source_theorem_semantic_primitive_ids": [
                "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                "split_conformal_good_rank_set_inclusion_bridge",
            ],
        },
    }

    work_orders = _formalizer_source_theorem_semantic_primitive_work_orders(
        proposal_packet=proposal,
        proof_bank_runtime_memory_summary=summary,
        theorem_goals=theorem_goals,
    )
    promotion_work_orders = _formalizer_source_theorem_promotion_work_orders(
        proposal_packet=proposal,
        proof_bank_runtime_memory_summary=summary,
        theorem_goals=theorem_goals,
    )
    agenda = _critic_next_action_agenda(
        question=question,
        retrieval_manifest={"counts": {"formal_source_hits": 1}},
        theory_packet={"packet_id": "theory:conformal"},
        simulation_manifest={"simulation_passed": True},
        algorithm_manifest={"n_executed": 1},
        formalization_manifest=formalization_manifest,
    )
    agenda_ids = {row["id"] for row in agenda}

    assert summary["recommended_formalizer_target_mode"] == (
        "source_theorem_exact_semantics_or_theorem_promotion"
    )
    assert summary[
        "source_theorem_semantic_primitive_support_already_kernel_verified"
    ] is True
    assert summary["source_theorem_promotion_ready_but_unproved"] is True
    assert summary[
        "source_theorem_promotion_ready_but_unproved_target_names"
    ] == ["split_conformal_finite_sample_coverage"]
    assert summary["recommended_source_theorem_integration_action"] == (
        "consume_ready_source_theorem_promotion_queue"
    )
    assert work_orders == []
    assert len(promotion_work_orders) == 1
    assert promotion_work_orders[0]["artifact_kind"] == "SourceTheoremPromotionWorkOrder"
    assert promotion_work_orders[0]["proof_evidence_status"] == (
        "WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    assert promotion_work_orders[0][
        "kernel_verified_source_theorem_semantic_primitive_ids"
    ] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    ]
    assert "formal_gap:source_theorem_exact_semantics_or_promotion" in agenda_ids
    assert "formal_gap:source_theorem_semantic_primitives" not in agenda_ids


def test_source_promotion_waits_for_all_placeholder_semantic_support() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]

    def summary_with_semantic_support(
        semantic_support_ids: list[str],
        placeholder_symbols: list[str] | None = None,
    ) -> dict[str, object]:
        if placeholder_symbols is None:
            placeholder_symbols = [
                "MeasureProbability",
                "Exchangeable",
                "orderStatistic",
            ]
        return _formalizer_proof_bank_runtime_memory_summary(
            context={
                "runtime_learning_memory": {
                    "artifact_kind": "RuntimeLearningMemoryContext",
                    "rows": [
                        {
                            "kernel_verified_proof_obligation_ids": verified_ids,
                            "kernel_verified_theorem_reduction_closure_work_order_ids": [
                                "theorem_reduction_closure_work_order:good_rank"
                            ],
                            "kernel_verified_theorem_reduction_closure_target_ids": [
                                "split_conformal_finite_sample_coverage_reduction_closure"
                            ],
                            "kernel_verified_theorem_reduction_closure_goal_ids": [
                                "split_conformal_finite_sample_coverage"
                            ],
                            "kernel_verified_source_theorem_semantic_primitive_ids": (
                                semantic_support_ids
                            ),
                        },
                        {
                            "learning_task": (
                                "source_theorem_exact_candidate_lean_feedback"
                            ),
                            "input_summary": {
                                "trigger": (
                                    "EXACT_SOURCE_PROOF_BODY_ARTIFACT_KERNEL_ENVIRONMENT_OPEN"
                                ),
                                "target_theorem_name": "split_conformal_coverage",
                                "source_theorem_kernel_verified": False,
                                "failure_classification": (
                                    "formal_environment_placeholder_primitives"
                                ),
                                "formal_environment_placeholder_symbols": (
                                    placeholder_symbols
                                ),
                            },
                        },
                    ],
                }
            },
            proof_bank_obligation_catalog=catalog,
            theorem_goals=theorem_goals,
            memory_kernel_verified_proof_obligation_ids=tuple(verified_ids),
            memory_prioritized_proof_obligation_ids=(),
        )

    proposal = {
        "packet_id": "formalizer_proposal:source_promotion",
        "formal_targets": [
            {
                "id": "split_conformal_coverage",
                "lean_statement_sketch": (
                    "theorem split_conformal_coverage : True := by trivial"
                ),
            }
        ],
    }
    partial_summary = summary_with_semantic_support(
        [
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ]
    )
    partial_promotion_work_orders = _formalizer_source_theorem_promotion_work_orders(
        proposal_packet=proposal,
        proof_bank_runtime_memory_summary=partial_summary,
        theorem_goals=theorem_goals,
    )

    assert partial_summary["required_source_theorem_semantic_primitive_support_ids"] == [
        "prob_measure_univ",
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    ]
    assert partial_summary["missing_source_theorem_semantic_primitive_support_ids"] == [
        "prob_measure_univ"
    ]
    assert partial_summary[
        "unresolved_source_theorem_semantic_primitive_placeholder_symbols"
    ] == []
    assert (
        partial_summary[
            "source_theorem_semantic_primitive_support_already_kernel_verified"
        ]
        is False
    )
    assert partial_summary["recommended_formalizer_target_mode"] == (
        "source_theorem_semantic_primitive_closure"
    )
    assert partial_promotion_work_orders == []

    complete_summary = summary_with_semantic_support(
        [
            "prob_measure_univ",
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ]
    )
    complete_promotion_work_orders = _formalizer_source_theorem_promotion_work_orders(
        proposal_packet=proposal,
        proof_bank_runtime_memory_summary=complete_summary,
        theorem_goals=theorem_goals,
    )

    assert complete_summary["missing_source_theorem_semantic_primitive_support_ids"] == []
    assert complete_summary[
        "unresolved_source_theorem_semantic_primitive_placeholder_symbols"
    ] == []
    assert (
        complete_summary[
            "source_theorem_semantic_primitive_support_already_kernel_verified"
        ]
        is True
    )
    assert complete_summary["recommended_formalizer_target_mode"] == (
        "source_theorem_exact_semantics_or_theorem_promotion"
    )
    assert len(complete_promotion_work_orders) == 1
    assert complete_promotion_work_orders[0][
        "kernel_verified_source_theorem_semantic_primitive_ids"
    ] == [
        "prob_measure_univ",
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    ]

    unknown_placeholder_summary = summary_with_semantic_support(
        [
            "prob_measure_univ",
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
        placeholder_symbols=[
            "MeasureProbability",
            "GeneratedUnknownSourcePrimitive",
        ],
    )
    assert unknown_placeholder_summary[
        "missing_source_theorem_semantic_primitive_support_ids"
    ] == []
    assert unknown_placeholder_summary[
        "unresolved_source_theorem_semantic_primitive_placeholder_symbols"
    ] == ["GeneratedUnknownSourcePrimitive"]
    assert (
        unknown_placeholder_summary[
            "source_theorem_semantic_primitive_support_already_kernel_verified"
        ]
        is False
    )
    assert unknown_placeholder_summary["recommended_formalizer_target_mode"] == (
        "source_theorem_semantic_primitive_closure"
    )


def test_source_theorem_integrator_blocker_memory_repairs_exact_target() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]

    summary = _formalizer_proof_bank_runtime_memory_summary(
        context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": verified_ids,
                        "kernel_verified_theorem_reduction_closure_work_order_ids": [
                            "theorem_reduction_closure_work_order:good_rank"
                        ],
                        "kernel_verified_theorem_reduction_closure_target_ids": [
                            "split_conformal_finite_sample_coverage_reduction_closure"
                        ],
                        "kernel_verified_theorem_reduction_closure_goal_ids": [
                            "split_conformal_finite_sample_coverage"
                        ],
                        "kernel_verified_source_theorem_semantic_primitive_ids": [
                            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                            "split_conformal_good_rank_set_inclusion_bridge",
                        ],
                    },
                    {
                        "learning_task": "source_theorem_integrator_blocker_feedback",
                        "input_summary": {
                            "trigger": "SOURCE_THEOREM_INTEGRATION_BLOCKED_ROUTE_PROBE",
                            "integration_status": "BLOCKED_ROUTE_PROBE_ARTIFACT",
                            "target_theorem_name": "split_conformal_finite_sample_coverage",
                            "route_probe_detected": True,
                            "source_theorem_kernel_verified": False,
                        },
                        "target_behavior": (
                            "generate or repair a genuine non-vacuous exact source theorem artifact"
                        ),
                    },
                ],
            }
        },
        proof_bank_obligation_catalog=catalog,
        theorem_goals=theorem_goals,
        memory_kernel_verified_proof_obligation_ids=tuple(verified_ids),
        memory_prioritized_proof_obligation_ids=(),
    )

    assert summary["recommended_formalizer_target_mode"] == (
        "source_theorem_exact_semantics_or_theorem_promotion"
    )
    assert summary["source_theorem_promotion_ready_but_unproved"] is True
    assert summary[
        "source_theorem_promotion_ready_but_unproved_target_names"
    ] == ["split_conformal_finite_sample_coverage"]
    assert summary["source_theorem_integrator_blocked"] is True
    assert summary["source_theorem_integrator_blocked_target_names"] == [
        "split_conformal_finite_sample_coverage"
    ]
    assert summary["source_theorem_integrator_blocker_triggers"] == [
        "SOURCE_THEOREM_INTEGRATION_BLOCKED_ROUTE_PROBE"
    ]
    assert summary["recommended_source_theorem_integration_action"] == (
        "repair_blocked_source_theorem_integration_artifacts"
    )


def test_exact_source_theorem_materializer_sanitizes_sorry_for_live_goal(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "exact_source_queue"
    queue_dir.mkdir()
    artifact_path = tmp_path / "exact_source_candidate.lean"
    transcript_path = tmp_path / "exact_source_candidate.jsonl"
    (
        queue_dir / "formal_verifier_agentic_proof_execution_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "execution_queue_id": "runtime_source_theorem:test",
                        "population_entry_id": "runtime_source_theorem_population:test",
                        "strategy_id": "runtime_source_theorem_promotion_exact_target_attempt",
                        "display_name": "Materialize exact source theorem",
                        "target_theorem_name": "exact_source_claim",
                        "candidate_bridge_lemma_name": "exact_source_claim",
                        "residual_gap": "replace forbidden placeholder with live goal",
                        "population_bucket": "source_theorem_promotion_attempt",
                        "source_theorem_materialization_mode": (
                            "exact_source_theorem_candidate"
                        ),
                        "lean_statement_sketch": (
                            "theorem exact_source_claim\n"
                            "    {Omega : Type*} {claim : Prop} "
                            "(h_claim : claim) : claim := by sorry"
                        ),
                        "kernel_overlay_context": {
                            "source_theorem_target_known": True,
                            "target_location": {
                                "target_lean_declaration": "exact_source_claim",
                                "target_imports": [
                                    "Mathlib",
                                    "StatInference.Conformal",
                                    "Bad;import Unsafe",
                                ],
                            },
                            "already_kernel_verified_subclaims": [
                                "source_semantic_bridge"
                            ],
                            "target_blockers": ["exact source theorem proof body"],
                        },
                        "candidate_artifact_path": str(artifact_path),
                        "execution_transcript_path": str(transcript_path),
                        "proof_state_provider_plan": [
                            "lean_goal",
                            "lean_diagnostic_messages",
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formal_verifier_agentic_proof_execution_materializer(
        queue_dir,
        tmp_path / "exact_source_materializer",
    )

    assert payload["n_exact_source_theorem_candidate_artifacts"] == 1
    assert payload["n_route_probe_artifacts"] == 0
    assert payload["n_live_goal_location_ready"] == 1
    row = payload["rows"][0]
    assert row["ok"] is True
    assert row["materialization_mode"] == "exact_source_theorem_candidate"
    assert row["target_lean_declaration"] == "exact_source_claim"
    source = artifact_path.read_text(encoding="utf-8")
    assert "import Mathlib" in source
    assert "import StatInference.Conformal" in source
    assert "Bad;import Unsafe" not in source
    assert "theorem exact_source_claim" in source
    assert "theorem exact_source_claim {Omega : Type _} {claim : Prop}" in source
    assert "theorem exact_source_claim\n    {Omega : Type*} {claim : Prop}" not in source
    assert "Type*" not in source
    assert "sorry" not in source
    assert "_route_probe" not in source
    assert "route probe" not in source.lower()
    assert "ProofEngineer must fill the exact source-theorem proof body" in source
    assert "fail_if_success trivial" in source
    assert row["live_proof_state_request"]["target_lean_declaration"] == (
        "exact_source_claim"
    )


def test_exact_source_theorem_materializer_infers_mathlib_for_stale_seed_queue(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "exact_source_queue"
    queue_dir.mkdir()
    artifact_path = tmp_path / "exact_source_candidate.lean"
    transcript_path = tmp_path / "exact_source_candidate.jsonl"
    (
        queue_dir / "formal_verifier_agentic_proof_execution_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "execution_queue_id": "runtime_source_theorem:mathlib_infer",
                        "population_entry_id": "runtime_source_theorem_population:mathlib_infer",
                        "strategy_id": "runtime_source_theorem_promotion_exact_target_attempt",
                        "display_name": "Materialize exact source theorem",
                        "target_theorem_name": "exact_source_claim",
                        "candidate_bridge_lemma_name": "exact_source_claim",
                        "residual_gap": "stale seed queue omitted imports",
                        "population_bucket": "source_theorem_promotion_attempt",
                        "source_theorem_materialization_mode": (
                            "exact_source_theorem_candidate"
                        ),
                        "lean_statement_sketch": (
                            "theorem exact_source_claim {Ω : Type _} "
                            "[MeasurableSpace Ω] (P : MeasureTheory.Measure Ω) "
                            "[MeasureTheory.IsProbabilityMeasure P] : True := by "
                            "exact True.intro"
                        ),
                        "kernel_overlay_context": {
                            "source_theorem_target_known": True,
                            "target_location": {
                                "target_lean_declaration": "exact_source_claim",
                                "target_imports": [],
                            },
                        },
                        "candidate_artifact_path": str(artifact_path),
                        "execution_transcript_path": str(transcript_path),
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formal_verifier_agentic_proof_execution_materializer(
        queue_dir,
        tmp_path / "exact_source_materializer",
    )

    assert payload["n_exact_source_theorem_candidate_artifacts"] == 1
    assert payload["rows"][0]["ok"] is True
    source = artifact_path.read_text(encoding="utf-8")
    assert source.startswith("import Mathlib\n\n/-!")
    assert "theorem exact_source_claim" in source
    assert "Type*" not in source
    assert "sorry" not in source


def test_exact_source_theorem_materializer_skips_non_lean_target(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "rocq_source_queue"
    queue_dir.mkdir()
    artifact_path = tmp_path / "rocq_source_candidate.v"
    transcript_path = tmp_path / "rocq_source_candidate.jsonl"
    (
        queue_dir / "formal_verifier_agentic_proof_execution_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "execution_queue_id": "runtime_source_theorem:rocq",
                        "population_entry_id": (
                            "runtime_source_theorem_population:rocq"
                        ),
                        "strategy_id": (
                            "runtime_source_theorem_promotion_exact_target_attempt"
                        ),
                        "display_name": "Materialize Rocq exact source theorem",
                        "target_theorem_name": "split_conformal_coverage",
                        "candidate_bridge_lemma_name": "",
                        "target_prover_family": "rocq",
                        "formal_statement_sketch": (
                            "Theorem split_conformal_coverage : True."
                        ),
                        "formal_imports": ["Coq.Init.Logic"],
                        "residual_gap": "Rocq proof body requires Rocq adapter",
                        "population_bucket": "source_theorem_promotion_attempt",
                        "source_theorem_materialization_mode": (
                            "exact_source_theorem_candidate"
                        ),
                        "kernel_overlay_context": {
                            "source_theorem_target_known": True,
                            "target_location": {
                                "target_prover_family": "rocq",
                                "formal_statement_sketch": (
                                    "Theorem split_conformal_coverage : True."
                                ),
                                "formal_imports": ["Coq.Init.Logic"],
                                "target_lean_declaration": "",
                                "target_imports": [],
                            },
                        },
                        "candidate_artifact_path": str(artifact_path),
                        "execution_transcript_path": str(transcript_path),
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    materializer_dir = tmp_path / "rocq_source_materializer"
    payload = export_formal_verifier_agentic_proof_execution_materializer(
        queue_dir,
        materializer_dir,
    )
    verifier_dir = tmp_path / "rocq_source_artifact_verifier"
    verifier_payload = export_formal_verifier_agentic_proof_execution_artifact_verifier(
        materializer_dir,
        verifier_dir,
        lean_command=("true",),
    )
    promotion_payload = export_formal_verifier_agentic_proof_source_theorem_promotion_queue(
        verifier_dir,
        tmp_path / "rocq_source_promotion_queue",
    )
    integrator_payload = export_formal_verifier_agentic_proof_source_theorem_integrator(
        tmp_path / "rocq_source_promotion_queue",
        tmp_path / "rocq_source_integrator",
        lean_command=("true",),
        local_lean=True,
    )

    assert payload["all_ok"] is True
    assert payload["n_exact_source_theorem_candidate_rows"] == 1
    assert payload["n_exact_source_theorem_candidate_artifacts"] == 0
    assert payload["n_materialized_artifacts"] == 0
    assert payload["n_live_goal_location_ready"] == 0
    assert payload["n_live_proof_state_requests"] == 0
    assert payload["n_unsupported_target_prover_rows"] == 1
    assert payload["by_target_prover_family"] == {"rocq": 1}
    assert payload["by_materialization_status"] == {
        "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_MATERIALIZER": 1
    }
    row = payload["rows"][0]
    assert row["ok"] is True
    assert row["errors"] == ()
    assert row["target_prover_family"] == "rocq"
    assert row["formal_statement_sketch"] == (
        "Theorem split_conformal_coverage : True."
    )
    assert row["formal_imports"] == ("Coq.Init.Logic",)
    assert row["target_lean_declaration"] == ""
    assert row["target_lean_file"] == ""
    assert row["live_goal_location_ready"] is False
    assert row["live_proof_state_request"] == {}
    assert row["source_theorem_target_provenance"][
        "target_prover_family"
    ] == "rocq"
    assert row["source_theorem_target_provenance"][
        "formal_statement_sketch"
    ] == "Theorem split_conformal_coverage : True."
    assert row["source_theorem_target_provenance"]["formal_imports"] == [
        "Coq.Init.Logic"
    ]
    assert not artifact_path.exists()
    assert not transcript_path.exists()

    assert verifier_payload["all_ok"] is True
    assert verifier_payload["n_verifier_rows"] == 1
    assert verifier_payload["n_local_lean_checked"] == 0
    assert verifier_payload["n_artifact_kernel_verified"] == 0
    assert verifier_payload["n_unsupported_target_prover_rows"] == 1
    assert verifier_payload["by_target_prover_family"] == {"rocq": 1}
    assert verifier_payload["by_verification_status"] == {
        "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_ARTIFACT_VERIFIER": 1
    }
    verifier_row = verifier_payload["rows"][0]
    assert verifier_row["ok"] is True
    assert verifier_row["errors"] == ()
    assert verifier_row["target_prover_family"] == "rocq"
    assert verifier_row["formal_statement_sketch"] == (
        "Theorem split_conformal_coverage : True."
    )
    assert verifier_row["formal_imports"] == ("Coq.Init.Logic",)
    assert verifier_row["target_lean_declaration"] == ""
    assert verifier_row["target_lean_line"] == 0
    assert verifier_row["live_proof_state_request_status"] == ""
    assert verifier_row["local_lean_checked"] is False
    assert verifier_row["diagnostics"] == (
        "target_prover_family rocq is not supported by Lean artifact verifier",
    )
    assert verifier_row["source_theorem_target_provenance"][
        "target_prover_family"
    ] == "rocq"

    assert promotion_payload["all_ok"] is True
    assert promotion_payload["n_promotion_rows"] == 1
    assert promotion_payload["n_unsupported_target_prover_rows"] == 1
    assert promotion_payload["by_target_prover_family"] == {"rocq": 1}
    assert promotion_payload["by_promotion_status"] == {
        "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_PROMOTION_QUEUE": 1
    }
    promotion_row = promotion_payload["rows"][0]
    assert promotion_row["ok"] is True
    assert promotion_row["target_prover_family"] == "rocq"
    assert promotion_row["formal_statement_sketch"] == (
        "Theorem split_conformal_coverage : True."
    )
    assert promotion_row["formal_imports"] == ("Coq.Init.Logic",)
    assert promotion_row["target_lean_declaration"] == ""
    assert promotion_row["promotion_status"] == (
        "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_PROMOTION_QUEUE"
    )
    assert promotion_row["action_type"] == (
        "dispatch_source_theorem_to_target_prover_adapter"
    )
    assert promotion_row["required_inputs"] == (
        "target_prover_family",
        "formal_statement_sketch",
        "formal_imports",
        "target_prover_adapter_contract",
    )
    assert promotion_row["evidence_paths"] == ()

    assert integrator_payload["all_ok"] is True
    assert integrator_payload["n_integration_rows"] == 1
    assert integrator_payload["n_local_lean_checked"] == 0
    assert integrator_payload["n_source_theorem_kernel_verified"] == 0
    assert integrator_payload["n_unsupported_target_prover_rows"] == 1
    assert integrator_payload["by_target_prover_family"] == {"rocq": 1}
    assert integrator_payload["by_integration_status"] == {
        "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_INTEGRATOR": 1
    }
    integrator_row = integrator_payload["rows"][0]
    assert integrator_row["ok"] is True
    assert integrator_row["target_prover_family"] == "rocq"
    assert integrator_row["formal_statement_sketch"] == (
        "Theorem split_conformal_coverage : True."
    )
    assert integrator_row["formal_imports"] == ("Coq.Init.Logic",)
    assert integrator_row["integration_status"] == (
        "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_INTEGRATOR"
    )
    assert integrator_row["local_lean_checked"] is False
    assert integrator_row["source_theorem_kernel_verified"] is False
    assert integrator_row["errors"] == ()


def test_source_theorem_exact_candidate_lean_failure_enters_runtime_memory(
    tmp_path: Path,
) -> None:
    verifier_dir = tmp_path / "artifact_verifier"
    verifier_dir.mkdir()
    candidate_path = tmp_path / "exact_source_candidate.lean"
    candidate_path.write_text(
        """
theorem exact_source_claim (claim : Prop) : claim := by
  -- missing proof body
""".strip()
        + "\n",
        encoding="utf-8",
    )
    verifier_manifest = (
        verifier_dir
        / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
    )
    verifier_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "artifact_verification_id": "artifact_verifier:failed_exact",
                        "verification_status": "ARTIFACT_LOCAL_LEAN_FAILED",
                        "target_theorem_name": "exact_source_claim",
                        "target_lean_declaration": "exact_source_claim",
                        "candidate_artifact_path": str(candidate_path),
                        "source_theorem_target_known": True,
                        "local_lean_checked": True,
                        "local_lean_compiled": False,
                        "artifact_kernel_verified": False,
                        "source_theorem_kernel_verified": False,
                        "failure_classification": "proof_body_incomplete",
                        "diagnostics": [
                            "exact_source_candidate.lean:2:2: error: unsolved goals"
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    learning_rows = _runtime_source_theorem_promotion_bridge_learning_rows(
        {"artifact_verifier_manifest": str(verifier_manifest)}
    )

    assert len(learning_rows) == 1
    assert learning_rows[0]["learning_task"] == (
        "source_theorem_exact_candidate_lean_feedback"
    )
    assert learning_rows[0]["input_summary"]["trigger"] == (
        "SOURCE_THEOREM_EXACT_CANDIDATE_LOCAL_LEAN_FAILED"
    )
    assert learning_rows[0]["target_theorem_name"] == "exact_source_claim"
    assert learning_rows[0]["proof_evidence_status"] == (
        "SOURCE_THEOREM_EXACT_CANDIDATE_LEAN_FEEDBACK_NOT_PROOF_EVIDENCE"
    )

    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]
    summary = _formalizer_proof_bank_runtime_memory_summary(
        context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": verified_ids,
                        "kernel_verified_theorem_reduction_closure_work_order_ids": [
                            "theorem_reduction_closure_work_order:good_rank"
                        ],
                        "kernel_verified_theorem_reduction_closure_target_ids": [
                            "split_conformal_finite_sample_coverage_reduction_closure"
                        ],
                        "kernel_verified_theorem_reduction_closure_goal_ids": [
                            "split_conformal_finite_sample_coverage"
                        ],
                        "kernel_verified_source_theorem_semantic_primitive_ids": [
                            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                            "split_conformal_good_rank_set_inclusion_bridge",
                        ],
                    },
                    *learning_rows,
                ],
            }
        },
        proof_bank_obligation_catalog=catalog,
        theorem_goals=theorem_goals,
        memory_kernel_verified_proof_obligation_ids=tuple(verified_ids),
        memory_prioritized_proof_obligation_ids=(),
    )

    assert summary["source_theorem_exact_candidate_requires_repair"] is True
    assert summary["source_theorem_exact_candidate_repair_target_names"] == [
        "exact_source_claim"
    ]
    assert summary["source_theorem_exact_candidate_repair_triggers"] == [
        "SOURCE_THEOREM_EXACT_CANDIDATE_LOCAL_LEAN_FAILED"
    ]
    assert summary["source_theorem_exact_candidate_failure_classifications"] == [
        "proof_body_incomplete"
    ]
    assert summary["source_theorem_exact_candidate_environment_gap"] is False
    assert summary["recommended_source_theorem_integration_action"] == (
        "repair_exact_source_theorem_candidate_proof_body"
    )
    assert "unsolved goals" in summary[
        "source_theorem_exact_candidate_repair_diagnostics"
    ][0]["diagnostics"][0]


def test_source_theorem_exact_candidate_environment_failure_guides_formalizer(
    tmp_path: Path,
) -> None:
    verifier_dir = tmp_path / "artifact_verifier"
    verifier_dir.mkdir()
    candidate_path = tmp_path / "exact_source_candidate.lean"
    candidate_path.write_text(
        "import Missing.StatEnvironment\n\n"
        "theorem exact_source_claim : True := by\n"
        "  exact True.intro\n",
        encoding="utf-8",
    )
    transcript_path = tmp_path / "exact_source_candidate.jsonl"
    materializer_dir = tmp_path / "materializer"
    materializer_dir.mkdir()
    (
        materializer_dir / "formal_verifier_agentic_proof_execution_materializer_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "materialization_id": "materializer:missing_env",
                        "execution_queue_id": "runtime_source_theorem:missing_env",
                        "display_name": "Missing env exact source theorem",
                        "target_theorem_name": "exact_source_claim",
                        "candidate_artifact_path": str(candidate_path),
                        "execution_transcript_path": str(transcript_path),
                        "target_lean_declaration": "exact_source_claim",
                        "target_lean_line": 3,
                        "source_theorem_target_known": True,
                        "live_proof_state_request": {
                            "request_id": "live_goal:missing_env",
                            "provider_preferences": ["lean_lsp_mcp"],
                            "target_lean_file": str(candidate_path),
                            "candidate_artifact_path": str(candidate_path),
                            "target_lean_line": 3,
                            "target_lean_declaration": "exact_source_claim",
                            "mcp_tool_calls": [
                                {"tool": "lean_goal"},
                                {"tool": "lean_diagnostic_messages"},
                            ],
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    verifier_payload = export_formal_verifier_agentic_proof_execution_artifact_verifier(
        materializer_dir,
        verifier_dir,
        lean_timeout=30,
    )
    row = verifier_payload["rows"][0]
    assert row["verification_status"] == "ARTIFACT_LOCAL_LEAN_FAILED"
    assert row["failure_classification"] == "lean_import_environment_missing"
    assert verifier_payload["by_failure_classification"] == {
        "lean_import_environment_missing": 1
    }
    immediate_work_orders = (
        _source_theorem_formal_environment_work_order_rows_from_artifact_verifier_payload(
            verifier_payload,
            artifact_verifier_manifest=str(
                verifier_dir
                / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
            ),
        )
    )
    assert len(immediate_work_orders) == 1
    assert immediate_work_orders[0]["artifact_kind"] == (
        "SourceTheoremFormalEnvironmentWorkOrder"
    )
    assert immediate_work_orders[0]["artifact_verification_id"] == row[
        "artifact_verification_id"
    ]
    assert immediate_work_orders[0]["target_theorem_name"] == "exact_source_claim"
    assert immediate_work_orders[0]["candidate_artifact_path"] == str(candidate_path)
    assert immediate_work_orders[0]["failure_classification"] == (
        "lean_import_environment_missing"
    )
    assert immediate_work_orders[0]["proof_evidence_status"] == (
        "WORK_ORDER_NOT_PROOF_EVIDENCE"
    )

    learning_rows = _runtime_source_theorem_promotion_bridge_learning_rows(
        {
            "artifact_verifier_manifest": str(
                verifier_dir
                / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
            )
        }
    )
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]
    summary = _formalizer_proof_bank_runtime_memory_summary(
        context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": verified_ids,
                        "kernel_verified_theorem_reduction_closure_work_order_ids": [
                            "theorem_reduction_closure_work_order:good_rank"
                        ],
                        "kernel_verified_theorem_reduction_closure_target_ids": [
                            "split_conformal_finite_sample_coverage_reduction_closure"
                        ],
                        "kernel_verified_theorem_reduction_closure_goal_ids": [
                            "split_conformal_finite_sample_coverage"
                        ],
                        "kernel_verified_source_theorem_semantic_primitive_ids": [
                            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                            "split_conformal_good_rank_set_inclusion_bridge",
                        ],
                    },
                    *learning_rows,
                ],
            }
        },
        proof_bank_obligation_catalog=catalog,
        theorem_goals=theorem_goals,
        memory_kernel_verified_proof_obligation_ids=tuple(verified_ids),
        memory_prioritized_proof_obligation_ids=(),
    )

    assert summary["source_theorem_exact_candidate_environment_gap"] is True
    assert summary["source_theorem_exact_candidate_failure_classifications"] == [
        "lean_import_environment_missing"
    ]
    assert summary["recommended_source_theorem_integration_action"] == (
        "repair_exact_source_theorem_candidate_formal_environment"
    )

    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:environment_gap",
        "question": {
            "id": question.id,
            "title": question.title,
        },
        "counts": {"formal_gap": 1, "kernel_verified": 0, "proved": 0},
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "proof_bank_runtime_memory_summary": summary,
    }
    agenda = _critic_next_action_agenda(
        question=question,
        retrieval_manifest={},
        theory_packet={},
        simulation_manifest={"simulation_passed": True},
        algorithm_manifest={},
        formalization_manifest=formalization_manifest,
    )
    assert agenda[0]["id"] == "formal_gap:source_theorem_formal_environment_repair"
    assert agenda[0]["trigger"] == (
        "SOURCE_THEOREM_EXACT_CANDIDATE_FORMAL_ENVIRONMENT_GAP"
    )

    work_orders = _runtime_source_theorem_formal_environment_work_order_rows(
        [{"blackboard": {"artifacts": {"formalization": formalization_manifest}}}]
    )
    assert len(work_orders) == 1
    assert work_orders[0]["artifact_kind"] == (
        "SourceTheoremFormalEnvironmentWorkOrder"
    )
    assert work_orders[0]["action_type"] == (
        "repair_exact_source_theorem_formal_environment"
    )
    assert work_orders[0]["target_theorem_name"] == "exact_source_claim"
    assert work_orders[0]["failure_classification"] == (
        "lean_import_environment_missing"
    )
    assert work_orders[0]["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"


def test_formal_environment_work_order_names_missing_symbols_and_typeclass_blockers() -> None:
    verifier_payload = {
        "rows": [
            {
                "artifact_verification_id": "artifact_verifier:source_env_gap",
                "target_theorem_name": "split_conformal_source_theorem",
                "target_lean_declaration": "split_conformal_source_theorem",
                "source_theorem_target_known": True,
                "source_theorem_target_resolution_id": "target_resolution:split",
                "source_theorem_route_id": "route:split_conformal_source",
                "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
                "source_theorem_statement": (
                    "split conformal source coverage theorem"
                ),
                "source_theorem_lean_file": "StatInference/Conformal/SplitCoverage.lean",
                "semantic_alignment_constraints": [
                    "preserve exact source theorem target"
                ],
                "candidate_artifact_path": "/tmp/split_conformal_source_theorem.lean",
                "source_theorem_kernel_verified": False,
                "failure_classification": "formal_environment_symbol_missing",
                "diagnostics": [
                    "failed to synthesize instance of type class\n  HSub ℕ ℝ ENNReal",
                    "Function expected at\n  Exchangeable\nbut this term has type\n  ?m.1\nHint: The identifier `Exchangeable` is unknown in the current environment.",
                    "Function expected at",
                    "  orderStat",
                    "Hint: The identifier `orderStat` is unknown in the current environment.",
                ],
            }
        ]
    }

    work_orders = _source_theorem_formal_environment_work_order_rows_from_artifact_verifier_payload(
        verifier_payload,
        artifact_verifier_manifest="/tmp/artifact_verifier_manifest.json",
    )

    assert len(work_orders) == 1
    work_order = work_orders[0]
    assert work_order["target_lean_declaration"] == "split_conformal_source_theorem"
    assert work_order["source_theorem_target_known"] is True
    assert work_order["source_theorem_target_provenance"][
        "source_theorem_target_resolution_id"
    ] == "target_resolution:split"
    assert work_order["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert work_order["source_theorem_target_provenance"][
        "source_theorem_statement"
    ] == "split conformal source coverage theorem"
    assert work_order["semantic_alignment_constraints"] == [
        "preserve exact source theorem target"
    ]
    assert work_order["missing_formal_symbols"] == ["Exchangeable", "orderStat"]
    assert work_order["typeclass_blockers"] == ["HSub ℕ ℝ ENNReal"]
    assert any(
        "`Exchangeable`" in task for task in work_order["recommended_repair_tasks"]
    )
    assert any("`orderStat`" in task for task in work_order["recommended_repair_tasks"])
    assert any(
        "`HSub ℕ ℝ ENNReal`" in task
        for task in work_order["recommended_repair_tasks"]
    )
    assert any(
        "runtime-source-theorem-promotion-proofengineer-bridge" in task
        for task in work_order["recommended_repair_tasks"]
    )
    assert work_order["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"


def test_formal_environment_proof_body_executor_learning_rows_enter_runtime_memory(
    tmp_path: Path,
) -> None:
    rows_path = tmp_path / "runtime_learning_rows.jsonl"
    learning_row = {
        "schema_version": 1,
        "learning_task": "exact_source_theorem_proof_body_execution_feedback",
        "target_theorem_name": "split_conformal_source_theorem",
        "execution_queue_id": "exact_source_queue:1",
        "trigger": "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED",
        "input_summary": {
            "failure_classification": "formal_environment_placeholder_primitives",
            "source_theorem_kernel_verified": False,
        },
        "kernel_verified_source_theorem_ids": [],
        "proof_evidence_status": (
            "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
        ),
    }
    rows_path.write_text(json.dumps(learning_row) + "\n", encoding="utf-8")
    executor_manifest = {
        "runtime_learning_export": {
            "runtime_learning_rows_jsonl": str(rows_path),
        }
    }

    rows = _runtime_source_theorem_formal_environment_proof_body_executor_learning_rows(
        executor_manifest
    )

    assert rows == [learning_row]
    assert rows[0]["kernel_verified_source_theorem_ids"] == []
    assert rows[0]["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
    )


def test_proof_body_executor_feedback_exports_formal_environment_work_order() -> None:
    learning_row = {
        "schema_version": 1,
        "learning_task": "exact_source_theorem_proof_body_execution_feedback",
        "target_theorem_name": "split_conformal_source_theorem",
        "target_lean_declaration": "split_conformal_source_theorem",
        "expected_target_lean_declaration": "split_conformal_source_theorem",
        "source_theorem_target_known": True,
        "source_theorem_target_provenance": {
            "source_theorem_route_id": "route:split_conformal_source",
            "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
            "source_theorem_statement": "split conformal source coverage theorem",
            "source_theorem_target_known": True,
            "target_lean_declaration": "split_conformal_source_theorem",
        },
        "semantic_alignment_constraints": [
            "preserve exact source theorem target"
        ],
        "source_work_order_id": "source_theorem_formal_environment_work_order:seed",
        "execution_queue_id": "exact_source_queue:1",
        "execution_result_id": "exact_source_result:1",
        "trigger": "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED",
        "input_summary": {
            "target_theorem_name": "split_conformal_source_theorem",
            "candidate_artifact_path": "runs/proof_body_attempt.lean",
            "source_theorem_kernel_verified": False,
            "failure_classification": "formal_environment_placeholder_primitives",
            "formal_environment_placeholder_symbols": ["Exchangeable", "orderStat"],
            "formal_environment_typeclass_blockers": ["HSub ℕ ℝ ENNReal"],
            "diagnostics": [
                "placeholder primitive still present: Exchangeable",
                "failed to synthesize instance of type class\n  HSub ℕ ℝ ENNReal",
            ],
        },
        "kernel_verified_source_theorem_ids": [],
        "proof_evidence_status": (
            "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
        ),
    }

    work_orders = (
        _runtime_source_theorem_formal_environment_work_order_rows_from_learning_rows(
            [learning_row]
        )
    )

    assert len(work_orders) == 1
    work_order = work_orders[0]
    assert work_order["artifact_kind"] == "SourceTheoremFormalEnvironmentWorkOrder"
    assert work_order["target_theorem_name"] == "split_conformal_source_theorem"
    assert work_order["target_lean_declaration"] == "split_conformal_source_theorem"
    assert work_order["source_theorem_target_known"] is True
    assert work_order["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert work_order["source_theorem_target_provenance"][
        "source_theorem_statement"
    ] == "split conformal source coverage theorem"
    assert work_order["semantic_alignment_constraints"] == [
        "preserve exact source theorem target"
    ]
    assert work_order["candidate_artifact_path"] == "runs/proof_body_attempt.lean"
    assert work_order["failure_classification"] == (
        "formal_environment_placeholder_primitives"
    )
    assert work_order["source_execution_result_id"] == "exact_source_result:1"
    assert work_order["source_execution_queue_id"] == "exact_source_queue:1"
    assert work_order["missing_formal_symbols"] == ["Exchangeable", "orderStat"]
    assert work_order["typeclass_blockers"] == ["HSub ℕ ℝ ENNReal"]
    assert any(
        "`Exchangeable`" in task for task in work_order["recommended_repair_tasks"]
    )
    assert work_order["action_type"] == (
        "repair_exact_source_theorem_formal_environment"
    )
    assert work_order["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"


def test_proof_body_executor_feedback_exports_semantic_primitive_work_orders() -> None:
    learning_row = {
        "schema_version": 1,
        "learning_task": "exact_source_theorem_proof_body_execution_feedback",
        "target_theorem_name": "split_conformal_coverage",
        "source_theorem_target_known": True,
        "source_theorem_target_provenance": {
            "source_theorem_target_known": True,
            "target_lean_declaration": "split_conformal_coverage",
            "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
            "artifact_verification_id": "artifact:split",
        },
        "semantic_alignment_constraints": [
            "preserve marginal coverage target",
        ],
        "source_work_order_id": "source_theorem_formal_environment_work_order:seed",
        "execution_queue_id": "exact_source_queue:1",
        "execution_result_id": "exact_source_result:1",
        "trigger": "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED",
        "input_summary": {
            "target_theorem_name": "split_conformal_coverage",
            "candidate_artifact_path": "runs/split_conformal_coverage_attempt.lean",
            "source_theorem_kernel_verified": False,
            "failure_classification": "formal_environment_placeholder_primitives",
            "formal_environment_placeholder_symbols": [
                "MeasureProbability",
                "Exchangeable",
                "orderStatistic",
            ],
            "formal_environment_typeclass_blockers": ["HSub ℕ ℝ ENNReal"],
            "proof_body_attempted": True,
            "proof_body_attempt_success": False,
            "proof_body_attempt_summaries": [
                "1:assumption:returncode=1:compiled=False"
            ],
            "candidate_live_proof_state_request": {
                "proof_body_goal_excerpt": [
                    "⊢ P {ω | s (Fin.last n₂) ω ≤ q_hat ω} ≥ ENNReal.ofReal (1 - α)"
                ]
            },
            "diagnostics": [
                "candidate artifact still contains placeholder primitive: MeasureProbability",
                "candidate artifact still contains placeholder primitive: Exchangeable",
                "candidate artifact still contains placeholder primitive: orderStatistic",
            ],
        },
        "kernel_verified_source_theorem_ids": [],
        "proof_evidence_status": (
            "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
        ),
    }

    work_orders = (
        _runtime_source_theorem_semantic_primitive_work_order_rows_from_learning_rows(
            [learning_row]
        )
    )

    assert len(work_orders) == 3
    by_symbol = {row["placeholder_symbol"]: row for row in work_orders}
    assert by_symbol["MeasureProbability"]["semantic_primitive_id"] == (
        "probability_measure_semantics"
    )
    assert by_symbol["MeasureProbability"]["candidate_registered_obligation_ids"] == [
        "prob_measure_univ"
    ]
    assert by_symbol["Exchangeable"]["semantic_primitive_id"] == (
        "exchangeability_to_uniform_rank_semantics"
    )
    assert by_symbol["Exchangeable"]["candidate_registered_obligation_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]
    assert by_symbol["Exchangeable"]["source_theorem_target_known"] is True
    assert by_symbol["Exchangeable"]["source_theorem_target_provenance"][
        "source_theorem_goal_id"
    ] == "split_conformal_finite_sample_coverage"
    assert by_symbol["Exchangeable"]["semantic_alignment_constraints"] == [
        "preserve marginal coverage target"
    ]
    assert by_symbol["Exchangeable"]["formal_environment_typeclass_blockers"] == [
        "HSub ℕ ℝ ENNReal"
    ]
    assert by_symbol["Exchangeable"]["proof_body_attempted"] is True
    assert by_symbol["Exchangeable"]["proof_body_attempt_success"] is False
    assert by_symbol["Exchangeable"]["proof_body_attempt_summaries"] == [
        "1:assumption:returncode=1:compiled=False"
    ]
    assert "ENNReal.ofReal" in by_symbol["Exchangeable"]["proof_body_goal_excerpt"][0]
    assert by_symbol["orderStatistic"]["semantic_primitive_id"] == (
        "order_statistic_quantile_semantics"
    )
    assert by_symbol["orderStatistic"]["candidate_registered_obligation_ids"] == [
        "split_conformal_good_rank_set_inclusion_bridge"
    ]
    assert all(
        row["runtime_queue_status"]
        == "PENDING_SOURCE_SEMANTIC_LEAN_PROOF_ATTEMPT"
        for row in work_orders
    )
    assert all(
        row["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"
        for row in work_orders
    )


def test_source_semantic_bridge_learning_rows_enter_runtime_memory(
    tmp_path: Path,
) -> None:
    learning_path = tmp_path / "runtime_learning_rows.jsonl"
    learning_row = {
        "schema_version": 1,
        "question_id": "split_conformal",
        "learning_task": "source_theorem_semantic_primitive_kernel_overlay",
        "input_summary": {
            "source_theorem_semantic_primitive_work_order_ids": [
                "source_theorem_semantic_primitive_work_order:exchangeability",
                "source_theorem_semantic_primitive_work_order:orderstat",
            ],
            "semantic_primitive_ids": [
                "exchangeability_to_uniform_rank_semantics",
                "order_statistic_quantile_semantics",
            ],
            "kernel_verified_source_theorem_semantic_primitive_ids": [
                "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                "split_conformal_good_rank_set_inclusion_bridge",
            ],
            "kernel_verified_source_theorem_semantic_support_obligation_ids": [
                "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                "split_conformal_good_rank_set_inclusion_bridge",
            ],
            "kernel_verified_proof_obligation_ids": [
                "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                "split_conformal_good_rank_set_inclusion_bridge",
            ],
            "proof_audit_manifest": str(tmp_path / "proof_audit_manifest.json"),
            "support_level": "registered_partial_semantic_bridge",
        },
        "source_theorem_semantic_primitive_work_order_ids": [
            "source_theorem_semantic_primitive_work_order:exchangeability",
            "source_theorem_semantic_primitive_work_order:orderstat",
        ],
        "semantic_primitive_ids": [
            "exchangeability_to_uniform_rank_semantics",
            "order_statistic_quantile_semantics",
        ],
        "kernel_verified_source_theorem_semantic_primitive_ids": [
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
        "kernel_verified_source_theorem_semantic_support_obligation_ids": [
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
        "kernel_verified_proof_obligation_ids": [
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
    }
    learning_path.write_text(json.dumps(learning_row) + "\n", encoding="utf-8")

    bridge_rows = _runtime_bridge_learning_rows(
        {"runtime_learning_rows_jsonl": str(learning_path)}
    )
    memory = _load_runtime_learning_memory([learning_path])
    semantic_ids = _runtime_learning_memory_kernel_verified_source_theorem_semantic_primitives(
        {"runtime_learning_memory": memory}
    )

    assert bridge_rows == [learning_row]
    assert memory["counts"]["rows_loaded"] == 1
    assert semantic_ids == (
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    )


def test_post_executor_semantic_learning_exports_source_promotion_work_order() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]
    input_learning_rows = [
        {
            "learning_task": "theorem_reduction_closure_kernel_overlay",
            "kernel_verified_proof_obligation_ids": verified_ids,
            "kernel_verified_theorem_reduction_closure_work_order_ids": [
                "theorem_reduction_closure_work_order:good_rank"
            ],
            "kernel_verified_theorem_reduction_closure_target_ids": [
                "split_conformal_finite_sample_coverage_reduction_closure"
            ],
            "kernel_verified_theorem_reduction_closure_goal_ids": [
                "split_conformal_finite_sample_coverage"
            ],
        },
    ]
    learning_rows = [
        {
            "learning_task": "source_theorem_semantic_primitive_kernel_overlay",
            "kernel_verified_source_theorem_semantic_primitive_ids": [
                "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                "split_conformal_good_rank_set_inclusion_bridge",
            ],
            "kernel_verified_proof_obligation_ids": [
                "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                "split_conformal_good_rank_set_inclusion_bridge",
            ],
        },
    ]
    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:post_executor_source_promotion",
        "question": {
            "id": "conformal_prediction_coverage",
            "title": "Split conformal prediction interval coverage",
        },
        "llm_formalizer_proof_engineer_proposal_id": (
            "formalizer_proposal:post_executor_source_promotion"
        ),
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "registered_proof_bank_obligation_catalog": catalog,
        "proof_bank_runtime_memory_summary": {
            "recommended_formalizer_target_mode": "source_theorem_semantic_primitive_closure",
        },
    }
    proposal = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer_proposal:post_executor_source_promotion",
        "formal_targets": [
            {
                "id": "split_conformal_finite_sample_coverage_lean",
                "informal_source": "split conformal finite-sample coverage",
                "lean_statement_sketch": (
                    "theorem split_conformal_finite_sample_coverage "
                    "(coverage_claim : Prop) (h_coverage : coverage_claim) : "
                    "coverage_claim := by exact h_coverage"
                ),
                "lean_imports": ["Mathlib"],
                "semantic_alignment_constraints": [
                    "exact source theorem must not assume the target"
                ],
            }
        ],
    }

    rows = _runtime_source_theorem_promotion_work_order_rows_from_learning_rows(
        [
            {
                "blackboard": {
                    "artifacts": {
                        formalization_manifest["manifest_id"]: formalization_manifest,
                        proposal["packet_id"]: proposal,
                    }
                }
            }
        ],
        learning_rows,
        architect_context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": input_learning_rows,
                "counts": {"rows_loaded": len(input_learning_rows)},
            }
        },
        source_runtime_learning_task="source_theorem_semantic_primitive_kernel_overlay",
    )

    assert len(rows) == 1
    assert rows[0]["artifact_kind"] == "SourceTheoremPromotionWorkOrder"
    assert rows[0]["same_run_post_executor_promotion"] is True
    assert rows[0]["source_runtime_learning_task"] == (
        "source_theorem_semantic_primitive_kernel_overlay"
    )
    assert rows[0]["kernel_verified_theorem_reduction_closure_target_ids"] == [
        "split_conformal_finite_sample_coverage_reduction_closure"
    ]
    assert rows[0]["kernel_verified_source_theorem_semantic_primitive_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    ]
    assert rows[0][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    ]
    assert rows[0]["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"


def test_post_executor_promotion_waits_for_executor_placeholder_support() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]
    input_learning_rows = [
        {
            "learning_task": "theorem_reduction_closure_kernel_overlay",
            "kernel_verified_proof_obligation_ids": verified_ids,
            "kernel_verified_theorem_reduction_closure_work_order_ids": [
                "theorem_reduction_closure_work_order:good_rank"
            ],
            "kernel_verified_theorem_reduction_closure_target_ids": [
                "split_conformal_finite_sample_coverage_reduction_closure"
            ],
            "kernel_verified_theorem_reduction_closure_goal_ids": [
                "split_conformal_finite_sample_coverage"
            ],
        },
    ]
    executor_feedback = {
        "learning_task": "exact_source_theorem_proof_body_execution_feedback",
        "target_theorem_name": "split_conformal_coverage",
        "source_theorem_kernel_verified": False,
        "input_summary": {
            "trigger": "EXACT_SOURCE_PROOF_BODY_ARTIFACT_KERNEL_ENVIRONMENT_OPEN",
            "target_theorem_name": "split_conformal_coverage",
            "source_theorem_kernel_verified": False,
            "failure_classification": "formal_environment_placeholder_primitives",
            "formal_environment_placeholder_symbols": [
                "MeasureProbability",
                "Exchangeable",
                "orderStatistic",
            ],
        },
    }
    partial_semantic_learning = {
        "learning_task": "source_theorem_semantic_primitive_kernel_overlay",
        "kernel_verified_source_theorem_semantic_primitive_ids": [
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
        "kernel_verified_source_theorem_semantic_support_obligation_ids": [
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
        "kernel_verified_proof_obligation_ids": [
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
    }
    complete_semantic_learning = {
        "learning_task": "source_theorem_semantic_primitive_kernel_overlay",
        "kernel_verified_source_theorem_semantic_primitive_ids": [
            "prob_measure_univ",
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
        "kernel_verified_source_theorem_semantic_support_obligation_ids": [
            "prob_measure_univ",
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
        "kernel_verified_proof_obligation_ids": [
            "prob_measure_univ",
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "split_conformal_good_rank_set_inclusion_bridge",
        ],
    }
    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:post_executor_placeholder_gate",
        "question": {
            "id": "conformal_prediction_coverage",
            "title": "Split conformal prediction interval coverage",
        },
        "llm_formalizer_proof_engineer_proposal_id": (
            "formalizer_proposal:post_executor_placeholder_gate"
        ),
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "registered_proof_bank_obligation_catalog": catalog,
        "proof_bank_runtime_memory_summary": {
            "recommended_formalizer_target_mode": "source_theorem_semantic_primitive_closure",
        },
    }
    proposal = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer_proposal:post_executor_placeholder_gate",
        "formal_targets": [
            {
                "id": "split_conformal_coverage",
                "lean_statement_sketch": (
                    "theorem split_conformal_coverage "
                    "(coverage_claim : Prop) (h_coverage : coverage_claim) : "
                    "coverage_claim := by exact h_coverage"
                ),
                "semantic_alignment_constraints": [
                    "exact source theorem must not assume the target"
                ],
            }
        ],
    }
    results = [
        {
            "blackboard": {
                "artifacts": {
                    formalization_manifest["manifest_id"]: formalization_manifest,
                    proposal["packet_id"]: proposal,
                }
            }
        }
    ]
    architect_context = {
        "runtime_learning_memory": {
            "artifact_kind": "RuntimeLearningMemoryContext",
            "rows": input_learning_rows,
            "counts": {"rows_loaded": len(input_learning_rows)},
        }
    }

    partial_rows = _runtime_source_theorem_promotion_work_order_rows_from_learning_rows(
        results,
        [executor_feedback, partial_semantic_learning],
        architect_context=architect_context,
        source_runtime_learning_task="source_theorem_semantic_primitive_kernel_overlay",
    )
    complete_rows = _runtime_source_theorem_promotion_work_order_rows_from_learning_rows(
        results,
        [executor_feedback, complete_semantic_learning],
        architect_context=architect_context,
        source_runtime_learning_task="source_theorem_semantic_primitive_kernel_overlay",
    )

    assert partial_rows == []
    assert len(complete_rows) == 1
    assert complete_rows[0]["artifact_kind"] == "SourceTheoremPromotionWorkOrder"
    assert complete_rows[0]["same_run_post_executor_promotion"] is True
    assert complete_rows[0][
        "required_source_theorem_semantic_primitive_support_ids"
    ] == [
        "prob_measure_univ",
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    ]
    assert complete_rows[0]["missing_source_theorem_semantic_primitive_support_ids"] == []
    assert complete_rows[0][
        "unresolved_source_theorem_semantic_primitive_placeholder_symbols"
    ] == []
    assert complete_rows[0]["kernel_verified_source_theorem_semantic_primitive_ids"] == [
        "prob_measure_univ",
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    ]
    assert complete_rows[0][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == [
        "prob_measure_univ",
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    ]
    assert complete_rows[0]["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"
    handoff_rows = _runtime_source_theorem_promotion_handoff_rows(complete_rows)
    seed_rows = _runtime_source_theorem_promotion_materialization_seed_rows(
        handoff_rows,
        runtime_out_dir=Path("runs/test_post_executor_placeholder_gate"),
    )
    assert handoff_rows[0][
        "required_source_theorem_semantic_primitive_support_ids"
    ] == complete_rows[0]["required_source_theorem_semantic_primitive_support_ids"]
    assert seed_rows[0][
        "required_source_theorem_semantic_primitive_support_ids"
    ] == complete_rows[0]["required_source_theorem_semantic_primitive_support_ids"]
    assert handoff_rows[0][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == complete_rows[0][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ]
    assert seed_rows[0][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == complete_rows[0][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ]
    assert seed_rows[0]["kernel_overlay_context"][
        "required_source_theorem_semantic_primitive_support_ids"
    ] == complete_rows[0]["required_source_theorem_semantic_primitive_support_ids"]
    assert seed_rows[0]["kernel_overlay_context"][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == complete_rows[0][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ]
    assert seed_rows[0]["kernel_overlay_context"][
        "missing_source_theorem_semantic_primitive_support_ids"
    ] == []
    assert seed_rows[0]["proof_evidence_status"] == (
        "MATERIALIZATION_SEED_NOT_PROOF_EVIDENCE"
    )


def test_source_theorem_promotion_infers_mathlib_import_for_statistical_statement(
    tmp_path: Path,
) -> None:
    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:source_promotion_infer_import",
        "question": {
            "id": "conformal_prediction_coverage",
            "title": "Split conformal prediction interval coverage",
        },
        "llm_formalizer_proof_engineer_proposal_id": (
            "formalizer_proposal:source_promotion_infer_import"
        ),
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "proof_bank_runtime_memory_summary": {
            "recommended_formalizer_target_mode": (
                "source_theorem_exact_semantics_or_theorem_promotion"
            ),
            "source_theorem_semantic_primitive_support_already_kernel_verified": True,
            "remaining_theorem_goal_ids": [
                "split_conformal_finite_sample_coverage"
            ],
            "memory_kernel_verified_theorem_reduction_closure_work_order_ids": [
                "theorem_reduction_closure_work_order:good_rank"
            ],
            "memory_kernel_verified_theorem_reduction_closure_target_ids": [
                "split_conformal_finite_sample_coverage_reduction_closure"
            ],
            "memory_kernel_verified_source_theorem_semantic_primitive_ids": [
                "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                "split_conformal_good_rank_set_inclusion_bridge",
            ],
        },
    }
    proposal = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer_proposal:source_promotion_infer_import",
        "formal_targets": [
            {
                "id": "split_conformal_finite_sample_coverage_lean",
                "informal_source": "split conformal finite-sample coverage",
                "lean_statement_sketch": (
                    "theorem split_conformal_coverage {Ω : Type _} "
                    "[MeasurableSpace Ω] (P : MeasureTheory.Measure Ω) "
                    "[MeasureTheory.IsProbabilityMeasure P] "
                    "(m : ℕ) (hm : 0 < m) : True := by exact True.intro"
                ),
                "lean_imports": [],
                "semantic_alignment_constraints": ["marginal coverage only"],
            }
        ],
    }
    rows = _runtime_source_theorem_promotion_work_order_rows(
        [
            {
                "blackboard": {
                    "artifacts": {
                        "formalization_manifest:source_promotion_infer_import": (
                            formalization_manifest
                        ),
                        "formalizer_proposal:source_promotion_infer_import": proposal,
                    }
                }
            }
        ]
    )
    handoff_rows = _runtime_source_theorem_promotion_handoff_rows(rows)
    materialization_seed_rows = (
        _runtime_source_theorem_promotion_materialization_seed_rows(
            handoff_rows,
            runtime_out_dir=tmp_path,
        )
    )

    assert rows[0]["lean_imports"] == ["Mathlib"]
    assert handoff_rows[0]["lean_imports"] == ["Mathlib"]
    assert materialization_seed_rows[0]["kernel_overlay_context"]["target_location"][
        "target_imports"
    ] == ["Mathlib"]


def test_source_theorem_promotion_preserves_non_lean_formal_target(
    tmp_path: Path,
) -> None:
    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:source_promotion_rocq",
        "question": {
            "id": "rocq_conformal_prediction_coverage",
            "title": "Rocq split conformal prediction interval coverage",
        },
        "llm_formalizer_proof_engineer_proposal_id": (
            "formalizer_proposal:source_promotion_rocq"
        ),
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "proof_bank_runtime_memory_summary": {
            "recommended_formalizer_target_mode": (
                "source_theorem_exact_semantics_or_theorem_promotion"
            ),
            "source_theorem_semantic_primitive_support_already_kernel_verified": True,
            "remaining_theorem_goal_ids": [
                "split_conformal_finite_sample_coverage"
            ],
            "memory_kernel_verified_theorem_reduction_closure_work_order_ids": [
                "theorem_reduction_closure_work_order:rocq_good_rank"
            ],
            "memory_kernel_verified_theorem_reduction_closure_target_ids": [
                "split_conformal_finite_sample_coverage_reduction_closure"
            ],
            "memory_kernel_verified_source_theorem_semantic_primitive_ids": [
                "rocq_split_conformal_rank_uniformity"
            ],
        },
    }
    proposal = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer_proposal:source_promotion_rocq",
        "formal_targets": [
            {
                "id": "split_conformal_finite_sample_coverage_rocq",
                "target_prover_family": "rocq",
                "source_theorem_route_id": "route:split_conformal_rocq_source",
                "source_theorem_statement": (
                    "Rocq split conformal finite-sample coverage source theorem"
                ),
                "formal_statement_sketch": (
                    "Theorem split_conformal_coverage : True."
                ),
                "formal_imports": ["Coq.Init.Logic"],
                "informal_source": "Rocq split conformal finite-sample coverage",
                "semantic_alignment_constraints": ["marginal coverage only"],
            }
        ],
    }

    rows = _runtime_source_theorem_promotion_work_order_rows(
        [
            {
                "blackboard": {
                    "artifacts": {
                        "formalization_manifest:source_promotion_rocq": (
                            formalization_manifest
                        ),
                        "formalizer_proposal:source_promotion_rocq": proposal,
                    }
                }
            }
        ]
    )
    handoff_rows = _runtime_source_theorem_promotion_handoff_rows(rows)
    materialization_seed_rows = (
        _runtime_source_theorem_promotion_materialization_seed_rows(
            handoff_rows,
            runtime_out_dir=tmp_path,
        )
    )

    assert len(rows) == 1
    assert rows[0]["target_prover_family"] == "rocq"
    assert rows[0]["formal_statement_sketch"].startswith(
        "Theorem split_conformal_coverage"
    )
    assert rows[0]["formal_imports"] == ["Coq.Init.Logic"]
    assert rows[0]["lean_statement_sketch"] == ""
    assert rows[0]["lean_imports"] == []
    assert rows[0]["source_theorem_target_known"] is True
    assert rows[0]["source_theorem_target_provenance"][
        "target_prover_family"
    ] == "rocq"
    assert rows[0]["source_theorem_target_provenance"][
        "formal_statement_sketch"
    ].startswith("Theorem split_conformal_coverage")

    assert len(handoff_rows) == 1
    assert handoff_rows[0]["target_prover_family"] == "rocq"
    assert handoff_rows[0]["target_lean_declaration"] == ""
    assert handoff_rows[0]["target_resolution_status"] == (
        "SOURCE_THEOREM_TARGET_SKETCH_PRESENT"
    )
    assert handoff_rows[0]["source_theorem_target_known"] is True
    assert handoff_rows[0]["formal_statement_sketch"] == rows[0][
        "formal_statement_sketch"
    ]
    assert handoff_rows[0]["formal_imports"] == ["Coq.Init.Logic"]
    assert handoff_rows[0]["lean_imports"] == []

    assert len(materialization_seed_rows) == 1
    assert materialization_seed_rows[0]["target_prover_family"] == "rocq"
    assert materialization_seed_rows[0]["source_theorem_target_known"] is True
    assert materialization_seed_rows[0]["candidate_bridge_lemma_name"] == ""
    assert materialization_seed_rows[0]["formal_statement_sketch"] == rows[0][
        "formal_statement_sketch"
    ]
    assert materialization_seed_rows[0]["formal_imports"] == ["Coq.Init.Logic"]
    assert materialization_seed_rows[0]["lean_statement_sketch"] == ""
    assert materialization_seed_rows[0]["materialization_seed_status"] == (
        "BLOCKED_UNSUPPORTED_TARGET_PROVER_FOR_LEAN_MATERIALIZER"
    )
    assert materialization_seed_rows[0]["execution_preflight_status"] == (
        "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_MATERIALIZER"
    )
    target_location = materialization_seed_rows[0]["kernel_overlay_context"][
        "target_location"
    ]
    assert target_location["target_prover_family"] == "rocq"
    assert target_location["formal_statement_sketch"] == rows[0][
        "formal_statement_sketch"
    ]
    assert target_location["formal_imports"] == ["Coq.Init.Logic"]
    assert target_location["target_lean_declaration"] == ""
    assert target_location["target_imports"] == []
    assert materialization_seed_rows[0]["target_location_preflight"][
        "live_goal_requested"
    ] is False


def test_source_theorem_promotion_bridge_exports_formal_environment_work_order(
    tmp_path: Path,
) -> None:
    seed_queue_dir = tmp_path / "source_theorem_seed_queue"
    seed_queue_dir.mkdir()
    candidate_path = tmp_path / "exact_source_candidate.lean"
    transcript_path = tmp_path / "exact_source_candidate.jsonl"
    (
        seed_queue_dir / "formal_verifier_agentic_proof_execution_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "schema_version": 1,
                        "execution_queue_id": "runtime_source_theorem:missing_env",
                        "population_entry_id": "population:missing_env",
                        "display_name": "Missing env exact source theorem",
                        "target_theorem_name": "exact_source_claim",
                        "candidate_bridge_lemma_name": "exact_source_claim",
                        "residual_gap": "source theorem formal environment missing",
                        "population_bucket": "source_theorem_promotion_attempt",
                        "candidate_artifact_path": str(candidate_path),
                        "execution_transcript_path": str(transcript_path),
                        "lean_statement_sketch": (
                            "theorem exact_source_claim : True := by\n"
                            "  exact True.intro"
                        ),
                        "source_theorem_materialization_mode": (
                            "exact_source_theorem_candidate"
                        ),
                        "strategy_id": (
                            "runtime_source_theorem_promotion_exact_target_attempt"
                        ),
                        "kernel_overlay_context": {
                            "source_theorem_target_known": True,
                            "target_location": {
                                "target_imports": ["Missing.StatEnvironment"],
                            },
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    bridge_payload = _run_runtime_source_theorem_promotion_proofengineer_bridge(
        seed_queue_dir=seed_queue_dir,
        out_dir=tmp_path / "runtime_source_theorem_promotion_proofengineer_bridge",
        local_lean=True,
        lean_project=None,
        lean_timeout=30,
    )

    assert bridge_payload["n_materialized_artifacts"] == 1
    assert bridge_payload["n_artifact_kernel_verified"] == 0
    assert bridge_payload["n_source_theorem_kernel_verified"] == 0
    assert bridge_payload["n_source_theorem_formal_environment_work_orders"] == 1
    assert bridge_payload["proof_evidence_status"] == (
        "SOURCE_THEOREM_PROMOTION_PROOFENGINEER_BRIDGE_NOT_SOURCE_THEOREM_PROOF"
    )
    work_orders_path = Path(
        bridge_payload["source_theorem_formal_environment_work_orders_jsonl"]
    )
    work_order_manifest_path = Path(
        bridge_payload["source_theorem_formal_environment_work_order_manifest"]
    )
    assert work_orders_path.exists()
    assert work_order_manifest_path.exists()
    work_orders = [
        json.loads(line)
        for line in work_orders_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(work_orders) == 1
    assert work_orders[0]["artifact_kind"] == (
        "SourceTheoremFormalEnvironmentWorkOrder"
    )
    assert work_orders[0]["action_type"] == (
        "repair_exact_source_theorem_formal_environment"
    )
    assert work_orders[0]["target_theorem_name"] == "exact_source_claim"
    assert work_orders[0]["candidate_artifact_path"] == str(candidate_path)
    assert work_orders[0]["failure_classification"] in {
        "lean_import_environment_missing",
        "lean_project_or_import_environment_missing",
        "lean_syntax_or_import_environment_gap",
    }
    assert work_orders[0]["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"
    (
        formal_env_bridge_manifest,
        proof_body_executor_manifest,
        formal_env_learning_rows,
        proof_body_learning_rows,
    ) = _run_runtime_source_theorem_formal_environment_bridge_stack(
        out_dir=tmp_path
        / "runtime_source_theorem_formal_environment_proofengineer_bridge_from_source_semantic_promotion",
        queue_jsonl=work_orders_path,
        question_id="conformal_prediction_coverage",
        config=ResearchAgentRuntimeConfig(
            source_theorem_formal_environment_proofengineer_bridge=True,
            source_theorem_formal_environment_proofengineer_execute_proof_body=False,
        ),
    )
    assert formal_env_bridge_manifest is not None
    assert proof_body_executor_manifest is None
    assert formal_env_bridge_manifest["n_repair_packets"] == 1
    assert formal_env_bridge_manifest["signature_probes_requested"] is False
    assert formal_env_bridge_manifest["n_proof_body_work_orders"] == 0
    assert formal_env_bridge_manifest["n_proof_body_execution_queue_rows"] == 0
    assert formal_env_bridge_manifest["proof_evidence_status"] == (
        "FORMAL_ENVIRONMENT_REPAIR_PACKETS_NOT_PROOF_EVIDENCE"
    )
    assert formal_env_learning_rows
    assert proof_body_learning_rows == []
    (
        formal_env_bridge_manifest_with_executor_requested,
        proof_body_executor_manifest_with_empty_queue,
        _formal_env_learning_rows_with_executor_requested,
        proof_body_learning_rows_with_empty_queue,
    ) = _run_runtime_source_theorem_formal_environment_bridge_stack(
        out_dir=tmp_path
        / "runtime_source_theorem_formal_environment_proofengineer_bridge_empty_proof_body_queue",
        queue_jsonl=work_orders_path,
        question_id="conformal_prediction_coverage",
        config=ResearchAgentRuntimeConfig(
            source_theorem_formal_environment_proofengineer_bridge=True,
            source_theorem_formal_environment_proofengineer_execute_proof_body=True,
        ),
    )
    assert formal_env_bridge_manifest_with_executor_requested is not None
    assert (
        formal_env_bridge_manifest_with_executor_requested[
            "n_proof_body_execution_queue_rows"
        ]
        == 0
    )
    assert proof_body_executor_manifest_with_empty_queue is None
    assert proof_body_learning_rows_with_empty_queue == []

    cli_out = tmp_path / "runtime_source_theorem_promotion_proofengineer_bridge_cli"
    code = main(
        [
            "runtime-source-theorem-promotion-proofengineer-bridge",
            "--seed-queue-dir",
            str(seed_queue_dir),
            "--out",
            str(cli_out),
            "--lean-timeout",
            "30",
            "--overwrite",
        ]
    )
    assert code == 0
    cli_manifest_path = (
        cli_out / "runtime_source_theorem_promotion_proofengineer_bridge_manifest.json"
    )
    assert cli_manifest_path.exists()
    cli_manifest = json.loads(cli_manifest_path.read_text(encoding="utf-8"))
    assert cli_manifest["overwrite_artifacts"] is True
    assert cli_manifest["n_source_theorem_formal_environment_work_orders"] == 1
    assert Path(
        cli_manifest["source_theorem_formal_environment_work_orders_jsonl"]
    ).exists()
    assert cli_manifest["proof_evidence_status"] == (
        "SOURCE_THEOREM_PROMOTION_PROOFENGINEER_BRIDGE_NOT_SOURCE_THEOREM_PROOF"
    )


def test_runtime_exports_source_theorem_promotion_queue_rows(tmp_path: Path) -> None:
    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:source_promotion",
        "question": {
            "id": "conformal_prediction_coverage",
            "title": "Split conformal prediction interval coverage",
        },
        "llm_formalizer_proof_engineer_proposal_id": "formalizer_proposal:source_promotion",
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "proof_bank_runtime_memory_summary": {
            "recommended_formalizer_target_mode": (
                "source_theorem_exact_semantics_or_theorem_promotion"
            ),
            "source_theorem_semantic_primitive_support_already_kernel_verified": True,
            "remaining_theorem_goal_ids": [
                "split_conformal_finite_sample_coverage"
            ],
            "memory_kernel_verified_theorem_reduction_closure_work_order_ids": [
                "theorem_reduction_closure_work_order:good_rank"
            ],
            "memory_kernel_verified_theorem_reduction_closure_target_ids": [
                "split_conformal_finite_sample_coverage_reduction_closure"
            ],
            "memory_kernel_verified_source_theorem_semantic_primitive_ids": [
                "split_conformal_bad_rank_budget_from_uniform_rank_bound",
                "split_conformal_good_rank_set_inclusion_bridge",
            ],
        },
    }
    proposal = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer_proposal:source_promotion",
        "formal_targets": [
            {
                "id": "split_conformal_finite_sample_coverage_lean",
                "source_theorem_route_id": "route:split_conformal_source",
                "source_theorem_statement": (
                    "split conformal finite-sample coverage source theorem"
                ),
                "source_theorem_lean_file": "StatInference/Conformal.lean",
                "informal_source": "split conformal finite-sample coverage",
                "lean_statement_sketch": (
                    "def qHat (coverage_claim : Prop) : Prop := coverage_claim\n"
                    "theorem split_conformal_coverage (coverage_claim : Prop) "
                    "(h_coverage : coverage_claim) : coverage_claim := by "
                    "exact h_coverage"
                ),
                "lean_imports": ["Mathlib", "StatInference.Conformal"],
                "semantic_alignment_constraints": ["marginal coverage only"],
            }
        ],
    }
    rows = _runtime_source_theorem_promotion_work_order_rows(
        [
            {
                "blackboard": {
                    "artifacts": {
                        "formalization_manifest:source_promotion": formalization_manifest,
                        "formalizer_proposal:source_promotion": proposal,
                    }
                }
            }
        ]
    )
    handoff_rows = _runtime_source_theorem_promotion_handoff_rows(rows)
    materialization_seed_rows = (
        _runtime_source_theorem_promotion_materialization_seed_rows(
            handoff_rows,
            runtime_out_dir=tmp_path,
        )
    )
    materialization_seed_queue_dir = (
        tmp_path / "runtime_source_theorem_promotion_materialization_seed_queue"
    )
    materialization_seed_queue_manifest = (
        _write_runtime_source_theorem_promotion_materialization_seed_queue(
            materialization_seed_rows,
            queue_dir=materialization_seed_queue_dir,
        )
    )
    materializer_payload = export_formal_verifier_agentic_proof_execution_materializer(
        materialization_seed_queue_dir,
        tmp_path / "materialized_source_theorem_promotion_exact_target",
    )
    bridge_payload = _run_runtime_source_theorem_promotion_proofengineer_bridge(
        seed_queue_dir=materialization_seed_queue_dir,
        out_dir=tmp_path / "runtime_source_theorem_promotion_proofengineer_bridge",
        local_lean=False,
        lean_project=None,
        lean_timeout=30,
    )

    assert len(rows) == 1
    assert rows[0]["artifact_kind"] == "SourceTheoremPromotionWorkOrder"
    assert rows[0]["runtime_queue_status"] == (
        "PENDING_SOURCE_THEOREM_TARGET_RESOLUTION_OR_PROMOTION"
    )
    assert rows[0]["question_id"] == "conformal_prediction_coverage"
    assert rows[0]["source_formal_target_id"] == (
        "split_conformal_finite_sample_coverage_lean"
    )
    assert rows[0]["source_theorem_target_known"] is True
    assert rows[0]["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert rows[0]["source_theorem_target_provenance"][
        "source_theorem_statement"
    ] == "split conformal finite-sample coverage source theorem"
    assert rows[0]["source_theorem_target_provenance"][
        "source_theorem_lean_file"
    ] == "StatInference/Conformal.lean"
    assert rows[0]["source_theorem_target_provenance"][
        "target_lean_declaration"
    ] == "split_conformal_coverage"
    assert rows[0]["source_theorem_target_provenance"][
        "semantic_alignment_constraints"
    ] == ["marginal coverage only"]
    assert rows[0]["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"
    assert rows[0]["kernel_verified_theorem_reduction_closure_work_order_ids"] == [
        "theorem_reduction_closure_work_order:good_rank"
    ]
    assert rows[0]["target_prover_family"] == "lean4"
    assert rows[0]["formal_statement_sketch"] == rows[0]["lean_statement_sketch"]
    assert rows[0]["formal_imports"] == ["Mathlib", "StatInference.Conformal"]
    assert rows[0]["lean_imports"] == ["Mathlib", "StatInference.Conformal"]
    assert len(handoff_rows) == 1
    assert handoff_rows[0]["artifact_kind"] == "RuntimeSourceTheoremPromotionHandoff"
    assert handoff_rows[0]["source_theorem_promotion_work_order_id"] == rows[0][
        "work_order_id"
    ]
    assert handoff_rows[0]["target_lean_declaration"] == "split_conformal_coverage"
    assert handoff_rows[0]["target_resolution_status"] == (
        "SOURCE_THEOREM_TARGET_SKETCH_PRESENT"
    )
    assert handoff_rows[0]["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert handoff_rows[0]["source_theorem_target_provenance"][
        "target_lean_declaration"
    ] == "split_conformal_coverage"
    assert handoff_rows[0]["handoff_status"] == (
        "NEEDS_KERNEL_VERIFIED_PROOF_ARTIFACT_BEFORE_PROMOTION"
    )
    assert handoff_rows[0]["downstream_queue_contract"][
        "ready_for_existing_source_theorem_promotion_queue"
    ] is False
    assert handoff_rows[0]["proof_evidence_status"] == "HANDOFF_NOT_PROOF_EVIDENCE"
    assert handoff_rows[0]["target_prover_family"] == "lean4"
    assert handoff_rows[0]["formal_statement_sketch"] == (
        rows[0]["formal_statement_sketch"]
    )
    assert handoff_rows[0]["formal_imports"] == ["Mathlib", "StatInference.Conformal"]
    assert handoff_rows[0]["lean_imports"] == ["Mathlib", "StatInference.Conformal"]
    assert len(materialization_seed_rows) == 1
    assert materialization_seed_rows[0]["artifact_kind"] == (
        "RuntimeSourceTheoremPromotionMaterializationSeed"
    )
    assert materialization_seed_rows[0]["materialization_seed_status"] == (
        "READY_FOR_AGENTIC_PROOF_EXECUTION_MATERIALIZER"
    )
    assert materialization_seed_rows[0]["source_theorem_target_known"] is True
    assert materialization_seed_rows[0]["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert materialization_seed_rows[0]["source_theorem_target_provenance"][
        "target_lean_declaration"
    ] == "split_conformal_coverage"
    assert materialization_seed_rows[0]["kernel_overlay_context"][
        "source_theorem_target_provenance"
    ]["source_theorem_route_id"] == "route:split_conformal_source"
    assert materialization_seed_rows[0]["population_bucket"] == (
        "source_theorem_promotion_attempt"
    )
    assert materialization_seed_rows[0]["strategy_id"] == (
        "runtime_source_theorem_promotion_exact_target_attempt"
    )
    assert materialization_seed_rows[0]["source_theorem_materialization_mode"] == (
        "exact_source_theorem_candidate"
    )
    assert materialization_seed_rows[0]["lean_statement_sketch"] == (
        "def qHat (coverage_claim : Prop) : Prop := coverage_claim\n"
        "theorem split_conformal_coverage (coverage_claim : Prop) "
        "(h_coverage : coverage_claim) : coverage_claim := by exact h_coverage"
    )
    assert materialization_seed_rows[0]["target_prover_family"] == "lean4"
    assert materialization_seed_rows[0]["formal_statement_sketch"] == (
        materialization_seed_rows[0]["lean_statement_sketch"]
    )
    assert materialization_seed_rows[0]["formal_imports"] == [
        "Mathlib",
        "StatInference.Conformal",
    ]
    assert materialization_seed_rows[0]["candidate_bridge_lemma_name"] == (
        "split_conformal_coverage"
    )
    assert materialization_seed_rows[0]["kernel_overlay_context"]["target_location"][
        "target_imports"
    ] == ["Mathlib", "StatInference.Conformal"]
    assert materialization_seed_rows[0]["kernel_overlay_context"]["target_location"][
        "target_prover_family"
    ] == "lean4"
    assert materialization_seed_rows[0]["kernel_overlay_context"]["target_location"][
        "formal_imports"
    ] == ["Mathlib", "StatInference.Conformal"]
    assert materialization_seed_rows[0]["proof_evidence_status"] == (
        "MATERIALIZATION_SEED_NOT_PROOF_EVIDENCE"
    )
    assert materialization_seed_queue_manifest["n_execution_queue_items"] == 1
    assert materialization_seed_queue_manifest["proof_evidence_status"] == (
        "MATERIALIZATION_SEED_QUEUE_NOT_PROOF_EVIDENCE"
    )
    assert materializer_payload["n_materialized_artifacts"] == 1
    assert materializer_payload["n_exact_source_theorem_candidate_artifacts"] == 1
    assert materializer_payload["n_route_probe_artifacts"] == 0
    assert materializer_payload["n_live_goal_location_ready"] == 1
    assert materializer_payload["n_kernel_verified"] == 0
    assert materializer_payload["proof_evidence_status"] == (
        "AGENTIC_PROOF_EXECUTION_MATERIALIZER_NOT_PROOF_EVIDENCE"
    )
    assert materializer_payload["rows"][0]["kernel_verified"] is False
    assert materializer_payload["rows"][0]["materialization_mode"] == (
        "exact_source_theorem_candidate"
    )
    assert materializer_payload["rows"][0]["target_lean_declaration"] == (
        "split_conformal_coverage"
    )
    assert materializer_payload["rows"][0]["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert materializer_payload["rows"][0]["source_theorem_target_provenance"][
        "semantic_alignment_constraints"
    ] == ["marginal coverage only"]
    assert materializer_payload["rows"][0]["live_proof_state_request"][
        "source_theorem_target_provenance"
    ]["source_theorem_route_id"] == "route:split_conformal_source"
    exact_source_text = Path(
        materializer_payload["rows"][0]["candidate_artifact_path"]
    ).read_text(encoding="utf-8")
    assert "import Mathlib" in exact_source_text
    assert "import StatInference.Conformal" in exact_source_text
    assert "theorem split_conformal_coverage" in exact_source_text
    assert "_route_probe" not in exact_source_text
    assert "route probe" not in exact_source_text.lower()
    assert bridge_payload["n_materialized_artifacts"] == 1
    assert bridge_payload["n_artifact_kernel_verified"] == 0
    assert bridge_payload["n_source_theorem_kernel_verified"] == 0
    assert bridge_payload["local_lean_skipped_reason"] == "local_lean_disabled"
    assert bridge_payload["proof_evidence_status"] == (
        "SOURCE_THEOREM_PROMOTION_PROOFENGINEER_BRIDGE_NOT_SOURCE_THEOREM_PROOF"
    )
    assert Path(bridge_payload["materializer_manifest"]).exists()
    assert Path(bridge_payload["bridge_manifest"]).exists()
    assert bridge_payload["n_source_theorem_integration_rows"] == 0
    assert bridge_payload["n_source_theorem_integration_blocked_route_probe"] == 0
    assert _runtime_source_theorem_promotion_bridge_learning_rows(bridge_payload) == []

    materialized_integrator_queue_dir = tmp_path / "materialized_exact_integrator_queue"
    materialized_integrator_queue_dir.mkdir()
    (
        materialized_integrator_queue_dir
        / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "schema_version": 1,
                        "source_theorem_promotion_id": (
                            "source_theorem_promotion:materialized_exact"
                        ),
                        "promotion_status": "READY_FOR_SOURCE_THEOREM_INTEGRATION",
                        "target_theorem_name": "split_conformal_coverage",
                        "candidate_artifact_path": str(
                            materializer_payload["rows"][0]["candidate_artifact_path"]
                        ),
                        "artifact_kernel_verified": True,
                        "source_theorem_target_known": True,
                        "source_theorem_kernel_verified": False,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    materialized_integrator_payload = (
        export_formal_verifier_agentic_proof_source_theorem_integrator(
            materialized_integrator_queue_dir,
            tmp_path / "materialized_exact_source_theorem_integrator",
            local_lean=False,
        )
    )
    assert materialized_integrator_payload["n_ready_for_local_lean"] == 1
    assert materialized_integrator_payload["n_blocked_route_probe"] == 0
    assert materialized_integrator_payload["rows"][0]["integration_status"] == (
        "EXACT_SOURCE_THEOREM_READY_FOR_LOCAL_LEAN"
    )

    ready_queue_dir = (
        tmp_path
        / "runtime_source_theorem_promotion_proofengineer_bridge"
        / "formal_verifier_agentic_proof_source_theorem_promotion_queue"
    )
    ready_queue_dir.mkdir(parents=True)
    ready_row = {
        "schema_version": 1,
        "source_theorem_promotion_id": "source_theorem_promotion:test",
        "question_id": "conformal_prediction_coverage",
        "question_title": "Split conformal prediction interval coverage",
        "promotion_status": "READY_FOR_SOURCE_THEOREM_INTEGRATION",
        "target_theorem_name": "split_conformal_coverage",
        "artifact_kernel_verified": True,
        "source_theorem_kernel_verified": False,
        "source_theorem_target_known": True,
        "source_theorem_target_provenance": {
            "source_theorem_route_id": "route:split_conformal_source",
            "source_theorem_statement": (
                "split conformal finite-sample coverage source theorem"
            ),
            "target_lean_declaration": "split_conformal_coverage",
            "source_theorem_target_known": True,
            "semantic_alignment_constraints": ["marginal coverage only"],
        },
    }
    duplicate_ready_row = {
        **ready_row,
        "source_theorem_promotion_id": "source_theorem_promotion:duplicate",
    }
    (ready_queue_dir / "formal_verifier_agentic_proof_source_theorem_promotion_queue.jsonl").write_text(
        json.dumps(ready_row, sort_keys=True)
        + "\n"
        + json.dumps(duplicate_ready_row, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    ready_bridge_payload = {
        **bridge_payload,
        "source_theorem_promotion_queue_dir": str(ready_queue_dir),
        "source_theorem_promotion_queue_manifest": str(
            ready_queue_dir
            / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json"
        ),
    }
    learning_rows = _runtime_source_theorem_promotion_bridge_learning_rows(
        ready_bridge_payload
    )
    assert len(learning_rows) == 1
    assert learning_rows[0]["learning_task"] == (
        "source_theorem_promotion_bridge_feedback"
    )
    assert learning_rows[0]["input_summary"]["trigger"] == (
        "SOURCE_THEOREM_PROMOTION_READY_BUT_UNPROVED"
    )
    assert learning_rows[0]["target_theorem_name"] == "split_conformal_coverage"
    assert learning_rows[0]["source_theorem_target_known"] is True
    assert learning_rows[0]["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert learning_rows[0]["input_summary"]["source_theorem_target_provenance"][
        "source_theorem_statement"
    ] == "split conformal finite-sample coverage source theorem"
    assert learning_rows[0]["semantic_alignment_constraints"] == [
        "marginal coverage only"
    ]
    assert learning_rows[0]["proof_evidence_status"] == (
        "SOURCE_THEOREM_PROMOTION_BRIDGE_LEARNING_NOT_PROOF_EVIDENCE"
    )

    integrator_queue_dir = tmp_path / "source_theorem_integrator_queue"
    integrator_queue_dir.mkdir()
    route_probe_artifact = tmp_path / "route_probe.lean"
    route_probe_artifact.write_text(
        """
/- This route probe is not theorem proof evidence. -/
theorem split_conformal_finite_sample_coverage_route_probe
    (split_conformal_finite_sample_coverage : True) : True := by
  exact True.intro
""".strip()
        + "\n",
        encoding="utf-8",
    )
    vacuous_exact_artifact = tmp_path / "vacuous_exact_source.lean"
    vacuous_exact_artifact.write_text(
        """
namespace AIStatisticianExactSource

theorem split_conformal_finite_sample_coverage : True := by
  exact True.intro

end AIStatisticianExactSource
""".strip()
        + "\n",
        encoding="utf-8",
    )
    exact_artifact = tmp_path / "exact_source.lean"
    exact_artifact.write_text(
        """
namespace AIStatisticianExactSource

theorem split_conformal_finite_sample_coverage (coverage_claim : Prop)
    (h_coverage : coverage_claim) : coverage_claim := by
  exact h_coverage

end AIStatisticianExactSource
""".strip()
        + "\n",
        encoding="utf-8",
    )
    integrator_rows = [
        {
            **ready_row,
            "source_theorem_promotion_id": "source_theorem_promotion:route_probe",
            "target_theorem_name": "split_conformal_finite_sample_coverage",
            "candidate_artifact_path": str(route_probe_artifact),
        },
        {
            **ready_row,
            "source_theorem_promotion_id": "source_theorem_promotion:vacuous",
            "target_theorem_name": "split_conformal_finite_sample_coverage",
            "candidate_artifact_path": str(vacuous_exact_artifact),
        },
        {
            **ready_row,
            "source_theorem_promotion_id": "source_theorem_promotion:exact",
            "target_theorem_name": "split_conformal_finite_sample_coverage",
            "candidate_artifact_path": str(exact_artifact),
        },
    ]
    (
        integrator_queue_dir
        / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json"
    ).write_text(
        json.dumps({"schema_version": 1, "rows": integrator_rows}, indent=2),
        encoding="utf-8",
    )
    integrator_payload = export_formal_verifier_agentic_proof_source_theorem_integrator(
        integrator_queue_dir,
        tmp_path / "source_theorem_integrator",
        local_lean=False,
    )
    assert integrator_payload["n_integration_rows"] == 3
    assert integrator_payload["n_blocked_route_probe"] == 1
    assert integrator_payload["n_blocked_vacuous_true_target"] == 1
    assert integrator_payload["n_ready_for_local_lean"] == 1
    assert integrator_payload["n_source_theorem_kernel_verified"] == 0
    statuses = {
        row["source_theorem_promotion_id"]: row["integration_status"]
        for row in integrator_payload["rows"]
    }
    assert statuses["source_theorem_promotion:route_probe"] == (
        "BLOCKED_ROUTE_PROBE_ARTIFACT"
    )
    assert statuses["source_theorem_promotion:vacuous"] == (
        "BLOCKED_VACUOUS_TRUE_SOURCE_THEOREM"
    )
    assert statuses["source_theorem_promotion:exact"] == (
        "EXACT_SOURCE_THEOREM_READY_FOR_LOCAL_LEAN"
    )
    assert integrator_payload["proof_evidence_status"] == (
        "SOURCE_THEOREM_INTEGRATOR_NOT_PROOF_EVIDENCE"
    )
    bridge_with_integrator = {
        **ready_bridge_payload,
        "source_theorem_integrator_manifest": str(
            tmp_path
            / "source_theorem_integrator"
            / "formal_verifier_agentic_proof_source_theorem_integrator_manifest.json"
        ),
    }
    integrator_learning_rows = _runtime_source_theorem_promotion_bridge_learning_rows(
        bridge_with_integrator
    )
    assert len(integrator_learning_rows) == 2
    learning_by_target = {
        row["target_theorem_name"]: row for row in integrator_learning_rows
    }
    assert learning_by_target["split_conformal_finite_sample_coverage"][
        "learning_task"
    ] == "source_theorem_integrator_blocker_feedback"
    assert learning_by_target["split_conformal_finite_sample_coverage"][
        "input_summary"
    ]["trigger"] == "SOURCE_THEOREM_INTEGRATION_BLOCKED_ROUTE_PROBE"
    assert "split_conformal_coverage" in learning_by_target


def test_runtime_exports_source_theorem_semantic_primitive_queue_rows() -> None:
    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:source_primitives",
        "question": {
            "id": "conformal_prediction_coverage",
            "title": "Split conformal prediction interval coverage",
        },
        "llm_formalizer_proof_engineer_proposal_id": "formalizer_proposal:source_primitives",
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "proof_bank_runtime_memory_summary": {
            "recommended_formalizer_target_mode": (
                "source_theorem_semantic_primitive_closure"
            ),
            "theorem_reduction_closure_already_kernel_verified": True,
            "remaining_theorem_goal_ids": [
                "split_conformal_finite_sample_coverage"
            ],
            "memory_kernel_verified_theorem_reduction_closure_work_order_ids": [
                "theorem_reduction_closure_work_order:good_rank"
            ],
            "memory_kernel_verified_theorem_reduction_closure_target_ids": [
                "split_conformal_finite_sample_coverage_reduction_closure"
            ],
            "memory_kernel_verified_proof_obligation_ids": [
                "split_conformal_good_rank_coverage_bridge"
            ],
        },
    }
    proposal = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer_proposal:source_primitives",
        "formal_targets": [{"id": "split_conformal_finite_sample_coverage_lean"}],
        "gap_taxonomy": [
            {
                "gap": "order statistic quantile semantics must be formalized for finite calibration scores.",
                "kind": "formal_primitives",
                "next_owner": "FormalizerProofEngineer",
            }
        ],
    }
    rows = _runtime_source_theorem_semantic_primitive_work_order_rows(
        [
            {
                "blackboard": {
                    "artifacts": {
                        "formalization_manifest:source_primitives": formalization_manifest,
                        "formalizer_proposal:source_primitives": proposal,
                    }
                }
            }
        ]
    )

    assert len(rows) == 1
    assert rows[0]["artifact_kind"] == "SourceTheoremSemanticPrimitiveWorkOrder"
    assert rows[0]["question_id"] == "conformal_prediction_coverage"
    assert rows[0]["runtime_queue_status"] == (
        "PENDING_SOURCE_SEMANTIC_LEAN_PROOF_ATTEMPT"
    )
    assert rows[0]["semantic_primitive_id"] == "order_statistic_quantile_semantics"
    assert rows[0]["kernel_verified_theorem_reduction_closure_work_order_ids"] == [
        "theorem_reduction_closure_work_order:good_rank"
    ]


def test_source_theorem_promotion_work_order_prefers_latest_repair_sketch(
    tmp_path: Path,
) -> None:
    base_summary = {
        "recommended_formalizer_target_mode": (
            "source_theorem_exact_semantics_or_theorem_promotion"
        ),
        "source_theorem_semantic_primitive_support_already_kernel_verified": True,
        "remaining_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
        "memory_kernel_verified_theorem_reduction_closure_work_order_ids": [
            "theorem_reduction_closure_work_order:good_rank"
        ],
        "memory_kernel_verified_theorem_reduction_closure_target_ids": [
            "split_conformal_finite_sample_coverage_reduction_closure"
        ],
        "memory_kernel_verified_source_theorem_semantic_primitive_ids": [
            "split_conformal_good_rank_set_inclusion_bridge"
        ],
    }
    old_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:old",
        "question": {"id": "conformal_prediction_coverage"},
        "llm_formalizer_proof_engineer_proposal_id": "formalizer_proposal:old",
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "proof_bank_runtime_memory_summary": base_summary,
    }
    new_manifest = {
        **old_manifest,
        "manifest_id": "formalization_manifest:new",
        "llm_formalizer_proof_engineer_proposal_id": "formalizer_proposal:new",
    }
    old_proposal = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer_proposal:old",
        "formal_targets": [
            {
                "id": "split_conformal_coverage_repair",
                "lean_statement_sketch": "theorem split_conformal_coverage : True := by",
                "informal_source": "old malformed repair sketch",
            }
        ],
    }
    new_sketch = "theorem split_conformal_coverage : True := by\n  trivial"
    new_proposal = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer_proposal:new",
        "formal_targets": [
            {
                "id": "split_conformal_coverage_repair",
                "lean_statement_sketch": new_sketch,
                "informal_source": "new repaired sketch",
                "semantic_alignment_constraints": ["preserve exact source target"],
            }
        ],
    }

    rows = _runtime_source_theorem_promotion_work_order_rows(
        [
            {
                "blackboard": {
                    "artifacts": {
                        "formalization_manifest:old": old_manifest,
                        "formalizer_proposal:old": old_proposal,
                        "formalization_manifest:new": new_manifest,
                        "formalizer_proposal:new": new_proposal,
                    }
                }
            }
        ]
    )
    handoff_rows = _runtime_source_theorem_promotion_handoff_rows(rows)
    materialization_seed_rows = (
        _runtime_source_theorem_promotion_materialization_seed_rows(
            handoff_rows,
            runtime_out_dir=tmp_path,
        )
    )

    assert len(rows) == 1
    assert rows[0]["source_formalizer_packet_id"] == "formalizer_proposal:new"
    assert rows[0]["source_formalization_manifest_id"] == "formalization_manifest:new"
    assert rows[0]["source_formalization_manifest_ids"] == [
        "formalization_manifest:old",
        "formalization_manifest:new",
    ]
    assert rows[0]["source_theorem_promotion_revision_count"] == 2
    assert rows[0]["lean_statement_sketch"] == new_sketch
    assert rows[0]["informal_source"] == "new repaired sketch"
    assert rows[0]["semantic_alignment_constraints"] == [
        "preserve exact source target"
    ]
    assert materialization_seed_rows[0]["source_formalizer_packet_id"] == (
        "formalizer_proposal:new"
    )
    assert materialization_seed_rows[0]["lean_statement_sketch"] == new_sketch


def test_runtime_evidence_summary_preserves_theorem_closure_memory_fields() -> None:
    summary = _runtime_evidence_summary(
        [
            {
                "blackboard": {
                    "artifacts": {
                        "formalization_manifest:test": {
                            "artifact_kind": "RuntimeFormalizationManifest",
                            "counts": {
                                "proved": 0,
                                "kernel_verified": 0,
                                "formal_gap": 1,
                                "failed": 0,
                            },
                            "registered_proof_bank_obligation_catalog": [],
                            "theorem_reduction_closure_work_orders": [],
                            "proof_obligation_control": {
                                "proof_bank_bridge_catalog_exhausted_by_memory": True,
                                "theorem_reduction_closure_required": False,
                                "theorem_reduction_closure_already_kernel_verified": True,
                                "memory_kernel_verified_theorem_reduction_closure_work_order_ids": [
                                    "theorem_reduction_closure_work_order:abc"
                                ],
                                "memory_kernel_verified_theorem_reduction_closure_target_ids": [
                                    "split_conformal_finite_sample_coverage_reduction_closure"
                                ],
                                "memory_kernel_verified_theorem_reduction_closure_goal_ids": [
                                    "split_conformal_finite_sample_coverage"
                                ],
                                "remaining_unverified_proof_bank_obligation_ids": [],
                            },
                        }
                    }
                }
            }
        ]
    )

    control = summary["proof"]["proof_obligation_control"]
    assert control["proof_bank_bridge_catalog_exhausted_by_memory"] is True
    assert control["theorem_reduction_closure_required"] is False
    assert control["theorem_reduction_closure_already_kernel_verified"] is True
    assert control["memory_kernel_verified_theorem_reduction_closure_work_order_ids"] == [
        "theorem_reduction_closure_work_order:abc"
    ]
    assert control["memory_kernel_verified_theorem_reduction_closure_target_ids"] == [
        "split_conformal_finite_sample_coverage_reduction_closure"
    ]
    assert control["memory_kernel_verified_theorem_reduction_closure_goal_ids"] == [
        "split_conformal_finite_sample_coverage"
    ]


def test_formalization_selects_new_source_primitive_after_verified_theorem_closure() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    question_payload = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    already_verified_ids = [
        str(row["obligation_id"])
        for row in catalog
        if str(row["obligation_id"]) != "split_conformal_good_rank_set_inclusion_bridge"
    ]

    class StaticFormalizer:
        def propose(self, **_kwargs: object) -> dict[str, object]:
            packet = dict(_formalizer_sample_response())
            packet.update(
                {
                    "schema_version": 1,
                    "artifact_kind": "FormalizerProofEngineerProposalPacket",
                    "packet_id": "formalizer_proposal:source_primitive_after_closure",
                    "source_agent": "StaticFormalizer",
                    "proof_evidence_status": "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE",
                    "kernel_verified": False,
                    "full_frontier_theorem_proved": False,
                    "proof_bank_obligation_requests": [],
                }
            )
            return packet

    subsystem = FormalizationEvaluatorRuntimeSubsystem(
        proposal_agent=StaticFormalizer(),
        proof_verifier=MockProofVerifier(),
        max_proof_obligations=1,
    )
    blackboard = BlackboardState(
        project_id="test",
        artifacts={
            "theory_packet:test": _runtime_sample_response(),
            "simulation_manifest:test": {"manifest_id": "simulation_manifest:test"},
            "algorithm_sandbox_manifest:test": {"manifest_id": "algorithm_sandbox_manifest:test"},
        },
    )
    task = AgentTask(
        task_id="task:formalization_source_primitive_after_verified_closure",
        owner_subsystem="FormalizationEvaluator",
        objective="test source primitive selection after theorem closure evidence",
        inputs={
            "question": question_payload,
            "architect_context": {
                "runtime_learning_memory": {
                    "artifact_kind": "RuntimeLearningMemoryContext",
                    "rows": [
                        {
                            "kernel_verified_proof_obligation_ids": already_verified_ids,
                            "kernel_verified_theorem_reduction_closure_work_order_ids": [
                                "theorem_reduction_closure_work_order:good_rank"
                            ],
                            "kernel_verified_theorem_reduction_closure_target_ids": [
                                "split_conformal_finite_sample_coverage_reduction_closure"
                            ],
                            "kernel_verified_theorem_reduction_closure_goal_ids": [
                                "split_conformal_finite_sample_coverage"
                            ],
                        }
                    ],
                }
            },
            "theory_packet_id": "theory_packet:test",
            "simulation_manifest_id": "simulation_manifest:test",
            "algorithm_sandbox_manifest_id": "algorithm_sandbox_manifest:test",
        },
    )

    result = subsystem.run(task, blackboard)
    manifest = next(
        row
        for key, row in result.produced_artifacts.items()
        if key.startswith("formalization_manifest:")
    )
    control = manifest["proof_obligation_control"]
    summary = manifest["proof_bank_runtime_memory_summary"]

    assert summary["theorem_reduction_closure_already_kernel_verified"] is True
    assert summary["theorem_reduction_closure_required"] is False
    assert summary["recommended_formalizer_target_mode"] == (
        "source_theorem_semantic_primitive_closure"
    )
    assert summary["remaining_unverified_proof_bank_obligation_ids"] == [
        "split_conformal_good_rank_set_inclusion_bridge"
    ]
    assert control["selected_proof_obligation_ids"] == [
        "split_conformal_good_rank_set_inclusion_bridge"
    ]
    assert manifest["counts"]["kernel_verified"] == 0


def test_formalization_selects_rank_budget_after_good_rank_inclusion_memory() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    question_payload = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    already_verified_ids = [
        str(row["obligation_id"])
        for row in catalog
        if str(row["obligation_id"])
        != "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]

    class StaticFormalizer:
        def propose(self, **_kwargs: object) -> dict[str, object]:
            packet = dict(_formalizer_sample_response())
            packet.update(
                {
                    "schema_version": 1,
                    "artifact_kind": "FormalizerProofEngineerProposalPacket",
                    "packet_id": "formalizer_proposal:rank_budget_after_inclusion",
                    "source_agent": "StaticFormalizer",
                    "proof_evidence_status": "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE",
                    "kernel_verified": False,
                    "full_frontier_theorem_proved": False,
                    "proof_bank_obligation_requests": [],
                }
            )
            return packet

    subsystem = FormalizationEvaluatorRuntimeSubsystem(
        proposal_agent=StaticFormalizer(),
        proof_verifier=MockProofVerifier(),
        max_proof_obligations=1,
    )
    blackboard = BlackboardState(
        project_id="test",
        artifacts={
            "theory_packet:test": _runtime_sample_response(),
            "simulation_manifest:test": {"manifest_id": "simulation_manifest:test"},
            "algorithm_sandbox_manifest:test": {"manifest_id": "algorithm_sandbox_manifest:test"},
        },
    )
    task = AgentTask(
        task_id="task:formalization_rank_budget_after_good_rank_inclusion",
        owner_subsystem="FormalizationEvaluator",
        objective="test rank-budget primitive selection after good-rank inclusion memory",
        inputs={
            "question": question_payload,
            "architect_context": {
                "runtime_learning_memory": {
                    "artifact_kind": "RuntimeLearningMemoryContext",
                    "rows": [
                        {
                            "kernel_verified_proof_obligation_ids": already_verified_ids,
                            "kernel_verified_theorem_reduction_closure_work_order_ids": [
                                "theorem_reduction_closure_work_order:good_rank"
                            ],
                            "kernel_verified_theorem_reduction_closure_target_ids": [
                                "split_conformal_finite_sample_coverage_reduction_closure"
                            ],
                            "kernel_verified_theorem_reduction_closure_goal_ids": [
                                "split_conformal_finite_sample_coverage"
                            ],
                        }
                    ],
                }
            },
            "theory_packet_id": "theory_packet:test",
            "simulation_manifest_id": "simulation_manifest:test",
            "algorithm_sandbox_manifest_id": "algorithm_sandbox_manifest:test",
        },
    )

    result = subsystem.run(task, blackboard)
    manifest = next(
        row
        for key, row in result.produced_artifacts.items()
        if key.startswith("formalization_manifest:")
    )
    control = manifest["proof_obligation_control"]
    summary = manifest["proof_bank_runtime_memory_summary"]

    assert summary["theorem_reduction_closure_already_kernel_verified"] is True
    assert summary["recommended_formalizer_target_mode"] == (
        "source_theorem_semantic_primitive_closure"
    )
    assert summary["remaining_unverified_proof_bank_obligation_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]
    assert control["selected_proof_obligation_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]
    assert manifest["counts"]["kernel_verified"] == 0


def test_formalization_runtime_suppresses_llm_requests_already_kernel_verified_in_memory() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    question_payload = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }

    class StaticFormalizer:
        def propose(self, **_kwargs: object) -> dict[str, object]:
            packet = dict(_formalizer_sample_response())
            packet.update(
                {
                    "schema_version": 1,
                    "artifact_kind": "FormalizerProofEngineerProposalPacket",
                    "packet_id": "formalizer_proposal:memory_suppression",
                    "source_agent": "StaticFormalizer",
                    "proof_evidence_status": "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE",
                    "kernel_verified": False,
                    "full_frontier_theorem_proved": False,
                }
            )
            return packet

    subsystem = FormalizationEvaluatorRuntimeSubsystem(
        proposal_agent=StaticFormalizer(),
        proof_verifier=MockProofVerifier(),
        max_proof_obligations=1,
    )
    blackboard = BlackboardState(
        project_id="test",
        artifacts={
            "theory_packet:test": _runtime_sample_response(),
            "simulation_manifest:test": {"manifest_id": "simulation_manifest:test"},
            "algorithm_sandbox_manifest:test": {"manifest_id": "algorithm_sandbox_manifest:test"},
        },
    )
    task = AgentTask(
        task_id="task:formalization_memory_suppression",
        owner_subsystem="FormalizationEvaluator",
        objective="test proof-obligation memory suppression",
        inputs={
            "question": question_payload,
            "architect_context": {
                "runtime_learning_memory": {
                    "artifact_kind": "RuntimeLearningMemoryContext",
                    "rows": [
                        {
                            "kernel_verified_proof_obligation_ids": ["variance_nonneg"],
                            "recommended_proof_obligation_ids": ["event_indicator_expectation"],
                        }
                    ],
                }
            },
            "theory_packet_id": "theory_packet:test",
            "simulation_manifest_id": "simulation_manifest:test",
            "algorithm_sandbox_manifest_id": "algorithm_sandbox_manifest:test",
        },
    )

    result = subsystem.run(task, blackboard)
    manifest = next(
        row
        for key, row in result.produced_artifacts.items()
        if key.startswith("formalization_manifest:")
    )
    control = manifest["proof_obligation_control"]

    assert control["memory_kernel_verified_proof_obligation_ids"] == ["variance_nonneg"]
    assert control["memory_prioritized_proof_obligation_ids"] == ["event_indicator_expectation"]
    assert control["llm_requested_proof_obligation_ids"] == ["variance_nonneg"]
    assert control["llm_prioritized_proof_obligation_ids"] == []
    assert control["llm_suppressed_kernel_verified_proof_obligation_ids"] == ["variance_nonneg"]
    assert control["excluded_proof_obligation_ids"] == ["variance_nonneg"]
    assert control["excluded_candidate_proof_obligation_ids"] == ["variance_nonneg"]
    assert control["prioritized_proof_obligation_ids"] == ["event_indicator_expectation"]
    assert "variance_nonneg" not in control["eligible_proof_obligation_ids_before_limit"]
    assert control["selected_priority_proof_obligation_ids"] == ["event_indicator_expectation"]
    assert "variance_nonneg" not in control["selected_proof_obligation_ids"]
    assert "variance_nonneg" not in control["deferred_proof_obligation_ids_due_to_max"]


def test_formalization_runtime_exports_theorem_reduction_closure_work_order() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    question_payload = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]

    class StaticClosureFormalizer:
        def propose(self, **_kwargs: object) -> dict[str, object]:
            packet = dict(_formalizer_sample_response())
            packet.update(
                {
                    "schema_version": 1,
                    "artifact_kind": "FormalizerProofEngineerProposalPacket",
                    "packet_id": "formalizer_proposal:closure",
                    "source_agent": "StaticClosureFormalizer",
                    "proof_evidence_status": "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE",
                    "kernel_verified": False,
                    "full_frontier_theorem_proved": False,
                    "formal_targets": [
                        {
                            "id": "split_conformal_finite_sample_coverage_reduction_closure",
                            "informal_source": "connect verified conformal bridge obligations to the frontier theorem",
                            "lean_statement_sketch": "theorem split_conformal_finite_sample_coverage_reduction_closure := by",
                            "semantic_alignment_constraints": ["marginal coverage only"],
                            "expected_status": "OPEN",
                        }
                    ],
                    "proof_bank_obligation_requests": [],
                    "gap_taxonomy": [
                        {
                            "gap": "theorem-level reduction closure still needs Lean proof",
                            "kind": "proof_search",
                            "next_owner": "ProofEngineer/AgentRuntime",
                        }
                    ],
                }
            )
            return packet

    subsystem = FormalizationEvaluatorRuntimeSubsystem(
        proposal_agent=StaticClosureFormalizer(),
        proof_verifier=MockProofVerifier(),
        max_proof_obligations=1,
    )
    blackboard = BlackboardState(
        project_id="test",
        artifacts={
            "theory_packet:test": _runtime_sample_response(),
            "simulation_manifest:test": {"manifest_id": "simulation_manifest:test"},
            "algorithm_sandbox_manifest:test": {"manifest_id": "algorithm_sandbox_manifest:test"},
        },
    )
    task = AgentTask(
        task_id="task:formalization_theorem_closure_work_order",
        owner_subsystem="FormalizationEvaluator",
        objective="test theorem closure work-order export",
        inputs={
            "question": question_payload,
            "architect_context": {
                "runtime_learning_memory": {
                    "artifact_kind": "RuntimeLearningMemoryContext",
                    "rows": [
                        {
                            "kernel_verified_proof_obligation_ids": verified_ids,
                            "recommended_proof_obligation_ids": verified_ids,
                        }
                    ],
                },
                "environment_feedback": {
                    "high_priority_agenda": [
                        {
                            "id": "formal_gap:theorem_reduction_closure",
                            "owner_subsystem": "Formalizer/LeanProver",
                        }
                    ]
                },
            },
            "theory_packet_id": "theory_packet:test",
            "simulation_manifest_id": "simulation_manifest:test",
            "algorithm_sandbox_manifest_id": "algorithm_sandbox_manifest:test",
        },
    )

    result = subsystem.run(task, blackboard)
    manifest = next(
        row
        for key, row in result.produced_artifacts.items()
        if key.startswith("formalization_manifest:")
    )
    control = manifest["proof_obligation_control"]
    work_orders = manifest["theorem_reduction_closure_work_orders"]

    assert control["proof_bank_bridge_catalog_exhausted_by_memory"] is True
    assert control["theorem_reduction_closure_required"] is True
    assert control["n_selected_proof_obligations"] == 0
    assert manifest["counts"]["theorem_reduction_closure_work_orders"] == 1
    assert work_orders[0]["artifact_kind"] == "TheoremReductionClosureWorkOrder"
    assert work_orders[0]["proof_mode"] == "theorem_level_reduction_closure"
    assert work_orders[0]["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"
    assert work_orders[0]["target_theorem_goal_ids"] == ["split_conformal_finite_sample_coverage"]
    assert set(work_orders[0]["verified_bridge_obligation_ids"]) == set(verified_ids)
    queue_rows = _runtime_theorem_reduction_closure_work_order_rows(
        [{"blackboard": {"artifacts": result.produced_artifacts}}]
    )
    assert len(queue_rows) == 1
    assert queue_rows[0]["work_order_id"] == work_orders[0]["work_order_id"]
    assert queue_rows[0]["source_formalization_manifest_id"] == manifest["manifest_id"]
    assert queue_rows[0]["question_id"] == "conformal_prediction_coverage"
    assert queue_rows[0]["runtime_queue_status"] == "PENDING_LEAN_PROOF_ATTEMPT"
    assert "not proof evidence" in queue_rows[0]["runtime_queue_boundary"]


def test_formalization_runtime_uses_deterministic_theorem_closure_when_memory_exhausted() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    question_payload = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]

    class ExplodingFormalizer:
        def propose(self, **_kwargs: object) -> dict[str, object]:
            raise AssertionError("Formalizer should not be called after proof-bank memory is exhausted")

    subsystem = FormalizationEvaluatorRuntimeSubsystem(
        proposal_agent=ExplodingFormalizer(),
        proof_verifier=MockProofVerifier(),
        max_proof_obligations=1,
    )
    blackboard = BlackboardState(
        project_id="test",
        artifacts={
            "theory_packet:test": _runtime_sample_response(),
            "simulation_manifest:test": {"manifest_id": "simulation_manifest:test"},
            "algorithm_sandbox_manifest:test": {"manifest_id": "algorithm_sandbox_manifest:test"},
        },
    )
    task = AgentTask(
        task_id="task:formalization_deterministic_theorem_closure",
        owner_subsystem="FormalizationEvaluator",
        objective="test deterministic theorem closure when proof-bank memory is exhausted",
        inputs={
            "question": question_payload,
            "architect_context": {
                "runtime_learning_memory": {
                    "artifact_kind": "RuntimeLearningMemoryContext",
                    "rows": [
                        {
                            "kernel_verified_proof_obligation_ids": verified_ids,
                            "recommended_proof_obligation_ids": verified_ids,
                        }
                    ],
                },
            },
            "theory_packet_id": "theory_packet:test",
            "simulation_manifest_id": "simulation_manifest:test",
            "algorithm_sandbox_manifest_id": "algorithm_sandbox_manifest:test",
        },
    )

    result = subsystem.run(task, blackboard)
    manifest = next(
        row
        for key, row in result.produced_artifacts.items()
        if key.startswith("formalization_manifest:")
    )
    proposal_id = manifest["llm_formalizer_proof_engineer_proposal_id"]
    proposal = result.produced_artifacts[proposal_id]
    control = manifest["proof_obligation_control"]
    work_orders = manifest["theorem_reduction_closure_work_orders"]
    proposal_evidence = next(
        row
        for row in result.evidence_entries
        if row.artifact_id == proposal_id
    )

    assert proposal["source_agent"] == "DeterministicTheoremClosureWorkOrderSeed"
    assert proposal["provider"] == "deterministic"
    assert proposal["proof_evidence_status"] == (
        "DETERMINISTIC_THEOREM_CLOSURE_PACKET_NOT_PROOF_EVIDENCE"
    )
    assert proposal["proof_bank_obligation_requests"] == []
    assert proposal["formal_targets"][0]["expected_status"] == "KERNEL_CHECK_READY"
    assert "sorry" not in proposal["formal_targets"][0]["lean_statement_sketch"]
    assert "splitConformalFiniteSampleCoverage_reductionClosure" in proposal["formal_targets"][0][
        "lean_statement_sketch"
    ]
    assert "hGoodCovered" in proposal["formal_targets"][0]["lean_statement_sketch"]
    assert "good-rank-containment-to-coverage" in proposal["formal_targets"][0]["lean_statement_sketch"]
    assert "exchangeability, rank-uniformity, and order-statistic construction remain explicit" in proposal[
        "formal_targets"
    ][0]["lean_statement_sketch"]
    assert control["proof_bank_bridge_catalog_exhausted_by_memory"] is True
    assert control["theorem_reduction_closure_required"] is True
    assert control["n_selected_proof_obligations"] == 0
    assert control["selected_proof_obligation_ids"] == []
    assert control["llm_requested_proof_obligation_ids"] == []
    assert work_orders and len(work_orders) == 1
    assert work_orders[0]["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"
    assert work_orders[0]["target_theorem_goal_ids"] == ["split_conformal_finite_sample_coverage"]
    assert set(work_orders[0]["verified_bridge_obligation_ids"]) == set(verified_ids)
    assert proposal_evidence.evidence_type == "deterministic_theorem_closure_work_order_seed"
    assert proposal_evidence.status == "WORK_ORDER_SEED_RECORDED_NOT_PROOF_EVIDENCE"


def test_runtime_optional_theorem_closure_bridge_exports_next_run_memory_without_kernel_claim(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "runtime"
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _procedures, theorem_goals = TheoryPlanner().plan(problem)
    catalog = FormalSubclaimProver().proof_obligation_catalog(problem, theorem_goals)
    verified_ids = [str(row["obligation_id"]) for row in catalog]

    developer = LLMTheoryDeveloperAgent(
        provider=StaticArchitectLLMProvider(_runtime_sample_response()),
        config=ResearchArchitectConfig(provider_name="static", model="static-theory-model"),
    )
    simulation_engineer = LLMSimulationEngineerAgent(
        provider=StaticArchitectLLMProvider(_simulation_sample_response()),
        config=SimulationEngineerConfig(provider_name="static", model="static-simulation-model"),
    )
    algorithm_engineer = LLMAlgorithmEngineerAgent(
        provider=StaticArchitectLLMProvider(_algorithm_sample_response()),
        config=AlgorithmEngineerConfig(provider_name="static", model="static-algorithm-model"),
    )
    formalizer = LLMFormalizerProofEngineerAgent(
        provider=StaticArchitectLLMProvider(_formalizer_sample_response()),
        config=FormalizerConfig(provider_name="static", model="static-formalizer-model"),
    )
    critic_evaluator = LLMCriticEvaluatorAgent(
        provider=StaticArchitectLLMProvider(_critic_sample_response()),
        config=CriticEvaluatorConfig(provider_name="static", model="static-critic-model"),
    )

    manifest = run_research_agent_runtime(
        [question],
        out_dir,
        theory_developer=developer,
        simulation_engineer=simulation_engineer,
        algorithm_engineer=algorithm_engineer,
        formalizer=formalizer,
        critic_evaluator=critic_evaluator,
        proof_state_provider=LocalLeanProofStateFeedbackProvider(lean_command=("true",)),
        architect_context={
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "kernel_verified_proof_obligation_ids": verified_ids,
                        "recommended_proof_obligation_ids": verified_ids,
                    }
                ],
            }
        },
        config=ResearchAgentRuntimeConfig(
            n_runs=40,
            seed=20260528,
            max_iterations=8,
            theorem_closure_proofengineer_bridge=True,
            theorem_closure_proofengineer_local_lean=False,
        ),
    )

    assert manifest["n_runtime_theorem_reduction_closure_work_orders"] == 1
    assert manifest["theorem_closure_proofengineer_bridge_requested"] is True
    assert manifest["theorem_closure_proofengineer_bridge_ran"] is True
    assert manifest["theorem_closure_proofengineer_bridge_runtime_learning_ready"] is False
    assert manifest["theorem_closure_proofengineer_bridge_n_kernel_verified"] == 0
    assert manifest["theorem_closure_proofengineer_bridge_proof_evidence_status"] == (
        "NO_KERNEL_VERIFIED_THEOREM_CLOSURE"
    )
    assert manifest["n_kernel_verified_subclaims"] == 0
    assert "does not retroactively prove the current run" in manifest[
        "theorem_closure_proofengineer_bridge_boundary"
    ]

    bridge_manifest_path = Path(
        manifest["artifacts"][
            "runtime_theorem_reduction_closure_proofengineer_bridge_manifest"
        ]
    )
    learning_path = Path(
        manifest["artifacts"][
            "runtime_theorem_reduction_closure_proofengineer_learning_rows_jsonl"
        ]
    )
    bridge_manifest = json.loads(bridge_manifest_path.read_text(encoding="utf-8"))
    learning_rows = [
        json.loads(line)
        for line in learning_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert bridge_manifest["n_work_orders"] == 1
    assert bridge_manifest["n_kernel_verified"] == 0
    assert bridge_manifest["runtime_learning_ready"] is False
    assert "not proof evidence unless" in bridge_manifest["boundary"]
    assert len(learning_rows) == 1
    assert learning_rows[0]["kernel_verified_theorem_reduction_closure_work_order_ids"] == []
    assert "routing guidance" in learning_rows[0]["boundary"]


def test_runtime_theorem_closure_queue_backfills_prior_formalizer_artifacts() -> None:
    proposal = dict(_formalizer_sample_response())
    proposal.update(
        {
            "artifact_kind": "FormalizerProofEngineerProposalPacket",
            "packet_id": "formalizer_proposal:prior_closure",
            "formal_targets": [
                {
                    "id": "split_conformal_finite_sample_coverage_reduction_closure",
                    "informal_source": "connect verified bridge obligations to frontier theorem",
                    "lean_statement_sketch": "theorem split_conformal_finite_sample_coverage_reduction_closure := by",
                    "semantic_alignment_constraints": ["marginal coverage only"],
                    "expected_status": "OPEN",
                }
            ],
            "proof_bank_obligation_requests": [],
        }
    )
    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:prior",
        "question": {
            "id": "conformal_prediction_coverage",
            "title": "Split conformal prediction interval coverage",
        },
        "llm_formalizer_proof_engineer_proposal_id": proposal["packet_id"],
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage"}
        ],
        "proof_bank_runtime_memory_summary": {
            "theorem_reduction_closure_required": True,
            "recommended_formalizer_target_mode": "theorem_level_reduction_closure",
            "remaining_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
            "memory_kernel_verified_proof_obligation_ids": ["prob_compl"],
            "remaining_unverified_proof_bank_obligation_ids": [],
        },
    }

    rows = _runtime_theorem_reduction_closure_work_order_rows(
        [
            {
                "blackboard": {
                    "artifacts": {
                        str(proposal["packet_id"]): proposal,
                        "formalization_manifest:prior": formalization_manifest,
                    }
                }
            }
        ]
    )

    assert len(rows) == 1
    assert rows[0]["source_formalizer_packet_id"] == proposal["packet_id"]
    assert rows[0]["source_formalization_manifest_id"] == "formalization_manifest:prior"
    assert rows[0]["source_formalization_manifest_ids"] == ["formalization_manifest:prior"]
    assert rows[0]["n_source_formalization_manifests"] == 1
    assert rows[0]["source_formal_target_id"] == "split_conformal_finite_sample_coverage_reduction_closure"
    assert rows[0]["target_theorem_goal_ids"] == ["split_conformal_finite_sample_coverage"]
    assert rows[0]["verified_bridge_obligation_ids"] == ["prob_compl"]
    duplicate_manifest = dict(formalization_manifest)
    duplicate_manifest["manifest_id"] = "formalization_manifest:prior_second_pass"
    duplicate_rows = _runtime_theorem_reduction_closure_work_order_rows(
        [
            {
                "blackboard": {
                    "artifacts": {
                        str(proposal["packet_id"]): proposal,
                        "formalization_manifest:prior": formalization_manifest,
                        "formalization_manifest:prior_second_pass": duplicate_manifest,
                    }
                }
            }
        ]
    )
    assert len(duplicate_rows) == 1
    assert duplicate_rows[0]["source_formalization_manifest_ids"] == [
        "formalization_manifest:prior",
        "formalization_manifest:prior_second_pass",
    ]
    assert duplicate_rows[0]["n_source_formalization_manifests"] == 2


def test_critic_routes_formal_gap_to_theorem_closure_after_proof_bank_exhausted() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:all_kernel_subclaims",
        "counts": {"formal_gap": 1, "kernel_verified": 2, "proved": 2, "failed": 0},
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage", "status": "FORMAL_GAP"}
        ],
        "formal_subclaims": [
            {
                "id": "conformal:prob_compl",
                "claim_type": "lean_obligation",
                "proof_obligation_id": "prob_compl",
                "status": "PROVED",
                "kernel_verified": True,
            },
            {
                "id": "conformal:prob_measure_univ",
                "claim_type": "lean_obligation",
                "proof_obligation_id": "prob_measure_univ",
                "status": "PROVED",
                "kernel_verified": True,
            },
            {
                "id": "conformal:split_conformal_finite_sample_coverage",
                "claim_type": "theorem_goal",
                "status": "FORMAL_GAP",
            },
        ],
        "proof_obligation_control": {
            "candidate_proof_obligation_ids": ["prob_compl", "prob_measure_univ"],
            "selected_proof_obligation_ids": ["prob_compl", "prob_measure_univ"],
            "selected_priority_proof_obligation_ids": [],
            "deferred_proof_obligation_ids_due_to_max": [],
            "deferred_priority_proof_obligation_ids_due_to_max": [],
            "memory_kernel_verified_proof_obligation_ids": ["prob_compl", "prob_measure_univ"],
            "excluded_candidate_proof_obligation_ids": ["prob_compl", "prob_measure_univ"],
            "proof_bank_bridge_catalog_exhausted_by_memory": True,
            "theorem_reduction_closure_required": True,
        },
        "proof_bank_runtime_memory_summary": {
            "proof_bank_bridge_catalog_exhausted_by_memory": True,
            "theorem_reduction_closure_required": True,
            "recommended_formalizer_target_mode": "theorem_level_reduction_closure",
        },
        "theorem_reduction_closure_work_orders": [
            {
                "work_order_id": "theorem_reduction_closure_work_order:test",
                "proof_mode": "theorem_level_reduction_closure",
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            }
        ],
    }
    agenda = _critic_next_action_agenda(
        question=question,
        retrieval_manifest={"counts": {"formal_source_hits": 1}},
        theory_packet={"packet_id": "theory:conformal"},
        simulation_manifest={"simulation_passed": True},
        algorithm_manifest={"n_executed": 0},
        formalization_manifest=formalization_manifest,
    )
    agenda_ids = {row["id"] for row in agenda}
    learning_rows = _critic_learning_rows(
        question=question,
        agenda=agenda,
        retrieval_manifest={"manifest_id": "retrieval:test", "counts": {"formal_source_hits": 1}},
        theory_packet={"packet_id": "theory:conformal", "estimator_specs": []},
        simulation_manifest={"manifest_id": "simulation:test", "simulation_passed": True},
        algorithm_manifest={"manifest_id": "algorithm:test", "n_executed": 0},
        formalization_manifest=formalization_manifest,
    )
    feedback_row = next(
        row for row in learning_rows if row["learning_task"] == "simulation_algorithm_formalization_feedback"
    )

    assert "formal_gap:theorem_reduction_closure" in agenda_ids
    assert "formal_gap:proof_bank_expansion" not in agenda_ids
    assert feedback_row["recommended_proof_obligation_ids"] == []
    assert feedback_row["selected_unverified_proof_obligation_ids"] == []
    assert feedback_row["recommended_formalizer_target_mode"] == "theorem_level_reduction_closure"
    assert feedback_row["theorem_reduction_closure_work_order_ids"] == [
        "theorem_reduction_closure_work_order:test"
    ]
    assert feedback_row["input_summary"]["proof_bank_bridge_catalog_exhausted_by_memory"] is True
    assert feedback_row["input_summary"]["theorem_reduction_closure_required"] is True
    assert feedback_row["input_summary"]["theorem_reduction_closure_work_order_ids"] == [
        "theorem_reduction_closure_work_order:test"
    ]
    assert feedback_row["formal_gap_target_ids"] == ["conformal:split_conformal_finite_sample_coverage"]


def test_critic_routes_to_source_primitives_after_verified_theorem_closure() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    formalization_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization_manifest:verified_closure_remaining_semantics",
        "counts": {"formal_gap": 1, "kernel_verified": 1, "proved": 1, "failed": 0},
        "deterministic_theorem_goals": [
            {"id": "split_conformal_finite_sample_coverage", "status": "FORMAL_GAP"}
        ],
        "formal_subclaims": [
            {
                "id": "conformal:prob_measure_univ",
                "claim_type": "lean_obligation",
                "proof_obligation_id": "prob_measure_univ",
                "status": "PROVED",
                "kernel_verified": True,
            },
            {
                "id": "conformal:split_conformal_finite_sample_coverage",
                "claim_type": "theorem_goal",
                "status": "FORMAL_GAP",
            },
        ],
        "proof_obligation_control": {
            "candidate_proof_obligation_ids": ["prob_measure_univ"],
            "selected_proof_obligation_ids": [],
            "selected_priority_proof_obligation_ids": [],
            "deferred_proof_obligation_ids_due_to_max": [],
            "deferred_priority_proof_obligation_ids_due_to_max": [],
            "memory_kernel_verified_proof_obligation_ids": ["prob_measure_univ"],
            "excluded_candidate_proof_obligation_ids": ["prob_measure_univ"],
            "proof_bank_bridge_catalog_exhausted_by_memory": True,
            "theorem_reduction_closure_required": False,
            "theorem_reduction_closure_already_kernel_verified": True,
            "memory_kernel_verified_theorem_reduction_closure_work_order_ids": [
                "theorem_reduction_closure_work_order:good_rank"
            ],
            "memory_kernel_verified_theorem_reduction_closure_goal_ids": [
                "split_conformal_finite_sample_coverage"
            ],
        },
        "proof_bank_runtime_memory_summary": {
            "proof_bank_bridge_catalog_exhausted_by_memory": True,
            "theorem_reduction_closure_required": False,
            "theorem_reduction_closure_already_kernel_verified": True,
            "recommended_formalizer_target_mode": (
                "source_theorem_semantic_primitive_closure"
            ),
        },
        "theorem_reduction_closure_work_orders": [],
    }

    agenda = _critic_next_action_agenda(
        question=question,
        retrieval_manifest={"counts": {"formal_source_hits": 1}},
        theory_packet={"packet_id": "theory:conformal"},
        simulation_manifest={"simulation_passed": True},
        algorithm_manifest={"n_executed": 1},
        formalization_manifest=formalization_manifest,
    )
    agenda_ids = {row["id"] for row in agenda}

    assert "formal_gap:source_theorem_semantic_primitives" in agenda_ids
    assert "formal_gap:theorem_reduction_closure" not in agenda_ids
    assert "formal_gap:proof_bank_expansion" not in agenda_ids


def test_proof_audit_learning_export_marks_kernel_verified_obligations_as_memory(tmp_path: Path) -> None:
    proof_manifest = tmp_path / "proof_audit_manifest.json"
    proof_manifest.write_text(
        json.dumps(
            {
                "verifier": "local.lake_env_lean",
                "verification_strength": "local_lean_kernel_batch",
                "checks": [
                    {
                        "obligation_id": "finite_conformal_rank_coverage_counting",
                        "kernel_verified": True,
                    },
                    {
                        "obligation_id": "order_statistic_quantile_rule_bridge",
                        "kernel_verified": False,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "learning_export"

    code = main(
        [
            "proof-audit-learning-export",
            "--proof-audit-manifest",
            str(proof_manifest),
            "--question-id",
            "conformal_prediction_coverage",
            "--out",
            str(out_dir),
        ]
    )
    assert code == 0
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    memory = _load_runtime_learning_memory([learning_path])
    assert memory["counts"]["rows_loaded"] == 1
    row = memory["rows"][0]
    assert row["kernel_verified_proof_obligation_ids"] == ["finite_conformal_rank_coverage_counting"]

    selected, off_catalog, rejected = _runtime_learning_memory_proof_obligation_ids(
        {
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    row,
                    {
                        "deferred_priority_proof_obligation_ids_due_to_max": [
                            "finite_conformal_rank_coverage_counting",
                            "order_statistic_quantile_rule_bridge",
                        ]
                    },
                ],
            }
        },
        catalog_ids=(
            "finite_conformal_rank_coverage_counting",
            "order_statistic_quantile_rule_bridge",
        ),
    )

    assert selected == ("order_statistic_quantile_rule_bridge",)
    assert off_catalog == ()
    assert rejected == ()


def test_theorem_reduction_closure_learning_export_keeps_closure_memory_separate(
    tmp_path: Path,
) -> None:
    closure_manifest = tmp_path / "theorem_reduction_closure_work_order_audit_manifest.json"
    closure_manifest.write_text(
        json.dumps(
            {
                "proof_evidence_status": "KERNEL_VERIFIED_THEOREM_CLOSURE_PRESENT",
                "local_lean_project": "/tmp/LeanPractice",
                "local_lean_timeout_seconds": 240,
                "checks": [
                    {
                        "work_order_id": "theorem_reduction_closure_work_order:good_rank",
                        "source_formal_target_id": (
                            "split_conformal_finite_sample_coverage_reduction_closure"
                        ),
                        "target_theorem_goal_ids": [
                            "split_conformal_finite_sample_coverage"
                        ],
                        "verified_bridge_obligation_ids": [
                            "prob_measure_univ",
                            "split_conformal_good_rank_coverage_bridge",
                        ],
                        "kernel_verified": True,
                    },
                    {
                        "work_order_id": "theorem_reduction_closure_work_order:placeholder",
                        "source_formal_target_id": "placeholder",
                        "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
                        "verified_bridge_obligation_ids": ["prob_compl"],
                        "kernel_verified": False,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "closure_learning_export"

    code = main(
        [
            "theorem-reduction-closure-learning-export",
            "--theorem-reduction-closure-audit-manifest",
            str(closure_manifest),
            "--question-id",
            "conformal_prediction_coverage",
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    memory = _load_runtime_learning_memory([learning_path])
    assert memory["counts"]["rows_loaded"] == 1
    row = memory["rows"][0]
    assert row["kernel_verified_theorem_reduction_closure_work_order_ids"] == [
        "theorem_reduction_closure_work_order:good_rank"
    ]
    assert row["kernel_verified_theorem_reduction_closure_target_ids"] == [
        "split_conformal_finite_sample_coverage_reduction_closure"
    ]
    assert row["kernel_verified_theorem_reduction_closure_goal_ids"] == [
        "split_conformal_finite_sample_coverage"
    ]
    assert row["verified_bridge_obligation_ids"] == [
        "prob_measure_univ",
        "split_conformal_good_rank_coverage_bridge",
    ]

    kernel_verified = _runtime_learning_memory_kernel_verified_proof_obligation_ids(
        {
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [row],
            }
        },
        catalog_ids=(
            "prob_measure_univ",
            "split_conformal_good_rank_coverage_bridge",
        ),
    )
    selected, off_catalog, rejected = _runtime_learning_memory_proof_obligation_ids(
        {
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [row],
            }
        },
        catalog_ids=(
            "prob_measure_univ",
            "split_conformal_good_rank_coverage_bridge",
        ),
    )

    assert kernel_verified == ()
    assert selected == ()
    assert off_catalog == ()
    assert rejected == ()

    export_manifest = json.loads(
        (
            out_dir / "theorem_reduction_closure_runtime_learning_export_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        export_manifest["n_kernel_verified_theorem_reduction_closure_work_order_ids"]
        == 1
    )


def _architect_sample_response() -> dict[str, object]:
    return {
        "intake_assessment": {
            "problem_type": "frontier semiparametric causal inference theory",
            "frontier_difficulty": "high",
            "primary_success_criteria": [
                "derive a checkable estimand and estimator proposal",
                "route executable checks through the runtime",
                "preserve Lean/kernel proof boundaries",
            ],
            "known_risks": [
                "conditional exchangeability may be semantically underformalized",
                "simulation diagnostics are empirical rather than theorem evidence",
            ],
        },
        "subsystem_execution_plan": [
            {
                "subsystem": "RetrievalMemory",
                "objective": "collect source, knowledge, and formal-source context",
                "inputs_needed": ["open question", "tags"],
                "expected_artifacts": ["retrieval_memory_manifest"],
                "acceptance_gate": "retrieval context records source boundaries",
            },
            {
                "subsystem": "TheoryDeveloper",
                "objective": "derive estimand, estimator, theorem cards, and proof plan",
                "inputs_needed": ["question", "retrieval_context"],
                "expected_artifacts": ["theory_derivation_packet"],
                "acceptance_gate": "schema-valid proposal with no proof-evidence claim",
            },
            {
                "subsystem": "SimulationEvaluator",
                "objective": "run registered simulation diagnostics after proposal",
                "inputs_needed": ["theory packet", "registered problem"],
                "expected_artifacts": ["simulation_manifest"],
                "acceptance_gate": "runtime records seed, metrics, and empirical boundary",
            },
            {
                "subsystem": "AlgorithmEngineer",
                "objective": "run sandbox prototypes for unregistered estimator specs",
                "inputs_needed": ["implementation gaps", "simulation manifest"],
                "expected_artifacts": ["algorithm_sandbox_manifest"],
                "acceptance_gate": "sandbox prototype records reproducible metrics",
            },
            {
                "subsystem": "FormalizationEvaluator",
                "objective": "separate proof-bank feedback, kernel rows, and formal gaps",
                "inputs_needed": ["theory packet", "simulation manifest"],
                "expected_artifacts": ["formalization_manifest"],
                "acceptance_gate": "kernel count only comes from verifier rows",
            },
            {
                "subsystem": "CriticEvaluator",
                "objective": "audit evidence boundaries and export learning rows",
                "inputs_needed": ["runtime artifacts", "evidence ledger"],
                "expected_artifacts": ["critic_evaluator_manifest", "runtime_learning_rows"],
                "acceptance_gate": "critic agenda preserves proof and execution boundaries",
            },
        ],
        "retrieval_strategy": {
            "paper_queries": ["AIPW semiparametric efficiency cross fitting"],
            "formal_source_queries": ["Slutsky theorem asymptotic normality Lean"],
            "lean_rag_priorities": ["conditional expectation", "asymptotic normality", "positivity"],
        },
        "problem_analysis": {
            "theorem_family": "semiparametric efficiency and asymptotic normality",
            "statistical_objects": ["ATE estimand", "cross-fit AIPW estimator", "nuisance rates"],
            "likely_analogy_classes": ["double machine learning", "one-step estimator CLT"],
            "key_obstacles": ["positivity", "nuisance convergence", "exchangeability bridge"],
            "missing_information": ["source theorem matching nuisance-rate assumptions"],
        },
        "stat_knowledge_bank_plan": {
            "source_families_to_collect": ["DML/AIPW asymptotic normality papers"],
            "assumption_dimensions": ["DGP", "estimand", "asymptotic regime", "positivity"],
            "proof_skeletons_to_track": ["orthogonal decomposition", "empirical process remainder"],
            "failed_attempt_memory_policy": "record assumption mismatches and formal blockers as prompt memory only",
        },
        "literature_fair_comparison_plan": [
            {
                "candidate_source_family": "double machine learning ATE CLT",
                "must_match": ["estimand", "sample splitting", "nuisance rate regime"],
                "likely_mismatches": ["overlap condition strength", "measurability assumptions"],
                "unsafe_transfer_risks": ["borrowing theorem without positivity or Donsker alternative"],
            }
        ],
        "iteration_policy": {
            "reroute_triggers": ["simulation diagnostic failure", "formal gap", "missing algorithm adapter"],
            "max_repair_rounds": 2,
            "stop_conditions": ["critic agenda records remaining gaps", "validator rejects unsafe claim"],
        },
        "evidence_gates": [
            {
                "artifact_kind": "LLM theory packet",
                "required_evidence": "schema validation plus downstream runtime checks",
                "not_evidence": "Lean proof evidence",
            }
        ],
        "risk_register": [
            {
                "risk": "LLM proposal may strengthen assumptions silently",
                "mitigation": "critic and formalizer must surface semantic risks",
                "owner_subsystem": "CriticEvaluator",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "RetrievalMemory",
                "action": "retrieve source and formal context before theory derivation",
                "acceptance_gate": "retrieval manifest is present in blackboard",
            }
        ],
    }


def _runtime_sample_response() -> dict[str, object]:
    return {
        "problem_card": {
            "observed_data": "i.i.d. observations O_i=(X_i,A_i,Y_i)",
            "dgp": "semiparametric observed-data law with binary treatment",
            "estimand": "psi = E[m_1(X)-m_0(X)]",
            "nuisance_quantities": ["m_a(x)", "e(x)"],
            "assumptions": ["consistency", "conditional exchangeability", "positivity"],
            "asymptotic_regime": "n -> infinity with nuisance product-rate control",
            "desired_theorem_type": "asymptotic linearity and normality",
        },
        "theory_derivation_packet": {
            "derivation_summary": "Use Neyman-orthogonal AIPW score for the ATE.",
            "derivation_steps": [
                {
                    "id": "orthogonal_score",
                    "claim": "AIPW score has first-order insensitivity to nuisance error.",
                    "equation_or_argument": "phi = m1-m0 + A/e(Y-m1) - (1-A)/(1-e)(Y-m0) - psi",
                    "depends_on": ["identification"],
                    "risk": "positivity and integrability are required",
                }
            ],
            "self_critique": ["The proposed cross-fit estimator still needs an AlgorithmEngineer adapter."],
            "rejected_alternatives": [
                {"name": "IPW only", "reason": "unstable under near-positivity violations"}
            ],
        },
        "estimator_specs": [
            {
                "id": "crossfit_aipw",
                "name": "cross-fitted AIPW",
                "formula": "P_n phi_hat + psi_hat",
                "algorithm_sketch": "fit nuisances on folds and evaluate held-out scores",
                "tuning": ["number of folds"],
                "required_assumptions": ["positivity", "product-rate nuisance convergence"],
            },
            {
                "id": "generated_bias_probe",
                "name": "generated deterministic bias probe",
                "formula": "controlled deterministic Monte Carlo summary",
                "algorithm_sketch": "use an AgentRuntime-vetted generated Python sandbox draft",
                "tuning": ["replicates"],
                "required_assumptions": ["finite deterministic summary metrics"],
            }
        ],
        "theorem_cards": [
            {
                "id": "aipw_asymptotic_normality",
                "informal_statement": "Under consistency, exchangeability, positivity, and nuisance rates, cross-fitted AIPW is asymptotically normal.",
                "assumptions_used": ["consistency", "exchangeability", "positivity"],
                "conclusion": "sqrt(n)(psi_hat-psi) -> N(0, Var(phi))",
                "rate_or_limit_law": "root-n CLT",
                "proof_strategy": "show influence-function expansion plus negligible second-order remainder",
                "semantic_risks": ["formalizing conditional exchangeability faithfully"],
            }
        ],
        "lemma_cards": [
            {
                "id": "second_order_remainder_bound",
                "statement": "The product of nuisance errors bounds the AIPW remainder.",
                "depends_on": ["orthogonal_score"],
                "used_by": ["aipw_asymptotic_normality"],
                "formalization_difficulty": "high",
            }
        ],
        "proof_plan": {
            "proof_dependency_dag": [
                {"from": "second_order_remainder_bound", "to": "aipw_asymptotic_normality"}
            ],
            "required_primitives": ["conditional_expectation", "slutsky_theorem"],
            "acceptable_strengthening": ["bounded outcomes for first Lean target"],
            "unacceptable_changes": ["replace conditional exchangeability with randomized treatment"],
        },
        "formalization_requests": [
            {
                "id": "lean_aipw_asymptotic_normality",
                "target_theorem_card": "aipw_asymptotic_normality",
                "lean_statement_sketch": "theorem aipw_asymptotic_normality ...",
                "semantic_alignment_constraints": ["do not drop nuisance remainder"],
                "kernel_status": "OPEN",
            }
        ],
        "simulation_ademp_spec": {
            "aim": "stress AIPW coverage under nuisance misspecification",
            "dgps": ["well-overlapped", "near-positivity violation"],
            "methods": ["crossfit_aipw", "ipw_only"],
            "performance_measures": ["bias", "rmse", "coverage_95"],
            "stress_tests": ["propensity scores close to zero"],
            "expected_theoretical_behavior": ["coverage approaches nominal under overlap"],
        },
        "critic_findings": [
            {
                "critic": "runtime_critic",
                "finding": "crossfit_aipw needs executable implementation before simulation can judge that exact estimator",
                "reroute_if_confirmed": "AlgorithmEngineer",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "AlgorithmEngineer",
                "action": "implement crossfit_aipw adapter",
                "acceptance_gate": "reproducible simulation manifest",
            }
        ],
    }


def _algorithm_sample_response() -> dict[str, object]:
    return {
        "implementation_targets": [
            {
                "estimator_id": "crossfit_aipw",
                "adapter_strategy": "Use the registered crossfit_aipw sandbox template for a binary-treatment ATE prototype.",
                "registered_template_hint": "crossfit_aipw",
                "data_contract": [
                    "observed columns X, A, Y",
                    "binary treatment with overlap diagnostics",
                    "fold assignments for held-out nuisance predictions",
                ],
                "validation_metrics": ["bias", "rmse", "coverage_95", "n_success"],
                "risk_controls": ["clip propensity scores", "report near-positivity stress behavior"],
            },
            {
                "estimator_id": "generated_bias_probe",
                "adapter_strategy": "Use a generated Python draft only after AgentRuntime static safety checks.",
                "registered_template_hint": "none",
                "data_contract": ["seed", "replicates"],
                "validation_metrics": ["mean_bias_probe", "rmse", "n_runs"],
                "risk_controls": ["no imports", "bounded deterministic arithmetic", "sandbox-only output"],
            }
        ],
        "sandbox_plan": {
            "prototype_steps": [
                "instantiate the crossfit AIPW runtime template",
                "run repeated Monte Carlo simulations",
                "record coverage and RMSE diagnostics",
            ],
            "stress_tests": ["near positivity violation", "nuisance misspecification"],
            "expected_outputs": ["simulation metrics JSON", "prototype status row"],
            "expected_failure_modes": ["coverage below target when overlap is weak"],
        },
        "code_generation_plan": {
            "files_to_generate": ["sandbox prototype only", "generated draft for generated_bias_probe"],
            "functions_to_implement": ["fit nuisances", "compute AIPW score", "run_sandbox"],
            "dependencies": ["numpy for registered template", "math for generated draft"],
            "runtime_executor": "AgentRuntime",
        },
        "sandbox_code_drafts": [
            {
                "estimator_id": "generated_bias_probe",
                "language": "python",
                "entrypoint": "run_sandbox",
                "code": (
                    "def run_sandbox(seed: int, replicates: int) -> dict:\n"
                    "    n = max(5, int(replicates))\n"
                    "    total = 0.0\n"
                    "    sq_total = 0.0\n"
                    "    for i in range(n):\n"
                    "        value = float(((int(seed) + i * 17) % 101)) / 100.0 - 0.5\n"
                    "        total = total + value\n"
                    "        sq_total = sq_total + value * value\n"
                    "    mean = total / float(n)\n"
                    "    variance = sq_total / float(n) - mean * mean\n"
                    "    if variance < 0.0:\n"
                    "        variance = 0.0\n"
                    "    return {\n"
                    "        'status': 'ok',\n"
                    "        'n_runs': n,\n"
                    "        'mean_bias_probe': mean,\n"
                    "        'rmse': math.sqrt(variance + mean * mean),\n"
                    "        'sandbox_failed': False,\n"
                    "    }\n"
                ),
                "intended_metrics": ["mean_bias_probe", "rmse", "n_runs"],
                "safety_notes": ["no imports", "no filesystem access", "AgentRuntime executes if static guard passes"],
            }
        ],
        "promotion_gate": {
            "required_tests": ["sandbox smoke passes", "registered algorithm audit passes"],
            "required_reproducibility_evidence": ["fixed seed", "recorded metrics", "artifact hash"],
            "production_registration_requirements": ["registry entry", "focused simulation rerun"],
        },
        "critic_findings": [
            {
                "critic": "implementation_critic",
                "finding": "The prototype must remain sandbox-only until promoted through registry tests.",
                "reroute_if_confirmed": "AlgorithmEngineer",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "AgentRuntime",
                "action": "execute registered crossfit_aipw sandbox template",
                "acceptance_gate": "reproducible sandbox metrics recorded",
            }
        ],
    }


def _conformal_algorithm_sample_response() -> dict[str, object]:
    return {
        "implementation_targets": [
            {
                "estimator_id": "E1",
                "adapter_strategy": "Use the registered split_conformal_interval sandbox template.",
                "registered_template_hint": "split_conformal_interval",
                "data_contract": [
                    "exchangeable regression observations",
                    "train/calibration/test split",
                    "residual quantile interval output",
                ],
                "validation_metrics": ["coverage_90", "mean_interval_width", "n_success"],
                "risk_controls": [
                    "record marginal-only coverage boundary",
                    "stress nonlinear and heavy-tail DGPs",
                ],
            }
        ],
        "sandbox_plan": {
            "prototype_steps": ["execute trusted split conformal template"],
            "stress_tests": ["linear", "nonlinear", "heavy-tailed"],
            "expected_outputs": ["coverage_90", "mean_interval_width"],
            "expected_failure_modes": ["coverage below nominal under non-exchangeable shift"],
        },
        "code_generation_plan": {
            "files_to_generate": [],
            "functions_to_implement": [],
            "dependencies": ["trusted runtime template only"],
            "runtime_executor": "AgentRuntime",
        },
        "sandbox_code_drafts": [],
        "promotion_gate": {
            "required_tests": ["trusted template sandbox smoke passes"],
            "required_reproducibility_evidence": ["fixed seed", "metrics JSON", "script hash"],
            "production_registration_requirements": ["registered algorithm review"],
        },
        "critic_findings": [
            {
                "critic": "implementation_boundary",
                "finding": "Template execution is empirical implementation evidence only.",
                "reroute_if_confirmed": "AlgorithmEngineer",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "AgentRuntime",
                "action": "run trusted split conformal sandbox template",
                "acceptance_gate": "algorithm manifest has n_executed >= 1",
            }
        ],
    }


def _simulation_sample_response() -> dict[str, object]:
    return {
        "simulation_targets": [
            {
                "procedure_id": "aipw_crossfit",
                "estimand": "average treatment effect",
                "primary_question": "Does the proposed AIPW estimator achieve nominal coverage under overlap?",
                "target_theorem_card": "aipw_asymptotic_normality",
            }
        ],
        "dgp_plan": [
            {
                "id": "well_overlapped_binary_treatment",
                "description": "Binary treatment observational DGP with bounded propensity away from zero.",
                "parameters": ["n", "overlap bound", "outcome noise"],
                "assumptions_stressed": ["positivity", "nuisance product rate"],
                "expected_behavior": "coverage should approach nominal and RMSE should shrink",
            }
        ],
        "metric_plan": ["bias", "rmse", "coverage_95"],
        "stress_tests": ["near-positivity violation", "nuisance misspecification"],
        "failure_interpretation": [
            {
                "diagnostic": "coverage below target",
                "possible_cause": "positivity or nuisance-rate failure",
                "reroute_to": "TheoryDeveloper",
            }
        ],
        "runtime_execution_plan": {
            "registered_simulator": "ResearchSimulator.run",
            "n_runs": 80,
            "seed": 20260528,
            "notes": ["AgentRuntime owns execution and records metrics."],
        },
        "critic_findings": [
            {
                "critic": "simulation_critic",
                "finding": "Registered simulator evidence remains empirical and cannot prove asymptotic normality.",
                "reroute_if_confirmed": "FormalizationEvaluator",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "AgentRuntime",
                "action": "run registered ResearchSimulator with fixed seed",
                "acceptance_gate": "simulation manifest records metrics and proof boundary",
            }
        ],
    }


def _formalizer_sample_response() -> dict[str, object]:
    return {
        "formal_targets": [
            {
                "id": "lean_aipw_asymptotic_normality_open_target",
                "informal_source": "AIPW asymptotic normality theorem card",
                "lean_statement_sketch": "theorem aipw_asymptotic_normality_open_target ...",
                "semantic_alignment_constraints": [
                    "do not drop the nuisance product-rate remainder",
                    "keep positivity as an explicit lower-bound assumption",
                ],
                "expected_status": "OPEN",
            }
        ],
        "lemma_dependency_plan": [
            {
                "from": "second_order_remainder_bound",
                "to": "aipw_asymptotic_normality",
                "role": "reduce estimator expansion to CLT plus negligible remainder",
                "risk": "conditional expectation and asymptotic probability primitives may be missing",
            }
        ],
        "retrieval_queries": [
            {
                "query": "Slutsky theorem asymptotic normality Lean StatInference",
                "target_library": "StatInference",
                "purpose": "find reusable convergence bridge primitives",
            }
        ],
        "proof_search_plan": {
            "preferred_tools": ["formal_source_retriever", "proof_bank", "local_lean_smoke"],
            "tactic_or_certificate_hints": ["start with bounded-outcome finite helper lemmas"],
            "kernel_check_plan": ["run FormalSubclaimProver and then local Lean for any promoted candidate"],
            "known_blockers": ["conditional exchangeability formalization", "product-rate asymptotics"],
        },
        "proof_bank_obligation_requests": [
            {
                "obligation_id": "variance_nonneg",
                "target_theorem_card": "aipw_asymptotic_normality",
                "reason": "representative registered kernel-smoke dependency for variance/nonnegativity bookkeeping",
                "verification_priority": "high",
            },
            {
                "obligation_id": "constant_estimator_unbiased",
                "target_theorem_card": "aipw_asymptotic_normality",
                "reason": "deliberately off-catalog registered request used to verify runtime filtering",
                "verification_priority": "low",
            }
        ],
        "gap_taxonomy": [
            {
                "gap": "conditional exchangeability source theorem",
                "kind": "formal_primitives",
                "next_owner": "Formalizer/LeanProver",
            }
        ],
        "critic_findings": [
            {
                "critic": "proof_boundary_critic",
                "finding": "The plan must not promote mock/static proof rows to kernel evidence.",
                "reroute_if_confirmed": "FormalizationEvaluator",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "FormalizationEvaluator",
                "action": "run registered proof-bank subclaims and preserve formal gaps",
                "acceptance_gate": "formalization manifest records kernel count and gaps separately",
            }
        ],
    }


def _critic_sample_response() -> dict[str, object]:
    return {
        "evidence_boundary_audit": [
            {
                "artifact_id": "formalization_manifest",
                "evidence_type": "formalization_proof_feedback",
                "boundary_ok": True,
                "risk": "proved rows are non-kernel unless local Lean/AXLE rerun records kernel evidence",
                "required_followup": "run kernel rerun queue before claiming theorem proof evidence",
            }
        ],
        "reroute_recommendations": [
            {
                "owner_subsystem": "Formalizer/LeanProver",
                "trigger": "FORMAL_GAP",
                "action": "expand proof-bank primitives for conditional exchangeability and Slutsky bridge",
                "priority": "high",
                "acceptance_gate": "local Lean or AXLE kernel verifies promoted obligations",
            }
        ],
        "learning_updates": [
            {
                "learning_task": "proof_boundary_preservation",
                "input_signal": "formalization counts include proved rows but kernel_verified is zero",
                "target_behavior": "route to kernel rerun instead of claiming verified theorem evidence",
                "negative_example": "treating static proof-bank rows as source theorem proof",
            }
        ],
        "benchmark_expansion_plan": [
            {
                "benchmark_item": "hard-mode AIPW theorem discovery with hidden estimand/procedure",
                "capability_target": "discover theorem then preserve proof gaps",
                "success_evidence": "separate discovery accuracy, simulation evidence, and kernel proof counts",
            }
        ],
        "kernel_evidence_requirements": [
            "AXLE/local Lean verification of each promoted formal obligation",
            "separate source theorem semantic alignment review",
        ],
        "critic_findings": [
            {
                "critic": "evidence_boundary_critic",
                "finding": "The runtime correctly separates LLM proposals from executable and proof evidence.",
                "reroute_if_confirmed": "CriticEvaluator",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "Formalizer/LeanProver",
                "action": "run kernel proof smoke on representative proof-bank rows",
                "acceptance_gate": "kernel_verified count comes from AXLE/local Lean",
            }
        ],
    }


def test_simulation_engineer_canonicalizes_registered_simulator_field() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    response = _simulation_sample_response()
    runtime_plan = dict(response["runtime_execution_plan"])  # type: ignore[index]
    runtime_plan["registered_simulator"] = "AgentRuntime registered simulator"
    runtime_plan["n_runs"] = 999
    runtime_plan["seed"] = 999
    response["runtime_execution_plan"] = runtime_plan
    agent = LLMSimulationEngineerAgent(
        provider=StaticArchitectLLMProvider(response),
        config=SimulationEngineerConfig(provider_name="static", model="static-simulation-model"),
    )

    packet = agent.propose(
        question=question,
        theory_packet={"packet_id": "theory:test"},
        registered_problem={"problem_class": "semiparametric_causal_ate"},
        registered_procedures=[],
        n_runs=80,
        seed=20260528,
    )
    execution_plan = packet["runtime_execution_plan"]

    assert execution_plan["registered_simulator"] == "ResearchSimulator.run"
    assert execution_plan["llm_requested_registered_simulator"] == "AgentRuntime registered simulator"
    assert execution_plan["n_runs"] == 80
    assert execution_plan["seed"] == 20260528
    assert "AgentRuntime owns simulator selection" in execution_plan["canonicalization_boundary"]


def test_agent_runtime_does_not_retry_timeout_subsystem_exception() -> None:
    class TimeoutSubsystem:
        name = "TheoryDeveloper"

        def __init__(self) -> None:
            self.calls = 0

        def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
            self.calls += 1
            raise TimeoutError("simulated live generator timeout")

    subsystem = TimeoutSubsystem()
    progress_rows: list[dict[str, object]] = []
    runtime = AgentRuntime(
        subsystems={"TheoryDeveloper": subsystem},
        blackboard=BlackboardState(project_id="timeout-test"),
    )

    result = runtime.run(
        AgentTask(
            task_id="theory:timeout",
            owner_subsystem="TheoryDeveloper",
            objective="prove timeout exceptions fail fast",
        ),
        max_iterations=1,
        max_transient_subsystem_retries=2,
        progress_callback=progress_rows.append,
    )

    assert subsystem.calls == 1
    assert result.status == "FAILED"
    assert result.traces[0].failure_classification == "subsystem_exception"
    assert not any(
        row.get("event_type") == "subsystem_retry" for row in progress_rows
    )


def test_research_agent_runtime_records_theory_to_simulation_loop() -> None:
    out_dir = Path("runs/test_research_agent_runtime")
    shutil.rmtree(out_dir, ignore_errors=True)
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    developer = LLMTheoryDeveloperAgent(
        provider=StaticArchitectLLMProvider(_runtime_sample_response()),
        config=ResearchArchitectConfig(provider_name="static", model="static-theory-model"),
    )
    architect_coordinator = LLMArchitectCoordinatorAgent(
        provider=StaticArchitectLLMProvider(_architect_sample_response()),
        config=ArchitectCoordinatorConfig(provider_name="static", model="static-architect-model"),
    )
    simulation_engineer = LLMSimulationEngineerAgent(
        provider=StaticArchitectLLMProvider(_simulation_sample_response()),
        config=SimulationEngineerConfig(provider_name="static", model="static-simulation-model"),
    )
    algorithm_engineer = LLMAlgorithmEngineerAgent(
        provider=StaticArchitectLLMProvider(_algorithm_sample_response()),
        config=AlgorithmEngineerConfig(provider_name="static", model="static-algorithm-model"),
    )
    formalizer = LLMFormalizerProofEngineerAgent(
        provider=StaticArchitectLLMProvider(_formalizer_sample_response()),
        config=FormalizerConfig(provider_name="static", model="static-formalizer-model"),
    )
    critic_evaluator = LLMCriticEvaluatorAgent(
        provider=StaticArchitectLLMProvider(_critic_sample_response()),
        config=CriticEvaluatorConfig(provider_name="static", model="static-critic-model"),
    )

    manifest = run_research_agent_runtime(
        [question],
        out_dir,
        theory_developer=developer,
        architect_coordinator=architect_coordinator,
        simulation_engineer=simulation_engineer,
        algorithm_engineer=algorithm_engineer,
        formalizer=formalizer,
        critic_evaluator=critic_evaluator,
        proof_state_provider=LocalLeanProofStateFeedbackProvider(lean_command=("true",)),
        config=ResearchAgentRuntimeConfig(n_runs=80, seed=20260528, max_iterations=12),
    )

    assert manifest["runtime_stage"] == "architect_retrieval_theory_simulation_algorithm_formalization_critic_environment_loop"
    assert manifest["runtime_evaluation_mode"] == "debug"
    assert manifest["status_counts"]
    assert manifest["n_runtime_next_action_items"] > 0
    assert manifest["n_runtime_learning_rows"] > 0
    evidence_summary = manifest["runtime_evidence_summary"]
    assert evidence_summary["artifact_kind"] == "RuntimeEvidenceSummary"
    assert manifest["runtime_input_context"]["artifact_kind"] == "RuntimeInputContextSummary"
    assert manifest["runtime_input_context"]["runtime_learning_memory_supplied"] is False
    assert manifest["runtime_input_context"]["runtime_learning_memory_rows_loaded"] == 0
    assert evidence_summary["proof"]["n_formalization_manifests"] == 2
    assert evidence_summary["proof"]["n_kernel_verified_subclaims"] == 0
    assert evidence_summary["proof"]["n_formal_gaps"] == 6
    assert evidence_summary["proof"]["has_kernel_evidence"] is False
    assert evidence_summary["proof"]["has_formal_gaps"] is True
    assert evidence_summary["proof"]["has_formalization_gap_planner_bridge"] is True
    assert evidence_summary["proof"]["n_formalization_gap_planner_bridges"] == 2
    assert evidence_summary["proof"]["n_formalization_gap_planner_routes"] == 6
    assert evidence_summary["proof"]["n_formalization_gap_planner_primitives"] > 0
    proof_control = evidence_summary["proof"]["proof_obligation_control"]
    assert proof_control["n_selected_proof_obligations"] == evidence_summary["proof"]["n_proved_subclaims"]
    assert proof_control["n_candidate_proof_obligations"] == evidence_summary["proof"]["n_proved_subclaims"]
    assert proof_control["selected_proof_obligation_ids"]
    assert proof_control["llm_requested_proof_obligation_ids"] == ["variance_nonneg"]
    assert proof_control["llm_off_catalog_proof_obligation_ids"] == ["constant_estimator_unbiased"]
    assert proof_control["prioritized_proof_obligation_ids"] == ["variance_nonneg"]
    assert proof_control["selected_priority_proof_obligation_ids"] == ["variance_nonneg"]
    assert proof_control["eligible_proof_obligation_ids_before_limit"]
    assert proof_control["deferred_proof_obligation_ids_due_to_max"] == []
    assert proof_control["deferred_priority_proof_obligation_ids_due_to_max"] == []
    assert evidence_summary["algorithm"]["n_algorithm_sandbox_executed"] == 4
    assert evidence_summary["algorithm"]["n_generated_code_sandbox_executed"] == 2
    assert evidence_summary["algorithm"]["n_unsafe_generated_code_rejected"] == 0
    assert evidence_summary["honesty_boundary"]["kernel_subclaims_imply_full_frontier_theorem"] is False
    assert manifest["n_kernel_verified_subclaims"] == 0
    assert manifest["n_formal_gaps"] == 6
    assert manifest["n_algorithm_sandbox_executed"] == 4
    assert manifest["n_generated_code_sandbox_executed"] == 2
    assert manifest["n_unsafe_generated_code_rejected"] == 0
    assert Path(manifest["artifacts"]["runtime_llm_topology_json"]).exists()
    theorem_closure_queue_path = Path(
        manifest["artifacts"]["runtime_theorem_reduction_closure_work_orders_jsonl"]
    )
    assert theorem_closure_queue_path.exists()
    assert manifest["n_runtime_theorem_reduction_closure_work_orders"] == 0
    source_theorem_environment_queue_path = Path(
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_work_orders_jsonl"
        ]
    )
    assert source_theorem_environment_queue_path.exists()
    assert manifest["n_runtime_source_theorem_formal_environment_work_orders"] == 0
    assert (
        manifest[
            "source_theorem_promotion_proofengineer_bridge_n_formal_environment_work_orders"
        ]
        == 0
    )
    assert (
        manifest[
            "source_theorem_promotion_proofengineer_bridge_overwrite_artifacts_requested"
        ]
        is False
    )
    bridges_path = Path(
        manifest["artifacts"]["runtime_formalization_gap_planner_bridges_jsonl"]
    )
    assert bridges_path.exists()
    assert Path(manifest["artifacts"]["runtime_formalization_gap_planner_seed_dir"]).exists()
    handoffs_path = Path(
        manifest["artifacts"]["runtime_formalization_gap_planner_handoffs_jsonl"]
    )
    assert handoffs_path.exists()
    assert manifest["n_runtime_formalization_gap_planner_bridges"] == 2
    assert manifest["n_runtime_formalization_gap_planner_routes"] == 6
    assert manifest["n_runtime_formalization_gap_planner_handoffs"] == 2
    topology = manifest["llm_runtime_topology"]
    assert topology["artifact_kind"] == "RuntimeLLMTopologyManifest"
    assert topology["counts"]["llm_agents_enabled"] == 6
    assert topology["counts"]["enabled_by_model_tier"] == {"haiku": 3, "sonnet": 3}
    assert topology["counts"]["enabled_by_provider"] == {"static": 6}
    assert topology["counts"]["unsupported_generator_backends_enabled"] == 0
    assert topology["counts"]["anthropic_model_tier_mismatches"] == 0
    assert topology["counts"]["resolved_claude_model_tier_policy_violations"] == 0
    assert topology["policy_status"] == "OK"
    assert topology["policy_violations"] == []
    theory_row = next(row for row in topology["llm_agents"] if row["subsystem"] == "TheoryDeveloper")
    assert theory_row["max_tokens"] == 4500
    assert topology["policy"]["supported_generator_providers"] == ["anthropic", "openai", "static"]
    assert topology["policy"]["default_live_provider"] == "anthropic"
    assert topology["policy"]["claude_model_selection"]["models_by_tier"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-8",
    }
    assert topology["policy"]["resolved_claude_models_by_tier"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-8",
    }
    assert topology["policy"]["resolved_claude_model_tier_policy_status"] == "OK"
    assert topology["policy"]["resolved_claude_model_tier_policy_violations"] == []
    assert topology["policy"]["resolved_claude_model_freshness_status"] == "CURRENT"
    assert topology["policy"]["resolved_claude_model_freshness_warnings"] == []
    assert "not evergreen aliases" in topology["policy"]["claude_model_selection"]["model_id_versioning"]
    assert "LLM backends generate structured proposals only" in topology["policy"]["backend_boundary"]
    assert Path(manifest["artifacts"]["runtime_next_action_agenda_jsonl"]).exists()
    assert Path(manifest["artifacts"]["runtime_learning_rows_jsonl"]).exists()
    result_path = Path(manifest["artifacts"]["per_question_results"][0])
    result = json.loads(result_path.read_text(encoding="utf-8"))
    progress_path = Path(manifest["artifacts"]["runtime_progress_jsonl"])
    assert progress_path.exists()
    progress_rows = [
        json.loads(line)
        for line in progress_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert progress_rows[0]["event_type"] == "subsystem_start"
    assert progress_rows[0]["subsystem"] == "ArchitectCoordinator"
    assert any(row["event_type"] == "subsystem_finish" for row in progress_rows)
    assert [row["status"] for row in result["traces"][:12]] == [
        "REROUTE",
        "REROUTE",
        "REROUTE",
        "REROUTE",
        "REROUTE",
        "REROUTE",
        "REVISE",
        "REROUTE",
        "REROUTE",
        "REROUTE",
        "REROUTE",
        "ACCEPTED",
    ]
    assert result["traces"][0]["subsystem"] == "ArchitectCoordinator"
    assert result["traces"][1]["subsystem"] == "RetrievalMemory"
    architect_plan = result["traces"][1]["task"]["inputs"]["architect_context"]["architect_runtime_plan"]
    assert architect_plan["problem_analysis"]["theorem_family"] == "semiparametric efficiency and asymptotic normality"
    assert "DML/AIPW asymptotic normality papers" in architect_plan["stat_knowledge_bank_plan"]["source_families_to_collect"]
    assert architect_plan["literature_fair_comparison_plan"][0]["candidate_source_family"] == "double machine learning ATE CLT"
    assert result["traces"][2]["task"]["acceptance_gate"] == "schema-valid proposal with no proof-evidence claim"
    assert result["traces"][3]["task"]["acceptance_gate"] == "runtime records seed, metrics, and empirical boundary"
    assert result["traces"][4]["task"]["acceptance_gate"] == "sandbox prototype records reproducible metrics"
    assert result["traces"][5]["task"]["acceptance_gate"] == "kernel count only comes from verifier rows"
    assert result["traces"][6]["task"]["acceptance_gate"] == "critic agenda preserves proof and execution boundaries"
    assert result["traces"][6]["subsystem"] == "CriticEvaluator"
    assert result["traces"][7]["subsystem"] == "TheoryDeveloper"
    assert result["traces"][7]["task"]["inputs"]["environment_feedback"]["feedback_source"] == "CriticEvaluator"
    assert (
        result["traces"][7]["task"]["inputs"]["environment_feedback"]["required_revision"].startswith(
            "Revise theorem statements"
        )
    )
    assert result["traces"][11]["subsystem"] == "CriticEvaluator"
    retrieval_context = result["traces"][2]["task"]["inputs"]["architect_context"]["retrieval_context"]
    assert retrieval_context["knowledge_cards"]
    assert retrieval_context["paper_sources"]
    assert "Retrieval hits are not proof evidence" in retrieval_context["boundary"]
    assert result["traces"][3]["tool_calls"][0]["tool_name"] == "ResearchSimulator.run"
    algorithm_tool_names = {row["tool_name"] for row in result["traces"][4]["tool_calls"]}
    assert "python.crossfit_aipw_sandbox" in algorithm_tool_names
    assert "python.generated_algorithm_sandbox" in algorithm_tool_names
    assert result["traces"][5]["tool_calls"][0]["tool_name"] == "FormalSubclaimProver.prove"
    artifacts = result["blackboard"]["artifacts"]
    topology_artifact = next(row for key, row in artifacts.items() if key.startswith("runtime_llm_topology:"))
    assert topology_artifact["manifest_id"] == topology["manifest_id"]
    assert all(row["generator_only"] is True for row in topology_artifact["llm_agents"])
    assert all(row["acts_in_environment"] is False for row in topology_artifact["llm_agents"])
    architect_proposal = next(row for key, row in artifacts.items() if key.startswith("architect_coordinator_proposal:"))
    assert architect_proposal["source_agent"] == "LLMArchitectCoordinatorAgent"
    assert architect_proposal["proof_evidence_status"] == "LLM_ARCHITECT_COORDINATOR_PROPOSAL_NOT_PROOF_EVIDENCE"
    assert architect_proposal["runtime_executed"] is False
    assert architect_proposal["kernel_verified"] is False
    retrieval_manifest = next(row for key, row in artifacts.items() if key.startswith("retrieval_memory_manifest:"))
    assert retrieval_manifest["runtime_architect_control"]["acceptance_gate"] == "retrieval context records source boundaries"
    assert (
        retrieval_manifest["runtime_architect_control"]["problem_analysis"]["theorem_family"]
        == "semiparametric efficiency and asymptotic normality"
    )
    assert (
        retrieval_manifest["runtime_architect_control"]["literature_fair_comparison_plan"][0][
            "candidate_source_family"
        ]
        == "double machine learning ATE CLT"
    )
    assert retrieval_manifest["counts"]["knowledge_cards"] > 0
    assert retrieval_manifest["counts"]["paper_sources"] > 0
    theory_packet = next(row for key, row in artifacts.items() if key.startswith("theory_derivation:"))
    assert theory_packet["runtime_architect_control"]["acceptance_gate"] == "schema-valid proposal with no proof-evidence claim"
    simulation_proposal = next(row for key, row in artifacts.items() if key.startswith("simulation_engineer_proposal:"))
    assert simulation_proposal["source_agent"] == "LLMSimulationEngineerAgent"
    assert simulation_proposal["simulation_evidence_status"] == "LLM_SIMULATION_PROPOSAL_NOT_EXECUTION_EVIDENCE"
    assert simulation_proposal["simulations_executed"] is False
    simulation_manifest = next(row for key, row in artifacts.items() if key.startswith("simulation_manifest:"))
    assert simulation_manifest["runtime_architect_control"]["acceptance_gate"] == "runtime records seed, metrics, and empirical boundary"
    assert simulation_manifest["llm_simulation_engineer_proposal_id"] == simulation_proposal["packet_id"]
    assert simulation_manifest["proof_evidence_status"] == "SIMULATION_NOT_PROOF_EVIDENCE"
    assert simulation_manifest["implementation_gaps"][0]["estimator_id"] == "crossfit_aipw"
    algorithm_manifest = next(row for key, row in artifacts.items() if key.startswith("algorithm_sandbox_manifest:"))
    assert algorithm_manifest["runtime_architect_control"]["acceptance_gate"] == "sandbox prototype records reproducible metrics"
    algorithm_proposal = next(row for key, row in artifacts.items() if key.startswith("algorithm_engineer_proposal:"))
    assert algorithm_proposal["source_agent"] == "LLMAlgorithmEngineerAgent"
    assert algorithm_proposal["execution_evidence_status"] == "LLM_ALGORITHM_PROPOSAL_NOT_EXECUTION_EVIDENCE"
    assert algorithm_proposal["sandbox_executed"] is False
    assert algorithm_manifest["llm_algorithm_engineer_proposal_id"] == algorithm_proposal["packet_id"]
    assert algorithm_manifest["n_executed"] == 2
    assert algorithm_manifest["n_passed"] == 2
    assert algorithm_manifest["n_generated_code_executed"] == 1
    assert algorithm_manifest["n_unsafe_generated_code_rejected"] == 0
    assert algorithm_manifest["promotion_ready"] is False
    crossfit_prototype = next(row for row in algorithm_manifest["prototypes"] if row["estimator_id"] == "crossfit_aipw")
    generated_prototype = next(row for row in algorithm_manifest["prototypes"] if row["estimator_id"] == "generated_bias_probe")
    assert crossfit_prototype["metrics"]["n_success"] > 0
    assert crossfit_prototype["llm_algorithm_engineer_target"]["registered_template_hint"] == "crossfit_aipw"
    assert generated_prototype["executor"] == "generated_python_sandbox"
    assert generated_prototype["prototype_status"] == "EXECUTED"
    assert generated_prototype["smoke_passed"] is True
    assert generated_prototype["promotion_ready"] is False
    assert generated_prototype["metrics"]["n_runs"] == 80
    assert "mean_bias_probe" in generated_prototype["metrics"]
    assert generated_prototype["llm_algorithm_engineer_target"]["registered_template_hint"] == "none"
    formalizer_proposal = next(row for key, row in artifacts.items() if key.startswith("formalizer_proposal:"))
    assert formalizer_proposal["source_agent"] == "LLMFormalizerProofEngineerAgent"
    assert formalizer_proposal["proof_evidence_status"] == "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE"
    assert formalizer_proposal["kernel_verified"] is False
    assert formalizer_proposal["full_frontier_theorem_proved"] is False
    assert formalizer_proposal["proof_bank_obligation_requests"][0]["obligation_id"] == "variance_nonneg"
    assert formalizer_proposal["proof_bank_obligation_requests"][1]["obligation_id"] == "constant_estimator_unbiased"
    formalization_manifest = next(row for key, row in artifacts.items() if key.startswith("formalization_manifest:"))
    assert formalization_manifest["runtime_architect_control"]["acceptance_gate"] == "kernel count only comes from verifier rows"
    assert formalization_manifest["full_frontier_theorem_proved"] is False
    assert formalization_manifest["algorithm_sandbox_manifest_id"].startswith("algorithm_sandbox_manifest:")
    assert formalization_manifest["llm_formalizer_proof_engineer_proposal_id"] == formalizer_proposal["packet_id"]
    assert formalization_manifest["llm_proof_bank_obligation_requests"][0]["obligation_id"] == "variance_nonneg"
    assert formalization_manifest["registered_proof_bank_obligation_catalog"]
    assert any(
        row["obligation_id"] == "variance_nonneg"
        for row in formalization_manifest["registered_proof_bank_obligation_catalog"]
    )
    assert all(
        "proof_body" not in row
        for row in formalization_manifest["registered_proof_bank_obligation_catalog"]
    )
    assert "not proof evidence" in formalization_manifest["registered_proof_bank_obligation_catalog_boundary"]
    assert formalization_manifest["proof_obligation_control"]["llm_requested_proof_obligation_ids"] == ["variance_nonneg"]
    assert formalization_manifest["proof_obligation_control"]["llm_off_catalog_proof_obligation_ids"] == [
        "constant_estimator_unbiased"
    ]
    assert formalization_manifest["proof_obligation_control"]["llm_rejected_proof_obligation_ids"] == []
    assert formalization_manifest["proof_obligation_control"]["selected_proof_obligation_ids"][0] == "variance_nonneg"
    assert formalization_manifest["proof_obligation_control"]["selected_priority_proof_obligation_ids"] == ["variance_nonneg"]
    assert "constant_estimator_unbiased" not in formalization_manifest["proof_obligation_control"][
        "selected_priority_proof_obligation_ids"
    ]
    assert formalization_manifest["counts"]["formal_gap"] > 0
    assert formalization_manifest["counts"]["proved"] > 0
    assert formalization_manifest["proof_state_feedback_manifest_id"].startswith("proof_state_feedback_manifest:")
    assert formalization_manifest["counts"]["proof_state_feedback"] > 0
    assert formalization_manifest["formalization_gap_planner_bridge_id"].startswith(
        "runtime_formalization_gap_planner_bridge:"
    )
    assert formalization_manifest[
        "formalization_gap_planner_standalone_seed_artifact_id"
    ].startswith("runtime_formalization_gap_planner_standalone_seed:")
    assert formalization_manifest["counts"]["formalization_gap_planner_routes"] > 0
    gap_planner_bridge = next(
        row
        for key, row in artifacts.items()
        if key.startswith("runtime_formalization_gap_planner_bridge:")
    )
    assert gap_planner_bridge["artifact_kind"] == "RuntimeFormalizationGapPlannerBridge"
    assert gap_planner_bridge["target_prover_family"] == "lean4"
    assert gap_planner_bridge["standalone_seed"]["target_prover_family"] == "lean4"
    assert all(
        route["target_prover_family"] == "lean4"
        for route in gap_planner_bridge["standalone_seed"]["routes"]
    )
    first_runtime_route = gap_planner_bridge["standalone_seed"]["routes"][0]
    assert first_runtime_route["replan_metadata"]["formal_declaration_hits"]
    assert (
        first_runtime_route["replan_metadata"]["lean_declaration_hits"]
        == first_runtime_route["replan_metadata"]["formal_declaration_hits"]
    )
    assert gap_planner_bridge["counts"]["routes"] > 0
    assert gap_planner_bridge["counts"]["primitives"] > 0
    assert gap_planner_bridge["counts"]["candidate_declaration_rows"] > 0
    assert (
        gap_planner_bridge["counts"]["primitives_with_candidate_declaration_rows"] > 0
    )
    assert any(
        primitive.get("candidate_declaration_rows")
        for route in gap_planner_bridge["standalone_seed"]["routes"]
        for primitive in route["primitives"]
    )
    assert "--model-tier auto" in gap_planner_bridge["next_llm_route_planner_prompt_cli"]
    assert "--max-repair-attempts 1" in gap_planner_bridge["next_llm_route_planner_prompt_cli"]
    assert "--provider anthropic" in gap_planner_bridge["next_llm_route_planner_prompt_cli"]
    assert (
        "--formalization-gap-planner-target-intake-dir"
        in gap_planner_bridge["next_llm_route_planner_prompt_cli"]
    )
    assert (
        "--formalization-gap-planner-component-resource-registry-dir"
        in gap_planner_bridge["next_llm_route_planner_prompt_cli"]
    )
    assert "--invoke-provider" not in gap_planner_bridge["next_llm_route_planner_prompt_cli"]
    assert "--invoke-provider" in gap_planner_bridge["next_llm_route_planner_live_cli"]
    assert (
        "--formalization-gap-planner-target-intake-dir"
        in gap_planner_bridge["next_llm_route_planner_live_cli"]
    )
    assert (
        "--formalization-gap-planner-component-resource-registry-dir"
        in gap_planner_bridge["next_llm_route_planner_live_cli"]
    )
    assert "formalization-gap-planner-reuse-smoke" in gap_planner_bridge["next_reuse_smoke_cli"]
    assert "--llm-route-planner-provider anthropic" in gap_planner_bridge["next_reuse_smoke_cli"]
    assert "--feedback-llm-route-planner-provider anthropic" in gap_planner_bridge["next_reuse_smoke_cli"]
    assert "--llm-route-planner-invoke-provider" not in gap_planner_bridge["next_reuse_smoke_cli"]
    assert "--feedback-llm-route-planner-invoke-provider" not in gap_planner_bridge["next_reuse_smoke_cli"]
    assert gap_planner_bridge["proof_evidence_status"] == (
        "RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE"
    )
    handoff_rows = [
        json.loads(line)
        for line in handoffs_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    persisted_bridge_rows = [
        json.loads(line)
        for line in bridges_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(persisted_bridge_rows) == 2
    assert persisted_bridge_rows[0]["standalone_seed_path"].endswith(".json")
    assert persisted_bridge_rows[0]["target_intake_path"].endswith(".json")
    assert persisted_bridge_rows[0]["target_intake_dir"].endswith("target_intake")
    assert (
        "formalization-gap-planner-target-intake"
        in persisted_bridge_rows[0]["target_intake_cli"]
    )
    assert persisted_bridge_rows[0]["target_prover_family"] == "lean4"
    assert persisted_bridge_rows[0]["counts"]["candidate_declaration_rows"] > 0
    assert persisted_bridge_rows[0]["component_resource_registry_dir"].endswith(
        "component_resource_registry"
    )
    assert (
        "formalization-gap-planner-component-resource-registry"
        in persisted_bridge_rows[0]["component_resource_registry_cli"]
    )
    assert "--model-tier auto" in persisted_bridge_rows[0]["llm_route_planner_prompt_cli"]
    assert "--max-repair-attempts 1" in persisted_bridge_rows[0]["llm_route_planner_prompt_cli"]
    assert (
        persisted_bridge_rows[0]["target_intake_dir"]
        in persisted_bridge_rows[0]["llm_route_planner_prompt_cli"]
    )
    assert (
        "--formalization-gap-planner-target-intake-dir"
        in persisted_bridge_rows[0]["llm_route_planner_prompt_cli"]
    )
    assert (
        "--formalization-gap-planner-component-resource-registry-dir"
        in persisted_bridge_rows[0]["llm_route_planner_prompt_cli"]
    )
    assert "formalization-gap-planner-reuse-smoke" in persisted_bridge_rows[0]["reuse_smoke_cli"]
    assert "--llm-route-planner-invoke-provider" not in persisted_bridge_rows[0]["reuse_smoke_cli"]
    assert len(handoff_rows) == 2
    handoff = handoff_rows[0]
    assert handoff["artifact_kind"] == "RuntimeFormalizationGapPlannerHandoff"
    assert handoff["target_prover_family"] == "lean4"
    assert handoff["target_intake_path"].endswith(".json")
    assert handoff["target_intake_dir"].endswith("target_intake")
    assert "formalization-gap-planner-target-intake" in handoff["target_intake_cli"]
    assert handoff["recommended_llm_provider"] == "anthropic"
    assert handoff["recommended_model_tier"] == "auto"
    assert handoff["component_resource_registry_dir"].endswith(
        "component_resource_registry"
    )
    assert (
        "formalization-gap-planner-component-resource-registry"
        in handoff["component_resource_registry_cli"]
    )
    assert "--model-tier auto" in handoff["llm_route_planner_prompt_cli"]
    assert "--max-repair-attempts 1" in handoff["llm_route_planner_prompt_cli"]
    assert "--provider anthropic" in handoff["llm_route_planner_prompt_cli"]
    assert "--formalization-gap-planner-target-intake-dir" in handoff[
        "llm_route_planner_prompt_cli"
    ]
    assert handoff["target_intake_dir"] in handoff["llm_route_planner_prompt_cli"]
    assert (
        "--formalization-gap-planner-component-resource-registry-dir"
        in handoff["llm_route_planner_prompt_cli"]
    )
    assert "--invoke-provider" not in handoff["llm_route_planner_prompt_cli"]
    assert "--invoke-provider" in handoff["llm_route_planner_live_cli"]
    assert "--formalization-gap-planner-target-intake-dir" in handoff[
        "llm_route_planner_live_cli"
    ]
    assert handoff["target_intake_dir"] in handoff["llm_route_planner_live_cli"]
    assert (
        "--formalization-gap-planner-component-resource-registry-dir"
        in handoff["llm_route_planner_live_cli"]
    )
    assert "formalization-gap-planner-reuse-smoke" in handoff["reuse_smoke_cli"]
    assert "--llm-route-planner-provider anthropic" in handoff["reuse_smoke_cli"]
    assert "--feedback-llm-route-planner-provider anthropic" in handoff["reuse_smoke_cli"]
    assert "--llm-route-planner-invoke-provider" not in handoff["reuse_smoke_cli"]
    assert "--feedback-llm-route-planner-invoke-provider" not in handoff["reuse_smoke_cli"]
    assert handoff["proof_evidence_status"] == (
        "RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE"
    )
    runtime_handoff_audit = audit_formalization_gap_planner_runtime_handoffs(
        handoffs_path,
        out_dir / "runtime_formalization_gap_planner_handoff_audit",
        run_smoke=True,
    )
    assert runtime_handoff_audit["all_ok"] is True
    assert runtime_handoff_audit["n_handoffs"] == 2
    assert runtime_handoff_audit["n_cost_control_ok"] == 2
    assert runtime_handoff_audit["n_live_explicit_ok"] == 2
    assert runtime_handoff_audit["n_reuse_smoke_cost_control_ok"] == 2
    assert runtime_handoff_audit["n_component_resource_registry_smoke_ok"] == 2
    assert (
        runtime_handoff_audit[
            "n_component_resource_registry_components_in_prompt"
        ]
        > 0
    )
    assert (
        runtime_handoff_audit["n_component_resource_registry_resources_in_prompt"]
        > 0
    )
    assert (
        runtime_handoff_audit["n_component_resource_registry_contracts_in_prompt"]
        > 0
    )
    assert runtime_handoff_audit["n_target_intake_smoke_ok"] == 2
    assert runtime_handoff_audit["n_target_intake_targets"] >= 2
    assert runtime_handoff_audit["n_target_intake_primitive_seeds"] > 0
    assert runtime_handoff_audit["n_standalone_smoke_ok"] == 2
    assert runtime_handoff_audit["n_llm_prompt_smoke_ok"] == 2
    assert runtime_handoff_audit["n_llm_prompt_packets"] >= 2
    assert (
        runtime_handoff_audit["n_llm_prompt_requests_with_target_intake_rows"]
        == runtime_handoff_audit["n_llm_prompt_packets"]
    )
    assert runtime_handoff_audit["n_llm_prompt_target_intake_rows"] > 0
    assert (
        runtime_handoff_audit[
            "n_llm_prompt_requests_with_minimal_delta_cost_hints"
        ]
        == runtime_handoff_audit["n_llm_prompt_packets"]
    )
    assert runtime_handoff_audit["n_llm_prompt_primitive_cost_hints"] > 0
    assert runtime_handoff_audit["n_llm_prompt_route_option_cost_hints"] > 0
    assert runtime_handoff_audit["n_llm_prompt_model_tier_mismatches"] == 0
    assert (
        runtime_handoff_audit["n_llm_prompt_model_tier_haiku"]
        + runtime_handoff_audit["n_llm_prompt_model_tier_sonnet"]
        + runtime_handoff_audit["n_llm_prompt_model_tier_opus"]
        == runtime_handoff_audit["n_llm_prompt_packets"]
    )
    assert runtime_handoff_audit["n_seed_candidate_declaration_rows"] > 0
    assert (
        runtime_handoff_audit["n_seed_primitives_with_candidate_declaration_rows"] > 0
    )
    assert all(
        summary["seed_candidate_declaration_rows"] > 0
        for summary in runtime_handoff_audit["smoke_summaries"]
    )
    assert all(
        summary["llm_prompt_model_tier_haiku"]
        + summary["llm_prompt_model_tier_sonnet"]
        + summary["llm_prompt_model_tier_opus"]
        == summary["llm_prompt_packets"]
        for summary in runtime_handoff_audit["smoke_summaries"]
    )
    assert runtime_handoff_audit["by_category"]["target_prover"] == 6
    assert Path(
        runtime_handoff_audit[
            "runtime_formalization_gap_planner_handoffs_jsonl"
        ]
    ).exists()
    assert Path(
        out_dir
        / "runtime_formalization_gap_planner_handoff_audit"
        / "formalization_gap_planner_runtime_handoff_audit_manifest.json"
    ).exists()
    runtime_handoff_report = (
        out_dir
        / "runtime_formalization_gap_planner_handoff_audit"
        / "formalization_gap_planner_runtime_handoff_audit.md"
    ).read_text(encoding="utf-8")
    assert "Seed candidate declaration rows:" in runtime_handoff_report
    assert "Target-intake smoke OK:" in runtime_handoff_report
    assert "Target-intake context in prompts:" in runtime_handoff_report
    assert "Component-resource registry smoke OK:" in runtime_handoff_report
    assert "Registry context in prompts:" in runtime_handoff_report
    assert "Minimal-delta cost hints in prompts:" in runtime_handoff_report
    assert "LLM prompt model-tier mismatches:" in runtime_handoff_report
    assert "LLM prompt model tiers:" in runtime_handoff_report
    standalone_seed = gap_planner_bridge["standalone_seed"]
    assert validate_standalone_input_payload(standalone_seed) == []
    assert standalone_seed["component_name"] == "formalization_gap_planner_standalone_input"
    assert standalone_seed["routes"][0]["replan_metadata"]["residual_goals"]
    assert all(
        isinstance(ref, str)
        for route in standalone_seed["routes"]
        for ref in route["source_refs"]
    )
    proof_state_manifest = next(row for key, row in artifacts.items() if key.startswith("proof_state_feedback_manifest:"))
    assert proof_state_manifest["provider_name"] == "local_lean_proof_state_feedback"
    assert proof_state_manifest["lean_lsp_mcp_live_called"] is False
    assert proof_state_manifest["proof_evidence_status"] == PROOF_STATE_FEEDBACK_STATUS
    assert proof_state_manifest["counts"]["rows"] == formalization_manifest["counts"]["proof_state_feedback"]
    assert proof_state_manifest["counts"]["residual_goals"] > 0
    assert any(row["attempt_status"] == "formal_gap_scaffold_blocked" for row in proof_state_manifest["rows"])
    assert all(row["proof_evidence_status"] == PROOF_STATE_FEEDBACK_STATUS for row in proof_state_manifest["rows"])
    critic_proposal = next(row for key, row in artifacts.items() if key.startswith("critic_evaluator_proposal:"))
    assert critic_proposal["source_agent"] == "LLMCriticEvaluatorAgent"
    assert critic_proposal["proof_evidence_status"] == "LLM_CRITIC_EVALUATOR_PROPOSAL_NOT_PROOF_EVIDENCE"
    assert critic_proposal["kernel_verified"] is False
    assert critic_proposal["full_frontier_theorem_proved"] is False
    critic_manifest = next(row for key, row in artifacts.items() if key.startswith("critic_evaluator_manifest:"))
    assert critic_manifest["runtime_architect_control"]["acceptance_gate"] == "critic agenda preserves proof and execution boundaries"
    assert critic_manifest["llm_critic_evaluator_proposal_id"] == critic_proposal["packet_id"]
    assert critic_manifest["critic_repair_round"] == 0
    assert critic_manifest["max_critic_repair_rounds"] == 1
    assert critic_manifest["runtime_reroute_decision"]["reroute_to_theory_developer"] is True
    critic_manifests = [row for key, row in artifacts.items() if key.startswith("critic_evaluator_manifest:")]
    assert critic_manifests[-1]["critic_repair_round"] == 1
    assert critic_manifests[-1]["runtime_reroute_decision"]["reroute_to_theory_developer"] is False
    agenda_ids = {row["id"] for row in critic_manifest["next_action_agenda"]}
    assert "formal_gap:proof_bank_expansion" in agenda_ids
    assert "formal_gap:gap_planner_handoff" in agenda_ids
    assert "proof_feedback:kernel_rerun" in agenda_ids
    assert "algorithm:prototype_review" in agenda_ids
    assert critic_manifest["learning_rows"]
    feedback_memory = next(
        row
        for row in critic_manifest["learning_rows"]
        if row["learning_task"] == "simulation_algorithm_formalization_feedback"
    )
    assert feedback_memory["recommended_proof_obligation_ids"][0] == "variance_nonneg"
    assert "variance_nonneg" in feedback_memory["selected_proof_obligation_ids"]
    assert "variance_nonneg" in feedback_memory["proved_non_kernel_proof_obligation_ids"]
    assert result["blackboard"]["evidence_ledger"][0]["evidence_type"] == "llm_architect_coordinator_proposal"
    assert result["blackboard"]["evidence_ledger"][1]["evidence_type"] == "retrieval_memory"
    assert result["blackboard"]["evidence_ledger"][2]["evidence_type"] == "llm_theory_derivation"
    assert any(row["evidence_type"] == "llm_simulation_engineer_proposal" for row in result["blackboard"]["evidence_ledger"])
    assert any(row["evidence_type"] == "llm_algorithm_engineer_proposal" for row in result["blackboard"]["evidence_ledger"])
    assert any(row["evidence_type"] == "algorithm_sandbox" for row in result["blackboard"]["evidence_ledger"])
    assert any(row["evidence_type"] == "llm_formalizer_proof_engineer_proposal" for row in result["blackboard"]["evidence_ledger"])
    assert any(row["evidence_type"] == "proof_state_feedback" for row in result["blackboard"]["evidence_ledger"])
    assert any(row["evidence_type"] == "formalization_gap_planner_runtime_bridge" for row in result["blackboard"]["evidence_ledger"])
    assert any(row["evidence_type"] == "llm_critic_evaluator_proposal" for row in result["blackboard"]["evidence_ledger"])
    assert result["blackboard"]["evidence_ledger"][-1]["evidence_type"] == "critic_evaluator"

    audit = audit_research_agent_runtime(out_dir, out_dir / "runtime_alignment_audit")
    assert audit["all_ok"] is True
    assert audit["result_errors"] == []
    assert audit["n_result_errors"] == 0
    assert audit["capability_ready_for_full_ai_statistician"] is False
    assert audit["capability_status"] == "CONTRACT_OK_WITH_CAPABILITY_GAPS"
    scorecard = audit["capability_scorecard"]
    scorecard_rows = {row["requirement_id"]: row for row in scorecard["rows"]}
    assert scorecard["artifact_kind"] == "RuntimeCapabilityScorecard"
    assert scorecard["runtime_evaluation_mode"] == "debug"
    assert scorecard["ready"] is False
    ladder = audit["capability_ladder"]
    assert ladder["artifact_kind"] == "RuntimeCapabilityLadder"
    assert ladder["max_contiguous_level"] == 0
    assert ladder["levels"][0]["passed"] is True
    assert ladder["levels"][1]["passed"] is False
    assert scorecard_rows["runtime_marked_capability_eval"]["passed"] is False
    assert scorecard_rows["architect_orchestrated"]["passed"] is True
    assert scorecard_rows["dynamic_stat_knowledge_bank_planned"]["passed"] is True
    assert scorecard_rows["live_generator_agents_enabled"]["passed"] is False
    assert scorecard_rows["live_lean_lsp_mcp_called"]["passed"] is False
    assert scorecard_rows["full_frontier_theorem_kernel_proved"]["passed"] is False
    assert "no live Anthropic/OpenAI generator agents were enabled" in audit["capability_gaps"]
    assert "Lean LSP/MCP was not called live for proof-state diagnostics" in audit["capability_gaps"]
    assert "no full frontier theorem was kernel-proved" in audit["capability_gaps"]
    assert audit["architect_coordinator_enabled"] is True
    assert audit["llm_topology_policy_ok"] is True
    assert audit["unsupported_generator_backends_enabled"] == 0
    assert audit["n_live_generator_agents_enabled"] == 0
    assert audit["n_lean_lsp_mcp_live_calls"] == 0
    assert audit["n_critic_reroutes"] == 1
    assert audit["has_kernel_evidence"] is False
    assert audit["has_real_kernel_evidence"] is False
    assert audit["n_results_with_kernel_evidence"] == 0
    assert audit["n_results_with_real_kernel_evidence"] == 0
    assert audit["n_kernel_verified_subclaims"] == 0
    assert audit["n_real_kernel_verified_subclaims"] == 0
    assert audit["n_non_real_kernel_verified_subclaims"] == 0
    assert audit["kernel_verified_verifiers"] == []
    assert audit["n_memory_prioritized_proof_obligations"] == 0
    assert audit["n_memory_off_catalog_proof_obligations"] == 0
    assert audit["n_memory_rejected_proof_obligations"] == 0
    assert audit["n_algorithm_sandbox_executed"] == 4
    assert audit["n_generated_code_sandbox_executed"] == 2
    assert audit["n_unsafe_generated_code_rejected"] == 0
    assert audit["n_runtime_progress_events"] >= audit["n_runtime_traces"] * 2
    assert audit["n_results_with_problem_analysis"] == 1
    assert audit["n_results_with_stat_knowledge_bank_plan"] == 1
    assert audit["n_results_with_literature_fair_comparison_plan"] == 1
    assert audit["n_results_with_runtime_learning_memory_input"] == 0
    assert audit["n_runtime_learning_memory_input_rows"] == 0
    system_overlay = _research_agent_runtime_audit_overlay(
        out_dir / "system_overlay",
        configured_runtime_dir=str(out_dir),
    )
    assert system_overlay["requested"] is True
    assert system_overlay["available"] is True
    assert system_overlay["all_ok"] is True
    assert system_overlay["capability_ready_for_full_ai_statistician"] is False
    assert system_overlay["capability_status"] == "CONTRACT_OK_WITH_CAPABILITY_GAPS"
    assert system_overlay["architect_coordinator_enabled"] is True
    assert system_overlay["n_critic_reroutes"] == 1
    assert system_overlay["has_real_kernel_evidence"] is False
    assert system_overlay["n_results_with_real_kernel_evidence"] == 0
    assert system_overlay["n_real_kernel_verified_subclaims"] == 0
    assert system_overlay["n_non_real_kernel_verified_subclaims"] == 0
    assert Path(system_overlay["manifest_path"]).exists()


def test_runtime_capability_ladder_separates_closure_memory_from_full_theorem() -> None:
    payload = {
        "all_ok": True,
        "n_results": 1,
        "n_distinct_question_ids": 1,
        "n_live_generator_agents_enabled": 6,
        "architect_coordinator_enabled": True,
        "n_algorithm_sandbox_executed": 1,
        "n_real_kernel_verified_subclaims": 0,
        "n_runtime_memory_kernel_verified_proof_obligation_ids": 9,
        "n_runtime_memory_kernel_verified_theorem_reduction_closure_goal_ids": 1,
        "n_runtime_memory_kernel_verified_source_theorem_semantic_primitive_ids": 2,
        "n_real_kernel_verified_source_theorem_semantic_primitive_subclaims": 0,
        "n_runtime_theorem_reduction_closure_work_orders": 0,
        "n_full_frontier_theorem_proved": 0,
        "n_formal_gaps": 2,
    }

    ladder = _runtime_capability_ladder(payload)
    rows = {row["level"]: row for row in ladder["levels"]}

    assert ladder["artifact_kind"] == "RuntimeCapabilityLadder"
    assert ladder["max_contiguous_level"] == 6
    assert ladder["max_evidence_level"] == 6
    assert rows[4]["passed"] is True
    assert rows[5]["passed"] is True
    assert rows[6]["passed"] is True
    assert rows[7]["passed"] is False
    assert "no full source/frontier theorem" in rows[7]["blocker"]


def test_runtime_capability_ladder_accepts_proof_body_source_kernel_evidence() -> None:
    payload = {
        "all_ok": True,
        "n_results": 1,
        "n_distinct_question_ids": 1,
        "n_live_generator_agents_enabled": 6,
        "architect_coordinator_enabled": True,
        "n_algorithm_sandbox_executed": 1,
        "n_real_kernel_verified_subclaims": 0,
        "n_runtime_memory_kernel_verified_proof_obligation_ids": 9,
        "n_runtime_memory_kernel_verified_theorem_reduction_closure_goal_ids": 1,
        "n_runtime_memory_kernel_verified_source_theorem_semantic_primitive_ids": 2,
        "n_real_kernel_verified_source_theorem_semantic_primitive_subclaims": 0,
        "n_runtime_theorem_reduction_closure_work_orders": 0,
        "n_full_frontier_theorem_proved": 0,
        "source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified": 1,
        "n_formal_gaps": 0,
    }

    ladder = _runtime_capability_ladder(payload)
    rows = {row["level"]: row for row in ladder["levels"]}

    assert rows[7]["passed"] is True
    assert ladder["max_contiguous_level"] == 7


def test_runtime_audit_resolves_workspace_relative_run_paths(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runs" / "live_runtime"
    runtime_dir.mkdir(parents=True)
    result_path = runtime_dir / "conformal_prediction_coverage_runtime_result.json"
    result_path.write_text("{}", encoding="utf-8")
    manifest = {
        "artifacts": {
            "per_question_results": [
                "runs/live_runtime/conformal_prediction_coverage_runtime_result.json"
            ]
        }
    }

    paths = _resolve_manifest_paths(runtime_dir, manifest)

    assert paths == [result_path]


def test_runtime_topology_resolves_empty_config_model_from_tier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
        "claude-sonnet-topology-test",
    )
    developer = LLMTheoryDeveloperAgent(
        provider=StaticArchitectLLMProvider(_runtime_sample_response()),
        config=ResearchArchitectConfig(provider_name="anthropic"),
    )

    row = _llm_agent_topology_row(
        "TheoryDeveloper",
        developer,
        model_tier="sonnet",
        role="deductive statistical theory discovery",
    )

    assert row["enabled"] is True
    assert row["provider_name"] == "anthropic"
    assert row["backend_provider_name"] == "static"
    assert row["configured_model"] == ""
    assert row["model"] == "claude-sonnet-topology-test"
    assert row["model_tier"] == "sonnet"


def test_runtime_topology_audit_rejects_resolved_claude_tier_policy_violation() -> None:
    topology = {
        "policy_status": "OK",
        "counts": {"unsupported_generator_backends_enabled": 0},
        "policy": {
            "supported_generator_providers": ["anthropic", "openai", "static"],
            "resolved_claude_models_by_tier": {
                "haiku": "claude-sonnet-4-6",
                "sonnet": "claude-sonnet-4-6",
                "opus": "claude-sonnet-4-6",
            },
            "resolved_claude_model_tier_policy_status": "POLICY_VIOLATION",
            "resolved_claude_model_tier_policy_violations": [
                (
                    "Claude cost-aware tier routing collapsed to one resolved "
                    "model (claude-sonnet-4-6)"
                )
            ],
        },
        "llm_agents": [],
    }

    errors = _audit_topology({"llm_runtime_topology": topology})

    assert any(
        "resolved Claude model tier policy status is not OK" in error
        for error in errors
    )
    assert any("collapsed to one resolved model" in error for error in errors)


def test_research_agent_runtime_records_capability_eval_mode_in_manifest() -> None:
    out_dir = Path("runs/test_research_agent_runtime_capability_eval_mode")
    shutil.rmtree(out_dir, ignore_errors=True)
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    developer = LLMTheoryDeveloperAgent(
        provider=StaticArchitectLLMProvider(_runtime_sample_response()),
        config=ResearchArchitectConfig(provider_name="static", model="static-theory-model"),
    )
    architect_coordinator = LLMArchitectCoordinatorAgent(
        provider=StaticArchitectLLMProvider(_architect_sample_response()),
        config=ArchitectCoordinatorConfig(provider_name="static", model="static-architect-model"),
    )

    manifest = run_research_agent_runtime(
        [question],
        out_dir,
        theory_developer=developer,
        architect_coordinator=architect_coordinator,
        config=ResearchAgentRuntimeConfig(
            n_runs=10,
            seed=20260528,
            max_iterations=2,
            llm_timeout_seconds=17.0,
            evaluation_mode="capability_eval",
        ),
    )

    assert manifest["runtime_evaluation_mode"] == "capability_eval"
    assert manifest["config"]["llm_timeout_seconds"] == 17.0
    audit = audit_research_agent_runtime(out_dir, out_dir / "audit")
    scorecard_rows = {
        row["requirement_id"]: row for row in audit["capability_scorecard"]["rows"]
    }
    assert audit["runtime_evaluation_mode"] == "capability_eval"
    assert audit["capability_scorecard"]["runtime_evaluation_mode"] == "capability_eval"
    assert scorecard_rows["runtime_marked_capability_eval"]["passed"] is True
    assert audit["capability_ready_for_full_ai_statistician"] is False


def test_runtime_formalization_gap_planner_bridge_preserves_non_lean_target() -> None:
    bridge = _runtime_formalization_gap_planner_bridge(
        question=OpenResearchQuestion(
            id="q_rocq",
            title="Rocq target theorem",
            description="Plan a reusable Rocq formalization route.",
        ),
        problem=ResearchProblemSpec(
            question_id="q_rocq",
            problem_class="rank statistic",
            dgp="exchangeable observations",
            estimand="rank bound",
            assumptions=("exchangeability",),
            asymptotic_regime="finite sample",
            diagnostics=(),
        ),
        theorem_goals=[
            TheoremGoal(
                id="rank_uniformity",
                title="Rocq rank uniformity",
                informal_statement=(
                    "A rank statistic is uniformly distributed under exchangeability."
                ),
                proof_strategy="Use a Rocq exchangeability lemma and prove a bridge.",
                status="FORMAL_GAP",
                required_primitives=("exchangeability_bridge",),
                proof_obligations=("rocq_rank_uniformity",),
            )
        ],
        subclaims=[
            FormalSubclaim(
                id="subclaim:rank_uniformity",
                title="Rocq rank subclaim",
                status="FAILED",
                claim="Rocq rank bridge needs a library alignment lemma.",
                claim_type="theory_gap",
                proof_obligation_id="rocq_rank_uniformity",
                verifier="Rocq/coq-lsp",
                formal_source_hits=[
                    {
                        "source_id": "rocq_probability",
                        "source_type": "rocq_library",
                        "name": "Rocq.Probability.exchangeable",
                    }
                ],
                primitive_formal_source_hits={
                    "exchangeability_bridge": [
                        {
                            "source_id": "rocq_probability",
                            "source_type": "rocq_library",
                            "declaration": "Rocq.Probability.exchangeable",
                        }
                    ]
                },
            )
        ],
        proof_state_rows=[
            {
                "subclaim_id": "subclaim:rank_uniformity",
                "target_prover_family": "rocq",
                "attempt_status": "target_prover_failed",
                "residual_goals": ["missing finite rank bridge"],
            }
        ],
        retrieval_context={
            "target_prover_family": "rocq",
            "paper_sources": [],
            "knowledge_cards": [],
            "formal_source_hits": [
                {
                    "theorem_goal_id": "rank_uniformity",
                    "hits": [
                        {
                            "source_type": "rocq_library",
                            "name": "Rocq.Probability.exchangeable",
                        }
                    ],
                }
            ],
        },
        formalization_manifest_id="formalization_manifest:rocq",
        proof_state_feedback_manifest_id="proof_state_feedback_manifest:rocq",
    )

    assert bridge["target_prover_family"] == "rocq"
    seed = bridge["standalone_seed"]
    assert seed["target_prover_family"] == "rocq"
    assert validate_standalone_input_payload(seed) == []
    assert seed["routes"][0]["target_prover_family"] == "rocq"
    assert seed["routes"][0]["replan_metadata"]["residual_goals"] == [
        "missing finite rank bridge"
    ]
    assert "lean_declaration_hits" not in seed["routes"][0]["replan_metadata"]
    assert seed["routes"][0]["replan_metadata"]["formal_declaration_hits"] == [
        {
            "source_id": "rocq_probability",
            "source_type": "rocq_library",
            "name": "Rocq.Probability.exchangeable",
            "declaration": "Rocq.Probability.exchangeable",
            "target_prover_family": "rocq",
            "source_field": "runtime_formal_source_hits",
        },
        {
            "primitive": "exchangeability_bridge",
            "source_id": "rocq_probability",
            "source_type": "rocq_library",
            "declaration": "Rocq.Probability.exchangeable",
            "target_prover_family": "rocq",
            "source_field": "runtime_primitive_formal_source_hits",
        },
    ]
    primitive = seed["routes"][0]["primitives"][0]
    assert primitive["candidate_declaration_rows"] == [
        {
            "declaration": "Rocq.Probability.exchangeable",
            "target_prover_family": "rocq",
            "source_field": "runtime_primitive_formal_source_hits",
        }
    ]
    assert bridge["counts"]["candidate_declaration_rows"] == 2
    assert bridge["counts"]["primitives_with_candidate_declaration_rows"] == 2


def test_runtime_target_intake_payload_preserves_mixed_route_targets() -> None:
    bridge = {
        "bridge_id": "runtime_formalization_gap_planner_bridge:mixed_targets",
        "target_prover_family": "rocq",
        "standalone_seed_artifact_id": (
            "runtime_formalization_gap_planner_standalone_seed:mixed_targets"
        ),
        "question": {
            "id": "mixed_target_question",
            "title": "Mixed prover target question",
        },
        "problem": {"problem_class": "distribution_free_prediction"},
        "standalone_seed": {
            "schema_version": 1,
            "component_name": "formalization_gap_planner_standalone_input",
            "library_snapshot_ref": "portable:runtime-mixed-targets",
            "routes": [
                {
                    "route_id": "lean_rank_route",
                    "display_name": "lean_rank_route",
                    "target_prover_family": "lean4",
                    "theorem_statement": "A Lean rank route.",
                    "source_refs": ["runtime fixture"],
                    "primitives": [
                        {
                            "primitive": "exchangeability",
                            "coverage_status": "exact_exists",
                            "candidate_declaration_rows": [
                                {
                                    "declaration": "Probability.exchangeable",
                                    "target_prover_family": "lean4",
                                    "source_field": "runtime_test_fixture",
                                }
                            ],
                        }
                    ],
                },
                {
                    "route_id": "rocq_rank_route",
                    "display_name": "rocq_rank_route",
                    "target_prover_family": "rocq",
                    "theorem_statement": "A Rocq rank route.",
                    "source_refs": ["runtime fixture"],
                    "primitives": [
                        {
                            "primitive": "exchangeability",
                            "coverage_status": "exact_exists",
                            "candidate_declaration_rows": [
                                {
                                    "declaration": "Rocq.Probability.exchangeable",
                                    "target_prover_family": "rocq",
                                    "source_field": "runtime_test_fixture",
                                }
                            ],
                        }
                    ],
                },
            ],
        },
    }

    payload = _runtime_formalization_gap_planner_target_intake_payload(bridge)

    assert payload["target_prover_family"] == "rocq"
    assert [target["target_prover_family"] for target in payload["targets"]] == [
        "lean4",
        "rocq",
    ]
    assert payload["targets"][0]["candidate_primitives"][0][
        "candidate_declaration_rows"
    ][0]["target_prover_family"] == "lean4"
    assert payload["targets"][1]["candidate_primitives"][0][
        "candidate_declaration_rows"
    ][0]["target_prover_family"] == "rocq"

    bridge_without_scalar_target = dict(bridge)
    bridge_without_scalar_target.pop("target_prover_family")
    mixed_payload = _runtime_formalization_gap_planner_target_intake_payload(
        bridge_without_scalar_target
    )
    assert "target_prover_family" not in mixed_payload
    assert [target["target_prover_family"] for target in mixed_payload["targets"]] == [
        "lean4",
        "rocq",
    ]


def test_formal_subclaim_prover_flags_configured_filter_that_excludes_all_candidates() -> None:
    question = load_open_research_questions(Path("examples/research_questions.json"))[1]
    problem = ProblemFormalizer().formalize(question)
    _, theorem_goals = TheoryPlanner().plan(problem)
    prover = FormalSubclaimProver(
        verifier=MockProofVerifier(),
        proof_obligation_ids=("variance_nonneg",),
        max_proof_obligations=1,
    )

    subclaims = asyncio.run(prover.prove(problem, theorem_goals))
    control = prover.proof_obligation_control()

    assert all(row.claim_type != "lean_obligation" for row in subclaims)
    assert any(row.status == "FORMAL_GAP" for row in subclaims)
    assert "prob_measure_univ" in control["candidate_proof_obligation_ids"]
    assert control["configured_proof_obligation_ids"] == ["variance_nonneg"]
    assert control["requested_non_candidate_proof_obligation_ids"] == ["variance_nonneg"]
    assert control["requested_candidate_intersection"] == []
    assert control["proof_selection_filtered_all_candidates"] is True
    assert control["n_selected_proof_obligations"] == 0


def test_research_agent_runtime_rejects_unsupported_generator_provider() -> None:
    out_dir = Path("runs/test_research_agent_runtime_unsupported_provider_policy")
    shutil.rmtree(out_dir, ignore_errors=True)
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    developer = LLMTheoryDeveloperAgent(
        provider=StaticArchitectLLMProvider(_runtime_sample_response()),
        config=ResearchArchitectConfig(provider_name="codex_exec", model="gpt-codex-test"),
    )

    with pytest.raises(ValueError, match="not accepted as pure LLM generator"):
        run_research_agent_runtime(
            [question],
            out_dir,
            theory_developer=developer,
            config=ResearchAgentRuntimeConfig(n_runs=10, seed=20260528, max_iterations=2),
        )


def test_direct_llm_workers_reject_codex_provider_before_backend_call() -> None:
    class BackendThatMustNotBeCalled:
        provider_name = "codex_exec"

        def __init__(self) -> None:
            self.requests = []

        def generate(self, request):
            self.requests.append(request)
            raise AssertionError("agent-style provider backend must not be called")

    question = OpenResearchQuestion(
        id="codex_provider_policy",
        title="Codex provider policy",
        description="Check that direct LLM workers reject agent-style providers.",
        tags=("policy",),
    )
    worker_calls = [
        (
            "TheoryDeveloper",
            lambda backend: LLMTheoryDeveloperAgent(
                provider=backend,
                config=ResearchArchitectConfig(
                    provider_name="codex_exec",
                    model="gpt-codex-test",
                ),
            ).derive(question),
        ),
        (
            "ArchitectCoordinator",
            lambda backend: LLMArchitectCoordinatorAgent(
                provider=backend,
                config=ArchitectCoordinatorConfig(
                    provider_name="codex_exec",
                    model="gpt-codex-test",
                ),
            ).propose(
                question=question,
                architect_context={},
                runtime_config={},
            ),
        ),
        (
            "SimulationEngineer",
            lambda backend: LLMSimulationEngineerAgent(
                provider=backend,
                config=SimulationEngineerConfig(
                    provider_name="codex_exec",
                    model="gpt-codex-test",
                ),
            ).propose(
                question=question,
                theory_packet={},
                registered_problem={},
                registered_procedures=[],
                n_runs=1,
                seed=1,
            ),
        ),
        (
            "AlgorithmEngineer",
            lambda backend: LLMAlgorithmEngineerAgent(
                provider=backend,
                config=AlgorithmEngineerConfig(
                    provider_name="codex_exec",
                    model="gpt-codex-test",
                ),
            ).propose(
                question=question,
                theory_packet={},
                simulation_manifest={},
                implementation_gaps=[],
            ),
        ),
        (
            "FormalizerProofEngineer",
            lambda backend: LLMFormalizerProofEngineerAgent(
                provider=backend,
                config=FormalizerConfig(
                    provider_name="codex_exec",
                    model="gpt-codex-test",
                ),
            ).propose(
                question=question,
                theory_packet={},
                simulation_manifest={},
                algorithm_manifest={},
                registered_problem={},
                theorem_goals=[],
            ),
        ),
        (
            "CriticEvaluator",
            lambda backend: LLMCriticEvaluatorAgent(
                provider=backend,
                config=CriticEvaluatorConfig(
                    provider_name="codex_exec",
                    model="gpt-codex-test",
                ),
            ).propose(
                question=question,
                retrieval_manifest={},
                theory_packet={},
                simulation_manifest={},
                algorithm_manifest={},
                formalization_manifest={},
                deterministic_agenda=[],
                deterministic_learning_rows=[],
            ),
        ),
    ]

    for worker_name, call_worker in worker_calls:
        backend = BackendThatMustNotBeCalled()
        with pytest.raises(ValueError, match="not accepted as pure LLM generator"):
            call_worker(backend)
        assert backend.requests == [], worker_name


def test_research_agent_runtime_rejects_anthropic_model_tier_mismatch() -> None:
    out_dir = Path("runs/test_research_agent_runtime_model_tier_policy")
    shutil.rmtree(out_dir, ignore_errors=True)
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    developer = LLMTheoryDeveloperAgent(
        provider=StaticArchitectLLMProvider(_runtime_sample_response()),
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model="claude-sonnet-4-6",
        ),
    )
    simulation_engineer = LLMSimulationEngineerAgent(
        provider=StaticArchitectLLMProvider(_simulation_sample_response()),
        config=SimulationEngineerConfig(
            provider_name="anthropic",
            model="claude-sonnet-4-6",
        ),
    )

    with pytest.raises(
        ValueError,
        match="SimulationEngineer expected Claude haiku tier",
    ):
        run_research_agent_runtime(
            [question],
            out_dir,
            theory_developer=developer,
            simulation_engineer=simulation_engineer,
            config=ResearchAgentRuntimeConfig(n_runs=10, seed=20260528, max_iterations=2),
        )


def test_research_agent_runtime_cli_capability_eval_rejects_debug_modes() -> None:
    root = Path("runs/test_research_agent_runtime_capability_eval_guard")
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response_file = root / "response.json"
    response_file.write_text(json.dumps(_runtime_sample_response()), encoding="utf-8")

    static_code = main(
        [
            "research-agent-runtime",
            "--capability-eval",
            "--provider",
            "static",
            "--static-response-file",
            str(response_file),
            "--question-file",
            "examples/research_questions.json",
            "--max-questions",
            "1",
            "--local-lean",
            "--out",
            str(root / "static_out"),
        ]
    )
    assert static_code == 2

    no_architect_code = main(
        [
            "research-agent-runtime",
            "--capability-eval",
            "--provider",
            "anthropic",
            "--architect-coordinator-provider",
            "none",
            "--question-file",
            "examples/research_questions.json",
            "--max-questions",
            "1",
            "--local-lean",
            "--out",
            str(root / "no_architect_out"),
        ]
    )
    assert no_architect_code == 2

    manual_filter_code = main(
        [
            "research-agent-runtime",
            "--capability-eval",
            "--provider",
            "anthropic",
            "--question-file",
            "examples/research_questions.json",
            "--max-questions",
            "1",
            "--local-lean",
            "--proof-obligation-id",
            "variance_nonneg",
            "--out",
            str(root / "manual_filter_out"),
        ]
    )
    assert manual_filter_code == 2

    missing_proofengineer_path_code = main(
        [
            "research-agent-runtime",
            "--capability-eval",
            "--provider",
            "anthropic",
            "--architect-coordinator-provider",
            "anthropic",
            "--simulation-engineer-provider",
            "anthropic",
            "--algorithm-engineer-provider",
            "anthropic",
            "--formalizer-provider",
            "anthropic",
            "--critic-evaluator-provider",
            "anthropic",
            "--question-file",
            "examples/research_questions.json",
            "--max-questions",
            "1",
            "--local-lean",
            "--out",
            str(root / "missing_proofengineer_path_out"),
        ]
    )
    assert missing_proofengineer_path_code == 2


def test_research_agent_runtime_cli_static_provider_exports_trace() -> None:
    root = Path("runs/test_research_agent_runtime_cli")
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    response_file = root / "response.json"
    learning_file = root / "runtime_learning_rows.jsonl"
    out_dir = root / "out"
    response_file.write_text(json.dumps(_runtime_sample_response()), encoding="utf-8")
    learning_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "question_id": "prior_frontier_case",
                "learning_task": "proof_boundary_preservation",
                "input_summary": {
                    "formalization_counts": {"formal_gap": 2, "kernel_verified": 0},
                    "trigger": "registered proof rows saturated the search diagnostic",
                },
                "recommended_proof_obligation_ids": [
                    "variance_nonneg",
                    "constant_estimator_unbiased",
                    "not_registered_obligation",
                ],
                "target_behavior": "rerun representative obligations through local Lean before claiming proof evidence",
                "acceptance_gate": "kernel_verified counts only come from local Lean or AXLE verifier rows",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    code = main(
        [
            "research-agent-runtime",
            "--provider",
            "static",
            "--static-response-file",
            str(response_file),
            "--question-file",
            "examples/research_questions.json",
            "--max-questions",
            "1",
            "--runs",
            "80",
            "--learning-memory-jsonl",
            str(learning_file),
            "--max-learning-memory-rows",
            "5",
            "--max-proof-obligations",
            "2",
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    manifest = json.loads((out_dir / "research_agent_runtime_manifest.json").read_text())
    assert manifest["n_questions"] == 1
    assert manifest["runtime_evidence_summary"]["artifact_kind"] == "RuntimeEvidenceSummary"
    completion = manifest["runtime_completion_summary"]
    assert completion["artifact_kind"] == "RuntimeCompletionSummary"
    assert completion["n_questions"] == 1
    assert len(completion["rows"]) == 1
    assert completion["rows"][0]["status"] in manifest["status_counts"]
    assert completion["rows"][0]["last_completed_subsystem"]
    assert "not theorem proof evidence" in completion["boundary"]
    assert manifest["runtime_input_context"]["artifact_kind"] == "RuntimeInputContextSummary"
    assert manifest["runtime_input_context"]["runtime_learning_memory_supplied"] is True
    assert manifest["runtime_input_context"]["runtime_learning_memory_rows_loaded"] == 1
    assert manifest["runtime_evaluation_mode"] == "debug"
    assert str(learning_file) in manifest["runtime_input_context"]["runtime_learning_memory_source_paths"]
    assert "not proof evidence" in manifest["runtime_input_context"]["boundary"]
    assert "n_kernel_verified_subclaims" in manifest
    assert "n_formal_gaps" in manifest
    proof_control = manifest["runtime_evidence_summary"]["proof"]["proof_obligation_control"]
    assert manifest["n_registered_proof_bank_obligation_candidates"] == proof_control[
        "n_registered_proof_bank_obligation_candidates"
    ]
    assert manifest["n_candidate_proof_obligations"] == proof_control["n_candidate_proof_obligations"]
    assert manifest["n_selected_proof_obligations"] == proof_control["n_selected_proof_obligations"]
    assert manifest["n_llm_requested_proof_obligations"] == len(
        proof_control["llm_requested_proof_obligation_ids"]
    )
    assert manifest["n_memory_kernel_verified_proof_obligations"] == len(
        proof_control["memory_kernel_verified_proof_obligation_ids"]
    )
    assert manifest["proof_bank_bridge_catalog_exhausted_by_memory"] == proof_control[
        "proof_bank_bridge_catalog_exhausted_by_memory"
    ]
    assert manifest["theorem_reduction_closure_required"] == proof_control[
        "theorem_reduction_closure_required"
    ]
    assert manifest["remaining_unverified_proof_bank_obligation_ids"] == proof_control[
        "remaining_unverified_proof_bank_obligation_ids"
    ]
    assert manifest["selected_proof_obligation_ids"] == proof_control["selected_proof_obligation_ids"]
    assert proof_control["max_proof_obligations"] == 2
    assert proof_control["n_selected_proof_obligations"] == 4
    assert proof_control["memory_prioritized_proof_obligation_ids"] == ["variance_nonneg"]
    assert proof_control["memory_off_catalog_proof_obligation_ids"] == ["constant_estimator_unbiased"]
    assert proof_control["memory_rejected_proof_obligation_ids"] == ["not_registered_obligation"]
    assert proof_control["prioritized_proof_obligation_ids"] == ["variance_nonneg"]
    assert proof_control["selected_priority_proof_obligation_ids"] == ["variance_nonneg"]
    assert Path(manifest["artifacts"]["runtime_traces_jsonl"]).exists()
    progress_path = Path(manifest["artifacts"]["runtime_progress_jsonl"])
    assert progress_path.exists()
    progress_rows = [
        json.loads(line)
        for line in progress_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert progress_rows[0]["event_type"] == "subsystem_start"
    assert progress_rows[0]["subsystem"] == "RetrievalMemory"
    assert any(row["event_type"] == "subsystem_finish" for row in progress_rows)
    result = json.loads(Path(manifest["artifacts"]["per_question_results"][0]).read_text(encoding="utf-8"))
    learning_context = result["traces"][1]["task"]["inputs"]["architect_context"]["runtime_learning_memory"]
    assert learning_context["artifact_kind"] == "RuntimeLearningMemoryContext"
    assert learning_context["counts"]["rows_loaded"] == 1
    assert "not proof evidence" in learning_context["boundary"]
    assert learning_context["rows"][0]["question_id"] == "prior_frontier_case"
    assert learning_context["rows"][0]["recommended_proof_obligation_ids"] == [
        "variance_nonneg",
        "constant_estimator_unbiased",
        "not_registered_obligation",
    ]
    assert "local Lean before claiming proof evidence" in learning_context["rows"][0]["target_behavior"]
    evidence_types = {row["evidence_type"] for row in result["blackboard"]["evidence_ledger"]}
    assert "runtime_learning_memory" not in evidence_types
    assert "proof_state_feedback" not in evidence_types
    assert "formalization_proof_feedback" in evidence_types
    audit = audit_research_agent_runtime(out_dir, root / "out_audit")
    assert audit["all_ok"] is True
    assert audit["capability_ready_for_full_ai_statistician"] is False
    scorecard = audit["capability_scorecard"]
    scorecard_rows = {row["requirement_id"]: row for row in scorecard["rows"]}
    assert scorecard["runtime_evaluation_mode"] == "debug"
    assert scorecard["ready"] is False
    assert scorecard_rows["runtime_progress_observable"]["passed"] is True
    assert scorecard_rows["runtime_marked_capability_eval"]["passed"] is False
    assert scorecard_rows["architect_orchestrated"]["passed"] is False
    assert scorecard_rows["live_generator_agents_enabled"]["passed"] is False
    assert "no live Anthropic/OpenAI generator agents were enabled" in audit["capability_gaps"]
    assert "ArchitectCoordinator was disabled; this is a subsystem-chain run, not architect-orchestrated research" in audit["capability_gaps"]
    assert audit["llm_topology_policy_ok"] is True
    assert audit["unsupported_generator_backends_enabled"] == 0
    assert audit["has_real_kernel_evidence"] is False
    assert audit["n_results_with_real_kernel_evidence"] == 0
    assert audit["n_real_kernel_verified_subclaims"] == 0
    assert audit["n_non_real_kernel_verified_subclaims"] == 0
    assert audit["n_memory_prioritized_proof_obligations"] == 2
    assert audit["n_memory_off_catalog_proof_obligations"] == 2
    assert audit["n_memory_rejected_proof_obligations"] == 2
    assert audit["n_runtime_progress_events"] >= audit["n_runtime_traces"] * 2
    assert audit["n_results_with_runtime_learning_memory_input"] == 1
    assert audit["n_runtime_learning_memory_input_rows"] == 1

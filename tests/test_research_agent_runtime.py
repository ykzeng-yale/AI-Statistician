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
)
from ai_statistician.critic_evaluator_llm import CriticEvaluatorConfig, LLMCriticEvaluatorAgent
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
    _proof_bank_obligation_request_ids,
    _registered_algorithm_template_hint,
    _runtime_learning_memory_kernel_verified_proof_obligation_ids,
    _runtime_learning_memory_proof_obligation_ids,
    _runtime_formalization_gap_planner_bridge,
    _runtime_formalization_gap_planner_target_intake_payload,
    _run_generated_python_sandbox,
    _run_split_conformal_interval_prototype,
    run_research_agent_runtime,
)
from ai_statistician.research_agent_runtime_audit import audit_research_agent_runtime
from ai_statistician.research_system_audit import _research_agent_runtime_audit_overlay
from ai_statistician.agent_runtime import AgentTask, BlackboardState
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
from ai_statistician.simulation_engineer_llm import LLMSimulationEngineerAgent, SimulationEngineerConfig
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
    assert "variance_nonneg" in prompt
    assert "priority_only_for_kernel_smoke_selection" in prompt
    assert "proof_body" not in prompt


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
    assert control["prioritized_proof_obligation_ids"] == ["event_indicator_expectation"]
    assert control["selected_priority_proof_obligation_ids"] == ["event_indicator_expectation"]
    assert "variance_nonneg" not in control["selected_proof_obligation_ids"]


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
        "--formalization-gap-planner-component-resource-registry-dir"
        in gap_planner_bridge["next_llm_route_planner_prompt_cli"]
    )
    assert "--invoke-provider" not in gap_planner_bridge["next_llm_route_planner_prompt_cli"]
    assert "--invoke-provider" in gap_planner_bridge["next_llm_route_planner_live_cli"]
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
    assert (
        "--formalization-gap-planner-component-resource-registry-dir"
        in handoff["llm_route_planner_prompt_cli"]
    )
    assert "--invoke-provider" not in handoff["llm_route_planner_prompt_cli"]
    assert "--invoke-provider" in handoff["llm_route_planner_live_cli"]
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
        runtime_handoff_audit[
            "n_llm_prompt_requests_with_minimal_delta_cost_hints"
        ]
        == runtime_handoff_audit["n_llm_prompt_packets"]
    )
    assert runtime_handoff_audit["n_llm_prompt_primitive_cost_hints"] > 0
    assert runtime_handoff_audit["n_llm_prompt_route_option_cost_hints"] > 0
    assert runtime_handoff_audit["n_llm_prompt_model_tier_mismatches"] == 0
    assert runtime_handoff_audit["n_seed_candidate_declaration_rows"] > 0
    assert (
        runtime_handoff_audit["n_seed_primitives_with_candidate_declaration_rows"] > 0
    )
    assert all(
        summary["seed_candidate_declaration_rows"] > 0
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
    assert "Component-resource registry smoke OK:" in runtime_handoff_report
    assert "Registry context in prompts:" in runtime_handoff_report
    assert "Minimal-delta cost hints in prompts:" in runtime_handoff_report
    assert "LLM prompt model-tier mismatches:" in runtime_handoff_report
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
    assert audit["capability_ready_for_full_ai_statistician"] is False
    assert audit["capability_status"] == "CONTRACT_OK_WITH_CAPABILITY_GAPS"
    scorecard = audit["capability_scorecard"]
    scorecard_rows = {row["requirement_id"]: row for row in scorecard["rows"]}
    assert scorecard["artifact_kind"] == "RuntimeCapabilityScorecard"
    assert scorecard["runtime_evaluation_mode"] == "debug"
    assert scorecard["ready"] is False
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

    with pytest.raises(ValueError, match="LLM topology policy violation"):
        run_research_agent_runtime(
            [question],
            out_dir,
            theory_developer=developer,
            config=ResearchAgentRuntimeConfig(n_runs=10, seed=20260528, max_iterations=2),
        )


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
    assert manifest["runtime_input_context"]["artifact_kind"] == "RuntimeInputContextSummary"
    assert manifest["runtime_input_context"]["runtime_learning_memory_supplied"] is True
    assert manifest["runtime_input_context"]["runtime_learning_memory_rows_loaded"] == 1
    assert manifest["runtime_evaluation_mode"] == "debug"
    assert str(learning_file) in manifest["runtime_input_context"]["runtime_learning_memory_source_paths"]
    assert "not proof evidence" in manifest["runtime_input_context"]["boundary"]
    assert "n_kernel_verified_subclaims" in manifest
    assert "n_formal_gaps" in manifest
    proof_control = manifest["runtime_evidence_summary"]["proof"]["proof_obligation_control"]
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

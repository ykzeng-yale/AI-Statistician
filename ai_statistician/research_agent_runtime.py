from __future__ import annotations

import asyncio
import ast
import json
import math
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    ToolCallRecord,
)
from .architect_coordinator_llm import (
    ARCHITECT_COORDINATOR_BOUNDARY,
    ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE,
    LLMArchitectCoordinatorAgent,
)
from .algorithm_engineer_llm import (
    ALGORITHM_ENGINEER_BOUNDARY,
    ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
    LLMAlgorithmEngineerAgent,
)
from .critic_evaluator_llm import (
    CRITIC_EVALUATOR_BOUNDARY,
    CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE,
    LLMCriticEvaluatorAgent,
)
from .fingerprint import stable_hash
from .formal_verifier_agentic_proof_execution_artifact_verifier import (
    export_formal_verifier_agentic_proof_execution_artifact_verifier,
)
from .formal_verifier_agentic_proof_execution_materializer import (
    export_formal_verifier_agentic_proof_execution_materializer,
)
from .formal_verifier_agentic_proof_source_theorem_promotion_queue import (
    export_formal_verifier_agentic_proof_source_theorem_promotion_queue,
)
from .formal_verifier_agentic_proof_source_theorem_integrator import (
    export_formal_verifier_agentic_proof_source_theorem_integrator,
)
from .exact_source_theorem_proof_body_executor import (
    export_exact_source_theorem_proof_body_execution_results,
)
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
)
from .formalizer_llm import (
    FORMALIZER_BOUNDARY,
    FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE,
    LLMFormalizerProofEngineerAgent,
)
from .model_backend import (
    ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
    CLAUDE_MODEL_TIERS,
    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    SUPPORTED_LIVE_GENERATOR_PROVIDERS,
    claude_model_freshness_warnings,
    claude_model_tier_mismatch,
    claude_model_tier_policy_violations,
    resolve_generator_model,
)
from .formal_source_index import FormalSourceHit, FormalSourceRetriever
from .proof_bank import get_obligation
from .proof_state_feedback import (
    PROOF_STATE_FEEDBACK_BOUNDARY,
    ProofStateFeedbackProvider,
    proof_state_feedback_row_to_json,
)
from .research_architect import (
    KERNEL_PROOF_BOUNDARY,
    LLMTheoryDeveloperAgent,
    THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
)
from .research_lab import FormalSubclaimProver, ProblemFormalizer, ResearchSimulator, TheoryPlanner
from .research_knowledge import retrieve_problem_knowledge
from .research_paper_index import retrieve_paper_sources
from .research_schema import (
    CandidateProcedure,
    FormalSubclaim,
    KnowledgeCard,
    OpenResearchQuestion,
    PaperSourceHit,
    ResearchProblemSpec,
    ResearchSimulation,
    TheoremGoal,
)
from .simulation_engineer_llm import (
    LLMSimulationEngineerAgent,
    SIMULATION_ENGINEER_BOUNDARY,
    SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
)
from .source_theorem_semantic_primitive_proofengineer_bridge import (
    run_source_theorem_semantic_primitive_proofengineer_bridge,
)
from .source_theorem_formal_environment_proofengineer_bridge import (
    run_source_theorem_formal_environment_proofengineer_bridge,
)
from .theorem_reduction_closure_proofengineer_bridge import (
    run_theorem_reduction_closure_proofengineer_bridge,
)
from .verifier import ProofVerifier


RUNTIME_SCHEMA_VERSION = 1
SIMULATION_NOT_PROOF_BOUNDARY = (
    "Executable simulation and deterministic scaffold runs are empirical "
    "environment observations. They can falsify or support a proposal, but "
    "they are not theorem proof evidence."
)
RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE = (
    "RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE"
)
RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY = (
    "Runtime formalization gap planner bridge artifacts are planner input "
    "seeds derived from AI Statistician runtime retrieval, formalization, and "
    "proof-state feedback. They are not theorem proof evidence and do not "
    "claim that any route is minimal until the standalone planner, audits, and "
    "target-prover replay run."
)


@dataclass(frozen=True)
class ResearchAgentRuntimeConfig:
    n_runs: int = 100
    seed: int = 20260528
    max_iterations: int = 12
    max_subsystem_retries: int = 1
    max_critic_repair_rounds: int = 1
    proof_obligation_ids: tuple[str, ...] = ()
    max_proof_obligations: int = 0
    llm_timeout_seconds: float = DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS
    evaluation_mode: str = "debug"
    theorem_closure_proofengineer_bridge: bool = False
    theorem_closure_proofengineer_local_lean: bool = False
    theorem_closure_proofengineer_lean_project: str = ""
    theorem_closure_proofengineer_lean_timeout: int = 240
    source_semantic_proofengineer_bridge: bool = False
    source_semantic_proofengineer_local_lean: bool = False
    source_semantic_proofengineer_lean_project: str = ""
    source_semantic_proofengineer_lean_timeout: int = 90
    source_theorem_formal_environment_proofengineer_bridge: bool = False
    source_theorem_formal_environment_proofengineer_signature_probes: bool = False
    source_theorem_formal_environment_proofengineer_execute_proof_body: bool = False
    source_theorem_formal_environment_proofengineer_proof_body_local_lean: bool = False
    source_theorem_formal_environment_proofengineer_proof_body_overwrite_artifacts: bool = False
    source_theorem_formal_environment_proofengineer_lean_project: str = ""
    source_theorem_formal_environment_proofengineer_lean_timeout: int = 90
    source_theorem_promotion_proofengineer_bridge: bool = False
    source_theorem_promotion_proofengineer_local_lean: bool = False
    source_theorem_promotion_proofengineer_overwrite_artifacts: bool = False
    source_theorem_promotion_proofengineer_lean_project: str = ""
    source_theorem_promotion_proofengineer_lean_timeout: int = 90


def _run_runtime_source_theorem_formal_environment_bridge_stack(
    *,
    out_dir: Path,
    queue_jsonl: Path | None,
    question_id: str,
    config: ResearchAgentRuntimeConfig,
) -> tuple[
    dict[str, Any] | None,
    dict[str, Any] | None,
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    if (
        not config.source_theorem_formal_environment_proofengineer_bridge
        or queue_jsonl is None
    ):
        return None, None, [], []
    bridge_manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=out_dir,
        queue_jsonl=queue_jsonl,
        question_id=question_id,
        run_signature_probes=(
            config.source_theorem_formal_environment_proofengineer_signature_probes
        ),
        lean_project=(
            Path(config.source_theorem_formal_environment_proofengineer_lean_project)
            if config.source_theorem_formal_environment_proofengineer_lean_project
            else None
        ),
        lean_timeout=config.source_theorem_formal_environment_proofengineer_lean_timeout,
    )
    proof_body_executor_manifest: dict[str, Any] | None = None
    n_proof_body_execution_queue_rows = int(
        bridge_manifest.get("n_proof_body_execution_queue_rows", 0) or 0
    )
    if (
        config.source_theorem_formal_environment_proofengineer_execute_proof_body
        and bridge_manifest.get("proof_body_execution_queue_manifest")
        and n_proof_body_execution_queue_rows > 0
    ):
        proof_body_execution_queue_dir = Path(
            str(bridge_manifest["proof_body_execution_queue_manifest"])
        ).parent
        proof_body_executor_manifest = export_exact_source_theorem_proof_body_execution_results(
            proof_body_execution_queue_dir,
            out_dir=out_dir.parent
            / (out_dir.name.replace("proofengineer_bridge", "proof_body_executor")),
            overwrite=(
                config.source_theorem_formal_environment_proofengineer_proof_body_overwrite_artifacts
            ),
            local_lean=(
                config.source_theorem_formal_environment_proofengineer_proof_body_local_lean
            ),
            lean_project=(
                Path(config.source_theorem_formal_environment_proofengineer_lean_project)
                if config.source_theorem_formal_environment_proofengineer_lean_project
                else None
            ),
            lean_timeout=config.source_theorem_formal_environment_proofengineer_lean_timeout,
        )
    bridge_learning_rows = _runtime_source_theorem_formal_environment_bridge_learning_rows(
        bridge_manifest
    )
    proof_body_executor_learning_rows = (
        _runtime_source_theorem_formal_environment_proof_body_executor_learning_rows(
            proof_body_executor_manifest
        )
        if proof_body_executor_manifest is not None
        else []
    )
    return (
        bridge_manifest,
        proof_body_executor_manifest,
        bridge_learning_rows,
        proof_body_executor_learning_rows,
    )


class ArchitectCoordinatorRuntimeSubsystem:
    name = "ArchitectCoordinator"

    def __init__(
        self,
        *,
        coordinator: LLMArchitectCoordinatorAgent,
        runtime_config: ResearchAgentRuntimeConfig,
    ) -> None:
        self.coordinator = coordinator
        self.runtime_config = runtime_config

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        packet = self.coordinator.propose(
            question=question,
            architect_context=context,
            runtime_config=asdict(self.runtime_config),
        )
        packet_id = str(packet["packet_id"])
        context["architect_coordinator_proposal_id"] = packet_id
        context["architect_runtime_plan"] = {
            "subsystem_execution_plan": packet.get("subsystem_execution_plan", []),
            "problem_analysis": packet.get("problem_analysis", {}),
            "stat_knowledge_bank_plan": packet.get("stat_knowledge_bank_plan", {}),
            "literature_fair_comparison_plan": packet.get("literature_fair_comparison_plan", []),
            "retrieval_strategy": packet.get("retrieval_strategy", {}),
            "iteration_policy": packet.get("iteration_policy", {}),
            "evidence_gates": packet.get("evidence_gates", []),
            "boundary": packet.get("evidence_boundary", ARCHITECT_COORDINATOR_BOUNDARY),
        }
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, packet_id])[:20],
            task_id=task.task_id,
            artifact_id=packet_id,
            evidence_type="llm_architect_coordinator_proposal",
            status="PROPOSAL_RECORDED_REQUIRES_RUNTIME_EXECUTION",
            boundary=ARCHITECT_COORDINATOR_BOUNDARY,
            payload={
                "n_subsystem_steps": len(packet.get("subsystem_execution_plan", []) or []),
                "runtime_executed": False,
                "proof_evidence_status": ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE,
            },
        )
        return AgentStepResult(
            status="REROUTE",
            rationale=(
                "ArchitectCoordinator recorded a top-level execution plan and "
                "is routing to RetrievalMemory for source and formal context."
            ),
            produced_artifacts={packet_id: packet},
            observations=(
                EnvironmentObservation(
                    observation_type="llm_architect_coordinator_proposal",
                    summary="validated ArchitectCoordinator execution plan recorded",
                    payload={
                        "packet_id": packet_id,
                        "n_subsystem_steps": len(packet.get("subsystem_execution_plan", []) or []),
                        "proof_evidence_status": ARCHITECT_COORDINATOR_PROPOSAL_NOT_EVIDENCE,
                    },
                ),
            ),
            evidence_entries=(evidence,),
            next_task=AgentTask(
                task_id=f"retrieve:{question.id}:{stable_hash(packet_id)[:8]}",
                owner_subsystem="RetrievalMemory",
                objective="Retrieve paper, statistical knowledge, and formal-source context before theory derivation.",
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": context,
                },
                allowed_tools=("research_knowledge", "paper_index", "formal_source_retriever"),
                expected_artifacts=("retrieval_memory_manifest",),
                acceptance_gate="retrieval context recorded with explicit non-proof boundary",
                stop_condition="retrieval context routed to TheoryDeveloper",
            ),
        )


class RetrievalMemoryRuntimeSubsystem:
    name = "RetrievalMemory"

    def __init__(self, *, formal_source_retriever: Any | None = None) -> None:
        self.formal_source_retriever = formal_source_retriever or FormalSourceRetriever()

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        retrieval_control = _architect_control_payload(context, "RetrievalMemory")
        problem = ProblemFormalizer().formalize(question)
        _procedures, theorem_goals = TheoryPlanner().plan(problem)
        knowledge = retrieve_problem_knowledge(question, problem, theorem_goals, k=8)
        paper_sources = retrieve_paper_sources(question, problem, theorem_goals, k=5)
        formal_hits = _runtime_formal_source_hits(
            self.formal_source_retriever,
            problem=problem,
            theorem_goals=theorem_goals,
            k=4,
        )
        manifest_id = "retrieval_memory_manifest:" + stable_hash([task.task_id, question.id, formal_hits])[:20]
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeRetrievalMemoryManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "runtime_architect_control": retrieval_control,
            "problem": _problem_to_json(problem),
            "theorem_goals": [_theorem_goal_to_json(row) for row in theorem_goals],
            "knowledge_cards": [_knowledge_card_to_json(row) for row in knowledge],
            "paper_sources": [_paper_source_to_json(row) for row in paper_sources],
            "formal_source_hits": formal_hits,
            "counts": {
                "knowledge_cards": len(knowledge),
                "paper_sources": len(paper_sources),
                "formal_source_hit_groups": len(formal_hits),
                "formal_source_hits": sum(len(row.get("hits", [])) for row in formal_hits),
            },
            "boundary": (
                "Retrieval memory supplies source, analogy, and Lean declaration context. "
                "Retrieval hits are not proof evidence and must be checked by downstream gates."
            ),
        }
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="retrieval_memory",
            status="RETRIEVAL_CONTEXT_RECORDED",
            boundary=str(manifest["boundary"]),
            payload={
                **manifest["counts"],
                "architect_acceptance_gate": retrieval_control.get("acceptance_gate", ""),
            },
        )
        context["retrieval_memory_manifest_id"] = manifest_id
        context["retrieval_context"] = {
            "knowledge_cards": manifest["knowledge_cards"],
            "paper_sources": manifest["paper_sources"],
            "formal_source_hits": manifest["formal_source_hits"],
            "boundary": manifest["boundary"],
        }
        return AgentStepResult(
            status="REROUTE",
            rationale="Runtime retrieval memory recorded paper, knowledge, and formal-source context for TheoryDeveloper.",
            produced_artifacts={manifest_id: manifest},
            observations=(
                EnvironmentObservation(
                    observation_type="retrieval_memory",
                    summary=(
                        f"knowledge={len(knowledge)} papers={len(paper_sources)} "
                        f"formal_hit_groups={len(formal_hits)}"
                    ),
                    payload=manifest["counts"],
                ),
            ),
            evidence_entries=(evidence,),
            next_task=AgentTask(
                task_id=f"theory:{question.id}:{stable_hash(manifest_id)[:8]}",
                owner_subsystem="TheoryDeveloper",
                objective="Derive a statistical theory proposal using retrieval memory context.",
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": context,
                },
                allowed_tools=("model_backend", "rag_memory"),
                expected_artifacts=_architect_expected_artifacts(
                    context,
                    "TheoryDeveloper",
                    ("theory_derivation_packet",),
                ),
                acceptance_gate=_architect_acceptance_gate(
                    context,
                    "TheoryDeveloper",
                    "validated theory packet with proof boundary and retrieval context",
                ),
                stop_condition="theory packet routed to simulation feedback",
            ),
        )


class TheoryDeveloperRuntimeSubsystem:
    name = "TheoryDeveloper"

    def __init__(
        self,
        *,
        theory_developer: LLMTheoryDeveloperAgent,
        n_runs: int,
        seed: int,
    ) -> None:
        self.theory_developer = theory_developer
        self.n_runs = n_runs
        self.seed = seed

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        context["runtime_task"] = _runtime_task_prompt_summary(task)
        if "environment_feedback" in task.inputs:
            context["environment_feedback"] = task.inputs["environment_feedback"]
        packet = self.theory_developer.derive(question, architect_context=context)
        theory_control = _architect_control_payload(context, "TheoryDeveloper")
        packet["runtime_architect_control"] = theory_control
        packet_id = _unique_runtime_artifact_id(
            blackboard,
            str(packet["packet_id"]),
            task_id=task.task_id,
        )
        if packet_id != str(packet["packet_id"]):
            packet = dict(packet)
            packet["base_packet_id"] = str(packet["packet_id"])
            packet["packet_id"] = packet_id
            packet["runtime_revision_artifact"] = True
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, packet_id])[:20],
            task_id=task.task_id,
            artifact_id=packet_id,
            evidence_type="llm_theory_derivation",
            status="PROPOSAL_RECORDED_REQUIRES_GATES",
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
                "kernel_verified": False,
                "architect_acceptance_gate": theory_control.get("acceptance_gate", ""),
            },
        )
        next_task = AgentTask(
            task_id=f"simulation:{question.id}:{stable_hash(packet_id)[:8]}",
            owner_subsystem="SimulationEvaluator",
            objective=(
                "Evaluate the LLM theory proposal against executable registered "
                "simulation environments and record implementation gaps."
            ),
            inputs={
                "question": _question_to_payload(question),
                "theory_packet_id": packet_id,
                "architect_context": context,
                "n_runs": self.n_runs,
                "seed": self.seed,
            },
            allowed_tools=("research_simulator", "python"),
            expected_artifacts=_architect_expected_artifacts(
                context,
                "SimulationEvaluator",
                ("simulation_manifest", "implementation_gap_manifest"),
            ),
            acceptance_gate=_architect_acceptance_gate(
                context,
                "SimulationEvaluator",
                "simulation manifest plus explicit proof/implementation boundaries",
            ),
            stop_condition="simulation diagnostics recorded or rerouted to TheoryDeveloper",
        )
        return AgentStepResult(
            status="REROUTE",
            rationale="LLM TheoryDeveloper produced a proposal; runtime is routing it to executable simulation feedback.",
            produced_artifacts={packet_id: packet},
            observations=(
                EnvironmentObservation(
                    observation_type="llm_theory_derivation_packet",
                    summary="validated LLM theory proposal recorded for downstream gates",
                    payload={
                        "packet_id": packet_id,
                        "n_theorem_cards": len(packet.get("theorem_cards", []) or []),
                        "n_estimator_specs": len(packet.get("estimator_specs", []) or []),
                        "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
                    },
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
        )


class SimulationEvaluatorRuntimeSubsystem:
    name = "SimulationEvaluator"

    def __init__(self, *, proposal_agent: LLMSimulationEngineerAgent | None = None) -> None:
        self.proposal_agent = proposal_agent

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        simulation_control = _architect_control_payload(context, "SimulationEvaluator")
        packet_id = str(task.inputs.get("theory_packet_id", ""))
        packet = blackboard.artifacts.get(packet_id, {})
        problem = ProblemFormalizer().formalize(question)
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        n_runs = int(task.inputs.get("n_runs", 100))
        seed = int(task.inputs.get("seed", 20260528))
        proposal_packet: dict[str, Any] | None = None
        produced_artifacts: dict[str, Any] = {}
        proposal_evidence: EvidenceLedgerEntry | None = None
        observations: list[EnvironmentObservation] = [
            EnvironmentObservation(
                observation_type="deterministic_problem_formalization",
                summary=f"problem_class={problem.problem_class}",
                payload={
                    "problem_class": problem.problem_class,
                    "estimand": problem.estimand,
                    "diagnostics": list(problem.diagnostics),
                },
            )
        ]
        if self.proposal_agent is not None:
            proposal_packet = self.proposal_agent.propose(
                question=question,
                theory_packet=packet if isinstance(packet, Mapping) else {},
                registered_problem=_problem_to_json(problem),
                registered_procedures=[_procedure_to_json(row) for row in procedures],
                n_runs=n_runs,
                seed=seed,
            )
            proposal_id = str(proposal_packet["packet_id"])
            produced_artifacts[proposal_id] = proposal_packet
            observations.append(
                EnvironmentObservation(
                    observation_type="llm_simulation_engineer_proposal",
                    summary=(
                        "validated LLM SimulatorEngineer proposal recorded before "
                        "registered simulator execution"
                    ),
                    payload={
                        "packet_id": proposal_id,
                        "n_dgp_plan_rows": len(proposal_packet.get("dgp_plan", []) or []),
                        "n_stress_tests": len(proposal_packet.get("stress_tests", []) or []),
                        "simulation_evidence_status": SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
                    },
                )
            )
            proposal_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:" + stable_hash([task.task_id, proposal_id])[:20],
                task_id=task.task_id,
                artifact_id=proposal_id,
                evidence_type="llm_simulation_engineer_proposal",
                status="PROPOSAL_RECORDED_REQUIRES_RUNTIME_EXECUTION",
                boundary=SIMULATION_ENGINEER_BOUNDARY,
                payload={
                    "n_dgp_plan_rows": len(proposal_packet.get("dgp_plan", []) or []),
                    "n_stress_tests": len(proposal_packet.get("stress_tests", []) or []),
                    "simulations_executed": False,
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                },
            )
        simulations = ResearchSimulator(n_runs=n_runs, seed=seed).run(problem, procedures)
        simulation_passed = bool(simulations) and all(row.passed for row in simulations)
        implementation_gaps = _implementation_gaps(packet, procedures)
        manifest_id = "simulation_manifest:" + stable_hash([task.task_id, packet_id, n_runs, seed])[:20]
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeSimulationManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "theory_packet_id": packet_id,
            "runtime_architect_control": simulation_control,
            "llm_simulation_engineer_proposal_id": (
                str(proposal_packet.get("packet_id", "")) if proposal_packet else ""
            ),
            "problem": _problem_to_json(problem),
            "registered_procedures": [_procedure_to_json(row) for row in procedures],
            "theorem_goals": [_theorem_goal_to_json(row) for row in theorem_goals],
            "simulations": [_simulation_to_json(row) for row in simulations],
            "simulation_passed": simulation_passed,
            "implementation_gaps": implementation_gaps,
            "proof_evidence_status": "SIMULATION_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": SIMULATION_NOT_PROOF_BOUNDARY,
        }
        produced_artifacts[manifest_id] = manifest
        observations.append(
            EnvironmentObservation(
                observation_type="simulation_result",
                summary=f"simulations={len(simulations)} passed={simulation_passed}",
                payload={
                    "n_simulations": len(simulations),
                    "simulation_passed": simulation_passed,
                    "procedure_ids": [row.procedure_id for row in simulations],
                    "failed_procedure_ids": [row.procedure_id for row in simulations if not row.passed],
                },
            )
        )
        if implementation_gaps:
            observations.append(
                EnvironmentObservation(
                    observation_type="implementation_gap",
                    summary="LLM estimator specs are not yet executable registered algorithms.",
                    payload={"implementation_gaps": implementation_gaps},
                )
            )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="simulation",
            status="EXECUTED_REPRODUCIBLY" if simulations else "NO_EXECUTABLE_SIMULATION",
            boundary=SIMULATION_NOT_PROOF_BOUNDARY,
            payload={
                "n_runs": n_runs,
                "seed": seed,
                "simulation_passed": simulation_passed,
                "architect_acceptance_gate": simulation_control.get("acceptance_gate", ""),
            },
        )
        if simulation_passed:
            if implementation_gaps:
                next_task = AgentTask(
                    task_id=f"algorithm:{question.id}:{stable_hash([packet_id, manifest_id])[:8]}",
                    owner_subsystem="AlgorithmEngineer",
                    objective=(
                        "Build and run sandbox prototypes for LLM estimator specs "
                        "that do not yet have registered executable algorithms."
                    ),
                    inputs={
                        "question": _question_to_payload(question),
                        "theory_packet_id": packet_id,
                        "simulation_manifest_id": manifest_id,
                        "implementation_gaps": implementation_gaps,
                        "n_runs": n_runs,
                        "seed": seed,
                        "architect_context": context,
                    },
                    allowed_tools=("python", "filesystem_sandbox"),
                    expected_artifacts=_architect_expected_artifacts(
                        context,
                        "AlgorithmEngineer",
                        ("algorithm_sandbox_manifest",),
                    ),
                    acceptance_gate=_architect_acceptance_gate(
                        context,
                        "AlgorithmEngineer",
                        "sandbox prototype executed or explicit unsupported-prototype gap recorded",
                    ),
                    stop_condition="algorithm sandbox feedback recorded",
                )
            else:
                next_task = _formalization_task(
                    question=question,
                    packet_id=packet_id,
                    simulation_manifest_id=manifest_id,
                    architect_context=context,
                )
            return AgentStepResult(
                status="REROUTE",
                rationale=(
                    "Runtime recorded executable simulation feedback and is routing "
                    "remaining implementation/formalization feedback through the agent runtime."
                ),
                produced_artifacts=produced_artifacts,
                observations=tuple(observations),
                tool_calls=(
                    ToolCallRecord(
                        tool_name="ResearchSimulator.run",
                        inputs={"n_runs": n_runs, "seed": seed, "n_procedures": len(procedures)},
                        exit_status="0",
                        stdout_summary=f"{len(simulations)} simulation rows recorded",
                        safety_boundary=SIMULATION_NOT_PROOF_BOUNDARY,
                    ),
                ),
                evidence_entries=tuple(row for row in (proposal_evidence, evidence) if row is not None),
                next_task=next_task,
            )
        feedback = {
            "simulation_manifest_id": manifest_id,
            "simulation_passed": simulation_passed,
            "failed_simulations": [
                _simulation_to_json(row)
                for row in simulations
                if not row.passed
            ],
            "implementation_gaps": implementation_gaps,
            "boundary": SIMULATION_NOT_PROOF_BOUNDARY,
        }
        revision_context = dict(context)
        revision_context["previous_theory_packet_id"] = packet_id
        next_task = AgentTask(
            task_id=f"theory-revise:{question.id}:{stable_hash(feedback)[:8]}",
            owner_subsystem="TheoryDeveloper",
            objective="Revise theorem/procedure proposal using executable simulation feedback.",
            inputs={
                "question": _question_to_payload(question),
                "architect_context": revision_context,
                "environment_feedback": feedback,
            },
            expected_artifacts=("revised_theory_derivation_packet",),
            acceptance_gate="revised packet must address failed simulation diagnostics",
            stop_condition="proposal revised or blocker classified",
        )
        return AgentStepResult(
            status="REVISE",
            rationale="Simulation did not pass; runtime is routing feedback back to TheoryDeveloper.",
            produced_artifacts=produced_artifacts,
            observations=tuple(observations),
            tool_calls=(
                ToolCallRecord(
                    tool_name="ResearchSimulator.run",
                    inputs={"n_runs": n_runs, "seed": seed, "n_procedures": len(procedures)},
                    exit_status="0",
                    stdout_summary=f"{len(simulations)} simulation rows recorded",
                    safety_boundary=SIMULATION_NOT_PROOF_BOUNDARY,
                ),
            ),
            evidence_entries=tuple(row for row in (proposal_evidence, evidence) if row is not None),
            next_task=next_task,
            failure_classification="simulation_diagnostic_failure",
        )


class AlgorithmEngineerRuntimeSubsystem:
    name = "AlgorithmEngineer"

    def __init__(
        self,
        *,
        out_dir: Path,
        n_runs: int,
        seed: int,
        proposal_agent: LLMAlgorithmEngineerAgent | None = None,
        timeout_s: int = 60,
    ) -> None:
        self.out_dir = out_dir
        self.n_runs = n_runs
        self.seed = seed
        self.proposal_agent = proposal_agent
        self.timeout_s = timeout_s

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        algorithm_control = _architect_control_payload(context, "AlgorithmEngineer")
        packet_id = str(task.inputs.get("theory_packet_id", ""))
        packet = blackboard.artifacts.get(packet_id, {})
        simulation_manifest_id = str(task.inputs.get("simulation_manifest_id", ""))
        simulation_manifest = blackboard.artifacts.get(simulation_manifest_id, {})
        implementation_gaps = [
            row for row in task.inputs.get("implementation_gaps", []) or [] if isinstance(row, Mapping)
        ]
        proposal_packet: dict[str, Any] | None = None
        proposal_evidence: EvidenceLedgerEntry | None = None
        produced_artifacts: dict[str, Any] = {}
        observations: list[EnvironmentObservation] = []
        if self.proposal_agent is not None and implementation_gaps:
            proposal_packet = self.proposal_agent.propose(
                question=question,
                theory_packet=packet if isinstance(packet, Mapping) else {},
                simulation_manifest=simulation_manifest if isinstance(simulation_manifest, Mapping) else {},
                implementation_gaps=implementation_gaps,
            )
            proposal_id = str(proposal_packet["packet_id"])
            produced_artifacts[proposal_id] = proposal_packet
            observations.append(
                EnvironmentObservation(
                    observation_type="llm_algorithm_engineer_proposal",
                    summary=(
                        "validated LLM AlgorithmEngineer proposal recorded before "
                        "runtime sandbox execution"
                    ),
                    payload={
                        "packet_id": proposal_id,
                        "n_implementation_targets": len(
                            proposal_packet.get("implementation_targets", []) or []
                        ),
                        "execution_evidence_status": ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
                    },
                )
            )
            proposal_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:" + stable_hash([task.task_id, proposal_id])[:20],
                task_id=task.task_id,
                artifact_id=proposal_id,
                evidence_type="llm_algorithm_engineer_proposal",
                status="PROPOSAL_RECORDED_REQUIRES_SANDBOX",
                boundary=ALGORITHM_ENGINEER_BOUNDARY,
                payload={
                    "n_implementation_targets": len(
                        proposal_packet.get("implementation_targets", []) or []
                    ),
                    "sandbox_executed": False,
                    "production_registered": False,
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                },
            )
        sandbox_dir = self.out_dir / _safe_identifier(question.id) / stable_hash([task.task_id, packet_id])[:12]
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        prototype_rows: list[dict[str, Any]] = []
        tool_calls: list[ToolCallRecord] = []
        for gap in implementation_gaps:
            estimator_id = str(gap.get("estimator_id", ""))
            spec = _estimator_spec(packet, estimator_id)
            proposal_target = _algorithm_proposal_for_estimator(proposal_packet, estimator_id)
            code_draft = _algorithm_code_draft_for_estimator(proposal_packet, estimator_id)
            template_hint = _registered_algorithm_template_hint(
                proposal_target=proposal_target,
                spec=spec,
                question=question,
            )
            if estimator_id == "crossfit_aipw" or template_hint == "crossfit_aipw":
                prototype, tool_call = _run_crossfit_aipw_prototype(
                    sandbox_dir=sandbox_dir,
                    estimator_id=estimator_id,
                    spec=spec,
                    n_runs=int(task.inputs.get("n_runs", self.n_runs) or self.n_runs),
                    seed=int(task.inputs.get("seed", self.seed) or self.seed),
                    timeout_s=self.timeout_s,
                )
                prototype["llm_algorithm_engineer_target"] = proposal_target
                prototype_rows.append(prototype)
                tool_calls.append(tool_call)
            elif template_hint == "split_conformal_interval":
                prototype, tool_call = _run_split_conformal_interval_prototype(
                    sandbox_dir=sandbox_dir,
                    estimator_id=estimator_id,
                    spec=spec,
                    n_runs=int(task.inputs.get("n_runs", self.n_runs) or self.n_runs),
                    seed=int(task.inputs.get("seed", self.seed) or self.seed),
                    timeout_s=self.timeout_s,
                )
                prototype["llm_algorithm_engineer_target"] = proposal_target
                prototype_rows.append(prototype)
                tool_calls.append(tool_call)
            elif code_draft:
                prototype, tool_call = _run_generated_python_sandbox(
                    sandbox_dir=sandbox_dir,
                    estimator_id=estimator_id,
                    spec=spec,
                    code_draft=code_draft,
                    n_runs=int(task.inputs.get("n_runs", self.n_runs) or self.n_runs),
                    seed=int(task.inputs.get("seed", self.seed) or self.seed),
                    timeout_s=self.timeout_s,
                )
                prototype["llm_algorithm_engineer_target"] = proposal_target
                prototype_rows.append(prototype)
                tool_calls.append(tool_call)
            else:
                prototype_rows.append(
                    {
                        "estimator_id": estimator_id,
                        "prototype_status": "UNSUPPORTED_SANDBOX_TEMPLATE",
                        "spec": dict(spec),
                        "reason": "No sandbox implementation template is registered for this estimator id.",
                        "promotion_ready": False,
                        "llm_algorithm_engineer_target": proposal_target,
                    }
                )
        manifest_id = "algorithm_sandbox_manifest:" + stable_hash([task.task_id, prototype_rows])[:20]
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeAlgorithmSandboxManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "runtime_architect_control": algorithm_control,
            "llm_algorithm_engineer_proposal_id": (
                str(proposal_packet.get("packet_id", "")) if proposal_packet else ""
            ),
            "prototypes": prototype_rows,
            "n_prototypes": len(prototype_rows),
            "n_executed": sum(1 for row in prototype_rows if row.get("prototype_status") == "EXECUTED"),
            "n_passed": sum(1 for row in prototype_rows if row.get("smoke_passed") is True),
            "n_generated_code_executed": sum(
                1
                for row in prototype_rows
                if row.get("executor") == "generated_python_sandbox"
                and row.get("prototype_status") == "EXECUTED"
            ),
            "n_unsafe_generated_code_rejected": sum(
                1
                for row in prototype_rows
                if row.get("prototype_status") == "REJECTED_UNSAFE_GENERATED_CODE"
            ),
            "promotion_ready": False,
            "boundary": (
                "Algorithm sandbox prototypes are executable engineering evidence. "
                "They are not registered production algorithms and are not theorem proof evidence."
            ),
        }
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="algorithm_sandbox",
            status="EXECUTED_SANDBOX_PROTOTYPES" if manifest["n_executed"] else "NO_EXECUTABLE_PROTOTYPE",
            boundary=str(manifest["boundary"]),
            payload={
                "n_prototypes": manifest["n_prototypes"],
                "n_executed": manifest["n_executed"],
                "n_passed": manifest["n_passed"],
                "n_generated_code_executed": manifest["n_generated_code_executed"],
                "n_unsafe_generated_code_rejected": manifest["n_unsafe_generated_code_rejected"],
                "promotion_ready": False,
                "architect_acceptance_gate": algorithm_control.get("acceptance_gate", ""),
            },
        )
        produced_artifacts[manifest_id] = manifest
        next_task = _formalization_task(
            question=question,
            packet_id=packet_id,
            simulation_manifest_id=simulation_manifest_id,
            algorithm_sandbox_manifest_id=manifest_id,
            architect_context=context,
        )
        observations.append(
            EnvironmentObservation(
                observation_type="algorithm_sandbox_result",
                summary=(
                    f"prototypes={manifest['n_prototypes']} executed={manifest['n_executed']} "
                    f"passed={manifest['n_passed']} promotion_ready=false"
                ),
                payload={
                    "manifest_id": manifest_id,
                    "llm_algorithm_engineer_proposal_id": manifest["llm_algorithm_engineer_proposal_id"],
                    "n_prototypes": manifest["n_prototypes"],
                    "n_executed": manifest["n_executed"],
                    "n_passed": manifest["n_passed"],
                    "n_generated_code_executed": manifest["n_generated_code_executed"],
                    "n_unsafe_generated_code_rejected": manifest["n_unsafe_generated_code_rejected"],
                    "promotion_ready": False,
                },
            )
        )
        evidence_entries = [row for row in (proposal_evidence, evidence) if row is not None]
        return AgentStepResult(
            status="REROUTE",
            rationale=(
                "AlgorithmEngineer recorded sandbox executable feedback for unregistered "
                "LLM estimator specs and is routing to formalization/proof feedback."
            ),
            produced_artifacts=produced_artifacts,
            observations=tuple(observations),
            tool_calls=tuple(tool_calls),
            evidence_entries=tuple(evidence_entries),
            next_task=next_task,
        )


class FormalizationEvaluatorRuntimeSubsystem:
    name = "FormalizationEvaluator"

    def __init__(
        self,
        *,
        proposal_agent: LLMFormalizerProofEngineerAgent | None = None,
        proof_verifier: ProofVerifier | None = None,
        proof_state_provider: ProofStateFeedbackProvider | None = None,
        formal_source_retriever: Any | None = None,
        proof_obligation_ids: tuple[str, ...] = (),
        max_proof_obligations: int = 0,
    ) -> None:
        self.proposal_agent = proposal_agent
        self.proof_state_provider = proof_state_provider
        self.prover = FormalSubclaimProver(
            verifier=proof_verifier,
            formal_source_retriever=formal_source_retriever,
            proof_obligation_ids=proof_obligation_ids,
            max_proof_obligations=max_proof_obligations,
        )

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        formalization_control = _architect_control_payload(context, "FormalizationEvaluator")
        packet_id = str(task.inputs.get("theory_packet_id", ""))
        packet = blackboard.artifacts.get(packet_id, {})
        simulation_manifest_id = str(task.inputs.get("simulation_manifest_id", ""))
        algorithm_sandbox_manifest_id = str(task.inputs.get("algorithm_sandbox_manifest_id", ""))
        simulation_manifest = blackboard.artifacts.get(simulation_manifest_id, {})
        algorithm_manifest = blackboard.artifacts.get(algorithm_sandbox_manifest_id, {})
        problem = ProblemFormalizer().formalize(question)
        _procedures, theorem_goals = TheoryPlanner().plan(problem)
        proof_bank_obligation_catalog = self.prover.proof_obligation_catalog(problem, theorem_goals)
        proposal_packet: dict[str, Any] | None = None
        proposal_evidence: EvidenceLedgerEntry | None = None
        llm_requested_proof_obligation_ids: tuple[str, ...] = ()
        llm_prioritized_proof_obligation_ids: tuple[str, ...] = ()
        llm_suppressed_kernel_verified_proof_obligation_ids: tuple[str, ...] = ()
        llm_off_catalog_proof_obligation_ids: tuple[str, ...] = ()
        llm_rejected_proof_obligation_ids: tuple[str, ...] = ()
        memory_kernel_verified_proof_obligation_ids = (
            _runtime_learning_memory_kernel_verified_proof_obligation_ids(
                context,
                catalog_ids=tuple(
                    str(row.get("obligation_id", "") or "")
                    for row in proof_bank_obligation_catalog
                    if isinstance(row, Mapping)
                ),
            )
        )
        (
            memory_prioritized_proof_obligation_ids,
            memory_off_catalog_proof_obligation_ids,
            memory_rejected_proof_obligation_ids,
        ) = _runtime_learning_memory_proof_obligation_ids(
            context,
            catalog_ids=tuple(
                str(row.get("obligation_id", "") or "")
                for row in proof_bank_obligation_catalog
                if isinstance(row, Mapping)
            ),
        )
        proof_bank_runtime_memory_summary = _formalizer_proof_bank_runtime_memory_summary(
            context=context,
            proof_bank_obligation_catalog=proof_bank_obligation_catalog,
            theorem_goals=theorem_goals,
            memory_kernel_verified_proof_obligation_ids=memory_kernel_verified_proof_obligation_ids,
            memory_prioritized_proof_obligation_ids=memory_prioritized_proof_obligation_ids,
        )
        produced_artifacts: dict[str, Any] = {}
        observations: list[EnvironmentObservation] = []
        proposal_source = ""
        if _should_emit_deterministic_theorem_closure_packet(
            proof_bank_runtime_memory_summary
        ):
            proposal_packet = _deterministic_theorem_closure_proposal_packet(
                question=question,
                theorem_goals=theorem_goals,
                proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
            )
            proposal_source = "deterministic_theorem_closure_work_order_seed"
        elif self.proposal_agent is not None:
            proposal_packet = self.proposal_agent.propose(
                question=question,
                theory_packet=packet if isinstance(packet, Mapping) else {},
                simulation_manifest=simulation_manifest if isinstance(simulation_manifest, Mapping) else {},
                algorithm_manifest=algorithm_manifest if isinstance(algorithm_manifest, Mapping) else {},
                registered_problem=_problem_to_json(problem),
                theorem_goals=[_theorem_goal_to_json(row) for row in theorem_goals],
                proof_bank_obligation_catalog=proof_bank_obligation_catalog,
                proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
            )
            proposal_source = "llm_formalizer_proof_engineer_proposal"
        if proposal_packet is not None:
            (
                llm_requested_proof_obligation_ids,
                llm_off_catalog_proof_obligation_ids,
                llm_rejected_proof_obligation_ids,
            ) = _proof_bank_obligation_request_ids(
                proposal_packet,
                catalog_ids=tuple(
                    str(row.get("obligation_id", "") or "")
                    for row in proof_bank_obligation_catalog
                    if isinstance(row, Mapping)
                ),
            )
            memory_kernel_verified_set = set(memory_kernel_verified_proof_obligation_ids)
            llm_prioritized_proof_obligation_ids = tuple(
                row for row in llm_requested_proof_obligation_ids if row not in memory_kernel_verified_set
            )
            llm_suppressed_kernel_verified_proof_obligation_ids = tuple(
                row for row in llm_requested_proof_obligation_ids if row in memory_kernel_verified_set
            )
            proposal_id = str(proposal_packet["packet_id"])
            produced_artifacts[proposal_id] = proposal_packet
            is_deterministic_closure = (
                proposal_source == "deterministic_theorem_closure_work_order_seed"
            )
            observations.append(
                EnvironmentObservation(
                    observation_type=proposal_source,
                    summary=(
                        "deterministic theorem-closure work-order seed recorded after "
                        "runtime memory exhausted the registered proof-bank bridge catalog"
                        if is_deterministic_closure
                        else "validated LLM Formalizer/ProofEngineer proposal recorded "
                        "before proof-bank/kernel evaluation"
                    ),
                    payload={
                        "packet_id": proposal_id,
                        "source_agent": str(proposal_packet.get("source_agent", "")),
                        "n_formal_targets": len(proposal_packet.get("formal_targets", []) or []),
                        "n_retrieval_queries": len(proposal_packet.get("retrieval_queries", []) or []),
                        "n_proof_bank_obligation_requests": len(
                            proposal_packet.get("proof_bank_obligation_requests", []) or []
                        ),
                        "n_registered_proof_bank_obligation_candidates": len(proof_bank_obligation_catalog),
                        "n_registered_proof_bank_obligation_requests": len(llm_requested_proof_obligation_ids),
                        "n_prioritized_registered_proof_bank_obligation_requests": len(
                            llm_prioritized_proof_obligation_ids
                        ),
                        "n_suppressed_kernel_verified_proof_bank_obligation_requests": len(
                            llm_suppressed_kernel_verified_proof_obligation_ids
                        ),
                        "n_off_catalog_proof_bank_obligation_requests": len(
                            llm_off_catalog_proof_obligation_ids
                        ),
                        "proof_evidence_status": str(
                            proposal_packet.get(
                                "proof_evidence_status",
                                FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE,
                            )
                        ),
                    },
                )
            )
            proposal_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:" + stable_hash([task.task_id, proposal_id])[:20],
                task_id=task.task_id,
                artifact_id=proposal_id,
                evidence_type=proposal_source,
                status=(
                    "WORK_ORDER_SEED_RECORDED_NOT_PROOF_EVIDENCE"
                    if is_deterministic_closure
                    else "PROPOSAL_RECORDED_REQUIRES_KERNEL_VERIFICATION"
                ),
                boundary=FORMALIZER_BOUNDARY,
                payload={
                    "source_agent": str(proposal_packet.get("source_agent", "")),
                    "n_formal_targets": len(proposal_packet.get("formal_targets", []) or []),
                    "n_retrieval_queries": len(proposal_packet.get("retrieval_queries", []) or []),
                    "n_registered_proof_bank_obligation_candidates": len(proof_bank_obligation_catalog),
                    "n_registered_proof_bank_obligation_requests": len(llm_requested_proof_obligation_ids),
                    "n_prioritized_registered_proof_bank_obligation_requests": len(
                        llm_prioritized_proof_obligation_ids
                    ),
                    "n_suppressed_kernel_verified_proof_bank_obligation_requests": len(
                        llm_suppressed_kernel_verified_proof_obligation_ids
                    ),
                    "n_off_catalog_proof_bank_obligation_requests": len(llm_off_catalog_proof_obligation_ids),
                    "kernel_verified": False,
                    "full_frontier_theorem_proved": False,
                },
            )
        subclaims = asyncio.run(
            self.prover.prove(
                problem,
                theorem_goals,
                prioritized_proof_obligation_ids=(
                    *memory_prioritized_proof_obligation_ids,
                    *llm_prioritized_proof_obligation_ids,
                ),
                excluded_proof_obligation_ids=memory_kernel_verified_proof_obligation_ids,
            )
        )
        proof_obligation_control = self.prover.proof_obligation_control()
        proof_obligation_control["memory_prioritized_proof_obligation_ids"] = list(
            memory_prioritized_proof_obligation_ids
        )
        proof_obligation_control["memory_off_catalog_proof_obligation_ids"] = list(
            memory_off_catalog_proof_obligation_ids
        )
        proof_obligation_control["memory_rejected_proof_obligation_ids"] = list(
            memory_rejected_proof_obligation_ids
        )
        proof_obligation_control["memory_kernel_verified_proof_obligation_ids"] = list(
            memory_kernel_verified_proof_obligation_ids
        )
        proof_obligation_control["llm_requested_proof_obligation_ids"] = list(llm_requested_proof_obligation_ids)
        proof_obligation_control["llm_prioritized_proof_obligation_ids"] = list(
            llm_prioritized_proof_obligation_ids
        )
        proof_obligation_control["llm_suppressed_kernel_verified_proof_obligation_ids"] = list(
            llm_suppressed_kernel_verified_proof_obligation_ids
        )
        proof_obligation_control["llm_off_catalog_proof_obligation_ids"] = list(
            llm_off_catalog_proof_obligation_ids
        )
        proof_obligation_control["llm_rejected_proof_obligation_ids"] = list(llm_rejected_proof_obligation_ids)
        proof_obligation_control["priority_source"] = (
            "runtime_learning_memory+llm_formalizer"
            if memory_prioritized_proof_obligation_ids and llm_prioritized_proof_obligation_ids
            else "runtime_learning_memory"
            if memory_prioritized_proof_obligation_ids
            else "llm_formalizer"
            if llm_prioritized_proof_obligation_ids
            else "none"
        )
        proof_obligation_control["priority_boundary"] = (
            "LLM Formalizer and runtime-learning-memory proof-bank requests only prioritize registered "
            "subclaim kernel-smoke work. AgentRuntime filters them against the proof bank and current "
            "candidate catalog; requests already marked kernel verified by runtime-learning memory, "
            "off-catalog requests, and rejected requests are recorded but not used for proof selection. "
            "Requests and memory are not proof evidence."
        )
        proof_obligation_control["proof_bank_bridge_catalog_exhausted_by_memory"] = bool(
            proof_bank_runtime_memory_summary.get(
                "proof_bank_bridge_catalog_exhausted_by_memory",
                False,
            )
        )
        proof_obligation_control["theorem_reduction_closure_required"] = bool(
            proof_bank_runtime_memory_summary.get(
                "theorem_reduction_closure_required",
                False,
            )
        )
        proof_obligation_control["theorem_reduction_closure_already_kernel_verified"] = bool(
            proof_bank_runtime_memory_summary.get(
                "theorem_reduction_closure_already_kernel_verified",
                False,
            )
        )
        proof_obligation_control["memory_kernel_verified_theorem_reduction_closure_work_order_ids"] = list(
            proof_bank_runtime_memory_summary.get(
                "memory_kernel_verified_theorem_reduction_closure_work_order_ids",
                [],
            )
            or []
        )
        proof_obligation_control["memory_kernel_verified_theorem_reduction_closure_goal_ids"] = list(
            proof_bank_runtime_memory_summary.get(
                "memory_kernel_verified_theorem_reduction_closure_goal_ids",
                [],
            )
            or []
        )
        proof_obligation_control["memory_kernel_verified_theorem_reduction_closure_target_ids"] = list(
            proof_bank_runtime_memory_summary.get(
                "memory_kernel_verified_theorem_reduction_closure_target_ids",
                [],
            )
            or []
        )
        proof_obligation_control["memory_kernel_verified_source_theorem_semantic_primitive_ids"] = list(
            proof_bank_runtime_memory_summary.get(
                "memory_kernel_verified_source_theorem_semantic_primitive_ids",
                [],
            )
            or []
        )
        proof_obligation_control[
            "source_theorem_semantic_primitive_support_already_kernel_verified"
        ] = bool(
            proof_bank_runtime_memory_summary.get(
                "source_theorem_semantic_primitive_support_already_kernel_verified",
                False,
            )
        )
        proof_obligation_control["remaining_unverified_proof_bank_obligation_ids"] = list(
            proof_bank_runtime_memory_summary.get(
                "remaining_unverified_proof_bank_obligation_ids",
                [],
            )
            or []
        )
        n_proved = sum(1 for row in subclaims if row.status == "PROVED")
        n_kernel_verified = sum(1 for row in subclaims if row.kernel_verified)
        n_formal_gaps = sum(1 for row in subclaims if row.status == "FORMAL_GAP")
        n_failed = sum(1 for row in subclaims if row.status == "FAILED")
        verifier_names = sorted({str(row.verifier or "") for row in subclaims if row.verifier})
        proof_state_rows = (
            self.proof_state_provider.inspect(subclaims)
            if self.proof_state_provider is not None
            else []
        )
        proof_state_row_dicts = [proof_state_feedback_row_to_json(row) for row in proof_state_rows]
        n_residual_goals = sum(len(row.residual_goals) for row in proof_state_rows)
        n_route_revision = sum(1 for row in proof_state_rows if row.route_revision_recommended)
        n_local_lean_checked = sum(1 for row in proof_state_rows if row.local_lean_checked)
        proof_state_manifest_id = (
            "proof_state_feedback_manifest:" + stable_hash([task.task_id, packet_id, proof_state_row_dicts])[:20]
            if proof_state_rows
            else ""
        )
        manifest_id = "formalization_manifest:" + stable_hash([task.task_id, packet_id])[:20]
        gap_planner_bridge = _runtime_formalization_gap_planner_bridge(
            question=question,
            problem=problem,
            theorem_goals=theorem_goals,
            subclaims=subclaims,
            proof_state_rows=proof_state_row_dicts,
            retrieval_context=(
                context.get("retrieval_context", {})
                if isinstance(context.get("retrieval_context", {}), Mapping)
                else {}
            ),
            formalization_manifest_id=manifest_id,
            proof_state_feedback_manifest_id=proof_state_manifest_id,
        )
        theorem_reduction_closure_work_orders = _formalizer_theorem_reduction_closure_work_orders(
            proposal_packet=proposal_packet if isinstance(proposal_packet, Mapping) else {},
            proof_bank_runtime_memory_summary=proof_bank_runtime_memory_summary,
            theorem_goals=theorem_goals,
        )
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeFormalizationManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "algorithm_sandbox_manifest_id": algorithm_sandbox_manifest_id,
            "runtime_architect_control": formalization_control,
            "llm_formalizer_proof_engineer_proposal_id": (
                str(proposal_packet.get("packet_id", "")) if proposal_packet else ""
            ),
            "problem": _problem_to_json(problem),
            "llm_formalization_requests": (
                list(packet.get("formalization_requests", []) or [])
                if isinstance(packet, Mapping)
                else []
            ),
            "llm_proof_bank_obligation_requests": (
                list(proposal_packet.get("proof_bank_obligation_requests", []) or [])
                if isinstance(proposal_packet, Mapping)
                else []
            ),
            "deterministic_theorem_goals": [_theorem_goal_to_json(row) for row in theorem_goals],
            "registered_proof_bank_obligation_catalog": proof_bank_obligation_catalog,
            "registered_proof_bank_obligation_catalog_boundary": (
                "The catalog is proof-target selection context for the LLM Formalizer. "
                "It is not proof evidence and does not expose proof bodies."
            ),
            "proof_bank_runtime_memory_summary": proof_bank_runtime_memory_summary,
            "theorem_reduction_closure_work_orders": theorem_reduction_closure_work_orders,
            "theorem_reduction_closure_work_order_boundary": (
                "Theorem-reduction closure work orders are machine-actionable proof tasks "
                "for ProofEngineer/Lean. They are not proof evidence until AXLE/local Lean "
                "kernel verification closes the intended theorem-level reduction."
            ),
            "formal_subclaims": [_formal_subclaim_to_json(row) for row in subclaims],
            "proof_obligation_control": proof_obligation_control,
            "proof_state_feedback_manifest_id": proof_state_manifest_id,
            "formalization_gap_planner_bridge_id": gap_planner_bridge["bridge_id"],
            "formalization_gap_planner_standalone_seed_artifact_id": (
                gap_planner_bridge["standalone_seed_artifact_id"]
            ),
            "counts": {
                "proved": n_proved,
                "kernel_verified": n_kernel_verified,
                "formal_gap": n_formal_gaps,
                "failed": n_failed,
                "proof_state_feedback": len(proof_state_rows),
                "proof_state_residual_goals": n_residual_goals,
                "proof_state_route_revisions": n_route_revision,
                "formalization_gap_planner_routes": gap_planner_bridge["counts"][
                    "routes"
                ],
                "formalization_gap_planner_primitives": gap_planner_bridge["counts"][
                    "primitives"
                ],
                "theorem_reduction_closure_work_orders": len(
                    theorem_reduction_closure_work_orders
                ),
            },
            "verifiers": verifier_names,
            "full_frontier_theorem_proved": False,
            "proof_evidence_status": (
                "KERNEL_VERIFIED_SUBCLAIMS_PRESENT"
                if n_kernel_verified
                else "NO_KERNEL_VERIFIED_SUBCLAIMS_IN_THIS_RUN"
            ),
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        }
        proof_state_manifest = None
        if proof_state_rows:
            proof_state_manifest = {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "RuntimeProofStateFeedbackManifest",
                "manifest_id": proof_state_manifest_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "question": _question_to_payload(question),
                "theory_packet_id": packet_id,
                "formalization_manifest_id": manifest_id,
                "provider_name": getattr(self.proof_state_provider, "name", "unknown"),
                "provider_kind": "local_fallback_or_mcp_compatible",
                "lean_lsp_mcp_live_called": False,
                "local_lean_checked": n_local_lean_checked,
                "rows": proof_state_row_dicts,
                "counts": {
                    "rows": len(proof_state_rows),
                    "residual_goals": n_residual_goals,
                    "route_revision_recommended": n_route_revision,
                    "local_lean_checked": n_local_lean_checked,
                },
                "proof_evidence_status": "PROOF_STATE_FEEDBACK_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": PROOF_STATE_FEEDBACK_BOUNDARY,
            }
            produced_artifacts[proof_state_manifest_id] = proof_state_manifest
        produced_artifacts[str(gap_planner_bridge["standalone_seed_artifact_id"])] = (
            gap_planner_bridge["standalone_seed"]
        )
        produced_artifacts[str(gap_planner_bridge["bridge_id"])] = gap_planner_bridge
        produced_artifacts[manifest_id] = manifest
        evidence_status = (
            "KERNEL_VERIFIED_SUBCLAIMS_RECORDED"
            if n_kernel_verified
            else "FORMALIZATION_GAPS_AND_NONKERNEL_ROWS_RECORDED"
        )
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="formalization_proof_feedback",
            status=evidence_status,
            boundary=KERNEL_PROOF_BOUNDARY,
            payload={
                "counts": manifest["counts"],
                "full_frontier_theorem_proved": False,
                "verifiers": verifier_names,
                "architect_acceptance_gate": formalization_control.get("acceptance_gate", ""),
            },
        )
        proof_state_evidence = None
        if proof_state_manifest is not None:
            proof_state_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:" + stable_hash([task.task_id, proof_state_manifest_id])[:20],
                task_id=task.task_id,
                artifact_id=proof_state_manifest_id,
                evidence_type="proof_state_feedback",
                status="PROOF_STATE_FEEDBACK_RECORDED_NOT_PROOF_EVIDENCE",
                boundary=PROOF_STATE_FEEDBACK_BOUNDARY,
                payload={
                    "counts": proof_state_manifest["counts"],
                    "lean_lsp_mcp_live_called": False,
                    "provider_name": proof_state_manifest["provider_name"],
                },
            )
        gap_planner_evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, gap_planner_bridge["bridge_id"]])[:20],
            task_id=task.task_id,
            artifact_id=str(gap_planner_bridge["bridge_id"]),
            evidence_type="formalization_gap_planner_runtime_bridge",
            status="RUNTIME_FORMALIZATION_GAP_PLANNER_SEED_RECORDED_NOT_PROOF_EVIDENCE",
            boundary=str(gap_planner_bridge["proof_evidence_boundary"]),
            payload={
                "counts": gap_planner_bridge["counts"],
                "standalone_seed_artifact_id": gap_planner_bridge[
                    "standalone_seed_artifact_id"
                ],
            },
        )
        observations.append(
            EnvironmentObservation(
                observation_type="formalization_proof_feedback",
                summary=(
                    f"proved={n_proved} kernel_verified={n_kernel_verified} "
                    f"formal_gap={n_formal_gaps} failed={n_failed}"
                ),
                payload={
                    "counts": manifest["counts"],
                    "proof_evidence_status": manifest["proof_evidence_status"],
                    "full_frontier_theorem_proved": False,
                    "memory_kernel_verified_proof_obligation_ids": list(
                        memory_kernel_verified_proof_obligation_ids
                    ),
                    "llm_prioritized_proof_obligation_ids": list(
                        llm_prioritized_proof_obligation_ids
                    ),
                    "llm_suppressed_kernel_verified_proof_obligation_ids": list(
                        llm_suppressed_kernel_verified_proof_obligation_ids
                    ),
                },
            )
        )
        if proof_state_manifest is not None:
            observations.append(
                EnvironmentObservation(
                    observation_type="proof_state_feedback",
                    summary=(
                        f"proof_state_feedback={len(proof_state_rows)} residual_goals={n_residual_goals} "
                        f"route_revisions={n_route_revision} live_mcp=false"
                    ),
                    payload={
                        "manifest_id": proof_state_manifest_id,
                        "counts": proof_state_manifest["counts"],
                        "proof_evidence_status": proof_state_manifest["proof_evidence_status"],
                        "lean_lsp_mcp_live_called": False,
                    },
                )
            )
        observations.append(
            EnvironmentObservation(
                observation_type="formalization_gap_planner_runtime_bridge",
                summary=(
                    "runtime formalization gaps exported as standalone "
                    f"gap-planner seed routes={gap_planner_bridge['counts']['routes']} "
                    f"primitives={gap_planner_bridge['counts']['primitives']}"
                ),
                payload={
                    "bridge_id": gap_planner_bridge["bridge_id"],
                    "standalone_seed_artifact_id": gap_planner_bridge[
                        "standalone_seed_artifact_id"
                    ],
                    "counts": gap_planner_bridge["counts"],
                    "proof_evidence_status": gap_planner_bridge[
                        "proof_evidence_status"
                    ],
                },
            )
        )
        tool_calls = [
            ToolCallRecord(
                tool_name="FormalSubclaimProver.prove",
                inputs={
                    "n_theorem_goals": len(theorem_goals),
                    "problem_class": problem.problem_class,
                    "llm_requested_proof_obligation_ids": list(llm_requested_proof_obligation_ids),
                    "llm_prioritized_proof_obligation_ids": list(
                        llm_prioritized_proof_obligation_ids
                    ),
                    "llm_suppressed_kernel_verified_proof_obligation_ids": list(
                        llm_suppressed_kernel_verified_proof_obligation_ids
                    ),
                    "memory_kernel_verified_proof_obligation_ids": list(
                        memory_kernel_verified_proof_obligation_ids
                    ),
                    "memory_prioritized_proof_obligation_ids": list(
                        memory_prioritized_proof_obligation_ids
                    ),
                    "llm_off_catalog_proof_obligation_ids": list(llm_off_catalog_proof_obligation_ids),
                    "llm_rejected_proof_obligation_ids": list(llm_rejected_proof_obligation_ids),
                    "max_proof_obligations": proof_obligation_control.get("max_proof_obligations", 0),
                },
                exit_status="0" if n_failed == 0 else "failed_subclaims_present",
                stdout_summary=(
                    f"proved={n_proved}, kernel_verified={n_kernel_verified}, "
                    f"formal_gap={n_formal_gaps}, failed={n_failed}"
                ),
                safety_boundary=KERNEL_PROOF_BOUNDARY,
            )
        ]
        if proof_state_manifest is not None:
            tool_calls.append(
                ToolCallRecord(
                    tool_name="ProofStateFeedbackProvider.inspect",
                    inputs={
                        "provider": proof_state_manifest["provider_name"],
                        "n_subclaims": len(subclaims),
                        "lean_lsp_mcp_live_called": False,
                    },
                    exit_status="0",
                    stdout_summary=(
                        f"rows={len(proof_state_rows)}, residual_goals={n_residual_goals}, "
                        f"route_revisions={n_route_revision}"
                    ),
                    safety_boundary=PROOF_STATE_FEEDBACK_BOUNDARY,
                )
            )
        return AgentStepResult(
            status="REROUTE",
            rationale=(
                "Runtime recorded formalization/proof feedback. Registered "
                "subclaims and frontier gaps are distinguished; full frontier "
                "theorem remains unproved unless a separate kernel-verified "
                "reduction closes the gaps. Routing to CriticEvaluator for next-action "
                "agenda and learning rows."
            ),
            produced_artifacts=produced_artifacts,
            observations=tuple(observations),
            tool_calls=tuple(tool_calls),
            evidence_entries=tuple(row for row in (proposal_evidence, evidence, proof_state_evidence, gap_planner_evidence) if row is not None),
            next_task=AgentTask(
                task_id=f"critic:{question.id}:{stable_hash(manifest_id)[:8]}",
                owner_subsystem="CriticEvaluator",
                objective=(
                    "Evaluate all runtime artifacts, preserve evidence boundaries, "
                    "and export next-action agenda plus learning rows."
                ),
                inputs={
                    "question": _question_to_payload(question),
                    "theory_packet_id": packet_id,
                    "formalization_manifest_id": manifest_id,
                    "architect_context": context,
                },
                allowed_tools=("blackboard", "evidence_ledger"),
                expected_artifacts=_architect_expected_artifacts(
                    context,
                    "CriticEvaluator",
                    ("critic_evaluator_manifest", "runtime_learning_rows"),
                ),
                acceptance_gate=_architect_acceptance_gate(
                    context,
                    "CriticEvaluator",
                    "agenda distinguishes implementation, simulation, formal, and kernel-evidence gaps",
                ),
                stop_condition="critic agenda and learning rows recorded",
            ),
        )


class CriticEvaluatorRuntimeSubsystem:
    name = "CriticEvaluator"

    def __init__(
        self,
        *,
        proposal_agent: LLMCriticEvaluatorAgent | None = None,
        runtime_config: ResearchAgentRuntimeConfig = ResearchAgentRuntimeConfig(),
    ) -> None:
        self.proposal_agent = proposal_agent
        self.runtime_config = runtime_config

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        context = dict(task.inputs.get("architect_context", {}) or {})
        critic_control = _architect_control_payload(context, "CriticEvaluator")
        retrieval_manifest = _latest_artifact(blackboard, "retrieval_memory_manifest:")
        theory_packet = _latest_artifact(blackboard, "theory_derivation:")
        simulation_manifest = _latest_artifact(blackboard, "simulation_manifest:")
        algorithm_manifest = _latest_artifact(blackboard, "algorithm_sandbox_manifest:")
        formalization_manifest = _latest_artifact(blackboard, "formalization_manifest:")
        agenda = _critic_next_action_agenda(
            question=question,
            retrieval_manifest=retrieval_manifest,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            algorithm_manifest=algorithm_manifest,
            formalization_manifest=formalization_manifest,
        )
        learning_rows = _critic_learning_rows(
            question=question,
            agenda=agenda,
            retrieval_manifest=retrieval_manifest,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            algorithm_manifest=algorithm_manifest,
            formalization_manifest=formalization_manifest,
        )
        critic_round = _critic_repair_round(context)
        max_critic_repair_rounds = _effective_critic_repair_rounds(
            context,
            self.runtime_config,
        )
        should_repair = _critic_should_reroute_to_theory(
            agenda=agenda,
            formalization_manifest=formalization_manifest,
            critic_round=critic_round,
            max_critic_repair_rounds=max_critic_repair_rounds,
        )
        repair_feedback = _critic_repair_feedback(
            question=question,
            critic_round=critic_round,
            max_critic_repair_rounds=max_critic_repair_rounds,
            retrieval_manifest=retrieval_manifest,
            theory_packet=theory_packet,
            simulation_manifest=simulation_manifest,
            algorithm_manifest=algorithm_manifest,
            formalization_manifest=formalization_manifest,
            agenda=agenda,
        )
        proposal_packet: dict[str, Any] | None = None
        proposal_evidence: EvidenceLedgerEntry | None = None
        produced_artifacts: dict[str, Any] = {}
        observations: list[EnvironmentObservation] = []
        if self.proposal_agent is not None:
            proposal_packet = self.proposal_agent.propose(
                question=question,
                retrieval_manifest=retrieval_manifest,
                theory_packet=theory_packet,
                simulation_manifest=simulation_manifest,
                algorithm_manifest=algorithm_manifest,
                formalization_manifest=formalization_manifest,
                deterministic_agenda=agenda,
                deterministic_learning_rows=learning_rows,
            )
            proposal_id = str(proposal_packet["packet_id"])
            produced_artifacts[proposal_id] = proposal_packet
            observations.append(
                EnvironmentObservation(
                    observation_type="llm_critic_evaluator_proposal",
                    summary=(
                        "validated LLM CriticEvaluator boundary-audit and learning "
                        "proposal recorded before deterministic agenda export"
                    ),
                    payload={
                        "packet_id": proposal_id,
                        "n_boundary_audit_rows": len(proposal_packet.get("evidence_boundary_audit", []) or []),
                        "n_reroute_recommendations": len(proposal_packet.get("reroute_recommendations", []) or []),
                        "proof_evidence_status": CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE,
                    },
                )
            )
            proposal_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:" + stable_hash([task.task_id, proposal_id])[:20],
                task_id=task.task_id,
                artifact_id=proposal_id,
                evidence_type="llm_critic_evaluator_proposal",
                status="PROPOSAL_RECORDED_NOT_AUTHORITY_GATE",
                boundary=CRITIC_EVALUATOR_BOUNDARY,
                payload={
                    "n_boundary_audit_rows": len(proposal_packet.get("evidence_boundary_audit", []) or []),
                    "n_learning_updates": len(proposal_packet.get("learning_updates", []) or []),
                    "kernel_verified": False,
                    "full_frontier_theorem_proved": False,
                },
            )
        manifest_id = "critic_evaluator_manifest:" + stable_hash([task.task_id, agenda, learning_rows])[:20]
        manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeCriticEvaluatorManifest",
            "manifest_id": manifest_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": _question_to_payload(question),
            "runtime_architect_control": critic_control,
            "llm_critic_evaluator_proposal_id": (
                str(proposal_packet.get("packet_id", "")) if proposal_packet else ""
            ),
            "next_action_agenda": agenda,
            "learning_rows": learning_rows,
            "critic_repair_round": critic_round,
            "max_critic_repair_rounds": max_critic_repair_rounds,
            "runtime_reroute_decision": {
                "reroute_to_theory_developer": should_repair,
                "reason": (
                    "formal/proof feedback requires another theory-discovery pass"
                    if should_repair
                    else "critic repair budget exhausted or no theory-level repair trigger"
                ),
                "environment_feedback": repair_feedback if should_repair else {},
            },
            "counts": {
                "agenda_items": len(agenda),
                "learning_rows": len(learning_rows),
                "kernel_verified": int(
                    (formalization_manifest.get("counts", {}) if isinstance(formalization_manifest, Mapping) else {}).get(
                        "kernel_verified", 0
                    )
                    or 0
                ),
                "formal_gaps": int(
                    (formalization_manifest.get("counts", {}) if isinstance(formalization_manifest, Mapping) else {}).get(
                        "formal_gap", 0
                    )
                    or 0
                ),
            },
            "boundary": (
                "Critic/evaluator rows are orchestration and learning signals. "
                "They do not promote retrieval, simulation, sandbox code, or mock proof rows to theorem proof evidence."
            ),
        }
        produced_artifacts[manifest_id] = manifest
        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, manifest_id])[:20],
            task_id=task.task_id,
            artifact_id=manifest_id,
            evidence_type="critic_evaluator",
            status="NEXT_ACTION_AGENDA_AND_LEARNING_ROWS_RECORDED",
            boundary=str(manifest["boundary"]),
            payload={
                **manifest["counts"],
                "architect_acceptance_gate": critic_control.get("acceptance_gate", ""),
            },
        )
        observations.append(
            EnvironmentObservation(
                observation_type="critic_evaluator",
                summary=(
                    f"agenda_items={len(agenda)} learning_rows={len(learning_rows)} "
                    f"critic_repair_round={critic_round}/{max_critic_repair_rounds} "
                    f"reroute_to_theory={should_repair}"
                ),
                payload={
                    **manifest["counts"],
                    "critic_repair_round": critic_round,
                    "max_critic_repair_rounds": max_critic_repair_rounds,
                    "reroute_to_theory_developer": should_repair,
                },
            )
        )
        if should_repair:
            revision_context = dict(context)
            revision_context["previous_theory_packet_id"] = str(theory_packet.get("packet_id", ""))
            revision_context["runtime_feedback_loop"] = {
                "source_subsystem": "CriticEvaluator",
                "critic_repair_round": critic_round + 1,
                "max_critic_repair_rounds": max_critic_repair_rounds,
                "critic_evaluator_manifest_id": manifest_id,
            }
            return AgentStepResult(
                status="REVISE",
                rationale=(
                    "CriticEvaluator found formal/proof feedback that should revise "
                    "the theory proposal before stopping the runtime loop."
                ),
                produced_artifacts=produced_artifacts,
                observations=tuple(observations),
                evidence_entries=tuple(row for row in (proposal_evidence, evidence) if row is not None),
                next_task=AgentTask(
                    task_id=f"theory-critic-revise:{question.id}:{stable_hash([manifest_id, critic_round])[:8]}",
                    owner_subsystem="TheoryDeveloper",
                    objective=(
                        "Revise the statistical theory/procedure/proof plan using CriticEvaluator "
                        "formal-gap and proof-state feedback."
                    ),
                    inputs={
                        "question": _question_to_payload(question),
                        "architect_context": revision_context,
                        "environment_feedback": repair_feedback,
                    },
                    allowed_tools=("model_backend", "rag_memory", "evidence_ledger"),
                    expected_artifacts=("critic_revised_theory_derivation_packet",),
                    acceptance_gate=(
                        "revised theory packet addresses critic formal/proof feedback "
                        "without promoting non-kernel evidence"
                    ),
                    stop_condition="revised theory packet routed through simulation/formalization gates",
                ),
                failure_classification="critic_requested_theory_revision",
            )
        return AgentStepResult(
            status="ACCEPTED",
            rationale="CriticEvaluator recorded next-action agenda and learning rows from the runtime trace.",
            produced_artifacts=produced_artifacts,
            observations=tuple(observations),
            evidence_entries=tuple(row for row in (proposal_evidence, evidence) if row is not None),
        )


def run_research_agent_runtime(
    questions: list[OpenResearchQuestion],
    out_dir: Path,
    *,
    theory_developer: LLMTheoryDeveloperAgent,
    architect_coordinator: LLMArchitectCoordinatorAgent | None = None,
    simulation_engineer: LLMSimulationEngineerAgent | None = None,
    algorithm_engineer: LLMAlgorithmEngineerAgent | None = None,
    formalizer: LLMFormalizerProofEngineerAgent | None = None,
    critic_evaluator: LLMCriticEvaluatorAgent | None = None,
    proof_verifier: ProofVerifier | None = None,
    proof_state_provider: ProofStateFeedbackProvider | None = None,
    formal_source_retriever: Any | None = None,
    config: ResearchAgentRuntimeConfig = ResearchAgentRuntimeConfig(),
    architect_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    progress_path = out_dir / "runtime_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")
    shared_formal_source_retriever = formal_source_retriever or FormalSourceRetriever()
    llm_topology = _runtime_llm_topology(
        architect_coordinator=architect_coordinator,
        theory_developer=theory_developer,
        simulation_engineer=simulation_engineer,
        algorithm_engineer=algorithm_engineer,
        formalizer=formalizer,
        critic_evaluator=critic_evaluator,
        proof_state_provider=proof_state_provider,
    )
    if llm_topology["policy_status"] != "OK":
        raise ValueError(
            "LLM topology policy violation: "
            + "; ".join(str(row) for row in llm_topology["policy_violations"])
        )
    for question in questions:
        blackboard = BlackboardState(project_id=f"ai_statistician:{question.id}")
        blackboard.artifacts[llm_topology["manifest_id"]] = llm_topology
        subsystems: dict[str, Any] = {
            "RetrievalMemory": RetrievalMemoryRuntimeSubsystem(
                formal_source_retriever=shared_formal_source_retriever,
            ),
            "TheoryDeveloper": TheoryDeveloperRuntimeSubsystem(
                theory_developer=theory_developer,
                n_runs=config.n_runs,
                seed=config.seed,
            ),
            "SimulationEvaluator": SimulationEvaluatorRuntimeSubsystem(
                proposal_agent=simulation_engineer,
            ),
            "AlgorithmEngineer": AlgorithmEngineerRuntimeSubsystem(
                out_dir=out_dir / "algorithm_sandbox",
                n_runs=config.n_runs,
                seed=config.seed,
                proposal_agent=algorithm_engineer,
            ),
            "FormalizationEvaluator": FormalizationEvaluatorRuntimeSubsystem(
                proposal_agent=formalizer,
                proof_verifier=proof_verifier,
                proof_state_provider=proof_state_provider,
                formal_source_retriever=shared_formal_source_retriever,
                proof_obligation_ids=config.proof_obligation_ids,
                max_proof_obligations=config.max_proof_obligations,
            ),
            "CriticEvaluator": CriticEvaluatorRuntimeSubsystem(
                proposal_agent=critic_evaluator,
                runtime_config=config,
            ),
        }
        if architect_coordinator is not None:
            subsystems = {
                "ArchitectCoordinator": ArchitectCoordinatorRuntimeSubsystem(
                    coordinator=architect_coordinator,
                    runtime_config=config,
                ),
                **subsystems,
            }
        runtime = AgentRuntime(
            subsystems=subsystems,
            blackboard=blackboard,
        )
        def record_progress(row: dict[str, Any]) -> None:
            _append_jsonl_row(
                progress_path,
                {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "question_id": question.id,
                    "question_title": question.title,
                    **row,
                },
            )

        initial_task = (
            AgentTask(
                task_id=f"architect:{question.id}",
                owner_subsystem="ArchitectCoordinator",
                objective=(
                    "Create the top-level AI Statistician execution plan, evidence gates, "
                    "retrieval priorities, and iteration policy before runtime execution."
                ),
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": dict(architect_context or {}),
                },
                allowed_tools=("model_backend", "blackboard"),
                expected_artifacts=("architect_coordinator_proposal",),
                acceptance_gate="validated coordinator packet with explicit non-proof boundary",
                stop_condition="coordinator routes to RetrievalMemory",
            )
            if architect_coordinator is not None
            else AgentTask(
                task_id=f"retrieve:{question.id}",
                owner_subsystem="RetrievalMemory",
                objective="Retrieve paper, statistical knowledge, and formal-source context before theory derivation.",
                inputs={
                    "question": _question_to_payload(question),
                    "architect_context": dict(architect_context or {}),
                },
                allowed_tools=("research_knowledge", "paper_index", "formal_source_retriever"),
                expected_artifacts=("retrieval_memory_manifest",),
                acceptance_gate="retrieval context recorded with explicit non-proof boundary",
                stop_condition="retrieval context routed to TheoryDeveloper",
            )
        )
        result = runtime.run(
            initial_task,
            max_iterations=config.max_iterations,
            max_transient_subsystem_retries=config.max_subsystem_retries,
            progress_callback=record_progress,
        )
        result_json = result.to_json()
        result_path = out_dir / f"{_safe_identifier(question.id)}_runtime_result.json"
        result_path.write_text(json.dumps(result_json, indent=2, default=str), encoding="utf-8")
        result_json["artifact_path"] = str(result_path)
        results.append(result_json)
        for trace in result_json["traces"]:
            trace_rows.append(
                {
                    "question_id": question.id,
                    "question_title": question.title,
                    **trace,
                }
            )

    traces_path = out_dir / "runtime_traces.jsonl"
    _write_jsonl(traces_path, trace_rows)
    llm_topology_path = out_dir / "runtime_llm_topology.json"
    llm_topology_path.write_text(json.dumps(llm_topology, indent=2, default=str), encoding="utf-8")
    manifest_path = out_dir / "research_agent_runtime_manifest.json"
    status_counts: dict[str, int] = {}
    for row in results:
        status = str(row["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    completion_summary = _runtime_completion_summary(results)
    failure_summary = _runtime_failure_summary(completion_summary)
    evidence_summary = _runtime_evidence_summary(results)
    proof_control_summary = evidence_summary["proof"]["proof_obligation_control"]
    manifest = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_stage": (
            "architect_retrieval_theory_simulation_algorithm_formalization_critic_environment_loop"
            if architect_coordinator is not None
            else "retrieval_theory_simulation_algorithm_formalization_critic_environment_loop"
        ),
        "runtime_evaluation_mode": config.evaluation_mode,
        "n_questions": len(questions),
        "config": asdict(config),
        "runtime_input_context": _runtime_input_context_summary(architect_context or {}),
        "status_counts": dict(sorted(status_counts.items())),
        "runtime_completion_summary": completion_summary,
        "runtime_failure_summary": failure_summary,
        "runtime_terminal_kind": failure_summary["terminal_kind"],
        "terminal_subsystem": failure_summary["terminal_subsystem"],
        "terminal_task_id": failure_summary["terminal_task_id"],
        "terminal_classification": failure_summary["terminal_classification"],
        "incomplete_pending_next_task_id": failure_summary["pending_next_task_id"],
        "failed_subsystem": failure_summary["failed_subsystem"],
        "failed_task_id": failure_summary["failed_task_id"],
        "failure_classification": failure_summary["failure_classification"],
        "runtime_evidence_summary": evidence_summary,
        "n_kernel_verified_subclaims": evidence_summary["proof"]["n_kernel_verified_subclaims"],
        "n_formal_gaps": evidence_summary["proof"]["n_formal_gaps"],
        "n_registered_proof_bank_obligation_candidates": proof_control_summary[
            "n_registered_proof_bank_obligation_candidates"
        ],
        "n_candidate_proof_obligations": proof_control_summary["n_candidate_proof_obligations"],
        "n_selected_proof_obligations": proof_control_summary["n_selected_proof_obligations"],
        "n_llm_requested_proof_obligations": len(
            proof_control_summary.get("llm_requested_proof_obligation_ids", []) or []
        ),
        "n_memory_kernel_verified_proof_obligations": len(
            proof_control_summary.get("memory_kernel_verified_proof_obligation_ids", []) or []
        ),
        "proof_bank_bridge_catalog_exhausted_by_memory": bool(
            proof_control_summary.get("proof_bank_bridge_catalog_exhausted_by_memory", False)
        ),
        "theorem_reduction_closure_required": bool(
            proof_control_summary.get("theorem_reduction_closure_required", False)
        ),
        "theorem_reduction_closure_already_kernel_verified": bool(
            proof_control_summary.get(
                "theorem_reduction_closure_already_kernel_verified",
                False,
            )
        ),
        "memory_kernel_verified_theorem_reduction_closure_work_order_ids": list(
            proof_control_summary.get(
                "memory_kernel_verified_theorem_reduction_closure_work_order_ids",
                [],
            )
            or []
        ),
        "memory_kernel_verified_theorem_reduction_closure_target_ids": list(
            proof_control_summary.get(
                "memory_kernel_verified_theorem_reduction_closure_target_ids",
                [],
            )
            or []
        ),
        "memory_kernel_verified_theorem_reduction_closure_goal_ids": list(
            proof_control_summary.get(
                "memory_kernel_verified_theorem_reduction_closure_goal_ids",
                [],
            )
            or []
        ),
        "memory_kernel_verified_source_theorem_semantic_primitive_ids": list(
            proof_control_summary.get(
                "memory_kernel_verified_source_theorem_semantic_primitive_ids",
                [],
            )
            or []
        ),
        "source_theorem_semantic_primitive_support_already_kernel_verified": bool(
            proof_control_summary.get(
                "source_theorem_semantic_primitive_support_already_kernel_verified",
                False,
            )
        ),
        "remaining_unverified_proof_bank_obligation_ids": list(
            proof_control_summary.get("remaining_unverified_proof_bank_obligation_ids", []) or []
        ),
        "selected_proof_obligation_ids": list(
            proof_control_summary.get("selected_proof_obligation_ids", []) or []
        ),
        "n_algorithm_sandbox_executed": evidence_summary["algorithm"]["n_algorithm_sandbox_executed"],
        "n_generated_code_sandbox_executed": evidence_summary["algorithm"]["n_generated_code_sandbox_executed"],
        "n_unsafe_generated_code_rejected": evidence_summary["algorithm"]["n_unsafe_generated_code_rejected"],
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "simulation_evidence_boundary": SIMULATION_NOT_PROOF_BOUNDARY,
        "llm_runtime_topology": llm_topology,
        "artifacts": {
            "runtime_progress_jsonl": str(progress_path),
            "runtime_traces_jsonl": str(traces_path),
            "runtime_llm_topology_json": str(llm_topology_path),
            "per_question_results": [str(row["artifact_path"]) for row in results],
        },
    }
    agenda_rows = _runtime_agenda_rows(results)
    learning_rows = _runtime_learning_rows(results)
    theorem_reduction_closure_work_order_rows = (
        _runtime_theorem_reduction_closure_work_order_rows(results)
    )
    source_theorem_semantic_primitive_work_order_rows = (
        _runtime_source_theorem_semantic_primitive_work_order_rows(results)
    )
    source_theorem_formal_environment_work_order_rows = (
        _runtime_source_theorem_formal_environment_work_order_rows(results)
    )
    source_theorem_promotion_work_order_rows = (
        _runtime_source_theorem_promotion_work_order_rows(results)
    )
    source_theorem_promotion_handoff_rows = (
        _runtime_source_theorem_promotion_handoff_rows(
            source_theorem_promotion_work_order_rows
        )
    )
    source_theorem_promotion_materialization_seed_rows = (
        _runtime_source_theorem_promotion_materialization_seed_rows(
            source_theorem_promotion_handoff_rows,
            runtime_out_dir=out_dir,
        )
    )
    gap_planner_bridge_rows = _runtime_formalization_gap_planner_bridge_rows(results)
    agenda_path = out_dir / "runtime_next_action_agenda.jsonl"
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    theorem_reduction_closure_work_orders_path = (
        out_dir / "runtime_theorem_reduction_closure_work_orders.jsonl"
    )
    source_theorem_semantic_primitive_work_orders_path = (
        out_dir / "runtime_source_theorem_semantic_primitive_work_orders.jsonl"
    )
    source_theorem_semantic_primitive_executor_work_orders_path = (
        out_dir
        / "runtime_source_theorem_semantic_primitive_work_orders_from_proof_body_executor.jsonl"
    )
    source_theorem_formal_environment_work_orders_path = (
        out_dir / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    )
    source_theorem_promotion_work_orders_path = (
        out_dir / "runtime_source_theorem_promotion_work_orders.jsonl"
    )
    source_theorem_promotion_handoffs_path = (
        out_dir / "runtime_source_theorem_promotion_handoffs.jsonl"
    )
    source_theorem_promotion_materialization_seeds_path = (
        out_dir / "runtime_source_theorem_promotion_materialization_seeds.jsonl"
    )
    source_theorem_promotion_materialization_seed_queue_dir = (
        out_dir / "runtime_source_theorem_promotion_materialization_seed_queue"
    )
    source_theorem_promotion_source_semantic_work_orders_path = (
        out_dir
        / "runtime_source_theorem_promotion_work_orders_from_source_semantic_support.jsonl"
    )
    source_theorem_promotion_source_semantic_handoffs_path = (
        out_dir
        / "runtime_source_theorem_promotion_handoffs_from_source_semantic_support.jsonl"
    )
    source_theorem_promotion_source_semantic_materialization_seeds_path = (
        out_dir
        / "runtime_source_theorem_promotion_materialization_seeds_from_source_semantic_support.jsonl"
    )
    source_theorem_promotion_source_semantic_materialization_seed_queue_dir = (
        out_dir
        / "runtime_source_theorem_promotion_materialization_seed_queue_from_source_semantic_support"
    )
    source_theorem_promotion_post_executor_work_orders_path = (
        out_dir
        / "runtime_source_theorem_promotion_work_orders_from_post_executor_semantic_support.jsonl"
    )
    source_theorem_promotion_post_executor_handoffs_path = (
        out_dir
        / "runtime_source_theorem_promotion_handoffs_from_post_executor_semantic_support.jsonl"
    )
    source_theorem_promotion_post_executor_materialization_seeds_path = (
        out_dir
        / "runtime_source_theorem_promotion_materialization_seeds_from_post_executor_semantic_support.jsonl"
    )
    source_theorem_promotion_post_executor_materialization_seed_queue_dir = (
        out_dir
        / "runtime_source_theorem_promotion_materialization_seed_queue_from_post_executor_semantic_support"
    )
    gap_planner_bridges_path = out_dir / "runtime_formalization_gap_planner_bridges.jsonl"
    gap_planner_seed_dir = out_dir / "runtime_formalization_gap_planner_seeds"
    gap_planner_target_intake_dir = out_dir / "runtime_formalization_gap_planner_target_intake"
    gap_planner_handoffs_path = out_dir / "runtime_formalization_gap_planner_handoffs.jsonl"
    _write_jsonl(agenda_path, agenda_rows)
    _write_jsonl(learning_path, learning_rows)
    _write_jsonl(
        theorem_reduction_closure_work_orders_path,
        theorem_reduction_closure_work_order_rows,
    )
    _write_jsonl(
        source_theorem_semantic_primitive_work_orders_path,
        source_theorem_semantic_primitive_work_order_rows,
    )
    _write_jsonl(
        source_theorem_formal_environment_work_orders_path,
        source_theorem_formal_environment_work_order_rows,
    )
    _write_jsonl(
        source_theorem_promotion_work_orders_path,
        source_theorem_promotion_work_order_rows,
    )
    _write_jsonl(
        source_theorem_promotion_handoffs_path,
        source_theorem_promotion_handoff_rows,
    )
    _write_jsonl(
        source_theorem_promotion_materialization_seeds_path,
        source_theorem_promotion_materialization_seed_rows,
    )
    _write_runtime_source_theorem_promotion_materialization_seed_queue(
        source_theorem_promotion_materialization_seed_rows,
        queue_dir=source_theorem_promotion_materialization_seed_queue_dir,
    )
    theorem_closure_bridge_manifest: dict[str, Any] | None = None
    if (
        config.theorem_closure_proofengineer_bridge
        and theorem_reduction_closure_work_order_rows
    ):
        theorem_closure_bridge_manifest = run_theorem_reduction_closure_proofengineer_bridge(
            out_dir=out_dir / "runtime_theorem_reduction_closure_proofengineer_bridge",
            queue_jsonl=theorem_reduction_closure_work_orders_path,
            question_id=questions[0].id if len(questions) == 1 else "",
            local_lean=config.theorem_closure_proofengineer_local_lean,
            lean_project=(
                Path(config.theorem_closure_proofengineer_lean_project)
                if config.theorem_closure_proofengineer_lean_project
                else None
            ),
            lean_timeout=config.theorem_closure_proofengineer_lean_timeout,
        )
    source_semantic_bridge_manifest: dict[str, Any] | None = None
    if (
        config.source_semantic_proofengineer_bridge
        and source_theorem_semantic_primitive_work_order_rows
    ):
        source_semantic_bridge_manifest = (
            run_source_theorem_semantic_primitive_proofengineer_bridge(
                out_dir=out_dir
                / "runtime_source_theorem_semantic_primitive_proofengineer_bridge",
                queue_jsonl=source_theorem_semantic_primitive_work_orders_path,
                question_id=questions[0].id if len(questions) == 1 else "",
                local_lean=config.source_semantic_proofengineer_local_lean,
                lean_project=(
                    Path(config.source_semantic_proofengineer_lean_project)
                    if config.source_semantic_proofengineer_lean_project
                    else None
                ),
                lean_timeout=config.source_semantic_proofengineer_lean_timeout,
            )
        )
    source_theorem_promotion_bridge_manifest: dict[str, Any] | None = None
    if (
        config.source_theorem_promotion_proofengineer_bridge
        and source_theorem_promotion_materialization_seed_rows
    ):
        source_theorem_promotion_bridge_manifest = (
            _run_runtime_source_theorem_promotion_proofengineer_bridge(
                seed_queue_dir=source_theorem_promotion_materialization_seed_queue_dir,
                out_dir=out_dir
                / "runtime_source_theorem_promotion_proofengineer_bridge",
                local_lean=config.source_theorem_promotion_proofengineer_local_lean,
                overwrite_artifacts=(
                    config.source_theorem_promotion_proofengineer_overwrite_artifacts
                ),
                lean_project=(
                    Path(config.source_theorem_promotion_proofengineer_lean_project)
                    if config.source_theorem_promotion_proofengineer_lean_project
                    else None
                ),
                lean_timeout=config.source_theorem_promotion_proofengineer_lean_timeout,
            )
        )
    source_theorem_promotion_bridge_learning_rows = (
        _runtime_source_theorem_promotion_bridge_learning_rows(
            source_theorem_promotion_bridge_manifest
        )
        if source_theorem_promotion_bridge_manifest is not None
        else []
    )
    theorem_closure_bridge_learning_rows = (
        _runtime_bridge_learning_rows(theorem_closure_bridge_manifest)
        if theorem_closure_bridge_manifest is not None
        else []
    )
    source_semantic_bridge_learning_rows = (
        _runtime_bridge_learning_rows(source_semantic_bridge_manifest)
        if source_semantic_bridge_manifest is not None
        else []
    )
    source_theorem_promotion_source_semantic_work_order_rows: list[dict[str, Any]] = []
    new_source_theorem_promotion_source_semantic_work_order_rows: list[
        dict[str, Any]
    ] = []
    source_theorem_promotion_source_semantic_handoff_rows: list[dict[str, Any]] = []
    source_theorem_promotion_source_semantic_materialization_seed_rows: list[
        dict[str, Any]
    ] = []
    source_theorem_promotion_source_semantic_bridge_manifest: dict[str, Any] | None = None
    source_theorem_promotion_source_semantic_bridge_learning_rows: list[
        dict[str, Any]
    ] = []
    source_theorem_formal_environment_bridge_manifest: dict[str, Any] | None = None
    source_theorem_formal_environment_bridge_queue = (
        source_theorem_formal_environment_work_orders_path
        if source_theorem_formal_environment_work_order_rows
        else None
    )
    if (
        source_theorem_formal_environment_bridge_queue is None
        and source_theorem_promotion_bridge_manifest is not None
        and source_theorem_promotion_bridge_manifest.get(
            "source_theorem_formal_environment_work_orders_jsonl"
        )
    ):
        source_theorem_formal_environment_bridge_queue = Path(
            str(
                source_theorem_promotion_bridge_manifest[
                    "source_theorem_formal_environment_work_orders_jsonl"
                ]
            )
        )
    (
        source_theorem_formal_environment_bridge_manifest,
        source_theorem_formal_environment_proof_body_executor_manifest,
        source_theorem_formal_environment_bridge_learning_rows,
        source_theorem_formal_environment_proof_body_executor_learning_rows,
    ) = _run_runtime_source_theorem_formal_environment_bridge_stack(
        out_dir=out_dir / "runtime_source_theorem_formal_environment_proofengineer_bridge",
        queue_jsonl=source_theorem_formal_environment_bridge_queue,
        question_id=questions[0].id if len(questions) == 1 else "",
        config=config,
    )
    source_theorem_formal_environment_source_semantic_bridge_manifest: (
        dict[str, Any] | None
    ) = None
    source_theorem_formal_environment_source_semantic_proof_body_executor_manifest: (
        dict[str, Any] | None
    ) = None
    source_theorem_formal_environment_source_semantic_bridge_learning_rows: list[
        dict[str, Any]
    ] = []
    source_theorem_formal_environment_source_semantic_proof_body_executor_learning_rows: list[
        dict[str, Any]
    ] = []
    if theorem_closure_bridge_learning_rows:
        learning_rows.extend(theorem_closure_bridge_learning_rows)
        _write_jsonl(learning_path, learning_rows)
    if source_semantic_bridge_learning_rows:
        learning_rows.extend(source_semantic_bridge_learning_rows)
        _write_jsonl(learning_path, learning_rows)
        source_theorem_promotion_source_semantic_work_order_rows = (
            _runtime_source_theorem_promotion_work_order_rows_from_learning_rows(
                results,
                learning_rows,
                architect_context=architect_context,
                source_runtime_learning_task=(
                    "source_theorem_semantic_primitive_kernel_overlay"
                ),
            )
        )
        existing_promotion_work_order_ids = {
            str(row.get("work_order_id", "") or "")
            for row in source_theorem_promotion_work_order_rows
            if isinstance(row, Mapping)
        }
        new_source_theorem_promotion_source_semantic_work_order_rows = [
            row
            for row in source_theorem_promotion_source_semantic_work_order_rows
            if str(row.get("work_order_id", "") or "")
            not in existing_promotion_work_order_ids
        ]
        if new_source_theorem_promotion_source_semantic_work_order_rows:
            _write_jsonl(
                source_theorem_promotion_source_semantic_work_orders_path,
                new_source_theorem_promotion_source_semantic_work_order_rows,
            )
            source_theorem_promotion_work_order_rows.extend(
                new_source_theorem_promotion_source_semantic_work_order_rows
            )
            _write_jsonl(
                source_theorem_promotion_work_orders_path,
                source_theorem_promotion_work_order_rows,
            )
            source_theorem_promotion_handoff_rows = (
                _runtime_source_theorem_promotion_handoff_rows(
                    source_theorem_promotion_work_order_rows
                )
            )
            source_theorem_promotion_materialization_seed_rows = (
                _runtime_source_theorem_promotion_materialization_seed_rows(
                    source_theorem_promotion_handoff_rows,
                    runtime_out_dir=out_dir,
                )
            )
            _write_jsonl(
                source_theorem_promotion_handoffs_path,
                source_theorem_promotion_handoff_rows,
            )
            _write_jsonl(
                source_theorem_promotion_materialization_seeds_path,
                source_theorem_promotion_materialization_seed_rows,
            )
            _write_runtime_source_theorem_promotion_materialization_seed_queue(
                source_theorem_promotion_materialization_seed_rows,
                queue_dir=source_theorem_promotion_materialization_seed_queue_dir,
            )
            source_theorem_promotion_source_semantic_handoff_rows = (
                _runtime_source_theorem_promotion_handoff_rows(
                    new_source_theorem_promotion_source_semantic_work_order_rows
                )
            )
            source_theorem_promotion_source_semantic_materialization_seed_rows = (
                _runtime_source_theorem_promotion_materialization_seed_rows(
                    source_theorem_promotion_source_semantic_handoff_rows,
                    runtime_out_dir=out_dir,
                )
            )
            _write_jsonl(
                source_theorem_promotion_source_semantic_handoffs_path,
                source_theorem_promotion_source_semantic_handoff_rows,
            )
            _write_jsonl(
                source_theorem_promotion_source_semantic_materialization_seeds_path,
                source_theorem_promotion_source_semantic_materialization_seed_rows,
            )
            _write_runtime_source_theorem_promotion_materialization_seed_queue(
                source_theorem_promotion_source_semantic_materialization_seed_rows,
                queue_dir=(
                    source_theorem_promotion_source_semantic_materialization_seed_queue_dir
                ),
            )
            if config.source_theorem_promotion_proofengineer_bridge:
                source_theorem_promotion_source_semantic_bridge_manifest = (
                    _run_runtime_source_theorem_promotion_proofengineer_bridge(
                        seed_queue_dir=(
                            source_theorem_promotion_source_semantic_materialization_seed_queue_dir
                        ),
                        out_dir=out_dir
                        / "runtime_source_theorem_promotion_proofengineer_bridge_from_source_semantic_support",
                        local_lean=(
                            config.source_theorem_promotion_proofengineer_local_lean
                        ),
                        overwrite_artifacts=(
                            config.source_theorem_promotion_proofengineer_overwrite_artifacts
                        ),
                        lean_project=(
                            Path(
                                config.source_theorem_promotion_proofengineer_lean_project
                            )
                            if config.source_theorem_promotion_proofengineer_lean_project
                            else None
                        ),
                        lean_timeout=(
                            config.source_theorem_promotion_proofengineer_lean_timeout
                        ),
                    )
                )
                source_theorem_promotion_source_semantic_bridge_learning_rows = (
                    _runtime_source_theorem_promotion_bridge_learning_rows(
                        source_theorem_promotion_source_semantic_bridge_manifest
                    )
                )
                if source_theorem_promotion_source_semantic_bridge_learning_rows:
                    learning_rows.extend(
                        source_theorem_promotion_source_semantic_bridge_learning_rows
                    )
                    _write_jsonl(learning_path, learning_rows)
                source_semantic_formal_environment_queue_value = str(
                    source_theorem_promotion_source_semantic_bridge_manifest.get(
                        "source_theorem_formal_environment_work_orders_jsonl",
                        "",
                    )
                    or ""
                )
                if source_semantic_formal_environment_queue_value:
                    (
                        source_theorem_formal_environment_source_semantic_bridge_manifest,
                        source_theorem_formal_environment_source_semantic_proof_body_executor_manifest,
                        source_theorem_formal_environment_source_semantic_bridge_learning_rows,
                        source_theorem_formal_environment_source_semantic_proof_body_executor_learning_rows,
                    ) = _run_runtime_source_theorem_formal_environment_bridge_stack(
                        out_dir=out_dir
                        / "runtime_source_theorem_formal_environment_proofengineer_bridge_from_source_semantic_promotion",
                        queue_jsonl=Path(source_semantic_formal_environment_queue_value),
                        question_id=questions[0].id if len(questions) == 1 else "",
                        config=config,
                    )
                    if (
                        source_theorem_formal_environment_source_semantic_bridge_learning_rows
                    ):
                        learning_rows.extend(
                            source_theorem_formal_environment_source_semantic_bridge_learning_rows
                        )
                        _write_jsonl(learning_path, learning_rows)
                    if (
                        source_theorem_formal_environment_source_semantic_proof_body_executor_learning_rows
                    ):
                        learning_rows.extend(
                            source_theorem_formal_environment_source_semantic_proof_body_executor_learning_rows
                        )
                        _write_jsonl(learning_path, learning_rows)
    if source_theorem_promotion_bridge_learning_rows:
        learning_rows.extend(source_theorem_promotion_bridge_learning_rows)
        _write_jsonl(learning_path, learning_rows)
    if source_theorem_formal_environment_bridge_learning_rows:
        learning_rows.extend(source_theorem_formal_environment_bridge_learning_rows)
        _write_jsonl(learning_path, learning_rows)
    if source_theorem_formal_environment_proof_body_executor_learning_rows:
        learning_rows.extend(source_theorem_formal_environment_proof_body_executor_learning_rows)
        _write_jsonl(learning_path, learning_rows)
    all_source_theorem_formal_environment_proof_body_executor_learning_rows = [
        *source_theorem_formal_environment_proof_body_executor_learning_rows,
        *source_theorem_formal_environment_source_semantic_proof_body_executor_learning_rows,
    ]
    source_theorem_semantic_primitive_executor_work_order_rows = (
        _runtime_source_theorem_semantic_primitive_work_order_rows_from_learning_rows(
            all_source_theorem_formal_environment_proof_body_executor_learning_rows
        )
    )
    source_semantic_post_executor_bridge_manifest: dict[str, Any] | None = None
    source_semantic_post_executor_bridge_learning_rows: list[dict[str, Any]] = []
    new_semantic_work_order_rows: list[dict[str, Any]] = []
    source_theorem_promotion_post_executor_work_order_rows: list[dict[str, Any]] = []
    new_source_theorem_promotion_post_executor_work_order_rows: list[dict[str, Any]] = []
    source_theorem_promotion_post_executor_handoff_rows: list[dict[str, Any]] = []
    source_theorem_promotion_post_executor_materialization_seed_rows: list[
        dict[str, Any]
    ] = []
    source_theorem_promotion_post_executor_bridge_manifest: dict[str, Any] | None = None
    source_theorem_promotion_post_executor_bridge_learning_rows: list[dict[str, Any]] = []
    if source_theorem_semantic_primitive_executor_work_order_rows:
        seen_semantic_work_order_ids = {
            str(row.get("work_order_id", "") or "")
            for row in source_theorem_semantic_primitive_work_order_rows
            if isinstance(row, Mapping)
        }
        new_semantic_work_order_rows = [
            row
            for row in source_theorem_semantic_primitive_executor_work_order_rows
            if str(row.get("work_order_id", "") or "")
            not in seen_semantic_work_order_ids
        ]
        if new_semantic_work_order_rows:
            _write_jsonl(
                source_theorem_semantic_primitive_executor_work_orders_path,
                new_semantic_work_order_rows,
            )
            source_theorem_semantic_primitive_work_order_rows.extend(
                new_semantic_work_order_rows
            )
            _write_jsonl(
                source_theorem_semantic_primitive_work_orders_path,
                source_theorem_semantic_primitive_work_order_rows,
            )
            if config.source_semantic_proofengineer_bridge:
                source_semantic_post_executor_bridge_manifest = (
                    run_source_theorem_semantic_primitive_proofengineer_bridge(
                        out_dir=out_dir
                        / "runtime_source_theorem_semantic_primitive_proofengineer_bridge_from_proof_body_executor",
                        queue_jsonl=source_theorem_semantic_primitive_executor_work_orders_path,
                        question_id=questions[0].id if len(questions) == 1 else "",
                        local_lean=config.source_semantic_proofengineer_local_lean,
                        lean_project=(
                            Path(config.source_semantic_proofengineer_lean_project)
                            if config.source_semantic_proofengineer_lean_project
                            else None
                        ),
                        lean_timeout=config.source_semantic_proofengineer_lean_timeout,
                    )
                )
                source_semantic_post_executor_bridge_learning_rows = (
                    _runtime_bridge_learning_rows(
                        source_semantic_post_executor_bridge_manifest
                    )
                )
                if source_semantic_post_executor_bridge_learning_rows:
                    learning_rows.extend(source_semantic_post_executor_bridge_learning_rows)
                    _write_jsonl(learning_path, learning_rows)
                    source_theorem_promotion_post_executor_work_order_rows = (
                        _runtime_source_theorem_promotion_work_order_rows_from_learning_rows(
                            results,
                            learning_rows,
                            architect_context=architect_context,
                            source_runtime_learning_task=(
                                "source_theorem_semantic_primitive_kernel_overlay"
                            ),
                        )
                    )
                    existing_promotion_work_order_ids = {
                        str(row.get("work_order_id", "") or "")
                        for row in source_theorem_promotion_work_order_rows
                        if isinstance(row, Mapping)
                    }
                    new_source_theorem_promotion_post_executor_work_order_rows = [
                        row
                        for row in source_theorem_promotion_post_executor_work_order_rows
                        if str(row.get("work_order_id", "") or "")
                        not in existing_promotion_work_order_ids
                    ]
                    if new_source_theorem_promotion_post_executor_work_order_rows:
                        _write_jsonl(
                            source_theorem_promotion_post_executor_work_orders_path,
                            new_source_theorem_promotion_post_executor_work_order_rows,
                        )
                        source_theorem_promotion_work_order_rows.extend(
                            new_source_theorem_promotion_post_executor_work_order_rows
                        )
                        _write_jsonl(
                            source_theorem_promotion_work_orders_path,
                            source_theorem_promotion_work_order_rows,
                        )
                        source_theorem_promotion_handoff_rows = (
                            _runtime_source_theorem_promotion_handoff_rows(
                                source_theorem_promotion_work_order_rows
                            )
                        )
                        source_theorem_promotion_materialization_seed_rows = (
                            _runtime_source_theorem_promotion_materialization_seed_rows(
                                source_theorem_promotion_handoff_rows,
                                runtime_out_dir=out_dir,
                            )
                        )
                        _write_jsonl(
                            source_theorem_promotion_handoffs_path,
                            source_theorem_promotion_handoff_rows,
                        )
                        _write_jsonl(
                            source_theorem_promotion_materialization_seeds_path,
                            source_theorem_promotion_materialization_seed_rows,
                        )
                        _write_runtime_source_theorem_promotion_materialization_seed_queue(
                            source_theorem_promotion_materialization_seed_rows,
                            queue_dir=source_theorem_promotion_materialization_seed_queue_dir,
                        )
                        source_theorem_promotion_post_executor_handoff_rows = (
                            _runtime_source_theorem_promotion_handoff_rows(
                                new_source_theorem_promotion_post_executor_work_order_rows
                            )
                        )
                        source_theorem_promotion_post_executor_materialization_seed_rows = (
                            _runtime_source_theorem_promotion_materialization_seed_rows(
                                source_theorem_promotion_post_executor_handoff_rows,
                                runtime_out_dir=out_dir,
                            )
                        )
                        _write_jsonl(
                            source_theorem_promotion_post_executor_handoffs_path,
                            source_theorem_promotion_post_executor_handoff_rows,
                        )
                        _write_jsonl(
                            source_theorem_promotion_post_executor_materialization_seeds_path,
                            source_theorem_promotion_post_executor_materialization_seed_rows,
                        )
                        _write_runtime_source_theorem_promotion_materialization_seed_queue(
                            source_theorem_promotion_post_executor_materialization_seed_rows,
                            queue_dir=(
                                source_theorem_promotion_post_executor_materialization_seed_queue_dir
                            ),
                        )
                        if config.source_theorem_promotion_proofengineer_bridge:
                            source_theorem_promotion_post_executor_bridge_manifest = (
                                _run_runtime_source_theorem_promotion_proofengineer_bridge(
                                    seed_queue_dir=(
                                        source_theorem_promotion_post_executor_materialization_seed_queue_dir
                                    ),
                                    out_dir=out_dir
                                    / "runtime_source_theorem_promotion_proofengineer_bridge_from_post_executor_semantic_support",
                                    local_lean=(
                                        config.source_theorem_promotion_proofengineer_local_lean
                                    ),
                                    overwrite_artifacts=(
                                        config.source_theorem_promotion_proofengineer_overwrite_artifacts
                                    ),
                                    lean_project=(
                                        Path(
                                            config.source_theorem_promotion_proofengineer_lean_project
                                        )
                                        if config.source_theorem_promotion_proofengineer_lean_project
                                        else None
                                    ),
                                    lean_timeout=(
                                        config.source_theorem_promotion_proofengineer_lean_timeout
                                    ),
                                )
                            )
                            source_theorem_promotion_post_executor_bridge_learning_rows = (
                                _runtime_source_theorem_promotion_bridge_learning_rows(
                                    source_theorem_promotion_post_executor_bridge_manifest
                                )
                            )
                            if (
                                source_theorem_promotion_post_executor_bridge_learning_rows
                            ):
                                learning_rows.extend(
                                    source_theorem_promotion_post_executor_bridge_learning_rows
                                )
                                _write_jsonl(learning_path, learning_rows)
    source_theorem_formal_environment_executor_work_order_rows = (
        _runtime_source_theorem_formal_environment_work_order_rows_from_learning_rows(
            source_theorem_formal_environment_proof_body_executor_learning_rows
        )
    )
    if source_theorem_formal_environment_executor_work_order_rows:
        seen_work_order_ids = {
            str(row.get("work_order_id", "") or "")
            for row in source_theorem_formal_environment_work_order_rows
            if isinstance(row, Mapping)
        }
        new_work_order_rows = [
            row
            for row in source_theorem_formal_environment_executor_work_order_rows
            if str(row.get("work_order_id", "") or "") not in seen_work_order_ids
        ]
        if new_work_order_rows:
            source_theorem_formal_environment_work_order_rows.extend(
                new_work_order_rows
            )
            _write_jsonl(
                source_theorem_formal_environment_work_orders_path,
                source_theorem_formal_environment_work_order_rows,
            )
    _write_runtime_formalization_gap_planner_seed_files(
        gap_planner_bridge_rows,
        seed_dir=gap_planner_seed_dir,
    )
    _write_runtime_formalization_gap_planner_target_intake_files(
        gap_planner_bridge_rows,
        target_intake_dir=gap_planner_target_intake_dir,
    )
    gap_planner_handoff_rows = _runtime_formalization_gap_planner_handoff_rows(
        gap_planner_bridge_rows,
        runtime_out_dir=out_dir,
    )
    _write_jsonl(gap_planner_handoffs_path, gap_planner_handoff_rows)
    _write_jsonl(gap_planner_bridges_path, gap_planner_bridge_rows)
    manifest["artifacts"]["runtime_next_action_agenda_jsonl"] = str(agenda_path)
    manifest["artifacts"]["runtime_learning_rows_jsonl"] = str(learning_path)
    manifest["artifacts"]["runtime_theorem_reduction_closure_work_orders_jsonl"] = str(
        theorem_reduction_closure_work_orders_path
    )
    manifest["artifacts"][
        "runtime_source_theorem_semantic_primitive_work_orders_jsonl"
    ] = str(source_theorem_semantic_primitive_work_orders_path)
    if new_semantic_work_order_rows:
        manifest["artifacts"][
            "runtime_source_theorem_semantic_primitive_work_orders_from_proof_body_executor_jsonl"
        ] = str(source_theorem_semantic_primitive_executor_work_orders_path)
    manifest["artifacts"][
        "runtime_source_theorem_formal_environment_work_orders_jsonl"
    ] = str(source_theorem_formal_environment_work_orders_path)
    manifest["artifacts"]["runtime_source_theorem_promotion_work_orders_jsonl"] = str(
        source_theorem_promotion_work_orders_path
    )
    manifest["artifacts"]["runtime_source_theorem_promotion_handoffs_jsonl"] = str(
        source_theorem_promotion_handoffs_path
    )
    manifest["artifacts"][
        "runtime_source_theorem_promotion_materialization_seeds_jsonl"
    ] = str(source_theorem_promotion_materialization_seeds_path)
    manifest["artifacts"][
        "runtime_source_theorem_promotion_materialization_seed_queue_dir"
    ] = str(source_theorem_promotion_materialization_seed_queue_dir)
    if new_source_theorem_promotion_source_semantic_work_order_rows:
        manifest["artifacts"][
            "runtime_source_theorem_promotion_work_orders_from_source_semantic_support_jsonl"
        ] = str(source_theorem_promotion_source_semantic_work_orders_path)
        manifest["artifacts"][
            "runtime_source_theorem_promotion_handoffs_from_source_semantic_support_jsonl"
        ] = str(source_theorem_promotion_source_semantic_handoffs_path)
        manifest["artifacts"][
            "runtime_source_theorem_promotion_materialization_seeds_from_source_semantic_support_jsonl"
        ] = str(source_theorem_promotion_source_semantic_materialization_seeds_path)
        manifest["artifacts"][
            "runtime_source_theorem_promotion_materialization_seed_queue_from_source_semantic_support_dir"
        ] = str(source_theorem_promotion_source_semantic_materialization_seed_queue_dir)
    if new_source_theorem_promotion_post_executor_work_order_rows:
        manifest["artifacts"][
            "runtime_source_theorem_promotion_work_orders_from_post_executor_semantic_support_jsonl"
        ] = str(source_theorem_promotion_post_executor_work_orders_path)
        manifest["artifacts"][
            "runtime_source_theorem_promotion_handoffs_from_post_executor_semantic_support_jsonl"
        ] = str(source_theorem_promotion_post_executor_handoffs_path)
        manifest["artifacts"][
            "runtime_source_theorem_promotion_materialization_seeds_from_post_executor_semantic_support_jsonl"
        ] = str(source_theorem_promotion_post_executor_materialization_seeds_path)
        manifest["artifacts"][
            "runtime_source_theorem_promotion_materialization_seed_queue_from_post_executor_semantic_support_dir"
        ] = str(source_theorem_promotion_post_executor_materialization_seed_queue_dir)
    if theorem_closure_bridge_manifest is not None:
        manifest["artifacts"][
            "runtime_theorem_reduction_closure_proofengineer_bridge_manifest"
        ] = str(
            out_dir
            / "runtime_theorem_reduction_closure_proofengineer_bridge"
            / "theorem_reduction_closure_proofengineer_bridge_manifest.json"
        )
        manifest["artifacts"][
            "runtime_theorem_reduction_closure_proofengineer_learning_rows_jsonl"
        ] = str(theorem_closure_bridge_manifest["runtime_learning_rows_jsonl"])
        manifest["artifacts"][
            "runtime_theorem_reduction_closure_proofengineer_audit_manifest"
        ] = str(theorem_closure_bridge_manifest["audit_manifest"])
    if source_semantic_bridge_manifest is not None:
        manifest["artifacts"][
            "runtime_source_theorem_semantic_primitive_proofengineer_bridge_manifest"
        ] = str(
            out_dir
            / "runtime_source_theorem_semantic_primitive_proofengineer_bridge"
            / "source_theorem_semantic_primitive_proofengineer_bridge_manifest.json"
        )
        manifest["artifacts"][
            "runtime_source_theorem_semantic_primitive_proofengineer_learning_rows_jsonl"
        ] = str(source_semantic_bridge_manifest["runtime_learning_rows_jsonl"])
        manifest["artifacts"][
            "runtime_source_theorem_semantic_primitive_proofengineer_learning_export_manifest"
        ] = str(source_semantic_bridge_manifest["runtime_learning_export_manifest"])
        manifest["artifacts"][
            "runtime_source_theorem_semantic_primitive_proofengineer_checks_jsonl"
        ] = str(source_semantic_bridge_manifest["checks_jsonl"])
    if source_semantic_post_executor_bridge_manifest is not None:
        manifest["artifacts"][
            "runtime_source_theorem_semantic_primitive_proofengineer_bridge_from_proof_body_executor_manifest"
        ] = str(
            out_dir
            / "runtime_source_theorem_semantic_primitive_proofengineer_bridge_from_proof_body_executor"
            / "source_theorem_semantic_primitive_proofengineer_bridge_manifest.json"
        )
        manifest["artifacts"][
            "runtime_source_theorem_semantic_primitive_proofengineer_from_proof_body_executor_learning_rows_jsonl"
        ] = str(source_semantic_post_executor_bridge_manifest["runtime_learning_rows_jsonl"])
        manifest["artifacts"][
            "runtime_source_theorem_semantic_primitive_proofengineer_from_proof_body_executor_learning_export_manifest"
        ] = str(
            source_semantic_post_executor_bridge_manifest[
                "runtime_learning_export_manifest"
            ]
        )
        manifest["artifacts"][
            "runtime_source_theorem_semantic_primitive_proofengineer_from_proof_body_executor_checks_jsonl"
        ] = str(source_semantic_post_executor_bridge_manifest["checks_jsonl"])
    if source_theorem_formal_environment_bridge_manifest is not None:
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proofengineer_bridge_manifest"
        ] = str(
            out_dir
            / "runtime_source_theorem_formal_environment_proofengineer_bridge"
            / "source_theorem_formal_environment_proofengineer_bridge_manifest.json"
        )
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proofengineer_repair_packets_jsonl"
        ] = str(source_theorem_formal_environment_bridge_manifest["repair_packets_jsonl"])
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proofengineer_learning_rows_jsonl"
        ] = str(
            source_theorem_formal_environment_bridge_manifest[
                "runtime_learning_rows_jsonl"
            ]
        )
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proofengineer_learning_export_manifest"
        ] = str(
            source_theorem_formal_environment_bridge_manifest[
                "runtime_learning_export_manifest"
            ]
        )
        if source_theorem_formal_environment_bridge_manifest.get(
            "signature_probe_manifest"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_signature_probe_manifest"
            ] = str(
                source_theorem_formal_environment_bridge_manifest[
                    "signature_probe_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_signature_probe_rows_jsonl"
            ] = str(
                source_theorem_formal_environment_bridge_manifest[
                    "signature_probe_rows_jsonl"
                ]
            )
        if source_theorem_formal_environment_bridge_manifest.get(
            "proof_body_work_orders_jsonl"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_proof_body_work_orders_jsonl"
            ] = str(
                source_theorem_formal_environment_bridge_manifest[
                    "proof_body_work_orders_jsonl"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_proof_body_work_order_manifest"
            ] = str(
                source_theorem_formal_environment_bridge_manifest[
                    "proof_body_work_order_manifest"
                ]
            )
        if source_theorem_formal_environment_bridge_manifest.get(
            "proof_body_execution_queue_jsonl"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_proof_body_execution_queue_jsonl"
            ] = str(
                source_theorem_formal_environment_bridge_manifest[
                    "proof_body_execution_queue_jsonl"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_proof_body_execution_queue_manifest"
            ] = str(
                source_theorem_formal_environment_bridge_manifest[
                    "proof_body_execution_queue_manifest"
                ]
            )
    if source_theorem_formal_environment_proof_body_executor_manifest is not None:
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proof_body_executor_manifest"
        ] = str(
            source_theorem_formal_environment_proof_body_executor_manifest[
                "execution_result_manifest"
            ]
        )
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proof_body_executor_results_jsonl"
        ] = str(
            source_theorem_formal_environment_proof_body_executor_manifest[
                "execution_results_jsonl"
            ]
        )
        executor_learning_export = (
            source_theorem_formal_environment_proof_body_executor_manifest.get(
                "runtime_learning_export",
                {},
            )
        )
        if isinstance(executor_learning_export, Mapping):
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proof_body_executor_learning_rows_jsonl"
            ] = str(executor_learning_export.get("runtime_learning_rows_jsonl", "") or "")
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proof_body_executor_learning_manifest"
            ] = str(executor_learning_export.get("runtime_learning_manifest", "") or "")
    if source_theorem_formal_environment_source_semantic_bridge_manifest is not None:
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proofengineer_bridge_from_source_semantic_promotion_manifest"
        ] = str(
            out_dir
            / "runtime_source_theorem_formal_environment_proofengineer_bridge_from_source_semantic_promotion"
            / "source_theorem_formal_environment_proofengineer_bridge_manifest.json"
        )
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proofengineer_from_source_semantic_promotion_repair_packets_jsonl"
        ] = str(
            source_theorem_formal_environment_source_semantic_bridge_manifest[
                "repair_packets_jsonl"
            ]
        )
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proofengineer_from_source_semantic_promotion_learning_rows_jsonl"
        ] = str(
            source_theorem_formal_environment_source_semantic_bridge_manifest[
                "runtime_learning_rows_jsonl"
            ]
        )
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proofengineer_from_source_semantic_promotion_learning_export_manifest"
        ] = str(
            source_theorem_formal_environment_source_semantic_bridge_manifest[
                "runtime_learning_export_manifest"
            ]
        )
        if source_theorem_formal_environment_source_semantic_bridge_manifest.get(
            "signature_probe_manifest"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_from_source_semantic_promotion_signature_probe_manifest"
            ] = str(
                source_theorem_formal_environment_source_semantic_bridge_manifest[
                    "signature_probe_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_from_source_semantic_promotion_signature_probe_rows_jsonl"
            ] = str(
                source_theorem_formal_environment_source_semantic_bridge_manifest[
                    "signature_probe_rows_jsonl"
                ]
            )
        if source_theorem_formal_environment_source_semantic_bridge_manifest.get(
            "proof_body_work_orders_jsonl"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_from_source_semantic_promotion_proof_body_work_orders_jsonl"
            ] = str(
                source_theorem_formal_environment_source_semantic_bridge_manifest[
                    "proof_body_work_orders_jsonl"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_from_source_semantic_promotion_proof_body_work_order_manifest"
            ] = str(
                source_theorem_formal_environment_source_semantic_bridge_manifest[
                    "proof_body_work_order_manifest"
                ]
            )
        if source_theorem_formal_environment_source_semantic_bridge_manifest.get(
            "proof_body_execution_queue_jsonl"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_from_source_semantic_promotion_proof_body_execution_queue_jsonl"
            ] = str(
                source_theorem_formal_environment_source_semantic_bridge_manifest[
                    "proof_body_execution_queue_jsonl"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proofengineer_from_source_semantic_promotion_proof_body_execution_queue_manifest"
            ] = str(
                source_theorem_formal_environment_source_semantic_bridge_manifest[
                    "proof_body_execution_queue_manifest"
                ]
            )
    if (
        source_theorem_formal_environment_source_semantic_proof_body_executor_manifest
        is not None
    ):
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_manifest"
        ] = str(
            source_theorem_formal_environment_source_semantic_proof_body_executor_manifest[
                "execution_result_manifest"
            ]
        )
        manifest["artifacts"][
            "runtime_source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_results_jsonl"
        ] = str(
            source_theorem_formal_environment_source_semantic_proof_body_executor_manifest[
                "execution_results_jsonl"
            ]
        )
        executor_learning_export = (
            source_theorem_formal_environment_source_semantic_proof_body_executor_manifest.get(
                "runtime_learning_export",
                {},
            )
        )
        if isinstance(executor_learning_export, Mapping):
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_learning_rows_jsonl"
            ] = str(executor_learning_export.get("runtime_learning_rows_jsonl", "") or "")
            manifest["artifacts"][
                "runtime_source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_learning_manifest"
            ] = str(executor_learning_export.get("runtime_learning_manifest", "") or "")
    if source_theorem_promotion_bridge_manifest is not None:
        manifest["artifacts"][
            "runtime_source_theorem_promotion_proofengineer_bridge_manifest"
        ] = str(source_theorem_promotion_bridge_manifest["bridge_manifest"])
        manifest["artifacts"][
            "runtime_source_theorem_promotion_proofengineer_materializer_manifest"
        ] = str(source_theorem_promotion_bridge_manifest["materializer_manifest"])
        manifest["artifacts"][
            "runtime_source_theorem_promotion_proofengineer_materializer_dir"
        ] = str(source_theorem_promotion_bridge_manifest["materializer_dir"])
        if source_theorem_promotion_bridge_manifest.get("artifact_verifier_manifest"):
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_artifact_verifier_manifest"
            ] = str(
                source_theorem_promotion_bridge_manifest[
                    "artifact_verifier_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_artifact_verifier_dir"
            ] = str(source_theorem_promotion_bridge_manifest["artifact_verifier_dir"])
        if source_theorem_promotion_bridge_manifest.get(
            "source_theorem_formal_environment_work_order_manifest"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_formal_environment_work_order_manifest"
            ] = str(
                source_theorem_promotion_bridge_manifest[
                    "source_theorem_formal_environment_work_order_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_formal_environment_work_orders_jsonl"
            ] = str(
                source_theorem_promotion_bridge_manifest[
                    "source_theorem_formal_environment_work_orders_jsonl"
                ]
            )
        if source_theorem_promotion_bridge_manifest.get(
            "source_theorem_promotion_queue_manifest"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_promotion_queue_manifest"
            ] = str(
                source_theorem_promotion_bridge_manifest[
                    "source_theorem_promotion_queue_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_promotion_queue_dir"
            ] = str(
                source_theorem_promotion_bridge_manifest[
                    "source_theorem_promotion_queue_dir"
                ]
            )
        if source_theorem_promotion_bridge_manifest.get(
            "source_theorem_integrator_manifest"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_source_theorem_integrator_manifest"
            ] = str(
                source_theorem_promotion_bridge_manifest[
                    "source_theorem_integrator_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_source_theorem_integrator_dir"
            ] = str(
                source_theorem_promotion_bridge_manifest[
                    "source_theorem_integrator_dir"
                ]
            )
    if source_theorem_promotion_source_semantic_bridge_manifest is not None:
        manifest["artifacts"][
            "runtime_source_theorem_promotion_proofengineer_bridge_from_source_semantic_support_manifest"
        ] = str(source_theorem_promotion_source_semantic_bridge_manifest["bridge_manifest"])
        manifest["artifacts"][
            "runtime_source_theorem_promotion_proofengineer_from_source_semantic_support_materializer_manifest"
        ] = str(
            source_theorem_promotion_source_semantic_bridge_manifest[
                "materializer_manifest"
            ]
        )
        manifest["artifacts"][
            "runtime_source_theorem_promotion_proofengineer_from_source_semantic_support_materializer_dir"
        ] = str(source_theorem_promotion_source_semantic_bridge_manifest["materializer_dir"])
        if source_theorem_promotion_source_semantic_bridge_manifest.get(
            "artifact_verifier_manifest"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_from_source_semantic_support_artifact_verifier_manifest"
            ] = str(
                source_theorem_promotion_source_semantic_bridge_manifest[
                    "artifact_verifier_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_from_source_semantic_support_artifact_verifier_dir"
            ] = str(
                source_theorem_promotion_source_semantic_bridge_manifest[
                    "artifact_verifier_dir"
                ]
            )
        if source_theorem_promotion_source_semantic_bridge_manifest.get(
            "source_theorem_formal_environment_work_order_manifest"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_from_source_semantic_support_formal_environment_work_order_manifest"
            ] = str(
                source_theorem_promotion_source_semantic_bridge_manifest[
                    "source_theorem_formal_environment_work_order_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_from_source_semantic_support_formal_environment_work_orders_jsonl"
            ] = str(
                source_theorem_promotion_source_semantic_bridge_manifest[
                    "source_theorem_formal_environment_work_orders_jsonl"
                ]
            )
    if source_theorem_promotion_post_executor_bridge_manifest is not None:
        manifest["artifacts"][
            "runtime_source_theorem_promotion_proofengineer_bridge_from_post_executor_semantic_support_manifest"
        ] = str(source_theorem_promotion_post_executor_bridge_manifest["bridge_manifest"])
        manifest["artifacts"][
            "runtime_source_theorem_promotion_proofengineer_from_post_executor_semantic_support_materializer_manifest"
        ] = str(
            source_theorem_promotion_post_executor_bridge_manifest[
                "materializer_manifest"
            ]
        )
        manifest["artifacts"][
            "runtime_source_theorem_promotion_proofengineer_from_post_executor_semantic_support_materializer_dir"
        ] = str(
            source_theorem_promotion_post_executor_bridge_manifest["materializer_dir"]
        )
        if source_theorem_promotion_post_executor_bridge_manifest.get(
            "artifact_verifier_manifest"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_from_post_executor_semantic_support_artifact_verifier_manifest"
            ] = str(
                source_theorem_promotion_post_executor_bridge_manifest[
                    "artifact_verifier_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_from_post_executor_semantic_support_artifact_verifier_dir"
            ] = str(
                source_theorem_promotion_post_executor_bridge_manifest[
                    "artifact_verifier_dir"
                ]
            )
        if source_theorem_promotion_post_executor_bridge_manifest.get(
            "source_theorem_formal_environment_work_order_manifest"
        ):
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_from_post_executor_semantic_support_formal_environment_work_order_manifest"
            ] = str(
                source_theorem_promotion_post_executor_bridge_manifest[
                    "source_theorem_formal_environment_work_order_manifest"
                ]
            )
            manifest["artifacts"][
                "runtime_source_theorem_promotion_proofengineer_from_post_executor_semantic_support_formal_environment_work_orders_jsonl"
            ] = str(
                source_theorem_promotion_post_executor_bridge_manifest[
                    "source_theorem_formal_environment_work_orders_jsonl"
                ]
            )
    manifest["artifacts"]["runtime_formalization_gap_planner_bridges_jsonl"] = str(
        gap_planner_bridges_path
    )
    manifest["artifacts"]["runtime_formalization_gap_planner_seed_dir"] = str(
        gap_planner_seed_dir
    )
    manifest["artifacts"]["runtime_formalization_gap_planner_target_intake_dir"] = str(
        gap_planner_target_intake_dir
    )
    manifest["artifacts"]["runtime_formalization_gap_planner_handoffs_jsonl"] = str(
        gap_planner_handoffs_path
    )
    manifest["n_runtime_next_action_items"] = len(agenda_rows)
    manifest["n_runtime_learning_rows"] = len(learning_rows)
    manifest["n_runtime_theorem_reduction_closure_work_orders"] = len(
        theorem_reduction_closure_work_order_rows
    )
    manifest["n_runtime_source_theorem_semantic_primitive_work_orders"] = len(
        source_theorem_semantic_primitive_work_order_rows
    )
    manifest[
        "n_runtime_source_theorem_semantic_primitive_work_orders_from_proof_body_executor"
    ] = len(source_theorem_semantic_primitive_executor_work_order_rows)
    manifest[
        "n_runtime_new_source_theorem_semantic_primitive_work_orders_from_proof_body_executor"
    ] = len(new_semantic_work_order_rows)
    manifest[
        "n_runtime_source_theorem_semantic_primitive_learning_rows_from_proof_body_executor_bridge"
    ] = len(source_semantic_post_executor_bridge_learning_rows)
    manifest["n_runtime_source_theorem_formal_environment_work_orders"] = len(
        source_theorem_formal_environment_work_order_rows
    )
    manifest[
        "n_runtime_source_theorem_formal_environment_work_orders_from_proof_body_executor"
    ] = len(source_theorem_formal_environment_executor_work_order_rows)
    manifest["n_runtime_source_theorem_promotion_work_orders"] = len(
        source_theorem_promotion_work_order_rows
    )
    manifest[
        "n_runtime_source_theorem_promotion_work_orders_from_source_semantic_support"
    ] = len(source_theorem_promotion_source_semantic_work_order_rows)
    manifest[
        "n_runtime_new_source_theorem_promotion_work_orders_from_source_semantic_support"
    ] = len(new_source_theorem_promotion_source_semantic_work_order_rows)
    manifest[
        "n_runtime_source_theorem_promotion_work_orders_from_post_executor_semantic_support"
    ] = len(source_theorem_promotion_post_executor_work_order_rows)
    manifest[
        "n_runtime_new_source_theorem_promotion_work_orders_from_post_executor_semantic_support"
    ] = len(new_source_theorem_promotion_post_executor_work_order_rows)
    manifest["n_runtime_source_theorem_promotion_handoffs"] = len(
        source_theorem_promotion_handoff_rows
    )
    manifest[
        "n_runtime_source_theorem_promotion_handoffs_from_source_semantic_support"
    ] = len(source_theorem_promotion_source_semantic_handoff_rows)
    manifest[
        "n_runtime_source_theorem_promotion_handoffs_from_post_executor_semantic_support"
    ] = len(source_theorem_promotion_post_executor_handoff_rows)
    manifest["n_runtime_source_theorem_promotion_materialization_seeds"] = len(
        source_theorem_promotion_materialization_seed_rows
    )
    manifest[
        "n_runtime_source_theorem_promotion_materialization_seeds_from_source_semantic_support"
    ] = len(source_theorem_promotion_source_semantic_materialization_seed_rows)
    manifest[
        "n_runtime_source_theorem_promotion_materialization_seeds_from_post_executor_semantic_support"
    ] = len(source_theorem_promotion_post_executor_materialization_seed_rows)
    manifest["theorem_closure_proofengineer_bridge_requested"] = bool(
        config.theorem_closure_proofengineer_bridge
    )
    manifest["theorem_closure_proofengineer_bridge_ran"] = (
        theorem_closure_bridge_manifest is not None
    )
    manifest["theorem_closure_proofengineer_bridge_skipped_reason"] = (
        ""
        if theorem_closure_bridge_manifest is not None
        else (
            "bridge_disabled"
            if not config.theorem_closure_proofengineer_bridge
            else "no_theorem_reduction_closure_work_orders"
        )
    )
    manifest["theorem_closure_proofengineer_bridge_runtime_learning_ready"] = bool(
        theorem_closure_bridge_manifest
        and theorem_closure_bridge_manifest.get("runtime_learning_ready") is True
    )
    manifest["theorem_closure_proofengineer_bridge_n_kernel_verified"] = int(
        theorem_closure_bridge_manifest.get("n_kernel_verified", 0)
        if theorem_closure_bridge_manifest
        else 0
    )
    manifest["theorem_closure_proofengineer_bridge_proof_evidence_status"] = str(
        theorem_closure_bridge_manifest.get("proof_evidence_status", "")
        if theorem_closure_bridge_manifest
        else ""
    )
    manifest["theorem_closure_proofengineer_bridge_boundary"] = (
        "The runtime theorem-closure ProofEngineer bridge consumes emitted "
        "work orders after the current runtime loop and exports separate "
        "runtime-learning rows for a later run. It does not retroactively "
        "prove the current run, and it is proof evidence only for closure "
        "rows whose referenced audit manifest has kernel_verified=true."
    )
    manifest["source_semantic_proofengineer_bridge_requested"] = bool(
        config.source_semantic_proofengineer_bridge
    )
    manifest["source_semantic_proofengineer_bridge_ran"] = (
        source_semantic_bridge_manifest is not None
    )
    manifest["source_semantic_proofengineer_bridge_skipped_reason"] = (
        ""
        if source_semantic_bridge_manifest is not None
        else (
            "bridge_disabled"
            if not config.source_semantic_proofengineer_bridge
            else "no_source_theorem_semantic_primitive_work_orders"
        )
    )
    manifest["source_semantic_proofengineer_bridge_runtime_learning_ready"] = bool(
        source_semantic_bridge_manifest
        and source_semantic_bridge_manifest.get("runtime_learning_ready") is True
    )
    manifest["source_semantic_proofengineer_bridge_n_kernel_verified_registered_candidates"] = int(
        source_semantic_bridge_manifest.get(
            "n_kernel_verified_registered_candidate_obligations",
            0,
        )
        if source_semantic_bridge_manifest
        else 0
    )
    manifest["source_semantic_proofengineer_bridge_proof_evidence_status"] = str(
        source_semantic_bridge_manifest.get("proof_evidence_status", "")
        if source_semantic_bridge_manifest
        else ""
    )
    manifest["source_semantic_proofengineer_bridge_boundary"] = (
        "The runtime source-semantic ProofEngineer bridge consumes upstream "
        "semantic primitive work orders after the current runtime loop and may "
        "export separate runtime-learning rows for a later run. It does not "
        "retroactively prove the current run, and verified registered semantic "
        "bridges do not by themselves prove the full source theorem or any "
        "unformalized upstream statistical definition."
    )
    manifest["source_semantic_post_executor_proofengineer_bridge_requested"] = bool(
        config.source_semantic_proofengineer_bridge
        and source_theorem_semantic_primitive_executor_work_order_rows
    )
    manifest["source_semantic_post_executor_proofengineer_bridge_ran"] = (
        source_semantic_post_executor_bridge_manifest is not None
    )
    manifest[
        "source_semantic_post_executor_proofengineer_bridge_skipped_reason"
    ] = (
        ""
        if source_semantic_post_executor_bridge_manifest is not None
        else (
            "bridge_disabled"
            if not config.source_semantic_proofengineer_bridge
            else "no_new_executor_derived_source_theorem_semantic_primitive_work_orders"
            if source_theorem_semantic_primitive_executor_work_order_rows
            else "no_executor_derived_source_theorem_semantic_primitive_work_orders"
        )
    )
    manifest[
        "source_semantic_post_executor_proofengineer_bridge_runtime_learning_ready"
    ] = bool(
        source_semantic_post_executor_bridge_manifest
        and source_semantic_post_executor_bridge_manifest.get(
            "runtime_learning_ready"
        )
        is True
    )
    manifest[
        "source_semantic_post_executor_proofengineer_bridge_n_kernel_verified_registered_candidates"
    ] = int(
        source_semantic_post_executor_bridge_manifest.get(
            "n_kernel_verified_registered_candidate_obligations",
            0,
        )
        if source_semantic_post_executor_bridge_manifest
        else 0
    )
    manifest[
        "source_semantic_post_executor_proofengineer_bridge_proof_evidence_status"
    ] = str(
        source_semantic_post_executor_bridge_manifest.get("proof_evidence_status", "")
        if source_semantic_post_executor_bridge_manifest
        else ""
    )
    manifest["source_semantic_post_executor_proofengineer_bridge_boundary"] = (
        "This second source-semantic bridge pass only consumes semantic primitive "
        "work orders derived from exact proof-body executor feedback. It may export "
        "kernel-verified registered support rows into runtime learning memory, but "
        "does not prove the full source theorem or the placeholder primitive's full "
        "statistical semantics."
    )
    manifest["source_theorem_formal_environment_proofengineer_bridge_requested"] = bool(
        config.source_theorem_formal_environment_proofengineer_bridge
    )
    manifest["source_theorem_formal_environment_proofengineer_bridge_ran"] = (
        source_theorem_formal_environment_bridge_manifest is not None
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_bridge_skipped_reason"
    ] = (
        ""
        if source_theorem_formal_environment_bridge_manifest is not None
        else (
            "bridge_disabled"
            if not config.source_theorem_formal_environment_proofengineer_bridge
            else "no_source_theorem_formal_environment_work_orders"
        )
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_bridge_n_repair_packets"
    ] = int(
        source_theorem_formal_environment_bridge_manifest.get("n_repair_packets", 0)
        if source_theorem_formal_environment_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_bridge_n_missing_formal_symbols"
    ] = int(
        source_theorem_formal_environment_bridge_manifest.get(
            "n_missing_formal_symbols",
            0,
        )
        if source_theorem_formal_environment_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_bridge_n_typeclass_blockers"
    ] = int(
        source_theorem_formal_environment_bridge_manifest.get(
            "n_typeclass_blockers",
            0,
        )
        if source_theorem_formal_environment_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_bridge_n_learning_rows"
    ] = len(source_theorem_formal_environment_bridge_learning_rows)
    manifest[
        "source_theorem_formal_environment_proofengineer_signature_probes_requested"
    ] = bool(config.source_theorem_formal_environment_proofengineer_signature_probes)
    manifest[
        "source_theorem_formal_environment_proofengineer_n_signature_probe_rows"
    ] = int(
        source_theorem_formal_environment_bridge_manifest.get(
            "n_signature_probe_rows",
            0,
        )
        if source_theorem_formal_environment_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_n_signature_probes_reached_proof_body"
    ] = int(
        source_theorem_formal_environment_bridge_manifest.get(
            "n_signature_probes_reached_proof_body",
            0,
        )
        if source_theorem_formal_environment_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_signature_probe_proof_evidence_status"
    ] = str(
        source_theorem_formal_environment_bridge_manifest.get(
            "signature_probe_proof_evidence_status",
            "",
        )
        if source_theorem_formal_environment_bridge_manifest
        else ""
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_n_proof_body_work_orders"
    ] = int(
        source_theorem_formal_environment_bridge_manifest.get(
            "n_proof_body_work_orders",
            0,
        )
        if source_theorem_formal_environment_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_proof_body_work_order_proof_evidence_status"
    ] = str(
        source_theorem_formal_environment_bridge_manifest.get(
            "proof_body_work_order_proof_evidence_status",
            "",
        )
        if source_theorem_formal_environment_bridge_manifest
        else ""
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_n_proof_body_execution_queue_rows"
    ] = int(
        source_theorem_formal_environment_bridge_manifest.get(
            "n_proof_body_execution_queue_rows",
            0,
        )
        if source_theorem_formal_environment_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_n_proof_body_execution_live_goal_requests"
    ] = int(
        source_theorem_formal_environment_bridge_manifest.get(
            "n_proof_body_execution_live_goal_requests",
            0,
        )
        if source_theorem_formal_environment_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_proof_body_execution_queue_proof_evidence_status"
    ] = str(
        source_theorem_formal_environment_bridge_manifest.get(
            "proof_body_execution_queue_proof_evidence_status",
            "",
        )
        if source_theorem_formal_environment_bridge_manifest
        else ""
    )
    manifest[
        "source_theorem_formal_environment_proofengineer_bridge_proof_evidence_status"
    ] = str(
        source_theorem_formal_environment_bridge_manifest.get(
            "proof_evidence_status",
            "",
        )
        if source_theorem_formal_environment_bridge_manifest
        else ""
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_requested"
    ] = bool(config.source_theorem_formal_environment_proofengineer_execute_proof_body)
    manifest["source_theorem_formal_environment_proof_body_executor_ran"] = (
        source_theorem_formal_environment_proof_body_executor_manifest is not None
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_local_lean_requested"
    ] = bool(config.source_theorem_formal_environment_proofengineer_proof_body_local_lean)
    manifest[
        "source_theorem_formal_environment_proof_body_executor_skipped_reason"
    ] = (
        ""
        if source_theorem_formal_environment_proof_body_executor_manifest is not None
        else (
            "executor_disabled"
            if not config.source_theorem_formal_environment_proofengineer_execute_proof_body
            else "no_proof_body_execution_queue"
        )
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_n_result_rows"
    ] = int(
        source_theorem_formal_environment_proof_body_executor_manifest.get(
            "n_execution_result_rows",
            0,
        )
        if source_theorem_formal_environment_proof_body_executor_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_n_local_lean_checked"
    ] = int(
        source_theorem_formal_environment_proof_body_executor_manifest.get(
            "n_local_lean_checked",
            0,
        )
        if source_theorem_formal_environment_proof_body_executor_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_n_artifact_kernel_verified"
    ] = int(
        source_theorem_formal_environment_proof_body_executor_manifest.get(
            "n_artifact_kernel_verified",
            0,
        )
        if source_theorem_formal_environment_proof_body_executor_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified"
    ] = int(
        source_theorem_formal_environment_proof_body_executor_manifest.get(
            "n_source_theorem_kernel_verified",
            0,
        )
        if source_theorem_formal_environment_proof_body_executor_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_n_placeholder_environment_blockers"
    ] = int(
        source_theorem_formal_environment_proof_body_executor_manifest.get(
            "n_placeholder_environment_blockers",
            0,
        )
        if source_theorem_formal_environment_proof_body_executor_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_n_learning_rows"
    ] = len(source_theorem_formal_environment_proof_body_executor_learning_rows)
    manifest[
        "source_theorem_formal_environment_proof_body_executor_proof_evidence_status"
    ] = str(
        source_theorem_formal_environment_proof_body_executor_manifest.get(
            "proof_evidence_status",
            "",
        )
        if source_theorem_formal_environment_proof_body_executor_manifest
        else ""
    )
    manifest[
        "source_theorem_formal_environment_from_source_semantic_promotion_bridge_requested"
    ] = bool(
        config.source_theorem_formal_environment_proofengineer_bridge
        and source_theorem_promotion_source_semantic_bridge_manifest is not None
        and source_theorem_promotion_source_semantic_bridge_manifest.get(
            "source_theorem_formal_environment_work_orders_jsonl"
        )
    )
    manifest[
        "source_theorem_formal_environment_from_source_semantic_promotion_bridge_ran"
    ] = (
        source_theorem_formal_environment_source_semantic_bridge_manifest is not None
    )
    manifest[
        "source_theorem_formal_environment_from_source_semantic_promotion_bridge_skipped_reason"
    ] = (
        ""
        if source_theorem_formal_environment_source_semantic_bridge_manifest is not None
        else (
            "bridge_disabled"
            if not config.source_theorem_formal_environment_proofengineer_bridge
            else "no_source_semantic_promotion_bridge"
            if source_theorem_promotion_source_semantic_bridge_manifest is None
            else "no_source_semantic_promotion_formal_environment_work_orders"
        )
    )
    manifest[
        "source_theorem_formal_environment_from_source_semantic_promotion_bridge_n_repair_packets"
    ] = int(
        source_theorem_formal_environment_source_semantic_bridge_manifest.get(
            "n_repair_packets",
            0,
        )
        if source_theorem_formal_environment_source_semantic_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_from_source_semantic_promotion_bridge_n_learning_rows"
    ] = len(source_theorem_formal_environment_source_semantic_bridge_learning_rows)
    manifest[
        "source_theorem_formal_environment_from_source_semantic_promotion_bridge_n_proof_body_work_orders"
    ] = int(
        source_theorem_formal_environment_source_semantic_bridge_manifest.get(
            "n_proof_body_work_orders",
            0,
        )
        if source_theorem_formal_environment_source_semantic_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_from_source_semantic_promotion_bridge_n_proof_body_execution_queue_rows"
    ] = int(
        source_theorem_formal_environment_source_semantic_bridge_manifest.get(
            "n_proof_body_execution_queue_rows",
            0,
        )
        if source_theorem_formal_environment_source_semantic_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_from_source_semantic_promotion_bridge_proof_evidence_status"
    ] = str(
        source_theorem_formal_environment_source_semantic_bridge_manifest.get(
            "proof_evidence_status",
            "",
        )
        if source_theorem_formal_environment_source_semantic_bridge_manifest
        else ""
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_requested"
    ] = bool(
        config.source_theorem_formal_environment_proofengineer_execute_proof_body
        and source_theorem_formal_environment_source_semantic_bridge_manifest is not None
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_ran"
    ] = (
        source_theorem_formal_environment_source_semantic_proof_body_executor_manifest
        is not None
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_n_result_rows"
    ] = int(
        source_theorem_formal_environment_source_semantic_proof_body_executor_manifest.get(
            "n_execution_result_rows",
            0,
        )
        if source_theorem_formal_environment_source_semantic_proof_body_executor_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_n_source_theorem_kernel_verified"
    ] = int(
        source_theorem_formal_environment_source_semantic_proof_body_executor_manifest.get(
            "n_source_theorem_kernel_verified",
            0,
        )
        if source_theorem_formal_environment_source_semantic_proof_body_executor_manifest
        else 0
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_n_learning_rows"
    ] = len(
        source_theorem_formal_environment_source_semantic_proof_body_executor_learning_rows
    )
    manifest[
        "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_proof_evidence_status"
    ] = str(
        source_theorem_formal_environment_source_semantic_proof_body_executor_manifest.get(
            "proof_evidence_status",
            "",
        )
        if source_theorem_formal_environment_source_semantic_proof_body_executor_manifest
        else ""
    )
    manifest["source_theorem_formal_environment_proofengineer_bridge_boundary"] = (
        "The runtime source-theorem formal-environment ProofEngineer bridge "
        "consumes exact-source environment work orders and exports repair "
        "packets/runtime-learning rows for a later run. It does not prove the "
        "current run; proof evidence requires a later local Lean/AXLE verifier "
        "manifest with artifact/source theorem kernel verification."
    )
    manifest["source_theorem_promotion_proofengineer_bridge_requested"] = bool(
        config.source_theorem_promotion_proofengineer_bridge
    )
    manifest["source_theorem_promotion_proofengineer_bridge_ran"] = (
        source_theorem_promotion_bridge_manifest is not None
    )
    manifest["source_theorem_promotion_proofengineer_bridge_skipped_reason"] = (
        ""
        if source_theorem_promotion_bridge_manifest is not None
        else (
            "bridge_disabled"
            if not config.source_theorem_promotion_proofengineer_bridge
            else "no_source_theorem_promotion_materialization_seeds"
        )
    )
    manifest[
        "source_theorem_promotion_proofengineer_bridge_local_lean_requested"
    ] = bool(config.source_theorem_promotion_proofengineer_local_lean)
    manifest[
        "source_theorem_promotion_proofengineer_bridge_overwrite_artifacts_requested"
    ] = bool(config.source_theorem_promotion_proofengineer_overwrite_artifacts)
    manifest[
        "source_theorem_promotion_proofengineer_bridge_n_materialized_artifacts"
    ] = int(
        source_theorem_promotion_bridge_manifest.get("n_materialized_artifacts", 0)
        if source_theorem_promotion_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_proofengineer_bridge_n_artifact_kernel_verified"
    ] = int(
        source_theorem_promotion_bridge_manifest.get("n_artifact_kernel_verified", 0)
        if source_theorem_promotion_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_proofengineer_bridge_n_formal_environment_work_orders"
    ] = int(
        source_theorem_promotion_bridge_manifest.get(
            "n_source_theorem_formal_environment_work_orders",
            0,
        )
        if source_theorem_promotion_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_proofengineer_bridge_n_ready_for_source_theorem_integration"
    ] = int(
        source_theorem_promotion_bridge_manifest.get(
            "n_ready_for_source_theorem_integration",
            0,
        )
        if source_theorem_promotion_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_proofengineer_bridge_n_source_theorem_kernel_verified"
    ] = int(
        source_theorem_promotion_bridge_manifest.get(
            "n_source_theorem_kernel_verified",
            0,
        )
        if source_theorem_promotion_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_proofengineer_bridge_n_source_theorem_integration_rows"
    ] = int(
        source_theorem_promotion_bridge_manifest.get(
            "n_source_theorem_integration_rows",
            0,
        )
        if source_theorem_promotion_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_proofengineer_bridge_n_source_theorem_integration_blocked_route_probe"
    ] = int(
        source_theorem_promotion_bridge_manifest.get(
            "n_source_theorem_integration_blocked_route_probe",
            0,
        )
        if source_theorem_promotion_bridge_manifest
        else 0
    )
    manifest["source_theorem_promotion_proofengineer_bridge_proof_evidence_status"] = str(
        source_theorem_promotion_bridge_manifest.get("proof_evidence_status", "")
        if source_theorem_promotion_bridge_manifest
        else ""
    )
    manifest["source_theorem_promotion_proofengineer_bridge_boundary"] = (
        "The runtime source-theorem promotion ProofEngineer bridge consumes "
        "materialization seeds after the current runtime loop. Materialized "
        "route probes and artifact-kernel checks are not source theorem proof; "
        "source theorem proof requires source_theorem_kernel_verified=true for "
        "the exact source target."
    )
    manifest["source_theorem_promotion_proofengineer_bridge_n_learning_rows"] = len(
        source_theorem_promotion_bridge_learning_rows
    )
    manifest[
        "source_theorem_promotion_source_semantic_proofengineer_bridge_requested"
    ] = bool(
        config.source_theorem_promotion_proofengineer_bridge
        and source_theorem_promotion_source_semantic_materialization_seed_rows
    )
    manifest[
        "source_theorem_promotion_source_semantic_proofengineer_bridge_ran"
    ] = source_theorem_promotion_source_semantic_bridge_manifest is not None
    manifest[
        "source_theorem_promotion_source_semantic_proofengineer_bridge_skipped_reason"
    ] = (
        ""
        if source_theorem_promotion_source_semantic_bridge_manifest is not None
        else (
            "bridge_disabled"
            if not config.source_theorem_promotion_proofengineer_bridge
            else "no_new_source_semantic_source_theorem_promotion_materialization_seeds"
            if source_theorem_promotion_source_semantic_work_order_rows
            else "no_source_semantic_source_theorem_promotion_work_orders"
        )
    )
    manifest[
        "source_theorem_promotion_source_semantic_proofengineer_bridge_n_materialized_artifacts"
    ] = int(
        source_theorem_promotion_source_semantic_bridge_manifest.get(
            "n_materialized_artifacts",
            0,
        )
        if source_theorem_promotion_source_semantic_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_source_semantic_proofengineer_bridge_n_artifact_kernel_verified"
    ] = int(
        source_theorem_promotion_source_semantic_bridge_manifest.get(
            "n_artifact_kernel_verified",
            0,
        )
        if source_theorem_promotion_source_semantic_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_source_semantic_proofengineer_bridge_n_source_theorem_kernel_verified"
    ] = int(
        source_theorem_promotion_source_semantic_bridge_manifest.get(
            "n_source_theorem_kernel_verified",
            0,
        )
        if source_theorem_promotion_source_semantic_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_source_semantic_proofengineer_bridge_n_formal_environment_work_orders"
    ] = int(
        source_theorem_promotion_source_semantic_bridge_manifest.get(
            "n_source_theorem_formal_environment_work_orders",
            0,
        )
        if source_theorem_promotion_source_semantic_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_source_semantic_proofengineer_bridge_proof_evidence_status"
    ] = str(
        source_theorem_promotion_source_semantic_bridge_manifest.get(
            "proof_evidence_status",
            "",
        )
        if source_theorem_promotion_source_semantic_bridge_manifest
        else ""
    )
    manifest[
        "source_theorem_promotion_source_semantic_proofengineer_bridge_n_learning_rows"
    ] = len(source_theorem_promotion_source_semantic_bridge_learning_rows)
    manifest["source_theorem_promotion_source_semantic_proofengineer_bridge_boundary"] = (
        "This bridge pass is triggered only after the source-semantic ProofEngineer "
        "bridge has exported same-run kernel-verified registered support rows. It "
        "materializes or checks source-theorem promotion candidates, but it is not "
        "full source theorem proof unless a downstream verifier row reports "
        "source_theorem_kernel_verified=true for the exact source target."
    )
    manifest[
        "source_theorem_promotion_post_executor_proofengineer_bridge_requested"
    ] = bool(
        config.source_theorem_promotion_proofengineer_bridge
        and source_theorem_promotion_post_executor_materialization_seed_rows
    )
    manifest[
        "source_theorem_promotion_post_executor_proofengineer_bridge_ran"
    ] = source_theorem_promotion_post_executor_bridge_manifest is not None
    manifest[
        "source_theorem_promotion_post_executor_proofengineer_bridge_skipped_reason"
    ] = (
        ""
        if source_theorem_promotion_post_executor_bridge_manifest is not None
        else (
            "bridge_disabled"
            if not config.source_theorem_promotion_proofengineer_bridge
            else "no_new_post_executor_source_theorem_promotion_materialization_seeds"
            if source_theorem_promotion_post_executor_work_order_rows
            else "no_post_executor_source_theorem_promotion_work_orders"
        )
    )
    manifest[
        "source_theorem_promotion_post_executor_proofengineer_bridge_n_materialized_artifacts"
    ] = int(
        source_theorem_promotion_post_executor_bridge_manifest.get(
            "n_materialized_artifacts",
            0,
        )
        if source_theorem_promotion_post_executor_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_post_executor_proofengineer_bridge_n_artifact_kernel_verified"
    ] = int(
        source_theorem_promotion_post_executor_bridge_manifest.get(
            "n_artifact_kernel_verified",
            0,
        )
        if source_theorem_promotion_post_executor_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_post_executor_proofengineer_bridge_n_source_theorem_kernel_verified"
    ] = int(
        source_theorem_promotion_post_executor_bridge_manifest.get(
            "n_source_theorem_kernel_verified",
            0,
        )
        if source_theorem_promotion_post_executor_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_post_executor_proofengineer_bridge_n_formal_environment_work_orders"
    ] = int(
        source_theorem_promotion_post_executor_bridge_manifest.get(
            "n_source_theorem_formal_environment_work_orders",
            0,
        )
        if source_theorem_promotion_post_executor_bridge_manifest
        else 0
    )
    manifest[
        "source_theorem_promotion_post_executor_proofengineer_bridge_proof_evidence_status"
    ] = str(
        source_theorem_promotion_post_executor_bridge_manifest.get(
            "proof_evidence_status",
            "",
        )
        if source_theorem_promotion_post_executor_bridge_manifest
        else ""
    )
    manifest[
        "source_theorem_promotion_post_executor_proofengineer_bridge_n_learning_rows"
    ] = len(source_theorem_promotion_post_executor_bridge_learning_rows)
    manifest["source_theorem_promotion_post_executor_proofengineer_bridge_boundary"] = (
        "This bridge pass is triggered only after same-run exact proof-body "
        "executor feedback has produced source-semantic primitive work orders "
        "and the source-semantic ProofEngineer bridge has exported kernel-verified "
        "registered support rows. It materializes or checks promotion candidates, "
        "but it is not full source theorem proof unless a downstream verifier row "
        "reports source_theorem_kernel_verified=true for the exact source target."
    )
    manifest["n_runtime_formalization_gap_planner_bridges"] = len(
        gap_planner_bridge_rows
    )
    manifest["n_runtime_formalization_gap_planner_routes"] = sum(
        int(row.get("counts", {}).get("routes", 0) or 0)
        for row in gap_planner_bridge_rows
    )
    manifest["n_runtime_formalization_gap_planner_handoffs"] = len(
        gap_planner_handoff_rows
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _runtime_llm_topology(
    *,
    architect_coordinator: LLMArchitectCoordinatorAgent | None,
    theory_developer: LLMTheoryDeveloperAgent,
    simulation_engineer: LLMSimulationEngineerAgent | None,
    algorithm_engineer: LLMAlgorithmEngineerAgent | None,
    formalizer: LLMFormalizerProofEngineerAgent | None,
    critic_evaluator: LLMCriticEvaluatorAgent | None,
    proof_state_provider: ProofStateFeedbackProvider | None,
) -> dict[str, Any]:
    agents = [
        _llm_agent_topology_row(
            "ArchitectCoordinator",
            architect_coordinator,
            model_tier="sonnet",
            role="top-level research plan, evidence gates, and subsystem routing",
        ),
        _llm_agent_topology_row(
            "TheoryDeveloper",
            theory_developer,
            model_tier="sonnet",
            role="deductive statistical theory discovery and theorem/procedure proposal",
        ),
        _llm_agent_topology_row(
            "SimulationEngineer",
            simulation_engineer,
            model_tier="haiku",
            role="simulation and falsifier proposal under runtime execution gates",
        ),
        _llm_agent_topology_row(
            "AlgorithmEngineer",
            algorithm_engineer,
            model_tier="haiku",
            role="algorithm prototype and stress-test implementation proposal",
        ),
        _llm_agent_topology_row(
            "FormalizerProofEngineer",
            formalizer,
            model_tier="sonnet",
            role="Lean/formal-target/proof-search proposal before kernel gates",
        ),
        _llm_agent_topology_row(
            "CriticEvaluator",
            critic_evaluator,
            model_tier="haiku",
            role="boundary audit, learning rows, and next-action triage",
        ),
    ]
    enabled = [row for row in agents if row["enabled"]]
    by_tier: dict[str, int] = {}
    by_provider: dict[str, int] = {}
    for row in enabled:
        tier = str(row.get("model_tier", ""))
        provider = str(row.get("provider_name", ""))
        by_tier[tier] = by_tier.get(tier, 0) + 1
        by_provider[provider] = by_provider.get(provider, 0) + 1
    resolved_claude_models_by_tier = _resolved_claude_models_by_tier()
    resolved_claude_model_tier_policy_violations = (
        claude_model_tier_policy_violations(resolved_claude_models_by_tier)
    )
    resolved_claude_model_freshness_warnings = (
        claude_model_freshness_warnings(resolved_claude_models_by_tier)
    )
    violations = _llm_topology_policy_violations(agents) + [
        "resolved Claude model tier policy violation: " + violation
        for violation in resolved_claude_model_tier_policy_violations
    ]
    manifest = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeLLMTopologyManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "default_live_provider": "anthropic",
            "supported_generator_providers": list(SUPPORTED_LIVE_GENERATOR_PROVIDERS),
            "claude_model_selection": ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
            "resolved_claude_models_by_tier": resolved_claude_models_by_tier,
            "resolved_claude_model_tier_policy_status": (
                "OK"
                if not resolved_claude_model_tier_policy_violations
                else "POLICY_VIOLATION"
            ),
            "resolved_claude_model_tier_policy_violations": (
                resolved_claude_model_tier_policy_violations
            ),
            "resolved_claude_model_freshness_status": (
                "CURRENT"
                if not resolved_claude_model_freshness_warnings
                else "NON_CURRENT"
            ),
            "resolved_claude_model_freshness_warnings": (
                resolved_claude_model_freshness_warnings
            ),
            "primary_cost_split": "sonnet_for_architect_theory_formalizer__haiku_for_simulation_algorithm_critic",
            "backend_boundary": (
                "LLM backends generate structured proposals only. AgentRuntime owns "
                "tool use, filesystem changes, execution, tests, Lean checks, and evidence promotion."
            ),
        },
        "llm_agents": agents,
        "policy_status": "OK" if not violations else "POLICY_VIOLATION",
        "policy_violations": violations,
        "non_llm_runtime_providers": {
            "proof_state_provider": getattr(proof_state_provider, "name", "") if proof_state_provider else "",
            "proof_state_feedback_is_proof_evidence": False,
        },
        "counts": {
            "llm_agents_total": len(agents),
            "llm_agents_enabled": len(enabled),
            "llm_agents_disabled": len(agents) - len(enabled),
            "enabled_by_model_tier": dict(sorted(by_tier.items())),
            "enabled_by_provider": dict(sorted(by_provider.items())),
            "unsupported_generator_backends_enabled": sum(
                1 for row in enabled if _has_unsupported_generator_provider(row)
            ),
            "anthropic_model_tier_mismatches": sum(
                1 for row in enabled if _anthropic_model_tier_mismatch(row)
            ),
            "resolved_claude_model_tier_policy_violations": len(
                resolved_claude_model_tier_policy_violations
            ),
        },
        "boundary": (
            "This manifest is runtime/model provenance and cost-control metadata. "
            "It is not proof, simulation, or implementation evidence."
        ),
    }
    manifest["manifest_id"] = "runtime_llm_topology:" + stable_hash(
        [
            manifest["policy"],
            manifest["llm_agents"],
            manifest["non_llm_runtime_providers"],
        ]
    )[:20]
    return manifest


def _resolved_claude_models_by_tier() -> dict[str, str]:
    return {
        tier: resolve_generator_model(
            provider_name="anthropic",
            requested_model="",
            model_tier=tier,
        )
        for tier in CLAUDE_MODEL_TIERS
    }


def _llm_topology_policy_violations(agents: list[dict[str, Any]]) -> list[str]:
    violations: list[str] = []
    for row in agents:
        if not row.get("enabled"):
            continue
        unsupported = _unsupported_generator_providers(row)
        if unsupported:
            violations.append(
                f"{row.get('subsystem')} uses unsupported generator provider(s): "
                + ", ".join(sorted(unsupported))
            )
        mismatch = _anthropic_model_tier_mismatch(row)
        if mismatch:
            violations.append(mismatch)
    return violations


def _has_unsupported_generator_provider(row: Mapping[str, Any]) -> bool:
    return bool(_unsupported_generator_providers(row))


def _unsupported_generator_providers(row: Mapping[str, Any]) -> set[str]:
    allowed = set(SUPPORTED_LIVE_GENERATOR_PROVIDERS)
    providers = {
        str(row.get("provider_name", "") or "").strip().lower(),
        str(row.get("backend_provider_name", "") or "").strip().lower(),
    }
    providers.discard("")
    return {provider for provider in providers if provider not in allowed}


def _anthropic_model_tier_mismatch(row: Mapping[str, Any]) -> str:
    providers = {
        str(row.get("provider_name", "") or "").strip().lower(),
        str(row.get("backend_provider_name", "") or "").strip().lower(),
    }
    if "anthropic" not in providers:
        return ""
    return claude_model_tier_mismatch(
        str(row.get("model", "") or "").strip(),
        str(row.get("model_tier", "") or "").strip().lower(),
        subject=str(row.get("subsystem", "") or "").strip(),
    )


def _llm_agent_topology_row(
    subsystem: str,
    agent: Any | None,
    *,
    model_tier: str,
    role: str,
) -> dict[str, Any]:
    if agent is None:
        return {
            "subsystem": subsystem,
            "enabled": False,
            "provider_name": "",
            "backend_provider_name": "",
            "model": "",
            "model_tier": model_tier,
            "role": role,
            "generator_only": True,
            "acts_in_environment": False,
        }
    config = getattr(agent, "config", None)
    provider = getattr(agent, "provider", None)
    provider_name = str(getattr(config, "provider_name", "") or getattr(provider, "provider_name", "") or "")
    config_model_tier = str(getattr(config, "model_tier", "") or model_tier)
    requested_model = str(getattr(config, "model", "") or "")
    resolved_model = resolve_generator_model(
        provider_name=provider_name,
        requested_model=requested_model,
        model_tier=config_model_tier,
    )
    return {
        "subsystem": subsystem,
        "enabled": True,
        "provider_name": provider_name,
        "backend_provider_name": str(getattr(provider, "provider_name", provider_name) or ""),
        "model": resolved_model,
        "configured_model": requested_model,
        "model_tier": config_model_tier,
        "role": role,
        "generator_only": True,
        "acts_in_environment": False,
        "max_tokens": int(getattr(config, "max_tokens", 0) or 0),
        "temperature": float(getattr(config, "temperature", 0.0) or 0.0),
    }


def _implementation_gaps(packet: Any, procedures: list[CandidateProcedure]) -> list[dict[str, Any]]:
    if not isinstance(packet, Mapping):
        return []
    registered_ids = {row.id for row in procedures}
    registered_algorithms = {row.algorithm for row in procedures}
    gaps: list[dict[str, Any]] = []
    for row in packet.get("estimator_specs", []) or []:
        if not isinstance(row, Mapping):
            continue
        estimator_id = str(row.get("id") or row.get("name") or "").strip()
        if not estimator_id:
            continue
        if estimator_id in registered_ids or estimator_id in registered_algorithms:
            continue
        gaps.append(
            {
                "estimator_id": estimator_id,
                "status": "REQUIRES_ALGORITHM_ENGINEER_ADAPTER",
                "reason": "LLM estimator spec has no registered executable algorithm in this runtime slice.",
            }
        )
    return gaps


def _critic_repair_round(context: Mapping[str, Any]) -> int:
    loop = context.get("runtime_feedback_loop")
    if not isinstance(loop, Mapping):
        return 0
    try:
        return max(0, int(loop.get("critic_repair_round", 0) or 0))
    except (TypeError, ValueError):
        return 0


def _unique_runtime_artifact_id(
    blackboard: BlackboardState,
    artifact_id: str,
    *,
    task_id: str,
) -> str:
    if artifact_id not in blackboard.artifacts:
        return artifact_id
    return f"{artifact_id}:runtime_revision:{stable_hash(task_id)[:8]}"


def _effective_critic_repair_rounds(
    context: Mapping[str, Any],
    config: ResearchAgentRuntimeConfig,
) -> int:
    configured = max(0, int(config.max_critic_repair_rounds))
    policy = _architect_runtime_plan(context).get("iteration_policy", {})
    if not isinstance(policy, Mapping):
        return configured
    try:
        architect_max = int(policy.get("max_repair_rounds", configured) or configured)
    except (TypeError, ValueError):
        return configured
    return max(0, min(configured, architect_max))


def _critic_should_reroute_to_theory(
    *,
    agenda: list[dict[str, Any]],
    formalization_manifest: Mapping[str, Any],
    critic_round: int,
    max_critic_repair_rounds: int,
) -> bool:
    if critic_round >= max_critic_repair_rounds:
        return False
    formal_counts = formalization_manifest.get("counts", {}) if isinstance(formalization_manifest, Mapping) else {}
    if int(formal_counts.get("formal_gap", 0) or 0) > 0:
        return True
    if int(formal_counts.get("proof_state_route_revisions", 0) or 0) > 0:
        return True
    if int(formal_counts.get("kernel_verified", 0) or 0) == 0 and int(formal_counts.get("proved", 0) or 0) > 0:
        return True
    for row in agenda:
        agenda_id = str(row.get("id", ""))
        if agenda_id.startswith(("formal_gap:", "proof_feedback:", "simulation:theory_revision")):
            return True
    return False


def _critic_repair_feedback(
    *,
    question: OpenResearchQuestion,
    critic_round: int,
    max_critic_repair_rounds: int,
    retrieval_manifest: Mapping[str, Any],
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    algorithm_manifest: Mapping[str, Any],
    formalization_manifest: Mapping[str, Any],
    agenda: list[dict[str, Any]],
) -> dict[str, Any]:
    formal_counts = formalization_manifest.get("counts", {}) if isinstance(formalization_manifest, Mapping) else {}
    return {
        "feedback_source": "CriticEvaluator",
        "question_id": question.id,
        "critic_repair_round": critic_round,
        "next_critic_repair_round": critic_round + 1,
        "max_critic_repair_rounds": max_critic_repair_rounds,
        "theory_packet_id": str(theory_packet.get("packet_id", "")),
        "retrieval_memory_manifest_id": str(retrieval_manifest.get("manifest_id", "")),
        "simulation_manifest_id": str(simulation_manifest.get("manifest_id", "")),
        "algorithm_sandbox_manifest_id": str(algorithm_manifest.get("manifest_id", "")),
        "formalization_manifest_id": str(formalization_manifest.get("manifest_id", "")),
        "formalization_counts": dict(formal_counts) if isinstance(formal_counts, Mapping) else {},
        "high_priority_agenda": [
            _compact_agenda_item(row)
            for row in agenda
            if str(row.get("priority", "")).lower() == "high"
        ],
        "formal_subclaim_feedback": [
            _compact_formal_subclaim_feedback(row)
            for row in formalization_manifest.get("formal_subclaims", [])[:8]
            if isinstance(row, Mapping)
        ],
        "proof_state_feedback_manifest_id": str(
            formalization_manifest.get("proof_state_feedback_manifest_id", "")
        ),
        "required_revision": (
            "Revise theorem statements, assumptions, estimator specification, or proof plan "
            "to address formal gaps and non-kernel proof feedback. Do not claim proof evidence "
            "unless AXLE/local Lean kernel verification closes the intended claim."
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _compact_agenda_item(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id", "")),
        "owner_subsystem": str(row.get("owner_subsystem", "")),
        "trigger": str(row.get("trigger", "")),
        "action": str(row.get("action", "")),
        "acceptance_gate": str(row.get("acceptance_gate", "")),
        "priority": str(row.get("priority", "")),
    }


def _compact_formal_subclaim_feedback(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id", "")),
        "claim_type": str(row.get("claim_type", "")),
        "status": str(row.get("status", "")),
        "kernel_verified": bool(row.get("kernel_verified", False)),
        "gap_reason": str(row.get("gap_reason", "")),
        "errors": list(row.get("errors", []) or [])[:3],
        "proof_dependencies": list(row.get("proof_dependencies", []) or [])[:5],
    }


def _architect_runtime_plan(context: Mapping[str, Any]) -> dict[str, Any]:
    plan = context.get("architect_runtime_plan")
    return dict(plan) if isinstance(plan, Mapping) else {}


def _architect_subsystem_plan(context: Mapping[str, Any], subsystem: str) -> dict[str, Any]:
    plan = _architect_runtime_plan(context)
    for row in plan.get("subsystem_execution_plan", []) or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("subsystem", "")).strip() == subsystem:
            return dict(row)
    return {}


def _architect_acceptance_gate(
    context: Mapping[str, Any],
    subsystem: str,
    default: str,
) -> str:
    row = _architect_subsystem_plan(context, subsystem)
    gate = str(row.get("acceptance_gate", "")).strip()
    return gate or default


def _architect_expected_artifacts(
    context: Mapping[str, Any],
    subsystem: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    row = _architect_subsystem_plan(context, subsystem)
    artifacts = [
        str(item).strip()
        for item in row.get("expected_artifacts", []) or []
        if str(item).strip()
    ]
    return tuple(artifacts) if artifacts else default


def _architect_control_payload(context: Mapping[str, Any], subsystem: str) -> dict[str, Any]:
    plan = _architect_runtime_plan(context)
    row = _architect_subsystem_plan(context, subsystem)
    if not plan and not row:
        return {}
    evidence_gates = [
        dict(item)
        for item in plan.get("evidence_gates", []) or []
        if isinstance(item, Mapping)
    ]
    iteration_policy = plan.get("iteration_policy", {})
    retrieval_strategy = plan.get("retrieval_strategy", {})
    problem_analysis = plan.get("problem_analysis", {})
    knowledge_bank_plan = plan.get("stat_knowledge_bank_plan", {})
    fair_comparison_plan = plan.get("literature_fair_comparison_plan", [])
    return {
        "architect_coordinator_proposal_id": str(
            context.get("architect_coordinator_proposal_id", "")
        ),
        "subsystem": subsystem,
        "subsystem_plan": row,
        "acceptance_gate": str(row.get("acceptance_gate", "")).strip(),
        "expected_artifacts": [
            str(item).strip()
            for item in row.get("expected_artifacts", []) or []
            if str(item).strip()
        ],
        "evidence_gates": evidence_gates,
        "iteration_policy": dict(iteration_policy) if isinstance(iteration_policy, Mapping) else {},
        "retrieval_strategy": dict(retrieval_strategy) if isinstance(retrieval_strategy, Mapping) else {},
        "problem_analysis": dict(problem_analysis) if isinstance(problem_analysis, Mapping) else {},
        "stat_knowledge_bank_plan": dict(knowledge_bank_plan) if isinstance(knowledge_bank_plan, Mapping) else {},
        "literature_fair_comparison_plan": [
            dict(item) for item in fair_comparison_plan if isinstance(item, Mapping)
        ],
        "boundary": str(plan.get("boundary", "")),
    }


def _latest_artifact(blackboard: BlackboardState, prefix: str) -> dict[str, Any]:
    for key in reversed(list(blackboard.artifacts.keys())):
        if key.startswith(prefix) and isinstance(blackboard.artifacts[key], dict):
            return dict(blackboard.artifacts[key])
    return {}


def _algorithm_proposal_for_estimator(
    proposal_packet: Mapping[str, Any] | None,
    estimator_id: str,
) -> dict[str, Any]:
    if not isinstance(proposal_packet, Mapping):
        return {}
    for row in proposal_packet.get("implementation_targets", []) or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("estimator_id", "")) == estimator_id:
            return dict(row)
    return {}


def _algorithm_code_draft_for_estimator(
    proposal_packet: Mapping[str, Any] | None,
    estimator_id: str,
) -> dict[str, Any]:
    if not isinstance(proposal_packet, Mapping):
        return {}
    for row in proposal_packet.get("sandbox_code_drafts", []) or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("estimator_id", "")) == estimator_id:
            return dict(row)
    return {}


def _registered_algorithm_template_hint(
    *,
    proposal_target: Mapping[str, Any],
    spec: Mapping[str, Any],
    question: OpenResearchQuestion,
) -> str:
    explicit = str(proposal_target.get("registered_template_hint", "") or "").strip()
    if explicit == "none":
        return ""
    if explicit in {"crossfit_aipw", "split_conformal_interval"}:
        return explicit
    haystack = " ".join(
        str(part)
        for part in (
            explicit,
            spec.get("id", ""),
            spec.get("name", ""),
            spec.get("algorithm_sketch", ""),
            spec.get("formula", ""),
            question.id,
            question.title,
            question.description,
            " ".join(question.tags),
        )
    ).lower()
    if "crossfit" in haystack or "aipw" in haystack:
        return "crossfit_aipw"
    if "conformal" in haystack and (
        "interval" in haystack
        or "prediction" in haystack
        or "coverage" in haystack
    ):
        return "split_conformal_interval"
    return ""


def _critic_next_action_agenda(
    *,
    question: OpenResearchQuestion,
    retrieval_manifest: Mapping[str, Any],
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    algorithm_manifest: Mapping[str, Any],
    formalization_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    agenda: list[dict[str, Any]] = []
    formal_counts = formalization_manifest.get("counts", {}) if isinstance(formalization_manifest, Mapping) else {}
    proof_bank_memory_summary = (
        formalization_manifest.get("proof_bank_runtime_memory_summary", {})
        if isinstance(
            formalization_manifest.get("proof_bank_runtime_memory_summary", {}),
            Mapping,
        )
        else {}
    )
    if int(formal_counts.get("formal_gap", 0) or 0) > 0:
        gap_goals = [
            row.get("id", "")
            for row in formalization_manifest.get("deterministic_theorem_goals", []) or []
            if isinstance(row, Mapping)
        ]
        if proof_bank_memory_summary.get(
            "source_theorem_exact_candidate_environment_gap", False
        ):
            agenda.append(
                {
                    "id": "formal_gap:source_theorem_formal_environment_repair",
                    "owner_subsystem": "Formalizer/ProofEngineer/LeanProver",
                    "trigger": "SOURCE_THEOREM_EXACT_CANDIDATE_FORMAL_ENVIRONMENT_GAP",
                    "action": (
                        "repair the exact source-theorem candidate formal environment: "
                        "identify the required Lean project, imports, source theorem "
                        "module, and missing statistical primitives before attempting "
                        "proof-body tactics"
                    ),
                    "acceptance_gate": (
                        "local Lean/AXLE reaches the exact source theorem declaration "
                        "with imports and symbols resolved; proof evidence still requires "
                        "artifact_kernel_verified/source_theorem_kernel_verified"
                    ),
                    "target_ids": list(
                        proof_bank_memory_summary.get(
                            "source_theorem_exact_candidate_repair_target_names",
                            [],
                        )
                        or []
                    )
                    or [row for row in gap_goals if row],
                    "failure_classifications": list(
                        proof_bank_memory_summary.get(
                            "source_theorem_exact_candidate_failure_classifications",
                            [],
                        )
                        or []
                    ),
                    "priority": "high",
                    "proof_boundary": KERNEL_PROOF_BOUNDARY,
                }
            )
        elif _formalization_manifest_has_remaining_proof_bank_work(formalization_manifest):
            agenda.append(
                {
                    "id": "formal_gap:proof_bank_expansion",
                    "owner_subsystem": "Formalizer/LeanProver",
                    "trigger": "FORMAL_GAP",
                    "action": "promote retrieved formal-source hits into reusable Lean proof-bank obligations",
                    "acceptance_gate": "AXLE/local Lean kernel verifies the new obligation and full theorem gaps remain explicit",
                    "target_ids": [row for row in gap_goals if row],
                    "priority": "high",
                    "proof_boundary": KERNEL_PROOF_BOUNDARY,
                }
            )
        elif _formalization_manifest_has_kernel_verified_theorem_closure(
            formalization_manifest
        ) and _formalization_manifest_has_kernel_verified_source_semantic_support(
            formalization_manifest
        ):
            agenda.append(
                {
                    "id": "formal_gap:source_theorem_exact_semantics_or_promotion",
                    "owner_subsystem": "TheoryDeveloper/Formalizer/LeanProver",
                    "trigger": "FORMAL_GAP_AFTER_KERNEL_VERIFIED_CLOSURE_AND_SEMANTIC_BRIDGE_SUPPORT",
                    "action": (
                        "target exact upstream statistical semantic definitions or source-theorem "
                        "promotion, while preserving the distinction between verified registered "
                        "semantic bridges and the full source theorem"
                    ),
                    "acceptance_gate": (
                        "AXLE/local Lean kernel verifies exact upstream semantic primitives or "
                        "the full source theorem; registered bridge evidence remains separately scoped"
                    ),
                    "target_ids": [row for row in gap_goals if row],
                    "priority": "high",
                    "proof_boundary": KERNEL_PROOF_BOUNDARY,
                }
            )
        elif _formalization_manifest_has_kernel_verified_theorem_closure(
            formalization_manifest
        ):
            agenda.append(
                {
                    "id": "formal_gap:source_theorem_semantic_primitives",
                    "owner_subsystem": "TheoryDeveloper/Formalizer/LeanProver",
                    "trigger": "FORMAL_GAP_AFTER_KERNEL_VERIFIED_THEOREM_REDUCTION_CLOSURE",
                    "action": (
                        "formalize the upstream statistical semantics needed by the source theorem, "
                        "such as exchangeability-to-uniform-rank and order-statistic quantile construction"
                    ),
                    "acceptance_gate": (
                        "AXLE/local Lean kernel verifies each upstream primitive, and the manifest "
                        "keeps theorem-reduction closure evidence separate from full source theorem proof"
                    ),
                    "target_ids": [row for row in gap_goals if row],
                    "priority": "high",
                    "proof_boundary": KERNEL_PROOF_BOUNDARY,
                }
            )
        else:
            agenda.append(
                {
                    "id": "formal_gap:theorem_reduction_closure",
                    "owner_subsystem": "Formalizer/LeanProver",
                    "trigger": "FORMAL_GAP_WITH_PROOF_BANK_EXHAUSTED",
                    "action": (
                        "formalize the theorem-level reduction that connects the "
                        "kernel-verified proof-bank subclaims to the frontier theorem statement"
                    ),
                    "acceptance_gate": (
                        "AXLE/local Lean kernel verifies the theorem-level reduction, "
                        "or the manifest records a precise semantic/source theorem blocker"
                    ),
                    "target_ids": [row for row in gap_goals if row],
                    "priority": "high",
                    "proof_boundary": KERNEL_PROOF_BOUNDARY,
                }
            )
        if str(formalization_manifest.get("formalization_gap_planner_bridge_id", "")).strip():
            agenda.append(
                {
                    "id": "formal_gap:gap_planner_handoff",
                    "owner_subsystem": "FormalizationGapPlanner",
                    "trigger": "FORMAL_GAP_WITH_RUNTIME_GAP_PLANNER_SEED",
                    "action": (
                        "stage the LLM route-planner prompt packets from the "
                        "runtime standalone seed, then run the standalone "
                        "minimal-delta planner before expanding broad theory"
                    ),
                    "acceptance_gate": (
                        "LLM route plan, standalone gap plan, source grounding "
                        "audit, and target-prover replay preserve proof boundaries"
                    ),
                    "formalization_gap_planner_bridge_id": str(
                        formalization_manifest.get(
                            "formalization_gap_planner_bridge_id",
                            "",
                        )
                    ),
                    "standalone_seed_artifact_id": str(
                        formalization_manifest.get(
                            "formalization_gap_planner_standalone_seed_artifact_id",
                            "",
                        )
                    ),
                    "target_ids": [row for row in gap_goals if row],
                    "priority": "high",
                    "proof_boundary": (
                        RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY
                    ),
                }
            )
    if int(formal_counts.get("kernel_verified", 0) or 0) == 0 and int(formal_counts.get("proved", 0) or 0) > 0:
        agenda.append(
            {
                "id": "proof_feedback:kernel_rerun",
                "owner_subsystem": "FormalizationEvaluator",
                "trigger": "NONKERNEL_PROOF_ROWS",
                "action": "rerun registered proof-bank rows with --local-lean or --real-lean before claiming kernel evidence",
                "acceptance_gate": "kernel_verified count is recorded from AXLE/local Lean",
                "priority": "high",
                "proof_boundary": KERNEL_PROOF_BOUNDARY,
            }
        )
    if isinstance(algorithm_manifest, Mapping) and int(algorithm_manifest.get("n_executed", 0) or 0) > 0:
        agenda.append(
            {
                "id": "algorithm:prototype_review",
                "owner_subsystem": "AlgorithmEngineer",
                "trigger": "SANDBOX_PROTOTYPE_EXECUTED",
                "action": "review sandbox prototype and, if appropriate, promote through registered algorithm audit",
                "acceptance_gate": "production implementation hash, registry entry, tests, and simulation rerun pass",
                "target_ids": [
                    row.get("estimator_id", "")
                    for row in algorithm_manifest.get("prototypes", []) or []
                    if isinstance(row, Mapping)
                ],
                "priority": "medium",
                "boundary": algorithm_manifest.get("boundary", ""),
            }
        )
    if isinstance(simulation_manifest, Mapping) and simulation_manifest.get("simulation_passed") is not True:
        agenda.append(
            {
                "id": "simulation:theory_revision",
                "owner_subsystem": "TheoryDeveloper",
                "trigger": "SIMULATION_DIAGNOSTIC_FAILURE",
                "action": "revise theorem/procedure using failed simulation diagnostics",
                "acceptance_gate": "rerun simulation passes or blocker is classified",
                "priority": "high",
                "boundary": SIMULATION_NOT_PROOF_BOUNDARY,
            }
        )
    retrieval_counts = retrieval_manifest.get("counts", {}) if isinstance(retrieval_manifest, Mapping) else {}
    if int(retrieval_counts.get("formal_source_hits", 0) or 0) == 0:
        agenda.append(
            {
                "id": "retrieval:expand_formal_sources",
                "owner_subsystem": "RetrievalMemory",
                "trigger": "NO_FORMAL_SOURCE_HITS",
                "action": "expand Lean/Mathlib/StatInference/OpenProver search context for this theorem family",
                "acceptance_gate": "retrieval manifest records formal-source hits or an explicit source-authority gap",
                "priority": "medium",
                "boundary": retrieval_manifest.get("boundary", ""),
            }
        )
    if not agenda:
        agenda.append(
            {
                "id": "monitor:runtime_trace",
                "owner_subsystem": "CriticEvaluator",
                "trigger": "NO_BLOCKING_RUNTIME_GAPS",
                "action": "archive runtime trace or expand benchmark stress tests",
                "acceptance_gate": "evidence ledger boundaries remain intact",
                "priority": "low",
            }
        )
    for row in agenda:
        row["question_id"] = question.id
        row["theory_packet_id"] = str(theory_packet.get("packet_id", ""))
    return agenda


def _formalization_manifest_has_remaining_proof_bank_work(
    formalization_manifest: Mapping[str, Any],
) -> bool:
    proof_control = (
        formalization_manifest.get("proof_obligation_control", {})
        if isinstance(formalization_manifest.get("proof_obligation_control"), Mapping)
        else {}
    )
    if not proof_control:
        return True
    for key in (
        "deferred_priority_proof_obligation_ids_due_to_max",
        "deferred_proof_obligation_ids_due_to_max",
        "requested_non_candidate_proof_obligation_ids",
    ):
        if any(str(row).strip() for row in proof_control.get(key, []) or []):
            return True
    formal_subclaims = (
        formalization_manifest.get("formal_subclaims", [])
        if isinstance(formalization_manifest.get("formal_subclaims", []), list)
        else []
    )
    for row in formal_subclaims:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("claim_type", "")) != "lean_obligation":
            continue
        if row.get("status") == "FAILED":
            return True
        if row.get("status") == "PROVED" and row.get("kernel_verified") is not True:
            return True
    candidate_ids = {
        str(row).strip()
        for row in proof_control.get("candidate_proof_obligation_ids", []) or []
        if str(row).strip()
    }
    if not candidate_ids:
        return False
    kernel_verified_ids = {
        str(row.get("proof_obligation_id", "")).strip()
        for row in formal_subclaims
        if isinstance(row, Mapping)
        and row.get("kernel_verified") is True
        and str(row.get("proof_obligation_id", "")).strip()
    }
    kernel_verified_ids |= {
        str(row).strip()
        for row in proof_control.get("memory_kernel_verified_proof_obligation_ids", []) or []
        if str(row).strip()
    }
    kernel_verified_ids |= {
        str(row).strip()
        for row in proof_control.get("excluded_candidate_proof_obligation_ids", []) or []
        if str(row).strip()
    }
    return bool(candidate_ids - kernel_verified_ids)


def _formalization_manifest_has_kernel_verified_theorem_closure(
    formalization_manifest: Mapping[str, Any],
) -> bool:
    proof_control = (
        formalization_manifest.get("proof_obligation_control", {})
        if isinstance(formalization_manifest.get("proof_obligation_control"), Mapping)
        else {}
    )
    if proof_control.get("theorem_reduction_closure_already_kernel_verified") is True:
        return True
    summary = (
        formalization_manifest.get("proof_bank_runtime_memory_summary", {})
        if isinstance(
            formalization_manifest.get("proof_bank_runtime_memory_summary"),
            Mapping,
        )
        else {}
    )
    return summary.get("theorem_reduction_closure_already_kernel_verified") is True


def _formalization_manifest_has_kernel_verified_source_semantic_support(
    formalization_manifest: Mapping[str, Any],
) -> bool:
    proof_control = (
        formalization_manifest.get("proof_obligation_control", {})
        if isinstance(formalization_manifest.get("proof_obligation_control"), Mapping)
        else {}
    )
    if any(
        str(row).strip()
        for row in proof_control.get(
            "memory_kernel_verified_source_theorem_semantic_primitive_ids",
            [],
        )
        or []
    ):
        return True
    summary = (
        formalization_manifest.get("proof_bank_runtime_memory_summary", {})
        if isinstance(
            formalization_manifest.get("proof_bank_runtime_memory_summary"),
            Mapping,
        )
        else {}
    )
    return any(
        str(row).strip()
        for row in summary.get(
            "memory_kernel_verified_source_theorem_semantic_primitive_ids",
            [],
        )
        or []
    )


def _runtime_learning_memory_kernel_verified_theorem_reduction_closure(
    architect_context: Mapping[str, Any],
) -> dict[str, tuple[str, ...]]:
    memory = (
        architect_context.get("runtime_learning_memory", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if (
        not isinstance(memory, Mapping)
        or memory.get("artifact_kind") != "RuntimeLearningMemoryContext"
    ):
        return {"work_order_ids": (), "target_ids": (), "goal_ids": ()}
    rows = memory.get("rows", []) if isinstance(memory.get("rows"), list) else []
    work_order_ids: list[str] = []
    target_ids: list[str] = []
    goal_ids: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        for key, bucket in (
            ("kernel_verified_theorem_reduction_closure_work_order_ids", work_order_ids),
            ("kernel_verified_theorem_reduction_closure_target_ids", target_ids),
            ("kernel_verified_theorem_reduction_closure_goal_ids", goal_ids),
        ):
            for value in row.get(key, []) or []:
                text = str(value).strip()
                if text:
                    bucket.append(text)
        input_summary = row.get("input_summary", {})
        if isinstance(input_summary, Mapping):
            for key, bucket in (
                ("kernel_verified_theorem_reduction_closure_work_order_ids", work_order_ids),
                ("kernel_verified_theorem_reduction_closure_target_ids", target_ids),
                ("kernel_verified_theorem_reduction_closure_goal_ids", goal_ids),
            ):
                for value in input_summary.get(key, []) or []:
                    text = str(value).strip()
                    if text:
                        bucket.append(text)
    return {
        "work_order_ids": tuple(dict.fromkeys(work_order_ids)),
        "target_ids": tuple(dict.fromkeys(target_ids)),
        "goal_ids": tuple(dict.fromkeys(goal_ids)),
    }


def _runtime_learning_memory_kernel_verified_source_theorem_semantic_primitives(
    architect_context: Mapping[str, Any],
) -> tuple[str, ...]:
    memory = (
        architect_context.get("runtime_learning_memory", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if not isinstance(memory, Mapping) or memory.get("artifact_kind") != "RuntimeLearningMemoryContext":
        return ()
    rows = memory.get("rows", []) if isinstance(memory.get("rows"), list) else []
    primitive_ids: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        for value in row.get("kernel_verified_source_theorem_semantic_primitive_ids", []) or []:
            text = str(value).strip()
            if text:
                primitive_ids.append(text)
        input_summary = row.get("input_summary", {})
        if isinstance(input_summary, Mapping):
            for value in input_summary.get(
                "kernel_verified_source_theorem_semantic_primitive_ids",
                [],
            ) or []:
                text = str(value).strip()
                if text:
                    primitive_ids.append(text)
    return tuple(dict.fromkeys(primitive_ids))


def _runtime_learning_memory_source_theorem_promotion_ready_unproved_targets(
    architect_context: Mapping[str, Any],
) -> tuple[str, ...]:
    memory = (
        architect_context.get("runtime_learning_memory", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if not isinstance(memory, Mapping) or memory.get("artifact_kind") != "RuntimeLearningMemoryContext":
        return ()
    rows = memory.get("rows", []) if isinstance(memory.get("rows"), list) else []
    targets: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        input_summary = row.get("input_summary", {})
        trigger = _runtime_learning_row_trigger(row, input_summary)
        if (
            str(row.get("learning_task", "") or "")
            != "source_theorem_promotion_bridge_feedback"
            and trigger != "SOURCE_THEOREM_PROMOTION_READY_BUT_UNPROVED"
        ):
            continue
        source_theorem_kernel_verified = bool(
            row.get("source_theorem_kernel_verified", False)
        )
        if isinstance(input_summary, Mapping):
            source_theorem_kernel_verified = bool(
                source_theorem_kernel_verified
                or input_summary.get("source_theorem_kernel_verified", False)
            )
        if source_theorem_kernel_verified:
            continue
        target = str(row.get("target_theorem_name", "") or "").strip()
        if not target and isinstance(input_summary, Mapping):
            target = str(input_summary.get("target_theorem_name", "") or "").strip()
        if target:
            targets.append(target)
    return tuple(dict.fromkeys(targets))


_SOURCE_THEOREM_INTEGRATOR_BLOCKER_TRIGGERS = frozenset(
    {
        "SOURCE_THEOREM_INTEGRATION_BLOCKED_ROUTE_PROBE",
        "SOURCE_THEOREM_INTEGRATION_BLOCKED_VACUOUS_TRUE",
        "SOURCE_THEOREM_INTEGRATION_BLOCKED_TARGET_ASSUMED",
    }
)


_SOURCE_THEOREM_EXACT_CANDIDATE_REPAIR_TRIGGERS = frozenset(
    {
        "SOURCE_THEOREM_EXACT_CANDIDATE_LOCAL_LEAN_FAILED",
        "SOURCE_THEOREM_EXACT_CANDIDATE_STATIC_CHECK_FAILED",
        "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED",
        "EXACT_SOURCE_PROOF_BODY_CANDIDATE_MATERIALIZED",
        "EXACT_SOURCE_PROOF_BODY_ARTIFACT_KERNEL_ENVIRONMENT_OPEN",
    }
)

_SOURCE_THEOREM_EXACT_CANDIDATE_ENVIRONMENT_FAILURES = frozenset(
    {
        "formal_environment_placeholder_primitives",
        "formal_environment_typeclass_blockers_unreviewed",
        "lean_import_environment_missing",
        "formal_environment_symbol_missing",
        "formal_environment_instance_missing",
        "lean_project_or_import_environment_missing",
        "lean_syntax_or_import_environment_gap",
    }
)

_SOURCE_THEOREM_TARGET_PROVENANCE_STRING_KEYS = (
    "source_formalization_manifest_id",
    "source_formalizer_packet_id",
    "source_formal_target_id",
    "source_runtime_learning_task",
    "question_id",
    "source_theorem_target_resolution_id",
    "source_theorem_promotion_id",
    "source_theorem_route_id",
    "source_theorem_queue_item_id",
    "source_theorem_replay_id",
    "source_theorem_task_id",
    "source_theorem_question_id",
    "source_theorem_goal_id",
    "source_theorem_statement",
    "source_theorem_skeleton",
    "source_theorem_lean_file",
    "target_lean_declaration",
    "artifact_verification_id",
    "artifact_verifier_manifest",
    "materialization_id",
    "execution_queue_id",
)


def _source_theorem_target_provenance_from_row(row: Mapping[str, Any]) -> dict[str, Any]:
    sources: list[Mapping[str, Any]] = [row]
    for nested_key in (
        "source_theorem_target_provenance",
        "source_theorem_target_context",
        "kernel_overlay_context",
        "overlay_row",
    ):
        nested = row.get(nested_key, {})
        if isinstance(nested, Mapping):
            sources.append(nested)
    provenance: dict[str, Any] = {}
    if any("source_theorem_target_known" in source for source in sources):
        provenance["source_theorem_target_known"] = any(
            bool(source.get("source_theorem_target_known", False))
            for source in sources
        )
    constraints: list[str] = []
    for source in sources:
        for key in _SOURCE_THEOREM_TARGET_PROVENANCE_STRING_KEYS:
            if key in provenance:
                continue
            value = str(source.get(key, "") or "").strip()
            if value:
                provenance[key] = value
        constraints.extend(
            str(value).strip()
            for value in source.get("semantic_alignment_constraints", []) or []
            if str(value).strip()
        )
    if constraints:
        provenance["semantic_alignment_constraints"] = list(dict.fromkeys(constraints))
    return provenance


def _runtime_learning_row_trigger(
    row: Mapping[str, Any],
    input_summary: Any,
) -> str:
    if isinstance(input_summary, Mapping):
        trigger = str(input_summary.get("trigger", "") or "").strip()
        if trigger:
            return trigger
    return str(row.get("trigger", "") or "").strip()


def _source_theorem_missing_formal_symbols_from_diagnostics(
    diagnostics: list[str],
) -> list[str]:
    symbols: list[str] = []
    for index, message in enumerate(diagnostics):
        text = str(message)
        for match in re.finditer(r"identifier `([^`]+)` is unknown", text):
            symbol = match.group(1).strip()
            if symbol and symbol not in symbols:
                symbols.append(symbol)
        lines = text.splitlines()
        for line_index, line in enumerate(lines):
            if "Function expected at" not in line:
                continue
            followup_lines = lines[line_index + 1 :]
            for followup in diagnostics[index + 1 : index + 4]:
                followup_lines.extend(str(followup).splitlines())
            for followup in followup_lines:
                candidate = str(followup).strip()
                if not candidate or candidate.startswith(("but ", "Note:", "Hint:")):
                    continue
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_'.]*", candidate):
                    if candidate not in symbols:
                        symbols.append(candidate)
                    break
    return symbols


def _source_theorem_typeclass_blockers_from_diagnostics(
    diagnostics: list[str],
) -> list[str]:
    blockers: list[str] = []
    for index, message in enumerate(diagnostics):
        text = str(message)
        if "failed to synthesize instance of type class" not in text:
            continue
        lines = text.splitlines()
        followup_lines: list[str] = []
        for line_index, line in enumerate(lines):
            if "failed to synthesize instance of type class" in line:
                followup_lines.extend(lines[line_index + 1 :])
                break
        for followup in diagnostics[index + 1 : index + 5]:
            followup_lines.extend(str(followup).splitlines())
        for followup in followup_lines:
            candidate = str(followup).strip()
            if not candidate or candidate.startswith(("Hint:", "Note:")):
                continue
            if candidate not in blockers:
                blockers.append(candidate)
            break
    return blockers


def _source_theorem_formal_environment_repair_tasks(
    *,
    missing_symbols: list[str],
    typeclass_blockers: list[str],
    failure_classification: str,
) -> list[str]:
    tasks: list[str] = []
    for symbol in missing_symbols:
        tasks.append(
            "resolve Lean declaration/import or explicitly formalize source-theorem "
            f"primitive `{symbol}`"
        )
    for blocker in typeclass_blockers:
        tasks.append(
            "repair exact source-theorem statement so Lean can synthesize typeclass "
            f"instance `{blocker}` without coercion ambiguity"
        )
    if not tasks and failure_classification:
        tasks.append(
            "repair exact source-theorem formal environment for "
            + failure_classification
        )
    if tasks:
        tasks.append(
            "rerun runtime-source-theorem-promotion-proofengineer-bridge with "
            "--overwrite and local Lean/AXLE before claiming proof evidence"
        )
    return tasks[:8]


def _source_theorem_formal_environment_context(
    *,
    diagnostics: list[str],
    failure_classification: str,
) -> dict[str, Any]:
    missing_symbols = _source_theorem_missing_formal_symbols_from_diagnostics(
        diagnostics
    )
    typeclass_blockers = _source_theorem_typeclass_blockers_from_diagnostics(
        diagnostics
    )
    return {
        "missing_formal_symbols": missing_symbols,
        "typeclass_blockers": typeclass_blockers,
        "recommended_repair_tasks": _source_theorem_formal_environment_repair_tasks(
            missing_symbols=missing_symbols,
            typeclass_blockers=typeclass_blockers,
            failure_classification=failure_classification,
        ),
    }


def _runtime_learning_memory_source_theorem_integrator_blockers(
    architect_context: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    memory = (
        architect_context.get("runtime_learning_memory", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if not isinstance(memory, Mapping) or memory.get("artifact_kind") != "RuntimeLearningMemoryContext":
        return ()
    rows = memory.get("rows", []) if isinstance(memory.get("rows"), list) else []
    blockers: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        input_summary = row.get("input_summary", {})
        trigger = _runtime_learning_row_trigger(row, input_summary)
        if (
            str(row.get("learning_task", "") or "")
            != "source_theorem_integrator_blocker_feedback"
            and trigger not in _SOURCE_THEOREM_INTEGRATOR_BLOCKER_TRIGGERS
        ):
            continue
        source_theorem_kernel_verified = bool(
            row.get("source_theorem_kernel_verified", False)
        )
        if isinstance(input_summary, Mapping):
            source_theorem_kernel_verified = bool(
                source_theorem_kernel_verified
                or input_summary.get("source_theorem_kernel_verified", False)
            )
        if source_theorem_kernel_verified:
            continue
        target = str(row.get("target_theorem_name", "") or "").strip()
        if not target and isinstance(input_summary, Mapping):
            target = str(input_summary.get("target_theorem_name", "") or "").strip()
        integration_status = ""
        if isinstance(input_summary, Mapping):
            integration_status = str(input_summary.get("integration_status", "") or "")
        key = (target, trigger or integration_status)
        if key in seen:
            continue
        seen.add(key)
        blockers.append(
            {
                "target_theorem_name": target,
                "trigger": trigger,
                "integration_status": integration_status,
                "route_probe_detected": bool(
                    input_summary.get("route_probe_detected", False)
                )
                if isinstance(input_summary, Mapping)
                else False,
                "vacuous_true_target_detected": bool(
                    input_summary.get("vacuous_true_target_detected", False)
                )
                if isinstance(input_summary, Mapping)
                else False,
                "target_assumption_detected": bool(
                    input_summary.get("target_assumption_detected", False)
                )
                if isinstance(input_summary, Mapping)
                else False,
            }
        )
    return tuple(blockers)


def _runtime_learning_memory_source_theorem_exact_candidate_repairs(
    architect_context: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    memory = (
        architect_context.get("runtime_learning_memory", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if not isinstance(memory, Mapping) or memory.get("artifact_kind") != "RuntimeLearningMemoryContext":
        return ()
    rows = memory.get("rows", []) if isinstance(memory.get("rows"), list) else []
    repairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        input_summary = row.get("input_summary", {})
        trigger = _runtime_learning_row_trigger(row, input_summary)
        if (
            str(row.get("learning_task", "") or "")
            != "source_theorem_exact_candidate_lean_feedback"
            and trigger not in _SOURCE_THEOREM_EXACT_CANDIDATE_REPAIR_TRIGGERS
        ):
            continue
        source_theorem_kernel_verified = bool(
            row.get("source_theorem_kernel_verified", False)
        )
        if isinstance(input_summary, Mapping):
            source_theorem_kernel_verified = bool(
                source_theorem_kernel_verified
                or input_summary.get("source_theorem_kernel_verified", False)
            )
        if source_theorem_kernel_verified:
            continue
        target = str(row.get("target_theorem_name", "") or "").strip()
        if not target and isinstance(input_summary, Mapping):
            target = str(input_summary.get("target_theorem_name", "") or "").strip()
        diagnostics: list[str] = []
        failure_classification = ""
        if isinstance(input_summary, Mapping):
            diagnostics = [
                str(value)
                for value in input_summary.get("diagnostics", []) or []
                if str(value).strip()
            ][:8]
            failure_classification = str(
                input_summary.get("failure_classification", "") or ""
            )
            missing_symbols = [
                str(value)
                for value in (
                    input_summary.get("missing_formal_symbols", [])
                    or input_summary.get("formal_environment_placeholder_symbols", [])
                    or []
                )
                if str(value).strip()
            ]
            typeclass_blockers = [
                str(value)
                for value in (
                    input_summary.get("typeclass_blockers", [])
                    or input_summary.get("formal_environment_typeclass_blockers", [])
                    or []
                )
                if str(value).strip()
            ]
            recommended_repair_tasks = [
                str(value)
                for value in input_summary.get("recommended_repair_tasks", []) or []
                if str(value).strip()
            ]
            if not recommended_repair_tasks and (
                missing_symbols or typeclass_blockers or failure_classification
            ):
                recommended_repair_tasks = _source_theorem_formal_environment_repair_tasks(
                    missing_symbols=missing_symbols,
                    typeclass_blockers=typeclass_blockers,
                    failure_classification=failure_classification,
                )
        else:
            missing_symbols = []
            typeclass_blockers = []
            recommended_repair_tasks = []
        key = (target, trigger)
        if key in seen:
            continue
        seen.add(key)
        repairs.append(
            {
                "target_theorem_name": target,
                "trigger": trigger,
                "verification_status": (
                    str(
                        input_summary.get("verification_status")
                        or input_summary.get("execution_status")
                        or ""
                    )
                    if isinstance(input_summary, Mapping)
                    else ""
                ),
                "candidate_artifact_path": str(
                    row.get("candidate_artifact_path")
                    or (
                        input_summary.get("candidate_artifact_path", "")
                        if isinstance(input_summary, Mapping)
                        else ""
                    )
                    or ""
                ),
                "failure_classification": failure_classification,
                "diagnostics": diagnostics,
                "missing_formal_symbols": missing_symbols,
                "typeclass_blockers": typeclass_blockers,
                "recommended_repair_tasks": recommended_repair_tasks,
            }
        )
    return tuple(repairs)


def _formalizer_proof_bank_runtime_memory_summary(
    *,
    context: Mapping[str, Any],
    proof_bank_obligation_catalog: list[Mapping[str, Any]],
    theorem_goals: list[TheoremGoal],
    memory_kernel_verified_proof_obligation_ids: tuple[str, ...],
    memory_prioritized_proof_obligation_ids: tuple[str, ...],
) -> dict[str, Any]:
    catalog_ids = tuple(
        str(row.get("obligation_id", "") or "").strip()
        for row in proof_bank_obligation_catalog
        if isinstance(row, Mapping) and str(row.get("obligation_id", "") or "").strip()
    )
    catalog_set = set(catalog_ids)
    kernel_verified_ids = tuple(
        row for row in memory_kernel_verified_proof_obligation_ids if row in catalog_set
    )
    prioritized_ids = tuple(row for row in memory_prioritized_proof_obligation_ids if row in catalog_set)
    remaining_ids = tuple(sorted(catalog_set - set(kernel_verified_ids)))
    environment_feedback = (
        context.get("environment_feedback", {}) if isinstance(context.get("environment_feedback"), Mapping) else {}
    )
    high_priority_agenda = [
        row
        for row in environment_feedback.get("high_priority_agenda", []) or []
        if isinstance(row, Mapping)
    ]
    high_priority_agenda_ids = tuple(
        str(row.get("id", "") or "").strip()
        for row in high_priority_agenda
        if str(row.get("id", "") or "").strip()
    )
    theorem_closure_requested_by_critic = (
        "formal_gap:theorem_reduction_closure" in high_priority_agenda_ids
    )
    catalog_exhausted = bool(catalog_ids) and not remaining_ids
    theorem_goal_ids = tuple(_theorem_goal_id(row) for row in theorem_goals if _theorem_goal_id(row))
    theorem_closure_memory = _runtime_learning_memory_kernel_verified_theorem_reduction_closure(
        context
    )
    source_semantic_memory_ids = (
        _runtime_learning_memory_kernel_verified_source_theorem_semantic_primitives(
            context
        )
    )
    promotion_ready_unproved_targets = (
        _runtime_learning_memory_source_theorem_promotion_ready_unproved_targets(
            context
        )
    )
    source_theorem_integrator_blockers = (
        _runtime_learning_memory_source_theorem_integrator_blockers(context)
    )
    source_theorem_exact_candidate_repairs = (
        _runtime_learning_memory_source_theorem_exact_candidate_repairs(context)
    )
    source_theorem_integrator_blocked_targets = tuple(
        dict.fromkeys(
            str(row.get("target_theorem_name", "") or "").strip()
            for row in source_theorem_integrator_blockers
            if str(row.get("target_theorem_name", "") or "").strip()
        )
    )
    source_theorem_exact_candidate_repair_targets = tuple(
        dict.fromkeys(
            str(row.get("target_theorem_name", "") or "").strip()
            for row in source_theorem_exact_candidate_repairs
            if str(row.get("target_theorem_name", "") or "").strip()
        )
    )
    exact_candidate_failure_classifications = tuple(
        dict.fromkeys(
            str(row.get("failure_classification", "") or "").strip()
            for row in source_theorem_exact_candidate_repairs
            if str(row.get("failure_classification", "") or "").strip()
        )
    )
    exact_candidate_environment_gap = any(
        value in _SOURCE_THEOREM_EXACT_CANDIDATE_ENVIRONMENT_FAILURES
        for value in exact_candidate_failure_classifications
    )
    unresolved_source_theorem_promotion_targets = tuple(
        dict.fromkeys(
            [
                *promotion_ready_unproved_targets,
                *source_theorem_integrator_blocked_targets,
                *source_theorem_exact_candidate_repair_targets,
            ]
        )
    )
    closure_goal_ids = tuple(
        row for row in theorem_closure_memory["goal_ids"] if row in set(theorem_goal_ids)
    )
    theorem_reduction_closure_already_kernel_verified = bool(closure_goal_ids)
    source_theorem_semantic_primitive_support_already_kernel_verified = bool(
        theorem_reduction_closure_already_kernel_verified and source_semantic_memory_ids
    )
    theorem_reduction_closure_required = bool(
        (theorem_closure_requested_by_critic or catalog_exhausted)
        and not theorem_reduction_closure_already_kernel_verified
    )
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "FormalizerProofBankRuntimeMemorySummary",
        "proof_bank_bridge_catalog_size": len(catalog_set),
        "memory_kernel_verified_proof_obligation_ids": sorted(kernel_verified_ids),
        "memory_prioritized_unverified_proof_obligation_ids": sorted(prioritized_ids),
        "remaining_unverified_proof_bank_obligation_ids": list(remaining_ids),
        "proof_bank_bridge_catalog_exhausted_by_memory": catalog_exhausted,
        "critic_high_priority_agenda_ids": list(high_priority_agenda_ids),
        "theorem_reduction_closure_already_kernel_verified": theorem_reduction_closure_already_kernel_verified,
        "memory_kernel_verified_theorem_reduction_closure_work_order_ids": list(
            theorem_closure_memory["work_order_ids"]
        ),
        "memory_kernel_verified_theorem_reduction_closure_target_ids": list(
            theorem_closure_memory["target_ids"]
        ),
        "memory_kernel_verified_theorem_reduction_closure_goal_ids": list(
            closure_goal_ids
        ),
        "memory_kernel_verified_source_theorem_semantic_primitive_ids": list(
            source_semantic_memory_ids
        ),
        "source_theorem_semantic_primitive_support_already_kernel_verified": (
            source_theorem_semantic_primitive_support_already_kernel_verified
        ),
        "source_theorem_promotion_ready_but_unproved": bool(
            unresolved_source_theorem_promotion_targets
        ),
        "source_theorem_promotion_ready_but_unproved_target_names": list(
            unresolved_source_theorem_promotion_targets
        ),
        "source_theorem_integrator_blocked": bool(
            source_theorem_integrator_blockers
        ),
        "source_theorem_integrator_blocked_target_names": list(
            source_theorem_integrator_blocked_targets
        ),
        "source_theorem_integrator_blocker_triggers": list(
            dict.fromkeys(
                str(row.get("trigger", "") or "")
                for row in source_theorem_integrator_blockers
                if str(row.get("trigger", "") or "")
            )
        ),
        "source_theorem_exact_candidate_requires_repair": bool(
            source_theorem_exact_candidate_repairs
        ),
        "source_theorem_exact_candidate_repair_target_names": list(
            source_theorem_exact_candidate_repair_targets
        ),
        "source_theorem_exact_candidate_repair_triggers": list(
            dict.fromkeys(
                str(row.get("trigger", "") or "")
                for row in source_theorem_exact_candidate_repairs
                if str(row.get("trigger", "") or "")
            )
        ),
        "source_theorem_exact_candidate_failure_classifications": list(
            exact_candidate_failure_classifications
        ),
        "source_theorem_exact_candidate_environment_gap": (
            exact_candidate_environment_gap
        ),
        "source_theorem_exact_candidate_repair_diagnostics": [
            {
                "target_theorem_name": str(
                    row.get("target_theorem_name", "") or ""
                ),
                "verification_status": str(
                    row.get("verification_status", "") or ""
                ),
                "candidate_artifact_path": str(
                    row.get("candidate_artifact_path", "") or ""
                ),
                "failure_classification": str(
                    row.get("failure_classification", "") or ""
                ),
                "diagnostics": list(row.get("diagnostics", []) or []),
                "missing_formal_symbols": list(
                    row.get("missing_formal_symbols", []) or []
                ),
                "typeclass_blockers": list(row.get("typeclass_blockers", []) or []),
                "recommended_repair_tasks": list(
                    row.get("recommended_repair_tasks", []) or []
                ),
            }
            for row in source_theorem_exact_candidate_repairs[:3]
        ],
        "recommended_source_theorem_integration_action": (
            "repair_exact_source_theorem_candidate_formal_environment"
            if exact_candidate_environment_gap
            else
            "repair_exact_source_theorem_candidate_proof_body"
            if source_theorem_exact_candidate_repairs
            else
            "repair_blocked_source_theorem_integration_artifacts"
            if source_theorem_integrator_blockers
            else
            "consume_ready_source_theorem_promotion_queue"
            if unresolved_source_theorem_promotion_targets
            else ""
        ),
        "theorem_reduction_closure_required": theorem_reduction_closure_required,
        "remaining_theorem_goal_ids": list(theorem_goal_ids),
        "recommended_formalizer_target_mode": (
            "theorem_level_reduction_closure"
            if theorem_reduction_closure_required
            else "source_theorem_exact_semantics_or_theorem_promotion"
            if source_theorem_semantic_primitive_support_already_kernel_verified
            else "source_theorem_semantic_primitive_closure"
            if theorem_reduction_closure_already_kernel_verified
            else "registered_proof_bank_obligation_selection"
        ),
        "boundary": (
            "Runtime learning memory records prior kernel-verified bridge obligations and routing hints only. "
            "It is not new proof evidence. When the registered bridge catalog is already exhausted, the "
            "Formalizer should target a theorem-level Lean reduction that connects those verified bridge "
            "obligations to the remaining frontier theorem goal. If runtime memory already records a "
            "kernel-verified theorem-reduction closure, subsequent iterations should target upstream "
            "source-theorem semantic primitives instead of repeating the same closure work order. If "
            "source-semantic bridge support is also kernel verified, subsequent iterations should target "
            "exact upstream semantic definitions or source-theorem promotion while keeping those stronger "
            "claims separate from the registered bridge evidence. If memory records a source-theorem "
            "promotion row that is ready but unproved, consume that exact source-theorem integration "
            "queue next instead of repeating route-probe materialization. If memory records an "
            "integrator blocker, repair the source-theorem artifact into a non-vacuous exact theorem "
            "proof target; route probes, vacuous True targets, and artifacts that assume the target "
            "remain blocked and are not proof evidence. If memory records an exact source-theorem "
            "proof-body executor failure, route the next Formalizer packet to the reported proof-body "
            "or formal-environment repair target; placeholder formal primitives must be closed before "
            "a compiled artifact can be treated as source-theorem proof. If memory records an exact source-theorem "
            "candidate that reached local Lean but failed, keep the exact declaration and repair the "
            "proof body/import/theory gaps from the verifier diagnostics instead of regenerating a "
            "route probe."
        ),
    }


def _should_emit_deterministic_theorem_closure_packet(
    proof_bank_runtime_memory_summary: Mapping[str, Any],
) -> bool:
    return bool(
        proof_bank_runtime_memory_summary.get(
            "proof_bank_bridge_catalog_exhausted_by_memory",
            False,
        )
        and proof_bank_runtime_memory_summary.get(
            "recommended_formalizer_target_mode",
            "",
        )
        == "theorem_level_reduction_closure"
    )


def _deterministic_theorem_closure_proposal_packet(
    *,
    question: OpenResearchQuestion,
    theorem_goals: list[TheoremGoal],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
) -> dict[str, Any]:
    target_goal_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get("remaining_theorem_goal_ids", []) or []
        if str(row).strip()
    ] or [_theorem_goal_id(row) for row in theorem_goals if _theorem_goal_id(row)]
    verified_bridge_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get(
            "memory_kernel_verified_proof_obligation_ids",
            [],
        )
        or []
        if str(row).strip()
    ]
    target_rows: list[dict[str, Any]] = []
    for goal_id in target_goal_ids:
        safe_goal = _safe_identifier(goal_id or "frontier_theorem")
        lean_statement_sketch = _deterministic_theorem_closure_lean_statement_sketch(
            goal_id=goal_id,
            verified_bridge_ids=verified_bridge_ids,
        )
        is_kernel_check_ready = "sorry" not in lean_statement_sketch
        target_rows.append(
            {
                "id": f"{safe_goal}_reduction_closure",
                "informal_source": (
                    "Connect the runtime-memory kernel-verified proof-bank bridge "
                    "obligations to the remaining frontier theorem goal."
                ),
                "lean_statement_sketch": lean_statement_sketch,
                "semantic_alignment_constraints": [
                    "Do not strengthen assumptions beyond the source theorem.",
                    "Preserve the theorem goal semantics; bridge obligations are subclaims only.",
                    "Do not treat this work order or sketch as proof evidence until local Lean/AXLE checks it.",
                ],
                "expected_status": "KERNEL_CHECK_READY" if is_kernel_check_ready else "OPEN",
            }
        )
    packet_id = (
        "formalizer_proposal:"
        + stable_hash(
            {
                "source_agent": "DeterministicTheoremClosureWorkOrderSeed",
                "question_id": question.id,
                "target_goal_ids": target_goal_ids,
                "verified_bridge_ids": verified_bridge_ids,
            }
        )[:24]
    )
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": packet_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "DeterministicTheoremClosureWorkOrderSeed",
        "provider": "deterministic",
        "model": "runtime_memory_theorem_closure_seed",
        "model_tier": "none",
        "question": _question_to_payload(question),
        "proof_evidence_status": "DETERMINISTIC_THEOREM_CLOSURE_PACKET_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": FORMALIZER_BOUNDARY,
        "kernel_verified": False,
        "full_frontier_theorem_proved": False,
        "formal_targets": target_rows,
        "lemma_dependency_plan": [
            {
                "from": "kernel_verified_proof_bank_bridge_memory",
                "to": ",".join(target_goal_ids),
                "role": "theorem-level reduction work order",
                "risk": "source theorem may still require missing formal primitives or semantic alignment",
            }
        ],
        "retrieval_queries": [
            {
                "query": "theorem-level reduction closure for verified proof-bank bridge obligations",
                "target_library": "LeanRAG",
                "purpose": "find source theorem primitives and reusable Lean reductions",
            }
        ],
        "proof_search_plan": {
            "preferred_tools": ["local_lean", "lean_lsp_mcp", "formal_source_retriever"],
            "tactic_or_certificate_hints": [
                "start from the exported theorem-reduction closure work order",
                "reuse only kernel-verified bridge obligations from runtime memory",
            ],
            "kernel_check_plan": [
                "materialize a Lean theorem-level reduction with no sorry",
                "run local Lean or AXLE before claiming proof evidence",
            ],
            "known_blockers": [
                "the full source theorem may still need exchangeability/order-statistic primitives",
            ],
        },
        "proof_bank_obligation_requests": [],
        "gap_taxonomy": [
            {
                "gap": "theorem-level reduction closure still needs a Lean proof",
                "kind": "proof_search",
                "next_owner": "ProofEngineer/LeanProver",
            }
        ],
        "critic_findings": [
            {
                "critic": "proof_boundary_critic",
                "finding": (
                    "All registered bridge obligations are memory-kernel-verified, "
                    "but the frontier theorem is not proved until the reduction closes."
                ),
                "reroute_if_confirmed": "FormalizationEvaluator",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "ProofEngineer/LeanProver",
                "action": "prove the theorem-level reduction closure or record exact blockers",
                "acceptance_gate": "local Lean/AXLE kernel verifies the intended reduction with no sorry",
            }
        ],
    }


def _deterministic_theorem_closure_lean_statement_sketch(
    *,
    goal_id: str,
    verified_bridge_ids: list[str],
) -> str:
    verified_bridge_set = set(verified_bridge_ids)
    if goal_id == "split_conformal_finite_sample_coverage" and (
        "split_conformal_good_rank_coverage_bridge" in verified_bridge_set
        or "split_conformal_bad_rank_reduction_bridge" in verified_bridge_set
    ):
        if "split_conformal_good_rank_coverage_bridge" in verified_bridge_set:
            obligation_id = "split_conformal_good_rank_coverage_bridge"
            source_theorem_name = "splitConformalCoverage_of_goodRankCoverage"
            reduction_description = "good-rank-containment-to-coverage"
        else:
            obligation_id = "split_conformal_bad_rank_reduction_bridge"
            source_theorem_name = "splitConformalCoverage_of_badRankBudget"
            reduction_description = "bad-rank-budget-to-coverage"
        obligation = get_obligation(obligation_id)
        statement = obligation.formal_statement.strip().replace(
            f"theorem {source_theorem_name}",
            "theorem splitConformalFiniteSampleCoverage_reductionClosure",
            1,
        )
        candidate = re.sub(
            r":=\s*by\s+sorry\s*$",
            ":= " + obligation.proof_body.strip(),
            statement,
            flags=re.S,
        )
        if "sorry" not in candidate:
            return (
                "/-\n"
                "Deterministic theorem-closure reduction generated from the "
                f"kernel-verified {obligation_id} proof-bank obligation.\n"
                f"This proves the {reduction_description} reduction only; exchangeability, "
                "rank-uniformity, and order-statistic construction remain explicit upstream assumptions.\n"
                "-/\n"
                + candidate
            )
    safe_goal = _safe_identifier(goal_id or "frontier_theorem")
    return "\n".join(
        [
            f"theorem {safe_goal}_reduction_closure :",
            "    True := by",
            "  -- Replace this placeholder with the theorem-level reduction",
            "  -- from the verified bridge obligations to the source theorem.",
            "  sorry",
        ]
    )


def _formalizer_theorem_reduction_closure_work_orders(
    *,
    proposal_packet: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    theorem_goals: list[Any],
) -> list[dict[str, Any]]:
    if not proof_bank_runtime_memory_summary.get("theorem_reduction_closure_required"):
        return []
    target_mode = str(
        proof_bank_runtime_memory_summary.get("recommended_formalizer_target_mode", "")
        or ""
    )
    if target_mode != "theorem_level_reduction_closure":
        return []
    remaining_goal_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get("remaining_theorem_goal_ids", []) or []
        if str(row).strip()
    ] or [_theorem_goal_id(row) for row in theorem_goals if _theorem_goal_id(row)]
    verified_bridge_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get(
            "memory_kernel_verified_proof_obligation_ids",
            [],
        )
        or []
        if str(row).strip()
    ]
    work_orders: list[dict[str, Any]] = []
    gap_rows = [
        dict(row)
        for row in proposal_packet.get("gap_taxonomy", []) or []
        if isinstance(row, Mapping)
    ][:5]
    for target in proposal_packet.get("formal_targets", []) or []:
        if not isinstance(target, Mapping):
            continue
        target_id = str(target.get("id", "") or "").strip()
        target_text = json.dumps(target, default=str).lower()
        is_closure_target = (
            "reduction_closure" in target_id
            or "theorem_level_reduction" in target_text
            or ("reduction" in target_text and "closure" in target_text)
        )
        if not target_id or not is_closure_target:
            continue
        work_order = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "TheoremReductionClosureWorkOrder",
            "work_order_id": "theorem_reduction_closure_work_order:"
            + stable_hash([target_id, remaining_goal_ids, verified_bridge_ids])[:20],
            "source_formalizer_packet_id": str(proposal_packet.get("packet_id", "")),
            "source_formal_target_id": target_id,
            "target_theorem_goal_ids": remaining_goal_ids,
            "verified_bridge_obligation_ids": verified_bridge_ids,
            "remaining_unverified_proof_bank_obligation_ids": [
                str(row).strip()
                for row in proof_bank_runtime_memory_summary.get(
                    "remaining_unverified_proof_bank_obligation_ids",
                    [],
                )
                or []
                if str(row).strip()
            ],
            "lean_statement_sketch": str(target.get("lean_statement_sketch", "") or ""),
            "informal_source": str(target.get("informal_source", "") or ""),
            "semantic_alignment_constraints": [
                str(row)
                for row in target.get("semantic_alignment_constraints", []) or []
            ][:5],
            "gap_taxonomy": gap_rows,
            "proof_mode": "theorem_level_reduction_closure",
            "acceptance_gate": (
                "AXLE/local Lean kernel verifies the theorem-level reduction with no sorry; "
                "otherwise record the exact formal primitive, semantic alignment, or source-theorem blocker."
            ),
            "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        }
        work_orders.append(work_order)
    return work_orders


def _source_semantic_primitive_id(gap_text: str, gap_kind: str) -> str:
    text = f"{gap_kind} {gap_text}".lower()
    if "exchangeab" in text and "rank" in text:
        return "exchangeability_to_uniform_rank_semantics"
    if "exchangeab" in text:
        return "exchangeability_semantics"
    if "orderstat" in text or "order statistic" in text or "quantile" in text:
        return "order_statistic_quantile_semantics"
    if "rank" in text and "uniform" in text:
        return "rank_uniformity_semantics"
    if "measur" in text:
        return "measurability_semantics"
    return "source_theorem_semantic_primitive:" + stable_hash(
        [gap_kind, gap_text]
    )[:16]


def _formalizer_source_theorem_semantic_primitive_work_orders(
    *,
    proposal_packet: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    theorem_goals: list[Any],
) -> list[dict[str, Any]]:
    target_mode = str(
        proof_bank_runtime_memory_summary.get("recommended_formalizer_target_mode", "")
        or ""
    )
    if target_mode != "source_theorem_semantic_primitive_closure":
        return []
    if not proof_bank_runtime_memory_summary.get(
        "theorem_reduction_closure_already_kernel_verified"
    ):
        return []

    target_goal_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get("remaining_theorem_goal_ids", []) or []
        if str(row).strip()
    ] or [_theorem_goal_id(row) for row in theorem_goals if _theorem_goal_id(row)]
    closure_work_order_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get(
            "memory_kernel_verified_theorem_reduction_closure_work_order_ids",
            [],
        )
        or []
        if str(row).strip()
    ]
    closure_target_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get(
            "memory_kernel_verified_theorem_reduction_closure_target_ids",
            [],
        )
        or []
        if str(row).strip()
    ]
    verified_bridge_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get(
            "memory_kernel_verified_proof_obligation_ids",
            [],
        )
        or []
        if str(row).strip()
    ]
    source_formal_target_ids = [
        str(row.get("id", "") or "").strip()
        for row in proposal_packet.get("formal_targets", []) or []
        if isinstance(row, Mapping) and str(row.get("id", "") or "").strip()
    ]
    gap_rows = [
        dict(row)
        for row in proposal_packet.get("gap_taxonomy", []) or []
        if isinstance(row, Mapping)
    ]
    selected_gaps: list[dict[str, str]] = []
    for row in gap_rows:
        gap = str(row.get("gap", "") or "").strip()
        kind = str(row.get("kind", "") or "").strip()
        next_owner = str(row.get("next_owner", "") or "").strip()
        text = f"{kind} {gap}".lower()
        stale_reduction_gap = (
            "reduction closure" in text
            or "reduction_closure" in text
            or "single lean proof term" in text
        )
        source_semantic_gap = (
            "formal_primitive" in text
            or "formal primitive" in text
            or "exchangeab" in text
            or "orderstat" in text
            or "order statistic" in text
            or "quantile" in text
            or "rank uniform" in text
            or "source theorem semantic" in text
        )
        if gap and source_semantic_gap and not stale_reduction_gap:
            selected_gaps.append(
                {"gap": gap, "kind": kind, "next_owner": next_owner}
            )

    if not selected_gaps:
        selected_gaps.append(
            {
                "gap": (
                    "Formalize the upstream statistical semantics required to connect "
                    "the kernel-verified theorem-reduction closure to the source theorem."
                ),
                "kind": "source_theorem_semantic_primitives",
                "next_owner": "FormalizerProofEngineer",
            }
        )

    work_orders: list[dict[str, Any]] = []
    for gap_row in selected_gaps[:8]:
        gap = gap_row["gap"]
        kind = gap_row["kind"]
        primitive_id = _source_semantic_primitive_id(gap, kind)
        work_orders.append(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "source_theorem_semantic_primitive_work_order:"
                + stable_hash(
                    [
                        primitive_id,
                        gap,
                        target_goal_ids,
                        closure_work_order_ids,
                        source_formal_target_ids,
                    ]
                )[:20],
                "semantic_primitive_id": primitive_id,
                "semantic_primitive_gap": gap,
                "semantic_primitive_gap_kind": kind,
                "next_owner": gap_row["next_owner"] or "FormalizerProofEngineer",
                "source_formalizer_packet_id": str(proposal_packet.get("packet_id", "")),
                "source_formal_target_ids": source_formal_target_ids,
                "target_theorem_goal_ids": target_goal_ids,
                "kernel_verified_theorem_reduction_closure_work_order_ids": closure_work_order_ids,
                "kernel_verified_theorem_reduction_closure_target_ids": closure_target_ids,
                "memory_kernel_verified_bridge_obligation_ids": verified_bridge_ids,
                "proof_mode": "source_theorem_semantic_primitive_closure",
                "acceptance_gate": (
                    "AXLE/local Lean kernel verifies the upstream semantic primitive "
                    "with no sorry, and the manifest keeps this primitive evidence "
                    "separate from theorem-reduction closure and full source theorem proof."
                ),
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            }
        )
    return work_orders


def _runtime_source_theorem_formal_environment_work_order_rows(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for result in results:
        artifacts = result.get("blackboard", {}).get("artifacts", {})
        if not isinstance(artifacts, Mapping):
            continue
        for artifact in artifacts.values():
            if not (
                isinstance(artifact, Mapping)
                and artifact.get("artifact_kind") == "RuntimeFormalizationManifest"
            ):
                continue
            proof_memory = artifact.get("proof_bank_runtime_memory_summary", {})
            if not isinstance(proof_memory, Mapping) or not proof_memory.get(
                "source_theorem_exact_candidate_environment_gap",
                False,
            ):
                continue
            question = (
                artifact.get("question", {})
                if isinstance(artifact.get("question"), Mapping)
                else {}
            )
            repair_rows = [
                row
                for row in proof_memory.get(
                    "source_theorem_exact_candidate_repair_diagnostics",
                    [],
                )
                or []
                if isinstance(row, Mapping)
            ]
            if not repair_rows:
                repair_rows = [
                    {
                        "target_theorem_name": target,
                        "failure_classification": failure,
                        "diagnostics": [],
                        "candidate_artifact_path": "",
                    }
                    for target in proof_memory.get(
                        "source_theorem_exact_candidate_repair_target_names",
                        [],
                    )
                    or []
                    for failure in proof_memory.get(
                        "source_theorem_exact_candidate_failure_classifications",
                        [],
                    )
                    or [""]
                ]
            for repair in repair_rows[:8]:
                failure_classification = str(
                    repair.get("failure_classification", "") or ""
                ).strip()
                if (
                    failure_classification
                    and failure_classification
                    not in _SOURCE_THEOREM_EXACT_CANDIDATE_ENVIRONMENT_FAILURES
                ):
                    continue
                target_theorem_name = str(
                    repair.get("target_theorem_name", "") or ""
                ).strip()
                candidate_artifact_path = str(
                    repair.get("candidate_artifact_path", "") or ""
                ).strip()
                diagnostics = [
                    str(value)
                    for value in repair.get("diagnostics", []) or []
                    if str(value).strip()
                ][:8]
                context = _source_theorem_formal_environment_context(
                    diagnostics=diagnostics,
                    failure_classification=failure_classification,
                )
                missing_symbols = [
                    str(value)
                    for value in (
                        repair.get("missing_formal_symbols", [])
                        or context["missing_formal_symbols"]
                    )
                    if str(value).strip()
                ]
                typeclass_blockers = [
                    str(value)
                    for value in (
                        repair.get("typeclass_blockers", [])
                        or context["typeclass_blockers"]
                    )
                    if str(value).strip()
                ]
                recommended_repair_tasks = [
                    str(value)
                    for value in (
                        repair.get("recommended_repair_tasks", [])
                        or context["recommended_repair_tasks"]
                    )
                    if str(value).strip()
                ]
                source_target_provenance = _source_theorem_target_provenance_from_row(
                    repair
                )
                if question.get("id") and not source_target_provenance.get(
                    "source_theorem_question_id"
                ):
                    source_target_provenance["source_theorem_question_id"] = str(
                        question.get("id", "")
                    )
                semantic_alignment_constraints = list(
                    source_target_provenance.get("semantic_alignment_constraints", [])
                    or []
                )
                work_order_id = "source_theorem_formal_environment_work_order:" + stable_hash(
                    [
                        artifact.get("manifest_id", ""),
                        target_theorem_name,
                        candidate_artifact_path,
                        failure_classification,
                        diagnostics,
                        source_target_provenance,
                    ]
                )[:20]
                if work_order_id in seen:
                    continue
                seen.add(work_order_id)
                rows.append(
                    {
                        "schema_version": RUNTIME_SCHEMA_VERSION,
                        "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                        "work_order_id": work_order_id,
                        "source_formalization_manifest_id": str(
                            artifact.get("manifest_id", "") or ""
                        ),
                        "question_id": str(question.get("id", "") or ""),
                        "question_title": str(question.get("title", "") or ""),
                        "target_theorem_name": target_theorem_name,
                        "target_lean_declaration": str(
                            source_target_provenance.get("target_lean_declaration", "")
                            or target_theorem_name
                        ),
                        "candidate_artifact_path": candidate_artifact_path,
                        "source_theorem_target_known": bool(
                            source_target_provenance.get(
                                "source_theorem_target_known",
                                False,
                            )
                        ),
                        "source_theorem_target_provenance": source_target_provenance,
                        "semantic_alignment_constraints": semantic_alignment_constraints,
                        "failure_classification": failure_classification,
                        "diagnostics": diagnostics,
                        "missing_formal_symbols": missing_symbols,
                        "typeclass_blockers": typeclass_blockers,
                        "recommended_repair_tasks": recommended_repair_tasks,
                        "owner_agent": "Formalizer/ProofEngineer/LeanProver",
                        "action_type": "repair_exact_source_theorem_formal_environment",
                        "required_outputs": [
                            "local Lean project or AXLE environment for the exact source theorem",
                            "Lean import list for the theorem and upstream statistical primitives",
                            "missing formal symbols or instances that must be defined before proof search",
                            "rerunnable exact-source artifact verifier manifest",
                        ],
                        "acceptance_gate": (
                            "local Lean/AXLE resolves imports and reaches the exact source theorem "
                            "declaration; artifact/source theorem proof evidence still requires "
                            "kernel verification and no sorry/admit/axiom placeholders"
                        ),
                        "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                    }
                )
    return rows


def _runtime_source_theorem_formal_environment_work_order_rows_from_learning_rows(
    learning_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Queue formal-environment repairs from exact proof-body executor feedback."""

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in learning_rows:
        if not isinstance(row, Mapping):
            continue
        input_summary = row.get("input_summary", {})
        trigger = _runtime_learning_row_trigger(row, input_summary)
        if (
            str(row.get("learning_task", "") or "")
            != "exact_source_theorem_proof_body_execution_feedback"
            and trigger not in _SOURCE_THEOREM_EXACT_CANDIDATE_REPAIR_TRIGGERS
        ):
            continue
        source_theorem_kernel_verified = bool(
            row.get("source_theorem_kernel_verified", False)
        )
        if isinstance(input_summary, Mapping):
            source_theorem_kernel_verified = bool(
                source_theorem_kernel_verified
                or input_summary.get("source_theorem_kernel_verified", False)
            )
        if source_theorem_kernel_verified:
            continue
        failure_classification = ""
        target_theorem_name = str(row.get("target_theorem_name", "") or "").strip()
        target_lean_declaration = str(
            row.get("target_lean_declaration", "")
            or row.get("expected_target_lean_declaration", "")
            or ""
        ).strip()
        candidate_artifact_path = ""
        diagnostics: list[str] = []
        missing_symbols: list[str] = []
        typeclass_blockers: list[str] = []
        recommended_repair_tasks: list[str] = []
        if isinstance(input_summary, Mapping):
            failure_classification = str(
                input_summary.get("failure_classification", "") or ""
            ).strip()
            if not target_theorem_name:
                target_theorem_name = str(
                    input_summary.get("target_theorem_name", "") or ""
                ).strip()
            if not target_lean_declaration:
                target_lean_declaration = str(
                    input_summary.get("target_lean_declaration", "")
                    or input_summary.get("expected_target_lean_declaration", "")
                    or ""
                ).strip()
            candidate_artifact_path = str(
                input_summary.get("candidate_artifact_path", "") or ""
            ).strip()
            diagnostics = [
                str(value)
                for value in input_summary.get("diagnostics", []) or []
                if str(value).strip()
            ][:8]
            missing_symbols = [
                str(value)
                for value in (
                    input_summary.get("missing_formal_symbols", [])
                    or input_summary.get("formal_environment_placeholder_symbols", [])
                    or []
                )
                if str(value).strip()
            ]
            typeclass_blockers = [
                str(value)
                for value in (
                    input_summary.get("typeclass_blockers", [])
                    or input_summary.get("formal_environment_typeclass_blockers", [])
                    or []
                )
                if str(value).strip()
            ]
            recommended_repair_tasks = [
                str(value)
                for value in input_summary.get("recommended_repair_tasks", []) or []
                if str(value).strip()
            ]
        if not target_theorem_name:
            target_theorem_name = target_lean_declaration
        source_target_provenance = _source_theorem_target_provenance_from_row(row)
        if isinstance(input_summary, Mapping):
            input_summary_provenance = _source_theorem_target_provenance_from_row(
                input_summary
            )
            for key, value in input_summary_provenance.items():
                if key not in source_target_provenance:
                    source_target_provenance[key] = value
        if target_lean_declaration and not source_target_provenance.get(
            "target_lean_declaration"
        ):
            source_target_provenance["target_lean_declaration"] = target_lean_declaration
        if bool(row.get("source_theorem_target_known", False)) or bool(
            source_target_provenance.get("source_theorem_target_known", False)
        ):
            source_target_provenance["source_theorem_target_known"] = True
        semantic_alignment_constraints = list(
            source_target_provenance.get("semantic_alignment_constraints", []) or []
        )
        if not candidate_artifact_path:
            candidate_artifact_path = str(
                row.get("candidate_artifact_path", "") or ""
            ).strip()
        if not failure_classification:
            failure_classification = str(
                row.get("failure_classification", "") or ""
            ).strip()
        if (
            failure_classification
            not in _SOURCE_THEOREM_EXACT_CANDIDATE_ENVIRONMENT_FAILURES
        ):
            continue
        context = _source_theorem_formal_environment_context(
            diagnostics=diagnostics,
            failure_classification=failure_classification,
        )
        if not missing_symbols:
            missing_symbols = context["missing_formal_symbols"]
        if not typeclass_blockers:
            typeclass_blockers = context["typeclass_blockers"]
        if not recommended_repair_tasks:
            recommended_repair_tasks = (
                _source_theorem_formal_environment_repair_tasks(
                    missing_symbols=missing_symbols,
                    typeclass_blockers=typeclass_blockers,
                    failure_classification=failure_classification,
                )
                or context["recommended_repair_tasks"]
            )
        source_learning_row_id = str(
            row.get("runtime_learning_row_id", "")
            or row.get("learning_row_id", "")
            or row.get("execution_result_id", "")
            or ""
        ).strip()
        execution_result_id = str(row.get("execution_result_id", "") or "").strip()
        execution_queue_id = str(row.get("execution_queue_id", "") or "").strip()
        work_order_id = "source_theorem_formal_environment_work_order:" + stable_hash(
            [
                source_learning_row_id,
                execution_result_id,
                execution_queue_id,
                target_theorem_name,
                candidate_artifact_path,
                failure_classification,
                diagnostics,
                source_target_provenance,
            ]
        )[:20]
        if work_order_id in seen:
            continue
        seen.add(work_order_id)
        rows.append(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": work_order_id,
                "source_learning_task": str(row.get("learning_task", "") or ""),
                "source_learning_row_id": source_learning_row_id,
                "source_execution_result_id": execution_result_id,
                "source_execution_queue_id": execution_queue_id,
                "source_work_order_id": str(row.get("source_work_order_id", "") or ""),
                "target_theorem_name": target_theorem_name,
                "target_lean_declaration": target_lean_declaration
                or target_theorem_name,
                "candidate_artifact_path": candidate_artifact_path,
                "source_theorem_target_known": bool(
                    source_target_provenance.get("source_theorem_target_known", False)
                ),
                "source_theorem_target_provenance": source_target_provenance,
                "semantic_alignment_constraints": semantic_alignment_constraints,
                "failure_classification": failure_classification,
                "diagnostics": diagnostics,
                "missing_formal_symbols": missing_symbols,
                "typeclass_blockers": typeclass_blockers,
                "recommended_repair_tasks": recommended_repair_tasks,
                "owner_agent": "Formalizer/ProofEngineer/LeanProver",
                "action_type": "repair_exact_source_theorem_formal_environment",
                "required_outputs": [
                    "local Lean project or AXLE environment for the exact source theorem",
                    "Lean import list for the theorem and upstream statistical primitives",
                    "missing formal symbols or instances that must be defined before proof search",
                    "rerunnable exact-source artifact verifier manifest",
                ],
                "acceptance_gate": (
                    "local Lean/AXLE resolves imports and reaches the exact source theorem "
                    "declaration; artifact/source theorem proof evidence still requires "
                    "kernel verification and no sorry/admit/axiom placeholders"
                ),
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            }
        )
    return rows


def _source_theorem_formal_environment_work_order_rows_from_artifact_verifier_payload(
    artifact_verifier_payload: Mapping[str, Any],
    *,
    artifact_verifier_manifest: str,
) -> list[dict[str, Any]]:
    """Queue formal-environment repair directly from exact-source verifier failures."""

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in artifact_verifier_payload.get("rows", []) or []:
        if not isinstance(row, Mapping):
            continue
        if not bool(row.get("source_theorem_target_known", False)):
            continue
        if bool(row.get("source_theorem_kernel_verified", False)):
            continue
        failure_classification = str(
            row.get("failure_classification", "") or ""
        ).strip()
        if (
            failure_classification
            not in _SOURCE_THEOREM_EXACT_CANDIDATE_ENVIRONMENT_FAILURES
        ):
            continue
        target_theorem_name = str(
            row.get("target_theorem_name", "")
            or row.get("target_lean_declaration", "")
            or ""
        ).strip()
        candidate_artifact_path = str(
            row.get("candidate_artifact_path", "") or ""
        ).strip()
        diagnostics = [
            str(value)
            for value in row.get("diagnostics", []) or []
            if str(value).strip()
        ]
        context = _source_theorem_formal_environment_context(
            diagnostics=diagnostics,
            failure_classification=failure_classification,
        )
        artifact_verification_id = str(
            row.get("artifact_verification_id", "") or ""
        ).strip()
        source_target_provenance = _source_theorem_target_provenance_from_row(row)
        source_target_provenance["source_theorem_target_known"] = True
        if artifact_verification_id and not source_target_provenance.get(
            "artifact_verification_id"
        ):
            source_target_provenance["artifact_verification_id"] = artifact_verification_id
        if artifact_verifier_manifest and not source_target_provenance.get(
            "artifact_verifier_manifest"
        ):
            source_target_provenance["artifact_verifier_manifest"] = (
                artifact_verifier_manifest
            )
        semantic_alignment_constraints = list(
            source_target_provenance.get("semantic_alignment_constraints", []) or []
        )
        work_order_id = "source_theorem_formal_environment_work_order:" + stable_hash(
            [
                artifact_verification_id,
                target_theorem_name,
                candidate_artifact_path,
                failure_classification,
                diagnostics[:8],
                source_target_provenance,
            ]
        )[:20]
        if work_order_id in seen:
            continue
        seen.add(work_order_id)
        rows.append(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": work_order_id,
                "source_formalization_manifest_id": "",
                "artifact_verification_id": artifact_verification_id,
                "artifact_verifier_manifest": artifact_verifier_manifest,
                "target_theorem_name": target_theorem_name,
                "target_lean_declaration": str(
                    source_target_provenance.get("target_lean_declaration", "")
                    or target_theorem_name
                ),
                "candidate_artifact_path": candidate_artifact_path,
                "source_theorem_target_known": True,
                "source_theorem_target_provenance": source_target_provenance,
                "semantic_alignment_constraints": semantic_alignment_constraints,
                "failure_classification": failure_classification,
                "diagnostics": diagnostics[:8],
                "missing_formal_symbols": context["missing_formal_symbols"],
                "typeclass_blockers": context["typeclass_blockers"],
                "recommended_repair_tasks": context["recommended_repair_tasks"],
                "owner_agent": "Formalizer/ProofEngineer/LeanProver",
                "action_type": "repair_exact_source_theorem_formal_environment",
                "required_outputs": [
                    "local Lean project or AXLE environment for the exact source theorem",
                    "Lean import list for the theorem and upstream statistical primitives",
                    "missing formal symbols or instances that must be defined before proof search",
                    "rerunnable exact-source artifact verifier manifest",
                ],
                "acceptance_gate": (
                    "local Lean/AXLE resolves imports and reaches the exact source theorem "
                    "declaration; artifact/source theorem proof evidence still requires "
                    "kernel verification and no sorry/admit/axiom placeholders"
                ),
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            }
        )
    return rows


def _formalizer_source_theorem_promotion_work_orders(
    *,
    proposal_packet: Mapping[str, Any],
    proof_bank_runtime_memory_summary: Mapping[str, Any],
    theorem_goals: list[Any],
) -> list[dict[str, Any]]:
    target_mode = str(
        proof_bank_runtime_memory_summary.get("recommended_formalizer_target_mode", "")
        or ""
    )
    if target_mode != "source_theorem_exact_semantics_or_theorem_promotion":
        return []
    if not proof_bank_runtime_memory_summary.get(
        "source_theorem_semantic_primitive_support_already_kernel_verified"
    ):
        return []

    target_goal_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get("remaining_theorem_goal_ids", []) or []
        if str(row).strip()
    ] or [_theorem_goal_id(row) for row in theorem_goals if _theorem_goal_id(row)]
    closure_work_order_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get(
            "memory_kernel_verified_theorem_reduction_closure_work_order_ids",
            [],
        )
        or []
        if str(row).strip()
    ]
    closure_target_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get(
            "memory_kernel_verified_theorem_reduction_closure_target_ids",
            [],
        )
        or []
        if str(row).strip()
    ]
    semantic_primitive_ids = [
        str(row).strip()
        for row in proof_bank_runtime_memory_summary.get(
            "memory_kernel_verified_source_theorem_semantic_primitive_ids",
            [],
        )
        or []
        if str(row).strip()
    ]
    source_targets = [
        row
        for row in proposal_packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
    ]
    if not source_targets:
        source_targets = [
            {
                "id": goal_id,
                "informal_source": "",
                "lean_statement_sketch": "",
                "lean_imports": [],
                "semantic_alignment_constraints": [],
            }
            for goal_id in target_goal_ids
        ]
    work_orders: list[dict[str, Any]] = []
    for target in source_targets[:8]:
        source_formal_target_id = str(target.get("id", "") or "").strip()
        if not source_formal_target_id:
            continue
        target_lean_declaration = _lean_declaration_name(
            str(target.get("lean_statement_sketch", "") or "")
        )
        source_target_provenance = _source_theorem_target_provenance_from_row(
            target
        )
        source_target_provenance.setdefault(
            "source_formalizer_packet_id",
            str(proposal_packet.get("packet_id", "") or ""),
        )
        source_target_provenance.setdefault(
            "source_formal_target_id",
            source_formal_target_id,
        )
        if len(target_goal_ids) == 1:
            source_target_provenance.setdefault(
                "source_theorem_goal_id",
                target_goal_ids[0],
            )
        if target_lean_declaration:
            source_target_provenance.setdefault(
                "target_lean_declaration",
                target_lean_declaration,
            )
            source_target_provenance["source_theorem_target_known"] = True
        semantic_alignment_constraints = list(
            source_target_provenance.get("semantic_alignment_constraints", [])
            or []
        )
        work_orders.append(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": "SourceTheoremPromotionWorkOrder",
                "work_order_id": "source_theorem_promotion_work_order:"
                + stable_hash(
                    [
                        source_formal_target_id,
                        target_goal_ids,
                        closure_work_order_ids,
                        semantic_primitive_ids,
                    ]
                )[:20],
                "source_formalizer_packet_id": str(proposal_packet.get("packet_id", "")),
                "source_formal_target_id": source_formal_target_id,
                "target_theorem_goal_ids": target_goal_ids,
                "kernel_verified_theorem_reduction_closure_work_order_ids": closure_work_order_ids,
                "kernel_verified_theorem_reduction_closure_target_ids": closure_target_ids,
                "kernel_verified_source_theorem_semantic_primitive_ids": semantic_primitive_ids,
                "lean_statement_sketch": str(target.get("lean_statement_sketch", "") or ""),
                "lean_imports": _formal_target_imports(target),
                "informal_source": str(target.get("informal_source", "") or ""),
                "source_theorem_target_known": bool(
                    source_target_provenance.get(
                        "source_theorem_target_known",
                        False,
                    )
                ),
                "source_theorem_target_provenance": source_target_provenance,
                "semantic_alignment_constraints": semantic_alignment_constraints[:8],
                "proof_mode": "source_theorem_exact_semantics_or_theorem_promotion",
                "action_type": "resolve_exact_source_theorem_target_and_attempt_promotion",
                "acceptance_gate": (
                    "AXLE/local Lean kernel verifies either exact upstream semantic definitions "
                    "or the full source theorem target. Kernel-verified bridge and closure rows "
                    "remain supporting evidence only until the source theorem itself is checked."
                ),
                "required_inputs": [
                    "exact source theorem Lean statement or paper-backed formal target",
                    "kernel-verified theorem-reduction closure manifest",
                    "kernel-verified source-semantic bridge proof-audit manifest",
                    "bounded proof artifact or source theorem patch",
                ],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            }
        )
    return work_orders


def _theorem_goal_id(row: Any) -> str:
    if isinstance(row, Mapping):
        return str(row.get("id", "") or "").strip()
    return str(getattr(row, "id", "") or "").strip()


def _formal_target_imports(target: Mapping[str, Any]) -> list[str]:
    imports = target.get("lean_imports", target.get("target_imports", []))
    if isinstance(imports, list):
        explicit_imports = [str(row).strip() for row in imports if str(row).strip()]
        if explicit_imports:
            return explicit_imports
    return _infer_formal_target_imports(target)


def _infer_formal_target_imports(target: Mapping[str, Any]) -> list[str]:
    statement = str(target.get("lean_statement_sketch", "") or "")
    source = str(target.get("informal_source", "") or "")
    text = f"{statement}\n{source}"
    mathlib_markers = (
        "MeasureTheory.",
        "MeasurableSpace",
        "IsProbabilityMeasure",
        "Nat.ceil",
        "Fin ",
        "Fin.",
        "ENNReal",
        "Set ",
        "{ω |",
        "{omega |",
    )
    if any(marker in text for marker in mathlib_markers):
        return ["Mathlib"]
    return []


def _critic_learning_rows(
    *,
    question: OpenResearchQuestion,
    agenda: list[dict[str, Any]],
    retrieval_manifest: Mapping[str, Any],
    theory_packet: Mapping[str, Any],
    simulation_manifest: Mapping[str, Any],
    algorithm_manifest: Mapping[str, Any],
    formalization_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    base = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "question_id": question.id,
        "question_title": question.title,
        "theory_packet_id": str(theory_packet.get("packet_id", "")),
        "retrieval_manifest_id": str(retrieval_manifest.get("manifest_id", "")),
        "simulation_manifest_id": str(simulation_manifest.get("manifest_id", "")),
        "algorithm_sandbox_manifest_id": str(algorithm_manifest.get("manifest_id", "")),
        "formalization_manifest_id": str(formalization_manifest.get("manifest_id", "")),
    }
    formal_subclaims = (
        formalization_manifest.get("formal_subclaims", [])
        if isinstance(formalization_manifest.get("formal_subclaims", []), list)
        else []
    )
    proof_control = (
        formalization_manifest.get("proof_obligation_control", {})
        if isinstance(formalization_manifest.get("proof_obligation_control"), Mapping)
        else {}
    )
    proof_bank_memory_summary = (
        formalization_manifest.get("proof_bank_runtime_memory_summary", {})
        if isinstance(formalization_manifest.get("proof_bank_runtime_memory_summary"), Mapping)
        else {}
    )
    selected_proof_obligation_ids = [
        str(row) for row in proof_control.get("selected_proof_obligation_ids", []) or []
    ]
    deferred_proof_obligation_ids_due_to_max = [
        str(row) for row in proof_control.get("deferred_proof_obligation_ids_due_to_max", []) or []
    ]
    deferred_priority_proof_obligation_ids_due_to_max = [
        str(row)
        for row in proof_control.get("deferred_priority_proof_obligation_ids_due_to_max", []) or []
    ]
    kernel_verified_proof_obligation_ids = [
        str(row.get("proof_obligation_id", ""))
        for row in formal_subclaims
        if isinstance(row, Mapping)
        and row.get("kernel_verified") is True
        and str(row.get("proof_obligation_id", "")).strip()
    ]
    proved_non_kernel_proof_obligation_ids = [
        str(row.get("proof_obligation_id", ""))
        for row in formal_subclaims
        if isinstance(row, Mapping)
        and row.get("status") == "PROVED"
        and row.get("kernel_verified") is not True
        and str(row.get("proof_obligation_id", "")).strip()
    ]
    failed_proof_obligation_ids = [
        str(row.get("proof_obligation_id", ""))
        for row in formal_subclaims
        if isinstance(row, Mapping)
        and row.get("status") == "FAILED"
        and str(row.get("proof_obligation_id", "")).strip()
    ]
    formal_gap_target_ids = [
        str(row.get("id", ""))
        for row in formal_subclaims
        if isinstance(row, Mapping) and row.get("status") == "FORMAL_GAP"
    ]
    kernel_verified_set = {row for row in kernel_verified_proof_obligation_ids if row}
    selected_unverified_proof_obligation_ids = [
        row for row in selected_proof_obligation_ids if row not in kernel_verified_set
    ]
    recommended_proof_obligation_ids = (
        failed_proof_obligation_ids
        or proved_non_kernel_proof_obligation_ids
        or deferred_priority_proof_obligation_ids_due_to_max
        or deferred_proof_obligation_ids_due_to_max
        or selected_unverified_proof_obligation_ids
    )
    theorem_reduction_closure_work_order_ids = [
        str(row.get("work_order_id", "") or "").strip()
        for row in formalization_manifest.get("theorem_reduction_closure_work_orders", []) or []
        if isinstance(row, Mapping) and str(row.get("work_order_id", "") or "").strip()
    ]
    rows: list[dict[str, Any]] = []
    rows.append(
        {
            **base,
            "learning_task": "retrieval_to_theory_context",
            "input_summary": {
                "retrieval_counts": retrieval_manifest.get("counts", {}),
                "theory_estimator_ids": [
                    row.get("id", "")
                    for row in theory_packet.get("estimator_specs", []) or []
                    if isinstance(row, Mapping)
                ],
            },
            "target_behavior": "use retrieval context as guidance while preserving non-proof boundary",
        }
    )
    rows.append(
        {
            **base,
            "learning_task": "simulation_algorithm_formalization_feedback",
            "input_summary": {
                "simulation_passed": simulation_manifest.get("simulation_passed"),
                "algorithm_n_executed": algorithm_manifest.get("n_executed", 0),
                "formalization_counts": formalization_manifest.get("counts", {}),
                "selected_proof_obligation_ids": selected_proof_obligation_ids,
                "selected_unverified_proof_obligation_ids": selected_unverified_proof_obligation_ids,
                "deferred_proof_obligation_ids_due_to_max": deferred_proof_obligation_ids_due_to_max,
                "deferred_priority_proof_obligation_ids_due_to_max": (
                    deferred_priority_proof_obligation_ids_due_to_max
                ),
                "kernel_verified_proof_obligation_ids": kernel_verified_proof_obligation_ids,
                "proved_non_kernel_proof_obligation_ids": proved_non_kernel_proof_obligation_ids,
                "failed_proof_obligation_ids": failed_proof_obligation_ids,
                "formal_gap_target_ids": formal_gap_target_ids,
                "recommended_proof_obligation_ids": recommended_proof_obligation_ids,
                "proof_bank_bridge_catalog_exhausted_by_memory": bool(
                    proof_bank_memory_summary.get(
                        "proof_bank_bridge_catalog_exhausted_by_memory",
                        False,
                    )
                    or proof_control.get(
                        "proof_bank_bridge_catalog_exhausted_by_memory",
                        False,
                    )
                ),
                "theorem_reduction_closure_required": bool(
                    proof_bank_memory_summary.get(
                        "theorem_reduction_closure_required",
                        False,
                    )
                    or proof_control.get("theorem_reduction_closure_required", False)
                ),
                "theorem_reduction_closure_work_order_ids": (
                    theorem_reduction_closure_work_order_ids
                ),
            },
            "selected_proof_obligation_ids": selected_proof_obligation_ids,
            "selected_unverified_proof_obligation_ids": selected_unverified_proof_obligation_ids,
            "deferred_proof_obligation_ids_due_to_max": deferred_proof_obligation_ids_due_to_max,
            "deferred_priority_proof_obligation_ids_due_to_max": (
                deferred_priority_proof_obligation_ids_due_to_max
            ),
            "kernel_verified_proof_obligation_ids": kernel_verified_proof_obligation_ids,
            "proved_non_kernel_proof_obligation_ids": proved_non_kernel_proof_obligation_ids,
            "failed_proof_obligation_ids": failed_proof_obligation_ids,
            "formal_gap_target_ids": formal_gap_target_ids,
            "recommended_proof_obligation_ids": recommended_proof_obligation_ids,
            "recommended_formalizer_target_mode": str(
                proof_bank_memory_summary.get("recommended_formalizer_target_mode", "")
                or (
                    "theorem_level_reduction_closure"
                    if proof_control.get("theorem_reduction_closure_required", False)
                    else ""
                )
            ),
            "theorem_reduction_closure_work_order_ids": theorem_reduction_closure_work_order_ids,
            "target_behavior": "route implementation gaps, formal gaps, and kernel rerun needs to the correct subsystem",
        }
    )
    for item in agenda:
        rows.append(
            {
                **base,
                "learning_task": "next_action_routing",
                "input_summary": {
                    "trigger": item.get("trigger", ""),
                    "owner_subsystem": item.get("owner_subsystem", ""),
                },
                "target_behavior": item.get("action", ""),
                "acceptance_gate": item.get("acceptance_gate", ""),
            }
        )
    return rows


def _runtime_agenda_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        artifacts = result.get("blackboard", {}).get("artifacts", {})
        if not isinstance(artifacts, Mapping):
            continue
        for artifact in artifacts.values():
            if isinstance(artifact, Mapping) and artifact.get("artifact_kind") == "RuntimeCriticEvaluatorManifest":
                for item in artifact.get("next_action_agenda", []) or []:
                    if isinstance(item, Mapping):
                        rows.append(dict(item))
    return rows


def _runtime_learning_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        artifacts = result.get("blackboard", {}).get("artifacts", {})
        if not isinstance(artifacts, Mapping):
            continue
        for artifact in artifacts.values():
            if isinstance(artifact, Mapping) and artifact.get("artifact_kind") == "RuntimeCriticEvaluatorManifest":
                for item in artifact.get("learning_rows", []) or []:
                    if isinstance(item, Mapping):
                        rows.append(dict(item))
    return rows


def _runtime_theorem_reduction_closure_work_order_rows(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_work_order_id: dict[str, int] = {}
    for result in results:
        artifacts = result.get("blackboard", {}).get("artifacts", {})
        if not isinstance(artifacts, Mapping):
            continue
        for artifact in artifacts.values():
            if not (
                isinstance(artifact, Mapping)
                and artifact.get("artifact_kind") == "RuntimeFormalizationManifest"
            ):
                continue
            question = artifact.get("question", {}) if isinstance(artifact.get("question"), Mapping) else {}
            work_order_items = list(
                artifact.get("theorem_reduction_closure_work_orders", []) or []
            )
            if not work_order_items:
                proposal_id = str(
                    artifact.get("llm_formalizer_proof_engineer_proposal_id", "")
                    or ""
                )
                proposal_packet = artifacts.get(proposal_id, {})
                if isinstance(proposal_packet, Mapping):
                    proof_bank_summary = (
                        artifact.get("proof_bank_runtime_memory_summary", {})
                        if isinstance(artifact.get("proof_bank_runtime_memory_summary"), Mapping)
                        else {}
                    )
                    theorem_goals = [
                        row
                        for row in artifact.get("deterministic_theorem_goals", []) or []
                        if isinstance(row, Mapping)
                    ]
                    work_order_items = _formalizer_theorem_reduction_closure_work_orders(
                        proposal_packet=proposal_packet,
                        proof_bank_runtime_memory_summary=proof_bank_summary,
                        theorem_goals=theorem_goals,
                    )
            for item in work_order_items:
                if not isinstance(item, Mapping):
                    continue
                row = dict(item)
                row["source_formalization_manifest_id"] = str(
                    artifact.get("manifest_id", "")
                )
                row["question_id"] = str(question.get("id", "") or "")
                row["question_title"] = str(question.get("title", "") or "")
                row["runtime_queue_status"] = "PENDING_LEAN_PROOF_ATTEMPT"
                row["runtime_queue_boundary"] = (
                    "This queue row is a proof task exported from live runtime. "
                    "It is not proof evidence until AXLE/local Lean kernel verification "
                    "accepts the theorem-level reduction."
                )
                work_order_id = str(row.get("work_order_id", "") or "").strip()
                source_manifest_id = str(row.get("source_formalization_manifest_id", "") or "")
                if work_order_id in by_work_order_id:
                    existing = rows[by_work_order_id[work_order_id]]
                    source_ids = [
                        str(value)
                        for value in existing.get("source_formalization_manifest_ids", []) or []
                        if str(value).strip()
                    ]
                    if source_manifest_id and source_manifest_id not in source_ids:
                        source_ids.append(source_manifest_id)
                    existing["source_formalization_manifest_ids"] = source_ids
                    existing["n_source_formalization_manifests"] = len(source_ids)
                    continue
                row["source_formalization_manifest_ids"] = (
                    [source_manifest_id] if source_manifest_id else []
                )
                row["n_source_formalization_manifests"] = len(
                    row["source_formalization_manifest_ids"]
                )
                if work_order_id:
                    by_work_order_id[work_order_id] = len(rows)
                rows.append(row)
    return rows


def _runtime_source_theorem_semantic_primitive_work_order_rows(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_work_order_id: dict[str, int] = {}
    for result in results:
        artifacts = result.get("blackboard", {}).get("artifacts", {})
        if not isinstance(artifacts, Mapping):
            continue
        for artifact in artifacts.values():
            if not (
                isinstance(artifact, Mapping)
                and artifact.get("artifact_kind") == "RuntimeFormalizationManifest"
            ):
                continue
            question = artifact.get("question", {}) if isinstance(artifact.get("question"), Mapping) else {}
            proposal_id = str(
                artifact.get("llm_formalizer_proof_engineer_proposal_id", "") or ""
            )
            proposal_packet = artifacts.get(proposal_id, {})
            if not isinstance(proposal_packet, Mapping):
                continue
            proof_bank_summary = (
                artifact.get("proof_bank_runtime_memory_summary", {})
                if isinstance(artifact.get("proof_bank_runtime_memory_summary"), Mapping)
                else {}
            )
            theorem_goals = [
                row
                for row in artifact.get("deterministic_theorem_goals", []) or []
                if isinstance(row, Mapping)
            ]
            work_order_items = _formalizer_source_theorem_semantic_primitive_work_orders(
                proposal_packet=proposal_packet,
                proof_bank_runtime_memory_summary=proof_bank_summary,
                theorem_goals=theorem_goals,
            )
            for item in work_order_items:
                if not isinstance(item, Mapping):
                    continue
                row = dict(item)
                row["source_formalization_manifest_id"] = str(
                    artifact.get("manifest_id", "")
                )
                row["question_id"] = str(question.get("id", "") or "")
                row["question_title"] = str(question.get("title", "") or "")
                row["runtime_queue_status"] = "PENDING_SOURCE_SEMANTIC_LEAN_PROOF_ATTEMPT"
                row["runtime_queue_boundary"] = (
                    "This queue row is an upstream source-theorem semantic primitive "
                    "proof task exported from live runtime. It is not proof evidence "
                    "until AXLE/local Lean kernel verification accepts the intended "
                    "semantic primitive."
                )
                work_order_id = str(row.get("work_order_id", "") or "").strip()
                source_manifest_id = str(row.get("source_formalization_manifest_id", "") or "")
                if work_order_id in by_work_order_id:
                    existing = rows[by_work_order_id[work_order_id]]
                    source_ids = [
                        str(value)
                        for value in existing.get("source_formalization_manifest_ids", []) or []
                        if str(value).strip()
                    ]
                    if source_manifest_id and source_manifest_id not in source_ids:
                        source_ids.append(source_manifest_id)
                    existing["source_formalization_manifest_ids"] = source_ids
                    existing["n_source_formalization_manifests"] = len(source_ids)
                    continue
                row["source_formalization_manifest_ids"] = (
                    [source_manifest_id] if source_manifest_id else []
                )
                row["n_source_formalization_manifests"] = len(
                    row["source_formalization_manifest_ids"]
                )
                if work_order_id:
                    by_work_order_id[work_order_id] = len(rows)
                rows.append(row)
    return rows


def _runtime_source_theorem_semantic_primitive_work_order_rows_from_learning_rows(
    learning_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Queue semantic primitive closure when exact candidates only typecheck via placeholders."""

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in learning_rows:
        if not isinstance(row, Mapping):
            continue
        input_summary = row.get("input_summary", {})
        trigger = _runtime_learning_row_trigger(row, input_summary)
        if (
            str(row.get("learning_task", "") or "")
            != "exact_source_theorem_proof_body_execution_feedback"
            and trigger not in _SOURCE_THEOREM_EXACT_CANDIDATE_REPAIR_TRIGGERS
        ):
            continue
        if not isinstance(input_summary, Mapping):
            continue
        source_theorem_kernel_verified = bool(
            row.get("source_theorem_kernel_verified", False)
            or input_summary.get("source_theorem_kernel_verified", False)
        )
        if source_theorem_kernel_verified:
            continue
        failure_classification = str(
            input_summary.get("failure_classification", "") or ""
        ).strip()
        if failure_classification != "formal_environment_placeholder_primitives":
            continue
        target_theorem_name = str(
            row.get("target_theorem_name", "")
            or input_summary.get("target_theorem_name", "")
            or ""
        ).strip()
        candidate_artifact_path = str(
            input_summary.get("candidate_artifact_path", "")
            or row.get("candidate_artifact_path", "")
            or ""
        ).strip()
        placeholder_symbols = [
            str(value).strip()
            for value in (
                input_summary.get("formal_environment_placeholder_symbols", [])
                or input_summary.get("missing_formal_symbols", [])
                or []
            )
            if str(value).strip()
        ]
        diagnostics = [
            str(value)
            for value in input_summary.get("diagnostics", []) or []
            if str(value).strip()
        ][:8]
        source_learning_row_id = str(
            row.get("runtime_learning_row_id", "")
            or row.get("learning_row_id", "")
            or row.get("execution_result_id", "")
            or ""
        ).strip()
        for symbol in placeholder_symbols:
            gap = _semantic_primitive_gap_for_placeholder_symbol(
                symbol,
                target_theorem_name=target_theorem_name,
            )
            kind = "source_theorem_semantic_primitives"
            primitive_id = _source_semantic_primitive_id(gap, kind)
            work_order_id = "source_theorem_semantic_primitive_work_order:" + stable_hash(
                [
                    source_learning_row_id,
                    row.get("execution_result_id", ""),
                    row.get("execution_queue_id", ""),
                    target_theorem_name,
                    symbol,
                    primitive_id,
                    candidate_artifact_path,
                ]
            )[:20]
            if work_order_id in seen:
                continue
            seen.add(work_order_id)
            rows.append(
                {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                    "work_order_id": work_order_id,
                    "semantic_primitive_id": primitive_id,
                    "semantic_primitive_gap": gap,
                    "semantic_primitive_gap_kind": kind,
                    "next_owner": "FormalizerProofEngineer",
                    "source_learning_task": str(row.get("learning_task", "") or ""),
                    "source_learning_row_id": source_learning_row_id,
                    "source_execution_result_id": str(
                        row.get("execution_result_id", "") or ""
                    ),
                    "source_execution_queue_id": str(
                        row.get("execution_queue_id", "") or ""
                    ),
                    "source_formal_environment_work_order_id": str(
                        row.get("source_work_order_id", "") or ""
                    ),
                    "target_theorem_name": target_theorem_name,
                    "candidate_artifact_path": candidate_artifact_path,
                    "placeholder_symbol": symbol,
                    "failure_classification": failure_classification,
                    "diagnostics": diagnostics,
                    "target_theorem_goal_ids": (
                        [target_theorem_name] if target_theorem_name else []
                    ),
                    "candidate_registered_obligation_ids": (
                        list(_registered_support_for_placeholder_symbol(symbol))
                    ),
                    "proof_mode": "source_theorem_semantic_primitive_closure",
                    "runtime_queue_status": "PENDING_SOURCE_SEMANTIC_LEAN_PROOF_ATTEMPT",
                    "runtime_queue_boundary": (
                        "This queue row was exported from exact source proof-body executor "
                        "feedback after placeholder formal primitives blocked source-theorem "
                        "promotion. It is not proof evidence until AXLE/local Lean kernel "
                        "verification accepts the intended semantic primitive."
                    ),
                    "acceptance_gate": (
                        "AXLE/local Lean kernel verifies the upstream semantic primitive "
                        "with no sorry, and the manifest keeps this primitive evidence "
                        "separate from signature scaffolds and full source theorem proof."
                    ),
                    "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                    "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                }
            )
    return rows


def _semantic_primitive_gap_for_placeholder_symbol(
    symbol: str,
    *,
    target_theorem_name: str,
) -> str:
    normalized = symbol.strip()
    target = f" for `{target_theorem_name}`" if target_theorem_name else ""
    if normalized == "Exchangeable":
        return (
            "Replace placeholder `Exchangeable := True` with reviewed exchangeability "
            f"semantics and its finite-rank/uniformity bridge{target}."
        )
    if normalized == "orderStat":
        return (
            "Replace placeholder `orderStat := 0` with reviewed finite-sample "
            f"order-statistic/quantile semantics{target}."
        )
    return (
        f"Replace placeholder formal primitive `{normalized}` with a reviewed "
        f"source-theorem semantic primitive{target}."
    )


def _registered_support_for_placeholder_symbol(symbol: str) -> tuple[str, ...]:
    normalized = symbol.strip()
    if normalized == "Exchangeable":
        return ("split_conformal_bad_rank_budget_from_uniform_rank_bound",)
    if normalized == "orderStat":
        return ("split_conformal_good_rank_set_inclusion_bridge",)
    return ()


def _runtime_source_theorem_promotion_work_order_rows(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_work_order_id: dict[str, int] = {}
    for result in results:
        artifacts = result.get("blackboard", {}).get("artifacts", {})
        if not isinstance(artifacts, Mapping):
            continue
        for artifact in artifacts.values():
            if not (
                isinstance(artifact, Mapping)
                and artifact.get("artifact_kind") == "RuntimeFormalizationManifest"
            ):
                continue
            question = artifact.get("question", {}) if isinstance(artifact.get("question"), Mapping) else {}
            proposal_id = str(
                artifact.get("llm_formalizer_proof_engineer_proposal_id", "") or ""
            )
            proposal_packet = artifacts.get(proposal_id, {})
            if not isinstance(proposal_packet, Mapping):
                continue
            proof_bank_summary = (
                artifact.get("proof_bank_runtime_memory_summary", {})
                if isinstance(artifact.get("proof_bank_runtime_memory_summary"), Mapping)
                else {}
            )
            theorem_goals = [
                row
                for row in artifact.get("deterministic_theorem_goals", []) or []
                if isinstance(row, Mapping)
            ]
            work_order_items = _formalizer_source_theorem_promotion_work_orders(
                proposal_packet=proposal_packet,
                proof_bank_runtime_memory_summary=proof_bank_summary,
                theorem_goals=theorem_goals,
            )
            for item in work_order_items:
                if not isinstance(item, Mapping):
                    continue
                row = dict(item)
                row["source_formalization_manifest_id"] = str(
                    artifact.get("manifest_id", "")
                )
                row["question_id"] = str(question.get("id", "") or "")
                row["question_title"] = str(question.get("title", "") or "")
                source_target_provenance = _source_theorem_target_provenance_from_row(
                    row
                )
                if row.get("source_formalization_manifest_id"):
                    source_target_provenance.setdefault(
                        "source_formalization_manifest_id",
                        str(row.get("source_formalization_manifest_id", "") or ""),
                    )
                if row.get("question_id"):
                    source_target_provenance.setdefault(
                        "question_id",
                        str(row.get("question_id", "") or ""),
                    )
                row["source_theorem_target_provenance"] = source_target_provenance
                row["source_theorem_target_known"] = bool(
                    source_target_provenance.get("source_theorem_target_known", False)
                )
                row["runtime_queue_status"] = "PENDING_SOURCE_THEOREM_TARGET_RESOLUTION_OR_PROMOTION"
                row["runtime_queue_boundary"] = (
                    "This queue row is a source-theorem promotion work order exported "
                    "from live runtime. It is not proof evidence until AXLE/local Lean "
                    "kernel verification accepts the exact source theorem or exact "
                    "upstream semantic target."
                )
                work_order_id = str(row.get("work_order_id", "") or "").strip()
                source_manifest_id = str(row.get("source_formalization_manifest_id", "") or "")
                if work_order_id in by_work_order_id:
                    existing = rows[by_work_order_id[work_order_id]]
                    source_ids = [
                        str(value)
                        for value in existing.get("source_formalization_manifest_ids", []) or []
                        if str(value).strip()
                    ]
                    if source_manifest_id and source_manifest_id not in source_ids:
                        source_ids.append(source_manifest_id)
                    existing["source_formalization_manifest_ids"] = source_ids
                    existing["n_source_formalization_manifests"] = len(source_ids)
                    existing["source_theorem_promotion_revision_count"] = len(source_ids)
                    for key in (
                        "source_formalization_manifest_id",
                        "source_formalizer_packet_id",
                        "source_formal_target_id",
                        "lean_statement_sketch",
                        "lean_imports",
                        "informal_source",
                        "source_theorem_target_known",
                        "source_theorem_target_provenance",
                        "semantic_alignment_constraints",
                    ):
                        value = row.get(key)
                        if value:
                            existing[key] = value
                    continue
                row["source_formalization_manifest_ids"] = (
                    [source_manifest_id] if source_manifest_id else []
                )
                row["n_source_formalization_manifests"] = len(
                    row["source_formalization_manifest_ids"]
                )
                if work_order_id:
                    by_work_order_id[work_order_id] = len(rows)
                rows.append(row)
    return rows


def _runtime_learning_memory_context_from_rows(
    learning_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = [dict(row) for row in learning_rows if isinstance(row, Mapping)]
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeLearningMemoryContext",
        "source_paths": [],
        "rows": rows,
        "counts": {
            "rows_loaded": len(rows),
            "source_paths": 0,
            "errors": 0,
            "max_rows": len(rows),
        },
        "errors": [],
        "boundary": (
            "Same-run runtime learning rows are orchestration memory only. "
            "They may route later proof work when they cite kernel verifier "
            "manifests, but they are not themselves theorem proof evidence."
        ),
    }


def _runtime_learning_rows_with_input_memory(
    architect_context: Mapping[str, Any] | None,
    learning_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    memory = (
        architect_context.get("runtime_learning_memory", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if (
        isinstance(memory, Mapping)
        and memory.get("artifact_kind") == "RuntimeLearningMemoryContext"
        and isinstance(memory.get("rows"), list)
    ):
        rows.extend(
            dict(row) for row in memory.get("rows", []) if isinstance(row, Mapping)
        )
    rows.extend(dict(row) for row in learning_rows if isinstance(row, Mapping))
    return rows


def _runtime_source_theorem_promotion_work_order_rows_from_learning_rows(
    results: list[dict[str, Any]],
    learning_rows: list[dict[str, Any]],
    *,
    architect_context: Mapping[str, Any] | None = None,
    source_runtime_learning_task: str,
) -> list[dict[str, Any]]:
    """Recompute source-theorem promotion readiness after same-run bridge feedback."""

    combined_learning_rows = _runtime_learning_rows_with_input_memory(
        architect_context,
        learning_rows,
    )
    memory_context = {
        "runtime_learning_memory": _runtime_learning_memory_context_from_rows(
            combined_learning_rows
        )
    }
    rows: list[dict[str, Any]] = []
    by_work_order_id: dict[str, int] = {}
    for result in results:
        artifacts = result.get("blackboard", {}).get("artifacts", {})
        if not isinstance(artifacts, Mapping):
            continue
        for artifact in artifacts.values():
            if not (
                isinstance(artifact, Mapping)
                and artifact.get("artifact_kind") == "RuntimeFormalizationManifest"
            ):
                continue
            question = (
                artifact.get("question", {})
                if isinstance(artifact.get("question"), Mapping)
                else {}
            )
            proposal_id = str(
                artifact.get("llm_formalizer_proof_engineer_proposal_id", "") or ""
            )
            proposal_packet = artifacts.get(proposal_id, {})
            if not isinstance(proposal_packet, Mapping):
                continue
            theorem_goals = [
                row
                for row in artifact.get("deterministic_theorem_goals", []) or []
                if isinstance(row, Mapping)
            ]
            proof_bank_obligation_catalog = [
                row
                for row in artifact.get("registered_proof_bank_obligation_catalog", [])
                or []
                if isinstance(row, Mapping)
            ]
            catalog_ids = tuple(
                str(row.get("obligation_id", "") or "").strip()
                for row in proof_bank_obligation_catalog
                if str(row.get("obligation_id", "") or "").strip()
            )
            memory_kernel_verified_ids = (
                _runtime_learning_memory_kernel_verified_proof_obligation_ids(
                    memory_context,
                    catalog_ids=catalog_ids,
                )
            )
            memory_prioritized_ids, _memory_off_catalog, _memory_rejected = (
                _runtime_learning_memory_proof_obligation_ids(
                    memory_context,
                    catalog_ids=catalog_ids,
                )
            )
            proof_bank_summary = _formalizer_proof_bank_runtime_memory_summary(
                context=memory_context,
                proof_bank_obligation_catalog=proof_bank_obligation_catalog,
                theorem_goals=theorem_goals,  # type: ignore[arg-type]
                memory_kernel_verified_proof_obligation_ids=memory_kernel_verified_ids,
                memory_prioritized_proof_obligation_ids=memory_prioritized_ids,
            )
            work_order_items = _formalizer_source_theorem_promotion_work_orders(
                proposal_packet=proposal_packet,
                proof_bank_runtime_memory_summary=proof_bank_summary,
                theorem_goals=theorem_goals,
            )
            for item in work_order_items:
                if not isinstance(item, Mapping):
                    continue
                row = dict(item)
                row["source_formalization_manifest_id"] = str(
                    artifact.get("manifest_id", "")
                )
                row["question_id"] = str(question.get("id", "") or "")
                row["question_title"] = str(question.get("title", "") or "")
                row["source_runtime_learning_task"] = source_runtime_learning_task
                row["same_run_post_executor_promotion"] = True
                source_target_provenance = _source_theorem_target_provenance_from_row(
                    row
                )
                if row.get("source_formalization_manifest_id"):
                    source_target_provenance.setdefault(
                        "source_formalization_manifest_id",
                        str(row.get("source_formalization_manifest_id", "") or ""),
                    )
                if row.get("question_id"):
                    source_target_provenance.setdefault(
                        "question_id",
                        str(row.get("question_id", "") or ""),
                    )
                if source_runtime_learning_task:
                    source_target_provenance.setdefault(
                        "source_runtime_learning_task",
                        source_runtime_learning_task,
                    )
                row["source_theorem_target_provenance"] = source_target_provenance
                row["source_theorem_target_known"] = bool(
                    source_target_provenance.get("source_theorem_target_known", False)
                )
                row["runtime_queue_status"] = (
                    "PENDING_SOURCE_THEOREM_TARGET_RESOLUTION_OR_PROMOTION"
                )
                row["runtime_queue_boundary"] = (
                    "This same-run queue row was derived after ProofEngineer bridge "
                    "learning memory reported kernel-verified source-semantic support. "
                    "It is not proof evidence until AXLE/local Lean verifies the exact "
                    "source theorem or exact upstream semantic target."
                )
                work_order_id = str(row.get("work_order_id", "") or "").strip()
                source_manifest_id = str(
                    row.get("source_formalization_manifest_id", "") or ""
                )
                if work_order_id in by_work_order_id:
                    existing = rows[by_work_order_id[work_order_id]]
                    source_ids = [
                        str(value)
                        for value in existing.get(
                            "source_formalization_manifest_ids", []
                        )
                        or []
                        if str(value).strip()
                    ]
                    if source_manifest_id and source_manifest_id not in source_ids:
                        source_ids.append(source_manifest_id)
                    existing["source_formalization_manifest_ids"] = source_ids
                    existing["n_source_formalization_manifests"] = len(source_ids)
                    for key in (
                        "source_formalization_manifest_id",
                        "source_formalizer_packet_id",
                        "source_formal_target_id",
                        "lean_statement_sketch",
                        "lean_imports",
                        "informal_source",
                        "source_theorem_target_known",
                        "source_theorem_target_provenance",
                        "semantic_alignment_constraints",
                    ):
                        value = row.get(key)
                        if value:
                            existing[key] = value
                    continue
                row["source_formalization_manifest_ids"] = (
                    [source_manifest_id] if source_manifest_id else []
                )
                row["n_source_formalization_manifests"] = len(
                    row["source_formalization_manifest_ids"]
                )
                if work_order_id:
                    by_work_order_id[work_order_id] = len(rows)
                rows.append(row)
    return rows


def _runtime_source_theorem_promotion_handoff_rows(
    work_order_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in work_order_rows:
        if not isinstance(item, Mapping):
            continue
        work_order_id = str(item.get("work_order_id", "") or "").strip()
        source_target_id = str(item.get("source_formal_target_id", "") or "").strip()
        lean_statement_sketch = str(item.get("lean_statement_sketch", "") or "").strip()
        target_lean_declaration = _lean_declaration_name(lean_statement_sketch)
        source_target_provenance = _source_theorem_target_provenance_from_row(item)
        if source_target_id:
            source_target_provenance.setdefault(
                "source_formal_target_id",
                source_target_id,
            )
        if target_lean_declaration:
            source_target_provenance.setdefault(
                "target_lean_declaration",
                target_lean_declaration,
            )
            source_target_provenance["source_theorem_target_known"] = True
        target_status = (
            "SOURCE_THEOREM_TARGET_SKETCH_PRESENT"
            if lean_statement_sketch
            else "NEEDS_EXACT_SOURCE_THEOREM_TARGET"
        )
        handoff_status = (
            "NEEDS_KERNEL_VERIFIED_PROOF_ARTIFACT_BEFORE_PROMOTION"
        )
        row = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeSourceTheoremPromotionHandoff",
            "handoff_id": "runtime_source_theorem_promotion_handoff:"
            + stable_hash([work_order_id, source_target_id, target_lean_declaration])[:20],
            "source_theorem_promotion_work_order_id": work_order_id,
            "source_formalization_manifest_id": str(
                item.get("source_formalization_manifest_id", "") or ""
            ),
            "source_formalizer_packet_id": str(
                item.get("source_formalizer_packet_id", "") or ""
            ),
            "question_id": str(item.get("question_id", "") or ""),
            "question_title": str(item.get("question_title", "") or ""),
            "source_formal_target_id": source_target_id,
            "target_theorem_goal_ids": list(
                item.get("target_theorem_goal_ids", []) or []
            ),
            "target_lean_declaration": target_lean_declaration,
            "source_theorem_target_known": bool(
                source_target_provenance.get("source_theorem_target_known", False)
            ),
            "source_theorem_target_provenance": source_target_provenance,
            "target_resolution_status": target_status,
            "handoff_status": handoff_status,
            "owner_agent": "Formalizer/ProofEngineer",
            "action_type": "materialize_source_theorem_proof_artifact_before_promotion",
            "kernel_verified_theorem_reduction_closure_work_order_ids": list(
                item.get("kernel_verified_theorem_reduction_closure_work_order_ids", [])
                or []
            ),
            "kernel_verified_theorem_reduction_closure_target_ids": list(
                item.get("kernel_verified_theorem_reduction_closure_target_ids", [])
                or []
            ),
            "kernel_verified_source_theorem_semantic_primitive_ids": list(
                item.get("kernel_verified_source_theorem_semantic_primitive_ids", [])
                or []
            ),
            "lean_statement_sketch": lean_statement_sketch,
            "lean_imports": list(item.get("lean_imports", []) or []),
            "semantic_alignment_constraints": list(
                item.get("semantic_alignment_constraints", []) or []
            ),
            "downstream_queue_contract": {
                "next_queue": (
                    "formal_verifier_agentic_proof_execution_materializer -> "
                    "formal_verifier_agentic_proof_execution_artifact_verifier -> "
                    "formal_verifier_agentic_proof_source_theorem_promotion_queue"
                ),
                "required_artifact_fields": [
                    "candidate_artifact_path",
                    "target_lean_declaration",
                    "artifact_kernel_verified",
                    "source_theorem_target_known or source_theorem_lean_file",
                ],
                "current_artifact_kernel_verified": False,
                "ready_for_existing_source_theorem_promotion_queue": False,
            },
            "command_plan": [
                "materialize a bounded Lean proof artifact for the source theorem target from this work order",
                "run the artifact verifier with AXLE/local Lean until artifact_kernel_verified=true",
                "feed the verified artifact row into formal_verifier_agentic_proof_source_theorem_promotion_queue",
                "promote only after the exact source theorem target passes AXLE/local Lean",
            ],
            "acceptance_gate": (
                "A downstream artifact verifier row has artifact_kernel_verified=true, "
                "then source-theorem promotion proves the exact source theorem target. "
                "Bridge/closure evidence alone is insufficient."
            ),
            "proof_evidence_status": "HANDOFF_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        }
        rows.append(row)
    return rows


def _runtime_source_theorem_promotion_materialization_seed_rows(
    handoff_rows: list[dict[str, Any]],
    *,
    runtime_out_dir: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rank, item in enumerate(handoff_rows, start=1):
        if not isinstance(item, Mapping):
            continue
        handoff_id = str(item.get("handoff_id", "") or "").strip()
        work_order_id = str(
            item.get("source_theorem_promotion_work_order_id", "") or ""
        ).strip()
        source_target_id = str(item.get("source_formal_target_id", "") or "").strip()
        target_lean_declaration = str(
            item.get("target_lean_declaration", "") or ""
        ).strip()
        target_status = str(item.get("target_resolution_status", "") or "")
        source_target_provenance = _source_theorem_target_provenance_from_row(item)
        if work_order_id:
            source_target_provenance.setdefault(
                "source_theorem_promotion_id",
                work_order_id,
            )
        if source_target_id:
            source_target_provenance.setdefault(
                "source_formal_target_id",
                source_target_id,
            )
        if target_lean_declaration:
            source_target_provenance.setdefault(
                "target_lean_declaration",
                target_lean_declaration,
            )
        target_known = (
            target_status == "SOURCE_THEOREM_TARGET_SKETCH_PRESENT"
            and bool(target_lean_declaration)
        )
        if target_known:
            source_target_provenance["source_theorem_target_known"] = True
        seed_hash = stable_hash(
            [
                handoff_id,
                work_order_id,
                source_target_id,
                target_lean_declaration,
                source_target_provenance,
            ]
        )[:16]
        execution_queue_id = (
            "runtime_source_theorem_promotion_materialization_seed:" + seed_hash
        )
        safe_name = _safe_identifier(
            target_lean_declaration or source_target_id or work_order_id or "source_theorem"
        )
        candidate_artifact_path = (
            runtime_out_dir
            / "runtime_source_theorem_promotion_candidate_artifacts"
            / f"{safe_name}_{seed_hash}.lean"
        )
        execution_transcript_path = (
            runtime_out_dir
            / "runtime_source_theorem_promotion_execution_transcripts"
            / f"{safe_name}_{seed_hash}.jsonl"
        )
        verified_closure_ids = [
            str(value)
            for value in item.get(
                "kernel_verified_theorem_reduction_closure_target_ids", []
            )
            or []
            if str(value).strip()
        ]
        verified_semantic_ids = [
            str(value)
            for value in item.get(
                "kernel_verified_source_theorem_semantic_primitive_ids", []
            )
            or []
            if str(value).strip()
        ]
        target_goal_ids = [
            str(value)
            for value in item.get("target_theorem_goal_ids", []) or []
            if str(value).strip()
        ]
        lean_statement_sketch = str(
            item.get("lean_statement_sketch", "") or ""
        ).strip()
        lean_imports = [
            str(value).strip()
            for value in item.get("lean_imports", []) or []
            if str(value).strip()
        ]
        semantic_constraints = [
            str(value)
            for value in item.get("semantic_alignment_constraints", []) or []
            if str(value).strip()
        ]
        materialization_status = (
            "READY_FOR_AGENTIC_PROOF_EXECUTION_MATERIALIZER"
            if target_known
            else "BLOCKED_NEEDS_EXACT_SOURCE_THEOREM_TARGET"
        )
        row = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeSourceTheoremPromotionMaterializationSeed",
            "materialization_seed_id": execution_queue_id,
            "execution_queue_id": execution_queue_id,
            "population_entry_id": "runtime_source_theorem_promotion:" + seed_hash,
            "safety_policy_id": "runtime_source_theorem_promotion_materialization_seed",
            "candidate_evaluation_id": "runtime_source_theorem_promotion:" + seed_hash,
            "strategy_id": "runtime_source_theorem_promotion_exact_target_attempt",
            "followup_id": handoff_id,
            "residual_obligation_id": work_order_id or source_target_id,
            "source_theorem_promotion_handoff_id": handoff_id,
            "source_theorem_promotion_work_order_id": work_order_id,
            "source_formalization_manifest_id": str(
                item.get("source_formalization_manifest_id", "") or ""
            ),
            "source_formalizer_packet_id": str(
                item.get("source_formalizer_packet_id", "") or ""
            ),
            "question_id": str(item.get("question_id", "") or ""),
            "question_title": str(item.get("question_title", "") or ""),
            "source_formal_target_id": source_target_id,
            "display_name": (
                "Materialize exact source-theorem candidate for "
                + (target_lean_declaration or source_target_id or "source theorem")
            ),
            "target_theorem_name": target_lean_declaration or source_target_id,
            "candidate_bridge_lemma_name": target_lean_declaration,
            "lean_statement_sketch": lean_statement_sketch,
            "source_theorem_target_provenance": source_target_provenance,
            "residual_gap": (
                "exact source-theorem proof artifact must be materialized and "
                "kernel verified before source-theorem promotion"
            ),
            "action_class": "materialize_source_theorem_promotion_candidate_artifact",
            "generation_mode": "runtime_source_theorem_promotion_materialization_seed",
            "source_theorem_materialization_mode": "exact_source_theorem_candidate",
            "population_bucket": "source_theorem_promotion_attempt",
            "goal_cache_key": "runtime_source_theorem_promotion:" + (
                target_lean_declaration or source_target_id or seed_hash
            ),
            "candidate_database_key": (
                "runtime_source_theorem_promotion_candidate_database:" + seed_hash
            ),
            "candidate_lineage_key": (
                "runtime_source_theorem_promotion_lineage:" + seed_hash
            ),
            "proof_sketch_population_key": (
                "runtime_source_theorem_promotion_sketch_population:" + seed_hash
            ),
            "kernel_overlay_context": {
                "source_theorem_promotion_handoff_id": handoff_id,
                "source_theorem_promotion_work_order_id": work_order_id,
                "source_formal_target_id": source_target_id,
                "source_theorem_target_known": target_known,
                "source_theorem_target_provenance": source_target_provenance,
                "target_location": {
                    "target_lean_declaration": target_lean_declaration,
                    "target_imports": lean_imports,
                },
                "already_kernel_verified_subclaims": [
                    *verified_closure_ids,
                    *verified_semantic_ids,
                ],
                "target_blockers": [
                    *target_goal_ids,
                    *semantic_constraints,
                    "exact_source_theorem_statement_alignment",
                    "artifact_kernel_verified_before_source_theorem_promotion",
                ],
                "source_theorem_boundary": (
                    "The materialized artifact must use the exact source-theorem "
                    "declaration from the Formalizer sketch. It is only proof "
                    "evidence after downstream local Lean/AXLE verification."
                ),
            },
            "candidate_artifact_path": str(candidate_artifact_path),
            "execution_transcript_path": str(execution_transcript_path),
            "target_location_preflight": {
                "live_goal_requested": True,
                "live_goal_location_ready": False,
                "execution_preflight_status": (
                    "NEEDS_MATERIALIZED_CANDIDATE_ARTIFACT"
                    if target_known
                    else "NEEDS_EXACT_SOURCE_THEOREM_TARGET"
                ),
                "target_lean_declaration": target_lean_declaration,
                "candidate_artifact_path": str(candidate_artifact_path),
                "next_step": (
                    "run formal_verifier_agentic_proof_execution_materializer on "
                    "the runtime source-theorem promotion seed queue"
                ),
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            },
            "live_goal_location_ready": False,
            "execution_preflight_status": (
                "NEEDS_MATERIALIZED_CANDIDATE_ARTIFACT"
                if target_known
                else "NEEDS_EXACT_SOURCE_THEOREM_TARGET"
            ),
            "proof_state_provider_plan": [
                "lean_goal",
                "lean_diagnostic_messages",
                "lean_local_search",
                "lean_multi_attempt",
            ],
            "proof_route_dag_plan": [
                "materialize the exact source-theorem declaration from the Formalizer sketch",
                "inspect live Lean goal before changing proof body",
                "do not promote until exact source theorem artifact is kernel verified",
            ],
            "verified_sketch_gate_plan": [
                "candidate artifact declaration matches the source theorem target",
                "artifact verifier must report artifact_kernel_verified=true before source theorem promotion",
                "source theorem integrator must reject route probes or target-as-assumption shortcuts",
            ],
            "blueprint_export_plan": [
                "label this row as proof-worker input, not proof evidence",
                "separate closure/bridge evidence from exact source theorem proof",
            ],
            "command_plan": [
                "run formal_verifier_agentic_proof_execution_materializer on the seed queue",
                "run formal_verifier_agentic_proof_execution_artifact_verifier on the materialized artifact",
                "feed only kernel-verified artifact rows into source-theorem promotion",
            ],
            "required_static_checks": [
                "candidate artifact has no sorry/admit/axiom/unsafe tokens",
                "candidate exact theorem does not restate the target as a True assumption",
                "source theorem promotion remains blocked until artifact verifier accepts",
            ],
            "required_dynamic_checks": [
                "lean_goal",
                "lean_diagnostic_messages",
                "local Lean or AXLE kernel verification",
                "source-theorem promotion queue exact-target review",
            ],
            "output_contract": [
                "write an exact-source-theorem Lean candidate artifact at candidate_artifact_path",
                "write execution transcript and live proof-state request",
                "mark proof evidence only after artifact verifier and source-theorem promotion succeed",
            ],
            "promotion_gate": (
                "source theorem promotion requires a downstream artifact verifier row "
                "with artifact_kernel_verified=true for the exact source theorem target"
            ),
            "materialization_seed_status": materialization_status,
            "execution_status": materialization_status,
            "owner_agent": "Formalizer/ProofEngineer",
            "priority_score": 95 if target_known else 10,
            "rank": rank,
            "source_theorem_target_known": target_known,
            "proof_evidence_status": "MATERIALIZATION_SEED_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            "ok": target_known,
            "errors": [] if target_known else ["target Lean declaration missing"],
        }
        rows.append(row)
    return rows


def _write_runtime_source_theorem_promotion_materialization_seed_queue(
    seed_rows: list[dict[str, Any]],
    *,
    queue_dir: Path,
) -> dict[str, Any]:
    queue_dir.mkdir(parents=True, exist_ok=True)
    ready_rows = [
        row
        for row in seed_rows
        if row.get("materialization_seed_status")
        == "READY_FOR_AGENTIC_PROOF_EXECUTION_MATERIALIZER"
    ]
    payload = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_kind": "RuntimeSourceTheoremPromotionMaterializationSeedQueue",
        "n_source_theorem_promotion_materialization_seeds": len(seed_rows),
        "n_execution_queue_items": len(ready_rows),
        "n_blocked": len(seed_rows) - len(ready_rows),
        "all_ok": all(bool(row.get("ok")) for row in seed_rows),
        "rows": ready_rows,
        "proof_evidence_status": "MATERIALIZATION_SEED_QUEUE_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "limitations": [
            "seed queue rows are materializer inputs, not proof outputs",
            "materialized route probes are still not source theorem proofs",
            "source theorem promotion remains blocked until local Lean/AXLE accepts the exact target artifact",
        ],
    }
    (queue_dir / "formal_verifier_agentic_proof_execution_queue_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (queue_dir / "formal_verifier_agentic_proof_execution_queue.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True, default=str) for row in ready_rows)
        + ("\n" if ready_rows else ""),
        encoding="utf-8",
    )
    return payload


def _run_runtime_source_theorem_promotion_proofengineer_bridge(
    *,
    seed_queue_dir: Path,
    out_dir: Path,
    local_lean: bool,
    lean_project: Path | None,
    lean_timeout: int,
    overwrite_artifacts: bool = False,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    materializer_dir = out_dir / "formal_verifier_agentic_proof_execution_materializer"
    materializer_payload = export_formal_verifier_agentic_proof_execution_materializer(
        seed_queue_dir,
        materializer_dir,
        overwrite=overwrite_artifacts,
    )
    artifact_verifier_payload: dict[str, Any] | None = None
    artifact_verifier_dir = out_dir / "formal_verifier_agentic_proof_execution_artifact_verifier"
    source_theorem_promotion_queue_payload: dict[str, Any] | None = None
    source_theorem_promotion_queue_dir = (
        out_dir / "formal_verifier_agentic_proof_source_theorem_promotion_queue"
    )
    source_theorem_integrator_payload: dict[str, Any] | None = None
    source_theorem_integrator_dir = (
        out_dir / "formal_verifier_agentic_proof_source_theorem_integrator"
    )
    if local_lean and int(materializer_payload.get("n_materializer_rows", 0) or 0) > 0:
        artifact_verifier_payload = (
            export_formal_verifier_agentic_proof_execution_artifact_verifier(
                materializer_dir,
                artifact_verifier_dir,
                lean_project=lean_project,
                lean_timeout=lean_timeout,
            )
        )
        source_theorem_promotion_queue_payload = (
            export_formal_verifier_agentic_proof_source_theorem_promotion_queue(
                artifact_verifier_dir,
                source_theorem_promotion_queue_dir,
            )
        )
        source_theorem_integrator_payload = (
            export_formal_verifier_agentic_proof_source_theorem_integrator(
                source_theorem_promotion_queue_dir,
                source_theorem_integrator_dir,
                lean_project=lean_project,
                lean_timeout=lean_timeout,
                local_lean=local_lean,
            )
        )
    artifact_verifier_manifest_path = (
        artifact_verifier_dir
        / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
    )
    source_theorem_formal_environment_work_order_rows: list[dict[str, Any]] = []
    source_theorem_formal_environment_work_order_jsonl = Path()
    source_theorem_formal_environment_work_order_manifest = Path()
    if artifact_verifier_payload is not None:
        source_theorem_formal_environment_work_order_rows = (
            _source_theorem_formal_environment_work_order_rows_from_artifact_verifier_payload(
                artifact_verifier_payload,
                artifact_verifier_manifest=str(artifact_verifier_manifest_path),
            )
        )
        source_theorem_formal_environment_work_order_dir = (
            out_dir
            / "formal_verifier_agentic_proof_source_theorem_formal_environment_work_orders"
        )
        source_theorem_formal_environment_work_order_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
        source_theorem_formal_environment_work_order_jsonl = (
            source_theorem_formal_environment_work_order_dir
            / "formal_verifier_agentic_proof_source_theorem_formal_environment_work_orders.jsonl"
        )
        source_theorem_formal_environment_work_order_manifest = (
            source_theorem_formal_environment_work_order_dir
            / "formal_verifier_agentic_proof_source_theorem_formal_environment_work_order_manifest.json"
        )
        _write_jsonl(
            source_theorem_formal_environment_work_order_jsonl,
            source_theorem_formal_environment_work_order_rows,
        )
        source_theorem_formal_environment_work_order_manifest.write_text(
            json.dumps(
                {
                    "schema_version": RUNTIME_SCHEMA_VERSION,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "artifact_kind": (
                        "SourceTheoremFormalEnvironmentWorkOrderManifest"
                    ),
                    "artifact_verifier_manifest": str(artifact_verifier_manifest_path),
                    "source_theorem_formal_environment_work_orders_jsonl": str(
                        source_theorem_formal_environment_work_order_jsonl
                    ),
                    "n_source_theorem_formal_environment_work_orders": len(
                        source_theorem_formal_environment_work_order_rows
                    ),
                    "rows": source_theorem_formal_environment_work_order_rows,
                    "proof_evidence_status": "WORK_ORDER_MANIFEST_NOT_PROOF_EVIDENCE",
                    "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
    local_lean_skipped_reason = (
        ""
        if artifact_verifier_payload is not None
        else (
            "local_lean_disabled"
            if not local_lean
            else "no_materializer_rows"
        )
    )
    bridge_manifest_path = (
        out_dir / "runtime_source_theorem_promotion_proofengineer_bridge_manifest.json"
    )
    payload = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_kind": "RuntimeSourceTheoremPromotionProofEngineerBridgeManifest",
        "seed_queue_dir": str(seed_queue_dir),
        "materializer_dir": str(materializer_dir),
        "materializer_manifest": str(
            materializer_dir
            / "formal_verifier_agentic_proof_execution_materializer_manifest.json"
        ),
        "artifact_verifier_dir": (
            str(artifact_verifier_dir) if artifact_verifier_payload is not None else ""
        ),
        "artifact_verifier_manifest": (
            str(artifact_verifier_manifest_path)
            if artifact_verifier_payload is not None
            else ""
        ),
        "source_theorem_formal_environment_work_orders_jsonl": (
            str(source_theorem_formal_environment_work_order_jsonl)
            if artifact_verifier_payload is not None
            else ""
        ),
        "source_theorem_formal_environment_work_order_manifest": (
            str(source_theorem_formal_environment_work_order_manifest)
            if artifact_verifier_payload is not None
            else ""
        ),
        "source_theorem_promotion_queue_dir": (
            str(source_theorem_promotion_queue_dir)
            if source_theorem_promotion_queue_payload is not None
            else ""
        ),
        "source_theorem_promotion_queue_manifest": (
            str(
                source_theorem_promotion_queue_dir
                / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json"
            )
            if source_theorem_promotion_queue_payload is not None
            else ""
        ),
        "source_theorem_integrator_dir": (
            str(source_theorem_integrator_dir)
            if source_theorem_integrator_payload is not None
            else ""
        ),
        "source_theorem_integrator_manifest": (
            str(
                source_theorem_integrator_dir
                / "formal_verifier_agentic_proof_source_theorem_integrator_manifest.json"
            )
            if source_theorem_integrator_payload is not None
            else ""
        ),
        "local_lean_requested": local_lean,
        "local_lean_skipped_reason": local_lean_skipped_reason,
        "overwrite_artifacts": overwrite_artifacts,
        "lean_project": str(lean_project or ""),
        "lean_timeout": lean_timeout,
        "n_materializer_rows": int(
            materializer_payload.get("n_materializer_rows", 0) or 0
        ),
        "n_materialized_artifacts": int(
            materializer_payload.get("n_materialized_artifacts", 0) or 0
        ),
        "n_live_goal_location_ready": int(
            materializer_payload.get("n_live_goal_location_ready", 0) or 0
        ),
        "n_artifact_verifier_rows": int(
            artifact_verifier_payload.get("n_verifier_rows", 0)
            if artifact_verifier_payload
            else 0
        ),
        "n_artifact_kernel_verified": int(
            artifact_verifier_payload.get("n_artifact_kernel_verified", 0)
            if artifact_verifier_payload
            else 0
        ),
        "n_source_theorem_formal_environment_work_orders": len(
            source_theorem_formal_environment_work_order_rows
        ),
        "n_source_theorem_kernel_verified": int(
            source_theorem_integrator_payload.get(
                "n_source_theorem_kernel_verified",
                0,
            )
            if source_theorem_integrator_payload
            else 0
        ),
        "n_source_theorem_integration_rows": int(
            source_theorem_integrator_payload.get("n_integration_rows", 0)
            if source_theorem_integrator_payload
            else 0
        ),
        "n_source_theorem_integration_blocked_route_probe": int(
            source_theorem_integrator_payload.get("n_blocked_route_probe", 0)
            if source_theorem_integrator_payload
            else 0
        ),
        "n_source_theorem_integration_ready_for_local_lean": int(
            source_theorem_integrator_payload.get("n_ready_for_local_lean", 0)
            if source_theorem_integrator_payload
            else 0
        ),
        "n_source_theorem_promotion_rows": int(
            source_theorem_promotion_queue_payload.get("n_promotion_rows", 0)
            if source_theorem_promotion_queue_payload
            else 0
        ),
        "n_ready_for_source_theorem_integration": int(
            source_theorem_promotion_queue_payload.get(
                "n_ready_for_source_theorem_integration",
                0,
            )
            if source_theorem_promotion_queue_payload
            else 0
        ),
        "proof_evidence_status": (
            "SOURCE_THEOREM_PROMOTION_PROOFENGINEER_BRIDGE_NOT_SOURCE_THEOREM_PROOF"
        ),
        "proof_evidence_boundary": (
            "This bridge may produce materialized route probes and local Lean "
            "artifact-kernel checks. These are not source theorem proof evidence "
            "unless a downstream row has source_theorem_kernel_verified=true for "
            "the exact source target."
        ),
        "limitations": [
            "materializer output is a route probe, not the source theorem",
            "artifact_kernel_verified is evidence for the generated artifact only",
            "source-theorem promotion remains a separate exact-target integration gate",
            "the source-theorem integrator blocks route probes and only records proof when the exact target passes Lean/AXLE",
        ],
    }
    bridge_manifest_path.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    payload["bridge_manifest"] = str(bridge_manifest_path)
    return payload


def _runtime_source_theorem_promotion_bridge_learning_rows(
    bridge_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Feed post-runtime source-theorem promotion status back into memory."""
    integrator_rows = _runtime_source_theorem_integrator_bridge_learning_rows(
        bridge_manifest
    )
    exact_candidate_rows = _runtime_source_theorem_artifact_verifier_bridge_learning_rows(
        bridge_manifest
    )
    queue_dir_value = str(
        bridge_manifest.get("source_theorem_promotion_queue_dir", "") or ""
    )
    if not queue_dir_value:
        return [*integrator_rows, *exact_candidate_rows]
    queue_dir = Path(queue_dir_value)
    queue_jsonl = (
        queue_dir / "formal_verifier_agentic_proof_source_theorem_promotion_queue.jsonl"
    )
    if not queue_jsonl.exists():
        return [*integrator_rows, *exact_candidate_rows]
    rows: list[dict[str, Any]] = [*integrator_rows, *exact_candidate_rows]
    seen_targets: set[str] = set()
    for row in rows:
        target = str(row.get("target_theorem_name", "") or "")
        if target:
            seen_targets.add(target)
    for raw_line in queue_jsonl.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, Mapping):
            continue
        promotion_status = str(row.get("promotion_status", "") or "")
        source_theorem_kernel_verified = bool(
            row.get("source_theorem_kernel_verified", False)
        )
        if (
            promotion_status != "READY_FOR_SOURCE_THEOREM_INTEGRATION"
            or source_theorem_kernel_verified
        ):
            continue
        target_theorem_name = str(row.get("target_theorem_name", "") or "")
        source_target_provenance = _source_theorem_target_provenance_from_row(row)
        if target_theorem_name:
            source_target_provenance.setdefault(
                "target_lean_declaration",
                target_theorem_name,
            )
        if row.get("source_theorem_promotion_id"):
            source_target_provenance.setdefault(
                "source_theorem_promotion_id",
                str(row.get("source_theorem_promotion_id", "") or ""),
            )
        dedupe_key = target_theorem_name or str(
            row.get("source_theorem_promotion_id", "") or ""
        )
        plain_dedupe_key = dedupe_key
        if source_target_provenance:
            dedupe_key = stable_hash([dedupe_key, source_target_provenance])
        if plain_dedupe_key in seen_targets or dedupe_key in seen_targets:
            continue
        if plain_dedupe_key:
            seen_targets.add(plain_dedupe_key)
        if dedupe_key:
            seen_targets.add(dedupe_key)
        rows.append(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "question_id": str(row.get("question_id", "") or ""),
                "question_title": str(row.get("question_title", "") or ""),
                "learning_task": "source_theorem_promotion_bridge_feedback",
                "input_summary": {
                    "trigger": "SOURCE_THEOREM_PROMOTION_READY_BUT_UNPROVED",
                    "owner_subsystem": "Formalizer/ProofEngineer",
                    "promotion_status": promotion_status,
                    "target_theorem_name": target_theorem_name,
                    "source_theorem_target_known": bool(
                        source_target_provenance.get(
                            "source_theorem_target_known",
                            False,
                        )
                        or row.get("source_theorem_target_known", False)
                    ),
                    "source_theorem_target_provenance": source_target_provenance,
                    "semantic_alignment_constraints": list(
                        source_target_provenance.get(
                            "semantic_alignment_constraints",
                            [],
                        )
                        or []
                    ),
                    "artifact_kernel_verified": bool(
                        row.get("artifact_kernel_verified", False)
                    ),
                    "source_theorem_kernel_verified": source_theorem_kernel_verified,
                },
                "target_behavior": (
                    "consume the READY_FOR_SOURCE_THEOREM_INTEGRATION row with an "
                    "exact source-theorem integration prover; do not repeat route-probe "
                    "materialization or claim theorem proof from artifact_kernel_verified"
                ),
                "acceptance_gate": (
                    "source_theorem_kernel_verified=true for "
                    + (target_theorem_name or "the exact source theorem target")
                ),
                "source_theorem_promotion_queue_manifest": str(
                    bridge_manifest.get("source_theorem_promotion_queue_manifest", "")
                    or ""
                ),
                "source_theorem_promotion_id": str(
                    row.get("source_theorem_promotion_id", "") or ""
                ),
                "target_theorem_name": target_theorem_name,
                "source_theorem_target_known": bool(
                    source_target_provenance.get(
                        "source_theorem_target_known",
                        False,
                    )
                    or row.get("source_theorem_target_known", False)
                ),
                "source_theorem_target_provenance": source_target_provenance,
                "semantic_alignment_constraints": list(
                    source_target_provenance.get(
                        "semantic_alignment_constraints",
                        [],
                    )
                    or []
                ),
                "proof_evidence_status": "SOURCE_THEOREM_PROMOTION_BRIDGE_LEARNING_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            }
        )
    return rows


def _runtime_bridge_learning_rows(
    bridge_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    learning_rows_path_value = str(
        bridge_manifest.get("runtime_learning_rows_jsonl", "") or ""
    )
    if not learning_rows_path_value:
        return []
    learning_rows_path = Path(learning_rows_path_value)
    if not learning_rows_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in learning_rows_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _runtime_source_theorem_formal_environment_bridge_learning_rows(
    bridge_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return _runtime_bridge_learning_rows(bridge_manifest)


def _runtime_source_theorem_formal_environment_proof_body_executor_learning_rows(
    executor_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    export_payload = executor_manifest.get("runtime_learning_export", {})
    if not isinstance(export_payload, Mapping):
        return []
    learning_rows_path_value = str(export_payload.get("runtime_learning_rows_jsonl", "") or "")
    if not learning_rows_path_value:
        return []
    learning_rows_path = Path(learning_rows_path_value)
    if not learning_rows_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in learning_rows_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _runtime_source_theorem_artifact_verifier_bridge_learning_rows(
    bridge_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    verifier_manifest_value = str(
        bridge_manifest.get("artifact_verifier_manifest", "") or ""
    )
    if not verifier_manifest_value:
        return []
    verifier_manifest_path = Path(verifier_manifest_value)
    if not verifier_manifest_path.exists():
        return []
    try:
        verifier_payload = json.loads(verifier_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(verifier_payload, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for row in verifier_payload.get("rows", []) or []:
        if not isinstance(row, Mapping):
            continue
        if bool(row.get("source_theorem_kernel_verified", False)):
            continue
        if not bool(row.get("source_theorem_target_known", False)):
            continue
        status = str(row.get("verification_status", "") or "")
        if status not in {
            "ARTIFACT_LOCAL_LEAN_FAILED",
            "STATIC_ARTIFACT_CHECK_FAILED",
        }:
            continue
        target_theorem_name = str(
            row.get("target_theorem_name", "")
            or row.get("target_lean_declaration", "")
            or ""
        )
        source_target_provenance = _source_theorem_target_provenance_from_row(row)
        if target_theorem_name:
            source_target_provenance.setdefault(
                "target_lean_declaration",
                target_theorem_name,
            )
        if row.get("artifact_verification_id"):
            source_target_provenance.setdefault(
                "artifact_verification_id",
                str(row.get("artifact_verification_id", "") or ""),
            )
        dedupe_key = target_theorem_name or str(row.get("materialization_id", "") or "")
        if dedupe_key in seen_targets:
            continue
        if dedupe_key:
            seen_targets.add(dedupe_key)
        trigger = (
            "SOURCE_THEOREM_EXACT_CANDIDATE_LOCAL_LEAN_FAILED"
            if status == "ARTIFACT_LOCAL_LEAN_FAILED"
            else "SOURCE_THEOREM_EXACT_CANDIDATE_STATIC_CHECK_FAILED"
        )
        diagnostics = [
            str(value)
            for value in row.get("diagnostics", []) or []
            if str(value).strip()
        ]
        failure_classification = str(row.get("failure_classification", "") or "")
        environment_context = _source_theorem_formal_environment_context(
            diagnostics=diagnostics,
            failure_classification=failure_classification,
        )
        rows.append(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "question_id": str(row.get("question_id", "") or ""),
                "question_title": str(row.get("question_title", "") or ""),
                "learning_task": "source_theorem_exact_candidate_lean_feedback",
                "input_summary": {
                    "trigger": trigger,
                    "owner_subsystem": "Formalizer/ProofEngineer",
                    "verification_status": status,
                    "target_theorem_name": target_theorem_name,
                    "target_lean_declaration": str(
                        row.get("target_lean_declaration", "") or ""
                    ),
                    "source_theorem_target_known": bool(
                        source_target_provenance.get(
                            "source_theorem_target_known",
                            False,
                        )
                        or row.get("source_theorem_target_known", False)
                    ),
                    "source_theorem_target_provenance": source_target_provenance,
                    "semantic_alignment_constraints": list(
                        source_target_provenance.get(
                            "semantic_alignment_constraints",
                            [],
                        )
                        or []
                    ),
                    "candidate_artifact_path": str(
                        row.get("candidate_artifact_path", "") or ""
                    ),
                    "local_lean_checked": bool(row.get("local_lean_checked", False)),
                    "local_lean_compiled": bool(row.get("local_lean_compiled", False)),
                    "artifact_kernel_verified": bool(
                        row.get("artifact_kernel_verified", False)
                    ),
                    "source_theorem_kernel_verified": bool(
                        row.get("source_theorem_kernel_verified", False)
                    ),
                    "diagnostics": diagnostics[:8],
                    "failure_classification": failure_classification,
                    "missing_formal_symbols": environment_context[
                        "missing_formal_symbols"
                    ],
                    "typeclass_blockers": environment_context["typeclass_blockers"],
                    "recommended_repair_tasks": environment_context[
                        "recommended_repair_tasks"
                    ],
                },
                "target_behavior": (
                    "repair the exact source-theorem candidate proof body, imports, "
                    "or formal primitives using the local Lean diagnostics; preserve "
                    "the exact declaration and do not fall back to a route probe"
                ),
                "acceptance_gate": (
                    "artifact_kernel_verified=true and then source_theorem_kernel_verified=true "
                    "for " + (target_theorem_name or "the exact source theorem target")
                ),
                "artifact_verifier_manifest": verifier_manifest_value,
                "artifact_verification_id": str(
                    row.get("artifact_verification_id", "") or ""
                ),
                "candidate_artifact_path": str(
                    row.get("candidate_artifact_path", "") or ""
                ),
                "target_theorem_name": target_theorem_name,
                "source_theorem_target_known": bool(
                    source_target_provenance.get(
                        "source_theorem_target_known",
                        False,
                    )
                    or row.get("source_theorem_target_known", False)
                ),
                "source_theorem_target_provenance": source_target_provenance,
                "semantic_alignment_constraints": list(
                    source_target_provenance.get(
                        "semantic_alignment_constraints",
                        [],
                    )
                    or []
                ),
                "proof_evidence_status": "SOURCE_THEOREM_EXACT_CANDIDATE_LEAN_FEEDBACK_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            }
        )
    return rows


def _runtime_source_theorem_integrator_bridge_learning_rows(
    bridge_manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    integrator_manifest_value = str(
        bridge_manifest.get("source_theorem_integrator_manifest", "") or ""
    )
    if not integrator_manifest_value:
        return []
    integrator_manifest_path = Path(integrator_manifest_value)
    if not integrator_manifest_path.exists():
        return []
    try:
        integrator_payload = json.loads(integrator_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(integrator_payload, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for row in integrator_payload.get("rows", []) or []:
        if not isinstance(row, Mapping):
            continue
        source_theorem_kernel_verified = bool(
            row.get("source_theorem_kernel_verified", False)
        )
        if source_theorem_kernel_verified:
            continue
        integration_status = str(row.get("integration_status", "") or "")
        if integration_status not in {
            "BLOCKED_ROUTE_PROBE_ARTIFACT",
            "BLOCKED_VACUOUS_TRUE_SOURCE_THEOREM",
            "BLOCKED_TARGET_ASSUMED_AS_HYPOTHESIS",
        }:
            continue
        target_theorem_name = str(row.get("target_theorem_name", "") or "")
        source_target_provenance = _source_theorem_target_provenance_from_row(row)
        if target_theorem_name:
            source_target_provenance.setdefault(
                "target_lean_declaration",
                target_theorem_name,
            )
        if row.get("source_theorem_promotion_id"):
            source_target_provenance.setdefault(
                "source_theorem_promotion_id",
                str(row.get("source_theorem_promotion_id", "") or ""),
            )
        dedupe_key = target_theorem_name or str(
            row.get("source_theorem_promotion_id", "") or ""
        )
        if dedupe_key in seen_targets:
            continue
        if dedupe_key:
            seen_targets.add(dedupe_key)
        trigger = (
            "SOURCE_THEOREM_INTEGRATION_BLOCKED_ROUTE_PROBE"
            if integration_status == "BLOCKED_ROUTE_PROBE_ARTIFACT"
            else "SOURCE_THEOREM_INTEGRATION_BLOCKED_VACUOUS_TRUE"
            if integration_status == "BLOCKED_VACUOUS_TRUE_SOURCE_THEOREM"
            else "SOURCE_THEOREM_INTEGRATION_BLOCKED_TARGET_ASSUMED"
        )
        rows.append(
            {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "question_id": str(row.get("question_id", "") or ""),
                "question_title": str(row.get("question_title", "") or ""),
                "learning_task": "source_theorem_integrator_blocker_feedback",
                "input_summary": {
                    "trigger": trigger,
                    "owner_subsystem": "Formalizer/ProofEngineer",
                    "integration_status": integration_status,
                    "target_theorem_name": target_theorem_name,
                    "route_probe_detected": bool(row.get("route_probe_detected", False)),
                    "vacuous_true_target_detected": bool(
                        row.get("vacuous_true_target_detected", False)
                    ),
                    "target_assumption_detected": bool(
                        row.get("target_assumption_detected", False)
                    ),
                    "source_theorem_target_known": bool(
                        source_target_provenance.get(
                            "source_theorem_target_known",
                            False,
                        )
                        or row.get("source_theorem_target_known", False)
                    ),
                    "source_theorem_target_provenance": source_target_provenance,
                    "semantic_alignment_constraints": list(
                        source_target_provenance.get(
                            "semantic_alignment_constraints",
                            [],
                        )
                        or []
                    ),
                    "source_theorem_kernel_verified": source_theorem_kernel_verified,
                },
                "target_behavior": (
                    "generate or repair a genuine non-vacuous exact source theorem "
                    "artifact for the target declaration; do not submit route probes, "
                    "vacuous True targets, or artifacts that assume the target theorem"
                ),
                "acceptance_gate": (
                    "exact source theorem artifact passes source-theorem integrator "
                    "with source_theorem_kernel_verified=true for "
                    + (target_theorem_name or "the target declaration")
                ),
                "source_theorem_integrator_manifest": integrator_manifest_value,
                "source_theorem_promotion_id": str(
                    row.get("source_theorem_promotion_id", "") or ""
                ),
                "target_theorem_name": target_theorem_name,
                "source_theorem_target_known": bool(
                    source_target_provenance.get(
                        "source_theorem_target_known",
                        False,
                    )
                    or row.get("source_theorem_target_known", False)
                ),
                "source_theorem_target_provenance": source_target_provenance,
                "semantic_alignment_constraints": list(
                    source_target_provenance.get(
                        "semantic_alignment_constraints",
                        [],
                    )
                    or []
                ),
                "proof_evidence_status": "SOURCE_THEOREM_INTEGRATOR_BLOCKER_LEARNING_NOT_PROOF_EVIDENCE",
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            }
        )
    return rows


def _lean_declaration_name(lean_statement: str) -> str:
    # Source-theorem promotion sketches often include support definitions before
    # the actual theorem. Prefer theorem/lemma declarations so the ProofEngineer
    # does not try to promote a helper `def` such as qHat as the source theorem.
    match = re.search(
        r"\b(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'.]*)",
        lean_statement,
    )
    if match:
        return match.group(1)
    match = re.search(
        r"\b(?:def|example)\s+([A-Za-z_][A-Za-z0-9_'.]*)",
        lean_statement,
    )
    return match.group(1) if match else ""


def _runtime_input_context_summary(architect_context: Mapping[str, Any]) -> dict[str, Any]:
    memory = (
        architect_context.get("runtime_learning_memory", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if not isinstance(memory, Mapping) or memory.get("artifact_kind") != "RuntimeLearningMemoryContext":
        return {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeInputContextSummary",
            "runtime_learning_memory_supplied": False,
            "runtime_learning_memory_rows_loaded": 0,
            "runtime_learning_memory_source_paths": [],
            "runtime_learning_memory_errors": 0,
            "boundary": (
                "Runtime input context is orchestration prompt memory only. "
                "It is not proof evidence, simulation evidence, execution evidence, "
                "or source authority."
            ),
        }
    counts = memory.get("counts", {}) if isinstance(memory.get("counts"), Mapping) else {}
    rows = memory.get("rows", []) if isinstance(memory.get("rows"), list) else []
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeInputContextSummary",
        "runtime_learning_memory_supplied": True,
        "runtime_learning_memory_rows_loaded": int(counts.get("rows_loaded", len(rows)) or 0),
        "runtime_learning_memory_source_paths": [
            str(path) for path in memory.get("source_paths", []) or []
        ],
        "runtime_learning_memory_errors": int(counts.get("errors", 0) or 0),
        "runtime_learning_memory_max_rows": int(counts.get("max_rows", 0) or 0),
        "boundary": (
            "Prior runtime learning rows are bounded prompt memory and orchestration "
            "guidance. They are not proof evidence, simulation evidence, execution "
            "evidence, or source authority."
        ),
    }


def _runtime_formalization_gap_planner_bridge_rows(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        artifacts = result.get("blackboard", {}).get("artifacts", {})
        if not isinstance(artifacts, Mapping):
            continue
        for artifact in artifacts.values():
            if (
                isinstance(artifact, Mapping)
                and artifact.get("artifact_kind")
                == "RuntimeFormalizationGapPlannerBridge"
            ):
                rows.append(dict(artifact))
    return rows


def _write_runtime_formalization_gap_planner_seed_files(
    bridge_rows: list[dict[str, Any]],
    *,
    seed_dir: Path,
) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    for index, bridge in enumerate(bridge_rows):
        seed = bridge.get("standalone_seed", {})
        if not isinstance(seed, Mapping):
            continue
        question = bridge.get("question", {})
        question_id = (
            str(question.get("id", "")).strip()
            if isinstance(question, Mapping)
            else ""
        )
        seed_id = str(bridge.get("standalone_seed_artifact_id", "")).strip()
        filename = (
            f"{_safe_identifier(question_id or 'question')}_"
            f"{_safe_identifier(seed_id or str(index))}.json"
        )
        seed_path = seed_dir / filename
        seed_path.write_text(json.dumps(seed, indent=2, default=str), encoding="utf-8")
        bridge["standalone_seed_path"] = str(seed_path)


def _write_runtime_formalization_gap_planner_target_intake_files(
    bridge_rows: list[dict[str, Any]],
    *,
    target_intake_dir: Path,
) -> None:
    target_intake_dir.mkdir(parents=True, exist_ok=True)
    for index, bridge in enumerate(bridge_rows):
        payload = _runtime_formalization_gap_planner_target_intake_payload(bridge)
        if not payload.get("targets"):
            continue
        question = bridge.get("question", {})
        question_id = (
            str(question.get("id", "")).strip()
            if isinstance(question, Mapping)
            else ""
        )
        bridge_id = str(bridge.get("bridge_id", "")).strip()
        filename = (
            f"{_safe_identifier(question_id or 'question')}_"
            f"{_safe_identifier(bridge_id or str(index))}.json"
        )
        target_intake_path = target_intake_dir / filename
        target_intake_path.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        bridge["target_intake_path"] = str(target_intake_path)


def _runtime_formalization_gap_planner_target_intake_payload(
    bridge: Mapping[str, Any],
) -> dict[str, Any]:
    seed = bridge.get("standalone_seed", {})
    if not isinstance(seed, Mapping):
        seed = {}
    question = bridge.get("question", {})
    if not isinstance(question, Mapping):
        question = {}
    problem = bridge.get("problem", {})
    if not isinstance(problem, Mapping):
        problem = {}
    routes = [
        dict(route)
        for route in seed.get("routes", [])
        if isinstance(route, Mapping)
    ]
    route_target_prover_families = [
        _runtime_formalization_gap_planner_route_target_prover_family(route)
        for route in routes
    ]
    unique_route_targets = tuple(
        dict.fromkeys(target for target in route_target_prover_families if target)
    )
    target_prover_family = str(
        bridge.get("target_prover_family")
        or seed.get("target_prover_family")
        or (unique_route_targets[0] if len(unique_route_targets) == 1 else "")
        or ("" if unique_route_targets else "lean4")
    )
    library_snapshot_ref = str(
        seed.get("library_snapshot_ref")
        or "ai_statistician_runtime_formalization_snapshot"
    )
    background_primitives = [
        str(primitive)
        for primitive in seed.get("background_primitives", [])
        if str(primitive).strip()
    ]
    targets = [
        _runtime_formalization_gap_planner_target_intake_target(
            route,
            question=question,
            problem=problem,
            target_prover_family=(
                _runtime_formalization_gap_planner_route_target_prover_family(
                    route,
                    fallback_target_prover_family=target_prover_family,
                )
            ),
            library_snapshot_ref=library_snapshot_ref,
            background_primitives=background_primitives,
        )
        for route in routes
    ]
    payload = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_target_intake",
        "source_component": "ai_statistician_research_agent_runtime",
        "runtime_bridge_id": str(bridge.get("bridge_id", "")),
        "standalone_seed_artifact_id": str(
            bridge.get("standalone_seed_artifact_id", "")
        ),
        "library_snapshot_ref": library_snapshot_ref,
        "domain": str(problem.get("problem_class", "")),
        "background_primitives": background_primitives,
        "targets": targets,
        "proof_evidence_status": (
            RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE
        ),
        "proof_evidence_boundary": RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY,
    }
    if target_prover_family:
        payload["target_prover_family"] = target_prover_family
    return payload


def _runtime_formalization_gap_planner_route_target_prover_family(
    route: Mapping[str, Any],
    *,
    fallback_target_prover_family: str = "",
) -> str:
    metadata = route.get("replan_metadata", {})
    metadata = metadata if isinstance(metadata, Mapping) else {}
    return str(
        route.get("target_prover_family")
        or route.get("target_prover")
        or metadata.get("target_prover_family")
        or metadata.get("target_prover")
        or fallback_target_prover_family
    ).strip()


def _runtime_formalization_gap_planner_target_intake_target(
    route: Mapping[str, Any],
    *,
    question: Mapping[str, Any],
    problem: Mapping[str, Any],
    target_prover_family: str,
    library_snapshot_ref: str,
    background_primitives: list[str],
) -> dict[str, Any]:
    source_refs = [
        str(ref)
        for ref in route.get("source_refs", [])
        if str(ref).strip()
    ]
    theorem_statement = str(route.get("theorem_statement", "")).strip()
    theorem_skeleton = str(route.get("theorem_skeleton", "")).strip()
    target_id = str(
        route.get("route_id")
        or route.get("theorem_goal_id")
        or route.get("question_id")
        or question.get("id", "")
    ).strip()
    primitive_rows = [
        dict(primitive)
        for primitive in route.get("primitives", [])
        if isinstance(primitive, Mapping)
    ]
    desired_shape = theorem_skeleton or "runtime formalization gap planner route"
    informal_steps = [
        str(step)
        for step in route.get("informal_proof_steps", [])
        if str(step).strip()
    ]
    procedure = str(problem.get("estimand") or problem.get("dgp") or "").strip()
    return {
        "target_id": target_id,
        "standalone_route_id": str(route.get("route_id", "")).strip(),
        "title": str(route.get("display_name") or question.get("title") or target_id),
        "domain": str(route.get("problem_class") or problem.get("problem_class") or ""),
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": library_snapshot_ref,
        "theorem_statement": theorem_statement,
        "theorem_skeleton": theorem_skeleton,
        "objects": background_primitives,
        "assumptions": [
            str(assumption)
            for assumption in problem.get("assumptions", [])
            if str(assumption).strip()
        ],
        "statistical_procedure": procedure,
        "desired_conclusion": theorem_statement,
        "desired_theorem_shape": desired_shape,
        "known_proof_sources": source_refs,
        "source_refs": source_refs,
        "candidate_primitives": primitive_rows,
        "informal_proof_steps": informal_steps,
        "runtime_replan_metadata": dict(route.get("replan_metadata", {}))
        if isinstance(route.get("replan_metadata"), Mapping)
        else {},
    }


def _runtime_formalization_gap_planner_handoff_rows(
    bridge_rows: list[dict[str, Any]],
    *,
    runtime_out_dir: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    handoff_root = runtime_out_dir / "runtime_formalization_gap_planner_handoffs"
    for bridge in bridge_rows:
        seed_path_text = str(bridge.get("standalone_seed_path", "")).strip()
        target_intake_path_text = str(bridge.get("target_intake_path", "")).strip()
        if not seed_path_text or not target_intake_path_text:
            continue
        seed_path = Path(seed_path_text)
        bridge_id = str(bridge.get("bridge_id", "")).strip()
        seed = bridge.get("standalone_seed", {})
        if not isinstance(seed, Mapping):
            seed = {}
        target_prover_family = str(
            bridge.get("target_prover_family") or seed.get("target_prover_family") or ""
        )
        library_snapshot_ref = str(seed.get("library_snapshot_ref", ""))
        question = bridge.get("question", {})
        question_id = (
            str(question.get("id", "")).strip()
            if isinstance(question, Mapping)
            else ""
        )
        handoff_slug = _safe_identifier(
            question_id or bridge_id or seed_path.stem or "runtime_gap_planner"
        )
        seed_arg = shlex.quote(str(seed_path))
        target_intake_arg = shlex.quote(target_intake_path_text)
        standalone_out = handoff_root / handoff_slug / "standalone_plan"
        target_intake_out = handoff_root / handoff_slug / "target_intake"
        component_resource_registry_out = (
            handoff_root / handoff_slug / "component_resource_registry"
        )
        llm_prompt_out = handoff_root / handoff_slug / "llm_route_planner_prompt"
        llm_live_out = handoff_root / handoff_slug / "llm_route_planner_live"
        reuse_smoke_out = handoff_root / handoff_slug / "reuse_smoke"
        component_resource_registry_arg = shlex.quote(
            str(component_resource_registry_out)
        )
        target_intake_dir_arg = shlex.quote(str(target_intake_out))
        standalone_plan_cli = (
            "python3 -m ai_statistician.cli formalization-gap-planner-standalone-plan "
            f"--input {seed_arg} --out {shlex.quote(str(standalone_out))}"
        )
        target_intake_cli = (
            "python3 -m ai_statistician.cli formalization-gap-planner-target-intake "
            f"--input {target_intake_arg} --out {target_intake_dir_arg}"
        )
        component_resource_registry_cli = (
            "python3 -m ai_statistician.cli "
            "formalization-gap-planner-component-resource-registry "
            f"--out {component_resource_registry_arg}"
        )
        llm_route_planner_prompt_cli = (
            "python3 -m ai_statistician.cli formalization-gap-planner-llm-route-planner "
            f"--input {seed_arg} --provider anthropic --model-tier auto "
            "--max-repair-attempts 1 "
            f"--formalization-gap-planner-target-intake-dir {target_intake_dir_arg} "
            "--formalization-gap-planner-component-resource-registry-dir "
            f"{component_resource_registry_arg} "
            f"--out {shlex.quote(str(llm_prompt_out))}"
        )
        llm_route_planner_live_cli = (
            "python3 -m ai_statistician.cli formalization-gap-planner-llm-route-planner "
            f"--input {seed_arg} --provider anthropic --model-tier auto "
            "--max-repair-attempts 1 "
            f"--formalization-gap-planner-target-intake-dir {target_intake_dir_arg} "
            "--formalization-gap-planner-component-resource-registry-dir "
            f"{component_resource_registry_arg} "
            f"--invoke-provider --out {shlex.quote(str(llm_live_out))}"
        )
        reuse_smoke_cli = (
            "python3 -m ai_statistician.cli formalization-gap-planner-reuse-smoke "
            f"--input {target_intake_arg} "
            f"--target-prover-family {shlex.quote(target_prover_family)} "
            f"--target-library-snapshot-ref {shlex.quote(library_snapshot_ref)} "
            "--llm-route-planner-provider anthropic "
            "--llm-route-planner-model-tier auto "
            "--llm-route-planner-max-repair-attempts 1 "
            "--feedback-llm-route-planner-provider anthropic "
            "--feedback-llm-route-planner-model-tier auto "
            "--feedback-llm-route-planner-max-repair-attempts 1 "
            f"--out {shlex.quote(str(reuse_smoke_out))}"
        )
        row = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeFormalizationGapPlannerHandoff",
            "handoff_id": "runtime_formalization_gap_planner_handoff:"
            + stable_hash([bridge_id, seed_path_text, standalone_plan_cli])[:20],
            "bridge_id": bridge_id,
            "question_id": question_id,
            "standalone_seed_artifact_id": str(
                bridge.get("standalone_seed_artifact_id", "")
            ),
            "standalone_seed_path": seed_path_text,
            "target_intake_path": target_intake_path_text,
            "target_prover_family": target_prover_family,
            "library_snapshot_ref": library_snapshot_ref,
            "recommended_llm_provider": "anthropic",
            "recommended_model_tier": "auto",
            "model_tier_policy": (
                "stage Anthropic prompt packets with --model-tier auto; the "
                "LLM route planner chooses Claude Haiku for small bounded "
                "routes and Claude Sonnet for residual, bridge, source-port, "
                "or new-theory routes"
            ),
            "target_intake_dir": str(target_intake_out),
            "target_intake_cli": target_intake_cli,
            "component_resource_registry_dir": str(component_resource_registry_out),
            "component_resource_registry_cli": component_resource_registry_cli,
            "standalone_plan_cli": standalone_plan_cli,
            "llm_route_planner_prompt_cli": llm_route_planner_prompt_cli,
            "llm_route_planner_live_cli": llm_route_planner_live_cli,
            "reuse_smoke_cli": reuse_smoke_cli,
            "cost_control": (
                "Use reuse_smoke_cli or llm_route_planner_prompt_cli first; "
                "they write request packets without calling the Anthropic API. "
                "Add live execution only after inspecting the staged prompts "
                "or run llm_route_planner_live_cli explicitly."
            ),
            "proof_evidence_status": (
                RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE
            ),
            "proof_evidence_boundary": RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY,
        }
        bridge["handoff_id"] = row["handoff_id"]
        bridge["standalone_plan_cli"] = standalone_plan_cli
        bridge["target_intake_dir"] = str(target_intake_out)
        bridge["target_intake_cli"] = target_intake_cli
        bridge["component_resource_registry_dir"] = str(
            component_resource_registry_out
        )
        bridge["component_resource_registry_cli"] = component_resource_registry_cli
        bridge["llm_route_planner_prompt_cli"] = llm_route_planner_prompt_cli
        bridge["llm_route_planner_live_cli"] = llm_route_planner_live_cli
        bridge["reuse_smoke_cli"] = reuse_smoke_cli
        bridge["recommended_llm_provider"] = "anthropic"
        bridge["recommended_model_tier"] = "auto"
        bridge["target_prover_family"] = row["target_prover_family"]
        rows.append(row)
    return rows


def _runtime_formalization_gap_planner_bridge(
    *,
    question: OpenResearchQuestion,
    problem: ResearchProblemSpec,
    theorem_goals: list[TheoremGoal],
    subclaims: list[FormalSubclaim],
    proof_state_rows: list[dict[str, Any]],
    retrieval_context: Mapping[str, Any],
    formalization_manifest_id: str,
    proof_state_feedback_manifest_id: str,
) -> dict[str, Any]:
    source_refs = _runtime_gap_planner_source_refs(retrieval_context)
    source_ref_rows = _runtime_gap_planner_source_ref_rows(retrieval_context)
    proof_state_by_subclaim = _runtime_proof_state_by_subclaim(proof_state_rows)
    target_prover_family = _runtime_gap_planner_target_prover_family(
        retrieval_context=retrieval_context,
        theorem_goals=theorem_goals,
        subclaims=subclaims,
        proof_state_rows=proof_state_rows,
    )
    routes = [
        _runtime_gap_planner_route(
            question=question,
            problem=problem,
            theorem_goal=goal,
            subclaims=subclaims,
            proof_state_by_subclaim=proof_state_by_subclaim,
            source_refs=source_refs,
            formalization_manifest_id=formalization_manifest_id,
            proof_state_feedback_manifest_id=proof_state_feedback_manifest_id,
            target_prover_family=target_prover_family,
        )
        for goal in theorem_goals
    ]
    seed = {
        "schema_version": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
        "component_name": FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
        "target_prover_family": target_prover_family,
        "library_snapshot_ref": "ai_statistician_runtime_formalization_snapshot",
        "source_component": "ai_statistician_research_agent_runtime",
        "question_id": question.id,
        "background_primitives": list(
            _runtime_gap_planner_background_primitives(theorem_goals)
        ),
        "routes": routes,
        "runtime_formalization_manifest_id": formalization_manifest_id,
        "proof_evidence_status": (
            RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE
        ),
        "proof_evidence_boundary": RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY,
    }
    bridge_id = "runtime_formalization_gap_planner_bridge:" + stable_hash(
        [question.id, formalization_manifest_id, seed]
    )[:20]
    standalone_seed_artifact_id = (
        "runtime_formalization_gap_planner_standalone_seed:"
        + stable_hash([bridge_id, seed])[:20]
    )
    counts = {
        "routes": len(routes),
        "primitives": sum(len(route.get("primitives", [])) for route in routes),
        "routes_with_residual_goals": sum(
            1
            for route in routes
            if route.get("replan_metadata", {}).get("residual_goals")
        ),
        "residual_goals": sum(
            len(route.get("replan_metadata", {}).get("residual_goals", []))
            for route in routes
        ),
        "exact_exists_primitives": sum(
            1
            for route in routes
            for primitive in route.get("primitives", [])
            if primitive.get("coverage_status") == "exact_exists"
        ),
        "bridge_needed_primitives": sum(
            1
            for route in routes
            for primitive in route.get("primitives", [])
            if primitive.get("coverage_status") == "bridge_needed"
        ),
        "source_port_needed_primitives": sum(
            1
            for route in routes
            for primitive in route.get("primitives", [])
            if primitive.get("coverage_status") == "source_port_needed"
        ),
        "primitives_with_candidate_declaration_rows": sum(
            1
            for route in routes
            for primitive in route.get("primitives", [])
            if primitive.get("candidate_declaration_rows")
        ),
        "candidate_declaration_rows": sum(
            len(primitive.get("candidate_declaration_rows", []) or [])
            for route in routes
            for primitive in route.get("primitives", [])
        ),
    }
    seed["runtime_bridge_id"] = bridge_id
    seed["standalone_seed_artifact_id"] = standalone_seed_artifact_id
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeFormalizationGapPlannerBridge",
        "bridge_id": bridge_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": _question_to_payload(question),
        "problem": _problem_to_json(problem),
        "formalization_manifest_id": formalization_manifest_id,
        "proof_state_feedback_manifest_id": proof_state_feedback_manifest_id,
        "target_prover_family": target_prover_family,
        "standalone_seed_artifact_id": standalone_seed_artifact_id,
        "standalone_seed": seed,
        "source_ref_rows": source_ref_rows,
        "counts": counts,
        "next_cli": (
            "python3 -m ai_statistician.cli formalization-gap-planner-standalone-plan "
            "--input <runtime_formalization_gap_planner_standalone_seed.json> "
            "--out runs/formalization_gap_planner_runtime_standalone_plan"
        ),
        "next_llm_route_planner_prompt_cli": (
            "python3 -m ai_statistician.cli formalization-gap-planner-llm-route-planner "
            "--input <runtime_formalization_gap_planner_standalone_seed.json> "
            "--provider anthropic --model-tier auto "
            "--max-repair-attempts 1 "
            "--formalization-gap-planner-target-intake-dir "
            "<runtime_formalization_gap_planner_target_intake_dir> "
            "--formalization-gap-planner-component-resource-registry-dir "
            "<runtime_formalization_gap_planner_component_resource_registry_dir> "
            "--out runs/formalization_gap_planner_runtime_llm_route_planner_prompt"
        ),
        "next_llm_route_planner_live_cli": (
            "python3 -m ai_statistician.cli formalization-gap-planner-llm-route-planner "
            "--input <runtime_formalization_gap_planner_standalone_seed.json> "
            "--provider anthropic --model-tier auto --max-repair-attempts 1 "
            "--formalization-gap-planner-target-intake-dir "
            "<runtime_formalization_gap_planner_target_intake_dir> "
            "--formalization-gap-planner-component-resource-registry-dir "
            "<runtime_formalization_gap_planner_component_resource_registry_dir> "
            "--invoke-provider "
            "--out runs/formalization_gap_planner_runtime_llm_route_planner_live"
        ),
        "next_reuse_smoke_cli": (
            "python3 -m ai_statistician.cli formalization-gap-planner-reuse-smoke "
            "--input <runtime_formalization_gap_planner_target_intake.json> "
            f"--target-prover-family {target_prover_family} "
            "--target-library-snapshot-ref ai_statistician_runtime_formalization_snapshot "
            "--llm-route-planner-provider anthropic --llm-route-planner-model-tier auto "
            "--llm-route-planner-max-repair-attempts 1 "
            "--feedback-llm-route-planner-provider anthropic "
            "--feedback-llm-route-planner-model-tier auto "
            "--feedback-llm-route-planner-max-repair-attempts 1 "
            "--out runs/formalization_gap_planner_runtime_reuse_smoke"
        ),
        "proof_evidence_status": (
            RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE
        ),
        "proof_evidence_boundary": RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY,
    }


def _runtime_gap_planner_route(
    *,
    question: OpenResearchQuestion,
    problem: ResearchProblemSpec,
    theorem_goal: TheoremGoal,
    subclaims: list[FormalSubclaim],
    proof_state_by_subclaim: Mapping[str, tuple[dict[str, Any], ...]],
    source_refs: tuple[str, ...],
    formalization_manifest_id: str,
    proof_state_feedback_manifest_id: str,
    target_prover_family: str,
) -> dict[str, Any]:
    related_subclaims = _runtime_related_subclaims(theorem_goal, subclaims)
    residual_goals = _runtime_gap_residual_goals(
        related_subclaims,
        proof_state_by_subclaim,
    )
    primitives = _runtime_gap_route_primitives(
        theorem_goal,
        related_subclaims,
        residual_goals=residual_goals,
        source_refs=source_refs,
        target_prover_family=target_prover_family,
    )
    formal_declaration_hits = _runtime_gap_formal_declaration_hits(
        related_subclaims,
        target_prover_family=target_prover_family,
    )
    route_id = (
        "runtime_gap_route:"
        + stable_hash([question.id, theorem_goal.id, formalization_manifest_id])[:20]
    )
    replan_metadata = {
        "source_component": "ai_statistician_research_agent_runtime",
        "formalization_manifest_id": formalization_manifest_id,
        "proof_state_feedback_manifest_id": proof_state_feedback_manifest_id,
        "runtime_theorem_goal_id": theorem_goal.id,
        "runtime_formal_subclaim_ids": [row.id for row in related_subclaims],
        "residual_goals": list(residual_goals),
        "source_refs": list(source_refs),
        "formal_declaration_hits": formal_declaration_hits,
        "applied_prover_attempt_statuses": _runtime_gap_attempt_statuses(
            related_subclaims,
            proof_state_by_subclaim,
        ),
        "route_revision_reasons": list(residual_goals[:8]),
        "proof_evidence_status": (
            RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE
        ),
        "proof_evidence_boundary": RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY,
    }
    if target_prover_family == "lean4":
        replan_metadata["lean_declaration_hits"] = formal_declaration_hits
    return {
        "route_id": route_id,
        "task_id": question.id,
        "question_id": question.id,
        "problem_class": problem.problem_class,
        "theorem_goal_id": theorem_goal.id,
        "display_name": theorem_goal.title,
        "theorem_statement": theorem_goal.informal_statement,
        "theorem_skeleton": _runtime_gap_theorem_skeleton(related_subclaims),
        "target_prover_family": target_prover_family,
        "informal_proof_steps": _str_tuple((theorem_goal.proof_strategy,)),
        "source_refs": list(source_refs),
        "primitives": primitives,
        "replan_metadata": replan_metadata,
        "proof_evidence_status": (
            RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE
        ),
        "proof_evidence_boundary": RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY,
    }


def _runtime_gap_route_primitives(
    theorem_goal: TheoremGoal,
    subclaims: list[FormalSubclaim],
    *,
    residual_goals: tuple[str, ...],
    source_refs: tuple[str, ...],
    target_prover_family: str,
) -> list[dict[str, Any]]:
    primitives: list[dict[str, Any]] = []
    primitive_names = _str_tuple(theorem_goal.required_primitives)
    for primitive in primitive_names:
        hits = _runtime_primitive_hits(subclaims, primitive)
        candidate_declarations = _runtime_declaration_names(hits)
        primitives.append(
            {
                "primitive": primitive,
                "coverage_status": "bridge_needed" if hits else "source_port_needed",
                "candidate_declarations": candidate_declarations,
                "candidate_declaration_rows": _runtime_declaration_rows(
                    hits,
                    fallback_declarations=candidate_declarations,
                    target_prover_family=target_prover_family,
                    source_field="runtime_primitive_formal_source_hits",
                ),
                "source_refs": list(source_refs),
                "expected_premises": list(_str_tuple(theorem_goal.proof_obligations)),
                "side_conditions": list(residual_goals[:5]),
                "next_step": (
                    "search formal library and prove a focused bridge"
                    if hits
                    else "collect source-backed theorem statement before porting"
                ),
            }
        )
    for subclaim in subclaims:
        primitive = subclaim.proof_obligation_id or subclaim.id.split(":")[-1]
        if primitive in primitive_names:
            continue
        candidate_declarations = _runtime_declaration_names(
            subclaim.formal_source_hits
        ) or ([str(subclaim.proof_obligation_id)] if subclaim.proof_obligation_id else [])
        primitives.append(
            {
                "primitive": primitive,
                "coverage_status": _runtime_subclaim_coverage_status(subclaim),
                "candidate_declarations": candidate_declarations,
                "candidate_declaration_rows": _runtime_declaration_rows(
                    subclaim.formal_source_hits,
                    fallback_declarations=candidate_declarations,
                    target_prover_family=target_prover_family,
                    source_field=(
                        "runtime_formal_source_hits"
                        if subclaim.formal_source_hits
                        else "runtime_proof_obligation_id"
                    ),
                ),
                "source_refs": list(source_refs),
                "side_conditions": list(_str_tuple([*subclaim.errors[:3], subclaim.gap_reason or ""])),
                "next_step": _runtime_subclaim_next_step(subclaim),
            }
        )
    if not primitives:
        primitives.append(
            {
                "primitive": theorem_goal.id,
                "coverage_status": (
                    "source_port_needed"
                    if theorem_goal.status == "FORMAL_GAP"
                    else "bridge_needed"
                ),
                "source_refs": list(source_refs),
                "side_conditions": list(residual_goals[:5]),
                "next_step": "build primitive coverage map from theorem goal",
            }
        )
    return primitives


def _runtime_related_subclaims(
    theorem_goal: TheoremGoal,
    subclaims: list[FormalSubclaim],
) -> list[FormalSubclaim]:
    goal_key = theorem_goal.id
    obligation_ids = set(_str_tuple(theorem_goal.proof_obligations))
    related = [
        row
        for row in subclaims
        if row.id.endswith(":" + goal_key)
        or (row.proof_obligation_id and row.proof_obligation_id in obligation_ids)
    ]
    if related:
        return related
    gap_rows = [row for row in subclaims if row.status == "FORMAL_GAP"]
    return gap_rows or subclaims


def _runtime_gap_residual_goals(
    subclaims: list[FormalSubclaim],
    proof_state_by_subclaim: Mapping[str, tuple[dict[str, Any], ...]],
) -> tuple[str, ...]:
    residuals: list[str] = []
    for subclaim in subclaims:
        residuals.extend(_str_tuple([subclaim.gap_reason or "", *subclaim.errors[:3]]))
        for row in proof_state_by_subclaim.get(subclaim.id, ()):
            residuals.extend(_str_tuple(row.get("residual_goals", [])))
            residuals.extend(_str_tuple(row.get("diagnostics", []))[:3])
    return _str_tuple(dict.fromkeys(residuals))


def _runtime_proof_state_by_subclaim(
    proof_state_rows: list[dict[str, Any]],
) -> dict[str, tuple[dict[str, Any], ...]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in proof_state_rows:
        subclaim_id = str(row.get("subclaim_id", "")).strip()
        if not subclaim_id:
            continue
        grouped.setdefault(subclaim_id, []).append(dict(row))
    return {key: tuple(value) for key, value in grouped.items()}


def _runtime_gap_theorem_skeleton(subclaims: list[FormalSubclaim]) -> str:
    for subclaim in subclaims:
        if subclaim.lean_statement:
            return str(subclaim.lean_statement)
    return ""


def _runtime_subclaim_coverage_status(subclaim: FormalSubclaim) -> str:
    if subclaim.kernel_verified:
        return "exact_exists"
    if subclaim.status == "PROVED":
        return "near_exists"
    if subclaim.formal_source_hits or subclaim.primitive_formal_source_hits:
        return "bridge_needed"
    if subclaim.status == "FAILED":
        return "bridge_needed"
    return "source_port_needed"


def _runtime_subclaim_next_step(subclaim: FormalSubclaim) -> str:
    if subclaim.kernel_verified:
        return "reuse kernel-verified proof-bank subclaim"
    if subclaim.status == "PROVED":
        return "replay or strengthen non-kernel proof-bank subclaim"
    if subclaim.formal_source_hits or subclaim.primitive_formal_source_hits:
        return "prove bridge from retrieved formal declarations"
    return "search source literature and formal library before route revision"


def _runtime_primitive_hits(
    subclaims: list[FormalSubclaim],
    primitive: str,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for subclaim in subclaims:
        hits.extend(subclaim.primitive_formal_source_hits.get(primitive, []))
    return hits


def _runtime_gap_formal_declaration_hits(
    subclaims: list[FormalSubclaim],
    *,
    target_prover_family: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for subclaim in subclaims:
        for hit in subclaim.formal_source_hits:
            rows.append(
                _runtime_gap_formal_declaration_hit_row(
                    hit,
                    target_prover_family=target_prover_family,
                    source_field="runtime_formal_source_hits",
                )
            )
        for primitive, hits in subclaim.primitive_formal_source_hits.items():
            for hit in hits:
                rows.append(
                    {
                        "primitive": primitive,
                        **_runtime_gap_formal_declaration_hit_row(
                            hit,
                            target_prover_family=target_prover_family,
                            source_field="runtime_primitive_formal_source_hits",
                        ),
                    }
                )
    return rows[:40]


def _runtime_gap_formal_declaration_hit_row(
    hit: Mapping[str, Any],
    *,
    target_prover_family: str,
    source_field: str,
) -> dict[str, Any]:
    row = dict(hit)
    declaration = ""
    for key in ("declaration", "declaration_name", "name"):
        if str(hit.get(key, "")).strip():
            declaration = str(hit.get(key, "")).strip()
            break
    if declaration:
        row["declaration"] = declaration
    row["target_prover_family"] = str(
        hit.get("target_prover_family", "")
        or hit.get("target_prover", "")
        or _target_prover_family_from_value(hit)
        or target_prover_family
    ).strip()
    row["source_field"] = str(hit.get("source_field", "") or source_field)
    return row


def _runtime_declaration_names(hits: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for hit in hits:
        for key in ("declaration", "declaration_name", "name"):
            if str(hit.get(key, "")).strip():
                names.append(str(hit.get(key, "")).strip())
    return list(dict.fromkeys(names))[:12]


def _runtime_declaration_rows(
    hits: list[dict[str, Any]],
    *,
    fallback_declarations: list[str],
    target_prover_family: str,
    source_field: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for hit in hits:
        declaration = ""
        for key in ("declaration", "declaration_name", "name"):
            if str(hit.get(key, "")).strip():
                declaration = str(hit.get(key, "")).strip()
                break
        if not declaration:
            continue
        rows.append(
            {
                "declaration": declaration,
                "target_prover_family": str(
                    hit.get("target_prover_family", "")
                    or hit.get("target_prover", "")
                    or target_prover_family
                ).strip(),
                "source_field": str(hit.get("source_field", "") or source_field),
            }
        )
    if not rows:
        rows.extend(
            {
                "declaration": declaration,
                "target_prover_family": target_prover_family,
                "source_field": source_field,
            }
            for declaration in _str_tuple(fallback_declarations)
        )
    compact: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        declaration = str(row.get("declaration", "")).strip()
        prover = str(row.get("target_prover_family", "")).strip()
        key = (declaration.casefold(), prover.casefold())
        if not declaration or key in seen:
            continue
        seen.add(key)
        compact.append(
            {
                "declaration": declaration,
                "target_prover_family": prover,
                "source_field": str(row.get("source_field", "")).strip()
                or source_field,
            }
        )
    return compact[:12]


def _runtime_gap_attempt_statuses(
    subclaims: list[FormalSubclaim],
    proof_state_by_subclaim: Mapping[str, tuple[dict[str, Any], ...]],
) -> list[str]:
    statuses: list[str] = []
    for subclaim in subclaims:
        for row in proof_state_by_subclaim.get(subclaim.id, ()):
            statuses.extend(_str_tuple(row.get("attempt_status", "")))
    return list(dict.fromkeys(statuses))[:12]


def _runtime_gap_planner_source_refs(
    retrieval_context: Mapping[str, Any],
) -> tuple[str, ...]:
    refs: list[str] = []
    for row in retrieval_context.get("paper_sources", []) or []:
        if isinstance(row, Mapping):
            refs.append(str(row.get("id", "") or row.get("source_path", "")).strip())
    for row in retrieval_context.get("knowledge_cards", []) or []:
        if isinstance(row, Mapping):
            refs.append(str(row.get("id", "") or row.get("location", "")).strip())
    return _str_tuple(dict.fromkeys(ref for ref in refs if ref))


def _runtime_gap_planner_source_ref_rows(
    retrieval_context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("paper_sources", "knowledge_cards"):
        for row in retrieval_context.get(key, []) or []:
            if isinstance(row, Mapping):
                rows.append({"source_collection": key, **dict(row)})
    return rows[:40]


def _runtime_gap_planner_target_prover_family(
    *,
    retrieval_context: Mapping[str, Any],
    theorem_goals: list[TheoremGoal],
    subclaims: list[FormalSubclaim],
    proof_state_rows: list[dict[str, Any]],
) -> str:
    explicit = _first_target_prover_family(
        retrieval_context,
        *[
            row
            for row in retrieval_context.get("formal_source_hits", []) or []
            if isinstance(row, Mapping)
        ],
        *proof_state_rows,
    )
    if explicit:
        return explicit
    for subclaim in subclaims:
        explicit = _first_target_prover_family(
            {
                "claim_type": subclaim.claim_type,
                "verifier": subclaim.verifier or "",
                "lean_statement": subclaim.lean_statement or "",
                "formal_source_hits": subclaim.formal_source_hits,
                "primitive_formal_source_hits": subclaim.primitive_formal_source_hits,
            }
        )
        if explicit:
            return explicit
    for goal in theorem_goals:
        explicit = _target_prover_family_from_text(
            " ".join(
                [
                    goal.title,
                    goal.informal_statement,
                    goal.proof_strategy,
                    " ".join(goal.required_primitives),
                    " ".join(goal.proof_obligations),
                ]
            )
        )
        if explicit:
            return explicit
    return "lean4"


def _first_target_prover_family(*values: Any) -> str:
    for value in values:
        inferred = _target_prover_family_from_value(value)
        if inferred:
            return inferred
    return ""


def _target_prover_family_from_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        for key in (
            "target_prover_family",
            "target_prover",
            "prover_family",
            "prover",
            "verifier",
            "source_type",
            "source_id",
            "claim_type",
            "path",
            "name",
            "signature",
            "lean_statement",
        ):
            text = str(value.get(key, "") or "").strip()
            inferred = _target_prover_family_from_text(text)
            if inferred:
                return inferred
        for nested_key in (
            "formal_source_hits",
            "primitive_formal_source_hits",
            "hits",
            "rows",
        ):
            inferred = _target_prover_family_from_value(value.get(nested_key))
            if inferred:
                return inferred
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            inferred = _target_prover_family_from_value(item)
            if inferred:
                return inferred
        return ""
    return _target_prover_family_from_text(str(value))


def _target_prover_family_from_text(text: str) -> str:
    lowered = str(text or "").strip().lower()
    if not lowered:
        return ""
    if any(token in lowered for token in ("rocq", "coq-lsp", "serapi", "sertop")):
        return "rocq"
    if "coq" in lowered:
        return "coq"
    if any(token in lowered for token in ("isabelle", "sledgehammer", "isabelle/hol")):
        return "isabelle"
    if "agda" in lowered:
        return "agda"
    if any(
        token in lowered
        for token in (
            "lean4",
            "lean 4",
            "lean_library",
            "lean_obligation",
            ".lean",
            "lake",
            "mathlib",
        )
    ):
        return "lean4"
    return ""


def _runtime_gap_planner_background_primitives(
    theorem_goals: list[TheoremGoal],
) -> tuple[str, ...]:
    return _str_tuple(
        dict.fromkeys(
            primitive
            for goal in theorem_goals
            for primitive in goal.required_primitives
            if primitive
        )
    )


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Mapping):
        return tuple(str(key) for key in value.keys() if str(key))
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),) if str(value) else ()


def _runtime_completion_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    counts = {
        "accepted": 0,
        "failed": 0,
        "blocked": 0,
        "max_iterations_reached": 0,
        "budget_exhausted_with_pending_next_task": 0,
        "budget_exhausted_after_revision_request": 0,
    }
    for result in results:
        traces = result.get("traces", []) if isinstance(result.get("traces"), list) else []
        final_trace = traces[-1] if traces and isinstance(traces[-1], Mapping) else {}
        first_trace = traces[0] if traces and isinstance(traces[0], Mapping) else {}
        first_task = first_trace.get("task", {}) if isinstance(first_trace.get("task"), Mapping) else {}
        first_inputs = first_task.get("inputs", {}) if isinstance(first_task.get("inputs"), Mapping) else {}
        question = first_inputs.get("question", {}) if isinstance(first_inputs.get("question"), Mapping) else {}
        status = str(result.get("status", "") or "")
        pending_next_task_id = str(final_trace.get("next_task_id", "") or "")
        failure_classification = str(final_trace.get("failure_classification", "") or "")
        last_task_id = str(final_trace.get("task_id", "") or "")
        max_iterations_reached = status == "MAX_ITERATIONS_REACHED"
        budget_exhausted_with_pending = bool(max_iterations_reached and pending_next_task_id)
        budget_exhausted_after_revision = bool(
            budget_exhausted_with_pending
            and (
                "critic" in pending_next_task_id
                or "revise" in pending_next_task_id
                or "revision" in failure_classification
                or last_task_id.startswith("theory-critic-revise:")
            )
        )
        if status == "ACCEPTED":
            terminal_kind = "accepted"
            counts["accepted"] += 1
        elif status == "FAILED":
            terminal_kind = "failed"
            counts["failed"] += 1
        elif status == "BLOCKED":
            terminal_kind = "blocked"
            counts["blocked"] += 1
        elif max_iterations_reached and pending_next_task_id:
            terminal_kind = "budget_exhausted_with_pending_next_task"
            counts["max_iterations_reached"] += 1
            counts["budget_exhausted_with_pending_next_task"] += 1
        elif max_iterations_reached:
            terminal_kind = "budget_exhausted_without_pending_next_task"
            counts["max_iterations_reached"] += 1
        else:
            terminal_kind = status.lower() or "unknown"
        if budget_exhausted_after_revision:
            counts["budget_exhausted_after_revision_request"] += 1
        rows.append(
            {
                "question_id": str(question.get("id", "") or ""),
                "question_title": str(question.get("title", "") or ""),
                "status": status,
                "terminal_kind": terminal_kind,
                "n_iterations": len(traces),
                "final_task_id": str(result.get("final_task_id", "") or ""),
                "last_completed_task_id": last_task_id,
                "last_completed_subsystem": str(final_trace.get("subsystem", "") or ""),
                "last_completed_status": str(final_trace.get("status", "") or ""),
                "last_failure_classification": failure_classification,
                "pending_next_task_id": pending_next_task_id,
                "max_iterations_reached": max_iterations_reached,
                "budget_exhausted_with_pending_next_task": budget_exhausted_with_pending,
                "budget_exhausted_after_revision_request": budget_exhausted_after_revision,
            }
        )
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeCompletionSummary",
        "n_questions": len(results),
        **counts,
        "rows": rows,
        "boundary": (
            "Runtime completion status describes orchestration progress and budget exhaustion only. "
            "It is not theorem proof evidence, simulation evidence, or a claim that remaining formal gaps are closed."
        ),
    }


def _runtime_failure_summary(completion_summary: Mapping[str, Any]) -> dict[str, Any]:
    rows = completion_summary.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    failure_rows = [
        row for row in rows
        if isinstance(row, Mapping)
        and str(row.get("terminal_kind", "") or "") in {
            "failed",
            "blocked",
        }
    ]
    incomplete_rows = [
        row for row in rows
        if isinstance(row, Mapping)
        and str(row.get("terminal_kind", "") or "") in {
            "budget_exhausted_with_pending_next_task",
            "budget_exhausted_without_pending_next_task",
        }
    ]
    first_failure = failure_rows[0] if failure_rows else {}
    first_terminal = first_failure or (incomplete_rows[0] if incomplete_rows else {})
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeFailureSummary",
        "n_failure_rows": len(failure_rows),
        "n_incomplete_rows": len(incomplete_rows),
        "has_failure": bool(failure_rows),
        "has_incomplete_pending_work": bool(incomplete_rows),
        "terminal_question_id": str(first_terminal.get("question_id", "") or ""),
        "terminal_subsystem": str(first_terminal.get("last_completed_subsystem", "") or ""),
        "terminal_task_id": str(
            first_terminal.get("last_completed_task_id", "")
            or first_terminal.get("final_task_id", "")
            or ""
        ),
        "terminal_status": str(first_terminal.get("status", "") or ""),
        "terminal_kind": str(first_terminal.get("terminal_kind", "") or ""),
        "terminal_classification": str(first_terminal.get("last_failure_classification", "") or ""),
        "failed_question_id": str(first_failure.get("question_id", "") or ""),
        "failed_subsystem": str(first_failure.get("last_completed_subsystem", "") or ""),
        "failed_task_id": str(
            first_failure.get("last_completed_task_id", "")
            or first_failure.get("final_task_id", "")
            or ""
        ),
        "failure_status": str(first_failure.get("status", "") or ""),
        "failure_terminal_kind": str(first_failure.get("terminal_kind", "") or ""),
        "failure_classification": str(first_failure.get("last_failure_classification", "") or ""),
        "pending_next_task_id": str(first_terminal.get("pending_next_task_id", "") or ""),
        "boundary": (
            "Runtime terminal status is an orchestration diagnostic. Budget exhaustion "
            "with a pending next task is incomplete work, not a subsystem failure. This "
            "summary does not downgrade kernel-verified subclaims or promote partial "
            "runtime progress to theorem proof evidence."
        ),
    }


def _runtime_evidence_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    proof = {
        "n_formalization_manifests": 0,
        "n_proved_subclaims": 0,
        "n_kernel_verified_subclaims": 0,
        "n_non_kernel_proved_subclaims": 0,
        "n_formal_gaps": 0,
        "n_failed_subclaims": 0,
        "n_formalization_gap_planner_bridges": 0,
        "n_formalization_gap_planner_routes": 0,
        "n_formalization_gap_planner_primitives": 0,
        "n_theorem_reduction_closure_work_orders": 0,
        "n_full_frontier_theorem_proved": 0,
        "has_kernel_evidence": False,
        "has_formal_gaps": False,
        "has_formalization_gap_planner_bridge": False,
        "has_theorem_reduction_closure_work_orders": False,
        "verifiers": [],
        "verification_strengths": [],
        "proof_obligation_control": {
            "configured_proof_obligation_ids": [],
            "requested_proof_obligation_ids": [],
            "memory_prioritized_proof_obligation_ids": [],
            "memory_kernel_verified_proof_obligation_ids": [],
            "memory_off_catalog_proof_obligation_ids": [],
            "memory_rejected_proof_obligation_ids": [],
            "llm_requested_proof_obligation_ids": [],
            "llm_prioritized_proof_obligation_ids": [],
            "llm_suppressed_kernel_verified_proof_obligation_ids": [],
            "llm_off_catalog_proof_obligation_ids": [],
            "llm_rejected_proof_obligation_ids": [],
            "prioritized_proof_obligation_ids": [],
            "max_proof_obligations": 0,
            "n_registered_proof_bank_obligation_candidates": 0,
            "n_candidate_proof_obligations": 0,
            "n_selected_proof_obligations": 0,
            "selected_proof_obligation_ids": [],
            "selected_priority_proof_obligation_ids": [],
            "eligible_proof_obligation_ids_before_limit": [],
            "excluded_proof_obligation_ids": [],
            "excluded_candidate_proof_obligation_ids": [],
            "deferred_proof_obligation_ids_due_to_max": [],
            "deferred_priority_proof_obligation_ids_due_to_max": [],
            "remaining_unverified_proof_bank_obligation_ids": [],
            "proof_bank_bridge_catalog_exhausted_by_memory": False,
            "theorem_reduction_closure_required": False,
            "theorem_reduction_closure_already_kernel_verified": False,
            "memory_kernel_verified_theorem_reduction_closure_work_order_ids": [],
            "memory_kernel_verified_theorem_reduction_closure_target_ids": [],
            "memory_kernel_verified_theorem_reduction_closure_goal_ids": [],
            "memory_kernel_verified_source_theorem_semantic_primitive_ids": [],
            "source_theorem_semantic_primitive_support_already_kernel_verified": False,
            "selection_boundary": (
                "Proof-obligation controls limit registered proof-bank subclaim verification only. "
                "They do not remove frontier formal gaps and do not prove the full theorem."
            ),
        },
        "boundary": KERNEL_PROOF_BOUNDARY,
    }
    simulation = {
        "n_simulation_manifests": 0,
        "n_simulation_rows": 0,
        "n_simulation_manifests_passed": 0,
        "boundary": SIMULATION_NOT_PROOF_BOUNDARY,
    }
    algorithm = {
        "n_algorithm_manifests": 0,
        "n_algorithm_sandbox_prototypes": 0,
        "n_algorithm_sandbox_executed": 0,
        "n_algorithm_sandbox_passed": 0,
        "n_generated_code_sandbox_executed": 0,
        "n_unsafe_generated_code_rejected": 0,
        "promotion_ready": False,
        "boundary": (
            "Algorithm sandbox summaries are implementation evidence only; "
            "they are not production registration or theorem proof evidence."
        ),
    }
    verifier_names: set[str] = set()
    strengths: set[str] = set()
    for result in results:
        artifacts = result.get("blackboard", {}).get("artifacts", {})
        if not isinstance(artifacts, Mapping):
            continue
        for artifact in artifacts.values():
            if not isinstance(artifact, Mapping):
                continue
            kind = str(artifact.get("artifact_kind", ""))
            if kind == "RuntimeFormalizationManifest":
                counts = artifact.get("counts", {}) if isinstance(artifact.get("counts"), Mapping) else {}
                proof["n_formalization_manifests"] += 1
                proof["n_proved_subclaims"] += int(counts.get("proved", 0) or 0)
                proof["n_kernel_verified_subclaims"] += int(counts.get("kernel_verified", 0) or 0)
                proof["n_formal_gaps"] += int(counts.get("formal_gap", 0) or 0)
                proof["n_failed_subclaims"] += int(counts.get("failed", 0) or 0)
                proof["n_theorem_reduction_closure_work_orders"] += len(
                    artifact.get("theorem_reduction_closure_work_orders", []) or []
                )
                if artifact.get("full_frontier_theorem_proved") is True:
                    proof["n_full_frontier_theorem_proved"] += 1
                control = (
                    artifact.get("proof_obligation_control", {})
                    if isinstance(artifact.get("proof_obligation_control"), Mapping)
                    else {}
                )
                proof_control = proof["proof_obligation_control"]
                proof_control["max_proof_obligations"] = max(
                    int(proof_control.get("max_proof_obligations", 0) or 0),
                    int(control.get("max_proof_obligations", 0) or 0),
                )
                proof_control["n_candidate_proof_obligations"] += int(
                    control.get("n_candidate_proof_obligations", 0) or 0
                )
                proof_control["n_registered_proof_bank_obligation_candidates"] += len(
                    artifact.get("registered_proof_bank_obligation_catalog", []) or []
                )
                proof_control["n_selected_proof_obligations"] += int(
                    control.get("n_selected_proof_obligations", 0) or 0
                )
                proof_control["requested_proof_obligation_ids"] = sorted(
                    set(proof_control.get("requested_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("requested_proof_obligation_ids", []) or []}
                )
                proof_control["configured_proof_obligation_ids"] = sorted(
                    set(proof_control.get("configured_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("configured_proof_obligation_ids", []) or []}
                )
                proof_control["memory_prioritized_proof_obligation_ids"] = sorted(
                    set(proof_control.get("memory_prioritized_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("memory_prioritized_proof_obligation_ids", []) or []}
                )
                proof_control["memory_kernel_verified_proof_obligation_ids"] = sorted(
                    set(proof_control.get("memory_kernel_verified_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("memory_kernel_verified_proof_obligation_ids", []) or []}
                )
                proof_control["memory_off_catalog_proof_obligation_ids"] = sorted(
                    set(proof_control.get("memory_off_catalog_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("memory_off_catalog_proof_obligation_ids", []) or []}
                )
                proof_control["memory_rejected_proof_obligation_ids"] = sorted(
                    set(proof_control.get("memory_rejected_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("memory_rejected_proof_obligation_ids", []) or []}
                )
                proof_control["llm_requested_proof_obligation_ids"] = sorted(
                    set(proof_control.get("llm_requested_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("llm_requested_proof_obligation_ids", []) or []}
                )
                proof_control["llm_prioritized_proof_obligation_ids"] = sorted(
                    set(proof_control.get("llm_prioritized_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("llm_prioritized_proof_obligation_ids", []) or []}
                )
                proof_control["llm_suppressed_kernel_verified_proof_obligation_ids"] = sorted(
                    set(
                        proof_control.get(
                            "llm_suppressed_kernel_verified_proof_obligation_ids",
                            [],
                        )
                        or []
                    )
                    | {
                        str(row)
                        for row in control.get(
                            "llm_suppressed_kernel_verified_proof_obligation_ids",
                            [],
                        )
                        or []
                    }
                )
                proof_control["llm_off_catalog_proof_obligation_ids"] = sorted(
                    set(proof_control.get("llm_off_catalog_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("llm_off_catalog_proof_obligation_ids", []) or []}
                )
                proof_control["llm_rejected_proof_obligation_ids"] = sorted(
                    set(proof_control.get("llm_rejected_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("llm_rejected_proof_obligation_ids", []) or []}
                )
                proof_control["prioritized_proof_obligation_ids"] = sorted(
                    set(proof_control.get("prioritized_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("prioritized_proof_obligation_ids", []) or []}
                )
                proof_control["selected_proof_obligation_ids"] = sorted(
                    set(proof_control.get("selected_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("selected_proof_obligation_ids", []) or []}
                )
                proof_control["selected_priority_proof_obligation_ids"] = sorted(
                    set(proof_control.get("selected_priority_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("selected_priority_proof_obligation_ids", []) or []}
                )
                proof_control["eligible_proof_obligation_ids_before_limit"] = sorted(
                    set(proof_control.get("eligible_proof_obligation_ids_before_limit", []) or [])
                    | {str(row) for row in control.get("eligible_proof_obligation_ids_before_limit", []) or []}
                )
                proof_control["excluded_proof_obligation_ids"] = sorted(
                    set(proof_control.get("excluded_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("excluded_proof_obligation_ids", []) or []}
                )
                proof_control["excluded_candidate_proof_obligation_ids"] = sorted(
                    set(proof_control.get("excluded_candidate_proof_obligation_ids", []) or [])
                    | {str(row) for row in control.get("excluded_candidate_proof_obligation_ids", []) or []}
                )
                proof_control["deferred_proof_obligation_ids_due_to_max"] = sorted(
                    set(proof_control.get("deferred_proof_obligation_ids_due_to_max", []) or [])
                    | {str(row) for row in control.get("deferred_proof_obligation_ids_due_to_max", []) or []}
                )
                proof_control["deferred_priority_proof_obligation_ids_due_to_max"] = sorted(
                    set(proof_control.get("deferred_priority_proof_obligation_ids_due_to_max", []) or [])
                    | {
                        str(row)
                        for row in control.get("deferred_priority_proof_obligation_ids_due_to_max", []) or []
                    }
                )
                proof_control["remaining_unverified_proof_bank_obligation_ids"] = sorted(
                    set(proof_control.get("remaining_unverified_proof_bank_obligation_ids", []) or [])
                    | {
                        str(row)
                        for row in control.get("remaining_unverified_proof_bank_obligation_ids", []) or []
                    }
                )
                proof_control["proof_bank_bridge_catalog_exhausted_by_memory"] = bool(
                    proof_control.get("proof_bank_bridge_catalog_exhausted_by_memory", False)
                    or control.get("proof_bank_bridge_catalog_exhausted_by_memory", False)
                )
                proof_control["theorem_reduction_closure_required"] = bool(
                    proof_control.get("theorem_reduction_closure_required", False)
                    or control.get("theorem_reduction_closure_required", False)
                )
                proof_control["theorem_reduction_closure_already_kernel_verified"] = bool(
                    proof_control.get(
                        "theorem_reduction_closure_already_kernel_verified",
                        False,
                    )
                    or control.get(
                        "theorem_reduction_closure_already_kernel_verified",
                        False,
                    )
                )
                for key in (
                    "memory_kernel_verified_theorem_reduction_closure_work_order_ids",
                    "memory_kernel_verified_theorem_reduction_closure_target_ids",
                    "memory_kernel_verified_theorem_reduction_closure_goal_ids",
                    "memory_kernel_verified_source_theorem_semantic_primitive_ids",
                ):
                    proof_control[key] = sorted(
                        set(proof_control.get(key, []) or [])
                        | {str(row) for row in control.get(key, []) or []}
                    )
                proof_control[
                    "source_theorem_semantic_primitive_support_already_kernel_verified"
                ] = bool(
                    proof_control.get(
                        "source_theorem_semantic_primitive_support_already_kernel_verified",
                        False,
                    )
                    or control.get(
                        "source_theorem_semantic_primitive_support_already_kernel_verified",
                        False,
                    )
                )
                for verifier in artifact.get("verifiers", []) or []:
                    if str(verifier).strip():
                        verifier_names.add(str(verifier))
                for row in artifact.get("formal_subclaims", []) or []:
                    if not isinstance(row, Mapping):
                        continue
                    if str(row.get("claim_type", "")) != "lean_obligation":
                        continue
                    strength = str(row.get("verification_strength", "") or "")
                    if strength:
                        strengths.add(strength)
            elif kind == "RuntimeFormalizationGapPlannerBridge":
                counts = artifact.get("counts", {}) if isinstance(artifact.get("counts"), Mapping) else {}
                proof["n_formalization_gap_planner_bridges"] += 1
                proof["n_formalization_gap_planner_routes"] += int(
                    counts.get("routes", 0) or 0
                )
                proof["n_formalization_gap_planner_primitives"] += int(
                    counts.get("primitives", 0) or 0
                )
            elif kind == "RuntimeSimulationManifest":
                simulation["n_simulation_manifests"] += 1
                simulation["n_simulation_rows"] += len(artifact.get("simulations", []) or [])
                if artifact.get("simulation_passed") is True:
                    simulation["n_simulation_manifests_passed"] += 1
            elif kind == "RuntimeAlgorithmSandboxManifest":
                algorithm["n_algorithm_manifests"] += 1
                algorithm["n_algorithm_sandbox_prototypes"] += int(artifact.get("n_prototypes", 0) or 0)
                algorithm["n_algorithm_sandbox_executed"] += int(artifact.get("n_executed", 0) or 0)
                algorithm["n_algorithm_sandbox_passed"] += int(artifact.get("n_passed", 0) or 0)
                algorithm["n_generated_code_sandbox_executed"] += int(
                    artifact.get("n_generated_code_executed", 0) or 0
                )
                algorithm["n_unsafe_generated_code_rejected"] += int(
                    artifact.get("n_unsafe_generated_code_rejected", 0) or 0
                )
                algorithm["promotion_ready"] = bool(algorithm["promotion_ready"] or artifact.get("promotion_ready"))
    proof["n_non_kernel_proved_subclaims"] = max(
        0,
        int(proof["n_proved_subclaims"]) - int(proof["n_kernel_verified_subclaims"]),
    )
    proof["has_kernel_evidence"] = int(proof["n_kernel_verified_subclaims"]) > 0
    proof["has_formal_gaps"] = int(proof["n_formal_gaps"]) > 0
    proof["has_formalization_gap_planner_bridge"] = (
        int(proof["n_formalization_gap_planner_bridges"]) > 0
    )
    proof["has_theorem_reduction_closure_work_orders"] = (
        int(proof["n_theorem_reduction_closure_work_orders"]) > 0
    )
    proof["verifiers"] = sorted(verifier_names)
    proof["verification_strengths"] = sorted(strengths)
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeEvidenceSummary",
        "proof": proof,
        "simulation": simulation,
        "algorithm": algorithm,
        "honesty_boundary": {
            "llm_proposals_are_evidence": False,
            "simulation_is_theorem_proof": False,
            "algorithm_sandbox_is_production_registration": False,
            "kernel_subclaims_imply_full_frontier_theorem": False,
        },
    }


def _proof_bank_obligation_request_ids(
    packet: Mapping[str, Any] | None,
    *,
    catalog_ids: tuple[str, ...] = (),
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if not isinstance(packet, Mapping):
        return (), (), ()
    catalog_set = {str(row).strip() for row in catalog_ids if str(row).strip()}
    raw_ids: list[str] = []
    for row in packet.get("proof_bank_obligation_requests", []) or []:
        obligation_id = ""
        if isinstance(row, Mapping):
            obligation_id = str(row.get("obligation_id", "") or "").strip()
        else:
            obligation_id = str(row or "").strip()
        if obligation_id:
            raw_ids.append(obligation_id)
    valid: list[str] = []
    off_catalog: list[str] = []
    rejected: list[str] = []
    for obligation_id in dict.fromkeys(raw_ids):
        try:
            get_obligation(obligation_id)
        except Exception:
            rejected.append(obligation_id)
        else:
            if catalog_set and obligation_id not in catalog_set:
                off_catalog.append(obligation_id)
            else:
                valid.append(obligation_id)
    return tuple(valid), tuple(off_catalog), tuple(rejected)


def _runtime_learning_memory_kernel_verified_proof_obligation_ids(
    architect_context: Mapping[str, Any],
    *,
    catalog_ids: tuple[str, ...] = (),
) -> tuple[str, ...]:
    memory = (
        architect_context.get("runtime_learning_memory", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if not isinstance(memory, Mapping) or memory.get("artifact_kind") != "RuntimeLearningMemoryContext":
        return ()
    rows = memory.get("rows", []) if isinstance(memory.get("rows"), list) else []
    requested_rows: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        for obligation_id in row.get("kernel_verified_proof_obligation_ids", []) or []:
            text = str(obligation_id).strip()
            if text:
                requested_rows.append({"obligation_id": text})
        input_summary = row.get("input_summary", {})
        if isinstance(input_summary, Mapping):
            for obligation_id in input_summary.get("kernel_verified_proof_obligation_ids", []) or []:
                text = str(obligation_id).strip()
                if text:
                    requested_rows.append({"obligation_id": text})
    valid, _off_catalog, _rejected = _proof_bank_obligation_request_ids(
        {"proof_bank_obligation_requests": requested_rows},
        catalog_ids=catalog_ids,
    )
    return valid


def _runtime_learning_memory_proof_obligation_ids(
    architect_context: Mapping[str, Any],
    *,
    catalog_ids: tuple[str, ...] = (),
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    memory = (
        architect_context.get("runtime_learning_memory", {})
        if isinstance(architect_context, Mapping)
        else {}
    )
    if not isinstance(memory, Mapping) or memory.get("artifact_kind") != "RuntimeLearningMemoryContext":
        return (), (), ()
    rows = memory.get("rows", []) if isinstance(memory.get("rows"), list) else []
    already_kernel_verified_ids = set(
        _runtime_learning_memory_kernel_verified_proof_obligation_ids(
            architect_context,
            catalog_ids=catalog_ids,
        )
    )
    requested_rows: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        for key in (
            "recommended_proof_obligation_ids",
            "deferred_priority_proof_obligation_ids_due_to_max",
            "deferred_proof_obligation_ids_due_to_max",
            "selected_proof_obligation_ids",
            "proved_non_kernel_proof_obligation_ids",
            "failed_proof_obligation_ids",
        ):
            for obligation_id in row.get(key, []) or []:
                text = str(obligation_id).strip()
                if text and text not in already_kernel_verified_ids:
                    requested_rows.append({"obligation_id": text})
        input_summary = row.get("input_summary", {})
        if isinstance(input_summary, Mapping):
            for key in (
                "recommended_proof_obligation_ids",
                "deferred_priority_proof_obligation_ids_due_to_max",
                "deferred_proof_obligation_ids_due_to_max",
                "selected_proof_obligation_ids",
                "proved_non_kernel_proof_obligation_ids",
                "failed_proof_obligation_ids",
            ):
                for obligation_id in input_summary.get(key, []) or []:
                    text = str(obligation_id).strip()
                    if text and text not in already_kernel_verified_ids:
                        requested_rows.append({"obligation_id": text})
    return _proof_bank_obligation_request_ids(
        {"proof_bank_obligation_requests": requested_rows},
        catalog_ids=catalog_ids,
    )


def _runtime_formal_source_hits(
    retriever: Any,
    *,
    problem: ResearchProblemSpec,
    theorem_goals: list[TheoremGoal],
    k: int,
) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for goal in theorem_goals:
        query = " ".join(
            [
                problem.problem_class,
                problem.dgp,
                problem.estimand,
                " ".join(problem.assumptions),
                goal.title,
                goal.informal_statement,
                goal.proof_strategy,
                " ".join(goal.required_primitives),
                " ".join(goal.proof_obligations),
            ]
        )
        hits = retriever.search(query, k=k) if retriever is not None else []
        groups.append(
            {
                "theorem_goal_id": goal.id,
                "query_fingerprint": stable_hash(query),
                "hits": [_formal_source_hit_to_json(row) for row in hits],
            }
        )
    return groups


def _knowledge_card_to_json(card: KnowledgeCard) -> dict[str, Any]:
    return asdict(card)


def _paper_source_to_json(source: PaperSourceHit) -> dict[str, Any]:
    return asdict(source)


def _formal_source_hit_to_json(hit: FormalSourceHit) -> dict[str, Any]:
    declaration = hit.declaration
    return {
        "source_id": declaration.source_id,
        "source_type": declaration.source_type,
        "path": declaration.path,
        "line": declaration.line,
        "kind": declaration.kind,
        "name": declaration.name,
        "signature": declaration.signature,
        "score": round(hit.score, 4),
        "matched_terms": list(hit.matched_terms),
    }


def _formalization_task(
    *,
    question: OpenResearchQuestion,
    packet_id: str,
    simulation_manifest_id: str,
    algorithm_sandbox_manifest_id: str = "",
    architect_context: Mapping[str, Any] | None = None,
) -> AgentTask:
    context = dict(architect_context or {})
    return AgentTask(
        task_id=f"formalize:{question.id}:{stable_hash([packet_id, simulation_manifest_id, algorithm_sandbox_manifest_id])[:8]}",
        owner_subsystem="FormalizationEvaluator",
        objective=(
            "Run formal subclaim/proof-gap evaluation for the supported theory "
            "proposal and record proved rows versus formal gaps."
        ),
        inputs={
            "question": _question_to_payload(question),
            "theory_packet_id": packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "algorithm_sandbox_manifest_id": algorithm_sandbox_manifest_id,
            "architect_context": context,
        },
        allowed_tools=("proof_bank_retriever", "formal_source_retriever", "proof_verifier"),
        expected_artifacts=_architect_expected_artifacts(
            context,
            "FormalizationEvaluator",
            ("formalization_manifest",),
        ),
        acceptance_gate=_architect_acceptance_gate(
            context,
            "FormalizationEvaluator",
            "formalization manifest distinguishes proved subclaims from formal gaps",
        ),
        stop_condition="formalization/proof feedback recorded",
    )


def _estimator_spec(packet: Any, estimator_id: str) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return {}
    for row in packet.get("estimator_specs", []) or []:
        if not isinstance(row, Mapping):
            continue
        row_id = str(row.get("id") or row.get("name") or "")
        if row_id == estimator_id:
            return dict(row)
    return {}


def _run_generated_python_sandbox(
    *,
    sandbox_dir: Path,
    estimator_id: str,
    spec: Mapping[str, Any],
    code_draft: Mapping[str, Any],
    n_runs: int,
    seed: int,
    timeout_s: int,
) -> tuple[dict[str, Any], ToolCallRecord]:
    code = str(code_draft.get("code", "") or "")
    script_path = sandbox_dir / f"{_safe_identifier(estimator_id)}_generated_draft.py"
    runner_path = sandbox_dir / f"{_safe_identifier(estimator_id)}_generated_runner.py"
    result_path = sandbox_dir / f"{_safe_identifier(estimator_id)}_generated_result.json"
    safety_errors = _generated_python_sandbox_safety_errors(code)
    boundary = (
        "Generated Python sandbox drafts are untrusted LLM implementation proposals. "
        "AgentRuntime executes only drafts that pass a conservative static guard in "
        "a bounded subprocess. Passing sandbox metrics are implementation evidence, "
        "not production registration and not theorem proof evidence."
    )
    if safety_errors:
        prototype = {
            "estimator_id": estimator_id,
            "prototype_status": "REJECTED_UNSAFE_GENERATED_CODE",
            "executor": "generated_python_sandbox",
            "spec": dict(spec),
            "script_path": "",
            "result_path": "",
            "script_hash": stable_hash(code),
            "safety_errors": safety_errors,
            "metrics": {},
            "smoke_passed": False,
            "promotion_ready": False,
            "boundary": boundary,
        }
        tool_call = ToolCallRecord(
            tool_name="python.generated_sandbox_precheck",
            inputs={"seed": seed, "estimator_id": estimator_id},
            input_hash=stable_hash({"code": code, "seed": seed}),
            exit_status="rejected",
            stdout_summary="generated Python draft rejected by static guard",
            stderr_summary="; ".join(safety_errors)[:500],
            safety_boundary=boundary,
        )
        return prototype, tool_call

    sandbox_dir.mkdir(parents=True, exist_ok=True)
    script_path.write_text(code, encoding="utf-8")
    runner_path.write_text(_generated_python_sandbox_runner_script(), encoding="utf-8")
    replicates = max(5, min(int(n_runs), 80))
    cmd = [
        sys.executable,
        "-I",
        str(runner_path.resolve()),
        "--code",
        str(script_path.resolve()),
        "--out",
        str(result_path.resolve()),
        "--replicates",
        str(replicates),
        "--seed",
        str(seed),
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(sandbox_dir),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        returncode = int(completed.returncode)
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = str(exc.stdout or "").strip()
        stderr = f"timeout after {timeout_s}s: {exc.stderr or ''}".strip()
    metrics: dict[str, Any] = {}
    if result_path.exists():
        try:
            metrics = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive artifact parsing
            metrics = {"parse_error": repr(exc)}
    smoke_passed = (
        returncode == 0
        and bool(metrics)
        and not bool(metrics.get("sandbox_failed", False))
        and _metrics_are_finite(metrics)
    )
    prototype = {
        "estimator_id": estimator_id,
        "prototype_status": "EXECUTED" if returncode == 0 else "FAILED",
        "executor": "generated_python_sandbox",
        "spec": dict(spec),
        "script_path": str(script_path),
        "runner_path": str(runner_path),
        "result_path": str(result_path),
        "script_hash": stable_hash(code),
        "returncode": returncode,
        "safety_errors": [],
        "metrics": metrics,
        "smoke_passed": smoke_passed,
        "promotion_ready": False,
        "boundary": boundary,
    }
    tool_call = ToolCallRecord(
        tool_name="python.generated_algorithm_sandbox",
        inputs={
            "replicates": replicates,
            "seed": seed,
            "script_path": str(script_path),
            "entrypoint": "run_sandbox",
        },
        output_paths=(str(result_path),),
        input_hash=stable_hash({"code": code, "replicates": replicates, "seed": seed}),
        output_hash=stable_hash(metrics) if metrics else "",
        exit_status=str(returncode),
        stdout_summary=stdout[:500],
        stderr_summary=stderr[:500],
        safety_boundary=boundary,
    )
    return prototype, tool_call


def _generated_python_sandbox_safety_errors(code: str) -> list[str]:
    errors: list[str] = []
    if not code.strip():
        return ["empty generated Python draft"]
    if len(code) > 12000:
        errors.append("generated Python draft exceeds 12000 characters")
    lowered = code.lower()
    forbidden_text = (
        "subprocess",
        "socket",
        "urllib",
        "requests",
        "pathlib",
        "shutil",
        "os.",
        "sys.",
        "open(",
        "__import__",
        "eval(",
        "exec(",
        "compile(",
        "globals(",
        "locals(",
        "vars(",
        "getattr(",
        "setattr(",
        "delattr(",
        "input(",
        "breakpoint(",
    )
    for token in forbidden_text:
        if token in lowered:
            errors.append(f"forbidden generated-code token: {token}")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"generated Python draft syntax error: {exc}"]
    function_names = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    if "run_sandbox" not in function_names:
        errors.append("generated Python draft must define run_sandbox")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            errors.append("generated Python draft cannot import modules")
        elif isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef, ast.With, ast.AsyncWith)):
            errors.append(f"unsupported generated-code node: {node.__class__.__name__}")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            errors.append("generated Python draft cannot use global/nonlocal")
        elif isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id in {
                "__builtins__",
                "__loader__",
                "__spec__",
                "__file__",
                "__name__",
            }:
                errors.append(f"forbidden generated-code name: {node.id}")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                errors.append(f"forbidden generated-code private attribute: {node.attr}")
            if isinstance(node.value, ast.Name) and node.value.id not in {"math", "statistics"}:
                errors.append(
                    "generated-code attribute access is limited to math/statistics modules"
                )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                name = node.func.id
                allowed_calls = {
                    "abs",
                    "bool",
                    "dict",
                    "enumerate",
                    "float",
                    "int",
                    "len",
                    "list",
                    "max",
                    "min",
                    "pow",
                    "range",
                    "round",
                    "sorted",
                    "str",
                    "sum",
                    "tuple",
                    *function_names,
                }
                if name not in allowed_calls:
                    errors.append(f"forbidden generated-code call: {name}")
            elif isinstance(node.func, ast.Attribute):
                if not (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id in {"math", "statistics"}
                    and not node.func.attr.startswith("_")
                ):
                    errors.append("forbidden generated-code method call")
            else:
                errors.append("unsupported generated-code call form")
    return sorted(set(errors))


def _metrics_are_finite(metrics: Mapping[str, Any]) -> bool:
    for value in metrics.values():
        if isinstance(value, bool) or value is None or isinstance(value, str):
            continue
        if isinstance(value, int):
            continue
        if isinstance(value, float):
            if not math.isfinite(value):
                return False
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    if not math.isfinite(float(item)):
                        return False
            continue
        if isinstance(value, Mapping):
            if not _metrics_are_finite(value):
                return False
            continue
    return True


def _generated_python_sandbox_runner_script() -> str:
    return r'''from __future__ import annotations

import argparse
import json
import math
import statistics


SAFE_BUILTINS = {
    "abs": abs,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "pow": pow,
    "range": range,
    "round": round,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--replicates", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    with open(args.code, "r", encoding="utf-8") as handle:
        source = handle.read()
    namespace = {
        "__builtins__": SAFE_BUILTINS,
        "math": math,
        "statistics": statistics,
    }
    exec(compile(source, args.code, "exec"), namespace, namespace)
    run_sandbox = namespace.get("run_sandbox")
    if not callable(run_sandbox):
        raise RuntimeError("generated draft did not define callable run_sandbox")
    payload = run_sandbox(seed=args.seed, replicates=args.replicates)
    if not isinstance(payload, dict):
        raise RuntimeError("run_sandbox must return a dict")
    payload.setdefault("sandbox_failed", False)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
'''


def _run_crossfit_aipw_prototype(
    *,
    sandbox_dir: Path,
    estimator_id: str,
    spec: Mapping[str, Any],
    n_runs: int,
    seed: int,
    timeout_s: int,
) -> tuple[dict[str, Any], ToolCallRecord]:
    script_path = sandbox_dir / f"{_safe_identifier(estimator_id)}_prototype.py"
    result_path = sandbox_dir / f"{_safe_identifier(estimator_id)}_result.json"
    script = _crossfit_aipw_prototype_script()
    script_path.write_text(script, encoding="utf-8")
    replicates = max(10, min(int(n_runs), 80))
    cmd = [
        sys.executable,
        str(script_path.resolve()),
        "--out",
        str(result_path.resolve()),
        "--replicates",
        str(replicates),
        "--seed",
        str(seed),
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(sandbox_dir),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        returncode = int(completed.returncode)
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = str(exc.stdout or "").strip()
        stderr = f"timeout after {timeout_s}s: {exc.stderr or ''}".strip()
    metrics: dict[str, Any] = {}
    if result_path.exists():
        try:
            metrics = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive artifact parsing
            metrics = {"parse_error": repr(exc)}
    smoke_passed = (
        returncode == 0
        and bool(metrics)
        and float(metrics.get("n_failed", 1.0)) == 0.0
        and 0.0 <= float(metrics.get("coverage_95", -1.0)) <= 1.0
    )
    boundary = (
        "Sandbox prototype execution checks implementation plausibility and "
        "finite metrics only. It is not a registered production algorithm and "
        "not theorem proof evidence."
    )
    prototype = {
        "estimator_id": estimator_id,
        "prototype_status": "EXECUTED" if returncode == 0 else "FAILED",
        "spec": dict(spec),
        "script_path": str(script_path),
        "result_path": str(result_path),
        "script_hash": stable_hash(script),
        "returncode": returncode,
        "metrics": metrics,
        "smoke_passed": smoke_passed,
        "promotion_ready": False,
        "boundary": boundary,
    }
    tool_call = ToolCallRecord(
        tool_name="python.crossfit_aipw_sandbox",
        inputs={"replicates": replicates, "seed": seed, "script_path": str(script_path)},
        output_paths=(str(result_path),),
        input_hash=stable_hash({"script": script, "replicates": replicates, "seed": seed}),
        output_hash=stable_hash(metrics) if metrics else "",
        exit_status=str(returncode),
        stdout_summary=stdout[:500],
        stderr_summary=stderr[:500],
        safety_boundary=boundary,
    )
    return prototype, tool_call


def _crossfit_aipw_prototype_script() -> str:
    return r'''from __future__ import annotations

import argparse
import json
import math

import numpy as np


def _ridge_fit(x, y, ridge=1e-3):
    x_aug = np.column_stack([np.ones(x.shape[0]), x])
    gram = x_aug.T @ x_aug + ridge * np.eye(x_aug.shape[1])
    return np.linalg.solve(gram, x_aug.T @ y)


def _ridge_predict(beta, x):
    return np.column_stack([np.ones(x.shape[0]), x]) @ beta


def _one_run(rng, n=300, p=5):
    x = rng.normal(size=(n, p))
    logits = 0.35 * x[:, 0] - 0.25 * x[:, 1]
    e_true = 1.0 / (1.0 + np.exp(-logits))
    a = rng.binomial(1, e_true)
    tau = 1.0
    base = 0.5 * x[:, 0] + 0.25 * x[:, 1] ** 2 - 0.2 * x[:, 2]
    y = base + tau * a + rng.normal(scale=1.0, size=n)
    fold = rng.permutation(n) % 2
    scores = np.zeros(n)
    failed = 0
    for k in (0, 1):
        train = fold != k
        test = fold == k
        x_train = x[train]
        a_train = a[train]
        y_train = y[train]
        try:
            beta_e = _ridge_fit(x_train, a_train, ridge=1e-2)
            e_hat = np.clip(_ridge_predict(beta_e, x[test]), 0.05, 0.95)
            beta_0 = _ridge_fit(x_train[a_train == 0], y_train[a_train == 0], ridge=1e-2)
            beta_1 = _ridge_fit(x_train[a_train == 1], y_train[a_train == 1], ridge=1e-2)
            m0 = _ridge_predict(beta_0, x[test])
            m1 = _ridge_predict(beta_1, x[test])
            y_test = y[test]
            a_test = a[test]
            scores[test] = m1 - m0 + a_test / e_hat * (y_test - m1) - (1 - a_test) / (1 - e_hat) * (y_test - m0)
        except Exception:
            failed += int(np.sum(test))
            scores[test] = np.nan
    if np.any(~np.isfinite(scores)):
        return math.nan, math.nan, 0, failed + int(np.sum(~np.isfinite(scores)))
    psi_hat = float(np.mean(scores))
    se = float(np.std(scores, ddof=1) / math.sqrt(n))
    covered = int(abs(psi_hat - tau) <= 1.96 * se) if se > 0.0 and math.isfinite(se) else 0
    return psi_hat, se, covered, failed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--replicates", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260528)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    estimates = []
    ses = []
    covered = []
    n_failed = 0
    for _ in range(args.replicates):
        estimate, se, hit, failed = _one_run(rng)
        if failed or not math.isfinite(estimate) or not math.isfinite(se):
            n_failed += 1
            continue
        estimates.append(estimate)
        ses.append(se)
        covered.append(hit)
    estimates_arr = np.asarray(estimates, dtype=float)
    ses_arr = np.asarray(ses, dtype=float)
    if estimates_arr.size == 0:
        payload = {"n_runs": args.replicates, "n_failed": args.replicates, "status": "all_failed"}
    else:
        bias = float(np.mean(estimates_arr - 1.0))
        payload = {
            "status": "ok",
            "n_runs": args.replicates,
            "n_success": int(estimates_arr.size),
            "n_failed": int(n_failed),
            "bias": bias,
            "rmse": float(np.sqrt(np.mean((estimates_arr - 1.0) ** 2))),
            "coverage_95": float(np.mean(covered)),
            "mean_se": float(np.mean(ses_arr)),
            "empirical_sd": float(np.std(estimates_arr, ddof=1)) if estimates_arr.size > 1 else 0.0,
        }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
'''


def _run_split_conformal_interval_prototype(
    *,
    sandbox_dir: Path,
    estimator_id: str,
    spec: Mapping[str, Any],
    n_runs: int,
    seed: int,
    timeout_s: int,
) -> tuple[dict[str, Any], ToolCallRecord]:
    script_path = sandbox_dir / f"{_safe_identifier(estimator_id)}_split_conformal_template.py"
    result_path = sandbox_dir / f"{_safe_identifier(estimator_id)}_split_conformal_result.json"
    script = _split_conformal_interval_prototype_script()
    script_path.write_text(script, encoding="utf-8")
    replicates = max(10, min(int(n_runs), 100))
    cmd = [
        sys.executable,
        str(script_path.resolve()),
        "--out",
        str(result_path.resolve()),
        "--replicates",
        str(replicates),
        "--seed",
        str(seed),
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(sandbox_dir),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        returncode = int(completed.returncode)
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = str(exc.stdout or "").strip()
        stderr = f"timeout after {timeout_s}s: {exc.stderr or ''}".strip()
    metrics: dict[str, Any] = {}
    if result_path.exists():
        try:
            metrics = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive artifact parsing
            metrics = {"parse_error": repr(exc)}
    smoke_passed = (
        returncode == 0
        and bool(metrics)
        and float(metrics.get("n_failed", 1.0)) == 0.0
        and 0.0 <= float(metrics.get("coverage_90", -1.0)) <= 1.0
        and float(metrics.get("mean_interval_width", 0.0)) > 0.0
    )
    boundary = (
        "Trusted split-conformal sandbox execution checks implementation plausibility "
        "and empirical coverage metrics only. It is not production registration and "
        "not theorem proof evidence."
    )
    prototype = {
        "estimator_id": estimator_id,
        "prototype_status": "EXECUTED" if returncode == 0 else "FAILED",
        "executor": "registered_split_conformal_interval_template",
        "spec": dict(spec),
        "script_path": str(script_path),
        "result_path": str(result_path),
        "script_hash": stable_hash(script),
        "returncode": returncode,
        "metrics": metrics,
        "smoke_passed": smoke_passed,
        "promotion_ready": False,
        "boundary": boundary,
    }
    tool_call = ToolCallRecord(
        tool_name="python.split_conformal_interval_sandbox",
        inputs={"replicates": replicates, "seed": seed, "script_path": str(script_path)},
        output_paths=(str(result_path),),
        input_hash=stable_hash({"script": script, "replicates": replicates, "seed": seed}),
        output_hash=stable_hash(metrics) if metrics else "",
        exit_status=str(returncode),
        stdout_summary=stdout[:500],
        stderr_summary=stderr[:500],
        safety_boundary=boundary,
    )
    return prototype, tool_call


def _split_conformal_interval_prototype_script() -> str:
    return r'''from __future__ import annotations

import argparse
import json
import math

import numpy as np


def _ridge_fit(x, y, ridge=1e-3):
    x_aug = np.column_stack([np.ones(x.shape[0]), x])
    gram = x_aug.T @ x_aug + ridge * np.eye(x_aug.shape[1])
    return np.linalg.solve(gram, x_aug.T @ y)


def _ridge_predict(beta, x):
    return np.column_stack([np.ones(x.shape[0]), x]) @ beta


def _response(x, beta, rng, *, heavy_tail=False, nonlinear=False):
    signal = x @ beta
    if nonlinear:
        signal = signal + 0.5 * np.sin(x[:, 0]) - 0.25 * x[:, 1] * x[:, 2]
    if heavy_tail:
        noise = rng.standard_t(df=3, size=x.shape[0])
    else:
        noise = rng.normal(scale=1.0, size=x.shape[0])
    return signal + noise


def _one_run(rng, *, alpha=0.1, n_train=120, n_cal=80, n_test=120, d=5, mode="linear"):
    n_total = n_train + n_cal + n_test
    x = rng.normal(size=(n_total, d))
    beta = rng.normal(size=d)
    y = _response(
        x,
        beta,
        rng,
        heavy_tail=(mode == "heavy_tail"),
        nonlinear=(mode == "nonlinear"),
    )
    x_train = x[:n_train]
    y_train = y[:n_train]
    x_cal = x[n_train:n_train + n_cal]
    y_cal = y[n_train:n_train + n_cal]
    x_test = x[n_train + n_cal:]
    y_test = y[n_train + n_cal:]
    beta_hat = _ridge_fit(x_train, y_train)
    cal_pred = _ridge_predict(beta_hat, x_cal)
    scores = np.abs(y_cal - cal_pred)
    if np.any(~np.isfinite(scores)):
        return math.nan, math.nan, math.nan, 1
    order = int(math.ceil((1.0 - alpha) * (n_cal + 1))) - 1
    order = max(0, min(order, n_cal - 1))
    q = float(np.sort(scores)[order])
    test_pred = _ridge_predict(beta_hat, x_test)
    covered = np.abs(y_test - test_pred) <= q
    return float(np.mean(covered)), float(2.0 * q), q, 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--replicates", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260607)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    modes = ("linear", "nonlinear", "heavy_tail")
    coverages = []
    widths = []
    quantiles = []
    by_mode = {mode: [] for mode in modes}
    n_failed = 0
    for idx in range(args.replicates):
        mode = modes[idx % len(modes)]
        coverage, width, q, failed = _one_run(rng, mode=mode)
        if failed or not (math.isfinite(coverage) and math.isfinite(width) and math.isfinite(q)):
            n_failed += 1
            continue
        coverages.append(coverage)
        widths.append(width)
        quantiles.append(q)
        by_mode[mode].append(coverage)
    if not coverages:
        payload = {"status": "all_failed", "n_runs": args.replicates, "n_failed": args.replicates}
    else:
        payload = {
            "status": "ok",
            "alpha": 0.1,
            "nominal_coverage": 0.9,
            "n_runs": args.replicates,
            "n_success": len(coverages),
            "n_failed": n_failed,
            "coverage_90": float(np.mean(coverages)),
            "coverage_sd": float(np.std(np.asarray(coverages), ddof=1)) if len(coverages) > 1 else 0.0,
            "mean_interval_width": float(np.mean(widths)),
            "mean_calibration_quantile": float(np.mean(quantiles)),
            "coverage_by_mode": {
                mode: float(np.mean(values)) if values else math.nan
                for mode, values in by_mode.items()
            },
        }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
'''


def _question_to_payload(question: OpenResearchQuestion) -> dict[str, Any]:
    return {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }


def _runtime_task_prompt_summary(task: AgentTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "owner_subsystem": task.owner_subsystem,
        "objective": task.objective,
        "allowed_tools": list(task.allowed_tools),
        "expected_artifacts": list(task.expected_artifacts),
        "acceptance_gate": task.acceptance_gate,
        "stop_condition": task.stop_condition,
    }


def _question_from_payload(payload: Mapping[str, Any]) -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id=str(payload["id"]),
        title=str(payload.get("title", payload["id"])),
        description=str(payload["description"]),
        tags=tuple(str(row) for row in payload.get("tags", ()) or ()),
    )


def _problem_to_json(problem: ResearchProblemSpec) -> dict[str, Any]:
    row = asdict(problem)
    row["assumptions"] = list(problem.assumptions)
    row["diagnostics"] = list(problem.diagnostics)
    row["stress_tests"] = list(problem.stress_tests)
    return row


def _procedure_to_json(procedure: CandidateProcedure) -> dict[str, Any]:
    return asdict(procedure)


def _theorem_goal_to_json(goal: TheoremGoal) -> dict[str, Any]:
    return asdict(goal)


def _simulation_to_json(simulation: ResearchSimulation) -> dict[str, Any]:
    return asdict(simulation)


def _formal_subclaim_to_json(subclaim: FormalSubclaim) -> dict[str, Any]:
    return asdict(subclaim)


def _safe_identifier(raw: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", raw.strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "question"


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")


def _append_jsonl_row(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")
        handle.flush()

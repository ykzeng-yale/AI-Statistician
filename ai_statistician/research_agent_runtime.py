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
from .formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_COMPONENT,
    FORMALIZATION_GAP_PLANNER_STANDALONE_INPUT_SCHEMA_VERSION,
)
from .formalizer_llm import (
    FORMALIZER_BOUNDARY,
    FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE,
    LLMFormalizerProofEngineerAgent,
)
from .model_backend import ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY
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
            if estimator_id == "crossfit_aipw":
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
        llm_off_catalog_proof_obligation_ids: tuple[str, ...] = ()
        llm_rejected_proof_obligation_ids: tuple[str, ...] = ()
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
        produced_artifacts: dict[str, Any] = {}
        observations: list[EnvironmentObservation] = []
        if self.proposal_agent is not None:
            proposal_packet = self.proposal_agent.propose(
                question=question,
                theory_packet=packet if isinstance(packet, Mapping) else {},
                simulation_manifest=simulation_manifest if isinstance(simulation_manifest, Mapping) else {},
                algorithm_manifest=algorithm_manifest if isinstance(algorithm_manifest, Mapping) else {},
                registered_problem=_problem_to_json(problem),
                theorem_goals=[_theorem_goal_to_json(row) for row in theorem_goals],
                proof_bank_obligation_catalog=proof_bank_obligation_catalog,
            )
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
            proposal_id = str(proposal_packet["packet_id"])
            produced_artifacts[proposal_id] = proposal_packet
            observations.append(
                EnvironmentObservation(
                    observation_type="llm_formalizer_proof_engineer_proposal",
                    summary=(
                        "validated LLM Formalizer/ProofEngineer proposal recorded "
                        "before proof-bank/kernel evaluation"
                    ),
                    payload={
                        "packet_id": proposal_id,
                        "n_formal_targets": len(proposal_packet.get("formal_targets", []) or []),
                        "n_retrieval_queries": len(proposal_packet.get("retrieval_queries", []) or []),
                        "n_proof_bank_obligation_requests": len(
                            proposal_packet.get("proof_bank_obligation_requests", []) or []
                        ),
                        "n_registered_proof_bank_obligation_candidates": len(proof_bank_obligation_catalog),
                        "n_registered_proof_bank_obligation_requests": len(llm_requested_proof_obligation_ids),
                        "n_off_catalog_proof_bank_obligation_requests": len(
                            llm_off_catalog_proof_obligation_ids
                        ),
                        "proof_evidence_status": FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE,
                    },
                )
            )
            proposal_evidence = EvidenceLedgerEntry(
                evidence_id="evidence:" + stable_hash([task.task_id, proposal_id])[:20],
                task_id=task.task_id,
                artifact_id=proposal_id,
                evidence_type="llm_formalizer_proof_engineer_proposal",
                status="PROPOSAL_RECORDED_REQUIRES_KERNEL_VERIFICATION",
                boundary=FORMALIZER_BOUNDARY,
                payload={
                    "n_formal_targets": len(proposal_packet.get("formal_targets", []) or []),
                    "n_retrieval_queries": len(proposal_packet.get("retrieval_queries", []) or []),
                    "n_registered_proof_bank_obligation_candidates": len(proof_bank_obligation_catalog),
                    "n_registered_proof_bank_obligation_requests": len(llm_requested_proof_obligation_ids),
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
                    *llm_requested_proof_obligation_ids,
                ),
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
        proof_obligation_control["llm_requested_proof_obligation_ids"] = list(llm_requested_proof_obligation_ids)
        proof_obligation_control["llm_off_catalog_proof_obligation_ids"] = list(
            llm_off_catalog_proof_obligation_ids
        )
        proof_obligation_control["llm_rejected_proof_obligation_ids"] = list(llm_rejected_proof_obligation_ids)
        proof_obligation_control["priority_source"] = (
            "runtime_learning_memory+llm_formalizer"
            if memory_prioritized_proof_obligation_ids and llm_requested_proof_obligation_ids
            else "runtime_learning_memory"
            if memory_prioritized_proof_obligation_ids
            else "llm_formalizer"
            if llm_requested_proof_obligation_ids
            else "none"
        )
        proof_obligation_control["priority_boundary"] = (
            "LLM Formalizer and runtime-learning-memory proof-bank requests only prioritize registered "
            "subclaim kernel-smoke work. AgentRuntime filters them against the proof bank and current "
            "candidate catalog; off-catalog or rejected requests are recorded but not used for proof "
            "selection. Requests and memory are not proof evidence."
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
                    "llm_prioritized_proof_obligation_ids": list(llm_requested_proof_obligation_ids),
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
    evidence_summary = _runtime_evidence_summary(results)
    manifest = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_stage": (
            "architect_retrieval_theory_simulation_algorithm_formalization_critic_environment_loop"
            if architect_coordinator is not None
            else "retrieval_theory_simulation_algorithm_formalization_critic_environment_loop"
        ),
        "n_questions": len(questions),
        "config": asdict(config),
        "runtime_input_context": _runtime_input_context_summary(architect_context or {}),
        "status_counts": dict(sorted(status_counts.items())),
        "runtime_evidence_summary": evidence_summary,
        "n_kernel_verified_subclaims": evidence_summary["proof"]["n_kernel_verified_subclaims"],
        "n_formal_gaps": evidence_summary["proof"]["n_formal_gaps"],
        "n_algorithm_sandbox_executed": evidence_summary["algorithm"]["n_algorithm_sandbox_executed"],
        "n_generated_code_sandbox_executed": evidence_summary["algorithm"]["n_generated_code_sandbox_executed"],
        "n_unsafe_generated_code_rejected": evidence_summary["algorithm"]["n_unsafe_generated_code_rejected"],
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "simulation_evidence_boundary": SIMULATION_NOT_PROOF_BOUNDARY,
        "llm_runtime_topology": llm_topology,
        "artifacts": {
            "runtime_traces_jsonl": str(traces_path),
            "runtime_llm_topology_json": str(llm_topology_path),
            "per_question_results": [str(row["artifact_path"]) for row in results],
        },
    }
    agenda_rows = _runtime_agenda_rows(results)
    learning_rows = _runtime_learning_rows(results)
    gap_planner_bridge_rows = _runtime_formalization_gap_planner_bridge_rows(results)
    agenda_path = out_dir / "runtime_next_action_agenda.jsonl"
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    gap_planner_bridges_path = out_dir / "runtime_formalization_gap_planner_bridges.jsonl"
    gap_planner_seed_dir = out_dir / "runtime_formalization_gap_planner_seeds"
    gap_planner_handoffs_path = out_dir / "runtime_formalization_gap_planner_handoffs.jsonl"
    _write_jsonl(agenda_path, agenda_rows)
    _write_jsonl(learning_path, learning_rows)
    _write_runtime_formalization_gap_planner_seed_files(
        gap_planner_bridge_rows,
        seed_dir=gap_planner_seed_dir,
    )
    gap_planner_handoff_rows = _runtime_formalization_gap_planner_handoff_rows(
        gap_planner_bridge_rows,
        runtime_out_dir=out_dir,
    )
    _write_jsonl(gap_planner_handoffs_path, gap_planner_handoff_rows)
    _write_jsonl(gap_planner_bridges_path, gap_planner_bridge_rows)
    manifest["artifacts"]["runtime_next_action_agenda_jsonl"] = str(agenda_path)
    manifest["artifacts"]["runtime_learning_rows_jsonl"] = str(learning_path)
    manifest["artifacts"]["runtime_formalization_gap_planner_bridges_jsonl"] = str(
        gap_planner_bridges_path
    )
    manifest["artifacts"]["runtime_formalization_gap_planner_seed_dir"] = str(
        gap_planner_seed_dir
    )
    manifest["artifacts"]["runtime_formalization_gap_planner_handoffs_jsonl"] = str(
        gap_planner_handoffs_path
    )
    manifest["n_runtime_next_action_items"] = len(agenda_rows)
    manifest["n_runtime_learning_rows"] = len(learning_rows)
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
    violations = _llm_topology_policy_violations(agents)
    manifest = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeLLMTopologyManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "default_live_provider": "anthropic",
            "supported_generator_providers": ["anthropic", "openai", "static"],
            "claude_model_selection": ANTHROPIC_CLAUDE_MODEL_SELECTION_POLICY,
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
    allowed = {"anthropic", "openai", "static"}
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
    expected_tier = str(row.get("model_tier", "") or "").strip().lower()
    model = str(row.get("model", "") or "").strip()
    actual_tier = _anthropic_model_family(model)
    if not expected_tier or not actual_tier or actual_tier == expected_tier:
        return ""
    return (
        f"{row.get('subsystem')} expected Claude {expected_tier} tier "
        f"but is configured with {model}"
    )


def _anthropic_model_family(model: str) -> str:
    key = model.strip().lower()
    for family in ("haiku", "sonnet", "opus"):
        if family in key:
            return family
    return ""


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
    return {
        "subsystem": subsystem,
        "enabled": True,
        "provider_name": provider_name,
        "backend_provider_name": str(getattr(provider, "provider_name", provider_name) or ""),
        "model": str(getattr(config, "model", "") or ""),
        "model_tier": model_tier,
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
    if int(formal_counts.get("formal_gap", 0) or 0) > 0:
        gap_goals = [
            row.get("id", "")
            for row in formalization_manifest.get("deterministic_theorem_goals", []) or []
            if isinstance(row, Mapping)
        ]
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
    selected_proof_obligation_ids = [
        str(row) for row in proof_control.get("selected_proof_obligation_ids", []) or []
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
    recommended_proof_obligation_ids = (
        failed_proof_obligation_ids
        or proved_non_kernel_proof_obligation_ids
        or selected_proof_obligation_ids
    )
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
                "kernel_verified_proof_obligation_ids": kernel_verified_proof_obligation_ids,
                "proved_non_kernel_proof_obligation_ids": proved_non_kernel_proof_obligation_ids,
                "failed_proof_obligation_ids": failed_proof_obligation_ids,
                "formal_gap_target_ids": formal_gap_target_ids,
                "recommended_proof_obligation_ids": recommended_proof_obligation_ids,
            },
            "selected_proof_obligation_ids": selected_proof_obligation_ids,
            "kernel_verified_proof_obligation_ids": kernel_verified_proof_obligation_ids,
            "proved_non_kernel_proof_obligation_ids": proved_non_kernel_proof_obligation_ids,
            "failed_proof_obligation_ids": failed_proof_obligation_ids,
            "formal_gap_target_ids": formal_gap_target_ids,
            "recommended_proof_obligation_ids": recommended_proof_obligation_ids,
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


def _runtime_formalization_gap_planner_handoff_rows(
    bridge_rows: list[dict[str, Any]],
    *,
    runtime_out_dir: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    handoff_root = runtime_out_dir / "runtime_formalization_gap_planner_handoffs"
    for bridge in bridge_rows:
        seed_path_text = str(bridge.get("standalone_seed_path", "")).strip()
        if not seed_path_text:
            continue
        seed_path = Path(seed_path_text)
        bridge_id = str(bridge.get("bridge_id", "")).strip()
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
        standalone_out = handoff_root / handoff_slug / "standalone_plan"
        llm_prompt_out = handoff_root / handoff_slug / "llm_route_planner_prompt"
        llm_live_out = handoff_root / handoff_slug / "llm_route_planner_live"
        standalone_plan_cli = (
            "python3 -m ai_statistician.cli formalization-gap-planner-standalone-plan "
            f"--input {seed_arg} --out {shlex.quote(str(standalone_out))}"
        )
        llm_route_planner_prompt_cli = (
            "python3 -m ai_statistician.cli formalization-gap-planner-llm-route-planner "
            f"--input {seed_arg} --provider anthropic --model-tier auto "
            "--max-repair-attempts 1 "
            f"--out {shlex.quote(str(llm_prompt_out))}"
        )
        llm_route_planner_live_cli = (
            "python3 -m ai_statistician.cli formalization-gap-planner-llm-route-planner "
            f"--input {seed_arg} --provider anthropic --model-tier auto "
            f"--max-repair-attempts 1 --invoke-provider --out {shlex.quote(str(llm_live_out))}"
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
            "target_prover_family": str(bridge.get("target_prover_family", "")),
            "recommended_llm_provider": "anthropic",
            "recommended_model_tier": "auto",
            "model_tier_policy": (
                "stage Anthropic prompt packets with --model-tier auto; the "
                "LLM route planner chooses Claude Haiku for small bounded "
                "routes and Claude Sonnet for residual, bridge, source-port, "
                "or new-theory routes"
            ),
            "standalone_plan_cli": standalone_plan_cli,
            "llm_route_planner_prompt_cli": llm_route_planner_prompt_cli,
            "llm_route_planner_live_cli": llm_route_planner_live_cli,
            "cost_control": (
                "Use llm_route_planner_prompt_cli first; it writes request "
                "packets without calling the Anthropic API. Add live execution "
                "only after inspecting the staged prompts or run "
                "llm_route_planner_live_cli explicitly."
            ),
            "proof_evidence_status": (
                RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE
            ),
            "proof_evidence_boundary": RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY,
        }
        bridge["handoff_id"] = row["handoff_id"]
        bridge["standalone_plan_cli"] = standalone_plan_cli
        bridge["llm_route_planner_prompt_cli"] = llm_route_planner_prompt_cli
        bridge["llm_route_planner_live_cli"] = llm_route_planner_live_cli
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
            "--out runs/formalization_gap_planner_runtime_llm_route_planner_prompt"
        ),
        "next_llm_route_planner_live_cli": (
            "python3 -m ai_statistician.cli formalization-gap-planner-llm-route-planner "
            "--input <runtime_formalization_gap_planner_standalone_seed.json> "
            "--provider anthropic --model-tier auto --max-repair-attempts 1 --invoke-provider "
            "--out runs/formalization_gap_planner_runtime_llm_route_planner_live"
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
    route_id = (
        "runtime_gap_route:"
        + stable_hash([question.id, theorem_goal.id, formalization_manifest_id])[:20]
    )
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
        "replan_metadata": {
            "source_component": "ai_statistician_research_agent_runtime",
            "formalization_manifest_id": formalization_manifest_id,
            "proof_state_feedback_manifest_id": proof_state_feedback_manifest_id,
            "runtime_theorem_goal_id": theorem_goal.id,
            "runtime_formal_subclaim_ids": [row.id for row in related_subclaims],
            "residual_goals": list(residual_goals),
            "source_refs": list(source_refs),
            "lean_declaration_hits": _runtime_gap_lean_hits(related_subclaims),
            "applied_prover_attempt_statuses": _runtime_gap_attempt_statuses(
                related_subclaims,
                proof_state_by_subclaim,
            ),
            "route_revision_reasons": list(residual_goals[:8]),
            "proof_evidence_status": (
                RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_NOT_PROOF_EVIDENCE
            ),
            "proof_evidence_boundary": RUNTIME_FORMALIZATION_GAP_PLANNER_BRIDGE_BOUNDARY,
        },
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


def _runtime_gap_lean_hits(subclaims: list[FormalSubclaim]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for subclaim in subclaims:
        rows.extend(dict(hit) for hit in subclaim.formal_source_hits)
        for primitive, hits in subclaim.primitive_formal_source_hits.items():
            for hit in hits:
                rows.append({"primitive": primitive, **dict(hit)})
    return rows[:40]


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
        "n_full_frontier_theorem_proved": 0,
        "has_kernel_evidence": False,
        "has_formal_gaps": False,
        "has_formalization_gap_planner_bridge": False,
        "verifiers": [],
        "verification_strengths": [],
        "proof_obligation_control": {
            "configured_proof_obligation_ids": [],
            "requested_proof_obligation_ids": [],
            "memory_prioritized_proof_obligation_ids": [],
            "memory_off_catalog_proof_obligation_ids": [],
            "memory_rejected_proof_obligation_ids": [],
            "llm_requested_proof_obligation_ids": [],
            "llm_off_catalog_proof_obligation_ids": [],
            "llm_rejected_proof_obligation_ids": [],
            "prioritized_proof_obligation_ids": [],
            "max_proof_obligations": 0,
            "n_registered_proof_bank_obligation_candidates": 0,
            "n_candidate_proof_obligations": 0,
            "n_selected_proof_obligations": 0,
            "selected_proof_obligation_ids": [],
            "selected_priority_proof_obligation_ids": [],
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
    already_kernel_verified_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        for obligation_id in row.get("kernel_verified_proof_obligation_ids", []) or []:
            text = str(obligation_id).strip()
            if text:
                already_kernel_verified_ids.add(text)
        input_summary = row.get("input_summary", {})
        if isinstance(input_summary, Mapping):
            for obligation_id in input_summary.get("kernel_verified_proof_obligation_ids", []) or []:
                text = str(obligation_id).strip()
                if text:
                    already_kernel_verified_ids.add(text)
    requested_rows: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        for key in (
            "recommended_proof_obligation_ids",
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

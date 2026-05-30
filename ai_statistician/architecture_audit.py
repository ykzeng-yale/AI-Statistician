from __future__ import annotations

import inspect
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .research_lab import (
    AIStatisticalTheoryLab,
    FormalSubclaimProver,
    ProblemFormalizer,
    ResearchSimulator,
    TheoryPlanner,
    _build_next_iteration_agenda,
)
from .research_loop import ResearchLoopCoordinator
from .algorithm_engineer import DefaultAlgorithmEngineer
from .proof_engineer import DefaultProofEngineer
from .theory_developer import DefaultTheoryDeveloper
from .theory_proposal import AnthropicTheoryProposer


@dataclass(frozen=True)
class ArchitectureComponent:
    component: str
    status: str
    evidence: tuple[str, ...]
    limitation: str
    target_delta: str


@dataclass(frozen=True)
class FeedbackRoute:
    trigger: str
    owner_agent: str
    action: str
    live_execution_status: str
    evidence: str


def audit_architecture(out_dir: Path | None = None) -> dict[str, object]:
    """Audit implemented architecture vs the intended closed-loop research lab.

    The current system has real proof, simulation, retrieval, trace, and agenda
    components. The important honesty boundary is that feedback is routed into
    ``next_iteration_agenda`` rather than automatically executing another theory
    development round inside ``AIStatisticalTheoryLab.run``.
    """

    run_source = inspect.getsource(AIStatisticalTheoryLab.run)
    has_one_pass_run = all(
        token in run_source
        for token in (
            "self.formalizer.formalize",
            "self.planner.plan",
            "self.prover.prove",
            "self.simulator.run",
            "build_theory_plan",
        )
    )
    has_live_revision_loop = callable(getattr(ResearchLoopCoordinator, "iterate", None))
    has_registered_live_repair_handler_interface = (
        "repair_handlers" in inspect.signature(ResearchLoopCoordinator).parameters
    )
    has_next_iteration_agenda = callable(_build_next_iteration_agenda)

    components = [
        ArchitectureComponent(
            component="problem_formalizer",
            status="ACHIEVED",
            evidence=(f"{ProblemFormalizer.__module__}.{ProblemFormalizer.__name__}",),
            limitation="Deterministic registry-backed extraction, not arbitrary paper parsing.",
            target_delta="Add LLM/paper parser repair loop with structured confidence and unsupported-topic rejection.",
        ),
        ArchitectureComponent(
            component="theory_planner",
            status="ACHIEVED",
            evidence=(f"{TheoryPlanner.__module__}.{TheoryPlanner.__name__}", "emits procedures, theorem goals, informal derivation text"),
            limitation="Registry/template-driven; it does not freely invent new estimator families or theorem programs.",
            target_delta="Add LLM TheoryDeveloper that proposes and revises estimators, assumptions, proof plans, and theorem decompositions.",
        ),
        ArchitectureComponent(
            component="llm_theory_developer",
            status="PARTIAL",
            evidence=(f"{AnthropicTheoryProposer.__module__}.{AnthropicTheoryProposer.__name__}", "optional gated intake/classification before deterministic execution"),
            limitation="Current LLM proposer is gated by supported families and is not the main theorem-development engine.",
            target_delta="Promote to a live TheoryDeveloper with verifier/simulator feedback and strict registry/sandbox acceptance gates.",
        ),
        ArchitectureComponent(
            component="retrieval_layer",
            status="ACHIEVED",
            evidence=("local Lean/source retrieval, proof-bank retrieval, SQLite/shape/graph-backed formal-source search",),
            limitation="Provider fusion with Lean Finder/ReProver/Loogle and learned premise ranking is still integration work.",
            target_delta="Fuse local index, external providers, graph features, embeddings, and AXLE attempt-cache feedback.",
        ),
        ArchitectureComponent(
            component="formal_subclaim_prover",
            status="ACHIEVED",
            evidence=(f"{FormalSubclaimProver.__module__}.{FormalSubclaimProver.__name__}", "AXLE/Lean verifies registered proof-bank obligations"),
            limitation="Verifies reusable subclaims; it is not yet a general proof-search/autoformalization engine for arbitrary frontier theorems.",
            target_delta="Add Formalizer + ProofEngineer loop: statement repair, premise retrieval, tactic/proof search, proof-bank promotion.",
        ),
        ArchitectureComponent(
            component="algorithm_engineer",
            status="ACHIEVED",
            evidence=("vetted research algorithm registry is executed by ResearchSimulator",),
            limitation="Algorithms are registry-vetted; arbitrary LLM-written code is not admitted into production execution.",
            target_delta="Add sandboxed algorithm proposal/repair with property tests, implementation hashes, and simulator feedback gates.",
        ),
        ArchitectureComponent(
            component="research_simulator",
            status="ACHIEVED",
            evidence=(f"{ResearchSimulator.__module__}.{ResearchSimulator.__name__}", "runs problem-specific diagnostics and classifies simulation failures"),
            limitation="Deterministic empirical critic over registered metrics; not yet a learned critic or live rerun driver.",
            target_delta="Make simulator diagnoses executable loop signals, not only report/agenda evidence.",
        ),
        ArchitectureComponent(
            component="feedback_router",
            status="ACHIEVED" if has_next_iteration_agenda else "NOT_IMPLEMENTED",
            evidence=(f"{_build_next_iteration_agenda.__module__}.{_build_next_iteration_agenda.__name__}", "routes formal gaps, failed proofs, and simulation diagnoses to owner agents"),
            limitation="Feedback is queued into a next-iteration agenda.",
            target_delta="Connect agenda items to an active coordinator that executes the next revision round.",
        ),
        ArchitectureComponent(
            component="live_revision_loop",
            status="PARTIAL" if has_live_revision_loop else "NOT_IMPLEMENTED",
            evidence=(
                f"{ResearchLoopCoordinator.__module__}.{ResearchLoopCoordinator.__name__}.iterate",
                f"{DefaultProofEngineer.__module__}.{DefaultProofEngineer.__name__}",
                f"{DefaultTheoryDeveloper.__module__}.{DefaultTheoryDeveloper.__name__}",
                f"{DefaultAlgorithmEngineer.__module__}.{DefaultAlgorithmEngineer.__name__}",
                "AIStatisticalTheoryLab.run remains one-pass; ResearchLoopCoordinator executes the next_iteration_agenda around it",
                "registered repair_handlers can execute live proof/theory/algorithm/simulator repair actions and request reruns",
                "live repair handler outputs are checked against per-trigger repair contracts before reruns are allowed",
                "DefaultProofEngineer verifies existing proof-bank bridges for FORMAL_GAP actions before emitting repair artifacts",
                "DefaultTheoryDeveloper converts simulation theory/procedure failures into scoped revision artifacts",
                "DefaultAlgorithmEngineer converts numerical/implementation failures into scoped repair artifacts",
                "AIStatisticalTheoryLab accepts theory_revisions overlays and applies them before retrieval/proof/simulation",
            ),
            limitation=(
                "The loop executes safe built-in routes, can call registered live repair handlers, and has a narrow "
                "default proof-bank bridge handler plus scoped default theory-revision proposal handler; free-form "
                "theory repair, new proof search, and arbitrary code mutation still require stronger agents."
            ),
            target_delta="Register default LLM TheoryDeveloper, proof-search ProofEngineer, and sandboxed AlgorithmEngineer repair handlers.",
        ),
    ]

    feedback_routes = [
        FeedbackRoute(
            trigger="FORMAL_GAP",
            owner_agent="formal_verifier",
            action="retrieve_or_build_missing_lean_primitives",
            live_execution_status="EXECUTABLE_DEFAULT_PROOF_BANK_BRIDGE_OR_RETRIEVAL_REVIEW",
            evidence="ResearchLoopCoordinator invokes DefaultProofEngineer for bridgeable FORMAL_GAP items and otherwise reviews formal-source hits",
        ),
        FeedbackRoute(
            trigger="FAILED_PROOF_OBLIGATION",
            owner_agent="formal_verifier",
            action="repair_axiom_verified_proof_or_downgrade_to_gap",
            live_execution_status="EXECUTABLE_WITH_REGISTERED_LIVE_HANDLER",
            evidence="ResearchLoopCoordinator can call a registered FAILED_PROOF_OBLIGATION/proof handler, otherwise exports proof-engineer repair work",
        ),
        FeedbackRoute(
            trigger="THEORY_OR_PROCEDURE_ISSUE",
            owner_agent="theory_developer",
            action="revise_estimator_or_theorem_acceptance_rule",
            live_execution_status="EXECUTABLE_SCOPED_THEORY_REVISION_PROPOSAL",
            evidence="ResearchLoopCoordinator invokes DefaultTheoryDeveloper or a registered handler for THEORY_OR_PROCEDURE_ISSUE",
        ),
        FeedbackRoute(
            trigger="IMPLEMENTATION_OR_NUMERICAL_ISSUE",
            owner_agent="algorithm_engineer",
            action="repair_algorithm_implementation_or_numerical_stability",
            live_execution_status="EXECUTABLE_SCOPED_ALGORITHM_REPAIR_PROPOSAL",
            evidence="ResearchLoopCoordinator invokes DefaultAlgorithmEngineer or a registered handler for IMPLEMENTATION_OR_NUMERICAL_ISSUE",
        ),
        FeedbackRoute(
            trigger="ENVIRONMENT_OR_DGP_ISSUE",
            owner_agent="simulator_agent",
            action="implement_or_correct_simulation_environment",
            live_execution_status="EXECUTABLE_WITH_REGISTERED_LIVE_HANDLER",
            evidence="ResearchLoopCoordinator can call a registered ENVIRONMENT_OR_DGP_ISSUE handler, otherwise exports simulator-extension work",
        ),
        FeedbackRoute(
            trigger="INSUFFICIENT_MC_PRECISION",
            owner_agent="simulator_agent",
            action="rerun_with_larger_monte_carlo_budget",
            live_execution_status="EXECUTABLE_RERUN_MORE_MC",
            evidence="ResearchLoopCoordinator increases n_runs and reruns when round budget remains",
        ),
        FeedbackRoute(
            trigger="NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS",
            owner_agent="research_coordinator",
            action="archive_trace_or_expand_benchmark_stress_tests",
            live_execution_status="EXECUTABLE_MONITOR",
            evidence="ResearchLoopCoordinator terminates clean monitor-only traces",
        ),
    ]

    target_requirements = [
        {
            "requirement": "LLM informal statistical theory development before formalization",
            "status": "PARTIAL",
            "current_evidence": "TheoryPlanner emits derivation text; AnthropicTheoryProposer is optional/gated.",
            "missing": "Free-form theorem/estimator invention with revision from proof and simulation failures.",
        },
        {
            "requirement": "Formalizer + ProofEngineer with Lean proof repair/search",
            "status": "PARTIAL",
            "current_evidence": "FormalSubclaimProver verifies registered AXLE obligations and exports formal gaps.",
            "missing": "Live generation/repair of arbitrary Lean statements and proofs from theorem goals.",
        },
        {
            "requirement": "Simulator feedback actively revises algorithm or theory in the same run",
            "status": "PARTIAL",
            "current_evidence": "ResearchLoopCoordinator executes MC precision reruns, invokes DefaultTheoryDeveloper for scoped theory-revision proposals, applies contract-valid theory revision overlays to the next lab round, and can invoke contract-checked registered live theory/algorithm/simulator repair handlers before rerunning.",
            "missing": "Default trained TheoryDeveloper that can invent and justify new estimator families, plus AlgorithmEngineer promotion that applies sandboxed patches and reruns them.",
        },
        {
            "requirement": "Formal proof feedback actively revises assumptions/theorem statements/proof search",
            "status": "PARTIAL",
            "current_evidence": "ResearchLoopCoordinator reviews formal-source hits for FORMAL_GAP rows, invokes a default verified proof-bank bridge handler, and can invoke contract-checked registered proof-repair handlers.",
            "missing": "Default automated statement repair, premise search, tactic/proof search, and true new proof-bank theorem promotion within the same loop.",
        },
        {
            "requirement": "End-to-end arbitrary frontier stat theory development",
            "status": "NOT_IMPLEMENTED",
            "current_evidence": "System handles supported benchmark surface with scoped surrogate support and honest gaps.",
            "missing": "Full autonomous JASA/AOAS theorem discovery with Lean proofs of new asymptotic guarantees.",
        },
    ]

    status_counts = Counter(row.status for row in components)
    payload: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_status": "PARTIAL_LIVE_FEEDBACK_LOOP_WITH_SCOPED_AUTONOMY",
        "is_current_architecture_correct_for_release_scaffold": True,
        "is_current_architecture_correct_for_full_autonomous_ai_statistician": False,
        "implemented_feedback_mode": "bounded_research_loop_over_next_iteration_agenda",
        "target_feedback_mode": "fully_live_iterative_research_loop",
        "has_one_pass_research_run": has_one_pass_run,
        "has_live_revision_loop": has_live_revision_loop,
        "has_registered_live_repair_handler_interface": has_registered_live_repair_handler_interface,
        "all_release_scaffold_components_present": all(
            row.status != "NOT_IMPLEMENTED" for row in components if row.component != "live_revision_loop"
        ),
        "component_counts": dict(sorted(status_counts.items())),
        "components": [asdict(row) for row in components],
        "feedback_routes": [asdict(row) for row in feedback_routes],
        "target_closed_loop_requirements": target_requirements,
        "next_architecture_step": {
            "name": "ResearchLoopCoordinator.iterate(max_rounds)",
            "description": (
                "Register default repair handlers behind the bounded coordinator: proof gaps should trigger "
                "Formalizer/ProofEngineer search, theory failures should revise estimators or assumptions, "
                "and numerical failures should repair sandboxed implementations."
            ),
            "minimum_acceptance_tests": [
                "a simulation THEORY_OR_PROCEDURE_ISSUE triggers a revised theory plan in round 2",
                "an IMPLEMENTATION_OR_NUMERICAL_ISSUE triggers algorithm repair without changing theory",
                "a FAILED_PROOF_OBLIGATION triggers proof repair or downgrades to FORMAL_GAP with source hits",
                "each round appends immutable trace events and preserves AXLE/kernel evidence",
            ],
        },
    }
    if out_dir is not None:
        write_architecture_audit(payload, out_dir)
    return payload


def write_architecture_audit(payload: dict[str, object], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "architecture_audit_manifest.json"
    report = out_dir / "architecture_audit.md"
    manifest.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report.write_text(_markdown_report(payload), encoding="utf-8")
    return manifest, report


def _markdown_report(payload: dict[str, object]) -> str:
    components = payload["components"]
    routes = payload["feedback_routes"]
    requirements = payload["target_closed_loop_requirements"]
    lines = [
        "# Architecture Audit",
        "",
        f"Status: `{payload['architecture_status']}`",
        "",
        "## Verdict",
        "",
        "- Correct for the current production-safe scaffold: yes.",
        "- Correct for a fully autonomous closed-loop AI statistician: no.",
        "- Implemented feedback mode: queued `next_iteration_agenda`.",
        "- Target feedback mode: live iterative research loop.",
        "",
        "## Implemented Components",
        "",
        "| Component | Status | Limitation | Target delta |",
        "|---|---|---|---|",
    ]
    for row in components:  # type: ignore[assignment]
        lines.append(
            f"| `{row['component']}` | `{row['status']}` | {row['limitation']} | {row['target_delta']} |"
        )
    lines.extend(
        [
            "",
            "## Feedback Routes",
            "",
            "| Trigger | Owner | Action | Execution status |",
            "|---|---|---|---|",
        ]
    )
    for row in routes:  # type: ignore[assignment]
        lines.append(
            f"| `{row['trigger']}` | `{row['owner_agent']}` | `{row['action']}` | `{row['live_execution_status']}` |"
        )
    lines.extend(
        [
            "",
            "## Target Closed-Loop Requirements",
            "",
            "| Requirement | Status | Missing piece |",
            "|---|---|---|",
        ]
    )
    for row in requirements:  # type: ignore[assignment]
        lines.append(f"| {row['requirement']} | `{row['status']}` | {row['missing']} |")
    next_step = payload["next_architecture_step"]  # type: ignore[assignment]
    lines.extend(
        [
            "",
            "## Next Architecture Step",
            "",
            f"`{next_step['name']}`: {next_step['description']}",
            "",
            "Minimum acceptance tests:",
        ]
    )
    for item in next_step["minimum_acceptance_tests"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)

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
    has_live_revision_loop = "for " in run_source and "max_round" in run_source
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
            status="NOT_IMPLEMENTED" if not has_live_revision_loop else "ACHIEVED",
            evidence=("AIStatisticalTheoryLab.run is one-pass" if has_one_pass_run else "run method requires manual inspection",),
            limitation="No iterate(max_rounds) coordinator currently reruns theory planning, formal proof repair, algorithm repair, and simulation after feedback.",
            target_delta="Implement ResearchLoopCoordinator.iterate(max_rounds) with stop conditions: proved/validated, explicit gap, or exhausted budget.",
        ),
    ]

    feedback_routes = [
        FeedbackRoute(
            trigger="FORMAL_GAP",
            owner_agent="formal_verifier",
            action="retrieve_or_build_missing_lean_primitives",
            live_execution_status="QUEUED_NOT_EXECUTED",
            evidence="_build_next_iteration_agenda creates formal_gap:* items",
        ),
        FeedbackRoute(
            trigger="FAILED_PROOF_OBLIGATION",
            owner_agent="formal_verifier",
            action="repair_axiom_verified_proof_or_downgrade_to_gap",
            live_execution_status="QUEUED_NOT_EXECUTED",
            evidence="_build_next_iteration_agenda creates failed_obligation:* items",
        ),
        FeedbackRoute(
            trigger="THEORY_OR_PROCEDURE_ISSUE",
            owner_agent="theory_developer",
            action="revise_estimator_or_theorem_acceptance_rule",
            live_execution_status="QUEUED_NOT_EXECUTED",
            evidence="ResearchSimulator diagnosis escalates biased or invalid statistical behavior to theory_developer",
        ),
        FeedbackRoute(
            trigger="IMPLEMENTATION_OR_NUMERICAL_ISSUE",
            owner_agent="algorithm_engineer",
            action="repair_algorithm_implementation_or_numerical_stability",
            live_execution_status="QUEUED_NOT_EXECUTED",
            evidence="ResearchSimulator diagnosis escalates numerical/implementation issues to algorithm_engineer",
        ),
        FeedbackRoute(
            trigger="ENVIRONMENT_OR_DGP_ISSUE",
            owner_agent="simulator_agent",
            action="implement_or_correct_simulation_environment",
            live_execution_status="QUEUED_NOT_EXECUTED",
            evidence="ResearchSimulator diagnosis escalates simulation-design issues to simulator_agent",
        ),
        FeedbackRoute(
            trigger="NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS",
            owner_agent="research_coordinator",
            action="archive_trace_or_expand_benchmark_stress_tests",
            live_execution_status="QUEUED_NOT_EXECUTED",
            evidence="_build_next_iteration_agenda creates monitor:* items for clean traces",
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
            "status": "NOT_IMPLEMENTED",
            "current_evidence": "SimulationDiagnosis and next_iteration_agenda route the issue.",
            "missing": "Coordinator applies the route, reruns the owner agent, and re-evaluates.",
        },
        {
            "requirement": "Formal proof feedback actively revises assumptions/theorem statements/proof search",
            "status": "NOT_IMPLEMENTED",
            "current_evidence": "Failed proof obligations and FORMAL_GAP rows are queued.",
            "missing": "Automated proof repair, assumption revision, or proof-bank expansion within the same loop.",
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
        "architecture_status": "SCAFFOLD_WITH_QUEUED_FEEDBACK_NOT_LIVE_CLOSED_LOOP",
        "is_current_architecture_correct_for_release_scaffold": True,
        "is_current_architecture_correct_for_full_autonomous_ai_statistician": False,
        "implemented_feedback_mode": "queued_next_iteration_agenda",
        "target_feedback_mode": "live_iterative_research_loop",
        "has_one_pass_research_run": has_one_pass_run,
        "has_live_revision_loop": has_live_revision_loop,
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
                "Execute the next_iteration_agenda: route proof gaps to Formalizer/ProofEngineer, "
                "simulation theory failures to TheoryDeveloper, numerical failures to AlgorithmEngineer, "
                "then rerun proof and simulation until convergence, explicit formal gap, or budget exhaustion."
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

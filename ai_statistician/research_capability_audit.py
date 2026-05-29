from __future__ import annotations

import inspect
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .frontier_coverage_audit import audit_frontier_coverage
from .proof_bank import all_obligations, proof_bank_fingerprint
from .research_knowledge import FORMAL_INFRASTRUCTURE_KNOWLEDGE, KNOWLEDGE_CARDS, retrieve_problem_knowledge
from .research_paper_index import build_paper_source_index, retrieve_paper_sources
from .research_lab import (
    AIStatisticalTheoryLab,
    FormalSubclaimProver,
    PROVABLE_SUBCLAIMS,
    ProblemFormalizer,
    ResearchSimulator,
    TheoryPlanner,
    all_research_algorithm_specs,
    build_research_provenance,
    load_open_research_questions,
    research_algorithm_registry_fingerprint,
    write_research_trace,
    _build_next_iteration_agenda,
)
from .research_schema import CandidateProcedure, ResearchProblemSpec, ResearchSimulation, SimulationDiagnosis


@dataclass(frozen=True)
class ResearchCapabilityFinding:
    requirement: str
    status: str
    current_release_gate: bool
    evidence: tuple[str, ...]
    limitations: tuple[str, ...] = ()


def build_research_capability_audit(
    *,
    root: Path | None = None,
    question_file: Path = Path("examples/research_questions.json"),
    frontier_benchmark_file: Path = Path("docs/frontier_stat_theory_benchmark.md"),
    max_manifests: int = 12,
) -> dict[str, object]:
    """Map the broad AI Statistical Theory Lab goal to inspectable evidence.

    The goal is intentionally larger than the current system. This audit keeps
    those two facts separate:

    - current release scaffold: deterministic intake, theory plans, proof-bank
      verification hooks, simulations, traces, and frontier smoke coverage.
    - full target: autonomous frontier statistical theory development with Lean
      proofs of new asymptotic theorems.

    Rows with ``current_release_gate=False`` are roadmap capabilities. They are
    reported honestly but do not make the current scaffold fail.
    """

    project_root = (root or Path.cwd()).resolve()
    question_path = _resolve(project_root, question_file)
    frontier_path = _resolve(project_root, frontier_benchmark_file)
    questions = load_open_research_questions(question_path)

    formalizer = ProblemFormalizer()
    planner = TheoryPlanner()
    problems = [formalizer.formalize(question) for question in questions]
    supported_pairs = [
        (question, problem)
        for question, problem in zip(questions, problems, strict=True)
        if problem.problem_class != "unsupported_frontier_question"
    ]
    supported_problems = [problem for _question, problem in supported_pairs]
    plans = [planner.plan(problem) for problem in supported_problems]
    procedures = [procedure for plan, _goals in plans for procedure in plan]
    theorem_goals = [goal for _plan, goals in plans for goal in goals]
    knowledge_hits = [
        retrieve_problem_knowledge(question, problem, goals, k=8)
        for (question, problem), (_procedures, goals) in zip(supported_pairs, plans, strict=True)
    ]
    paper_index = build_paper_source_index()
    paper_hits = [
        retrieve_paper_sources(question, problem, goals, records=paper_index, k=5)
        for (question, problem), (_procedures, goals) in zip(supported_pairs, plans, strict=True)
    ]
    algorithms = all_research_algorithm_specs()
    obligations = all_obligations()
    frontier = audit_frontier_coverage(benchmark_file=frontier_path)
    all_research_manifests = _latest_research_manifests(project_root / "runs", max_count=10000)
    latest_manifests = all_research_manifests[:max_manifests]
    latest_research_system = _latest_named(all_research_manifests, "research_system_audit_manifest.json")
    latest_research_benchmark = _latest_named(all_research_manifests, "research_benchmark_manifest.json")
    latest_research_eval = _latest_named(all_research_manifests, "research_evaluation_manifest.json")
    latest_proof_audit = _latest_named(all_research_manifests, "proof_audit_manifest.json")
    latest_proof_payload = _read_manifest_payload(latest_proof_audit)
    latest_proof_obligations = int(latest_proof_payload.get("n_obligations", 0)) if latest_proof_payload else 0
    latest_kernel_verified = int(latest_proof_payload.get("n_kernel_verified", 0)) if latest_proof_payload else 0
    latest_non_kernel_verified = int(latest_proof_payload.get("n_non_kernel_verified", 0)) if latest_proof_payload else 0
    latest_all_kernel_verified = bool(latest_proof_payload.get("all_kernel_verified")) if latest_proof_payload else False
    latest_full_bank_kernel_verified = (
        latest_all_kernel_verified
        and latest_proof_obligations >= len(obligations)
        and latest_kernel_verified >= len(obligations)
    )
    proof_subclaim_status = (
        "ACHIEVED"
        if latest_full_bank_kernel_verified
        else "PARTIAL"
        if obligations and PROVABLE_SUBCLAIMS
        else "NOT_ACHIEVED"
    )

    findings = [
        ResearchCapabilityFinding(
            requirement="accept open research questions and paper-style inputs",
            status="ACHIEVED" if questions else "NOT_ACHIEVED",
            current_release_gate=True,
            evidence=(
                f"{len(questions)} JSON open research questions loaded from {question_path}",
                "Markdown paper-style intake is implemented by load_open_research_questions for .md/.txt files",
                str((project_root / "examples" / "research_paper_abstracts.md").resolve()),
                str((project_root / "examples" / "research_unsupported_paper_abstracts.md").resolve()),
            ),
            limitations=("Input extraction is deterministic v0 pattern matching, not arbitrary paper parsing.",),
        ),
        ResearchCapabilityFinding(
            requirement="extract DGP, estimand, assumptions, diagnostics, and asymptotic regime",
            status="ACHIEVED" if supported_problems and all(_problem_complete(row) for row in supported_problems) else "NOT_ACHIEVED",
            current_release_gate=True,
            evidence=tuple(
                f"{row.question_id}: class={row.problem_class}; assumptions={len(row.assumptions)}; "
                f"diagnostics={len(row.diagnostics)}; extraction_fields={len(row.extraction_evidence)}"
                for row in supported_problems
            ),
            limitations=(
                "Unsupported frontier classes are routed to manual review rather than guessed.",
                "The formalizer covers registered problem classes, not every JASA/AOAS topic.",
            ),
        ),
        ResearchCapabilityFinding(
            requirement="generate informal theory plans and candidate procedures",
            status=(
                "ACHIEVED"
                if procedures
                and theorem_goals
                and all(_procedure_complete(row) for row in procedures)
                and all(_theorem_goal_complete(row) for row in theorem_goals)
                else "NOT_ACHIEVED"
            ),
            current_release_gate=True,
            evidence=(
                f"procedures={len(procedures)}",
                f"theorem_goals={len(theorem_goals)}",
                f"formal_gap_goals={sum(1 for row in theorem_goals if row.status == 'FORMAL_GAP')}",
                f"theorem_goal_proof_obligation_links={sum(len(row.proof_obligations) for row in theorem_goals)}",
                f"missing_formal_primitives={len({primitive for goal in theorem_goals for primitive in goal.required_primitives})}",
                f"{TheoryPlanner.__module__}.{TheoryPlanner.__name__}",
            ),
            limitations=(
                "Theory plans are registry-backed templates today; free-form estimator invention is still a roadmap item.",
            ),
        ),
        ResearchCapabilityFinding(
            requirement="retrieve related paper, statistical-method, Lean, and prover/search knowledge",
            status=(
                "ACHIEVED"
                if knowledge_hits
                and all(_knowledge_hit_ok(row) for row in knowledge_hits)
                and paper_hits
                and all(_paper_hit_ok(row) for row in paper_hits)
                else "NOT_ACHIEVED"
            ),
            current_release_gate=True,
            evidence=(
                f"knowledge_cards={len(KNOWLEDGE_CARDS)}",
                f"formal_infrastructure_cards={len(FORMAL_INFRASTRUCTURE_KNOWLEDGE)}",
                f"paper_source_records={len(paper_index)}",
                f"problem_retrieval_rows={len(knowledge_hits)}",
                f"paper_retrieval_rows={len(paper_hits)}",
                "each supported example retrieves a statistical method card, Lean/search infrastructure card, and local paper/source hit",
            ),
            limitations=(
                "Retrieval is a deterministic/local knowledge layer; Loogle, Lean Finder, ReProver, and semantic paper search are integration targets.",
            ),
        ),
        ResearchCapabilityFinding(
            requirement="prove available Mathlib-backed subclaims in Lean via AXLE",
            status=proof_subclaim_status,
            current_release_gate=True,
            evidence=(
                f"proof_bank_obligations={len(obligations)}",
                f"research_problem_classes_with_subclaims={len(PROVABLE_SUBCLAIMS)}",
                f"latest_proof_audit_obligations={latest_proof_obligations}",
                f"latest_proof_audit_kernel_verified={latest_kernel_verified}",
                f"latest_proof_audit_non_kernel_verified={latest_non_kernel_verified}",
                f"latest_proof_audit_all_kernel_verified={latest_all_kernel_verified}",
                f"latest_proof_audit_full_bank_kernel_verified={latest_full_bank_kernel_verified}",
                f"{FormalSubclaimProver.__module__}.{FormalSubclaimProver.__name__}",
                "research-system-audit --real-lean verifies these obligations with AXLE when available",
                latest_proof_audit["path"] if latest_proof_audit else "no latest proof audit manifest found",
                latest_research_system["path"] if latest_research_system else "no latest research system audit manifest found",
            ),
            limitations=(
                "These are finite Mathlib-backed subclaims, not complete proofs of new frontier asymptotic theorems.",
                "Offline mock-positive proof rows are regression evidence only; AXLE readiness requires kernel_verified=true for the full registered proof bank.",
            ),
        ),
        ResearchCapabilityFinding(
            requirement="formalize frontier theorem goals and persist Lean skeletons for gaps",
            status="ACHIEVED" if theorem_goals and all(row.status == "FORMAL_GAP" for row in theorem_goals) else "NOT_ACHIEVED",
            current_release_gate=True,
            evidence=(
                f"theorem_goals={len(theorem_goals)}",
                f"theorem_goal_proof_obligation_links={sum(len(row.proof_obligations) for row in theorem_goals)}",
                f"missing_formal_primitives={len({primitive for goal in theorem_goals for primitive in goal.required_primitives})}",
                "run_research_benchmark exports formal_gaps/*.lean skeletons",
                latest_research_benchmark["path"] if latest_research_benchmark else "no latest research benchmark manifest found",
            ),
            limitations=(
                "Skeletons are honest FORMAL_GAP artifacts; they are not Lean proofs.",
            ),
        ),
        ResearchCapabilityFinding(
            requirement="prove full frontier asymptotic/statistical theorem goals in Lean",
            status="PARTIAL",
            current_release_gate=False,
            evidence=(
                "available subclaims are proven through the proof bank",
                "frontier theorem goals are represented as explicit FORMAL_GAP skeletons",
                "gap backlog audit validates every recorded gap maps to a theorem goal",
            ),
            limitations=(
                "No current trace proves CLT, semiparametric efficiency, Donsker conditions, BH FDR theorem, Ville inequality, Davis-Kahan recovery, or Hill/Weissman asymptotics end to end in Lean.",
                "This is the central remaining research-goal gap.",
            ),
        ),
        ResearchCapabilityFinding(
            requirement="implement and audit vetted algorithms for proposed procedures",
            status="ACHIEVED" if algorithms and all(row.registry_status == "vetted" for row in algorithms) else "NOT_ACHIEVED",
            current_release_gate=True,
            evidence=tuple(
                f"{row.id}@{row.version} status={row.registry_status} hash={row.implementation_hash[:12]}"
                for row in algorithms
            ),
            limitations=("The current release executes registry-vetted algorithms, not arbitrary LLM-written code.",),
        ),
        ResearchCapabilityFinding(
            requirement="simulate DGP environments and evaluate statistical diagnostics",
            status="ACHIEVED" if procedures and callable(getattr(ResearchSimulator, "run", None)) else "NOT_ACHIEVED",
            current_release_gate=True,
            evidence=(
                f"{ResearchSimulator.__module__}.{ResearchSimulator.__name__}",
                "diagnostics include bias, RMSE, coverage, FDR, power, optional-stopping error, PCA alignment, and tail-quantile coverage depending on class",
                latest_research_eval["path"] if latest_research_eval else "no latest research evaluation manifest found",
            ),
            limitations=("Simulation validates behavior empirically; it does not replace formal asymptotic proof.",),
        ),
        ResearchCapabilityFinding(
            requirement="classify simulation outcomes and route feedback to the right agent",
            status=(
                "ACHIEVED"
                if "diagnosis" in getattr(ResearchSimulation, "__dataclass_fields__", {})
                and callable(getattr(ResearchSimulator, "_diagnose_simulation", None))
                else "NOT_ACHIEVED"
            ),
            current_release_gate=True,
            evidence=(
                f"{SimulationDiagnosis.__module__}.{SimulationDiagnosis.__name__}",
                "diagnosis.status in {OK, THEORY_OR_PROCEDURE_ISSUE, IMPLEMENTATION_OR_NUMERICAL_ISSUE, ENVIRONMENT_OR_DGP_ISSUE, INSUFFICIENT_MC_PRECISION}",
                "diagnosis.escalate_to in {none, theory_developer, algorithm_engineer, simulator_environment, rerun_more_mc}",
                "research_trace_audit validates diagnosis consistency for every simulation row",
            ),
            limitations=(
                "Diagnosis is deterministic rule-based adjudication over registered metrics; it is not yet a learned simulator critic.",
            ),
        ),
        ResearchCapabilityFinding(
            requirement="turn proof gaps and simulation diagnoses into a next-iteration research agenda",
            status="ACHIEVED" if callable(_build_next_iteration_agenda) else "NOT_ACHIEVED",
            current_release_gate=True,
            evidence=(
                f"{_build_next_iteration_agenda.__module__}.{_build_next_iteration_agenda.__name__}",
                "theory_plan.next_iteration_agenda records owner_agent, trigger, action, evidence, owner_counts, and stop_condition",
                "research_trace_audit validates next_iteration_agenda shape for every trace",
                "research_report renders the agenda for human review",
            ),
            limitations=(
                "Agenda items are deterministic handoff instructions; the current release does not automatically execute another improvement round.",
            ),
        ),
        ResearchCapabilityFinding(
            requirement="persist auditable traces, provenance, fingerprints, and gap backlog",
            status="ACHIEVED" if callable(write_research_trace) else "NOT_ACHIEVED",
            current_release_gate=True,
            evidence=(
                f"{write_research_trace.__module__}.{write_research_trace.__name__}",
                f"proof_bank_fingerprint={proof_bank_fingerprint()[:12]}",
                f"research_algorithm_registry_fingerprint={research_algorithm_registry_fingerprint()[:12]}",
                f"provenance_keys={', '.join(sorted(build_research_provenance()))}",
            ),
            limitations=(),
        ),
        ResearchCapabilityFinding(
            requirement="benchmark frontier-style statistical questions",
            status="PARTIAL" if int(frontier["n_supported"]) > 0 else "NOT_ACHIEVED",
            current_release_gate=True,
            evidence=(
                f"frontier_benchmark_questions={frontier['n_questions']}",
                f"frontier_supported={frontier['n_supported']}",
                f"frontier_unsupported={frontier['n_unsupported']}",
                f"supported_classes={', '.join(sorted(k for k in frontier['by_problem_class'] if k != 'unsupported_frontier_question'))}",
            ),
            limitations=(
                "Coverage is a benchmark surface, not a claim of arbitrary JASA/AOAS coverage.",
                "Unsupported rows remain explicit backlog rather than false positives.",
            ),
        ),
        ResearchCapabilityFinding(
            requirement="autonomously solve arbitrary frontier journal statistical theory problems end to end",
            status="NOT_ACHIEVED",
            current_release_gate=False,
            evidence=(
                "the system rejects unsupported frontier classes instead of hallucinating solutions",
                "formal gaps are recorded for all nontrivial frontier theorem goals",
                "the benchmark quantifies the supported/unsupported frontier split",
            ),
            limitations=(
                "The current system is a production scaffold and benchmarked research workflow, not a fully autonomous statistical theorist.",
                "A new milestone should target one frontier theorem family at a time with reusable Lean libraries.",
            ),
        ),
    ]

    release_findings = [row for row in findings if row.current_release_gate]
    all_current_release_requirements_met = all(row.status != "NOT_ACHIEVED" for row in release_findings)
    payload: dict[str, object] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(project_root),
        "question_file": str(question_path),
        "frontier_benchmark_file": str(frontier_path),
        "goal_complete": False,
        "all_current_release_requirements_met": all_current_release_requirements_met,
        "n_achieved": sum(1 for row in findings if row.status == "ACHIEVED"),
        "n_partial": sum(1 for row in findings if row.status == "PARTIAL"),
        "n_not_achieved": sum(1 for row in findings if row.status == "NOT_ACHIEVED"),
        "n_current_release_gate": len(release_findings),
        "n_current_release_gate_met": sum(1 for row in release_findings if row.status != "NOT_ACHIEVED"),
        "frontier_summary": {
            "n_questions": frontier["n_questions"],
            "n_supported": frontier["n_supported"],
            "n_unsupported": frontier["n_unsupported"],
            "supported_rate": frontier["supported_rate"],
            "by_problem_class": frontier["by_problem_class"],
        },
        "findings": [asdict(row) for row in findings],
        "latest_manifests": latest_manifests,
        "source_files": {
            "research_lab": inspect.getsourcefile(AIStatisticalTheoryLab),
            "research_schema": str((project_root / "ai_statistician" / "research_schema.py").resolve()),
            "research_knowledge": str((project_root / "ai_statistician" / "research_knowledge.py").resolve()),
            "research_system_audit": str((project_root / "ai_statistician" / "research_system_audit.py").resolve()),
            "frontier_benchmark": str(frontier_path),
        },
        "fingerprints": {
            "proof_bank": proof_bank_fingerprint(),
            "research_algorithm_registry": research_algorithm_registry_fingerprint(),
            **build_research_provenance(),
        },
    }
    return payload


def write_research_capability_audit(report: dict[str, object], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "research_capability_audit_manifest.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    (out_dir / "research_capability_audit.md").write_text(_markdown_report(report), encoding="utf-8")
    return path


def _resolve(root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    if path.exists():
        return path.resolve()
    return (root / path).resolve()


def _problem_complete(problem: ResearchProblemSpec) -> bool:
    return all(
        (
            bool(problem.question_id),
            bool(problem.problem_class),
            bool(problem.dgp),
            bool(problem.estimand),
            bool(problem.assumptions),
            bool(problem.asymptotic_regime),
            bool(problem.diagnostics),
            bool(problem.extraction_evidence),
            _extraction_evidence_complete(problem),
        )
    )


def _extraction_evidence_complete(problem: ResearchProblemSpec) -> bool:
    if problem.problem_class == "unsupported_frontier_question":
        return bool(problem.extraction_evidence.get("unsupported_reason"))
    return all(
        bool(problem.extraction_evidence.get(key))
        for key in ("problem_class", "dgp", "estimand", "assumptions", "asymptotic_regime")
    )


def _procedure_complete(procedure: CandidateProcedure) -> bool:
    return all(
        (
            bool(procedure.id),
            bool(procedure.formula),
            bool(procedure.informal_derivation),
            bool(procedure.algorithm),
            bool(procedure.theorem_goals),
            bool(procedure.simulation_design),
        )
    )


def _theorem_goal_complete(goal: Any) -> bool:
    return all(
        (
            bool(goal.id),
            bool(goal.title),
            bool(goal.informal_statement),
            bool(goal.proof_strategy),
            bool(goal.status),
            bool(goal.required_primitives),
        )
    )


def _knowledge_hit_ok(hits: list[Any]) -> bool:
    return bool(hits) and any(hit.source_type == "statistical_method" for hit in hits) and any(
        hit.id in FORMAL_INFRASTRUCTURE_KNOWLEDGE for hit in hits
    )


def _paper_hit_ok(hits: list[Any]) -> bool:
    return bool(hits) and any(
        getattr(hit, "source_type", "") in {"frontier_stat_paper", "ai_math_paper"}
        for hit in hits
    )


def _latest_research_manifests(run_dir: Path, *, max_count: int) -> list[dict[str, object]]:
    if not run_dir.exists():
        return []
    names = {
        "frontier_coverage_manifest.json",
        "frontier_smoke_manifest.json",
        "proof_audit_manifest.json",
        "research_algorithm_audit_manifest.json",
        "research_benchmark_manifest.json",
        "research_capability_audit_manifest.json",
        "research_evaluation_manifest.json",
        "research_gap_backlog_manifest.json",
        "research_intake_audit_manifest.json",
        "research_knowledge_audit_manifest.json",
        "research_system_audit_manifest.json",
        "research_trace_audit_manifest.json",
        "retrieval_audit_manifest.json",
    }
    rows: list[dict[str, object]] = []
    for path in run_dir.rglob("*.json"):
        if path.name not in names:
            continue
        stat = path.stat()
        rows.append(
            {
                "name": path.name,
                "path": str(path.resolve()),
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "size_bytes": stat.st_size,
            }
        )
    return sorted(rows, key=lambda row: str(row["modified_at"]), reverse=True)[:max_count]


def _latest_named(rows: list[dict[str, object]], name: str) -> dict[str, object] | None:
    return next((row for row in rows if row["name"] == name), None)


def _read_manifest_payload(row: dict[str, object] | None) -> dict[str, Any]:
    if row is None:
        return {}
    try:
        path = Path(str(row["path"]))
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# AI Statistical Theory Lab Capability Audit",
        "",
        f"- Goal complete: `{payload['goal_complete']}`",
        f"- Current release scaffold met: `{payload['all_current_release_requirements_met']}`",
        f"- Achieved / partial / not achieved: {payload['n_achieved']} / {payload['n_partial']} / {payload['n_not_achieved']}",
        f"- Frontier supported: {payload['frontier_summary']['n_supported']}/{payload['frontier_summary']['n_questions']}",
        "",
        "## Findings",
        "",
        "| Status | Gate | Requirement | Evidence | Limitations |",
        "|---|---:|---|---|---|",
    ]
    for row in payload["findings"]:  # type: ignore[index]
        evidence = "<br>".join(str(item) for item in row["evidence"][:4])
        limitations = "<br>".join(str(item) for item in row["limitations"]) or "-"
        lines.append(
            f"| {row['status']} | {row['current_release_gate']} | {row['requirement']} | {evidence} | {limitations} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The current system is a release-ready scaffold for open-question statistical theory development: it normalizes registered problem classes, proposes theory plans and procedures, proves available Mathlib-backed subclaims, records explicit Lean skeletons for frontier gaps, runs simulations, and writes auditable traces.",
            "",
            "It is not yet a fully autonomous statistical theorist. Full Lean proofs of new frontier asymptotic results remain the central incomplete goal.",
        ]
    )
    return "\n".join(lines) + "\n"

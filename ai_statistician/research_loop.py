from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .formal_source_index import build_formal_source_search_backend
from .research_lab import AIStatisticalTheoryLab
from .research_schema import OpenResearchQuestion, ResearchReport
from .verifier import ProofVerifier


class ResearchLabLike(Protocol):
    async def run(self, question: OpenResearchQuestion) -> ResearchReport:
        ...


LabFactory = Callable[[int, int], ResearchLabLike]


@dataclass(frozen=True)
class LoopConfig:
    max_rounds: int = 2
    n_runs: int = 100
    seed: int = 20260528
    mc_rerun_multiplier: int = 3


class ResearchLoopCoordinator:
    """Execute the research trace feedback agenda for a bounded number of rounds.

    This is the first live-loop layer over ``AIStatisticalTheoryLab``. It does
    not claim to solve arbitrary theory repair yet. Instead it executes the
    agenda routes that are currently safe to automate and records when a route
    needs a stronger TheoryDeveloper, ProofEngineer, AlgorithmEngineer, or
    simulator-extension model.
    """

    def __init__(
        self,
        *,
        proof_verifier: ProofVerifier | None = None,
        formal_source_retriever: Any | None = None,
        n_runs: int = 100,
        seed: int = 20260528,
        lab_factory: LabFactory | None = None,
    ) -> None:
        self.proof_verifier = proof_verifier
        self.formal_source_retriever = formal_source_retriever
        self.n_runs = n_runs
        self.seed = seed
        self.lab_factory = lab_factory

    async def iterate(
        self,
        question: OpenResearchQuestion,
        *,
        max_rounds: int = 2,
        mc_rerun_multiplier: int = 3,
    ) -> dict[str, Any]:
        n_runs = self.n_runs
        rounds: list[dict[str, Any]] = []
        final_report: ResearchReport | None = None
        final_status = "MAX_ROUNDS_REACHED"

        for round_index in range(1, max_rounds + 1):
            lab = self._make_lab(n_runs=n_runs, seed=self.seed + round_index - 1)
            report = await lab.run(question)
            final_report = report
            agenda = _agenda_from_report(report)
            actions = [self._execute_agenda_item(item, report) for item in agenda.get("items", [])]
            round_summary = _round_summary(round_index, n_runs, report, actions)
            rounds.append(round_summary)

            if _only_monitor_actions(actions):
                final_status = "CONVERGED_MONITOR_READY"
                break
            if _should_rerun_more_mc(actions) and round_index < max_rounds:
                n_runs = max(n_runs + 1, n_runs * mc_rerun_multiplier)
                continue
            blocking_status = _blocking_status(actions)
            if blocking_status:
                final_status = blocking_status
                break
        else:
            final_status = "MAX_ROUNDS_REACHED"

        return {
            "loop_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question_id": question.id,
            "question_title": question.title,
            "status": final_status,
            "max_rounds": max_rounds,
            "initial_n_runs": self.n_runs,
            "mc_rerun_multiplier": mc_rerun_multiplier,
            "n_rounds": len(rounds),
            "rounds": rounds,
            "final_report": final_report.to_json() if final_report is not None else None,
            "honesty_boundary": {
                "executes_feedback_agenda": True,
                "free_form_theory_revision": False,
                "arbitrary_lean_proof_search": False,
                "arbitrary_algorithm_generation": False,
            },
        }

    def _make_lab(self, *, n_runs: int, seed: int) -> ResearchLabLike:
        if self.lab_factory is not None:
            return self.lab_factory(n_runs, seed)
        return AIStatisticalTheoryLab(
            proof_verifier=self.proof_verifier,
            formal_source_retriever=self.formal_source_retriever,
            n_runs=n_runs,
            seed=seed,
        )

    def _execute_agenda_item(self, item: dict[str, Any], report: ResearchReport) -> dict[str, Any]:
        trigger = str(item.get("trigger", "UNKNOWN"))
        owner = str(item.get("owner_agent", "research_coordinator"))
        action = str(item.get("action", "triage"))
        base = {
            "id": str(item.get("id", "")),
            "trigger": trigger,
            "owner_agent": owner,
            "action": action,
            "evidence": str(item.get("evidence", "")),
        }
        if trigger == "NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS":
            return {
                **base,
                "execution_status": "EXECUTED_MONITOR",
                "result": "No blocking proof or simulation action remains for this trace.",
            }
        if trigger == "INSUFFICIENT_MC_PRECISION":
            return {
                **base,
                "execution_status": "EXECUTED_RERUN_MORE_MC",
                "result": "Coordinator will rerun the research lab with a larger Monte Carlo budget if round budget remains.",
            }
        if trigger == "FORMAL_GAP":
            target = str(item.get("target_theorem_goal", ""))
            matching_gap = next((row for row in report.formal_subclaims if row.id.endswith(target)), None)
            n_source_hits = 0
            if matching_gap is not None:
                n_source_hits += len(matching_gap.formal_source_hits)
                n_source_hits += sum(len(hits) for hits in matching_gap.primitive_formal_source_hits.values())
            return {
                **base,
                "execution_status": "EXECUTED_RETRIEVAL_REVIEW",
                "result": (
                    "Formal gap was reviewed against attached local Lean/source hits; "
                    "promotion still requires a ProofEngineer to add a verified obligation."
                ),
                "formal_source_hits_reviewed": n_source_hits,
            }
        if trigger == "FAILED_PROOF_OBLIGATION":
            return {
                **base,
                "execution_status": "REQUIRES_PROOF_ENGINEER",
                "result": "A live proof-search/repair engine is required to repair this AXLE failure.",
            }
        if trigger == "THEORY_OR_PROCEDURE_ISSUE":
            return {
                **base,
                "execution_status": "REQUIRES_THEORY_DEVELOPER",
                "result": "A theory revision is required before another simulation run is meaningful.",
            }
        if trigger == "IMPLEMENTATION_OR_NUMERICAL_ISSUE":
            return {
                **base,
                "execution_status": "REQUIRES_ALGORITHM_ENGINEER",
                "result": "A code or numerical-stability repair is required before rerunning the same theory.",
            }
        if trigger == "ENVIRONMENT_OR_DGP_ISSUE":
            return {
                **base,
                "execution_status": "REQUIRES_SIMULATOR_EXTENSION",
                "result": "The simulator environment must be added or corrected before this procedure can be judged.",
            }
        return {
            **base,
            "execution_status": "REQUIRES_COORDINATOR_TRIAGE",
            "result": "Unknown agenda trigger; manual coordinator triage required.",
        }


async def run_research_loop_benchmark(
    questions: list[OpenResearchQuestion],
    out_dir: Path,
    *,
    proof_verifier: ProofVerifier | None = None,
    formal_source_index_path: Path | None = None,
    config: LoopConfig = LoopConfig(),
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    formal_source_retriever = (
        build_formal_source_search_backend(db_path=formal_source_index_path)
        if formal_source_index_path is not None
        else None
    )
    coordinator = ResearchLoopCoordinator(
        proof_verifier=proof_verifier,
        formal_source_retriever=formal_source_retriever,
        n_runs=config.n_runs,
        seed=config.seed,
    )
    results = [
        await coordinator.iterate(
            question,
            max_rounds=config.max_rounds,
            mc_rerun_multiplier=config.mc_rerun_multiplier,
        )
        for question in questions
    ]
    trace_paths = [write_research_loop_trace(row, out_dir) for row in results]
    status_counts: dict[str, int] = {}
    for row in results:
        status = str(row["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    manifest: dict[str, Any] = {
        "loop_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "n_questions": len(questions),
        "config": asdict(config),
        "status_counts": dict(sorted(status_counts.items())),
        "questions": [
            {
                "question_id": row["question_id"],
                "status": row["status"],
                "n_rounds": row["n_rounds"],
                "round_statuses": [round_row["report_status"] for round_row in row["rounds"]],
                "action_statuses": sorted(
                    {
                        action["execution_status"]
                        for round_row in row["rounds"]
                        for action in round_row["actions"]
                    }
                ),
            }
            for row in results
        ],
        "trace_paths": [str(path) for path in trace_paths],
        "formal_source_index_path": str(formal_source_index_path) if formal_source_index_path else "",
        "all_loop_traces_written": all(path.exists() for path in trace_paths),
    }
    (out_dir / "research_loop_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return manifest


def write_research_loop_trace(result: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{result['question_id']}_research_loop.json"
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return path


def _agenda_from_report(report: ResearchReport) -> dict[str, Any]:
    agenda = report.theory_plan.get("next_iteration_agenda", {})
    return agenda if isinstance(agenda, dict) else {"items": []}


def _round_summary(
    round_index: int,
    n_runs: int,
    report: ResearchReport,
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "round": round_index,
        "n_runs": n_runs,
        "report_status": report.status,
        "proved_subclaims": sum(1 for row in report.formal_subclaims if row.status == "PROVED"),
        "formal_gaps": sum(1 for row in report.formal_subclaims if row.status == "FORMAL_GAP"),
        "failed_subclaims": sum(1 for row in report.formal_subclaims if row.status == "FAILED"),
        "simulation_passed": sum(1 for row in report.simulations if row.passed),
        "simulation_total": len(report.simulations),
        "simulation_diagnoses": [
            row.diagnosis.status if row.diagnosis is not None else "missing"
            for row in report.simulations
        ],
        "actions": actions,
    }


def _only_monitor_actions(actions: list[dict[str, Any]]) -> bool:
    return bool(actions) and all(row["execution_status"] == "EXECUTED_MONITOR" for row in actions)


def _should_rerun_more_mc(actions: list[dict[str, Any]]) -> bool:
    return any(row["execution_status"] == "EXECUTED_RERUN_MORE_MC" for row in actions)


def _blocking_status(actions: list[dict[str, Any]]) -> str:
    statuses = {row["execution_status"] for row in actions}
    if "REQUIRES_THEORY_DEVELOPER" in statuses:
        return "REQUIRES_THEORY_DEVELOPER"
    if "REQUIRES_ALGORITHM_ENGINEER" in statuses:
        return "REQUIRES_ALGORITHM_ENGINEER"
    if "REQUIRES_SIMULATOR_EXTENSION" in statuses:
        return "REQUIRES_SIMULATOR_EXTENSION"
    if "REQUIRES_PROOF_ENGINEER" in statuses:
        return "REQUIRES_PROOF_ENGINEER"
    if "REQUIRES_COORDINATOR_TRIAGE" in statuses:
        return "REQUIRES_COORDINATOR_TRIAGE"
    if "EXECUTED_RETRIEVAL_REVIEW" in statuses:
        return "FORMAL_GAPS_REVIEWED"
    return ""

from __future__ import annotations

import json
import inspect
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .fingerprint import stable_hash
from .formal_source_index import build_formal_source_search_backend
from .proof_engineer import DefaultProofEngineer
from .research_lab import AIStatisticalTheoryLab
from .research_schema import OpenResearchQuestion, ResearchReport
from .verifier import ProofVerifier


class ResearchLabLike(Protocol):
    async def run(self, question: OpenResearchQuestion) -> ResearchReport:
        ...


LabFactory = Callable[[int, int], ResearchLabLike]
LiveRepairHandler = Callable[[dict[str, Any], ResearchReport], Any]

LIVE_REPAIR_TASK_TYPE_BY_TRIGGER = {
    "FORMAL_GAP": "proof_bank_expansion_from_formal_gap",
    "FAILED_PROOF_OBLIGATION": "lean_proof_repair_from_axle_error",
    "THEORY_OR_PROCEDURE_ISSUE": "theory_revision_from_simulation_failure",
    "IMPLEMENTATION_OR_NUMERICAL_ISSUE": "algorithm_repair_from_numerical_failure",
    "ENVIRONMENT_OR_DGP_ISSUE": "simulator_environment_extension",
}


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
        repair_handlers: dict[str, LiveRepairHandler] | None = None,
        enable_default_proof_engineer: bool = True,
    ) -> None:
        self.proof_verifier = proof_verifier
        self.formal_source_retriever = formal_source_retriever
        self.n_runs = n_runs
        self.seed = seed
        self.lab_factory = lab_factory
        self.repair_handlers = dict(repair_handlers or {})
        self.enable_default_proof_engineer = enable_default_proof_engineer
        self.default_proof_engineer = (
            DefaultProofEngineer(self.proof_verifier) if enable_default_proof_engineer else None
        )

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
            actions = [await self._execute_agenda_item(item, report) for item in agenda.get("items", [])]
            round_summary = _round_summary(round_index, n_runs, report, actions)
            rounds.append(round_summary)

            if _only_monitor_actions(actions):
                final_status = "CONVERGED_MONITOR_READY"
                break
            if _should_rerun_more_mc(actions) and round_index < max_rounds:
                n_runs = max(n_runs + 1, n_runs * mc_rerun_multiplier)
                continue
            if _should_rerun_after_live_repair(actions) and round_index < max_rounds:
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
                "executes_registered_live_repair_handlers": bool(self.repair_handlers),
                "executes_default_proof_engineer_bridge_handler": self.enable_default_proof_engineer,
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

    async def _execute_agenda_item(self, item: dict[str, Any], report: ResearchReport) -> dict[str, Any]:
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
        live_result = await self._try_live_repair_handler(item, report, base)
        if live_result is not None:
            return live_result
        if trigger == "FORMAL_GAP" and self.default_proof_engineer is not None:
            default_result = await self.default_proof_engineer.repair_formal_gap(item, report)
            if default_result is not None:
                default_action = self._contract_checked_live_result(
                    default_result,
                    trigger=trigger,
                    base=base,
                    handler_name="DefaultProofEngineer",
                )
                default_action.setdefault(
                    "repair_task",
                    _repair_task(
                        report=report,
                        item=item,
                        task_type="proof_bank_expansion_from_formal_gap",
                        prompt=(
                            "Review the DefaultProofEngineer bridge artifact and promote it into the "
                            "smallest reusable Lean theorem or theory-plan obligation that reduces this FORMAL_GAP."
                        ),
                        acceptance_criteria=(
                            "bridge artifact is AXLE verify_proof checked when kernel verification is required",
                            "the theory plan records the proof-bank bridge as a reusable dependency",
                            "the frontier theorem still retains explicit gaps for primitives not covered by the bridge",
                        ),
                        context={
                            "target_theorem_goal": item.get("target_theorem_goal", ""),
                            "required_primitives": item.get("required_primitives", []),
                            "default_proof_engineer_status": default_action.get("execution_status", ""),
                        },
                    ),
                )
                return default_action
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
                "repair_task": _repair_task(
                    report=report,
                    item=item,
                    task_type="proof_bank_expansion_from_formal_gap",
                    prompt=(
                        "Promote this FORMAL_GAP into the smallest reusable Lean theorem. "
                        "Use attached Mathlib/StatInference/source hits and existing proof-bank bridges; "
                        "do not submit a placeholder or sorry proof."
                    ),
                    acceptance_criteria=(
                        "Lean statement has no h_frontier_missing placeholder assumptions",
                        "proof body passes AXLE verify_proof with kernel_verified=true",
                        "new obligation is reusable by at least one formalization target",
                        "formal-source hits or proof-bank dependencies are recorded",
                    ),
                    context={
                        "target_theorem_goal": target,
                        "formal_source_hits_reviewed": n_source_hits,
                        "required_primitives": item.get("required_primitives", []),
                    },
                ),
            }
        if trigger == "FAILED_PROOF_OBLIGATION":
            return {
                **base,
                "execution_status": "REQUIRES_PROOF_ENGINEER",
                "result": "A live proof-search/repair engine is required to repair this AXLE failure.",
                "repair_task": _repair_task(
                    report=report,
                    item=item,
                    task_type="lean_proof_repair_from_axle_error",
                    prompt=(
                        "Repair the failed Lean proof obligation using verifier errors, expected premises, "
                        "retrieved declarations, and Mathlib-compatible proof terms."
                    ),
                    acceptance_criteria=(
                        "repaired proof passes AXLE verify_proof",
                        "no sorry/admit/axiom/unsafe placeholder is introduced",
                        "proof dependencies are recorded for proof-bank audit",
                    ),
                    context={"required_primitives": item.get("required_primitives", [])},
                ),
            }
        if trigger == "THEORY_OR_PROCEDURE_ISSUE":
            return {
                **base,
                "execution_status": "REQUIRES_THEORY_DEVELOPER",
                "result": "A theory revision is required before another simulation run is meaningful.",
                "repair_task": _repair_task(
                    report=report,
                    item=item,
                    task_type="theory_revision_from_simulation_failure",
                    prompt=(
                        "Revise the statistical theory plan. Decide whether the estimand, estimator, "
                        "standard error, assumptions, theorem statement, or acceptance rule is wrong; "
                        "then produce a revised procedure/theorem plan ready for formalization and simulation."
                    ),
                    acceptance_criteria=(
                        "revised theorem statement explains the failed diagnostics",
                        "revised procedure has a registered or sandboxable algorithm path",
                        "simulation diagnostics are expected to pass under the declared DGP/stress tests",
                        "new assumptions are explicit and not silently stronger than the input problem",
                    ),
                    context={
                        "target_procedure": item.get("target_procedure", ""),
                        "failed_diagnostics": item.get("failed_diagnostics", []),
                        "failed_stress_tests": item.get("failed_stress_tests", []),
                        "metric_evidence_keys": item.get("metric_evidence_keys", []),
                    },
                ),
            }
        if trigger == "IMPLEMENTATION_OR_NUMERICAL_ISSUE":
            return {
                **base,
                "execution_status": "REQUIRES_ALGORITHM_ENGINEER",
                "result": "A code or numerical-stability repair is required before rerunning the same theory.",
                "repair_task": _repair_task(
                    report=report,
                    item=item,
                    task_type="algorithm_repair_from_numerical_failure",
                    prompt=(
                        "Repair the implementation or numerical-stability issue while preserving the "
                        "current statistical estimand and theorem plan."
                    ),
                    acceptance_criteria=(
                        "implementation hash changes or numerical guard is justified",
                        "property/simulation test reproduces the old failure before repair",
                        "rerun has finite metrics and fewer failed replicates",
                    ),
                    context={
                        "target_procedure": item.get("target_procedure", ""),
                        "failed_diagnostics": item.get("failed_diagnostics", []),
                    },
                ),
            }
        if trigger == "ENVIRONMENT_OR_DGP_ISSUE":
            return {
                **base,
                "execution_status": "REQUIRES_SIMULATOR_EXTENSION",
                "result": "The simulator environment must be added or corrected before this procedure can be judged.",
                "repair_task": _repair_task(
                    report=report,
                    item=item,
                    task_type="simulator_environment_extension",
                    prompt=(
                        "Implement or correct the DGP/procedure simulator so the proposed statistical "
                        "procedure can be judged under the declared assumptions and stress tests."
                    ),
                    acceptance_criteria=(
                        "new simulator covers the declared DGP and stress tests",
                        "metrics include every requested diagnostic or documented alias",
                        "environment failures are no longer classified as simulator_missing",
                    ),
                    context={
                        "target_procedure": item.get("target_procedure", ""),
                        "failed_diagnostics": item.get("failed_diagnostics", []),
                        "failed_stress_tests": item.get("failed_stress_tests", []),
                    },
                ),
            }
        return {
            **base,
            "execution_status": "REQUIRES_COORDINATOR_TRIAGE",
            "result": "Unknown agenda trigger; manual coordinator triage required.",
            "repair_task": _repair_task(
                report=report,
                item=item,
                task_type="coordinator_triage_unknown_trigger",
                prompt="Classify this unknown research-loop agenda item and route it to the correct agent.",
                acceptance_criteria=("trigger is mapped to an owner agent", "a new loop handler or explicit limitation is added"),
                context={},
            ),
        }

    async def _try_live_repair_handler(
        self,
        item: dict[str, Any],
        report: ResearchReport,
        base: dict[str, Any],
    ) -> dict[str, Any] | None:
        trigger = str(item.get("trigger", ""))
        owner = str(item.get("owner_agent", ""))
        handler = self.repair_handlers.get(trigger) or self.repair_handlers.get(owner)
        if handler is None:
            return None
        raw = handler(item, report)
        if inspect.isawaitable(raw):
            raw = await raw
        if not isinstance(raw, dict):
            return {
                **base,
                "execution_status": "REPAIR_HANDLER_INVALID_OUTPUT",
                "result": "Registered live repair handler did not return a dictionary.",
                "rerun_requested": False,
            }
        return self._contract_checked_live_result(raw, trigger=trigger, base=base, handler_name=handler.__class__.__name__)

    def _contract_checked_live_result(
        self,
        raw: dict[str, Any],
        *,
        trigger: str,
        base: dict[str, Any],
        handler_name: str,
    ) -> dict[str, Any]:
        task_type = str(raw.get("task_type") or LIVE_REPAIR_TASK_TYPE_BY_TRIGGER.get(trigger, ""))
        contract = _output_contract(task_type)
        contract_errors = _validate_live_repair_output(raw, task_type)
        if contract_errors:
            return {
                **base,
                **raw,
                "execution_status": "REPAIR_HANDLER_CONTRACT_FAILED",
                "result": "Registered live repair handler output failed its repair contract.",
                "rerun_requested": False,
                "live_repair_task_type": task_type,
                "repair_contract": contract,
                "repair_contract_ok": False,
                "repair_contract_errors": contract_errors,
                "live_repair_handler": raw.get("live_repair_handler", handler_name),
            }
        execution_status = str(raw.get("execution_status", "EXECUTED_LIVE_REPAIR"))
        result = str(raw.get("result", "Registered live repair handler executed."))
        return {
            **base,
            **raw,
            "execution_status": execution_status,
            "result": result,
            "rerun_requested": bool(raw.get("rerun_requested", False)),
            "live_repair_task_type": task_type,
            "repair_contract": contract,
            "repair_contract_ok": True,
            "repair_contract_errors": [],
            "live_repair_handler": raw.get("live_repair_handler", handler_name),
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
    repair_tasks = _repair_tasks_from_results(results)
    repair_task_path = out_dir / "research_loop_repair_tasks.jsonl"
    _write_jsonl(repair_task_path, repair_tasks)
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
        "repair_tasks_jsonl": str(repair_task_path),
        "n_repair_tasks": len(repair_tasks),
        "repair_tasks_by_agent": _count_by_key(repair_tasks, "owner_agent"),
        "repair_tasks_by_type": _count_by_key(repair_tasks, "task_type"),
        "formal_source_index_path": str(formal_source_index_path) if formal_source_index_path else "",
        "all_loop_traces_written": all(path.exists() for path in trace_paths),
        "all_repair_tasks_exported": repair_task_path.exists(),
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


def _repair_task(
    *,
    report: ResearchReport,
    item: dict[str, Any],
    task_type: str,
    prompt: str,
    acceptance_criteria: tuple[str, ...],
    context: dict[str, Any],
) -> dict[str, Any]:
    source_action_id = str(item.get("id", ""))
    owner = str(item.get("owner_agent", "research_coordinator"))
    payload = {
        "schema_version": 1,
        "task_id": (
            f"loop_repair:{owner}:{task_type}:"
            f"{stable_hash([report.question.id, source_action_id, task_type])[:12]}"
        ),
        "source_action_id": source_action_id,
        "question_id": report.question.id,
        "problem_class": report.problem.problem_class,
        "owner_agent": owner,
        "task_type": task_type,
        "trigger": str(item.get("trigger", "")),
        "priority": str(item.get("priority", "medium")),
        "prompt": prompt,
        "evidence": str(item.get("evidence", "")),
        "context": {
            "dgp": report.problem.dgp,
            "estimand": report.problem.estimand,
            "assumptions": list(report.problem.assumptions),
            "asymptotic_regime": report.problem.asymptotic_regime,
            **context,
        },
        "acceptance_criteria": list(acceptance_criteria),
        "output_contract": _output_contract(task_type),
    }
    return payload


def _output_contract(task_type: str) -> dict[str, Any]:
    if task_type == "proof_bank_expansion_from_formal_gap":
        return {
            "required_fields": [
                "lean_statement",
                "proof_body",
                "expected_lemmas",
                "proof_dependencies",
                "reuse_targets",
            ],
            "required_gate": "AXLE verify_proof kernel_verified=true",
        }
    if task_type == "lean_proof_repair_from_axle_error":
        return {
            "required_fields": ["repaired_proof_body", "error_analysis", "proof_dependencies"],
            "required_gate": "AXLE verify_proof kernel_verified=true",
        }
    if task_type == "theory_revision_from_simulation_failure":
        return {
            "required_fields": [
                "revised_procedure",
                "revised_theorem_goals",
                "assumption_delta",
                "expected_simulation_delta",
            ],
            "required_gate": "rerun research-loop or research-benchmark without the same simulation diagnosis",
        }
    if task_type == "algorithm_repair_from_numerical_failure":
        return {
            "required_fields": ["patch_summary", "implementation_hash", "reproduction_test", "rerun_metrics"],
            "required_gate": "algorithm audit plus finite simulation metrics",
        }
    if task_type == "simulator_environment_extension":
        return {
            "required_fields": ["dgp_generator", "diagnostic_metrics", "stress_test_coverage", "validation_run"],
            "required_gate": "research trace audit accepts the new simulator row",
        }
    return {
        "required_fields": ["classification", "owner_agent", "proposed_handler"],
        "required_gate": "architecture audit documents the new route",
    }


def _validate_live_repair_output(raw: dict[str, Any], task_type: str) -> list[str]:
    errors: list[str] = []
    if not task_type:
        errors.append("live repair task_type missing and could not be inferred from trigger")
    artifact = raw.get("repair_artifact")
    if not isinstance(artifact, dict):
        errors.append("repair_artifact must be an object")
        artifact = {}
    contract = _output_contract(task_type)
    required_fields = [str(row) for row in contract.get("required_fields", []) if str(row)]
    for field in required_fields:
        if field not in artifact or artifact.get(field) in (None, "", [], {}):
            errors.append(f"repair_artifact missing required field: {field}")
    if raw.get("rerun_requested") and errors:
        errors.append("rerun_requested=true is forbidden until the repair contract is satisfied")
    if task_type in {"proof_bank_expansion_from_formal_gap", "lean_proof_repair_from_axle_error"}:
        verified = artifact.get("kernel_verified") is True or raw.get("kernel_verified") is True
        if raw.get("rerun_requested") and not verified:
            errors.append("proof repair rerun requires kernel_verified=true")
    return errors


def _repair_tasks_from_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for result in results:
        for round_row in result.get("rounds", []):
            for action in round_row.get("actions", []):
                task = action.get("repair_task")
                if isinstance(task, dict):
                    tasks.append(task)
    return tasks


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")


def _count_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


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


def _should_rerun_after_live_repair(actions: list[dict[str, Any]]) -> bool:
    return any(bool(row.get("rerun_requested")) for row in actions)


def _blocking_status(actions: list[dict[str, Any]]) -> str:
    statuses = {row["execution_status"] for row in actions}
    if "REPAIR_HANDLER_INVALID_OUTPUT" in statuses or "REPAIR_HANDLER_CONTRACT_FAILED" in statuses:
        return "REPAIR_HANDLER_CONTRACT_FAILED"
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
    if "EXECUTED_PROOF_BANK_BRIDGE_REPAIR" in statuses:
        return "FORMAL_GAPS_BRIDGED"
    if "EXECUTED_RETRIEVAL_REVIEW" in statuses:
        return "FORMAL_GAPS_REVIEWED"
    return ""

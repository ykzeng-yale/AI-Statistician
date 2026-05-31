from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .research_lab import ResearchSimulator
from .research_schema import CandidateProcedure, ResearchAlgorithmSpec, ResearchProblemSpec


@dataclass(frozen=True)
class FrontierSimulationRerunRow:
    item_id: str
    question_id: str
    problem_class: str
    procedure_id: str
    original_status: str
    original_failed_diagnostics: tuple[str, ...]
    rerun_status: str
    rerun_escalate_to: str
    rerun_failed_diagnostics: tuple[str, ...]
    resolved: bool
    new_owner_agent: str
    action: str
    evidence: str
    trace_path: str
    ok: bool
    errors: tuple[str, ...] = ()


def audit_frontier_simulation_reruns(
    triage_manifest: Path,
    out_dir: Path | None = None,
    *,
    n_runs: int = 60,
    seed: int = 20260531,
) -> dict[str, object]:
    """Rerun simulator-agent frontier triage items with a larger MC budget."""

    manifest_errors: list[str] = []
    triage = _read_json(triage_manifest, manifest_errors)
    rows: list[FrontierSimulationRerunRow] = []
    for item in triage.get("rows", []) if isinstance(triage.get("rows"), list) else []:
        if not isinstance(item, dict):
            continue
        if item.get("owner_agent") != "simulator_agent" or item.get("trigger") != "SIMULATION_FLAGGED":
            continue
        rows.append(_rerun_item(item, n_runs=n_runs, seed=seed))

    by_status = Counter(row.rerun_status for row in rows)
    by_owner = Counter(row.new_owner_agent for row in rows)
    by_action = Counter(row.action for row in rows)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "triage_manifest": str(triage_manifest),
        "config": {
            "n_runs": n_runs,
            "seed": seed,
        },
        "n_items": len(rows),
        "n_resolved": sum(1 for row in rows if row.resolved),
        "n_still_flagged": sum(1 for row in rows if not row.resolved and row.ok),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not manifest_errors and all(row.ok for row in rows),
        "all_resolved": all(row.resolved for row in rows),
        "manifest_errors": manifest_errors,
        "by_rerun_status": dict(sorted(by_status.items())),
        "by_new_owner_agent": dict(sorted(by_owner.items())),
        "by_action": dict(sorted(by_action.items())),
        "rerun_fingerprint": stable_hash([asdict(row) for row in rows]),
        "rows": [asdict(row) for row in rows],
        "limitations": [
            "reruns use the current vetted simulator, not arbitrary generated code",
            "resolved means the higher-budget simulation diagnosis is OK, not that the full frontier theorem is proved",
            "still-flagged rows are routed to the next owner agent for theory or algorithm revision",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "frontier_simulation_rerun_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "frontier_simulation_rerun.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _rerun_item(item: dict[str, Any], *, n_runs: int, seed: int) -> FrontierSimulationRerunRow:
    errors: list[str] = []
    trace_path = Path(str(item.get("trace_path", "")))
    trace = _read_json(trace_path, errors)
    procedure_id = str(item.get("procedure_id", ""))
    question_id = str(item.get("question_id", trace_path.stem))
    problem_class = str(item.get("problem_class", ""))
    original_status = str(item.get("diagnosis_status", ""))
    original_failed = tuple(str(row) for row in item.get("failed_diagnostics", []) or [])
    rerun_status = ""
    rerun_escalate_to = ""
    rerun_failed: tuple[str, ...] = ()
    resolved = False
    new_owner = "simulator_agent"
    action = "fix_trace_or_triage_metadata_before_rerun"
    evidence = ""

    if trace:
        try:
            problem = ResearchProblemSpec(**trace["problem"])
            problem_class = problem.problem_class or problem_class
            procedure = _procedure_from_trace(trace, procedure_id)
            simulation = ResearchSimulator(n_runs=n_runs, seed=seed).run(problem, [procedure])[0]
            diagnosis = simulation.diagnosis
            rerun_status = diagnosis.status if diagnosis is not None else ("OK" if simulation.passed else "UNKNOWN")
            rerun_escalate_to = diagnosis.escalate_to if diagnosis is not None else "none"
            rerun_failed = tuple(diagnosis.failed_diagnostics if diagnosis is not None else ())
            resolved = bool(simulation.passed)
            new_owner, action = _route_rerun_result(resolved, rerun_escalate_to, rerun_failed)
            evidence = _simulation_evidence(simulation.metrics, diagnosis)
        except Exception as exc:
            errors.append(f"rerun failed: {type(exc).__name__}: {exc}")

    return FrontierSimulationRerunRow(
        item_id=str(item.get("item_id", "")),
        question_id=question_id,
        problem_class=problem_class,
        procedure_id=procedure_id,
        original_status=original_status,
        original_failed_diagnostics=original_failed,
        rerun_status=rerun_status,
        rerun_escalate_to=rerun_escalate_to,
        rerun_failed_diagnostics=rerun_failed,
        resolved=resolved,
        new_owner_agent=new_owner,
        action=action,
        evidence=evidence,
        trace_path=str(trace_path),
        ok=not errors and bool(procedure_id) and bool(rerun_status),
        errors=tuple(errors),
    )


def _procedure_from_trace(trace: dict[str, Any], procedure_id: str) -> CandidateProcedure:
    for procedure in trace.get("procedures", []) or []:
        if not isinstance(procedure, dict) or str(procedure.get("id", "")) != procedure_id:
            continue
        payload = dict(procedure)
        if isinstance(payload.get("algorithm_spec"), dict):
            payload["algorithm_spec"] = ResearchAlgorithmSpec(**payload["algorithm_spec"])
        return CandidateProcedure(**payload)
    raise ValueError(f"procedure {procedure_id!r} not found in trace")


def _route_rerun_result(
    resolved: bool,
    escalate_to: str,
    failed_diagnostics: tuple[str, ...],
) -> tuple[str, str]:
    if resolved:
        return "research_coordinator", "mark_simulation_flag_resolved_after_higher_budget_rerun"
    if escalate_to == "theory_developer" or {"bias", "relative_bias", "coverage_95", "se_ratio"} & set(failed_diagnostics):
        return "theory_developer", "revise_theory_or_procedure_after_higher_budget_simulation_failure"
    if escalate_to == "algorithm_engineer":
        return "algorithm_engineer", "inspect_algorithm_after_higher_budget_simulation_failure"
    return "simulator_agent", "schedule_deeper_stress_sweep_or_seed_sensitivity_eval"


def _simulation_evidence(metrics: dict[str, float], diagnosis: Any | None) -> str:
    selected = []
    for key in (
        "n_runs",
        "bias",
        "relative_bias",
        "rmse",
        "coverage_95",
        "se_ratio",
        "selection_accuracy",
        "false_discovery_rate",
        "active_recall",
    ):
        if key in metrics:
            selected.append(f"{key}={metrics[key]}")
    if diagnosis is not None and getattr(diagnosis, "rationale", ""):
        selected.insert(0, str(diagnosis.rationale))
    return "; ".join(selected)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("rows", [])
    lines = [
        "# Frontier Simulation Rerun Audit",
        "",
        "This audit reruns simulator-agent frontier triage items with a larger",
        "Monte Carlo budget and re-routes remaining failures to the correct owner.",
        "",
        f"- Triage manifest: `{payload.get('triage_manifest')}`",
        f"- Rerun items: {payload.get('n_ok')}/{payload.get('n_items')} audit-clean",
        f"- Resolved: {payload.get('n_resolved')}",
        f"- Still flagged: {payload.get('n_still_flagged')}",
        f"- All resolved: {payload.get('all_resolved')}",
        f"- Fingerprint: `{payload.get('rerun_fingerprint')}`",
        "",
        "## Owner Counts After Rerun",
        "",
    ]
    by_owner = payload.get("by_new_owner_agent", {})
    if isinstance(by_owner, dict):
        for owner, count in by_owner.items():
            lines.append(f"- `{owner}`: {count}")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Resolved | New owner | Status | Question | Procedure | Evidence |",
            "|---|---|---|---|---|---|",
        ]
    )
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"| {row.get('resolved')} | `{row.get('new_owner_agent')}` | `{row.get('rerun_status')}` | "
                f"`{row.get('question_id')}` | `{row.get('procedure_id')}` | {str(row.get('evidence', ''))[:120]} |"
            )
    return "\n".join(lines) + "\n"

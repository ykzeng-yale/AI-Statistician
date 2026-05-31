from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


@dataclass(frozen=True)
class FrontierTheoryRevisionQueueRow:
    task_id: str
    question_id: str
    problem_class: str
    procedure_id: str
    trigger: str
    priority: str
    failure_class: str
    evidence: str
    target_theorem_goals: tuple[str, ...]
    revised_procedure: str
    revised_theorem_goals: tuple[str, ...]
    assumption_delta: tuple[str, ...]
    next_formal_obligations: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    trace_path: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_frontier_theory_revision_queue(
    simulation_rerun_manifest: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export theory-development tasks from still-flagged frontier reruns."""

    manifest_errors: list[str] = []
    rerun = _read_json(simulation_rerun_manifest, manifest_errors)
    rows: list[FrontierTheoryRevisionQueueRow] = []
    for item in rerun.get("rows", []) if isinstance(rerun.get("rows"), list) else []:
        if not isinstance(item, dict):
            continue
        if item.get("new_owner_agent") != "theory_developer" or bool(item.get("resolved")):
            continue
        rows.append(_revision_row(item))

    by_problem_class = Counter(row.problem_class for row in rows)
    by_failure_class = Counter(row.failure_class for row in rows)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "simulation_rerun_manifest": str(simulation_rerun_manifest),
        "n_tasks": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not manifest_errors and all(row.ok for row in rows),
        "manifest_errors": manifest_errors,
        "by_problem_class": dict(sorted(by_problem_class.items())),
        "by_failure_class": dict(sorted(by_failure_class.items())),
        "queue_fingerprint": stable_hash([asdict(row) for row in rows]),
        "rows": [asdict(row) for row in rows],
        "limitations": [
            "revision tasks are scoped theory-development proposals, not applied registry changes",
            "new formal obligations are theorem targets for future AXLE/Lean proof-bank expansion",
            "acceptance criteria require a later implementation and rerun before claiming improvement",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "frontier_theory_revision_queue_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "frontier_theory_revision_queue.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "frontier_theory_revision_queue.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _revision_row(item: dict[str, Any]) -> FrontierTheoryRevisionQueueRow:
    errors: list[str] = []
    trace_path = Path(str(item.get("trace_path", "")))
    trace = _read_json(trace_path, errors)
    question_id = str(item.get("question_id", trace_path.stem))
    problem_class = str(item.get("problem_class", ""))
    procedure_id = str(item.get("procedure_id", ""))
    failed_diagnostics = tuple(str(row) for row in item.get("rerun_failed_diagnostics", []) or [])
    procedure_goals = _procedure_theorem_goals(trace, procedure_id)
    if not procedure_goals:
        procedure_goals = tuple(str(row.get("id", "")) for row in trace.get("theorem_goals", []) if isinstance(row, dict))
    artifact = _revision_artifact(
        procedure_id=procedure_id,
        theorem_goals=procedure_goals,
        failed_diagnostics=failed_diagnostics,
    )
    if not procedure_id:
        errors.append("procedure_id missing")
    if not failed_diagnostics:
        errors.append("rerun_failed_diagnostics missing")
    if not procedure_goals:
        errors.append("target_theorem_goals missing")
    return FrontierTheoryRevisionQueueRow(
        task_id=f"frontier_theory_revision:{question_id}:{procedure_id}",
        question_id=question_id,
        problem_class=problem_class,
        procedure_id=procedure_id,
        trigger="HIGHER_BUDGET_SIMULATION_STILL_FLAGGED",
        priority="high",
        failure_class=str(artifact["failure_class"]),
        evidence=str(item.get("evidence", "")),
        target_theorem_goals=procedure_goals,
        revised_procedure=str(artifact["revised_procedure"]),
        revised_theorem_goals=tuple(str(row) for row in artifact["revised_theorem_goals"]),
        assumption_delta=tuple(str(row) for row in artifact["assumption_delta"]),
        next_formal_obligations=tuple(str(row) for row in artifact["next_formal_obligations"]),
        acceptance_criteria=tuple(str(row) for row in artifact["acceptance_criteria"]),
        trace_path=str(trace_path),
        ok=not errors,
        errors=tuple(errors),
    )


def _procedure_theorem_goals(trace: dict[str, Any], procedure_id: str) -> tuple[str, ...]:
    for procedure in trace.get("procedures", []) or []:
        if not isinstance(procedure, dict) or str(procedure.get("id", "")) != procedure_id:
            continue
        return tuple(str(row) for row in procedure.get("theorem_goals", []) or [] if str(row))
    return ()


def _revision_artifact(
    *,
    procedure_id: str,
    theorem_goals: tuple[str, ...],
    failed_diagnostics: tuple[str, ...],
) -> dict[str, object]:
    diagnostic_text = " ".join(failed_diagnostics).lower()
    if any(token in diagnostic_text for token in ("selection", "screen", "support", "recall", "subspace")):
        return {
            "revised_procedure": f"{procedure_id}:threshold_calibrated_screening_variant",
            "revised_theorem_goals": [
                *[f"{goal}_selection_consistency" for goal in theorem_goals],
                "screening_selection_accuracy_under_signal_separation",
                "false_discovery_control_for_screening_rule",
                "subspace_alignment_under_nuisance_dependence",
            ],
            "assumption_delta": [
                "add an explicit signal-separation or margin condition for active coordinates",
                "calibrate the screening threshold against nuisance predictor dependence and dimensionality",
                "separate support-recovery accuracy from RMSE and interval-coverage claims",
            ],
            "next_formal_obligations": [
                "screening_statistic_concentration",
                "signal_margin_implies_active_selection",
                "inactive_coordinate_union_bound",
                "selection_accuracy_lower_bound_from_support_events",
            ],
            "acceptance_criteria": [
                "higher-budget rerun clears the registered selection_accuracy threshold",
                "false_discovery_rate does not increase materially after threshold calibration",
                "new theorem goals remain marked as FORMAL_GAP until AXLE proof obligations are added",
            ],
            "failure_class": "selection_or_screening_failure",
        }
    return {
        "revised_procedure": f"{procedure_id}:diagnostic_revised_variant",
        "revised_theorem_goals": [
            *[f"{goal}_diagnostic_alignment" for goal in theorem_goals],
            "diagnostic_failure_decomposition",
            "revised_acceptance_rule_under_declared_dgp",
        ],
        "assumption_delta": [
            "make the theorem/simulation acceptance rule explicit for the failed diagnostic",
            "identify whether the failure is theory, implementation, or simulator-environment driven",
        ],
        "next_formal_obligations": [
            "diagnostic_event_formalization",
            "acceptance_rule_soundness",
        ],
        "acceptance_criteria": [
            "the same simulator diagnostic no longer fails after applying the revision",
            "the revised theorem plan exposes any still-missing Lean primitive as a formal gap",
        ],
        "failure_class": "generic_theory_or_procedure_failure",
    }


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
        "# Frontier Theory Revision Queue",
        "",
        "This queue converts higher-budget simulation failures into scoped",
        "TheoryDeveloper tasks with revised theorem goals and formal obligations.",
        "",
        f"- Simulation rerun manifest: `{payload.get('simulation_rerun_manifest')}`",
        f"- Tasks: {payload.get('n_ok')}/{payload.get('n_tasks')} audit-clean",
        f"- Fingerprint: `{payload.get('queue_fingerprint')}`",
        "",
        "## Rows",
        "",
        "| Question | Procedure | Failure class | Next formal obligations |",
        "|---|---|---|---|",
    ]
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            obligations = ", ".join(str(item) for item in row.get("next_formal_obligations", [])[:4])
            lines.append(
                f"| `{row.get('question_id')}` | `{row.get('procedure_id')}` | "
                f"`{row.get('failure_class')}` | {obligations} |"
            )
    return "\n".join(lines) + "\n"

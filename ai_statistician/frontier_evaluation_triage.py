from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


@dataclass(frozen=True)
class FrontierEvaluationTriageItem:
    item_id: str
    question_id: str
    topic: str
    problem_class: str
    owner_agent: str
    trigger: str
    priority: str
    action: str
    evidence: str
    trace_path: str
    expected_result: str = ""
    missing_terms: tuple[str, ...] = ()
    coverage: float = 0.0
    procedure_id: str = ""
    diagnosis_status: str = ""
    failed_diagnostics: tuple[str, ...] = ()
    failed_stress_tests: tuple[str, ...] = ()
    ok: bool = True
    errors: tuple[str, ...] = ()


def audit_frontier_evaluation_triage(
    run_dir: Path,
    theory_target_manifest: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Build an actionable queue from frontier theory-target and simulation misses.

    The all-frontier benchmark intentionally exposes partial capability: some
    expected theory targets are not recovered, and some simulations are flagged
    under the selected Monte Carlo budget. This audit turns those limitations
    into owner-routed work items so the next run can improve the right subsystem
    instead of burying the evidence in separate manifests.
    """

    manifest_errors: list[str] = []
    theory_payload = _read_json(theory_target_manifest, manifest_errors)
    benchmark_manifest = _read_json(run_dir / "research_benchmark_manifest.json", manifest_errors)

    rows: list[FrontierEvaluationTriageItem] = []
    if isinstance(theory_payload.get("rows"), list):
        rows.extend(_theory_target_items(theory_payload["rows"]))
    else:
        manifest_errors.append("theory target manifest rows missing")

    summaries = (
        benchmark_manifest.get("questions", [])
        if isinstance(benchmark_manifest.get("questions"), list)
        else []
    )
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        question_id = str(summary.get("question", ""))
        if not question_id:
            manifest_errors.append("research benchmark summary missing question id")
            continue
        trace_path = run_dir / f"{question_id}.json"
        trace = _read_json(trace_path, manifest_errors)
        if trace:
            rows.extend(_simulation_items(trace, trace_path))

    by_owner = Counter(row.owner_agent for row in rows)
    by_trigger = Counter(row.trigger for row in rows)
    by_priority = Counter(row.priority for row in rows)
    by_problem_class = Counter(row.problem_class for row in rows)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "theory_target_manifest": str(theory_target_manifest),
        "n_items": len(rows),
        "n_theory_target_misses": sum(1 for row in rows if row.trigger == "THEORY_TARGET_MISS"),
        "n_simulation_flags": sum(1 for row in rows if row.trigger == "SIMULATION_FLAGGED"),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not manifest_errors and all(row.ok for row in rows),
        "manifest_errors": manifest_errors,
        "by_owner": dict(sorted(by_owner.items())),
        "by_trigger": dict(sorted(by_trigger.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_problem_class": dict(sorted(by_problem_class.items())),
        "triage_fingerprint": stable_hash([asdict(row) for row in rows]),
        "rows": [asdict(row) for row in rows],
        "limitations": [
            "theory target misses are token-overlap diagnostics, not semantic proof failures",
            "simulation flags may reflect low Monte Carlo budget rather than a wrong estimator",
            "owner routing is deterministic triage for the next iteration, not autonomous repair completion",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "frontier_evaluation_triage_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "frontier_evaluation_triage.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}


def _theory_target_items(rows: list[Any]) -> list[FrontierEvaluationTriageItem]:
    items: list[FrontierEvaluationTriageItem] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        question_id = str(row.get("question_id", ""))
        problem_class = str(row.get("problem_class", ""))
        topic = str(row.get("topic", ""))
        trace_path = str(row.get("trace_path", ""))
        for idx, score in enumerate(row.get("expected_result_scores", []) or [], start=1):
            if not isinstance(score, dict) or bool(score.get("covered")):
                continue
            coverage = float(score.get("coverage", 0.0) or 0.0)
            missing_terms = tuple(str(item) for item in score.get("missing_terms", []) or [])
            expected_result = str(score.get("expected_result", ""))
            item_id = f"theory_target:{question_id}:{idx}"
            evidence = (
                f"coverage={coverage:.3f}; missing_terms={', '.join(missing_terms[:10]) or '<none>'}"
            )
            items.append(
                _validated_item(
                    FrontierEvaluationTriageItem(
                        item_id=item_id,
                        question_id=question_id,
                        topic=topic,
                        problem_class=problem_class,
                        owner_agent="theory_developer",
                        trigger="THEORY_TARGET_MISS",
                        priority="high" if coverage < 0.10 else "medium",
                        action="revise_theory_plan_to_cover_frontier_expected_result",
                        evidence=evidence,
                        trace_path=trace_path,
                        expected_result=expected_result,
                        missing_terms=missing_terms,
                        coverage=coverage,
                    )
                )
            )
    return items


def _simulation_items(trace: dict[str, Any], trace_path: Path) -> list[FrontierEvaluationTriageItem]:
    question = trace.get("question") if isinstance(trace.get("question"), dict) else {}
    problem = trace.get("problem") if isinstance(trace.get("problem"), dict) else {}
    question_id = str(question.get("id", trace_path.stem))
    problem_class = str(problem.get("problem_class", ""))
    topic = str(question.get("topic", ""))
    items: list[FrontierEvaluationTriageItem] = []
    for idx, simulation in enumerate(trace.get("simulations", []) or [], start=1):
        if not isinstance(simulation, dict) or bool(simulation.get("passed", True)):
            continue
        diagnosis = simulation.get("diagnosis") if isinstance(simulation.get("diagnosis"), dict) else {}
        failed_diagnostics = tuple(str(item) for item in diagnosis.get("failed_diagnostics", []) or [])
        failed_stress_tests = tuple(str(item) for item in diagnosis.get("failed_stress_tests", []) or [])
        diagnosis_status = str(diagnosis.get("status", ""))
        owner_agent, priority, action = _route_simulation_failure(diagnosis_status, diagnosis, failed_diagnostics)
        procedure_id = str(simulation.get("procedure_id", ""))
        evidence = _simulation_evidence(diagnosis, simulation)
        items.append(
            _validated_item(
                FrontierEvaluationTriageItem(
                    item_id=f"simulation:{question_id}:{procedure_id or idx}",
                    question_id=question_id,
                    topic=topic,
                    problem_class=problem_class,
                    owner_agent=owner_agent,
                    trigger="SIMULATION_FLAGGED",
                    priority=priority,
                    action=action,
                    evidence=evidence,
                    trace_path=str(trace_path),
                    procedure_id=procedure_id,
                    diagnosis_status=diagnosis_status,
                    failed_diagnostics=failed_diagnostics,
                    failed_stress_tests=failed_stress_tests,
                )
            )
        )
    return items


def _route_simulation_failure(
    diagnosis_status: str,
    diagnosis: dict[str, Any],
    failed_diagnostics: tuple[str, ...],
) -> tuple[str, str, str]:
    escalate_to = str(diagnosis.get("escalate_to", ""))
    failed = set(failed_diagnostics)
    if diagnosis_status == "INSUFFICIENT_MC_PRECISION" or escalate_to == "rerun_more_mc" or "mc_precision" in failed:
        return "simulator_agent", "medium", "rerun_with_larger_monte_carlo_budget_and_stress_sweep"
    if {"bias", "relative_bias", "coverage_95", "se_ratio"} & failed:
        return "theory_developer", "high", "revise_estimator_or_variance_theory_from_simulation_diagnosis"
    return "algorithm_engineer", "high", "inspect_algorithm_implementation_against_theory_plan"


def _simulation_evidence(diagnosis: dict[str, Any], simulation: dict[str, Any]) -> str:
    metrics = diagnosis.get("metric_evidence") if isinstance(diagnosis.get("metric_evidence"), dict) else {}
    if not metrics:
        metrics = simulation.get("metrics") if isinstance(simulation.get("metrics"), dict) else {}
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
    rationale = str(diagnosis.get("rationale", ""))
    return "; ".join([rationale, *selected]).strip("; ")


def _validated_item(item: FrontierEvaluationTriageItem) -> FrontierEvaluationTriageItem:
    errors: list[str] = []
    if not item.item_id:
        errors.append("item_id missing")
    if not item.question_id:
        errors.append("question_id missing")
    if item.owner_agent not in {"theory_developer", "simulator_agent", "algorithm_engineer"}:
        errors.append("owner_agent invalid")
    if item.trigger not in {"THEORY_TARGET_MISS", "SIMULATION_FLAGGED"}:
        errors.append("trigger invalid")
    if item.priority not in {"high", "medium", "low"}:
        errors.append("priority invalid")
    if not item.action:
        errors.append("action missing")
    if not item.evidence:
        errors.append("evidence missing")
    if item.trigger == "THEORY_TARGET_MISS" and not item.expected_result:
        errors.append("theory target miss missing expected_result")
    if item.trigger == "SIMULATION_FLAGGED" and not item.procedure_id:
        errors.append("simulation flag missing procedure_id")
    if not errors:
        return item
    return FrontierEvaluationTriageItem(
        **{
            **asdict(item),
            "ok": False,
            "errors": tuple(errors),
        }
    )


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("rows", [])
    lines = [
        "# Frontier Evaluation Triage",
        "",
        "This report converts all-frontier theory-target misses and simulation",
        "flags into owner-routed next-iteration work items.",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Items: {payload.get('n_ok')}/{payload.get('n_items')} audit-clean",
        f"- Theory-target misses: {payload.get('n_theory_target_misses')}",
        f"- Simulation flags: {payload.get('n_simulation_flags')}",
        f"- Fingerprint: `{payload.get('triage_fingerprint')}`",
        "",
        "## Owner Counts",
        "",
    ]
    by_owner = payload.get("by_owner", {})
    if isinstance(by_owner, dict):
        for owner, count in by_owner.items():
            lines.append(f"- `{owner}`: {count}")
    lines.extend(
        [
            "",
            "## Top Items",
            "",
            "| Priority | Owner | Trigger | Question | Target | Evidence |",
            "|---|---|---|---|---|---|",
        ]
    )
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    if isinstance(rows, list):
        sorted_rows = sorted(
            [row for row in rows if isinstance(row, dict)],
            key=lambda row: (
                priority_rank.get(str(row.get("priority", "")), 9),
                str(row.get("owner_agent", "")),
                str(row.get("question_id", "")),
                str(row.get("item_id", "")),
            ),
        )
        for row in sorted_rows[:60]:
            target = row.get("expected_result") or row.get("procedure_id") or ""
            lines.append(
                f"| {row.get('priority')} | `{row.get('owner_agent')}` | `{row.get('trigger')}` | "
                f"`{row.get('question_id')}` | {str(target)[:80]} | {str(row.get('evidence', ''))[:100]} |"
            )
    return "\n".join(lines) + "\n"

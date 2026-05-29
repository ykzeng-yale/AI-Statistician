from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NextIterationQueueRow:
    item_id: str
    question_id: str
    problem_class: str
    owner_agent: str
    trigger: str
    priority: str
    action: str
    evidence: str
    target_procedure: str
    target_theorem_goal: str
    required_primitives: tuple[str, ...]
    failed_diagnostics: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


def audit_next_iteration_queue(run_dir: Path, out_dir: Path | None = None) -> dict[str, object]:
    """Aggregate per-trace next-iteration agenda items into one run-level queue."""

    manifest_path = run_dir / "research_benchmark_manifest.json"
    manifest_errors: list[str] = []
    rows: list[NextIterationQueueRow] = []
    if not manifest_path.exists():
        manifest_errors.append(f"missing research benchmark manifest: {manifest_path}")
        summaries: list[dict[str, Any]] = []
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            manifest_errors.append(f"failed to parse manifest JSON: {type(exc).__name__}: {exc}")
            manifest = {}
        summaries = list(manifest.get("questions", [])) if isinstance(manifest.get("questions"), list) else []

    for summary in summaries:
        question_id = str(summary.get("question", "<missing>"))
        trace_path = run_dir / f"{question_id}.json"
        if not trace_path.exists():
            manifest_errors.append(f"missing research trace file: {trace_path}")
            continue
        try:
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
        except Exception as exc:
            manifest_errors.append(f"failed to parse trace JSON {trace_path}: {type(exc).__name__}: {exc}")
            continue
        rows.extend(_queue_rows_for_trace(trace, summary))

    by_owner = Counter(row.owner_agent for row in rows)
    by_trigger = Counter(row.trigger for row in rows)
    by_priority = Counter(row.priority for row in rows)
    actionable_rows = [row for row in rows if not row.item_id.startswith("monitor:")]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "manifest": str(manifest_path),
        "n_questions": len(summaries),
        "n_items": len(rows),
        "n_actionable_items": len(actionable_rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not manifest_errors and bool(rows) and all(row.ok for row in rows),
        "manifest_errors": manifest_errors,
        "by_owner": dict(sorted(by_owner.items())),
        "by_trigger": dict(sorted(by_trigger.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "next_iteration_queue_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "next_iteration_queue.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _queue_rows_for_trace(trace: dict[str, Any], summary: dict[str, Any]) -> list[NextIterationQueueRow]:
    question = trace.get("question") if isinstance(trace.get("question"), dict) else {}
    problem = trace.get("problem") if isinstance(trace.get("problem"), dict) else {}
    question_id = str(question.get("id", summary.get("question", "<missing>")))
    problem_class = str(problem.get("problem_class", summary.get("problem_class", "<missing>")))
    theory_plan = trace.get("theory_plan") if isinstance(trace.get("theory_plan"), dict) else {}
    agenda = (
        theory_plan.get("next_iteration_agenda", {})
        if isinstance(theory_plan.get("next_iteration_agenda"), dict)
        else {}
    )
    items = agenda.get("items", []) if isinstance(agenda.get("items"), list) else []
    rows: list[NextIterationQueueRow] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        errors: list[str] = []
        item_id = str(item.get("id", ""))
        owner_agent = str(item.get("owner_agent", ""))
        trigger = str(item.get("trigger", ""))
        priority = str(item.get("priority", ""))
        action = str(item.get("action", ""))
        evidence = str(item.get("evidence", ""))
        if not item_id:
            errors.append("item_id missing")
        if owner_agent not in {
            "formal_verifier",
            "theory_developer",
            "algorithm_engineer",
            "simulator_agent",
            "research_coordinator",
        }:
            errors.append("owner_agent invalid")
        if priority not in {"high", "medium", "low"}:
            errors.append("priority invalid")
        if not trigger:
            errors.append("trigger missing")
        if not action:
            errors.append("action missing")
        if not evidence:
            errors.append("evidence missing")
        if item_id.startswith("formal_gap:") and trigger != "FORMAL_GAP":
            errors.append("formal_gap item trigger mismatch")
        if item_id.startswith("failed_obligation:") and trigger != "FAILED_PROOF_OBLIGATION":
            errors.append("failed_obligation item trigger mismatch")
        if item_id.startswith("simulation:") and not str(item.get("target_procedure", "")):
            errors.append("simulation item missing target_procedure")
        if item_id.startswith("monitor:") and owner_agent != "research_coordinator":
            errors.append("monitor item owner mismatch")
        rows.append(
            NextIterationQueueRow(
                item_id=item_id,
                question_id=question_id,
                problem_class=problem_class,
                owner_agent=owner_agent,
                trigger=trigger,
                priority=priority,
                action=action,
                evidence=evidence,
                target_procedure=str(item.get("target_procedure", "")),
                target_theorem_goal=str(item.get("target_theorem_goal", "")),
                required_primitives=tuple(str(row) for row in item.get("required_primitives", []) or []),
                failed_diagnostics=tuple(str(row) for row in item.get("failed_diagnostics", []) or []),
                ok=not errors,
                errors=tuple(errors),
            )
        )
    return rows


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("rows", [])
    lines = [
        "# AI Statistical Theory Lab Next-Iteration Queue",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Items: {payload.get('n_ok')}/{payload.get('n_items')} audit-clean",
        f"- Actionable items: {payload.get('n_actionable_items')}",
        "",
        "## Owner Counts",
        "",
    ]
    by_owner = payload.get("by_owner", {})
    if isinstance(by_owner, dict) and by_owner:
        for owner, count in sorted(by_owner.items()):
            lines.append(f"- `{owner}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Queue", ""])
    if not rows:
        lines.append("No next-iteration agenda items recorded.")
        return "\n".join(lines) + "\n"
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = "OK" if row.get("ok") else "NEEDS_ATTENTION"
        lines.extend(
            [
                f"### {row.get('item_id')} [{status}]",
                "",
                f"- Question: `{row.get('question_id')}`",
                f"- Problem class: `{row.get('problem_class')}`",
                f"- Owner: `{row.get('owner_agent')}`",
                f"- Trigger: `{row.get('trigger')}`",
                f"- Priority: `{row.get('priority')}`",
                f"- Action: `{row.get('action')}`",
                f"- Evidence: {row.get('evidence')}",
            ]
        )
        if row.get("required_primitives"):
            lines.append(
                "- Required primitives: "
                + ", ".join(f"`{item}`" for item in row.get("required_primitives", []))
            )
        if row.get("failed_diagnostics"):
            lines.append(
                "- Failed diagnostics: "
                + ", ".join(f"`{item}`" for item in row.get("failed_diagnostics", []))
            )
        errors = row.get("errors") or []
        for error in errors:
            lines.append(f"- Error: {error}")
        lines.append("")
    return "\n".join(lines) + "\n"

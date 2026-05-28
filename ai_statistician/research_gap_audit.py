from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResearchGapBacklogRow:
    gap_id: str
    question_id: str
    problem_class: str
    title: str
    theorem_goal_id: str
    proof_strategy: str
    required_primitives: tuple[str, ...]
    gap_reason: str
    artifact_path: str
    artifact_exists: bool
    procedures: tuple[str, ...]
    related_knowledge: tuple[str, ...]
    proved_subclaims: tuple[str, ...]
    supporting_proof_obligations: tuple[str, ...]
    retrieved_formal_sources: tuple[str, ...]
    primitive_formal_sources: dict[str, tuple[str, ...]]
    ok: bool
    errors: tuple[str, ...] = ()


def audit_research_gap_backlog(run_dir: Path, out_dir: Path | None = None) -> dict[str, object]:
    """Aggregate and validate FORMAL_GAP records from a research benchmark run."""

    manifest_path = run_dir / "research_benchmark_manifest.json"
    manifest_errors: list[str] = []
    rows: list[ResearchGapBacklogRow] = []
    if not manifest_path.exists():
        manifest_errors.append(f"missing research benchmark manifest: {manifest_path}")
        manifest: dict[str, Any] = {}
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
        rows.extend(_gap_rows_for_trace(trace, summary, run_dir))

    expected_gaps = sum(
        int(row.get("formal", {}).get("gaps", 0))
        for row in summaries
        if isinstance(row.get("formal"), dict)
    )
    if expected_gaps != len(rows):
        manifest_errors.append(f"manifest gap count {expected_gaps} does not match backlog rows {len(rows)}")

    by_problem_class = Counter(row.problem_class for row in rows)
    by_required_primitive = Counter(
        primitive
        for row in rows
        for primitive in row.required_primitives
    )
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "manifest": str(manifest_path),
        "n_questions": len(summaries),
        "n_gaps": len(rows),
        "n_artifacts_present": sum(1 for row in rows if row.artifact_exists),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not manifest_errors and all(row.ok for row in rows),
        "manifest_errors": manifest_errors,
        "by_problem_class": dict(sorted(by_problem_class.items())),
        "by_required_primitive": dict(sorted(by_required_primitive.items())),
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "research_gap_backlog_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "research_gap_backlog.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _gap_rows_for_trace(
    trace: dict[str, Any],
    summary: dict[str, Any],
    run_dir: Path,
) -> list[ResearchGapBacklogRow]:
    question = trace.get("question") if isinstance(trace.get("question"), dict) else {}
    problem = trace.get("problem") if isinstance(trace.get("problem"), dict) else {}
    question_id = str(question.get("id", summary.get("question", "<missing>")))
    problem_class = str(problem.get("problem_class", summary.get("problem_class", "<missing>")))
    theorem_goals = {
        str(goal.get("id")): goal
        for goal in trace.get("theorem_goals", [])
        if isinstance(goal, dict) and goal.get("id")
    }
    procedures_by_goal: dict[str, list[str]] = {}
    for procedure in trace.get("procedures", []):
        if not isinstance(procedure, dict):
            continue
        procedure_id = str(procedure.get("id", ""))
        for goal_id in procedure.get("theorem_goals", []) or []:
            procedures_by_goal.setdefault(str(goal_id), []).append(procedure_id)
    related_knowledge = tuple(
        str(card.get("id"))
        for card in trace.get("knowledge", [])
        if isinstance(card, dict) and card.get("id")
    )
    proved_subclaims = tuple(
        str(row.get("proof_obligation_id") or row.get("id"))
        for row in trace.get("formal_subclaims", [])
        if isinstance(row, dict) and row.get("status") == "PROVED"
    )

    rows: list[ResearchGapBacklogRow] = []
    for subclaim in trace.get("formal_subclaims", []):
        if not isinstance(subclaim, dict) or subclaim.get("status") != "FORMAL_GAP":
            continue
        gap_id = str(subclaim.get("id", ""))
        theorem_goal_id = gap_id.split(":")[-1] if gap_id else ""
        goal = theorem_goals.get(theorem_goal_id, {})
        artifact_path = str(subclaim.get("artifact_path") or "")
        artifact_exists = bool(artifact_path) and _artifact_exists(Path(artifact_path), run_dir)
        errors: list[str] = []
        if subclaim.get("claim_type") != "theory_gap":
            errors.append("gap claim_type is not theory_gap")
        if theorem_goal_id not in theorem_goals:
            errors.append("gap does not map to a theorem goal")
        if not subclaim.get("gap_reason"):
            errors.append("gap_reason missing")
        required_primitives = tuple(
            str(item)
            for item in goal.get("required_primitives", ())
            if str(item)
        )
        if not required_primitives:
            errors.append("gap theorem goal missing required_primitives")
        supporting_proof_obligations = tuple(
            str(item)
            for item in goal.get("proof_obligations", ())
            if str(item)
        )
        missing_support = sorted(set(supporting_proof_obligations) - set(proved_subclaims))
        if missing_support:
            errors.append(
                "gap theorem goal proof_obligations missing proved subclaims: "
                + ", ".join(missing_support)
            )
        if "FORMAL_GAP" not in str(subclaim.get("lean_statement", "")):
            errors.append("Lean skeleton does not identify FORMAL_GAP status")
        elif required_primitives and not all(
            primitive in str(subclaim.get("lean_statement", ""))
            for primitive in required_primitives
        ):
            errors.append("Lean skeleton missing one or more required primitives")
        if not artifact_exists:
            errors.append("Lean skeleton artifact missing")
        if subclaim.get("proof_obligation_id"):
            errors.append("formal gap must not claim a proof_obligation_id")
        formal_source_hits = subclaim.get("formal_source_hits", [])
        if not isinstance(formal_source_hits, list) or not formal_source_hits:
            errors.append("formal gap missing formal_source_hits")
            retrieved_formal_sources: tuple[str, ...] = ()
        else:
            retrieved_formal_sources = tuple(
                str(hit.get("name"))
                for hit in formal_source_hits
                if isinstance(hit, dict) and hit.get("name")
            )
            if not retrieved_formal_sources:
                errors.append("formal gap formal_source_hits contain no declaration names")
        primitive_hits = subclaim.get("primitive_formal_source_hits")
        primitive_formal_sources: dict[str, tuple[str, ...]] = {}
        if required_primitives:
            if not isinstance(primitive_hits, dict) or not primitive_hits:
                errors.append("formal gap missing primitive_formal_source_hits")
            else:
                missing_primitive_hit_rows = sorted(set(required_primitives) - set(str(key) for key in primitive_hits))
                if missing_primitive_hit_rows:
                    errors.append(
                        "formal gap primitive_formal_source_hits missing primitives: "
                        + ", ".join(missing_primitive_hit_rows)
                    )
                for primitive in required_primitives:
                    rows_for_primitive = primitive_hits.get(primitive)
                    if not isinstance(rows_for_primitive, list) or not rows_for_primitive:
                        errors.append(f"formal gap primitive {primitive} has no retrieved formal sources")
                        primitive_formal_sources[primitive] = ()
                        continue
                    names = tuple(
                        str(hit.get("name"))
                        for hit in rows_for_primitive
                        if isinstance(hit, dict) and hit.get("name")
                    )
                    primitive_formal_sources[primitive] = names
                    if not names:
                        errors.append(f"formal gap primitive {primitive} hit rows contain no declaration names")
        rows.append(
            ResearchGapBacklogRow(
                gap_id=gap_id,
                question_id=question_id,
                problem_class=problem_class,
                title=str(subclaim.get("title") or goal.get("title") or theorem_goal_id),
                theorem_goal_id=theorem_goal_id,
                proof_strategy=str(goal.get("proof_strategy", "")),
                required_primitives=required_primitives,
                gap_reason=str(subclaim.get("gap_reason", "")),
                artifact_path=artifact_path,
                artifact_exists=artifact_exists,
                procedures=tuple(sorted(procedures_by_goal.get(theorem_goal_id, []))),
                related_knowledge=related_knowledge,
                proved_subclaims=proved_subclaims,
                supporting_proof_obligations=supporting_proof_obligations,
                retrieved_formal_sources=retrieved_formal_sources,
                primitive_formal_sources=primitive_formal_sources,
                ok=not errors,
                errors=tuple(errors),
            )
        )
    return rows


def _artifact_exists(path: Path, run_dir: Path) -> bool:
    if path.exists():
        return True
    return (run_dir / path).exists()


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("rows", [])
    lines = [
        "# AI Statistical Theory Lab Formal Gap Backlog",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Gaps: {payload.get('n_ok')}/{payload.get('n_gaps')} audit-clean",
        f"- Skeleton artifacts present: {payload.get('n_artifacts_present')}/{payload.get('n_gaps')}",
        "",
        "## Missing Formal Primitives",
        "",
    ]
    primitive_counts = payload.get("by_required_primitive", {})
    if isinstance(primitive_counts, dict) and primitive_counts:
        for primitive, count in sorted(primitive_counts.items(), key=lambda item: (-int(item[1]), str(item[0]))):
            lines.append(f"- `{primitive}`: {count}")
    else:
        lines.append("No missing primitives recorded.")
    lines.extend(
        [
            "",
            "## Gaps",
            "",
        ]
    )
    if not rows:
        lines.append("No formal gaps recorded.")
        return "\n".join(lines) + "\n"
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = "OK" if row.get("ok") else "NEEDS_ATTENTION"
        lines.extend(
            [
                f"### {row.get('gap_id')} [{status}]",
                "",
                f"- Problem class: `{row.get('problem_class')}`",
                f"- Title: {row.get('title')}",
                f"- Procedures: {', '.join(row.get('procedures', [])) or 'none'}",
                f"- Skeleton: `{row.get('artifact_path')}`",
                f"- Required primitives: {', '.join(f'`{item}`' for item in row.get('required_primitives', [])) or 'none'}",
                f"- Proof strategy: {row.get('proof_strategy')}",
                f"- Gap reason: {row.get('gap_reason')}",
                f"- Supporting proof obligations for this goal: {', '.join(row.get('supporting_proof_obligations', [])) or 'none'}",
                f"- Proved subclaims available: {', '.join(row.get('proved_subclaims', [])) or 'none'}",
                f"- Retrieved formal sources: {', '.join(row.get('retrieved_formal_sources', [])) or 'none'}",
                "- Primitive-level candidates:",
                *_primitive_source_lines(row.get("primitive_formal_sources", {})),
                f"- Related knowledge: {', '.join(row.get('related_knowledge', [])) or 'none'}",
                "",
            ]
        )
        errors = row.get("errors") or []
        for error in errors:
            lines.append(f"  - Error: {error}")
        if errors:
            lines.append("")
    return "\n".join(lines)


def _primitive_source_lines(value: object) -> list[str]:
    if not isinstance(value, dict) or not value:
        return ["  - none"]
    lines = []
    for primitive, hits in sorted(value.items()):
        if isinstance(hits, list):
            hit_text = ", ".join(str(item) for item in hits) or "none"
        else:
            hit_text = str(hits) if hits else "none"
        lines.append(f"  - `{primitive}`: {hit_text}")
    return lines

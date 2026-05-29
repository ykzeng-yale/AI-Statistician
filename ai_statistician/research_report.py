from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_research_markdown_report(run_dir: Path, out_dir: Path | None = None) -> dict[str, object]:
    """Write a human-readable report for a persisted research benchmark run.

    The JSON traces are the authoritative audit artifacts. This report is a
    compact review layer: it assembles the extracted statistical problem,
    proposed procedures, verified subclaims, formal gaps, source grounding, and
    simulation diagnostics into one Markdown file for a statistician or theorem
    developer to read before opening individual traces.
    """

    manifest_path = run_dir / "research_benchmark_manifest.json"
    errors: list[str] = []
    if not manifest_path.exists():
        errors.append(f"missing research benchmark manifest: {manifest_path}")
        manifest: dict[str, Any] = {}
        summaries: list[dict[str, Any]] = []
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"failed to parse manifest JSON: {type(exc).__name__}: {exc}")
            manifest = {}
        summaries = list(manifest.get("questions", [])) if isinstance(manifest.get("questions"), list) else []

    rows: list[dict[str, Any]] = []
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        question_id = str(summary.get("question", "<missing>"))
        trace_path = run_dir / f"{question_id}.json"
        if not trace_path.exists():
            errors.append(f"missing research trace: {trace_path}")
            continue
        try:
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"failed to parse trace JSON {trace_path}: {type(exc).__name__}: {exc}")
            continue
        rows.append(_report_row(trace, summary, trace_path))

    status_counts = Counter(str(row.get("status", "<missing>")) for row in rows)
    problem_counts = Counter(str(row.get("problem_class", "<missing>")) for row in rows)
    counts = {
        "questions": len(rows),
        "ready_with_gaps": status_counts.get("RESEARCH_TRACE_READY_WITH_FORMAL_GAPS", 0),
        "simulation_flagged": status_counts.get("SIMULATION_FLAGGED_WITH_FORMAL_GAPS", 0),
        "formal_blocked": status_counts.get("FORMAL_BLOCKED", 0),
        "proved_subclaims": sum(int(row["formal"]["proved"]) for row in rows),
        "kernel_verified_subclaims": sum(int(row["formal"]["kernel_verified"]) for row in rows),
        "formal_gaps": sum(int(row["formal"]["gaps"]) for row in rows),
        "simulations": sum(len(row["simulations"]) for row in rows),
        "simulations_passed": sum(1 for row in rows for sim in row["simulations"] if sim.get("passed")),
    }
    payload: dict[str, object] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "manifest": str(manifest_path),
        "all_ok": not errors and bool(rows),
        "errors": errors,
        "counts": counts,
        "by_status": dict(sorted(status_counts.items())),
        "by_problem_class": dict(sorted(problem_counts.items())),
        "provenance": manifest.get("provenance", {}),
        "formal_source_search": manifest.get("formal_source_search", {}),
        "rows": rows,
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / "research_report.md"
        manifest_out = out_dir / "research_report_manifest.json"
        report_path.write_text(_markdown_report(payload), encoding="utf-8")
        manifest_out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        payload["report_path"] = str(report_path)
        payload["manifest_path"] = str(manifest_out)
    return payload


def _report_row(trace: dict[str, Any], summary: dict[str, Any], trace_path: Path) -> dict[str, Any]:
    question = trace.get("question") if isinstance(trace.get("question"), dict) else {}
    problem = trace.get("problem") if isinstance(trace.get("problem"), dict) else {}
    procedures = trace.get("procedures", []) if isinstance(trace.get("procedures"), list) else []
    theorem_goals = trace.get("theorem_goals", []) if isinstance(trace.get("theorem_goals"), list) else []
    formal_subclaims = trace.get("formal_subclaims", []) if isinstance(trace.get("formal_subclaims"), list) else []
    simulations = trace.get("simulations", []) if isinstance(trace.get("simulations"), list) else []
    paper_sources = trace.get("paper_sources", []) if isinstance(trace.get("paper_sources"), list) else []
    knowledge = trace.get("knowledge", []) if isinstance(trace.get("knowledge"), list) else []
    theory_plan = trace.get("theory_plan") if isinstance(trace.get("theory_plan"), dict) else {}
    agenda = (
        theory_plan.get("next_iteration_agenda", {})
        if isinstance(theory_plan.get("next_iteration_agenda"), dict)
        else {}
    )

    proved = [row for row in formal_subclaims if isinstance(row, dict) and row.get("status") == "PROVED"]
    gaps = [row for row in formal_subclaims if isinstance(row, dict) and row.get("status") == "FORMAL_GAP"]
    failed = [row for row in formal_subclaims if isinstance(row, dict) and row.get("status") == "FAILED"]
    formal_sources = _top_formal_source_names(gaps)

    return {
        "question_id": str(question.get("id", summary.get("question", "<missing>"))),
        "title": str(question.get("title", "")),
        "status": str(trace.get("status", summary.get("status", "<missing>"))),
        "problem_class": str(problem.get("problem_class", summary.get("problem_class", "<missing>"))),
        "trace_path": str(trace_path),
        "problem": {
            "dgp": str(problem.get("dgp", "")),
            "estimand": str(problem.get("estimand", "")),
            "assumptions": tuple(str(item) for item in problem.get("assumptions", []) or []),
            "asymptotic_regime": str(problem.get("asymptotic_regime", "")),
            "diagnostics": tuple(str(item) for item in problem.get("diagnostics", []) or []),
            "stress_tests": tuple(str(item) for item in problem.get("stress_tests", []) or []),
            "extraction_evidence": problem.get("extraction_evidence", {}),
        },
        "procedures": [
            {
                "id": str(row.get("id", "")),
                "name": str(row.get("name", "")),
                "role": str(row.get("role", "")),
                "algorithm": str(row.get("algorithm", "")),
                "formula": str(row.get("formula", "")),
                "informal_derivation": str(row.get("informal_derivation", "")),
                "theorem_goals": tuple(str(item) for item in row.get("theorem_goals", []) or []),
                "limitations": tuple(str(item) for item in row.get("limitations", []) or []),
            }
            for row in procedures
            if isinstance(row, dict)
        ],
        "theorem_goals": [
            {
                "id": str(row.get("id", "")),
                "title": str(row.get("title", "")),
                "status": str(row.get("status", "")),
                "required_primitives": tuple(str(item) for item in row.get("required_primitives", []) or []),
                "proof_obligations": tuple(str(item) for item in row.get("proof_obligations", []) or []),
            }
            for row in theorem_goals
            if isinstance(row, dict)
        ],
        "formal": {
            "proved": len(proved),
            "kernel_verified": sum(1 for row in proved if row.get("kernel_verified")),
            "mock_verified": sum(1 for row in proved if row.get("verification_strength") == "mock_static_check"),
            "gaps": len(gaps),
            "failed": len(failed),
            "proved_obligations": tuple(str(row.get("proof_obligation_id") or row.get("id")) for row in proved[:10]),
            "gap_ids": tuple(str(row.get("id")) for row in gaps[:10]),
            "gap_primitives": tuple(_unique_gap_primitives(gaps)[:12]),
            "formal_sources": tuple(formal_sources[:8]),
        },
        "simulations": [
            {
                "procedure_id": str(row.get("procedure_id", "")),
                "passed": bool(row.get("passed")),
                "metrics": row.get("metrics", {}) if isinstance(row.get("metrics"), dict) else {},
                "stress_tests": tuple(str(item) for item in row.get("stress_tests", []) or []),
                "diagnosis": row.get("diagnosis", {}) if isinstance(row.get("diagnosis"), dict) else {},
            }
            for row in simulations
            if isinstance(row, dict)
        ],
        "paper_sources": [
            {
                "id": str(row.get("id", "")),
                "source_type": str(row.get("source_type", "")),
                "title": str(row.get("title", "")),
                "score": row.get("score", 0),
            }
            for row in paper_sources[:5]
            if isinstance(row, dict)
        ],
        "knowledge_sources": [
            {
                "id": str(row.get("id", "")),
                "source_type": str(row.get("source_type", "")),
                "title": str(row.get("title", "")),
            }
            for row in knowledge[:8]
            if isinstance(row, dict)
        ],
        "next_iteration_agenda": {
            "owner_counts": agenda.get("owner_counts", {}) if isinstance(agenda.get("owner_counts"), dict) else {},
            "items": [
                {
                    "id": str(item.get("id", "")),
                    "owner_agent": str(item.get("owner_agent", "")),
                    "trigger": str(item.get("trigger", "")),
                    "action": str(item.get("action", "")),
                }
                for item in (agenda.get("items", []) if isinstance(agenda.get("items"), list) else [])[:6]
                if isinstance(item, dict)
            ],
        },
    }


def _unique_gap_primitives(gaps: list[dict[str, Any]]) -> list[str]:
    seen: list[str] = []
    for gap in gaps:
        primitive_hits = gap.get("primitive_formal_source_hits", {})
        if isinstance(primitive_hits, dict):
            for primitive in primitive_hits:
                primitive_name = str(primitive)
                if primitive_name and primitive_name not in seen:
                    seen.append(primitive_name)
        lean_statement = str(gap.get("lean_statement", ""))
        marker = "Missing formal primitives:"
        if marker in lean_statement:
            for line in lean_statement.split(marker, 1)[1].splitlines():
                stripped = line.strip()
                if stripped.startswith("- "):
                    primitive_name = stripped[2:].strip()
                    if primitive_name and primitive_name not in seen:
                        seen.append(primitive_name)
                elif stripped and not stripped.startswith("-"):
                    break
    return seen


def _top_formal_source_names(gaps: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for gap in gaps:
        for hit in gap.get("formal_source_hits", []) or []:
            if isinstance(hit, dict) and hit.get("name"):
                name = str(hit["name"])
                if name not in names:
                    names.append(name)
        primitive_hits = gap.get("primitive_formal_source_hits", {})
        if isinstance(primitive_hits, dict):
            for rows in primitive_hits.values():
                if not isinstance(rows, list):
                    continue
                for hit in rows:
                    if isinstance(hit, dict) and hit.get("name"):
                        name = str(hit["name"])
                        if name not in names:
                            names.append(name)
    return names


def _markdown_report(payload: dict[str, object]) -> str:
    counts = payload.get("counts", {})
    rows = payload.get("rows", [])
    lines = [
        "# AI Statistical Theory Lab Research Report",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Questions: {counts.get('questions', 0)}",
        f"- Ready with formal gaps: {counts.get('ready_with_gaps', 0)}",
        f"- Proved subclaims: {counts.get('proved_subclaims', 0)}",
        f"- Kernel-verified subclaims: {counts.get('kernel_verified_subclaims', 0)}",
        f"- Formal gaps: {counts.get('formal_gaps', 0)}",
        f"- Simulations passed: {counts.get('simulations_passed', 0)}/{counts.get('simulations', 0)}",
        "",
        "This report summarizes persisted trace artifacts. It is not a substitute",
        "for the JSON traces or Lean proof/audit manifests.",
        "",
    ]
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.extend(_question_markdown(row))
    if payload.get("errors"):
        lines.extend(["## Report Errors", ""])
        for error in payload.get("errors", []) or []:
            lines.append(f"- {error}")
        lines.append("")
    return "\n".join(lines)


def _question_markdown(row: dict[str, Any]) -> list[str]:
    problem = row.get("problem", {})
    formal = row.get("formal", {})
    lines = [
        f"## {row.get('question_id')}: {row.get('title')}",
        "",
        f"- Status: `{row.get('status')}`",
        f"- Problem class: `{row.get('problem_class')}`",
        f"- Trace: `{row.get('trace_path')}`",
        "",
        "### Problem Extraction",
        "",
        f"- DGP: {_one_line(problem.get('dgp', ''))}",
        f"- Estimand: {_one_line(problem.get('estimand', ''))}",
        f"- Assumptions: {_join_inline(problem.get('assumptions', ())) or 'none'}",
        f"- Asymptotic regime: {_one_line(problem.get('asymptotic_regime', ''))}",
        f"- Diagnostics: {_join_inline(problem.get('diagnostics', ())) or 'none'}",
        f"- Stress tests: {_join_inline(problem.get('stress_tests', ())) or 'none'}",
        "",
        "### Candidate Procedures",
        "",
    ]
    procedures = row.get("procedures", [])
    if procedures:
        for procedure in procedures:
            if not isinstance(procedure, dict):
                continue
            lines.extend(
                [
                    f"- `{procedure.get('id')}` ({procedure.get('algorithm')}): {_one_line(procedure.get('name', ''))}",
                    f"  - Formula: {_one_line(procedure.get('formula', ''), limit=280)}",
                    f"  - Informal derivation: {_one_line(procedure.get('informal_derivation', ''), limit=320)}",
                    f"  - Theorem goals: {_join_inline(procedure.get('theorem_goals', ())) or 'none'}",
                ]
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "### Formal Proof Status",
            "",
            f"- Proved subclaims: {formal.get('proved', 0)}",
            f"- Kernel verified: {formal.get('kernel_verified', 0)}",
            f"- Mock verified: {formal.get('mock_verified', 0)}",
            f"- Formal gaps: {formal.get('gaps', 0)}",
            f"- Proved obligations: {_join_inline(formal.get('proved_obligations', ())) or 'none'}",
            f"- Gap ids: {_join_inline(formal.get('gap_ids', ())) or 'none'}",
            f"- Missing primitives: {_join_inline(formal.get('gap_primitives', ())) or 'none'}",
            f"- Formal source candidates: {_join_inline(formal.get('formal_sources', ())) or 'none'}",
            "",
            "### Simulation Diagnostics",
            "",
        ]
    )
    simulations = row.get("simulations", [])
    if simulations:
        for simulation in simulations:
            if not isinstance(simulation, dict):
                continue
            lines.append(
                f"- `{simulation.get('procedure_id')}` passed={simulation.get('passed')}: "
                f"{_metrics_summary(simulation.get('metrics', {}))}"
            )
            diagnosis = simulation.get("diagnosis", {})
            if isinstance(diagnosis, dict) and diagnosis:
                lines.append(
                    f"  - Diagnosis: {diagnosis.get('status')} "
                    f"(escalate_to={diagnosis.get('escalate_to')})"
                )
            stress_tests = _join_inline(simulation.get("stress_tests", ()))
            if stress_tests:
                lines.append(f"  - Stress tests: {stress_tests}")
    else:
        lines.append("- none")
    agenda = row.get("next_iteration_agenda", {})
    if isinstance(agenda, dict) and agenda.get("items"):
        lines.extend(["", "### Next Iteration Agenda", ""])
        owner_counts = agenda.get("owner_counts", {})
        if isinstance(owner_counts, dict) and owner_counts:
            counts = ", ".join(f"{owner}:{count}" for owner, count in sorted(owner_counts.items()))
            lines.append(f"- Owner counts: {counts}")
        for item in agenda.get("items", []):
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('id')}` -> {item.get('owner_agent')}: "
                f"{item.get('action')} ({item.get('trigger')})"
            )
    lines.extend(["", "### Source Grounding", ""])
    paper_sources = row.get("paper_sources", [])
    if paper_sources:
        for source in paper_sources[:3]:
            if isinstance(source, dict):
                lines.append(
                    f"- Paper/source `{source.get('id')}` ({source.get('source_type')}, score={source.get('score')}): "
                    f"{_one_line(source.get('title', ''), limit=180)}"
                )
    else:
        lines.append("- No paper/source hits recorded.")
    knowledge_sources = row.get("knowledge_sources", [])
    if knowledge_sources:
        lines.append(f"- Knowledge cards: {_join_inline(source.get('id', '') for source in knowledge_sources) or 'none'}")
    lines.append("")
    return lines


def _metrics_summary(metrics: Any) -> str:
    if not isinstance(metrics, dict):
        return "no metrics"
    preferred = (
        "bias",
        "relative_bias",
        "rmse",
        "coverage_95",
        "se_ratio",
        "empirical_fdr",
        "type1_error",
        "power",
        "mean_alignment",
        "tail_coverage",
        "average_width",
    )
    parts = []
    for key in preferred:
        if key not in metrics:
            continue
        value = metrics[key]
        parts.append(f"{key}={_format_metric(value)}")
    return ", ".join(parts) if parts else ", ".join(
        f"{key}={_format_metric(value)}" for key, value in list(metrics.items())[:6]
    )


def _format_metric(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{float(value):.4g}"
    return str(value)


def _join_inline(items: Any) -> str:
    if not items:
        return ""
    return ", ".join(f"`{str(item)}`" for item in items if str(item))


def _one_line(text: Any, *, limit: int = 220) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: max(0, limit - 3)].rstrip() + "..."

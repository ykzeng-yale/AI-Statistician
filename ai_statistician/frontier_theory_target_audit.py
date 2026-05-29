from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .frontier_coverage_audit import load_frontier_benchmark_questions
from .retrieval import tokens


@dataclass(frozen=True)
class FrontierExpectedResultScore:
    expected_result: str
    coverage: float
    matched_terms: tuple[str, ...]
    missing_terms: tuple[str, ...]
    covered: bool


@dataclass(frozen=True)
class FrontierTheoryTargetRow:
    question_id: str
    title: str
    topic: str
    problem_class: str
    trace_path: str
    n_expected_results: int
    n_covered_results: int
    mean_expected_result_coverage: float
    expected_result_scores: tuple[FrontierExpectedResultScore, ...]
    ok: bool
    errors: tuple[str, ...]


def audit_frontier_theory_targets(
    run_dir: Path,
    out_dir: Path | None = None,
    *,
    benchmark_file: Path = Path("docs/frontier_stat_theory_benchmark.md"),
    coverage_threshold: float = 0.18,
) -> dict[str, object]:
    """Compare generated frontier traces against withheld expected theory targets.

    The benchmark's expected theoretical results are intentionally withheld from
    paper retrieval and theory planning. This audit uses them only after traces
    are written, as grading evidence. The gate checks that every trace was
    scored against available gold targets; the match rate is diagnostic rather
    than a release blocker because the current system still reports many
    frontier theorem goals as formal gaps.
    """

    benchmark_rows = {row.id: row for row in load_frontier_benchmark_questions(benchmark_file)}
    manifest_path = run_dir / "research_benchmark_manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    question_ids = [
        str(row.get("question", ""))
        for row in manifest.get("questions", [])
        if isinstance(row, dict) and row.get("question")
    ]
    if not question_ids:
        question_ids = sorted(path.stem for path in run_dir.glob("*.json") if path.name != "research_benchmark_manifest.json")

    rows = [_score_trace(question_id, run_dir, benchmark_rows, coverage_threshold) for question_id in question_ids]
    scored = [row for row in rows if row.n_expected_results > 0 and not row.errors]
    n_expected = sum(row.n_expected_results for row in scored)
    n_covered = sum(row.n_covered_results for row in scored)
    mean_coverage = (
        sum(row.mean_expected_result_coverage for row in scored) / len(scored)
        if scored
        else 0.0
    )
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(benchmark_file),
        "run_dir": str(run_dir),
        "coverage_threshold": coverage_threshold,
        "n_traces": len(rows),
        "n_scored": len(scored),
        "n_expected_results": n_expected,
        "n_covered_results": n_covered,
        "expected_result_coverage_rate": n_covered / n_expected if n_expected else 0.0,
        "mean_trace_coverage": mean_coverage,
        "all_scored": bool(rows) and len(scored) == len(rows),
        "all_expected_results_covered": bool(scored) and all(row.ok for row in scored),
        "audit_fingerprint": stable_hash([asdict(row) for row in rows]),
        "rows": [asdict(row) for row in rows],
        "limitations": [
            "token-overlap grading only; it does not prove semantic equivalence to the paper",
            "expected_theoretical_results are used only after trace generation, never in paper-source retrieval",
            "low coverage is a frontier-theory planning diagnostic, not a Lean proof failure",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "frontier_theory_target_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "frontier_theory_target.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _score_trace(
    question_id: str,
    run_dir: Path,
    benchmark_rows: dict[str, Any],
    coverage_threshold: float,
) -> FrontierTheoryTargetRow:
    errors: list[str] = []
    gold = benchmark_rows.get(question_id)
    trace_path = run_dir / f"{question_id}.json"
    trace: dict[str, Any] = {}
    if gold is None:
        errors.append("missing frontier benchmark gold row")
    if not trace_path.exists():
        errors.append("missing research trace JSON")
    else:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))

    expected_results = tuple(getattr(gold, "expected_results", ()) if gold is not None else ())
    generated_text = _generated_theory_text(trace)
    scores = tuple(
        _score_expected_result(expected, generated_text, coverage_threshold)
        for expected in expected_results
    )
    n_covered = sum(1 for row in scores if row.covered)
    mean_coverage = sum(row.coverage for row in scores) / len(scores) if scores else 0.0
    if not expected_results:
        errors.append("missing expected theoretical results")
    if not generated_text.strip():
        errors.append("trace has no generated theory text")

    return FrontierTheoryTargetRow(
        question_id=question_id,
        title=str(getattr(gold, "title", trace.get("question", {}).get("title", "")) if gold is not None else ""),
        topic=str(getattr(gold, "topic", "") if gold is not None else ""),
        problem_class=str(trace.get("problem", {}).get("problem_class", "")),
        trace_path=str(trace_path),
        n_expected_results=len(expected_results),
        n_covered_results=n_covered,
        mean_expected_result_coverage=round(mean_coverage, 4),
        expected_result_scores=scores,
        ok=not errors and n_covered == len(expected_results),
        errors=tuple(errors),
    )


def _score_expected_result(
    expected: str,
    generated_text: str,
    coverage_threshold: float,
) -> FrontierExpectedResultScore:
    expected_tokens = _content_tokens(expected)
    generated_tokens = _content_tokens(generated_text)
    matched = tuple(sorted(expected_tokens & generated_tokens))
    missing = tuple(sorted(expected_tokens - generated_tokens)[:30])
    coverage = len(matched) / len(expected_tokens) if expected_tokens else 0.0
    return FrontierExpectedResultScore(
        expected_result=expected,
        coverage=round(coverage, 4),
        matched_terms=matched[:30],
        missing_terms=missing,
        covered=coverage >= coverage_threshold,
    )


def _content_tokens(text: str) -> set[str]:
    generic = {
        "asymptotic",
        "derive",
        "define",
        "estimator",
        "estimators",
        "estimand",
        "estimands",
        "inference",
        "procedure",
        "procedures",
        "prove",
        "result",
        "results",
        "statistical",
        "theorem",
        "theory",
    }
    return {token for token in tokens(text) if len(token) >= 3 and token not in generic}


def _generated_theory_text(trace: dict[str, Any]) -> str:
    parts: list[str] = []
    problem = trace.get("problem", {})
    if isinstance(problem, dict):
        parts.extend(
            str(problem.get(key, ""))
            for key in ("problem_class", "dgp", "estimand", "asymptotic_regime")
        )
        parts.extend(str(item) for item in problem.get("assumptions", []) or [])
        parts.extend(str(item) for item in problem.get("diagnostics", []) or [])
    for procedure in trace.get("procedures", []) or []:
        if isinstance(procedure, dict):
            parts.extend(
                str(procedure.get(key, ""))
                for key in ("id", "name", "role", "formula", "informal_derivation", "algorithm", "simulation_design")
            )
            parts.extend(str(item) for item in procedure.get("theorem_goals", []) or [])
    for goal in trace.get("theorem_goals", []) or []:
        if isinstance(goal, dict):
            parts.extend(
                str(goal.get(key, ""))
                for key in ("id", "title", "informal_statement", "proof_strategy", "status")
            )
            parts.extend(str(item) for item in goal.get("required_primitives", []) or [])
    for subclaim in trace.get("formal_subclaims", []) or []:
        if isinstance(subclaim, dict):
            parts.extend(str(subclaim.get(key, "")) for key in ("title", "claim", "gap_reason"))
    return " ".join(parts)


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Frontier Theory Target Audit",
        "",
        "This audit compares generated research traces against withheld",
        "`expected_theoretical_results` after trace generation. It is a diagnostic",
        "benchmark score, not a Lean verification claim.",
        "",
        f"- Traces scored: {payload['n_scored']}/{payload['n_traces']}",
        f"- Expected results covered: {payload['n_covered_results']}/{payload['n_expected_results']}",
        f"- Expected-result coverage rate: {float(payload['expected_result_coverage_rate']):.3f}",
        f"- Mean trace coverage: {float(payload['mean_trace_coverage']):.3f}",
        f"- All traces scored: {payload['all_scored']}",
        f"- All expected results covered: {payload['all_expected_results_covered']}",
        f"- Fingerprint: `{payload['audit_fingerprint']}`",
        "",
        "## Rows",
        "",
        "| Question | Problem class | Covered | Mean coverage | Notes |",
        "|---|---|---:|---:|---|",
    ]
    for row in payload["rows"]:  # type: ignore[index]
        errors = "; ".join(row["errors"]) if row["errors"] else ""
        lines.append(
            f"| `{row['question_id']}` | `{row['problem_class']}` | "
            f"{row['n_covered_results']}/{row['n_expected_results']} | "
            f"{row['mean_expected_result_coverage']:.3f} | {errors or 'scored'} |"
        )
    return "\n".join(lines) + "\n"

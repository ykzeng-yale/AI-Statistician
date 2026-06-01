from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .frontier_coverage_audit import FrontierBenchmarkQuestion, load_frontier_benchmark_questions
from .frontier_theory_target_audit import audit_frontier_theory_targets
from .research_gap_audit import audit_research_gap_backlog
from .research_intake_audit import UNSUPPORTED_PROBLEM_CLASS
from .research_lab import ProblemFormalizer, build_research_provenance, run_research_benchmark
from .research_schema import OpenResearchQuestion
from .research_trace_audit import audit_research_traces
from .verifier import MockProofVerifier, ProofVerifier


DEFAULT_HOLDOUT_FILE = Path("benchmarks/fresh_holdout_frontier_benchmark.md")
DEFAULT_FRONTIER_FILE = Path("docs/frontier_stat_theory_benchmark.md")


@dataclass(frozen=True)
class FreshHoldoutSelection:
    question_id: str
    title: str
    source: str
    problem_class: str
    supported: bool
    source_identity_withheld_from_prompt: bool


async def audit_fresh_holdout_frontier(
    out_dir: Path,
    *,
    benchmark_file: Path = DEFAULT_HOLDOUT_FILE,
    main_frontier_file: Path = DEFAULT_FRONTIER_FILE,
    proof_verifier: ProofVerifier | None = None,
    formal_source_retriever: Any | None = None,
    formal_source_search: dict[str, str] | None = None,
    n_runs: int = 20,
    seed: int = 20260601,
) -> dict[str, object]:
    """Run a fresh-holdout frontier pilot without adding it to training inputs.

    The benchmark file contains source and gold-theory metadata for grading, but
    the system under test receives only generic title, open question, and
    assumptions. This audit checks that traces are written and scored separately
    from the curated 60-question frontier corpus. It does not claim theorem
    proving success; full theorem gaps remain formal gaps unless backed by
    proof-bank/AXLE evidence elsewhere.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    verifier = proof_verifier or MockProofVerifier()
    rows = load_frontier_benchmark_questions(benchmark_file)
    main_rows = load_frontier_benchmark_questions(main_frontier_file)
    main_ids = {row.id for row in main_rows}
    main_source_terms = {
        term
        for row in main_rows
        for term in _source_identity_terms(row.source)
    }
    duplicate_ids = sorted({row.id for row in rows if sum(1 for other in rows if other.id == row.id) > 1})
    overlap_with_main = sorted(row.id for row in rows if row.id in main_ids)
    overlap_with_main_sources = sorted(
        {
            row.id
            for row in rows
            if any(term in main_source_terms for term in _source_identity_terms(row.source))
        }
    )
    missing_required = [
        row.id
        for row in rows
        if not row.open_question or not row.assumptions or not row.expected_results or not row.source
    ]

    formalizer = ProblemFormalizer()
    selections: list[FreshHoldoutSelection] = []
    supported_questions: list[OpenResearchQuestion] = []
    unsupported_ids: list[str] = []
    for row in rows:
        open_question = row.to_open_research_question()
        problem = formalizer.formalize(open_question)
        supported = problem.problem_class != UNSUPPORTED_PROBLEM_CLASS
        if supported:
            supported_questions.append(open_question)
        else:
            unsupported_ids.append(row.id)
        selections.append(
            FreshHoldoutSelection(
                question_id=row.id,
                title=row.title,
                source=row.source,
                problem_class=problem.problem_class,
                supported=supported,
                source_identity_withheld_from_prompt=_source_identity_withheld_from_prompt(row),
            )
        )

    benchmark_dir = out_dir / "research_benchmark"
    if supported_questions:
        benchmark_manifest = await run_research_benchmark(
            supported_questions,
            benchmark_dir,
            proof_verifier=verifier,
            formal_source_retriever=formal_source_retriever,
            formal_source_search=formal_source_search,
            n_runs=n_runs,
            seed=seed,
        )
        trace_manifest = audit_research_traces(benchmark_dir, out_dir / "research_trace_audit")
        gap_manifest = audit_research_gap_backlog(benchmark_dir, out_dir / "research_gap_backlog")
        theory_target_manifest = audit_frontier_theory_targets(
            benchmark_dir,
            out_dir / "frontier_theory_target_audit",
            benchmark_file=benchmark_file,
        )
    else:
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        benchmark_manifest = {
            "n_questions": 0,
            "n_ready_with_gaps": 0,
            "n_simulation_flagged": 0,
            "n_formal_blocked": 0,
            "questions": [],
            "formal_source_search": formal_source_search or {"backend": "not_run"},
        }
        trace_manifest = {"all_ok": False, "n_traces": 0}
        gap_manifest = {"all_ok": False, "n_gaps": 0}
        theory_target_manifest = {
            "all_scored": False,
            "n_scored": 0,
            "n_expected_results": 0,
            "n_covered_results": 0,
            "expected_result_coverage_rate": 0.0,
        }

    leakage = _scan_source_identity_leakage(benchmark_dir, rows)
    all_prompt_identity_withheld = all(row.source_identity_withheld_from_prompt for row in selections)
    benchmark_integrity_ok = (
        bool(rows)
        and not duplicate_ids
        and not overlap_with_main
        and not overlap_with_main_sources
        and not missing_required
    )
    traces_ok = (
        int(benchmark_manifest.get("n_questions", 0)) == len(supported_questions)
        and bool(trace_manifest.get("all_ok"))
        and bool(gap_manifest.get("all_ok"))
        and bool(theory_target_manifest.get("all_scored"))
    )
    all_ok = (
        benchmark_integrity_ok
        and all_prompt_identity_withheld
        and not leakage["leaked"]
        and bool(supported_questions)
        and traces_ok
    )
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(benchmark_file),
        "main_frontier_file": str(main_frontier_file),
        "provenance": build_research_provenance(),
        "n_entries": len(rows),
        "n_supported": len(supported_questions),
        "n_unsupported": len(unsupported_ids),
        "n_scored_traces": int(theory_target_manifest.get("n_scored", 0)),
        "n_expected_results": int(theory_target_manifest.get("n_expected_results", 0)),
        "n_covered_expected_results": int(theory_target_manifest.get("n_covered_results", 0)),
        "expected_result_coverage_rate": float(
            theory_target_manifest.get("expected_result_coverage_rate", 0.0)
        ),
        "all_entries_supported": len(supported_questions) == len(rows) if rows else False,
        "all_prompt_identity_withheld": all_prompt_identity_withheld,
        "source_identity_leakage_detected": bool(leakage["leaked"]),
        "benchmark_integrity_ok": benchmark_integrity_ok,
        "traces_ok": traces_ok,
        "all_ok": all_ok,
        "unsupported_ids": unsupported_ids,
        "duplicate_ids": duplicate_ids,
        "overlap_with_main_frontier_ids": overlap_with_main,
        "overlap_with_main_frontier_sources": overlap_with_main_sources,
        "missing_required_fields": missing_required,
        "source_identity_leakage": leakage,
        "selections": [asdict(row) for row in selections],
        "research_benchmark": {
            "n_questions": benchmark_manifest.get("n_questions", 0),
            "n_ready_with_gaps": benchmark_manifest.get("n_ready_with_gaps", 0),
            "n_simulation_flagged": benchmark_manifest.get("n_simulation_flagged", 0),
            "n_formal_blocked": benchmark_manifest.get("n_formal_blocked", 0),
            "formal_source_search": benchmark_manifest.get("formal_source_search", {}),
        },
        "artifacts": {
            "research_benchmark": str(benchmark_dir / "research_benchmark_manifest.json"),
            "research_trace_audit": str(out_dir / "research_trace_audit" / "research_trace_audit_manifest.json"),
            "research_gap_backlog": str(out_dir / "research_gap_backlog" / "research_gap_backlog_manifest.json"),
            "frontier_theory_target_audit": str(
                out_dir / "frontier_theory_target_audit" / "frontier_theory_target_manifest.json"
            ),
        },
        "limitations": [
            "Fresh-holdout scoring is token-overlap theory-target evidence, not proof evidence.",
            "Supported holdout entries still produce formal gaps unless proof-bank obligations verify subclaims.",
            "Unsupported holdout entries are counted separately; rejection is an honesty signal, not a solved-theory result.",
            "The pilot is smaller than the curated 60-question frontier benchmark and should be periodically refreshed.",
        ],
        "audit_fingerprint": stable_hash(
            {
                "benchmark_file": str(benchmark_file),
                "selections": [asdict(row) for row in selections],
                "leakage": leakage,
                "theory_targets": {
                    "n_scored": theory_target_manifest.get("n_scored", 0),
                    "n_expected_results": theory_target_manifest.get("n_expected_results", 0),
                    "n_covered_results": theory_target_manifest.get("n_covered_results", 0),
                },
            }
        ),
    }
    (out_dir / "fresh_holdout_frontier_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "fresh_holdout_frontier.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _source_identity_withheld_from_prompt(row: FrontierBenchmarkQuestion) -> bool:
    prompt_text = "\n".join((row.title, row.open_question, row.assumptions)).lower()
    forbidden = ("doi", "http://", "https://", "10.1080/", "10.1093/", "jasa", "biometrika")
    return not any(term in prompt_text for term in forbidden)


def _scan_source_identity_leakage(
    benchmark_dir: Path,
    rows: list[FrontierBenchmarkQuestion],
) -> dict[str, object]:
    source_terms: dict[str, list[str]] = {}
    for row in rows:
        terms = _source_identity_terms(row.source)
        if terms:
            source_terms[row.id] = sorted(set(terms))
    leaks: list[dict[str, str]] = []
    for trace_path in benchmark_dir.glob("*.json"):
        if trace_path.name == "research_benchmark_manifest.json":
            continue
        text = trace_path.read_text(encoding="utf-8")
        for question_id, terms in source_terms.items():
            for term in terms:
                if term and term in text:
                    leaks.append(
                        {
                            "trace": str(trace_path),
                            "question_id": question_id,
                            "leaked_term": term,
                        }
                    )
    return {
        "leaked": bool(leaks),
        "n_checked_source_terms": sum(len(terms) for terms in source_terms.values()),
        "leaks": leaks,
    }


def _source_identity_terms(source: str) -> tuple[str, ...]:
    terms = []
    terms.extend(re.findall(r"10\.\d{4,9}/[A-Za-z0-9._;()/:+-]+", source))
    terms.extend(re.findall(r"https?://\S+", source))
    return tuple(sorted(set(terms)))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Fresh Holdout Frontier Audit",
        "",
        f"- Benchmark file: `{payload.get('benchmark_file')}`",
        f"- Entries: {payload.get('n_entries')}",
        f"- Supported/traced entries: {payload.get('n_supported')}/{payload.get('n_entries')}",
        f"- Scored traces: {payload.get('n_scored_traces')}",
        f"- Expected-result coverage: {payload.get('n_covered_expected_results')}/"
        f"{payload.get('n_expected_results')} ({float(payload.get('expected_result_coverage_rate', 0.0)):.1%})",
        f"- Source identity withheld from prompts: {payload.get('all_prompt_identity_withheld')}",
        f"- Source identity leakage detected in traces: {payload.get('source_identity_leakage_detected')}",
        f"- Audit OK: {payload.get('all_ok')}",
        "",
        "## Honesty Boundary",
        "",
        "This is holdout theory-target and trace evidence, not Lean theorem proof evidence. "
        "Formal proof evidence remains limited to proof-bank obligations verified by AXLE/Lean.",
        "",
        "## Unsupported Holdout Entries",
        "",
    ]
    unsupported = payload.get("unsupported_ids", [])
    if isinstance(unsupported, list) and unsupported:
        for question_id in unsupported:
            lines.append(f"- `{question_id}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Selections", ""])
    selections = payload.get("selections", [])
    if isinstance(selections, list):
        for row in selections:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('question_id')}`: class=`{row.get('problem_class')}`, "
                f"supported={row.get('supported')}, withheld={row.get('source_identity_withheld_from_prompt')}"
            )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

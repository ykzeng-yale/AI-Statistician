from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .frontier_coverage_audit import FrontierBenchmarkQuestion, load_frontier_benchmark_questions
from .frontier_theory_target_audit import audit_frontier_theory_targets
from .research_gap_audit import audit_research_gap_backlog
from .research_intake_audit import UNSUPPORTED_PROBLEM_CLASS
from .research_lab import ProblemFormalizer, build_research_provenance, run_research_benchmark
from .research_schema import OpenResearchQuestion
from .research_trace_audit import audit_research_traces
from .verifier import AxleProofVerifier, MockProofVerifier, ProofVerifier


@dataclass(frozen=True)
class FrontierSmokeConfig:
    n_runs: int = 60
    seed: int = 20260528
    max_per_class: int = 1
    use_axle: bool = False


@dataclass(frozen=True)
class FrontierSmokeSelection:
    question_id: str
    title: str
    topic: str
    source: str
    problem_class: str
    open_question: str


def select_supported_frontier_questions(
    benchmark_file: Path = Path("docs/frontier_stat_theory_benchmark.md"),
    *,
    max_per_class: int = 1,
) -> tuple[list[OpenResearchQuestion], list[FrontierSmokeSelection]]:
    """Select supported paper-style frontier questions for an executable smoke run."""

    formalizer = ProblemFormalizer()
    counts: dict[str, int] = {}
    questions: list[OpenResearchQuestion] = []
    selections: list[FrontierSmokeSelection] = []
    for row in load_frontier_benchmark_questions(benchmark_file):
        open_question = row.to_open_research_question()
        problem = formalizer.formalize(open_question)
        if problem.problem_class == UNSUPPORTED_PROBLEM_CLASS:
            continue
        if counts.get(problem.problem_class, 0) >= max_per_class:
            continue
        counts[problem.problem_class] = counts.get(problem.problem_class, 0) + 1
        questions.append(_frontier_question_with_tags(row, open_question, problem.problem_class))
        selections.append(
            FrontierSmokeSelection(
                question_id=row.id,
                title=row.title,
                topic=row.topic,
                source=row.source,
                problem_class=problem.problem_class,
                open_question=row.open_question,
            )
        )
    return questions, selections


async def run_frontier_smoke_benchmark(
    out_dir: Path,
    *,
    benchmark_file: Path = Path("docs/frontier_stat_theory_benchmark.md"),
    config: FrontierSmokeConfig = FrontierSmokeConfig(),
    proof_verifier: ProofVerifier | None = None,
    formal_source_retriever: Any | None = None,
    formal_source_search: dict[str, str] | None = None,
) -> dict[str, object]:
    """Run full research traces on selected supported entries from the frontier corpus."""

    started_at = time.perf_counter()
    stage_timings: list[dict[str, object]] = []
    stage_start = started_at

    out_dir.mkdir(parents=True, exist_ok=True)
    verifier = proof_verifier or (AxleProofVerifier() if config.use_axle else MockProofVerifier())
    questions, selections = select_supported_frontier_questions(
        benchmark_file,
        max_per_class=config.max_per_class,
    )
    stage_start = _record_stage(stage_timings, "select_supported_frontier_questions", stage_start)

    benchmark_manifest = await run_research_benchmark(
        questions,
        out_dir / "research_benchmark",
        proof_verifier=verifier,
        formal_source_retriever=formal_source_retriever,
        formal_source_search=formal_source_search,
        formal_source_index_path=None if formal_source_retriever is not None else out_dir / "formal_source_index.sqlite",
        n_runs=config.n_runs,
        seed=config.seed,
    )
    stage_start = _record_stage(stage_timings, "research_benchmark", stage_start)

    trace_manifest = audit_research_traces(
        out_dir / "research_benchmark",
        out_dir / "research_trace_audit",
    )
    gap_manifest = audit_research_gap_backlog(
        out_dir / "research_benchmark",
        out_dir / "research_gap_backlog",
    )
    stage_start = _record_stage(stage_timings, "trace_and_gap_audits", stage_start)

    theory_target_manifest = audit_frontier_theory_targets(
        out_dir / "research_benchmark",
        out_dir / "frontier_theory_target_audit",
        benchmark_file=benchmark_file,
    )
    stage_start = _record_stage(stage_timings, "frontier_theory_target_audit", stage_start)

    selected_classes = sorted({row.problem_class for row in selections})
    benchmark_ok = (
        bool(selections)
        and int(benchmark_manifest["n_questions"]) == len(selections)
        and int(benchmark_manifest["n_ready_with_gaps"]) == len(selections)
        and int(benchmark_manifest["n_formal_blocked"]) == 0
        and int(benchmark_manifest["n_simulation_flagged"]) == 0
    )
    gates = {
        "selected_supported_questions": bool(selections),
        "research_benchmark": benchmark_ok,
        "research_trace_audit": bool(trace_manifest["all_ok"]),
        "research_gap_backlog": bool(gap_manifest["all_ok"]),
        "frontier_theory_target_audit": bool(theory_target_manifest["all_scored"]),
    }
    total_elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    slowest_stages = sorted(
        stage_timings,
        key=lambda row: (-int(row["elapsed_ms"]), str(row["stage"])),
    )[:6]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(benchmark_file),
        "config": {
            "n_runs": config.n_runs,
            "seed": config.seed,
            "max_per_class": config.max_per_class,
            "use_axle": config.use_axle,
            "verifier": verifier.name,
        },
        "provenance": build_research_provenance(),
        "all_gates_passed": all(gates.values()),
        "gates": gates,
        "timings": {
            "total_elapsed_ms": total_elapsed_ms,
            "stages": stage_timings,
            "slowest_stages": slowest_stages,
        },
        "n_selected": len(selections),
        "selected_problem_classes": selected_classes,
        "selections": [asdict(row) for row in selections],
        "counts": {
            "questions": benchmark_manifest["n_questions"],
            "ready_with_gaps": benchmark_manifest["n_ready_with_gaps"],
            "formal_blocked": benchmark_manifest["n_formal_blocked"],
            "simulation_flagged": benchmark_manifest["n_simulation_flagged"],
            "traces_ok": trace_manifest["n_ok"],
            "traces_total": trace_manifest["n_traces"],
            "gap_backlog_ok": gap_manifest["n_ok"],
            "gap_backlog_total": gap_manifest["n_gaps"],
            "theory_targets_scored": theory_target_manifest["n_scored"],
            "theory_targets_total": theory_target_manifest["n_traces"],
            "theory_expected_results": theory_target_manifest["n_expected_results"],
            "theory_expected_results_covered": theory_target_manifest["n_covered_results"],
            "theory_expected_result_coverage_rate": theory_target_manifest["expected_result_coverage_rate"],
            "theory_mean_trace_coverage": theory_target_manifest["mean_trace_coverage"],
            "frontier_smoke_total_elapsed_ms": total_elapsed_ms,
            "frontier_smoke_slowest_stage": str(slowest_stages[0]["stage"]) if slowest_stages else "",
            "frontier_smoke_slowest_stage_elapsed_ms": int(slowest_stages[0]["elapsed_ms"]) if slowest_stages else 0,
        },
        "questions": benchmark_manifest["questions"],
        "artifacts": {
            "research_benchmark": str(out_dir / "research_benchmark" / "research_benchmark_manifest.json"),
            "formal_source_index": str(
                formal_source_search.get("sqlite_index_path", "")
                if formal_source_search
                else out_dir / "formal_source_index.sqlite"
            ),
            "research_trace_audit": str(
                out_dir / "research_trace_audit" / "research_trace_audit_manifest.json"
            ),
            "research_gap_backlog": str(
                out_dir / "research_gap_backlog" / "research_gap_backlog_manifest.json"
            ),
            "research_gap_backlog_report": str(out_dir / "research_gap_backlog" / "research_gap_backlog.md"),
            "frontier_theory_target_audit": str(
                out_dir / "frontier_theory_target_audit" / "frontier_theory_target_manifest.json"
            ),
            "frontier_theory_target_report": str(
                out_dir / "frontier_theory_target_audit" / "frontier_theory_target.md"
            ),
        },
    }
    (out_dir / "frontier_smoke_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "selected_questions.json").write_text(
        json.dumps([asdict(row) for row in selections], indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def _record_stage(
    stage_timings: list[dict[str, object]],
    stage: str,
    started_at: float,
) -> float:
    now = time.perf_counter()
    stage_timings.append(
        {
            "stage": stage,
            "elapsed_ms": int((now - started_at) * 1000),
        }
    )
    return now


def _frontier_question_with_tags(
    row: FrontierBenchmarkQuestion,
    question: OpenResearchQuestion,
    problem_class: str,
) -> OpenResearchQuestion:
    tags = tuple(dict.fromkeys((*question.tags, "frontier_smoke", problem_class)))
    return OpenResearchQuestion(
        id=row.id,
        title=row.title,
        description=question.description,
        tags=tags,
    )

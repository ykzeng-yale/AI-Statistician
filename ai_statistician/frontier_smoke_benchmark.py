from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .frontier_coverage_audit import FrontierBenchmarkQuestion, load_frontier_benchmark_questions
from .frontier_evaluation_triage import audit_frontier_evaluation_triage
from .frontier_simulation_rerun_audit import audit_frontier_simulation_reruns
from .frontier_theory_target_audit import audit_frontier_theory_targets
from .proof_bank import proof_bank_fingerprint
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
    # max_per_class=0 disables the per-class cap and selects every supported
    # frontier entry. This is the S3 all-frontier theory-target gate; the
    # default remains a one-per-class smoke suite for release speed.
    max_per_class: int = 1
    use_axle: bool = False
    cache_dir: str | None = None
    refresh_cache: bool = False
    simulation_rerun_runs: int = 60


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
        if max_per_class > 0 and counts.get(problem.problem_class, 0) >= max_per_class:
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

    cache_info = _frontier_smoke_cache_info(
        benchmark_file=benchmark_file,
        config=config,
        verifier=verifier,
        selections=selections,
        formal_source_search=formal_source_search,
    )
    benchmark_dir = out_dir / "research_benchmark"
    cached_manifest = _load_cached_research_benchmark(
        cache_info=cache_info,
        target_dir=benchmark_dir,
    )
    if cached_manifest is not None:
        benchmark_manifest = cached_manifest
        cache_status = "hit"
        cache_stored = False
        stage_start = _record_stage(stage_timings, "research_benchmark_cache_hit", stage_start)
    else:
        benchmark_manifest = await run_research_benchmark(
            questions,
            benchmark_dir,
            proof_verifier=verifier,
            formal_source_retriever=formal_source_retriever,
            formal_source_search=formal_source_search,
            formal_source_index_path=(
                None if formal_source_retriever is not None else out_dir / "formal_source_index.sqlite"
            ),
            n_runs=config.n_runs,
            seed=config.seed,
        )
        cache_status = "disabled" if not cache_info["enabled"] else "miss"
        cache_stored = False
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
    evaluation_triage_manifest = audit_frontier_evaluation_triage(
        out_dir / "research_benchmark",
        out_dir / "frontier_theory_target_audit" / "frontier_theory_target_manifest.json",
        out_dir / "frontier_evaluation_triage",
    )
    stage_start = _record_stage(stage_timings, "frontier_evaluation_triage", stage_start)
    simulation_rerun_manifest = audit_frontier_simulation_reruns(
        out_dir / "frontier_evaluation_triage" / "frontier_evaluation_triage_manifest.json",
        out_dir / "frontier_simulation_rerun",
        n_runs=max(config.simulation_rerun_runs, config.n_runs),
        seed=config.seed,
    )
    stage_start = _record_stage(stage_timings, "frontier_simulation_rerun", stage_start)

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
        "frontier_evaluation_triage": bool(evaluation_triage_manifest["all_ok"]),
        "frontier_simulation_rerun": bool(simulation_rerun_manifest["all_ok"]),
    }
    if cache_info["enabled"] and cache_status == "miss" and all(gates.values()):
        _store_cached_research_benchmark(cache_info=cache_info, source_dir=benchmark_dir)
        cache_stored = True
        stage_start = _record_stage(stage_timings, "research_benchmark_cache_store", stage_start)
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
            "cache_dir": str(cache_info["root"]) if cache_info["enabled"] else "",
            "refresh_cache": config.refresh_cache,
            "simulation_rerun_runs": config.simulation_rerun_runs,
        },
        "provenance": build_research_provenance(),
        "cache": {
            "enabled": bool(cache_info["enabled"]),
            "status": cache_status,
            "cache_key": str(cache_info["key"]),
            "cache_dir": str(cache_info["root"]) if cache_info["enabled"] else "",
            "cache_entry": str(cache_info["entry"]) if cache_info["enabled"] else "",
            "stored": cache_stored,
        },
        "all_gates_passed": all(gates.values()),
        "gates": gates,
        "timings": {
            "total_elapsed_ms": total_elapsed_ms,
            "stages": stage_timings,
            "slowest_stages": slowest_stages,
        },
        "n_selected": len(selections),
        "selection_scope": "all_supported" if config.max_per_class <= 0 else "per_problem_class_cap",
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
            "frontier_triage_items": evaluation_triage_manifest["n_items"],
            "frontier_triage_theory_target_misses": evaluation_triage_manifest["n_theory_target_misses"],
            "frontier_triage_simulation_flags": evaluation_triage_manifest["n_simulation_flags"],
            "frontier_simulation_rerun_items": simulation_rerun_manifest["n_items"],
            "frontier_simulation_rerun_resolved": simulation_rerun_manifest["n_resolved"],
            "frontier_simulation_rerun_still_flagged": simulation_rerun_manifest["n_still_flagged"],
            "frontier_smoke_total_elapsed_ms": total_elapsed_ms,
            "frontier_smoke_slowest_stage": str(slowest_stages[0]["stage"]) if slowest_stages else "",
            "frontier_smoke_slowest_stage_elapsed_ms": int(slowest_stages[0]["elapsed_ms"]) if slowest_stages else 0,
            "frontier_smoke_cache_enabled": bool(cache_info["enabled"]),
            "frontier_smoke_cache_status": cache_status,
            "frontier_smoke_cache_key": str(cache_info["key"]),
            "frontier_smoke_cache_stored": cache_stored,
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
            "frontier_evaluation_triage": str(
                out_dir / "frontier_evaluation_triage" / "frontier_evaluation_triage_manifest.json"
            ),
            "frontier_evaluation_triage_report": str(
                out_dir / "frontier_evaluation_triage" / "frontier_evaluation_triage.md"
            ),
            "frontier_simulation_rerun": str(
                out_dir / "frontier_simulation_rerun" / "frontier_simulation_rerun_manifest.json"
            ),
            "frontier_simulation_rerun_report": str(
                out_dir / "frontier_simulation_rerun" / "frontier_simulation_rerun.md"
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


def _frontier_smoke_cache_info(
    *,
    benchmark_file: Path,
    config: FrontierSmokeConfig,
    verifier: ProofVerifier,
    selections: list[FrontierSmokeSelection],
    formal_source_search: dict[str, str] | None,
) -> dict[str, object]:
    root = Path(config.cache_dir) if config.cache_dir else None
    key = _frontier_smoke_cache_key(
        benchmark_file=benchmark_file,
        config=config,
        verifier=verifier,
        selections=selections,
        formal_source_search=formal_source_search,
    )
    return {
        "enabled": root is not None,
        "root": root or Path(),
        "key": key,
        "entry": (root / key) if root is not None else Path(),
        "refresh": config.refresh_cache,
    }


def _frontier_smoke_cache_key(
    *,
    benchmark_file: Path,
    config: FrontierSmokeConfig,
    verifier: ProofVerifier,
    selections: list[FrontierSmokeSelection],
    formal_source_search: dict[str, str] | None,
) -> str:
    benchmark_text = benchmark_file.read_text(encoding="utf-8") if benchmark_file.exists() else ""
    payload = {
        "cache_schema": 1,
        "benchmark_file": str(benchmark_file),
        "benchmark_file_hash": stable_hash(benchmark_text),
        "config": {
            "n_runs": config.n_runs,
            "seed": config.seed,
            "max_per_class": config.max_per_class,
            "use_axle": config.use_axle,
        },
        "verifier": verifier.name,
        "selected_questions": [asdict(row) for row in selections],
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "research_provenance": _stable_research_provenance_for_cache(),
        "formal_source_search": _normalized_formal_source_search(formal_source_search),
        "engine_fingerprints": {
            "frontier_smoke_benchmark": _source_file_hash(Path(__file__)),
            "research_lab": _source_file_hash(Path(__file__).with_name("research_lab.py")),
            "research_schema": _source_file_hash(Path(__file__).with_name("research_schema.py")),
        },
    }
    return stable_hash(payload)[:24]


def _source_file_hash(path: Path) -> str:
    return stable_hash(path.read_text(encoding="utf-8")) if path.exists() else ""


def _stable_research_provenance_for_cache() -> dict[str, str]:
    provenance = dict(build_research_provenance())
    # Source-inventory fingerprints include file counts for local working trees,
    # so generated run artifacts can invalidate an otherwise identical smoke run.
    # Keep the trace-generation fingerprints that affect selected procedures,
    # paper grounding, proof obligations, and research logic.
    provenance.pop("research_source_inventory_fingerprint", None)
    return provenance


def _normalized_formal_source_search(formal_source_search: dict[str, str] | None) -> dict[str, str]:
    if not formal_source_search:
        return {}
    stable_keys = ("backend", "graph_backend")
    return {
        key: str(formal_source_search[key])
        for key in stable_keys
        if key in formal_source_search and formal_source_search[key]
    }


def _load_cached_research_benchmark(
    *,
    cache_info: dict[str, object],
    target_dir: Path,
) -> dict[str, Any] | None:
    if not cache_info["enabled"] or cache_info["refresh"]:
        return None
    entry = Path(str(cache_info["entry"]))
    cached_dir = entry / "research_benchmark"
    manifest_path = cached_dir / "research_benchmark_manifest.json"
    cache_manifest_path = entry / "frontier_smoke_cache_manifest.json"
    if not manifest_path.exists() or not cache_manifest_path.exists():
        return None
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(cached_dir, target_dir)
    return json.loads((target_dir / "research_benchmark_manifest.json").read_text(encoding="utf-8"))


def _store_cached_research_benchmark(
    *,
    cache_info: dict[str, object],
    source_dir: Path,
) -> None:
    if not cache_info["enabled"]:
        return
    entry = Path(str(cache_info["entry"]))
    cached_dir = entry / "research_benchmark"
    if cached_dir.exists():
        shutil.rmtree(cached_dir)
    entry.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, cached_dir)
    cache_payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cache_schema": 1,
        "cache_key": str(cache_info["key"]),
        "research_benchmark_manifest": str(cached_dir / "research_benchmark_manifest.json"),
    }
    (entry / "frontier_smoke_cache_manifest.json").write_text(
        json.dumps(cache_payload, indent=2, default=str),
        encoding="utf-8",
    )


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

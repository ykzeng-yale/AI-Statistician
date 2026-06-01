from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .frontier_backlog_audit import audit_frontier_backlog
from .frontier_coverage_audit import audit_frontier_coverage
from .frontier_precision_audit import audit_frontier_precision
from .fresh_holdout_frontier_audit import audit_fresh_holdout_frontier
from .algorithm_repair_promotion import export_algorithm_repair_promotion_queue
from .algorithm_repair_patch_policy_model import train_algorithm_repair_patch_policy_model
from .algorithm_repair_patch_training_export import export_algorithm_repair_patch_training_dataset
from .algorithm_repair_production_patch_plan import export_algorithm_repair_production_patch_plan
from .algorithm_repair_reviewed_patch_apply import apply_reviewed_algorithm_repair_source_patches
from .algorithm_repair_reviewed_patch_validate import validate_reviewed_algorithm_repair_patches
from .algorithm_simulation_stress_audit import audit_algorithm_simulation_stress
from .algorithm_repair_sandbox import evaluate_algorithm_repair_sandbox
from .algorithm_repair_sandbox_apply import apply_algorithm_repair_sandbox_results
from .algorithm_repair_sandbox_patch_eval import evaluate_algorithm_repair_sandbox_patches
from .algorithm_repair_sandbox_rerun import rerun_algorithm_repair_sandbox_applications
from .adversarial_intake_audit import audit_adversarial_unsupported_intake
from .architecture_audit import audit_architecture
from .evaluation_benchmark_guidance import build_evaluation_benchmark_guidance
from .formal_gap_task_export import export_formal_gap_lean_tasks
from .formalization_target_audit import audit_formalization_targets
from .formal_source_graph import audit_formal_source_graph
from .formal_source_hybrid import FormalSourceHybridRetriever
from .formal_source_index import FormalSourceSqliteIndex, build_formal_source_search_backend
from .formal_source_retrieval_ablation import run_formal_source_retrieval_ablation_benchmark
from .formal_source_retrieval_benchmark import run_formal_source_retrieval_benchmark
from .autoform_harness import audit_autoform_harness
from .autoform_target_export import export_autoform_targets
from .frontier_smoke_benchmark import FrontierSmokeConfig, run_frontier_smoke_benchmark
from .proof_audit import audit_proof_bank
from .proof_bank import proof_bank_fingerprint
from .proof_bank_expansion_export import export_proof_bank_expansion_candidates
from .primitive_source_coverage_audit import audit_primitive_source_coverage
from .proof_policy_baseline import evaluate_retrieval_proof_policy_baseline
from .proof_policy_model import train_proof_policy_model
from .proof_repair_export import export_proof_repair_dataset
from .proof_search_audit import audit_proof_search_controller
from .proof_search_retrieval_ablation import run_proof_search_retrieval_ablation
from .proof_search_training_export import export_proof_search_process_dataset
from .proof_search_value_model import train_proof_search_value_model
from .proof_training_export import export_proof_training_dataset
from .prover_component_audit import build_prover_component_audit, write_prover_component_audit
from .research_gap_audit import audit_research_gap_backlog
from .research_intake_audit import audit_research_question_intake
from .research_knowledge_audit import audit_research_knowledge
from .research_capability_audit import build_research_capability_audit, write_research_capability_audit
from .research_lab import (
    audit_research_algorithm_registry,
    build_research_provenance,
    load_open_research_questions,
    run_research_benchmark,
)
from .research_loop import LoopConfig, run_research_loop_benchmark
from .research_loop_live_repair_audit import audit_research_loop_live_repair_artifacts
from .research_loop_repair_audit import audit_research_loop_repair_tasks
from .research_next_iteration_audit import audit_next_iteration_queue
from .research_policy_baseline import evaluate_research_policy_baseline
from .research_report import build_research_markdown_report
from .research_schema import OpenResearchQuestion
from .research_trace_audit import audit_research_traces
from .research_training_export import export_research_training_dataset
from .retrieval import audit_proof_bank_retrieval
from .verifier import AxleProofVerifier, CachingProofVerifier, LocalLeanProofVerifier, MockProofVerifier, ProofVerifier


@dataclass(frozen=True)
class ResearchSystemAuditConfig:
    n_runs: int = 100
    seed: int = 20260528
    frontier_smoke_runs: int = 25
    use_axle: bool = False
    use_local_lean: bool = False
    local_lean_project: str | None = None
    local_lean_timeout: int = 90
    formal_source_index_cache: str | None = "runs/formal_source_index_cache/formal_source_index.sqlite"
    refresh_formal_source_index_cache: bool = False
    lean_rag_db: str | None = None
    frontier_smoke_cache: str | None = "runs/frontier_smoke_cache"
    refresh_frontier_smoke_cache: bool = False
    formal_source_graph_cache: str | None = "runs/formal_source_graph_cache"
    refresh_formal_source_graph_cache: bool = False
    research_benchmark_cache: str | None = "runs/research_benchmark_cache"
    refresh_research_benchmark_cache: bool = False


async def run_research_system_audit(
    out_dir: Path,
    *,
    question_file: Path | None = None,
    config: ResearchSystemAuditConfig = ResearchSystemAuditConfig(),
) -> dict[str, object]:
    """Run release-style gates for the open-question research workflow."""

    audit_start = time.perf_counter()
    stage_timings: list[dict[str, object]] = []
    stage_start = audit_start

    out_dir.mkdir(parents=True, exist_ok=True)
    if config.use_local_lean:
        base_verifier: ProofVerifier = LocalLeanProofVerifier(
            project_root=config.local_lean_project,
            timeout_s=config.local_lean_timeout,
        )
    else:
        base_verifier = AxleProofVerifier() if config.use_axle else MockProofVerifier()
    verifier = CachingProofVerifier(base_verifier)
    actual_question_file = question_file or Path("examples/research_questions.json")
    questions = load_open_research_questions(actual_question_file)
    stage_start = _record_stage(stage_timings, "setup", stage_start)

    formal_source_index_path = out_dir / "formal_source_index.sqlite"
    formal_source_retriever = build_formal_source_search_backend(
        db_path=formal_source_index_path,
        cache_path=(
            Path(config.formal_source_index_cache)
            if config.formal_source_index_cache
            else None
        ),
        refresh_cache=config.refresh_formal_source_index_cache,
        lean_rag_db_path=Path(config.lean_rag_db) if config.lean_rag_db else None,
    )
    stage_start = _record_stage(stage_timings, "formal_source_index_backend", stage_start)

    formal_source_declarations = (
        formal_source_retriever.load_declarations()
        if hasattr(formal_source_retriever, "load_declarations")
        else []
    )
    formal_source_graph_manifest = audit_formal_source_graph(
        out_dir / "formal_source_graph",
        declarations=formal_source_declarations or None,
        cache_path=(
            Path(config.formal_source_graph_cache)
            if config.formal_source_graph_cache
            else None
        ),
        refresh_cache=config.refresh_formal_source_graph_cache,
    )
    formal_source_search = {
        "backend": "sqlite_fts_shape_graph_hybrid",
        "sqlite_index_path": str(formal_source_index_path),
        "graph_backend": "declaration_symbol_graph",
        "dependency_graph_backend": (
            "lean_rag_dependency_graph"
            if getattr(formal_source_retriever, "lean_rag_dependency_graph_enabled", False)
            else ""
        ),
        "lean_rag_db_path": getattr(formal_source_retriever, "lean_rag_dependency_graph_path", ""),
        "lean_rag_auto_discovered": getattr(
            formal_source_retriever,
            "lean_rag_dependency_graph_auto_discovered",
            False,
        ),
        "graph_manifest": str(out_dir / "formal_source_graph" / "formal_source_graph_manifest.json"),
    }
    stage_start = _record_stage(stage_timings, "formal_source_graph", stage_start)

    formal_source_retrieval_benchmark_manifest = run_formal_source_retrieval_benchmark(
        out_dir / "formal_source_retrieval_benchmark",
        retriever=formal_source_retriever,
    )
    baseline_formal_source_retriever = FormalSourceHybridRetriever(
        formal_source_declarations,
        FormalSourceSqliteIndex(formal_source_index_path),
        dependency_retriever=None,
    )
    formal_source_retrieval_ablation_manifest = run_formal_source_retrieval_ablation_benchmark(
        out_dir / "formal_source_retrieval_ablation",
        baseline_retriever=baseline_formal_source_retriever,
        enhanced_retriever=formal_source_retriever,
    )
    stage_start = _record_stage(stage_timings, "formal_source_retrieval_benchmark", stage_start)

    frontier_manifest = audit_frontier_coverage(out_dir / "frontier_coverage_audit")
    frontier_precision_manifest = audit_frontier_precision(out_dir / "frontier_precision_audit")
    frontier_backlog_manifest = audit_frontier_backlog(out_dir / "frontier_backlog_audit")
    stage_start = _record_stage(stage_timings, "frontier_static_audits", stage_start)

    architecture_manifest = audit_architecture(out_dir / "architecture_audit")
    capability_report = build_research_capability_audit(
        root=Path.cwd(),
        question_file=actual_question_file,
        max_manifests=12,
    )
    write_research_capability_audit(capability_report, out_dir / "research_capability_audit")
    stage_start = _record_stage(stage_timings, "architecture_capability_audits", stage_start)

    proof_manifest = await audit_proof_bank(
        verifier,
        out_dir / "proof_audit",
        export_lean=True,
        include_negative_controls=not (config.use_axle or config.use_local_lean),
    )
    stage_start = _record_stage(stage_timings, "proof_audit", stage_start)

    frontier_smoke_manifest = await run_frontier_smoke_benchmark(
        out_dir / "frontier_smoke_benchmark",
        config=FrontierSmokeConfig(
            n_runs=config.frontier_smoke_runs,
            seed=config.seed,
            max_per_class=1,
            use_axle=config.use_axle,
            cache_dir=config.frontier_smoke_cache,
            refresh_cache=config.refresh_frontier_smoke_cache,
        ),
        proof_verifier=verifier,
        formal_source_retriever=formal_source_retriever,
        formal_source_search=formal_source_search,
    )
    stage_start = _record_stage(stage_timings, "frontier_smoke_benchmark", stage_start)

    fresh_holdout_manifest = await audit_fresh_holdout_frontier(
        out_dir / "fresh_holdout_frontier_audit",
        proof_verifier=verifier,
        formal_source_retriever=formal_source_retriever,
        formal_source_search=formal_source_search,
        n_runs=max(10, min(config.frontier_smoke_runs, 20)),
        seed=config.seed + 707,
    )
    stage_start = _record_stage(stage_timings, "fresh_holdout_frontier_audit", stage_start)

    intake_manifest = audit_research_question_intake(out_dir / "research_intake_audit")
    adversarial_intake_manifest = audit_adversarial_unsupported_intake(
        out_dir / "adversarial_intake_audit"
    )
    knowledge_manifest = audit_research_knowledge(out_dir / "research_knowledge_audit")
    autoform_harness_manifest = audit_autoform_harness(out_dir / "autoform_harness")
    retrieval_manifest = audit_proof_bank_retrieval(out_dir / "retrieval_audit", k=5)
    algorithm_manifest = audit_research_algorithm_registry(out_dir / "research_algorithm_audit")
    algorithm_simulation_stress_manifest = audit_algorithm_simulation_stress(
        out_dir / "algorithm_simulation_stress_audit",
        question_file=actual_question_file,
        seeds=(config.seed + 31, config.seed + 32, config.seed + 33),
        n_runs=max(10, min(config.n_runs, 25)),
    )
    stage_start = _record_stage(stage_timings, "small_static_audits", stage_start)

    proof_attempt_log = Path(str(proof_manifest["proof_attempt_log"]["attempt_log"]))
    proof_training_manifest = export_proof_training_dataset(
        proof_attempt_log,
        out_dir / "proof_training_export",
        validation_fraction=0.2,
    )
    proof_repair_manifest = export_proof_repair_dataset(
        proof_attempt_log,
        out_dir / "proof_repair_export",
        validation_fraction=0.2,
    )
    proof_policy_manifest = evaluate_retrieval_proof_policy_baseline(
        Path(str(proof_training_manifest["train_jsonl"])),
        Path(str(proof_training_manifest["validation_jsonl"])),
        out_dir / "proof_policy_baseline",
        k=5,
    )
    proof_policy_model_manifest = train_proof_policy_model(
        Path(str(proof_training_manifest["train_jsonl"])),
        out_dir / "proof_policy_model",
        validation_jsonl=Path(str(proof_training_manifest["validation_jsonl"])),
        k=5,
    )
    proof_search_bootstrap_manifest = await audit_proof_search_controller(
        out_dir / "proof_search_bootstrap_audit",
        verifier=verifier,
        max_obligations=12,
        max_nodes=8,
        include_invalid_probe=True,
        proof_policy_model_json=Path(str(proof_policy_model_manifest["model_json"])),
        formal_source_retriever=formal_source_retriever,
    )
    proof_search_bootstrap_training_manifest = export_proof_search_process_dataset(
        Path(str(proof_search_bootstrap_manifest["results_jsonl"])),
        out_dir / "proof_search_bootstrap_training_export",
        validation_fraction=0.2,
    )
    proof_search_value_manifest = train_proof_search_value_model(
        Path(str(proof_search_bootstrap_training_manifest["train_jsonl"])),
        out_dir / "proof_search_value_model",
        validation_jsonl=Path(str(proof_search_bootstrap_training_manifest["validation_jsonl"])),
    )
    proof_search_manifest = await audit_proof_search_controller(
        out_dir / "proof_search_audit",
        verifier=verifier,
        max_obligations=12,
        max_nodes=8,
        include_invalid_probe=True,
        proof_policy_model_json=Path(str(proof_policy_model_manifest["model_json"])),
        proof_value_model_json=Path(str(proof_search_value_manifest["model_json"])),
        formal_source_retriever=formal_source_retriever,
    )
    proof_search_retrieval_ablation_manifest = await run_proof_search_retrieval_ablation(
        out_dir / "proof_search_retrieval_ablation",
        baseline_retriever=baseline_formal_source_retriever,
        enhanced_retriever=formal_source_retriever,
        verifier=verifier,
        max_obligations=6,
        max_nodes=4,
        formal_source_k=4,
    )
    proof_search_training_manifest = export_proof_search_process_dataset(
        Path(str(proof_search_manifest["results_jsonl"])),
        out_dir / "proof_search_training_export",
        validation_fraction=0.2,
    )
    stage_start = _record_stage(stage_timings, "proof_training_repair_policy_exports", stage_start)

    prover_component_report = build_prover_component_audit(
        root=Path.cwd(),
        question_file=actual_question_file,
    )
    write_prover_component_audit(prover_component_report, out_dir / "prover_component_audit")
    stage_start = _record_stage(stage_timings, "prover_component_audit", stage_start)

    benchmark_cache_info = _research_benchmark_cache_info(
        questions=questions,
        question_file=actual_question_file,
        config=config,
        verifier=verifier,
        formal_source_search=formal_source_search,
    )
    benchmark_dir = out_dir / "research_benchmark"
    cached_benchmark_manifest = _load_cached_research_benchmark(
        cache_info=benchmark_cache_info,
        target_dir=benchmark_dir,
    )
    if cached_benchmark_manifest is not None:
        benchmark_manifest = cached_benchmark_manifest
        benchmark_cache_status = "hit"
        benchmark_cache_stored = False
        stage_start = _record_stage(stage_timings, "research_benchmark_cache_hit", stage_start)
    else:
        benchmark_manifest = await run_research_benchmark(
            questions,
            benchmark_dir,
            proof_verifier=verifier,
            formal_source_retriever=formal_source_retriever,
            formal_source_search=formal_source_search,
            n_runs=config.n_runs,
            seed=config.seed,
        )
        benchmark_cache_status = "disabled" if not benchmark_cache_info["enabled"] else "miss"
        benchmark_cache_stored = False
        stage_start = _record_stage(stage_timings, "research_benchmark", stage_start)

    trace_manifest = audit_research_traces(
        out_dir / "research_benchmark",
        out_dir / "research_trace_audit",
    )
    gap_backlog_manifest = audit_research_gap_backlog(
        out_dir / "research_benchmark",
        out_dir / "research_gap_backlog",
    )
    formalization_target_manifest = audit_formalization_targets(
        out_dir / "research_benchmark",
        out_dir / "formalization_target_audit",
    )
    formal_gap_task_manifest = export_formal_gap_lean_tasks(
        out_dir / "research_benchmark",
        out_dir / "formal_gap_lean_tasks",
    )
    autoform_target_manifest = export_autoform_targets(
        out_dir / "research_benchmark",
        out_dir / "autoform_targets",
    )
    proof_bank_expansion_manifest = export_proof_bank_expansion_candidates(
        out_dir / "research_benchmark",
        out_dir / "proof_bank_expansion",
    )
    primitive_source_coverage_manifest = audit_primitive_source_coverage(
        out_dir / "research_benchmark",
        out_dir / "primitive_source_coverage",
        formal_source_retriever=formal_source_retriever,
        formal_source_index_path=formal_source_index_path,
        lean_rag_db_path=Path(config.lean_rag_db) if config.lean_rag_db else None,
    )
    stage_start = _record_stage(stage_timings, "research_trace_gap_exports", stage_start)

    research_training_manifest = export_research_training_dataset(
        out_dir / "research_benchmark",
        out_dir / "research_training_export",
        validation_fraction=0.2,
    )
    research_policy_manifest = evaluate_research_policy_baseline(
        Path(str(research_training_manifest["train_jsonl"])),
        Path(str(research_training_manifest["validation_jsonl"])),
        out_dir / "research_policy_baseline",
        k=5,
    )
    next_iteration_manifest = audit_next_iteration_queue(
        out_dir / "research_benchmark",
        out_dir / "next_iteration_queue",
    )
    research_report_manifest = build_research_markdown_report(
        out_dir / "research_benchmark",
        out_dir / "research_report",
    )
    stage_start = _record_stage(stage_timings, "research_training_policy_report_exports", stage_start)

    research_loop_manifest = await run_research_loop_benchmark(
        questions[:1],
        out_dir / "research_loop",
        proof_verifier=verifier,
        formal_source_retriever=formal_source_retriever,
        formal_source_index_path=formal_source_index_path,
        config=LoopConfig(max_rounds=2, n_runs=config.n_runs, seed=config.seed),
    )
    stage_start = _record_stage(stage_timings, "research_loop", stage_start)

    research_loop_repair_manifest = audit_research_loop_repair_tasks(
        out_dir / "research_loop",
        out_dir / "research_loop_repair_audit",
    )
    research_loop_live_repair_manifest = audit_research_loop_live_repair_artifacts(
        out_dir / "research_loop",
        out_dir / "research_loop_live_repair_audit",
    )
    stage_start = _record_stage(stage_timings, "research_loop_repair_audits", stage_start)

    algorithm_repair_promotion_manifest = export_algorithm_repair_promotion_queue(
        out_dir / "research_loop",
        out_dir / "algorithm_repair_promotion",
    )
    algorithm_repair_sandbox_manifest = evaluate_algorithm_repair_sandbox(
        out_dir / "algorithm_repair_promotion",
        out_dir / "algorithm_repair_sandbox",
    )
    algorithm_repair_sandbox_apply_manifest = apply_algorithm_repair_sandbox_results(
        out_dir / "algorithm_repair_sandbox",
        out_dir / "algorithm_repair_sandbox_apply",
    )
    algorithm_repair_sandbox_rerun_manifest = rerun_algorithm_repair_sandbox_applications(
        out_dir / "algorithm_repair_sandbox_apply",
        out_dir / "algorithm_repair_sandbox_rerun",
        question_file=actual_question_file,
        n_runs=max(10, min(config.n_runs, 50)),
        seed=config.seed + 17,
    )
    algorithm_repair_sandbox_patch_eval_manifest = evaluate_algorithm_repair_sandbox_patches(
        out_dir / "algorithm_repair_sandbox_apply",
        out_dir / "algorithm_repair_sandbox_patch_eval",
        question_file=actual_question_file,
        n_runs=max(10, min(config.n_runs, 50)),
        seed=config.seed + 19,
    )
    algorithm_repair_patch_training_manifest = export_algorithm_repair_patch_training_dataset(
        out_dir / "algorithm_repair_sandbox_patch_eval",
        out_dir / "algorithm_repair_patch_training_export",
        validation_fraction=0.2,
    )
    algorithm_repair_patch_policy_manifest = train_algorithm_repair_patch_policy_model(
        Path(str(algorithm_repair_patch_training_manifest["train_jsonl"])),
        out_dir / "algorithm_repair_patch_policy_model",
        validation_jsonl=Path(str(algorithm_repair_patch_training_manifest["validation_jsonl"])),
    )
    algorithm_repair_production_patch_plan_manifest = export_algorithm_repair_production_patch_plan(
        out_dir / "algorithm_repair_patch_policy_model",
        out_dir / "algorithm_repair_production_patch_plan",
    )
    algorithm_repair_reviewed_patch_apply_manifest = apply_reviewed_algorithm_repair_source_patches(
        out_dir / "algorithm_repair_production_patch_plan",
        out_dir / "algorithm_repair_reviewed_patch_apply",
        source_root=Path("."),
    )
    algorithm_repair_reviewed_patch_validate_manifest = validate_reviewed_algorithm_repair_patches(
        out_dir / "algorithm_repair_reviewed_patch_apply",
        out_dir / "algorithm_repair_reviewed_patch_validate",
        source_root=Path("."),
        question_file=actual_question_file,
        n_runs=max(5, min(config.n_runs, 10)),
        seed=config.seed + 23,
    )
    stage_start = _record_stage(stage_timings, "algorithm_repair_pipeline", stage_start)

    benchmark_gate_ok = (
        int(benchmark_manifest["n_questions"]) == len(questions)
        and int(benchmark_manifest["n_ready_with_gaps"]) == len(questions)
        and int(benchmark_manifest["n_simulation_flagged"]) == 0
        and int(benchmark_manifest["n_formal_blocked"]) == 0
    )
    formalized_gaps_ok = all(
        row["formal"]["gaps"] == row["formal"]["formalized_gaps"]
        for row in benchmark_manifest["questions"]
    )
    gates = {
        "frontier_coverage_audit": bool(frontier_manifest["all_ok"]),
        "frontier_precision_audit": bool(frontier_precision_manifest["all_ok"]),
        "frontier_backlog_audit": bool(frontier_backlog_manifest["all_ok"]),
        "architecture_audit": bool(architecture_manifest["all_release_scaffold_components_present"]),
        "research_capability_audit": bool(capability_report["all_current_release_requirements_met"]),
        "frontier_smoke_benchmark": bool(frontier_smoke_manifest["all_gates_passed"]),
        "research_intake_audit": bool(intake_manifest["all_ok"]),
        "adversarial_intake_audit": bool(adversarial_intake_manifest["all_ok"]),
        "research_knowledge_audit": bool(knowledge_manifest["all_ok"]),
        "autoform_harness": bool(autoform_harness_manifest["ready_for_integration"]),
        "retrieval_audit": bool(retrieval_manifest["all_top_k"]),
        "formal_source_graph": bool(formal_source_graph_manifest["all_queries_ok"]),
        "formal_source_retrieval_benchmark": bool(formal_source_retrieval_benchmark_manifest["all_ok"]),
        "formal_source_retrieval_ablation": bool(formal_source_retrieval_ablation_manifest["all_ok"]),
        "fresh_holdout_frontier_audit": bool(fresh_holdout_manifest["all_ok"]),
        "research_algorithm_audit": bool(algorithm_manifest["all_ok"]),
        "algorithm_simulation_stress_audit": bool(algorithm_simulation_stress_manifest["all_ok"]),
        "proof_audit": bool(proof_manifest["all_verified"])
        and bool(proof_manifest["dependency_graph"]["all_ok"])
        and (
            not (config.use_axle or config.use_local_lean)
            or bool(proof_manifest["all_kernel_verified"])
        ),
        "proof_training_export": int(proof_training_manifest["n_sft_examples"])
        == int(proof_manifest["proof_attempt_log"]["n_positive"]),
        "proof_repair_export": (
            int(proof_repair_manifest["n_repair_examples"]) == int(proof_repair_manifest["n_negative_attempts"])
            if proof_manifest["negative_controls"]["enabled"]
            else int(proof_repair_manifest["n_repair_examples"]) >= 0
        ),
        "proof_policy_baseline": int(proof_policy_manifest["n_train"])
        + int(proof_policy_manifest["n_validation"])
        == int(proof_training_manifest["n_sft_examples"]),
        "proof_policy_model": int(proof_policy_model_manifest["n_train"]) > 0
        and int(proof_policy_model_manifest["n_features"]) > 0,
        "proof_search_audit": bool(proof_search_manifest["all_solved"])
        and bool(proof_search_manifest["policy_model_enabled"])
        and bool(proof_search_manifest["value_model_enabled"])
        and int(proof_search_manifest["tactic_template_candidates_total"]) > 0
        and int(proof_search_manifest["retrieval_candidates_total"]) > 0
        and bool(proof_search_manifest["formal_source_retriever_enabled"])
        and int(proof_search_manifest["formal_source_candidates_total"]) > 0
        and int(proof_search_manifest["policy_scored_expanded_nodes"]) > 0
        and int(proof_search_manifest["value_scored_expanded_nodes"]) > 0,
        "proof_search_retrieval_ablation": bool(proof_search_retrieval_ablation_manifest["all_ok"]),
        "proof_search_training_export": int(proof_search_training_manifest["n_process_examples"])
        == int(proof_search_manifest["nodes_expanded"]),
        "proof_search_value_model": int(proof_search_value_manifest["n_train"]) > 0
        and int(proof_search_value_manifest["n_features"]) > 0,
        "prover_component_audit": bool(prover_component_report["paper_outline_exists"])
        and int(prover_component_report["summary"]["components"]) > 0,
        "research_benchmark": benchmark_gate_ok,
        "formal_gap_skeletons": formalized_gaps_ok,
        "research_trace_audit": bool(trace_manifest["all_ok"]),
        "research_gap_backlog": bool(gap_backlog_manifest["all_ok"]),
        "formalization_target_audit": bool(formalization_target_manifest["all_ok"]),
        "formal_gap_task_export": bool(formal_gap_task_manifest["all_ok"]),
        "autoform_target_export": bool(autoform_target_manifest["all_ok"])
        and int(autoform_target_manifest["n_targets"]) == int(formal_gap_task_manifest["n_tasks"]),
        "proof_bank_expansion_export": bool(proof_bank_expansion_manifest["all_ok"]),
        "primitive_source_coverage_audit": bool(primitive_source_coverage_manifest["all_ok"]),
        "research_training_export": bool(research_training_manifest["all_ok"]),
        "research_policy_baseline": bool(research_policy_manifest["all_ok"]),
        "next_iteration_queue": bool(next_iteration_manifest["all_ok"]),
        "research_report": bool(research_report_manifest["all_ok"]),
        "research_loop": bool(research_loop_manifest["all_loop_traces_written"])
        and bool(research_loop_manifest["all_repair_tasks_exported"])
        and bool(research_loop_manifest["all_live_repair_artifacts_exported"])
        and int(research_loop_manifest["n_questions"]) == 1,
        "research_loop_repair_audit": bool(research_loop_repair_manifest["all_ok"]),
        "research_loop_live_repair_audit": bool(research_loop_live_repair_manifest["all_ok"]),
        "algorithm_repair_promotion": bool(algorithm_repair_promotion_manifest["all_ok"]),
        "algorithm_repair_sandbox": bool(algorithm_repair_sandbox_manifest["all_ok"]),
        "algorithm_repair_sandbox_apply": bool(algorithm_repair_sandbox_apply_manifest["all_ok"]),
        "algorithm_repair_sandbox_rerun": bool(algorithm_repair_sandbox_rerun_manifest["all_ok"]),
        "algorithm_repair_sandbox_patch_eval": bool(algorithm_repair_sandbox_patch_eval_manifest["all_ok"]),
        "algorithm_repair_patch_training_export": bool(algorithm_repair_patch_training_manifest["all_ok"]),
        "algorithm_repair_patch_policy_model": bool(algorithm_repair_patch_policy_manifest["all_ok"]),
        "algorithm_repair_production_patch_plan": bool(algorithm_repair_production_patch_plan_manifest["all_ok"]),
        "algorithm_repair_reviewed_patch_apply": bool(algorithm_repair_reviewed_patch_apply_manifest["all_ok"]),
        "algorithm_repair_reviewed_patch_validate": bool(algorithm_repair_reviewed_patch_validate_manifest["all_ok"]),
    }
    benchmark_cache_gate_names = (
        "research_benchmark",
        "formal_gap_skeletons",
        "research_trace_audit",
        "research_gap_backlog",
        "formalization_target_audit",
        "formal_gap_task_export",
        "autoform_target_export",
        "proof_bank_expansion_export",
        "research_training_export",
        "research_policy_baseline",
        "next_iteration_queue",
        "research_report",
    )
    if (
        benchmark_cache_info["enabled"]
        and benchmark_cache_status == "miss"
        and all(bool(gates[name]) for name in benchmark_cache_gate_names)
    ):
        _store_cached_research_benchmark(cache_info=benchmark_cache_info, source_dir=benchmark_dir)
        benchmark_cache_stored = True
        stage_start = _record_stage(stage_timings, "research_benchmark_cache_store", stage_start)
    total_elapsed_ms = int((time.perf_counter() - audit_start) * 1000)
    slowest_stages = sorted(
        stage_timings,
        key=lambda row: (-int(row["elapsed_ms"]), str(row["stage"])),
    )[:8]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "n_runs": config.n_runs,
            "seed": config.seed,
            "frontier_smoke_runs": config.frontier_smoke_runs,
            "use_axle": config.use_axle,
            "use_local_lean": config.use_local_lean,
            "local_lean_project": config.local_lean_project or "",
            "local_lean_timeout": config.local_lean_timeout,
            "formal_source_index_cache": config.formal_source_index_cache or "",
            "refresh_formal_source_index_cache": config.refresh_formal_source_index_cache,
            "lean_rag_db": config.lean_rag_db or "",
            "frontier_smoke_cache": config.frontier_smoke_cache or "",
            "refresh_frontier_smoke_cache": config.refresh_frontier_smoke_cache,
            "formal_source_graph_cache": config.formal_source_graph_cache or "",
            "refresh_formal_source_graph_cache": config.refresh_formal_source_graph_cache,
            "research_benchmark_cache": config.research_benchmark_cache or "",
            "refresh_research_benchmark_cache": config.refresh_research_benchmark_cache,
            "question_file": str(question_file or Path("examples/research_questions.json")),
        },
        "all_gates_passed": all(gates.values()),
        "gates": gates,
        "timings": {
            "total_elapsed_ms": total_elapsed_ms,
            "stages": stage_timings,
            "slowest_stages": slowest_stages,
        },
        "counts": {
            "questions": len(questions),
            "audit_total_elapsed_ms": total_elapsed_ms,
            "audit_slowest_stage": str(slowest_stages[0]["stage"]) if slowest_stages else "",
            "audit_slowest_stage_elapsed_ms": int(slowest_stages[0]["elapsed_ms"]) if slowest_stages else 0,
            "frontier_questions": frontier_manifest["n_questions"],
            "frontier_supported": frontier_manifest["n_supported"],
            "frontier_unsupported": frontier_manifest["n_unsupported"],
            "frontier_precision_ok": frontier_precision_manifest["n_ok"],
            "frontier_precision_supported": frontier_precision_manifest["n_supported"],
            "frontier_precision_flagged": frontier_precision_manifest["n_flagged"],
            "frontier_backlog_ok": frontier_backlog_manifest["n_ok"],
            "frontier_backlog_total": frontier_backlog_manifest["n_backlog"],
            "frontier_backlog_domains": len(frontier_backlog_manifest["by_domain"]),
            "frontier_backlog_required_primitives": len(frontier_backlog_manifest["by_required_primitive"]),
            "architecture_components_achieved": architecture_manifest["component_counts"].get("ACHIEVED", 0),
            "architecture_components_partial": architecture_manifest["component_counts"].get("PARTIAL", 0),
            "architecture_components_not_implemented": architecture_manifest["component_counts"].get("NOT_IMPLEMENTED", 0),
            "architecture_has_live_revision_loop": architecture_manifest["has_live_revision_loop"],
            "architecture_feedback_routes": len(architecture_manifest["feedback_routes"]),
            "research_capability_achieved": capability_report["n_achieved"],
            "research_capability_partial": capability_report["n_partial"],
            "research_capability_not_achieved": capability_report["n_not_achieved"],
            "research_capability_goal_complete": capability_report["goal_complete"],
            "research_capability_current_release_gate_met": capability_report["n_current_release_gate_met"],
            "research_capability_current_release_gate": capability_report["n_current_release_gate"],
            "frontier_smoke_questions": frontier_smoke_manifest["n_selected"],
            "frontier_smoke_runs": frontier_smoke_manifest["config"]["n_runs"],
            "frontier_smoke_total_elapsed_ms": frontier_smoke_manifest["counts"][
                "frontier_smoke_total_elapsed_ms"
            ],
            "frontier_smoke_slowest_stage": frontier_smoke_manifest["counts"][
                "frontier_smoke_slowest_stage"
            ],
            "frontier_smoke_slowest_stage_elapsed_ms": frontier_smoke_manifest["counts"][
                "frontier_smoke_slowest_stage_elapsed_ms"
            ],
            "frontier_smoke_cache_enabled": frontier_smoke_manifest["counts"][
                "frontier_smoke_cache_enabled"
            ],
            "frontier_smoke_cache_status": frontier_smoke_manifest["counts"][
                "frontier_smoke_cache_status"
            ],
            "frontier_smoke_cache_key": frontier_smoke_manifest["counts"][
                "frontier_smoke_cache_key"
            ],
            "frontier_smoke_ready": frontier_smoke_manifest["counts"]["ready_with_gaps"],
            "frontier_theory_targets_scored": frontier_smoke_manifest["counts"]["theory_targets_scored"],
            "frontier_theory_targets_total": frontier_smoke_manifest["counts"]["theory_targets_total"],
            "frontier_theory_expected_results": frontier_smoke_manifest["counts"]["theory_expected_results"],
            "frontier_theory_expected_results_covered": frontier_smoke_manifest["counts"][
                "theory_expected_results_covered"
            ],
            "frontier_theory_expected_result_coverage_rate": frontier_smoke_manifest["counts"][
                "theory_expected_result_coverage_rate"
            ],
            "fresh_holdout_frontier_entries": fresh_holdout_manifest["n_entries"],
            "fresh_holdout_frontier_supported": fresh_holdout_manifest["n_supported"],
            "fresh_holdout_frontier_unsupported": fresh_holdout_manifest["n_unsupported"],
            "fresh_holdout_frontier_scored_traces": fresh_holdout_manifest["n_scored_traces"],
            "fresh_holdout_frontier_expected_results": fresh_holdout_manifest["n_expected_results"],
            "fresh_holdout_frontier_expected_results_covered": fresh_holdout_manifest[
                "n_covered_expected_results"
            ],
            "fresh_holdout_frontier_expected_result_coverage_rate": fresh_holdout_manifest[
                "expected_result_coverage_rate"
            ],
            "fresh_holdout_frontier_all_entries_supported": fresh_holdout_manifest[
                "all_entries_supported"
            ],
            "fresh_holdout_frontier_identity_withheld": fresh_holdout_manifest[
                "all_prompt_identity_withheld"
            ],
            "fresh_holdout_frontier_source_leakage_detected": fresh_holdout_manifest[
                "source_identity_leakage_detected"
            ],
            "fresh_holdout_frontier_traces_ok": fresh_holdout_manifest["traces_ok"],
            "fresh_holdout_frontier_all_ok": fresh_holdout_manifest["all_ok"],
            "research_intake_supported": intake_manifest["n_supported"],
            "research_intake_supported_accepted": intake_manifest["n_supported_accepted"],
            "research_intake_unsupported": intake_manifest["n_unsupported"],
            "research_intake_unsupported_rejected": intake_manifest["n_unsupported_rejected"],
            "adversarial_intake_cases": adversarial_intake_manifest["n_cases"],
            "adversarial_intake_ok": adversarial_intake_manifest["n_ok"],
            "adversarial_intake_rejected": adversarial_intake_manifest["n_rejected"],
            "adversarial_intake_accepted": adversarial_intake_manifest["n_accepted"],
            "research_knowledge_cards": knowledge_manifest["n_cards"],
            "research_knowledge_sources_ok": knowledge_manifest["n_source_ok"],
            "research_source_inventory_ok": knowledge_manifest["source_inventory"]["n_ok"],
            "research_source_inventory_total": knowledge_manifest["source_inventory"]["n_sources"],
            "research_knowledge_problem_rows": knowledge_manifest["n_problem_rows"],
            "research_knowledge_problem_ok": knowledge_manifest["n_problem_ok"],
            "autoform_harness_ready": autoform_harness_manifest["ready_for_integration"],
            "formal_source_graph_symbols": formal_source_graph_manifest["n_symbol_nodes"],
            "formal_source_graph_edges": formal_source_graph_manifest["n_edges"],
            "formal_source_graph_queries_ok": formal_source_graph_manifest["n_query_ok"],
            "formal_source_graph_queries": formal_source_graph_manifest["n_queries"],
            "formal_source_graph_cache_enabled": formal_source_graph_manifest["cache"]["enabled"],
            "formal_source_graph_cache_status": formal_source_graph_manifest["cache"]["status"],
            "formal_source_graph_cache_key": formal_source_graph_manifest["cache"]["cache_key"],
            "formal_source_retrieval_benchmark_cases": formal_source_retrieval_benchmark_manifest["n_cases"],
            "formal_source_retrieval_benchmark_ok": formal_source_retrieval_benchmark_manifest["n_ok"],
            "formal_source_retrieval_benchmark_recall_at_k": formal_source_retrieval_benchmark_manifest[
                "recall_at_k"
            ],
            "formal_source_retrieval_benchmark_mrr": formal_source_retrieval_benchmark_manifest[
                "mean_reciprocal_rank"
            ],
            "formal_source_retrieval_ablation_cases": formal_source_retrieval_ablation_manifest["n_cases"],
            "formal_source_retrieval_ablation_new_hits": formal_source_retrieval_ablation_manifest["n_new_hits"],
            "formal_source_retrieval_ablation_lost_hits": formal_source_retrieval_ablation_manifest["n_lost_hits"],
            "formal_source_retrieval_ablation_rank_improved": formal_source_retrieval_ablation_manifest[
                "n_rank_improved"
            ],
            "formal_source_retrieval_ablation_rank_regressed": formal_source_retrieval_ablation_manifest[
                "n_rank_regressed"
            ],
            "formal_source_index_cache_status": getattr(formal_source_retriever, "cache_status", "unknown"),
            "formal_source_index_cache_path": getattr(formal_source_retriever, "cache_path", ""),
            "lean_rag_dependency_graph_enabled": getattr(
                formal_source_retriever,
                "lean_rag_dependency_graph_enabled",
                False,
            ),
            "lean_rag_dependency_graph_path": getattr(
                formal_source_retriever,
                "lean_rag_dependency_graph_path",
                "",
            ),
            "lean_rag_dependency_graph_auto_discovered": getattr(
                formal_source_retriever,
                "lean_rag_dependency_graph_auto_discovered",
                False,
            ),
            "research_ready_with_gaps": benchmark_manifest["n_ready_with_gaps"],
            "research_simulation_flagged": benchmark_manifest["n_simulation_flagged"],
            "research_formal_blocked": benchmark_manifest["n_formal_blocked"],
            "research_benchmark_cache_enabled": benchmark_cache_info["enabled"],
            "research_benchmark_cache_status": benchmark_cache_status,
            "research_benchmark_cache_key": benchmark_cache_info["key"],
            "research_benchmark_cache_stored": benchmark_cache_stored,
            "retrieval_top_k": retrieval_manifest["top_k"],
            "retrieval_total": retrieval_manifest["n_obligations"],
            "research_algorithms_ok": algorithm_manifest["n_ok"],
            "research_algorithms_total": algorithm_manifest["n_algorithms"],
            "algorithm_simulation_stress_cases": algorithm_simulation_stress_manifest[
                "n_seeded_simulations"
            ],
            "algorithm_simulation_stress_algorithms": algorithm_simulation_stress_manifest[
                "n_algorithms"
            ],
            "algorithm_simulation_stress_seeds": algorithm_simulation_stress_manifest[
                "n_seeds"
            ],
            "algorithm_simulation_stress_all_passed": algorithm_simulation_stress_manifest[
                "all_passed"
            ],
            "algorithm_simulation_stress_all_finite_metrics": algorithm_simulation_stress_manifest[
                "all_finite_metrics"
            ],
            "algorithm_simulation_stress_all_stress_ledgers_ok": algorithm_simulation_stress_manifest[
                "all_stress_ledgers_ok"
            ],
            "algorithm_simulation_stress_all_diagnoses_ok": algorithm_simulation_stress_manifest[
                "all_diagnoses_ok"
            ],
            "algorithm_simulation_stress_multi_seed_checked": algorithm_simulation_stress_manifest[
                "multi_seed_stability_checked"
            ],
            "algorithm_simulation_stress_flags": algorithm_simulation_stress_manifest[
                "n_stress_flags"
            ],
            "proofs_verified": proof_manifest["n_verified"],
            "proofs_kernel_verified": proof_manifest["n_kernel_verified"],
            "proofs_non_kernel_verified": proof_manifest["n_non_kernel_verified"],
            "proofs_all_kernel_verified": proof_manifest["all_kernel_verified"],
            "proof_verification_strength": proof_manifest["verification_strength"],
            "proofs_total": proof_manifest["n_obligations"],
            "verifier_cache_hits": verifier.cache_hits,
            "verifier_cache_misses": verifier.cache_misses,
            "verifier_cache_size": verifier.cache_info()["size"],
            "proof_dependency_edges": proof_manifest["dependency_graph"]["n_edges"],
            "proof_dependencies_ok": proof_manifest["dependency_graph"]["all_ok"],
            "proof_training_examples": proof_training_manifest["n_sft_examples"],
            "proof_training_kernel_examples": proof_training_manifest["n_kernel_positive_attempts"],
            "proof_training_train": proof_training_manifest["n_train"],
            "proof_training_validation": proof_training_manifest["n_validation"],
            "proof_attempt_negatives": proof_manifest["proof_attempt_log"]["n_negative"],
            "proof_negative_controls_enabled": proof_manifest["negative_controls"]["enabled"],
            "proof_repair_examples": proof_repair_manifest["n_repair_examples"],
            "proof_repair_negative_attempts": proof_repair_manifest["n_negative_attempts"],
            "proof_repair_train": proof_repair_manifest["n_train"],
            "proof_repair_validation": proof_repair_manifest["n_validation"],
            "proof_policy_baseline_top1_exact": proof_policy_manifest["top1_exact"],
            "proof_policy_baseline_top_k_exact": proof_policy_manifest["top_k_exact"],
            "proof_policy_baseline_validation": proof_policy_manifest["n_validation"],
            "proof_policy_baseline_context_hits": proof_policy_manifest["predicted_in_retrieved_context"],
            "proof_policy_model_train": proof_policy_model_manifest["n_train"],
            "proof_policy_model_validation": proof_policy_model_manifest["n_validation"],
            "proof_policy_model_features": proof_policy_model_manifest["n_features"],
            "proof_policy_model_train_top1_exact": proof_policy_model_manifest["train_top1_exact"],
            "proof_policy_model_validation_top1_exact": proof_policy_model_manifest["validation_top1_exact"],
            "proof_policy_model_validation_top_k_exact": proof_policy_model_manifest["validation_top_k_exact"],
            "proof_search_obligations": proof_search_manifest["n_obligations"],
            "proof_search_solved": proof_search_manifest["n_solved"],
            "proof_search_kernel_verified": proof_search_manifest["n_kernel_verified"],
            "proof_search_nodes_expanded": proof_search_manifest["nodes_expanded"],
            "proof_search_mean_nodes_expanded": proof_search_manifest["mean_nodes_expanded"],
            "proof_search_tactic_template_candidates_total": proof_search_manifest[
                "tactic_template_candidates_total"
            ],
            "proof_search_tactic_template_nodes_expanded": proof_search_manifest[
                "tactic_template_nodes_expanded"
            ],
            "proof_search_retrieval_candidates_total": proof_search_manifest[
                "retrieval_candidates_total"
            ],
            "proof_search_retrieval_candidate_nodes_expanded": proof_search_manifest[
                "retrieval_candidate_nodes_expanded"
            ],
            "proof_search_formal_source_retriever_enabled": proof_search_manifest[
                "formal_source_retriever_enabled"
            ],
            "proof_search_formal_source_candidates_total": proof_search_manifest[
                "formal_source_candidates_total"
            ],
            "proof_search_formal_source_candidate_nodes_expanded": proof_search_manifest[
                "formal_source_candidate_nodes_expanded"
            ],
            "proof_search_bootstrap_nodes_expanded": proof_search_bootstrap_manifest["nodes_expanded"],
            "proof_search_bootstrap_process_examples": proof_search_bootstrap_training_manifest[
                "n_process_examples"
            ],
            "proof_search_policy_model_enabled": proof_search_manifest["policy_model_enabled"],
            "proof_search_policy_scored_expanded_nodes": proof_search_manifest[
                "policy_scored_expanded_nodes"
            ],
            "proof_search_value_model_enabled": proof_search_manifest["value_model_enabled"],
            "proof_search_value_scored_expanded_nodes": proof_search_manifest[
                "value_scored_expanded_nodes"
            ],
            "proof_search_retrieval_ablation_solved_delta": proof_search_retrieval_ablation_manifest[
                "solved_delta"
            ],
            "proof_search_retrieval_ablation_candidate_delta": proof_search_retrieval_ablation_manifest[
                "formal_source_candidate_delta"
            ],
            "proof_search_retrieval_ablation_node_delta": proof_search_retrieval_ablation_manifest[
                "nodes_expanded_delta"
            ],
            "proof_search_retrieval_ablation_no_solved_regression": proof_search_retrieval_ablation_manifest[
                "no_solved_regression"
            ],
            "proof_search_process_examples": proof_search_training_manifest["n_process_examples"],
            "proof_search_process_positive": proof_search_training_manifest["n_positive"],
            "proof_search_process_negative": proof_search_training_manifest["n_negative"],
            "proof_search_process_train": proof_search_training_manifest["n_train"],
            "proof_search_process_validation": proof_search_training_manifest["n_validation"],
            "proof_search_value_train": proof_search_value_manifest["n_train"],
            "proof_search_value_validation": proof_search_value_manifest["n_validation"],
            "proof_search_value_features": proof_search_value_manifest["n_features"],
            "proof_search_value_train_accuracy": proof_search_value_manifest["train_accuracy"],
            "proof_search_value_validation_accuracy": proof_search_value_manifest["validation_accuracy"],
            "prover_components_total": prover_component_report["summary"]["components"],
            "prover_components_ready": prover_component_report["summary"]["ready"],
            "prover_components_partial": prover_component_report["summary"]["partial"],
            "prover_components_missing_or_not_trained": prover_component_report["summary"]["missing_or_not_trained"],
            "prover_component_goal_complete": prover_component_report["summary"]["honest_goal_complete"],
            "research_traces_ok": trace_manifest["n_ok"],
            "research_traces_total": trace_manifest["n_traces"],
            "theorem_goal_proof_obligations": trace_manifest["n_theorem_goal_proof_obligations"],
            "verified_theorem_goal_proof_obligations": trace_manifest[
                "n_verified_theorem_goal_proof_obligations"
            ],
            "unique_theorem_goal_proof_obligations": trace_manifest[
                "n_unique_theorem_goal_proof_obligations"
            ],
            "unique_verified_theorem_goal_proof_obligations": trace_manifest[
                "n_unique_verified_theorem_goal_proof_obligations"
            ],
            "theorem_goal_proof_obligation_coverage_rate": trace_manifest[
                "theorem_goal_proof_obligation_coverage_rate"
            ],
            "formal_gaps": sum(row["formal"]["gaps"] for row in benchmark_manifest["questions"]),
            "formalized_gaps": sum(row["formal"]["formalized_gaps"] for row in benchmark_manifest["questions"]),
            "gap_backlog_ok": gap_backlog_manifest["n_ok"],
            "gap_backlog_total": gap_backlog_manifest["n_gaps"],
            "missing_formal_primitives": len(gap_backlog_manifest["by_required_primitive"]),
            "formalization_targets_ok": formalization_target_manifest["n_ok"],
            "formalization_targets_total": formalization_target_manifest["n_targets"],
            "formalization_targets_with_proof_bank_bridge": formalization_target_manifest[
                "n_with_proof_bank_bridge"
            ],
            "formal_gap_lean_tasks_ok": formal_gap_task_manifest["n_ok"],
            "formal_gap_lean_tasks_total": formal_gap_task_manifest["n_tasks"],
            "autoform_targets_ok": autoform_target_manifest["n_ok"],
            "autoform_targets_total": autoform_target_manifest["n_targets"],
            "proof_bank_expansion_candidates_ok": proof_bank_expansion_manifest["n_ok"],
            "proof_bank_expansion_candidates_total": proof_bank_expansion_manifest["n_candidates"],
            "proof_bank_expansion_bridge_ready": proof_bank_expansion_manifest["n_bridge_ready"],
            "proof_bank_expansion_blocked_placeholder": proof_bank_expansion_manifest[
                "n_blocked_placeholder"
            ],
            "proof_bank_expansion_candidate_ready": proof_bank_expansion_manifest["n_candidate_ready"],
            "proof_bank_expansion_compose_existing_bridge_chain": proof_bank_expansion_manifest[
                "n_compose_existing_bridge_chain"
            ],
            "proof_bank_expansion_add_minimal_wrapper": proof_bank_expansion_manifest[
                "n_add_minimal_wrapper"
            ],
            "proof_bank_expansion_design_bridge_lemma": proof_bank_expansion_manifest[
                "n_design_bridge_lemma"
            ],
            "proof_bank_expansion_design_from_first_principles": proof_bank_expansion_manifest[
                "n_design_from_first_principles"
            ],
            "primitive_source_coverage_primitives": primitive_source_coverage_manifest["n_primitives"],
            "primitive_source_coverage_direct_wrapper_possible": primitive_source_coverage_manifest[
                "n_direct_wrapper_possible"
            ],
            "primitive_source_coverage_bridge_lemma_needed": primitive_source_coverage_manifest[
                "n_bridge_lemma_needed"
            ],
            "primitive_source_coverage_source_only_not_importable": primitive_source_coverage_manifest[
                "n_source_only_not_importable"
            ],
            "primitive_source_coverage_no_source_found": primitive_source_coverage_manifest[
                "n_no_source_found"
            ],
            "primitive_source_coverage_external_supported": primitive_source_coverage_manifest[
                "n_external_source_supported"
            ],
            "primitive_source_coverage_compose_existing_bridge_chain": primitive_source_coverage_manifest[
                "n_compose_existing_bridge_chain"
            ],
            "primitive_source_coverage_add_minimal_wrapper": primitive_source_coverage_manifest[
                "n_add_minimal_wrapper"
            ],
            "primitive_source_coverage_design_bridge_lemma": primitive_source_coverage_manifest[
                "n_design_bridge_lemma"
            ],
            "primitive_source_coverage_port_external_source": primitive_source_coverage_manifest[
                "n_port_external_source"
            ],
            "primitive_source_coverage_design_from_first_principles": primitive_source_coverage_manifest[
                "n_design_from_first_principles"
            ],
            "primitive_source_coverage_lean_rag_enabled": primitive_source_coverage_manifest[
                "lean_rag_dependency_graph_enabled"
            ],
            "research_training_sft_examples": research_training_manifest["n_sft_examples"],
            "research_training_train": research_training_manifest["n_train"],
            "research_training_validation": research_training_manifest["n_validation"],
            "research_training_grpo_tasks": research_training_manifest["n_grpo_tasks"],
            "research_training_traces": research_training_manifest["n_traces"],
            "research_policy_baseline_validation": research_policy_manifest["n_validation"],
            "research_policy_baseline_same_task": research_policy_manifest["same_task"],
            "research_policy_baseline_same_task_rate": research_policy_manifest["same_task_rate"],
            "research_policy_baseline_mean_json_key_f1": research_policy_manifest["mean_json_key_f1"],
            "research_policy_baseline_valid_json": research_policy_manifest["predicted_valid_json"],
            "next_iteration_items": next_iteration_manifest["n_items"],
            "next_iteration_actionable_items": next_iteration_manifest["n_actionable_items"],
            "next_iteration_ok": next_iteration_manifest["n_ok"],
            "next_iteration_formal_verifier_items": next_iteration_manifest["by_owner"].get(
                "formal_verifier",
                0,
            ),
            "research_report_questions": research_report_manifest["counts"]["questions"],
            "research_report_formal_gaps": research_report_manifest["counts"]["formal_gaps"],
            "research_report_simulations_passed": research_report_manifest["counts"]["simulations_passed"],
            "research_report_simulations": research_report_manifest["counts"]["simulations"],
            "research_loop_questions": research_loop_manifest["n_questions"],
            "research_loop_traces_written": research_loop_manifest["all_loop_traces_written"],
            "research_loop_repair_tasks_exported": research_loop_manifest["all_repair_tasks_exported"],
            "research_loop_repair_tasks": research_loop_manifest["n_repair_tasks"],
            "research_loop_live_repair_artifacts_exported": research_loop_manifest[
                "all_live_repair_artifacts_exported"
            ],
            "research_loop_live_repair_artifacts": research_loop_manifest["n_live_repair_artifacts"],
            "research_loop_theory_revisions": research_loop_manifest["n_theory_revisions"],
            "research_loop_live_repair_artifacts_contract_ok": research_loop_manifest[
                "live_repair_artifacts_contract_ok"
            ],
            "research_loop_live_repair_artifacts_kernel_verified": research_loop_manifest[
                "live_repair_artifacts_kernel_verified"
            ],
            "research_loop_status_kinds": len(research_loop_manifest["status_counts"]),
            "research_loop_repair_tasks_ok": research_loop_repair_manifest["n_ok"],
            "research_loop_repair_sft_examples": research_loop_repair_manifest["n_sft_examples"],
            "research_loop_repair_sft_train": research_loop_repair_manifest["n_train"],
            "research_loop_repair_sft_validation": research_loop_repair_manifest["n_validation"],
            "research_loop_live_repair_artifacts_ok": research_loop_live_repair_manifest["n_ok"],
            "research_loop_live_repair_sft_examples": research_loop_live_repair_manifest[
                "n_sft_examples"
            ],
            "research_loop_live_repair_sft_train": research_loop_live_repair_manifest["n_train"],
            "research_loop_live_repair_sft_validation": research_loop_live_repair_manifest[
                "n_validation"
            ],
            "algorithm_repair_promotion_candidates": algorithm_repair_promotion_manifest["n_candidates"],
            "algorithm_repair_promotion_candidates_ok": algorithm_repair_promotion_manifest["n_ok"],
            "algorithm_repair_promotion_artifacts": algorithm_repair_promotion_manifest[
                "n_algorithm_repair_artifacts"
            ],
            "algorithm_repair_sandbox_candidates": algorithm_repair_sandbox_manifest["n_candidates"],
            "algorithm_repair_sandbox_candidates_ok": algorithm_repair_sandbox_manifest["n_ok"],
            "algorithm_repair_sandbox_apply_candidates": algorithm_repair_sandbox_apply_manifest["n_candidates"],
            "algorithm_repair_sandbox_apply_candidates_ok": algorithm_repair_sandbox_apply_manifest["n_ok"],
            "algorithm_repair_sandbox_rerun_candidates": algorithm_repair_sandbox_rerun_manifest["n_candidates"],
            "algorithm_repair_sandbox_rerun_candidates_ok": algorithm_repair_sandbox_rerun_manifest["n_ok"],
            "algorithm_repair_sandbox_patch_eval_candidates": algorithm_repair_sandbox_patch_eval_manifest[
                "n_candidates"
            ],
            "algorithm_repair_sandbox_patch_eval_candidates_ok": algorithm_repair_sandbox_patch_eval_manifest[
                "n_ok"
            ],
            "algorithm_repair_sandbox_patch_eval_executed": algorithm_repair_sandbox_patch_eval_manifest[
                "n_isolated_patches_executed"
            ],
            "algorithm_repair_sandbox_patch_eval_before_after": algorithm_repair_sandbox_patch_eval_manifest[
                "n_before_after_comparisons"
            ],
            "algorithm_repair_sandbox_patch_eval_production_patches": algorithm_repair_sandbox_patch_eval_manifest[
                "n_production_patches_applied"
            ],
            "algorithm_repair_sandbox_patch_eval_promotion_ready": algorithm_repair_sandbox_patch_eval_manifest[
                "n_promotion_ready"
            ],
            "algorithm_repair_patch_training_examples": algorithm_repair_patch_training_manifest[
                "n_training_examples"
            ],
            "algorithm_repair_patch_training_train": algorithm_repair_patch_training_manifest["n_train"],
            "algorithm_repair_patch_training_validation": algorithm_repair_patch_training_manifest[
                "n_validation"
            ],
            "algorithm_repair_patch_training_production_patches": algorithm_repair_patch_training_manifest[
                "n_production_patches_applied"
            ],
            "algorithm_repair_patch_training_promotion_ready": algorithm_repair_patch_training_manifest[
                "n_promotion_ready"
            ],
            "algorithm_repair_patch_policy_train": algorithm_repair_patch_policy_manifest["n_train"],
            "algorithm_repair_patch_policy_validation": algorithm_repair_patch_policy_manifest[
                "n_validation"
            ],
            "algorithm_repair_patch_policy_training_pairs": algorithm_repair_patch_policy_manifest[
                "n_training_pairs"
            ],
            "algorithm_repair_patch_policy_features": algorithm_repair_patch_policy_manifest["n_features"],
            "algorithm_repair_patch_policy_validation_safe_decision_accuracy": algorithm_repair_patch_policy_manifest[
                "validation_safe_decision_accuracy"
            ],
            "algorithm_repair_patch_policy_validation_chose_gold": algorithm_repair_patch_policy_manifest[
                "validation_chose_gold"
            ],
            "algorithm_repair_patch_policy_validation_rejected_unsafe": algorithm_repair_patch_policy_manifest[
                "validation_rejected_unsafe"
            ],
            "algorithm_repair_production_patch_plans": algorithm_repair_production_patch_plan_manifest[
                "n_plans"
            ],
            "algorithm_repair_production_patch_plans_ok": algorithm_repair_production_patch_plan_manifest[
                "n_ok"
            ],
            "algorithm_repair_production_patch_review_required": algorithm_repair_production_patch_plan_manifest[
                "n_review_required"
            ],
            "algorithm_repair_production_patch_applied": algorithm_repair_production_patch_plan_manifest[
                "n_production_patches_applied"
            ],
            "algorithm_repair_production_patch_promotion_ready": algorithm_repair_production_patch_plan_manifest[
                "n_promotion_ready"
            ],
            "algorithm_repair_reviewed_patch_apply_candidates": algorithm_repair_reviewed_patch_apply_manifest[
                "n_plans"
            ],
            "algorithm_repair_reviewed_patch_apply_candidates_ok": algorithm_repair_reviewed_patch_apply_manifest[
                "n_ok"
            ],
            "algorithm_repair_reviewed_patch_apply_source_changed": algorithm_repair_reviewed_patch_apply_manifest[
                "n_source_changed"
            ],
            "algorithm_repair_reviewed_patch_apply_syntax_valid": algorithm_repair_reviewed_patch_apply_manifest[
                "n_syntax_valid"
            ],
            "algorithm_repair_reviewed_patch_apply_target_found": algorithm_repair_reviewed_patch_apply_manifest[
                "n_target_symbol_found"
            ],
            "algorithm_repair_reviewed_patch_apply_production_patches": algorithm_repair_reviewed_patch_apply_manifest[
                "n_production_patches_applied"
            ],
            "algorithm_repair_reviewed_patch_apply_promotion_ready": algorithm_repair_reviewed_patch_apply_manifest[
                "n_promotion_ready"
            ],
            "algorithm_repair_reviewed_patch_validate_candidates": algorithm_repair_reviewed_patch_validate_manifest[
                "n_candidates"
            ],
            "algorithm_repair_reviewed_patch_validate_candidates_ok": algorithm_repair_reviewed_patch_validate_manifest[
                "n_ok"
            ],
            "algorithm_repair_reviewed_patch_validate_import_ok": algorithm_repair_reviewed_patch_validate_manifest[
                "n_import_ok"
            ],
            "algorithm_repair_reviewed_patch_validate_algorithm_audit_ok": algorithm_repair_reviewed_patch_validate_manifest[
                "n_algorithm_audit_ok"
            ],
            "algorithm_repair_reviewed_patch_validate_simulation_completed": algorithm_repair_reviewed_patch_validate_manifest[
                "n_simulation_completed"
            ],
            "algorithm_repair_reviewed_patch_validate_patched_metric_present": algorithm_repair_reviewed_patch_validate_manifest[
                "n_patched_metric_present"
            ],
            "algorithm_repair_reviewed_patch_validate_finite_metrics_ok": algorithm_repair_reviewed_patch_validate_manifest[
                "n_finite_metrics_ok"
            ],
            "algorithm_repair_reviewed_patch_validate_production_patches": algorithm_repair_reviewed_patch_validate_manifest[
                "n_production_patches_applied"
            ],
            "algorithm_repair_reviewed_patch_validate_promotion_ready": algorithm_repair_reviewed_patch_validate_manifest[
                "n_promotion_ready"
            ],
        },
        "questions": benchmark_manifest["questions"],
        "provenance": benchmark_manifest["provenance"],
        "artifacts": {
            "frontier_coverage_audit": str(
                out_dir / "frontier_coverage_audit" / "frontier_coverage_manifest.json"
            ),
            "frontier_coverage_report": str(out_dir / "frontier_coverage_audit" / "frontier_coverage.md"),
            "frontier_precision_audit": str(
                out_dir / "frontier_precision_audit" / "frontier_precision_manifest.json"
            ),
            "frontier_precision_report": str(out_dir / "frontier_precision_audit" / "frontier_precision.md"),
            "frontier_backlog_audit": str(
                out_dir / "frontier_backlog_audit" / "frontier_backlog_manifest.json"
            ),
            "frontier_backlog_report": str(out_dir / "frontier_backlog_audit" / "frontier_backlog.md"),
            "architecture_audit": str(out_dir / "architecture_audit" / "architecture_audit_manifest.json"),
            "architecture_report": str(out_dir / "architecture_audit" / "architecture_audit.md"),
            "research_capability_audit": str(
                out_dir / "research_capability_audit" / "research_capability_audit_manifest.json"
            ),
            "research_capability_report": str(
                out_dir / "research_capability_audit" / "research_capability_audit.md"
            ),
            "frontier_smoke_benchmark": str(
                out_dir / "frontier_smoke_benchmark" / "frontier_smoke_manifest.json"
            ),
            "frontier_theory_target_audit": str(
                out_dir
                / "frontier_smoke_benchmark"
                / "frontier_theory_target_audit"
                / "frontier_theory_target_manifest.json"
            ),
            "frontier_theory_target_report": str(
                out_dir
                / "frontier_smoke_benchmark"
                / "frontier_theory_target_audit"
                / "frontier_theory_target.md"
            ),
            "research_intake_audit": str(
                out_dir / "research_intake_audit" / "research_intake_audit_manifest.json"
            ),
            "adversarial_intake_audit": str(
                out_dir / "adversarial_intake_audit" / "adversarial_intake_manifest.json"
            ),
            "adversarial_intake_report": str(
                out_dir / "adversarial_intake_audit" / "adversarial_intake.md"
            ),
            "research_knowledge_audit": str(
                out_dir / "research_knowledge_audit" / "research_knowledge_audit_manifest.json"
            ),
            "research_knowledge_report": str(
                out_dir / "research_knowledge_audit" / "research_knowledge_audit.md"
            ),
            "research_source_inventory": str(
                out_dir
                / "research_knowledge_audit"
                / "source_inventory"
                / "research_source_inventory_manifest.json"
            ),
            "research_source_inventory_report": str(
                out_dir / "research_knowledge_audit" / "source_inventory" / "research_source_inventory.md"
            ),
            "autoform_harness": str(out_dir / "autoform_harness" / "autoform_harness_manifest.json"),
            "autoform_harness_report": str(out_dir / "autoform_harness" / "autoform_harness.md"),
            "retrieval_audit": str(out_dir / "retrieval_audit" / "retrieval_audit_manifest.json"),
            "formal_source_graph": str(out_dir / "formal_source_graph" / "formal_source_graph_manifest.json"),
            "formal_source_graph_report": str(out_dir / "formal_source_graph" / "formal_source_graph.md"),
            "formal_source_retrieval_benchmark": str(
                out_dir
                / "formal_source_retrieval_benchmark"
                / "formal_source_retrieval_benchmark_manifest.json"
            ),
            "formal_source_retrieval_benchmark_report": str(
                out_dir
                / "formal_source_retrieval_benchmark"
                / "formal_source_retrieval_benchmark.md"
            ),
            "formal_source_retrieval_ablation": str(
                out_dir
                / "formal_source_retrieval_ablation"
                / "formal_source_retrieval_ablation_manifest.json"
            ),
            "formal_source_retrieval_ablation_report": str(
                out_dir
                / "formal_source_retrieval_ablation"
                / "formal_source_retrieval_ablation.md"
            ),
            "fresh_holdout_frontier_audit": str(
                out_dir / "fresh_holdout_frontier_audit" / "fresh_holdout_frontier_manifest.json"
            ),
            "fresh_holdout_frontier_report": str(
                out_dir / "fresh_holdout_frontier_audit" / "fresh_holdout_frontier.md"
            ),
            "research_algorithm_audit": str(
                out_dir / "research_algorithm_audit" / "research_algorithm_audit_manifest.json"
            ),
            "algorithm_simulation_stress_audit": str(
                out_dir
                / "algorithm_simulation_stress_audit"
                / "algorithm_simulation_stress_manifest.json"
            ),
            "algorithm_simulation_stress_report": str(
                out_dir / "algorithm_simulation_stress_audit" / "algorithm_simulation_stress.md"
            ),
            "proof_audit": str(out_dir / "proof_audit" / "proof_audit_manifest.json"),
            "proof_attempt_log": str(out_dir / "proof_audit" / "proof_attempts.jsonl"),
            "proof_training_export": str(out_dir / "proof_training_export" / "proof_training_manifest.json"),
            "proof_training_train": str(out_dir / "proof_training_export" / "proof_sft_train.jsonl"),
            "proof_training_validation": str(out_dir / "proof_training_export" / "proof_sft_validation.jsonl"),
            "proof_repair_export": str(out_dir / "proof_repair_export" / "proof_repair_manifest.json"),
            "proof_repair_train": str(out_dir / "proof_repair_export" / "proof_repair_train.jsonl"),
            "proof_repair_validation": str(out_dir / "proof_repair_export" / "proof_repair_validation.jsonl"),
            "proof_policy_baseline": str(
                out_dir / "proof_policy_baseline" / "proof_policy_baseline_manifest.json"
            ),
            "proof_policy_baseline_predictions": str(
                out_dir / "proof_policy_baseline" / "proof_policy_baseline_predictions.jsonl"
            ),
            "proof_policy_model": str(out_dir / "proof_policy_model" / "proof_policy_model_manifest.json"),
            "proof_policy_model_json": str(out_dir / "proof_policy_model" / "proof_policy_model.json"),
            "proof_policy_model_predictions": str(
                out_dir / "proof_policy_model" / "proof_policy_model_predictions.jsonl"
            ),
            "proof_search_audit": str(out_dir / "proof_search_audit" / "proof_search_audit_manifest.json"),
            "proof_search_results": str(out_dir / "proof_search_audit" / "proof_search_results.jsonl"),
            "proof_search_bootstrap_audit": str(
                out_dir / "proof_search_bootstrap_audit" / "proof_search_audit_manifest.json"
            ),
            "proof_search_bootstrap_results": str(
                out_dir / "proof_search_bootstrap_audit" / "proof_search_results.jsonl"
            ),
            "proof_search_bootstrap_training_export": str(
                out_dir / "proof_search_bootstrap_training_export" / "proof_search_training_manifest.json"
            ),
            "proof_search_retrieval_ablation": str(
                out_dir
                / "proof_search_retrieval_ablation"
                / "proof_search_retrieval_ablation_manifest.json"
            ),
            "proof_search_retrieval_ablation_report": str(
                out_dir / "proof_search_retrieval_ablation" / "proof_search_retrieval_ablation.md"
            ),
            "proof_search_training_export": str(
                out_dir / "proof_search_training_export" / "proof_search_training_manifest.json"
            ),
            "proof_search_process_train": str(
                out_dir / "proof_search_training_export" / "proof_search_process_train.jsonl"
            ),
            "proof_search_process_validation": str(
                out_dir / "proof_search_training_export" / "proof_search_process_validation.jsonl"
            ),
            "proof_search_value_model": str(
                out_dir / "proof_search_value_model" / "proof_search_value_model_manifest.json"
            ),
            "proof_search_value_model_json": str(
                out_dir / "proof_search_value_model" / "proof_search_value_model.json"
            ),
            "prover_component_audit": str(
                out_dir / "prover_component_audit" / "prover_component_audit_manifest.json"
            ),
            "prover_component_report": str(out_dir / "prover_component_audit" / "prover_component_audit.md"),
            "research_benchmark": str(out_dir / "research_benchmark" / "research_benchmark_manifest.json"),
            "formal_source_index": str(formal_source_index_path),
            "research_trace_audit": str(out_dir / "research_trace_audit" / "research_trace_audit_manifest.json"),
            "research_gap_backlog": str(
                out_dir / "research_gap_backlog" / "research_gap_backlog_manifest.json"
            ),
            "research_gap_backlog_report": str(out_dir / "research_gap_backlog" / "research_gap_backlog.md"),
            "formalization_target_audit": str(
                out_dir / "formalization_target_audit" / "formalization_target_manifest.json"
            ),
            "formalization_target_report": str(
                out_dir / "formalization_target_audit" / "formalization_targets.md"
            ),
            "formal_gap_lean_tasks": str(
                out_dir / "formal_gap_lean_tasks" / "formal_gap_lean_task_manifest.json"
            ),
            "formal_gap_lean_tasks_jsonl": str(
                out_dir / "formal_gap_lean_tasks" / "formal_gap_lean_tasks.jsonl"
            ),
            "formal_gap_lean_tasks_report": str(
                out_dir / "formal_gap_lean_tasks" / "formal_gap_lean_tasks.md"
            ),
            "autoform_targets": str(out_dir / "autoform_targets" / "autoform_targets_manifest.json"),
            "autoform_targets_yaml": str(out_dir / "autoform_targets" / "autoform_targets.yaml"),
            "autoform_targets_report": str(out_dir / "autoform_targets" / "autoform_targets.md"),
            "proof_bank_expansion": str(
                out_dir / "proof_bank_expansion" / "proof_bank_expansion_manifest.json"
            ),
            "proof_bank_expansion_report": str(out_dir / "proof_bank_expansion" / "proof_bank_expansion.md"),
            "proof_bank_expansion_lemma_proposals": str(
                out_dir / "proof_bank_expansion" / "lemma_proposals.jsonl"
            ),
            "proof_bank_expansion_theorem_hole_queue": str(
                out_dir / "proof_bank_expansion" / "theorem_hole_promotion_queue_manifest.json"
            ),
            "primitive_source_coverage": str(
                out_dir / "primitive_source_coverage" / "primitive_source_coverage_manifest.json"
            ),
            "primitive_source_coverage_report": str(
                out_dir / "primitive_source_coverage" / "primitive_source_coverage.md"
            ),
            "research_training_export": str(
                out_dir / "research_training_export" / "research_training_manifest.json"
            ),
            "research_training_report": str(out_dir / "research_training_export" / "research_training.md"),
            "research_training_train": str(out_dir / "research_training_export" / "research_sft_train.jsonl"),
            "research_training_validation": str(
                out_dir / "research_training_export" / "research_sft_validation.jsonl"
            ),
            "research_training_grpo": str(out_dir / "research_training_export" / "research_grpo_tasks.jsonl"),
            "research_training_legacy_manifest": str(
                out_dir / "research_training_export" / "legacy_training_manifest.json"
            ),
            "research_policy_baseline": str(
                out_dir / "research_policy_baseline" / "research_policy_baseline_manifest.json"
            ),
            "research_policy_baseline_predictions": str(
                out_dir / "research_policy_baseline" / "research_policy_baseline_predictions.jsonl"
            ),
            "next_iteration_queue": str(
                out_dir / "next_iteration_queue" / "next_iteration_queue_manifest.json"
            ),
            "next_iteration_queue_report": str(out_dir / "next_iteration_queue" / "next_iteration_queue.md"),
            "research_report": str(out_dir / "research_report" / "research_report.md"),
            "research_report_manifest": str(out_dir / "research_report" / "research_report_manifest.json"),
            "research_loop": str(out_dir / "research_loop" / "research_loop_manifest.json"),
            "research_loop_repair_tasks": str(out_dir / "research_loop" / "research_loop_repair_tasks.jsonl"),
            "research_loop_live_repair_artifacts": str(
                out_dir / "research_loop" / "research_loop_live_repair_artifacts.jsonl"
            ),
            "research_loop_repair_audit": str(
                out_dir / "research_loop_repair_audit" / "research_loop_repair_audit_manifest.json"
            ),
            "research_loop_repair_train": str(
                out_dir / "research_loop_repair_audit" / "research_loop_repair_sft_train.jsonl"
            ),
            "research_loop_repair_validation": str(
                out_dir / "research_loop_repair_audit" / "research_loop_repair_sft_validation.jsonl"
            ),
            "research_loop_live_repair_audit": str(
                out_dir
                / "research_loop_live_repair_audit"
                / "research_loop_live_repair_audit_manifest.json"
            ),
            "research_loop_live_repair_train": str(
                out_dir
                / "research_loop_live_repair_audit"
                / "research_loop_live_repair_sft_train.jsonl"
            ),
            "research_loop_live_repair_validation": str(
                out_dir
                / "research_loop_live_repair_audit"
                / "research_loop_live_repair_sft_validation.jsonl"
            ),
            "algorithm_repair_promotion": str(
                out_dir / "algorithm_repair_promotion" / "algorithm_repair_promotion_manifest.json"
            ),
            "algorithm_repair_promotion_queue": str(
                out_dir / "algorithm_repair_promotion" / "algorithm_repair_promotion_queue.jsonl"
            ),
            "algorithm_repair_sandbox": str(
                out_dir / "algorithm_repair_sandbox" / "algorithm_repair_sandbox_manifest.json"
            ),
            "algorithm_repair_sandbox_results": str(
                out_dir / "algorithm_repair_sandbox" / "algorithm_repair_sandbox_results.jsonl"
            ),
            "algorithm_repair_sandbox_apply": str(
                out_dir / "algorithm_repair_sandbox_apply" / "algorithm_repair_sandbox_apply_manifest.json"
            ),
            "algorithm_repair_sandbox_apply_results": str(
                out_dir / "algorithm_repair_sandbox_apply" / "algorithm_repair_sandbox_apply_results.jsonl"
            ),
            "algorithm_repair_sandbox_rerun": str(
                out_dir / "algorithm_repair_sandbox_rerun" / "algorithm_repair_sandbox_rerun_manifest.json"
            ),
            "algorithm_repair_sandbox_rerun_results": str(
                out_dir / "algorithm_repair_sandbox_rerun" / "algorithm_repair_sandbox_rerun_results.jsonl"
            ),
            "algorithm_repair_sandbox_patch_eval": str(
                out_dir
                / "algorithm_repair_sandbox_patch_eval"
                / "algorithm_repair_sandbox_patch_eval_manifest.json"
            ),
            "algorithm_repair_sandbox_patch_eval_results": str(
                out_dir
                / "algorithm_repair_sandbox_patch_eval"
                / "algorithm_repair_sandbox_patch_eval_results.jsonl"
            ),
            "algorithm_repair_patch_training_export": str(
                out_dir
                / "algorithm_repair_patch_training_export"
                / "algorithm_repair_patch_training_manifest.json"
            ),
            "algorithm_repair_patch_training_train": str(
                out_dir / "algorithm_repair_patch_training_export" / "algorithm_repair_patch_train.jsonl"
            ),
            "algorithm_repair_patch_training_validation": str(
                out_dir
                / "algorithm_repair_patch_training_export"
                / "algorithm_repair_patch_validation.jsonl"
            ),
            "algorithm_repair_patch_policy_model": str(
                out_dir
                / "algorithm_repair_patch_policy_model"
                / "algorithm_repair_patch_policy_model_manifest.json"
            ),
            "algorithm_repair_patch_policy_model_json": str(
                out_dir
                / "algorithm_repair_patch_policy_model"
                / "algorithm_repair_patch_policy_model.json"
            ),
            "algorithm_repair_patch_policy_validation_predictions": str(
                out_dir
                / "algorithm_repair_patch_policy_model"
                / "algorithm_repair_patch_policy_validation_predictions.jsonl"
            ),
            "algorithm_repair_production_patch_plan": str(
                out_dir
                / "algorithm_repair_production_patch_plan"
                / "algorithm_repair_production_patch_plan_manifest.json"
            ),
            "algorithm_repair_production_patch_plans": str(
                out_dir
                / "algorithm_repair_production_patch_plan"
                / "algorithm_repair_production_patch_plans.jsonl"
            ),
            "algorithm_repair_reviewed_patch_apply": str(
                out_dir
                / "algorithm_repair_reviewed_patch_apply"
                / "algorithm_repair_reviewed_patch_apply_manifest.json"
            ),
            "algorithm_repair_reviewed_patch_apply_results": str(
                out_dir
                / "algorithm_repair_reviewed_patch_apply"
                / "algorithm_repair_reviewed_patch_apply_results.jsonl"
            ),
            "algorithm_repair_reviewed_patch_validate": str(
                out_dir
                / "algorithm_repair_reviewed_patch_validate"
                / "algorithm_repair_reviewed_patch_validate_manifest.json"
            ),
            "algorithm_repair_reviewed_patch_validate_results": str(
                out_dir
                / "algorithm_repair_reviewed_patch_validate"
                / "algorithm_repair_reviewed_patch_validate_results.jsonl"
            ),
            "formal_gaps": str(out_dir / "research_benchmark" / "formal_gaps"),
        },
    }
    evaluation_benchmark_guidance_manifest = build_evaluation_benchmark_guidance(
        out_dir / "evaluation_benchmark_guidance",
        system_audit_payload=payload,
    )
    payload["gates"]["evaluation_benchmark_guidance"] = bool(
        evaluation_benchmark_guidance_manifest["all_ok"]
    )
    payload["counts"].update(
        {
            "evaluation_benchmark_guidance_suites": evaluation_benchmark_guidance_manifest[
                "n_suites"
            ],
            "evaluation_benchmark_guidance_exercised": evaluation_benchmark_guidance_manifest[
                "n_exercised"
            ],
            "evaluation_benchmark_guidance_stale_or_missing": evaluation_benchmark_guidance_manifest[
                "n_stale_or_missing"
            ],
            "evaluation_benchmark_guidance_capacity_gaps": evaluation_benchmark_guidance_manifest[
                "n_saturated_or_capacity_gap"
            ],
            "evaluation_benchmark_guidance_actions": len(
                evaluation_benchmark_guidance_manifest["top_actions"]
            ),
        }
    )
    payload["artifacts"]["evaluation_benchmark_guidance"] = str(
        out_dir / "evaluation_benchmark_guidance" / "evaluation_benchmark_guidance_manifest.json"
    )
    payload["artifacts"]["evaluation_benchmark_guidance_report"] = str(
        out_dir / "evaluation_benchmark_guidance" / "evaluation_benchmark_guidance.md"
    )
    payload["all_gates_passed"] = all(bool(value) for value in payload["gates"].values())
    (out_dir / "research_system_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
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


def _research_benchmark_cache_info(
    *,
    questions: list[OpenResearchQuestion],
    question_file: Path,
    config: ResearchSystemAuditConfig,
    verifier: ProofVerifier,
    formal_source_search: dict[str, str],
) -> dict[str, Any]:
    root = Path(config.research_benchmark_cache) if config.research_benchmark_cache else None
    key = _research_benchmark_cache_key(
        questions=questions,
        question_file=question_file,
        config=config,
        verifier=verifier,
        formal_source_search=formal_source_search,
    )
    return {
        "enabled": root is not None,
        "root": root or Path(),
        "key": key,
        "entry": (root / key) if root is not None else Path(),
        "refresh": config.refresh_research_benchmark_cache,
    }


def _research_benchmark_cache_key(
    *,
    questions: list[OpenResearchQuestion],
    question_file: Path,
    config: ResearchSystemAuditConfig,
    verifier: ProofVerifier,
    formal_source_search: dict[str, str],
) -> str:
    question_file_text = question_file.read_text(encoding="utf-8") if question_file.exists() else ""
    payload = {
        "cache_schema": 1,
        "question_file": str(question_file),
        "question_file_hash": stable_hash(question_file_text),
        "questions": [asdict(question) for question in questions],
        "config": {
            "n_runs": config.n_runs,
            "seed": config.seed,
            "use_axle": config.use_axle,
            "use_local_lean": config.use_local_lean,
            "local_lean_timeout": config.local_lean_timeout,
        },
        "verifier": verifier.name,
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "research_provenance": _stable_research_provenance_for_cache(),
        "formal_source_search": _normalized_formal_source_search(formal_source_search),
        "engine_fingerprints": {
            "research_system_audit": _source_file_hash(Path(__file__)),
            "research_lab": _source_file_hash(Path(__file__).with_name("research_lab.py")),
            "research_schema": _source_file_hash(Path(__file__).with_name("research_schema.py")),
        },
    }
    return stable_hash(payload)[:24]


def _stable_research_provenance_for_cache() -> dict[str, str]:
    provenance = dict(build_research_provenance())
    # The source inventory includes generated local run artifacts. Those do not
    # change the deterministic research traces, so excluding this field prevents
    # routine audit output from invalidating a valid benchmark cache entry.
    provenance.pop("research_source_inventory_fingerprint", None)
    return provenance


def _normalized_formal_source_search(formal_source_search: dict[str, str]) -> dict[str, str]:
    stable_keys = ("backend", "graph_backend", "dependency_graph_backend")
    return {
        key: str(formal_source_search[key])
        for key in stable_keys
        if key in formal_source_search and formal_source_search[key]
    }


def _source_file_hash(path: Path) -> str:
    return stable_hash(path.read_text(encoding="utf-8")) if path.exists() else ""


def _load_cached_research_benchmark(
    *,
    cache_info: dict[str, Any],
    target_dir: Path,
) -> dict[str, Any] | None:
    if not cache_info["enabled"] or cache_info["refresh"]:
        return None
    entry = Path(str(cache_info["entry"]))
    cached_dir = entry / "research_benchmark"
    manifest_path = cached_dir / "research_benchmark_manifest.json"
    cache_manifest_path = entry / "research_benchmark_cache_manifest.json"
    if not manifest_path.exists() or not cache_manifest_path.exists():
        return None
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(cached_dir, target_dir)
    return json.loads((target_dir / "research_benchmark_manifest.json").read_text(encoding="utf-8"))


def _store_cached_research_benchmark(
    *,
    cache_info: dict[str, Any],
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
    (entry / "research_benchmark_cache_manifest.json").write_text(
        json.dumps(cache_payload, indent=2, default=str),
        encoding="utf-8",
    )

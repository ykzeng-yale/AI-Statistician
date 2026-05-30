from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .frontier_backlog_audit import audit_frontier_backlog
from .frontier_coverage_audit import audit_frontier_coverage
from .frontier_precision_audit import audit_frontier_precision
from .architecture_audit import audit_architecture
from .formal_gap_task_export import export_formal_gap_lean_tasks
from .formalization_target_audit import audit_formalization_targets
from .formal_source_graph import audit_formal_source_graph
from .formal_source_index import build_formal_source_search_backend
from .autoform_harness import audit_autoform_harness
from .autoform_target_export import export_autoform_targets
from .frontier_smoke_benchmark import FrontierSmokeConfig, run_frontier_smoke_benchmark
from .proof_audit import audit_proof_bank
from .proof_bank_expansion_export import export_proof_bank_expansion_candidates
from .proof_policy_baseline import evaluate_retrieval_proof_policy_baseline
from .proof_repair_export import export_proof_repair_dataset
from .proof_training_export import export_proof_training_dataset
from .prover_component_audit import build_prover_component_audit, write_prover_component_audit
from .research_gap_audit import audit_research_gap_backlog
from .research_intake_audit import audit_research_question_intake
from .research_knowledge_audit import audit_research_knowledge
from .research_capability_audit import build_research_capability_audit, write_research_capability_audit
from .research_lab import audit_research_algorithm_registry, load_open_research_questions, run_research_benchmark
from .research_loop import LoopConfig, run_research_loop_benchmark
from .research_loop_repair_audit import audit_research_loop_repair_tasks
from .research_next_iteration_audit import audit_next_iteration_queue
from .research_policy_baseline import evaluate_research_policy_baseline
from .research_report import build_research_markdown_report
from .research_trace_audit import audit_research_traces
from .research_training_export import export_research_training_dataset
from .retrieval import audit_proof_bank_retrieval
from .verifier import AxleProofVerifier, CachingProofVerifier, MockProofVerifier, ProofVerifier


@dataclass(frozen=True)
class ResearchSystemAuditConfig:
    n_runs: int = 100
    seed: int = 20260528
    use_axle: bool = False


async def run_research_system_audit(
    out_dir: Path,
    *,
    question_file: Path | None = None,
    config: ResearchSystemAuditConfig = ResearchSystemAuditConfig(),
) -> dict[str, object]:
    """Run release-style gates for the open-question research workflow."""

    out_dir.mkdir(parents=True, exist_ok=True)
    base_verifier: ProofVerifier = AxleProofVerifier() if config.use_axle else MockProofVerifier()
    verifier = CachingProofVerifier(base_verifier)
    actual_question_file = question_file or Path("examples/research_questions.json")
    questions = load_open_research_questions(actual_question_file)
    formal_source_index_path = out_dir / "formal_source_index.sqlite"
    formal_source_retriever = build_formal_source_search_backend(db_path=formal_source_index_path)
    formal_source_declarations = (
        formal_source_retriever.load_declarations()
        if hasattr(formal_source_retriever, "load_declarations")
        else []
    )
    formal_source_graph_manifest = audit_formal_source_graph(
        out_dir / "formal_source_graph",
        declarations=formal_source_declarations or None,
    )
    formal_source_search = {
        "backend": "sqlite_fts_shape_graph_hybrid",
        "sqlite_index_path": str(formal_source_index_path),
        "graph_backend": "declaration_symbol_graph",
        "graph_manifest": str(out_dir / "formal_source_graph" / "formal_source_graph_manifest.json"),
    }

    frontier_manifest = audit_frontier_coverage(out_dir / "frontier_coverage_audit")
    frontier_precision_manifest = audit_frontier_precision(out_dir / "frontier_precision_audit")
    frontier_backlog_manifest = audit_frontier_backlog(out_dir / "frontier_backlog_audit")
    architecture_manifest = audit_architecture(out_dir / "architecture_audit")
    capability_report = build_research_capability_audit(
        root=Path.cwd(),
        question_file=actual_question_file,
        max_manifests=12,
    )
    write_research_capability_audit(capability_report, out_dir / "research_capability_audit")
    frontier_smoke_manifest = await run_frontier_smoke_benchmark(
        out_dir / "frontier_smoke_benchmark",
        config=FrontierSmokeConfig(n_runs=config.n_runs, seed=config.seed, max_per_class=1, use_axle=config.use_axle),
        proof_verifier=verifier,
        formal_source_retriever=formal_source_retriever,
        formal_source_search=formal_source_search,
    )
    intake_manifest = audit_research_question_intake(out_dir / "research_intake_audit")
    knowledge_manifest = audit_research_knowledge(out_dir / "research_knowledge_audit")
    autoform_harness_manifest = audit_autoform_harness(out_dir / "autoform_harness")
    retrieval_manifest = audit_proof_bank_retrieval(out_dir / "retrieval_audit", k=5)
    algorithm_manifest = audit_research_algorithm_registry(out_dir / "research_algorithm_audit")
    proof_manifest = await audit_proof_bank(
        verifier,
        out_dir / "proof_audit",
        export_lean=True,
        include_negative_controls=not config.use_axle,
    )
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
    prover_component_report = build_prover_component_audit(
        root=Path.cwd(),
        question_file=actual_question_file,
    )
    write_prover_component_audit(prover_component_report, out_dir / "prover_component_audit")
    benchmark_manifest = await run_research_benchmark(
        questions,
        out_dir / "research_benchmark",
        proof_verifier=verifier,
        formal_source_retriever=formal_source_retriever,
        formal_source_search=formal_source_search,
        n_runs=config.n_runs,
        seed=config.seed,
    )
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
    research_loop_manifest = await run_research_loop_benchmark(
        questions[:1],
        out_dir / "research_loop",
        proof_verifier=verifier,
        formal_source_index_path=formal_source_index_path,
        config=LoopConfig(max_rounds=2, n_runs=config.n_runs, seed=config.seed),
    )
    research_loop_repair_manifest = audit_research_loop_repair_tasks(
        out_dir / "research_loop",
        out_dir / "research_loop_repair_audit",
    )

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
        "research_knowledge_audit": bool(knowledge_manifest["all_ok"]),
        "autoform_harness": bool(autoform_harness_manifest["ready_for_integration"]),
        "retrieval_audit": bool(retrieval_manifest["all_top_k"]),
        "formal_source_graph": bool(formal_source_graph_manifest["all_queries_ok"]),
        "research_algorithm_audit": bool(algorithm_manifest["all_ok"]),
        "proof_audit": bool(proof_manifest["all_verified"])
        and bool(proof_manifest["dependency_graph"]["all_ok"]),
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
        "research_training_export": bool(research_training_manifest["all_ok"]),
        "research_policy_baseline": bool(research_policy_manifest["all_ok"]),
        "next_iteration_queue": bool(next_iteration_manifest["all_ok"]),
        "research_report": bool(research_report_manifest["all_ok"]),
        "research_loop": bool(research_loop_manifest["all_loop_traces_written"])
        and bool(research_loop_manifest["all_repair_tasks_exported"])
        and int(research_loop_manifest["n_questions"]) == 1,
        "research_loop_repair_audit": bool(research_loop_repair_manifest["all_ok"]),
    }
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "n_runs": config.n_runs,
            "seed": config.seed,
            "use_axle": config.use_axle,
            "question_file": str(question_file or Path("examples/research_questions.json")),
        },
        "all_gates_passed": all(gates.values()),
        "gates": gates,
        "counts": {
            "questions": len(questions),
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
            "research_intake_supported": intake_manifest["n_supported"],
            "research_intake_supported_accepted": intake_manifest["n_supported_accepted"],
            "research_intake_unsupported": intake_manifest["n_unsupported"],
            "research_intake_unsupported_rejected": intake_manifest["n_unsupported_rejected"],
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
            "research_ready_with_gaps": benchmark_manifest["n_ready_with_gaps"],
            "research_simulation_flagged": benchmark_manifest["n_simulation_flagged"],
            "research_formal_blocked": benchmark_manifest["n_formal_blocked"],
            "retrieval_top_k": retrieval_manifest["top_k"],
            "retrieval_total": retrieval_manifest["n_obligations"],
            "research_algorithms_ok": algorithm_manifest["n_ok"],
            "research_algorithms_total": algorithm_manifest["n_algorithms"],
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
            "prover_components_total": prover_component_report["summary"]["components"],
            "prover_components_ready": prover_component_report["summary"]["ready"],
            "prover_components_partial": prover_component_report["summary"]["partial"],
            "prover_components_missing_or_not_trained": prover_component_report["summary"]["missing_or_not_trained"],
            "prover_component_goal_complete": prover_component_report["summary"]["honest_goal_complete"],
            "research_traces_ok": trace_manifest["n_ok"],
            "research_traces_total": trace_manifest["n_traces"],
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
            "research_loop_status_kinds": len(research_loop_manifest["status_counts"]),
            "research_loop_repair_tasks_ok": research_loop_repair_manifest["n_ok"],
            "research_loop_repair_sft_examples": research_loop_repair_manifest["n_sft_examples"],
            "research_loop_repair_sft_train": research_loop_repair_manifest["n_train"],
            "research_loop_repair_sft_validation": research_loop_repair_manifest["n_validation"],
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
            "research_algorithm_audit": str(
                out_dir / "research_algorithm_audit" / "research_algorithm_audit_manifest.json"
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
            "research_loop_repair_audit": str(
                out_dir / "research_loop_repair_audit" / "research_loop_repair_audit_manifest.json"
            ),
            "research_loop_repair_train": str(
                out_dir / "research_loop_repair_audit" / "research_loop_repair_sft_train.jsonl"
            ),
            "research_loop_repair_validation": str(
                out_dir / "research_loop_repair_audit" / "research_loop_repair_sft_validation.jsonl"
            ),
            "formal_gaps": str(out_dir / "research_benchmark" / "formal_gaps"),
        },
    }
    (out_dir / "research_system_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    return payload

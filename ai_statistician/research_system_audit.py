from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .model_backend import (
    is_live_generator_backend,
    normalize_generator_provider_name,
)
from .frontier_backlog_audit import audit_frontier_backlog
from .frontier_coverage_audit import audit_frontier_coverage
from .frontier_discover_and_prove_prompt_packets import (
    export_frontier_discover_and_prove_prompt_packets,
)
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
from .assumption_interface_export import export_assumption_interfaces
from .claim_ledger_action_export import export_claim_ledger_actions
from .claim_ledger import build_claim_ledger
from .stat_claim_certificate_checker_audit import audit_stat_claim_certificate_checkers
from .stat_claim_certificate_plan import export_stat_claim_certificate_plan
from .stat_claim_certificate_readiness_overlay import (
    export_stat_claim_certificate_readiness_overlay,
)
from .stat_claim_certificate_witness_materializer import (
    materialize_stat_claim_certificate_witness_drafts,
)
from .stat_claim_certificate_witness_context_packets import (
    export_stat_claim_certificate_witness_context_packets,
)
from .stat_claim_certificate_witness_context_triage import (
    export_stat_claim_certificate_witness_context_triage,
)
from .stat_claim_certificate_witness_queue import export_stat_claim_certificate_witness_queue
from .stat_claim_certificate_witness_prompt_packets import (
    export_stat_claim_certificate_witness_prompt_packets,
)
from .stat_claim_certificate_witness_response_apply import (
    apply_stat_claim_certificate_witness_responses,
)
from .stat_claim_certificate_witness_response_validation import (
    validate_stat_claim_certificate_witness_worker_outputs,
)
from .stat_claim_certificate_witness_validator import (
    validate_stat_claim_certificate_witness_drafts,
)
from .evaluation_benchmark_guidance import build_evaluation_benchmark_guidance
from .formal_gap_task_export import export_formal_gap_lean_tasks
from .formalization_delta_plan import build_formalization_delta_plan
from .formalization_gap_planner_refinement_queue import (
    export_formalization_gap_planner_refinement_queue,
)
from .formalization_gap_planner_adapter_registry import (
    export_formalization_gap_planner_adapter_registry,
)
from .formalization_gap_planner_adapter_registry_audit import (
    audit_formalization_gap_planner_adapter_registry,
)
from .formalization_gap_planner_component_resource_registry import (
    export_formalization_gap_planner_component_resource_registry,
)
from .formalization_gap_planner_component_resource_registry_audit import (
    audit_formalization_gap_planner_component_resource_registry,
)
from .formalization_gap_planner_benchmark import (
    default_formalization_gap_planner_ground_truth_path,
    export_formalization_gap_planner_benchmark,
)
from .formalization_gap_planner_benchmark_audit import (
    audit_formalization_gap_planner_benchmark,
)
from .formalization_gap_planner_ablation_study import (
    export_formalization_gap_planner_ablation_study,
)
from .formalization_gap_planner_evaluation import evaluate_formalization_gap_planner
from .formalization_gap_planner_cross_prover_matrix_audit import (
    audit_formalization_gap_planner_cross_prover_matrix,
)
from .formalization_gap_planner_refinement_adapters import (
    export_formalization_gap_planner_refinement_adapter_responses,
)
from .formalization_gap_planner_local_formal_source_adapter import (
    export_formalization_gap_planner_local_formal_source_adapter_responses,
)
from .formalization_gap_planner_local_literature_adapter import (
    export_formalization_gap_planner_local_literature_adapter_responses,
)
from .formalization_gap_planner_local_proof_state_adapter import (
    export_formalization_gap_planner_local_proof_state_adapter_responses,
)
from .formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)
from .formalization_gap_planner_route_revision_overlay import (
    export_formalization_gap_planner_route_revision_overlay,
)
from .formalization_gap_planner_route_stability_audit import (
    audit_formalization_gap_planner_route_stability,
)
from .formalization_gap_planner_route_replan_handoff import (
    export_formalization_gap_planner_route_replan_handoff,
)
from .formalization_gap_planner_route_replan_handoff_audit import (
    audit_formalization_gap_planner_route_replan_handoff,
)
from .formalization_gap_planner_source_grounding_audit import (
    audit_formalization_gap_planner_source_grounding,
)
from .formalization_gap_planner_target_intake import (
    normalize_formalization_gap_planner_target_intake,
)
from .formalization_gap_planner_prover_adapter_contract import (
    export_formalization_gap_planner_prover_adapter_contract,
)
from .formalization_gap_planner_portable_plan_audit import (
    audit_formalization_gap_planner_portable_plan,
)
from .formalization_gap_planner_library_coverage_map import (
    export_formalization_gap_planner_library_coverage_map,
)
from .formalization_gap_planner_primitive_action_queue import (
    export_formalization_gap_planner_primitive_action_queue,
)
from .formalization_gap_planner_action_resource_plan import (
    export_formalization_gap_planner_action_resource_plan,
)
from .formalization_gap_planner_resource_request_queue import (
    export_formalization_gap_planner_resource_request_queue,
)
from .formalization_gap_planner_resource_response_ledger import (
    export_formalization_gap_planner_resource_response_ledger,
)
from .formalization_gap_planner_minimal_delta_audit import (
    audit_formalization_gap_planner_minimal_delta,
)
from .formalization_gap_planner_publication_bundle import (
    export_formalization_gap_planner_publication_bundle,
)
from .formalization_gap_planner_publication_bundle_audit import (
    audit_formalization_gap_planner_publication_bundle,
)
from .formalization_gap_planner_proof_state_triage import (
    export_formalization_gap_planner_proof_state_triage,
)
from .formalization_gap_planner_interactive_session import (
    export_formalization_gap_planner_interactive_session,
)
from .formalization_target_audit import audit_formalization_targets
from .formal_verifier_queue import export_formal_verifier_queue
from .goal_conditioned_minimal_formalization_plan import (
    export_goal_conditioned_minimal_formalization_plan,
)
from .formal_verifier_replay_attempt import export_formal_verifier_replay_attempts
from .formal_verifier_replay_calibration import export_formal_verifier_replay_calibration
from .formal_verifier_replay_export import export_formal_verifier_replay
from .formal_verifier_replay_repair_application import (
    export_formal_verifier_replay_repair_application_tasks,
)
from .formal_verifier_replay_repair_application_validation import (
    export_formal_verifier_replay_repair_application_validation,
)
from .formal_verifier_replay_repair_execution_queue import (
    export_formal_verifier_replay_repair_execution_queue,
)
from .formal_verifier_replay_repair_prompt_packets import (
    export_formal_verifier_replay_repair_prompt_packets,
)
from .formal_verifier_replay_repair_patch_autoworker import (
    export_formal_verifier_replay_repair_patch_autoworker,
)
from .formal_verifier_replay_repair_patch_response_validation import (
    export_formal_verifier_replay_repair_patch_response_validation,
)
from .formal_verifier_replay_repair_patch_response_promotion import (
    export_formal_verifier_replay_repair_patch_response_promotion,
)
from .formal_verifier_replay_repair_patch_rerun_queue import (
    export_formal_verifier_replay_repair_patch_rerun_queue,
)
from .formal_verifier_replay_repair_patch_rerun_attempt import (
    export_formal_verifier_replay_repair_patch_rerun_attempts,
)
from .formal_verifier_replay_repair_patch_rerun_calibration import (
    export_formal_verifier_replay_repair_patch_rerun_calibration,
)
from .formal_verifier_replay_repair_patch_rerun_residual_obligations import (
    export_formal_verifier_replay_repair_patch_rerun_residual_obligations,
)
from .formal_verifier_replay_repair_patch_rerun_residual_prompt_packets import (
    export_formal_verifier_replay_repair_patch_rerun_residual_prompt_packets,
)
from .formal_verifier_replay_repair_patch_rerun_residual_autoworker import (
    export_formal_verifier_replay_repair_patch_rerun_residual_autoworker,
)
from .formal_verifier_replay_repair_patch_rerun_residual_response_validation import (
    export_formal_verifier_replay_repair_patch_rerun_residual_response_validation,
)
from .formal_verifier_replay_repair_patch_rerun_residual_followup_queue import (
    export_formal_verifier_replay_repair_patch_rerun_residual_followup_queue,
)
from .formal_verifier_agentic_proof_strategy_plan import (
    export_formal_verifier_agentic_proof_strategy_plan,
)
from .formal_verifier_agentic_proof_candidate_evaluation_queue import (
    export_formal_verifier_agentic_proof_candidate_evaluation_queue,
)
from .formal_verifier_agentic_proof_safety_policy import (
    export_formal_verifier_agentic_proof_safety_policy,
)
from .formal_verifier_agentic_proof_attempt_population import (
    export_formal_verifier_agentic_proof_attempt_population,
)
from .formal_verifier_agentic_proof_execution_queue import (
    export_formal_verifier_agentic_proof_execution_queue,
)
from .formal_verifier_agentic_proof_execution_materializer import (
    export_formal_verifier_agentic_proof_execution_materializer,
)
from .formal_verifier_agentic_proof_execution_artifact_verifier import (
    export_formal_verifier_agentic_proof_execution_artifact_verifier,
)
from .formal_verifier_agentic_proof_source_theorem_promotion_queue import (
    export_formal_verifier_agentic_proof_source_theorem_promotion_queue,
)
from .formal_verifier_agentic_proof_source_theorem_target_resolution import (
    export_formal_verifier_agentic_proof_source_theorem_target_resolution,
)
from .formal_verifier_replay_repair import export_formal_verifier_replay_repair_packets
from .formal_source_graph import audit_formal_source_graph
from .formal_source_hybrid import FormalSourceHybridRetriever
from .formal_source_index import FormalSourceSqliteIndex, build_formal_source_search_backend
from .formal_source_retrieval_ablation import run_formal_source_retrieval_ablation_benchmark
from .formal_source_retrieval_benchmark import (
    ALL_FORMAL_SOURCE_RETRIEVAL_BENCHMARKS,
    EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
    run_formal_source_retrieval_benchmark,
)
from .huggingface_lean_source_audit import audit_huggingface_lean_sources
from .hf_lean_source_revalidation_tasks import (
    export_huggingface_lean_source_revalidation_tasks,
)
from .hf_lean_source_revalidation_prompt_packets import (
    export_huggingface_lean_source_revalidation_prompt_packets,
)
from .hf_lean_source_revalidation_artifact_validation import (
    export_huggingface_lean_source_revalidation_artifact_validation,
)
from .hf_lean_source_revalidation_promotion_queue import (
    export_huggingface_lean_source_revalidation_promotion_queue,
)
from .lean_rag_package_audit import (
    apply_lean_rag_source_registry_expansion,
    audit_lean_rag_package,
    preflight_lean_rag_source_registry_expansion,
    stage_lean_rag_source_registry_expansion,
)
from .lean_rag_dependency_health import audit_lean_rag_dependency_health
from .autoform_harness import audit_autoform_harness
from .autoform_target_export import export_autoform_targets
from .frontier_smoke_benchmark import FrontierSmokeConfig, run_frontier_smoke_benchmark
from .paper_theory_roundtrip import export_paper_theory_roundtrip
from .proof_audit import audit_proof_bank
from .proof_bank_action_export import export_proof_bank_actions
from .proof_bank import all_obligations, proof_bank_fingerprint
from .proof_bank_expansion_export import export_proof_bank_expansion_candidates
from .primitive_source_coverage_audit import audit_primitive_source_coverage
from .proof_policy_baseline import evaluate_retrieval_proof_policy_baseline
from .proof_policy_model import train_proof_policy_model
from .proof_repair_export import export_proof_repair_dataset
from .proof_search_audit import audit_proof_search_controller
from .proof_search_kernel_rerun_queue import export_proof_search_kernel_rerun_queue
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
from .research_agent_runtime_offline_smoke import (
    OFFLINE_RUNTIME_SMOKE_BOUNDARY,
    OFFLINE_RUNTIME_SMOKE_SOURCE,
    run_research_agent_runtime_offline_smoke,
)
from .research_agent_runtime_audit import audit_research_agent_runtime
from .retrieval import audit_proof_bank_retrieval
from .theorem_composition_export import export_theorem_composition_packets
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
    kernel_smoke_ids: tuple[str, ...] = ()
    kernel_smoke_from_actions: int = 0
    formal_source_index_cache: str | None = "runs/formal_source_index_cache/formal_source_index.sqlite"
    refresh_formal_source_index_cache: bool = False
    lean_rag_db: str | None = None
    lean_rag_package_root: str | None = None
    frontier_smoke_cache: str | None = "runs/frontier_smoke_cache"
    refresh_frontier_smoke_cache: bool = False
    formal_source_graph_cache: str | None = "runs/formal_source_graph_cache"
    refresh_formal_source_graph_cache: bool = False
    research_benchmark_cache: str | None = "runs/research_benchmark_cache"
    refresh_research_benchmark_cache: bool = False
    formal_verifier_replay_attempts: int = 0
    formal_verifier_replay_attempt_log: str | None = None
    verify_agentic_artifacts: bool = False
    adaptive_mc_rerun: bool = True
    adaptive_mc_multiplier: int = 5
    research_agent_runtime_dir: str | None = None
    research_agent_runtime_offline_smoke: bool = True
    research_agent_runtime_contract_smoke: bool = True


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

    lean_rag_dependency_health_manifest = audit_lean_rag_dependency_health(
        out_dir / "lean_rag_dependency_health",
        requested_db_path=Path(config.lean_rag_db) if config.lean_rag_db else None,
        active_db_path=(
            Path(str(getattr(formal_source_retriever, "lean_rag_dependency_graph_path", "")))
            if getattr(formal_source_retriever, "lean_rag_dependency_graph_path", "")
            else None
        ),
        auto_discovered=bool(
            getattr(formal_source_retriever, "lean_rag_dependency_graph_auto_discovered", False)
        ),
    )
    stage_start = _record_stage(stage_timings, "lean_rag_dependency_health", stage_start)

    lean_rag_package_manifest = audit_lean_rag_package(
        out_dir / "lean_rag_package_audit",
        package_root=Path(config.lean_rag_package_root) if config.lean_rag_package_root else None,
    )
    stage_start = _record_stage(stage_timings, "lean_rag_package_audit", stage_start)
    lean_rag_source_registry_expansion_manifest = (
        stage_lean_rag_source_registry_expansion(
            out_dir / "lean_rag_source_registry_expansion",
            package_root=Path(config.lean_rag_package_root)
            if config.lean_rag_package_root
            else None,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "lean_rag_source_registry_expansion",
        stage_start,
    )
    lean_rag_source_registry_expansion_preflight_manifest = (
        preflight_lean_rag_source_registry_expansion(
            out_dir / "lean_rag_source_registry_expansion_preflight",
            expansion_manifest=(
                out_dir
                / "lean_rag_source_registry_expansion"
                / "source_registry_expansion_manifest.json"
            ),
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "lean_rag_source_registry_expansion_preflight",
        stage_start,
    )
    lean_rag_source_registry_expansion_apply_manifest = (
        apply_lean_rag_source_registry_expansion(
            out_dir / "lean_rag_source_registry_expansion_apply",
            expansion_manifest=(
                out_dir
                / "lean_rag_source_registry_expansion"
                / "source_registry_expansion_manifest.json"
            ),
            preflight_manifest=(
                out_dir
                / "lean_rag_source_registry_expansion_preflight"
                / "source_registry_expansion_preflight_manifest.json"
            ),
            dry_run=True,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "lean_rag_source_registry_expansion_apply",
        stage_start,
    )
    huggingface_lean_source_manifest = audit_huggingface_lean_sources(
        out_dir / "huggingface_lean_source_audit",
        use_network=False,
    )
    stage_start = _record_stage(stage_timings, "huggingface_lean_source_audit", stage_start)
    huggingface_lean_source_revalidation_tasks_manifest = (
        export_huggingface_lean_source_revalidation_tasks(
            out_dir
            / "huggingface_lean_source_audit"
            / "huggingface_lean_source_revalidation_queue.jsonl",
            out_dir / "huggingface_lean_source_revalidation_tasks",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "huggingface_lean_source_revalidation_tasks",
        stage_start,
    )
    huggingface_lean_source_revalidation_prompt_packets_manifest = (
        export_huggingface_lean_source_revalidation_prompt_packets(
            out_dir / "huggingface_lean_source_revalidation_tasks",
            out_dir / "huggingface_lean_source_revalidation_prompt_packets",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "huggingface_lean_source_revalidation_prompt_packets",
        stage_start,
    )
    huggingface_lean_source_revalidation_artifact_validation_manifest = (
        export_huggingface_lean_source_revalidation_artifact_validation(
            out_dir / "huggingface_lean_source_revalidation_tasks",
            out_dir / "huggingface_lean_source_revalidation_artifact_validation",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "huggingface_lean_source_revalidation_artifact_validation",
        stage_start,
    )
    huggingface_lean_source_revalidation_promotion_queue_manifest = (
        export_huggingface_lean_source_revalidation_promotion_queue(
            out_dir / "huggingface_lean_source_revalidation_artifact_validation",
            out_dir / "huggingface_lean_source_revalidation_promotion_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "huggingface_lean_source_revalidation_promotion_queue",
        stage_start,
    )

    formal_source_retrieval_benchmark_manifest = run_formal_source_retrieval_benchmark(
        out_dir / "formal_source_retrieval_benchmark",
        retriever=formal_source_retriever,
    )
    formal_source_retrieval_external_manifest = run_formal_source_retrieval_benchmark(
        out_dir / "formal_source_retrieval_external_benchmark",
        retriever=formal_source_retriever,
        cases=EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
    )
    formal_source_retrieval_all_manifest = run_formal_source_retrieval_benchmark(
        out_dir / "formal_source_retrieval_all_benchmark",
        retriever=formal_source_retriever,
        cases=ALL_FORMAL_SOURCE_RETRIEVAL_BENCHMARKS,
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
    frontier_dap_prompt_packets_manifest = export_frontier_discover_and_prove_prompt_packets(
        out_dir / "frontier_discover_and_prove_prompt_packets",
        max_packets=int(frontier_manifest.get("n_questions", 60) or 60),
    )
    stage_start = _record_stage(
        stage_timings,
        "frontier_discover_and_prove_prompt_packets",
        stage_start,
    )
    paper_theory_roundtrip_manifest = export_paper_theory_roundtrip(
        Path("examples/paper_theory_roundtrip_sample.tex"),
        out_dir / "paper_theory_roundtrip",
        paper_id="paper_theory_roundtrip_sample",
    )
    stage_start = _record_stage(
        stage_timings,
        "paper_theory_roundtrip",
        stage_start,
    )

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
    kernel_smoke_manifest: dict[str, object] | None = None
    kernel_smoke_auto_ids: list[str] = []
    kernel_smoke_selected_ids = list(dict.fromkeys(config.kernel_smoke_ids))
    claim_ledger_proof_manifest_path = out_dir / "proof_audit" / "proof_audit_manifest.json"

    frontier_smoke_manifest = await run_frontier_smoke_benchmark(
        out_dir / "frontier_smoke_benchmark",
        config=FrontierSmokeConfig(
            n_runs=config.frontier_smoke_runs,
            seed=config.seed,
            max_per_class=1,
            use_axle=config.use_axle,
            cache_dir=config.frontier_smoke_cache,
            refresh_cache=config.refresh_frontier_smoke_cache,
            adaptive_mc_rerun=config.adaptive_mc_rerun,
            adaptive_mc_multiplier=config.adaptive_mc_multiplier,
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
        n_runs=max(25, min(config.n_runs, 50)),
        adaptive_mc_rerun=config.adaptive_mc_rerun,
        adaptive_mc_multiplier=config.adaptive_mc_multiplier,
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
    proof_search_retrieval_no_registered_ablation_manifest = await run_proof_search_retrieval_ablation(
        out_dir / "proof_search_retrieval_no_registered_ablation",
        baseline_retriever=baseline_formal_source_retriever,
        enhanced_retriever=formal_source_retriever,
        verifier=verifier,
        max_obligations=6,
        max_nodes=4,
        formal_source_k=4,
        include_registered_proof=False,
        baseline_name="proof_search_without_dependency_graph_no_registered_proof",
        enhanced_name="proof_search_with_dependency_graph_no_registered_proof",
    )
    proof_search_training_manifest = export_proof_search_process_dataset(
        Path(str(proof_search_manifest["results_jsonl"])),
        out_dir / "proof_search_training_export",
        validation_fraction=0.2,
    )
    proof_search_kernel_rerun_queue_manifest = export_proof_search_kernel_rerun_queue(
        out_dir / "proof_search_audit",
        out_dir / "proof_search_kernel_rerun_queue",
        local_lean_project=config.local_lean_project,
        local_lean_timeout=config.local_lean_timeout,
    )
    proof_search_kernel_rerun_local_lean_manifest = (
        _proof_search_kernel_rerun_local_lean_overlay(out_dir)
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
            adaptive_mc_rerun=config.adaptive_mc_rerun,
            adaptive_mc_multiplier=config.adaptive_mc_multiplier,
        )
        benchmark_cache_status = "disabled" if not benchmark_cache_info["enabled"] else "miss"
        benchmark_cache_stored = False
        stage_start = _record_stage(stage_timings, "research_benchmark", stage_start)

    trace_manifest = audit_research_traces(
        out_dir / "research_benchmark",
        out_dir / "research_trace_audit",
    )
    stage_start = _record_stage(stage_timings, "research_trace_audit", stage_start)
    gap_backlog_manifest = audit_research_gap_backlog(
        out_dir / "research_benchmark",
        out_dir / "research_gap_backlog",
    )
    stage_start = _record_stage(stage_timings, "research_gap_backlog", stage_start)
    formalization_target_manifest = audit_formalization_targets(
        out_dir / "research_benchmark",
        out_dir / "formalization_target_audit",
    )
    stage_start = _record_stage(stage_timings, "formalization_target_audit", stage_start)
    formal_gap_task_manifest = export_formal_gap_lean_tasks(
        out_dir / "research_benchmark",
        out_dir / "formal_gap_lean_tasks",
    )
    stage_start = _record_stage(stage_timings, "formal_gap_task_export", stage_start)
    autoform_target_manifest = export_autoform_targets(
        out_dir / "research_benchmark",
        out_dir / "autoform_targets",
    )
    stage_start = _record_stage(stage_timings, "autoform_target_export", stage_start)
    proof_bank_expansion_manifest = export_proof_bank_expansion_candidates(
        out_dir / "research_benchmark",
        out_dir / "proof_bank_expansion",
    )
    stage_start = _record_stage(stage_timings, "proof_bank_expansion_export", stage_start)
    proof_bank_action_manifest = export_proof_bank_actions(
        out_dir / "proof_bank_expansion",
        out_dir / "proof_bank_actions",
    )
    stage_start = _record_stage(stage_timings, "proof_bank_action_export", stage_start)
    assumption_interface_manifest = export_assumption_interfaces(
        out_dir / "proof_bank_actions",
        out_dir / "assumption_interfaces",
        lean_project=config.local_lean_project,
        lean_timeout=config.local_lean_timeout,
    )
    stage_start = _record_stage(stage_timings, "assumption_interface_export", stage_start)
    if config.kernel_smoke_from_actions > 0:
        kernel_smoke_auto_ids = _select_kernel_smoke_ids_from_actions(
            proof_bank_action_manifest,
            limit=config.kernel_smoke_from_actions,
            exclude=kernel_smoke_selected_ids,
        )
        kernel_smoke_selected_ids = list(
            dict.fromkeys([*kernel_smoke_selected_ids, *kernel_smoke_auto_ids])
        )
    if kernel_smoke_selected_ids:
        kernel_smoke_verifier = CachingProofVerifier(
            LocalLeanProofVerifier(
                project_root=config.local_lean_project,
                timeout_s=config.local_lean_timeout,
            )
        )
        kernel_smoke_manifest = await audit_proof_bank(
            kernel_smoke_verifier,
            out_dir / "kernel_smoke_proof_audit",
            ids=kernel_smoke_selected_ids,
            export_lean=True,
            export_attempt_log=True,
            include_negative_controls=False,
        )
        claim_ledger_proof_manifest_path = (
            out_dir / "kernel_smoke_proof_audit" / "proof_audit_manifest.json"
        )
        stage_start = _record_stage(stage_timings, "kernel_smoke_proof_audit", stage_start)
    primitive_source_coverage_manifest = audit_primitive_source_coverage(
        out_dir / "research_benchmark",
        out_dir / "primitive_source_coverage",
        formal_source_retriever=formal_source_retriever,
        formal_source_index_path=formal_source_index_path,
        lean_rag_db_path=Path(config.lean_rag_db) if config.lean_rag_db else None,
    )
    stage_start = _record_stage(stage_timings, "primitive_source_coverage_audit", stage_start)
    formalization_delta_manifest = build_formalization_delta_plan(
        out_dir / "proof_bank_actions",
        out_dir / "formalization_delta_plan",
        primitive_source_coverage_dir=out_dir / "primitive_source_coverage",
        formal_gap_tasks_dir=out_dir / "formal_gap_lean_tasks",
    )
    stage_start = _record_stage(stage_timings, "formalization_delta_plan", stage_start)
    formal_verifier_queue_manifest = export_formal_verifier_queue(
        out_dir / "formalization_delta_plan",
        out_dir / "formal_verifier_queue",
        proof_search_no_registered_ablation_dir=out_dir / "proof_search_retrieval_no_registered_ablation",
        kernel_smoke_proof_audit_dir=(out_dir / "kernel_smoke_proof_audit")
        if kernel_smoke_manifest is not None
        else None,
        proof_attempt_log_path=out_dir / "proof_audit" / "proof_attempts.jsonl",
        proof_search_results_path=out_dir / "proof_search_audit" / "proof_search_results.jsonl",
    )
    stage_start = _record_stage(stage_timings, "formal_verifier_queue", stage_start)
    goal_conditioned_minimal_formalization_plan_manifest = (
        export_goal_conditioned_minimal_formalization_plan(
            out_dir / "formalization_delta_plan",
            out_dir / "formal_verifier_queue",
            out_dir / "goal_conditioned_minimal_formalization_plan",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "goal_conditioned_minimal_formalization_plan",
        stage_start,
    )
    formalization_gap_planner_portable_plan_audit_manifest = (
        audit_formalization_gap_planner_portable_plan(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_portable_plan_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_portable_plan_audit",
        stage_start,
    )
    formalization_gap_planner_library_coverage_map_manifest = (
        export_formalization_gap_planner_library_coverage_map(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_library_coverage_map",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_library_coverage_map",
        stage_start,
    )
    formalization_gap_planner_primitive_action_queue_manifest = (
        export_formalization_gap_planner_primitive_action_queue(
            out_dir / "formalization_gap_planner_library_coverage_map",
            out_dir / "formalization_gap_planner_primitive_action_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_primitive_action_queue",
        stage_start,
    )
    formalization_gap_planner_adapter_registry_manifest = (
        export_formalization_gap_planner_adapter_registry(
            out_dir / "formalization_gap_planner_adapter_registry",
            lean_rag_db_path=Path(config.lean_rag_db) if config.lean_rag_db else None,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_adapter_registry",
        stage_start,
    )
    formalization_gap_planner_adapter_registry_audit_manifest = (
        audit_formalization_gap_planner_adapter_registry(
            out_dir / "formalization_gap_planner_adapter_registry",
            out_dir / "formalization_gap_planner_adapter_registry_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_adapter_registry_audit",
        stage_start,
    )
    formalization_gap_planner_component_resource_registry_manifest = (
        export_formalization_gap_planner_component_resource_registry(
            out_dir / "formalization_gap_planner_component_resource_registry",
            formalization_gap_planner_adapter_registry_dir=out_dir
            / "formalization_gap_planner_adapter_registry",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_component_resource_registry",
        stage_start,
    )
    formalization_gap_planner_component_resource_registry_audit_manifest = (
        audit_formalization_gap_planner_component_resource_registry(
            out_dir / "formalization_gap_planner_component_resource_registry",
            out_dir / "formalization_gap_planner_component_resource_registry_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_component_resource_registry_audit",
        stage_start,
    )
    formalization_gap_planner_action_resource_plan_manifest = (
        export_formalization_gap_planner_action_resource_plan(
            out_dir / "formalization_gap_planner_primitive_action_queue",
            out_dir / "formalization_gap_planner_component_resource_registry",
            out_dir / "formalization_gap_planner_action_resource_plan",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_action_resource_plan",
        stage_start,
    )
    formalization_gap_planner_resource_request_queue_manifest = (
        export_formalization_gap_planner_resource_request_queue(
            out_dir / "formalization_gap_planner_action_resource_plan",
            out_dir / "formalization_gap_planner_resource_request_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_resource_request_queue",
        stage_start,
    )
    formalization_gap_planner_resource_response_ledger_manifest = (
        export_formalization_gap_planner_resource_response_ledger(
            out_dir / "formalization_gap_planner_resource_request_queue",
            out_dir / "formalization_gap_planner_resource_response_ledger",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_resource_response_ledger",
        stage_start,
    )
    formalization_gap_planner_minimal_delta_audit_manifest = (
        audit_formalization_gap_planner_minimal_delta(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_minimal_delta_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_minimal_delta_audit",
        stage_start,
    )
    formalization_gap_planner_source_grounding_audit_manifest = (
        audit_formalization_gap_planner_source_grounding(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_source_grounding_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_source_grounding_audit",
        stage_start,
    )
    formalization_gap_planner_target_intake_manifest = (
        normalize_formalization_gap_planner_target_intake(
            Path("data/formalization_gap_planner_target_intake_example.json"),
            out_dir / "formalization_gap_planner_target_intake",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_target_intake",
        stage_start,
    )
    formalization_gap_planner_benchmark_manifest = (
        export_formalization_gap_planner_benchmark(
            out_dir / "formalization_gap_planner_benchmark",
            ground_truth_path=default_formalization_gap_planner_ground_truth_path(),
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_benchmark",
        stage_start,
    )
    formalization_gap_planner_benchmark_audit_manifest = (
        audit_formalization_gap_planner_benchmark(
            out_dir / "formalization_gap_planner_benchmark",
            out_dir / "formalization_gap_planner_benchmark_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_benchmark_audit",
        stage_start,
    )
    formalization_gap_planner_evaluation_manifest = evaluate_formalization_gap_planner(
        out_dir / "goal_conditioned_minimal_formalization_plan",
        out_dir
        / "formalization_gap_planner_benchmark"
        / "formalization_gap_planner_ground_truth.json",
        out_dir / "formalization_gap_planner_evaluation",
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_evaluation",
        stage_start,
    )
    formal_verifier_replay_manifest = export_formal_verifier_replay(
        out_dir / "formal_verifier_queue",
        out_dir / "formal_verifier_replay",
    )
    stage_start = _record_stage(stage_timings, "formal_verifier_replay", stage_start)
    replay_attempt_verifier: ProofVerifier = verifier
    if config.formal_verifier_replay_attempts > 0 and config.local_lean_project:
        replay_attempt_verifier = LocalLeanProofVerifier(
            project_root=config.local_lean_project,
            timeout_s=config.local_lean_timeout,
        )
    formal_verifier_replay_attempt_manifest = await export_formal_verifier_replay_attempts(
        out_dir / "formal_verifier_replay",
        out_dir / "formal_verifier_replay_attempts",
        verifier=replay_attempt_verifier,
        formal_gap_tasks_dir=out_dir / "formal_gap_lean_tasks",
        max_tasks=config.formal_verifier_replay_attempts,
    )
    stage_start = _record_stage(stage_timings, "formal_verifier_replay_attempts", stage_start)
    replay_attempt_log_path = (
        Path(config.formal_verifier_replay_attempt_log)
        if config.formal_verifier_replay_attempt_log
        else Path(str(formal_verifier_replay_attempt_manifest["attempt_log"]))
    )
    formal_verifier_replay_calibration_manifest = export_formal_verifier_replay_calibration(
        out_dir / "formal_verifier_replay",
        out_dir / "formal_verifier_replay_calibration",
        attempt_log_path=replay_attempt_log_path,
    )
    stage_start = _record_stage(stage_timings, "formal_verifier_replay_calibration", stage_start)
    formalization_gap_planner_refinement_queue_manifest = (
        export_formalization_gap_planner_refinement_queue(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_refinement_queue",
            formalization_gap_planner_evaluation_dir=out_dir
            / "formalization_gap_planner_evaluation",
            formal_verifier_replay_calibration_dir=out_dir
            / "formal_verifier_replay_calibration",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_refinement_queue",
        stage_start,
    )
    formalization_gap_planner_refinement_adapter_manifest = (
        export_formalization_gap_planner_refinement_adapter_responses(
            out_dir / "formalization_gap_planner_refinement_queue",
            out_dir / "formalization_gap_planner_refinement_adapter_responses",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_refinement_adapter_responses",
        stage_start,
    )
    formalization_gap_planner_local_literature_adapter_manifest = (
        export_formalization_gap_planner_local_literature_adapter_responses(
            out_dir / "formalization_gap_planner_refinement_queue",
            out_dir / "formalization_gap_planner_local_literature_adapter",
            base_response_jsonl=out_dir
            / "formalization_gap_planner_refinement_adapter_responses"
            / "formalization_gap_planner_refinement_evidence_responses.jsonl",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_local_literature_adapter",
        stage_start,
    )
    formalization_gap_planner_local_formal_source_adapter_manifest = (
        export_formalization_gap_planner_local_formal_source_adapter_responses(
            out_dir / "formalization_gap_planner_refinement_queue",
            out_dir / "formalization_gap_planner_local_formal_source_adapter",
            lean_rag_db_path=Path(config.lean_rag_db) if config.lean_rag_db else None,
            base_response_jsonl=out_dir
            / "formalization_gap_planner_local_literature_adapter"
            / "formalization_gap_planner_refinement_evidence_responses.jsonl",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_local_formal_source_adapter",
        stage_start,
    )
    formalization_gap_planner_local_proof_state_adapter_manifest = (
        export_formalization_gap_planner_local_proof_state_adapter_responses(
            out_dir / "formalization_gap_planner_refinement_queue",
            out_dir / "formalization_gap_planner_local_proof_state_adapter",
            lean_project=config.local_lean_project,
            lean_timeout=config.local_lean_timeout,
            base_response_jsonl=out_dir
            / "formalization_gap_planner_local_formal_source_adapter"
            / "formalization_gap_planner_refinement_evidence_responses.jsonl",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_local_proof_state_adapter",
        stage_start,
    )
    formalization_gap_planner_refinement_evidence_manifest = (
        export_formalization_gap_planner_refinement_evidence(
            out_dir / "formalization_gap_planner_refinement_queue",
            out_dir / "formalization_gap_planner_refinement_evidence",
            response_jsonl=out_dir
            / "formalization_gap_planner_local_proof_state_adapter"
            / "formalization_gap_planner_refinement_evidence_responses.jsonl",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_refinement_evidence",
        stage_start,
    )
    formalization_gap_planner_route_revision_overlay_manifest = (
        export_formalization_gap_planner_route_revision_overlay(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_refinement_evidence",
            out_dir / "formalization_gap_planner_route_revision_overlay",
            formalization_gap_planner_resource_response_ledger_dir=out_dir
            / "formalization_gap_planner_resource_response_ledger",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_route_revision_overlay",
        stage_start,
    )
    formalization_gap_planner_route_stability_audit_manifest = (
        audit_formalization_gap_planner_route_stability(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_refinement_evidence",
            out_dir / "formalization_gap_planner_route_revision_overlay",
            out_dir / "formalization_gap_planner_route_stability_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_route_stability_audit",
        stage_start,
    )
    formalization_gap_planner_route_replan_handoff_manifest = (
        export_formalization_gap_planner_route_replan_handoff(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_route_revision_overlay",
            out_dir / "formalization_gap_planner_route_replan_handoff",
            formalization_gap_planner_route_stability_audit_dir=out_dir
            / "formalization_gap_planner_route_stability_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_route_replan_handoff",
        stage_start,
    )
    formalization_gap_planner_route_replan_handoff_audit_manifest = (
        audit_formalization_gap_planner_route_replan_handoff(
            out_dir / "formalization_gap_planner_route_replan_handoff",
            out_dir / "formalization_gap_planner_route_replan_handoff_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_route_replan_handoff_audit",
        stage_start,
    )
    formalization_gap_planner_proof_state_triage_manifest = (
        export_formalization_gap_planner_proof_state_triage(
            out_dir / "formalization_gap_planner_route_revision_overlay",
            out_dir / "formalization_gap_planner_proof_state_triage",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_proof_state_triage",
        stage_start,
    )
    formalization_gap_planner_interactive_session_manifest = (
        export_formalization_gap_planner_interactive_session(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_interactive_session",
            formalization_gap_planner_refinement_queue_dir=out_dir
            / "formalization_gap_planner_refinement_queue",
            formalization_gap_planner_refinement_evidence_dir=out_dir
            / "formalization_gap_planner_refinement_evidence",
            formalization_gap_planner_route_stability_audit_dir=out_dir
            / "formalization_gap_planner_route_stability_audit",
            formalization_gap_planner_route_replan_handoff_dir=out_dir
            / "formalization_gap_planner_route_replan_handoff",
            formalization_gap_planner_proof_state_triage_dir=out_dir
            / "formalization_gap_planner_proof_state_triage",
            formalization_gap_planner_component_resource_registry_dir=out_dir
            / "formalization_gap_planner_component_resource_registry",
            formalization_gap_planner_resource_request_queue_dir=out_dir
            / "formalization_gap_planner_resource_request_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_interactive_session",
        stage_start,
    )
    formalization_gap_planner_ablation_study_manifest = (
        export_formalization_gap_planner_ablation_study(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_evaluation",
            out_dir / "formalization_gap_planner_ablation_study",
            formalization_gap_planner_interactive_session_dir=out_dir
            / "formalization_gap_planner_interactive_session",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_ablation_study",
        stage_start,
    )
    formalization_gap_planner_library_snapshot_ref = (
        "research_system_audit_formal_source_index:"
        + stable_hash(
            [
                str(formal_source_index_path),
                str(config.lean_rag_db or ""),
                len(formal_source_declarations),
            ]
        )[:12]
    )
    formalization_gap_planner_prover_adapter_contract_manifest = (
        export_formalization_gap_planner_prover_adapter_contract(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_prover_adapter_contract",
            target_prover_family="other",
            library_snapshot_ref=formalization_gap_planner_library_snapshot_ref,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_prover_adapter_contract",
        stage_start,
    )
    formalization_gap_planner_cross_prover_matrix_audit_manifest = (
        audit_formalization_gap_planner_cross_prover_matrix(
            out_dir / "goal_conditioned_minimal_formalization_plan",
            out_dir / "formalization_gap_planner_cross_prover_matrix_audit",
            library_snapshot_ref_prefix=formalization_gap_planner_library_snapshot_ref,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_cross_prover_matrix_audit",
        stage_start,
    )
    formalization_gap_planner_publication_bundle_manifest = (
        export_formalization_gap_planner_publication_bundle(
            out_dir / "formalization_gap_planner_publication_bundle",
            lean_rag_db_path=Path(config.lean_rag_db) if config.lean_rag_db else None,
            goal_conditioned_minimal_formalization_plan_dir=out_dir
            / "goal_conditioned_minimal_formalization_plan",
            formalization_gap_planner_evaluation_dir=out_dir
            / "formalization_gap_planner_evaluation",
            formalization_gap_planner_ablation_study_dir=out_dir
            / "formalization_gap_planner_ablation_study",
            formalization_gap_planner_portable_plan_audit_dir=out_dir
            / "formalization_gap_planner_portable_plan_audit",
            formalization_gap_planner_library_coverage_map_dir=out_dir
            / "formalization_gap_planner_library_coverage_map",
            formalization_gap_planner_primitive_action_queue_dir=out_dir
            / "formalization_gap_planner_primitive_action_queue",
            formalization_gap_planner_action_resource_plan_dir=out_dir
            / "formalization_gap_planner_action_resource_plan",
            formalization_gap_planner_resource_request_queue_dir=out_dir
            / "formalization_gap_planner_resource_request_queue",
            formalization_gap_planner_resource_response_ledger_dir=out_dir
            / "formalization_gap_planner_resource_response_ledger",
            formalization_gap_planner_minimal_delta_audit_dir=out_dir
            / "formalization_gap_planner_minimal_delta_audit",
            formalization_gap_planner_source_grounding_audit_dir=out_dir
            / "formalization_gap_planner_source_grounding_audit",
            formalization_gap_planner_target_intake_dir=out_dir
            / "formalization_gap_planner_target_intake",
            formalization_gap_planner_refinement_queue_dir=out_dir
            / "formalization_gap_planner_refinement_queue",
            formalization_gap_planner_refinement_adapter_dir=out_dir
            / "formalization_gap_planner_refinement_adapter_responses",
            formalization_gap_planner_local_literature_adapter_dir=out_dir
            / "formalization_gap_planner_local_literature_adapter",
            formalization_gap_planner_local_formal_source_adapter_dir=out_dir
            / "formalization_gap_planner_local_formal_source_adapter",
            formalization_gap_planner_local_proof_state_adapter_dir=out_dir
            / "formalization_gap_planner_local_proof_state_adapter",
            formalization_gap_planner_refinement_evidence_dir=out_dir
            / "formalization_gap_planner_refinement_evidence",
            formalization_gap_planner_route_revision_overlay_dir=out_dir
            / "formalization_gap_planner_route_revision_overlay",
            formalization_gap_planner_route_stability_audit_dir=out_dir
            / "formalization_gap_planner_route_stability_audit",
            formalization_gap_planner_route_replan_handoff_dir=out_dir
            / "formalization_gap_planner_route_replan_handoff",
            formalization_gap_planner_route_replan_handoff_audit_dir=out_dir
            / "formalization_gap_planner_route_replan_handoff_audit",
            formalization_gap_planner_proof_state_triage_dir=out_dir
            / "formalization_gap_planner_proof_state_triage",
            formalization_gap_planner_interactive_session_dir=out_dir
            / "formalization_gap_planner_interactive_session",
            formalization_gap_planner_prover_adapter_contract_dir=out_dir
            / "formalization_gap_planner_prover_adapter_contract",
            formalization_gap_planner_cross_prover_matrix_audit_dir=out_dir
            / "formalization_gap_planner_cross_prover_matrix_audit",
            formalization_gap_planner_adapter_registry_audit_dir=out_dir
            / "formalization_gap_planner_adapter_registry_audit",
            formalization_gap_planner_component_resource_registry_audit_dir=out_dir
            / "formalization_gap_planner_component_resource_registry_audit",
            library_snapshot_ref=formalization_gap_planner_library_snapshot_ref,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_publication_bundle",
        stage_start,
    )
    formalization_gap_planner_publication_bundle_audit_manifest = (
        audit_formalization_gap_planner_publication_bundle(
            out_dir / "formalization_gap_planner_publication_bundle",
            out_dir / "formalization_gap_planner_publication_bundle_audit",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formalization_gap_planner_publication_bundle_audit",
        stage_start,
    )
    formal_verifier_replay_repair_manifest = export_formal_verifier_replay_repair_packets(
        out_dir / "formal_verifier_replay",
        out_dir / "formal_verifier_replay_attempts",
        out_dir / "formal_verifier_replay_calibration",
        out_dir / "formal_verifier_replay_repair",
    )
    stage_start = _record_stage(stage_timings, "formal_verifier_replay_repair", stage_start)
    formal_verifier_replay_repair_application_manifest = (
        export_formal_verifier_replay_repair_application_tasks(
            out_dir / "formal_verifier_replay_repair",
            out_dir / "formal_verifier_replay_attempts",
            out_dir / "formal_verifier_replay_repair_application",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_application",
        stage_start,
    )
    formal_verifier_replay_repair_application_validation_manifest = (
        export_formal_verifier_replay_repair_application_validation(
            out_dir / "formal_verifier_replay_repair_application",
            out_dir / "formal_verifier_replay_repair_application_validation",
            lean_project=config.local_lean_project,
            lean_timeout=config.local_lean_timeout,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_application_validation",
        stage_start,
    )
    formal_verifier_replay_repair_execution_queue_manifest = (
        export_formal_verifier_replay_repair_execution_queue(
            out_dir / "formal_verifier_replay_repair_application",
            out_dir / "formal_verifier_replay_repair_application_validation",
            out_dir / "formal_verifier_replay_repair_execution_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_execution_queue",
        stage_start,
    )
    formal_verifier_replay_repair_prompt_packets_manifest = (
        export_formal_verifier_replay_repair_prompt_packets(
            out_dir / "formal_verifier_replay_repair_execution_queue",
            out_dir / "formal_verifier_replay_repair_application",
            out_dir / "formal_verifier_replay_repair_prompt_packets",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_prompt_packets",
        stage_start,
    )
    formal_verifier_replay_repair_patch_autoworker_manifest = (
        export_formal_verifier_replay_repair_patch_autoworker(
            out_dir / "formal_verifier_replay_repair_prompt_packets",
            out_dir / "formal_verifier_replay_repair_patch_autoworker",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_autoworker",
        stage_start,
    )
    formal_verifier_replay_repair_patch_response_validation_manifest = (
        export_formal_verifier_replay_repair_patch_response_validation(
            out_dir / "formal_verifier_replay_repair_prompt_packets",
            out_dir / "formal_verifier_replay_repair_patch_response_validation",
            response_jsonl=(
                out_dir
                / "formal_verifier_replay_repair_patch_autoworker"
                / "formal_verifier_replay_repair_patch_responses.jsonl"
            ),
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_response_validation",
        stage_start,
    )
    formal_verifier_replay_repair_patch_response_promotion_manifest = (
        export_formal_verifier_replay_repair_patch_response_promotion(
            out_dir / "formal_verifier_replay_repair_patch_response_validation",
            out_dir / "formal_verifier_replay_repair_patch_response_promotion",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_response_promotion",
        stage_start,
    )
    formal_verifier_replay_repair_patch_rerun_queue_manifest = (
        export_formal_verifier_replay_repair_patch_rerun_queue(
            out_dir / "formal_verifier_replay_repair_patch_response_validation",
            out_dir / "formal_verifier_replay_repair_patch_response_promotion",
            out_dir / "formal_verifier_replay_repair_patch_rerun_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_rerun_queue",
        stage_start,
    )
    formal_verifier_replay_repair_patch_rerun_attempt_manifest = (
        export_formal_verifier_replay_repair_patch_rerun_attempts(
            out_dir / "formal_verifier_replay_repair_patch_rerun_queue",
            out_dir / "formal_verifier_replay_repair_patch_rerun_attempts",
            lean_project=config.local_lean_project,
            lean_timeout=config.local_lean_timeout,
            max_items=config.formal_verifier_replay_attempts,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_rerun_attempts",
        stage_start,
    )
    formal_verifier_replay_repair_patch_rerun_calibration_manifest = (
        export_formal_verifier_replay_repair_patch_rerun_calibration(
            out_dir / "formal_verifier_replay_repair_patch_rerun_queue",
            out_dir / "formal_verifier_replay_repair_patch_rerun_attempts",
            out_dir / "formal_verifier_replay_repair_patch_rerun_calibration",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_rerun_calibration",
        stage_start,
    )
    formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest = (
        export_formal_verifier_replay_repair_patch_rerun_residual_obligations(
            out_dir / "formal_verifier_replay_repair_patch_rerun_calibration",
            out_dir / "primitive_source_coverage",
            out_dir / "proof_bank_actions",
            out_dir / "formal_verifier_replay_repair_patch_rerun_residual_obligations",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_rerun_residual_obligations",
        stage_start,
    )
    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest = (
        export_formal_verifier_replay_repair_patch_rerun_residual_prompt_packets(
            out_dir / "formal_verifier_replay_repair_patch_rerun_residual_obligations",
            out_dir / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets",
            max_packets=40,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets",
        stage_start,
    )
    formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest = (
        export_formal_verifier_replay_repair_patch_rerun_residual_autoworker(
            out_dir / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets",
            out_dir / "formal_verifier_replay_repair_patch_rerun_residual_autoworker",
            max_responses=40,
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_rerun_residual_autoworker",
        stage_start,
    )
    formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest = (
        export_formal_verifier_replay_repair_patch_rerun_residual_response_validation(
            out_dir / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets",
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_response_validation",
            response_jsonl=(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_autoworker"
                / "formal_verifier_replay_repair_patch_rerun_residual_responses.jsonl"
            ),
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_rerun_residual_response_validation",
        stage_start,
    )
    formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest = (
        export_formal_verifier_replay_repair_patch_rerun_residual_followup_queue(
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_response_validation",
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_replay_repair_patch_rerun_residual_followup_queue",
        stage_start,
    )
    formal_verifier_agentic_proof_strategy_plan_manifest = (
        export_formal_verifier_agentic_proof_strategy_plan(
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue",
            out_dir / "formal_verifier_agentic_proof_strategy_plan",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_agentic_proof_strategy_plan",
        stage_start,
    )
    formal_verifier_agentic_proof_candidate_evaluation_queue_manifest = (
        export_formal_verifier_agentic_proof_candidate_evaluation_queue(
            out_dir / "formal_verifier_agentic_proof_strategy_plan",
            out_dir / "formal_verifier_agentic_proof_candidate_evaluation_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_agentic_proof_candidate_evaluation_queue",
        stage_start,
    )
    formal_verifier_agentic_proof_safety_policy_manifest = (
        export_formal_verifier_agentic_proof_safety_policy(
            out_dir / "formal_verifier_agentic_proof_candidate_evaluation_queue",
            out_dir / "formal_verifier_agentic_proof_safety_policy",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_agentic_proof_safety_policy",
        stage_start,
    )
    formal_verifier_agentic_proof_attempt_population_manifest = (
        export_formal_verifier_agentic_proof_attempt_population(
            out_dir / "formal_verifier_agentic_proof_safety_policy",
            out_dir / "formal_verifier_agentic_proof_attempt_population",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_agentic_proof_attempt_population",
        stage_start,
    )
    formal_verifier_agentic_proof_execution_queue_manifest = (
        export_formal_verifier_agentic_proof_execution_queue(
            out_dir / "formal_verifier_agentic_proof_attempt_population",
            out_dir / "formal_verifier_agentic_proof_execution_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_agentic_proof_execution_queue",
        stage_start,
    )
    formal_verifier_agentic_proof_execution_materializer_manifest = (
        export_formal_verifier_agentic_proof_execution_materializer(
            out_dir / "formal_verifier_agentic_proof_execution_queue",
            out_dir / "formal_verifier_agentic_proof_execution_materializer",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_agentic_proof_execution_materializer",
        stage_start,
    )
    if config.verify_agentic_artifacts:
        formal_verifier_agentic_proof_execution_artifact_verifier_manifest = (
            export_formal_verifier_agentic_proof_execution_artifact_verifier(
                out_dir / "formal_verifier_agentic_proof_execution_materializer",
                out_dir / "formal_verifier_agentic_proof_execution_artifact_verifier",
                lean_project=config.local_lean_project,
                lean_timeout=config.local_lean_timeout,
            )
        )
    else:
        formal_verifier_agentic_proof_execution_artifact_verifier_manifest = (
            _write_disabled_agentic_artifact_verifier_manifest(
                out_dir / "formal_verifier_agentic_proof_execution_artifact_verifier",
                materializer_manifest=formal_verifier_agentic_proof_execution_materializer_manifest,
            )
        )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_agentic_proof_execution_artifact_verifier",
        stage_start,
    )
    formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest = (
        export_formal_verifier_agentic_proof_source_theorem_promotion_queue(
            out_dir / "formal_verifier_agentic_proof_execution_artifact_verifier",
            out_dir / "formal_verifier_agentic_proof_source_theorem_promotion_queue",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_agentic_proof_source_theorem_promotion_queue",
        stage_start,
    )
    formal_verifier_agentic_proof_source_theorem_target_resolution_manifest = (
        export_formal_verifier_agentic_proof_source_theorem_target_resolution(
            out_dir / "formal_verifier_agentic_proof_source_theorem_promotion_queue",
            out_dir / "formal_verifier_agentic_proof_source_theorem_target_resolution",
            formal_verifier_queue_dir=out_dir / "formal_verifier_queue",
            formal_verifier_replay_dir=out_dir / "formal_verifier_replay",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "formal_verifier_agentic_proof_source_theorem_target_resolution",
        stage_start,
    )

    research_training_manifest = export_research_training_dataset(
        out_dir / "research_benchmark",
        out_dir / "research_training_export",
        validation_fraction=0.2,
    )
    stage_start = _record_stage(stage_timings, "research_training_export", stage_start)
    research_policy_manifest = evaluate_research_policy_baseline(
        Path(str(research_training_manifest["train_jsonl"])),
        Path(str(research_training_manifest["validation_jsonl"])),
        out_dir / "research_policy_baseline",
        k=5,
    )
    stage_start = _record_stage(stage_timings, "research_policy_baseline", stage_start)
    next_iteration_manifest = audit_next_iteration_queue(
        out_dir / "research_benchmark",
        out_dir / "next_iteration_queue",
    )
    stage_start = _record_stage(stage_timings, "next_iteration_queue", stage_start)
    research_report_manifest = build_research_markdown_report(
        out_dir / "research_benchmark",
        out_dir / "research_report",
    )
    stage_start = _record_stage(stage_timings, "research_report", stage_start)
    claim_ledger_manifest = build_claim_ledger(
        out_dir / "research_benchmark",
        out_dir / "claim_ledger",
        proof_audit_manifest=claim_ledger_proof_manifest_path,
        repair_response_promotion_manifest=(
            out_dir
            / "formal_verifier_replay_repair_patch_response_promotion"
            / "formal_verifier_replay_repair_patch_response_promotion_manifest.json"
        ),
    )
    stage_start = _record_stage(stage_timings, "claim_ledger", stage_start)
    claim_ledger_action_manifest = export_claim_ledger_actions(
        out_dir / "claim_ledger",
        out_dir / "claim_ledger_actions",
    )
    stage_start = _record_stage(stage_timings, "claim_ledger_actions", stage_start)
    stat_claim_certificate_manifest = export_stat_claim_certificate_plan(
        out_dir / "claim_ledger",
        out_dir / "stat_claim_certificate_plan",
    )
    stage_start = _record_stage(stage_timings, "stat_claim_certificate_plan", stage_start)
    stat_claim_certificate_checker_manifest = await audit_stat_claim_certificate_checkers(
        verifier,
        out_dir / "stat_claim_certificate_checker_audit",
    )
    stage_start = _record_stage(stage_timings, "stat_claim_certificate_checker_audit", stage_start)
    stat_claim_certificate_readiness_manifest = export_stat_claim_certificate_readiness_overlay(
        out_dir / "stat_claim_certificate_plan",
        out_dir / "stat_claim_certificate_checker_audit",
        out_dir / "stat_claim_certificate_readiness",
    )
    stage_start = _record_stage(stage_timings, "stat_claim_certificate_readiness", stage_start)
    stat_claim_certificate_witness_queue_manifest = export_stat_claim_certificate_witness_queue(
        out_dir / "stat_claim_certificate_plan",
        out_dir / "stat_claim_certificate_readiness",
        out_dir / "stat_claim_certificate_witness_queue",
    )
    stage_start = _record_stage(stage_timings, "stat_claim_certificate_witness_queue", stage_start)
    stat_claim_certificate_witness_materializer_manifest = materialize_stat_claim_certificate_witness_drafts(
        out_dir / "stat_claim_certificate_witness_queue",
        out_dir / "stat_claim_certificate_witness_materializer",
    )
    stage_start = _record_stage(stage_timings, "stat_claim_certificate_witness_materializer", stage_start)
    stat_claim_certificate_witness_prompt_packets_manifest = (
        export_stat_claim_certificate_witness_prompt_packets(
            out_dir / "stat_claim_certificate_witness_materializer",
            out_dir / "stat_claim_certificate_witness_prompt_packets",
        )
    )
    stage_start = _record_stage(stage_timings, "stat_claim_certificate_witness_prompt_packets", stage_start)
    stat_claim_certificate_witness_context_packets_manifest = (
        export_stat_claim_certificate_witness_context_packets(
            out_dir / "stat_claim_certificate_witness_prompt_packets",
            out_dir / "stat_claim_certificate_witness_context_packets",
        )
    )
    stage_start = _record_stage(stage_timings, "stat_claim_certificate_witness_context_packets", stage_start)
    stat_claim_certificate_witness_context_triage_manifest = (
        export_stat_claim_certificate_witness_context_triage(
            out_dir / "stat_claim_certificate_witness_context_packets",
            out_dir / "stat_claim_certificate_witness_context_triage",
        )
    )
    stage_start = _record_stage(stage_timings, "stat_claim_certificate_witness_context_triage", stage_start)
    stat_claim_certificate_witness_response_validation_manifest = (
        validate_stat_claim_certificate_witness_worker_outputs(
            out_dir / "stat_claim_certificate_witness_prompt_packets",
            out_dir / "stat_claim_certificate_witness_response_validation",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "stat_claim_certificate_witness_response_validation",
        stage_start,
    )
    stat_claim_certificate_witness_response_apply_manifest = (
        apply_stat_claim_certificate_witness_responses(
            out_dir / "stat_claim_certificate_witness_response_validation",
            out_dir / "stat_claim_certificate_witness_response_apply",
            materializer_dir=out_dir / "stat_claim_certificate_witness_materializer",
        )
    )
    stage_start = _record_stage(
        stage_timings,
        "stat_claim_certificate_witness_response_apply",
        stage_start,
    )
    stat_claim_certificate_witness_validator_manifest = validate_stat_claim_certificate_witness_drafts(
        out_dir / "stat_claim_certificate_witness_response_apply",
        out_dir / "stat_claim_certificate_witness_validator",
    )
    stage_start = _record_stage(stage_timings, "stat_claim_certificate_witness_validator", stage_start)
    theorem_composition_manifest = export_theorem_composition_packets(
        out_dir / "claim_ledger",
        out_dir / "theorem_composition",
    )
    stage_start = _record_stage(stage_timings, "theorem_composition_export", stage_start)

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
    research_agent_runtime_audit_manifest = _research_agent_runtime_audit_overlay(
        out_dir,
        configured_runtime_dir=config.research_agent_runtime_dir,
        enable_offline_smoke=config.research_agent_runtime_offline_smoke,
        enable_contract_smoke=config.research_agent_runtime_contract_smoke,
        question_file=actual_question_file,
    )
    stage_start = _record_stage(stage_timings, "research_agent_runtime_audit_overlay", stage_start)
    runtime_scorecard_rows = (
        research_agent_runtime_audit_manifest.get("capability_scorecard", {}).get(
            "rows",
            [],
        )
        if isinstance(
            research_agent_runtime_audit_manifest.get("capability_scorecard", {}),
            Mapping,
        )
        else []
    )
    runtime_scorecard_rows_by_id = {
        str(row.get("requirement_id", "") or ""): row
        for row in runtime_scorecard_rows
        if isinstance(row, Mapping) and str(row.get("requirement_id", "") or "")
    }
    runtime_pf_semantic_bridge_scorecard_row = runtime_scorecard_rows_by_id.get(
        "pseudo_formal_semantic_primitives_reach_source_semantic_bridge",
        {},
    )
    runtime_pf_exact_semantic_source_lookup_scorecard_row = (
        runtime_scorecard_rows_by_id.get(
            "pseudo_formal_exact_semantic_definitions_reach_exact_definition_source_lookup",
            {},
        )
    )
    runtime_architect_deferred_meta_scorecard_row = (
        runtime_scorecard_rows_by_id.get(
            "architect_deferred_meta_capability_gaps_visible",
            {},
        )
    )
    runtime_architect_deferred_meta_resolved_scorecard_row = (
        runtime_scorecard_rows_by_id.get(
            "architect_deferred_meta_capability_gaps_resolved",
            {},
        )
    )
    runtime_architect_deferred_meta_replay_scorecard_row = (
        runtime_scorecard_rows_by_id.get(
            "architect_deferred_meta_capability_gap_resolution_replay_priority_pinned",
            {},
        )
    )
    runtime_formal_gap_planner_context_scorecard_row = (
        runtime_scorecard_rows_by_id.get(
            "formal_gap_planner_executable_handoff_context_complete",
            {},
        )
    )
    runtime_formal_gap_planner_followthrough_scorecard_row = (
        runtime_scorecard_rows_by_id.get(
            "formal_gap_planner_live_route_planner_followthrough",
            {},
        )
    )
    runtime_source_theorem_proof_body_executor_scorecard_row = (
        runtime_scorecard_rows_by_id.get(
            "source_theorem_proof_body_executor_ran",
            {},
        )
    )
    runtime_source_theorem_signature_probe_scorecard_row = (
        runtime_scorecard_rows_by_id.get(
            "source_theorem_signature_probe_reached_proof_body",
            {},
        )
    )
    runtime_source_theorem_proof_body_same_lane_scorecard_row = (
        runtime_scorecard_rows_by_id.get(
            "source_theorem_proof_body_same_lane_verifier_evidence",
            {},
        )
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
        "frontier_discover_and_prove_prompt_packets": bool(
            frontier_dap_prompt_packets_manifest["all_ok"]
        ),
        "paper_theory_roundtrip": bool(paper_theory_roundtrip_manifest["all_ok"]),
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
        "lean_rag_dependency_health": bool(lean_rag_dependency_health_manifest["all_ok"]),
        "lean_rag_package_contract": bool(lean_rag_package_manifest["all_ok"]),
        "lean_rag_source_registry_expansion": bool(
            lean_rag_source_registry_expansion_manifest["all_ok"]
        ),
        "lean_rag_source_registry_expansion_preflight": bool(
            lean_rag_source_registry_expansion_preflight_manifest[
                "source_registry_apply_ready"
            ]
            or int(lean_rag_source_registry_expansion_manifest.get("n_staged", 0)) == 0
        ),
        "lean_rag_source_registry_expansion_apply": bool(
            (
                lean_rag_source_registry_expansion_apply_manifest["apply_ready"]
                and lean_rag_source_registry_expansion_apply_manifest["dry_run"]
                and not lean_rag_source_registry_expansion_apply_manifest["applied"]
            )
            or int(lean_rag_source_registry_expansion_manifest.get("n_staged", 0)) == 0
        ),
        "huggingface_lean_source_audit": bool(
            huggingface_lean_source_manifest["summary"].get("oproofs_detected")
        )
        and int(huggingface_lean_source_manifest["summary"].get("n_candidates", 0)) > 0,
        "huggingface_lean_source_revalidation_tasks": bool(
            huggingface_lean_source_revalidation_tasks_manifest["all_ok"]
        )
        and int(huggingface_lean_source_revalidation_tasks_manifest["n_tasks"]) > 0,
        "huggingface_lean_source_revalidation_prompt_packets": bool(
            huggingface_lean_source_revalidation_prompt_packets_manifest["all_ok"]
        )
        and int(
            huggingface_lean_source_revalidation_prompt_packets_manifest[
                "n_prompt_packets"
            ]
        )
        > 0,
        "huggingface_lean_source_revalidation_artifact_validation": bool(
            huggingface_lean_source_revalidation_artifact_validation_manifest["all_ok"]
        )
        and int(
            huggingface_lean_source_revalidation_artifact_validation_manifest[
                "n_validation_rows"
            ]
        )
        > 0,
        "huggingface_lean_source_revalidation_promotion_queue": bool(
            huggingface_lean_source_revalidation_promotion_queue_manifest["all_ok"]
        )
        and int(
            huggingface_lean_source_revalidation_promotion_queue_manifest[
                "n_promotion_rows"
            ]
        )
        > 0,
        "fresh_holdout_frontier_audit": bool(fresh_holdout_manifest["all_ok"]),
        "research_algorithm_audit": bool(algorithm_manifest["all_ok"]),
        "algorithm_simulation_stress_audit": bool(algorithm_simulation_stress_manifest["all_ok"]),
        "research_agent_runtime_audit": (
            bool(research_agent_runtime_audit_manifest["all_ok"])
            if research_agent_runtime_audit_manifest["requested"]
            else True
        ),
        "proof_audit": bool(proof_manifest["all_verified"])
        and bool(proof_manifest["dependency_graph"]["all_ok"])
        and (
            not (config.use_axle or config.use_local_lean)
            or bool(proof_manifest["all_kernel_verified"])
        ),
        "kernel_smoke_proof_audit": (
            True
            if kernel_smoke_manifest is None
            else bool(kernel_smoke_manifest["all_kernel_verified"])
            and bool(kernel_smoke_manifest["dependency_graph"]["all_ok"])
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
        "proof_search_retrieval_no_registered_ablation": bool(
            proof_search_retrieval_no_registered_ablation_manifest["all_ok"]
        )
        and not bool(proof_search_retrieval_no_registered_ablation_manifest["include_registered_proof"]),
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
        "proof_bank_action_export": bool(proof_bank_action_manifest["all_ok"]),
        "assumption_interface_export": bool(assumption_interface_manifest["all_ok"]),
        "primitive_source_coverage_audit": bool(primitive_source_coverage_manifest["all_ok"]),
        "formalization_delta_plan": bool(formalization_delta_manifest["all_ok"]),
        "formal_verifier_queue": bool(formal_verifier_queue_manifest["all_ok"]),
        "goal_conditioned_minimal_formalization_plan": bool(
            goal_conditioned_minimal_formalization_plan_manifest["all_ok"]
        ),
        "formalization_gap_planner_portable_plan_audit": bool(
            formalization_gap_planner_portable_plan_audit_manifest["all_ok"]
        ),
        "formalization_gap_planner_library_coverage_map": bool(
            formalization_gap_planner_library_coverage_map_manifest["all_ok"]
        ),
        "formalization_gap_planner_primitive_action_queue": bool(
            formalization_gap_planner_primitive_action_queue_manifest["all_ok"]
        ),
        "formalization_gap_planner_minimal_delta_audit": bool(
            formalization_gap_planner_minimal_delta_audit_manifest["all_ok"]
        ),
        "formalization_gap_planner_source_grounding_audit": bool(
            formalization_gap_planner_source_grounding_audit_manifest["all_ok"]
        ),
        "formalization_gap_planner_target_intake": bool(
            formalization_gap_planner_target_intake_manifest["all_ok"]
        ),
        "formalization_gap_planner_benchmark": bool(
            formalization_gap_planner_benchmark_manifest["all_ok"]
        ),
        "formalization_gap_planner_benchmark_audit": bool(
            formalization_gap_planner_benchmark_audit_manifest["all_ok"]
        ),
        "formalization_gap_planner_evaluation": bool(
            formalization_gap_planner_evaluation_manifest["all_ok"]
        ),
        "formal_verifier_replay": bool(formal_verifier_replay_manifest["all_ok"]),
        "formal_verifier_replay_attempts": bool(formal_verifier_replay_attempt_manifest["all_ok"]),
        "formal_verifier_replay_calibration": bool(
            formal_verifier_replay_calibration_manifest["all_ok"]
        ),
        "formalization_gap_planner_refinement_queue": bool(
            formalization_gap_planner_refinement_queue_manifest["all_ok"]
        ),
        "formalization_gap_planner_refinement_adapter_responses": bool(
            formalization_gap_planner_refinement_adapter_manifest["all_ok"]
        ),
        "formalization_gap_planner_local_literature_adapter": bool(
            formalization_gap_planner_local_literature_adapter_manifest["all_ok"]
        ),
        "formalization_gap_planner_local_formal_source_adapter": bool(
            formalization_gap_planner_local_formal_source_adapter_manifest["all_ok"]
        ),
        "formalization_gap_planner_local_proof_state_adapter": bool(
            formalization_gap_planner_local_proof_state_adapter_manifest["all_ok"]
        ),
        "formalization_gap_planner_refinement_evidence": bool(
            formalization_gap_planner_refinement_evidence_manifest["all_ok"]
        ),
        "formalization_gap_planner_route_revision_overlay": bool(
            formalization_gap_planner_route_revision_overlay_manifest["all_ok"]
        ),
        "formalization_gap_planner_route_stability_audit": bool(
            formalization_gap_planner_route_stability_audit_manifest["all_ok"]
        ),
        "formalization_gap_planner_route_replan_handoff": bool(
            formalization_gap_planner_route_replan_handoff_manifest["all_ok"]
        ),
        "formalization_gap_planner_route_replan_handoff_audit": bool(
            formalization_gap_planner_route_replan_handoff_audit_manifest["all_ok"]
        ),
        "formalization_gap_planner_proof_state_triage": bool(
            formalization_gap_planner_proof_state_triage_manifest["all_ok"]
        ),
        "formalization_gap_planner_interactive_session": bool(
            formalization_gap_planner_interactive_session_manifest["all_ok"]
        ),
        "formalization_gap_planner_ablation_study": bool(
            formalization_gap_planner_ablation_study_manifest["all_ok"]
        ),
        "formalization_gap_planner_prover_adapter_contract": bool(
            formalization_gap_planner_prover_adapter_contract_manifest["all_ok"]
        ),
        "formalization_gap_planner_adapter_registry": bool(
            formalization_gap_planner_adapter_registry_manifest["all_ok"]
        ),
        "formalization_gap_planner_adapter_registry_audit": bool(
            formalization_gap_planner_adapter_registry_audit_manifest["all_ok"]
        ),
        "formalization_gap_planner_component_resource_registry": bool(
            formalization_gap_planner_component_resource_registry_manifest["all_ok"]
        ),
        "formalization_gap_planner_component_resource_registry_audit": bool(
            formalization_gap_planner_component_resource_registry_audit_manifest[
                "all_ok"
            ]
        ),
        "formalization_gap_planner_action_resource_plan": bool(
            formalization_gap_planner_action_resource_plan_manifest["all_ok"]
        ),
        "formalization_gap_planner_resource_request_queue": bool(
            formalization_gap_planner_resource_request_queue_manifest["all_ok"]
        ),
        "formalization_gap_planner_resource_response_ledger": bool(
            formalization_gap_planner_resource_response_ledger_manifest["all_ok"]
        ),
        "formalization_gap_planner_cross_prover_matrix_audit": bool(
            formalization_gap_planner_cross_prover_matrix_audit_manifest["all_ok"]
        ),
        "formalization_gap_planner_publication_bundle": bool(
            formalization_gap_planner_publication_bundle_manifest["all_ok"]
        ),
        "formalization_gap_planner_publication_bundle_audit": bool(
            formalization_gap_planner_publication_bundle_audit_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair": bool(formal_verifier_replay_repair_manifest["all_ok"]),
        "formal_verifier_replay_repair_application": bool(
            formal_verifier_replay_repair_application_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_application_validation": bool(
            formal_verifier_replay_repair_application_validation_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_execution_queue": bool(
            formal_verifier_replay_repair_execution_queue_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_prompt_packets": bool(
            formal_verifier_replay_repair_prompt_packets_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_patch_autoworker": bool(
            formal_verifier_replay_repair_patch_autoworker_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_patch_response_validation": bool(
            formal_verifier_replay_repair_patch_response_validation_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_patch_response_promotion": bool(
            formal_verifier_replay_repair_patch_response_promotion_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_patch_rerun_queue": bool(
            formal_verifier_replay_repair_patch_rerun_queue_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_patch_rerun_attempts": bool(
            formal_verifier_replay_repair_patch_rerun_attempt_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_patch_rerun_calibration": bool(
            formal_verifier_replay_repair_patch_rerun_calibration_manifest["all_ok"]
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_obligations": bool(
            formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "all_ok"
            ]
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets": bool(
            formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest[
                "all_ok"
            ]
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_autoworker": bool(
            formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest[
                "all_ok"
            ]
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_response_validation": bool(
            formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "all_ok"
            ]
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_followup_queue": bool(
            formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest[
                "all_ok"
            ]
        ),
        "formal_verifier_agentic_proof_strategy_plan": bool(
            formal_verifier_agentic_proof_strategy_plan_manifest["all_ok"]
        ),
        "formal_verifier_agentic_proof_candidate_evaluation_queue": bool(
            formal_verifier_agentic_proof_candidate_evaluation_queue_manifest["all_ok"]
        ),
        "formal_verifier_agentic_proof_safety_policy": bool(
            formal_verifier_agentic_proof_safety_policy_manifest["all_ok"]
        ),
        "formal_verifier_agentic_proof_attempt_population": bool(
            formal_verifier_agentic_proof_attempt_population_manifest["all_ok"]
        ),
        "formal_verifier_agentic_proof_execution_queue": bool(
            formal_verifier_agentic_proof_execution_queue_manifest["all_ok"]
        ),
        "formal_verifier_agentic_proof_execution_materializer": bool(
            formal_verifier_agentic_proof_execution_materializer_manifest["all_ok"]
        ),
        "formal_verifier_agentic_proof_execution_artifact_verifier": bool(
            formal_verifier_agentic_proof_execution_artifact_verifier_manifest["all_ok"]
        ),
        "formal_verifier_agentic_proof_source_theorem_promotion_queue": bool(
            formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest[
                "all_ok"
            ]
        ),
        "formal_verifier_agentic_proof_source_theorem_target_resolution": bool(
            formal_verifier_agentic_proof_source_theorem_target_resolution_manifest[
                "all_ok"
            ]
        ),
        "research_training_export": bool(research_training_manifest["all_ok"]),
        "research_policy_baseline": bool(research_policy_manifest["all_ok"]),
        "next_iteration_queue": bool(next_iteration_manifest["all_ok"]),
        "research_report": bool(research_report_manifest["all_ok"]),
        "claim_ledger": bool(claim_ledger_manifest["all_ok"]),
        "claim_ledger_actions": bool(claim_ledger_action_manifest["all_ok"]),
        "stat_claim_certificate_plan": bool(stat_claim_certificate_manifest["all_ok"]),
        "stat_claim_certificate_checker_audit": bool(stat_claim_certificate_checker_manifest["all_ok"]),
        "stat_claim_certificate_readiness": bool(stat_claim_certificate_readiness_manifest["all_ok"]),
        "stat_claim_certificate_witness_queue": bool(stat_claim_certificate_witness_queue_manifest["all_ok"]),
        "stat_claim_certificate_witness_materializer": bool(
            stat_claim_certificate_witness_materializer_manifest["all_ok"]
        ),
        "stat_claim_certificate_witness_prompt_packets": bool(
            stat_claim_certificate_witness_prompt_packets_manifest["all_ok"]
        ),
        "stat_claim_certificate_witness_context_packets": bool(
            stat_claim_certificate_witness_context_packets_manifest["all_ok"]
        ),
        "stat_claim_certificate_witness_context_triage": bool(
            stat_claim_certificate_witness_context_triage_manifest["all_ok"]
        ),
        "stat_claim_certificate_witness_response_validation": bool(
            stat_claim_certificate_witness_response_validation_manifest["all_ok"]
        ),
        "stat_claim_certificate_witness_response_apply": bool(
            stat_claim_certificate_witness_response_apply_manifest["all_ok"]
        ),
        "stat_claim_certificate_witness_validator": bool(
            stat_claim_certificate_witness_validator_manifest["all_ok"]
        ),
        "theorem_composition_export": bool(theorem_composition_manifest["all_ok"]),
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
        "proof_bank_action_export",
        "formal_verifier_queue",
        "goal_conditioned_minimal_formalization_plan",
        "formalization_gap_planner_portable_plan_audit",
        "formalization_gap_planner_library_coverage_map",
        "formalization_gap_planner_primitive_action_queue",
        "formalization_gap_planner_target_intake",
        "formalization_gap_planner_benchmark",
        "formalization_gap_planner_benchmark_audit",
        "formalization_gap_planner_evaluation",
        "formal_verifier_replay",
        "formal_verifier_replay_attempts",
        "formal_verifier_replay_calibration",
        "formalization_gap_planner_refinement_queue",
        "formalization_gap_planner_refinement_adapter_responses",
        "formalization_gap_planner_local_literature_adapter",
        "formalization_gap_planner_local_formal_source_adapter",
        "formalization_gap_planner_local_proof_state_adapter",
        "formalization_gap_planner_refinement_evidence",
        "formalization_gap_planner_route_revision_overlay",
        "formalization_gap_planner_route_stability_audit",
        "formalization_gap_planner_route_replan_handoff",
        "formalization_gap_planner_route_replan_handoff_audit",
        "formalization_gap_planner_proof_state_triage",
        "formalization_gap_planner_interactive_session",
        "formalization_gap_planner_ablation_study",
        "formalization_gap_planner_prover_adapter_contract",
        "formalization_gap_planner_adapter_registry",
        "formalization_gap_planner_adapter_registry_audit",
        "formalization_gap_planner_component_resource_registry",
        "formalization_gap_planner_component_resource_registry_audit",
        "formalization_gap_planner_action_resource_plan",
        "formalization_gap_planner_resource_request_queue",
        "formalization_gap_planner_resource_response_ledger",
        "formalization_gap_planner_publication_bundle",
        "formalization_gap_planner_publication_bundle_audit",
        "formal_verifier_replay_repair",
        "formal_verifier_replay_repair_application",
        "formal_verifier_replay_repair_application_validation",
        "formal_verifier_replay_repair_execution_queue",
        "formal_verifier_replay_repair_prompt_packets",
        "formal_verifier_replay_repair_patch_autoworker",
        "formal_verifier_replay_repair_patch_response_validation",
        "formal_verifier_replay_repair_patch_response_promotion",
        "formal_verifier_replay_repair_patch_rerun_queue",
        "formal_verifier_replay_repair_patch_rerun_attempts",
        "formal_verifier_replay_repair_patch_rerun_calibration",
        "formal_verifier_replay_repair_patch_rerun_residual_obligations",
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets",
        "formal_verifier_replay_repair_patch_rerun_residual_autoworker",
        "formal_verifier_replay_repair_patch_rerun_residual_response_validation",
        "formal_verifier_replay_repair_patch_rerun_residual_followup_queue",
        "formal_verifier_agentic_proof_strategy_plan",
        "formal_verifier_agentic_proof_candidate_evaluation_queue",
        "formal_verifier_agentic_proof_safety_policy",
        "formal_verifier_agentic_proof_attempt_population",
        "formal_verifier_agentic_proof_execution_queue",
        "formal_verifier_agentic_proof_execution_materializer",
        "formal_verifier_agentic_proof_execution_artifact_verifier",
        "formal_verifier_agentic_proof_source_theorem_promotion_queue",
        "formal_verifier_agentic_proof_source_theorem_target_resolution",
        "research_training_export",
        "research_policy_baseline",
        "next_iteration_queue",
        "research_report",
        "claim_ledger",
        "claim_ledger_actions",
        "stat_claim_certificate_plan",
        "stat_claim_certificate_checker_audit",
        "stat_claim_certificate_readiness",
        "stat_claim_certificate_witness_queue",
        "stat_claim_certificate_witness_materializer",
        "stat_claim_certificate_witness_prompt_packets",
        "stat_claim_certificate_witness_context_packets",
        "stat_claim_certificate_witness_context_triage",
        "stat_claim_certificate_witness_response_validation",
        "stat_claim_certificate_witness_response_apply",
        "stat_claim_certificate_witness_validator",
        "theorem_composition_export",
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
            "kernel_smoke_ids": list(config.kernel_smoke_ids),
            "kernel_smoke_from_actions": config.kernel_smoke_from_actions,
            "formal_source_index_cache": config.formal_source_index_cache or "",
            "refresh_formal_source_index_cache": config.refresh_formal_source_index_cache,
            "lean_rag_db": config.lean_rag_db or "",
            "lean_rag_package_root": config.lean_rag_package_root or "",
            "frontier_smoke_cache": config.frontier_smoke_cache or "",
            "refresh_frontier_smoke_cache": config.refresh_frontier_smoke_cache,
            "formal_source_graph_cache": config.formal_source_graph_cache or "",
            "refresh_formal_source_graph_cache": config.refresh_formal_source_graph_cache,
            "research_benchmark_cache": config.research_benchmark_cache or "",
            "refresh_research_benchmark_cache": config.refresh_research_benchmark_cache,
            "formal_verifier_replay_attempts": config.formal_verifier_replay_attempts,
            "formal_verifier_replay_attempt_log": config.formal_verifier_replay_attempt_log or "",
            "verify_agentic_artifacts": config.verify_agentic_artifacts,
            "adaptive_mc_rerun": config.adaptive_mc_rerun,
            "adaptive_mc_multiplier": config.adaptive_mc_multiplier,
            "research_agent_runtime_dir": config.research_agent_runtime_dir or "",
            "research_agent_runtime_offline_smoke": (
                config.research_agent_runtime_offline_smoke
            ),
            "research_agent_runtime_contract_smoke": (
                config.research_agent_runtime_contract_smoke
            ),
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
            "frontier_dap_prompt_packets": frontier_dap_prompt_packets_manifest[
                "n_prompt_packets"
            ],
            "frontier_dap_output_contracts": frontier_dap_prompt_packets_manifest[
                "n_output_contracts"
            ],
            "frontier_dap_expected_results_withheld": frontier_dap_prompt_packets_manifest[
                "n_expected_results_withheld"
            ],
            "frontier_dap_source_identity_withheld": frontier_dap_prompt_packets_manifest[
                "n_source_identity_withheld"
            ],
            "frontier_dap_prompt_expected_result_leaks": frontier_dap_prompt_packets_manifest[
                "n_prompt_expected_result_leaks"
            ],
            "frontier_dap_source_identity_leaks": frontier_dap_prompt_packets_manifest[
                "n_prompt_source_identity_leaks"
            ],
            "frontier_dap_proof_evidence_ready": frontier_dap_prompt_packets_manifest[
                "n_proof_evidence_ready"
            ],
            "frontier_dap_proof_evidence_status": frontier_dap_prompt_packets_manifest[
                "proof_evidence_status"
            ],
            "paper_theory_roundtrip_tex_files": paper_theory_roundtrip_manifest[
                "n_tex_files"
            ],
            "paper_theory_roundtrip_statements": paper_theory_roundtrip_manifest[
                "n_statements"
            ],
            "paper_theory_roundtrip_statements_with_proofs": paper_theory_roundtrip_manifest[
                "n_with_proofs"
            ],
            "paper_theory_roundtrip_dependency_edges": paper_theory_roundtrip_manifest[
                "n_dependency_edges"
            ],
            "paper_theory_roundtrip_stat_theory_ir_rows": paper_theory_roundtrip_manifest[
                "n_stat_theory_ir_rows"
            ],
            "paper_theory_roundtrip_lean_candidate_queue_rows": paper_theory_roundtrip_manifest[
                "n_lean_candidate_queue_rows"
            ],
            "paper_theory_roundtrip_roundtrip_review_rows": paper_theory_roundtrip_manifest[
                "n_roundtrip_review_rows"
            ],
            "paper_theory_roundtrip_proof_evidence_ready": paper_theory_roundtrip_manifest[
                "n_proof_evidence_ready"
            ],
            "paper_theory_roundtrip_proof_evidence_status": paper_theory_roundtrip_manifest[
                "proof_evidence_status"
            ],
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
            "formal_source_retrieval_external_benchmark_cases": formal_source_retrieval_external_manifest[
                "n_cases"
            ],
            "formal_source_retrieval_external_benchmark_ok": formal_source_retrieval_external_manifest["n_ok"],
            "formal_source_retrieval_external_benchmark_recall_at_k": formal_source_retrieval_external_manifest[
                "recall_at_k"
            ],
            "formal_source_retrieval_external_benchmark_mrr": formal_source_retrieval_external_manifest[
                "mean_reciprocal_rank"
            ],
            "formal_source_retrieval_all_benchmark_cases": formal_source_retrieval_all_manifest["n_cases"],
            "formal_source_retrieval_all_benchmark_ok": formal_source_retrieval_all_manifest["n_ok"],
            "formal_source_retrieval_all_benchmark_recall_at_k": formal_source_retrieval_all_manifest[
                "recall_at_k"
            ],
            "formal_source_retrieval_all_benchmark_mrr": formal_source_retrieval_all_manifest[
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
            "formal_source_retrieval_ablation_dependency_sensitive_cases": formal_source_retrieval_ablation_manifest[
                "n_dependency_sensitive_cases"
            ],
            "formal_source_retrieval_ablation_dependency_sensitive_new_hits": formal_source_retrieval_ablation_manifest[
                "n_dependency_sensitive_new_hits"
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
            "lean_rag_dependency_health_status": lean_rag_dependency_health_manifest[
                "health_status"
            ],
            "lean_rag_dependency_health_ok": lean_rag_dependency_health_manifest["all_ok"],
            "lean_rag_dependency_active_enabled": lean_rag_dependency_health_manifest[
                "active_enabled"
            ],
            "lean_rag_dependency_fallback_used": lean_rag_dependency_health_manifest[
                "fallback_used"
            ],
            "lean_rag_dependency_fallback_reason": lean_rag_dependency_health_manifest[
                "fallback_reason"
            ],
            "lean_rag_dependency_requested_integrity_ok": lean_rag_dependency_health_manifest[
                "requested_health"
            ].get("integrity_check_ok", False),
            "lean_rag_dependency_requested_fts_probe_ok": lean_rag_dependency_health_manifest[
                "requested_health"
            ].get("fts_probe_ok", False),
            "lean_rag_package_available": lean_rag_package_manifest["available"],
            "lean_rag_package_contract_ok": lean_rag_package_manifest["contract_ok"],
            "lean_rag_package_root": lean_rag_package_manifest["package_root"],
            "lean_rag_package_branch": lean_rag_package_manifest["git"].get("branch", ""),
            "lean_rag_package_commit": lean_rag_package_manifest["git"].get("commit", ""),
            "lean_rag_package_dirty": lean_rag_package_manifest["git"].get("dirty", False),
            "lean_rag_package_local_sources": lean_rag_package_manifest["source_registry"].get(
                "n_local_sources",
                0,
            ),
            "lean_rag_package_external_sources": lean_rag_package_manifest["source_registry"].get(
                "n_external_sources",
                0,
            ),
            "lean_rag_package_seed_queries": lean_rag_package_manifest["seed_queries"].get(
                "n_queries",
                0,
            ),
            "lean_rag_package_seed_query_lanes": lean_rag_package_manifest["seed_queries"].get(
                "n_lanes",
                0,
            ),
            "lean_rag_package_target_sources": lean_rag_package_manifest[
                "target_source_coverage"
            ].get("n_targets", 0),
            "lean_rag_package_target_sources_present": lean_rag_package_manifest[
                "target_source_coverage"
            ].get("n_present", 0),
            "lean_rag_package_target_sources_missing": lean_rag_package_manifest[
                "target_source_coverage"
            ].get("n_missing", 0),
            "lean_rag_package_target_source_coverage_ok": lean_rag_package_manifest[
                "target_source_coverage"
            ].get("coverage_ok", False),
            "lean_rag_package_missing_target_sources": list(
                lean_rag_package_manifest["target_source_coverage"].get(
                    "missing_target_ids",
                    (),
                )
            ),
            "lean_rag_package_registry_expansion_candidates": lean_rag_package_manifest[
                "target_source_coverage"
            ].get("n_registry_expansion_candidates", 0),
            "lean_rag_package_registry_expansion_candidate_names": [
                str(dict(candidate.get("entry", {}) or {}).get("name", ""))
                for candidate in lean_rag_package_manifest[
                    "target_source_coverage"
                ].get("registry_expansion_candidates", ())
                if isinstance(candidate, dict)
            ],
            "lean_rag_package_verify_candidates_with_lean": lean_rag_package_manifest[
                "source_registry"
            ].get("policy", {}).get("verify_candidates_with_lean", False),
            "lean_rag_package_refresh_dirty_checkouts": lean_rag_package_manifest[
                "source_registry"
            ].get("policy", {}).get("refresh_dirty_checkouts", None),
            "lean_rag_package_graph_manifest_available": lean_rag_package_manifest[
                "shared_graph_manifest"
            ].get("available", False),
            "lean_rag_package_indexed_checkouts": lean_rag_package_manifest[
                "shared_graph_manifest"
            ].get("n_indexed_checkouts", 0),
            "lean_rag_package_dirty_indexed_checkouts": lean_rag_package_manifest[
                "shared_graph_manifest"
            ].get("n_dirty_checkouts", 0),
            "lean_rag_package_status_drift_supported": lean_rag_package_manifest[
                "script_capabilities"
            ].get("shared_status_reports_live_drift", False),
            "huggingface_lean_source_candidates": huggingface_lean_source_manifest[
                "summary"
            ].get("n_candidates", 0),
            "huggingface_lean_source_high_priority": huggingface_lean_source_manifest[
                "summary"
            ].get("n_high", 0),
            "huggingface_lean_source_critical": huggingface_lean_source_manifest[
                "summary"
            ].get("n_critical", 0),
            "huggingface_lean_source_public_ungated": huggingface_lean_source_manifest[
                "summary"
            ].get("n_public_ungated", 0),
            "huggingface_lean_source_oproofs_detected": huggingface_lean_source_manifest[
                "summary"
            ].get("oproofs_detected", False),
            "huggingface_lean_source_oproofs_reported_rows": huggingface_lean_source_manifest[
                "summary"
            ].get("oproofs_reported_rows", 0),
            "huggingface_lean_source_rag_integration_rows": len(
                huggingface_lean_source_manifest.get("rag_integration_plan", ())
            ),
            "huggingface_lean_source_revalidation_queue_rows": huggingface_lean_source_manifest[
                "revalidation_queue_summary"
            ].get("n_queue_rows", 0),
            "huggingface_lean_source_revalidation_queue_ready": huggingface_lean_source_manifest[
                "revalidation_queue_summary"
            ].get("n_ready", 0),
            "huggingface_lean_source_revalidation_queue_blocked": huggingface_lean_source_manifest[
                "revalidation_queue_summary"
            ].get("n_blocked", 0),
            "huggingface_lean_source_revalidation_queue_kernel_verified": huggingface_lean_source_manifest[
                "revalidation_queue_summary"
            ].get("n_kernel_verified", 0),
            "huggingface_lean_source_revalidation_queue_proof_evidence_ready": huggingface_lean_source_manifest[
                "revalidation_queue_summary"
            ].get("n_proof_evidence_ready", 0),
            "huggingface_lean_source_revalidation_queue_proof_evidence_status": huggingface_lean_source_manifest[
                "revalidation_queue_summary"
            ].get("proof_evidence_status", ""),
            "huggingface_lean_source_revalidation_tasks": huggingface_lean_source_revalidation_tasks_manifest[
                "n_tasks"
            ],
            "huggingface_lean_source_revalidation_tasks_ready": huggingface_lean_source_revalidation_tasks_manifest[
                "n_ready"
            ],
            "huggingface_lean_source_revalidation_tasks_blocked": huggingface_lean_source_revalidation_tasks_manifest[
                "n_blocked"
            ],
            "huggingface_lean_source_revalidation_tasks_license_review_required": huggingface_lean_source_revalidation_tasks_manifest[
                "n_license_review_required"
            ],
            "huggingface_lean_source_revalidation_tasks_kernel_verified": huggingface_lean_source_revalidation_tasks_manifest[
                "n_kernel_verified"
            ],
            "huggingface_lean_source_revalidation_tasks_proof_evidence_ready": huggingface_lean_source_revalidation_tasks_manifest[
                "n_proof_evidence_ready"
            ],
            "huggingface_lean_source_revalidation_tasks_proof_evidence_status": huggingface_lean_source_revalidation_tasks_manifest[
                "proof_evidence_status"
            ],
            "huggingface_lean_source_revalidation_prompt_packets": huggingface_lean_source_revalidation_prompt_packets_manifest[
                "n_prompt_packets"
            ],
            "huggingface_lean_source_revalidation_prompt_packets_ready_tasks": huggingface_lean_source_revalidation_prompt_packets_manifest[
                "n_ready_tasks"
            ],
            "huggingface_lean_source_revalidation_prompt_packets_license_review_required": huggingface_lean_source_revalidation_prompt_packets_manifest[
                "n_license_review_required"
            ],
            "huggingface_lean_source_revalidation_prompt_packets_output_contracts": huggingface_lean_source_revalidation_prompt_packets_manifest[
                "n_with_output_contract"
            ],
            "huggingface_lean_source_revalidation_prompt_packets_proof_evidence_status": huggingface_lean_source_revalidation_prompt_packets_manifest[
                "proof_evidence_status"
            ],
            "huggingface_lean_source_revalidation_artifact_validation_rows": huggingface_lean_source_revalidation_artifact_validation_manifest[
                "n_validation_rows"
            ],
            "huggingface_lean_source_revalidation_artifact_validation_responses": huggingface_lean_source_revalidation_artifact_validation_manifest[
                "n_responses"
            ],
            "huggingface_lean_source_revalidation_artifact_validation_awaiting": huggingface_lean_source_revalidation_artifact_validation_manifest[
                "n_awaiting_worker_output"
            ],
            "huggingface_lean_source_revalidation_artifact_validation_contract_ok": huggingface_lean_source_revalidation_artifact_validation_manifest[
                "n_contract_ok"
            ],
            "huggingface_lean_source_revalidation_artifact_validation_kernel_verified_rows": huggingface_lean_source_revalidation_artifact_validation_manifest[
                "n_kernel_verified_rows"
            ],
            "huggingface_lean_source_revalidation_artifact_validation_proof_evidence_ready": huggingface_lean_source_revalidation_artifact_validation_manifest[
                "n_proof_evidence_ready"
            ],
            "huggingface_lean_source_revalidation_artifact_validation_proof_evidence_status": huggingface_lean_source_revalidation_artifact_validation_manifest[
                "proof_evidence_status"
            ],
            "huggingface_lean_source_revalidation_promotion_rows": huggingface_lean_source_revalidation_promotion_queue_manifest[
                "n_promotion_rows"
            ],
            "huggingface_lean_source_revalidation_promotion_ready": huggingface_lean_source_revalidation_promotion_queue_manifest[
                "n_ready_for_promotion"
            ],
            "huggingface_lean_source_revalidation_promotion_awaiting": huggingface_lean_source_revalidation_promotion_queue_manifest[
                "n_awaiting_worker_output"
            ],
            "huggingface_lean_source_revalidation_promotion_blocked": huggingface_lean_source_revalidation_promotion_queue_manifest[
                "n_blocked"
            ],
            "huggingface_lean_source_revalidation_promotion_kernel_verified_rows": huggingface_lean_source_revalidation_promotion_queue_manifest[
                "n_kernel_verified_rows"
            ],
            "huggingface_lean_source_revalidation_promotion_proof_evidence_ready": huggingface_lean_source_revalidation_promotion_queue_manifest[
                "n_proof_evidence_ready"
            ],
            "huggingface_lean_source_revalidation_promotion_proof_evidence_status": huggingface_lean_source_revalidation_promotion_queue_manifest[
                "proof_evidence_status"
            ],
            "huggingface_lean_source_proof_evidence_ready": huggingface_lean_source_manifest[
                "summary"
            ].get("proof_evidence_ready", 0),
            "huggingface_lean_source_use_network": huggingface_lean_source_manifest[
                "sources"
            ].get("use_network", False),
            "lean_rag_source_registry_expansion_all_ok": lean_rag_source_registry_expansion_manifest[
                "all_ok"
            ],
            "lean_rag_source_registry_expansion_stage_ready": lean_rag_source_registry_expansion_manifest[
                "stage_ready"
            ],
            "lean_rag_source_registry_expansion_candidates": lean_rag_source_registry_expansion_manifest[
                "n_candidates"
            ],
            "lean_rag_source_registry_expansion_deferred_candidates": lean_rag_source_registry_expansion_manifest.get(
                "n_deferred_candidates", 0
            ),
            "lean_rag_source_registry_expansion_staged": lean_rag_source_registry_expansion_manifest[
                "n_staged"
            ],
            "lean_rag_source_registry_expansion_invalid": lean_rag_source_registry_expansion_manifest[
                "n_invalid"
            ],
            "lean_rag_source_registry_expansion_coverage_before_present": lean_rag_source_registry_expansion_manifest[
                "target_source_coverage_before"
            ].get("n_present", 0),
            "lean_rag_source_registry_expansion_coverage_after_present": lean_rag_source_registry_expansion_manifest[
                "target_source_coverage_after"
            ].get("n_present", 0),
            "lean_rag_source_registry_expansion_coverage_after_missing": lean_rag_source_registry_expansion_manifest[
                "target_source_coverage_after"
            ].get("n_missing", 0),
            "lean_rag_source_registry_expansion_preflight_apply_ready": lean_rag_source_registry_expansion_preflight_manifest[
                "source_registry_apply_ready"
            ],
            "lean_rag_source_registry_expansion_preflight_external_refresh_ready": lean_rag_source_registry_expansion_preflight_manifest[
                "external_refresh_ready"
            ],
            "lean_rag_source_registry_expansion_preflight_clone_required": lean_rag_source_registry_expansion_preflight_manifest[
                "n_clone_required"
            ],
            "lean_rag_source_registry_expansion_preflight_indexer_unsupported": lean_rag_source_registry_expansion_preflight_manifest[
                "n_indexer_unsupported"
            ],
            "lean_rag_source_registry_expansion_preflight_hard_blockers": lean_rag_source_registry_expansion_preflight_manifest[
                "n_hard_blockers"
            ],
            "lean_rag_source_registry_expansion_apply_ready": lean_rag_source_registry_expansion_apply_manifest[
                "apply_ready"
            ],
            "lean_rag_source_registry_expansion_apply_dry_run": lean_rag_source_registry_expansion_apply_manifest[
                "dry_run"
            ],
            "lean_rag_source_registry_expansion_apply_applied": lean_rag_source_registry_expansion_apply_manifest[
                "applied"
            ],
            "lean_rag_source_registry_expansion_apply_no_staged": lean_rag_source_registry_expansion_apply_manifest.get(
                "no_staged",
                False,
            ),
            "lean_rag_source_registry_expansion_apply_errors": len(
                lean_rag_source_registry_expansion_apply_manifest.get("errors", ())
            ),
            "lean_rag_source_registry_expansion_apply_warnings": len(
                lean_rag_source_registry_expansion_apply_manifest.get("warnings", ())
            ),
            "lean_rag_source_registry_expansion_apply_current_fingerprint_match": (
                bool(
                    lean_rag_source_registry_expansion_apply_manifest.get(
                        "no_staged", False
                    )
                )
                or (
                    lean_rag_source_registry_expansion_apply_manifest.get(
                        "source_registry_fingerprint_before_expected"
                    )
                    == lean_rag_source_registry_expansion_apply_manifest.get(
                        "source_registry_fingerprint_before_actual"
                    )
                )
            ),
            "lean_rag_source_registry_expansion_apply_staged_fingerprint_match": (
                bool(
                    lean_rag_source_registry_expansion_apply_manifest.get(
                        "no_staged", False
                    )
                )
                or (
                    lean_rag_source_registry_expansion_apply_manifest.get(
                        "staged_source_registry_fingerprint_expected"
                    )
                    == lean_rag_source_registry_expansion_apply_manifest.get(
                        "staged_source_registry_fingerprint_actual"
                    )
                )
            ),
            "research_ready_with_gaps": benchmark_manifest["n_ready_with_gaps"],
            "research_simulation_flagged": benchmark_manifest["n_simulation_flagged"],
            "research_formal_blocked": benchmark_manifest["n_formal_blocked"],
            "research_adaptive_mc_rerun_enabled": benchmark_manifest.get("simulation_policy", {}).get(
                "adaptive_mc_rerun",
                False,
            ),
            "research_adaptive_mc_rows": benchmark_manifest.get("simulation_policy", {}).get(
                "adaptive_mc_rows",
                0,
            ),
            "research_adaptive_mc_resolved": benchmark_manifest.get("simulation_policy", {}).get(
                "adaptive_mc_resolved",
                0,
            ),
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
            "algorithm_simulation_stress_adaptive_mc_rerun_enabled": algorithm_simulation_stress_manifest[
                "adaptive_mc_rerun"
            ],
            "algorithm_simulation_stress_adaptive_mc_rows": algorithm_simulation_stress_manifest[
                "adaptive_mc_rows"
            ],
            "algorithm_simulation_stress_adaptive_mc_resolved": algorithm_simulation_stress_manifest[
                "adaptive_mc_resolved"
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
            "research_agent_runtime_audit_requested": research_agent_runtime_audit_manifest[
                "requested"
            ],
            "research_agent_runtime_audit_available": research_agent_runtime_audit_manifest[
                "available"
            ],
            "research_agent_runtime_audit_source": research_agent_runtime_audit_manifest.get(
                "runtime_audit_source", ""
            ),
            "research_agent_runtime_contract_smoke": bool(
                research_agent_runtime_audit_manifest.get("contract_smoke", False)
            ),
            "research_agent_runtime_offline_smoke": bool(
                research_agent_runtime_audit_manifest.get(
                    "offline_runtime_smoke", False
                )
            ),
            "research_agent_runtime_audit_all_ok": research_agent_runtime_audit_manifest[
                "all_ok"
            ],
            "research_agent_runtime_capability_ready_for_full_ai_statistician": research_agent_runtime_audit_manifest[
                "capability_ready_for_full_ai_statistician"
            ],
            "research_agent_runtime_capability_status": research_agent_runtime_audit_manifest[
                "capability_status"
            ],
            "research_agent_runtime_capability_gaps": research_agent_runtime_audit_manifest[
                "capability_gaps"
            ],
            "research_agent_runtime_audit_results": research_agent_runtime_audit_manifest[
                "n_results"
            ],
            "research_agent_runtime_audit_ok": research_agent_runtime_audit_manifest["n_ok"],
            "research_agent_runtime_budget_exhausted_with_pending_next_task": research_agent_runtime_audit_manifest[
                "n_budget_exhausted_with_pending_next_task"
            ],
            "research_agent_runtime_budgeted_continuation_contract_ok": research_agent_runtime_audit_manifest[
                "n_budgeted_continuation_contract_ok"
            ],
            "research_agent_runtime_resumed_from_pending_task": research_agent_runtime_audit_manifest[
                "runtime_resumed_from_pending_task"
            ],
            "research_agent_runtime_architect_enabled": research_agent_runtime_audit_manifest[
                "architect_coordinator_enabled"
            ],
            "research_agent_runtime_topology_ok": research_agent_runtime_audit_manifest[
                "llm_topology_policy_ok"
            ],
            "research_agent_runtime_unsupported_generator_backends": research_agent_runtime_audit_manifest[
                "unsupported_generator_backends_enabled"
            ],
            "research_agent_runtime_critic_reroutes": research_agent_runtime_audit_manifest[
                "n_critic_reroutes"
            ],
            "research_agent_runtime_live_generator_agents_enabled": research_agent_runtime_audit_manifest[
                "n_live_generator_agents_enabled"
            ],
            "research_agent_runtime_architect_deferred_meta_capability_gaps": research_agent_runtime_audit_manifest.get(
                "n_architect_initial_routing_deferred_meta_capability_gaps",
                0,
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gap_owners": research_agent_runtime_audit_manifest.get(
                "architect_initial_routing_deferred_meta_capability_gap_owners",
                {},
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gap_requirement_ids": research_agent_runtime_audit_manifest.get(
                "architect_initial_routing_deferred_meta_capability_gap_requirement_ids",
                [],
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gaps_visible": bool(
                runtime_architect_deferred_meta_scorecard_row.get("passed", True)
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gaps_evidence": str(
                runtime_architect_deferred_meta_scorecard_row.get("evidence", "")
                or ""
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gaps_blocker": str(
                runtime_architect_deferred_meta_scorecard_row.get("blocker", "")
                or ""
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gaps_resolved": bool(
                runtime_architect_deferred_meta_resolved_scorecard_row.get(
                    "passed",
                    not bool(
                        research_agent_runtime_audit_manifest.get(
                            "n_architect_initial_routing_deferred_meta_capability_gaps",
                            0,
                        )
                    ),
                )
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gaps_resolution_evidence": str(
                runtime_architect_deferred_meta_resolved_scorecard_row.get(
                    "evidence",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gaps_resolution_blocker": str(
                runtime_architect_deferred_meta_resolved_scorecard_row.get(
                    "blocker",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned": bool(
                runtime_architect_deferred_meta_replay_scorecard_row.get(
                    "passed",
                    True,
                )
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned_evidence": str(
                runtime_architect_deferred_meta_replay_scorecard_row.get(
                    "evidence",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_architect_deferred_meta_capability_gap_resolution_replay_priority_pinned_blocker": str(
                runtime_architect_deferred_meta_replay_scorecard_row.get(
                    "blocker",
                    "",
                )
                or ""
            ),
            **_research_agent_runtime_exact_semantic_definition_authoring_count_rollup(
                research_agent_runtime_audit_manifest
            ),
            "research_agent_runtime_lean_lsp_mcp_live_calls": research_agent_runtime_audit_manifest[
                "n_lean_lsp_mcp_live_calls"
            ],
            "research_agent_runtime_algorithm_sandbox_executed": research_agent_runtime_audit_manifest[
                "n_algorithm_sandbox_executed"
            ],
            "research_agent_runtime_generated_code_sandbox_executed": research_agent_runtime_audit_manifest[
                "n_generated_code_sandbox_executed"
            ],
            "research_agent_runtime_generated_code_sandbox_failed_then_passed_repair_sequences": research_agent_runtime_audit_manifest[
                "n_generated_code_sandbox_failed_then_passed_repair_sequences"
            ],
            "research_agent_runtime_generated_code_sandbox_metric_gate_failed": research_agent_runtime_audit_manifest[
                "n_generated_code_sandbox_metric_gate_failed"
            ],
            "research_agent_runtime_unsafe_generated_code_rejected": research_agent_runtime_audit_manifest[
                "n_unsafe_generated_code_rejected"
            ],
            "research_agent_runtime_generated_simulation_sandbox_executed": research_agent_runtime_audit_manifest[
                "n_generated_simulation_sandbox_executed"
            ],
            "research_agent_runtime_generated_simulation_sandbox_failed_then_passed_repair_sequences": research_agent_runtime_audit_manifest[
                "n_generated_simulation_sandbox_failed_then_passed_repair_sequences"
            ],
            "research_agent_runtime_generated_simulation_sandbox_metric_gate_failed": research_agent_runtime_audit_manifest[
                "n_generated_simulation_sandbox_metric_gate_failed"
            ],
            "research_agent_runtime_unsafe_generated_simulation_code_rejected": research_agent_runtime_audit_manifest[
                "n_unsafe_generated_simulation_code_rejected"
            ],
            "research_agent_runtime_formalizer_lean_candidate_local_lean_checked": research_agent_runtime_audit_manifest[
                "n_formalizer_lean_candidate_local_lean_checked"
            ],
            "research_agent_runtime_formalizer_lean_candidate_local_lean_compiled": research_agent_runtime_audit_manifest[
                "n_formalizer_lean_candidate_local_lean_compiled"
            ],
            "research_agent_runtime_learning_rows": research_agent_runtime_audit_manifest[
                "n_runtime_learning_rows"
            ],
            "research_agent_runtime_pending_task_memory_rows": research_agent_runtime_audit_manifest[
                "n_runtime_pending_task_memory_rows"
            ],
            "research_agent_runtime_route_critical_target_identity_rows": research_agent_runtime_audit_manifest[
                "n_runtime_route_critical_target_identity_rows"
            ],
            "research_agent_runtime_route_critical_rows_missing_target_ids": research_agent_runtime_audit_manifest[
                "n_runtime_route_critical_rows_missing_target_ids"
            ],
            "research_agent_runtime_route_critical_target_identity_channels": research_agent_runtime_audit_manifest[
                "runtime_route_critical_target_identity_channels"
            ],
            "research_agent_runtime_route_critical_rows_missing_target_ids_sample": research_agent_runtime_audit_manifest[
                "runtime_route_critical_rows_missing_target_ids"
            ],
            "research_agent_runtime_handoff_artifact_missing_feedback_rows": research_agent_runtime_audit_manifest[
                "n_runtime_handoff_artifact_missing_feedback_rows"
            ],
            "research_agent_runtime_handoff_artifact_missing_ids": research_agent_runtime_audit_manifest[
                "runtime_handoff_artifact_missing_ids"
            ],
            "research_agent_runtime_handoff_artifact_missing_owner_subsystems": research_agent_runtime_audit_manifest[
                "runtime_handoff_artifact_missing_owner_subsystems"
            ],
            "research_agent_runtime_learning_memory_inputs": research_agent_runtime_audit_manifest[
                "n_results_with_runtime_learning_memory_input"
            ],
            "research_agent_runtime_learning_memory_input_rows": research_agent_runtime_audit_manifest[
                "n_runtime_learning_memory_input_rows"
            ],
            "research_agent_runtime_capability_gap_routing_inputs": research_agent_runtime_audit_manifest[
                "n_results_with_runtime_capability_gap_routing_input"
            ],
            "research_agent_runtime_capability_gap_routing_input_rows": research_agent_runtime_audit_manifest[
                "n_runtime_capability_gap_routing_input_rows"
            ],
            "research_agent_runtime_capability_gap_routing_input_rows_seen": research_agent_runtime_audit_manifest[
                "n_runtime_capability_gap_routing_input_rows_seen"
            ],
            "research_agent_runtime_capability_gap_routing_input_retention_policy": research_agent_runtime_audit_manifest[
                "runtime_capability_gap_routing_input_retention_policy"
            ],
            "research_agent_runtime_capability_gap_routing_input_retention_selection_counts": research_agent_runtime_audit_manifest.get(
                "runtime_capability_gap_routing_input_retention_selection_counts",
                {},
            ),
            "research_agent_runtime_capability_gap_routing_input_requirement_ids": research_agent_runtime_audit_manifest.get(
                "runtime_capability_gap_routing_input_requirement_ids",
                [],
            ),
            "research_agent_runtime_capability_gap_routing_input_priority_pinned_requirement_ids": research_agent_runtime_audit_manifest.get(
                "runtime_capability_gap_routing_input_priority_pinned_requirement_ids",
                [],
            ),
            "research_agent_runtime_capability_gap_routing_input_owner_subsystems": research_agent_runtime_audit_manifest.get(
                "runtime_capability_gap_routing_input_owner_subsystems",
                {},
            ),
            "research_agent_runtime_capability_gap_routing_followup_commands": _research_agent_runtime_capability_gap_routing_followup_commands(
                research_agent_runtime_audit_manifest
            ),
            "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection": research_agent_runtime_audit_manifest.get(
                "n_runtime_capability_gap_routing_input_rows_missing_retention_selection",
                0,
            ),
            "research_agent_runtime_capability_gap_routing_input_rows_missing_retention_selection_boundary": research_agent_runtime_audit_manifest.get(
                "n_runtime_capability_gap_routing_input_rows_missing_retention_selection_boundary",
                0,
            ),
            "research_agent_runtime_cross_task_theorem_family_rows": research_agent_runtime_audit_manifest.get(
                "n_runtime_cross_task_theorem_family_rows",
                0,
            ),
            "research_agent_runtime_cross_task_theorem_family_rows_with_explicit_family": research_agent_runtime_audit_manifest.get(
                "n_runtime_cross_task_theorem_family_rows_with_explicit_family",
                0,
            ),
            "research_agent_runtime_cross_task_theorem_family_rows_with_target_bound_kernel": research_agent_runtime_audit_manifest.get(
                "n_runtime_cross_task_theorem_family_rows_with_target_bound_kernel",
                0,
            ),
            "research_agent_runtime_cross_task_theorem_family_rows_with_open_formal_gaps": research_agent_runtime_audit_manifest.get(
                "n_runtime_cross_task_theorem_family_rows_with_open_formal_gaps",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_routing_contract_complete": research_agent_runtime_audit_manifest[
                "runtime_pseudo_formal_block_routing_contract_complete"
            ],
            "research_agent_runtime_pseudo_formal_block_routing_rows": research_agent_runtime_audit_manifest[
                "n_runtime_pseudo_formal_block_routing_rows"
            ],
            "research_agent_runtime_pseudo_formal_block_routing_effective_rows": research_agent_runtime_audit_manifest.get(
                "n_runtime_pseudo_formal_block_routing_effective_rows",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_routing_diagnostic_rows": research_agent_runtime_audit_manifest.get(
                "n_runtime_pseudo_formal_block_routing_diagnostic_rows",
                0,
            ),
            "research_agent_runtime_pseudo_formalization_required_formalization_manifests": research_agent_runtime_audit_manifest.get(
                "n_runtime_pseudo_formalization_required_formalization_manifests",
                0,
            ),
            "research_agent_runtime_pseudo_formalization_required_missing_routing_rows": research_agent_runtime_audit_manifest[
                "n_runtime_pseudo_formalization_required_missing_routing_rows"
            ],
            "research_agent_runtime_pseudo_formalization_required_manifest_ids": research_agent_runtime_audit_manifest.get(
                "runtime_pseudo_formalization_required_manifest_ids",
                [],
            ),
            "research_agent_runtime_pseudo_formalization_required_missing_routing_manifest_ids": research_agent_runtime_audit_manifest.get(
                "runtime_pseudo_formalization_required_missing_routing_manifest_ids",
                [],
            ),
            "research_agent_runtime_pseudo_formalization_routed_manifest_ids": research_agent_runtime_audit_manifest.get(
                "runtime_pseudo_formalization_routed_manifest_ids",
                [],
            ),
            "research_agent_runtime_pseudo_formalization_effective_routed_manifest_ids": research_agent_runtime_audit_manifest.get(
                "runtime_pseudo_formalization_effective_routed_manifest_ids",
                [],
            ),
            "research_agent_runtime_pseudo_formalization_routed_manifests": research_agent_runtime_audit_manifest.get(
                "n_runtime_pseudo_formalization_routed_manifests",
                0,
            ),
            "research_agent_runtime_pseudo_formalization_effective_routed_manifests": research_agent_runtime_audit_manifest.get(
                "n_runtime_pseudo_formalization_effective_routed_manifests",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_routing_row_kinds": research_agent_runtime_audit_manifest.get(
                "runtime_pseudo_formal_block_routing_row_kinds",
                {},
            ),
            "research_agent_runtime_pseudo_formal_block_routing_diagnostic_row_kinds": research_agent_runtime_audit_manifest.get(
                "runtime_pseudo_formal_block_routing_diagnostic_row_kinds",
                {},
            ),
            "research_agent_runtime_pseudo_formal_block_routing_effective_target_lanes": research_agent_runtime_audit_manifest.get(
                "runtime_pseudo_formal_block_routing_effective_target_lanes",
                {},
            ),
            "research_agent_runtime_pseudo_formal_block_routing_diagnostic_target_lanes": research_agent_runtime_audit_manifest.get(
                "runtime_pseudo_formal_block_routing_diagnostic_target_lanes",
                {},
            ),
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_method_lineage": research_agent_runtime_audit_manifest[
                "n_runtime_pseudo_formal_block_routing_rows_missing_method_lineage"
            ],
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_scope_parent": research_agent_runtime_audit_manifest[
                "n_runtime_pseudo_formal_block_routing_rows_missing_scope_parent"
            ],
            "research_agent_runtime_pseudo_formal_block_routing_rows_invalid_scope_parent": research_agent_runtime_audit_manifest[
                "n_runtime_pseudo_formal_block_routing_rows_invalid_scope_parent"
            ],
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_inherited_scope": research_agent_runtime_audit_manifest[
                "n_runtime_pseudo_formal_block_routing_rows_missing_inherited_scope"
            ],
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_row_kind": research_agent_runtime_audit_manifest.get(
                "n_runtime_pseudo_formal_block_routing_rows_missing_row_kind",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_routing_rows_missing_or_wrong_nonproof_boundary": research_agent_runtime_audit_manifest[
                "n_runtime_pseudo_formal_block_routing_rows_missing_or_wrong_nonproof_boundary"
            ],
            "research_agent_runtime_pseudo_formal_block_routing_issues": research_agent_runtime_audit_manifest[
                "runtime_pseudo_formal_block_routing_contract_issues"
            ],
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_attached": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_attached",
                False,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_manifest_path": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_manifest_path",
                "",
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_capability_evidence_ok": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_capability_evidence_ok",
                False,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_live_generator": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_live_generator",
                False,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_static_or_fixture_only": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_static_or_fixture_only",
                True,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_fixture_plumbing_ok": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_fixture_plumbing_ok",
                False,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_prompt_packets": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_prompt_packets",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_valid_responses": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_valid_responses",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_runtime_learning_rows": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_runtime_learning_rows",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_paths": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_source_runtime_learning_jsonl_paths",
                [],
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_jsonl_path_count": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_source_runtime_learning_jsonl_path_count",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_reference_dir": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_source_runtime_learning_lineage_reference_dir",
                "",
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_source_runtime_learning_lineage_ok": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_source_runtime_learning_lineage_ok",
                False,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_accepted_blocks": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_accepted_blocks",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_failed_blocks": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_failed_blocks",
                0,
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_provider": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_provider_name",
                "",
            ),
            "research_agent_runtime_pseudo_formal_block_verifier_component_gate_backend_provider": research_agent_runtime_audit_manifest.get(
                "internal_pseudo_formal_block_verifier_eval_backend_provider_name",
                "",
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attached": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_attached",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_manifest_path": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_manifest_path",
                "",
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_capability_evidence_ok",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_live_generator": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_live_generator",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_static_or_fixture_only": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_static_or_fixture_only",
                True,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_fixture_plumbing_ok": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_fixture_plumbing_ok",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_pseudo_formal_packets",
                0,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_work_order_rows": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_work_order_rows",
                0,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_routable_work_order_rows",
                0,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_row_kinds": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_routable_row_kinds",
                [],
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_routable_target_lanes": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_routable_target_lanes",
                [],
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_nonproof_boundary_preserved",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_raw_model_output_written": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_raw_model_output_written",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_lane_present",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_proof_evidence_status_ok",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_no_theorem_proof_claim",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attachment_gate_recomputed": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_attachment_gate_recomputed",
                False,
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_attachment_gate_requirements": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_attachment_gate_requirements",
                {},
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_provider": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_provider_name",
                "",
            ),
            "research_agent_runtime_formalizer_pseudo_formal_packet_component_gate_backend_provider": research_agent_runtime_audit_manifest.get(
                "internal_formalizer_pseudo_formal_packet_eval_backend_provider_name",
                "",
            ),
            "research_agent_runtime_pseudo_formal_semantic_primitive_work_orders": research_agent_runtime_audit_manifest.get(
                "n_runtime_source_theorem_semantic_primitive_work_orders_from_pseudo_formal",
                0,
            ),
            "research_agent_runtime_pseudo_formal_exact_semantic_definition_work_orders": research_agent_runtime_audit_manifest.get(
                "n_runtime_source_theorem_exact_semantic_definition_work_orders_from_pseudo_formal",
                0,
            ),
            "research_agent_runtime_pseudo_formal_exact_semantic_definition_lean_environment_repair_tasks": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_semantic_definition_lean_environment_repair_executor_n_tasks_from_pseudo_formal",
                0,
            ),
            "research_agent_runtime_pseudo_formal_exact_semantic_definition_lean_environment_repair_results": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_semantic_definition_lean_environment_repair_executor_n_results_from_pseudo_formal",
                0,
            ),
            "research_agent_runtime_pseudo_formal_late_exact_semantic_definition_lean_environment_repair_tasks": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_semantic_definition_late_lean_environment_repair_executor_n_tasks_from_pseudo_formal",
                0,
            ),
            "research_agent_runtime_pseudo_formal_late_exact_semantic_definition_lean_environment_repair_results": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_semantic_definition_late_lean_environment_repair_executor_n_results_from_pseudo_formal",
                0,
            ),
            "research_agent_runtime_pseudo_formal_exact_semantic_definition_lean_environment_repair_ready_for_proof_body": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_semantic_definition_lean_environment_repair_executor_source_theorem_ready_for_exact_proof_body",
                False,
            ),
            "research_agent_runtime_pseudo_formal_late_exact_semantic_definition_lean_environment_repair_ready_for_proof_body": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_semantic_definition_late_lean_environment_repair_executor_source_theorem_ready_for_exact_proof_body",
                False,
            ),
            "research_agent_runtime_pseudo_formal_semantic_primitives_reach_source_semantic_bridge": bool(
                runtime_pf_semantic_bridge_scorecard_row.get("passed", True)
            ),
            "research_agent_runtime_pseudo_formal_semantic_bridge_evidence": str(
                runtime_pf_semantic_bridge_scorecard_row.get("evidence", "") or ""
            ),
            "research_agent_runtime_pseudo_formal_semantic_bridge_blocker": str(
                runtime_pf_semantic_bridge_scorecard_row.get("blocker", "") or ""
            ),
            "research_agent_runtime_pseudo_formal_exact_semantic_definitions_reach_exact_definition_source_lookup": bool(
                runtime_pf_exact_semantic_source_lookup_scorecard_row.get(
                    "passed",
                    True,
                )
            ),
            "research_agent_runtime_pseudo_formal_exact_semantic_definition_source_lookup_evidence": str(
                runtime_pf_exact_semantic_source_lookup_scorecard_row.get(
                    "evidence",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_pseudo_formal_exact_semantic_definition_source_lookup_blocker": str(
                runtime_pf_exact_semantic_source_lookup_scorecard_row.get(
                    "blocker",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_source_semantic_proofengineer_bridge_requested": research_agent_runtime_audit_manifest.get(
                "source_semantic_proofengineer_bridge_requested",
                False,
            ),
            "research_agent_runtime_source_semantic_proofengineer_bridge_ran": research_agent_runtime_audit_manifest.get(
                "source_semantic_proofengineer_bridge_ran",
                False,
            ),
            "research_agent_runtime_source_semantic_proofengineer_bridge_proof_evidence_status": research_agent_runtime_audit_manifest.get(
                "source_semantic_proofengineer_bridge_proof_evidence_status",
                "",
            ),
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_ran": research_agent_runtime_audit_manifest.get(
                "source_theorem_formal_environment_proof_body_executor_ran",
                False,
            ),
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_local_lean_requested": research_agent_runtime_audit_manifest.get(
                "source_theorem_formal_environment_proof_body_executor_local_lean_requested",
                False,
            ),
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_result_rows": research_agent_runtime_audit_manifest.get(
                "source_theorem_formal_environment_proof_body_executor_n_result_rows",
                0,
            ),
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_local_lean_checked": research_agent_runtime_audit_manifest.get(
                "source_theorem_formal_environment_proof_body_executor_n_local_lean_checked",
                0,
            ),
            "research_agent_runtime_source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified": research_agent_runtime_audit_manifest.get(
                "source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified",
                0,
            ),
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_ran": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_proof_body_repair_executor_ran",
                False,
            ),
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_result_rows": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_proof_body_repair_executor_n_result_rows",
                0,
            ),
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_local_lean_checked": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_proof_body_repair_executor_n_local_lean_checked",
                0,
            ),
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached",
                0,
            ),
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached_with_semantic_blockers": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_reached_with_semantic_blockers",
                0,
            ),
            "research_agent_runtime_source_theorem_exact_proof_body_repair_executor_n_source_theorem_kernel_verified": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_proof_body_repair_executor_n_source_theorem_kernel_verified",
                0,
            ),
            "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_ran": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_ran",
                False,
            ),
            "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_result_rows": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_result_rows",
                0,
            ),
            "research_agent_runtime_source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_source_theorem_kernel_verified": research_agent_runtime_audit_manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_verifier_approved_proof_body_recheck_executor_n_source_theorem_kernel_verified",
                0,
            ),
            "research_agent_runtime_source_theorem_proof_body_result_row_count": research_agent_runtime_audit_manifest.get(
                "source_theorem_proof_body_result_row_count",
                0,
            ),
            "research_agent_runtime_source_theorem_proof_body_goal_reached_evidence_count": research_agent_runtime_audit_manifest.get(
                "source_theorem_proof_body_goal_reached_evidence_count",
                0,
            ),
            "research_agent_runtime_source_theorem_proof_body_goal_reached_with_semantic_blockers": research_agent_runtime_audit_manifest.get(
                "source_theorem_proof_body_goal_reached_with_semantic_blockers",
                0,
            ),
            "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_present": bool(
                runtime_source_theorem_signature_probe_scorecard_row
            ),
            "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_ok": bool(
                runtime_source_theorem_signature_probe_scorecard_row.get(
                    "passed",
                    False,
                )
            ),
            "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_evidence": str(
                runtime_source_theorem_signature_probe_scorecard_row.get(
                    "evidence",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_source_theorem_signature_probe_reached_proof_body_scorecard_blocker": str(
                runtime_source_theorem_signature_probe_scorecard_row.get(
                    "blocker",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_source_theorem_kernel_verified_count": research_agent_runtime_audit_manifest.get(
                "source_theorem_kernel_verified_count",
                0,
            ),
            "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_present": bool(
                runtime_source_theorem_proof_body_executor_scorecard_row
            ),
            "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_ok": bool(
                runtime_source_theorem_proof_body_executor_scorecard_row.get(
                    "passed",
                    False,
                )
            ),
            "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_evidence": str(
                runtime_source_theorem_proof_body_executor_scorecard_row.get(
                    "evidence",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_source_theorem_proof_body_executor_ran_scorecard_blocker": str(
                runtime_source_theorem_proof_body_executor_scorecard_row.get(
                    "blocker",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_evidence_present": bool(
                runtime_source_theorem_proof_body_same_lane_scorecard_row
            ),
            "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_evidence": bool(
                runtime_source_theorem_proof_body_same_lane_scorecard_row.get(
                    "passed",
                    False,
                )
            ),
            "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_scorecard_evidence": str(
                runtime_source_theorem_proof_body_same_lane_scorecard_row.get(
                    "evidence",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_source_theorem_proof_body_same_lane_verifier_scorecard_blocker": str(
                runtime_source_theorem_proof_body_same_lane_scorecard_row.get(
                    "blocker",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_formal_gap_planner_handoff_rows": research_agent_runtime_audit_manifest.get(
                "n_runtime_formal_gap_planner_handoff_rows",
                0,
            ),
            "research_agent_runtime_formal_gap_planner_handoff_rows_missing_execution_context": research_agent_runtime_audit_manifest.get(
                "n_runtime_formal_gap_planner_handoff_rows_missing_execution_context",
                0,
            ),
            "research_agent_runtime_formal_gap_planner_executable_handoff_context_complete": bool(
                runtime_formal_gap_planner_context_scorecard_row.get("passed", True)
            ),
            "research_agent_runtime_formal_gap_planner_executable_handoff_context_evidence": str(
                runtime_formal_gap_planner_context_scorecard_row.get("evidence", "")
                or ""
            ),
            "research_agent_runtime_formal_gap_planner_executable_handoff_context_blocker": str(
                runtime_formal_gap_planner_context_scorecard_row.get("blocker", "")
                or ""
            ),
            "research_agent_runtime_formal_gap_planner_live_route_planner_followthrough": bool(
                runtime_formal_gap_planner_followthrough_scorecard_row.get(
                    "passed",
                    True,
                )
            ),
            "research_agent_runtime_formal_gap_planner_live_route_planner_followthrough_evidence": str(
                runtime_formal_gap_planner_followthrough_scorecard_row.get(
                    "evidence",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_formal_gap_planner_live_route_planner_followthrough_blocker": str(
                runtime_formal_gap_planner_followthrough_scorecard_row.get(
                    "blocker",
                    "",
                )
                or ""
            ),
            "research_agent_runtime_formal_gap_planner_live_route_planner_invocations": research_agent_runtime_audit_manifest.get(
                "n_runtime_formalization_gap_planner_live_route_planner_invocations",
                0,
            ),
            "research_agent_runtime_formal_gap_planner_live_route_planner_response_contract_ok": research_agent_runtime_audit_manifest.get(
                "n_runtime_formalization_gap_planner_live_route_planner_response_contract_ok",
                0,
            ),
            "research_agent_runtime_formal_gap_planner_live_route_planner_target_prover_replay_all_ok": research_agent_runtime_audit_manifest.get(
                "n_runtime_formalization_gap_planner_live_route_planner_target_prover_replay_all_ok",
                0,
            ),
            "research_agent_runtime_formal_gap_planner_target_prover_replay_route_revision_proposals": research_agent_runtime_audit_manifest.get(
                "n_runtime_formalization_gap_planner_live_route_planner_target_prover_replay_route_revision_proposals",
                0,
            ),
            "research_agent_runtime_formal_gap_planner_target_prover_replay_route_revision_complete_feedback_proposal_ids": research_agent_runtime_audit_manifest.get(
                "n_runtime_target_prover_replay_route_revision_complete_feedback_proposal_ids",
                0,
            ),
            "research_agent_runtime_problem_analysis": research_agent_runtime_audit_manifest[
                "n_results_with_problem_analysis"
            ],
            "research_agent_runtime_stat_knowledge_bank": research_agent_runtime_audit_manifest[
                "n_results_with_stat_knowledge_bank_plan"
            ],
            "research_agent_runtime_literature_fair_comparison": research_agent_runtime_audit_manifest[
                "n_results_with_literature_fair_comparison_plan"
            ],
            "research_agent_runtime_kernel_verified_subclaims": research_agent_runtime_audit_manifest[
                "n_kernel_verified_subclaims"
            ],
            "research_agent_runtime_has_real_kernel_evidence": research_agent_runtime_audit_manifest[
                "has_real_kernel_evidence"
            ],
            "research_agent_runtime_results_with_real_kernel_evidence": research_agent_runtime_audit_manifest[
                "n_results_with_real_kernel_evidence"
            ],
            "research_agent_runtime_real_kernel_verified_subclaims": research_agent_runtime_audit_manifest[
                "n_real_kernel_verified_subclaims"
            ],
            "research_agent_runtime_non_real_kernel_verified_subclaims": research_agent_runtime_audit_manifest[
                "n_non_real_kernel_verified_subclaims"
            ],
            "research_agent_runtime_kernel_verified_verifiers": research_agent_runtime_audit_manifest[
                "kernel_verified_verifiers"
            ],
            "research_agent_runtime_formal_gaps": research_agent_runtime_audit_manifest[
                "n_formal_gaps"
            ],
            "research_agent_runtime_registered_proof_bank_obligation_candidates": research_agent_runtime_audit_manifest[
                "n_registered_proof_bank_obligation_candidates"
            ],
            "research_agent_runtime_memory_prioritized_proof_obligations": research_agent_runtime_audit_manifest[
                "n_memory_prioritized_proof_obligations"
            ],
            "research_agent_runtime_memory_off_catalog_proof_obligations": research_agent_runtime_audit_manifest[
                "n_memory_off_catalog_proof_obligations"
            ],
            "research_agent_runtime_memory_rejected_proof_obligations": research_agent_runtime_audit_manifest[
                "n_memory_rejected_proof_obligations"
            ],
            "research_agent_runtime_llm_requested_proof_obligations": research_agent_runtime_audit_manifest[
                "n_llm_requested_proof_obligations"
            ],
            "research_agent_runtime_llm_off_catalog_proof_obligations": research_agent_runtime_audit_manifest[
                "n_llm_off_catalog_proof_obligations"
            ],
            "research_agent_runtime_llm_rejected_proof_obligations": research_agent_runtime_audit_manifest[
                "n_llm_rejected_proof_obligations"
            ],
            "proofs_verified": proof_manifest["n_verified"],
            "proofs_kernel_verified": proof_manifest["n_kernel_verified"],
            "proofs_non_kernel_verified": proof_manifest["n_non_kernel_verified"],
            "proofs_all_kernel_verified": proof_manifest["all_kernel_verified"],
            "proof_verification_strength": proof_manifest["verification_strength"],
            "proofs_total": proof_manifest["n_obligations"],
            "kernel_smoke_proof_audit_enabled": kernel_smoke_manifest is not None,
            "kernel_smoke_proof_audit_ids": kernel_smoke_selected_ids,
            "kernel_smoke_proof_audit_explicit_ids": list(config.kernel_smoke_ids),
            "kernel_smoke_proof_audit_auto_ids": kernel_smoke_auto_ids,
            "kernel_smoke_from_actions": config.kernel_smoke_from_actions,
            "kernel_smoke_proof_audit_verified": (
                int(kernel_smoke_manifest["n_verified"]) if kernel_smoke_manifest else 0
            ),
            "kernel_smoke_proof_audit_kernel_verified": (
                int(kernel_smoke_manifest["n_kernel_verified"]) if kernel_smoke_manifest else 0
            ),
            "kernel_smoke_proof_audit_total": (
                int(kernel_smoke_manifest["n_obligations"]) if kernel_smoke_manifest else 0
            ),
            "kernel_smoke_proof_audit_all_kernel_verified": (
                bool(kernel_smoke_manifest["all_kernel_verified"]) if kernel_smoke_manifest else False
            ),
            "kernel_smoke_proof_audit_verifier": (
                str(kernel_smoke_manifest["verifier"]) if kernel_smoke_manifest else ""
            ),
            "kernel_smoke_proof_audit_strength": (
                str(kernel_smoke_manifest["verification_strength"]) if kernel_smoke_manifest else ""
            ),
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
            "proof_search_kernel_rerun_local_lean_verified": proof_search_kernel_rerun_local_lean_manifest[
                "n_kernel_verified"
            ],
            "proof_search_kernel_rerun_local_lean_total": proof_search_kernel_rerun_local_lean_manifest[
                "n_obligations"
            ],
            "proof_search_kernel_rerun_local_lean_verifier": proof_search_kernel_rerun_local_lean_manifest[
                "verifier"
            ],
            "proof_search_kernel_rerun_queue_items": proof_search_kernel_rerun_queue_manifest[
                "n_queue_rows"
            ],
            "proof_search_kernel_rerun_queue_ready": proof_search_kernel_rerun_queue_manifest[
                "n_ready_for_local_lean_or_axle"
            ],
            "proof_search_kernel_rerun_queue_blocked": proof_search_kernel_rerun_queue_manifest[
                "n_blocked_missing_selected_proof_body"
            ],
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
            "proof_search_retrieval_no_registered_ablation_solved_delta": proof_search_retrieval_no_registered_ablation_manifest[
                "solved_delta"
            ],
            "proof_search_retrieval_no_registered_ablation_candidate_delta": proof_search_retrieval_no_registered_ablation_manifest[
                "formal_source_candidate_delta"
            ],
            "proof_search_retrieval_no_registered_ablation_node_delta": proof_search_retrieval_no_registered_ablation_manifest[
                "nodes_expanded_delta"
            ],
            "proof_search_retrieval_no_registered_ablation_no_solved_regression": proof_search_retrieval_no_registered_ablation_manifest[
                "no_solved_regression"
            ],
            "proof_search_retrieval_no_registered_ablation_enhanced_all_solved": proof_search_retrieval_no_registered_ablation_manifest[
                "enhanced_all_solved"
            ],
            "proof_search_retrieval_no_registered_ablation_include_registered_proof": proof_search_retrieval_no_registered_ablation_manifest[
                "include_registered_proof"
            ],
            "proof_search_retrieval_no_registered_ablation_baseline_solved": proof_search_retrieval_no_registered_ablation_manifest[
                "baseline"
            ]["n_solved"],
            "proof_search_retrieval_no_registered_ablation_enhanced_solved": proof_search_retrieval_no_registered_ablation_manifest[
                "enhanced"
            ]["n_solved"],
            "proof_search_retrieval_no_registered_ablation_baseline_candidates": proof_search_retrieval_no_registered_ablation_manifest[
                "baseline"
            ]["formal_source_candidates_total"],
            "proof_search_retrieval_no_registered_ablation_enhanced_candidates": proof_search_retrieval_no_registered_ablation_manifest[
                "enhanced"
            ]["formal_source_candidates_total"],
            "proof_search_retrieval_no_registered_ablation_lean_rag_dependency_graph_enabled": proof_search_retrieval_no_registered_ablation_manifest[
                "lean_rag_dependency_graph_enabled"
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
            "formalization_targets_exact_proof_bank_resolved": formalization_target_manifest[
                "n_exact_proof_bank_resolved"
            ],
            "formalization_targets_assumption_interface": formalization_target_manifest[
                "n_assumption_interface_targets"
            ],
            "formalization_targets_unresolved": formalization_target_manifest["n_unresolved_targets"],
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
            "proof_bank_expansion_reuse_exact_proof_bank_obligation": proof_bank_expansion_manifest[
                "n_reuse_exact_proof_bank_obligation"
            ],
            "proof_bank_expansion_compose_existing_bridge_chain": proof_bank_expansion_manifest[
                "n_compose_existing_bridge_chain"
            ],
            "proof_bank_expansion_add_minimal_wrapper": proof_bank_expansion_manifest[
                "n_add_minimal_wrapper"
            ],
            "proof_bank_expansion_design_bridge_lemma": proof_bank_expansion_manifest[
                "n_design_bridge_lemma"
            ],
            "proof_bank_expansion_formalize_assumption_interface": proof_bank_expansion_manifest[
                "n_formalize_assumption_interface"
            ],
            "proof_bank_expansion_design_from_first_principles": proof_bank_expansion_manifest[
                "n_design_from_first_principles"
            ],
            "proof_bank_actions": proof_bank_action_manifest["n_actions"],
            "proof_bank_actions_ok": proof_bank_action_manifest["n_ok"],
            "proof_bank_actions_reuse_exact_proof_bank_obligation": proof_bank_action_manifest[
                "n_reuse_exact_proof_bank_obligation"
            ],
            "proof_bank_actions_compose_existing_bridge_chain": proof_bank_action_manifest[
                "n_compose_existing_bridge_chain"
            ],
            "proof_bank_actions_add_minimal_wrapper": proof_bank_action_manifest[
                "n_add_minimal_wrapper"
            ],
            "proof_bank_actions_design_bridge_lemma": proof_bank_action_manifest[
                "n_design_bridge_lemma"
            ],
            "proof_bank_actions_formalize_assumption_interface": proof_bank_action_manifest[
                "n_formalize_assumption_interface"
            ],
            "proof_bank_actions_design_from_first_principles": proof_bank_action_manifest[
                "n_design_from_first_principles"
            ],
            "assumption_interfaces": assumption_interface_manifest["n_interfaces"],
            "assumption_interfaces_ok": assumption_interface_manifest["n_ok"],
            "assumption_interfaces_local_lean_checked": assumption_interface_manifest[
                "n_local_lean_checked"
            ],
            "assumption_interfaces_local_lean_compiled": assumption_interface_manifest[
                "n_local_lean_compiled"
            ],
            "assumption_interfaces_all_local_lean_compiled": assumption_interface_manifest[
                "all_local_lean_compiled"
            ],
            "formalization_delta_plan_rows": formalization_delta_manifest["n_plan_rows"],
            "formalization_delta_plan_ok": formalization_delta_manifest["n_ok"],
            "formalization_delta_plan_total_estimated_cost": formalization_delta_manifest[
                "total_estimated_cost"
            ],
            "formalization_delta_graph_nodes": formalization_delta_manifest["dependency_graph_nodes"],
            "formalization_delta_graph_edges": formalization_delta_manifest["dependency_graph_edges"],
            "formalization_delta_graph_problem_class_nodes": formalization_delta_manifest[
                "dependency_graph_problem_class_nodes"
            ],
            "formalization_delta_graph_theorem_goal_nodes": formalization_delta_manifest[
                "dependency_graph_theorem_goal_nodes"
            ],
            "formalization_delta_graph_theorem_skeleton_nodes": formalization_delta_manifest[
                "dependency_graph_theorem_skeleton_nodes"
            ],
            "formalization_delta_graph_import_nodes": formalization_delta_manifest[
                "dependency_graph_import_nodes"
            ],
            "formalization_delta_graph_informal_proof_step_nodes": formalization_delta_manifest[
                "dependency_graph_informal_proof_step_nodes"
            ],
            "formalization_delta_graph_goal_to_primitive_edges": formalization_delta_manifest[
                "dependency_graph_goal_to_primitive_edges"
            ],
            "formalization_delta_graph_goal_to_skeleton_edges": formalization_delta_manifest[
                "dependency_graph_goal_to_skeleton_edges"
            ],
            "formalization_delta_graph_skeleton_to_proof_step_edges": formalization_delta_manifest[
                "dependency_graph_skeleton_to_proof_step_edges"
            ],
            "formalization_delta_theorem_routes": formalization_delta_manifest[
                "n_theorem_formalization_routes"
            ],
            "formalization_delta_theorem_routes_with_informal_steps": formalization_delta_manifest[
                "n_theorem_routes_with_informal_steps"
            ],
            "formalization_delta_theorem_routes_with_reuse_candidates": formalization_delta_manifest[
                "n_theorem_routes_with_reuse_candidates"
            ],
            "formalization_delta_theorem_routes_requiring_new_theory": formalization_delta_manifest[
                "n_theorem_routes_requiring_new_theory"
            ],
            "formalization_delta_plan_low_cost_existing_reuse": formalization_delta_manifest[
                "n_low_cost_existing_reuse"
            ],
            "formalization_delta_plan_medium_cost_bridge_or_wrapper": formalization_delta_manifest[
                "n_medium_cost_bridge_or_wrapper"
            ],
            "formalization_delta_plan_high_cost_new_theory": formalization_delta_manifest[
                "n_high_cost_new_theory"
            ],
            "formal_verifier_queue_items": formal_verifier_queue_manifest["n_items"],
            "formal_verifier_queue_ok": formal_verifier_queue_manifest["n_ok"],
            "formal_verifier_queue_high_priority": formal_verifier_queue_manifest["n_high_priority"],
            "formal_verifier_queue_reuse_or_composition": formal_verifier_queue_manifest[
                "n_reuse_or_composition"
            ],
            "formal_verifier_queue_bridge_or_wrapper": formal_verifier_queue_manifest[
                "n_bridge_or_wrapper"
            ],
            "formal_verifier_queue_requires_new_theory": formal_verifier_queue_manifest[
                "n_requires_new_theory"
            ],
            "formal_verifier_queue_routes_with_no_registered_rag_lift": formal_verifier_queue_manifest[
                "n_routes_with_no_registered_rag_lift"
            ],
            "formal_verifier_queue_related_proof_obligations": formal_verifier_queue_manifest[
                "n_related_proof_obligations"
            ],
            "formal_verifier_queue_rows_with_attempt_history": formal_verifier_queue_manifest[
                "n_rows_with_attempt_history"
            ],
            "formal_verifier_queue_rows_with_negative_attempt_history": formal_verifier_queue_manifest[
                "n_rows_with_negative_attempt_history"
            ],
            "formal_verifier_queue_rows_with_kernel_attempt_history": formal_verifier_queue_manifest[
                "n_rows_with_kernel_attempt_history"
            ],
            "formal_verifier_queue_rows_with_proof_search_solution": formal_verifier_queue_manifest[
                "n_rows_with_proof_search_solution"
            ],
            "formal_verifier_queue_proof_attempt_positive": formal_verifier_queue_manifest[
                "n_proof_attempt_positive"
            ],
            "formal_verifier_queue_proof_attempt_negative": formal_verifier_queue_manifest[
                "n_proof_attempt_negative"
            ],
            "formal_verifier_queue_proof_attempt_kernel_verified": formal_verifier_queue_manifest[
                "n_proof_attempt_kernel_verified"
            ],
            "formal_verifier_queue_proof_search_solved": formal_verifier_queue_manifest[
                "n_proof_search_solved"
            ],
            "formal_verifier_queue_proof_search_unsolved": formal_verifier_queue_manifest[
                "n_proof_search_unsolved"
            ],
            "formal_verifier_queue_proof_search_kernel_verified": formal_verifier_queue_manifest[
                "n_proof_search_kernel_verified"
            ],
            "formal_verifier_queue_max_dependency_graph_depth": formal_verifier_queue_manifest[
                "max_dependency_graph_depth"
            ],
            "formal_verifier_queue_max_import_cone_size": formal_verifier_queue_manifest[
                "max_import_cone_size"
            ],
            "formal_verifier_queue_rows_with_local_or_proof_bank_source_trust": formal_verifier_queue_manifest[
                "n_rows_with_local_or_proof_bank_source_trust"
            ],
            "formal_verifier_queue_semantic_strong": formal_verifier_queue_manifest[
                "n_rows_semantic_strong"
            ],
            "formal_verifier_queue_semantic_supported": formal_verifier_queue_manifest[
                "n_rows_semantic_supported"
            ],
            "formal_verifier_queue_semantic_needs_review": formal_verifier_queue_manifest[
                "n_rows_semantic_needs_review"
            ],
            "formal_verifier_queue_mean_semantic_faithfulness_score": formal_verifier_queue_manifest[
                "mean_semantic_faithfulness_score"
            ],
            "formal_verifier_queue_rows_with_kernel_smoke_overlap": formal_verifier_queue_manifest[
                "n_rows_with_kernel_smoke_overlap"
            ],
            "formal_verifier_queue_rows_source_trust_kernel_calibrated": formal_verifier_queue_manifest[
                "n_rows_source_trust_kernel_calibrated"
            ],
            "formal_verifier_queue_kernel_smoke_related_obligations": formal_verifier_queue_manifest[
                "n_kernel_smoke_related_obligations"
            ],
            "formal_verifier_queue_kernel_smoke_related_verified": formal_verifier_queue_manifest[
                "n_kernel_smoke_related_verified"
            ],
            "formal_verifier_queue_no_registered_rag_candidate_delta": formal_verifier_queue_manifest[
                "no_registered_rag_candidate_delta"
            ],
            "formal_verifier_queue_no_registered_rag_solved_delta": formal_verifier_queue_manifest[
                "no_registered_rag_solved_delta"
            ],
            "formal_verifier_queue_kernel_smoke_kernel_verified": formal_verifier_queue_manifest[
                "kernel_smoke_kernel_verified"
            ],
            "formal_verifier_queue_kernel_smoke_total": formal_verifier_queue_manifest[
                "kernel_smoke_total"
            ],
            "goal_conditioned_minimal_formalization_plans": goal_conditioned_minimal_formalization_plan_manifest[
                "n_goal_plans"
            ],
            "goal_conditioned_minimal_formalization_ready": goal_conditioned_minimal_formalization_plan_manifest[
                "n_ready"
            ],
            "goal_conditioned_minimal_formalization_low_cost": goal_conditioned_minimal_formalization_plan_manifest[
                "n_low_cost_goal_plans"
            ],
            "goal_conditioned_minimal_formalization_reuse_or_composition": goal_conditioned_minimal_formalization_plan_manifest[
                "n_reuse_or_composition"
            ],
            "goal_conditioned_minimal_formalization_bridge_or_wrapper": goal_conditioned_minimal_formalization_plan_manifest[
                "n_bridge_or_wrapper"
            ],
            "goal_conditioned_minimal_formalization_requires_new_theory": goal_conditioned_minimal_formalization_plan_manifest[
                "n_requires_new_theory"
            ],
            "goal_conditioned_minimal_formalization_existing_reuse_nodes": goal_conditioned_minimal_formalization_plan_manifest[
                "n_existing_reuse_nodes"
            ],
            "goal_conditioned_minimal_formalization_wrapper_nodes": goal_conditioned_minimal_formalization_plan_manifest[
                "n_wrapper_nodes"
            ],
            "goal_conditioned_minimal_formalization_bridge_nodes": goal_conditioned_minimal_formalization_plan_manifest[
                "n_bridge_nodes"
            ],
            "goal_conditioned_minimal_formalization_source_discovery_nodes": goal_conditioned_minimal_formalization_plan_manifest[
                "n_source_discovery_nodes"
            ],
            "goal_conditioned_minimal_formalization_first_principles_nodes": goal_conditioned_minimal_formalization_plan_manifest[
                "n_first_principles_nodes"
            ],
            "goal_conditioned_minimal_formalization_do_not_formalize_hints": goal_conditioned_minimal_formalization_plan_manifest[
                "n_do_not_formalize_hints"
            ],
            "goal_conditioned_minimal_formalization_and_or_nodes": goal_conditioned_minimal_formalization_plan_manifest[
                "n_and_or_plan_nodes"
            ],
            "goal_conditioned_minimal_formalization_and_or_edges": goal_conditioned_minimal_formalization_plan_manifest[
                "n_and_or_plan_edges"
            ],
            "goal_conditioned_minimal_formalization_informal_dag_nodes": goal_conditioned_minimal_formalization_plan_manifest[
                "n_informal_knowledge_dag_nodes"
            ],
            "goal_conditioned_minimal_formalization_informal_dag_edges": goal_conditioned_minimal_formalization_plan_manifest[
                "n_informal_knowledge_dag_edges"
            ],
            "goal_conditioned_minimal_formalization_lean_realization_dag_nodes": goal_conditioned_minimal_formalization_plan_manifest[
                "n_lean_realization_dag_nodes"
            ],
            "goal_conditioned_minimal_formalization_lean_realization_dag_edges": goal_conditioned_minimal_formalization_plan_manifest[
                "n_lean_realization_dag_edges"
            ],
            "goal_conditioned_minimal_formalization_route_alignment_edges": goal_conditioned_minimal_formalization_plan_manifest[
                "n_route_alignment_edges"
            ],
            "goal_conditioned_minimal_formalization_route_alignment_edge_schema_valid": goal_conditioned_minimal_formalization_plan_manifest[
                "n_route_alignment_edge_schema_valid"
            ],
            "goal_conditioned_minimal_formalization_route_alignment_edge_schema_invalid": goal_conditioned_minimal_formalization_plan_manifest[
                "n_route_alignment_edge_schema_invalid"
            ],
            "goal_conditioned_minimal_formalization_goal_plan_row_schema_valid": goal_conditioned_minimal_formalization_plan_manifest[
                "n_goal_plan_row_schema_valid"
            ],
            "goal_conditioned_minimal_formalization_goal_plan_row_schema_invalid": goal_conditioned_minimal_formalization_plan_manifest[
                "n_goal_plan_row_schema_invalid"
            ],
            "goal_conditioned_minimal_formalization_route_revision_triggers": goal_conditioned_minimal_formalization_plan_manifest[
                "n_route_revision_triggers"
            ],
            "goal_conditioned_minimal_formalization_portable_work_packets": goal_conditioned_minimal_formalization_plan_manifest[
                "n_portable_work_packets"
            ],
            "goal_conditioned_minimal_formalization_ok": goal_conditioned_minimal_formalization_plan_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_portable_plan_audit_checks": formalization_gap_planner_portable_plan_audit_manifest[
                "n_checks"
            ],
            "formalization_gap_planner_portable_plan_audit_ok": formalization_gap_planner_portable_plan_audit_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_portable_plan_audit_failed": formalization_gap_planner_portable_plan_audit_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_portable_plan_audit_row_schema_valid": formalization_gap_planner_portable_plan_audit_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_portable_plan_audit_row_schema_invalid": formalization_gap_planner_portable_plan_audit_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_portable_plan_audit_rows": formalization_gap_planner_portable_plan_audit_manifest[
                "n_plan_rows"
            ],
            "formalization_gap_planner_portable_plan_audit_contract_errors": formalization_gap_planner_portable_plan_audit_manifest[
                "n_contract_errors"
            ],
            "formalization_gap_planner_portable_plan_audit_two_dag_rows": formalization_gap_planner_portable_plan_audit_manifest[
                "n_rows_with_two_dag"
            ],
            "formalization_gap_planner_portable_plan_audit_alignment_rows": formalization_gap_planner_portable_plan_audit_manifest[
                "n_rows_with_alignment_edges"
            ],
            "formalization_gap_planner_portable_plan_audit_route_alignment_edges": formalization_gap_planner_portable_plan_audit_manifest[
                "n_route_alignment_edges"
            ],
            "formalization_gap_planner_portable_plan_audit_route_alignment_edge_schema_valid": formalization_gap_planner_portable_plan_audit_manifest[
                "n_route_alignment_edge_schema_valid"
            ],
            "formalization_gap_planner_portable_plan_audit_route_alignment_edge_schema_invalid": formalization_gap_planner_portable_plan_audit_manifest[
                "n_route_alignment_edge_schema_invalid"
            ],
            "formalization_gap_planner_portable_plan_audit_work_packet_rows": formalization_gap_planner_portable_plan_audit_manifest[
                "n_rows_with_work_packets"
            ],
            "formalization_gap_planner_portable_plan_audit_no_kernel_claim_rows": formalization_gap_planner_portable_plan_audit_manifest[
                "n_rows_without_kernel_claims"
            ],
            "formalization_gap_planner_library_coverage_rows": formalization_gap_planner_library_coverage_map_manifest[
                "n_coverage_rows"
            ],
            "formalization_gap_planner_library_coverage_ok": formalization_gap_planner_library_coverage_map_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_library_coverage_failed": formalization_gap_planner_library_coverage_map_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_library_coverage_exact_exists": formalization_gap_planner_library_coverage_map_manifest[
                "n_exact_exists"
            ],
            "formalization_gap_planner_library_coverage_near_exists": formalization_gap_planner_library_coverage_map_manifest[
                "n_near_exists"
            ],
            "formalization_gap_planner_library_coverage_wrapper_needed": formalization_gap_planner_library_coverage_map_manifest[
                "n_wrapper_needed"
            ],
            "formalization_gap_planner_library_coverage_bridge_needed": formalization_gap_planner_library_coverage_map_manifest[
                "n_bridge_needed"
            ],
            "formalization_gap_planner_library_coverage_source_port_needed": formalization_gap_planner_library_coverage_map_manifest[
                "n_source_port_needed"
            ],
            "formalization_gap_planner_library_coverage_definition_or_theory_missing": formalization_gap_planner_library_coverage_map_manifest[
                "n_definition_or_theory_missing"
            ],
            "formalization_gap_planner_library_coverage_unknown_or_unaligned": formalization_gap_planner_library_coverage_map_manifest[
                "n_unknown_or_unaligned"
            ],
            "formalization_gap_planner_library_coverage_rows_with_alignment": formalization_gap_planner_library_coverage_map_manifest[
                "n_rows_with_alignment"
            ],
            "formalization_gap_planner_library_coverage_row_schema_valid": formalization_gap_planner_library_coverage_map_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_library_coverage_row_schema_invalid": formalization_gap_planner_library_coverage_map_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_primitive_action_queue_items": formalization_gap_planner_primitive_action_queue_manifest[
                "n_action_items"
            ],
            "formalization_gap_planner_primitive_action_queue_ok": formalization_gap_planner_primitive_action_queue_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_primitive_action_queue_failed": formalization_gap_planner_primitive_action_queue_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_primitive_action_queue_target_prover_replay": formalization_gap_planner_primitive_action_queue_manifest[
                "n_target_prover_replay"
            ],
            "formalization_gap_planner_primitive_action_queue_compose_existing_declarations": formalization_gap_planner_primitive_action_queue_manifest[
                "n_compose_existing_declarations"
            ],
            "formalization_gap_planner_primitive_action_queue_write_wrapper": formalization_gap_planner_primitive_action_queue_manifest[
                "n_write_wrapper"
            ],
            "formalization_gap_planner_primitive_action_queue_prove_bridge_lemma": formalization_gap_planner_primitive_action_queue_manifest[
                "n_prove_bridge_lemma"
            ],
            "formalization_gap_planner_primitive_action_queue_source_port": formalization_gap_planner_primitive_action_queue_manifest[
                "n_source_port"
            ],
            "formalization_gap_planner_primitive_action_queue_design_new_theory_fragment": formalization_gap_planner_primitive_action_queue_manifest[
                "n_design_new_theory_fragment"
            ],
            "formalization_gap_planner_primitive_action_queue_rerun_library_alignment": formalization_gap_planner_primitive_action_queue_manifest[
                "n_rerun_library_alignment"
            ],
            "formalization_gap_planner_primitive_action_queue_row_schema_valid": formalization_gap_planner_primitive_action_queue_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_primitive_action_queue_row_schema_invalid": formalization_gap_planner_primitive_action_queue_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_action_resource_plan_rows": formalization_gap_planner_action_resource_plan_manifest[
                "n_resource_plan_rows"
            ],
            "formalization_gap_planner_action_resource_plan_ok": formalization_gap_planner_action_resource_plan_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_action_resource_plan_failed": formalization_gap_planner_action_resource_plan_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_action_resource_plan_row_schema_valid": formalization_gap_planner_action_resource_plan_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_action_resource_plan_row_schema_invalid": formalization_gap_planner_action_resource_plan_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_action_resource_plan_with_local_first_resources": formalization_gap_planner_action_resource_plan_manifest[
                "n_with_local_first_resources"
            ],
            "formalization_gap_planner_action_resource_plan_with_frontier_resources": formalization_gap_planner_action_resource_plan_manifest[
                "n_with_frontier_escalation_resources"
            ],
            "formalization_gap_planner_action_resource_plan_with_resource_contracts": formalization_gap_planner_action_resource_plan_manifest[
                "n_with_resource_contracts"
            ],
            "formalization_gap_planner_resource_request_queue_rows": formalization_gap_planner_resource_request_queue_manifest[
                "n_resource_request_rows"
            ],
            "formalization_gap_planner_resource_request_queue_ok": formalization_gap_planner_resource_request_queue_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_resource_request_queue_failed": formalization_gap_planner_resource_request_queue_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_resource_request_queue_local_first": formalization_gap_planner_resource_request_queue_manifest[
                "n_local_first_requests"
            ],
            "formalization_gap_planner_resource_request_queue_frontier_escalation": formalization_gap_planner_resource_request_queue_manifest[
                "n_frontier_escalation_requests"
            ],
            "formalization_gap_planner_resource_request_queue_distinct_resources": formalization_gap_planner_resource_request_queue_manifest[
                "n_distinct_resources"
            ],
            "formalization_gap_planner_resource_request_queue_row_schema_valid": formalization_gap_planner_resource_request_queue_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_resource_request_queue_row_schema_invalid": formalization_gap_planner_resource_request_queue_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_resource_response_ledger_rows": formalization_gap_planner_resource_response_ledger_manifest[
                "n_ledger_rows"
            ],
            "formalization_gap_planner_resource_response_ledger_ok": formalization_gap_planner_resource_response_ledger_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_resource_response_ledger_response_present": formalization_gap_planner_resource_response_ledger_manifest[
                "n_response_present"
            ],
            "formalization_gap_planner_resource_response_ledger_awaiting": formalization_gap_planner_resource_response_ledger_manifest[
                "n_awaiting_response"
            ],
            "formalization_gap_planner_resource_response_ledger_contract_ok": formalization_gap_planner_resource_response_ledger_manifest[
                "n_response_contract_ok"
            ],
            "formalization_gap_planner_resource_response_ledger_request_playbook_present": formalization_gap_planner_resource_response_ledger_manifest[
                "n_request_playbook_present"
            ],
            "formalization_gap_planner_resource_response_ledger_playbook_grounded": formalization_gap_planner_resource_response_ledger_manifest[
                "n_response_playbook_grounded"
            ],
            "formalization_gap_planner_resource_response_ledger_playbook_grounding_failures": formalization_gap_planner_resource_response_ledger_manifest[
                "n_response_playbook_grounding_failures"
            ],
            "formalization_gap_planner_resource_response_ledger_route_revision_recommended": formalization_gap_planner_resource_response_ledger_manifest[
                "n_route_revision_recommended"
            ],
            "formalization_gap_planner_resource_response_ledger_rejected": formalization_gap_planner_resource_response_ledger_manifest[
                "n_rejected"
            ],
            "formalization_gap_planner_resource_response_ledger_row_schema_valid": formalization_gap_planner_resource_response_ledger_manifest[
                "n_ledger_row_schema_valid"
            ],
            "formalization_gap_planner_resource_response_ledger_row_schema_invalid": formalization_gap_planner_resource_response_ledger_manifest[
                "n_ledger_row_schema_invalid"
            ],
            "formalization_gap_planner_minimal_delta_audit_checks": formalization_gap_planner_minimal_delta_audit_manifest[
                "n_checks"
            ],
            "formalization_gap_planner_minimal_delta_audit_ok": formalization_gap_planner_minimal_delta_audit_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_minimal_delta_audit_failed": formalization_gap_planner_minimal_delta_audit_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_minimal_delta_audit_cost_formula_rows": formalization_gap_planner_minimal_delta_audit_manifest[
                "n_rows_with_cost_formula_ok"
            ],
            "formalization_gap_planner_minimal_delta_audit_work_packet_rows": formalization_gap_planner_minimal_delta_audit_manifest[
                "n_rows_with_work_packet_cut_ok"
            ],
            "formalization_gap_planner_minimal_delta_audit_dominated_routes": formalization_gap_planner_minimal_delta_audit_manifest[
                "n_dominated_route_witnesses"
            ],
            "formalization_gap_planner_minimal_delta_decision_rows": formalization_gap_planner_minimal_delta_audit_manifest[
                "n_minimal_delta_decision_rows"
            ],
            "formalization_gap_planner_minimal_delta_decision_row_schema_valid": formalization_gap_planner_minimal_delta_audit_manifest[
                "n_minimal_delta_decision_row_schema_valid"
            ],
            "formalization_gap_planner_minimal_delta_decision_row_schema_invalid": formalization_gap_planner_minimal_delta_audit_manifest[
                "n_minimal_delta_decision_row_schema_invalid"
            ],
            "formalization_gap_planner_source_grounding_rows": formalization_gap_planner_source_grounding_audit_manifest[
                "n_source_grounding_rows"
            ],
            "formalization_gap_planner_source_grounding_informal_route_rows": formalization_gap_planner_source_grounding_audit_manifest[
                "n_informal_route_grounding_rows"
            ],
            "formalization_gap_planner_source_grounding_residual_rows": formalization_gap_planner_source_grounding_audit_manifest[
                "n_residual_grounding_rows"
            ],
            "formalization_gap_planner_source_grounding_residual_goals": formalization_gap_planner_source_grounding_audit_manifest[
                "n_residual_goals"
            ],
            "formalization_gap_planner_source_grounding_residual_primitives": formalization_gap_planner_source_grounding_audit_manifest[
                "n_residual_primitives"
            ],
            "formalization_gap_planner_source_grounding_residual_unaccounted": formalization_gap_planner_source_grounding_audit_manifest[
                "n_residual_unaccounted"
            ],
            "formalization_gap_planner_source_grounding_source_backed": formalization_gap_planner_source_grounding_audit_manifest[
                "n_source_backed"
            ],
            "formalization_gap_planner_source_grounding_pending": formalization_gap_planner_source_grounding_audit_manifest[
                "n_source_search_pending"
            ],
            "formalization_gap_planner_source_grounding_formal_boundary": formalization_gap_planner_source_grounding_audit_manifest[
                "n_formal_boundary_declared"
            ],
            "formalization_gap_planner_source_grounding_unaccounted": formalization_gap_planner_source_grounding_audit_manifest[
                "n_unaccounted"
            ],
            "formalization_gap_planner_source_grounding_row_schema_valid": formalization_gap_planner_source_grounding_audit_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_source_grounding_row_schema_invalid": formalization_gap_planner_source_grounding_audit_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_target_intake_targets": formalization_gap_planner_target_intake_manifest[
                "n_targets"
            ],
            "formalization_gap_planner_target_intake_ok": formalization_gap_planner_target_intake_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_target_intake_primitive_seeds": formalization_gap_planner_target_intake_manifest[
                "n_primitive_seed_rows"
            ],
            "formalization_gap_planner_target_intake_literature_queries": formalization_gap_planner_target_intake_manifest[
                "n_literature_queries"
            ],
            "formalization_gap_planner_target_intake_lean_queries": formalization_gap_planner_target_intake_manifest[
                "n_lean_grounding_queries"
            ],
            "formalization_gap_planner_target_intake_formal_library_queries": formalization_gap_planner_target_intake_manifest[
                "n_formal_library_grounding_queries"
            ],
            "formalization_gap_planner_target_intake_missing_sources": formalization_gap_planner_target_intake_manifest[
                "n_missing_proof_sources"
            ],
            "formalization_gap_planner_benchmark_routes": formalization_gap_planner_benchmark_manifest[
                "n_routes"
            ],
            "formalization_gap_planner_benchmark_required_primitives": formalization_gap_planner_benchmark_manifest[
                "n_required_primitives"
            ],
            "formalization_gap_planner_benchmark_kernel_verified_routes": formalization_gap_planner_benchmark_manifest[
                "n_kernel_verified_routes"
            ],
            "formalization_gap_planner_benchmark_route_row_schema_valid": formalization_gap_planner_benchmark_manifest[
                "n_route_row_schema_valid"
            ],
            "formalization_gap_planner_benchmark_route_row_schema_invalid": formalization_gap_planner_benchmark_manifest[
                "n_route_row_schema_invalid"
            ],
            "formalization_gap_planner_benchmark_audit_checks": formalization_gap_planner_benchmark_audit_manifest[
                "n_checks"
            ],
            "formalization_gap_planner_benchmark_audit_ok": formalization_gap_planner_benchmark_audit_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_benchmark_audit_failed": formalization_gap_planner_benchmark_audit_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_benchmark_audit_splits": formalization_gap_planner_benchmark_audit_manifest[
                "n_evaluation_splits"
            ],
            "formalization_gap_planner_benchmark_audit_routes_with_source_refs": formalization_gap_planner_benchmark_audit_manifest[
                "n_routes_with_source_refs"
            ],
            "formalization_gap_planner_benchmark_audit_route_row_schema_valid": formalization_gap_planner_benchmark_audit_manifest[
                "n_route_row_schema_valid"
            ],
            "formalization_gap_planner_benchmark_audit_route_row_schema_invalid": formalization_gap_planner_benchmark_audit_manifest[
                "n_route_row_schema_invalid"
            ],
            "formalization_gap_planner_evaluation_rows": formalization_gap_planner_evaluation_manifest[
                "n_evaluation_rows"
            ],
            "formalization_gap_planner_evaluation_row_schema_valid": formalization_gap_planner_evaluation_manifest[
                "n_evaluation_row_schema_valid"
            ],
            "formalization_gap_planner_evaluation_row_schema_invalid": formalization_gap_planner_evaluation_manifest[
                "n_evaluation_row_schema_invalid"
            ],
            "formalization_gap_planner_evaluation_matched_ground_truth": formalization_gap_planner_evaluation_manifest[
                "n_matched_ground_truth"
            ],
            "formalization_gap_planner_evaluation_ground_truth_rows": formalization_gap_planner_evaluation_manifest[
                "n_ground_truth_rows"
            ],
            "formalization_gap_planner_evaluation_ok": formalization_gap_planner_evaluation_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_evaluation_two_dag_contract_ok": formalization_gap_planner_evaluation_manifest[
                "n_two_dag_contract_ok"
            ],
            "formalization_gap_planner_evaluation_alignment_contract_ok": formalization_gap_planner_evaluation_manifest[
                "n_alignment_contract_ok"
            ],
            "formalization_gap_planner_evaluation_unaligned_primitives": formalization_gap_planner_evaluation_manifest[
                "n_unaligned_primitives"
            ],
            "formalization_gap_planner_evaluation_feedback_loop_ready": formalization_gap_planner_evaluation_manifest[
                "n_feedback_loop_ready"
            ],
            "formalization_gap_planner_evaluation_rows_with_route_adoption_status": formalization_gap_planner_evaluation_manifest.get(
                "n_rows_with_llm_route_planner_route_adoption_status",
                0,
            ),
            "formalization_gap_planner_evaluation_rows_ready_for_route_adoption": formalization_gap_planner_evaluation_manifest.get(
                "n_rows_ready_for_route_adoption",
                0,
            ),
            "formalization_gap_planner_evaluation_rows_pending_refinement_before_route_adoption": formalization_gap_planner_evaluation_manifest.get(
                "n_rows_pending_refinement_before_route_adoption",
                0,
            ),
            **_formalization_gap_planner_evaluation_route_adoption_count_rollups(
                formalization_gap_planner_evaluation_manifest
            ),
            "formalization_gap_planner_evaluation_ground_truth_residual_rows": formalization_gap_planner_evaluation_manifest.get(
                "n_ground_truth_residual_rows",
                0,
            ),
            "formalization_gap_planner_evaluation_predicted_residual_primitives": formalization_gap_planner_evaluation_manifest.get(
                "n_predicted_residual_primitives",
                0,
            ),
            "formalization_gap_planner_evaluation_ground_truth_residual_primitives": formalization_gap_planner_evaluation_manifest.get(
                "n_ground_truth_residual_primitives",
                0,
            ),
            "formalization_gap_planner_evaluation_mean_route_recall": formalization_gap_planner_evaluation_manifest[
                "mean_route_recall"
            ],
            "formalization_gap_planner_evaluation_mean_delta_precision": formalization_gap_planner_evaluation_manifest[
                "mean_delta_precision"
            ],
            "formalization_gap_planner_evaluation_mean_residual_precision": formalization_gap_planner_evaluation_manifest.get(
                "mean_residual_precision",
                0.0,
            ),
            "formalization_gap_planner_evaluation_mean_residual_recall": formalization_gap_planner_evaluation_manifest.get(
                "mean_residual_recall",
                0.0,
            ),
            "formalization_gap_planner_evaluation_mean_alignment_coverage": formalization_gap_planner_evaluation_manifest[
                "mean_alignment_coverage"
            ],
            "formal_verifier_replay_tasks": formal_verifier_replay_manifest["n_replay_tasks"],
            "formal_verifier_replay_ok": formal_verifier_replay_manifest["n_ok"],
            "formal_verifier_replay_kernel_calibrated": formal_verifier_replay_manifest[
                "n_kernel_calibrated"
            ],
            "formal_verifier_replay_proof_search_subclaim": formal_verifier_replay_manifest[
                "n_proof_search_subclaim_replay"
            ],
            "formal_verifier_replay_bridge_lemma": formal_verifier_replay_manifest[
                "n_bridge_lemma_replay"
            ],
            "formal_verifier_replay_semantic_review": formal_verifier_replay_manifest[
                "n_semantic_review"
            ],
            "formal_verifier_replay_training_examples": formal_verifier_replay_manifest[
                "n_training_examples"
            ],
            "formal_verifier_replay_subclaim_obligations": formal_verifier_replay_manifest[
                "n_subclaim_replay_obligations"
            ],
            "formal_verifier_replay_kernel_smoke_related_verified": formal_verifier_replay_manifest[
                "n_kernel_smoke_related_verified"
            ],
            "formal_verifier_replay_attempt_source_tasks": formal_verifier_replay_attempt_manifest[
                "n_source_replay_tasks"
            ],
            "formal_verifier_replay_attempts": formal_verifier_replay_attempt_manifest[
                "n_attempted"
            ],
            "formal_verifier_replay_attempt_positive": formal_verifier_replay_attempt_manifest[
                "n_positive"
            ],
            "formal_verifier_replay_attempt_negative": formal_verifier_replay_attempt_manifest[
                "n_negative"
            ],
            "formal_verifier_replay_attempt_kernel_verified": formal_verifier_replay_attempt_manifest[
                "n_kernel_verified"
            ],
            "formal_verifier_replay_attempt_non_kernel_positive": formal_verifier_replay_attempt_manifest[
                "n_non_kernel_positive"
            ],
            "formal_verifier_replay_attempt_placeholder_removed": formal_verifier_replay_attempt_manifest[
                "n_placeholder_removed"
            ],
            "formal_verifier_replay_attempt_with_formal_gap_task": formal_verifier_replay_attempt_manifest[
                "n_with_formal_gap_task"
            ],
            "formal_verifier_replay_calibration_rows": formal_verifier_replay_calibration_manifest[
                "n_calibration_rows"
            ],
            "formal_verifier_replay_calibration_ok": formal_verifier_replay_calibration_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_attempted": formal_verifier_replay_calibration_manifest[
                "n_attempted_replay_tasks"
            ],
            "formal_verifier_replay_awaiting_full_route_attempt": formal_verifier_replay_calibration_manifest[
                "n_awaiting_full_route_attempt"
            ],
            "formal_verifier_replay_failed_full_route_attempt": formal_verifier_replay_calibration_manifest[
                "n_failed_full_route_attempt"
            ],
            "formal_verifier_replay_non_kernel_positive": formal_verifier_replay_calibration_manifest[
                "n_non_kernel_positive"
            ],
            "formal_verifier_replay_full_route_kernel_verified": formal_verifier_replay_calibration_manifest[
                "n_kernel_verified"
            ],
            "formal_verifier_replay_calibration_repair_training_examples": formal_verifier_replay_calibration_manifest[
                "n_repair_training_examples"
            ],
            "formalization_gap_planner_refinement_queue_items": formalization_gap_planner_refinement_queue_manifest[
                "n_refinement_items"
            ],
            "formalization_gap_planner_refinement_queue_ready": formalization_gap_planner_refinement_queue_manifest[
                "n_ready"
            ],
            "formalization_gap_planner_refinement_queue_item_schema_valid": formalization_gap_planner_refinement_queue_manifest[
                "n_item_schema_valid"
            ],
            "formalization_gap_planner_refinement_queue_item_schema_invalid": formalization_gap_planner_refinement_queue_manifest[
                "n_item_schema_invalid"
            ],
            "formalization_gap_planner_refinement_queue_blocked": formalization_gap_planner_refinement_queue_manifest[
                "n_blocked"
            ],
            "formalization_gap_planner_refinement_queue_literature": formalization_gap_planner_refinement_queue_manifest[
                "n_literature_discovery_items"
            ],
            "formalization_gap_planner_refinement_queue_formal_grounding": formalization_gap_planner_refinement_queue_manifest[
                "n_formal_library_grounding_items"
            ],
            "formalization_gap_planner_refinement_queue_lean_grounding": formalization_gap_planner_refinement_queue_manifest[
                "n_lean_library_grounding_items"
            ],
            "formalization_gap_planner_refinement_queue_proof_feedback": formalization_gap_planner_refinement_queue_manifest[
                "n_proof_state_feedback_items"
            ],
            "formalization_gap_planner_refinement_queue_route_revision": formalization_gap_planner_refinement_queue_manifest[
                "n_route_revision_items"
            ],
            "formalization_gap_planner_refinement_queue_with_evaluation_signal": formalization_gap_planner_refinement_queue_manifest[
                "n_with_evaluation_signal"
            ],
            "formalization_gap_planner_refinement_queue_with_prover_feedback": formalization_gap_planner_refinement_queue_manifest[
                "n_with_prover_feedback"
            ],
            "formalization_gap_planner_refinement_queue_with_failed_prover_feedback": formalization_gap_planner_refinement_queue_manifest[
                "n_with_failed_prover_feedback"
            ],
            "formalization_gap_planner_refinement_queue_ok": formalization_gap_planner_refinement_queue_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_refinement_adapter_responses": formalization_gap_planner_refinement_adapter_manifest[
                "n_responses"
            ],
            "formalization_gap_planner_refinement_adapter_ground_truth_matched": formalization_gap_planner_refinement_adapter_manifest[
                "n_ground_truth_matched"
            ],
            "formalization_gap_planner_refinement_adapter_literature_responses": formalization_gap_planner_refinement_adapter_manifest[
                "n_literature_responses"
            ],
            "formalization_gap_planner_refinement_adapter_formal_grounding_responses": formalization_gap_planner_refinement_adapter_manifest[
                "n_formal_grounding_responses"
            ],
            "formalization_gap_planner_refinement_adapter_lean_grounding_responses": formalization_gap_planner_refinement_adapter_manifest[
                "n_lean_grounding_responses"
            ],
            "formalization_gap_planner_refinement_adapter_prover_feedback_responses": formalization_gap_planner_refinement_adapter_manifest[
                "n_prover_feedback_responses"
            ],
            "formalization_gap_planner_refinement_adapter_route_revision_responses": formalization_gap_planner_refinement_adapter_manifest[
                "n_route_revision_responses"
            ],
            "formalization_gap_planner_refinement_adapter_route_revision_recommended": formalization_gap_planner_refinement_adapter_manifest[
                "n_route_revision_recommended"
            ],
            "formalization_gap_planner_refinement_adapter_response_schema_valid": formalization_gap_planner_refinement_adapter_manifest[
                "n_response_schema_valid"
            ],
            "formalization_gap_planner_refinement_adapter_response_schema_invalid": formalization_gap_planner_refinement_adapter_manifest[
                "n_response_schema_invalid"
            ],
            "formalization_gap_planner_refinement_adapter_ok": formalization_gap_planner_refinement_adapter_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_local_literature_responses": formalization_gap_planner_local_literature_adapter_manifest[
                "n_local_literature_responses"
            ],
            "formalization_gap_planner_local_literature_source_hits": formalization_gap_planner_local_literature_adapter_manifest[
                "n_source_hits"
            ],
            "formalization_gap_planner_local_literature_gap_responses": formalization_gap_planner_local_literature_adapter_manifest[
                "n_literature_gap_responses"
            ],
            "formalization_gap_planner_local_literature_merged_responses": formalization_gap_planner_local_literature_adapter_manifest[
                "n_merged_responses"
            ],
            "formalization_gap_planner_local_literature_response_schema_valid": formalization_gap_planner_local_literature_adapter_manifest[
                "n_local_response_schema_valid"
            ],
            "formalization_gap_planner_local_literature_response_schema_invalid": formalization_gap_planner_local_literature_adapter_manifest[
                "n_local_response_schema_invalid"
            ],
            "formalization_gap_planner_local_formal_source_responses": formalization_gap_planner_local_formal_source_adapter_manifest[
                "n_local_formal_source_responses"
            ],
            "formalization_gap_planner_local_formal_source_formal_grounding_rows": formalization_gap_planner_local_formal_source_adapter_manifest[
                "n_formal_library_grounding_rows"
            ],
            "formalization_gap_planner_local_formal_source_legacy_lean_grounding_rows": formalization_gap_planner_local_formal_source_adapter_manifest[
                "n_lean_library_grounding_rows"
            ],
            "formalization_gap_planner_local_formal_source_hits": formalization_gap_planner_local_formal_source_adapter_manifest[
                "n_hits"
            ],
            "formalization_gap_planner_local_formal_source_exact_exists": formalization_gap_planner_local_formal_source_adapter_manifest[
                "n_exact_exists"
            ],
            "formalization_gap_planner_local_formal_source_merged_responses": formalization_gap_planner_local_formal_source_adapter_manifest[
                "n_merged_responses"
            ],
            "formalization_gap_planner_local_formal_source_response_schema_valid": formalization_gap_planner_local_formal_source_adapter_manifest[
                "n_local_response_schema_valid"
            ],
            "formalization_gap_planner_local_formal_source_response_schema_invalid": formalization_gap_planner_local_formal_source_adapter_manifest[
                "n_local_response_schema_invalid"
            ],
            "formalization_gap_planner_local_proof_state_responses": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_local_proof_state_responses"
            ],
            "formalization_gap_planner_local_proof_state_target_prover_scaffold_accepted": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_target_prover_scaffold_accepted"
            ],
            "formalization_gap_planner_local_proof_state_target_prover_failed": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_target_prover_failed"
            ],
            "formalization_gap_planner_local_proof_state_target_prover_unavailable": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_target_prover_unavailable"
            ],
            "formalization_gap_planner_local_proof_state_non_target_prover_skeleton": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_non_target_prover_skeleton"
            ],
            "formalization_gap_planner_local_proof_state_unavailable": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_local_lean_unavailable"
            ],
            "formalization_gap_planner_local_proof_state_placeholder_blocked": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_placeholder_blocked"
            ],
            "formalization_gap_planner_local_proof_state_formal_gap_scaffold_blocked": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_formal_gap_scaffold_blocked"
            ],
            "formalization_gap_planner_local_proof_state_missing_skeleton": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_missing_skeleton"
            ],
            "formalization_gap_planner_local_proof_state_merged_responses": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_merged_responses"
            ],
            "formalization_gap_planner_local_proof_state_response_schema_valid": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_local_response_schema_valid"
            ],
            "formalization_gap_planner_local_proof_state_response_schema_invalid": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_local_response_schema_invalid"
            ],
            "formalization_gap_planner_local_adapter_response_schema_valid": sum(
                int(payload.get("n_local_response_schema_valid", 0) or 0)
                for payload in (
                    formalization_gap_planner_local_literature_adapter_manifest,
                    formalization_gap_planner_local_formal_source_adapter_manifest,
                    formalization_gap_planner_local_proof_state_adapter_manifest,
                )
            ),
            "formalization_gap_planner_local_adapter_response_schema_invalid": sum(
                int(payload.get("n_local_response_schema_invalid", 0) or 0)
                for payload in (
                    formalization_gap_planner_local_literature_adapter_manifest,
                    formalization_gap_planner_local_formal_source_adapter_manifest,
                    formalization_gap_planner_local_proof_state_adapter_manifest,
                )
            ),
            "formalization_gap_planner_local_adapter_merged_response_schema_valid": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_merged_response_schema_valid"
            ],
            "formalization_gap_planner_local_adapter_merged_response_schema_invalid": formalization_gap_planner_local_proof_state_adapter_manifest[
                "n_merged_response_schema_invalid"
            ],
            "formalization_gap_planner_refinement_evidence_rows": formalization_gap_planner_refinement_evidence_manifest[
                "n_evidence_rows"
            ],
            "formalization_gap_planner_refinement_evidence_responses": formalization_gap_planner_refinement_evidence_manifest[
                "n_responses"
            ],
            "formalization_gap_planner_refinement_evidence_response_present": formalization_gap_planner_refinement_evidence_manifest[
                "n_response_present"
            ],
            "formalization_gap_planner_refinement_evidence_awaiting_tool_response": formalization_gap_planner_refinement_evidence_manifest[
                "n_awaiting_tool_response"
            ],
            "formalization_gap_planner_refinement_evidence_contract_ok": formalization_gap_planner_refinement_evidence_manifest[
                "n_contract_ok"
            ],
            "formalization_gap_planner_refinement_response_schema_valid": formalization_gap_planner_refinement_evidence_manifest[
                "n_response_schema_valid"
            ],
            "formalization_gap_planner_refinement_response_schema_invalid": formalization_gap_planner_refinement_evidence_manifest[
                "n_response_schema_invalid"
            ],
            "formalization_gap_planner_refinement_evidence_row_schema_valid": formalization_gap_planner_refinement_evidence_manifest[
                "n_evidence_row_schema_valid"
            ],
            "formalization_gap_planner_refinement_evidence_row_schema_invalid": formalization_gap_planner_refinement_evidence_manifest[
                "n_evidence_row_schema_invalid"
            ],
            "formalization_gap_planner_refinement_evidence_literature": formalization_gap_planner_refinement_evidence_manifest[
                "n_literature_evidence"
            ],
            "formalization_gap_planner_refinement_evidence_formal_grounding": formalization_gap_planner_refinement_evidence_manifest[
                "n_formal_grounding_evidence"
            ],
            "formalization_gap_planner_refinement_evidence_lean_grounding": formalization_gap_planner_refinement_evidence_manifest[
                "n_lean_grounding_evidence"
            ],
            "formalization_gap_planner_refinement_evidence_prover_feedback": formalization_gap_planner_refinement_evidence_manifest[
                "n_prover_feedback_evidence"
            ],
            "formalization_gap_planner_refinement_evidence_route_revision": formalization_gap_planner_refinement_evidence_manifest[
                "n_route_revision_evidence"
            ],
            "formalization_gap_planner_refinement_evidence_route_revision_recommended": formalization_gap_planner_refinement_evidence_manifest[
                "n_route_revision_recommended"
            ],
            "formalization_gap_planner_refinement_evidence_route_revision_proposals": formalization_gap_planner_refinement_evidence_manifest[
                "n_route_revision_proposals"
            ],
            "formalization_gap_planner_refinement_evidence_rejected": formalization_gap_planner_refinement_evidence_manifest[
                "n_rejected"
            ],
            "formalization_gap_planner_refinement_evidence_ok": formalization_gap_planner_refinement_evidence_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_route_revision_overlay_rows": formalization_gap_planner_route_revision_overlay_manifest[
                "n_overlay_rows"
            ],
            "formalization_gap_planner_route_revision_overlay_refinement_evidence_proposals": formalization_gap_planner_route_revision_overlay_manifest[
                "n_refinement_evidence_route_revision_proposals"
            ],
            "formalization_gap_planner_route_revision_overlay_resource_response_ledger_proposals": formalization_gap_planner_route_revision_overlay_manifest[
                "n_resource_response_ledger_route_revision_proposals"
            ],
            "formalization_gap_planner_route_revision_overlay_row_schema_valid": formalization_gap_planner_route_revision_overlay_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_route_revision_overlay_row_schema_invalid": formalization_gap_planner_route_revision_overlay_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_route_revision_overlay_routes_with_revision": formalization_gap_planner_route_revision_overlay_manifest[
                "n_routes_with_revision"
            ],
            "formalization_gap_planner_route_revision_overlay_routes_without_revision": formalization_gap_planner_route_revision_overlay_manifest[
                "n_routes_without_revision"
            ],
            "formalization_gap_planner_route_revision_overlay_added_primitives": formalization_gap_planner_route_revision_overlay_manifest[
                "n_added_primitives"
            ],
            "formalization_gap_planner_route_revision_overlay_added_delta_primitives": formalization_gap_planner_route_revision_overlay_manifest[
                "n_added_delta_primitives"
            ],
            "formalization_gap_planner_route_revision_overlay_alignment_rows": formalization_gap_planner_route_revision_overlay_manifest[
                "n_rows_with_alignment_contract"
            ],
            "formalization_gap_planner_route_revision_overlay_alignment_edges": formalization_gap_planner_route_revision_overlay_manifest[
                "n_route_alignment_edges"
            ],
            "formalization_gap_planner_route_revision_overlay_unaligned_primitives": formalization_gap_planner_route_revision_overlay_manifest[
                "n_unaligned_primitives"
            ],
            "formalization_gap_planner_route_revision_overlay_ok": formalization_gap_planner_route_revision_overlay_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_route_stability_rows": formalization_gap_planner_route_stability_audit_manifest[
                "n_stability_rows"
            ],
            "formalization_gap_planner_route_stability_stable": formalization_gap_planner_route_stability_audit_manifest[
                "n_stable"
            ],
            "formalization_gap_planner_route_stability_needs_expansion": formalization_gap_planner_route_stability_audit_manifest[
                "n_needs_expansion"
            ],
            "formalization_gap_planner_route_stability_apply_revision": formalization_gap_planner_route_stability_audit_manifest[
                "n_apply_route_revision"
            ],
            "formalization_gap_planner_route_stability_expand_literature": formalization_gap_planner_route_stability_audit_manifest[
                "n_expand_literature"
            ],
            "formalization_gap_planner_route_stability_expand_formal": formalization_gap_planner_route_stability_audit_manifest[
                "n_expand_formal_grounding"
            ],
            "formalization_gap_planner_route_stability_expand_lean": formalization_gap_planner_route_stability_audit_manifest[
                "n_expand_lean_grounding"
            ],
            "formalization_gap_planner_route_stability_expand_proof_state": formalization_gap_planner_route_stability_audit_manifest[
                "n_expand_proof_state"
            ],
            "formalization_gap_planner_route_stability_new_primitives": formalization_gap_planner_route_stability_audit_manifest[
                "n_new_primitives_since_plan"
            ],
            "formalization_gap_planner_route_stability_row_schema_valid": formalization_gap_planner_route_stability_audit_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_route_stability_row_schema_invalid": formalization_gap_planner_route_stability_audit_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_route_stability_ok": formalization_gap_planner_route_stability_audit_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_route_replan_handoff_rows": formalization_gap_planner_route_replan_handoff_manifest[
                "n_handoff_rows"
            ],
            "formalization_gap_planner_route_replan_handoff_row_schema_valid": formalization_gap_planner_route_replan_handoff_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_route_replan_handoff_row_schema_invalid": formalization_gap_planner_route_replan_handoff_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_route_replan_handoff_requiring_replan": formalization_gap_planner_route_replan_handoff_manifest[
                "n_routes_requiring_replan"
            ],
            "formalization_gap_planner_route_replan_handoff_seed_routes": formalization_gap_planner_route_replan_handoff_manifest[
                "n_standalone_seed_routes"
            ],
            "formalization_gap_planner_route_replan_handoff_alignment_edges": formalization_gap_planner_route_replan_handoff_manifest[
                "n_route_alignment_edges"
            ],
            "formalization_gap_planner_route_replan_handoff_unaligned_primitives": formalization_gap_planner_route_replan_handoff_manifest[
                "n_unaligned_primitives"
            ],
            "formalization_gap_planner_route_replan_handoff_residual_routes": formalization_gap_planner_route_replan_handoff_manifest[
                "n_routes_with_residual_goals"
            ],
            "formalization_gap_planner_route_replan_handoff_resource_response_ledger_feedback": formalization_gap_planner_route_replan_handoff_manifest[
                "n_routes_with_resource_response_ledger_feedback"
            ],
            "formalization_gap_planner_route_replan_handoff_distinct_prover_diagnostic_signatures": formalization_gap_planner_route_replan_handoff_manifest[
                "n_distinct_prover_diagnostic_signatures"
            ],
            "formalization_gap_planner_route_replan_handoff_ok": formalization_gap_planner_route_replan_handoff_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_route_replan_handoff_audit_checks": formalization_gap_planner_route_replan_handoff_audit_manifest[
                "n_checks"
            ],
            "formalization_gap_planner_route_replan_handoff_audit_ok": formalization_gap_planner_route_replan_handoff_audit_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_route_replan_handoff_audit_failed": formalization_gap_planner_route_replan_handoff_audit_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_route_replan_handoff_audit_row_schema_valid": formalization_gap_planner_route_replan_handoff_audit_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_route_replan_handoff_audit_row_schema_invalid": formalization_gap_planner_route_replan_handoff_audit_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_route_replan_handoff_audit_roundtrip_ok": formalization_gap_planner_route_replan_handoff_audit_manifest[
                "roundtrip_all_ok"
            ],
            "formalization_gap_planner_route_replan_handoff_audit_roundtrip_routes": formalization_gap_planner_route_replan_handoff_audit_manifest[
                "n_roundtrip_goal_plans"
            ],
            "formalization_gap_planner_route_replan_handoff_audit_roundtrip_alignment_edges": formalization_gap_planner_route_replan_handoff_audit_manifest[
                "n_roundtrip_route_alignment_edges"
            ],
            "formalization_gap_planner_proof_state_triage_items": formalization_gap_planner_proof_state_triage_manifest[
                "n_triage_items"
            ],
            "formalization_gap_planner_proof_state_triage_formal_gap_scaffold_items": formalization_gap_planner_proof_state_triage_manifest[
                "n_formal_gap_scaffold_items"
            ],
            "formalization_gap_planner_proof_state_triage_target_prover_failed_items": formalization_gap_planner_proof_state_triage_manifest[
                "n_target_prover_failed_items"
            ],
            "formalization_gap_planner_proof_state_triage_target_prover_unavailable_items": formalization_gap_planner_proof_state_triage_manifest[
                "n_target_prover_unavailable_items"
            ],
            "formalization_gap_planner_proof_state_triage_non_target_prover_skeleton_items": formalization_gap_planner_proof_state_triage_manifest[
                "n_non_target_prover_skeleton_items"
            ],
            "formalization_gap_planner_proof_state_triage_local_lean_failed_items": formalization_gap_planner_proof_state_triage_manifest[
                "n_local_lean_failed_items"
            ],
            "formalization_gap_planner_proof_state_triage_non_lean_skeleton_items": formalization_gap_planner_proof_state_triage_manifest[
                "n_non_lean_skeleton_items"
            ],
            "formalization_gap_planner_proof_state_triage_distinct_signatures": formalization_gap_planner_proof_state_triage_manifest[
                "n_distinct_diagnostic_signatures"
            ],
            "formalization_gap_planner_proof_state_triage_row_schema_valid": formalization_gap_planner_proof_state_triage_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_proof_state_triage_row_schema_invalid": formalization_gap_planner_proof_state_triage_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_proof_state_triage_ok": formalization_gap_planner_proof_state_triage_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_interactive_session_rows": formalization_gap_planner_interactive_session_manifest[
                "n_session_rows"
            ],
            "formalization_gap_planner_interactive_session_row_schema_valid": formalization_gap_planner_interactive_session_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_interactive_session_row_schema_invalid": formalization_gap_planner_interactive_session_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_interactive_decision_policy_rows": formalization_gap_planner_interactive_session_manifest[
                "n_decision_policy_rows"
            ],
            "formalization_gap_planner_interactive_decision_policy_row_schema_valid": formalization_gap_planner_interactive_session_manifest[
                "n_decision_policy_row_schema_valid"
            ],
            "formalization_gap_planner_interactive_decision_policy_row_schema_invalid": formalization_gap_planner_interactive_session_manifest[
                "n_decision_policy_row_schema_invalid"
            ],
            "formalization_gap_planner_interactive_decision_policy_rows_with_resource_contracts": formalization_gap_planner_interactive_session_manifest[
                "n_decision_policy_rows_with_resource_contracts"
            ],
            "formalization_gap_planner_interactive_decision_policy_rows_with_frontier_resources": formalization_gap_planner_interactive_session_manifest[
                "n_decision_policy_rows_with_frontier_resources"
            ],
            "formalization_gap_planner_interactive_decision_policy_rows_with_required_quality_signals": formalization_gap_planner_interactive_session_manifest[
                "n_decision_policy_rows_with_required_quality_signals"
            ],
            "formalization_gap_planner_interactive_decision_policy_rows_with_quality_gates": formalization_gap_planner_interactive_session_manifest[
                "n_decision_policy_rows_with_quality_gates"
            ],
            "formalization_gap_planner_interactive_decision_policy_rows_with_response_validation_signals": formalization_gap_planner_interactive_session_manifest[
                "n_decision_policy_rows_with_response_validation_signals"
            ],
            "formalization_gap_planner_interactive_session_ok": formalization_gap_planner_interactive_session_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_interactive_session_replan": formalization_gap_planner_interactive_session_manifest[
                "n_run_route_replan"
            ],
            "formalization_gap_planner_interactive_session_waiting_for_adapter_responses": formalization_gap_planner_interactive_session_manifest[
                "n_waiting_for_adapter_responses"
            ],
            "formalization_gap_planner_interactive_session_rows_requiring_replan": formalization_gap_planner_interactive_session_manifest[
                "n_rows_requiring_replan"
            ],
            "formalization_gap_planner_interactive_session_replay": formalization_gap_planner_interactive_session_manifest[
                "n_run_target_prover_replay"
            ],
            "formalization_gap_planner_interactive_session_source_refs": formalization_gap_planner_interactive_session_manifest[
                "n_rows_with_source_refs"
            ],
            "formalization_gap_planner_interactive_session_residual_goals": formalization_gap_planner_interactive_session_manifest[
                "n_rows_with_residual_goals"
            ],
            "formalization_gap_planner_interactive_session_rows_with_resource_requests": formalization_gap_planner_interactive_session_manifest[
                "n_rows_with_resource_requests"
            ],
            "formalization_gap_planner_interactive_session_resource_requests_linked": formalization_gap_planner_interactive_session_manifest[
                "n_resource_requests_linked"
            ],
            "formalization_gap_planner_interactive_session_resource_request_execution_commands": formalization_gap_planner_interactive_session_manifest[
                "n_resource_request_execution_commands"
            ],
            "formalization_gap_planner_ablation_variants": formalization_gap_planner_ablation_study_manifest[
                "n_ablation_variants"
            ],
            "formalization_gap_planner_ablation_ok": formalization_gap_planner_ablation_study_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_ablation_routes": formalization_gap_planner_ablation_study_manifest[
                "n_evaluation_rows"
            ],
            "formalization_gap_planner_ablation_row_schema_valid": formalization_gap_planner_ablation_study_manifest[
                "n_row_schema_valid"
            ],
            "formalization_gap_planner_ablation_row_schema_invalid": formalization_gap_planner_ablation_study_manifest[
                "n_row_schema_invalid"
            ],
            "formalization_gap_planner_ablation_best_route_recall": formalization_gap_planner_ablation_study_manifest[
                "best_variant_by_route_recall"
            ],
            "formalization_gap_planner_ablation_largest_route_drop": formalization_gap_planner_ablation_study_manifest[
                "largest_route_recall_drop_variant"
            ],
            "formalization_gap_planner_ablation_largest_delta_drop": formalization_gap_planner_ablation_study_manifest[
                "largest_delta_recall_drop_variant"
            ],
            "formalization_gap_planner_ablation_largest_residual_drop": formalization_gap_planner_ablation_study_manifest.get(
                "largest_residual_recall_drop_variant",
                "",
            ),
            "formalization_gap_planner_ablation_largest_route_adoption_ready_drop": formalization_gap_planner_ablation_study_manifest.get(
                "largest_route_adoption_ready_drop_variant",
                "",
            ),
            "formalization_gap_planner_prover_adapter_packets": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_packets"
            ],
            "formalization_gap_planner_prover_adapter_packet_ok": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_packet_ok"
            ],
            "formalization_gap_planner_prover_adapter_packet_schema_valid": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_packet_schema_valid"
            ],
            "formalization_gap_planner_prover_adapter_packets_with_alignment": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_packets_with_alignment"
            ],
            "formalization_gap_planner_prover_adapter_responses": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_responses"
            ],
            "formalization_gap_planner_prover_adapter_awaiting_mapping": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_awaiting_adapter_mapping"
            ],
            "formalization_gap_planner_prover_adapter_response_contract_ok": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_response_contract_ok"
            ],
            "formalization_gap_planner_prover_adapter_response_validation_row_schema_valid": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_response_validation_row_schema_valid"
            ],
            "formalization_gap_planner_prover_adapter_response_validation_row_schema_invalid": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_response_validation_row_schema_invalid"
            ],
            "formalization_gap_planner_prover_adapter_rejected": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_rejected"
            ],
            "formalization_gap_planner_prover_adapter_kernel_claims_rejected": formalization_gap_planner_prover_adapter_contract_manifest[
                "n_kernel_verified_claims_rejected"
            ],
            "formalization_gap_planner_adapter_registry_adapters": formalization_gap_planner_adapter_registry_manifest[
                "n_adapters"
            ],
            "formalization_gap_planner_adapter_registry_row_schema_valid": formalization_gap_planner_adapter_registry_manifest[
                "n_adapter_row_schema_valid"
            ],
            "formalization_gap_planner_adapter_registry_row_schema_invalid": formalization_gap_planner_adapter_registry_manifest[
                "n_adapter_row_schema_invalid"
            ],
            "formalization_gap_planner_adapter_registry_ready": formalization_gap_planner_adapter_registry_manifest[
                "n_ready_local_or_configured"
            ],
            "formalization_gap_planner_adapter_registry_contract_only": formalization_gap_planner_adapter_registry_manifest[
                "n_contract_only"
            ],
            "formalization_gap_planner_adapter_registry_audit_checks": formalization_gap_planner_adapter_registry_audit_manifest[
                "n_checks"
            ],
            "formalization_gap_planner_adapter_registry_audit_ok": formalization_gap_planner_adapter_registry_audit_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_adapter_registry_audit_failed": formalization_gap_planner_adapter_registry_audit_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_adapter_registry_audit_row_schema_valid": formalization_gap_planner_adapter_registry_audit_manifest[
                "n_adapter_row_schema_valid"
            ],
            "formalization_gap_planner_adapter_registry_audit_row_schema_invalid": formalization_gap_planner_adapter_registry_audit_manifest[
                "n_adapter_row_schema_invalid"
            ],
            "formalization_gap_planner_adapter_registry_audit_jsonl_row_schema_valid": formalization_gap_planner_adapter_registry_audit_manifest[
                "n_adapter_jsonl_row_schema_valid"
            ],
            "formalization_gap_planner_adapter_registry_audit_jsonl_row_schema_invalid": formalization_gap_planner_adapter_registry_audit_manifest[
                "n_adapter_jsonl_row_schema_invalid"
            ],
            "formalization_gap_planner_adapter_registry_audit_required_ids_present": formalization_gap_planner_adapter_registry_audit_manifest[
                "n_required_adapter_ids_present"
            ],
            "formalization_gap_planner_adapter_registry_audit_required_ids": formalization_gap_planner_adapter_registry_audit_manifest[
                "n_required_adapter_ids"
            ],
            "formalization_gap_planner_component_resource_registry_components": formalization_gap_planner_component_resource_registry_manifest[
                "n_component_rows"
            ],
            "formalization_gap_planner_component_resource_registry_resources": formalization_gap_planner_component_resource_registry_manifest[
                "n_resources"
            ],
            "formalization_gap_planner_component_resource_registry_component_row_schema_valid": formalization_gap_planner_component_resource_registry_manifest[
                "n_component_row_schema_valid"
            ],
            "formalization_gap_planner_component_resource_registry_component_row_schema_invalid": formalization_gap_planner_component_resource_registry_manifest[
                "n_component_row_schema_invalid"
            ],
            "formalization_gap_planner_component_resource_registry_resource_row_schema_valid": formalization_gap_planner_component_resource_registry_manifest[
                "n_resource_row_schema_valid"
            ],
            "formalization_gap_planner_component_resource_registry_resource_row_schema_invalid": formalization_gap_planner_component_resource_registry_manifest[
                "n_resource_row_schema_invalid"
            ],
            "formalization_gap_planner_component_resource_registry_contracts": formalization_gap_planner_component_resource_registry_manifest[
                "n_resource_contract_rows"
            ],
            "formalization_gap_planner_component_resource_registry_contracts_ok": formalization_gap_planner_component_resource_registry_manifest[
                "n_resource_contract_rows_ok"
            ],
            "formalization_gap_planner_component_resource_registry_contract_row_schema_valid": formalization_gap_planner_component_resource_registry_manifest[
                "n_resource_contract_row_schema_valid"
            ],
            "formalization_gap_planner_component_resource_registry_contract_row_schema_invalid": formalization_gap_planner_component_resource_registry_manifest[
                "n_resource_contract_row_schema_invalid"
            ],
            "formalization_gap_planner_component_resource_registry_execution_plans": formalization_gap_planner_component_resource_registry_manifest[
                "n_execution_plan_rows"
            ],
            "formalization_gap_planner_component_resource_registry_execution_plans_ok": formalization_gap_planner_component_resource_registry_manifest[
                "n_execution_plan_rows_ok"
            ],
            "formalization_gap_planner_component_resource_registry_execution_plan_row_schema_valid": formalization_gap_planner_component_resource_registry_manifest[
                "n_execution_plan_row_schema_valid"
            ],
            "formalization_gap_planner_component_resource_registry_execution_plan_row_schema_invalid": formalization_gap_planner_component_resource_registry_manifest[
                "n_execution_plan_row_schema_invalid"
            ],
            "formalization_gap_planner_component_resource_registry_frontier": formalization_gap_planner_component_resource_registry_manifest[
                "n_frontier_resources"
            ],
            "formalization_gap_planner_component_resource_registry_mcp_cli": formalization_gap_planner_component_resource_registry_manifest[
                "n_mcp_or_cli_resources"
            ],
            "formalization_gap_planner_component_resource_registry_resources_with_capability_tags": formalization_gap_planner_component_resource_registry_manifest[
                "n_resources_with_capability_tags"
            ],
            "formalization_gap_planner_component_resource_registry_resources_with_validation_signals": formalization_gap_planner_component_resource_registry_manifest[
                "n_resources_with_validation_signals"
            ],
            "formalization_gap_planner_component_resource_registry_components_with_quality_signals": formalization_gap_planner_component_resource_registry_manifest[
                "n_component_rows_with_required_quality_signals"
            ],
            "formalization_gap_planner_component_resource_registry_execution_plans_with_quality_gates": formalization_gap_planner_component_resource_registry_manifest[
                "n_execution_plans_with_quality_gates"
            ],
            "formalization_gap_planner_component_resource_registry_contracts_with_response_validation_signals": formalization_gap_planner_component_resource_registry_manifest[
                "n_resource_contracts_with_response_validation_signals"
            ],
            "formalization_gap_planner_component_resource_registry_audit_checks": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_checks"
            ],
            "formalization_gap_planner_component_resource_registry_audit_ok": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_component_resource_registry_audit_failed": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_component_resource_registry_audit_required_components_present": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_required_component_ids_present"
            ],
            "formalization_gap_planner_component_resource_registry_audit_components_with_execution_plan": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_components_with_execution_plan"
            ],
            "formalization_gap_planner_component_resource_registry_audit_execution_plan_schema_valid": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_execution_plan_schema_valid"
            ],
            "formalization_gap_planner_component_resource_registry_audit_execution_plan_schema_invalid": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_execution_plan_schema_invalid"
            ],
            "formalization_gap_planner_component_resource_registry_audit_component_row_schema_valid": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_component_row_schema_valid"
            ],
            "formalization_gap_planner_component_resource_registry_audit_component_row_schema_invalid": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_component_row_schema_invalid"
            ],
            "formalization_gap_planner_component_resource_registry_audit_resource_row_schema_valid": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_resource_row_schema_valid"
            ],
            "formalization_gap_planner_component_resource_registry_audit_resource_row_schema_invalid": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_resource_row_schema_invalid"
            ],
            "formalization_gap_planner_component_resource_registry_audit_contract_row_schema_valid": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_resource_contract_row_schema_valid"
            ],
            "formalization_gap_planner_component_resource_registry_audit_contract_row_schema_invalid": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_resource_contract_row_schema_invalid"
            ],
            "formalization_gap_planner_component_resource_registry_audit_resources_with_contract": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_resources_with_contract"
            ],
            "formalization_gap_planner_component_resource_registry_audit_required_components": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_required_component_ids"
            ],
            "formalization_gap_planner_component_resource_registry_audit_required_resources_present": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_required_resource_ids_present"
            ],
            "formalization_gap_planner_component_resource_registry_audit_required_resources": formalization_gap_planner_component_resource_registry_audit_manifest[
                "n_required_resource_ids"
            ],
            "formalization_gap_planner_cross_prover_matrix_targets": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_targets"
            ],
            "formalization_gap_planner_cross_prover_matrix_targets_ok": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_targets_ok"
            ],
            "formalization_gap_planner_cross_prover_matrix_row_schema_valid": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_matrix_row_schema_valid"
            ],
            "formalization_gap_planner_cross_prover_matrix_row_schema_invalid": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_matrix_row_schema_invalid"
            ],
            "formalization_gap_planner_cross_prover_matrix_total_packets": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_total_packets"
            ],
            "formalization_gap_planner_cross_prover_matrix_packet_ok": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_total_packet_ok"
            ],
            "formalization_gap_planner_cross_prover_matrix_packet_schema_valid": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_total_packet_schema_valid"
            ],
            "formalization_gap_planner_cross_prover_matrix_packets_schema_invalid": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_total_packets_schema_invalid"
            ],
            "formalization_gap_planner_cross_prover_matrix_packet_row_schema_valid": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_packet_row_schema_valid"
            ],
            "formalization_gap_planner_cross_prover_matrix_packet_row_schema_invalid": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_packet_row_schema_invalid"
            ],
            "formalization_gap_planner_cross_prover_matrix_response_validation_row_schema_valid": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_response_validation_row_schema_valid"
            ],
            "formalization_gap_planner_cross_prover_matrix_response_validation_row_schema_invalid": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_response_validation_row_schema_invalid"
            ],
            "formalization_gap_planner_cross_prover_matrix_packets_with_alignment": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_total_packets_with_alignment"
            ],
            "formalization_gap_planner_cross_prover_matrix_packets_missing_alignment": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_total_packets_missing_alignment"
            ],
            "formalization_gap_planner_cross_prover_matrix_rejected": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_rejected"
            ],
            "formalization_gap_planner_cross_prover_matrix_kernel_claims_rejected": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "n_kernel_verified_claims_rejected"
            ],
            "formalization_gap_planner_cross_prover_matrix_packet_count_consistent": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "packet_count_consistent"
            ],
            "formalization_gap_planner_cross_prover_matrix_alignment_packet_count_consistent": formalization_gap_planner_cross_prover_matrix_audit_manifest[
                "alignment_packet_count_consistent"
            ],
            "formalization_gap_planner_cross_prover_target_summary_rows": (
                formalization_gap_planner_cross_prover_matrix_audit_manifest.get(
                    "target_summary",
                    {},
                ).get("n_target_rows", 0)
                if isinstance(
                    formalization_gap_planner_cross_prover_matrix_audit_manifest.get(
                        "target_summary"
                    ),
                    dict,
                )
                else 0
            ),
            "formalization_gap_planner_cross_prover_target_summary_contract_errors": formalization_gap_planner_cross_prover_matrix_audit_manifest.get(
                "n_target_summary_contract_errors",
                0,
            ),
            "formalization_gap_planner_publication_bundle_core_artifacts": formalization_gap_planner_publication_bundle_manifest[
                "n_core_artifacts"
            ],
            "formalization_gap_planner_publication_bundle_core_artifacts_ok": formalization_gap_planner_publication_bundle_manifest[
                "n_core_artifacts_ok"
            ],
            "formalization_gap_planner_publication_bundle_optional_artifacts_requested": formalization_gap_planner_publication_bundle_manifest[
                "n_optional_artifacts_requested"
            ],
            "formalization_gap_planner_publication_bundle_optional_files_copied": formalization_gap_planner_publication_bundle_manifest[
                "n_optional_artifact_files_copied"
            ],
            "formalization_gap_planner_publication_bundle_docs_copied": formalization_gap_planner_publication_bundle_manifest[
                "n_docs_copied"
            ],
            "formalization_gap_planner_publication_bundle_reproduction_entrypoints": formalization_gap_planner_publication_bundle_manifest[
                "reproduction_summary"
            ]["n_entrypoints"],
            "formalization_gap_planner_publication_bundle_reproduction_commands": formalization_gap_planner_publication_bundle_manifest[
                "reproduction_summary"
            ]["n_commands"],
            "formalization_gap_planner_publication_bundle_schema_catalog_entries": (
                formalization_gap_planner_publication_bundle_manifest.get(
                    "schema_catalog_summary",
                    {},
                ).get("n_schema_entries", 0)
                if isinstance(
                    formalization_gap_planner_publication_bundle_manifest.get(
                        "schema_catalog_summary"
                    ),
                    dict,
                )
                else 0
            ),
            "formalization_gap_planner_publication_bundle_schema_catalog_contract_errors": (
                formalization_gap_planner_publication_bundle_manifest.get(
                    "schema_catalog_summary",
                    {},
                ).get("n_schema_catalog_contract_errors", 0)
                if isinstance(
                    formalization_gap_planner_publication_bundle_manifest.get(
                        "schema_catalog_summary"
                    ),
                    dict,
                )
                else 0
            ),
            "formalization_gap_planner_publication_bundle_schema_catalog_all_ok": (
                bool(
                    formalization_gap_planner_publication_bundle_manifest.get(
                        "schema_catalog_summary",
                        {},
                    ).get("all_ok", False)
                )
                if isinstance(
                    formalization_gap_planner_publication_bundle_manifest.get(
                        "schema_catalog_summary"
                    ),
                    dict,
                )
                else False
            ),
            "formalization_gap_planner_publication_bundle_audit_checks": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_checks"
            ],
            "formalization_gap_planner_publication_bundle_audit_ok": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_ok"
            ],
            "formalization_gap_planner_publication_bundle_audit_failed": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_failed"
            ],
            "formalization_gap_planner_publication_bundle_audit_component_execution_plan_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_component_execution_plan_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_component_execution_plan_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_component_execution_plan_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_component_resource_component_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_component_resource_component_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_component_resource_component_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_component_resource_component_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_component_resource_resource_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_component_resource_resource_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_component_resource_resource_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_component_resource_resource_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_component_resource_contract_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_component_resource_contract_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_component_resource_contract_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_component_resource_contract_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_prover_adapter_packet_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_prover_adapter_packet_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_prover_adapter_packet_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_prover_adapter_packet_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_benchmark_route_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_benchmark_route_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_benchmark_route_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_benchmark_route_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_evaluation_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_evaluation_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_evaluation_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_evaluation_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_evaluation_route_adoption_manifest_checked": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_evaluation_route_adoption_manifest_checked",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_evaluation_route_adoption_manifest_valid": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_evaluation_route_adoption_manifest_valid",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_evaluation_route_adoption_row_checked": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_evaluation_route_adoption_row_checked",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_evaluation_route_adoption_row_valid": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_evaluation_route_adoption_row_valid",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_decision_policy_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_interactive_decision_policy_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_decision_policy_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_interactive_decision_policy_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_decision_policy_link_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_interactive_decision_policy_link_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_decision_policy_link_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_interactive_decision_policy_link_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_session_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_interactive_session_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_session_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_interactive_session_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_session_resource_response_status_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_interactive_session_resource_response_status_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_session_resource_response_status_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_interactive_session_resource_response_status_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_session_generic_prover_fields_checked": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_interactive_session_generic_prover_fields_checked",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_interactive_session_generic_prover_fields_valid": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_interactive_session_generic_prover_fields_valid",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_refinement_evidence_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_refinement_evidence_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_refinement_evidence_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_refinement_evidence_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_refinement_adapter_response_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_refinement_adapter_response_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_refinement_adapter_response_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_refinement_adapter_response_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_refinement_work_item_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_refinement_work_item_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_refinement_work_item_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_refinement_work_item_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_minimal_delta_decision_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_minimal_delta_decision_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_minimal_delta_decision_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_minimal_delta_decision_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_goal_plan_row_contract_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_goal_plan_row_contract_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_goal_plan_row_contract_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_goal_plan_row_contract_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_goal_plan_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_goal_plan_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_goal_plan_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_goal_plan_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_source_grounding_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_source_grounding_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_source_grounding_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_source_grounding_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_target_intake_row_contract_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_target_intake_row_contract_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_target_intake_row_contract_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_target_intake_row_contract_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_target_intake_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_target_intake_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_target_intake_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_target_intake_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_adapter_registry_audit_check_contract_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_adapter_registry_audit_check_contract_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_adapter_registry_audit_check_contract_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_adapter_registry_audit_check_contract_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_component_resource_registry_audit_check_contract_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_component_resource_registry_audit_check_contract_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_component_resource_registry_audit_check_contract_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_component_resource_registry_audit_check_contract_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_local_adapter_response_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_local_adapter_response_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_local_adapter_response_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_local_adapter_response_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_stability_audit_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_stability_audit_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_stability_audit_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_stability_audit_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_stability_resource_response_status_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_stability_resource_response_status_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_stability_resource_response_status_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_stability_resource_response_status_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_stability_generic_prover_fields_checked": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_route_stability_generic_prover_fields_checked",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_route_stability_generic_prover_fields_valid": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_route_stability_generic_prover_fields_valid",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_route_revision_overlay_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_revision_overlay_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_revision_overlay_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_revision_overlay_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_revision_resource_response_evidence_ref_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_revision_resource_response_evidence_ref_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_revision_resource_response_evidence_ref_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_revision_resource_response_evidence_ref_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_revision_resource_response_trace_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_revision_resource_response_trace_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_revision_resource_response_trace_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_revision_resource_response_trace_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_revision_resource_response_status_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_revision_resource_response_status_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_revision_resource_response_status_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_revision_resource_response_status_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_replan_handoff_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_replan_handoff_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_replan_handoff_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_replan_handoff_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_replan_handoff_audit_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_replan_handoff_audit_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_route_replan_handoff_audit_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_route_replan_handoff_audit_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_ablation_study_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_ablation_study_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_ablation_study_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_ablation_study_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_portable_plan_audit_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_portable_plan_audit_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_portable_plan_audit_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_portable_plan_audit_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_proof_state_triage_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_proof_state_triage_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_proof_state_triage_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_proof_state_triage_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_proof_state_triage_generic_prover_fields_checked": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_proof_state_triage_generic_prover_fields_checked",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_proof_state_triage_generic_prover_fields_valid": formalization_gap_planner_publication_bundle_audit_manifest.get(
                "n_optional_proof_state_triage_generic_prover_fields_valid",
                0,
            ),
            "formalization_gap_planner_publication_bundle_audit_optional_library_coverage_map_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_library_coverage_map_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_library_coverage_map_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_library_coverage_map_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_primitive_action_queue_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_primitive_action_queue_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_primitive_action_queue_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_primitive_action_queue_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_action_resource_plan_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_action_resource_plan_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_action_resource_plan_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_action_resource_plan_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_queue_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_queue_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_queue_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_queue_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_contract_alignment_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_contract_alignment_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_contract_alignment_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_contract_alignment_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_action_plan_ref_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_action_plan_ref_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_action_plan_ref_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_action_plan_ref_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_payload_identity_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_payload_identity_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_payload_identity_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_payload_identity_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_dispatch_spec_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_dispatch_spec_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_request_dispatch_spec_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_request_dispatch_spec_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_response_ledger_row_schema_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_response_ledger_row_schema_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_response_ledger_row_schema_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_response_ledger_row_schema_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_response_request_ref_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_response_request_ref_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_response_request_ref_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_response_request_ref_valid"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_response_contract_field_accounting_checked": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_response_contract_field_accounting_checked"
            ],
            "formalization_gap_planner_publication_bundle_audit_optional_resource_response_contract_field_accounting_valid": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_optional_resource_response_contract_field_accounting_valid"
            ],
            "formalization_gap_planner_publication_bundle_files": formalization_gap_planner_publication_bundle_audit_manifest[
                "n_bundle_files"
            ],
            "formal_verifier_replay_repair_packets": formal_verifier_replay_repair_manifest[
                "n_repair_packets"
            ],
            "formal_verifier_replay_repair_ok": formal_verifier_replay_repair_manifest["n_ok"],
            "formal_verifier_replay_repair_tactic_no_progress": formal_verifier_replay_repair_manifest[
                "n_tactic_no_progress"
            ],
            "formal_verifier_replay_repair_missing_identifier": formal_verifier_replay_repair_manifest[
                "n_missing_identifier"
            ],
            "formal_verifier_replay_repair_type_mismatch": formal_verifier_replay_repair_manifest[
                "n_type_mismatch"
            ],
            "formal_verifier_replay_repair_placeholder_or_gap": formal_verifier_replay_repair_manifest[
                "n_placeholder_or_gap"
            ],
            "formal_verifier_replay_repair_with_attempt": formal_verifier_replay_repair_manifest[
                "n_with_attempt"
            ],
            "formal_verifier_replay_repair_with_exact_subclaims": formal_verifier_replay_repair_manifest[
                "n_with_exact_subclaims"
            ],
            "formal_verifier_replay_repair_training_examples": formal_verifier_replay_repair_manifest[
                "n_training_examples"
            ],
            "formal_verifier_replay_repair_application_tasks": formal_verifier_replay_repair_application_manifest[
                "n_application_tasks"
            ],
            "formal_verifier_replay_repair_application_ok": formal_verifier_replay_repair_application_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_application_bridge_lemma": formal_verifier_replay_repair_application_manifest[
                "n_bridge_lemma_applications"
            ],
            "formal_verifier_replay_repair_application_import_or_declaration": formal_verifier_replay_repair_application_manifest[
                "n_import_or_declaration_applications"
            ],
            "formal_verifier_replay_repair_application_statement_alignment": formal_verifier_replay_repair_application_manifest[
                "n_statement_alignment_applications"
            ],
            "formal_verifier_replay_repair_application_with_source_statement": formal_verifier_replay_repair_application_manifest[
                "n_with_source_statement"
            ],
            "formal_verifier_replay_repair_application_with_artifact": formal_verifier_replay_repair_application_manifest[
                "n_with_artifact"
            ],
            "formal_verifier_replay_repair_application_training_examples": formal_verifier_replay_repair_application_manifest[
                "n_training_examples"
            ],
            "formal_verifier_replay_repair_application_validation_rows": formal_verifier_replay_repair_application_validation_manifest[
                "n_validation_rows"
            ],
            "formal_verifier_replay_repair_application_validation_ok": formal_verifier_replay_repair_application_validation_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_application_validation_static_ok": formal_verifier_replay_repair_application_validation_manifest[
                "n_static_ok"
            ],
            "formal_verifier_replay_repair_application_validation_placeholder_free": formal_verifier_replay_repair_application_validation_manifest[
                "n_placeholder_free"
            ],
            "formal_verifier_replay_repair_application_validation_non_evidence_boundary": formal_verifier_replay_repair_application_validation_manifest[
                "n_with_non_evidence_boundary"
            ],
            "formal_verifier_replay_repair_application_validation_local_lean_checked": formal_verifier_replay_repair_application_validation_manifest[
                "n_local_lean_checked"
            ],
            "formal_verifier_replay_repair_application_validation_local_lean_compiled": formal_verifier_replay_repair_application_validation_manifest[
                "n_local_lean_compiled"
            ],
            "formal_verifier_replay_repair_application_validation_all_local_lean_compiled": formal_verifier_replay_repair_application_validation_manifest[
                "all_local_lean_compiled"
            ],
            "formal_verifier_replay_repair_execution_queue_items": formal_verifier_replay_repair_execution_queue_manifest[
                "n_queue_items"
            ],
            "formal_verifier_replay_repair_execution_queue_ok": formal_verifier_replay_repair_execution_queue_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_execution_queue_ready": formal_verifier_replay_repair_execution_queue_manifest[
                "n_ready_for_patch"
            ],
            "formal_verifier_replay_repair_execution_queue_ready_local_lean": formal_verifier_replay_repair_execution_queue_manifest[
                "n_ready_local_lean_compiled"
            ],
            "formal_verifier_replay_repair_execution_queue_ready_static": formal_verifier_replay_repair_execution_queue_manifest[
                "n_ready_static_validated"
            ],
            "formal_verifier_replay_repair_execution_queue_blocked": formal_verifier_replay_repair_execution_queue_manifest[
                "n_blocked"
            ],
            "formal_verifier_replay_repair_execution_queue_placeholder_free": formal_verifier_replay_repair_execution_queue_manifest[
                "n_placeholder_free"
            ],
            "formal_verifier_replay_repair_prompt_packets": formal_verifier_replay_repair_prompt_packets_manifest[
                "n_prompt_packets"
            ],
            "formal_verifier_replay_repair_prompt_packets_ok": formal_verifier_replay_repair_prompt_packets_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_prompt_packets_with_scaffold_source": formal_verifier_replay_repair_prompt_packets_manifest[
                "n_with_scaffold_source"
            ],
            "formal_verifier_replay_repair_prompt_packets_with_command_plan": formal_verifier_replay_repair_prompt_packets_manifest[
                "n_with_command_plan"
            ],
            "formal_verifier_replay_repair_prompt_packets_local_lean_compiled_scaffold": formal_verifier_replay_repair_prompt_packets_manifest[
                "n_local_lean_compiled_scaffold"
            ],
            "formal_verifier_replay_repair_patch_autoworker_responses": formal_verifier_replay_repair_patch_autoworker_manifest[
                "n_responses"
            ],
            "formal_verifier_replay_repair_patch_autoworker_ok": formal_verifier_replay_repair_patch_autoworker_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_autoworker_patch_proposals": formal_verifier_replay_repair_patch_autoworker_manifest[
                "n_patch_proposals"
            ],
            "formal_verifier_replay_repair_patch_autoworker_kernel_verified": formal_verifier_replay_repair_patch_autoworker_manifest[
                "n_kernel_verified"
            ],
            "formal_verifier_replay_repair_patch_autoworker_artifacts": formal_verifier_replay_repair_patch_autoworker_manifest[
                "n_patch_artifacts"
            ],
            "formal_verifier_replay_repair_patch_response_validation_rows": formal_verifier_replay_repair_patch_response_validation_manifest[
                "n_response_validation_rows"
            ],
            "formal_verifier_replay_repair_patch_response_validation_responses": formal_verifier_replay_repair_patch_response_validation_manifest[
                "n_response_present"
            ],
            "formal_verifier_replay_repair_patch_response_validation_awaiting": formal_verifier_replay_repair_patch_response_validation_manifest[
                "n_awaiting_worker_response"
            ],
            "formal_verifier_replay_repair_patch_response_validation_contract_ok": formal_verifier_replay_repair_patch_response_validation_manifest[
                "n_contract_ok"
            ],
            "formal_verifier_replay_repair_patch_response_validation_patch_proposal_not_proof": formal_verifier_replay_repair_patch_response_validation_manifest[
                "n_patch_proposal_not_proof"
            ],
            "formal_verifier_replay_repair_patch_response_validation_accepted_full_route_kernel_verified": formal_verifier_replay_repair_patch_response_validation_manifest[
                "n_accepted_full_route_kernel_verified"
            ],
            "formal_verifier_replay_repair_patch_response_validation_rejected": formal_verifier_replay_repair_patch_response_validation_manifest[
                "n_rejected"
            ],
            "formal_verifier_replay_repair_patch_response_validation_ok": formal_verifier_replay_repair_patch_response_validation_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_response_promotion_rows": formal_verifier_replay_repair_patch_response_promotion_manifest[
                "n_promotion_rows"
            ],
            "formal_verifier_replay_repair_patch_response_promotion_ready": formal_verifier_replay_repair_patch_response_promotion_manifest[
                "n_ready_for_proof_promotion"
            ],
            "formal_verifier_replay_repair_patch_response_promotion_awaiting": formal_verifier_replay_repair_patch_response_promotion_manifest[
                "n_awaiting_worker_response"
            ],
            "formal_verifier_replay_repair_patch_response_promotion_patch_needs_replay": formal_verifier_replay_repair_patch_response_promotion_manifest[
                "n_patch_proposal_needs_replay_calibration"
            ],
            "formal_verifier_replay_repair_patch_response_promotion_blocked": formal_verifier_replay_repair_patch_response_promotion_manifest[
                "n_blocked"
            ],
            "formal_verifier_replay_repair_patch_response_promotion_ok": formal_verifier_replay_repair_patch_response_promotion_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_rerun_queue_items": formal_verifier_replay_repair_patch_rerun_queue_manifest[
                "n_rerun_queue_items"
            ],
            "formal_verifier_replay_repair_patch_rerun_queue_ready": formal_verifier_replay_repair_patch_rerun_queue_manifest[
                "n_ready_for_patch_replay"
            ],
            "formal_verifier_replay_repair_patch_rerun_queue_blocked": formal_verifier_replay_repair_patch_rerun_queue_manifest[
                "n_blocked"
            ],
            "formal_verifier_replay_repair_patch_rerun_queue_with_artifact": formal_verifier_replay_repair_patch_rerun_queue_manifest[
                "n_with_patched_artifact"
            ],
            "formal_verifier_replay_repair_patch_rerun_queue_with_commands": formal_verifier_replay_repair_patch_rerun_queue_manifest[
                "n_with_rerun_commands"
            ],
            "formal_verifier_replay_repair_patch_rerun_queue_ok": formal_verifier_replay_repair_patch_rerun_queue_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_rerun_attempts": formal_verifier_replay_repair_patch_rerun_attempt_manifest[
                "n_rerun_attempt_rows"
            ],
            "formal_verifier_replay_repair_patch_rerun_attempts_local_lean_checked": formal_verifier_replay_repair_patch_rerun_attempt_manifest[
                "n_local_lean_checked"
            ],
            "formal_verifier_replay_repair_patch_rerun_attempts_local_lean_compiled": formal_verifier_replay_repair_patch_rerun_attempt_manifest[
                "n_local_lean_compiled"
            ],
            "formal_verifier_replay_repair_patch_rerun_attempts_patch_markers": formal_verifier_replay_repair_patch_rerun_attempt_manifest[
                "n_with_patch_proposal_marker"
            ],
            "formal_verifier_replay_repair_patch_rerun_attempts_residual_gaps": formal_verifier_replay_repair_patch_rerun_attempt_manifest[
                "n_with_residual_formal_gaps"
            ],
            "formal_verifier_replay_repair_patch_rerun_attempts_ok": formal_verifier_replay_repair_patch_rerun_attempt_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_rerun_calibration_rows": formal_verifier_replay_repair_patch_rerun_calibration_manifest[
                "n_calibration_rows"
            ],
            "formal_verifier_replay_repair_patch_rerun_calibration_attempted": formal_verifier_replay_repair_patch_rerun_calibration_manifest[
                "n_attempted"
            ],
            "formal_verifier_replay_repair_patch_rerun_calibration_compiled": formal_verifier_replay_repair_patch_rerun_calibration_manifest[
                "n_local_lean_compiled"
            ],
            "formal_verifier_replay_repair_patch_rerun_calibration_full_route_kernel_verified": formal_verifier_replay_repair_patch_rerun_calibration_manifest[
                "n_full_route_kernel_verified"
            ],
            "formal_verifier_replay_repair_patch_rerun_calibration_compiled_patch_proposal_not_proof": formal_verifier_replay_repair_patch_rerun_calibration_manifest[
                "n_compiled_patch_proposal_not_proof"
            ],
            "formal_verifier_replay_repair_patch_rerun_calibration_compiled_with_residual_gaps": formal_verifier_replay_repair_patch_rerun_calibration_manifest[
                "n_compiled_with_residual_gaps"
            ],
            "formal_verifier_replay_repair_patch_rerun_calibration_ok": formal_verifier_replay_repair_patch_rerun_calibration_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_obligations": formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "n_residual_obligation_rows"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_routes": formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "n_routes_with_residual_obligations"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_unique_gaps": formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "n_unique_residual_gaps"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_exact_reuse": formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "n_exact_proof_bank_reuse"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_bridge_chain": formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "n_compose_existing_bridge_chain"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_minimal_wrapper": formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "n_add_minimal_wrapper"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_design_bridge": formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "n_design_bridge_lemma"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_source_discovery": formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "n_source_discovery_needed"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_ok": formal_verifier_replay_repair_patch_rerun_residual_obligation_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets": formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest[
                "n_prompt_packets"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_ok": formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_with_artifact_context": formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest[
                "n_with_patched_artifact_context"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_with_output_contract": formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest[
                "n_with_output_contract"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_exact_reuse": formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest[
                "n_exact_reuse_packets"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_bridge_chain": formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest[
                "n_bridge_chain_packets"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_source_discovery": formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest[
                "n_source_discovery_packets"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_responses": formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest[
                "n_responses"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_ok": formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_patch_proposals": formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest[
                "n_residual_patch_proposals"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_source_discovery": formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest[
                "n_source_discovery_responses"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_kernel_verified": formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest[
                "n_kernel_verified"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_artifacts": formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest[
                "n_patch_artifacts"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_rows": formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "n_response_validation_rows"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_responses": formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "n_response_present"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_awaiting": formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "n_awaiting_worker_response"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_contract_ok": formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "n_contract_ok"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_patch_proposal_not_proof": formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "n_residual_patch_proposal_not_proof"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_source_discovery": formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "n_source_discovery_responses"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_accepted_full_route_kernel_verified": formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "n_accepted_full_route_kernel_verified"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_rejected": formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "n_rejected"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_ok": formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest[
                "n_ok"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_items": formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest[
                "n_followup_items"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_ready": formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest[
                "n_ready"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_blocked": formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest[
                "n_blocked"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_patch_rerun": formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest[
                "n_patch_rerun_items"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_source_discovery": formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest[
                "n_source_discovery_items"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_with_artifact": formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest[
                "n_with_artifact"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_with_source_queries": formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest[
                "n_with_source_queries"
            ],
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_ok": formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_strategy_plan_rows": formal_verifier_agentic_proof_strategy_plan_manifest[
                "n_strategy_rows"
            ],
            "formal_verifier_agentic_proof_strategy_plan_ready": formal_verifier_agentic_proof_strategy_plan_manifest[
                "n_ready"
            ],
            "formal_verifier_agentic_proof_strategy_plan_patch_evolve_blocks": formal_verifier_agentic_proof_strategy_plan_manifest[
                "n_patch_evolve_blocks"
            ],
            "formal_verifier_agentic_proof_strategy_plan_source_discovery_cache_items": formal_verifier_agentic_proof_strategy_plan_manifest[
                "n_source_discovery_cache_items"
            ],
            "formal_verifier_agentic_proof_strategy_plan_with_live_tool_plan": formal_verifier_agentic_proof_strategy_plan_manifest[
                "n_with_live_tool_plan"
            ],
            "formal_verifier_agentic_proof_strategy_plan_ok": formal_verifier_agentic_proof_strategy_plan_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_items": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_candidate_queue_items"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_ready": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_ready"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_blocked": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_blocked"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_patch_candidates": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_patch_candidate_items"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_source_discovery_candidates": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_source_discovery_candidate_items"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_kernel_overlay_candidates": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_kernel_overlay_candidate_items"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_with_candidate_database_key": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_with_candidate_database_key"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_with_live_evaluator_pool": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_with_live_evaluator_pool"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_with_kernel_overlay_context": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_with_kernel_overlay_context"
            ],
            "formal_verifier_agentic_proof_candidate_evaluation_queue_ok": formal_verifier_agentic_proof_candidate_evaluation_queue_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_safety_policy_rows": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_safety_policy_rows"
            ],
            "formal_verifier_agentic_proof_safety_policy_ready": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_ready"
            ],
            "formal_verifier_agentic_proof_safety_policy_blocked": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_blocked"
            ],
            "formal_verifier_agentic_proof_safety_policy_patch_bounded_edit": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_patch_bounded_edit_policies"
            ],
            "formal_verifier_agentic_proof_safety_policy_source_validation": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_source_validation_policies"
            ],
            "formal_verifier_agentic_proof_safety_policy_with_goal_cache_key": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_with_goal_cache_key"
            ],
            "formal_verifier_agentic_proof_safety_policy_with_anti_cheat_checks": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_with_anti_cheat_checks"
            ],
            "formal_verifier_agentic_proof_safety_policy_with_safeverify_gate": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_with_safeverify_gate"
            ],
            "formal_verifier_agentic_proof_safety_policy_with_kernel_overlay_context": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_with_kernel_overlay_context"
            ],
            "formal_verifier_agentic_proof_safety_policy_ok": formal_verifier_agentic_proof_safety_policy_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_attempt_population_entries": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_population_entries"
            ],
            "formal_verifier_agentic_proof_attempt_population_ready": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_ready"
            ],
            "formal_verifier_agentic_proof_attempt_population_blocked": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_blocked"
            ],
            "formal_verifier_agentic_proof_attempt_population_patch_entries": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_patch_population_entries"
            ],
            "formal_verifier_agentic_proof_attempt_population_source_entries": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_source_population_entries"
            ],
            "formal_verifier_agentic_proof_attempt_population_with_goal_cache_key": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_with_goal_cache_key"
            ],
            "formal_verifier_agentic_proof_attempt_population_with_lineage_key": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_with_lineage_key"
            ],
            "formal_verifier_agentic_proof_attempt_population_with_sampling_weight": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_with_sampling_weight"
            ],
            "formal_verifier_agentic_proof_attempt_population_with_kernel_overlay_context": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_with_kernel_overlay_context"
            ],
            "formal_verifier_agentic_proof_attempt_population_untried": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_untried"
            ],
            "formal_verifier_agentic_proof_attempt_population_ok": formal_verifier_agentic_proof_attempt_population_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_execution_queue_items": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_execution_queue_items"
            ],
            "formal_verifier_agentic_proof_execution_queue_ready": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_ready"
            ],
            "formal_verifier_agentic_proof_execution_queue_blocked": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_blocked"
            ],
            "formal_verifier_agentic_proof_execution_queue_patch_items": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_patch_execution_items"
            ],
            "formal_verifier_agentic_proof_execution_queue_source_items": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_source_execution_items"
            ],
            "formal_verifier_agentic_proof_execution_queue_with_candidate_artifact_path": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_with_candidate_artifact_path"
            ],
            "formal_verifier_agentic_proof_execution_queue_with_live_tool_plan": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_with_live_tool_plan"
            ],
            "formal_verifier_agentic_proof_execution_queue_with_proof_route_dag_plan": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_with_proof_route_dag_plan"
            ],
            "formal_verifier_agentic_proof_execution_queue_with_verified_sketch_gate": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_with_verified_sketch_gate"
            ],
            "formal_verifier_agentic_proof_execution_queue_with_blueprint_export_plan": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_with_blueprint_export_plan"
            ],
            "formal_verifier_agentic_proof_execution_queue_with_kernel_overlay_context": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_with_kernel_overlay_context"
            ],
            "formal_verifier_agentic_proof_execution_queue_live_goal_requested": formal_verifier_agentic_proof_execution_queue_manifest.get(
                "n_live_goal_requested", 0
            ),
            "formal_verifier_agentic_proof_execution_queue_live_goal_location_ready": formal_verifier_agentic_proof_execution_queue_manifest.get(
                "n_live_goal_location_ready", 0
            ),
            "formal_verifier_agentic_proof_execution_queue_needs_target_location": formal_verifier_agentic_proof_execution_queue_manifest.get(
                "n_needs_target_location", 0
            ),
            "formal_verifier_agentic_proof_execution_queue_candidate_artifact_exists": formal_verifier_agentic_proof_execution_queue_manifest.get(
                "n_candidate_artifact_exists", 0
            ),
            "formal_verifier_agentic_proof_execution_queue_ok": formal_verifier_agentic_proof_execution_queue_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_execution_materializer_rows": formal_verifier_agentic_proof_execution_materializer_manifest[
                "n_materializer_rows"
            ],
            "formal_verifier_agentic_proof_execution_materializer_artifacts": formal_verifier_agentic_proof_execution_materializer_manifest[
                "n_materialized_artifacts"
            ],
            "formal_verifier_agentic_proof_execution_materializer_new_artifacts": formal_verifier_agentic_proof_execution_materializer_manifest[
                "n_new_artifacts"
            ],
            "formal_verifier_agentic_proof_execution_materializer_live_goal_location_ready": formal_verifier_agentic_proof_execution_materializer_manifest[
                "n_live_goal_location_ready"
            ],
            "formal_verifier_agentic_proof_execution_materializer_live_proof_state_requests": formal_verifier_agentic_proof_execution_materializer_manifest[
                "n_live_proof_state_requests"
            ],
            "formal_verifier_agentic_proof_execution_materializer_lean_lsp_mcp_ready_requests": formal_verifier_agentic_proof_execution_materializer_manifest[
                "n_lean_lsp_mcp_ready_requests"
            ],
            "formal_verifier_agentic_proof_execution_materializer_kernel_verified": formal_verifier_agentic_proof_execution_materializer_manifest[
                "n_kernel_verified"
            ],
            "formal_verifier_agentic_proof_execution_materializer_ok": formal_verifier_agentic_proof_execution_materializer_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_execution_artifact_verifier_enabled": formal_verifier_agentic_proof_execution_artifact_verifier_manifest.get(
                "enabled", config.verify_agentic_artifacts
            ),
            "formal_verifier_agentic_proof_execution_artifact_verifier_rows": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_verifier_rows"
            ],
            "formal_verifier_agentic_proof_execution_artifact_verifier_checked": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_local_lean_checked"
            ],
            "formal_verifier_agentic_proof_execution_artifact_verifier_compiled": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_local_lean_compiled"
            ],
            "formal_verifier_agentic_proof_execution_artifact_kernel_verified": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_artifact_kernel_verified"
            ],
            "formal_verifier_agentic_proof_execution_source_theorem_kernel_verified": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_source_theorem_kernel_verified"
            ],
            "formal_verifier_agentic_proof_execution_artifact_forbidden_token_failures": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_forbidden_token_failures"
            ],
            "formal_verifier_agentic_proof_execution_artifact_transcript_paths": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_execution_transcript_paths"
            ],
            "formal_verifier_agentic_proof_execution_artifact_transcript_events_written": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_execution_transcript_events_written"
            ],
            "formal_verifier_agentic_proof_execution_artifact_live_proof_state_requests": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_live_proof_state_requests"
            ],
            "formal_verifier_agentic_proof_execution_artifact_live_proof_state_request_valid": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_live_proof_state_request_valid"
            ],
            "formal_verifier_agentic_proof_execution_artifact_lean_lsp_mcp_ready_requests": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_lean_lsp_mcp_ready_requests"
            ],
            "formal_verifier_agentic_proof_execution_artifact_live_proof_state_request_failures": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_live_proof_state_request_failures"
            ],
            "formal_verifier_agentic_proof_execution_artifact_verifier_ok": formal_verifier_agentic_proof_execution_artifact_verifier_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_execution_artifact_proof_evidence_status": formal_verifier_agentic_proof_execution_artifact_verifier_manifest.get(
                "proof_evidence_status", ""
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_rows": formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest[
                "n_promotion_rows"
            ],
            "formal_verifier_agentic_proof_source_theorem_promotion_artifact_kernel_inputs": formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest[
                "n_artifact_kernel_verified_inputs"
            ],
            "formal_verifier_agentic_proof_source_theorem_promotion_ready": formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest[
                "n_ready_for_source_theorem_integration"
            ],
            "formal_verifier_agentic_proof_source_theorem_promotion_needs_target_resolution": formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest[
                "n_needs_source_theorem_target_resolution"
            ],
            "formal_verifier_agentic_proof_source_theorem_promotion_source_theorem_kernel_verified": formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest[
                "n_source_theorem_kernel_verified"
            ],
            "formal_verifier_agentic_proof_source_theorem_promotion_needs_source_target": formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest[
                "n_needs_source_theorem_target"
            ],
            "formal_verifier_agentic_proof_source_theorem_promotion_blocked_artifact_failed": formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest[
                "n_blocked_artifact_verification_failed"
            ],
            "formal_verifier_agentic_proof_source_theorem_promotion_ok": formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_source_theorem_promotion_proof_evidence_status": formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.get(
                "proof_evidence_status", ""
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_rows": formal_verifier_agentic_proof_source_theorem_target_resolution_manifest[
                "n_target_resolution_rows"
            ],
            "formal_verifier_agentic_proof_source_theorem_target_resolution_resolved": formal_verifier_agentic_proof_source_theorem_target_resolution_manifest[
                "n_resolved_source_theorem_targets"
            ],
            "formal_verifier_agentic_proof_source_theorem_target_resolution_needs_route_match": formal_verifier_agentic_proof_source_theorem_target_resolution_manifest[
                "n_needs_route_ledger_match"
            ],
            "formal_verifier_agentic_proof_source_theorem_target_resolution_already_known": formal_verifier_agentic_proof_source_theorem_target_resolution_manifest[
                "n_already_source_theorem_target_known"
            ],
            "formal_verifier_agentic_proof_source_theorem_target_resolution_blocked_artifact_kernel": formal_verifier_agentic_proof_source_theorem_target_resolution_manifest[
                "n_blocked_artifact_kernel_required"
            ],
            "formal_verifier_agentic_proof_source_theorem_target_resolution_overlays": formal_verifier_agentic_proof_source_theorem_target_resolution_manifest[
                "n_overlay_rows"
            ],
            "formal_verifier_agentic_proof_source_theorem_target_resolution_ok": formal_verifier_agentic_proof_source_theorem_target_resolution_manifest[
                "n_ok"
            ],
            "formal_verifier_agentic_proof_source_theorem_target_resolution_proof_evidence_status": formal_verifier_agentic_proof_source_theorem_target_resolution_manifest.get(
                "proof_evidence_status", ""
            ),
            "proof_bank_actions_high_priority": proof_bank_action_manifest["by_priority"].get("high", 0),
            "proof_bank_actions_medium_priority": proof_bank_action_manifest["by_priority"].get("medium", 0),
            "proof_bank_actions_low_priority": proof_bank_action_manifest["by_priority"].get("low", 0),
            "primitive_source_coverage_primitives": primitive_source_coverage_manifest["n_primitives"],
            "primitive_source_coverage_exact_proof_bank_obligation_available": primitive_source_coverage_manifest[
                "n_exact_proof_bank_obligation_available"
            ],
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
            "primitive_source_coverage_external_search_policy": primitive_source_coverage_manifest[
                "external_search_policy"
            ],
            "primitive_source_coverage_external_queries": primitive_source_coverage_manifest[
                "n_external_source_queries"
            ],
            "primitive_source_coverage_external_skipped_supported": primitive_source_coverage_manifest[
                "n_external_source_search_skipped_supported"
            ],
            "primitive_source_coverage_compose_existing_bridge_chain": primitive_source_coverage_manifest[
                "n_compose_existing_bridge_chain"
            ],
            "primitive_source_coverage_reuse_exact_proof_bank_obligation": primitive_source_coverage_manifest[
                "n_reuse_exact_proof_bank_obligation"
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
            "claim_ledger_claims": claim_ledger_manifest["n_claims"],
            "claim_ledger_ok": claim_ledger_manifest["n_ok"],
            "claim_ledger_questions": claim_ledger_manifest["n_questions"],
            "claim_ledger_formal_gaps": claim_ledger_manifest["by_status"].get("FORMAL_GAP", 0),
            "claim_ledger_kernel_proved_subclaims": claim_ledger_manifest["by_status"].get(
                "KERNEL_PROVED_SUBCLAIM",
                0,
            ),
            "claim_ledger_mock_proved_subclaims": claim_ledger_manifest["by_status"].get(
                "MOCK_PROVED_SUBCLAIM",
                0,
            ),
            "claim_ledger_simulation_supported": claim_ledger_manifest["by_status"].get(
                "SIMULATION_SUPPORTED",
                0,
            ),
            "claim_ledger_simulation_flagged": claim_ledger_manifest["by_status"].get(
                "SIMULATION_FLAGGED",
                0,
            ),
            "claim_ledger_revision_queued": claim_ledger_manifest["by_status"].get("REVISION_QUEUED", 0),
            "claim_ledger_kernel_overlay_upgrades": claim_ledger_manifest["n_kernel_overlay_upgrades"],
            "claim_ledger_proof_audit_overlay_enabled": claim_ledger_manifest["proof_audit_overlay_enabled"],
            "claim_ledger_repair_response_promotion_overlay_enabled": claim_ledger_manifest[
                "repair_response_promotion_overlay_enabled"
            ],
            "claim_ledger_repair_response_promotion_overlay_rows": claim_ledger_manifest[
                "n_repair_response_promotion_overlay_rows"
            ],
            "claim_ledger_repair_response_promotion_upgrades": claim_ledger_manifest[
                "n_repair_response_promotion_upgrades"
            ],
            "claim_ledger_formal_gap_exact_proof_bank_reuse_rows": claim_ledger_manifest[
                "n_formal_gap_rows_with_exact_proof_bank_reuse"
            ],
            "claim_ledger_exact_proof_bank_reuse_links": claim_ledger_manifest[
                "n_exact_proof_bank_reuse_links"
            ],
            "claim_ledger_actions": claim_ledger_action_manifest["n_actions"],
            "claim_ledger_actions_ok": claim_ledger_action_manifest["n_ok"],
            "claim_ledger_actions_exact_proof_bank_reuse": claim_ledger_action_manifest[
                "n_exact_proof_bank_reuse_actions"
            ],
            "claim_ledger_actions_formal_verifier": claim_ledger_action_manifest["by_owner"].get(
                "formal_verifier",
                0,
            ),
            "claim_ledger_actions_theory_developer": claim_ledger_action_manifest["by_owner"].get(
                "theory_developer",
                0,
            ),
            "claim_ledger_actions_algorithm_engineer": claim_ledger_action_manifest["by_owner"].get(
                "algorithm_engineer",
                0,
            ),
            "claim_ledger_actions_simulator_agent": claim_ledger_action_manifest["by_owner"].get(
                "simulator_agent",
                0,
            ),
            "claim_ledger_actions_research_coordinator": claim_ledger_action_manifest["by_owner"].get(
                "research_coordinator",
                0,
            ),
            "stat_claim_certificate_targets": stat_claim_certificate_manifest["n_targets"],
            "stat_claim_certificate_targets_ok": stat_claim_certificate_manifest["n_ok"],
            "stat_claim_certificate_checker_families": stat_claim_certificate_manifest[
                "n_checker_families"
            ],
            "stat_claim_certificate_proof_evidence_ready": stat_claim_certificate_manifest[
                "n_proof_evidence_ready"
            ],
            "stat_claim_certificate_proof_evidence_status": stat_claim_certificate_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_conformal_targets": stat_claim_certificate_manifest[
                "by_family"
            ].get("conformal_coverage_certificate", 0),
            "stat_claim_certificate_randomization_targets": stat_claim_certificate_manifest[
                "by_family"
            ].get("randomization_variance_certificate", 0),
            "stat_claim_certificate_multiple_testing_targets": stat_claim_certificate_manifest[
                "by_family"
            ].get("multiple_testing_threshold_certificate", 0),
            "stat_claim_certificate_privacy_targets": stat_claim_certificate_manifest[
                "by_family"
            ].get("privacy_accountant_certificate", 0),
            "stat_claim_certificate_kkt_targets": stat_claim_certificate_manifest["by_family"].get(
                "kkt_optimality_certificate",
                0,
            ),
            "stat_claim_certificate_checker_obligations": stat_claim_certificate_checker_manifest[
                "n_obligations"
            ],
            "stat_claim_certificate_checker_verified": stat_claim_certificate_checker_manifest[
                "n_verified"
            ],
            "stat_claim_certificate_checker_kernel_verified": stat_claim_certificate_checker_manifest[
                "n_kernel_verified"
            ],
            "stat_claim_certificate_checker_non_kernel_verified": stat_claim_certificate_checker_manifest[
                "n_non_kernel_verified"
            ],
            "stat_claim_certificate_checker_all_kernel_verified": stat_claim_certificate_checker_manifest[
                "all_kernel_verified"
            ],
            "stat_claim_certificate_checker_proof_evidence_status": stat_claim_certificate_checker_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_readiness_targets": stat_claim_certificate_readiness_manifest[
                "n_targets"
            ],
            "stat_claim_certificate_readiness_ok": stat_claim_certificate_readiness_manifest[
                "n_ok"
            ],
            "stat_claim_certificate_readiness_checker_available": stat_claim_certificate_readiness_manifest[
                "n_checker_available"
            ],
            "stat_claim_certificate_readiness_checker_verified": stat_claim_certificate_readiness_manifest[
                "n_checker_verified"
            ],
            "stat_claim_certificate_readiness_checker_kernel_verified": stat_claim_certificate_readiness_manifest[
                "n_checker_kernel_verified"
            ],
            "stat_claim_certificate_readiness_ready_for_witness_validation": stat_claim_certificate_readiness_manifest[
                "n_ready_for_witness_validation"
            ],
            "stat_claim_certificate_readiness_missing_checker": stat_claim_certificate_readiness_manifest[
                "n_missing_checker"
            ],
            "stat_claim_certificate_readiness_non_kernel_checker": stat_claim_certificate_readiness_manifest[
                "n_non_kernel_checker"
            ],
            "stat_claim_certificate_readiness_proof_evidence_status": stat_claim_certificate_readiness_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_witness_queue_tasks": stat_claim_certificate_witness_queue_manifest[
                "n_tasks"
            ],
            "stat_claim_certificate_witness_queue_ok": stat_claim_certificate_witness_queue_manifest[
                "n_ok"
            ],
            "stat_claim_certificate_witness_queue_blocked": stat_claim_certificate_witness_queue_manifest[
                "n_blocked"
            ],
            "stat_claim_certificate_witness_queue_missing_checker": stat_claim_certificate_witness_queue_manifest[
                "n_missing_checker"
            ],
            "stat_claim_certificate_witness_queue_non_kernel_checker": stat_claim_certificate_witness_queue_manifest[
                "n_non_kernel_checker"
            ],
            "stat_claim_certificate_witness_queue_proof_evidence_status": stat_claim_certificate_witness_queue_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_witness_materializer_drafts": stat_claim_certificate_witness_materializer_manifest[
                "n_drafts"
            ],
            "stat_claim_certificate_witness_materializer_ok": stat_claim_certificate_witness_materializer_manifest[
                "n_ok"
            ],
            "stat_claim_certificate_witness_materializer_unfilled": stat_claim_certificate_witness_materializer_manifest[
                "n_unfilled"
            ],
            "stat_claim_certificate_witness_materializer_ready_for_checker_validation": stat_claim_certificate_witness_materializer_manifest[
                "n_ready_for_checker_validation"
            ],
            "stat_claim_certificate_witness_materializer_proof_evidence_status": stat_claim_certificate_witness_materializer_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_witness_prompt_packets": stat_claim_certificate_witness_prompt_packets_manifest[
                "n_prompt_packets"
            ],
            "stat_claim_certificate_witness_prompt_packets_ok": stat_claim_certificate_witness_prompt_packets_manifest[
                "n_ok"
            ],
            "stat_claim_certificate_witness_prompt_packets_with_source_evidence_paths": stat_claim_certificate_witness_prompt_packets_manifest[
                "n_with_source_evidence_paths"
            ],
            "stat_claim_certificate_witness_prompt_packets_with_output_contract": stat_claim_certificate_witness_prompt_packets_manifest[
                "n_with_output_contract"
            ],
            "stat_claim_certificate_witness_prompt_packets_with_checker_contract": stat_claim_certificate_witness_prompt_packets_manifest[
                "n_with_checker_contract"
            ],
            "stat_claim_certificate_witness_prompt_packets_proof_evidence_status": stat_claim_certificate_witness_prompt_packets_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_witness_context_packets": stat_claim_certificate_witness_context_packets_manifest[
                "n_context_packets"
            ],
            "stat_claim_certificate_witness_context_packets_ok": stat_claim_certificate_witness_context_packets_manifest[
                "n_ok"
            ],
            "stat_claim_certificate_witness_context_packets_with_context": stat_claim_certificate_witness_context_packets_manifest[
                "n_with_context"
            ],
            "stat_claim_certificate_witness_context_packets_source_paths": stat_claim_certificate_witness_context_packets_manifest[
                "n_source_paths"
            ],
            "stat_claim_certificate_witness_context_packets_resolved_source_paths": stat_claim_certificate_witness_context_packets_manifest[
                "n_resolved_source_paths"
            ],
            "stat_claim_certificate_witness_context_packets_missing_source_paths": stat_claim_certificate_witness_context_packets_manifest[
                "n_missing_source_paths"
            ],
            "stat_claim_certificate_witness_context_packets_snippets": stat_claim_certificate_witness_context_packets_manifest[
                "n_snippets"
            ],
            "stat_claim_certificate_witness_context_packets_field_hints": stat_claim_certificate_witness_context_packets_manifest[
                "n_field_context_hints"
            ],
            "stat_claim_certificate_witness_context_packets_field_direct_matches": stat_claim_certificate_witness_context_packets_manifest[
                "n_field_context_direct_matches"
            ],
            "stat_claim_certificate_witness_context_packets_field_fallbacks": stat_claim_certificate_witness_context_packets_manifest[
                "n_field_context_fallbacks"
            ],
            "stat_claim_certificate_witness_context_packets_field_no_context": stat_claim_certificate_witness_context_packets_manifest[
                "n_field_context_no_context"
            ],
            "stat_claim_certificate_witness_context_packets_proof_evidence_status": stat_claim_certificate_witness_context_packets_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_witness_context_triage_rows": stat_claim_certificate_witness_context_triage_manifest[
                "n_triage_rows"
            ],
            "stat_claim_certificate_witness_context_triage_ok": stat_claim_certificate_witness_context_triage_manifest[
                "n_ok"
            ],
            "stat_claim_certificate_witness_context_triage_worker_ready": stat_claim_certificate_witness_context_triage_manifest[
                "n_worker_ready"
            ],
            "stat_claim_certificate_witness_context_triage_source_review_required": stat_claim_certificate_witness_context_triage_manifest[
                "n_source_review_required"
            ],
            "stat_claim_certificate_witness_context_triage_blocked_missing_context": stat_claim_certificate_witness_context_triage_manifest[
                "n_blocked_missing_context"
            ],
            "stat_claim_certificate_witness_context_triage_direct_fields": stat_claim_certificate_witness_context_triage_manifest[
                "n_direct_match_fields"
            ],
            "stat_claim_certificate_witness_context_triage_fallback_fields": stat_claim_certificate_witness_context_triage_manifest[
                "n_fallback_context_fields"
            ],
            "stat_claim_certificate_witness_context_triage_no_context_fields": stat_claim_certificate_witness_context_triage_manifest[
                "n_no_context_fields"
            ],
            "stat_claim_certificate_witness_context_triage_missing_source_paths": stat_claim_certificate_witness_context_triage_manifest[
                "n_missing_source_paths"
            ],
            "stat_claim_certificate_witness_context_triage_proof_evidence_status": stat_claim_certificate_witness_context_triage_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_witness_response_validation_rows": stat_claim_certificate_witness_response_validation_manifest[
                "n_response_validation_rows"
            ],
            "stat_claim_certificate_witness_response_validation_responses": stat_claim_certificate_witness_response_validation_manifest[
                "n_responses"
            ],
            "stat_claim_certificate_witness_response_validation_awaiting": stat_claim_certificate_witness_response_validation_manifest[
                "n_awaiting_worker_output"
            ],
            "stat_claim_certificate_witness_response_validation_missing_worker_outputs": stat_claim_certificate_witness_response_validation_manifest[
                "n_missing_worker_outputs"
            ],
            "stat_claim_certificate_witness_response_validation_contract_ok": stat_claim_certificate_witness_response_validation_manifest[
                "n_contract_ok"
            ],
            "stat_claim_certificate_witness_response_validation_accepted_for_draft_update": stat_claim_certificate_witness_response_validation_manifest[
                "n_accepted_for_draft_update"
            ],
            "stat_claim_certificate_witness_response_validation_incomplete": stat_claim_certificate_witness_response_validation_manifest[
                "n_incomplete"
            ],
            "stat_claim_certificate_witness_response_validation_missing_source_evidence": stat_claim_certificate_witness_response_validation_manifest[
                "n_missing_source_evidence"
            ],
            "stat_claim_certificate_witness_response_validation_open_semantic_gap_rows": stat_claim_certificate_witness_response_validation_manifest[
                "n_open_semantic_gap_rows"
            ],
            "stat_claim_certificate_witness_response_validation_proof_overclaim_rows": stat_claim_certificate_witness_response_validation_manifest[
                "n_proof_overclaim_rows"
            ],
            "stat_claim_certificate_witness_response_validation_unknown_prompt_rows": stat_claim_certificate_witness_response_validation_manifest[
                "n_unknown_prompt_rows"
            ],
            "stat_claim_certificate_witness_response_validation_ok": stat_claim_certificate_witness_response_validation_manifest[
                "n_ok"
            ],
            "stat_claim_certificate_witness_response_validation_proof_evidence_status": stat_claim_certificate_witness_response_validation_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_witness_response_apply_drafts": stat_claim_certificate_witness_response_apply_manifest[
                "n_drafts"
            ],
            "stat_claim_certificate_witness_response_apply_ok": stat_claim_certificate_witness_response_apply_manifest[
                "n_ok"
            ],
            "stat_claim_certificate_witness_response_apply_applied": stat_claim_certificate_witness_response_apply_manifest[
                "n_worker_response_applied"
            ],
            "stat_claim_certificate_witness_response_apply_accepted_for_draft_update": stat_claim_certificate_witness_response_apply_manifest[
                "n_accepted_for_draft_update"
            ],
            "stat_claim_certificate_witness_response_apply_awaiting": stat_claim_certificate_witness_response_apply_manifest[
                "n_awaiting_worker_output"
            ],
            "stat_claim_certificate_witness_response_apply_rejected_response_rows": stat_claim_certificate_witness_response_apply_manifest[
                "n_rejected_response_rows"
            ],
            "stat_claim_certificate_witness_response_apply_missing_validation_rows": stat_claim_certificate_witness_response_apply_manifest[
                "n_missing_validation_rows"
            ],
            "stat_claim_certificate_witness_response_apply_missing_response_rows": stat_claim_certificate_witness_response_apply_manifest[
                "n_missing_response_rows"
            ],
            "stat_claim_certificate_witness_response_apply_missing_response_fields": stat_claim_certificate_witness_response_apply_manifest[
                "n_missing_response_fields"
            ],
            "stat_claim_certificate_witness_response_apply_proof_evidence_status": stat_claim_certificate_witness_response_apply_manifest[
                "proof_evidence_status"
            ],
            "stat_claim_certificate_witness_validator_drafts": stat_claim_certificate_witness_validator_manifest[
                "n_drafts"
            ],
            "stat_claim_certificate_witness_validator_ok": stat_claim_certificate_witness_validator_manifest[
                "n_ok"
            ],
            "stat_claim_certificate_witness_validator_ready_for_checker_validation": stat_claim_certificate_witness_validator_manifest[
                "n_ready_for_checker_validation"
            ],
            "stat_claim_certificate_witness_validator_incomplete": stat_claim_certificate_witness_validator_manifest[
                "n_incomplete"
            ],
            "stat_claim_certificate_witness_validator_missing_source_evidence": stat_claim_certificate_witness_validator_manifest[
                "n_missing_source_evidence"
            ],
            "stat_claim_certificate_witness_validator_open_semantic_gap_rows": stat_claim_certificate_witness_validator_manifest[
                "n_open_semantic_gap_rows"
            ],
            "stat_claim_certificate_witness_validator_proof_overclaim_rows": stat_claim_certificate_witness_validator_manifest[
                "n_proof_overclaim_rows"
            ],
            "stat_claim_certificate_witness_validator_proof_evidence_status": stat_claim_certificate_witness_validator_manifest[
                "proof_evidence_status"
            ],
            "theorem_composition_packets": theorem_composition_manifest["n_packets"],
            "theorem_composition_packets_ok": theorem_composition_manifest["n_ok"],
            "theorem_composition_exact_proof_bank_links": theorem_composition_manifest[
                "n_exact_proof_bank_links"
            ],
            "theorem_composition_unresolved_primitives": theorem_composition_manifest[
                "n_unresolved_primitives"
            ],
            "theorem_composition_packets_with_unresolved_primitives": theorem_composition_manifest[
                "n_packets_with_unresolved_primitives"
            ],
            "theorem_composition_ready_for_exact_reuse": theorem_composition_manifest[
                "n_ready_for_exact_reuse_composition"
            ],
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
            "frontier_discover_and_prove_prompt_packets": str(
                out_dir
                / "frontier_discover_and_prove_prompt_packets"
                / "frontier_discover_and_prove_prompt_packets_manifest.json"
            ),
            "frontier_discover_and_prove_prompt_packets_jsonl": str(
                out_dir
                / "frontier_discover_and_prove_prompt_packets"
                / "frontier_discover_and_prove_prompt_packets.jsonl"
            ),
            "frontier_discover_and_prove_prompt_packets_report": str(
                out_dir
                / "frontier_discover_and_prove_prompt_packets"
                / "frontier_discover_and_prove_prompt_packets.md"
            ),
            "paper_theory_roundtrip": str(
                out_dir / "paper_theory_roundtrip" / "paper_theory_roundtrip_manifest.json"
            ),
            "paper_theory_roundtrip_statement_catalog_jsonl": str(
                out_dir / "paper_theory_roundtrip" / "paper_statement_catalog.jsonl"
            ),
            "paper_theory_roundtrip_stat_theory_ir_jsonl": str(
                out_dir / "paper_theory_roundtrip" / "stat_theory_ir.jsonl"
            ),
            "paper_theory_roundtrip_lean_candidate_queue_jsonl": str(
                out_dir
                / "paper_theory_roundtrip"
                / "statement_to_lean_candidate_queue.jsonl"
            ),
            "paper_theory_roundtrip_roundtrip_review_queue_jsonl": str(
                out_dir
                / "paper_theory_roundtrip"
                / "lean_to_latex_roundtrip_review_queue.jsonl"
            ),
            "paper_theory_roundtrip_dependency_graph": str(
                out_dir / "paper_theory_roundtrip" / "paper_theory_dependency_graph.json"
            ),
            "paper_theory_roundtrip_report": str(
                out_dir / "paper_theory_roundtrip" / "paper_theory_roundtrip.md"
            ),
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
            "formal_source_retrieval_external_benchmark": str(
                out_dir
                / "formal_source_retrieval_external_benchmark"
                / "formal_source_retrieval_benchmark_manifest.json"
            ),
            "formal_source_retrieval_external_benchmark_report": str(
                out_dir
                / "formal_source_retrieval_external_benchmark"
                / "formal_source_retrieval_benchmark.md"
            ),
            "formal_source_retrieval_all_benchmark": str(
                out_dir
                / "formal_source_retrieval_all_benchmark"
                / "formal_source_retrieval_benchmark_manifest.json"
            ),
            "formal_source_retrieval_all_benchmark_report": str(
                out_dir
                / "formal_source_retrieval_all_benchmark"
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
            "lean_rag_dependency_health": str(
                out_dir / "lean_rag_dependency_health" / "lean_rag_dependency_health_manifest.json"
            ),
            "lean_rag_dependency_health_report": str(
                out_dir / "lean_rag_dependency_health" / "lean_rag_dependency_health.md"
            ),
            "lean_rag_package_audit": str(
                out_dir / "lean_rag_package_audit" / "lean_rag_package_audit_manifest.json"
            ),
            "lean_rag_package_report": str(
                out_dir / "lean_rag_package_audit" / "lean_rag_package_audit.md"
            ),
            "lean_rag_source_registry_expansion": str(
                out_dir
                / "lean_rag_source_registry_expansion"
                / "source_registry_expansion_manifest.json"
            ),
            "lean_rag_source_registry_expansion_report": str(
                out_dir
                / "lean_rag_source_registry_expansion"
                / "source_registry_expansion.md"
            ),
            "lean_rag_source_registry_expansion_staged_registry": str(
                out_dir
                / "lean_rag_source_registry_expansion"
                / "staged_source_registry.json"
            ),
            "lean_rag_source_registry_expansion_delta": str(
                out_dir
                / "lean_rag_source_registry_expansion"
                / "source_registry_delta.json"
            ),
            "lean_rag_source_registry_expansion_preflight": str(
                out_dir
                / "lean_rag_source_registry_expansion_preflight"
                / "source_registry_expansion_preflight_manifest.json"
            ),
            "lean_rag_source_registry_expansion_preflight_report": str(
                out_dir
                / "lean_rag_source_registry_expansion_preflight"
                / "source_registry_expansion_preflight.md"
            ),
            "lean_rag_source_registry_expansion_apply": str(
                out_dir
                / "lean_rag_source_registry_expansion_apply"
                / "source_registry_expansion_apply_manifest.json"
            ),
            "lean_rag_source_registry_expansion_apply_report": str(
                out_dir
                / "lean_rag_source_registry_expansion_apply"
                / "source_registry_expansion_apply.md"
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
            "research_agent_runtime_audit": str(
                out_dir
                / "research_agent_runtime_audit"
                / "research_agent_runtime_audit_manifest.json"
            ),
            "research_agent_runtime_audit_report": str(
                out_dir / "research_agent_runtime_audit" / "research_agent_runtime_audit.md"
            ),
            "huggingface_lean_source_audit": str(
                out_dir
                / "huggingface_lean_source_audit"
                / "huggingface_lean_source_audit_manifest.json"
            ),
            "huggingface_lean_source_rag_integration_plan": str(
                out_dir
                / "huggingface_lean_source_audit"
                / "huggingface_lean_rag_integration_plan.json"
            ),
            "huggingface_lean_source_revalidation_queue": str(
                out_dir
                / "huggingface_lean_source_audit"
                / "huggingface_lean_source_revalidation_queue.jsonl"
            ),
            "huggingface_lean_source_revalidation_tasks": str(
                out_dir
                / "huggingface_lean_source_revalidation_tasks"
                / "hf_lean_source_revalidation_tasks_manifest.json"
            ),
            "huggingface_lean_source_revalidation_tasks_jsonl": str(
                out_dir
                / "huggingface_lean_source_revalidation_tasks"
                / "hf_lean_source_revalidation_tasks.jsonl"
            ),
            "huggingface_lean_source_revalidation_tasks_report": str(
                out_dir
                / "huggingface_lean_source_revalidation_tasks"
                / "hf_lean_source_revalidation_tasks.md"
            ),
            "huggingface_lean_source_revalidation_prompt_packets": str(
                out_dir
                / "huggingface_lean_source_revalidation_prompt_packets"
                / "hf_lean_source_revalidation_prompt_packets_manifest.json"
            ),
            "huggingface_lean_source_revalidation_prompt_packets_jsonl": str(
                out_dir
                / "huggingface_lean_source_revalidation_prompt_packets"
                / "hf_lean_source_revalidation_prompt_packets.jsonl"
            ),
            "huggingface_lean_source_revalidation_prompt_packets_report": str(
                out_dir
                / "huggingface_lean_source_revalidation_prompt_packets"
                / "hf_lean_source_revalidation_prompt_packets.md"
            ),
            "huggingface_lean_source_revalidation_artifact_validation": str(
                out_dir
                / "huggingface_lean_source_revalidation_artifact_validation"
                / "hf_lean_source_revalidation_artifact_validation_manifest.json"
            ),
            "huggingface_lean_source_revalidation_artifact_validation_jsonl": str(
                out_dir
                / "huggingface_lean_source_revalidation_artifact_validation"
                / "hf_lean_source_revalidation_artifact_validation.jsonl"
            ),
            "huggingface_lean_source_revalidation_artifact_validation_report": str(
                out_dir
                / "huggingface_lean_source_revalidation_artifact_validation"
                / "hf_lean_source_revalidation_artifact_validation.md"
            ),
            "huggingface_lean_source_revalidation_promotion_queue": str(
                out_dir
                / "huggingface_lean_source_revalidation_promotion_queue"
                / "hf_lean_source_revalidation_promotion_queue_manifest.json"
            ),
            "huggingface_lean_source_revalidation_promotion_queue_jsonl": str(
                out_dir
                / "huggingface_lean_source_revalidation_promotion_queue"
                / "hf_lean_source_revalidation_promotion_queue.jsonl"
            ),
            "huggingface_lean_source_revalidation_promotion_queue_report": str(
                out_dir
                / "huggingface_lean_source_revalidation_promotion_queue"
                / "hf_lean_source_revalidation_promotion_queue.md"
            ),
            "huggingface_lean_source_report": str(
                out_dir
                / "huggingface_lean_source_audit"
                / "huggingface_lean_source_audit.md"
            ),
            "proof_audit": str(out_dir / "proof_audit" / "proof_audit_manifest.json"),
            "proof_attempt_log": str(out_dir / "proof_audit" / "proof_attempts.jsonl"),
            "kernel_smoke_proof_audit": str(
                out_dir / "kernel_smoke_proof_audit" / "proof_audit_manifest.json"
            ),
            "kernel_smoke_proof_attempt_log": str(
                out_dir / "kernel_smoke_proof_audit" / "proof_attempts.jsonl"
            ),
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
            "proof_search_kernel_rerun_local_lean": str(
                proof_search_kernel_rerun_local_lean_manifest["manifest_path"]
            ),
            "proof_search_kernel_rerun_local_lean_results": str(
                proof_search_kernel_rerun_local_lean_manifest["results_jsonl"]
            ),
            "proof_search_kernel_rerun_queue": str(
                out_dir
                / "proof_search_kernel_rerun_queue"
                / "proof_search_kernel_rerun_queue_manifest.json"
            ),
            "proof_search_kernel_rerun_queue_jsonl": str(
                out_dir / "proof_search_kernel_rerun_queue" / "proof_search_kernel_rerun_queue.jsonl"
            ),
            "proof_search_kernel_rerun_queue_report": str(
                out_dir / "proof_search_kernel_rerun_queue" / "proof_search_kernel_rerun_queue.md"
            ),
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
            "proof_search_retrieval_no_registered_ablation": str(
                out_dir
                / "proof_search_retrieval_no_registered_ablation"
                / "proof_search_retrieval_ablation_manifest.json"
            ),
            "proof_search_retrieval_no_registered_ablation_report": str(
                out_dir
                / "proof_search_retrieval_no_registered_ablation"
                / "proof_search_retrieval_ablation.md"
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
            "proof_bank_actions": str(out_dir / "proof_bank_actions" / "proof_bank_action_manifest.json"),
            "proof_bank_actions_jsonl": str(out_dir / "proof_bank_actions" / "proof_bank_actions.jsonl"),
            "proof_bank_actions_report": str(out_dir / "proof_bank_actions" / "proof_bank_actions.md"),
            "assumption_interfaces": str(
                out_dir / "assumption_interfaces" / "assumption_interface_manifest.json"
            ),
            "assumption_interfaces_jsonl": str(
                out_dir / "assumption_interfaces" / "assumption_interfaces.jsonl"
            ),
            "assumption_interfaces_report": str(
                out_dir / "assumption_interfaces" / "assumption_interfaces.md"
            ),
            "formalization_delta_plan": str(
                out_dir / "formalization_delta_plan" / "formalization_delta_plan_manifest.json"
            ),
            "formalization_delta_plan_jsonl": str(
                out_dir / "formalization_delta_plan" / "formalization_delta_plan.jsonl"
            ),
            "formalization_delta_graph": str(
                out_dir / "formalization_delta_plan" / "formalization_delta_graph.json"
            ),
            "formalization_delta_plan_report": str(
                out_dir / "formalization_delta_plan" / "formalization_delta_plan.md"
            ),
            "formal_verifier_queue": str(
                out_dir / "formal_verifier_queue" / "formal_verifier_queue_manifest.json"
            ),
            "formal_verifier_queue_jsonl": str(
                out_dir / "formal_verifier_queue" / "formal_verifier_queue.jsonl"
            ),
            "formal_verifier_queue_report": str(
                out_dir / "formal_verifier_queue" / "formal_verifier_queue.md"
            ),
            "goal_conditioned_minimal_formalization_plan": str(
                out_dir
                / "goal_conditioned_minimal_formalization_plan"
                / "goal_conditioned_minimal_formalization_plan_manifest.json"
            ),
            "goal_conditioned_minimal_formalization_plan_jsonl": str(
                out_dir
                / "goal_conditioned_minimal_formalization_plan"
                / "goal_conditioned_minimal_formalization_plan.jsonl"
            ),
            "goal_conditioned_minimal_formalization_plan_report": str(
                out_dir
                / "goal_conditioned_minimal_formalization_plan"
                / "goal_conditioned_minimal_formalization_plan.md"
            ),
            "goal_conditioned_minimal_formalization_route_alignment_edge_schema": str(
                out_dir
                / "goal_conditioned_minimal_formalization_plan"
                / "formalization_gap_planner_route_alignment_edge.schema.json"
            ),
            "goal_conditioned_minimal_formalization_plan_row_schema": str(
                out_dir
                / "goal_conditioned_minimal_formalization_plan"
                / "library_aware_formalization_gap_plan_row.schema.json"
            ),
            "formalization_gap_planner_portable_plan_audit": str(
                out_dir
                / "formalization_gap_planner_portable_plan_audit"
                / "formalization_gap_planner_portable_plan_audit_manifest.json"
            ),
            "formalization_gap_planner_portable_plan_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_portable_plan_audit"
                / "formalization_gap_planner_portable_plan_audit.jsonl"
            ),
            "formalization_gap_planner_portable_plan_audit_row_schema": str(
                out_dir
                / "formalization_gap_planner_portable_plan_audit"
                / "formalization_gap_planner_portable_plan_audit_row.schema.json"
            ),
            "formalization_gap_planner_portable_plan_audit_report": str(
                out_dir
                / "formalization_gap_planner_portable_plan_audit"
                / "formalization_gap_planner_portable_plan_audit.md"
            ),
            "formalization_gap_planner_portable_plan_audit_route_alignment_edge_schema": str(
                out_dir
                / "formalization_gap_planner_portable_plan_audit"
                / "formalization_gap_planner_route_alignment_edge.schema.json"
            ),
            "formalization_gap_planner_library_coverage_map": str(
                out_dir
                / "formalization_gap_planner_library_coverage_map"
                / "formalization_gap_planner_library_coverage_map_manifest.json"
            ),
            "formalization_gap_planner_library_coverage_map_jsonl": str(
                out_dir
                / "formalization_gap_planner_library_coverage_map"
                / "formalization_gap_planner_library_coverage_map.jsonl"
            ),
            "formalization_gap_planner_library_coverage_map_row_schema": str(
                out_dir
                / "formalization_gap_planner_library_coverage_map"
                / "formalization_gap_planner_library_coverage_map_row.schema.json"
            ),
            "formalization_gap_planner_library_coverage_map_report": str(
                out_dir
                / "formalization_gap_planner_library_coverage_map"
                / "formalization_gap_planner_library_coverage_map.md"
            ),
            "formalization_gap_planner_primitive_action_queue": str(
                out_dir
                / "formalization_gap_planner_primitive_action_queue"
                / "formalization_gap_planner_primitive_action_queue_manifest.json"
            ),
            "formalization_gap_planner_primitive_action_queue_jsonl": str(
                out_dir
                / "formalization_gap_planner_primitive_action_queue"
                / "formalization_gap_planner_primitive_action_queue.jsonl"
            ),
            "formalization_gap_planner_primitive_action_queue_row_schema": str(
                out_dir
                / "formalization_gap_planner_primitive_action_queue"
                / "formalization_gap_planner_primitive_action_queue_row.schema.json"
            ),
            "formalization_gap_planner_primitive_action_queue_report": str(
                out_dir
                / "formalization_gap_planner_primitive_action_queue"
                / "formalization_gap_planner_primitive_action_queue.md"
            ),
            "formalization_gap_planner_action_resource_plan": str(
                out_dir
                / "formalization_gap_planner_action_resource_plan"
                / "formalization_gap_planner_action_resource_plan_manifest.json"
            ),
            "formalization_gap_planner_action_resource_plan_jsonl": str(
                out_dir
                / "formalization_gap_planner_action_resource_plan"
                / "formalization_gap_planner_action_resource_plan.jsonl"
            ),
            "formalization_gap_planner_action_resource_plan_row_schema": str(
                out_dir
                / "formalization_gap_planner_action_resource_plan"
                / "formalization_gap_planner_action_resource_plan_row.schema.json"
            ),
            "formalization_gap_planner_action_resource_plan_report": str(
                out_dir
                / "formalization_gap_planner_action_resource_plan"
                / "formalization_gap_planner_action_resource_plan.md"
            ),
            "formalization_gap_planner_resource_request_queue": str(
                out_dir
                / "formalization_gap_planner_resource_request_queue"
                / "formalization_gap_planner_resource_request_queue_manifest.json"
            ),
            "formalization_gap_planner_resource_request_queue_jsonl": str(
                out_dir
                / "formalization_gap_planner_resource_request_queue"
                / "formalization_gap_planner_resource_request_queue.jsonl"
            ),
            "formalization_gap_planner_resource_request_queue_row_schema": str(
                out_dir
                / "formalization_gap_planner_resource_request_queue"
                / "formalization_gap_planner_resource_request_queue_row.schema.json"
            ),
            "formalization_gap_planner_resource_request_queue_report": str(
                out_dir
                / "formalization_gap_planner_resource_request_queue"
                / "formalization_gap_planner_resource_request_queue.md"
            ),
            "formalization_gap_planner_resource_response_ledger": str(
                out_dir
                / "formalization_gap_planner_resource_response_ledger"
                / "formalization_gap_planner_resource_response_ledger_manifest.json"
            ),
            "formalization_gap_planner_resource_response_ledger_jsonl": str(
                out_dir
                / "formalization_gap_planner_resource_response_ledger"
                / "formalization_gap_planner_resource_response_ledger.jsonl"
            ),
            "formalization_gap_planner_resource_response_ledger_response_schema": str(
                out_dir
                / "formalization_gap_planner_resource_response_ledger"
                / "formalization_gap_planner_resource_response.schema.json"
            ),
            "formalization_gap_planner_resource_response_ledger_row_schema": str(
                out_dir
                / "formalization_gap_planner_resource_response_ledger"
                / "formalization_gap_planner_resource_response_ledger_row.schema.json"
            ),
            "formalization_gap_planner_resource_response_ledger_report": str(
                out_dir
                / "formalization_gap_planner_resource_response_ledger"
                / "formalization_gap_planner_resource_response_ledger.md"
            ),
            "formalization_gap_planner_minimal_delta_audit": str(
                out_dir
                / "formalization_gap_planner_minimal_delta_audit"
                / "formalization_gap_planner_minimal_delta_audit_manifest.json"
            ),
            "formalization_gap_planner_minimal_delta_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_minimal_delta_audit"
                / "formalization_gap_planner_minimal_delta_audit.jsonl"
            ),
            "formalization_gap_planner_minimal_delta_audit_report": str(
                out_dir
                / "formalization_gap_planner_minimal_delta_audit"
                / "formalization_gap_planner_minimal_delta_audit.md"
            ),
            "formalization_gap_planner_minimal_delta_decisions_jsonl": str(
                out_dir
                / "formalization_gap_planner_minimal_delta_audit"
                / "formalization_gap_planner_minimal_delta_decisions.jsonl"
            ),
            "formalization_gap_planner_minimal_delta_decision_row_schema": str(
                out_dir
                / "formalization_gap_planner_minimal_delta_audit"
                / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
            ),
            "formalization_gap_planner_source_grounding_audit": str(
                out_dir
                / "formalization_gap_planner_source_grounding_audit"
                / "formalization_gap_planner_source_grounding_audit_manifest.json"
            ),
            "formalization_gap_planner_source_grounding_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_source_grounding_audit"
                / "formalization_gap_planner_source_grounding_audit.jsonl"
            ),
            "formalization_gap_planner_source_grounding_audit_report": str(
                out_dir
                / "formalization_gap_planner_source_grounding_audit"
                / "formalization_gap_planner_source_grounding_audit.md"
            ),
            "formalization_gap_planner_source_grounding_row_schema": str(
                out_dir
                / "formalization_gap_planner_source_grounding_audit"
                / "formalization_gap_planner_source_grounding_row.schema.json"
            ),
            "formalization_gap_planner_target_intake": str(
                out_dir
                / "formalization_gap_planner_target_intake"
                / "formalization_gap_planner_target_intake_manifest.json"
            ),
            "formalization_gap_planner_target_intake_jsonl": str(
                out_dir
                / "formalization_gap_planner_target_intake"
                / "formalization_gap_planner_target_intake.jsonl"
            ),
            "formalization_gap_planner_target_intake_seed": str(
                out_dir
                / "formalization_gap_planner_target_intake"
                / "formalization_gap_planner_target_intake_standalone_seed.json"
            ),
            "formalization_gap_planner_target_intake_report": str(
                out_dir
                / "formalization_gap_planner_target_intake"
                / "formalization_gap_planner_target_intake.md"
            ),
            "formalization_gap_planner_target_intake_schema": str(
                out_dir
                / "formalization_gap_planner_target_intake"
                / "formalization_gap_planner_target_intake.schema.json"
            ),
            "formalization_gap_planner_target_intake_row_schema": str(
                out_dir
                / "formalization_gap_planner_target_intake"
                / "formalization_gap_planner_target_intake_row.schema.json"
            ),
            "formalization_gap_planner_benchmark": str(
                out_dir
                / "formalization_gap_planner_benchmark"
                / "formalization_gap_planner_benchmark_manifest.json"
            ),
            "formalization_gap_planner_benchmark_ground_truth": str(
                out_dir
                / "formalization_gap_planner_benchmark"
                / "formalization_gap_planner_ground_truth.json"
            ),
            "formalization_gap_planner_benchmark_jsonl": str(
                out_dir
                / "formalization_gap_planner_benchmark"
                / "formalization_gap_planner_benchmark_routes.jsonl"
            ),
            "formalization_gap_planner_benchmark_route_schema": str(
                out_dir
                / "formalization_gap_planner_benchmark"
                / "formalization_gap_planner_benchmark_route.schema.json"
            ),
            "formalization_gap_planner_benchmark_report": str(
                out_dir
                / "formalization_gap_planner_benchmark"
                / "formalization_gap_planner_benchmark.md"
            ),
            "formalization_gap_planner_benchmark_audit": str(
                out_dir
                / "formalization_gap_planner_benchmark_audit"
                / "formalization_gap_planner_benchmark_audit_manifest.json"
            ),
            "formalization_gap_planner_benchmark_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_benchmark_audit"
                / "formalization_gap_planner_benchmark_audit.jsonl"
            ),
            "formalization_gap_planner_benchmark_audit_report": str(
                out_dir
                / "formalization_gap_planner_benchmark_audit"
                / "formalization_gap_planner_benchmark_audit.md"
            ),
            "formalization_gap_planner_evaluation": str(
                out_dir
                / "formalization_gap_planner_evaluation"
                / "formalization_gap_planner_evaluation_manifest.json"
            ),
            "formalization_gap_planner_evaluation_jsonl": str(
                out_dir
                / "formalization_gap_planner_evaluation"
                / "formalization_gap_planner_evaluation.jsonl"
            ),
            "formalization_gap_planner_evaluation_row_schema": str(
                out_dir
                / "formalization_gap_planner_evaluation"
                / "formalization_gap_planner_evaluation_row.schema.json"
            ),
            "formalization_gap_planner_evaluation_report": str(
                out_dir
                / "formalization_gap_planner_evaluation"
                / "formalization_gap_planner_evaluation.md"
            ),
            "formalization_gap_planner_ablation_study": str(
                out_dir
                / "formalization_gap_planner_ablation_study"
                / "formalization_gap_planner_ablation_study_manifest.json"
            ),
            "formalization_gap_planner_ablation_study_jsonl": str(
                out_dir
                / "formalization_gap_planner_ablation_study"
                / "formalization_gap_planner_ablation_study.jsonl"
            ),
            "formalization_gap_planner_ablation_study_row_schema": str(
                out_dir
                / "formalization_gap_planner_ablation_study"
                / "formalization_gap_planner_ablation_study_row.schema.json"
            ),
            "formalization_gap_planner_ablation_study_report": str(
                out_dir
                / "formalization_gap_planner_ablation_study"
                / "formalization_gap_planner_ablation_study.md"
            ),
            "formal_verifier_replay": str(
                out_dir / "formal_verifier_replay" / "formal_verifier_replay_manifest.json"
            ),
            "formal_verifier_replay_jsonl": str(
                out_dir / "formal_verifier_replay" / "formal_verifier_replay_tasks.jsonl"
            ),
            "formal_verifier_replay_training_jsonl": str(
                out_dir / "formal_verifier_replay" / "formal_verifier_replay_training.jsonl"
            ),
            "formal_verifier_replay_report": str(
                out_dir / "formal_verifier_replay" / "formal_verifier_replay.md"
            ),
            "formal_verifier_replay_attempts": str(
                out_dir
                / "formal_verifier_replay_attempts"
                / "formal_verifier_replay_attempt_manifest.json"
            ),
            "formal_verifier_replay_attempts_jsonl": str(
                out_dir
                / "formal_verifier_replay_attempts"
                / "formal_verifier_replay_attempts.jsonl"
            ),
            "formal_verifier_replay_attempts_report": str(
                out_dir
                / "formal_verifier_replay_attempts"
                / "formal_verifier_replay_attempts.md"
            ),
            "formal_verifier_replay_calibration": str(
                out_dir
                / "formal_verifier_replay_calibration"
                / "formal_verifier_replay_calibration_manifest.json"
            ),
            "formal_verifier_replay_calibration_jsonl": str(
                out_dir
                / "formal_verifier_replay_calibration"
                / "formal_verifier_replay_calibration.jsonl"
            ),
            "formal_verifier_replay_calibration_repair_training_jsonl": str(
                out_dir
                / "formal_verifier_replay_calibration"
                / "formal_verifier_replay_repair_training.jsonl"
            ),
            "formal_verifier_replay_calibration_report": str(
                out_dir
                / "formal_verifier_replay_calibration"
                / "formal_verifier_replay_calibration.md"
            ),
            "formalization_gap_planner_refinement_queue": str(
                out_dir
                / "formalization_gap_planner_refinement_queue"
                / "formalization_gap_planner_refinement_queue_manifest.json"
            ),
            "formalization_gap_planner_refinement_queue_jsonl": str(
                out_dir
                / "formalization_gap_planner_refinement_queue"
                / "formalization_gap_planner_refinement_queue.jsonl"
            ),
            "formalization_gap_planner_refinement_work_item_schema": str(
                out_dir
                / "formalization_gap_planner_refinement_queue"
                / "formalization_gap_planner_refinement_work_item.schema.json"
            ),
            "formalization_gap_planner_refinement_queue_report": str(
                out_dir
                / "formalization_gap_planner_refinement_queue"
                / "formalization_gap_planner_refinement_queue.md"
            ),
            "formalization_gap_planner_refinement_adapter_responses": str(
                out_dir
                / "formalization_gap_planner_refinement_adapter_responses"
                / "formalization_gap_planner_refinement_adapter_manifest.json"
            ),
            "formalization_gap_planner_refinement_adapter_responses_jsonl": str(
                out_dir
                / "formalization_gap_planner_refinement_adapter_responses"
                / "formalization_gap_planner_refinement_evidence_responses.jsonl"
            ),
            "formalization_gap_planner_refinement_adapter_response_schema": str(
                out_dir
                / "formalization_gap_planner_refinement_adapter_responses"
                / "formalization_gap_planner_refinement_tool_response.schema.json"
            ),
            "formalization_gap_planner_refinement_adapter_responses_report": str(
                out_dir
                / "formalization_gap_planner_refinement_adapter_responses"
                / "formalization_gap_planner_refinement_adapter.md"
            ),
            "formalization_gap_planner_local_literature_adapter": str(
                out_dir
                / "formalization_gap_planner_local_literature_adapter"
                / "formalization_gap_planner_local_literature_adapter_manifest.json"
            ),
            "formalization_gap_planner_local_literature_adapter_jsonl": str(
                out_dir
                / "formalization_gap_planner_local_literature_adapter"
                / "formalization_gap_planner_local_literature_adapter_responses.jsonl"
            ),
            "formalization_gap_planner_local_literature_adapter_response_schema": str(
                out_dir
                / "formalization_gap_planner_local_literature_adapter"
                / "formalization_gap_planner_refinement_tool_response.schema.json"
            ),
            "formalization_gap_planner_local_literature_adapter_report": str(
                out_dir
                / "formalization_gap_planner_local_literature_adapter"
                / "formalization_gap_planner_local_literature_adapter.md"
            ),
            "formalization_gap_planner_local_formal_source_adapter": str(
                out_dir
                / "formalization_gap_planner_local_formal_source_adapter"
                / "formalization_gap_planner_local_formal_source_adapter_manifest.json"
            ),
            "formalization_gap_planner_local_formal_source_adapter_jsonl": str(
                out_dir
                / "formalization_gap_planner_local_formal_source_adapter"
                / "formalization_gap_planner_local_formal_source_adapter_responses.jsonl"
            ),
            "formalization_gap_planner_local_formal_source_adapter_response_schema": str(
                out_dir
                / "formalization_gap_planner_local_formal_source_adapter"
                / "formalization_gap_planner_refinement_tool_response.schema.json"
            ),
            "formalization_gap_planner_local_formal_source_adapter_report": str(
                out_dir
                / "formalization_gap_planner_local_formal_source_adapter"
                / "formalization_gap_planner_local_formal_source_adapter.md"
            ),
            "formalization_gap_planner_local_proof_state_adapter": str(
                out_dir
                / "formalization_gap_planner_local_proof_state_adapter"
                / "formalization_gap_planner_local_proof_state_adapter_manifest.json"
            ),
            "formalization_gap_planner_local_proof_state_adapter_jsonl": str(
                out_dir
                / "formalization_gap_planner_local_proof_state_adapter"
                / "formalization_gap_planner_local_proof_state_adapter_responses.jsonl"
            ),
            "formalization_gap_planner_local_proof_state_adapter_response_schema": str(
                out_dir
                / "formalization_gap_planner_local_proof_state_adapter"
                / "formalization_gap_planner_refinement_tool_response.schema.json"
            ),
            "formalization_gap_planner_local_proof_state_adapter_report": str(
                out_dir
                / "formalization_gap_planner_local_proof_state_adapter"
                / "formalization_gap_planner_local_proof_state_adapter.md"
            ),
            "formalization_gap_planner_refinement_evidence": str(
                out_dir
                / "formalization_gap_planner_refinement_evidence"
                / "formalization_gap_planner_refinement_evidence_manifest.json"
            ),
            "formalization_gap_planner_refinement_evidence_jsonl": str(
                out_dir
                / "formalization_gap_planner_refinement_evidence"
                / "formalization_gap_planner_refinement_evidence.jsonl"
            ),
            "formalization_gap_planner_refinement_tool_response_schema": str(
                out_dir
                / "formalization_gap_planner_refinement_evidence"
                / "formalization_gap_planner_refinement_tool_response.schema.json"
            ),
            "formalization_gap_planner_refinement_evidence_row_schema": str(
                out_dir
                / "formalization_gap_planner_refinement_evidence"
                / "formalization_gap_planner_refinement_evidence_row.schema.json"
            ),
            "formalization_gap_planner_route_revision_proposals_jsonl": str(
                out_dir
                / "formalization_gap_planner_refinement_evidence"
                / "formalization_gap_planner_route_revision_proposals.jsonl"
            ),
            "formalization_gap_planner_refinement_evidence_report": str(
                out_dir
                / "formalization_gap_planner_refinement_evidence"
                / "formalization_gap_planner_refinement_evidence.md"
            ),
            "formalization_gap_planner_route_revision_overlay": str(
                out_dir
                / "formalization_gap_planner_route_revision_overlay"
                / "formalization_gap_planner_route_revision_overlay_manifest.json"
            ),
            "formalization_gap_planner_route_revision_overlay_jsonl": str(
                out_dir
                / "formalization_gap_planner_route_revision_overlay"
                / "formalization_gap_planner_route_revision_overlay.jsonl"
            ),
            "formalization_gap_planner_route_revision_overlay_row_schema": str(
                out_dir
                / "formalization_gap_planner_route_revision_overlay"
                / "formalization_gap_planner_route_revision_overlay_row.schema.json"
            ),
            "formalization_gap_planner_route_revision_overlay_report": str(
                out_dir
                / "formalization_gap_planner_route_revision_overlay"
                / "formalization_gap_planner_route_revision_overlay.md"
            ),
            "formalization_gap_planner_route_stability_audit": str(
                out_dir
                / "formalization_gap_planner_route_stability_audit"
                / "formalization_gap_planner_route_stability_audit_manifest.json"
            ),
            "formalization_gap_planner_route_stability_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_route_stability_audit"
                / "formalization_gap_planner_route_stability_audit.jsonl"
            ),
            "formalization_gap_planner_route_stability_audit_row_schema": str(
                out_dir
                / "formalization_gap_planner_route_stability_audit"
                / "formalization_gap_planner_route_stability_audit_row.schema.json"
            ),
            "formalization_gap_planner_route_stability_audit_report": str(
                out_dir
                / "formalization_gap_planner_route_stability_audit"
                / "formalization_gap_planner_route_stability_audit.md"
            ),
            "formalization_gap_planner_route_replan_handoff": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff"
                / "formalization_gap_planner_route_replan_handoff_manifest.json"
            ),
            "formalization_gap_planner_route_replan_handoff_jsonl": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff"
                / "formalization_gap_planner_route_replan_handoff.jsonl"
            ),
            "formalization_gap_planner_route_replan_handoff_row_schema": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff"
                / "formalization_gap_planner_route_replan_handoff_row.schema.json"
            ),
            "formalization_gap_planner_route_replan_standalone_seed": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff"
                / "formalization_gap_planner_route_replan_standalone_seed.json"
            ),
            "formalization_gap_planner_route_replan_standalone_seed_schema": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff"
                / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
            ),
            "formalization_gap_planner_route_replan_handoff_report": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff"
                / "formalization_gap_planner_route_replan_handoff.md"
            ),
            "formalization_gap_planner_route_replan_handoff_audit": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff_audit"
                / "formalization_gap_planner_route_replan_handoff_audit_manifest.json"
            ),
            "formalization_gap_planner_route_replan_handoff_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff_audit"
                / "formalization_gap_planner_route_replan_handoff_audit.jsonl"
            ),
            "formalization_gap_planner_route_replan_handoff_audit_row_schema": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff_audit"
                / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
            ),
            "formalization_gap_planner_route_replan_handoff_audit_report": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff_audit"
                / "formalization_gap_planner_route_replan_handoff_audit.md"
            ),
            "formalization_gap_planner_route_replan_handoff_audit_roundtrip_plan": str(
                out_dir
                / "formalization_gap_planner_route_replan_handoff_audit"
                / "formalization_gap_planner_route_replan_roundtrip_plan"
                / "goal_conditioned_minimal_formalization_plan_manifest.json"
            ),
            "formalization_gap_planner_proof_state_triage": str(
                out_dir
                / "formalization_gap_planner_proof_state_triage"
                / "formalization_gap_planner_proof_state_triage_manifest.json"
            ),
            "formalization_gap_planner_proof_state_triage_jsonl": str(
                out_dir
                / "formalization_gap_planner_proof_state_triage"
                / "formalization_gap_planner_proof_state_triage.jsonl"
            ),
            "formalization_gap_planner_proof_state_triage_row_schema": str(
                out_dir
                / "formalization_gap_planner_proof_state_triage"
                / "formalization_gap_planner_proof_state_triage_row.schema.json"
            ),
            "formalization_gap_planner_proof_state_triage_report": str(
                out_dir
                / "formalization_gap_planner_proof_state_triage"
                / "formalization_gap_planner_proof_state_triage.md"
            ),
            "formalization_gap_planner_interactive_session": str(
                out_dir
                / "formalization_gap_planner_interactive_session"
                / "formalization_gap_planner_interactive_session_manifest.json"
            ),
            "formalization_gap_planner_interactive_session_jsonl": str(
                out_dir
                / "formalization_gap_planner_interactive_session"
                / "formalization_gap_planner_interactive_session.jsonl"
            ),
            "formalization_gap_planner_interactive_session_row_schema": str(
                out_dir
                / "formalization_gap_planner_interactive_session"
                / "formalization_gap_planner_interactive_session_row.schema.json"
            ),
            "formalization_gap_planner_interactive_decision_policy_jsonl": str(
                out_dir
                / "formalization_gap_planner_interactive_session"
                / "formalization_gap_planner_interactive_decision_policy.jsonl"
            ),
            "formalization_gap_planner_interactive_decision_policy_row_schema": str(
                out_dir
                / "formalization_gap_planner_interactive_session"
                / "formalization_gap_planner_interactive_decision_policy_row.schema.json"
            ),
            "formalization_gap_planner_interactive_session_report": str(
                out_dir
                / "formalization_gap_planner_interactive_session"
                / "formalization_gap_planner_interactive_session.md"
            ),
            "formalization_gap_planner_prover_adapter_contract": str(
                out_dir
                / "formalization_gap_planner_prover_adapter_contract"
                / "formalization_gap_planner_prover_adapter_contract_manifest.json"
            ),
            "formalization_gap_planner_prover_adapter_packets_jsonl": str(
                out_dir
                / "formalization_gap_planner_prover_adapter_contract"
                / "formalization_gap_planner_prover_adapter_packets.jsonl"
            ),
            "formalization_gap_planner_prover_adapter_response_validation_jsonl": str(
                out_dir
                / "formalization_gap_planner_prover_adapter_contract"
                / "formalization_gap_planner_prover_adapter_response_validation.jsonl"
            ),
            "formalization_gap_planner_prover_adapter_response_schema": str(
                out_dir
                / "formalization_gap_planner_prover_adapter_contract"
                / "formalization_gap_planner_prover_adapter_response.schema.json"
            ),
            "formalization_gap_planner_prover_adapter_response_validation_row_schema": str(
                out_dir
                / "formalization_gap_planner_prover_adapter_contract"
                / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
            ),
            "formalization_gap_planner_prover_adapter_packet_schema": str(
                out_dir
                / "formalization_gap_planner_prover_adapter_contract"
                / "formalization_gap_planner_prover_adapter_packet.schema.json"
            ),
            "formalization_gap_planner_prover_adapter_contract_report": str(
                out_dir
                / "formalization_gap_planner_prover_adapter_contract"
                / "formalization_gap_planner_prover_adapter_contract.md"
            ),
            "formalization_gap_planner_adapter_registry": str(
                out_dir
                / "formalization_gap_planner_adapter_registry"
                / "formalization_gap_planner_adapter_registry_manifest.json"
            ),
            "formalization_gap_planner_adapter_registry_jsonl": str(
                out_dir
                / "formalization_gap_planner_adapter_registry"
                / "formalization_gap_planner_adapter_registry.jsonl"
            ),
            "formalization_gap_planner_adapter_registry_row_schema": str(
                out_dir
                / "formalization_gap_planner_adapter_registry"
                / "formalization_gap_planner_adapter_registry_row.schema.json"
            ),
            "formalization_gap_planner_adapter_registry_report": str(
                out_dir
                / "formalization_gap_planner_adapter_registry"
                / "formalization_gap_planner_adapter_registry.md"
            ),
            "formalization_gap_planner_adapter_registry_audit": str(
                out_dir
                / "formalization_gap_planner_adapter_registry_audit"
                / "formalization_gap_planner_adapter_registry_audit_manifest.json"
            ),
            "formalization_gap_planner_adapter_registry_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_adapter_registry_audit"
                / "formalization_gap_planner_adapter_registry_audit.jsonl"
            ),
            "formalization_gap_planner_adapter_registry_audit_report": str(
                out_dir
                / "formalization_gap_planner_adapter_registry_audit"
                / "formalization_gap_planner_adapter_registry_audit.md"
            ),
            "formalization_gap_planner_component_resource_registry": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_registry_manifest.json"
            ),
            "formalization_gap_planner_component_resource_registry_jsonl": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_registry.jsonl"
            ),
            "formalization_gap_planner_component_resource_resources_jsonl": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_resources.jsonl"
            ),
            "formalization_gap_planner_component_resource_execution_plans_jsonl": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_execution_plans.jsonl"
            ),
            "formalization_gap_planner_component_resource_contracts_jsonl": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_contracts.jsonl"
            ),
            "formalization_gap_planner_component_resource_resource_row_schema": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_resource_row.schema.json"
            ),
            "formalization_gap_planner_component_resource_component_row_schema": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_component_row.schema.json"
            ),
            "formalization_gap_planner_component_resource_execution_plan_schema": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_execution_plan.schema.json"
            ),
            "formalization_gap_planner_component_resource_contract_row_schema": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_contract_row.schema.json"
            ),
            "formalization_gap_planner_component_resource_registry_report": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry"
                / "formalization_gap_planner_component_resource_registry.md"
            ),
            "formalization_gap_planner_component_resource_registry_audit": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry_audit"
                / "formalization_gap_planner_component_resource_registry_audit_manifest.json"
            ),
            "formalization_gap_planner_component_resource_registry_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry_audit"
                / "formalization_gap_planner_component_resource_registry_audit.jsonl"
            ),
            "formalization_gap_planner_component_resource_registry_audit_report": str(
                out_dir
                / "formalization_gap_planner_component_resource_registry_audit"
                / "formalization_gap_planner_component_resource_registry_audit.md"
            ),
            "formalization_gap_planner_cross_prover_matrix_audit": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_cross_prover_matrix_audit_manifest.json"
            ),
            "formalization_gap_planner_cross_prover_matrix_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_cross_prover_matrix_audit.jsonl"
            ),
            "formalization_gap_planner_cross_prover_matrix_audit_row_schema": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
            ),
            "formalization_gap_planner_cross_prover_packets_jsonl": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_cross_prover_packets.jsonl"
            ),
            "formalization_gap_planner_cross_prover_packet_schema": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_prover_adapter_packet.schema.json"
            ),
            "formalization_gap_planner_cross_prover_response_validation_jsonl": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_cross_prover_response_validation.jsonl"
            ),
            "formalization_gap_planner_cross_prover_response_validation_row_schema": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
            ),
            "formalization_gap_planner_cross_prover_target_summary": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_cross_prover_target_summary.json"
            ),
            "formalization_gap_planner_cross_prover_target_summary_schema": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_cross_prover_target_summary.schema.json"
            ),
            "formalization_gap_planner_cross_prover_matrix_audit_report": str(
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit"
                / "formalization_gap_planner_cross_prover_matrix_audit.md"
            ),
            "formalization_gap_planner_publication_bundle": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "formalization_gap_planner_publication_bundle_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_report": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "formalization_gap_planner_publication_bundle.md"
            ),
            "formalization_gap_planner_publication_bundle_contract": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "contract"
                / "formalization_gap_planner_portable_contract.json"
            ),
            "formalization_gap_planner_publication_bundle_schema": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "contract"
                / "library_aware_formalization_gap_plan.schema.json"
            ),
            "formalization_gap_planner_publication_bundle_schema_catalog": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "contract"
                / "formalization_gap_planner_schema_catalog.json"
            ),
            "formalization_gap_planner_publication_bundle_schema_catalog_schema": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "contract"
                / "formalization_gap_planner_schema_catalog.schema.json"
            ),
            "formalization_gap_planner_publication_bundle_component_resource_registry": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "component_resource_registry"
                / "formalization_gap_planner_component_resource_registry_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_benchmark_audit": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "benchmark_audit"
                / "formalization_gap_planner_benchmark_audit_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_interactive_session": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "artifacts"
                / "formalization_gap_planner_interactive_session"
                / "formalization_gap_planner_interactive_session_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_ablation_study": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "artifacts"
                / "formalization_gap_planner_ablation_study"
                / "formalization_gap_planner_ablation_study_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_local_literature_adapter": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "artifacts"
                / "formalization_gap_planner_local_literature_adapter"
                / "formalization_gap_planner_local_literature_adapter_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_local_formal_source_adapter": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "artifacts"
                / "formalization_gap_planner_local_formal_source_adapter"
                / "formalization_gap_planner_local_formal_source_adapter_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_local_proof_state_adapter": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "artifacts"
                / "formalization_gap_planner_local_proof_state_adapter"
                / "formalization_gap_planner_local_proof_state_adapter_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_reproduction_manifest": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "reproduce"
                / "formalization_gap_planner_reproduction_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_reproduction_report": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "reproduce"
                / "formalization_gap_planner_reproduction.md"
            ),
            "formalization_gap_planner_publication_bundle_standalone_example": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "examples"
                / "formalization_gap_planner_standalone_example.json"
            ),
            "formalization_gap_planner_publication_bundle_target_intake_example": str(
                out_dir
                / "formalization_gap_planner_publication_bundle"
                / "examples"
                / "formalization_gap_planner_target_intake_example.json"
            ),
            "formalization_gap_planner_publication_bundle_audit": str(
                out_dir
                / "formalization_gap_planner_publication_bundle_audit"
                / "formalization_gap_planner_publication_bundle_audit_manifest.json"
            ),
            "formalization_gap_planner_publication_bundle_audit_jsonl": str(
                out_dir
                / "formalization_gap_planner_publication_bundle_audit"
                / "formalization_gap_planner_publication_bundle_audit.jsonl"
            ),
            "formalization_gap_planner_publication_bundle_audit_report": str(
                out_dir
                / "formalization_gap_planner_publication_bundle_audit"
                / "formalization_gap_planner_publication_bundle_audit.md"
            ),
            "formal_verifier_replay_repair": str(
                out_dir
                / "formal_verifier_replay_repair"
                / "formal_verifier_replay_repair_manifest.json"
            ),
            "formal_verifier_replay_repair_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair"
                / "formal_verifier_replay_repair_packets.jsonl"
            ),
            "formal_verifier_replay_repair_training_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair"
                / "formal_verifier_replay_repair_training.jsonl"
            ),
            "formal_verifier_replay_repair_report": str(
                out_dir
                / "formal_verifier_replay_repair"
                / "formal_verifier_replay_repair.md"
            ),
            "formal_verifier_replay_repair_application": str(
                out_dir
                / "formal_verifier_replay_repair_application"
                / "formal_verifier_replay_repair_application_manifest.json"
            ),
            "formal_verifier_replay_repair_application_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_application"
                / "formal_verifier_replay_repair_application_tasks.jsonl"
            ),
            "formal_verifier_replay_repair_application_training_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_application"
                / "formal_verifier_replay_repair_application_training.jsonl"
            ),
            "formal_verifier_replay_repair_application_report": str(
                out_dir
                / "formal_verifier_replay_repair_application"
                / "formal_verifier_replay_repair_application.md"
            ),
            "formal_verifier_replay_repair_application_validation": str(
                out_dir
                / "formal_verifier_replay_repair_application_validation"
                / "formal_verifier_replay_repair_application_validation_manifest.json"
            ),
            "formal_verifier_replay_repair_application_validation_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_application_validation"
                / "formal_verifier_replay_repair_application_validation.jsonl"
            ),
            "formal_verifier_replay_repair_application_validation_report": str(
                out_dir
                / "formal_verifier_replay_repair_application_validation"
                / "formal_verifier_replay_repair_application_validation.md"
            ),
            "formal_verifier_replay_repair_execution_queue": str(
                out_dir
                / "formal_verifier_replay_repair_execution_queue"
                / "formal_verifier_replay_repair_execution_queue_manifest.json"
            ),
            "formal_verifier_replay_repair_execution_queue_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_execution_queue"
                / "formal_verifier_replay_repair_execution_queue.jsonl"
            ),
            "formal_verifier_replay_repair_execution_queue_report": str(
                out_dir
                / "formal_verifier_replay_repair_execution_queue"
                / "formal_verifier_replay_repair_execution_queue.md"
            ),
            "formal_verifier_replay_repair_prompt_packets": str(
                out_dir
                / "formal_verifier_replay_repair_prompt_packets"
                / "formal_verifier_replay_repair_prompt_packets_manifest.json"
            ),
            "formal_verifier_replay_repair_prompt_packets_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_prompt_packets"
                / "formal_verifier_replay_repair_prompt_packets.jsonl"
            ),
            "formal_verifier_replay_repair_prompt_packets_report": str(
                out_dir
                / "formal_verifier_replay_repair_prompt_packets"
                / "formal_verifier_replay_repair_prompt_packets.md"
            ),
            "formal_verifier_replay_repair_patch_autoworker": str(
                out_dir
                / "formal_verifier_replay_repair_patch_autoworker"
                / "formal_verifier_replay_repair_patch_autoworker_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_autoworker_responses": str(
                out_dir
                / "formal_verifier_replay_repair_patch_autoworker"
                / "formal_verifier_replay_repair_patch_responses.jsonl"
            ),
            "formal_verifier_replay_repair_patch_autoworker_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_autoworker"
                / "formal_verifier_replay_repair_patch_autoworker.md"
            ),
            "formal_verifier_replay_repair_patch_response_validation": str(
                out_dir
                / "formal_verifier_replay_repair_patch_response_validation"
                / "formal_verifier_replay_repair_patch_response_validation_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_response_validation_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_patch_response_validation"
                / "formal_verifier_replay_repair_patch_response_validation.jsonl"
            ),
            "formal_verifier_replay_repair_patch_response_validation_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_response_validation"
                / "formal_verifier_replay_repair_patch_response_validation.md"
            ),
            "formal_verifier_replay_repair_patch_response_promotion": str(
                out_dir
                / "formal_verifier_replay_repair_patch_response_promotion"
                / "formal_verifier_replay_repair_patch_response_promotion_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_response_promotion_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_patch_response_promotion"
                / "formal_verifier_replay_repair_patch_response_promotion.jsonl"
            ),
            "formal_verifier_replay_repair_patch_response_promotion_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_response_promotion"
                / "formal_verifier_replay_repair_patch_response_promotion.md"
            ),
            "formal_verifier_replay_repair_patch_rerun_queue": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_queue"
                / "formal_verifier_replay_repair_patch_rerun_queue_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_rerun_queue_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_queue"
                / "formal_verifier_replay_repair_patch_rerun_queue.jsonl"
            ),
            "formal_verifier_replay_repair_patch_rerun_queue_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_queue"
                / "formal_verifier_replay_repair_patch_rerun_queue.md"
            ),
            "formal_verifier_replay_repair_patch_rerun_attempts": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_attempts"
                / "formal_verifier_replay_repair_patch_rerun_attempt_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_rerun_attempts_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_attempts"
                / "formal_verifier_replay_repair_patch_rerun_attempts.jsonl"
            ),
            "formal_verifier_replay_repair_patch_rerun_attempts_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_attempts"
                / "formal_verifier_replay_repair_patch_rerun_attempts.md"
            ),
            "formal_verifier_replay_repair_patch_rerun_calibration": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_calibration"
                / "formal_verifier_replay_repair_patch_rerun_calibration_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_rerun_calibration_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_calibration"
                / "formal_verifier_replay_repair_patch_rerun_calibration.jsonl"
            ),
            "formal_verifier_replay_repair_patch_rerun_calibration_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_calibration"
                / "formal_verifier_replay_repair_patch_rerun_calibration.md"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_obligations": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_obligations"
                / "formal_verifier_replay_repair_patch_rerun_residual_obligations_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_obligations"
                / "formal_verifier_replay_repair_patch_rerun_residual_obligations.jsonl"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_obligations"
                / "formal_verifier_replay_repair_patch_rerun_residual_obligations.md"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets"
                / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets"
                / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.jsonl"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets"
                / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.md"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_autoworker"
                / "formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_responses": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_autoworker"
                / "formal_verifier_replay_repair_patch_rerun_residual_responses.jsonl"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_autoworker"
                / "formal_verifier_replay_repair_patch_rerun_residual_autoworker.md"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_response_validation"
                / "formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_response_validation"
                / "formal_verifier_replay_repair_patch_rerun_residual_response_validation.jsonl"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_response_validation"
                / "formal_verifier_replay_repair_patch_rerun_residual_response_validation.md"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue"
                / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest.json"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_jsonl": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue"
                / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue.jsonl"
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_report": str(
                out_dir
                / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue"
                / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue.md"
            ),
            "formal_verifier_agentic_proof_strategy_plan": str(
                out_dir
                / "formal_verifier_agentic_proof_strategy_plan"
                / "formal_verifier_agentic_proof_strategy_plan_manifest.json"
            ),
            "formal_verifier_agentic_proof_strategy_plan_jsonl": str(
                out_dir
                / "formal_verifier_agentic_proof_strategy_plan"
                / "formal_verifier_agentic_proof_strategy_plan.jsonl"
            ),
            "formal_verifier_agentic_proof_strategy_plan_report": str(
                out_dir
                / "formal_verifier_agentic_proof_strategy_plan"
                / "formal_verifier_agentic_proof_strategy_plan.md"
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue": str(
                out_dir
                / "formal_verifier_agentic_proof_candidate_evaluation_queue"
                / "formal_verifier_agentic_proof_candidate_evaluation_queue_manifest.json"
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_jsonl": str(
                out_dir
                / "formal_verifier_agentic_proof_candidate_evaluation_queue"
                / "formal_verifier_agentic_proof_candidate_evaluation_queue.jsonl"
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_report": str(
                out_dir
                / "formal_verifier_agentic_proof_candidate_evaluation_queue"
                / "formal_verifier_agentic_proof_candidate_evaluation_queue.md"
            ),
            "formal_verifier_agentic_proof_safety_policy": str(
                out_dir
                / "formal_verifier_agentic_proof_safety_policy"
                / "formal_verifier_agentic_proof_safety_policy_manifest.json"
            ),
            "formal_verifier_agentic_proof_safety_policy_jsonl": str(
                out_dir
                / "formal_verifier_agentic_proof_safety_policy"
                / "formal_verifier_agentic_proof_safety_policy.jsonl"
            ),
            "formal_verifier_agentic_proof_safety_policy_report": str(
                out_dir
                / "formal_verifier_agentic_proof_safety_policy"
                / "formal_verifier_agentic_proof_safety_policy.md"
            ),
            "formal_verifier_agentic_proof_attempt_population": str(
                out_dir
                / "formal_verifier_agentic_proof_attempt_population"
                / "formal_verifier_agentic_proof_attempt_population_manifest.json"
            ),
            "formal_verifier_agentic_proof_attempt_population_jsonl": str(
                out_dir
                / "formal_verifier_agentic_proof_attempt_population"
                / "formal_verifier_agentic_proof_attempt_population.jsonl"
            ),
            "formal_verifier_agentic_proof_attempt_population_report": str(
                out_dir
                / "formal_verifier_agentic_proof_attempt_population"
                / "formal_verifier_agentic_proof_attempt_population.md"
            ),
            "formal_verifier_agentic_proof_execution_queue": str(
                out_dir
                / "formal_verifier_agentic_proof_execution_queue"
                / "formal_verifier_agentic_proof_execution_queue_manifest.json"
            ),
            "formal_verifier_agentic_proof_execution_queue_jsonl": str(
                out_dir
                / "formal_verifier_agentic_proof_execution_queue"
                / "formal_verifier_agentic_proof_execution_queue.jsonl"
            ),
            "formal_verifier_agentic_proof_execution_queue_report": str(
                out_dir
                / "formal_verifier_agentic_proof_execution_queue"
                / "formal_verifier_agentic_proof_execution_queue.md"
            ),
            "formal_verifier_agentic_proof_execution_materializer": str(
                out_dir
                / "formal_verifier_agentic_proof_execution_materializer"
                / "formal_verifier_agentic_proof_execution_materializer_manifest.json"
            ),
            "formal_verifier_agentic_proof_execution_materializer_jsonl": str(
                out_dir
                / "formal_verifier_agentic_proof_execution_materializer"
                / "formal_verifier_agentic_proof_execution_materializer.jsonl"
            ),
            "formal_verifier_agentic_proof_execution_materializer_report": str(
                out_dir
                / "formal_verifier_agentic_proof_execution_materializer"
                / "formal_verifier_agentic_proof_execution_materializer.md"
            ),
            "formal_verifier_agentic_proof_execution_artifact_verifier": str(
                out_dir
                / "formal_verifier_agentic_proof_execution_artifact_verifier"
                / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
            ),
            "formal_verifier_agentic_proof_execution_artifact_verifier_jsonl": str(
                out_dir
                / "formal_verifier_agentic_proof_execution_artifact_verifier"
                / "formal_verifier_agentic_proof_execution_artifact_verifier.jsonl"
            ),
            "formal_verifier_agentic_proof_execution_artifact_verifier_report": str(
                out_dir
                / "formal_verifier_agentic_proof_execution_artifact_verifier"
                / "formal_verifier_agentic_proof_execution_artifact_verifier.md"
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_queue": str(
                out_dir
                / "formal_verifier_agentic_proof_source_theorem_promotion_queue"
                / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json"
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_queue_jsonl": str(
                out_dir
                / "formal_verifier_agentic_proof_source_theorem_promotion_queue"
                / "formal_verifier_agentic_proof_source_theorem_promotion_queue.jsonl"
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_queue_report": str(
                out_dir
                / "formal_verifier_agentic_proof_source_theorem_promotion_queue"
                / "formal_verifier_agentic_proof_source_theorem_promotion_queue.md"
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution": str(
                out_dir
                / "formal_verifier_agentic_proof_source_theorem_target_resolution"
                / "formal_verifier_agentic_proof_source_theorem_target_resolution_manifest.json"
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_jsonl": str(
                out_dir
                / "formal_verifier_agentic_proof_source_theorem_target_resolution"
                / "formal_verifier_agentic_proof_source_theorem_target_resolution.jsonl"
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_overlays": str(
                out_dir
                / "formal_verifier_agentic_proof_source_theorem_target_resolution"
                / "formal_verifier_agentic_proof_source_theorem_target_resolution_overlays.jsonl"
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_report": str(
                out_dir
                / "formal_verifier_agentic_proof_source_theorem_target_resolution"
                / "formal_verifier_agentic_proof_source_theorem_target_resolution.md"
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
            "claim_ledger": str(out_dir / "claim_ledger" / "claim_ledger_manifest.json"),
            "claim_ledger_jsonl": str(out_dir / "claim_ledger" / "claim_ledger.jsonl"),
            "claim_ledger_report": str(out_dir / "claim_ledger" / "claim_ledger.md"),
            "claim_ledger_actions": str(
                out_dir / "claim_ledger_actions" / "claim_ledger_action_manifest.json"
            ),
            "claim_ledger_actions_jsonl": str(out_dir / "claim_ledger_actions" / "claim_ledger_actions.jsonl"),
            "claim_ledger_actions_report": str(out_dir / "claim_ledger_actions" / "claim_ledger_actions.md"),
            "stat_claim_certificate_plan": str(
                out_dir / "stat_claim_certificate_plan" / "stat_claim_certificate_plan_manifest.json"
            ),
            "stat_claim_certificate_targets_jsonl": str(
                out_dir / "stat_claim_certificate_plan" / "stat_claim_certificate_targets.jsonl"
            ),
            "stat_claim_certificate_plan_report": str(
                out_dir / "stat_claim_certificate_plan" / "stat_claim_certificate_plan.md"
            ),
            "stat_claim_certificate_checker_audit": str(
                out_dir
                / "stat_claim_certificate_checker_audit"
                / "stat_claim_certificate_checker_audit_manifest.json"
            ),
            "stat_claim_certificate_checker_lean_dir": str(
                out_dir / "stat_claim_certificate_checker_audit" / "lean"
            ),
            "stat_claim_certificate_checker_attempts": str(
                out_dir / "stat_claim_certificate_checker_audit" / "proof_attempts.jsonl"
            ),
            "stat_claim_certificate_checker_report": str(
                out_dir
                / "stat_claim_certificate_checker_audit"
                / "stat_claim_certificate_checker_audit.md"
            ),
            "stat_claim_certificate_readiness": str(
                out_dir
                / "stat_claim_certificate_readiness"
                / "stat_claim_certificate_readiness_manifest.json"
            ),
            "stat_claim_certificate_readiness_jsonl": str(
                out_dir
                / "stat_claim_certificate_readiness"
                / "stat_claim_certificate_readiness.jsonl"
            ),
            "stat_claim_certificate_readiness_report": str(
                out_dir
                / "stat_claim_certificate_readiness"
                / "stat_claim_certificate_readiness.md"
            ),
            "stat_claim_certificate_witness_queue": str(
                out_dir
                / "stat_claim_certificate_witness_queue"
                / "stat_claim_certificate_witness_queue_manifest.json"
            ),
            "stat_claim_certificate_witness_tasks": str(
                out_dir
                / "stat_claim_certificate_witness_queue"
                / "stat_claim_certificate_witness_tasks.jsonl"
            ),
            "stat_claim_certificate_witness_blocked": str(
                out_dir
                / "stat_claim_certificate_witness_queue"
                / "stat_claim_certificate_witness_blocked.jsonl"
            ),
            "stat_claim_certificate_witness_queue_report": str(
                out_dir
                / "stat_claim_certificate_witness_queue"
                / "stat_claim_certificate_witness_queue.md"
            ),
            "stat_claim_certificate_witness_materializer": str(
                out_dir
                / "stat_claim_certificate_witness_materializer"
                / "stat_claim_certificate_witness_materializer_manifest.json"
            ),
            "stat_claim_certificate_witness_drafts": str(
                out_dir
                / "stat_claim_certificate_witness_materializer"
                / "stat_claim_certificate_witness_drafts.jsonl"
            ),
            "stat_claim_certificate_witness_draft_dir": str(
                out_dir / "stat_claim_certificate_witness_materializer" / "witness_drafts"
            ),
            "stat_claim_certificate_witness_materializer_report": str(
                out_dir
                / "stat_claim_certificate_witness_materializer"
                / "stat_claim_certificate_witness_materializer.md"
            ),
            "stat_claim_certificate_witness_prompt_packets": str(
                out_dir
                / "stat_claim_certificate_witness_prompt_packets"
                / "stat_claim_certificate_witness_prompt_packets_manifest.json"
            ),
            "stat_claim_certificate_witness_prompt_packets_jsonl": str(
                out_dir
                / "stat_claim_certificate_witness_prompt_packets"
                / "stat_claim_certificate_witness_prompt_packets.jsonl"
            ),
            "stat_claim_certificate_witness_prompt_packets_report": str(
                out_dir
                / "stat_claim_certificate_witness_prompt_packets"
                / "stat_claim_certificate_witness_prompt_packets.md"
            ),
            "stat_claim_certificate_witness_context_packets": str(
                out_dir
                / "stat_claim_certificate_witness_context_packets"
                / "stat_claim_certificate_witness_context_packets_manifest.json"
            ),
            "stat_claim_certificate_witness_context_packets_jsonl": str(
                out_dir
                / "stat_claim_certificate_witness_context_packets"
                / "stat_claim_certificate_witness_context_packets.jsonl"
            ),
            "stat_claim_certificate_witness_context_packets_report": str(
                out_dir
                / "stat_claim_certificate_witness_context_packets"
                / "stat_claim_certificate_witness_context_packets.md"
            ),
            "stat_claim_certificate_witness_context_triage": str(
                out_dir
                / "stat_claim_certificate_witness_context_triage"
                / "stat_claim_certificate_witness_context_triage_manifest.json"
            ),
            "stat_claim_certificate_witness_context_triage_jsonl": str(
                out_dir
                / "stat_claim_certificate_witness_context_triage"
                / "stat_claim_certificate_witness_context_triage.jsonl"
            ),
            "stat_claim_certificate_witness_context_worker_ready": str(
                out_dir
                / "stat_claim_certificate_witness_context_triage"
                / "stat_claim_certificate_witness_context_worker_ready.jsonl"
            ),
            "stat_claim_certificate_witness_context_source_review": str(
                out_dir
                / "stat_claim_certificate_witness_context_triage"
                / "stat_claim_certificate_witness_context_source_review.jsonl"
            ),
            "stat_claim_certificate_witness_context_triage_report": str(
                out_dir
                / "stat_claim_certificate_witness_context_triage"
                / "stat_claim_certificate_witness_context_triage.md"
            ),
            "stat_claim_certificate_witness_response_validation": str(
                out_dir
                / "stat_claim_certificate_witness_response_validation"
                / "stat_claim_certificate_witness_response_validation_manifest.json"
            ),
            "stat_claim_certificate_witness_response_validation_jsonl": str(
                out_dir
                / "stat_claim_certificate_witness_response_validation"
                / "stat_claim_certificate_witness_response_validation.jsonl"
            ),
            "stat_claim_certificate_witness_response_validation_report": str(
                out_dir
                / "stat_claim_certificate_witness_response_validation"
                / "stat_claim_certificate_witness_response_validation.md"
            ),
            "stat_claim_certificate_witness_response_apply": str(
                out_dir
                / "stat_claim_certificate_witness_response_apply"
                / "stat_claim_certificate_witness_response_apply_manifest.json"
            ),
            "stat_claim_certificate_witness_response_apply_jsonl": str(
                out_dir
                / "stat_claim_certificate_witness_response_apply"
                / "stat_claim_certificate_witness_response_apply.jsonl"
            ),
            "stat_claim_certificate_witness_response_apply_drafts": str(
                out_dir
                / "stat_claim_certificate_witness_response_apply"
                / "stat_claim_certificate_witness_drafts.jsonl"
            ),
            "stat_claim_certificate_witness_response_apply_draft_dir": str(
                out_dir / "stat_claim_certificate_witness_response_apply" / "witness_drafts"
            ),
            "stat_claim_certificate_witness_response_apply_report": str(
                out_dir
                / "stat_claim_certificate_witness_response_apply"
                / "stat_claim_certificate_witness_response_apply.md"
            ),
            "stat_claim_certificate_witness_validator": str(
                out_dir
                / "stat_claim_certificate_witness_validator"
                / "stat_claim_certificate_witness_validator_manifest.json"
            ),
            "stat_claim_certificate_witness_validation": str(
                out_dir
                / "stat_claim_certificate_witness_validator"
                / "stat_claim_certificate_witness_validation.jsonl"
            ),
            "stat_claim_certificate_witness_validator_report": str(
                out_dir
                / "stat_claim_certificate_witness_validator"
                / "stat_claim_certificate_witness_validator.md"
            ),
            "theorem_composition": str(
                out_dir / "theorem_composition" / "theorem_composition_manifest.json"
            ),
            "theorem_composition_jsonl": str(
                out_dir / "theorem_composition" / "theorem_composition_packets.jsonl"
            ),
            "theorem_composition_report": str(out_dir / "theorem_composition" / "theorem_composition.md"),
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
    coding_agent_repair_eval_manifest = _coding_agent_generated_code_repair_eval_overlay(
        out_dir
    )
    payload["counts"].update(
        {
            "coding_agent_generated_code_repair_capability_evidence_ok": bool(
                coding_agent_repair_eval_manifest["capability_evidence_ok"]
            ),
            "coding_agent_algorithm_capability_evidence_ok": bool(
                coding_agent_repair_eval_manifest["algorithm_capability_evidence_ok"]
            ),
            "coding_agent_simulation_capability_evidence_ok": bool(
                coding_agent_repair_eval_manifest["simulation_capability_evidence_ok"]
            ),
            "coding_agent_algorithm_repair_sequences": int(
                coding_agent_repair_eval_manifest["algorithm_repair_sequences"]
            ),
            "coding_agent_simulation_repair_sequences": int(
                coding_agent_repair_eval_manifest["simulation_repair_sequences"]
            ),
            "coding_agent_generated_code_repair_live_generator": bool(
                coding_agent_repair_eval_manifest["live_generator"]
            ),
            "coding_agent_generated_code_repair_static_or_fixture_only": bool(
                coding_agent_repair_eval_manifest["static_or_fixture_only"]
            ),
            "coding_agent_generated_code_repair_fixture_plumbing_ok": bool(
                coding_agent_repair_eval_manifest["fixture_plumbing_ok"]
            ),
            "coding_agent_generated_code_repair_provider": str(
                coding_agent_repair_eval_manifest["provider_name"]
            ),
        }
    )
    if bool(coding_agent_repair_eval_manifest["available"]):
        payload["artifacts"]["coding_agent_generated_code_repair_eval"] = str(
            coding_agent_repair_eval_manifest["manifest_path"]
        )
    formalizer_lean_repair_eval_manifest = (
        _formalizer_lean_candidate_repair_eval_overlay(out_dir)
    )
    payload["counts"].update(
        {
            "formalizer_lean_candidate_repair_capability_evidence_ok": bool(
                formalizer_lean_repair_eval_manifest["capability_evidence_ok"]
            ),
            "formalizer_lean_candidate_repair_live_generator": bool(
                formalizer_lean_repair_eval_manifest["live_generator"]
            ),
            "formalizer_lean_candidate_repair_static_or_fixture_only": bool(
                formalizer_lean_repair_eval_manifest["static_or_fixture_only"]
            ),
            "formalizer_lean_candidate_repair_sequences": int(
                formalizer_lean_repair_eval_manifest["repair_sequences"]
            ),
            "formalizer_lean_candidate_repair_local_lean_checked": int(
                formalizer_lean_repair_eval_manifest["local_lean_checked"]
            ),
            "formalizer_lean_candidate_repair_local_lean_compiled": int(
                formalizer_lean_repair_eval_manifest["local_lean_compiled"]
            ),
            "formalizer_lean_candidate_repair_candidate_kernel_verified": bool(
                formalizer_lean_repair_eval_manifest["candidate_kernel_verified"]
            ),
            "formalizer_lean_candidate_repair_source_theorem_kernel_verified": bool(
                formalizer_lean_repair_eval_manifest[
                    "source_theorem_kernel_verified"
                ]
            ),
            "formalizer_lean_candidate_repair_provider": str(
                formalizer_lean_repair_eval_manifest["provider_name"]
            ),
        }
    )
    if bool(formalizer_lean_repair_eval_manifest["available"]):
        payload["artifacts"]["formalizer_lean_candidate_repair_eval"] = str(
            formalizer_lean_repair_eval_manifest["manifest_path"]
        )
    formalizer_pseudo_formal_packet_eval_manifest = (
        _formalizer_pseudo_formal_packet_eval_overlay(out_dir)
    )
    payload["counts"].update(
        {
            "formalizer_pseudo_formal_packet_component_gate_capability_evidence_ok": bool(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "capability_evidence_ok"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_live_generator": bool(
                formalizer_pseudo_formal_packet_eval_manifest["live_generator"]
            ),
            "formalizer_pseudo_formal_packet_component_gate_static_or_fixture_only": bool(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "static_or_fixture_only"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_fixture_plumbing_ok": bool(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "fixture_plumbing_ok"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_proof_evidence_status_ok": bool(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "proof_evidence_status_ok"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_no_theorem_proof_claim": bool(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "no_theorem_proof_claim"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_pseudo_formal_packets": int(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "n_pseudo_formal_packets"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_work_order_rows": int(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "n_pseudo_formal_work_order_rows"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_routable_work_order_rows": int(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "n_pseudo_formal_routable_work_order_rows"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_routable_row_kinds": list(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "pseudo_formal_routable_row_kinds"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_routable_target_lanes": list(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "pseudo_formal_routable_target_lanes"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_exact_semantic_definition_lane_present": bool(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "exact_semantic_definition_lane_present"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_nonproof_boundary_preserved": bool(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "nonproof_boundary_preserved"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_raw_model_output_written": bool(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "raw_model_output_written"
                ]
            ),
            "formalizer_pseudo_formal_packet_component_gate_provider": str(
                formalizer_pseudo_formal_packet_eval_manifest["provider_name"]
            ),
            "formalizer_pseudo_formal_packet_component_gate_backend_provider": str(
                formalizer_pseudo_formal_packet_eval_manifest[
                    "backend_provider_name"
                ]
            ),
        }
    )
    if bool(formalizer_pseudo_formal_packet_eval_manifest["available"]):
        payload["artifacts"]["formalizer_pseudo_formal_packet_eval"] = str(
            formalizer_pseudo_formal_packet_eval_manifest["manifest_path"]
        )
    pseudo_formal_block_verifier_component_gate_manifest = (
        _pseudo_formal_block_verifier_component_gate_overlay(out_dir)
    )
    payload["counts"].update(
        {
            "pseudo_formal_block_verifier_component_gate_capability_evidence_ok": bool(
                pseudo_formal_block_verifier_component_gate_manifest[
                    "capability_evidence_ok"
                ]
            ),
            "pseudo_formal_block_verifier_component_gate_live_generator": bool(
                pseudo_formal_block_verifier_component_gate_manifest["live_generator"]
            ),
            "pseudo_formal_block_verifier_component_gate_static_or_fixture_only": bool(
                pseudo_formal_block_verifier_component_gate_manifest[
                    "static_or_fixture_only"
                ]
            ),
            "pseudo_formal_block_verifier_component_gate_fixture_plumbing_ok": bool(
                pseudo_formal_block_verifier_component_gate_manifest[
                    "fixture_plumbing_ok"
                ]
            ),
            "pseudo_formal_block_verifier_component_gate_prompt_packets": int(
                pseudo_formal_block_verifier_component_gate_manifest[
                    "n_prompt_packets"
                ]
            ),
            "pseudo_formal_block_verifier_component_gate_valid_responses": int(
                pseudo_formal_block_verifier_component_gate_manifest[
                    "n_valid_responses"
                ]
            ),
            "pseudo_formal_block_verifier_component_gate_runtime_learning_rows": int(
                pseudo_formal_block_verifier_component_gate_manifest[
                    "n_runtime_learning_rows"
                ]
            ),
            "pseudo_formal_block_verifier_component_gate_accepted_blocks": int(
                pseudo_formal_block_verifier_component_gate_manifest[
                    "n_accepted_blocks"
                ]
            ),
            "pseudo_formal_block_verifier_component_gate_failed_blocks": int(
                pseudo_formal_block_verifier_component_gate_manifest[
                    "n_failed_blocks"
                ]
            ),
            "pseudo_formal_block_verifier_component_gate_provider": str(
                pseudo_formal_block_verifier_component_gate_manifest["provider_name"]
            ),
            "pseudo_formal_block_verifier_component_gate_backend_provider": str(
                pseudo_formal_block_verifier_component_gate_manifest[
                    "backend_provider_name"
                ]
            ),
        }
    )
    if bool(pseudo_formal_block_verifier_component_gate_manifest["available"]):
        payload["artifacts"]["pseudo_formal_block_verifier_component_gate"] = str(
            pseudo_formal_block_verifier_component_gate_manifest["manifest_path"]
        )
    architect_policy_eval_manifest = _architect_research_path_policy_eval_overlay(
        out_dir
    )
    payload["counts"].update(
        {
            "architect_research_path_policy_capability_evidence_ok": bool(
                architect_policy_eval_manifest["capability_evidence_ok"]
            ),
            "architect_research_path_policy_live_generator": bool(
                architect_policy_eval_manifest["live_generator"]
            ),
            "architect_research_path_policy_static_or_fixture_only": bool(
                architect_policy_eval_manifest["static_or_fixture_only"]
            ),
            "architect_research_path_policy_cases": int(
                architect_policy_eval_manifest["n_cases"]
            ),
            "architect_research_path_policy_cases_ok": int(
                architect_policy_eval_manifest["n_cases_ok"]
            ),
            "architect_research_path_policy_problem_analysis": int(
                architect_policy_eval_manifest["n_with_problem_analysis"]
            ),
            "architect_research_path_policy_knowledge_bank_plan": int(
                architect_policy_eval_manifest["n_with_stat_knowledge_bank_plan"]
            ),
            "architect_research_path_policy_literature_fair_comparison_plan": int(
                architect_policy_eval_manifest[
                    "n_with_literature_fair_comparison_plan"
                ]
            ),
            "architect_research_path_policy_provider": str(
                architect_policy_eval_manifest["provider_name"]
            ),
        }
    )
    if bool(architect_policy_eval_manifest["available"]):
        payload["artifacts"]["architect_research_path_policy_eval"] = str(
            architect_policy_eval_manifest["manifest_path"]
        )
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


def _research_agent_runtime_exact_semantic_definition_authoring_count_rollup(
    manifest: Mapping[str, Any],
) -> dict[str, object]:
    def _manifest_int(key: str) -> int:
        return int(manifest.get(key, 0) or 0)

    def _manifest_bool(key: str) -> bool:
        return bool(manifest.get(key, False))

    def _manifest_str(key: str) -> str:
        return str(manifest.get(key, "") or "").strip()

    primary_required = _manifest_bool(
        "source_theorem_exact_semantic_definition_authoring_worker_required"
    )
    retry_required = _manifest_bool(
        "source_theorem_exact_semantic_definition_authoring_retry_tasks_required"
    ) or _manifest_bool(
        "source_theorem_exact_semantic_definition_authoring_repair_tasks_required"
    )
    structural_reformulation_required = _manifest_bool(
        "source_theorem_exact_semantic_definition_structural_reformulation_tasks_required"
    ) or _manifest_int(
        "source_theorem_exact_semantic_definition_structural_reformulation_n_tasks"
    ) > 0
    late_required = _manifest_bool(
        "source_theorem_exact_semantic_definition_late_authoring_worker_ran"
    ) or _manifest_int(
        "source_theorem_exact_semantic_definition_late_authoring_worker_n_manifests"
    ) > 0
    post_runtime_worker_lineage_ok = _manifest_bool(
        "post_runtime_exact_semantic_definition_authoring_worker_lineage_ok"
    )
    post_runtime_materializer_lineage_ok = _manifest_bool(
        "post_runtime_exact_semantic_definition_authoring_candidate_materializer_lineage_ok"
    )
    post_runtime_lean_repair_lineage_ok = _manifest_bool(
        "post_runtime_exact_semantic_definition_materialized_lean_repair_executor_lineage_ok"
    )
    post_runtime_worker_provider_name = (
        _manifest_str("post_runtime_exact_semantic_definition_authoring_worker_provider_name")
        if post_runtime_worker_lineage_ok
        else ""
    )
    post_runtime_worker_backend_provider_name = (
        _manifest_str(
            "post_runtime_exact_semantic_definition_authoring_worker_backend_provider_name"
        )
        if post_runtime_worker_lineage_ok
        else ""
    )
    provider_names = list(
        dict.fromkeys(
            value
            for value in (
                _manifest_str(
                    "source_theorem_exact_semantic_definition_authoring_worker_provider_name"
                ),
                _manifest_str(
                    "source_theorem_exact_semantic_definition_authoring_retry_worker_provider_name"
                ),
                *(
                    str(value).strip()
                    for value in manifest.get(
                        "source_theorem_exact_semantic_definition_late_authoring_worker_provider_names",
                        [],
                    )
                    or []
                ),
                post_runtime_worker_provider_name,
            )
            if value
        )
    )
    backend_provider_names = list(
        dict.fromkeys(
            value
            for value in (
                _manifest_str(
                    "source_theorem_exact_semantic_definition_authoring_worker_backend_provider_name"
                ),
                _manifest_str(
                    "source_theorem_exact_semantic_definition_authoring_retry_worker_backend_provider_name"
                ),
                *(
                    str(value).strip()
                    for value in manifest.get(
                        "source_theorem_exact_semantic_definition_late_authoring_worker_backend_provider_names",
                        [],
                    )
                    or []
                ),
                post_runtime_worker_backend_provider_name,
            )
            if value
        )
    )
    post_runtime_tasks = (
        _manifest_int(
            "post_runtime_exact_semantic_definition_authoring_worker_n_source_authoring_tasks"
        )
        if post_runtime_worker_lineage_ok
        else 0
    )
    post_runtime_llm_attempted = (
        _manifest_int(
            "post_runtime_exact_semantic_definition_authoring_worker_n_llm_attempted"
        )
        if post_runtime_worker_lineage_ok
        else 0
    )
    post_runtime_live_llm_attempted = (
        _manifest_int(
            "post_runtime_exact_semantic_definition_authoring_worker_n_live_llm_attempted"
        )
        if post_runtime_worker_lineage_ok
        else 0
    )
    post_runtime_candidate_packets = (
        _manifest_int(
            "post_runtime_exact_semantic_definition_authoring_worker_n_candidate_packets"
        )
        if post_runtime_worker_lineage_ok
        else 0
    )
    post_runtime_materialized_tasks = (
        _manifest_int(
            "post_runtime_exact_semantic_definition_authoring_candidate_materializer_n_materialized_lean_repair_tasks"
        )
        if post_runtime_materializer_lineage_ok
        else 0
    )
    post_runtime_local_lean_checked = (
        _manifest_int(
            "post_runtime_exact_semantic_definition_materialized_lean_repair_executor_n_local_lean_checked"
        )
        if post_runtime_lean_repair_lineage_ok
        else 0
    )
    post_runtime_local_lean_compiled = (
        _manifest_int(
            "post_runtime_exact_semantic_definition_materialized_lean_repair_executor_n_local_lean_compiled"
        )
        if post_runtime_lean_repair_lineage_ok
        else 0
    )
    post_runtime_lean_repair_by_failure = (
        dict(
            manifest.get(
                "post_runtime_exact_semantic_definition_materialized_lean_repair_executor_by_failure_classification",
                {},
            )
            or {}
        )
        if post_runtime_lean_repair_lineage_ok
        else {}
    )
    post_runtime_lean_repair_dominant_failure = (
        _manifest_str(
            "post_runtime_exact_semantic_definition_materialized_lean_repair_executor_dominant_failure_classification"
        )
        if post_runtime_lean_repair_lineage_ok
        else ""
    )
    return {
        "research_agent_runtime_exact_semantic_definition_authoring_required": (
            primary_required
            or retry_required
            or structural_reformulation_required
            or late_required
        ),
        "research_agent_runtime_exact_semantic_definition_authoring_primary_required": primary_required,
        "research_agent_runtime_exact_semantic_definition_authoring_retry_required": retry_required,
        "research_agent_runtime_exact_semantic_definition_authoring_structural_reformulation_required": structural_reformulation_required,
        "research_agent_runtime_exact_semantic_definition_authoring_late_required": late_required,
        "research_agent_runtime_exact_semantic_definition_authoring_tasks": (
            _manifest_int("n_source_theorem_exact_semantic_definition_authoring_tasks")
            + _manifest_int(
                "source_theorem_exact_semantic_definition_authoring_retry_n_tasks"
            )
            + _manifest_int(
                "source_theorem_exact_semantic_definition_structural_reformulation_n_tasks"
            )
            + post_runtime_tasks
        ),
        "research_agent_runtime_exact_semantic_definition_authoring_structural_reformulation_tasks": _manifest_int(
            "source_theorem_exact_semantic_definition_structural_reformulation_n_tasks"
        ),
        "research_agent_runtime_exact_semantic_definition_authoring_llm_attempted": (
            _manifest_int(
                "source_theorem_exact_semantic_definition_authoring_worker_n_llm_attempted"
            )
            + _manifest_int(
                "source_theorem_exact_semantic_definition_authoring_retry_worker_n_llm_attempted"
            )
            + _manifest_int(
                "source_theorem_exact_semantic_definition_late_authoring_worker_n_llm_attempted"
            )
            + post_runtime_llm_attempted
        ),
        "research_agent_runtime_exact_semantic_definition_authoring_live_llm_attempted": (
            _manifest_int(
                "source_theorem_exact_semantic_definition_authoring_worker_n_live_llm_attempted"
            )
            + _manifest_int(
                "source_theorem_exact_semantic_definition_authoring_retry_worker_n_live_llm_attempted"
            )
            + _manifest_int(
                "source_theorem_exact_semantic_definition_late_authoring_worker_n_live_llm_attempted"
            )
            + post_runtime_live_llm_attempted
        ),
        "research_agent_runtime_exact_semantic_definition_authoring_provider_names": provider_names,
        "research_agent_runtime_exact_semantic_definition_authoring_backend_provider_names": backend_provider_names,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_attached": _manifest_bool(
            "post_runtime_exact_semantic_definition_authoring_worker_attached"
        ),
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_lineage_ok": post_runtime_worker_lineage_ok,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_live_llm_attempted": post_runtime_live_llm_attempted,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_worker_candidate_packets": post_runtime_candidate_packets,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_materializer_lineage_ok": post_runtime_materializer_lineage_ok,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_materialized_lean_repair_tasks": post_runtime_materialized_tasks,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_lean_repair_lineage_ok": post_runtime_lean_repair_lineage_ok,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_checked": post_runtime_local_lean_checked,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_local_lean_compiled": post_runtime_local_lean_compiled,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_lean_repair_by_failure_classification": post_runtime_lean_repair_by_failure,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_lean_repair_dominant_failure_classification": post_runtime_lean_repair_dominant_failure,
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_proofengineer_state": (
            _manifest_str(
                "post_runtime_exact_semantic_definition_materialized_lean_repair_executor_proofengineer_state"
            )
            if post_runtime_lean_repair_lineage_ok
            else ""
        ),
        "research_agent_runtime_exact_semantic_definition_authoring_post_runtime_proof_evidence_status": (
            _manifest_str(
                "post_runtime_exact_semantic_definition_materialized_lean_repair_executor_proof_evidence_status"
            )
            if post_runtime_lean_repair_lineage_ok
            else ""
        ),
    }


def _research_agent_runtime_capability_gap_routing_followup_commands(
    manifest: Mapping[str, Any],
    *,
    limit: int = 4,
) -> list[dict[str, str]]:
    rows = manifest.get("runtime_capability_gap_routing_rows", [])
    if not isinstance(rows, list):
        return []
    priority_pinned_requirement_ids = {
        str(value).strip()
        for value in manifest.get(
            "runtime_capability_gap_routing_input_priority_pinned_requirement_ids",
            [],
        )
        or []
        if str(value).strip()
    }
    ordered_rows = sorted(
        (
            (index, row)
            for index, row in enumerate(rows)
            if isinstance(row, Mapping)
            and str(row.get("recommended_capability_eval_command", "") or "").strip()
        ),
        key=lambda item: _research_agent_runtime_capability_gap_followup_sort_key(
            item[1],
            source_index=item[0],
            priority_pinned_requirement_ids=priority_pinned_requirement_ids,
        ),
    )
    commands: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for _, row in ordered_rows:
        command = str(row.get("recommended_capability_eval_command", "") or "").strip()
        requirement_id = str(row.get("requirement_id", "") or "").strip()
        key = (requirement_id, command)
        if key in seen:
            continue
        seen.add(key)
        commands.append(
            {
                "requirement_id": requirement_id,
                "owner_subsystem": str(
                    row.get("next_owner_subsystem", "") or ""
                ).strip(),
                "scope": str(row.get("scope", "") or "").strip(),
                "priority": str(row.get("priority", "") or "").strip(),
                "retention_selection": str(
                    row.get("retention_selection", "") or ""
                ).strip(),
                "retention_selection_boundary": str(
                    row.get("retention_selection_boundary", "") or ""
                ).strip(),
                "proof_evidence_status": str(
                    row.get("proof_evidence_status", "") or ""
                ).strip(),
                "routing_boundary": str(
                    row.get("routing_boundary", "") or ""
                ).strip(),
                "command": command,
            }
        )
        if len(commands) >= limit:
            break
    return commands


def _research_agent_runtime_capability_gap_followup_sort_key(
    row: Mapping[str, Any],
    *,
    source_index: int,
    priority_pinned_requirement_ids: set[str],
) -> tuple[int, int, int, int]:
    requirement_id = str(row.get("requirement_id", "") or "").strip()
    retention_selection = str(row.get("retention_selection", "") or "").strip()
    priority_pinned = (
        retention_selection == "priority_pinned"
        or requirement_id in priority_pinned_requirement_ids
    )
    scope = str(row.get("scope", "") or "").strip()
    try:
        priority = int(row.get("priority", source_index + 1) or source_index + 1)
    except (TypeError, ValueError):
        priority = source_index + 1
    return (
        0 if priority_pinned else 1,
        0 if scope == "integrated_runtime" else 1,
        priority,
        source_index,
    )


def _proof_search_kernel_rerun_local_lean_overlay(out_dir: Path) -> dict[str, object]:
    manifest_path = (
        out_dir.parent
        / "proof_search_kernel_rerun_local_lean"
        / "proof_search_audit_manifest.json"
    )
    empty = {
        "manifest_path": "",
        "results_jsonl": "",
        "n_obligations": 0,
        "n_solved": 0,
        "n_kernel_verified": 0,
        "verifier": "",
        "all_kernel_verified_if_verifier_requires_kernel": False,
    }
    if not manifest_path.exists():
        return empty
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    return {
        "manifest_path": str(manifest_path),
        "results_jsonl": str(payload.get("results_jsonl", "")),
        "n_obligations": int(payload.get("n_obligations", 0) or 0),
        "n_solved": int(payload.get("n_solved", 0) or 0),
        "n_kernel_verified": int(payload.get("n_kernel_verified", 0) or 0),
        "verifier": str(payload.get("verifier", "")),
        "all_kernel_verified_if_verifier_requires_kernel": bool(
            payload.get("all_kernel_verified_if_verifier_requires_kernel", False)
        ),
    }


def _coding_agent_generated_code_repair_eval_overlay(out_dir: Path) -> dict[str, object]:
    manifest_path = _coding_agent_generated_code_repair_eval_manifest_path(out_dir)
    empty = {
        "available": False,
        "manifest_path": "",
        "provider_name": "",
        "backend_provider_name": "",
        "model": "",
        "live_generator": False,
        "capability_evidence_ok": False,
        "algorithm_capability_evidence_ok": False,
        "simulation_capability_evidence_ok": False,
        "algorithm_repair_sequences": 0,
        "simulation_repair_sequences": 0,
        "fixture_plumbing_ok": False,
        "static_or_fixture_only": False,
        "proof_evidence_status": "",
    }
    if not manifest_path.exists():
        return empty
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    provider_name = normalize_generator_provider_name(payload.get("provider_name", ""))
    backend_provider_name = normalize_generator_provider_name(
        payload.get("backend_provider_name", provider_name)
    )
    raw_component_backend_provider_names = payload.get(
        "component_backend_provider_names",
        [],
    )
    if isinstance(raw_component_backend_provider_names, str):
        raw_component_backend_provider_names = [raw_component_backend_provider_names]
    elif not isinstance(raw_component_backend_provider_names, (list, tuple)):
        raw_component_backend_provider_names = []
    component_backend_provider_names = [
        normalize_generator_provider_name(name)
        for name in raw_component_backend_provider_names
        if normalize_generator_provider_name(name)
    ]
    if not component_backend_provider_names and backend_provider_name:
        component_backend_provider_names = [backend_provider_name]
    backend_live = bool(component_backend_provider_names) and all(
        is_live_generator_backend(provider_name, name)
        for name in component_backend_provider_names
    )
    live_generator = bool(payload.get("live_generator", False) and backend_live)
    algorithm_capability_evidence_ok = bool(
        payload.get("algorithm_capability_evidence_ok", False)
    )
    simulation_capability_evidence_ok = bool(
        payload.get("simulation_capability_evidence_ok", False)
    )
    capability_evidence_ok = bool(
        live_generator
        and algorithm_capability_evidence_ok
        and simulation_capability_evidence_ok
        and payload.get("capability_evidence_ok", False)
    )
    return {
        "available": True,
        "manifest_path": str(manifest_path),
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "component_backend_provider_names": component_backend_provider_names,
        "model": str(payload.get("model", "")),
        "live_generator": live_generator,
        "capability_evidence_ok": capability_evidence_ok,
        "algorithm_capability_evidence_ok": algorithm_capability_evidence_ok,
        "simulation_capability_evidence_ok": simulation_capability_evidence_ok,
        "algorithm_repair_sequences": int(
            payload.get("algorithm_repair_sequences", 0) or 0
        ),
        "simulation_repair_sequences": int(
            payload.get("simulation_repair_sequences", 0) or 0
        ),
        "fixture_plumbing_ok": bool(payload.get("fixture_plumbing_ok", False)),
        "static_or_fixture_only": bool(
            payload.get("static_or_fixture_only", False) or not live_generator
        ),
        "proof_evidence_status": str(payload.get("proof_evidence_status", "")),
    }


def _coding_agent_generated_code_repair_eval_manifest_path(out_dir: Path) -> Path:
    canonical = (
        out_dir.parent
        / "coding_agent_generated_code_repair_eval"
        / "coding_agent_generated_code_repair_eval_manifest.json"
    )
    if canonical.exists():
        return canonical
    candidates = sorted(
        out_dir.parent.glob(
            "coding_agent_generated_code_repair_eval*/"
            "coding_agent_generated_code_repair_eval_manifest.json"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else canonical


def _formalizer_lean_candidate_repair_eval_overlay(out_dir: Path) -> dict[str, object]:
    manifest_path = _formalizer_lean_candidate_repair_eval_manifest_path(out_dir)
    empty = {
        "available": False,
        "manifest_path": "",
        "provider_name": "",
        "backend_provider_name": "",
        "model": "",
        "live_generator": False,
        "capability_evidence_ok": False,
        "candidate_kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "full_frontier_theorem_proved": False,
        "repair_sequences": 0,
        "local_lean_checked": 0,
        "local_lean_compiled": 0,
        "fixture_plumbing_ok": False,
        "static_or_fixture_only": False,
        "proof_evidence_status": "",
    }
    if not manifest_path.exists():
        return empty
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    provider_name = normalize_generator_provider_name(payload.get("provider_name", ""))
    backend_provider_name = normalize_generator_provider_name(
        payload.get("backend_provider_name", provider_name)
    )
    live_generator = bool(
        payload.get("live_generator", False)
        and is_live_generator_backend(provider_name, backend_provider_name)
    )
    repair_sequences = int(
        payload.get(
            "n_formalizer_lean_candidate_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    local_lean_checked = int(
        payload.get("n_formalizer_lean_candidate_local_lean_checked", 0)
        or 0
    )
    local_lean_compiled = int(
        payload.get("n_formalizer_lean_candidate_local_lean_compiled", 0)
        or 0
    )
    candidate_kernel_verified = bool(
        payload.get("candidate_kernel_verified", False)
    )
    source_theorem_kernel_verified = bool(
        payload.get("source_theorem_kernel_verified", False)
    )
    capability_evidence_ok = bool(
        live_generator
        and repair_sequences > 0
        and local_lean_checked > 0
        and local_lean_compiled > 0
        and candidate_kernel_verified
        and payload.get("capability_evidence_ok", False)
    )
    static_or_fixture_only = bool(
        payload.get("static_or_fixture_only", False) or not live_generator
    )
    fixture_plumbing_ok = bool(
        static_or_fixture_only
        and repair_sequences > 0
        and local_lean_compiled > 0
        and candidate_kernel_verified
    )
    return {
        "available": True,
        "manifest_path": str(manifest_path),
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "model": str(payload.get("model", "")),
        "live_generator": live_generator,
        "capability_evidence_ok": capability_evidence_ok,
        "candidate_kernel_verified": candidate_kernel_verified,
        "source_theorem_kernel_verified": source_theorem_kernel_verified,
        "full_frontier_theorem_proved": bool(
            payload.get("full_frontier_theorem_proved", False)
        ),
        "repair_sequences": repair_sequences,
        "local_lean_checked": local_lean_checked,
        "local_lean_compiled": local_lean_compiled,
        "fixture_plumbing_ok": fixture_plumbing_ok,
        "static_or_fixture_only": static_or_fixture_only,
        "proof_evidence_status": str(payload.get("proof_evidence_status", "")),
    }


def _formalizer_lean_candidate_repair_eval_manifest_path(out_dir: Path) -> Path:
    canonical = (
        out_dir.parent
        / "formalizer_lean_candidate_repair_eval"
        / "formalizer_lean_candidate_repair_eval_manifest.json"
    )
    if canonical.exists():
        return canonical
    candidates = sorted(
        out_dir.parent.glob(
            "formalizer_lean_candidate_repair_eval*/"
            "formalizer_lean_candidate_repair_eval_manifest.json"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else canonical


def _formalizer_pseudo_formal_packet_eval_overlay(out_dir: Path) -> dict[str, object]:
    manifest_path = _formalizer_pseudo_formal_packet_eval_manifest_path(out_dir)
    empty = {
        "available": False,
        "manifest_path": "",
        "provider_name": "",
        "backend_provider_name": "",
        "model": "",
        "live_generator": False,
        "capability_evidence_ok": False,
        "artifact_kind_ok": False,
        "proof_evidence_status_ok": False,
        "no_theorem_proof_claim": False,
        "n_pseudo_formal_packets": 0,
        "n_pseudo_formal_work_order_rows": 0,
        "n_pseudo_formal_routable_work_order_rows": 0,
        "pseudo_formal_routable_row_kinds": [],
        "pseudo_formal_routable_target_lanes": [],
        "exact_semantic_definition_lane_present": False,
        "nonproof_boundary_preserved": False,
        "raw_model_output_written": False,
        "fixture_plumbing_ok": False,
        "static_or_fixture_only": False,
        "proof_evidence_status": "",
        "all_ok": False,
        "errors": ["formalizer_pseudo_formal_packet_eval_manifest_missing"],
    }
    if not manifest_path.exists():
        return empty
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            **empty,
            "manifest_path": str(manifest_path),
            "errors": ["formalizer_pseudo_formal_packet_eval_manifest_unreadable"],
        }
    provider_name = normalize_generator_provider_name(payload.get("provider_name", ""))
    backend_provider_name = normalize_generator_provider_name(
        payload.get("backend_provider_name", provider_name)
    )
    live_generator = bool(
        payload.get("live_generator", False)
        and is_live_generator_backend(provider_name, backend_provider_name)
    )
    artifact_kind_ok = (
        str(payload.get("artifact_kind", ""))
        == "FormalizerPseudoFormalPacketEvalManifest"
    )
    proof_evidence_status = str(payload.get("proof_evidence_status", ""))
    proof_evidence_status_ok = (
        proof_evidence_status
        == "FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE"
    )
    capability_requirements = (
        payload.get("capability_evidence_requirements", {})
        if isinstance(payload.get("capability_evidence_requirements", {}), Mapping)
        else {}
    )
    n_pseudo_formal_packets = int(
        payload.get("n_pseudo_formal_packets", 0) or 0
    )
    n_pseudo_formal_work_order_rows = int(
        payload.get("n_pseudo_formal_work_order_rows", 0) or 0
    )
    n_pseudo_formal_routable_work_order_rows = int(
        payload.get("n_pseudo_formal_routable_work_order_rows", 0) or 0
    )
    row_kinds = [
        str(value)
        for value in payload.get("pseudo_formal_routable_row_kinds", [])
        if str(value)
    ]
    target_lanes = [
        str(value)
        for value in payload.get("pseudo_formal_routable_target_lanes", [])
        if str(value)
    ]
    exact_semantic_definition_lane_present = bool(
        payload.get("exact_semantic_definition_lane_present", False)
        or "source_theorem_exact_semantic_definition" in target_lanes
    )
    nonproof_boundary_preserved = bool(
        capability_requirements.get("nonproof_boundary_preserved", False)
        or payload.get("nonproof_boundary_preserved", False)
    )
    raw_model_output_written = bool(payload.get("raw_model_output_written", False))
    no_theorem_proof_claim = (
        payload.get("source_theorem_kernel_verified") is False
        and payload.get("full_frontier_theorem_proved") is False
    )
    static_or_fixture_only = bool(
        payload.get("static_or_fixture_only", False) or not live_generator
    )
    fixture_plumbing_ok = bool(
        payload.get("fixture_plumbing_ok", False)
        and artifact_kind_ok
        and proof_evidence_status_ok
        and n_pseudo_formal_packets > 0
        and n_pseudo_formal_routable_work_order_rows > 0
        and exact_semantic_definition_lane_present
        and nonproof_boundary_preserved
        and not raw_model_output_written
        and no_theorem_proof_claim
    )
    capability_evidence_ok = bool(
        live_generator
        and fixture_plumbing_ok
        and payload.get("capability_evidence_ok", False)
    )
    errors = [
        error
        for error in (
            "" if artifact_kind_ok else "artifact_kind_mismatch",
            ""
            if proof_evidence_status_ok
            else "proof_evidence_status_must_remain_non_proof",
            "" if live_generator else "live_generator_missing_or_static_backend",
            "" if n_pseudo_formal_packets > 0 else "pseudo_formal_packets_missing",
            ""
            if n_pseudo_formal_routable_work_order_rows > 0
            else "routable_work_order_rows_missing",
            ""
            if "source_theorem_exact_semantic_definition" in target_lanes
            else "exact_semantic_definition_lane_missing",
            ""
            if nonproof_boundary_preserved
            else "nonproof_boundary_not_preserved",
            "" if not raw_model_output_written else "raw_model_output_written",
            "" if no_theorem_proof_claim else "theorem_proof_claim_present",
        )
        if error
    ]
    return {
        "available": True,
        "manifest_path": str(manifest_path),
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "model": str(payload.get("model", "")),
        "live_generator": live_generator,
        "capability_evidence_ok": capability_evidence_ok,
        "artifact_kind_ok": artifact_kind_ok,
        "proof_evidence_status_ok": proof_evidence_status_ok,
        "no_theorem_proof_claim": no_theorem_proof_claim,
        "n_pseudo_formal_packets": n_pseudo_formal_packets,
        "n_pseudo_formal_work_order_rows": n_pseudo_formal_work_order_rows,
        "n_pseudo_formal_routable_work_order_rows": n_pseudo_formal_routable_work_order_rows,
        "pseudo_formal_routable_row_kinds": row_kinds,
        "pseudo_formal_routable_target_lanes": target_lanes,
        "exact_semantic_definition_lane_present": exact_semantic_definition_lane_present,
        "nonproof_boundary_preserved": nonproof_boundary_preserved,
        "raw_model_output_written": raw_model_output_written,
        "fixture_plumbing_ok": fixture_plumbing_ok,
        "static_or_fixture_only": static_or_fixture_only,
        "proof_evidence_status": proof_evidence_status,
        "all_ok": bool(
            artifact_kind_ok and proof_evidence_status_ok and fixture_plumbing_ok
        ),
        "errors": errors,
    }


def _formalizer_pseudo_formal_packet_eval_manifest_path(out_dir: Path) -> Path:
    canonical = (
        out_dir.parent
        / "formalizer_pseudo_formal_packet_eval"
        / "formalizer_pseudo_formal_packet_eval_manifest.json"
    )
    if canonical.exists():
        return canonical
    candidates = sorted(
        out_dir.parent.glob(
            "formalizer_pseudo_formal_packet_eval*/"
            "formalizer_pseudo_formal_packet_eval_manifest.json"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else canonical


def _pseudo_formal_block_verifier_component_gate_overlay(
    out_dir: Path,
) -> dict[str, object]:
    manifest_path = _pseudo_formal_block_verifier_component_gate_manifest_path(
        out_dir
    )
    empty = {
        "available": False,
        "manifest_path": "",
        "provider_name": "",
        "backend_provider_name": "",
        "component_backend_provider_names": [],
        "model": "",
        "live_generator": False,
        "capability_evidence_ok": False,
        "artifact_kind_ok": False,
        "proof_evidence_status_ok": False,
        "n_prompt_packets": 0,
        "n_ok_prompt_packets": 0,
        "n_llm_response_rows": 0,
        "n_ok_responses": 0,
        "n_valid_responses": 0,
        "n_runtime_learning_rows": 0,
        "n_accepted_blocks": 0,
        "n_failed_blocks": 0,
        "fixture_plumbing_ok": False,
        "static_or_fixture_only": False,
        "proof_evidence_status": "",
        "all_ok": False,
        "errors": ["pseudo_formal_block_verifier_component_gate_manifest_missing"],
    }
    if not manifest_path.exists():
        return empty
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            **empty,
            "manifest_path": str(manifest_path),
            "errors": ["pseudo_formal_block_verifier_component_gate_manifest_unreadable"],
        }
    provider_name = normalize_generator_provider_name(payload.get("provider_name", ""))
    backend_provider_name = normalize_generator_provider_name(
        payload.get("backend_provider_name", provider_name)
    )
    raw_component_backend_provider_names = payload.get(
        "component_backend_provider_names",
        [],
    )
    if isinstance(raw_component_backend_provider_names, str):
        raw_component_backend_provider_names = [
            raw_component_backend_provider_names
        ]
    elif not isinstance(raw_component_backend_provider_names, (list, tuple)):
        raw_component_backend_provider_names = []
    component_backend_provider_names = [
        normalize_generator_provider_name(name)
        for name in raw_component_backend_provider_names
        if normalize_generator_provider_name(name)
    ]
    if not component_backend_provider_names and backend_provider_name:
        component_backend_provider_names = [backend_provider_name]
    backend_live = bool(component_backend_provider_names) and all(
        is_live_generator_backend(provider_name, backend_provider_name)
        for backend_provider_name in component_backend_provider_names
    )
    live_generator = bool(payload.get("live_generator", False) and backend_live)
    artifact_kind_ok = (
        str(payload.get("artifact_kind", ""))
        == "PseudoFormalBlockVerifierComponentGateManifest"
    )
    proof_evidence_status = str(payload.get("proof_evidence_status", ""))
    proof_evidence_status_ok = (
        proof_evidence_status
        == "PSEUDO_FORMAL_BLOCK_VERIFIER_COMPONENT_GATE_NOT_PROOF_EVIDENCE"
    )
    n_prompt_packets = int(payload.get("n_prompt_packets", 0) or 0)
    n_ok_prompt_packets = int(payload.get("n_ok_prompt_packets", 0) or 0)
    n_llm_response_rows = int(payload.get("n_llm_response_rows", 0) or 0)
    n_ok_responses = int(payload.get("n_ok_responses", 0) or 0)
    n_valid_responses = int(payload.get("n_valid_responses", 0) or 0)
    n_runtime_learning_rows = int(
        payload.get("n_runtime_learning_rows", 0) or 0
    )
    n_accepted_blocks = int(payload.get("n_accepted_blocks", 0) or 0)
    n_failed_blocks = int(payload.get("n_failed_blocks", 0) or 0)
    static_or_fixture_only = bool(
        payload.get("static_or_fixture_only", False) or not live_generator
    )
    fixture_plumbing_ok = bool(
        payload.get("fixture_plumbing_ok", False)
        and artifact_kind_ok
        and proof_evidence_status_ok
        and n_prompt_packets > 0
        and n_ok_prompt_packets > 0
        and n_llm_response_rows > 0
        and n_valid_responses > 0
        and n_runtime_learning_rows > 0
    )
    capability_evidence_ok = bool(
        live_generator
        and fixture_plumbing_ok
        and payload.get("capability_evidence_ok", False)
    )
    errors = [
        error
        for error in (
            "" if artifact_kind_ok else "artifact_kind_mismatch",
            ""
            if proof_evidence_status_ok
            else "proof_evidence_status_must_remain_non_proof",
            "" if live_generator else "live_generator_missing_or_static_backend",
            "" if fixture_plumbing_ok else "component_gate_chain_incomplete",
        )
        if error
    ]
    return {
        "available": True,
        "manifest_path": str(manifest_path),
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "component_backend_provider_names": component_backend_provider_names,
        "model": str(payload.get("model", "")),
        "live_generator": live_generator,
        "capability_evidence_ok": capability_evidence_ok,
        "artifact_kind_ok": artifact_kind_ok,
        "proof_evidence_status_ok": proof_evidence_status_ok,
        "n_prompt_packets": n_prompt_packets,
        "n_ok_prompt_packets": n_ok_prompt_packets,
        "n_llm_response_rows": n_llm_response_rows,
        "n_ok_responses": n_ok_responses,
        "n_valid_responses": n_valid_responses,
        "n_runtime_learning_rows": n_runtime_learning_rows,
        "n_accepted_blocks": n_accepted_blocks,
        "n_failed_blocks": n_failed_blocks,
        "fixture_plumbing_ok": fixture_plumbing_ok,
        "static_or_fixture_only": static_or_fixture_only,
        "proof_evidence_status": proof_evidence_status,
        "all_ok": bool(
            artifact_kind_ok and proof_evidence_status_ok and fixture_plumbing_ok
        ),
        "errors": errors,
    }


def _pseudo_formal_block_verifier_component_gate_manifest_path(
    out_dir: Path,
) -> Path:
    canonical = (
        out_dir.parent
        / "pseudo_formal_block_verifier_component_gate"
        / "pseudo_formal_block_verifier_component_gate_manifest.json"
    )
    if canonical.exists():
        return canonical
    candidates = sorted(
        out_dir.parent.glob(
            "pseudo_formal_block_verifier_component_gate*/"
            "pseudo_formal_block_verifier_component_gate_manifest.json"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else canonical


def _architect_research_path_policy_eval_overlay(out_dir: Path) -> dict[str, object]:
    manifest_path = _architect_research_path_policy_eval_manifest_path(out_dir)
    empty = {
        "available": False,
        "manifest_path": "",
        "provider_name": "",
        "backend_provider_name": "",
        "model": "",
        "live_generator": False,
        "capability_evidence_ok": False,
        "n_cases": 0,
        "n_cases_ok": 0,
        "n_with_problem_analysis": 0,
        "n_with_stat_knowledge_bank_plan": 0,
        "n_with_literature_fair_comparison_plan": 0,
        "fixture_plumbing_ok": False,
        "static_or_fixture_only": False,
        "proof_evidence_status": "",
    }
    if not manifest_path.exists():
        return empty
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    provider_name = normalize_generator_provider_name(payload.get("provider_name", ""))
    backend_provider_name = normalize_generator_provider_name(
        payload.get("backend_provider_name", provider_name)
    )
    live_generator = bool(
        payload.get("live_generator", False)
        and is_live_generator_backend(provider_name, backend_provider_name)
    )
    n_cases = int(payload.get("n_cases", 0) or 0)
    n_cases_ok = int(payload.get("n_cases_ok", 0) or 0)
    n_with_problem_analysis = int(payload.get("n_with_problem_analysis", 0) or 0)
    n_with_knowledge_plan = int(
        payload.get("n_with_stat_knowledge_bank_plan", 0) or 0
    )
    n_with_fair_comparison = int(
        payload.get("n_with_literature_fair_comparison_plan", 0) or 0
    )
    all_cases_ok = bool(
        n_cases > 0
        and n_cases_ok == n_cases
        and n_with_problem_analysis == n_cases
        and n_with_knowledge_plan == n_cases
        and n_with_fair_comparison == n_cases
        and payload.get("all_cases_ok", False)
    )
    static_or_fixture_only = bool(
        payload.get("static_or_fixture_only", False) or not live_generator
    )
    return {
        "available": True,
        "manifest_path": str(manifest_path),
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "model": str(payload.get("model", "")),
        "live_generator": live_generator,
        "capability_evidence_ok": bool(
            live_generator and all_cases_ok and payload.get("capability_evidence_ok", False)
        ),
        "n_cases": n_cases,
        "n_cases_ok": n_cases_ok,
        "n_with_problem_analysis": n_with_problem_analysis,
        "n_with_stat_knowledge_bank_plan": n_with_knowledge_plan,
        "n_with_literature_fair_comparison_plan": n_with_fair_comparison,
        "fixture_plumbing_ok": bool(static_or_fixture_only and all_cases_ok),
        "static_or_fixture_only": static_or_fixture_only,
        "proof_evidence_status": str(payload.get("proof_evidence_status", "")),
    }


def _architect_research_path_policy_eval_manifest_path(out_dir: Path) -> Path:
    canonical = (
        out_dir.parent
        / "architect_research_path_policy_eval"
        / "architect_research_path_policy_eval_manifest.json"
    )
    if canonical.exists():
        return canonical
    candidates = sorted(
        out_dir.parent.glob(
            "architect_research_path_policy_eval*/"
            "architect_research_path_policy_eval_manifest.json"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else canonical


def _research_agent_runtime_audit_overlay(
    out_dir: Path,
    *,
    configured_runtime_dir: str | None,
    enable_offline_smoke: bool = True,
    enable_contract_smoke: bool = True,
    question_file: Path = Path("examples/research_questions.json"),
) -> dict[str, object]:
    audit_out = out_dir / "research_agent_runtime_audit"
    runtime_dir = Path(configured_runtime_dir) if configured_runtime_dir else None
    if runtime_dir is not None:
        payload = audit_research_agent_runtime(runtime_dir, audit_out)
        payload["requested"] = True
        payload["available"] = bool((runtime_dir / "research_agent_runtime_manifest.json").exists())
        payload["runtime_dir"] = str(runtime_dir)
        payload["runtime_audit_source"] = "configured_runtime_dir"
        payload["offline_runtime_smoke"] = False
        payload["contract_smoke"] = False
        payload["manifest_path"] = str(audit_out / "research_agent_runtime_audit_manifest.json")
        payload["report_path"] = str(audit_out / "research_agent_runtime_audit.md")
        (audit_out / "research_agent_runtime_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        return payload

    if enable_offline_smoke:
        runtime_dir = out_dir / "research_agent_runtime_offline_smoke"
        run_research_agent_runtime_offline_smoke(
            runtime_dir,
            question_file=question_file,
        )
        payload = audit_research_agent_runtime(runtime_dir, audit_out)
        payload["requested"] = True
        payload["available"] = True
        payload["runtime_dir"] = str(runtime_dir)
        payload["runtime_audit_source"] = OFFLINE_RUNTIME_SMOKE_SOURCE
        payload["offline_runtime_smoke"] = True
        payload["contract_smoke"] = False
        payload["manifest_path"] = str(
            audit_out / "research_agent_runtime_audit_manifest.json"
        )
        payload["report_path"] = str(audit_out / "research_agent_runtime_audit.md")
        payload["readiness_boundary"] = (
            str(payload.get("readiness_boundary", "") or "")
            + " "
            + OFFLINE_RUNTIME_SMOKE_BOUNDARY
        ).strip()
        limitations = list(payload.get("limitations", []) or [])
        limitations.append(
            "system-generated offline AgentRuntime smoke is static-backend runtime evidence, not live autonomous runtime evidence"
        )
        payload["limitations"] = limitations
        (audit_out / "research_agent_runtime_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        return payload

    if enable_contract_smoke:
        runtime_dir = _write_research_agent_runtime_contract_smoke(
            out_dir / "research_agent_runtime_contract_smoke"
        )
        payload = audit_research_agent_runtime(runtime_dir, audit_out)
        payload["requested"] = True
        payload["available"] = True
        payload["runtime_dir"] = str(runtime_dir)
        payload["runtime_audit_source"] = "system_generated_contract_smoke"
        payload["offline_runtime_smoke"] = False
        payload["contract_smoke"] = True
        payload["manifest_path"] = str(audit_out / "research_agent_runtime_audit_manifest.json")
        payload["report_path"] = str(audit_out / "research_agent_runtime_audit.md")
        payload["readiness_boundary"] = (
            str(payload.get("readiness_boundary", "") or "")
            + " This system-generated contract smoke proves only that the "
            "ResearchAgentRuntime audit contract, continuation accounting, "
            "learning-row plumbing, and non-proof boundary are exercised by the "
            "system audit. It is not a live autonomous AI Statistician run."
        ).strip()
        limitations = list(payload.get("limitations", []) or [])
        limitations.append(
            "system-generated AgentRuntime contract smoke is not live autonomous runtime evidence"
        )
        payload["limitations"] = limitations
        (audit_out / "research_agent_runtime_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        return payload

    audit_out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requested": False,
        "available": False,
        "all_ok": False,
        "capability_ready_for_full_ai_statistician": False,
        "capability_status": "NOT_REQUESTED",
        "capability_gaps": [
            "research-agent-runtime audit was not requested",
        ],
        "errors": [],
        "runtime_dir": "",
        "runtime_audit_source": "not_requested",
        "offline_runtime_smoke": False,
        "contract_smoke": False,
        "manifest_path": str(audit_out / "research_agent_runtime_audit_manifest.json"),
        "report_path": str(audit_out / "research_agent_runtime_audit.md"),
        "n_results": 0,
        "n_ok": 0,
        "n_budget_exhausted_with_pending_next_task": 0,
        "n_budgeted_continuation_contract_ok": 0,
        "runtime_resumed_from_pending_task": False,
        "runtime_resume_policy": "",
        "runtime_resume_context": {},
        "n_runtime_traces": 0,
        "n_runtime_next_action_items": 0,
        "n_runtime_learning_rows": 0,
        "n_runtime_pending_task_memory_rows": 0,
        "n_runtime_route_critical_target_identity_rows": 0,
        "n_runtime_route_critical_rows_missing_target_ids": 0,
        "runtime_route_critical_target_identity_channels": [],
        "runtime_route_critical_rows_missing_target_ids": [],
        "n_runtime_handoff_artifact_missing_feedback_rows": 0,
        "runtime_handoff_artifact_missing_ids": [],
        "runtime_handoff_artifact_missing_owner_subsystems": [],
        "has_real_kernel_evidence": False,
        "n_results_with_real_kernel_evidence": 0,
        "n_kernel_verified_subclaims": 0,
        "n_real_kernel_verified_subclaims": 0,
        "n_non_real_kernel_verified_subclaims": 0,
        "kernel_verified_verifiers": [],
        "n_formal_gaps": 0,
        "n_registered_proof_bank_obligation_candidates": 0,
        "n_memory_prioritized_proof_obligations": 0,
        "n_memory_off_catalog_proof_obligations": 0,
        "n_memory_rejected_proof_obligations": 0,
        "n_llm_requested_proof_obligations": 0,
        "n_llm_off_catalog_proof_obligations": 0,
        "n_llm_rejected_proof_obligations": 0,
        "n_full_frontier_theorem_proved": 0,
        "architect_coordinator_enabled": False,
        "llm_topology_policy_ok": False,
        "unsupported_generator_backends_enabled": 0,
        "n_live_generator_agents_enabled": 0,
        "n_architect_initial_routing_deferred_meta_capability_gaps": 0,
        "architect_initial_routing_deferred_meta_capability_gap_owners": {},
        "architect_initial_routing_deferred_meta_capability_gap_requirement_ids": [],
        "n_critic_reroutes": 0,
        "n_lean_lsp_mcp_live_calls": 0,
        "n_source_theorem_exact_semantic_definition_authoring_tasks": 0,
        "source_theorem_exact_semantic_definition_authoring_worker_required": False,
        "source_theorem_exact_semantic_definition_authoring_worker_provider_name": "",
        "source_theorem_exact_semantic_definition_authoring_worker_backend_provider_name": "",
        "source_theorem_exact_semantic_definition_authoring_worker_n_llm_attempted": 0,
        "source_theorem_exact_semantic_definition_authoring_worker_n_live_llm_attempted": 0,
        "source_theorem_exact_semantic_definition_authoring_retry_tasks_required": False,
        "source_theorem_exact_semantic_definition_authoring_repair_tasks_required": False,
        "source_theorem_exact_semantic_definition_authoring_retry_n_tasks": 0,
        "source_theorem_exact_semantic_definition_structural_reformulation_tasks_required": False,
        "source_theorem_exact_semantic_definition_structural_reformulation_n_tasks": 0,
        "source_theorem_exact_semantic_definition_authoring_retry_worker_provider_name": "",
        "source_theorem_exact_semantic_definition_authoring_retry_worker_backend_provider_name": "",
        "source_theorem_exact_semantic_definition_authoring_retry_worker_n_llm_attempted": 0,
        "source_theorem_exact_semantic_definition_authoring_retry_worker_n_live_llm_attempted": 0,
        "source_theorem_exact_semantic_definition_late_authoring_worker_ran": False,
        "source_theorem_exact_semantic_definition_late_authoring_worker_n_manifests": 0,
        "source_theorem_exact_semantic_definition_late_authoring_worker_provider_names": [],
        "source_theorem_exact_semantic_definition_late_authoring_worker_backend_provider_names": [],
        "source_theorem_exact_semantic_definition_late_authoring_worker_n_llm_attempted": 0,
        "source_theorem_exact_semantic_definition_late_authoring_worker_n_live_llm_attempted": 0,
        "n_algorithm_sandbox_executed": 0,
        "n_generated_code_sandbox_executed": 0,
        "n_generated_code_sandbox_failed_then_passed_repair_sequences": 0,
        "n_generated_code_sandbox_metric_gate_failed": 0,
        "n_unsafe_generated_code_rejected": 0,
        "n_generated_simulation_sandbox_executed": 0,
        "n_generated_simulation_sandbox_failed_then_passed_repair_sequences": 0,
        "n_generated_simulation_sandbox_metric_gate_failed": 0,
        "n_unsafe_generated_simulation_code_rejected": 0,
        "n_formalizer_lean_candidate_local_lean_checked": 0,
        "n_formalizer_lean_candidate_local_lean_compiled": 0,
        "n_results_with_runtime_learning_memory_input": 0,
        "n_runtime_learning_memory_input_rows": 0,
        "n_results_with_runtime_capability_gap_routing_input": 0,
        "n_runtime_capability_gap_routing_input_rows": 0,
        "n_runtime_capability_gap_routing_input_rows_seen": 0,
        "runtime_capability_gap_routing_input_retention_policy": "",
        "runtime_capability_gap_routing_input_retention_selection_counts": {},
        "runtime_capability_gap_routing_input_requirement_ids": [],
        "runtime_capability_gap_routing_input_priority_pinned_requirement_ids": [],
        "runtime_capability_gap_routing_input_owner_subsystems": {},
        "runtime_capability_gap_routing_followup_commands": [],
        "n_runtime_capability_gap_routing_input_rows_missing_retention_selection": 0,
        "n_runtime_capability_gap_routing_input_rows_missing_retention_selection_boundary": 0,
        "n_runtime_cross_task_theorem_family_rows": 0,
        "n_runtime_cross_task_theorem_family_rows_with_explicit_family": 0,
        "n_runtime_cross_task_theorem_family_rows_with_target_bound_kernel": 0,
        "n_runtime_cross_task_theorem_family_rows_with_open_formal_gaps": 0,
        "runtime_pseudo_formal_block_routing_contract_complete": False,
        "n_runtime_pseudo_formal_block_routing_rows": 0,
        "n_runtime_pseudo_formal_block_routing_effective_rows": 0,
        "n_runtime_pseudo_formal_block_routing_diagnostic_rows": 0,
        "n_runtime_pseudo_formalization_required_formalization_manifests": 0,
        "n_runtime_pseudo_formalization_required_missing_routing_rows": 0,
        "runtime_pseudo_formalization_required_manifest_ids": [],
        "runtime_pseudo_formalization_required_missing_routing_manifest_ids": [],
        "runtime_pseudo_formalization_routed_manifest_ids": [],
        "runtime_pseudo_formalization_effective_routed_manifest_ids": [],
        "n_runtime_pseudo_formalization_routed_manifests": 0,
        "n_runtime_pseudo_formalization_effective_routed_manifests": 0,
        "runtime_pseudo_formal_block_routing_row_kinds": {},
        "runtime_pseudo_formal_block_routing_diagnostic_row_kinds": {},
        "runtime_pseudo_formal_block_routing_effective_target_lanes": {},
        "runtime_pseudo_formal_block_routing_diagnostic_target_lanes": {},
        "n_runtime_pseudo_formal_block_routing_rows_missing_method_lineage": 0,
        "n_runtime_pseudo_formal_block_routing_rows_missing_scope_parent": 0,
        "n_runtime_pseudo_formal_block_routing_rows_invalid_scope_parent": 0,
        "n_runtime_pseudo_formal_block_routing_rows_missing_inherited_scope": 0,
        "n_runtime_pseudo_formal_block_routing_rows_missing_row_kind": 0,
        "n_runtime_pseudo_formal_block_routing_rows_missing_or_wrong_nonproof_boundary": 0,
        "runtime_pseudo_formal_block_routing_contract_issues": [],
        "n_runtime_source_theorem_semantic_primitive_work_orders_from_pseudo_formal": 0,
        "n_runtime_source_theorem_exact_semantic_definition_work_orders_from_pseudo_formal": 0,
        "source_semantic_proofengineer_bridge_requested": False,
        "source_semantic_proofengineer_bridge_ran": False,
        "source_semantic_proofengineer_bridge_proof_evidence_status": "",
        "n_runtime_formal_gap_planner_handoff_rows": 0,
        "n_runtime_formal_gap_planner_handoff_rows_missing_execution_context": 0,
        "n_runtime_formalization_gap_planner_live_route_planner_invocations": 0,
        "n_runtime_formalization_gap_planner_live_route_planner_response_contract_ok": 0,
        "n_runtime_formalization_gap_planner_live_route_planner_target_prover_replay_all_ok": 0,
        "n_runtime_formalization_gap_planner_live_route_planner_target_prover_replay_route_revision_proposals": 0,
        "n_runtime_target_prover_replay_route_revision_complete_feedback_proposal_ids": 0,
        "n_results_with_problem_analysis": 0,
        "n_results_with_stat_knowledge_bank_plan": 0,
        "n_results_with_literature_fair_comparison_plan": 0,
        "limitations": [
            "research-agent-runtime audit was not requested for this system audit run",
            "pass --research-agent-runtime-dir to include AgentRuntime alignment in the gate",
        ],
    }
    (audit_out / "research_agent_runtime_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (audit_out / "research_agent_runtime_audit.md").write_text(
        "\n".join(
            [
                "# Research Agent Runtime Audit",
                "",
                "- requested: False",
                "- available: False",
                "- pass `--research-agent-runtime-dir <dir>` to include AgentRuntime alignment in the gate",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return payload


def _write_research_agent_runtime_contract_smoke(runtime_dir: Path) -> Path:
    """Write a deterministic AgentRuntime audit-contract smoke fixture.

    The fixture intentionally stops at a pending formal continuation. It gives the
    system audit concrete runtime artifacts to audit without implying live LLM,
    generated-code, simulation-repair, Lean-kernel, or full theorem readiness.
    """

    if runtime_dir.exists():
        shutil.rmtree(runtime_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    trace_path = runtime_dir / "runtime_traces.jsonl"
    agenda_path = runtime_dir / "runtime_next_action_agenda.jsonl"
    learning_path = runtime_dir / "runtime_learning_rows.jsonl"
    result_path = runtime_dir / "contract_smoke_runtime_result.json"
    pending_task = {
        "task_id": "formalize:contract-smoke:repair",
        "owner_subsystem": "FormalizationEvaluator",
        "objective": (
            "Continue the remaining formal gap after the system-audit runtime "
            "contract smoke budget is exhausted."
        ),
        "inputs": {
            "question": {
                "id": "contract_smoke",
                "title": "AgentRuntime contract smoke",
            },
            "proof_evidence_status": "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE",
        },
    }
    trace = {
        "schema_version": 1,
        "subsystem": "CriticEvaluator",
        "task_id": "critic:contract-smoke:review",
        "task": {
            "task_id": "critic:contract-smoke:review",
            "owner_subsystem": "CriticEvaluator",
            "inputs": {
                "question": {
                    "id": "contract_smoke",
                    "title": "AgentRuntime contract smoke",
                }
            },
        },
        "status": "REVISE",
        "failure_classification": "formal_gap_remaining",
        "next_task_id": pending_task["task_id"],
        "next_task": pending_task,
        "proof_evidence_status": "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE",
        "boundary": (
            "Contract-smoke trace exercises budgeted continuation and learning "
            "plumbing only; it is not theorem proof evidence."
        ),
    }
    agenda = {
        "schema_version": 1,
        "artifact_kind": "RuntimeNextActionAgendaRow",
        "id": "formal_gap:contract-smoke:repair",
        "owner_subsystem": "FormalizationEvaluator",
        "trigger": "RUNTIME_CONTRACT_SMOKE_FORMAL_GAP",
        "action": "repair remaining formal gap from contract-smoke runtime audit",
        "acceptance_gate": "future runtime must provide target-prover replay evidence",
        "target_ids": ["contract_smoke:formal_gap"],
        "proof_evidence_status": "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE",
        "boundary": (
            "Agenda row is generated by deterministic system-audit contract smoke "
            "and cannot promote a theorem."
        ),
    }
    learning = {
        "schema_version": 1,
        "artifact_kind": "RuntimeLearningRow",
        "learning_task": "formal_gap_feedback",
        "question_id": "contract_smoke",
        "target_ids": ["contract_smoke:formal_gap"],
        "next_owner_subsystem": "FormalizationEvaluator",
        "input_summary": {
            "source": "system_generated_contract_smoke",
            "formal_gap": True,
            "proof_evidence_status": "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE",
        },
        "target_behavior": "resume formalization with exact target-prover replay",
        "proof_evidence_status": "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE",
        "boundary": (
            "Learning row is runtime memory only and is not theorem proof evidence."
        ),
    }
    trace_path.write_text(json.dumps(trace, sort_keys=True) + "\n", encoding="utf-8")
    agenda_path.write_text(json.dumps(agenda, sort_keys=True) + "\n", encoding="utf-8")
    learning_path.write_text(
        json.dumps(learning, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = {
        "schema_version": 1,
        "status": "MAX_ITERATIONS_REACHED",
        "blackboard": {
            "project_id": "project:contract_smoke",
            "artifacts": {
                "retrieval_memory_manifest:contract_smoke": {
                    "artifact_kind": "RetrievalMemoryManifest",
                    "question_id": "contract_smoke",
                },
                "theory_derivation:contract_smoke": {
                    "artifact_kind": "TheoryDerivationPacket",
                    "question_id": "contract_smoke",
                },
                "simulation_manifest:contract_smoke": {
                    "artifact_kind": "RuntimeSimulationManifest",
                    "n_generated_simulation_sandbox_executed": 0,
                    "n_generated_simulation_sandbox_passed": 0,
                    "n_generated_simulation_sandbox_metric_gate_failed": 0,
                    "n_unsafe_generated_simulation_code_rejected": 0,
                    "proof_evidence_status": (
                        "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE"
                    ),
                },
                "algorithm_sandbox_manifest:contract_smoke": {
                    "artifact_kind": "RuntimeAlgorithmSandboxManifest",
                    "n_executed": 0,
                    "n_generated_code_executed": 0,
                    "n_metric_gate_failed": 0,
                    "n_unsafe_generated_code_rejected": 0,
                    "proof_evidence_status": (
                        "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE"
                    ),
                },
                "formalization_manifest:contract_smoke": {
                    "artifact_kind": "RuntimeFormalizationManifest",
                    "counts": {"kernel_verified": 0, "formal_gap": 1},
                    "formal_subclaims": [],
                    "proof_evidence_status": (
                        "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE"
                    ),
                },
                "critic_evaluator_manifest:contract_smoke": {
                    "artifact_kind": "RuntimeCriticEvaluatorManifest",
                    "next_action_agenda": [agenda],
                    "learning_rows": [learning],
                    "runtime_reroute_decision": {
                        "reroute_to_theory_developer": False,
                    },
                    "proof_evidence_status": (
                        "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE"
                    ),
                },
            },
        },
        "traces": [trace],
    }
    result_path.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "runtime_stage": (
            "retrieval_theory_simulation_algorithm_formalization_critic_environment_loop"
        ),
        "runtime_evaluation_mode": "system_contract_smoke",
        "runtime_audit_source": "system_generated_contract_smoke",
        "contract_smoke": True,
        "runtime_resume_context": {
            "schema_version": 1,
            "artifact_kind": "RuntimeResumeContext",
            "n_initial_task_overrides": 1,
            "n_rehydrated_blackboard_artifacts": 6,
            "resumed_from_pending_task": True,
            "boundary": (
                "Contract smoke preserves continuation accounting only; it is "
                "not proof evidence."
            ),
        },
        "n_questions": 1,
        "n_runtime_next_action_items": 1,
        "n_runtime_learning_rows": 1,
        "llm_runtime_topology": {
            "policy_status": "OK",
            "counts": {
                "unsupported_generator_backends_enabled": 0,
                "subsystem_model_tier_policy_mismatches": 0,
                "enabled_by_provider": {},
            },
            "policy": {
                "resolved_claude_models_by_tier": {
                    "haiku": "claude-haiku-contract-smoke",
                    "sonnet": "claude-sonnet-contract-smoke",
                    "opus": "claude-opus-contract-smoke",
                }
            },
        },
        "artifacts": {
            "per_question_results": [str(result_path)],
            "runtime_traces_jsonl": str(trace_path),
            "runtime_next_action_agenda_jsonl": str(agenda_path),
            "runtime_learning_rows_jsonl": str(learning_path),
        },
        "proof_evidence_status": "RUNTIME_CONTRACT_SMOKE_NOT_PROOF_EVIDENCE",
        "boundary": (
            "This deterministic runtime smoke exists only so the system audit "
            "exercises the AgentRuntime audit contract by default. It is not live "
            "autonomous runtime evidence and cannot satisfy theorem proof gates."
        ),
    }
    (runtime_dir / "research_agent_runtime_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True),
        encoding="utf-8",
    )
    return runtime_dir


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


def _formalization_gap_planner_evaluation_route_adoption_count_rollups(
    formalization_gap_planner_evaluation_manifest: Mapping[str, Any],
) -> dict[str, int]:
    return {
        "formalization_gap_planner_evaluation_route_adoption_blockers": int(
            formalization_gap_planner_evaluation_manifest.get(
                "n_llm_route_adoption_blockers",
                0,
            )
            or 0
        ),
        "formalization_gap_planner_evaluation_route_adoption_pending_quality_control_blockers": int(
            formalization_gap_planner_evaluation_manifest.get(
                "n_llm_route_adoption_pending_quality_control_blockers",
                0,
            )
            or 0
        ),
        "formalization_gap_planner_evaluation_route_adoption_pending_source_grounding_blockers": int(
            formalization_gap_planner_evaluation_manifest.get(
                "n_llm_route_adoption_pending_source_grounding_blockers",
                0,
            )
            or 0
        ),
    }


def _select_kernel_smoke_ids_from_actions(
    proof_bank_action_manifest: dict[str, object],
    *,
    limit: int,
    exclude: list[str] | tuple[str, ...] = (),
) -> list[str]:
    """Pick registered proof-bank obligations worth local-kernel smoke checking.

    Exact proof-bank reuse rows are selected first because they can immediately
    upgrade claim-ledger rows from mock/static support to kernel-backed support.
    Broader bridge-chain rows are useful next, but they remain premise-selection
    evidence until a non-placeholder composition proof is accepted by Lean.
    """

    if limit <= 0:
        return []
    valid_obligation_ids = {obligation.id for obligation in all_obligations()}
    selected: list[str] = []
    seen = set(str(item) for item in exclude)
    action_rank = {
        "reuse_exact_proof_bank_obligation": 0,
        "compose_existing_bridge_chain": 1,
        "add_minimal_wrapper": 2,
        "design_bridge_lemma": 3,
        "design_from_first_principles": 4,
    }

    def row_sort_key(row: dict[str, object]) -> tuple[int, int, int, str]:
        action_class = str(row.get("action_class", ""))
        return (
            action_rank.get(action_class, 99),
            int(row.get("priority_rank", 99) or 99),
            -int(row.get("priority_score", 0) or 0),
            str(row.get("primitive", "")),
        )

    rows = [
        row
        for row in proof_bank_action_manifest.get("actions", [])
        if isinstance(row, dict) and bool(row.get("ok", False))
    ]
    for row in sorted(rows, key=row_sort_key):
        candidates: list[str] = []
        primitive = str(row.get("primitive", ""))
        if primitive:
            candidates.append(primitive)
        candidates.extend(
            str(item)
            for item in row.get("bridge_candidate_obligations", []) or []
            if str(item)
        )
        candidates.extend(
            str(item) for item in row.get("expected_premises", []) or [] if str(item)
        )
        for obligation_id in candidates:
            if obligation_id in seen or obligation_id not in valid_obligation_ids:
                continue
            selected.append(obligation_id)
            seen.add(obligation_id)
            if len(selected) >= limit:
                return selected
    return selected


def _write_disabled_agentic_artifact_verifier_manifest(
    out_dir: Path,
    *,
    materializer_manifest: dict[str, object],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "enabled": False,
        "disable_reason": "verify_agentic_artifacts is false for this audit",
        "n_materializer_rows": int(materializer_manifest.get("n_materializer_rows", 0) or 0),
        "n_verifier_rows": 0,
        "n_local_lean_checked": 0,
        "n_local_lean_compiled": 0,
        "n_artifact_kernel_verified": 0,
        "n_source_theorem_kernel_verified": 0,
        "n_forbidden_token_failures": 0,
        "n_execution_transcript_paths": 0,
        "n_execution_transcript_events_written": 0,
        "n_live_proof_state_requests": 0,
        "n_live_proof_state_request_valid": 0,
        "n_lean_lsp_mcp_ready_requests": 0,
        "n_live_proof_state_request_failures": 0,
        "n_ok": 0,
        "all_artifacts_kernel_verified": False,
        "all_ok": True,
        "errors": [],
        "by_verification_status": {},
        "rows": [],
        "artifact_verifier_fingerprint": stable_hash(
            [
                "disabled_agentic_artifact_verifier",
                materializer_manifest.get("materializer_fingerprint", ""),
            ]
        ),
        "proof_evidence_status": "AGENTIC_ARTIFACT_VERIFIER_DISABLED_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": (
            "Agentic artifact verification was not requested. This disabled "
            "manifest records zero artifact kernel checks and zero source theorem "
            "kernel checks; it is not theorem proof evidence."
        ),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (
        out_dir
        / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
    ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (
        out_dir / "formal_verifier_agentic_proof_execution_artifact_verifier.jsonl"
    ).write_text("", encoding="utf-8")
    (
        out_dir / "formal_verifier_agentic_proof_execution_artifact_verifier.md"
    ).write_text(
        "# Formal Verifier Agentic Proof Execution Artifact Verifier\n\n"
        "Disabled for this audit. No artifact-level Lean checks were run, and no "
        "source theorem proof evidence is claimed.\n",
        encoding="utf-8",
    )
    return payload


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
            "adaptive_mc_rerun": config.adaptive_mc_rerun,
            "adaptive_mc_multiplier": config.adaptive_mc_multiplier,
        },
        "verifier": verifier.name,
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "research_provenance": _stable_research_provenance_for_cache(),
        "formal_source_search": _normalized_formal_source_search(formal_source_search),
        "engine_fingerprints": {
            "research_system_audit": _source_file_hash(Path(__file__)),
            "claim_ledger": _source_file_hash(Path(__file__).with_name("claim_ledger.py")),
            "claim_ledger_action_export": _source_file_hash(
                Path(__file__).with_name("claim_ledger_action_export.py")
            ),
            "stat_claim_certificate_checker_audit": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_checker_audit.py")
            ),
            "stat_claim_certificate_plan": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_plan.py")
            ),
            "stat_claim_certificate_readiness_overlay": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_readiness_overlay.py")
            ),
            "stat_claim_certificate_witness_queue": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_witness_queue.py")
            ),
            "stat_claim_certificate_witness_materializer": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_witness_materializer.py")
            ),
            "stat_claim_certificate_witness_prompt_packets": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_witness_prompt_packets.py")
            ),
            "stat_claim_certificate_witness_context_packets": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_witness_context_packets.py")
            ),
            "stat_claim_certificate_witness_context_triage": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_witness_context_triage.py")
            ),
            "stat_claim_certificate_witness_response_apply": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_witness_response_apply.py")
            ),
            "stat_claim_certificate_witness_response_validation": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_witness_response_validation.py")
            ),
            "stat_claim_certificate_witness_validator": _source_file_hash(
                Path(__file__).with_name("stat_claim_certificate_witness_validator.py")
            ),
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

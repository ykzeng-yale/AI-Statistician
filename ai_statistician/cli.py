from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Mapping

from .algorithms import audit_algorithm_registry
from .algorithm_repair_promotion import export_algorithm_repair_promotion_queue
from .algorithm_repair_patch_training_export import export_algorithm_repair_patch_training_dataset
from .algorithm_repair_patch_policy_model import train_algorithm_repair_patch_policy_model
from .algorithm_repair_production_patch_plan import export_algorithm_repair_production_patch_plan
from .algorithm_repair_reviewed_patch_apply import apply_reviewed_algorithm_repair_source_patches
from .algorithm_repair_reviewed_patch_validate import validate_reviewed_algorithm_repair_patches
from .algorithm_repair_sandbox import evaluate_algorithm_repair_sandbox
from .algorithm_repair_sandbox_apply import apply_algorithm_repair_sandbox_results
from .algorithm_repair_sandbox_patch_eval import evaluate_algorithm_repair_sandbox_patches
from .algorithm_repair_sandbox_rerun import rerun_algorithm_repair_sandbox_applications
from .architecture_audit import audit_architecture
from .assumption_interface_export import export_assumption_interfaces
from .autoform_harness import audit_autoform_harness
from .capability_audit import build_capability_audit, write_capability_audit
from .claim_ledger_action_export import export_claim_ledger_actions
from .claim_ledger import build_claim_ledger
from .stat_claim_certificate_checker_audit import audit_stat_claim_certificate_checkers
from .stat_claim_certificate_plan import export_stat_claim_certificate_plan
from .stat_claim_certificate_readiness_overlay import (
    export_stat_claim_certificate_readiness_overlay,
)
from .stat_claim_certificate_witness_queue import (
    export_stat_claim_certificate_witness_queue,
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
from .doctor import build_doctor_report, write_doctor_manifest
from .evaluation import EvalConfig, run_seed_eval
from .autoform_target_export import export_autoform_targets
from .frontier_backlog_audit import audit_frontier_backlog
from .frontier_coverage_audit import audit_frontier_coverage
from .frontier_discover_and_prove_prompt_packets import (
    export_frontier_discover_and_prove_prompt_packets,
)
from .frontier_evaluation_triage import audit_frontier_evaluation_triage
from .frontier_precision_audit import audit_frontier_precision
from .frontier_simulation_rerun_audit import audit_frontier_simulation_reruns
from .frontier_smoke_benchmark import FrontierSmokeConfig, run_frontier_smoke_benchmark
from .frontier_theory_revision_formalization_audit import audit_frontier_theory_revision_formalization
from .frontier_theory_revision_queue import export_frontier_theory_revision_queue
from .frontier_theory_target_audit import audit_frontier_theory_targets
from .formal_gap_task_export import export_formal_gap_lean_tasks
from .formalization_delta_plan import build_formalization_delta_plan
from .formalization_gap_planner_benchmark import export_formalization_gap_planner_benchmark
from .formalization_gap_planner_benchmark_audit import (
    audit_formalization_gap_planner_benchmark,
)
from .formalization_gap_planner_ablation_study import (
    export_formalization_gap_planner_ablation_study,
)
from .formalization_gap_planner_evaluation import evaluate_formalization_gap_planner
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
from .formalization_gap_planner_interactive_session import (
    export_formalization_gap_planner_interactive_session,
)
from .formalization_gap_planner_cross_prover_matrix_audit import (
    DEFAULT_REUSE_TARGETS as FORMALIZATION_GAP_PLANNER_REUSE_TARGETS,
    audit_formalization_gap_planner_cross_prover_matrix,
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
from .formalization_gap_planner_library_coverage_map import (
    export_formalization_gap_planner_library_coverage_map,
)
from .formalization_gap_planner_llm_route_planner import (
    export_formalization_gap_planner_llm_route_planner,
    validate_formalization_gap_planner_llm_route_planner_response_payloads,
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
from .formalization_gap_planner_minimal_delta_audit_feedback_adapter import (
    export_formalization_gap_planner_minimal_delta_audit_feedback_responses,
)
from .formalization_gap_planner_portable_plan_audit import (
    audit_formalization_gap_planner_portable_plan,
)
from .formalization_gap_planner_publication_bundle import (
    export_formalization_gap_planner_publication_bundle,
)
from .formalization_gap_planner_publication_bundle_audit import (
    audit_formalization_gap_planner_publication_bundle,
)
from .formalization_gap_planner_reuse_smoke import (
    run_formalization_gap_planner_reuse_smoke,
)
from .formalization_gap_planner_prover_adapter_contract import (
    export_formalization_gap_planner_prover_adapter_contract,
)
from .formalization_gap_planner_prover_adapter_feedback_adapter import (
    export_formalization_gap_planner_prover_adapter_feedback_responses,
)
from .formalization_gap_planner_refinement_adapters import (
    export_formalization_gap_planner_refinement_adapter_responses,
)
from .formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)
from .formalization_gap_planner_refinement_queue import (
    export_formalization_gap_planner_refinement_queue,
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
from .formalization_gap_planner_runtime_handoff_audit import (
    audit_formalization_gap_planner_runtime_handoffs,
)
from .formalization_gap_planner_proof_state_triage import (
    export_formalization_gap_planner_proof_state_triage,
)
from .formalization_gap_planner_source_grounding_audit import (
    audit_formalization_gap_planner_source_grounding,
)
from .formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)
from .formalization_gap_planner_target_intake import (
    normalize_formalization_gap_planner_target_intake,
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
from .formal_verifier_agentic_proof_trace_memory import (
    export_formal_verifier_agentic_proof_trace_memory,
)
from .formal_verifier_agentic_proof_source_theorem_promotion_queue import (
    export_formal_verifier_agentic_proof_source_theorem_promotion_queue,
)
from .formal_verifier_agentic_proof_source_theorem_target_resolution import (
    export_formal_verifier_agentic_proof_source_theorem_target_resolution,
)
from .formal_verifier_replay_repair import export_formal_verifier_replay_repair_packets
from .formal_source_graph import audit_formal_source_graph
from .formal_source_index import (
    FormalSourceRoot,
    FormalSourceSqliteIndex,
    audit_formal_source_index,
    build_formal_source_search_backend,
)
from .formal_source_hybrid import FormalSourceHybridRetriever
from .formal_source_retrieval_ablation import run_formal_source_retrieval_ablation_benchmark
from .formal_source_retrieval_benchmark import (
    ALL_FORMAL_SOURCE_RETRIEVAL_BENCHMARKS,
    DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
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
from .intake_audit import audit_question_intake
from .lean_rag_package_audit import (
    apply_lean_rag_source_registry_expansion,
    audit_lean_rag_package,
    preflight_lean_rag_source_registry_expansion,
    stage_lean_rag_source_registry_expansion,
)
from .lean_blueprint_knowledge import export_lean_blueprint_knowledge
from .lean_rag_dependency_health import audit_lean_rag_dependency_health
from .paper_theory_roundtrip import export_paper_theory_roundtrip
from .proof_audit import audit_proof_bank
from .proof_bank_action_export import export_proof_bank_actions
from .proof_bank import all_obligations, obligations_by_tags
from .proof_bank_expansion_export import export_proof_bank_expansion_candidates
from .proof_policy_baseline import evaluate_retrieval_proof_policy_baseline
from .proof_policy_model import train_proof_policy_model
from .proof_repair_export import export_proof_repair_dataset
from .proof_search_audit import audit_proof_search_controller
from .proof_search_kernel_rerun_queue import export_proof_search_kernel_rerun_queue
from .proof_search_retrieval_ablation import run_proof_search_retrieval_ablation
from .proof_search_training_export import export_proof_search_process_dataset
from .proof_search_value_model import train_proof_search_value_model
from .rag_collaboration_export import export_rag_collaboration_manifest
from .proof_training_export import export_proof_training_dataset
from .prover_component_audit import build_prover_component_audit, write_prover_component_audit
from .release import ReleaseBundleConfig, build_release_bundle
from .theorem_reduction_closure_work_order_audit import (
    audit_theorem_reduction_closure_work_orders,
)
from .theorem_reduction_closure_learning_export import (
    export_theorem_reduction_closure_learning_from_manifest,
)
from .theorem_reduction_closure_proofengineer_bridge import (
    resolve_theorem_reduction_queue_path,
    run_theorem_reduction_closure_proofengineer_bridge,
)
from .research_evaluation import ResearchEvalConfig, run_research_seed_eval
from .research_gap_audit import audit_research_gap_backlog
from .research_intake_audit import audit_research_question_intake
from .research_knowledge_audit import audit_research_knowledge
from .research_lab import audit_research_algorithm_registry, load_open_research_questions, run_research_benchmark
from .research_loop import LoopConfig, run_research_loop_benchmark
from .research_loop_live_repair_audit import audit_research_loop_live_repair_artifacts
from .research_loop_repair_audit import audit_research_loop_repair_tasks
from .research_next_iteration_audit import audit_next_iteration_queue
from .research_capability_audit import build_research_capability_audit, write_research_capability_audit
from .research_policy_baseline import evaluate_research_policy_baseline
from .research_report import build_research_markdown_report
from .research_architect import (
    AnthropicArchitectLLMProvider,
    LLMTheoryDeveloperRepairHandler,
    LLMTheoryDeveloperAgent,
    ResearchArchitectAgent,
    ResearchArchitectConfig,
    StaticArchitectLLMProvider,
)
from .architect_coordinator_llm import ArchitectCoordinatorConfig, LLMArchitectCoordinatorAgent
from .algorithm_engineer_llm import AlgorithmEngineerConfig, LLMAlgorithmEngineerAgent
from .model_backend import (
    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    SUPPORTED_LIVE_GENERATOR_PROVIDERS,
    OpenAIResponsesGeneratorBackend,
    default_generator_model,
    default_generator_provider,
)
from .proof_state_feedback import LocalLeanProofStateFeedbackProvider
from .simulation_engineer_llm import LLMSimulationEngineerAgent, SimulationEngineerConfig
from .research_agent_runtime import ResearchAgentRuntimeConfig, run_research_agent_runtime
from .research_agent_runtime_audit import audit_research_agent_runtime
from .research_system_audit import ResearchSystemAuditConfig, run_research_system_audit
from .research_trace_audit import audit_research_traces
from .research_training_export import export_research_training_dataset
from .critic_evaluator_llm import CriticEvaluatorConfig, LLMCriticEvaluatorAgent
from .formalizer_llm import FormalizerConfig, LLMFormalizerProofEngineerAgent
from .questions import QUESTIONS, load_question_file
from .retrieval import audit_proof_bank_retrieval
from .system import AIStatisticianSystem, compact_summary, write_run_manifest, write_trace
from .system_audit import SystemAuditConfig, load_audit_questions, run_system_audit
from .theorem_composition_export import export_theorem_composition_packets
from .theory_proposal import GeneratorTheoryProposer
from .trace_audit import audit_run_traces
from .verifier import AxleProofVerifier, LocalLeanProofVerifier, MockProofVerifier


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _attach_runtime_learning_memory(args: argparse.Namespace, context: dict[str, object]) -> None:
    paths = [str(item) for item in getattr(args, "learning_memory_jsonl", []) or [] if str(item).strip()]
    if not paths:
        return
    context["runtime_learning_memory"] = _load_runtime_learning_memory(
        [Path(item) for item in paths],
        max_rows=int(getattr(args, "max_learning_memory_rows", 20) or 20),
    )


def _load_runtime_learning_memory(paths: list[Path], *, max_rows: int = 20) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            continue
        for line_no, line in enumerate(lines, start=1):
            if len(rows) >= max_rows:
                break
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_no}: {exc}")
                continue
            if isinstance(payload, dict):
                rows.append(_compact_runtime_learning_memory_row(payload))
            else:
                errors.append(f"{path}:{line_no}: expected JSON object")
        if len(rows) >= max_rows:
            break
    return {
        "schema_version": 1,
        "artifact_kind": "RuntimeLearningMemoryContext",
        "source_paths": [str(path) for path in paths],
        "rows": rows,
        "counts": {
            "rows_loaded": len(rows),
            "source_paths": len(paths),
            "errors": len(errors),
            "max_rows": max_rows,
        },
        "errors": errors[:10],
        "boundary": (
            "Prior runtime learning rows are prompt memory and orchestration guidance. "
            "They are not proof evidence, simulation evidence, execution evidence, or source authority."
        ),
    }


def _compact_runtime_learning_memory_row(row: Mapping[str, object]) -> dict[str, object]:
    compact = {
        "schema_version": row.get("schema_version", 1),
        "question_id": str(row.get("question_id", "")),
        "learning_task": str(row.get("learning_task", "")),
        "input_summary": row.get("input_summary", {}) if isinstance(row.get("input_summary", {}), dict) else {},
        "target_behavior": str(row.get("target_behavior", "")),
        "acceptance_gate": str(row.get("acceptance_gate", "")),
    }
    for key in (
        "recommended_proof_obligation_ids",
        "selected_proof_obligation_ids",
        "kernel_verified_proof_obligation_ids",
        "proved_non_kernel_proof_obligation_ids",
        "failed_proof_obligation_ids",
        "formal_gap_target_ids",
        "kernel_verified_theorem_reduction_closure_work_order_ids",
        "kernel_verified_theorem_reduction_closure_target_ids",
        "kernel_verified_theorem_reduction_closure_goal_ids",
        "verified_bridge_obligation_ids",
    ):
        values = row.get(key, ())
        if isinstance(values, list):
            compact[key] = [str(item) for item in values if str(item).strip()]
    return compact


def _proof_audit_learning_export(args: argparse.Namespace) -> int:
    manifest_path = Path(args.proof_audit_manifest)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = payload.get("checks", [])
    if not isinstance(checks, list):
        raise ValueError(f"proof audit manifest checks is not a list: {manifest_path}")
    kernel_ids = [
        str(row.get("obligation_id", "")).strip()
        for row in checks
        if isinstance(row, Mapping)
        and row.get("kernel_verified") is True
        and str(row.get("obligation_id", "")).strip()
    ]
    row = {
        "schema_version": 1,
        "question_id": str(args.question_id or ""),
        "learning_task": "proof_audit_kernel_overlay",
        "input_summary": {
            "proof_audit_manifest": str(manifest_path),
            "kernel_verified_proof_obligation_ids": kernel_ids,
            "verification_strength": str(payload.get("verification_strength", "")),
            "verifier": str(payload.get("verifier", "")),
        },
        "kernel_verified_proof_obligation_ids": kernel_ids,
        "target_behavior": (
            "Treat listed proof-bank obligations as already kernel-verified subclaim evidence "
            "for proof-obligation selection memory; do not treat them as full theorem proof."
        ),
        "acceptance_gate": (
            "Only checks with kernel_verified=true from the referenced proof_audit_manifest are exported."
        ),
        "boundary": (
            "Proof-audit learning rows are runtime memory and proof-selection guidance. "
            "They preserve the referenced local Lean/AXLE proof-audit manifest as the proof evidence; "
            "they do not prove unlisted obligations or the full frontier theorem."
        ),
    }
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    learning_path.write_text(json.dumps(row, default=str) + "\n", encoding="utf-8")
    export_manifest = {
        "schema_version": 1,
        "artifact_kind": "ProofAuditRuntimeLearningExportManifest",
        "proof_audit_manifest": str(manifest_path),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_kernel_verified_proof_obligation_ids": len(kernel_ids),
        "kernel_verified_proof_obligation_ids": kernel_ids,
        "boundary": row["boundary"],
    }
    manifest_out = out_dir / "proof_audit_runtime_learning_export_manifest.json"
    manifest_out.write_text(json.dumps(export_manifest, indent=2, default=str), encoding="utf-8")
    print("\nAI Statistician Proof-Audit Runtime Learning Export")
    print("=" * 72)
    print(f"kernel_verified_ids={len(kernel_ids)}")
    print(f"runtime learning rows written to {learning_path.resolve()}")
    print(f"export manifest written to {manifest_out.resolve()}")
    return 0


def _export_theorem_reduction_closure_learning_from_manifest(
    *,
    manifest_path: Path,
    out_dir: Path,
    question_id: str = "",
) -> dict[str, object]:
    return export_theorem_reduction_closure_learning_from_manifest(
        manifest_path=manifest_path,
        out_dir=out_dir,
        question_id=question_id,
    )


def _theorem_reduction_closure_learning_export(args: argparse.Namespace) -> int:
    result = _export_theorem_reduction_closure_learning_from_manifest(
        manifest_path=Path(args.theorem_reduction_closure_audit_manifest),
        out_dir=Path(args.out),
        question_id=str(args.question_id or ""),
    )
    export_manifest = result["export_manifest"]
    learning_path = Path(result["runtime_learning_rows_jsonl"])
    manifest_out = Path(result["export_manifest_path"])
    print("\nAI Statistician Theorem-Reduction Closure Runtime Learning Export")
    print("=" * 72)
    print(
        "kernel_verified_closure_work_orders="
        f"{export_manifest['n_kernel_verified_theorem_reduction_closure_work_order_ids']}"
    )
    print(f"runtime learning rows written to {learning_path.resolve()}")
    print(f"export manifest written to {manifest_out.resolve()}")
    return 0


LIVE_GENERATOR_PROVIDER_CHOICES = SUPPORTED_LIVE_GENERATOR_PROVIDERS
SUBSYSTEM_GENERATOR_PROVIDER_CHOICES = (
    "same",
    "anthropic",
    "openai",
    "static",
    "none",
)


def _default_live_generator_provider() -> str:
    provider = default_generator_provider()
    return provider if provider in LIVE_GENERATOR_PROVIDER_CHOICES else "anthropic"


def _default_model_for_provider(
    provider_name: str,
    requested_model: str = "",
    *,
    model_tier: str = "sonnet",
) -> str:
    return default_generator_model(provider_name, requested_model, model_tier=model_tier)


def _model_for_subsystem_provider(
    *,
    provider_choice: str,
    explicit_model: str,
    args: argparse.Namespace,
    default_model: str,
    model_tier: str,
) -> str:
    if explicit_model:
        return explicit_model
    primary_provider = getattr(args, "provider", _default_live_generator_provider())
    if provider_choice == primary_provider:
        return _default_model_for_provider(primary_provider, model_tier=model_tier)
    if provider_choice == "same":
        return default_model
    return _default_model_for_provider(provider_choice, model_tier=model_tier)


def _build_theory_generator_backend(
    *,
    provider_name: str,
    static_response_file: str = "",
    llm_timeout_seconds: float | None = None,
):
    if provider_name == "static":
        if not static_response_file:
            raise ValueError("a static response file is required with provider=static")
        return (
            StaticArchitectLLMProvider(Path(static_response_file).read_text(encoding="utf-8")),
            "static",
        )
    if provider_name == "anthropic":
        return AnthropicArchitectLLMProvider(timeout_s=llm_timeout_seconds), "anthropic"
    if provider_name == "openai":
        return OpenAIResponsesGeneratorBackend(), "openai"
    raise ValueError(f"unknown theory provider: {provider_name}")


def _build_algorithm_engineer_agent_from_args(args: argparse.Namespace, *, default_model: str):
    provider_choice = getattr(args, "algorithm_engineer_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "algorithm_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "algorithm_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier="haiku",
    )
    return LLMAlgorithmEngineerAgent(
        provider=provider,
        config=AlgorithmEngineerConfig(
            model=model,
            model_tier="haiku",
            max_tokens=getattr(args, "algorithm_max_tokens", 5000),
            temperature=getattr(args, "algorithm_temperature", 0.1),
            provider_name=provider_name,
        ),
    )


def _build_simulation_engineer_agent_from_args(args: argparse.Namespace, *, default_model: str):
    provider_choice = getattr(args, "simulation_engineer_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "simulation_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "simulation_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier="haiku",
    )
    return LLMSimulationEngineerAgent(
        provider=provider,
        config=SimulationEngineerConfig(
            model=model,
            model_tier="haiku",
            max_tokens=getattr(args, "simulation_max_tokens", 5000),
            temperature=getattr(args, "simulation_temperature", 0.1),
            provider_name=provider_name,
        ),
    )


def _build_formalizer_agent_from_args(args: argparse.Namespace, *, default_model: str):
    provider_choice = getattr(args, "formalizer_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "formalizer_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "formalizer_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier="sonnet",
    )
    return LLMFormalizerProofEngineerAgent(
        provider=provider,
        config=FormalizerConfig(
            model=model,
            model_tier="sonnet",
            max_tokens=getattr(args, "formalizer_max_tokens", 6000),
            temperature=getattr(args, "formalizer_temperature", 0.1),
            provider_name=provider_name,
        ),
    )


def _build_critic_evaluator_agent_from_args(args: argparse.Namespace, *, default_model: str):
    provider_choice = getattr(args, "critic_evaluator_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "critic_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "critic_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier="haiku",
    )
    return LLMCriticEvaluatorAgent(
        provider=provider,
        config=CriticEvaluatorConfig(
            model=model,
            model_tier="haiku",
            max_tokens=getattr(args, "critic_max_tokens", 5000),
            temperature=getattr(args, "critic_temperature", 0.1),
            provider_name=provider_name,
        ),
    )


def _build_architect_coordinator_agent_from_args(args: argparse.Namespace, *, default_model: str):
    provider_choice = getattr(args, "architect_coordinator_provider", "none")
    if provider_choice == "none":
        return None
    if provider_choice == "same":
        provider_choice = getattr(args, "provider", _default_live_generator_provider())
    static_file = getattr(args, "architect_static_response_file", "")
    if provider_choice == "static" and not static_file:
        return None
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=static_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    model = _model_for_subsystem_provider(
        provider_choice=provider_choice,
        explicit_model=getattr(args, "architect_llm_model", ""),
        args=args,
        default_model=default_model,
        model_tier="sonnet",
    )
    return LLMArchitectCoordinatorAgent(
        provider=provider,
        config=ArchitectCoordinatorConfig(
            model=model,
            model_tier="sonnet",
            max_tokens=getattr(args, "architect_max_tokens", 5000),
            temperature=getattr(args, "architect_temperature", 0.1),
            provider_name=provider_name,
        ),
    )


async def _demo(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    system = (
        AIStatisticianSystem.with_axle(n_runs=args.runs, seed=args.seed)
        if args.real_lean
        else AIStatisticianSystem(n_runs=args.runs, seed=args.seed)
    )
    questions = _questions_from_args(args)
    reports = []
    for question in questions:
        report = await system.run(question)
        reports.append(report)
        if args.out:
            write_trace(report, Path(args.out))
    if args.out:
        write_run_manifest(reports, Path(args.out))

    print("\nAI Statistician System")
    print("=" * 72)
    for report in reports:
        s = compact_summary(report)
        print(
            f"{s['status']:18} {s['question']:24} "
            f"formal={s['formal']:>4} verifier={s['verifier']}"
        )
        print(
            f"  bias={s['bias']:+.5f} rel_bias={s['relative_bias']:+.5f} "
            f"rmse={s['rmse']:.5f} coverage95={s['coverage_95']:.3f}"
        )
        print(f"  sim feedback: {report.simulation.feedback}")
        for proof in report.proofs:
            badge = "OK" if proof.ok else "FAIL"
            print(f"  proof {badge}: {proof.obligation_id} ({proof.elapsed_ms} ms)")
            if proof.errors:
                print(f"    error: {proof.errors[0][:180]}")
        if args.verbose:
            print(f"  estimator: {report.estimator.formula}")
            print(f"  obligations: {', '.join(report.estimator.formal_obligation_ids)}")
    if args.out:
        print(f"\ntraces written to {Path(args.out).resolve()}")
        print(f"manifest written to {(Path(args.out) / 'manifest.json').resolve()}")
    return 0


def _questions_from_args(args: argparse.Namespace):
    proposer = _theory_proposer_from_args(args)
    questions = []
    if args.question_file:
        questions.extend(
            load_question_file(
                Path(args.question_file),
                theory_proposer=proposer,
                force_theory_proposer=bool(getattr(args, "force_llm_theory", False)),
            )
        )
    if getattr(args, "question", None):
        questions.extend(QUESTIONS[question_id] for question_id in args.question)
    if not questions:
        questions.extend(QUESTIONS.values())
    return questions


def _theory_proposer_from_args(args: argparse.Namespace):
    if not getattr(args, "llm_theory", False):
        return None
    provider_choice = getattr(args, "llm_provider", _default_live_generator_provider())
    provider, provider_name = _build_theory_generator_backend(
        provider_name=provider_choice,
        static_response_file=getattr(args, "llm_static_response_file", ""),
    )
    return GeneratorTheoryProposer(
        provider=provider,
        model=_default_model_for_provider(
            provider_choice,
            getattr(args, "llm_model", ""),
            model_tier="haiku",
        ),
        model_tier="haiku",
        provider_name=provider_name,
        max_tokens=getattr(args, "llm_max_tokens", 700),
    )


def _proof_verifier_from_args(args: argparse.Namespace):
    if getattr(args, "local_lean", False):
        lean_project = getattr(args, "lean_project", None) or getattr(
            args,
            "local_lean_project",
            None,
        )
        lean_timeout = getattr(
            args,
            "lean_timeout",
            getattr(args, "local_lean_timeout", 90),
        ) or getattr(args, "local_lean_timeout", 90)
        return LocalLeanProofVerifier(
            project_root=lean_project,
            timeout_s=lean_timeout,
        )
    return AxleProofVerifier() if getattr(args, "real_lean", False) else MockProofVerifier()


def _proof_state_provider_from_args(args: argparse.Namespace):
    if not getattr(args, "local_lean", False):
        return None
    lean_project = getattr(args, "lean_project", None) or getattr(
        args,
        "local_lean_project",
        None,
    )
    lean_timeout = getattr(
        args,
        "lean_timeout",
        getattr(args, "local_lean_timeout", 90),
    ) or getattr(args, "local_lean_timeout", 90)
    return LocalLeanProofStateFeedbackProvider(
        project_root=lean_project,
        timeout_s=lean_timeout,
    )


async def _eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = _questions_from_args(args)
    if args.seeds:
        seeds = tuple(int(seed) for seed in args.seeds)
    else:
        seeds = tuple(range(args.seed_start, args.seed_start + args.n_seeds))
    payload = await run_seed_eval(
        questions,
        EvalConfig(seeds=seeds, n_runs=args.runs, use_axle=args.real_lean),
        Path(args.out),
    )
    print("\nAI Statistician Evaluation")
    print("=" * 72)
    for question_id, row in payload["summary"].items():
        print(
            f"{question_id:32} accepted={row['accepted']}/{row['trials']} "
            f"rate={row['acceptance_rate']:.2f} "
            f"mean_coverage95={row['mean_coverage_95']:.3f} "
            f"mean_rmse={row['mean_rmse']:.5f}"
        )
    print(f"\nevaluation manifest written to {(Path(args.out) / 'evaluation_manifest.json').resolve()}")
    return 0


def _theory_intake(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = _questions_from_args(args)
    print("\nAI Statistician Theory Intake")
    print("=" * 72)
    for question in questions:
        print(
            f"{question.id:32} dgp_family={question.dgp_family:10} "
            f"estimator_family={question.estimator_family:20} params={question.true_params}"
        )
        proposal_tags = [tag for tag in question.tags if tag.startswith("theory_proposal:")]
        if proposal_tags:
            print(f"  {proposal_tags[0]}")
    return 0


async def _proof_audit(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    payload = await audit_proof_bank(
        verifier,
        Path(args.out),
        ids=args.id,
        tags=args.tag,
        require_all_tags=args.require_all_tags,
        export_lean=not args.no_export_lean,
        export_attempt_log=not args.no_attempt_log,
        include_negative_controls=args.negative_controls,
    )
    print("\nAI Statistician Proof-Bank Audit")
    print("=" * 72)
    print(
        f"verified={payload['n_verified']}/{payload['n_obligations']} "
        f"kernel={payload['n_kernel_verified']}/{payload['n_obligations']} "
        f"verifier={payload['verifier']} strength={payload['verification_strength']}"
    )
    for check in payload["checks"]:
        badge = "OK" if check["ok"] else "FAIL"
        print(f"  proof {badge}: {check['obligation_id']} ({check['elapsed_ms']} ms)")
        if check["errors"]:
            print(f"    error: {check['errors'][0][:180]}")
    print(f"\nproof audit manifest written to {(Path(args.out) / 'proof_audit_manifest.json').resolve()}")
    if payload["lean_export_dir"]:
        print(f"Lean exports written to {Path(str(payload['lean_export_dir'])).resolve()}")
    if payload.get("proof_attempt_log"):
        attempt_log = payload["proof_attempt_log"]
        print(f"proof attempts written to {Path(str(attempt_log['attempt_log'])).resolve()}")
    return 0


def _theorem_reduction_closure_work_order_audit(args: argparse.Namespace) -> int:
    payload = audit_theorem_reduction_closure_work_orders(
        Path(args.queue_jsonl),
        Path(args.out),
        run_local_lean=args.local_lean,
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout_seconds=args.lean_timeout,
    )
    print("\nAI Statistician Theorem Reduction Closure Work-Order Audit")
    print("=" * 72)
    print(
        f"work_orders={payload['n_work_orders']} "
        f"exported={payload['n_exported_lean_sketches']} "
        f"local_lean_attempted={payload['n_local_lean_attempted']} "
        f"kernel_verified={payload['n_kernel_verified']} "
        f"placeholders={payload['n_placeholder_rejected']} "
        f"proof_evidence={payload['proof_evidence_status']}"
    )
    print(
        "manifest written to "
        f"{(Path(args.out) / 'theorem_reduction_closure_work_order_audit_manifest.json').resolve()}"
    )
    print(f"Lean sketches written to {Path(str(payload['lean_export_dir'])).resolve()}")
    return 0


def _theorem_reduction_closure_proofengineer_bridge(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    bridge_manifest = run_theorem_reduction_closure_proofengineer_bridge(
        out_dir=out_dir,
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        queue_jsonl=Path(args.queue_jsonl) if args.queue_jsonl else None,
        question_id=str(args.question_id or ""),
        local_lean=bool(args.local_lean),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
    )
    audit_manifest_path = Path(str(bridge_manifest["audit_manifest"]))
    bridge_manifest_path = out_dir / "theorem_reduction_closure_proofengineer_bridge_manifest.json"
    print("\nAI Statistician Theorem-Reduction Closure ProofEngineer Bridge")
    print("=" * 72)
    print(
        f"work_orders={bridge_manifest['n_work_orders']} "
        f"kernel_verified={bridge_manifest['n_kernel_verified']} "
        f"runtime_learning_ready={bridge_manifest['runtime_learning_ready']}"
    )
    print(f"audit manifest written to {audit_manifest_path.resolve()}")
    print(
        "runtime learning rows written to "
        f"{Path(str(bridge_manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"bridge manifest written to {bridge_manifest_path.resolve()}")
    return 0


def _resolve_theorem_reduction_queue_path(args: argparse.Namespace) -> Path:
    return resolve_theorem_reduction_queue_path(
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        queue_jsonl=Path(args.queue_jsonl) if args.queue_jsonl else None,
    )


def _algorithm_audit(args: argparse.Namespace) -> int:
    payload = audit_algorithm_registry(Path(args.out))
    print("\nAI Statistician Algorithm Audit")
    print("=" * 72)
    print(f"passed={payload['n_ok']}/{payload['n_algorithms']}")
    for row in payload["algorithms"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  algorithm {badge}: {row['algorithm_id']} hash={row['implementation_hash'][:12]}")
        if row["errors"]:
            print(f"    error: {row['errors'][0][:180]}")
    print(f"\nalgorithm audit manifest written to {(Path(args.out) / 'algorithm_audit_manifest.json').resolve()}")
    return 0


def _proof_training_export(args: argparse.Namespace) -> int:
    payload = export_proof_training_dataset(
        Path(args.attempt_log),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistician Proof Training Export")
    print("=" * 72)
    print(
        f"examples={payload['n_sft_examples']} train={payload['n_train']} "
        f"validation={payload['n_validation']} source_attempts={payload['n_attempts']}"
    )
    print(f"train_jsonl={Path(str(payload['train_jsonl'])).resolve()}")
    print(f"validation_jsonl={Path(str(payload['validation_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_training_manifest.json').resolve()}")
    return 0


def _proof_repair_export(args: argparse.Namespace) -> int:
    payload = export_proof_repair_dataset(
        Path(args.attempt_log),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistician Proof Repair Export")
    print("=" * 72)
    print(
        f"repair_examples={payload['n_repair_examples']} "
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"negative_attempts={payload['n_negative_attempts']}"
    )
    print(f"train_jsonl={Path(str(payload['train_jsonl'])).resolve()}")
    print(f"validation_jsonl={Path(str(payload['validation_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_repair_manifest.json').resolve()}")
    return 0


def _proof_policy_baseline(args: argparse.Namespace) -> int:
    payload = evaluate_retrieval_proof_policy_baseline(
        Path(args.train_jsonl),
        Path(args.validation_jsonl),
        Path(args.out),
        k=args.k,
    )
    print("\nAI Statistician Proof Policy Baseline")
    print("=" * 72)
    print(
        f"validation={payload['n_validation']} train={payload['n_train']} "
        f"top1_exact={payload['top1_exact']}/{payload['n_validation']} "
        f"top{payload['k']}_exact={payload['top_k_exact']}/{payload['n_validation']}"
    )
    print(
        f"context_hits={payload['predicted_in_retrieved_context']}/{payload['n_validation']} "
        f"mean_score={payload['mean_top1_score']:.3f}"
    )
    print(f"predictions={Path(str(payload['predictions_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_policy_baseline_manifest.json').resolve()}")
    return 0


def _proof_policy_train(args: argparse.Namespace) -> int:
    payload = train_proof_policy_model(
        Path(args.train_jsonl),
        Path(args.out),
        validation_jsonl=Path(args.validation_jsonl) if args.validation_jsonl else None,
        k=args.k,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
        negatives_per_query=args.negatives_per_query,
    )
    print("\nAI Statistician Proof Policy Model")
    print("=" * 72)
    print(
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"train_top1={payload['train_top1_exact']}/{payload['n_train']} "
        f"validation_top{payload['k']}={payload['validation_top_k_exact']}/{payload['n_validation']}"
    )
    print(f"model={Path(str(payload['model_json'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_policy_model_manifest.json').resolve()}")
    return 0


async def _proof_search_audit(args: argparse.Namespace) -> int:
    verifier = _proof_verifier_from_args(args)
    payload = await audit_proof_search_controller(
        Path(args.out),
        verifier=verifier,
        max_obligations=args.max_obligations,
        max_nodes=args.max_nodes,
        include_invalid_probe=args.include_invalid_probe,
        include_registered_proof=not args.no_registered_proof,
        proof_policy_model_json=Path(args.policy_model_json) if args.policy_model_json else None,
        proof_value_model_json=Path(args.value_model_json) if args.value_model_json else None,
    )
    print("\nAI Statistician Proof Search Audit")
    print("=" * 72)
    print(
        f"solved={payload['n_solved']}/{payload['n_obligations']} "
        f"kernel_verified={payload['n_kernel_verified']} "
        f"mean_nodes={payload['mean_nodes_expanded']:.2f} "
        f"policy_model={'on' if payload['policy_model_enabled'] else 'off'} "
        f"value_model={'on' if payload['value_model_enabled'] else 'off'} "
        f"registered={payload['include_registered_proof']}"
    )
    print(f"results={Path(str(payload['results_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_search_audit_manifest.json').resolve()}")
    return 0


def _proof_search_kernel_rerun_queue(args: argparse.Namespace) -> int:
    payload = export_proof_search_kernel_rerun_queue(
        Path(args.proof_search_audit_dir),
        Path(args.out),
        local_lean_project=args.local_lean_project,
        local_lean_timeout=args.local_lean_timeout,
        max_rows=args.max_rows,
    )
    print("\nAI Statistician Proof Search Kernel Rerun Queue")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_queue_rows']} "
        f"ready={payload['n_ready_for_local_lean_or_axle']} "
        f"blocked={payload['n_blocked_missing_selected_proof_body']} "
        f"source_kernel={payload['n_source_kernel_verified']} "
        f"all_ok={payload['all_ok']}"
    )
    print(f"rerun command: {payload['batch_local_lean_rerun_command']}")
    print(
        f"manifest written to "
        f"{(Path(args.out) / 'proof_search_kernel_rerun_queue_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'proof_search_kernel_rerun_queue.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'proof_search_kernel_rerun_queue.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _proof_search_training_export(args: argparse.Namespace) -> int:
    payload = export_proof_search_process_dataset(
        Path(args.results_jsonl),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistician Proof Search Process Export")
    print("=" * 72)
    print(
        f"examples={payload['n_process_examples']} "
        f"positive={payload['n_positive']} negative={payload['n_negative']} "
        f"train={payload['n_train']} validation={payload['n_validation']}"
    )
    print(f"train_jsonl={Path(str(payload['train_jsonl'])).resolve()}")
    print(f"validation_jsonl={Path(str(payload['validation_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_search_training_manifest.json').resolve()}")
    return 0


def _proof_search_value_train(args: argparse.Namespace) -> int:
    payload = train_proof_search_value_model(
        Path(args.train_jsonl),
        Path(args.out),
        validation_jsonl=Path(args.validation_jsonl) if args.validation_jsonl else None,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
    )
    print("\nAI Statistician Proof Search Value Model")
    print("=" * 72)
    print(
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"train_acc={payload['train_accuracy']:.3f} "
        f"val_acc={payload['validation_accuracy']:.3f}"
    )
    print(f"model={Path(str(payload['model_json'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_search_value_model_manifest.json').resolve()}")
    return 0


def _research_algorithm_audit(args: argparse.Namespace) -> int:
    payload = audit_research_algorithm_registry(Path(args.out))
    print("\nAI Statistical Theory Lab Algorithm Audit")
    print("=" * 72)
    print(f"passed={payload['n_ok']}/{payload['n_algorithms']}")
    for row in payload["algorithms"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  algorithm {badge}: {row['algorithm_id']} hash={row['implementation_hash'][:12]}")
        for error in row["errors"]:
            print(f"    error: {error[:180]}")
    print(
        f"\nresearch algorithm audit manifest written to "
        f"{(Path(args.out) / 'research_algorithm_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _research_intake_audit(args: argparse.Namespace) -> int:
    supported_files = tuple(Path(path) for path in args.supported_file) if args.supported_file else None
    unsupported_files = tuple(Path(path) for path in args.unsupported_file) if args.unsupported_file else None
    payload = audit_research_question_intake(
        Path(args.out),
        supported_files=supported_files,
        unsupported_files=unsupported_files,
    )
    print("\nAI Statistical Theory Lab Intake Audit")
    print("=" * 72)
    print(
        f"supported={payload['n_supported_accepted']}/{payload['n_supported']} "
        f"unsupported_rejected={payload['n_unsupported_rejected']}/{payload['n_unsupported']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(
            f"  {badge:4} {row['question_id']} expected={row['expected']} "
            f"class={row['problem_class']}"
        )
        if row["error"]:
            print(f"       {row['error'][:180]}")
    print(
        f"\nresearch intake audit manifest written to "
        f"{(Path(args.out) / 'research_intake_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _frontier_coverage_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_coverage(Path(args.out), benchmark_file=Path(args.benchmark_file))
    print("\nAI Statistical Theory Lab Frontier Coverage Audit")
    print("=" * 72)
    print(
        f"parsed={payload['n_questions']} supported={payload['n_supported']} "
        f"unsupported={payload['n_unsupported']} rate={payload['supported_rate']:.2f} "
        f"all_ok={payload['all_ok']}"
    )
    for problem_class, count in payload["by_problem_class"].items():
        print(f"  {problem_class}: {count}")
    print(
        f"\nfrontier coverage manifest written to "
        f"{(Path(args.out) / 'frontier_coverage_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_coverage.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_precision_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_precision(Path(args.out), benchmark_file=Path(args.benchmark_file))
    print("\nAI Statistical Theory Lab Frontier Precision Audit")
    print("=" * 72)
    print(
        f"supported={payload['n_supported']} body_evidence_ok={payload['n_ok']} "
        f"flagged={payload['n_flagged']} all_ok={payload['all_ok']}"
    )
    for row in payload["rows"]:
        evidence = ", ".join(row["evidence_terms"]) or row["reason"]
        print(f"  {row['ok']}: {row['question_id']} class={row['problem_class']} evidence={evidence}")
    print(f"\nfrontier precision manifest written to {(Path(args.out) / 'frontier_precision_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'frontier_precision.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_backlog_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_backlog(Path(args.out), benchmark_file=Path(args.benchmark_file))
    print("\nAI Statistical Theory Lab Frontier Backlog Audit")
    print("=" * 72)
    print(
        f"backlog={payload['n_ok']}/{payload['n_backlog']} "
        f"domains={len(payload['by_domain'])} all_ok={payload['all_ok']}"
    )
    for domain, count in payload["by_domain"].items():
        print(f"  {domain}: {count}")
    print(f"\nfrontier backlog manifest written to {(Path(args.out) / 'frontier_backlog_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'frontier_backlog.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_theory_target_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_theory_targets(
        Path(args.run_dir),
        Path(args.out),
        benchmark_file=Path(args.benchmark_file),
        coverage_threshold=args.coverage_threshold,
    )
    print("\nAI Statistical Theory Lab Frontier Theory Target Audit")
    print("=" * 72)
    print(
        f"scored={payload['n_scored']}/{payload['n_traces']} "
        f"covered={payload['n_covered_results']}/{payload['n_expected_results']} "
        f"rate={payload['expected_result_coverage_rate']:.2f} "
        f"all_scored={payload['all_scored']}"
    )
    for row in payload["rows"]:
        print(
            f"  {row['question_id']}: class={row['problem_class']} "
            f"covered={row['n_covered_results']}/{row['n_expected_results']} "
            f"mean={row['mean_expected_result_coverage']:.2f}"
        )
    print(
        f"\nfrontier theory target manifest written to "
        f"{(Path(args.out) / 'frontier_theory_target_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_theory_target.md').resolve()}")
    return 0 if payload["all_scored"] else 1


def _frontier_discover_and_prove_prompt_packets(args: argparse.Namespace) -> int:
    payload = export_frontier_discover_and_prove_prompt_packets(
        Path(args.out),
        benchmark_file=Path(args.benchmark_file),
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Frontier Discover-and-Prove Prompt Packets")
    print("=" * 72)
    print(
        f"packets={payload['n_prompt_packets']} "
        f"contracts={payload['n_output_contracts']} "
        f"expected_leaks={payload['n_prompt_expected_result_leaks']} "
        f"source_leaks={payload['n_prompt_source_identity_leaks']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nfrontier DAP prompt manifest written to "
        f"{(Path(args.out) / 'frontier_discover_and_prove_prompt_packets_manifest.json').resolve()}"
    )
    print(
        f"jsonl written to "
        f"{(Path(args.out) / 'frontier_discover_and_prove_prompt_packets.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'frontier_discover_and_prove_prompt_packets.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _paper_theory_roundtrip(args: argparse.Namespace) -> int:
    payload = export_paper_theory_roundtrip(
        Path(args.paper_root),
        Path(args.out),
        paper_id=args.paper_id or None,
        max_statements=args.max_statements,
    )
    print("\nAI Statistical Theory Lab Paper Theory Round-Trip")
    print("=" * 72)
    print(
        f"tex_files={payload['n_tex_files']} statements={payload['n_statements']} "
        f"lean_queue={payload['n_lean_candidate_queue_rows']} "
        f"roundtrip={payload['n_roundtrip_review_rows']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\npaper theory manifest written to "
        f"{(Path(args.out) / 'paper_theory_roundtrip_manifest.json').resolve()}"
    )
    print(
        f"statement catalog written to "
        f"{(Path(args.out) / 'paper_statement_catalog.jsonl').resolve()}"
    )
    print(
        f"Lean candidate queue written to "
        f"{(Path(args.out) / 'statement_to_lean_candidate_queue.jsonl').resolve()}"
    )
    print(
        f"round-trip review queue written to "
        f"{(Path(args.out) / 'lean_to_latex_roundtrip_review_queue.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _frontier_evaluation_triage(args: argparse.Namespace) -> int:
    payload = audit_frontier_evaluation_triage(
        Path(args.run_dir),
        Path(args.theory_target_manifest),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Frontier Evaluation Triage")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_items']} "
        f"theory_misses={payload['n_theory_target_misses']} "
        f"simulation_flags={payload['n_simulation_flags']} "
        f"all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_owner"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nfrontier evaluation triage manifest written to "
        f"{(Path(args.out) / 'frontier_evaluation_triage_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_evaluation_triage.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_simulation_rerun_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_simulation_reruns(
        Path(args.triage_manifest),
        Path(args.out),
        n_runs=args.runs,
        seed=args.seed,
    )
    print("\nAI Statistical Theory Lab Frontier Simulation Rerun Audit")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_items']} "
        f"resolved={payload['n_resolved']} "
        f"still_flagged={payload['n_still_flagged']} "
        f"all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_new_owner_agent"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nfrontier simulation rerun manifest written to "
        f"{(Path(args.out) / 'frontier_simulation_rerun_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_simulation_rerun.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_theory_revision_queue(args: argparse.Namespace) -> int:
    payload = export_frontier_theory_revision_queue(
        Path(args.simulation_rerun_manifest),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Frontier Theory Revision Queue")
    print("=" * 72)
    print(
        f"tasks={payload['n_ok']}/{payload['n_tasks']} "
        f"all_ok={payload['all_ok']}"
    )
    for failure_class, count in payload["by_failure_class"].items():
        print(f"  {failure_class}: {count}")
    print(
        f"\nfrontier theory revision queue manifest written to "
        f"{(Path(args.out) / 'frontier_theory_revision_queue_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'frontier_theory_revision_queue.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'frontier_theory_revision_queue.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_theory_revision_formalization_audit(args: argparse.Namespace) -> int:
    source_index = Path(args.formal_source_index) if args.formal_source_index else Path(args.out) / "formal_source_index.sqlite"
    payload = audit_frontier_theory_revision_formalization(
        Path(args.revision_queue_manifest),
        Path(args.out),
        formal_source_index_path=source_index,
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Frontier Theory Revision Formalization Audit")
    print("=" * 72)
    print(
        f"obligations={payload['n_ok']}/{payload['n_obligations']} "
        f"unique={payload['n_unique_obligations']} "
        f"proof_bank_bridge={payload['n_unique_proof_bank_bridge']} "
        f"local_source_only={payload['n_unique_local_source_only']} "
        f"source_gap={payload['n_unique_source_gap']} "
        f"all_ok={payload['all_ok']}"
    )
    for classification, count in payload["by_unique_classification"].items():
        print(f"  {classification}: {count}")
    print(
        f"\nfrontier theory revision formalization manifest written to "
        f"{(Path(args.out) / 'frontier_theory_revision_formalization_manifest.json').resolve()}"
    )
    print(
        f"jsonl written to "
        f"{(Path(args.out) / 'frontier_theory_revision_formalization_tasks.jsonl').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_theory_revision_formalization.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_knowledge_audit(args: argparse.Namespace) -> int:
    payload = audit_research_knowledge(Path(args.out), question_file=Path(args.question_file))
    print("\nAI Statistical Theory Lab Knowledge Audit")
    print("=" * 72)
    print(
        f"sources={payload['n_source_ok']}/{payload['n_cards']} "
        f"inventory={payload['source_inventory']['n_ok']}/{payload['source_inventory']['n_sources']} "
        f"problem_retrieval={payload['n_problem_ok']}/{payload['n_problem_rows']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["problem_rows"]:
        print(
            f"  {row['question_id']}: class={row['problem_class']} "
            f"primary={row['expected_primary']} top={row['top_hit']} "
            f"formal_infra={row['has_formal_infra']}"
        )
    print(
        f"\nresearch knowledge manifest written to "
        f"{(Path(args.out) / 'research_knowledge_audit_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'research_knowledge_audit.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _lean_blueprint_knowledge(args: argparse.Namespace) -> int:
    payload = export_lean_blueprint_knowledge(
        Path(args.out),
        blueprint_root=Path(args.blueprint_root) if args.blueprint_root else None,
    )
    graph = payload["knowledge_graph"]
    source = payload["source"]
    print("\nAI Statistical Theory Lab LeanBlueprint Knowledge")
    print("=" * 72)
    print(
        f"available={source.get('exists')} all_ok={payload['all_ok']} "
        f"commit={str(source.get('git_commit', ''))[:12]} root={source.get('root')}"
    )
    print(
        f"macros={len(payload['macros'])} statuses={len(payload['statuses'])} "
        f"graph={graph.get('n_nodes')} nodes/{graph.get('n_edges')} edges"
    )
    print(
        f"\nLeanBlueprint manifest written to "
        f"{(Path(args.out) / 'lean_blueprint_knowledge_manifest.json').resolve()}"
    )
    print(f"graph written to {(Path(args.out) / 'lean_blueprint_knowledge_graph.json').resolve()}")
    print(
        f"adapter plan written to "
        f"{(Path(args.out) / 'lean_blueprint_visualization_adapter_plan.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


async def _frontier_smoke_benchmark(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    payload = await run_frontier_smoke_benchmark(
        Path(args.out),
        benchmark_file=Path(args.benchmark_file),
        config=FrontierSmokeConfig(
            n_runs=args.runs,
            seed=args.seed,
            max_per_class=args.max_per_class,
            use_axle=args.real_lean,
            cache_dir=args.frontier_smoke_cache or None,
            refresh_cache=args.refresh_frontier_smoke_cache,
            simulation_rerun_runs=args.simulation_rerun_runs,
        ),
        proof_verifier=verifier,
    )
    print("\nAI Statistical Theory Lab Frontier Smoke Benchmark")
    print("=" * 72)
    print(
        f"selected={payload['n_selected']} ready={payload['counts']['ready_with_gaps']}/{payload['counts']['questions']} "
        f"triage={payload['counts']['frontier_triage_items']} "
        f"rerun_resolved={payload['counts']['frontier_simulation_rerun_resolved']} "
        f"theory_revisions={payload['counts']['frontier_theory_revision_tasks']} "
        f"formalized_revision_obligations={payload['counts']['frontier_theory_revision_formal_obligations']} "
        f"all_gates_passed={payload['all_gates_passed']} "
        f"cache={payload['counts']['frontier_smoke_cache_status']}"
    )
    for row in payload["selections"]:
        print(f"  {row['question_id']}: class={row['problem_class']} topic={row['topic']}")
    print(f"\nfrontier smoke manifest written to {(Path(args.out) / 'frontier_smoke_manifest.json').resolve()}")
    return 0 if payload["all_gates_passed"] else 1


def _retrieval_audit(args: argparse.Namespace) -> int:
    payload = audit_proof_bank_retrieval(
        Path(args.out),
        k=args.k,
        include_loogle=args.loogle,
        loogle_k=args.loogle_k,
        loogle_timeout_s=args.loogle_timeout,
    )
    print("\nAI Statistician Retrieval Audit")
    print("=" * 72)
    print(
        f"top1={payload['top1']}/{payload['n_obligations']} "
        f"top{payload['k']}={payload['top_k']}/{payload['n_obligations']} "
        f"mrr={payload['mrr']:.3f}"
    )
    for row in payload["rows"]:
        top1 = row["top1"] or "none"
        print(f"  {row['obligation_id']}: rank={row['rank']} top1={top1}")
    if payload["loogle"]["enabled"]:
        loogle = payload["loogle"]
        print(
            f"\nloogle evidence: expected_lemma_hits="
            f"{loogle['n_expected_lemma_hits']}/{loogle['n_queries']} "
            f"errors={loogle['n_errors']}"
        )
        for row in loogle["rows"][:5]:
            status = "HIT" if row["expected_lemma_hit"] else "MISS"
            first = row["hits"][0] if row["hits"] else (row["error"] or "none")
            print(f"  loogle {status}: {row['obligation_id']} first={first}")
    print(f"\nretrieval audit manifest written to {(Path(args.out) / 'retrieval_audit_manifest.json').resolve()}")
    return 0


def _formal_source_audit(args: argparse.Namespace) -> int:
    payload = audit_formal_source_index(Path(args.out), k=args.k, backend=args.backend)
    print("\nAI Statistical Theory Lab Formal Source Index")
    print("=" * 72)
    print(
        f"sources={payload['n_sources']} declarations={payload['n_declarations']} "
        f"queries={payload['n_query_ok']}/{payload['n_queries']} backend={payload['search_backend']}"
    )
    for row in payload["query_rows"]:
        first = row["top_hits"][0] if row["top_hits"] else None
        first_name = first["name"] if first else "none"
        first_source = first["source_id"] if first else "none"
        print(f"  {row['query_id']}: ok={row['ok']} top={first_name} source={first_source}")
    print(
        f"\nformal source index manifest written to "
        f"{(Path(args.out) / 'formal_source_index_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_index.md').resolve()}")
    if payload.get("sqlite_index_path"):
        print(f"sqlite index written to {Path(str(payload['sqlite_index_path'])).resolve()}")
    return 0 if payload["all_queries_ok"] else 1


def _formal_source_graph_audit(args: argparse.Namespace) -> int:
    payload = audit_formal_source_graph(
        Path(args.out),
        k=args.k,
        cache_path=Path(args.formal_source_graph_cache) if args.formal_source_graph_cache else None,
        refresh_cache=args.refresh_formal_source_graph_cache,
    )
    print("\nAI Statistical Theory Lab Formal Source Graph")
    print("=" * 72)
    print(
        f"declarations={payload['n_declarations']} "
        f"symbols={payload['n_symbol_nodes']} edges={payload['n_edges']} "
        f"queries={payload['n_query_ok']}/{payload['n_queries']} "
        f"cache={payload['cache']['status']}"
    )
    for row in payload["query_rows"]:
        first = row["top_hits"][0] if row["top_hits"] else None
        first_name = first["name"] if first else "none"
        first_source = first["source_id"] if first else "none"
        print(f"  {row['query_id']}: ok={row['ok']} top={first_name} source={first_source}")
    print(
        f"\nformal source graph manifest written to "
        f"{(Path(args.out) / 'formal_source_graph_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_graph.md').resolve()}")
    return 0 if payload["all_queries_ok"] else 1


def _lean_rag_package_audit(args: argparse.Namespace) -> int:
    payload = audit_lean_rag_package(
        Path(args.out),
        package_root=Path(args.package_root) if args.package_root else None,
        db_dir=Path(args.db_dir) if args.db_dir else None,
    )
    registry = payload["source_registry"]
    seeds = payload["seed_queries"]
    coverage = payload["target_source_coverage"]
    graph = payload["shared_graph_manifest"]
    print("\nAI Statistical Theory Lab Lean RAG Package Audit")
    print("=" * 72)
    print(
        f"available={payload['available']} contract_ok={payload['contract_ok']} "
        f"package_root={payload['package_root']}"
    )
    print(
        f"sources=local:{registry.get('n_local_sources', 0)} "
        f"external:{registry.get('n_external_sources', 0)} "
        f"seed_queries={seeds.get('n_queries', 0)} lanes={','.join(seeds.get('lanes', [])) or 'none'}"
    )
    missing_targets = ",".join(coverage.get("missing_target_ids", [])) or "none"
    print(
        f"target_sources={coverage.get('n_present', 0)}/{coverage.get('n_targets', 0)} "
        f"coverage_ok={coverage.get('coverage_ok', False)} "
        f"registry_candidates={coverage.get('n_registry_expansion_candidates', 0)} "
        f"missing={missing_targets}"
    )
    print(
        f"shared_graph_manifest={graph.get('available')} "
        f"indexed_checkouts={graph.get('n_indexed_checkouts', 0)} "
        f"dirty_checkouts={graph.get('n_dirty_checkouts', 0)} "
        f"failed_checkouts={graph.get('n_failed_checkouts', 0)}"
    )
    print(
        f"\nlean RAG package audit manifest written to "
        f"{(Path(args.out) / 'lean_rag_package_audit_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'lean_rag_package_audit.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _lean_rag_source_registry_expansion(args: argparse.Namespace) -> int:
    payload = stage_lean_rag_source_registry_expansion(
        Path(args.out),
        package_root=Path(args.package_root) if args.package_root else None,
        db_dir=Path(args.db_dir) if args.db_dir else None,
    )
    before = payload["target_source_coverage_before"]
    after = payload["target_source_coverage_after"]
    print("\nAI Statistical Theory Lab Lean RAG Source Registry Expansion")
    print("=" * 72)
    print(
        f"package_contract_ok={payload['package_contract_ok']} "
        f"stage_ready={payload['stage_ready']} package_root={payload['package_root']}"
    )
    print(
        f"coverage={before.get('n_present', 0)}/{before.get('n_targets', 0)} -> "
        f"{after.get('n_present', 0)}/{after.get('n_targets', 0)} "
        f"candidates={payload['n_candidates']} staged={payload['n_staged']} "
        f"already_present={payload['n_already_present']} invalid={payload['n_invalid']}"
    )
    print(f"clone_commands={len(payload.get('clone_commands', []))}")
    print(
        f"\nsource registry expansion manifest written to "
        f"{(Path(args.out) / 'source_registry_expansion_manifest.json').resolve()}"
    )
    print(f"staged source registry written to {(Path(args.out) / 'staged_source_registry.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _lean_rag_source_registry_expansion_preflight(args: argparse.Namespace) -> int:
    payload = preflight_lean_rag_source_registry_expansion(
        Path(args.out),
        expansion_manifest=Path(args.expansion_manifest),
    )
    print("\nAI Statistical Theory Lab Lean RAG Source Registry Expansion Preflight")
    print("=" * 72)
    print(
        f"package_clean={payload['package_clean']} "
        f"apply_ready={payload['source_registry_apply_ready']} "
        f"no_staged={payload.get('no_staged', False)} "
        f"external_refresh_ready={payload['external_refresh_ready']}"
    )
    print(
        f"rows={payload['n_rows']} clone_required={payload['n_clone_required']} "
        f"present_clean_git={payload['n_present_clean_git']} "
        f"present_local_path={payload['n_present_local_path']} "
        f"indexer_unsupported={payload['n_indexer_unsupported']} "
        f"hard_blockers={payload['n_hard_blockers']}"
    )
    print(
        f"\nsource registry expansion preflight manifest written to "
        f"{(Path(args.out) / 'source_registry_expansion_preflight_manifest.json').resolve()}"
    )
    return 0 if payload["source_registry_apply_ready"] or payload.get("no_staged", False) else 1


def _lean_rag_source_registry_expansion_apply(args: argparse.Namespace) -> int:
    payload = apply_lean_rag_source_registry_expansion(
        Path(args.out),
        expansion_manifest=Path(args.expansion_manifest),
        preflight_manifest=Path(args.preflight_manifest)
        if args.preflight_manifest
        else None,
        dry_run=not args.apply,
    )
    before = dict(payload.get("target_source_coverage_before", {}) or {})
    after = dict(payload.get("target_source_coverage_after", {}) or {})
    print("\nAI Statistical Theory Lab Lean RAG Source Registry Expansion Apply")
    print("=" * 72)
    print(
        f"dry_run={payload['dry_run']} apply_ready={payload['apply_ready']} "
        f"applied={payload['applied']} no_staged={payload.get('no_staged', False)}"
    )
    print(
        f"coverage={before.get('n_present', 0)}/{before.get('n_targets', 0)} -> "
        f"{after.get('n_present', 0)}/{after.get('n_targets', 0)} "
        f"staged={payload['n_staged']}"
    )
    if payload["errors"]:
        print("errors=" + "; ".join(str(error) for error in payload["errors"]))
    if payload["warnings"]:
        print("warnings=" + "; ".join(str(warning) for warning in payload["warnings"]))
    print(
        f"\nsource registry expansion apply manifest written to "
        f"{(Path(args.out) / 'source_registry_expansion_apply_manifest.json').resolve()}"
    )
    return 0 if payload["apply_ready"] and (
        payload["dry_run"] or payload["applied"] or payload.get("no_staged", False)
    ) else 1


def _huggingface_lean_source_audit(args: argparse.Namespace) -> int:
    payload = audit_huggingface_lean_sources(
        Path(args.out),
        max_results_per_query=args.max_results_per_query,
        max_detail_fetches=args.max_detail_fetches,
        timeout_s=args.timeout,
        use_network=not args.no_network,
    )
    summary = payload["summary"]
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Audit")
    print("=" * 72)
    print(
        f"candidates={summary.get('n_candidates', 0)} "
        f"critical={summary.get('n_critical', 0)} high={summary.get('n_high', 0)} "
        f"public_ungated={summary.get('n_public_ungated', 0)}"
    )
    print(
        f"oproofs_detected={summary.get('oproofs_detected', False)} "
        f"oproofs_rows={summary.get('oproofs_reported_rows', 0)} "
        f"oproofs_shards={summary.get('oproofs_parquet_shards', 0)} "
        f"proof_evidence_ready={summary.get('proof_evidence_ready', 0)}"
    )
    queue_summary = payload.get("revalidation_queue_summary", {})
    print(
        f"revalidation_queue={queue_summary.get('n_queue_rows', 0)} "
        f"ready={queue_summary.get('n_ready', 0)} "
        f"kernel_verified={queue_summary.get('n_kernel_verified', 0)} "
        f"status={queue_summary.get('proof_evidence_status', '')}"
    )
    for row in payload["rows"][:10]:
        print(
            f"  {row['priority']:8} {row['dataset_id']:48} "
            f"class={row['relevance_class']} rows={row['num_rows']}"
        )
    print(
        f"\nhuggingface Lean source audit manifest written to "
        f"{(Path(args.out) / 'huggingface_lean_source_audit_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'huggingface_lean_source_audit.md').resolve()}")
    return 0 if summary.get("oproofs_detected") else 1


def _huggingface_lean_source_revalidation_tasks(args: argparse.Namespace) -> int:
    payload = export_huggingface_lean_source_revalidation_tasks(
        Path(args.queue_jsonl),
        Path(args.out),
        max_tasks=args.max_tasks,
        sample_seed=args.sample_seed,
    )
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Revalidation Tasks")
    print("=" * 72)
    print(
        f"tasks={payload['n_tasks']} ready={payload['n_ready']} "
        f"blocked={payload['n_blocked']} "
        f"license_review={payload['n_license_review_required']}"
    )
    print(
        f"kernel_verified={payload['n_kernel_verified']} "
        f"proof_evidence_ready={payload['n_proof_evidence_ready']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nhf Lean source revalidation task manifest written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_tasks_manifest.json').resolve()}"
    )
    print(
        f"task queue written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_tasks.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _huggingface_lean_source_revalidation_prompt_packets(args: argparse.Namespace) -> int:
    payload = export_huggingface_lean_source_revalidation_prompt_packets(
        Path(args.task_dir),
        Path(args.out),
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Revalidation Prompt Packets")
    print("=" * 72)
    print(
        f"tasks={payload['n_tasks']} ready={payload['n_ready_tasks']} "
        f"prompt_packets={payload['n_prompt_packets']} "
        f"license_review={payload['n_license_review_required']}"
    )
    print(
        f"output_contracts={payload['n_with_output_contract']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nhf Lean source revalidation prompt packet manifest written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_prompt_packets_manifest.json').resolve()}"
    )
    print(
        f"prompt packet queue written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_prompt_packets.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _huggingface_lean_source_revalidation_artifact_validation(args: argparse.Namespace) -> int:
    payload = export_huggingface_lean_source_revalidation_artifact_validation(
        Path(args.task_dir),
        Path(args.out),
        response_jsonl=Path(args.response_jsonl) if args.response_jsonl else None,
    )
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Revalidation Artifact Validation")
    print("=" * 72)
    print(
        f"tasks={payload['n_tasks']} responses={payload['n_responses']} "
        f"awaiting={payload['n_awaiting_worker_output']} "
        f"contract_ok={payload['n_contract_ok']}"
    )
    print(
        f"kernel_verified_rows={payload['n_kernel_verified_rows']} "
        f"proof_evidence_ready={payload['n_proof_evidence_ready']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nhf Lean source revalidation artifact validation manifest written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_artifact_validation_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _huggingface_lean_source_revalidation_promotion_queue(args: argparse.Namespace) -> int:
    payload = export_huggingface_lean_source_revalidation_promotion_queue(
        Path(args.artifact_validation_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Hugging Face Lean Source Revalidation Promotion Queue")
    print("=" * 72)
    print(
        f"rows={payload['n_promotion_rows']} ready={payload['n_ready_for_promotion']} "
        f"awaiting={payload['n_awaiting_worker_output']} blocked={payload['n_blocked']}"
    )
    print(
        f"kernel_verified_rows={payload['n_kernel_verified_rows']} "
        f"proof_evidence_ready={payload['n_proof_evidence_ready']} "
        f"status={payload['proof_evidence_status']}"
    )
    print(
        f"\nhf Lean source promotion queue manifest written to "
        f"{(Path(args.out) / 'hf_lean_source_revalidation_promotion_queue_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _lean_rag_dependency_health(args: argparse.Namespace) -> int:
    payload = audit_lean_rag_dependency_health(
        Path(args.out),
        requested_db_path=Path(args.db) if args.db else None,
        active_db_path=Path(args.active_db) if args.active_db else Path(args.db) if args.db else None,
        auto_discovered=args.auto_discovered,
    )
    print("\nAI Statistical Theory Lab Lean RAG Dependency Health")
    print("=" * 72)
    print(
        f"status={payload['health_status']} active={payload['active_enabled']} "
        f"fallback={payload['fallback_used']} reason={payload['fallback_reason']}"
    )
    print(
        f"\nlean RAG dependency health manifest written to "
        f"{(Path(args.out) / 'lean_rag_dependency_health_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'lean_rag_dependency_health.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formal_source_retrieval_benchmark(args: argparse.Namespace) -> int:
    suites = {
        "default": DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
        "external": EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
        "all": ALL_FORMAL_SOURCE_RETRIEVAL_BENCHMARKS,
    }
    retriever = build_formal_source_search_backend(
        db_path=Path(args.formal_source_index),
        cache_path=Path(args.formal_source_index_cache) if args.formal_source_index_cache else None,
        refresh_cache=args.refresh_formal_source_index_cache,
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
    )
    payload = run_formal_source_retrieval_benchmark(
        Path(args.out),
        retriever=retriever,
        cases=suites[args.suite],
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Formal Source Retrieval Benchmark")
    print("=" * 72)
    print(
        f"suite={args.suite} hits={payload['n_ok']}/{payload['n_cases']} "
        f"recall@{payload['k']}={payload['recall_at_k']:.3f} "
        f"mrr={payload['mean_reciprocal_rank']:.3f} "
        f"lean_rag={payload['lean_rag_dependency_graph_enabled']} "
        f"cache={getattr(retriever, 'cache_status', 'unknown')}"
    )
    for row in payload["rows"]:
        print(
            f"  {row['query_id']}: ok={row['ok']} rank={row['hit_rank'] or 'miss'} "
            f"top={row['top1_name']} source={row['top1_source_id']}"
        )
    print(
        f"\nretrieval benchmark manifest written to "
        f"{(Path(args.out) / 'formal_source_retrieval_benchmark_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_retrieval_benchmark.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formal_source_retrieval_ablation(args: argparse.Namespace) -> int:
    suites = {
        "default": DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
        "external": EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
        "all": ALL_FORMAL_SOURCE_RETRIEVAL_BENCHMARKS,
    }
    baseline_retriever, enhanced_retriever = _formal_source_ablation_retrievers(args)
    payload = run_formal_source_retrieval_ablation_benchmark(
        Path(args.out),
        baseline_retriever=baseline_retriever,
        enhanced_retriever=enhanced_retriever,
        cases=suites[args.suite],
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Formal Source Retrieval Ablation")
    print("=" * 72)
    print(
        f"suite={args.suite} cases={payload['n_cases']} "
        f"new_hits={payload['n_new_hits']} lost_hits={payload['n_lost_hits']} "
        f"rank_improved={payload['n_rank_improved']} rank_regressed={payload['n_rank_regressed']} "
        f"dependency_sensitive={payload['n_dependency_sensitive_cases']} "
        f"lean_rag={payload['enhanced']['lean_rag_dependency_graph_enabled']}"
    )
    print(
        f"baseline_recall={payload['baseline']['recall_at_k']:.3f} "
        f"enhanced_recall={payload['enhanced']['recall_at_k']:.3f}"
    )
    print(
        f"\nretrieval ablation manifest written to "
        f"{(Path(args.out) / 'formal_source_retrieval_ablation_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_retrieval_ablation.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _proof_search_retrieval_ablation(args: argparse.Namespace) -> int:
    baseline_retriever, enhanced_retriever = _formal_source_ablation_retrievers(args)
    payload = asyncio.run(
        run_proof_search_retrieval_ablation(
            Path(args.out),
            baseline_retriever=baseline_retriever,
            enhanced_retriever=enhanced_retriever,
            verifier=_proof_verifier_from_args(args),
            max_obligations=args.max_obligations,
            max_nodes=args.max_nodes,
            formal_source_k=args.formal_source_k,
            include_registered_proof=not args.no_registered_proof,
        )
    )
    print("\nAI Statistical Theory Lab Proof Search Retrieval Ablation")
    print("=" * 72)
    print(
        f"solved_delta={payload['solved_delta']} "
        f"candidate_delta={payload['formal_source_candidate_delta']} "
        f"node_delta={payload['nodes_expanded_delta']} "
        f"lean_rag={payload['lean_rag_dependency_graph_enabled']} "
        f"dependency_graph_search={payload['dependency_graph_search'] or 'disabled'} "
        f"registered={payload['include_registered_proof']} "
        f"saturated={payload['saturation_warning']}"
    )
    print(
        f"baseline_solved={payload['baseline']['n_solved']}/{payload['baseline']['n_obligations']} "
        f"enhanced_solved={payload['enhanced']['n_solved']}/{payload['enhanced']['n_obligations']}"
    )
    print(
        f"\nproof-search ablation manifest written to "
        f"{(Path(args.out) / 'proof_search_retrieval_ablation_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'proof_search_retrieval_ablation.md').resolve()}")
    return 0 if payload["no_solved_regression"] else 1


def _formal_source_ablation_retrievers(args: argparse.Namespace) -> tuple[object, object]:
    index_path = Path(args.formal_source_index)
    enhanced_retriever = build_formal_source_search_backend(
        db_path=index_path,
        cache_path=Path(args.formal_source_index_cache) if args.formal_source_index_cache else None,
        refresh_cache=args.refresh_formal_source_index_cache,
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
    )
    declarations = (
        enhanced_retriever.load_declarations()
        if hasattr(enhanced_retriever, "load_declarations")
        else []
    )
    baseline_retriever = FormalSourceHybridRetriever(
        declarations,
        FormalSourceSqliteIndex(index_path),
        dependency_retriever=None,
    )
    return baseline_retriever, enhanced_retriever


def _intake_audit(args: argparse.Namespace) -> int:
    supported_files = tuple(Path(path) for path in args.supported_file) if args.supported_file else None
    unsupported_files = tuple(Path(path) for path in args.unsupported_file) if args.unsupported_file else None
    payload = audit_question_intake(
        Path(args.out),
        supported_files=supported_files,
        unsupported_files=unsupported_files,
    )
    print("\nAI Statistician Intake Audit")
    print("=" * 72)
    print(
        f"supported={payload['n_supported_accepted']}/{payload['n_supported']} "
        f"unsupported_rejected={payload['n_unsupported_rejected']}/{payload['n_unsupported']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['question_id']} expected={row['expected']}")
        if row["error"]:
            print(f"       {row['error'][:180]}")
    print(f"\nintake audit manifest written to {(Path(args.out) / 'intake_audit_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _trace_audit(args: argparse.Namespace) -> int:
    payload = audit_run_traces(Path(args.run_dir), Path(args.out))
    print("\nAI Statistician Trace Audit")
    print("=" * 72)
    print(f"traces={payload['n_ok']}/{payload['n_traces']} all_ok={payload['all_ok']}")
    for error in payload["manifest_errors"]:
        print(f"  manifest error: {error}")
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['question_id']} {row['trace_path']}")
        for error in row["errors"]:
            print(f"       {error[:180]}")
    print(f"\ntrace audit manifest written to {(Path(args.out) / 'trace_audit_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_trace_audit(args: argparse.Namespace) -> int:
    payload = audit_research_traces(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Trace Audit")
    print("=" * 72)
    print(f"traces={payload['n_ok']}/{payload['n_traces']} all_ok={payload['all_ok']}")
    for error in payload["manifest_errors"]:
        print(f"  manifest error: {error}")
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['question_id']} {row['trace_path']}")
        for error in row["errors"]:
            print(f"       {error[:180]}")
    print(f"\nresearch trace audit manifest written to {(Path(args.out) / 'research_trace_audit_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_gap_audit(args: argparse.Namespace) -> int:
    payload = audit_research_gap_backlog(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Formal Gap Backlog")
    print("=" * 72)
    print(
        f"gaps={payload['n_ok']}/{payload['n_gaps']} "
        f"artifacts={payload['n_artifacts_present']}/{payload['n_gaps']} "
        f"all_ok={payload['all_ok']}"
    )
    for error in payload["manifest_errors"]:
        print(f"  manifest error: {error}")
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['gap_id']} class={row['problem_class']}")
        for error in row["errors"]:
            print(f"       {error[:180]}")
    print(
        f"\nresearch gap backlog written to "
        f"{(Path(args.out) / 'research_gap_backlog_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'research_gap_backlog.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formalization_target_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_targets(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Formalization Target Queue")
    print("=" * 72)
    print(f"targets={payload['n_ok']}/{payload['n_targets']} all_ok={payload['all_ok']}")
    for row in payload["top_targets"][:10]:
        print(
            f"  {row['priority_band']:24} score={row['priority_score']:4} "
            f"{row['primitive']} gaps={row['n_gaps']}"
        )
        print(f"       bridge: {row['bridge_readiness']}")
        print(f"       next: {row['suggested_next_step'][:180]}")
    print(
        f"\nformalization target manifest written to "
        f"{(Path(args.out) / 'formalization_target_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formalization_targets.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formal_gap_task_export(args: argparse.Namespace) -> int:
    payload = export_formal_gap_lean_tasks(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Formal Gap Lean Tasks")
    print("=" * 72)
    print(f"tasks={payload['n_ok']}/{payload['n_tasks']} all_ok={payload['all_ok']}")
    for row in payload["tasks"][:10]:
        print(
            f"  {row['priority_hint']:24} {row['task_id']} "
            f"primitives={len(row['required_primitives'])}"
        )
    print(
        f"\nformal gap task manifest written to "
        f"{(Path(args.out) / 'formal_gap_lean_task_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'formal_gap_lean_tasks.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'formal_gap_lean_tasks.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _autoform_target_export(args: argparse.Namespace) -> int:
    payload = export_autoform_targets(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Autoform Target Export")
    print("=" * 72)
    print(f"targets={payload['n_ok']}/{payload['n_targets']} all_ok={payload['all_ok']}")
    print(f"yaml written to {Path(str(payload['autoform_targets_yaml'])).resolve()}")
    print(f"book dir written to {Path(str(payload['autoform_book_dir'])).resolve()}")
    for command in payload["command_templates"]:
        print(f"  {command}")
    for error in payload["errors"]:
        print(f"  error: {error}")
    return 0 if payload["all_ok"] else 1


def _autoform_harness_audit(args: argparse.Namespace) -> int:
    payload = audit_autoform_harness(Path(args.out))
    profile = payload["profile"]
    print("\nAI Statistical Theory Lab Autoform Harness Audit")
    print("=" * 72)
    print(
        f"ready={payload['ready_for_integration']} "
        f"root={profile['root']} commit={str(profile['git_commit'])[:12]}"
    )
    for key in (
        "has_statement_extraction",
        "has_lean_eval",
        "has_dependency_graph_eval",
        "has_lean_proof_checker",
        "has_lean_repl_tool",
        "has_native_lsp_tool",
        "has_lean_skill_docs",
        "has_multi_agent_bot",
        "has_visualizer",
    ):
        print(f"  {key}: {profile[key]}")
    print(f"\nautoform harness manifest written to {(Path(args.out) / 'autoform_harness_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'autoform_harness.md').resolve()}")
    return 0 if payload["ready_for_integration"] else 1


def _proof_bank_expansion_export(args: argparse.Namespace) -> int:
    payload = export_proof_bank_expansion_candidates(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Proof-Bank Expansion Candidates")
    print("=" * 72)
    print(
        f"candidates={payload['n_ok']}/{payload['n_candidates']} "
        f"bridge_ready={payload['n_bridge_ready']} "
        f"exact_reuse={payload['n_reuse_exact_proof_bank_obligation']} "
        f"blocked_placeholder={payload['n_blocked_placeholder']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["candidates"][:10]:
        print(
            f"  {row['status']:22} score={row['priority_score']:4} "
            f"{row['primitive']} tasks={len(row['source_task_ids'])}"
        )
    print(
        f"\nproof-bank expansion manifest written to "
        f"{(Path(args.out) / 'proof_bank_expansion_manifest.json').resolve()}"
    )
    print(f"lemma proposals JSONL written to {(Path(args.out) / 'lemma_proposals.jsonl').resolve()}")
    print(
        f"theorem-hole queue written to "
        f"{(Path(args.out) / 'theorem_hole_promotion_queue_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _proof_bank_action_export(args: argparse.Namespace) -> int:
    payload = export_proof_bank_actions(Path(args.proof_bank_expansion_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Proof-Bank Actions")
    print("=" * 72)
    print(
        f"actions={payload['n_ok']}/{payload['n_actions']} "
        f"expansion_candidates={payload['expansion_candidates']} all_ok={payload['all_ok']}"
    )
    for action_class, count in payload["by_action_class"].items():
        print(f"  {action_class}: {count}")
    print(
        f"\nproof-bank action manifest written to "
        f"{(Path(args.out) / 'proof_bank_action_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'proof_bank_actions.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'proof_bank_actions.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _assumption_interface_export(args: argparse.Namespace) -> int:
    payload = export_assumption_interfaces(
        Path(args.proof_bank_actions_dir),
        Path(args.out),
        lean_project=args.lean_project,
        lean_timeout=args.lean_timeout,
    )
    print("\nAI Statistical Theory Lab Assumption Interfaces")
    print("=" * 72)
    print(
        f"interfaces={payload['n_ok']}/{payload['n_interfaces']} "
        f"local_lean={payload['n_local_lean_compiled']}/{payload['n_local_lean_checked']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nassumption interface manifest written to "
        f"{(Path(args.out) / 'assumption_interface_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'assumption_interfaces.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'assumption_interfaces.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formalization_delta_plan(args: argparse.Namespace) -> int:
    payload = build_formalization_delta_plan(
        Path(args.proof_bank_actions_dir),
        Path(args.out),
        primitive_source_coverage_dir=(
            Path(args.primitive_source_coverage_dir)
            if args.primitive_source_coverage_dir
            else None
        ),
        formal_gap_tasks_dir=Path(args.formal_gap_tasks_dir) if args.formal_gap_tasks_dir else None,
    )
    print("\nAI Statistical Theory Lab Formalization Delta Plan")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_plan_rows']} "
        f"cost={payload['total_estimated_cost']} "
        f"graph={payload['dependency_graph_nodes']}n/{payload['dependency_graph_edges']}e "
        f"low={payload['n_low_cost_existing_reuse']} "
        f"medium={payload['n_medium_cost_bridge_or_wrapper']} "
        f"high={payload['n_high_cost_new_theory']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nformalization delta manifest written to "
        f"{(Path(args.out) / 'formalization_delta_plan_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'formalization_delta_plan.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'formalization_delta_plan.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formal_source_roots_from_specs(specs: list[str] | None) -> tuple[FormalSourceRoot, ...] | None:
    if not specs:
        return None
    roots: list[FormalSourceRoot] = []
    for idx, spec in enumerate(specs, start=1):
        if "=" in spec:
            root_id, location = spec.split("=", 1)
        else:
            location = spec
            root_id = f"formal_source_root_{idx}"
        roots.append(FormalSourceRoot(root_id.strip(), location.strip()))
    return tuple(roots)


def _formal_verifier_queue(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_queue(
        Path(args.formalization_delta_dir),
        Path(args.out),
        proof_search_no_registered_ablation_dir=(
            Path(args.proof_search_no_registered_ablation_dir)
            if args.proof_search_no_registered_ablation_dir
            else None
        ),
        kernel_smoke_proof_audit_dir=(
            Path(args.kernel_smoke_proof_audit_dir)
            if args.kernel_smoke_proof_audit_dir
            else None
        ),
        proof_attempt_log_path=Path(args.proof_attempt_log)
        if args.proof_attempt_log
        else None,
        proof_search_results_path=Path(args.proof_search_results)
        if args.proof_search_results
        else None,
        max_routes=args.max_routes,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_items']} "
        f"high={payload['n_high_priority']} "
        f"new_theory={payload['n_requires_new_theory']} "
        f"rag_delta={payload['no_registered_rag_candidate_delta']} "
        f"kernel_smoke={payload['kernel_smoke_kernel_verified']}/{payload['kernel_smoke_total']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nformal verifier queue manifest written to "
        f"{(Path(args.out) / 'formal_verifier_queue_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'formal_verifier_queue.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'formal_verifier_queue.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _goal_conditioned_minimal_formalization_plan(args: argparse.Namespace) -> int:
    payload = export_goal_conditioned_minimal_formalization_plan(
        Path(args.formalization_delta_plan_dir),
        Path(args.formal_verifier_queue_dir),
        Path(args.out),
        max_routes=args.max_routes,
    )
    print("\nAI Statistical Theory Lab Goal-Conditioned Minimal Formalization Plan")
    print("=" * 72)
    print(
        f"plans={payload['n_ok']}/{payload['n_goal_plans']} "
        f"low_cost={payload['n_low_cost_goal_plans']} "
        f"reuse={payload['n_existing_reuse_nodes']} "
        f"wrappers={payload['n_wrapper_nodes']} "
        f"bridges={payload['n_bridge_nodes']} "
        f"source={payload['n_source_discovery_nodes']} "
        f"first_principles={payload['n_first_principles_nodes']} "
        f"minimal_cuts={payload['n_goal_plans_with_minimal_cut']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\ngoal-conditioned minimal formalization manifest written to "
        f"{(Path(args.out) / 'goal_conditioned_minimal_formalization_plan_manifest.json').resolve()}"
    )
    print(
        f"jsonl written to "
        f"{(Path(args.out) / 'goal_conditioned_minimal_formalization_plan.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'goal_conditioned_minimal_formalization_plan.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_target_intake(args: argparse.Namespace) -> int:
    payload = normalize_formalization_gap_planner_target_intake(
        Path(args.input),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Target Intake")
    print("=" * 72)
    print(
        f"targets={payload['n_ok']}/{payload['n_targets']} "
        f"primitive_seeds={payload['n_primitive_seed_rows']} "
        f"literature_queries={payload['n_literature_queries']} "
        f"formal_library_queries={payload['n_formal_library_grounding_queries']} "
        f"missing_sources={payload['n_missing_proof_sources']} "
        f"missing_skeletons={payload['n_missing_theorem_skeleton']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\ntarget-intake manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_target_intake_manifest.json').resolve()}"
    )
    print(
        f"standalone seed written to "
        f"{(Path(args.out) / 'formalization_gap_planner_target_intake_standalone_seed.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_standalone_plan(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_standalone_plan(
        Path(args.input),
        Path(args.out),
        max_routes=args.max_routes,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Standalone Plan")
    print("=" * 72)
    print(
        f"plans={payload['n_ok']}/{payload['n_goal_plans']} "
        f"target={payload['target_prover_family']} "
        f"reuse={payload['n_existing_reuse_nodes']} "
        f"wrappers={payload['n_wrapper_nodes']} "
        f"bridges={payload['n_bridge_nodes']} "
        f"source={payload['n_source_discovery_nodes']} "
        f"first_principles={payload['n_first_principles_nodes']} "
        f"packets={payload['n_portable_work_packets']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nstandalone gap-plan manifest written to "
        f"{(Path(args.out) / 'goal_conditioned_minimal_formalization_plan_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_llm_route_planner(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_llm_route_planner(
        Path(args.input),
        Path(args.out),
        provider_name=args.provider,
        model=args.model,
        model_tier=args.model_tier,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        max_repair_attempts=args.max_repair_attempts,
        invoke_provider=args.invoke_provider,
        response_json=Path(args.response_json) if args.response_json else None,
        static_response_json=(
            Path(args.static_response_file) if args.static_response_file else None
        ),
        formalization_gap_planner_target_intake_dir=(
            Path(args.formalization_gap_planner_target_intake_dir)
            if args.formalization_gap_planner_target_intake_dir
            else None
        ),
        goal_conditioned_minimal_formalization_plan_dir=(
            Path(args.goal_conditioned_minimal_formalization_plan_dir)
            if args.goal_conditioned_minimal_formalization_plan_dir
            else None
        ),
        formalization_gap_planner_library_coverage_map_dir=(
            Path(args.formalization_gap_planner_library_coverage_map_dir)
            if args.formalization_gap_planner_library_coverage_map_dir
            else None
        ),
        formalization_gap_planner_source_grounding_audit_dir=(
            Path(args.formalization_gap_planner_source_grounding_audit_dir)
            if args.formalization_gap_planner_source_grounding_audit_dir
            else None
        ),
        formalization_gap_planner_resource_request_queue_dir=(
            Path(args.formalization_gap_planner_resource_request_queue_dir)
            if args.formalization_gap_planner_resource_request_queue_dir
            else None
        ),
        formalization_gap_planner_resource_response_ledger_dir=(
            Path(args.formalization_gap_planner_resource_response_ledger_dir)
            if args.formalization_gap_planner_resource_response_ledger_dir
            else None
        ),
        formalization_gap_planner_refinement_evidence_dir=(
            Path(args.formalization_gap_planner_refinement_evidence_dir)
            if args.formalization_gap_planner_refinement_evidence_dir
            else None
        ),
        formalization_gap_planner_route_revision_overlay_dir=(
            Path(args.formalization_gap_planner_route_revision_overlay_dir)
            if args.formalization_gap_planner_route_revision_overlay_dir
            else None
        ),
        formalization_gap_planner_route_replan_handoff_dir=(
            Path(args.formalization_gap_planner_route_replan_handoff_dir)
            if args.formalization_gap_planner_route_replan_handoff_dir
            else None
        ),
        formalization_gap_planner_interactive_session_dir=(
            Path(args.formalization_gap_planner_interactive_session_dir)
            if args.formalization_gap_planner_interactive_session_dir
            else None
        ),
        formalization_gap_planner_component_resource_registry_dir=(
            Path(args.formalization_gap_planner_component_resource_registry_dir)
            if args.formalization_gap_planner_component_resource_registry_dir
            else None
        ),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner LLM Route Planner")
    print("=" * 78)
    print(
        f"requests={payload['n_request_schema_valid']}/{payload['n_request_packets']} "
        f"responses={payload['n_response_present']} "
        f"accepted={payload['n_accepted_route_plans']} "
        f"awaiting={payload['n_awaiting_llm_response']} "
        f"search_requests={payload['n_search_requests']} "
        f"preflight_blocks={payload['n_generation_preflight_blocked']} "
        f"rejected={payload['n_rejected']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nLLM route planner manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_llm_route_planner_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_llm_route_planner_response_payload_validate(
    args: argparse.Namespace,
) -> int:
    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        Path(args.input),
        Path(args.out),
        request_context_json=(
            Path(args.request_context) if args.request_context else None
        ),
    )
    print(
        "\nAI Statistical Theory Lab Formalization Gap Planner "
        "LLM Response Payload Validator"
    )
    print("=" * 78)
    print(
        f"payloads={payload['n_valid_payloads']}/{payload['n_payloads']} "
        f"invalid={payload['n_invalid_payloads']} "
        f"request_bound={payload['n_request_bound_payloads']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nLLM response-payload validation manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_portable_plan_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_portable_plan(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Portable Plan Audit")
    print("=" * 72)
    print(
        f"checks={payload['n_ok']}/{payload['n_checks']} "
        f"failed={payload['n_failed']} "
        f"rows={payload['n_plan_rows']} "
        f"target={payload['target_prover_family']} "
        f"two_dag={payload['n_rows_with_two_dag']} "
        f"work_packets={payload['n_rows_with_work_packets']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nportable plan audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_portable_plan_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_library_coverage_map(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_library_coverage_map(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Library Coverage Map")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_coverage_rows']} "
        f"exact={payload['n_exact_exists']} "
        f"near={payload['n_near_exists']} "
        f"wrapper={payload['n_wrapper_needed']} "
        f"bridge={payload['n_bridge_needed']} "
        f"source={payload['n_source_port_needed']} "
        f"new_theory={payload['n_definition_or_theory_missing']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nlibrary coverage map manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_library_coverage_map_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_primitive_action_queue(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_primitive_action_queue(
        Path(args.formalization_gap_planner_library_coverage_map_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Primitive Action Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_action_items']} "
        f"replay={payload['n_target_prover_replay']} "
        f"compose={payload['n_compose_existing_declarations']} "
        f"wrapper={payload['n_write_wrapper']} "
        f"bridge={payload['n_prove_bridge_lemma']} "
        f"source={payload['n_source_port']} "
        f"new_theory={payload['n_design_new_theory_fragment']} "
        f"rerun={payload['n_rerun_library_alignment']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nprimitive action queue manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_primitive_action_queue_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_action_resource_plan(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_action_resource_plan(
        Path(args.formalization_gap_planner_primitive_action_queue_dir),
        Path(args.formalization_gap_planner_component_resource_registry_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Action Resource Plan")
    print("=" * 72)
    print(
        f"plans={payload['n_ok']}/{payload['n_resource_plan_rows']} "
        f"local={payload['n_with_local_first_resources']} "
        f"frontier={payload['n_with_frontier_escalation_resources']} "
        f"contracts={payload['n_with_resource_contracts']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\naction resource plan manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_action_resource_plan_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_resource_request_queue(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_resource_request_queue(
        Path(args.formalization_gap_planner_action_resource_plan_dir),
        Path(args.out),
        formalization_gap_planner_llm_route_planner_dir=(
            Path(args.formalization_gap_planner_llm_route_planner_dir)
            if args.formalization_gap_planner_llm_route_planner_dir
            else None
        ),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Resource Request Queue")
    print("=" * 72)
    print(
        f"requests={payload['n_ok']}/{payload['n_resource_request_rows']} "
        f"local={payload['n_local_first_requests']} "
        f"frontier={payload['n_frontier_escalation_requests']} "
        f"llm_rows={payload['n_llm_route_planner_resource_request_rows']} "
        f"resources={payload['n_distinct_resources']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nresource request queue manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_resource_request_queue_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_resource_response_ledger(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_resource_response_ledger(
        Path(args.formalization_gap_planner_resource_request_queue_dir),
        Path(args.out),
        response_jsonl=Path(args.response_jsonl) if args.response_jsonl else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Resource Response Ledger")
    print("=" * 76)
    print(
        f"ledger={payload['n_ok']}/{payload['n_ledger_rows']} "
        f"responses={payload['n_response_present']} "
        f"awaiting={payload['n_awaiting_response']} "
        f"contract_ok={payload['n_response_contract_ok']} "
        f"rejected={payload['n_rejected']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nresource response ledger manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_resource_response_ledger_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_minimal_delta_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_minimal_delta(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Minimal Delta Audit")
    print("=" * 72)
    print(
        f"checks={payload['n_ok']}/{payload['n_checks']} "
        f"failed={payload['n_failed']} "
        f"rows={payload['n_plan_rows']} "
        f"cost_formula={payload['n_rows_with_cost_formula_ok']} "
        f"work_packets={payload['n_rows_with_work_packet_cut_ok']} "
        f"dominated={payload['n_dominated_route_witnesses']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nminimal delta audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_minimal_delta_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_source_grounding_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_source_grounding(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.out),
        formalization_gap_planner_refinement_evidence_dir=Path(
            args.formalization_gap_planner_refinement_evidence_dir
        )
        if args.formalization_gap_planner_refinement_evidence_dir
        else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Source Grounding Audit")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_source_grounding_rows']} "
        f"source={payload['n_source_backed']} "
        f"pending={payload['n_source_search_pending']} "
        f"boundary={payload['n_formal_boundary_declared']} "
        f"unaccounted={payload['n_unaccounted']} "
        f"residual={payload['n_residual_grounding_rows']} "
        f"residual_unaccounted={payload['n_residual_unaccounted']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nsource grounding audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_source_grounding_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_benchmark(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_benchmark(
        Path(args.out),
        ground_truth_path=Path(args.ground_truth) if args.ground_truth else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Benchmark")
    print("=" * 72)
    print(
        f"routes={payload['n_ok']}/{payload['n_routes']} "
        f"required={payload['n_required_primitives']} "
        f"delta={payload['n_actual_delta_primitives']} "
        f"reuse={payload['n_existing_reuse_primitives']} "
        f"kernel_truth={payload['n_kernel_verified_routes']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nbenchmark manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_benchmark_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_benchmark_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_benchmark(
        Path(args.formalization_gap_planner_benchmark_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Benchmark Audit")
    print("=" * 72)
    print(
        f"checks={payload['n_ok']}/{payload['n_checks']} "
        f"failed={payload['n_failed']} "
        f"routes={payload['n_routes']} "
        f"families={payload['n_theorem_families']} "
        f"splits={payload['n_evaluation_splits']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nbenchmark audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_benchmark_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_ablation_study(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_ablation_study(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.formalization_gap_planner_evaluation_dir),
        Path(args.out),
        formalization_gap_planner_interactive_session_dir=Path(
            args.formalization_gap_planner_interactive_session_dir
        )
        if args.formalization_gap_planner_interactive_session_dir
        else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Ablation Study")
    print("=" * 72)
    print(
        f"variants={payload['n_ok']}/{payload['n_ablation_variants']} "
        f"routes={payload['n_evaluation_rows']} "
        f"best={payload['best_variant_by_route_recall']} "
        f"largest_route_drop={payload['largest_route_recall_drop_variant']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nablation study manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_ablation_study_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_interactive_session(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_interactive_session(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.out),
        formalization_gap_planner_refinement_queue_dir=Path(
            args.formalization_gap_planner_refinement_queue_dir
        )
        if args.formalization_gap_planner_refinement_queue_dir
        else None,
        formalization_gap_planner_refinement_evidence_dir=Path(
            args.formalization_gap_planner_refinement_evidence_dir
        )
        if args.formalization_gap_planner_refinement_evidence_dir
        else None,
        formalization_gap_planner_route_stability_audit_dir=Path(
            args.formalization_gap_planner_route_stability_audit_dir
        )
        if args.formalization_gap_planner_route_stability_audit_dir
        else None,
        formalization_gap_planner_route_replan_handoff_dir=Path(
            args.formalization_gap_planner_route_replan_handoff_dir
        )
        if args.formalization_gap_planner_route_replan_handoff_dir
        else None,
        formalization_gap_planner_proof_state_triage_dir=Path(
            args.formalization_gap_planner_proof_state_triage_dir
        )
        if args.formalization_gap_planner_proof_state_triage_dir
        else None,
        formalization_gap_planner_component_resource_registry_dir=Path(
            args.formalization_gap_planner_component_resource_registry_dir
        )
        if args.formalization_gap_planner_component_resource_registry_dir
        else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Interactive Session")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_session_rows']} "
        f"literature={payload['n_run_literature_search']} "
        f"lean={payload['n_run_lean_grounding']} "
        f"proof_state={payload['n_run_proof_state_feedback']} "
        f"replan={payload['n_run_route_replan']} "
        f"replay={payload['n_run_target_prover_replay']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\ninteractive session manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_interactive_session_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_adapter_registry(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_adapter_registry(
        Path(args.out),
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
        paper_library_dir=Path(args.paper_library_dir) if args.paper_library_dir else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Adapter Registry")
    print("=" * 72)
    print(
        f"adapters={payload['n_ok']}/{payload['n_adapters']} "
        f"ready={payload['n_ready_local_or_configured']} "
        f"contract_only={payload['n_contract_only']} "
        f"needs_install={payload['n_needs_install']} "
        f"needs_credentials={payload['n_needs_credentials']} "
        f"needs_config={payload['n_needs_configuration']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nadapter registry manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_adapter_registry_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_adapter_registry_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_adapter_registry(
        Path(args.formalization_gap_planner_adapter_registry_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Adapter Registry Audit")
    print("=" * 72)
    print(
        f"checks={payload['n_ok']}/{payload['n_checks']} "
        f"failed={payload['n_failed']} "
        f"adapters={payload['n_registry_rows']} "
        f"required={payload['n_required_adapter_ids_present']}/{payload['n_required_adapter_ids']} "
        f"ready={payload['n_ready_local_or_configured']} "
        f"mcp_cli={payload['n_mcp_or_cli_surfaces']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nadapter registry audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_adapter_registry_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_component_resource_registry(
    args: argparse.Namespace,
) -> int:
    payload = export_formalization_gap_planner_component_resource_registry(
        Path(args.out),
        formalization_gap_planner_adapter_registry_dir=Path(
            args.formalization_gap_planner_adapter_registry_dir
        )
        if args.formalization_gap_planner_adapter_registry_dir
        else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Component Resource Registry")
    print("=" * 72)
    print(
        f"components={payload['n_component_rows_ok']}/{payload['n_component_rows']} "
        f"resources={payload['n_resource_rows_ok']}/{payload['n_resources']} "
        f"frontier={payload['n_frontier_resources']} "
        f"mcp_cli={payload['n_mcp_or_cli_resources']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\ncomponent resource registry manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_component_resource_registry_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_component_resource_registry_audit(
    args: argparse.Namespace,
) -> int:
    payload = audit_formalization_gap_planner_component_resource_registry(
        Path(args.formalization_gap_planner_component_resource_registry_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Component Resource Registry Audit")
    print("=" * 72)
    print(
        f"checks={payload['n_ok']}/{payload['n_checks']} "
        f"failed={payload['n_failed']} "
        f"components={payload['n_required_component_ids_present']}/{payload['n_required_component_ids']} "
        f"resources={payload['n_required_resource_ids_present']}/{payload['n_required_resource_ids']} "
        f"frontier={payload['n_frontier_resources']} "
        f"mcp_cli={payload['n_mcp_or_cli_resources']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\ncomponent resource registry audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_component_resource_registry_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_evaluation(args: argparse.Namespace) -> int:
    payload = evaluate_formalization_gap_planner(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.ground_truth),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Evaluation")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_evaluation_rows']} "
        f"matched={payload['n_matched_ground_truth']} "
        f"route_recall={payload['mean_route_recall']:.3f} "
        f"delta_recall={payload['mean_delta_recall']:.3f} "
        f"coverage_acc={payload['mean_coverage_classification_accuracy']:.3f} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nevaluation manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_evaluation_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_refinement_queue(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_refinement_queue(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.out),
        formalization_gap_planner_evaluation_dir=(
            Path(args.formalization_gap_planner_evaluation_dir)
            if args.formalization_gap_planner_evaluation_dir
            else None
        ),
        formal_verifier_replay_calibration_dir=(
            Path(args.formal_verifier_replay_calibration_dir)
            if args.formal_verifier_replay_calibration_dir
            else None
        ),
        max_items=args.max_items,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Refinement Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_refinement_items']} "
        f"literature={payload['n_literature_discovery_items']} "
        f"formal={payload.get('n_formal_library_grounding_items', payload['n_lean_library_grounding_items'])} "
        f"lean_legacy={payload['n_lean_library_grounding_items']} "
        f"prover={payload['n_proof_state_feedback_items']} "
        f"revision={payload['n_route_revision_items']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nrefinement queue manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_refinement_queue_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_refinement_adapter_responses(
    args: argparse.Namespace,
) -> int:
    payload = export_formalization_gap_planner_refinement_adapter_responses(
        Path(args.formalization_gap_planner_refinement_queue_dir),
        Path(args.out),
        ground_truth_path=Path(args.ground_truth) if args.ground_truth else None,
        max_items=args.max_items,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Refinement Adapter")
    print("=" * 72)
    print(
        f"responses={payload['n_responses']}/{payload['n_queue_rows']} "
        f"matched={payload['n_ground_truth_matched']} "
        f"literature={payload['n_literature_responses']} "
        f"formal={payload.get('n_formal_grounding_responses', payload['n_lean_grounding_responses'])} "
        f"lean_legacy={payload['n_lean_grounding_responses']} "
        f"prover={payload['n_prover_feedback_responses']} "
        f"revision={payload['n_route_revision_responses']} "
        f"revision_recommended={payload['n_route_revision_recommended']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nadapter manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_refinement_adapter_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_local_literature_adapter(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_local_literature_adapter_responses(
        Path(args.formalization_gap_planner_refinement_queue_dir),
        Path(args.out),
        literature_roots=tuple(Path(root) for root in (args.literature_root or [])),
        base_response_jsonl=Path(args.base_response_jsonl)
        if args.base_response_jsonl
        else None,
        max_items=args.max_items,
        k=args.k,
        max_file_bytes=args.max_file_bytes,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Local Literature Adapter")
    print("=" * 72)
    print(
        f"responses={payload['n_local_literature_responses']}/"
        f"{payload['n_literature_discovery_rows']} "
        f"merged={payload['n_merged_responses']} "
        f"docs={payload['n_documents_indexed']} "
        f"hits={payload['n_source_hits']} "
        f"gaps={payload['n_literature_gap_responses']} "
        f"revision={payload['n_route_revision_recommended']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nlocal literature adapter manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_local_literature_adapter_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_local_formal_source_adapter(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_local_formal_source_adapter_responses(
        Path(args.formalization_gap_planner_refinement_queue_dir),
        Path(args.out),
        formal_source_roots=_formal_source_roots_from_specs(args.formal_source_root),
        formal_source_index_db=Path(args.formal_source_index_db)
        if args.formal_source_index_db
        else None,
        formal_source_index_cache=Path(args.formal_source_index_cache)
        if args.formal_source_index_cache
        else None,
        refresh_formal_source_index_cache=args.refresh_formal_source_index_cache,
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
        base_response_jsonl=Path(args.base_response_jsonl)
        if args.base_response_jsonl
        else None,
        max_items=args.max_items,
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Local Formal Source Adapter")
    print("=" * 72)
    print(
        f"responses={payload['n_local_formal_source_responses']}/"
        f"{payload.get('n_formal_library_grounding_rows', payload['n_lean_library_grounding_rows'])} "
        f"lean_legacy={payload['n_lean_library_grounding_rows']} "
        f"merged={payload['n_merged_responses']} "
        f"hits={payload['n_hits']} "
        f"exact={payload['n_exact_exists']} "
        f"wrapper={payload['n_wrapper_needed']} "
        f"source={payload['n_source_discovery_needed']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nlocal formal-source adapter manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_local_formal_source_adapter_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_local_proof_state_adapter(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_local_proof_state_adapter_responses(
        Path(args.formalization_gap_planner_refinement_queue_dir),
        Path(args.out),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=args.lean_timeout,
        base_response_jsonl=Path(args.base_response_jsonl)
        if args.base_response_jsonl
        else None,
        max_items=args.max_items,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Local Proof-State Adapter")
    print("=" * 72)
    print(
        f"responses={payload['n_local_proof_state_responses']}/"
        f"{payload['n_proof_state_feedback_rows']} "
        f"merged={payload['n_merged_responses']} "
        f"accepted={payload['n_kernel_scaffold_accepted']} "
        f"failed={payload['n_local_lean_failed']} "
        f"unavailable={payload['n_local_lean_unavailable']} "
        f"placeholder={payload['n_placeholder_blocked']} "
        f"formal_gap={payload['n_formal_gap_scaffold_blocked']} "
        f"nonlean={payload['n_non_lean_skeleton']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nlocal proof-state adapter manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_local_proof_state_adapter_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_prover_adapter_feedback(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_prover_adapter_feedback_responses(
        Path(args.formalization_gap_planner_refinement_queue_dir),
        Path(args.out),
        formalization_gap_planner_prover_adapter_contract_dir=(
            Path(args.formalization_gap_planner_prover_adapter_contract_dir)
            if args.formalization_gap_planner_prover_adapter_contract_dir
            else None
        ),
        formalization_gap_planner_cross_prover_matrix_audit_dir=(
            Path(args.formalization_gap_planner_cross_prover_matrix_audit_dir)
            if args.formalization_gap_planner_cross_prover_matrix_audit_dir
            else None
        ),
        base_response_jsonl=Path(args.base_response_jsonl)
        if args.base_response_jsonl
        else None,
        target_prover_family=args.target_prover_family,
        max_items=args.max_items,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Prover-Adapter Feedback")
    print("=" * 78)
    print(
        f"responses={payload['n_generated_feedback_responses']}/"
        f"{payload['n_proof_state_feedback_rows']} "
        f"validation={payload['n_validation_rows']} "
        f"matched={payload['n_matched_proof_state_feedback_rows']} "
        f"unmatched={payload['n_unmatched_proof_state_feedback_rows']} "
        f"merged={payload['n_merged_responses']} "
        f"revision={payload['n_route_revision_recommended']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nprover-adapter feedback manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_prover_adapter_feedback_adapter_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_minimal_delta_audit_feedback(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_minimal_delta_audit_feedback_responses(
        Path(args.formalization_gap_planner_refinement_queue_dir),
        Path(args.formalization_gap_planner_minimal_delta_audit_dir),
        Path(args.out),
        base_response_jsonl=Path(args.base_response_jsonl)
        if args.base_response_jsonl
        else None,
        max_items=args.max_items,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Minimal-Delta Audit Feedback")
    print("=" * 86)
    print(
        f"responses={payload['n_generated_feedback_responses']}/"
        f"{payload['n_route_revision_rows']} "
        f"failed_decisions={payload['n_failed_minimal_delta_decision_rows']} "
        f"matched={payload['n_matched_route_revision_rows']} "
        f"unmatched={payload['n_unmatched_route_revision_rows']} "
        f"merged={payload['n_merged_responses']} "
        f"revision={payload['n_route_revision_recommended']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nminimal-delta audit feedback manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_minimal_delta_audit_feedback_adapter_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_refinement_evidence(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_refinement_evidence(
        Path(args.formalization_gap_planner_refinement_queue_dir),
        Path(args.out),
        response_jsonl=Path(args.response_jsonl) if args.response_jsonl else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Refinement Evidence")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_evidence_rows']} "
        f"responses={payload['n_responses']} "
        f"awaiting={payload['n_awaiting_tool_response']} "
        f"contract={payload['n_contract_ok']} "
        f"revision={payload['n_route_revision_recommended']} "
        f"proposals={payload['n_route_revision_proposals']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nrefinement evidence manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_refinement_evidence_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_route_revision_overlay(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_route_revision_overlay(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.formalization_gap_planner_refinement_evidence_dir),
        Path(args.out),
        formalization_gap_planner_resource_response_ledger_dir=Path(
            args.formalization_gap_planner_resource_response_ledger_dir
        )
        if args.formalization_gap_planner_resource_response_ledger_dir
        else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Route Revision Overlay")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_overlay_rows']} "
        f"revised={payload['n_routes_with_revision']} "
        f"unrevised={payload['n_routes_without_revision']} "
        f"orphan={payload['n_orphan_route_revision_proposals']} "
        f"ledger_proposals={payload['n_resource_response_ledger_route_revision_proposals']} "
        f"added={payload['n_added_primitives']} "
        f"delta_added={payload['n_added_delta_primitives']} "
        f"prover_status_routes={payload['n_routes_with_prover_attempt_status']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nroute revision overlay manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_route_revision_overlay_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_route_stability_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_route_stability(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.formalization_gap_planner_refinement_evidence_dir),
        Path(args.formalization_gap_planner_route_revision_overlay_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Route Stability Audit")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_stability_rows']} "
        f"stable={payload['n_stable']} "
        f"needs_expansion={payload['n_needs_expansion']} "
        f"awaiting={payload['n_awaiting_responses']} "
        f"replan={payload['n_apply_route_revision']} "
        f"literature={payload['n_expand_literature']} "
        f"lean={payload['n_expand_lean_grounding']} "
        f"proof_state={payload['n_expand_proof_state']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nroute stability audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_route_stability_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_route_replan_handoff(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_route_replan_handoff(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.formalization_gap_planner_route_revision_overlay_dir),
        Path(args.out),
        formalization_gap_planner_route_stability_audit_dir=Path(
            args.formalization_gap_planner_route_stability_audit_dir
        )
        if args.formalization_gap_planner_route_stability_audit_dir
        else None,
        target_prover_family=args.target_prover_family,
        library_snapshot_ref=args.library_snapshot_ref,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Route-Replan Handoff")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_handoff_rows']} "
        f"replan={payload['n_routes_requiring_replan']} "
        f"seed_routes={payload['n_standalone_seed_routes']} "
        f"residual_routes={payload['n_routes_with_residual_goals']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nroute-replan handoff manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_route_replan_handoff_manifest.json').resolve()}"
    )
    print(
        f"standalone replan seed written to "
        f"{(Path(args.out) / 'formalization_gap_planner_route_replan_standalone_seed.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_route_replan_handoff_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_route_replan_handoff(
        Path(args.formalization_gap_planner_route_replan_handoff_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Route-Replan Handoff Audit")
    print("=" * 72)
    print(
        f"checks={payload['n_ok']}/{payload['n_checks']} "
        f"failed={payload['n_failed']} "
        f"rows={payload['n_handoff_rows']} "
        f"seed_routes={payload['n_seed_routes']} "
        f"roundtrip={payload['n_roundtrip_goal_plans']} "
        f"roundtrip_ok={payload['roundtrip_all_ok']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nroute-replan handoff audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_route_replan_handoff_audit_manifest.json').resolve()}"
    )
    print(
        f"roundtrip planner manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_route_replan_roundtrip_plan' / 'goal_conditioned_minimal_formalization_plan_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_runtime_handoff_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_runtime_handoffs(
        Path(args.runtime_formalization_gap_planner_handoffs_jsonl),
        Path(args.out),
        run_smoke=not args.no_smoke,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Runtime Handoff Audit")
    print("=" * 72)
    print(
        f"handoffs={payload['n_handoffs']} "
        f"checks={payload['n_ok']}/{payload['n_checks']} "
        f"failed={payload['n_failed']} "
        f"cost_control={payload['n_cost_control_ok']} "
        f"standalone_smoke={payload['n_standalone_smoke_ok']} "
        f"llm_prompt_smoke={payload['n_llm_prompt_smoke_ok']} "
        f"prompt_packets={payload['n_llm_prompt_packets']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nruntime handoff audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_runtime_handoff_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_proof_state_triage(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_proof_state_triage(
        Path(args.formalization_gap_planner_route_revision_overlay_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Proof-State Triage")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_triage_items']} "
        f"formal_gap={payload['n_formal_gap_scaffold_items']} "
        f"local_failed={payload['n_local_lean_failed_items']} "
        f"nonlean={payload['n_non_lean_skeleton_items']} "
        f"signatures={payload['n_distinct_diagnostic_signatures']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nproof-state triage manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_proof_state_triage_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_publication_bundle(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_publication_bundle(
        Path(args.out),
        ground_truth_path=Path(args.ground_truth) if args.ground_truth else None,
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
        paper_library_dir=Path(args.paper_library_dir)
        if args.paper_library_dir
        else None,
        formalization_gap_planner_target_intake_dir=Path(
            args.formalization_gap_planner_target_intake_dir
        )
        if args.formalization_gap_planner_target_intake_dir
        else None,
        formalization_gap_planner_llm_route_planner_dir=Path(
            args.formalization_gap_planner_llm_route_planner_dir
        )
        if args.formalization_gap_planner_llm_route_planner_dir
        else None,
        formalization_gap_planner_feedback_llm_route_planner_dir=Path(
            args.formalization_gap_planner_feedback_llm_route_planner_dir
        )
        if args.formalization_gap_planner_feedback_llm_route_planner_dir
        else None,
        formalization_gap_planner_llm_route_planner_response_payload_validation_dir=Path(
            args.formalization_gap_planner_llm_route_planner_response_payload_validation_dir
        )
        if args.formalization_gap_planner_llm_route_planner_response_payload_validation_dir
        else None,
        goal_conditioned_minimal_formalization_plan_dir=Path(
            args.goal_conditioned_minimal_formalization_plan_dir
        )
        if args.goal_conditioned_minimal_formalization_plan_dir
        else None,
        formalization_gap_planner_evaluation_dir=Path(
            args.formalization_gap_planner_evaluation_dir
        )
        if args.formalization_gap_planner_evaluation_dir
        else None,
        formalization_gap_planner_ablation_study_dir=Path(
            args.formalization_gap_planner_ablation_study_dir
        )
        if args.formalization_gap_planner_ablation_study_dir
        else None,
        formalization_gap_planner_portable_plan_audit_dir=Path(
            args.formalization_gap_planner_portable_plan_audit_dir
        )
        if args.formalization_gap_planner_portable_plan_audit_dir
        else None,
        formalization_gap_planner_library_coverage_map_dir=Path(
            args.formalization_gap_planner_library_coverage_map_dir
        )
        if args.formalization_gap_planner_library_coverage_map_dir
        else None,
        formalization_gap_planner_primitive_action_queue_dir=Path(
            args.formalization_gap_planner_primitive_action_queue_dir
        )
        if args.formalization_gap_planner_primitive_action_queue_dir
        else None,
        formalization_gap_planner_action_resource_plan_dir=Path(
            args.formalization_gap_planner_action_resource_plan_dir
        )
        if args.formalization_gap_planner_action_resource_plan_dir
        else None,
        formalization_gap_planner_resource_request_queue_dir=Path(
            args.formalization_gap_planner_resource_request_queue_dir
        )
        if args.formalization_gap_planner_resource_request_queue_dir
        else None,
        formalization_gap_planner_resource_response_ledger_dir=Path(
            args.formalization_gap_planner_resource_response_ledger_dir
        )
        if args.formalization_gap_planner_resource_response_ledger_dir
        else None,
        formalization_gap_planner_minimal_delta_audit_dir=Path(
            args.formalization_gap_planner_minimal_delta_audit_dir
        )
        if args.formalization_gap_planner_minimal_delta_audit_dir
        else None,
        formalization_gap_planner_minimal_delta_audit_feedback_adapter_dir=Path(
            args.formalization_gap_planner_minimal_delta_audit_feedback_adapter_dir
        )
        if args.formalization_gap_planner_minimal_delta_audit_feedback_adapter_dir
        else None,
        formalization_gap_planner_source_grounding_audit_dir=Path(
            args.formalization_gap_planner_source_grounding_audit_dir
        )
        if args.formalization_gap_planner_source_grounding_audit_dir
        else None,
        formalization_gap_planner_refinement_queue_dir=Path(
            args.formalization_gap_planner_refinement_queue_dir
        )
        if args.formalization_gap_planner_refinement_queue_dir
        else None,
        formalization_gap_planner_refinement_adapter_dir=Path(
            args.formalization_gap_planner_refinement_adapter_dir
        )
        if args.formalization_gap_planner_refinement_adapter_dir
        else None,
        formalization_gap_planner_local_literature_adapter_dir=Path(
            args.formalization_gap_planner_local_literature_adapter_dir
        )
        if args.formalization_gap_planner_local_literature_adapter_dir
        else None,
        formalization_gap_planner_local_formal_source_adapter_dir=Path(
            args.formalization_gap_planner_local_formal_source_adapter_dir
        )
        if args.formalization_gap_planner_local_formal_source_adapter_dir
        else None,
        formalization_gap_planner_local_proof_state_adapter_dir=Path(
            args.formalization_gap_planner_local_proof_state_adapter_dir
        )
        if args.formalization_gap_planner_local_proof_state_adapter_dir
        else None,
        formalization_gap_planner_prover_adapter_feedback_adapter_dir=Path(
            args.formalization_gap_planner_prover_adapter_feedback_adapter_dir
        )
        if args.formalization_gap_planner_prover_adapter_feedback_adapter_dir
        else None,
        formalization_gap_planner_refinement_evidence_dir=Path(
            args.formalization_gap_planner_refinement_evidence_dir
        )
        if args.formalization_gap_planner_refinement_evidence_dir
        else None,
        formalization_gap_planner_route_revision_overlay_dir=Path(
            args.formalization_gap_planner_route_revision_overlay_dir
        )
        if args.formalization_gap_planner_route_revision_overlay_dir
        else None,
        formalization_gap_planner_route_stability_audit_dir=Path(
            args.formalization_gap_planner_route_stability_audit_dir
        )
        if args.formalization_gap_planner_route_stability_audit_dir
        else None,
        formalization_gap_planner_route_replan_handoff_dir=Path(
            args.formalization_gap_planner_route_replan_handoff_dir
        )
        if args.formalization_gap_planner_route_replan_handoff_dir
        else None,
        formalization_gap_planner_route_replan_handoff_audit_dir=Path(
            args.formalization_gap_planner_route_replan_handoff_audit_dir
        )
        if args.formalization_gap_planner_route_replan_handoff_audit_dir
        else None,
        formalization_gap_planner_runtime_handoff_audit_dir=Path(
            args.formalization_gap_planner_runtime_handoff_audit_dir
        )
        if args.formalization_gap_planner_runtime_handoff_audit_dir
        else None,
        formalization_gap_planner_proof_state_triage_dir=Path(
            args.formalization_gap_planner_proof_state_triage_dir
        )
        if args.formalization_gap_planner_proof_state_triage_dir
        else None,
        formalization_gap_planner_interactive_session_dir=Path(
            args.formalization_gap_planner_interactive_session_dir
        )
        if args.formalization_gap_planner_interactive_session_dir
        else None,
        formalization_gap_planner_prover_adapter_contract_dir=Path(
            args.formalization_gap_planner_prover_adapter_contract_dir
        )
        if args.formalization_gap_planner_prover_adapter_contract_dir
        else None,
        formalization_gap_planner_cross_prover_matrix_audit_dir=Path(
            args.formalization_gap_planner_cross_prover_matrix_audit_dir
        )
        if args.formalization_gap_planner_cross_prover_matrix_audit_dir
        else None,
        formalization_gap_planner_adapter_registry_audit_dir=Path(
            args.formalization_gap_planner_adapter_registry_audit_dir
        )
        if args.formalization_gap_planner_adapter_registry_audit_dir
        else None,
        formalization_gap_planner_component_resource_registry_audit_dir=Path(
            args.formalization_gap_planner_component_resource_registry_audit_dir
        )
        if args.formalization_gap_planner_component_resource_registry_audit_dir
        else None,
        library_snapshot_ref=args.library_snapshot_ref,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Publication Bundle")
    print("=" * 72)
    print(
        f"bundle={payload['bundle_id']} "
        f"core={payload['n_core_artifacts_ok']}/{payload['n_core_artifacts']} "
        f"optional_files={payload['n_optional_artifact_files_copied']} "
        f"adapters={payload['adapter_registry_summary']['n_adapters']} "
        f"routes={payload['benchmark_summary']['n_routes']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\npublication bundle manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_publication_bundle_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_prover_adapter_contract(args: argparse.Namespace) -> int:
    payload = export_formalization_gap_planner_prover_adapter_contract(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.out),
        target_prover_family=args.target_prover_family,
        library_snapshot_ref=args.library_snapshot_ref,
        adapter_response_jsonl=Path(args.adapter_response_jsonl)
        if args.adapter_response_jsonl
        else None,
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Prover Adapter Contract")
    print("=" * 72)
    print(
        f"target={payload['target_prover_family']} "
        f"packets={payload['n_packet_ok']}/{payload['n_packets']} "
        f"responses={payload['n_response_present']}/{payload['n_packets']} "
        f"contract={payload['n_response_contract_ok']} "
        f"awaiting={payload['n_awaiting_adapter_mapping']} "
        f"rejected={payload['n_rejected']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nprover adapter contract manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_prover_adapter_contract_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_cross_prover_matrix_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_cross_prover_matrix(
        Path(args.goal_conditioned_minimal_formalization_plan_dir),
        Path(args.out),
        target_prover_families=tuple(
            args.target_prover_family or FORMALIZATION_GAP_PLANNER_REUSE_TARGETS
        ),
        library_snapshot_ref_prefix=args.library_snapshot_ref_prefix,
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Cross-Prover Matrix")
    print("=" * 72)
    print(
        f"targets={payload['n_targets_ok']}/{payload['n_targets']} "
        f"packets={payload['n_total_packet_ok']}/{payload['n_total_packets']} "
        f"awaiting={payload['n_awaiting_adapter_mapping']} "
        f"rejected={payload['n_rejected']} "
        f"consistent={payload['packet_count_consistent']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\ncross-prover matrix manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_cross_prover_matrix_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_publication_bundle_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_gap_planner_publication_bundle(
        Path(args.publication_bundle_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Publication Bundle Audit")
    print("=" * 72)
    print(
        f"checks={payload['n_ok']}/{payload['n_checks']} "
        f"failed={payload['n_failed']} "
        f"files={payload['n_bundle_files']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\npublication bundle audit manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_publication_bundle_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formalization_gap_planner_reuse_smoke(args: argparse.Namespace) -> int:
    payload = run_formalization_gap_planner_reuse_smoke(
        Path(args.input),
        Path(args.out),
        target_prover_family=args.target_prover_family,
        target_library_snapshot_ref=args.target_library_snapshot_ref,
        max_routes=args.max_routes,
        ground_truth_path=Path(args.ground_truth) if args.ground_truth else None,
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
        paper_library_dir=Path(args.paper_library_dir)
        if args.paper_library_dir
        else None,
        llm_route_planner_provider=args.llm_route_planner_provider,
        llm_route_planner_model=args.llm_route_planner_model,
        llm_route_planner_model_tier=args.llm_route_planner_model_tier,
        llm_route_planner_max_tokens=args.llm_route_planner_max_tokens,
        llm_route_planner_max_repair_attempts=(
            args.llm_route_planner_max_repair_attempts
        ),
        llm_route_planner_temperature=args.llm_route_planner_temperature,
        llm_route_planner_invoke_provider=args.llm_route_planner_invoke_provider,
        llm_route_planner_response_json=(
            Path(args.llm_route_planner_response_json)
            if args.llm_route_planner_response_json
            else None
        ),
        llm_route_planner_static_response_json=(
            Path(args.llm_route_planner_static_response_file)
            if args.llm_route_planner_static_response_file
            else None
        ),
        feedback_llm_route_planner_provider=args.feedback_llm_route_planner_provider,
        feedback_llm_route_planner_model=args.feedback_llm_route_planner_model,
        feedback_llm_route_planner_model_tier=(
            args.feedback_llm_route_planner_model_tier
        ),
        feedback_llm_route_planner_max_tokens=args.feedback_llm_route_planner_max_tokens,
        feedback_llm_route_planner_max_repair_attempts=(
            args.feedback_llm_route_planner_max_repair_attempts
        ),
        feedback_llm_route_planner_temperature=args.feedback_llm_route_planner_temperature,
        feedback_llm_route_planner_invoke_provider=(
            args.feedback_llm_route_planner_invoke_provider
        ),
        feedback_llm_route_planner_response_json=(
            Path(args.feedback_llm_route_planner_response_json)
            if args.feedback_llm_route_planner_response_json
            else None
        ),
        feedback_llm_route_planner_static_response_json=(
            Path(args.feedback_llm_route_planner_static_response_file)
            if args.feedback_llm_route_planner_static_response_file
            else None
        ),
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Reuse Smoke")
    print("=" * 72)
    print(
        f"stages={payload['n_ok']}/{payload['n_stages']} "
        f"target={payload['target_prover_family']} "
        f"llm_accepted={payload['n_llm_route_planner_accepted_route_plans']} "
        f"llm_awaiting={payload['n_llm_route_planner_awaiting']} "
        f"feedback_llm_accepted={payload['n_feedback_llm_route_planner_accepted_route_plans']} "
        f"feedback_llm_awaiting={payload['n_feedback_llm_route_planner_awaiting']} "
        f"packets={payload['n_portable_work_packets']} "
        f"awaiting_adapter={payload['n_awaiting_adapter_mapping']} "
        f"registry_audit_failed={payload['n_adapter_registry_audit_failed']} "
        f"resource_audit_failed={payload['n_component_resource_audit_failed']} "
        f"minimal_failed={payload['n_minimal_delta_audit_failed']} "
        f"source_unaccounted={payload['n_source_grounding_unaccounted']} "
        f"cross_targets={payload['n_cross_prover_targets_ok']}/{payload['n_cross_prover_targets']} "
        f"handoff_audit_failed={payload['n_route_replan_handoff_audit_failed']} "
        f"handoff_roundtrip={payload['n_route_replan_roundtrip_goal_plans']} "
        f"bundle_checks={payload['n_publication_bundle_audit_checks']} "
        f"bundle_failed={payload['n_publication_bundle_audit_failed']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nreuse smoke manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_reuse_smoke_manifest.json').resolve()}"
    )
    print(
        f"publication bundle manifest written to "
        f"{(Path(args.out) / 'formalization_gap_planner_publication_bundle' / 'formalization_gap_planner_publication_bundle_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_export(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay(
        Path(args.formal_verifier_queue_dir),
        Path(args.out),
        max_tasks=args.max_tasks,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Replay")
    print("=" * 72)
    print(
        f"tasks={payload['n_ok']}/{payload['n_replay_tasks']} "
        f"kernel_calibrated={payload['n_kernel_calibrated']} "
        f"proof_search_replay={payload['n_proof_search_subclaim_replay']} "
        f"bridge_replay={payload['n_bridge_lemma_replay']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nformal verifier replay manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_manifest.json').resolve()}"
    )
    print(f"task jsonl written to {(Path(args.out) / 'formal_verifier_replay_tasks.jsonl').resolve()}")
    print(
        f"training jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_training.jsonl').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_verifier_replay.md').resolve()}")
    return 0 if payload["all_ok"] else 1


async def _formal_verifier_replay_attempts(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    payload = await export_formal_verifier_replay_attempts(
        Path(args.formal_verifier_replay_dir),
        Path(args.out),
        verifier=verifier,
        formal_gap_tasks_dir=Path(args.formal_gap_tasks_dir) if args.formal_gap_tasks_dir else None,
        max_tasks=args.max_tasks,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Replay Attempts")
    print("=" * 72)
    print(
        f"attempted={payload['n_attempted']}/{payload['n_source_replay_tasks']} "
        f"positive={payload['n_positive']} "
        f"kernel={payload['n_kernel_verified']} "
        f"failed={payload['n_negative']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nformal verifier replay attempt manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_attempt_manifest.json').resolve()}"
    )
    print(
        f"attempt jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_attempts.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_attempts.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_calibration(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_calibration(
        Path(args.formal_verifier_replay_dir),
        Path(args.out),
        attempt_log_path=Path(args.attempt_log) if args.attempt_log else None,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Replay Calibration")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_calibration_rows']} "
        f"attempted={payload['n_attempted_replay_tasks']} "
        f"awaiting={payload['n_awaiting_full_route_attempt']} "
        f"failed={payload['n_failed_full_route_attempt']} "
        f"kernel={payload['n_kernel_verified']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nformal verifier replay calibration manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_calibration_manifest.json').resolve()}"
    )
    print(
        f"calibration jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_calibration.jsonl').resolve()}"
    )
    print(
        f"repair training jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_training.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_calibration.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_export(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_packets(
        Path(args.formal_verifier_replay_dir),
        Path(args.formal_verifier_replay_attempt_dir),
        Path(args.formal_verifier_replay_calibration_dir),
        Path(args.out),
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Replay Repair")
    print("=" * 72)
    print(
        f"packets={payload['n_ok']}/{payload['n_repair_packets']} "
        f"tactic_no_progress={payload['n_tactic_no_progress']} "
        f"missing_identifier={payload['n_missing_identifier']} "
        f"exact_subclaims={payload['n_with_exact_subclaims']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nformal verifier replay repair manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_manifest.json').resolve()}"
    )
    print(
        f"repair packet jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_packets.jsonl').resolve()}"
    )
    print(
        f"repair training jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_training.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_application_export(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_application_tasks(
        Path(args.formal_verifier_replay_repair_dir),
        Path(args.formal_verifier_replay_attempt_dir),
        Path(args.out),
        max_tasks=args.max_tasks,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Replay Repair Application")
    print("=" * 72)
    print(
        f"tasks={payload['n_ok']}/{payload['n_application_tasks']} "
        f"bridge={payload['n_bridge_lemma_applications']} "
        f"import={payload['n_import_or_declaration_applications']} "
        f"statement_alignment={payload['n_statement_alignment_applications']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nformal verifier replay repair application manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_application_manifest.json').resolve()}"
    )
    print(
        f"application task jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_application_tasks.jsonl').resolve()}"
    )
    print(
        f"application training jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_application_training.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_application.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_application_validation(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_application_validation(
        Path(args.formal_verifier_replay_repair_application_dir),
        Path(args.out),
        lean_project=args.lean_project,
        lean_timeout=args.lean_timeout,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Replay Repair Application Validation")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_validation_rows']} "
        f"static_ok={payload['n_static_ok']} "
        f"local_lean={payload['n_local_lean_compiled']}/{payload['n_local_lean_checked']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nvalidation manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_application_validation_manifest.json').resolve()}"
    )
    print(
        f"validation jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_application_validation.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_application_validation.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_execution_queue(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_execution_queue(
        Path(args.formal_verifier_replay_repair_application_dir),
        Path(args.formal_verifier_replay_repair_application_validation_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Replay Repair Execution Queue")
    print("=" * 72)
    print(
        f"queue={payload['n_ok']}/{payload['n_queue_items']} "
        f"ready={payload['n_ready_for_patch']} "
        f"local_lean_ready={payload['n_ready_local_lean_compiled']} "
        f"blocked={payload['n_blocked']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nexecution queue manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_execution_queue_manifest.json').resolve()}"
    )
    print(
        f"execution queue jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_execution_queue.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_execution_queue.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_prompt_packets(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_prompt_packets(
        Path(args.formal_verifier_replay_repair_execution_queue_dir),
        Path(args.formal_verifier_replay_repair_application_dir),
        Path(args.out),
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Replay Repair Prompt Packets")
    print("=" * 72)
    print(
        f"packets={payload['n_ok']}/{payload['n_prompt_packets']} "
        f"scaffolds={payload['n_with_scaffold_source']} "
        f"commands={payload['n_with_command_plan']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nprompt packet manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_prompt_packets_manifest.json').resolve()}"
    )
    print(
        f"prompt packet jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_prompt_packets.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_prompt_packets.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_response_validation(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_patch_response_validation(
        Path(args.formal_verifier_replay_repair_prompt_packets_dir),
        Path(args.out),
        response_jsonl=Path(args.response_jsonl) if args.response_jsonl else None,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Repair Patch Response Validation")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_response_validation_rows']} "
        f"responses={payload['n_response_present']} "
        f"awaiting={payload['n_awaiting_worker_response']} "
        f"accepted={payload['n_accepted_full_route_kernel_verified']} "
        f"rejected={payload['n_rejected']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nresponse validation manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_response_validation_manifest.json').resolve()}"
    )
    print(
        f"response validation jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_response_validation.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_response_validation.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_autoworker(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_patch_autoworker(
        Path(args.formal_verifier_replay_repair_prompt_packets_dir),
        Path(args.out),
        max_responses=args.max_responses,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Repair Patch Autoworker")
    print("=" * 72)
    print(
        f"responses={payload['n_ok']}/{payload['n_responses']} "
        f"patch_proposals={payload['n_patch_proposals']} "
        f"kernel_verified={payload['n_kernel_verified']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nautoworker manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_autoworker_manifest.json').resolve()}"
    )
    print(
        f"response jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_responses.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_autoworker.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_response_promotion(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_patch_response_promotion(
        Path(args.formal_verifier_replay_repair_patch_response_validation_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Repair Patch Response Promotion")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_promotion_rows']} "
        f"ready={payload['n_ready_for_proof_promotion']} "
        f"awaiting={payload['n_awaiting_worker_response']} "
        f"patch_needs_replay={payload['n_patch_proposal_needs_replay_calibration']} "
        f"blocked={payload['n_blocked']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\npromotion manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_response_promotion_manifest.json').resolve()}"
    )
    print(
        f"promotion jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_response_promotion.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_response_promotion.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_rerun_queue(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_patch_rerun_queue(
        Path(args.formal_verifier_replay_repair_patch_response_validation_dir),
        Path(args.formal_verifier_replay_repair_patch_response_promotion_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Repair Patch Rerun Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_rerun_queue_items']} "
        f"ready={payload['n_ready_for_patch_replay']} "
        f"blocked={payload['n_blocked']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\npatch rerun manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_queue_manifest.json').resolve()}"
    )
    print(
        f"patch rerun jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_queue.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_queue.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_rerun_attempts(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_patch_rerun_attempts(
        Path(args.formal_verifier_replay_repair_patch_rerun_queue_dir),
        Path(args.out),
        lean_project=args.lean_project,
        lean_timeout=args.lean_timeout,
        max_items=args.max_items,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Repair Patch Rerun Attempts")
    print("=" * 72)
    print(
        f"attempts={payload['n_ok']}/{payload['n_rerun_attempt_rows']} "
        f"lean_checked={payload['n_local_lean_checked']} "
        f"lean_compiled={payload['n_local_lean_compiled']} "
        f"patch_markers={payload['n_with_patch_proposal_marker']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\npatch rerun attempt manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_attempt_manifest.json').resolve()}"
    )
    print(
        f"patch rerun attempt jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_attempts.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_attempts.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_rerun_calibration(args: argparse.Namespace) -> int:
    payload = export_formal_verifier_replay_repair_patch_rerun_calibration(
        Path(args.formal_verifier_replay_repair_patch_rerun_queue_dir),
        Path(args.formal_verifier_replay_repair_patch_rerun_attempt_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Repair Patch Rerun Calibration")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_calibration_rows']} "
        f"compiled={payload['n_local_lean_compiled']} "
        f"full_route_kernel={payload['n_full_route_kernel_verified']} "
        f"compiled_patch_proposals={payload['n_compiled_patch_proposal_not_proof']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\npatch rerun calibration manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_calibration_manifest.json').resolve()}"
    )
    print(
        f"patch rerun calibration jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_calibration.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_calibration.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_rerun_residual_obligations(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_replay_repair_patch_rerun_residual_obligations(
        Path(args.formal_verifier_replay_repair_patch_rerun_calibration_dir),
        Path(args.primitive_source_coverage_dir),
        Path(args.proof_bank_actions_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Patch Rerun Residual Obligations")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_residual_obligation_rows']} "
        f"routes={payload['n_routes_with_residual_obligations']} "
        f"unique_gaps={payload['n_unique_residual_gaps']} "
        f"exact_reuse={payload['n_exact_proof_bank_reuse']} "
        f"bridge_chain={payload['n_compose_existing_bridge_chain']} "
        f"source_discovery={payload['n_source_discovery_needed']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nresidual obligation manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_obligations_manifest.json').resolve()}"
    )
    print(
        f"residual obligation jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_obligations.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_obligations.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_rerun_residual_prompt_packets(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_replay_repair_patch_rerun_residual_prompt_packets(
        Path(args.formal_verifier_replay_repair_patch_rerun_residual_obligations_dir),
        Path(args.out),
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Patch Rerun Residual Prompt Packets")
    print("=" * 72)
    print(
        f"packets={payload['n_ok']}/{payload['n_prompt_packets']} "
        f"residual_rows={payload['n_residual_obligation_rows']} "
        f"artifact_context={payload['n_with_patched_artifact_context']} "
        f"exact_reuse={payload['n_exact_reuse_packets']} "
        f"bridge_chain={payload['n_bridge_chain_packets']} "
        f"source_discovery={payload['n_source_discovery_packets']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nresidual prompt packet manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest.json').resolve()}"
    )
    print(
        f"residual prompt packet jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_rerun_residual_autoworker(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_replay_repair_patch_rerun_residual_autoworker(
        Path(args.formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir),
        Path(args.out),
        max_responses=args.max_responses,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Patch Rerun Residual Autoworker")
    print("=" * 72)
    print(
        f"responses={payload['n_ok']}/{payload['n_responses']} "
        f"patch_proposals={payload['n_residual_patch_proposals']} "
        f"source_discovery={payload['n_source_discovery_responses']} "
        f"kernel_verified={payload['n_kernel_verified']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nresidual autoworker manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest.json').resolve()}"
    )
    print(
        f"residual response jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_responses.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_autoworker.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_rerun_residual_response_validation(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_replay_repair_patch_rerun_residual_response_validation(
        Path(args.formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir),
        Path(args.out),
        response_jsonl=Path(args.response_jsonl) if args.response_jsonl else None,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Patch Rerun Residual Response Validation")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_response_validation_rows']} "
        f"responses={payload['n_response_present']} "
        f"awaiting={payload['n_awaiting_worker_response']} "
        f"contract_ok={payload['n_contract_ok']} "
        f"patch_proposals={payload['n_residual_patch_proposal_not_proof']} "
        f"source_discovery={payload['n_source_discovery_responses']} "
        f"accepted={payload['n_accepted_full_route_kernel_verified']} "
        f"rejected={payload['n_rejected']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nresidual response validation manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest.json').resolve()}"
    )
    print(
        f"residual response validation jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_response_validation.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_response_validation.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_replay_repair_patch_rerun_residual_followup_queue(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_replay_repair_patch_rerun_residual_followup_queue(
        Path(
            args.formal_verifier_replay_repair_patch_rerun_residual_response_validation_dir
        ),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Patch Rerun Residual Follow-up Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_followup_items']} "
        f"ready={payload['n_ready']} "
        f"blocked={payload['n_blocked']} "
        f"patch_rerun={payload['n_patch_rerun_items']} "
        f"source_discovery={payload['n_source_discovery_items']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nresidual follow-up queue manifest written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest.json').resolve()}"
    )
    print(
        f"residual follow-up queue jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_followup_queue.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_replay_repair_patch_rerun_residual_followup_queue.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_strategy_plan(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_strategy_plan(
        Path(
            args.formal_verifier_replay_repair_patch_rerun_residual_followup_queue_dir
        ),
        Path(args.out),
        rag_collaboration_manifest=(
            Path(args.rag_collaboration_manifest)
            if args.rag_collaboration_manifest
            else None
        ),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Proof Strategy Plan")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_strategy_rows']} "
        f"ready={payload['n_ready']} "
        f"patch_evolve_blocks={payload['n_patch_evolve_blocks']} "
        f"source_discovery_cache_items={payload['n_source_discovery_cache_items']} "
        f"kernel_overlay_composition_seeds={payload['n_kernel_overlay_composition_seeds']} "
        f"with_live_tool_plan={payload['n_with_live_tool_plan']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nagentic proof strategy manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_strategy_plan_manifest.json').resolve()}"
    )
    print(
        f"agentic proof strategy jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_strategy_plan.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_strategy_plan.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_candidate_evaluation_queue(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_candidate_evaluation_queue(
        Path(args.formal_verifier_agentic_proof_strategy_plan_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Proof Candidate Evaluation Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_candidate_queue_items']} "
        f"ready={payload['n_ready']} "
        f"blocked={payload['n_blocked']} "
        f"patch_candidates={payload['n_patch_candidate_items']} "
        f"source_discovery_candidates={payload['n_source_discovery_candidate_items']} "
        f"kernel_overlay_candidates={payload['n_kernel_overlay_candidate_items']} "
        f"with_live_evaluator_pool={payload['n_with_live_evaluator_pool']} "
        f"kernel_overlay_context={payload['n_with_kernel_overlay_context']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nagentic proof candidate evaluation queue manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_candidate_evaluation_queue_manifest.json').resolve()}"
    )
    print(
        f"agentic proof candidate evaluation queue jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_candidate_evaluation_queue.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_candidate_evaluation_queue.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_safety_policy(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_safety_policy(
        Path(args.formal_verifier_agentic_proof_candidate_evaluation_queue_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Proof Safety Policy")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_safety_policy_rows']} "
        f"ready={payload['n_ready']} "
        f"blocked={payload['n_blocked']} "
        f"bounded_edit={payload['n_patch_bounded_edit_policies']} "
        f"source_validation={payload['n_source_validation_policies']} "
        f"anti_cheat={payload['n_with_anti_cheat_checks']} "
        f"kernel_overlay_context={payload['n_with_kernel_overlay_context']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nagentic proof safety policy manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_safety_policy_manifest.json').resolve()}"
    )
    print(
        f"agentic proof safety policy jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_safety_policy.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_safety_policy.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_attempt_population(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_attempt_population(
        Path(args.formal_verifier_agentic_proof_safety_policy_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Proof Attempt Population")
    print("=" * 72)
    print(
        f"entries={payload['n_ok']}/{payload['n_population_entries']} "
        f"ready={payload['n_ready']} "
        f"blocked={payload['n_blocked']} "
        f"patch={payload['n_patch_population_entries']} "
        f"source={payload['n_source_population_entries']} "
        f"goal_cache={payload['n_with_goal_cache_key']} "
        f"kernel_overlay_context={payload['n_with_kernel_overlay_context']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nagentic proof attempt population manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_attempt_population_manifest.json').resolve()}"
    )
    print(
        f"agentic proof attempt population jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_attempt_population.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_attempt_population.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_execution_queue(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_execution_queue(
        Path(args.formal_verifier_agentic_proof_attempt_population_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Proof Execution Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_execution_queue_items']} "
        f"ready={payload['n_ready']} "
        f"blocked={payload['n_blocked']} "
        f"patch={payload['n_patch_execution_items']} "
        f"source={payload['n_source_execution_items']} "
        f"candidate_artifacts={payload['n_with_candidate_artifact_path']} "
        f"live_tool_plan={payload['n_with_live_tool_plan']} "
        f"proof_route_dag={payload['n_with_proof_route_dag_plan']} "
        f"verified_sketch={payload['n_with_verified_sketch_gate']} "
        f"blueprint_export={payload['n_with_blueprint_export_plan']} "
        f"kernel_overlay_context={payload['n_with_kernel_overlay_context']} "
        f"live_goal_ready={payload['n_live_goal_location_ready']}/{payload['n_live_goal_requested']} "
        f"needs_target_location={payload['n_needs_target_location']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nagentic proof execution queue manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_execution_queue_manifest.json').resolve()}"
    )
    print(
        f"agentic proof execution queue jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_execution_queue.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_execution_queue.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_execution_materializer(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_execution_materializer(
        Path(args.formal_verifier_agentic_proof_execution_queue_dir),
        Path(args.out),
        overwrite=args.overwrite,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Proof Execution Materializer")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_materializer_rows']} "
        f"artifacts={payload['n_materialized_artifacts']} "
        f"new={payload['n_new_artifacts']} "
        f"live_goal_ready={payload['n_live_goal_location_ready']} "
        f"live_requests={payload['n_live_proof_state_requests']} "
        f"lean_lsp_mcp_ready={payload['n_lean_lsp_mcp_ready_requests']} "
        f"kernel={payload['n_kernel_verified']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nagentic proof execution materializer manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_execution_materializer_manifest.json').resolve()}"
    )
    print(
        f"agentic proof execution materializer jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_execution_materializer.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_execution_materializer.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_execution_artifact_verifier(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_execution_artifact_verifier(
        Path(args.formal_verifier_agentic_proof_execution_materializer_dir),
        Path(args.out),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=args.lean_timeout,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Proof Artifact Verifier")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_verifier_rows']} "
        f"checked={payload['n_local_lean_checked']} "
        f"compiled={payload['n_local_lean_compiled']} "
        f"artifact_kernel={payload['n_artifact_kernel_verified']} "
        f"source_theorem_kernel={payload['n_source_theorem_kernel_verified']} "
        f"live_request_valid={payload['n_live_proof_state_request_valid']}/"
        f"{payload['n_live_proof_state_requests']} "
        f"lean_lsp_mcp_ready={payload['n_lean_lsp_mcp_ready_requests']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nagentic proof artifact verifier manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json').resolve()}"
    )
    print(
        f"agentic proof artifact verifier jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_execution_artifact_verifier.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_execution_artifact_verifier.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_source_theorem_promotion_queue(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_source_theorem_promotion_queue(
        Path(args.formal_verifier_agentic_proof_execution_artifact_verifier_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Source-Theorem Queue")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_promotion_rows']} "
        f"artifact_kernel_inputs={payload['n_artifact_kernel_verified_inputs']} "
        f"ready_source_integration={payload['n_ready_for_source_theorem_integration']} "
        f"needs_target_resolution={payload['n_needs_source_theorem_target_resolution']} "
        f"source_theorem_kernel={payload['n_source_theorem_kernel_verified']} "
        f"needs_source_target={payload['n_needs_source_theorem_target']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nsource-theorem promotion queue manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json').resolve()}"
    )
    print(
        f"source-theorem promotion queue jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_source_theorem_promotion_queue.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_source_theorem_promotion_queue.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_trace_memory(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_trace_memory(
        Path(args.formal_verifier_agentic_proof_execution_artifact_verifier_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Proof Trace Memory")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_trace_memory_rows']} "
        f"events={payload['n_transcript_events']} "
        f"verifier_events={payload['n_with_verifier_result_event']} "
        f"artifact_kernel={payload['n_artifact_kernel_verified']} "
        f"source_theorem_kernel={payload['n_source_theorem_kernel_verified']} "
        f"goal_cache={payload['n_goal_cache_keys']} "
        f"lineage={payload['n_candidate_lineage_keys']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nagentic proof trace memory manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_trace_memory_manifest.json').resolve()}"
    )
    print(
        f"agentic proof trace memory jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_trace_memory.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_trace_memory.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _formal_verifier_agentic_proof_source_theorem_target_resolution(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_source_theorem_target_resolution(
        Path(args.formal_verifier_agentic_proof_source_theorem_promotion_queue_dir),
        Path(args.out),
        formal_verifier_queue_dir=Path(args.formal_verifier_queue_dir)
        if args.formal_verifier_queue_dir
        else None,
        formal_verifier_replay_dir=Path(args.formal_verifier_replay_dir)
        if args.formal_verifier_replay_dir
        else None,
    )
    print("\nAI Statistical Theory Lab Formal Verifier Agentic Source-Theorem Target Resolution")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_target_resolution_rows']} "
        f"resolved={payload['n_resolved_source_theorem_targets']} "
        f"needs_route_match={payload['n_needs_route_ledger_match']} "
        f"overlays={payload['n_overlay_rows']} all_ok={payload['all_ok']}"
    )
    print(
        f"\nsource-theorem target resolution manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_source_theorem_target_resolution_manifest.json').resolve()}"
    )
    print(
        f"source-theorem target overlays written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_source_theorem_target_resolution_overlays.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _research_training_export(args: argparse.Namespace) -> int:
    payload = export_research_training_dataset(
        Path(args.run_dir),
        Path(args.out),
        validation_fraction=args.validation_fraction,
        base_model=args.base_model,
    )
    print("\nAI Statistical Theory Lab Research Training Export")
    print("=" * 72)
    print(
        f"traces={payload['n_traces']} sft={payload['n_sft_examples']} "
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"grpo={payload['n_grpo_tasks']} all_ok={payload['all_ok']}"
    )
    for task, count in payload["by_task"].items():
        print(f"  {task}: {count}")
    print(f"\nresearch training manifest written to {(Path(args.out) / 'research_training_manifest.json').resolve()}")
    print(f"train JSONL written to {(Path(args.out) / 'research_sft_train.jsonl').resolve()}")
    print(f"validation JSONL written to {(Path(args.out) / 'research_sft_validation.jsonl').resolve()}")
    return 0 if payload["all_ok"] else 1


def _rag_collaboration_export(args: argparse.Namespace) -> int:
    artifact_overrides: dict[str, str] = {}
    if args.formalization_gap_planner_proof_state_triage_manifest:
        artifact_overrides["formalization_gap_planner_proof_state_triage"] = (
            args.formalization_gap_planner_proof_state_triage_manifest
        )
    payload = export_rag_collaboration_manifest(
        Path(args.system_audit_manifest),
        Path(args.out),
        max_targets=args.max_targets,
        artifact_overrides=artifact_overrides,
    )
    proof = payload["proof_evidence"]
    rag = payload["rag_provider_evidence"]
    queue = payload["formal_capacity_queue"]
    composition = payload.get("theorem_composition_handoff", {})
    print("\nAI Statistical Theory Lab RAG Collaboration Handoff")
    print("=" * 72)
    print(
        f"proofs={proof['proofs_kernel_verified']}/{proof['proofs_total']} "
        f"lean_rag={rag['lean_rag_dependency_graph_enabled']} "
        f"missing_primitives={queue['missing_formal_primitives']}"
    )
    print(
        f"queue exact_reuse={queue.get('reuse_exact_proof_bank_obligation')} "
        f"compose={queue['compose_existing_bridge_chain']} "
        f"minimal_wrapper={queue['add_minimal_wrapper']} "
        f"design_bridge={queue['design_bridge_lemma']}"
    )
    print(
        f"theorem composition packets={composition.get('theorem_composition_packets')} "
        f"exact_links={composition.get('theorem_composition_exact_proof_bank_links')} "
        f"unresolved={composition.get('theorem_composition_unresolved_primitives')}"
    )
    print(f"handoff targets={len(queue['handoff_targets'])}")
    print(
        f"\nRAG collaboration manifest written to "
        f"{(Path(args.out) / 'rag_collaboration_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'rag_collaboration.md').resolve()}")
    return 0


def _research_policy_baseline(args: argparse.Namespace) -> int:
    payload = evaluate_research_policy_baseline(
        Path(args.train_jsonl),
        Path(args.validation_jsonl),
        Path(args.out),
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Research Policy Baseline")
    print("=" * 72)
    print(
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"top1_exact={payload['top1_exact_rate']:.3f} "
        f"same_task={payload['same_task_rate']:.3f} "
        f"json_key_f1={payload['mean_json_key_f1']:.3f} "
        f"all_ok={payload['all_ok']}"
    )
    print(f"\nmanifest written to {(Path(args.out) / 'research_policy_baseline_manifest.json').resolve()}")
    print(f"predictions written to {(Path(args.out) / 'research_policy_baseline_predictions.jsonl').resolve()}")
    return 0 if payload["all_ok"] else 1


def _next_iteration_audit(args: argparse.Namespace) -> int:
    payload = audit_next_iteration_queue(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Next-Iteration Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_items']} "
        f"actionable={payload['n_actionable_items']} all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_owner"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nnext-iteration queue manifest written to "
        f"{(Path(args.out) / 'next_iteration_queue_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'next_iteration_queue.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_report(args: argparse.Namespace) -> int:
    payload = build_research_markdown_report(Path(args.run_dir), Path(args.out))
    counts = payload["counts"]
    print("\nAI Statistical Theory Lab Research Report")
    print("=" * 72)
    print(
        f"questions={counts['questions']} ready_with_gaps={counts['ready_with_gaps']} "
        f"proved={counts['proved_subclaims']} gaps={counts['formal_gaps']} "
        f"simulations={counts['simulations_passed']}/{counts['simulations']}"
    )
    for error in payload["errors"]:
        print(f"  report error: {error[:180]}")
    print(f"\nmarkdown report written to {(Path(args.out) / 'research_report.md').resolve()}")
    print(f"report manifest written to {(Path(args.out) / 'research_report_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _claim_ledger(args: argparse.Namespace) -> int:
    payload = build_claim_ledger(
        Path(args.run_dir),
        Path(args.out),
        proof_audit_manifest=Path(args.proof_audit_manifest) if args.proof_audit_manifest else None,
        repair_response_promotion_manifest=(
            Path(args.repair_response_promotion_manifest)
            if args.repair_response_promotion_manifest
            else None
        ),
    )
    print("\nAI Statistical Theory Lab Claim Ledger")
    print("=" * 72)
    print(
        f"claims={payload['n_ok']}/{payload['n_claims']} "
        f"questions={payload['n_questions']} "
        f"kernel_overlay_upgrades={payload['n_kernel_overlay_upgrades']} "
        f"repair_response_promotion_upgrades={payload['n_repair_response_promotion_upgrades']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_status"].items():
        print(f"  {status}: {count}")
    print(f"\nclaim ledger manifest written to {(Path(args.out) / 'claim_ledger_manifest.json').resolve()}")
    print(f"jsonl written to {(Path(args.out) / 'claim_ledger.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'claim_ledger.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _claim_ledger_action_export(args: argparse.Namespace) -> int:
    payload = export_claim_ledger_actions(Path(args.claim_ledger_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Claim Ledger Actions")
    print("=" * 72)
    print(
        f"actions={payload['n_ok']}/{payload['n_actions']} "
        f"ledger_claims={payload['ledger_claims']} all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_owner"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nclaim-ledger action manifest written to "
        f"{(Path(args.out) / 'claim_ledger_action_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'claim_ledger_actions.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'claim_ledger_actions.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_plan(args: argparse.Namespace) -> int:
    payload = export_stat_claim_certificate_plan(
        Path(args.claim_ledger_dir),
        Path(args.out),
        max_targets=args.max_targets,
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Plan")
    print("=" * 72)
    print(
        f"targets={payload['n_ok']}/{payload['n_targets']} "
        f"families={payload['n_checker_families']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for family, count in payload["by_family"].items():
        print(f"  {family}: {count}")
    print(
        f"\nstat-claim certificate manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_plan_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'stat_claim_certificate_targets.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'stat_claim_certificate_plan.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_checker_audit(args: argparse.Namespace) -> int:
    verifier = _proof_verifier_from_args(args)
    payload = asyncio.run(
        audit_stat_claim_certificate_checkers(
            verifier,
            Path(args.out),
            ids=args.id or None,
        )
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Checker Audit")
    print("=" * 72)
    print(
        f"verified={payload['n_verified']}/{payload['n_obligations']} "
        f"kernel={payload['n_kernel_verified']}/{payload['n_obligations']} "
        f"status={payload['proof_evidence_status']} "
        f"verifier={payload['verifier']}"
    )
    print(
        f"\nchecker audit manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_checker_audit_manifest.json').resolve()}"
    )
    print(f"Lean artifacts written to {(Path(args.out) / 'lean').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'stat_claim_certificate_checker_audit.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_readiness_overlay(args: argparse.Namespace) -> int:
    payload = export_stat_claim_certificate_readiness_overlay(
        Path(args.certificate_plan_dir),
        Path(args.checker_audit_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Readiness")
    print("=" * 72)
    print(
        f"targets={payload['n_ok']}/{payload['n_targets']} "
        f"ready={payload['n_ready_for_witness_validation']} "
        f"checker_kernel={payload['n_checker_kernel_verified']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nreadiness manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_readiness_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'stat_claim_certificate_readiness.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'stat_claim_certificate_readiness.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_witness_queue(args: argparse.Namespace) -> int:
    payload = export_stat_claim_certificate_witness_queue(
        Path(args.certificate_plan_dir),
        Path(args.readiness_dir),
        Path(args.out),
        max_tasks=args.max_tasks,
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Witness Queue")
    print("=" * 72)
    print(
        f"tasks={payload['n_ok']}/{payload['n_tasks']} "
        f"blocked={payload['n_blocked']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for family, count in payload["by_family"].items():
        print(f"  {family}: {count}")
    print(
        f"\nwitness queue manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_queue_manifest.json').resolve()}"
    )
    print(f"tasks written to {(Path(args.out) / 'stat_claim_certificate_witness_tasks.jsonl').resolve()}")
    print(f"blocked rows written to {(Path(args.out) / 'stat_claim_certificate_witness_blocked.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'stat_claim_certificate_witness_queue.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_witness_materialize(args: argparse.Namespace) -> int:
    payload = materialize_stat_claim_certificate_witness_drafts(
        Path(args.witness_queue_dir),
        Path(args.out),
        max_drafts=args.max_drafts,
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Witness Materializer")
    print("=" * 72)
    print(
        f"drafts={payload['n_ok']}/{payload['n_drafts']} "
        f"unfilled={payload['n_unfilled']} "
        f"ready_for_checker={payload['n_ready_for_checker_validation']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for family, count in payload["by_family"].items():
        print(f"  {family}: {count}")
    print(
        f"\nwitness materializer manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_materializer_manifest.json').resolve()}"
    )
    print(f"draft rows written to {(Path(args.out) / 'stat_claim_certificate_witness_drafts.jsonl').resolve()}")
    print(f"draft files written to {(Path(args.out) / 'witness_drafts').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'stat_claim_certificate_witness_materializer.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_witness_prompt_packets(args: argparse.Namespace) -> int:
    payload = export_stat_claim_certificate_witness_prompt_packets(
        Path(args.materializer_dir),
        Path(args.out),
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Witness Prompt Packets")
    print("=" * 72)
    print(
        f"packets={payload['n_ok']}/{payload['n_prompt_packets']} "
        f"source_grounded={payload['n_with_source_evidence_paths']} "
        f"contracts={payload['n_with_output_contract']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for family, count in payload["by_family"].items():
        print(f"  {family}: {count}")
    print(
        f"\nwitness prompt packet manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_prompt_packets_manifest.json').resolve()}"
    )
    print(f"prompt packets written to {(Path(args.out) / 'stat_claim_certificate_witness_prompt_packets.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'stat_claim_certificate_witness_prompt_packets.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_witness_context_packets(args: argparse.Namespace) -> int:
    payload = export_stat_claim_certificate_witness_context_packets(
        Path(args.prompt_packets_dir),
        Path(args.out),
        max_packets=args.max_packets,
        max_snippets_per_source=args.max_snippets_per_source,
        max_snippet_chars=args.max_snippet_chars,
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Witness Context Packets")
    print("=" * 72)
    print(
        f"context_packets={payload['n_ok']}/{payload['n_context_packets']} "
        f"source_paths={payload['n_resolved_source_paths']}/{payload['n_source_paths']} "
        f"snippets={payload['n_snippets']} "
        f"direct_field_matches={payload['n_field_context_direct_matches']} "
        f"fallback_field_context={payload['n_field_context_fallbacks']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for family, count in payload["by_family"].items():
        print(f"  {family}: {count}")
    print(
        f"\nwitness context packet manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_context_packets_manifest.json').resolve()}"
    )
    print(
        f"context packets written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_context_packets.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_context_packets.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_witness_context_triage(args: argparse.Namespace) -> int:
    payload = export_stat_claim_certificate_witness_context_triage(
        Path(args.context_packets_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Witness Context Triage")
    print("=" * 72)
    print(
        f"triage={payload['n_ok']}/{payload['n_triage_rows']} "
        f"worker_ready={payload['n_worker_ready']} "
        f"source_review={payload['n_source_review_required']} "
        f"blocked_missing_context={payload['n_blocked_missing_context']} "
        f"direct_fields={payload['n_direct_match_fields']} "
        f"fallback_fields={payload['n_fallback_context_fields']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nwitness context triage manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_context_triage_manifest.json').resolve()}"
    )
    print(
        f"triage rows written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_context_triage.jsonl').resolve()}"
    )
    print(
        f"worker-ready rows written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_context_worker_ready.jsonl').resolve()}"
    )
    print(
        f"source-review rows written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_context_source_review.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_context_triage.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_witness_response_validate(args: argparse.Namespace) -> int:
    payload = validate_stat_claim_certificate_witness_worker_outputs(
        Path(args.prompt_packets_dir),
        Path(args.out),
        worker_output_jsonl=Path(args.worker_output_jsonl)
        if args.worker_output_jsonl
        else None,
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Witness Response Validation")
    print("=" * 72)
    print(
        f"responses={payload['n_responses']} "
        f"accepted={payload['n_accepted_for_draft_update']} "
        f"awaiting={payload['n_awaiting_worker_output']} "
        f"overclaims={payload['n_proof_overclaim_rows']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nwitness response validation manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_response_validation_manifest.json').resolve()}"
    )
    print(
        f"validation rows written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_response_validation.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_response_validation.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_witness_response_apply(args: argparse.Namespace) -> int:
    payload = apply_stat_claim_certificate_witness_responses(
        Path(args.response_validation_dir),
        Path(args.out),
        materializer_dir=Path(args.materializer_dir) if args.materializer_dir else None,
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Witness Response Apply")
    print("=" * 72)
    print(
        f"drafts={payload['n_ok']}/{payload['n_drafts']} "
        f"applied={payload['n_worker_response_applied']} "
        f"awaiting={payload['n_awaiting_worker_output']} "
        f"rejected={payload['n_rejected_response_rows']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nwitness response apply manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_response_apply_manifest.json').resolve()}"
    )
    print(
        f"applied rows written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_response_apply.jsonl').resolve()}"
    )
    print(f"draft rows written to {(Path(args.out) / 'stat_claim_certificate_witness_drafts.jsonl').resolve()}")
    print(f"draft files written to {(Path(args.out) / 'witness_drafts').resolve()}")
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_response_apply.md').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _stat_claim_certificate_witness_validate(args: argparse.Namespace) -> int:
    payload = validate_stat_claim_certificate_witness_drafts(
        Path(args.materializer_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Statistical Claim Certificate Witness Validator")
    print("=" * 72)
    print(
        f"drafts={payload['n_ok']}/{payload['n_drafts']} "
        f"ready_for_checker={payload['n_ready_for_checker_validation']} "
        f"incomplete={payload['n_incomplete']} "
        f"overclaims={payload['n_proof_overclaim_rows']} "
        f"status={payload['proof_evidence_status']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nwitness validator manifest written to "
        f"{(Path(args.out) / 'stat_claim_certificate_witness_validator_manifest.json').resolve()}"
    )
    print(f"validation rows written to {(Path(args.out) / 'stat_claim_certificate_witness_validation.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'stat_claim_certificate_witness_validator.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _theorem_composition_export(args: argparse.Namespace) -> int:
    payload = export_theorem_composition_packets(Path(args.claim_ledger_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Theorem Composition Packets")
    print("=" * 72)
    print(
        f"packets={payload['n_ok']}/{payload['n_packets']} "
        f"exact_links={payload['n_exact_proof_bank_links']} "
        f"unresolved_primitives={payload['n_unresolved_primitives']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\ntheorem-composition manifest written to "
        f"{(Path(args.out) / 'theorem_composition_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'theorem_composition_packets.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'theorem_composition.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _doctor(args: argparse.Namespace) -> int:
    report = build_doctor_report(
        root=Path(args.root),
        env_file=Path(args.env_file),
        max_manifests=args.max_manifests,
    )
    if args.out:
        manifest = write_doctor_manifest(report, Path(args.out))
    else:
        manifest = None
    if args.json:
        import json

        print(json.dumps(report, indent=2, default=str))
    else:
        summary = report["summary"]
        print("\nAI Statistician Doctor")
        print("=" * 72)
        print(f"root={report['root']}")
        print(f"required_ok={summary['required_ok']}")
        print(f"real_lean_ready={summary['real_lean_ready']}")
        print(f"llm_theory_ready={summary['llm_theory_ready']}")
        print(f"llm_provider={summary['llm_provider']}")
        print(f"llm_models={summary['llm_models']}")
        print(f"openprover_available={summary['openprover_available']}")
        print(f"registered: obligations={summary['n_obligations']} algorithms={summary['n_algorithms']}")
        for check in report["checks"]:
            required = "required" if check["required"] else "optional"
            print(f"  {check['status']:4} {check['name']} ({required})")
            print(f"       {check['detail']}")
        latest = report["latest_manifests"]
        if latest:
            print("\nlatest manifests")
            for row in latest[: args.max_manifests]:
                print(f"  {row['name']}: {row['path']}")
        if manifest:
            print(f"\ndoctor manifest written to {manifest.resolve()}")
    return 0 if report["summary"]["required_ok"] else 1


def _capability_audit(args: argparse.Namespace) -> int:
    report = build_capability_audit(root=Path(args.root), max_manifests=args.max_manifests)
    manifest = write_capability_audit(report, Path(args.out))
    if args.json:
        import json

        print(json.dumps(report, indent=2, default=str))
    else:
        print("\nAI Statistician Capability Audit")
        print("=" * 72)
        print(f"root={report['root']}")
        print(f"all_required_capabilities_present={report['all_required_capabilities_present']}")
        print(f"ready={report['n_ready']} partial={report['n_partial']} missing={report['n_missing']}")
        for row in report["findings"]:
            print(f"  {row['status']:7} {row['requirement']}")
            for evidence in row["evidence"][:3]:
                print(f"          evidence: {evidence}")
            for limitation in row["limitations"]:
                print(f"          limitation: {limitation}")
        print(f"\ncapability audit manifest written to {manifest.resolve()}")
    return 0 if report["all_required_capabilities_present"] else 1


def _research_capability_audit(args: argparse.Namespace) -> int:
    report = build_research_capability_audit(
        root=Path(args.root),
        question_file=Path(args.question_file),
        frontier_benchmark_file=Path(args.frontier_benchmark_file),
        max_manifests=args.max_manifests,
    )
    manifest = write_research_capability_audit(report, Path(args.out))
    if args.json:
        import json

        print(json.dumps(report, indent=2, default=str))
    else:
        print("\nAI Statistical Theory Lab Capability Audit")
        print("=" * 72)
        print(f"root={report['root']}")
        print(f"goal_complete={report['goal_complete']}")
        print(f"all_current_release_requirements_met={report['all_current_release_requirements_met']}")
        print(
            f"achieved={report['n_achieved']} partial={report['n_partial']} "
            f"not_achieved={report['n_not_achieved']}"
        )
        frontier = report["frontier_summary"]
        print(f"frontier_supported={frontier['n_supported']}/{frontier['n_questions']}")
        for row in report["findings"]:
            gate = "gate" if row["current_release_gate"] else "roadmap"
            print(f"  {row['status']:12} {gate:7} {row['requirement']}")
            for evidence in row["evidence"][:3]:
                print(f"          evidence: {evidence}")
            for limitation in row["limitations"][:2]:
                print(f"          limitation: {limitation}")
        print(f"\nresearch capability audit manifest written to {manifest.resolve()}")
        print(f"markdown report written to {(Path(args.out) / 'research_capability_audit.md').resolve()}")
    return 0 if report["all_current_release_requirements_met"] else 1


def _architecture_audit(args: argparse.Namespace) -> int:
    payload = audit_architecture(Path(args.out))
    print("\nAI Statistician Architecture Audit")
    print("=" * 72)
    print(f"architecture_status={payload['architecture_status']}")
    print(
        "release_scaffold_correct="
        f"{payload['is_current_architecture_correct_for_release_scaffold']}"
    )
    print(
        "full_autonomous_correct="
        f"{payload['is_current_architecture_correct_for_full_autonomous_ai_statistician']}"
    )
    print(f"implemented_feedback_mode={payload['implemented_feedback_mode']}")
    print(f"target_feedback_mode={payload['target_feedback_mode']}")
    for row in payload["components"]:
        print(f"  {row['status']:15} {row['component']}")
    print(f"\narchitecture audit manifest written to {(Path(args.out) / 'architecture_audit_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'architecture_audit.md').resolve()}")
    return 0 if payload["all_release_scaffold_components_present"] else 1


def _prover_component_audit(args: argparse.Namespace) -> int:
    payload = build_prover_component_audit(
        root=Path(args.root),
        question_file=Path(args.question_file),
        frontier_benchmark_file=Path(args.frontier_benchmark_file),
    )
    manifest, report = write_prover_component_audit(payload, Path(args.out))
    if args.json:
        import json

        print(json.dumps(payload, indent=2, default=str))
    else:
        summary = payload["summary"]
        print("\nAI Statistician Prover Component Audit")
        print("=" * 72)
        print(f"paper_outline_exists={payload['paper_outline_exists']}")
        print(
            f"components={summary['components']} ready={summary['ready']} "
            f"partial={summary['partial']} missing_or_not_trained={summary['missing_or_not_trained']}"
        )
        for row in payload["rows"]:
            print(f"  {row['status']:25} {row['component']}")
            for item in row["missing_or_next"][:2]:
                print(f"          next: {item}")
        print(f"\nprover component audit manifest written to {manifest.resolve()}")
        print(f"markdown report written to {report.resolve()}")
    return 0


async def _system_audit(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_audit_questions(args.question_file, args.include_partial_examples)
    seeds = tuple(int(seed) for seed in args.seeds) if args.seeds else tuple(
        range(args.seed_start, args.seed_start + args.n_seeds)
    )
    payload = await run_system_audit(
        Path(args.out),
        questions=questions,
        config=SystemAuditConfig(
            n_runs=args.runs,
            seeds=seeds,
            use_axle=args.real_lean,
            include_eval=not args.no_eval,
        ),
    )
    print("\nAI Statistician System Audit")
    print("=" * 72)
    print(f"all_gates_passed={payload['all_gates_passed']}")
    for gate, ok in payload["gates"].items():
        print(f"  {gate}: {'OK' if ok else 'FAIL'}")
    counts = payload["counts"]
    print(
        f"  questions={counts['question_runs_accepted']}/{counts['questions']} "
        f"proofs={counts['proofs_verified']}/{counts['proofs_total']} "
        f"algorithms={counts['algorithms_ok']}/{counts['algorithms_total']}"
    )
    print(f"\nsystem audit manifest written to {(Path(args.out) / 'system_audit_manifest.json').resolve()}")
    return 0


async def _release_bundle(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_audit_questions(args.question_file, args.include_partial_examples)
    seeds = tuple(int(seed) for seed in args.seeds) if args.seeds else tuple(
        range(args.seed_start, args.seed_start + args.n_seeds)
    )
    payload = await build_release_bundle(
        Path(args.out),
        root=Path(args.root),
        env_file=Path(args.env_file),
        questions=questions,
        config=ReleaseBundleConfig(
            n_runs=args.runs,
            seeds=seeds,
            use_axle=args.real_lean,
            include_eval=not args.no_eval,
            max_manifests=args.max_manifests,
        ),
    )
    print("\nAI Statistician Release Bundle")
    print("=" * 72)
    print(f"release_id={payload['release_id'][:16]}")
    print(f"all_release_gates_passed={payload['all_release_gates_passed']}")
    for gate, ok in payload["gates"].items():
        print(f"  {gate}: {'OK' if ok else 'FAIL'}")
    counts = payload["counts"]
    print(
        f"  questions={counts['question_runs_accepted']}/{counts['questions']} "
        f"proofs={counts['proofs_verified']}/{counts['proofs_total']} "
        f"algorithms={counts['algorithms_ok']}/{counts['algorithms_total']}"
    )
    print(f"\nrelease manifest written to {(Path(args.out) / 'release_manifest.json').resolve()}")
    return 0 if payload["all_release_gates_passed"] else 1


async def _research_benchmark(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    questions = load_open_research_questions(Path(args.question_file))
    payload = await run_research_benchmark(
        questions,
        Path(args.out),
        proof_verifier=verifier,
        formal_source_index_path=(
            Path(args.out) / "formal_source_index.sqlite"
            if args.formal_source_backend == "sqlite"
            else None
        ),
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
        n_runs=args.runs,
        seed=args.seed,
        adaptive_mc_rerun=args.adaptive_mc_rerun,
        adaptive_mc_multiplier=args.adaptive_mc_multiplier,
    )
    print("\nAI Statistical Theory Lab Benchmark")
    print("=" * 72)
    print(
        f"questions={payload['n_questions']} "
        f"ready_with_gaps={payload['n_ready_with_gaps']} "
        f"simulation_flagged={payload['n_simulation_flagged']} "
        f"formal_blocked={payload['n_formal_blocked']}"
    )
    if payload.get("simulation_policy"):
        policy = payload["simulation_policy"]
        print(
            "simulation_policy="
            f"adaptive_mc_rerun={policy.get('adaptive_mc_rerun')} "
            f"adaptive_mc_rows={policy.get('adaptive_mc_rows')} "
            f"adaptive_mc_resolved={policy.get('adaptive_mc_resolved')}"
        )
    if payload.get("formal_source_search"):
        search = payload["formal_source_search"]
        print(f"formal_source_search={search['backend']}")
        if search.get("sqlite_index_path"):
            print(f"sqlite index written to {Path(str(search['sqlite_index_path'])).resolve()}")
        if search.get("dependency_graph_backend"):
            print(f"dependency_graph_search={search['dependency_graph_backend']}")
    for row in payload["questions"]:
        formal = row["formal"]
        print(
            f"{row['status']:38} {row['question']:34} "
            f"class={row['problem_class']}"
        )
        print(
            f"  formal: proved={formal['proved']} gaps={formal['gaps']} "
            f"formalized_gaps={formal.get('formalized_gaps', 0)} failed={formal['failed']} "
            f"procedures={', '.join(row['procedures']) or 'none'}"
        )
        for sim in row["simulations"]:
            metrics = sim["metrics"]
            if "coverage_95" in metrics:
                print(
                    f"  sim {sim['procedure_id']}: passed={sim['passed']} "
                    f"coverage95={metrics['coverage_95']:.3f} rmse={metrics.get('rmse', metrics.get('rmse_center', 0.0)):.4f}"
                )
            else:
                print(f"  sim {sim['procedure_id']}: passed={sim['passed']}")
    print(f"\nresearch manifest written to {(Path(args.out) / 'research_benchmark_manifest.json').resolve()}")
    return 0


async def _research_loop(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    questions = load_open_research_questions(Path(args.question_file))
    if args.max_questions:
        questions = questions[: args.max_questions]
    repair_handlers = None
    if getattr(args, "llm_theory_developer", False):
        provider, provider_name = _build_theory_generator_backend(
            provider_name=args.llm_theory_provider,
            static_response_file=args.llm_theory_static_response_file,
        )
        model = _default_model_for_provider(
            args.llm_theory_provider,
            args.llm_theory_model,
            model_tier="sonnet",
        )
        theory_developer = LLMTheoryDeveloperAgent(
            provider=provider,
            config=ResearchArchitectConfig(
                model=model,
                model_tier="sonnet",
                max_tokens=args.llm_theory_max_tokens,
                temperature=args.llm_theory_temperature,
                provider_name=provider_name,
            ),
        )
        repair_handlers = {
            "THEORY_OR_PROCEDURE_ISSUE": LLMTheoryDeveloperRepairHandler(
                theory_developer=theory_developer,
                out_dir=Path(args.out) / "llm_theory_developer_repairs",
            )
        }
    payload = await run_research_loop_benchmark(
        questions,
        Path(args.out),
        proof_verifier=verifier,
        formal_source_index_path=(
            Path(args.out) / "formal_source_index.sqlite"
            if args.formal_source_backend == "sqlite"
            else None
        ),
        lean_rag_db_path=Path(args.lean_rag_db) if args.lean_rag_db else None,
        repair_handlers=repair_handlers,
        enable_default_theory_developer=not getattr(args, "disable_default_theory_developer", False),
        config=LoopConfig(
            max_rounds=args.max_rounds,
            n_runs=args.runs,
            seed=args.seed,
            mc_rerun_multiplier=args.mc_rerun_multiplier,
        ),
    )
    print("\nAI Statistical Theory Lab Research Loop")
    print("=" * 72)
    print(
        f"questions={payload['n_questions']} max_rounds={payload['config']['max_rounds']} "
        f"all_traces_written={payload['all_loop_traces_written']} "
        f"repair_tasks={payload['n_repair_tasks']}"
    )
    for status, count in payload["status_counts"].items():
        print(f"  {status}: {count}")
    for row in payload["questions"]:
        print(
            f"{row['status']:32} {row['question_id']:34} "
            f"rounds={row['n_rounds']} actions={', '.join(row['action_statuses'])}"
        )
    print(f"\nresearch loop manifest written to {(Path(args.out) / 'research_loop_manifest.json').resolve()}")
    return 0 if payload["all_loop_traces_written"] else 1


def _research_loop_repair_audit(args: argparse.Namespace) -> int:
    payload = audit_research_loop_repair_tasks(
        Path(args.loop_dir),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistical Theory Lab Research Loop Repair Audit")
    print("=" * 72)
    print(
        f"tasks={payload['n_ok']}/{payload['n_tasks']} "
        f"sft={payload['n_sft_examples']} all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_owner"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nrepair audit manifest written to "
        f"{(Path(args.out) / 'research_loop_repair_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _research_loop_live_repair_audit(args: argparse.Namespace) -> int:
    payload = audit_research_loop_live_repair_artifacts(
        Path(args.loop_dir),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistical Theory Lab Research Loop Live Repair Audit")
    print("=" * 72)
    print(
        f"artifacts={payload['n_ok']}/{payload['n_artifacts']} "
        f"kernel_verified={payload['n_kernel_verified']} "
        f"sft={payload['n_sft_examples']} all_ok={payload['all_ok']}"
    )
    for handler, count in payload["by_handler"].items():
        print(f"  {handler}: {count}")
    print(
        f"\nlive repair audit manifest written to "
        f"{(Path(args.out) / 'research_loop_live_repair_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_promotion(args: argparse.Namespace) -> int:
    payload = export_algorithm_repair_promotion_queue(
        Path(args.loop_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Promotion Queue")
    print("=" * 72)
    print(
        f"algorithm_artifacts={payload['n_algorithm_repair_artifacts']} "
        f"candidates={payload['n_ok']}/{payload['n_candidates']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_sandbox_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nalgorithm repair promotion manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_promotion_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_sandbox(args: argparse.Namespace) -> int:
    payload = evaluate_algorithm_repair_sandbox(
        Path(args.promotion_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Sandbox Evaluation")
    print("=" * 72)
    print(
        f"candidates={payload['n_ok']}/{payload['n_candidates']} "
        f"algorithm_audit_ok={payload['algorithm_audit_all_ok']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_sandbox_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nalgorithm repair sandbox manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_sandbox_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_sandbox_apply(args: argparse.Namespace) -> int:
    payload = apply_algorithm_repair_sandbox_results(
        Path(args.sandbox_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Sandbox Apply Evaluation")
    print("=" * 72)
    print(
        f"applied_artifacts={payload['n_ok']}/{payload['n_candidates']} "
        f"algorithm_audit_ok={payload['algorithm_audit_all_ok']} "
        f"all_ok={payload['all_ok']}"
    )
    for mode, count in payload["by_application_mode"].items():
        print(f"  {mode}: {count}")
    print(
        f"\nalgorithm repair sandbox apply manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_sandbox_apply_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_sandbox_rerun(args: argparse.Namespace) -> int:
    payload = rerun_algorithm_repair_sandbox_applications(
        Path(args.apply_dir),
        Path(args.out),
        question_file=Path(args.question_file),
        n_runs=args.runs,
        seed=args.seed,
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Sandbox Rerun Evaluation")
    print("=" * 72)
    print(
        f"rerun_artifacts={payload['n_ok']}/{payload['n_candidates']} "
        f"algorithm_audit_ok={payload['algorithm_audit_all_ok']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_rerun_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nalgorithm repair sandbox rerun manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_sandbox_rerun_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_sandbox_patch_eval(args: argparse.Namespace) -> int:
    payload = evaluate_algorithm_repair_sandbox_patches(
        Path(args.apply_dir),
        Path(args.out),
        question_file=Path(args.question_file),
        n_runs=args.runs,
        seed=args.seed,
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Sandbox Patch Evaluation")
    print("=" * 72)
    print(
        f"patch_eval_artifacts={payload['n_ok']}/{payload['n_candidates']} "
        f"before_after={payload['n_before_after_comparisons']} "
        f"production_patches={payload['n_production_patches_applied']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_comparison_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nalgorithm repair sandbox patch-eval manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_sandbox_patch_eval_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_patch_training_export(args: argparse.Namespace) -> int:
    payload = export_algorithm_repair_patch_training_dataset(
        Path(args.patch_eval_dir),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Patch Training Export")
    print("=" * 72)
    print(
        f"examples={payload['n_training_examples']} "
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"production_patches={payload['n_production_patches_applied']} "
        f"promotion_ready={payload['n_promotion_ready']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_comparison_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nalgorithm repair patch training manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_patch_training_manifest.json').resolve()}"
    )
    print(f"train JSONL written to {(Path(args.out) / 'algorithm_repair_patch_train.jsonl').resolve()}")
    print(
        f"validation JSONL written to "
        f"{(Path(args.out) / 'algorithm_repair_patch_validation.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_patch_policy_train(args: argparse.Namespace) -> int:
    payload = train_algorithm_repair_patch_policy_model(
        Path(args.train_jsonl),
        Path(args.out),
        validation_jsonl=Path(args.validation_jsonl) if args.validation_jsonl else None,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Patch Policy Model")
    print("=" * 72)
    print(
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"pairs={payload['n_training_pairs']} features={payload['n_features']} "
        f"val_safe_acc={payload['validation_safe_decision_accuracy']:.3f} "
        f"all_ok={payload['all_ok']}"
    )
    print(f"model={Path(str(payload['model_json'])).resolve()}")
    print(
        f"manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_patch_policy_model_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_production_patch_plan(args: argparse.Namespace) -> int:
    payload = export_algorithm_repair_production_patch_plan(
        Path(args.policy_model_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Production Patch Plans")
    print("=" * 72)
    print(
        f"plans={payload['n_ok']}/{payload['n_plans']} "
        f"review_required={payload['n_review_required']} "
        f"production_patches={payload['n_production_patches_applied']} "
        f"promotion_ready={payload['n_promotion_ready']} "
        f"all_ok={payload['all_ok']}"
    )
    for kind, count in payload["by_patch_kind"].items():
        print(f"  {kind}: {count}")
    print(
        f"\nproduction patch plan manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_production_patch_plan_manifest.json').resolve()}"
    )
    print(f"plans JSONL written to {(Path(args.out) / 'algorithm_repair_production_patch_plans.jsonl').resolve()}")
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_reviewed_patch_apply(args: argparse.Namespace) -> int:
    payload = apply_reviewed_algorithm_repair_source_patches(
        Path(args.plan_dir),
        Path(args.out),
        source_root=Path(args.source_root),
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Reviewed Patch Apply")
    print("=" * 72)
    print(
        f"patch_candidates={payload['n_ok']}/{payload['n_plans']} "
        f"source_changed={payload['n_source_changed']} "
        f"syntax_valid={payload['n_syntax_valid']} "
        f"production_patches={payload['n_production_patches_applied']} "
        f"all_ok={payload['all_ok']}"
    )
    for kind, count in payload["by_patch_kind"].items():
        print(f"  {kind}: {count}")
    print(
        f"\nreviewed patch apply manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_reviewed_patch_apply_manifest.json').resolve()}"
    )
    print(f"results JSONL written to {(Path(args.out) / 'algorithm_repair_reviewed_patch_apply_results.jsonl').resolve()}")
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_reviewed_patch_validate(args: argparse.Namespace) -> int:
    payload = validate_reviewed_algorithm_repair_patches(
        Path(args.apply_dir),
        Path(args.out),
        source_root=Path(args.source_root),
        question_file=Path(args.question_file),
        n_runs=args.runs,
        seed=args.seed,
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Reviewed Patch Validation")
    print("=" * 72)
    print(
        f"validated={payload['n_ok']}/{payload['n_candidates']} "
        f"imports={payload['n_import_ok']} "
        f"simulations={payload['n_simulation_completed']} "
        f"patched_metric={payload['n_patched_metric_present']} "
        f"all_ok={payload['all_ok']}"
    )
    for kind, count in payload["by_patch_kind"].items():
        print(f"  {kind}: {count}")
    print(
        f"\nreviewed patch validation manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_reviewed_patch_validate_manifest.json').resolve()}"
    )
    print(f"results JSONL written to {(Path(args.out) / 'algorithm_repair_reviewed_patch_validate_results.jsonl').resolve()}")
    return 0 if payload["all_ok"] else 1


async def _research_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_open_research_questions(Path(args.question_file))
    seeds = tuple(int(seed) for seed in args.seeds) if args.seeds else tuple(
        range(args.seed_start, args.seed_start + args.n_seeds)
    )
    payload = await run_research_seed_eval(
        questions,
        ResearchEvalConfig(seeds=seeds, n_runs=args.runs, use_axle=args.real_lean),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Evaluation")
    print("=" * 72)
    print(
        f"questions={payload['n_questions']} seeds={payload['n_seeds']} "
        f"all_ready_with_gaps={payload['all_ready_with_gaps']} "
        f"trace_audits_ok={payload['all_trace_audits_ok']}"
    )
    for question_id, row in payload["summary"].items():
        print(
            f"{question_id:34} ready={row['ready_with_gaps']}/{row['trials']} "
            f"rate={row['ready_rate']:.2f} "
            f"sim_flagged={row['simulation_flagged']} formal_blocked={row['formal_blocked']}"
        )
        for procedure_id, metrics in row["procedures"].items():
            metric_bits = []
            labels = {
                "coverage_95": "coverage95",
                "rmse": "rmse",
                "rmse_center": "rmse_center",
                "empirical_fdr": "fdr",
                "type1_error": "type1",
                "power": "power",
                "rejection_rate": "rej_rate",
                "alt_mean_stop_time": "alt_stop",
                "null_mean_stop_time": "null_stop",
                "average_width": "avg_width",
                "mean_alignment": "align",
                "mean_subspace_error": "subspace_err",
                "mean_angle_error_rad": "angle_rad",
                "mean_top_eigenvalue": "top_eval",
                "tail_index_rmse": "gamma_rmse",
                "tail_index_coverage_95": "gamma_cov",
                "quantile_relative_bias": "q_rel_bias",
                "quantile_coverage_95": "q_cov",
            }
            for metric_key, label in labels.items():
                value = metrics.get(metric_key, {}).get("mean")
                if value is not None:
                    metric_bits.append(f"{label}={value:.4f}")
            if metric_bits:
                print(f"  {procedure_id}: " + " ".join(metric_bits))
    print(f"\nresearch evaluation manifest written to {(Path(args.out) / 'research_evaluation_manifest.json').resolve()}")
    return 0 if payload["all_trace_audits_ok"] else 1


async def _research_system_audit(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    payload = await run_research_system_audit(
        Path(args.out),
        question_file=Path(args.question_file),
        config=ResearchSystemAuditConfig(
            n_runs=args.runs,
            seed=args.seed,
            frontier_smoke_runs=args.frontier_smoke_runs,
            use_axle=args.real_lean,
            use_local_lean=args.local_lean,
            local_lean_project=args.lean_project,
            local_lean_timeout=args.lean_timeout,
            kernel_smoke_ids=tuple(args.kernel_smoke_id or ()),
            kernel_smoke_from_actions=args.kernel_smoke_from_actions,
            formal_source_index_cache=args.formal_source_index_cache,
            refresh_formal_source_index_cache=args.refresh_formal_source_index_cache,
            lean_rag_db=args.lean_rag_db,
            lean_rag_package_root=args.lean_rag_package_root,
            frontier_smoke_cache=args.frontier_smoke_cache,
            refresh_frontier_smoke_cache=args.refresh_frontier_smoke_cache,
            formal_source_graph_cache=args.formal_source_graph_cache,
            refresh_formal_source_graph_cache=args.refresh_formal_source_graph_cache,
            research_benchmark_cache=args.research_benchmark_cache,
            refresh_research_benchmark_cache=args.refresh_research_benchmark_cache,
            formal_verifier_replay_attempts=args.formal_verifier_replay_attempts,
            formal_verifier_replay_attempt_log=args.formal_verifier_replay_attempt_log,
            verify_agentic_artifacts=args.verify_agentic_artifacts,
            adaptive_mc_rerun=not args.no_adaptive_mc_rerun,
            adaptive_mc_multiplier=args.adaptive_mc_multiplier,
            research_agent_runtime_dir=args.research_agent_runtime_dir or None,
        ),
    )
    print("\nAI Statistical Theory Lab System Audit")
    print("=" * 72)
    print(f"all_gates_passed={payload['all_gates_passed']}")
    for gate, ok in payload["gates"].items():
        print(f"  {gate}: {'OK' if ok else 'FAIL'}")
    counts = payload["counts"]
    print(
        f"  questions={counts['research_ready_with_gaps']}/{counts['questions']} "
        f"frontier_supported={counts['frontier_supported']}/{counts['frontier_questions']} "
        f"frontier_precision={counts['frontier_precision_ok']}/{counts['frontier_precision_supported']} "
        f"frontier_backlog={counts['frontier_backlog_ok']}/{counts['frontier_backlog_total']} "
        f"frontier_smoke={counts['frontier_smoke_ready']}/{counts['frontier_smoke_questions']} "
        f"frontier_smoke_cache={counts['frontier_smoke_cache_status']} "
        f"formal_graph_cache={counts['formal_source_graph_cache_status']} "
        f"lean_rag_deps={counts['lean_rag_dependency_graph_enabled']} "
        f"lean_rag_package={counts['lean_rag_package_contract_ok']} "
        f"agent_runtime={counts['research_agent_runtime_audit_all_ok']} "
        f"agent_runtime_requested={counts['research_agent_runtime_audit_requested']} "
        f"research_cache={counts['research_benchmark_cache_status']} "
        f"intake_supported={counts['research_intake_supported_accepted']}/{counts['research_intake_supported']} "
        f"intake_unsupported={counts['research_intake_unsupported_rejected']}/{counts['research_intake_unsupported']} "
        f"knowledge={counts['research_knowledge_problem_ok']}/{counts['research_knowledge_problem_rows']} "
        f"sources={counts['research_source_inventory_ok']}/{counts['research_source_inventory_total']} "
        f"algorithms={counts['research_algorithms_ok']}/{counts['research_algorithms_total']} "
        f"proofs={counts['proofs_verified']}/{counts['proofs_total']} "
        f"traces={counts['research_traces_ok']}/{counts['research_traces_total']} "
        f"formalized_gaps={counts['formalized_gaps']}/{counts['formal_gaps']} "
        f"autoform_targets={counts['autoform_targets_ok']}/{counts['autoform_targets_total']} "
        f"gap_backlog={counts['gap_backlog_ok']}/{counts['gap_backlog_total']} "
        f"missing_primitives={counts['missing_formal_primitives']}"
    )
    print(f"\nresearch system audit manifest written to {(Path(args.out) / 'research_system_audit_manifest.json').resolve()}")
    return 0 if payload["all_gates_passed"] else 1


def _list(args: argparse.Namespace) -> int:
    print("Questions")
    for q in QUESTIONS.values():
        print(f"- {q.id}: {q.title}")
    print("\nFormal obligations")
    rows = obligations_by_tags(set(args.tag or [])) if args.tag else all_obligations()
    for obligation in rows:
        print(f"- {obligation.id}: {obligation.title} [{', '.join(obligation.tags)}]")
    return 0


def _research_architect_theory_develop(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_open_research_questions(Path(args.question_file))
    if args.max_questions:
        questions = questions[: args.max_questions]
    provider, provider_name = _build_theory_generator_backend(
        provider_name=args.provider,
        static_response_file=args.static_response_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    context: dict[str, object] = {}
    if args.context_json:
        context = json.loads(Path(args.context_json).read_text(encoding="utf-8"))
    _attach_runtime_learning_memory(args, context)
    model = _default_model_for_provider(args.provider, args.llm_model, model_tier="sonnet")
    theory_developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            model=model,
            model_tier="sonnet",
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            provider_name=provider_name,
        ),
    )
    architect = ResearchArchitectAgent(
        theory_developer=theory_developer,
        out_dir=Path(args.out),
    )
    manifest = architect.run_theory_development(questions, architect_context=context)
    print("\nAI Statistician Research Architect")
    print("=" * 72)
    print(
        f"questions={manifest['n_questions']} "
        f"theory_packets={manifest['n_theory_derivation_packets']} "
        f"all_packets_ok={manifest['all_packets_ok']}"
    )
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    print(
        "architect manifest written to "
        f"{(Path(args.out) / 'research_architect_manifest.json').resolve()}"
    )
    return 0 if manifest["all_packets_ok"] else 1


def _research_agent_runtime(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    if getattr(args, "capability_eval", False):
        config_errors = _research_agent_runtime_capability_config_errors(args)
        if config_errors:
            print("\nAI Statistician Agent Runtime capability eval rejected")
            print("=" * 72)
            for error in config_errors:
                print(f"- {error}")
            return 2
    verifier = _proof_verifier_from_args(args)
    proof_state_provider = _proof_state_provider_from_args(args)
    questions = load_open_research_questions(Path(args.question_file))
    if args.max_questions:
        questions = questions[: args.max_questions]
    provider, provider_name = _build_theory_generator_backend(
        provider_name=args.provider,
        static_response_file=args.static_response_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    context: dict[str, object] = {}
    if args.context_json:
        context = json.loads(Path(args.context_json).read_text(encoding="utf-8"))
    _attach_runtime_learning_memory(args, context)
    model = _default_model_for_provider(args.provider, args.llm_model, model_tier="sonnet")
    theory_developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            model=model,
            model_tier="sonnet",
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            provider_name=provider_name,
        ),
    )
    architect_coordinator = _build_architect_coordinator_agent_from_args(args, default_model=model)
    algorithm_engineer = _build_algorithm_engineer_agent_from_args(args, default_model=model)
    simulation_engineer = _build_simulation_engineer_agent_from_args(args, default_model=model)
    formalizer = _build_formalizer_agent_from_args(args, default_model=model)
    critic_evaluator = _build_critic_evaluator_agent_from_args(args, default_model=model)
    manifest = run_research_agent_runtime(
        questions,
        Path(args.out),
        theory_developer=theory_developer,
        architect_coordinator=architect_coordinator,
        simulation_engineer=simulation_engineer,
        algorithm_engineer=algorithm_engineer,
        formalizer=formalizer,
        critic_evaluator=critic_evaluator,
        proof_verifier=verifier,
        proof_state_provider=proof_state_provider,
        architect_context=context,
        config=ResearchAgentRuntimeConfig(
            n_runs=args.runs,
            seed=args.seed,
            max_iterations=args.max_iterations,
            max_subsystem_retries=args.max_subsystem_retries,
            max_critic_repair_rounds=args.max_critic_repair_rounds,
            proof_obligation_ids=tuple(args.proof_obligation_id or ()),
            max_proof_obligations=args.max_proof_obligations,
            llm_timeout_seconds=args.llm_timeout_seconds,
            evaluation_mode=(
                "capability_eval"
                if getattr(args, "capability_eval", False)
                else "debug"
            ),
            theorem_closure_proofengineer_bridge=bool(
                getattr(args, "theorem_closure_proofengineer_bridge", False)
            ),
            theorem_closure_proofengineer_local_lean=bool(
                getattr(args, "theorem_closure_proofengineer_local_lean", False)
            ),
            theorem_closure_proofengineer_lean_project=str(
                getattr(args, "theorem_closure_proofengineer_lean_project", "") or ""
            ),
            theorem_closure_proofengineer_lean_timeout=int(
                getattr(args, "theorem_closure_proofengineer_lean_timeout", 240)
            ),
        ),
    )
    print("\nAI Statistician Agent Runtime")
    print("=" * 72)
    print(
        f"questions={manifest['n_questions']} "
        f"status_counts={manifest['status_counts']}"
    )
    evidence = manifest["runtime_evidence_summary"]
    proof_control = evidence["proof"].get("proof_obligation_control", {})
    print(
        f"kernel_verified_subclaims={evidence['proof']['n_kernel_verified_subclaims']} "
        f"formal_gaps={evidence['proof']['n_formal_gaps']} "
        f"registered_proof_obligation_candidates={proof_control.get('n_registered_proof_bank_obligation_candidates', 0)} "
        f"selected_proof_obligations={proof_control.get('n_selected_proof_obligations', 0)} "
        f"llm_requested_proof_obligations={len(proof_control.get('llm_requested_proof_obligation_ids', []) or [])} "
        f"llm_off_catalog_proof_obligations={len(proof_control.get('llm_off_catalog_proof_obligation_ids', []) or [])} "
        f"algorithm_sandbox_executed={evidence['algorithm']['n_algorithm_sandbox_executed']} "
        f"generated_code_sandbox_executed={evidence['algorithm']['n_generated_code_sandbox_executed']}"
    )
    print(f"simulation_boundary={manifest['simulation_evidence_boundary']}")
    print(
        "runtime manifest written to "
        f"{(Path(args.out) / 'research_agent_runtime_manifest.json').resolve()}"
    )
    if getattr(args, "capability_eval", False):
        audit = audit_research_agent_runtime(
            Path(args.out),
            Path(args.out) / "runtime_capability_audit",
        )
        scorecard = audit.get("capability_scorecard", {})
        print(
            f"capability_scorecard={scorecard.get('n_passed')}/"
            f"{scorecard.get('n_requirements')} "
            f"ready={scorecard.get('ready')}"
        )
        return 0 if audit.get("capability_ready_for_full_ai_statistician") else 1
    return 0


def _research_agent_runtime_capability_config_errors(
    args: argparse.Namespace,
) -> list[str]:
    errors: list[str] = []
    if getattr(args, "provider", "") not in {"anthropic", "openai"}:
        errors.append("capability eval requires --provider anthropic or --provider openai")
    subsystem_provider_fields = (
        ("architect_coordinator_provider", "ArchitectCoordinator"),
        ("simulation_engineer_provider", "SimulationEngineer"),
        ("algorithm_engineer_provider", "AlgorithmEngineer"),
        ("formalizer_provider", "Formalizer"),
        ("critic_evaluator_provider", "CriticEvaluator"),
    )
    for field_name, subsystem in subsystem_provider_fields:
        provider_choice = str(getattr(args, field_name, "none") or "none")
        if provider_choice in {"none", "static"}:
            errors.append(
                f"capability eval requires live {subsystem}; "
                f"{field_name}={provider_choice}"
            )
    if not (getattr(args, "local_lean", False) or getattr(args, "real_lean", False)):
        errors.append("capability eval requires --local-lean or --real-lean")
    if getattr(args, "proof_obligation_id", None):
        errors.append(
            "capability eval must not use --proof-obligation-id; manual proof filters are debug-only"
        )
    return errors


def _research_agent_runtime_audit(args: argparse.Namespace) -> int:
    payload = audit_research_agent_runtime(Path(args.runtime_dir), Path(args.out))
    print("\nAI Statistician Agent Runtime Audit")
    print("=" * 72)
    print(
        f"results={payload['n_ok']}/{payload['n_results']} "
        f"traces={payload['n_runtime_traces']} "
        f"agenda={payload['n_runtime_next_action_items']} "
        f"learning={payload['n_runtime_learning_rows']}"
    )
    print(
        f"kernel_verified_subclaims={payload['n_kernel_verified_subclaims']} "
        f"results_with_real_kernel_evidence={payload['n_results_with_real_kernel_evidence']} "
        f"real_kernel_verified_subclaims={payload['n_real_kernel_verified_subclaims']} "
        f"non_real_kernel_verified_subclaims={payload['n_non_real_kernel_verified_subclaims']} "
        f"formal_gaps={payload['n_formal_gaps']} "
        f"registered_proof_obligation_candidates={payload['n_registered_proof_bank_obligation_candidates']} "
        f"memory_prioritized_proof_obligations={payload['n_memory_prioritized_proof_obligations']} "
        f"memory_off_catalog_proof_obligations={payload['n_memory_off_catalog_proof_obligations']} "
        f"memory_rejected_proof_obligations={payload['n_memory_rejected_proof_obligations']} "
        f"llm_requested_proof_obligations={payload['n_llm_requested_proof_obligations']} "
        f"llm_off_catalog_proof_obligations={payload['n_llm_off_catalog_proof_obligations']} "
        f"llm_rejected_proof_obligations={payload['n_llm_rejected_proof_obligations']} "
        f"full_frontier_theorem_proved={payload['n_full_frontier_theorem_proved']}"
    )
    print(
        f"architect={payload['architect_coordinator_enabled']} "
        f"topology_ok={payload['llm_topology_policy_ok']} "
        f"unsupported_backends={payload['unsupported_generator_backends_enabled']} "
        f"critic_reroutes={payload['n_critic_reroutes']}"
    )
    print(
        f"algorithm_sandbox_executed={payload['n_algorithm_sandbox_executed']} "
        f"generated_code_sandbox_executed={payload['n_generated_code_sandbox_executed']} "
        f"unsafe_generated_code_rejected={payload['n_unsafe_generated_code_rejected']}"
    )
    print(
        f"learning_memory_inputs={payload['n_results_with_runtime_learning_memory_input']} "
        f"learning_memory_rows={payload['n_runtime_learning_memory_input_rows']} "
        f"problem_analysis={payload['n_results_with_problem_analysis']} "
        f"stat_knowledge_bank={payload['n_results_with_stat_knowledge_bank_plan']} "
        f"fair_comparison={payload['n_results_with_literature_fair_comparison_plan']}"
    )
    print(f"all_ok={payload['all_ok']}")
    print(
        "runtime audit manifest written to "
        f"{(Path(args.out) / 'research_agent_runtime_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Statistician production core")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="run estimator + formal proof + simulation loop")
    demo.add_argument("--question", action="append", choices=sorted(QUESTIONS), help="run one built-in question; repeatable")
    demo.add_argument("--question-file", help="run one or more external questions from JSON")
    demo.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    demo.add_argument("--llm-theory", action="store_true", help="allow a generator backend to classify supported estimator/DGP families during intake")
    demo.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    demo.add_argument("--llm-provider", choices=LIVE_GENERATOR_PROVIDER_CHOICES, default=_default_live_generator_provider())
    demo.add_argument("--llm-static-response-file", default="", help="JSON response to replay when --llm-provider static is used")
    demo.add_argument("--llm-model", default="", help="model name for the intake generator; Anthropic defaults to Claude Haiku 4.5 for this light classifier")
    demo.add_argument("--llm-max-tokens", type=int, default=700)
    demo.add_argument("--runs", type=int, default=1000, help="Monte Carlo replicates")
    demo.add_argument("--seed", type=int, default=20260528)
    demo.add_argument("--out", default="runs/latest", help="trace output directory")
    demo.add_argument("--env-file", default=".env")
    demo.add_argument("--verbose", action="store_true")
    demo.set_defaults(func=lambda args: asyncio.run(_demo(args)))

    eval_cmd = sub.add_parser("eval", help="run multi-seed evaluation and write an aggregate manifest")
    eval_cmd.add_argument("--question", action="append", choices=sorted(QUESTIONS), help="run one built-in question; repeatable")
    eval_cmd.add_argument("--question-file", help="run one or more external questions from JSON")
    eval_cmd.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    eval_cmd.add_argument("--llm-theory", action="store_true", help="allow a generator backend to classify supported estimator/DGP families during intake")
    eval_cmd.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    eval_cmd.add_argument("--llm-provider", choices=LIVE_GENERATOR_PROVIDER_CHOICES, default=_default_live_generator_provider())
    eval_cmd.add_argument("--llm-static-response-file", default="", help="JSON response to replay when --llm-provider static is used")
    eval_cmd.add_argument("--llm-model", default="", help="model name for the intake generator; Anthropic defaults to Claude Haiku 4.5 for this light classifier")
    eval_cmd.add_argument("--llm-max-tokens", type=int, default=700)
    eval_cmd.add_argument("--runs", type=int, default=500, help="Monte Carlo replicates per trial")
    eval_cmd.add_argument("--n-seeds", type=int, default=3)
    eval_cmd.add_argument("--seed-start", type=int, default=20260528)
    eval_cmd.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    eval_cmd.add_argument("--out", default="runs/eval", help="evaluation output directory")
    eval_cmd.add_argument("--env-file", default=".env")
    eval_cmd.set_defaults(func=lambda args: asyncio.run(_eval(args)))

    proof_audit = sub.add_parser("proof-audit", help="verify the reusable formal proof bank")
    proof_audit.add_argument("--id", action="append", help="specific obligation id; repeatable")
    proof_audit.add_argument("--tag", action="append", help="filter obligations by tag; repeatable")
    proof_audit.add_argument("--require-all-tags", action="store_true", help="require all provided tags instead of any")
    proof_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    proof_audit.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    proof_audit.add_argument("--lean-project", help="local Lake project used by --local-lean")
    proof_audit.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    proof_audit.add_argument("--out", default="runs/proof_audit", help="proof audit output directory")
    proof_audit.add_argument("--env-file", default=".env")
    proof_audit.add_argument("--no-export-lean", action="store_true", help="do not export checked Lean candidates")
    proof_audit.add_argument("--no-attempt-log", action="store_true", help="do not write proof_attempts.jsonl training/audit data")
    proof_audit.add_argument(
        "--negative-controls",
        action="store_true",
        help="also verify one intentionally empty proof body per obligation for repair/value-model data",
    )
    proof_audit.set_defaults(func=lambda args: asyncio.run(_proof_audit(args)))

    theorem_reduction_closure_work_order_audit = sub.add_parser(
        "theorem-reduction-closure-work-order-audit",
        help=(
            "export and optionally local-Lean-check theorem-level reduction closure "
            "work orders emitted by research-agent-runtime"
        ),
    )
    theorem_reduction_closure_work_order_audit.add_argument(
        "--queue-jsonl",
        required=True,
        help="runtime_theorem_reduction_closure_work_orders.jsonl from research-agent-runtime",
    )
    theorem_reduction_closure_work_order_audit.add_argument(
        "--out",
        default="runs/theorem_reduction_closure_work_order_audit",
        help="audit output directory",
    )
    theorem_reduction_closure_work_order_audit.add_argument(
        "--local-lean",
        action="store_true",
        help="run local lake env lean on exported sketches; only successful rows count as proof evidence",
    )
    theorem_reduction_closure_work_order_audit.add_argument(
        "--lean-project",
        help="local Lake project used by --local-lean",
    )
    theorem_reduction_closure_work_order_audit.add_argument(
        "--lean-timeout",
        type=int,
        default=240,
        help="timeout seconds for each theorem-closure local Lean check",
    )
    theorem_reduction_closure_work_order_audit.set_defaults(
        func=_theorem_reduction_closure_work_order_audit
    )

    theorem_reduction_closure_proofengineer_bridge = sub.add_parser(
        "theorem-reduction-closure-proofengineer-bridge",
        help=(
            "run the ProofEngineer bridge from AgentRuntime theorem-reduction "
            "closure work orders to runtime learning memory"
        ),
    )
    bridge_source = theorem_reduction_closure_proofengineer_bridge.add_mutually_exclusive_group(
        required=True
    )
    bridge_source.add_argument(
        "--runtime-dir",
        help=(
            "research-agent-runtime output directory containing "
            "research_agent_runtime_manifest.json"
        ),
    )
    bridge_source.add_argument(
        "--queue-jsonl",
        help="runtime_theorem_reduction_closure_work_orders.jsonl from research-agent-runtime",
    )
    theorem_reduction_closure_proofengineer_bridge.add_argument(
        "--question-id",
        default="",
        help="optional question id to attach to exported runtime learning memory",
    )
    theorem_reduction_closure_proofengineer_bridge.add_argument(
        "--out",
        default="runs/theorem_reduction_closure_proofengineer_bridge",
        help="bridge output directory",
    )
    theorem_reduction_closure_proofengineer_bridge.add_argument(
        "--local-lean",
        action="store_true",
        help="run local lake env lean; only successful rows become proof evidence",
    )
    theorem_reduction_closure_proofengineer_bridge.add_argument(
        "--lean-project",
        help="local Lake project used by --local-lean",
    )
    theorem_reduction_closure_proofengineer_bridge.add_argument(
        "--lean-timeout",
        type=int,
        default=240,
        help="timeout seconds for each theorem-closure local Lean check",
    )
    theorem_reduction_closure_proofengineer_bridge.set_defaults(
        func=_theorem_reduction_closure_proofengineer_bridge
    )

    proof_audit_learning_export = sub.add_parser(
        "proof-audit-learning-export",
        help=(
            "convert kernel-verified proof-audit rows into runtime_learning_rows.jsonl "
            "for AgentRuntime proof-selection memory"
        ),
    )
    proof_audit_learning_export.add_argument(
        "--proof-audit-manifest",
        required=True,
        help="path to proof_audit_manifest.json containing kernel-verified checks",
    )
    proof_audit_learning_export.add_argument(
        "--question-id",
        default="",
        help="optional question id to attach to the runtime learning row",
    )
    proof_audit_learning_export.add_argument(
        "--out",
        default="runs/proof_audit_learning_export",
        help="output directory for runtime_learning_rows.jsonl and manifest",
    )
    proof_audit_learning_export.set_defaults(func=_proof_audit_learning_export)

    theorem_reduction_closure_learning_export = sub.add_parser(
        "theorem-reduction-closure-learning-export",
        help=(
            "convert kernel-verified theorem-reduction closure audit rows into "
            "runtime_learning_rows.jsonl for AgentRuntime routing memory"
        ),
    )
    theorem_reduction_closure_learning_export.add_argument(
        "--theorem-reduction-closure-audit-manifest",
        required=True,
        help=(
            "path to theorem_reduction_closure_work_order_audit_manifest.json "
            "containing kernel-verified closure checks"
        ),
    )
    theorem_reduction_closure_learning_export.add_argument(
        "--question-id",
        default="",
        help="optional question id to attach to the runtime learning row",
    )
    theorem_reduction_closure_learning_export.add_argument(
        "--out",
        default="runs/theorem_reduction_closure_learning_export",
        help="output directory for runtime_learning_rows.jsonl and manifest",
    )
    theorem_reduction_closure_learning_export.set_defaults(
        func=_theorem_reduction_closure_learning_export
    )

    proof_training_export = sub.add_parser(
        "proof-training-export",
        help="export verifier-positive proof attempts as whole-proof SFT JSONL data",
    )
    proof_training_export.add_argument(
        "--attempt-log",
        required=True,
        help="path to proof_attempts.jsonl from proof-audit",
    )
    proof_training_export.add_argument(
        "--validation-fraction",
        type=float,
        default=0.2,
        help="deterministic validation split fraction in [0, 1)",
    )
    proof_training_export.add_argument(
        "--out",
        default="runs/proof_training_export",
        help="output directory for proof_sft_*.jsonl and manifest",
    )
    proof_training_export.set_defaults(func=_proof_training_export)

    proof_repair_export = sub.add_parser(
        "proof-repair-export",
        help="export failed proof attempts paired with accepted proof bodies for repair training",
    )
    proof_repair_export.add_argument(
        "--attempt-log",
        required=True,
        help="path to proof_attempts.jsonl from proof-audit",
    )
    proof_repair_export.add_argument(
        "--validation-fraction",
        type=float,
        default=0.2,
        help="deterministic validation split fraction in [0, 1)",
    )
    proof_repair_export.add_argument(
        "--out",
        default="runs/proof_repair_export",
        help="output directory for proof_repair_*.jsonl and manifest",
    )
    proof_repair_export.set_defaults(func=_proof_repair_export)

    proof_policy_baseline = sub.add_parser(
        "proof-policy-baseline",
        help="evaluate a nearest-neighbor whole-proof policy over exported SFT data",
    )
    proof_policy_baseline.add_argument("--train-jsonl", required=True, help="proof_sft_train.jsonl")
    proof_policy_baseline.add_argument("--validation-jsonl", required=True, help="proof_sft_validation.jsonl")
    proof_policy_baseline.add_argument("--k", type=int, default=5, help="top-k proof-memory candidates")
    proof_policy_baseline.add_argument(
        "--out",
        default="runs/proof_policy_baseline",
        help="output directory for baseline predictions and manifest",
    )
    proof_policy_baseline.set_defaults(func=_proof_policy_baseline)

    proof_policy_train = sub.add_parser(
        "proof-policy-train",
        help="train a small whole-proof candidate ranking policy from proof SFT examples",
    )
    proof_policy_train.add_argument("--train-jsonl", required=True, help="proof_sft_train.jsonl")
    proof_policy_train.add_argument(
        "--validation-jsonl",
        default="",
        help="optional proof_sft_validation.jsonl; defaults to train set",
    )
    proof_policy_train.add_argument("--k", type=int, default=5)
    proof_policy_train.add_argument("--epochs", type=int, default=80)
    proof_policy_train.add_argument("--learning-rate", type=float, default=0.1)
    proof_policy_train.add_argument("--l2", type=float, default=0.001)
    proof_policy_train.add_argument("--negatives-per-query", type=int, default=8)
    proof_policy_train.add_argument(
        "--out",
        default="runs/proof_policy_model",
        help="output directory for proof_policy_model.json and predictions",
    )
    proof_policy_train.set_defaults(func=_proof_policy_train)

    proof_search_audit = sub.add_parser(
        "proof-search-audit",
        help="audit the bounded best-first whole-proof search controller",
    )
    proof_search_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof")
    proof_search_audit.add_argument("--local-lean", action="store_true", help="use local Lean kernel verifier")
    proof_search_audit.add_argument("--local-lean-project", default=None)
    proof_search_audit.add_argument("--local-lean-timeout", type=int, default=90)
    proof_search_audit.add_argument(
        "--max-obligations",
        type=int,
        default=12,
        help="number of proof-bank obligations to search",
    )
    proof_search_audit.add_argument("--max-nodes", type=int, default=8, help="candidate nodes per obligation")
    proof_search_audit.add_argument(
        "--include-invalid-probe",
        action="store_true",
        help="put one invalid high-priority candidate before the registered proof to test branch/error logging",
    )
    proof_search_audit.add_argument(
        "--no-registered-proof",
        action="store_true",
        help="exclude gold registered proof bodies for a harder retrieval/search diagnostic",
    )
    proof_search_audit.add_argument(
        "--policy-model-json",
        default=None,
        help="optional proof_policy_model.json used to score and rerank candidate proof bodies",
    )
    proof_search_audit.add_argument(
        "--value-model-json",
        default=None,
        help="optional proof_search_value_model.json used to score and rerank candidate proof bodies",
    )
    proof_search_audit.add_argument(
        "--out",
        default="runs/proof_search_audit",
        help="output directory for proof_search_results.jsonl and manifest",
    )
    proof_search_audit.set_defaults(func=lambda args: asyncio.run(_proof_search_audit(args)))

    proof_search_kernel_rerun_queue = sub.add_parser(
        "proof-search-kernel-rerun-queue",
        help="queue mock/static proof-search solutions for AXLE/local Lean replay",
    )
    proof_search_kernel_rerun_queue.add_argument(
        "--proof-search-audit-dir",
        required=True,
        help="directory containing proof_search_audit_manifest.json and proof_search_results.jsonl",
    )
    proof_search_kernel_rerun_queue.add_argument(
        "--local-lean-project",
        default=None,
        help="optional local Lake project for the generated local Lean replay command",
    )
    proof_search_kernel_rerun_queue.add_argument("--local-lean-timeout", type=int, default=90)
    proof_search_kernel_rerun_queue.add_argument("--max-rows", type=int, default=50)
    proof_search_kernel_rerun_queue.add_argument(
        "--out",
        default="runs/proof_search_kernel_rerun_queue",
        help="proof-search kernel rerun queue output directory",
    )
    proof_search_kernel_rerun_queue.set_defaults(func=_proof_search_kernel_rerun_queue)

    proof_search_training_export = sub.add_parser(
        "proof-search-training-export",
        help="export proof-search expanded nodes as process-reward/value-model training examples",
    )
    proof_search_training_export.add_argument(
        "--results-jsonl",
        required=True,
        help="proof_search_results.jsonl from proof-search-audit",
    )
    proof_search_training_export.add_argument("--validation-fraction", type=float, default=0.2)
    proof_search_training_export.add_argument(
        "--out",
        default="runs/proof_search_training_export",
        help="output directory for proof_search_process_*.jsonl and manifest",
    )
    proof_search_training_export.set_defaults(func=_proof_search_training_export)

    proof_search_value_train = sub.add_parser(
        "proof-search-value-train",
        help="train a small logistic value baseline from proof-search process examples",
    )
    proof_search_value_train.add_argument(
        "--train-jsonl",
        required=True,
        help="proof_search_process_train.jsonl",
    )
    proof_search_value_train.add_argument(
        "--validation-jsonl",
        default="",
        help="optional proof_search_process_validation.jsonl; defaults to train set",
    )
    proof_search_value_train.add_argument("--epochs", type=int, default=200)
    proof_search_value_train.add_argument("--learning-rate", type=float, default=0.2)
    proof_search_value_train.add_argument("--l2", type=float, default=0.001)
    proof_search_value_train.add_argument(
        "--out",
        default="runs/proof_search_value_model",
        help="output directory for value model and prediction manifests",
    )
    proof_search_value_train.set_defaults(func=_proof_search_value_train)

    algorithm_audit = sub.add_parser("algorithm-audit", help="audit vetted algorithm implementations")
    algorithm_audit.add_argument("--out", default="runs/algorithm_audit", help="algorithm audit output directory")
    algorithm_audit.set_defaults(func=_algorithm_audit)

    research_algorithm_audit = sub.add_parser(
        "research-algorithm-audit",
        help="audit AI Statistical Theory Lab research procedure implementations",
    )
    research_algorithm_audit.add_argument(
        "--out",
        default="runs/research_algorithm_audit",
        help="research algorithm audit output directory",
    )
    research_algorithm_audit.set_defaults(func=_research_algorithm_audit)

    research_intake_audit = sub.add_parser(
        "research-intake-audit",
        help="audit paper-style research-question normalization and unsupported-topic rejection",
    )
    research_intake_audit.add_argument(
        "--supported-file",
        action="append",
        help="supported research question file; repeatable",
    )
    research_intake_audit.add_argument(
        "--unsupported-file",
        action="append",
        help="unsupported research question file; repeatable",
    )
    research_intake_audit.add_argument(
        "--out",
        default="runs/research_intake_audit",
        help="research intake audit output directory",
    )
    research_intake_audit.set_defaults(func=_research_intake_audit)

    research_knowledge_audit = sub.add_parser(
        "research-knowledge-audit",
        help="audit problem-aware research knowledge retrieval and source locations",
    )
    research_knowledge_audit.add_argument(
        "--question-file",
        default="examples/research_questions.json",
        help="supported research question file used for problem-aware retrieval checks",
    )
    research_knowledge_audit.add_argument(
        "--out",
        default="runs/research_knowledge_audit",
        help="research knowledge audit output directory",
    )
    research_knowledge_audit.set_defaults(func=_research_knowledge_audit)

    lean_blueprint_knowledge = sub.add_parser(
        "lean-blueprint-knowledge",
        help="export LeanBlueprint knowledge and visualization adapter artifacts",
    )
    lean_blueprint_knowledge.add_argument(
        "--blueprint-root",
        default="",
        help="optional local PatrickMassot/leanblueprint checkout; defaults to ~/.codex/external/leanblueprint",
    )
    lean_blueprint_knowledge.add_argument(
        "--out",
        default="runs/lean_blueprint_knowledge",
        help="LeanBlueprint knowledge output directory",
    )
    lean_blueprint_knowledge.set_defaults(func=_lean_blueprint_knowledge)

    frontier_coverage_audit = sub.add_parser(
        "frontier-coverage-audit",
        help="parse the frontier paper benchmark and report deterministic research-lab coverage",
    )
    frontier_coverage_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_coverage_audit.add_argument(
        "--out",
        default="runs/frontier_coverage_audit",
        help="frontier coverage audit output directory",
    )
    frontier_coverage_audit.set_defaults(func=_frontier_coverage_audit)

    frontier_precision_audit = sub.add_parser(
        "frontier-precision-audit",
        help="validate that supported frontier classifications have direct body-text evidence",
    )
    frontier_precision_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_precision_audit.add_argument(
        "--out",
        default="runs/frontier_precision_audit",
        help="frontier precision audit output directory",
    )
    frontier_precision_audit.set_defaults(func=_frontier_precision_audit)

    frontier_backlog_audit = sub.add_parser(
        "frontier-backlog-audit",
        help="cluster unsupported frontier benchmark rows into future theory-roadmap domains",
    )
    frontier_backlog_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_backlog_audit.add_argument(
        "--out",
        default="runs/frontier_backlog_audit",
        help="frontier unsupported-theory backlog output directory",
    )
    frontier_backlog_audit.set_defaults(func=_frontier_backlog_audit)

    frontier_theory_target_audit = sub.add_parser(
        "frontier-theory-target-audit",
        help="score generated frontier traces against withheld expected theoretical results",
    )
    frontier_theory_target_audit.add_argument(
        "--run-dir",
        required=True,
        help="research_benchmark directory containing generated frontier trace JSON files",
    )
    frontier_theory_target_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_theory_target_audit.add_argument(
        "--coverage-threshold",
        type=float,
        default=0.18,
        help="token-coverage threshold for marking one expected result as covered",
    )
    frontier_theory_target_audit.add_argument(
        "--out",
        default="runs/frontier_theory_target_audit",
        help="frontier theory target audit output directory",
    )
    frontier_theory_target_audit.set_defaults(func=_frontier_theory_target_audit)

    frontier_dap_prompt_packets = sub.add_parser(
        "frontier-discover-and-prove-prompt-packets",
        help="export DAP-style hard-mode frontier discovery and hard-to-easy rewrite prompt packets",
    )
    frontier_dap_prompt_packets.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_dap_prompt_packets.add_argument(
        "--max-packets",
        type=int,
        default=60,
        help="maximum hard-mode frontier rows to export",
    )
    frontier_dap_prompt_packets.add_argument(
        "--out",
        default="runs/frontier_discover_and_prove_prompt_packets",
        help="frontier DAP prompt packet output directory",
    )
    frontier_dap_prompt_packets.set_defaults(
        func=_frontier_discover_and_prove_prompt_packets
    )

    paper_theory_roundtrip = sub.add_parser(
        "paper-theory-roundtrip",
        help="extract TeX paper statements and queue Lean realization plus Lean-to-LaTeX review work",
    )
    paper_theory_roundtrip.add_argument(
        "--paper-root",
        default="examples/paper_theory_roundtrip_sample.tex",
        help="paper .tex file or directory containing arXiv LaTeX source",
    )
    paper_theory_roundtrip.add_argument(
        "--paper-id",
        default="",
        help="optional stable paper id for emitted statement ids",
    )
    paper_theory_roundtrip.add_argument("--max-statements", type=int, default=200)
    paper_theory_roundtrip.add_argument(
        "--out",
        default="runs/paper_theory_roundtrip",
        help="paper theory round-trip output directory",
    )
    paper_theory_roundtrip.set_defaults(func=_paper_theory_roundtrip)

    frontier_evaluation_triage = sub.add_parser(
        "frontier-evaluation-triage",
        help="turn frontier theory-target misses and simulation flags into owner-routed work items",
    )
    frontier_evaluation_triage.add_argument(
        "--run-dir",
        required=True,
        help="research_benchmark directory containing generated frontier trace JSON files",
    )
    frontier_evaluation_triage.add_argument(
        "--theory-target-manifest",
        required=True,
        help="frontier_theory_target_manifest.json produced by frontier-theory-target-audit",
    )
    frontier_evaluation_triage.add_argument(
        "--out",
        default="runs/frontier_evaluation_triage",
        help="frontier evaluation triage output directory",
    )
    frontier_evaluation_triage.set_defaults(func=_frontier_evaluation_triage)

    frontier_simulation_rerun_audit = sub.add_parser(
        "frontier-simulation-rerun-audit",
        help="rerun simulator-agent frontier triage items with a larger Monte Carlo budget",
    )
    frontier_simulation_rerun_audit.add_argument(
        "--triage-manifest",
        required=True,
        help="frontier_evaluation_triage_manifest.json containing simulator-agent items",
    )
    frontier_simulation_rerun_audit.add_argument("--runs", type=int, default=60)
    frontier_simulation_rerun_audit.add_argument("--seed", type=int, default=20260531)
    frontier_simulation_rerun_audit.add_argument(
        "--out",
        default="runs/frontier_simulation_rerun",
        help="frontier simulation rerun output directory",
    )
    frontier_simulation_rerun_audit.set_defaults(func=_frontier_simulation_rerun_audit)

    frontier_theory_revision_queue = sub.add_parser(
        "frontier-theory-revision-queue",
        help="export scoped TheoryDeveloper tasks for still-flagged frontier simulation reruns",
    )
    frontier_theory_revision_queue.add_argument(
        "--simulation-rerun-manifest",
        required=True,
        help="frontier_simulation_rerun_manifest.json produced by frontier-simulation-rerun-audit",
    )
    frontier_theory_revision_queue.add_argument(
        "--out",
        default="runs/frontier_theory_revision_queue",
        help="frontier theory revision queue output directory",
    )
    frontier_theory_revision_queue.set_defaults(func=_frontier_theory_revision_queue)

    frontier_theory_revision_formalization = sub.add_parser(
        "frontier-theory-revision-formalization-audit",
        help="ground frontier theory-revision obligations in proof-bank and Lean-source retrieval",
    )
    frontier_theory_revision_formalization.add_argument(
        "--revision-queue-manifest",
        required=True,
        help="frontier_theory_revision_queue_manifest.json produced by frontier-theory-revision-queue",
    )
    frontier_theory_revision_formalization.add_argument(
        "--formal-source-index",
        default="",
        help="optional existing formal_source_index.sqlite; defaults to an index under --out",
    )
    frontier_theory_revision_formalization.add_argument("--k", type=int, default=5)
    frontier_theory_revision_formalization.add_argument(
        "--out",
        default="runs/frontier_theory_revision_formalization",
        help="frontier theory-revision formalization audit output directory",
    )
    frontier_theory_revision_formalization.set_defaults(func=_frontier_theory_revision_formalization_audit)

    frontier_smoke_benchmark = sub.add_parser(
        "frontier-smoke-benchmark",
        help="run full research traces on selected supported entries from the frontier paper benchmark",
    )
    frontier_smoke_benchmark.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_smoke_benchmark.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    frontier_smoke_benchmark.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    frontier_smoke_benchmark.add_argument("--lean-project", help="local Lake project used by --local-lean")
    frontier_smoke_benchmark.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    frontier_smoke_benchmark.add_argument("--runs", type=int, default=60, help="Monte Carlo replicates for each selected paper-style question")
    frontier_smoke_benchmark.add_argument(
        "--simulation-rerun-runs",
        type=int,
        default=60,
        help="Monte Carlo replicates for simulator-agent reruns of flagged frontier triage items",
    )
    frontier_smoke_benchmark.add_argument("--seed", type=int, default=20260528)
    frontier_smoke_benchmark.add_argument(
        "--max-per-class",
        type=int,
        default=1,
        help="maximum selected questions per formalized problem class; use 0 to score all supported frontier entries",
    )
    frontier_smoke_benchmark.add_argument(
        "--frontier-smoke-cache",
        default="",
        help="optional persistent cache directory for selected frontier smoke traces; empty disables",
    )
    frontier_smoke_benchmark.add_argument(
        "--refresh-frontier-smoke-cache",
        action="store_true",
        help="rebuild the selected frontier smoke trace cache entry",
    )
    frontier_smoke_benchmark.add_argument("--out", default="runs/frontier_smoke_benchmark", help="frontier smoke output directory")
    frontier_smoke_benchmark.add_argument("--env-file", default=".env")
    frontier_smoke_benchmark.set_defaults(func=lambda args: asyncio.run(_frontier_smoke_benchmark(args)))

    retrieval_audit = sub.add_parser("retrieval-audit", help="audit proof-bank premise retrieval")
    retrieval_audit.add_argument("--k", type=int, default=5, help="top-k threshold")
    retrieval_audit.add_argument("--loogle", action="store_true", help="also record optional Loogle search evidence")
    retrieval_audit.add_argument("--loogle-k", type=int, default=10, help="number of Loogle declarations to keep per query")
    retrieval_audit.add_argument("--loogle-timeout", type=float, default=8.0, help="seconds before a Loogle query is recorded as an error")
    retrieval_audit.add_argument("--out", default="runs/retrieval_audit", help="retrieval audit output directory")
    retrieval_audit.set_defaults(func=_retrieval_audit)

    formal_source_audit = sub.add_parser(
        "formal-source-audit",
        help="index local Lean formal sources and audit theorem-mining queries",
    )
    formal_source_audit.add_argument("--k", type=int, default=8, help="number of declarations to keep per query")
    formal_source_audit.add_argument(
        "--backend",
        choices=("sqlite", "memory"),
        default="sqlite",
        help="retrieval backend for theorem-mining queries",
    )
    formal_source_audit.add_argument(
        "--out",
        default="runs/formal_source_index",
        help="formal source index output directory",
    )
    formal_source_audit.set_defaults(func=_formal_source_audit)

    formal_source_graph_audit = sub.add_parser(
        "formal-source-graph-audit",
        help="audit graph expansion over local Lean/stat declaration symbols",
    )
    formal_source_graph_audit.add_argument("--k", type=int, default=8, help="number of graph-expanded declarations to keep per query")
    formal_source_graph_audit.add_argument(
        "--formal-source-graph-cache",
        default="",
        help="optional persistent cache directory for formal-source graph audits; empty disables",
    )
    formal_source_graph_audit.add_argument(
        "--refresh-formal-source-graph-cache",
        action="store_true",
        help="rebuild the matching formal-source graph cache entry",
    )
    formal_source_graph_audit.add_argument(
        "--out",
        default="runs/formal_source_graph",
        help="formal source graph output directory",
    )
    formal_source_graph_audit.set_defaults(func=_formal_source_graph_audit)

    lean_rag_package_audit = sub.add_parser(
        "lean-rag-package-audit",
        help="audit the shared EmpericalProcessLEAN/lean_rag package contract",
    )
    lean_rag_package_audit.add_argument(
        "--package-root",
        default="",
        help="optional path to the lean_rag package root; auto-discovered when omitted",
    )
    lean_rag_package_audit.add_argument(
        "--db-dir",
        default="",
        help="optional shared_proof_retrieval build/lean_graph directory to inspect",
    )
    lean_rag_package_audit.add_argument(
        "--out",
        default="runs/lean_rag_package_audit",
        help="lean RAG package audit output directory",
    )
    lean_rag_package_audit.set_defaults(func=_lean_rag_package_audit)

    lean_rag_source_registry_expansion = sub.add_parser(
        "lean-rag-source-registry-expansion",
        help="stage source_registry.json additions from Lean RAG target-source candidates",
    )
    lean_rag_source_registry_expansion.add_argument(
        "--package-root",
        default="",
        help="optional path to the lean_rag package root; auto-discovered when omitted",
    )
    lean_rag_source_registry_expansion.add_argument(
        "--db-dir",
        default="",
        help="optional shared_proof_retrieval build/lean_graph directory to inspect",
    )
    lean_rag_source_registry_expansion.add_argument(
        "--out",
        default="runs/lean_rag_source_registry_expansion",
        help="source registry expansion output directory",
    )
    lean_rag_source_registry_expansion.set_defaults(func=_lean_rag_source_registry_expansion)

    lean_rag_source_registry_expansion_preflight = sub.add_parser(
        "lean-rag-source-registry-expansion-preflight",
        help="check local readiness for a staged Lean RAG source registry expansion",
    )
    lean_rag_source_registry_expansion_preflight.add_argument(
        "--expansion-manifest",
        required=True,
        help="path to source_registry_expansion_manifest.json",
    )
    lean_rag_source_registry_expansion_preflight.add_argument(
        "--out",
        default="runs/lean_rag_source_registry_expansion_preflight",
        help="source registry expansion preflight output directory",
    )
    lean_rag_source_registry_expansion_preflight.set_defaults(
        func=_lean_rag_source_registry_expansion_preflight
    )

    lean_rag_source_registry_expansion_apply = sub.add_parser(
        "lean-rag-source-registry-expansion-apply",
        help="dry-run or apply a reviewed staged Lean RAG source registry expansion",
    )
    lean_rag_source_registry_expansion_apply.add_argument(
        "--expansion-manifest",
        required=True,
        help="path to source_registry_expansion_manifest.json",
    )
    lean_rag_source_registry_expansion_apply.add_argument(
        "--preflight-manifest",
        default="",
        help="optional source_registry_expansion_preflight_manifest.json to enforce",
    )
    lean_rag_source_registry_expansion_apply.add_argument(
        "--apply",
        action="store_true",
        help="mutate source_registry.json after all safety gates pass; omitted means dry-run",
    )
    lean_rag_source_registry_expansion_apply.add_argument(
        "--out",
        default="runs/lean_rag_source_registry_expansion_apply",
        help="source registry expansion apply output directory",
    )
    lean_rag_source_registry_expansion_apply.set_defaults(
        func=_lean_rag_source_registry_expansion_apply
    )

    huggingface_lean_source_audit = sub.add_parser(
        "huggingface-lean-source-audit",
        help="discover and rank Hugging Face Lean corpora for local RAG/training reuse",
    )
    huggingface_lean_source_audit.add_argument(
        "--max-results-per-query",
        type=int,
        default=100,
        help="maximum Hugging Face dataset search results per Lean-related query",
    )
    huggingface_lean_source_audit.add_argument(
        "--max-detail-fetches",
        type=int,
        default=140,
        help="maximum dataset detail API calls after search and pinned-source discovery",
    )
    huggingface_lean_source_audit.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="per-request Hugging Face API timeout in seconds",
    )
    huggingface_lean_source_audit.add_argument(
        "--no-network",
        action="store_true",
        help="only use built-in pinned metadata; mainly for smoke tests",
    )
    huggingface_lean_source_audit.add_argument(
        "--out",
        default="runs/huggingface_lean_source_audit",
        help="Hugging Face Lean source audit output directory",
    )
    huggingface_lean_source_audit.set_defaults(func=_huggingface_lean_source_audit)

    huggingface_lean_source_revalidation_tasks = sub.add_parser(
        "huggingface-lean-source-revalidation-tasks",
        help="export worker task packets from the Hugging Face Lean source revalidation queue",
    )
    huggingface_lean_source_revalidation_tasks.add_argument(
        "--queue-jsonl",
        default="runs/huggingface_lean_source_audit/huggingface_lean_source_revalidation_queue.jsonl",
        help="Hugging Face Lean source revalidation queue JSONL",
    )
    huggingface_lean_source_revalidation_tasks.add_argument(
        "--max-tasks",
        type=int,
        default=20,
        help="maximum source revalidation task packets to export",
    )
    huggingface_lean_source_revalidation_tasks.add_argument(
        "--sample-seed",
        type=int,
        default=20260605,
        help="deterministic sample seed recorded in task packets",
    )
    huggingface_lean_source_revalidation_tasks.add_argument(
        "--out",
        default="runs/huggingface_lean_source_revalidation_tasks",
        help="Hugging Face Lean source revalidation task output directory",
    )
    huggingface_lean_source_revalidation_tasks.set_defaults(
        func=_huggingface_lean_source_revalidation_tasks
    )

    huggingface_lean_source_revalidation_prompt_packets = sub.add_parser(
        "huggingface-lean-source-revalidation-prompt-packets",
        help="export worker prompt packets and response contracts for Hugging Face Lean source revalidation",
    )
    huggingface_lean_source_revalidation_prompt_packets.add_argument(
        "--task-dir",
        default="runs/huggingface_lean_source_revalidation_tasks",
        help="directory containing hf_lean_source_revalidation_tasks_manifest.json",
    )
    huggingface_lean_source_revalidation_prompt_packets.add_argument(
        "--max-packets",
        type=int,
        default=20,
        help="maximum source revalidation prompt packets to export",
    )
    huggingface_lean_source_revalidation_prompt_packets.add_argument(
        "--out",
        default="runs/huggingface_lean_source_revalidation_prompt_packets",
        help="Hugging Face Lean source revalidation prompt packet output directory",
    )
    huggingface_lean_source_revalidation_prompt_packets.set_defaults(
        func=_huggingface_lean_source_revalidation_prompt_packets
    )

    huggingface_lean_source_revalidation_artifact_validation = sub.add_parser(
        "huggingface-lean-source-revalidation-artifact-validation",
        help="validate worker outputs for Hugging Face Lean source revalidation task packets",
    )
    huggingface_lean_source_revalidation_artifact_validation.add_argument(
        "--task-dir",
        default="runs/huggingface_lean_source_revalidation_tasks",
        help="directory containing hf_lean_source_revalidation_tasks_manifest.json",
    )
    huggingface_lean_source_revalidation_artifact_validation.add_argument(
        "--response-jsonl",
        default="",
        help="optional worker output JSONL; default is task-dir/hf_lean_source_revalidation_worker_outputs.jsonl",
    )
    huggingface_lean_source_revalidation_artifact_validation.add_argument(
        "--out",
        default="runs/huggingface_lean_source_revalidation_artifact_validation",
        help="Hugging Face Lean source revalidation artifact validation output directory",
    )
    huggingface_lean_source_revalidation_artifact_validation.set_defaults(
        func=_huggingface_lean_source_revalidation_artifact_validation
    )

    huggingface_lean_source_revalidation_promotion_queue = sub.add_parser(
        "huggingface-lean-source-revalidation-promotion-queue",
        help="export promotion-review rows from validated Hugging Face Lean source artifacts",
    )
    huggingface_lean_source_revalidation_promotion_queue.add_argument(
        "--artifact-validation-dir",
        default="runs/huggingface_lean_source_revalidation_artifact_validation",
        help="directory containing hf_lean_source_revalidation_artifact_validation_manifest.json",
    )
    huggingface_lean_source_revalidation_promotion_queue.add_argument(
        "--out",
        default="runs/huggingface_lean_source_revalidation_promotion_queue",
        help="Hugging Face Lean source promotion queue output directory",
    )
    huggingface_lean_source_revalidation_promotion_queue.set_defaults(
        func=_huggingface_lean_source_revalidation_promotion_queue
    )

    lean_rag_dependency_health = sub.add_parser(
        "lean-rag-dependency-health",
        help="validate an optional EmpericalProcessLEAN lean_rag dependency graph SQLite DB",
    )
    lean_rag_dependency_health.add_argument(
        "--db",
        default="",
        help="requested lean_rag dependency graph SQLite DB path",
    )
    lean_rag_dependency_health.add_argument(
        "--active-db",
        default="",
        help="active DB path actually attached by the search backend, if any",
    )
    lean_rag_dependency_health.add_argument(
        "--auto-discovered",
        action="store_true",
        help="mark the active DB as auto-discovered rather than explicitly requested",
    )
    lean_rag_dependency_health.add_argument(
        "--out",
        default="runs/lean_rag_dependency_health",
        help="lean RAG dependency health output directory",
    )
    lean_rag_dependency_health.set_defaults(func=_lean_rag_dependency_health)

    formal_source_retrieval_benchmark = sub.add_parser(
        "formal-source-retrieval-benchmark",
        help="measure gold-family retrieval recall over default, external, or combined Lean source suites",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--suite",
        choices=("default", "external", "all"),
        default="default",
        help="benchmark suite to run",
    )
    formal_source_retrieval_benchmark.add_argument("--k", type=int, default=8)
    formal_source_retrieval_benchmark.add_argument(
        "--formal-source-index",
        default="runs/formal_source_retrieval_benchmark/formal_source_index.sqlite",
        help="SQLite index path for this benchmark run",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--formal-source-index-cache",
        default="runs/formal_source_index_cache/formal_source_index.sqlite",
        help="persistent SQLite cache; pass empty string to disable",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--refresh-formal-source-index-cache",
        action="store_true",
        help="rebuild and overwrite the persistent formal-source index cache",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--lean-rag-db",
        default=None,
        help="optional EmpericalProcessLEAN lean_rag dependency graph SQLite DB",
    )
    formal_source_retrieval_benchmark.add_argument(
        "--out",
        default="runs/formal_source_retrieval_benchmark",
        help="formal-source retrieval benchmark output directory",
    )
    formal_source_retrieval_benchmark.set_defaults(func=_formal_source_retrieval_benchmark)

    formal_source_retrieval_ablation = sub.add_parser(
        "formal-source-retrieval-ablation",
        help="compare formal-source retrieval with and without the Lean RAG dependency graph provider",
    )
    formal_source_retrieval_ablation.add_argument(
        "--suite",
        choices=("default", "external", "all"),
        default="default",
        help="benchmark suite to include before dependency-sensitive Lean RAG probes",
    )
    formal_source_retrieval_ablation.add_argument("--k", type=int, default=8)
    formal_source_retrieval_ablation.add_argument(
        "--formal-source-index",
        default="runs/formal_source_retrieval_ablation/formal_source_index.sqlite",
        help="SQLite index path for this ablation run",
    )
    formal_source_retrieval_ablation.add_argument(
        "--formal-source-index-cache",
        default="runs/formal_source_index_cache/formal_source_index.sqlite",
        help="persistent SQLite cache; pass empty string to disable",
    )
    formal_source_retrieval_ablation.add_argument(
        "--refresh-formal-source-index-cache",
        action="store_true",
        help="rebuild and overwrite the persistent formal-source index cache",
    )
    formal_source_retrieval_ablation.add_argument(
        "--lean-rag-db",
        default=None,
        help="optional EmpericalProcessLEAN lean_rag dependency graph SQLite DB",
    )
    formal_source_retrieval_ablation.add_argument(
        "--out",
        default="runs/formal_source_retrieval_ablation",
        help="formal-source retrieval ablation output directory",
    )
    formal_source_retrieval_ablation.set_defaults(func=_formal_source_retrieval_ablation)

    proof_search_retrieval_ablation = sub.add_parser(
        "proof-search-retrieval-ablation",
        help="compare bounded proof-search behavior with and without the Lean RAG dependency graph provider",
    )
    proof_search_retrieval_ablation.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof")
    proof_search_retrieval_ablation.add_argument("--local-lean", action="store_true", help="use local Lean kernel verifier")
    proof_search_retrieval_ablation.add_argument("--lean-project", default=None)
    proof_search_retrieval_ablation.add_argument("--lean-timeout", type=int, default=90)
    proof_search_retrieval_ablation.add_argument("--max-obligations", type=int, default=6)
    proof_search_retrieval_ablation.add_argument("--max-nodes", type=int, default=4)
    proof_search_retrieval_ablation.add_argument("--formal-source-k", type=int, default=4)
    proof_search_retrieval_ablation.add_argument(
        "--no-registered-proof",
        action="store_true",
        help="exclude gold registered proof bodies to measure RAG/search lift under a harder diagnostic",
    )
    proof_search_retrieval_ablation.add_argument(
        "--formal-source-index",
        default="runs/proof_search_retrieval_ablation/formal_source_index.sqlite",
        help="SQLite index path for this ablation run",
    )
    proof_search_retrieval_ablation.add_argument(
        "--formal-source-index-cache",
        default="runs/formal_source_index_cache/formal_source_index.sqlite",
        help="persistent SQLite cache; pass empty string to disable",
    )
    proof_search_retrieval_ablation.add_argument(
        "--refresh-formal-source-index-cache",
        action="store_true",
        help="rebuild and overwrite the persistent formal-source index cache",
    )
    proof_search_retrieval_ablation.add_argument(
        "--lean-rag-db",
        default=None,
        help="optional EmpericalProcessLEAN lean_rag dependency graph SQLite DB",
    )
    proof_search_retrieval_ablation.add_argument(
        "--out",
        default="runs/proof_search_retrieval_ablation",
        help="proof-search retrieval ablation output directory",
    )
    proof_search_retrieval_ablation.set_defaults(func=_proof_search_retrieval_ablation)

    intake_audit = sub.add_parser("intake-audit", help="audit supported question intake and unsupported question rejection")
    intake_audit.add_argument("--supported-file", action="append", help="supported question JSON file; repeatable")
    intake_audit.add_argument("--unsupported-file", action="append", help="unsupported question JSON file; repeatable")
    intake_audit.add_argument("--out", default="runs/intake_audit", help="intake audit output directory")
    intake_audit.set_defaults(func=_intake_audit)

    trace_audit = sub.add_parser("trace-audit", help="validate per-question traces against a run manifest")
    trace_audit.add_argument("--run-dir", required=True, help="directory containing manifest.json and question trace JSON files")
    trace_audit.add_argument("--out", default="runs/trace_audit", help="trace audit output directory")
    trace_audit.set_defaults(func=_trace_audit)

    research_trace_audit = sub.add_parser(
        "research-trace-audit",
        help="validate AI Statistical Theory Lab benchmark traces against their manifest",
    )
    research_trace_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_trace_audit.add_argument(
        "--out",
        default="runs/research_trace_audit",
        help="research trace audit output directory",
    )
    research_trace_audit.set_defaults(func=_research_trace_audit)

    research_gap_audit = sub.add_parser(
        "research-gap-audit",
        help="aggregate and validate FORMAL_GAP records from a research benchmark run",
    )
    research_gap_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_gap_audit.add_argument(
        "--out",
        default="runs/research_gap_backlog",
        help="formal gap backlog output directory",
    )
    research_gap_audit.set_defaults(func=_research_gap_audit)

    formalization_target_audit = sub.add_parser(
        "formalization-target-audit",
        help="rank missing FORMAL_GAP primitives into a Lean theorem-development queue",
    )
    formalization_target_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    formalization_target_audit.add_argument(
        "--out",
        default="runs/formalization_target_audit",
        help="formalization target audit output directory",
    )
    formalization_target_audit.set_defaults(func=_formalization_target_audit)

    formal_gap_task_export = sub.add_parser(
        "formal-gap-task-export",
        help="export FORMAL_GAP skeletons as machine-readable Lean task JSONL",
    )
    formal_gap_task_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    formal_gap_task_export.add_argument(
        "--out",
        default="runs/formal_gap_lean_tasks",
        help="formal gap Lean task output directory",
    )
    formal_gap_task_export.set_defaults(func=_formal_gap_task_export)

    autoform_target_export = sub.add_parser(
        "autoform-target-export",
        help="export FORMAL_GAP tasks as Autoform-Bot-compatible target YAML",
    )
    autoform_target_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    autoform_target_export.add_argument(
        "--out",
        default="runs/autoform_targets",
        help="Autoform target YAML/book output directory",
    )
    autoform_target_export.set_defaults(func=_autoform_target_export)

    autoform_harness_audit = sub.add_parser(
        "autoform-harness-audit",
        help="audit the local Autoform-Bot harness checkout and reusable entrypoints",
    )
    autoform_harness_audit.add_argument(
        "--out",
        default="runs/autoform_harness",
        help="Autoform harness audit output directory",
    )
    autoform_harness_audit.set_defaults(func=_autoform_harness_audit)

    proof_bank_expansion_export = sub.add_parser(
        "proof-bank-expansion-export",
        help="export formal-gap tasks as proof-bank lemma proposals and theorem-hole queue rows",
    )
    proof_bank_expansion_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    proof_bank_expansion_export.add_argument(
        "--out",
        default="runs/proof_bank_expansion",
        help="proof-bank expansion candidate output directory",
    )
    proof_bank_expansion_export.set_defaults(func=_proof_bank_expansion_export)

    proof_bank_action_export = sub.add_parser(
        "proof-bank-action-export",
        help="export ranked FormalVerifier action rows from proof-bank expansion candidates",
    )
    proof_bank_action_export.add_argument(
        "--proof-bank-expansion-dir",
        required=True,
        help="directory containing proof_bank_expansion_manifest.json and lemma_proposals.jsonl",
    )
    proof_bank_action_export.add_argument(
        "--out",
        default="runs/proof_bank_actions",
        help="proof-bank action output directory",
    )
    proof_bank_action_export.set_defaults(func=_proof_bank_action_export)

    assumption_interface_export = sub.add_parser(
        "assumption-interface-export",
        help="export formalized Lean assumption-interface predicate targets from proof-bank actions",
    )
    assumption_interface_export.add_argument(
        "--proof-bank-actions-dir",
        required=True,
        help="directory containing proof_bank_action_manifest.json",
    )
    assumption_interface_export.add_argument(
        "--out",
        default="runs/assumption_interfaces",
        help="assumption-interface output directory",
    )
    assumption_interface_export.add_argument("--lean-project", help="optional local Lake project for `lake env lean` checks")
    assumption_interface_export.add_argument("--lean-timeout", type=int, default=90)
    assumption_interface_export.set_defaults(func=_assumption_interface_export)

    formalization_delta_plan = sub.add_parser(
        "formalization-delta-plan",
        help="rank the minimal useful Lean formalization delta from proof-bank action rows",
    )
    formalization_delta_plan.add_argument(
        "--proof-bank-actions-dir",
        required=True,
        help="directory containing proof_bank_action_manifest.json",
    )
    formalization_delta_plan.add_argument(
        "--primitive-source-coverage-dir",
        help="optional directory containing primitive_source_coverage_manifest.json",
    )
    formalization_delta_plan.add_argument(
        "--formal-gap-tasks-dir",
        help="optional directory containing formal_gap_lean_task_manifest.json",
    )
    formalization_delta_plan.add_argument(
        "--out",
        default="runs/formalization_delta_plan",
        help="formalization-delta output directory",
    )
    formalization_delta_plan.set_defaults(func=_formalization_delta_plan)

    formal_verifier_queue = sub.add_parser(
        "formal-verifier-queue",
        help="export verifier-facing theorem-route work items from the formalization delta plan",
    )
    formal_verifier_queue.add_argument(
        "--formalization-delta-dir",
        required=True,
        help="directory containing formalization_delta_plan_manifest.json",
    )
    formal_verifier_queue.add_argument(
        "--proof-search-no-registered-ablation-dir",
        help="optional directory containing the no-registered proof-search retrieval ablation manifest",
    )
    formal_verifier_queue.add_argument(
        "--kernel-smoke-proof-audit-dir",
        help="optional directory containing the focused kernel-smoke proof audit manifest",
    )
    formal_verifier_queue.add_argument(
        "--proof-attempt-log",
        help="optional proof_attempts.jsonl used to attach prior verifier positives/negatives",
    )
    formal_verifier_queue.add_argument(
        "--proof-search-results",
        help="optional proof_search_results.jsonl used to attach prior proof-search outcomes",
    )
    formal_verifier_queue.add_argument("--max-routes", type=int, default=20)
    formal_verifier_queue.add_argument(
        "--out",
        default="runs/formal_verifier_queue",
        help="formal-verifier queue output directory",
    )
    formal_verifier_queue.set_defaults(func=_formal_verifier_queue)

    goal_conditioned_minimal_formalization_plan = sub.add_parser(
        "goal-conditioned-minimal-formalization-plan",
        help="choose the smallest theorem-specific Lean formalization route from delta and verifier queue artifacts",
    )
    goal_conditioned_minimal_formalization_plan.add_argument(
        "--formalization-delta-plan-dir",
        required=True,
        help="directory containing formalization_delta_plan_manifest.json",
    )
    goal_conditioned_minimal_formalization_plan.add_argument(
        "--formal-verifier-queue-dir",
        required=True,
        help="directory containing formal_verifier_queue_manifest.json",
    )
    goal_conditioned_minimal_formalization_plan.add_argument("--max-routes", type=int, default=20)
    goal_conditioned_minimal_formalization_plan.add_argument(
        "--out",
        default="runs/goal_conditioned_minimal_formalization_plan",
        help="goal-conditioned minimal formalization output directory",
    )
    goal_conditioned_minimal_formalization_plan.set_defaults(
        func=_goal_conditioned_minimal_formalization_plan
    )

    formalization_gap_planner_target_intake = sub.add_parser(
        "formalization-gap-planner-target-intake",
        help="normalize a raw theorem request into portable gap-planner route seeds",
    )
    formalization_gap_planner_target_intake.add_argument(
        "--input",
        required=True,
        help="target theorem request JSON, JSON list, or plain text file",
    )
    formalization_gap_planner_target_intake.add_argument(
        "--out",
        default="runs/formalization_gap_planner_target_intake",
        help="target-intake output directory",
    )
    formalization_gap_planner_target_intake.set_defaults(
        func=_formalization_gap_planner_target_intake
    )

    formalization_gap_planner_reuse_smoke = sub.add_parser(
        "formalization-gap-planner-reuse-smoke",
        help=(
            "run target intake, standalone planning, audits, prover-adapter "
            "contract, refinement loop, and publication-bundle audit as one reusable smoke test"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--input",
        required=True,
        help="target theorem request JSON, JSON list, or plain text file",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--target-prover-family",
        default="rocq",
        choices=["lean4", "lean", "rocq", "coq", "isabelle", "isabelle/hol", "agda", "other"],
        help="target prover ecosystem for public work-packet mapping smoke",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--target-library-snapshot-ref",
        default="",
        help="target-prover library snapshot label written into adapter packets",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--max-routes",
        type=int,
        default=20,
        help="maximum number of standalone route plans to emit",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--ground-truth",
        help="optional route-truth JSON file for the bundled benchmark",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--lean-rag-db",
        help="optional Lean RAG dependency graph SQLite DB for adapter-registry readiness",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--paper-library-dir",
        help="optional local paper/text corpus directory for adapter-registry readiness",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-provider",
        default="anthropic",
        choices=["prompt_only", "static", "anthropic", "openai"],
        help=(
            "LLM route-planner provider used inside the full reuse-smoke path; "
            "Anthropic/Claude is staged by default and only called when --llm-route-planner-invoke-provider is set"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-model",
        default="",
        help="explicit model name for live LLM route-planner providers; overrides --llm-route-planner-model-tier",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-model-tier",
        default="auto",
        choices=["auto", "haiku", "sonnet", "opus"],
        help=(
            "Claude tier policy for the primary route planner; auto uses Haiku "
            "for small bounded routes and Sonnet for residual/bridge/source-port/new-theory routes"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-max-tokens",
        type=int,
        default=9000,
        help="maximum output tokens for live LLM route-planner providers",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-max-repair-attempts",
        type=int,
        default=1,
        help=(
            "maximum local-validator repair retries for primary LLM route-planner responses; "
            "set 0 to avoid extra live provider calls"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-temperature",
        type=float,
        default=0.1,
        help="temperature for live LLM route-planner providers",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-invoke-provider",
        action="store_true",
        help=(
            "invoke the selected LLM route-planner provider; without this, "
            "reviewed response JSON is only validated"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-response-json",
        help="optional reviewed LLM route-planner response JSON to validate and consume",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-static-response-file",
        help=(
            "offline static response JSON for deterministic reviewed replay; "
            "use with --llm-route-planner-invoke-provider to generate one response per request"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-provider",
        default="anthropic",
        choices=["prompt_only", "static", "anthropic", "openai"],
        help=(
            "feedback LLM route-planner provider for the route-replan seed; "
            "Anthropic/Claude is staged by default and only called when --feedback-llm-route-planner-invoke-provider is set"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-model",
        default="",
        help="explicit model name for feedback LLM route-planner providers; overrides --feedback-llm-route-planner-model-tier",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-model-tier",
        default="auto",
        choices=["auto", "haiku", "sonnet", "opus"],
        help=(
            "Claude tier policy for the feedback route planner; auto uses Haiku "
            "for small bounded routes and Sonnet for residual/bridge/source-port/new-theory routes"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-max-tokens",
        type=int,
        default=9000,
        help="maximum output tokens for feedback LLM route-planner providers",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-max-repair-attempts",
        type=int,
        default=1,
        help=(
            "maximum local-validator repair retries for feedback LLM route-planner responses; "
            "set 0 to avoid extra live provider calls"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-temperature",
        type=float,
        default=0.1,
        help="temperature for feedback LLM route-planner providers",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-invoke-provider",
        action="store_true",
        help=(
            "invoke the selected feedback LLM route-planner provider after "
            "prover residuals and interactive-session context are available"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-response-json",
        help="optional reviewed feedback LLM route-planner response JSON to validate and consume",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-static-response-file",
        help=(
            "offline static feedback response JSON for deterministic replay; "
            "use with --feedback-llm-route-planner-invoke-provider to generate one response per request"
        ),
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--out",
        default="runs/formalization_gap_planner_reuse_smoke",
        help="reuse-smoke output directory",
    )
    formalization_gap_planner_reuse_smoke.set_defaults(
        func=_formalization_gap_planner_reuse_smoke
    )

    formalization_gap_planner_standalone_plan = sub.add_parser(
        "formalization-gap-planner-standalone-plan",
        help=(
            "build a portable formalization-gap plan from standalone theorem, "
            "route, and library-coverage JSON"
        ),
    )
    formalization_gap_planner_standalone_plan.add_argument(
        "--input",
        required=True,
        help="standalone theorem-route JSON input",
    )
    formalization_gap_planner_standalone_plan.add_argument(
        "--max-routes",
        type=int,
        default=20,
        help="maximum number of route plans to emit",
    )
    formalization_gap_planner_standalone_plan.add_argument(
        "--out",
        default="runs/formalization_gap_planner_standalone_plan",
        help="standalone formalization-gap planner output directory",
    )
    formalization_gap_planner_standalone_plan.set_defaults(
        func=_formalization_gap_planner_standalone_plan
    )

    formalization_gap_planner_llm_route_planner = sub.add_parser(
        "formalization-gap-planner-llm-route-planner",
        help=(
            "stage or run the LLM-backed proof-route planner over standalone "
            "formalization-gap input"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--input",
        required=True,
        help="standalone theorem-route JSON input",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--provider",
        default="anthropic",
        choices=["prompt_only", "static", "anthropic", "openai"],
        help=(
            "LLM generator provider; Anthropic/Claude is staged by default, "
            "and no provider is called unless --invoke-provider is set"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--model",
        default="",
        help="explicit model name for live provider calls or provenance metadata; overrides --model-tier",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--model-tier",
        default="auto",
        choices=["auto", "haiku", "sonnet", "opus"],
        help=(
            "Claude tier policy for Anthropic calls; auto uses Haiku for small "
            "bounded routes and Sonnet for residual/bridge/source-port/new-theory routes"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--max-tokens",
        type=int,
        default=9000,
        help="maximum generator output tokens when --invoke-provider is set",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="generator temperature when --invoke-provider is set",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--max-repair-attempts",
        type=int,
        default=1,
        help=(
            "maximum local-validator repair retries for invoked LLM responses; "
            "set 0 to disable extra provider calls"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--invoke-provider",
        action="store_true",
        help="call the configured generator backend instead of only staging prompts",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--response-json",
        help="reviewed LLM route-planner response JSON to validate and apply",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--static-response-file",
        help=(
            "static JSON payload; with --invoke-provider it is used as a fake "
            "generator, otherwise it is validated as a reviewed response"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-target-intake-dir",
        help=(
            "optional target-intake directory carrying normalized theorem "
            "objects, assumptions, procedure, claim, theorem shape, and search queries"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        help="optional current plan directory for context packet construction",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-library-coverage-map-dir",
        help="optional library coverage map directory for context packet construction",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-source-grounding-audit-dir",
        help="optional source-grounding audit directory for context packet construction",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-resource-request-queue-dir",
        help="optional resource-request queue directory carrying pending local/frontier tool dispatch packets",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-resource-response-ledger-dir",
        help="optional resource-response ledger directory carrying prover residuals",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-refinement-evidence-dir",
        help="optional refinement-evidence directory carrying literature, library, and proof-state feedback",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-route-revision-overlay-dir",
        help="optional route-revision overlay directory carrying accepted route repairs",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-route-replan-handoff-dir",
        help="optional route-replan handoff directory carrying replay and next-command context",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-interactive-session-dir",
        help="optional interactive-session directory carrying next-action and decision-policy context",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-component-resource-registry-dir",
        help="optional component-resource registry directory carrying available tool/resource contracts",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--out",
        default="runs/formalization_gap_planner_llm_route_planner",
        help="LLM route planner output directory",
    )
    formalization_gap_planner_llm_route_planner.set_defaults(
        func=_formalization_gap_planner_llm_route_planner
    )

    formalization_gap_planner_llm_route_planner_response_payload_validate = (
        sub.add_parser(
            "formalization-gap-planner-llm-route-planner-response-payload-validate",
            help=(
                "validate raw LLM route-planner response payload JSON against "
                "the reusable public payload schema"
            ),
        )
    )
    formalization_gap_planner_llm_route_planner_response_payload_validate.add_argument(
        "--input",
        required=True,
        help="raw payload JSON, wrapper response JSON, list, or responses bundle",
    )
    formalization_gap_planner_llm_route_planner_response_payload_validate.add_argument(
        "--request-context",
        default="",
        help=(
            "optional staged LLM route-planner request packet, request JSONL, "
            "manifest, or output directory for request-bound validation"
        ),
    )
    formalization_gap_planner_llm_route_planner_response_payload_validate.add_argument(
        "--out",
        default=(
            "runs/"
            "formalization_gap_planner_llm_route_planner_response_payload_validate"
        ),
        help="response-payload validation output directory",
    )
    formalization_gap_planner_llm_route_planner_response_payload_validate.set_defaults(
        func=_formalization_gap_planner_llm_route_planner_response_payload_validate
    )

    formalization_gap_planner_portable_plan_audit = sub.add_parser(
        "formalization-gap-planner-portable-plan-audit",
        help="audit a portable formalization-gap plan manifest before reuse",
    )
    formalization_gap_planner_portable_plan_audit.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_portable_plan_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_portable_plan_audit",
        help="portable plan audit output directory",
    )
    formalization_gap_planner_portable_plan_audit.set_defaults(
        func=_formalization_gap_planner_portable_plan_audit
    )

    formalization_gap_planner_library_coverage_map = sub.add_parser(
        "formalization-gap-planner-library-coverage-map",
        help="export per-primitive library coverage rows from a portable formalization-gap plan",
    )
    formalization_gap_planner_library_coverage_map.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_library_coverage_map.add_argument(
        "--out",
        default="runs/formalization_gap_planner_library_coverage_map",
        help="library coverage map output directory",
    )
    formalization_gap_planner_library_coverage_map.set_defaults(
        func=_formalization_gap_planner_library_coverage_map
    )

    formalization_gap_planner_primitive_action_queue = sub.add_parser(
        "formalization-gap-planner-primitive-action-queue",
        help="export executable primitive work orders from a library coverage map",
    )
    formalization_gap_planner_primitive_action_queue.add_argument(
        "--formalization-gap-planner-library-coverage-map-dir",
        required=True,
        help="directory containing formalization_gap_planner_library_coverage_map_manifest.json",
    )
    formalization_gap_planner_primitive_action_queue.add_argument(
        "--out",
        default="runs/formalization_gap_planner_primitive_action_queue",
        help="primitive action queue output directory",
    )
    formalization_gap_planner_primitive_action_queue.set_defaults(
        func=_formalization_gap_planner_primitive_action_queue
    )

    formalization_gap_planner_action_resource_plan = sub.add_parser(
        "formalization-gap-planner-action-resource-plan",
        help="join primitive formalization actions to local/frontier resources and contracts",
    )
    formalization_gap_planner_action_resource_plan.add_argument(
        "--formalization-gap-planner-primitive-action-queue-dir",
        required=True,
        help="directory containing formalization_gap_planner_primitive_action_queue_manifest.json",
    )
    formalization_gap_planner_action_resource_plan.add_argument(
        "--formalization-gap-planner-component-resource-registry-dir",
        required=True,
        help="directory containing formalization_gap_planner_component_resource_registry_manifest.json",
    )
    formalization_gap_planner_action_resource_plan.add_argument(
        "--out",
        default="runs/formalization_gap_planner_action_resource_plan",
        help="action resource plan output directory",
    )
    formalization_gap_planner_action_resource_plan.set_defaults(
        func=_formalization_gap_planner_action_resource_plan
    )

    formalization_gap_planner_resource_request_queue = sub.add_parser(
        "formalization-gap-planner-resource-request-queue",
        help="expand action-resource plans into per-resource local/frontier request packets",
    )
    formalization_gap_planner_resource_request_queue.add_argument(
        "--formalization-gap-planner-action-resource-plan-dir",
        required=True,
        help="directory containing formalization_gap_planner_action_resource_plan_manifest.json",
    )
    formalization_gap_planner_resource_request_queue.add_argument(
        "--formalization-gap-planner-llm-route-planner-dir",
        default="",
        help=(
            "optional directory containing "
            "formalization_gap_planner_llm_route_planner_manifest.json; "
            "search_requests and planner_next_actions are converted into "
            "bounded resource request packets"
        ),
    )
    formalization_gap_planner_resource_request_queue.add_argument(
        "--out",
        default="runs/formalization_gap_planner_resource_request_queue",
        help="resource request queue output directory",
    )
    formalization_gap_planner_resource_request_queue.set_defaults(
        func=_formalization_gap_planner_resource_request_queue
    )

    formalization_gap_planner_resource_response_ledger = sub.add_parser(
        "formalization-gap-planner-resource-response-ledger",
        help="validate local/frontier resource responses against resource request packets",
    )
    formalization_gap_planner_resource_response_ledger.add_argument(
        "--formalization-gap-planner-resource-request-queue-dir",
        required=True,
        help="directory containing formalization_gap_planner_resource_request_queue_manifest.json",
    )
    formalization_gap_planner_resource_response_ledger.add_argument(
        "--response-jsonl",
        help="optional JSONL of resource responses keyed by resource_request_id",
    )
    formalization_gap_planner_resource_response_ledger.add_argument(
        "--out",
        default="runs/formalization_gap_planner_resource_response_ledger",
        help="resource response ledger output directory",
    )
    formalization_gap_planner_resource_response_ledger.set_defaults(
        func=_formalization_gap_planner_resource_response_ledger
    )

    formalization_gap_planner_minimal_delta_audit = sub.add_parser(
        "formalization-gap-planner-minimal-delta-audit",
        help="audit costed route cuts for structural minimal Lean-delta discipline",
    )
    formalization_gap_planner_minimal_delta_audit.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_minimal_delta_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_minimal_delta_audit",
        help="minimal-delta audit output directory",
    )
    formalization_gap_planner_minimal_delta_audit.set_defaults(
        func=_formalization_gap_planner_minimal_delta_audit
    )

    formalization_gap_planner_source_grounding_audit = sub.add_parser(
        "formalization-gap-planner-source-grounding-audit",
        help="audit informal route-DAG nodes for source refs or bounded literature-search obligations",
    )
    formalization_gap_planner_source_grounding_audit.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_source_grounding_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_source_grounding_audit",
        help="source-grounding audit output directory",
    )
    formalization_gap_planner_source_grounding_audit.add_argument(
        "--formalization-gap-planner-refinement-evidence-dir",
        help=(
            "optional refinement evidence directory; when supplied, prover "
            "residual goals are audited for source refs, bounded literature "
            "search hooks, or explicit formal-gap boundaries"
        ),
    )
    formalization_gap_planner_source_grounding_audit.set_defaults(
        func=_formalization_gap_planner_source_grounding_audit
    )

    formalization_gap_planner_benchmark = sub.add_parser(
        "formalization-gap-planner-benchmark",
        help="export reusable route-truth labels for formalization-gap planner evaluation",
    )
    formalization_gap_planner_benchmark.add_argument(
        "--ground-truth",
        help="optional route-truth JSON file; defaults to the packaged benchmark file",
    )
    formalization_gap_planner_benchmark.add_argument(
        "--out",
        default="runs/formalization_gap_planner_benchmark",
        help="formalization-gap planner benchmark output directory",
    )
    formalization_gap_planner_benchmark.set_defaults(
        func=_formalization_gap_planner_benchmark
    )

    formalization_gap_planner_benchmark_audit = sub.add_parser(
        "formalization-gap-planner-benchmark-audit",
        help="audit route-truth benchmark quality, splits, sources, and proof boundary",
    )
    formalization_gap_planner_benchmark_audit.add_argument(
        "--formalization-gap-planner-benchmark-dir",
        required=True,
        help="directory containing formalization_gap_planner_benchmark_manifest.json",
    )
    formalization_gap_planner_benchmark_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_benchmark_audit",
        help="formalization-gap planner benchmark audit output directory",
    )
    formalization_gap_planner_benchmark_audit.set_defaults(
        func=_formalization_gap_planner_benchmark_audit
    )

    formalization_gap_planner_ablation_study = sub.add_parser(
        "formalization-gap-planner-ablation-study",
        help="compare route-planner metrics under no-literature/no-Lean/no-proof-feedback baselines",
    )
    formalization_gap_planner_ablation_study.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_ablation_study.add_argument(
        "--formalization-gap-planner-evaluation-dir",
        required=True,
        help="directory containing formalization_gap_planner_evaluation_manifest.json",
    )
    formalization_gap_planner_ablation_study.add_argument(
        "--formalization-gap-planner-interactive-session-dir",
        help="optional directory containing formalization_gap_planner_interactive_session_manifest.json",
    )
    formalization_gap_planner_ablation_study.add_argument(
        "--out",
        default="runs/formalization_gap_planner_ablation_study",
        help="formalization-gap planner ablation study output directory",
    )
    formalization_gap_planner_ablation_study.set_defaults(
        func=_formalization_gap_planner_ablation_study
    )

    formalization_gap_planner_interactive_session = sub.add_parser(
        "formalization-gap-planner-interactive-session",
        help="summarize the next bounded interaction for each planner route",
    )
    formalization_gap_planner_interactive_session.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_interactive_session.add_argument(
        "--formalization-gap-planner-refinement-queue-dir",
        help="optional directory containing formalization_gap_planner_refinement_queue_manifest.json",
    )
    formalization_gap_planner_interactive_session.add_argument(
        "--formalization-gap-planner-refinement-evidence-dir",
        help="optional directory containing formalization_gap_planner_refinement_evidence_manifest.json",
    )
    formalization_gap_planner_interactive_session.add_argument(
        "--formalization-gap-planner-route-stability-audit-dir",
        help="optional directory containing formalization_gap_planner_route_stability_audit_manifest.json",
    )
    formalization_gap_planner_interactive_session.add_argument(
        "--formalization-gap-planner-route-replan-handoff-dir",
        help="optional directory containing formalization_gap_planner_route_replan_handoff_manifest.json",
    )
    formalization_gap_planner_interactive_session.add_argument(
        "--formalization-gap-planner-proof-state-triage-dir",
        help="optional directory containing formalization_gap_planner_proof_state_triage_manifest.json",
    )
    formalization_gap_planner_interactive_session.add_argument(
        "--formalization-gap-planner-component-resource-registry-dir",
        help="optional directory containing formalization_gap_planner_component_resource_registry_manifest.json",
    )
    formalization_gap_planner_interactive_session.add_argument(
        "--out",
        default="runs/formalization_gap_planner_interactive_session",
        help="formalization-gap planner interactive session output directory",
    )
    formalization_gap_planner_interactive_session.set_defaults(
        func=_formalization_gap_planner_interactive_session
    )

    formalization_gap_planner_adapter_registry = sub.add_parser(
        "formalization-gap-planner-adapter-registry",
        help="export readiness and response contracts for formalization-gap planner adapters",
    )
    formalization_gap_planner_adapter_registry.add_argument(
        "--lean-rag-db",
        help="optional Lean RAG dependency graph SQLite DB for library-grounding readiness",
    )
    formalization_gap_planner_adapter_registry.add_argument(
        "--paper-library-dir",
        help="optional local paper/PDF/text corpus directory for PaperQA2 readiness",
    )
    formalization_gap_planner_adapter_registry.add_argument(
        "--out",
        default="runs/formalization_gap_planner_adapter_registry",
        help="formalization-gap planner adapter registry output directory",
    )
    formalization_gap_planner_adapter_registry.set_defaults(
        func=_formalization_gap_planner_adapter_registry
    )

    formalization_gap_planner_adapter_registry_audit = sub.add_parser(
        "formalization-gap-planner-adapter-registry-audit",
        help="audit adapter-registry coverage, response contracts, and proof boundary",
    )
    formalization_gap_planner_adapter_registry_audit.add_argument(
        "--formalization-gap-planner-adapter-registry-dir",
        required=True,
        help="directory containing formalization_gap_planner_adapter_registry_manifest.json",
    )
    formalization_gap_planner_adapter_registry_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_adapter_registry_audit",
        help="formalization-gap planner adapter registry audit output directory",
    )
    formalization_gap_planner_adapter_registry_audit.set_defaults(
        func=_formalization_gap_planner_adapter_registry_audit
    )

    formalization_gap_planner_component_resource_registry = sub.add_parser(
        "formalization-gap-planner-component-resource-registry",
        help="export component-to-resource coverage for the formalization-gap planner",
    )
    formalization_gap_planner_component_resource_registry.add_argument(
        "--formalization-gap-planner-adapter-registry-dir",
        help="optional adapter registry directory for adapter readiness annotations",
    )
    formalization_gap_planner_component_resource_registry.add_argument(
        "--out",
        default="runs/formalization_gap_planner_component_resource_registry",
        help="formalization-gap planner component resource registry output directory",
    )
    formalization_gap_planner_component_resource_registry.set_defaults(
        func=_formalization_gap_planner_component_resource_registry
    )

    formalization_gap_planner_component_resource_registry_audit = sub.add_parser(
        "formalization-gap-planner-component-resource-registry-audit",
        help="audit component-resource coverage, frontier tools, and proof boundary",
    )
    formalization_gap_planner_component_resource_registry_audit.add_argument(
        "--formalization-gap-planner-component-resource-registry-dir",
        required=True,
        help="directory containing formalization_gap_planner_component_resource_registry_manifest.json",
    )
    formalization_gap_planner_component_resource_registry_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_component_resource_registry_audit",
        help="formalization-gap planner component resource registry audit output directory",
    )
    formalization_gap_planner_component_resource_registry_audit.set_defaults(
        func=_formalization_gap_planner_component_resource_registry_audit
    )

    formalization_gap_planner_evaluation = sub.add_parser(
        "formalization-gap-planner-evaluation",
        help="score a goal-conditioned formalization-gap plan against route truth",
    )
    formalization_gap_planner_evaluation.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_evaluation.add_argument(
        "--ground-truth",
        required=True,
        help="route-truth JSON file, usually from formalization-gap-planner-benchmark",
    )
    formalization_gap_planner_evaluation.add_argument(
        "--out",
        default="runs/formalization_gap_planner_evaluation",
        help="formalization-gap planner evaluation output directory",
    )
    formalization_gap_planner_evaluation.set_defaults(
        func=_formalization_gap_planner_evaluation
    )

    formalization_gap_planner_refinement_queue = sub.add_parser(
        "formalization-gap-planner-refinement-queue",
        help="materialize interactive refinement work items from a gap-planner manifest",
    )
    formalization_gap_planner_refinement_queue.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_refinement_queue.add_argument(
        "--formalization-gap-planner-evaluation-dir",
        help="optional directory containing formalization_gap_planner_evaluation_manifest.json",
    )
    formalization_gap_planner_refinement_queue.add_argument(
        "--formal-verifier-replay-calibration-dir",
        help="optional directory containing formal_verifier_replay_calibration_manifest.json",
    )
    formalization_gap_planner_refinement_queue.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="limit exported refinement items; 0 keeps all",
    )
    formalization_gap_planner_refinement_queue.add_argument(
        "--out",
        default="runs/formalization_gap_planner_refinement_queue",
        help="formalization-gap planner refinement queue output directory",
    )
    formalization_gap_planner_refinement_queue.set_defaults(
        func=_formalization_gap_planner_refinement_queue
    )

    formalization_gap_planner_refinement_adapter_responses = sub.add_parser(
        "formalization-gap-planner-refinement-adapter-responses",
        help="produce deterministic local evidence responses for refinement queue rows",
    )
    formalization_gap_planner_refinement_adapter_responses.add_argument(
        "--formalization-gap-planner-refinement-queue-dir",
        required=True,
        help="directory containing formalization_gap_planner_refinement_queue_manifest.json",
    )
    formalization_gap_planner_refinement_adapter_responses.add_argument(
        "--ground-truth",
        help="optional route-truth JSON file; defaults to the packaged benchmark file",
    )
    formalization_gap_planner_refinement_adapter_responses.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="limit emitted responses; 0 keeps all queue rows",
    )
    formalization_gap_planner_refinement_adapter_responses.add_argument(
        "--out",
        default="runs/formalization_gap_planner_refinement_adapter",
        help="formalization-gap planner refinement adapter output directory",
    )
    formalization_gap_planner_refinement_adapter_responses.set_defaults(
        func=_formalization_gap_planner_refinement_adapter_responses
    )

    formalization_gap_planner_local_literature_adapter = sub.add_parser(
        "formalization-gap-planner-local-literature-adapter",
        help="emit literature-route evidence responses from a local text corpus",
    )
    formalization_gap_planner_local_literature_adapter.add_argument(
        "--formalization-gap-planner-refinement-queue-dir",
        required=True,
        help="directory containing formalization_gap_planner_refinement_queue_manifest.json",
    )
    formalization_gap_planner_local_literature_adapter.add_argument(
        "--literature-root",
        action="append",
        help="local text/markdown/json corpus root or file; repeatable",
    )
    formalization_gap_planner_local_literature_adapter.add_argument(
        "--base-response-jsonl",
        help="optional existing response JSONL to merge with local literature responses",
    )
    formalization_gap_planner_local_literature_adapter.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="limit queue rows scanned before filtering literature hooks; 0 keeps all",
    )
    formalization_gap_planner_local_literature_adapter.add_argument(
        "-k",
        type=int,
        default=5,
        help="local source hits per literature-discovery item",
    )
    formalization_gap_planner_local_literature_adapter.add_argument(
        "--max-file-bytes",
        type=int,
        default=1_000_000,
        help="maximum bytes read from each local corpus file",
    )
    formalization_gap_planner_local_literature_adapter.add_argument(
        "--out",
        default="runs/formalization_gap_planner_local_literature_adapter",
        help="local literature adapter output directory",
    )
    formalization_gap_planner_local_literature_adapter.set_defaults(
        func=_formalization_gap_planner_local_literature_adapter
    )

    formalization_gap_planner_local_formal_source_adapter = sub.add_parser(
        "formalization-gap-planner-local-formal-source-adapter",
        help="emit Lean-library-grounding responses from the local formal-source retriever",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "--formalization-gap-planner-refinement-queue-dir",
        required=True,
        help="directory containing formalization_gap_planner_refinement_queue_manifest.json",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "--formal-source-root",
        action="append",
        help="optional formal source root as id=/path or /path; repeatable",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "--formal-source-index-db",
        help="optional SQLite index path; defaults inside --out",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "--formal-source-index-cache",
        help="optional persistent formal-source SQLite cache",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "--refresh-formal-source-index-cache",
        action="store_true",
        help="rebuild the formal-source cache before searching",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "--lean-rag-db",
        help="optional Lean RAG dependency graph SQLite DB",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "--base-response-jsonl",
        help="optional existing response JSONL to merge with local Lean-grounding responses",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="limit queue rows scanned before filtering Lean-grounding hooks; 0 keeps all",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "-k",
        type=int,
        default=5,
        help="declaration hits per primitive",
    )
    formalization_gap_planner_local_formal_source_adapter.add_argument(
        "--out",
        default="runs/formalization_gap_planner_local_formal_source_adapter",
        help="local formal-source adapter output directory",
    )
    formalization_gap_planner_local_formal_source_adapter.set_defaults(
        func=_formalization_gap_planner_local_formal_source_adapter
    )

    formalization_gap_planner_local_proof_state_adapter = sub.add_parser(
        "formalization-gap-planner-local-proof-state-adapter",
        help="emit prover-feedback responses from local Lean proof-state checks",
    )
    formalization_gap_planner_local_proof_state_adapter.add_argument(
        "--formalization-gap-planner-refinement-queue-dir",
        required=True,
        help="directory containing formalization_gap_planner_refinement_queue_manifest.json",
    )
    formalization_gap_planner_local_proof_state_adapter.add_argument(
        "--lean-project",
        help="optional Lake project; when set the adapter runs lake env lean",
    )
    formalization_gap_planner_local_proof_state_adapter.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each local Lean proof-state probe",
    )
    formalization_gap_planner_local_proof_state_adapter.add_argument(
        "--base-response-jsonl",
        help="optional existing response JSONL to merge with local proof-state responses",
    )
    formalization_gap_planner_local_proof_state_adapter.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="limit queue rows scanned before filtering proof-state hooks; 0 keeps all",
    )
    formalization_gap_planner_local_proof_state_adapter.add_argument(
        "--out",
        default="runs/formalization_gap_planner_local_proof_state_adapter",
        help="local proof-state adapter output directory",
    )
    formalization_gap_planner_local_proof_state_adapter.set_defaults(
        func=_formalization_gap_planner_local_proof_state_adapter
    )

    formalization_gap_planner_prover_adapter_feedback = sub.add_parser(
        "formalization-gap-planner-prover-adapter-feedback",
        help=(
            "convert target-prover adapter validation rows into refinement "
            "prover-feedback responses"
        ),
    )
    formalization_gap_planner_prover_adapter_feedback.add_argument(
        "--formalization-gap-planner-refinement-queue-dir",
        required=True,
        help="directory containing formalization_gap_planner_refinement_queue_manifest.json",
    )
    formalization_gap_planner_prover_adapter_feedback.add_argument(
        "--formalization-gap-planner-prover-adapter-contract-dir",
        help="optional directory containing prover-adapter response-validation JSONL",
    )
    formalization_gap_planner_prover_adapter_feedback.add_argument(
        "--formalization-gap-planner-cross-prover-matrix-audit-dir",
        help="optional directory containing aggregate cross-prover response-validation JSONL",
    )
    formalization_gap_planner_prover_adapter_feedback.add_argument(
        "--base-response-jsonl",
        help="optional existing response JSONL to merge with target-prover feedback",
    )
    formalization_gap_planner_prover_adapter_feedback.add_argument(
        "--target-prover-family",
        default="",
        help="optional target prover family filter such as lean4, rocq, isabelle, or agda",
    )
    formalization_gap_planner_prover_adapter_feedback.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="limit queue rows scanned before filtering proof-state hooks; 0 keeps all",
    )
    formalization_gap_planner_prover_adapter_feedback.add_argument(
        "--out",
        default="runs/formalization_gap_planner_prover_adapter_feedback_adapter",
        help="prover-adapter feedback output directory",
    )
    formalization_gap_planner_prover_adapter_feedback.set_defaults(
        func=_formalization_gap_planner_prover_adapter_feedback
    )

    formalization_gap_planner_minimal_delta_audit_feedback = sub.add_parser(
        "formalization-gap-planner-minimal-delta-audit-feedback",
        help=(
            "convert failed minimal-delta audit decisions into route-revision "
            "refinement responses"
        ),
    )
    formalization_gap_planner_minimal_delta_audit_feedback.add_argument(
        "--formalization-gap-planner-refinement-queue-dir",
        required=True,
        help="directory containing formalization_gap_planner_refinement_queue_manifest.json",
    )
    formalization_gap_planner_minimal_delta_audit_feedback.add_argument(
        "--formalization-gap-planner-minimal-delta-audit-dir",
        required=True,
        help="directory containing formalization_gap_planner_minimal_delta_audit_manifest.json",
    )
    formalization_gap_planner_minimal_delta_audit_feedback.add_argument(
        "--base-response-jsonl",
        help="optional existing response JSONL to merge with minimal-delta audit feedback",
    )
    formalization_gap_planner_minimal_delta_audit_feedback.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="limit queue rows scanned before filtering route-revision hooks; 0 keeps all",
    )
    formalization_gap_planner_minimal_delta_audit_feedback.add_argument(
        "--out",
        default="runs/formalization_gap_planner_minimal_delta_audit_feedback_adapter",
        help="minimal-delta audit feedback output directory",
    )
    formalization_gap_planner_minimal_delta_audit_feedback.set_defaults(
        func=_formalization_gap_planner_minimal_delta_audit_feedback
    )

    formalization_gap_planner_refinement_evidence = sub.add_parser(
        "formalization-gap-planner-refinement-evidence",
        help="validate refinement tool responses and emit route-revision proposals",
    )
    formalization_gap_planner_refinement_evidence.add_argument(
        "--formalization-gap-planner-refinement-queue-dir",
        required=True,
        help="directory containing formalization_gap_planner_refinement_queue_manifest.json",
    )
    formalization_gap_planner_refinement_evidence.add_argument(
        "--response-jsonl",
        help="optional response JSONL; defaults to the queue directory response filename",
    )
    formalization_gap_planner_refinement_evidence.add_argument(
        "--out",
        default="runs/formalization_gap_planner_refinement_evidence",
        help="formalization-gap planner refinement evidence output directory",
    )
    formalization_gap_planner_refinement_evidence.set_defaults(
        func=_formalization_gap_planner_refinement_evidence
    )

    formalization_gap_planner_route_revision_overlay = sub.add_parser(
        "formalization-gap-planner-route-revision-overlay",
        help="apply refinement evidence proposals back onto goal-conditioned route plans",
    )
    formalization_gap_planner_route_revision_overlay.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_route_revision_overlay.add_argument(
        "--formalization-gap-planner-refinement-evidence-dir",
        required=True,
        help="directory containing formalization_gap_planner_refinement_evidence_manifest.json",
    )
    formalization_gap_planner_route_revision_overlay.add_argument(
        "--formalization-gap-planner-resource-response-ledger-dir",
        help=(
            "optional directory containing "
            "formalization_gap_planner_resource_response_ledger_manifest.json; "
            "accepted responses with route feedback are applied as overlay proposals"
        ),
    )
    formalization_gap_planner_route_revision_overlay.add_argument(
        "--out",
        default="runs/formalization_gap_planner_route_revision_overlay",
        help="formalization-gap planner route revision overlay output directory",
    )
    formalization_gap_planner_route_revision_overlay.set_defaults(
        func=_formalization_gap_planner_route_revision_overlay
    )

    formalization_gap_planner_route_stability_audit = sub.add_parser(
        "formalization-gap-planner-route-stability-audit",
        help="decide whether each route has stabilized or needs bounded evidence expansion",
    )
    formalization_gap_planner_route_stability_audit.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_route_stability_audit.add_argument(
        "--formalization-gap-planner-refinement-evidence-dir",
        required=True,
        help="directory containing formalization_gap_planner_refinement_evidence_manifest.json",
    )
    formalization_gap_planner_route_stability_audit.add_argument(
        "--formalization-gap-planner-route-revision-overlay-dir",
        required=True,
        help="directory containing formalization_gap_planner_route_revision_overlay_manifest.json",
    )
    formalization_gap_planner_route_stability_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_route_stability_audit",
        help="formalization-gap planner route-stability audit output directory",
    )
    formalization_gap_planner_route_stability_audit.set_defaults(
        func=_formalization_gap_planner_route_stability_audit
    )

    formalization_gap_planner_route_replan_handoff = sub.add_parser(
        "formalization-gap-planner-route-replan-handoff",
        help="write a replayable standalone seed from route-revision overlay rows",
    )
    formalization_gap_planner_route_replan_handoff.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_route_replan_handoff.add_argument(
        "--formalization-gap-planner-route-revision-overlay-dir",
        required=True,
        help="directory containing formalization_gap_planner_route_revision_overlay_manifest.json",
    )
    formalization_gap_planner_route_replan_handoff.add_argument(
        "--formalization-gap-planner-route-stability-audit-dir",
        help="optional directory containing formalization_gap_planner_route_stability_audit_manifest.json",
    )
    formalization_gap_planner_route_replan_handoff.add_argument(
        "--target-prover-family",
        default="",
        help="optional target prover family override for the standalone replan seed",
    )
    formalization_gap_planner_route_replan_handoff.add_argument(
        "--library-snapshot-ref",
        default="",
        help="optional library snapshot ref override for the standalone replan seed",
    )
    formalization_gap_planner_route_replan_handoff.add_argument(
        "--out",
        default="runs/formalization_gap_planner_route_replan_handoff",
        help="route-replan handoff output directory",
    )
    formalization_gap_planner_route_replan_handoff.set_defaults(
        func=_formalization_gap_planner_route_replan_handoff
    )

    formalization_gap_planner_route_replan_handoff_audit = sub.add_parser(
        "formalization-gap-planner-route-replan-handoff-audit",
        help="audit a route-replan handoff and replay its standalone planner seed",
    )
    formalization_gap_planner_route_replan_handoff_audit.add_argument(
        "--formalization-gap-planner-route-replan-handoff-dir",
        required=True,
        help="directory containing formalization_gap_planner_route_replan_handoff_manifest.json",
    )
    formalization_gap_planner_route_replan_handoff_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_route_replan_handoff_audit",
        help="route-replan handoff audit output directory",
    )
    formalization_gap_planner_route_replan_handoff_audit.set_defaults(
        func=_formalization_gap_planner_route_replan_handoff_audit
    )

    formalization_gap_planner_runtime_handoff_audit = sub.add_parser(
        "formalization-gap-planner-runtime-handoff-audit",
        help=(
            "audit AI Statistician runtime formalization-gap planner handoffs "
            "and offline prompt-only LLM route-planner replay"
        ),
    )
    formalization_gap_planner_runtime_handoff_audit.add_argument(
        "--runtime-formalization-gap-planner-handoffs-jsonl",
        required=True,
        help="runtime_formalization_gap_planner_handoffs.jsonl emitted by research-agent-runtime",
    )
    formalization_gap_planner_runtime_handoff_audit.add_argument(
        "--no-smoke",
        action="store_true",
        help="skip offline standalone and prompt-only LLM route-planner smoke replay",
    )
    formalization_gap_planner_runtime_handoff_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_runtime_handoff_audit",
        help="runtime handoff audit output directory",
    )
    formalization_gap_planner_runtime_handoff_audit.set_defaults(
        func=_formalization_gap_planner_runtime_handoff_audit
    )

    formalization_gap_planner_proof_state_triage = sub.add_parser(
        "formalization-gap-planner-proof-state-triage",
        help="rank route-level proof-state statuses into proof-worker triage items",
    )
    formalization_gap_planner_proof_state_triage.add_argument(
        "--formalization-gap-planner-route-revision-overlay-dir",
        required=True,
        help="directory containing formalization_gap_planner_route_revision_overlay_manifest.json",
    )
    formalization_gap_planner_proof_state_triage.add_argument(
        "--out",
        default="runs/formalization_gap_planner_proof_state_triage",
        help="proof-state triage output directory",
    )
    formalization_gap_planner_proof_state_triage.set_defaults(
        func=_formalization_gap_planner_proof_state_triage
    )

    formalization_gap_planner_publication_bundle = sub.add_parser(
        "formalization-gap-planner-publication-bundle",
        help="write a reusable publication bundle for the library-aware formalization gap planner",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--ground-truth",
        help="optional route-truth JSON file; defaults to the packaged benchmark file",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--lean-rag-db",
        help="optional Lean RAG dependency graph SQLite DB for adapter-registry readiness",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--paper-library-dir",
        help="optional local paper/text corpus directory for adapter-registry readiness",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-target-intake-dir",
        help="optional target-intake directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-llm-route-planner-dir",
        help="optional primary LLM route-planner directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-feedback-llm-route-planner-dir",
        help="optional feedback LLM route-planner directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-llm-route-planner-response-payload-validation-dir",
        help=(
            "optional LLM route-planner response-payload validation directory "
            "to copy into the bundle"
        ),
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        help="optional planner run directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-evaluation-dir",
        help="optional planner evaluation directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-ablation-study-dir",
        help="optional planner ablation-study directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-portable-plan-audit-dir",
        help="optional portable plan audit directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-library-coverage-map-dir",
        help="optional library coverage-map directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-primitive-action-queue-dir",
        help="optional primitive action-queue directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-action-resource-plan-dir",
        help="optional action-resource plan directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-resource-request-queue-dir",
        help="optional resource request-queue directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-resource-response-ledger-dir",
        help="optional resource response-ledger directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-minimal-delta-audit-dir",
        help="optional minimal-delta audit directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-minimal-delta-audit-feedback-adapter-dir",
        help="optional minimal-delta audit feedback-adapter response directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-source-grounding-audit-dir",
        help="optional source-grounding audit directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-refinement-queue-dir",
        help="optional refinement queue directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-refinement-adapter-dir",
        help="optional deterministic refinement-adapter response directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-local-literature-adapter-dir",
        help="optional local literature-adapter response directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-local-formal-source-adapter-dir",
        help="optional local formal-source-adapter response directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-local-proof-state-adapter-dir",
        help="optional local proof-state-adapter response directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-prover-adapter-feedback-adapter-dir",
        help="optional target-prover feedback-adapter response directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-refinement-evidence-dir",
        help="optional refinement evidence directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-route-revision-overlay-dir",
        help="optional route-revision overlay directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-route-stability-audit-dir",
        help="optional route-stability audit directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-route-replan-handoff-dir",
        help="optional route-replan handoff directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-route-replan-handoff-audit-dir",
        help="optional route-replan handoff audit directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-runtime-handoff-audit-dir",
        help="optional AI Statistician runtime handoff audit directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-proof-state-triage-dir",
        help="optional proof-state triage directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-interactive-session-dir",
        help="optional interactive-session directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-prover-adapter-contract-dir",
        help="optional prover-adapter contract directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-cross-prover-matrix-audit-dir",
        help="optional cross-prover matrix audit directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-adapter-registry-audit-dir",
        help="optional adapter-registry audit directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--formalization-gap-planner-component-resource-registry-audit-dir",
        help="optional component-resource-registry audit directory to copy into the bundle",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--library-snapshot-ref",
        default="portable_publication_bundle",
        help="library snapshot label written into the portable contract",
    )
    formalization_gap_planner_publication_bundle.add_argument(
        "--out",
        default="runs/formalization_gap_planner_publication_bundle",
        help="publication bundle output directory",
    )
    formalization_gap_planner_publication_bundle.set_defaults(
        func=_formalization_gap_planner_publication_bundle
    )

    formalization_gap_planner_publication_bundle_audit = sub.add_parser(
        "formalization-gap-planner-publication-bundle-audit",
        help="audit a formalization-gap planner publication bundle for reuse readiness",
    )
    formalization_gap_planner_publication_bundle_audit.add_argument(
        "--publication-bundle-dir",
        required=True,
        help="directory containing formalization_gap_planner_publication_bundle_manifest.json",
    )
    formalization_gap_planner_publication_bundle_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_publication_bundle_audit",
        help="publication bundle audit output directory",
    )
    formalization_gap_planner_publication_bundle_audit.set_defaults(
        func=_formalization_gap_planner_publication_bundle_audit
    )

    formalization_gap_planner_prover_adapter_contract = sub.add_parser(
        "formalization-gap-planner-prover-adapter-contract",
        help="export portable work-packet mappings and validate target-prover adapter responses",
    )
    formalization_gap_planner_prover_adapter_contract.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_prover_adapter_contract.add_argument(
        "--target-prover-family",
        default="other",
        choices=["lean4", "lean", "rocq", "coq", "isabelle", "isabelle/hol", "agda", "other"],
        help="target prover ecosystem for adapter mapping packets",
    )
    formalization_gap_planner_prover_adapter_contract.add_argument(
        "--library-snapshot-ref",
        default="",
        help="target-prover library snapshot label written into adapter packets",
    )
    formalization_gap_planner_prover_adapter_contract.add_argument(
        "--adapter-response-jsonl",
        help="optional target-prover adapter response JSONL to validate",
    )
    formalization_gap_planner_prover_adapter_contract.add_argument(
        "--max-packets",
        type=int,
        default=0,
        help="limit exported portable work packets; 0 keeps all",
    )
    formalization_gap_planner_prover_adapter_contract.add_argument(
        "--out",
        default="runs/formalization_gap_planner_prover_adapter_contract",
        help="prover adapter contract output directory",
    )
    formalization_gap_planner_prover_adapter_contract.set_defaults(
        func=_formalization_gap_planner_prover_adapter_contract
    )

    formalization_gap_planner_cross_prover_matrix_audit = sub.add_parser(
        "formalization-gap-planner-cross-prover-matrix-audit",
        help="audit portable work-packet emission across Lean4, Rocq, Isabelle, and Agda",
    )
    formalization_gap_planner_cross_prover_matrix_audit.add_argument(
        "--goal-conditioned-minimal-formalization-plan-dir",
        required=True,
        help="directory containing goal_conditioned_minimal_formalization_plan_manifest.json",
    )
    formalization_gap_planner_cross_prover_matrix_audit.add_argument(
        "--target-prover-family",
        action="append",
        choices=["lean4", "lean", "rocq", "coq", "isabelle", "isabelle/hol", "agda"],
        help="target prover family to include; repeatable, defaults to lean4/rocq/isabelle/agda",
    )
    formalization_gap_planner_cross_prover_matrix_audit.add_argument(
        "--library-snapshot-ref-prefix",
        default="cross_prover_matrix",
        help="prefix for per-prover library snapshot labels",
    )
    formalization_gap_planner_cross_prover_matrix_audit.add_argument(
        "--max-packets",
        type=int,
        default=0,
        help="limit exported portable work packets per target; 0 keeps all",
    )
    formalization_gap_planner_cross_prover_matrix_audit.add_argument(
        "--out",
        default="runs/formalization_gap_planner_cross_prover_matrix_audit",
        help="cross-prover matrix audit output directory",
    )
    formalization_gap_planner_cross_prover_matrix_audit.set_defaults(
        func=_formalization_gap_planner_cross_prover_matrix_audit
    )

    formal_verifier_replay = sub.add_parser(
        "formal-verifier-replay-export",
        help="export route-level FormalVerifier replay tasks from a verifier queue",
    )
    formal_verifier_replay.add_argument(
        "--formal-verifier-queue-dir",
        required=True,
        help="directory containing formal_verifier_queue_manifest.json",
    )
    formal_verifier_replay.add_argument("--max-tasks", type=int, default=20)
    formal_verifier_replay.add_argument(
        "--out",
        default="runs/formal_verifier_replay",
        help="formal-verifier replay output directory",
    )
    formal_verifier_replay.set_defaults(func=_formal_verifier_replay_export)

    formal_verifier_replay_attempts = sub.add_parser(
        "formal-verifier-replay-attempts",
        help="run full theorem/bridge replay attempts and write verifier feedback JSONL",
    )
    formal_verifier_replay_attempts.add_argument(
        "--formal-verifier-replay-dir",
        required=True,
        help="directory containing formal_verifier_replay_manifest.json",
    )
    formal_verifier_replay_attempts.add_argument(
        "--formal-gap-tasks-dir",
        help="optional directory containing formal_gap_lean_task_manifest.json for real skeleton statements",
    )
    formal_verifier_replay_attempts.add_argument("--max-tasks", type=int, default=3)
    formal_verifier_replay_attempts.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof")
    formal_verifier_replay_attempts.add_argument("--local-lean", action="store_true", help="use local lake env lean")
    formal_verifier_replay_attempts.add_argument("--lean-project", help="local Lake project used by --local-lean")
    formal_verifier_replay_attempts.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each local Lean check",
    )
    formal_verifier_replay_attempts.add_argument(
        "--out",
        default="runs/formal_verifier_replay_attempts",
        help="formal-verifier replay attempt output directory",
    )
    formal_verifier_replay_attempts.add_argument("--env-file", default=".env")
    formal_verifier_replay_attempts.set_defaults(
        func=lambda args: asyncio.run(_formal_verifier_replay_attempts(args))
    )

    formal_verifier_replay_calibration = sub.add_parser(
        "formal-verifier-replay-calibration",
        help="calibrate FormalVerifier replay tasks against full-route proof attempt feedback",
    )
    formal_verifier_replay_calibration.add_argument(
        "--formal-verifier-replay-dir",
        required=True,
        help="directory containing formal_verifier_replay_manifest.json",
    )
    formal_verifier_replay_calibration.add_argument(
        "--attempt-log",
        help="optional JSONL of full theorem/bridge replay proof attempts",
    )
    formal_verifier_replay_calibration.add_argument(
        "--out",
        default="runs/formal_verifier_replay_calibration",
        help="formal-verifier replay calibration output directory",
    )
    formal_verifier_replay_calibration.set_defaults(func=_formal_verifier_replay_calibration)

    formal_verifier_replay_repair = sub.add_parser(
        "formal-verifier-replay-repair-export",
        help="export route-specific repair packets from failed FormalVerifier replay attempts",
    )
    formal_verifier_replay_repair.add_argument(
        "--formal-verifier-replay-dir",
        required=True,
        help="directory containing formal_verifier_replay_manifest.json",
    )
    formal_verifier_replay_repair.add_argument(
        "--formal-verifier-replay-attempt-dir",
        required=True,
        help="directory containing formal_verifier_replay_attempt_manifest.json",
    )
    formal_verifier_replay_repair.add_argument(
        "--formal-verifier-replay-calibration-dir",
        required=True,
        help="directory containing formal_verifier_replay_calibration_manifest.json",
    )
    formal_verifier_replay_repair.add_argument("--max-packets", type=int, default=20)
    formal_verifier_replay_repair.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair",
        help="formal-verifier replay repair packet output directory",
    )
    formal_verifier_replay_repair.set_defaults(func=_formal_verifier_replay_repair_export)

    formal_verifier_replay_repair_application = sub.add_parser(
        "formal-verifier-replay-repair-application-export",
        help="export Lean repair-application scaffolds from FormalVerifier replay repair packets",
    )
    formal_verifier_replay_repair_application.add_argument(
        "--formal-verifier-replay-repair-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_manifest.json",
    )
    formal_verifier_replay_repair_application.add_argument(
        "--formal-verifier-replay-attempt-dir",
        required=True,
        help="directory containing formal_verifier_replay_attempt_manifest.json",
    )
    formal_verifier_replay_repair_application.add_argument("--max-tasks", type=int, default=20)
    formal_verifier_replay_repair_application.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_application",
        help="formal-verifier replay repair application output directory",
    )
    formal_verifier_replay_repair_application.set_defaults(
        func=_formal_verifier_replay_repair_application_export
    )

    formal_verifier_replay_repair_application_validation = sub.add_parser(
        "formal-verifier-replay-repair-application-validation",
        help="validate Lean repair-application scaffolds as non-evidence source artifacts",
    )
    formal_verifier_replay_repair_application_validation.add_argument(
        "--formal-verifier-replay-repair-application-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_application_manifest.json",
    )
    formal_verifier_replay_repair_application_validation.add_argument(
        "--lean-project",
        default=None,
        help="optional local Lean project for lake env lean scaffold compilation",
    )
    formal_verifier_replay_repair_application_validation.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout in seconds for each optional local Lean scaffold compile",
    )
    formal_verifier_replay_repair_application_validation.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_application_validation",
        help="formal-verifier replay repair application validation output directory",
    )
    formal_verifier_replay_repair_application_validation.set_defaults(
        func=_formal_verifier_replay_repair_application_validation
    )

    formal_verifier_replay_repair_execution_queue = sub.add_parser(
        "formal-verifier-replay-repair-execution-queue",
        help="export ranked repair-patch work orders from validated replay scaffolds",
    )
    formal_verifier_replay_repair_execution_queue.add_argument(
        "--formal-verifier-replay-repair-application-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_application_manifest.json",
    )
    formal_verifier_replay_repair_execution_queue.add_argument(
        "--formal-verifier-replay-repair-application-validation-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_application_validation_manifest.json",
    )
    formal_verifier_replay_repair_execution_queue.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_execution_queue",
        help="formal-verifier replay repair execution queue output directory",
    )
    formal_verifier_replay_repair_execution_queue.set_defaults(
        func=_formal_verifier_replay_repair_execution_queue
    )

    formal_verifier_replay_repair_prompt_packets = sub.add_parser(
        "formal-verifier-replay-repair-prompt-packets",
        help="export prover/RAG prompt packets from ready repair execution queue items",
    )
    formal_verifier_replay_repair_prompt_packets.add_argument(
        "--formal-verifier-replay-repair-execution-queue-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_execution_queue_manifest.json",
    )
    formal_verifier_replay_repair_prompt_packets.add_argument(
        "--formal-verifier-replay-repair-application-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_application_manifest.json",
    )
    formal_verifier_replay_repair_prompt_packets.add_argument("--max-packets", type=int, default=20)
    formal_verifier_replay_repair_prompt_packets.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_prompt_packets",
        help="formal-verifier replay repair prompt packet output directory",
    )
    formal_verifier_replay_repair_prompt_packets.set_defaults(
        func=_formal_verifier_replay_repair_prompt_packets
    )

    formal_verifier_replay_repair_patch_autoworker = sub.add_parser(
        "formal-verifier-replay-repair-patch-autoworker",
        help="generate conservative local repair patch responses from prompt packets",
    )
    formal_verifier_replay_repair_patch_autoworker.add_argument(
        "--formal-verifier-replay-repair-prompt-packets-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_prompt_packets_manifest.json",
    )
    formal_verifier_replay_repair_patch_autoworker.add_argument(
        "--max-responses",
        type=int,
        default=20,
        help="maximum prompt packets to answer with patch proposals",
    )
    formal_verifier_replay_repair_patch_autoworker.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_autoworker",
        help="formal-verifier repair patch autoworker output directory",
    )
    formal_verifier_replay_repair_patch_autoworker.set_defaults(
        func=_formal_verifier_replay_repair_patch_autoworker
    )

    formal_verifier_replay_repair_patch_response_validation = sub.add_parser(
        "formal-verifier-replay-repair-patch-response-validation",
        help="validate prover/RAG repair patch responses against prompt-packet proof-evidence gates",
    )
    formal_verifier_replay_repair_patch_response_validation.add_argument(
        "--formal-verifier-replay-repair-prompt-packets-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_prompt_packets_manifest.json",
    )
    formal_verifier_replay_repair_patch_response_validation.add_argument(
        "--response-jsonl",
        default="",
        help="optional JSONL of worker repair patch responses; defaults to the prompt-packet directory",
    )
    formal_verifier_replay_repair_patch_response_validation.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_response_validation",
        help="formal-verifier repair patch response validation output directory",
    )
    formal_verifier_replay_repair_patch_response_validation.set_defaults(
        func=_formal_verifier_replay_repair_patch_response_validation
    )

    formal_verifier_replay_repair_patch_response_promotion = sub.add_parser(
        "formal-verifier-replay-repair-patch-response-promotion",
        help="export proof-ledger promotion rows from validated repair patch responses",
    )
    formal_verifier_replay_repair_patch_response_promotion.add_argument(
        "--formal-verifier-replay-repair-patch-response-validation-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_response_validation_manifest.json",
    )
    formal_verifier_replay_repair_patch_response_promotion.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_response_promotion",
        help="formal-verifier repair patch response promotion output directory",
    )
    formal_verifier_replay_repair_patch_response_promotion.set_defaults(
        func=_formal_verifier_replay_repair_patch_response_promotion
    )

    formal_verifier_replay_repair_patch_rerun_queue = sub.add_parser(
        "formal-verifier-replay-repair-patch-rerun-queue",
        help="export replay-calibration queue rows from validated repair patch proposals",
    )
    formal_verifier_replay_repair_patch_rerun_queue.add_argument(
        "--formal-verifier-replay-repair-patch-response-validation-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_response_validation_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_queue.add_argument(
        "--formal-verifier-replay-repair-patch-response-promotion-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_response_promotion_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_queue.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_rerun_queue",
        help="formal-verifier repair patch rerun queue output directory",
    )
    formal_verifier_replay_repair_patch_rerun_queue.set_defaults(
        func=_formal_verifier_replay_repair_patch_rerun_queue
    )

    formal_verifier_replay_repair_patch_rerun_attempts = sub.add_parser(
        "formal-verifier-replay-repair-patch-rerun-attempts",
        help="run local Lean checks for queued repair patch artifacts",
    )
    formal_verifier_replay_repair_patch_rerun_attempts.add_argument(
        "--formal-verifier-replay-repair-patch-rerun-queue-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_rerun_queue_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_attempts.add_argument(
        "--lean-project",
        help="local Lake project used to run lake env lean on patched artifacts",
    )
    formal_verifier_replay_repair_patch_rerun_attempts.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout in seconds for each patched artifact Lean check",
    )
    formal_verifier_replay_repair_patch_rerun_attempts.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="maximum ready queue items to attempt; 0 means all ready items",
    )
    formal_verifier_replay_repair_patch_rerun_attempts.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_rerun_attempts",
        help="formal-verifier repair patch rerun attempt output directory",
    )
    formal_verifier_replay_repair_patch_rerun_attempts.set_defaults(
        func=_formal_verifier_replay_repair_patch_rerun_attempts
    )

    formal_verifier_replay_repair_patch_rerun_calibration = sub.add_parser(
        "formal-verifier-replay-repair-patch-rerun-calibration",
        help="calibrate patch-rerun attempts before proof-ledger promotion",
    )
    formal_verifier_replay_repair_patch_rerun_calibration.add_argument(
        "--formal-verifier-replay-repair-patch-rerun-queue-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_rerun_queue_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_calibration.add_argument(
        "--formal-verifier-replay-repair-patch-rerun-attempt-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_rerun_attempt_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_calibration.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_rerun_calibration",
        help="formal-verifier repair patch rerun calibration output directory",
    )
    formal_verifier_replay_repair_patch_rerun_calibration.set_defaults(
        func=_formal_verifier_replay_repair_patch_rerun_calibration
    )

    formal_verifier_replay_repair_patch_rerun_residual_obligations = sub.add_parser(
        "formal-verifier-replay-repair-patch-rerun-residual-obligations",
        help="export residual proof/library obligations from unverified patch-rerun calibration rows",
    )
    formal_verifier_replay_repair_patch_rerun_residual_obligations.add_argument(
        "--formal-verifier-replay-repair-patch-rerun-calibration-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_rerun_calibration_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_residual_obligations.add_argument(
        "--primitive-source-coverage-dir",
        required=True,
        help="directory containing primitive_source_coverage_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_residual_obligations.add_argument(
        "--proof-bank-actions-dir",
        required=True,
        help="directory containing proof_bank_action_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_residual_obligations.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_rerun_residual_obligations",
        help="formal-verifier repair patch rerun residual-obligation output directory",
    )
    formal_verifier_replay_repair_patch_rerun_residual_obligations.set_defaults(
        func=_formal_verifier_replay_repair_patch_rerun_residual_obligations
    )

    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets = sub.add_parser(
        "formal-verifier-replay-repair-patch-rerun-residual-prompt-packets",
        help="export prover/RAG prompt packets for patch-rerun residual obligations",
    )
    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.add_argument(
        "--formal-verifier-replay-repair-patch-rerun-residual-obligations-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_rerun_residual_obligations_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.add_argument(
        "--max-packets",
        type=int,
        default=40,
    )
    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_rerun_residual_prompt_packets",
        help="formal-verifier repair patch rerun residual prompt-packet output directory",
    )
    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.set_defaults(
        func=_formal_verifier_replay_repair_patch_rerun_residual_prompt_packets
    )

    formal_verifier_replay_repair_patch_rerun_residual_autoworker = sub.add_parser(
        "formal-verifier-replay-repair-patch-rerun-residual-autoworker",
        help="generate conservative local responses for patch-rerun residual prompt packets",
    )
    formal_verifier_replay_repair_patch_rerun_residual_autoworker.add_argument(
        "--formal-verifier-replay-repair-patch-rerun-residual-prompt-packets-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_residual_autoworker.add_argument(
        "--max-responses",
        type=int,
        default=40,
    )
    formal_verifier_replay_repair_patch_rerun_residual_autoworker.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_rerun_residual_autoworker",
        help="formal-verifier repair patch rerun residual autoworker output directory",
    )
    formal_verifier_replay_repair_patch_rerun_residual_autoworker.set_defaults(
        func=_formal_verifier_replay_repair_patch_rerun_residual_autoworker
    )

    formal_verifier_replay_repair_patch_rerun_residual_response_validation = (
        sub.add_parser(
            "formal-verifier-replay-repair-patch-rerun-residual-response-validation",
            help="validate worker responses to patch-rerun residual prompt packets",
        )
    )
    formal_verifier_replay_repair_patch_rerun_residual_response_validation.add_argument(
        "--formal-verifier-replay-repair-patch-rerun-residual-prompt-packets-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_residual_response_validation.add_argument(
        "--response-jsonl",
        default="",
        help="optional JSONL file of residual worker responses",
    )
    formal_verifier_replay_repair_patch_rerun_residual_response_validation.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_rerun_residual_response_validation",
        help="formal-verifier repair patch rerun residual response-validation output directory",
    )
    formal_verifier_replay_repair_patch_rerun_residual_response_validation.set_defaults(
        func=_formal_verifier_replay_repair_patch_rerun_residual_response_validation
    )

    formal_verifier_replay_repair_patch_rerun_residual_followup_queue = (
        sub.add_parser(
            "formal-verifier-replay-repair-patch-rerun-residual-followup-queue",
            help="queue follow-up work from validated patch-rerun residual responses",
        )
    )
    formal_verifier_replay_repair_patch_rerun_residual_followup_queue.add_argument(
        "--formal-verifier-replay-repair-patch-rerun-residual-response-validation-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest.json",
    )
    formal_verifier_replay_repair_patch_rerun_residual_followup_queue.add_argument(
        "--out",
        default="runs/formal_verifier_replay_repair_patch_rerun_residual_followup_queue",
        help="formal-verifier repair patch rerun residual follow-up queue output directory",
    )
    formal_verifier_replay_repair_patch_rerun_residual_followup_queue.set_defaults(
        func=_formal_verifier_replay_repair_patch_rerun_residual_followup_queue
    )

    formal_verifier_agentic_proof_strategy_plan = sub.add_parser(
        "formal-verifier-agentic-proof-strategy-plan",
        help="plan agentic proof-search strategies from residual follow-up queue items",
    )
    formal_verifier_agentic_proof_strategy_plan.add_argument(
        "--formal-verifier-replay-repair-patch-rerun-residual-followup-queue-dir",
        required=True,
        help="directory containing formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest.json",
    )
    formal_verifier_agentic_proof_strategy_plan.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_strategy_plan",
        help="formal-verifier agentic proof strategy plan output directory",
    )
    formal_verifier_agentic_proof_strategy_plan.add_argument(
        "--rag-collaboration-manifest",
        default="",
        help=(
            "optional rag_collaboration_manifest.json containing kernel-overlay "
            "composition agentic seeds to append to the strategy plan"
        ),
    )
    formal_verifier_agentic_proof_strategy_plan.set_defaults(
        func=_formal_verifier_agentic_proof_strategy_plan
    )

    formal_verifier_agentic_proof_candidate_evaluation_queue = sub.add_parser(
        "formal-verifier-agentic-proof-candidate-evaluation-queue",
        help="queue candidate generation/evaluation work from agentic proof strategy rows",
    )
    formal_verifier_agentic_proof_candidate_evaluation_queue.add_argument(
        "--formal-verifier-agentic-proof-strategy-plan-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_strategy_plan_manifest.json",
    )
    formal_verifier_agentic_proof_candidate_evaluation_queue.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_candidate_evaluation_queue",
        help="formal-verifier agentic proof candidate evaluation queue output directory",
    )
    formal_verifier_agentic_proof_candidate_evaluation_queue.set_defaults(
        func=_formal_verifier_agentic_proof_candidate_evaluation_queue
    )

    formal_verifier_agentic_proof_safety_policy = sub.add_parser(
        "formal-verifier-agentic-proof-safety-policy",
        help="export bounded-edit and anti-cheat safety policies for proof candidate work",
    )
    formal_verifier_agentic_proof_safety_policy.add_argument(
        "--formal-verifier-agentic-proof-candidate-evaluation-queue-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_candidate_evaluation_queue_manifest.json",
    )
    formal_verifier_agentic_proof_safety_policy.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_safety_policy",
        help="formal-verifier agentic proof safety policy output directory",
    )
    formal_verifier_agentic_proof_safety_policy.set_defaults(
        func=_formal_verifier_agentic_proof_safety_policy
    )

    formal_verifier_agentic_proof_attempt_population = sub.add_parser(
        "formal-verifier-agentic-proof-attempt-population",
        help="seed reusable proof-attempt population memory from safety policies",
    )
    formal_verifier_agentic_proof_attempt_population.add_argument(
        "--formal-verifier-agentic-proof-safety-policy-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_safety_policy_manifest.json",
    )
    formal_verifier_agentic_proof_attempt_population.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_attempt_population",
        help="formal-verifier agentic proof attempt population output directory",
    )
    formal_verifier_agentic_proof_attempt_population.set_defaults(
        func=_formal_verifier_agentic_proof_attempt_population
    )

    formal_verifier_agentic_proof_execution_queue = sub.add_parser(
        "formal-verifier-agentic-proof-execution-queue",
        help="export executable proof-worker contracts from proof-attempt memory",
    )
    formal_verifier_agentic_proof_execution_queue.add_argument(
        "--formal-verifier-agentic-proof-attempt-population-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_attempt_population_manifest.json",
    )
    formal_verifier_agentic_proof_execution_queue.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_execution_queue",
        help="formal-verifier agentic proof execution queue output directory",
    )
    formal_verifier_agentic_proof_execution_queue.set_defaults(
        func=_formal_verifier_agentic_proof_execution_queue
    )

    formal_verifier_agentic_proof_execution_materializer = sub.add_parser(
        "formal-verifier-agentic-proof-execution-materializer",
        help="materialize bounded Lean artifacts from agentic proof execution rows",
    )
    formal_verifier_agentic_proof_execution_materializer.add_argument(
        "--formal-verifier-agentic-proof-execution-queue-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_execution_queue_manifest.json",
    )
    formal_verifier_agentic_proof_execution_materializer.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_execution_materializer",
        help="formal-verifier agentic proof execution materializer output directory",
    )
    formal_verifier_agentic_proof_execution_materializer.add_argument(
        "--overwrite",
        action="store_true",
        help="rewrite existing candidate artifacts instead of reusing them",
    )
    formal_verifier_agentic_proof_execution_materializer.set_defaults(
        func=_formal_verifier_agentic_proof_execution_materializer
    )

    formal_verifier_agentic_proof_execution_artifact_verifier = sub.add_parser(
        "formal-verifier-agentic-proof-execution-artifact-verifier",
        help="run local Lean checks on materialized agentic proof artifacts",
    )
    formal_verifier_agentic_proof_execution_artifact_verifier.add_argument(
        "--formal-verifier-agentic-proof-execution-materializer-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_execution_materializer_manifest.json",
    )
    formal_verifier_agentic_proof_execution_artifact_verifier.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_execution_artifact_verifier",
        help="formal-verifier agentic proof execution artifact verifier output directory",
    )
    formal_verifier_agentic_proof_execution_artifact_verifier.add_argument(
        "--lean-project",
        default="",
        help="optional local Lake project; when set runs lake env lean",
    )
    formal_verifier_agentic_proof_execution_artifact_verifier.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="seconds before local Lean artifact verification times out",
    )
    formal_verifier_agentic_proof_execution_artifact_verifier.set_defaults(
        func=_formal_verifier_agentic_proof_execution_artifact_verifier
    )

    formal_verifier_agentic_proof_trace_memory = sub.add_parser(
        "formal-verifier-agentic-proof-trace-memory",
        help="summarize agentic proof execution transcripts into reusable search memory",
    )
    formal_verifier_agentic_proof_trace_memory.add_argument(
        "--formal-verifier-agentic-proof-execution-artifact-verifier-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json",
    )
    formal_verifier_agentic_proof_trace_memory.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_trace_memory",
        help="formal-verifier agentic proof trace memory output directory",
    )
    formal_verifier_agentic_proof_trace_memory.set_defaults(
        func=_formal_verifier_agentic_proof_trace_memory
    )

    formal_verifier_agentic_proof_source_theorem_promotion_queue = sub.add_parser(
        "formal-verifier-agentic-proof-source-theorem-promotion-queue",
        help=(
            "queue source-theorem integration work from agentic artifact verifier rows"
        ),
    )
    formal_verifier_agentic_proof_source_theorem_promotion_queue.add_argument(
        "--formal-verifier-agentic-proof-execution-artifact-verifier-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json",
    )
    formal_verifier_agentic_proof_source_theorem_promotion_queue.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_source_theorem_promotion_queue",
        help="formal-verifier agentic source-theorem promotion queue output directory",
    )
    formal_verifier_agentic_proof_source_theorem_promotion_queue.set_defaults(
        func=_formal_verifier_agentic_proof_source_theorem_promotion_queue
    )

    formal_verifier_agentic_proof_source_theorem_target_resolution = sub.add_parser(
        "formal-verifier-agentic-proof-source-theorem-target-resolution",
        help="resolve route-ledger source theorem targets for agentic artifact proof probes",
    )
    formal_verifier_agentic_proof_source_theorem_target_resolution.add_argument(
        "--formal-verifier-agentic-proof-source-theorem-promotion-queue-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json",
    )
    formal_verifier_agentic_proof_source_theorem_target_resolution.add_argument(
        "--formal-verifier-queue-dir",
        default="",
        help="optional directory containing formal_verifier_queue_manifest.json",
    )
    formal_verifier_agentic_proof_source_theorem_target_resolution.add_argument(
        "--formal-verifier-replay-dir",
        default="",
        help="optional directory containing formal_verifier_replay_manifest.json",
    )
    formal_verifier_agentic_proof_source_theorem_target_resolution.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_source_theorem_target_resolution",
        help="formal-verifier agentic source-theorem target resolution output directory",
    )
    formal_verifier_agentic_proof_source_theorem_target_resolution.set_defaults(
        func=_formal_verifier_agentic_proof_source_theorem_target_resolution
    )

    rag_collaboration_export = sub.add_parser(
        "rag-collaboration-export",
        help="export a compact handoff manifest for the shared RAG/prover-search thread",
    )
    rag_collaboration_export.add_argument(
        "--system-audit-manifest",
        required=True,
        help="path to a research_system_audit_manifest.json with retrieval/proof artifacts",
    )
    rag_collaboration_export.add_argument(
        "--out",
        default="runs/rag_collaboration",
        help="RAG collaboration handoff output directory",
    )
    rag_collaboration_export.add_argument(
        "--max-targets",
        type=int,
        default=20,
        help="maximum non-composition formal primitives to include as RAG handoff targets",
    )
    rag_collaboration_export.add_argument(
        "--formalization-gap-planner-proof-state-triage-manifest",
        default="",
        help=(
            "optional standalone proof-state triage manifest to include in the RAG handoff "
            "without requiring the source system-audit manifest to list it"
        ),
    )
    rag_collaboration_export.set_defaults(func=_rag_collaboration_export)

    research_training_export = sub.add_parser(
        "research-training-export",
        help="export research traces as SFT/GRPO seed data for theory-lab agents",
    )
    research_training_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_training_export.add_argument(
        "--validation-fraction",
        type=float,
        default=0.2,
        help="deterministic validation split fraction in [0, 1)",
    )
    research_training_export.add_argument(
        "--base-model",
        default="untrained-trace-export",
        help="base model label recorded in the legacy training manifest",
    )
    research_training_export.add_argument(
        "--out",
        default="runs/research_training_export",
        help="research trace training export output directory",
    )
    research_training_export.set_defaults(func=_research_training_export)

    research_policy_baseline = sub.add_parser(
        "research-policy-baseline",
        help="evaluate a nearest-neighbor baseline over exported research-agent SFT data",
    )
    research_policy_baseline.add_argument("--train-jsonl", required=True, help="research_sft_train.jsonl")
    research_policy_baseline.add_argument("--validation-jsonl", required=True, help="research_sft_validation.jsonl")
    research_policy_baseline.add_argument("--k", type=int, default=5, help="top-k research-memory candidates")
    research_policy_baseline.add_argument(
        "--out",
        default="runs/research_policy_baseline",
        help="output directory for research policy baseline predictions and manifest",
    )
    research_policy_baseline.set_defaults(func=_research_policy_baseline)

    next_iteration_audit = sub.add_parser(
        "next-iteration-audit",
        help="aggregate per-trace next_iteration_agenda items into a run-level agent queue",
    )
    next_iteration_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    next_iteration_audit.add_argument(
        "--out",
        default="runs/next_iteration_queue",
        help="next-iteration queue output directory",
    )
    next_iteration_audit.set_defaults(func=_next_iteration_audit)

    research_report = sub.add_parser(
        "research-report",
        help="write a human-readable Markdown report from persisted AI Statistical Theory Lab traces",
    )
    research_report.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_report.add_argument(
        "--out",
        default="runs/research_report",
        help="research report output directory",
    )
    research_report.set_defaults(func=_research_report)

    claim_ledger = sub.add_parser(
        "claim-ledger",
        help="write a typed claim/evidence ledger from persisted AI Statistical Theory Lab traces",
    )
    claim_ledger.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    claim_ledger.add_argument(
        "--out",
        default="runs/claim_ledger",
        help="claim ledger output directory",
    )
    claim_ledger.add_argument(
        "--proof-audit-manifest",
        help="optional proof_audit_manifest.json used to overlay real kernel proof evidence",
    )
    claim_ledger.add_argument(
        "--repair-response-promotion-manifest",
        help=(
            "optional formal_verifier_replay_repair_patch_response_promotion_manifest.json "
            "used to overlay accepted full-route repair evidence"
        ),
    )
    claim_ledger.set_defaults(func=_claim_ledger)

    claim_ledger_actions = sub.add_parser(
        "claim-ledger-action-export",
        help="export owner-agent work items from a typed claim ledger",
    )
    claim_ledger_actions.add_argument(
        "--claim-ledger-dir",
        required=True,
        help="directory containing claim_ledger_manifest.json and claim_ledger.jsonl",
    )
    claim_ledger_actions.add_argument(
        "--out",
        default="runs/claim_ledger_actions",
        help="claim-ledger action output directory",
    )
    claim_ledger_actions.set_defaults(func=_claim_ledger_action_export)

    stat_claim_certificate_plan = sub.add_parser(
        "stat-claim-certificate-plan",
        help="export Axon-style certificate-checker targets from a typed claim ledger",
    )
    stat_claim_certificate_plan.add_argument(
        "--claim-ledger-dir",
        required=True,
        help="directory containing claim_ledger_manifest.json and claim_ledger.jsonl",
    )
    stat_claim_certificate_plan.add_argument(
        "--max-targets",
        type=int,
        default=40,
        help="maximum certificate-checker target rows to export",
    )
    stat_claim_certificate_plan.add_argument(
        "--out",
        default="runs/stat_claim_certificate_plan",
        help="statistical claim certificate plan output directory",
    )
    stat_claim_certificate_plan.set_defaults(func=_stat_claim_certificate_plan)

    stat_claim_certificate_checker_audit = sub.add_parser(
        "stat-claim-certificate-checker-audit",
        help="verify small statistical certificate-checker soundness theorems",
    )
    stat_claim_certificate_checker_audit.add_argument(
        "--id",
        action="append",
        help="certificate checker obligation id to verify; repeatable",
    )
    stat_claim_certificate_checker_audit.add_argument(
        "--local-lean",
        action="store_true",
        help="use local lake env lean kernel verification",
    )
    stat_claim_certificate_checker_audit.add_argument(
        "--lean-project",
        help="local Lake project used by --local-lean",
    )
    stat_claim_certificate_checker_audit.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each local Lean check",
    )
    stat_claim_certificate_checker_audit.add_argument(
        "--real-lean",
        action="store_true",
        help="use AXLE verify_proof instead of mock verifier",
    )
    stat_claim_certificate_checker_audit.add_argument(
        "--out",
        default="runs/stat_claim_certificate_checker_audit",
        help="certificate checker audit output directory",
    )
    stat_claim_certificate_checker_audit.set_defaults(
        func=_stat_claim_certificate_checker_audit
    )

    stat_claim_certificate_readiness = sub.add_parser(
        "stat-claim-certificate-readiness",
        help="overlay kernel-verified checker availability onto certificate-plan targets",
    )
    stat_claim_certificate_readiness.add_argument(
        "--certificate-plan-dir",
        required=True,
        help="directory containing stat_claim_certificate_plan_manifest.json",
    )
    stat_claim_certificate_readiness.add_argument(
        "--checker-audit-dir",
        required=True,
        help="directory containing stat_claim_certificate_checker_audit_manifest.json",
    )
    stat_claim_certificate_readiness.add_argument(
        "--out",
        default="runs/stat_claim_certificate_readiness",
        help="certificate readiness overlay output directory",
    )
    stat_claim_certificate_readiness.set_defaults(
        func=_stat_claim_certificate_readiness_overlay
    )

    stat_claim_certificate_witness_queue = sub.add_parser(
        "stat-claim-certificate-witness-queue",
        help="export witness-generation tasks for kernel-ready certificate targets",
    )
    stat_claim_certificate_witness_queue.add_argument(
        "--certificate-plan-dir",
        required=True,
        help="directory containing stat_claim_certificate_plan_manifest.json",
    )
    stat_claim_certificate_witness_queue.add_argument(
        "--readiness-dir",
        required=True,
        help="directory containing stat_claim_certificate_readiness_manifest.json",
    )
    stat_claim_certificate_witness_queue.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="optional maximum number of ready witness tasks to export",
    )
    stat_claim_certificate_witness_queue.add_argument(
        "--out",
        default="runs/stat_claim_certificate_witness_queue",
        help="certificate witness queue output directory",
    )
    stat_claim_certificate_witness_queue.set_defaults(
        func=_stat_claim_certificate_witness_queue
    )

    stat_claim_certificate_witness_materialize = sub.add_parser(
        "stat-claim-certificate-witness-materialize",
        help="materialize unfilled witness JSON draft files from certificate witness tasks",
    )
    stat_claim_certificate_witness_materialize.add_argument(
        "--witness-queue-dir",
        required=True,
        help="directory containing stat_claim_certificate_witness_queue_manifest.json",
    )
    stat_claim_certificate_witness_materialize.add_argument(
        "--max-drafts",
        type=int,
        default=None,
        help="optional maximum number of witness drafts to materialize",
    )
    stat_claim_certificate_witness_materialize.add_argument(
        "--out",
        default="runs/stat_claim_certificate_witness_materializer",
        help="certificate witness materializer output directory",
    )
    stat_claim_certificate_witness_materialize.set_defaults(
        func=_stat_claim_certificate_witness_materialize
    )

    stat_claim_certificate_witness_prompt_packets = sub.add_parser(
        "stat-claim-certificate-witness-prompt-packets",
        help="export source-grounded prompt packets for filling certificate witness drafts",
    )
    stat_claim_certificate_witness_prompt_packets.add_argument(
        "--materializer-dir",
        required=True,
        help="directory containing stat_claim_certificate_witness_materializer_manifest.json",
    )
    stat_claim_certificate_witness_prompt_packets.add_argument(
        "--max-packets",
        type=int,
        default=None,
        help="optional maximum number of witness prompt packets to export",
    )
    stat_claim_certificate_witness_prompt_packets.add_argument(
        "--out",
        default="runs/stat_claim_certificate_witness_prompt_packets",
        help="certificate witness prompt packet output directory",
    )
    stat_claim_certificate_witness_prompt_packets.set_defaults(
        func=_stat_claim_certificate_witness_prompt_packets
    )

    stat_claim_certificate_witness_context_packets = sub.add_parser(
        "stat-claim-certificate-witness-context-packets",
        help="resolve certificate witness prompt evidence paths into bounded source-context packets",
    )
    stat_claim_certificate_witness_context_packets.add_argument(
        "--prompt-packets-dir",
        required=True,
        help="directory containing stat_claim_certificate_witness_prompt_packets_manifest.json",
    )
    stat_claim_certificate_witness_context_packets.add_argument(
        "--max-packets",
        type=int,
        default=None,
        help="optional maximum number of witness context packets to export",
    )
    stat_claim_certificate_witness_context_packets.add_argument(
        "--max-snippets-per-source",
        type=int,
        default=3,
        help="maximum snippets to retain from each cited source file",
    )
    stat_claim_certificate_witness_context_packets.add_argument(
        "--max-snippet-chars",
        type=int,
        default=1200,
        help="maximum characters per source snippet",
    )
    stat_claim_certificate_witness_context_packets.add_argument(
        "--out",
        default="runs/stat_claim_certificate_witness_context_packets",
        help="certificate witness context packet output directory",
    )
    stat_claim_certificate_witness_context_packets.set_defaults(
        func=_stat_claim_certificate_witness_context_packets
    )

    stat_claim_certificate_witness_context_triage = sub.add_parser(
        "stat-claim-certificate-witness-context-triage",
        help="triage certificate witness context packets into worker-ready and source-review queues",
    )
    stat_claim_certificate_witness_context_triage.add_argument(
        "--context-packets-dir",
        required=True,
        help="directory containing stat_claim_certificate_witness_context_packets_manifest.json",
    )
    stat_claim_certificate_witness_context_triage.add_argument(
        "--out",
        default="runs/stat_claim_certificate_witness_context_triage",
        help="certificate witness context triage output directory",
    )
    stat_claim_certificate_witness_context_triage.set_defaults(
        func=_stat_claim_certificate_witness_context_triage
    )

    stat_claim_certificate_witness_response_validate = sub.add_parser(
        "stat-claim-certificate-witness-response-validate",
        help="validate worker outputs for certificate witness prompt packets",
    )
    stat_claim_certificate_witness_response_validate.add_argument(
        "--prompt-packets-dir",
        required=True,
        help="directory containing stat_claim_certificate_witness_prompt_packets_manifest.json",
    )
    stat_claim_certificate_witness_response_validate.add_argument(
        "--worker-output-jsonl",
        default=None,
        help="optional worker-output JSONL path; defaults to the prompt-packet contract path",
    )
    stat_claim_certificate_witness_response_validate.add_argument(
        "--out",
        default="runs/stat_claim_certificate_witness_response_validation",
        help="certificate witness response-validation output directory",
    )
    stat_claim_certificate_witness_response_validate.set_defaults(
        func=_stat_claim_certificate_witness_response_validate
    )

    stat_claim_certificate_witness_response_apply = sub.add_parser(
        "stat-claim-certificate-witness-response-apply",
        help="copy accepted witness worker responses into draft artifacts",
    )
    stat_claim_certificate_witness_response_apply.add_argument(
        "--response-validation-dir",
        required=True,
        help="directory containing stat_claim_certificate_witness_response_validation_manifest.json",
    )
    stat_claim_certificate_witness_response_apply.add_argument(
        "--materializer-dir",
        default=None,
        help="optional materializer directory; defaults to the prompt-packet manifest lineage",
    )
    stat_claim_certificate_witness_response_apply.add_argument(
        "--out",
        default="runs/stat_claim_certificate_witness_response_apply",
        help="certificate witness response-apply output directory",
    )
    stat_claim_certificate_witness_response_apply.set_defaults(
        func=_stat_claim_certificate_witness_response_apply
    )

    stat_claim_certificate_witness_validate = sub.add_parser(
        "stat-claim-certificate-witness-validate",
        help="validate materialized certificate witness drafts before checker execution",
    )
    stat_claim_certificate_witness_validate.add_argument(
        "--materializer-dir",
        required=True,
        help="directory containing stat_claim_certificate_witness_materializer_manifest.json",
    )
    stat_claim_certificate_witness_validate.add_argument(
        "--out",
        default="runs/stat_claim_certificate_witness_validator",
        help="certificate witness validator output directory",
    )
    stat_claim_certificate_witness_validate.set_defaults(
        func=_stat_claim_certificate_witness_validate
    )

    theorem_composition = sub.add_parser(
        "theorem-composition-export",
        help="export theorem-composition packets from claim-ledger exact proof-bank reuse rows",
    )
    theorem_composition.add_argument(
        "--claim-ledger-dir",
        required=True,
        help="directory containing claim_ledger_manifest.json and claim_ledger.jsonl",
    )
    theorem_composition.add_argument(
        "--out",
        default="runs/theorem_composition",
        help="theorem-composition packet output directory",
    )
    theorem_composition.set_defaults(func=_theorem_composition_export)

    doctor = sub.add_parser("doctor", help="inspect local readiness for proof, LLM, retrieval, and audit runs")
    doctor.add_argument("--root", default=".", help="project root to inspect")
    doctor.add_argument("--env-file", default=".env", help="dotenv file to inspect for redacted key presence")
    doctor.add_argument("--out", default="runs/doctor", help="write doctor_manifest.json to this directory")
    doctor.add_argument("--max-manifests", type=int, default=12, help="number of latest run manifests to display")
    doctor.add_argument("--json", action="store_true", help="print machine-readable JSON")
    doctor.set_defaults(func=_doctor)

    capability_audit = sub.add_parser(
        "capability-audit",
        help="map the production objective to current source and manifest evidence",
    )
    capability_audit.add_argument("--root", default=".", help="project root to inspect")
    capability_audit.add_argument("--out", default="runs/capability_audit", help="write capability_audit_manifest.json here")
    capability_audit.add_argument("--max-manifests", type=int, default=12, help="number of recent manifests to include")
    capability_audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    capability_audit.set_defaults(func=_capability_audit)

    research_capability_audit = sub.add_parser(
        "research-capability-audit",
        help="map the broad AI Statistical Theory Lab goal to current evidence and honest gaps",
    )
    research_capability_audit.add_argument("--root", default=".", help="project root to inspect")
    research_capability_audit.add_argument("--question-file", default="examples/research_questions.json")
    research_capability_audit.add_argument(
        "--frontier-benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    research_capability_audit.add_argument(
        "--out",
        default="runs/research_capability_audit",
        help="write research_capability_audit_manifest.json here",
    )
    research_capability_audit.add_argument("--max-manifests", type=int, default=12, help="number of recent research manifests to include")
    research_capability_audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    research_capability_audit.set_defaults(func=_research_capability_audit)

    architecture_audit = sub.add_parser(
        "architecture-audit",
        help="audit current one-pass scaffold vs target closed-loop AI statistician architecture",
    )
    architecture_audit.add_argument(
        "--out",
        default="runs/architecture_audit",
        help="write architecture_audit_manifest.json here",
    )
    architecture_audit.set_defaults(func=_architecture_audit)

    prover_component_audit = sub.add_parser(
        "prover-component-audit",
        help="audit the system against the modern prover-stack components from the AI-for-math paper outline",
    )
    prover_component_audit.add_argument("--root", default=".", help="project root to inspect")
    prover_component_audit.add_argument("--question-file", default="examples/research_questions.json")
    prover_component_audit.add_argument(
        "--frontier-benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    prover_component_audit.add_argument(
        "--out",
        default="runs/prover_component_audit",
        help="write prover_component_audit_manifest.json here",
    )
    prover_component_audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    prover_component_audit.set_defaults(func=_prover_component_audit)

    system_audit = sub.add_parser("system-audit", help="run release-style system gates and write one manifest")
    system_audit.add_argument("--question-file", help="additional question JSON file")
    system_audit.add_argument("--include-partial-examples", action="store_true", help="include examples/partial_questions.json")
    system_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    system_audit.add_argument("--runs", type=int, default=300, help="Monte Carlo replicates per question")
    system_audit.add_argument("--n-seeds", type=int, default=2)
    system_audit.add_argument("--seed-start", type=int, default=20260528)
    system_audit.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    system_audit.add_argument("--no-eval", action="store_true", help="skip multi-seed evaluation gate")
    system_audit.add_argument("--out", default="runs/system_audit", help="system audit output directory")
    system_audit.add_argument("--env-file", default=".env")
    system_audit.set_defaults(func=lambda args: asyncio.run(_system_audit(args)))

    release_bundle = sub.add_parser("release-bundle", help="write a top-level release manifest from doctor, capability, and system audits")
    release_bundle.add_argument("--root", default=".", help="project root to inspect")
    release_bundle.add_argument("--question-file", help="additional question JSON file")
    release_bundle.add_argument("--include-partial-examples", action="store_true", help="include examples/partial_questions.json")
    release_bundle.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof in the bundled system audit")
    release_bundle.add_argument("--runs", type=int, default=300, help="Monte Carlo replicates per question")
    release_bundle.add_argument("--n-seeds", type=int, default=2)
    release_bundle.add_argument("--seed-start", type=int, default=20260528)
    release_bundle.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    release_bundle.add_argument("--no-eval", action="store_true", help="skip multi-seed evaluation gate inside the bundle")
    release_bundle.add_argument("--max-manifests", type=int, default=12, help="number of recent manifests to include in doctor/capability subreports")
    release_bundle.add_argument("--out", default="runs/release_bundle", help="release bundle output directory")
    release_bundle.add_argument("--env-file", default=".env")
    release_bundle.set_defaults(func=lambda args: asyncio.run(_release_bundle(args)))

    theory_intake = sub.add_parser("theory-intake", help="normalize question JSON through deterministic or LLM-gated theory intake")
    theory_intake.add_argument("--question-file", required=True, help="question JSON file")
    theory_intake.add_argument("--llm-theory", action="store_true", help="allow a generator backend to classify supported estimator/DGP families during intake")
    theory_intake.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    theory_intake.add_argument("--llm-provider", choices=LIVE_GENERATOR_PROVIDER_CHOICES, default=_default_live_generator_provider())
    theory_intake.add_argument("--llm-static-response-file", default="", help="JSON response to replay when --llm-provider static is used")
    theory_intake.add_argument("--llm-model", default="", help="model name for the intake generator; Anthropic defaults to Claude Haiku 4.5 for this light classifier")
    theory_intake.add_argument("--llm-max-tokens", type=int, default=700)
    theory_intake.add_argument("--env-file", default=".env")
    theory_intake.set_defaults(func=_theory_intake)

    research_benchmark = sub.add_parser(
        "research-benchmark",
        help="run the next-stage open-question statistical theory lab benchmark",
    )
    research_benchmark.add_argument("--question-file", default="examples/research_questions.json")
    research_benchmark.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_benchmark.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    research_benchmark.add_argument("--lean-project", help="local Lake project used by --local-lean")
    research_benchmark.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    research_benchmark.add_argument("--runs", type=int, default=100, help="Monte Carlo research-simulation replicates")
    research_benchmark.add_argument("--seed", type=int, default=20260528)
    research_benchmark.add_argument(
        "--adaptive-mc-rerun",
        action="store_true",
        help="rerun only simulations diagnosed as INSUFFICIENT_MC_PRECISION with a larger MC budget",
    )
    research_benchmark.add_argument(
        "--adaptive-mc-multiplier",
        type=int,
        default=5,
        help="multiplier for adaptive MC reruns of precision-limited simulation rows",
    )
    research_benchmark.add_argument(
        "--formal-source-backend",
        choices=("sqlite", "memory"),
        default="sqlite",
        help="formal-gap retrieval backend for local Lean/stat source search",
    )
    research_benchmark.add_argument(
        "--lean-rag-db",
        default="",
        help=(
            "optional SQLite DB generated by EmpericalProcessLEAN/lean_rag "
            "shared_proof_retrieval.py; auto-discovered from the standard runs/ path when omitted"
        ),
    )
    research_benchmark.add_argument("--out", default="runs/research_benchmark", help="research trace output directory")
    research_benchmark.add_argument("--env-file", default=".env")
    research_benchmark.set_defaults(func=lambda args: asyncio.run(_research_benchmark(args)))

    research_loop = sub.add_parser(
        "research-loop",
        help="execute bounded live feedback rounds over research traces",
    )
    research_loop.add_argument("--question-file", default="examples/research_questions.json")
    research_loop.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_loop.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    research_loop.add_argument("--lean-project", help="local Lake project used by --local-lean")
    research_loop.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    research_loop.add_argument("--runs", type=int, default=100, help="initial Monte Carlo research-simulation replicates")
    research_loop.add_argument("--seed", type=int, default=20260528)
    research_loop.add_argument("--max-rounds", type=int, default=2)
    research_loop.add_argument("--mc-rerun-multiplier", type=int, default=3)
    research_loop.add_argument("--max-questions", type=int, default=0, help="optional cap for quick smoke runs")
    research_loop.add_argument(
        "--llm-theory-developer",
        action="store_true",
        help="use the LLM TheoryDeveloper live repair handler for theory/procedure simulation failures",
    )
    research_loop.add_argument(
        "--llm-theory-provider",
        choices=LIVE_GENERATOR_PROVIDER_CHOICES,
        default=_default_live_generator_provider(),
        help=(
            "generator backend for --llm-theory-developer; defaults to Anthropic "
            "Claude API"
        ),
    )
    research_loop.add_argument(
        "--llm-theory-static-response-file",
        default="",
        help="JSON response file for --llm-theory-provider static",
    )
    research_loop.add_argument(
        "--llm-theory-model",
        default="",
        help="model name for the LLM TheoryDeveloper; Anthropic defaults to Claude Sonnet 4.6 for theory repair",
    )
    research_loop.add_argument("--llm-theory-max-tokens", type=int, default=9000)
    research_loop.add_argument("--llm-theory-temperature", type=float, default=0.2)
    research_loop.add_argument(
        "--disable-default-theory-developer",
        action="store_true",
        help="disable the conservative DefaultTheoryDeveloper fallback",
    )
    research_loop.add_argument(
        "--formal-source-backend",
        choices=("sqlite", "memory"),
        default="sqlite",
        help="formal-gap retrieval backend for local Lean/stat source search",
    )
    research_loop.add_argument(
        "--lean-rag-db",
        default="",
        help=(
            "optional SQLite DB generated by EmpericalProcessLEAN/lean_rag "
            "shared_proof_retrieval.py; auto-discovered from the standard runs/ path when omitted"
        ),
    )
    research_loop.add_argument("--out", default="runs/research_loop", help="research loop output directory")
    research_loop.add_argument("--env-file", default=".env")
    research_loop.set_defaults(func=lambda args: asyncio.run(_research_loop(args)))

    research_loop_repair_audit = sub.add_parser(
        "research-loop-repair-audit",
        help="audit research-loop repair tasks and export SFT planning examples",
    )
    research_loop_repair_audit.add_argument("--loop-dir", required=True, help="directory containing research_loop_manifest.json")
    research_loop_repair_audit.add_argument(
        "--out",
        default="runs/research_loop_repair_audit",
        help="research loop repair audit output directory",
    )
    research_loop_repair_audit.add_argument("--validation-fraction", type=float, default=0.2)
    research_loop_repair_audit.set_defaults(func=_research_loop_repair_audit)

    research_loop_live_repair_audit = sub.add_parser(
        "research-loop-live-repair-audit",
        help="audit executed live repair artifacts and export SFT execution examples",
    )
    research_loop_live_repair_audit.add_argument(
        "--loop-dir",
        required=True,
        help="directory containing research_loop_manifest.json",
    )
    research_loop_live_repair_audit.add_argument(
        "--out",
        default="runs/research_loop_live_repair_audit",
        help="research loop live repair audit output directory",
    )
    research_loop_live_repair_audit.add_argument("--validation-fraction", type=float, default=0.2)
    research_loop_live_repair_audit.set_defaults(func=_research_loop_live_repair_audit)

    algorithm_repair_promotion = sub.add_parser(
        "algorithm-repair-promotion",
        help="convert algorithm live-repair artifacts into sandbox patch candidates",
    )
    algorithm_repair_promotion.add_argument(
        "--loop-dir",
        required=True,
        help="directory containing research_loop_manifest.json",
    )
    algorithm_repair_promotion.add_argument(
        "--out",
        default="runs/algorithm_repair_promotion",
        help="algorithm repair promotion output directory",
    )
    algorithm_repair_promotion.set_defaults(func=_algorithm_repair_promotion)

    algorithm_repair_sandbox = sub.add_parser(
        "algorithm-repair-sandbox",
        help="evaluate algorithm repair promotion candidates against the current vetted registry",
    )
    algorithm_repair_sandbox.add_argument(
        "--promotion-dir",
        required=True,
        help="directory containing algorithm_repair_promotion_manifest.json",
    )
    algorithm_repair_sandbox.add_argument(
        "--out",
        default="runs/algorithm_repair_sandbox",
        help="algorithm repair sandbox output directory",
    )
    algorithm_repair_sandbox.set_defaults(func=_algorithm_repair_sandbox)

    algorithm_repair_sandbox_apply = sub.add_parser(
        "algorithm-repair-sandbox-apply",
        help="create non-mutating applied sandbox artifacts for ready algorithm repair plans",
    )
    algorithm_repair_sandbox_apply.add_argument(
        "--sandbox-dir",
        required=True,
        help="directory containing algorithm_repair_sandbox_manifest.json",
    )
    algorithm_repair_sandbox_apply.add_argument(
        "--out",
        default="runs/algorithm_repair_sandbox_apply",
        help="algorithm repair sandbox apply output directory",
    )
    algorithm_repair_sandbox_apply.set_defaults(func=_algorithm_repair_sandbox_apply)

    algorithm_repair_sandbox_rerun = sub.add_parser(
        "algorithm-repair-sandbox-rerun",
        help="rerun current vetted simulators for sandbox-applied algorithm repair plans",
    )
    algorithm_repair_sandbox_rerun.add_argument(
        "--apply-dir",
        required=True,
        help="directory containing algorithm_repair_sandbox_apply_manifest.json",
    )
    algorithm_repair_sandbox_rerun.add_argument("--question-file", default="examples/research_questions.json")
    algorithm_repair_sandbox_rerun.add_argument("--runs", type=int, default=50)
    algorithm_repair_sandbox_rerun.add_argument("--seed", type=int, default=20260530)
    algorithm_repair_sandbox_rerun.add_argument(
        "--out",
        default="runs/algorithm_repair_sandbox_rerun",
        help="algorithm repair sandbox rerun output directory",
    )
    algorithm_repair_sandbox_rerun.set_defaults(func=_algorithm_repair_sandbox_rerun)

    algorithm_repair_sandbox_patch_eval = sub.add_parser(
        "algorithm-repair-sandbox-patch-eval",
        help="execute deterministic isolated patch evaluation for sandbox-applied algorithm repairs",
    )
    algorithm_repair_sandbox_patch_eval.add_argument(
        "--apply-dir",
        required=True,
        help="directory containing algorithm_repair_sandbox_apply_manifest.json",
    )
    algorithm_repair_sandbox_patch_eval.add_argument(
        "--question-file",
        default="examples/research_questions.json",
    )
    algorithm_repair_sandbox_patch_eval.add_argument("--runs", type=int, default=50)
    algorithm_repair_sandbox_patch_eval.add_argument("--seed", type=int, default=20260531)
    algorithm_repair_sandbox_patch_eval.add_argument(
        "--out",
        default="runs/algorithm_repair_sandbox_patch_eval",
        help="algorithm repair sandbox patch-eval output directory",
    )
    algorithm_repair_sandbox_patch_eval.set_defaults(func=_algorithm_repair_sandbox_patch_eval)

    algorithm_repair_patch_training_export = sub.add_parser(
        "algorithm-repair-patch-training-export",
        help="export isolated patch-eval evidence as algorithm repair promotion-policy training data",
    )
    algorithm_repair_patch_training_export.add_argument(
        "--patch-eval-dir",
        required=True,
        help="directory containing algorithm_repair_sandbox_patch_eval_manifest.json",
    )
    algorithm_repair_patch_training_export.add_argument(
        "--out",
        default="runs/algorithm_repair_patch_training_export",
        help="algorithm repair patch training export output directory",
    )
    algorithm_repair_patch_training_export.add_argument("--validation-fraction", type=float, default=0.2)
    algorithm_repair_patch_training_export.set_defaults(func=_algorithm_repair_patch_training_export)

    algorithm_repair_patch_policy_train = sub.add_parser(
        "algorithm-repair-patch-policy-train",
        help="train a deterministic promotion-safety policy baseline from patch-eval examples",
    )
    algorithm_repair_patch_policy_train.add_argument("--train-jsonl", required=True)
    algorithm_repair_patch_policy_train.add_argument("--validation-jsonl")
    algorithm_repair_patch_policy_train.add_argument(
        "--out",
        default="runs/algorithm_repair_patch_policy_model",
        help="algorithm repair patch policy model output directory",
    )
    algorithm_repair_patch_policy_train.add_argument("--epochs", type=int, default=100)
    algorithm_repair_patch_policy_train.add_argument("--learning-rate", type=float, default=0.15)
    algorithm_repair_patch_policy_train.add_argument("--l2", type=float, default=0.001)
    algorithm_repair_patch_policy_train.set_defaults(func=_algorithm_repair_patch_policy_train)

    algorithm_repair_production_patch_plan = sub.add_parser(
        "algorithm-repair-production-patch-plan",
        help="export reviewed production source-change plans from safe patch-policy predictions",
    )
    algorithm_repair_production_patch_plan.add_argument(
        "--policy-model-dir",
        required=True,
        help="directory containing algorithm_repair_patch_policy_model_manifest.json",
    )
    algorithm_repair_production_patch_plan.add_argument(
        "--out",
        default="runs/algorithm_repair_production_patch_plan",
        help="algorithm repair production patch plan output directory",
    )
    algorithm_repair_production_patch_plan.set_defaults(func=_algorithm_repair_production_patch_plan)

    algorithm_repair_reviewed_patch_apply = sub.add_parser(
        "algorithm-repair-reviewed-patch-apply",
        help="apply reviewed algorithm repair patch plans in an isolated source workspace",
    )
    algorithm_repair_reviewed_patch_apply.add_argument(
        "--plan-dir",
        required=True,
        help="directory containing algorithm_repair_production_patch_plan_manifest.json",
    )
    algorithm_repair_reviewed_patch_apply.add_argument("--source-root", default=".")
    algorithm_repair_reviewed_patch_apply.add_argument(
        "--out",
        default="runs/algorithm_repair_reviewed_patch_apply",
        help="algorithm repair reviewed patch apply output directory",
    )
    algorithm_repair_reviewed_patch_apply.set_defaults(func=_algorithm_repair_reviewed_patch_apply)

    algorithm_repair_reviewed_patch_validate = sub.add_parser(
        "algorithm-repair-reviewed-patch-validate",
        help="import copied package with reviewed patches and rerun affected-procedure simulation",
    )
    algorithm_repair_reviewed_patch_validate.add_argument(
        "--apply-dir",
        required=True,
        help="directory containing algorithm_repair_reviewed_patch_apply_manifest.json",
    )
    algorithm_repair_reviewed_patch_validate.add_argument("--source-root", default=".")
    algorithm_repair_reviewed_patch_validate.add_argument("--question-file", default="examples/research_questions.json")
    algorithm_repair_reviewed_patch_validate.add_argument("--runs", type=int, default=10)
    algorithm_repair_reviewed_patch_validate.add_argument("--seed", type=int, default=20260601)
    algorithm_repair_reviewed_patch_validate.add_argument(
        "--out",
        default="runs/algorithm_repair_reviewed_patch_validate",
        help="algorithm repair reviewed patch validation output directory",
    )
    algorithm_repair_reviewed_patch_validate.set_defaults(func=_algorithm_repair_reviewed_patch_validate)

    research_eval = sub.add_parser(
        "research-eval",
        help="run multi-seed evaluation for the open-question statistical theory lab benchmark",
    )
    research_eval.add_argument("--question-file", default="examples/research_questions.json")
    research_eval.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_eval.add_argument("--runs", type=int, default=80, help="Monte Carlo research-simulation replicates per seed")
    research_eval.add_argument("--n-seeds", type=int, default=3)
    research_eval.add_argument("--seed-start", type=int, default=20260528)
    research_eval.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    research_eval.add_argument("--out", default="runs/research_eval", help="research evaluation output directory")
    research_eval.add_argument("--env-file", default=".env")
    research_eval.set_defaults(func=lambda args: asyncio.run(_research_eval(args)))

    research_system_audit = sub.add_parser(
        "research-system-audit",
        help="run release-style gates for the AI Statistical Theory Lab workflow",
    )
    research_system_audit.add_argument("--question-file", default="examples/research_questions.json")
    research_system_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_system_audit.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    research_system_audit.add_argument("--lean-project", help="local Lake project used by --local-lean")
    research_system_audit.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    research_system_audit.add_argument(
        "--kernel-smoke-id",
        action="append",
        help=(
            "run a small local Lean proof-audit overlay for this proof obligation id; "
            "repeatable. Uses --lean-project/--lean-timeout and does not replace the "
            "main proof audit."
        ),
    )
    research_system_audit.add_argument(
        "--kernel-smoke-from-actions",
        type=int,
        default=0,
        help=(
            "auto-select up to N registered proof-bank obligations from the current "
            "proof-bank action queue for a local Lean smoke overlay. Exact proof-bank "
            "reuse rows are prioritized before broader bridge-chain rows."
        ),
    )
    research_system_audit.add_argument(
        "--formal-verifier-replay-attempt-log",
        default="",
        help="optional JSONL of full theorem/bridge replay attempts used to calibrate replay tasks",
    )
    research_system_audit.add_argument(
        "--formal-verifier-replay-attempts",
        type=int,
        default=0,
        help=(
            "attempt the first N FormalVerifier replay targets during the audit; "
            "when --lean-project is set these attempts use local Lean"
        ),
    )
    research_system_audit.add_argument(
        "--verify-agentic-artifacts",
        action="store_true",
        help=(
            "run local Lean checks on materialized agentic proof-worker artifacts; "
            "this reports artifact-level kernel evidence only, not source theorem proof evidence"
        ),
    )
    research_system_audit.add_argument(
        "--formal-source-index-cache",
        default="runs/formal_source_index_cache/formal_source_index.sqlite",
        help="persistent SQLite cache for repeated formal-source index builds; pass empty string to disable",
    )
    research_system_audit.add_argument(
        "--refresh-formal-source-index-cache",
        action="store_true",
        help="rebuild and overwrite the persistent formal-source index cache",
    )
    research_system_audit.add_argument(
        "--lean-rag-db",
        default="",
        help=(
            "optional SQLite DB generated by EmpericalProcessLEAN/lean_rag "
            "shared_proof_retrieval.py; auto-discovered from the standard runs/ path when omitted"
        ),
    )
    research_system_audit.add_argument(
        "--lean-rag-package-root",
        default="",
        help="optional EmpericalProcessLEAN/lean_rag package root for source-registry and seed-query contract audit",
    )
    research_system_audit.add_argument(
        "--formal-source-graph-cache",
        default="runs/formal_source_graph_cache",
        help="persistent cache directory for repeated formal-source graph audits; pass empty string to disable",
    )
    research_system_audit.add_argument(
        "--refresh-formal-source-graph-cache",
        action="store_true",
        help="rebuild and overwrite the matching formal-source graph cache entry",
    )
    research_system_audit.add_argument("--runs", type=int, default=100, help="Monte Carlo research-simulation replicates")
    research_system_audit.add_argument(
        "--frontier-smoke-runs",
        type=int,
        default=25,
        help="Monte Carlo replicates for broad frontier smoke traces; keep lower than --runs for fast release gates",
    )
    research_system_audit.add_argument(
        "--frontier-smoke-cache",
        default="runs/frontier_smoke_cache",
        help="persistent cache directory for repeated frontier smoke trace generation; pass empty string to disable",
    )
    research_system_audit.add_argument(
        "--refresh-frontier-smoke-cache",
        action="store_true",
        help="rebuild and overwrite the matching frontier smoke trace cache entry",
    )
    research_system_audit.add_argument(
        "--research-benchmark-cache",
        default="runs/research_benchmark_cache",
        help="persistent cache directory for repeated main research benchmark traces; pass empty string to disable",
    )
    research_system_audit.add_argument(
        "--refresh-research-benchmark-cache",
        action="store_true",
        help="rebuild and overwrite the matching main research benchmark trace cache entry",
    )
    research_system_audit.add_argument("--seed", type=int, default=20260528)
    research_system_audit.add_argument(
        "--no-adaptive-mc-rerun",
        action="store_true",
        help="disable bounded adaptive reruns for simulations diagnosed as INSUFFICIENT_MC_PRECISION",
    )
    research_system_audit.add_argument(
        "--adaptive-mc-multiplier",
        type=int,
        default=5,
        help="multiplier for adaptive MC reruns in research benchmark and frontier smoke gates",
    )
    research_system_audit.add_argument(
        "--research-agent-runtime-dir",
        default="",
        help=(
            "optional research-agent-runtime output directory to audit as an AgentRuntime "
            "alignment overlay; when supplied, this overlay participates in gates"
        ),
    )
    research_system_audit.add_argument("--out", default="runs/research_system_audit", help="research system audit output directory")
    research_system_audit.add_argument("--env-file", default=".env")
    research_system_audit.set_defaults(func=lambda args: asyncio.run(_research_system_audit(args)))

    research_architect_theory = sub.add_parser(
        "research-architect-theory",
        help="run Architect -> LLM TheoryDeveloper and persist typed derivation/evidence artifacts",
    )
    research_architect_theory.add_argument("--question-file", default="examples/research_questions.json")
    research_architect_theory.add_argument("--max-questions", type=int, default=0, help="optional cap for quick runs")
    research_architect_theory.add_argument(
        "--provider",
        choices=LIVE_GENERATOR_PROVIDER_CHOICES,
        default=_default_live_generator_provider(),
        help="generator backend; defaults to Anthropic Claude API",
    )
    research_architect_theory.add_argument(
        "--static-response-file",
        default="",
        help="JSON response to replay when --provider static is used",
    )
    research_architect_theory.add_argument(
        "--context-json",
        default="",
        help="optional Architect context JSON with retrieval/proof/simulation feedback",
    )
    research_architect_theory.add_argument(
        "--learning-memory-jsonl",
        action="append",
        default=[],
        help="prior runtime_learning_rows.jsonl to inject as bounded non-evidence prompt memory; repeatable",
    )
    research_architect_theory.add_argument("--max-learning-memory-rows", type=int, default=20)
    research_architect_theory.add_argument(
        "--llm-model",
        default="",
        help="model name for the TheoryDeveloper provider; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_architect_theory.add_argument("--max-tokens", type=int, default=ResearchArchitectConfig().max_tokens)
    research_architect_theory.add_argument("--temperature", type=float, default=0.2)
    research_architect_theory.add_argument("--out", default="runs/research_architect_theory")
    research_architect_theory.add_argument("--env-file", default=".env")
    research_architect_theory.set_defaults(func=_research_architect_theory_develop)

    research_agent_runtime = sub.add_parser(
        "research-agent-runtime",
        help=(
            "run the first AI Statistician AgentRuntime loop: "
            "TheoryDeveloper -> SimulationEvaluator with blackboard/evidence traces"
        ),
    )
    research_agent_runtime.add_argument("--question-file", default="examples/research_questions.json")
    research_agent_runtime.add_argument("--max-questions", type=int, default=0, help="optional cap for quick runs")
    research_agent_runtime.add_argument(
        "--provider",
        choices=LIVE_GENERATOR_PROVIDER_CHOICES,
        default=_default_live_generator_provider(),
        help="generator backend; defaults to Anthropic Claude API",
    )
    research_agent_runtime.add_argument(
        "--static-response-file",
        default="",
        help="JSON response to replay when --provider static is used",
    )
    research_agent_runtime.add_argument(
        "--context-json",
        default="",
        help="optional Architect context JSON with retrieval/proof/simulation feedback",
    )
    research_agent_runtime.add_argument(
        "--learning-memory-jsonl",
        action="append",
        default=[],
        help="prior runtime_learning_rows.jsonl to inject as bounded non-evidence prompt memory; repeatable",
    )
    research_agent_runtime.add_argument("--max-learning-memory-rows", type=int, default=20)
    research_agent_runtime.add_argument(
        "--llm-model",
        default="",
        help="model name for the TheoryDeveloper provider; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_agent_runtime.add_argument("--max-tokens", type=int, default=ResearchArchitectConfig().max_tokens)
    research_agent_runtime.add_argument("--temperature", type=float, default=0.2)
    research_agent_runtime.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
        help=(
            "wall-clock timeout for each live LLM generator request; timeout "
            "exceptions are not retried by default so one subsystem cannot stall "
            "the full AgentRuntime"
        ),
    )
    research_agent_runtime.add_argument(
        "--architect-coordinator-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for top-level ArchitectCoordinator proposals; "
            "same reuses the main live provider, while static requires "
            "--architect-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--architect-static-response-file",
        default="",
        help="JSON ArchitectCoordinator response to replay when --architect-coordinator-provider static",
    )
    research_agent_runtime.add_argument(
        "--architect-llm-model",
        default="",
        help="model name for ArchitectCoordinator proposals; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_agent_runtime.add_argument("--architect-max-tokens", type=int, default=5000)
    research_agent_runtime.add_argument("--architect-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument(
        "--simulation-engineer-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for SimulatorEngineer proposals; same reuses the "
            "main live provider, while static requires --simulation-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--simulation-static-response-file",
        default="",
        help="JSON SimulatorEngineer response to replay when --simulation-engineer-provider static",
    )
    research_agent_runtime.add_argument(
        "--simulation-llm-model",
        default="",
        help="model name for SimulatorEngineer proposals; Anthropic defaults to Claude Haiku 4.5",
    )
    research_agent_runtime.add_argument("--simulation-max-tokens", type=int, default=5000)
    research_agent_runtime.add_argument("--simulation-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument(
        "--algorithm-engineer-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for AlgorithmEngineer proposals; same reuses the "
            "main live provider, while static requires --algorithm-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--algorithm-static-response-file",
        default="",
        help="JSON AlgorithmEngineer response to replay when --algorithm-engineer-provider static",
    )
    research_agent_runtime.add_argument(
        "--algorithm-llm-model",
        default="",
        help="model name for AlgorithmEngineer proposals; Anthropic defaults to Claude Haiku 4.5",
    )
    research_agent_runtime.add_argument("--algorithm-max-tokens", type=int, default=5000)
    research_agent_runtime.add_argument("--algorithm-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument(
        "--formalizer-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for Formalizer/ProofEngineer proposals; same reuses "
            "the main live provider, while static requires --formalizer-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-static-response-file",
        default="",
        help="JSON Formalizer/ProofEngineer response to replay when --formalizer-provider static",
    )
    research_agent_runtime.add_argument(
        "--formalizer-llm-model",
        default="",
        help="model name for Formalizer/ProofEngineer proposals; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_agent_runtime.add_argument("--formalizer-max-tokens", type=int, default=6000)
    research_agent_runtime.add_argument("--formalizer-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument(
        "--critic-evaluator-provider",
        choices=SUBSYSTEM_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "generator backend for CriticEvaluator boundary-audit proposals; same "
            "reuses the main live provider, while static requires --critic-static-response-file"
        ),
    )
    research_agent_runtime.add_argument(
        "--critic-static-response-file",
        default="",
        help="JSON CriticEvaluator response to replay when --critic-evaluator-provider static",
    )
    research_agent_runtime.add_argument(
        "--critic-llm-model",
        default="",
        help="model name for CriticEvaluator proposals; Anthropic defaults to Claude Haiku 4.5",
    )
    research_agent_runtime.add_argument("--critic-max-tokens", type=int, default=5000)
    research_agent_runtime.add_argument("--critic-temperature", type=float, default=0.1)
    research_agent_runtime.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for registered proof-bank subclaims")
    research_agent_runtime.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification for registered proof-bank subclaims")
    research_agent_runtime.add_argument("--lean-project", default="", help="local Lake project used by --local-lean")
    research_agent_runtime.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    research_agent_runtime.add_argument(
        "--theorem-closure-proofengineer-bridge",
        action="store_true",
        help=(
            "after the runtime loop emits theorem-reduction closure work orders, "
            "run the ProofEngineer bridge and export separate learning rows for a later run"
        ),
    )
    research_agent_runtime.add_argument(
        "--theorem-closure-proofengineer-local-lean",
        action="store_true",
        help=(
            "when the theorem-closure ProofEngineer bridge is enabled, run local "
            "lake env lean; only kernel-verified closure rows become proof evidence"
        ),
    )
    research_agent_runtime.add_argument(
        "--theorem-closure-proofengineer-lean-project",
        default="",
        help="local Lake project used by --theorem-closure-proofengineer-local-lean",
    )
    research_agent_runtime.add_argument(
        "--theorem-closure-proofengineer-lean-timeout",
        type=int,
        default=240,
        help="timeout seconds for each theorem-closure local Lean check",
    )
    research_agent_runtime.add_argument(
        "--proof-obligation-id",
        action="append",
        default=[],
        help=(
            "limit registered proof-bank verification to this relevant obligation id; "
            "repeatable. Formal gaps are still emitted."
        ),
    )
    research_agent_runtime.add_argument(
        "--max-proof-obligations",
        type=int,
        default=0,
        help="optional cap on registered proof-bank obligations verified inside AgentRuntime; 0 means no cap",
    )
    research_agent_runtime.add_argument("--runs", type=int, default=100)
    research_agent_runtime.add_argument("--seed", type=int, default=20260528)
    research_agent_runtime.add_argument("--max-iterations", type=int, default=12)
    research_agent_runtime.add_argument(
        "--max-subsystem-retries",
        type=int,
        default=1,
        help=(
            "runtime-level retries for transient provider/subsystem exceptions "
            "such as API connection errors; retry observations are recorded in traces"
        ),
    )
    research_agent_runtime.add_argument(
        "--max-critic-repair-rounds",
        type=int,
        default=1,
        help="bounded CriticEvaluator -> TheoryDeveloper repair loops before accepting remaining gaps",
    )
    research_agent_runtime.add_argument(
        "--capability-eval",
        action="store_true",
        help=(
            "run as a strict main-capability evaluation: reject static/no-Architect/"
            "manual-proof-filter debug modes and return nonzero unless the runtime "
            "capability scorecard is ready"
        ),
    )
    research_agent_runtime.add_argument("--out", default="runs/research_agent_runtime")
    research_agent_runtime.add_argument("--env-file", default=".env")
    research_agent_runtime.set_defaults(func=_research_agent_runtime)

    research_agent_runtime_audit = sub.add_parser(
        "research-agent-runtime-audit",
        help="audit AgentRuntime outputs, agenda/learning rows, and proof-boundary accounting",
    )
    research_agent_runtime_audit.add_argument("--runtime-dir", default="runs/research_agent_runtime")
    research_agent_runtime_audit.add_argument("--out", default="runs/research_agent_runtime_audit")
    research_agent_runtime_audit.set_defaults(func=_research_agent_runtime_audit)

    list_cmd = sub.add_parser("list", help="list registered questions and formal obligations")
    list_cmd.add_argument("--tag", action="append", help="filter obligations by tag")
    list_cmd.set_defaults(func=_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

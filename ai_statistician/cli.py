from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .agent_runtime import AgentTask
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
    LLM_ROUTE_PLANNER_DEFAULT_MAX_STAGED_FOLLOWUP_STAGE_CALLS,
    LLM_ROUTE_PLANNER_DEFAULT_MAX_TOKENS,
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
from .formal_verifier_agentic_proof_source_theorem_integrator import (
    export_formal_verifier_agentic_proof_source_theorem_integrator,
)
from .exact_source_theorem_proof_body_executor import (
    export_exact_source_theorem_proof_body_execution_results,
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
from .pseudo_formalization import (
    PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
    PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
    PSEUDO_FORMAL_INDEPENDENT_BLOCK_VERIFIER_PROVENANCES,
    PSEUDO_FORMAL_NON_ROUTABLE_WORK_ORDER_ROW_KINDS,
    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
    PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP,
)
from .pseudo_formal_block_verifier_worker import (
    export_pseudo_formal_block_verifier_llm_responses,
    export_pseudo_formal_block_verifier_prompt_packets,
    export_pseudo_formal_block_verifier_response_validation,
    run_pseudo_formal_block_verifier_component_gate,
)
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
from .source_theorem_semantic_primitive_proofengineer_bridge import (
    run_source_theorem_semantic_primitive_proofengineer_bridge,
)
from .source_theorem_proof_body_adapter_proofengineer_bridge import (
    run_source_theorem_proof_body_adapter_proofengineer_bridge,
)
from .source_to_bridge_premise_derivation_proofengineer_bridge import (
    run_source_to_bridge_premise_derivation_proofengineer_bridge,
)
from .source_theorem_formal_environment_proofengineer_bridge import (
    export_exact_source_theorem_proof_body_repair_execution_queue,
    run_source_theorem_formal_environment_proofengineer_bridge,
)
from .source_theorem_exact_semantic_definition_source_lookup import (
    run_source_theorem_exact_semantic_definition_candidate_synthesis,
    run_source_theorem_exact_semantic_definition_closure_review,
    run_source_theorem_exact_semantic_definition_source_lookup,
)
from .source_theorem_exact_semantic_definition_proofengineer_bridge import (
    run_source_theorem_exact_semantic_definition_proofengineer_bridge,
)
from .source_theorem_exact_semantic_definition_lean_repair_executor import (
    run_source_theorem_exact_semantic_definition_lean_repair_executor,
)
from .source_theorem_exact_semantic_definition_authoring_worker import (
    AuthoringCandidateMaterializerConfig,
    AuthoringWorkerConfig,
    run_source_theorem_exact_semantic_definition_authoring_candidate_materializer,
    run_source_theorem_exact_semantic_definition_authoring_worker,
)
from .source_theorem_exact_semantic_definition_lean_environment_repair_executor import (
    run_source_theorem_exact_semantic_definition_lean_environment_repair_executor,
)
from .source_theorem_exact_semantic_definition_verifier_gate_executor import (
    run_source_theorem_exact_semantic_definition_verifier_gate_executor,
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
from .architect_research_path_policy_eval import (
    run_architect_research_path_policy_eval,
    write_architect_research_path_policy_eval_failure_manifest,
)
from .algorithm_engineer_llm import AlgorithmEngineerConfig, LLMAlgorithmEngineerAgent
from .algorithm_engineer_generated_code_repair_eval import (
    run_algorithm_engineer_generated_code_repair_eval,
    write_algorithm_engineer_generated_code_repair_eval_failure_manifest,
)
from .simulation_engineer_generated_code_repair_eval import (
    run_simulation_engineer_generated_code_repair_eval,
    write_simulation_engineer_generated_code_repair_eval_failure_manifest,
)
from .coding_agent_generated_code_repair_eval import (
    run_coding_agent_generated_code_repair_eval,
)
from .model_backend import (
    CLAUDE_MODEL_TIERS,
    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    SUPPORTED_GENERATOR_PROVIDERS,
    SUPPORTED_LIVE_GENERATOR_PROVIDERS,
    OpenAIResponsesGeneratorBackend,
    _call_with_wall_clock_timeout,
    default_generator_model,
    default_generator_provider,
)
from .proof_state_feedback import (
    LeanLspMcpProofStateFeedbackProvider,
    LocalLeanProofStateFeedbackProvider,
)
from .simulation_engineer_llm import LLMSimulationEngineerAgent, SimulationEngineerConfig
from .research_agent_runtime import (
    ResearchAgentRuntimeConfig,
    RUNTIME_FORMALIZATION_GAP_PLANNER_LIVE_ROUTE_PLANNER_CONTRACT_REPAIR_TRIGGER,
    RUNTIME_FORMALIZATION_GAP_PLANNER_TARGET_PROVER_REPLAY_ROUTE_REVISION_TRIGGER,
    RUNTIME_FORMAL_GAP_DIRECT_FEEDBACK_LEARNING_TASKS,
    RUNTIME_FORMAL_GAP_LIVE_ROUTE_PLANNER_CONTRACT_FEEDBACK_LEARNING_TASKS,
    RUNTIME_FORMAL_GAP_NEXT_ACTION_ROUTE_IDS,
    RUNTIME_FORMAL_GAP_NEXT_ACTION_TRIGGERS,
    RUNTIME_FORMAL_GAP_ROUTE_FEEDBACK_LEARNING_TASKS,
    RUNTIME_FORMAL_GAP_TARGET_PROVER_REPLAY_FEEDBACK_LEARNING_TASKS,
    RUNTIME_LEARNING_MEMORY_ROUTE_CRITICAL_LEARNING_TASKS,
    RUNTIME_LEARNING_MEMORY_ROUTE_CRITICAL_TRIGGERS,
    RUNTIME_SCHEMA_VERSION,
    _runtime_coding_agent_component_gate_learning_rows,
    _runtime_coding_agent_capability_learning_rows,
    _runtime_coding_agent_capability_table,
    _runtime_component_gate_summary,
    _formalizer_proof_bank_runtime_memory_summary,
    _runtime_formalizer_component_gate_learning_rows,
    _runtime_formalizer_pf_copy_ready_retry_next_action_agenda_rows,
    _runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows,
    _runtime_generated_next_action_learning_rows,
    _runtime_pseudo_formal_block_verifier_component_gate_learning_rows,
    _dedupe_runtime_next_action_agenda_rows,
    _normalize_runtime_blackboard_artifacts,
    _run_runtime_source_theorem_promotion_proofengineer_bridge,
    _write_runtime_learning_rows_jsonl,
    _write_runtime_next_action_agenda_jsonl,
    run_research_agent_runtime,
)
from .research_agent_runtime_audit import audit_research_agent_runtime
from .research_system_audit import ResearchSystemAuditConfig, run_research_system_audit
from .research_trace_audit import audit_research_traces
from .research_training_export import export_research_training_dataset
from .critic_evaluator_llm import CriticEvaluatorConfig, LLMCriticEvaluatorAgent
from .formalizer_llm import FormalizerConfig, LLMFormalizerProofEngineerAgent
from .formalizer_lean_candidate_repair_eval import (
    run_formalizer_lean_candidate_repair_eval,
    write_formalizer_lean_candidate_repair_eval_failure_manifest,
)
from .formalizer_pseudo_formal_packet_eval import (
    FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE,
    run_formalizer_pseudo_formal_packet_eval,
    write_formalizer_pseudo_formal_packet_eval_failure_manifest,
)
from .questions import QUESTIONS, load_question_file
from .retrieval import audit_proof_bank_retrieval
from .system import AIStatisticianSystem, compact_summary, write_run_manifest, write_trace
from .system_audit import SystemAuditConfig, load_audit_questions, run_system_audit
from .task_family import (
    is_explicit_task_family,
    primary_task_family_from_question,
    task_family_value,
)
from .theorem_composition_export import export_theorem_composition_packets
from .theory_proposal import GeneratorTheoryProposer
from .trace_audit import audit_run_traces
from .verifier import AxleProofVerifier, LocalLeanProofVerifier, MockProofVerifier


_DEFAULT_DOTENV = Path(".env")
_OPERATOR_DOTENV_ENV_VAR = "AI_STATISTICIAN_ENV_FILE"
_OPERATOR_DOTENV_FILENAMES = (
    "api_key_AI_statistician.md",
    "api_keys_AI_statistician.md",
)


def _resolve_dotenv_path(path: Path | str | None) -> Path:
    requested = Path(path or _DEFAULT_DOTENV).expanduser()
    if requested.exists():
        return requested
    if requested != _DEFAULT_DOTENV:
        return requested

    operator_env_file = os.environ.get(_OPERATOR_DOTENV_ENV_VAR, "").strip()
    if operator_env_file:
        return Path(os.path.expandvars(operator_env_file)).expanduser()

    for filename in _OPERATOR_DOTENV_FILENAMES:
        candidate = Path.home() / "Downloads" / filename
        if candidate.exists():
            return candidate
    return requested


def _load_dotenv(path: Path) -> None:
    path = _resolve_dotenv_path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("```"):
            continue
        if stripped.lower().startswith("export "):
            stripped = stripped[len("export ") :].strip()
        if "=" in stripped:
            key, value = stripped.split("=", 1)
        elif ":" in stripped:
            key, value = stripped.split(":", 1)
            key = _dotenv_key_from_markdown_label(key)
        else:
            key = _dotenv_key_from_secret_value(stripped)
            value = stripped
        key = key.strip()
        value = value.strip().strip("'\"`")
        if key and value:
            os.environ.setdefault(key, value)


def _dotenv_key_from_markdown_label(label: str) -> str:
    normalized = "".join(
        ch for ch in str(label or "").strip().lower() if ch.isalnum()
    )
    if normalized in {
        "anthropicapikey",
        "anthropicapi",
        "claudeapikey",
        "claudeapi",
    }:
        return "ANTHROPIC_API_KEY"
    if normalized in {"openaiapikey", "openaiapi"}:
        return "OPENAI_API_KEY"
    if normalized in {"aristotleapikey", "aristotleapi"}:
        return "ARISTOTLE_API_KEY"
    if normalized in {
        "axleapikey",
        "axleapi",
        "axiommathaxleapikey",
        "axiommathaxleapi",
    }:
        return "AXLE_API_KEY"
    return str(label or "").strip()


def _dotenv_key_from_secret_value(value: str) -> str:
    stripped = str(value or "").strip()
    if stripped.startswith("sk-ant-"):
        return "ANTHROPIC_API_KEY"
    if stripped.startswith("sk-"):
        return "OPENAI_API_KEY"
    return ""


def _attach_runtime_learning_memory(
    args: argparse.Namespace,
    context: dict[str, object],
    *,
    extra_paths: list[Path] | None = None,
) -> None:
    raw_paths = [
        *(str(item) for item in extra_paths or [] if str(item).strip()),
        *(
            str(item)
            for item in getattr(args, "learning_memory_jsonl", []) or []
            if str(item).strip()
        ),
    ]
    paths = list(dict.fromkeys(raw_paths))
    if not paths:
        return
    context["runtime_learning_memory"] = _load_runtime_learning_memory(
        [Path(item) for item in paths],
        max_rows=int(getattr(args, "max_learning_memory_rows", 20) or 20),
    )


def _attach_runtime_capability_gap_routing(
    args: argparse.Namespace,
    context: dict[str, object],
) -> None:
    raw_paths = [
        str(item)
        for item in getattr(args, "capability_gap_routing_jsonl", []) or []
        if str(item).strip()
    ]
    paths = list(dict.fromkeys(raw_paths))
    if not paths:
        return
    context["runtime_capability_gap_routing"] = (
        _load_runtime_capability_gap_routing(
            [Path(item) for item in paths],
            max_rows=int(getattr(args, "max_capability_gap_routing_rows", 20) or 20),
        )
    )


def _load_runtime_resume_task_from_manifest(
    path: Path,
) -> tuple[str, AgentTask, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    artifact_kind = str(payload.get("artifact_kind", "") or "")
    if artifact_kind == "RuntimePendingNextTask":
        task_payload = payload.get("pending_next_task")
    else:
        task_payload = payload.get("incomplete_pending_next_task")
    if not isinstance(task_payload, Mapping) or not task_payload:
        raise ValueError(
            f"{path} does not contain an incomplete pending runtime task payload"
        )
    task_payload = _runtime_resume_task_payload_with_source_handoff(
        task_payload,
        resume_payload=payload,
        resume_path=path,
    )
    question_id = _runtime_resume_task_question_id(task_payload)
    if not question_id and artifact_kind == "RuntimePendingNextTask":
        question_id = str(payload.get("question_id", "") or "")
    if not question_id:
        question_id = str(payload.get("runtime_failure_summary", {}).get("terminal_question_id", "") or "")
    if not question_id:
        question_ids = payload.get("question_ids")
        if isinstance(question_ids, list) and len(question_ids) == 1:
            question_id = str(question_ids[0] or "")
    if not question_id:
        raise ValueError(
            f"{path} pending task does not expose a question id; cannot resume safely"
        )
    artifacts = _runtime_resume_blackboard_artifacts(
        resume_path=path,
        resume_payload=payload,
        question_id=question_id,
    )
    return (
        question_id,
        _agent_task_from_payload(_normalize_runtime_resume_task_payload(task_payload)),
        artifacts,
    )


def _runtime_resume_task_payload_with_source_handoff(
    task_payload: Mapping[str, Any],
    *,
    resume_payload: Mapping[str, Any],
    resume_path: Path,
) -> dict[str, Any]:
    normalized = dict(task_payload)
    source_handoff = (
        resume_payload.get("source_handoff", {})
        if isinstance(resume_payload.get("source_handoff", {}), Mapping)
        else resume_payload.get("incomplete_pending_next_task_source_handoff", {})
        if isinstance(
            resume_payload.get("incomplete_pending_next_task_source_handoff", {}),
            Mapping,
        )
        else {}
    )
    source_handoff_id = str(
        resume_payload.get("source_handoff_id", "")
        or resume_payload.get("incomplete_pending_next_task_source_handoff_id", "")
        or source_handoff.get("handoff_id", "")
        or ""
    ).strip()
    if not source_handoff_id:
        return normalized
    inputs = (
        dict(normalized.get("inputs", {}))
        if isinstance(normalized.get("inputs", {}), Mapping)
        else {}
    )
    architect_context = (
        dict(inputs.get("architect_context", {}))
        if isinstance(inputs.get("architect_context", {}), Mapping)
        else {}
    )
    if isinstance(architect_context.get("runtime_resume_source_handoff"), Mapping):
        return normalized
    source_manifest_path = str(
        resume_payload.get("source_manifest_path", "")
        or resume_payload.get("_manifest_path", "")
        or resume_path
    )
    architect_context["runtime_resume_source_handoff"] = {
        "artifact_kind": "RuntimeResumeSourceHandoff",
        "handoff_id": source_handoff_id,
        "from_task_id": str(source_handoff.get("from_task_id", "") or ""),
        "to_task_id": str(source_handoff.get("to_task_id", "") or ""),
        "from_subsystem": str(source_handoff.get("from_subsystem", "") or ""),
        "to_subsystem": str(source_handoff.get("to_subsystem", "") or ""),
        "status": str(source_handoff.get("status", "") or ""),
        "failure_classification": str(
            source_handoff.get("failure_classification", "") or ""
        ),
        "produced_artifact_ids": [
            str(value)
            for value in source_handoff.get("produced_artifact_ids", []) or []
            if str(value).strip()
        ],
        "evidence_ids": [
            str(value)
            for value in source_handoff.get("evidence_ids", []) or []
            if str(value).strip()
        ],
        "source_manifest_path": source_manifest_path,
        "source_handoff_export_path": str(
            resume_payload.get("runtime_task_handoffs_jsonl", "") or ""
        ),
        "proof_evidence_status": "RUNTIME_HANDOFF_LINEAGE_NOT_PROOF_EVIDENCE",
        "boundary": (
            "Runtime resume source handoff is orchestration lineage only. "
            "It preserves why this pending task was scheduled, but it is not "
            "statistical, simulation, generated-code, or proof evidence."
        ),
    }
    inputs["architect_context"] = architect_context
    normalized["inputs"] = inputs
    return normalized


def _runtime_resume_learning_memory_paths(path: Path) -> list[Path]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, Mapping):
        return []
    source_manifest = _resolve_runtime_resume_source_manifest(
        resume_path=path,
        resume_payload=payload,
    )
    if source_manifest is None:
        return []
    artifacts = source_manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        return []
    raw_path = str(artifacts.get("runtime_learning_rows_jsonl", "") or "")
    if not raw_path:
        return []
    resolved = _resolve_runtime_resume_path(
        raw_path,
        base_dir=Path(source_manifest.get("_manifest_path", "") or ".").parent,
    )
    return [resolved] if resolved is not None else []


def _normalize_runtime_resume_task_payload(
    task_payload: Mapping[str, object],
) -> dict[str, object]:
    """Fill backward-compatible repair fields for persisted pending runtime tasks."""

    normalized = dict(task_payload)
    inputs = (
        dict(normalized.get("inputs", {}))
        if isinstance(normalized.get("inputs", {}), Mapping)
        else {}
    )
    feedback = (
        dict(inputs.get("environment_feedback", {}))
        if isinstance(inputs.get("environment_feedback", {}), Mapping)
        else {}
    )
    if (
        str(feedback.get("feedback_source", "") or "") == "CriticEvaluator"
        and str(feedback.get("required_revision", "") or "").strip()
    ):
        feedback.setdefault("failure_classification", "critic_requested_theory_revision")
        feedback.setdefault("required_repair", str(feedback.get("required_revision", "")))
        inputs["environment_feedback"] = feedback
        normalized["inputs"] = inputs
    return normalized


def _runtime_resume_blackboard_artifacts(
    *,
    resume_path: Path,
    resume_payload: Mapping[str, Any],
    question_id: str,
) -> dict[str, Any]:
    source_manifest = _resolve_runtime_resume_source_manifest(
        resume_path=resume_path,
        resume_payload=resume_payload,
    )
    if source_manifest is None:
        return {}
    artifacts = source_manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        return {}
    result_paths = artifacts.get("per_question_results", [])
    if not isinstance(result_paths, list):
        return {}
    for raw_result_path in result_paths:
        result_path = _resolve_runtime_resume_path(
            str(raw_result_path),
            base_dir=Path(source_manifest.get("_manifest_path", "") or ".").parent,
        )
        if result_path is None:
            continue
        try:
            result_payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if _runtime_result_question_id(result_payload) != question_id:
            continue
        blackboard = result_payload.get("blackboard", {})
        if not isinstance(blackboard, Mapping):
            return {}
        blackboard_artifacts = blackboard.get("artifacts", {})
        if not isinstance(blackboard_artifacts, Mapping):
            return {}
        normalized_artifacts = _normalize_runtime_blackboard_artifacts(
            blackboard_artifacts
        )
        normalized_artifacts.update(
            _runtime_resume_prior_ledger_artifacts(
                result_payload,
                question_id=question_id,
                source_manifest_path=str(
                    source_manifest.get("_manifest_path", "") or resume_path
                ),
                source_result_path=str(result_path),
            )
        )
        return normalized_artifacts
    return {}


def _runtime_resume_prior_ledger_artifacts(
    result_payload: Mapping[str, Any],
    *,
    question_id: str,
    source_manifest_path: str,
    source_result_path: str,
) -> dict[str, Any]:
    blackboard = (
        result_payload.get("blackboard", {})
        if isinstance(result_payload.get("blackboard", {}), Mapping)
        else {}
    )
    prior_evidence = [
        dict(row)
        for row in blackboard.get("evidence_ledger", []) or []
        if isinstance(row, Mapping)
    ]
    prior_handoffs = [
        dict(row)
        for row in blackboard.get("handoff_ledger", []) or []
        if isinstance(row, Mapping)
    ]
    artifacts: dict[str, Any] = {}
    common = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "question_id": str(question_id or ""),
        "source_manifest_path": str(source_manifest_path or ""),
        "source_result_path": str(source_result_path or ""),
        "proof_evidence_status": "PRIOR_RUNTIME_LEDGER_NOT_CURRENT_EVIDENCE",
        "boundary": (
            "Prior runtime ledger rows are resume continuity memory only. "
            "They are rehydrated as blackboard artifacts, not as current "
            "evidence_ledger or handoff_ledger entries, and do not prove any "
            "new statistical, simulation, generated-code, or theorem claim."
        ),
    }
    if prior_evidence:
        artifacts[f"runtime_resume_prior_evidence_ledger:{question_id}"] = {
            **common,
            "artifact_kind": "RuntimeResumePriorEvidenceLedger",
            "n_prior_evidence_rows": len(prior_evidence),
            "rows": prior_evidence,
        }
    if prior_handoffs:
        artifacts[f"runtime_resume_prior_handoff_ledger:{question_id}"] = {
            **common,
            "artifact_kind": "RuntimeResumePriorHandoffLedger",
            "n_prior_handoff_rows": len(prior_handoffs),
            "rows": prior_handoffs,
        }
    return artifacts


def _resolve_runtime_resume_source_manifest(
    *,
    resume_path: Path,
    resume_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    source_manifest_path = str(resume_payload.get("source_manifest_path", "") or "")
    if not source_manifest_path and str(resume_payload.get("artifact_kind", "") or "") != "RuntimePendingNextTask":
        source_manifest_path = str(resume_path)
    if not source_manifest_path:
        return None
    path = _resolve_runtime_resume_path(source_manifest_path, base_dir=resume_path.parent)
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict):
        payload["_manifest_path"] = str(path)
        return payload
    return None


def _resolve_runtime_resume_path(raw_path: str, *, base_dir: Path) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path)
    candidates = [path]
    if not path.is_absolute():
        candidates.append(base_dir / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _runtime_result_question_id(payload: Mapping[str, Any]) -> str:
    traces = payload.get("traces", [])
    if isinstance(traces, list):
        for trace in traces:
            if not isinstance(trace, Mapping):
                continue
            task = trace.get("task", {})
            if not isinstance(task, Mapping):
                continue
            question_id = _runtime_resume_task_question_id(task)
            if question_id:
                return question_id
    blackboard = payload.get("blackboard", {})
    if isinstance(blackboard, Mapping):
        project_id = str(blackboard.get("project_id", "") or "")
        prefix = "ai_statistician:"
        if project_id.startswith(prefix):
            return project_id[len(prefix) :]
    return ""


def _runtime_resume_task_question_id(task_payload: Mapping[str, object]) -> str:
    inputs = task_payload.get("inputs", {})
    if not isinstance(inputs, Mapping):
        return ""
    question = inputs.get("question", {})
    if isinstance(question, Mapping) and str(question.get("id", "") or ""):
        return str(question.get("id", "") or "")
    environment_feedback = inputs.get("environment_feedback", {})
    if isinstance(environment_feedback, Mapping) and str(
        environment_feedback.get("question_id", "") or ""
    ):
        return str(environment_feedback.get("question_id", "") or "")
    return ""


def _agent_task_from_payload(payload: Mapping[str, object]) -> AgentTask:
    task_id = str(payload.get("task_id", "") or "")
    owner_subsystem = str(payload.get("owner_subsystem", "") or "")
    if not task_id or not owner_subsystem:
        raise ValueError(
            "pending resume task must include task_id and owner_subsystem"
        )
    return AgentTask(
        task_id=task_id,
        owner_subsystem=owner_subsystem,
        objective=str(payload.get("objective", "") or ""),
        inputs=dict(payload.get("inputs", {}) if isinstance(payload.get("inputs"), Mapping) else {}),
        allowed_tools=tuple(
            str(item)
            for item in (
                payload.get("allowed_tools", [])
                if isinstance(payload.get("allowed_tools"), list | tuple)
                else []
            )
        ),
        budget=dict(payload.get("budget", {}) if isinstance(payload.get("budget"), Mapping) else {}),
        expected_artifacts=tuple(
            str(item)
            for item in (
                payload.get("expected_artifacts", [])
                if isinstance(payload.get("expected_artifacts"), list | tuple)
                else []
            )
        ),
        acceptance_gate=str(payload.get("acceptance_gate", "") or ""),
        stop_condition=str(payload.get("stop_condition", "") or ""),
    )


def _select_questions_by_id(
    questions: list[object],
    question_ids: list[str] | tuple[str, ...],
) -> tuple[list[object], list[str]]:
    requested = [str(item).strip() for item in question_ids if str(item).strip()]
    if not requested:
        return questions, []
    by_id = {str(getattr(question, "id", "") or ""): question for question in questions}
    selected: list[object] = []
    missing: list[str] = []
    for question_id in requested:
        question = by_id.get(question_id)
        if question is None:
            missing.append(question_id)
            continue
        selected.append(question)
    return selected, missing


def _selected_question_task_families(questions: list[object]) -> list[str]:
    families: list[str] = []
    for question in questions:
        family = primary_task_family_from_question(question)
        if is_explicit_task_family(family):
            families.append(family)
    return sorted(dict.fromkeys(families))


def _select_questions_by_task_family(
    questions: list[object],
    task_families: list[str] | tuple[str, ...],
) -> tuple[list[object], list[str]]:
    requested = [
        task_family_value(item)
        for item in task_families
        if str(item).strip()
    ]
    if not requested:
        return questions, []
    invalid_requested = [
        item for item in requested if not is_explicit_task_family(item)
    ]
    explicit_requested = [
        item for item in requested if is_explicit_task_family(item)
    ]
    requested_keys = {item.lower() for item in explicit_requested}
    selected: list[object] = []
    available_keys: set[str] = set()
    for question in questions:
        family = primary_task_family_from_question(question)
        if not is_explicit_task_family(family):
            continue
        family_key = family.lower()
        available_keys.add(family_key)
        if family_key in requested_keys:
            selected.append(question)
    missing = [
        *invalid_requested,
        *(
            item
            for item in explicit_requested
            if item.lower() not in available_keys
        ),
    ]
    return selected, missing


def _minimum_task_family_selection_errors(
    questions: list[object],
    *,
    min_task_families: int,
) -> list[str]:
    if min_task_families <= 0:
        return []
    families = _selected_question_task_families(questions)
    if len(families) >= min_task_families:
        return []
    question_ids = [
        str(getattr(question, "id", "") or "")
        for question in questions
        if str(getattr(question, "id", "") or "")
    ]
    return [
        "--min-task-families="
        f"{min_task_families} requires at least {min_task_families} explicit "
        "statistics task families after question selection; selected "
        f"families={families} question_ids={question_ids}"
    ]


def _load_runtime_learning_memory(paths: list[Path], *, max_rows: int = 20) -> dict[str, object]:
    all_rows: list[dict[str, object]] = []
    errors: list[str] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            continue
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_no}: {exc}")
                continue
            if isinstance(payload, dict):
                all_rows.append(_compact_runtime_learning_memory_row(payload))
            else:
                errors.append(f"{path}:{line_no}: expected JSON object")
    row_limit = max(int(max_rows or 0), 0)
    rows: list[dict[str, object]] = []
    retention_policy = "latest_rows"
    if row_limit:
        pinned_by_key: dict[str, tuple[int, int, dict[str, object]]] = {}
        for row_index, row in enumerate(all_rows):
            if not _runtime_learning_memory_should_pin_row(row):
                continue
            pin_key = _runtime_learning_memory_pin_key(row)
            if not pin_key:
                pin_key = f"runtime_learning_row:{row_index}"
            priority = _runtime_learning_memory_pin_priority(row)
            existing = pinned_by_key.get(pin_key)
            if existing is not None and (existing[0], existing[1]) >= (
                priority,
                row_index,
            ):
                continue
            pinned_by_key[pin_key] = (priority, row_index, row)
        prioritized_pins = sorted(
            pinned_by_key.values(),
            key=lambda item: (item[0], item[1]),
            reverse=True,
        )[:row_limit]
        prioritized_pins.sort(key=lambda item: item[1])
        pinned_rows = [row for _priority, _row_index, row in prioritized_pins]
        latest_rows = all_rows[-row_limit:]
        seen: set[str] = set()
        seen_pin_keys: set[str] = set()
        for row in [*pinned_rows, *latest_rows]:
            pin_key = (
                _runtime_learning_memory_pin_key(row)
                if _runtime_learning_memory_should_pin_row(row)
                else ""
            )
            if pin_key and pin_key in seen_pin_keys:
                continue
            fingerprint = json.dumps(row, sort_keys=True, ensure_ascii=False)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            if pin_key:
                seen_pin_keys.add(pin_key)
            rows.append(row)
            if len(rows) >= row_limit:
                break
        if pinned_rows:
            retention_policy = "priority_pinned_latest_rows"
    return {
        "schema_version": 1,
        "artifact_kind": "RuntimeLearningMemoryContext",
        "source_paths": [str(path) for path in paths],
        "rows": rows,
        "counts": {
            "rows_loaded": len(rows),
            "rows_seen": len(all_rows),
            "source_paths": len(paths),
            "errors": len(errors),
            "max_rows": max_rows,
            "retention_policy": retention_policy,
        },
        "errors": errors[:10],
        "boundary": (
            "Prior runtime learning rows are prompt memory and orchestration guidance. "
            "They are not proof evidence, simulation evidence, execution evidence, or source authority."
        ),
    }


def _compact_runtime_capability_gap_routing_row(
    row: Mapping[str, object],
) -> dict[str, object]:
    compact = {
        "schema_version": row.get("schema_version", 1),
        "artifact_kind": str(
            row.get("artifact_kind", "RuntimeCapabilityGapRoutingRow")
            or "RuntimeCapabilityGapRoutingRow"
        ),
        "id": str(row.get("id", "")),
        "requirement_id": str(row.get("requirement_id", "")),
        "scope": str(row.get("scope", "")),
        "gap_status": str(row.get("gap_status", "")),
        "next_owner_subsystem": str(row.get("next_owner_subsystem", "")),
        "target_behavior": str(row.get("target_behavior", "")),
        "success_metric": str(row.get("success_metric", "")),
        "recommended_capability_eval_command": str(
            row.get("recommended_capability_eval_command", "")
        ),
        "blocker": str(row.get("blocker", "")),
        "evidence": str(row.get("evidence", "")),
        "proof_evidence_status": str(row.get("proof_evidence_status", "")),
        "routing_boundary": str(row.get("routing_boundary", "")),
        "fingerprint": str(row.get("fingerprint", "")),
    }
    scorecard_payload = row.get("scorecard_payload", {})
    if isinstance(scorecard_payload, Mapping):
        compact["scorecard_payload"] = (
            _compact_runtime_capability_gap_scorecard_payload(scorecard_payload)
        )
    for key in (
        "priority",
        "retention_selection",
        "retention_selection_boundary",
        "source_artifact_kind",
        "source_scorecard_ready",
        "source_scorecard_runtime_evaluation_mode",
    ):
        if key in row:
            compact[key] = row[key]
    return compact


def _compact_runtime_capability_gap_scorecard_payload(
    payload: Mapping[str, object],
) -> dict[str, object]:
    scorecard_row = (
        payload.get("scorecard_row", {})
        if isinstance(payload.get("scorecard_row", {}), Mapping)
        else {}
    )
    audit_metrics = (
        payload.get("audit_metrics", {})
        if isinstance(payload.get("audit_metrics", {}), Mapping)
        else {}
    )
    return {
        "artifact_kind": str(
            payload.get(
                "artifact_kind",
                "RuntimeCapabilityGapScorecardPayload",
            )
            or "RuntimeCapabilityGapScorecardPayload"
        ),
        "requirement_id": str(payload.get("requirement_id", "")),
        "scorecard_row": {
            str(key): _compact_runtime_capability_gap_value(value)
            for key, value in list(scorecard_row.items())[:12]
        },
        "audit_metrics": {
            key: _compact_runtime_capability_gap_value(value)
            for key, value in _compact_runtime_capability_gap_metric_items(
                audit_metrics,
                limit=24,
            )
        },
        "proof_evidence_status": str(payload.get("proof_evidence_status", "")),
        "boundary": str(payload.get("boundary", ""))[:500],
    }


def _compact_runtime_capability_gap_metric_items(
    audit_metrics: Mapping[str, object],
    *,
    limit: int,
) -> list[tuple[str, object]]:
    indexed_items = [
        (str(key), value, index)
        for index, (key, value) in enumerate(audit_metrics.items())
    ]

    def priority(item: tuple[str, object, int]) -> tuple[int, int]:
        key, value, index = item
        score = 0
        if _runtime_capability_gap_metric_has_signal(key, value):
            score -= 100
        for token, weight in (
            ("architect_initial_routing_deferred_meta", 40),
            ("deferred_meta", 40),
            ("lean_environment_repair", 38),
            ("source_pseudo_formal", 36),
            ("contract_issues", 35),
            ("environment_repair", 32),
            ("missing", 30),
            ("invalid", 30),
            ("exact_semantic_definition", 28),
            ("pseudo_formal", 26),
            ("required", 25),
            ("authoring", 24),
            ("candidate", 22),
            ("proof_evidence_status", 21),
            ("inherited_scope", 20),
            ("scope_parent", 20),
            ("contract_complete", 15),
        ):
            if token in key:
                score -= weight
        return (score, index)

    return [
        (key, value)
        for key, value, _ in sorted(indexed_items, key=priority)[: max(limit, 0)]
    ]


def _runtime_capability_gap_metric_has_signal(key: str, value: object) -> bool:
    if isinstance(value, bool):
        return value is False if "complete" in key or "passed" in key else value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return bool(value)
    return value is not None


def _compact_runtime_capability_gap_value(value: object) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value[:500] if isinstance(value, str) else value
    if isinstance(value, Mapping):
        return {
            str(key): _compact_runtime_capability_gap_value(nested)
            for key, nested in list(value.items())[:12]
        }
    if isinstance(value, list):
        return [_compact_runtime_capability_gap_value(item) for item in value[:12]]
    return str(value)[:500]


def _load_runtime_capability_gap_routing(
    paths: list[Path],
    *,
    max_rows: int = 20,
) -> dict[str, object]:
    all_rows: list[dict[str, object]] = []
    errors: list[str] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            continue
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_no}: {exc}")
                continue
            if not isinstance(payload, dict):
                errors.append(f"{path}:{line_no}: expected JSON object")
                continue
            if str(payload.get("artifact_kind", "") or "") not in {
                "",
                "RuntimeCapabilityGapRoutingRow",
            }:
                errors.append(
                    f"{path}:{line_no}: expected RuntimeCapabilityGapRoutingRow"
                )
                continue
            all_rows.append(_compact_runtime_capability_gap_routing_row(payload))
    row_limit = max(int(max_rows or 0), 0)
    rows: list[dict[str, object]] = []
    retention_policy = "latest_rows"
    if row_limit:
        latest_reserve = _runtime_capability_gap_routing_latest_reserve(
            row_limit=row_limit,
            rows_seen=len(all_rows),
        )
        pinned_rows = _priority_pinned_runtime_capability_gap_rows(
            all_rows,
            max_rows=max(row_limit - latest_reserve, 0),
        )
        latest_capacity = max(row_limit - len(pinned_rows), 0)
        latest_rows = all_rows[-latest_capacity:] if latest_capacity else []
        seen: set[str] = set()
        seen_pin_keys: set[str] = set()
        row_indexes = {id(row): index for index, row in enumerate(all_rows)}

        def append_candidates(
            candidates: list[dict[str, object]],
            *,
            retention_selection: str,
        ) -> None:
            for row in candidates:
                pin_key = _runtime_capability_gap_routing_pin_key(row)
                if pin_key and pin_key in seen_pin_keys:
                    continue
                fingerprint = json.dumps(row, sort_keys=True, ensure_ascii=False)
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                if pin_key:
                    seen_pin_keys.add(pin_key)
                row["retention_selection"] = retention_selection
                row["retention_selection_boundary"] = (
                    "Selection metadata explains why this routing row was "
                    "retained for prompt context; it is not proof evidence, "
                    "simulation evidence, generated-code evidence, verifier "
                    "evidence, or source authority."
                )
                rows.append(row)
                if len(rows) >= row_limit:
                    break

        append_candidates(pinned_rows, retention_selection="priority_pinned")
        if len(rows) < row_limit:
            append_candidates(latest_rows, retention_selection="latest")
        if len(rows) < row_limit:
            append_candidates(
                list(reversed(all_rows)),
                retention_selection="latest_backfill",
            )
        rows.sort(key=lambda row: row_indexes.get(id(row), 0))
        if pinned_rows:
            retention_policy = "priority_pinned_latest_rows"
    return {
        "schema_version": 1,
        "artifact_kind": "RuntimeCapabilityGapRoutingContext",
        "source_paths": [str(path) for path in paths],
        "rows": rows,
        "counts": {
            "rows_loaded": len(rows),
            "rows_seen": len(all_rows),
            "source_paths": len(paths),
            "errors": len(errors),
            "max_rows": max_rows,
            "retention_policy": retention_policy,
        },
        "errors": errors[:10],
        "boundary": (
            "Capability gap routing rows are prompt-routing and work-allocation "
            "context only. They are not proof evidence, simulation evidence, "
            "generated-code evidence, verifier evidence, or source authority."
        ),
    }


def _runtime_capability_gap_routing_latest_reserve(
    *,
    row_limit: int,
    rows_seen: int,
) -> int:
    if row_limit <= 1 or rows_seen <= row_limit:
        return 0
    return min(5, max(1, row_limit // 5))


def _priority_pinned_runtime_capability_gap_rows(
    rows: list[dict[str, object]],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    pinned_by_key: dict[str, tuple[int, int, dict[str, object]]] = {}
    for row_index, row in enumerate(rows):
        priority = _runtime_capability_gap_routing_pin_priority(row)
        if priority < 80:
            continue
        pin_key = _runtime_capability_gap_routing_pin_key(row)
        if not pin_key:
            pin_key = f"runtime_capability_gap_row:{row_index}"
        existing = pinned_by_key.get(pin_key)
        if existing is not None and (existing[0], existing[1]) >= (
            priority,
            row_index,
        ):
            continue
        pinned_by_key[pin_key] = (priority, row_index, row)
    prioritized = sorted(
        pinned_by_key.values(),
        key=lambda item: (item[0], item[1]),
        reverse=True,
    )[:max(max_rows, 0)]
    prioritized.sort(key=lambda item: item[1])
    return [row for _priority, _row_index, row in prioritized]


def _runtime_capability_gap_routing_pin_key(row: Mapping[str, object]) -> str:
    requirement_id = str(row.get("requirement_id", "") or "").strip()
    if not requirement_id:
        requirement_id = str(row.get("id", "") or "").strip()
    if not requirement_id:
        return ""
    scope = str(row.get("scope", "integrated_runtime") or "integrated_runtime")
    return f"{scope}:{requirement_id}"


def _runtime_capability_gap_routing_pin_priority(row: Mapping[str, object]) -> int:
    explicit_priority = row.get("priority", None)
    score = 0
    try:
        if explicit_priority is not None and str(explicit_priority).strip():
            # Audit-generated priority is a scorecard rank: 1 is the first gap.
            score += 10_000 - int(explicit_priority)
    except (TypeError, ValueError):
        pass
    if not score:
        scope = str(row.get("scope", "") or "").strip()
        if scope != "component_calibration":
            score += 20
        else:
            score -= 20
        if str(row.get("gap_status", "") or "").strip().upper() in {"", "OPEN"}:
            score += 10
        owner = str(row.get("next_owner_subsystem", "") or "").strip()
        if owner and owner != "ArchitectCoordinator":
            score += 60
        elif owner == "ArchitectCoordinator":
            score += 10
    requirement_id = str(row.get("requirement_id", "") or "").lower()
    if "deferred_meta" in requirement_id:
        score += 2_000
    critical_tokens = (
        "architect",
        "capability_gap",
        "candidate_materialization",
        "candidate_materialized",
        "candidate_verifier",
        "exact_semantic_definition",
        "exact_proof_body",
        "formal",
        "frontier",
        "kernel",
        "lean",
        "live",
        "proof",
        "pseudo_formal",
        "simulation",
        "source_theorem",
        "theorem",
    )
    if any(token in requirement_id for token in critical_tokens):
        score += 50
    if (
        "candidate_materialization" in requirement_id
        or "candidate_materialized" in requirement_id
    ):
        score += 1_500
    if "exact_semantic_definition" in requirement_id and (
        "authoring" in requirement_id or "candidate_verifier" in requirement_id
    ):
        score += 1_200
    if "source_theorem" in requirement_id and "proof_body" in requirement_id:
        score += 1_000
    if "full_frontier" in requirement_id and "kernel" in requirement_id:
        score += 800
    payload = (
        row.get("scorecard_payload", {})
        if isinstance(row.get("scorecard_payload", {}), Mapping)
        else {}
    )
    audit_metrics = (
        payload.get("audit_metrics", {})
        if isinstance(payload.get("audit_metrics", {}), Mapping)
        else {}
    )
    if any(
        (
            "architect_initial_routing_deferred_meta" in str(key)
            or "deferred_meta" in str(key)
        )
        and _runtime_capability_gap_metric_has_signal(str(key), value)
        for key, value in audit_metrics.items()
    ):
        score += 2_000
    if any(
        (
            "candidate_materialization" in str(key)
            or "candidate_materialized" in str(key)
        )
        and _runtime_capability_gap_metric_has_signal(str(key), value)
        for key, value in audit_metrics.items()
    ):
        score += 1_500
    if any(
        (
            "source_theorem_exact_semantic_definition_authoring" in str(key)
            or "post_runtime_exact_semantic_definition_authoring" in str(key)
        )
        and _runtime_capability_gap_metric_has_signal(str(key), value)
        for key, value in audit_metrics.items()
    ):
        score += 1_200
    if any(
        (
            "source_theorem_exact_semantic_definition_lean_environment_"
            "repair_executor"
            in str(key)
            or "source_theorem_exact_semantic_definition_lean_repair_"
            "executor_n_lean_environment_repair_tasks_from_pseudo_formal"
            in str(key)
            or "source_theorem_exact_semantic_definition_lean_repair_"
            "executor_n_lean_environment_repair_tasks_from_formalizer_pf_component_gate"
            in str(key)
        )
        and (
            _runtime_capability_gap_metric_has_signal(str(key), value)
            or "from_pseudo_formal" in str(key)
            or "source_pseudo_formal" in str(key)
            or "proof_evidence_status" in str(key)
        )
        for key, value in audit_metrics.items()
    ):
        score += 1_200
    if any(
        _runtime_capability_gap_metric_has_signal(str(key), value)
        for key, value in audit_metrics.items()
    ):
        score += 45
    if str(row.get("blocker", "") or "").strip():
        score += 5
    return score


_FORMAL_GAP_NEXT_ACTION_ROUTE_IDS = RUNTIME_FORMAL_GAP_NEXT_ACTION_ROUTE_IDS
_FORMAL_GAP_NEXT_ACTION_TRIGGERS = RUNTIME_FORMAL_GAP_NEXT_ACTION_TRIGGERS
_FORMAL_GAP_DIRECT_FEEDBACK_LEARNING_TASKS = (
    RUNTIME_FORMAL_GAP_DIRECT_FEEDBACK_LEARNING_TASKS
)
_FORMAL_GAP_LIVE_ROUTE_PLANNER_CONTRACT_FEEDBACK_LEARNING_TASKS = (
    RUNTIME_FORMAL_GAP_LIVE_ROUTE_PLANNER_CONTRACT_FEEDBACK_LEARNING_TASKS
)
_FORMAL_GAP_ROUTE_FEEDBACK_LEARNING_TASKS = (
    RUNTIME_FORMAL_GAP_ROUTE_FEEDBACK_LEARNING_TASKS
)
_FORMAL_GAP_TARGET_PROVER_REPLAY_FEEDBACK_LEARNING_TASKS = (
    RUNTIME_FORMAL_GAP_TARGET_PROVER_REPLAY_FEEDBACK_LEARNING_TASKS
)
_RUNTIME_LEARNING_MEMORY_ROUTE_CRITICAL_LEARNING_TASKS = (
    RUNTIME_LEARNING_MEMORY_ROUTE_CRITICAL_LEARNING_TASKS
)
_RUNTIME_LEARNING_MEMORY_ROUTE_CRITICAL_TRIGGERS = (
    RUNTIME_LEARNING_MEMORY_ROUTE_CRITICAL_TRIGGERS
)


def _runtime_learning_memory_bool_like(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _runtime_learning_memory_false_like(value: object) -> bool:
    if isinstance(value, bool):
        return value is False
    if isinstance(value, str):
        return value.strip().lower() in {"0", "false", "no", "n"}
    return False


def _runtime_learning_memory_source_to_bridge_premise_derivation_kernel_verified(
    row: Mapping[str, object],
) -> bool:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    return bool(
        _runtime_learning_memory_bool_like(
            row.get("source_to_bridge_premise_derivation_kernel_verified", False)
        )
        or _runtime_learning_memory_bool_like(
            row.get("premise_derivation_kernel_verified", False)
        )
        or _runtime_learning_memory_bool_like(
            input_summary.get(
                "source_to_bridge_premise_derivation_kernel_verified",
                False,
            )
        )
        or _runtime_learning_memory_bool_like(
            input_summary.get("premise_derivation_kernel_verified", False)
        )
    )


def _runtime_learning_memory_source_theorem_proof_body_adapter_kernel_verified(
    row: Mapping[str, object],
) -> bool:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    return bool(
        _runtime_learning_memory_bool_like(row.get("adapter_kernel_verified", False))
        or _runtime_learning_memory_bool_like(
            row.get("source_theorem_proof_body_adapter_kernel_verified", False)
        )
        or _runtime_learning_memory_bool_like(
            input_summary.get("adapter_kernel_verified", False)
        )
        or _runtime_learning_memory_bool_like(
            input_summary.get(
                "source_theorem_proof_body_adapter_kernel_verified",
                False,
            )
        )
    )


def _runtime_learning_memory_row_trigger(row: Mapping[str, object]) -> str:
    input_summary = row.get("input_summary", {})
    if isinstance(input_summary, Mapping):
        trigger = str(input_summary.get("trigger", "") or "").strip()
        if trigger:
            return trigger
    return str(row.get("trigger", "") or "").strip()


def _runtime_learning_memory_pseudo_formal_bv_mapping(
    row: Mapping[str, object],
) -> dict[str, object]:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    row_value = row.get("block_verification", {})
    input_value = input_summary.get("block_verification", {})
    if isinstance(row_value, Mapping) and row_value:
        return dict(row_value)
    if isinstance(input_value, Mapping):
        return dict(input_value)
    if isinstance(row_value, Mapping):
        return dict(row_value)
    return {}


def _runtime_learning_memory_pseudo_formal_bv_status(
    row: Mapping[str, object],
) -> str:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    row_kind = str(
        row.get("row_kind", "")
        or row.get("pseudo_formal_row_kind", "")
        or input_summary.get("row_kind", "")
        or input_summary.get("pseudo_formal_row_kind", "")
        or ""
    ).strip()
    block_verification = _runtime_learning_memory_pseudo_formal_bv_mapping(row)
    provenance = str(
        row.get("block_verification_verifier_provenance", "")
        or input_summary.get("block_verification_verifier_provenance", "")
        or block_verification.get("verifier_provenance", "")
        or block_verification.get("verifier_source", "")
        or ""
    ).strip()
    independent = bool(
        row.get("block_verification_independent", False)
        or input_summary.get("block_verification_independent", False)
        or block_verification.get("independent_verifier", False)
        or provenance in PSEUDO_FORMAL_INDEPENDENT_BLOCK_VERIFIER_PROVENANCES
    )
    request_role = bool(
        row_kind == PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND
        or row.get("independent_block_verification_required", False)
        or input_summary.get("independent_block_verification_required", False)
        or str(row.get("next_owner_subsystem", "") or "").strip()
        == "BlockVerifier/CalibrationReferee"
        or str(input_summary.get("next_owner_subsystem", "") or "").strip()
        == "BlockVerifier/CalibrationReferee"
    )
    if not request_role:
        return ""
    verdict = str(block_verification.get("verdict", "") or "").strip()
    if independent and verdict in {"accepted", "failed"}:
        return "completed"
    return "pending"


def _runtime_learning_memory_row_is_formal_gap_next_action_routing(
    row: Mapping[str, object],
) -> bool:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    learning_task = str(
        row.get("learning_task", "") or input_summary.get("learning_task", "") or ""
    )
    if learning_task not in _FORMAL_GAP_ROUTE_FEEDBACK_LEARNING_TASKS:
        return False
    if learning_task in _FORMAL_GAP_DIRECT_FEEDBACK_LEARNING_TASKS:
        return True
    agenda_id = str(
        row.get("agenda_id", "") or input_summary.get("agenda_id", "") or ""
    ).strip()
    trigger = _runtime_learning_memory_row_trigger(row)
    return bool(
        agenda_id in _FORMAL_GAP_NEXT_ACTION_ROUTE_IDS
        or trigger in _FORMAL_GAP_NEXT_ACTION_TRIGGERS
    )


def _runtime_learning_memory_formal_gap_next_action_stage(
    row: Mapping[str, object],
) -> str:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    agenda_id = str(
        row.get("agenda_id", "") or input_summary.get("agenda_id", "") or ""
    ).strip()
    learning_task = str(
        row.get("learning_task", "") or input_summary.get("learning_task", "") or ""
    )
    trigger = _runtime_learning_memory_row_trigger(row)
    if (
        learning_task
        in _FORMAL_GAP_LIVE_ROUTE_PLANNER_CONTRACT_FEEDBACK_LEARNING_TASKS
        or trigger
        == RUNTIME_FORMALIZATION_GAP_PLANNER_LIVE_ROUTE_PLANNER_CONTRACT_REPAIR_TRIGGER
    ):
        return "gap_planner_contract_repair"
    if (
        learning_task in _FORMAL_GAP_TARGET_PROVER_REPLAY_FEEDBACK_LEARNING_TASKS
        or trigger
        == RUNTIME_FORMALIZATION_GAP_PLANNER_TARGET_PROVER_REPLAY_ROUTE_REVISION_TRIGGER
    ):
        return "target_prover_replay_route_revision"
    if (
        agenda_id == "formal_gap:gap_planner_handoff"
        or trigger == "FORMAL_GAP_WITH_RUNTIME_GAP_PLANNER_SEED"
    ):
        return "gap_planner_handoff"
    if agenda_id == "formal_gap:proof_bank_expansion" or trigger == "FORMAL_GAP":
        return "proof_bank_expansion"
    return "formal_gap_route"


def _runtime_learning_memory_row_requires_candidate_materialization(
    row: Mapping[str, object],
) -> bool:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    if _runtime_learning_memory_bool_like(
        row.get("candidate_materialization_required", False)
    ) or _runtime_learning_memory_bool_like(
        input_summary.get("candidate_materialization_required", False)
    ):
        return True
    materialization_failures = {
        "source_theorem_candidate_materialization_required",
        "source_theorem_candidate_artifact_missing",
    }
    failure = str(row.get("failure_classification", "") or "")
    input_failure = str(input_summary.get("failure_classification", "") or "")
    if failure in materialization_failures or input_failure in materialization_failures:
        return True
    for probe_row in input_summary.get("signature_probe_rows", []) or []:
        if not isinstance(probe_row, Mapping):
            continue
        probe_failure = str(probe_row.get("failure_classification", "") or "")
        if _runtime_learning_memory_bool_like(
            probe_row.get("candidate_materialization_required", False)
        ):
            return True
        if probe_failure in materialization_failures:
            return True
    return False


def _runtime_learning_memory_pin_priority(row: Mapping[str, object]) -> int:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    learning_task = str(
        row.get("learning_task", "") or input_summary.get("learning_task", "") or ""
    )
    proof_evidence_status = str(
        row.get("proof_evidence_status", "")
        or input_summary.get("proof_evidence_status", "")
        or ""
    )
    runtime_queue_status = str(
        row.get("runtime_queue_status", "")
        or input_summary.get("runtime_queue_status", "")
        or ""
    )
    trigger = str(input_summary.get("trigger", "") or row.get("trigger", "") or "")
    environment_repair_status = str(
        row.get("environment_repair_status", "")
        or input_summary.get("environment_repair_status", "")
        or ""
    )
    direct_source_to_bridge_premise_target_ids = _runtime_learning_memory_string_values(
        row,
        "target_ids",
        "target_theorem_goal_ids",
    )
    direct_source_to_bridge_premise_names = _runtime_learning_memory_string_values(
        row,
        "source_to_bridge_premise_names",
        "premise_names",
        "source_to_bridge_premise_name",
        "premise_name",
    )
    direct_verified_source_to_bridge_premise = bool(
        learning_task == "source_to_bridge_premise_derivation_feedback"
        and direct_source_to_bridge_premise_target_ids
        and direct_source_to_bridge_premise_names
        and (
            _runtime_learning_memory_source_to_bridge_premise_derivation_kernel_verified(
                row
            )
            or bool(
                _runtime_learning_memory_string_values(
                    row,
                    "kernel_verified_source_to_bridge_premise_derivation_ids",
                )
            )
            or proof_evidence_status
            == "KERNEL_VERIFIED_SOURCE_TO_BRIDGE_PREMISE_DERIVATIONS_PRESENT"
        )
    )
    if learning_task == "source_theorem_proof_body_adapter_feedback" and (
        _runtime_learning_memory_source_theorem_proof_body_adapter_kernel_verified(
            row
        )
        or bool(
            _runtime_learning_memory_string_values(
                row,
                "kernel_verified_source_theorem_proof_body_adapter_ids",
            )
        )
        or proof_evidence_status
        == "KERNEL_VERIFIED_SOURCE_THEOREM_PROOF_BODY_ADAPTER_PRESENT"
        or runtime_queue_status
        == "SOURCE_THEOREM_PROOF_BODY_ADAPTER_KERNEL_VERIFIED"
    ):
        return 100
    if direct_verified_source_to_bridge_premise:
        return 98
    if _runtime_learning_memory_row_requires_candidate_materialization(row):
        return 97
    if environment_repair_status:
        return 96
    if _runtime_learning_memory_row_has_typechecked_exact_semantic_definition_candidate(
        row
    ):
        return 95
    if (
        _runtime_learning_memory_source_to_bridge_premise_derivation_kernel_verified(
            row
        )
        or bool(
            _runtime_learning_memory_string_values(
                row,
                "kernel_verified_source_to_bridge_premise_derivation_ids",
            )
        )
        or proof_evidence_status
        == "KERNEL_VERIFIED_SOURCE_TO_BRIDGE_PREMISE_DERIVATIONS_PRESENT"
    ):
        return 94
    if learning_task == "source_theorem_proof_body_adapter_feedback":
        return 93
    if learning_task == "exact_source_theorem_proof_body_execution_feedback":
        return 93
    if learning_task == "source_theorem_formal_environment_repair_feedback":
        return 93
    if learning_task == "source_to_bridge_premise_derivation_feedback":
        return 92
    if learning_task == "theory_derivation_trace_feedback":
        return 91
    if learning_task == "theory_trace_downstream_alignment_feedback":
        return 91
    if _runtime_learning_memory_row_is_formal_gap_next_action_routing(row):
        if _runtime_learning_memory_formal_gap_next_action_stage(row) in {
            "gap_planner_handoff",
            "gap_planner_contract_repair",
            "target_prover_replay_route_revision",
        }:
            return 90
        return 89
    if learning_task == "formalizer_runtime_capability_contract_feedback":
        return 90
    if (
        learning_task
        == "formalizer_pseudo_formal_packet_component_gate_copy_ready_retry_task"
        or trigger == "FORMALIZER_PF_BV_COPY_READY_RETRY_REQUIRED"
        or runtime_queue_status
        == "PENDING_FORMALIZER_PF_BV_RETRY_FROM_COPY_READY_FAILURE"
    ):
        return 90
    if learning_task == PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK:
        row_kind = str(
            row.get("row_kind", "")
            or row.get("pseudo_formal_row_kind", "")
            or input_summary.get("row_kind", "")
            or input_summary.get("pseudo_formal_row_kind", "")
            or ""
        )
        if _runtime_learning_memory_pseudo_formal_bv_status(row) == "completed":
            return 91
        if row_kind in PSEUDO_FORMAL_NON_ROUTABLE_WORK_ORDER_ROW_KINDS:
            return 89
        return 90
    if learning_task == "architect_orchestration_feedback":
        return 90
    if learning_task == "coding_agent_generated_code_capability_feedback":
        return 89
    if learning_task == "runtime_handoff_artifact_missing_feedback":
        return 89
    if learning_task in {
        "formalizer_lean_candidate_kernel_feedback",
        "formalizer_lean_candidate_proof_state_feedback",
    }:
        return 89
    if learning_task == "formalizer_lean_candidate_component_gate_feedback":
        return 88
    if learning_task == "formalizer_pseudo_formal_packet_component_gate_feedback":
        return 88
    if learning_task == "coding_agent_generated_code_component_gate_feedback":
        return 87
    exact_semantic_definition_repair_priority = (
        _runtime_learning_memory_exact_semantic_definition_repair_priority(row)
    )
    if exact_semantic_definition_repair_priority:
        return exact_semantic_definition_repair_priority
    if learning_task == "source_theorem_exact_semantic_definition_work_order":
        return 70
    return 10


def _runtime_learning_memory_pin_key(row: Mapping[str, object]) -> str:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    learning_task = str(
        row.get("learning_task", "") or input_summary.get("learning_task", "") or ""
    )
    target = str(
        row.get("target_theorem_name", "")
        or input_summary.get("target_theorem_name", "")
        or ""
    )
    target_scope_values = _runtime_learning_memory_string_values(
        row,
        "target_ids",
        "target_id",
        "target_theorem_goal_ids",
    )
    target_scope = ",".join(sorted(target_scope_values)) or target
    if not target:
        target = target_scope
    placeholder = str(
        row.get("placeholder_symbol", "")
        or input_summary.get("placeholder_symbol", "")
        or ""
    )
    if _runtime_learning_memory_row_has_typechecked_exact_semantic_definition_candidate(
        row
    ):
        candidate = row.get(
            "source_theorem_exact_semantic_definition_typechecked_candidate",
            input_summary.get(
                "source_theorem_exact_semantic_definition_typechecked_candidate",
                {},
            ),
        )
        if not isinstance(candidate, Mapping):
            candidate = {}
        artifact_path = str(
            row.get("definition_only_candidate_artifact_path", "")
            or input_summary.get("definition_only_candidate_artifact_path", "")
            or candidate.get("definition_only_candidate_artifact_path", "")
            or ""
        ).strip()
        semantic_status = str(
            row.get("semantic_definition_typecheck_evidence_status", "")
            or input_summary.get("semantic_definition_typecheck_evidence_status", "")
            or candidate.get("semantic_definition_typecheck_evidence_status", "")
            or ""
        ).strip()
        return (
            "typechecked_exact_semantic_definition:"
            + target
            + ":"
            + placeholder
            + ":"
            + (artifact_path or semantic_status)
            + ":"
            + _runtime_learning_memory_exact_semantic_definition_repair_pin_stage(row)
        )
    if (
        learning_task == "source_theorem_exact_semantic_definition_work_order"
        and placeholder
    ):
        return f"{learning_task}:{target}:{placeholder}"
    if learning_task == "source_theorem_proof_body_adapter_feedback":
        adapter_unproven_premises = _runtime_learning_memory_string_values(
            row,
            "unproven_bridge_premise_names",
        )
        adapter_ids = _runtime_learning_memory_string_values(
            row,
            "kernel_verified_source_theorem_proof_body_adapter_ids",
        )
        adapter_artifacts = _runtime_learning_memory_string_values(
            row,
            "adapter_candidate_artifact_path",
            "verified_source_theorem_proof_body_adapter_artifact_paths",
        )
        adapter_declarations = _runtime_learning_memory_string_values(
            row,
            "adapter_declaration_name",
            "verified_source_theorem_proof_body_adapter_declarations",
        )
        adapter_kernel_verified = (
            _runtime_learning_memory_source_theorem_proof_body_adapter_kernel_verified(
                row
            )
        )
        if adapter_ids or adapter_kernel_verified:
            return (
                "verified_source_theorem_proof_body_adapter:"
                + target
                + ":"
                + ",".join(adapter_ids)
                + ":"
                + ",".join(adapter_declarations)
                + ":"
                + ",".join(adapter_artifacts)
            )
    premise_names = _runtime_learning_memory_string_values(
        row,
        "source_to_bridge_premise_name",
        "premise_name",
        "source_to_bridge_premise_names",
        "premise_names",
    )
    verified_premise_ids = _runtime_learning_memory_string_values(
        row,
        "kernel_verified_source_to_bridge_premise_derivation_ids",
    )
    if premise_names and (
        _runtime_learning_memory_source_to_bridge_premise_derivation_kernel_verified(
            row
        )
    ):
        return "verified_source_to_bridge_premise:" + target + ":" + ",".join(
            premise_names
        )
    if verified_premise_ids:
        return "verified_source_to_bridge_premise_ids:" + target + ":" + ",".join(
            verified_premise_ids
        )
    if (
        learning_task == "source_theorem_proof_body_adapter_feedback"
        and (premise_names or adapter_unproven_premises)
    ):
        return "source_theorem_proof_body_adapter_feedback:" + target + ":" + ",".join(
            premise_names or adapter_unproven_premises
        )
    if learning_task == "exact_source_theorem_proof_body_execution_feedback":
        failure_classification = str(
            row.get("failure_classification", "")
            or input_summary.get("failure_classification", "")
            or ""
        ).strip()
        proof_body_gate_status = str(
            row.get("proof_body_gate_status", "")
            or input_summary.get("proof_body_gate_status", "")
            or ""
        ).strip()
        artifact_path = str(
            row.get("candidate_artifact_path", "")
            or input_summary.get("candidate_artifact_path", "")
            or row.get("proof_body_artifact_path", "")
            or input_summary.get("proof_body_artifact_path", "")
            or ""
        ).strip()
        return (
            "exact_source_theorem_proof_body_execution_feedback:"
            + target_scope
            + ":"
            + (failure_classification or proof_body_gate_status or "proof_body")
            + ":"
            + artifact_path
        )
    if learning_task == "source_theorem_formal_environment_repair_feedback":
        failure_classification = str(
            row.get("failure_classification", "")
            or input_summary.get("failure_classification", "")
            or ""
        ).strip()
        missing_symbols = ",".join(
            _runtime_learning_memory_string_values(
                row,
                "missing_formal_symbols",
                "formal_environment_placeholder_symbols",
            )
        )
        return (
            "source_theorem_formal_environment_repair_feedback:"
            + target_scope
            + ":"
            + (missing_symbols or placeholder or "formal_environment")
            + ":"
            + failure_classification
        )
    if learning_task == "source_to_bridge_premise_derivation_feedback" and premise_names:
        failure_classification = str(
            row.get("failure_classification", "")
            or input_summary.get("failure_classification", "")
            or ""
        ).strip()
        return (
            "source_to_bridge_premise_derivation_feedback:"
            + target_scope
            + ":"
            + ",".join(premise_names)
            + ":"
            + failure_classification
        )
    if learning_task == "formalizer_lean_candidate_kernel_feedback":
        candidate_id = str(
            row.get("candidate_id", "") or input_summary.get("candidate_id", "") or ""
        ).strip()
        artifact_path = str(
            row.get("artifact_path", "")
            or input_summary.get("artifact_path", "")
            or row.get("kernel_check_artifact_path", "")
            or input_summary.get("kernel_check_artifact_path", "")
            or ""
        ).strip()
        return (
            "formalizer_lean_candidate_kernel_feedback:"
            + target_scope
            + ":"
            + candidate_id
            + ":"
            + artifact_path
        )
    if learning_task == "formalizer_lean_candidate_proof_state_feedback":
        return (
            "formalizer_lean_candidate_proof_state_feedback:"
            + target_scope
            + ":"
            + str(row.get("source_manifest_id", "") or "")
            + ":"
            + str(row.get("source_materialization_manifest_id", "") or "")
        )
    if learning_task == PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK:
        work_order_id = str(
            row.get("source_pseudo_formal_work_order_id", "")
            or input_summary.get("work_order_id", "")
            or row.get("work_order_id", "")
            or ""
        ).strip()
        target_lane = str(
            row.get("target_lane", "") or input_summary.get("target_lane", "") or ""
        ).strip()
        row_kind = str(
            row.get("row_kind", "")
            or row.get("pseudo_formal_row_kind", "")
            or input_summary.get("row_kind", "")
            or input_summary.get("pseudo_formal_row_kind", "")
            or ""
        ).strip()
        source_block_id = str(
            row.get("source_block_id", "")
            or input_summary.get("source_block_id", "")
            or placeholder
            or ""
        ).strip()
        return (
            PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK
            + ":"
            + (target_lane or PSEUDO_FORMAL_TARGET_LANE_FORMAL_GAP)
            + ":"
            + (row_kind or "row")
            + ":"
            + (source_block_id or "block")
            + ":"
            + (work_order_id or "work_order")
        )
    if _runtime_learning_memory_row_requires_candidate_materialization(row):
        return "candidate_materialization_required:" + (target_scope or target)
    if _runtime_learning_memory_row_is_exact_semantic_definition_repair_task(row):
        return (
            "exact_semantic_definition_repair:"
            + target
            + ":"
            + placeholder
            + ":"
            + _runtime_learning_memory_exact_semantic_definition_repair_pin_stage(row)
        )
    if learning_task == "source_theorem_proof_body_adapter_feedback":
        adapter_candidate_imports = _runtime_learning_memory_string_values(
            row,
            "adapter_candidate_imports",
        )
        unavailable_import = str(
            row.get("unavailable_import", "")
            or input_summary.get("unavailable_import", "")
            or ""
        ).strip()
        adapter_artifact = str(
            row.get("adapter_candidate_artifact_path", "")
            or input_summary.get("adapter_candidate_artifact_path", "")
            or ""
        ).strip()
        if unavailable_import or adapter_candidate_imports:
            return (
                "source_theorem_proof_body_adapter_import:"
                + target
                + ":"
                + unavailable_import
                + ":"
                + ",".join(adapter_candidate_imports)
                + ":"
                + adapter_artifact
            )
    if learning_task == "theory_derivation_trace_feedback":
        question_id = str(
            row.get("question_id", "") or input_summary.get("question_id", "") or ""
        ).strip()
        work_order_id = str(
            row.get("work_order_id", "")
            or input_summary.get("work_order_id", "")
            or ""
        ).strip()
        failure_scope = ",".join(
            _runtime_learning_memory_string_values(row, "failure_classifications")
        )
        return (
            "theory_derivation_trace_feedback:"
            + question_id
            + ":"
            + work_order_id
            + ":"
            + failure_scope
        )
    if learning_task == "theory_trace_downstream_alignment_feedback":
        question_id = str(
            row.get("question_id", "") or input_summary.get("question_id", "") or ""
        ).strip()
        work_order_id = str(
            row.get("work_order_id", "")
            or input_summary.get("work_order_id", "")
            or ""
        ).strip()
        consumer = str(
            row.get("target_consumer_subsystem", "")
            or input_summary.get("target_consumer_subsystem", "")
            or ""
        ).strip()
        failure_scope = ",".join(
            _runtime_learning_memory_string_values(row, "failure_classifications")
        )
        return (
            "theory_trace_downstream_alignment_feedback:"
            + question_id
            + ":"
            + consumer
            + ":"
            + work_order_id
            + ":"
            + failure_scope
        )
    if _runtime_learning_memory_row_is_formal_gap_next_action_routing(row):
        question_id = str(
            row.get("question_id", "") or input_summary.get("question_id", "") or ""
        ).strip()
        agenda_id = str(
            row.get("agenda_id", "") or input_summary.get("agenda_id", "") or ""
        ).strip()
        feedback_id = str(
            row.get("route_planner_contract_feedback_id", "")
            or input_summary.get("route_planner_contract_feedback_id", "")
            or row.get("route_revision_proposal_id", "")
            or input_summary.get("route_revision_proposal_id", "")
            or ""
        ).strip()
        trigger = _runtime_learning_memory_row_trigger(row)
        target_scope = ",".join(
            _runtime_learning_memory_string_values(
                row,
                "target_ids",
                "target_id",
                "target_theorem_goal_ids",
                "formal_gap_target_ids",
                "target_theorem_name",
            )
        )
        bridge_ids = _runtime_learning_memory_string_values(
            row,
            "formalization_gap_planner_bridge_id",
            "supporting_formalization_gap_planner_bridge_ids",
        )
        seed_ids = _runtime_learning_memory_string_values(
            row,
            "standalone_seed_artifact_id",
            "supporting_standalone_seed_artifact_ids",
        )
        handoff_ids = _runtime_learning_memory_string_values(
            row,
            "formalization_gap_planner_handoff_id",
            "supporting_formalization_gap_planner_handoff_ids",
            "handoff_id",
        )
        return (
            "formal_gap_next_action_routing:"
            + (question_id or "global")
            + ":"
            + (agenda_id or feedback_id or "formal_gap")
            + ":"
            + trigger
            + ":"
            + (target_scope or target)
            + ":"
            + (",".join(bridge_ids) or ",".join(handoff_ids) or ",".join(seed_ids))
        )
    if learning_task == "formalizer_lean_candidate_component_gate_feedback":
        component_manifest = str(
            row.get("component_eval_manifest_path", "")
            or row.get("source_manifest_path", "")
            or input_summary.get("component_eval_manifest_path", "")
            or ""
        ).strip()
        provider_name = str(
            row.get("provider_name", "")
            or input_summary.get("provider_name", "")
            or ""
        ).strip()
        return (
            "formalizer_lean_candidate_component_gate_feedback:"
            + (component_manifest or provider_name or "attached")
        )
    if learning_task == "formalizer_pseudo_formal_packet_component_gate_feedback":
        component_manifest = str(
            row.get("component_eval_manifest_path", "")
            or row.get("source_manifest_path", "")
            or input_summary.get("component_eval_manifest_path", "")
            or ""
        ).strip()
        provider_name = str(
            row.get("provider_name", "")
            or input_summary.get("provider_name", "")
            or ""
        ).strip()
        return (
            "formalizer_pseudo_formal_packet_component_gate_feedback:"
            + (component_manifest or provider_name or "attached")
        )
    pf_retry_trigger = _runtime_learning_memory_row_trigger(row)
    if (
        learning_task
        == "formalizer_pseudo_formal_packet_component_gate_copy_ready_retry_task"
        or pf_retry_trigger == "FORMALIZER_PF_BV_COPY_READY_RETRY_REQUIRED"
        or str(
            row.get("runtime_queue_status", "")
            or input_summary.get("runtime_queue_status", "")
            or ""
        ).strip()
        == "PENDING_FORMALIZER_PF_BV_RETRY_FROM_COPY_READY_FAILURE"
    ):
        repair_seed = row.get(
            "pseudo_formal_failure_concrete_lane_routable_repair_seed",
            input_summary.get(
                "pseudo_formal_failure_concrete_lane_routable_repair_seed",
                {},
            ),
        )
        if not isinstance(repair_seed, Mapping):
            repair_seed = {}
        question_id = str(
            row.get("question_id", "") or input_summary.get("question_id", "") or ""
        ).strip()
        work_order_id = str(
            row.get("work_order_id", "") or input_summary.get("work_order_id", "") or ""
        ).strip()
        component_manifest = str(
            row.get("component_eval_manifest_path", "")
            or input_summary.get("component_eval_manifest_path", "")
            or ""
        ).strip()
        packet_id = str(
            row.get("target_packet_id", "")
            or input_summary.get("target_packet_id", "")
            or repair_seed.get("packet_id", "")
            or ""
        ).strip()
        theorem_id = str(
            row.get("target_theorem_name", "")
            or input_summary.get("target_theorem_name", "")
            or repair_seed.get("theorem_id", "")
            or ""
        ).strip()
        return (
            "formalizer_pseudo_formal_packet_copy_ready_retry:"
            + (question_id or "global")
            + ":"
            + (component_manifest or work_order_id or packet_id or "attached")
            + ":"
            + (theorem_id or packet_id or work_order_id or "retry")
        )
    if learning_task == "formalizer_runtime_capability_contract_feedback":
        question_id = str(
            row.get("question_id", "") or input_summary.get("question_id", "") or ""
        ).strip()
        failure_classification = str(
            row.get("failure_classification", "")
            or input_summary.get("failure_classification", "")
            or ""
        ).strip()
        missing_flags = ",".join(
            sorted(
                str(item.get("flag", "") or "")
                for item in input_summary.get("missing_contracts", []) or []
                if isinstance(item, Mapping) and str(item.get("flag", "") or "")
            )
        )
        source_failure_id = str(
            row.get("source_failure_id", "")
            or input_summary.get("source_failure_id", "")
            or ""
        ).strip()
        return (
            "formalizer_runtime_capability_contract_feedback:"
            + (target_scope or question_id or "global")
            + ":"
            + (missing_flags or failure_classification or source_failure_id)
        )
    if learning_task == "coding_agent_generated_code_component_gate_feedback":
        component_manifest = str(
            row.get("component_eval_manifest_path", "")
            or row.get("source_manifest_path", "")
            or input_summary.get("component_eval_manifest_path", "")
            or ""
        ).strip()
        provider_name = str(
            row.get("provider_name", "")
            or input_summary.get("provider_name", "")
            or ""
        ).strip()
        return (
            "coding_agent_generated_code_component_gate_feedback:"
            + (component_manifest or provider_name or "attached")
        )
    if learning_task == "coding_agent_generated_code_capability_feedback":
        question_id = str(
            row.get("question_id", "") or input_summary.get("question_id", "") or ""
        ).strip()
        capability_id = str(
            row.get("capability_id", "")
            or input_summary.get("capability_id", "")
            or ""
        ).strip()
        next_owner = str(
            row.get("next_owner_subsystem", "")
            or input_summary.get("next_owner_subsystem", "")
            or ""
        ).strip()
        return (
            "coding_agent_generated_code_capability_feedback:"
            + (question_id or "global")
            + ":"
            + (capability_id or "unknown_capability")
            + ":"
            + (next_owner or "unknown_owner")
        )
    if learning_task == "architect_orchestration_feedback":
        question_id = str(
            row.get("question_id", "") or input_summary.get("question_id", "") or ""
        ).strip()
        work_order_id = str(
            row.get("work_order_id", "")
            or input_summary.get("work_order_id", "")
            or ""
        ).strip()
        pending_task_id = str(
            row.get("pending_task_id", "")
            or input_summary.get("pending_task_id", "")
            or ""
        ).strip()
        architect_status = str(
            row.get("architect_control_status", "")
            or input_summary.get("architect_control_status", "")
            or ""
        ).strip()
        return (
            "architect_orchestration_feedback:"
            + question_id
            + ":"
            + work_order_id
            + ":"
            + pending_task_id
            + ":"
            + architect_status
        )
    if learning_task == "runtime_handoff_artifact_missing_feedback":
        question_id = str(
            row.get("question_id", "") or input_summary.get("question_id", "") or ""
        ).strip()
        work_order_id = str(
            row.get("work_order_id", "")
            or input_summary.get("work_order_id", "")
            or ""
        ).strip()
        missing_artifact_id = str(
            row.get("missing_artifact_id", "")
            or input_summary.get("missing_artifact_id", "")
            or ""
        ).strip()
        repair_owner = str(
            row.get("next_owner_subsystem", "")
            or row.get("repair_owner_agent", "")
            or input_summary.get("repair_owner_agent", "")
            or ""
        ).strip()
        return (
            "runtime_handoff_artifact_missing_feedback:"
            + question_id
            + ":"
            + missing_artifact_id
            + ":"
            + repair_owner
            + ":"
            + work_order_id
        )
    return ""


def _runtime_learning_memory_string_values(
    row: Mapping[str, object],
    *keys: str,
) -> tuple[str, ...]:
    values: list[str] = []
    sources: list[Mapping[str, object]] = [row]
    input_summary = row.get("input_summary", {})
    if isinstance(input_summary, Mapping):
        sources.append(input_summary)
    for source in sources:
        for key in keys:
            raw = source.get(key)
            candidates = raw if isinstance(raw, list | tuple | set) else [raw]
            for value in candidates:
                text = str(value or "").strip()
                if text:
                    values.append(text)
    return tuple(dict.fromkeys(values))


def _runtime_learning_memory_should_pin_row(row: Mapping[str, object]) -> bool:
    if not isinstance(row, Mapping):
        return False
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    trigger = str(input_summary.get("trigger", "") or row.get("trigger", "") or "")
    proof_evidence_status = str(
        row.get("proof_evidence_status", "")
        or input_summary.get("proof_evidence_status", "")
        or ""
    )
    runtime_queue_status = str(
        row.get("runtime_queue_status", "")
        or input_summary.get("runtime_queue_status", "")
        or ""
    )
    learning_task = str(
        row.get("learning_task", "") or input_summary.get("learning_task", "") or ""
    )
    if _runtime_learning_memory_row_is_formal_gap_next_action_routing(row):
        return True
    if learning_task in _RUNTIME_LEARNING_MEMORY_ROUTE_CRITICAL_LEARNING_TASKS:
        return True
    if trigger in _RUNTIME_LEARNING_MEMORY_ROUTE_CRITICAL_TRIGGERS:
        return True
    if (
        learning_task == "source_theorem_proof_body_adapter_feedback"
        and _runtime_learning_memory_pin_priority(row) >= 100
    ):
        return True
    if _runtime_learning_memory_row_has_typechecked_exact_semantic_definition_candidate(
        row
    ):
        return True
    if _runtime_learning_memory_row_is_exact_semantic_definition_repair_task(row):
        return True
    if _runtime_learning_memory_source_to_bridge_premise_derivation_kernel_verified(
        row
    ):
        return True
    if (
        trigger == "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_KERNEL_VERIFIED"
        or proof_evidence_status
        == "KERNEL_VERIFIED_SOURCE_TO_BRIDGE_PREMISE_DERIVATIONS_PRESENT"
    ):
        return True
    if _runtime_learning_memory_string_values(
        row,
        "kernel_verified_source_to_bridge_premise_derivation_ids",
        "verified_source_to_bridge_premise_derivation_signature_excerpts",
        "source_to_bridge_premise_derivation_signature_excerpts",
    ):
        return True
    if (
        learning_task == "source_theorem_proof_body_adapter_feedback"
        and (
            bool(row.get("adapter_candidate_requires_unproven_bridge_premises", False))
            or bool(
                input_summary.get(
                    "adapter_candidate_requires_unproven_bridge_premises",
                    False,
                )
            )
            or bool(row.get("unproven_bridge_premise_names", []) or [])
            or bool(input_summary.get("unproven_bridge_premise_names", []) or [])
            or str(
                row.get("unavailable_import", "")
                or input_summary.get("unavailable_import", "")
                or ""
            ).strip()
            or _runtime_learning_memory_string_values(
                row,
                "adapter_candidate_imports",
            )
        )
    ):
        return True
    placeholder_definition_status = str(
        row.get("placeholder_definition_status", "")
        or input_summary.get("placeholder_definition_status", "")
        or ""
    )
    if learning_task == "source_theorem_exact_semantic_definition_work_order" and (
        runtime_queue_status
        == "PENDING_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_SEMANTIC_DEFINITION"
        or placeholder_definition_status
        == "OPEN_REQUIRES_REVIEWED_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_DEFINITION"
        or proof_evidence_status
        == "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE"
        or bool(row.get("source_to_bridge_adapter_object_names_requiring_source_instantiation", []))
        or bool(
            input_summary.get(
                "source_to_bridge_adapter_object_names_requiring_source_instantiation",
                [],
            )
        )
    ):
        return True
    if _runtime_learning_memory_bool_like(
        row.get("candidate_materialization_required", False)
    ) or _runtime_learning_memory_bool_like(
        input_summary.get("candidate_materialization_required", False)
    ):
        return True
    materialization_failures = {
        "source_theorem_candidate_materialization_required",
        "source_theorem_candidate_artifact_missing",
    }
    failure = str(row.get("failure_classification", "") or "")
    input_failure = str(input_summary.get("failure_classification", "") or "")
    if failure in materialization_failures or input_failure in materialization_failures:
        return True
    for probe_row in input_summary.get("signature_probe_rows", []) or []:
        if not isinstance(probe_row, Mapping):
            continue
        probe_failure = str(probe_row.get("failure_classification", "") or "")
        if _runtime_learning_memory_bool_like(
            probe_row.get("candidate_materialization_required", False)
        ):
            return True
        if probe_failure in materialization_failures:
            return True
    return False


def _runtime_learning_memory_row_is_exact_semantic_definition_repair_task(
    row: Mapping[str, object],
) -> bool:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    placeholder = str(
        row.get("placeholder_symbol", "")
        or input_summary.get("placeholder_symbol", "")
        or ""
    ).strip()
    if not placeholder:
        return False
    learning_task = str(row.get("learning_task", "") or "")
    proof_evidence_status = str(
        row.get("proof_evidence_status", "")
        or input_summary.get("proof_evidence_status", "")
        or ""
    )
    runtime_queue_status = str(
        row.get("runtime_queue_status", "")
        or input_summary.get("runtime_queue_status", "")
        or ""
    )
    trigger = str(input_summary.get("trigger", "") or row.get("trigger", "") or "")
    if learning_task.startswith("source_theorem_exact_semantic_definition_"):
        return True
    if runtime_queue_status in {
        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_REPAIR",
        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW",
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED",
        "PENDING_EXACT_SEMANTIC_DEFINITION_LOCAL_LEAN_CHECK",
        "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_REPAIR",
        "PENDING_LIVE_LLM_EXACT_SEMANTIC_DEFINITION_AUTHORING",
        "BLOCKED_EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED",
        "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_AUTHORING",
        "PENDING_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_SEMANTIC_DEFINITION",
    }:
        return True
    if trigger in {
        "EXACT_SOURCE_SEMANTIC_DEFINITION_WORK_ORDER",
        "EXACT_SOURCE_SEMANTIC_DEFINITION_SOURCE_LOOKUP",
        "EXACT_SOURCE_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION",
        "EXACT_SOURCE_SEMANTIC_DEFINITION_AUTHORING_BACKEND_REQUIRED",
        "EXACT_SOURCE_SEMANTIC_DEFINITION_EXTERNAL_EXPORT_REVIEW_REQUIRED",
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_PROMPT_PACKET",
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_MATERIALIZED",
        "EXACT_SEMANTIC_DEFINITION_LEAN_IMPORT_ENVIRONMENT_REPAIR",
        "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_PREFLIGHT",
        "EXACT_SOURCE_SEMANTIC_DEFINITION_VERIFIER_GATE_REPAIR",
        "SOURCE_TO_BRIDGE_ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER",
    }:
        return True
    if proof_evidence_status in {
        "WORK_ORDER_NOT_PROOF_EVIDENCE",
        "SOURCE_LOOKUP_NOT_PROOF_EVIDENCE",
        "DEFINITION_CLOSURE_WORK_ORDER_NOT_PROOF_EVIDENCE",
        "DEFINITION_CLOSURE_REVIEW_PACKET_NOT_PROOF_EVIDENCE",
        "EXACT_SEMANTIC_DEFINITION_PROOFENGINEER_BRIDGE_NOT_PROOF_EVIDENCE",
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF",
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_MATERIALIZATION_NOT_PROOF_EVIDENCE",
        "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_REPAIR_TASK_NOT_PROOF_EVIDENCE",
        "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_REPAIR_EXECUTION_NOT_PROOF_EVIDENCE",
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_EXECUTION_NOT_SOURCE_THEOREM_PROOF",
        "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE",
        "GENERATED_NEXT_ACTION_ROUTING_NOT_PROOF_EVIDENCE",
    } and (
        "semantic_definition" in learning_task
        or "semantic_definition" in trigger.lower()
        or runtime_queue_status.startswith("PENDING_")
    ):
        return True
    return False


def _runtime_learning_memory_exact_semantic_definition_repair_priority(
    row: Mapping[str, object],
) -> int:
    if not _runtime_learning_memory_row_is_exact_semantic_definition_repair_task(row):
        return 0
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    learning_task = str(row.get("learning_task", "") or "")
    proof_evidence_status = str(
        row.get("proof_evidence_status", "")
        or input_summary.get("proof_evidence_status", "")
        or ""
    )
    runtime_queue_status = str(
        row.get("runtime_queue_status", "")
        or input_summary.get("runtime_queue_status", "")
        or ""
    )
    trigger = str(input_summary.get("trigger", "") or row.get("trigger", "") or "")
    failure_classification = str(
        row.get("failure_classification", "")
        or input_summary.get("failure_classification", "")
        or ""
    ).strip()
    environment_repair_status = str(
        row.get("environment_repair_status", "")
        or input_summary.get("environment_repair_status", "")
        or ""
    ).strip()
    semantic_status = str(
        row.get("semantic_definition_typecheck_evidence_status", "")
        or input_summary.get("semantic_definition_typecheck_evidence_status", "")
        or ""
    ).strip()
    artifact_path = str(
        row.get("definition_only_candidate_artifact_path", "")
        or row.get("candidate_artifact_path", "")
        or input_summary.get("definition_only_candidate_artifact_path", "")
        or input_summary.get("candidate_artifact_path", "")
        or ""
    ).strip()
    if environment_repair_status:
        return 96
    if (
        runtime_queue_status == "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_REPAIR"
        or trigger == "EXACT_SOURCE_SEMANTIC_DEFINITION_VERIFIER_GATE_REPAIR"
        or failure_classification.startswith(
            "exact_semantic_definition_verifier_gate_"
        )
    ):
        return 95
    if (
        runtime_queue_status
        in {
            "PENDING_LIVE_LLM_EXACT_SEMANTIC_DEFINITION_AUTHORING",
            "BLOCKED_EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED",
            "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_AUTHORING",
        }
        or trigger
        in {
            "EXACT_SOURCE_SEMANTIC_DEFINITION_AUTHORING_BACKEND_REQUIRED",
            "EXACT_SOURCE_SEMANTIC_DEFINITION_EXTERNAL_EXPORT_REVIEW_REQUIRED",
            "EXACT_SEMANTIC_DEFINITION_AUTHORING_PROMPT_PACKET",
        }
    ):
        return 94
    if (
        artifact_path
        or semantic_status
        or runtime_queue_status
        in {
            "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_REPAIR",
            "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW",
            "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED",
            "PENDING_EXACT_SEMANTIC_DEFINITION_LOCAL_LEAN_CHECK",
        }
        or (
            learning_task
            in {
                "source_theorem_exact_semantic_definition_work_order",
                "source_theorem_exact_semantic_definition_source_lookup",
                "source_theorem_exact_semantic_definition_closure_work_order",
                "source_theorem_exact_semantic_definition_closure_review_packet",
                "source_theorem_exact_semantic_definition_proofengineer_bridge",
            }
            and proof_evidence_status != (
                "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE"
            )
        )
    ):
        return 92
    if "lean_environment" in learning_task or runtime_queue_status == "LAKEFILE_MISSING":
        return 89
    return 88


def _runtime_learning_memory_exact_semantic_definition_repair_pin_stage(
    row: Mapping[str, object],
) -> str:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    runtime_queue_status = str(
        row.get("runtime_queue_status", "")
        or input_summary.get("runtime_queue_status", "")
        or ""
    ).strip()
    trigger = str(input_summary.get("trigger", "") or row.get("trigger", "") or "")
    failure_classification = str(
        row.get("failure_classification", "")
        or input_summary.get("failure_classification", "")
        or ""
    ).strip()
    if (
        runtime_queue_status == "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_REPAIR"
        or trigger == "EXACT_SOURCE_SEMANTIC_DEFINITION_VERIFIER_GATE_REPAIR"
        or failure_classification.startswith(
            "exact_semantic_definition_verifier_gate_"
        )
    ):
        return "verifier_gate_repair"
    if (
        runtime_queue_status == "BLOCKED_EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED"
        or trigger == "EXACT_SOURCE_SEMANTIC_DEFINITION_EXTERNAL_EXPORT_REVIEW_REQUIRED"
    ):
        return "authoring_external_export_review_required"
    if (
        runtime_queue_status
        in {
            "PENDING_LIVE_LLM_EXACT_SEMANTIC_DEFINITION_AUTHORING",
            "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_AUTHORING",
        }
        or trigger
        in {
            "EXACT_SOURCE_SEMANTIC_DEFINITION_AUTHORING_BACKEND_REQUIRED",
            "EXACT_SEMANTIC_DEFINITION_AUTHORING_PROMPT_PACKET",
        }
    ):
        return "authoring_backend_required"
    return (
        trigger.strip()
        or runtime_queue_status
        or str(row.get("proof_evidence_status", "") or "").strip()
        or str(row.get("learning_task", "") or "").strip()
        or "unspecified"
    )


def _runtime_learning_memory_row_has_typechecked_exact_semantic_definition_candidate(
    row: Mapping[str, object],
) -> bool:
    input_summary = row.get("input_summary", {})
    if not isinstance(input_summary, Mapping):
        input_summary = {}
    candidate = row.get(
        "source_theorem_exact_semantic_definition_typechecked_candidate",
        input_summary.get(
            "source_theorem_exact_semantic_definition_typechecked_candidate",
            {},
        ),
    )
    if not isinstance(candidate, Mapping):
        candidate = {}
    semantic_status = str(
        row.get("semantic_definition_typecheck_evidence_status", "")
        or input_summary.get("semantic_definition_typecheck_evidence_status", "")
        or candidate.get("semantic_definition_typecheck_evidence_status", "")
        or ""
    )
    local_compiled = bool(
        row.get("local_definition_lean_compiled", False)
        or input_summary.get("local_definition_lean_compiled", False)
        or candidate.get("local_definition_lean_compiled", False)
    )
    artifact_path = str(
        row.get("definition_only_candidate_artifact_path", "")
        or input_summary.get("definition_only_candidate_artifact_path", "")
        or candidate.get("definition_only_candidate_artifact_path", "")
        or ""
    ).strip()
    if local_compiled and (artifact_path or semantic_status):
        return True
    return semantic_status in {
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF",
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_LOCAL_LEAN_COMPILED_REVIEW_REQUIRED",
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED",
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED",
    }


def _compact_runtime_learning_memory_row(row: Mapping[str, object]) -> dict[str, object]:
    compact = {
        "schema_version": row.get("schema_version", 1),
        "question_id": str(row.get("question_id", "")),
        "artifact_kind": str(row.get("artifact_kind", "")),
        "learning_task": str(row.get("learning_task", "")),
        "input_summary": _compact_runtime_learning_input_summary(
            row.get("input_summary", {})
        ),
        "target_behavior": str(row.get("target_behavior", "")),
        "acceptance_gate": str(row.get("acceptance_gate", "")),
    }
    for key in (
        "work_order_id",
        "next_owner_subsystem",
        "source_manifest_id",
        "source_materialization_manifest_id",
        "source_failure_id",
        "source_manifest_path",
        "source_rows_path",
        "source_formalizer_packet_id",
        "source_agenda_id",
        "source_prompt_packet_id",
        "source_authoring_task_id",
        "source_pseudo_formal_work_order_id",
        "source_formalizer_proposal_id",
        "source_formalization_manifest_id",
        "source_packet_id",
        "prompt_scaffold_origin",
        "source_prompt_scaffold_kind",
        "source_prompt_scaffold_id",
        "source_prompt_scaffold_required_output_key",
        "source_artifact_id",
        "source_theorem_id",
        "source_block_id",
        "source_block_type",
        "source_block_conclusion",
        "block_depth",
        "dependency_scope",
        "scope_parent_id",
        "source_block_proof_text",
        "structural_quality_ok",
        "faithfulness_status",
        "faithfulness_repair_status",
        "block_verification",
        "structural_quality",
        "block_verification_verifier_provenance",
        "block_verification_independent",
        "independent_block_verification_required",
        "independent_block_verification_status",
        "independent_block_verification_completed",
        "bv_calibration",
        "pseudo_formal_method_contract_id",
        "pseudo_formal_pipeline_stage",
        "feedback_type",
        "algorithm_sandbox_manifest_id",
        "simulation_manifest_id",
        "estimator_id",
        "simulation_id",
        "prototype_status",
        "executor",
        "smoke_passed",
        "execution_smoke_passed",
        "script_path",
        "code_excerpt",
        "stderr_summary",
        "reason",
        "required_repair",
        "n_prototypes",
        "n_executed",
        "n_passed",
        "n_metric_gate_failed",
        "n_generated_code_executed",
        "n_unsafe_generated_code_rejected",
        "n_generated_simulation_sandbox_prototypes",
        "n_generated_simulation_sandbox_executed",
        "n_generated_simulation_sandbox_passed",
        "n_generated_simulation_sandbox_metric_gate_failed",
        "n_unsafe_generated_simulation_code_rejected",
        "action_type",
        "target_theorem_name",
        "target_lean_declaration",
        "candidate_id",
        "candidate_kind",
        "source_field",
        "source_hash",
        "placeholder_symbol",
        "replacement_strategy",
        "next_step_kind",
        "definition_candidate_status",
        "artifact_path",
        "precheck_status",
        "target_lean_file",
        "target_lean_line",
        "target_lean_column",
        "local_lean_attempted",
        "local_lean_compiled",
        "local_lean_exit_status",
        "local_lean_project",
        "local_lean_timeout",
        "local_lean_skipped_reason",
        "local_lean_stdout_excerpt",
        "local_lean_stderr_excerpt",
        "kernel_verified",
        "source_theorem_target_known",
        "diagnostic_helper_not_source_theorem",
        "lean_source_excerpt",
        "review_status",
        "forbidden_placeholder_detected",
        "semantic_definition_risk_detected",
        "ready_for_definition_lean_check",
        "candidate_synthesis_status",
        "definition_candidate_review_mode",
        "replacement_applied",
        "semantic_risk",
        "source_theorem_kernel_evidence_eligible",
        "source_theorem_kernel_verified",
        "source_theorem_proof_body_adapter_kernel_verified",
        "semantic_definition_kernel_verified",
        "adapter_kernel_verified",
        "adapter_candidate_evidence_eligible",
        "adapter_candidate_artifact_path",
        "adapter_declaration_name",
        "synthesized_candidate_artifact_path",
        "definition_only_candidate_artifact_path",
        "local_definition_lean_checked",
        "local_definition_lean_compiled",
        "semantic_definition_typecheck_evidence_status",
        "lookup_id",
        "lookup_status",
        "semantic_closure_status",
        "placeholder_definition_status",
        "source_theorem_ready_for_exact_proof_body",
        "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
        "source_theorem_semantic_support_only",
        "source_semantic_alignment_review_required",
        "source_theorem_target_identity_status",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "proof_boundary",
        "boundary",
        "priority",
        "formalization_gap_planner_bridge_id",
        "standalone_seed_artifact_id",
        "formalization_gap_planner_handoff_id",
        "handoff_id",
        "formalization_gap_planner_execution_contexts",
        "formalization_gap_planner_execution_plan_stage_ids",
        "standalone_seed_path",
        "target_intake_path",
        "target_intake_cli",
        "component_resource_registry_cli",
        "standalone_plan_cli",
        "llm_route_planner_prompt_cli",
        "llm_route_planner_live_cli",
        "reuse_smoke_cli",
        "recommended_llm_provider",
        "recommended_model_tier",
        "target_prover_family",
        "memory_status",
        "next_owner_agent",
        "next_action",
        "proof_body_attempt_source",
        "trigger",
        "execution_status",
        "source_execution_status",
        "source_execution_result_id",
        "source_lean_repair_task_id",
        "authoring_trigger",
        "authoring_mode",
        "runtime_queue_status",
        "verifier_gate_status",
        "verifier_gate_result_id",
        "source_verifier_gate_work_order_id",
        "source_anchor_context_rows",
        "runtime_generated_queue_name",
        "environment_repair_status",
        "candidate_lean_project_hint",
        "candidate_source_file",
        "unavailable_module_prefix",
        "dependency_fetch_required",
        "ready_to_rerun_lean_repair",
        "source_environment_repair_task_id",
        "source_to_bridge_metadata_blocker_status",
        "source_to_bridge_metadata_blocker_kind",
        "source_formalizer_packet_id",
        "recommended_formalizer_target_mode",
        "candidate_request_id",
        "source_kind",
        "source_index",
        "metadata_authoring_status",
        "request_complete",
        "failure_classification",
        "route_planner_contract_feedback_id",
        "route_revision_proposal_id",
        "refinement_evidence_id",
        "refinement_item_id",
        "goal_plan_id",
        "route_id",
        "route_revision_summary",
        "route_revision_overlay_dir",
        "route_revision_overlay_manifest",
        "n_route_revision_overlay_rows",
        "n_route_revision_overlay_routes_with_revision",
        "n_route_revision_overlay_orphan_rows",
        "prover_attempt_status",
        "prover_attempt_class",
        "prover_diagnostic_signature",
        "source_target_prover_family",
        "refinement_evidence_dir",
        "route_revision_proposals_path",
        "contract_counts",
        "provider_token_counts",
        "runtime_requested_evidence_contract",
        "formalizer_candidate_local_lean",
        "proof_state_provider",
        "n_candidate_sources",
        "n_local_lean_checked",
        "n_live_proof_state_requests",
        "n_lean_lsp_mcp_ready_requests",
        "candidate_proof_state_manifest_id",
        "candidate_artifact_path",
        "source_candidate_artifact_path",
        "adapter_candidate_artifact_path",
        "adapter_declaration_name",
        "adapter_kernel_verified",
        "adapter_candidate_evidence_eligible",
        "signature_probe_artifact_path",
        "proof_body_signature_probe_artifact_path",
        "execution_transcript_path",
        "proof_body_gate_status",
        "proof_body_status",
        "proof_body_signature_probe_artifact_rows",
        "proof_body_signature_artifact_count",
        "source_theorem_proof_body_signature_artifact_count",
        "proof_body_goal_reached",
        "proof_body_semantic_review_blocked",
        "proof_body_attempt_blocked_before_goal",
        "proof_body_attempted",
        "proof_body_attempt_count",
        "proof_body_attempt_success",
        "proof_body_goal_conclusion",
        "source_to_bridge_premise_goal_conclusion",
        "adapter_candidate_requires_unproven_bridge_premises",
        "unavailable_import",
        "premise_name",
        "source_to_bridge_premise_name",
        "premise_target_type",
        "premise_target_source",
        "source_to_bridge_premise_target_type",
        "premise_derivation_kernel_verified",
        "source_to_bridge_premise_derivation_kernel_verified",
        "premise_candidate_artifact_path",
        "premise_candidate_declaration_name",
        "source_to_bridge_premise_candidate_artifact_path",
        "source_to_bridge_premise_candidate_declaration_name",
        "candidate_contract",
        "premise_derivation_gap_kind",
        "recommended_next_action",
        "source_to_bridge_premise_derivation_candidate_request_id",
        "source_to_bridge_grouped_premise_derivation_candidate_request_id",
        "source_to_bridge_premise_derivation_source_candidate_request_id",
        "source_to_bridge_grouped_premise_derivation_source_candidate_request_id",
        "adapter_instantiation_group_id",
        "shared_adapter_instantiation_contract",
        "semantic_anchor_reference_gate",
        "candidate_materialization_required",
        "candidate_materialization_contract",
        "source_theorem_exact_semantic_definition_typechecked_candidate",
        "row_kind",
        "target_lane",
        "semantic_primitive_id",
        "capability_id",
        "recommended_capability_eval_command",
        "success_metric",
        "component_eval",
        "component_eval_manifest_path",
        "provider_name",
        "backend_provider_name",
        "model",
        "live_generator",
        "static_or_fixture_only",
        "capability_evidence_ok",
        "algorithm_capability_evidence_ok",
        "simulation_capability_evidence_ok",
        "repair_sequences",
        "algorithm_repair_sequences",
        "simulation_repair_sequences",
        "algorithm_live_repair_sequences",
        "simulation_live_repair_sequences",
        "local_lean_checked",
        "local_lean_compiled",
        "proofengineer_repair_task_observed",
        "prior_feedback_proof_state_provider",
        "prior_feedback_proof_state_rows",
        "candidate_kernel_verified",
        "full_frontier_theorem_proved",
        "prior_failure_feedback_injected",
        "autonomous_live_failed_then_passed_repair_observed",
        "capability_evidence_scope",
        "target_component",
        "missing_contracts",
        "required_runtime_configuration",
        "required_formalizer_behavior",
        "pseudo_formal_block_verifier_worker",
    ):
        value = row.get(key)
        if value not in (None, "", [], {}):
            compact[key] = _compact_runtime_learning_field_value(key, value)
    if "scope_parent_id" in row and "scope_parent_id" not in compact:
        compact["scope_parent_id"] = str(row.get("scope_parent_id", "") or "")
    for key in (
        "recommended_proof_obligation_ids",
        "selected_proof_obligation_ids",
        "target_ids",
        "dependency_ids",
        "dependency_statement_context",
        "inherited_scope",
        "source_block_premises",
        "structural_quality_issues",
        "kernel_verified_proof_obligation_ids",
        "proved_non_kernel_proof_obligation_ids",
        "failed_proof_obligation_ids",
        "formal_gap_target_ids",
        "kernel_verified_theorem_reduction_closure_work_order_ids",
        "kernel_verified_theorem_reduction_closure_target_ids",
        "kernel_verified_theorem_reduction_closure_declarations",
        "verified_theorem_reduction_closure_artifact_paths",
        "kernel_verified_theorem_reduction_closure_signature_excerpts",
        "kernel_verified_theorem_reduction_closure_goal_ids",
        "kernel_verified_source_theorem_semantic_definition_ids",
        "kernel_verified_source_theorem_proof_body_adapter_ids",
        "verified_source_theorem_proof_body_adapter_artifact_paths",
        "verified_source_theorem_proof_body_adapter_declarations",
        "kernel_verified_source_theorem_semantic_support_obligation_ids",
        "kernel_verified_source_theorem_semantic_primitive_ids",
        "candidate_registered_obligation_ids",
        "search_targets",
        "source_lookup_hits",
        "semantic_alignment_blockers",
        "semantic_alignment_constraints",
        "verifier_gate_blockers",
        "known_gaps",
        "source_anchor_context",
        "recommended_repair_tasks",
        "proof_body_recheck_blockers",
        "candidate_source_declarations",
        "candidate_source_references",
        "required_next_checks",
        "forbidden_placeholder_matches",
        "semantic_definition_risks",
        "recommended_commands",
        "local_lean_diagnostics",
        "verified_bridge_obligation_ids",
        "proof_body_attempt_summaries",
        "proof_body_goal_excerpt",
        "proof_body_goal_binder_names",
        "source_to_bridge_premise_goal_binder_names",
        "proof_body_signature_probe_artifact_paths",
        "source_theorem_exact_proof_body_gate_open_target_names",
        "exact_goal_shape_obligation_ids",
        "exact_goal_shape_obligations",
        "diagnostics",
        "adapter_candidate_imports",
        "precheck_errors",
        "prototypes",
        "generated_simulation_prototypes",
        "metric_gate_errors",
        "safety_errors",
        "premise_names",
        "unproven_bridge_premise_names",
        "source_to_bridge_premise_names",
        "premise_semantic_anchor_binder_names",
        "premise_semantic_anchor_binders",
        "exact_source_theorem_binders",
        "required_semantic_anchor_reference_names",
        "required_bridge_premise_names_for_shared_instantiation",
        "adapter_object_names_requiring_source_instantiation",
        "source_to_bridge_adapter_object_names_requiring_source_instantiation",
        "diagnostic_helper_candidate_ids",
        "source_to_bridge_metadata_blocker_target_ids",
        "source_to_bridge_metadata_blocker_helper_candidate_ids",
        "supporting_formalization_gap_planner_bridge_ids",
        "supporting_standalone_seed_artifact_ids",
        "supporting_formalization_gap_planner_handoff_ids",
        "target_theorem_goal_ids",
        "missing_required_metadata_fields",
        "required_candidate_fields",
        "candidate_materialization_statuses",
        "kernel_verified_source_to_bridge_premise_derivation_ids",
        "verified_source_to_bridge_premise_derivation_signature_excerpts",
        "source_to_bridge_premise_derivation_signature_excerpts",
        "premise_candidate_signature_excerpts",
        "failure_classifications",
        "staged_followup_assembly_error_summary",
        "staged_followup_assembly_error_preview",
        "target_primitives",
        "revised_selected_primitives",
        "revised_delta_primitives",
        "route_revision_reasons",
        "route_revision_overlay_dirs",
        "route_revision_overlay_manifests",
        "source_anchors",
        "required_theory_trace_consumers",
        "theory_trace_consuming_subsystems",
        "structured_theory_trace_aligned_subsystems",
        "component_backend_provider_names",
    ):
        values = row.get(key, ())
        if isinstance(values, list):
            if key in {"prototypes", "generated_simulation_prototypes"}:
                compact[key] = [
                    _compact_runtime_learning_sandbox_prototype(item)
                    for item in values[:5]
                    if isinstance(item, Mapping)
                ]
                continue
            compact[key] = [
                _compact_runtime_learning_value(item)
                for item in values
                if str(item).strip()
            ]
    for key in (
        "source_to_bridge_premise_derivation_candidate_request",
        "source_to_bridge_grouped_premise_derivation_candidate_request",
        "source_to_bridge_premise_derivation_source_candidate_request",
        "source_to_bridge_grouped_premise_derivation_source_candidate_request",
        "proof_body_goal_context",
        "source_to_bridge_premise_goal_context",
    ):
        value = row.get(key)
        if isinstance(value, Mapping):
            if key in {
                "source_to_bridge_premise_derivation_candidate_request",
                "source_to_bridge_grouped_premise_derivation_candidate_request",
                "source_to_bridge_premise_derivation_source_candidate_request",
                "source_to_bridge_grouped_premise_derivation_source_candidate_request",
            }:
                compact[key] = _compact_source_to_bridge_premise_request(value)
            else:
                compact[key] = _compact_runtime_learning_value(value)
    value = row.get("candidate_definition_request")
    if isinstance(value, Mapping):
        compact["candidate_definition_request"] = (
            _compact_candidate_definition_request(value)
        )
    input_summary = compact.get("input_summary", {})
    if isinstance(input_summary, Mapping):
        for key in (
            "adapter_candidate_artifact_path",
            "adapter_declaration_name",
            "target_theorem_name",
            "adapter_kernel_verified",
            "source_theorem_proof_body_adapter_kernel_verified",
            "verified_source_theorem_proof_body_adapter_artifact_paths",
            "verified_source_theorem_proof_body_adapter_declarations",
            "adapter_candidate_evidence_eligible",
            "source_candidate_artifact_path",
            "execution_status",
            "source_execution_status",
            "source_execution_result_id",
            "source_lean_repair_task_id",
            "authoring_trigger",
            "authoring_mode",
            "verifier_gate_status",
            "verifier_gate_result_id",
            "source_verifier_gate_work_order_id",
            "source_anchor_context_rows",
            "source_to_bridge_premise_derivation_candidate_request_id",
            "source_to_bridge_grouped_premise_derivation_candidate_request_id",
            "source_to_bridge_premise_derivation_source_candidate_request_id",
            "source_to_bridge_grouped_premise_derivation_source_candidate_request_id",
            "candidate_materialization_required",
            "candidate_materialization_contract",
            "source_agenda_id",
            "source_pseudo_formal_work_order_id",
            "source_formalizer_proposal_id",
            "source_formalization_manifest_id",
            "source_packet_id",
            "prompt_scaffold_origin",
            "source_prompt_scaffold_kind",
            "source_prompt_scaffold_id",
            "source_prompt_scaffold_required_output_key",
            "source_artifact_id",
            "source_theorem_id",
            "source_block_id",
            "source_block_type",
            "source_block_conclusion",
            "block_depth",
            "dependency_scope",
            "scope_parent_id",
            "faithfulness_status",
            "faithfulness_repair_status",
            "block_verification",
            "bv_calibration",
            "pseudo_formal_method_contract_id",
            "pseudo_formal_pipeline_stage",
            "row_kind",
            "target_lane",
            "runtime_generated_queue_name",
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
            "adapter_candidate_requires_unproven_bridge_premises",
            "unavailable_import",
            "premise_derivation_kernel_verified",
            "source_to_bridge_premise_derivation_kernel_verified",
            "premise_candidate_artifact_path",
            "premise_candidate_declaration_name",
            "source_to_bridge_premise_candidate_artifact_path",
            "source_to_bridge_premise_candidate_declaration_name",
            "route_planner_contract_feedback_id",
            "route_revision_proposal_id",
            "refinement_evidence_id",
            "refinement_item_id",
            "goal_plan_id",
            "route_id",
            "route_revision_summary",
            "route_revision_overlay_dir",
            "route_revision_overlay_manifest",
            "n_route_revision_overlay_rows",
            "n_route_revision_overlay_routes_with_revision",
            "n_route_revision_overlay_orphan_rows",
            "prover_attempt_status",
            "prover_attempt_class",
            "prover_diagnostic_signature",
            "source_target_prover_family",
            "refinement_evidence_dir",
            "route_revision_proposals_path",
            "contract_counts",
            "provider_token_counts",
            "source_rows_path",
            "proof_body_signature_probe_artifact_path",
            "proof_body_signature_probe_artifact_rows",
            "proof_body_signature_artifact_count",
            "source_theorem_proof_body_signature_artifact_count",
        ):
            if key not in compact and input_summary.get(key) not in (None, "", [], {}):
                compact[key] = input_summary[key]
        for key in (
            "target_ids",
            "target_theorem_goal_ids",
            "inherited_scope",
            "candidate_materialization_statuses",
            "verifier_gate_blockers",
            "known_gaps",
            "source_anchor_context",
            "recommended_repair_tasks",
            "proof_body_recheck_blockers",
            "proof_body_signature_probe_artifact_paths",
            "source_theorem_exact_proof_body_gate_open_target_names",
            "adapter_candidate_imports",
            "kernel_verified_source_to_bridge_premise_derivation_ids",
            "unproven_bridge_premise_names",
            "verified_source_to_bridge_premise_derivation_signature_excerpts",
            "source_to_bridge_premise_derivation_signature_excerpts",
            "premise_candidate_signature_excerpts",
            "staged_followup_assembly_error_summary",
            "staged_followup_assembly_error_preview",
            "target_primitives",
            "revised_selected_primitives",
            "revised_delta_primitives",
            "route_revision_reasons",
            "route_revision_overlay_dirs",
            "route_revision_overlay_manifests",
            "source_anchors",
        ):
            value = input_summary.get(key)
            if (
                key not in compact
                and isinstance(value, list)
                and value
            ):
                compact[key] = [
                    _compact_runtime_learning_value(item)
                    for item in value[:12]
                    if str(item).strip()
                ]
        for key in (
            "source_to_bridge_premise_derivation_candidate_request",
            "source_to_bridge_grouped_premise_derivation_candidate_request",
            "source_to_bridge_premise_derivation_source_candidate_request",
            "source_to_bridge_grouped_premise_derivation_source_candidate_request",
        ):
            value = input_summary.get(key)
            if key not in compact and isinstance(value, Mapping):
                compact[key] = _compact_source_to_bridge_premise_request(value)
        value = input_summary.get("candidate_definition_request")
        if (
            "candidate_definition_request" not in compact
            and isinstance(value, Mapping)
        ):
            compact["candidate_definition_request"] = (
                _compact_candidate_definition_request(value)
            )
    return compact


def _compact_runtime_learning_sandbox_prototype(
    value: Mapping[str, object],
) -> dict[str, object]:
    keys = (
        "estimator_id",
        "simulation_id",
        "prototype_status",
        "executor",
        "smoke_passed",
        "execution_smoke_passed",
        "metric_gate_errors",
        "safety_errors",
        "script_path",
        "code_excerpt",
        "stderr_summary",
        "reason",
    )
    compact: dict[str, object] = {}
    for key in keys:
        child = value.get(key)
        if child in (None, "", [], {}):
            continue
        if isinstance(child, list):
            compact[key] = [
                _compact_runtime_learning_value(item) for item in child[:5]
            ]
        else:
            compact[key] = _compact_runtime_learning_field_value(key, child)
    return compact


def _compact_runtime_learning_input_summary(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    compact: dict[str, object] = {}
    scalar_keys = (
        "trigger",
        "question_id",
        "learning_task",
        "next_owner_subsystem",
        "owner_subsystem",
        "agenda_id",
        "source_agenda_id",
        "source_pseudo_formal_work_order_id",
        "source_formalizer_proposal_id",
        "source_formalization_manifest_id",
        "source_packet_id",
        "source_prompt_scaffold_kind",
        "source_prompt_scaffold_id",
        "source_prompt_scaffold_required_output_key",
        "source_artifact_id",
        "source_theorem_id",
        "source_block_id",
        "source_block_type",
        "source_block_conclusion",
        "source_block_proof_text",
        "structural_quality_ok",
        "pseudo_formal_method_contract_id",
        "pseudo_formal_pipeline_stage",
        "row_kind",
        "target_lane",
        "block_verification_verifier_provenance",
        "block_verification_independent",
        "independent_block_verification_required",
        "independent_block_verification_status",
        "independent_block_verification_completed",
        "formalization_gap_planner_bridge_id",
        "standalone_seed_artifact_id",
        "formalization_gap_planner_handoff_id",
        "handoff_id",
        "formalization_gap_planner_execution_contexts",
        "formalization_gap_planner_execution_plan_stage_ids",
        "standalone_seed_path",
        "target_intake_path",
        "target_intake_cli",
        "component_resource_registry_cli",
        "standalone_plan_cli",
        "llm_route_planner_prompt_cli",
        "llm_route_planner_live_cli",
        "reuse_smoke_cli",
        "recommended_llm_provider",
        "recommended_model_tier",
        "target_prover_family",
        "proof_boundary",
        "boundary",
        "priority",
        "work_order_id",
        "source_prompt_packet_id",
        "source_authoring_task_id",
        "semantic_primitive_id",
        "target_theorem_name",
        "placeholder_symbol",
        "lookup_id",
        "lookup_status",
        "runtime_queue_status",
        "runtime_generated_queue_name",
        "environment_repair_status",
        "candidate_lean_project_hint",
        "candidate_source_file",
        "unavailable_module_prefix",
        "dependency_fetch_required",
        "ready_to_rerun_lean_repair",
        "source_environment_repair_task_id",
        "verification_status",
        "execution_status",
        "source_execution_status",
        "source_execution_result_id",
        "source_lean_repair_task_id",
        "provider_name",
        "backend_provider_name",
        "n_feedback_rows",
        "attempt_status",
        "lean_lsp_mcp_live_called",
        "authoring_trigger",
        "authoring_mode",
        "failure_classification",
        "route_planner_contract_feedback_id",
        "route_revision_proposal_id",
        "refinement_evidence_id",
        "refinement_item_id",
        "goal_plan_id",
        "route_id",
        "route_revision_summary",
        "route_revision_overlay_dir",
        "route_revision_overlay_manifest",
        "n_route_revision_overlay_rows",
        "n_route_revision_overlay_routes_with_revision",
        "n_route_revision_overlay_orphan_rows",
        "prover_attempt_status",
        "prover_attempt_class",
        "prover_diagnostic_signature",
        "source_target_prover_family",
        "refinement_evidence_dir",
        "route_revision_proposals_path",
        "source_manifest_id",
        "source_manifest_path",
        "source_rows_path",
        "candidate_artifact_path",
        "source_candidate_artifact_path",
        "signature_probe_artifact_path",
        "proof_body_signature_probe_artifact_path",
        "execution_transcript_path",
        "proof_audit_manifest",
        "source_theorem_kernel_verified",
        "semantic_definition_kernel_verified",
        "artifact_kernel_verified",
        "source_theorem_proof_body_adapter_kernel_verified",
        "local_lean_checked",
        "local_lean_compiled",
        "local_definition_lean_checked",
        "local_definition_lean_compiled",
        "semantic_definition_typecheck_evidence_status",
        "proof_evidence_status",
        "proof_body_attempted",
        "proof_body_attempt_source",
        "proof_body_attempt_count",
        "proof_body_attempt_success",
        "proof_body_goal_conclusion",
        "source_to_bridge_premise_goal_conclusion",
        "adapter_candidate_requires_unproven_bridge_premises",
        "proof_body_gate_status",
        "proof_body_status",
        "proof_body_signature_probe_artifact_rows",
        "proof_body_signature_artifact_count",
        "source_theorem_proof_body_signature_artifact_count",
        "proof_body_goal_reached",
        "proof_body_semantic_review_blocked",
        "proof_body_attempt_blocked_before_goal",
        "simulation_passed",
        "algorithm_n_executed",
        "source_to_bridge_metadata_blocker_status",
        "source_to_bridge_metadata_blocker_kind",
        "source_formalizer_packet_id",
        "recommended_formalizer_target_mode",
        "candidate_request_id",
        "source_kind",
        "source_index",
        "metadata_authoring_status",
        "request_complete",
        "support_level",
        "semantic_closure_status",
        "placeholder_definition_status",
        "source_theorem_ready_for_exact_proof_body",
        "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
        "source_theorem_semantic_support_only",
        "source_semantic_alignment_review_required",
        "source_theorem_target_identity_status",
        "action_type",
        "replacement_strategy",
        "next_step_kind",
        "definition_candidate_status",
        "review_status",
        "forbidden_placeholder_detected",
        "semantic_definition_risk_detected",
        "ready_for_definition_lean_check",
        "candidate_synthesis_status",
        "definition_candidate_review_mode",
        "replacement_applied",
        "semantic_risk",
        "source_theorem_kernel_evidence_eligible",
        "adapter_candidate_artifact_path",
        "adapter_declaration_name",
        "adapter_kernel_verified",
        "adapter_candidate_evidence_eligible",
        "synthesized_candidate_artifact_path",
        "definition_only_candidate_artifact_path",
        "premise_name",
        "source_to_bridge_premise_name",
        "premise_target_type",
        "premise_target_source",
        "source_to_bridge_premise_target_type",
        "premise_derivation_kernel_verified",
        "source_to_bridge_premise_derivation_kernel_verified",
        "premise_candidate_artifact_path",
        "premise_candidate_declaration_name",
        "source_to_bridge_premise_candidate_artifact_path",
        "source_to_bridge_premise_candidate_declaration_name",
        "candidate_contract",
        "premise_derivation_gap_kind",
        "recommended_next_action",
        "source_to_bridge_premise_derivation_candidate_request_id",
        "source_to_bridge_grouped_premise_derivation_candidate_request_id",
        "source_to_bridge_premise_derivation_source_candidate_request_id",
        "source_to_bridge_grouped_premise_derivation_source_candidate_request_id",
        "adapter_instantiation_group_id",
        "shared_adapter_instantiation_contract",
        "semantic_anchor_reference_gate",
        "candidate_materialization_required",
        "candidate_materialization_contract",
        "runtime_requested_evidence_contract",
        "source_failure_id",
        "source_materialization_manifest_id",
        "formalizer_candidate_local_lean",
        "proof_state_provider",
        "n_candidate_sources",
        "n_local_lean_checked",
        "n_live_proof_state_requests",
        "n_lean_lsp_mcp_ready_requests",
        "candidate_proof_state_manifest_id",
        "n_theory_derivation_packets",
        "n_theory_derivation_packets_with_contract",
        "n_theory_derivation_packets_with_min_derivation_steps",
        "n_theory_derivation_packets_with_equation_chain",
        "n_theory_derivation_packets_with_assumption_ledger",
        "n_theory_derivation_packets_with_formalization_handoff",
        "all_required_theory_trace_consumers_observed",
        "all_required_theory_trace_alignment_consumers_observed",
        "component_eval_manifest_path",
        "component_eval",
        "model",
        "backend_provider_name",
        "live_generator",
        "static_or_fixture_only",
        "capability_evidence_ok",
        "algorithm_capability_evidence_ok",
        "simulation_capability_evidence_ok",
        "repair_sequences",
        "algorithm_repair_sequences",
        "simulation_repair_sequences",
        "algorithm_live_repair_sequences",
        "simulation_live_repair_sequences",
        "local_lean_checked",
        "local_lean_compiled",
        "proofengineer_repair_task_observed",
        "prior_feedback_proof_state_provider",
        "prior_feedback_proof_state_rows",
        "candidate_kernel_verified",
        "full_frontier_theorem_proved",
        "prior_failure_feedback_injected",
        "autonomous_live_failed_then_passed_repair_observed",
        "capability_evidence_scope",
        "target_component",
        "contract_counts",
        "provider_token_counts",
    )
    list_keys = (
        "target_ids",
        "dependency_ids",
        "dependency_statement_context",
        "inherited_scope",
        "source_block_premises",
        "structural_quality_issues",
        "target_theorem_goal_ids",
        "selected_proof_obligation_ids",
        "selected_unverified_proof_obligation_ids",
        "kernel_verified_proof_obligation_ids",
        "kernel_verified_source_theorem_semantic_primitive_ids",
        "kernel_verified_source_theorem_semantic_support_obligation_ids",
        "kernel_verified_source_theorem_semantic_definition_ids",
        "kernel_verified_source_theorem_proof_body_adapter_ids",
        "verified_source_theorem_proof_body_adapter_artifact_paths",
        "verified_source_theorem_proof_body_adapter_declarations",
        "kernel_verified_theorem_reduction_closure_work_order_ids",
        "kernel_verified_theorem_reduction_closure_target_ids",
        "kernel_verified_theorem_reduction_closure_declarations",
        "verified_theorem_reduction_closure_artifact_paths",
        "kernel_verified_theorem_reduction_closure_signature_excerpts",
        "kernel_verified_theorem_reduction_closure_goal_ids",
        "source_theorem_semantic_primitive_work_order_ids",
        "semantic_primitive_ids",
        "candidate_registered_obligation_ids",
        "search_targets",
        "source_lookup_hits",
        "semantic_alignment_constraints",
        "semantic_alignment_blockers",
        "candidate_source_declarations",
        "candidate_source_references",
        "required_next_checks",
        "forbidden_placeholder_matches",
        "semantic_definition_risks",
        "recommended_commands",
        "local_lean_diagnostics",
        "formal_gap_target_ids",
        "formal_environment_placeholder_symbols",
        "missing_formal_symbols",
        "formal_environment_typeclass_blockers",
        "typeclass_blockers",
        "recommended_proof_obligation_ids",
        "proof_body_attempt_summaries",
        "proof_body_goal_excerpt",
        "proof_body_goal_binder_names",
        "source_to_bridge_premise_goal_binder_names",
        "proof_body_signature_probe_artifact_paths",
        "source_theorem_exact_proof_body_gate_open_target_names",
        "exact_goal_shape_obligation_ids",
        "exact_goal_shape_obligations",
        "diagnostics",
        "residual_goals",
        "requested_tools",
        "executed_tools",
        "tool_call_trace",
        "premise_names",
        "unproven_bridge_premise_names",
        "source_to_bridge_premise_names",
        "premise_semantic_anchor_binder_names",
        "premise_semantic_anchor_binders",
        "exact_source_theorem_binders",
        "required_semantic_anchor_reference_names",
        "required_bridge_premise_names_for_shared_instantiation",
        "adapter_object_names_requiring_source_instantiation",
        "source_to_bridge_adapter_object_names_requiring_source_instantiation",
        "diagnostic_helper_candidate_ids",
        "source_to_bridge_metadata_blocker_target_ids",
        "source_to_bridge_metadata_blocker_helper_candidate_ids",
        "supporting_formalization_gap_planner_bridge_ids",
        "supporting_standalone_seed_artifact_ids",
        "supporting_formalization_gap_planner_handoff_ids",
        "missing_required_metadata_fields",
        "required_candidate_fields",
        "candidate_materialization_statuses",
        "kernel_verified_source_to_bridge_premise_derivation_ids",
        "verified_source_to_bridge_premise_derivation_signature_excerpts",
        "source_to_bridge_premise_derivation_signature_excerpts",
        "premise_candidate_signature_excerpts",
        "failure_classifications",
        "staged_followup_assembly_error_summary",
        "staged_followup_assembly_error_preview",
        "target_primitives",
        "revised_selected_primitives",
        "revised_delta_primitives",
        "route_revision_reasons",
        "route_revision_overlay_dirs",
        "route_revision_overlay_manifests",
        "source_anchors",
        "required_theory_trace_consumers",
        "theory_trace_consuming_subsystems",
        "structured_theory_trace_aligned_subsystems",
        "component_backend_provider_names",
        "missing_contracts",
        "required_runtime_configuration",
        "required_formalizer_behavior",
    )
    mapping_keys = (
        "block_verification",
        "structural_quality",
        "prompt_scaffold_origin",
        "pseudo_formal_block_verifier_worker",
        "formalization_counts",
        "retrieval_counts",
        "runtime_requested_evidence_contract",
        "source_theorem_target_provenance",
        "definition_contract",
        "candidate_definition_request",
        "source_to_bridge_premise_derivation_candidate_request",
        "source_to_bridge_grouped_premise_derivation_candidate_request",
        "source_to_bridge_premise_derivation_source_candidate_request",
        "source_to_bridge_grouped_premise_derivation_source_candidate_request",
        "proof_body_goal_context",
        "source_to_bridge_premise_goal_context",
        "source_theorem_exact_semantic_definition_typechecked_candidate",
        "contract_counts",
        "provider_token_counts",
    )
    for key in scalar_keys:
        if key in value and value[key] not in (None, "", [], {}):
            compact[key] = _compact_runtime_learning_field_value(key, value[key])
    for key in list_keys:
        items = value.get(key)
        if isinstance(items, list):
            limit = 4 if key in {"diagnostics", "proof_body_goal_excerpt", "proof_body_attempt_summaries"} else 12
            compact[key] = [
                _compact_runtime_learning_value(item)
                for item in items[:limit]
                if str(item).strip()
            ]
    for key in mapping_keys:
        child = value.get(key)
        if isinstance(child, Mapping):
            if key in {
                "source_to_bridge_premise_derivation_candidate_request",
                "source_to_bridge_grouped_premise_derivation_candidate_request",
            }:
                compact[key] = _compact_source_to_bridge_premise_request(child)
            elif key == "candidate_definition_request":
                compact[key] = _compact_candidate_definition_request(child)
            else:
                compact[key] = {
                    str(child_key): _compact_runtime_learning_value(child_value)
                    for child_key, child_value in list(child.items())[:12]
                    if child_value not in (None, "", [], {})
                }
    if "scope_parent_id" in value and "scope_parent_id" not in compact:
        compact["scope_parent_id"] = str(value.get("scope_parent_id", "") or "")
    live_request = value.get("candidate_live_proof_state_request")
    if isinstance(live_request, Mapping):
        goal_excerpt = live_request.get("proof_body_goal_excerpt", [])
        if isinstance(goal_excerpt, list) and goal_excerpt and "proof_body_goal_excerpt" not in compact:
            compact["proof_body_goal_excerpt"] = [
                _compact_runtime_learning_value(item)
                for item in goal_excerpt[:8]
                if str(item).strip()
            ]
        if (
            isinstance(goal_excerpt, list)
            and any(str(item).strip() for item in goal_excerpt)
            and "proof_body_signature_probe_artifact_rows" not in compact
            and "n_proof_body_signature_probe_artifact_rows" not in compact
            and "proof_body_signature_artifact_count" not in compact
            and "source_theorem_proof_body_signature_artifact_count" not in compact
            and "proof_body_signature_probe_artifact_path" not in compact
            and "source_theorem_signature_probe_artifact_path" not in compact
            and "signature_probe_artifact_path" not in compact
        ):
            compact["proof_body_signature_probe_artifact_rows"] = 1
        lean_multi_attempt = live_request.get("lean_multi_attempt", {})
        if (
            isinstance(lean_multi_attempt, Mapping)
            and isinstance(lean_multi_attempt.get("attempts"), list)
            and "proof_body_attempt_summaries" not in compact
        ):
            summaries: list[object] = []
            for attempt in lean_multi_attempt.get("attempts", [])[:4]:
                if not isinstance(attempt, Mapping):
                    continue
                status = str(attempt.get("status", "") or "").strip()
                proof_body = str(attempt.get("proof_body", "") or "").strip()
                if status or proof_body:
                    summaries.append(
                        {
                            "status": status,
                            "proof_body": proof_body[:240],
                        }
                    )
            if summaries:
                compact["proof_body_attempt_summaries"] = summaries
    checks = value.get("semantic_primitive_checks")
    if isinstance(checks, list):
        compact["semantic_primitive_checks"] = [
            {
                sub_key: _compact_runtime_learning_value(check.get(sub_key))
                for sub_key in (
                    "placeholder_symbol",
                    "semantic_primitive_id",
                    "target_theorem_name",
                    "work_order_id",
                    "kernel_verified_registered_obligation_ids",
                    "target_theorem_goal_ids",
                )
                if isinstance(check, Mapping)
                and check.get(sub_key) not in (None, "", [], {})
            }
            for check in checks[:4]
            if isinstance(check, Mapping)
        ]
    return compact


def _compact_source_to_bridge_premise_request(value: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "candidate_request_id",
        "grouped_candidate_request_id",
        "target_theorem_name",
        "target_lean_declaration",
        "premise_name",
        "premise_names",
        "premise_target_type",
        "premise_target_source",
        "source_to_bridge_premise_target_type",
        "premise_candidate_declaration_name",
        "premise_candidate_declaration_names",
        "adapter_instantiation_group_id",
        "required_bridge_premise_names_for_shared_instantiation",
        "adapter_object_names_requiring_source_instantiation",
        "bridge_object_instantiation_policy",
        "shared_adapter_instantiation_contract",
        "exact_source_theorem_binders",
        "premise_semantic_anchor_binders",
        "premise_semantic_anchor_binder_names",
        "required_semantic_anchor_reference_names",
        "semantic_anchor_reference_gate",
        "candidate_contract",
        "proof_body_goal_context",
        "proof_body_goal_binder_names",
        "proof_body_goal_conclusion",
        "source_to_bridge_premise_goal_context",
        "source_to_bridge_premise_goal_binder_names",
        "source_to_bridge_premise_goal_conclusion",
        "forbidden_actions",
        "proof_evidence_status",
    )
    compact: dict[str, object] = {}
    for key in keys:
        child = value.get(key)
        if child not in (None, "", [], {}):
            compact[key] = _compact_runtime_learning_value(child)
    return compact


def _compact_candidate_definition_request(value: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "request_kind",
        "target_theorem_name",
        "placeholder_symbol",
        "semantic_goal",
        "required_anchor_names",
        "available_anchor_names",
        "missing_required_anchor_names",
        "required_binders",
        "required_adapter_object_names",
        "available_adapter_object_names",
        "missing_required_adapter_object_names",
        "source_to_bridge_adapter_instantiation_group_id",
        "required_bridge_premise_names_for_shared_instantiation",
        "forbidden_shortcuts",
        "local_lean_gate",
        "proof_evidence_status",
    )
    keep_empty_list_keys = {
        "missing_required_anchor_names",
        "missing_required_adapter_object_names",
    }
    compact: dict[str, object] = {}
    for key in keys:
        child = value.get(key)
        if key in keep_empty_list_keys and isinstance(child, list):
            compact[key] = _compact_candidate_definition_request_value(key, child)
            continue
        if child not in (None, "", [], {}):
            compact[key] = _compact_candidate_definition_request_value(key, child)
    return compact


def _compact_candidate_definition_request_value(key: str, value: object) -> object:
    """Compact semantic-definition request fields without dropping source anchors."""

    if isinstance(value, list):
        limit = 16 if key.endswith("_names") else 12
        return [_compact_runtime_learning_value(item) for item in value[:limit]]
    return _compact_runtime_learning_value(value)


def _compact_runtime_learning_value(value: object) -> object:
    if isinstance(value, str):
        return value if len(value) <= 320 else value[:317] + "..."
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    if isinstance(value, list):
        return [_compact_runtime_learning_value(item) for item in value[:8]]
    if isinstance(value, Mapping):
        return {
            str(key): _compact_runtime_learning_value(child)
            for key, child in list(value.items())[:8]
            if child not in (None, "", [], {})
        }
    return str(value)[:320]


def _compact_formalization_gap_planner_execution_context(value: object) -> object:
    context_keys = (
        "bridge_id",
        "formalization_gap_planner_bridge_id",
        "handoff_id",
        "formalization_gap_planner_handoff_id",
        "standalone_seed_artifact_id",
        "standalone_seed_path",
        "target_intake_path",
        "target_intake_dir",
        "target_intake_cli",
        "component_resource_registry_dir",
        "component_resource_registry_cli",
        "standalone_plan_dir",
        "standalone_plan_cli",
        "llm_route_planner_prompt_cli",
        "llm_route_planner_live_cli",
        "reuse_smoke_cli",
        "execution_plan_stage_ids",
        "formalization_gap_planner_execution_plan_stage_ids",
        "recommended_llm_provider",
        "recommended_model_tier",
        "target_prover_family",
        "proof_evidence_status",
        "proof_evidence_boundary",
    )
    if isinstance(value, list):
        return [
            _compact_formalization_gap_planner_execution_context(item)
            for item in value[:4]
        ]
    if not isinstance(value, Mapping):
        return _compact_runtime_learning_value(value)
    compact: dict[str, object] = {}
    for key in context_keys:
        child = value.get(key)
        if child in (None, "", [], {}):
            continue
        if isinstance(child, str) and (
            _runtime_learning_key_is_path_like(key) or key.endswith("_cli")
        ):
            compact[key] = child
        elif isinstance(child, list):
            compact[key] = [_compact_runtime_learning_value(item) for item in child[:8]]
        else:
            compact[key] = _compact_runtime_learning_value(child)
    return compact


def _compact_runtime_learning_field_value(key: str, value: object) -> object:
    if key == "formalization_gap_planner_execution_contexts":
        return _compact_formalization_gap_planner_execution_context(value)
    if isinstance(value, str) and _runtime_learning_key_is_path_like(key):
        return value
    return _compact_runtime_learning_value(value)


def _runtime_learning_key_is_path_like(key: str) -> bool:
    normalized = key.lower()
    return normalized.endswith(
        (
            "_path",
            "_paths",
            "_jsonl",
            "_manifest",
            "_dir",
            "_file",
            "_root",
            "_cli",
        )
    )


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
GENERATOR_PROVIDER_CHOICES = SUPPORTED_GENERATOR_PROVIDERS
SUBSYSTEM_GENERATOR_PROVIDER_CHOICES = (
    "same",
    *GENERATOR_PROVIDER_CHOICES,
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
        return OpenAIResponsesGeneratorBackend(timeout_s=llm_timeout_seconds), "openai"
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
    local_lean_enabled = bool(getattr(args, "local_lean", False))
    formalizer_candidate_local_lean_enabled = bool(
        getattr(args, "formalizer_candidate_local_lean", False)
    )
    formalizer_candidate_lean_lsp_mcp_enabled = bool(
        getattr(args, "formalizer_candidate_lean_lsp_mcp", False)
    )
    formalizer_candidate_local_lean_enabled = (
        formalizer_candidate_local_lean_enabled
        or formalizer_candidate_lean_lsp_mcp_enabled
    )
    if not local_lean_enabled and not formalizer_candidate_local_lean_enabled:
        return None
    lean_project = (
        (
            getattr(args, "formalizer_candidate_lean_project", None)
            if formalizer_candidate_local_lean_enabled
            else None
        )
        or getattr(args, "lean_project", None)
        or getattr(args, "local_lean_project", None)
    )
    lean_timeout = (
        (
            getattr(args, "formalizer_candidate_lean_timeout", None)
            if formalizer_candidate_local_lean_enabled
            else None
        )
        or getattr(
            args,
            "lean_timeout",
            getattr(args, "local_lean_timeout", 90),
        )
        or getattr(args, "local_lean_timeout", 90)
    )
    provider_cls = (
        LeanLspMcpProofStateFeedbackProvider
        if formalizer_candidate_lean_lsp_mcp_enabled
        else LocalLeanProofStateFeedbackProvider
    )
    return provider_cls(
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


def _source_theorem_semantic_primitive_proofengineer_bridge(
    args: argparse.Namespace,
) -> int:
    out_dir = Path(args.out)
    bridge_manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=out_dir,
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        queue_jsonl=Path(args.queue_jsonl) if args.queue_jsonl else None,
        proof_body_executor_dir=(
            Path(args.proof_body_executor_dir)
            if args.proof_body_executor_dir
            else None
        ),
        question_id=str(args.question_id or ""),
        local_lean=bool(args.local_lean),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
        proof_audit_manifest=(
            Path(args.proof_audit_manifest) if args.proof_audit_manifest else None
        ),
    )
    bridge_manifest_path = (
        out_dir / "source_theorem_semantic_primitive_proofengineer_bridge_manifest.json"
    )
    print("\nAI Statistician Source-Theorem Semantic-Primitive ProofEngineer Bridge")
    print("=" * 72)
    print(
        f"work_orders={bridge_manifest['n_work_orders']} "
        f"registered_candidates={bridge_manifest['n_registered_candidate_obligations']} "
        f"kernel_verified_candidates="
        f"{bridge_manifest['n_kernel_verified_registered_candidate_obligations']} "
        f"runtime_learning_ready={bridge_manifest['runtime_learning_ready']}"
    )
    if bridge_manifest.get("source_proof_audit_manifest"):
        print(
            "proof audit manifest used: "
            f"{Path(str(bridge_manifest['source_proof_audit_manifest'])).resolve()}"
        )
    print(
        "runtime learning rows written to "
        f"{Path(str(bridge_manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"bridge manifest written to {bridge_manifest_path.resolve()}")
    return 0


def _source_theorem_proof_body_adapter_proofengineer_bridge(
    args: argparse.Namespace,
) -> int:
    out_dir = Path(args.out)
    bridge_manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=out_dir,
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        queue_jsonl=Path(args.queue_jsonl) if args.queue_jsonl else None,
        question_id=str(args.question_id or ""),
        local_lean=bool(args.local_lean),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
    )
    bridge_manifest_path = (
        out_dir / "source_theorem_proof_body_adapter_proofengineer_bridge_manifest.json"
    )
    print("\nAI Statistician Source-Theorem Proof-Body Adapter ProofEngineer Bridge")
    print("=" * 72)
    print(
        f"work_orders={bridge_manifest['n_work_orders']} "
        f"adapter_rows={bridge_manifest['n_adapter_check_rows']} "
        f"adapter_kernel_verified={bridge_manifest['n_adapter_kernel_verified']} "
        f"runtime_learning_ready={bridge_manifest['runtime_learning_ready']}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(bridge_manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"bridge manifest written to {bridge_manifest_path.resolve()}")
    print(f"proof_evidence_status={bridge_manifest['proof_evidence_status']}")
    return 0


def _source_to_bridge_premise_derivation_proofengineer_bridge(
    args: argparse.Namespace,
) -> int:
    out_dir = Path(args.out)
    bridge_manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=out_dir,
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        queue_jsonl=Path(args.queue_jsonl) if args.queue_jsonl else None,
        adapter_bridge_dir=(
            Path(args.adapter_bridge_dir) if args.adapter_bridge_dir else None
        ),
        question_id=str(args.question_id or ""),
        local_lean=bool(args.local_lean),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
    )
    bridge_manifest_path = (
        out_dir / "source_to_bridge_premise_derivation_proofengineer_bridge_manifest.json"
    )
    print("\nAI Statistician Source-to-Bridge Premise Derivation ProofEngineer Bridge")
    print("=" * 72)
    print(
        f"work_orders={bridge_manifest['n_work_orders']} "
        f"premise_rows={bridge_manifest['n_premise_derivation_check_rows']} "
        "premise_kernel_verified="
        f"{bridge_manifest['n_premise_derivation_kernel_verified']} "
        f"runtime_learning_ready={bridge_manifest['runtime_learning_ready']}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(bridge_manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"bridge manifest written to {bridge_manifest_path.resolve()}")
    print(f"proof_evidence_status={bridge_manifest['proof_evidence_status']}")
    return 0


def _source_theorem_formal_environment_proofengineer_bridge(
    args: argparse.Namespace,
) -> int:
    out_dir = Path(args.out)
    bridge_manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=out_dir,
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        queue_jsonl=Path(args.queue_jsonl) if args.queue_jsonl else None,
        question_id=str(args.question_id or ""),
        run_signature_probes=bool(getattr(args, "run_signature_probes", False)),
        lean_project=Path(args.lean_project) if getattr(args, "lean_project", "") else None,
        lean_timeout=int(getattr(args, "lean_timeout", 90)),
    )
    bridge_manifest_path = (
        out_dir / "source_theorem_formal_environment_proofengineer_bridge_manifest.json"
    )
    print("\nAI Statistician Source-Theorem Formal-Environment ProofEngineer Bridge")
    print("=" * 72)
    print(
        f"work_orders={bridge_manifest['n_work_orders']} "
        f"repair_packets={bridge_manifest['n_repair_packets']} "
        f"missing_symbols={bridge_manifest['n_missing_formal_symbols']} "
        f"typeclass_blockers={bridge_manifest['n_typeclass_blockers']}"
    )
    print(f"repair packets written to {Path(str(bridge_manifest['repair_packets_jsonl'])).resolve()}")
    print(
        "runtime learning rows written to "
        f"{Path(str(bridge_manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"bridge manifest written to {bridge_manifest_path.resolve()}")
    if bridge_manifest.get("signature_probe_manifest"):
        print(
            "signature probe manifest written to "
            f"{Path(str(bridge_manifest['signature_probe_manifest'])).resolve()}"
        )
    if bridge_manifest.get("proof_body_work_orders_jsonl"):
        print(
            "proof-body work orders written to "
            f"{Path(str(bridge_manifest['proof_body_work_orders_jsonl'])).resolve()}"
        )
    if bridge_manifest.get("proof_body_execution_queue_jsonl"):
        print(
            "proof-body execution queue written to "
            f"{Path(str(bridge_manifest['proof_body_execution_queue_jsonl'])).resolve()}"
        )
    print(f"proof_evidence_status={bridge_manifest['proof_evidence_status']}")
    return 0


def _source_theorem_exact_semantic_definition_source_lookup(
    args: argparse.Namespace,
) -> int:
    source_roots = [Path(value) for value in args.source_root or []]
    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=Path(args.out),
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        queue_jsonl=Path(args.queue_jsonl) if args.queue_jsonl else None,
        source_roots=source_roots,
        max_hits_per_work_order=int(args.max_hits_per_work_order),
    )
    print("\nAI Statistician Exact Semantic-Definition Source Lookup")
    print("=" * 72)
    print(
        f"work_orders={manifest['n_work_orders']} "
        f"rows_with_hits={manifest['n_rows_with_source_hits']} "
        f"source_hits={manifest['n_source_lookup_hits']} "
        f"learning={manifest['n_runtime_learning_rows']}"
    )
    print(
        "lookup rows written to "
        f"{Path(str(manifest['lookup_rows_jsonl'])).resolve()}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"manifest written to {Path(str(manifest['manifest_path'])).resolve()}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    return 0


def _source_theorem_exact_semantic_definition_closure_review(
    args: argparse.Namespace,
) -> int:
    manifest = run_source_theorem_exact_semantic_definition_closure_review(
        out_dir=Path(args.out),
        review_packets_jsonl=(
            Path(args.review_packets_jsonl)
            if args.review_packets_jsonl
            else None
        ),
        lookup_manifest=Path(args.lookup_manifest) if args.lookup_manifest else None,
        candidate_artifact_path=(
            Path(args.candidate_artifact) if args.candidate_artifact else None
        ),
    )
    print("\nAI Statistician Exact Semantic-Definition Closure Review")
    print("=" * 72)
    print(
        f"review_packets={manifest['n_review_packets']} "
        f"review_results={manifest['n_review_results']} "
        f"forbidden_placeholders={manifest['n_forbidden_placeholder_definitions']} "
        f"ready_for_lean={manifest['n_ready_for_definition_lean_check']}"
    )
    print(
        "review results written to "
        f"{Path(str(manifest['review_results_jsonl'])).resolve()}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"manifest written to {Path(str(manifest['manifest_path'])).resolve()}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    return 0


def _source_theorem_exact_semantic_definition_proofengineer_bridge(
    args: argparse.Namespace,
) -> int:
    manifest = run_source_theorem_exact_semantic_definition_proofengineer_bridge(
        out_dir=Path(args.out),
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        lookup_manifest=Path(args.lookup_manifest) if args.lookup_manifest else None,
        review_packets_jsonl=(
            Path(args.review_packets_jsonl)
            if args.review_packets_jsonl
            else None
        ),
        question_id=str(args.question_id or ""),
    )
    print("\nAI Statistician Exact Semantic-Definition ProofEngineer Bridge")
    print("=" * 72)
    print(
        f"review_packets={manifest['n_review_packets']} "
        f"repair_packets={manifest['n_repair_packets']} "
        f"lean_repair_tasks={manifest['n_lean_repair_tasks']} "
        f"import_candidates={manifest['n_import_candidate_declaration_packets']} "
        f"synthesize_from_refs={manifest['n_synthesize_from_references_packets']}"
    )
    print(
        "repair packets written to "
        f"{Path(str(manifest['repair_packets_jsonl'])).resolve()}"
    )
    print(
        "Lean repair tasks written to "
        f"{Path(str(manifest['lean_repair_tasks_jsonl'])).resolve()}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"manifest written to {Path(str(manifest['manifest_path'])).resolve()}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    return 0


def _source_theorem_exact_semantic_definition_lean_repair_executor(
    args: argparse.Namespace,
) -> int:
    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=Path(args.out),
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        bridge_manifest=Path(args.bridge_manifest) if args.bridge_manifest else None,
        materializer_manifest=(
            Path(args.materializer_manifest) if args.materializer_manifest else None
        ),
        tasks_jsonl=Path(args.tasks_jsonl) if args.tasks_jsonl else None,
        source_roots=tuple(Path(value) for value in (args.source_root or [])),
        local_lean=bool(args.local_lean),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
    )
    print("\nAI Statistician Exact Semantic-Definition Lean Repair Executor")
    print("=" * 72)
    print(
        f"tasks={manifest['n_tasks']} "
        f"results={manifest['n_results']} "
        f"source_files_resolved={manifest['n_candidate_source_files_resolved']} "
        f"local_lean_checked={manifest['n_local_lean_checked']} "
        f"local_lean_compiled={manifest['n_local_lean_compiled']} "
        f"authoring_tasks={manifest.get('n_exact_semantic_definition_authoring_tasks', 0)}"
    )
    print(
        "execution results written to "
        f"{Path(str(manifest['execution_results_jsonl'])).resolve()}"
    )
    if manifest.get("exact_semantic_definition_authoring_tasks_jsonl"):
        print(
            "definition authoring tasks written to "
            f"{Path(str(manifest['exact_semantic_definition_authoring_tasks_jsonl'])).resolve()}"
        )
    print(
        "runtime learning rows written to "
        f"{Path(str(manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"manifest written to {Path(str(manifest['manifest_path'])).resolve()}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    return 0


def _source_theorem_exact_semantic_definition_authoring_worker(
    args: argparse.Namespace,
) -> int:
    _load_dotenv(Path(args.env_file))
    provider_name = str(args.provider or "none")
    provider = None
    if provider_name != "none" and not bool(args.dry_run):
        provider, provider_name = _build_theory_generator_backend(
            provider_name=provider_name,
            static_response_file=str(args.static_response_file or ""),
            llm_timeout_seconds=float(args.llm_timeout_seconds),
        )
    manifest = run_source_theorem_exact_semantic_definition_authoring_worker(
        out_dir=Path(args.out),
        runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
        repair_executor_manifest=(
            Path(args.repair_executor_manifest)
            if args.repair_executor_manifest
            else None
        ),
        authoring_tasks_jsonl=(
            Path(args.authoring_tasks_jsonl)
            if args.authoring_tasks_jsonl
            else None
        ),
        provider=provider,
        config=AuthoringWorkerConfig(
            provider_name=provider_name,
            model=str(args.llm_model or ""),
            model_tier=str(args.model_tier or "sonnet"),
            max_tokens=int(args.max_tokens),
            temperature=float(args.temperature),
            max_repair_attempts=int(args.max_repair_attempts),
            dry_run=bool(args.dry_run or provider is None),
            max_tasks=int(args.max_tasks),
            placeholder_symbols=tuple(args.placeholder_symbol or ()),
            allow_external_export=bool(args.allow_external_export),
            external_export_mode=str(args.external_export_mode or "full"),
            external_export_approval_manifest=str(
                args.external_export_approval_manifest or ""
            ),
        ),
    )
    print("\nAI Statistician Exact Semantic-Definition Authoring Worker")
    print("=" * 72)
    print(
        f"tasks={manifest['n_authoring_tasks']} "
        f"prompt_packets={manifest['n_prompt_packets']} "
        f"provider={manifest.get('provider_name', '')} "
        f"backend_provider={manifest.get('backend_provider_name', '')} "
        f"llm_attempted={manifest['n_llm_attempted']} "
        f"live_llm_attempted={manifest.get('n_live_llm_attempted', 0)} "
        f"static_or_fixture_llm_attempted={manifest.get('n_static_or_fixture_llm_attempted', 0)} "
        f"candidate_packets={manifest['n_candidate_packets']} "
        f"candidate_ok={manifest['n_candidate_packets_ok']}"
    )
    print(
        "prompt packets written to "
        f"{Path(str(manifest['authoring_prompt_packets_jsonl'])).resolve()}"
    )
    print(
        "candidate packets written to "
        f"{Path(str(manifest['authoring_candidate_packets_jsonl'])).resolve()}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"manifest written to {Path(str(manifest['manifest_path'])).resolve()}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    return 0


def _source_theorem_exact_semantic_definition_authoring_candidate_materialize(
    args: argparse.Namespace,
) -> int:
    manifest = (
        run_source_theorem_exact_semantic_definition_authoring_candidate_materializer(
            out_dir=Path(args.out),
            authoring_worker_manifest=(
                Path(args.authoring_worker_manifest)
                if args.authoring_worker_manifest
                else None
            ),
            candidate_packets_jsonl=(
                Path(args.candidate_packets_jsonl)
                if args.candidate_packets_jsonl
                else None
            ),
            config=AuthoringCandidateMaterializerConfig(
                max_candidates=int(args.max_candidates),
                include_source_comments=not bool(args.no_source_comments),
            ),
        )
    )
    print("\nAI Statistician Exact Semantic-Definition Candidate Materializer")
    print("=" * 72)
    print(
        f"candidate_packets={manifest['n_candidate_packets']} "
        f"materialized={manifest['n_materialized_definition_only_candidates']} "
        f"lean_repair_tasks={manifest['n_materialized_lean_repair_tasks']} "
        f"blocked={manifest['n_blocked_candidates']}"
    )
    print(
        "materialization rows written to "
        f"{Path(str(manifest['materialization_rows_jsonl'])).resolve()}"
    )
    print(
        "materialized Lean repair tasks written to "
        f"{Path(str(manifest['materialized_lean_repair_tasks_jsonl'])).resolve()}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"manifest written to {Path(str(manifest['manifest_path'])).resolve()}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    return 0


def _source_theorem_exact_semantic_definition_lean_environment_repair_executor(
    args: argparse.Namespace,
) -> int:
    manifest = (
        run_source_theorem_exact_semantic_definition_lean_environment_repair_executor(
            out_dir=Path(args.out),
            runtime_dir=Path(args.runtime_dir) if args.runtime_dir else None,
            repair_executor_manifest=(
                Path(args.repair_executor_manifest)
                if args.repair_executor_manifest
                else None
            ),
            environment_tasks_jsonl=(
                Path(args.environment_tasks_jsonl)
                if args.environment_tasks_jsonl
                else None
            ),
        )
    )
    print("\nAI Statistician Exact Semantic-Definition Lean Environment Repair")
    print("=" * 72)
    print(
        f"tasks={manifest['n_tasks']} "
        f"results={manifest['n_results']} "
        f"dependency_fetch_required={manifest['n_dependency_fetch_required']} "
        f"ready_to_rerun={manifest['n_ready_to_rerun_lean_repair']}"
    )
    print(
        "environment results written to "
        f"{Path(str(manifest['environment_repair_results_jsonl'])).resolve()}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"manifest written to {Path(str(manifest['manifest_path'])).resolve()}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    return 0


def _source_theorem_exact_semantic_definition_verifier_gate_executor(
    args: argparse.Namespace,
) -> int:
    manifest = run_source_theorem_exact_semantic_definition_verifier_gate_executor(
        out_dir=Path(args.out),
        recheck_manifest=Path(args.recheck_manifest)
        if args.recheck_manifest
        else None,
        work_orders_jsonl=Path(args.work_orders_jsonl)
        if args.work_orders_jsonl
        else None,
        local_lean=bool(args.local_lean),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
    )
    print("\nAI Statistician Exact Semantic-Definition Verifier Gate")
    print("=" * 72)
    print(
        f"work_orders={manifest['n_work_orders']} "
        f"results={manifest['n_results']} "
        f"local_lean_checked={manifest['n_local_lean_checked']} "
        f"local_lean_compiled={manifest['n_local_lean_compiled']} "
        f"approved={manifest['n_verifier_approved']} "
        f"blocked={manifest['n_verifier_blocked']}"
    )
    print(
        "verifier results written to "
        f"{Path(str(manifest['verifier_gate_results_jsonl'])).resolve()}"
    )
    print(
        "approved review packets written to "
        f"{Path(str(manifest['verifier_approved_review_packets_jsonl'])).resolve()}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    print(f"manifest written to {Path(str(manifest['manifest_path'])).resolve()}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    return 0


def _source_theorem_exact_semantic_definition_candidate_synthesis(
    args: argparse.Namespace,
) -> int:
    manifest = run_source_theorem_exact_semantic_definition_candidate_synthesis(
        out_dir=Path(args.out),
        review_manifest=Path(args.review_manifest) if args.review_manifest else None,
        review_results_jsonl=(
            Path(args.review_results_jsonl)
            if args.review_results_jsonl
            else None
        ),
        candidate_artifact_path=Path(args.candidate_artifact),
        proof_body_queue_manifest=(
            Path(args.proof_body_queue_manifest)
            if getattr(args, "proof_body_queue_manifest", "")
            else None
        ),
        proof_body_queue_jsonl=(
            Path(args.proof_body_queue_jsonl)
            if getattr(args, "proof_body_queue_jsonl", "")
            else None
        ),
        allow_draft_semantic_repair=bool(args.allow_draft_semantic_repair),
        local_lean=bool(args.local_lean),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
    )
    print("\nAI Statistician Exact Semantic-Definition Candidate Synthesis")
    print("=" * 72)
    print(
        f"review_results={manifest['n_review_results']} "
        f"replacements={manifest['n_replacements_applied']} "
        f"forbidden_after={manifest['n_forbidden_placeholder_definitions_after']} "
        f"local_lean_compiled={manifest['local_lean_compiled']}"
    )
    print(
        "synthesized artifact written to "
        f"{Path(str(manifest['synthesized_candidate_artifact_path'])).resolve()}"
    )
    print(
        "synthesis rows written to "
        f"{Path(str(manifest['candidate_synthesis_results_jsonl'])).resolve()}"
    )
    print(
        "runtime learning rows written to "
        f"{Path(str(manifest['runtime_learning_rows_jsonl'])).resolve()}"
    )
    if manifest.get("proof_body_recheck_queue_manifest"):
        print(
            "proof-body recheck queue written to "
            f"{Path(str(manifest['proof_body_recheck_queue_manifest'])).resolve()}"
        )
    print(f"manifest written to {Path(str(manifest['manifest_path'])).resolve()}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
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
        f"local_execution={payload.get('ready_for_local_execution')} "
        f"availability={profile.get('availability_status', '')} "
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
        max_estimated_prompt_input_tokens=args.max_estimated_prompt_input_tokens,
        max_route_requests=args.max_route_requests,
        max_repair_attempts=args.max_repair_attempts,
        max_staged_followup_stage_calls=(
            args.max_staged_followup_stage_calls
        ),
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
        source_theorem_semantic_primitive_bridge_dir=(
            Path(args.source_theorem_semantic_primitive_bridge_dir)
            if args.source_theorem_semantic_primitive_bridge_dir
            else None
        ),
        source_theorem_semantic_primitive_from_proof_body_executor_work_orders_dir=(
            Path(
                args.source_theorem_semantic_primitive_from_proof_body_executor_work_orders_dir
            )
            if args.source_theorem_semantic_primitive_from_proof_body_executor_work_orders_dir
            else None
        ),
        source_theorem_formal_environment_bridge_dir=(
            Path(args.source_theorem_formal_environment_bridge_dir)
            if args.source_theorem_formal_environment_bridge_dir
            else None
        ),
        exact_source_theorem_proof_body_executor_dir=(
            Path(args.exact_source_theorem_proof_body_executor_dir)
            if args.exact_source_theorem_proof_body_executor_dir
            else None
        ),
        formalization_gap_planner_refinement_evidence_dir=(
            Path(args.formalization_gap_planner_refinement_evidence_dir)
            if args.formalization_gap_planner_refinement_evidence_dir
            else None
        ),
        formalization_gap_planner_route_contract_feedback_jsonl=(
            Path(args.formalization_gap_planner_route_contract_feedback_jsonl)
            if args.formalization_gap_planner_route_contract_feedback_jsonl
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
        f"prompt_budget_blocks={payload['n_prompt_token_budget_preflight_blocked']} "
        f"staged_followup_stage_attempts={payload['n_staged_followup_stage_attempt_rows']} "
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
        formalization_gap_planner_resource_request_queue_dir=Path(
            args.formalization_gap_planner_resource_request_queue_dir
        )
        if args.formalization_gap_planner_resource_request_queue_dir
        else None,
    )
    print("\nAI Statistical Theory Lab Formalization Gap Planner Interactive Session")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_session_rows']} "
        f"literature={payload['n_run_literature_search']} "
        f"lean={payload['n_run_lean_grounding']} "
        f"proof_state={payload['n_run_proof_state_feedback']} "
        f"resource_requests={payload['n_resource_requests_linked']} "
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
        llm_route_planner_max_estimated_prompt_input_tokens=(
            args.llm_route_planner_max_estimated_prompt_input_tokens
        ),
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
        feedback_llm_route_planner_max_estimated_prompt_input_tokens=(
            args.feedback_llm_route_planner_max_estimated_prompt_input_tokens
        ),
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
        f"llm_prompt_budget_blocks={payload['n_llm_route_planner_prompt_token_budget_preflight_blocked']} "
        f"feedback_llm_accepted={payload['n_feedback_llm_route_planner_accepted_route_plans']} "
        f"feedback_llm_awaiting={payload['n_feedback_llm_route_planner_awaiting']} "
        f"feedback_prompt_budget_blocks={payload['n_feedback_llm_route_planner_prompt_token_budget_preflight_blocked']} "
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


def _pseudo_formal_block_verifier_prompt_packets(args: argparse.Namespace) -> int:
    payload = export_pseudo_formal_block_verifier_prompt_packets(
        [Path(path) for path in args.runtime_learning_jsonl],
        Path(args.out),
        max_packets=args.max_packets,
    )
    print("\nAI Statistical Theory Lab Pseudo-Formal BlockVerifier Prompt Packets")
    print("=" * 72)
    print(
        f"requests={payload['n_request_rows']} "
        f"packets={payload['n_ok_prompt_packets']}/{payload['n_prompt_packets']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nprompt manifest written to "
        f"{(Path(args.out) / 'pseudo_formal_block_verifier_prompt_packets_manifest.json').resolve()}"
    )
    print(
        f"prompt packet jsonl written to "
        f"{(Path(args.out) / 'pseudo_formal_block_verifier_prompt_packets.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _pseudo_formal_block_verifier_llm_responses(args: argparse.Namespace) -> int:
    provider_name = str(args.provider or "anthropic").strip().lower()
    provider = _pseudo_formal_block_verifier_provider(
        provider_name=provider_name,
        static_response_file=(
            Path(args.static_response_file)
            if str(args.static_response_file or "").strip()
            else None
        ),
        llm_timeout_seconds=args.llm_timeout_seconds,
    )
    payload = export_pseudo_formal_block_verifier_llm_responses(
        Path(args.prompt_packets_manifest),
        Path(args.out),
        provider=provider,
        provider_name=provider_name,
        model=str(args.model or ""),
        model_tier=str(args.model_tier or "sonnet"),
        max_packets=args.max_packets,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        max_repair_attempts=args.max_repair_attempts,
    )
    print("\nAI Statistical Theory Lab Pseudo-Formal BlockVerifier LLM Responses")
    print("=" * 72)
    print(
        f"provider={payload['provider_name']} model={payload['model']} "
        f"responses={payload['n_ok_responses']}/{payload['n_prompt_packets']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nLLM response manifest written to "
        f"{(Path(args.out) / 'pseudo_formal_block_verifier_llm_response_manifest.json').resolve()}"
    )
    print(
        f"response jsonl written to "
        f"{(Path(args.out) / 'pseudo_formal_block_verifier_responses.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _pseudo_formal_block_verifier_provider(
    *,
    provider_name: str,
    static_response_file: Path | None,
    llm_timeout_seconds: float | None,
):
    if provider_name == "anthropic":
        return AnthropicArchitectLLMProvider(timeout_s=llm_timeout_seconds)
    if provider_name == "openai":
        return OpenAIResponsesGeneratorBackend(timeout_s=llm_timeout_seconds)
    if provider_name == "static":
        if static_response_file is None:
            raise ValueError("static provider requires --static-response-file")
        return StaticArchitectLLMProvider(
            static_response_file.read_text(encoding="utf-8")
        )
    raise ValueError(
        "unsupported PF BlockVerifier provider: "
        f"{provider_name!r}; expected anthropic, openai, or static"
    )


def _pseudo_formal_block_verifier_response_validation(args: argparse.Namespace) -> int:
    payload = export_pseudo_formal_block_verifier_response_validation(
        Path(args.prompt_packets_manifest),
        Path(args.response_jsonl),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Pseudo-Formal BlockVerifier Response Validation")
    print("=" * 72)
    print(
        f"responses={payload['n_valid_responses']}/{payload['n_responses']} "
        f"learning_rows={payload['n_runtime_learning_rows']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nvalidation manifest written to "
        f"{(Path(args.out) / 'pseudo_formal_block_verifier_response_validation_manifest.json').resolve()}"
    )
    print(
        f"runtime learning rows written to "
        f"{(Path(args.out) / 'runtime_learning_rows.jsonl').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _pseudo_formal_block_verifier_component_gate(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    provider_name = str(args.provider or "anthropic").strip().lower()
    provider = _pseudo_formal_block_verifier_provider(
        provider_name=provider_name,
        static_response_file=(
            Path(args.static_response_file)
            if str(args.static_response_file or "").strip()
            else None
        ),
        llm_timeout_seconds=args.llm_timeout_seconds,
    )
    payload = run_pseudo_formal_block_verifier_component_gate(
        [Path(path) for path in args.runtime_learning_jsonl],
        Path(args.out),
        provider=provider,
        provider_name=provider_name,
        model=str(args.model or ""),
        model_tier=str(args.model_tier or "sonnet"),
        max_packets=args.max_packets,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        max_repair_attempts=args.max_repair_attempts,
    )
    print("\nAI Statistical Theory Lab Pseudo-Formal BlockVerifier Component Gate")
    print("=" * 72)
    print(f"provider={payload['provider_name']} model={payload['model']}")
    print(f"live_generator={payload['live_generator']}")
    print(f"static_or_fixture_only={payload['static_or_fixture_only']}")
    print(f"fixture_plumbing_ok={payload['fixture_plumbing_ok']}")
    print(f"capability_evidence_ok={payload['capability_evidence_ok']}")
    print(
        "prompt_packets="
        f"{payload['n_ok_prompt_packets']}/{payload['n_prompt_packets']} "
        "valid_responses="
        f"{payload['n_valid_responses']} "
        "runtime_learning_rows="
        f"{payload['n_runtime_learning_rows']}"
    )
    print(f"proof_evidence_status={payload['proof_evidence_status']}")
    print(f"manifest={payload['artifacts']['manifest_json']}")
    if payload["capability_evidence_ok"]:
        return 0
    if args.allow_fixture_success and payload["fixture_plumbing_ok"]:
        return 0
    return 1


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


def _exact_source_theorem_proof_body_executor(args: argparse.Namespace) -> int:
    queue_dir = (
        Path(args.exact_source_theorem_proof_body_execution_queue_dir)
        if args.exact_source_theorem_proof_body_execution_queue_dir
        else None
    )
    generated_queue_payload: Mapping[str, object] | None = None
    if args.proof_body_repair_work_orders_jsonl:
        generated_queue_payload = (
            export_exact_source_theorem_proof_body_repair_execution_queue(
                proof_body_repair_work_orders_jsonl=Path(
                    args.proof_body_repair_work_orders_jsonl
                ),
                out_dir=Path(args.out)
                / "exact_source_theorem_proof_body_repair_execution_queue",
            )
        )
        queue_dir = Path(
            str(generated_queue_payload["proof_body_execution_queue_manifest"])
        ).parent
    if queue_dir is None:
        raise SystemExit(
            "exact-source-theorem-proof-body-executor requires either "
            "--exact-source-theorem-proof-body-execution-queue-dir or "
            "--proof-body-repair-work-orders-jsonl"
        )
    payload = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        Path(args.out),
        overwrite=bool(args.overwrite),
        local_lean=bool(args.local_lean),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
    )
    print("\nAI Statistical Theory Lab Exact Source Theorem Proof-Body Executor")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_execution_result_rows']} "
        f"materialized={payload['n_materialized_candidate_artifacts']} "
        f"checked={payload['n_local_lean_checked']} "
        f"artifact_kernel={payload['n_artifact_kernel_verified']} "
        f"source_theorem_kernel={payload['n_source_theorem_kernel_verified']} "
        f"placeholder_env_blockers={payload['n_placeholder_environment_blockers']} "
        f"all_ok={payload['all_ok']}"
    )
    if generated_queue_payload is not None:
        print(
            "direct proof-body repair execution queue written to "
            f"{Path(str(generated_queue_payload['proof_body_execution_queue_manifest'])).resolve()}"
        )
    print(
        "exact source proof-body executor manifest written to "
        f"{(Path(args.out) / 'exact_source_theorem_proof_body_execution_result_manifest.json').resolve()}"
    )
    print(f"proof_evidence_status={payload['proof_evidence_status']}")
    return 0 if payload["all_ok"] else 1


def _runtime_source_theorem_promotion_proofengineer_bridge(
    args: argparse.Namespace,
) -> int:
    payload = _run_runtime_source_theorem_promotion_proofengineer_bridge(
        seed_queue_dir=Path(args.seed_queue_dir),
        out_dir=Path(args.out),
        local_lean=not bool(args.no_local_lean),
        overwrite_artifacts=bool(args.overwrite),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
    )
    print("\nAI Statistical Theory Lab Runtime Source-Theorem ProofEngineer Bridge")
    print("=" * 72)
    print(
        f"materialized={payload['n_materialized_artifacts']} "
        f"artifact_kernel={payload['n_artifact_kernel_verified']} "
        f"formal_env_work_orders={payload['n_source_theorem_formal_environment_work_orders']} "
        f"ready_source_integration={payload['n_ready_for_source_theorem_integration']} "
        f"source_kernel={payload['n_source_theorem_kernel_verified']} "
        f"local_lean_skipped={payload['local_lean_skipped_reason'] or 'no'}"
    )
    print(
        f"\nbridge manifest written to "
        f"{(Path(args.out) / 'runtime_source_theorem_promotion_proofengineer_bridge_manifest.json').resolve()}"
    )
    if payload.get("source_theorem_formal_environment_work_order_manifest"):
        print(
            f"formal-environment work-order manifest written to "
            f"{Path(str(payload['source_theorem_formal_environment_work_order_manifest'])).resolve()}"
        )
    print(f"proof evidence status: {payload['proof_evidence_status']}")
    return 0


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


def _formal_verifier_agentic_proof_source_theorem_integrator(
    args: argparse.Namespace,
) -> int:
    payload = export_formal_verifier_agentic_proof_source_theorem_integrator(
        Path(args.formal_verifier_agentic_proof_source_theorem_promotion_queue_dir),
        Path(args.out),
        lean_project=Path(args.lean_project) if args.lean_project else None,
        lean_timeout=int(args.lean_timeout),
        local_lean=not bool(args.no_local_lean),
    )
    print("\nAI Statistical Theory Lab Formal Verifier Source-Theorem Integrator")
    print("=" * 72)
    print(
        f"rows={payload['n_ok']}/{payload['n_integration_rows']} "
        f"source_kernel={payload['n_source_theorem_kernel_verified']} "
        f"route_probe_blocked={payload['n_blocked_route_probe']} "
        f"ready_local_lean={payload['n_ready_for_local_lean']} "
        f"all_ok={payload['all_ok']}"
    )
    print(
        f"\nsource theorem integrator manifest written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_source_theorem_integrator_manifest.json').resolve()}"
    )
    print(
        f"source theorem integrator jsonl written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_source_theorem_integrator.jsonl').resolve()}"
    )
    print(
        f"markdown report written to "
        f"{(Path(args.out) / 'formal_verifier_agentic_proof_source_theorem_integrator.md').resolve()}"
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
    env_file = _resolve_dotenv_path(Path(args.env_file))
    _load_dotenv(env_file)
    report = build_doctor_report(
        root=Path(args.root),
        env_file=env_file,
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
        print(f"local_lean_available={summary['local_lean_available']}")
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
            research_agent_runtime_offline_smoke=(
                not args.no_research_agent_runtime_offline_smoke
            ),
            research_agent_runtime_contract_smoke=(
                not args.no_research_agent_runtime_contract_smoke
            ),
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
    questions, missing_question_ids = _select_questions_by_id(
        questions,
        getattr(args, "question_id", []) or [],
    )
    if missing_question_ids:
        print("\nAI Statistician Research Architect rejected question ids")
        print("=" * 72)
        for question_id in missing_question_ids:
            print(f"- unknown question_id: {question_id}")
        return 2
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
    _attach_runtime_capability_gap_routing(args, context)
    model = _default_model_for_provider(args.provider, args.llm_model, model_tier="sonnet")
    theory_developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            model=model,
            model_tier="sonnet",
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            provider_name=provider_name,
            max_repair_attempts=args.max_repair_attempts,
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
    _apply_research_agent_runtime_capability_eval_preset(args)
    _apply_research_agent_runtime_live_lean_defaults(args)
    if getattr(args, "capability_eval", False):
        config_errors = _research_agent_runtime_capability_config_errors(args)
        if config_errors:
            print("\nAI Statistician Agent Runtime capability eval rejected")
            print("=" * 72)
            for error in config_errors:
                print(f"- {error}")
            return 2
    static_config_errors = _research_agent_runtime_static_subsystem_config_errors(args)
    if static_config_errors:
        print("\nAI Statistician Agent Runtime static subsystem config rejected")
        print("=" * 72)
        for error in static_config_errors:
            print(f"- {error}")
        return 2
    verifier = _proof_verifier_from_args(args)
    proof_state_provider = _proof_state_provider_from_args(args)
    resume_initial_tasks: dict[str, AgentTask] = {}
    resume_blackboard_artifacts: dict[str, dict[str, Any]] = {}
    resume_question_id = ""
    resume_learning_memory_paths: list[Path] = []
    if getattr(args, "resume_runtime_manifest", ""):
        resume_manifest_path = Path(args.resume_runtime_manifest)
        try:
            (
                resume_question_id,
                resume_task,
                resume_artifacts,
            ) = _load_runtime_resume_task_from_manifest(resume_manifest_path)
            resume_learning_memory_paths = _runtime_resume_learning_memory_paths(
                resume_manifest_path
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print("\nAI Statistician Agent Runtime rejected resume manifest")
            print("=" * 72)
            print(f"- {exc}")
            return 2
        resume_initial_tasks[resume_question_id] = resume_task
        resume_blackboard_artifacts[resume_question_id] = resume_artifacts
    questions = load_open_research_questions(Path(args.question_file))
    requested_question_ids = list(getattr(args, "question_id", []) or [])
    if resume_question_id and not requested_question_ids:
        requested_question_ids = [resume_question_id]
    questions, missing_question_ids = _select_questions_by_id(
        questions,
        requested_question_ids,
    )
    if missing_question_ids:
        print("\nAI Statistician Agent Runtime rejected question ids")
        print("=" * 72)
        for question_id in missing_question_ids:
            print(f"- unknown question_id: {question_id}")
        return 2
    questions, missing_task_families = _select_questions_by_task_family(
        questions,
        getattr(args, "question_task_family", []) or [],
    )
    if missing_task_families:
        print("\nAI Statistician Agent Runtime rejected task families")
        print("=" * 72)
        for task_family in missing_task_families:
            print(f"- unknown task_family: {task_family}")
        return 2
    if args.max_questions:
        questions = questions[: args.max_questions]
    task_family_selection_errors = _minimum_task_family_selection_errors(
        questions,
        min_task_families=int(getattr(args, "min_task_families", 0) or 0),
    )
    if task_family_selection_errors:
        print("\nAI Statistician Agent Runtime rejected task-family selection")
        print("=" * 72)
        for error in task_family_selection_errors:
            print(f"- {error}")
        return 2
    if resume_question_id and (
        len(questions) != 1 or str(getattr(questions[0], "id", "") or "") != resume_question_id
    ):
        print("\nAI Statistician Agent Runtime rejected resume selection")
        print("=" * 72)
        print(
            "- --resume-runtime-manifest must run exactly the pending question id: "
            f"{resume_question_id}"
        )
        return 2
    provider, provider_name = _build_theory_generator_backend(
        provider_name=args.provider,
        static_response_file=args.static_response_file,
        llm_timeout_seconds=getattr(args, "llm_timeout_seconds", None),
    )
    context: dict[str, object] = {}
    if args.context_json:
        context = json.loads(Path(args.context_json).read_text(encoding="utf-8"))
    _attach_runtime_learning_memory(
        args,
        context,
        extra_paths=resume_learning_memory_paths,
    )
    _attach_runtime_capability_gap_routing(args, context)
    model = _default_model_for_provider(args.provider, args.llm_model, model_tier="sonnet")
    theory_developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            model=model,
            model_tier="sonnet",
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            provider_name=provider_name,
            max_repair_attempts=args.theory_max_repair_attempts,
        ),
    )
    architect_coordinator = _build_architect_coordinator_agent_from_args(args, default_model=model)
    algorithm_engineer = _build_algorithm_engineer_agent_from_args(args, default_model=model)
    simulation_engineer = _build_simulation_engineer_agent_from_args(args, default_model=model)
    formalizer = _build_formalizer_agent_from_args(args, default_model=model)
    critic_evaluator = _build_critic_evaluator_agent_from_args(args, default_model=model)
    resume_through_architect = _effective_resume_through_architect(
        args,
        architect_coordinator_configured=architect_coordinator is not None,
    )
    gap_planner_live_provider_arg = str(
        getattr(args, "formalization_gap_planner_live_provider", "same") or "same"
    )
    if gap_planner_live_provider_arg == "same":
        gap_planner_live_provider = (
            provider_name
            if provider_name in LIVE_GENERATOR_PROVIDER_CHOICES
            else _default_live_generator_provider()
        )
    else:
        gap_planner_live_provider = gap_planner_live_provider_arg
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
        initial_task_overrides=resume_initial_tasks,
        initial_blackboard_artifacts=resume_blackboard_artifacts,
        config=ResearchAgentRuntimeConfig(
            n_runs=args.runs,
            seed=args.seed,
            max_iterations=args.max_iterations,
            max_subsystem_retries=args.max_subsystem_retries,
            max_critic_repair_rounds=args.max_critic_repair_rounds,
            algorithm_engineer_generated_code_repair_yield_after_attempts=int(
                getattr(
                    args,
                    "algorithm_engineer_generated_code_repair_yield_after_attempts",
                    0,
                )
                or 0
            ),
            simulation_evaluator_generated_code_repair_yield_after_attempts=int(
                getattr(
                    args,
                    "simulation_evaluator_generated_code_repair_yield_after_attempts",
                    0,
                )
                or 0
            ),
            formalizer_lean_candidate_repair_yield_to_gap_planner_after_attempts=int(
                getattr(
                    args,
                    "formalizer_lean_candidate_repair_yield_to_gap_planner_after_attempts",
                    0,
                )
                or 0
            ),
            resume_through_architect=resume_through_architect,
            formal_verification_policy=str(
                getattr(args, "formal_verification_policy", "optional") or "optional"
            ),
            recommended_research_path=str(
                getattr(args, "recommended_research_path", "") or ""
            ),
            proof_obligation_ids=tuple(args.proof_obligation_id or ()),
            max_proof_obligations=args.max_proof_obligations,
            llm_timeout_seconds=args.llm_timeout_seconds,
            evaluation_mode=(
                "capability_eval"
                if getattr(args, "capability_eval", False)
                else "debug"
            ),
            formalizer_candidate_local_lean=bool(
                getattr(args, "formalizer_candidate_local_lean", False)
                or getattr(args, "formalizer_candidate_lean_lsp_mcp", False)
            ),
            formalizer_candidate_lean_lsp_mcp=bool(
                getattr(args, "formalizer_candidate_lean_lsp_mcp", False)
            ),
            formalizer_candidate_lean_project=str(
                getattr(args, "formalizer_candidate_lean_project", "")
                or getattr(args, "lean_project", "")
                or ""
            ),
            formalizer_candidate_lean_timeout=int(
                getattr(args, "formalizer_candidate_lean_timeout", 30)
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
            source_semantic_proofengineer_bridge=bool(
                getattr(args, "source_semantic_proofengineer_bridge", False)
            ),
            source_semantic_proofengineer_local_lean=bool(
                getattr(args, "source_semantic_proofengineer_local_lean", False)
            ),
            source_semantic_proofengineer_lean_project=str(
                getattr(args, "source_semantic_proofengineer_lean_project", "") or ""
            ),
            source_semantic_proofengineer_lean_timeout=int(
                getattr(args, "source_semantic_proofengineer_lean_timeout", 90)
            ),
            source_theorem_proof_body_adapter_proofengineer_bridge=bool(
                getattr(
                    args,
                    "source_theorem_proof_body_adapter_proofengineer_bridge",
                    False,
                )
            ),
            source_theorem_proof_body_adapter_proofengineer_local_lean=bool(
                getattr(
                    args,
                    "source_theorem_proof_body_adapter_proofengineer_local_lean",
                    False,
                )
            ),
            source_theorem_proof_body_adapter_proofengineer_lean_project=str(
                getattr(
                    args,
                    "source_theorem_proof_body_adapter_proofengineer_lean_project",
                    "",
                )
                or ""
            ),
            source_theorem_proof_body_adapter_proofengineer_lean_timeout=int(
                getattr(
                    args,
                    "source_theorem_proof_body_adapter_proofengineer_lean_timeout",
                    90,
                )
            ),
            source_to_bridge_premise_derivation_proofengineer_bridge=bool(
                getattr(
                    args,
                    "source_to_bridge_premise_derivation_proofengineer_bridge",
                    False,
                )
            ),
            source_to_bridge_premise_derivation_proofengineer_local_lean=bool(
                getattr(
                    args,
                    "source_to_bridge_premise_derivation_proofengineer_local_lean",
                    False,
                )
            ),
            source_to_bridge_premise_derivation_proofengineer_lean_project=str(
                getattr(
                    args,
                    "source_to_bridge_premise_derivation_proofengineer_lean_project",
                    "",
                )
                or ""
            ),
            source_to_bridge_premise_derivation_proofengineer_lean_timeout=int(
                getattr(
                    args,
                    "source_to_bridge_premise_derivation_proofengineer_lean_timeout",
                    90,
                )
            ),
            source_theorem_formal_environment_proofengineer_bridge=bool(
                getattr(
                    args,
                    "source_theorem_formal_environment_proofengineer_bridge",
                    False,
                )
            ),
            source_theorem_formal_environment_proofengineer_signature_probes=bool(
                getattr(
                    args,
                    "source_theorem_formal_environment_proofengineer_signature_probes",
                    False,
                )
            ),
            source_theorem_formal_environment_proofengineer_execute_proof_body=bool(
                getattr(
                    args,
                    "source_theorem_formal_environment_proofengineer_execute_proof_body",
                    False,
                )
            ),
            source_theorem_formal_environment_proofengineer_proof_body_local_lean=bool(
                getattr(
                    args,
                    "source_theorem_formal_environment_proofengineer_proof_body_local_lean",
                    False,
                )
            ),
            source_theorem_formal_environment_proofengineer_proof_body_overwrite_artifacts=bool(
                getattr(
                    args,
                    "source_theorem_formal_environment_proofengineer_proof_body_overwrite_artifacts",
                    False,
                )
            ),
            source_theorem_formal_environment_proofengineer_lean_project=str(
                getattr(
                    args,
                    "source_theorem_formal_environment_proofengineer_lean_project",
                    "",
                )
                or ""
            ),
            source_theorem_formal_environment_proofengineer_lean_timeout=int(
                getattr(
                    args,
                    "source_theorem_formal_environment_proofengineer_lean_timeout",
                    90,
                )
            ),
            source_theorem_promotion_proofengineer_bridge=bool(
                getattr(
                    args,
                    "source_theorem_promotion_proofengineer_bridge",
                    False,
                )
            ),
            source_theorem_promotion_proofengineer_local_lean=bool(
                getattr(
                    args,
                    "source_theorem_promotion_proofengineer_local_lean",
                    False,
                )
            ),
            source_theorem_promotion_proofengineer_overwrite_artifacts=bool(
                getattr(
                    args,
                    "source_theorem_promotion_proofengineer_overwrite_artifacts",
                    False,
                )
            ),
            source_theorem_promotion_proofengineer_lean_project=str(
                getattr(
                    args,
                    "source_theorem_promotion_proofengineer_lean_project",
                    "",
                )
                or ""
            ),
            source_theorem_promotion_proofengineer_lean_timeout=int(
                getattr(
                    args,
                    "source_theorem_promotion_proofengineer_lean_timeout",
                    90,
                )
            ),
            source_theorem_exact_semantic_definition_source_lookup=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_source_lookup",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_source_roots=tuple(
                str(value)
                for value in (
                    getattr(
                        args,
                        "source_theorem_exact_semantic_definition_source_root",
                        [],
                    )
                    or []
                )
                if str(value).strip()
            ),
            source_theorem_exact_semantic_definition_source_lookup_max_hits=int(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_source_lookup_max_hits",
                    8,
                )
            ),
            source_theorem_exact_semantic_definition_proofengineer_bridge=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_proofengineer_bridge",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_lean_repair_executor=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_lean_repair_executor",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_lean_repair_executor_local_lean=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_lean_repair_executor_local_lean",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_lean_repair_executor_lean_project=str(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_lean_repair_executor_lean_project",
                    "",
                )
                or ""
            ),
            source_theorem_exact_semantic_definition_lean_repair_executor_lean_timeout=int(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_lean_repair_executor_lean_timeout",
                    90,
                )
            ),
            source_theorem_exact_semantic_definition_lean_environment_repair_executor=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_lean_environment_repair_executor",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_authoring_worker=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_authoring_worker_provider=str(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_provider",
                    "none",
                )
                or "none"
            ),
            source_theorem_exact_semantic_definition_authoring_worker_static_response_file=str(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_static_response_file",
                    "",
                )
                or ""
            ),
            source_theorem_exact_semantic_definition_authoring_worker_model=str(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_model",
                    "",
                )
                or ""
            ),
            source_theorem_exact_semantic_definition_authoring_worker_model_tier=str(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_model_tier",
                    "sonnet",
                )
                or "sonnet"
            ),
            source_theorem_exact_semantic_definition_authoring_worker_max_tokens=int(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_max_tokens",
                    4000,
                )
            ),
            source_theorem_exact_semantic_definition_authoring_worker_temperature=float(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_temperature",
                    0.0,
                )
            ),
            source_theorem_exact_semantic_definition_authoring_worker_max_repair_attempts=int(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_max_repair_attempts",
                    1,
                )
            ),
            source_theorem_exact_semantic_definition_authoring_worker_llm_timeout_seconds=float(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_llm_timeout_seconds",
                    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
                )
            ),
            source_theorem_exact_semantic_definition_authoring_worker_max_tasks=int(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_max_tasks",
                    0,
                )
            ),
            source_theorem_exact_semantic_definition_authoring_worker_allow_external_export=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_allow_external_export",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_authoring_worker_external_export_mode=str(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_authoring_worker_external_export_mode",
                    "redacted",
                )
                or "redacted"
            ),
            source_theorem_exact_semantic_definition_closure_review=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_closure_review",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_candidate_synthesis=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_candidate_synthesis",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_candidate_synthesis_allow_draft_semantic_repair=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_candidate_synthesis_allow_draft_semantic_repair",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_candidate_synthesis_local_lean=bool(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_candidate_synthesis_local_lean",
                    False,
                )
            ),
            source_theorem_exact_semantic_definition_candidate_synthesis_lean_project=str(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_candidate_synthesis_lean_project",
                    "",
                )
                or ""
            ),
            source_theorem_exact_semantic_definition_candidate_synthesis_lean_timeout=int(
                getattr(
                    args,
                    "source_theorem_exact_semantic_definition_candidate_synthesis_lean_timeout",
                    90,
                )
            ),
            formalization_gap_planner_live_route_planner=bool(
                getattr(
                    args,
                    "formalization_gap_planner_live_route_planner",
                    False,
                )
            ),
            formalization_gap_planner_live_max_handoffs=int(
                getattr(
                    args,
                    "formalization_gap_planner_live_max_handoffs",
                    1,
                )
            ),
            formalization_gap_planner_live_max_route_requests_per_handoff=int(
                getattr(
                    args,
                    "formalization_gap_planner_live_max_route_requests_per_handoff",
                    1,
                )
            ),
            formalization_gap_planner_live_provider=gap_planner_live_provider,
            formalization_gap_planner_live_model=str(
                getattr(args, "formalization_gap_planner_live_model", "") or ""
            ),
            formalization_gap_planner_live_model_tier=str(
                getattr(
                    args,
                    "formalization_gap_planner_live_model_tier",
                    "auto",
                )
                or "auto"
            ),
            formalization_gap_planner_live_max_tokens=int(
                getattr(
                    args,
                    "formalization_gap_planner_live_max_tokens",
                    LLM_ROUTE_PLANNER_DEFAULT_MAX_TOKENS,
                )
            ),
            formalization_gap_planner_live_temperature=float(
                getattr(
                    args,
                    "formalization_gap_planner_live_temperature",
                    0.1,
                )
            ),
            formalization_gap_planner_live_max_repair_attempts=int(
                getattr(
                    args,
                    "formalization_gap_planner_live_max_repair_attempts",
                    1,
                )
            ),
            formalization_gap_planner_live_timeout_seconds=float(
                getattr(
                    args,
                    "formalization_gap_planner_live_timeout_seconds",
                    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
                )
            ),
        ),
    )
    if getattr(args, "run_coding_agent_generated_code_repair_eval", False):
        manifest = _attach_coding_agent_generated_code_repair_eval_to_runtime_manifest(
            args,
            manifest,
        )
    if getattr(args, "run_formalizer_lean_candidate_repair_eval", False):
        manifest = _attach_formalizer_lean_candidate_repair_eval_to_runtime_manifest(
            args,
            manifest,
        )
    if getattr(args, "run_formalizer_pseudo_formal_packet_eval", False):
        manifest = _attach_formalizer_pseudo_formal_packet_eval_to_runtime_manifest(
            args,
            manifest,
        )
    if getattr(args, "run_pseudo_formal_block_verifier_eval", False):
        manifest = _attach_pseudo_formal_block_verifier_eval_to_runtime_manifest(
            args,
            manifest,
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
        routed_rows = [
            row
            for row in scorecard.get("rows", []) or []
            if (
                isinstance(row, dict)
                and row.get("passed") is not True
                and str(row.get("recommended_capability_eval_command", "") or "").strip()
            )
        ]
        if routed_rows:
            print("capability_routing:")
            for row in routed_rows[:3]:
                print(
                    f"- {row.get('requirement_id')}: "
                    f"owner={row.get('next_owner_subsystem')} "
                    f"command={row.get('recommended_capability_eval_command')}"
                )
        return 0 if audit.get("capability_ready_for_full_ai_statistician") else 1
    return 0


def _load_existing_component_eval_manifest(
    path: Path,
    *,
    expected_artifact_kind: str,
) -> dict[str, Any]:
    """Load a prior component calibration manifest for runtime attachment."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"component eval manifest is not a JSON object: {path}")
    artifact_kind = str(payload.get("artifact_kind", "") or "")
    if artifact_kind != expected_artifact_kind:
        raise ValueError(
            "component eval manifest has artifact_kind="
            f"{artifact_kind!r}; expected {expected_artifact_kind!r}: {path}"
        )
    artifacts = (
        dict(payload.get("artifacts", {}))
        if isinstance(payload.get("artifacts", {}), dict)
        else {}
    )
    artifacts.setdefault("manifest_json", str(path))
    payload["artifacts"] = artifacts
    payload.setdefault(
        "attachment_boundary",
        (
            "This manifest was produced by a standalone component calibration "
            "run and is attached to the runtime manifest as calibration evidence "
            "only. It is not theorem proof evidence and not integrated runtime "
            "research success."
        ),
    )
    return payload


def _strict_formalizer_pseudo_formal_packet_attachment_summary(
    eval_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Recompute the runtime-attached Formalizer PF/BV gate from manifest facts."""

    gate_summary = _runtime_component_gate_summary(eval_manifest)
    capability_requirements = (
        dict(eval_manifest.get("capability_evidence_requirements", {}) or {})
        if isinstance(eval_manifest.get("capability_evidence_requirements", {}), Mapping)
        else {}
    )
    routable_target_lanes = [
        str(value)
        for value in eval_manifest.get("pseudo_formal_routable_target_lanes", [])
        if str(value).strip()
    ]
    n_pseudo_formal_packets = int(
        eval_manifest.get("n_pseudo_formal_packets", 0) or 0
    )
    n_routable_rows = int(
        eval_manifest.get("n_pseudo_formal_routable_work_order_rows", 0) or 0
    )
    nonproof_boundary_preserved = bool(
        _runtime_learning_memory_bool_like(
            capability_requirements.get("nonproof_boundary_preserved", False)
        )
        or _runtime_learning_memory_bool_like(
            eval_manifest.get("nonproof_boundary_preserved", False)
        )
    )
    raw_model_output_written = _runtime_learning_memory_bool_like(
        eval_manifest.get("raw_model_output_written", False)
    )
    exact_lane_present = (
        PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION
        in routable_target_lanes
    )
    n_exact_semantic_rows = int(
        eval_manifest.get("n_pseudo_formal_exact_semantic_definition_rows", 0) or 0
    )
    n_exact_semantic_rows_with_source_anchors = int(
        eval_manifest.get(
            "n_pseudo_formal_exact_semantic_definition_rows_with_source_anchors",
            0,
        )
        or 0
    )
    n_exact_semantic_rows_with_semantic_requirements = int(
        eval_manifest.get(
            "n_pseudo_formal_exact_semantic_definition_rows_with_semantic_requirements",
            0,
        )
        or 0
    )
    n_exact_semantic_rows_with_lineage = int(
        eval_manifest.get(
            "n_pseudo_formal_exact_semantic_definition_rows_with_lineage",
            0,
        )
        or 0
    )
    exact_semantic_rows_source_anchored = _runtime_learning_memory_bool_like(
        eval_manifest.get("exact_semantic_definition_rows_source_anchored", False)
    )
    exact_semantic_rows_semantic_requirements_present = (
        _runtime_learning_memory_bool_like(
            eval_manifest.get(
                "exact_semantic_definition_rows_semantic_requirements_present",
                False,
            )
        )
    )
    exact_semantic_rows_lineage_complete = _runtime_learning_memory_bool_like(
        eval_manifest.get("exact_semantic_definition_rows_lineage_complete", False)
    )
    proof_evidence_status_ok = (
        str(eval_manifest.get("proof_evidence_status", "") or "")
        == FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE
    )
    no_theorem_proof_claim = (
        _runtime_learning_memory_false_like(
            eval_manifest.get("source_theorem_kernel_verified")
        )
        and _runtime_learning_memory_false_like(
            eval_manifest.get("full_frontier_theorem_proved")
        )
    )
    strict_fixture_plumbing_ok = bool(
        _runtime_learning_memory_bool_like(
            eval_manifest.get("fixture_plumbing_ok", False)
        )
        and n_pseudo_formal_packets > 0
        and n_routable_rows > 0
        and exact_lane_present
        and n_exact_semantic_rows > 0
        and exact_semantic_rows_source_anchored
        and exact_semantic_rows_semantic_requirements_present
        and exact_semantic_rows_lineage_complete
        and nonproof_boundary_preserved
        and not raw_model_output_written
        and proof_evidence_status_ok
        and no_theorem_proof_claim
    )
    strict_capability_evidence_ok = bool(
        gate_summary["capability_evidence_ok"]
        and strict_fixture_plumbing_ok
    )
    return {
        **gate_summary,
        "fixture_plumbing_ok": strict_fixture_plumbing_ok,
        "capability_evidence_ok": strict_capability_evidence_ok,
        "exact_semantic_definition_lane_present": exact_lane_present,
        "nonproof_boundary_preserved": nonproof_boundary_preserved,
        "raw_model_output_written": raw_model_output_written,
        "proof_evidence_status_ok": proof_evidence_status_ok,
        "no_theorem_proof_claim": no_theorem_proof_claim,
        "n_pseudo_formal_exact_semantic_definition_rows": n_exact_semantic_rows,
        "n_pseudo_formal_exact_semantic_definition_rows_with_source_anchors": (
            n_exact_semantic_rows_with_source_anchors
        ),
        "n_pseudo_formal_exact_semantic_definition_rows_with_semantic_requirements": (
            n_exact_semantic_rows_with_semantic_requirements
        ),
        "n_pseudo_formal_exact_semantic_definition_rows_with_lineage": (
            n_exact_semantic_rows_with_lineage
        ),
        "exact_semantic_definition_rows_source_anchored": (
            exact_semantic_rows_source_anchored
        ),
        "exact_semantic_definition_rows_semantic_requirements_present": (
            exact_semantic_rows_semantic_requirements_present
        ),
        "exact_semantic_definition_rows_lineage_complete": (
            exact_semantic_rows_lineage_complete
        ),
        "attachment_gate_recomputed": True,
        "attachment_gate_requirements": {
            "live_generator": bool(gate_summary["live_generator"]),
            "manifest_capability_evidence_ok": _runtime_learning_memory_bool_like(
                eval_manifest.get("capability_evidence_ok", False)
            ),
            "fixture_plumbing_ok": strict_fixture_plumbing_ok,
            "pseudo_formal_packets_present": n_pseudo_formal_packets > 0,
            "routable_work_order_rows_present": n_routable_rows > 0,
            "exact_semantic_definition_lane_present": exact_lane_present,
            "exact_semantic_definition_rows_present": n_exact_semantic_rows > 0,
            "exact_semantic_definition_rows_source_anchored": (
                exact_semantic_rows_source_anchored
            ),
            "exact_semantic_definition_rows_semantic_requirements_present": (
                exact_semantic_rows_semantic_requirements_present
            ),
            "exact_semantic_definition_rows_lineage_complete": (
                exact_semantic_rows_lineage_complete
            ),
            "nonproof_boundary_preserved": nonproof_boundary_preserved,
            "raw_model_output_not_written": not raw_model_output_written,
            "proof_evidence_status_ok": proof_evidence_status_ok,
            "no_theorem_proof_claim": no_theorem_proof_claim,
        },
    }


def _attach_coding_agent_generated_code_repair_eval_to_runtime_manifest(
    args: argparse.Namespace,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Run the generated-code repair gate and attach it to a runtime manifest."""

    provider_name = str(
        getattr(args, "coding_agent_repair_eval_provider", "same") or "same"
    )
    if provider_name == "same":
        provider_name = str(getattr(args, "provider", "anthropic") or "anthropic")
    out_dir = Path(
        getattr(args, "coding_agent_repair_eval_out", "")
        or Path(args.out) / "internal_coding_agent_generated_code_repair_eval"
    )
    existing_manifest_path = str(
        getattr(args, "coding_agent_repair_eval_existing_manifest", "") or ""
    ).strip()
    if existing_manifest_path:
        eval_manifest = _load_existing_component_eval_manifest(
            Path(existing_manifest_path),
            expected_artifact_kind="CodingAgentGeneratedCodeRepairEvalManifest",
        )
    else:
        eval_manifest = run_coding_agent_generated_code_repair_eval(
            question_file=Path(args.question_file),
            question_id=(
                str(getattr(args, "coding_agent_repair_eval_question_id", "") or "")
                or "conformal_prediction_coverage"
            ),
            out_dir=out_dir,
            provider_name=provider_name,
            model=str(getattr(args, "coding_agent_repair_eval_model", "") or ""),
            algorithm_static_response_file=(
                Path(getattr(args, "coding_agent_repair_eval_algorithm_static_response_file", ""))
                if getattr(args, "coding_agent_repair_eval_algorithm_static_response_file", "")
                else None
            ),
            simulation_static_response_file=(
                Path(getattr(args, "coding_agent_repair_eval_simulation_static_response_file", ""))
                if getattr(args, "coding_agent_repair_eval_simulation_static_response_file", "")
                else None
            ),
            llm_timeout_seconds=float(
                getattr(
                    args,
                    "coding_agent_repair_eval_llm_timeout_seconds",
                    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
                )
            ),
            max_tokens=int(getattr(args, "coding_agent_repair_eval_max_tokens", 4000)),
            temperature=float(getattr(args, "coding_agent_repair_eval_temperature", 0.1)),
            n_runs=int(getattr(args, "coding_agent_repair_eval_runs", args.runs)),
            seed=int(getattr(args, "coding_agent_repair_eval_seed", args.seed)),
            target_coverage=float(
                getattr(args, "coding_agent_repair_eval_target_coverage", 0.9)
            ),
            max_repair_attempts=int(
                getattr(args, "coding_agent_repair_eval_max_repair_attempts", 4)
            ),
        )
    gate_summary = _runtime_component_gate_summary(eval_manifest)
    attached = {
        "artifact_kind": "RuntimeAttachedCodingAgentGeneratedCodeRepairEval",
        "manifest_path": str(eval_manifest.get("artifacts", {}).get("manifest_json", "")),
        "provider_name": str(gate_summary["provider_name"]),
        "backend_provider_name": str(gate_summary["backend_provider_name"]),
        "component_backend_provider_names": list(
            gate_summary["component_backend_provider_names"]
        ),
        "model": str(eval_manifest.get("model", "")),
        "live_generator": bool(gate_summary["live_generator"]),
        "static_or_fixture_only": bool(gate_summary["static_or_fixture_only"]),
        "fixture_plumbing_ok": _runtime_learning_memory_bool_like(
            eval_manifest.get("fixture_plumbing_ok", False)
        ),
        "capability_evidence_ok": bool(gate_summary["capability_evidence_ok"]),
        "algorithm_capability_evidence_ok": bool(
            eval_manifest.get("algorithm_capability_evidence_ok", False)
        ),
        "simulation_capability_evidence_ok": bool(
            eval_manifest.get("simulation_capability_evidence_ok", False)
        ),
        "algorithm_repair_sequences": int(
            eval_manifest.get("algorithm_repair_sequences", 0) or 0
        ),
        "algorithm_live_repair_sequences": int(
            eval_manifest.get("algorithm_live_repair_sequences", 0) or 0
        ),
        "simulation_repair_sequences": int(
            eval_manifest.get("simulation_repair_sequences", 0) or 0
        ),
        "simulation_live_repair_sequences": int(
            eval_manifest.get("simulation_live_repair_sequences", 0) or 0
        ),
        "prior_failure_feedback_injected": bool(
            eval_manifest.get("prior_failure_feedback_injected", False)
        ),
        "autonomous_live_failed_then_passed_repair_observed": bool(
            eval_manifest.get(
                "autonomous_live_failed_then_passed_repair_observed",
                False,
            )
        ),
        "capability_evidence_scope": str(
            eval_manifest.get("capability_evidence_scope", "") or ""
        ),
        "proof_evidence_status": str(
            eval_manifest.get(
                "proof_evidence_status",
                "CODING_AGENT_GENERATED_CODE_REPAIR_EVAL_NOT_PROOF_EVIDENCE",
            )
        ),
        "boundary": (
            "This attached component gate checks generated-code repair capability "
            "for AlgorithmEngineer and SimulationEngineer. It is not theorem proof, "
            "not simulation proof, and not a substitute for an integrated "
            "AgentRuntime research success."
        ),
    }
    manifest["internal_coding_agent_generated_code_repair_eval"] = attached
    manifest["internal_coding_agent_generated_code_repair_eval_provider_name"] = str(
        attached["provider_name"]
    )
    manifest["internal_coding_agent_generated_code_repair_eval_backend_provider_name"] = str(
        attached["backend_provider_name"]
    )
    manifest[
        "internal_coding_agent_generated_code_repair_eval_component_backend_provider_names"
    ] = list(attached["component_backend_provider_names"])
    manifest["internal_coding_agent_generated_code_repair_eval_live_generator"] = bool(
        attached["live_generator"]
    )
    manifest["internal_coding_agent_generated_code_repair_eval_capability_evidence_ok"] = bool(
        attached["capability_evidence_ok"]
    )
    manifest[
        "internal_coding_agent_generated_code_repair_eval_static_or_fixture_only"
    ] = bool(attached["static_or_fixture_only"])
    manifest[
        "internal_coding_agent_generated_code_repair_eval_algorithm_repair_sequences"
    ] = int(attached["algorithm_repair_sequences"])
    manifest[
        "internal_coding_agent_generated_code_repair_eval_algorithm_live_repair_sequences"
    ] = int(attached["algorithm_live_repair_sequences"])
    manifest[
        "internal_coding_agent_generated_code_repair_eval_simulation_repair_sequences"
    ] = int(attached["simulation_repair_sequences"])
    manifest[
        "internal_coding_agent_generated_code_repair_eval_simulation_live_repair_sequences"
    ] = int(attached["simulation_live_repair_sequences"])
    manifest[
        "internal_coding_agent_generated_code_repair_eval_autonomous_live_failed_then_passed_repair_observed"
    ] = bool(attached["autonomous_live_failed_then_passed_repair_observed"])
    manifest[
        "internal_coding_agent_generated_code_repair_eval_capability_evidence_scope"
    ] = str(attached["capability_evidence_scope"])
    manifest.setdefault("artifacts", {})[
        "internal_coding_agent_generated_code_repair_eval_manifest_json"
    ] = str(attached["manifest_path"])
    _refresh_runtime_coding_agent_capability_manifest(
        manifest,
        runtime_out_dir=Path(args.out),
    )
    manifest_path = Path(args.out) / "research_agent_runtime_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _attach_formalizer_lean_candidate_repair_eval_to_runtime_manifest(
    args: argparse.Namespace,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Run the Formalizer Lean-candidate repair gate and attach it to runtime output."""

    provider_name = str(
        getattr(args, "formalizer_repair_eval_provider", "same") or "same"
    )
    if provider_name == "same":
        provider_name = str(getattr(args, "provider", "anthropic") or "anthropic")
    out_dir = Path(
        getattr(args, "formalizer_repair_eval_out", "")
        or Path(args.out) / "internal_formalizer_lean_candidate_repair_eval"
    )
    eval_model = str(getattr(args, "formalizer_repair_eval_model", "") or "")
    runtime_timeout_seconds = float(
        getattr(
            args,
            "formalizer_repair_eval_runtime_timeout_seconds",
            max(DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS * 2.0, 300.0),
        )
        or 0.0
    )
    existing_manifest_path = str(
        getattr(args, "formalizer_repair_eval_existing_manifest", "") or ""
    ).strip()
    if existing_manifest_path:
        eval_manifest = _load_existing_component_eval_manifest(
            Path(existing_manifest_path),
            expected_artifact_kind="FormalizerLeanCandidateRepairEvalManifest",
        )
    else:
        question_id = (
            str(getattr(args, "formalizer_repair_eval_question_id", "") or "")
            or "conformal_prediction_coverage"
        )

        def _run_eval() -> dict[str, Any]:
            return run_formalizer_lean_candidate_repair_eval(
                question_file=Path(args.question_file),
                question_id=question_id,
                out_dir=out_dir,
                provider_name=provider_name,
                model=eval_model,
                static_response_file=(
                    Path(
                        getattr(
                            args,
                            "formalizer_repair_eval_static_response_file",
                            "",
                        )
                    )
                    if getattr(args, "formalizer_repair_eval_static_response_file", "")
                    else None
                ),
                llm_timeout_seconds=float(
                    getattr(
                        args,
                        "formalizer_repair_eval_llm_timeout_seconds",
                        DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
                    )
                ),
                max_tokens=int(getattr(args, "formalizer_repair_eval_max_tokens", 4000)),
                temperature=float(
                    getattr(args, "formalizer_repair_eval_temperature", 0.1)
                ),
                lean_project=(
                    Path(getattr(args, "formalizer_repair_eval_lean_project", ""))
                    if getattr(args, "formalizer_repair_eval_lean_project", "")
                    else None
                ),
                lean_timeout=int(
                    getattr(args, "formalizer_repair_eval_lean_timeout", 15)
                ),
                lean_lsp_mcp_proof_state_feedback=bool(
                    getattr(args, "formalizer_candidate_lean_lsp_mcp", False)
                ),
                max_repair_attempts=int(
                    getattr(args, "formalizer_repair_eval_max_repair_attempts", 3)
                ),
            )

        try:
            if runtime_timeout_seconds > 0:
                eval_manifest = _call_with_wall_clock_timeout(
                    _run_eval,
                    timeout_s=runtime_timeout_seconds,
                    provider_name=f"{provider_name}:formalizer_repair_eval",
                    model=eval_model or "formalizer_lean_candidate_repair_eval",
                )
            else:
                eval_manifest = _run_eval()
        except Exception as exc:
            eval_manifest = write_formalizer_lean_candidate_repair_eval_failure_manifest(
                out_dir=out_dir,
                provider_name=provider_name,
                model=eval_model,
                question_id=question_id,
                exc=exc,
            )
    gate_summary = _runtime_component_gate_summary(eval_manifest)
    prior_feedback_counts = dict(
        eval_manifest.get("prior_feedback_proof_state_counts", {}) or {}
    )
    attached = {
        "artifact_kind": "RuntimeAttachedFormalizerLeanCandidateRepairEval",
        "manifest_path": str(eval_manifest.get("artifacts", {}).get("manifest_json", "")),
        "provider_name": str(gate_summary["provider_name"]),
        "backend_provider_name": str(gate_summary["backend_provider_name"]),
        "model": str(eval_manifest.get("model", "")),
        "result_status": str(eval_manifest.get("result_status", "") or ""),
        "failure_classification": str(
            eval_manifest.get("failure_classification", "") or ""
        ),
        "failure_exception_type": str(
            eval_manifest.get("failure_exception_type", "") or ""
        ),
        "failure_message": str(eval_manifest.get("failure_message", "") or ""),
        "live_generator": bool(gate_summary["live_generator"]),
        "static_or_fixture_only": bool(gate_summary["static_or_fixture_only"]),
        "capability_evidence_ok": bool(gate_summary["capability_evidence_ok"]),
        "attachment_runtime_timeout_seconds": runtime_timeout_seconds,
        "candidate_kernel_verified": bool(
            eval_manifest.get("candidate_kernel_verified", False)
        ),
        "proofengineer_repair_task_observed": bool(
            eval_manifest.get("proofengineer_repair_task_observed", False)
        ),
        "prior_feedback_proof_state_provider": str(
            eval_manifest.get("prior_feedback_proof_state_provider", "") or ""
        ),
        "prior_feedback_proof_state_rows": int(
            eval_manifest.get("prior_feedback_proof_state_rows", 0) or 0
        ),
        "prior_feedback_proof_state_counts": dict(
            prior_feedback_counts
        ),
        "prior_feedback_local_lean_tool_calls": int(
            prior_feedback_counts.get("local_lean_tool_calls", 0) or 0
        ),
        "prior_feedback_lean_lsp_mcp_tool_calls": int(
            prior_feedback_counts.get("lean_lsp_mcp_tool_calls", 0) or 0
        ),
        "prior_feedback_executed_tool_calls": int(
            prior_feedback_counts.get("executed_tool_calls", 0) or 0
        ),
        "source_theorem_kernel_verified": _runtime_learning_memory_bool_like(
            eval_manifest.get("source_theorem_kernel_verified", False)
        ),
        "full_frontier_theorem_proved": _runtime_learning_memory_bool_like(
            eval_manifest.get("full_frontier_theorem_proved", False)
        ),
        "repair_sequences": int(
            eval_manifest.get(
                "n_formalizer_lean_candidate_failed_then_passed_repair_sequences",
                0,
            )
            or 0
        ),
        "local_lean_checked": int(
            eval_manifest.get("n_formalizer_lean_candidate_local_lean_checked", 0)
            or 0
        ),
        "local_lean_compiled": int(
            eval_manifest.get("n_formalizer_lean_candidate_local_lean_compiled", 0)
            or 0
        ),
        "proof_evidence_status": str(
            eval_manifest.get(
                "proof_evidence_status",
                "FORMALIZER_LEAN_CANDIDATE_REPAIR_EVAL_NOT_SOURCE_THEOREM_PROOF_EVIDENCE",
            )
        ),
        "boundary": (
            "This attached component gate checks Formalizer/ProofEngineer "
            "Lean-candidate repair capability. A compiled helper candidate is "
            "kernel evidence only for that exact helper artifact; it is not "
            "source theorem proof and not full frontier theorem closure."
        ),
    }
    manifest["internal_formalizer_lean_candidate_repair_eval"] = attached
    manifest["internal_formalizer_lean_candidate_repair_eval_provider_name"] = str(
        attached["provider_name"]
    )
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_backend_provider_name"
    ] = str(attached["backend_provider_name"])
    manifest["internal_formalizer_lean_candidate_repair_eval_live_generator"] = bool(
        attached["live_generator"]
    )
    manifest["internal_formalizer_lean_candidate_repair_eval_result_status"] = str(
        attached["result_status"]
    )
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_failure_classification"
    ] = str(attached["failure_classification"])
    manifest["internal_formalizer_lean_candidate_repair_eval_capability_evidence_ok"] = bool(
        attached["capability_evidence_ok"]
    )
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_static_or_fixture_only"
    ] = bool(attached["static_or_fixture_only"])
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_repair_sequences"
    ] = int(attached["repair_sequences"])
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_local_lean_checked"
    ] = int(attached["local_lean_checked"])
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_local_lean_compiled"
    ] = int(attached["local_lean_compiled"])
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_proofengineer_repair_task_observed"
    ] = bool(attached["proofengineer_repair_task_observed"])
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_prior_feedback_proof_state_rows"
    ] = int(attached["prior_feedback_proof_state_rows"])
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_prior_feedback_local_lean_tool_calls"
    ] = int(attached["prior_feedback_local_lean_tool_calls"])
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_prior_feedback_lean_lsp_mcp_tool_calls"
    ] = int(attached["prior_feedback_lean_lsp_mcp_tool_calls"])
    manifest[
        "internal_formalizer_lean_candidate_repair_eval_prior_feedback_executed_tool_calls"
    ] = int(attached["prior_feedback_executed_tool_calls"])
    manifest.setdefault("artifacts", {})[
        "internal_formalizer_lean_candidate_repair_eval_manifest_json"
    ] = str(attached["manifest_path"])
    _refresh_runtime_coding_agent_capability_manifest(
        manifest,
        runtime_out_dir=Path(args.out),
    )
    manifest_path = Path(args.out) / "research_agent_runtime_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _attach_formalizer_pseudo_formal_packet_eval_to_runtime_manifest(
    args: argparse.Namespace,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Run the Formalizer PF/BV packet gate and attach it to runtime output."""

    provider_name = str(
        getattr(args, "formalizer_pseudo_formal_packet_eval_provider", "same")
        or "same"
    )
    if provider_name == "same":
        provider_name = str(getattr(args, "provider", "anthropic") or "anthropic")
    out_dir = Path(
        getattr(args, "formalizer_pseudo_formal_packet_eval_out", "")
        or Path(args.out) / "internal_formalizer_pseudo_formal_packet_eval"
    )
    existing_manifest_path = str(
        getattr(args, "formalizer_pseudo_formal_packet_eval_existing_manifest", "")
        or ""
    ).strip()
    if existing_manifest_path:
        eval_manifest = _load_existing_component_eval_manifest(
            Path(existing_manifest_path),
            expected_artifact_kind="FormalizerPseudoFormalPacketEvalManifest",
        )
    else:
        eval_model = str(
            getattr(args, "formalizer_pseudo_formal_packet_eval_model", "")
            or ""
        )
        runtime_timeout_seconds = float(
            getattr(
                args,
                "formalizer_pseudo_formal_packet_eval_runtime_timeout_seconds",
                max(DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS * 2.0, 300.0),
            )
            or 0.0
        )

        def _run_eval() -> dict[str, Any]:
            return run_formalizer_pseudo_formal_packet_eval(
                out_dir=out_dir,
                provider_name=provider_name,
                model=eval_model,
                static_response_file=(
                    Path(
                        getattr(
                            args,
                            "formalizer_pseudo_formal_packet_eval_static_response_file",
                            "",
                        )
                    )
                    if getattr(
                        args,
                        "formalizer_pseudo_formal_packet_eval_static_response_file",
                        "",
                    )
                    else None
                ),
                llm_timeout_seconds=float(
                    getattr(
                        args,
                        "formalizer_pseudo_formal_packet_eval_llm_timeout_seconds",
                        DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
                    )
                ),
                max_tokens=int(
                    getattr(
                        args,
                        "formalizer_pseudo_formal_packet_eval_max_tokens",
                        5000,
                    )
                ),
                temperature=float(
                    getattr(
                        args,
                        "formalizer_pseudo_formal_packet_eval_temperature",
                        0.1,
                    )
                ),
                max_repair_attempts=int(
                    getattr(
                        args,
                        "formalizer_pseudo_formal_packet_eval_max_repair_attempts",
                        1,
                    )
                ),
            )

        try:
            if runtime_timeout_seconds > 0:
                eval_manifest = _call_with_wall_clock_timeout(
                    _run_eval,
                    timeout_s=runtime_timeout_seconds,
                    provider_name=f"{provider_name}:formalizer_pseudo_formal_packet_eval",
                    model=eval_model or "formalizer_pseudo_formal_packet_eval",
                )
            else:
                eval_manifest = _run_eval()
        except Exception as exc:
            eval_manifest = (
                write_formalizer_pseudo_formal_packet_eval_failure_manifest(
                    out_dir=out_dir,
                    provider_name=provider_name,
                    model=eval_model,
                    exc=exc,
                )
            )
    gate_summary = _strict_formalizer_pseudo_formal_packet_attachment_summary(
        eval_manifest
    )
    eval_artifacts = (
        dict(eval_manifest.get("artifacts", {}) or {})
        if isinstance(eval_manifest.get("artifacts", {}), Mapping)
        else {}
    )
    attached = {
        "artifact_kind": "RuntimeAttachedFormalizerPseudoFormalPacketEval",
        "manifest_path": str(eval_artifacts.get("manifest_json", "")),
        "artifacts": eval_artifacts,
        "work_order_rows_jsonl": str(
            eval_artifacts.get("work_order_rows_jsonl", "") or ""
        ),
        "routable_work_order_rows_jsonl": str(
            eval_artifacts.get("routable_work_order_rows_jsonl", "") or ""
        ),
        "exact_semantic_definition_rows_jsonl": str(
            eval_artifacts.get("exact_semantic_definition_rows_jsonl", "") or ""
        ),
        "diagnostic_work_order_rows_jsonl": str(
            eval_artifacts.get("diagnostic_work_order_rows_jsonl", "") or ""
        ),
        "provider_name": str(gate_summary["provider_name"]),
        "backend_provider_name": str(gate_summary["backend_provider_name"]),
        "model": str(eval_manifest.get("model", "")),
        "result_status": str(eval_manifest.get("result_status", "")),
        "failure_type": str(eval_manifest.get("failure_type", "")),
        "errors": [
            str(value)
            for value in eval_manifest.get("errors", [])
            if str(value).strip()
        ],
        "pseudo_formal_failure_validation_issue_summary": (
            eval_manifest.get("pseudo_formal_failure_validation_issue_summary", {})
        ),
        "pseudo_formal_failure_issue_specific_repair_actions": (
            eval_manifest.get(
                "pseudo_formal_failure_issue_specific_repair_actions",
                [],
            )
        ),
        "pseudo_formal_failure_concrete_lane_routable_repair_seed": (
            eval_manifest.get(
                "pseudo_formal_failure_concrete_lane_routable_repair_seed",
                {},
            )
        ),
        "pseudo_formal_failure_validator_ready_copy_contract": (
            eval_manifest.get(
                "pseudo_formal_failure_validator_ready_copy_contract",
                {},
            )
        ),
        "pseudo_formal_failure_copy_contract_summary": (
            eval_manifest.get(
                "pseudo_formal_failure_copy_contract_summary",
                {},
            )
        ),
        "pseudo_formal_failure_copy_ready": _runtime_learning_memory_bool_like(
            eval_manifest.get("pseudo_formal_failure_copy_ready", False)
        ),
        "pseudo_formal_failure_copy_exact_semantic_definition_ready": (
            _runtime_learning_memory_bool_like(
                eval_manifest.get(
                    "pseudo_formal_failure_copy_exact_semantic_definition_ready",
                    False,
                )
            )
        ),
        "pseudo_formal_failure_repair_seed_available": (
            _runtime_learning_memory_bool_like(
                eval_manifest.get(
                    "pseudo_formal_failure_repair_seed_available",
                    False,
                )
            )
        ),
        "pseudo_formal_failure_required_target_lanes": [
            str(value)
            for value in eval_manifest.get(
                "pseudo_formal_failure_required_target_lanes",
                [],
            )
            if str(value).strip()
        ],
        "live_generator": bool(gate_summary["live_generator"]),
        "static_or_fixture_only": bool(gate_summary["static_or_fixture_only"]),
        "fixture_plumbing_ok": bool(gate_summary["fixture_plumbing_ok"]),
        "capability_evidence_ok": bool(gate_summary["capability_evidence_ok"]),
        "attachment_runtime_timeout_seconds": float(
            getattr(
                args,
                "formalizer_pseudo_formal_packet_eval_runtime_timeout_seconds",
                max(DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS * 2.0, 300.0),
            )
            or 0.0
        ),
        "n_pseudo_formal_packets": int(
            eval_manifest.get("n_pseudo_formal_packets", 0) or 0
        ),
        "n_pseudo_formal_work_order_rows": int(
            eval_manifest.get("n_pseudo_formal_work_order_rows", 0) or 0
        ),
        "n_pseudo_formal_routable_work_order_rows": int(
            eval_manifest.get("n_pseudo_formal_routable_work_order_rows", 0) or 0
        ),
        "pseudo_formal_routable_row_kinds": [
            str(value)
            for value in eval_manifest.get("pseudo_formal_routable_row_kinds", [])
            if str(value).strip()
        ],
        "pseudo_formal_routable_target_lanes": [
            str(value)
            for value in eval_manifest.get("pseudo_formal_routable_target_lanes", [])
            if str(value).strip()
        ],
        "nonproof_boundary_preserved": bool(
            gate_summary["nonproof_boundary_preserved"]
        ),
        "raw_model_output_written": bool(
            gate_summary["raw_model_output_written"]
        ),
        "exact_semantic_definition_lane_present": bool(
            gate_summary["exact_semantic_definition_lane_present"]
        ),
        "n_pseudo_formal_exact_semantic_definition_rows": int(
            gate_summary["n_pseudo_formal_exact_semantic_definition_rows"]
        ),
        "n_pseudo_formal_exact_semantic_definition_rows_with_source_anchors": int(
            gate_summary[
                "n_pseudo_formal_exact_semantic_definition_rows_with_source_anchors"
            ]
        ),
        "n_pseudo_formal_exact_semantic_definition_rows_with_semantic_requirements": int(
            gate_summary[
                "n_pseudo_formal_exact_semantic_definition_rows_with_semantic_requirements"
            ]
        ),
        "n_pseudo_formal_exact_semantic_definition_rows_with_lineage": int(
            gate_summary[
                "n_pseudo_formal_exact_semantic_definition_rows_with_lineage"
            ]
        ),
        "exact_semantic_definition_rows_source_anchored": bool(
            gate_summary["exact_semantic_definition_rows_source_anchored"]
        ),
        "exact_semantic_definition_rows_semantic_requirements_present": bool(
            gate_summary[
                "exact_semantic_definition_rows_semantic_requirements_present"
            ]
        ),
        "exact_semantic_definition_rows_lineage_complete": bool(
            gate_summary["exact_semantic_definition_rows_lineage_complete"]
        ),
        "proof_evidence_status_ok": bool(gate_summary["proof_evidence_status_ok"]),
        "no_theorem_proof_claim": bool(gate_summary["no_theorem_proof_claim"]),
        "attachment_gate_recomputed": bool(
            gate_summary["attachment_gate_recomputed"]
        ),
        "attachment_gate_requirements": dict(
            gate_summary["attachment_gate_requirements"]
        ),
        "source_theorem_kernel_verified": _runtime_learning_memory_bool_like(
            eval_manifest.get("source_theorem_kernel_verified", False)
        ),
        "full_frontier_theorem_proved": _runtime_learning_memory_bool_like(
            eval_manifest.get("full_frontier_theorem_proved", False)
        ),
        "proof_evidence_status": str(
            eval_manifest.get(
                "proof_evidence_status",
                "FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE",
            )
        ),
        "boundary": (
            "This attached component gate checks whether Formalizer/ProofEngineer "
            "can emit schema-valid pseudo-formal packets with effective "
            "lane-routable work-order rows under required PF/BV activation. It is "
            "not theorem proof evidence, not source theorem kernel verification, "
            "and not full frontier theorem closure."
        ),
    }
    manifest["internal_formalizer_pseudo_formal_packet_eval"] = attached
    manifest["internal_formalizer_pseudo_formal_packet_eval_provider_name"] = str(
        attached["provider_name"]
    )
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_backend_provider_name"
    ] = str(attached["backend_provider_name"])
    manifest["internal_formalizer_pseudo_formal_packet_eval_result_status"] = str(
        attached["result_status"]
    )
    manifest["internal_formalizer_pseudo_formal_packet_eval_failure_type"] = str(
        attached["failure_type"]
    )
    manifest["internal_formalizer_pseudo_formal_packet_eval_errors"] = list(
        attached["errors"]
    )
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_failure_required_target_lanes"
    ] = list(attached["pseudo_formal_failure_required_target_lanes"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_failure_validation_issue_summary"
    ] = attached["pseudo_formal_failure_validation_issue_summary"]
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_failure_concrete_lane_routable_repair_seed"
    ] = attached["pseudo_formal_failure_concrete_lane_routable_repair_seed"]
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_failure_validator_ready_copy_contract"
    ] = attached["pseudo_formal_failure_validator_ready_copy_contract"]
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_failure_copy_contract_summary"
    ] = attached["pseudo_formal_failure_copy_contract_summary"]
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_failure_copy_ready"
    ] = bool(attached["pseudo_formal_failure_copy_ready"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_failure_copy_exact_semantic_definition_ready"
    ] = bool(attached["pseudo_formal_failure_copy_exact_semantic_definition_ready"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_failure_repair_seed_available"
    ] = bool(attached["pseudo_formal_failure_repair_seed_available"])
    manifest["internal_formalizer_pseudo_formal_packet_eval_live_generator"] = bool(
        attached["live_generator"]
    )
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_static_or_fixture_only"
    ] = bool(attached["static_or_fixture_only"])
    manifest["internal_formalizer_pseudo_formal_packet_eval_fixture_plumbing_ok"] = bool(
        attached["fixture_plumbing_ok"]
    )
    manifest["internal_formalizer_pseudo_formal_packet_eval_capability_evidence_ok"] = bool(
        attached["capability_evidence_ok"]
    )
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_attachment_runtime_timeout_seconds"
    ] = float(attached["attachment_runtime_timeout_seconds"])
    manifest["internal_formalizer_pseudo_formal_packet_eval_pseudo_formal_packets"] = int(
        attached["n_pseudo_formal_packets"]
    )
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_work_order_rows"
    ] = int(attached["n_pseudo_formal_work_order_rows"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_routable_work_order_rows"
    ] = int(attached["n_pseudo_formal_routable_work_order_rows"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_routable_row_kinds"
    ] = list(attached["pseudo_formal_routable_row_kinds"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_routable_target_lanes"
    ] = list(attached["pseudo_formal_routable_target_lanes"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_nonproof_boundary_preserved"
    ] = bool(attached["nonproof_boundary_preserved"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_raw_model_output_written"
    ] = bool(attached["raw_model_output_written"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_lane_present"
    ] = bool(attached["exact_semantic_definition_lane_present"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows"
    ] = int(attached["n_pseudo_formal_exact_semantic_definition_rows"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_with_source_anchors"
    ] = int(
        attached[
            "n_pseudo_formal_exact_semantic_definition_rows_with_source_anchors"
        ]
    )
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_with_semantic_requirements"
    ] = int(
        attached[
            "n_pseudo_formal_exact_semantic_definition_rows_with_semantic_requirements"
        ]
    )
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_with_lineage"
    ] = int(attached["n_pseudo_formal_exact_semantic_definition_rows_with_lineage"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_source_anchored"
    ] = bool(attached["exact_semantic_definition_rows_source_anchored"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_semantic_requirements_present"
    ] = bool(attached["exact_semantic_definition_rows_semantic_requirements_present"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_exact_semantic_definition_rows_lineage_complete"
    ] = bool(attached["exact_semantic_definition_rows_lineage_complete"])
    manifest[
        "internal_formalizer_pseudo_formal_packet_eval_attachment_gate_recomputed"
    ] = bool(attached["attachment_gate_recomputed"])
    manifest.setdefault("artifacts", {})[
        "internal_formalizer_pseudo_formal_packet_eval_manifest_json"
    ] = str(attached["manifest_path"])
    for artifact_key in (
        "work_order_rows_jsonl",
        "routable_work_order_rows_jsonl",
        "exact_semantic_definition_rows_jsonl",
        "diagnostic_work_order_rows_jsonl",
    ):
        artifact_path = str(attached.get(artifact_key, "") or "").strip()
        if artifact_path:
            manifest["artifacts"][
                f"internal_formalizer_pseudo_formal_packet_eval_{artifact_key}"
            ] = artifact_path
    _refresh_runtime_coding_agent_capability_manifest(
        manifest,
        runtime_out_dir=Path(args.out),
    )
    manifest_path = Path(args.out) / "research_agent_runtime_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _attach_pseudo_formal_block_verifier_eval_to_runtime_manifest(
    args: argparse.Namespace,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Run the PF/BV component gate and attach it to runtime output."""

    provider_name = str(
        getattr(args, "pseudo_formal_block_verifier_eval_provider", "same") or "same"
    )
    if provider_name == "same":
        provider_name = str(getattr(args, "provider", "anthropic") or "anthropic")
    out_dir = Path(
        getattr(args, "pseudo_formal_block_verifier_eval_out", "")
        or Path(args.out) / "internal_pseudo_formal_block_verifier_eval"
    )
    existing_manifest_path = str(
        getattr(args, "pseudo_formal_block_verifier_eval_existing_manifest", "")
        or ""
    ).strip()
    if existing_manifest_path:
        eval_manifest = _load_existing_component_eval_manifest(
            Path(existing_manifest_path),
            expected_artifact_kind="PseudoFormalBlockVerifierComponentGateManifest",
        )
    else:
        runtime_learning_paths = [
            Path(path)
            for path in (
                getattr(args, "pseudo_formal_block_verifier_runtime_learning_jsonl", [])
                or []
            )
            if str(path).strip()
        ]
        if not runtime_learning_paths:
            runtime_learning_paths = [
                _materialize_pseudo_formal_block_verifier_source_rows(
                    args,
                    manifest,
                    runtime_out_dir=Path(args.out),
                )
            ]
        provider = _pseudo_formal_block_verifier_provider(
            provider_name=provider_name,
            static_response_file=(
                Path(getattr(args, "pseudo_formal_block_verifier_eval_static_response_file", ""))
                if getattr(args, "pseudo_formal_block_verifier_eval_static_response_file", "")
                else None
            ),
            llm_timeout_seconds=float(
                getattr(
                    args,
                    "pseudo_formal_block_verifier_eval_llm_timeout_seconds",
                    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
                )
            ),
        )
        eval_manifest = run_pseudo_formal_block_verifier_component_gate(
            runtime_learning_paths,
            out_dir,
            provider=provider,
            provider_name=provider_name,
            model=str(getattr(args, "pseudo_formal_block_verifier_eval_model", "") or ""),
            model_tier=str(
                getattr(args, "pseudo_formal_block_verifier_eval_model_tier", "sonnet")
                or "sonnet"
            ),
            max_packets=int(
                getattr(args, "pseudo_formal_block_verifier_eval_max_packets", 20)
            ),
            max_tokens=int(
                getattr(args, "pseudo_formal_block_verifier_eval_max_tokens", 2000)
            ),
            temperature=float(
                getattr(args, "pseudo_formal_block_verifier_eval_temperature", 0.0)
            ),
            max_repair_attempts=int(
                getattr(
                    args,
                    "pseudo_formal_block_verifier_eval_max_repair_attempts",
                    1,
                )
            ),
        )
    gate_summary = _runtime_component_gate_summary(eval_manifest)
    artifacts = (
        dict(eval_manifest.get("artifacts", {}) or {})
        if isinstance(eval_manifest.get("artifacts", {}), Mapping)
        else {}
    )
    source_runtime_learning_jsonl_paths = [
        str(path).strip()
        for path in eval_manifest.get("source_runtime_learning_jsonl_paths", [])
        if str(path).strip()
    ]
    source_runtime_learning_lineage_reference_dir = str(Path(args.out).resolve())
    source_runtime_learning_lineage_ok = (
        _pseudo_formal_source_runtime_learning_lineage_ok(
            source_runtime_learning_jsonl_paths,
            runtime_out_dir=Path(args.out),
        )
    )
    attached = {
        "artifact_kind": "RuntimeAttachedPseudoFormalBlockVerifierEval",
        "manifest_path": str(artifacts.get("manifest_json", "")),
        "prompt_packets_manifest_path": str(
            artifacts.get("prompt_packets_manifest_json", "")
        ),
        "llm_response_manifest_path": str(
            artifacts.get("llm_response_manifest_json", "")
        ),
        "response_validation_manifest_path": str(
            artifacts.get("response_validation_manifest_json", "")
        ),
        "runtime_learning_rows_jsonl": str(
            artifacts.get("runtime_learning_rows_jsonl", "")
        ),
        "provider_name": str(gate_summary["provider_name"]),
        "backend_provider_name": str(gate_summary["backend_provider_name"]),
        "component_backend_provider_names": list(
            gate_summary["component_backend_provider_names"]
        ),
        "model": str(eval_manifest.get("model", "")),
        "live_generator": bool(gate_summary["live_generator"]),
        "static_or_fixture_only": bool(gate_summary["static_or_fixture_only"]),
        "fixture_plumbing_ok": _runtime_learning_memory_bool_like(
            eval_manifest.get("fixture_plumbing_ok", False)
        ),
        "capability_evidence_ok": bool(gate_summary["capability_evidence_ok"]),
        "n_prompt_packets": int(eval_manifest.get("n_prompt_packets", 0) or 0),
        "n_ok_prompt_packets": int(eval_manifest.get("n_ok_prompt_packets", 0) or 0),
        "n_llm_response_rows": int(
            eval_manifest.get("n_llm_response_rows", 0) or 0
        ),
        "n_ok_responses": int(eval_manifest.get("n_ok_responses", 0) or 0),
        "n_valid_responses": int(eval_manifest.get("n_valid_responses", 0) or 0),
        "n_runtime_learning_rows": int(
            eval_manifest.get("n_runtime_learning_rows", 0) or 0
        ),
        "n_source_runtime_learning_jsonl_paths": len(
            source_runtime_learning_jsonl_paths
        ),
        "source_runtime_learning_jsonl_paths": list(
            source_runtime_learning_jsonl_paths
        ),
        "source_runtime_learning_lineage_reference_dir": (
            source_runtime_learning_lineage_reference_dir
        ),
        "source_runtime_learning_lineage_ok": bool(
            source_runtime_learning_lineage_ok
        ),
        "n_accepted_blocks": int(eval_manifest.get("n_accepted_blocks", 0) or 0),
        "n_failed_blocks": int(eval_manifest.get("n_failed_blocks", 0) or 0),
        "runtime_learning_rows": [
            dict(row)
            for row in eval_manifest.get("runtime_learning_rows", [])
            if isinstance(row, Mapping)
        ],
        "proof_evidence_status": str(
            eval_manifest.get(
                "proof_evidence_status",
                "PSEUDO_FORMAL_BLOCK_VERIFIER_COMPONENT_GATE_NOT_PROOF_EVIDENCE",
            )
        ),
        "boundary": (
            "This attached component gate checks PF/BV prompt generation, live "
            "LLM BlockVerifier responses, and response validation. It is not "
            "Lean/AXLE proof evidence and not integrated theorem closure."
        ),
    }
    manifest["internal_pseudo_formal_block_verifier_eval"] = attached
    manifest["internal_pseudo_formal_block_verifier_eval_provider_name"] = str(
        attached["provider_name"]
    )
    manifest["internal_pseudo_formal_block_verifier_eval_backend_provider_name"] = str(
        attached["backend_provider_name"]
    )
    manifest[
        "internal_pseudo_formal_block_verifier_eval_component_backend_provider_names"
    ] = list(attached["component_backend_provider_names"])
    manifest["internal_pseudo_formal_block_verifier_eval_live_generator"] = bool(
        attached["live_generator"]
    )
    manifest["internal_pseudo_formal_block_verifier_eval_static_or_fixture_only"] = bool(
        attached["static_or_fixture_only"]
    )
    manifest["internal_pseudo_formal_block_verifier_eval_fixture_plumbing_ok"] = bool(
        attached["fixture_plumbing_ok"]
    )
    manifest["internal_pseudo_formal_block_verifier_eval_capability_evidence_ok"] = bool(
        attached["capability_evidence_ok"]
    )
    manifest["internal_pseudo_formal_block_verifier_eval_prompt_packets"] = int(
        attached["n_prompt_packets"]
    )
    manifest["internal_pseudo_formal_block_verifier_eval_valid_responses"] = int(
        attached["n_valid_responses"]
    )
    manifest["internal_pseudo_formal_block_verifier_eval_runtime_learning_rows"] = int(
        attached["n_runtime_learning_rows"]
    )
    manifest[
        "internal_pseudo_formal_block_verifier_eval_source_runtime_learning_jsonl_paths"
    ] = list(source_runtime_learning_jsonl_paths)
    manifest[
        "internal_pseudo_formal_block_verifier_eval_source_runtime_learning_jsonl_path_count"
    ] = len(source_runtime_learning_jsonl_paths)
    manifest[
        "internal_pseudo_formal_block_verifier_eval_source_runtime_learning_lineage_reference_dir"
    ] = source_runtime_learning_lineage_reference_dir
    manifest[
        "internal_pseudo_formal_block_verifier_eval_source_runtime_learning_lineage_ok"
    ] = bool(source_runtime_learning_lineage_ok)
    manifest.setdefault("artifacts", {})[
        "internal_pseudo_formal_block_verifier_eval_manifest_json"
    ] = str(attached["manifest_path"])
    _refresh_runtime_coding_agent_capability_manifest(
        manifest,
        runtime_out_dir=Path(args.out),
    )
    manifest_path = Path(args.out) / "research_agent_runtime_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _pseudo_formal_source_runtime_learning_lineage_ok(
    source_runtime_learning_jsonl_paths: list[str],
    *,
    runtime_out_dir: Path,
) -> bool:
    """Return true when PF/BV consumed learning rows from this runtime output."""

    try:
        runtime_root = runtime_out_dir.expanduser().resolve()
    except OSError:
        runtime_root = runtime_out_dir.expanduser().absolute()
    for raw_path in source_runtime_learning_jsonl_paths:
        if not str(raw_path).strip():
            continue
        source_path = Path(str(raw_path).strip()).expanduser()
        try:
            if not source_path.is_absolute():
                source_path = (Path.cwd() / source_path).resolve()
            else:
                source_path = source_path.resolve()
            source_path.relative_to(runtime_root)
            return True
        except (OSError, ValueError):
            continue
    return False


def _materialize_pseudo_formal_block_verifier_source_rows(
    args: argparse.Namespace,
    manifest: dict[str, Any],
    *,
    runtime_out_dir: Path,
) -> Path:
    """Materialize current-runtime PF/BV source rows before attached validation."""

    artifacts = manifest.get("artifacts", {})
    default_runtime_learning_path = (
        str(artifacts.get("runtime_learning_rows_jsonl", "") or "")
        if isinstance(artifacts, Mapping)
        else ""
    )
    source_paths = [
        Path(default_runtime_learning_path or runtime_out_dir / "runtime_learning_rows.jsonl")
    ]
    source_paths.extend(
        Path(path)
        for path in getattr(args, "learning_memory_jsonl", []) or []
        if str(path).strip()
    )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source_path in source_paths:
        if not source_path.exists():
            continue
        for line in source_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            row.setdefault("artifact_kind", "RuntimeLearningRow")
            row.setdefault(
                "materialized_for_component_gate",
                "pseudo_formal_block_verifier_component_gate",
            )
            row.setdefault(
                "materialization_boundary",
                (
                    "This row was materialized under the current AgentRuntime "
                    "output directory so an attached PF/BV component gate can "
                    "consume runtime-visible learning memory. It remains "
                    "non-proof routing memory."
                ),
            )
            fingerprint = json.dumps(row, sort_keys=True, default=str)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            rows.append(row)
    source_rows_path = runtime_out_dir / "runtime_pseudo_formal_block_verifier_source_rows.jsonl"
    source_rows_path.parent.mkdir(parents=True, exist_ok=True)
    source_rows_path.write_text(
        "".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )
    artifacts = manifest.setdefault("artifacts", {})
    if isinstance(artifacts, dict):
        artifacts["runtime_pseudo_formal_block_verifier_source_rows_jsonl"] = str(
            source_rows_path
        )
    manifest["runtime_pseudo_formal_block_verifier_source_rows"] = len(rows)
    manifest[
        "runtime_pseudo_formal_block_verifier_source_rows_materialized_from"
    ] = [str(path) for path in source_paths]
    return source_rows_path


def _refresh_runtime_coding_agent_capability_manifest(
    manifest: dict[str, Any],
    *,
    runtime_out_dir: Path,
) -> None:
    """Refresh capability table and learning rows after attached component gates."""

    manifest["runtime_coding_agent_capability"] = (
        _runtime_coding_agent_capability_table(manifest)
    )
    capability_learning_rows = _runtime_coding_agent_capability_learning_rows(
        manifest=manifest,
        capability_table=manifest["runtime_coding_agent_capability"],
    )
    coding_component_gate_learning_rows = (
        _runtime_coding_agent_component_gate_learning_rows(manifest)
    )
    component_gate_learning_rows = _runtime_formalizer_component_gate_learning_rows(
        manifest
    )
    formalizer_pseudo_formal_packet_learning_rows = (
        _runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows(
            manifest
        )
    )
    formalizer_pf_copy_ready_retry_next_action_rows = (
        _runtime_formalizer_pf_copy_ready_retry_next_action_agenda_rows(
            formalizer_pseudo_formal_packet_learning_rows
        )
    )
    formalizer_pf_copy_ready_retry_next_action_learning_rows = (
        _runtime_generated_next_action_learning_rows(
            formalizer_pf_copy_ready_retry_next_action_rows
        )
    )
    pseudo_formal_component_gate_learning_rows = (
        _runtime_pseudo_formal_block_verifier_component_gate_learning_rows(manifest)
    )
    artifacts = manifest.setdefault("artifacts", {})
    learning_path_raw = str(artifacts.get("runtime_learning_rows_jsonl", "") or "")
    if learning_path_raw:
        learning_path = Path(learning_path_raw)
    else:
        learning_path = runtime_out_dir / "runtime_learning_rows.jsonl"
        artifacts["runtime_learning_rows_jsonl"] = str(learning_path)
    existing_rows: list[dict[str, Any]] = []
    if learning_path.exists():
        for line in learning_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                existing_rows.append(row)
    retained_rows = [
        row
        for row in existing_rows
        if row.get("learning_task")
        not in {
            "coding_agent_generated_code_capability_feedback",
            "coding_agent_generated_code_component_gate_feedback",
            "formalizer_lean_candidate_component_gate_feedback",
            "formalizer_pseudo_formal_packet_component_gate_feedback",
            "formalizer_pseudo_formal_packet_component_gate_copy_ready_retry_task",
            "pseudo_formal_block_verifier_component_gate_feedback",
        }
        and not (
            row.get("learning_task") == "generated_next_action_routing"
            and isinstance(row.get("input_summary", {}), Mapping)
            and (
                row.get("input_summary", {}).get("source_learning_task")
                == "formalizer_pseudo_formal_packet_component_gate_copy_ready_retry_task"
                or row.get("input_summary", {}).get("trigger")
                == "FORMALIZER_PF_BV_COPY_READY_RETRY_REQUIRED"
            )
        )
        and row.get("source_component_gate")
        not in {
            "formalizer_pseudo_formal_packet_component_gate",
            "pseudo_formal_block_verifier_component_gate",
        }
    ]
    refreshed_rows = [
        *retained_rows,
        *capability_learning_rows,
        *coding_component_gate_learning_rows,
        *component_gate_learning_rows,
        *formalizer_pseudo_formal_packet_learning_rows,
        *formalizer_pf_copy_ready_retry_next_action_learning_rows,
        *pseudo_formal_component_gate_learning_rows,
    ]
    learning_path.parent.mkdir(parents=True, exist_ok=True)
    _write_runtime_learning_rows_jsonl(learning_path, refreshed_rows)
    agenda_path_raw = str(artifacts.get("runtime_next_action_agenda_jsonl", "") or "")
    if agenda_path_raw:
        agenda_path = Path(agenda_path_raw)
    else:
        agenda_path = runtime_out_dir / "runtime_next_action_agenda.jsonl"
        artifacts["runtime_next_action_agenda_jsonl"] = str(agenda_path)
    existing_agenda_rows: list[dict[str, Any]] = []
    if agenda_path.exists():
        for line in agenda_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                existing_agenda_rows.append(row)
    retained_agenda_rows = [
        row
        for row in existing_agenda_rows
        if row.get("trigger") != "FORMALIZER_PF_BV_COPY_READY_RETRY_REQUIRED"
        and row.get("runtime_generated_queue_name")
        != "formalizer_pf_bv_copy_ready_retries"
    ]
    refreshed_agenda_rows = _dedupe_runtime_next_action_agenda_rows(
        [
            *retained_agenda_rows,
            *formalizer_pf_copy_ready_retry_next_action_rows,
        ]
    )
    _write_runtime_next_action_agenda_jsonl(agenda_path, refreshed_agenda_rows)
    manifest["n_runtime_coding_agent_capability_learning_rows"] = len(
        capability_learning_rows
    )
    manifest["n_runtime_coding_agent_component_gate_learning_rows"] = len(
        coding_component_gate_learning_rows
    )
    manifest["n_runtime_formalizer_component_gate_learning_rows"] = len(
        component_gate_learning_rows
    )
    manifest["n_runtime_formalizer_pseudo_formal_packet_component_gate_learning_rows"] = len(
        formalizer_pseudo_formal_packet_learning_rows
    )
    manifest[
        "n_runtime_formalizer_pseudo_formal_packet_copy_ready_retry_next_action_items"
    ] = len(formalizer_pf_copy_ready_retry_next_action_rows)
    manifest["proof_bank_runtime_memory_summary"] = (
        _formalizer_proof_bank_runtime_memory_summary(
            context={
                "runtime_learning_memory": {
                    "artifact_kind": "RuntimeLearningMemoryContext",
                    "rows": refreshed_rows,
                    "counts": {
                        "rows_loaded": len(refreshed_rows),
                        "source": "runtime_capability_manifest_refresh",
                    },
                    "retention_policy": "runtime_capability_manifest_refresh",
                }
            },
            proof_bank_obligation_catalog=[],
            theorem_goals=[],
            memory_kernel_verified_proof_obligation_ids=(),
            memory_prioritized_proof_obligation_ids=(),
        )
    )
    manifest["n_runtime_pseudo_formal_block_verifier_component_gate_learning_rows"] = len(
        pseudo_formal_component_gate_learning_rows
    )
    manifest["n_runtime_learning_rows"] = len(refreshed_rows)
    manifest["n_runtime_next_action_items"] = len(refreshed_agenda_rows)


def _apply_research_agent_runtime_capability_eval_preset(
    args: argparse.Namespace,
) -> None:
    """Populate strict live capability-eval defaults without weakening gates."""

    preset = str(getattr(args, "capability_eval_preset", "") or "").strip()
    if preset in {"", "none"}:
        return
    if preset not in {"minimal-live", "full-live"}:
        raise ValueError(f"unsupported capability eval preset: {preset}")

    if str(getattr(args, "provider", "") or "") not in {"anthropic", "openai"}:
        args.provider = _default_live_generator_provider()
    for field_name in (
        "architect_coordinator_provider",
        "simulation_engineer_provider",
        "algorithm_engineer_provider",
        "formalizer_provider",
        "critic_evaluator_provider",
    ):
        if str(getattr(args, field_name, "") or "") in {"", "none", "static"}:
            setattr(args, field_name, "same")

    if not bool(getattr(args, "local_lean", False)) and not bool(
        getattr(args, "real_lean", False)
    ):
        args.local_lean = True
    lean_project = str(getattr(args, "lean_project", "") or "").strip()
    if not lean_project:
        for default_lean_project in (
            _capability_eval_default_lean_project_candidates()
        ):
            if _is_lake_project(default_lean_project):
                args.lean_project = str(default_lean_project)
                lean_project = str(default_lean_project)
                break

    for field_name in (
        "formalizer_candidate_local_lean",
        "theorem_closure_proofengineer_bridge",
        "theorem_closure_proofengineer_local_lean",
        "source_semantic_proofengineer_bridge",
        "source_semantic_proofengineer_local_lean",
        "source_theorem_promotion_proofengineer_bridge",
        "source_theorem_promotion_proofengineer_local_lean",
        "source_theorem_formal_environment_proofengineer_bridge",
        "source_theorem_formal_environment_proofengineer_signature_probes",
        "source_theorem_formal_environment_proofengineer_execute_proof_body",
        "source_theorem_formal_environment_proofengineer_proof_body_local_lean",
        "source_theorem_proof_body_adapter_proofengineer_bridge",
        "source_theorem_proof_body_adapter_proofengineer_local_lean",
        "source_to_bridge_premise_derivation_proofengineer_bridge",
        "source_to_bridge_premise_derivation_proofengineer_local_lean",
        "source_theorem_exact_semantic_definition_source_lookup",
        "source_theorem_exact_semantic_definition_proofengineer_bridge",
        "source_theorem_exact_semantic_definition_lean_repair_executor",
        "source_theorem_exact_semantic_definition_lean_repair_executor_local_lean",
        "source_theorem_exact_semantic_definition_lean_environment_repair_executor",
        "source_theorem_exact_semantic_definition_closure_review",
        "source_theorem_exact_semantic_definition_candidate_synthesis",
        "source_theorem_exact_semantic_definition_candidate_synthesis_local_lean",
    ):
        setattr(args, field_name, True)

    lean_project_fields = (
        "formalizer_candidate_lean_project",
        "theorem_closure_proofengineer_lean_project",
        "source_semantic_proofengineer_lean_project",
        "source_theorem_proof_body_adapter_proofengineer_lean_project",
        "source_to_bridge_premise_derivation_proofengineer_lean_project",
        "source_theorem_formal_environment_proofengineer_lean_project",
        "source_theorem_promotion_proofengineer_lean_project",
        "source_theorem_exact_semantic_definition_lean_repair_executor_lean_project",
        "source_theorem_exact_semantic_definition_candidate_synthesis_lean_project",
    )
    if lean_project:
        for field_name in lean_project_fields:
            if not str(getattr(args, field_name, "") or "").strip():
                setattr(args, field_name, lean_project)

    roots = list(
        getattr(args, "source_theorem_exact_semantic_definition_source_root", [])
        or []
    )
    default_source_root = Path("legacy_sources/ai_statistician")
    if not roots and default_source_root.exists():
        roots.append(str(default_source_root))
    args.source_theorem_exact_semantic_definition_source_root = roots
    if preset == "full-live":
        args.formalizer_candidate_lean_lsp_mcp = True
        args.formalization_gap_planner_live_route_planner = True
        if (
            int(
                getattr(
                    args,
                    "algorithm_engineer_generated_code_repair_yield_after_attempts",
                    0,
                )
                or 0
            )
            <= 0
        ):
            args.algorithm_engineer_generated_code_repair_yield_after_attempts = 1
        if (
            int(
                getattr(
                    args,
                    "simulation_evaluator_generated_code_repair_yield_after_attempts",
                    0,
                )
                or 0
            )
            <= 0
        ):
            args.simulation_evaluator_generated_code_repair_yield_after_attempts = 1
        if (
            int(
                getattr(
                    args,
                    "formalizer_lean_candidate_repair_yield_to_gap_planner_after_attempts",
                    0,
                )
                or 0
            )
            <= 0
        ):
            args.formalizer_lean_candidate_repair_yield_to_gap_planner_after_attempts = 1
        if (
            int(
                getattr(
                    args,
                    "formalization_gap_planner_live_max_handoffs",
                    1,
                )
                or 0
            )
            <= 0
        ):
            args.formalization_gap_planner_live_max_handoffs = 1
        if (
            int(
                getattr(
                    args,
                    "formalization_gap_planner_live_max_route_requests_per_handoff",
                    1,
                )
                or 0
            )
            <= 0
        ):
            args.formalization_gap_planner_live_max_route_requests_per_handoff = 1
        if (
            float(
                getattr(
                    args,
                    "formalization_gap_planner_live_timeout_seconds",
                    DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
                )
                or 0
            )
            <= 0
        ):
            args.formalization_gap_planner_live_timeout_seconds = (
                DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS
            )
        if str(
            getattr(args, "formalization_gap_planner_live_provider", "same")
            or "same"
        ) in {"", "none", "static"}:
            args.formalization_gap_planner_live_provider = "same"
        args.run_coding_agent_generated_code_repair_eval = True
        args.run_formalizer_lean_candidate_repair_eval = True
        args.source_theorem_exact_semantic_definition_authoring_worker = True
        authoring_provider = str(
            getattr(
                args,
                "source_theorem_exact_semantic_definition_authoring_worker_provider",
                "none",
            )
            or "none"
        )
        if authoring_provider in {"", "none", "static"}:
            args.source_theorem_exact_semantic_definition_authoring_worker_provider = (
                args.provider
            )
        args.source_theorem_exact_semantic_definition_authoring_worker_allow_external_export = True
        args.source_theorem_exact_semantic_definition_authoring_worker_external_export_mode = (
            "full"
        )
        if str(
            getattr(args, "coding_agent_repair_eval_provider", "same") or "same"
        ) in {"", "none", "static"}:
            args.coding_agent_repair_eval_provider = "same"
        if str(
            getattr(args, "formalizer_repair_eval_provider", "same") or "same"
        ) in {"", "none", "static"}:
            args.formalizer_repair_eval_provider = "same"
        args.run_formalizer_pseudo_formal_packet_eval = True
        if str(
            getattr(args, "formalizer_pseudo_formal_packet_eval_provider", "same")
            or "same"
        ) in {"", "none", "static"}:
            args.formalizer_pseudo_formal_packet_eval_provider = "same"
        args.run_pseudo_formal_block_verifier_eval = True
        if str(
            getattr(args, "pseudo_formal_block_verifier_eval_provider", "same")
            or "same"
        ) in {"", "none", "static"}:
            args.pseudo_formal_block_verifier_eval_provider = "same"
        if lean_project and not str(
            getattr(args, "formalizer_repair_eval_lean_project", "") or ""
        ).strip():
            args.formalizer_repair_eval_lean_project = lean_project


def _apply_research_agent_runtime_live_lean_defaults(
    args: argparse.Namespace,
) -> None:
    """Attach the vendored Lake project to live Formalizer/ProofEngineer checks.

    This is intentionally narrower than the capability-eval preset: it does not
    enable registered proof-bank local Lean gates or broad source-theorem proof
    bridges. It prevents live Formalizer/ProofEngineer runs from stalling before
    local diagnostics, and it keeps source-to-bridge premise work orders from
    being dropped after the Formalizer emits them.
    """

    if not _research_agent_runtime_formalizer_resolves_to_live_provider(args):
        return
    lean_project = str(getattr(args, "lean_project", "") or "").strip()
    if not lean_project:
        for default_lean_project in (
            _capability_eval_default_lean_project_candidates()
        ):
            if _is_lake_project(default_lean_project):
                lean_project = str(default_lean_project)
                args.lean_project = lean_project
                break
    if not lean_project:
        return
    if not str(getattr(args, "formalizer_candidate_lean_project", "") or "").strip():
        args.formalizer_candidate_lean_project = lean_project
    if not bool(getattr(args, "formalizer_candidate_lean_lsp_mcp", False)):
        args.formalizer_candidate_local_lean = True
    if not str(
        getattr(
            args,
            "source_to_bridge_premise_derivation_proofengineer_lean_project",
            "",
        )
        or ""
    ).strip():
        args.source_to_bridge_premise_derivation_proofengineer_lean_project = (
            lean_project
        )
    args.source_to_bridge_premise_derivation_proofengineer_bridge = True
    args.source_to_bridge_premise_derivation_proofengineer_local_lean = True


def _research_agent_runtime_formalizer_resolves_to_live_provider(
    args: argparse.Namespace,
) -> bool:
    configured_provider = str(
        getattr(args, "formalizer_provider", "same") or "same"
    )
    main_provider = str(getattr(args, "provider", "") or "")
    resolved_provider = (
        main_provider if configured_provider == "same" else configured_provider
    )
    return resolved_provider in {"anthropic", "openai"}


def _effective_resume_through_architect(
    args: argparse.Namespace,
    *,
    architect_coordinator_configured: bool,
) -> bool:
    explicit = getattr(args, "resume_through_architect", None)
    if explicit is not None:
        return bool(explicit)
    return (
        bool(getattr(args, "capability_eval", False))
        and bool(str(getattr(args, "resume_runtime_manifest", "") or "").strip())
        and bool(architect_coordinator_configured)
    )


def _research_agent_runtime_static_subsystem_config_errors(
    args: argparse.Namespace,
) -> list[str]:
    errors: list[str] = []
    subsystem_static_files = (
        (
            "architect_coordinator_provider",
            "architect_static_response_file",
            "ArchitectCoordinator",
            "--architect-static-response-file",
        ),
        (
            "simulation_engineer_provider",
            "simulation_static_response_file",
            "SimulationEngineer",
            "--simulation-static-response-file",
        ),
        (
            "algorithm_engineer_provider",
            "algorithm_static_response_file",
            "AlgorithmEngineer",
            "--algorithm-static-response-file",
        ),
        (
            "formalizer_provider",
            "formalizer_static_response_file",
            "Formalizer/ProofEngineer",
            "--formalizer-static-response-file",
        ),
        (
            "critic_evaluator_provider",
            "critic_static_response_file",
            "CriticEvaluator",
            "--critic-static-response-file",
        ),
    )
    main_provider = str(getattr(args, "provider", "") or "")
    for provider_field, static_file_field, subsystem, flag in subsystem_static_files:
        configured_provider = str(getattr(args, provider_field, "none") or "none")
        if configured_provider == "none":
            continue
        resolved_provider = (
            main_provider if configured_provider == "same" else configured_provider
        )
        if resolved_provider != "static":
            continue
        if str(getattr(args, static_file_field, "") or "").strip():
            continue
        errors.append(
            f"{subsystem} resolves to static via --{provider_field.replace('_', '-')}="
            f"{configured_provider} but {flag} was not supplied; set "
            f"--{provider_field.replace('_', '-')} none to intentionally disable "
            "that subsystem in a partial debug replay"
        )
    return errors


def _capability_eval_default_lean_project_candidates() -> tuple[Path, ...]:
    from .research_source_inventory import VENDORED_EMPIRICAL_PROCESS_ROOT

    project_root = Path(__file__).resolve().parents[1]
    relative_vendored_project = Path("legacy_sources/emperical_process_lean")
    repo_vendored_project = project_root / relative_vendored_project
    candidates = (
        relative_vendored_project,
        repo_vendored_project,
        VENDORED_EMPIRICAL_PROCESS_ROOT,
        Path.home() / "LeanProjects" / "LeanPractice",
    )
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return tuple(unique)


def _is_lake_project(path: Path) -> bool:
    return (
        path.exists()
        and path.is_dir()
        and (
            (path / "lakefile.lean").exists()
            or (path / "lakefile.toml").exists()
        )
    )


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
    component_eval_provider_fields = (
        (
            "run_coding_agent_generated_code_repair_eval",
            "coding_agent_repair_eval_provider",
            "coding_agent_repair_eval_existing_manifest",
            "coding-agent generated-code repair eval",
        ),
        (
            "run_formalizer_lean_candidate_repair_eval",
            "formalizer_repair_eval_provider",
            "formalizer_repair_eval_existing_manifest",
            "Formalizer Lean-candidate repair eval",
        ),
        (
            "run_formalizer_pseudo_formal_packet_eval",
            "formalizer_pseudo_formal_packet_eval_provider",
            "formalizer_pseudo_formal_packet_eval_existing_manifest",
            "Formalizer PF/BV packet eval",
        ),
        (
            "run_pseudo_formal_block_verifier_eval",
            "pseudo_formal_block_verifier_eval_provider",
            "pseudo_formal_block_verifier_eval_existing_manifest",
            "pseudo-formal BlockVerifier eval",
        ),
    )
    main_provider = str(getattr(args, "provider", "") or "")
    for (
        enabled_field,
        provider_field,
        existing_manifest_field,
        component_name,
    ) in component_eval_provider_fields:
        if not bool(getattr(args, enabled_field, False)):
            continue
        if str(getattr(args, existing_manifest_field, "") or "").strip():
            continue
        provider_choice = str(getattr(args, provider_field, "same") or "same")
        resolved_provider = (
            main_provider if provider_choice == "same" else provider_choice
        )
        if resolved_provider not in {"anthropic", "openai"}:
            errors.append(
                f"capability eval requires live {component_name}; "
                f"{provider_field}={provider_choice} resolves to "
                f"{resolved_provider or 'none'}"
            )
    if not (getattr(args, "local_lean", False) or getattr(args, "real_lean", False)):
        errors.append("capability eval requires --local-lean or --real-lean")
    if getattr(args, "proof_obligation_id", None):
        errors.append(
            "capability eval must not use --proof-obligation-id; manual proof filters are debug-only"
        )
    if str(getattr(args, "recommended_research_path", "") or "").strip():
        errors.append(
            "capability eval must not use --recommended-research-path; "
            "manual path overrides are controlled-smoke/debug-only and cannot "
            "stand in for live Architect path selection"
        )
    proofengineer_required_flags = (
        (
            "formalizer_candidate_local_lean",
            "--formalizer-candidate-local-lean",
        ),
        (
            "theorem_closure_proofengineer_bridge",
            "--theorem-closure-proofengineer-bridge",
        ),
        (
            "theorem_closure_proofengineer_local_lean",
            "--theorem-closure-proofengineer-local-lean",
        ),
        (
            "source_semantic_proofengineer_bridge",
            "--source-semantic-proofengineer-bridge",
        ),
        (
            "source_semantic_proofengineer_local_lean",
            "--source-semantic-proofengineer-local-lean",
        ),
        (
            "source_theorem_promotion_proofengineer_bridge",
            "--source-theorem-promotion-proofengineer-bridge",
        ),
        (
            "source_theorem_promotion_proofengineer_local_lean",
            "--source-theorem-promotion-proofengineer-local-lean",
        ),
        (
            "source_theorem_formal_environment_proofengineer_bridge",
            "--source-theorem-formal-environment-proofengineer-bridge",
        ),
        (
            "source_theorem_formal_environment_proofengineer_signature_probes",
            "--source-theorem-formal-environment-proofengineer-signature-probes",
        ),
        (
            "source_theorem_formal_environment_proofengineer_execute_proof_body",
            "--source-theorem-formal-environment-proofengineer-execute-proof-body",
        ),
        (
            "source_theorem_formal_environment_proofengineer_proof_body_local_lean",
            "--source-theorem-formal-environment-proofengineer-proof-body-local-lean",
        ),
        (
            "source_theorem_proof_body_adapter_proofengineer_bridge",
            "--source-theorem-proof-body-adapter-proofengineer-bridge",
        ),
        (
            "source_theorem_proof_body_adapter_proofengineer_local_lean",
            "--source-theorem-proof-body-adapter-proofengineer-local-lean",
        ),
        (
            "source_to_bridge_premise_derivation_proofengineer_bridge",
            "--source-to-bridge-premise-derivation-proofengineer-bridge",
        ),
        (
            "source_to_bridge_premise_derivation_proofengineer_local_lean",
            "--source-to-bridge-premise-derivation-proofengineer-local-lean",
        ),
        (
            "source_theorem_exact_semantic_definition_source_lookup",
            "--source-theorem-exact-semantic-definition-source-lookup",
        ),
        (
            "source_theorem_exact_semantic_definition_proofengineer_bridge",
            "--source-theorem-exact-semantic-definition-proofengineer-bridge",
        ),
        (
            "source_theorem_exact_semantic_definition_lean_repair_executor",
            "--source-theorem-exact-semantic-definition-lean-repair-executor",
        ),
        (
            "source_theorem_exact_semantic_definition_lean_repair_executor_local_lean",
            "--source-theorem-exact-semantic-definition-lean-repair-executor-local-lean",
        ),
        (
            "source_theorem_exact_semantic_definition_lean_environment_repair_executor",
            "--source-theorem-exact-semantic-definition-lean-environment-repair-executor",
        ),
        (
            "source_theorem_exact_semantic_definition_closure_review",
            "--source-theorem-exact-semantic-definition-closure-review",
        ),
        (
            "source_theorem_exact_semantic_definition_candidate_synthesis",
            "--source-theorem-exact-semantic-definition-candidate-synthesis",
        ),
        (
            "source_theorem_exact_semantic_definition_candidate_synthesis_local_lean",
            "--source-theorem-exact-semantic-definition-candidate-synthesis-local-lean",
        ),
    )
    for field_name, flag in proofengineer_required_flags:
        if not bool(getattr(args, field_name, False)):
            errors.append(
                "capability eval requires the internal ProofEngineer proof path; "
                f"missing {flag}"
            )
    if (
        str(getattr(args, "capability_eval_preset", "") or "") == "full-live"
        and not bool(getattr(args, "formalizer_candidate_lean_lsp_mcp", False))
    ):
        errors.append(
            "capability eval preset full-live requires the live Lean LSP/MCP "
            "proof-state feedback path; missing "
            "--formalizer-candidate-lean-lsp-mcp"
        )
    if str(getattr(args, "capability_eval_preset", "") or "") == "full-live":
        for enabled_field, _, _, component_name in component_eval_provider_fields:
            if not bool(getattr(args, enabled_field, False)):
                errors.append(
                    "capability eval preset full-live requires attached live "
                    f"{component_name}; missing --{enabled_field.replace('_', '-')}"
                )
        if not bool(
            getattr(args, "formalization_gap_planner_live_route_planner", False)
        ):
            errors.append(
                "capability eval preset full-live requires the integrated live "
                "FormalizationGapPlanner route-planner feedback path; missing "
                "--formalization-gap-planner-live-route-planner"
            )
        route_provider_choice = str(
            getattr(args, "formalization_gap_planner_live_provider", "same")
            or "same"
        )
        route_provider = (
            main_provider if route_provider_choice == "same" else route_provider_choice
        )
        if route_provider not in {"anthropic", "openai"}:
            errors.append(
                "capability eval preset full-live requires a live "
                "FormalizationGapPlanner route-planner provider; "
                "formalization_gap_planner_live_provider="
                f"{route_provider_choice} resolves to {route_provider or 'none'}"
            )
        if (
            int(
                getattr(
                    args,
                    "formalization_gap_planner_live_max_handoffs",
                    0,
                )
                or 0
            )
            <= 0
        ):
            errors.append(
                "capability eval preset full-live requires "
                "--formalization-gap-planner-live-max-handoffs > 0"
            )
        if (
            int(
                getattr(
                    args,
                    "algorithm_engineer_generated_code_repair_yield_after_attempts",
                    0,
                )
                or 0
            )
            <= 0
        ):
            errors.append(
                "capability eval preset full-live requires bounded "
                "AlgorithmEngineer generated-code repair scheduling; set "
                "--algorithm-engineer-generated-code-repair-yield-after-attempts > 0"
            )
        if (
            int(
                getattr(
                    args,
                    "simulation_evaluator_generated_code_repair_yield_after_attempts",
                    0,
                )
                or 0
            )
            <= 0
        ):
            errors.append(
                "capability eval preset full-live requires bounded "
                "SimulationEvaluator generated-simulation repair scheduling; set "
                "--simulation-evaluator-generated-code-repair-yield-after-attempts > 0"
            )
        if (
            int(
                getattr(
                    args,
                    "formalizer_lean_candidate_repair_yield_to_gap_planner_after_attempts",
                    0,
                )
                or 0
            )
            <= 0
        ):
            errors.append(
                "capability eval preset full-live requires bounded "
                "Formalizer/ProofEngineer Lean-candidate repair scheduling; set "
                "--formalizer-lean-candidate-repair-yield-to-gap-planner-after-attempts > 0"
            )
        if (
            int(
                getattr(
                    args,
                    "formalization_gap_planner_live_max_route_requests_per_handoff",
                    0,
                )
                or 0
            )
            <= 0
        ):
            errors.append(
                "capability eval preset full-live requires bounded live "
                "FormalizationGapPlanner route-planner fanout; set "
                "--formalization-gap-planner-live-max-route-requests-per-handoff > 0"
            )
        if (
            float(
                getattr(
                    args,
                    "formalization_gap_planner_live_timeout_seconds",
                    0.0,
                )
                or 0.0
            )
            <= 0.0
        ):
            errors.append(
                "capability eval preset full-live requires "
                "--formalization-gap-planner-live-timeout-seconds > 0"
            )
    if (
        bool(getattr(args, "formalizer_candidate_local_lean", False))
        or bool(getattr(args, "formalizer_candidate_lean_lsp_mcp", False))
    ) and not (
        str(getattr(args, "formalizer_candidate_lean_project", "") or "").strip()
        or str(getattr(args, "lean_project", "") or "").strip()
    ):
        errors.append(
            "capability eval with --formalizer-candidate-local-lean requires "
            "--formalizer-candidate-lean-project or --lean-project so Mathlib/"
            "StatInference imports are available to the local Lean checker"
        )
    if not (
        getattr(args, "source_theorem_exact_semantic_definition_source_root", [])
        or []
    ):
        errors.append(
            "capability eval requires at least one "
            "--source-theorem-exact-semantic-definition-source-root for internal "
            "exact-semantic lookup"
        )
    return errors


def _research_agent_runtime_audit(args: argparse.Namespace) -> int:
    post_runtime_authoring_manifest = str(
        getattr(
            args,
            "post_runtime_exact_semantic_definition_authoring_worker_manifest",
            "",
        )
        or ""
    ).strip()
    post_runtime_materializer_manifest = str(
        getattr(
            args,
            "post_runtime_exact_semantic_definition_authoring_candidate_materializer_manifest",
            "",
        )
        or ""
    ).strip()
    post_runtime_lean_repair_manifest = str(
        getattr(
            args,
            "post_runtime_exact_semantic_definition_materialized_lean_repair_executor_manifest",
            "",
        )
        or ""
    ).strip()
    payload = audit_research_agent_runtime(
        Path(args.runtime_dir),
        Path(args.out),
        post_runtime_exact_semantic_definition_authoring_worker_manifest=(
            Path(post_runtime_authoring_manifest)
            if post_runtime_authoring_manifest
            else None
        ),
        post_runtime_exact_semantic_definition_authoring_candidate_materializer_manifest=(
            Path(post_runtime_materializer_manifest)
            if post_runtime_materializer_manifest
            else None
        ),
        post_runtime_exact_semantic_definition_materialized_lean_repair_executor_manifest=(
            Path(post_runtime_lean_repair_manifest)
            if post_runtime_lean_repair_manifest
            else None
        ),
    )
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


def _algorithm_engineer_generated_code_repair_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    try:
        manifest = run_algorithm_engineer_generated_code_repair_eval(
            question_file=Path(args.question_file),
            question_id=args.question_id,
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            static_response_file=(
                Path(args.static_response_file)
                if args.static_response_file
                else None
            ),
            llm_timeout_seconds=args.llm_timeout_seconds,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            n_runs=args.runs,
            seed=args.seed,
            target_coverage=args.target_coverage,
            max_repair_attempts=args.max_repair_attempts,
        )
    except Exception as exc:
        manifest = write_algorithm_engineer_generated_code_repair_eval_failure_manifest(
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            question_id=args.question_id,
            exc=exc,
        )
        print("\nAI Statistician AlgorithmEngineer generated-code repair eval failed")
        print("=" * 72)
        print(f"- {exc}")
        print(f"manifest={manifest['artifacts']['manifest_json']}")
        return 1
    print("\nAI Statistician AlgorithmEngineer Generated-Code Repair Eval")
    print("=" * 72)
    print(f"provider={manifest['provider_name']} model={manifest['model']}")
    print(f"live_generator={manifest['live_generator']}")
    print(f"result_status={manifest['result_status']}")
    print(
        "generated_code_executed="
        f"{manifest['n_generated_code_sandbox_executed']} "
        "passed="
        f"{manifest['n_generated_code_sandbox_passed']} "
        "metric_gate_failed="
        f"{manifest['n_generated_code_sandbox_metric_gate_failed']}"
    )
    print(
        "fail_then_pass_repair_sequences="
        f"{manifest['n_generated_code_sandbox_failed_then_passed_repair_sequences']}"
    )
    fixture_plumbing_ok = bool(
        manifest["static_or_fixture_only"] and manifest["sandbox_clean_after_repair"]
    )
    print(f"fixture_plumbing_ok={fixture_plumbing_ok}")
    print(f"capability_evidence_ok={manifest['capability_evidence_ok']}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    print(f"manifest={manifest['artifacts']['manifest_json']}")
    if manifest["capability_evidence_ok"]:
        return 0
    if args.allow_fixture_success and fixture_plumbing_ok:
        return 0
    return 1


def _simulation_engineer_generated_code_repair_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    try:
        manifest = run_simulation_engineer_generated_code_repair_eval(
            question_file=Path(args.question_file),
            question_id=args.question_id,
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            static_response_file=(
                Path(args.static_response_file)
                if args.static_response_file
                else None
            ),
            llm_timeout_seconds=args.llm_timeout_seconds,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            n_runs=args.runs,
            seed=args.seed,
            target_coverage=args.target_coverage,
            max_repair_attempts=args.max_repair_attempts,
        )
    except Exception as exc:
        manifest = write_simulation_engineer_generated_code_repair_eval_failure_manifest(
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            question_id=args.question_id,
            exc=exc,
        )
        print("\nAI Statistician SimulationEngineer generated-code repair eval failed")
        print("=" * 72)
        print(f"- {exc}")
        print(f"manifest={manifest['artifacts']['manifest_json']}")
        return 1
    print("\nAI Statistician SimulationEngineer Generated-Code Repair Eval")
    print("=" * 72)
    print(f"provider={manifest['provider_name']} model={manifest['model']}")
    print(f"live_generator={manifest['live_generator']}")
    print(f"result_status={manifest['result_status']}")
    print(
        "generated_simulation_executed="
        f"{manifest['n_generated_simulation_sandbox_executed']} "
        "passed="
        f"{manifest['n_generated_simulation_sandbox_passed']} "
        "metric_gate_failed="
        f"{manifest['n_generated_simulation_sandbox_metric_gate_failed']}"
    )
    print(
        "fail_then_pass_repair_sequences="
        f"{manifest['n_generated_simulation_sandbox_failed_then_passed_repair_sequences']}"
    )
    fixture_plumbing_ok = bool(
        manifest["static_or_fixture_only"] and manifest["sandbox_clean_after_repair"]
    )
    print(f"fixture_plumbing_ok={fixture_plumbing_ok}")
    print(f"capability_evidence_ok={manifest['capability_evidence_ok']}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    print(f"manifest={manifest['artifacts']['manifest_json']}")
    if manifest["capability_evidence_ok"]:
        return 0
    if args.allow_fixture_success and fixture_plumbing_ok:
        return 0
    return 1


def _coding_agent_generated_code_repair_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    manifest = run_coding_agent_generated_code_repair_eval(
        question_file=Path(args.question_file),
        question_id=args.question_id,
        out_dir=Path(args.out),
        provider_name=args.provider,
        model=args.llm_model,
        algorithm_static_response_file=(
            Path(args.algorithm_static_response_file)
            if args.algorithm_static_response_file
            else None
        ),
        simulation_static_response_file=(
            Path(args.simulation_static_response_file)
            if args.simulation_static_response_file
            else None
        ),
        llm_timeout_seconds=args.llm_timeout_seconds,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        n_runs=args.runs,
        seed=args.seed,
        target_coverage=args.target_coverage,
        max_repair_attempts=args.max_repair_attempts,
    )
    print("\nAI Statistician Coding-Agent Generated-Code Repair Eval")
    print("=" * 72)
    print(f"provider={manifest['provider_name']} model={manifest['model']}")
    print(f"live_generator={manifest['live_generator']}")
    print(
        "algorithm_ok="
        f"{manifest['algorithm_capability_evidence_ok']} "
        "simulation_ok="
        f"{manifest['simulation_capability_evidence_ok']}"
    )
    print(
        "repair_sequences="
        f"algorithm:{manifest['algorithm_repair_sequences']} "
        f"simulation:{manifest['simulation_repair_sequences']}"
    )
    print(f"fixture_plumbing_ok={manifest['fixture_plumbing_ok']}")
    print(f"capability_evidence_ok={manifest['capability_evidence_ok']}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    print(f"manifest={manifest['artifacts']['manifest_json']}")
    if manifest["capability_evidence_ok"]:
        return 0
    if args.allow_fixture_success and manifest["fixture_plumbing_ok"]:
        return 0
    return 1


def _formalizer_lean_candidate_repair_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    lean_project = (
        Path(args.lean_project)
        if getattr(args, "lean_project", "")
        else None
    )
    try:
        manifest = run_formalizer_lean_candidate_repair_eval(
            question_file=Path(args.question_file),
            question_id=args.question_id,
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            static_response_file=(
                Path(args.static_response_file)
                if args.static_response_file
                else None
            ),
            llm_timeout_seconds=args.llm_timeout_seconds,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            lean_project=lean_project,
            lean_timeout=args.lean_timeout,
            lean_lsp_mcp_proof_state_feedback=bool(
                getattr(args, "lean_lsp_mcp_proof_state_feedback", False)
            ),
            max_repair_attempts=args.max_repair_attempts,
        )
    except Exception as exc:
        manifest = write_formalizer_lean_candidate_repair_eval_failure_manifest(
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            question_id=args.question_id,
            exc=exc,
        )
        print("\nAI Statistician Formalizer Lean-Candidate Repair Eval failed")
        print("=" * 72)
        print(f"- {exc}")
        print(f"manifest={manifest['artifacts']['manifest_json']}")
        return 1
    print("\nAI Statistician Formalizer Lean-Candidate Repair Eval")
    print("=" * 72)
    print(f"provider={manifest['provider_name']} model={manifest['model']}")
    print(f"live_generator={manifest['live_generator']}")
    print(f"result_status={manifest['result_status']}")
    print(
        "lean_candidates="
        f"{manifest['n_formalizer_lean_candidate_sources']} "
        "checked="
        f"{manifest['n_formalizer_lean_candidate_local_lean_checked']} "
        "compiled="
        f"{manifest['n_formalizer_lean_candidate_local_lean_compiled']}"
    )
    print(
        "fail_then_pass_repair_sequences="
        f"{manifest['n_formalizer_lean_candidate_failed_then_passed_repair_sequences']}"
    )
    fixture_plumbing_ok = bool(
        manifest["static_or_fixture_only"]
        and manifest["candidate_kernel_verified"]
        and manifest["repair_loop_observed"]
    )
    print(f"fixture_plumbing_ok={fixture_plumbing_ok}")
    print(f"capability_evidence_ok={manifest['capability_evidence_ok']}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    print(f"manifest={manifest['artifacts']['manifest_json']}")
    if manifest["capability_evidence_ok"]:
        return 0
    if args.allow_fixture_success and fixture_plumbing_ok:
        return 0
    return 1


def _formalizer_pseudo_formal_packet_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    try:
        manifest = run_formalizer_pseudo_formal_packet_eval(
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            static_response_file=(
                Path(args.static_response_file)
                if args.static_response_file
                else None
            ),
            llm_timeout_seconds=args.llm_timeout_seconds,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            max_repair_attempts=args.max_repair_attempts,
        )
    except Exception as exc:
        manifest = write_formalizer_pseudo_formal_packet_eval_failure_manifest(
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            exc=exc,
        )
        print("\nAI Statistician Formalizer PF/BV Packet Eval failed")
        print("=" * 72)
        print(f"- {exc}")
        print(f"manifest={manifest['artifacts']['manifest_json']}")
        return 1
    print("\nAI Statistician Formalizer PF/BV Packet Eval")
    print("=" * 72)
    print(f"provider={manifest['provider_name']} model={manifest['model']}")
    print(f"live_generator={manifest['live_generator']}")
    print(f"result_status={manifest['result_status']}")
    print(
        "pf_packets="
        f"{manifest['n_pseudo_formal_packets']} "
        "work_order_rows="
        f"{manifest['n_pseudo_formal_work_order_rows']} "
        "routable_rows="
        f"{manifest['n_pseudo_formal_routable_work_order_rows']}"
    )
    print(
        "target_lanes="
        f"{','.join(manifest['pseudo_formal_routable_target_lanes'])}"
    )
    print(f"fixture_plumbing_ok={manifest['fixture_plumbing_ok']}")
    print(f"capability_evidence_ok={manifest['capability_evidence_ok']}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    print(f"manifest={manifest['artifacts']['manifest_json']}")
    if manifest["capability_evidence_ok"]:
        return 0
    if args.allow_fixture_success and manifest["fixture_plumbing_ok"]:
        return 0
    return 1


def _architect_research_path_policy_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    try:
        manifest = run_architect_research_path_policy_eval(
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            static_response_file=(
                Path(args.static_response_file)
                if args.static_response_file
                else None
            ),
            llm_timeout_seconds=args.llm_timeout_seconds,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
    except Exception as exc:
        manifest = write_architect_research_path_policy_eval_failure_manifest(
            out_dir=Path(args.out),
            provider_name=args.provider,
            model=args.llm_model,
            exc=exc,
        )
        print("\nAI Statistician Architect Research-Path Policy Eval failed")
        print("=" * 72)
        print(f"- {exc}")
        print(f"manifest={manifest['artifacts']['manifest_json']}")
        return 1
    print("\nAI Statistician Architect Research-Path Policy Eval")
    print("=" * 72)
    print(f"provider={manifest['provider_name']} model={manifest['model']}")
    print(f"live_generator={manifest['live_generator']}")
    print(f"cases_ok={manifest['n_cases_ok']}/{manifest['n_cases']}")
    print(
        "long_horizon_fields="
        f"problem_analysis:{manifest['n_with_problem_analysis']} "
        f"knowledge_bank:{manifest['n_with_stat_knowledge_bank_plan']} "
        f"fair_comparison:{manifest['n_with_literature_fair_comparison_plan']}"
    )
    fixture_plumbing_ok = bool(
        manifest["static_or_fixture_only"] and manifest["all_cases_ok"]
    )
    print(f"fixture_plumbing_ok={fixture_plumbing_ok}")
    print(f"capability_evidence_ok={manifest['capability_evidence_ok']}")
    print(f"proof_evidence_status={manifest['proof_evidence_status']}")
    print(f"manifest={manifest['artifacts']['manifest_json']}")
    if manifest["capability_evidence_ok"]:
        return 0
    if args.allow_fixture_success and fixture_plumbing_ok:
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Statistician production core")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="run estimator + formal proof + simulation loop")
    demo.add_argument("--question", action="append", choices=sorted(QUESTIONS), help="run one built-in question; repeatable")
    demo.add_argument("--question-file", help="run one or more external questions from JSON")
    demo.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    demo.add_argument("--llm-theory", action="store_true", help="allow a generator backend to classify supported estimator/DGP families during intake")
    demo.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    demo.add_argument("--llm-provider", choices=GENERATOR_PROVIDER_CHOICES, default=_default_live_generator_provider())
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
    eval_cmd.add_argument("--llm-provider", choices=GENERATOR_PROVIDER_CHOICES, default=_default_live_generator_provider())
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

    source_theorem_semantic_primitive_proofengineer_bridge = sub.add_parser(
        "source-theorem-semantic-primitive-proofengineer-bridge",
        help=(
            "run the ProofEngineer bridge from AgentRuntime source-theorem "
            "semantic primitive work orders to runtime learning memory"
        ),
    )
    semantic_bridge_source = (
        source_theorem_semantic_primitive_proofengineer_bridge.add_mutually_exclusive_group(
            required=True
        )
    )
    semantic_bridge_source.add_argument(
        "--runtime-dir",
        help=(
            "research-agent-runtime output directory containing "
            "research_agent_runtime_manifest.json"
        ),
    )
    semantic_bridge_source.add_argument(
        "--queue-jsonl",
        help=(
            "runtime_source_theorem_semantic_primitive_work_orders.jsonl from "
            "research-agent-runtime"
        ),
    )
    semantic_bridge_source.add_argument(
        "--proof-body-executor-dir",
        help=(
            "exact-source theorem proof-body executor output directory; the bridge "
            "will materialize source semantic primitive work orders from its runtime "
            "learning rows"
        ),
    )
    source_theorem_semantic_primitive_proofengineer_bridge.add_argument(
        "--question-id",
        default="",
        help="optional question id to attach to exported runtime learning memory",
    )
    source_theorem_semantic_primitive_proofengineer_bridge.add_argument(
        "--out",
        default="runs/source_theorem_semantic_primitive_proofengineer_bridge",
        help="bridge output directory",
    )
    source_theorem_semantic_primitive_proofengineer_bridge.add_argument(
        "--local-lean",
        action="store_true",
        help=(
            "run local lake env lean for registered semantic-bridge obligations; "
            "only successful rows become support evidence"
        ),
    )
    source_theorem_semantic_primitive_proofengineer_bridge.add_argument(
        "--lean-project",
        help="local Lake project used by --local-lean",
    )
    source_theorem_semantic_primitive_proofengineer_bridge.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each source-semantic local Lean check",
    )
    source_theorem_semantic_primitive_proofengineer_bridge.add_argument(
        "--proof-audit-manifest",
        default="",
        help=(
            "optional existing proof_audit_manifest.json to reuse instead of "
            "running a new local Lean audit"
        ),
    )
    source_theorem_semantic_primitive_proofengineer_bridge.set_defaults(
        func=_source_theorem_semantic_primitive_proofengineer_bridge
    )

    source_theorem_proof_body_adapter_proofengineer_bridge = sub.add_parser(
        "source-theorem-proof-body-adapter-proofengineer-bridge",
        help=(
            "consume AgentRuntime source-theorem proof-body adapter work orders "
            "and export adapter ProofEngineer feedback/runtime learning rows"
        ),
    )
    adapter_bridge_source = (
        source_theorem_proof_body_adapter_proofengineer_bridge.add_mutually_exclusive_group(
            required=True
        )
    )
    adapter_bridge_source.add_argument(
        "--runtime-dir",
        help=(
            "research-agent-runtime output directory containing "
            "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
        ),
    )
    adapter_bridge_source.add_argument(
        "--queue-jsonl",
        help=(
            "runtime_source_theorem_proof_body_adapter_work_orders.jsonl from "
            "research-agent-runtime"
        ),
    )
    source_theorem_proof_body_adapter_proofengineer_bridge.add_argument(
        "--question-id",
        default="",
        help="optional question id to attach to exported runtime learning memory",
    )
    source_theorem_proof_body_adapter_proofengineer_bridge.add_argument(
        "--out",
        default="runs/source_theorem_proof_body_adapter_proofengineer_bridge",
        help="bridge output directory",
    )
    source_theorem_proof_body_adapter_proofengineer_bridge.add_argument(
        "--local-lean",
        action="store_true",
        help=(
            "run local lake env lean on adapter candidates; only non-vacuous "
            "compiled adapters become adapter evidence"
        ),
    )
    source_theorem_proof_body_adapter_proofengineer_bridge.add_argument(
        "--lean-project",
        help="local Lake project used by --local-lean",
    )
    source_theorem_proof_body_adapter_proofengineer_bridge.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each adapter local Lean check",
    )
    source_theorem_proof_body_adapter_proofengineer_bridge.set_defaults(
        func=_source_theorem_proof_body_adapter_proofengineer_bridge
    )

    source_to_bridge_premise_derivation_proofengineer_bridge = sub.add_parser(
        "source-to-bridge-premise-derivation-proofengineer-bridge",
        help=(
            "consume source-to-bridge premise derivation work orders and export "
            "ProofEngineer feedback/runtime learning rows"
        ),
    )
    premise_bridge_source = (
        source_to_bridge_premise_derivation_proofengineer_bridge.add_mutually_exclusive_group(
            required=True
        )
    )
    premise_bridge_source.add_argument(
        "--runtime-dir",
        help=(
            "research-agent-runtime output directory containing "
            "runtime_source_to_bridge_premise_derivation_queue_jsonl"
        ),
    )
    premise_bridge_source.add_argument(
        "--adapter-bridge-dir",
        help=(
            "source-theorem-proof-body-adapter-proofengineer-bridge output "
            "directory containing a source-to-bridge premise derivation queue"
        ),
    )
    premise_bridge_source.add_argument(
        "--queue-jsonl",
        help="source_to_bridge_premise_derivation_queue.jsonl to consume directly",
    )
    source_to_bridge_premise_derivation_proofengineer_bridge.add_argument(
        "--question-id",
        default="",
        help="optional question id to attach to exported runtime learning memory",
    )
    source_to_bridge_premise_derivation_proofengineer_bridge.add_argument(
        "--out",
        default=(
            "runs/source_to_bridge_premise_derivation_proofengineer_bridge"
        ),
        help="bridge output directory",
    )
    source_to_bridge_premise_derivation_proofengineer_bridge.add_argument(
        "--local-lean",
        action="store_true",
        help=(
            "run local lake env lean on premise-derivation candidates; only "
            "non-vacuous compiled premise derivations become premise evidence"
        ),
    )
    source_to_bridge_premise_derivation_proofengineer_bridge.add_argument(
        "--lean-project",
        help="local Lake project used by --local-lean",
    )
    source_to_bridge_premise_derivation_proofengineer_bridge.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each premise-derivation local Lean check",
    )
    source_to_bridge_premise_derivation_proofengineer_bridge.set_defaults(
        func=_source_to_bridge_premise_derivation_proofengineer_bridge
    )

    source_theorem_formal_environment_proofengineer_bridge = sub.add_parser(
        "source-theorem-formal-environment-proofengineer-bridge",
        help=(
            "convert AgentRuntime source-theorem formal-environment work orders "
            "into ProofEngineer repair packets and runtime learning rows"
        ),
    )
    env_bridge_source = (
        source_theorem_formal_environment_proofengineer_bridge.add_mutually_exclusive_group(
            required=True
        )
    )
    env_bridge_source.add_argument(
        "--runtime-dir",
        help=(
            "research-agent-runtime output directory containing "
            "research_agent_runtime_manifest.json"
        ),
    )
    env_bridge_source.add_argument(
        "--queue-jsonl",
        help=(
            "runtime_source_theorem_formal_environment_work_orders.jsonl or "
            "formal-environment work orders emitted by the source-theorem promotion bridge"
        ),
    )
    source_theorem_formal_environment_proofengineer_bridge.add_argument(
        "--question-id",
        default="",
        help="optional question id to attach to exported runtime learning memory",
    )
    source_theorem_formal_environment_proofengineer_bridge.add_argument(
        "--run-signature-probes",
        action="store_true",
        help=(
            "materialize typecheck-only Lean signature probes from repair packets; "
            "these probes are diagnostics and not proof evidence"
        ),
    )
    source_theorem_formal_environment_proofengineer_bridge.add_argument(
        "--lean-project",
        default="",
        help="optional local Lake project used by --run-signature-probes",
    )
    source_theorem_formal_environment_proofengineer_bridge.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each signature-probe local Lean check",
    )
    source_theorem_formal_environment_proofengineer_bridge.add_argument(
        "--out",
        default="runs/source_theorem_formal_environment_proofengineer_bridge",
        help="bridge output directory",
    )
    source_theorem_formal_environment_proofengineer_bridge.set_defaults(
        func=_source_theorem_formal_environment_proofengineer_bridge
    )

    source_theorem_exact_semantic_definition_source_lookup = sub.add_parser(
        "source-theorem-exact-semantic-definition-source-lookup",
        help=(
            "search local Lean sources for exact semantic definitions requested by "
            "AgentRuntime exact-semantic work orders"
        ),
    )
    exact_definition_lookup_source = (
        source_theorem_exact_semantic_definition_source_lookup.add_mutually_exclusive_group(
            required=True
        )
    )
    exact_definition_lookup_source.add_argument(
        "--runtime-dir",
        help=(
            "research-agent-runtime output directory containing "
            "runtime_source_theorem_exact_semantic_definition_work_orders.jsonl"
        ),
    )
    exact_definition_lookup_source.add_argument(
        "--queue-jsonl",
        help=(
            "runtime_source_theorem_exact_semantic_definition_work_orders.jsonl "
            "from research-agent-runtime"
        ),
    )
    source_theorem_exact_semantic_definition_source_lookup.add_argument(
        "--source-root",
        action="append",
        default=[],
        help=(
            "Lean source root to search; repeat for Mathlib/StatInference/"
            "EmpiricalProcessLEAN checkouts"
        ),
    )
    source_theorem_exact_semantic_definition_source_lookup.add_argument(
        "--max-hits-per-work-order",
        type=int,
        default=8,
        help="maximum source text hits retained for each exact-semantic work order",
    )
    source_theorem_exact_semantic_definition_source_lookup.add_argument(
        "--out",
        default="runs/source_theorem_exact_semantic_definition_source_lookup",
        help="source lookup output directory",
    )
    source_theorem_exact_semantic_definition_source_lookup.set_defaults(
        func=_source_theorem_exact_semantic_definition_source_lookup
    )

    source_theorem_exact_semantic_definition_closure_review = sub.add_parser(
        "source-theorem-exact-semantic-definition-closure-review",
        help=(
            "review exact semantic-definition closure packets against a candidate "
            "Lean artifact and reject forbidden placeholder definitions"
        ),
    )
    exact_definition_review_source = (
        source_theorem_exact_semantic_definition_closure_review.add_mutually_exclusive_group(
            required=True
        )
    )
    exact_definition_review_source.add_argument(
        "--review-packets-jsonl",
        help=(
            "source_theorem_exact_semantic_definition_closure_review_packets.jsonl "
            "from exact semantic-definition source lookup"
        ),
    )
    exact_definition_review_source.add_argument(
        "--lookup-manifest",
        help=(
            "source_theorem_exact_semantic_definition_source_lookup_manifest.json "
            "listing definition_closure_review_packets_jsonl"
        ),
    )
    source_theorem_exact_semantic_definition_closure_review.add_argument(
        "--candidate-artifact",
        default="",
        help=(
            "exact source theorem Lean candidate artifact whose placeholder "
            "definitions should be statically reviewed"
        ),
    )
    source_theorem_exact_semantic_definition_closure_review.add_argument(
        "--out",
        default="runs/source_theorem_exact_semantic_definition_closure_review",
        help="closure review output directory",
    )
    source_theorem_exact_semantic_definition_closure_review.set_defaults(
        func=_source_theorem_exact_semantic_definition_closure_review
    )

    source_theorem_exact_semantic_definition_proofengineer_bridge = sub.add_parser(
        "source-theorem-exact-semantic-definition-proofengineer-bridge",
        help=(
            "turn exact semantic-definition review packets into ProofEngineer "
            "repair packets and runtime learning rows"
        ),
    )
    exact_definition_bridge_source = (
        source_theorem_exact_semantic_definition_proofengineer_bridge.add_mutually_exclusive_group(
            required=True
        )
    )
    exact_definition_bridge_source.add_argument(
        "--runtime-dir",
        help=(
            "research-agent-runtime output directory containing exact "
            "semantic-definition source lookup artifacts"
        ),
    )
    exact_definition_bridge_source.add_argument(
        "--lookup-manifest",
        help=(
            "source_theorem_exact_semantic_definition_source_lookup_manifest.json "
            "listing definition_closure_review_packets_jsonl"
        ),
    )
    exact_definition_bridge_source.add_argument(
        "--review-packets-jsonl",
        help=(
            "source_theorem_exact_semantic_definition_closure_review_packets.jsonl "
            "from exact semantic-definition source lookup"
        ),
    )
    source_theorem_exact_semantic_definition_proofengineer_bridge.add_argument(
        "--question-id",
        default="",
        help="optional question id to attach to exported runtime learning memory",
    )
    source_theorem_exact_semantic_definition_proofengineer_bridge.add_argument(
        "--out",
        default="runs/source_theorem_exact_semantic_definition_proofengineer_bridge",
        help="bridge output directory",
    )
    source_theorem_exact_semantic_definition_proofengineer_bridge.set_defaults(
        func=_source_theorem_exact_semantic_definition_proofengineer_bridge
    )

    source_theorem_exact_semantic_definition_lean_repair_executor = sub.add_parser(
        "source-theorem-exact-semantic-definition-lean-repair-executor",
        help=(
            "consume exact semantic-definition Lean repair tasks, resolve candidate "
            "source declarations, and optionally run local Lean diagnostics"
        ),
    )
    exact_definition_lean_repair_source = (
        source_theorem_exact_semantic_definition_lean_repair_executor.add_mutually_exclusive_group(
            required=True
        )
    )
    exact_definition_lean_repair_source.add_argument(
        "--runtime-dir",
        help="research-agent-runtime output directory listing Lean repair tasks",
    )
    exact_definition_lean_repair_source.add_argument(
        "--bridge-manifest",
        help=(
            "source_theorem_exact_semantic_definition_proofengineer_bridge_manifest.json "
            "listing lean_repair_tasks_jsonl"
        ),
    )
    exact_definition_lean_repair_source.add_argument(
        "--materializer-manifest",
        help=(
            "source_theorem_exact_semantic_definition_authoring_candidate_materializer_manifest.json "
            "listing materialized_lean_repair_tasks_jsonl"
        ),
    )
    exact_definition_lean_repair_source.add_argument(
        "--tasks-jsonl",
        help="source_theorem_exact_semantic_definition_lean_repair_tasks.jsonl",
    )
    source_theorem_exact_semantic_definition_lean_repair_executor.add_argument(
        "--source-root",
        action="append",
        default=[],
        help="Lean source root used to resolve candidate import declaration paths",
    )
    source_theorem_exact_semantic_definition_lean_repair_executor.add_argument(
        "--local-lean",
        action="store_true",
        help="run local Lean on resolved import-candidate source files",
    )
    source_theorem_exact_semantic_definition_lean_repair_executor.add_argument(
        "--lean-project",
        default="",
        help="optional local Lake project for --local-lean",
    )
    source_theorem_exact_semantic_definition_lean_repair_executor.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for local Lean diagnostics",
    )
    source_theorem_exact_semantic_definition_lean_repair_executor.add_argument(
        "--out",
        default="runs/source_theorem_exact_semantic_definition_lean_repair_executor",
        help="Lean repair executor output directory",
    )
    source_theorem_exact_semantic_definition_lean_repair_executor.set_defaults(
        func=_source_theorem_exact_semantic_definition_lean_repair_executor
    )

    source_theorem_exact_semantic_definition_authoring_worker = sub.add_parser(
        "source-theorem-exact-semantic-definition-authoring-worker",
        help=(
            "prepare or run generator-only authoring for exact semantic "
            "definitions requested by the Lean repair executor"
        ),
    )
    exact_definition_authoring_source = (
        source_theorem_exact_semantic_definition_authoring_worker.add_mutually_exclusive_group(
            required=True
        )
    )
    exact_definition_authoring_source.add_argument(
        "--runtime-dir",
        help="research-agent-runtime output directory listing authoring tasks",
    )
    exact_definition_authoring_source.add_argument(
        "--repair-executor-manifest",
        help=(
            "source_theorem_exact_semantic_definition_lean_repair_executor_manifest.json "
            "listing exact_semantic_definition_authoring_tasks_jsonl"
        ),
    )
    exact_definition_authoring_source.add_argument(
        "--authoring-tasks-jsonl",
        help="source_theorem_exact_semantic_definition_authoring_tasks.jsonl",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--provider",
        choices=("none",) + GENERATOR_PROVIDER_CHOICES,
        default="none",
        help=(
            "generator backend for authoring; default none writes prompt packets "
            "without calling an LLM"
        ),
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--dry-run",
        action="store_true",
        help="write prompt packets only even when --provider is set",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--allow-external-export",
        action="store_true",
        help=(
            "allow sending local proof/formalization authoring context to the "
            "external Anthropic/OpenAI provider; without this flag, external "
            "providers emit export-review packets instead of making API calls"
        ),
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--external-export-mode",
        choices=("full", "redacted"),
        default="full",
        help=(
            "prompt payload mode for external LLM authoring. redacted removes "
            "local source paths and Lean snippets from source_reference_hints "
            "while preserving counts and binder/semantic contracts"
        ),
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--external-export-approval-manifest",
        default="",
        help=(
            "optional JSON/JSONL approval manifest listing exact prompt/review "
            "packet ids or export payload fingerprints approved for external "
            "Anthropic/OpenAI authoring calls"
        ),
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--static-response-file",
        default="",
        help="JSON response to replay when --provider static is used",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--llm-model",
        default="",
        help="model name for the authoring worker; Anthropic defaults to Claude Sonnet 4.6",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--model-tier",
        choices=("haiku", "sonnet", "opus"),
        default="sonnet",
        help="Claude cost tier for authoring; default Sonnet because this is proof/formalization work",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
        help="maximum output tokens for live authoring calls",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="authoring worker generation temperature",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--max-repair-attempts",
        type=int,
        default=1,
        help="maximum local JSON validation repair retries for live authoring calls",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
        help="wall-clock timeout for each live authoring generator request",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--max-tasks",
        type=int,
        default=0,
        help="optional cap on authoring tasks for focused smokes",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--placeholder-symbol",
        action="append",
        default=[],
        help=(
            "only prepare/run authoring tasks for this placeholder symbol; may "
            "be repeated for focused ProofEngineer closure runs"
        ),
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--env-file",
        default=".env",
        help="dotenv file used for Anthropic/OpenAI API keys",
    )
    source_theorem_exact_semantic_definition_authoring_worker.add_argument(
        "--out",
        default="runs/source_theorem_exact_semantic_definition_authoring_worker",
        help="authoring worker output directory",
    )
    source_theorem_exact_semantic_definition_authoring_worker.set_defaults(
        func=_source_theorem_exact_semantic_definition_authoring_worker
    )

    source_theorem_exact_semantic_definition_authoring_candidate_materialize = (
        sub.add_parser(
            "source-theorem-exact-semantic-definition-authoring-candidate-materialize",
            help=(
                "materialize validated exact semantic-definition authoring "
                "candidate packets into definition-only Lean drafts and "
                "downstream Lean repair tasks"
            ),
        )
    )
    exact_definition_authoring_candidate_source = (
        source_theorem_exact_semantic_definition_authoring_candidate_materialize.add_mutually_exclusive_group(
            required=True
        )
    )
    exact_definition_authoring_candidate_source.add_argument(
        "--authoring-worker-manifest",
        help=(
            "source_theorem_exact_semantic_definition_authoring_worker_manifest.json "
            "listing authoring_candidate_packets_jsonl"
        ),
    )
    exact_definition_authoring_candidate_source.add_argument(
        "--candidate-packets-jsonl",
        help="source_theorem_exact_semantic_definition_authoring_candidate_packets.jsonl",
    )
    source_theorem_exact_semantic_definition_authoring_candidate_materialize.add_argument(
        "--max-candidates",
        type=int,
        default=0,
        help="optional cap on candidate packets for focused smokes",
    )
    source_theorem_exact_semantic_definition_authoring_candidate_materialize.add_argument(
        "--no-source-comments",
        action="store_true",
        help="omit authoring packet comments from generated definition-only Lean files",
    )
    source_theorem_exact_semantic_definition_authoring_candidate_materialize.add_argument(
        "--out",
        default=(
            "runs/"
            "source_theorem_exact_semantic_definition_authoring_candidate_materializer"
        ),
        help="authoring candidate materializer output directory",
    )
    source_theorem_exact_semantic_definition_authoring_candidate_materialize.set_defaults(
        func=_source_theorem_exact_semantic_definition_authoring_candidate_materialize
    )

    source_theorem_exact_semantic_definition_lean_environment_repair_executor = (
        sub.add_parser(
            "source-theorem-exact-semantic-definition-lean-environment-repair-executor",
            help=(
                "preflight exact semantic-definition Lean environment repair tasks "
                "by inspecting inferred Lake project dependency/cache readiness"
            ),
        )
    )
    exact_definition_environment_repair_source = (
        source_theorem_exact_semantic_definition_lean_environment_repair_executor.add_mutually_exclusive_group(
            required=True
        )
    )
    exact_definition_environment_repair_source.add_argument(
        "--runtime-dir",
        help="research-agent-runtime output directory listing environment repair tasks",
    )
    exact_definition_environment_repair_source.add_argument(
        "--repair-executor-manifest",
        help=(
            "source_theorem_exact_semantic_definition_lean_repair_executor_manifest.json "
            "listing lean_environment_repair_tasks_jsonl"
        ),
    )
    exact_definition_environment_repair_source.add_argument(
        "--environment-tasks-jsonl",
        help="source_theorem_exact_semantic_definition_lean_environment_repair_tasks.jsonl",
    )
    source_theorem_exact_semantic_definition_lean_environment_repair_executor.add_argument(
        "--out",
        default=(
            "runs/"
            "source_theorem_exact_semantic_definition_lean_environment_repair_executor"
        ),
        help="Lean environment repair preflight output directory",
    )
    source_theorem_exact_semantic_definition_lean_environment_repair_executor.set_defaults(
        func=_source_theorem_exact_semantic_definition_lean_environment_repair_executor
    )

    source_theorem_exact_semantic_definition_verifier_gate_executor = sub.add_parser(
        "source-theorem-exact-semantic-definition-verifier-gate-executor",
        help=(
            "execute verifier-gate work orders for LLM-approved, typechecked exact "
            "semantic-definition candidates before proof-body recheck"
        ),
    )
    exact_definition_verifier_gate_source = (
        source_theorem_exact_semantic_definition_verifier_gate_executor.add_mutually_exclusive_group(
            required=True
        )
    )
    exact_definition_verifier_gate_source.add_argument(
        "--recheck-manifest",
        help=(
            "exact_source_theorem_proof_body_execution_queue_manifest.json "
            "listing verifier_gate_work_orders_jsonl"
        ),
    )
    exact_definition_verifier_gate_source.add_argument(
        "--work-orders-jsonl",
        help=(
            "source_theorem_exact_semantic_definition_typechecked_review_verifier_gate_work_orders.jsonl"
        ),
    )
    source_theorem_exact_semantic_definition_verifier_gate_executor.add_argument(
        "--local-lean",
        action="store_true",
        help="rerun local Lean on the definition-only candidate artifact",
    )
    source_theorem_exact_semantic_definition_verifier_gate_executor.add_argument(
        "--lean-project",
        default="",
        help="optional local Lake project for --local-lean",
    )
    source_theorem_exact_semantic_definition_verifier_gate_executor.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for local Lean verifier diagnostics",
    )
    source_theorem_exact_semantic_definition_verifier_gate_executor.add_argument(
        "--out",
        default=(
            "runs/"
            "source_theorem_exact_semantic_definition_verifier_gate_executor"
        ),
        help="verifier-gate executor output directory",
    )
    source_theorem_exact_semantic_definition_verifier_gate_executor.set_defaults(
        func=_source_theorem_exact_semantic_definition_verifier_gate_executor
    )

    source_theorem_exact_semantic_definition_candidate_synthesis = sub.add_parser(
        "source-theorem-exact-semantic-definition-candidate-synthesis",
        help=(
            "synthesize non-vacuous exact semantic-definition candidate drafts "
            "from closure review results and optionally run local Lean diagnostics"
        ),
    )
    exact_definition_synthesis_source = (
        source_theorem_exact_semantic_definition_candidate_synthesis.add_mutually_exclusive_group(
            required=True
        )
    )
    exact_definition_synthesis_source.add_argument(
        "--review-manifest",
        help=(
            "source_theorem_exact_semantic_definition_closure_review_manifest.json "
            "listing review_results_jsonl"
        ),
    )
    exact_definition_synthesis_source.add_argument(
        "--review-results-jsonl",
        help=(
            "source_theorem_exact_semantic_definition_closure_review_results.jsonl "
            "from closure review"
        ),
    )
    source_theorem_exact_semantic_definition_candidate_synthesis.add_argument(
        "--candidate-artifact",
        required=True,
        help="exact source theorem Lean candidate artifact to repair",
    )
    source_theorem_exact_semantic_definition_candidate_synthesis.add_argument(
        "--allow-draft-semantic-repair",
        action="store_true",
        help=(
            "opt in to replacing semantically risky known placeholders with "
            "non-proof draft definitions; default remains to block and export a "
            "review queue"
        ),
    )
    exact_definition_synthesis_recheck_source = (
        source_theorem_exact_semantic_definition_candidate_synthesis.add_mutually_exclusive_group()
    )
    exact_definition_synthesis_recheck_source.add_argument(
        "--proof-body-queue-manifest",
        default="",
        help=(
            "optional exact_source_theorem_proof_body_execution_queue_manifest.json; "
            "when supplied, emit a diagnostic recheck queue pointing at the synthesized artifact"
        ),
    )
    exact_definition_synthesis_recheck_source.add_argument(
        "--proof-body-queue-jsonl",
        default="",
        help=(
            "optional exact_source_theorem_proof_body_execution_queue.jsonl; "
            "when supplied, emit a diagnostic recheck queue pointing at the synthesized artifact"
        ),
    )
    source_theorem_exact_semantic_definition_candidate_synthesis.add_argument(
        "--local-lean",
        action="store_true",
        help="run local Lean on the synthesized candidate artifact as diagnostics",
    )
    source_theorem_exact_semantic_definition_candidate_synthesis.add_argument(
        "--lean-project",
        default="",
        help="optional local Lake project for --local-lean",
    )
    source_theorem_exact_semantic_definition_candidate_synthesis.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for the local Lean diagnostic check",
    )
    source_theorem_exact_semantic_definition_candidate_synthesis.add_argument(
        "--out",
        default="runs/source_theorem_exact_semantic_definition_candidate_synthesis",
        help="candidate synthesis output directory",
    )
    source_theorem_exact_semantic_definition_candidate_synthesis.set_defaults(
        func=_source_theorem_exact_semantic_definition_candidate_synthesis
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
        default=LLM_ROUTE_PLANNER_DEFAULT_MAX_TOKENS,
        help="maximum output tokens for live LLM route-planner providers",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--llm-route-planner-max-estimated-prompt-input-tokens",
        type=int,
        default=0,
        help=(
            "optional primary route-planner preflight cap on deterministic "
            "prompt input-token estimates before generation; 0 disables blocking"
        ),
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
        default=LLM_ROUTE_PLANNER_DEFAULT_MAX_TOKENS,
        help="maximum output tokens for feedback LLM route-planner providers",
    )
    formalization_gap_planner_reuse_smoke.add_argument(
        "--feedback-llm-route-planner-max-estimated-prompt-input-tokens",
        type=int,
        default=0,
        help=(
            "optional feedback route-planner preflight cap on deterministic "
            "prompt input-token estimates before generation; 0 disables blocking"
        ),
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
        default=LLM_ROUTE_PLANNER_DEFAULT_MAX_TOKENS,
        help="maximum generator output tokens when --invoke-provider is set",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--max-estimated-prompt-input-tokens",
        type=int,
        default=0,
        help=(
            "optional preflight cap on deterministic prompt input-token "
            "estimates before generation; 0 disables blocking"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--max-route-requests",
        type=int,
        default=0,
        help=(
            "optional cap on route-planner request packets generated from the "
            "standalone seed; 0 plans every route"
        ),
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
        "--max-staged-followup-stage-calls",
        type=int,
        default=LLM_ROUTE_PLANNER_DEFAULT_MAX_STAGED_FOLLOWUP_STAGE_CALLS,
        help=(
            "maximum compact staged-followup provider calls after a bounded "
            "live response is truncated or fails JSON extraction; 0 disables "
            "staged followup execution"
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
        "--source-theorem-semantic-primitive-bridge-dir",
        help=(
            "optional source-theorem semantic primitive bridge output directory "
            "carrying source semantic support checks"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--source-theorem-semantic-primitive-from-proof-body-executor-work-orders-dir",
        help=(
            "optional directory or JSONL carrying semantic primitive work orders "
            "materialized from exact proof-body executor feedback"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--source-theorem-formal-environment-bridge-dir",
        help=(
            "optional source-theorem formal-environment bridge output directory "
            "carrying repair packets for missing symbols/typeclasses"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--exact-source-theorem-proof-body-executor-dir",
        help=(
            "optional exact source-theorem proof-body executor output directory "
            "carrying local Lean execution results"
        ),
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-refinement-evidence-dir",
        help="optional refinement-evidence directory carrying literature, library, and proof-state feedback",
    )
    formalization_gap_planner_llm_route_planner.add_argument(
        "--formalization-gap-planner-route-contract-feedback-jsonl",
        help=(
            "optional JSONL or rows manifest carrying live route-planner "
            "contract feedback rows to force contract-aware replanning"
        ),
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
        "--formalization-gap-planner-resource-request-queue-dir",
        help="optional directory containing formalization_gap_planner_resource_request_queue_manifest.json",
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

    pseudo_formal_block_verifier_prompt_packets = sub.add_parser(
        "pseudo-formal-block-verifier-prompt-packets",
        help=(
            "export independent PF/BV block-verifier prompt packets from "
            "runtime learning request rows"
        ),
    )
    pseudo_formal_block_verifier_prompt_packets.add_argument(
        "--runtime-learning-jsonl",
        action="append",
        required=True,
        help=(
            "runtime_learning_rows.jsonl containing "
            "pseudo_formal_independent_block_verification_request rows; repeatable"
        ),
    )
    pseudo_formal_block_verifier_prompt_packets.add_argument(
        "--max-packets",
        type=int,
        default=20,
        help="maximum independent PF/BV request rows to export",
    )
    pseudo_formal_block_verifier_prompt_packets.add_argument(
        "--out",
        default="runs/pseudo_formal_block_verifier_prompt_packets",
        help="pseudo-formal block-verifier prompt packet output directory",
    )
    pseudo_formal_block_verifier_prompt_packets.set_defaults(
        func=_pseudo_formal_block_verifier_prompt_packets
    )

    pseudo_formal_block_verifier_llm_responses = sub.add_parser(
        "pseudo-formal-block-verifier-llm-responses",
        help=(
            "run generator-only LLM responses for independent PF/BV "
            "block-verifier prompt packets"
        ),
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--prompt-packets-manifest",
        required=True,
        help="pseudo_formal_block_verifier_prompt_packets_manifest.json",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--provider",
        choices=["anthropic", "openai", "static"],
        default="anthropic",
        help="generator-only provider for independent BV responses",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--model",
        default="",
        help="optional provider model override; default resolves by model tier",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--model-tier",
        choices=list(CLAUDE_MODEL_TIERS),
        default="sonnet",
        help="Claude cost tier used when provider/model resolution needs a default",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--static-response-file",
        default="",
        help="JSON response fixture used only with --provider static",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
        help="wall-clock timeout for live generator calls",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--max-packets",
        type=int,
        default=20,
        help="maximum prompt packets to answer",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--max-tokens",
        type=int,
        default=2000,
        help="maximum output tokens for each BV response",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="generator temperature for BV responses",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--max-repair-attempts",
        type=int,
        default=1,
        help="JSON validation repair attempts before marking a response failed",
    )
    pseudo_formal_block_verifier_llm_responses.add_argument(
        "--out",
        default="runs/pseudo_formal_block_verifier_llm_responses",
        help="pseudo-formal block-verifier LLM response output directory",
    )
    pseudo_formal_block_verifier_llm_responses.set_defaults(
        func=_pseudo_formal_block_verifier_llm_responses
    )

    pseudo_formal_block_verifier_response_validation = sub.add_parser(
        "pseudo-formal-block-verifier-response-validation",
        help=(
            "validate independent PF/BV block-verifier responses and export "
            "runtime learning feedback rows"
        ),
    )
    pseudo_formal_block_verifier_response_validation.add_argument(
        "--prompt-packets-manifest",
        required=True,
        help="pseudo_formal_block_verifier_prompt_packets_manifest.json",
    )
    pseudo_formal_block_verifier_response_validation.add_argument(
        "--response-jsonl",
        required=True,
        help="JSONL of independent block-verifier responses",
    )
    pseudo_formal_block_verifier_response_validation.add_argument(
        "--out",
        default="runs/pseudo_formal_block_verifier_response_validation",
        help="pseudo-formal block-verifier response validation output directory",
    )
    pseudo_formal_block_verifier_response_validation.set_defaults(
        func=_pseudo_formal_block_verifier_response_validation
    )

    pseudo_formal_block_verifier_component_gate = sub.add_parser(
        "pseudo-formal-block-verifier-component-gate",
        help=(
            "run the full PF/BV component gate: prompt packets, generator "
            "responses, response validation, and non-proof runtime feedback rows"
        ),
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--runtime-learning-jsonl",
        action="append",
        required=True,
        help=(
            "runtime_learning_rows.jsonl containing independent PF/BV "
            "block-verification request rows; repeatable"
        ),
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--provider",
        choices=["anthropic", "openai", "static"],
        default="anthropic",
        help="generator-only provider for the PF/BV BlockVerifier component gate",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--model",
        default="",
        help="optional provider model override; default resolves by model tier",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--model-tier",
        choices=list(CLAUDE_MODEL_TIERS),
        default="sonnet",
        help="Claude cost tier used when provider/model resolution needs a default",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--static-response-file",
        default="",
        help="JSON response fixture used only with --provider static",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
        help="wall-clock timeout for live generator calls",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--max-packets",
        type=int,
        default=20,
        help="maximum independent PF/BV request rows to evaluate",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--max-tokens",
        type=int,
        default=2000,
        help="maximum output tokens for each BV response",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="generator temperature for BV responses",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--max-repair-attempts",
        type=int,
        default=1,
        help="JSON validation repair attempts before marking a response failed",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--out",
        default="runs/pseudo_formal_block_verifier_component_gate",
        help="pseudo-formal block-verifier component gate output directory",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--env-file",
        default=".env",
        help="environment file for live generator API keys",
    )
    pseudo_formal_block_verifier_component_gate.add_argument(
        "--allow-fixture-success",
        action="store_true",
        help=(
            "return success for static fixture plumbing checks; default success "
            "requires live PF/BV capability evidence"
        ),
    )
    pseudo_formal_block_verifier_component_gate.set_defaults(
        func=_pseudo_formal_block_verifier_component_gate
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

    exact_source_theorem_proof_body_executor = sub.add_parser(
        "exact-source-theorem-proof-body-executor",
        help=(
            "consume exact source-theorem proof-body execution queue rows, "
            "materialize candidate artifacts, and optionally run local Lean"
        ),
    )
    exact_source_theorem_proof_body_executor.add_argument(
        "--exact-source-theorem-proof-body-execution-queue-dir",
        default="",
        help=(
            "directory containing "
            "exact_source_theorem_proof_body_execution_queue_manifest.json"
        ),
    )
    exact_source_theorem_proof_body_executor.add_argument(
        "--proof-body-repair-work-orders-jsonl",
        default="",
        help=(
            "optional runtime_source_theorem_promotion_work_orders.jsonl containing "
            "source_theorem_exact_proof_body_repair rows; when set, the CLI first "
            "materializes an exact source theorem proof-body execution queue"
        ),
    )
    exact_source_theorem_proof_body_executor.add_argument(
        "--out",
        default="runs/exact_source_theorem_proof_body_executor",
        help="exact source theorem proof-body executor output directory",
    )
    exact_source_theorem_proof_body_executor.add_argument(
        "--overwrite",
        action="store_true",
        help="rewrite existing candidate artifacts instead of reusing them",
    )
    exact_source_theorem_proof_body_executor.add_argument(
        "--local-lean",
        action="store_true",
        help="run local lake env lean/lean on materialized candidate artifacts",
    )
    exact_source_theorem_proof_body_executor.add_argument(
        "--lean-project",
        default="",
        help="optional local Lake project; when set runs lake env lean",
    )
    exact_source_theorem_proof_body_executor.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="seconds before local Lean proof-body execution check times out",
    )
    exact_source_theorem_proof_body_executor.set_defaults(
        func=_exact_source_theorem_proof_body_executor
    )

    runtime_source_theorem_promotion_proofengineer_bridge = sub.add_parser(
        "runtime-source-theorem-promotion-proofengineer-bridge",
        help=(
            "materialize source-theorem promotion seeds, run optional local Lean, "
            "and emit ProofEngineer bridge work orders"
        ),
    )
    runtime_source_theorem_promotion_proofengineer_bridge.add_argument(
        "--seed-queue-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_execution_queue_manifest.json",
    )
    runtime_source_theorem_promotion_proofengineer_bridge.add_argument(
        "--out",
        default="runs/runtime_source_theorem_promotion_proofengineer_bridge",
        help="runtime source-theorem promotion ProofEngineer bridge output directory",
    )
    runtime_source_theorem_promotion_proofengineer_bridge.add_argument(
        "--lean-project",
        default="",
        help="optional local Lake project; when set runs lake env lean",
    )
    runtime_source_theorem_promotion_proofengineer_bridge.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="seconds before each local Lean artifact/source-theorem check times out",
    )
    runtime_source_theorem_promotion_proofengineer_bridge.add_argument(
        "--no-local-lean",
        action="store_true",
        help="materialize only; skip local Lean artifact and source-theorem checks",
    )
    runtime_source_theorem_promotion_proofengineer_bridge.add_argument(
        "--overwrite",
        action="store_true",
        help="rewrite existing exact-source candidate artifacts before verification",
    )
    runtime_source_theorem_promotion_proofengineer_bridge.set_defaults(
        func=_runtime_source_theorem_promotion_proofengineer_bridge
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

    formal_verifier_agentic_proof_source_theorem_integrator = sub.add_parser(
        "formal-verifier-agentic-proof-source-theorem-integrator",
        help=(
            "attempt exact source-theorem Lean integration from ready promotion rows"
        ),
    )
    formal_verifier_agentic_proof_source_theorem_integrator.add_argument(
        "--formal-verifier-agentic-proof-source-theorem-promotion-queue-dir",
        required=True,
        help="directory containing formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json",
    )
    formal_verifier_agentic_proof_source_theorem_integrator.add_argument(
        "--out",
        default="runs/formal_verifier_agentic_proof_source_theorem_integrator",
        help="formal-verifier agentic source-theorem integrator output directory",
    )
    formal_verifier_agentic_proof_source_theorem_integrator.add_argument(
        "--lean-project",
        default="",
        help="optional local Lake project; when set runs lake env lean",
    )
    formal_verifier_agentic_proof_source_theorem_integrator.add_argument(
        "--lean-timeout",
        type=int,
        default=90,
        help="seconds before local Lean source-theorem verification times out",
    )
    formal_verifier_agentic_proof_source_theorem_integrator.add_argument(
        "--no-local-lean",
        action="store_true",
        help="only run exact-source static guards without local Lean",
    )
    formal_verifier_agentic_proof_source_theorem_integrator.set_defaults(
        func=_formal_verifier_agentic_proof_source_theorem_integrator
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
    theory_intake.add_argument("--llm-provider", choices=GENERATOR_PROVIDER_CHOICES, default=_default_live_generator_provider())
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
        choices=GENERATOR_PROVIDER_CHOICES,
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
    research_system_audit.add_argument(
        "--no-research-agent-runtime-contract-smoke",
        action="store_true",
        help=(
            "disable the deterministic AgentRuntime audit-contract fallback when "
            "--research-agent-runtime-dir is not supplied and offline runtime "
            "smoke is disabled"
        ),
    )
    research_system_audit.add_argument(
        "--no-research-agent-runtime-offline-smoke",
        action="store_true",
        help=(
            "disable the default static-backend real AgentRuntime smoke when "
            "--research-agent-runtime-dir is not supplied"
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
    research_architect_theory.add_argument(
        "--question-id",
        action="append",
        default=[],
        help=(
            "run only the matching question id from --question-file; repeatable "
            "for targeted live/runtime-learning smokes"
        ),
    )
    research_architect_theory.add_argument("--max-questions", type=int, default=0, help="optional cap for quick runs")
    research_architect_theory.add_argument(
        "--provider",
        choices=GENERATOR_PROVIDER_CHOICES,
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
        "--capability-gap-routing-jsonl",
        action="append",
        default=[],
        help=(
            "runtime_capability_gap_routing.jsonl from a prior runtime audit to "
            "inject as bounded non-evidence Architect routing context; repeatable"
        ),
    )
    research_architect_theory.add_argument(
        "--max-capability-gap-routing-rows",
        type=int,
        default=20,
    )
    research_architect_theory.add_argument(
        "--llm-model",
        default="",
        help="model name for the TheoryDeveloper provider; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_architect_theory.add_argument("--max-tokens", type=int, default=ResearchArchitectConfig().max_tokens)
    research_architect_theory.add_argument("--temperature", type=float, default=0.2)
    research_architect_theory.add_argument(
        "--max-repair-attempts",
        type=int,
        default=ResearchArchitectConfig().max_repair_attempts,
        help=(
            "maximum local-validator repair retries for TheoryDeveloper JSON "
            "packets; set 0 to disable extra provider calls"
        ),
    )
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
    research_agent_runtime.add_argument(
        "--question-id",
        action="append",
        default=[],
        help=(
            "run only the matching question id from --question-file; repeatable "
            "for targeted live/runtime-learning smokes"
        ),
    )
    research_agent_runtime.add_argument(
        "--question-task-family",
        action="append",
        default=[],
        help=(
            "run only questions whose primary statistics task family matches "
            "this value; repeatable for cross-family capability eval selection"
        ),
    )
    research_agent_runtime.add_argument(
        "--min-task-families",
        type=int,
        default=0,
        help=(
            "reject the selected question set unless it contains at least this "
            "many explicit statistics task families; useful before live L9 "
            "capability runs"
        ),
    )
    research_agent_runtime.add_argument("--max-questions", type=int, default=0, help="optional cap for quick runs")
    research_agent_runtime.add_argument(
        "--provider",
        choices=GENERATOR_PROVIDER_CHOICES,
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
        "--resume-runtime-manifest",
        default="",
        help=(
            "resume from a prior research-agent-runtime manifest that ended with "
            "incomplete_pending_next_task; the run starts from that exact AgentTask "
            "payload instead of restarting at Architect/Retrieval"
        ),
    )
    resume_architect_group = research_agent_runtime.add_mutually_exclusive_group()
    resume_architect_group.add_argument(
        "--resume-through-architect",
        dest="resume_through_architect",
        action="store_true",
        default=None,
        help=(
            "when --resume-runtime-manifest and ArchitectCoordinator are configured, "
            "run an Architect resume-review turn before returning to the pending task"
        ),
    )
    resume_architect_group.add_argument(
        "--no-resume-through-architect",
        dest="resume_through_architect",
        action="store_false",
        help=(
            "when --resume-runtime-manifest is set, resume the pending AgentTask "
            "directly; intended for debug/replay runs because capability audits will "
            "not count this as live ArchitectCoordinator orchestration"
        ),
    )
    research_agent_runtime.add_argument(
        "--learning-memory-jsonl",
        action="append",
        default=[],
        help="prior runtime_learning_rows.jsonl to inject as bounded non-evidence prompt memory; repeatable",
    )
    research_agent_runtime.add_argument("--max-learning-memory-rows", type=int, default=20)
    research_agent_runtime.add_argument(
        "--capability-gap-routing-jsonl",
        action="append",
        default=[],
        help=(
            "runtime_capability_gap_routing.jsonl from a prior runtime audit to "
            "inject as bounded non-evidence Architect/runtime routing context; "
            "repeatable"
        ),
    )
    research_agent_runtime.add_argument(
        "--max-capability-gap-routing-rows",
        type=int,
        default=20,
    )
    research_agent_runtime.add_argument(
        "--llm-model",
        default="",
        help="model name for the TheoryDeveloper provider; Anthropic defaults to Claude Sonnet 4.6",
    )
    research_agent_runtime.add_argument("--max-tokens", type=int, default=ResearchArchitectConfig().max_tokens)
    research_agent_runtime.add_argument("--temperature", type=float, default=0.2)
    research_agent_runtime.add_argument(
        "--theory-max-repair-attempts",
        type=int,
        default=ResearchArchitectConfig().max_repair_attempts,
        help=(
            "maximum local-validator repair retries for TheoryDeveloper JSON "
            "packets; set 0 to disable extra provider calls"
        ),
    )
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
        "--formalizer-candidate-local-lean",
        action="store_true",
        help=(
            "run local Lean on materialized LLM Formalizer candidate artifacts; "
            "this checks the generated Lean file itself, not just registered proof-bank subclaims"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-candidate-lean-lsp-mcp",
        action="store_true",
        help=(
            "when --formalizer-candidate-local-lean is enabled, also call Lean LSP MCP "
            "diagnostic tools on materialized Formalizer candidate artifacts and feed the "
            "tool trace back to ProofEngineer; diagnostic only, not proof evidence"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-candidate-lean-project",
        default="",
        help=(
            "local Lake project used by --formalizer-candidate-local-lean; "
            "defaults to --lean-project when omitted"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-candidate-lean-timeout",
        type=int,
        default=30,
        help="timeout seconds for each materialized Formalizer candidate local Lean check",
    )
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
        "--source-semantic-proofengineer-bridge",
        action="store_true",
        help=(
            "after the runtime loop emits source-theorem semantic primitive "
            "work orders, run the ProofEngineer bridge and export separate "
            "learning rows for a later run"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-semantic-proofengineer-local-lean",
        action="store_true",
        help=(
            "when the source-semantic ProofEngineer bridge is enabled, run "
            "local lake env lean for registered semantic-bridge obligations"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-semantic-proofengineer-lean-project",
        default="",
        help="local Lake project used by --source-semantic-proofengineer-local-lean",
    )
    research_agent_runtime.add_argument(
        "--source-semantic-proofengineer-lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each source-semantic local Lean check",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-proof-body-adapter-proofengineer-bridge",
        action="store_true",
        help=(
            "after source-theorem proof-body adapter work orders are emitted, "
            "materialize adapter candidates and export ProofEngineer feedback rows"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-proof-body-adapter-proofengineer-local-lean",
        action="store_true",
        help=(
            "when the proof-body adapter bridge is enabled, run local Lean on "
            "adapter candidates"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-proof-body-adapter-proofengineer-lean-project",
        default="",
        help=(
            "optional local Lake project used by "
            "--source-theorem-proof-body-adapter-proofengineer-local-lean"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-proof-body-adapter-proofengineer-lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each proof-body adapter local Lean check",
    )
    research_agent_runtime.add_argument(
        "--source-to-bridge-premise-derivation-proofengineer-bridge",
        action="store_true",
        help=(
            "after source-to-bridge premise derivation work orders are emitted, "
            "materialize premise derivation candidates and export ProofEngineer "
            "feedback rows"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-to-bridge-premise-derivation-proofengineer-local-lean",
        action="store_true",
        help=(
            "when the premise-derivation bridge is enabled, run local Lean on "
            "premise-derivation candidates"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-to-bridge-premise-derivation-proofengineer-lean-project",
        default="",
        help=(
            "optional local Lake project used by "
            "--source-to-bridge-premise-derivation-proofengineer-local-lean"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-to-bridge-premise-derivation-proofengineer-lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each source-to-bridge premise local Lean check",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-formal-environment-proofengineer-bridge",
        action="store_true",
        help=(
            "after exact source-theorem environment work orders are emitted, "
            "export ProofEngineer repair packets and runtime learning rows"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-formal-environment-proofengineer-signature-probes",
        action="store_true",
        help=(
            "when the formal-environment bridge is enabled, materialize and run "
            "typecheck-only Lean signature probes; these are diagnostics, not proof evidence"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-formal-environment-proofengineer-execute-proof-body",
        action="store_true",
        help=(
            "after signature probes reach a proof body, consume the generated "
            "proof-body execution queue and export ProofEngineer feedback rows"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-formal-environment-proofengineer-proof-body-local-lean",
        action="store_true",
        help=(
            "when proof-body execution is enabled, run local Lean on materialized "
            "candidate artifacts"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-formal-environment-proofengineer-proof-body-overwrite-artifacts",
        action="store_true",
        help=(
            "when proof-body execution is enabled, rewrite existing candidate "
            "artifacts before optional local Lean checks"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-formal-environment-proofengineer-lean-project",
        default="",
        help=(
            "optional local Lake project used by formal-environment signature probes"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-formal-environment-proofengineer-lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each formal-environment signature-probe local Lean check",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-promotion-proofengineer-bridge",
        action="store_true",
        help=(
            "after the runtime loop emits source-theorem promotion materialization "
            "seeds, run the materializer bridge and optionally local Lean artifact "
            "checks before source-theorem promotion"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-promotion-proofengineer-local-lean",
        action="store_true",
        help=(
            "when the source-theorem promotion ProofEngineer bridge is enabled, "
            "run local Lean on materialized route-probe artifacts"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-promotion-proofengineer-overwrite-artifacts",
        action="store_true",
        help=(
            "when the source-theorem promotion ProofEngineer bridge is enabled, "
            "rewrite existing exact-source candidate artifacts before verification"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-promotion-proofengineer-lean-project",
        default="",
        help=(
            "optional local Lake project used by "
            "--source-theorem-promotion-proofengineer-local-lean"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-promotion-proofengineer-lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for each source-theorem promotion artifact Lean check",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-source-lookup",
        action="store_true",
        help=(
            "after exact semantic-definition work orders are emitted, search "
            "configured local Lean source roots and append source-lookup learning rows"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-source-root",
        action="append",
        default=[],
        help=(
            "Lean source root searched by the exact semantic-definition lookup stage; "
            "repeat for Mathlib/StatInference/EmpiricalProcessLEAN checkouts"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-source-lookup-max-hits",
        type=int,
        default=8,
        help="maximum source text hits retained for each exact semantic-definition work order",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-proofengineer-bridge",
        action="store_true",
        help=(
            "after exact semantic-definition source lookup, export "
            "ProofEngineer repair packets and runtime learning rows"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-lean-repair-executor",
        action="store_true",
        help=(
            "after the exact semantic-definition ProofEngineer bridge, consume "
            "Lean repair tasks and append non-proof ProofEngineer feedback rows"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-lean-repair-executor-local-lean",
        action="store_true",
        help=(
            "when the exact semantic-definition Lean repair executor is enabled, "
            "run local Lean on resolved import-candidate source files"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-lean-repair-executor-lean-project",
        default="",
        help="local Lake project used by exact semantic-definition Lean repair executor",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-lean-repair-executor-lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for exact semantic-definition Lean repair executor checks",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-lean-environment-repair-executor",
        action="store_true",
        help=(
            "after the exact semantic-definition Lean repair executor emits Lake "
            "environment repair tasks, run the non-proof environment preflight and "
            "append focused next-action learning rows"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker",
        action="store_true",
        help=(
            "after the exact semantic-definition Lean repair executor emits "
            "authoring tasks, stage generator-only authoring prompt packets in the "
            "runtime trace; use the explicit provider flags for candidate replay"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-provider",
        choices=("none",) + GENERATOR_PROVIDER_CHOICES,
        default="none",
        help=(
            "generator backend for exact semantic-definition authoring tasks; "
            "none stages prompt packets only, static replays a reviewed JSON "
            "response, and live providers require explicit external-export approval"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-static-response-file",
        default="",
        help=(
            "JSON authoring response to replay when the exact semantic-definition "
            "authoring worker provider is static"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-model",
        default="",
        help=(
            "model label recorded for exact semantic-definition authoring worker "
            "candidate packets"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-model-tier",
        choices=CLAUDE_MODEL_TIERS,
        default="sonnet",
        help=(
            "Claude cost tier for live exact semantic-definition authoring; "
            "default Sonnet because this is proof/formalization work"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-max-tokens",
        type=int,
        default=4000,
        help="maximum output tokens for each live exact semantic-definition authoring call",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-temperature",
        type=float,
        default=0.0,
        help="generation temperature for live exact semantic-definition authoring",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-max-repair-attempts",
        type=int,
        default=1,
        help="maximum JSON validation repair retries for live authoring calls",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
        help="wall-clock timeout for each live exact semantic-definition authoring call",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-max-tasks",
        type=int,
        default=0,
        help="optional cap on exact semantic-definition authoring tasks staged by the runtime",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-allow-external-export",
        action="store_true",
        help=(
            "allow the integrated runtime authoring worker to send exact "
            "semantic-definition prompt context to Anthropic/OpenAI; without this, "
            "live providers emit export-review packets but do not call the API"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-authoring-worker-external-export-mode",
        choices=("full", "redacted"),
        default="redacted",
        help=(
            "prompt payload mode for staged exact semantic-definition authoring "
            "packets; redacted is the runtime default"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-closure-review",
        action="store_true",
        help=(
            "after exact semantic-definition source lookup, review the current "
            "exact source-theorem candidate artifact for forbidden placeholder definitions"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-candidate-synthesis",
        action="store_true",
        help=(
            "after closure review finds placeholder definitions, synthesize a "
            "draft non-vacuous candidate artifact and append non-proof learning rows"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-candidate-synthesis-allow-draft-semantic-repair",
        action="store_true",
        help=(
            "opt in to replacing semantically risky known exact-definition "
            "placeholders with non-proof draft definitions; default remains to "
            "block and export a semantic-definition repair queue"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-candidate-synthesis-local-lean",
        action="store_true",
        help=(
            "when exact semantic-definition candidate synthesis is enabled, run "
            "local Lean on the synthesized candidate as diagnostics only"
        ),
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-candidate-synthesis-lean-project",
        default="",
        help="local Lake project used by exact semantic-definition candidate synthesis",
    )
    research_agent_runtime.add_argument(
        "--source-theorem-exact-semantic-definition-candidate-synthesis-lean-timeout",
        type=int,
        default=90,
        help="timeout seconds for exact semantic-definition candidate synthesis local Lean checks",
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
        "--formal-verification-policy",
        choices=("required", "optional", "advisory"),
        default="optional",
        help=(
            "research acceptance contract: required blocks final acceptance "
            "without Lean/AXLE source theorem evidence, optional lets Architect "
            "choose proof-first/simulation-first/dual-track, and advisory uses "
            "formal tools only as diagnostics with explicit gap disclosure"
        ),
    )
    research_agent_runtime.add_argument(
        "--recommended-research-path",
        choices=("simulation_first", "proof_first", "dual_track"),
        default="",
        help=(
            "optional runtime research-path request. Leave unset to let the "
            "Architect choose under --formal-verification-policy=optional; set "
            "to simulation_first, proof_first, or dual_track for controlled evals"
        ),
    )
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
        "--formalization-gap-planner-live-route-planner",
        action="store_true",
        help=(
            "inside AgentRuntime, follow successful gap-planner handoff smoke "
            "with a bounded live LLM route-planner task instead of stopping at "
            "prompt packets awaiting response"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalization-gap-planner-live-max-handoffs",
        type=int,
        default=1,
        help=(
            "maximum runtime gap-planner handoffs to send to the live route "
            "planner when --formalization-gap-planner-live-route-planner is enabled"
        ),
    )
    research_agent_runtime.add_argument(
        "--algorithm-engineer-generated-code-repair-yield-after-attempts",
        type=int,
        default=0,
        help=(
            "in capability-eval, route unresolved AlgorithmEngineer generated-code "
            "diagnostics to FormalizationEvaluator after this many self-repair "
            "attempts; 0 keeps the legacy unbounded self-repair routing"
        ),
    )
    research_agent_runtime.add_argument(
        "--simulation-evaluator-generated-code-repair-yield-after-attempts",
        type=int,
        default=0,
        help=(
            "in capability-eval, route unresolved SimulationEvaluator "
            "generated-simulation diagnostics to FormalizationEvaluator after "
            "this many self-repair attempts; 0 keeps the legacy unbounded "
            "self-repair routing"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-lean-candidate-repair-yield-to-gap-planner-after-attempts",
        type=int,
        default=0,
        help=(
            "in capability-eval, route repeated Formalizer/ProofEngineer "
            "Lean-candidate diagnostics to FormalizationGapPlanner after this "
            "many repair attempts; 0 keeps the legacy unbounded ProofEngineer "
            "repair routing"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalization-gap-planner-live-max-route-requests-per-handoff",
        type=int,
        default=1,
        help=(
            "maximum route-planner request packets generated inside each live "
            "runtime gap-planner handoff; 0 permits every route in the handoff seed"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalization-gap-planner-live-provider",
        choices=("same",) + LIVE_GENERATOR_PROVIDER_CHOICES,
        default="same",
        help=(
            "provider for the integrated live gap-planner route planner; same "
            "uses the main --provider"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalization-gap-planner-live-model",
        default="",
        help="optional model override for the integrated live gap-planner route planner",
    )
    research_agent_runtime.add_argument(
        "--formalization-gap-planner-live-model-tier",
        choices=("auto",) + CLAUDE_MODEL_TIERS,
        default="auto",
        help=(
            "Claude cost tier policy for integrated live gap-planner route "
            "planning; auto uses the route-planner model-tier policy"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalization-gap-planner-live-max-tokens",
        type=int,
        default=9000,
        help="maximum output tokens for each live gap-planner route-planner call",
    )
    research_agent_runtime.add_argument(
        "--formalization-gap-planner-live-temperature",
        type=float,
        default=0.1,
        help="generation temperature for live gap-planner route planning",
    )
    research_agent_runtime.add_argument(
        "--formalization-gap-planner-live-max-repair-attempts",
        type=int,
        default=1,
        help="maximum JSON repair attempts for live gap-planner route-planner responses",
    )
    research_agent_runtime.add_argument(
        "--formalization-gap-planner-live-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
        help="wall-clock timeout for each live gap-planner route-planner provider call",
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
    research_agent_runtime.add_argument(
        "--capability-eval-preset",
        choices=("none", "minimal-live", "full-live"),
        default="none",
        help=(
            "populate strict live capability-eval defaults without weakening "
            "the scorecard gates. minimal-live enables live providers and the "
            "internal Lean/ProofEngineer paths; full-live also attaches the "
            "coding-agent repair, Formalizer/Lean repair, live Lean-LSP/MCP, "
            "PF/BV BlockVerifier, and integrated FormalizationGapPlanner live "
            "route-planner gates. "
            "Static fixtures never become capability evidence."
        ),
    )
    research_agent_runtime.add_argument(
        "--run-coding-agent-generated-code-repair-eval",
        action="store_true",
        help=(
            "after AgentRuntime finishes, run the combined AlgorithmEngineer + "
            "SimulationEngineer generated-code repair gate and attach its manifest "
            "to the runtime manifest. This component gate is not theorem proof and "
            "does not substitute for integrated runtime success."
        ),
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-provider",
        choices=("same", "anthropic", "openai", "static"),
        default="same",
        help=(
            "provider for --run-coding-agent-generated-code-repair-eval; same uses "
            "the runtime --provider"
        ),
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-model",
        default="",
        help="optional model for the attached coding-agent repair eval",
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-question-id",
        default="conformal_prediction_coverage",
        help=(
            "question id for the attached component repair eval; defaults to "
            "the conformal generated-code repair probe and is intentionally "
            "separate from the main runtime question selection"
        ),
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-algorithm-static-response-file",
        default="",
        help=(
            "AlgorithmEngineer static JSON response for the attached repair eval "
            "when --coding-agent-repair-eval-provider static"
        ),
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-simulation-static-response-file",
        default="",
        help=(
            "SimulationEngineer static JSON response for the attached repair eval "
            "when --coding-agent-repair-eval-provider static"
        ),
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-max-tokens",
        type=int,
        default=4000,
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-temperature",
        type=float,
        default=0.1,
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-runs",
        type=int,
        default=24,
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-seed",
        type=int,
        default=20260623,
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-target-coverage",
        type=float,
        default=0.9,
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-max-repair-attempts",
        type=int,
        default=4,
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-out",
        default="",
        help=(
            "optional output directory for the attached coding-agent repair eval; "
            "defaults to <runtime-out>/internal_coding_agent_generated_code_repair_eval"
        ),
    )
    research_agent_runtime.add_argument(
        "--coding-agent-repair-eval-existing-manifest",
        default="",
        help=(
            "attach an existing CodingAgentGeneratedCodeRepairEvalManifest instead "
            "of rerunning the coding-agent repair eval. The attachment remains "
            "component calibration evidence only."
        ),
    )
    research_agent_runtime.add_argument(
        "--run-formalizer-lean-candidate-repair-eval",
        action="store_true",
        help=(
            "after AgentRuntime finishes, run the Formalizer/ProofEngineer "
            "Lean-candidate repair gate and attach its manifest to the runtime "
            "manifest. This component gate is not source theorem proof."
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-provider",
        choices=("same", "anthropic", "openai", "static"),
        default="same",
        help=(
            "provider for --run-formalizer-lean-candidate-repair-eval; same uses "
            "the runtime --provider"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-model",
        default="",
        help="optional model for the attached Formalizer Lean-candidate repair eval",
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-question-id",
        default="conformal_prediction_coverage",
        help=(
            "source question id recorded by the attached Formalizer component "
            "eval; the eval itself uses a synthetic helper-repair question"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-static-response-file",
        default="",
        help=(
            "Formalizer static JSON response for the attached repair eval when "
            "--formalizer-repair-eval-provider static"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-runtime-timeout-seconds",
        type=float,
        default=max(DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS * 2.0, 300.0),
        help=(
            "wall-clock timeout for the attached Formalizer Lean-candidate "
            "repair eval as a whole; use 0 to disable. Timeout produces an "
            "attached failure manifest and does not invalidate the completed "
            "AgentRuntime manifest."
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-max-tokens",
        type=int,
        default=4000,
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-temperature",
        type=float,
        default=0.1,
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-lean-project",
        default="",
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-lean-timeout",
        type=int,
        default=15,
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-max-repair-attempts",
        type=int,
        default=3,
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-out",
        default="",
        help=(
            "optional output directory for the attached Formalizer repair eval; "
            "defaults to <runtime-out>/internal_formalizer_lean_candidate_repair_eval"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-repair-eval-existing-manifest",
        default="",
        help=(
            "attach an existing FormalizerLeanCandidateRepairEvalManifest instead "
            "of rerunning the Formalizer repair eval. The attachment remains "
            "component calibration evidence only."
        ),
    )
    research_agent_runtime.add_argument(
        "--run-formalizer-pseudo-formal-packet-eval",
        action="store_true",
        help=(
            "after AgentRuntime finishes, run the Formalizer/ProofEngineer PF/BV "
            "packet-emission gate and attach its manifest to the runtime manifest. "
            "This component gate is not theorem proof evidence."
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-provider",
        choices=("same", "anthropic", "openai", "static"),
        default="same",
        help=(
            "provider for --run-formalizer-pseudo-formal-packet-eval; same uses "
            "the runtime --provider"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-model",
        default="",
        help="optional model for the attached Formalizer PF/BV packet eval",
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-static-response-file",
        default="",
        help=(
            "Formalizer static JSON response for the attached PF/BV packet eval "
            "when --formalizer-pseudo-formal-packet-eval-provider static"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-runtime-timeout-seconds",
        type=float,
        default=max(DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS * 2.0, 300.0),
        help=(
            "wall-clock cap for the attached Formalizer PF/BV packet eval; "
            "timeouts are written as failure manifests so full-live runtime "
            "outputs do not strand after the main manifest is written"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-max-tokens",
        type=int,
        default=5000,
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-temperature",
        type=float,
        default=0.1,
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-max-repair-attempts",
        type=int,
        default=1,
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-out",
        default="",
        help=(
            "optional output directory for the attached Formalizer PF/BV packet "
            "eval; defaults to <runtime-out>/internal_formalizer_pseudo_formal_packet_eval"
        ),
    )
    research_agent_runtime.add_argument(
        "--formalizer-pseudo-formal-packet-eval-existing-manifest",
        default="",
        help=(
            "attach an existing FormalizerPseudoFormalPacketEvalManifest instead "
            "of rerunning the PF/BV packet eval. The attachment remains component "
            "calibration evidence only."
        ),
    )
    research_agent_runtime.add_argument(
        "--run-pseudo-formal-block-verifier-eval",
        action="store_true",
        help=(
            "after AgentRuntime finishes, run the PF/BV prompt, LLM response, "
            "and response-validation component gate and attach validated "
            "non-proof feedback rows to runtime memory"
        ),
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-provider",
        choices=("same", "anthropic", "openai", "static"),
        default="same",
        help=(
            "provider for --run-pseudo-formal-block-verifier-eval; same uses "
            "the runtime --provider"
        ),
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-model",
        default="",
        help="optional model override for the attached PF/BV component gate",
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-model-tier",
        choices=list(CLAUDE_MODEL_TIERS),
        default="sonnet",
        help="Claude cost tier used by the attached PF/BV component gate",
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-static-response-file",
        default="",
        help=(
            "static JSON response fixture used only with "
            "--pseudo-formal-block-verifier-eval-provider static"
        ),
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-runtime-learning-jsonl",
        action="append",
        default=[],
        help=(
            "runtime_learning_rows.jsonl to scan for independent PF/BV request "
            "rows; repeatable. Defaults to this runtime's learning rows."
        ),
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-max-packets",
        type=int,
        default=20,
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-max-tokens",
        type=int,
        default=2000,
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-temperature",
        type=float,
        default=0.0,
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-max-repair-attempts",
        type=int,
        default=1,
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-out",
        default="",
        help=(
            "optional output directory for the attached PF/BV component gate; "
            "defaults to <runtime-out>/internal_pseudo_formal_block_verifier_eval"
        ),
    )
    research_agent_runtime.add_argument(
        "--pseudo-formal-block-verifier-eval-existing-manifest",
        default="",
        help=(
            "attach an existing PseudoFormalBlockVerifierComponentGateManifest "
            "instead of rerunning PF/BV. The attachment remains component "
            "calibration evidence only."
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
    research_agent_runtime_audit.add_argument(
        "--post-runtime-exact-semantic-definition-authoring-worker-manifest",
        default="",
        help=(
            "optional SourceTheoremExactSemanticDefinitionAuthoringWorkerManifest "
            "from a post-runtime live authoring probe. The audit uses it only as "
            "lineage-checked authoring handoff/attempt evidence, not theorem proof."
        ),
    )
    research_agent_runtime_audit.add_argument(
        "--post-runtime-exact-semantic-definition-authoring-candidate-materializer-manifest",
        default="",
        help=(
            "optional SourceTheoremExactSemanticDefinitionAuthoringCandidateMaterializerManifest "
            "from a post-runtime materialization probe. The audit uses it only as "
            "lineage-checked candidate-materialization diagnostics, not theorem proof."
        ),
    )
    research_agent_runtime_audit.add_argument(
        "--post-runtime-exact-semantic-definition-materialized-lean-repair-executor-manifest",
        default="",
        help=(
            "optional SourceTheoremExactSemanticDefinitionLeanRepairExecutorManifest "
            "from a post-runtime local Lean repair/check probe. The audit uses it "
            "only as lineage-checked local Lean diagnostics, not source theorem proof."
        ),
    )
    research_agent_runtime_audit.set_defaults(func=_research_agent_runtime_audit)

    algorithm_engineer_generated_code_repair_eval = sub.add_parser(
        "algorithm-engineer-generated-code-repair-eval",
        help=(
            "component eval for AlgorithmEngineer generated-code repair: inject "
            "a prior metric-gate failure, call a generator backend, execute the "
            "new Python sandbox locally, and record fail-then-pass evidence"
        ),
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--question-file",
        default="examples/research_questions.json",
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--question-id",
        default="conformal_prediction_coverage",
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--provider",
        choices=("anthropic", "openai", "static"),
        default=_default_live_generator_provider(),
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--static-response-file",
        default="",
        help="JSON response to replay when --provider static",
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--llm-model",
        default="",
        help="model name for AlgorithmEngineer; Anthropic defaults to Claude Haiku 4.5",
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--temperature",
        type=float,
        default=0.1,
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--runs",
        type=int,
        default=24,
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--seed",
        type=int,
        default=20260623,
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--target-coverage",
        type=float,
        default=0.9,
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--max-repair-attempts",
        type=int,
        default=4,
        help=(
            "bounded generated-code repair attempts after the initial proposal; "
            "default allows validation repair and metric-gate repair"
        ),
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--out",
        default="runs/algorithm_engineer_generated_code_repair_eval",
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--env-file",
        default=".env",
    )
    algorithm_engineer_generated_code_repair_eval.add_argument(
        "--allow-fixture-success",
        action="store_true",
        help=(
            "return success for static fixture plumbing checks; default success "
            "requires live generator capability evidence"
        ),
    )
    algorithm_engineer_generated_code_repair_eval.set_defaults(
        func=_algorithm_engineer_generated_code_repair_eval
    )

    simulation_engineer_generated_code_repair_eval = sub.add_parser(
        "simulation-engineer-generated-code-repair-eval",
        help=(
            "component eval for SimulationEngineer generated-code repair: inject "
            "a prior metric-gate failure, call a generator backend, execute the "
            "new Python stress-test sandbox locally, and record fail-then-pass evidence"
        ),
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--question-file",
        default="examples/research_questions.json",
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--question-id",
        default="conformal_prediction_coverage",
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--provider",
        choices=("anthropic", "openai", "static"),
        default=_default_live_generator_provider(),
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--static-response-file",
        default="",
        help="JSON response to replay when --provider static",
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--llm-model",
        default="",
        help="model name for SimulationEngineer; Anthropic defaults to Claude Haiku 4.5",
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--temperature",
        type=float,
        default=0.1,
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--runs",
        type=int,
        default=24,
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--seed",
        type=int,
        default=20260623,
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--target-coverage",
        type=float,
        default=0.9,
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--max-repair-attempts",
        type=int,
        default=4,
        help=(
            "bounded generated-simulation repair attempts after the initial proposal; "
            "default allows validation repair and metric-gate repair"
        ),
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--out",
        default="runs/simulation_engineer_generated_code_repair_eval",
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--env-file",
        default=".env",
    )
    simulation_engineer_generated_code_repair_eval.add_argument(
        "--allow-fixture-success",
        action="store_true",
        help=(
            "return success for static fixture plumbing checks; default success "
            "requires live generator capability evidence"
        ),
    )
    simulation_engineer_generated_code_repair_eval.set_defaults(
        func=_simulation_engineer_generated_code_repair_eval
    )

    coding_agent_generated_code_repair_eval = sub.add_parser(
        "coding-agent-generated-code-repair-eval",
        help=(
            "combined coding-agent capability gate: AlgorithmEngineer and "
            "SimulationEngineer must both show generated-code fail-then-pass repair"
        ),
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--question-file",
        default="examples/research_questions.json",
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--question-id",
        default="conformal_prediction_coverage",
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--provider",
        choices=("anthropic", "openai", "static"),
        default=_default_live_generator_provider(),
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--algorithm-static-response-file",
        default="",
        help="AlgorithmEngineer JSON response to replay when --provider static",
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--simulation-static-response-file",
        default="",
        help="SimulationEngineer JSON response to replay when --provider static",
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--llm-model",
        default="",
        help="model name for coding-agent eval; Anthropic defaults to Claude Haiku 4.5",
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--temperature",
        type=float,
        default=0.1,
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--runs",
        type=int,
        default=24,
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--seed",
        type=int,
        default=20260623,
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--target-coverage",
        type=float,
        default=0.9,
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--max-repair-attempts",
        type=int,
        default=4,
        help=(
            "bounded repair attempts per component after the initial proposal; "
            "default allows validation repair and metric-gate repair"
        ),
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--out",
        default="runs/coding_agent_generated_code_repair_eval",
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--env-file",
        default=".env",
    )
    coding_agent_generated_code_repair_eval.add_argument(
        "--allow-fixture-success",
        action="store_true",
        help=(
            "return success for static fixture plumbing checks; default success "
            "requires both live generated-code repair capabilities"
        ),
    )
    coding_agent_generated_code_repair_eval.set_defaults(
        func=_coding_agent_generated_code_repair_eval
    )

    formalizer_lean_candidate_repair_eval = sub.add_parser(
        "formalizer-lean-candidate-repair-eval",
        help=(
            "component eval for Formalizer/ProofEngineer Lean-candidate repair: "
            "inject a prior local-Lean failure, call a generator backend, "
            "materialize the generated Lean candidate, run local Lean, and "
            "record fail-then-pass evidence"
        ),
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--question-file",
        default="examples/research_questions.json",
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--question-id",
        default="conformal_prediction_coverage",
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--provider",
        choices=("anthropic", "openai", "static"),
        default=_default_live_generator_provider(),
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--static-response-file",
        default="",
        help="Formalizer JSON response to replay when --provider static",
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--llm-model",
        default="",
        help="model name for Formalizer/ProofEngineer; Anthropic defaults to Claude Sonnet 4.6",
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--temperature",
        type=float,
        default=0.1,
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--lean-project",
        default="",
        help="optional local Lake project used by local Lean candidate checks",
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--lean-timeout",
        type=int,
        default=15,
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--lean-lsp-mcp-proof-state-feedback",
        action="store_true",
        help=(
            "use the Lean LSP/MCP proof-state provider for injected prior "
            "candidate feedback instead of the local-only adapter"
        ),
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--max-repair-attempts",
        type=int,
        default=3,
        help=(
            "bounded Formalizer repair attempts after injected local-Lean feedback"
        ),
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--out",
        default="runs/formalizer_lean_candidate_repair_eval",
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--env-file",
        default=".env",
    )
    formalizer_lean_candidate_repair_eval.add_argument(
        "--allow-fixture-success",
        action="store_true",
        help=(
            "return success for static fixture plumbing checks; default success "
            "requires live generator Lean-candidate repair evidence"
        ),
    )
    formalizer_lean_candidate_repair_eval.set_defaults(
        func=_formalizer_lean_candidate_repair_eval
    )

    formalizer_pseudo_formal_packet_eval = sub.add_parser(
        "formalizer-pseudo-formal-packet-eval",
        help=(
            "component eval for Formalizer/ProofEngineer PF/BV packet emission: "
            "force required pseudo-formal activation, validate source-anchored "
            "PF/BV packets, and record lane-routable work-order evidence"
        ),
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--provider",
        choices=("anthropic", "openai", "static"),
        default=_default_live_generator_provider(),
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--static-response-file",
        default="",
        help="Formalizer JSON response to replay when --provider static",
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--llm-model",
        default="",
        help="model name for Formalizer/ProofEngineer; Anthropic defaults to Claude Sonnet 4.6",
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--max-tokens",
        type=int,
        default=5000,
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--temperature",
        type=float,
        default=0.1,
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--max-repair-attempts",
        type=int,
        default=1,
        help=(
            "bounded Formalizer JSON repair attempts after required PF/BV "
            "packet validation failures"
        ),
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--out",
        default="runs/formalizer_pseudo_formal_packet_eval",
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--env-file",
        default=".env",
    )
    formalizer_pseudo_formal_packet_eval.add_argument(
        "--allow-fixture-success",
        action="store_true",
        help=(
            "return success for static fixture plumbing checks; default success "
            "requires live generator PF/BV packet emission evidence"
        ),
    )
    formalizer_pseudo_formal_packet_eval.set_defaults(
        func=_formalizer_pseudo_formal_packet_eval
    )

    architect_research_path_policy_eval = sub.add_parser(
        "architect-research-path-policy-eval",
        help=(
            "component eval for ArchitectCoordinator evidence-policy routing: "
            "check required/proof-first, advisory/simulation-first, and optional "
            "research-path plans from a generator backend"
        ),
    )
    architect_research_path_policy_eval.add_argument(
        "--provider",
        choices=("anthropic", "openai", "static"),
        default=_default_live_generator_provider(),
    )
    architect_research_path_policy_eval.add_argument(
        "--static-response-file",
        default="",
        help="JSON object or list of Architect responses to replay when --provider static",
    )
    architect_research_path_policy_eval.add_argument(
        "--llm-model",
        default="",
        help="model name for ArchitectCoordinator; Anthropic defaults to Claude Sonnet 4.6",
    )
    architect_research_path_policy_eval.add_argument(
        "--llm-timeout-seconds",
        type=float,
        default=DEFAULT_LIVE_GENERATOR_TIMEOUT_SECONDS,
    )
    architect_research_path_policy_eval.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
    )
    architect_research_path_policy_eval.add_argument(
        "--temperature",
        type=float,
        default=0.1,
    )
    architect_research_path_policy_eval.add_argument(
        "--out",
        default="runs/architect_research_path_policy_eval",
    )
    architect_research_path_policy_eval.add_argument(
        "--env-file",
        default=".env",
    )
    architect_research_path_policy_eval.add_argument(
        "--allow-fixture-success",
        action="store_true",
        help=(
            "return success for static fixture plumbing checks; default success "
            "requires live generator Architect policy evidence"
        ),
    )
    architect_research_path_policy_eval.set_defaults(
        func=_architect_research_path_policy_eval
    )

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

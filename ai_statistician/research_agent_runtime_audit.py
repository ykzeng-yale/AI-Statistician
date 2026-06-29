from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .model_backend import SUPPORTED_LIVE_GENERATOR_PROVIDERS
from .proof_bank import FORMAL_OBLIGATIONS
from .research_agent_runtime import (
    SOURCE_THEOREM_AUDIT_FORMAL_ENV_AGGREGATE_KERNEL_EVIDENCE_KEYS,
    SOURCE_THEOREM_AUDIT_FORMAL_ENV_AGGREGATE_RESULT_ROW_KEYS,
    SOURCE_THEOREM_AUDIT_KERNEL_EVIDENCE_COUNT_KEYS,
    _formalizer_lean_candidate_repair_sequence_count,
    _generated_sandbox_repair_sequence_counts,
    _runtime_evidence_summary,
    _runtime_evidence_truth_table_from_manifest,
    _runtime_manifest_int_sum,
)


RESEARCH_AGENT_RUNTIME_AUDIT_SCHEMA_VERSION = 1
REQUIRED_RUNTIME_STAGE = "retrieval_theory_simulation_algorithm_formalization_critic_environment_loop"
REQUIRED_ARCHITECT_RUNTIME_STAGE = (
    "architect_retrieval_theory_simulation_algorithm_formalization_critic_environment_loop"
)
REQUIRED_SUBSYSTEMS = (
    "RetrievalMemory",
    "TheoryDeveloper",
    "SimulationEvaluator",
    "AlgorithmEngineer",
    "FormalizationEvaluator",
    "CriticEvaluator",
)
REQUIRED_ARCHITECT_SUBSYSTEMS = ("ArchitectCoordinator", *REQUIRED_SUBSYSTEMS)
SUPPORTED_GENERATOR_PROVIDERS = set(SUPPORTED_LIVE_GENERATOR_PROVIDERS)
REAL_KERNEL_VERIFIERS = {"axle.verify_proof", "local.lake_env_lean"}
PROOF_STATE_FEEDBACK_ARTIFACT_PREFIXES = (
    "proof_state_feedback_manifest:",
    "formalizer_lean_candidate_proof_state_feedback_manifest:",
)


def _manifest_or_proof_summary_count(
    manifest: Mapping[str, Any],
    proof_summary: Mapping[str, Any],
    key: str,
) -> int:
    return max(
        int(manifest.get(key, 0) or 0),
        int(proof_summary.get(key, 0) or 0),
    )


@dataclass(frozen=True)
class RuntimeAuditRow:
    question_id: str
    result_path: str
    ok: bool
    status: str
    n_traces: int
    n_retrieval_manifests: int
    n_theory_packets: int
    n_simulation_manifests: int
    n_generated_simulation_sandbox_executed: int
    n_generated_simulation_sandbox_passed: int
    n_generated_simulation_sandbox_metric_gate_failed: int
    n_generated_simulation_sandbox_failed_then_passed_repair_sequences: int
    n_unsafe_generated_simulation_code_rejected: int
    n_algorithm_manifests: int
    n_algorithm_sandbox_executed: int
    n_generated_code_sandbox_executed: int
    n_generated_code_sandbox_metric_gate_failed: int
    n_generated_code_sandbox_failed_then_passed_repair_sequences: int
    n_unsafe_generated_code_rejected: int
    n_formalization_manifests: int
    n_critic_manifests: int
    n_kernel_verified_subclaims: int
    n_real_kernel_verified_subclaims: int
    n_non_real_kernel_verified_subclaims: int
    kernel_verified_verifiers: tuple[str, ...]
    real_kernel_verified_proof_obligation_ids: tuple[str, ...]
    real_kernel_verified_source_theorem_semantic_primitive_ids: tuple[str, ...]
    n_formal_gaps: int
    n_registered_proof_bank_obligation_candidates: int
    n_memory_prioritized_proof_obligations: int
    n_memory_off_catalog_proof_obligations: int
    n_memory_rejected_proof_obligations: int
    n_llm_requested_proof_obligations: int
    n_llm_off_catalog_proof_obligations: int
    n_llm_rejected_proof_obligations: int
    full_frontier_theorem_proved: bool
    n_agenda_items: int
    n_learning_rows: int
    architect_coordinator_enabled: bool
    n_critic_reroutes: int
    n_lean_lsp_mcp_live_calls: int
    has_runtime_learning_memory_input: bool
    has_kernel_verified_theorem_reduction_closure_memory: bool
    has_source_theorem_semantic_primitive_target_mode: bool
    has_problem_analysis: bool
    has_stat_knowledge_bank_plan: bool
    has_literature_fair_comparison_plan: bool
    errors: tuple[str, ...] = ()


def audit_research_agent_runtime(
    runtime_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest_path = runtime_dir / "research_agent_runtime_manifest.json"
    manifest = _load_json(manifest_path, errors)
    runtime_stage = str(manifest.get("runtime_stage", ""))
    if runtime_stage not in {REQUIRED_RUNTIME_STAGE, REQUIRED_ARCHITECT_RUNTIME_STAGE}:
        errors.append(
            f"runtime_stage must be {REQUIRED_RUNTIME_STAGE} or {REQUIRED_ARCHITECT_RUNTIME_STAGE}"
        )
    topology_errors = _audit_topology(manifest)
    errors.extend(topology_errors)
    result_paths = _resolve_manifest_paths(runtime_dir, manifest)
    rows = [_audit_result_path(path) for path in result_paths]
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        artifacts = {}
    trace_path = _resolve_path(runtime_dir, artifacts.get("runtime_traces_jsonl", ""))
    progress_path = _resolve_path(runtime_dir, artifacts.get("runtime_progress_jsonl", ""))
    agenda_path = _resolve_path(runtime_dir, artifacts.get("runtime_next_action_agenda_jsonl", ""))
    learning_path = _resolve_path(runtime_dir, artifacts.get("runtime_learning_rows_jsonl", ""))
    trace_rows = _load_jsonl(trace_path, errors, required=True)
    progress_rows = _load_jsonl(
        progress_path,
        errors,
        required=bool(artifacts.get("runtime_progress_jsonl")),
    )
    agenda_rows = _load_jsonl(agenda_path, errors, required=True)
    learning_rows = _load_jsonl(learning_path, errors, required=True)
    if int(manifest.get("n_questions", -1)) != len(rows):
        errors.append("manifest n_questions does not match per-question result count")
    if int(manifest.get("n_runtime_next_action_items", -1)) != len(agenda_rows):
        errors.append("manifest n_runtime_next_action_items does not match agenda JSONL")
    if int(manifest.get("n_runtime_learning_rows", -1)) != len(learning_rows):
        errors.append("manifest n_runtime_learning_rows does not match learning JSONL")
    if len(trace_rows) != sum(row.n_traces for row in rows):
        errors.append("runtime_traces.jsonl row count does not match per-question traces")
    if artifacts.get("runtime_progress_jsonl") and len(progress_rows) < 2 * len(trace_rows):
        errors.append(
            "runtime_progress.jsonl must include start and finish events for each completed trace"
        )
    runtime_input_context = (
        manifest.get("runtime_input_context", {})
        if isinstance(manifest.get("runtime_input_context"), Mapping)
        else {}
    )
    runtime_learning_memory_rows_loaded = int(
        runtime_input_context.get("runtime_learning_memory_rows_loaded", 0) or 0
    )
    runtime_learning_memory_supplied = (
        runtime_input_context.get("runtime_learning_memory_supplied") is True
    )
    if runtime_learning_memory_supplied and runtime_learning_memory_rows_loaded <= 0:
        errors.append("runtime input context declares learning memory but loaded zero rows")
    if runtime_learning_memory_rows_loaded > 0 and not any(
        row.has_runtime_learning_memory_input for row in rows
    ):
        errors.append("runtime input context memory rows were not propagated into per-question traces")

    result_errors = [
        {
            "question_id": row.question_id,
            "result_path": row.result_path,
            "errors": list(row.errors),
        }
        for row in rows
        if row.errors
    ]
    by_status = Counter(row.status for row in rows)
    n_kernel_verified_subclaims = sum(row.n_kernel_verified_subclaims for row in rows)
    n_real_kernel_verified_subclaims = sum(row.n_real_kernel_verified_subclaims for row in rows)
    n_non_real_kernel_verified_subclaims = sum(row.n_non_real_kernel_verified_subclaims for row in rows)
    runtime_memory_evidence = _runtime_learning_memory_evidence(trace_rows)
    runtime_evidence_summary = (
        dict(manifest.get("runtime_evidence_summary", {}) or {})
        if isinstance(manifest.get("runtime_evidence_summary", {}), Mapping)
        else {}
    )
    runtime_proof_summary = (
        dict(runtime_evidence_summary.get("proof", {}) or {})
        if isinstance(runtime_evidence_summary.get("proof", {}), Mapping)
        else {}
    )
    runtime_theory_summary = (
        dict(runtime_evidence_summary.get("theory", {}) or {})
        if isinstance(runtime_evidence_summary.get("theory", {}), Mapping)
        else {}
    )
    runtime_theory_summary = _merge_runtime_theory_summaries(
        runtime_theory_summary,
        _runtime_theory_summary_from_result_paths(result_paths),
    )
    derived_formalizer_repair_sequences = (
        _formalizer_lean_candidate_repair_sequences_from_result_paths(result_paths)
    )
    formalizer_repair_sequences = max(
        int(
            manifest.get(
                "n_formalizer_lean_candidate_failed_then_passed_repair_sequences",
                0,
            )
            or 0
        ),
        int(
            runtime_proof_summary.get(
                "n_formalizer_lean_candidate_failed_then_passed_repair_sequences",
                0,
            )
            or 0
        ),
        derived_formalizer_repair_sequences,
    )
    attached_coding_agent_repair_eval = (
        dict(manifest.get("internal_coding_agent_generated_code_repair_eval", {}) or {})
        if isinstance(
            manifest.get("internal_coding_agent_generated_code_repair_eval", {}),
            Mapping,
        )
        else {}
    )
    attached_formalizer_repair_eval = (
        dict(manifest.get("internal_formalizer_lean_candidate_repair_eval", {}) or {})
        if isinstance(
            manifest.get("internal_formalizer_lean_candidate_repair_eval", {}),
            Mapping,
        )
        else {}
    )
    payload: dict[str, Any] = {
        "schema_version": RESEARCH_AGENT_RUNTIME_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_dir": str(runtime_dir),
        "manifest": str(manifest_path),
        "runtime_stage": manifest.get("runtime_stage", ""),
        "runtime_architect_coordinator_registered": bool(
            manifest.get("runtime_architect_coordinator_registered", False)
        ),
        "runtime_architect_coordinator_executed": any(
            row.architect_coordinator_enabled for row in rows
        ),
        "n_runtime_architect_coordinator_traces": sum(
            1
            for row in trace_rows
            if str(row.get("subsystem", "") or "") == "ArchitectCoordinator"
        ),
        "runtime_evaluation_mode": str(manifest.get("runtime_evaluation_mode", "")),
        "effective_formal_verification_policy": str(
            manifest.get("effective_formal_verification_policy", "")
            or manifest.get("formal_verification_policy", "")
            or ""
        ),
        "requested_recommended_research_path": str(
            manifest.get("requested_recommended_research_path", "") or ""
        ),
        "effective_recommended_research_path": str(
            manifest.get("effective_recommended_research_path", "") or ""
        ),
        "runtime_research_path_control_propagated": bool(
            manifest.get("runtime_research_path_control_propagated", False)
        ),
        "runtime_research_path_execution_summary": (
            dict(manifest.get("runtime_research_path_execution_summary", {}) or {})
            if isinstance(
                manifest.get("runtime_research_path_execution_summary", {}),
                Mapping,
            )
            else {}
        ),
        "n_results": len(rows),
        "n_distinct_question_ids": len({row.question_id for row in rows if row.question_id}),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "result_errors": result_errors,
        "n_result_errors": sum(len(row["errors"]) for row in result_errors),
        "by_status": dict(sorted(by_status.items())),
        "n_runtime_progress_events": len(progress_rows),
        "n_runtime_traces": len(trace_rows),
        "n_runtime_next_action_items": len(agenda_rows),
        "n_runtime_learning_rows": len(learning_rows),
        "n_runtime_theorem_reduction_closure_work_orders": int(
            manifest.get("n_runtime_theorem_reduction_closure_work_orders", 0) or 0
        ),
        "has_kernel_evidence": n_kernel_verified_subclaims > 0,
        "has_real_kernel_evidence": n_real_kernel_verified_subclaims > 0,
        "has_non_real_kernel_evidence": n_non_real_kernel_verified_subclaims > 0,
        "n_results_with_kernel_evidence": sum(
            1 for row in rows if row.n_kernel_verified_subclaims > 0
        ),
        "n_results_with_real_kernel_evidence": sum(
            1 for row in rows if row.n_real_kernel_verified_subclaims > 0
        ),
        "n_results_with_non_real_kernel_evidence": sum(
            1 for row in rows if row.n_non_real_kernel_verified_subclaims > 0
        ),
        "n_kernel_verified_subclaims": n_kernel_verified_subclaims,
        "n_real_kernel_verified_subclaims": n_real_kernel_verified_subclaims,
        "n_non_real_kernel_verified_subclaims": n_non_real_kernel_verified_subclaims,
        "kernel_verified_verifiers": sorted(
            {
                verifier
                for row in rows
                for verifier in row.kernel_verified_verifiers
                if verifier
            }
        ),
        "real_kernel_verified_proof_obligation_ids": sorted(
            {
                obligation_id
                for row in rows
                for obligation_id in row.real_kernel_verified_proof_obligation_ids
                if obligation_id
            }
        ),
        "real_kernel_verified_source_theorem_semantic_primitive_ids": sorted(
            {
                obligation_id
                for row in rows
                for obligation_id in row.real_kernel_verified_source_theorem_semantic_primitive_ids
                if obligation_id
            }
        ),
        "n_real_kernel_verified_source_theorem_semantic_primitive_subclaims": sum(
            len(row.real_kernel_verified_source_theorem_semantic_primitive_ids)
            for row in rows
        ),
        "runtime_memory_kernel_verified_proof_obligation_ids": runtime_memory_evidence[
            "kernel_verified_proof_obligation_ids"
        ],
        "runtime_memory_kernel_verified_source_theorem_semantic_primitive_ids": (
            runtime_memory_evidence[
                "kernel_verified_source_theorem_semantic_primitive_ids"
            ]
        ),
        "runtime_memory_kernel_verified_source_theorem_semantic_support_obligation_ids": (
            runtime_memory_evidence[
                "kernel_verified_source_theorem_semantic_support_obligation_ids"
            ]
        ),
        "runtime_memory_kernel_verified_theorem_reduction_closure_work_order_ids": (
            runtime_memory_evidence[
                "kernel_verified_theorem_reduction_closure_work_order_ids"
            ]
        ),
        "runtime_memory_kernel_verified_theorem_reduction_closure_target_ids": (
            runtime_memory_evidence[
                "kernel_verified_theorem_reduction_closure_target_ids"
            ]
        ),
        "runtime_memory_kernel_verified_theorem_reduction_closure_goal_ids": (
            runtime_memory_evidence[
                "kernel_verified_theorem_reduction_closure_goal_ids"
            ]
        ),
        "n_runtime_memory_kernel_verified_proof_obligation_ids": len(
            runtime_memory_evidence["kernel_verified_proof_obligation_ids"]
        ),
        "n_runtime_memory_kernel_verified_source_theorem_semantic_primitive_ids": len(
            runtime_memory_evidence[
                "kernel_verified_source_theorem_semantic_primitive_ids"
            ]
        ),
        "n_runtime_memory_kernel_verified_source_theorem_semantic_support_obligation_ids": len(
            runtime_memory_evidence[
                "kernel_verified_source_theorem_semantic_support_obligation_ids"
            ]
        ),
        "n_runtime_memory_kernel_verified_theorem_reduction_closure_goal_ids": len(
            runtime_memory_evidence[
                "kernel_verified_theorem_reduction_closure_goal_ids"
            ]
        ),
        "n_formal_gaps": sum(row.n_formal_gaps for row in rows),
        "n_registered_proof_bank_obligation_candidates": sum(
            row.n_registered_proof_bank_obligation_candidates for row in rows
        ),
        "n_memory_prioritized_proof_obligations": sum(
            row.n_memory_prioritized_proof_obligations for row in rows
        ),
        "n_memory_off_catalog_proof_obligations": sum(
            row.n_memory_off_catalog_proof_obligations for row in rows
        ),
        "n_memory_rejected_proof_obligations": sum(
            row.n_memory_rejected_proof_obligations for row in rows
        ),
        "n_llm_requested_proof_obligations": sum(
            row.n_llm_requested_proof_obligations for row in rows
        ),
        "n_llm_off_catalog_proof_obligations": sum(
            row.n_llm_off_catalog_proof_obligations for row in rows
        ),
        "n_llm_rejected_proof_obligations": sum(
            row.n_llm_rejected_proof_obligations for row in rows
        ),
        "n_full_frontier_theorem_proved": sum(1 for row in rows if row.full_frontier_theorem_proved),
        "n_algorithm_sandbox_executed": sum(row.n_algorithm_sandbox_executed for row in rows),
        "n_generated_simulation_sandbox_executed": sum(
            row.n_generated_simulation_sandbox_executed for row in rows
        ),
        "n_generated_simulation_sandbox_passed": sum(
            row.n_generated_simulation_sandbox_passed for row in rows
        ),
        "n_generated_simulation_sandbox_metric_gate_failed": sum(
            row.n_generated_simulation_sandbox_metric_gate_failed for row in rows
        ),
        "n_generated_simulation_sandbox_failed_then_passed_repair_sequences": sum(
            row.n_generated_simulation_sandbox_failed_then_passed_repair_sequences
            for row in rows
        ),
        "n_unsafe_generated_simulation_code_rejected": sum(
            row.n_unsafe_generated_simulation_code_rejected for row in rows
        ),
        "n_generated_code_sandbox_executed": sum(
            row.n_generated_code_sandbox_executed for row in rows
        ),
        "n_generated_code_sandbox_metric_gate_failed": sum(
            row.n_generated_code_sandbox_metric_gate_failed for row in rows
        ),
        "n_generated_code_sandbox_failed_then_passed_repair_sequences": sum(
            row.n_generated_code_sandbox_failed_then_passed_repair_sequences
            for row in rows
        ),
        "n_unsafe_generated_code_rejected": sum(
            row.n_unsafe_generated_code_rejected for row in rows
        ),
        "internal_coding_agent_generated_code_repair_eval_attached": bool(
            attached_coding_agent_repair_eval
        ),
        "internal_coding_agent_generated_code_repair_eval_manifest_path": str(
            attached_coding_agent_repair_eval.get("manifest_path", "") or ""
        ),
        "internal_coding_agent_generated_code_repair_eval_live_generator": bool(
            attached_coding_agent_repair_eval.get("live_generator", False)
        ),
        "internal_coding_agent_generated_code_repair_eval_static_or_fixture_only": bool(
            attached_coding_agent_repair_eval.get("static_or_fixture_only", False)
        ),
        "internal_coding_agent_generated_code_repair_eval_capability_evidence_ok": bool(
            attached_coding_agent_repair_eval.get("capability_evidence_ok", False)
        ),
        "internal_coding_agent_generated_code_repair_eval_algorithm_repair_sequences": int(
            attached_coding_agent_repair_eval.get("algorithm_repair_sequences", 0)
            or 0
        ),
        "internal_coding_agent_generated_code_repair_eval_simulation_repair_sequences": int(
            attached_coding_agent_repair_eval.get("simulation_repair_sequences", 0)
            or 0
        ),
        "internal_formalizer_lean_candidate_repair_eval_attached": bool(
            attached_formalizer_repair_eval
        ),
        "internal_formalizer_lean_candidate_repair_eval_manifest_path": str(
            attached_formalizer_repair_eval.get("manifest_path", "") or ""
        ),
        "internal_formalizer_lean_candidate_repair_eval_live_generator": bool(
            attached_formalizer_repair_eval.get("live_generator", False)
        ),
        "internal_formalizer_lean_candidate_repair_eval_static_or_fixture_only": bool(
            attached_formalizer_repair_eval.get("static_or_fixture_only", False)
        ),
        "internal_formalizer_lean_candidate_repair_eval_capability_evidence_ok": bool(
            attached_formalizer_repair_eval.get("capability_evidence_ok", False)
        ),
        "internal_formalizer_lean_candidate_repair_eval_repair_sequences": int(
            attached_formalizer_repair_eval.get("repair_sequences", 0) or 0
        ),
        "internal_formalizer_lean_candidate_repair_eval_local_lean_checked": int(
            attached_formalizer_repair_eval.get("local_lean_checked", 0) or 0
        ),
        "internal_formalizer_lean_candidate_repair_eval_local_lean_compiled": int(
            attached_formalizer_repair_eval.get("local_lean_compiled", 0) or 0
        ),
        "n_llm_formalizer_proof_engineer_proposals": int(
            manifest.get("n_llm_formalizer_proof_engineer_proposals", 0) or 0
        ),
        "n_deterministic_formalizer_work_order_seed_proposals": int(
            manifest.get("n_deterministic_formalizer_work_order_seed_proposals", 0)
            or 0
        ),
        "n_formalizer_lean_candidate_local_lean_checked": int(
            _manifest_or_proof_summary_count(
                manifest,
                runtime_proof_summary,
                "n_formalizer_lean_candidate_local_lean_checked",
            )
        ),
        "n_formalizer_lean_candidate_local_lean_compiled": int(
            _manifest_or_proof_summary_count(
                manifest,
                runtime_proof_summary,
                "n_formalizer_lean_candidate_local_lean_compiled",
            )
        ),
        "n_formalizer_lean_candidate_live_proof_state_requests": int(
            _manifest_or_proof_summary_count(
                manifest,
                runtime_proof_summary,
                "n_formalizer_lean_candidate_live_proof_state_requests",
            )
        ),
        "n_formalizer_lean_candidate_lean_lsp_mcp_ready_requests": int(
            _manifest_or_proof_summary_count(
                manifest,
                runtime_proof_summary,
                "n_formalizer_lean_candidate_lean_lsp_mcp_ready_requests",
            )
        ),
        "n_formalizer_lean_candidate_proof_state_feedback_rows": int(
            _manifest_or_proof_summary_count(
                manifest,
                runtime_proof_summary,
                "n_formalizer_lean_candidate_proof_state_feedback_rows",
            )
        ),
        "n_formalizer_lean_candidate_local_lean_tool_calls": int(
            _manifest_or_proof_summary_count(
                manifest,
                runtime_proof_summary,
                "n_formalizer_lean_candidate_local_lean_tool_calls",
            )
        ),
        "n_formalizer_lean_candidate_lean_lsp_mcp_live_calls": int(
            _manifest_or_proof_summary_count(
                manifest,
                runtime_proof_summary,
                "n_formalizer_lean_candidate_lean_lsp_mcp_live_calls",
            )
        ),
        "n_formalizer_lean_candidate_failed_then_passed_repair_sequences": (
            formalizer_repair_sequences
        ),
        "n_formalizer_lean_candidate_failed_then_passed_repair_sequences_derived_from_results": (
            derived_formalizer_repair_sequences
        ),
        "n_lean_lsp_mcp_live_calls": sum(row.n_lean_lsp_mcp_live_calls for row in rows),
        "source_theorem_promotion_proofengineer_bridge_ran": bool(
            manifest.get("source_theorem_promotion_proofengineer_bridge_ran", False)
        ),
        "source_theorem_promotion_proofengineer_bridge_skipped_reason": str(
            manifest.get("source_theorem_promotion_proofengineer_bridge_skipped_reason", "")
            or ""
        ),
        "source_theorem_promotion_proofengineer_bridge_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_promotion_proofengineer_bridge_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_promotion_source_semantic_proofengineer_bridge_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_promotion_source_semantic_proofengineer_bridge_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_promotion_post_executor_proofengineer_bridge_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_promotion_post_executor_proofengineer_bridge_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_formal_environment_proofengineer_bridge_ran": bool(
            manifest.get("source_theorem_formal_environment_proofengineer_bridge_ran", False)
        )
        or bool(
            manifest.get(
                "source_theorem_formal_environment_from_source_semantic_promotion_bridge_ran",
                False,
            )
        ),
        "source_theorem_formal_environment_proofengineer_bridge_skipped_reason": str(
            manifest.get("source_theorem_formal_environment_proofengineer_bridge_skipped_reason", "")
            or manifest.get(
                "source_theorem_formal_environment_from_source_semantic_promotion_bridge_skipped_reason",
                "",
            )
            or ""
        ),
        "source_theorem_formal_environment_proofengineer_n_signature_probes_reached_proof_body": max(
            int(
                manifest.get(
                    "source_theorem_formal_environment_proofengineer_n_signature_probes_reached_proof_body",
                    0,
                )
                or 0
            ),
            int(
                manifest.get(
                    "source_theorem_formal_environment_from_source_semantic_promotion_bridge_n_proof_body_work_orders",
                    0,
                )
                or 0
            ),
        ),
        "source_theorem_exact_proof_body_repair_executor_ran": bool(
            manifest.get("source_theorem_exact_proof_body_repair_executor_ran", False)
        ),
        "source_theorem_exact_proof_body_repair_executor_n_result_rows": int(
            manifest.get("source_theorem_exact_proof_body_repair_executor_n_result_rows", 0)
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_dominant_failure_classification": str(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_dominant_failure_classification",
                "",
            )
            or ""
        ),
        "source_theorem_exact_proof_body_repair_executor_by_proof_body_gate_status": (
            dict(
                manifest.get(
                    "source_theorem_exact_proof_body_repair_executor_by_proof_body_gate_status",
                    {},
                )
                or {}
            )
            if isinstance(
                manifest.get(
                    "source_theorem_exact_proof_body_repair_executor_by_proof_body_gate_status",
                    {},
                ),
                Mapping,
            )
            else {}
        ),
        "source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_excerpt_rows": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_n_proof_body_goal_excerpt_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_first_proof_body_goal_excerpt": [
            str(value)
            for value in manifest.get(
                "source_theorem_exact_proof_body_repair_executor_first_proof_body_goal_excerpt",
                [],
            )
            or []
            if str(value).strip()
        ][:8],
        "n_runtime_source_theorem_exact_proof_body_repair_work_orders_from_proof_body_adapter_feedback": int(
            manifest.get(
                "n_runtime_source_theorem_exact_proof_body_repair_work_orders_from_proof_body_adapter_feedback",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_ran": bool(
            manifest.get(
                "source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_ran",
                False,
            )
        ),
        "source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_n_rows": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_n_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_n_ready": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_n_ready",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_requested": bool(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_requested",
                False,
            )
        ),
        "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_ran": bool(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_ran",
                False,
            )
        ),
        "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_result_rows": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_result_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_dominant_failure_classification": str(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_dominant_failure_classification",
                "",
            )
            or ""
        ),
        "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_by_proof_body_gate_status": (
            dict(
                manifest.get(
                    "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_by_proof_body_gate_status",
                    {},
                )
                or {}
            )
            if isinstance(
                manifest.get(
                    "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_by_proof_body_gate_status",
                    {},
                ),
                Mapping,
            )
            else {}
        ),
        "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_proof_body_goal_excerpt_rows": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_proof_body_goal_excerpt_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_first_proof_body_goal_excerpt": [
            str(value)
            for value in manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_first_proof_body_goal_excerpt",
                [],
            )
            or []
            if str(value).strip()
        ][:8],
        "n_runtime_source_theorem_semantic_primitive_work_orders_from_proof_body_adapter_feedback": int(
            manifest.get(
                "n_runtime_source_theorem_semantic_primitive_work_orders_from_proof_body_adapter_feedback",
                0,
            )
            or 0
        ),
        "n_runtime_new_source_theorem_semantic_primitive_work_orders_from_proof_body_adapter_feedback": int(
            manifest.get(
                "n_runtime_new_source_theorem_semantic_primitive_work_orders_from_proof_body_adapter_feedback",
                0,
            )
            or 0
        ),
        "n_runtime_source_theorem_exact_semantic_definition_work_orders": int(
            manifest.get(
                "n_runtime_source_theorem_exact_semantic_definition_work_orders",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_source_lookup_required": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_source_lookup_required",
                False,
            )
            or int(
                manifest.get(
                    "n_runtime_source_theorem_exact_semantic_definition_work_orders",
                    0,
                )
                or 0
            )
        ),
        "source_theorem_exact_semantic_definition_source_lookup_ran": bool(
            manifest.get("source_theorem_exact_semantic_definition_source_lookup_ran", False)
        ),
        "source_theorem_exact_semantic_definition_source_lookup_skipped_reason": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_source_lookup_skipped_reason",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_n_closure_review_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_n_closure_review_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_proofengineer_bridge_required": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_proofengineer_bridge_required",
                False,
            )
            or int(
                manifest.get(
                    "source_theorem_exact_semantic_definition_n_closure_review_packets",
                    0,
                )
                or 0
            )
        ),
        "source_theorem_exact_semantic_definition_proofengineer_bridge_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_proofengineer_bridge_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_proofengineer_bridge_skipped_reason": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_proofengineer_bridge_skipped_reason",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_proofengineer_bridge_n_lean_repair_tasks": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_proofengineer_bridge_n_lean_repair_tasks",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_required": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_required",
                False,
            )
            or int(
                manifest.get(
                    "source_theorem_exact_semantic_definition_proofengineer_bridge_n_lean_repair_tasks",
                    0,
                )
                or 0
            )
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_skipped_reason": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_skipped_reason",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_local_lean_requested": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_local_lean_requested",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_n_results": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_n_results",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_n_local_lean_checked": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_n_local_lean_checked",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_n_local_lean_compiled": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_n_local_lean_compiled",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_n_typechecked_candidate_review_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_n_typechecked_candidate_review_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_typechecked_candidate_review_required": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_typechecked_candidate_review_required",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_lean_repair_executor_typechecked_candidate_review_required_reason": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_lean_repair_executor_typechecked_candidate_review_required_reason",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_late_materialized_lean_repair_executor_n_typechecked_candidate_review_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_materialized_lean_repair_executor_n_typechecked_candidate_review_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_materialized_candidate_review_required": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_materialized_candidate_review_required",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_late_materialized_candidate_review_required_reason": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_materialized_candidate_review_required_reason",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_late_lean_repair_executor_n_typechecked_candidate_review_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_lean_repair_executor_n_typechecked_candidate_review_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_lean_repair_executor_typechecked_candidate_review_required": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_lean_repair_executor_typechecked_candidate_review_required",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_late_lean_repair_executor_typechecked_candidate_review_required_reason": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_lean_repair_executor_typechecked_candidate_review_required_reason",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_candidate_synthesis_n_proof_body_recheck_queue_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_candidate_synthesis_n_proof_body_recheck_queue_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_proof_body_recheck_executor_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_proof_body_recheck_executor_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_proof_body_recheck_executor_skipped_reason": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_proof_body_recheck_executor_skipped_reason",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_result_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_result_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_proof_body_recheck_executor_dominant_failure_classification": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_proof_body_recheck_executor_dominant_failure_classification",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_proof_body_recheck_executor_by_proof_body_gate_status": (
            dict(
                manifest.get(
                    "source_theorem_exact_semantic_definition_proof_body_recheck_executor_by_proof_body_gate_status",
                    {},
                )
                or {}
            )
            if isinstance(
                manifest.get(
                    "source_theorem_exact_semantic_definition_proof_body_recheck_executor_by_proof_body_gate_status",
                    {},
                ),
                Mapping,
            )
            else {}
        ),
        "source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_proof_body_goal_excerpt_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_proof_body_goal_excerpt_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_proof_body_recheck_executor_first_proof_body_goal_excerpt": [
            str(value)
            for value in manifest.get(
                "source_theorem_exact_semantic_definition_proof_body_recheck_executor_first_proof_body_goal_excerpt",
                [],
            )
            or []
            if str(value).strip()
        ][:8],
        "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_approved_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_approved_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_blocked_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_blocked_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_verifier_gate_work_orders": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_verifier_gate_work_orders",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_execution_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_execution_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_n_result_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_n_result_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_dominant_failure_classification": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_dominant_failure_classification",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_by_proof_body_gate_status": (
            dict(
                manifest.get(
                    "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_by_proof_body_gate_status",
                    {},
                )
                or {}
            )
            if isinstance(
                manifest.get(
                    "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_by_proof_body_gate_status",
                    {},
                ),
                Mapping,
            )
            else {}
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_n_proof_body_goal_excerpt_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_n_proof_body_goal_excerpt_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_first_proof_body_goal_excerpt": [
            str(value)
            for value in manifest.get(
                "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_first_proof_body_goal_excerpt",
                [],
            )
            or []
            if str(value).strip()
        ][:8],
        "source_theorem_exact_semantic_definition_materialized_lean_repair_executor_n_typechecked_candidate_review_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_lean_repair_executor_n_typechecked_candidate_review_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_candidate_review_required": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_candidate_review_required",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_n_review_typechecked_candidate_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_n_review_typechecked_candidate_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_n_review_typechecked_candidate_packets_with_semantic_review_decision": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_n_review_typechecked_candidate_packets_with_semantic_review_decision",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_n_review_typechecked_candidate_packets_llm_approved": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_n_review_typechecked_candidate_packets_llm_approved",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_approved_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_approved_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_llm_approved_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_llm_approved_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_blocked_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_blocked_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_verifier_gate_work_orders": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_verifier_gate_work_orders",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_execution_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_execution_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_n_result_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_n_result_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_dominant_failure_classification": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_dominant_failure_classification",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_by_proof_body_gate_status": (
            dict(
                manifest.get(
                    "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_by_proof_body_gate_status",
                    {},
                )
                or {}
            )
            if isinstance(
                manifest.get(
                    "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_by_proof_body_gate_status",
                    {},
                ),
                Mapping,
            )
            else {}
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_n_proof_body_goal_excerpt_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_n_proof_body_goal_excerpt_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_first_proof_body_goal_excerpt": [
            str(value)
            for value in manifest.get(
                "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_first_proof_body_goal_excerpt",
                [],
            )
            or []
            if str(value).strip()
        ][:8],
        "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_approved_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_approved_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_blocked_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_blocked_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_verifier_gate_work_orders": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_verifier_gate_work_orders",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_execution_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_execution_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_n_result_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_n_result_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_dominant_failure_classification": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_dominant_failure_classification",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_by_proof_body_gate_status": (
            dict(
                manifest.get(
                    "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_by_proof_body_gate_status",
                    {},
                )
                or {}
            )
            if isinstance(
                manifest.get(
                    "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_by_proof_body_gate_status",
                    {},
                ),
                Mapping,
            )
            else {}
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_n_proof_body_goal_excerpt_rows": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_n_proof_body_goal_excerpt_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_first_proof_body_goal_excerpt": [
            str(value)
            for value in manifest.get(
                "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_first_proof_body_goal_excerpt",
                [],
            )
            or []
            if str(value).strip()
        ][:8],
        "source_theorem_exact_semantic_definition_repair_required": bool(
            manifest.get("source_theorem_exact_semantic_definition_repair_required", False)
        ),
        "source_theorem_exact_semantic_definition_repair_required_reason": str(
            manifest.get("source_theorem_exact_semantic_definition_repair_required_reason", "")
            or ""
        ),
        "n_runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer": int(
            manifest.get(
                "n_runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer",
                0,
            )
            or 0
        ),
        "source_to_bridge_premise_derivation_from_formalizer_bridge_required": bool(
            manifest.get(
                "source_to_bridge_premise_derivation_from_formalizer_bridge_required",
                False,
            )
            or int(
                manifest.get(
                    "n_runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer",
                    0,
                )
                or 0
            )
        ),
        "source_to_bridge_premise_derivation_from_formalizer_bridge_ran": bool(
            manifest.get(
                "source_to_bridge_premise_derivation_from_formalizer_bridge_ran",
                False,
            )
        ),
        "source_to_bridge_premise_derivation_from_formalizer_bridge_skipped_reason": str(
            manifest.get(
                "source_to_bridge_premise_derivation_from_formalizer_bridge_skipped_reason",
                "",
            )
            or ""
        ),
        "source_to_bridge_premise_derivation_from_formalizer_bridge_n_rows": int(
            manifest.get(
                "source_to_bridge_premise_derivation_from_formalizer_bridge_n_rows",
                0,
            )
            or 0
        ),
        "source_to_bridge_premise_derivation_from_formalizer_bridge_n_learning_rows": int(
            manifest.get(
                "source_to_bridge_premise_derivation_from_formalizer_bridge_n_learning_rows",
                0,
            )
            or 0
        ),
        "source_to_bridge_premise_derivation_from_formalizer_bridge_n_local_lean_skipped_not_evidence_eligible": int(
            manifest.get(
                "source_to_bridge_premise_derivation_from_formalizer_bridge_n_local_lean_skipped_not_evidence_eligible",
                0,
            )
            or 0
        ),
        "source_to_bridge_premise_derivation_from_formalizer_bridge_dominant_failure_classification": str(
            manifest.get(
                "source_to_bridge_premise_derivation_from_formalizer_bridge_dominant_failure_classification",
                "",
            )
            or ""
        ),
        "source_to_bridge_premise_derivation_from_formalizer_bridge_by_failure_classification": dict(
            manifest.get(
                "source_to_bridge_premise_derivation_from_formalizer_bridge_by_failure_classification",
                {},
            )
            or {}
        )
        if isinstance(
            manifest.get(
                "source_to_bridge_premise_derivation_from_formalizer_bridge_by_failure_classification",
                {},
            ),
            Mapping,
        )
        else {},
        "n_runtime_source_theorem_proof_body_adapter_work_orders_from_formalizer_premise_derivation_feedback": int(
            manifest.get(
                "n_runtime_source_theorem_proof_body_adapter_work_orders_from_formalizer_premise_derivation_feedback",
                0,
            )
            or 0
        ),
        "n_runtime_source_theorem_proof_body_adapter_work_orders_from_adapter_premise_derivation_feedback": int(
            manifest.get(
                "n_runtime_source_theorem_proof_body_adapter_work_orders_from_adapter_premise_derivation_feedback",
                0,
            )
            or 0
        ),
        "source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_ran": bool(
            manifest.get(
                "source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_ran",
                False,
            )
        ),
        "source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_skipped_reason": str(
            manifest.get(
                "source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_skipped_reason",
                "",
            )
            or ""
        ),
        "source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_n_adapter_kernel_verified": int(
            manifest.get(
                "source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_n_adapter_kernel_verified",
                0,
            )
            or 0
        ),
        "n_runtime_source_theorem_exact_proof_body_repair_work_orders_from_adapter_premise_derivation_feedback": int(
            manifest.get(
                "n_runtime_source_theorem_exact_proof_body_repair_work_orders_from_adapter_premise_derivation_feedback",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_execution_queue_from_adapter_premise_derivation_feedback_ran": bool(
            manifest.get(
                "source_theorem_exact_proof_body_repair_execution_queue_from_adapter_premise_derivation_feedback_ran",
                False,
            )
        ),
        "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_ran": bool(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_ran",
                False,
            )
        ),
        "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_requested": bool(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_requested",
                False,
            )
        ),
        "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_n_result_rows": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_n_result_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_n_source_theorem_kernel_verified": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_n_source_theorem_kernel_verified",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_dominant_failure_classification": str(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_dominant_failure_classification",
                "",
            )
            or ""
        ),
        "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_by_proof_body_gate_status": (
            dict(
                manifest.get(
                    "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_by_proof_body_gate_status",
                    {},
                )
                or {}
            )
            if isinstance(
                manifest.get(
                    "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_by_proof_body_gate_status",
                    {},
                ),
                Mapping,
            )
            else {}
        ),
        "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_n_proof_body_goal_excerpt_rows": int(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_n_proof_body_goal_excerpt_rows",
                0,
            )
            or 0
        ),
        "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_first_proof_body_goal_excerpt": [
            str(value)
            for value in manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_first_proof_body_goal_excerpt",
                [],
            )
            or []
            if str(value).strip()
        ][:8],
        "source_theorem_proof_body_adapter_proofengineer_bridge_required": bool(
            manifest.get(
                "source_theorem_proof_body_adapter_required",
                False,
            )
            or int(
                manifest.get(
                    "n_runtime_source_theorem_proof_body_adapter_work_orders",
                    0,
                )
                or 0
            )
        ),
        "source_theorem_proof_body_adapter_proofengineer_bridge_ran": bool(
            manifest.get(
                "source_theorem_proof_body_adapter_proofengineer_bridge_ran",
                False,
            )
        ),
        "source_theorem_proof_body_adapter_proofengineer_bridge_n_rows": int(
            manifest.get(
                "source_theorem_proof_body_adapter_proofengineer_bridge_n_rows",
                0,
            )
            or 0
        ),
        "source_theorem_proof_body_adapter_proofengineer_bridge_skipped_reason": str(
            manifest.get(
                "source_theorem_proof_body_adapter_proofengineer_bridge_skipped_reason",
                "",
            )
            or (
                ""
                if manifest.get(
                    "source_theorem_proof_body_adapter_proofengineer_bridge_ran",
                    False,
                )
                else "adapter_bridge_not_run"
            )
        ),
        "source_theorem_formal_environment_proof_body_executor_ran": bool(
            manifest.get("source_theorem_formal_environment_proof_body_executor_ran", False)
        )
        or bool(
            manifest.get(
                "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_ran",
                False,
            )
        )
        or bool(manifest.get("source_theorem_exact_proof_body_repair_executor_ran", False))
        or bool(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_ran",
                False,
            )
        )
        or bool(
            manifest.get(
                "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_ran",
                False,
            )
        ),
        "source_theorem_formal_environment_proof_body_executor_local_lean_requested": bool(
            manifest.get(
                "source_theorem_formal_environment_proof_body_executor_local_lean_requested",
                False,
            )
        ),
        "source_theorem_formal_environment_proof_body_executor_n_result_rows": _runtime_manifest_int_sum(
            manifest,
            SOURCE_THEOREM_AUDIT_FORMAL_ENV_AGGREGATE_RESULT_ROW_KEYS,
        ),
        "source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified": _runtime_manifest_int_sum(
            manifest,
            SOURCE_THEOREM_AUDIT_FORMAL_ENV_AGGREGATE_KERNEL_EVIDENCE_KEYS,
        ),
        "architect_coordinator_enabled": any(row.architect_coordinator_enabled for row in rows),
        "llm_topology_policy_ok": not topology_errors,
        "unsupported_generator_backends_enabled": _topology_unsupported_count(manifest),
        "n_live_generator_agents_enabled": _topology_live_generator_count(manifest),
        "n_critic_reroutes": sum(row.n_critic_reroutes for row in rows),
        "n_results_with_runtime_learning_memory_input": sum(
            1 for row in rows if row.has_runtime_learning_memory_input
        ),
        "n_results_with_kernel_verified_theorem_reduction_closure_memory": sum(
            1 for row in rows if row.has_kernel_verified_theorem_reduction_closure_memory
        ),
        "n_results_with_source_theorem_semantic_primitive_target_mode": sum(
            1 for row in rows if row.has_source_theorem_semantic_primitive_target_mode
        ),
        "n_runtime_learning_memory_input_rows": runtime_learning_memory_rows_loaded,
        "runtime_learning_memory_input_supplied": runtime_learning_memory_supplied,
        "n_results_with_problem_analysis": sum(1 for row in rows if row.has_problem_analysis),
        "n_results_with_stat_knowledge_bank_plan": sum(
            1 for row in rows if row.has_stat_knowledge_bank_plan
        ),
        "n_results_with_literature_fair_comparison_plan": sum(
            1 for row in rows if row.has_literature_fair_comparison_plan
        ),
        "n_theory_derivation_packets": int(
            runtime_theory_summary.get("n_theory_derivation_packets", 0) or 0
        ),
        "n_theory_derivation_packets_with_contract": int(
            runtime_theory_summary.get(
                "n_theory_derivation_packets_with_contract",
                0,
            )
            or 0
        ),
        "n_theory_derivation_packets_with_min_derivation_steps": int(
            runtime_theory_summary.get(
                "n_theory_derivation_packets_with_min_derivation_steps",
                0,
            )
            or 0
        ),
        "n_theory_derivation_packets_with_equation_chain": int(
            runtime_theory_summary.get(
                "n_theory_derivation_packets_with_equation_chain",
                0,
            )
            or 0
        ),
        "n_theory_derivation_packets_with_assumption_ledger": int(
            runtime_theory_summary.get(
                "n_theory_derivation_packets_with_assumption_ledger",
                0,
            )
            or 0
        ),
        "n_theory_derivation_packets_with_formalization_handoff": int(
            runtime_theory_summary.get(
                "n_theory_derivation_packets_with_formalization_handoff",
                0,
            )
            or 0
        ),
        "n_theory_trace_consumption_contracts": int(
            runtime_theory_summary.get(
                "n_theory_trace_consumption_contracts",
                0,
            )
            or 0
        ),
        "n_theory_trace_consumption_contracts_with_trace": int(
            runtime_theory_summary.get(
                "n_theory_trace_consumption_contracts_with_trace",
                0,
            )
            or 0
        ),
        "n_theory_trace_consumption_contracts_with_equation_chain": int(
            runtime_theory_summary.get(
                "n_theory_trace_consumption_contracts_with_equation_chain",
                0,
            )
            or 0
        ),
        "n_theory_trace_consumption_contracts_with_assumption_ledger": int(
            runtime_theory_summary.get(
                "n_theory_trace_consumption_contracts_with_assumption_ledger",
                0,
            )
            or 0
        ),
        "n_theory_trace_consumption_contracts_with_formalization_handoff": int(
            runtime_theory_summary.get(
                "n_theory_trace_consumption_contracts_with_formalization_handoff",
                0,
            )
            or 0
        ),
        "n_theory_trace_alignment_contracts": int(
            runtime_theory_summary.get(
                "n_theory_trace_alignment_contracts",
                0,
            )
            or 0
        ),
        "n_theory_trace_alignment_contracts_with_llm_alignment": int(
            runtime_theory_summary.get(
                "n_theory_trace_alignment_contracts_with_llm_alignment",
                0,
            )
            or 0
        ),
        "n_structured_theory_trace_alignment_contracts": int(
            runtime_theory_summary.get(
                "n_structured_theory_trace_alignment_contracts",
                0,
            )
            or 0
        ),
        "n_theory_trace_alignment_contracts_with_unsupported_anchors": int(
            runtime_theory_summary.get(
                "n_theory_trace_alignment_contracts_with_unsupported_anchors",
                0,
            )
            or 0
        ),
        "theory_trace_consuming_subsystems": list(
            runtime_theory_summary.get("theory_trace_consuming_subsystems", [])
            if isinstance(
                runtime_theory_summary.get("theory_trace_consuming_subsystems", []),
                list,
            )
            else []
        ),
        "structured_theory_trace_consuming_subsystems": list(
            runtime_theory_summary.get(
                "structured_theory_trace_consuming_subsystems",
                [],
            )
            if isinstance(
                runtime_theory_summary.get(
                    "structured_theory_trace_consuming_subsystems",
                    [],
                ),
                list,
            )
            else []
        ),
        "required_theory_trace_consumers": list(
            runtime_theory_summary.get("required_theory_trace_consumers", [])
            if isinstance(
                runtime_theory_summary.get("required_theory_trace_consumers", []),
                list,
            )
            else []
        ),
        "all_required_theory_trace_consumers_observed": bool(
            runtime_theory_summary.get(
                "all_required_theory_trace_consumers_observed",
                False,
            )
        ),
        "theory_trace_aligned_subsystems": list(
            runtime_theory_summary.get("theory_trace_aligned_subsystems", [])
            if isinstance(
                runtime_theory_summary.get("theory_trace_aligned_subsystems", []),
                list,
            )
            else []
        ),
        "structured_theory_trace_aligned_subsystems": list(
            runtime_theory_summary.get(
                "structured_theory_trace_aligned_subsystems",
                [],
            )
            if isinstance(
                runtime_theory_summary.get(
                    "structured_theory_trace_aligned_subsystems",
                    [],
                ),
                list,
            )
            else []
        ),
        "all_required_theory_trace_alignment_consumers_observed": bool(
            runtime_theory_summary.get(
                "all_required_theory_trace_alignment_consumers_observed",
                False,
            )
        ),
        "theory_trace_consumption_boundary": str(
            runtime_theory_summary.get("theory_trace_consumption_boundary", "") or ""
        ),
        "theory_trace_alignment_boundary": str(
            runtime_theory_summary.get("theory_trace_alignment_boundary", "") or ""
        ),
        "structured_theory_derivation_trace_observed": bool(
            runtime_theory_summary.get(
                "structured_derivation_trace_observed",
                False,
            )
        ),
        "theory_derivation_trace_boundary": str(
            runtime_theory_summary.get("boundary", "") or ""
        ),
        "has_kernel_evidence": any(row.n_kernel_verified_subclaims > 0 for row in rows),
        "has_formal_gaps": any(row.n_formal_gaps > 0 for row in rows),
        "rows": [asdict(row) for row in rows],
        "dataset_fingerprint": stable_hash(
            {
                "rows": [asdict(row) for row in rows],
                "agenda": agenda_rows,
                "learning": learning_rows,
                "progress": progress_rows,
            }
        ),
        "limitations": [
            "runtime audit validates orchestration artifacts and evidence boundaries, not theorem truth",
            "kernel evidence is counted only from formalization manifests with kernel_verified subclaims",
            "full frontier theorem proof remains false unless a separate kernel-verified reduction closes formal gaps",
        ],
    }
    capability_scorecard = _runtime_capability_scorecard(payload)
    payload["capability_scorecard"] = capability_scorecard
    payload["capability_ladder"] = _runtime_capability_ladder(payload)
    payload["evidence_truth_table"] = _runtime_evidence_truth_table(payload)
    capability_gaps = _runtime_capability_gaps_from_scorecard(capability_scorecard)
    payload["capability_ready_for_full_ai_statistician"] = not capability_gaps
    payload["capability_status"] = (
        "FULL_AUTONOMOUS_AI_STATISTICIAN_READY"
        if not capability_gaps
        else (
            "CONTRACT_OK_WITH_CAPABILITY_GAPS"
            if payload["all_ok"]
            else "CONTRACT_ERRORS_AND_CAPABILITY_GAPS"
        )
    )
    payload["capability_gaps"] = capability_gaps
    payload["readiness_boundary"] = (
        "all_ok only means runtime artifacts satisfy the audit contract. "
        "capability_ready_for_full_ai_statistician is the stricter gate for the "
        "original goal: live Architect orchestration, executable algorithm feedback, "
        "live Lean LSP/MCP proof-state interaction, real kernel evidence, and no "
        "remaining full-theorem formal gaps."
    )
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_out = out_dir / "research_agent_runtime_audit_manifest.json"
        report_out = out_dir / "research_agent_runtime_audit.md"
        manifest_out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        report_out.write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _audit_result_path(path: Path) -> RuntimeAuditRow:
    errors: list[str] = []
    data = _load_json(path, errors)
    blackboard = data.get("blackboard", {}) if isinstance(data.get("blackboard"), Mapping) else {}
    artifacts = blackboard.get("artifacts", {}) if isinstance(blackboard.get("artifacts"), Mapping) else {}
    traces = data.get("traces", []) if isinstance(data.get("traces"), list) else []
    subsystem_sequence = [str(row.get("subsystem", "")) for row in traces if isinstance(row, Mapping)]
    architect_enabled = bool(subsystem_sequence and subsystem_sequence[0] == "ArchitectCoordinator")
    architect_resume = architect_enabled and _trace_is_architect_resume(traces)
    expected_sequence = (
        ("ArchitectCoordinator",)
        if architect_resume
        else REQUIRED_ARCHITECT_SUBSYSTEMS
        if architect_enabled
        else REQUIRED_SUBSYSTEMS
    )
    if tuple(subsystem_sequence[: len(expected_sequence)]) != expected_sequence:
        errors.append("runtime trace subsystem order is incomplete or misordered")
    if architect_resume and len(subsystem_sequence) > 1:
        pending_owner = _architect_resume_pending_owner(traces)
        if pending_owner and subsystem_sequence[1] != pending_owner:
            errors.append(
                "architect resume review did not route to the original pending subsystem"
            )
    if data.get("status") != "ACCEPTED":
        errors.append("runtime result status is not ACCEPTED")

    retrieval = _artifacts_with_prefix(artifacts, "retrieval_memory_manifest:")
    theory = _artifacts_with_prefix(artifacts, "theory_derivation:")
    simulation = _artifacts_with_prefix(artifacts, "simulation_manifest:")
    algorithm = _artifacts_with_prefix(artifacts, "algorithm_sandbox_manifest:")
    formalization = _artifacts_with_prefix(artifacts, "formalization_manifest:")
    proof_state_feedback = _proof_state_feedback_artifacts(artifacts)
    critic = _artifacts_with_prefix(artifacts, "critic_evaluator_manifest:")
    required_counts = {
        "retrieval manifest": retrieval,
        "theory packet": theory,
        "simulation manifest": simulation,
        "formalization manifest": formalization,
        "critic manifest": critic,
    }
    for label, rows in required_counts.items():
        if not rows:
            errors.append(f"missing {label}")
    if not algorithm:
        errors.append("missing algorithm sandbox manifest")

    n_kernel = 0
    n_real_kernel = 0
    n_non_real_kernel = 0
    kernel_verified_verifiers: set[str] = set()
    real_kernel_verified_proof_obligation_ids: list[str] = []
    real_kernel_verified_source_theorem_semantic_primitive_ids: list[str] = []
    n_formal_gaps = 0
    n_registered_proof_bank_obligation_candidates = 0
    n_memory_prioritized_proof_obligations = 0
    n_memory_off_catalog_proof_obligations = 0
    n_memory_rejected_proof_obligations = 0
    n_llm_requested_proof_obligations = 0
    n_llm_off_catalog_proof_obligations = 0
    n_llm_rejected_proof_obligations = 0
    full_frontier_theorem_proved = False
    has_kernel_verified_theorem_reduction_closure_memory = False
    has_source_theorem_semantic_primitive_target_mode = False
    for manifest in formalization:
        counts = manifest.get("counts", {}) if isinstance(manifest.get("counts"), Mapping) else {}
        control = (
            manifest.get("proof_obligation_control", {})
            if isinstance(manifest.get("proof_obligation_control"), Mapping)
            else {}
        )
        memory_summary = (
            manifest.get("proof_bank_runtime_memory_summary", {})
            if isinstance(manifest.get("proof_bank_runtime_memory_summary"), Mapping)
            else {}
        )
        if (
            control.get("theorem_reduction_closure_already_kernel_verified") is True
            or memory_summary.get("theorem_reduction_closure_already_kernel_verified") is True
        ):
            has_kernel_verified_theorem_reduction_closure_memory = True
        if (
            memory_summary.get("recommended_formalizer_target_mode")
            == "source_theorem_semantic_primitive_closure"
        ):
            has_source_theorem_semantic_primitive_target_mode = True
        n_kernel += int(counts.get("kernel_verified", 0) or 0)
        for subclaim in manifest.get("formal_subclaims", []) or []:
            if not isinstance(subclaim, Mapping) or subclaim.get("kernel_verified") is not True:
                continue
            verifier = str(subclaim.get("verifier", "") or "unknown")
            kernel_verified_verifiers.add(verifier)
            proof_obligation_id = str(subclaim.get("proof_obligation_id", "") or "").strip()
            if verifier in REAL_KERNEL_VERIFIERS:
                n_real_kernel += 1
                if proof_obligation_id:
                    real_kernel_verified_proof_obligation_ids.append(proof_obligation_id)
                    if _proof_obligation_has_tag(
                        proof_obligation_id,
                        "source_theorem_semantic_primitive",
                    ):
                        real_kernel_verified_source_theorem_semantic_primitive_ids.append(
                            proof_obligation_id
                        )
            else:
                n_non_real_kernel += 1
        n_formal_gaps += int(counts.get("formal_gap", 0) or 0)
        n_registered_proof_bank_obligation_candidates += len(
            manifest.get("registered_proof_bank_obligation_catalog", []) or []
        )
        n_memory_prioritized_proof_obligations += len(
            control.get("memory_prioritized_proof_obligation_ids", []) or []
        )
        n_memory_off_catalog_proof_obligations += len(
            control.get("memory_off_catalog_proof_obligation_ids", []) or []
        )
        n_memory_rejected_proof_obligations += len(
            control.get("memory_rejected_proof_obligation_ids", []) or []
        )
        n_llm_requested_proof_obligations += len(
            control.get("llm_requested_proof_obligation_ids", []) or []
        )
        n_llm_off_catalog_proof_obligations += len(
            control.get("llm_off_catalog_proof_obligation_ids", []) or []
        )
        n_llm_rejected_proof_obligations += len(
            control.get("llm_rejected_proof_obligation_ids", []) or []
        )
        if manifest.get("full_frontier_theorem_proved") is True:
            full_frontier_theorem_proved = True
            if int(counts.get("formal_gap", 0) or 0) > 0:
                errors.append("full_frontier_theorem_proved=true while formal gaps remain")
            if int(counts.get("kernel_verified", 0) or 0) <= 0:
                errors.append("full_frontier_theorem_proved=true without kernel-verified subclaims")
    if n_kernel != n_real_kernel + n_non_real_kernel:
        errors.append(
            "formalization manifest kernel_verified count does not match kernel-verified subclaim rows"
        )
    if n_non_real_kernel:
        errors.append(
            "kernel_verified subclaims use non-real verifier(s): "
            + ",".join(
                sorted(verifier for verifier in kernel_verified_verifiers if verifier not in REAL_KERNEL_VERIFIERS)
            )
        )
    n_agenda = sum(
        len(row.get("next_action_agenda", []) or [])
        for row in critic
        if isinstance(row.get("next_action_agenda", []), list)
    )
    n_learning = sum(
        len(row.get("learning_rows", []) or [])
        for row in critic
        if isinstance(row.get("learning_rows", []), list)
    )
    if n_agenda <= 0:
        errors.append("critic evaluator agenda is empty")
    if n_learning <= 0:
        errors.append("critic evaluator learning rows are empty")
    n_algorithm_sandbox_executed = sum(
        int(row.get("n_executed", 0) or 0)
        for row in algorithm
    )
    n_generated_simulation_sandbox_executed = sum(
        int(row.get("n_generated_simulation_sandbox_executed", 0) or 0)
        for row in simulation
    )
    n_generated_simulation_sandbox_passed = sum(
        int(row.get("n_generated_simulation_sandbox_passed", 0) or 0)
        for row in simulation
    )
    n_generated_simulation_sandbox_metric_gate_failed = sum(
        int(row.get("n_generated_simulation_sandbox_metric_gate_failed", 0) or 0)
        for row in simulation
    )
    repair_sequences = _generated_sandbox_repair_sequence_counts(artifacts)
    n_generated_simulation_sandbox_failed_then_passed_repair_sequences = int(
        repair_sequences.get(
            "n_generated_simulation_sandbox_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    n_unsafe_generated_simulation_code_rejected = sum(
        int(row.get("n_unsafe_generated_simulation_code_rejected", 0) or 0)
        for row in simulation
    )
    n_generated_code_sandbox_executed = sum(
        int(row.get("n_generated_code_executed", 0) or 0)
        for row in algorithm
    )
    n_generated_code_sandbox_metric_gate_failed = sum(
        int(row.get("n_metric_gate_failed", 0) or 0)
        for row in algorithm
    )
    n_generated_code_sandbox_failed_then_passed_repair_sequences = int(
        repair_sequences.get(
            "n_generated_code_sandbox_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    n_unsafe_generated_code_rejected = sum(
        int(row.get("n_unsafe_generated_code_rejected", 0) or 0)
        for row in algorithm
    )
    n_critic_reroutes = sum(
        1
        for row in critic
        if isinstance(row.get("runtime_reroute_decision"), Mapping)
        and row.get("runtime_reroute_decision", {}).get("reroute_to_theory_developer") is True
    )
    n_lean_lsp_mcp_live_calls = sum(
        1 for row in proof_state_feedback if row.get("lean_lsp_mcp_live_called") is True
    )
    if not any(
        isinstance(row.get("runtime_reroute_decision"), Mapping)
        for row in critic
    ):
        errors.append("critic evaluator reroute decision is missing")
    has_runtime_learning_memory_input = _trace_has_runtime_learning_memory_input(traces)
    has_problem_analysis = _trace_has_architect_runtime_field(traces, "problem_analysis")
    has_stat_knowledge_bank_plan = _trace_has_architect_runtime_field(traces, "stat_knowledge_bank_plan")
    has_literature_fair_comparison_plan = _trace_has_architect_runtime_field(
        traces,
        "literature_fair_comparison_plan",
    )
    if architect_enabled:
        if not has_problem_analysis:
            errors.append("Architect runtime plan missing problem_analysis")
        if not has_stat_knowledge_bank_plan:
            errors.append("Architect runtime plan missing stat_knowledge_bank_plan")
        if not has_literature_fair_comparison_plan:
            errors.append("Architect runtime plan missing literature_fair_comparison_plan")
    question_id = str(
        data.get("blackboard", {}).get("project_id", "").split(":", 1)[-1]
        if isinstance(data.get("blackboard"), Mapping)
        else ""
    )
    return RuntimeAuditRow(
        question_id=question_id,
        result_path=str(path),
        ok=not errors,
        status=str(data.get("status", "")),
        n_traces=len(traces),
        n_retrieval_manifests=len(retrieval),
        n_theory_packets=len(theory),
        n_simulation_manifests=len(simulation),
        n_generated_simulation_sandbox_executed=n_generated_simulation_sandbox_executed,
        n_generated_simulation_sandbox_passed=n_generated_simulation_sandbox_passed,
        n_generated_simulation_sandbox_metric_gate_failed=(
            n_generated_simulation_sandbox_metric_gate_failed
        ),
        n_generated_simulation_sandbox_failed_then_passed_repair_sequences=(
            n_generated_simulation_sandbox_failed_then_passed_repair_sequences
        ),
        n_unsafe_generated_simulation_code_rejected=n_unsafe_generated_simulation_code_rejected,
        n_algorithm_manifests=len(algorithm),
        n_algorithm_sandbox_executed=n_algorithm_sandbox_executed,
        n_generated_code_sandbox_executed=n_generated_code_sandbox_executed,
        n_generated_code_sandbox_metric_gate_failed=n_generated_code_sandbox_metric_gate_failed,
        n_generated_code_sandbox_failed_then_passed_repair_sequences=(
            n_generated_code_sandbox_failed_then_passed_repair_sequences
        ),
        n_unsafe_generated_code_rejected=n_unsafe_generated_code_rejected,
        n_formalization_manifests=len(formalization),
        n_critic_manifests=len(critic),
        n_kernel_verified_subclaims=n_kernel,
        n_real_kernel_verified_subclaims=n_real_kernel,
        n_non_real_kernel_verified_subclaims=n_non_real_kernel,
        kernel_verified_verifiers=tuple(sorted(kernel_verified_verifiers)),
        real_kernel_verified_proof_obligation_ids=tuple(
            dict.fromkeys(real_kernel_verified_proof_obligation_ids)
        ),
        real_kernel_verified_source_theorem_semantic_primitive_ids=tuple(
            dict.fromkeys(real_kernel_verified_source_theorem_semantic_primitive_ids)
        ),
        n_formal_gaps=n_formal_gaps,
        n_registered_proof_bank_obligation_candidates=n_registered_proof_bank_obligation_candidates,
        n_memory_prioritized_proof_obligations=n_memory_prioritized_proof_obligations,
        n_memory_off_catalog_proof_obligations=n_memory_off_catalog_proof_obligations,
        n_memory_rejected_proof_obligations=n_memory_rejected_proof_obligations,
        n_llm_requested_proof_obligations=n_llm_requested_proof_obligations,
        n_llm_off_catalog_proof_obligations=n_llm_off_catalog_proof_obligations,
        n_llm_rejected_proof_obligations=n_llm_rejected_proof_obligations,
        full_frontier_theorem_proved=full_frontier_theorem_proved,
        n_agenda_items=n_agenda,
        n_learning_rows=n_learning,
        architect_coordinator_enabled=architect_enabled,
        n_critic_reroutes=n_critic_reroutes,
        n_lean_lsp_mcp_live_calls=n_lean_lsp_mcp_live_calls,
        has_runtime_learning_memory_input=has_runtime_learning_memory_input,
        has_kernel_verified_theorem_reduction_closure_memory=(
            has_kernel_verified_theorem_reduction_closure_memory
        ),
        has_source_theorem_semantic_primitive_target_mode=(
            has_source_theorem_semantic_primitive_target_mode
        ),
        has_problem_analysis=has_problem_analysis,
        has_stat_knowledge_bank_plan=has_stat_knowledge_bank_plan,
        has_literature_fair_comparison_plan=has_literature_fair_comparison_plan,
        errors=tuple(errors),
    )


def _audit_topology(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    topology = manifest.get("llm_runtime_topology", {})
    if not isinstance(topology, Mapping):
        return ["missing llm_runtime_topology"]
    if topology.get("policy_status") != "OK":
        errors.append("llm_runtime_topology policy_status is not OK")
    counts = topology.get("counts", {}) if isinstance(topology.get("counts"), Mapping) else {}
    unsupported = int(counts.get("unsupported_generator_backends_enabled", 0) or 0)
    if unsupported:
        errors.append(f"unsupported generator backends enabled: {unsupported}")
    subsystem_tier_mismatches = int(
        counts.get("subsystem_model_tier_policy_mismatches", 0) or 0
    )
    if subsystem_tier_mismatches:
        errors.append(
            "subsystem model tier policy mismatches: "
            + str(subsystem_tier_mismatches)
        )
    policy = topology.get("policy", {}) if isinstance(topology.get("policy"), Mapping) else {}
    supported = set(str(item) for item in policy.get("supported_generator_providers", []) or [])
    if supported and supported != SUPPORTED_GENERATOR_PROVIDERS:
        errors.append(
            "supported generator providers changed: "
            + ",".join(sorted(supported))
        )
    resolved_status = str(
        policy.get("resolved_claude_model_tier_policy_status", "")
    )
    if resolved_status and resolved_status != "OK":
        errors.append(
            "resolved Claude model tier policy status is not OK: "
            + resolved_status
        )
    resolved_violations = policy.get(
        "resolved_claude_model_tier_policy_violations",
        [],
    )
    if isinstance(resolved_violations, list) and resolved_violations:
        errors.append(
            "resolved Claude model tier policy violations: "
            + "; ".join(str(item) for item in resolved_violations)
        )
    resolved_models = policy.get("resolved_claude_models_by_tier", {})
    if isinstance(resolved_models, Mapping):
        missing_tiers = sorted({"haiku", "sonnet", "opus"} - set(resolved_models))
        if missing_tiers:
            errors.append(
                "resolved Claude model tier map missing: "
                + ",".join(missing_tiers)
            )
    agents = topology.get("llm_agents", []) if isinstance(topology.get("llm_agents"), list) else []
    for agent in agents:
        if not isinstance(agent, Mapping) or not agent.get("enabled"):
            continue
        if agent.get("generator_only") is not True:
            errors.append(f"{agent.get('subsystem')} is not generator_only")
        if agent.get("acts_in_environment") is not False:
            errors.append(f"{agent.get('subsystem')} acts_in_environment is not false")
        provider_names = {
            str(agent.get("provider_name", "") or "").strip().lower(),
            str(agent.get("backend_provider_name", "") or "").strip().lower(),
        }
        provider_names.discard("")
        unsupported_names = sorted(provider_names - SUPPORTED_GENERATOR_PROVIDERS)
        if unsupported_names:
            errors.append(
                f"{agent.get('subsystem')} uses unsupported provider(s): "
                + ",".join(unsupported_names)
            )
        expected_tier = str(agent.get("expected_model_tier", "") or "").strip().lower()
        configured_tier = str(agent.get("model_tier", "") or "").strip().lower()
        if expected_tier and expected_tier != "auto" and configured_tier != expected_tier:
            errors.append(
                f"{agent.get('subsystem')} expected model_tier {expected_tier} "
                f"but is configured with {configured_tier or 'missing'}"
            )
    return sorted(set(errors))


def _trace_is_architect_resume(traces: list[Any]) -> bool:
    if not traces:
        return False
    first = traces[0]
    if not isinstance(first, Mapping):
        return False
    if str(first.get("subsystem", "") or "") != "ArchitectCoordinator":
        return False
    task = first.get("task", {})
    if not isinstance(task, Mapping):
        return False
    if str(task.get("task_id", "") or "").startswith("architect-resume:"):
        return True
    inputs = task.get("inputs", {})
    return (
        isinstance(inputs, Mapping)
        and isinstance(inputs.get("resume_pending_task", {}), Mapping)
        and bool(inputs.get("resume_pending_task", {}))
    )


def _architect_resume_pending_owner(traces: list[Any]) -> str:
    if not traces or not isinstance(traces[0], Mapping):
        return ""
    task = traces[0].get("task", {})
    if not isinstance(task, Mapping):
        return ""
    inputs = task.get("inputs", {})
    if not isinstance(inputs, Mapping):
        return ""
    pending = inputs.get("resume_pending_task", {})
    if not isinstance(pending, Mapping):
        return ""
    return str(pending.get("owner_subsystem", "") or "")


def _topology_unsupported_count(manifest: Mapping[str, Any]) -> int:
    topology = manifest.get("llm_runtime_topology", {})
    if not isinstance(topology, Mapping):
        return 0
    counts = topology.get("counts", {}) if isinstance(topology.get("counts"), Mapping) else {}
    return int(counts.get("unsupported_generator_backends_enabled", 0) or 0)


def _topology_live_generator_count(manifest: Mapping[str, Any]) -> int:
    topology = manifest.get("llm_runtime_topology", {})
    if not isinstance(topology, Mapping):
        return 0
    counts = topology.get("counts", {}) if isinstance(topology.get("counts"), Mapping) else {}
    by_provider = counts.get("enabled_by_provider", {})
    if not isinstance(by_provider, Mapping):
        return 0
    return sum(
        int(by_provider.get(provider, 0) or 0)
        for provider in ("anthropic", "openai")
    )


def _runtime_capability_gaps(payload: Mapping[str, Any]) -> list[str]:
    return _runtime_capability_gaps_from_scorecard(_runtime_capability_scorecard(payload))


def _payload_source_theorem_kernel_count(payload: Mapping[str, Any]) -> int:
    return sum(
        int(payload.get(key, 0) or 0)
        for key in SOURCE_THEOREM_AUDIT_KERNEL_EVIDENCE_COUNT_KEYS
    )


def _runtime_capability_gaps_from_scorecard(
    scorecard: Mapping[str, Any],
) -> list[str]:
    rows = scorecard.get("rows", []) if isinstance(scorecard, Mapping) else []
    gaps: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if row.get("passed") is True:
            continue
        blocker = str(row.get("blocker", "")).strip()
        if blocker:
            gaps.append(blocker)
    return gaps


def _runtime_learning_memory_evidence(traces: list[Any]) -> dict[str, list[str]]:
    proof_obligation_ids: list[str] = []
    source_semantic_ids: list[str] = []
    source_semantic_support_obligation_ids: list[str] = []
    closure_work_order_ids: list[str] = []
    closure_target_ids: list[str] = []
    closure_goal_ids: list[str] = []
    for trace in traces:
        if not isinstance(trace, Mapping):
            continue
        task = trace.get("task", {}) if isinstance(trace.get("task"), Mapping) else {}
        inputs = task.get("inputs", {}) if isinstance(task.get("inputs"), Mapping) else {}
        context = inputs.get("architect_context", {}) if isinstance(inputs.get("architect_context"), Mapping) else {}
        memory = context.get("runtime_learning_memory", {})
        if not isinstance(memory, Mapping) or memory.get("artifact_kind") != "RuntimeLearningMemoryContext":
            continue
        rows = memory.get("rows", []) if isinstance(memory.get("rows"), list) else []
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            _extend_unique_from_row(
                proof_obligation_ids,
                row,
                "kernel_verified_proof_obligation_ids",
            )
            _extend_unique_from_row(
                source_semantic_support_obligation_ids,
                row,
                "kernel_verified_source_theorem_semantic_support_obligation_ids",
            )
            for obligation_id in proof_obligation_ids:
                if _proof_obligation_has_tag(
                    obligation_id,
                    "source_theorem_semantic_primitive",
                ):
                    _append_unique(source_semantic_ids, obligation_id)
            _extend_unique_from_row(
                closure_work_order_ids,
                row,
                "kernel_verified_theorem_reduction_closure_work_order_ids",
            )
            _extend_unique_from_row(
                closure_target_ids,
                row,
                "kernel_verified_theorem_reduction_closure_target_ids",
            )
            _extend_unique_from_row(
                closure_goal_ids,
                row,
                "kernel_verified_theorem_reduction_closure_goal_ids",
            )
            input_summary = row.get("input_summary", {})
            if isinstance(input_summary, Mapping):
                _extend_unique_from_row(
                    proof_obligation_ids,
                    input_summary,
                    "kernel_verified_proof_obligation_ids",
                )
                _extend_unique_from_row(
                    source_semantic_support_obligation_ids,
                    input_summary,
                    "kernel_verified_source_theorem_semantic_support_obligation_ids",
                )
                for obligation_id in proof_obligation_ids:
                    if _proof_obligation_has_tag(
                        obligation_id,
                        "source_theorem_semantic_primitive",
                    ):
                        _append_unique(source_semantic_ids, obligation_id)
                _extend_unique_from_row(
                    closure_work_order_ids,
                    input_summary,
                    "kernel_verified_theorem_reduction_closure_work_order_ids",
                )
                _extend_unique_from_row(
                    closure_target_ids,
                    input_summary,
                    "kernel_verified_theorem_reduction_closure_target_ids",
                )
                _extend_unique_from_row(
                    closure_goal_ids,
                    input_summary,
                    "kernel_verified_theorem_reduction_closure_goal_ids",
                )
    return {
        "kernel_verified_proof_obligation_ids": proof_obligation_ids,
        "kernel_verified_source_theorem_semantic_support_obligation_ids": (
            source_semantic_support_obligation_ids or source_semantic_ids
        ),
        "kernel_verified_source_theorem_semantic_primitive_ids": source_semantic_ids,
        "kernel_verified_theorem_reduction_closure_work_order_ids": closure_work_order_ids,
        "kernel_verified_theorem_reduction_closure_target_ids": closure_target_ids,
        "kernel_verified_theorem_reduction_closure_goal_ids": closure_goal_ids,
    }


def _extend_unique_from_row(target: list[str], row: Mapping[str, Any], key: str) -> None:
    for value in row.get(key, []) or []:
        _append_unique(target, str(value).strip())


def _append_unique(target: list[str], value: str) -> None:
    if value and value not in target:
        target.append(value)


def _proof_obligation_has_tag(obligation_id: str, tag: str) -> bool:
    obligation = FORMAL_OBLIGATIONS.get(str(obligation_id).strip())
    return bool(obligation and tag in obligation.tags)


def _runtime_capability_ladder(payload: Mapping[str, Any]) -> dict[str, Any]:
    source_theorem_kernel_count = _payload_source_theorem_kernel_count(payload)
    integrated_algorithm_repair_sequences = int(
        payload.get("n_generated_code_sandbox_failed_then_passed_repair_sequences", 0)
        or 0
    )
    integrated_simulation_repair_sequences = int(
        payload.get(
            "n_generated_simulation_sandbox_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    attached_coding_repair_ready = (
        bool(
            payload.get(
                "internal_coding_agent_generated_code_repair_eval_capability_evidence_ok",
                False,
            )
        )
        and bool(
            payload.get(
                "internal_coding_agent_generated_code_repair_eval_live_generator",
                False,
            )
        )
        and not bool(
            payload.get(
                "internal_coding_agent_generated_code_repair_eval_static_or_fixture_only",
                False,
            )
        )
        and int(
            payload.get(
                "internal_coding_agent_generated_code_repair_eval_algorithm_repair_sequences",
                0,
            )
            or 0
        )
        > 0
        and int(
            payload.get(
                "internal_coding_agent_generated_code_repair_eval_simulation_repair_sequences",
                0,
            )
            or 0
        )
        > 0
    )
    integrated_formalizer_repair_sequences = int(
        payload.get(
            "n_formalizer_lean_candidate_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    integrated_llm_formalizer_proposals = int(
        payload.get("n_llm_formalizer_proof_engineer_proposals", 0) or 0
    )
    integrated_deterministic_formalizer_seeds = int(
        payload.get("n_deterministic_formalizer_work_order_seed_proposals", 0)
        or 0
    )
    attached_formalizer_repair_ready = (
        bool(
            payload.get(
                "internal_formalizer_lean_candidate_repair_eval_capability_evidence_ok",
                False,
            )
        )
        and bool(
            payload.get(
                "internal_formalizer_lean_candidate_repair_eval_live_generator",
                False,
            )
        )
        and not bool(
            payload.get(
                "internal_formalizer_lean_candidate_repair_eval_static_or_fixture_only",
                False,
            )
        )
        and int(
            payload.get(
                "internal_formalizer_lean_candidate_repair_eval_repair_sequences",
                0,
            )
            or 0
        )
        > 0
        and int(
            payload.get(
                "internal_formalizer_lean_candidate_repair_eval_local_lean_checked",
                0,
            )
            or 0
        )
        > 0
    )
    integrated_formalizer_agentic_repair_ready = (
        integrated_llm_formalizer_proposals > 0
        and integrated_formalizer_repair_sequences > 0
    )
    generated_code_and_lean_repair_ready = (
        (
            integrated_algorithm_repair_sequences > 0
            and integrated_simulation_repair_sequences > 0
        )
        or attached_coding_repair_ready
    ) and (
        integrated_formalizer_agentic_repair_ready
        or attached_formalizer_repair_ready
    )
    levels = [
        _ladder_level(
            0,
            "schema_static_replay_contract_valid",
            payload.get("all_ok") is True and int(payload.get("n_results", 0) or 0) > 0,
            f"all_ok={payload.get('all_ok')} n_results={payload.get('n_results')}",
            "runtime artifacts did not satisfy the basic audit contract",
        ),
        _ladder_level(
            1,
            "live_llm_generator_packets_valid",
            payload.get("all_ok") is True
            and int(payload.get("n_live_generator_agents_enabled", 0) or 0) > 0,
            (
                f"all_ok={payload.get('all_ok')} "
                f"n_live_generator_agents_enabled={payload.get('n_live_generator_agents_enabled')}"
            ),
            "no completed audited run used Anthropic/OpenAI generator-backed agents",
        ),
        _ladder_level(
            2,
            "live_architect_controlled_runtime_completed",
            payload.get("all_ok") is True
            and int(payload.get("n_live_generator_agents_enabled", 0) or 0) > 0
            and payload.get("architect_coordinator_enabled") is True,
            (
                f"architect_coordinator_enabled={payload.get('architect_coordinator_enabled')} "
                f"n_live_generator_agents_enabled={payload.get('n_live_generator_agents_enabled')}"
            ),
            "live run did not complete under ArchitectCoordinator control",
        ),
        _ladder_level(
            3,
            "live_generated_code_and_lean_repair_environment_feedback",
            generated_code_and_lean_repair_ready,
            (
                "integrated_algorithm_repair_sequences="
                f"{integrated_algorithm_repair_sequences} "
                "integrated_simulation_repair_sequences="
                f"{integrated_simulation_repair_sequences} "
                "integrated_formalizer_repair_sequences="
                f"{integrated_formalizer_repair_sequences} "
                "integrated_llm_formalizer_proposals="
                f"{integrated_llm_formalizer_proposals} "
                "integrated_deterministic_formalizer_seeds="
                f"{integrated_deterministic_formalizer_seeds} "
                "attached_coding_repair_ready="
                f"{attached_coding_repair_ready} "
                "attached_formalizer_repair_ready="
                f"{attached_formalizer_repair_ready}"
            ),
            (
                "no live generated-code Algorithm/Simulation repair gate plus "
                "generated Lean-candidate repair gate was observed; registered "
                "templates, one-shot sandbox execution, and static fixtures do "
                "not demonstrate coding-agent environment iteration"
            ),
        ),
        _ladder_level(
            4,
            "bridge_subclaim_kernel_evidence_available",
            int(payload.get("n_real_kernel_verified_subclaims", 0) or 0) > 0
            or int(payload.get("n_runtime_memory_kernel_verified_proof_obligation_ids", 0) or 0)
            > 0,
            (
                f"runtime_real_kernel={payload.get('n_real_kernel_verified_subclaims')} "
                "memory_kernel_proof_obligations="
                f"{payload.get('n_runtime_memory_kernel_verified_proof_obligation_ids')}"
            ),
            "no local Lean/AXLE kernel-verified bridge subclaim was produced or consumed",
        ),
        _ladder_level(
            5,
            "theorem_reduction_closure_kernel_evidence_available",
            int(
                payload.get(
                    "n_runtime_memory_kernel_verified_theorem_reduction_closure_goal_ids",
                    0,
                )
                or 0
            )
            > 0,
            (
                "memory_kernel_theorem_closure_goals="
                f"{payload.get('n_runtime_memory_kernel_verified_theorem_reduction_closure_goal_ids')} "
                "runtime_work_orders="
                f"{payload.get('n_runtime_theorem_reduction_closure_work_orders')}"
            ),
            "no kernel-verified theorem-reduction closure was consumed by this runtime",
        ),
        _ladder_level(
            6,
            "source_theorem_semantic_primitives_kernel_evidence_available",
            int(
                payload.get(
                    "n_runtime_memory_kernel_verified_source_theorem_semantic_primitive_ids",
                    0,
                )
                or 0
            )
            > 0
            or int(
                payload.get(
                    "n_real_kernel_verified_source_theorem_semantic_primitive_subclaims",
                    0,
                )
                or 0
            )
            > 0,
            (
                "memory_semantic_primitives="
                f"{payload.get('n_runtime_memory_kernel_verified_source_theorem_semantic_primitive_ids')} "
                "runtime_semantic_primitives="
                f"{payload.get('n_real_kernel_verified_source_theorem_semantic_primitive_subclaims')}"
            ),
            "no kernel-verified source-theorem semantic primitive was produced or consumed",
        ),
        _ladder_level(
            7,
            "full_source_theorem_kernel_verified",
            (
                int(payload.get("n_full_frontier_theorem_proved", 0) or 0) > 0
                or source_theorem_kernel_count > 0
            )
            and int(payload.get("n_formal_gaps", 0) or 0) <= 0,
            (
                f"n_full_frontier_theorem_proved={payload.get('n_full_frontier_theorem_proved')} "
                "proof_body_source_kernel="
                f"{source_theorem_kernel_count} "
                f"n_formal_gaps={payload.get('n_formal_gaps')}"
            ),
            "no full source/frontier theorem was kernel-verified with formal gaps closed",
        ),
        _ladder_level(
            8,
            "cross_task_generalization_demonstrated",
            int(payload.get("n_distinct_question_ids", 0) or 0) >= 2
            and int(payload.get("n_full_frontier_theorem_proved", 0) or 0) >= 2,
            (
                f"n_distinct_question_ids={payload.get('n_distinct_question_ids')} "
                f"n_full_frontier_theorem_proved={payload.get('n_full_frontier_theorem_proved')}"
            ),
            "no multi-question kernel-verified theorem generalization was demonstrated",
        ),
    ]
    max_contiguous = -1
    for row in levels:
        if row["level"] == max_contiguous + 1 and row["passed"] is True:
            max_contiguous = int(row["level"])
            continue
        break
    passed_levels = [int(row["level"]) for row in levels if row["passed"] is True]
    max_evidence = max(passed_levels) if passed_levels else -1
    first_blocking_level = next(
        (
            row
            for row in levels
            if row["level"] == max_contiguous + 1
            and row["passed"] is not True
        ),
        None,
    )
    noncontiguous_evidence = bool(max_evidence > max_contiguous)
    return {
        "artifact_kind": "RuntimeCapabilityLadder",
        "scale": "L0-L8",
        "max_contiguous_level": max_contiguous,
        "max_contiguous_level_label": (
            levels[max_contiguous]["label"]
            if max_contiguous >= 0
            else "no_contiguous_runtime_contract"
        ),
        "max_evidence_level": max_evidence,
        "max_evidence_level_label": (
            levels[max_evidence]["label"] if max_evidence >= 0 else "no_runtime_evidence"
        ),
        "current_level_label": (
            levels[max_contiguous]["label"] if max_contiguous >= 0 else "no_runtime_contract"
        ),
        "first_blocking_level": first_blocking_level,
        "noncontiguous_evidence_observed": noncontiguous_evidence,
        "noncontiguous_evidence_warning": (
            "Later capability evidence is present, but earlier runtime contract "
            "levels failed. Treat the later level as diagnostic progress only, "
            "not as integrated readiness."
            if noncontiguous_evidence
            else ""
        ),
        "levels": levels,
        "boundary": (
            "This ladder is descriptive evidence, not a proof gate. LLM routing, "
            "simulation, retrieval, and consumed runtime memory are separated from "
            "kernel-verified theorem evidence; L7 is required before claiming a full "
            "source theorem proof, and L8 is required before claiming cross-task generalization."
        ),
    }


def _ladder_level(
    level: int,
    label: str,
    passed: bool,
    evidence: str,
    blocker: str,
) -> dict[str, Any]:
    return {
        "level": level,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
        "blocker": "" if passed else blocker,
    }


def _runtime_capability_scorecard(payload: Mapping[str, Any]) -> dict[str, Any]:
    n_results = int(payload.get("n_results", 0) or 0)
    source_theorem_kernel_count = _payload_source_theorem_kernel_count(payload)
    integrated_algorithm_repair_sequences = int(
        payload.get("n_generated_code_sandbox_failed_then_passed_repair_sequences", 0)
        or 0
    )
    integrated_simulation_repair_sequences = int(
        payload.get(
            "n_generated_simulation_sandbox_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    attached_repair_eval_algorithm_sequences = int(
        payload.get(
            "internal_coding_agent_generated_code_repair_eval_algorithm_repair_sequences",
            0,
        )
        or 0
    )
    attached_repair_eval_simulation_sequences = int(
        payload.get(
            "internal_coding_agent_generated_code_repair_eval_simulation_repair_sequences",
            0,
        )
        or 0
    )
    attached_live_component_repair_gate_passed = (
        bool(
            payload.get(
                "internal_coding_agent_generated_code_repair_eval_capability_evidence_ok",
                False,
            )
        )
        and bool(
            payload.get(
                "internal_coding_agent_generated_code_repair_eval_live_generator",
                False,
            )
        )
        and not bool(
            payload.get(
                "internal_coding_agent_generated_code_repair_eval_static_or_fixture_only",
                False,
            )
        )
        and attached_repair_eval_algorithm_sequences > 0
        and attached_repair_eval_simulation_sequences > 0
    )
    integrated_formalizer_candidate_checked = int(
        payload.get("n_formalizer_lean_candidate_local_lean_checked", 0) or 0
    )
    integrated_formalizer_live_proof_state_requests = int(
        payload.get("n_formalizer_lean_candidate_live_proof_state_requests", 0)
        or 0
    )
    integrated_formalizer_lean_lsp_mcp_ready_requests = int(
        payload.get(
            "n_formalizer_lean_candidate_lean_lsp_mcp_ready_requests",
            0,
        )
        or 0
    )
    integrated_formalizer_proof_state_feedback_rows = int(
        payload.get(
            "n_formalizer_lean_candidate_proof_state_feedback_rows",
            0,
        )
        or 0
    )
    integrated_formalizer_local_lean_tool_calls = int(
        payload.get(
            "n_formalizer_lean_candidate_local_lean_tool_calls",
            0,
        )
        or 0
    )
    integrated_formalizer_lean_lsp_mcp_live_calls = int(
        payload.get(
            "n_formalizer_lean_candidate_lean_lsp_mcp_live_calls",
            0,
        )
        or 0
    )
    integrated_formalizer_repair_sequences = int(
        payload.get(
            "n_formalizer_lean_candidate_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    attached_formalizer_repair_sequences = int(
        payload.get(
            "internal_formalizer_lean_candidate_repair_eval_repair_sequences",
            0,
        )
        or 0
    )
    attached_formalizer_local_lean_checked = int(
        payload.get(
            "internal_formalizer_lean_candidate_repair_eval_local_lean_checked",
            0,
        )
        or 0
    )
    attached_formalizer_live_gate_passed = (
        bool(
            payload.get(
                "internal_formalizer_lean_candidate_repair_eval_capability_evidence_ok",
                False,
            )
        )
        and bool(
            payload.get(
                "internal_formalizer_lean_candidate_repair_eval_live_generator",
                False,
            )
        )
        and not bool(
            payload.get(
                "internal_formalizer_lean_candidate_repair_eval_static_or_fixture_only",
                False,
            )
        )
        and attached_formalizer_repair_sequences > 0
        and attached_formalizer_local_lean_checked > 0
    )
    integrated_llm_formalizer_proposals = int(
        payload.get("n_llm_formalizer_proof_engineer_proposals", 0) or 0
    )
    integrated_deterministic_formalizer_seeds = int(
        payload.get("n_deterministic_formalizer_work_order_seed_proposals", 0)
        or 0
    )
    integrated_formalizer_agentic_repair_ready = (
        integrated_llm_formalizer_proposals > 0
        and integrated_formalizer_repair_sequences > 0
    )
    primary_typechecked_review_required = bool(
        payload.get(
            "source_theorem_exact_semantic_definition_lean_repair_executor_typechecked_candidate_review_required",
            False,
        )
    )
    primary_materialized_typechecked_review_required = bool(
        payload.get(
            "source_theorem_exact_semantic_definition_materialized_candidate_review_required",
            False,
        )
    )
    late_typechecked_review_required = bool(
        payload.get(
            "source_theorem_exact_semantic_definition_late_materialized_candidate_review_required",
            False,
        )
        or payload.get(
            "source_theorem_exact_semantic_definition_late_lean_repair_executor_typechecked_candidate_review_required",
            False,
        )
    )
    primary_typechecked_review_recheck_rows = int(
        payload.get(
            "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_execution_rows",
            0,
        )
        or 0
    )
    exact_semantic_definition_candidate_synthesis_recheck_rows = int(
        payload.get(
            "source_theorem_exact_semantic_definition_candidate_synthesis_n_proof_body_recheck_queue_rows",
            0,
        )
        or 0
    )
    exact_semantic_definition_candidate_synthesis_recheck_executor_ran = (
        payload.get(
            "source_theorem_exact_semantic_definition_proof_body_recheck_executor_ran"
        )
        is True
    )
    primary_typechecked_review_verifier_gate_work_orders = int(
        payload.get(
            "source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_verifier_gate_work_orders",
            0,
        )
        or 0
    )
    materialized_typechecked_review_recheck_rows = int(
        payload.get(
            "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_execution_rows",
            0,
        )
        or 0
    )
    materialized_typechecked_review_verifier_gate_work_orders = int(
        payload.get(
            "source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_verifier_gate_work_orders",
            0,
        )
        or 0
    )
    late_typechecked_review_recheck_rows = int(
        payload.get(
            "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_execution_rows",
            0,
        )
        or 0
    )
    primary_typechecked_review_recheck_executor_ran = (
        payload.get(
            "source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_ran"
        )
        is True
    )
    materialized_typechecked_review_recheck_executor_ran = (
        payload.get(
            "source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_ran"
        )
        is True
    )
    late_typechecked_review_recheck_executor_ran = (
        payload.get(
            "source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_ran"
        )
        is True
    )
    rows = [
        _scorecard_row(
            "runtime_marked_capability_eval",
            str(payload.get("runtime_evaluation_mode", "")) == "capability_eval",
            f"runtime_evaluation_mode={payload.get('runtime_evaluation_mode')}",
            "runtime manifest was not marked as capability_eval",
        ),
        _scorecard_row(
            "runtime_result_present",
            n_results > 0,
            f"n_results={n_results}",
            "no per-question runtime result was audited",
        ),
        _scorecard_row(
            "live_generator_agents_enabled",
            int(payload.get("n_live_generator_agents_enabled", 0) or 0) > 0,
            f"n_live_generator_agents_enabled={payload.get('n_live_generator_agents_enabled')}",
            "no live Anthropic/OpenAI generator agents were enabled",
        ),
        _scorecard_row(
            "architect_orchestrated",
            payload.get("architect_coordinator_enabled") is True,
            f"architect_coordinator_enabled={payload.get('architect_coordinator_enabled')}",
            "ArchitectCoordinator was disabled; this is a subsystem-chain run, not architect-orchestrated research",
        ),
        _scorecard_row(
            "architect_research_path_control_propagated",
            payload.get("runtime_research_path_control_propagated") is True,
            (
                "effective_policy="
                f"{payload.get('effective_formal_verification_policy')} "
                "effective_path="
                f"{payload.get('effective_recommended_research_path')} "
                "summary="
                f"{_research_path_summary_detail(payload)}"
            ),
            "Architect evidence contract did not propagate consistently to runtime artifacts",
        ),
        _scorecard_row(
            "research_path_selected_by_architect_not_manual_override",
            not str(payload.get("requested_recommended_research_path", "") or "").strip(),
            (
                "requested_recommended_research_path="
                f"{payload.get('requested_recommended_research_path')}"
            ),
            (
                "manual --recommended-research-path override was used; this is "
                "controlled-smoke/debug routing, not autonomous Architect path selection"
            ),
        ),
        _scorecard_row(
            "architect_problem_analysis_present",
            int(payload.get("n_results_with_problem_analysis", 0) or 0) >= n_results,
            f"problem_analysis={payload.get('n_results_with_problem_analysis')}/{n_results}",
            "Architect problem_analysis was missing for at least one result",
        ),
        _scorecard_row(
            "dynamic_stat_knowledge_bank_planned",
            int(payload.get("n_results_with_stat_knowledge_bank_plan", 0) or 0) >= n_results,
            f"stat_knowledge_bank={payload.get('n_results_with_stat_knowledge_bank_plan')}/{n_results}",
            "dynamic StatKnowledgeBank planning was missing for at least one result",
        ),
        _scorecard_row(
            "literature_fair_comparison_planned",
            int(payload.get("n_results_with_literature_fair_comparison_plan", 0) or 0) >= n_results,
            f"literature_fair_comparison={payload.get('n_results_with_literature_fair_comparison_plan')}/{n_results}",
            "literature fair-comparison planning was missing for at least one result",
        ),
        _scorecard_row(
            "theory_derivation_trace_contract_observed",
            payload.get("structured_theory_derivation_trace_observed") is True,
            (
                "theory_packets="
                f"{payload.get('n_theory_derivation_packets')} "
                "with_contract="
                f"{payload.get('n_theory_derivation_packets_with_contract')} "
                "with_min_steps="
                f"{payload.get('n_theory_derivation_packets_with_min_derivation_steps')} "
                "with_equation_chain="
                f"{payload.get('n_theory_derivation_packets_with_equation_chain')} "
                "with_assumption_ledger="
                f"{payload.get('n_theory_derivation_packets_with_assumption_ledger')} "
                "with_formalization_handoff="
                f"{payload.get('n_theory_derivation_packets_with_formalization_handoff')}"
            ),
            (
                "TheoryDeveloper did not produce a structured derivation trace "
                "with equation-chain, assumption-ledger, and formalization handoff; "
                "downstream coding/proof workers are not receiving enough LLM-derived "
                "theory context"
            ),
        ),
        _scorecard_row(
            "downstream_theory_trace_consumption_observed",
            payload.get("all_required_theory_trace_consumers_observed") is True,
            (
                "structured_consumers="
                f"{payload.get('structured_theory_trace_consuming_subsystems')} "
                "all_consumers="
                f"{payload.get('theory_trace_consuming_subsystems')} "
                "required="
                f"{payload.get('required_theory_trace_consumers')} "
                "contracts="
                f"{payload.get('n_theory_trace_consumption_contracts')} "
                "with_trace="
                f"{payload.get('n_theory_trace_consumption_contracts_with_trace')} "
                "with_equation_chain="
                f"{payload.get('n_theory_trace_consumption_contracts_with_equation_chain')} "
                "with_assumption_ledger="
                f"{payload.get('n_theory_trace_consumption_contracts_with_assumption_ledger')} "
                "with_formalization_handoff="
                f"{payload.get('n_theory_trace_consumption_contracts_with_formalization_handoff')}"
            ),
            (
                "SimulationEngineer, AlgorithmEngineer, and FormalizerProofEngineer "
                "did not all consume the structured theory derivation trace by "
                "runtime contract; the system is not yet proving a theory-to-code/proof "
                "agent handoff"
            ),
        ),
        _scorecard_row(
            "downstream_theory_trace_alignment_observed",
            payload.get(
                "all_required_theory_trace_alignment_consumers_observed"
            )
            is True,
            (
                "structured_aligned_subsystems="
                f"{payload.get('structured_theory_trace_aligned_subsystems')} "
                "aligned_subsystems="
                f"{payload.get('theory_trace_aligned_subsystems')} "
                "required="
                f"{payload.get('required_theory_trace_consumers')} "
                "alignment_contracts="
                f"{payload.get('n_theory_trace_alignment_contracts')} "
                "with_llm_alignment="
                f"{payload.get('n_theory_trace_alignment_contracts_with_llm_alignment')} "
                "structured="
                f"{payload.get('n_structured_theory_trace_alignment_contracts')} "
                "unsupported="
                f"{payload.get('n_theory_trace_alignment_contracts_with_unsupported_anchors')}"
            ),
            (
                "SimulationEngineer, AlgorithmEngineer, and FormalizerProofEngineer "
                "did not all bind their proposal artifacts to supported theory "
                "derivation anchors; supplied context is not yet auditable as a "
                "theory-to-artifact handoff"
            ),
        ),
        _scorecard_row(
            "algorithm_sandbox_executed",
            int(payload.get("n_algorithm_sandbox_executed", 0) or 0) > 0,
            f"n_algorithm_sandbox_executed={payload.get('n_algorithm_sandbox_executed')}",
            "no algorithm sandbox prototype executed",
        ),
        _scorecard_row(
            "generated_algorithm_code_executed",
            int(payload.get("n_generated_code_sandbox_executed", 0) or 0) > 0,
            (
                "n_generated_code_sandbox_executed="
                f"{payload.get('n_generated_code_sandbox_executed')}"
            ),
            (
                "no Claude/OpenAI-generated algorithm code executed locally; "
                "registered templates are baselines and do not demonstrate "
                "coding-agent implementation capacity"
            ),
        ),
        _scorecard_row(
            "generated_algorithm_sandbox_clean",
            int(payload.get("n_unsafe_generated_code_rejected", 0) or 0) <= 0
            or integrated_algorithm_repair_sequences > 0,
            (
                "n_unsafe_generated_code_rejected="
                f"{payload.get('n_unsafe_generated_code_rejected')} "
                "integrated_algorithm_repair_sequences="
                f"{integrated_algorithm_repair_sequences}"
            ),
            (
                "at least one generated algorithm draft was rejected by the "
                "sandbox guard and no later generated-code repair loop passed"
            ),
        ),
        _scorecard_row(
            "generated_algorithm_metric_gate_clean",
            int(payload.get("n_generated_code_sandbox_metric_gate_failed", 0) or 0)
            <= 0
            or integrated_algorithm_repair_sequences > 0,
            (
                "n_generated_code_sandbox_metric_gate_failed="
                f"{payload.get('n_generated_code_sandbox_metric_gate_failed')} "
                "integrated_algorithm_repair_sequences="
                f"{integrated_algorithm_repair_sequences}"
            ),
            (
                "at least one generated algorithm draft executed locally but failed "
                "the statistical metric gate and no later generated-code repair "
                "loop passed"
            ),
        ),
        _scorecard_row(
            "generated_algorithm_repair_loop_observed",
            integrated_algorithm_repair_sequences > 0,
            (
                "n_generated_code_sandbox_failed_then_passed_repair_sequences="
                f"{payload.get('n_generated_code_sandbox_failed_then_passed_repair_sequences')}"
            ),
            (
                "no generated algorithm draft failure was followed by a later "
                "generated draft passing local sandbox/metric gates; one-shot "
                "execution is not evidence of autonomous coding repair"
            ),
        ),
        _scorecard_row(
            "generated_simulation_code_executed",
            int(payload.get("n_generated_simulation_sandbox_executed", 0) or 0)
            > 0,
            (
                "n_generated_simulation_sandbox_executed="
                f"{payload.get('n_generated_simulation_sandbox_executed')}"
            ),
            (
                "no Claude/OpenAI-generated simulation stress-test code executed "
                "locally; registered simulator rows alone do not demonstrate "
                "simulation coding-agent capacity"
            ),
        ),
        _scorecard_row(
            "generated_simulation_sandbox_clean",
            int(payload.get("n_unsafe_generated_simulation_code_rejected", 0) or 0)
            <= 0
            or integrated_simulation_repair_sequences > 0,
            (
                "n_unsafe_generated_simulation_code_rejected="
                f"{payload.get('n_unsafe_generated_simulation_code_rejected')} "
                "integrated_simulation_repair_sequences="
                f"{integrated_simulation_repair_sequences}"
            ),
            (
                "at least one generated simulation draft was rejected by the "
                "sandbox guard and no later generated-code repair loop passed"
            ),
        ),
        _scorecard_row(
            "generated_simulation_metric_gate_clean",
            int(
                payload.get(
                    "n_generated_simulation_sandbox_metric_gate_failed",
                    0,
                )
                or 0
            )
            <= 0
            or integrated_simulation_repair_sequences > 0,
            (
                "n_generated_simulation_sandbox_metric_gate_failed="
                f"{payload.get('n_generated_simulation_sandbox_metric_gate_failed')} "
                "integrated_simulation_repair_sequences="
                f"{integrated_simulation_repair_sequences}"
            ),
            (
                "at least one generated simulation draft executed locally but failed "
                "the statistical metric gate and no later generated-code repair "
                "loop passed"
            ),
        ),
        _scorecard_row(
            "generated_simulation_repair_loop_observed",
            integrated_simulation_repair_sequences > 0,
            (
                "n_generated_simulation_sandbox_failed_then_passed_repair_sequences="
                f"{payload.get('n_generated_simulation_sandbox_failed_then_passed_repair_sequences')}"
            ),
            (
                "no generated simulation draft failure was followed by a later "
                "generated draft passing local sandbox/metric gates; registered "
                "simulation rows or one-shot execution do not demonstrate "
                "simulation coding-agent repair"
            ),
        ),
        _scorecard_row(
            "coding_agent_generated_code_repair_component_gate",
            (
                integrated_algorithm_repair_sequences > 0
                and integrated_simulation_repair_sequences > 0
            )
            or attached_live_component_repair_gate_passed,
            (
                "integrated_algorithm_repair_sequences="
                f"{integrated_algorithm_repair_sequences} "
                "integrated_simulation_repair_sequences="
                f"{integrated_simulation_repair_sequences} "
                "attached_component_capability="
                f"{payload.get('internal_coding_agent_generated_code_repair_eval_capability_evidence_ok')} "
                "attached_live_generator="
                f"{payload.get('internal_coding_agent_generated_code_repair_eval_live_generator')} "
                "attached_static_or_fixture_only="
                f"{payload.get('internal_coding_agent_generated_code_repair_eval_static_or_fixture_only')} "
                "attached_algorithm_repair_sequences="
                f"{attached_repair_eval_algorithm_sequences} "
                "attached_simulation_repair_sequences="
                f"{attached_repair_eval_simulation_sequences}"
            ),
            (
                "neither integrated AgentRuntime repair loops nor an attached "
                "live combined coding-agent repair gate show both AlgorithmEngineer "
                "and SimulationEngineer fail-then-pass generated-code repair evidence"
            ),
        ),
        _scorecard_row(
            "llm_formalizer_proofengineer_proposal_observed",
            integrated_llm_formalizer_proposals > 0
            or attached_formalizer_live_gate_passed,
            (
                "n_llm_formalizer_proof_engineer_proposals="
                f"{payload.get('n_llm_formalizer_proof_engineer_proposals')} "
                "n_deterministic_formalizer_work_order_seed_proposals="
                f"{payload.get('n_deterministic_formalizer_work_order_seed_proposals')} "
                "attached_formalizer_live_gate="
                f"{attached_formalizer_live_gate_passed}"
            ),
            (
                "deterministic theorem-closure seeds are work-order scaffolds; "
                "they cannot replace a live Claude/OpenAI Formalizer or "
                "ProofEngineer proposal in capability evidence"
            ),
        ),
        _scorecard_row(
            "formalizer_lean_candidate_local_check_attempted",
            (
                integrated_llm_formalizer_proposals > 0
                and integrated_formalizer_candidate_checked > 0
            )
            or (
                attached_formalizer_live_gate_passed
                and attached_formalizer_local_lean_checked > 0
            ),
            (
                "n_formalizer_lean_candidate_local_lean_checked="
                f"{payload.get('n_formalizer_lean_candidate_local_lean_checked')} "
                "n_llm_formalizer_proof_engineer_proposals="
                f"{payload.get('n_llm_formalizer_proof_engineer_proposals')} "
                "compiled="
                f"{payload.get('n_formalizer_lean_candidate_local_lean_compiled')} "
                "attached_live_local_lean_checked="
                f"{attached_formalizer_local_lean_checked}"
            ),
            (
                "no Claude/OpenAI-generated Formalizer Lean candidate was checked "
                "with local Lean; proof packets without local diagnostics do not "
                "demonstrate Formalizer/ProofEngineer capacity"
            ),
        ),
        _scorecard_row(
            "formalizer_lean_candidate_proof_state_request_routed",
            (
                integrated_llm_formalizer_proposals > 0
                and integrated_formalizer_live_proof_state_requests > 0
                and integrated_formalizer_lean_lsp_mcp_ready_requests > 0
            ),
            (
                "live_proof_state_requests="
                f"{payload.get('n_formalizer_lean_candidate_live_proof_state_requests')} "
                "lean_lsp_mcp_ready="
                f"{payload.get('n_formalizer_lean_candidate_lean_lsp_mcp_ready_requests')}"
            ),
            (
                "Formalizer Lean candidate failures did not produce "
                "Lean-LSP/MCP-ready ProofEngineer proof-state requests; local "
                "Lean checks alone do not demonstrate an autonomous prover loop"
            ),
        ),
        _scorecard_row(
            "formalizer_lean_candidate_proof_state_feedback_recorded",
            integrated_llm_formalizer_proposals > 0
            and integrated_formalizer_proof_state_feedback_rows > 0,
            (
                "proof_state_feedback_rows="
                f"{payload.get('n_formalizer_lean_candidate_proof_state_feedback_rows')}"
            ),
            (
                "Formalizer Lean candidate failures did not produce structured "
                "ProofEngineer feedback rows with diagnostics/residual goals for "
                "the next Claude/OpenAI repair turn"
            ),
        ),
        _scorecard_row(
            "formalizer_local_lean_tool_call_observed",
            integrated_llm_formalizer_proposals > 0
            and integrated_formalizer_local_lean_tool_calls > 0,
            (
                "local_lean_tool_calls="
                f"{payload.get('n_formalizer_lean_candidate_local_lean_tool_calls')}"
            ),
            (
                "ProofEngineer feedback did not record actual local Lean tool "
                "execution in executed_tools/tool_call_trace; candidate local "
                "checks without tool-call transcript are weaker repair context"
            ),
        ),
        _scorecard_row(
            "formalizer_live_prover_tool_call_observed",
            integrated_llm_formalizer_proposals > 0
            and integrated_formalizer_lean_lsp_mcp_live_calls > 0,
            (
                "lean_lsp_mcp_live_calls="
                f"{payload.get('n_formalizer_lean_candidate_lean_lsp_mcp_live_calls')}"
            ),
            (
                "LeanDojo/ReProver/Lean-LSP style prover tools were requested "
                "or staged but no live prover tool call was observed; request "
                "rows alone are not full ProofEngineer capacity"
            ),
        ),
        _scorecard_row(
            "formalizer_lean_candidate_repair_component_gate",
            integrated_formalizer_agentic_repair_ready
            or attached_formalizer_live_gate_passed,
            (
                "integrated_formalizer_repair_sequences="
                f"{integrated_formalizer_repair_sequences} "
                "integrated_llm_formalizer_proposals="
                f"{integrated_llm_formalizer_proposals} "
                "attached_component_capability="
                f"{payload.get('internal_formalizer_lean_candidate_repair_eval_capability_evidence_ok')} "
                "attached_live_generator="
                f"{payload.get('internal_formalizer_lean_candidate_repair_eval_live_generator')} "
                "attached_static_or_fixture_only="
                f"{payload.get('internal_formalizer_lean_candidate_repair_eval_static_or_fixture_only')} "
                "attached_repair_sequences="
                f"{attached_formalizer_repair_sequences} "
                "attached_local_lean_checked="
                f"{attached_formalizer_local_lean_checked}"
            ),
            (
                "neither integrated AgentRuntime repair loops nor an attached "
                "live Formalizer Lean-candidate repair gate showed fail-then-pass "
                "generated Lean repair with local Lean diagnostics; static fixtures "
                "and proof packets do not demonstrate this capacity"
            ),
        ),
        _scorecard_row(
            "runtime_progress_observable",
            int(payload.get("n_runtime_progress_events", 0) or 0)
            >= 2 * int(payload.get("n_runtime_traces", 0) or 0)
            and int(payload.get("n_runtime_traces", 0) or 0) > 0,
            (
                f"progress_events={payload.get('n_runtime_progress_events')} "
                f"runtime_traces={payload.get('n_runtime_traces')}"
            ),
            "runtime progress JSONL did not record start/finish events for every trace",
        ),
        _scorecard_row(
            "source_theorem_promotion_proofengineer_bridge_ran",
            payload.get("source_theorem_promotion_proofengineer_bridge_ran") is True,
            (
                "ran="
                f"{payload.get('source_theorem_promotion_proofengineer_bridge_ran')} "
                "skipped="
                f"{payload.get('source_theorem_promotion_proofengineer_bridge_skipped_reason')}"
            ),
            "source-theorem promotion ProofEngineer bridge did not run inside the runtime",
        ),
        _scorecard_row(
            "source_theorem_formal_environment_bridge_ran",
            (
                payload.get("source_theorem_formal_environment_proofengineer_bridge_ran")
                is True
            ),
            (
                "ran="
                f"{payload.get('source_theorem_formal_environment_proofengineer_bridge_ran')} "
                "skipped="
                f"{payload.get('source_theorem_formal_environment_proofengineer_bridge_skipped_reason')}"
            ),
            "source-theorem formal-environment ProofEngineer bridge did not run inside the runtime",
        ),
        _scorecard_row(
            "source_theorem_signature_probe_reached_proof_body",
            int(
                payload.get(
                    "source_theorem_formal_environment_proofengineer_n_signature_probes_reached_proof_body",
                    0,
                )
                or 0
            )
            > 0,
            (
                "n_signature_or_proof_body_work_orders="
                f"{payload.get('source_theorem_formal_environment_proofengineer_n_signature_probes_reached_proof_body')}"
            ),
            "source-theorem signature probe did not reach an exact proof body",
        ),
        _scorecard_row(
            "source_theorem_proof_body_executor_ran",
            payload.get("source_theorem_formal_environment_proof_body_executor_ran")
            is True,
            (
                "ran="
                f"{payload.get('source_theorem_formal_environment_proof_body_executor_ran')} "
                "n_rows="
                f"{payload.get('source_theorem_formal_environment_proof_body_executor_n_result_rows')}"
            ),
            "exact source-theorem proof-body executor did not run inside the runtime",
        ),
        _scorecard_row(
            "post_adapter_exact_source_theorem_proof_body_retry_queued",
            int(
                payload.get(
                    "n_runtime_source_theorem_exact_proof_body_repair_work_orders_from_proof_body_adapter_feedback",
                    0,
                )
                or 0
            )
            <= 0
            or (
                payload.get(
                    "source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_ran"
                )
                is True
            ),
            (
                "work_orders="
                f"{payload.get('n_runtime_source_theorem_exact_proof_body_repair_work_orders_from_proof_body_adapter_feedback')} "
                "queue_ran="
                f"{payload.get('source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_ran')} "
                "queue_rows="
                f"{payload.get('source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_n_rows')}"
            ),
            "verified proof-body adapter feedback did not trigger a same-run exact source theorem retry queue",
        ),
        _scorecard_row(
            "post_adapter_exact_source_theorem_proof_body_executor_ran",
            (
                payload.get(
                    "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_requested"
                )
                is not True
            )
            or (
                payload.get(
                    "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_ran"
                )
                is True
            ),
            (
                "requested="
                f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_requested')} "
                "ran="
                f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_ran')} "
                "n_rows="
                f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_result_rows')} "
                "source_kernel="
                f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_source_theorem_kernel_verified')}"
            ),
            "same-run post-adapter exact source theorem proof-body executor was requested but did not run",
        ),
        _scorecard_row(
            "post_adapter_failure_rerouted_to_semantic_primitives_or_source_proved",
            (
                payload.get(
                    "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_ran"
                )
                is not True
            )
            or
            int(
                payload.get(
                    "source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_source_theorem_kernel_verified",
                    0,
                )
                or 0
            )
            > 0
            or int(
                payload.get(
                    "n_runtime_new_source_theorem_semantic_primitive_work_orders_from_proof_body_adapter_feedback",
                    0,
                )
                or 0
            )
            > 0,
            (
                "post_adapter_source_kernel="
                f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_source_theorem_kernel_verified')} "
                "new_semantic_work_orders="
                f"{payload.get('n_runtime_new_source_theorem_semantic_primitive_work_orders_from_proof_body_adapter_feedback')}"
            ),
            "post-adapter proof-body failure neither proved the source theorem nor rerouted to semantic primitive work",
        ),
        _scorecard_row(
            "exact_semantic_definition_source_lookup_handoff_not_dropped",
            (
                payload.get("source_theorem_exact_semantic_definition_source_lookup_required")
                is not True
            )
            or (
                payload.get("source_theorem_exact_semantic_definition_source_lookup_ran")
                is True
            ),
            (
                "work_orders="
                f"{payload.get('n_runtime_source_theorem_exact_semantic_definition_work_orders')} "
                "required="
                f"{payload.get('source_theorem_exact_semantic_definition_source_lookup_required')} "
                "ran="
                f"{payload.get('source_theorem_exact_semantic_definition_source_lookup_ran')} "
                "skipped="
                f"{payload.get('source_theorem_exact_semantic_definition_source_lookup_skipped_reason')}"
            ),
            "exact semantic-definition work orders were generated but source lookup did not run",
        ),
        _scorecard_row(
            "exact_semantic_definition_proofengineer_bridge_handoff_not_dropped",
            (
                payload.get(
                    "source_theorem_exact_semantic_definition_proofengineer_bridge_required"
                )
                is not True
            )
            or (
                payload.get(
                    "source_theorem_exact_semantic_definition_proofengineer_bridge_ran"
                )
                is True
            ),
            (
                "review_packets="
                f"{payload.get('source_theorem_exact_semantic_definition_n_closure_review_packets')} "
                "required="
                f"{payload.get('source_theorem_exact_semantic_definition_proofengineer_bridge_required')} "
                "ran="
                f"{payload.get('source_theorem_exact_semantic_definition_proofengineer_bridge_ran')} "
                "skipped="
                f"{payload.get('source_theorem_exact_semantic_definition_proofengineer_bridge_skipped_reason')}"
            ),
            "source lookup produced exact semantic-definition review packets but the ProofEngineer bridge did not run",
        ),
        _scorecard_row(
            "exact_semantic_definition_lean_repair_executor_handoff_not_dropped",
            (
                payload.get(
                    "source_theorem_exact_semantic_definition_lean_repair_executor_required"
                )
                is not True
            )
            or (
                payload.get(
                    "source_theorem_exact_semantic_definition_lean_repair_executor_ran"
                )
                is True
            ),
            (
                "lean_tasks="
                f"{payload.get('source_theorem_exact_semantic_definition_proofengineer_bridge_n_lean_repair_tasks')} "
                "required="
                f"{payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_required')} "
                "ran="
                f"{payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_ran')} "
                "skipped="
                f"{payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_skipped_reason')} "
                "local_lean_requested="
                f"{payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_local_lean_requested')}"
            ),
            "ProofEngineer bridge produced exact semantic-definition Lean repair tasks but the Lean repair executor did not run",
        ),
        _scorecard_row(
            "exact_semantic_definition_candidate_synthesis_recheck_executor_not_dropped",
            exact_semantic_definition_candidate_synthesis_recheck_rows <= 0
            or exact_semantic_definition_candidate_synthesis_recheck_executor_ran,
            (
                "recheck_queue_rows="
                f"{payload.get('source_theorem_exact_semantic_definition_candidate_synthesis_n_proof_body_recheck_queue_rows')} "
                "executor_ran="
                f"{payload.get('source_theorem_exact_semantic_definition_proof_body_recheck_executor_ran')} "
                "executor_results="
                f"{payload.get('source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_result_rows')} "
                "source_kernel="
                f"{payload.get('source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_source_theorem_kernel_verified')} "
                "skipped="
                f"{payload.get('source_theorem_exact_semantic_definition_proof_body_recheck_executor_skipped_reason')}"
            ),
            (
                "exact semantic-definition candidate synthesis produced "
                "proof-body recheck rows but the same-run proof-body executor "
                "did not run"
            ),
        ),
        _scorecard_row(
            "exact_semantic_definition_late_typechecked_review_not_hidden",
            not (
                primary_typechecked_review_required
                or primary_materialized_typechecked_review_required
                or late_typechecked_review_required
            )
            or primary_typechecked_review_recheck_rows > 0
            or primary_typechecked_review_verifier_gate_work_orders > 0
            or materialized_typechecked_review_recheck_rows > 0
            or materialized_typechecked_review_verifier_gate_work_orders > 0
            or late_typechecked_review_recheck_rows > 0
            or int(
                payload.get(
                    "source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_verifier_gate_work_orders",
                    0,
                )
                or 0
            )
            > 0
            or (
                payload.get("source_theorem_exact_semantic_definition_repair_required")
                is True
                and bool(
                    str(
                        payload.get(
                            "source_theorem_exact_semantic_definition_repair_required_reason",
                            "",
                        )
                        or ""
                    ).strip()
                )
            ),
            (
                "primary_materialized_review_packets="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_lean_repair_executor_n_typechecked_candidate_review_packets')} "
                "primary_materialized_review_required="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_candidate_review_required')} "
                "primary_materialized_bridge_ran="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_ran')} "
                "primary_materialized_llm_approved="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_llm_approved_packets')} "
                "primary_materialized_verifier_gate_work_orders="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
                "late_materialized_review_packets="
                f"{payload.get('source_theorem_exact_semantic_definition_late_materialized_lean_repair_executor_n_typechecked_candidate_review_packets')} "
                "late_materialized_review_required="
                f"{payload.get('source_theorem_exact_semantic_definition_late_materialized_candidate_review_required')} "
                "late_review_packets="
                f"{payload.get('source_theorem_exact_semantic_definition_late_lean_repair_executor_n_typechecked_candidate_review_packets')} "
                "late_review_required="
                f"{payload.get('source_theorem_exact_semantic_definition_late_lean_repair_executor_typechecked_candidate_review_required')} "
                "primary_review_required="
                f"{payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_typechecked_candidate_review_required')} "
                "primary_llm_approved="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_packets')} "
                "primary_llm_approved_requiring_verifier_gate="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate')} "
                "primary_verifier_gate_work_orders="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
                "late_llm_approved="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_packets')} "
                "late_llm_approved_requiring_verifier_gate="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate')} "
                "late_verifier_gate_work_orders="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
                "repair_required="
                f"{payload.get('source_theorem_exact_semantic_definition_repair_required')} "
                "repair_reason="
                f"{payload.get('source_theorem_exact_semantic_definition_repair_required_reason')}"
                " primary_recheck_execution_rows="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_execution_rows')}"
                " late_recheck_execution_rows="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_execution_rows')}"
            ),
            (
                "typechecked exact semantic-definition candidate review is pending "
                "but the runtime did not expose it as exact semantic-definition repair work"
            ),
        ),
        _scorecard_row(
            "exact_semantic_definition_typechecked_review_recheck_executor_not_dropped",
            (
                primary_typechecked_review_recheck_rows <= 0
                or primary_typechecked_review_recheck_executor_ran
            )
            and (
                materialized_typechecked_review_recheck_rows <= 0
                or materialized_typechecked_review_recheck_executor_ran
            )
            and (
                late_typechecked_review_recheck_rows <= 0
                or late_typechecked_review_recheck_executor_ran
            ),
            (
                "primary_queue_ran="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_ran')} "
                "primary_approved="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_approved_packets')} "
                "primary_llm_approved="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_packets')} "
                "primary_llm_approved_requiring_verifier_gate="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate')} "
                "primary_verifier_gate_work_orders="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
                "primary_execution_rows="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_execution_rows')} "
                "primary_executor_ran="
                f"{payload.get('source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_ran')} "
                "materialized_queue_ran="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_ran')} "
                "materialized_llm_approved="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_llm_approved_packets')} "
                "materialized_verifier_gate_work_orders="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
                "materialized_execution_rows="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_execution_rows')} "
                "materialized_executor_ran="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_ran')} "
                "materialized_source_kernel_verified="
                f"{payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified')} "
                "late_queue_ran="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_ran')} "
                "late_approved="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_approved_packets')} "
                "late_llm_approved="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_packets')} "
                "late_llm_approved_requiring_verifier_gate="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate')} "
                "late_verifier_gate_work_orders="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
                "late_execution_rows="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_execution_rows')} "
                "late_executor_ran="
                f"{payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_ran')}"
            ),
            (
                "approved exact semantic-definition review packets produced "
                "proof-body recheck rows but the exact proof-body executor did not run"
            ),
        ),
        _scorecard_row(
            "source_to_bridge_premise_derivation_from_formalizer_handoff_not_dropped",
            (
                payload.get(
                    "source_to_bridge_premise_derivation_from_formalizer_bridge_required"
                )
                is not True
            )
            or (
                payload.get(
                    "source_to_bridge_premise_derivation_from_formalizer_bridge_ran"
                )
                is True
            ),
            (
                "work_orders="
                f"{payload.get('n_runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer')} "
                "required="
                f"{payload.get('source_to_bridge_premise_derivation_from_formalizer_bridge_required')} "
                "ran="
                f"{payload.get('source_to_bridge_premise_derivation_from_formalizer_bridge_ran')} "
                "skipped="
                f"{payload.get('source_to_bridge_premise_derivation_from_formalizer_bridge_skipped_reason')} "
                "check_rows="
                f"{payload.get('source_to_bridge_premise_derivation_from_formalizer_bridge_n_rows')} "
                "learning_rows="
                f"{payload.get('source_to_bridge_premise_derivation_from_formalizer_bridge_n_learning_rows')} "
                "skipped_not_evidence_eligible="
                f"{payload.get('source_to_bridge_premise_derivation_from_formalizer_bridge_n_local_lean_skipped_not_evidence_eligible')} "
                "dominant_failure="
                f"{payload.get('source_to_bridge_premise_derivation_from_formalizer_bridge_dominant_failure_classification')}"
            ),
            (
                "Formalizer emitted source-to-bridge premise derivation work "
                "orders but the same-run ProofEngineer premise bridge did not run"
            ),
        ),
        _scorecard_row(
            "formalizer_premise_feedback_adapter_handoff_not_dropped",
            int(
                payload.get(
                    "n_runtime_source_theorem_proof_body_adapter_work_orders_from_formalizer_premise_derivation_feedback",
                    0,
                )
                or 0
            )
            <= 0
            or (
                payload.get(
                    "source_theorem_proof_body_adapter_proofengineer_bridge_ran"
                )
                is True
            ),
            (
                "adapter_work_orders_from_formalizer_premise_feedback="
                f"{payload.get('n_runtime_source_theorem_proof_body_adapter_work_orders_from_formalizer_premise_derivation_feedback')} "
                "adapter_bridge_ran="
                f"{payload.get('source_theorem_proof_body_adapter_proofengineer_bridge_ran')} "
                "adapter_bridge_rows="
                f"{payload.get('source_theorem_proof_body_adapter_proofengineer_bridge_n_rows')} "
                "skipped="
                f"{payload.get('source_theorem_proof_body_adapter_proofengineer_bridge_skipped_reason')}"
            ),
            (
                "Formalizer premise-derivation feedback generated source-theorem "
                "adapter work orders, but the same-run adapter ProofEngineer "
                "bridge did not run"
            ),
        ),
        _scorecard_row(
            "adapter_premise_feedback_adapter_retry_not_silently_dropped",
            int(
                payload.get(
                    "n_runtime_source_theorem_proof_body_adapter_work_orders_from_adapter_premise_derivation_feedback",
                    0,
                )
                or 0
            )
            <= 0
            or (
                payload.get(
                    "source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_ran"
                )
                is True
            ),
            (
                "adapter_work_orders_from_adapter_premise_feedback="
                f"{payload.get('n_runtime_source_theorem_proof_body_adapter_work_orders_from_adapter_premise_derivation_feedback')} "
                "retry_bridge_ran="
                f"{payload.get('source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_ran')} "
                "skipped="
                f"{payload.get('source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_skipped_reason')}"
            ),
            (
                "Adapter-generated premise-derivation feedback produced "
                "source-theorem adapter work orders, but the runtime does not "
                "yet run the bounded same-run adapter retry"
            ),
        ),
        _scorecard_row(
            "adapter_premise_verified_adapter_exact_retry_queued",
            int(
                payload.get(
                    "source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_n_adapter_kernel_verified",
                    0,
                )
                or 0
            )
            <= 0
            or (
                int(
                    payload.get(
                        "n_runtime_source_theorem_exact_proof_body_repair_work_orders_from_adapter_premise_derivation_feedback",
                        0,
                    )
                    or 0
                )
                > 0
                and payload.get(
                    "source_theorem_exact_proof_body_repair_execution_queue_from_adapter_premise_derivation_feedback_ran"
                )
                is True
            ),
            (
                "adapter_retry_kernel_verified="
                f"{payload.get('source_theorem_proof_body_adapter_from_adapter_premise_derivation_feedback_bridge_n_adapter_kernel_verified')} "
                "exact_repair_work_orders="
                f"{payload.get('n_runtime_source_theorem_exact_proof_body_repair_work_orders_from_adapter_premise_derivation_feedback')} "
                "exact_queue_ran="
                f"{payload.get('source_theorem_exact_proof_body_repair_execution_queue_from_adapter_premise_derivation_feedback_ran')}"
            ),
            (
                "Adapter-premise feedback produced a kernel-verified source-to-bridge "
                "adapter, but the runtime did not queue the exact source-theorem "
                "proof-body retry"
            ),
        ),
        _scorecard_row(
            "adapter_premise_verified_adapter_exact_executor_ran_when_requested",
            (
                payload.get(
                    "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_requested"
                )
                is not True
            )
            or (
                payload.get(
                    "source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_ran"
                )
                is True
            ),
            (
                "exact_executor_requested="
                f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_requested')} "
                "exact_executor_ran="
                f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_ran')} "
                "exact_executor_results="
                f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_adapter_premise_derivation_feedback_n_result_rows')}"
            ),
            (
                "Adapter-premise verified-adapter exact source-theorem proof-body "
                "executor was requested but did not run"
            ),
        ),
        _scorecard_row(
            "source_theorem_proof_body_local_lean_gate_requested",
            (
                payload.get(
                    "source_theorem_formal_environment_proof_body_executor_local_lean_requested"
                )
                is True
            ),
            (
                "local_lean_requested="
                f"{payload.get('source_theorem_formal_environment_proof_body_executor_local_lean_requested')}"
            ),
            "exact source-theorem proof-body executor did not request local Lean",
        ),
        _scorecard_row(
            "live_lean_lsp_mcp_called",
            int(payload.get("n_lean_lsp_mcp_live_calls", 0) or 0) > 0,
            f"n_lean_lsp_mcp_live_calls={payload.get('n_lean_lsp_mcp_live_calls')}",
            "Lean LSP/MCP was not called live for proof-state diagnostics",
        ),
        _scorecard_row(
            "real_kernel_subclaim_verified",
            int(payload.get("n_real_kernel_verified_subclaims", 0) or 0) > 0,
            f"n_real_kernel_verified_subclaims={payload.get('n_real_kernel_verified_subclaims')}",
            "no real AXLE/local Lean kernel-verified subclaim was recorded",
        ),
        _scorecard_row(
            "no_formal_gaps_remaining",
            int(payload.get("n_formal_gaps", 0) or 0) <= 0,
            f"n_formal_gaps={payload.get('n_formal_gaps')}",
            "formal gaps remain open",
        ),
        _scorecard_row(
            "full_frontier_theorem_kernel_proved",
            int(payload.get("n_full_frontier_theorem_proved", 0) or 0) > 0
            or source_theorem_kernel_count > 0,
            (
                f"n_full_frontier_theorem_proved={payload.get('n_full_frontier_theorem_proved')} "
                "proof_body_source_kernel="
                f"{source_theorem_kernel_count}"
            ),
            "no full frontier theorem was kernel-proved",
        ),
    ]
    n_passed = sum(1 for row in rows if row["passed"])
    return {
        "artifact_kind": "RuntimeCapabilityScorecard",
        "scope": "live autonomous AI Statistician core runtime readiness",
        "runtime_evaluation_mode": str(payload.get("runtime_evaluation_mode", "")),
        "n_requirements": len(rows),
        "n_passed": n_passed,
        "n_failed": len(rows) - n_passed,
        "ready": n_passed == len(rows),
        "rows": rows,
        "boundary": (
            "This scorecard is a capability truth table. It separates runtime "
            "contract health from live-agent ability and Lean-kernel theorem evidence."
        ),
    }


def _research_path_summary_detail(payload: Mapping[str, Any]) -> str:
    summary = payload.get("runtime_research_path_execution_summary", {})
    if not isinstance(summary, Mapping):
        return "missing"
    return (
        "controlled="
        f"{summary.get('n_controlled_artifacts')} "
        "with_contract="
        f"{summary.get('n_controlled_artifacts_with_evidence_contract')} "
        "policy_mismatches="
        f"{summary.get('n_policy_mismatches')} "
        "path_mismatches="
        f"{summary.get('n_path_mismatches')} "
        "subsystems="
        f"{summary.get('controlled_subsystems')}"
    )


def _scorecard_row(
    requirement_id: str,
    passed: bool,
    evidence: str,
    blocker: str,
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "passed": bool(passed),
        "evidence": evidence,
        "blocker": "" if passed else blocker,
    }


def _runtime_evidence_truth_table(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _runtime_evidence_truth_table_from_manifest(payload)


def _trace_has_runtime_learning_memory_input(traces: list[Any]) -> bool:
    for trace in traces:
        if not isinstance(trace, Mapping):
            continue
        task = trace.get("task", {}) if isinstance(trace.get("task"), Mapping) else {}
        inputs = task.get("inputs", {}) if isinstance(task.get("inputs"), Mapping) else {}
        context = inputs.get("architect_context", {}) if isinstance(inputs.get("architect_context"), Mapping) else {}
        memory = context.get("runtime_learning_memory", {})
        if isinstance(memory, Mapping) and memory.get("artifact_kind") == "RuntimeLearningMemoryContext":
            return True
    return False


def _trace_has_architect_runtime_field(traces: list[Any], field: str) -> bool:
    for trace in traces:
        if not isinstance(trace, Mapping):
            continue
        task = trace.get("task", {}) if isinstance(trace.get("task"), Mapping) else {}
        inputs = task.get("inputs", {}) if isinstance(task.get("inputs"), Mapping) else {}
        context = inputs.get("architect_context", {}) if isinstance(inputs.get("architect_context"), Mapping) else {}
        plan = context.get("architect_runtime_plan", {})
        if not isinstance(plan, Mapping):
            continue
        value = plan.get(field)
        if value not in ({}, [], "", None):
            return True
    return False


def _resolve_manifest_paths(runtime_dir: Path, manifest: Mapping[str, Any]) -> list[Path]:
    artifacts = manifest.get("artifacts", {}) if isinstance(manifest.get("artifacts"), Mapping) else {}
    raw_paths = artifacts.get("per_question_results", [])
    paths: list[Path] = []
    if isinstance(raw_paths, list):
        for raw in raw_paths:
            path = _resolve_path(runtime_dir, str(raw))
            if path:
                paths.append(path)
    return paths


def _resolve_path(base: Path, raw: object) -> Path:
    text = str(raw or "").strip()
    if not text:
        return base / "__missing_path__"
    path = Path(text)
    if path.is_absolute() or path.exists():
        return path
    candidates = [base / path]
    parts = path.parts
    if len(parts) >= 2 and base.parent.name and parts[0] == base.parent.name:
        candidates.append(base.parent.parent / path)
    if parts and parts[0] == base.name:
        candidates.append(base.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _formalizer_lean_candidate_repair_sequences_from_result_paths(
    result_paths: list[Path],
) -> int:
    total = 0
    for path in result_paths:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, Mapping):
            continue
        blackboard = (
            payload.get("blackboard", {})
            if isinstance(payload.get("blackboard"), Mapping)
            else {}
        )
        artifacts = (
            blackboard.get("artifacts", {})
            if isinstance(blackboard.get("artifacts"), Mapping)
            else {}
        )
        if not isinstance(artifacts, Mapping):
            continue
        total += _formalizer_lean_candidate_repair_sequence_count(artifacts)
    return total


def _runtime_theory_summary_from_result_paths(
    result_paths: list[Path],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for path in result_paths:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            results.append(payload)
    if not results:
        return {}
    summary = _runtime_evidence_summary(results)
    theory = summary.get("theory", {}) if isinstance(summary, Mapping) else {}
    return dict(theory) if isinstance(theory, Mapping) else {}


def _merge_runtime_theory_summaries(
    manifest_summary: Mapping[str, Any],
    derived_summary: Mapping[str, Any],
) -> dict[str, Any]:
    merged: dict[str, Any] = dict(manifest_summary)
    integer_keys = (
        "n_theory_derivation_packets",
        "n_theory_derivation_packets_with_contract",
        "n_theory_derivation_packets_with_min_derivation_steps",
        "n_theory_derivation_packets_with_equation_chain",
        "n_theory_derivation_packets_with_assumption_ledger",
        "n_theory_derivation_packets_with_formalization_handoff",
        "n_theory_trace_consumption_contracts",
        "n_theory_trace_consumption_contracts_with_trace",
        "n_theory_trace_consumption_contracts_with_equation_chain",
        "n_theory_trace_consumption_contracts_with_assumption_ledger",
        "n_theory_trace_consumption_contracts_with_formalization_handoff",
        "n_theory_trace_alignment_contracts",
        "n_theory_trace_alignment_contracts_with_llm_alignment",
        "n_structured_theory_trace_alignment_contracts",
        "n_theory_trace_alignment_contracts_with_unsupported_anchors",
        "max_derivation_steps",
        "max_equation_chain_steps",
        "max_assumption_ledger_rows",
    )
    for key in integer_keys:
        merged[key] = max(
            _safe_int(merged.get(key, 0)),
            _safe_int(derived_summary.get(key, 0)),
        )

    list_keys = (
        "theory_trace_consuming_subsystems",
        "structured_theory_trace_consuming_subsystems",
        "required_theory_trace_consumers",
        "theory_trace_aligned_subsystems",
        "structured_theory_trace_aligned_subsystems",
    )
    for key in list_keys:
        merged[key] = sorted(
            {
                str(value)
                for source in (merged.get(key, []), derived_summary.get(key, []))
                if isinstance(source, list)
                for value in source
                if str(value).strip()
            }
        )

    boolean_keys = (
        "all_required_theory_trace_consumers_observed",
        "all_required_theory_trace_alignment_consumers_observed",
        "structured_derivation_trace_observed",
    )
    for key in boolean_keys:
        merged[key] = bool(merged.get(key, False)) or bool(
            derived_summary.get(key, False)
        )

    for key in (
        "theory_trace_consumption_boundary",
        "theory_trace_alignment_boundary",
        "boundary",
    ):
        if not str(merged.get(key, "") or "").strip():
            value = str(derived_summary.get(key, "") or "").strip()
            if value:
                merged[key] = value
    return merged


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _artifacts_with_prefix(artifacts: Mapping[str, Any], prefix: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in artifacts.items():
        if str(key).startswith(prefix) and isinstance(value, Mapping):
            rows.append(dict(value))
    return rows


def _proof_state_feedback_artifacts(artifacts: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for prefix in PROOF_STATE_FEEDBACK_ARTIFACT_PREFIXES:
        rows.extend(_artifacts_with_prefix(artifacts, prefix))
    return rows


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse JSON {path}: {type(exc).__name__}: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"JSON file is not an object: {path}")
        return {}
    return payload


def _load_jsonl(path: Path, errors: list[str], *, required: bool) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        if required:
            errors.append(f"failed to read JSONL file {path}: {type(exc).__name__}: {exc}")
        return []
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"failed to parse JSONL {path}:{idx}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"JSONL row is not an object: {path}:{idx}")
    return rows


def _markdown_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Research Agent Runtime Audit",
        "",
        f"- all_ok: {payload.get('all_ok')}",
        f"- capability_ready_for_full_ai_statistician: {payload.get('capability_ready_for_full_ai_statistician')}",
        f"- capability_status: {payload.get('capability_status')}",
        f"- capability scorecard: {payload.get('capability_scorecard', {}).get('n_passed')}/"
        f"{payload.get('capability_scorecard', {}).get('n_requirements')} passed",
        f"- capability ladder max contiguous level: {payload.get('capability_ladder', {}).get('max_contiguous_level')}",
        f"- capability ladder max contiguous label: {payload.get('capability_ladder', {}).get('max_contiguous_level_label')}",
        f"- capability ladder max evidence level: {payload.get('capability_ladder', {}).get('max_evidence_level')}",
        f"- capability ladder max evidence label: {payload.get('capability_ladder', {}).get('max_evidence_level_label')}",
        f"- capability ladder current label: {payload.get('capability_ladder', {}).get('current_level_label')}",
        "- capability ladder noncontiguous evidence observed: "
        f"{payload.get('capability_ladder', {}).get('noncontiguous_evidence_observed')}",
        f"- evidence truth table source theorem kernel verified: {payload.get('evidence_truth_table', {}).get('source_theorem_kernel_verified')}",
        f"- evidence truth table formal gaps open: {payload.get('evidence_truth_table', {}).get('formal_gaps_open')}",
        f"- current exact proof-body blocker: {payload.get('evidence_truth_table', {}).get('current_exact_proof_body_blocker')}",
        f"- runtime evaluation mode: {payload.get('runtime_evaluation_mode')}",
        f"- results: {payload.get('n_ok')}/{payload.get('n_results')}",
        f"- result errors: {payload.get('n_result_errors')}",
        f"- runtime progress events: {payload.get('n_runtime_progress_events')}",
        f"- runtime traces: {payload.get('n_runtime_traces')}",
        f"- agenda items: {payload.get('n_runtime_next_action_items')}",
        f"- learning rows: {payload.get('n_runtime_learning_rows')}",
        f"- live generator agents enabled: {payload.get('n_live_generator_agents_enabled')}",
        f"- ArchitectCoordinator enabled: {payload.get('architect_coordinator_enabled')}",
        f"- LLM topology policy ok: {payload.get('llm_topology_policy_ok')}",
        f"- unsupported generator backends: {payload.get('unsupported_generator_backends_enabled')}",
        f"- critic reroutes: {payload.get('n_critic_reroutes')}",
        f"- theory derivation packets: {payload.get('n_theory_derivation_packets')}",
        "- structured theory derivation trace observed: "
        f"{payload.get('structured_theory_derivation_trace_observed')}",
        "- theory packets with equation chain / assumption ledger / formalization handoff: "
        f"{payload.get('n_theory_derivation_packets_with_equation_chain')} / "
        f"{payload.get('n_theory_derivation_packets_with_assumption_ledger')} / "
        f"{payload.get('n_theory_derivation_packets_with_formalization_handoff')}",
        f"- theory derivation trace boundary: {payload.get('theory_derivation_trace_boundary')}",
        "- downstream theory trace consumers: "
        f"{payload.get('theory_trace_consuming_subsystems')}",
        "- structured downstream theory trace consumers: "
        f"{payload.get('structured_theory_trace_consuming_subsystems')}",
        "- required downstream theory trace consumers observed: "
        f"{payload.get('all_required_theory_trace_consumers_observed')}",
        "- theory trace consumption contracts with trace / equation chain / assumption ledger / formalization handoff: "
        f"{payload.get('n_theory_trace_consumption_contracts_with_trace')} / "
        f"{payload.get('n_theory_trace_consumption_contracts_with_equation_chain')} / "
        f"{payload.get('n_theory_trace_consumption_contracts_with_assumption_ledger')} / "
        f"{payload.get('n_theory_trace_consumption_contracts_with_formalization_handoff')}",
        f"- theory trace consumption boundary: {payload.get('theory_trace_consumption_boundary')}",
        "- structured downstream theory trace alignment consumers: "
        f"{payload.get('structured_theory_trace_aligned_subsystems')}",
        "- required downstream theory trace alignment consumers observed: "
        f"{payload.get('all_required_theory_trace_alignment_consumers_observed')}",
        "- theory trace alignment contracts total / claimed / structured / unsupported: "
        f"{payload.get('n_theory_trace_alignment_contracts')} / "
        f"{payload.get('n_theory_trace_alignment_contracts_with_llm_alignment')} / "
        f"{payload.get('n_structured_theory_trace_alignment_contracts')} / "
        f"{payload.get('n_theory_trace_alignment_contracts_with_unsupported_anchors')}",
        f"- theory trace alignment boundary: {payload.get('theory_trace_alignment_boundary')}",
        f"- algorithm sandbox executed: {payload.get('n_algorithm_sandbox_executed')}",
        f"- generated-code sandbox executed: {payload.get('n_generated_code_sandbox_executed')}",
        f"- generated-code metric gate failed: {payload.get('n_generated_code_sandbox_metric_gate_failed')}",
        "- generated-code fail->pass repair sequences: "
        f"{payload.get('n_generated_code_sandbox_failed_then_passed_repair_sequences')}",
        f"- unsafe generated-code rejected: {payload.get('n_unsafe_generated_code_rejected')}",
        f"- generated simulation sandbox executed: {payload.get('n_generated_simulation_sandbox_executed')}",
        f"- generated simulation sandbox passed: {payload.get('n_generated_simulation_sandbox_passed')}",
        f"- generated simulation metric gate failed: {payload.get('n_generated_simulation_sandbox_metric_gate_failed')}",
        "- generated simulation fail->pass repair sequences: "
        f"{payload.get('n_generated_simulation_sandbox_failed_then_passed_repair_sequences')}",
        f"- unsafe generated simulation rejected: {payload.get('n_unsafe_generated_simulation_code_rejected')}",
        f"- Lean LSP/MCP live calls: {payload.get('n_lean_lsp_mcp_live_calls')}",
        f"- runtime-learning-memory inputs: {payload.get('n_results_with_runtime_learning_memory_input')}",
        f"- runtime-learning-memory input rows: {payload.get('n_runtime_learning_memory_input_rows')}",
        f"- problem-analysis rows: {payload.get('n_results_with_problem_analysis')}",
        f"- stat-knowledge-bank rows: {payload.get('n_results_with_stat_knowledge_bank_plan')}",
        f"- literature-fair-comparison rows: {payload.get('n_results_with_literature_fair_comparison_plan')}",
        f"- kernel verified subclaims: {payload.get('n_kernel_verified_subclaims')}",
        f"- results with kernel evidence: {payload.get('n_results_with_kernel_evidence')}",
        f"- has real kernel evidence: {payload.get('has_real_kernel_evidence')}",
        f"- results with real kernel evidence: {payload.get('n_results_with_real_kernel_evidence')}",
        f"- real-kernel verified subclaims: {payload.get('n_real_kernel_verified_subclaims')}",
        f"- non-real-kernel verified subclaims: {payload.get('n_non_real_kernel_verified_subclaims')}",
        f"- kernel verified verifiers: {payload.get('kernel_verified_verifiers')}",
        f"- runtime-memory kernel proof obligations: {payload.get('n_runtime_memory_kernel_verified_proof_obligation_ids')}",
        f"- runtime-memory theorem closure goals: {payload.get('n_runtime_memory_kernel_verified_theorem_reduction_closure_goal_ids')}",
        f"- runtime-memory semantic primitives: {payload.get('n_runtime_memory_kernel_verified_source_theorem_semantic_primitive_ids')}",
        f"- formal gaps: {payload.get('n_formal_gaps')}",
        f"- registered proof-obligation candidates: {payload.get('n_registered_proof_bank_obligation_candidates')}",
        f"- memory-prioritized proof obligations: {payload.get('n_memory_prioritized_proof_obligations')}",
        f"- memory off-catalog proof obligations: {payload.get('n_memory_off_catalog_proof_obligations')}",
        f"- memory-rejected proof obligations: {payload.get('n_memory_rejected_proof_obligations')}",
        f"- LLM-requested proof obligations: {payload.get('n_llm_requested_proof_obligations')}",
        f"- LLM off-catalog proof obligations: {payload.get('n_llm_off_catalog_proof_obligations')}",
        f"- LLM-rejected proof obligations: {payload.get('n_llm_rejected_proof_obligations')}",
        f"- full frontier theorem proved: {payload.get('n_full_frontier_theorem_proved')}",
        "- source-theorem kernel verified total: "
        f"{_payload_source_theorem_kernel_count(payload)}",
        "- exact proof-body repair executor source-kernel verified: "
        f"{payload.get('source_theorem_exact_proof_body_repair_executor_n_source_theorem_kernel_verified')}",
        "- post-adapter exact proof-body retry queue ran: "
        f"{payload.get('source_theorem_exact_proof_body_repair_execution_queue_from_proof_body_adapter_feedback_ran')}",
        "- post-adapter exact proof-body executor ran: "
        f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_ran')}",
        "- post-adapter exact proof-body executor source-kernel verified: "
        f"{payload.get('source_theorem_exact_proof_body_repair_executor_from_proof_body_adapter_feedback_n_source_theorem_kernel_verified')}",
        "- source theorem promotion source-kernel verified: "
        f"direct={payload.get('source_theorem_promotion_proofengineer_bridge_n_source_theorem_kernel_verified')} "
        f"source_semantic={payload.get('source_theorem_promotion_source_semantic_proofengineer_bridge_n_source_theorem_kernel_verified')} "
        f"post_executor={payload.get('source_theorem_promotion_post_executor_proofengineer_bridge_n_source_theorem_kernel_verified')}",
        "- post-adapter semantic primitive work orders: "
        f"{payload.get('n_runtime_new_source_theorem_semantic_primitive_work_orders_from_proof_body_adapter_feedback')}",
        "- exact semantic-definition work orders: "
        f"{payload.get('n_runtime_source_theorem_exact_semantic_definition_work_orders')}",
        "- exact semantic-definition source lookup: "
        f"required={payload.get('source_theorem_exact_semantic_definition_source_lookup_required')} "
        f"ran={payload.get('source_theorem_exact_semantic_definition_source_lookup_ran')} "
        f"skipped={payload.get('source_theorem_exact_semantic_definition_source_lookup_skipped_reason')}",
        "- exact semantic-definition ProofEngineer bridge: "
        f"required={payload.get('source_theorem_exact_semantic_definition_proofengineer_bridge_required')} "
        f"ran={payload.get('source_theorem_exact_semantic_definition_proofengineer_bridge_ran')} "
        f"skipped={payload.get('source_theorem_exact_semantic_definition_proofengineer_bridge_skipped_reason')}",
        "- exact semantic-definition Lean repair executor: "
        f"required={payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_required')} "
        f"ran={payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_ran')} "
        f"local_lean_requested={payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_local_lean_requested')} "
        f"skipped={payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_skipped_reason')}",
        "- exact semantic-definition candidate-synthesis proof-body recheck: "
        f"queue_rows={payload.get('source_theorem_exact_semantic_definition_candidate_synthesis_n_proof_body_recheck_queue_rows')} "
        f"executor_ran={payload.get('source_theorem_exact_semantic_definition_proof_body_recheck_executor_ran')} "
        f"result_rows={payload.get('source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_result_rows')} "
        f"source_kernel_verified={payload.get('source_theorem_exact_semantic_definition_proof_body_recheck_executor_n_source_theorem_kernel_verified')} "
        f"failure={payload.get('source_theorem_exact_semantic_definition_proof_body_recheck_executor_dominant_failure_classification')}",
        "- exact semantic-definition late typechecked review: "
        f"primary_materialized_packets={payload.get('source_theorem_exact_semantic_definition_materialized_lean_repair_executor_n_typechecked_candidate_review_packets')} "
        f"primary_materialized_required={payload.get('source_theorem_exact_semantic_definition_materialized_candidate_review_required')} "
        f"primary_materialized_bridge_ran={payload.get('source_theorem_exact_semantic_definition_materialized_candidate_review_proofengineer_bridge_ran')} "
        f"primary_materialized_llm_approved={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_llm_approved_packets')} "
        f"primary_materialized_verifier_gate_work_orders={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
        f"late_materialized_packets={payload.get('source_theorem_exact_semantic_definition_late_materialized_lean_repair_executor_n_typechecked_candidate_review_packets')} "
        f"late_materialized_required={payload.get('source_theorem_exact_semantic_definition_late_materialized_candidate_review_required')} "
        f"late_packets={payload.get('source_theorem_exact_semantic_definition_late_lean_repair_executor_n_typechecked_candidate_review_packets')} "
        f"late_required={payload.get('source_theorem_exact_semantic_definition_late_lean_repair_executor_typechecked_candidate_review_required')} "
        f"primary_required={payload.get('source_theorem_exact_semantic_definition_lean_repair_executor_typechecked_candidate_review_required')} "
        f"repair_required={payload.get('source_theorem_exact_semantic_definition_repair_required')} "
        f"repair_reason={payload.get('source_theorem_exact_semantic_definition_repair_required_reason')}",
        "- exact semantic-definition typechecked-review proof-body recheck: "
        f"primary_queue_ran={payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_ran')} "
        f"primary_approved={payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_approved_packets')} "
        f"primary_llm_approved={payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_packets')} "
        f"primary_llm_approved_requiring_verifier_gate={payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate')} "
        f"primary_verifier_gate_work_orders={payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
        f"primary_blocked={payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_blocked_packets')} "
        f"primary_execution_rows={payload.get('source_theorem_exact_semantic_definition_typechecked_review_recheck_queue_n_execution_rows')} "
        f"primary_executor_ran={payload.get('source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_ran')} "
        f"primary_source_kernel_verified={payload.get('source_theorem_exact_semantic_definition_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified')} "
        f"materialized_queue_ran={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_ran')} "
        f"materialized_approved={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_approved_packets')} "
        f"materialized_llm_approved={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_llm_approved_packets')} "
        f"materialized_llm_approved_requiring_verifier_gate={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate')} "
        f"materialized_verifier_gate_work_orders={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
        f"materialized_blocked={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_blocked_packets')} "
        f"materialized_execution_rows={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_recheck_queue_n_execution_rows')} "
        f"materialized_executor_ran={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_ran')} "
        f"materialized_result_rows={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_n_result_rows')} "
        f"materialized_source_kernel_verified={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified')} "
        f"materialized_failure={payload.get('source_theorem_exact_semantic_definition_materialized_typechecked_review_proof_body_recheck_executor_dominant_failure_classification')} "
        f"late_queue_ran={payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_ran')} "
        f"late_approved={payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_approved_packets')} "
        f"late_llm_approved={payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_packets')} "
        f"late_llm_approved_requiring_verifier_gate={payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_llm_approved_requiring_verifier_gate')} "
        f"late_verifier_gate_work_orders={payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_verifier_gate_work_orders')} "
        f"late_blocked={payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_blocked_packets')} "
        f"late_execution_rows={payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_recheck_queue_n_execution_rows')} "
        f"late_executor_ran={payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_ran')} "
        f"late_source_kernel_verified={payload.get('source_theorem_exact_semantic_definition_late_typechecked_review_proof_body_recheck_executor_n_source_theorem_kernel_verified')}",
        "",
        "## Capability Gaps",
    ]
    if payload.get("capability_gaps"):
        for gap in payload.get("capability_gaps", []) or []:
            lines.append(f"- {gap}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Rows",
    ])
    for row in payload.get("rows", []) or []:
        lines.append(
            f"- {row.get('question_id')}: ok={row.get('ok')} traces={row.get('n_traces')} "
            f"kernel={row.get('n_kernel_verified_subclaims')} "
            f"real_kernel={row.get('n_real_kernel_verified_subclaims')} "
            f"gaps={row.get('n_formal_gaps')}"
        )
        for error in row.get("errors", []) or []:
            lines.append(f"  - error: {error}")
    if payload.get("errors"):
        lines.append("")
        lines.append("## Manifest Errors")
        for error in payload.get("errors", []) or []:
            lines.append(f"- {error}")
    return "\n".join(lines) + "\n"

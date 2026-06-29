from __future__ import annotations

import json
import shlex
from collections import Counter
from dataclasses import asdict, dataclass, replace
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
    SOURCE_THEOREM_PROOF_BODY_GOAL_EXCERPT_KEYS,
    SOURCE_THEOREM_PROOF_BODY_GOAL_EXCERPT_ROW_KEYS,
    SOURCE_THEOREM_PROOF_BODY_GOAL_REACHED_KEYS,
    SOURCE_THEOREM_PROOF_BODY_RESULT_ROW_KEYS,
    _formalizer_lean_candidate_repair_sequence_count,
    _generated_sandbox_repair_sequence_counts,
    _runtime_evidence_summary,
    _runtime_evidence_truth_table_from_manifest,
    _runtime_manifest_int_sum,
)
from .task_family import (
    explicit_task_family_list,
    is_explicit_task_family,
    primary_task_family_from_mapping,
    task_family_value,
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


def _compact_string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, int, float, bool)):
        raw_values = [values]
    elif isinstance(values, Mapping):
        raw_values = values.values()
    else:
        try:
            raw_values = list(values)
        except TypeError:
            raw_values = [values]
    compacted: list[str] = []
    for value in raw_values:
        text = str(value or "").strip()
        if text:
            compacted.append(text)
    return list(dict.fromkeys(compacted))


def _payload_distinct_task_family_count(payload: Mapping[str, Any]) -> int:
    raw_task_families = _compact_string_list(payload.get("task_families", []))
    task_families = explicit_task_family_list(raw_task_families)
    if raw_task_families:
        return len(task_families)
    explicit_count = int(payload.get("n_distinct_task_families", 0) or 0)
    if explicit_count > 0:
        return explicit_count
    return 0


def _payload_cross_task_full_theorem_family_count(
    payload: Mapping[str, Any],
) -> int:
    raw_proved_families = _compact_string_list(
        payload.get("task_families_with_full_frontier_theorem_proved", [])
    )
    proved_families = explicit_task_family_list(raw_proved_families)
    if raw_proved_families:
        return len(proved_families)
    explicit_count = int(
        payload.get("n_task_families_with_full_frontier_theorem_proved", 0) or 0
    )
    if explicit_count > 0:
        return explicit_count
    return 0


def _runtime_result_primary_task_family(payload: Mapping[str, Any]) -> str:
    family = primary_task_family_from_mapping(payload)
    if family:
        return family
    blackboard = (
        payload.get("blackboard", {})
        if isinstance(payload.get("blackboard", {}), Mapping)
        else {}
    )
    family = primary_task_family_from_mapping(blackboard)
    if family:
        return family
    artifacts = (
        blackboard.get("artifacts", {})
        if isinstance(blackboard.get("artifacts", {}), Mapping)
        else {}
    )
    for artifact in artifacts.values():
        if isinstance(artifact, Mapping):
            family = primary_task_family_from_mapping(artifact)
            if family:
                return family
    traces = payload.get("traces", [])
    if isinstance(traces, list):
        for trace in traces:
            if not isinstance(trace, Mapping):
                continue
            family = primary_task_family_from_mapping(trace)
            if family:
                return family
            task = trace.get("task", {})
            if isinstance(task, Mapping):
                family = primary_task_family_from_mapping(task)
                if family:
                    return family
                inputs = task.get("inputs", {})
                if isinstance(inputs, Mapping):
                    family = primary_task_family_from_mapping(inputs)
                    if family:
                        return family
    return ""


def _manifest_question_task_family_map(manifest: Mapping[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    raw_families = manifest.get("question_task_families", {})
    if isinstance(raw_families, Mapping):
        for question_id, family in raw_families.items():
            normalized = task_family_value(family)
            if is_explicit_task_family(normalized):
                out[str(question_id)] = normalized
    raw_tags = manifest.get("question_tags", {})
    if isinstance(raw_tags, Mapping):
        for question_id, tags in raw_tags.items():
            if str(question_id) in out:
                continue
            family = primary_task_family_from_mapping({"tags": tags})
            if is_explicit_task_family(family):
                out[str(question_id)] = family
    return out


def _rows_with_manifest_task_family_backfill(
    rows: list["RuntimeAuditRow"],
    manifest: Mapping[str, Any],
) -> tuple[list["RuntimeAuditRow"], int]:
    family_by_question = _manifest_question_task_family_map(manifest)
    if not family_by_question:
        return rows, 0
    backfilled: list[RuntimeAuditRow] = []
    n_backfilled = 0
    for row in rows:
        if is_explicit_task_family(row.task_family):
            backfilled.append(row)
            continue
        family = family_by_question.get(row.question_id, "")
        if not family:
            backfilled.append(row)
            continue
        backfilled.append(replace(row, task_family=family))
        n_backfilled += 1
    return backfilled, n_backfilled


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
    task_family: str
    result_path: str
    ok: bool
    status: str
    pending_next_task_id: str
    pending_next_task_owner_subsystem: str
    budget_exhausted_with_pending_next_task: bool
    budgeted_continuation_contract_ok: bool
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
    manifest_question_task_families = _manifest_question_task_family_map(manifest)
    rows, n_rows_task_family_backfilled_from_manifest = (
        _rows_with_manifest_task_family_backfill(rows, manifest)
    )
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        artifacts = {}
    trace_path = _resolve_path(runtime_dir, artifacts.get("runtime_traces_jsonl", ""))
    progress_path = _resolve_path(runtime_dir, artifacts.get("runtime_progress_jsonl", ""))
    agenda_path = _resolve_path(runtime_dir, artifacts.get("runtime_next_action_agenda_jsonl", ""))
    learning_path = _resolve_path(runtime_dir, artifacts.get("runtime_learning_rows_jsonl", ""))
    pending_task_raw_path = artifacts.get("runtime_pending_next_task_json", "")
    pending_task_payload = (
        _load_json(_resolve_path(runtime_dir, pending_task_raw_path), errors)
        if str(pending_task_raw_path or "").strip()
        else {}
    )
    runtime_pending_task_memory_rows = _runtime_pending_task_memory_rows(
        pending_task_payload
    )
    trace_rows = _load_jsonl(trace_path, errors, required=True)
    progress_rows = _load_jsonl(
        progress_path,
        errors,
        required=bool(artifacts.get("runtime_progress_jsonl")),
    )
    agenda_rows = _load_jsonl(agenda_path, errors, required=True)
    learning_rows = _load_jsonl(learning_path, errors, required=True)
    exact_semantic_definition_authoring_task_rows = (
        _runtime_exact_semantic_definition_authoring_task_rows(
            runtime_dir=runtime_dir,
            artifacts=artifacts,
            errors=errors,
        )
    )
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

    runtime_handoff_artifact_missing_summary = (
        _runtime_handoff_artifact_missing_audit_summary(
            manifest=manifest,
            learning_rows=learning_rows,
            agenda_rows=agenda_rows,
        )
    )
    runtime_target_identity_summary = _runtime_target_identity_audit_summary(
        pending_memory_rows=(
            runtime_pending_task_memory_rows
            if str(pending_task_raw_path or "").strip()
            else None
        ),
        learning_rows=learning_rows,
        agenda_rows=agenda_rows,
    )
    runtime_source_to_bridge_feedback_contract_summary = (
        _runtime_source_to_bridge_feedback_contract_audit_summary(
            pending_task_payload=(
                pending_task_payload
                if str(pending_task_raw_path or "").strip()
                else None
            ),
            pending_memory_rows=(
                runtime_pending_task_memory_rows
                if str(pending_task_raw_path or "").strip()
                else None
            ),
            learning_rows=learning_rows,
        )
    )
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
        "runtime_resume_policy": str(manifest.get("runtime_resume_policy", "") or ""),
        "runtime_resumed_from_pending_task": bool(
            manifest.get("runtime_resumed_from_pending_task") is True
            or (
                isinstance(manifest.get("runtime_resume_context", {}), Mapping)
                and int(
                    manifest.get("runtime_resume_context", {}).get(
                        "n_initial_task_overrides",
                        0,
                    )
                    or 0
                )
                > 0
            )
        ),
        "runtime_resume_context": (
            dict(manifest.get("runtime_resume_context", {}) or {})
            if isinstance(manifest.get("runtime_resume_context", {}), Mapping)
            else {}
        ),
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
        "question_ids": sorted(
            {row.question_id for row in rows if row.question_id}
        ),
        "n_distinct_question_ids": len(
            {row.question_id for row in rows if row.question_id}
        ),
        "task_families": sorted(
            {
                row.task_family
                for row in rows
                if is_explicit_task_family(row.task_family)
            }
        ),
        "n_distinct_task_families": len(
            {
                row.task_family
                for row in rows
                if is_explicit_task_family(row.task_family)
            }
        ),
        "manifest_question_task_families": dict(
            sorted(manifest_question_task_families.items())
        ),
        "n_rows_task_family_backfilled_from_manifest": (
            n_rows_task_family_backfilled_from_manifest
        ),
        "question_ids_with_full_frontier_theorem_proved": sorted(
            {
                row.question_id
                for row in rows
                if row.question_id and row.full_frontier_theorem_proved
            }
        ),
        "n_question_ids_with_full_frontier_theorem_proved": len(
            {
                row.question_id
                for row in rows
                if row.question_id and row.full_frontier_theorem_proved
            }
        ),
        "task_families_with_full_frontier_theorem_proved": sorted(
            {
                row.task_family
                for row in rows
                if (
                    is_explicit_task_family(row.task_family)
                    and row.full_frontier_theorem_proved
                )
            }
        ),
        "n_task_families_with_full_frontier_theorem_proved": len(
            {
                row.task_family
                for row in rows
                if (
                    is_explicit_task_family(row.task_family)
                    and row.full_frontier_theorem_proved
                )
            }
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_budget_exhausted_with_pending_next_task": sum(
            1 for row in rows if row.budget_exhausted_with_pending_next_task
        ),
        "n_budgeted_continuation_contract_ok": sum(
            1 for row in rows if row.budgeted_continuation_contract_ok
        ),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "result_errors": result_errors,
        "n_result_errors": sum(len(row["errors"]) for row in result_errors),
        "by_status": dict(sorted(by_status.items())),
        "n_runtime_progress_events": len(progress_rows),
        "n_runtime_traces": len(trace_rows),
        "n_runtime_next_action_items": len(agenda_rows),
        "n_runtime_learning_rows": len(learning_rows),
        "n_runtime_pending_task_memory_rows": len(runtime_pending_task_memory_rows),
        "n_runtime_handoff_artifact_missing_feedback_rows": int(
            runtime_handoff_artifact_missing_summary[
                "n_runtime_handoff_artifact_missing_feedback_rows"
            ]
        ),
        "n_runtime_handoff_artifact_missing_learning_rows": int(
            runtime_handoff_artifact_missing_summary[
                "n_runtime_handoff_artifact_missing_learning_rows"
            ]
        ),
        "n_runtime_handoff_artifact_missing_agenda_rows": int(
            runtime_handoff_artifact_missing_summary[
                "n_runtime_handoff_artifact_missing_agenda_rows"
            ]
        ),
        "runtime_handoff_artifact_missing_ids": list(
            runtime_handoff_artifact_missing_summary[
                "runtime_handoff_artifact_missing_ids"
            ]
        ),
        "runtime_handoff_artifact_missing_roles": list(
            runtime_handoff_artifact_missing_summary[
                "runtime_handoff_artifact_missing_roles"
            ]
        ),
        "runtime_handoff_artifact_missing_owner_subsystems": list(
            runtime_handoff_artifact_missing_summary[
                "runtime_handoff_artifact_missing_owner_subsystems"
            ]
        ),
        "runtime_handoff_artifact_missing_boundary": str(
            runtime_handoff_artifact_missing_summary[
                "runtime_handoff_artifact_missing_boundary"
            ]
        ),
        "n_runtime_route_critical_target_identity_rows": int(
            runtime_target_identity_summary[
                "n_runtime_route_critical_target_identity_rows"
            ]
        ),
        "n_runtime_route_critical_rows_missing_target_ids": int(
            runtime_target_identity_summary[
                "n_runtime_route_critical_rows_missing_target_ids"
            ]
        ),
        "runtime_route_critical_rows_missing_target_ids": list(
            runtime_target_identity_summary[
                "runtime_route_critical_rows_missing_target_ids"
            ]
        ),
        "runtime_route_critical_target_identity_channels": list(
            runtime_target_identity_summary[
                "runtime_route_critical_target_identity_channels"
            ]
        ),
        "runtime_route_critical_target_identity_boundary": str(
            runtime_target_identity_summary[
                "runtime_route_critical_target_identity_boundary"
            ]
        ),
        "n_runtime_source_to_bridge_feedback_contract_rows": int(
            runtime_source_to_bridge_feedback_contract_summary[
                "n_runtime_source_to_bridge_feedback_contract_rows"
            ]
        ),
        "n_runtime_source_to_bridge_feedback_rows_missing_declaration_contract": int(
            runtime_source_to_bridge_feedback_contract_summary[
                "n_runtime_source_to_bridge_feedback_rows_missing_declaration_contract"
            ]
        ),
        "runtime_source_to_bridge_feedback_rows_missing_declaration_contract": list(
            runtime_source_to_bridge_feedback_contract_summary[
                "runtime_source_to_bridge_feedback_rows_missing_declaration_contract"
            ]
        ),
        "runtime_source_to_bridge_feedback_contract_channels": list(
            runtime_source_to_bridge_feedback_contract_summary[
                "runtime_source_to_bridge_feedback_contract_channels"
            ]
        ),
        "runtime_source_to_bridge_feedback_contract_boundary": str(
            runtime_source_to_bridge_feedback_contract_summary[
                "runtime_source_to_bridge_feedback_contract_boundary"
            ]
        ),
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
        "n_source_theorem_exact_semantic_definition_authoring_tasks": len(
            exact_semantic_definition_authoring_task_rows
        ),
        "source_theorem_exact_semantic_definition_authoring_worker_required": bool(
            exact_semantic_definition_authoring_task_rows
        ),
        "source_theorem_exact_semantic_definition_authoring_worker_requested": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_worker_requested",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_authoring_worker_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_worker_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_authoring_worker_skipped_reason": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_worker_skipped_reason",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_authoring_worker_dry_run": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_worker_dry_run",
                True,
            )
        ),
        "source_theorem_exact_semantic_definition_authoring_worker_external_export_mode": str(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_worker_external_export_mode",
                "",
            )
            or ""
        ),
        "source_theorem_exact_semantic_definition_authoring_worker_n_prompt_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_worker_n_prompt_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_authoring_worker_n_llm_attempted": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_worker_n_llm_attempted",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_authoring_candidate_materializer_ran": bool(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_candidate_materializer_ran",
                False,
            )
        ),
        "source_theorem_exact_semantic_definition_authoring_candidate_materializer_n_candidate_packets": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_candidate_materializer_n_candidate_packets",
                0,
            )
            or 0
        ),
        "source_theorem_exact_semantic_definition_authoring_candidate_materializer_n_materialized_lean_repair_tasks": int(
            manifest.get(
                "source_theorem_exact_semantic_definition_authoring_candidate_materializer_n_materialized_lean_repair_tasks",
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
    payload["runtime_architect_control_status"] = _runtime_architect_control_status(
        payload
    )
    payload["runtime_architect_orchestration_evidence"] = (
        _runtime_architect_orchestration_evidence(payload)
    )
    payload["runtime_architect_orchestration_blocker"] = (
        _runtime_architect_orchestration_blocker(payload)
    )
    payload["source_theorem_proof_body_goal_reached_evidence_count"] = (
        _payload_source_theorem_proof_body_goal_reached_count(payload)
    )
    payload["source_theorem_proof_body_result_row_count"] = (
        _payload_source_theorem_proof_body_result_row_count(payload)
    )
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
    pending_contract = _runtime_result_pending_next_task_contract(data, traces)
    pending_contract_errors = list(pending_contract["errors"])
    budgeted_continuation_contract_ok = bool(pending_contract["ok"])
    architect_enabled = bool(subsystem_sequence and subsystem_sequence[0] == "ArchitectCoordinator")
    architect_resume = architect_enabled and _trace_is_architect_resume(traces)
    expected_sequence = (
        ("ArchitectCoordinator",)
        if architect_resume
        else REQUIRED_ARCHITECT_SUBSYSTEMS
        if architect_enabled
        else REQUIRED_SUBSYSTEMS
    )
    static_order_ok = tuple(subsystem_sequence[: len(expected_sequence)]) == expected_sequence
    budgeted_continuation_order_ok = (
        budgeted_continuation_contract_ok
        and _runtime_trace_sequence_uses_known_subsystems(subsystem_sequence)
    )
    if not static_order_ok and not budgeted_continuation_order_ok:
        errors.append("runtime trace subsystem order is incomplete or misordered")
    if architect_resume and len(subsystem_sequence) > 1:
        pending_owner = _architect_resume_pending_owner(traces)
        if (
            pending_owner
            and subsystem_sequence[1] != pending_owner
            and not _architect_resume_routed_to_theory_refresh(traces)
        ):
            errors.append(
                "architect resume review did not route to the original pending subsystem"
            )
    if data.get("status") != "ACCEPTED":
        if budgeted_continuation_contract_ok:
            pass
        else:
            errors.append("runtime result status is not ACCEPTED")
            errors.extend(pending_contract_errors)

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
    task_family = _runtime_result_primary_task_family(data)
    return RuntimeAuditRow(
        question_id=question_id,
        task_family=task_family,
        result_path=str(path),
        ok=not errors,
        status=str(data.get("status", "")),
        pending_next_task_id=str(pending_contract["pending_next_task_id"]),
        pending_next_task_owner_subsystem=str(
            pending_contract["pending_next_task_owner_subsystem"]
        ),
        budget_exhausted_with_pending_next_task=bool(
            pending_contract["budget_exhausted_with_pending_next_task"]
        ),
        budgeted_continuation_contract_ok=budgeted_continuation_contract_ok,
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


def _architect_resume_routed_to_theory_refresh(traces: list[Any]) -> bool:
    if len(traces) < 2 or not isinstance(traces[1], Mapping):
        return False
    second = traces[1]
    if str(second.get("subsystem", "") or "") != "TheoryDeveloper":
        return False
    task = second.get("task", {})
    if not isinstance(task, Mapping):
        return False
    if not str(task.get("task_id", "") or "").startswith("theory-resume-refresh:"):
        return False
    inputs = task.get("inputs", {})
    if not isinstance(inputs, Mapping):
        return False
    feedback = (
        inputs.get("environment_feedback", {})
        if isinstance(inputs.get("environment_feedback", {}), Mapping)
        else {}
    )
    return (
        str(feedback.get("trigger", "") or "")
        == "RUNTIME_THEORY_DERIVATION_TRACE_INCOMPLETE"
        and str(feedback.get("feedback_source", "") or "") == "ArchitectCoordinator"
    )


def _runtime_trace_sequence_uses_known_subsystems(
    subsystem_sequence: list[str],
) -> bool:
    known_subsystems = set(REQUIRED_ARCHITECT_SUBSYSTEMS)
    return bool(subsystem_sequence) and all(
        str(subsystem or "") in known_subsystems
        for subsystem in subsystem_sequence
    )


def _runtime_result_pending_next_task_contract(
    data: Mapping[str, Any],
    traces: list[Any],
) -> dict[str, Any]:
    status = str(data.get("status", "") or "")
    errors: list[str] = []
    pending_next_task_id = ""
    pending_next_task_owner_subsystem = ""
    if status != "MAX_ITERATIONS_REACHED":
        return {
            "ok": False,
            "budget_exhausted_with_pending_next_task": False,
            "pending_next_task_id": "",
            "pending_next_task_owner_subsystem": "",
            "errors": (),
        }
    final_trace = traces[-1] if traces and isinstance(traces[-1], Mapping) else {}
    if not final_trace:
        errors.append("MAX_ITERATIONS_REACHED result has no final trace")
        return {
            "ok": False,
            "budget_exhausted_with_pending_next_task": False,
            "pending_next_task_id": "",
            "pending_next_task_owner_subsystem": "",
            "errors": tuple(errors),
        }
    pending_next_task_id = str(final_trace.get("next_task_id", "") or "").strip()
    pending_task = (
        final_trace.get("next_task", {})
        if isinstance(final_trace.get("next_task", {}), Mapping)
        else {}
    )
    if not pending_next_task_id:
        errors.append("MAX_ITERATIONS_REACHED result is missing next_task_id")
    if not pending_task:
        errors.append("MAX_ITERATIONS_REACHED result is missing routeable next_task")
    else:
        task_id = str(pending_task.get("task_id", "") or "").strip()
        pending_next_task_owner_subsystem = str(
            pending_task.get("owner_subsystem", "") or ""
        ).strip()
        if not task_id:
            errors.append("pending next_task is missing task_id")
        elif pending_next_task_id and task_id != pending_next_task_id:
            errors.append("pending next_task task_id does not match next_task_id")
        if not pending_next_task_owner_subsystem:
            errors.append("pending next_task is missing owner_subsystem")
        elif pending_next_task_owner_subsystem not in set(REQUIRED_ARCHITECT_SUBSYSTEMS):
            errors.append(
                "pending next_task owner_subsystem is not a known runtime subsystem"
            )
        if not isinstance(pending_task.get("inputs", {}), Mapping):
            errors.append("pending next_task inputs must be an object")
    return {
        "ok": not errors,
        "budget_exhausted_with_pending_next_task": bool(pending_next_task_id),
        "pending_next_task_id": pending_next_task_id,
        "pending_next_task_owner_subsystem": pending_next_task_owner_subsystem,
        "errors": tuple(errors),
    }


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


def _payload_source_theorem_proof_body_goal_reached_count(
    payload: Mapping[str, Any],
) -> int:
    return _runtime_manifest_int_sum(
        payload,
        SOURCE_THEOREM_PROOF_BODY_GOAL_REACHED_KEYS,
    ) + _runtime_manifest_int_sum(
        payload,
        SOURCE_THEOREM_PROOF_BODY_GOAL_EXCERPT_ROW_KEYS,
    ) + _runtime_manifest_int_sum(
        payload,
        SOURCE_THEOREM_PROOF_BODY_GOAL_EXCERPT_KEYS,
    )


def _payload_source_theorem_proof_body_result_row_count(
    payload: Mapping[str, Any],
) -> int:
    return _runtime_manifest_int_sum(
        payload,
        SOURCE_THEOREM_PROOF_BODY_RESULT_ROW_KEYS,
    )


def _runtime_architect_trace_count(payload: Mapping[str, Any]) -> int:
    return int(payload.get("n_runtime_architect_coordinator_traces", 0) or 0)


def _runtime_architect_orchestration_executed(payload: Mapping[str, Any]) -> bool:
    return bool(
        payload.get("architect_coordinator_enabled") is True
        or payload.get("runtime_architect_coordinator_executed") is True
        or _runtime_architect_trace_count(payload) > 0
    )


def _runtime_architect_context_propagated(payload: Mapping[str, Any]) -> bool:
    return bool(
        payload.get("runtime_research_path_control_propagated") is True
        or payload.get("runtime_resumed_from_pending_task") is True
        or str(payload.get("runtime_stage", "") or "").startswith("architect_")
        or str(payload.get("runtime_resume_policy", "") or "").startswith("direct_pending_task")
        or str(payload.get("architect_recommended_research_path", "") or "").strip()
        or str(
            payload.get("architect_recommended_formal_verification_policy", "") or ""
        ).strip()
        or str(payload.get("architect_coordinator_proposal_id", "") or "").strip()
    )


def _runtime_architect_control_status(payload: Mapping[str, Any]) -> str:
    if _runtime_architect_orchestration_executed(payload):
        return "PRESENT"
    if payload.get("runtime_architect_coordinator_registered") is True:
        return "REGISTERED_NOT_EXECUTED"
    if _runtime_architect_context_propagated(payload):
        return "PROPAGATED_FROM_RESUME"
    return "DISABLED"


def _runtime_architect_orchestration_evidence(payload: Mapping[str, Any]) -> str:
    return (
        "architect_coordinator_enabled="
        f"{payload.get('architect_coordinator_enabled')} "
        "runtime_architect_coordinator_registered="
        f"{payload.get('runtime_architect_coordinator_registered')} "
        "runtime_architect_coordinator_executed="
        f"{payload.get('runtime_architect_coordinator_executed')} "
        "n_runtime_architect_coordinator_traces="
        f"{_runtime_architect_trace_count(payload)} "
        "runtime_resume_policy="
        f"{payload.get('runtime_resume_policy', '')} "
        "architect_control_status="
        f"{_runtime_architect_control_status(payload)}"
    )


def _runtime_architect_orchestration_blocker(payload: Mapping[str, Any]) -> str:
    status = _runtime_architect_control_status(payload)
    if status == "PRESENT":
        return ""
    if status == "REGISTERED_NOT_EXECUTED":
        return (
            "ArchitectCoordinator was registered, but no ArchitectCoordinator trace "
            "executed in this runtime budget; rerun through ArchitectCoordinator "
            "before claiming architect-orchestrated research"
        )
    if status == "PROPAGATED_FROM_RESUME":
        return (
            "Architect-derived context was propagated, but no ArchitectCoordinator "
            "trace executed in this runtime budget; propagated context is "
            "continuity evidence, not architect-orchestrated research"
        )
    return (
        "ArchitectCoordinator was not configured or did not register; this is a "
        "subsystem-chain run, not architect-orchestrated research"
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


def _runtime_handoff_artifact_missing_audit_summary(
    *,
    manifest: Mapping[str, Any],
    learning_rows: list[Any],
    agenda_rows: list[Any],
) -> dict[str, Any]:
    learning_feedback_rows = [
        row
        for row in learning_rows
        if _is_runtime_handoff_artifact_missing_learning_row(row)
    ]
    agenda_feedback_rows = [
        row for row in agenda_rows if _is_runtime_handoff_artifact_missing_agenda_row(row)
    ]
    n_learning_rows = max(
        _safe_int(manifest.get("n_runtime_handoff_artifact_feedback_learning_rows", 0)),
        len(learning_feedback_rows),
    )
    n_agenda_rows = max(
        _safe_int(
            manifest.get("n_runtime_handoff_artifact_feedback_next_action_rows", 0)
        ),
        len(agenda_feedback_rows),
    )
    feedback_rows = [*learning_feedback_rows, *agenda_feedback_rows]
    return {
        "n_runtime_handoff_artifact_missing_feedback_rows": max(
            n_learning_rows,
            n_agenda_rows,
        ),
        "n_runtime_handoff_artifact_missing_learning_rows": n_learning_rows,
        "n_runtime_handoff_artifact_missing_agenda_rows": n_agenda_rows,
        "runtime_handoff_artifact_missing_ids": _sorted_row_values(
            feedback_rows,
            "missing_artifact_id",
        ),
        "runtime_handoff_artifact_missing_roles": _sorted_row_values(
            feedback_rows,
            "missing_artifact_role",
        ),
        "runtime_handoff_artifact_missing_owner_subsystems": _sorted_row_values(
            feedback_rows,
            "next_owner_subsystem",
            "owner_subsystem",
            "repair_owner_agent",
        ),
        "runtime_handoff_artifact_missing_boundary": (
            "missing handoff artifact feedback is orchestration evidence only; "
            "readiness requires the producing subsystem to rehydrate the requested "
            "artifact before a downstream agent can claim an end-to-end handoff"
        ),
    }


def _is_runtime_handoff_artifact_missing_learning_row(row: Any) -> bool:
    if not isinstance(row, Mapping):
        return False
    if str(row.get("learning_task", "") or "") == (
        "runtime_handoff_artifact_missing_feedback"
    ):
        return True
    input_summary = row.get("input_summary", {})
    if isinstance(input_summary, Mapping):
        return str(input_summary.get("trigger", "") or "") == (
            "RUNTIME_HANDOFF_ARTIFACT_MISSING"
        )
    return False


def _is_runtime_handoff_artifact_missing_agenda_row(row: Any) -> bool:
    if not isinstance(row, Mapping):
        return False
    if str(row.get("trigger", "") or "") == "RUNTIME_HANDOFF_ARTIFACT_MISSING":
        return True
    for key in ("work_order_id", "agenda_item_id", "id"):
        value = str(row.get(key, "") or "")
        if value.startswith("runtime_handoff_missing:"):
            return True
    return False


def _sorted_row_values(rows: list[Any], *keys: str) -> list[str]:
    values: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        for key in keys:
            value = str(row.get(key, "") or "").strip()
            if value:
                values.add(value)
    return sorted(values)


def _runtime_target_identity_audit_summary(
    *,
    agenda_rows: list[Any],
    pending_memory_rows: list[Any] | None = None,
    learning_rows: list[Any] | None = None,
) -> dict[str, Any]:
    missing_rows: list[dict[str, str]] = []
    route_critical_rows = 0
    channels: set[str] = set()
    row_sources: list[tuple[str, list[Any]]] = []
    if pending_memory_rows is not None:
        row_sources.append(("runtime_pending_task_memory", pending_memory_rows))
    else:
        row_sources.append(("runtime_learning_rows", learning_rows or []))
    row_sources.append(("runtime_next_action_agenda", agenda_rows))
    for channel, rows in row_sources:
        for index, row in enumerate(rows):
            if not _runtime_route_row_requires_target_identity(row):
                continue
            if (
                channel in {"runtime_learning_rows", "runtime_pending_task_memory"}
                and not _runtime_route_row_has_target_identity_hint(row)
            ):
                continue
            route_critical_rows += 1
            channels.add(channel)
            if _runtime_route_row_has_top_level_target_ids(row):
                continue
            missing_rows.append(
                {
                    "channel": channel,
                    "index": str(index),
                    "row_id": _runtime_route_row_identifier(row),
                    "learning_task": _runtime_route_row_field(row, "learning_task"),
                    "trigger": _runtime_route_row_trigger_value(row),
                    "owner_subsystem": _runtime_route_row_field(
                        row,
                        "owner_subsystem",
                        "next_owner_subsystem",
                    ),
                    "target_hint": _runtime_route_row_target_hint(row),
                }
            )
    return {
        "n_runtime_route_critical_target_identity_rows": route_critical_rows,
        "n_runtime_route_critical_rows_missing_target_ids": len(missing_rows),
        "runtime_route_critical_rows_missing_target_ids": missing_rows[:25],
        "runtime_route_critical_target_identity_channels": sorted(channels),
        "runtime_route_critical_target_identity_boundary": (
            "route-critical proof/formal agenda and learning rows must carry "
            "top-level target_ids before they are reused as AgentRuntime memory "
            "or handoff instructions; targetless rows are orchestration context "
            "only and cannot justify source-theorem proof progress"
        ),
    }


def _runtime_source_to_bridge_feedback_contract_audit_summary(
    *,
    pending_task_payload: Mapping[str, Any] | None = None,
    pending_memory_rows: list[Any] | None = None,
    learning_rows: list[Any] | None = None,
) -> dict[str, Any]:
    missing_rows: list[dict[str, Any]] = []
    contract_rows = 0
    channels: set[str] = set()
    row_sources: list[tuple[str, list[Any]]] = []
    if isinstance(pending_task_payload, Mapping) and pending_task_payload:
        row_sources.extend(
            _runtime_pending_task_source_to_bridge_feedback_row_sources(
                pending_task_payload
            )
        )
    if pending_memory_rows is not None:
        row_sources.append(("runtime_pending_task_memory", pending_memory_rows))
    else:
        row_sources.append(("runtime_learning_rows", learning_rows or []))
    for channel, rows in row_sources:
        for index, row in enumerate(rows):
            if not _runtime_source_to_bridge_feedback_row_requires_declaration(row):
                continue
            contract_rows += 1
            channels.add(channel)
            missing_fields = _runtime_source_to_bridge_feedback_missing_contract_fields(
                row
            )
            if not missing_fields:
                continue
            missing_rows.append(
                {
                    "channel": channel,
                    "index": str(index),
                    "row_id": _runtime_route_row_identifier(row),
                    "learning_task": _runtime_route_row_field(row, "learning_task"),
                    "trigger": _runtime_route_row_trigger_value(row),
                    "failure_classification": _runtime_route_row_field(
                        row,
                        "failure_classification",
                    ),
                    "premise_name": _runtime_route_row_field(row, "premise_name"),
                    "target_theorem_name": _runtime_route_row_field(
                        row,
                        "target_theorem_name",
                        "target_lean_declaration",
                    ),
                    "missing_fields": missing_fields,
                }
            )
    return {
        "n_runtime_source_to_bridge_feedback_contract_rows": contract_rows,
        "n_runtime_source_to_bridge_feedback_rows_missing_declaration_contract": len(
            missing_rows
        ),
        "runtime_source_to_bridge_feedback_rows_missing_declaration_contract": (
            missing_rows[:25]
        ),
        "runtime_source_to_bridge_feedback_contract_channels": sorted(channels),
        "runtime_source_to_bridge_feedback_contract_boundary": (
            "source-to-bridge premise derivation feedback and metadata-authoring "
            "requests that re-enter prompt memory must carry exact "
            "premise_candidate_declaration_name contracts at the diagnostic/request "
            "boundary. These contracts identify the Lean declaration to author or "
            "repair; they are routing metadata, not proof evidence."
        ),
    }


def _runtime_pending_task_source_to_bridge_feedback_row_sources(
    payload: Mapping[str, Any],
) -> list[tuple[str, list[Any]]]:
    pending_task = (
        payload.get("pending_next_task", {})
        if isinstance(payload.get("pending_next_task", {}), Mapping)
        else {}
    )
    inputs = (
        pending_task.get("inputs", {})
        if isinstance(pending_task.get("inputs", {}), Mapping)
        else {}
    )
    architect_context = (
        inputs.get("architect_context", {})
        if isinstance(inputs.get("architect_context", {}), Mapping)
        else {}
    )
    row_sources: list[tuple[str, list[Any]]] = []
    for channel, feedback in (
        ("runtime_pending_task_environment_feedback", inputs.get("environment_feedback")),
        (
            "runtime_pending_task_architect_context_environment_feedback",
            architect_context.get("environment_feedback"),
        ),
    ):
        if not isinstance(feedback, Mapping):
            continue
        rows = _runtime_environment_feedback_source_to_bridge_contract_rows(feedback)
        if rows:
            row_sources.append((channel, rows))
    return row_sources


def _runtime_environment_feedback_source_to_bridge_contract_rows(
    feedback: Mapping[str, Any],
) -> list[Any]:
    rows: list[Any] = []
    premise_feedback = feedback.get("source_to_bridge_premise_derivation_feedback", {})
    if isinstance(premise_feedback, Mapping):
        diagnostics = premise_feedback.get("diagnostics", [])
        if isinstance(diagnostics, list):
            rows.extend(row for row in diagnostics if isinstance(row, Mapping))
    top_level_diagnostics = feedback.get(
        "source_to_bridge_premise_derivation_diagnostics",
        [],
    )
    if isinstance(top_level_diagnostics, list):
        rows.extend(row for row in top_level_diagnostics if isinstance(row, Mapping))
    return rows


def _runtime_source_to_bridge_feedback_row_requires_declaration(row: Any) -> bool:
    if not isinstance(row, Mapping):
        return False
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    learning_task = str(
        row.get("learning_task", "") or input_summary.get("learning_task", "") or ""
    ).strip()
    if learning_task == "generated_next_action_routing":
        return False
    request = (
        row.get("source_to_bridge_premise_derivation_candidate_request", {})
        if isinstance(
            row.get("source_to_bridge_premise_derivation_candidate_request", {}),
            Mapping,
        )
        else {}
    )
    input_request = (
        input_summary.get("source_to_bridge_premise_derivation_candidate_request", {})
        if isinstance(
            input_summary.get("source_to_bridge_premise_derivation_candidate_request", {}),
            Mapping,
        )
        else {}
    )
    text = " ".join(
        str(source.get(key, "") or "")
        for source in (row, input_summary)
        for key in (
            "learning_task",
            "trigger",
            "failure_classification",
            "runtime_queue_status",
            "proof_evidence_status",
            "metadata_authoring_status",
        )
    ).lower()
    has_source_to_bridge_marker = (
        "source_to_bridge" in text
        or "source-to-bridge" in text
        or bool(request)
        or bool(input_request)
    )
    if not has_source_to_bridge_marker:
        return False
    premise = (
        _runtime_source_to_bridge_contract_text(row, input_summary, request, input_request, "premise_name")
        or _runtime_source_to_bridge_contract_text(
            row,
            input_summary,
            request,
            input_request,
            "source_to_bridge_premise_name",
        )
    )
    target = (
        _runtime_source_to_bridge_contract_text(
            row,
            input_summary,
            request,
            input_request,
            "target_theorem_name",
        )
        or _runtime_source_to_bridge_contract_text(
            row,
            input_summary,
            request,
            input_request,
            "target_lean_declaration",
        )
    )
    return bool(premise and target)


def _runtime_source_to_bridge_feedback_missing_contract_fields(
    row: Any,
) -> list[str]:
    if not isinstance(row, Mapping):
        return ["row_not_object"]
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    request = (
        row.get("source_to_bridge_premise_derivation_candidate_request", {})
        if isinstance(
            row.get("source_to_bridge_premise_derivation_candidate_request", {}),
            Mapping,
        )
        else {}
    )
    input_request = (
        input_summary.get("source_to_bridge_premise_derivation_candidate_request", {})
        if isinstance(
            input_summary.get("source_to_bridge_premise_derivation_candidate_request", {}),
            Mapping,
        )
        else {}
    )
    missing: list[str] = []
    declaration = (
        _runtime_source_to_bridge_contract_text(
            row,
            input_summary,
            request,
            input_request,
            "premise_candidate_declaration_name",
        )
        or _runtime_source_to_bridge_contract_text(
            row,
            input_summary,
            request,
            input_request,
            "source_to_bridge_premise_candidate_declaration_name",
        )
    )
    if not declaration:
        missing.append("premise_candidate_declaration_name")
    if request:
        request_declaration = _runtime_source_to_bridge_contract_text(
            request,
            {},
            input_request,
            {},
            "premise_candidate_declaration_name",
        ) or _runtime_source_to_bridge_contract_text(
            request,
            {},
            input_request,
            {},
            "source_to_bridge_premise_candidate_declaration_name",
        )
        if not request_declaration:
            missing.append(
                "source_to_bridge_premise_derivation_candidate_request.premise_candidate_declaration_name"
            )
    return missing


def _runtime_source_to_bridge_contract_text(
    row: Mapping[str, Any],
    input_summary: Mapping[str, Any],
    request: Mapping[str, Any],
    input_request: Mapping[str, Any],
    key: str,
) -> str:
    return str(
        row.get(key, "")
        or request.get(key, "")
        or input_summary.get(key, "")
        or input_request.get(key, "")
        or ""
    ).strip()


def _runtime_pending_task_memory_rows(payload: Mapping[str, Any]) -> list[Any]:
    pending_task = (
        payload.get("pending_next_task", {})
        if isinstance(payload.get("pending_next_task", {}), Mapping)
        else {}
    )
    inputs = (
        pending_task.get("inputs", {})
        if isinstance(pending_task.get("inputs", {}), Mapping)
        else {}
    )
    context = (
        inputs.get("architect_context", {})
        if isinstance(inputs.get("architect_context", {}), Mapping)
        else {}
    )
    memory = (
        context.get("runtime_learning_memory", {})
        if isinstance(context.get("runtime_learning_memory", {}), Mapping)
        else {}
    )
    rows = memory.get("rows", [])
    return list(rows) if isinstance(rows, list) else []


def _runtime_route_row_requires_target_identity(row: Any) -> bool:
    if not isinstance(row, Mapping):
        return False
    text = " ".join(
        str(value)
        for value in (
            row.get("learning_task", ""),
            row.get("trigger", ""),
            row.get("id", ""),
            row.get("agenda_item_id", ""),
            row.get("work_order_id", ""),
            row.get("gap_id", ""),
            row.get("route_reason", ""),
            row.get("target_behavior", ""),
            row.get("acceptance_gate", ""),
            row.get("runtime_queue_status", ""),
            row.get("proof_evidence_status", ""),
            row.get("owner_subsystem", ""),
            row.get("next_owner_subsystem", ""),
        )
        if str(value).strip()
    ).lower()
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    text += " " + " ".join(
        str(input_summary.get(key, ""))
        for key in (
            "trigger",
            "learning_task",
            "runtime_queue_status",
            "proof_evidence_status",
            "target_behavior",
            "acceptance_gate",
        )
        if str(input_summary.get(key, "")).strip()
    ).lower()
    target_identity_markers = (
        "source_theorem",
        "source-to-bridge",
        "source_to_bridge",
        "formalizer",
        "formalization",
        "formal_gap",
        "proof_body",
        "proof-bank",
        "proof_bank",
        "semantic_definition",
        "semantic-definition",
        "semantic_primitive",
        "semantic-primitive",
        "theorem_reduction",
        "lean_candidate",
        "lean-candidate",
        "proof_feedback",
    )
    if any(marker in text for marker in target_identity_markers):
        return True
    for key in (
        "target_theorem_name",
        "target_lean_declaration",
        "source_theorem_goal_id",
        "source_theorem_target_provenance",
        "target_theorem_goal_ids",
        "candidate_definition_request",
        "source_to_bridge_premise_derivation_candidate_request",
        "placeholder_symbol",
        "premise_name",
        "proof_body_gate_status",
    ):
        value = row.get(key)
        if value not in (None, "", [], {}):
            return True
    return False


def _runtime_route_row_has_top_level_target_ids(row: Any) -> bool:
    if not isinstance(row, Mapping):
        return False
    return any(str(value).strip() for value in row.get("target_ids", []) or [])


def _runtime_route_row_has_target_identity_hint(row: Any) -> bool:
    if not isinstance(row, Mapping):
        return False
    learning_task = str(row.get("learning_task", "") or "").strip()
    formalizer_candidate_feedback = learning_task in {
        "formalizer_lean_candidate_kernel_feedback",
        "formalizer_lean_candidate_proof_state_feedback",
    }
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    provenance = (
        row.get("source_theorem_target_provenance", {})
        if isinstance(row.get("source_theorem_target_provenance", {}), Mapping)
        else {}
    )
    if formalizer_candidate_feedback:
        for source in (row, input_summary, provenance):
            for key in ("target_theorem_goal_ids", "target_ids"):
                if any(str(value).strip() for value in source.get(key, []) or []):
                    return True
            for key in ("source_theorem_goal_id", "target_id", "target_theorem_name"):
                if str(source.get(key, "") or "").strip():
                    return True
        return bool(row.get("source_theorem_target_known")) and bool(
            str(row.get("target_lean_declaration", "") or "").strip()
        )
    for source in (row, input_summary, provenance):
        for key in (
            "target_theorem_name",
            "target_lean_declaration",
            "source_theorem_goal_id",
            "target_id",
        ):
            if str(source.get(key, "") or "").strip():
                return True
        for key in ("target_theorem_goal_ids", "target_ids"):
            if any(str(value).strip() for value in source.get(key, []) or []):
                return True
    return False


def _runtime_route_row_identifier(row: Any) -> str:
    return _runtime_route_row_field(
        row,
        "runtime_learning_row_id",
        "learning_row_id",
        "agenda_item_id",
        "work_order_id",
        "id",
        "gap_id",
    )


def _runtime_route_row_field(row: Any, *keys: str) -> str:
    if not isinstance(row, Mapping):
        return ""
    for key in keys:
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _runtime_route_row_trigger_value(row: Any) -> str:
    trigger = _runtime_route_row_field(row, "trigger")
    if trigger:
        return trigger
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row, Mapping)
        and isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    return str(input_summary.get("trigger", "") or "").strip()


def _runtime_route_row_target_hint(row: Any) -> str:
    if not isinstance(row, Mapping):
        return ""
    values: list[str] = []
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    provenance = (
        row.get("source_theorem_target_provenance", {})
        if isinstance(row.get("source_theorem_target_provenance", {}), Mapping)
        else {}
    )
    for source in (row, input_summary, provenance):
        for key in (
            "target_theorem_name",
            "target_lean_declaration",
            "source_theorem_goal_id",
            "target_id",
        ):
            value = str(source.get(key, "") or "").strip()
            if value:
                values.append(f"{key}={value}")
        for key in ("target_theorem_goal_ids", "target_ids"):
            row_values = [
                str(value).strip()
                for value in source.get(key, []) or []
                if str(value).strip()
            ]
            if row_values:
                values.append(f"{key}={row_values}")
    return " ".join(dict.fromkeys(values))


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
    distinct_task_family_count = _payload_distinct_task_family_count(payload)
    cross_task_full_theorem_family_count = (
        _payload_cross_task_full_theorem_family_count(payload)
    )
    architect_orchestration_executed = _runtime_architect_orchestration_executed(
        payload
    )
    architect_orchestration_evidence = _runtime_architect_orchestration_evidence(
        payload
    )
    architect_orchestration_blocker = _runtime_architect_orchestration_blocker(
        payload
    )
    integrated_algorithm_repair_sequences = int(
        payload.get("n_generated_code_sandbox_failed_then_passed_repair_sequences", 0)
        or 0
    )
    integrated_algorithm_code_executed = int(
        payload.get("n_generated_code_sandbox_executed", 0) or 0
    )
    integrated_simulation_repair_sequences = int(
        payload.get(
            "n_generated_simulation_sandbox_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    integrated_simulation_code_executed = int(
        payload.get("n_generated_simulation_sandbox_executed", 0) or 0
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
    integrated_formalizer_candidate_checked = int(
        payload.get("n_formalizer_lean_candidate_local_lean_checked", 0) or 0
    )
    integrated_formalizer_proof_state_feedback_rows = int(
        payload.get("n_formalizer_lean_candidate_proof_state_feedback_rows", 0) or 0
    )
    integrated_formalizer_local_lean_tool_calls = int(
        payload.get("n_formalizer_lean_candidate_local_lean_tool_calls", 0) or 0
    )
    integrated_formalizer_lean_lsp_mcp_live_calls = int(
        payload.get("n_formalizer_lean_candidate_lean_lsp_mcp_live_calls", 0) or 0
    )
    integrated_llm_formalizer_proposals = int(
        payload.get("n_llm_formalizer_proof_engineer_proposals", 0) or 0
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
    generated_code_execution_ready = (
        (
            (
                integrated_algorithm_code_executed > 0
                or integrated_algorithm_repair_sequences > 0
            )
            and (
                integrated_simulation_code_executed > 0
                or integrated_simulation_repair_sequences > 0
            )
        )
        or attached_coding_repair_ready
    )
    generated_code_repair_ready = (
        (
            integrated_algorithm_repair_sequences > 0
            and integrated_simulation_repair_sequences > 0
        )
        or attached_coding_repair_ready
    )
    formalizer_local_check_ready = (
        integrated_llm_formalizer_proposals > 0
        and (
            integrated_formalizer_candidate_checked > 0
            or integrated_formalizer_repair_sequences > 0
        )
    ) or attached_formalizer_repair_ready
    proofengineer_feedback_repair_ready = (
        (
            integrated_formalizer_agentic_repair_ready
            and (
                integrated_formalizer_proof_state_feedback_rows > 0
                or integrated_formalizer_local_lean_tool_calls > 0
                or integrated_formalizer_lean_lsp_mcp_live_calls > 0
            )
        )
        or attached_formalizer_repair_ready
    )
    helper_kernel_evidence_ready = (
        int(payload.get("n_real_kernel_verified_subclaims", 0) or 0) > 0
        or int(payload.get("n_runtime_memory_kernel_verified_proof_obligation_ids", 0) or 0)
        > 0
        or int(
            payload.get(
                "n_runtime_memory_kernel_verified_theorem_reduction_closure_goal_ids",
                0,
            )
            or 0
        )
        > 0
        or int(
            payload.get(
                "n_runtime_memory_kernel_verified_source_theorem_semantic_primitive_ids",
                0,
            )
            or 0
        )
        > 0
        or int(
            payload.get("n_real_kernel_verified_source_theorem_semantic_primitive_subclaims", 0)
            or 0
        )
        > 0
        or int(payload.get("n_full_frontier_theorem_proved", 0) or 0) > 0
        or source_theorem_kernel_count > 0
    )
    source_theorem_kernel_ready = (
        (
            int(payload.get("n_full_frontier_theorem_proved", 0) or 0) > 0
            or source_theorem_kernel_count > 0
        )
        and int(payload.get("n_formal_gaps", 0) or 0) <= 0
    )
    cross_task_generalization_ready = (
        distinct_task_family_count >= 2
        and cross_task_full_theorem_family_count >= 2
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
            and architect_orchestration_executed,
            (
                f"{architect_orchestration_evidence} "
                "n_live_generator_agents_enabled="
                f"{payload.get('n_live_generator_agents_enabled')}"
            ),
            architect_orchestration_blocker
            or "live run did not complete under ArchitectCoordinator control",
        ),
        _ladder_level(
            3,
            "generated_algorithm_and_simulation_code_executed",
            generated_code_execution_ready,
            (
                "integrated_algorithm_code_executed="
                f"{integrated_algorithm_code_executed} "
                "integrated_simulation_code_executed="
                f"{integrated_simulation_code_executed} "
                "integrated_algorithm_repair_sequences="
                f"{integrated_algorithm_repair_sequences} "
                "integrated_simulation_repair_sequences="
                f"{integrated_simulation_repair_sequences} "
                "attached_coding_repair_ready="
                f"{attached_coding_repair_ready}"
            ),
            (
                "no live generated AlgorithmEngineer and SimulationEngineer "
                "code execution was observed; registered templates or static "
                "fixtures do not demonstrate coding-agent execution"
            ),
        ),
        _ladder_level(
            4,
            "generated_code_failed_then_passed_repair_observed",
            generated_code_repair_ready,
            (
                "integrated_algorithm_repair_sequences="
                f"{integrated_algorithm_repair_sequences} "
                "integrated_simulation_repair_sequences="
                f"{integrated_simulation_repair_sequences} "
                "attached_coding_repair_ready="
                f"{attached_coding_repair_ready}"
            ),
            (
                "no generated algorithm and simulation failure diagnostics were "
                "followed by passing LLM-authored repairs"
            ),
        ),
        _ladder_level(
            5,
            "formalizer_candidate_local_lean_checked",
            formalizer_local_check_ready,
            (
                "integrated_llm_formalizer_proposals="
                f"{integrated_llm_formalizer_proposals} "
                "formalizer_candidate_checked="
                f"{integrated_formalizer_candidate_checked} "
                "integrated_formalizer_repair_sequences="
                f"{integrated_formalizer_repair_sequences} "
                "attached_formalizer_repair_ready="
                f"{attached_formalizer_repair_ready}"
            ),
            (
                "no live Formalizer/ProofEngineer Lean candidate was "
                "materialized and checked by local Lean"
            ),
        ),
        _ladder_level(
            6,
            "proofengineer_verifier_trace_repair_observed",
            proofengineer_feedback_repair_ready,
            (
                "integrated_formalizer_repair_sequences="
                f"{integrated_formalizer_repair_sequences} "
                "proof_state_feedback_rows="
                f"{integrated_formalizer_proof_state_feedback_rows} "
                "local_lean_tool_calls="
                f"{integrated_formalizer_local_lean_tool_calls} "
                "lean_lsp_mcp_live_calls="
                f"{integrated_formalizer_lean_lsp_mcp_live_calls} "
                "attached_formalizer_repair_ready="
                f"{attached_formalizer_repair_ready}"
            ),
            (
                "no ProofEngineer repair loop consumed verifier/proof-state "
                "tool traces and produced a repaired Lean candidate"
            ),
        ),
        _ladder_level(
            7,
            "helper_or_bridge_subclaim_kernel_verified",
            helper_kernel_evidence_ready,
            (
                "runtime_real_kernel="
                f"{payload.get('n_real_kernel_verified_subclaims')} "
                "memory_kernel_proof_obligations="
                f"{payload.get('n_runtime_memory_kernel_verified_proof_obligation_ids')} "
                "memory_kernel_theorem_closure_goals="
                f"{payload.get('n_runtime_memory_kernel_verified_theorem_reduction_closure_goal_ids')} "
                "memory_semantic_primitives="
                f"{payload.get('n_runtime_memory_kernel_verified_source_theorem_semantic_primitive_ids')} "
                "runtime_semantic_primitives="
                f"{payload.get('n_real_kernel_verified_source_theorem_semantic_primitive_subclaims')} "
                "source_theorem_kernel="
                f"{source_theorem_kernel_count} "
            ),
            "no local Lean/AXLE kernel-verified helper or bridge subclaim was available",
        ),
        _ladder_level(
            8,
            "full_source_theorem_kernel_verified",
            source_theorem_kernel_ready,
            (
                f"n_full_frontier_theorem_proved={payload.get('n_full_frontier_theorem_proved')} "
                "proof_body_source_kernel="
                f"{source_theorem_kernel_count} "
                f"n_formal_gaps={payload.get('n_formal_gaps')}"
            ),
            "no full source/frontier theorem was kernel-verified with formal gaps closed",
        ),
        _ladder_level(
            9,
            "cross_task_generalization_demonstrated",
            cross_task_generalization_ready,
            (
                f"n_distinct_question_ids={payload.get('n_distinct_question_ids')} "
                "n_distinct_task_families="
                f"{payload.get('n_distinct_task_families')} "
                f"n_full_frontier_theorem_proved={payload.get('n_full_frontier_theorem_proved')} "
                "proved_question_ids="
                f"{payload.get('question_ids_with_full_frontier_theorem_proved')} "
                "proved_task_families="
                f"{payload.get('task_families_with_full_frontier_theorem_proved')}"
            ),
            (
                "no multi-family kernel-verified theorem generalization was "
                "demonstrated"
            ),
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
        "scale": "L0-L9",
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
            "kernel-verified theorem evidence; L8 is required before claiming a full "
            "source theorem proof, and L9 is required before claiming cross-task generalization."
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
    distinct_task_family_count = _payload_distinct_task_family_count(payload)
    cross_task_full_theorem_family_count = (
        _payload_cross_task_full_theorem_family_count(payload)
    )
    proof_body_goal_reached_count = (
        _payload_source_theorem_proof_body_goal_reached_count(payload)
    )
    proof_body_result_row_count = _payload_source_theorem_proof_body_result_row_count(
        payload
    )
    architect_orchestration_executed = _runtime_architect_orchestration_executed(
        payload
    )
    architect_orchestration_evidence = _runtime_architect_orchestration_evidence(
        payload
    )
    architect_orchestration_blocker = _runtime_architect_orchestration_blocker(
        payload
    )
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
    runtime_handoff_artifact_missing_feedback_rows = int(
        payload.get("n_runtime_handoff_artifact_missing_feedback_rows", 0) or 0
    )
    runtime_route_missing_target_ids_count = int(
        payload.get("n_runtime_route_critical_rows_missing_target_ids", 0) or 0
    )
    runtime_source_to_bridge_missing_declaration_contract_count = int(
        payload.get(
            "n_runtime_source_to_bridge_feedback_rows_missing_declaration_contract",
            0,
        )
        or 0
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
    exact_semantic_definition_authoring_tasks = int(
        payload.get(
            "n_source_theorem_exact_semantic_definition_authoring_tasks",
            0,
        )
        or 0
    )
    exact_semantic_definition_authoring_worker_required = bool(
        payload.get(
            "source_theorem_exact_semantic_definition_authoring_worker_required",
            False,
        )
        or exact_semantic_definition_authoring_tasks > 0
    )
    exact_semantic_definition_authoring_worker_ran = (
        payload.get(
            "source_theorem_exact_semantic_definition_authoring_worker_ran",
            False,
        )
        is True
    )
    exact_semantic_definition_authoring_worker_llm_attempted = int(
        payload.get(
            "source_theorem_exact_semantic_definition_authoring_worker_n_llm_attempted",
            0,
        )
        or 0
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
            architect_orchestration_executed,
            architect_orchestration_evidence,
            architect_orchestration_blocker,
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="ArchitectCoordinator",
                target_behavior=(
                    "Resume through Architect so the formal verification policy, "
                    "recommended research path, and evidence contract are "
                    "propagated into every downstream runtime artifact."
                ),
                success_metric=(
                    "runtime_research_path_control_propagated=true with zero "
                    "policy/path mismatches in runtime_research_path_execution_summary"
                ),
            ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="ArchitectCoordinator",
                target_behavior=(
                    "Resume the pending runtime through Architect and require a "
                    "problem_analysis packet before retrieval/theory execution."
                ),
                success_metric=(
                    "n_results_with_problem_analysis equals n_results in the "
                    "capability audit"
                ),
            ),
        ),
        _scorecard_row(
            "dynamic_stat_knowledge_bank_planned",
            int(payload.get("n_results_with_stat_knowledge_bank_plan", 0) or 0) >= n_results,
            f"stat_knowledge_bank={payload.get('n_results_with_stat_knowledge_bank_plan')}/{n_results}",
            "dynamic StatKnowledgeBank planning was missing for at least one result",
            **_runtime_resume_scorecard_routing(
                payload,
                owner="ArchitectCoordinator",
                target_behavior=(
                    "Resume through Architect with a dynamic StatKnowledgeBank "
                    "plan that selects statistical concepts and retrieval targets "
                    "from the question instead of static templates."
                ),
                success_metric=(
                    "n_results_with_stat_knowledge_bank_plan equals n_results"
                ),
            ),
        ),
        _scorecard_row(
            "literature_fair_comparison_planned",
            int(payload.get("n_results_with_literature_fair_comparison_plan", 0) or 0) >= n_results,
            f"literature_fair_comparison={payload.get('n_results_with_literature_fair_comparison_plan')}/{n_results}",
            "literature fair-comparison planning was missing for at least one result",
            **_runtime_resume_scorecard_routing(
                payload,
                owner="ArchitectCoordinator",
                target_behavior=(
                    "Resume through Architect with a literature fair-comparison "
                    "plan that names baseline methods, theorem claims, and "
                    "evaluation criteria before theory development."
                ),
                success_metric=(
                    "n_results_with_literature_fair_comparison_plan equals n_results"
                ),
            ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="TheoryDeveloper",
                target_behavior=(
                    "Resume the pending task and require a TheoryDerivationPacket "
                    "with stable anchors, equation_chain, assumption_ledger, and "
                    "formalization_handoff consumed by code and proof agents."
                ),
                success_metric=(
                    "structured_theory_derivation_trace_observed=true with "
                    "equation-chain, assumption-ledger, and formalization handoff "
                    "counts all positive"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="AgentRuntimeOrchestrator",
                target_behavior=(
                    "Route the structured TheoryDerivationPacket into "
                    "AlgorithmEngineer, SimulationEvaluator, and "
                    "FormalizationEvaluator tasks without losing equation or "
                    "assumption anchors."
                ),
                success_metric=(
                    "all_required_theory_trace_consumers_observed=true and each "
                    "required consumer records a theory-trace consumption contract"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="AgentRuntimeOrchestrator",
                target_behavior=(
                    "Require downstream generated artifacts to cite supported "
                    "theory derivation anchors and reject unsupported anchor "
                    "references before evaluation passes."
                ),
                success_metric=(
                    "all_required_theory_trace_alignment_consumers_observed=true "
                    "and n_theory_trace_alignment_contracts_with_unsupported_anchors=0"
                ),
            ),
        ),
        _scorecard_row(
            "route_critical_target_ids_complete",
            runtime_route_missing_target_ids_count <= 0,
            (
                "route_critical_rows="
                f"{payload.get('n_runtime_route_critical_target_identity_rows')} "
                "missing_target_ids="
                f"{payload.get('n_runtime_route_critical_rows_missing_target_ids')} "
                "channels="
                f"{payload.get('runtime_route_critical_target_identity_channels')} "
                "sample_missing="
                f"{payload.get('runtime_route_critical_rows_missing_target_ids')}"
            ),
            (
                "route-critical proof/formal agenda or learning rows lacked "
                "top-level target_ids; preserve source-theorem target identity "
                "before reusing runtime memory or handoff instructions"
            ),
        ),
        _scorecard_row(
            "source_to_bridge_feedback_declaration_contracts_complete",
            runtime_source_to_bridge_missing_declaration_contract_count <= 0,
            (
                "contract_rows="
                f"{payload.get('n_runtime_source_to_bridge_feedback_contract_rows')} "
                "missing_declaration_contracts="
                f"{payload.get('n_runtime_source_to_bridge_feedback_rows_missing_declaration_contract')} "
                "channels="
                f"{payload.get('runtime_source_to_bridge_feedback_contract_channels')} "
                "missing="
                f"{payload.get('runtime_source_to_bridge_feedback_rows_missing_declaration_contract')}"
            ),
            (
                "source-to-bridge premise derivation feedback or metadata-authoring "
                "requests are being reused without exact "
                "premise_candidate_declaration_name contracts; downstream "
                "Formalizer/ProofEngineer turns must not guess the Lean declaration "
                "name from stale or null request metadata"
            ),
        ),
        _scorecard_row(
            "explicit_handoff_artifacts_available",
            runtime_handoff_artifact_missing_feedback_rows <= 0,
            (
                "missing_handoff_feedback_rows="
                f"{payload.get('n_runtime_handoff_artifact_missing_feedback_rows')} "
                "learning_rows="
                f"{payload.get('n_runtime_handoff_artifact_missing_learning_rows')} "
                "agenda_rows="
                f"{payload.get('n_runtime_handoff_artifact_missing_agenda_rows')} "
                "missing_artifact_ids="
                f"{payload.get('runtime_handoff_artifact_missing_ids')} "
                "missing_roles="
                f"{payload.get('runtime_handoff_artifact_missing_roles')} "
                "owner_subsystems="
                f"{payload.get('runtime_handoff_artifact_missing_owner_subsystems')}"
            ),
            (
                "explicit subsystem handoff artifact ids were missing from the "
                "blackboard; rerun or rehydrate the producing subsystem before "
                "claiming an end-to-end AgentRuntime handoff"
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
                f"{payload.get('n_generated_code_sandbox_executed')} "
                "attached_live_component_repair_gate_passed="
                f"{attached_live_component_repair_gate_passed} "
                "attached_algorithm_repair_sequences="
                f"{attached_repair_eval_algorithm_sequences}"
            ),
            (
                "no Claude/OpenAI-generated algorithm code executed locally; "
                "registered templates are baselines, and attached component "
                "repair gates do not substitute for integrated AlgorithmEngineer "
                "execution from runtime theory context"
            ),
            **_runtime_resume_scorecard_routing(
                payload,
                owner="AlgorithmEngineer",
                target_behavior=(
                    "Resume after theory derivation and route the structured "
                    "TheoryDerivationPacket into AlgorithmEngineer so it generates "
                    "Python algorithm code and executes it in the local sandbox."
                ),
                success_metric=(
                    "n_generated_code_sandbox_executed>0 for an integrated "
                    "runtime AlgorithmEngineer artifact"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="AlgorithmEngineer",
                target_behavior=(
                    "Feed sandbox rejection diagnostics back to AlgorithmEngineer "
                    "and require a revised generated-code draft that passes the "
                    "local sandbox guard."
                ),
                success_metric=(
                    "n_unsafe_generated_code_rejected is zero or "
                    "n_generated_code_sandbox_failed_then_passed_repair_sequences>0"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="AlgorithmEngineer",
                target_behavior=(
                    "Feed statistical metric-gate diagnostics back to "
                    "AlgorithmEngineer and require a revised generated algorithm "
                    "that passes the metric gate."
                ),
                success_metric=(
                    "n_generated_code_sandbox_metric_gate_failed is zero or "
                    "n_generated_code_sandbox_failed_then_passed_repair_sequences>0"
                ),
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
                "generated draft passing local sandbox/metric gates; attached "
                "component gates can show isolated coding-agent capacity, but "
                "one-shot integrated execution is not evidence of autonomous "
                "runtime coding repair"
            ),
            **_runtime_resume_scorecard_routing(
                payload,
                owner="AlgorithmEngineer",
                target_behavior=(
                    "Run an integrated fail-then-pass generated algorithm repair "
                    "sequence using sandbox or metric-gate feedback from the same "
                    "runtime question."
                ),
                success_metric=(
                    "n_generated_code_sandbox_failed_then_passed_repair_sequences>0"
                ),
            ),
        ),
        _scorecard_row(
            "generated_simulation_code_executed",
            int(payload.get("n_generated_simulation_sandbox_executed", 0) or 0)
            > 0,
            (
                "n_generated_simulation_sandbox_executed="
                f"{payload.get('n_generated_simulation_sandbox_executed')} "
                "attached_live_component_repair_gate_passed="
                f"{attached_live_component_repair_gate_passed} "
                "attached_simulation_repair_sequences="
                f"{attached_repair_eval_simulation_sequences}"
            ),
            (
                "no Claude/OpenAI-generated simulation stress-test code executed "
                "locally; registered simulator rows and attached component gates "
                "do not substitute for integrated SimulationEvaluator execution "
                "from runtime theory context"
            ),
            **_runtime_resume_scorecard_routing(
                payload,
                owner="SimulationEvaluator",
                target_behavior=(
                    "Resume after theory/algorithm handoff and require "
                    "SimulationEvaluator to generate stress-test Python code that "
                    "runs in the local sandbox."
                ),
                success_metric=(
                    "n_generated_simulation_sandbox_executed>0 for an integrated "
                    "runtime SimulationEvaluator artifact"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="SimulationEvaluator",
                target_behavior=(
                    "Feed sandbox rejection diagnostics back to SimulationEvaluator "
                    "and require a revised generated simulation that passes the "
                    "local sandbox guard."
                ),
                success_metric=(
                    "n_unsafe_generated_simulation_code_rejected is zero or "
                    "n_generated_simulation_sandbox_failed_then_passed_repair_sequences>0"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="SimulationEvaluator",
                target_behavior=(
                    "Feed empirical metric-gate diagnostics back to "
                    "SimulationEvaluator and require a revised generated stress "
                    "test that passes the configured metric gate."
                ),
                success_metric=(
                    "n_generated_simulation_sandbox_metric_gate_failed is zero or "
                    "n_generated_simulation_sandbox_failed_then_passed_repair_sequences>0"
                ),
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
                "simulation rows, attached component gates, or one-shot execution "
                "do not demonstrate integrated simulation coding-agent repair"
            ),
            **_runtime_resume_scorecard_routing(
                payload,
                owner="SimulationEvaluator",
                target_behavior=(
                    "Run an integrated fail-then-pass generated simulation repair "
                    "sequence using sandbox or metric-gate feedback from the same "
                    "runtime question."
                ),
                success_metric=(
                    "n_generated_simulation_sandbox_failed_then_passed_repair_sequences>0"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="FormalizationEvaluator",
                target_behavior=(
                    "Resume with a live Formalizer/ProofEngineer proposal that "
                    "uses the structured theory handoff to generate a Lean theorem "
                    "statement or proof candidate."
                ),
                success_metric=(
                    "n_llm_formalizer_proof_engineer_proposals>0 or a live "
                    "attached formalizer repair gate passes"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="FormalizationEvaluator",
                target_behavior=(
                    "Generate a Lean candidate from the theory handoff and run a "
                    "local Lean diagnostic check before emitting proof feedback."
                ),
                success_metric=(
                    "n_llm_formalizer_proof_engineer_proposals>0 and "
                    "n_formalizer_lean_candidate_local_lean_checked>0, or the "
                    "attached live formalizer repair gate checks local Lean"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="FormalizationEvaluator",
                target_behavior=(
                    "Convert local Lean candidate failures into Lean-LSP/MCP-ready "
                    "proof-state requests for the ProofEngineer repair loop."
                ),
                success_metric=(
                    "n_formalizer_lean_candidate_live_proof_state_requests>0 and "
                    "n_formalizer_lean_candidate_lean_lsp_mcp_ready_requests>0"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="FormalizationEvaluator",
                target_behavior=(
                    "Record structured proof-state feedback rows with Lean "
                    "diagnostics, residual goals, and target ids for the next "
                    "Formalizer/ProofEngineer repair turn."
                ),
                success_metric=(
                    "n_formalizer_lean_candidate_proof_state_feedback_rows>0"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="FormalizationEvaluator",
                target_behavior=(
                    "Attach actual local Lean tool-call traces to ProofEngineer "
                    "feedback so later LLM repair turns see executable diagnostics."
                ),
                success_metric=(
                    "n_formalizer_lean_candidate_local_lean_tool_calls>0"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="FormalizationEvaluator",
                target_behavior=(
                    "Drive a live Lean proof-state/prover tool call from the "
                    "ProofEngineer feedback request rather than stopping at a "
                    "queued request row."
                ),
                success_metric=(
                    "n_formalizer_lean_candidate_lean_lsp_mcp_live_calls>0"
                ),
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
            **_runtime_resume_scorecard_routing(
                payload,
                owner="FormalizationEvaluator",
                target_behavior=(
                    "Run a fail-then-pass generated Lean candidate repair loop "
                    "with local Lean diagnostics, either integrated in the runtime "
                    "or through the attached live formalizer repair gate."
                ),
                success_metric=(
                    "n_formalizer_lean_candidate_failed_then_passed_repair_sequences>0 "
                    "with live LLM proposals, or attached live formalizer repair "
                    "gate evidence passes"
                ),
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
            proof_body_goal_reached_count > 0,
            (
                "proof_body_goal_reached_evidence="
                f"{proof_body_goal_reached_count} "
                "proof_body_result_rows="
                f"{proof_body_result_row_count} "
                "signature_probe_reached="
                f"{payload.get('source_theorem_formal_environment_proofengineer_n_signature_probes_reached_proof_body')}"
            ),
            (
                "exact source-theorem proof-body goal was not reached; result "
                "rows without goal evidence are pre-proof-body blockers, not "
                "proof-body repair evidence"
            ),
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
            "exact_semantic_definition_authoring_worker_handoff_not_dropped",
            (not exact_semantic_definition_authoring_worker_required)
            or exact_semantic_definition_authoring_worker_ran,
            (
                "authoring_tasks="
                f"{payload.get('n_source_theorem_exact_semantic_definition_authoring_tasks')} "
                "required="
                f"{payload.get('source_theorem_exact_semantic_definition_authoring_worker_required')} "
                "requested="
                f"{payload.get('source_theorem_exact_semantic_definition_authoring_worker_requested')} "
                "ran="
                f"{payload.get('source_theorem_exact_semantic_definition_authoring_worker_ran')} "
                "prompt_packets="
                f"{payload.get('source_theorem_exact_semantic_definition_authoring_worker_n_prompt_packets')} "
                "skipped="
                f"{payload.get('source_theorem_exact_semantic_definition_authoring_worker_skipped_reason')}"
            ),
            (
                "exact semantic-definition Lean repair emitted authoring tasks "
                "but the LLM authoring worker did not run"
            ),
        ),
        _scorecard_row(
            "exact_semantic_definition_authoring_worker_live_attempted",
            (not exact_semantic_definition_authoring_worker_required)
            or exact_semantic_definition_authoring_worker_llm_attempted > 0,
            (
                "authoring_tasks="
                f"{payload.get('n_source_theorem_exact_semantic_definition_authoring_tasks')} "
                "ran="
                f"{payload.get('source_theorem_exact_semantic_definition_authoring_worker_ran')} "
                "dry_run="
                f"{payload.get('source_theorem_exact_semantic_definition_authoring_worker_dry_run')} "
                "external_export_mode="
                f"{payload.get('source_theorem_exact_semantic_definition_authoring_worker_external_export_mode')} "
                "llm_attempted="
                f"{payload.get('source_theorem_exact_semantic_definition_authoring_worker_n_llm_attempted')}"
            ),
            (
                "exact semantic-definition authoring tasks were only staged or "
                "blocked; no live LLM authoring attempt was recorded"
            ),
            **_runtime_resume_scorecard_routing(
                payload,
                owner="Formalizer/ProofEngineer",
                target_behavior=(
                    "Run the exact semantic-definition authoring worker with a "
                    "live provider and then route generated definition-only "
                    "candidates through materialization and local Lean/AXLE."
                ),
                success_metric=(
                    "source_theorem_exact_semantic_definition_authoring_worker_n_llm_attempted>0"
                ),
            ),
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
        _scorecard_row(
            "cross_task_full_theorem_generalization_demonstrated",
            distinct_task_family_count >= 2
            and cross_task_full_theorem_family_count >= 2,
            (
                "n_distinct_question_ids="
                f"{payload.get('n_distinct_question_ids')} "
                "question_ids="
                f"{payload.get('question_ids')} "
                "n_distinct_task_families="
                f"{payload.get('n_distinct_task_families')} "
                "task_families="
                f"{payload.get('task_families')} "
                "n_full_frontier_theorem_proved="
                f"{payload.get('n_full_frontier_theorem_proved')} "
                "n_question_ids_with_full_frontier_theorem_proved="
                f"{payload.get('n_question_ids_with_full_frontier_theorem_proved')} "
                "question_ids_with_full_frontier_theorem_proved="
                f"{payload.get('question_ids_with_full_frontier_theorem_proved')} "
                "n_task_families_with_full_frontier_theorem_proved="
                f"{payload.get('n_task_families_with_full_frontier_theorem_proved')} "
                "task_families_with_full_frontier_theorem_proved="
                f"{payload.get('task_families_with_full_frontier_theorem_proved')}"
            ),
            (
                "capability eval has not kernel-verified full source/frontier "
                "theorems across at least two distinct statistics task families; "
                "two question ids inside one family cannot establish general "
                "AI Statistician readiness"
            ),
            **_cross_task_generalization_scorecard_routing(payload),
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
    **routing: Any,
) -> dict[str, Any]:
    row = {
        "requirement_id": requirement_id,
        "passed": bool(passed),
        "evidence": evidence,
        "blocker": "" if passed else blocker,
    }
    if routing and not bool(passed):
        row.update(routing)
    return row


def _cross_task_generalization_scorecard_routing(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    families = explicit_task_family_list(payload.get("task_families", []))
    first_family = families[0] if families else "conformal"
    second_family = (
        "experimental_design"
        if first_family != "experimental_design"
        else "multiple_testing"
    )
    command = (
        ".venv/bin/python -m ai_statistician.cli research-agent-runtime "
        f"--question-task-family {first_family} "
        f"--question-task-family {second_family} "
        "--min-task-families 2 "
        "--provider anthropic "
        "--capability-eval "
        "--capability-eval-preset full-live "
        "--max-iterations 8 "
        "--out runs/main_worker_cross_family_full_live"
    )
    return {
        "next_owner_subsystem": "ArchitectCoordinator",
        "target_behavior": (
            "Run a live Architect-controlled capability eval over at least two "
            "explicit statistics task families, then prove full source/frontier "
            "theorems in each selected family before claiming L9 generality."
        ),
        "recommended_capability_eval_command": command,
        "success_metric": (
            "n_distinct_task_families>=2 and "
            "n_task_families_with_full_frontier_theorem_proved>=2 with "
            "local Lean/AXLE kernel verification for the full source/frontier "
            "theorem in each family"
        ),
        "proof_evidence_status": "CAPABILITY_SCORECARD_ROUTING_NOT_PROOF_EVIDENCE",
        "routing_boundary": (
            "This recommendation is evaluation routing metadata. It is not proof "
            "evidence and does not satisfy L9 until the audit records real "
            "kernel-verified full theorem evidence across the selected families."
        ),
    }


def _capability_resume_out_dir(payload: Mapping[str, Any]) -> str:
    runtime_dir = str(payload.get("runtime_dir", "") or "").strip()
    if not runtime_dir:
        return "runs/main_worker_runtime_resume_full_live"
    path = Path(runtime_dir)
    return str(path.with_name(f"{path.name}_resume_full_live"))


def _capability_resume_command(
    payload: Mapping[str, Any],
    *,
    max_iterations: int = 8,
) -> str:
    manifest_path = str(payload.get("manifest", "") or "").strip()
    manifest_arg = manifest_path if manifest_path else "<prior_runtime_manifest>"
    out_arg = _capability_resume_out_dir(payload)
    return (
        ".venv/bin/python -m ai_statistician.cli research-agent-runtime "
        f"--resume-runtime-manifest {shlex.quote(manifest_arg)} "
        "--provider anthropic "
        "--capability-eval "
        "--capability-eval-preset full-live "
        "--resume-through-architect "
        f"--max-iterations {max_iterations} "
        f"--out {shlex.quote(out_arg)}"
    )


def _runtime_resume_scorecard_routing(
    payload: Mapping[str, Any],
    *,
    owner: str,
    target_behavior: str,
    success_metric: str,
    max_iterations: int = 8,
) -> dict[str, Any]:
    return {
        "next_owner_subsystem": owner,
        "target_behavior": target_behavior,
        "recommended_capability_eval_command": _capability_resume_command(
            payload,
            max_iterations=max_iterations,
        ),
        "success_metric": success_metric,
        "proof_evidence_status": "CAPABILITY_SCORECARD_ROUTING_NOT_PROOF_EVIDENCE",
        "routing_boundary": (
            "This recommendation resumes an evaluation run and is not proof "
            "evidence. Capability is satisfied only after the resumed runtime "
            "records the requested live-agent artifacts and, where relevant, "
            "real Lean/AXLE kernel evidence in the audit."
        ),
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


def _runtime_exact_semantic_definition_authoring_task_rows(
    *,
    runtime_dir: Path,
    artifacts: Mapping[str, Any],
    errors: list[str],
) -> list[dict[str, Any]]:
    raw_manifest_path = str(
        artifacts.get(
            "runtime_source_theorem_exact_semantic_definition_lean_repair_executor_manifest",
            "",
        )
        or ""
    )
    if not raw_manifest_path.strip():
        return []
    executor_manifest_path = _resolve_path(runtime_dir, raw_manifest_path)
    if not executor_manifest_path.exists():
        errors.append(
            "missing exact semantic-definition Lean repair executor manifest: "
            f"{executor_manifest_path}"
        )
        return []
    executor_manifest = _load_json(executor_manifest_path, errors)
    raw_tasks_path = str(
        executor_manifest.get("exact_semantic_definition_authoring_tasks_jsonl", "")
        or ""
    )
    if not raw_tasks_path.strip():
        return []
    tasks_path = _resolve_path(executor_manifest_path.parent, raw_tasks_path)
    return _load_jsonl(tasks_path, errors, required=True)


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
        f"- runtime resumed from pending task: {payload.get('runtime_resumed_from_pending_task')}",
        f"- results: {payload.get('n_ok')}/{payload.get('n_results')}",
        f"- question ids: {payload.get('question_ids')}",
        f"- task families: {payload.get('task_families')}",
        "- rows task-family backfilled from manifest: "
        f"{payload.get('n_rows_task_family_backfilled_from_manifest')}",
        "- question ids with full frontier theorem proved: "
        f"{payload.get('question_ids_with_full_frontier_theorem_proved')}",
        "- task families with full frontier theorem proved: "
        f"{payload.get('task_families_with_full_frontier_theorem_proved')}",
        f"- result errors: {payload.get('n_result_errors')}",
        "- budgeted continuations contract-ok: "
        f"{payload.get('n_budgeted_continuation_contract_ok')}/"
        f"{payload.get('n_budget_exhausted_with_pending_next_task')}",
        f"- runtime progress events: {payload.get('n_runtime_progress_events')}",
        f"- runtime traces: {payload.get('n_runtime_traces')}",
        f"- agenda items: {payload.get('n_runtime_next_action_items')}",
        f"- learning rows: {payload.get('n_runtime_learning_rows')}",
        "",
        "## Capability Routing",
    ]
    routed_rows = [
        row
        for row in payload.get("capability_scorecard", {}).get("rows", []) or []
        if (
            isinstance(row, Mapping)
            and row.get("passed") is not True
            and str(row.get("recommended_capability_eval_command", "") or "").strip()
        )
    ]
    if routed_rows:
        for row in routed_rows:
            lines.extend(
                [
                    f"- {row.get('requirement_id')}: owner={row.get('next_owner_subsystem')}",
                    f"  - target: {row.get('target_behavior')}",
                    f"  - command: `{row.get('recommended_capability_eval_command')}`",
                    f"  - success: {row.get('success_metric')}",
                    f"  - boundary: {row.get('routing_boundary')}",
                ]
            )
    else:
        lines.append("- no scorecard routing recommendations")
    lines.extend([
        "",
        "## Runtime Handoff Identity",
        f"- pending task memory rows: {payload.get('n_runtime_pending_task_memory_rows')}",
        "- route-critical target identity rows / missing target_ids: "
        f"{payload.get('n_runtime_route_critical_target_identity_rows')} / "
        f"{payload.get('n_runtime_route_critical_rows_missing_target_ids')}",
        "- route-critical target identity channels: "
        f"{payload.get('runtime_route_critical_target_identity_channels')}",
        "- route-critical target identity missing sample: "
        f"{payload.get('runtime_route_critical_rows_missing_target_ids')}",
        "- source-to-bridge feedback declaration contracts / missing: "
        f"{payload.get('n_runtime_source_to_bridge_feedback_contract_rows')} / "
        f"{payload.get('n_runtime_source_to_bridge_feedback_rows_missing_declaration_contract')}",
        "- source-to-bridge feedback contract channels: "
        f"{payload.get('runtime_source_to_bridge_feedback_contract_channels')}",
        "- source-to-bridge feedback declaration missing sample: "
        f"{payload.get('runtime_source_to_bridge_feedback_rows_missing_declaration_contract')}",
        "- missing handoff artifact feedback rows / learning / agenda: "
        f"{payload.get('n_runtime_handoff_artifact_missing_feedback_rows')} / "
        f"{payload.get('n_runtime_handoff_artifact_missing_learning_rows')} / "
        f"{payload.get('n_runtime_handoff_artifact_missing_agenda_rows')}",
        "- missing handoff artifact ids / roles / owners: "
        f"{payload.get('runtime_handoff_artifact_missing_ids')} / "
        f"{payload.get('runtime_handoff_artifact_missing_roles')} / "
        f"{payload.get('runtime_handoff_artifact_missing_owner_subsystems')}",
        "",
    ])
    lines.extend([
        f"- live generator agents enabled: {payload.get('n_live_generator_agents_enabled')}",
        f"- ArchitectCoordinator trace executed: {payload.get('architect_coordinator_enabled')}",
        f"- Architect control status: {payload.get('runtime_architect_control_status')}",
        f"- Architect orchestration evidence: {payload.get('runtime_architect_orchestration_evidence')}",
        f"- Architect orchestration blocker: {payload.get('runtime_architect_orchestration_blocker')}",
        f"- LLM topology policy ok: {payload.get('llm_topology_policy_ok')}",
        f"- unsupported generator backends: {payload.get('unsupported_generator_backends_enabled')}",
        f"- critic reroutes: {payload.get('n_critic_reroutes')}",
        "- exact source proof-body goal-reached evidence count: "
        f"{payload.get('source_theorem_proof_body_goal_reached_evidence_count')}",
        "- exact source proof-body result row count: "
        f"{payload.get('source_theorem_proof_body_result_row_count')}",
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
    ])
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
            f"- {row.get('question_id')}: family={row.get('task_family')} "
            f"ok={row.get('ok')} traces={row.get('n_traces')} "
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

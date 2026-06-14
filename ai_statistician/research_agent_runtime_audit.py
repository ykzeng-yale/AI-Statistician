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
    n_algorithm_manifests: int
    n_algorithm_sandbox_executed: int
    n_generated_code_sandbox_executed: int
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
    payload: dict[str, Any] = {
        "schema_version": RESEARCH_AGENT_RUNTIME_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_dir": str(runtime_dir),
        "manifest": str(manifest_path),
        "runtime_stage": manifest.get("runtime_stage", ""),
        "runtime_evaluation_mode": str(manifest.get("runtime_evaluation_mode", "")),
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
        "n_generated_code_sandbox_executed": sum(
            row.n_generated_code_sandbox_executed for row in rows
        ),
        "n_unsafe_generated_code_rejected": sum(
            row.n_unsafe_generated_code_rejected for row in rows
        ),
        "n_lean_lsp_mcp_live_calls": sum(row.n_lean_lsp_mcp_live_calls for row in rows),
        "source_theorem_promotion_proofengineer_bridge_ran": bool(
            manifest.get("source_theorem_promotion_proofengineer_bridge_ran", False)
        ),
        "source_theorem_promotion_proofengineer_bridge_skipped_reason": str(
            manifest.get("source_theorem_promotion_proofengineer_bridge_skipped_reason", "")
            or ""
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
        "source_theorem_formal_environment_proof_body_executor_ran": bool(
            manifest.get("source_theorem_formal_environment_proof_body_executor_ran", False)
        )
        or bool(
            manifest.get(
                "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_ran",
                False,
            )
        ),
        "source_theorem_formal_environment_proof_body_executor_local_lean_requested": bool(
            manifest.get(
                "source_theorem_formal_environment_proof_body_executor_local_lean_requested",
                False,
            )
        ),
        "source_theorem_formal_environment_proof_body_executor_n_result_rows": (
            int(
                manifest.get(
                    "source_theorem_formal_environment_proof_body_executor_n_result_rows",
                    0,
                )
                or 0
            )
            + int(
                manifest.get(
                    "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_n_result_rows",
                    0,
                )
                or 0
            )
        ),
        "source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified": (
            int(
                manifest.get(
                    "source_theorem_formal_environment_proof_body_executor_n_source_theorem_kernel_verified",
                    0,
                )
                or 0
            )
            + int(
                manifest.get(
                    "source_theorem_formal_environment_proof_body_executor_from_source_semantic_promotion_n_source_theorem_kernel_verified",
                    0,
                )
                or 0
            )
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
    expected_sequence = REQUIRED_ARCHITECT_SUBSYSTEMS if architect_enabled else REQUIRED_SUBSYSTEMS
    if tuple(subsystem_sequence[: len(expected_sequence)]) != expected_sequence:
        errors.append("runtime trace subsystem order is incomplete or misordered")
    if data.get("status") != "ACCEPTED":
        errors.append("runtime result status is not ACCEPTED")

    retrieval = _artifacts_with_prefix(artifacts, "retrieval_memory_manifest:")
    theory = _artifacts_with_prefix(artifacts, "theory_derivation:")
    simulation = _artifacts_with_prefix(artifacts, "simulation_manifest:")
    algorithm = _artifacts_with_prefix(artifacts, "algorithm_sandbox_manifest:")
    formalization = _artifacts_with_prefix(artifacts, "formalization_manifest:")
    proof_state_feedback = _artifacts_with_prefix(artifacts, "proof_state_feedback_manifest:")
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
    n_generated_code_sandbox_executed = sum(
        int(row.get("n_generated_code_executed", 0) or 0)
        for row in algorithm
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
        n_algorithm_manifests=len(algorithm),
        n_algorithm_sandbox_executed=n_algorithm_sandbox_executed,
        n_generated_code_sandbox_executed=n_generated_code_sandbox_executed,
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
    return sorted(set(errors))


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
            "environment_algorithm_feedback_executed",
            int(payload.get("n_algorithm_sandbox_executed", 0) or 0) > 0,
            f"n_algorithm_sandbox_executed={payload.get('n_algorithm_sandbox_executed')}",
            "no executable algorithm sandbox feedback was produced",
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
            int(payload.get("n_full_frontier_theorem_proved", 0) or 0) > 0
            and int(payload.get("n_formal_gaps", 0) or 0) <= 0,
            (
                f"n_full_frontier_theorem_proved={payload.get('n_full_frontier_theorem_proved')} "
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
    return {
        "artifact_kind": "RuntimeCapabilityLadder",
        "scale": "L0-L8",
        "max_contiguous_level": max_contiguous,
        "max_evidence_level": max(passed_levels) if passed_levels else -1,
        "current_level_label": (
            levels[max_contiguous]["label"] if max_contiguous >= 0 else "no_runtime_contract"
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
            "algorithm_sandbox_executed",
            int(payload.get("n_algorithm_sandbox_executed", 0) or 0) > 0,
            f"n_algorithm_sandbox_executed={payload.get('n_algorithm_sandbox_executed')}",
            "no algorithm sandbox prototype executed",
        ),
        _scorecard_row(
            "generated_algorithm_sandbox_clean",
            int(payload.get("n_unsafe_generated_code_rejected", 0) or 0) <= 0,
            f"n_unsafe_generated_code_rejected={payload.get('n_unsafe_generated_code_rejected')}",
            "at least one generated algorithm draft was rejected by the sandbox guard",
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
            int(payload.get("n_full_frontier_theorem_proved", 0) or 0) > 0,
            f"n_full_frontier_theorem_proved={payload.get('n_full_frontier_theorem_proved')}",
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


def _artifacts_with_prefix(artifacts: Mapping[str, Any], prefix: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in artifacts.items():
        if str(key).startswith(prefix) and isinstance(value, Mapping):
            rows.append(dict(value))
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
        f"- capability ladder max evidence level: {payload.get('capability_ladder', {}).get('max_evidence_level')}",
        f"- capability ladder current label: {payload.get('capability_ladder', {}).get('current_level_label')}",
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
        f"- algorithm sandbox executed: {payload.get('n_algorithm_sandbox_executed')}",
        f"- generated-code sandbox executed: {payload.get('n_generated_code_sandbox_executed')}",
        f"- unsafe generated-code rejected: {payload.get('n_unsafe_generated_code_rejected')}",
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

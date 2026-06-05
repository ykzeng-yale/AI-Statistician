from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


RAG_COLLABORATION_EXPORT_SCHEMA_VERSION = 1


def export_rag_collaboration_manifest(
    system_audit_manifest: Path,
    out_dir: Path,
    *,
    max_targets: int = 20,
    artifact_overrides: dict[str, str | Path] | None = None,
) -> dict[str, object]:
    """Export a compact handoff for the shared RAG/prover-search thread.

    The research-system audit already writes many detailed manifests. This
    export collects the parts that matter to an external RAG infrastructure
    loop: which provider was active, which retrieval ablations moved, which
    formal primitives remain hard, and which proof-bank facts are genuinely
    kernel evidence. Retrieval hits remain premise suggestions, not proof
    evidence.
    """

    system_audit_manifest = system_audit_manifest.expanduser()
    system_payload = _read_json(system_audit_manifest)
    run_dir = system_audit_manifest.parent
    counts = dict(system_payload.get("counts", {}) or {})
    artifacts = dict(system_payload.get("artifacts", {}) or {})
    normalized_artifact_overrides = {
        str(key): str(value)
        for key, value in dict(artifact_overrides or {}).items()
        if str(key) and str(value)
    }
    artifacts.update(normalized_artifact_overrides)
    artifact_auto_discoveries = _auto_discover_artifacts(
        artifacts,
        run_dir,
        protected_keys=set(normalized_artifact_overrides),
    )
    artifacts.update(artifact_auto_discoveries)

    proof_payload = _read_json(_artifact_path(artifacts, "proof_audit", run_dir))
    proof_search_kernel_rerun_local_lean_path = _artifact_path(
        artifacts,
        "proof_search_kernel_rerun_local_lean",
        run_dir,
    )
    proof_search_kernel_rerun_local_lean_payload = _read_json(
        proof_search_kernel_rerun_local_lean_path
    )
    kernel_proof_evidence_overlays = _kernel_proof_evidence_overlays(
        run_dir,
        system_proof_bank_fingerprint=str(proof_payload.get("proof_bank_fingerprint", "")),
    )
    retrieval_payload = _read_json(_artifact_path(artifacts, "formal_source_retrieval_benchmark", run_dir))
    retrieval_ablation_payload = _read_json(
        _artifact_path(artifacts, "formal_source_retrieval_ablation", run_dir)
    )
    lean_rag_package_payload = _read_json(_artifact_path(artifacts, "lean_rag_package_audit", run_dir))
    lean_rag_dependency_health_path = _artifact_path(
        artifacts,
        "lean_rag_dependency_health",
        run_dir,
    )
    lean_rag_dependency_health_payload = _read_json(lean_rag_dependency_health_path)
    proof_search_ablation_payload = _read_json(
        _artifact_path(artifacts, "proof_search_retrieval_ablation", run_dir)
    )
    proof_search_no_registered_ablation_path = _artifact_path(
        artifacts,
        "proof_search_retrieval_no_registered_ablation",
        run_dir,
    )
    proof_search_no_registered_ablation_payload = _read_json(proof_search_no_registered_ablation_path)
    primitive_payload = _read_json(_artifact_path(artifacts, "primitive_source_coverage", run_dir))
    expansion_payload = _read_json(_artifact_path(artifacts, "proof_bank_expansion", run_dir))
    theorem_composition_path = _artifact_path(artifacts, "theorem_composition", run_dir)
    theorem_composition_payload = _read_json(theorem_composition_path)
    formal_verifier_queue_path = _artifact_path(artifacts, "formal_verifier_queue", run_dir)
    formal_verifier_queue_payload = _read_json(formal_verifier_queue_path)
    proof_search_kernel_rerun_queue_path = _artifact_path(
        artifacts,
        "proof_search_kernel_rerun_queue",
        run_dir,
    )
    proof_search_kernel_rerun_queue_payload = _read_json(proof_search_kernel_rerun_queue_path)
    goal_conditioned_minimal_formalization_plan_path = _artifact_path(
        artifacts,
        "goal_conditioned_minimal_formalization_plan",
        run_dir,
    )
    goal_conditioned_minimal_formalization_plan_payload = _read_json(
        goal_conditioned_minimal_formalization_plan_path
    )
    formal_verifier_replay_path = _artifact_path(artifacts, "formal_verifier_replay", run_dir)
    formal_verifier_replay_payload = _read_json(formal_verifier_replay_path)
    formal_verifier_replay_attempt_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_attempts",
        run_dir,
    )
    formal_verifier_replay_attempt_payload = _read_json(formal_verifier_replay_attempt_path)
    formal_verifier_replay_calibration_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_calibration",
        run_dir,
    )
    formal_verifier_replay_calibration_payload = _read_json(
        formal_verifier_replay_calibration_path
    )
    formal_verifier_replay_repair_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair",
        run_dir,
    )
    formal_verifier_replay_repair_payload = _read_json(formal_verifier_replay_repair_path)
    formal_verifier_replay_repair_application_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_application",
        run_dir,
    )
    formal_verifier_replay_repair_application_payload = _read_json(
        formal_verifier_replay_repair_application_path
    )
    formal_verifier_replay_repair_application_validation_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_application_validation",
        run_dir,
    )
    formal_verifier_replay_repair_application_validation_payload = _read_json(
        formal_verifier_replay_repair_application_validation_path
    )
    formal_verifier_replay_repair_execution_queue_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_execution_queue",
        run_dir,
    )
    formal_verifier_replay_repair_execution_queue_payload = _read_json(
        formal_verifier_replay_repair_execution_queue_path
    )
    formal_verifier_replay_repair_prompt_packets_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_prompt_packets",
        run_dir,
    )
    formal_verifier_replay_repair_prompt_packets_payload = _read_json(
        formal_verifier_replay_repair_prompt_packets_path
    )
    formal_verifier_replay_repair_patch_autoworker_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_autoworker",
        run_dir,
    )
    formal_verifier_replay_repair_patch_autoworker_payload = _read_json(
        formal_verifier_replay_repair_patch_autoworker_path
    )
    formal_verifier_replay_repair_patch_response_validation_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_response_validation",
        run_dir,
    )
    formal_verifier_replay_repair_patch_response_validation_payload = _read_json(
        formal_verifier_replay_repair_patch_response_validation_path
    )
    formal_verifier_replay_repair_patch_response_promotion_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_response_promotion",
        run_dir,
    )
    formal_verifier_replay_repair_patch_response_promotion_payload = _read_json(
        formal_verifier_replay_repair_patch_response_promotion_path
    )
    formal_verifier_replay_repair_patch_rerun_queue_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_rerun_queue",
        run_dir,
    )
    formal_verifier_replay_repair_patch_rerun_queue_payload = _read_json(
        formal_verifier_replay_repair_patch_rerun_queue_path
    )
    formal_verifier_replay_repair_patch_rerun_attempt_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_rerun_attempts",
        run_dir,
    )
    formal_verifier_replay_repair_patch_rerun_attempt_payload = _read_json(
        formal_verifier_replay_repair_patch_rerun_attempt_path
    )
    formal_verifier_replay_repair_patch_rerun_calibration_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_rerun_calibration",
        run_dir,
    )
    formal_verifier_replay_repair_patch_rerun_calibration_payload = _read_json(
        formal_verifier_replay_repair_patch_rerun_calibration_path
    )
    formal_verifier_replay_repair_patch_rerun_residual_obligation_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_rerun_residual_obligations",
        run_dir,
    )
    formal_verifier_replay_repair_patch_rerun_residual_obligation_payload = _read_json(
        formal_verifier_replay_repair_patch_rerun_residual_obligation_path
    )
    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets",
        run_dir,
    )
    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_payload = _read_json(
        formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_path
    )
    formal_verifier_replay_repair_patch_rerun_residual_autoworker_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_rerun_residual_autoworker",
        run_dir,
    )
    formal_verifier_replay_repair_patch_rerun_residual_autoworker_payload = _read_json(
        formal_verifier_replay_repair_patch_rerun_residual_autoworker_path
    )
    formal_verifier_replay_repair_patch_rerun_residual_response_validation_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_rerun_residual_response_validation",
        run_dir,
    )
    formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload = _read_json(
        formal_verifier_replay_repair_patch_rerun_residual_response_validation_path
    )
    formal_verifier_replay_repair_patch_rerun_residual_followup_queue_path = _artifact_path(
        artifacts,
        "formal_verifier_replay_repair_patch_rerun_residual_followup_queue",
        run_dir,
    )
    formal_verifier_replay_repair_patch_rerun_residual_followup_queue_payload = _read_json(
        formal_verifier_replay_repair_patch_rerun_residual_followup_queue_path
    )
    formal_verifier_agentic_proof_strategy_plan_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_strategy_plan",
        run_dir,
    )
    formal_verifier_agentic_proof_strategy_plan_payload = _read_json(
        formal_verifier_agentic_proof_strategy_plan_path
    )
    formal_verifier_agentic_proof_candidate_evaluation_queue_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_candidate_evaluation_queue",
        run_dir,
    )
    formal_verifier_agentic_proof_candidate_evaluation_queue_payload = _read_json(
        formal_verifier_agentic_proof_candidate_evaluation_queue_path
    )
    formal_verifier_agentic_proof_safety_policy_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_safety_policy",
        run_dir,
    )
    formal_verifier_agentic_proof_safety_policy_payload = _read_json(
        formal_verifier_agentic_proof_safety_policy_path
    )
    formal_verifier_agentic_proof_attempt_population_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_attempt_population",
        run_dir,
    )
    formal_verifier_agentic_proof_attempt_population_payload = _read_json(
        formal_verifier_agentic_proof_attempt_population_path
    )
    formal_verifier_agentic_proof_execution_queue_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_execution_queue",
        run_dir,
    )
    formal_verifier_agentic_proof_execution_queue_payload = _read_json(
        formal_verifier_agentic_proof_execution_queue_path
    )
    formal_verifier_agentic_proof_execution_materializer_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_execution_materializer",
        run_dir,
    )
    formal_verifier_agentic_proof_execution_materializer_payload = _read_json(
        formal_verifier_agentic_proof_execution_materializer_path
    )
    formal_verifier_agentic_proof_execution_artifact_verifier_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_execution_artifact_verifier",
        run_dir,
    )
    formal_verifier_agentic_proof_execution_artifact_verifier_payload = _read_json(
        formal_verifier_agentic_proof_execution_artifact_verifier_path
    )
    formal_verifier_agentic_proof_trace_memory_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_trace_memory",
        run_dir,
    )
    formal_verifier_agentic_proof_trace_memory_payload = _read_json(
        formal_verifier_agentic_proof_trace_memory_path
    )
    formal_verifier_agentic_proof_source_theorem_promotion_queue_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_source_theorem_promotion_queue",
        run_dir,
    )
    formal_verifier_agentic_proof_source_theorem_promotion_queue_payload = _read_json(
        formal_verifier_agentic_proof_source_theorem_promotion_queue_path
    )
    formal_verifier_agentic_proof_source_theorem_target_resolution_path = _artifact_path(
        artifacts,
        "formal_verifier_agentic_proof_source_theorem_target_resolution",
        run_dir,
    )
    formal_verifier_agentic_proof_source_theorem_target_resolution_payload = _read_json(
        formal_verifier_agentic_proof_source_theorem_target_resolution_path
    )
    formalization_gap_planner_proof_state_triage_path = _artifact_path(
        artifacts,
        "formalization_gap_planner_proof_state_triage",
        run_dir,
    )
    formalization_gap_planner_proof_state_triage_payload = _read_json(
        formalization_gap_planner_proof_state_triage_path
    )
    huggingface_lean_source_audit_path = _artifact_path(
        artifacts,
        "huggingface_lean_source_audit",
        run_dir,
    )
    huggingface_lean_source_audit_payload = _read_json(huggingface_lean_source_audit_path)
    huggingface_lean_source_revalidation_tasks_path = _artifact_path(
        artifacts,
        "huggingface_lean_source_revalidation_tasks",
        run_dir,
    )
    huggingface_lean_source_revalidation_tasks_payload = _read_json(
        huggingface_lean_source_revalidation_tasks_path
    )
    huggingface_lean_source_revalidation_prompt_packets_path = _artifact_path(
        artifacts,
        "huggingface_lean_source_revalidation_prompt_packets",
        run_dir,
    )
    huggingface_lean_source_revalidation_prompt_packets_payload = _read_json(
        huggingface_lean_source_revalidation_prompt_packets_path
    )
    huggingface_lean_source_revalidation_artifact_validation_path = _artifact_path(
        artifacts,
        "huggingface_lean_source_revalidation_artifact_validation",
        run_dir,
    )
    huggingface_lean_source_revalidation_artifact_validation_payload = _read_json(
        huggingface_lean_source_revalidation_artifact_validation_path
    )
    huggingface_lean_source_revalidation_promotion_queue_path = _artifact_path(
        artifacts,
        "huggingface_lean_source_revalidation_promotion_queue",
        run_dir,
    )
    huggingface_lean_source_revalidation_promotion_queue_payload = _read_json(
        huggingface_lean_source_revalidation_promotion_queue_path
    )
    guidance_payload = _read_json(_artifact_path(artifacts, "evaluation_benchmark_guidance", run_dir))
    counts = _overlay_auto_discovered_agentic_counts(
        counts,
        artifact_auto_discoveries,
        formal_verifier_agentic_proof_strategy_plan_payload=formal_verifier_agentic_proof_strategy_plan_payload,
        formal_verifier_agentic_proof_candidate_evaluation_queue_payload=formal_verifier_agentic_proof_candidate_evaluation_queue_payload,
        formal_verifier_agentic_proof_safety_policy_payload=formal_verifier_agentic_proof_safety_policy_payload,
        formal_verifier_agentic_proof_attempt_population_payload=formal_verifier_agentic_proof_attempt_population_payload,
        formal_verifier_agentic_proof_execution_queue_payload=formal_verifier_agentic_proof_execution_queue_payload,
        formal_verifier_agentic_proof_execution_materializer_payload=formal_verifier_agentic_proof_execution_materializer_payload,
        formal_verifier_agentic_proof_execution_artifact_verifier_payload=formal_verifier_agentic_proof_execution_artifact_verifier_payload,
        formal_verifier_agentic_proof_trace_memory_payload=formal_verifier_agentic_proof_trace_memory_payload,
        formal_verifier_agentic_proof_source_theorem_promotion_queue_payload=formal_verifier_agentic_proof_source_theorem_promotion_queue_payload,
        formal_verifier_agentic_proof_source_theorem_target_resolution_payload=formal_verifier_agentic_proof_source_theorem_target_resolution_payload,
    )
    huggingface_lean_source_summary = dict(
        huggingface_lean_source_audit_payload.get("summary", {}) or {}
    )
    huggingface_lean_source_revalidation_queue_summary = dict(
        huggingface_lean_source_audit_payload.get("revalidation_queue_summary", {}) or {}
    )

    target_rows = _handoff_targets(
        primitive_payload.get("rows", []),
        expansion_payload.get("candidates", []),
        max_targets=max_targets,
    )
    theorem_composition_handoff = {
        "theorem_composition_packets": counts.get(
            "theorem_composition_packets",
            theorem_composition_payload.get("n_packets"),
        ),
        "theorem_composition_packets_ok": counts.get(
            "theorem_composition_packets_ok",
            theorem_composition_payload.get("n_ok"),
        ),
        "theorem_composition_exact_proof_bank_links": counts.get(
            "theorem_composition_exact_proof_bank_links",
            theorem_composition_payload.get("n_exact_proof_bank_links"),
        ),
        "theorem_composition_unresolved_primitives": counts.get(
            "theorem_composition_unresolved_primitives",
            theorem_composition_payload.get("n_unresolved_primitives"),
        ),
        "theorem_composition_packets_with_unresolved_primitives": counts.get(
            "theorem_composition_packets_with_unresolved_primitives",
            theorem_composition_payload.get("n_packets_with_unresolved_primitives"),
        ),
        "theorem_composition_ready_for_exact_reuse": counts.get(
            "theorem_composition_ready_for_exact_reuse",
            theorem_composition_payload.get("n_ready_for_exact_reuse_composition"),
        ),
        "theorem_composition_manifest": str(theorem_composition_path),
        "packet_preview": _theorem_composition_packet_preview(
            theorem_composition_payload,
            max_packets=min(max_targets, 10),
        ),
        "proof_evidence_boundary": (
            "Theorem-composition packets are coordination plans. Exact proof-bank obligations "
            "are Lean proof evidence only for their registered subclaims; the enclosing "
            "frontier theorem remains a FORMAL_GAP until a non-placeholder composed proof "
            "passes AXLE/local Lean verify_proof."
        ),
    }
    kernel_proof_overlay_alignment = _kernel_proof_overlay_alignment(
        kernel_proof_evidence_overlays,
        theorem_composition_handoff,
        formal_verifier_queue_payload,
        formal_verifier_replay_payload,
        max_rows=min(max_targets, 10),
    )
    payload: dict[str, object] = {
        "schema_version": RAG_COLLABORATION_EXPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_system_audit_manifest": str(system_audit_manifest),
        "source_run_dir": str(run_dir),
        "artifact_overrides_applied": dict(sorted(normalized_artifact_overrides.items())),
        "artifact_auto_discoveries_applied": dict(sorted(artifact_auto_discoveries.items())),
        "proof_evidence": {
            "proofs_kernel_verified": counts.get("proofs_kernel_verified"),
            "proofs_total": counts.get("proofs_total"),
            "proof_verification_strength": counts.get("proof_verification_strength"),
            "proof_bank_fingerprint": proof_payload.get("proof_bank_fingerprint"),
            "proof_dependency_edges": counts.get("proof_dependency_edges"),
            "proof_audit_manifest": str(_artifact_path(artifacts, "proof_audit", run_dir)),
            "proof_search_kernel_rerun_local_lean_verified": counts.get(
                "proof_search_kernel_rerun_local_lean_verified",
                proof_search_kernel_rerun_local_lean_payload.get("n_kernel_verified"),
            ),
            "proof_search_kernel_rerun_local_lean_total": counts.get(
                "proof_search_kernel_rerun_local_lean_total",
                proof_search_kernel_rerun_local_lean_payload.get("n_obligations"),
            ),
            "proof_search_kernel_rerun_local_lean_verifier": counts.get(
                "proof_search_kernel_rerun_local_lean_verifier",
                proof_search_kernel_rerun_local_lean_payload.get("verifier"),
            ),
            "proof_search_kernel_rerun_local_lean_manifest": str(
                proof_search_kernel_rerun_local_lean_path
            ),
            "proof_search_kernel_rerun_local_lean_results": str(
                proof_search_kernel_rerun_local_lean_payload.get("results_jsonl", "")
            ),
            "proof_search_kernel_rerun_local_lean_boundary": (
                "Focused local Lean proof-search rerun evidence calibrates the selected "
                "proof-search obligations only. It does not mutate the default system-audit "
                "proof_search_kernel_verified count unless the system audit itself is run "
                "with AXLE/local Lean."
            ),
        },
        "kernel_proof_evidence_overlays": kernel_proof_evidence_overlays,
        "kernel_proof_overlay_alignment": kernel_proof_overlay_alignment,
        "rag_provider_evidence": {
            "lean_rag_dependency_graph_enabled": counts.get("lean_rag_dependency_graph_enabled"),
            "lean_rag_dependency_graph_path": counts.get("lean_rag_dependency_graph_path"),
            "lean_rag_dependency_graph_auto_discovered": counts.get(
                "lean_rag_dependency_graph_auto_discovered"
            ),
            "lean_rag_dependency_health_status": counts.get(
                "lean_rag_dependency_health_status",
                lean_rag_dependency_health_payload.get("health_status"),
            ),
            "lean_rag_dependency_health_ok": counts.get(
                "lean_rag_dependency_health_ok",
                lean_rag_dependency_health_payload.get("all_ok"),
            ),
            "lean_rag_dependency_active_enabled": counts.get(
                "lean_rag_dependency_active_enabled",
                lean_rag_dependency_health_payload.get("active_enabled"),
            ),
            "lean_rag_dependency_fallback_used": counts.get(
                "lean_rag_dependency_fallback_used",
                lean_rag_dependency_health_payload.get("fallback_used"),
            ),
            "lean_rag_dependency_fallback_reason": counts.get(
                "lean_rag_dependency_fallback_reason",
                lean_rag_dependency_health_payload.get("fallback_reason"),
            ),
            "lean_rag_dependency_health_manifest": str(lean_rag_dependency_health_path),
            "lean_rag_package_available": counts.get("lean_rag_package_available"),
            "lean_rag_package_contract_ok": counts.get("lean_rag_package_contract_ok"),
            "lean_rag_package_root": counts.get("lean_rag_package_root"),
            "lean_rag_package_branch": counts.get("lean_rag_package_branch"),
            "lean_rag_package_commit": counts.get("lean_rag_package_commit"),
            "lean_rag_package_dirty": counts.get("lean_rag_package_dirty"),
            "lean_rag_package_local_sources": counts.get("lean_rag_package_local_sources"),
            "lean_rag_package_external_sources": counts.get("lean_rag_package_external_sources"),
            "lean_rag_package_seed_queries": counts.get("lean_rag_package_seed_queries"),
            "lean_rag_package_seed_query_lanes": counts.get("lean_rag_package_seed_query_lanes"),
            "lean_rag_package_seed_lanes": _lean_rag_seed_lanes(lean_rag_package_payload),
            "lean_rag_package_target_sources": counts.get("lean_rag_package_target_sources"),
            "lean_rag_package_target_sources_present": counts.get(
                "lean_rag_package_target_sources_present"
            ),
            "lean_rag_package_target_sources_missing": counts.get(
                "lean_rag_package_target_sources_missing"
            ),
            "lean_rag_package_target_source_coverage_ok": counts.get(
                "lean_rag_package_target_source_coverage_ok"
            ),
            "lean_rag_package_missing_target_sources": counts.get(
                "lean_rag_package_missing_target_sources",
                dict(lean_rag_package_payload.get("target_source_coverage", {}) or {}).get(
                    "missing_target_ids",
                    [],
                ),
            ),
            "lean_rag_package_target_source_boundary": dict(
                lean_rag_package_payload.get("target_source_coverage", {}) or {}
            ).get("proof_evidence_boundary", ""),
            "lean_rag_package_registry_expansion_candidates": counts.get(
                "lean_rag_package_registry_expansion_candidates",
                dict(lean_rag_package_payload.get("target_source_coverage", {}) or {}).get(
                    "n_registry_expansion_candidates",
                    0,
                ),
            ),
            "lean_rag_package_registry_expansion_candidate_names": counts.get(
                "lean_rag_package_registry_expansion_candidate_names",
                [
                    str(dict(candidate.get("entry", {}) or {}).get("name", ""))
                    for candidate in dict(
                        lean_rag_package_payload.get("target_source_coverage", {}) or {}
                    ).get("registry_expansion_candidates", [])
                    if isinstance(candidate, dict)
                ],
            ),
            "lean_rag_package_registry_expansion_candidate_entries": dict(
                lean_rag_package_payload.get("target_source_coverage", {}) or {}
            ).get("registry_expansion_candidates", []),
            "lean_rag_package_policy": dict(
                dict(lean_rag_package_payload.get("source_registry", {}) or {}).get("policy", {})
                or {}
            ),
            "lean_rag_package_manifest": str(
                _artifact_path(artifacts, "lean_rag_package_audit", run_dir)
            ),
            "formal_source_graph_symbols": counts.get("formal_source_graph_symbols"),
            "formal_source_graph_edges": counts.get("formal_source_graph_edges"),
            "formal_source_retrieval_recall_at_k": counts.get(
                "formal_source_retrieval_benchmark_recall_at_k"
            ),
            "formal_source_retrieval_mrr": counts.get("formal_source_retrieval_benchmark_mrr"),
            "formal_source_retrieval_external_recall_at_k": counts.get(
                "formal_source_retrieval_external_benchmark_recall_at_k"
            ),
            "formal_source_retrieval_external_mrr": counts.get(
                "formal_source_retrieval_external_benchmark_mrr"
            ),
            "formal_source_retrieval_all_recall_at_k": counts.get(
                "formal_source_retrieval_all_benchmark_recall_at_k"
            ),
            "formal_source_retrieval_all_mrr": counts.get("formal_source_retrieval_all_benchmark_mrr"),
            "retrieval_benchmark_manifest": str(
                _artifact_path(artifacts, "formal_source_retrieval_benchmark", run_dir)
            ),
            "retrieval_external_benchmark_manifest": str(
                _artifact_path(artifacts, "formal_source_retrieval_external_benchmark", run_dir)
            ),
            "retrieval_all_benchmark_manifest": str(
                _artifact_path(artifacts, "formal_source_retrieval_all_benchmark", run_dir)
            ),
            "dependency_graph_search": retrieval_payload.get("dependency_graph_search", ""),
        },
        "retrieval_ablation_evidence": {
            "formal_source_cases": retrieval_ablation_payload.get("n_cases"),
            "formal_source_new_hits": retrieval_ablation_payload.get("n_new_hits"),
            "formal_source_lost_hits": retrieval_ablation_payload.get("n_lost_hits"),
            "formal_source_dependency_sensitive_new_hits": retrieval_ablation_payload.get(
                "n_dependency_sensitive_new_hits"
            ),
            "proof_search_solved_delta": proof_search_ablation_payload.get("solved_delta"),
            "proof_search_candidate_delta": proof_search_ablation_payload.get(
                "formal_source_candidate_delta"
            ),
            "proof_search_node_delta": proof_search_ablation_payload.get("nodes_expanded_delta"),
            "proof_search_dependency_graph_search": proof_search_ablation_payload.get(
                "dependency_graph_search", ""
            ),
            "proof_search_no_registered_solved_delta": proof_search_no_registered_ablation_payload.get(
                "solved_delta"
            ),
            "proof_search_no_registered_candidate_delta": proof_search_no_registered_ablation_payload.get(
                "formal_source_candidate_delta"
            ),
            "proof_search_no_registered_node_delta": proof_search_no_registered_ablation_payload.get(
                "nodes_expanded_delta"
            ),
            "proof_search_no_registered_include_registered_proof": proof_search_no_registered_ablation_payload.get(
                "include_registered_proof"
            ),
            "proof_search_no_registered_dependency_graph_search": proof_search_no_registered_ablation_payload.get(
                "dependency_graph_search",
                "",
            ),
            "formal_source_retrieval_ablation_manifest": str(
                _artifact_path(artifacts, "formal_source_retrieval_ablation", run_dir)
            ),
            "proof_search_retrieval_ablation_manifest": str(
                _artifact_path(artifacts, "proof_search_retrieval_ablation", run_dir)
            ),
            "proof_search_retrieval_no_registered_ablation_manifest": str(
                proof_search_no_registered_ablation_path
            ),
        },
        "formal_capacity_queue": {
            "missing_formal_primitives": counts.get("missing_formal_primitives"),
            "formalization_targets_with_proof_bank_bridge": counts.get(
                "formalization_targets_with_proof_bank_bridge"
            ),
            "formalization_targets_exact_proof_bank_resolved": counts.get(
                "formalization_targets_exact_proof_bank_resolved"
            ),
            "reuse_exact_proof_bank_obligation": counts.get(
                "proof_bank_expansion_reuse_exact_proof_bank_obligation"
            ),
            "compose_existing_bridge_chain": counts.get(
                "proof_bank_expansion_compose_existing_bridge_chain"
            ),
            "add_minimal_wrapper": counts.get("proof_bank_expansion_add_minimal_wrapper"),
            "design_bridge_lemma": counts.get("proof_bank_expansion_design_bridge_lemma"),
            "design_from_first_principles": counts.get(
                "proof_bank_expansion_design_from_first_principles"
            ),
            "primitive_source_external_supported": counts.get(
                "primitive_source_coverage_external_supported"
            ),
            "formal_verifier_queue_items": counts.get(
                "formal_verifier_queue_items",
                formal_verifier_queue_payload.get("n_items"),
            ),
            "formal_verifier_queue_high_priority": counts.get(
                "formal_verifier_queue_high_priority",
                formal_verifier_queue_payload.get("n_high_priority"),
            ),
            "formal_verifier_queue_requires_new_theory": counts.get(
                "formal_verifier_queue_requires_new_theory",
                formal_verifier_queue_payload.get("n_requires_new_theory"),
            ),
            "formal_verifier_queue_routes_with_no_registered_rag_lift": counts.get(
                "formal_verifier_queue_routes_with_no_registered_rag_lift",
                formal_verifier_queue_payload.get("n_routes_with_no_registered_rag_lift"),
            ),
            "formal_verifier_queue_rows_with_attempt_history": counts.get(
                "formal_verifier_queue_rows_with_attempt_history",
                formal_verifier_queue_payload.get("n_rows_with_attempt_history"),
            ),
            "formal_verifier_queue_proof_attempt_positive": counts.get(
                "formal_verifier_queue_proof_attempt_positive",
                formal_verifier_queue_payload.get("n_proof_attempt_positive"),
            ),
            "formal_verifier_queue_proof_attempt_negative": counts.get(
                "formal_verifier_queue_proof_attempt_negative",
                formal_verifier_queue_payload.get("n_proof_attempt_negative"),
            ),
            "formal_verifier_queue_proof_search_solved": counts.get(
                "formal_verifier_queue_proof_search_solved",
                formal_verifier_queue_payload.get("n_proof_search_solved"),
            ),
            "proof_search_kernel_rerun_queue_items": counts.get(
                "proof_search_kernel_rerun_queue_items",
                proof_search_kernel_rerun_queue_payload.get("n_queue_rows"),
            ),
            "proof_search_kernel_rerun_queue_ready": counts.get(
                "proof_search_kernel_rerun_queue_ready",
                proof_search_kernel_rerun_queue_payload.get("n_ready_for_local_lean_or_axle"),
            ),
            "proof_search_kernel_rerun_queue_blocked": counts.get(
                "proof_search_kernel_rerun_queue_blocked",
                proof_search_kernel_rerun_queue_payload.get(
                    "n_blocked_missing_selected_proof_body"
                ),
            ),
            "proof_search_kernel_rerun_queue_manifest": str(proof_search_kernel_rerun_queue_path),
            "proof_search_kernel_rerun_queue_command": proof_search_kernel_rerun_queue_payload.get(
                "batch_local_lean_rerun_command",
                "",
            ),
            "proof_search_kernel_rerun_queue_preview": _proof_search_kernel_rerun_queue_preview(
                proof_search_kernel_rerun_queue_payload,
                max_rows=min(max_targets, 10),
            ),
            "huggingface_lean_source_candidates": counts.get(
                "huggingface_lean_source_candidates",
                huggingface_lean_source_summary.get("n_candidates"),
            ),
            "huggingface_lean_source_high_priority": counts.get(
                "huggingface_lean_source_high_priority",
                huggingface_lean_source_summary.get("n_high"),
            ),
            "huggingface_lean_source_critical": counts.get(
                "huggingface_lean_source_critical",
                huggingface_lean_source_summary.get("n_critical"),
            ),
            "huggingface_lean_source_public_ungated": counts.get(
                "huggingface_lean_source_public_ungated",
                huggingface_lean_source_summary.get("n_public_ungated"),
            ),
            "huggingface_lean_source_formal_proof_pair_sources": counts.get(
                "huggingface_lean_source_formal_proof_pair_sources",
                huggingface_lean_source_summary.get("n_formal_proof_pair_sources"),
            ),
            "huggingface_lean_source_tactic_state_sources": counts.get(
                "huggingface_lean_source_tactic_state_sources",
                huggingface_lean_source_summary.get("n_tactic_state_sources"),
            ),
            "huggingface_lean_source_repair_or_process_sources": counts.get(
                "huggingface_lean_source_repair_or_process_sources",
                huggingface_lean_source_summary.get("n_repair_or_process_sources"),
            ),
            "huggingface_lean_source_formal_code_corpora": counts.get(
                "huggingface_lean_source_formal_code_corpora",
                huggingface_lean_source_summary.get("n_formal_code_corpora"),
            ),
            "huggingface_lean_source_total_reported_dataset_rows": counts.get(
                "huggingface_lean_source_total_reported_dataset_rows",
                huggingface_lean_source_summary.get("total_reported_dataset_rows"),
            ),
            "huggingface_lean_source_oproofs_detected": counts.get(
                "huggingface_lean_source_oproofs_detected",
                huggingface_lean_source_summary.get("oproofs_detected"),
            ),
            "huggingface_lean_source_oproofs_reported_rows": counts.get(
                "huggingface_lean_source_oproofs_reported_rows",
                huggingface_lean_source_summary.get("oproofs_reported_rows"),
            ),
            "huggingface_lean_source_oproofs_parquet_shards": counts.get(
                "huggingface_lean_source_oproofs_parquet_shards",
                huggingface_lean_source_summary.get("oproofs_parquet_shards"),
            ),
            "huggingface_lean_source_rag_integration_rows": counts.get(
                "huggingface_lean_source_rag_integration_rows",
                len(huggingface_lean_source_audit_payload.get("rag_integration_plan", []) or []),
            ),
            "huggingface_lean_source_revalidation_queue_rows": counts.get(
                "huggingface_lean_source_revalidation_queue_rows",
                huggingface_lean_source_revalidation_queue_summary.get("n_queue_rows"),
            ),
            "huggingface_lean_source_revalidation_queue_ready": counts.get(
                "huggingface_lean_source_revalidation_queue_ready",
                huggingface_lean_source_revalidation_queue_summary.get("n_ready"),
            ),
            "huggingface_lean_source_revalidation_queue_blocked": counts.get(
                "huggingface_lean_source_revalidation_queue_blocked",
                huggingface_lean_source_revalidation_queue_summary.get("n_blocked"),
            ),
            "huggingface_lean_source_revalidation_queue_kernel_verified": counts.get(
                "huggingface_lean_source_revalidation_queue_kernel_verified",
                huggingface_lean_source_revalidation_queue_summary.get("n_kernel_verified"),
            ),
            "huggingface_lean_source_revalidation_queue_proof_evidence_ready": counts.get(
                "huggingface_lean_source_revalidation_queue_proof_evidence_ready",
                huggingface_lean_source_revalidation_queue_summary.get("n_proof_evidence_ready"),
            ),
            "huggingface_lean_source_revalidation_queue_proof_evidence_status": counts.get(
                "huggingface_lean_source_revalidation_queue_proof_evidence_status",
                huggingface_lean_source_revalidation_queue_summary.get("proof_evidence_status"),
            ),
            "huggingface_lean_source_revalidation_tasks": counts.get(
                "huggingface_lean_source_revalidation_tasks",
                huggingface_lean_source_revalidation_tasks_payload.get("n_tasks"),
            ),
            "huggingface_lean_source_revalidation_tasks_ready": counts.get(
                "huggingface_lean_source_revalidation_tasks_ready",
                huggingface_lean_source_revalidation_tasks_payload.get("n_ready"),
            ),
            "huggingface_lean_source_revalidation_tasks_blocked": counts.get(
                "huggingface_lean_source_revalidation_tasks_blocked",
                huggingface_lean_source_revalidation_tasks_payload.get("n_blocked"),
            ),
            "huggingface_lean_source_revalidation_tasks_license_review_required": counts.get(
                "huggingface_lean_source_revalidation_tasks_license_review_required",
                huggingface_lean_source_revalidation_tasks_payload.get(
                    "n_license_review_required"
                ),
            ),
            "huggingface_lean_source_revalidation_tasks_kernel_verified": counts.get(
                "huggingface_lean_source_revalidation_tasks_kernel_verified",
                huggingface_lean_source_revalidation_tasks_payload.get("n_kernel_verified"),
            ),
            "huggingface_lean_source_revalidation_tasks_proof_evidence_ready": counts.get(
                "huggingface_lean_source_revalidation_tasks_proof_evidence_ready",
                huggingface_lean_source_revalidation_tasks_payload.get(
                    "n_proof_evidence_ready"
                ),
            ),
            "huggingface_lean_source_revalidation_tasks_proof_evidence_status": counts.get(
                "huggingface_lean_source_revalidation_tasks_proof_evidence_status",
                huggingface_lean_source_revalidation_tasks_payload.get(
                    "proof_evidence_status"
                ),
            ),
            "huggingface_lean_source_revalidation_prompt_packets": counts.get(
                "huggingface_lean_source_revalidation_prompt_packets",
                huggingface_lean_source_revalidation_prompt_packets_payload.get(
                    "n_prompt_packets"
                ),
            ),
            "huggingface_lean_source_revalidation_prompt_packets_ready_tasks": counts.get(
                "huggingface_lean_source_revalidation_prompt_packets_ready_tasks",
                huggingface_lean_source_revalidation_prompt_packets_payload.get(
                    "n_ready_tasks"
                ),
            ),
            "huggingface_lean_source_revalidation_prompt_packets_license_review_required": counts.get(
                "huggingface_lean_source_revalidation_prompt_packets_license_review_required",
                huggingface_lean_source_revalidation_prompt_packets_payload.get(
                    "n_license_review_required"
                ),
            ),
            "huggingface_lean_source_revalidation_prompt_packets_output_contracts": counts.get(
                "huggingface_lean_source_revalidation_prompt_packets_output_contracts",
                huggingface_lean_source_revalidation_prompt_packets_payload.get(
                    "n_with_output_contract"
                ),
            ),
            "huggingface_lean_source_revalidation_prompt_packets_proof_evidence_status": counts.get(
                "huggingface_lean_source_revalidation_prompt_packets_proof_evidence_status",
                huggingface_lean_source_revalidation_prompt_packets_payload.get(
                    "proof_evidence_status"
                ),
            ),
            "huggingface_lean_source_revalidation_artifact_validation_rows": counts.get(
                "huggingface_lean_source_revalidation_artifact_validation_rows",
                huggingface_lean_source_revalidation_artifact_validation_payload.get(
                    "n_validation_rows"
                ),
            ),
            "huggingface_lean_source_revalidation_artifact_validation_responses": counts.get(
                "huggingface_lean_source_revalidation_artifact_validation_responses",
                huggingface_lean_source_revalidation_artifact_validation_payload.get(
                    "n_responses"
                ),
            ),
            "huggingface_lean_source_revalidation_artifact_validation_awaiting": counts.get(
                "huggingface_lean_source_revalidation_artifact_validation_awaiting",
                huggingface_lean_source_revalidation_artifact_validation_payload.get(
                    "n_awaiting_worker_output"
                ),
            ),
            "huggingface_lean_source_revalidation_artifact_validation_contract_ok": counts.get(
                "huggingface_lean_source_revalidation_artifact_validation_contract_ok",
                huggingface_lean_source_revalidation_artifact_validation_payload.get(
                    "n_contract_ok"
                ),
            ),
            "huggingface_lean_source_revalidation_artifact_validation_kernel_verified_rows": counts.get(
                "huggingface_lean_source_revalidation_artifact_validation_kernel_verified_rows",
                huggingface_lean_source_revalidation_artifact_validation_payload.get(
                    "n_kernel_verified_rows"
                ),
            ),
            "huggingface_lean_source_revalidation_artifact_validation_proof_evidence_ready": counts.get(
                "huggingface_lean_source_revalidation_artifact_validation_proof_evidence_ready",
                huggingface_lean_source_revalidation_artifact_validation_payload.get(
                    "n_proof_evidence_ready"
                ),
            ),
            "huggingface_lean_source_revalidation_artifact_validation_proof_evidence_status": counts.get(
                "huggingface_lean_source_revalidation_artifact_validation_proof_evidence_status",
                huggingface_lean_source_revalidation_artifact_validation_payload.get(
                    "proof_evidence_status"
                ),
            ),
            "huggingface_lean_source_revalidation_promotion_rows": counts.get(
                "huggingface_lean_source_revalidation_promotion_rows",
                huggingface_lean_source_revalidation_promotion_queue_payload.get(
                    "n_promotion_rows"
                ),
            ),
            "huggingface_lean_source_revalidation_promotion_ready": counts.get(
                "huggingface_lean_source_revalidation_promotion_ready",
                huggingface_lean_source_revalidation_promotion_queue_payload.get(
                    "n_ready_for_promotion"
                ),
            ),
            "huggingface_lean_source_revalidation_promotion_awaiting": counts.get(
                "huggingface_lean_source_revalidation_promotion_awaiting",
                huggingface_lean_source_revalidation_promotion_queue_payload.get(
                    "n_awaiting_worker_output"
                ),
            ),
            "huggingface_lean_source_revalidation_promotion_blocked": counts.get(
                "huggingface_lean_source_revalidation_promotion_blocked",
                huggingface_lean_source_revalidation_promotion_queue_payload.get(
                    "n_blocked"
                ),
            ),
            "huggingface_lean_source_revalidation_promotion_kernel_verified_rows": counts.get(
                "huggingface_lean_source_revalidation_promotion_kernel_verified_rows",
                huggingface_lean_source_revalidation_promotion_queue_payload.get(
                    "n_kernel_verified_rows"
                ),
            ),
            "huggingface_lean_source_revalidation_promotion_proof_evidence_ready": counts.get(
                "huggingface_lean_source_revalidation_promotion_proof_evidence_ready",
                huggingface_lean_source_revalidation_promotion_queue_payload.get(
                    "n_proof_evidence_ready"
                ),
            ),
            "huggingface_lean_source_revalidation_promotion_proof_evidence_status": counts.get(
                "huggingface_lean_source_revalidation_promotion_proof_evidence_status",
                huggingface_lean_source_revalidation_promotion_queue_payload.get(
                    "proof_evidence_status"
                ),
            ),
            "huggingface_lean_source_proof_evidence_ready": counts.get(
                "huggingface_lean_source_proof_evidence_ready",
                huggingface_lean_source_summary.get("proof_evidence_ready"),
            ),
            "huggingface_lean_source_use_network": counts.get(
                "huggingface_lean_source_use_network",
                huggingface_lean_source_audit_payload.get("use_network"),
            ),
            "huggingface_lean_source_audit_manifest": str(huggingface_lean_source_audit_path),
            "huggingface_lean_source_rag_integration_plan": str(
                _artifact_path(
                    artifacts,
                    "huggingface_lean_source_rag_integration_plan",
                    run_dir,
                )
            ),
            "huggingface_lean_source_revalidation_queue_jsonl": str(
                _artifact_path(
                    artifacts,
                    "huggingface_lean_source_revalidation_queue",
                    run_dir,
                )
            ),
            "huggingface_lean_source_revalidation_tasks_manifest": str(
                huggingface_lean_source_revalidation_tasks_path
            ),
            "huggingface_lean_source_revalidation_prompt_packets_manifest": str(
                huggingface_lean_source_revalidation_prompt_packets_path
            ),
            "huggingface_lean_source_revalidation_artifact_validation_manifest": str(
                huggingface_lean_source_revalidation_artifact_validation_path
            ),
            "huggingface_lean_source_revalidation_promotion_manifest": str(
                huggingface_lean_source_revalidation_promotion_queue_path
            ),
            "huggingface_lean_source_revalidation_queue_preview": _huggingface_lean_source_revalidation_queue_preview(
                huggingface_lean_source_audit_payload,
                max_rows=min(max_targets, 10),
            ),
            "huggingface_lean_source_revalidation_tasks_preview": _huggingface_lean_source_revalidation_tasks_preview(
                huggingface_lean_source_revalidation_tasks_payload,
                max_rows=min(max_targets, 10),
            ),
            "huggingface_lean_source_revalidation_prompt_packets_preview": _huggingface_lean_source_revalidation_prompt_packets_preview(
                huggingface_lean_source_revalidation_prompt_packets_payload,
                max_rows=min(max_targets, 10),
            ),
            "huggingface_lean_source_revalidation_artifact_validation_preview": _huggingface_lean_source_revalidation_artifact_validation_preview(
                huggingface_lean_source_revalidation_artifact_validation_payload,
                max_rows=min(max_targets, 10),
            ),
            "huggingface_lean_source_revalidation_promotion_preview": _huggingface_lean_source_revalidation_promotion_preview(
                huggingface_lean_source_revalidation_promotion_queue_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_queue_max_dependency_graph_depth": counts.get(
                "formal_verifier_queue_max_dependency_graph_depth",
                formal_verifier_queue_payload.get("max_dependency_graph_depth"),
            ),
            "formal_verifier_queue_max_import_cone_size": counts.get(
                "formal_verifier_queue_max_import_cone_size",
                formal_verifier_queue_payload.get("max_import_cone_size"),
            ),
            "formal_verifier_queue_semantic_needs_review": counts.get(
                "formal_verifier_queue_semantic_needs_review",
                formal_verifier_queue_payload.get("n_rows_semantic_needs_review"),
            ),
            "formal_verifier_queue_mean_semantic_faithfulness_score": counts.get(
                "formal_verifier_queue_mean_semantic_faithfulness_score",
                formal_verifier_queue_payload.get("mean_semantic_faithfulness_score"),
            ),
            "formal_verifier_queue_rows_with_kernel_smoke_overlap": counts.get(
                "formal_verifier_queue_rows_with_kernel_smoke_overlap",
                formal_verifier_queue_payload.get("n_rows_with_kernel_smoke_overlap"),
            ),
            "formal_verifier_queue_rows_source_trust_kernel_calibrated": counts.get(
                "formal_verifier_queue_rows_source_trust_kernel_calibrated",
                formal_verifier_queue_payload.get("n_rows_source_trust_kernel_calibrated"),
            ),
            "formal_verifier_queue_manifest": str(formal_verifier_queue_path),
            "formal_verifier_queue_preview": _formal_verifier_queue_preview(
                formal_verifier_queue_payload,
                max_rows=min(max_targets, 10),
            ),
            "goal_conditioned_minimal_formalization_plans": counts.get(
                "goal_conditioned_minimal_formalization_plans",
                goal_conditioned_minimal_formalization_plan_payload.get("n_goal_plans"),
            ),
            "goal_conditioned_minimal_formalization_low_cost": counts.get(
                "goal_conditioned_minimal_formalization_low_cost",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_low_cost_goal_plans"
                ),
            ),
            "goal_conditioned_minimal_formalization_existing_reuse_nodes": counts.get(
                "goal_conditioned_minimal_formalization_existing_reuse_nodes",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_existing_reuse_nodes"
                ),
            ),
            "goal_conditioned_minimal_formalization_wrapper_nodes": counts.get(
                "goal_conditioned_minimal_formalization_wrapper_nodes",
                goal_conditioned_minimal_formalization_plan_payload.get("n_wrapper_nodes"),
            ),
            "goal_conditioned_minimal_formalization_bridge_nodes": counts.get(
                "goal_conditioned_minimal_formalization_bridge_nodes",
                goal_conditioned_minimal_formalization_plan_payload.get("n_bridge_nodes"),
            ),
            "goal_conditioned_minimal_formalization_source_discovery_nodes": counts.get(
                "goal_conditioned_minimal_formalization_source_discovery_nodes",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_source_discovery_nodes"
                ),
            ),
            "goal_conditioned_minimal_formalization_first_principles_nodes": counts.get(
                "goal_conditioned_minimal_formalization_first_principles_nodes",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_first_principles_nodes"
                ),
            ),
            "goal_conditioned_minimal_formalization_minimal_additional_nodes": counts.get(
                "goal_conditioned_minimal_formalization_minimal_additional_nodes",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_minimal_additional_formalization_nodes"
                ),
            ),
            "goal_conditioned_minimal_formalization_minimal_cuts": counts.get(
                "goal_conditioned_minimal_formalization_minimal_cuts",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_goal_plans_with_minimal_cut"
                ),
            ),
            "goal_conditioned_minimal_formalization_cost_terms": counts.get(
                "goal_conditioned_minimal_formalization_cost_terms",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_route_cost_breakdown_terms"
                ),
            ),
            "goal_conditioned_minimal_formalization_and_or_nodes": counts.get(
                "goal_conditioned_minimal_formalization_and_or_nodes",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_and_or_plan_nodes"
                ),
            ),
            "goal_conditioned_minimal_formalization_and_or_edges": counts.get(
                "goal_conditioned_minimal_formalization_and_or_edges",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_and_or_plan_edges"
                ),
            ),
            "goal_conditioned_minimal_formalization_route_revision_triggers": counts.get(
                "goal_conditioned_minimal_formalization_route_revision_triggers",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_route_revision_triggers"
                ),
            ),
            "goal_conditioned_minimal_formalization_portable_work_packets": counts.get(
                "goal_conditioned_minimal_formalization_portable_work_packets",
                goal_conditioned_minimal_formalization_plan_payload.get(
                    "n_portable_work_packets"
                ),
            ),
            "goal_conditioned_minimal_formalization_manifest": str(
                goal_conditioned_minimal_formalization_plan_path
            ),
            "goal_conditioned_minimal_formalization_plan_preview": _goal_conditioned_minimal_formalization_plan_preview(
                goal_conditioned_minimal_formalization_plan_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_tasks": counts.get(
                "formal_verifier_replay_tasks",
                formal_verifier_replay_payload.get("n_replay_tasks"),
            ),
            "formal_verifier_replay_kernel_calibrated": counts.get(
                "formal_verifier_replay_kernel_calibrated",
                formal_verifier_replay_payload.get("n_kernel_calibrated"),
            ),
            "formal_verifier_replay_proof_search_subclaim": counts.get(
                "formal_verifier_replay_proof_search_subclaim",
                formal_verifier_replay_payload.get("n_proof_search_subclaim_replay"),
            ),
            "formal_verifier_replay_bridge_lemma": counts.get(
                "formal_verifier_replay_bridge_lemma",
                formal_verifier_replay_payload.get("n_bridge_lemma_replay"),
            ),
            "formal_verifier_replay_semantic_review": counts.get(
                "formal_verifier_replay_semantic_review",
                formal_verifier_replay_payload.get("n_semantic_review"),
            ),
            "formal_verifier_replay_training_examples": counts.get(
                "formal_verifier_replay_training_examples",
                formal_verifier_replay_payload.get("n_training_examples"),
            ),
            "formal_verifier_replay_manifest": str(formal_verifier_replay_path),
            "formal_verifier_replay_preview": _formal_verifier_replay_preview(
                formal_verifier_replay_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_attempts": counts.get(
                "formal_verifier_replay_attempts",
                formal_verifier_replay_attempt_payload.get("n_attempted"),
            ),
            "formal_verifier_replay_attempt_positive": counts.get(
                "formal_verifier_replay_attempt_positive",
                formal_verifier_replay_attempt_payload.get("n_positive"),
            ),
            "formal_verifier_replay_attempt_negative": counts.get(
                "formal_verifier_replay_attempt_negative",
                formal_verifier_replay_attempt_payload.get("n_negative"),
            ),
            "formal_verifier_replay_attempt_kernel_verified": counts.get(
                "formal_verifier_replay_attempt_kernel_verified",
                formal_verifier_replay_attempt_payload.get("n_kernel_verified"),
            ),
            "formal_verifier_replay_attempts_manifest": str(formal_verifier_replay_attempt_path),
            "formal_verifier_replay_attempted": counts.get(
                "formal_verifier_replay_attempted",
                formal_verifier_replay_calibration_payload.get("n_attempted_replay_tasks"),
            ),
            "formal_verifier_replay_awaiting_full_route_attempt": counts.get(
                "formal_verifier_replay_awaiting_full_route_attempt",
                formal_verifier_replay_calibration_payload.get("n_awaiting_full_route_attempt"),
            ),
            "formal_verifier_replay_failed_full_route_attempt": counts.get(
                "formal_verifier_replay_failed_full_route_attempt",
                formal_verifier_replay_calibration_payload.get("n_failed_full_route_attempt"),
            ),
            "formal_verifier_replay_non_kernel_positive": counts.get(
                "formal_verifier_replay_non_kernel_positive",
                formal_verifier_replay_calibration_payload.get("n_non_kernel_positive"),
            ),
            "formal_verifier_replay_full_route_kernel_verified": counts.get(
                "formal_verifier_replay_full_route_kernel_verified",
                formal_verifier_replay_calibration_payload.get("n_kernel_verified"),
            ),
            "formal_verifier_replay_calibration_manifest": str(
                formal_verifier_replay_calibration_path
            ),
            "formal_verifier_replay_calibration_preview": _formal_verifier_replay_calibration_preview(
                formal_verifier_replay_calibration_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_packets": counts.get(
                "formal_verifier_replay_repair_packets",
                formal_verifier_replay_repair_payload.get("n_repair_packets"),
            ),
            "formal_verifier_replay_repair_ok": counts.get(
                "formal_verifier_replay_repair_ok",
                formal_verifier_replay_repair_payload.get("n_ok"),
            ),
            "formal_verifier_replay_repair_tactic_no_progress": counts.get(
                "formal_verifier_replay_repair_tactic_no_progress",
                formal_verifier_replay_repair_payload.get("n_tactic_no_progress"),
            ),
            "formal_verifier_replay_repair_missing_identifier": counts.get(
                "formal_verifier_replay_repair_missing_identifier",
                formal_verifier_replay_repair_payload.get("n_missing_identifier"),
            ),
            "formal_verifier_replay_repair_with_exact_subclaims": counts.get(
                "formal_verifier_replay_repair_with_exact_subclaims",
                formal_verifier_replay_repair_payload.get("n_with_exact_subclaims"),
            ),
            "formal_verifier_replay_repair_training_examples": counts.get(
                "formal_verifier_replay_repair_training_examples",
                formal_verifier_replay_repair_payload.get("n_training_examples"),
            ),
            "formal_verifier_replay_repair_manifest": str(formal_verifier_replay_repair_path),
            "formal_verifier_replay_repair_preview": _formal_verifier_replay_repair_preview(
                formal_verifier_replay_repair_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_application_tasks": counts.get(
                "formal_verifier_replay_repair_application_tasks",
                formal_verifier_replay_repair_application_payload.get("n_application_tasks"),
            ),
            "formal_verifier_replay_repair_application_ok": counts.get(
                "formal_verifier_replay_repair_application_ok",
                formal_verifier_replay_repair_application_payload.get("n_ok"),
            ),
            "formal_verifier_replay_repair_application_bridge_lemma": counts.get(
                "formal_verifier_replay_repair_application_bridge_lemma",
                formal_verifier_replay_repair_application_payload.get("n_bridge_lemma_applications"),
            ),
            "formal_verifier_replay_repair_application_import_or_declaration": counts.get(
                "formal_verifier_replay_repair_application_import_or_declaration",
                formal_verifier_replay_repair_application_payload.get(
                    "n_import_or_declaration_applications"
                ),
            ),
            "formal_verifier_replay_repair_application_manifest": str(
                formal_verifier_replay_repair_application_path
            ),
            "formal_verifier_replay_repair_application_preview": _formal_verifier_replay_repair_application_preview(
                formal_verifier_replay_repair_application_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_application_validation_rows": counts.get(
                "formal_verifier_replay_repair_application_validation_rows",
                formal_verifier_replay_repair_application_validation_payload.get("n_validation_rows"),
            ),
            "formal_verifier_replay_repair_application_validation_ok": counts.get(
                "formal_verifier_replay_repair_application_validation_ok",
                formal_verifier_replay_repair_application_validation_payload.get("n_ok"),
            ),
            "formal_verifier_replay_repair_application_validation_static_ok": counts.get(
                "formal_verifier_replay_repair_application_validation_static_ok",
                formal_verifier_replay_repair_application_validation_payload.get("n_static_ok"),
            ),
            "formal_verifier_replay_repair_application_validation_local_lean_checked": counts.get(
                "formal_verifier_replay_repair_application_validation_local_lean_checked",
                formal_verifier_replay_repair_application_validation_payload.get("n_local_lean_checked"),
            ),
            "formal_verifier_replay_repair_application_validation_local_lean_compiled": counts.get(
                "formal_verifier_replay_repair_application_validation_local_lean_compiled",
                formal_verifier_replay_repair_application_validation_payload.get("n_local_lean_compiled"),
            ),
            "formal_verifier_replay_repair_application_validation_manifest": str(
                formal_verifier_replay_repair_application_validation_path
            ),
            "formal_verifier_replay_repair_application_validation_preview": _formal_verifier_replay_repair_application_validation_preview(
                formal_verifier_replay_repair_application_validation_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_execution_queue_items": counts.get(
                "formal_verifier_replay_repair_execution_queue_items",
                formal_verifier_replay_repair_execution_queue_payload.get("n_queue_items"),
            ),
            "formal_verifier_replay_repair_execution_queue_ready": counts.get(
                "formal_verifier_replay_repair_execution_queue_ready",
                formal_verifier_replay_repair_execution_queue_payload.get("n_ready_for_patch"),
            ),
            "formal_verifier_replay_repair_execution_queue_ready_local_lean": counts.get(
                "formal_verifier_replay_repair_execution_queue_ready_local_lean",
                formal_verifier_replay_repair_execution_queue_payload.get(
                    "n_ready_local_lean_compiled"
                ),
            ),
            "formal_verifier_replay_repair_execution_queue_blocked": counts.get(
                "formal_verifier_replay_repair_execution_queue_blocked",
                formal_verifier_replay_repair_execution_queue_payload.get("n_blocked"),
            ),
            "formal_verifier_replay_repair_execution_queue_manifest": str(
                formal_verifier_replay_repair_execution_queue_path
            ),
            "formal_verifier_replay_repair_execution_queue_preview": _formal_verifier_replay_repair_execution_queue_preview(
                formal_verifier_replay_repair_execution_queue_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_prompt_packets": counts.get(
                "formal_verifier_replay_repair_prompt_packets",
                formal_verifier_replay_repair_prompt_packets_payload.get("n_prompt_packets"),
            ),
            "formal_verifier_replay_repair_prompt_packets_ok": counts.get(
                "formal_verifier_replay_repair_prompt_packets_ok",
                formal_verifier_replay_repair_prompt_packets_payload.get("n_ok"),
            ),
            "formal_verifier_replay_repair_prompt_packets_with_scaffold_source": counts.get(
                "formal_verifier_replay_repair_prompt_packets_with_scaffold_source",
                formal_verifier_replay_repair_prompt_packets_payload.get("n_with_scaffold_source"),
            ),
            "formal_verifier_replay_repair_prompt_packets_with_command_plan": counts.get(
                "formal_verifier_replay_repair_prompt_packets_with_command_plan",
                formal_verifier_replay_repair_prompt_packets_payload.get("n_with_command_plan"),
            ),
            "formal_verifier_replay_repair_prompt_packets_manifest": str(
                formal_verifier_replay_repair_prompt_packets_path
            ),
            "formal_verifier_replay_repair_prompt_packets_preview": _formal_verifier_replay_repair_prompt_packets_preview(
                formal_verifier_replay_repair_prompt_packets_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_autoworker_responses": counts.get(
                "formal_verifier_replay_repair_patch_autoworker_responses",
                formal_verifier_replay_repair_patch_autoworker_payload.get("n_responses"),
            ),
            "formal_verifier_replay_repair_patch_autoworker_patch_proposals": counts.get(
                "formal_verifier_replay_repair_patch_autoworker_patch_proposals",
                formal_verifier_replay_repair_patch_autoworker_payload.get("n_patch_proposals"),
            ),
            "formal_verifier_replay_repair_patch_autoworker_kernel_verified": counts.get(
                "formal_verifier_replay_repair_patch_autoworker_kernel_verified",
                formal_verifier_replay_repair_patch_autoworker_payload.get("n_kernel_verified"),
            ),
            "formal_verifier_replay_repair_patch_autoworker_artifacts": counts.get(
                "formal_verifier_replay_repair_patch_autoworker_artifacts",
                formal_verifier_replay_repair_patch_autoworker_payload.get("n_patch_artifacts"),
            ),
            "formal_verifier_replay_repair_patch_autoworker_manifest": str(
                formal_verifier_replay_repair_patch_autoworker_path
            ),
            "formal_verifier_replay_repair_patch_response_validation_rows": counts.get(
                "formal_verifier_replay_repair_patch_response_validation_rows",
                formal_verifier_replay_repair_patch_response_validation_payload.get(
                    "n_response_validation_rows"
                ),
            ),
            "formal_verifier_replay_repair_patch_response_validation_responses": counts.get(
                "formal_verifier_replay_repair_patch_response_validation_responses",
                formal_verifier_replay_repair_patch_response_validation_payload.get(
                    "n_response_present"
                ),
            ),
            "formal_verifier_replay_repair_patch_response_validation_awaiting": counts.get(
                "formal_verifier_replay_repair_patch_response_validation_awaiting",
                formal_verifier_replay_repair_patch_response_validation_payload.get(
                    "n_awaiting_worker_response"
                ),
            ),
            "formal_verifier_replay_repair_patch_response_validation_contract_ok": counts.get(
                "formal_verifier_replay_repair_patch_response_validation_contract_ok",
                formal_verifier_replay_repair_patch_response_validation_payload.get("n_contract_ok"),
            ),
            "formal_verifier_replay_repair_patch_response_validation_patch_proposal_not_proof": counts.get(
                "formal_verifier_replay_repair_patch_response_validation_patch_proposal_not_proof",
                formal_verifier_replay_repair_patch_response_validation_payload.get(
                    "n_patch_proposal_not_proof"
                ),
            ),
            "formal_verifier_replay_repair_patch_response_validation_accepted_full_route_kernel_verified": counts.get(
                "formal_verifier_replay_repair_patch_response_validation_accepted_full_route_kernel_verified",
                formal_verifier_replay_repair_patch_response_validation_payload.get(
                    "n_accepted_full_route_kernel_verified"
                ),
            ),
            "formal_verifier_replay_repair_patch_response_validation_rejected": counts.get(
                "formal_verifier_replay_repair_patch_response_validation_rejected",
                formal_verifier_replay_repair_patch_response_validation_payload.get("n_rejected"),
            ),
            "formal_verifier_replay_repair_patch_response_validation_manifest": str(
                formal_verifier_replay_repair_patch_response_validation_path
            ),
            "formal_verifier_replay_repair_patch_response_validation_preview": _formal_verifier_replay_repair_patch_response_validation_preview(
                formal_verifier_replay_repair_patch_response_validation_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_response_promotion_rows": counts.get(
                "formal_verifier_replay_repair_patch_response_promotion_rows",
                formal_verifier_replay_repair_patch_response_promotion_payload.get(
                    "n_promotion_rows"
                ),
            ),
            "formal_verifier_replay_repair_patch_response_promotion_ready": counts.get(
                "formal_verifier_replay_repair_patch_response_promotion_ready",
                formal_verifier_replay_repair_patch_response_promotion_payload.get(
                    "n_ready_for_proof_promotion"
                ),
            ),
            "formal_verifier_replay_repair_patch_response_promotion_awaiting": counts.get(
                "formal_verifier_replay_repair_patch_response_promotion_awaiting",
                formal_verifier_replay_repair_patch_response_promotion_payload.get(
                    "n_awaiting_worker_response"
                ),
            ),
            "formal_verifier_replay_repair_patch_response_promotion_patch_needs_replay": counts.get(
                "formal_verifier_replay_repair_patch_response_promotion_patch_needs_replay",
                formal_verifier_replay_repair_patch_response_promotion_payload.get(
                    "n_patch_proposal_needs_replay_calibration"
                ),
            ),
            "formal_verifier_replay_repair_patch_response_promotion_blocked": counts.get(
                "formal_verifier_replay_repair_patch_response_promotion_blocked",
                formal_verifier_replay_repair_patch_response_promotion_payload.get("n_blocked"),
            ),
            "formal_verifier_replay_repair_patch_response_promotion_manifest": str(
                formal_verifier_replay_repair_patch_response_promotion_path
            ),
            "formal_verifier_replay_repair_patch_response_promotion_preview": _formal_verifier_replay_repair_patch_response_promotion_preview(
                formal_verifier_replay_repair_patch_response_promotion_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_rerun_queue_items": counts.get(
                "formal_verifier_replay_repair_patch_rerun_queue_items",
                formal_verifier_replay_repair_patch_rerun_queue_payload.get(
                    "n_rerun_queue_items"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_queue_ready": counts.get(
                "formal_verifier_replay_repair_patch_rerun_queue_ready",
                formal_verifier_replay_repair_patch_rerun_queue_payload.get(
                    "n_ready_for_patch_replay"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_queue_blocked": counts.get(
                "formal_verifier_replay_repair_patch_rerun_queue_blocked",
                formal_verifier_replay_repair_patch_rerun_queue_payload.get("n_blocked"),
            ),
            "formal_verifier_replay_repair_patch_rerun_queue_manifest": str(
                formal_verifier_replay_repair_patch_rerun_queue_path
            ),
            "formal_verifier_replay_repair_patch_rerun_queue_preview": _formal_verifier_replay_repair_patch_rerun_queue_preview(
                formal_verifier_replay_repair_patch_rerun_queue_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_rerun_attempts": counts.get(
                "formal_verifier_replay_repair_patch_rerun_attempts",
                formal_verifier_replay_repair_patch_rerun_attempt_payload.get(
                    "n_rerun_attempt_rows"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_attempts_local_lean_compiled": counts.get(
                "formal_verifier_replay_repair_patch_rerun_attempts_local_lean_compiled",
                formal_verifier_replay_repair_patch_rerun_attempt_payload.get(
                    "n_local_lean_compiled"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_attempts_patch_markers": counts.get(
                "formal_verifier_replay_repair_patch_rerun_attempts_patch_markers",
                formal_verifier_replay_repair_patch_rerun_attempt_payload.get(
                    "n_with_patch_proposal_marker"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_attempts_manifest": str(
                formal_verifier_replay_repair_patch_rerun_attempt_path
            ),
            "formal_verifier_replay_repair_patch_rerun_attempts_preview": _formal_verifier_replay_repair_patch_rerun_attempt_preview(
                formal_verifier_replay_repair_patch_rerun_attempt_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_rerun_calibration_rows": counts.get(
                "formal_verifier_replay_repair_patch_rerun_calibration_rows",
                formal_verifier_replay_repair_patch_rerun_calibration_payload.get(
                    "n_calibration_rows"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_calibration_full_route_kernel_verified": counts.get(
                "formal_verifier_replay_repair_patch_rerun_calibration_full_route_kernel_verified",
                formal_verifier_replay_repair_patch_rerun_calibration_payload.get(
                    "n_full_route_kernel_verified"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_calibration_compiled_patch_proposal_not_proof": counts.get(
                "formal_verifier_replay_repair_patch_rerun_calibration_compiled_patch_proposal_not_proof",
                formal_verifier_replay_repair_patch_rerun_calibration_payload.get(
                    "n_compiled_patch_proposal_not_proof"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_calibration_manifest": str(
                formal_verifier_replay_repair_patch_rerun_calibration_path
            ),
            "formal_verifier_replay_repair_patch_rerun_calibration_preview": _formal_verifier_replay_repair_patch_rerun_calibration_preview(
                formal_verifier_replay_repair_patch_rerun_calibration_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_obligations": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_obligations",
                formal_verifier_replay_repair_patch_rerun_residual_obligation_payload.get(
                    "n_residual_obligation_rows"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_exact_reuse": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_obligations_exact_reuse",
                formal_verifier_replay_repair_patch_rerun_residual_obligation_payload.get(
                    "n_exact_proof_bank_reuse"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_bridge_chain": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_obligations_bridge_chain",
                formal_verifier_replay_repair_patch_rerun_residual_obligation_payload.get(
                    "n_compose_existing_bridge_chain"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_source_discovery": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_obligations_source_discovery",
                formal_verifier_replay_repair_patch_rerun_residual_obligation_payload.get(
                    "n_source_discovery_needed"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_manifest": str(
                formal_verifier_replay_repair_patch_rerun_residual_obligation_path
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_obligations_preview": _formal_verifier_replay_repair_patch_rerun_residual_obligation_preview(
                formal_verifier_replay_repair_patch_rerun_residual_obligation_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets",
                formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_payload.get(
                    "n_prompt_packets"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_ok": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_ok",
                formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_payload.get(
                    "n_ok"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_with_artifact_context": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_with_artifact_context",
                formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_payload.get(
                    "n_with_patched_artifact_context"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_with_output_contract": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_with_output_contract",
                formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_payload.get(
                    "n_with_output_contract"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_exact_reuse": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_exact_reuse",
                formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_payload.get(
                    "n_exact_reuse_packets"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_bridge_chain": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_bridge_chain",
                formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_payload.get(
                    "n_bridge_chain_packets"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_source_discovery": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_source_discovery",
                formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_payload.get(
                    "n_source_discovery_packets"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest": str(
                formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_path
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_preview": _formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_preview(
                formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_responses": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_autoworker_responses",
                formal_verifier_replay_repair_patch_rerun_residual_autoworker_payload.get(
                    "n_responses"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_patch_proposals": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_autoworker_patch_proposals",
                formal_verifier_replay_repair_patch_rerun_residual_autoworker_payload.get(
                    "n_residual_patch_proposals"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_source_discovery": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_autoworker_source_discovery",
                formal_verifier_replay_repair_patch_rerun_residual_autoworker_payload.get(
                    "n_source_discovery_responses"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_kernel_verified": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_autoworker_kernel_verified",
                formal_verifier_replay_repair_patch_rerun_residual_autoworker_payload.get(
                    "n_kernel_verified"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_artifacts": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_autoworker_artifacts",
                formal_verifier_replay_repair_patch_rerun_residual_autoworker_payload.get(
                    "n_patch_artifacts"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest": str(
                formal_verifier_replay_repair_patch_rerun_residual_autoworker_path
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker_preview": _formal_verifier_replay_repair_patch_rerun_residual_autoworker_preview(
                formal_verifier_replay_repair_patch_rerun_residual_autoworker_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_rows": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_response_validation_rows",
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload.get(
                    "n_response_validation_rows"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_responses": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_response_validation_responses",
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload.get(
                    "n_response_present"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_awaiting": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_response_validation_awaiting",
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload.get(
                    "n_awaiting_worker_response"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_contract_ok": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_response_validation_contract_ok",
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload.get(
                    "n_contract_ok"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_patch_proposal_not_proof": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_response_validation_patch_proposal_not_proof",
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload.get(
                    "n_residual_patch_proposal_not_proof"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_source_discovery": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_response_validation_source_discovery",
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload.get(
                    "n_source_discovery_responses"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_accepted_full_route_kernel_verified": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_response_validation_accepted_full_route_kernel_verified",
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload.get(
                    "n_accepted_full_route_kernel_verified"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_rejected": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_response_validation_rejected",
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload.get(
                    "n_rejected"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest": str(
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_path
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_response_validation_preview": _formal_verifier_replay_repair_patch_rerun_residual_response_validation_preview(
                formal_verifier_replay_repair_patch_rerun_residual_response_validation_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_items": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_items",
                formal_verifier_replay_repair_patch_rerun_residual_followup_queue_payload.get(
                    "n_followup_items"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_ready": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_ready",
                formal_verifier_replay_repair_patch_rerun_residual_followup_queue_payload.get(
                    "n_ready"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_blocked": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_blocked",
                formal_verifier_replay_repair_patch_rerun_residual_followup_queue_payload.get(
                    "n_blocked"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_patch_rerun": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_patch_rerun",
                formal_verifier_replay_repair_patch_rerun_residual_followup_queue_payload.get(
                    "n_patch_rerun_items"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_source_discovery": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_source_discovery",
                formal_verifier_replay_repair_patch_rerun_residual_followup_queue_payload.get(
                    "n_source_discovery_items"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_with_artifact": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_with_artifact",
                formal_verifier_replay_repair_patch_rerun_residual_followup_queue_payload.get(
                    "n_with_artifact"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_with_source_queries": counts.get(
                "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_with_source_queries",
                formal_verifier_replay_repair_patch_rerun_residual_followup_queue_payload.get(
                    "n_with_source_queries"
                ),
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest": str(
                formal_verifier_replay_repair_patch_rerun_residual_followup_queue_path
            ),
            "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_preview": _formal_verifier_replay_repair_patch_rerun_residual_followup_queue_preview(
                formal_verifier_replay_repair_patch_rerun_residual_followup_queue_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_strategy_plan_rows": counts.get(
                "formal_verifier_agentic_proof_strategy_plan_rows",
                formal_verifier_agentic_proof_strategy_plan_payload.get(
                    "n_strategy_rows"
                ),
            ),
            "formal_verifier_agentic_proof_strategy_plan_ready": counts.get(
                "formal_verifier_agentic_proof_strategy_plan_ready",
                formal_verifier_agentic_proof_strategy_plan_payload.get("n_ready"),
            ),
            "formal_verifier_agentic_proof_strategy_plan_patch_evolve_blocks": counts.get(
                "formal_verifier_agentic_proof_strategy_plan_patch_evolve_blocks",
                formal_verifier_agentic_proof_strategy_plan_payload.get(
                    "n_patch_evolve_blocks"
                ),
            ),
            "formal_verifier_agentic_proof_strategy_plan_source_discovery_cache_items": counts.get(
                "formal_verifier_agentic_proof_strategy_plan_source_discovery_cache_items",
                formal_verifier_agentic_proof_strategy_plan_payload.get(
                    "n_source_discovery_cache_items"
                ),
            ),
            "formal_verifier_agentic_proof_strategy_plan_kernel_overlay_composition_seeds": counts.get(
                "formal_verifier_agentic_proof_strategy_plan_kernel_overlay_composition_seeds",
                formal_verifier_agentic_proof_strategy_plan_payload.get(
                    "n_kernel_overlay_composition_seeds",
                    0,
                ),
            ),
            "formal_verifier_agentic_proof_strategy_plan_manifest": str(
                formal_verifier_agentic_proof_strategy_plan_path
            ),
            "formal_verifier_agentic_proof_strategy_plan_preview": _formal_verifier_agentic_proof_strategy_plan_preview(
                formal_verifier_agentic_proof_strategy_plan_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_items": counts.get(
                "formal_verifier_agentic_proof_candidate_evaluation_queue_items",
                formal_verifier_agentic_proof_candidate_evaluation_queue_payload.get(
                    "n_candidate_queue_items"
                ),
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_ready": counts.get(
                "formal_verifier_agentic_proof_candidate_evaluation_queue_ready",
                formal_verifier_agentic_proof_candidate_evaluation_queue_payload.get(
                    "n_ready"
                ),
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_blocked": counts.get(
                "formal_verifier_agentic_proof_candidate_evaluation_queue_blocked",
                formal_verifier_agentic_proof_candidate_evaluation_queue_payload.get(
                    "n_blocked"
                ),
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_patch_candidates": counts.get(
                "formal_verifier_agentic_proof_candidate_evaluation_queue_patch_candidates",
                formal_verifier_agentic_proof_candidate_evaluation_queue_payload.get(
                    "n_patch_candidate_items"
                ),
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_source_discovery_candidates": counts.get(
                "formal_verifier_agentic_proof_candidate_evaluation_queue_source_discovery_candidates",
                formal_verifier_agentic_proof_candidate_evaluation_queue_payload.get(
                    "n_source_discovery_candidate_items"
                ),
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_kernel_overlay_candidates": counts.get(
                "formal_verifier_agentic_proof_candidate_evaluation_queue_kernel_overlay_candidates",
                formal_verifier_agentic_proof_candidate_evaluation_queue_payload.get(
                    "n_kernel_overlay_candidate_items",
                    0,
                ),
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_with_kernel_overlay_context": counts.get(
                "formal_verifier_agentic_proof_candidate_evaluation_queue_with_kernel_overlay_context",
                formal_verifier_agentic_proof_candidate_evaluation_queue_payload.get(
                    "n_with_kernel_overlay_context",
                    0,
                ),
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_manifest": str(
                formal_verifier_agentic_proof_candidate_evaluation_queue_path
            ),
            "formal_verifier_agentic_proof_candidate_evaluation_queue_preview": _formal_verifier_agentic_proof_candidate_evaluation_queue_preview(
                formal_verifier_agentic_proof_candidate_evaluation_queue_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_safety_policy_rows": counts.get(
                "formal_verifier_agentic_proof_safety_policy_rows",
                formal_verifier_agentic_proof_safety_policy_payload.get(
                    "n_safety_policy_rows"
                ),
            ),
            "formal_verifier_agentic_proof_safety_policy_ready": counts.get(
                "formal_verifier_agentic_proof_safety_policy_ready",
                formal_verifier_agentic_proof_safety_policy_payload.get("n_ready"),
            ),
            "formal_verifier_agentic_proof_safety_policy_blocked": counts.get(
                "formal_verifier_agentic_proof_safety_policy_blocked",
                formal_verifier_agentic_proof_safety_policy_payload.get("n_blocked"),
            ),
            "formal_verifier_agentic_proof_safety_policy_patch_bounded_edit": counts.get(
                "formal_verifier_agentic_proof_safety_policy_patch_bounded_edit",
                formal_verifier_agentic_proof_safety_policy_payload.get(
                    "n_patch_bounded_edit_policies"
                ),
            ),
            "formal_verifier_agentic_proof_safety_policy_source_validation": counts.get(
                "formal_verifier_agentic_proof_safety_policy_source_validation",
                formal_verifier_agentic_proof_safety_policy_payload.get(
                    "n_source_validation_policies"
                ),
            ),
            "formal_verifier_agentic_proof_safety_policy_with_kernel_overlay_context": counts.get(
                "formal_verifier_agentic_proof_safety_policy_with_kernel_overlay_context",
                formal_verifier_agentic_proof_safety_policy_payload.get(
                    "n_with_kernel_overlay_context",
                    0,
                ),
            ),
            "formal_verifier_agentic_proof_safety_policy_manifest": str(
                formal_verifier_agentic_proof_safety_policy_path
            ),
            "formal_verifier_agentic_proof_safety_policy_preview": _formal_verifier_agentic_proof_safety_policy_preview(
                formal_verifier_agentic_proof_safety_policy_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_attempt_population_entries": counts.get(
                "formal_verifier_agentic_proof_attempt_population_entries",
                formal_verifier_agentic_proof_attempt_population_payload.get(
                    "n_population_entries"
                ),
            ),
            "formal_verifier_agentic_proof_attempt_population_ready": counts.get(
                "formal_verifier_agentic_proof_attempt_population_ready",
                formal_verifier_agentic_proof_attempt_population_payload.get("n_ready"),
            ),
            "formal_verifier_agentic_proof_attempt_population_blocked": counts.get(
                "formal_verifier_agentic_proof_attempt_population_blocked",
                formal_verifier_agentic_proof_attempt_population_payload.get("n_blocked"),
            ),
            "formal_verifier_agentic_proof_attempt_population_patch_entries": counts.get(
                "formal_verifier_agentic_proof_attempt_population_patch_entries",
                formal_verifier_agentic_proof_attempt_population_payload.get(
                    "n_patch_population_entries"
                ),
            ),
            "formal_verifier_agentic_proof_attempt_population_source_entries": counts.get(
                "formal_verifier_agentic_proof_attempt_population_source_entries",
                formal_verifier_agentic_proof_attempt_population_payload.get(
                    "n_source_population_entries"
                ),
            ),
            "formal_verifier_agentic_proof_attempt_population_with_kernel_overlay_context": counts.get(
                "formal_verifier_agentic_proof_attempt_population_with_kernel_overlay_context",
                formal_verifier_agentic_proof_attempt_population_payload.get(
                    "n_with_kernel_overlay_context",
                    0,
                ),
            ),
            "formal_verifier_agentic_proof_attempt_population_manifest": str(
                formal_verifier_agentic_proof_attempt_population_path
            ),
            "formal_verifier_agentic_proof_attempt_population_preview": _formal_verifier_agentic_proof_attempt_population_preview(
                formal_verifier_agentic_proof_attempt_population_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_execution_queue_items": counts.get(
                "formal_verifier_agentic_proof_execution_queue_items",
                formal_verifier_agentic_proof_execution_queue_payload.get(
                    "n_execution_queue_items"
                ),
            ),
            "formal_verifier_agentic_proof_execution_queue_ready": counts.get(
                "formal_verifier_agentic_proof_execution_queue_ready",
                formal_verifier_agentic_proof_execution_queue_payload.get("n_ready"),
            ),
            "formal_verifier_agentic_proof_execution_queue_blocked": counts.get(
                "formal_verifier_agentic_proof_execution_queue_blocked",
                formal_verifier_agentic_proof_execution_queue_payload.get(
                    "n_blocked"
                ),
            ),
            "formal_verifier_agentic_proof_execution_queue_patch_items": counts.get(
                "formal_verifier_agentic_proof_execution_queue_patch_items",
                formal_verifier_agentic_proof_execution_queue_payload.get(
                    "n_patch_execution_items"
                ),
            ),
            "formal_verifier_agentic_proof_execution_queue_source_items": counts.get(
                "formal_verifier_agentic_proof_execution_queue_source_items",
                formal_verifier_agentic_proof_execution_queue_payload.get(
                    "n_source_execution_items"
                ),
            ),
            "formal_verifier_agentic_proof_execution_queue_with_proof_route_dag_plan": counts.get(
                "formal_verifier_agentic_proof_execution_queue_with_proof_route_dag_plan",
                formal_verifier_agentic_proof_execution_queue_payload.get(
                    "n_with_proof_route_dag_plan",
                    0,
                ),
            ),
            "formal_verifier_agentic_proof_execution_queue_with_verified_sketch_gate": counts.get(
                "formal_verifier_agentic_proof_execution_queue_with_verified_sketch_gate",
                formal_verifier_agentic_proof_execution_queue_payload.get(
                    "n_with_verified_sketch_gate",
                    0,
                ),
            ),
            "formal_verifier_agentic_proof_execution_queue_with_blueprint_export_plan": counts.get(
                "formal_verifier_agentic_proof_execution_queue_with_blueprint_export_plan",
                formal_verifier_agentic_proof_execution_queue_payload.get(
                    "n_with_blueprint_export_plan",
                    0,
                ),
            ),
            "formal_verifier_agentic_proof_execution_queue_with_kernel_overlay_context": counts.get(
                "formal_verifier_agentic_proof_execution_queue_with_kernel_overlay_context",
                formal_verifier_agentic_proof_execution_queue_payload.get(
                    "n_with_kernel_overlay_context",
                    0,
                ),
            ),
            "formal_verifier_agentic_proof_execution_queue_manifest": str(
                formal_verifier_agentic_proof_execution_queue_path
            ),
            "formal_verifier_agentic_proof_execution_queue_preview": _formal_verifier_agentic_proof_execution_queue_preview(
                formal_verifier_agentic_proof_execution_queue_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_execution_materializer_rows": counts.get(
                "formal_verifier_agentic_proof_execution_materializer_rows",
                formal_verifier_agentic_proof_execution_materializer_payload.get(
                    "n_materializer_rows"
                ),
            ),
            "formal_verifier_agentic_proof_execution_materializer_artifacts": counts.get(
                "formal_verifier_agentic_proof_execution_materializer_artifacts",
                formal_verifier_agentic_proof_execution_materializer_payload.get(
                    "n_materialized_artifacts"
                ),
            ),
            "formal_verifier_agentic_proof_execution_materializer_live_goal_location_ready": counts.get(
                "formal_verifier_agentic_proof_execution_materializer_live_goal_location_ready",
                formal_verifier_agentic_proof_execution_materializer_payload.get(
                    "n_live_goal_location_ready"
                ),
            ),
            "formal_verifier_agentic_proof_execution_materializer_live_proof_state_requests": counts.get(
                "formal_verifier_agentic_proof_execution_materializer_live_proof_state_requests",
                formal_verifier_agentic_proof_execution_materializer_payload.get(
                    "n_live_proof_state_requests"
                ),
            ),
            "formal_verifier_agentic_proof_execution_materializer_lean_lsp_mcp_ready_requests": counts.get(
                "formal_verifier_agentic_proof_execution_materializer_lean_lsp_mcp_ready_requests",
                formal_verifier_agentic_proof_execution_materializer_payload.get(
                    "n_lean_lsp_mcp_ready_requests"
                ),
            ),
            "formal_verifier_agentic_proof_execution_materializer_kernel_verified": counts.get(
                "formal_verifier_agentic_proof_execution_materializer_kernel_verified",
                formal_verifier_agentic_proof_execution_materializer_payload.get(
                    "n_kernel_verified"
                ),
            ),
            "formal_verifier_agentic_proof_execution_materializer_manifest": str(
                formal_verifier_agentic_proof_execution_materializer_path
            ),
            "formal_verifier_agentic_proof_execution_materializer_preview": _formal_verifier_agentic_proof_execution_materializer_preview(
                formal_verifier_agentic_proof_execution_materializer_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_execution_artifact_verifier_enabled": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_verifier_enabled",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "enabled"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_verifier_checked": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_verifier_checked",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_local_lean_checked"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_verifier_compiled": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_verifier_compiled",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_local_lean_compiled"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_kernel_verified": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_kernel_verified",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_artifact_kernel_verified"
                ),
            ),
            "formal_verifier_agentic_proof_execution_source_theorem_kernel_verified": counts.get(
                "formal_verifier_agentic_proof_execution_source_theorem_kernel_verified",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_source_theorem_kernel_verified"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_transcript_paths": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_transcript_paths",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_execution_transcript_paths"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_transcript_events_written": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_transcript_events_written",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_execution_transcript_events_written"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_live_proof_state_requests": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_live_proof_state_requests",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_live_proof_state_requests"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_live_proof_state_request_valid": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_live_proof_state_request_valid",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_live_proof_state_request_valid"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_lean_lsp_mcp_ready_requests": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_lean_lsp_mcp_ready_requests",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_lean_lsp_mcp_ready_requests"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_live_proof_state_request_failures": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_live_proof_state_request_failures",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "n_live_proof_state_request_failures"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_proof_evidence_status": counts.get(
                "formal_verifier_agentic_proof_execution_artifact_proof_evidence_status",
                formal_verifier_agentic_proof_execution_artifact_verifier_payload.get(
                    "proof_evidence_status"
                ),
            ),
            "formal_verifier_agentic_proof_execution_artifact_verifier_manifest": str(
                formal_verifier_agentic_proof_execution_artifact_verifier_path
            ),
            "formal_verifier_agentic_proof_execution_artifact_verifier_preview": _formal_verifier_agentic_proof_execution_artifact_verifier_preview(
                formal_verifier_agentic_proof_execution_artifact_verifier_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_trace_memory_rows": counts.get(
                "formal_verifier_agentic_proof_trace_memory_rows",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "n_trace_memory_rows"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_transcript_events": counts.get(
                "formal_verifier_agentic_proof_trace_memory_transcript_events",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "n_transcript_events"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_verifier_events": counts.get(
                "formal_verifier_agentic_proof_trace_memory_verifier_events",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "n_with_verifier_result_event"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_artifact_kernel_verified": counts.get(
                "formal_verifier_agentic_proof_trace_memory_artifact_kernel_verified",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "n_artifact_kernel_verified"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_source_theorem_kernel_verified": counts.get(
                "formal_verifier_agentic_proof_trace_memory_source_theorem_kernel_verified",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "n_source_theorem_kernel_verified"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_goal_cache_keys": counts.get(
                "formal_verifier_agentic_proof_trace_memory_goal_cache_keys",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "n_goal_cache_keys"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_candidate_lineage_keys": counts.get(
                "formal_verifier_agentic_proof_trace_memory_candidate_lineage_keys",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "n_candidate_lineage_keys"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_with_repair_signals": counts.get(
                "formal_verifier_agentic_proof_trace_memory_with_repair_signals",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "n_with_repair_signals"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_with_required_followups": counts.get(
                "formal_verifier_agentic_proof_trace_memory_with_required_followups",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "n_with_required_followups"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_proof_evidence_status": counts.get(
                "formal_verifier_agentic_proof_trace_memory_proof_evidence_status",
                formal_verifier_agentic_proof_trace_memory_payload.get(
                    "proof_evidence_status"
                ),
            ),
            "formal_verifier_agentic_proof_trace_memory_manifest": str(
                formal_verifier_agentic_proof_trace_memory_path
            ),
            "formal_verifier_agentic_proof_trace_memory_preview": _formal_verifier_agentic_proof_trace_memory_preview(
                formal_verifier_agentic_proof_trace_memory_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_rows": counts.get(
                "formal_verifier_agentic_proof_source_theorem_promotion_rows",
                formal_verifier_agentic_proof_source_theorem_promotion_queue_payload.get(
                    "n_promotion_rows"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_artifact_kernel_inputs": counts.get(
                "formal_verifier_agentic_proof_source_theorem_promotion_artifact_kernel_inputs",
                formal_verifier_agentic_proof_source_theorem_promotion_queue_payload.get(
                    "n_artifact_kernel_verified_inputs"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_ready": counts.get(
                "formal_verifier_agentic_proof_source_theorem_promotion_ready",
                formal_verifier_agentic_proof_source_theorem_promotion_queue_payload.get(
                    "n_ready_for_source_theorem_integration"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_needs_target_resolution": counts.get(
                "formal_verifier_agentic_proof_source_theorem_promotion_needs_target_resolution",
                formal_verifier_agentic_proof_source_theorem_promotion_queue_payload.get(
                    "n_needs_source_theorem_target_resolution"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_source_theorem_kernel_verified": counts.get(
                "formal_verifier_agentic_proof_source_theorem_promotion_source_theorem_kernel_verified",
                formal_verifier_agentic_proof_source_theorem_promotion_queue_payload.get(
                    "n_source_theorem_kernel_verified"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_needs_source_target": counts.get(
                "formal_verifier_agentic_proof_source_theorem_promotion_needs_source_target",
                formal_verifier_agentic_proof_source_theorem_promotion_queue_payload.get(
                    "n_needs_source_theorem_target"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_blocked_artifact_failed": counts.get(
                "formal_verifier_agentic_proof_source_theorem_promotion_blocked_artifact_failed",
                formal_verifier_agentic_proof_source_theorem_promotion_queue_payload.get(
                    "n_blocked_artifact_verification_failed"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_manifest": str(
                formal_verifier_agentic_proof_source_theorem_promotion_queue_path
            ),
            "formal_verifier_agentic_proof_source_theorem_promotion_preview": _formal_verifier_agentic_proof_source_theorem_promotion_preview(
                formal_verifier_agentic_proof_source_theorem_promotion_queue_payload,
                max_rows=min(max_targets, 10),
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_rows": counts.get(
                "formal_verifier_agentic_proof_source_theorem_target_resolution_rows",
                formal_verifier_agentic_proof_source_theorem_target_resolution_payload.get(
                    "n_target_resolution_rows"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_resolved": counts.get(
                "formal_verifier_agentic_proof_source_theorem_target_resolution_resolved",
                formal_verifier_agentic_proof_source_theorem_target_resolution_payload.get(
                    "n_resolved_source_theorem_targets"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_needs_route_match": counts.get(
                "formal_verifier_agentic_proof_source_theorem_target_resolution_needs_route_match",
                formal_verifier_agentic_proof_source_theorem_target_resolution_payload.get(
                    "n_needs_route_ledger_match"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_already_known": counts.get(
                "formal_verifier_agentic_proof_source_theorem_target_resolution_already_known",
                formal_verifier_agentic_proof_source_theorem_target_resolution_payload.get(
                    "n_already_source_theorem_target_known"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_blocked_artifact_kernel": counts.get(
                "formal_verifier_agentic_proof_source_theorem_target_resolution_blocked_artifact_kernel",
                formal_verifier_agentic_proof_source_theorem_target_resolution_payload.get(
                    "n_blocked_artifact_kernel_required"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_overlays": counts.get(
                "formal_verifier_agentic_proof_source_theorem_target_resolution_overlays",
                formal_verifier_agentic_proof_source_theorem_target_resolution_payload.get(
                    "n_overlay_rows"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_ok": counts.get(
                "formal_verifier_agentic_proof_source_theorem_target_resolution_ok",
                formal_verifier_agentic_proof_source_theorem_target_resolution_payload.get(
                    "n_ok"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_proof_evidence_status": counts.get(
                "formal_verifier_agentic_proof_source_theorem_target_resolution_proof_evidence_status",
                formal_verifier_agentic_proof_source_theorem_target_resolution_payload.get(
                    "proof_evidence_status"
                ),
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_manifest": str(
                formal_verifier_agentic_proof_source_theorem_target_resolution_path
            ),
            "formal_verifier_agentic_proof_source_theorem_target_resolution_preview": _formal_verifier_agentic_proof_source_theorem_target_resolution_preview(
                formal_verifier_agentic_proof_source_theorem_target_resolution_payload,
                max_rows=min(max_targets, 10),
            ),
            "formalization_gap_planner_proof_state_triage_items": counts.get(
                "formalization_gap_planner_proof_state_triage_items",
                formalization_gap_planner_proof_state_triage_payload.get(
                    "n_triage_items"
                ),
            ),
            "formalization_gap_planner_proof_state_triage_formal_gap_scaffold_items": counts.get(
                "formalization_gap_planner_proof_state_triage_formal_gap_scaffold_items",
                formalization_gap_planner_proof_state_triage_payload.get(
                    "n_formal_gap_scaffold_items"
                ),
            ),
            "formalization_gap_planner_proof_state_triage_local_lean_failed_items": counts.get(
                "formalization_gap_planner_proof_state_triage_local_lean_failed_items",
                formalization_gap_planner_proof_state_triage_payload.get(
                    "n_local_lean_failed_items"
                ),
            ),
            "formalization_gap_planner_proof_state_triage_non_lean_skeleton_items": counts.get(
                "formalization_gap_planner_proof_state_triage_non_lean_skeleton_items",
                formalization_gap_planner_proof_state_triage_payload.get(
                    "n_non_lean_skeleton_items"
                ),
            ),
            "formalization_gap_planner_proof_state_triage_distinct_signatures": counts.get(
                "formalization_gap_planner_proof_state_triage_distinct_signatures",
                formalization_gap_planner_proof_state_triage_payload.get(
                    "n_distinct_diagnostic_signatures"
                ),
            ),
            "formalization_gap_planner_proof_state_triage_manifest": str(
                formalization_gap_planner_proof_state_triage_path
            ),
            "formalization_gap_planner_proof_state_triage_preview": _formalization_gap_planner_proof_state_triage_preview(
                formalization_gap_planner_proof_state_triage_payload,
                max_rows=min(max_targets, 10),
            ),
            "claim_ledger_repair_response_promotion_overlay_enabled": counts.get(
                "claim_ledger_repair_response_promotion_overlay_enabled"
            ),
            "claim_ledger_repair_response_promotion_overlay_rows": counts.get(
                "claim_ledger_repair_response_promotion_overlay_rows"
            ),
            "claim_ledger_repair_response_promotion_upgrades": counts.get(
                "claim_ledger_repair_response_promotion_upgrades"
            ),
            "handoff_targets": target_rows,
            "proof_bank_expansion_manifest": str(
                _artifact_path(artifacts, "proof_bank_expansion", run_dir)
            ),
            "primitive_source_coverage_manifest": str(
                _artifact_path(artifacts, "primitive_source_coverage", run_dir)
            ),
        },
        "theorem_composition_handoff": theorem_composition_handoff,
        "evaluation_guidance": {
            "top_actions": guidance_payload.get("top_actions", []),
            "saturated_or_capacity_gap_suites": guidance_payload.get(
                "saturated_or_capacity_gap_suites", []
            ),
            "evaluation_benchmark_guidance_manifest": str(
                _artifact_path(artifacts, "evaluation_benchmark_guidance", run_dir)
            ),
        },
        "collaboration_contract": {
            "source_of_truth": "local source mirrors plus commit-pinned manifests; RAG DB is cache/index",
            "recommended_next_rag_work": (
                "Improve provider fusion and hard retrieval benchmarks on the handoff_targets; "
                "feed improved DB path/schema back through --lean-rag-db."
            ),
            "expected_export_back": {
                "db_path": "SQLite/graph DB path",
                "lean_rag_package_root": "EmpericalProcessLEAN/lean_rag package root or commit-pinned checkout",
                "schema_summary": "table names and key columns",
                "retrieval_eval_manifest": "Recall/MRR/ablation manifest path",
                "provider_name": "provider identifier to report in AI-Statistician audits",
            },
        },
        "honesty_boundaries": [
            "RAG hits are retrieval evidence only, not Lean proof evidence.",
            "Only proof-audit rows with kernel_verified=true are proof evidence.",
            "Standalone kernel proof-audit overlays prove only listed obligations, not the source system-audit proof count.",
            "Kernel-overlay alignment is subclaim coverage guidance, not proof of enclosing theorem routes.",
            "Kernel-overlay composition agentic seeds are proof-worker routing artifacts, not theorem proof evidence.",
            "Simulation diagnostics are empirical evidence, not theorem proofs.",
            "FormalVerifier replay rows are executable task/training artifacts, not theorem proof evidence.",
            "FormalVerifier replay attempts are proof evidence only when kernel_verified=true and placeholders were removed.",
            "FormalVerifier replay calibration rows are proof evidence only for full-route kernel-verified targets.",
            "Focused proof-search local Lean reruns are overlay evidence for their selected obligations, not a replacement for default audit counts.",
            "Proof-search kernel-rerun queue rows are replay work orders, not proof evidence.",
            "FormalVerifier replay repair packets and proof templates are not proof evidence until a repaired attempt passes AXLE/local Lean.",
            "FormalVerifier replay repair application scaffolds are work artifacts, not proof evidence.",
            "FormalVerifier repair scaffold validation is source-artifact integrity evidence, not theorem proof evidence.",
            "FormalVerifier repair execution queue items are patch work orders, not theorem proof evidence.",
            "FormalVerifier repair prompt packets are worker instructions, not theorem proof evidence.",
            "FormalVerifier repair patch autoworker responses are local patch proposals, not theorem proof evidence.",
            "FormalVerifier repair patch responses are proof evidence only when response validation accepts full-route kernel-verified calibration.",
            "FormalVerifier repair patch response promotion rows are ledger-update contracts; they do not mutate the proof ledger by themselves.",
            "FormalVerifier repair patch rerun queue rows are replay-calibration work items, not theorem proof evidence.",
            "FormalVerifier repair patch rerun attempts are patched-artifact source checks, not theorem proof evidence.",
            "FormalVerifier repair patch rerun calibration rows are proof evidence only at full_route_kernel_verified.",
            "FormalVerifier repair patch rerun residual obligations are proof/library work contracts, not theorem proof evidence.",
            "FormalVerifier repair patch rerun residual prompt packets are worker instructions, not theorem proof evidence.",
            "FormalVerifier repair patch rerun residual autoworker responses are deterministic proposals, not theorem proof evidence.",
            "FormalVerifier repair patch rerun residual response validation accepts proof claims only with full_route_kernel_verified evidence.",
            "FormalVerifier repair patch rerun residual follow-up queue rows are operational work items, not theorem proof evidence.",
            "Goal-conditioned minimal formalization plans are route-selection artifacts, not theorem proof evidence.",
            "FormalVerifier agentic proof strategy plan rows are search/evaluator plans, not theorem proof evidence.",
            "FormalVerifier agentic proof candidate evaluation queue rows are candidate-generation work orders, not theorem proof evidence.",
            "FormalVerifier agentic proof safety policy rows are preflight guardrails, not theorem proof evidence.",
            "FormalVerifier agentic proof attempt population rows are search-memory records, not theorem proof evidence.",
            "FormalVerifier agentic proof execution queue rows are proof-worker work contracts, not theorem proof evidence.",
            "FormalVerifier agentic proof execution materializer rows are bounded proof-worker inputs, not theorem proof evidence.",
            "FormalVerifier agentic artifact verifier rows are artifact-level Lean checks only; they do not prove source theorem or residual gap claims.",
            "FormalVerifier agentic source-theorem promotion queue rows are target-resolution or integration work orders, not proof evidence.",
            "FormalVerifier agentic source-theorem target-resolution rows are route-ledger overlays, not proof evidence.",
            "Formalization gap proof-state triage rows are proof-worker work orders, not theorem proof evidence.",
            "Hugging Face Lean/OProofs source rows are retrieval, training, or benchmark candidates only; they become proof evidence only after reconstructed Lean artifacts pass local Lean/AXLE kernel verification and promotion review.",
            "Hugging Face Lean/OProofs prompt packets are worker instructions and response contracts, not proof evidence.",
            "Claim-ledger repair-response promotion overlays close formal gaps only for matching ready kernel-verified promotion rows.",
            "FORMAL_GAP and theorem-hole queues remain open until a non-placeholder Lean proof is verified.",
        ],
    }
    payload["handoff_fingerprint"] = stable_hash(
        {
            "proof_evidence": payload["proof_evidence"],
            "kernel_proof_evidence_overlays": payload["kernel_proof_evidence_overlays"],
            "kernel_proof_overlay_alignment": payload["kernel_proof_overlay_alignment"],
            "rag_provider_evidence": payload["rag_provider_evidence"],
            "formal_capacity_queue": payload["formal_capacity_queue"],
            "theorem_composition_handoff": payload["theorem_composition_handoff"],
        }
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rag_collaboration_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "rag_collaboration.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _artifact_path(artifacts: dict[str, object], key: str, run_dir: Path) -> Path:
    raw = str(artifacts.get(key, ""))
    if not raw:
        return Path("__missing__")
    path = Path(raw)
    if path.exists():
        return path
    candidate = run_dir / path
    return candidate if candidate.exists() else path


def _auto_discover_artifacts(
    artifacts: dict[str, object],
    run_dir: Path,
    *,
    protected_keys: set[str] | None = None,
) -> dict[str, str]:
    discoveries: dict[str, str] = {}
    if not _is_current_run_dir(run_dir):
        return discoveries
    protected = set(protected_keys or set())
    triage_key = "formalization_gap_planner_proof_state_triage"
    if triage_key not in protected and not str(artifacts.get(triage_key, "")):
        triage_manifest = (
            Path("current_formalization_gap_planner_proof_state_triage")
            / "formalization_gap_planner_proof_state_triage_manifest.json"
        )
        triage_candidate = _first_existing(run_dir.parent / triage_manifest)
        if triage_candidate is not None:
            discoveries[triage_key] = str(triage_candidate)
    proof_search_kernel_rerun_key = "proof_search_kernel_rerun_local_lean"
    if proof_search_kernel_rerun_key not in protected and not str(
        artifacts.get(proof_search_kernel_rerun_key, "")
    ):
        rerun_candidate = _first_existing(
            run_dir.parent
            / "proof_search_kernel_rerun_local_lean"
            / "proof_search_audit_manifest.json"
        )
        if rerun_candidate is not None:
            rerun_payload = _read_json(rerun_candidate)
            if int(rerun_payload.get("n_kernel_verified", 0) or 0) > 0:
                discoveries[proof_search_kernel_rerun_key] = str(rerun_candidate)
    same_run_candidates = {
        "huggingface_lean_source_revalidation_prompt_packets": (
            run_dir
            / "huggingface_lean_source_revalidation_prompt_packets"
            / "hf_lean_source_revalidation_prompt_packets_manifest.json"
        ),
    }
    for key, candidate in same_run_candidates.items():
        if key in protected or str(artifacts.get(key, "")):
            continue
        discovered = _first_existing(candidate)
        if discovered is not None:
            discoveries[key] = str(discovered)
    seeded_agentic_candidates = {
        "formal_verifier_agentic_proof_strategy_plan": (
            Path("current_kernel_overlay_seeded_agentic_proof_strategy_plan")
            / "formal_verifier_agentic_proof_strategy_plan_manifest.json",
            ("n_kernel_overlay_composition_seeds",),
        ),
        "formal_verifier_agentic_proof_candidate_evaluation_queue": (
            Path("current_kernel_overlay_seeded_agentic_proof_candidate_evaluation_queue")
            / "formal_verifier_agentic_proof_candidate_evaluation_queue_manifest.json",
            ("n_kernel_overlay_candidate_items", "n_with_kernel_overlay_context"),
        ),
        "formal_verifier_agentic_proof_safety_policy": (
            Path("current_kernel_overlay_seeded_agentic_proof_safety_policy")
            / "formal_verifier_agentic_proof_safety_policy_manifest.json",
            ("n_with_kernel_overlay_context",),
        ),
        "formal_verifier_agentic_proof_attempt_population": (
            Path("current_kernel_overlay_seeded_agentic_proof_attempt_population")
            / "formal_verifier_agentic_proof_attempt_population_manifest.json",
            ("n_with_kernel_overlay_context",),
        ),
        "formal_verifier_agentic_proof_execution_queue": (
            Path("current_kernel_overlay_seeded_agentic_proof_execution_queue")
            / "formal_verifier_agentic_proof_execution_queue_manifest.json",
            (
                "n_with_kernel_overlay_context",
                "n_with_proof_route_dag_plan",
                "n_with_verified_sketch_gate",
            ),
        ),
        "formal_verifier_agentic_proof_execution_materializer": (
            Path("current_kernel_overlay_seeded_agentic_proof_execution_materializer")
            / "formal_verifier_agentic_proof_execution_materializer_manifest.json",
            ("n_materialized_artifacts", "n_live_goal_location_ready"),
        ),
        "formal_verifier_agentic_proof_execution_artifact_verifier": (
            Path(
                "current_kernel_overlay_seeded_agentic_proof_execution_artifact_verifier"
            )
            / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json",
            ("n_artifact_kernel_verified", "n_local_lean_checked"),
        ),
        "formal_verifier_agentic_proof_trace_memory": (
            Path("current_kernel_overlay_seeded_agentic_proof_trace_memory")
            / "formal_verifier_agentic_proof_trace_memory_manifest.json",
            (
                "n_trace_memory_rows",
                "n_with_verifier_result_event",
                "n_artifact_kernel_verified",
            ),
        ),
        "formal_verifier_agentic_proof_source_theorem_promotion_queue": (
            Path(
                "current_kernel_overlay_seeded_agentic_proof_source_theorem_promotion_queue"
            )
            / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json",
            (
                "n_ready_for_source_theorem_integration",
                "n_needs_source_theorem_target_resolution",
                "n_source_theorem_kernel_verified",
            ),
        ),
        "formal_verifier_agentic_proof_source_theorem_target_resolution": (
            Path(
                "current_kernel_overlay_seeded_agentic_proof_source_theorem_target_resolution"
            )
            / "formal_verifier_agentic_proof_source_theorem_target_resolution_manifest.json",
            (
                "n_resolved_source_theorem_targets",
                "n_needs_route_ledger_match",
                "n_overlay_rows",
            ),
        ),
    }
    for key, (relative_path, context_counts) in seeded_agentic_candidates.items():
        if key in protected:
            continue
        candidate = _first_existing(run_dir.parent / relative_path)
        if candidate is None:
            continue
        candidate_score = _context_count_score(_read_json(candidate), context_counts)
        if candidate_score <= 0:
            continue
        existing_raw = str(artifacts.get(key, ""))
        if existing_raw:
            existing_score = _context_count_score(
                _read_json(_artifact_path(artifacts, key, run_dir)),
                context_counts,
            )
            if existing_score >= candidate_score:
                continue
        discoveries[key] = str(candidate)
    return discoveries


def _first_existing(*candidates: Path) -> Path | None:
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if candidate.exists():
            return candidate
    return None


def _context_count_score(payload: dict[str, Any], keys: tuple[str, ...]) -> int:
    score = 0
    for key in keys:
        try:
            score += int(payload.get(key, 0) or 0)
        except (TypeError, ValueError):
            continue
    return score


def _overlay_auto_discovered_agentic_counts(
    counts: dict[str, object],
    artifact_auto_discoveries: dict[str, str],
    **payloads: dict[str, Any],
) -> dict[str, object]:
    """Let richer auto-discovered current manifests replace stale generic counts."""

    updated = dict(counts)
    mappings = {
        "formal_verifier_agentic_proof_strategy_plan": (
            "formal_verifier_agentic_proof_strategy_plan_payload",
            {
                "formal_verifier_agentic_proof_strategy_plan_rows": "n_strategy_rows",
                "formal_verifier_agentic_proof_strategy_plan_ready": "n_ready",
                "formal_verifier_agentic_proof_strategy_plan_patch_evolve_blocks": "n_patch_evolve_blocks",
                "formal_verifier_agentic_proof_strategy_plan_source_discovery_cache_items": "n_source_discovery_cache_items",
                "formal_verifier_agentic_proof_strategy_plan_kernel_overlay_composition_seeds": "n_kernel_overlay_composition_seeds",
            },
        ),
        "formal_verifier_agentic_proof_candidate_evaluation_queue": (
            "formal_verifier_agentic_proof_candidate_evaluation_queue_payload",
            {
                "formal_verifier_agentic_proof_candidate_evaluation_queue_items": "n_candidate_queue_items",
                "formal_verifier_agentic_proof_candidate_evaluation_queue_ready": "n_ready",
                "formal_verifier_agentic_proof_candidate_evaluation_queue_blocked": "n_blocked",
                "formal_verifier_agentic_proof_candidate_evaluation_queue_patch_candidates": "n_patch_candidate_items",
                "formal_verifier_agentic_proof_candidate_evaluation_queue_source_discovery_candidates": "n_source_discovery_candidate_items",
                "formal_verifier_agentic_proof_candidate_evaluation_queue_kernel_overlay_candidates": "n_kernel_overlay_candidate_items",
                "formal_verifier_agentic_proof_candidate_evaluation_queue_with_kernel_overlay_context": "n_with_kernel_overlay_context",
            },
        ),
        "formal_verifier_agentic_proof_safety_policy": (
            "formal_verifier_agentic_proof_safety_policy_payload",
            {
                "formal_verifier_agentic_proof_safety_policy_rows": "n_safety_policy_rows",
                "formal_verifier_agentic_proof_safety_policy_ready": "n_ready",
                "formal_verifier_agentic_proof_safety_policy_blocked": "n_blocked",
                "formal_verifier_agentic_proof_safety_policy_patch_bounded_edit": "n_patch_bounded_edit_policies",
                "formal_verifier_agentic_proof_safety_policy_source_validation": "n_source_validation_policies",
                "formal_verifier_agentic_proof_safety_policy_with_kernel_overlay_context": "n_with_kernel_overlay_context",
            },
        ),
        "formal_verifier_agentic_proof_attempt_population": (
            "formal_verifier_agentic_proof_attempt_population_payload",
            {
                "formal_verifier_agentic_proof_attempt_population_entries": "n_population_entries",
                "formal_verifier_agentic_proof_attempt_population_ready": "n_ready",
                "formal_verifier_agentic_proof_attempt_population_blocked": "n_blocked",
                "formal_verifier_agentic_proof_attempt_population_patch_entries": "n_patch_population_entries",
                "formal_verifier_agentic_proof_attempt_population_source_entries": "n_source_population_entries",
                "formal_verifier_agentic_proof_attempt_population_with_kernel_overlay_context": "n_with_kernel_overlay_context",
            },
        ),
        "formal_verifier_agentic_proof_execution_queue": (
            "formal_verifier_agentic_proof_execution_queue_payload",
            {
                "formal_verifier_agentic_proof_execution_queue_items": "n_execution_queue_items",
                "formal_verifier_agentic_proof_execution_queue_ready": "n_ready",
                "formal_verifier_agentic_proof_execution_queue_blocked": "n_blocked",
                "formal_verifier_agentic_proof_execution_queue_patch_items": "n_patch_execution_items",
                "formal_verifier_agentic_proof_execution_queue_source_items": "n_source_execution_items",
                "formal_verifier_agentic_proof_execution_queue_with_candidate_artifact_path": "n_with_candidate_artifact_path",
                "formal_verifier_agentic_proof_execution_queue_with_live_tool_plan": "n_with_live_tool_plan",
                "formal_verifier_agentic_proof_execution_queue_with_proof_route_dag_plan": "n_with_proof_route_dag_plan",
                "formal_verifier_agentic_proof_execution_queue_with_verified_sketch_gate": "n_with_verified_sketch_gate",
                "formal_verifier_agentic_proof_execution_queue_with_blueprint_export_plan": "n_with_blueprint_export_plan",
                "formal_verifier_agentic_proof_execution_queue_with_kernel_overlay_context": "n_with_kernel_overlay_context",
                "formal_verifier_agentic_proof_execution_queue_live_goal_requested": "n_live_goal_requested",
                "formal_verifier_agentic_proof_execution_queue_live_goal_location_ready": "n_live_goal_location_ready",
                "formal_verifier_agentic_proof_execution_queue_needs_target_location": "n_needs_target_location",
                "formal_verifier_agentic_proof_execution_queue_candidate_artifact_exists": "n_candidate_artifact_exists",
            },
        ),
        "formal_verifier_agentic_proof_execution_materializer": (
            "formal_verifier_agentic_proof_execution_materializer_payload",
            {
                "formal_verifier_agentic_proof_execution_materializer_rows": "n_materializer_rows",
                "formal_verifier_agentic_proof_execution_materializer_artifacts": "n_materialized_artifacts",
                "formal_verifier_agentic_proof_execution_materializer_new_artifacts": "n_new_artifacts",
                "formal_verifier_agentic_proof_execution_materializer_live_goal_location_ready": "n_live_goal_location_ready",
                "formal_verifier_agentic_proof_execution_materializer_live_proof_state_requests": "n_live_proof_state_requests",
                "formal_verifier_agentic_proof_execution_materializer_lean_lsp_mcp_ready_requests": "n_lean_lsp_mcp_ready_requests",
                "formal_verifier_agentic_proof_execution_materializer_kernel_verified": "n_kernel_verified",
            },
        ),
        "formal_verifier_agentic_proof_execution_artifact_verifier": (
            "formal_verifier_agentic_proof_execution_artifact_verifier_payload",
            {
                "formal_verifier_agentic_proof_execution_artifact_verifier_enabled": "enabled",
                "formal_verifier_agentic_proof_execution_artifact_verifier_rows": "n_verifier_rows",
                "formal_verifier_agentic_proof_execution_artifact_verifier_checked": "n_local_lean_checked",
                "formal_verifier_agentic_proof_execution_artifact_verifier_compiled": "n_local_lean_compiled",
                "formal_verifier_agentic_proof_execution_artifact_kernel_verified": "n_artifact_kernel_verified",
                "formal_verifier_agentic_proof_execution_source_theorem_kernel_verified": "n_source_theorem_kernel_verified",
                "formal_verifier_agentic_proof_execution_artifact_forbidden_token_failures": "n_forbidden_token_failures",
                "formal_verifier_agentic_proof_execution_artifact_transcript_paths": "n_execution_transcript_paths",
                "formal_verifier_agentic_proof_execution_artifact_transcript_events_written": "n_execution_transcript_events_written",
                "formal_verifier_agentic_proof_execution_artifact_live_proof_state_requests": "n_live_proof_state_requests",
                "formal_verifier_agentic_proof_execution_artifact_live_proof_state_request_valid": "n_live_proof_state_request_valid",
                "formal_verifier_agentic_proof_execution_artifact_lean_lsp_mcp_ready_requests": "n_lean_lsp_mcp_ready_requests",
                "formal_verifier_agentic_proof_execution_artifact_live_proof_state_request_failures": "n_live_proof_state_request_failures",
                "formal_verifier_agentic_proof_execution_artifact_verifier_ok": "n_ok",
                "formal_verifier_agentic_proof_execution_artifact_proof_evidence_status": "proof_evidence_status",
            },
        ),
        "formal_verifier_agentic_proof_trace_memory": (
            "formal_verifier_agentic_proof_trace_memory_payload",
            {
                "formal_verifier_agentic_proof_trace_memory_rows": "n_trace_memory_rows",
                "formal_verifier_agentic_proof_trace_memory_transcript_events": "n_transcript_events",
                "formal_verifier_agentic_proof_trace_memory_verifier_events": "n_with_verifier_result_event",
                "formal_verifier_agentic_proof_trace_memory_artifact_kernel_verified": "n_artifact_kernel_verified",
                "formal_verifier_agentic_proof_trace_memory_source_theorem_kernel_verified": "n_source_theorem_kernel_verified",
                "formal_verifier_agentic_proof_trace_memory_goal_cache_keys": "n_goal_cache_keys",
                "formal_verifier_agentic_proof_trace_memory_candidate_lineage_keys": "n_candidate_lineage_keys",
                "formal_verifier_agentic_proof_trace_memory_with_repair_signals": "n_with_repair_signals",
                "formal_verifier_agentic_proof_trace_memory_with_required_followups": "n_with_required_followups",
                "formal_verifier_agentic_proof_trace_memory_ok": "n_ok",
                "formal_verifier_agentic_proof_trace_memory_proof_evidence_status": "proof_evidence_status",
            },
        ),
        "formal_verifier_agentic_proof_source_theorem_promotion_queue": (
            "formal_verifier_agentic_proof_source_theorem_promotion_queue_payload",
            {
                "formal_verifier_agentic_proof_source_theorem_promotion_rows": "n_promotion_rows",
                "formal_verifier_agentic_proof_source_theorem_promotion_artifact_kernel_inputs": "n_artifact_kernel_verified_inputs",
                "formal_verifier_agentic_proof_source_theorem_promotion_ready": "n_ready_for_source_theorem_integration",
                "formal_verifier_agentic_proof_source_theorem_promotion_needs_target_resolution": "n_needs_source_theorem_target_resolution",
                "formal_verifier_agentic_proof_source_theorem_promotion_source_theorem_kernel_verified": "n_source_theorem_kernel_verified",
                "formal_verifier_agentic_proof_source_theorem_promotion_needs_source_target": "n_needs_source_theorem_target",
                "formal_verifier_agentic_proof_source_theorem_promotion_blocked_artifact_failed": "n_blocked_artifact_verification_failed",
                "formal_verifier_agentic_proof_source_theorem_promotion_ok": "n_ok",
            },
        ),
        "formal_verifier_agentic_proof_source_theorem_target_resolution": (
            "formal_verifier_agentic_proof_source_theorem_target_resolution_payload",
            {
                "formal_verifier_agentic_proof_source_theorem_target_resolution_rows": "n_target_resolution_rows",
                "formal_verifier_agentic_proof_source_theorem_target_resolution_resolved": "n_resolved_source_theorem_targets",
                "formal_verifier_agentic_proof_source_theorem_target_resolution_needs_route_match": "n_needs_route_ledger_match",
                "formal_verifier_agentic_proof_source_theorem_target_resolution_already_known": "n_already_source_theorem_target_known",
                "formal_verifier_agentic_proof_source_theorem_target_resolution_blocked_artifact_kernel": "n_blocked_artifact_kernel_required",
                "formal_verifier_agentic_proof_source_theorem_target_resolution_overlays": "n_overlay_rows",
                "formal_verifier_agentic_proof_source_theorem_target_resolution_ok": "n_ok",
                "formal_verifier_agentic_proof_source_theorem_target_resolution_proof_evidence_status": "proof_evidence_status",
            },
        ),
    }
    for artifact_key, (payload_name, field_map) in mappings.items():
        if artifact_key not in artifact_auto_discoveries:
            continue
        payload = payloads.get(payload_name, {})
        if not isinstance(payload, dict):
            continue
        for count_key, payload_key in field_map.items():
            if payload_key in payload:
                updated[count_key] = payload[payload_key]
    return updated


def _kernel_proof_evidence_overlays(
    run_dir: Path,
    *,
    system_proof_bank_fingerprint: str,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    distinct_kernel_ids: set[str] = set()
    matching_kernel_ids: set[str] = set()
    if not _is_current_run_dir(run_dir):
        return _kernel_proof_evidence_overlay_payload(rows, distinct_kernel_ids, matching_kernel_ids)
    for manifest_path in _kernel_proof_audit_candidates(run_dir):
        payload = _read_json(manifest_path)
        if not _is_kernel_proof_audit_payload(payload):
            continue
        kernel_ids = _kernel_verified_obligation_ids(payload)
        if not kernel_ids:
            continue
        distinct_kernel_ids.update(kernel_ids)
        fingerprint = str(payload.get("proof_bank_fingerprint", ""))
        fingerprint_matches = bool(
            system_proof_bank_fingerprint
            and fingerprint
            and fingerprint == system_proof_bank_fingerprint
        )
        if fingerprint_matches:
            matching_kernel_ids.update(kernel_ids)
        rows.append(
            {
                "manifest": str(manifest_path),
                "created_at": payload.get("created_at", ""),
                "verifier": payload.get("verifier", ""),
                "verification_strength": payload.get("verification_strength", ""),
                "proof_bank_fingerprint": fingerprint,
                "fingerprint_matches_system_proof_bank": fingerprint_matches,
                "n_obligations": payload.get("n_obligations", 0),
                "n_verified": payload.get("n_verified", 0),
                "n_kernel_verified": payload.get("n_kernel_verified", 0),
                "all_kernel_verified": bool(payload.get("all_kernel_verified")),
                "sample_kernel_verified_obligations": kernel_ids[:8],
            }
        )
    rows.sort(
        key=lambda row: (
            not bool(row.get("fingerprint_matches_system_proof_bank")),
            -int(row.get("n_kernel_verified", 0) or 0),
            str(row.get("manifest", "")),
        )
    )
    return _kernel_proof_evidence_overlay_payload(rows, distinct_kernel_ids, matching_kernel_ids)


def _kernel_proof_evidence_overlay_payload(
    rows: list[dict[str, object]],
    distinct_kernel_ids: set[str],
    matching_kernel_ids: set[str],
) -> dict[str, object]:
    return {
        "standalone_kernel_proof_audits": len(rows),
        "standalone_kernel_proof_audits_matching_system_fingerprint": sum(
            1 for row in rows if row.get("fingerprint_matches_system_proof_bank")
        ),
        "standalone_kernel_verified_distinct_obligations": len(distinct_kernel_ids),
        "standalone_kernel_verified_distinct_current_fingerprint_obligations": len(
            matching_kernel_ids
        ),
        "standalone_kernel_verified_current_fingerprint_obligation_ids": sorted(
            matching_kernel_ids
        ),
        "standalone_kernel_verified_distinct_obligation_ids_preview": sorted(
            distinct_kernel_ids
        )[:25],
        "standalone_kernel_proof_audit_preview": rows[:8],
        "proof_evidence_boundary": (
            "Standalone kernel proof-audit overlays are Lean/AXLE proof evidence only "
            "for the listed proof-bank obligations. They do not upgrade the source "
            "system-audit proof count or close frontier formal gaps unless the proof-bank "
            "fingerprint and obligation IDs match the promoted claim."
        ),
    }


def _kernel_proof_overlay_alignment(
    kernel_overlay_payload: dict[str, object],
    theorem_composition_handoff: dict[str, object],
    formal_verifier_queue_payload: dict[str, Any],
    formal_verifier_replay_payload: dict[str, Any],
    *,
    max_rows: int,
) -> dict[str, object]:
    current_kernel_ids = set(
        str(item)
        for item in kernel_overlay_payload.get(
            "standalone_kernel_verified_current_fingerprint_obligation_ids",
            [],
        )
        if str(item)
    )
    composition_rows: list[dict[str, object]] = []
    composition_kernel_obligations: set[str] = set()
    for packet in theorem_composition_handoff.get("packet_preview", []):
        if not isinstance(packet, dict):
            continue
        exact_obligations = _str_list(packet.get("exact_proof_bank_obligations", []))
        matched = sorted(set(exact_obligations) & current_kernel_ids)
        if not matched:
            continue
        composition_kernel_obligations.update(matched)
        composition_rows.append(
            {
                "packet_id": packet.get("packet_id"),
                "source_claim_id": packet.get("source_claim_id"),
                "question_id": packet.get("question_id"),
                "problem_class": packet.get("problem_class"),
                "status": packet.get("status"),
                "exact_proof_bank_obligations": exact_obligations,
                "kernel_overlay_verified_obligations": matched,
                "unresolved_primitives": packet.get("unresolved_primitives", []),
                "required_gate": packet.get("required_gate", ""),
                "recommended_next_action": (
                    "reuse the matched kernel-verified subclaims, then build and "
                    "kernel-verify the non-placeholder composed theorem; do not "
                    "promote this packet as a full theorem proof by itself"
                ),
            }
        )

    queue_rows = _kernel_overlay_queue_alignment_rows(
        formal_verifier_queue_payload.get("rows", []),
        current_kernel_ids,
        id_key="item_id",
        obligation_key="related_proof_obligations",
        max_rows=max_rows,
    )
    replay_rows = _kernel_overlay_queue_alignment_rows(
        formal_verifier_replay_payload.get("tasks", []),
        current_kernel_ids,
        id_key="replay_id",
        obligation_key="subclaim_replay_obligations",
        max_rows=max_rows,
    )
    composition_work_items = _kernel_overlay_composition_work_items(
        composition_rows,
        max_rows=max_rows,
    )
    composition_agentic_seeds = _kernel_overlay_composition_agentic_seed_items(
        composition_work_items,
        max_rows=max_rows,
    )
    return {
        "current_fingerprint_kernel_obligations": len(current_kernel_ids),
        "theorem_composition_packets_with_kernel_overlay": len(composition_rows),
        "theorem_composition_kernel_overlay_obligations": len(
            composition_kernel_obligations
        ),
        "kernel_overlay_composition_work_items": len(composition_work_items),
        "kernel_overlay_composition_agentic_seeds": len(composition_agentic_seeds),
        "kernel_overlay_composition_agentic_seeds_ready": sum(
            1
            for row in composition_agentic_seeds
            if row.get("seed_status") == "READY_FOR_AGENTIC_COMPOSITION_ATTEMPT"
        ),
        "kernel_overlay_composition_agentic_seeds_with_source_queries": sum(
            1 for row in composition_agentic_seeds if row.get("source_discovery_queries")
        ),
        "kernel_overlay_composition_work_items_exact_subclaims_fully_matched": sum(
            1
            for row in composition_work_items
            if not row.get("unmatched_exact_proof_bank_obligations")
        ),
        "kernel_overlay_composition_work_items_with_unresolved_primitives": sum(
            1 for row in composition_work_items if row.get("unresolved_primitives")
        ),
        "formal_verifier_queue_rows_with_kernel_overlay": len(queue_rows),
        "formal_verifier_replay_tasks_with_kernel_overlay": len(replay_rows),
        "theorem_composition_kernel_overlay_preview": composition_rows[:max_rows],
        "kernel_overlay_composition_work_item_preview": composition_work_items,
        "kernel_overlay_composition_agentic_seed_preview": composition_agentic_seeds,
        "formal_verifier_queue_kernel_overlay_preview": queue_rows[:max_rows],
        "formal_verifier_replay_kernel_overlay_preview": replay_rows[:max_rows],
        "proof_evidence_boundary": (
            "Kernel-overlay alignment identifies proof-bank subclaims that already "
            "have matching-fingerprint kernel evidence. It is not proof evidence for "
            "the enclosing theorem route, replay task, or composition packet until "
            "the composed non-placeholder theorem passes AXLE/local Lean."
        ),
    }


def _kernel_overlay_composition_work_items(
    composition_rows: list[dict[str, object]],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    work_items: list[dict[str, object]] = []
    for row in composition_rows:
        exact = _str_list(row.get("exact_proof_bank_obligations", []))
        matched = _str_list(row.get("kernel_overlay_verified_obligations", []))
        unmatched = sorted(set(exact) - set(matched))
        unresolved = _str_list(row.get("unresolved_primitives", []))
        work_item_id = "kernel_overlay_composition_work:" + stable_hash(
            [row.get("packet_id"), matched, unmatched, unresolved]
        )[:16]
        work_items.append(
            {
                "work_item_id": work_item_id,
                "packet_id": row.get("packet_id"),
                "source_claim_id": row.get("source_claim_id"),
                "question_id": row.get("question_id"),
                "problem_class": row.get("problem_class"),
                "already_kernel_verified_subclaims": matched,
                "unmatched_exact_proof_bank_obligations": unmatched,
                "unresolved_primitives": unresolved,
                "target_blocker_count": len(unmatched) + len(unresolved),
                "recommended_next_action": row.get("recommended_next_action", ""),
                "proof_worker_contract": (
                    "Use the already_kernel_verified_subclaims as exact proof-bank "
                    "evidence for subclaims only; materialize any unmatched exact "
                    "obligations or unresolved primitives, then submit a non-placeholder "
                    "composed theorem proof to AXLE/local Lean."
                ),
                "promotion_gate": row.get("required_gate", ""),
                "proof_evidence_status": (
                    "KERNEL_OVERLAY_COMPOSITION_WORK_ITEM_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": (
                    "This work item is a proof-construction target. It is not proof "
                    "evidence for the source claim until the composed theorem passes "
                    "AXLE/local Lean."
                ),
            }
        )
    work_items.sort(
        key=lambda item: (
            int(item.get("target_blocker_count", 0) or 0),
            -len(item.get("already_kernel_verified_subclaims", []) or []),
            str(item.get("work_item_id", "")),
        )
    )
    return work_items[:max_rows]


def _kernel_overlay_composition_agentic_seed_items(
    work_items: list[dict[str, object]],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    seeds: list[dict[str, object]] = []
    for item in work_items:
        work_item_id = str(item.get("work_item_id", ""))
        source_claim_id = str(item.get("source_claim_id", ""))
        question_id = str(item.get("question_id", ""))
        matched = _str_list(item.get("already_kernel_verified_subclaims", []))
        unmatched = _str_list(item.get("unmatched_exact_proof_bank_obligations", []))
        unresolved = _str_list(item.get("unresolved_primitives", []))
        blockers = [*unmatched, *unresolved]
        goal_cache_key = "kernel_overlay_composition_goal:" + stable_hash(
            [source_claim_id, question_id, matched, blockers]
        )[:16]
        candidate_database_key = "kernel_overlay_composition_candidate:" + stable_hash(
            [work_item_id, goal_cache_key, blockers]
        )[:16]
        seed_id = "kernel_overlay_composition_agentic_seed:" + stable_hash(
            [work_item_id, candidate_database_key, goal_cache_key]
        )[:16]
        source_queries = tuple(
            f"{question_id} {blocker} Lean theorem proof source".strip()
            for blocker in blockers
            if blocker
        )
        seeds.append(
            {
                "seed_id": seed_id,
                "work_item_id": work_item_id,
                "packet_id": item.get("packet_id"),
                "source_claim_id": source_claim_id,
                "question_id": question_id,
                "problem_class": item.get("problem_class"),
                "seed_status": "READY_FOR_AGENTIC_COMPOSITION_ATTEMPT",
                "agentic_strategy_kind": "kernel_overlay_composition_patch_seed",
                "goal_cache_key": goal_cache_key,
                "candidate_database_key": candidate_database_key,
                "proof_sketch_population_key": (
                    "kernel_overlay_composition_sketch:"
                    + stable_hash([goal_cache_key, matched])[:16]
                ),
                "already_kernel_verified_subclaims": matched,
                "target_blockers": blockers,
                "source_discovery_queries": source_queries,
                "required_live_tools": (
                    "lean_goal",
                    "lean_diagnostic_messages",
                    "lean_hover",
                    "lean_local_search",
                    "lean_multi_attempt",
                ),
                "evaluator_gates": (
                    "bounded-edit statement/header guard",
                    "source discovery for unmatched blockers",
                    "sorry/axiom/placeholder scan",
                    "AXLE/local Lean composed theorem verification",
                ),
                "bounded_edit_contract": {
                    "bounded_edit_required": True,
                    "start_marker": "-- AI_STAT_EVOLVE_BLOCK_START",
                    "end_marker": "-- AI_STAT_EVOLVE_BLOCK_END",
                    "editable_scope": (
                        "composed theorem proof body plus minimal blocker bridge "
                        "lemmas only"
                    ),
                    "forbidden_tokens": ["sorry", "admit", "axiom"],
                    "anti_cheat_checks": [
                        "edit_outside_evolve_block",
                        "target_restated_as_helper_lemma",
                        "helper_lemma_contains_placeholder",
                        "hallucinated_known_source_lemma",
                    ],
                },
                "generation_contract": (
                    "reuse already_kernel_verified_subclaims as subclaim evidence only",
                    "materialize every target_blocker before claiming the source theorem",
                    "preserve theorem statement, imports, namespace, and declaration header",
                    "submit a non-placeholder composed theorem to AXLE/local Lean",
                ),
                "promotion_gate": item.get("promotion_gate", ""),
                "proof_evidence_status": (
                    "KERNEL_OVERLAY_COMPOSITION_AGENTIC_SEED_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": (
                    "This agentic seed is a proof-worker routing artifact, not proof "
                    "evidence. It becomes proof-relevant only after the composed "
                    "non-placeholder theorem passes AXLE/local Lean."
                ),
            }
        )
    seeds.sort(
        key=lambda seed: (
            len(seed.get("target_blockers", []) or []),
            str(seed.get("source_claim_id", "")),
            str(seed.get("seed_id", "")),
        )
    )
    return seeds[:max_rows]


def _kernel_overlay_queue_alignment_rows(
    rows_payload: object,
    current_kernel_ids: set[str],
    *,
    id_key: str,
    obligation_key: str,
    max_rows: int,
) -> list[dict[str, object]]:
    aligned_rows: list[dict[str, object]] = []
    if not isinstance(rows_payload, list):
        return aligned_rows
    for row in rows_payload:
        if not isinstance(row, dict):
            continue
        obligations = _str_list(row.get(obligation_key, []))
        matched = sorted(set(obligations) & current_kernel_ids)
        if not matched:
            continue
        aligned_rows.append(
            {
                id_key: row.get(id_key),
                "route_id": row.get("route_id"),
                "display_name": row.get("display_name"),
                "kernel_overlay_verified_obligations": matched,
                "all_candidate_obligations": obligations[:10],
                "required_gate": row.get("required_gate")
                or row.get("acceptance_gate")
                or row.get("required_kernel_boundary", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(aligned_rows) >= max_rows:
            break
    return aligned_rows


def _str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _kernel_proof_audit_candidates(run_dir: Path) -> list[Path]:
    candidate_patterns = (
        "current*_proof_audit*/proof_audit_manifest.json",
        "current*kernel_smoke*/proof_audit_manifest.json",
        "proof_audit_local_lean_current/proof_audit_manifest.json",
    )
    candidates: list[Path] = []
    seen: set[Path] = set()
    for pattern in candidate_patterns:
        for candidate in sorted(run_dir.parent.glob(pattern)):
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            candidates.append(candidate)
    return candidates


def _is_kernel_proof_audit_payload(payload: dict[str, Any]) -> bool:
    if int(payload.get("n_kernel_verified", 0) or 0) <= 0:
        return False
    strength = str(payload.get("verification_strength", "")).lower()
    verifier = str(payload.get("verifier", "")).lower()
    return (
        "kernel" in strength
        or "lean" in strength
        or "axle" in strength
        or "lean" in verifier
        or "axle" in verifier
    )


def _kernel_verified_obligation_ids(payload: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for row in payload.get("checks", []):
        if not isinstance(row, dict):
            continue
        obligation_id = str(row.get("obligation_id", ""))
        if obligation_id and row.get("kernel_verified"):
            ids.append(obligation_id)
    return list(dict.fromkeys(ids))


def _is_current_run_dir(run_dir: Path) -> bool:
    return run_dir.name.startswith("current_")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _handoff_targets(
    primitive_rows: object,
    candidate_rows: object,
    *,
    max_targets: int,
) -> list[dict[str, object]]:
    candidates_by_primitive = {
        str(row.get("primitive", "")): row
        for row in candidate_rows
        if isinstance(row, dict) and row.get("primitive")
    }
    rows: list[dict[str, object]] = []
    for row in primitive_rows if isinstance(primitive_rows, list) else []:
        if not isinstance(row, dict):
            continue
        action_class = str(row.get("action_class", ""))
        if action_class == "compose_existing_bridge_chain":
            continue
        primitive = str(row.get("primitive", ""))
        candidate = candidates_by_primitive.get(primitive, {})
        rows.append(
            {
                "primitive": primitive,
                "action_class": action_class,
                "classification": row.get("classification"),
                "n_gaps": row.get("n_gaps"),
                "problem_classes": row.get("problem_classes", []),
                "theorem_goals": row.get("theorem_goals", []),
                "proof_bank_bridge_obligations": row.get("proof_bank_bridge_obligations", [])[:8],
                "local_candidate_declarations": row.get("local_candidate_declarations", [])[:8],
                "external_candidate_declarations": row.get("external_candidate_declarations", [])[:8],
                "external_source_ids": row.get("external_source_ids", []),
                "suggested_next_step": row.get("suggested_next_step", ""),
                "proposal_id": candidate.get("proposal_id", ""),
                "query_hint": _query_hint(row),
            }
        )
    rows.sort(key=lambda item: (_action_priority(str(item.get("action_class", ""))), str(item.get("primitive", ""))))
    return rows[:max_targets]


def _lean_rag_seed_lanes(payload: dict[str, Any]) -> list[str]:
    seed_queries = dict(payload.get("seed_queries", {}) or {})
    lanes = seed_queries.get("lanes", [])
    if isinstance(lanes, list):
        return [str(lane) for lane in lanes]
    if isinstance(lanes, tuple):
        return [str(lane) for lane in lanes]
    return []


def _proof_search_kernel_rerun_queue_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    payload_rows = payload.get("rows", [])
    if not isinstance(payload_rows, list):
        return rows
    for row in payload_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "rerun_queue_id": row.get("rerun_queue_id"),
                "obligation_id": row.get("obligation_id"),
                "title": row.get("title"),
                "status": row.get("status"),
                "selected_source": row.get("selected_source"),
                "selected_verifier": row.get("selected_verifier"),
                "selected_verification_strength": row.get("selected_verification_strength"),
                "prior_nodes_expanded": row.get("prior_nodes_expanded", 0),
                "prior_candidates_total": row.get("prior_candidates_total", 0),
                "required_gate": row.get("required_gate"),
                "proof_evidence_status": row.get("proof_evidence_status"),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_queue_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    payload_rows = payload.get("rows", [])
    if not isinstance(payload_rows, list):
        return rows
    for row in payload_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "item_id": row.get("item_id"),
                "route_id": row.get("route_id"),
                "display_name": row.get("display_name"),
                "route_class": row.get("route_class"),
                "verification_stage": row.get("verification_stage"),
                "priority": row.get("priority"),
                "priority_score": row.get("priority_score"),
                "required_gate": row.get("required_gate"),
                "proof_attempt_mode": row.get("proof_attempt_mode"),
                "required_primitives": row.get("required_primitives", [])[:8],
                "related_proof_obligations": row.get("related_proof_obligations", [])[:8],
                "proof_history_status": row.get("proof_history_status", ""),
                "proof_attempt_positive": row.get("proof_attempt_positive", 0),
                "proof_attempt_negative": row.get("proof_attempt_negative", 0),
                "proof_search_solved": row.get("proof_search_solved", 0),
                "dependency_graph_depth": row.get("dependency_graph_depth", 0),
                "import_cone_size": row.get("import_cone_size", 0),
                "source_trust_level": row.get("source_trust_level", ""),
                "source_trust_calibration_status": row.get("source_trust_calibration_status", ""),
                "kernel_smoke_related_verified": row.get("kernel_smoke_related_verified", 0),
                "kernel_smoke_related_total": row.get("kernel_smoke_related_total", 0),
                "semantic_faithfulness_score": row.get("semantic_faithfulness_score", 0),
                "semantic_faithfulness_status": row.get("semantic_faithfulness_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _goal_conditioned_minimal_formalization_plan_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    plan_rows = payload.get("rows", [])
    if not isinstance(plan_rows, list):
        return rows
    for row in plan_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "goal_plan_id": row.get("goal_plan_id"),
                "route_id": row.get("route_id"),
                "display_name": row.get("display_name"),
                "route_class": row.get("route_class"),
                "recommended_action": row.get("recommended_action", ""),
                "best_route_cost": row.get("best_route_cost", 0),
                "goal_conditioned_cost": row.get("goal_conditioned_cost", 0),
                "route_cost_breakdown": row.get("route_cost_breakdown", {}),
                "route_efficiency_score": row.get("route_efficiency_score", 0),
                "selected_primitives": row.get("selected_primitives", [])[:8],
                "existing_reuse_nodes": row.get("existing_reuse_nodes", [])[:4],
                "wrapper_nodes": row.get("wrapper_nodes", [])[:4],
                "bridge_nodes": row.get("bridge_nodes", [])[:4],
                "source_discovery_nodes": row.get("source_discovery_nodes", [])[:4],
                "first_principles_nodes": row.get("first_principles_nodes", [])[:4],
                "minimal_additional_formalization_nodes": row.get(
                    "minimal_additional_formalization_nodes",
                    [],
                )[:6],
                "minimal_cut_summary": row.get("minimal_cut_summary", {}),
                "route_dag_contract": row.get("route_dag_contract", {}),
                "and_or_plan": _compact_graph_preview(row.get("and_or_plan", {})),
                "informal_knowledge_dag": _compact_graph_preview(
                    row.get("informal_knowledge_dag", {})
                ),
                "lean_realization_dag": _compact_graph_preview(
                    row.get("lean_realization_dag", {})
                ),
                "route_revision_triggers": row.get("route_revision_triggers", [])[:8],
                "portable_work_packets": row.get("portable_work_packets", [])[:6],
                "do_not_formalize_now": row.get("do_not_formalize_now", [])[:8],
                "next_work_packets": row.get("next_work_packets", [])[:6],
                "route_summary": row.get("route_summary", ""),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _compact_graph_preview(graph: Any) -> dict[str, object]:
    if not isinstance(graph, dict):
        return {}
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    return {
        "n_nodes": len(nodes) if isinstance(nodes, list) else 0,
        "n_edges": len(edges) if isinstance(edges, list) else 0,
        "nodes": nodes[:6] if isinstance(nodes, list) else [],
        "edges": edges[:6] if isinstance(edges, list) else [],
        "boundary": graph.get("boundary", ""),
    }


def _formal_verifier_replay_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    payload_rows = payload.get("tasks", [])
    if not isinstance(payload_rows, list):
        return rows
    for row in payload_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "replay_id": row.get("replay_id"),
                "source_queue_item_id": row.get("source_queue_item_id"),
                "route_id": row.get("route_id"),
                "display_name": row.get("display_name"),
                "replay_mode": row.get("replay_mode"),
                "replay_priority_score": row.get("replay_priority_score"),
                "acceptance_gate": row.get("acceptance_gate"),
                "subclaim_replay_obligations": row.get("subclaim_replay_obligations", [])[:8],
                "kernel_smoke_related_verified": row.get("kernel_smoke_related_verified", 0),
                "kernel_smoke_related_total": row.get("kernel_smoke_related_total", 0),
                "proof_search_solved": row.get("proof_search_solved", 0),
                "source_trust_calibration_status": row.get("source_trust_calibration_status", ""),
                "semantic_faithfulness_status": row.get("semantic_faithfulness_status", ""),
                "required_kernel_boundary": row.get("required_kernel_boundary", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_calibration_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    payload_rows = payload.get("rows", [])
    if not isinstance(payload_rows, list):
        return rows
    for row in payload_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "calibration_id": row.get("calibration_id"),
                "replay_id": row.get("replay_id"),
                "route_id": row.get("route_id"),
                "display_name": row.get("display_name"),
                "replay_mode": row.get("replay_mode"),
                "attempted": row.get("attempted", False),
                "n_attempts": row.get("n_attempts", 0),
                "replay_calibration_status": row.get("replay_calibration_status", ""),
                "full_route_proof_status": row.get("full_route_proof_status", ""),
                "first_error_category": row.get("first_error_category", ""),
                "replay_policy_update": row.get("replay_policy_update", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    packets = payload.get("packets", [])
    if not isinstance(packets, list):
        return rows
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        rows.append(
            {
                "packet_id": packet.get("packet_id"),
                "replay_id": packet.get("replay_id"),
                "route_id": packet.get("route_id"),
                "display_name": packet.get("display_name"),
                "repair_class": packet.get("repair_class"),
                "first_error_category": packet.get("first_error_category"),
                "candidate_bridge_lemma_name": packet.get("candidate_bridge_lemma_name"),
                "subclaim_replay_obligations": packet.get("subclaim_replay_obligations", [])[:8],
                "retrieval_hit_obligations": packet.get("retrieval_hit_obligations", [])[:8],
                "acceptance_gate": packet.get("acceptance_gate", ""),
                "repair_acceptance_gate": packet.get("repair_acceptance_gate", ""),
                "proof_evidence_boundary": packet.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_application_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list):
        return rows
    for task in tasks:
        if not isinstance(task, dict):
            continue
        rows.append(
            {
                "application_id": task.get("application_id"),
                "packet_id": task.get("packet_id"),
                "replay_id": task.get("replay_id"),
                "route_id": task.get("route_id"),
                "display_name": task.get("display_name"),
                "repair_class": task.get("repair_class"),
                "application_mode": task.get("application_mode"),
                "candidate_bridge_lemma_name": task.get("candidate_bridge_lemma_name"),
                "artifact_path": task.get("artifact_path"),
                "subclaim_replay_obligations": task.get("subclaim_replay_obligations", [])[:8],
                "verification_commands": task.get("verification_commands", [])[:3],
                "proof_evidence_boundary": task.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_application_validation_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    validation_rows = payload.get("rows", [])
    if not isinstance(validation_rows, list):
        return rows
    for row in validation_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "validation_id": row.get("validation_id"),
                "application_id": row.get("application_id"),
                "packet_id": row.get("packet_id"),
                "replay_id": row.get("replay_id"),
                "route_id": row.get("route_id"),
                "display_name": row.get("display_name"),
                "validation_status": row.get("validation_status"),
                "local_lean_checked": row.get("local_lean_checked", False),
                "local_lean_compiled": row.get("local_lean_compiled", False),
                "placeholder_free": row.get("placeholder_free", False),
                "static_checks_ok": row.get("static_checks_ok", False),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_execution_queue_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    queue = payload.get("queue", [])
    if not isinstance(queue, list):
        return rows
    for row in queue:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "execution_id": row.get("execution_id"),
                "execution_priority_rank": row.get("execution_priority_rank"),
                "application_id": row.get("application_id"),
                "validation_id": row.get("validation_id"),
                "packet_id": row.get("packet_id"),
                "replay_id": row.get("replay_id"),
                "route_id": row.get("route_id"),
                "display_name": row.get("display_name"),
                "execution_status": row.get("execution_status"),
                "priority_score": row.get("priority_score"),
                "application_mode": row.get("application_mode"),
                "candidate_bridge_lemma_name": row.get("candidate_bridge_lemma_name"),
                "artifact_path": row.get("artifact_path"),
                "local_lean_compiled": row.get("local_lean_compiled", False),
                "subclaim_replay_obligations": row.get("subclaim_replay_obligations", [])[:8],
                "command_plan": row.get("command_plan", [])[:3],
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_prompt_packets_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    packets = payload.get("packets", [])
    if not isinstance(packets, list):
        return rows
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        contract = packet.get("expected_output_contract")
        if not isinstance(contract, dict):
            contract = {}
        rows.append(
            {
                "prompt_packet_id": packet.get("prompt_packet_id"),
                "execution_id": packet.get("execution_id"),
                "execution_priority_rank": packet.get("execution_priority_rank"),
                "display_name": packet.get("display_name"),
                "execution_status": packet.get("execution_status"),
                "candidate_bridge_lemma_name": packet.get("candidate_bridge_lemma_name"),
                "artifact_path": packet.get("artifact_path"),
                "local_lean_compiled": packet.get("local_lean_compiled", False),
                "prompt_chars": len(str(packet.get("prompt", ""))),
                "contract_claim_status": contract.get("claim_status", ""),
                "contract_promotion_gate": contract.get("promotion_gate", ""),
                "proof_evidence_status": packet.get("proof_evidence_status", ""),
                "proof_evidence_boundary": packet.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_response_validation_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    validation_rows = payload.get("rows", [])
    if not isinstance(validation_rows, list):
        return rows
    for row in validation_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "response_validation_id": row.get("response_validation_id"),
                "prompt_packet_id": row.get("prompt_packet_id"),
                "execution_id": row.get("execution_id"),
                "display_name": row.get("display_name"),
                "candidate_bridge_lemma_name": row.get("candidate_bridge_lemma_name"),
                "response_present": row.get("response_present", False),
                "response_contract_ok": row.get("response_contract_ok", False),
                "acceptance_status": row.get("acceptance_status", ""),
                "claim_status": row.get("claim_status", ""),
                "replay_calibration_status": row.get("replay_calibration_status", ""),
                "kernel_verified": row.get("kernel_verified", False),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_response_promotion_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    promotion_rows = payload.get("rows", [])
    if not isinstance(promotion_rows, list):
        return rows
    for row in promotion_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "promotion_id": row.get("promotion_id"),
                "response_validation_id": row.get("response_validation_id"),
                "prompt_packet_id": row.get("prompt_packet_id"),
                "execution_id": row.get("execution_id"),
                "display_name": row.get("display_name"),
                "candidate_bridge_lemma_name": row.get("candidate_bridge_lemma_name"),
                "source_acceptance_status": row.get("source_acceptance_status", ""),
                "promotion_status": row.get("promotion_status", ""),
                "promotion_ready": row.get("promotion_ready", False),
                "action_type": row.get("action_type", ""),
                "required_gate": row.get("required_gate", ""),
                "evidence_paths": row.get("evidence_paths", [])[:4],
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_rerun_queue_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    queue_rows = payload.get("rows", [])
    if not isinstance(queue_rows, list):
        return rows
    for row in queue_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "rerun_id": row.get("rerun_id"),
                "response_validation_id": row.get("response_validation_id"),
                "promotion_id": row.get("promotion_id"),
                "replay_id": row.get("replay_id"),
                "display_name": row.get("display_name"),
                "candidate_bridge_lemma_name": row.get("candidate_bridge_lemma_name"),
                "patched_artifact_path": row.get("patched_artifact_path", ""),
                "rerun_status": row.get("rerun_status", ""),
                "patched_artifact_exists": row.get("patched_artifact_exists", False),
                "rerun_commands": row.get("rerun_commands", [])[:3],
                "required_gate": row.get("required_gate", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_rerun_attempt_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    attempt_rows = payload.get("rows", [])
    if not isinstance(attempt_rows, list):
        return rows
    for row in attempt_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "rerun_attempt_id": row.get("rerun_attempt_id"),
                "rerun_id": row.get("rerun_id"),
                "replay_id": row.get("replay_id"),
                "display_name": row.get("display_name"),
                "patched_artifact_path": row.get("patched_artifact_path", ""),
                "rerun_attempt_status": row.get("rerun_attempt_status", ""),
                "local_lean_checked": row.get("local_lean_checked", False),
                "local_lean_compiled": row.get("local_lean_compiled", False),
                "contains_patch_proposal_marker": row.get(
                    "contains_patch_proposal_marker",
                    False,
                ),
                "residual_formal_gaps": row.get("residual_formal_gaps", [])[:5],
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_rerun_calibration_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    calibration_rows = payload.get("rows", [])
    if not isinstance(calibration_rows, list):
        return rows
    for row in calibration_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "rerun_calibration_id": row.get("rerun_calibration_id"),
                "rerun_id": row.get("rerun_id"),
                "rerun_attempt_id": row.get("rerun_attempt_id"),
                "replay_id": row.get("replay_id"),
                "display_name": row.get("display_name"),
                "patch_rerun_calibration_status": row.get(
                    "patch_rerun_calibration_status",
                    "",
                ),
                "local_lean_compiled": row.get("local_lean_compiled", False),
                "n_residual_formal_gaps": row.get("n_residual_formal_gaps", 0),
                "full_route_proof_status": row.get("full_route_proof_status", ""),
                "next_action": row.get("next_action", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_rerun_residual_obligation_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    residual_rows = payload.get("rows", [])
    if not isinstance(residual_rows, list):
        return rows
    for row in residual_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "residual_obligation_id": row.get("residual_obligation_id"),
                "rerun_calibration_id": row.get("rerun_calibration_id"),
                "replay_id": row.get("replay_id"),
                "display_name": row.get("display_name"),
                "residual_gap": row.get("residual_gap"),
                "residual_kind": row.get("residual_kind"),
                "source_support_classification": row.get(
                    "source_support_classification",
                    "",
                ),
                "action_class": row.get("action_class", ""),
                "exact_proof_bank_obligation": row.get("exact_proof_bank_obligation", ""),
                "proof_bank_bridge_obligations": row.get(
                    "proof_bank_bridge_obligations",
                    [],
                )[:5],
                "local_candidate_declarations": row.get(
                    "local_candidate_declarations",
                    [],
                )[:3],
                "next_action": row.get("next_action", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    packets = payload.get("packets", [])
    if not isinstance(packets, list):
        return rows
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        contract = packet.get("expected_output_contract")
        if not isinstance(contract, dict):
            contract = {}
        rows.append(
            {
                "prompt_packet_id": packet.get("prompt_packet_id"),
                "residual_obligation_id": packet.get("residual_obligation_id"),
                "rerun_calibration_id": packet.get("rerun_calibration_id"),
                "replay_id": packet.get("replay_id"),
                "display_name": packet.get("display_name"),
                "residual_gap": packet.get("residual_gap"),
                "action_class": packet.get("action_class", ""),
                "source_support_classification": packet.get(
                    "source_support_classification",
                    "",
                ),
                "patched_artifact_path": packet.get("patched_artifact_path", ""),
                "patched_artifact_readable": packet.get(
                    "patched_artifact_readable",
                    False,
                ),
                "prompt_chars": len(str(packet.get("prompt", ""))),
                "contract_claim_status": contract.get("claim_status", ""),
                "contract_required_output_mode": contract.get("required_output_mode", ""),
                "contract_promotion_gate": contract.get("promotion_gate", ""),
                "proof_evidence_status": packet.get("proof_evidence_status", ""),
                "proof_evidence_boundary": packet.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_rerun_residual_autoworker_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    worker_rows = payload.get("rows", [])
    if not isinstance(worker_rows, list):
        return rows
    for row in worker_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "response_id": row.get("response_id"),
                "prompt_packet_id": row.get("prompt_packet_id"),
                "residual_obligation_id": row.get("residual_obligation_id"),
                "rerun_calibration_id": row.get("rerun_calibration_id"),
                "display_name": row.get("display_name"),
                "residual_gap": row.get("residual_gap"),
                "action_class": row.get("action_class", ""),
                "worker_status": row.get("worker_status", ""),
                "proposed_lean_artifact_path": row.get("proposed_lean_artifact_path", ""),
                "source_discovery_queries": row.get("source_discovery_queries", [])[:3],
                "remaining_residual_formal_gaps": row.get(
                    "remaining_residual_formal_gaps",
                    [],
                )[:5],
                "kernel_verified": row.get("kernel_verified", False),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_rerun_residual_response_validation_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    validation_rows = payload.get("rows", [])
    if not isinstance(validation_rows, list):
        return rows
    for row in validation_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "residual_response_validation_id": row.get(
                    "residual_response_validation_id"
                ),
                "prompt_packet_id": row.get("prompt_packet_id"),
                "residual_obligation_id": row.get("residual_obligation_id"),
                "rerun_calibration_id": row.get("rerun_calibration_id"),
                "display_name": row.get("display_name"),
                "residual_gap": row.get("residual_gap"),
                "action_class": row.get("action_class", ""),
                "response_present": row.get("response_present", False),
                "response_contract_ok": row.get("response_contract_ok", False),
                "acceptance_status": row.get("acceptance_status", ""),
                "patch_rerun_calibration_status": row.get(
                    "patch_rerun_calibration_status",
                    "",
                ),
                "kernel_verified": row.get("kernel_verified", False),
                "remaining_residual_formal_gaps": row.get(
                    "remaining_residual_formal_gaps",
                    [],
                )[:5],
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_replay_repair_patch_rerun_residual_followup_queue_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    followup_rows = payload.get("rows", [])
    if not isinstance(followup_rows, list):
        return rows
    for row in followup_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "followup_id": row.get("followup_id"),
                "residual_response_validation_id": row.get(
                    "residual_response_validation_id"
                ),
                "prompt_packet_id": row.get("prompt_packet_id"),
                "residual_obligation_id": row.get("residual_obligation_id"),
                "rerun_calibration_id": row.get("rerun_calibration_id"),
                "display_name": row.get("display_name"),
                "residual_gap": row.get("residual_gap"),
                "action_class": row.get("action_class", ""),
                "followup_kind": row.get("followup_kind", ""),
                "followup_status": row.get("followup_status", ""),
                "owner_agent": row.get("owner_agent", ""),
                "priority": row.get("priority", ""),
                "proposed_lean_artifact_path": row.get(
                    "proposed_lean_artifact_path",
                    "",
                ),
                "proposed_artifact_exists": row.get(
                    "proposed_artifact_exists",
                    False,
                ),
                "source_discovery_queries": row.get("source_discovery_queries", [])[:3],
                "execution_commands": row.get("execution_commands", [])[:2],
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_agentic_proof_strategy_plan_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    strategy_rows = payload.get("rows", [])
    if not isinstance(strategy_rows, list):
        return rows
    for row in strategy_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "strategy_id": row.get("strategy_id"),
                "rank": row.get("rank"),
                "followup_id": row.get("followup_id"),
                "display_name": row.get("display_name"),
                "residual_gap": row.get("residual_gap"),
                "followup_kind": row.get("followup_kind", ""),
                "followup_status": row.get("followup_status", ""),
                "agentic_strategy_kind": row.get("agentic_strategy_kind", ""),
                "paper_patterns": row.get("paper_patterns", [])[:4],
                "required_live_tools": row.get("required_live_tools", [])[:6],
                "evaluator_gates": row.get("evaluator_gates", [])[:5],
                "global_goal_cache_keys": row.get("global_goal_cache_keys", [])[:5],
                "candidate_database_key": row.get("candidate_database_key", ""),
                "priority_score": row.get("priority_score", 0),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_agentic_proof_candidate_evaluation_queue_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    queue_rows = payload.get("rows", [])
    if not isinstance(queue_rows, list):
        return rows
    for row in queue_rows:
        if not isinstance(row, dict):
            continue
        preview = {
            "candidate_evaluation_id": row.get("candidate_evaluation_id"),
            "rank": row.get("rank"),
            "strategy_id": row.get("strategy_id"),
            "display_name": row.get("display_name"),
            "residual_gap": row.get("residual_gap"),
            "generation_mode": row.get("generation_mode", ""),
            "candidate_database_key": row.get("candidate_database_key", ""),
            "candidate_lineage_key": row.get("candidate_lineage_key", ""),
            "attempt_budget": row.get("attempt_budget", 0),
            "status": row.get("status", ""),
            "evaluator_pool": row.get("evaluator_pool", [])[:8],
            "live_tool_sequence": row.get("live_tool_sequence", [])[:8],
            "promotion_gate": row.get("promotion_gate", ""),
            "proof_evidence_status": row.get("proof_evidence_status", ""),
            "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
        }
        preview.update(_kernel_overlay_context_preview_fields(row))
        rows.append(preview)
        if len(rows) >= max_rows:
            break
    return rows


def _kernel_overlay_context_preview_fields(row: dict[str, Any]) -> dict[str, object]:
    context = row.get("kernel_overlay_context", {})
    if not isinstance(context, dict) or not context:
        return {
            "kernel_overlay_context_present": False,
            "kernel_overlay_work_item_id": "",
            "kernel_overlay_seed_id": "",
            "kernel_overlay_source_claim_id": "",
            "kernel_overlay_verified_subclaims": [],
            "kernel_overlay_target_blockers": [],
            "kernel_overlay_source_discovery_queries": [],
        }
    return {
        "kernel_overlay_context_present": True,
        "kernel_overlay_work_item_id": str(context.get("work_item_id", "")),
        "kernel_overlay_seed_id": str(context.get("seed_id", "")),
        "kernel_overlay_source_claim_id": str(context.get("source_claim_id", "")),
        "kernel_overlay_verified_subclaims": _str_list(
            context.get("already_kernel_verified_subclaims", [])
        )[:6],
        "kernel_overlay_target_blockers": _str_list(
            context.get("target_blockers", [])
        )[:6],
        "kernel_overlay_source_discovery_queries": _str_list(
            context.get("source_discovery_queries", [])
        )[:4],
    }


def _formal_verifier_agentic_proof_safety_policy_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    policy_rows = payload.get("rows", [])
    if not isinstance(policy_rows, list):
        return rows
    for row in policy_rows:
        if not isinstance(row, dict):
            continue
        bounded_edit_policy = row.get("bounded_edit_policy", {})
        if not isinstance(bounded_edit_policy, dict):
            bounded_edit_policy = {}
        preview = {
            "safety_policy_id": row.get("safety_policy_id"),
            "rank": row.get("rank"),
            "candidate_evaluation_id": row.get("candidate_evaluation_id"),
            "display_name": row.get("display_name"),
            "residual_gap": row.get("residual_gap"),
            "generation_mode": row.get("generation_mode", ""),
            "policy_status": row.get("policy_status", ""),
            "goal_cache_key": row.get("goal_cache_key", ""),
            "bounded_edit_required": bounded_edit_policy.get(
                "bounded_edit_required",
                False,
            ),
            "bounded_edit_start_marker": bounded_edit_policy.get(
                "start_marker",
                "",
            ),
            "bounded_edit_end_marker": bounded_edit_policy.get("end_marker", ""),
            "anti_cheat_checks": row.get("anti_cheat_checks", [])[:8],
            "forbidden_tokens": row.get("forbidden_tokens", [])[:8],
            "required_static_checks": row.get("required_static_checks", [])[:8],
            "safeverify_gate": row.get("safeverify_gate", ""),
            "proof_evidence_status": row.get("proof_evidence_status", ""),
            "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
        }
        preview.update(_kernel_overlay_context_preview_fields(row))
        rows.append(preview)
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_agentic_proof_attempt_population_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    population_rows = payload.get("rows", [])
    if not isinstance(population_rows, list):
        return rows
    for row in population_rows:
        if not isinstance(row, dict):
            continue
        preview = {
            "population_entry_id": row.get("population_entry_id"),
            "rank": row.get("rank"),
            "safety_policy_id": row.get("safety_policy_id"),
            "display_name": row.get("display_name"),
            "residual_gap": row.get("residual_gap"),
            "generation_mode": row.get("generation_mode", ""),
            "population_bucket": row.get("population_bucket", ""),
            "attempt_status": row.get("attempt_status", ""),
            "goal_cache_key": row.get("goal_cache_key", ""),
            "candidate_lineage_key": row.get("candidate_lineage_key", ""),
            "proof_sketch_population_key": row.get(
                "proof_sketch_population_key",
                "",
            ),
            "selection_weight": row.get("selection_weight", 0),
            "diagnostic_signature": row.get("diagnostic_signature", ""),
            "lessons_learned": row.get("lessons_learned", [])[:4],
            "sampler_policy": row.get("sampler_policy", ""),
            "promotion_gate": row.get("promotion_gate", ""),
            "proof_evidence_status": row.get("proof_evidence_status", ""),
            "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
        }
        preview.update(_kernel_overlay_context_preview_fields(row))
        rows.append(preview)
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_agentic_proof_execution_queue_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    execution_rows = payload.get("rows", [])
    if not isinstance(execution_rows, list):
        return rows
    for row in execution_rows:
        if not isinstance(row, dict):
            continue
        preview = {
            "execution_queue_id": row.get("execution_queue_id"),
            "rank": row.get("rank"),
            "population_entry_id": row.get("population_entry_id"),
            "safety_policy_id": row.get("safety_policy_id"),
            "display_name": row.get("display_name"),
            "residual_gap": row.get("residual_gap"),
            "generation_mode": row.get("generation_mode", ""),
            "population_bucket": row.get("population_bucket", ""),
            "execution_status": row.get("execution_status", ""),
            "candidate_artifact_path": row.get("candidate_artifact_path", ""),
            "execution_transcript_path": row.get("execution_transcript_path", ""),
            "proof_state_provider_plan": row.get(
                "proof_state_provider_plan",
                [],
            )[:5],
            "proof_route_dag_plan": row.get("proof_route_dag_plan", [])[:4],
            "verified_sketch_gate_plan": row.get(
                "verified_sketch_gate_plan",
                [],
            )[:4],
            "blueprint_export_plan": row.get("blueprint_export_plan", [])[:4],
            "promotion_gate": row.get("promotion_gate", ""),
            "proof_evidence_status": row.get("proof_evidence_status", ""),
            "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
        }
        preview.update(_kernel_overlay_context_preview_fields(row))
        rows.append(preview)
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_agentic_proof_execution_materializer_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    materializer_rows = payload.get("rows", [])
    if not isinstance(materializer_rows, list):
        return rows
    for row in materializer_rows:
        if not isinstance(row, dict):
            continue
        live_request = row.get("live_proof_state_request", {})
        if not isinstance(live_request, dict):
            live_request = {}
        rows.append(
            {
                "materialization_id": row.get("materialization_id"),
                "execution_queue_id": row.get("execution_queue_id"),
                "display_name": row.get("display_name"),
                "target_theorem_name": row.get("target_theorem_name", ""),
                "materialization_status": row.get("materialization_status", ""),
                "candidate_artifact_path": row.get("candidate_artifact_path", ""),
                "target_lean_file": row.get("target_lean_file", ""),
                "target_lean_line": row.get("target_lean_line"),
                "target_lean_declaration": row.get("target_lean_declaration", ""),
                "live_goal_location_ready": row.get("live_goal_location_ready"),
                "live_proof_state_request_present": bool(live_request),
                "live_proof_state_request_id": live_request.get("request_id", ""),
                "live_proof_state_provider_preferences": live_request.get(
                    "provider_preferences",
                    [],
                ),
                "kernel_verified": row.get("kernel_verified"),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_agentic_proof_execution_artifact_verifier_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    verifier_rows = payload.get("rows", [])
    if not isinstance(verifier_rows, list):
        return rows
    for row in verifier_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "artifact_verification_id": row.get("artifact_verification_id"),
                "materialization_id": row.get("materialization_id"),
                "execution_queue_id": row.get("execution_queue_id"),
                "display_name": row.get("display_name"),
                "target_theorem_name": row.get("target_theorem_name", ""),
                "candidate_artifact_path": row.get("candidate_artifact_path", ""),
                "execution_transcript_path": row.get("execution_transcript_path", ""),
                "execution_transcript_event_id": row.get(
                    "execution_transcript_event_id",
                    "",
                ),
                "execution_transcript_event_written": row.get(
                    "execution_transcript_event_written"
                ),
                "target_lean_declaration": row.get("target_lean_declaration", ""),
                "target_lean_line": row.get("target_lean_line"),
                "live_proof_state_request_id": row.get(
                    "live_proof_state_request_id",
                    "",
                ),
                "live_proof_state_request_valid": row.get(
                    "live_proof_state_request_valid"
                ),
                "live_proof_state_request_status": row.get(
                    "live_proof_state_request_status",
                    "",
                ),
                "live_proof_state_requested_tools": row.get(
                    "live_proof_state_requested_tools",
                    [],
                ),
                "local_lean_checked": row.get("local_lean_checked"),
                "local_lean_compiled": row.get("local_lean_compiled"),
                "artifact_kernel_verified": row.get("artifact_kernel_verified"),
                "source_theorem_kernel_verified": row.get(
                    "source_theorem_kernel_verified"
                ),
                "verification_status": row.get("verification_status", ""),
                "verifier": row.get("verifier", ""),
                "verification_strength": row.get("verification_strength", ""),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_agentic_proof_trace_memory_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    memory_rows = payload.get("rows", [])
    if not isinstance(memory_rows, list):
        return rows
    for row in memory_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "trace_memory_id": row.get("trace_memory_id"),
                "execution_transcript_path": row.get(
                    "execution_transcript_path",
                    "",
                ),
                "execution_queue_id": row.get("execution_queue_id"),
                "artifact_verification_id": row.get("artifact_verification_id", ""),
                "live_proof_state_request_id": row.get(
                    "live_proof_state_request_id",
                    "",
                ),
                "goal_cache_key": row.get("goal_cache_key", ""),
                "candidate_lineage_key": row.get("candidate_lineage_key", ""),
                "target_theorem_name": row.get("target_theorem_name", ""),
                "target_lean_declaration": row.get("target_lean_declaration", ""),
                "event_types": row.get("event_types", []),
                "artifact_kernel_verified": row.get("artifact_kernel_verified"),
                "source_theorem_kernel_verified": row.get(
                    "source_theorem_kernel_verified"
                ),
                "learned_outcome": row.get("learned_outcome", ""),
                "diagnostic_signature": row.get("diagnostic_signature", ""),
                "sampler_policy_update": row.get("sampler_policy_update", ""),
                "replay_priority_delta": row.get("replay_priority_delta"),
                "repair_signals": row.get("repair_signals", [])[:5],
                "required_followups": row.get("required_followups", [])[:5],
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_agentic_proof_source_theorem_promotion_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    promotion_rows = payload.get("rows", [])
    if not isinstance(promotion_rows, list):
        return rows
    for row in promotion_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "source_theorem_promotion_id": row.get(
                    "source_theorem_promotion_id"
                ),
                "artifact_verification_id": row.get("artifact_verification_id"),
                "materialization_id": row.get("materialization_id"),
                "execution_queue_id": row.get("execution_queue_id"),
                "display_name": row.get("display_name"),
                "target_theorem_name": row.get("target_theorem_name", ""),
                "candidate_artifact_path": row.get("candidate_artifact_path", ""),
                "target_lean_declaration": row.get("target_lean_declaration", ""),
                "artifact_kernel_verified": row.get("artifact_kernel_verified"),
                "source_theorem_kernel_verified": row.get(
                    "source_theorem_kernel_verified"
                ),
                "source_theorem_target_known": row.get("source_theorem_target_known"),
                "promotion_status": row.get("promotion_status", ""),
                "owner_agent": row.get("owner_agent", ""),
                "action_type": row.get("action_type", ""),
                "priority": row.get("priority", ""),
                "required_gate": row.get("required_gate", ""),
                "required_inputs": row.get("required_inputs", [])[:6],
                "command_plan": row.get("command_plan", [])[:5],
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formal_verifier_agentic_proof_source_theorem_target_resolution_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    resolution_rows = payload.get("rows", [])
    if not isinstance(resolution_rows, list):
        return rows
    for row in resolution_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "target_resolution_id": row.get("target_resolution_id"),
                "source_theorem_promotion_id": row.get("source_theorem_promotion_id"),
                "artifact_verification_id": row.get("artifact_verification_id"),
                "execution_queue_id": row.get("execution_queue_id"),
                "display_name": row.get("display_name"),
                "target_theorem_name": row.get("target_theorem_name", ""),
                "candidate_artifact_path": row.get("candidate_artifact_path", ""),
                "resolution_status": row.get("resolution_status", ""),
                "match_source": row.get("match_source", ""),
                "source_route_id": row.get("source_route_id", ""),
                "source_queue_item_id": row.get("source_queue_item_id", ""),
                "source_replay_id": row.get("source_replay_id", ""),
                "task_id": row.get("task_id", ""),
                "question_id": row.get("question_id", ""),
                "theorem_goal_id": row.get("theorem_goal_id", ""),
                "source_theorem_target_known": row.get("source_theorem_target_known"),
                "source_theorem_statement": row.get("source_theorem_statement", ""),
                "source_theorem_lean_file": row.get("source_theorem_lean_file", ""),
                "artifact_kernel_verified": row.get("artifact_kernel_verified"),
                "action_type": row.get("action_type", ""),
                "required_gate": row.get("required_gate", ""),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _formalization_gap_planner_proof_state_triage_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    triage_rows = payload.get("rows", [])
    if not isinstance(triage_rows, list):
        return rows
    for row in triage_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "triage_item_id": row.get("triage_item_id"),
                "rank": row.get("rank"),
                "display_name": row.get("display_name"),
                "triage_class": row.get("triage_class", ""),
                "owner_agent": row.get("owner_agent", ""),
                "priority_score": row.get("priority_score", 0),
                "applied_prover_attempt_statuses": row.get(
                    "applied_prover_attempt_statuses",
                    [],
                ),
                "applied_prover_diagnostic_signatures": row.get(
                    "applied_prover_diagnostic_signatures",
                    [],
                ),
                "residual_goals": row.get("residual_goals", [])[:5],
                "added_delta_primitives": row.get("added_delta_primitives", [])[:5],
                "recommended_next_action": row.get("recommended_next_action", ""),
                "recommended_tools": row.get("recommended_tools", [])[:6],
                "required_artifacts": row.get("required_artifacts", [])[:5],
                "required_gate": row.get("required_gate", ""),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _huggingface_lean_source_revalidation_queue_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    raw_rows = payload.get("revalidation_queue", [])
    if not isinstance(raw_rows, list):
        return rows
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "revalidation_id": row.get("revalidation_id"),
                "source_id": row.get("source_id"),
                "dataset_id": row.get("dataset_id"),
                "url": row.get("url"),
                "priority": row.get("priority"),
                "relevance_class": row.get("relevance_class"),
                "retrieval_role": row.get("retrieval_role"),
                "ingestion_mode": row.get("ingestion_mode"),
                "license": row.get("license", ""),
                "num_rows": row.get("num_rows", 0),
                "parquet_shards": row.get("parquet_shards", 0),
                "revalidation_status": row.get("revalidation_status"),
                "owner_agent": row.get("owner_agent"),
                "action_type": row.get("action_type"),
                "required_gate": row.get("required_gate"),
                "license_review_required": row.get("license_review_required"),
                "do_not_vendor": row.get("do_not_vendor"),
                "kernel_verified_rows": row.get("kernel_verified_rows", 0),
                "proof_evidence_ready": row.get("proof_evidence_ready", 0),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _huggingface_lean_source_revalidation_tasks_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    raw_rows = payload.get("rows", [])
    if not isinstance(raw_rows, list):
        return rows
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "task_id": row.get("task_id"),
                "revalidation_id": row.get("revalidation_id"),
                "source_id": row.get("source_id"),
                "dataset_id": row.get("dataset_id"),
                "priority": row.get("priority"),
                "priority_score": row.get("priority_score"),
                "relevance_class": row.get("relevance_class"),
                "retrieval_role": row.get("retrieval_role"),
                "task_status": row.get("task_status"),
                "owner_agent": row.get("owner_agent"),
                "action_type": row.get("action_type"),
                "sample_strategy": row.get("sample_strategy"),
                "sample_size": row.get("sample_size", 0),
                "sample_seed": row.get("sample_seed"),
                "license_review_required": row.get("license_review_required"),
                "local_work_dir": row.get("local_work_dir"),
                "required_gate": row.get("required_gate"),
                "kernel_verified_rows": row.get("kernel_verified_rows", 0),
                "proof_evidence_ready": row.get("proof_evidence_ready", 0),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _huggingface_lean_source_revalidation_prompt_packets_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    raw_rows = payload.get("packets", [])
    if not isinstance(raw_rows, list):
        return rows
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "prompt_packet_id": row.get("prompt_packet_id"),
                "task_id": row.get("task_id"),
                "source_id": row.get("source_id"),
                "dataset_id": row.get("dataset_id"),
                "priority": row.get("priority"),
                "priority_score": row.get("priority_score"),
                "relevance_class": row.get("relevance_class"),
                "retrieval_role": row.get("retrieval_role"),
                "task_status": row.get("task_status"),
                "sample_strategy": row.get("sample_strategy"),
                "sample_size": row.get("sample_size", 0),
                "license_review_required": row.get("license_review_required"),
                "local_work_dir": row.get("local_work_dir"),
                "required_gate": row.get("required_gate"),
                "expected_output_contract": row.get("expected_output_contract", {}),
                "forbidden_claims": row.get("forbidden_claims", [])[:4],
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _huggingface_lean_source_revalidation_artifact_validation_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    raw_rows = payload.get("rows", [])
    if not isinstance(raw_rows, list):
        return rows
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "validation_id": row.get("validation_id"),
                "task_id": row.get("task_id"),
                "source_id": row.get("source_id"),
                "dataset_id": row.get("dataset_id"),
                "task_status": row.get("task_status"),
                "response_present": row.get("response_present"),
                "response_contract_ok": row.get("response_contract_ok"),
                "sample_manifest_path": row.get("sample_manifest_path"),
                "lean_reconstruction_dir": row.get("lean_reconstruction_dir"),
                "verifier_attempt_log": row.get("verifier_attempt_log"),
                "promotion_manifest_path": row.get("promotion_manifest_path"),
                "sampled_rows": row.get("sampled_rows", 0),
                "reconstructed_artifacts": row.get("reconstructed_artifacts", 0),
                "verifier": row.get("verifier", ""),
                "verification_strength": row.get("verification_strength", ""),
                "kernel_verified_rows": row.get("kernel_verified_rows", 0),
                "proof_evidence_ready": row.get("proof_evidence_ready", 0),
                "artifact_paths_exist": row.get("artifact_paths_exist"),
                "promotion_ready": row.get("promotion_ready"),
                "acceptance_status": row.get("acceptance_status"),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _huggingface_lean_source_revalidation_promotion_preview(
    payload: dict[str, Any],
    *,
    max_rows: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    raw_rows = payload.get("rows", [])
    if not isinstance(raw_rows, list):
        return rows
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "promotion_id": row.get("promotion_id"),
                "validation_id": row.get("validation_id"),
                "task_id": row.get("task_id"),
                "source_id": row.get("source_id"),
                "dataset_id": row.get("dataset_id"),
                "source_acceptance_status": row.get("source_acceptance_status"),
                "response_present": row.get("response_present"),
                "response_contract_ok": row.get("response_contract_ok"),
                "kernel_verified_rows": row.get("kernel_verified_rows", 0),
                "proof_evidence_ready": row.get("proof_evidence_ready", 0),
                "promotion_status": row.get("promotion_status"),
                "promotion_ready": row.get("promotion_ready"),
                "owner_agent": row.get("owner_agent"),
                "action_type": row.get("action_type"),
                "required_gate": row.get("required_gate"),
                "evidence_paths": row.get("evidence_paths", []),
                "proof_evidence_status": row.get("proof_evidence_status", ""),
                "proof_evidence_boundary": row.get("proof_evidence_boundary", ""),
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def _theorem_composition_packet_preview(
    payload: dict[str, Any],
    *,
    max_packets: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    packets = payload.get("packets", [])
    if not isinstance(packets, list):
        return rows
    for packet in packets[:max_packets]:
        if not isinstance(packet, dict):
            continue
        rows.append(
            {
                "packet_id": packet.get("packet_id"),
                "source_claim_id": packet.get("source_claim_id"),
                "question_id": packet.get("question_id"),
                "problem_class": packet.get("problem_class"),
                "status": packet.get("status"),
                "exact_proof_bank_obligations": packet.get("exact_proof_bank_obligations", []),
                "unresolved_primitives": packet.get("unresolved_primitives", []),
                "formal_source_hits": packet.get("formal_source_hits", [])[:5],
                "required_gate": packet.get("required_gate", ""),
                "proof_evidence_boundary": packet.get("proof_evidence_boundary", ""),
                "evidence_paths": packet.get("evidence_paths", []),
            }
        )
    return rows


def _action_priority(action_class: str) -> int:
    return {
        "add_minimal_wrapper": 0,
        "design_bridge_lemma": 1,
        "port_external_source": 2,
        "design_from_first_principles": 3,
    }.get(action_class, 9)


def _query_hint(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("primitive", "problem_classes", "theorem_goals"):
        value = row.get(key, "")
        if isinstance(value, list):
            parts.extend(str(item) for item in value[:4])
        elif value:
            parts.append(str(value))
    parts.extend(str(item) for item in row.get("proof_bank_bridge_obligations", [])[:3])
    parts.extend(str(item) for item in row.get("local_candidate_declarations", [])[:3])
    return " ".join(parts)


def _markdown_report(payload: dict[str, object]) -> str:
    proof = dict(payload.get("proof_evidence", {}) or {})
    kernel_overlays = dict(payload.get("kernel_proof_evidence_overlays", {}) or {})
    kernel_alignment = dict(payload.get("kernel_proof_overlay_alignment", {}) or {})
    rag = dict(payload.get("rag_provider_evidence", {}) or {})
    retrieval = dict(payload.get("retrieval_ablation_evidence", {}) or {})
    queue = dict(payload.get("formal_capacity_queue", {}) or {})
    composition = dict(payload.get("theorem_composition_handoff", {}) or {})
    lines = [
        "# RAG Collaboration Handoff",
        "",
        f"- Source run: `{payload.get('source_run_dir')}`",
        f"- Proof bank: `{proof.get('proofs_kernel_verified')}/{proof.get('proofs_total')}` kernel verified",
        f"- Proof-search local rerun: `{proof.get('proof_search_kernel_rerun_local_lean_verified')}/"
        f"{proof.get('proof_search_kernel_rerun_local_lean_total')}` kernel verified "
        f"via `{proof.get('proof_search_kernel_rerun_local_lean_verifier')}`",
        f"- Proof fingerprint: `{proof.get('proof_bank_fingerprint')}`",
        f"- Standalone kernel proof overlays: `{kernel_overlays.get('standalone_kernel_proof_audits')}` audits, "
        f"`{kernel_overlays.get('standalone_kernel_verified_distinct_obligations')}` distinct obligations "
        f"(`{kernel_overlays.get('standalone_kernel_proof_audits_matching_system_fingerprint')}` fingerprint-matched audits, "
        f"`{kernel_overlays.get('standalone_kernel_verified_distinct_current_fingerprint_obligations')}` fingerprint-matched obligations)",
        f"- Kernel overlay alignment: `{kernel_alignment.get('theorem_composition_packets_with_kernel_overlay')}` composition packets, "
        f"`{kernel_alignment.get('formal_verifier_queue_rows_with_kernel_overlay')}` queue rows, "
        f"`{kernel_alignment.get('formal_verifier_replay_tasks_with_kernel_overlay')}` replay tasks, "
        f"`{kernel_alignment.get('kernel_overlay_composition_work_items')}` composition work items, "
        f"`{kernel_alignment.get('kernel_overlay_composition_agentic_seeds')}` agentic seeds",
        f"- Lean RAG active: `{rag.get('lean_rag_dependency_graph_enabled')}`",
        f"- Lean RAG DB: `{rag.get('lean_rag_dependency_graph_path')}`",
        f"- Lean RAG DB health: `{rag.get('lean_rag_dependency_health_status')}` "
        f"(fallback `{rag.get('lean_rag_dependency_fallback_used')}`: "
        f"`{rag.get('lean_rag_dependency_fallback_reason')}`)",
        f"- Lean RAG package: `{rag.get('lean_rag_package_contract_ok')}` at `{rag.get('lean_rag_package_branch')}` / `{str(rag.get('lean_rag_package_commit') or '')[:12]}`",
        f"- Lean RAG seed lanes: `{', '.join(rag.get('lean_rag_package_seed_lanes', []))}`",
        f"- Lean RAG target sources: `{rag.get('lean_rag_package_target_sources_present')}/{rag.get('lean_rag_package_target_sources')}` present "
        f"(missing `{', '.join(rag.get('lean_rag_package_missing_target_sources', []) or [])}`)",
        f"- Lean RAG registry candidates: `{rag.get('lean_rag_package_registry_expansion_candidates')}` "
        f"(`{', '.join(rag.get('lean_rag_package_registry_expansion_candidate_names', []) or [])}`)",
        f"- Retrieval recall/MRR: `{rag.get('formal_source_retrieval_recall_at_k')}` / `{rag.get('formal_source_retrieval_mrr')}`",
        f"- External retrieval recall/MRR: `{rag.get('formal_source_retrieval_external_recall_at_k')}` / `{rag.get('formal_source_retrieval_external_mrr')}`",
        f"- Combined retrieval recall/MRR: `{rag.get('formal_source_retrieval_all_recall_at_k')}` / `{rag.get('formal_source_retrieval_all_mrr')}`",
        f"- Proof-search retrieval delta: ordinary candidates `{retrieval.get('proof_search_candidate_delta')}`, no-registered candidates `{retrieval.get('proof_search_no_registered_candidate_delta')}`",
        f"- Missing primitives: `{queue.get('missing_formal_primitives')}`",
        f"- Formal verifier queue: `{queue.get('formal_verifier_queue_items')}` items "
        f"(`{queue.get('formal_verifier_queue_high_priority')}` high priority, "
        f"`{queue.get('formal_verifier_queue_requires_new_theory')}` new-theory routes)",
        f"- Formal verifier proof history: `{queue.get('formal_verifier_queue_rows_with_attempt_history')}` rows "
        f"with attempt history, `{queue.get('formal_verifier_queue_proof_search_solved')}` solved subclaim searches",
        f"- Proof-search kernel rerun queue: `{queue.get('proof_search_kernel_rerun_queue_ready')}` ready, "
        f"`{queue.get('proof_search_kernel_rerun_queue_blocked')}` blocked "
        f"from `{queue.get('proof_search_kernel_rerun_queue_items')}` rows",
        f"- Hugging Face Lean/OProofs reuse: `{queue.get('huggingface_lean_source_candidates')}` candidates "
        f"(`{queue.get('huggingface_lean_source_high_priority')}` high priority, "
        f"OProofs detected `{queue.get('huggingface_lean_source_oproofs_detected')}`, "
        f"`{queue.get('huggingface_lean_source_revalidation_tasks_ready')}` tasks ready, "
        f"`{queue.get('huggingface_lean_source_revalidation_prompt_packets')}` prompt packets, "
        f"`{queue.get('huggingface_lean_source_revalidation_artifact_validation_awaiting')}` validation awaiting, "
        f"`{queue.get('huggingface_lean_source_revalidation_promotion_ready')}` promotion-ready, "
        f"`{queue.get('huggingface_lean_source_proof_evidence_ready')}` proof-evidence-ready)",
        f"- Formal verifier source/semantic checks: max depth `{queue.get('formal_verifier_queue_max_dependency_graph_depth')}`, "
        f"max import cone `{queue.get('formal_verifier_queue_max_import_cone_size')}`, "
        f"semantic review rows `{queue.get('formal_verifier_queue_semantic_needs_review')}`",
        f"- Formal verifier kernel calibration: `{queue.get('formal_verifier_queue_rows_source_trust_kernel_calibrated')}` "
        f"source-trust rows calibrated by kernel-smoke overlap",
        f"- Goal-conditioned minimal formalization: `{queue.get('goal_conditioned_minimal_formalization_plans')}` plans "
        f"(`{queue.get('goal_conditioned_minimal_formalization_low_cost')}` low cost, "
        f"`{queue.get('goal_conditioned_minimal_formalization_existing_reuse_nodes')}` reuse, "
        f"`{queue.get('goal_conditioned_minimal_formalization_wrapper_nodes')}` wrappers, "
        f"`{queue.get('goal_conditioned_minimal_formalization_bridge_nodes')}` bridges, "
        f"`{queue.get('goal_conditioned_minimal_formalization_minimal_cuts')}` minimal cuts, "
        f"`{queue.get('goal_conditioned_minimal_formalization_and_or_nodes')}` AND/OR nodes, "
        f"`{queue.get('goal_conditioned_minimal_formalization_portable_work_packets')}` portable packets)",
        f"- Formal verifier replay: `{queue.get('formal_verifier_replay_tasks')}` tasks "
        f"(`{queue.get('formal_verifier_replay_kernel_calibrated')}` kernel-calibrated, "
        f"`{queue.get('formal_verifier_replay_proof_search_subclaim')}` proof-search subclaim replay)",
        f"- Formal verifier replay attempts: `{queue.get('formal_verifier_replay_attempts')}` attempted "
        f"(`{queue.get('formal_verifier_replay_attempt_negative')}` failed, "
        f"`{queue.get('formal_verifier_replay_attempt_kernel_verified')}` kernel)",
        f"- Formal verifier replay calibration: attempted `{queue.get('formal_verifier_replay_attempted')}`, "
        f"awaiting `{queue.get('formal_verifier_replay_awaiting_full_route_attempt')}`, "
        f"failed `{queue.get('formal_verifier_replay_failed_full_route_attempt')}`, "
        f"kernel `{queue.get('formal_verifier_replay_full_route_kernel_verified')}`",
        f"- Formal verifier replay repair: `{queue.get('formal_verifier_replay_repair_packets')}` packets "
        f"(`{queue.get('formal_verifier_replay_repair_tactic_no_progress')}` tactic-no-progress, "
        f"`{queue.get('formal_verifier_replay_repair_missing_identifier')}` missing identifier)",
        f"- Formal verifier repair application: `{queue.get('formal_verifier_replay_repair_application_tasks')}` tasks "
        f"(`{queue.get('formal_verifier_replay_repair_application_bridge_lemma')}` bridge, "
        f"`{queue.get('formal_verifier_replay_repair_application_import_or_declaration')}` import/declaration)",
        f"- Formal verifier repair scaffold validation: `{queue.get('formal_verifier_replay_repair_application_validation_rows')}` rows "
        f"(`{queue.get('formal_verifier_replay_repair_application_validation_static_ok')}` static OK, "
        f"`{queue.get('formal_verifier_replay_repair_application_validation_local_lean_compiled')}` local Lean compiled)",
        f"- Formal verifier repair execution queue: `{queue.get('formal_verifier_replay_repair_execution_queue_items')}` items "
        f"(`{queue.get('formal_verifier_replay_repair_execution_queue_ready')}` ready, "
        f"`{queue.get('formal_verifier_replay_repair_execution_queue_blocked')}` blocked)",
        f"- Formal verifier repair prompt packets: `{queue.get('formal_verifier_replay_repair_prompt_packets')}` packets "
        f"(`{queue.get('formal_verifier_replay_repair_prompt_packets_with_scaffold_source')}` with scaffold source, "
        f"`{queue.get('formal_verifier_replay_repair_prompt_packets_with_command_plan')}` with commands)",
        f"- Formal verifier repair patch autoworker: `{queue.get('formal_verifier_replay_repair_patch_autoworker_responses')}` responses "
        f"(`{queue.get('formal_verifier_replay_repair_patch_autoworker_patch_proposals')}` patch proposals, "
        f"`{queue.get('formal_verifier_replay_repair_patch_autoworker_kernel_verified')}` kernel verified)",
        f"- Formal verifier repair response validation: `{queue.get('formal_verifier_replay_repair_patch_response_validation_rows')}` rows "
        f"(`{queue.get('formal_verifier_replay_repair_patch_response_validation_accepted_full_route_kernel_verified')}` accepted, "
        f"`{queue.get('formal_verifier_replay_repair_patch_response_validation_awaiting')}` awaiting, "
        f"`{queue.get('formal_verifier_replay_repair_patch_response_validation_rejected')}` rejected)",
        f"- Formal verifier repair response promotion: `{queue.get('formal_verifier_replay_repair_patch_response_promotion_rows')}` rows "
        f"(`{queue.get('formal_verifier_replay_repair_patch_response_promotion_ready')}` ready, "
        f"`{queue.get('formal_verifier_replay_repair_patch_response_promotion_awaiting')}` awaiting, "
        f"`{queue.get('formal_verifier_replay_repair_patch_response_promotion_blocked')}` blocked)",
        f"- Formal verifier repair patch rerun queue: `{queue.get('formal_verifier_replay_repair_patch_rerun_queue_items')}` items "
        f"(`{queue.get('formal_verifier_replay_repair_patch_rerun_queue_ready')}` ready, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_queue_blocked')}` blocked)",
        f"- Formal verifier repair patch rerun attempts: `{queue.get('formal_verifier_replay_repair_patch_rerun_attempts')}` attempts "
        f"(`{queue.get('formal_verifier_replay_repair_patch_rerun_attempts_local_lean_compiled')}` compiled, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_attempts_patch_markers')}` patch markers)",
        f"- Formal verifier repair patch rerun calibration: `{queue.get('formal_verifier_replay_repair_patch_rerun_calibration_rows')}` rows "
        f"(`{queue.get('formal_verifier_replay_repair_patch_rerun_calibration_full_route_kernel_verified')}` full-route kernel, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_calibration_compiled_patch_proposal_not_proof')}` compiled patch proposals)",
        f"- Formal verifier repair patch rerun residual obligations: `{queue.get('formal_verifier_replay_repair_patch_rerun_residual_obligations')}` rows "
        f"(`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_obligations_exact_reuse')}` exact reuse, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_obligations_bridge_chain')}` bridge-chain, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_obligations_source_discovery')}` source discovery)",
        f"- Formal verifier repair patch rerun residual prompt packets: `{queue.get('formal_verifier_replay_repair_patch_rerun_residual_prompt_packets')}` packets "
        f"(`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_with_artifact_context')}` with artifact context, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_with_output_contract')}` with output contract)",
        f"- Formal verifier repair patch rerun residual autoworker: `{queue.get('formal_verifier_replay_repair_patch_rerun_residual_autoworker_responses')}` responses "
        f"(`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_autoworker_patch_proposals')}` patch proposals, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_autoworker_source_discovery')}` source-discovery)",
        f"- Formal verifier repair patch rerun residual response validation: `{queue.get('formal_verifier_replay_repair_patch_rerun_residual_response_validation_rows')}` rows "
        f"(`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_response_validation_awaiting')}` awaiting, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_response_validation_rejected')}` rejected, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_response_validation_accepted_full_route_kernel_verified')}` accepted)",
        f"- Formal verifier repair patch rerun residual follow-up queue: `{queue.get('formal_verifier_replay_repair_patch_rerun_residual_followup_queue_items')}` items "
        f"(`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_followup_queue_ready')}` ready, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_followup_queue_blocked')}` blocked, "
        f"`{queue.get('formal_verifier_replay_repair_patch_rerun_residual_followup_queue_source_discovery')}` source-discovery)",
        f"- Formal verifier agentic proof strategy plan: `{queue.get('formal_verifier_agentic_proof_strategy_plan_rows')}` rows "
        f"(`{queue.get('formal_verifier_agentic_proof_strategy_plan_patch_evolve_blocks')}` patch evolve blocks, "
        f"`{queue.get('formal_verifier_agentic_proof_strategy_plan_source_discovery_cache_items')}` source-discovery cache items, "
        f"`{queue.get('formal_verifier_agentic_proof_strategy_plan_kernel_overlay_composition_seeds')}` kernel-overlay composition seeds)",
        f"- Formal verifier agentic proof candidate evaluation queue: `{queue.get('formal_verifier_agentic_proof_candidate_evaluation_queue_items')}` items "
        f"(`{queue.get('formal_verifier_agentic_proof_candidate_evaluation_queue_patch_candidates')}` patch candidates, "
        f"`{queue.get('formal_verifier_agentic_proof_candidate_evaluation_queue_source_discovery_candidates')}` source-discovery candidates, "
        f"`{queue.get('formal_verifier_agentic_proof_candidate_evaluation_queue_kernel_overlay_candidates')}` kernel-overlay candidates, "
        f"`{queue.get('formal_verifier_agentic_proof_candidate_evaluation_queue_with_kernel_overlay_context')}` with kernel-overlay context)",
        f"- Formal verifier agentic proof safety policy: `{queue.get('formal_verifier_agentic_proof_safety_policy_rows')}` rows "
        f"(`{queue.get('formal_verifier_agentic_proof_safety_policy_patch_bounded_edit')}` bounded-edit, "
        f"`{queue.get('formal_verifier_agentic_proof_safety_policy_source_validation')}` source-validation, "
        f"`{queue.get('formal_verifier_agentic_proof_safety_policy_with_kernel_overlay_context')}` with kernel-overlay context)",
        f"- Formal verifier agentic proof attempt population: `{queue.get('formal_verifier_agentic_proof_attempt_population_entries')}` entries "
        f"(`{queue.get('formal_verifier_agentic_proof_attempt_population_patch_entries')}` patch, "
        f"`{queue.get('formal_verifier_agentic_proof_attempt_population_source_entries')}` source, "
        f"`{queue.get('formal_verifier_agentic_proof_attempt_population_with_kernel_overlay_context')}` with kernel-overlay context)",
        f"- Formal verifier agentic proof execution queue: `{queue.get('formal_verifier_agentic_proof_execution_queue_items')}` items "
        f"(`{queue.get('formal_verifier_agentic_proof_execution_queue_ready')}` ready, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_queue_patch_items')}` patch, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_queue_source_items')}` source, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_queue_with_proof_route_dag_plan')}` route-DAG, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_queue_with_verified_sketch_gate')}` verified-sketch, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_queue_with_blueprint_export_plan')}` Blueprint, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_queue_with_kernel_overlay_context')}` with kernel-overlay context)",
        f"- Formal verifier agentic proof materializer: `{queue.get('formal_verifier_agentic_proof_execution_materializer_rows')}` rows "
        f"(`{queue.get('formal_verifier_agentic_proof_execution_materializer_artifacts')}` artifacts, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_materializer_live_goal_location_ready')}` live-goal locations, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_materializer_live_proof_state_requests')}` live proof-state requests, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_materializer_lean_lsp_mcp_ready_requests')}` Lean-LSP/MCP-ready, "
        f"`{queue.get('formal_verifier_agentic_proof_execution_materializer_kernel_verified')}` artifact kernels)",
        f"- Formal verifier agentic artifact verifier: checked `{queue.get('formal_verifier_agentic_proof_execution_artifact_verifier_checked')}`, "
        f"compiled `{queue.get('formal_verifier_agentic_proof_execution_artifact_verifier_compiled')}`, "
        f"artifact kernel `{queue.get('formal_verifier_agentic_proof_execution_artifact_kernel_verified')}`, "
        f"transcript events `{queue.get('formal_verifier_agentic_proof_execution_artifact_transcript_events_written')}`, "
        f"proof-state requests `{queue.get('formal_verifier_agentic_proof_execution_artifact_live_proof_state_request_valid')}`/"
        f"`{queue.get('formal_verifier_agentic_proof_execution_artifact_live_proof_state_requests')}` valid, "
        f"source theorem kernel `{queue.get('formal_verifier_agentic_proof_execution_source_theorem_kernel_verified')}` "
        f"({queue.get('formal_verifier_agentic_proof_execution_artifact_proof_evidence_status')})",
        f"- Formal verifier agentic proof trace memory: `{queue.get('formal_verifier_agentic_proof_trace_memory_rows')}` rows "
        f"(`{queue.get('formal_verifier_agentic_proof_trace_memory_verifier_events')}` verifier events, "
        f"`{queue.get('formal_verifier_agentic_proof_trace_memory_artifact_kernel_verified')}` artifact-kernel outcomes, "
        f"`{queue.get('formal_verifier_agentic_proof_trace_memory_source_theorem_kernel_verified')}` source-theorem kernels, "
        f"`{queue.get('formal_verifier_agentic_proof_trace_memory_goal_cache_keys')}` goal-cache keys, "
        f"`{queue.get('formal_verifier_agentic_proof_trace_memory_with_required_followups')}` with followups, "
        f"{queue.get('formal_verifier_agentic_proof_trace_memory_proof_evidence_status')})",
        f"- Formal verifier agentic source-theorem promotion: `{queue.get('formal_verifier_agentic_proof_source_theorem_promotion_rows')}` rows "
        f"(`{queue.get('formal_verifier_agentic_proof_source_theorem_promotion_ready')}` ready, "
        f"`{queue.get('formal_verifier_agentic_proof_source_theorem_promotion_needs_target_resolution')}` target-resolution, "
        f"`{queue.get('formal_verifier_agentic_proof_source_theorem_promotion_artifact_kernel_inputs')}` artifact-kernel inputs, "
        f"`{queue.get('formal_verifier_agentic_proof_source_theorem_promotion_source_theorem_kernel_verified')}` source-theorem kernels, "
        f"`{queue.get('formal_verifier_agentic_proof_source_theorem_promotion_needs_source_target')}` need source target)",
        f"- Formal verifier agentic source-theorem target resolution: `{queue.get('formal_verifier_agentic_proof_source_theorem_target_resolution_rows')}` rows "
        f"(`{queue.get('formal_verifier_agentic_proof_source_theorem_target_resolution_resolved')}` resolved, "
        f"`{queue.get('formal_verifier_agentic_proof_source_theorem_target_resolution_needs_route_match')}` need route match, "
        f"`{queue.get('formal_verifier_agentic_proof_source_theorem_target_resolution_overlays')}` overlays, "
        f"{queue.get('formal_verifier_agentic_proof_source_theorem_target_resolution_proof_evidence_status')})",
        f"- Formalization gap proof-state triage: `{queue.get('formalization_gap_planner_proof_state_triage_items')}` items "
        f"(`{queue.get('formalization_gap_planner_proof_state_triage_formal_gap_scaffold_items')}` formal-gap scaffold, "
        f"`{queue.get('formalization_gap_planner_proof_state_triage_local_lean_failed_items')}` local Lean failed, "
        f"`{queue.get('formalization_gap_planner_proof_state_triage_non_lean_skeleton_items')}` non-Lean skeleton)",
        "- Claim-ledger repair-response promotion overlay: "
        f"`{queue.get('claim_ledger_repair_response_promotion_upgrades')}` upgrades from "
        f"`{queue.get('claim_ledger_repair_response_promotion_overlay_rows')}` ready rows",
        f"- Queue: exact_reuse=`{queue.get('reuse_exact_proof_bank_obligation')}`, compose=`{queue.get('compose_existing_bridge_chain')}`, minimal_wrapper=`{queue.get('add_minimal_wrapper')}`, design_bridge=`{queue.get('design_bridge_lemma')}`",
        f"- Theorem composition packets: `{composition.get('theorem_composition_packets')}` "
        f"(exact links `{composition.get('theorem_composition_exact_proof_bank_links')}`, "
        f"unresolved primitives `{composition.get('theorem_composition_unresolved_primitives')}`)",
        "",
        "## Kernel Proof Evidence Overlays",
        "",
        str(kernel_overlays.get("proof_evidence_boundary", "")),
        "",
    ]
    for row in kernel_overlays.get("standalone_kernel_proof_audit_preview", []):
        if not isinstance(row, dict):
            continue
        sample_ids = ", ".join(
            f"`{item}`" for item in row.get("sample_kernel_verified_obligations", [])
        ) or "none"
        lines.append(
            f"- `{row.get('manifest')}`: kernel `{row.get('n_kernel_verified')}/{row.get('n_obligations')}`, "
            f"strength `{row.get('verification_strength')}`, fingerprint match `{row.get('fingerprint_matches_system_proof_bank')}`"
        )
        lines.append(f"  verifier: `{row.get('verifier')}`")
        lines.append(f"  sample obligations: {sample_ids}")
    lines.extend(["", "## Kernel Overlay Alignment", ""])
    lines.append(str(kernel_alignment.get("proof_evidence_boundary", "")))
    lines.append("")
    for row in kernel_alignment.get("theorem_composition_kernel_overlay_preview", []):
        if not isinstance(row, dict):
            continue
        matched = ", ".join(
            f"`{item}`" for item in row.get("kernel_overlay_verified_obligations", [])
        ) or "none"
        unresolved = ", ".join(
            f"`{item}`" for item in row.get("unresolved_primitives", [])
        ) or "none"
        lines.append(
            f"- composition `{row.get('packet_id')}` from `{row.get('source_claim_id')}`: {matched}"
        )
        lines.append(f"  unresolved: {unresolved}")
        lines.append(f"  next: {row.get('recommended_next_action')}")
    lines.extend(["", "### Composition Work Items", ""])
    for row in kernel_alignment.get("kernel_overlay_composition_work_item_preview", []):
        if not isinstance(row, dict):
            continue
        matched = ", ".join(
            f"`{item}`" for item in row.get("already_kernel_verified_subclaims", [])
        ) or "none"
        unmatched = ", ".join(
            f"`{item}`" for item in row.get("unmatched_exact_proof_bank_obligations", [])
        ) or "none"
        unresolved = ", ".join(
            f"`{item}`" for item in row.get("unresolved_primitives", [])
        ) or "none"
        lines.append(
            f"- `{row.get('work_item_id')}` for `{row.get('source_claim_id')}` "
            f"(blockers={row.get('target_blocker_count')})"
        )
        lines.append(f"  kernel subclaims: {matched}")
        lines.append(f"  unmatched exact obligations: {unmatched}")
        lines.append(f"  unresolved primitives: {unresolved}")
        lines.append(f"  gate: {row.get('promotion_gate')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "### Composition Agentic Seeds", ""])
    for row in kernel_alignment.get("kernel_overlay_composition_agentic_seed_preview", []):
        if not isinstance(row, dict):
            continue
        subclaims = ", ".join(
            f"`{item}`" for item in row.get("already_kernel_verified_subclaims", [])
        ) or "none"
        blockers = ", ".join(
            f"`{item}`" for item in row.get("target_blockers", [])
        ) or "none"
        tools = ", ".join(f"`{item}`" for item in row.get("required_live_tools", [])) or "none"
        queries = ", ".join(
            f"`{item}`" for item in row.get("source_discovery_queries", [])
        ) or "none"
        lines.append(
            f"- `{row.get('seed_id')}` for `{row.get('source_claim_id')}` "
            f"({row.get('seed_status')}): {row.get('agentic_strategy_kind')}"
        )
        lines.append(f"  goal cache key: `{row.get('goal_cache_key')}`")
        lines.append(f"  candidate DB key: `{row.get('candidate_database_key')}`")
        lines.append(f"  kernel subclaims: {subclaims}")
        lines.append(f"  blockers: {blockers}")
        lines.append(f"  source queries: {queries}")
        lines.append(f"  live tools: {tools}")
        lines.append(f"  gate: {row.get('promotion_gate')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    for row in kernel_alignment.get("formal_verifier_queue_kernel_overlay_preview", []):
        if not isinstance(row, dict):
            continue
        matched = ", ".join(
            f"`{item}`" for item in row.get("kernel_overlay_verified_obligations", [])
        ) or "none"
        lines.append(
            f"- queue `{row.get('item_id')}` `{row.get('display_name')}`: {matched}"
        )
        lines.append(f"  gate: {row.get('required_gate')}")
    for row in kernel_alignment.get("formal_verifier_replay_kernel_overlay_preview", []):
        if not isinstance(row, dict):
            continue
        matched = ", ".join(
            f"`{item}`" for item in row.get("kernel_overlay_verified_obligations", [])
        ) or "none"
        lines.append(
            f"- replay `{row.get('replay_id')}` `{row.get('display_name')}`: {matched}"
        )
        lines.append(f"  gate: {row.get('required_gate')}")
    lines.extend([
        "",
        "## Handoff Targets",
        "",
    ])
    for target in queue.get("handoff_targets", []):
        if not isinstance(target, dict):
            continue
        lines.append(
            f"- `{target.get('primitive')}` ({target.get('action_class')}): "
            f"{target.get('suggested_next_step')}"
        )
        lines.append(f"  query: `{target.get('query_hint')}`")
    lines.extend(["", "## Proof Search Kernel Rerun Queue", ""])
    command = str(queue.get("proof_search_kernel_rerun_queue_command") or "")
    if command:
        lines.append(f"- command: `{command}`")
    for row in queue.get("proof_search_kernel_rerun_queue_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('obligation_id')}` status=`{row.get('status')}` "
            f"source=`{row.get('selected_source')}` "
            f"strength=`{row.get('selected_verification_strength')}`"
        )
        lines.append(f"  gate: {row.get('required_gate')}")
    lines.extend(["", "## Hugging Face Lean/OProofs Revalidation", ""])
    lines.append(
        "HF Lean datasets are external retrieval/training candidates. They are not proof "
        "evidence until sampled Lean artifacts pass local Lean/AXLE and promotion review."
    )
    for row in queue.get("huggingface_lean_source_revalidation_queue_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('dataset_id')}` ({row.get('relevance_class')}): "
            f"{row.get('revalidation_status')}"
        )
        lines.append(
            f"  role: {row.get('retrieval_role')} "
            f"rows={row.get('num_rows')} shards={row.get('parquet_shards')}"
        )
        lines.append(f"  gate: {row.get('required_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
    lines.extend(["", "### HF Lean Revalidation Tasks", ""])
    for row in queue.get("huggingface_lean_source_revalidation_tasks_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('dataset_id')}` task `{row.get('task_id')}`: "
            f"{row.get('task_status')} sample={row.get('sample_size')}"
        )
        lines.append(f"  work dir: `{row.get('local_work_dir')}`")
        lines.append(f"  gate: {row.get('required_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
    lines.extend(["", "### HF Lean Prompt Packets", ""])
    for row in queue.get("huggingface_lean_source_revalidation_prompt_packets_preview", []):
        if not isinstance(row, dict):
            continue
        contract = row.get("expected_output_contract", {})
        if not isinstance(contract, dict):
            contract = {}
        lines.append(
            f"- `{row.get('dataset_id')}` prompt `{row.get('prompt_packet_id')}`: "
            f"{row.get('sample_strategy')} sample={row.get('sample_size')}"
        )
        lines.append(
            f"  response JSONL: `{contract.get('write_jsonl', '')}` "
            f"license_review={row.get('license_review_required')}"
        )
        lines.append(f"  gate: {row.get('required_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
    lines.extend(["", "### HF Lean Artifact Validation", ""])
    for row in queue.get("huggingface_lean_source_revalidation_artifact_validation_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('dataset_id')}` validation `{row.get('validation_id')}`: "
            f"{row.get('acceptance_status')}"
        )
        lines.append(
            f"  response={row.get('response_present')} contract={row.get('response_contract_ok')} "
            f"kernel_rows={row.get('kernel_verified_rows')}"
        )
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "### HF Lean Promotion Queue", ""])
    for row in queue.get("huggingface_lean_source_revalidation_promotion_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('dataset_id')}` promotion `{row.get('promotion_id')}`: "
            f"{row.get('promotion_status')} ready={row.get('promotion_ready')}"
        )
        lines.append(
            f"  kernel_rows={row.get('kernel_verified_rows')} "
            f"evidence_paths={len(row.get('evidence_paths', []) or [])}"
        )
        lines.append(f"  gate: {row.get('required_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
    lines.extend(["", "## Formal Verifier Queue", ""])
    for row in queue.get("formal_verifier_queue_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` ({row.get('priority')}, {row.get('verification_stage')}): "
            f"{row.get('required_gate')} "
            f"[history={row.get('proof_history_status')}, "
            f"attempts={row.get('proof_attempt_positive')}/{row.get('proof_attempt_negative')}, "
            f"search_solved={row.get('proof_search_solved')}, "
            f"source={row.get('source_trust_level')}, "
            f"kernel_calibration={row.get('source_trust_calibration_status')}, "
            f"semantic={row.get('semantic_faithfulness_score')}/"
            f"{row.get('semantic_faithfulness_status')}]"
        )
    lines.extend(["", "## Goal-Conditioned Minimal Formalization", ""])
    for row in queue.get("goal_conditioned_minimal_formalization_plan_preview", []):
        if not isinstance(row, dict):
            continue
        selected = ", ".join(
            f"`{item}`" for item in row.get("selected_primitives", [])
        ) or "none"
        skipped = ", ".join(
            f"`{item}`" for item in row.get("do_not_formalize_now", [])
        ) or "none"
        nodes = ", ".join(
            f"`{node.get('primitive')}`/{node.get('action_class')}"
            for node in row.get("minimal_additional_formalization_nodes", [])
            if isinstance(node, dict)
        ) or "reuse existing nodes"
        next_packets = ", ".join(
            f"`{packet.get('primitive')}`:{packet.get('worker_packet_kind')}"
            for packet in row.get("next_work_packets", [])
            if isinstance(packet, dict)
        ) or "none"
        cut = row.get("minimal_cut_summary", {})
        if not isinstance(cut, dict):
            cut = {}
        cost = row.get("route_cost_breakdown", {})
        if not isinstance(cost, dict):
            cost = {}
        lines.append(
            f"- `{row.get('display_name')}` cost={row.get('goal_conditioned_cost')} "
            f"efficiency={row.get('route_efficiency_score')} class={row.get('route_class')}"
        )
        lines.append(f"  selected primitives: {selected}")
        lines.append(f"  add now: {nodes}")
        lines.append(f"  do not formalize now: {skipped}")
        lines.append(
            "  minimal cut: "
            f"use_existing={len(cut.get('use_existing', []))} "
            f"wrappers={len(cut.get('add_wrappers', []))} "
            f"bridges={len(cut.get('add_bridge_lemmas', []))} "
            f"source={len(cut.get('add_source_discovery', []))} "
            f"first_principles={len(cut.get('add_first_principles', []))}"
        )
        lines.append(
            "  cost terms: "
            f"base={cost.get('base_route_cost')} "
            f"import={cost.get('import_cone_penalty')} "
            f"depth={cost.get('dependency_depth_penalty')} "
            f"blockers={cost.get('blocker_penalty')} "
            f"trust_credit={cost.get('source_trust_credit')}"
        )
        lines.append(f"  next packets: {next_packets}")
        lines.append(f"  summary: {row.get('route_summary')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Replay", ""])
    for row in queue.get("formal_verifier_replay_preview", []):
        if not isinstance(row, dict):
            continue
        obligations = ", ".join(
            f"`{item}`" for item in row.get("subclaim_replay_obligations", [])
        ) or "none"
        lines.append(
            f"- `{row.get('display_name')}` ({row.get('replay_mode')}): "
            f"{row.get('acceptance_gate')} "
            f"[subclaims={obligations}, "
            f"kernel={row.get('kernel_smoke_related_verified')}/"
            f"{row.get('kernel_smoke_related_total')}, "
            f"proof_search_solved={row.get('proof_search_solved')}]"
        )
    lines.extend(["", "## Formal Verifier Replay Calibration", ""])
    for row in queue.get("formal_verifier_replay_calibration_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}`: {row.get('replay_calibration_status')} "
            f"(attempts={row.get('n_attempts')}, error={row.get('first_error_category')})"
        )
        lines.append(f"  update: {row.get('replay_policy_update')}")
    lines.extend(["", "## Formal Verifier Replay Repair", ""])
    for packet in queue.get("formal_verifier_replay_repair_preview", []):
        if not isinstance(packet, dict):
            continue
        obligations = ", ".join(
            f"`{item}`" for item in packet.get("subclaim_replay_obligations", [])
        ) or "none"
        lines.append(
            f"- `{packet.get('display_name')}` ({packet.get('repair_class')}, "
            f"error={packet.get('first_error_category')}): "
            f"{packet.get('candidate_bridge_lemma_name')}"
        )
        lines.append(f"  subclaims: {obligations}")
        lines.append(f"  gate: {packet.get('repair_acceptance_gate')}")
        lines.append(f"  boundary: {packet.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Repair Application", ""])
    for task in queue.get("formal_verifier_replay_repair_application_preview", []):
        if not isinstance(task, dict):
            continue
        obligations = ", ".join(
            f"`{item}`" for item in task.get("subclaim_replay_obligations", [])
        ) or "none"
        lines.append(
            f"- `{task.get('display_name')}` ({task.get('application_mode')}): "
            f"{task.get('candidate_bridge_lemma_name')}"
        )
        lines.append(f"  artifact: `{task.get('artifact_path')}`")
        lines.append(f"  subclaims: {obligations}")
        lines.append(f"  boundary: {task.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Repair Application Validation", ""])
    for row in queue.get("formal_verifier_replay_repair_application_validation_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}`: {row.get('validation_status')} "
            f"(static={row.get('static_checks_ok')}, "
            f"local_lean={row.get('local_lean_compiled')})"
        )
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Repair Execution Queue", ""])
    for row in queue.get("formal_verifier_replay_repair_execution_queue_preview", []):
        if not isinstance(row, dict):
            continue
        commands = ", ".join(f"`{item}`" for item in row.get("command_plan", [])[:2]) or "none"
        lines.append(
            f"- #{row.get('execution_priority_rank')} `{row.get('display_name')}` "
            f"({row.get('execution_status')}): {row.get('candidate_bridge_lemma_name')}"
        )
        lines.append(f"  artifact: `{row.get('artifact_path')}`")
        lines.append(f"  commands: {commands}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Repair Prompt Packets", ""])
    for packet in queue.get("formal_verifier_replay_repair_prompt_packets_preview", []):
        if not isinstance(packet, dict):
            continue
        lines.append(
            f"- #{packet.get('execution_priority_rank')} `{packet.get('display_name')}`: "
            f"{packet.get('contract_claim_status')} "
            f"({packet.get('prompt_chars')} chars)"
        )
        lines.append(f"  bridge: `{packet.get('candidate_bridge_lemma_name')}`")
        lines.append(f"  gate: {packet.get('contract_promotion_gate')}")
        lines.append(f"  boundary: {packet.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Repair Response Validation", ""])
    for row in queue.get("formal_verifier_replay_repair_patch_response_validation_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` ({row.get('acceptance_status')}): "
            f"{row.get('candidate_bridge_lemma_name')}"
        )
        lines.append(
            f"  response={row.get('response_present')} contract={row.get('response_contract_ok')} "
            f"kernel={row.get('kernel_verified')} calibration={row.get('replay_calibration_status')}"
        )
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Repair Response Promotion", ""])
    for row in queue.get("formal_verifier_replay_repair_patch_response_promotion_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` ({row.get('promotion_status')}): "
            f"{row.get('candidate_bridge_lemma_name')}"
        )
        lines.append(
            f"  ready={row.get('promotion_ready')} action={row.get('action_type')} "
            f"gate={row.get('required_gate')}"
        )
        lines.append(f"  evidence paths: {', '.join(row.get('evidence_paths', [])) or 'none'}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Residual Prompt Packets", ""])
    for packet in queue.get(
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_preview",
        [],
    ):
        if not isinstance(packet, dict):
            continue
        lines.append(
            f"- `{packet.get('display_name')}` -> `{packet.get('residual_gap')}` "
            f"({packet.get('action_class')}): {packet.get('contract_claim_status')} "
            f"({packet.get('prompt_chars')} chars)"
        )
        lines.append(f"  artifact: `{packet.get('patched_artifact_path')}`")
        lines.append(f"  mode: {packet.get('contract_required_output_mode')}")
        lines.append(f"  gate: {packet.get('contract_promotion_gate')}")
        lines.append(f"  boundary: {packet.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Residual Autoworker", ""])
    for row in queue.get(
        "formal_verifier_replay_repair_patch_rerun_residual_autoworker_preview",
        [],
    ):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('worker_status')}): {row.get('action_class')}"
        )
        lines.append(f"  artifact: `{row.get('proposed_lean_artifact_path')}`")
        queries = ", ".join(f"`{item}`" for item in row.get("source_discovery_queries", [])) or "none"
        lines.append(f"  source queries: {queries}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Residual Response Validation", ""])
    for row in queue.get(
        "formal_verifier_replay_repair_patch_rerun_residual_response_validation_preview",
        [],
    ):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('acceptance_status')}): response={row.get('response_present')} "
            f"contract={row.get('response_contract_ok')}"
        )
        lines.append(
            f"  calibration={row.get('patch_rerun_calibration_status')} "
            f"kernel={row.get('kernel_verified')}"
        )
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Formal Verifier Residual Follow-up Queue", ""])
    for row in queue.get(
        "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_preview",
        [],
    ):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('followup_status')}): {row.get('followup_kind')} "
            f"for `{row.get('owner_agent')}`"
        )
        lines.append(f"  artifact: `{row.get('proposed_lean_artifact_path')}`")
        queries = ", ".join(f"`{item}`" for item in row.get("source_discovery_queries", [])) or "none"
        commands = ", ".join(f"`{item}`" for item in row.get("execution_commands", [])) or "none"
        lines.append(f"  source queries: {queries}")
        lines.append(f"  commands: {commands}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Agentic Proof Strategy Plan", ""])
    for row in queue.get(
        "formal_verifier_agentic_proof_strategy_plan_preview",
        [],
    ):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('agentic_strategy_kind')}): score={row.get('priority_score')}"
        )
        patterns = ", ".join(f"`{item}`" for item in row.get("paper_patterns", [])) or "none"
        tools = ", ".join(f"`{item}`" for item in row.get("required_live_tools", [])) or "none"
        gates = ", ".join(f"`{item}`" for item in row.get("evaluator_gates", [])) or "none"
        lines.append(f"  patterns: {patterns}")
        lines.append(f"  live tools: {tools}")
        lines.append(f"  evaluator gates: {gates}")
        lines.append(f"  candidate DB key: `{row.get('candidate_database_key')}`")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Agentic Proof Candidate Evaluation Queue", ""])
    for row in queue.get(
        "formal_verifier_agentic_proof_candidate_evaluation_queue_preview",
        [],
    ):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('status')}): {row.get('generation_mode')}"
        )
        evaluators = ", ".join(f"`{item}`" for item in row.get("evaluator_pool", [])) or "none"
        sequence = ", ".join(f"`{item}`" for item in row.get("live_tool_sequence", [])) or "none"
        lines.append(f"  candidate DB key: `{row.get('candidate_database_key')}`")
        lines.append(f"  lineage key: `{row.get('candidate_lineage_key')}`")
        if row.get("kernel_overlay_context_present"):
            subclaims = ", ".join(
                f"`{item}`" for item in row.get("kernel_overlay_verified_subclaims", [])
            ) or "none"
            blockers = ", ".join(
                f"`{item}`" for item in row.get("kernel_overlay_target_blockers", [])
            ) or "none"
            queries = ", ".join(
                f"`{item}`" for item in row.get("kernel_overlay_source_discovery_queries", [])
            ) or "none"
            lines.append(f"  kernel-overlay subclaims: {subclaims}")
            lines.append(f"  kernel-overlay blockers: {blockers}")
            lines.append(f"  kernel-overlay source queries: {queries}")
        lines.append(f"  attempt budget: {row.get('attempt_budget')}")
        lines.append(f"  evaluator pool: {evaluators}")
        lines.append(f"  live tool sequence: {sequence}")
        lines.append(f"  promotion gate: {row.get('promotion_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Agentic Proof Safety Policy", ""])
    for row in queue.get("formal_verifier_agentic_proof_safety_policy_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('policy_status')}): {row.get('generation_mode')}"
        )
        anti_cheat = ", ".join(f"`{item}`" for item in row.get("anti_cheat_checks", [])) or "none"
        forbidden = ", ".join(f"`{item}`" for item in row.get("forbidden_tokens", [])) or "none"
        lines.append(f"  goal cache key: `{row.get('goal_cache_key')}`")
        if row.get("kernel_overlay_context_present"):
            subclaims = ", ".join(
                f"`{item}`" for item in row.get("kernel_overlay_verified_subclaims", [])
            ) or "none"
            blockers = ", ".join(
                f"`{item}`" for item in row.get("kernel_overlay_target_blockers", [])
            ) or "none"
            lines.append(f"  kernel-overlay subclaims: {subclaims}")
            lines.append(f"  kernel-overlay blockers: {blockers}")
        lines.append(f"  bounded edit required: `{row.get('bounded_edit_required')}`")
        if row.get("bounded_edit_start_marker"):
            lines.append(
                f"  markers: `{row.get('bounded_edit_start_marker')}` / `{row.get('bounded_edit_end_marker')}`"
            )
        lines.append(f"  anti-cheat checks: {anti_cheat}")
        lines.append(f"  forbidden tokens: {forbidden}")
        lines.append(f"  SafeVerify gate: {row.get('safeverify_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Agentic Proof Attempt Population", ""])
    for row in queue.get("formal_verifier_agentic_proof_attempt_population_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('attempt_status')}): {row.get('population_bucket')}"
        )
        lessons = ", ".join(f"`{item}`" for item in row.get("lessons_learned", [])) or "none"
        lines.append(f"  goal cache key: `{row.get('goal_cache_key')}`")
        lines.append(f"  population key: `{row.get('proof_sketch_population_key')}`")
        if row.get("kernel_overlay_context_present"):
            subclaims = ", ".join(
                f"`{item}`" for item in row.get("kernel_overlay_verified_subclaims", [])
            ) or "none"
            blockers = ", ".join(
                f"`{item}`" for item in row.get("kernel_overlay_target_blockers", [])
            ) or "none"
            lines.append(f"  kernel-overlay subclaims: {subclaims}")
            lines.append(f"  kernel-overlay blockers: {blockers}")
        lines.append(f"  lineage key: `{row.get('candidate_lineage_key')}`")
        lines.append(f"  selection weight: {row.get('selection_weight')}")
        lines.append(f"  diagnostic signature: `{row.get('diagnostic_signature')}`")
        lines.append(f"  lessons: {lessons}")
        lines.append(f"  sampler policy: `{row.get('sampler_policy')}`")
        lines.append(f"  promotion gate: {row.get('promotion_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Agentic Proof Execution Queue", ""])
    for row in queue.get("formal_verifier_agentic_proof_execution_queue_preview", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('execution_status')}): {row.get('population_bucket')}"
        )
        tools = ", ".join(
            f"`{item}`" for item in row.get("proof_state_provider_plan", [])
        ) or "none"
        dag = ", ".join(
            f"`{item}`" for item in row.get("proof_route_dag_plan", [])[:2]
        ) or "none"
        sketch = ", ".join(
            f"`{item}`" for item in row.get("verified_sketch_gate_plan", [])[:2]
        ) or "none"
        blueprint = ", ".join(
            f"`{item}`" for item in row.get("blueprint_export_plan", [])[:2]
        ) or "none"
        lines.append(f"  artifact: `{row.get('candidate_artifact_path')}`")
        lines.append(f"  transcript: `{row.get('execution_transcript_path')}`")
        lines.append(f"  proof-state tools: {tools}")
        lines.append(f"  route-DAG plan: {dag}")
        lines.append(f"  verified-sketch gate: {sketch}")
        lines.append(f"  Blueprint export: {blueprint}")
        if row.get("kernel_overlay_context_present"):
            subclaims = ", ".join(
                f"`{item}`" for item in row.get("kernel_overlay_verified_subclaims", [])
            ) or "none"
            blockers = ", ".join(
                f"`{item}`" for item in row.get("kernel_overlay_target_blockers", [])
            ) or "none"
            lines.append(f"  kernel-overlay verified subclaims: {subclaims}")
            lines.append(f"  kernel-overlay target blockers: {blockers}")
        lines.append(f"  promotion gate: {row.get('promotion_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Agentic Proof Execution Materializer", ""])
    for row in queue.get(
        "formal_verifier_agentic_proof_execution_materializer_preview",
        [],
    ):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('materialization_id')}` for `{row.get('target_theorem_name')}` "
            f"({row.get('materialization_status')})"
        )
        lines.append(f"  artifact: `{row.get('candidate_artifact_path')}`")
        lines.append(
            f"  target: `{row.get('target_lean_file')}`:"
            f"{row.get('target_lean_line')} / `{row.get('target_lean_declaration')}`"
        )
        lines.append(
            f"  live goal ready: `{row.get('live_goal_location_ready')}`, "
            f"artifact kernel: `{row.get('kernel_verified')}`"
        )
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Agentic Proof Artifact Verifier", ""])
    lines.append(
        "Artifact verifier rows report Lean checks on generated artifacts; source-theorem "
        "kernel proof remains separate."
    )
    for row in queue.get(
        "formal_verifier_agentic_proof_execution_artifact_verifier_preview",
        [],
    ):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('artifact_verification_id')}` for `{row.get('target_theorem_name')}` "
            f"({row.get('verification_status')})"
        )
        lines.append(f"  artifact: `{row.get('candidate_artifact_path')}`")
        lines.append(
            f"  target: line {row.get('target_lean_line')} / "
            f"`{row.get('target_lean_declaration')}`"
        )
        lines.append(
            f"  checked: `{row.get('local_lean_checked')}`, "
            f"compiled: `{row.get('local_lean_compiled')}`, "
            f"artifact kernel: `{row.get('artifact_kernel_verified')}`, "
            f"source theorem kernel: `{row.get('source_theorem_kernel_verified')}`"
        )
        lines.append(
            f"  verifier: `{row.get('verifier')}` / `{row.get('verification_strength')}`"
        )
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Agentic Source-Theorem Promotion Queue", ""])
    lines.append(
        "Rows here are target-resolution or integration work orders from artifact-level Lean checks; "
        "they do not close source theorem gaps by themselves."
    )
    for row in queue.get(
        "formal_verifier_agentic_proof_source_theorem_promotion_preview",
        [],
    ):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('target_theorem_name')}` "
            f"({row.get('promotion_status')}): `{row.get('action_type')}`"
        )
        lines.append(f"  owner: `{row.get('owner_agent')}` priority `{row.get('priority')}`")
        lines.append(f"  artifact: `{row.get('candidate_artifact_path')}`")
        lines.append(
            f"  artifact kernel: `{row.get('artifact_kernel_verified')}`, "
            f"source theorem kernel: `{row.get('source_theorem_kernel_verified')}`, "
            f"source target known: `{row.get('source_theorem_target_known')}`"
        )
        commands = ", ".join(
            f"`{item}`" for item in row.get("command_plan", [])
        ) or "none"
        inputs = ", ".join(
            f"`{item}`" for item in row.get("required_inputs", [])
        ) or "none"
        lines.append(f"  required inputs: {inputs}")
        lines.append(f"  command plan: {commands}")
        lines.append(f"  gate: {row.get('required_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Agentic Source-Theorem Target Resolution", ""])
    lines.append(
        "Rows here attach route-ledger source targets to artifact-level proof probes; "
        "they are overlays for later source-theorem verification, not proof evidence."
    )
    for row in queue.get(
        "formal_verifier_agentic_proof_source_theorem_target_resolution_preview",
        [],
    ):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('target_theorem_name')}` "
            f"({row.get('resolution_status')}): `{row.get('action_type')}`"
        )
        lines.append(
            f"  match: `{row.get('match_source')}` route `{row.get('source_route_id')}` "
            f"queue `{row.get('source_queue_item_id')}` replay `{row.get('source_replay_id')}`"
        )
        lines.append(
            f"  source target known: `{row.get('source_theorem_target_known')}`, "
            f"artifact kernel: `{row.get('artifact_kernel_verified')}`"
        )
        if row.get("source_theorem_lean_file"):
            lines.append(f"  source file: `{row.get('source_theorem_lean_file')}`")
        if row.get("source_theorem_statement"):
            lines.append(f"  source statement: `{row.get('source_theorem_statement')}`")
        lines.append(f"  gate: {row.get('required_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Proof-State Triage", ""])
    for row in queue.get("formalization_gap_planner_proof_state_triage_preview", []):
        if not isinstance(row, dict):
            continue
        statuses = ", ".join(
            f"`{item}`" for item in row.get("applied_prover_attempt_statuses", [])
        ) or "none"
        tools = ", ".join(f"`{item}`" for item in row.get("recommended_tools", [])) or "none"
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` "
            f"({row.get('triage_class')}, score={row.get('priority_score')}): "
            f"{row.get('recommended_next_action')}"
        )
        lines.append(f"  owner: `{row.get('owner_agent')}`")
        lines.append(f"  attempt statuses: {statuses}")
        lines.append(f"  tools: {tools}")
        lines.append(f"  required gate: {row.get('required_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Theorem Composition Handoff", ""])
    lines.append(str(composition.get("proof_evidence_boundary", "")))
    lines.append("")
    for packet in composition.get("packet_preview", []):
        if not isinstance(packet, dict):
            continue
        obligations = ", ".join(
            f"`{item}`" for item in packet.get("exact_proof_bank_obligations", [])
        ) or "none"
        unresolved = ", ".join(f"`{item}`" for item in packet.get("unresolved_primitives", [])) or "none"
        lines.append(f"- `{packet.get('packet_id')}` from `{packet.get('source_claim_id')}`")
        lines.append(f"  exact obligations: {obligations}")
        lines.append(f"  unresolved primitives: {unresolved}")
        lines.append(f"  gate: {packet.get('required_gate')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("honesty_boundaries", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

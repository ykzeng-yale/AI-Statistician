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

    proof_payload = _read_json(_artifact_path(artifacts, "proof_audit", run_dir))
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
    guidance_payload = _read_json(_artifact_path(artifacts, "evaluation_benchmark_guidance", run_dir))

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
    payload: dict[str, object] = {
        "schema_version": RAG_COLLABORATION_EXPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_system_audit_manifest": str(system_audit_manifest),
        "source_run_dir": str(run_dir),
        "proof_evidence": {
            "proofs_kernel_verified": counts.get("proofs_kernel_verified"),
            "proofs_total": counts.get("proofs_total"),
            "proof_verification_strength": counts.get("proof_verification_strength"),
            "proof_bank_fingerprint": proof_payload.get("proof_bank_fingerprint"),
            "proof_dependency_edges": counts.get("proof_dependency_edges"),
            "proof_audit_manifest": str(_artifact_path(artifacts, "proof_audit", run_dir)),
        },
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
            "Simulation diagnostics are empirical evidence, not theorem proofs.",
            "FormalVerifier replay rows are executable task/training artifacts, not theorem proof evidence.",
            "FormalVerifier replay attempts are proof evidence only when kernel_verified=true and placeholders were removed.",
            "FormalVerifier replay calibration rows are proof evidence only for full-route kernel-verified targets.",
            "FormalVerifier replay repair packets and proof templates are not proof evidence until a repaired attempt passes AXLE/local Lean.",
            "FormalVerifier replay repair application scaffolds are work artifacts, not proof evidence.",
            "FormalVerifier repair scaffold validation is source-artifact integrity evidence, not theorem proof evidence.",
            "FormalVerifier repair execution queue items are patch work orders, not theorem proof evidence.",
            "FormalVerifier repair prompt packets are worker instructions, not theorem proof evidence.",
            "FormalVerifier repair patch responses are proof evidence only when response validation accepts full-route kernel-verified calibration.",
            "FormalVerifier repair patch response promotion rows are ledger-update contracts; they do not mutate the proof ledger by themselves.",
            "Claim-ledger repair-response promotion overlays close formal gaps only for matching ready kernel-verified promotion rows.",
            "FORMAL_GAP and theorem-hole queues remain open until a non-placeholder Lean proof is verified.",
        ],
    }
    payload["handoff_fingerprint"] = stable_hash(
        {
            "proof_evidence": payload["proof_evidence"],
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
    rag = dict(payload.get("rag_provider_evidence", {}) or {})
    retrieval = dict(payload.get("retrieval_ablation_evidence", {}) or {})
    queue = dict(payload.get("formal_capacity_queue", {}) or {})
    composition = dict(payload.get("theorem_composition_handoff", {}) or {})
    lines = [
        "# RAG Collaboration Handoff",
        "",
        f"- Source run: `{payload.get('source_run_dir')}`",
        f"- Proof bank: `{proof.get('proofs_kernel_verified')}/{proof.get('proofs_total')}` kernel verified",
        f"- Proof fingerprint: `{proof.get('proof_bank_fingerprint')}`",
        f"- Lean RAG active: `{rag.get('lean_rag_dependency_graph_enabled')}`",
        f"- Lean RAG DB: `{rag.get('lean_rag_dependency_graph_path')}`",
        f"- Lean RAG DB health: `{rag.get('lean_rag_dependency_health_status')}` "
        f"(fallback `{rag.get('lean_rag_dependency_fallback_used')}`: "
        f"`{rag.get('lean_rag_dependency_fallback_reason')}`)",
        f"- Lean RAG package: `{rag.get('lean_rag_package_contract_ok')}` at `{rag.get('lean_rag_package_branch')}` / `{str(rag.get('lean_rag_package_commit') or '')[:12]}`",
        f"- Lean RAG seed lanes: `{', '.join(rag.get('lean_rag_package_seed_lanes', []))}`",
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
        f"- Formal verifier source/semantic checks: max depth `{queue.get('formal_verifier_queue_max_dependency_graph_depth')}`, "
        f"max import cone `{queue.get('formal_verifier_queue_max_import_cone_size')}`, "
        f"semantic review rows `{queue.get('formal_verifier_queue_semantic_needs_review')}`",
        f"- Formal verifier kernel calibration: `{queue.get('formal_verifier_queue_rows_source_trust_kernel_calibrated')}` "
        f"source-trust rows calibrated by kernel-smoke overlap",
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
        f"- Formal verifier repair response validation: `{queue.get('formal_verifier_replay_repair_patch_response_validation_rows')}` rows "
        f"(`{queue.get('formal_verifier_replay_repair_patch_response_validation_accepted_full_route_kernel_verified')}` accepted, "
        f"`{queue.get('formal_verifier_replay_repair_patch_response_validation_awaiting')}` awaiting, "
        f"`{queue.get('formal_verifier_replay_repair_patch_response_validation_rejected')}` rejected)",
        f"- Formal verifier repair response promotion: `{queue.get('formal_verifier_replay_repair_patch_response_promotion_rows')}` rows "
        f"(`{queue.get('formal_verifier_replay_repair_patch_response_promotion_ready')}` ready, "
        f"`{queue.get('formal_verifier_replay_repair_patch_response_promotion_awaiting')}` awaiting, "
        f"`{queue.get('formal_verifier_replay_repair_patch_response_promotion_blocked')}` blocked)",
        "- Claim-ledger repair-response promotion overlay: "
        f"`{queue.get('claim_ledger_repair_response_promotion_upgrades')}` upgrades from "
        f"`{queue.get('claim_ledger_repair_response_promotion_overlay_rows')}` ready rows",
        f"- Queue: exact_reuse=`{queue.get('reuse_exact_proof_bank_obligation')}`, compose=`{queue.get('compose_existing_bridge_chain')}`, minimal_wrapper=`{queue.get('add_minimal_wrapper')}`, design_bridge=`{queue.get('design_bridge_lemma')}`",
        f"- Theorem composition packets: `{composition.get('theorem_composition_packets')}` "
        f"(exact links `{composition.get('theorem_composition_exact_proof_bank_links')}`, "
        f"unresolved primitives `{composition.get('theorem_composition_unresolved_primitives')}`)",
        "",
        "## Handoff Targets",
        "",
    ]
    for target in queue.get("handoff_targets", []):
        if not isinstance(target, dict):
            continue
        lines.append(
            f"- `{target.get('primitive')}` ({target.get('action_class')}): "
            f"{target.get('suggested_next_step')}"
        )
        lines.append(f"  query: `{target.get('query_hint')}`")
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

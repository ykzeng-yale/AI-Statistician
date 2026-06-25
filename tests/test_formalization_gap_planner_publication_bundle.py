from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.formalization_gap_planner_contract import (
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    portable_gap_plan_row_json_schema,
    route_alignment_edge_json_schema,
)
from ai_statistician.formalization_gap_planner_adapter_registry import (
    adapter_registry_row_json_schema,
)
from ai_statistician.formalization_gap_planner_benchmark import (
    benchmark_route_row_json_schema,
)
from ai_statistician.formalization_gap_planner_ablation_study import (
    ablation_study_row_json_schema,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    PORTABLE_REUSE_TARGETS,
    component_resource_contract_row_json_schema,
    component_resource_registry_component_row_json_schema,
    component_resource_registry_resource_row_json_schema,
    export_formalization_gap_planner_component_resource_registry,
)
from ai_statistician.formalization_gap_planner_evaluation import (
    evaluation_row_json_schema,
)
from ai_statistician.formalization_gap_planner_interactive_session import (
    interactive_decision_policy_row_json_schema,
    interactive_session_row_json_schema,
)
from ai_statistician.formalization_gap_planner_library_coverage_map import (
    PROOF_EVIDENCE_STATUS as LIBRARY_COVERAGE_MAP_PROOF_EVIDENCE_STATUS,
    library_coverage_map_row_json_schema,
)
from ai_statistician.formalization_gap_planner_local_formal_source_adapter import (
    LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES,
)
from ai_statistician.formalization_gap_planner_llm_route_planner import (
    LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID,
    LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID,
    LLM_ROUTE_PLANNER_PROVIDER_USAGE_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID,
    LLM_ROUTE_PLANNER_ROW_SCHEMA_ID,
    LLM_ROUTE_PLANNER_TARGET_THEOREM_CONTEXT_PACKET_SCHEMA_ID,
    PROVIDER_EXECUTION_MODE_PROMPT_ONLY_STAGED,
    PROOF_EVIDENCE_BOUNDARY as LLM_ROUTE_PLANNER_PROOF_EVIDENCE_BOUNDARY,
    ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE,
    ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID,
    ROUTE_ADOPTION_BLOCKER_VALUES,
    export_formalization_gap_planner_llm_route_planner,
    llm_route_planner_library_alignment_summary_json_schema,
    llm_route_planner_provider_usage_row_json_schema,
    llm_route_planner_route_planning_brief_json_schema,
    llm_route_planner_target_theorem_context_packet_json_schema,
    route_adoption_blocker_taxonomy_json_schema,
    validate_formalization_gap_planner_llm_route_planner_response_payloads,
    validate_route_adoption_blocker_taxonomy_payload,
)
from ai_statistician.formalization_gap_planner_route_adoption_blockers import (
    ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID,
    route_adoption_blocker_taxonomy_manifest_json_schema,
)
from ai_statistician.formalization_gap_planner_primitive_action_queue import (
    PROOF_EVIDENCE_STATUS as PRIMITIVE_ACTION_QUEUE_PROOF_EVIDENCE_STATUS,
    primitive_action_queue_row_json_schema,
)
from ai_statistician.formalization_gap_planner_action_resource_plan import (
    action_resource_plan_row_json_schema,
)
from ai_statistician.formalization_gap_planner_resource_request_queue import (
    resource_request_queue_row_json_schema,
)
from ai_statistician.formalization_gap_planner_resource_response_ledger import (
    resource_response_json_schema,
    resource_response_ledger_row_json_schema,
)
from ai_statistician.formalization_gap_planner_minimal_delta_audit import (
    minimal_delta_decision_row_json_schema,
)
from ai_statistician.formalization_gap_planner_portable_plan_audit import (
    portable_plan_audit_row_json_schema,
)
from ai_statistician.formalization_gap_planner_proof_state_triage import (
    proof_state_triage_row_json_schema,
)
from ai_statistician.formalization_gap_planner_prover_adapter_contract import (
    FORMAL_ATTEMPT_DEPENDENCY_PROTOCOL,
    prover_adapter_packet_json_schema,
    prover_adapter_response_json_schema,
    prover_adapter_response_validation_row_json_schema,
)
from ai_statistician.formalization_gap_planner_cross_prover_matrix_audit import (
    CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
    cross_prover_matrix_audit_row_json_schema,
    cross_prover_target_summary_json_schema,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    refinement_evidence_row_json_schema,
    refinement_tool_response_json_schema,
)
from ai_statistician.formalization_gap_planner_refinement_queue import (
    refinement_work_item_json_schema,
)
from ai_statistician.formalization_gap_planner_route_replan_handoff import (
    route_replan_handoff_row_json_schema,
)
from ai_statistician.formalization_gap_planner_route_replan_handoff_audit import (
    route_replan_handoff_audit_row_json_schema,
)
from ai_statistician.formalization_gap_planner_runtime_handoff_audit import (
    RUNTIME_HANDOFF_EXECUTION_PLAN_SCHEMA_ID,
    runtime_handoff_audit_row_json_schema,
    runtime_handoff_execution_plan_json_schema,
)
from ai_statistician.research_agent_runtime import (
    _runtime_formalization_gap_planner_handoff_execution_plan,
)
from ai_statistician.formalization_gap_planner_standalone import (
    FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID,
    llm_route_planner_seed_route_selection_json_schema,
    standalone_input_json_schema,
)
from ai_statistician.formalization_gap_planner_route_stability_audit import (
    route_stability_audit_row_json_schema,
)
from ai_statistician.formalization_gap_planner_route_revision_overlay import (
    route_revision_overlay_row_json_schema,
)
from ai_statistician.formalization_gap_planner_source_grounding_audit import (
    source_grounding_row_json_schema,
)
from ai_statistician.formalization_gap_planner_publication_bundle import (
    FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_LEAN_LEGACY_SCHEMA_ID,
    LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_TARGET_PROVER_SCHEMA_ID,
    export_formalization_gap_planner_publication_bundle,
    publication_bundle_manifest_json_schema,
    schema_catalog_json_schema,
    validate_schema_catalog_payload,
)
from ai_statistician.formalization_gap_planner_publication_bundle_audit import (
    PROOF_EVIDENCE_BOUNDARY_RESOURCE_REQUEST,
    _resource_request_dispatch_spec_errors,
)
from ai_statistician.formalization_gap_planner_target_intake import (
    LEGACY_TARGET_INTAKE_FIELD_ALIASES,
    target_intake_row_json_schema,
)
from ai_statistician.model_backend import (
    ANTHROPIC_MODEL_SOURCE_CHECKED_DATE,
    ANTHROPIC_MODEL_SOURCE_EVIDENCE,
    DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER,
    PROHIBITED_AGENT_GENERATOR_PROVIDERS,
)


def _assert_prompt_only_staged_route_planner_summary(
    summary: dict[str, object],
) -> None:
    assert (
        summary["provider_execution_mode"]
        == PROVIDER_EXECUTION_MODE_PROMPT_ONLY_STAGED
    )
    assert summary["invoke_provider"] is False
    assert summary["response_json_supplied"] is False
    assert summary["static_response_json_supplied"] is False
    assert summary["generator_backend_supplied"] is False
    assert summary["live_provider_backend_requested"] is False
    assert summary["static_generator_backend_requested"] is False
    assert summary["provider_generation_requested"] is False
    assert summary["n_prompt_token_budget_rows"] == summary["n_request_packets"]
    assert summary["max_estimated_prompt_input_tokens"] == 0
    assert summary["n_prompt_token_budget_preflight_blocked"] == 0
    assert summary["prompt_token_budget_preflight_errors"] == []
    assert summary["estimated_prompt_input_tokens"] > 0
    assert summary["estimated_prompt_max_output_tokens"] == 9000
    assert summary["estimated_prompt_total_token_budget"] == (
        summary["estimated_prompt_input_tokens"] + 9000
    )
    assert summary["estimated_prompt_input_cost_micro_usd"] == (
        summary["estimated_prompt_input_tokens"] * 3
    )
    assert summary["estimated_prompt_max_output_cost_micro_usd"] == 9000 * 15
    assert summary["estimated_prompt_base_input_output_cost_micro_usd"] == (
        summary["estimated_prompt_input_cost_micro_usd"]
        + summary["estimated_prompt_max_output_cost_micro_usd"]
    )
    assert summary["n_prompt_token_budget_rows_with_estimated_base_cost"] == (
        summary["n_prompt_token_budget_rows"]
    )
    assert summary["prompt_token_budget_summary"]["row_count"] == (
        summary["n_prompt_token_budget_rows"]
    )


def _assert_no_route_planner_execution_summary(summary: dict[str, object]) -> None:
    assert summary["provider_execution_mode"] == ""
    assert summary["invoke_provider"] is False
    assert summary["response_json_supplied"] is False
    assert summary["static_response_json_supplied"] is False
    assert summary["generator_backend_supplied"] is False
    assert summary["live_provider_backend_requested"] is False
    assert summary["static_generator_backend_requested"] is False
    assert summary["provider_generation_requested"] is False
    assert summary["estimated_prompt_input_cost_micro_usd"] == 0
    assert summary["estimated_prompt_max_output_cost_micro_usd"] == 0
    assert summary["estimated_prompt_base_input_output_cost_micro_usd"] == 0
    assert summary["n_prompt_token_budget_rows_with_estimated_base_cost"] == 0
    assert summary["n_standalone_seed_routes_llm_fallback_routes"] == 0
    assert (
        summary["n_standalone_seed_routes_llm_fallback_routes_marked_adoptable"]
        == 0
    )
    assert (
        summary["n_standalone_seed_routes_llm_fallback_selected_not_adoptable"]
        == 0
    )
    assert summary["n_standalone_seed_routes_with_llm_seed_route_source"] == 0
    assert summary["standalone_seed_route_by_llm_seed_route_source"] == {}
    assert summary["n_standalone_seed_routes_with_llm_fallback_boundary"] == 0


def _write_llm_route_planner_fixture_input(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    input_json = root / "standalone_input.json"
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_snapshot",
                "routes": [
                    {
                        "route_id": "route:fixture",
                        "display_name": "fixture formalization route",
                        "theorem_statement": (
                            "A fixture theorem follows from a source-backed bridge lemma."
                        ),
                        "source_refs": ["fixture_source"],
                        "source_snippets": [
                            {
                                "source_ref": "fixture_source",
                                "claim": (
                                    "The source-backed bridge lemma supplies "
                                    "the route's mathematical dependency."
                                ),
                                "excerpt": (
                                    "The fixture source states that the bridge "
                                    "conclusion follows from the source "
                                    "assumption."
                                ),
                                "target_primitives": ["bridge_conclusion"],
                            }
                        ],
                        "primitives": [
                            {
                                "primitive": "source_assumption",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Fixture.sourceAssumption"],
                            },
                            {
                                "primitive": "bridge_conclusion",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["source_assumption"],
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return input_json


def _write_prompt_only_llm_route_planner_artifact(
    root: Path,
    *,
    resource_response_ledger_dir: Path | None = None,
    route_replan_handoff_dir: Path | None = None,
    refinement_evidence_dir: Path | None = None,
) -> Path:
    input_json = _write_llm_route_planner_fixture_input(root)
    out_dir = root / "llm_route_planner"
    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_ledger_dir
        ),
        formalization_gap_planner_route_replan_handoff_dir=route_replan_handoff_dir,
        formalization_gap_planner_refinement_evidence_dir=refinement_evidence_dir,
    )
    assert payload["all_ok"]
    return out_dir


def _patch_llm_route_planner_provider_usage_manifest(
    out_dir: Path,
    *,
    model: str,
    model_tier: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
    ledger_rows: int = 1,
    ledger_escalations: int = 0,
    provider_failure_rows: int = 0,
    generated_escalations: int = 0,
    haiku_to_sonnet_escalations: int = 0,
) -> None:
    manifest_path = out_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    total_tokens = (
        input_tokens
        + output_tokens
        + cache_creation_input_tokens
        + cache_read_input_tokens
    )
    pricing = {
        "haiku": {"input": 1, "output": 5},
        "sonnet": {"input": 3, "output": 15},
        "opus": {"input": 5, "output": 25},
    }.get(model_tier, {"input": 0, "output": 0})
    estimated_input_cost = input_tokens * int(pricing["input"])
    estimated_output_cost = output_tokens * int(pricing["output"])
    estimated_base_cost = estimated_input_cost + estimated_output_cost
    cache_tokens_excluded = cache_creation_input_tokens + cache_read_input_tokens
    bucket = {
        "n_rows": 1,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_input_tokens": cache_creation_input_tokens,
        "cache_read_input_tokens": cache_read_input_tokens,
        "total_tokens": total_tokens,
        "estimated_input_cost_micro_usd": estimated_input_cost,
        "estimated_output_cost_micro_usd": estimated_output_cost,
        "estimated_base_input_output_cost_micro_usd": estimated_base_cost,
        "estimated_cache_tokens_excluded_from_base_cost": cache_tokens_excluded,
        "n_rows_with_estimated_base_cost": int(estimated_base_cost > 0),
    }
    manifest.update(
        {
            "provider_usage_summary": {
                "summary_kind": (
                    "formalization_gap_planner_llm_route_planner_provider_usage_summary"
                ),
                "row_count": 1,
                **bucket,
                "by_provider": {"anthropic": bucket},
                "by_model_tier": {model_tier: bucket},
                "by_model": {model: bucket},
            },
            "n_rows_with_provider_usage": 1,
            "total_provider_input_tokens": input_tokens,
            "total_provider_output_tokens": output_tokens,
            "total_provider_cache_creation_input_tokens": (
                cache_creation_input_tokens
            ),
            "total_provider_cache_read_input_tokens": cache_read_input_tokens,
            "total_provider_total_tokens": total_tokens,
            "total_provider_estimated_input_cost_micro_usd": estimated_input_cost,
            "total_provider_estimated_output_cost_micro_usd": estimated_output_cost,
            "total_provider_estimated_base_input_output_cost_micro_usd": (
                estimated_base_cost
            ),
            "total_provider_estimated_cache_tokens_excluded_from_base_cost": (
                cache_tokens_excluded
            ),
            "n_provider_usage_rows_with_estimated_base_cost": int(
                estimated_base_cost > 0
            ),
            "n_model_tier_decision_ledger_rows": ledger_rows,
            "n_model_tier_decision_ledger_rows_with_escalation": ledger_escalations,
            "n_model_tier_decision_ledger_provider_failure_rows": (
                provider_failure_rows
            ),
            "n_provider_failures": provider_failure_rows,
            "n_generated_responses_model_tier_escalated": generated_escalations,
            "n_generated_responses_haiku_to_sonnet_escalated": (
                haiku_to_sonnet_escalations
            ),
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _write_formal_source_retrieval_refinement_evidence(root: Path) -> Path:
    evidence_dir = root / "refinement_evidence_formal_source_retrieval"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "search_backend": "sqlite_fts_shape+local_char_ngram_semantic",
        "semantic_rerank_enabled": True,
        "semantic_provider_id": "local_char_ngram",
        "semantic_candidate_multiplier": 8,
        "semantic_weight": 8.0,
    }
    (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_refinement_evidence",
                "n_evidence_rows": 1,
                "n_rows_with_formal_source_retrieval_metadata": 1,
                "n_formal_grounding_rows_with_semantic_rerank": 1,
                "rows": [
                    {
                        "refinement_evidence_id": (
                            "refinement-evidence:fixture-route:formal-source"
                        ),
                        "refinement_item_id": "refinement:fixture-route:formal",
                        "goal_plan_id": "goal:fixture-route",
                        "route_id": "route:fixture",
                        "display_name": "fixture formalization route",
                        "hook_kind": "formal_library_grounding",
                        "response_present": True,
                        "response_contract_ok": True,
                        "evidence_kind": "formal_library_grounding",
                        "tool_name": "local_formal_source_index_adapter",
                        "target_prover_family": "lean4",
                        "target_primitives": ["bridge_conclusion"],
                        "formal_source_retrieval_metadata": metadata,
                        "formal_declaration_hits": [
                            {
                                "primitive": "bridge_conclusion",
                                "declaration": "Fixture.bridgeConclusion",
                                "source_type": "lean_library",
                                "target_prover_family": "lean4",
                                "matched_terms": ["local_char_ngram_semantic"],
                            }
                        ],
                        "coverage_updates": {"bridge_conclusion": "wrapper_needed"},
                        "route_revision_recommended": True,
                        "route_revision_reasons": [
                            "bridge_conclusion classified as wrapper_needed",
                        ],
                        "acceptance_status": (
                            "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE"
                        ),
                        "ok": True,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return evidence_dir


def _write_resource_feedback_response_ledger(root: Path) -> Path:
    ledger_dir = root / "resource_response_ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (
        ledger_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_response_ledger",
                "n_ledger_rows": 1,
                "rows": [
                    {
                        "resource_response_ledger_id": (
                            "resource-response:fixture-route"
                        ),
                        "resource_request_id": "resource-request:fixture-route",
                        "goal_plan_id": "goal:fixture-route",
                        "route_id": "route:fixture",
                        "display_name": "fixture formalization route",
                        "primitive": "bridge_conclusion",
                        "target_primitives": ["bridge_conclusion"],
                        "resource_id": "paperclip_mcp",
                        "expected_response_artifact": "source_evidence",
                        "priority_score": 88,
                        "minimal_delta_cost_score": 40,
                        "reuse_readiness_score": 70,
                        "evidence_readiness_score": 90,
                        "priority_rationale": [
                            "coverage_status=bridge_needed",
                            "minimal_delta_cost_score=40",
                            "reuse_readiness_score=70",
                            "evidence_readiness_score=90",
                        ],
                        "acceptance_gate": (
                            "source evidence must satisfy queued contract fields"
                        ),
                        "response_present": True,
                        "response_contract_minimum_met": True,
                        "response_contract_ok": True,
                        "response_summary": (
                            "Paperclip extracted source-backed bridge evidence "
                            "for the fixture route."
                        ),
                        "response_payload": {
                            "source_snippets": [
                                {
                                    "source_ref": "fixture_source",
                                    "claim": (
                                        "the bridge conclusion follows after "
                                        "the source assumption is available"
                                    ),
                                }
                            ],
                            "route_revision_recommended": True,
                        },
                        "response_artifacts": ["paperclip://fixture-bridge"],
                        "source_refs": ["fixture_source"],
                        "request_playbook_present": True,
                        "response_playbook_grounded": True,
                        "response_playbook_grounding_terms": [
                            "bridge_conclusion",
                            "source_assumption",
                        ],
                        "route_evidence_nodes": [
                            {
                                "node_id": "paperclip:bridge_conclusion",
                                "claim": (
                                    "the bridge conclusion needs the source "
                                    "assumption as an explicit premise"
                                ),
                            }
                        ],
                        "formal_declaration_hits": [
                            {
                                "declaration": "Fixture.bridgeConclusion",
                                "target_prover_family": "lean4",
                                "source_field": "formal_declaration_hits",
                            }
                        ],
                        "coverage_updates": {"bridge_conclusion": "bridge_needed"},
                        "residual_goals": [
                            "bridge_conclusion: expose source_assumption premise"
                        ],
                        "route_revision_recommended": True,
                        "route_revision_reasons": [
                            "add source_assumption as an explicit bridge premise"
                        ],
                        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ledger_dir


def _write_formal_attempt_feedback_handoff(root: Path) -> Path:
    handoff_dir = root / "route_replan_handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    formal_attempt_context = {
        "attempt_id": "attempt:fixture_bridge_conclusion",
        "formal_node_id": "formal:bridge_conclusion",
        "formal_attempt_queue_index": 0,
        "formal_attempt_dependency_status": "initial_ready",
        "attempt_kind": "bridge_proof",
        "primitive": "bridge_conclusion",
        "target_primitives": ["bridge_conclusion"],
        "target_prover_family": "lean4",
        "prerequisite_formal_node_ids": [],
        "prerequisite_attempt_ids": [],
        "missing_prerequisite_formal_node_ids": [],
        "expected_feedback": ["residual_goals", "diagnostic_signature"],
    }
    (
        handoff_dir
        / "formalization_gap_planner_route_replan_handoff_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_replan_handoff",
                "rows": [
                    {
                        "route_replan_handoff_id": (
                            "handoff:fixture_formal_attempt_feedback"
                        ),
                        "route_revision_overlay_id": (
                            "overlay:fixture_formal_attempt_feedback"
                        ),
                        "goal_plan_id": "goal:fixture-route",
                        "route_id": "route:fixture",
                        "display_name": "fixture formalization route",
                        "applied_hook_kinds": ["resource_response_ledger"],
                        "applied_resource_response_traces": [
                            {
                                "resource_response_ledger_id": (
                                    "ledger:fixture_formal_attempt"
                                ),
                                "resource_request_id": (
                                    "request:fixture_formal_attempt"
                                ),
                                "resource_id": "lean_lsp_mcp",
                                "target_primitives": ["bridge_conclusion"],
                                "formal_attempt_context": formal_attempt_context,
                                "residual_goals": [
                                    (
                                        "bridge_conclusion: missing source_assumption "
                                        "side condition"
                                    )
                                ],
                                "prover_attempt_status": (
                                    "failed_with_residual_goals"
                                ),
                                "prover_diagnostic_signature": (
                                    "residual_goal:fixture_bridge_side_condition"
                                ),
                                "route_revision_recommended": True,
                                "route_revision_reasons": [
                                    (
                                        "formal attempt exposed a bridge side "
                                        "condition"
                                    )
                                ],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return handoff_dir


def _write_llm_response_payload_validation_artifact(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    response_json = root / "response_payload.json"
    response_json.write_text(
        json.dumps(
            {
                "informal_knowledge_dag_nodes": [
                    {
                        "node_id": "informal:rank_uniformity",
                        "claim": "Exchangeability gives a finite-rank route.",
                        "depends_on": [],
                        "source_refs": ["fixture_source"],
                        "source_search_status": "SOURCE_BACKED",
                        }
                    ],
                    "informal_knowledge_dag_edges": [],
                    "formal_realization_dag_nodes": [
                        {
                            "node_id": "formal:rank_uniformity_bridge",
                            "primitive": "rank_uniformity",
                            "coverage_bucket": "bridge_needed",
                            "formalization_action": "prove_bridge",
                            "target_prover_family": "lean4",
                        }
                    ],
                    "formal_realization_dag_edges": [],
                    "lean_realization_dag_nodes": [
                        {
                            "node_id": "formal:rank_uniformity_bridge",
                        "primitive": "rank_uniformity",
                        "coverage_bucket": "bridge_needed",
                        "formalization_action": "prove_bridge",
                    }
                ],
                "route_alignment_edges": [
                    {
                        "informal_node_id": "informal:rank_uniformity",
                        "formal_node_id": "formal:rank_uniformity_bridge",
                        "alignment_status": "bridge_needed",
                        "alignment_rationale": "One bridge lemma is enough.",
                        }
                    ],
                    "formal_attempt_queue": [
                        {
                            "attempt_id": "attempt:rank_uniformity_bridge",
                            "formal_node_id": "formal:rank_uniformity_bridge",
                            "primitive": "rank_uniformity",
                            "target_prover_family": "lean4",
                            "owner": "lean_lsp",
                            "action": "attempt the rank-uniformity bridge lemma",
                            "attempt_kind": "bridge_proof",
                            "prerequisite_formal_node_ids": [],
                            "expected_feedback": ["residual_goals"],
                            "target_primitives": ["rank_uniformity"],
                        }
                    ],
                    "minimal_delta_plan": {
                    "selected_primitives": ["rank_uniformity"],
                    "cost_model_version": "formalization_gap_planner_minimal_delta_cost_policy:1",
                    "route_cost": 4,
                    "primitive_costs": [
                        {
                            "primitive": "rank_uniformity",
                            "coverage_bucket": "bridge_needed",
                            "base_cost": 4,
                            "proof_difficulty_cost": 0,
                            "import_cone_cost": 0,
                            "definition_or_typeclass_cost": 0,
                            "semantic_risk_cost": 0,
                            "reuse_credit": 0,
                            "total_cost": 4,
                            "cost_rationale": "A focused bridge lemma is minimal.",
                        }
                    ],
                    "and_or_cost_graph": {
                        "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                        "selected_route_option_id": "route_option:bridge",
                        "route_options": [
                            {
                                "route_option_id": "route_option:bridge",
                                "selected": True,
                                "selected_primitives": ["rank_uniformity"],
                                "route_cost": 4,
                                "cost_rationale": "The bridge route is cheapest.",
                            }
                        ],
                        "or_nodes": [
                            {
                                "node_id": "or:rank_uniformity",
                                "choices": ["route_option:bridge"],
                                "selection_rationale": "Only one bounded route is needed.",
                            }
                        ],
                        "and_edges": [
                            {
                                "route_option_id": "route_option:bridge",
                                "requires": ["rank_uniformity"],
                            }
                        ],
                    },
                    "minimality_rationale": "Add only the rank-uniformity bridge.",
                },
                "standalone_route": {
                    "route_id": "rank_route",
                    "display_name": "rank route",
                    "theorem_statement": "A finite-rank route follows from exchangeability.",
                    "source_refs": ["fixture_source"],
                    "primitives": [
                        {
                            "primitive": "rank_uniformity",
                            "coverage_status": "bridge_needed",
                            "source_refs": ["fixture_source"],
                        }
                    ],
                },
                "proof_evidence_boundary": LLM_ROUTE_PLANNER_PROOF_EVIDENCE_BOUNDARY,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_dir = root / "payload_validation"
    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
    )
    assert payload["all_ok"]
    return out_dir


def _fixture_residual_goal_context() -> dict[str, object]:
    return {
        "source_kind": "proof_state_feedback",
        "residual_goal": "rank_uniformity requires an explicit bridge lemma",
        "residual_goals": ["rank_uniformity"],
        "residual_primitives": ["rank_uniformity"],
        "source_refs": ["fixture-source"],
        "source_snippets": [
            {
                "source_ref": "fixture-source",
                "text": "Fixture source backs the residual bridge obligation.",
            }
        ],
        "formal_gap_boundary": (
            "Formal boundary: residual context guides adapter mapping but is "
            "not kernel proof evidence."
        ),
    }


def _fixture_prover_adapter_packet() -> dict[str, object]:
    residual_context = _fixture_residual_goal_context()
    return {
        "schema_version": 1,
        "prover_adapter_packet_id": "packet:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "packet_index": 1,
        "primitive": "rank_uniformity",
        "action_class": "bridge_lemma",
        "worker_packet_kind": "prove_bridge_lemma",
        "expected_cost": "small",
        "required_gate": "target prover kernel verification",
        "source_prover_family": "lean4",
        "target_prover_family": "rocq",
        "library_snapshot_ref": "rocq_fixture",
        "portable_work_packet": {
            "primitive": "rank_uniformity",
            "worker_packet_kind": "prove_bridge_lemma",
        },
        "standalone_input_trace": {
            "source_route_id": "route:fixture",
            "route_index": 1,
            "source_prover_family": "lean4",
            "source_target_prover_family": "lean4",
            "target_prover_family": "rocq",
            "target_library_snapshot_ref": "rocq_fixture",
            "trace_target_projection": "target_prover_adapter_contract",
            "llm_route_planner_route_adoption_status": (
                "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
            ),
            "llm_route_planner_route_adoption_blockers": [
                "search_requests_pending_evidence",
                "uncertainty_flags_require_review",
            ],
            "has_replan_metadata": True,
            "replan_metadata": {"revision_reason": "fixture route revision"},
            "residual_goal_contexts": [residual_context],
            "has_residual_goal_contexts": True,
            "residual_goal_context_count": 1,
            "residual_context_source_kinds": ["proof_state_feedback"],
            "applied_hook_kinds": ["resource_response_ledger"],
            "formal_attempt_queue_index": -1,
            "formal_attempt_initial_ready": False,
            "formal_attempt_dependency_status": "not_formal_attempt_queue_item",
            "formal_attempt_prerequisite_formal_node_ids": [],
            "formal_attempt_prerequisite_refinement_item_ids": [],
            "formal_attempt_blocking_prerequisite_formal_node_ids": [],
            "formal_attempt_missing_prerequisite_formal_node_ids": [],
            "formal_attempt_dependency_protocol": FORMAL_ATTEMPT_DEPENDENCY_PROTOCOL,
            "minimal_delta_action_witnesses": [],
            "minimal_delta_action_witness_count": 0,
            "has_minimal_delta_action_witness": False,
        },
        "residual_goal_contexts": [residual_context],
        "n_residual_goal_contexts": 1,
        "residual_context_source_kinds": ["proof_state_feedback"],
        "n_residual_contexts_with_source_refs": 1,
        "n_residual_contexts_with_formal_gap_boundary": 1,
        "llm_route_planner_route_adoption_status": (
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
        ),
        "llm_route_planner_route_adoption_blockers": [
            "search_requests_pending_evidence",
            "uncertainty_flags_require_review",
        ],
        "formal_attempt_queue_index": -1,
        "formal_attempt_initial_ready": False,
        "formal_attempt_dependency_status": "not_formal_attempt_queue_item",
        "formal_attempt_prerequisite_formal_node_ids": [],
        "formal_attempt_prerequisite_refinement_item_ids": [],
        "formal_attempt_blocking_prerequisite_formal_node_ids": [],
        "formal_attempt_missing_prerequisite_formal_node_ids": [],
        "formal_attempt_dependency_protocol": FORMAL_ATTEMPT_DEPENDENCY_PROTOCOL,
        "minimal_delta_action_witnesses": [],
        "minimal_delta_action_witness_count": 0,
        "has_minimal_delta_action_witness": False,
        "route_alignment_edge": {
            "source": "informal:rank_uniformity",
            "target": "formal:rank_uniformity",
            "kind": "aligned_to_formal_realization_candidate",
            "edge_type": "informal_to_formal_alignment",
            "primitive": "rank_uniformity",
            "action_class": "bridge_lemma",
            "alignment_status": "bridge_delta",
            "proof_evidence_status": (
                "GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": "not theorem proof evidence",
        },
        "alignment_status": "bridge_delta",
        "informal_route_node_id": "informal:rank_uniformity",
        "formal_realization_node_id": "formal:rank_uniformity",
        "required_adapter_response_fields": [
            "target_prover_family",
            "primitive",
            "mapping_status",
            "translated_statement",
            "translated_imports",
            "verifier_command",
            "library_snapshot_ref",
            "semantic_alignment_notes",
            "kernel_verified",
        ],
        "acceptance_gate": "target prover kernel verification through replay",
        "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }


def _fixture_prover_adapter_response_validation_row(
    packet: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "response_validation_id": "response-validation:fixture",
        "prover_adapter_packet_id": str(packet["prover_adapter_packet_id"]),
        "goal_plan_id": str(packet["goal_plan_id"]),
        "route_id": str(packet["route_id"]),
        "display_name": str(packet["display_name"]),
        "primitive": str(packet["primitive"]),
        "target_prover_family": str(packet["target_prover_family"]),
        "response_present": False,
        "response_contract_ok": False,
        "mapping_status": "",
        "translated_statement": "",
        "translated_imports": [],
        "verifier_command": "",
        "library_snapshot_ref": "",
        "semantic_alignment_notes": "",
        "residual_translation_gaps": [],
        "minimal_delta_action_witness_count": 0,
        "minimal_delta_action_witness_acknowledged": True,
        "addressed_minimal_delta_action_witnesses": [],
        "formal_attempt_dependency_status": "not_formal_attempt_queue_item",
        "prerequisite_feedback_satisfied": False,
        "prerequisite_response_ids": [],
        "kernel_verified_claimed": False,
        "acceptance_status": "AWAITING_PROVER_ADAPTER_MAPPING",
        "proof_evidence_status": "AWAITING_RESPONSE_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }


def _fixture_cross_prover_matrix_row(
    packet: dict[str, object],
    validation: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "matrix_row_id": "cross-prover-matrix:fixture",
        "target_prover_family": str(packet["target_prover_family"]),
        "target_library_snapshot_ref": "cross_prover_matrix:rocq",
        "contract_dir": "target_contracts/rocq",
        "contract_manifest_path": "target_contracts/rocq/manifest.json",
        "packet_jsonl_path": "target_contracts/rocq/packets.jsonl",
        "response_validation_jsonl_path": "target_contracts/rocq/validation.jsonl",
        "n_plan_rows": 1,
        "n_packets": 1,
        "n_packet_ok": 1,
        "n_packet_schema_valid": 1,
        "n_packets_schema_invalid": 0,
        "n_packets_with_alignment": 1,
        "n_packets_missing_alignment": 0,
        "n_packets_with_standalone_input_trace": 1,
        "n_packets_missing_standalone_input_trace": 0,
        "n_packets_with_target_library_snapshot_trace": 1,
        "n_packets_missing_target_library_snapshot_trace": 0,
        "n_packets_target_library_snapshot_mismatch": 0,
        "n_packets_with_replan_metadata_trace": 1,
        "n_packets_with_residual_goal_contexts": 1,
        "n_packet_residual_goal_contexts": 1,
        "packet_residual_context_source_kinds": ["proof_state_feedback"],
        "n_packet_residual_contexts_with_source_refs": 1,
        "n_packet_residual_contexts_with_formal_gap_boundary": 1,
        "n_packets_with_quality_controls": 1,
        "n_packet_quality_control_fields": 4,
        "packet_quality_control_fields": [
            "required_quality_signals",
            "resource_contract_ids",
            "response_validation_signals",
            "stop_conditions",
        ],
        "packet_quality_control_resource_contract_ids": [
            "lean_lsp:proof_state_feedback"
        ],
        "packet_quality_control_response_validation_signals": [
            "residual_goals_or_diagnostics_present"
        ],
        "packet_quality_control_stop_conditions": [
            "residual interpreted or source search requested"
        ],
        "by_packet_quality_control_field": {
            "required_quality_signals": {
                "n_packets": 1,
                "n_values": 1,
                "values": ["diagnostic_signature"],
            },
            "resource_contract_ids": {
                "n_packets": 1,
                "n_values": 1,
                "values": ["lean_lsp:proof_state_feedback"],
            },
            "response_validation_signals": {
                "n_packets": 1,
                "n_values": 1,
                "values": ["residual_goals_or_diagnostics_present"],
            },
            "stop_conditions": {
                "n_packets": 1,
                "n_values": 1,
                "values": ["residual interpreted or source search requested"],
            },
        },
        "n_packets_with_llm_route_adoption_status": 1,
        "n_packets_llm_route_adoption_ready": 0,
        "n_packets_llm_route_adoption_pending_refinement": 1,
        "n_packets_llm_route_adoption_rejected": 0,
        "n_packets_llm_route_adoption_awaiting_response": 0,
        "n_packet_llm_route_adoption_blockers": 2,
        "n_packet_llm_route_adoption_pending_quality_control_blockers": 1,
        "n_packet_llm_route_adoption_pending_source_grounding_blockers": 0,
        "by_packet_llm_route_adoption_status": {
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
        },
        "n_packets_with_formal_attempt_dependency": 0,
        "n_packets_formal_attempt_initial_ready": 0,
        "n_packets_formal_attempt_waiting": 0,
        "n_packets_formal_attempt_missing_prerequisites": 0,
        "by_packet_formal_attempt_dependency_status": {
            "not_formal_attempt_queue_item": 1
        },
        "n_response_present": 0,
        "n_awaiting_adapter_mapping": 1,
        "n_response_contract_ok": 0,
        "n_response_minimal_delta_action_witnesses_required": 0,
        "n_response_minimal_delta_action_witnesses_acknowledged": 0,
        "n_response_minimal_delta_action_witnesses_unacknowledged": 0,
        "n_response_addressed_minimal_delta_action_witnesses": 0,
        "n_rejected": 0,
        "n_kernel_verified_claims_rejected": 0,
        "packet_fingerprint": str(packet["prover_adapter_packet_id"]),
        "response_validation_fingerprint": str(validation["response_validation_id"]),
        "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_CONTRACT_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }


def _fixture_cross_prover_target_summary(
    packet: dict[str, object],
) -> dict[str, object]:
    target = str(packet["target_prover_family"])
    return {
        "schema_version": 1,
        "schema_id": CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
        "component_name": "formalization_gap_planner_cross_prover_target_summary",
        "n_target_rows": 1,
        "n_targets_ok": 1,
        "n_total_packets": 1,
        "n_total_packets_with_alignment": 1,
        "n_total_packets_with_standalone_input_trace": 1,
        "n_total_packets_missing_standalone_input_trace": 0,
        "n_total_packets_with_target_library_snapshot_trace": 1,
        "n_total_packets_missing_target_library_snapshot_trace": 0,
        "n_total_packets_target_library_snapshot_mismatch": 0,
        "n_total_packets_with_replan_metadata_trace": 1,
        "n_total_packets_with_residual_goal_contexts": 1,
        "n_total_packet_residual_goal_contexts": 1,
        "packet_residual_context_source_kinds": ["proof_state_feedback"],
        "n_total_packet_residual_contexts_with_source_refs": 1,
        "n_total_packet_residual_contexts_with_formal_gap_boundary": 1,
        "n_total_packets_with_quality_controls": 1,
        "n_total_packet_quality_control_fields": 4,
        "packet_quality_control_fields": [
            "required_quality_signals",
            "resource_contract_ids",
            "response_validation_signals",
            "stop_conditions",
        ],
        "packet_quality_control_resource_contract_ids": [
            "lean_lsp:proof_state_feedback"
        ],
        "packet_quality_control_response_validation_signals": [
            "residual_goals_or_diagnostics_present"
        ],
        "packet_quality_control_stop_conditions": [
            "residual interpreted or source search requested"
        ],
        "by_total_packet_quality_control_field": {
            "required_quality_signals": {
                "n_packets": 1,
                "n_values": 1,
                "values": ["diagnostic_signature"],
            },
            "resource_contract_ids": {
                "n_packets": 1,
                "n_values": 1,
                "values": ["lean_lsp:proof_state_feedback"],
            },
            "response_validation_signals": {
                "n_packets": 1,
                "n_values": 1,
                "values": ["residual_goals_or_diagnostics_present"],
            },
            "stop_conditions": {
                "n_packets": 1,
                "n_values": 1,
                "values": ["residual interpreted or source search requested"],
            },
        },
        "n_total_packets_with_llm_route_adoption_status": 1,
        "n_total_packets_llm_route_adoption_ready": 0,
        "n_total_packets_llm_route_adoption_pending_refinement": 1,
        "n_total_packets_llm_route_adoption_rejected": 0,
        "n_total_packets_llm_route_adoption_awaiting_response": 0,
        "n_total_packet_llm_route_adoption_blockers": 2,
        "n_total_packet_llm_route_adoption_pending_quality_control_blockers": 1,
        "n_total_packet_llm_route_adoption_pending_source_grounding_blockers": 0,
        "by_total_packet_llm_route_adoption_status": {
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
        },
        "n_total_packets_with_formal_attempt_dependency": 0,
        "n_total_packets_formal_attempt_initial_ready": 0,
        "n_total_packets_formal_attempt_waiting": 0,
        "n_total_packets_formal_attempt_missing_prerequisites": 0,
        "by_total_packet_formal_attempt_dependency_status": {
            "not_formal_attempt_queue_item": 1
        },
        "n_total_response_minimal_delta_action_witnesses_required": 0,
        "n_total_response_minimal_delta_action_witnesses_acknowledged": 0,
        "n_total_response_minimal_delta_action_witnesses_unacknowledged": 0,
        "n_total_response_addressed_minimal_delta_action_witnesses": 0,
        "target_rows": [
            {
                "target_prover_family": target,
                "target_library_snapshot_ref": "cross_prover_matrix:rocq",
                "n_packets": 1,
                "n_packets_with_alignment": 1,
                "n_packets_with_standalone_input_trace": 1,
                "n_packets_missing_standalone_input_trace": 0,
                "n_packets_with_target_library_snapshot_trace": 1,
                "n_packets_missing_target_library_snapshot_trace": 0,
                "n_packets_target_library_snapshot_mismatch": 0,
                "n_packets_with_replan_metadata_trace": 1,
                "n_packets_with_residual_goal_contexts": 1,
                "n_packet_residual_goal_contexts": 1,
                "packet_residual_context_source_kinds": [
                    "proof_state_feedback"
                ],
                "n_packet_residual_contexts_with_source_refs": 1,
                "n_packet_residual_contexts_with_formal_gap_boundary": 1,
                "n_packets_with_quality_controls": 1,
                "n_packet_quality_control_fields": 4,
                "packet_quality_control_fields": [
                    "required_quality_signals",
                    "resource_contract_ids",
                    "response_validation_signals",
                    "stop_conditions",
                ],
                "packet_quality_control_resource_contract_ids": [
                    "lean_lsp:proof_state_feedback"
                ],
                "packet_quality_control_response_validation_signals": [
                    "residual_goals_or_diagnostics_present"
                ],
                "packet_quality_control_stop_conditions": [
                    "residual interpreted or source search requested"
                ],
                "by_packet_quality_control_field": {
                    "required_quality_signals": {
                        "n_packets": 1,
                        "n_values": 1,
                        "values": ["diagnostic_signature"],
                    },
                    "resource_contract_ids": {
                        "n_packets": 1,
                        "n_values": 1,
                        "values": ["lean_lsp:proof_state_feedback"],
                    },
                    "response_validation_signals": {
                        "n_packets": 1,
                        "n_values": 1,
                        "values": ["residual_goals_or_diagnostics_present"],
                    },
                    "stop_conditions": {
                        "n_packets": 1,
                        "n_values": 1,
                        "values": [
                            "residual interpreted or source search requested"
                        ],
                    },
                },
                "n_packets_with_llm_route_adoption_status": 1,
                "n_packets_llm_route_adoption_ready": 0,
                "n_packets_llm_route_adoption_pending_refinement": 1,
                "n_packets_llm_route_adoption_rejected": 0,
                "n_packets_llm_route_adoption_awaiting_response": 0,
                "n_packet_llm_route_adoption_blockers": 2,
                "n_packet_llm_route_adoption_pending_quality_control_blockers": 1,
                "n_packet_llm_route_adoption_pending_source_grounding_blockers": 0,
                "by_packet_llm_route_adoption_status": {
                    "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
                },
                "n_packets_with_formal_attempt_dependency": 0,
                "n_packets_formal_attempt_initial_ready": 0,
                "n_packets_formal_attempt_waiting": 0,
                "n_packets_formal_attempt_missing_prerequisites": 0,
                "by_packet_formal_attempt_dependency_status": {
                    "not_formal_attempt_queue_item": 1
                },
                "n_response_validation_rows": 1,
                "n_response_minimal_delta_action_witnesses_required": 0,
                "n_response_minimal_delta_action_witnesses_acknowledged": 0,
                "n_response_minimal_delta_action_witnesses_unacknowledged": 0,
                "n_response_addressed_minimal_delta_action_witnesses": 0,
                "aggregate_packet_jsonl_path": (
                    "formalization_gap_planner_cross_prover_packets.jsonl"
                ),
                "aggregate_response_validation_jsonl_path": (
                    "formalization_gap_planner_cross_prover_response_validation.jsonl"
                ),
                "packet_filter_field": "target_prover_family",
                "packet_filter_value": target,
                "response_validation_filter_field": "target_prover_family",
                "response_validation_filter_value": target,
                "source_contract_manifest_path": (
                    "target_contracts/rocq/manifest.json"
                ),
                "ok": True,
                "errors": [],
            }
        ],
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_CROSS_PROVER_MATRIX_AUDIT_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "all_ok": True,
        "errors": [],
    }


def _fixture_library_coverage_map_row() -> dict[str, object]:
    return {
        "schema_version": 1,
        "coverage_map_id": "coverage-map:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:fixture",
        "primitive": "rank_uniformity",
        "coverage_bucket": "bridge_needed",
        "action_class": "design_bridge_lemma",
        "informal_node_id": "informal:rank_uniformity",
        "realization_node_id": "lean:rank_uniformity",
        "realization_node_kind": "bridge_candidate",
        "alignment_status": "bridge_delta",
        "candidate_declarations": ["Fixture.rankUniformity"],
        "declaration_sources": ["Fixture.rankUniformity"],
        "expected_premises": ["exchangeable scores"],
        "bridge_candidate_obligations": ["connect exchangeability to uniform rank"],
        "actionable_work_items": [
            "rank_uniformity: prove bridge from exchangeable scores to uniform rank"
        ],
        "source_refs": ["fixture-source"],
        "route_alignment_edge": {
            "source": "informal:rank_uniformity",
            "target": "lean:rank_uniformity",
            "kind": "aligned_to_formal_realization_candidate",
            "edge_type": "informal_to_formal_alignment",
            "primitive": "rank_uniformity",
            "action_class": "design_bridge_lemma",
            "alignment_status": "bridge_delta",
            "proof_evidence_status": (
                "GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": "not theorem proof evidence",
        },
        "needs_wrapper": False,
        "needs_bridge_lemma": True,
        "needs_source_search": False,
        "needs_new_definition_or_theory": False,
        "needs_prover_feedback": True,
        "reusable_without_new_declaration": False,
        "next_action": "prove a focused bridge lemma for rank_uniformity",
        "proof_evidence_status": LIBRARY_COVERAGE_MAP_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }


def _fixture_primitive_action_queue_row() -> dict[str, object]:
    return {
        "schema_version": 1,
        "primitive_action_id": "primitive-action:fixture",
        "coverage_map_id": "coverage-map:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:fixture",
        "primitive": "rank_uniformity",
        "coverage_bucket": "bridge_needed",
        "action_class": "design_bridge_lemma",
        "queue_action_kind": "prove_bridge_lemma",
        "owner_agent": "formal_verifier",
        "priority_score": 70,
        "rank": 1,
        "candidate_declarations": ["Fixture.rankUniformity"],
        "candidate_declaration_rows": [
            {
                "declaration": "Fixture.rankUniformity",
                "target_prover_family": "lean4",
                "source_field": "candidate_declarations",
            }
        ],
        "source_refs": ["fixture-source"],
        "expected_premises": ["exchangeable scores"],
        "bridge_candidate_obligations": ["connect exchangeability to uniform rank"],
        "actionable_work_items": [
            "rank_uniformity: prove bridge from exchangeable scores to uniform rank"
        ],
        "required_inputs": [
            "coverage map row",
            "portable route alignment edge",
            "target theorem or work packet",
            "bridge candidate obligations",
            "expected premises",
        ],
        "expected_outputs": [
            "bridge lemma statement",
            "bridge proof attempt transcript",
            "residual obligations for route revision",
        ],
        "recommended_tools": [
            "formal verifier",
            "formal source search",
            "proof-state adapter",
        ],
        "acceptance_gate": (
            "bridge lemma is accepted by the target prover or residual obligations "
            "are routed back"
        ),
        "execution_commands": [
            "python3 -m ai_statistician.cli formalization-gap-planner-refinement-queue",
        ],
        "next_action": "prove a focused bridge lemma for rank_uniformity",
        "proof_evidence_status": PRIMITIVE_ACTION_QUEUE_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }


def test_formalization_gap_planner_publication_bundle_cli_copies_llm_planner_artifacts() -> None:
    root = Path("runs/test_formalization_gap_planner_publication_bundle_cli_llm_artifacts")
    shutil.rmtree(root, ignore_errors=True)
    primary_dir = _write_prompt_only_llm_route_planner_artifact(root / "primary")
    feedback_dir = _write_prompt_only_llm_route_planner_artifact(root / "feedback")
    validation_dir = _write_llm_response_payload_validation_artifact(
        root / "payload_validation"
    )
    out_dir = root / "bundle"

    code = main(
        [
            "formalization-gap-planner-publication-bundle",
            "--formalization-gap-planner-llm-route-planner-dir",
            str(primary_dir),
            "--formalization-gap-planner-feedback-llm-route-planner-dir",
            str(feedback_dir),
            "--formalization-gap-planner-llm-route-planner-response-payload-validation-dir",
            str(validation_dir),
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    manifest = json.loads(
        (
            out_dir / "formalization_gap_planner_publication_bundle_manifest.json"
        ).read_text(encoding="utf-8")
    )
    optional_by_name = {
        str(row["artifact_name"]): row for row in manifest["optional_artifacts"]
    }
    assert optional_by_name["formalization_gap_planner_llm_route_planner"][
        "requested"
    ]
    assert optional_by_name["formalization_gap_planner_llm_route_planner"]["ok"]
    optional_manifest_schema = (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_manifest.schema.json"
    )
    assert optional_manifest_schema.exists()
    assert json.loads(optional_manifest_schema.read_text(encoding="utf-8"))[
        "$id"
    ] == LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID
    primary_copied_names = {
        Path(path).name
        for path in optional_by_name["formalization_gap_planner_llm_route_planner"][
            "copied_files"
        ]
    }
    assert (
        "formalization_gap_planner_llm_route_planner_provider_usage.jsonl"
        in primary_copied_names
    )
    assert (
        "formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json"
        in primary_copied_names
    )
    primary_provider_usage_jsonl = (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_provider_usage.jsonl"
    )
    assert primary_provider_usage_jsonl.exists()
    assert primary_provider_usage_jsonl.read_text(encoding="utf-8") == ""
    primary_provider_usage_schema = (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json"
    )
    assert json.loads(primary_provider_usage_schema.read_text(encoding="utf-8"))[
        "$id"
    ] == LLM_ROUTE_PLANNER_PROVIDER_USAGE_ROW_SCHEMA_ID
    assert optional_by_name["formalization_gap_planner_feedback_llm_route_planner"][
        "requested"
    ]
    assert optional_by_name["formalization_gap_planner_feedback_llm_route_planner"]["ok"]
    feedback_copied_names = {
        Path(path).name
        for path in optional_by_name[
            "formalization_gap_planner_feedback_llm_route_planner"
        ]["copied_files"]
    }
    assert (
        "formalization_gap_planner_llm_route_planner_provider_usage.jsonl"
        in feedback_copied_names
    )
    assert (
        "formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json"
        in feedback_copied_names
    )
    feedback_provider_usage_schema = (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_feedback_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json"
    )
    assert json.loads(feedback_provider_usage_schema.read_text(encoding="utf-8"))[
        "$id"
    ] == LLM_ROUTE_PLANNER_PROVIDER_USAGE_ROW_SCHEMA_ID
    assert manifest["llm_route_planner_summary"]["requested"] is True
    _assert_prompt_only_staged_route_planner_summary(
        manifest["llm_route_planner_summary"]
    )
    assert manifest["llm_route_planner_summary"]["n_request_packets"] == 1
    assert (
        manifest["llm_route_planner_summary"][
            "n_target_theorem_context_packets"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_context_packet_inventory"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_context_inventory_total_rows"
        ]
        >= 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_rows_with_context_packet_inventory"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"]["n_rows_with_target_context_summary"]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_target_context_summary_proof_source_refs"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_target_context_summary_proof_source_ref_support_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_target_context_summary_proof_source_ref_support_source_fields"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_available_source_snippets"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_available_source_snippets"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"]["n_requests_with_target_intake_rows"]
        == 0
    )
    assert manifest["llm_route_planner_summary"]["n_request_target_intake_rows"] == 0
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_current_goal_plan_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"]["n_request_current_goal_plan_rows"]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_resource_feedback_readiness_summary"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_resource_feedback_readiness_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_resource_feedback_reuse_ready_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_formal_attempt_feedback_summary"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_formal_attempt_feedback_contexts"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_formal_attempt_feedback_residual_goals"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_formal_attempt_feedback_failed_statuses"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_model_tier_decision_resource_feedback_readiness_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_model_tier_decision_resource_feedback_reuse_ready_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_model_tier_decision_resource_feedback_sonnet_triggers"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_model_tier_decision_formal_attempt_feedback_contexts"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_model_tier_decision_formal_attempt_feedback_residual_goals"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_route_adoption_precondition_known_blockers"
        ]
        >= 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_route_adoption_precondition_required_response_fields"
        ]
        >= 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_route_adoption_precondition_target_primitives"
        ]
        >= 0
    )
    assert manifest["llm_route_planner_summary"]["n_rows_with_provider_usage"] == 0
    assert manifest["llm_route_planner_summary"]["total_provider_input_tokens"] == 0
    assert manifest["llm_route_planner_summary"]["total_provider_output_tokens"] == 0
    assert manifest["llm_route_planner_summary"]["total_provider_total_tokens"] == 0
    assert (
        manifest["llm_route_planner_summary"]["provider_usage_summary"][
            "row_count"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"]["n_prompt_token_budget_rows"]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"]["estimated_prompt_input_tokens"]
        > 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "estimated_prompt_max_output_tokens"
        ]
        == 9000
    )
    assert (
        manifest["llm_route_planner_summary"][
            "estimated_prompt_total_token_budget"
        ]
        == manifest["llm_route_planner_summary"][
            "estimated_prompt_input_tokens"
        ]
        + 9000
    )
    assert (
        manifest["llm_route_planner_summary"][
            "estimated_prompt_input_cost_micro_usd"
        ]
        == manifest["llm_route_planner_summary"]["estimated_prompt_input_tokens"]
        * 3
    )
    assert (
        manifest["llm_route_planner_summary"][
            "estimated_prompt_max_output_cost_micro_usd"
        ]
        == 9000 * 15
    )
    assert (
        manifest["llm_route_planner_summary"][
            "estimated_prompt_base_input_output_cost_micro_usd"
        ]
        == manifest["llm_route_planner_summary"][
            "estimated_prompt_input_cost_micro_usd"
        ]
        + manifest["llm_route_planner_summary"][
            "estimated_prompt_max_output_cost_micro_usd"
        ]
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_prompt_token_budget_rows_with_estimated_base_cost"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_model_tier_decision_ledger_rows"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_model_tier_decision_ledger_rows_with_escalation"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_model_tier_decision_ledger_provider_failure_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_quality_control_obligation_inventory"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_pending_quality_control_values"
        ]
        == 0
    )
    assert manifest["llm_route_planner_summary"]["n_request_residual_goals"] == 0
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_residual_goal_contexts"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"]["n_request_residual_goal_contexts"]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_context_residual_goal_contexts"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_inventory_residual_goal_contexts"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_feedback_loop_summary_prior_llm_route_planner_hook_traces"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_component_resource_registry_context"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_component_resource_registry_resources_in_prompt"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_source_theorem_formal_environment_bridge_context"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_exact_source_theorem_proof_body_executor_context"
        ]
        == 0
    )
    assert manifest["llm_route_planner_summary"]["n_rows"] == 1
    assert manifest["llm_route_planner_summary"]["n_response_present"] == 0
    assert (
        manifest["llm_route_planner_summary"][
            "n_generated_responses_model_tier_escalated"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_generated_responses_haiku_to_sonnet_escalated"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_repair_attempt_ledger_model_tier_escalations"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_rows_with_model_tier_escalation"
        ]
        == 0
    )
    assert manifest["llm_route_planner_summary"]["n_request_model_tier_haiku"] == 0
    assert manifest["llm_route_planner_summary"]["n_request_model_tier_sonnet"] == 1
    assert manifest["llm_route_planner_summary"]["n_request_model_tier_opus"] == 0
    assert manifest["llm_route_planner_summary"]["by_request_model_tier"] == {
        "sonnet": 1
    }
    assert (
        manifest["llm_route_planner_summary"]["n_request_target_prover_families"]
        == 1
    )
    assert manifest["llm_route_planner_summary"][
        "by_request_target_prover_family"
    ] == {"lean4": 1}
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_library_alignment_summary"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_library_alignment_primitives"
        ]
        >= 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_library_alignment_bridge_or_harder_primitives"
        ]
        >= 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_library_alignment_route_options"
        ]
        >= 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_library_alignment_route_option_primitives"
        ]
        >= 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_library_alignment_route_option_bridge_or_harder_primitives"
        ]
        >= 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_library_alignment_route_option_target_compatible_reuse_declarations"
        ]
        >= 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "total_request_library_alignment_route_option_minimum_base_cost"
        ]
        >= 0
    )
    assert manifest["llm_route_planner_summary"][
        "by_request_library_alignment_delta_class"
    ]
    assert manifest["llm_route_planner_summary"][
        "by_request_library_alignment_minimum_coverage_bucket"
    ]
    assert (
        manifest["llm_route_planner_summary"][
            "n_requests_with_route_option_selection_brief"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_route_option_selection_candidate_options"
        ]
        >= 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_route_option_selection_candidate_primitives"
        ]
        >= 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_route_option_selection_candidates_with_residual_goals"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_route_option_selection_candidate_residual_goals"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_route_option_selection_lower_bound_options"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_route_option_selection_lower_bound_residual_goals"
        ]
        == 0
    )
    assert manifest["llm_route_planner_summary"][
        "n_informal_knowledge_dag_nodes"
    ] == 0
    assert manifest["llm_route_planner_summary"][
        "n_formal_realization_dag_nodes"
    ] == 0
    assert manifest["llm_route_planner_summary"][
        "legacy_response_field_aliases"
    ] == {"lean_realization_dag_nodes": "formal_realization_dag_nodes"}
    assert manifest["llm_route_planner_summary"][
        "n_lean_realization_dag_nodes"
    ] == 0
    assert manifest["llm_route_planner_summary"]["n_route_alignment_edges"] == 0
    assert manifest["llm_route_planner_summary"]["n_search_requests"] == 0
    assert manifest["llm_route_planner_summary"]["n_planner_next_actions"] == 0
    assert (
        manifest["llm_route_planner_summary"]["n_rows_with_planner_next_actions"]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"]["n_rows_with_residual_goal_contexts"]
        == 0
    )
    assert manifest["llm_route_planner_summary"]["n_row_residual_goal_contexts"] == 0
    assert manifest["llm_route_planner_summary"]["n_uncertainty_flags"] == 0
    assert manifest["llm_route_planner_summary"]["n_residual_interpretations"] == 0
    assert manifest["llm_route_planner_summary"]["n_source_snippets"] == 0
    assert manifest["llm_route_planner_summary"]["n_rows_with_source_snippets"] == 0
    assert (
        manifest["llm_route_planner_summary"]["n_formal_attempt_queue_items"]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"]["n_rows_with_formal_attempt_queue"]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_agentic_proof_execution_materializer_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_agentic_proof_execution_artifact_verifier_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_agentic_proof_source_theorem_promotion_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_proof_execution_feedback_rows"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_request_proof_execution_unsupported_target_prover_rows"
        ]
        == 0
    )
    assert manifest["llm_route_planner_summary"]["n_accepted_route_plans"] == 0
    assert (
        manifest["llm_route_planner_summary"][
            "n_accepted_with_formal_attempt_queue"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_route_adoption_awaiting_llm_response"
        ]
        == 1
    )
    assert manifest["llm_route_planner_summary"]["standalone_replay_gate_ok"] is False
    assert (
        manifest["llm_route_planner_summary"][
            "n_standalone_replay_route_candidates"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_standalone_replay_adoptable_route_candidates"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_standalone_replay_blocked_route_candidates"
        ]
        == 1
    )
    assert manifest["llm_route_planner_summary"]["standalone_replay_gate_blockers"] == [
        "llm_route_planner_response_missing"
    ]
    assert (
        manifest["llm_route_planner_summary"][
            "n_standalone_seed_routes_llm_fallback_routes"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_standalone_seed_routes_llm_fallback_routes_marked_adoptable"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_standalone_seed_routes_llm_fallback_selected_not_adoptable"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_standalone_seed_routes_with_llm_seed_route_source"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "standalone_seed_route_by_llm_seed_route_source"
        ]
        == {"fallback_input_route": 1}
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_standalone_seed_routes_with_llm_fallback_boundary"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_rows_with_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_row_route_adoption_precondition_known_blockers"
        ]
        >= 0
    )
    assert (
        manifest["llm_route_planner_summary"][
            "n_row_route_adoption_precondition_target_primitives"
        ]
        >= 0
    )
    assert manifest["feedback_llm_route_planner_summary"]["requested"] is True
    _assert_prompt_only_staged_route_planner_summary(
        manifest["feedback_llm_route_planner_summary"]
    )
    assert manifest["feedback_llm_route_planner_summary"]["n_request_packets"] == 1
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_target_theorem_context_packets"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_available_source_snippets"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_rows_with_target_context_summary"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_target_context_summary_proof_source_refs"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_target_context_summary_proof_source_ref_support_rows"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_target_context_summary_proof_source_ref_support_source_fields"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_available_source_snippets"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_model_tier_sonnet"
        ]
        == 1
    )
    assert manifest["feedback_llm_route_planner_summary"][
        "by_request_model_tier"
    ] == {"sonnet": 1}
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_target_prover_families"
        ]
        == 1
    )
    assert manifest["feedback_llm_route_planner_summary"][
        "by_request_target_prover_family"
    ] == {"lean4": 1}
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_library_alignment_summary"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_library_alignment_primitives"
        ]
        >= 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_library_alignment_route_options"
        ]
        >= 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_route_option_selection_brief"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_route_option_selection_candidate_options"
        ]
        >= 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_route_option_selection_candidate_primitives"
        ]
        >= 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_route_option_selection_candidates_with_residual_goals"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_route_option_selection_candidate_residual_goals"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_route_option_selection_lower_bound_options"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_route_option_selection_lower_bound_residual_goals"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_rows_with_provider_usage"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "total_provider_input_tokens"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "total_provider_output_tokens"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "total_provider_total_tokens"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"]["provider_usage_summary"][
            "row_count"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_prompt_token_budget_rows"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_input_tokens"
        ]
        > 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_max_output_tokens"
        ]
        == 9000
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_total_token_budget"
        ]
        == manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_input_tokens"
        ]
        + 9000
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_input_cost_micro_usd"
        ]
        == manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_input_tokens"
        ]
        * 3
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_max_output_cost_micro_usd"
        ]
        == 9000 * 15
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_base_input_output_cost_micro_usd"
        ]
        == manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_input_cost_micro_usd"
        ]
        + manifest["feedback_llm_route_planner_summary"][
            "estimated_prompt_max_output_cost_micro_usd"
        ]
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_prompt_token_budget_rows_with_estimated_base_cost"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_model_tier_decision_ledger_rows"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_model_tier_decision_ledger_rows_with_escalation"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_model_tier_decision_ledger_provider_failure_rows"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_model_tier_decision_resource_feedback_readiness_rows"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_model_tier_decision_resource_feedback_reuse_ready_rows"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_model_tier_decision_resource_feedback_sonnet_triggers"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_model_tier_decision_formal_attempt_feedback_contexts"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_model_tier_decision_formal_attempt_feedback_residual_goals"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers"
        ]
        == 0
    )
    report = (
        out_dir / "formalization_gap_planner_publication_bundle.md"
    ).read_text(encoding="utf-8")
    assert (
        "LLM route planner model-tier ledger rows/escalations/provider-failures: 1/0/0"
        in report
    )
    assert (
        "Feedback LLM route planner model-tier ledger rows/escalations/provider-failures: 1/0/0"
        in report
    )
    combined_usage = manifest["combined_llm_provider_usage_summary"]
    assert combined_usage["requested"] is True
    assert combined_usage["primary_requested"] is True
    assert combined_usage["feedback_requested"] is True
    assert combined_usage["n_route_planner_passes_requested"] == 2
    assert combined_usage["row_count"] == 0
    assert combined_usage["total_tokens"] == 0
    assert combined_usage["by_model_tier"] == {}
    assert (
        "LLM formal-attempt queues primary/feedback: primary_items=0 "
        "primary_rows=0 feedback_items=0 feedback_rows=0"
        in report
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_library_alignment_route_option_primitives"
        ]
        >= 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "total_request_library_alignment_route_option_minimum_base_cost"
        ]
        >= 0
    )
    assert manifest["feedback_llm_route_planner_summary"][
        "by_request_library_alignment_delta_class"
    ]
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_context_packet_inventory"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_context_inventory_total_rows"
        ]
        >= 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_rows_with_context_packet_inventory"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_route_adoption_precondition_known_blockers"
        ]
        >= 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_route_adoption_precondition_required_response_fields"
        ]
        >= 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_route_adoption_precondition_target_primitives"
        ]
        >= 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_quality_control_obligation_inventory"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_pending_quality_control_values"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_feedback_loop_summary_prior_llm_route_planner_hook_traces"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_feedback_loop_summary_prior_llm_route_planner_hook_traces"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_component_resource_registry_context"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_component_resource_registry_resources_in_prompt"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_source_theorem_formal_environment_bridge_context"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_requests_with_exact_source_theorem_proof_body_executor_context"
        ]
        == 0
    )
    assert manifest["feedback_llm_route_planner_summary"]["n_rows"] == 1
    assert manifest["feedback_llm_route_planner_summary"][
        "n_informal_knowledge_dag_nodes"
    ] == 0
    assert manifest["feedback_llm_route_planner_summary"][
        "n_formal_realization_dag_nodes"
    ] == 0
    assert manifest["feedback_llm_route_planner_summary"][
        "legacy_response_field_aliases"
    ] == {"lean_realization_dag_nodes": "formal_realization_dag_nodes"}
    assert manifest["feedback_llm_route_planner_summary"][
        "n_lean_realization_dag_nodes"
    ] == 0
    assert (
        manifest["feedback_llm_route_planner_summary"]["n_route_alignment_edges"]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_formal_attempt_queue_items"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_rows_with_formal_attempt_queue"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_agentic_proof_execution_materializer_rows"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_agentic_proof_execution_artifact_verifier_rows"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_agentic_proof_source_theorem_promotion_rows"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_proof_execution_feedback_rows"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_request_proof_execution_unsupported_target_prover_rows"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_route_adoption_awaiting_llm_response"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"]["standalone_replay_gate_ok"]
        is False
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_standalone_replay_route_candidates"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_standalone_replay_adoptable_route_candidates"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_standalone_replay_blocked_route_candidates"
        ]
        == 1
    )
    assert manifest["feedback_llm_route_planner_summary"][
        "standalone_replay_gate_blockers"
    ] == ["llm_route_planner_response_missing"]
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_standalone_seed_routes_llm_fallback_routes"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_standalone_seed_routes_llm_fallback_routes_marked_adoptable"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_standalone_seed_routes_llm_fallback_selected_not_adoptable"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_standalone_seed_routes_with_llm_seed_route_source"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "standalone_seed_route_by_llm_seed_route_source"
        ]
        == {"fallback_input_route": 1}
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_standalone_seed_routes_with_llm_fallback_boundary"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_rows_with_route_adoption_preconditions"
        ]
        == 1
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_row_route_adoption_precondition_known_blockers"
        ]
        >= 0
    )
    assert (
        manifest["feedback_llm_route_planner_summary"][
            "n_generated_responses_haiku_to_sonnet_escalated"
        ]
        == 0
    )
    assert optional_by_name[
        "formalization_gap_planner_llm_route_planner_response_payload_validation"
    ]["requested"]
    assert optional_by_name[
        "formalization_gap_planner_llm_route_planner_response_payload_validation"
    ]["ok"]
    validation_summary = manifest[
        "llm_route_planner_response_payload_validation_summary"
    ]
    assert validation_summary["requested"] is True
    assert validation_summary["n_payloads"] == 1
    assert validation_summary["n_valid_payloads"] == 1
    assert validation_summary["n_invalid_payloads"] == 0
    assert (
        validation_summary[
            "n_request_bound_payloads_with_route_adoption_status"
        ]
        == 0
    )
    assert validation_summary["n_request_bound_payloads_route_adoption_ready"] == 0
    assert (
        validation_summary[
            "n_request_bound_payloads_route_adoption_pending_refinement"
        ]
        == 0
    )
    assert validation_summary["n_request_bound_payloads_route_adoption_rejected"] == 0
    assert (
        validation_summary[
            "n_request_bound_payloads_adoptable_for_standalone_replay"
        ]
        == 0
    )
    assert validation_summary["by_request_bound_payload_route_adoption_status"] == {}
    assert (
        validation_summary["request_bound_payload_route_adoption_blocker_counts"]
        == {}
    )
    assert (
        validation_summary[
            "n_request_bound_payloads_with_route_adoption_preconditions"
        ]
        == 0
    )
    assert (
        validation_summary[
            "n_request_bound_payloads_with_blocking_route_adoption_preconditions"
        ]
        == 0
    )
    assert (
        validation_summary[
            "n_request_bound_payload_route_adoption_precondition_known_blockers"
        ]
        == 0
    )
    assert (
        validation_summary[
            "n_request_bound_payload_route_adoption_precondition_required_response_fields"
        ]
        == 0
    )
    assert (
        validation_summary[
            "n_request_bound_payload_route_adoption_precondition_target_primitives"
        ]
        == 0
    )
    assert (
        validation_summary[
            "n_request_bound_payloads_with_agentic_proof_strategy_plan"
        ]
        == 0
    )
    assert (
        validation_summary[
            "n_request_bound_payload_agentic_proof_strategy_plan_rows"
        ]
        == 0
    )
    assert (
        validation_summary[
            "n_request_bound_payload_agentic_proof_strategy_plan_ready"
        ]
        == 0
    )
    assert validation_summary["n_payloads_with_formal_attempt_queue"] == 1
    assert validation_summary["n_payload_formal_attempt_queue_items"] == 1
    assert validation_summary["n_payloads_with_formal_attempt_queue_errors"] == 0
    assert validation_summary["n_formal_attempt_queue_errors"] == 0
    assert (
        validation_summary[
            "n_payloads_with_agentic_proof_strategy_plan_obligation_errors"
        ]
        == 0
    )
    assert (
        validation_summary["n_agentic_proof_strategy_plan_obligation_errors"] == 0
    )
    assert validation_summary["n_payloads_with_declared_target_prover_family"] == 1
    assert (
        validation_summary[
            "n_request_bound_payloads_with_target_prover_family_mismatch"
        ]
        == 0
    )
    assert validation_summary["by_payload_target_prover_family"] == {"lean4": 1}
    assert validation_summary["by_request_context_target_prover_family"] == {}
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_requests.jsonl"
    ).exists()
    primary_alignment_jsonl = (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_library_alignment_summaries.jsonl"
    )
    primary_alignment_schema = (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json"
    )
    assert primary_alignment_jsonl.exists()
    assert primary_alignment_schema.exists()
    assert json.loads(primary_alignment_schema.read_text(encoding="utf-8"))[
        "$id"
    ] == LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID
    primary_alignment_rows = [
        json.loads(line)
        for line in primary_alignment_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(primary_alignment_rows) == manifest["llm_route_planner_summary"][
        "n_requests_with_library_alignment_summary"
    ]
    primary_target_context_jsonl = (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_target_theorem_context_packets.jsonl"
    )
    primary_target_context_schema = (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_target_theorem_context_packet.schema.json"
    )
    assert primary_target_context_jsonl.exists()
    assert primary_target_context_schema.exists()
    assert json.loads(primary_target_context_schema.read_text(encoding="utf-8"))[
        "$id"
    ] == LLM_ROUTE_PLANNER_TARGET_THEOREM_CONTEXT_PACKET_SCHEMA_ID
    primary_target_context_rows = [
        json.loads(line)
        for line in primary_target_context_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(primary_target_context_rows) == manifest["llm_route_planner_summary"][
        "n_request_packets"
    ]
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_feedback_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_library_alignment_summaries.jsonl"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_feedback_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner_response_payload_validation"
        / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.json"
    ).exists()


def test_publication_bundle_summarizes_llm_resource_feedback_readiness() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_resource_feedback"
    )
    shutil.rmtree(root, ignore_errors=True)
    resource_response_ledger_dir = _write_resource_feedback_response_ledger(
        root / "resource_feedback"
    )
    primary_dir = _write_prompt_only_llm_route_planner_artifact(
        root / "primary",
        resource_response_ledger_dir=resource_response_ledger_dir,
    )
    manifest_path = (
        primary_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
    )
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_payload.update(
        {
            "n_requests_with_feedback_loop_summary": 1,
            "n_feedback_loop_summary_residual_goals": 2,
            "n_feedback_loop_summary_replan_required": 1,
            "n_feedback_loop_summary_needs_more_literature": 1,
            "n_feedback_loop_summary_needs_more_library_grounding": 1,
            "n_feedback_loop_summary_needs_more_proof_state_feedback": 1,
            "n_feedback_loop_summary_need_actions": 3,
            "n_feedback_loop_summary_need_actions_literature": 1,
            "n_feedback_loop_summary_need_actions_library_grounding": 1,
            "n_feedback_loop_summary_need_actions_proof_state_feedback": 1,
        }
    )
    manifest_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
    out_dir = root / "bundle"

    payload = export_formalization_gap_planner_publication_bundle(
        out_dir,
        formalization_gap_planner_llm_route_planner_dir=primary_dir,
    )

    assert payload["all_ok"]
    raw_manifest = json.loads(
        (
            primary_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (
            out_dir / "formalization_gap_planner_publication_bundle_manifest.json"
        ).read_text(encoding="utf-8")
    )
    summary = manifest["llm_route_planner_summary"]
    assert raw_manifest["n_requests_with_resource_feedback_readiness_summary"] == 1
    assert raw_manifest["n_request_resource_feedback_readiness_rows"] == 1
    assert raw_manifest["n_request_resource_feedback_reuse_ready_rows"] == 0
    assert (
        raw_manifest[
            "n_request_model_tier_decision_resource_feedback_readiness_rows"
        ]
        == 1
    )
    assert (
        raw_manifest[
            "n_request_model_tier_decision_resource_feedback_reuse_ready_rows"
        ]
        == 0
    )
    assert (
        raw_manifest[
            "n_request_model_tier_decision_resource_feedback_sonnet_triggers"
        ]
        == 1
    )
    assert summary["n_requests_with_resource_feedback_readiness_summary"] == 1
    assert summary["n_request_resource_feedback_readiness_rows"] == 1
    assert summary["n_request_resource_feedback_reuse_ready_rows"] == 0
    assert summary["n_requests_with_feedback_loop_summary"] == 1
    assert summary["n_feedback_loop_summary_residual_goals"] == 2
    assert summary["n_feedback_loop_summary_replan_required"] == 1
    assert summary["n_feedback_loop_summary_needs_more_literature"] == 1
    assert summary["n_feedback_loop_summary_needs_more_library_grounding"] == 1
    assert summary["n_feedback_loop_summary_needs_more_proof_state_feedback"] == 1
    assert summary["n_feedback_loop_summary_need_actions"] == 3
    assert summary["n_feedback_loop_summary_need_actions_literature"] == 1
    assert summary["n_feedback_loop_summary_need_actions_library_grounding"] == 1
    assert summary["n_feedback_loop_summary_need_actions_proof_state_feedback"] == 1
    assert (
        summary[
            "n_request_model_tier_decision_resource_feedback_readiness_rows"
        ]
        == 1
    )
    assert (
        summary[
            "n_request_model_tier_decision_resource_feedback_reuse_ready_rows"
        ]
        == 0
    )
    assert (
        summary[
            "n_request_model_tier_decision_resource_feedback_sonnet_triggers"
        ]
        == 1
    )


def test_publication_bundle_summarizes_llm_formal_source_retrieval() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_formal_source_retrieval"
    )
    shutil.rmtree(root, ignore_errors=True)
    refinement_evidence_dir = _write_formal_source_retrieval_refinement_evidence(
        root / "refinement_evidence"
    )
    primary_dir = _write_prompt_only_llm_route_planner_artifact(
        root / "primary",
        refinement_evidence_dir=refinement_evidence_dir,
    )
    out_dir = root / "bundle"

    payload = export_formalization_gap_planner_publication_bundle(
        out_dir,
        formalization_gap_planner_llm_route_planner_dir=primary_dir,
    )

    assert payload["all_ok"]
    raw_manifest = json.loads(
        (
            primary_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (
            out_dir / "formalization_gap_planner_publication_bundle_manifest.json"
        ).read_text(encoding="utf-8")
    )
    summary = manifest["llm_route_planner_summary"]
    assert raw_manifest["n_requests_with_formal_source_retrieval_summary"] == 1
    assert raw_manifest["n_request_formal_source_retrieval_metadata_rows"] == 1
    assert raw_manifest["n_request_formal_source_semantic_rerank_rows"] == 1
    assert (
        raw_manifest[
            "n_request_route_option_selection_candidate_formal_source_retrieval_metadata_rows"
        ]
        == 1
    )
    assert (
        raw_manifest[
            "n_request_route_option_selection_lower_bound_formal_source_target_compatible_hits"
        ]
        == 1
    )
    assert summary["n_requests_with_formal_source_retrieval_summary"] == 1
    assert summary["n_request_formal_source_retrieval_metadata_rows"] == 1
    assert summary["n_request_formal_source_semantic_rerank_rows"] == 1
    assert (
        summary[
            "n_request_route_option_selection_candidate_formal_source_retrieval_metadata_rows"
        ]
        == 1
    )
    assert (
        summary[
            "n_request_route_option_selection_lower_bound_formal_source_target_compatible_hits"
        ]
        == 1
    )
    request_packet = raw_manifest["request_packets"][0]
    retrieval_summary = request_packet["context_packet"][
        "formal_source_retrieval_summary"
    ]
    assert retrieval_summary["total_count"] == 1
    assert retrieval_summary["semantic_rerank_count"] == 1


def test_publication_bundle_summarizes_llm_formal_attempt_feedback() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_formal_attempt_feedback"
    )
    shutil.rmtree(root, ignore_errors=True)
    handoff_dir = _write_formal_attempt_feedback_handoff(
        root / "formal_attempt_feedback"
    )
    primary_dir = _write_prompt_only_llm_route_planner_artifact(
        root / "primary",
        route_replan_handoff_dir=handoff_dir,
    )
    out_dir = root / "bundle"

    payload = export_formalization_gap_planner_publication_bundle(
        out_dir,
        formalization_gap_planner_llm_route_planner_dir=primary_dir,
    )

    assert payload["all_ok"]
    raw_manifest = json.loads(
        (
            primary_dir / "formalization_gap_planner_llm_route_planner_manifest.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (
            out_dir / "formalization_gap_planner_publication_bundle_manifest.json"
        ).read_text(encoding="utf-8")
    )
    summary = manifest["llm_route_planner_summary"]
    assert raw_manifest["n_requests_with_formal_attempt_feedback_summary"] == 1
    assert raw_manifest["n_request_formal_attempt_feedback_contexts"] == 1
    assert raw_manifest["n_request_formal_attempt_feedback_residual_goals"] == 1
    assert raw_manifest["n_request_formal_attempt_feedback_failed_statuses"] == 1
    assert (
        raw_manifest[
            "n_request_model_tier_decision_formal_attempt_feedback_contexts"
        ]
        == 1
    )
    assert (
        raw_manifest[
            "n_request_model_tier_decision_formal_attempt_feedback_residual_goals"
        ]
        == 1
    )
    assert (
        raw_manifest[
            "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses"
        ]
        == 1
    )
    assert (
        raw_manifest[
            "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers"
        ]
        == 1
    )
    assert summary["n_requests_with_formal_attempt_feedback_summary"] == 1
    assert summary["n_request_formal_attempt_feedback_contexts"] == 1
    assert summary["n_request_formal_attempt_feedback_residual_goals"] == 1
    assert summary["n_request_formal_attempt_feedback_failed_statuses"] == 1
    assert (
        summary[
            "n_request_model_tier_decision_formal_attempt_feedback_contexts"
        ]
        == 1
    )
    assert (
        summary[
            "n_request_model_tier_decision_formal_attempt_feedback_residual_goals"
        ]
        == 1
    )
    assert (
        summary[
            "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses"
        ]
        == 1
    )
    assert (
        summary[
            "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers"
        ]
        == 1
    )


def test_publication_bundle_lifts_route_brief_resource_request_counts() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_resource_request_brief_counts"
    )
    shutil.rmtree(root, ignore_errors=True)
    resource_request_dir = root / "resource_request_queue"
    resource_request_dir.mkdir(parents=True)
    (resource_request_dir / "formalization_gap_planner_resource_request_queue.jsonl").write_text(
        "",
        encoding="utf-8",
    )
    (
        resource_request_dir
        / "formalization_gap_planner_resource_request_queue_row.schema.json"
    ).write_text(
        json.dumps(resource_request_queue_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (resource_request_dir / "formalization_gap_planner_resource_request_queue.md").write_text(
        "# fixture\n",
        encoding="utf-8",
    )
    (
        resource_request_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_request_queue",
                "n_resource_request_rows": 11,
                "n_ok": 11,
                "n_failed": 0,
                "n_local_first_requests": 5,
                "n_frontier_escalation_requests": 6,
                "n_distinct_resources": 7,
                "n_llm_route_planner_rows": 1,
                "n_llm_route_planner_request_packets": 1,
                "n_llm_route_planner_request_route_planning_briefs": 1,
                "n_llm_route_planner_route_planning_brief_evidence_gaps": 2,
                "n_llm_route_planner_resource_request_rows": 4,
                "n_llm_route_planner_route_planning_brief_resource_request_rows": 7,
                "n_llm_route_planner_total_resource_request_rows": 11,
                "n_llm_route_planner_resource_request_rows_with_explicit_resource_binding": 6,
                "n_llm_route_planner_resource_request_rows_matching_explicit_resource_binding": 2,
                "n_llm_route_planner_resource_request_rows_from_hook_default_fanout": 5,
                "n_llm_route_planner_route_planning_brief_evidence_gap_rows": 7,
                "n_llm_route_planner_resource_request_rows_with_query_intents": 11,
                "n_llm_route_planner_resource_request_query_intents": 88,
                "n_llm_route_planning_brief_evidence_gap_query_intents": 56,
                "n_llm_route_planner_rows_with_route_adoption_preconditions": 1,
                "n_llm_route_planner_route_adoption_precondition_known_blockers": 2,
                "n_llm_route_planner_route_adoption_precondition_required_response_fields": 3,
                "n_llm_route_planner_route_adoption_precondition_target_primitives": 1,
                "n_llm_route_planner_resource_request_rows_with_route_adoption_preconditions": 4,
                "n_llm_route_planner_resource_request_route_adoption_precondition_target_primitives": 4,
                "n_row_schema_valid": 11,
                "n_row_schema_invalid": 0,
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_publication_bundle(
        root / "bundle",
        formalization_gap_planner_resource_request_queue_dir=resource_request_dir,
    )

    assert payload["all_ok"]
    summary = payload["resource_request_queue_summary"]
    assert summary["requested"] is True
    assert summary["n_llm_route_planner_request_packets"] == 1
    assert summary["n_llm_route_planner_request_route_planning_briefs"] == 1
    assert summary["n_llm_route_planner_route_planning_brief_evidence_gaps"] == 2
    assert summary["n_llm_route_planner_resource_request_rows"] == 4
    assert (
        summary["n_llm_route_planner_route_planning_brief_resource_request_rows"]
        == 7
    )
    assert summary["n_llm_route_planner_total_resource_request_rows"] == 11
    assert (
        summary[
            "n_llm_route_planner_resource_request_rows_with_explicit_resource_binding"
        ]
        == 6
    )
    assert (
        summary[
            "n_llm_route_planner_resource_request_rows_matching_explicit_resource_binding"
        ]
        == 2
    )
    assert (
        summary["n_llm_route_planner_resource_request_rows_from_hook_default_fanout"]
        == 5
    )
    assert summary["n_llm_route_planner_route_planning_brief_evidence_gap_rows"] == 7
    assert (
        summary["n_llm_route_planner_resource_request_rows_with_query_intents"]
        == 11
    )
    assert summary["n_llm_route_planner_resource_request_query_intents"] == 88
    assert summary["n_llm_route_planning_brief_evidence_gap_query_intents"] == 56


def test_publication_bundle_lifts_route_brief_resource_response_counts() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_resource_response_brief_counts"
    )
    shutil.rmtree(root, ignore_errors=True)
    resource_request_dir = root / "resource_request_queue"
    resource_response_dir = root / "resource_response_ledger"
    resource_request_dir.mkdir(parents=True)
    resource_response_dir.mkdir(parents=True)
    (resource_request_dir / "formalization_gap_planner_resource_request_queue.jsonl").write_text(
        "",
        encoding="utf-8",
    )
    (
        resource_request_dir
        / "formalization_gap_planner_resource_request_queue_row.schema.json"
    ).write_text(
        json.dumps(resource_request_queue_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (resource_request_dir / "formalization_gap_planner_resource_request_queue.md").write_text(
        "# fixture\n",
        encoding="utf-8",
    )
    (
        resource_request_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_request_queue",
                "n_resource_request_rows": 11,
                "n_ok": 11,
                "n_failed": 0,
                "n_local_first_requests": 5,
                "n_frontier_escalation_requests": 6,
                "n_distinct_resources": 7,
                "n_llm_route_planner_rows": 1,
                "n_llm_route_planner_request_packets": 1,
                "n_llm_route_planner_request_route_planning_briefs": 1,
                "n_llm_route_planner_route_planning_brief_evidence_gaps": 2,
                "n_llm_route_planner_resource_request_rows": 4,
                "n_llm_route_planner_route_planning_brief_resource_request_rows": 7,
                "n_llm_route_planner_total_resource_request_rows": 11,
                "n_llm_route_planner_resource_request_rows_with_explicit_resource_binding": 6,
                "n_llm_route_planner_resource_request_rows_matching_explicit_resource_binding": 2,
                "n_llm_route_planner_resource_request_rows_from_hook_default_fanout": 5,
                "n_llm_route_planner_route_planning_brief_evidence_gap_rows": 7,
                "n_llm_route_planner_resource_request_rows_with_query_intents": 11,
                "n_llm_route_planner_resource_request_query_intents": 88,
                "n_llm_route_planning_brief_evidence_gap_query_intents": 56,
                "n_llm_route_planner_rows_with_route_adoption_preconditions": 1,
                "n_llm_route_planner_route_adoption_precondition_known_blockers": 2,
                "n_llm_route_planner_route_adoption_precondition_required_response_fields": 3,
                "n_llm_route_planner_route_adoption_precondition_target_primitives": 1,
                "n_llm_route_planner_resource_request_rows_with_route_adoption_preconditions": 4,
                "n_llm_route_planner_resource_request_route_adoption_precondition_target_primitives": 4,
                "n_row_schema_valid": 11,
                "n_row_schema_invalid": 0,
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (resource_response_dir / "formalization_gap_planner_resource_response_ledger.jsonl").write_text(
        "",
        encoding="utf-8",
    )
    (
        resource_response_dir
        / "formalization_gap_planner_resource_response.schema.json"
    ).write_text(
        json.dumps(resource_response_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        resource_response_dir
        / "formalization_gap_planner_resource_response_ledger_row.schema.json"
    ).write_text(
        json.dumps(resource_response_ledger_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (resource_response_dir / "formalization_gap_planner_resource_response_ledger.md").write_text(
        "# fixture\n",
        encoding="utf-8",
    )
    (
        resource_response_dir
        / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_response_ledger",
                "n_ledger_rows": 7,
                "n_ok": 7,
                "n_response_present": 1,
                "n_awaiting_response": 6,
                "n_response_contract_ok": 1,
                "n_response_playbook_grounded": 1,
                "n_llm_route_planner_traced_requests": 7,
                "n_llm_route_planner_traced_responses": 1,
                "n_llm_route_planner_traced_route_planning_brief_evidence_gap_rows": 7,
                "n_llm_route_planner_traced_route_planning_brief_evidence_gap_responses": 1,
                "n_llm_route_planner_traced_route_planning_brief_evidence_gap_grounded_responses": 1,
                "n_llm_route_planner_residual_context_rows": 1,
                "n_rows_with_formal_declaration_hits": 1,
                "n_formal_declaration_hits": 2,
                "n_rows_with_legacy_lean_declaration_hits": 0,
                "n_rows_with_residual_goals": 1,
                "n_residual_goals": 1,
                "n_route_revision_recommended": 0,
                "n_rejected": 0,
                "n_ledger_row_schema_valid": 7,
                "n_ledger_row_schema_invalid": 0,
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_publication_bundle(
        root / "bundle",
        formalization_gap_planner_resource_request_queue_dir=resource_request_dir,
        formalization_gap_planner_resource_response_ledger_dir=(
            resource_response_dir
        ),
    )

    assert payload["all_ok"]
    summary = payload["resource_response_ledger_summary"]
    assert summary["requested"] is True
    assert summary["n_llm_route_planner_traced_requests"] == 7
    assert summary["n_llm_route_planner_traced_responses"] == 1
    assert (
        summary[
            "n_llm_route_planner_traced_route_planning_brief_evidence_gap_rows"
        ]
        == 7
    )
    assert (
        summary[
            "n_llm_route_planner_traced_route_planning_brief_evidence_gap_responses"
        ]
        == 1
    )
    assert (
        summary[
            "n_llm_route_planner_traced_route_planning_brief_evidence_gap_grounded_responses"
        ]
        == 1
    )
    loop_summary = payload["interactive_feedback_loop_summary"]
    assert loop_summary["requested"] is True
    assert loop_summary["resource_request_queue_requested"] is True
    assert loop_summary["resource_response_ledger_requested"] is True
    assert loop_summary["n_route_planning_brief_evidence_gap_rows"] == 7
    assert loop_summary["n_route_planning_brief_resource_request_rows"] == 7
    assert loop_summary["n_route_planning_brief_evidence_gap_responses"] == 1
    assert (
        loop_summary["n_route_planning_brief_evidence_gap_grounded_responses"]
        == 1
    )
    assert loop_summary["n_response_contract_ok"] == 1
    assert loop_summary["n_response_playbook_grounded"] == 1
    assert loop_summary["n_formal_declaration_feedback_rows"] == 1
    assert loop_summary["n_formal_declaration_feedback_hits"] == 2
    assert loop_summary["n_residual_goal_feedback_rows"] == 1
    assert loop_summary["n_residual_goal_feedback_goals"] == 1
    assert loop_summary["n_residual_goal_context_rows"] == 1
    assert loop_summary["route_brief_feedback_ready"] is True
    assert loop_summary["formal_library_feedback_present"] is True
    assert loop_summary["prover_residual_feedback_present"] is True
    assert loop_summary["interactive_feedback_loop_ready"] is True
    readme = Path(str(payload["readme_path"])).read_text(encoding="utf-8")
    assert "Interactive feedback loop ready: True" in readme


def test_publication_bundle_combines_primary_feedback_provider_usage() -> None:
    root = Path("runs/test_publication_bundle_combines_provider_usage")
    shutil.rmtree(root, ignore_errors=True)
    primary_dir = _write_prompt_only_llm_route_planner_artifact(root / "primary")
    feedback_dir = _write_prompt_only_llm_route_planner_artifact(root / "feedback")
    _patch_llm_route_planner_provider_usage_manifest(
        primary_dir,
        model="claude-haiku-4-5-20251001",
        model_tier="haiku",
        input_tokens=100,
        output_tokens=25,
        cache_creation_input_tokens=5,
        cache_read_input_tokens=7,
        ledger_rows=1,
    )
    _patch_llm_route_planner_provider_usage_manifest(
        feedback_dir,
        model="claude-sonnet-4-6",
        model_tier="sonnet",
        input_tokens=200,
        output_tokens=50,
        ledger_rows=2,
        ledger_escalations=1,
        provider_failure_rows=1,
        generated_escalations=1,
        haiku_to_sonnet_escalations=1,
    )

    payload = export_formalization_gap_planner_publication_bundle(
        root / "bundle",
        formalization_gap_planner_llm_route_planner_dir=primary_dir,
        formalization_gap_planner_feedback_llm_route_planner_dir=feedback_dir,
    )

    assert payload["all_ok"]
    combined_usage = payload["combined_llm_provider_usage_summary"]
    assert combined_usage["requested"] is True
    assert combined_usage["primary_requested"] is True
    assert combined_usage["feedback_requested"] is True
    assert combined_usage["n_route_planner_passes_requested"] == 2
    assert combined_usage["primary_row_count"] == 1
    assert combined_usage["feedback_row_count"] == 1
    assert combined_usage["row_count"] == 2
    assert combined_usage["n_rows"] == 2
    assert combined_usage["input_tokens"] == 300
    assert combined_usage["output_tokens"] == 75
    assert combined_usage["cache_creation_input_tokens"] == 5
    assert combined_usage["cache_read_input_tokens"] == 7
    assert combined_usage["total_tokens"] == 387
    assert combined_usage["estimated_input_cost_micro_usd"] == 700
    assert combined_usage["estimated_output_cost_micro_usd"] == 875
    assert combined_usage["estimated_base_input_output_cost_micro_usd"] == 1575
    assert combined_usage["estimated_cache_tokens_excluded_from_base_cost"] == 12
    assert combined_usage["n_rows_with_estimated_base_cost"] == 2
    assert combined_usage["by_provider"]["anthropic"]["n_rows"] == 2
    assert combined_usage["by_provider"]["anthropic"]["total_tokens"] == 387
    assert (
        combined_usage["by_provider"]["anthropic"][
            "estimated_base_input_output_cost_micro_usd"
        ]
        == 1575
    )
    assert combined_usage["by_model_tier"]["haiku"]["total_tokens"] == 137
    assert (
        combined_usage["by_model_tier"]["haiku"][
            "estimated_base_input_output_cost_micro_usd"
        ]
        == 225
    )
    assert combined_usage["by_model_tier"]["sonnet"]["total_tokens"] == 250
    assert (
        combined_usage["by_model_tier"]["sonnet"][
            "estimated_base_input_output_cost_micro_usd"
        ]
        == 1350
    )
    assert (
        combined_usage["by_model"]["claude-haiku-4-5-20251001"]["input_tokens"]
        == 100
    )
    assert combined_usage["by_model"]["claude-sonnet-4-6"]["input_tokens"] == 200
    assert (
        payload["llm_route_planner_summary"][
            "total_provider_estimated_base_input_output_cost_micro_usd"
        ]
        == 225
    )
    assert (
        payload["feedback_llm_route_planner_summary"][
            "total_provider_estimated_base_input_output_cost_micro_usd"
        ]
        == 1350
    )
    assert combined_usage["n_model_tier_decision_ledger_rows"] == 3
    assert combined_usage["n_model_tier_decision_ledger_rows_with_escalation"] == 1
    assert combined_usage["n_model_tier_decision_ledger_provider_failure_rows"] == 1
    assert combined_usage["n_provider_failures"] == 1
    assert combined_usage["n_generated_responses_model_tier_escalated"] == 1
    assert combined_usage["n_generated_responses_haiku_to_sonnet_escalated"] == 1
    assert (
        "not mathematical or theorem proof evidence"
        in combined_usage["usage_boundary"]
    )
    readme = Path(str(payload["readme_path"])).read_text(encoding="utf-8")
    assert "Combined LLM route planner provider usage" in readme


def test_formalization_gap_planner_publication_bundle_exports_reusable_artifacts() -> None:
    root = Path("runs/test_formalization_gap_planner_publication_bundle")
    out_dir = root / "bundle"
    paper_dir = root / "papers"
    lean_rag_db = root / "stat_inference.sqlite"
    target_intake_dir = root / "target_intake"
    plan_dir = root / "plan"
    evaluation_dir = root / "evaluation"
    ablation_study_dir = root / "ablation_study"
    plan_audit_dir = root / "plan_audit"
    library_coverage_map_dir = root / "library_coverage_map"
    primitive_action_queue_dir = root / "primitive_action_queue"
    minimal_delta_audit_dir = root / "minimal_delta_audit"
    source_grounding_audit_dir = root / "source_grounding_audit"
    refinement_queue_dir = root / "refinement_queue"
    refinement_adapter_dir = root / "refinement_adapter"
    local_literature_adapter_dir = root / "local_literature_adapter"
    local_formal_source_adapter_dir = root / "local_formal_source_adapter"
    local_proof_state_adapter_dir = root / "local_proof_state_adapter"
    refinement_evidence_dir = root / "refinement_evidence"
    route_revision_overlay_dir = root / "route_revision_overlay"
    stability_audit_dir = root / "stability_audit"
    replan_handoff_dir = root / "replan_handoff"
    replan_handoff_audit_dir = root / "replan_handoff_audit"
    runtime_handoff_audit_dir = root / "runtime_handoff_audit"
    proof_state_triage_dir = root / "proof_state_triage"
    interactive_session_dir = root / "interactive_session"
    prover_contract_dir = root / "prover_contract"
    cross_prover_matrix_dir = root / "cross_prover_matrix"
    adapter_registry_audit_dir = root / "adapter_registry_audit"
    component_resource_registry_audit_dir = root / "component_resource_registry_audit"
    shutil.rmtree(root, ignore_errors=True)
    paper_dir.mkdir(parents=True, exist_ok=True)
    target_intake_dir.mkdir(parents=True, exist_ok=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    ablation_study_dir.mkdir(parents=True, exist_ok=True)
    plan_audit_dir.mkdir(parents=True, exist_ok=True)
    library_coverage_map_dir.mkdir(parents=True, exist_ok=True)
    primitive_action_queue_dir.mkdir(parents=True, exist_ok=True)
    minimal_delta_audit_dir.mkdir(parents=True, exist_ok=True)
    source_grounding_audit_dir.mkdir(parents=True, exist_ok=True)
    refinement_queue_dir.mkdir(parents=True, exist_ok=True)
    refinement_adapter_dir.mkdir(parents=True, exist_ok=True)
    local_literature_adapter_dir.mkdir(parents=True, exist_ok=True)
    local_formal_source_adapter_dir.mkdir(parents=True, exist_ok=True)
    local_proof_state_adapter_dir.mkdir(parents=True, exist_ok=True)
    refinement_evidence_dir.mkdir(parents=True, exist_ok=True)
    route_revision_overlay_dir.mkdir(parents=True, exist_ok=True)
    stability_audit_dir.mkdir(parents=True, exist_ok=True)
    replan_handoff_dir.mkdir(parents=True, exist_ok=True)
    replan_handoff_audit_dir.mkdir(parents=True, exist_ok=True)
    runtime_handoff_audit_dir.mkdir(parents=True, exist_ok=True)
    proof_state_triage_dir.mkdir(parents=True, exist_ok=True)
    interactive_session_dir.mkdir(parents=True, exist_ok=True)
    prover_contract_dir.mkdir(parents=True, exist_ok=True)
    cross_prover_matrix_dir.mkdir(parents=True, exist_ok=True)
    adapter_registry_audit_dir.mkdir(parents=True, exist_ok=True)
    component_resource_registry_audit_dir.mkdir(parents=True, exist_ok=True)
    lean_rag_db.parent.mkdir(parents=True, exist_ok=True)
    lean_rag_db.write_text("", encoding="utf-8")
    component_resource_registry_fixture = (
        export_formalization_gap_planner_component_resource_registry(
            root / "component_resource_registry_fixture"
        )
    )
    contract_id_by_resource = {
        str(row["resource_id"]): str(row["resource_contract_id"])
        for row in component_resource_registry_fixture["resource_contract_rows"]
        if isinstance(row, dict)
    }
    interactive_policy_resource_ids = [
        "cross_prover_matrix_audit",
        "local_lake_lean",
        "lean_lsp_mcp",
    ]
    interactive_policy_contract_ids = [
        contract_id_by_resource[resource_id]
        for resource_id in interactive_policy_resource_ids
    ]
    (paper_dir / "route_note.md").write_text(
        "# route note\nconditional mean residual zero route evidence\n",
        encoding="utf-8",
    )
    for filename in (
        "formalization_gap_planner_target_intake_manifest.json",
        "formalization_gap_planner_target_intake.jsonl",
        "formalization_gap_planner_target_intake_standalone_seed.json",
        "formalization_gap_planner_target_intake.md",
        "formalization_gap_planner_target_intake.schema.json",
        "formalization_gap_planner_target_intake_row.schema.json",
    ):
        (target_intake_dir / filename).write_text(
            json.dumps({"fixture": filename}) if filename.endswith(".json") else "fixture\n",
            encoding="utf-8",
        )
    for filename in (
        "goal_conditioned_minimal_formalization_plan_manifest.json",
        "goal_conditioned_minimal_formalization_plan.jsonl",
        "goal_conditioned_minimal_formalization_plan.md",
        "library_aware_formalization_gap_plan.schema.json",
        "library_aware_formalization_gap_plan_row.schema.json",
        "formalization_gap_planner_route_alignment_edge.schema.json",
    ):
        (plan_dir / filename).write_text(
            (
                json.dumps(route_alignment_edge_json_schema(), indent=2)
                if filename.endswith(".schema.json")
                and "route_alignment_edge" in filename
                else json.dumps(portable_gap_plan_row_json_schema(), indent=2)
                if filename == "library_aware_formalization_gap_plan_row.schema.json"
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_ablation_study_manifest.json",
        "formalization_gap_planner_ablation_study.jsonl",
        "formalization_gap_planner_ablation_study_row.schema.json",
        "formalization_gap_planner_ablation_study.md",
    ):
        (ablation_study_dir / filename).write_text(
            (
                json.dumps(ablation_study_row_json_schema(), indent=2)
                if filename == "formalization_gap_planner_ablation_study_row.schema.json"
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    evaluation_row = {
        "schema_version": 1,
        "evaluation_id": "evaluation:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "matched_ground_truth": True,
        "match_key": "route_id:route:fixture",
        "predicted_route_primitives": ["rank_uniformity"],
        "ground_truth_route_primitives": ["rank_uniformity"],
        "route_true_positive_primitives": ["rank_uniformity"],
        "route_missing_primitives": [],
        "route_extra_primitives": [],
        "route_recall": 1.0,
        "route_precision": 1.0,
        "predicted_delta_primitives": ["rank_uniformity"],
        "ground_truth_delta_primitives": ["rank_uniformity"],
        "delta_true_positive_primitives": ["rank_uniformity"],
        "delta_unnecessary_primitives": [],
        "delta_missing_primitives": [],
        "delta_precision": 1.0,
        "delta_recall": 1.0,
        "predicted_residual_primitives": ["rank_uniformity"],
        "ground_truth_residual_primitives": ["rank_uniformity"],
        "residual_true_positive_primitives": ["rank_uniformity"],
        "residual_missing_primitives": [],
        "residual_extra_primitives": [],
        "residual_precision": 1.0,
        "residual_recall": 1.0,
        "predicted_residual_goals": ["rank_uniformity"],
        "ground_truth_residual_goals": ["rank_uniformity"],
        "predicted_existing_reuse_primitives": [],
        "ground_truth_existing_reuse_primitives": [],
        "existing_reuse_precision": 1.0,
        "existing_reuse_recall": 1.0,
        "coverage_classification_accuracy": 1.0,
        "n_coverage_classification_checked": 1,
        "coverage_classification_confusions": [],
        "two_dag_contract_ok": True,
        "alignment_contract_ok": True,
        "alignment_coverage": 1.0,
        "aligned_primitives": ["rank_uniformity"],
        "unaligned_primitives": [],
        "feedback_loop_ready": True,
        "minimal_delta_cost_graph_present": False,
        "minimal_delta_route_option_count": 0,
        "minimal_delta_selected_route_option_id": "",
        "minimal_delta_selected_route_cost": 0.0,
        "realization_coverage_witness_present": False,
        "realization_coverage_complete": False,
        "realization_missing_selected_formal_primitives": [],
        "realization_missing_delta_alignment_primitives": [],
        "realization_cost_hint_baseline_primitives": [],
        "realization_omitted_cost_hint_primitives": [],
        "realization_cost_hint_baseline_coverage_complete": True,
        "llm_route_planner_trace_present": False,
        "llm_route_planner_row_id": "",
        "llm_route_planner_provider": "",
        "llm_route_planner_model": "",
        "llm_route_planner_model_tier": "",
        "llm_route_planner_model_tier_decision_basis": "",
        "llm_route_planner_model_tier_decision_sonnet_triggers": [],
        "llm_route_planner_model_tier_decision_sonnet_trigger_count": 0,
        "llm_route_planner_source_feedback_row_count": 0,
        "llm_route_planner_source_feedback_unverified_semantic_primitive_row_count": 0,
        "llm_route_planner_source_feedback_proof_body_execution_failure_count": 0,
        "llm_route_planner_source_feedback_formal_environment_blocker_count": 0,
        "llm_route_planner_interactive_formal_attempt_queue_row_count": 0,
        "llm_route_planner_interactive_formal_attempt_queue_item_count": 0,
        "llm_route_planner_interactive_formal_attempt_queue_ready_item_count": 0,
        "llm_route_planner_interactive_formal_attempt_queue_blocked_item_count": 0,
        "llm_route_planner_interactive_formal_attempt_queue_execution_command_count": 0,
        "llm_route_planner_residual_goal_context_count": 0,
        "llm_route_planner_residual_goal_context_residual_goals": [],
        "llm_route_planner_residual_goal_context_source_ref_count": 0,
        "llm_route_planner_residual_goal_context_provenance_count": 0,
        "llm_route_planner_residual_goals_with_context_count": 0,
        "llm_route_planner_residual_goals_without_context": ["rank_uniformity"],
        "llm_route_planner_route_option_selection_brief_present": False,
        "llm_route_planner_route_option_selection_candidate_count": 0,
        "llm_route_planner_route_option_selection_candidate_primitive_count": 0,
        "llm_route_planner_route_option_selection_candidates_with_residual_goals": 0,
        "llm_route_planner_route_option_selection_candidate_residual_goal_count": 0,
        "llm_route_planner_route_option_selection_candidate_formal_source_retrieval_metadata_rows": 0,
        "llm_route_planner_route_option_selection_candidate_formal_source_semantic_rerank_rows": 0,
        "llm_route_planner_route_option_selection_candidate_formal_source_target_compatible_hits": 0,
        "llm_route_planner_route_option_selection_lower_bound_selected_route_option_id": "",
        "llm_route_planner_route_option_selected_route_option_id": "",
        "llm_route_planner_route_option_selection_lower_bound_residual_goal_count": 0,
        "llm_route_planner_route_option_selection_lower_bound_formal_source_retrieval_metadata_rows": 0,
        "llm_route_planner_route_option_selection_lower_bound_formal_source_semantic_rerank_rows": 0,
        "llm_route_planner_route_option_selection_lower_bound_formal_source_target_compatible_hits": 0,
        "llm_route_planner_route_option_selection_minimal_delta_selected_residual_goal_count": 0,
        "llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta": False,
        "llm_route_planner_route_option_selected_matches_lower_bound": False,
        "llm_route_planner_route_option_selected_matches_minimal_delta": False,
        "llm_route_planner_route_adoption_status": "",
        "llm_route_planner_route_adoption_blockers": [],
        "llm_route_planner_route_adoption_preconditions": {},
        "llm_route_planner_route_adoption_precondition_present": False,
        "llm_route_planner_route_adoption_precondition_blocked_before_response": False,
        "llm_route_planner_route_adoption_precondition_known_blockers": [],
        "llm_route_planner_route_adoption_precondition_required_response_fields": [],
        "llm_route_planner_route_adoption_precondition_known_blocker_count": 0,
        "llm_route_planner_route_adoption_precondition_required_response_field_count": 0,
        "llm_route_planner_acceptance_status": "",
        "llm_route_planner_model_selection_rationale": "",
        "llm_route_planner_has_generator_metadata": False,
        "llm_route_planner_generator_metadata_keys": [],
        "llm_route_planner_request_contract_blocked": False,
        "llm_route_planner_errors": [],
        "llm_route_planner_generation_errors": [],
        "quality_controls_present": False,
        "quality_controls": {},
        "quality_control_fields": [],
        "quality_control_resource_contract_ids": [],
        "quality_control_response_validation_signals": [],
        "quality_control_stop_conditions": [],
        "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "proof_evidence_boundary_ok": True,
        "kernel_verified_ground_truth": False,
        "kernel_verification_witnesses": [],
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_EVALUATION_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    (evaluation_dir / "formalization_gap_planner_evaluation_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_evaluation",
                "n_evaluation_rows": 1,
                "n_evaluation_row_schema_valid": 1,
                "n_evaluation_row_schema_invalid": 0,
                "bundled_ground_truth_filename": (
                    "formalization_gap_planner_evaluation_ground_truth.json"
                ),
                "n_rows_with_llm_route_planner_residual_goal_contexts": 0,
                "n_llm_route_planner_residual_goal_contexts": 0,
                "n_llm_route_planner_residual_goal_context_source_refs": 0,
                "n_llm_route_planner_residual_goal_context_provenance_values": 0,
                "n_llm_route_planner_residual_goals_with_context": 0,
                "n_llm_route_planner_residual_goals_without_context": 1,
                "n_rows_with_llm_route_planner_route_option_selection_brief": 0,
                "n_llm_route_planner_route_option_selection_candidate_options": 0,
                "n_llm_route_planner_route_option_selection_candidate_primitives": 0,
                "n_llm_route_planner_route_option_selection_candidates_with_residual_goals": 0,
                "n_llm_route_planner_route_option_selection_candidate_residual_goals": 0,
                "n_llm_route_planner_route_option_selection_candidate_formal_source_retrieval_metadata_rows": 0,
                "n_llm_route_planner_route_option_selection_candidate_formal_source_semantic_rerank_rows": 0,
                "n_llm_route_planner_route_option_selection_candidate_formal_source_target_compatible_hits": 0,
                "n_llm_route_planner_route_option_selection_lower_bound_residual_goals": 0,
                "n_llm_route_planner_route_option_selection_lower_bound_formal_source_retrieval_metadata_rows": 0,
                "n_llm_route_planner_route_option_selection_lower_bound_formal_source_semantic_rerank_rows": 0,
                "n_llm_route_planner_route_option_selection_lower_bound_formal_source_target_compatible_hits": 0,
                "n_rows_with_llm_route_planner_route_option_selected_route_option": 0,
                "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals": 0,
                "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta": 0,
                "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta": 0,
                "n_llm_route_planner_route_option_selected_matches_lower_bound": 0,
                "n_llm_route_planner_route_option_selected_mismatches_lower_bound": 0,
                "n_llm_route_planner_route_option_selected_matches_minimal_delta": 0,
                "n_llm_route_planner_route_option_selected_mismatches_minimal_delta": 0,
                "n_rows_with_llm_route_planner_request_contract_blocked": 0,
                "n_rows_with_llm_route_planner_errors": 0,
                "n_llm_route_planner_errors": 0,
                "n_llm_route_planner_generation_errors": 0,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "rows": [evaluation_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (evaluation_dir / "formalization_gap_planner_evaluation.jsonl").write_text(
        json.dumps(evaluation_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evaluation_dir / "formalization_gap_planner_evaluation_row.schema.json").write_text(
        json.dumps(evaluation_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        evaluation_dir / "formalization_gap_planner_evaluation_ground_truth.json"
    ).write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "route_id": "route:fixture",
                        "required_primitives": ["rank_uniformity"],
                        "actual_existing_reuse_primitives": [],
                        "actual_delta_primitives": ["rank_uniformity"],
                        "expected_residual_primitives": ["rank_uniformity"],
                        "expected_residual_goals": ["rank_uniformity"],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (evaluation_dir / "formalization_gap_planner_evaluation.md").write_text(
        "# evaluation\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    portable_plan_audit_row = {
        "schema_version": 1,
        "check_id": "formalization_gap_planner_portable_plan_audit:fixture",
        "check_name": "fixture_check",
        "category": "fixture",
        "expected": "ok",
        "observed": "ok",
        "ok": True,
        "severity": "info",
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_PORTABLE_PLAN_AUDIT_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": (
            "Portable formalization gap plan audit rows validate planner "
            "contracts and are not theorem proof evidence."
        ),
        "errors": [],
    }
    (
        plan_audit_dir / "formalization_gap_planner_portable_plan_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_portable_plan_audit",
                "n_checks": 1,
                "n_ok": 1,
                "n_failed": 0,
                "n_row_schema_valid": 1,
                "n_row_schema_invalid": 0,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "checks": [portable_plan_audit_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (plan_audit_dir / "formalization_gap_planner_portable_plan_audit.jsonl").write_text(
        json.dumps(portable_plan_audit_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        plan_audit_dir
        / "formalization_gap_planner_portable_plan_audit_row.schema.json"
    ).write_text(
        json.dumps(portable_plan_audit_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (plan_audit_dir / "formalization_gap_planner_portable_plan_audit.md").write_text(
        "# portable plan audit\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    library_coverage_map_row = _fixture_library_coverage_map_row()
    (
        library_coverage_map_dir
        / "formalization_gap_planner_library_coverage_map_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_library_coverage_map",
                "target_prover_family": "lean4",
                "n_target_prover_families": 1,
                "by_target_prover_family": {"lean4": 1},
                "n_coverage_rows": 1,
                "n_ok": 1,
                "n_failed": 0,
                "n_row_schema_valid": 1,
                "n_row_schema_invalid": 0,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "rows": [library_coverage_map_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        library_coverage_map_dir / "formalization_gap_planner_library_coverage_map.jsonl"
    ).write_text(
        json.dumps(library_coverage_map_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        library_coverage_map_dir
        / "formalization_gap_planner_library_coverage_map_row.schema.json"
    ).write_text(
        json.dumps(library_coverage_map_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        library_coverage_map_dir / "formalization_gap_planner_library_coverage_map.md"
    ).write_text(
        "# library coverage map\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    primitive_action_queue_row = _fixture_primitive_action_queue_row()
    (
        primitive_action_queue_dir
        / "formalization_gap_planner_primitive_action_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_primitive_action_queue",
                "n_action_items": 1,
                "n_ok": 1,
                "n_failed": 0,
                "n_row_schema_valid": 1,
                "n_row_schema_invalid": 0,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "rows": [primitive_action_queue_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        primitive_action_queue_dir
        / "formalization_gap_planner_primitive_action_queue.jsonl"
    ).write_text(
        json.dumps(primitive_action_queue_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        primitive_action_queue_dir
        / "formalization_gap_planner_primitive_action_queue_row.schema.json"
    ).write_text(
        json.dumps(primitive_action_queue_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        primitive_action_queue_dir
        / "formalization_gap_planner_primitive_action_queue.md"
    ).write_text(
        "# primitive action queue\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    for filename in (
        "formalization_gap_planner_minimal_delta_audit_manifest.json",
        "formalization_gap_planner_minimal_delta_audit.jsonl",
        "formalization_gap_planner_minimal_delta_decisions.jsonl",
        "formalization_gap_planner_minimal_delta_decision_row.schema.json",
        "formalization_gap_planner_minimal_delta_audit.md",
    ):
        (minimal_delta_audit_dir / filename).write_text(
            (
                json.dumps(minimal_delta_decision_row_json_schema(), indent=2)
                if filename.endswith(".schema.json")
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_source_grounding_audit_manifest.json",
        "formalization_gap_planner_source_grounding_audit.jsonl",
        "formalization_gap_planner_source_grounding_row.schema.json",
        "formalization_gap_planner_source_grounding_audit.md",
    ):
        (source_grounding_audit_dir / filename).write_text(
            (
                json.dumps(source_grounding_row_json_schema(), indent=2)
                if filename.endswith(".schema.json")
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_refinement_queue_manifest.json",
        "formalization_gap_planner_refinement_queue.jsonl",
        "formalization_gap_planner_refinement_work_item.schema.json",
        "formalization_gap_planner_refinement_queue.md",
    ):
        (refinement_queue_dir / filename).write_text(
            (
                json.dumps(refinement_work_item_json_schema(), indent=2)
                if filename.endswith(".schema.json")
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_refinement_adapter_manifest.json",
        "formalization_gap_planner_refinement_evidence_responses.jsonl",
        "formalization_gap_planner_refinement_tool_response.schema.json",
        "formalization_gap_planner_refinement_adapter.md",
    ):
        (refinement_adapter_dir / filename).write_text(
            json.dumps(refinement_tool_response_json_schema(), indent=2)
            if filename == "formalization_gap_planner_refinement_tool_response.schema.json"
            else json.dumps({"fixture": filename})
            if filename.endswith(".json")
            else "fixture\n",
            encoding="utf-8",
        )
    local_formal_source_adapter_manifest = {
        "component_name": "formalization_gap_planner_local_formal_source_adapter",
        "n_local_formal_source_responses": 1,
        "n_responses_with_legacy_lean_declaration_hits": 0,
        "legacy_formal_source_adapter_field_aliases": (
            LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES
        ),
    }
    for directory, prefix in (
        (local_literature_adapter_dir, "formalization_gap_planner_local_literature_adapter"),
        (local_formal_source_adapter_dir, "formalization_gap_planner_local_formal_source_adapter"),
        (local_proof_state_adapter_dir, "formalization_gap_planner_local_proof_state_adapter"),
    ):
        for filename in (
            f"{prefix}_manifest.json",
            "formalization_gap_planner_refinement_evidence_responses.jsonl",
            f"{prefix}_responses.jsonl",
            "formalization_gap_planner_refinement_tool_response.schema.json",
            f"{prefix}.md",
        ):
            if (
                directory == local_formal_source_adapter_dir
                and filename == "formalization_gap_planner_local_formal_source_adapter_manifest.json"
            ):
                text = json.dumps(local_formal_source_adapter_manifest, indent=2)
            elif filename == "formalization_gap_planner_refinement_tool_response.schema.json":
                text = json.dumps(refinement_tool_response_json_schema(), indent=2)
            elif filename.endswith(".json"):
                text = json.dumps({"fixture": filename})
            else:
                text = "fixture\n"
            (directory / filename).write_text(
                text,
                encoding="utf-8",
            )
    for filename in (
        "formalization_gap_planner_refinement_evidence_manifest.json",
        "formalization_gap_planner_refinement_evidence.jsonl",
        "formalization_gap_planner_route_revision_proposals.jsonl",
        "formalization_gap_planner_refinement_tool_response.schema.json",
        "formalization_gap_planner_refinement_evidence_row.schema.json",
        "formalization_gap_planner_refinement_evidence.md",
    ):
        (refinement_evidence_dir / filename).write_text(
            json.dumps(refinement_tool_response_json_schema(), indent=2)
            if filename == "formalization_gap_planner_refinement_tool_response.schema.json"
            else json.dumps(refinement_evidence_row_json_schema(), indent=2)
            if filename == "formalization_gap_planner_refinement_evidence_row.schema.json"
            else json.dumps({"fixture": filename})
            if filename.endswith(".json")
            else "fixture\n",
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_route_revision_overlay_manifest.json",
        "formalization_gap_planner_route_revision_overlay.jsonl",
        "formalization_gap_planner_route_revision_overlay_row.schema.json",
        "formalization_gap_planner_route_revision_overlay.md",
    ):
        (route_revision_overlay_dir / filename).write_text(
            (
                json.dumps(route_revision_overlay_row_json_schema(), indent=2)
                if filename.endswith(".schema.json")
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_route_stability_audit_manifest.json",
        "formalization_gap_planner_route_stability_audit.jsonl",
        "formalization_gap_planner_route_stability_audit_row.schema.json",
        "formalization_gap_planner_route_stability_audit.md",
    ):
        (stability_audit_dir / filename).write_text(
            (
                json.dumps(route_stability_audit_row_json_schema(), indent=2)
                if filename == "formalization_gap_planner_route_stability_audit_row.schema.json"
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_route_replan_handoff_manifest.json",
        "formalization_gap_planner_route_replan_handoff.jsonl",
        "formalization_gap_planner_route_replan_handoff_row.schema.json",
        "formalization_gap_planner_route_replan_standalone_seed.json",
        "formalization_gap_planner_route_replan_standalone_seed.schema.json",
        "formalization_gap_planner_route_replan_handoff.md",
    ):
        (replan_handoff_dir / filename).write_text(
            (
                json.dumps(standalone_input_json_schema(), indent=2)
                if filename
                == "formalization_gap_planner_route_replan_standalone_seed.schema.json"
                else json.dumps(route_replan_handoff_row_json_schema(), indent=2)
                if filename == "formalization_gap_planner_route_replan_handoff_row.schema.json"
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_route_replan_handoff_audit_manifest.json",
        "formalization_gap_planner_route_replan_handoff_audit.jsonl",
        "formalization_gap_planner_route_replan_handoff_audit_row.schema.json",
        "formalization_gap_planner_route_replan_handoff_audit.md",
    ):
        (replan_handoff_audit_dir / filename).write_text(
            (
                json.dumps(route_replan_handoff_audit_row_json_schema(), indent=2)
                if filename == "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    runtime_handoff_audit_row = {
        "schema_version": 1,
        "check_id": "runtime_handoff_audit:fixture",
        "check_name": "row_llm_prompt_has_component_resource_registry_context",
        "category": "component_resource_registry",
        "handoff_id": "runtime_formalization_gap_planner_handoff:fixture",
        "bridge_id": "runtime_formalization_gap_planner_bridge:fixture",
        "expected": "prompt packets include component/resource/contract rows",
        "observed": "registry_components=2 registry_resources=3 registry_contracts=3",
        "ok": True,
        "severity": "error",
        "errors": [],
    }
    runtime_handoff_execution_plan = (
        _runtime_formalization_gap_planner_handoff_execution_plan(
            standalone_plan_cli=(
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-standalone-plan "
                "--input seed.json --out standalone_plan"
            ),
            target_intake_cli=(
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-target-intake "
                "--input target_intake.json --out target_intake_dir"
            ),
            component_resource_registry_cli=(
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-component-resource-registry "
                "--out component_resource_registry"
            ),
            llm_route_planner_prompt_cli=(
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-llm-route-planner "
                "--input seed.json --provider anthropic --model-tier auto "
                "--max-repair-attempts 1 "
                "--max-estimated-prompt-input-tokens 0 "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "standalone_plan "
                "--formalization-gap-planner-target-intake-dir "
                "target_intake_dir "
                "--formalization-gap-planner-component-resource-registry-dir "
                "component_resource_registry "
                "--out llm_prompt"
            ),
            llm_route_planner_live_cli=(
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-llm-route-planner "
                "--input seed.json --provider anthropic --model-tier auto "
                "--max-repair-attempts 1 "
                "--max-estimated-prompt-input-tokens 0 "
                "--goal-conditioned-minimal-formalization-plan-dir "
                "standalone_plan "
                "--formalization-gap-planner-target-intake-dir "
                "target_intake_dir "
                "--formalization-gap-planner-component-resource-registry-dir "
                "component_resource_registry "
                "--invoke-provider --out llm_live"
            ),
            reuse_smoke_cli=(
                "python3 -m ai_statistician.cli "
                "formalization-gap-planner-reuse-smoke "
                "--input target_intake.json "
                "--target-prover-family lean4 "
                "--target-library-snapshot-ref fixture "
                "--llm-route-planner-provider anthropic "
                "--llm-route-planner-model-tier auto "
                "--llm-route-planner-max-repair-attempts 1 "
                "--llm-route-planner-max-estimated-prompt-input-tokens 0 "
                "--feedback-llm-route-planner-provider anthropic "
                "--feedback-llm-route-planner-model-tier auto "
                "--feedback-llm-route-planner-max-repair-attempts 1 "
                "--feedback-llm-route-planner-max-estimated-prompt-input-tokens 0 "
                "--out reuse_smoke"
            ),
            standalone_seed_path="seed.json",
            target_intake_path="target_intake.json",
            standalone_plan_dir="standalone_plan",
            target_intake_dir="target_intake_dir",
            component_resource_registry_dir="component_resource_registry",
            llm_prompt_out="llm_prompt",
            llm_live_out="llm_live",
            reuse_smoke_out="reuse_smoke",
            target_prover_family="lean4",
            library_snapshot_ref="fixture",
        )
    )
    runtime_handoff_execution_plan["artifact_kind"] = (
        "RuntimeFormalizationGapPlannerHandoffExecutionPlan"
    )
    runtime_handoff_execution_plan["handoff_id"] = runtime_handoff_audit_row[
        "handoff_id"
    ]
    runtime_handoff_execution_plan["bridge_id"] = runtime_handoff_audit_row[
        "bridge_id"
    ]
    runtime_handoff_execution_plan["source_row_index"] = 0
    (
        runtime_handoff_audit_dir
        / "formalization_gap_planner_runtime_handoff_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_runtime_handoff_audit",
                "n_handoffs": 1,
                "n_checks": 1,
                "n_ok": 1,
                "n_failed": 0,
                "n_row_schema_valid": 1,
                "n_row_schema_invalid": 0,
                "n_cost_control_ok": 1,
                "n_live_explicit_ok": 1,
                "n_execution_plans": 1,
                "n_execution_plan_stage_rows": 6,
                "n_execution_plan_schema_valid": 1,
                "n_execution_plan_rows": 1,
                "n_execution_plan_row_schema_valid": 1,
                "n_execution_plan_row_schema_invalid": 0,
                "n_execution_plan_prompt_stage_cost_control_ok": 1,
                "n_execution_plan_live_stage_explicit_ok": 1,
                "n_execution_plan_reuse_smoke_stage_cost_control_ok": 1,
                "n_standalone_smoke_ok": 1,
                "n_llm_prompt_smoke_ok": 1,
                "n_llm_prompt_packets": 1,
                "n_llm_prompt_model_tier_mismatches": 0,
                "n_llm_prompt_model_tier_haiku": 0,
                "n_llm_prompt_model_tier_sonnet": 1,
                "n_llm_prompt_model_tier_opus": 0,
                "n_llm_prompt_model_tier_decision_sonnet_triggers": 0,
                "n_llm_prompt_requests_with_formal_attempt_feedback_summary": 0,
                "n_llm_prompt_formal_attempt_feedback_contexts": 0,
                "n_llm_prompt_formal_attempt_feedback_residual_goals": 0,
                "n_llm_prompt_formal_attempt_feedback_failed_statuses": 0,
                (
                    "n_llm_prompt_model_tier_decision_"
                    "formal_attempt_feedback_contexts"
                ): 0,
                (
                    "n_llm_prompt_model_tier_decision_"
                    "formal_attempt_feedback_residual_goals"
                ): 0,
                (
                    "n_llm_prompt_model_tier_decision_"
                    "formal_attempt_feedback_failed_statuses"
                ): 0,
                (
                    "n_llm_prompt_model_tier_decision_"
                    "formal_attempt_feedback_sonnet_triggers"
                ): 0,
                "n_component_resource_registry_smoke_ok": 1,
                "n_component_resource_registry_components_in_prompt": 2,
                "n_component_resource_registry_resources_in_prompt": 3,
                "n_component_resource_registry_contracts_in_prompt": 3,
                "all_ok": True,
                "checks": [runtime_handoff_audit_row],
                "proof_evidence_status": (
                    "FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": "not theorem proof evidence",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        runtime_handoff_audit_dir
        / "formalization_gap_planner_runtime_handoff_audit.jsonl"
    ).write_text(json.dumps(runtime_handoff_audit_row) + "\n", encoding="utf-8")
    (
        runtime_handoff_audit_dir
        / "formalization_gap_planner_runtime_handoff_execution_plans.jsonl"
    ).write_text(
        json.dumps(runtime_handoff_execution_plan, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        runtime_handoff_audit_dir
        / "formalization_gap_planner_runtime_handoff_audit_row.schema.json"
    ).write_text(
        json.dumps(runtime_handoff_audit_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        runtime_handoff_audit_dir
        / "formalization_gap_planner_runtime_handoff_execution_plan.schema.json"
    ).write_text(
        json.dumps(runtime_handoff_execution_plan_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        runtime_handoff_audit_dir
        / "formalization_gap_planner_runtime_handoff_audit.md"
    ).write_text("fixture\n", encoding="utf-8")
    for filename in (
        "formalization_gap_planner_proof_state_triage_manifest.json",
        "formalization_gap_planner_proof_state_triage.jsonl",
        "formalization_gap_planner_proof_state_triage_row.schema.json",
        "formalization_gap_planner_proof_state_triage.md",
    ):
        (proof_state_triage_dir / filename).write_text(
            (
                json.dumps(proof_state_triage_row_json_schema(), indent=2)
                if filename == "formalization_gap_planner_proof_state_triage_row.schema.json"
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_interactive_session_manifest.json",
        "formalization_gap_planner_interactive_session.jsonl",
        "formalization_gap_planner_interactive_session_row.schema.json",
        "formalization_gap_planner_interactive_decision_policy.jsonl",
        "formalization_gap_planner_interactive_decision_policy_row.schema.json",
        "formalization_gap_planner_interactive_session.md",
    ):
        (interactive_session_dir / filename).write_text(
            (
                json.dumps(interactive_session_row_json_schema(), indent=2)
                if filename == "formalization_gap_planner_interactive_session_row.schema.json"
                else json.dumps(interactive_decision_policy_row_json_schema(), indent=2)
                if filename
                == "formalization_gap_planner_interactive_decision_policy_row.schema.json"
                else json.dumps(
                    {
                        "schema_version": 1,
                        "component_name": "formalization_gap_planner_interactive_session",
                        "n_decision_policy_rows": 1,
                        "n_decision_policy_row_schema_valid": 1,
                        "n_decision_policy_row_schema_invalid": 0,
                        "n_decision_policy_rows_with_resource_contracts": 1,
                        "n_decision_policy_rows_with_frontier_resources": 1,
                        "proof_evidence_boundary": "not theorem proof evidence",
                    },
                    indent=2,
                )
                if filename
                == "formalization_gap_planner_interactive_session_manifest.json"
                else json.dumps(
                    {
                        "schema_version": 1,
                        "decision_policy_row_id": "policy:fixture",
                        "interactive_session_row_id": "session:fixture",
                        "goal_plan_id": "goal:fixture",
                        "route_id": "route:fixture",
                        "display_name": "fixture route",
                        "session_state": "ROUTE_STABLE_READY_FOR_REPLAY",
                        "next_interaction_kind": "target_prover_replay",
                        "decision_rationale": "fixture replay policy",
                        "trigger_signals": [
                            "session_state:ROUTE_STABLE_READY_FOR_REPLAY",
                            "stable_under_current_evidence_bound",
                        ],
                        "evidence_inputs": [
                            "goal_conditioned_minimal_formalization_plan"
                        ],
                        "required_tool_contracts": [
                            "formalization_gap_planner_prover_adapter_packet.schema.json"
                        ],
                        "component_ids": [
                            "cross_prover_public_reuse",
                            "prover_feedback_refinement",
                        ],
                        "local_first_resource_ids": [
                            "cross_prover_matrix_audit",
                            "local_lake_lean",
                        ],
                        "frontier_escalation_resource_ids": ["lean_lsp_mcp"],
                        "resource_contract_ids": interactive_policy_contract_ids,
                        "required_quality_signals": [
                            "schema_valid_outputs",
                            "proof_boundary_preserved",
                            "portable_contract_artifacts_present",
                            "proof_state_residuals_classified",
                        ],
                        "quality_gates": [
                            "schema_valid_outputs",
                            "proof_boundary_preserved",
                            "no_kernel_claim_without_replay",
                        ],
                        "response_validation_signals": [
                            "schema_valid_response",
                            "proof_boundary_preserved",
                            "target_prover_family_and_adapter_contract_present",
                            "proof_state_diagnostics_or_residuals_present",
                        ],
                        "stop_conditions": [
                            "target prover replay is attempted through its kernel or certified checker"
                        ],
                        "fallback_actions": ["export prover-adapter packets"],
                        "bounded_evidence_claim": "not theorem proof evidence",
                        "resource_selection_rationale": "fixture resource contract mapping",
                        "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_NOT_PROOF_EVIDENCE",
                        "proof_evidence_boundary": "not theorem proof evidence",
                        "ok": True,
                        "errors": [],
                    }
                )
                if filename
                == "formalization_gap_planner_interactive_decision_policy.jsonl"
                else json.dumps({"fixture": filename})
                if filename.endswith(".json")
                else "fixture\n"
            ),
            encoding="utf-8",
        )
    prover_packet = _fixture_prover_adapter_packet()
    response_validation_row = _fixture_prover_adapter_response_validation_row(
        prover_packet
    )
    (prover_contract_dir / "formalization_gap_planner_prover_adapter_contract_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_prover_adapter_contract",
                "n_packets": 1,
                "n_packet_schema_valid": 1,
                "n_packet_ok": 1,
                "n_response_validation_row_schema_valid": 1,
                "n_response_validation_row_schema_invalid": 0,
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (prover_contract_dir / "formalization_gap_planner_prover_adapter_packets.jsonl").write_text(
        json.dumps(prover_packet, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (prover_contract_dir / "formalization_gap_planner_prover_adapter_packet.schema.json").write_text(
        json.dumps(prover_adapter_packet_json_schema(), indent=2),
        encoding="utf-8",
    )
    for filename in (
        "formalization_gap_planner_prover_adapter_response.schema.json",
        "formalization_gap_planner_prover_adapter_contract.md",
    ):
        (prover_contract_dir / filename).write_text(
            json.dumps({"fixture": filename}) if filename.endswith(".json") else "fixture\n",
            encoding="utf-8",
        )
    (
        prover_contract_dir
        / "formalization_gap_planner_prover_adapter_response_validation.jsonl"
    ).write_text(
        json.dumps(response_validation_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        prover_contract_dir
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    ).write_text(
        json.dumps(prover_adapter_response_validation_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    cross_prover_matrix_row = _fixture_cross_prover_matrix_row(
        prover_packet,
        response_validation_row,
    )
    cross_prover_target_summary = _fixture_cross_prover_target_summary(prover_packet)
    (cross_prover_matrix_dir / "formalization_gap_planner_cross_prover_matrix_audit_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_cross_prover_matrix_audit",
                "n_targets": 1,
                "n_targets_ok": 1,
                "n_matrix_row_schema_valid": 1,
                "n_matrix_row_schema_invalid": 0,
                "n_total_packets": 1,
                "n_total_packet_ok": 1,
                "n_total_packet_schema_valid": 1,
                "n_total_packets_schema_invalid": 0,
                "n_packet_row_schema_valid": 1,
                "n_packet_row_schema_invalid": 0,
                "n_response_validation_row_schema_valid": 1,
                "n_response_validation_row_schema_invalid": 0,
                "n_total_packets_with_alignment": 1,
                "n_total_packets_missing_alignment": 0,
                "n_total_packets_with_standalone_input_trace": 1,
                "n_total_packets_missing_standalone_input_trace": 0,
                    "n_total_packets_with_target_library_snapshot_trace": 1,
                    "n_total_packets_missing_target_library_snapshot_trace": 0,
                    "n_total_packets_target_library_snapshot_mismatch": 0,
                    "n_total_packets_with_replan_metadata_trace": 1,
                    "n_total_packets_with_residual_goal_contexts": 1,
                    "n_total_packet_residual_goal_contexts": 1,
                    "packet_residual_context_source_kinds": [
                        "proof_state_feedback"
                    ],
                    "n_total_packet_residual_contexts_with_source_refs": 1,
                    "n_total_packet_residual_contexts_with_formal_gap_boundary": 1,
                    "n_total_packets_with_quality_controls": 1,
                "n_total_packet_quality_control_fields": 4,
                "packet_quality_control_fields": [
                    "required_quality_signals",
                    "resource_contract_ids",
                    "response_validation_signals",
                    "stop_conditions",
                ],
                "packet_quality_control_resource_contract_ids": [
                    "lean_lsp:proof_state_feedback"
                ],
                "packet_quality_control_response_validation_signals": [
                    "residual_goals_or_diagnostics_present"
                ],
                "packet_quality_control_stop_conditions": [
                    "residual interpreted or source search requested"
                ],
                "by_total_packet_quality_control_field": {
                    "required_quality_signals": {
                        "n_packets": 1,
                        "n_values": 1,
                        "values": ["diagnostic_signature"],
                    },
                    "resource_contract_ids": {
                        "n_packets": 1,
                        "n_values": 1,
                        "values": ["lean_lsp:proof_state_feedback"],
                    },
                    "response_validation_signals": {
                        "n_packets": 1,
                        "n_values": 1,
                        "values": ["residual_goals_or_diagnostics_present"],
                    },
                    "stop_conditions": {
                        "n_packets": 1,
                        "n_values": 1,
                        "values": [
                            "residual interpreted or source search requested"
                        ],
                    },
                },
                "n_total_packets_with_llm_route_adoption_status": 1,
                "n_total_packets_llm_route_adoption_ready": 0,
                "n_total_packets_llm_route_adoption_pending_refinement": 1,
                "n_total_packets_llm_route_adoption_rejected": 0,
                "n_total_packets_llm_route_adoption_awaiting_response": 0,
                "n_total_packet_llm_route_adoption_blockers": 2,
                "n_total_packet_llm_route_adoption_pending_quality_control_blockers": 1,
                "n_total_packet_llm_route_adoption_pending_source_grounding_blockers": 0,
                "by_total_packet_llm_route_adoption_status": {
                    "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
                },
                "n_total_packets_with_formal_attempt_dependency": 0,
                "n_total_packets_formal_attempt_initial_ready": 0,
                "n_total_packets_formal_attempt_waiting": 0,
                "n_total_packets_formal_attempt_missing_prerequisites": 0,
                "by_total_packet_formal_attempt_dependency_status": {
                    "not_formal_attempt_queue_item": 1
                },
                "n_response_minimal_delta_action_witnesses_required": 0,
                "n_response_minimal_delta_action_witnesses_acknowledged": 0,
                "n_response_minimal_delta_action_witnesses_unacknowledged": 0,
                "n_response_addressed_minimal_delta_action_witnesses": 0,
                "packet_count_consistent": True,
                "alignment_packet_count_consistent": True,
                    "standalone_input_trace_packet_count_consistent": True,
                    "target_library_snapshot_trace_packet_count_consistent": True,
                    "quality_control_packet_count_consistent": True,
                    "residual_context_packet_count_consistent": True,
                    "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        cross_prover_matrix_dir
        / "formalization_gap_planner_cross_prover_matrix_audit.jsonl"
    ).write_text(
        json.dumps(cross_prover_matrix_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        cross_prover_matrix_dir
        / "formalization_gap_planner_cross_prover_target_summary.json"
    ).write_text(
        json.dumps(cross_prover_target_summary, indent=2),
        encoding="utf-8",
    )
    (
        cross_prover_matrix_dir
        / "formalization_gap_planner_cross_prover_packets.jsonl"
    ).write_text(json.dumps(prover_packet, sort_keys=True) + "\n", encoding="utf-8")
    (
        cross_prover_matrix_dir
        / "formalization_gap_planner_cross_prover_response_validation.jsonl"
    ).write_text(
        json.dumps(response_validation_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        cross_prover_matrix_dir
        / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
    ).write_text(
        json.dumps(cross_prover_matrix_audit_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        cross_prover_matrix_dir
        / "formalization_gap_planner_cross_prover_target_summary.schema.json"
    ).write_text(
        json.dumps(cross_prover_target_summary_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        cross_prover_matrix_dir
        / "formalization_gap_planner_prover_adapter_packet.schema.json"
    ).write_text(json.dumps(prover_adapter_packet_json_schema(), indent=2), encoding="utf-8")
    (
        cross_prover_matrix_dir
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    ).write_text(
        json.dumps(prover_adapter_response_validation_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (cross_prover_matrix_dir / "formalization_gap_planner_cross_prover_matrix_audit.md").write_text(
        "fixture\n",
        encoding="utf-8",
    )
    for filename in (
        "formalization_gap_planner_adapter_registry_audit_manifest.json",
        "formalization_gap_planner_adapter_registry_audit.jsonl",
        "formalization_gap_planner_adapter_registry_audit.md",
    ):
        (adapter_registry_audit_dir / filename).write_text(
            json.dumps({"fixture": filename}) if filename.endswith(".json") else "fixture\n",
            encoding="utf-8",
        )
    for filename in (
        "formalization_gap_planner_component_resource_registry_audit_manifest.json",
        "formalization_gap_planner_component_resource_registry_audit.jsonl",
        "formalization_gap_planner_component_resource_registry_audit.md",
    ):
        (component_resource_registry_audit_dir / filename).write_text(
            json.dumps({"fixture": filename}) if filename.endswith(".json") else "fixture\n",
            encoding="utf-8",
        )

    payload = export_formalization_gap_planner_publication_bundle(
        out_dir,
        lean_rag_db_path=lean_rag_db,
        paper_library_dir=paper_dir,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
        goal_conditioned_minimal_formalization_plan_dir=plan_dir,
        formalization_gap_planner_evaluation_dir=evaluation_dir,
        formalization_gap_planner_ablation_study_dir=ablation_study_dir,
        formalization_gap_planner_portable_plan_audit_dir=plan_audit_dir,
        formalization_gap_planner_library_coverage_map_dir=library_coverage_map_dir,
        formalization_gap_planner_primitive_action_queue_dir=primitive_action_queue_dir,
        formalization_gap_planner_minimal_delta_audit_dir=minimal_delta_audit_dir,
        formalization_gap_planner_source_grounding_audit_dir=source_grounding_audit_dir,
        formalization_gap_planner_refinement_queue_dir=refinement_queue_dir,
        formalization_gap_planner_refinement_adapter_dir=refinement_adapter_dir,
        formalization_gap_planner_local_literature_adapter_dir=local_literature_adapter_dir,
        formalization_gap_planner_local_formal_source_adapter_dir=local_formal_source_adapter_dir,
        formalization_gap_planner_local_proof_state_adapter_dir=local_proof_state_adapter_dir,
        formalization_gap_planner_refinement_evidence_dir=refinement_evidence_dir,
        formalization_gap_planner_route_revision_overlay_dir=route_revision_overlay_dir,
        formalization_gap_planner_route_stability_audit_dir=stability_audit_dir,
        formalization_gap_planner_route_replan_handoff_dir=replan_handoff_dir,
        formalization_gap_planner_route_replan_handoff_audit_dir=replan_handoff_audit_dir,
        formalization_gap_planner_runtime_handoff_audit_dir=runtime_handoff_audit_dir,
        formalization_gap_planner_proof_state_triage_dir=proof_state_triage_dir,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
        formalization_gap_planner_prover_adapter_contract_dir=prover_contract_dir,
        formalization_gap_planner_cross_prover_matrix_audit_dir=cross_prover_matrix_dir,
        formalization_gap_planner_adapter_registry_audit_dir=adapter_registry_audit_dir,
        formalization_gap_planner_component_resource_registry_audit_dir=component_resource_registry_audit_dir,
        library_snapshot_ref="fixture_snapshot",
    )

    assert payload["all_ok"]
    assert payload["portable_schema_id"] == PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID
    assert payload["n_core_artifacts_ok"] == payload["n_core_artifacts"]
    assert payload["benchmark_summary"]["n_routes"] >= 1
    assert payload["benchmark_summary"]["target_prover_family"] == "lean4"
    assert payload["benchmark_summary"]["n_target_prover_families"] == 1
    assert payload["benchmark_summary"]["by_target_prover_family"] == {
        "lean4": payload["benchmark_summary"]["n_routes"]
    }
    assert (
        payload["benchmark_summary"]["n_route_row_schema_valid"]
        == payload["benchmark_summary"]["n_routes"]
    )
    assert payload["benchmark_summary"]["n_route_row_schema_invalid"] == 0
    assert payload["benchmark_summary"]["n_kernel_verification_witnesses"] == 0
    assert (
        payload["benchmark_summary"]["n_kernel_verified_routes_missing_witnesses"]
        == 0
    )
    assert payload["benchmark_audit_summary"]["n_failed"] == 0
    assert payload["benchmark_audit_summary"]["n_evaluation_splits"] >= 2
    assert payload["benchmark_audit_summary"]["n_target_prover_families"] == 1
    assert payload["benchmark_audit_summary"]["by_target_prover_family"] == {
        "lean4": payload["benchmark_summary"]["n_routes"]
    }
    assert payload["evaluation_summary"]["requested"] is True
    assert payload["evaluation_summary"]["n_evaluation_rows"] == 1
    assert payload["evaluation_summary"]["n_evaluation_row_schema_valid"] == 1
    assert payload["evaluation_summary"]["n_evaluation_row_schema_invalid"] == 0
    assert payload["evaluation_summary"]["n_minimal_delta_route_options"] == 0
    assert (
        payload["evaluation_summary"]["mean_minimal_delta_selected_route_cost"]
        == 0.0
    )
    assert payload["evaluation_summary"]["n_kernel_verified_ground_truth"] == 0
    assert payload["evaluation_summary"]["n_kernel_verification_witnesses"] == 0
    assert (
        payload["evaluation_summary"][
            "n_kernel_verified_ground_truth_with_witnesses"
        ]
        == 0
    )
    assert payload["evaluation_summary"]["mean_alignment_coverage"] == 1.0
    assert payload["library_coverage_map_summary"]["requested"] is True
    assert payload["library_coverage_map_summary"]["target_prover_family"] == "lean4"
    assert payload["library_coverage_map_summary"]["n_target_prover_families"] == 1
    assert payload["library_coverage_map_summary"]["by_target_prover_family"] == {
        "lean4": 1
    }
    assert payload["library_coverage_map_summary"]["n_coverage_rows"] == 1
    assert payload["library_coverage_map_summary"]["n_ok"] == 1
    assert payload["library_coverage_map_summary"]["all_ok"] is True
    report_text = (
        out_dir / "formalization_gap_planner_publication_bundle.md"
    ).read_text(encoding="utf-8")
    assert (
        "Library coverage map target families: lean4 by={'lean4': 1}"
        in report_text
    )
    assert (
        payload["evaluation_summary"][
            "n_rows_with_llm_route_planner_residual_goal_contexts"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"]["n_llm_route_planner_residual_goal_contexts"]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_residual_goal_context_source_refs"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_residual_goal_context_provenance_values"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_residual_goals_without_context"
        ]
        == 1
    )
    assert (
        payload["evaluation_summary"][
            "n_rows_with_llm_route_planner_route_option_selection_brief"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_candidate_options"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_candidate_primitives"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_candidates_with_residual_goals"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_candidate_residual_goals"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_candidate_formal_source_retrieval_metadata_rows"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_candidate_formal_source_semantic_rerank_rows"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_candidate_formal_source_target_compatible_hits"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_lower_bound_residual_goals"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_lower_bound_formal_source_retrieval_metadata_rows"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_lower_bound_formal_source_semantic_rerank_rows"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_lower_bound_formal_source_target_compatible_hits"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_rows_with_llm_route_planner_route_option_selected_route_option"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_minimal_delta_selected_residual_goals"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_lower_bound_matches_minimal_delta"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selection_lower_bound_mismatches_minimal_delta"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selected_matches_lower_bound"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selected_mismatches_lower_bound"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selected_matches_minimal_delta"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_option_selected_mismatches_minimal_delta"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_rows_with_incomplete_cost_hint_baseline_coverage"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"]["n_realization_cost_hint_baseline_primitives"]
        == 0
    )
    assert (
        payload["evaluation_summary"]["n_realization_omitted_cost_hint_primitives"]
        == 0
    )
    assert payload["evaluation_summary"]["realization_cost_hint_baseline_primitives"] == ()
    assert payload["evaluation_summary"]["realization_omitted_cost_hint_primitives"] == ()
    assert (
        payload["evaluation_summary"][
            "n_rows_with_llm_route_planner_route_adoption_status"
        ]
        == 0
    )
    assert payload["evaluation_summary"]["n_rows_ready_for_route_adoption"] == 0
    assert (
        payload["evaluation_summary"][
            "n_rows_pending_refinement_before_route_adoption"
        ]
        == 0
    )
    assert payload["evaluation_summary"]["n_llm_route_adoption_blockers"] == 0
    assert (
        payload["evaluation_summary"][
            "n_rows_with_llm_route_planner_route_adoption_preconditions"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_rows_with_llm_route_planner_blocking_route_adoption_preconditions"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_adoption_precondition_known_blockers"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "n_llm_route_planner_route_adoption_precondition_required_response_fields"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "llm_route_planner_route_adoption_precondition_known_blockers"
        ]
        == ()
    )
    assert (
        payload["evaluation_summary"][
            "llm_route_planner_route_adoption_precondition_required_response_fields"
        ]
        == ()
    )
    assert payload["evaluation_summary"]["llm_route_adoption_blockers"] == ()
    assert payload["evaluation_summary"]["llm_route_adoption_blocker_counts"] == {}
    assert payload["evaluation_summary"]["llm_route_adoption_status_counts"] == {}
    assert (
        payload["evaluation_summary"]["evaluation_by_llm_route_adoption_blocker"]
        == {}
    )
    assert (
        payload["evaluation_summary"]["llm_route_planner_provider_usage_summary"]
        == {}
    )
    assert (
        payload["evaluation_summary"][
            "n_rows_with_llm_route_planner_provider_usage"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "total_llm_route_planner_provider_input_tokens"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "total_llm_route_planner_provider_output_tokens"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "total_llm_route_planner_provider_cache_creation_input_tokens"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "total_llm_route_planner_provider_cache_read_input_tokens"
        ]
        == 0
    )
    assert (
        payload["evaluation_summary"][
            "total_llm_route_planner_provider_total_tokens"
        ]
        == 0
    )
    assert payload["evaluation_summary"]["n_rows_with_quality_controls"] == 0
    assert payload["evaluation_summary"]["n_quality_control_fields"] == 0
    assert payload["evaluation_summary"]["quality_control_fields"] == ()
    assert payload["evaluation_summary"]["quality_control_resource_contract_ids"] == ()
    assert (
        payload["evaluation_summary"]["quality_control_response_validation_signals"]
        == ()
    )
    assert payload["evaluation_summary"]["quality_control_stop_conditions"] == ()
    cross_prover_attempt_summary = payload[
        "cross_prover_formal_attempt_dependency_summary"
    ]
    assert cross_prover_attempt_summary["requested"] is True
    assert cross_prover_attempt_summary["n_total_packets"] == 1
    assert (
        cross_prover_attempt_summary[
            "n_total_packets_with_formal_attempt_dependency"
        ]
        == 0
    )
    assert (
        cross_prover_attempt_summary[
            "n_total_packets_formal_attempt_initial_ready"
        ]
        == 0
    )
    assert (
        cross_prover_attempt_summary["n_total_packets_formal_attempt_waiting"]
        == 0
    )
    assert (
        cross_prover_attempt_summary[
            "n_total_packets_formal_attempt_missing_prerequisites"
        ]
        == 0
    )
    assert cross_prover_attempt_summary[
        "by_total_packet_formal_attempt_dependency_status"
    ] == {"not_formal_attempt_queue_item": 1}
    assert (
        cross_prover_attempt_summary[
            "n_total_response_minimal_delta_action_witnesses_required"
        ]
        == 0
    )
    assert (
        cross_prover_attempt_summary[
            "n_total_response_minimal_delta_action_witnesses_acknowledged"
        ]
        == 0
    )
    assert (
        cross_prover_attempt_summary[
            "n_total_response_minimal_delta_action_witnesses_unacknowledged"
        ]
        == 0
    )
    assert (
        cross_prover_attempt_summary[
            "n_total_response_addressed_minimal_delta_action_witnesses"
        ]
        == 0
    )
    assert cross_prover_attempt_summary["target_summary_consistent"] is True
    assert payload["llm_route_planner_summary"]["requested"] is False
    _assert_no_route_planner_execution_summary(payload["llm_route_planner_summary"])
    assert payload["llm_route_planner_summary"]["n_request_packets"] == 0
    assert payload["llm_route_planner_summary"]["n_rows"] == 0
    assert (
        payload["llm_route_planner_summary"][
            "n_request_proof_execution_feedback_rows"
        ]
        == 0
    )
    assert (
        payload["llm_route_planner_summary"][
            "n_feedback_loop_summary_prior_llm_route_planner_hook_traces"
        ]
        == 0
    )
    assert payload["llm_route_planner_summary"]["route_adoption_blocker_counts"] == {}
    assert (
        payload["llm_route_planner_summary"][
            "n_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == 0
    )
    assert payload["llm_route_planner_summary"]["by_route_adoption_status"] == {}
    assert payload["feedback_llm_route_planner_summary"]["requested"] is False
    _assert_no_route_planner_execution_summary(
        payload["feedback_llm_route_planner_summary"]
    )
    assert payload["feedback_llm_route_planner_summary"]["n_request_packets"] == 0
    assert payload["feedback_llm_route_planner_summary"]["n_rows"] == 0
    assert (
        payload["feedback_llm_route_planner_summary"][
            "n_request_proof_execution_feedback_rows"
        ]
        == 0
    )
    assert (
        payload["feedback_llm_route_planner_summary"][
            "n_feedback_loop_summary_prior_llm_route_planner_hook_traces"
        ]
        == 0
    )
    assert (
        payload["feedback_llm_route_planner_summary"][
            "route_adoption_blocker_counts"
        ]
        == {}
    )
    assert (
        payload["feedback_llm_route_planner_summary"][
            "n_route_adoption_pending_formal_gap_boundary_blockers"
        ]
        == 0
    )
    assert payload["feedback_llm_route_planner_summary"]["by_route_adoption_status"] == {}
    assert payload["adapter_registry_summary"]["n_adapters"] >= 16
    assert (
        payload["adapter_registry_summary"]["n_adapter_row_schema_valid"]
        == payload["adapter_registry_summary"]["n_adapters"]
    )
    assert payload["adapter_registry_summary"]["n_adapter_row_schema_invalid"] == 0
    assert payload["component_resource_registry_summary"]["n_component_rows"] >= 8
    assert payload["component_resource_registry_summary"]["n_frontier_resources"] >= 10
    assert (
        payload["component_resource_registry_summary"]["n_component_row_schema_valid"]
        == payload["component_resource_registry_summary"]["n_component_rows"]
    )
    assert payload["component_resource_registry_summary"]["n_component_row_schema_invalid"] == 0
    assert (
        payload["component_resource_registry_summary"]["n_resource_row_schema_valid"]
        == payload["component_resource_registry_summary"]["n_resources"]
    )
    assert payload["component_resource_registry_summary"]["n_resource_row_schema_invalid"] == 0
    assert (
        payload["component_resource_registry_summary"]["n_resource_contract_rows"]
        == payload["component_resource_registry_summary"]["n_resources"]
    )
    assert (
        payload["component_resource_registry_summary"][
            "n_resource_contract_row_schema_valid"
        ]
        == payload["component_resource_registry_summary"]["n_resource_contract_rows"]
    )
    assert (
        payload["component_resource_registry_summary"][
            "n_resource_contract_row_schema_invalid"
        ]
        == 0
    )
    assert payload["n_optional_artifact_files_copied"] == 128
    assert payload["runtime_handoff_audit_summary"][
        "n_llm_prompt_model_tier_mismatches"
    ] == 0
    assert payload["runtime_handoff_audit_summary"][
        "n_llm_prompt_model_tier_haiku"
    ] == 0
    assert payload["runtime_handoff_audit_summary"][
        "n_llm_prompt_model_tier_sonnet"
    ] == 1
    assert payload["runtime_handoff_audit_summary"][
        "n_llm_prompt_model_tier_opus"
    ] == 0
    assert payload["schema_catalog_summary"]["all_ok"]
    assert payload["schema_catalog_summary"]["n_schema_catalog_contract_errors"] == 0
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (out_dir / "contract" / "library_aware_formalization_gap_plan.schema.json").exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_portable_contract.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_prover_adapter_response.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_prover_adapter_packet.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_cross_prover_target_summary.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_refinement_evidence_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_refinement_work_item.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_proof_state_triage_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_interactive_session_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_interactive_decision_policy_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_portable_plan_audit_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_library_coverage_map_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_primitive_action_queue_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_action_resource_plan_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_resource_request_queue_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_resource_response.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_resource_response_ledger_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_source_grounding_row.schema.json"
    ).exists()
    assert (
        json.loads(
            (
                out_dir
                / "contract"
                / "formalization_gap_planner_llm_route_planner_request.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == LLM_ROUTE_PLANNER_REQUEST_SCHEMA_ID
    )
    library_alignment_summary_schema_payload = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        library_alignment_summary_schema_payload["$id"]
        == LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID
    )
    assert (
        library_alignment_summary_schema_payload
        == llm_route_planner_library_alignment_summary_json_schema()
    )
    target_theorem_context_schema_payload = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_llm_route_planner_target_theorem_context_packet.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        target_theorem_context_schema_payload["$id"]
        == LLM_ROUTE_PLANNER_TARGET_THEOREM_CONTEXT_PACKET_SCHEMA_ID
    )
    assert (
        target_theorem_context_schema_payload
        == llm_route_planner_target_theorem_context_packet_json_schema()
    )
    route_planning_brief_schema_payload = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        route_planning_brief_schema_payload["$id"]
        == LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID
    )
    assert (
        route_planning_brief_schema_payload
        == llm_route_planner_route_planning_brief_json_schema()
    )
    assert (
        json.loads(
            (
                out_dir
                / "contract"
                / "formalization_gap_planner_llm_route_planner_response.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == LLM_ROUTE_PLANNER_RESPONSE_SCHEMA_ID
    )
    assert (
        json.loads(
            (
                out_dir
                / "contract"
                / "formalization_gap_planner_llm_route_planner_response_payload.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_SCHEMA_ID
    )
    lean_legacy_payload_schema = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_llm_route_planner_response_payload_lean_legacy.schema.json"
        ).read_text(encoding="utf-8")
    )
    target_prover_payload_schema = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_llm_route_planner_response_payload_target_prover.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert lean_legacy_payload_schema["$id"] == (
        LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_LEAN_LEGACY_SCHEMA_ID
    )
    assert target_prover_payload_schema["$id"] == (
        LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_TARGET_PROVER_SCHEMA_ID
    )
    target_prover_payload_families = [
        target for target in PORTABLE_REUSE_TARGETS if target != "lean4"
    ]
    assert lean_legacy_payload_schema["x-target-prover-families"] == ["lean4"]
    assert (
        target_prover_payload_schema["x-target-prover-families"]
        == target_prover_payload_families
    )
    assert "lean_realization_dag_nodes" in lean_legacy_payload_schema[
        "properties"
    ]
    assert "lean_realization_dag_nodes" not in target_prover_payload_schema[
        "properties"
    ]
    assert target_prover_payload_schema["anyOf"] == [
        {"required": ["formal_realization_dag_nodes"]}
    ]
    assert (
        json.loads(
            (
                out_dir
                / "contract"
                / "formalization_gap_planner_llm_route_planner_response_payload_validation_manifest.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_MANIFEST_SCHEMA_ID
    )
    assert (
        json.loads(
            (
                out_dir
                / "contract"
                / "formalization_gap_planner_llm_route_planner_response_payload_validation_row.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == LLM_ROUTE_PLANNER_RESPONSE_PAYLOAD_VALIDATION_ROW_SCHEMA_ID
    )
    assert (
        json.loads(
            (
                out_dir
                / "contract"
                / "formalization_gap_planner_llm_route_planner_manifest.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID
    )
    assert (
        json.loads(
            (
                out_dir
                / "contract"
                / "formalization_gap_planner_llm_route_planner_row.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == LLM_ROUTE_PLANNER_ROW_SCHEMA_ID
    )
    route_adoption_taxonomy_schema = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_route_adoption_blocker_taxonomy.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert route_adoption_taxonomy_schema == route_adoption_blocker_taxonomy_json_schema()
    route_adoption_taxonomy_manifest_schema = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        route_adoption_taxonomy_manifest_schema
        == route_adoption_blocker_taxonomy_manifest_json_schema()
    )
    route_adoption_taxonomy_contract = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_route_adoption_blocker_taxonomy.json"
        ).read_text(encoding="utf-8")
    )
    assert route_adoption_taxonomy_contract["schema_id"] == (
        ROUTE_ADOPTION_BLOCKER_TAXONOMY_SCHEMA_ID
    )
    assert validate_route_adoption_blocker_taxonomy_payload(
        route_adoption_taxonomy_contract
    ) == ()
    assert (
        "rows[].realization_coverage_witness.realization_coverage_complete"
        in route_adoption_taxonomy_contract["blocker_trigger_fields"][
            ROUTE_ADOPTION_BLOCKER_REALIZATION_COVERAGE
        ]
    )
    assert (
        out_dir / "contract" / "formalization_gap_planner_route_revision_overlay_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_route_stability_audit_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_route_replan_handoff_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_runtime_handoff_audit_row.schema.json"
    ).exists()
    runtime_handoff_execution_plan_schema = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_runtime_handoff_execution_plan.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        runtime_handoff_execution_plan_schema["$id"]
        == RUNTIME_HANDOFF_EXECUTION_PLAN_SCHEMA_ID
    )
    assert (
        runtime_handoff_execution_plan_schema
        == runtime_handoff_execution_plan_json_schema()
    )
    assert (
        out_dir / "contract" / "formalization_gap_planner_ablation_study_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_route_alignment_edge.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "library_aware_formalization_gap_plan_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_schema_catalog.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_schema_catalog.schema.json"
    ).exists()
    publication_bundle_manifest_schema_payload = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_publication_bundle_manifest.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert publication_bundle_manifest_schema_payload["$id"] == (
        FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID
    )
    assert (
        publication_bundle_manifest_schema_payload["$id"]
        == publication_bundle_manifest_json_schema()["$id"]
    )
    assert (
        "llm_route_planner_response_payload_validation_summary"
        in publication_bundle_manifest_schema_payload["required"]
    )
    assert (
        "cross_prover_formal_attempt_dependency_summary"
        in publication_bundle_manifest_schema_payload["required"]
    )
    assert (
        "library_coverage_map_summary"
        in publication_bundle_manifest_schema_payload["required"]
    )
    evaluation_summary_schema = publication_bundle_manifest_schema_payload[
        "properties"
    ]["evaluation_summary"]
    assert set(
        evaluation_summary_schema["properties"]["llm_route_adoption_blockers"][
            "items"
        ]["enum"]
    ) == set(ROUTE_ADOPTION_BLOCKER_VALUES)
    assert set(
        evaluation_summary_schema["properties"][
            "llm_route_planner_route_adoption_precondition_known_blockers"
        ]["items"]["enum"]
    ) == set(ROUTE_ADOPTION_BLOCKER_VALUES)
    assert (
        "n_llm_route_adoption_pending_formal_attempt_queue_blockers"
        in evaluation_summary_schema["required"]
    )
    llm_summary_schema = publication_bundle_manifest_schema_payload[
        "properties"
    ]["llm_route_planner_summary"]
    assert set(
        llm_summary_schema["properties"]["route_adoption_blockers"]["items"][
            "enum"
        ]
    ) == set(ROUTE_ADOPTION_BLOCKER_VALUES)
    assert "n_request_available_source_snippets" in llm_summary_schema["required"]
    assert "n_requests_with_residual_goal_contexts" in llm_summary_schema["required"]
    assert "n_request_model_tier_sonnet" in llm_summary_schema["required"]
    assert "by_request_model_tier" in llm_summary_schema["required"]
    assert "n_request_target_prover_families" in llm_summary_schema["required"]
    assert "by_request_target_prover_family" in llm_summary_schema["required"]
    for field_name in (
        "estimated_prompt_input_cost_micro_usd",
        "estimated_prompt_max_output_cost_micro_usd",
        "estimated_prompt_base_input_output_cost_micro_usd",
        "n_prompt_token_budget_rows_with_estimated_base_cost",
    ):
        assert field_name in llm_summary_schema["required"]
        assert llm_summary_schema["properties"][field_name]["type"] == "integer"
        assert llm_summary_schema["properties"][field_name]["minimum"] == 0
    assert "n_planner_next_actions" in llm_summary_schema["required"]
    assert "n_row_residual_goal_contexts" in llm_summary_schema["required"]
    assert "n_rows_with_source_snippets" in llm_summary_schema["required"]
    assert "n_formal_attempt_queue_items" in llm_summary_schema["required"]
    assert "n_rows_with_formal_attempt_queue" in llm_summary_schema["required"]
    assert "n_accepted_with_formal_attempt_queue" in llm_summary_schema["required"]
    assert (
        "n_route_adoption_pending_formal_attempt_queue_blockers"
        in llm_summary_schema["required"]
    )
    assert (
        "n_requests_with_formal_attempt_feedback_summary"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_formal_attempt_feedback_contexts"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_formal_attempt_feedback_residual_goals"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_formal_attempt_feedback_failed_statuses"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_model_tier_decision_formal_attempt_feedback_contexts"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_model_tier_decision_formal_attempt_feedback_residual_goals"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_model_tier_decision_formal_attempt_feedback_failed_statuses"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_model_tier_decision_formal_attempt_feedback_sonnet_triggers"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_agentic_proof_execution_materializer_rows"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_agentic_proof_execution_artifact_verifier_rows"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_agentic_proof_source_theorem_promotion_rows"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_proof_execution_feedback_rows"
        in llm_summary_schema["required"]
    )
    assert (
        "n_request_proof_execution_unsupported_target_prover_rows"
        in llm_summary_schema["required"]
    )
    validation_summary_schema = publication_bundle_manifest_schema_payload[
        "properties"
    ]["llm_route_planner_response_payload_validation_summary"]
    assert (
        "n_request_bound_payloads_with_target_prover_family_mismatch"
        in validation_summary_schema["required"]
    )
    assert (
        "n_request_bound_payloads_with_route_adoption_preconditions"
        in validation_summary_schema["required"]
    )
    assert (
        "n_request_bound_payloads_with_route_adoption_status"
        in validation_summary_schema["required"]
    )
    assert (
        "n_request_bound_payloads_route_adoption_ready"
        in validation_summary_schema["required"]
    )
    assert (
        "n_request_bound_payloads_adoptable_for_standalone_replay"
        in validation_summary_schema["required"]
    )
    assert (
        "by_request_bound_payload_route_adoption_status"
        in validation_summary_schema["required"]
    )
    assert (
        "request_bound_payload_route_adoption_blocker_counts"
        in validation_summary_schema["required"]
    )
    assert (
        "n_request_bound_payloads_with_blocking_route_adoption_preconditions"
        in validation_summary_schema["required"]
    )
    assert "n_payloads_with_formal_attempt_queue" in validation_summary_schema[
        "required"
    ]
    assert "n_payload_formal_attempt_queue_items" in validation_summary_schema[
        "required"
    ]
    assert "n_payloads_with_formal_attempt_queue_errors" in validation_summary_schema[
        "required"
    ]
    assert "n_formal_attempt_queue_errors" in validation_summary_schema["required"]
    assert (
        "n_request_bound_payloads_with_agentic_proof_strategy_plan"
        in validation_summary_schema["required"]
    )
    assert (
        "n_agentic_proof_strategy_plan_obligation_errors"
        in validation_summary_schema["required"]
    )
    cross_prover_attempt_summary_schema = publication_bundle_manifest_schema_payload[
        "properties"
    ]["cross_prover_formal_attempt_dependency_summary"]
    assert (
        "n_total_packets_formal_attempt_waiting"
        in cross_prover_attempt_summary_schema["required"]
    )
    assert (
        "by_total_packet_formal_attempt_dependency_status"
        in cross_prover_attempt_summary_schema["required"]
    )
    assert "target_summary_consistent" in cross_prover_attempt_summary_schema[
        "required"
    ]
    assert "path" in publication_bundle_manifest_schema_payload["properties"][
        "core_artifacts"
    ]["items"]["required"]
    assert "requested" in publication_bundle_manifest_schema_payload["properties"][
        "optional_artifacts"
    ]["items"]["required"]
    assert "path" not in publication_bundle_manifest_schema_payload["properties"][
        "optional_artifacts"
    ]["items"]["required"]
    assert (
        out_dir / "contract" / "formalization_gap_planner_benchmark_route.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_evaluation_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_adapter_registry_row.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_standalone_input.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_target_intake.schema.json"
    ).exists()
    assert (
        out_dir / "contract" / "formalization_gap_planner_target_intake_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_component_resource_execution_plan.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_component_resource_resource_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_component_resource_component_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "contract"
        / "formalization_gap_planner_component_resource_contract_row.schema.json"
    ).exists()
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_component_resource_resource_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == component_resource_registry_resource_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_component_resource_component_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == component_resource_registry_component_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_component_resource_contract_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == component_resource_contract_row_json_schema()["$id"]
    target_intake_row_schema_payload = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_target_intake_row.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert target_intake_row_schema_payload["$id"] == target_intake_row_json_schema()["$id"]
    assert (
        target_intake_row_schema_payload["legacy_field_aliases"]
        == LEGACY_TARGET_INTAKE_FIELD_ALIASES
    )
    assert "formal_library_grounding_queries" in target_intake_row_schema_payload[
        "required"
    ]
    assert "lean_grounding_queries" not in target_intake_row_schema_payload["required"]
    portable_row_schema = json.loads(
        (
            out_dir
            / "contract"
            / "library_aware_formalization_gap_plan_row.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert portable_row_schema["$id"] == portable_gap_plan_row_json_schema()["$id"]
    assert "source_snippets" in portable_row_schema["$defs"]["plan_node"][
        "properties"
    ]
    assert "source_refs" in portable_row_schema["$defs"]["plan_node"][
        "properties"
    ]
    assert "source_snippets" in portable_row_schema["$defs"]["route_dag_node"][
        "properties"
    ]
    assert portable_row_schema["$defs"]["source_snippet"]["required"] == [
        "source_ref"
    ]
    assert "source_snippets" in portable_row_schema["properties"][
        "standalone_input_trace"
    ]["properties"]
    trace_schema_props = portable_row_schema["properties"]["standalone_input_trace"][
        "properties"
    ]
    assert trace_schema_props["source_prover_family"]["type"] == "string"
    assert trace_schema_props["source_target_prover_family"]["type"] == "string"
    assert trace_schema_props["target_prover_family"]["type"] == "string"
    assert trace_schema_props["target_library_snapshot_ref"]["type"] == "string"
    assert trace_schema_props["trace_target_projection"]["type"] == "string"
    assert trace_schema_props["llm_route_planner_fallback_route"]["type"] == (
        "boolean"
    )
    assert trace_schema_props["llm_route_planner_seed_route_source"]["type"] == (
        "string"
    )
    standalone_schema_payload = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_standalone_input.schema.json"
        ).read_text(encoding="utf-8")
    )
    standalone_props = standalone_schema_payload["properties"]
    standalone_route_props = standalone_schema_payload["$defs"]["route"]["properties"]
    standalone_replan_props = standalone_schema_payload["$defs"]["replan_metadata"][
        "properties"
    ]
    assert (
        standalone_props["llm_route_planner_seed_route_selection"]["$ref"]
        == "#/$defs/llm_route_planner_seed_route_selection"
    )
    assert standalone_route_props["llm_route_planner_seed_selected"]["type"] == "boolean"
    assert standalone_route_props["llm_route_planner_fallback_route"]["type"] == (
        "boolean"
    )
    assert standalone_replan_props["llm_route_planner_fallback_route"]["type"] == (
        "boolean"
    )
    assert (
        standalone_route_props["llm_route_planner_seed_selection_rank"]["minimum"]
        == 1
    )
    assert (
        standalone_replan_props["llm_route_planner_seed_selection_reason"]["minLength"]
        == 1
    )
    seed_route_selection_schema_payload = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_llm_route_planner_seed_route_selection.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        seed_route_selection_schema_payload["$id"]
        == FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID
    )
    assert (
        seed_route_selection_schema_payload
        == llm_route_planner_seed_route_selection_json_schema()
    )
    schema_catalog_schema_payload = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_schema_catalog.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert schema_catalog_schema_payload["$id"] == schema_catalog_json_schema()["$id"]
    schema_catalog_payload = json.loads(
        (
            out_dir / "contract" / "formalization_gap_planner_schema_catalog.json"
        ).read_text(encoding="utf-8")
    )
    assert schema_catalog_payload["component_name"] == "formalization_gap_planner_schema_catalog"
    assert schema_catalog_payload["all_ok"]
    assert schema_catalog_payload["n_missing_schema_ids"] == 0
    assert schema_catalog_payload["n_missing_schema_files"] == 0
    assert validate_schema_catalog_payload(schema_catalog_payload, bundle_dir=out_dir) == ()
    schema_catalog_entry_names = {
        row["artifact_name"] for row in schema_catalog_payload["schema_entries"]
    }
    schema_catalog_entries_by_name = {
        row["artifact_name"]: row for row in schema_catalog_payload["schema_entries"]
    }
    assert "portable_contract" in schema_catalog_entry_names
    assert "publication_bundle_manifest_schema" in schema_catalog_entry_names
    assert "portable_plan_row_schema" in schema_catalog_entry_names
    assert "target_intake_row_schema" in schema_catalog_entry_names
    assert "llm_route_planner_request_schema" in schema_catalog_entry_names
    assert (
        "llm_route_planner_library_alignment_summary_schema"
        in schema_catalog_entry_names
    )
    assert schema_catalog_entries_by_name[
        "llm_route_planner_library_alignment_summary_schema"
    ]["schema_id"] == LLM_ROUTE_PLANNER_LIBRARY_ALIGNMENT_SUMMARY_SCHEMA_ID
    assert "llm_route_planner_route_planning_brief_schema" in schema_catalog_entry_names
    assert schema_catalog_entries_by_name[
        "llm_route_planner_route_planning_brief_schema"
    ]["schema_id"] == LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID
    assert "llm_route_planner_response_schema" in schema_catalog_entry_names
    assert "llm_route_planner_response_payload_schema" in schema_catalog_entry_names
    assert (
        "llm_route_planner_response_payload_lean_legacy_schema"
        in schema_catalog_entry_names
    )
    assert (
        "llm_route_planner_response_payload_target_prover_schema"
        in schema_catalog_entry_names
    )
    assert schema_catalog_entries_by_name[
        "llm_route_planner_response_payload_lean_legacy_schema"
    ]["target_prover_families"] == ["lean4"]
    assert schema_catalog_entries_by_name[
        "llm_route_planner_response_payload_target_prover_schema"
    ]["target_prover_families"] == [
        target for target in PORTABLE_REUSE_TARGETS if target != "lean4"
    ]
    assert (
        "llm_route_planner_response_payload_validation_manifest_schema"
        in schema_catalog_entry_names
    )
    assert (
        "llm_route_planner_response_payload_validation_row_schema"
        in schema_catalog_entry_names
    )
    assert "llm_route_planner_manifest_schema" in schema_catalog_entry_names
    assert schema_catalog_entries_by_name["llm_route_planner_manifest_schema"][
        "schema_id"
    ] == LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID
    assert "llm_route_planner_row_schema" in schema_catalog_entry_names
    assert (
        "llm_route_planner_model_tier_decision_ledger_schema"
        in schema_catalog_entry_names
    )
    assert schema_catalog_entries_by_name[
        "llm_route_planner_model_tier_decision_ledger_schema"
    ]["schema_id"] == LLM_ROUTE_PLANNER_MODEL_TIER_DECISION_LEDGER_SCHEMA_ID
    assert (
        "llm_route_planner_provider_usage_row_schema"
        in schema_catalog_entry_names
    )
    assert schema_catalog_entries_by_name[
        "llm_route_planner_provider_usage_row_schema"
    ]["schema_id"] == LLM_ROUTE_PLANNER_PROVIDER_USAGE_ROW_SCHEMA_ID
    provider_usage_schema_payload = json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert provider_usage_schema_payload == (
        llm_route_planner_provider_usage_row_json_schema()
    )
    assert (
        "llm_route_planner_seed_route_selection_schema"
        in schema_catalog_entry_names
    )
    assert schema_catalog_entries_by_name[
        "llm_route_planner_seed_route_selection_schema"
    ]["schema_id"] == FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_SEED_ROUTE_SELECTION_SCHEMA_ID
    assert "route_adoption_blocker_taxonomy_schema" in schema_catalog_entry_names
    assert (
        "route_adoption_blocker_taxonomy_manifest_schema"
        in schema_catalog_entry_names
    )
    assert schema_catalog_entries_by_name[
        "route_adoption_blocker_taxonomy_manifest_schema"
    ]["schema_id"] == ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID
    assert "route_adoption_blocker_taxonomy_contract" in schema_catalog_entry_names
    assert "runtime_handoff_audit_row_schema" in schema_catalog_entry_names
    assert "runtime_handoff_execution_plan_schema" in schema_catalog_entry_names
    assert schema_catalog_entries_by_name[
        "runtime_handoff_execution_plan_schema"
    ]["schema_id"] == RUNTIME_HANDOFF_EXECUTION_PLAN_SCHEMA_ID
    assert all(
        (out_dir / row["relative_path"]).exists()
        for row in schema_catalog_payload["schema_entries"]
    )
    malformed_catalog = dict(schema_catalog_payload)
    malformed_catalog["n_schema_entries"] = 999
    malformed_catalog["schema_entries"] = [
        dict(schema_catalog_payload["schema_entries"][0], relative_path="../escape.json")
    ]
    malformed_errors = validate_schema_catalog_payload(
        malformed_catalog,
        bundle_dir=out_dir,
    )
    assert "n_schema_entries must equal number of schema_entries object rows" in (
        malformed_errors
    )
    assert any("relative_path escapes bundle" in error for error in malformed_errors)
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_benchmark_route.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == benchmark_route_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_evaluation_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == evaluation_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_adapter_registry_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == adapter_registry_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_prover_adapter_response.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == prover_adapter_response_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == prover_adapter_response_validation_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == cross_prover_matrix_audit_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_cross_prover_target_summary.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == cross_prover_target_summary_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_portable_plan_audit_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == portable_plan_audit_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_primitive_action_queue_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == primitive_action_queue_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_action_resource_plan_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == action_resource_plan_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_resource_request_queue_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == resource_request_queue_row_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_resource_response.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == resource_response_json_schema()["$id"]
    assert json.loads(
        (
            out_dir
            / "contract"
            / "formalization_gap_planner_resource_response_ledger_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == resource_response_ledger_row_json_schema()["$id"]
    contract_payload = json.loads(
        (out_dir / "contract" / "formalization_gap_planner_portable_contract.json").read_text(
            encoding="utf-8"
        )
    )
    route_contract = contract_payload["interactive_route_synthesis_contract"]
    assert "formal_library_coverage_mapping" in route_contract["loop"]
    assert "lean_coverage_mapping" not in route_contract["loop"]
    assert route_contract["legacy_stage_aliases"][
        "lean_coverage_mapping"
    ] == "formal_library_coverage_mapping"
    evaluation_protocol = contract_payload["evaluation_protocol"]
    assert "target_prover_effort_new_declarations" in evaluation_protocol[
        "primary_metrics"
    ]
    assert "target_prover_effort_failed_attempts" in evaluation_protocol[
        "primary_metrics"
    ]
    assert "lean_effort_new_declarations" not in evaluation_protocol[
        "primary_metrics"
    ]
    assert evaluation_protocol["legacy_metric_aliases"][
        "lean_effort_new_declarations"
    ] == "target_prover_effort_new_declarations"
    assert "no_formal_grounding" in evaluation_protocol["ablations"]
    assert "no_lean_rag" not in evaluation_protocol["ablations"]
    assert evaluation_protocol["legacy_ablation_aliases"]["no_lean_rag"] == (
        "no_formal_grounding"
    )
    assert "prover_adapter_packet_contract" in contract_payload
    assert "prover_adapter_response_validation_row_contract" in contract_payload
    assert "prover_adapter_response_contract" in contract_payload
    assert "cross_prover_matrix_audit_row_contract" in contract_payload
    assert "cross_prover_target_summary_contract" in contract_payload
    assert "refinement_work_item_contract" in contract_payload
    assert "refinement_tool_response_contract" in contract_payload
    assert "refinement_evidence_row_contract" in contract_payload
    assert "proof_state_triage_row_contract" in contract_payload
    assert "interactive_session_row_contract" in contract_payload
    assert "interactive_decision_policy_row_contract" in contract_payload
    assert "minimal_delta_decision_row_contract" in contract_payload
    assert "portable_plan_audit_row_contract" in contract_payload
    assert "library_coverage_map_row_contract" in contract_payload
    assert "primitive_action_queue_row_contract" in contract_payload
    assert "action_resource_plan_row_contract" in contract_payload
    assert "resource_request_queue_row_contract" in contract_payload
    assert "resource_response_contract" in contract_payload
    assert "resource_response_ledger_row_contract" in contract_payload
    assert "schema_catalog_contract" in contract_payload
    assert "source_grounding_row_contract" in contract_payload
    assert "llm_route_planner_request_contract" in contract_payload
    assert "llm_route_planner_response_contract" in contract_payload
    assert "llm_route_planner_response_payload_contract" in contract_payload
    assert "llm_route_planner_manifest_contract" in contract_payload
    assert (
        contract_payload["llm_route_planner_manifest_contract"]["$id"]
        == LLM_ROUTE_PLANNER_MANIFEST_SCHEMA_ID
    )
    assert "llm_route_planner_route_planning_brief_contract" in contract_payload
    assert (
        contract_payload["llm_route_planner_route_planning_brief_contract"]["$id"]
        == LLM_ROUTE_PLANNER_ROUTE_PLANNING_BRIEF_SCHEMA_ID
    )
    assert "route_adoption_blocker_taxonomy_manifest_schema_contract" in contract_payload
    assert (
        contract_payload[
            "route_adoption_blocker_taxonomy_manifest_schema_contract"
        ]["$id"]
        == ROUTE_ADOPTION_BLOCKER_TAXONOMY_MANIFEST_SCHEMA_ID
    )
    assert "llm_model_policy_contract" in contract_payload
    llm_model_policy = json.loads(
        (
            out_dir / "contract" / "ai_statistician_llm_model_policy.json"
        ).read_text(encoding="utf-8")
    )
    assert llm_model_policy["component_name"] == "ai_statistician_llm_model_policy"
    assert llm_model_policy["default_live_generator_provider"] == "anthropic"
    assert llm_model_policy["latest_claude_models_by_tier"] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-8",
    }
    assert (
        llm_model_policy["latest_claude_api_aliases_by_tier"]
        == DEFAULT_CLAUDE_GENERATOR_MODEL_ALIASES_BY_TIER
        == {
            "haiku": "claude-haiku-4-5",
            "sonnet": "claude-sonnet-4-6",
            "opus": "claude-opus-4-8",
        }
    )
    assert "Runtime calls use latest_claude_models_by_tier API IDs" in (
        llm_model_policy["runtime_model_id_policy"]
    )
    assert (
        llm_model_policy["source_checked_date"]
        == ANTHROPIC_MODEL_SOURCE_CHECKED_DATE
        == "2026-06-25"
    )
    assert llm_model_policy["source_evidence"] == ANTHROPIC_MODEL_SOURCE_EVIDENCE
    assert llm_model_policy["source_evidence"][
        "verified_latest_cost_tier_api_ids"
    ] == {
        "haiku": "claude-haiku-4-5-20251001",
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-8",
    }
    assert (
        "Claude 4.6+ dateless model IDs are pinned snapshots"
        in " ".join(llm_model_policy["source_evidence"]["claims"])
    )
    assert llm_model_policy["latest_claude_family_models_outside_cost_tiers"] == {
        "fable": "claude-fable-5",
        "mythos_limited_availability": "claude-mythos-5",
    }
    assert "not automatic AI Statistician cost tiers" in llm_model_policy[
        "outside_cost_tier_policy"
    ]
    request_time_policy = llm_model_policy["request_time_model_resolution_policy"]
    assert "request is built" in request_time_policy["empty_model_resolution"]
    assert (
        "Tier-specific Claude environment variables"
        in request_time_policy["tier_specific_env_overrides"]
    )
    assert request_time_policy["worker_default_tiers"] == {
        "TheoryIntake": "haiku",
        "SimulationEngineer": "haiku",
        "AlgorithmEngineer": "haiku",
        "CriticEvaluator": "haiku",
        "ArchitectCoordinator": "sonnet",
        "TheoryDeveloper": "sonnet",
        "FormalizerProofEngineer": "sonnet",
        "formalization_gap_planner_route_synthesis": "auto",
    }
    assert "codex" not in llm_model_policy["supported_live_generator_providers"]
    assert "codex_exec" not in llm_model_policy["supported_live_generator_providers"]
    assert set(llm_model_policy["prohibited_generator_providers"]) == set(
        PROHIBITED_AGENT_GENERATOR_PROVIDERS
    )
    assert (
        llm_model_policy["claude_tier_routing_contract"]["contract_name"]
        == "anthropic_claude_tier_routing_contract"
    )
    assert llm_model_policy["claude_tier_routing_contract"][
        "latest_claude_models_by_tier"
    ] == llm_model_policy["latest_claude_models_by_tier"]
    assert llm_model_policy["claude_tier_routing_contract"][
        "resolved_claude_model_tier_policy_status"
    ] == "OK"
    llm_model_policy_report = (
        out_dir / "contract" / "ai_statistician_llm_model_policy.md"
    )
    assert llm_model_policy_report.exists()
    assert "## Request-Time Resolution" in llm_model_policy_report.read_text(
        encoding="utf-8"
    )
    assert "Resolved tier policy status: `OK`; freshness status: `CURRENT`" in (
        llm_model_policy_report.read_text(encoding="utf-8")
    )
    assert (
        "llm_route_planner_response_payload_validation_manifest_contract"
        in contract_payload
    )
    assert (
        "llm_route_planner_response_payload_validation_row_contract"
        in contract_payload
    )
    assert "llm_route_planner_row_contract" in contract_payload
    assert "route_revision_overlay_row_contract" in contract_payload
    assert "route_stability_audit_row_contract" in contract_payload
    assert "route_replan_handoff_row_contract" in contract_payload
    assert "runtime_handoff_audit_row_contract" in contract_payload
    assert "runtime_handoff_execution_plan_contract" in contract_payload
    assert "route_alignment_edge_contract" in contract_payload
    assert "portable_gap_plan_row_contract" in contract_payload
    assert "benchmark_route_contract" in contract_payload
    assert "evaluation_row_contract" in contract_payload
    assert "adapter_registry_row_contract" in contract_payload
    assert "target_intake_contract" in contract_payload
    assert "target_intake_row_contract" in contract_payload
    assert "component_resource_execution_plan_contract" in contract_payload
    assert "component_resource_resource_row_contract" in contract_payload
    assert "component_resource_component_row_contract" in contract_payload
    assert "component_resource_contract_row_contract" in contract_payload
    assert (
        out_dir
        / "reproduce"
        / "formalization_gap_planner_reproduction_manifest.json"
    ).exists()
    reproduction_payload = json.loads(
        (
            out_dir
            / "reproduce"
            / "formalization_gap_planner_reproduction_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert reproduction_payload["component_name"] == "formalization_gap_planner_reproduction_manifest"
    assert reproduction_payload["n_commands"] >= 22
    command_by_name = {
        row["name"]: row["command"] for row in reproduction_payload["commands"]
    }
    assert any(
        row["entrypoint"] == "formalization-gap-planner-standalone-plan"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-llm-route-planner"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"]
        == "formalization-gap-planner-llm-route-planner-response-payload-validate"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"]
        == "formalization-gap-planner-route-adoption-blocker-taxonomy"
        for row in reproduction_payload["entrypoints"]
    )
    ablation_entrypoint = next(
        row
        for row in reproduction_payload["entrypoints"]
        if row["entrypoint"] == "formalization-gap-planner-ablation-study"
    )
    assert "no-formal-grounding" in ablation_entrypoint["purpose"]
    assert "no-Lean" not in ablation_entrypoint["purpose"]
    assert "run_llm_route_planner" in command_by_name
    assert (
        "formalization-gap-planner-llm-route-planner"
        in command_by_name["run_llm_route_planner"]
    )
    assert (
        "--formalization-gap-planner-component-resource-registry-dir"
        in command_by_name["run_llm_route_planner"]
    )
    assert (
        "--formalization-gap-planner-target-intake-dir"
        in command_by_name["run_llm_route_planner"]
    )
    assert "--model-tier auto" in command_by_name["run_llm_route_planner"]
    assert "--max-repair-attempts 1" in command_by_name["run_llm_route_planner"]
    assert (
        "<work_dir>/formalization_gap_planner_target_intake"
        in command_by_name["run_llm_route_planner"]
    )
    assert (
        "<bundle_dir>/component_resource_registry"
        in command_by_name["run_llm_route_planner"]
    )
    assert "validate_llm_route_payloads" in command_by_name
    assert (
        "formalization-gap-planner-llm-route-planner-response-payload-validate"
        in command_by_name["validate_llm_route_payloads"]
    )
    assert "--request-context" in command_by_name["validate_llm_route_payloads"]
    assert (
        "<work_dir>/formalization_gap_planner_llm_route_planner"
        in command_by_name["validate_llm_route_payloads"]
    )
    assert (
        "<reviewed_llm_route_payload_json>"
        in command_by_name["validate_llm_route_payloads"]
    )
    assert "run_feedback_llm_route_planner" in command_by_name
    assert (
        "formalization-gap-planner-llm-route-planner"
        in command_by_name["run_feedback_llm_route_planner"]
    )
    assert (
        "--formalization-gap-planner-interactive-session-dir"
        in command_by_name["run_feedback_llm_route_planner"]
    )
    assert (
        "--formalization-gap-planner-component-resource-registry-dir"
        in command_by_name["run_feedback_llm_route_planner"]
    )
    assert (
        "--formalization-gap-planner-target-intake-dir"
        in command_by_name["run_feedback_llm_route_planner"]
    )
    assert "--model-tier auto" in command_by_name["run_feedback_llm_route_planner"]
    assert "--max-repair-attempts 1" in command_by_name["run_feedback_llm_route_planner"]
    assert (
        "<work_dir>/formalization_gap_planner_target_intake"
        in command_by_name["run_feedback_llm_route_planner"]
    )
    assert (
        "<bundle_dir>/component_resource_registry"
        in command_by_name["run_feedback_llm_route_planner"]
    )
    assert (
        "formalization_gap_planner_route_replan_handoff/"
        in command_by_name["run_feedback_llm_route_planner"]
    )
    assert "validate_feedback_llm_route_payloads" in command_by_name
    assert (
        "formalization-gap-planner-llm-route-planner-response-payload-validate"
        in command_by_name["validate_feedback_llm_route_payloads"]
    )
    assert (
        "--request-context"
        in command_by_name["validate_feedback_llm_route_payloads"]
    )
    assert (
        "<work_dir>/formalization_gap_planner_feedback_llm_route_planner"
        in command_by_name["validate_feedback_llm_route_payloads"]
    )
    assert (
        "<reviewed_feedback_llm_route_payload_json>"
        in command_by_name["validate_feedback_llm_route_payloads"]
    )
    assert (
        "formalization_gap_planner_llm_route_planner_standalone_seed.json"
        in command_by_name["run_standalone_planner"]
    )
    assert "export_route_adoption_blocker_taxonomy" in command_by_name
    assert (
        "formalization-gap-planner-route-adoption-blocker-taxonomy"
        in command_by_name["export_route_adoption_blocker_taxonomy"]
    )
    assert (
        "formalization_gap_planner_route_adoption_blocker_taxonomy"
        in command_by_name["export_route_adoption_blocker_taxonomy"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-reuse-smoke"
        for row in reproduction_payload["entrypoints"]
    )
    assert "run_reuse_smoke" in command_by_name
    assert (
        "formalization-gap-planner-reuse-smoke"
        in command_by_name["run_reuse_smoke"]
    )
    assert (
        "examples/formalization_gap_planner_target_intake_example.json"
        in command_by_name["run_reuse_smoke"]
    )
    assert "--llm-route-planner-provider anthropic" in command_by_name["run_reuse_smoke"]
    assert "--feedback-llm-route-planner-provider anthropic" in command_by_name["run_reuse_smoke"]
    assert "--llm-route-planner-invoke-provider" not in command_by_name["run_reuse_smoke"]
    assert "--feedback-llm-route-planner-invoke-provider" not in command_by_name["run_reuse_smoke"]
    assert "run_runtime_handoff_reuse_smoke" in command_by_name
    assert (
        "runtime_formalization_gap_planner_target_intake"
        in command_by_name["run_runtime_handoff_reuse_smoke"]
    )
    assert (
        "formalization-gap-planner-reuse-smoke"
        in command_by_name["run_runtime_handoff_reuse_smoke"]
    )
    assert (
        "--feedback-llm-route-planner-invoke-provider"
        not in command_by_name["run_runtime_handoff_reuse_smoke"]
    )
    assert (
        "artifacts/formalization_gap_planner_feedback_llm_route_planner/formalization_gap_planner_llm_route_planner_manifest.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-benchmark-audit"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-evaluation"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-primitive-action-queue"
        for row in reproduction_payload["entrypoints"]
    )
    assert "export_primitive_action_queue" in command_by_name
    assert (
        "formalization-gap-planner-primitive-action-queue"
        in command_by_name["export_primitive_action_queue"]
    )
    assert "export_action_resource_plan" in command_by_name
    assert (
        "formalization-gap-planner-action-resource-plan"
        in command_by_name["export_action_resource_plan"]
    )
    assert "export_resource_request_queue" in command_by_name
    assert (
        "formalization-gap-planner-resource-request-queue"
        in command_by_name["export_resource_request_queue"]
    )
    assert "export_resource_response_ledger" in command_by_name
    assert (
        "formalization-gap-planner-resource-response-ledger"
        in command_by_name["export_resource_response_ledger"]
    )
    assert "run_evaluation" in command_by_name
    assert (
        "formalization-gap-planner-evaluation"
        in command_by_name["run_evaluation"]
    )
    assert (
        "<bundle_dir>/artifacts/formalization_gap_planner_evaluation/"
        "formalization_gap_planner_evaluation_ground_truth.json"
        in command_by_name["run_evaluation"]
    )
    assert "run_route_revision_overlay" in command_by_name
    assert (
        "--formalization-gap-planner-resource-response-ledger-dir"
        in command_by_name["run_route_revision_overlay"]
    )
    assert (
        "formalization_gap_planner_resource_response_ledger"
        in command_by_name["run_route_revision_overlay"]
    )
    route_overlay_entrypoint = next(
        row
        for row in reproduction_payload["entrypoints"]
        if row["entrypoint"] == "formalization-gap-planner-route-revision-overlay"
    )
    assert "resource-response ledger" in route_overlay_entrypoint["purpose"]
    assert "resource-response ledger" in route_overlay_entrypoint["required_input"]
    assert (
        "formalization-gap-planner-resource-request-queue"
        in {
            row["entrypoint"]
            for row in reproduction_payload["entrypoints"]
        }
    )
    assert (
        "formalization-gap-planner-resource-response-ledger"
        in {
            row["entrypoint"]
            for row in reproduction_payload["entrypoints"]
        }
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-action-resource-plan"
        for row in reproduction_payload["entrypoints"]
    )
    assert (
        "contract/formalization_gap_planner_prover_adapter_packet.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/ai_statistician_llm_model_policy.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/ai_statistician_llm_model_policy.md"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_target_intake_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_manifest.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/library_aware_formalization_gap_plan_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_schema_catalog.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_schema_catalog.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_publication_bundle_manifest.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_portable_plan_audit_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_library_coverage_map_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_primitive_action_queue_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_action_resource_plan_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_resource_request_queue_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_resource_response.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_resource_response_ledger_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_cross_prover_target_summary.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_source_grounding_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_request.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_library_alignment_summary.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_response.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_provider_usage_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_seed_route_selection.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_route_adoption_blocker_taxonomy.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_route_adoption_blocker_taxonomy_manifest.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_route_adoption_blocker_taxonomy.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_interactive_decision_policy_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_refinement_evidence_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_route_stability_audit_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_runtime_handoff_audit_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_ablation_study_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_proof_state_triage_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_benchmark_route.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_evaluation_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "artifacts/formalization_gap_planner_evaluation/"
        "formalization_gap_planner_evaluation_ground_truth.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_adapter_registry_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "benchmark/formalization_gap_planner_benchmark_routes.jsonl"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "benchmark/formalization_gap_planner_benchmark_route.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "adapter_registry/formalization_gap_planner_adapter_registry.jsonl"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "adapter_registry/formalization_gap_planner_adapter_registry_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_component_resource_resource_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_component_resource_component_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "contract/formalization_gap_planner_component_resource_contract_row.schema.json"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert (
        "component_resource_registry/formalization_gap_planner_component_resource_resources.jsonl"
        in reproduction_payload["bundle_relative_artifacts"]
    )
    assert any(
        row["entrypoint"]
        == "formalization-gap-planner-component-resource-registry-audit"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-refinement-queue"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-local-literature-adapter"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"]
        == "formalization-gap-planner-minimal-delta-audit-feedback"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-local-formal-source-adapter"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-local-proof-state-adapter"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-prover-adapter-feedback"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-route-replan-handoff"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-route-replan-handoff-audit"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-runtime-handoff-audit"
        for row in reproduction_payload["entrypoints"]
    )
    assert any(
        row["entrypoint"] == "formalization-gap-planner-proof-state-triage"
        for row in reproduction_payload["entrypoints"]
    )
    assert "formalization-gap-planner-refinement-queue" in command_by_name[
        "run_refinement_queue"
    ]
    assert "formalization-gap-planner-local-literature-adapter" in command_by_name[
        "run_local_literature_adapter"
    ]
    assert "formalization-gap-planner-local-formal-source-adapter" in command_by_name[
        "run_local_formal_source_adapter"
    ]
    assert "formalization-gap-planner-local-proof-state-adapter" in command_by_name[
        "run_local_proof_state_adapter"
    ]
    assert "formalization-gap-planner-prover-adapter-feedback" in command_by_name[
        "run_prover_adapter_feedback"
    ]
    assert "formalization-gap-planner-minimal-delta-audit" in command_by_name[
        "run_minimal_delta_audit"
    ]
    assert "formalization-gap-planner-minimal-delta-audit-feedback" in command_by_name[
        "run_minimal_delta_audit_feedback"
    ]
    assert "formalization_gap_planner_minimal_delta_audit_feedback_adapter/" in command_by_name[
        "run_local_literature_adapter"
    ]
    assert "formalization_gap_planner_local_proof_state_adapter/" in command_by_name[
        "run_prover_adapter_feedback"
    ]
    assert "formalization_gap_planner_prover_adapter_feedback_adapter/" in command_by_name[
        "run_refinement_evidence"
    ]
    assert "formalization-gap-planner-route-replan-handoff" in command_by_name[
        "run_route_replan_handoff"
    ]
    assert "formalization-gap-planner-route-replan-handoff-audit" in command_by_name[
        "audit_route_replan_handoff"
    ]
    assert "formalization-gap-planner-runtime-handoff-audit" in command_by_name[
        "audit_runtime_handoff"
    ]
    assert "formalization-gap-planner-proof-state-triage" in command_by_name[
        "run_proof_state_triage"
    ]
    assert (
        out_dir / "examples" / "formalization_gap_planner_standalone_example.json"
    ).exists()
    assert (
        out_dir / "examples" / "formalization_gap_planner_target_intake_example.json"
    ).exists()
    assert payload["example_target_prover_families"] == ("lean4", "rocq")
    assert payload["n_example_target_prover_families"] == 2
    assert payload["has_non_lean_example_input"] is True
    copied_example_by_name = {
        str(row["example_name"]): row for row in payload["copied_examples"]
    }
    assert copied_example_by_name["standalone_input_example"][
        "target_prover_family"
    ] == "rocq"
    assert copied_example_by_name["target_intake_example"][
        "target_prover_family"
    ] == "lean4"
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_evaluation"
        / "formalization_gap_planner_evaluation_ground_truth.json"
    ).exists()
    assert (
        out_dir / "reproduce" / "formalization_gap_planner_reproduction.md"
    ).exists()
    assert (
        out_dir / "benchmark" / "formalization_gap_planner_benchmark_manifest.json"
    ).exists()
    assert (
        out_dir
        / "benchmark_audit"
        / "formalization_gap_planner_benchmark_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_primitive_action_queue"
        / "formalization_gap_planner_primitive_action_queue_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_primitive_action_queue"
        / "formalization_gap_planner_primitive_action_queue_row.schema.json"
    ).exists()
    assert (
        out_dir / "adapter_registry" / "formalization_gap_planner_adapter_registry_manifest.json"
    ).exists()
    assert (
        out_dir / "adapter_registry" / "formalization_gap_planner_adapter_registry.jsonl"
    ).exists()
    assert (
        out_dir
        / "adapter_registry"
        / "formalization_gap_planner_adapter_registry_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_registry_manifest.json"
    ).exists()
    assert (
        out_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_execution_plans.jsonl"
    ).exists()
    assert (
        out_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_registry.jsonl"
    ).exists()
    assert (
        out_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_resources.jsonl"
    ).exists()
    assert (
        out_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_contracts.jsonl"
    ).exists()
    assert (
        out_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_component_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_resource_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_execution_plan.schema.json"
    ).exists()
    assert (
        out_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_contract_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_target_intake"
        / "formalization_gap_planner_target_intake_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_target_intake"
        / "formalization_gap_planner_target_intake_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "goal_conditioned_minimal_formalization_plan"
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "goal_conditioned_minimal_formalization_plan"
        / "library_aware_formalization_gap_plan_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_portable_plan_audit"
        / "formalization_gap_planner_portable_plan_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_portable_plan_audit"
        / "formalization_gap_planner_portable_plan_audit_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_minimal_delta_audit"
        / "formalization_gap_planner_minimal_delta_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_source_grounding_audit"
        / "formalization_gap_planner_source_grounding_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_refinement_queue"
        / "formalization_gap_planner_refinement_queue_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_refinement_adapter"
        / "formalization_gap_planner_refinement_adapter_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_refinement_adapter"
        / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_local_literature_adapter"
        / "formalization_gap_planner_local_literature_adapter_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_local_literature_adapter"
        / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_local_formal_source_adapter"
        / "formalization_gap_planner_local_formal_source_adapter_manifest.json"
    ).exists()
    copied_local_formal_source_manifest = json.loads(
        (
            out_dir
            / "artifacts"
            / "formalization_gap_planner_local_formal_source_adapter"
            / "formalization_gap_planner_local_formal_source_adapter_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        copied_local_formal_source_manifest[
            "legacy_formal_source_adapter_field_aliases"
        ]
        == LEGACY_FORMAL_SOURCE_ADAPTER_FIELD_ALIASES
    )
    assert (
        copied_local_formal_source_manifest[
            "n_responses_with_legacy_lean_declaration_hits"
        ]
        == 0
    )
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_local_formal_source_adapter"
        / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_local_proof_state_adapter"
        / "formalization_gap_planner_local_proof_state_adapter_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_local_proof_state_adapter"
        / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_refinement_evidence"
        / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_refinement_evidence"
        / "formalization_gap_planner_refinement_evidence_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_route_revision_overlay"
        / "formalization_gap_planner_route_revision_overlay_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_ablation_study"
        / "formalization_gap_planner_ablation_study_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_ablation_study"
        / "formalization_gap_planner_ablation_study_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_route_stability_audit"
        / "formalization_gap_planner_route_stability_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_route_stability_audit"
        / "formalization_gap_planner_route_stability_audit_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_route_replan_handoff"
        / "formalization_gap_planner_route_replan_handoff_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_route_replan_handoff"
        / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_route_replan_handoff_audit"
        / "formalization_gap_planner_route_replan_handoff_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_route_replan_handoff_audit"
        / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_runtime_handoff_audit"
        / "formalization_gap_planner_runtime_handoff_audit_manifest.json"
    ).exists()
    packaged_runtime_handoff_audit = json.loads(
        (
            out_dir
            / "artifacts"
            / "formalization_gap_planner_runtime_handoff_audit"
            / "formalization_gap_planner_runtime_handoff_audit_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert packaged_runtime_handoff_audit[
        "n_component_resource_registry_smoke_ok"
    ] == 1
    assert packaged_runtime_handoff_audit[
        "n_component_resource_registry_components_in_prompt"
    ] > 0
    assert packaged_runtime_handoff_audit[
        "n_component_resource_registry_resources_in_prompt"
    ] > 0
    assert packaged_runtime_handoff_audit[
        "n_component_resource_registry_contracts_in_prompt"
    ] > 0
    assert packaged_runtime_handoff_audit["n_execution_plan_rows"] == 1
    assert packaged_runtime_handoff_audit["n_execution_plan_row_schema_valid"] == 1
    assert packaged_runtime_handoff_audit["n_execution_plan_row_schema_invalid"] == 0
    assert packaged_runtime_handoff_audit["n_llm_prompt_model_tier_sonnet"] == 1
    assert (
        packaged_runtime_handoff_audit["n_llm_prompt_model_tier_haiku"]
        + packaged_runtime_handoff_audit["n_llm_prompt_model_tier_sonnet"]
        + packaged_runtime_handoff_audit["n_llm_prompt_model_tier_opus"]
        == packaged_runtime_handoff_audit["n_llm_prompt_packets"]
    )
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_runtime_handoff_audit"
        / "formalization_gap_planner_runtime_handoff_audit_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_runtime_handoff_audit"
        / "formalization_gap_planner_runtime_handoff_execution_plans.jsonl"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_runtime_handoff_audit"
        / "formalization_gap_planner_runtime_handoff_execution_plan.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_proof_state_triage"
        / "formalization_gap_planner_proof_state_triage_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_proof_state_triage"
        / "formalization_gap_planner_proof_state_triage_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_interactive_session"
        / "formalization_gap_planner_interactive_session_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_prover_adapter_contract"
        / "formalization_gap_planner_prover_adapter_contract_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_prover_adapter_contract"
        / "formalization_gap_planner_prover_adapter_packet.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_prover_adapter_contract"
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_cross_prover_matrix_audit"
        / "formalization_gap_planner_cross_prover_matrix_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_cross_prover_matrix_audit"
        / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_cross_prover_matrix_audit"
        / "formalization_gap_planner_cross_prover_target_summary.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_cross_prover_matrix_audit"
        / "formalization_gap_planner_cross_prover_target_summary.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_cross_prover_matrix_audit"
        / "formalization_gap_planner_prover_adapter_packet.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_cross_prover_matrix_audit"
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_adapter_registry_audit"
        / "formalization_gap_planner_adapter_registry_audit_manifest.json"
    ).exists()
    assert (
        out_dir
        / "artifacts"
        / "formalization_gap_planner_component_resource_registry_audit"
        / "formalization_gap_planner_component_resource_registry_audit_manifest.json"
    ).exists()


def test_publication_bundle_audit_accepts_rocq_serapi_dispatch_surface() -> None:
    dispatch_spec = {
        "adapter_surface": "rocq_serapi",
        "dispatch_kind": "frontier_mcp_or_cli",
        "execution_command": "dispatch rocq proof-state request through rocq_lsp_serapi",
        "expected_response_artifact": "proof_state_or_prover_feedback_response",
        "mcp_or_cli_hint": "Rocq SerAPI/LSP adapter",
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY_RESOURCE_REQUEST,
        "request_phase": "frontier_escalation",
        "resource_id": "rocq_lsp_serapi",
        "response_jsonl_contract": "formalization_gap_planner_resource_responses.jsonl",
        "target_prover_family": "rocq",
    }
    row = {
        "dispatch_spec": dispatch_spec,
        "execution_command": dispatch_spec["execution_command"],
        "expected_response_artifact": dispatch_spec["expected_response_artifact"],
        "mcp_or_cli_hint": dispatch_spec["mcp_or_cli_hint"],
        "request_payload": {"dispatch_spec": dispatch_spec},
        "request_phase": dispatch_spec["request_phase"],
        "resource_id": dispatch_spec["resource_id"],
        "target_prover_family": dispatch_spec["target_prover_family"],
    }

    assert _resource_request_dispatch_spec_errors(row) == ()

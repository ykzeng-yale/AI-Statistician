from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_ablation_study import (
    ablation_study_row_json_schema,
)
from ai_statistician.formalization_gap_planner_adapter_registry import (
    adapter_registry_row_json_schema,
)
from ai_statistician.formalization_gap_planner_contract import (
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
    portable_gap_plan_row_json_schema,
)
from ai_statistician.formalization_gap_planner_evaluation import (
    evaluation_row_json_schema,
)
from ai_statistician.formalization_gap_planner_library_coverage_map import (
    PROOF_EVIDENCE_STATUS as LIBRARY_COVERAGE_MAP_PROOF_EVIDENCE_STATUS,
    export_formalization_gap_planner_library_coverage_map,
    library_coverage_map_row_json_schema,
)
from ai_statistician.formalization_gap_planner_llm_route_planner import (
    PROOF_EVIDENCE_BOUNDARY as LLM_ROUTE_PLANNER_PROOF_EVIDENCE_BOUNDARY,
    export_formalization_gap_planner_llm_route_planner,
    validate_formalization_gap_planner_llm_route_planner_response_payloads,
)
from ai_statistician.formalization_gap_planner_primitive_action_queue import (
    PROOF_EVIDENCE_STATUS as PRIMITIVE_ACTION_QUEUE_PROOF_EVIDENCE_STATUS,
    export_formalization_gap_planner_primitive_action_queue,
    primitive_action_queue_row_json_schema,
)
from ai_statistician.formalization_gap_planner_action_resource_plan import (
    PROOF_EVIDENCE_STATUS as ACTION_RESOURCE_PLAN_PROOF_EVIDENCE_STATUS,
    action_resource_plan_row_json_schema,
    export_formalization_gap_planner_action_resource_plan,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    export_formalization_gap_planner_component_resource_registry,
)
from ai_statistician.formalization_gap_planner_resource_request_queue import (
    export_formalization_gap_planner_resource_request_queue,
    resource_request_queue_row_json_schema,
)
from ai_statistician.formalization_gap_planner_resource_response_ledger import (
    export_formalization_gap_planner_resource_response_ledger,
    resource_response_json_schema,
    resource_response_ledger_row_json_schema,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
    standalone_input_json_schema,
)
from ai_statistician.formalization_gap_planner_target_intake import (
    target_intake_row_json_schema,
    normalize_formalization_gap_planner_target_intake,
)
from ai_statistician.formalization_gap_planner_minimal_delta_audit import (
    minimal_delta_decision_row_json_schema,
)
from ai_statistician.formalization_gap_planner_publication_bundle import (
    FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID,
    export_formalization_gap_planner_publication_bundle,
    publication_bundle_manifest_json_schema,
    schema_catalog_json_schema,
)
from ai_statistician.formalization_gap_planner_publication_bundle_audit import (
    _handoff_seed_provenance_observed,
    _handoff_seed_provenance_ok,
    _runtime_handoff_audit_optional_checks,
    audit_formalization_gap_planner_publication_bundle,
)
from ai_statistician.formalization_gap_planner_runtime_handoff_audit import (
    runtime_handoff_audit_row_json_schema,
)
from ai_statistician.formalization_gap_planner_portable_plan_audit import (
    portable_plan_audit_row_json_schema,
)
from ai_statistician.formalization_gap_planner_prover_adapter_contract import (
    prover_adapter_packet_json_schema,
    prover_adapter_response_validation_row_json_schema,
)
from ai_statistician.formalization_gap_planner_cross_prover_matrix_audit import (
    CROSS_PROVER_TARGET_SUMMARY_SCHEMA_ID,
    cross_prover_matrix_audit_row_json_schema,
    cross_prover_target_summary_json_schema,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    refinement_tool_response_json_schema,
)
from ai_statistician.formalization_gap_planner_refinement_queue import (
    refinement_work_item_json_schema,
)
from ai_statistician.formalization_gap_planner_route_replan_handoff import (
    route_replan_handoff_row_json_schema,
)
from ai_statistician.formalization_gap_planner_route_revision_overlay import (
    export_formalization_gap_planner_route_revision_overlay,
    route_revision_overlay_row_json_schema,
)
from ai_statistician.formalization_gap_planner_route_stability_audit import (
    audit_formalization_gap_planner_route_stability,
    route_stability_audit_row_json_schema,
)
from ai_statistician.formalization_gap_planner_route_replan_handoff_audit import (
    route_replan_handoff_audit_row_json_schema,
)
from ai_statistician.formalization_gap_planner_source_grounding_audit import (
    source_grounding_row_json_schema,
)
from ai_statistician.formalization_gap_planner_interactive_session import (
    export_formalization_gap_planner_interactive_session,
    interactive_decision_policy_row_json_schema,
    interactive_session_row_json_schema,
)
from ai_statistician.formalization_gap_planner_proof_state_triage import (
    proof_state_triage_row_json_schema,
)


def test_handoff_seed_provenance_rejects_non_lean_legacy_declaration_alias() -> None:
    row = {
        "standalone_route_id": "replan_route:rocq_rank",
        "standalone_route": {
            "target_prover_family": "rocq",
            "replan_metadata": {"target_prover_family": "rocq"},
        },
        "formal_declaration_hits": [
            {
                "primitive": "rank_bridge",
                "declaration": "Rocq.Conformal.rank_bridge",
                "target_prover_family": "rocq",
            }
        ],
    }
    seed = {
        "routes": [
            {
                "route_id": "replan_route:rocq_rank",
                "target_prover_family": "rocq",
                "replan_metadata": {
                    "target_prover_family": "rocq",
                    "formal_declaration_hits": [
                        {
                            "primitive": "rank_bridge",
                            "declaration": "Rocq.Conformal.rank_bridge",
                            "target_prover_family": "rocq",
                        }
                    ],
                },
            }
        ]
    }

    assert _handoff_seed_provenance_ok([row], seed)
    observed = _handoff_seed_provenance_observed([row], seed)
    assert "non_lean_legacy_lean_declaration_hits=0" in observed

    bad_seed = json.loads(json.dumps(seed))
    bad_seed["routes"][0]["replan_metadata"]["lean_declaration_hits"] = [
        {
            "primitive": "rank_bridge",
            "declaration": "Rocq.Conformal.rank_bridge",
            "target_prover_family": "rocq",
        }
    ]

    assert not _handoff_seed_provenance_ok([row], bad_seed)
    bad_observed = _handoff_seed_provenance_observed([row], bad_seed)
    assert "non_lean_legacy_lean_declaration_hits=1" in bad_observed


def test_publication_bundle_audit_checks_runtime_handoff_registry_context() -> None:
    root = Path("runs/test_publication_bundle_audit_runtime_handoff_registry")
    shutil.rmtree(root, ignore_errors=True)
    artifact_dir = (
        root
        / "bundle"
        / "artifacts"
        / "formalization_gap_planner_runtime_handoff_audit"
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "schema_version": 1,
        "check_id": "runtime_handoff_audit:registry_context",
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
    (artifact_dir / "formalization_gap_planner_runtime_handoff_audit_manifest.json").write_text(
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
                "n_standalone_smoke_ok": 1,
                "n_llm_prompt_smoke_ok": 1,
                "n_llm_prompt_packets": 1,
                "n_component_resource_registry_smoke_ok": 1,
                "n_component_resource_registry_components_in_prompt": 2,
                "n_component_resource_registry_resources_in_prompt": 3,
                "n_component_resource_registry_contracts_in_prompt": 3,
                "all_ok": True,
                "checks": [row],
                "proof_evidence_status": (
                    "FORMALIZATION_GAP_PLANNER_RUNTIME_HANDOFF_AUDIT_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": "not theorem proof evidence",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (artifact_dir / "formalization_gap_planner_runtime_handoff_audit.jsonl").write_text(
        json.dumps(row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        artifact_dir
        / "formalization_gap_planner_runtime_handoff_audit_row.schema.json"
    ).write_text(
        json.dumps(runtime_handoff_audit_row_json_schema(), indent=2),
        encoding="utf-8",
    )

    checks = _runtime_handoff_audit_optional_checks(root / "bundle")
    by_name = {check.check_name: check for check in checks}

    assert by_name["optional_runtime_handoff_audit_cost_control"].ok
    assert by_name["optional_runtime_handoff_audit_prompt_smoke"].ok
    assert by_name[
        "optional_runtime_handoff_audit_component_resource_registry_smoke"
    ].ok
    assert by_name[
        "optional_runtime_handoff_audit_registry_context_in_prompt"
    ].ok
    assert by_name["optional_runtime_handoff_audit_row_0_schema_valid"].ok


def _fixture_prover_adapter_packet() -> dict[str, object]:
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
            "applied_hook_kinds": ["resource_response_ledger"],
            "quality_controls": {
                "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
                "required_quality_signals": ["diagnostic_signature"],
                "response_validation_signals": [
                    "residual_goals_or_diagnostics_present"
                ],
                "stop_conditions": [
                    "residual interpreted or source search requested"
                ],
            },
            "has_quality_controls": True,
            "quality_control_fields": [
                "required_quality_signals",
                "resource_contract_ids",
                "response_validation_signals",
                "stop_conditions",
            ],
        },
        "llm_route_planner_route_adoption_status": (
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
        ),
        "llm_route_planner_route_adoption_blockers": [
            "search_requests_pending_evidence",
            "uncertainty_flags_require_review",
        ],
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
        "kernel_verified_claimed": False,
        "acceptance_status": "AWAITING_PROVER_ADAPTER_MAPPING",
        "proof_evidence_status": "AWAITING_RESPONSE_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }


def _write_accepted_llm_route_planner_artifact(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    target_intake_dir = root / "target_intake"
    raw_target_json = root / "target_intake_request.json"
    raw_target_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_snapshot",
                "target_id": "rank_route",
                "title": "distribution_free_rank_bound",
                "theorem_statement": (
                    "A source-backed rank-uniformity bridge closes the "
                    "distribution-free rank route."
                ),
                "known_proof_sources": ["fixture_source"],
                "candidate_primitives": [
                    {
                        "primitive": "rank_uniformity",
                        "coverage_status": "bridge_needed",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    normalize_formalization_gap_planner_target_intake(
        raw_target_json,
        target_intake_dir,
    )
    input_json = (
        target_intake_dir
        / "formalization_gap_planner_target_intake_standalone_seed.json"
    )
    response_json = root / "llm_response.json"
    response_json.write_text(
        json.dumps(
            {
                "informal_knowledge_dag_nodes": [
                    {
                        "node_id": "informal:rank_uniformity",
                        "claim": "Exchangeability gives a uniform finite rank.",
                        "depends_on": [],
                        "source_refs": ["fixture_source"],
                        "source_search_status": "SOURCE_BACKED",
                        "semantic_role": "lemma",
                    }
                ],
                "lean_realization_dag_nodes": [
                    {
                        "node_id": "formal:rank_uniformity_bridge",
                        "primitive": "rank_uniformity",
                        "coverage_bucket": "bridge",
                        "candidate_declarations": [],
                        "formalization_action": "prove_bridge",
                    }
                ],
                "route_alignment_edges": [
                    {
                        "informal_node_id": "informal:rank_uniformity",
                        "formal_node_id": "formal:rank_uniformity_bridge",
                        "alignment_status": "bridge_needed",
                        "alignment_rationale": (
                            "The source-backed finite-rank statement should be "
                            "realized by one bridge lemma."
                        ),
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
                            "cost_rationale": "The reviewed route adds one focused bridge lemma.",
                        }
                    ],
                    "new_definitions": [],
                    "wrapper_lemmas": [],
                    "bridge_lemmas": ["rank_uniformity"],
                    "source_port_lemmas": [],
                    "do_not_formalize_now": ["full conformal prediction pipeline"],
                    "and_or_cost_graph": {
                        "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                        "selected_route_option_id": "route_option:rank_bridge",
                        "route_options": [
                            {
                                "route_option_id": "route_option:rank_bridge",
                                "selected": True,
                                "selected_primitives": ["rank_uniformity"],
                                "route_cost": 4,
                                "cost_rationale": "One focused bridge lemma is cheapest.",
                            },
                            {
                                "route_option_id": "route_option:rank_source_port",
                                "selected": False,
                                "selected_primitives": ["rank_uniformity"],
                                "route_cost": 7,
                                "cost_rationale": "A source port is broader than this route.",
                            },
                            {
                                "route_option_id": (
                                    "route_option:current_route_min_delta_baseline"
                                ),
                                "selected": False,
                                "selected_primitives": [
                                    (
                                        "a_source_backed_rank_uniformity_bridge_"
                                        "closes_the"
                                    ),
                                    "rank_uniformity",
                                    "uniform_bound",
                                ],
                                "route_cost": 44,
                                "cost_rationale": (
                                    "Request-bound baseline preserving all cost hints "
                                    "before the LLM route omits any primitive."
                                ),
                            },
                        ],
                        "or_nodes": [
                            {
                                "node_id": "or:rank_uniformity_realization",
                                "choices": [
                                    "route_option:rank_bridge",
                                    "route_option:rank_source_port",
                                    "route_option:current_route_min_delta_baseline",
                                ],
                                "selection_rationale": "The bridge route has lower route cost.",
                            }
                        ],
                        "and_edges": [
                            {
                                "route_option_id": "route_option:rank_bridge",
                                "requires": ["rank_uniformity"],
                            }
                        ],
                    },
                    "minimality_rationale": (
                        "Add the rank-uniformity bridge only; all broader "
                        "conformal prediction machinery is outside this route."
                    ),
                },
                "residual_interpretations": [],
                "search_requests": [
                    {
                        "request_kind": "literature",
                        "query": "rank_uniformity finite rank exchangeability",
                        "reason": (
                            "Confirm the source-backed rank-uniformity bridge "
                            "before route adoption."
                        ),
                        "target_primitives": ["rank_uniformity"],
                    }
                ],
                "uncertainty_flags": [],
                "semantic_alignment_risks": [],
                "planner_next_actions": [],
                "standalone_route": {
                    "route_id": "rank_route_llm_revision",
                    "display_name": "distribution_free_rank_bound_llm_revision",
                    "theorem_statement": (
                        "A source-backed rank-uniformity bridge closes the "
                        "distribution-free rank route."
                    ),
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
    out_dir = root / "llm_route_planner"
    component_resource_registry_dir = root / "component_resource_registry"
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir
    )
    payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        out_dir,
        provider_name="static",
        invoke_provider=True,
        static_response_json=response_json,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
        formalization_gap_planner_component_resource_registry_dir=(
            component_resource_registry_dir
        ),
    )
    assert payload["all_ok"]
    assert payload["n_accepted_route_plans"] == 1
    assert payload["n_rows_with_generator_metadata"] == 1
    return out_dir


def _write_llm_payload_validation_from_route_planner_artifact(
    llm_route_planner_dir: Path,
    root: Path,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    response_json = root / "response_payloads.json"
    raw_response_json = llm_route_planner_dir.parent / "llm_response.json"
    response_json.write_text(
        json.dumps(
            {"responses": [json.loads(raw_response_json.read_text(encoding="utf-8"))]},
            indent=2,
        ),
        encoding="utf-8",
    )
    out_dir = root / "payload_validation"
    payload = validate_formalization_gap_planner_llm_route_planner_response_payloads(
        response_json,
        out_dir,
        request_context_json=llm_route_planner_dir,
    )
    assert payload["all_ok"]
    assert payload["n_valid_payloads"] == 1
    assert payload["n_request_bound_payloads"] == 1
    return out_dir


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
        "n_packets_with_replan_metadata_trace": 1,
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
        "by_packet_llm_route_adoption_status": {
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
        },
        "n_response_present": 0,
        "n_awaiting_adapter_mapping": 1,
        "n_response_contract_ok": 0,
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
        "n_total_packets_with_replan_metadata_trace": 1,
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
        "by_total_packet_llm_route_adoption_status": {
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
        },
        "target_rows": [
            {
                "target_prover_family": target,
                "target_library_snapshot_ref": "cross_prover_matrix:rocq",
                "n_packets": 1,
                "n_packets_with_alignment": 1,
                "n_packets_with_standalone_input_trace": 1,
                "n_packets_missing_standalone_input_trace": 0,
                "n_packets_with_replan_metadata_trace": 1,
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
                "by_packet_llm_route_adoption_status": {
                    "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
                },
                "n_response_validation_rows": 1,
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


def _fixture_evaluation_row() -> dict[str, object]:
    return {
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
        "realization_coverage_witness_present": True,
        "realization_coverage_complete": False,
        "realization_missing_selected_formal_primitives": ["rank_uniformity"],
        "realization_missing_delta_alignment_primitives": ["rank_uniformity"],
        "realization_cost_hint_baseline_primitives": ["rank_uniformity"],
        "realization_omitted_cost_hint_primitives": ["rank_uniformity"],
        "realization_cost_hint_baseline_coverage_complete": False,
        "llm_route_planner_trace_present": True,
        "llm_route_planner_row_id": "llm-route-row:evaluation-fixture",
        "llm_route_planner_provider": "anthropic",
        "llm_route_planner_model": "claude-sonnet-4-6",
        "llm_route_planner_model_tier": "sonnet",
        "llm_route_planner_route_adoption_status": (
            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
        ),
        "llm_route_planner_route_adoption_blockers": [
            "search_requests_pending_evidence",
            "uncertainty_flags_require_review",
        ],
        "llm_route_planner_acceptance_status": (
            "ACCEPTED_SOURCE_GROUNDED_ROUTE_PLAN"
        ),
        "llm_route_planner_model_selection_rationale": (
            "auto selected Sonnet for evaluation fixture"
        ),
        "llm_route_planner_has_generator_metadata": True,
        "llm_route_planner_generator_metadata_keys": ["retry_count"],
        "quality_controls_present": True,
        "quality_controls": {
            "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
            "required_quality_signals": ["diagnostic_signature"],
            "response_validation_signals": [
                "residual_goals_or_diagnostics_present"
            ],
            "stop_conditions": [
                "residual interpreted or source search requested"
            ],
        },
        "quality_control_fields": [
            "required_quality_signals",
            "resource_contract_ids",
            "response_validation_signals",
            "stop_conditions",
        ],
        "quality_control_resource_contract_ids": [
            "lean_lsp:proof_state_feedback"
        ],
        "quality_control_response_validation_signals": [
            "residual_goals_or_diagnostics_present"
        ],
        "quality_control_stop_conditions": [
            "residual interpreted or source search requested"
        ],
        "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
        "proof_evidence_boundary_ok": True,
        "kernel_verified_ground_truth": False,
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_EVALUATION_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
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
        "candidate_declaration_rows": [
            {
                "declaration": "Fixture.rankUniformity",
                "target_prover_family": "lean4",
                "source_field": "candidate_declarations",
            }
        ],
        "declaration_sources": ["Fixture.rankUniformity"],
        "expected_premises": ["exchangeable scores"],
        "bridge_candidate_obligations": ["connect exchangeability to uniform rank"],
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


def _fixture_action_resource_plan_row() -> dict[str, object]:
    return {
        "schema_version": 1,
        "action_resource_plan_id": "action-resource-plan:fixture",
        "primitive_action_id": "primitive-action:fixture",
        "coverage_map_id": "coverage-map:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "primitive": "rank_uniformity",
        "coverage_bucket": "bridge_needed",
        "queue_action_kind": "prove_bridge_lemma",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:fixture",
        "candidate_declaration_rows": [
            {
                "declaration": "Fixture.rankUniformity",
                "target_prover_family": "lean4",
                "source_field": "candidate_declarations",
            }
        ],
        "component_ids": [
            "formal_library_coverage_mapping",
            "minimal_delta_and_or_planning",
            "prover_feedback_refinement",
        ],
        "local_first_resource_ids": [
            "local_formal_source_index",
            "local_lean_rag_dependency_graph",
            "local_lake_lean",
        ],
        "frontier_escalation_resource_ids": [
            "loogle_leansearch",
            "leanexplore_mcp",
            "lean_lsp_mcp",
        ],
        "adapter_ids": [
            "local_formal_source_index",
            "local_lean_rag_dependency_graph",
            "lean_lsp_mcp",
        ],
        "resource_contract_ids": [
            "resource-contract:formal-source",
            "resource-contract:lean-rag",
            "resource-contract:local-lake",
            "resource-contract:loogle",
            "resource-contract:leanexplore",
            "resource-contract:lean-lsp",
        ],
        "resource_contracts_by_resource": {
            "local_formal_source_index": ["resource-contract:formal-source"],
            "local_lean_rag_dependency_graph": ["resource-contract:lean-rag"],
            "local_lake_lean": ["resource-contract:local-lake"],
            "loogle_leansearch": ["resource-contract:loogle"],
            "leanexplore_mcp": ["resource-contract:leanexplore"],
            "lean_lsp_mcp": ["resource-contract:lean-lsp"],
        },
        "request_contract_fields_by_resource": {
            "local_formal_source_index": [
                "component_id",
                "route_id",
                "resource_id",
                "evidence_inputs",
                "proof_evidence_boundary",
            ],
            "local_lean_rag_dependency_graph": [
                "component_id",
                "route_id",
                "resource_id",
                "evidence_inputs",
                "proof_evidence_boundary",
            ],
            "local_lake_lean": [
                "component_id",
                "route_id",
                "resource_id",
                "evidence_inputs",
                "proof_evidence_boundary",
            ],
            "loogle_leansearch": [
                "component_id",
                "route_id",
                "resource_id",
                "evidence_inputs",
                "proof_evidence_boundary",
                "source_query_or_search_plan",
            ],
            "leanexplore_mcp": [
                "component_id",
                "route_id",
                "resource_id",
                "evidence_inputs",
                "proof_evidence_boundary",
                "source_query_or_search_plan",
                "mcp_tool_call",
            ],
            "lean_lsp_mcp": [
                "component_id",
                "route_id",
                "resource_id",
                "evidence_inputs",
                "proof_evidence_boundary",
                "mcp_tool_call",
            ],
        },
        "response_contract_fields_by_resource": {
            "local_formal_source_index": [
                "formal_declaration_hits",
                "lean_declaration_hits",
            ],
            "local_lean_rag_dependency_graph": [
                "declaration_hits",
                "dependency_neighbors",
            ],
            "local_lake_lean": ["prover_diagnostics", "residual_goals"],
            "loogle_leansearch": [
                "formal_declaration_hits",
                "lean_declaration_hits",
                "premise_candidates",
            ],
            "leanexplore_mcp": [
                "formal_declaration_hits",
                "lean_declaration_hits",
                "semantic_match_scores",
            ],
            "lean_lsp_mcp": ["prover_diagnostics", "residual_goals"],
        },
        "request_contract_fields": [
            "component_id",
            "route_id",
            "resource_id",
            "evidence_inputs",
            "proof_evidence_boundary",
            "source_query_or_search_plan",
            "mcp_tool_call",
        ],
        "response_contract_fields": [
            "formal_declaration_hits",
            "lean_declaration_hits",
            "declaration_hits",
            "dependency_neighbors",
            "premise_candidates",
            "semantic_match_scores",
            "prover_diagnostics",
            "residual_goals",
        ],
        "evidence_inputs": [
            "bridge candidate obligations",
            "expected premises",
            "library snapshot ref",
        ],
        "expected_outputs": [
            "bridge lemma statement",
            "residual goals",
            "route_revision_proposals",
        ],
        "escalation_triggers": [
            "local fallback returns no evidence rows",
            "residual goals introduce a primitive not aligned to the current route DAG",
        ],
        "stop_conditions": [
            "all expected outputs are present and schema-valid",
            "proof-boundary text is preserved and no kernel-proof claim is promoted",
        ],
        "acceptance_gate": "primitive gate: bridge lemma accepted or residuals routed",
        "reproduction_surface": (
            "formal_library_coverage_mapping: local_first=local_formal_source_index; "
            "frontier_escalation=lean_lsp_mcp"
        ),
        "execution_commands": [
            "python3 -m ai_statistician.cli formalization-gap-planner-refinement-queue",
        ],
        "resource_selection_reason": (
            "prove_bridge_lemma uses formal library coverage, minimal delta, "
            "and prover feedback components"
        ),
        "proof_evidence_status": ACTION_RESOURCE_PLAN_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }


def _write_local_adapter_fixture(
    adapter_dir: Path,
    *,
    artifact_name: str,
    local_count_field: str,
    response: dict[str, object],
) -> None:
    adapter_dir.mkdir(parents=True, exist_ok=True)
    (adapter_dir / f"{artifact_name}_manifest.json").write_text(
        json.dumps(
            {
                "component_name": artifact_name,
                local_count_field: 1,
                "n_merged_responses": 1,
                "n_local_response_schema_valid": 1,
                "n_local_response_schema_invalid": 0,
                "n_merged_response_schema_valid": 1,
                "n_merged_response_schema_invalid": 0,
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (adapter_dir / f"{artifact_name}_responses.jsonl").write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    ).write_text(
        json.dumps(response, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        adapter_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).write_text(
        json.dumps(refinement_tool_response_json_schema(), indent=2),
        encoding="utf-8",
    )
    (adapter_dir / f"{artifact_name}.md").write_text(
        "# local adapter fixture\nnot theorem proof evidence\n",
        encoding="utf-8",
    )


def test_publication_bundle_audit_accepts_self_contained_bundle() -> None:
    root = Path("runs/test_formalization_gap_planner_publication_bundle_audit")
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    paper_dir = root / "papers"
    target_intake_dir = root / "target_intake"
    goal_plan_dir = root / "goal_plan"
    prover_contract_dir = root / "prover_contract"
    cross_prover_matrix_dir = root / "cross_prover_matrix"
    portable_plan_audit_dir = root / "portable_plan_audit"
    library_coverage_map_dir = root / "library_coverage_map"
    primitive_action_queue_dir = root / "primitive_action_queue"
    action_resource_plan_dir = root / "action_resource_plan"
    minimal_delta_audit_dir = root / "minimal_delta_audit"
    source_grounding_audit_dir = root / "source_grounding_audit"
    refinement_queue_dir = root / "refinement_queue"
    evaluation_dir = root / "evaluation"
    ablation_study_dir = root / "ablation_study"
    refinement_adapter_dir = root / "refinement_adapter"
    local_literature_adapter_dir = root / "local_literature_adapter"
    local_formal_source_adapter_dir = root / "local_formal_source_adapter"
    local_proof_state_adapter_dir = root / "local_proof_state_adapter"
    route_revision_overlay_dir = root / "route_revision_overlay"
    replan_handoff_dir = root / "replan_handoff"
    replan_handoff_audit_dir = root / "replan_handoff_audit"
    adapter_registry_audit_dir = root / "adapter_registry_audit"
    component_resource_registry_audit_dir = root / "component_resource_registry_audit"
    shutil.rmtree(root, ignore_errors=True)
    paper_dir.mkdir(parents=True, exist_ok=True)
    target_intake_dir.mkdir(parents=True, exist_ok=True)
    goal_plan_dir.mkdir(parents=True, exist_ok=True)
    prover_contract_dir.mkdir(parents=True, exist_ok=True)
    cross_prover_matrix_dir.mkdir(parents=True, exist_ok=True)
    portable_plan_audit_dir.mkdir(parents=True, exist_ok=True)
    library_coverage_map_dir.mkdir(parents=True, exist_ok=True)
    primitive_action_queue_dir.mkdir(parents=True, exist_ok=True)
    action_resource_plan_dir.mkdir(parents=True, exist_ok=True)
    minimal_delta_audit_dir.mkdir(parents=True, exist_ok=True)
    source_grounding_audit_dir.mkdir(parents=True, exist_ok=True)
    refinement_queue_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    ablation_study_dir.mkdir(parents=True, exist_ok=True)
    refinement_adapter_dir.mkdir(parents=True, exist_ok=True)
    local_literature_adapter_dir.mkdir(parents=True, exist_ok=True)
    local_formal_source_adapter_dir.mkdir(parents=True, exist_ok=True)
    local_proof_state_adapter_dir.mkdir(parents=True, exist_ok=True)
    route_revision_overlay_dir.mkdir(parents=True, exist_ok=True)
    replan_handoff_dir.mkdir(parents=True, exist_ok=True)
    replan_handoff_audit_dir.mkdir(parents=True, exist_ok=True)
    adapter_registry_audit_dir.mkdir(parents=True, exist_ok=True)
    component_resource_registry_audit_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "route_note.md").write_text(
        "# Route note\nconditional mean residual zero\n",
        encoding="utf-8",
    )
    target_request_path = root / "target_request.json"
    target_request_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:fixture",
                "target_id": "rank_uniformity_fixture",
                "title": "Rank uniformity fixture",
                "domain": "distribution-free prediction",
                "theorem_statement": (
                    "For exchangeable calibration and test scores, the test "
                    "score rank is uniformly distributed."
                ),
                "objects": ["calibration scores", "test score rank"],
                "assumptions": ["exchangeable calibration and test scores"],
                "statistical_procedure": "rank-based conformal calibration",
                "desired_conclusion": "rank uniformity",
                "desired_theorem_shape": "finite sample rank identity",
                "known_proof_sources": ["fixture-source"],
                "candidate_primitives": [
                    {
                        "primitive": "rank_uniformity",
                        "coverage_status": "bridge_needed",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    normalize_formalization_gap_planner_target_intake(
        target_request_path,
        target_intake_dir,
    )
    export_formalization_gap_planner_standalone_plan(
        target_intake_dir
        / "formalization_gap_planner_target_intake_standalone_seed.json",
        goal_plan_dir,
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
                "n_total_packets_with_replan_metadata_trace": 1,
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
                "by_total_packet_llm_route_adoption_status": {
                    "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
                },
                "packet_count_consistent": True,
                "alignment_packet_count_consistent": True,
                "standalone_input_trace_packet_count_consistent": True,
                "quality_control_packet_count_consistent": True,
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
    ).write_text(
        json.dumps(prover_adapter_packet_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        cross_prover_matrix_dir
        / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
    ).write_text(
        json.dumps(prover_adapter_response_validation_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (cross_prover_matrix_dir / "formalization_gap_planner_cross_prover_matrix_audit.md").write_text(
        "# cross prover matrix\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    evaluation_row = _fixture_evaluation_row()
    evaluation_realization_missing_by_route = [
        {
            "route_id": "route:fixture",
            "goal_plan_id": "goal:fixture",
            "display_name": "fixture route",
            "missing_selected_formal_primitives": ["rank_uniformity"],
            "missing_delta_alignment_primitives": ["rank_uniformity"],
            "omitted_cost_hint_primitives": ["rank_uniformity"],
        }
    ]
    (evaluation_dir / "formalization_gap_planner_evaluation_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_evaluation",
                "n_evaluation_rows": 1,
                "n_evaluation_row_schema_valid": 1,
                "n_evaluation_row_schema_invalid": 0,
                "n_realization_missing_selected_formal_primitives": 1,
                "realization_missing_selected_formal_primitives": [
                    "rank_uniformity"
                ],
                "n_realization_missing_delta_alignment_primitives": 1,
                "realization_missing_delta_alignment_primitives": [
                    "rank_uniformity"
                ],
                "n_rows_with_incomplete_cost_hint_baseline_coverage": 1,
                "n_realization_cost_hint_baseline_primitives": 1,
                "realization_cost_hint_baseline_primitives": [
                    "rank_uniformity"
                ],
                "n_realization_omitted_cost_hint_primitives": 1,
                "realization_omitted_cost_hint_primitives": [
                    "rank_uniformity"
                ],
                "realization_missing_primitives_by_route": (
                    evaluation_realization_missing_by_route
                ),
                "n_rows_with_llm_route_planner_route_adoption_status": 1,
                "n_rows_ready_for_route_adoption": 0,
                "n_rows_pending_refinement_before_route_adoption": 1,
                "n_rows_awaiting_llm_route_planner_response": 0,
                "n_rows_rejected_llm_route_plan": 0,
                "n_llm_route_adoption_blockers": 2,
                "llm_route_adoption_blockers": [
                    "search_requests_pending_evidence",
                    "uncertainty_flags_require_review",
                ],
                "evaluation_by_llm_route_adoption_status": {
                    "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": {
                        "n_rows": 1,
                        "n_ok": 1,
                        "n_matched_ground_truth": 1,
                        "n_route_adoption_blockers": 2,
                        "mean_route_recall": 1.0,
                        "mean_delta_precision": 1.0,
                    }
                },
                "n_rows_with_quality_controls": 1,
                "n_quality_control_fields": 4,
                "quality_control_fields": [
                    "required_quality_signals",
                    "resource_contract_ids",
                    "response_validation_signals",
                    "stop_conditions",
                ],
                "quality_control_resource_contract_ids": [
                    "lean_lsp:proof_state_feedback"
                ],
                "quality_control_response_validation_signals": [
                    "residual_goals_or_diagnostics_present"
                ],
                "quality_control_stop_conditions": [
                    "residual interpreted or source search requested"
                ],
                "evaluation_by_quality_control_field": {
                    "required_quality_signals": {
                        "n_rows": 1,
                        "n_values": 1,
                        "values": ["diagnostic_signature"],
                    },
                    "resource_contract_ids": {
                        "n_rows": 1,
                        "n_values": 1,
                        "values": ["lean_lsp:proof_state_feedback"],
                    },
                    "response_validation_signals": {
                        "n_rows": 1,
                        "n_values": 1,
                        "values": ["residual_goals_or_diagnostics_present"],
                    },
                    "stop_conditions": {
                        "n_rows": 1,
                        "n_values": 1,
                        "values": [
                            "residual interpreted or source search requested"
                        ],
                    },
                },
                "bundled_ground_truth_filename": (
                    "formalization_gap_planner_evaluation_ground_truth.json"
                ),
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
        portable_plan_audit_dir
        / "formalization_gap_planner_portable_plan_audit_manifest.json"
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
    (
        portable_plan_audit_dir / "formalization_gap_planner_portable_plan_audit.jsonl"
    ).write_text(
        json.dumps(portable_plan_audit_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        portable_plan_audit_dir
        / "formalization_gap_planner_portable_plan_audit_row.schema.json"
    ).write_text(
        json.dumps(portable_plan_audit_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        portable_plan_audit_dir / "formalization_gap_planner_portable_plan_audit.md"
    ).write_text("# portable audit\nnot theorem proof evidence\n", encoding="utf-8")
    library_coverage_map_row = _fixture_library_coverage_map_row()
    (
        library_coverage_map_dir
        / "formalization_gap_planner_library_coverage_map_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_library_coverage_map",
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
    action_resource_plan_row = _fixture_action_resource_plan_row()
    (
        action_resource_plan_dir
        / "formalization_gap_planner_action_resource_plan_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_action_resource_plan",
                "n_resource_plan_rows": 1,
                "n_ok": 1,
                "n_failed": 0,
                "n_row_schema_valid": 1,
                "n_row_schema_invalid": 0,
                "n_with_local_first_resources": 1,
                "n_with_frontier_escalation_resources": 1,
                "n_with_resource_contracts": 1,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "rows": [action_resource_plan_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        action_resource_plan_dir
        / "formalization_gap_planner_action_resource_plan.jsonl"
    ).write_text(
        json.dumps(action_resource_plan_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        action_resource_plan_dir
        / "formalization_gap_planner_action_resource_plan_row.schema.json"
    ).write_text(
        json.dumps(action_resource_plan_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        action_resource_plan_dir
        / "formalization_gap_planner_action_resource_plan.md"
    ).write_text(
        "# action resource plan\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    minimal_delta_decision_row = {
        "schema_version": 1,
        "minimal_delta_decision_id": "minimal-delta:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:fixture",
        "route_class": "minimal_bridge_route",
        "pareto_profile": "non_dominated",
        "goal_conditioned_cost": 5,
        "route_efficiency_score": 90,
        "import_cone_size": 1,
        "dependency_graph_depth": 1,
        "route_cost_breakdown": {
            "base_route_cost": 5,
            "final_goal_conditioned_cost": 5,
        },
        "has_minimal_delta_and_or_cost_graph": False,
        "minimal_delta_route_option_count": 0,
        "minimal_delta_selected_route_option_id": "",
        "minimal_delta_selected_route_cost": 0.0,
        "minimal_delta_rejected_route_options": [],
        "selected_primitives": ["rank_uniformity"],
        "existing_reuse_primitives": [],
        "minimal_delta_primitives": ["rank_uniformity"],
        "work_packet_primitives": ["rank_uniformity"],
        "do_not_formalize_now": [],
        "cost_formula_ok": True,
        "node_cost_accounting_ok": True,
        "work_packet_cut_ok": True,
        "do_not_formalize_disjoint": True,
        "delta_nodes_connected": True,
        "cost_graph_selection_ok": True,
        "dominated_by_goal_plan_ids": [],
        "dominance_status": "NON_DOMINATED_UNDER_CURRENT_STRUCTURAL_PROXY",
        "minimality_evidence_status": (
            "STRUCTURAL_MINIMALITY_PROXY_NOT_SEMANTIC_OPTIMALITY"
        ),
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_MINIMAL_DELTA_AUDIT_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    (
        minimal_delta_audit_dir
        / "formalization_gap_planner_minimal_delta_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_minimal_delta_audit",
                "n_minimal_delta_decision_rows": 1,
                "n_minimal_delta_decision_row_schema_valid": 1,
                "n_minimal_delta_decision_row_schema_invalid": 0,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "minimal_delta_decision_rows": [minimal_delta_decision_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        minimal_delta_audit_dir
        / "formalization_gap_planner_minimal_delta_decisions.jsonl"
    ).write_text(
        json.dumps(minimal_delta_decision_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        minimal_delta_audit_dir
        / "formalization_gap_planner_minimal_delta_audit.jsonl"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "check_id": "minimal-delta-check:fixture",
                "check_name": "fixture_minimal_delta_check",
                "category": "fixture",
                "expected": "ok",
                "observed": "ok",
                "ok": True,
                "severity": "info",
                "errors": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (
        minimal_delta_audit_dir
        / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
    ).write_text(
        json.dumps(minimal_delta_decision_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        minimal_delta_audit_dir
        / "formalization_gap_planner_minimal_delta_audit.md"
    ).write_text(
        "# minimal delta audit\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    source_grounding_row = {
        "schema_version": 1,
        "source_grounding_id": "source-grounding:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "node_id": "informal:rank_uniformity",
        "node_kind": "lemma",
        "node_label": "rank uniformity",
        "source_refs": ["fixture-source"],
        "informal_proof_steps": ["use exchangeability to obtain uniform rank"],
        "literature_hook_present": True,
        "literature_queries": ["rank uniformity exchangeability conformal prediction"],
        "grounding_status": "source_backed",
        "required_next_action": "use attached source refs during route review",
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_SOURCE_GROUNDING_AUDIT_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    (
        source_grounding_audit_dir
        / "formalization_gap_planner_source_grounding_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_source_grounding_audit",
                "n_source_grounding_rows": 1,
                "n_row_schema_valid": 1,
                "n_row_schema_invalid": 0,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "rows": [source_grounding_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        source_grounding_audit_dir
        / "formalization_gap_planner_source_grounding_audit.jsonl"
    ).write_text(
        json.dumps(source_grounding_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        source_grounding_audit_dir
        / "formalization_gap_planner_source_grounding_row.schema.json"
    ).write_text(
        json.dumps(source_grounding_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        source_grounding_audit_dir
        / "formalization_gap_planner_source_grounding_audit.md"
    ).write_text(
        "# source grounding audit\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    refinement_work_item_row = {
        "schema_version": 2,
        "refinement_item_id": "refinement:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "theorem_skeleton": "theorem fixture_rank_uniformity : True := by trivial",
        "theorem_statement": "theorem fixture_rank_uniformity : True := by trivial",
        "route_class": "minimal_bridge_route",
        "pareto_profile": "non_dominated",
        "hook_kind": "lean_library_grounding",
        "refinement_stage": "formal_library_grounding",
        "owner_agent": "formal_source_agent",
        "target_primitives": ["rank_uniformity"],
        "trigger_kinds": ["coverage_gap"],
        "trigger_conditions": ["bridge lemma missing"],
        "trigger_next_actions": ["search Lean declarations"],
        "queries": ["rank_uniformity"],
        "recommended_tools": ["local_formal_source_index"],
        "frontier_resource_adapters": ["lean_lsp_mcp"],
        "evaluation_signal": "no_evaluation_signal",
        "evaluation_route_missing_primitives": [],
        "evaluation_delta_missing_primitives": [],
        "evaluation_coverage_confusions": [],
        "prover_feedback_status": "no_calibration_signal",
        "prover_feedback_error_category": "",
        "prover_feedback_first_error": "",
        "acceptance_record": "record evidence and rerun route revision overlay",
        "expected_artifacts": ["formalization_gap_planner_refinement_evidence"],
        "execution_commands": [
            "formalization-gap-planner-local-formal-source-adapter"
        ],
        "required_gate": "schema-valid refinement evidence response",
        "status": "READY_FOR_INTERACTIVE_REFINEMENT",
        "priority_score": 80,
        "rank": 1,
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_REFINEMENT_QUEUE_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    (
        refinement_queue_dir
        / "formalization_gap_planner_refinement_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_refinement_queue",
                "n_refinement_items": 1,
                "n_item_schema_valid": 1,
                "n_item_schema_invalid": 0,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "rows": [refinement_work_item_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        refinement_queue_dir
        / "formalization_gap_planner_refinement_queue.jsonl"
    ).write_text(
        json.dumps(refinement_work_item_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        refinement_queue_dir
        / "formalization_gap_planner_refinement_work_item.schema.json"
    ).write_text(
        json.dumps(refinement_work_item_json_schema(), indent=2),
        encoding="utf-8",
    )
    (refinement_queue_dir / "formalization_gap_planner_refinement_queue.md").write_text(
        "# refinement queue\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    ablation_row = {
        "schema_version": 1,
        "ablation_id": "ablation:fixture",
        "ablation_variant": "full_planner_observed",
        "ablated_signals": [],
        "n_routes": 1,
        "n_matched_routes": 1,
        "n_impacted_routes": 0,
        "n_impacted_primitives": 0,
        "impacted_primitives": [],
        "mean_route_recall": 1.0,
        "mean_route_precision": 1.0,
        "mean_delta_precision": 1.0,
        "mean_delta_recall": 1.0,
        "mean_residual_precision": 1.0,
        "mean_residual_recall": 1.0,
        "mean_existing_reuse_precision": 1.0,
        "mean_existing_reuse_recall": 1.0,
        "mean_coverage_accuracy": 1.0,
        "feedback_loop_readiness": 1.0,
        "next_action_replan_rate": 0.0,
        "next_action_replay_rate": 0.0,
        "route_adoption_ready_rate": 1.0,
        "route_adoption_pending_refinement_rate": 0.0,
        "mean_route_adoption_blockers": 0.0,
        "relative_route_recall_drop": 0.0,
        "relative_delta_recall_drop": 0.0,
        "relative_residual_recall_drop": 0.0,
        "relative_route_adoption_ready_drop": 0.0,
        "interpretation": "fixture ablation row",
        "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_ABLATION_STUDY_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    (ablation_study_dir / "formalization_gap_planner_ablation_study_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_ablation_study",
                "n_ablation_variants": 1,
                "n_row_schema_valid": 1,
                "n_row_schema_invalid": 0,
                "largest_route_adoption_ready_drop_variant": "full_planner_observed",
                "all_ok": True,
                "rows": [ablation_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (ablation_study_dir / "formalization_gap_planner_ablation_study.jsonl").write_text(
        json.dumps(ablation_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ablation_study_dir / "formalization_gap_planner_ablation_study_row.schema.json").write_text(
        json.dumps(ablation_study_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (ablation_study_dir / "formalization_gap_planner_ablation_study.md").write_text(
        "# ablation\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    refinement_adapter_response = {
        "refinement_item_id": "refinement:adapter",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "evidence_kind": "route_revision_proposal",
        "tool_name": "local_route_revision_adapter",
        "source_refs": ["fixture_source"],
        "route_revision_summary": "fixture route revision",
        "revised_selected_primitives": ["rank_uniformity"],
        "revised_delta_primitives": ["rank_uniformity"],
        "revised_informal_knowledge_dag_nodes": [{"node_id": "informal:rank"}],
        "revised_lean_realization_dag_nodes": [{"node_id": "lean:rank"}],
        "route_revision_recommended": True,
        "route_revision_reasons": ["fixture route revision"],
        "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_REFINEMENT_ADAPTER_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    (refinement_adapter_dir / "formalization_gap_planner_refinement_adapter_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_refinement_adapter_responses",
                "n_responses": 1,
                "n_response_schema_valid": 1,
                "n_response_schema_invalid": 0,
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        refinement_adapter_dir
        / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    ).write_text(
        json.dumps(refinement_adapter_response, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        refinement_adapter_dir
        / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).write_text(
        json.dumps(refinement_tool_response_json_schema(), indent=2),
        encoding="utf-8",
    )
    (refinement_adapter_dir / "formalization_gap_planner_refinement_adapter.md").write_text(
        "# refinement adapter\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    _write_local_adapter_fixture(
        local_literature_adapter_dir,
        artifact_name="formalization_gap_planner_local_literature_adapter",
        local_count_field="n_local_literature_responses",
        response={
            "refinement_item_id": "refinement:literature",
            "route_id": "route:fixture",
            "display_name": "fixture route",
            "evidence_kind": "literature_route_evidence",
            "tool_name": "local_literature_route_adapter",
            "source_refs": ["fixture_source"],
            "route_evidence_nodes": [{"node_id": "source:fixture"}],
            "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_LOCAL_LITERATURE_ADAPTER_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": "not theorem proof evidence",
        },
    )
    _write_local_adapter_fixture(
        local_formal_source_adapter_dir,
        artifact_name="formalization_gap_planner_local_formal_source_adapter",
        local_count_field="n_local_formal_source_responses",
        response={
            "refinement_item_id": "refinement:lean",
            "route_id": "route:fixture",
            "display_name": "fixture route",
            "evidence_kind": "lean_library_grounding",
            "tool_name": "local_formal_source_index_adapter",
            "lean_declaration_hits": [{"declaration": "Fixture.rank_uniformity"}],
            "coverage_updates": {"rank_uniformity": "wrapper_needed"},
            "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_LOCAL_FORMAL_SOURCE_ADAPTER_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": "not theorem proof evidence",
        },
    )
    _write_local_adapter_fixture(
        local_proof_state_adapter_dir,
        artifact_name="formalization_gap_planner_local_proof_state_adapter",
        local_count_field="n_local_proof_state_responses",
        response={
            "refinement_item_id": "refinement:proof",
            "route_id": "route:fixture",
            "display_name": "fixture route",
            "evidence_kind": "prover_feedback",
            "tool_name": "local_lean_proof_state_adapter",
            "attempt_status": "non_lean_skeleton",
            "prover_diagnostics": ["materialize theorem statement"],
            "residual_goals": ["rank_uniformity"],
            "route_revision_recommended": True,
            "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_LOCAL_PROOF_STATE_ADAPTER_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": "not theorem proof evidence",
        },
    )
    handoff_alignment_edges = [
        {
            "source": "informal:rank_uniformity",
            "target": "lean:rank_uniformity",
            "kind": "aligned_to_formal_realization_candidate",
            "primitive": "rank_uniformity",
            "alignment_status": "bridge_delta",
        }
    ]
    handoff_informal_nodes = [
        {
            "node_id": "informal:rank_uniformity",
            "label": "rank_uniformity",
            "primitive": "rank_uniformity",
        }
    ]
    handoff_lean_nodes = [
        {
            "node_id": "lean:rank_uniformity",
            "label": "rank_uniformity",
            "primitive": "rank_uniformity",
            "coverage_status": "bridge_needed",
        }
    ]
    resource_response_trace = {
        "resource_response_ledger_id": "rank_uniformity",
        "resource_request_id": "request:rank_uniformity",
        "resource_id": "local_lean_proof_state_adapter",
        "target_primitives": ["rank_uniformity"],
        "request_phase": "local_first",
        "expected_response_artifact": "proof_state_or_prover_feedback_response",
        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
        "matched_response_contract_fields": ["residual_goals"],
        "missing_response_contract_fields": [],
        "prover_attempt_status": "non_lean_skeleton",
        "prover_diagnostic_signature": "materialize_statement",
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    overlay_row = {
        "schema_version": 2,
        "route_revision_overlay_id": "overlay:rank_uniformity",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "revision_status": "ROUTE_REVISION_APPLIED",
        "original_selected_primitives": [],
        "revised_selected_primitives": ["rank_uniformity"],
        "added_primitives": ["rank_uniformity"],
        "removed_primitives": [],
        "original_delta_primitives": [],
        "revised_delta_primitives": ["rank_uniformity"],
        "added_delta_primitives": ["rank_uniformity"],
        "applied_proposal_ids": ["proposal:rank_uniformity"],
        "applied_refinement_evidence_ids": [
            "resource_response_ledger:rank_uniformity"
        ],
        "applied_hook_kinds": ["resource_response_ledger"],
        "applied_resource_response_traces": [resource_response_trace],
        "route_revision_reasons": ["proof-state feedback exposed missing bridge"],
        "route_revision_summaries": ["add rank uniformity bridge"],
        "source_refs": ["fixture source"],
        "formal_declaration_hits": [
            {"primitive": "rank_uniformity", "declaration": "Fixture.rank_uniformity"}
        ],
        "lean_declaration_hits": [
            {"primitive": "rank_uniformity", "declaration": "Fixture.rank_uniformity"}
        ],
        "residual_goals": ["rank_uniformity"],
        "applied_prover_attempt_statuses": ["non_lean_skeleton"],
        "applied_prover_diagnostic_signatures": ["materialize_statement"],
        "revised_informal_knowledge_dag_nodes": handoff_informal_nodes,
        "revised_formal_realization_dag_nodes": handoff_lean_nodes,
        "revised_lean_realization_dag_nodes": handoff_lean_nodes,
        "revised_route_alignment_edges": handoff_alignment_edges,
        "unaligned_primitives": [],
        "next_required_gate": "rerun planner and prover replay",
        "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    (
        route_revision_overlay_dir
        / "formalization_gap_planner_route_revision_overlay_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_revision_overlay",
                "n_overlay_rows": 1,
                "n_row_schema_valid": 1,
                "n_row_schema_invalid": 0,
                "n_rows_with_alignment_contract": 1,
                "n_unaligned_primitives": 0,
                "n_resource_response_ledger_route_revision_proposals": 1,
                "n_route_alignment_edges": 1,
                "n_formal_realization_dag_nodes": 1,
                "all_ok": True,
                "rows": [overlay_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        route_revision_overlay_dir / "formalization_gap_planner_route_revision_overlay.jsonl"
    ).write_text(
        json.dumps(overlay_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        route_revision_overlay_dir
        / "formalization_gap_planner_route_revision_overlay_row.schema.json"
    ).write_text(
        json.dumps(route_revision_overlay_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        route_revision_overlay_dir / "formalization_gap_planner_route_revision_overlay.md"
    ).write_text(
        "# route revision overlay\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    handoff_row = {
        "schema_version": 1,
        "route_replan_handoff_id": "handoff:rank_uniformity",
        "route_revision_overlay_id": "overlay:rank_uniformity",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "revision_status": "ROUTE_REVISION_APPLIED",
        "stability_decision": "APPLY_ROUTE_REVISION_AND_REPLAN",
        "requires_replan": True,
        "original_selected_primitives": [],
        "revised_selected_primitives": ["rank_uniformity"],
        "original_delta_primitives": [],
        "revised_delta_primitives": ["rank_uniformity"],
        "added_primitives": ["rank_uniformity"],
        "added_delta_primitives": ["rank_uniformity"],
        "residual_goals": ["rank_uniformity"],
        "applied_proposal_ids": ["proposal:rank_uniformity"],
        "applied_refinement_evidence_ids": [
            "resource_response_ledger:rank_uniformity"
        ],
        "applied_hook_kinds": ["resource_response_ledger"],
        "applied_resource_response_traces": [resource_response_trace],
        "resource_response_awaiting_request_ids": ["request:awaiting-rank-source"],
        "resource_response_rejected_request_ids": ["request:rejected-rank-proof"],
        "applied_prover_attempt_statuses": ["non_lean_skeleton"],
        "applied_prover_diagnostic_signatures": ["materialize_statement"],
        "route_revision_reasons": ["proof-state feedback exposed missing bridge"],
        "route_revision_summaries": ["add rank uniformity bridge"],
        "source_refs": ["fixture source"],
        "formal_declaration_hits": [
            {"primitive": "rank_uniformity", "declaration": "Fixture.rank_uniformity"}
        ],
        "lean_declaration_hits": [
            {"primitive": "rank_uniformity", "declaration": "Fixture.rank_uniformity"}
        ],
        "revised_informal_knowledge_dag_nodes": handoff_informal_nodes,
        "revised_formal_realization_dag_nodes": handoff_lean_nodes,
        "revised_lean_realization_dag_nodes": handoff_lean_nodes,
        "revised_route_alignment_edges": handoff_alignment_edges,
        "unaligned_primitives": [],
        "standalone_route_id": "replan_route:rank_uniformity",
        "standalone_route": {"route_id": "replan_route:rank_uniformity"},
        "next_commands": [
            "formalization-gap-planner-standalone-plan --input formalization_gap_planner_route_replan_standalone_seed.json"
        ],
        "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_ROUTE_REPLAN_HANDOFF_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    (replan_handoff_dir / "formalization_gap_planner_route_replan_handoff_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_replan_handoff",
                "n_handoff_rows": 1,
                "n_standalone_seed_routes": 1,
                "n_route_alignment_edges": 1,
                "n_revised_informal_knowledge_dag_nodes": 1,
                "n_revised_formal_realization_dag_nodes": 1,
                "n_revised_lean_realization_dag_nodes": 1,
                "n_unaligned_primitives": 0,
                "n_routes_with_resource_response_ledger_feedback": 1,
                "n_resource_response_awaiting_request_ids": 1,
                "n_resource_response_rejected_request_ids": 1,
                "n_distinct_prover_diagnostic_signatures": 1,
                "all_ok": True,
                "rows": [handoff_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (replan_handoff_dir / "formalization_gap_planner_route_replan_handoff.jsonl").write_text(
        json.dumps(handoff_row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        replan_handoff_dir
        / "formalization_gap_planner_route_replan_handoff_row.schema.json"
    ).write_text(
        json.dumps(route_replan_handoff_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (replan_handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "route_id": "replan_route:rank_uniformity",
                        "revised_informal_knowledge_dag_nodes": handoff_informal_nodes,
                        "revised_formal_realization_dag_nodes": handoff_lean_nodes,
                        "revised_lean_realization_dag_nodes": handoff_lean_nodes,
                        "revised_route_alignment_edges": handoff_alignment_edges,
                        "replan_metadata": {
                            "applied_proposal_ids": ["proposal:rank_uniformity"],
                            "applied_refinement_evidence_ids": [
                                "resource_response_ledger:rank_uniformity"
                            ],
                            "applied_hook_kinds": ["resource_response_ledger"],
                            "applied_resource_response_traces": [
                                resource_response_trace
                            ],
                            "resource_response_awaiting_request_ids": [
                                "request:awaiting-rank-source"
                            ],
                            "resource_response_rejected_request_ids": [
                                "request:rejected-rank-proof"
                            ],
                            "applied_prover_attempt_statuses": ["non_lean_skeleton"],
                            "applied_prover_diagnostic_signatures": [
                                "materialize_statement"
                            ],
                            "route_revision_reasons": [
                                "proof-state feedback exposed missing bridge"
                            ],
                            "route_revision_summaries": [
                                "add rank uniformity bridge"
                            ],
                            "residual_goals": ["rank_uniformity"],
                            "source_refs": ["fixture source"],
                            "formal_declaration_hits": [
                                {
                                    "primitive": "rank_uniformity",
                                    "declaration": "Fixture.rank_uniformity",
                                }
                            ],
                            "lean_declaration_hits": [
                                {
                                    "primitive": "rank_uniformity",
                                    "declaration": "Fixture.rank_uniformity",
                                }
                            ],
                            "revised_informal_knowledge_dag_nodes": handoff_informal_nodes,
                            "revised_formal_realization_dag_nodes": handoff_lean_nodes,
                            "revised_lean_realization_dag_nodes": handoff_lean_nodes,
                            "revised_route_alignment_edges": handoff_alignment_edges,
                        },
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        replan_handoff_dir
        / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
    ).write_text(
        json.dumps(standalone_input_json_schema(), indent=2),
        encoding="utf-8",
    )
    (replan_handoff_dir / "formalization_gap_planner_route_replan_handoff.md").write_text(
        "# handoff\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    audit_checks = [
        {
            "schema_version": 1,
            "check_id": "check:handoff_alignment_edges_present",
            "check_name": "handoff_alignment_edges_present",
            "category": "alignment",
            "expected": "all handoff rows preserve revised route alignment edges",
            "observed": "1/1",
            "ok": True,
            "severity": "error",
            "errors": [],
        },
        {
            "schema_version": 1,
            "check_id": "check:handoff_no_unaligned_primitives",
            "check_name": "handoff_no_unaligned_primitives",
            "category": "alignment",
            "expected": "zero unaligned primitives",
            "observed": "0",
            "ok": True,
            "severity": "error",
            "errors": [],
        },
        {
            "schema_version": 1,
            "check_id": "check:roundtrip_alignment_edges",
            "check_name": "roundtrip_alignment_edges",
            "category": "roundtrip",
            "expected": "roundtrip regenerates at least one alignment edge per seed route",
            "observed": "1",
            "ok": True,
            "severity": "error",
            "errors": [],
        },
        {
            "schema_version": 1,
            "check_id": "check:roundtrip_alignment_contract",
            "check_name": "roundtrip_alignment_contract",
            "category": "roundtrip",
            "expected": "all roundtrip rows have selected-primitive alignment",
            "observed": "1/1",
            "ok": True,
            "severity": "error",
            "errors": [],
        },
        {
            "schema_version": 1,
            "check_id": "check:roundtrip_standalone_input_trace",
            "check_name": "roundtrip_standalone_input_trace",
            "category": "roundtrip",
            "expected": "roundtrip goal-plan rows preserve standalone seed trace metadata",
            "observed": "trace_routes=1/1 trace_with_replan_metadata=1",
            "ok": True,
            "severity": "error",
            "errors": [],
        },
        {
            "schema_version": 1,
            "check_id": "check:row_0_seed_route_provenance_metadata",
            "check_name": "row_0_seed_route_provenance_metadata",
            "category": "provenance",
            "expected": "seed route preserves handoff-row provenance",
            "observed": "applied_hook_kinds=1",
            "ok": True,
            "severity": "error",
            "errors": [],
        },
    ]
    (replan_handoff_audit_dir / "formalization_gap_planner_route_replan_handoff_audit_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_replan_handoff_audit",
                "n_checks": 6,
                "n_failed": 0,
                "n_row_schema_valid": 6,
                "n_row_schema_invalid": 0,
                "n_seed_routes": 1,
                "n_roundtrip_goal_plans": 1,
                "n_roundtrip_route_alignment_edges": 1,
                "roundtrip_all_ok": True,
                "all_ok": True,
                "checks": audit_checks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (replan_handoff_audit_dir / "formalization_gap_planner_route_replan_handoff_audit.jsonl").write_text(
        "\n".join(json.dumps(check, sort_keys=True) for check in audit_checks) + "\n",
        encoding="utf-8",
    )
    (
        replan_handoff_audit_dir
        / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
    ).write_text(
        json.dumps(route_replan_handoff_audit_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (replan_handoff_audit_dir / "formalization_gap_planner_route_replan_handoff_audit.md").write_text(
        "# audit\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    adapter_registry_audit_check = {
        "schema_version": 1,
        "check_id": "adapter-registry-audit-check:fixture",
        "check_name": "adapter_registry_fixture_check",
        "category": "fixture",
        "expected": "ok",
        "observed": "ok",
        "ok": True,
        "severity": "info",
        "errors": [],
    }
    (
        adapter_registry_audit_dir
        / "formalization_gap_planner_adapter_registry_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_adapter_registry_audit",
                "n_checks": 1,
                "n_ok": 1,
                "n_failed": 0,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "checks": [adapter_registry_audit_check],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        adapter_registry_audit_dir
        / "formalization_gap_planner_adapter_registry_audit.jsonl"
    ).write_text(
        json.dumps(adapter_registry_audit_check, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        adapter_registry_audit_dir
        / "formalization_gap_planner_adapter_registry_audit.md"
    ).write_text(
        "# adapter registry audit\nnot theorem proof evidence\n",
        encoding="utf-8",
    )
    component_resource_registry_audit_check = {
        "schema_version": 1,
        "check_id": "component-resource-registry-audit-check:fixture",
        "check_name": "component_resource_registry_fixture_check",
        "category": "fixture",
        "expected": "ok",
        "observed": "ok",
        "ok": True,
        "severity": "info",
        "errors": [],
    }
    (
        component_resource_registry_audit_dir
        / "formalization_gap_planner_component_resource_registry_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": (
                    "formalization_gap_planner_component_resource_registry_audit"
                ),
                "n_checks": 1,
                "n_ok": 1,
                "n_failed": 0,
                "all_ok": True,
                "proof_evidence_boundary": "not theorem proof evidence",
                "checks": [component_resource_registry_audit_check],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        component_resource_registry_audit_dir
        / "formalization_gap_planner_component_resource_registry_audit.jsonl"
    ).write_text(
        json.dumps(component_resource_registry_audit_check, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        component_resource_registry_audit_dir
        / "formalization_gap_planner_component_resource_registry_audit.md"
    ).write_text(
        "# component resource registry audit\nnot theorem proof evidence\n",
        encoding="utf-8",
    )

    bundle_payload = export_formalization_gap_planner_publication_bundle(
        bundle_dir,
        paper_library_dir=paper_dir,
        formalization_gap_planner_target_intake_dir=target_intake_dir,
        goal_conditioned_minimal_formalization_plan_dir=goal_plan_dir,
        formalization_gap_planner_portable_plan_audit_dir=portable_plan_audit_dir,
        formalization_gap_planner_library_coverage_map_dir=library_coverage_map_dir,
        formalization_gap_planner_primitive_action_queue_dir=primitive_action_queue_dir,
        formalization_gap_planner_action_resource_plan_dir=action_resource_plan_dir,
        formalization_gap_planner_minimal_delta_audit_dir=minimal_delta_audit_dir,
        formalization_gap_planner_source_grounding_audit_dir=source_grounding_audit_dir,
        formalization_gap_planner_refinement_queue_dir=refinement_queue_dir,
        formalization_gap_planner_evaluation_dir=evaluation_dir,
        formalization_gap_planner_ablation_study_dir=ablation_study_dir,
        formalization_gap_planner_refinement_adapter_dir=refinement_adapter_dir,
        formalization_gap_planner_local_literature_adapter_dir=local_literature_adapter_dir,
        formalization_gap_planner_local_formal_source_adapter_dir=local_formal_source_adapter_dir,
        formalization_gap_planner_local_proof_state_adapter_dir=local_proof_state_adapter_dir,
        formalization_gap_planner_prover_adapter_contract_dir=prover_contract_dir,
        formalization_gap_planner_cross_prover_matrix_audit_dir=cross_prover_matrix_dir,
        formalization_gap_planner_route_revision_overlay_dir=route_revision_overlay_dir,
        formalization_gap_planner_route_replan_handoff_dir=replan_handoff_dir,
        formalization_gap_planner_route_replan_handoff_audit_dir=replan_handoff_audit_dir,
        formalization_gap_planner_adapter_registry_audit_dir=adapter_registry_audit_dir,
        formalization_gap_planner_component_resource_registry_audit_dir=component_resource_registry_audit_dir,
    )
    audit_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        audit_dir,
    )

    assert bundle_payload["all_ok"]
    assert audit_payload["all_ok"]
    assert audit_payload["n_failed"] == 0
    assert audit_payload["n_bundle_files"] >= 10
    assert audit_payload["n_component_execution_plan_schema_checked"] == 8
    assert (
        audit_payload["n_component_execution_plan_schema_valid"]
        == audit_payload["n_component_execution_plan_schema_checked"]
    )
    assert audit_payload["n_component_resource_component_row_schema_checked"] == 8
    assert (
        audit_payload["n_component_resource_component_row_schema_valid"]
        == audit_payload["n_component_resource_component_row_schema_checked"]
    )
    assert audit_payload["n_component_resource_resource_row_schema_checked"] >= 20
    assert (
        audit_payload["n_component_resource_resource_row_schema_valid"]
        == audit_payload["n_component_resource_resource_row_schema_checked"]
    )
    assert audit_payload["n_component_resource_contract_row_schema_checked"] >= 20
    assert (
        audit_payload["n_component_resource_contract_row_schema_valid"]
        == audit_payload["n_component_resource_contract_row_schema_checked"]
    )
    assert audit_payload["n_prover_adapter_packet_schema_checked"] == 1
    assert (
        audit_payload["n_prover_adapter_packet_schema_valid"]
        == audit_payload["n_prover_adapter_packet_schema_checked"]
    )
    assert audit_payload["n_prover_adapter_response_validation_row_schema_checked"] == 1
    assert audit_payload["n_prover_adapter_response_validation_row_schema_valid"] == 1
    assert audit_payload["n_optional_cross_prover_matrix_row_schema_checked"] == 1
    assert audit_payload["n_optional_cross_prover_matrix_row_schema_valid"] == 1
    assert audit_payload["n_optional_cross_prover_packet_row_schema_checked"] == 1
    assert audit_payload["n_optional_cross_prover_packet_row_schema_valid"] == 1
    assert audit_payload["n_optional_cross_prover_packet_trace_checked"] == 1
    assert audit_payload["n_optional_cross_prover_packet_trace_valid"] == 1
    assert (
        audit_payload[
            "n_optional_cross_prover_response_validation_row_schema_checked"
        ]
        == 1
    )
    assert (
        audit_payload["n_optional_cross_prover_response_validation_row_schema_valid"]
        == 1
    )
    assert audit_payload["n_benchmark_route_row_schema_checked"] == bundle_payload[
        "benchmark_summary"
    ]["n_routes"]
    assert (
        audit_payload["n_benchmark_route_row_schema_valid"]
        == audit_payload["n_benchmark_route_row_schema_checked"]
    )
    assert (
        audit_payload["n_adapter_registry_row_schema_checked"]
        == bundle_payload["adapter_registry_summary"]["n_adapters"]
    )
    assert (
        audit_payload["n_adapter_registry_row_schema_valid"]
        == audit_payload["n_adapter_registry_row_schema_checked"]
    )
    assert audit_payload["n_optional_evaluation_row_schema_checked"] == 1
    assert audit_payload["n_optional_evaluation_row_schema_valid"] == 1
    assert audit_payload["n_optional_evaluation_ground_truth_file_checked"] == 2
    assert audit_payload["n_optional_evaluation_ground_truth_file_valid"] == 2
    assert audit_payload["n_optional_evaluation_ground_truth_match_checked"] == 1
    assert audit_payload["n_optional_evaluation_ground_truth_match_valid"] == 1
    assert audit_payload["n_optional_evaluation_ground_truth_primitive_checked"] == 1
    assert audit_payload["n_optional_evaluation_ground_truth_primitive_valid"] == 1
    assert audit_payload["n_optional_evaluation_realization_missing_row_checked"] == 1
    assert audit_payload["n_optional_evaluation_realization_missing_row_valid"] == 1
    assert (
        audit_payload["n_optional_evaluation_realization_missing_manifest_checked"]
        == 1
    )
    assert (
        audit_payload["n_optional_evaluation_realization_missing_manifest_valid"]
        == 1
    )
    assert audit_payload["n_optional_evaluation_route_adoption_row_checked"] == 1
    assert audit_payload["n_optional_evaluation_route_adoption_row_valid"] == 1
    assert (
        audit_payload["n_optional_evaluation_route_adoption_manifest_checked"]
        == 1
    )
    assert audit_payload["n_optional_evaluation_route_adoption_manifest_valid"] == 1
    assert audit_payload["n_optional_evaluation_quality_control_row_checked"] == 1
    assert audit_payload["n_optional_evaluation_quality_control_row_valid"] == 1
    assert (
        audit_payload["n_optional_evaluation_quality_control_manifest_checked"]
        == 1
    )
    assert (
        audit_payload["n_optional_evaluation_quality_control_manifest_valid"]
        == 1
    )
    assert audit_payload["n_optional_evaluation_rows_with_route_adoption_status"] == 1
    assert audit_payload["optional_evaluation_route_adoption_status_counts"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
    }
    assert audit_payload["n_optional_evaluation_rows_ready_for_route_adoption"] == 0
    assert (
        audit_payload[
            "n_optional_evaluation_rows_pending_refinement_before_route_adoption"
        ]
        == 1
    )
    assert audit_payload["n_optional_evaluation_route_adoption_blockers"] == 2
    assert audit_payload["optional_evaluation_route_adoption_blockers"] == (
        "search_requests_pending_evidence",
        "uncertainty_flags_require_review",
    )
    assert audit_payload["n_optional_evaluation_rows_with_quality_controls"] == 1
    assert audit_payload["n_optional_evaluation_quality_control_fields"] == 4
    assert audit_payload["optional_evaluation_quality_control_fields"] == (
        "required_quality_signals",
        "resource_contract_ids",
        "response_validation_signals",
        "stop_conditions",
    )
    assert audit_payload[
        "optional_evaluation_quality_control_resource_contract_ids"
    ] == ("lean_lsp:proof_state_feedback",)
    assert audit_payload[
        "optional_evaluation_quality_control_response_validation_signals"
    ] == ("residual_goals_or_diagnostics_present",)
    assert audit_payload["optional_evaluation_quality_control_stop_conditions"] == (
        "residual interpreted or source search requested",
    )
    assert (
        audit_payload[
            "n_optional_evaluation_realization_missing_selected_formal_primitives"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_evaluation_realization_missing_delta_alignment_primitives"
        ]
        == 1
    )
    assert (
        audit_payload[
            "optional_evaluation_realization_missing_selected_formal_primitives"
        ]
        == ("rank_uniformity",)
    )
    assert (
        audit_payload[
            "optional_evaluation_realization_missing_delta_alignment_primitives"
        ]
        == ("rank_uniformity",)
    )
    assert (
        audit_payload[
            "n_optional_evaluation_rows_with_incomplete_cost_hint_baseline_coverage"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_evaluation_realization_cost_hint_baseline_primitives"
        ]
        == 1
    )
    assert (
        audit_payload[
            "optional_evaluation_realization_cost_hint_baseline_primitives"
        ]
        == ("rank_uniformity",)
    )
    assert (
        audit_payload[
            "n_optional_evaluation_realization_omitted_cost_hint_primitives"
        ]
        == 1
    )
    assert (
        audit_payload[
            "optional_evaluation_realization_omitted_cost_hint_primitives"
        ]
        == ("rank_uniformity",)
    )
    assert audit_payload["optional_evaluation_realization_missing_primitives_by_route"] == (
        {
            "route_id": "route:fixture",
            "goal_plan_id": "goal:fixture",
            "display_name": "fixture route",
            "missing_selected_formal_primitives": ("rank_uniformity",),
            "missing_delta_alignment_primitives": ("rank_uniformity",),
            "omitted_cost_hint_primitives": ("rank_uniformity",),
        },
    )
    assert any(
        row["check_name"] == "optional_evaluation_ground_truth_copy" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "bundle_evaluation_summary_consistent" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_evaluation_ground_truth_parse" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_evaluation_row_0_ground_truth_match"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_evaluation_row_0_ground_truth_primitives"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_evaluation_row_0_realization_missing_fields"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_evaluation_realization_missing_manifest"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_evaluation_row_0_route_adoption_fields"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_evaluation_route_adoption_manifest"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert audit_payload["n_optional_portable_plan_audit_row_schema_checked"] == 1
    assert audit_payload["n_optional_portable_plan_audit_row_schema_valid"] == 1
    assert audit_payload["n_optional_library_coverage_map_row_schema_checked"] == 1
    assert audit_payload["n_optional_library_coverage_map_row_schema_valid"] == 1
    assert audit_payload["n_optional_primitive_action_queue_row_schema_checked"] == 1
    assert audit_payload["n_optional_primitive_action_queue_row_schema_valid"] == 1
    assert audit_payload["n_optional_action_resource_plan_row_schema_checked"] == 1
    assert audit_payload["n_optional_action_resource_plan_row_schema_valid"] == 1
    bundled_action_plan_rows = [
        json.loads(line)
        for line in (
            bundle_dir
            / "artifacts"
            / "formalization_gap_planner_action_resource_plan"
            / "formalization_gap_planner_action_resource_plan.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    bundled_action_plan_row = bundled_action_plan_rows[0]
    assert "formal_declaration_hits" in bundled_action_plan_row[
        "response_contract_fields"
    ]
    assert "lean_declaration_hits" in bundled_action_plan_row[
        "response_contract_fields"
    ]
    for resource_id in (
        "local_formal_source_index",
        "loogle_leansearch",
        "leanexplore_mcp",
    ):
        resource_fields = bundled_action_plan_row[
            "response_contract_fields_by_resource"
        ][resource_id]
        assert "formal_declaration_hits" in resource_fields
        assert "lean_declaration_hits" in resource_fields
    assert audit_payload["n_optional_minimal_delta_decision_row_schema_checked"] == 1
    assert audit_payload["n_optional_minimal_delta_decision_row_schema_valid"] == 1
    assert audit_payload["n_optional_source_grounding_row_schema_checked"] == 1
    assert audit_payload["n_optional_source_grounding_row_schema_valid"] == 1
    assert audit_payload["n_optional_refinement_work_item_row_schema_checked"] == 1
    assert audit_payload["n_optional_refinement_work_item_row_schema_valid"] == 1
    assert audit_payload["n_optional_target_intake_row_contract_checked"] == 1
    assert audit_payload["n_optional_target_intake_row_contract_valid"] == 1
    assert audit_payload["n_optional_target_intake_row_schema_checked"] == 1
    assert audit_payload["n_optional_target_intake_row_schema_valid"] == 1
    assert audit_payload["n_optional_goal_plan_row_contract_checked"] == 1
    assert audit_payload["n_optional_goal_plan_row_contract_valid"] == 1
    assert audit_payload["n_optional_goal_plan_row_schema_checked"] == 1
    assert audit_payload["n_optional_goal_plan_row_schema_valid"] == 1
    assert audit_payload["n_optional_adapter_registry_audit_check_contract_checked"] == 1
    assert audit_payload["n_optional_adapter_registry_audit_check_contract_valid"] == 1
    assert (
        audit_payload[
            "n_optional_component_resource_registry_audit_check_contract_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_component_resource_registry_audit_check_contract_valid"
        ]
        == 1
    )
    assert audit_payload["n_optional_refinement_adapter_response_schema_checked"] == 1
    assert audit_payload["n_optional_refinement_adapter_response_schema_valid"] == 1
    assert audit_payload["n_optional_local_adapter_response_schema_checked"] == 6
    assert audit_payload["n_optional_local_adapter_response_schema_valid"] == 6
    assert any(
        row["check_name"] == "standalone_input_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "target_intake_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_plan_row_schema_id"
        and row["observed"] == portable_gap_plan_row_json_schema()["$id"]
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "schema_catalog_schema_id"
        and row["observed"] == schema_catalog_json_schema()["$id"]
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "publication_bundle_manifest_schema_file" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "publication_bundle_manifest_schema_id"
        and row["observed"]
        == FORMALIZATION_GAP_PLANNER_PUBLICATION_BUNDLE_MANIFEST_SCHEMA_ID
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "publication_bundle_manifest_schema_matches_contract"
        and row["expected"] == publication_bundle_manifest_json_schema()["$id"]
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "schema_catalog_payload_schema_id"
        and row["observed"] == schema_catalog_json_schema()["$id"]
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "schema_catalog_entries_present" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "schema_catalog_required_entries" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "schema_catalog_entry_paths_resolve" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "schema_catalog_contract_valid" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "schema_catalog_all_ok" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "schema_catalog_lean_legacy_payload_schema_targets"
        and row["observed"] == "lean4"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "schema_catalog_target_prover_payload_schema_targets"
        and row["observed"] == "rocq,isabelle,agda"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "llm_route_planner_response_payload_lean_legacy_schema_shape"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "llm_route_planner_response_payload_target_prover_schema_shape"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "route_adoption_blocker_taxonomy_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "route_adoption_blocker_taxonomy_payload"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_route_adoption_blocker_taxonomy_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_route_adoption_blocker_taxonomy_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "llm_route_planner_row_schema_route_adoption_status_enum_matches_taxonomy"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "llm_route_planner_row_schema_route_adoption_blocker_enum_matches_taxonomy"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_goal_plan_row_schema_id"
        and row["observed"] == portable_gap_plan_row_json_schema()["$id"]
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_portable_gap_plan_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_schema_catalog_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "llm_model_policy_default_provider"
        and row["observed"] == "anthropic"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "llm_model_policy_latest_claude_tiers"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "llm_model_policy_outside_cost_tier_models"
        and "claude-fable-5" in row["observed"]
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "llm_model_policy_rejects_codex"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_llm_model_policy_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "target_intake_row_schema_id"
        and row["observed"] == target_intake_row_json_schema()["$id"]
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_target_intake_row_schema_id"
        and row["observed"] == target_intake_row_json_schema()["$id"]
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_target_intake_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "component_execution_plan_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "component_resource_resource_row_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "component_resource_component_row_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "component_resource_contract_row_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "prover_adapter_packet_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "prover_adapter_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "prover_adapter_response_validation_row_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "cross_prover_matrix_audit_row_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "cross_prover_target_summary_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "refinement_tool_response_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "refinement_evidence_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "proof_state_triage_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "refinement_work_item_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "interactive_session_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "interactive_decision_policy_row_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "minimal_delta_decision_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "source_grounding_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "route_revision_overlay_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "route_stability_audit_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "route_replan_handoff_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "route_replan_handoff_audit_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "ablation_study_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_plan_audit_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "route_alignment_edge_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "benchmark_route_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "evaluation_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "adapter_registry_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "library_coverage_map_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "primitive_action_queue_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "action_resource_plan_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "resource_request_queue_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "resource_response_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "resource_response_schema_rejects_kernel_claim"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "resource_response_ledger_row_schema_id" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert json.loads(
        (
            bundle_dir
            / "contract"
            / "formalization_gap_planner_resource_request_queue_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == resource_request_queue_row_json_schema()["$id"]
    assert json.loads(
        (
            bundle_dir
            / "contract"
            / "formalization_gap_planner_resource_response.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == resource_response_json_schema()["$id"]
    assert json.loads(
        (
            bundle_dir
            / "contract"
            / "formalization_gap_planner_resource_response_ledger_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == resource_response_ledger_row_json_schema()["$id"]
    assert json.loads(
        (
            bundle_dir
            / "contract"
            / "formalization_gap_planner_adapter_registry_row.schema.json"
        ).read_text(encoding="utf-8")
    )["$id"] == adapter_registry_row_json_schema()["$id"]
    assert any(
        row["check_name"] == "adapter_registry_row_0_schema_valid" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "benchmark_route_row_0_schema_valid" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_evaluation_row_0_schema_valid" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_portable_plan_audit_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_library_coverage_map_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_primitive_action_queue_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_action_resource_plan_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_refinement_adapter_response_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_local_adapter_response_local_literature_adapter_local_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_local_adapter_response_local_formal_source_adapter_local_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_local_adapter_response_local_proof_state_adapter_local_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_prover_adapter_packet_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_prover_adapter_response_validation_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_cross_prover_matrix_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_cross_prover_packet_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_cross_prover_packet_row_0_standalone_input_trace"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_cross_prover_target_summary_contract_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_cross_prover_response_validation_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_component_execution_plan_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_component_resource_resource_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_component_resource_component_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_component_resource_contract_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_adapter_registry_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_prover_adapter_packet_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_prover_adapter_response_validation_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_cross_prover_matrix_audit_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_cross_prover_target_summary_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_refinement_tool_response_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_refinement_evidence_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_proof_state_triage_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_refinement_work_item_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_interactive_session_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_interactive_decision_policy_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_minimal_delta_decision_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_source_grounding_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_route_revision_overlay_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_route_stability_audit_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_route_replan_handoff_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_route_replan_handoff_audit_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_ablation_study_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_portable_plan_audit_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_library_coverage_map_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_primitive_action_queue_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_action_resource_plan_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_resource_request_queue_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_resource_response_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "portable_contract_has_resource_response_ledger_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_route_alignment_edge_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_benchmark_route_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "portable_contract_has_evaluation_row_contract"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_required_entrypoints" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_standalone_command" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_benchmark_audit_command" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_evaluation_command" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_evaluation_ground_truth_source"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_target_intake_command" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_reuse_smoke_command" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_runtime_handoff_reuse_smoke_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_component_resource_registry_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_action_resource_plan_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_resource_request_queue_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_resource_response_ledger_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "reproduction_route_revision_overlay_consumes_resource_response_ledger"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_required_commands" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_refinement_loop_commands" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_local_adapter_chain_commands" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_local_feedback_to_evidence_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_prover_adapter_feedback_to_evidence_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_route_replan_commands" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_llm_route_planner_command" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_llm_route_payload_validation_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "reproduction_feedback_llm_route_planner_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "reproduction_feedback_llm_route_payload_validation_command"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_revision_overlay_jsonl_parse"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_revision_overlay_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_route_revision_overlay_resource_response_ledger_proposals"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_replan_handoff_alignment_edges"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_replan_handoff_seed_provenance_metadata"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_route_replan_handoff_row_0_seed_alignment_preservation"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_route_replan_handoff_row_0_seed_dag_preservation"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_replan_handoff_seed_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_route_replan_handoff_seed_schema_replan_metadata"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_replan_handoff_resource_feedback_count"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_route_revision_overlay_generic_formal_dag_fields"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_route_replan_handoff_generic_formal_dag_fields"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_replan_handoff_jsonl_parse"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_replan_handoff_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_replan_handoff_audit_alignment_checks"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_route_replan_handoff_audit_provenance_checks"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_route_replan_handoff_audit_roundtrip_trace_checks"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert audit_payload["n_optional_route_revision_overlay_row_schema_checked"] == 1
    assert audit_payload["n_optional_route_revision_overlay_row_schema_valid"] == 1
    assert audit_payload["n_optional_route_replan_handoff_row_schema_checked"] == 1
    assert audit_payload["n_optional_route_replan_handoff_row_schema_valid"] == 1
    assert audit_payload["n_optional_route_replan_handoff_seed_alignment_checked"] == 1
    assert audit_payload["n_optional_route_replan_handoff_seed_alignment_valid"] == 1
    assert audit_payload["n_optional_route_replan_handoff_seed_dag_checked"] == 1
    assert audit_payload["n_optional_route_replan_handoff_seed_dag_valid"] == 1
    assert audit_payload["n_optional_route_revision_generic_formal_dag_checked"] == 1
    assert audit_payload["n_optional_route_revision_generic_formal_dag_valid"] == 1
    assert audit_payload["n_optional_route_replan_handoff_generic_formal_dag_checked"] == 1
    assert audit_payload["n_optional_route_replan_handoff_generic_formal_dag_valid"] == 1
    assert audit_payload["n_optional_route_replan_handoff_audit_row_schema_checked"] == 6
    assert audit_payload["n_optional_route_replan_handoff_audit_row_schema_valid"] == 6
    assert any(
        row["check_name"]
        == "optional_route_replan_handoff_audit_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert audit_payload["n_optional_ablation_study_row_schema_checked"] == 1
    assert audit_payload["n_optional_ablation_study_row_schema_valid"] == 1
    assert (
        audit_payload["n_optional_ablation_study_route_adoption_manifest_checked"]
        == 1
    )
    assert audit_payload["n_optional_ablation_study_route_adoption_manifest_valid"] == 1
    assert audit_payload["n_optional_ablation_study_rows_with_route_adoption_metrics"] == 1
    assert (
        audit_payload[
            "optional_ablation_study_largest_route_adoption_ready_drop_variant"
        ]
        == "full_planner_observed"
    )
    assert any(
        row["check_name"] == "optional_ablation_study_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_ablation_study_route_adoption_manifest"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    ablation_manifest_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_ablation_study"
        / "formalization_gap_planner_ablation_study_manifest.json"
    )
    ablation_manifest_payload = json.loads(
        ablation_manifest_path.read_text(encoding="utf-8")
    )
    corrupted_ablation_manifest = json.loads(json.dumps(ablation_manifest_payload))
    corrupted_ablation_manifest[
        "largest_route_adoption_ready_drop_variant"
    ] = "no_route_planner"
    ablation_manifest_path.write_text(
        json.dumps(corrupted_ablation_manifest, indent=2),
        encoding="utf-8",
    )
    rejected_ablation_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_ablation_route_adoption_loss",
    )
    ablation_failed_names = {
        row["check_name"]
        for row in rejected_ablation_payload["checks"]
        if not row["ok"]
    }
    assert not rejected_ablation_payload["all_ok"]
    assert "optional_ablation_study_route_adoption_manifest" in ablation_failed_names
    assert (
        rejected_ablation_payload[
            "n_optional_ablation_study_route_adoption_manifest_valid"
        ]
        == 0
    )
    ablation_manifest_path.write_text(
        json.dumps(ablation_manifest_payload, indent=2),
        encoding="utf-8",
    )
    assert any(
        row["check_name"] == "component_resource_registry_required_components"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "component_resource_registry_execution_plans"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "component_resource_registry_execution_plan_jsonl"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "component_resource_registry_execution_plan_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "component_resource_registry_component_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "component_resource_registry_resource_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "component_resource_registry_contract_row_0_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "benchmark_audit_splits" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "standalone_example_valid" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "target_intake_example_normalizes" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "example_target_prover_coverage" and row["ok"]
        for row in audit_payload["checks"]
    )
    assert "not theorem proof evidence" in audit_payload["proof_evidence_boundary"]
    assert (
        audit_dir
        / "formalization_gap_planner_publication_bundle_audit_manifest.json"
    ).exists()

    evaluation_manifest_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_evaluation"
        / "formalization_gap_planner_evaluation_manifest.json"
    )
    evaluation_manifest_payload = json.loads(
        evaluation_manifest_path.read_text(encoding="utf-8")
    )
    corrupted_evaluation_manifest = json.loads(json.dumps(evaluation_manifest_payload))
    corrupted_evaluation_manifest["n_realization_missing_selected_formal_primitives"] = 0
    corrupted_evaluation_manifest["realization_missing_selected_formal_primitives"] = []
    corrupted_evaluation_manifest["realization_missing_primitives_by_route"] = []
    evaluation_manifest_path.write_text(
        json.dumps(corrupted_evaluation_manifest, indent=2),
        encoding="utf-8",
    )
    rejected_evaluation_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_evaluation_realization_missing_loss",
    )
    evaluation_failed_names = {
        row["check_name"]
        for row in rejected_evaluation_payload["checks"]
        if not row["ok"]
    }
    assert not rejected_evaluation_payload["all_ok"]
    assert "optional_evaluation_realization_missing_manifest" in evaluation_failed_names
    assert (
        rejected_evaluation_payload[
            "n_optional_evaluation_realization_missing_manifest_valid"
        ]
        == 0
    )
    evaluation_manifest_path.write_text(
        json.dumps(evaluation_manifest_payload, indent=2),
        encoding="utf-8",
    )

    bundle_manifest_path = (
        bundle_dir / "formalization_gap_planner_publication_bundle_manifest.json"
    )
    bundle_manifest_payload = json.loads(
        bundle_manifest_path.read_text(encoding="utf-8")
    )
    corrupted_bundle_manifest = json.loads(json.dumps(bundle_manifest_payload))
    corrupted_bundle_manifest["evaluation_summary"][
        "n_realization_omitted_cost_hint_primitives"
    ] = 0
    corrupted_bundle_manifest["evaluation_summary"][
        "realization_omitted_cost_hint_primitives"
    ] = []
    bundle_manifest_path.write_text(
        json.dumps(corrupted_bundle_manifest, indent=2),
        encoding="utf-8",
    )
    rejected_bundle_summary_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_bundle_evaluation_summary_loss",
    )
    bundle_summary_failed_names = {
        row["check_name"]
        for row in rejected_bundle_summary_payload["checks"]
        if not row["ok"]
    }
    assert not rejected_bundle_summary_payload["all_ok"]
    assert "bundle_evaluation_summary_consistent" in bundle_summary_failed_names
    bundle_manifest_path.write_text(
        json.dumps(bundle_manifest_payload, indent=2),
        encoding="utf-8",
    )

    corrupted_quality_control_manifest = json.loads(
        json.dumps(evaluation_manifest_payload)
    )
    corrupted_quality_control_manifest["n_rows_with_quality_controls"] = 0
    corrupted_quality_control_manifest["n_quality_control_fields"] = 0
    corrupted_quality_control_manifest["quality_control_fields"] = []
    corrupted_quality_control_manifest[
        "quality_control_resource_contract_ids"
    ] = []
    corrupted_quality_control_manifest[
        "quality_control_response_validation_signals"
    ] = []
    corrupted_quality_control_manifest["quality_control_stop_conditions"] = []
    corrupted_quality_control_manifest["evaluation_by_quality_control_field"] = {}
    evaluation_manifest_path.write_text(
        json.dumps(corrupted_quality_control_manifest, indent=2),
        encoding="utf-8",
    )
    rejected_quality_control_evaluation_payload = (
        audit_formalization_gap_planner_publication_bundle(
            bundle_dir,
            root / "audit_rejects_evaluation_quality_control_loss",
        )
    )
    quality_control_evaluation_failed_names = {
        row["check_name"]
        for row in rejected_quality_control_evaluation_payload["checks"]
        if not row["ok"]
    }
    assert not rejected_quality_control_evaluation_payload["all_ok"]
    assert (
        "optional_evaluation_quality_control_manifest"
        in quality_control_evaluation_failed_names
    )
    assert (
        rejected_quality_control_evaluation_payload[
            "n_optional_evaluation_quality_control_manifest_valid"
        ]
        == 0
    )
    evaluation_manifest_path.write_text(
        json.dumps(evaluation_manifest_payload, indent=2),
        encoding="utf-8",
    )

    corrupted_route_adoption_manifest = json.loads(
        json.dumps(evaluation_manifest_payload)
    )
    corrupted_route_adoption_manifest[
        "n_rows_pending_refinement_before_route_adoption"
    ] = 0
    corrupted_route_adoption_manifest["n_llm_route_adoption_blockers"] = 0
    corrupted_route_adoption_manifest["llm_route_adoption_blockers"] = []
    corrupted_route_adoption_manifest["evaluation_by_llm_route_adoption_status"] = {}
    evaluation_manifest_path.write_text(
        json.dumps(corrupted_route_adoption_manifest, indent=2),
        encoding="utf-8",
    )
    rejected_route_adoption_evaluation_payload = (
        audit_formalization_gap_planner_publication_bundle(
            bundle_dir,
            root / "audit_rejects_evaluation_route_adoption_loss",
        )
    )
    route_adoption_evaluation_failed_names = {
        row["check_name"]
        for row in rejected_route_adoption_evaluation_payload["checks"]
        if not row["ok"]
    }
    assert not rejected_route_adoption_evaluation_payload["all_ok"]
    assert (
        "optional_evaluation_route_adoption_manifest"
        in route_adoption_evaluation_failed_names
    )
    assert (
        rejected_route_adoption_evaluation_payload[
            "n_optional_evaluation_route_adoption_manifest_valid"
        ]
        == 0
    )
    evaluation_manifest_path.write_text(
        json.dumps(evaluation_manifest_payload, indent=2),
        encoding="utf-8",
    )

    evaluation_rows_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_evaluation"
        / "formalization_gap_planner_evaluation.jsonl"
    )
    evaluation_rows_payload = [
        json.loads(line)
        for line in evaluation_rows_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    corrupted_route_adoption_rows = json.loads(json.dumps(evaluation_rows_payload))
    corrupted_route_adoption_rows[0][
        "llm_route_planner_route_adoption_blockers"
    ] = [
        "search_requests_pending_evidence",
        "invented_route_adoption_blocker",
    ]
    corrupted_route_adoption_manifest = json.loads(
        json.dumps(evaluation_manifest_payload)
    )
    corrupted_route_adoption_manifest["llm_route_adoption_blockers"] = [
        "search_requests_pending_evidence",
        "invented_route_adoption_blocker",
    ]
    corrupted_route_adoption_manifest["rows"] = corrupted_route_adoption_rows
    evaluation_rows_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in corrupted_route_adoption_rows
        )
        + "\n",
        encoding="utf-8",
    )
    evaluation_manifest_path.write_text(
        json.dumps(corrupted_route_adoption_manifest, indent=2),
        encoding="utf-8",
    )
    rejected_route_adoption_blocker_payload = (
        audit_formalization_gap_planner_publication_bundle(
            bundle_dir,
            root / "audit_rejects_unknown_route_adoption_blocker",
        )
    )
    route_adoption_blocker_failed_names = {
        row["check_name"]
        for row in rejected_route_adoption_blocker_payload["checks"]
        if not row["ok"]
    }
    route_adoption_blocker_row_check = next(
        row
        for row in rejected_route_adoption_blocker_payload["checks"]
        if row["check_name"] == "optional_evaluation_row_0_route_adoption_fields"
    )
    assert not rejected_route_adoption_blocker_payload["all_ok"]
    assert (
        "optional_evaluation_row_0_route_adoption_fields"
        in route_adoption_blocker_failed_names
    )
    assert (
        "optional_evaluation_route_adoption_manifest"
        not in route_adoption_blocker_failed_names
    )
    assert (
        rejected_route_adoption_blocker_payload[
            "n_optional_evaluation_route_adoption_row_valid"
        ]
        == 0
    )
    assert (
        rejected_route_adoption_blocker_payload[
            "n_optional_evaluation_route_adoption_manifest_valid"
        ]
        == 1
    )
    assert any(
        "unknown llm route-adoption blockers: invented_route_adoption_blocker"
        in error
        for error in route_adoption_blocker_row_check["errors"]
    )
    evaluation_rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in evaluation_rows_payload)
        + "\n",
        encoding="utf-8",
    )
    evaluation_manifest_path.write_text(
        json.dumps(evaluation_manifest_payload, indent=2),
        encoding="utf-8",
    )

    route_adoption_taxonomy_path = (
        bundle_dir
        / "contract"
        / "formalization_gap_planner_route_adoption_blocker_taxonomy.json"
    )
    route_adoption_taxonomy_payload = json.loads(
        route_adoption_taxonomy_path.read_text(encoding="utf-8")
    )
    corrupted_route_adoption_taxonomy = json.loads(
        json.dumps(route_adoption_taxonomy_payload)
    )
    corrupted_route_adoption_taxonomy["blocker_values"] = [
        "search_requests_pending_evidence",
        "invented_route_adoption_blocker",
    ]
    corrupted_route_adoption_taxonomy["blocker_definitions"] = {
        "search_requests_pending_evidence": "fixture definition",
        "invented_route_adoption_blocker": "fixture definition",
    }
    route_adoption_taxonomy_path.write_text(
        json.dumps(corrupted_route_adoption_taxonomy, indent=2),
        encoding="utf-8",
    )
    rejected_taxonomy_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_stale_route_adoption_taxonomy",
    )
    taxonomy_failed_names = {
        row["check_name"]
        for row in rejected_taxonomy_payload["checks"]
        if not row["ok"]
    }
    assert not rejected_taxonomy_payload["all_ok"]
    assert "route_adoption_blocker_taxonomy_payload" in taxonomy_failed_names
    assert (
        "llm_route_planner_row_schema_route_adoption_blocker_enum_matches_taxonomy"
        in taxonomy_failed_names
    )
    route_adoption_taxonomy_path.write_text(
        json.dumps(route_adoption_taxonomy_payload, indent=2),
        encoding="utf-8",
    )

    seed_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_route_replan_handoff"
        / "formalization_gap_planner_route_replan_standalone_seed.json"
    )
    seed_payload = json.loads(seed_path.read_text(encoding="utf-8"))
    corrupted_seed = json.loads(json.dumps(seed_payload))
    corrupted_seed["routes"][0]["revised_informal_knowledge_dag_nodes"] = []
    corrupted_seed["routes"][0]["replan_metadata"][
        "revised_route_alignment_edges"
    ] = []
    seed_path.write_text(json.dumps(corrupted_seed, indent=2), encoding="utf-8")
    rejected_handoff_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_replan_seed_preservation_loss",
    )
    handoff_failed_names = {
        row["check_name"] for row in rejected_handoff_payload["checks"] if not row["ok"]
    }
    assert not rejected_handoff_payload["all_ok"]
    assert (
        "optional_route_replan_handoff_row_0_seed_alignment_preservation"
        in handoff_failed_names
    )
    assert (
        "optional_route_replan_handoff_row_0_seed_dag_preservation"
        in handoff_failed_names
    )
    assert (
        rejected_handoff_payload[
            "n_optional_route_replan_handoff_seed_alignment_valid"
        ]
        == 0
    )
    assert (
        rejected_handoff_payload["n_optional_route_replan_handoff_seed_dag_valid"]
        == 0
    )
    seed_path.write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")

    generic_loss_seed = json.loads(json.dumps(seed_payload))
    generic_loss_seed["routes"][0].pop("revised_formal_realization_dag_nodes", None)
    generic_loss_seed["routes"][0]["replan_metadata"].pop(
        "revised_formal_realization_dag_nodes",
        None,
    )
    seed_path.write_text(json.dumps(generic_loss_seed, indent=2), encoding="utf-8")
    rejected_generic_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_replan_generic_formal_dag_loss",
    )
    generic_failed_names = {
        row["check_name"] for row in rejected_generic_payload["checks"] if not row["ok"]
    }
    assert not rejected_generic_payload["all_ok"]
    assert (
        "optional_route_replan_handoff_generic_formal_dag_fields"
        in generic_failed_names
    )
    assert (
        rejected_generic_payload[
            "n_optional_route_replan_handoff_generic_formal_dag_valid"
        ]
        == 0
    )
    seed_path.write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")

    (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_evaluation"
        / "formalization_gap_planner_evaluation_ground_truth.json"
    ).write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "route_id": "route:does-not-match",
                        "required_primitives": ["rank_uniformity"],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    rejected_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_evaluation_truth",
    )
    failed_names = {
        row["check_name"] for row in rejected_payload["checks"] if not row["ok"]
    }
    assert not rejected_payload["all_ok"]
    assert "optional_evaluation_row_0_ground_truth_match" in failed_names
    assert rejected_payload["n_optional_evaluation_ground_truth_file_valid"] == 2
    assert rejected_payload["n_optional_evaluation_ground_truth_match_checked"] == 1
    assert rejected_payload["n_optional_evaluation_ground_truth_match_valid"] == 0
    assert rejected_payload["n_optional_evaluation_ground_truth_primitive_checked"] == 1
    assert rejected_payload["n_optional_evaluation_ground_truth_primitive_valid"] == 0

    (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_evaluation"
        / "formalization_gap_planner_evaluation_ground_truth.json"
    ).write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "route_id": "route:fixture",
                        "required_primitives": ["different_primitive"],
                        "actual_existing_reuse_primitives": [],
                        "actual_delta_primitives": ["different_primitive"],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    stale_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_stale_evaluation_truth",
    )
    stale_failed_names = {
        row["check_name"] for row in stale_payload["checks"] if not row["ok"]
    }
    assert not stale_payload["all_ok"]
    assert "optional_evaluation_row_0_ground_truth_primitives" in stale_failed_names
    assert stale_payload["n_optional_evaluation_ground_truth_file_valid"] == 2
    assert stale_payload["n_optional_evaluation_ground_truth_match_checked"] == 1
    assert stale_payload["n_optional_evaluation_ground_truth_match_valid"] == 1
    assert stale_payload["n_optional_evaluation_ground_truth_primitive_checked"] == 1
    assert stale_payload["n_optional_evaluation_ground_truth_primitive_valid"] == 0


def test_publication_bundle_audit_rejects_stale_resource_request_contract_maps() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_audit_request_contracts"
    )
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:fixture",
                "routes": [
                    {
                        "display_name": "rank route",
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir,
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )
    export_formalization_gap_planner_publication_bundle(
        bundle_dir,
        formalization_gap_planner_action_resource_plan_dir=action_resource_plan_dir,
        formalization_gap_planner_resource_request_queue_dir=request_queue_dir,
    )
    request_jsonl = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_resource_request_queue"
        / "formalization_gap_planner_resource_request_queue.jsonl"
    )
    rows = [
        json.loads(line)
        for line in request_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows[0]["response_contract_fields"] = ["stale_response_field"]
    rows[0]["request_payload"]["response_contract_fields"] = ["stale_response_field"]
    rows[0]["request_playbook"]["expected_response_fields"] = [
        "stale_response_field"
    ]
    rows[0]["request_payload"]["request_playbook"] = rows[0]["request_playbook"]
    request_jsonl.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        audit_dir,
    )

    failed_names = {row["check_name"] for row in payload["checks"] if not row["ok"]}
    assert not payload["all_ok"]
    assert payload["n_optional_resource_request_queue_row_schema_valid"] == payload[
        "n_optional_resource_request_queue_row_schema_checked"
    ]
    assert (
        payload["n_optional_resource_request_action_plan_ref_valid"]
        == payload["n_optional_resource_request_action_plan_ref_checked"]
    )
    assert (
        payload["n_optional_resource_request_payload_identity_valid"]
        == payload["n_optional_resource_request_payload_identity_checked"]
    )
    assert (
        payload["n_optional_resource_request_dispatch_spec_valid"]
        == payload["n_optional_resource_request_dispatch_spec_checked"]
    )
    assert any(
        row["check_name"]
        == "optional_resource_request_queue_row_0_request_payload_identity"
        and row["ok"]
        for row in payload["checks"]
    )
    assert (
        payload["n_optional_resource_request_contract_alignment_valid"]
        < payload["n_optional_resource_request_contract_alignment_checked"]
    )
    assert "optional_resource_request_queue_row_0_resource_contract_alignment" in failed_names


def test_publication_bundle_audit_rejects_stale_resource_response_contract_accounting() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_audit_response_contracts"
    )
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    response_ledger_dir = root / "response_ledger"
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:fixture",
                "routes": [
                    {
                        "display_name": "rank route",
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir,
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )
    export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        response_ledger_dir,
    )
    export_formalization_gap_planner_publication_bundle(
        bundle_dir,
        formalization_gap_planner_resource_request_queue_dir=request_queue_dir,
        formalization_gap_planner_resource_response_ledger_dir=response_ledger_dir,
    )
    ledger_jsonl = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_resource_response_ledger"
        / "formalization_gap_planner_resource_response_ledger.jsonl"
    )
    rows = [
        json.loads(line)
        for line in ledger_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows[0]["missing_response_contract_fields"] = []
    rows[0]["response_contract_minimum_met"] = True
    rows[0]["dispatch_spec"] = dict(rows[0]["dispatch_spec"])
    rows[0]["dispatch_spec"]["adapter_surface"] = "stale_adapter_surface"
    ledger_jsonl.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        audit_dir,
    )

    failed_names = {row["check_name"] for row in payload["checks"] if not row["ok"]}
    assert not payload["all_ok"]
    assert payload["n_optional_resource_response_ledger_row_schema_valid"] == payload[
        "n_optional_resource_response_ledger_row_schema_checked"
    ]
    assert (
        payload["n_optional_resource_response_request_ref_valid"]
        == payload["n_optional_resource_response_request_ref_checked"]
    )
    assert (
        payload["n_optional_resource_response_contract_field_accounting_valid"]
        < payload[
            "n_optional_resource_response_contract_field_accounting_checked"
        ]
    )
    assert (
        "optional_resource_response_ledger_row_0_contract_field_accounting"
        in failed_names
    )
    accounting_check = next(
        row
        for row in payload["checks"]
        if row["check_name"]
        == "optional_resource_response_ledger_row_0_contract_field_accounting"
    )
    assert "dispatch_spec mismatch" in "; ".join(accounting_check["errors"])
    assert "response_contract_minimum_met" in "; ".join(accounting_check["errors"])


def test_publication_bundle_audit_rejects_accepted_resource_response_without_playbook_grounding() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_audit_resource_response_playbook_grounding"
    )
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    response_ledger_dir = root / "response_ledger"
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:fixture",
                "routes": [
                    {
                        "display_name": "rank route",
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir,
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )
    export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        response_ledger_dir,
    )
    export_formalization_gap_planner_publication_bundle(
        bundle_dir,
        formalization_gap_planner_resource_request_queue_dir=request_queue_dir,
        formalization_gap_planner_resource_response_ledger_dir=response_ledger_dir,
    )
    ledger_jsonl = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_resource_response_ledger"
        / "formalization_gap_planner_resource_response_ledger.jsonl"
    )
    rows = [
        json.loads(line)
        for line in ledger_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    response_contract_fields = list(rows[0]["response_contract_fields"])
    assert response_contract_fields
    rows[0]["response_present"] = True
    rows[0]["response_contract_minimum_met"] = True
    rows[0]["response_contract_ok"] = True
    rows[0]["matched_response_contract_fields"] = [response_contract_fields[0]]
    rows[0]["missing_response_contract_fields"] = response_contract_fields[1:]
    rows[0]["acceptance_status"] = "ACCEPTED_RESOURCE_RESPONSE"
    rows[0]["request_playbook_present"] = True
    rows[0]["response_playbook_grounded"] = False
    rows[0]["response_playbook_grounding_terms"] = []
    ledger_jsonl.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        audit_dir,
    )

    failed_names = {row["check_name"] for row in payload["checks"] if not row["ok"]}
    assert not payload["all_ok"]
    assert payload["n_optional_resource_response_ledger_row_schema_valid"] == payload[
        "n_optional_resource_response_ledger_row_schema_checked"
    ]
    assert (
        "optional_resource_response_ledger_row_0_contract_field_accounting"
        in failed_names
    )
    accounting_check = next(
        row
        for row in payload["checks"]
        if row["check_name"]
        == "optional_resource_response_ledger_row_0_contract_field_accounting"
    )
    accounting_errors = "; ".join(accounting_check["errors"])
    assert "response_contract_ok requires response_playbook_grounded" in accounting_errors
    assert "accepted resource response requires response_playbook_grounded" in (
        accounting_errors
    )


def test_publication_bundle_audit_rejects_unaccepted_route_revision_ledger_feedback() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_audit_overlay_ledger_provenance"
    )
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    response_ledger_dir = root / "response_ledger"
    route_revision_overlay_dir = root / "route_revision_overlay"
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:fixture",
                "routes": [
                    {
                        "display_name": "rank route",
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir,
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )
    ledger_payload = export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        response_ledger_dir,
    )
    ledger_row = ledger_payload["rows"][0]
    ledger_id = ledger_row["resource_response_ledger_id"]
    resource_response_trace = {
        "resource_response_ledger_id": ledger_id,
        "resource_request_id": ledger_row["resource_request_id"],
        "action_resource_plan_id": ledger_row["action_resource_plan_id"],
        "primitive_action_id": ledger_row["primitive_action_id"],
        "coverage_map_id": ledger_row["coverage_map_id"],
        "goal_plan_id": ledger_row["goal_plan_id"],
        "route_id": ledger_row["route_id"],
        "primitive": ledger_row["primitive"],
        "target_primitives": ledger_row["target_primitives"],
        "resource_id": ledger_row["resource_id"],
        "request_phase": ledger_row["request_phase"],
        "expected_response_artifact": ledger_row["expected_response_artifact"],
        "acceptance_gate": ledger_row["acceptance_gate"],
        "dispatch_spec": ledger_row["dispatch_spec"],
        "response_present": ledger_row["response_present"],
        "response_contract_fields": ledger_row["response_contract_fields"],
        "response_contract_minimum_met": ledger_row["response_contract_minimum_met"],
        "response_contract_ok": ledger_row["response_contract_ok"],
        "acceptance_status": ledger_row["acceptance_status"],
        "matched_response_contract_fields": ledger_row[
            "matched_response_contract_fields"
        ],
        "missing_response_contract_fields": ledger_row[
            "missing_response_contract_fields"
        ],
        "response_artifacts": ledger_row["response_artifacts"],
        "route_revision_recommended": ledger_row["route_revision_recommended"],
        "prover_attempt_status": ledger_row["prover_attempt_status"],
        "prover_diagnostic_signature": ledger_row["prover_diagnostic_signature"],
        "proof_evidence_status": ledger_row["proof_evidence_status"],
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    route_revision_overlay_dir.mkdir(parents=True, exist_ok=True)
    overlay_row = {
        "schema_version": 2,
        "route_revision_overlay_id": "overlay:awaiting-ledger",
        "goal_plan_id": ledger_payload["rows"][0]["goal_plan_id"],
        "route_id": ledger_payload["rows"][0]["route_id"],
        "display_name": ledger_payload["rows"][0]["display_name"],
        "revision_status": "ROUTE_REVISION_APPLIED",
        "original_selected_primitives": ["rank_uniformity"],
        "revised_selected_primitives": ["rank_uniformity"],
        "added_primitives": [],
        "removed_primitives": [],
        "original_delta_primitives": ["rank_uniformity"],
        "revised_delta_primitives": ["rank_uniformity"],
        "added_delta_primitives": [],
        "applied_proposal_ids": ["proposal:awaiting-ledger"],
        "applied_refinement_evidence_ids": [f"resource_response_ledger:{ledger_id}"],
        "applied_hook_kinds": ["resource_response_ledger"],
        "applied_resource_response_traces": [resource_response_trace],
        "route_revision_reasons": ["awaiting ledger row should not be accepted"],
        "route_revision_summaries": ["invalid provenance fixture"],
        "source_refs": [],
        "lean_declaration_hits": [],
        "residual_goals": [],
        "applied_prover_attempt_statuses": [],
        "applied_prover_diagnostic_signatures": [],
        "revised_informal_knowledge_dag_nodes": [
            {
                "node_id": "informal:rank_uniformity",
                "label": "rank_uniformity",
                "primitive": "rank_uniformity",
            }
        ],
        "revised_lean_realization_dag_nodes": [
            {
                "node_id": "lean:rank_uniformity",
                "label": "rank_uniformity",
                "primitive": "rank_uniformity",
            }
        ],
        "revised_route_alignment_edges": [
            {
                "source": "informal:rank_uniformity",
                "target": "lean:rank_uniformity",
                "kind": "aligned_to_formal_realization_candidate",
                "primitive": "rank_uniformity",
                "alignment_status": "bridge_delta",
            }
        ],
        "unaligned_primitives": [],
        "next_required_gate": "rerun planner and prover replay",
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_ROUTE_REVISION_OVERLAY_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    (
        route_revision_overlay_dir
        / "formalization_gap_planner_route_revision_overlay_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_revision_overlay",
                "n_overlay_rows": 1,
                "n_row_schema_valid": 1,
                "n_row_schema_invalid": 0,
                "n_rows_with_alignment_contract": 1,
                "n_unaligned_primitives": 0,
                "n_resource_response_ledger_route_revision_proposals": 1,
                "all_ok": True,
                "rows": [overlay_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        route_revision_overlay_dir
        / "formalization_gap_planner_route_revision_overlay.jsonl"
    ).write_text(json.dumps(overlay_row, sort_keys=True) + "\n", encoding="utf-8")
    (
        route_revision_overlay_dir
        / "formalization_gap_planner_route_revision_overlay_row.schema.json"
    ).write_text(
        json.dumps(route_revision_overlay_row_json_schema(), indent=2),
        encoding="utf-8",
    )
    (
        route_revision_overlay_dir / "formalization_gap_planner_route_revision_overlay.md"
    ).write_text("# route revision overlay\nnot theorem proof evidence\n", encoding="utf-8")

    export_formalization_gap_planner_publication_bundle(
        bundle_dir,
        formalization_gap_planner_resource_request_queue_dir=request_queue_dir,
        formalization_gap_planner_resource_response_ledger_dir=response_ledger_dir,
        formalization_gap_planner_route_revision_overlay_dir=route_revision_overlay_dir,
    )
    payload = audit_formalization_gap_planner_publication_bundle(bundle_dir, audit_dir)

    failed_names = {row["check_name"] for row in payload["checks"] if not row["ok"]}
    assert not payload["all_ok"]
    assert (
        payload["n_optional_route_revision_resource_response_evidence_ref_valid"]
        < payload["n_optional_route_revision_resource_response_evidence_ref_checked"]
    )
    assert payload["n_optional_route_revision_resource_response_trace_checked"] == 1
    assert payload["n_optional_route_revision_resource_response_trace_valid"] == 1
    assert (
        "optional_route_revision_overlay_row_0_resource_response_evidence_refs"
        in failed_names
    )
    assert (
        "optional_route_revision_overlay_row_0_resource_response_traces"
        not in failed_names
    )


def test_publication_bundle_audit_rejects_stale_route_revision_resource_status() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_audit_overlay_resource_status"
    )
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    response_ledger_dir = root / "response_ledger"
    evidence_dir = root / "evidence"
    route_revision_overlay_dir = root / "route_revision_overlay"
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:fixture",
                "routes": [
                    {
                        "display_name": "rank route",
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir,
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )
    export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        response_ledger_dir,
    )
    (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(json.dumps({"route_revision_proposals": []}, indent=2), encoding="utf-8")
    export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        route_revision_overlay_dir,
        formalization_gap_planner_resource_response_ledger_dir=response_ledger_dir,
    )
    export_formalization_gap_planner_publication_bundle(
        bundle_dir,
        formalization_gap_planner_resource_request_queue_dir=request_queue_dir,
        formalization_gap_planner_resource_response_ledger_dir=response_ledger_dir,
        formalization_gap_planner_route_revision_overlay_dir=route_revision_overlay_dir,
    )
    overlay_jsonl = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_route_revision_overlay"
        / "formalization_gap_planner_route_revision_overlay.jsonl"
    )
    rows = [
        json.loads(line)
        for line in overlay_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows[0]["resource_response_summary"]["awaiting"] > 0
    rows[0]["resource_response_summary"]["awaiting"] = 0
    rows[0]["resource_response_awaiting_request_ids"] = []
    overlay_jsonl.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_publication_bundle(bundle_dir, audit_dir)

    failed_names = {row["check_name"] for row in payload["checks"] if not row["ok"]}
    assert not payload["all_ok"]
    assert payload["n_optional_route_revision_resource_response_status_checked"] == 1
    assert payload["n_optional_route_revision_resource_response_status_valid"] == 0
    assert (
        "optional_route_revision_overlay_row_0_resource_response_status_summary"
        in failed_names
    )
    status_check = next(
        row
        for row in payload["checks"]
        if row["check_name"]
        == "optional_route_revision_overlay_row_0_resource_response_status_summary"
    )
    status_errors = "; ".join(status_check["errors"])
    assert "resource_response_summary.awaiting mismatch" in status_errors
    assert "resource_response_awaiting_request_ids mismatch" in status_errors


def test_publication_bundle_audit_rejects_stale_route_stability_resource_status() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_audit_stability_resource_status"
    )
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    response_ledger_dir = root / "response_ledger"
    evidence_dir = root / "evidence"
    route_revision_overlay_dir = root / "route_revision_overlay"
    route_stability_dir = root / "route_stability"
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:fixture",
                "routes": [
                    {
                        "display_name": "rank route",
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir,
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )
    export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        response_ledger_dir,
    )
    (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(json.dumps({"rows": [], "route_revision_proposals": []}, indent=2), encoding="utf-8")
    export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        route_revision_overlay_dir,
        formalization_gap_planner_resource_response_ledger_dir=response_ledger_dir,
    )
    stability_payload = audit_formalization_gap_planner_route_stability(
        plan_dir,
        evidence_dir,
        route_revision_overlay_dir,
        route_stability_dir,
    )
    assert stability_payload["rows"][0]["stability_decision"] == (
        "AWAITING_REFINEMENT_RESPONSES"
    )
    export_formalization_gap_planner_publication_bundle(
        bundle_dir,
        formalization_gap_planner_resource_request_queue_dir=request_queue_dir,
        formalization_gap_planner_resource_response_ledger_dir=response_ledger_dir,
        formalization_gap_planner_route_revision_overlay_dir=route_revision_overlay_dir,
        formalization_gap_planner_route_stability_audit_dir=route_stability_dir,
    )
    stability_jsonl = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_route_stability_audit"
        / "formalization_gap_planner_route_stability_audit.jsonl"
    )
    rows = [
        json.loads(line)
        for line in stability_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows[0]["stability_decision"] = "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND"
    rows[0]["stable_under_current_evidence_bound"] = True
    rows[0]["awaiting_hook_kinds"] = []
    rows[0]["resource_response_awaiting_request_ids"] = []
    rows[0]["response_summary_by_hook"]["resource_response_ledger"]["awaiting"] = 0
    stability_jsonl.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_publication_bundle(bundle_dir, audit_dir)

    failed_names = {row["check_name"] for row in payload["checks"] if not row["ok"]}
    assert not payload["all_ok"]
    assert payload["n_optional_route_stability_resource_response_status_checked"] == 1
    assert payload["n_optional_route_stability_resource_response_status_valid"] == 0
    assert (
        "optional_route_stability_audit_row_0_resource_response_status_consistency"
        in failed_names
    )
    consistency_check = next(
        row
        for row in payload["checks"]
        if row["check_name"]
        == "optional_route_stability_audit_row_0_resource_response_status_consistency"
    )
    consistency_errors = "; ".join(consistency_check["errors"])
    assert "awaiting resource responses require AWAITING_REFINEMENT_RESPONSES" in (
        consistency_errors
    )
    assert "awaiting_hook_kinds missing resource_response_ledger" in consistency_errors
    assert "response_summary_by_hook resource awaiting count is stale" in (
        consistency_errors
    )
    assert "resource_response_awaiting_request_ids mismatch" in consistency_errors


def test_publication_bundle_audit_rejects_stale_interactive_resource_status() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_audit_interactive_resource_status"
    )
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    response_ledger_dir = root / "response_ledger"
    evidence_dir = root / "evidence"
    route_revision_overlay_dir = root / "route_revision_overlay"
    route_stability_dir = root / "route_stability"
    interactive_session_dir = root / "interactive_session"
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:fixture",
                "routes": [
                    {
                        "display_name": "rank route",
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)
    export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir,
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )
    export_formalization_gap_planner_resource_response_ledger(
        request_queue_dir,
        response_ledger_dir,
    )
    (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(json.dumps({"rows": [], "route_revision_proposals": []}, indent=2), encoding="utf-8")
    export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        route_revision_overlay_dir,
        formalization_gap_planner_resource_response_ledger_dir=response_ledger_dir,
    )
    audit_formalization_gap_planner_route_stability(
        plan_dir,
        evidence_dir,
        route_revision_overlay_dir,
        route_stability_dir,
    )
    interactive_payload = export_formalization_gap_planner_interactive_session(
        plan_dir,
        interactive_session_dir,
        formalization_gap_planner_route_stability_audit_dir=route_stability_dir,
        formalization_gap_planner_component_resource_registry_dir=(
            component_resource_registry_dir
        ),
    )
    assert interactive_payload["rows"][0]["resource_response_awaiting_request_ids"]
    export_formalization_gap_planner_publication_bundle(
        bundle_dir,
        formalization_gap_planner_resource_request_queue_dir=request_queue_dir,
        formalization_gap_planner_resource_response_ledger_dir=response_ledger_dir,
        formalization_gap_planner_route_revision_overlay_dir=route_revision_overlay_dir,
        formalization_gap_planner_route_stability_audit_dir=route_stability_dir,
        formalization_gap_planner_interactive_session_dir=interactive_session_dir,
    )
    interactive_jsonl = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_interactive_session"
        / "formalization_gap_planner_interactive_session.jsonl"
    )
    rows = [
        json.loads(line)
        for line in interactive_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows[0]["resource_response_awaiting_request_ids"] = []
    rows[0]["next_tools"] = []
    rows[0]["next_commands"] = []
    interactive_jsonl.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_publication_bundle(bundle_dir, audit_dir)

    failed_names = {row["check_name"] for row in payload["checks"] if not row["ok"]}
    assert not payload["all_ok"]
    assert payload["n_optional_interactive_session_resource_response_status_checked"] == 1
    assert payload["n_optional_interactive_session_resource_response_status_valid"] == 0
    assert (
        "optional_interactive_session_row_0_resource_response_status_consistency"
        in failed_names
    )
    consistency_check = next(
        row
        for row in payload["checks"]
        if row["check_name"]
        == "optional_interactive_session_row_0_resource_response_status_consistency"
    )
    consistency_errors = "; ".join(consistency_check["errors"])
    assert "resource_response_awaiting_request_ids mismatch" in consistency_errors
    assert "next_tools missing resource_response_ledger" in consistency_errors
    assert "next_commands missing resource_request_id=" in consistency_errors


def test_publication_bundle_audit_validates_interactive_policy_resource_links() -> None:
    root = Path("runs/test_formalization_gap_planner_publication_bundle_audit_interactive_links")
    bundle_dir = root / "bundle"
    shutil.rmtree(root, ignore_errors=True)
    export_formalization_gap_planner_publication_bundle(bundle_dir)

    contract_rows = [
        json.loads(line)
        for line in (
            bundle_dir
            / "component_resource_registry"
            / "formalization_gap_planner_component_resource_contracts.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    contract_id_by_resource = {
        str(row["resource_id"]): str(row["resource_contract_id"])
        for row in contract_rows
    }
    local_resource_ids = ["cross_prover_matrix_audit", "local_lake_lean"]
    frontier_resource_ids = ["lean_lsp_mcp"]
    linked_contract_ids = [
        contract_id_by_resource[resource_id]
        for resource_id in [*local_resource_ids, *frontier_resource_ids]
    ]
    policy_row = {
        "schema_version": 1,
        "decision_policy_row_id": "policy:interactive-links",
        "interactive_session_row_id": "session:interactive-links",
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
        "evidence_inputs": ["goal_conditioned_minimal_formalization_plan"],
        "required_tool_contracts": [
            "formalization_gap_planner_prover_adapter_packet.schema.json"
        ],
        "component_ids": [
            "cross_prover_public_reuse",
            "prover_feedback_refinement",
        ],
        "local_first_resource_ids": local_resource_ids,
        "frontier_escalation_resource_ids": frontier_resource_ids,
        "resource_contract_ids": linked_contract_ids,
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
    artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_interactive_session"
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_files = {
        "formalization_gap_planner_interactive_session_manifest.json": json.dumps(
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
        ),
        "formalization_gap_planner_interactive_session.jsonl": "",
        "formalization_gap_planner_interactive_session_row.schema.json": json.dumps(
            interactive_session_row_json_schema(),
            indent=2,
        ),
        "formalization_gap_planner_interactive_decision_policy.jsonl": (
            json.dumps(policy_row, sort_keys=True) + "\n"
        ),
        "formalization_gap_planner_interactive_decision_policy_row.schema.json": json.dumps(
            interactive_decision_policy_row_json_schema(),
            indent=2,
        ),
        "formalization_gap_planner_interactive_session.md": "# fixture\n",
    }
    copied_files: list[str] = []
    for filename, content in artifact_files.items():
        path = artifact_dir / filename
        path.write_text(content, encoding="utf-8")
        copied_files.append(str(path))
    bundle_manifest_path = (
        bundle_dir / "formalization_gap_planner_publication_bundle_manifest.json"
    )
    bundle_manifest = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
    bundle_manifest["optional_artifacts"] = [
        *bundle_manifest.get("optional_artifacts", []),
        {
            "artifact_name": "formalization_gap_planner_interactive_session",
            "requested": True,
            "source_dir": str(artifact_dir),
            "dest_dir": str(artifact_dir),
            "n_files_copied": len(copied_files),
            "copied_files": copied_files,
            "missing_files": [],
            "ok": True,
        },
    ]
    bundle_manifest_path.write_text(
        json.dumps(bundle_manifest, indent=2),
        encoding="utf-8",
    )

    audit_payload = audit_formalization_gap_planner_publication_bundle(bundle_dir)

    assert audit_payload["all_ok"]
    assert audit_payload["n_optional_interactive_decision_policy_link_checked"] == 4
    assert (
        audit_payload["n_optional_interactive_decision_policy_link_valid"]
        == audit_payload["n_optional_interactive_decision_policy_link_checked"]
    )
    assert any(
        row["check_name"]
        == "optional_interactive_decision_policy_row_0_resource_contract_coverage"
        and row["ok"]
        for row in audit_payload["checks"]
    )

    policy_row["resource_contract_ids"] = ["resource-contract:missing"]
    (
        artifact_dir / "formalization_gap_planner_interactive_decision_policy.jsonl"
    ).write_text(json.dumps(policy_row, sort_keys=True) + "\n", encoding="utf-8")
    rejected_payload = audit_formalization_gap_planner_publication_bundle(bundle_dir)
    failed_names = {
        row["check_name"] for row in rejected_payload["checks"] if not row["ok"]
    }
    assert not rejected_payload["all_ok"]
    assert (
        "optional_interactive_decision_policy_row_0_resource_contract_links"
        in failed_names
    )


def test_publication_bundle_audit_rejects_stale_generic_prover_fields() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_publication_bundle_audit_generic_prover_fields"
    )
    bundle_dir = root / "bundle"
    shutil.rmtree(root, ignore_errors=True)
    export_formalization_gap_planner_publication_bundle(bundle_dir)

    def register_optional_artifact(
        artifact_name: str,
        files: dict[str, str],
    ) -> None:
        artifact_dir = bundle_dir / "artifacts" / artifact_name
        artifact_dir.mkdir(parents=True, exist_ok=True)
        copied_files: list[str] = []
        for filename, content in files.items():
            path = artifact_dir / filename
            path.write_text(content, encoding="utf-8")
            copied_files.append(str(path))
        bundle_manifest_path = (
            bundle_dir / "formalization_gap_planner_publication_bundle_manifest.json"
        )
        bundle_manifest = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
        bundle_manifest["optional_artifacts"] = [
            *bundle_manifest.get("optional_artifacts", []),
            {
                "artifact_name": artifact_name,
                "requested": True,
                "source_dir": str(artifact_dir),
                "dest_dir": str(artifact_dir),
                "n_files_copied": len(copied_files),
                "copied_files": copied_files,
                "missing_files": [],
                "ok": True,
            },
        ]
        bundle_manifest_path.write_text(
            json.dumps(bundle_manifest, indent=2),
            encoding="utf-8",
        )

    route_stability_row = {
        "schema_version": 1,
        "route_stability_audit_id": "stability:generic-prover-regression",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "stability_decision": "EXPAND_PROOF_STATE_FEEDBACK",
        "stable_under_current_evidence_bound": False,
        "needs_more_literature": False,
        "needs_more_formal_grounding": False,
        "needs_more_lean_grounding": False,
        "needs_more_proof_state_feedback": True,
        "needs_route_replanning": False,
        "response_summary_by_hook": {},
        "awaiting_hook_kinds": [],
        "rejected_hook_kinds": [],
        "responded_hook_kinds": ["proof_state_feedback"],
        "resource_response_awaiting_request_ids": [],
        "resource_response_rejected_request_ids": [],
        "revision_status": "ROUTE_REVISION_APPLIED",
        "original_selected_primitives": [],
        "revised_selected_primitives": ["rank_uniformity"],
        "added_primitives": ["rank_uniformity"],
        "removed_primitives": [],
        "original_delta_primitives": [],
        "revised_delta_primitives": ["rank_uniformity"],
        "added_delta_primitives": ["rank_uniformity"],
        "new_primitives_since_plan": ["rank_uniformity"],
        "source_refs": ["fixture source"],
        "formal_declaration_hits": [],
        "lean_declaration_hits": [],
        "residual_goals": ["rank_uniformity"],
        "prover_attempt_statuses": ["local_lean_failed"],
        "prover_attempt_classes": [],
        "target_prover_families": [],
        "route_revision_reasons": ["proof-state feedback exposed missing bridge"],
        "stopping_rule_evidence": ["proof-state feedback requested"],
        "next_actions": ["repair target prover proof state"],
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_ROUTE_STABILITY_AUDIT_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    register_optional_artifact(
        "formalization_gap_planner_route_stability_audit",
        {
            "formalization_gap_planner_route_stability_audit_manifest.json": json.dumps(
                {
                    "schema_version": 1,
                    "component_name": "formalization_gap_planner_route_stability_audit",
                    "n_stability_rows": 1,
                    "n_row_schema_valid": 1,
                    "n_row_schema_invalid": 0,
                    "rows": [route_stability_row],
                    "proof_evidence_boundary": "not theorem proof evidence",
                },
                indent=2,
            ),
            "formalization_gap_planner_route_stability_audit.jsonl": (
                json.dumps(route_stability_row, sort_keys=True) + "\n"
            ),
            "formalization_gap_planner_route_stability_audit_row.schema.json": json.dumps(
                route_stability_audit_row_json_schema(),
                indent=2,
            ),
            "formalization_gap_planner_route_stability_audit.md": "# fixture\n",
        },
    )

    proof_state_triage_row = {
        "schema_version": 1,
        "triage_item_id": "triage:generic-prover-regression",
        "route_revision_overlay_id": "overlay:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "revision_status": "ROUTE_REVISION_APPLIED",
        "triage_class": "repair_local_lean_proof_state",
        "prover_triage_class": "repair_target_prover_proof_state",
        "owner_agent": "formal_verifier",
        "applied_prover_attempt_statuses": ["local_lean_failed"],
        "applied_prover_attempt_classes": [],
        "target_prover_families": [],
        "applied_prover_diagnostic_signatures": ["unsolved_goals"],
        "residual_goals": ["rank_uniformity"],
        "added_delta_primitives": ["rank_uniformity"],
        "recommended_next_action": "repair target prover proof state",
        "required_artifacts": ["target-prover proof-state response"],
        "recommended_tools": ["target prover LSP"],
        "execution_commands": ["replay target prover packet"],
        "priority_score": 90,
        "rank": 1,
        "required_gate": "target prover kernel verification",
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_PROOF_STATE_TRIAGE_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    register_optional_artifact(
        "formalization_gap_planner_proof_state_triage",
        {
            "formalization_gap_planner_proof_state_triage_manifest.json": json.dumps(
                {
                    "schema_version": 1,
                    "component_name": "formalization_gap_planner_proof_state_triage",
                    "n_triage_items": 1,
                    "n_row_schema_valid": 1,
                    "n_row_schema_invalid": 0,
                    "rows": [proof_state_triage_row],
                    "proof_evidence_boundary": "not theorem proof evidence",
                },
                indent=2,
            ),
            "formalization_gap_planner_proof_state_triage.jsonl": (
                json.dumps(proof_state_triage_row, sort_keys=True) + "\n"
            ),
            "formalization_gap_planner_proof_state_triage_row.schema.json": json.dumps(
                proof_state_triage_row_json_schema(),
                indent=2,
            ),
            "formalization_gap_planner_proof_state_triage.md": "# fixture\n",
        },
    )

    interactive_session_row = {
        "schema_version": 1,
        "interactive_session_row_id": "session:generic-prover-regression",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "route_class": "bridge_needed",
        "pareto_profile": "minimal-delta",
        "session_state": "EXPAND_PROOF_STATE_FEEDBACK",
        "next_interaction_kind": "proof_state_feedback",
        "next_owner_agent": "formal_verifier",
        "next_tools": ["target prover LSP"],
        "next_queries": [],
        "next_commands": ["replay target prover packet"],
        "user_checkpoint": "review target prover residuals",
        "evidence_summary": {"proof_state_feedback": 1},
        "coverage_summary": {"bridge_needed": 1},
        "stability_decision": "EXPAND_PROOF_STATE_FEEDBACK",
        "stable_under_current_evidence_bound": False,
        "needs_more_literature": False,
        "needs_more_formal_grounding": False,
        "needs_more_lean_grounding": False,
        "needs_more_proof_state_feedback": True,
        "needs_route_replanning": False,
        "awaiting_hook_kinds": [],
        "rejected_hook_kinds": [],
        "responded_hook_kinds": ["proof_state_feedback"],
        "resource_response_awaiting_request_ids": [],
        "resource_response_rejected_request_ids": [],
        "residual_goals": ["rank_uniformity"],
        "source_refs": ["fixture source"],
        "formal_declaration_hits": [],
        "lean_declaration_hits": [],
        "route_revision_reasons": ["proof-state feedback exposed missing bridge"],
        "triage_class": "repair_local_lean_proof_state",
        "prover_triage_class": "repair_target_prover_proof_state",
        "applied_prover_attempt_classes": ["target_prover_failed"],
        "target_prover_families": [],
        "triage_required_gate": "target prover kernel verification",
        "replan_required": False,
        "standalone_seed_route_id": "route:fixture",
        "route_cost": 1.0,
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    decision_policy_row = {
        "schema_version": 1,
        "decision_policy_row_id": "policy:generic-prover-regression",
        "interactive_session_row_id": "session:generic-prover-regression",
        "goal_plan_id": "goal:fixture",
        "route_id": "route:fixture",
        "display_name": "fixture route",
        "session_state": "EXPAND_PROOF_STATE_FEEDBACK",
        "next_interaction_kind": "proof_state_feedback",
        "decision_rationale": "route needs target prover feedback",
        "trigger_signals": ["prover_attempt_classes_present"],
        "evidence_inputs": ["prover_attempt_classes"],
        "required_tool_contracts": [],
        "component_ids": [],
        "local_first_resource_ids": [],
        "frontier_escalation_resource_ids": [],
        "resource_contract_ids": [],
        "required_quality_signals": ["proof_state_residuals_classified"],
        "quality_gates": ["proof_boundary_preserved"],
        "response_validation_signals": ["proof_boundary_preserved"],
        "stop_conditions": ["target prover replay attempted"],
        "fallback_actions": ["export prover adapter packets"],
        "bounded_evidence_claim": "not theorem proof evidence",
        "resource_selection_rationale": "fixture",
        "proof_evidence_status": (
            "FORMALIZATION_GAP_PLANNER_INTERACTIVE_SESSION_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": "not theorem proof evidence",
        "ok": True,
        "errors": [],
    }
    register_optional_artifact(
        "formalization_gap_planner_interactive_session",
        {
            "formalization_gap_planner_interactive_session_manifest.json": json.dumps(
                {
                    "schema_version": 1,
                    "component_name": "formalization_gap_planner_interactive_session",
                    "n_session_rows": 1,
                    "n_row_schema_valid": 1,
                    "n_row_schema_invalid": 0,
                    "n_decision_policy_rows": 1,
                    "n_decision_policy_row_schema_valid": 1,
                    "n_decision_policy_row_schema_invalid": 0,
                    "rows": [interactive_session_row],
                    "decision_policy_rows": [decision_policy_row],
                    "proof_evidence_boundary": "not theorem proof evidence",
                },
                indent=2,
            ),
            "formalization_gap_planner_interactive_session.jsonl": (
                json.dumps(interactive_session_row, sort_keys=True) + "\n"
            ),
            "formalization_gap_planner_interactive_session_row.schema.json": json.dumps(
                interactive_session_row_json_schema(),
                indent=2,
            ),
            "formalization_gap_planner_interactive_decision_policy.jsonl": (
                json.dumps(decision_policy_row, sort_keys=True) + "\n"
            ),
            "formalization_gap_planner_interactive_decision_policy_row.schema.json": json.dumps(
                interactive_decision_policy_row_json_schema(),
                indent=2,
            ),
            "formalization_gap_planner_interactive_session.md": "# fixture\n",
        },
    )

    payload = audit_formalization_gap_planner_publication_bundle(bundle_dir)

    failed_names = {row["check_name"] for row in payload["checks"] if not row["ok"]}
    assert not payload["all_ok"]
    assert payload["n_optional_route_stability_audit_row_schema_valid"] == 1
    assert payload["n_optional_proof_state_triage_row_schema_valid"] == 1
    assert payload["n_optional_interactive_session_row_schema_valid"] == 1
    assert payload["n_optional_route_stability_generic_prover_fields_checked"] == 1
    assert payload["n_optional_route_stability_generic_prover_fields_valid"] == 0
    assert payload["n_optional_proof_state_triage_generic_prover_fields_checked"] == 1
    assert payload["n_optional_proof_state_triage_generic_prover_fields_valid"] == 0
    assert payload["n_optional_interactive_session_generic_prover_fields_checked"] == 1
    assert payload["n_optional_interactive_session_generic_prover_fields_valid"] == 0
    assert "optional_route_stability_audit_row_0_generic_prover_fields" in failed_names
    assert "optional_proof_state_triage_row_0_generic_prover_fields" in failed_names
    assert "optional_interactive_session_row_0_generic_prover_fields" in failed_names


def test_publication_bundle_audit_checks_accepted_llm_seed_provenance() -> None:
    root = Path("runs/test_formalization_gap_planner_publication_bundle_audit_llm_seed")
    bundle_dir = root / "bundle"
    shutil.rmtree(root, ignore_errors=True)
    primary_llm_dir = _write_accepted_llm_route_planner_artifact(root / "primary_llm")
    feedback_llm_dir = _write_accepted_llm_route_planner_artifact(root / "feedback_llm")
    payload_validation_dir = _write_llm_payload_validation_from_route_planner_artifact(
        primary_llm_dir,
        root / "payload_validation",
    )

    export_formalization_gap_planner_publication_bundle(
        bundle_dir,
        formalization_gap_planner_llm_route_planner_dir=primary_llm_dir,
        formalization_gap_planner_feedback_llm_route_planner_dir=feedback_llm_dir,
        formalization_gap_planner_llm_route_planner_response_payload_validation_dir=(
            payload_validation_dir
        ),
    )
    audit_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit",
    )

    assert audit_payload["all_ok"]
    assert any(
        row["check_name"] == "optional_llm_route_planner_response_payload_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_llm_route_planner_response_payload_validation_manifest_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_llm_route_planner_response_payload_validation_row_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "llm_route_planner_response_payload_validation_manifest_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "llm_route_planner_response_payload_validation_row_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_feedback_llm_route_planner_response_payload_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert audit_payload["n_optional_llm_route_planner_seed_provenance_checked"] == 1
    assert audit_payload["n_optional_llm_route_planner_seed_provenance_valid"] == 1
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_manifest_contract_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_manifest_contract_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_count_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_count_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_request_bound_accounting_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_request_bound_accounting_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_request_bound_coverage_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_request_bound_coverage_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_row_schema_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_response_payload_validation_row_schema_valid"
        ]
        == 1
    )
    assert any(
        row["check_name"]
        == "optional_llm_route_planner_response_payload_validation_manifest_schema_valid"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_llm_route_planner_response_payload_validation_row_0_payload_schema_id"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_llm_route_planner_response_payload_validation_request_bound_coverage"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_seed_model_provenance_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_seed_model_provenance_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_seed_realization_witness_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_seed_realization_witness_valid"
        ]
        == 1
    )
    assert audit_payload["n_optional_llm_route_planner_seed_alignment_checked"] == 1
    assert audit_payload["n_optional_llm_route_planner_seed_alignment_valid"] == 1
    assert audit_payload["n_optional_llm_route_planner_seed_dag_checked"] == 1
    assert audit_payload["n_optional_llm_route_planner_seed_dag_valid"] == 1
    assert audit_payload["n_optional_llm_route_planner_seed_search_handoff_checked"] == 1
    assert audit_payload["n_optional_llm_route_planner_seed_search_handoff_valid"] == 1
    assert (
        audit_payload[
            "n_optional_llm_route_planner_seed_route_adoption_readiness_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_seed_route_adoption_readiness_valid"
        ]
        == 1
    )
    assert audit_payload["n_optional_llm_route_planner_generic_formal_dag_checked"] == 1
    assert audit_payload["n_optional_llm_route_planner_generic_formal_dag_valid"] == 1
    assert (
        audit_payload[
            "n_optional_llm_route_planner_realization_witness_schema_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_realization_witness_schema_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_request_evidence_bound_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_request_evidence_bound_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_request_registry_context_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_request_registry_context_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_request_target_intake_context_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_request_target_intake_context_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_request_model_tier_mismatch_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_llm_route_planner_request_model_tier_mismatch_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_provenance_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_provenance_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_model_provenance_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_model_provenance_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_realization_witness_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_realization_witness_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_alignment_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_alignment_valid"
        ]
        == 1
    )
    assert audit_payload["n_optional_feedback_llm_route_planner_seed_dag_checked"] == 1
    assert audit_payload["n_optional_feedback_llm_route_planner_seed_dag_valid"] == 1
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_search_handoff_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_search_handoff_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_route_adoption_readiness_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_seed_route_adoption_readiness_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_generic_formal_dag_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_generic_formal_dag_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_realization_witness_schema_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_realization_witness_schema_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_request_evidence_bound_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_request_evidence_bound_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_request_registry_context_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_request_registry_context_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_request_target_intake_context_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_request_target_intake_context_valid"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_request_model_tier_mismatch_checked"
        ]
        == 1
    )
    assert (
        audit_payload[
            "n_optional_feedback_llm_route_planner_request_model_tier_mismatch_valid"
        ]
        == 1
    )
    assert any(
        row["check_name"] == "optional_llm_route_planner_row_0_seed_provenance"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_llm_route_planner_row_0_seed_model_provenance"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_llm_route_planner_row_0_seed_realization_witness_preservation"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"] == "optional_llm_route_planner_request_0_registry_context"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_feedback_llm_route_planner_row_0_seed_provenance"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_feedback_llm_route_planner_row_0_seed_model_provenance"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_feedback_llm_route_planner_row_0_seed_realization_witness_preservation"
        and row["ok"]
        for row in audit_payload["checks"]
    )
    assert any(
        row["check_name"]
        == "optional_feedback_llm_route_planner_request_0_registry_context"
        and row["ok"]
        for row in audit_payload["checks"]
    )

    llm_artifact_dir = (
        bundle_dir / "artifacts" / "formalization_gap_planner_llm_route_planner"
    )
    rows_path = llm_artifact_dir / "formalization_gap_planner_llm_route_planner.jsonl"
    seed_path = (
        llm_artifact_dir
        / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
    )
    original_rows = [
        json.loads(line)
        for line in rows_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    original_seed = json.loads(seed_path.read_text(encoding="utf-8"))
    alias_corrupted_rows = json.loads(json.dumps(original_rows))
    alias_corrupted_seed = json.loads(json.dumps(original_seed))
    alias_corrupted_rows[0]["target_prover_family"] = "rocq"
    alias_corrupted_rows[0]["lean_realization_dag_nodes"] = list(
        alias_corrupted_rows[0]["formal_realization_dag_nodes"]
    )
    alias_corrupted_rows[0]["formal_realization_dag_nodes"] = []
    alias_corrupted_seed["target_prover_family"] = "rocq"
    seed_route = alias_corrupted_seed["routes"][0]
    seed_route["target_prover_family"] = "rocq"
    seed_route["revised_lean_realization_dag_nodes"] = list(
        seed_route["revised_formal_realization_dag_nodes"]
    )
    seed_route.pop("revised_formal_realization_dag_nodes", None)
    seed_metadata = seed_route["replan_metadata"]
    seed_metadata["target_prover_family"] = "rocq"
    seed_metadata["revised_lean_realization_dag_nodes"] = list(
        seed_metadata["revised_formal_realization_dag_nodes"]
    )
    seed_metadata.pop("revised_formal_realization_dag_nodes", None)
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in alias_corrupted_rows)
        + "\n",
        encoding="utf-8",
    )
    seed_path.write_text(json.dumps(alias_corrupted_seed, indent=2), encoding="utf-8")
    rejected_alias_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_non_lean_llm_lean_alias_seed_dag",
    )
    alias_failed_names = {
        row["check_name"] for row in rejected_alias_payload["checks"] if not row["ok"]
    }
    assert not rejected_alias_payload["all_ok"]
    assert (
        "optional_llm_route_planner_row_0_seed_dag_preservation"
        in alias_failed_names
    )
    assert (
        "optional_llm_route_planner_generic_formal_dag_fields"
        in alias_failed_names
    )
    assert rejected_alias_payload["n_optional_llm_route_planner_seed_dag_valid"] == 0
    assert (
        rejected_alias_payload[
            "n_optional_llm_route_planner_generic_formal_dag_valid"
        ]
        == 0
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in original_rows) + "\n",
        encoding="utf-8",
    )
    seed_path.write_text(json.dumps(original_seed, indent=2), encoding="utf-8")

    manifest_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatch_manifest = json.loads(json.dumps(manifest))
    mismatch_manifest["n_request_model_tier_mismatches"] = 1
    mismatch_manifest["request_model_tier_mismatches"] = [
        {
            "request_id": "formalization_gap_planner_llm_route_request:bad",
            "route_id": "rank_route",
            "provider_name": "anthropic",
            "model": "claude-sonnet-4-6",
            "model_tier": "haiku",
            "error": "expected Claude haiku tier but is configured with claude-sonnet-4-6",
        }
    ]
    manifest_path.write_text(json.dumps(mismatch_manifest, indent=2), encoding="utf-8")
    rejected_tier_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_route_planner_model_tier_mismatch",
    )
    tier_checks = [
        row
        for row in rejected_tier_payload["checks"]
        if row["check_name"]
        == "optional_llm_route_planner_request_model_tier_mismatch_policy"
    ]
    assert tier_checks
    assert not tier_checks[0]["ok"]
    assert any("model-tier mismatch" in error for error in tier_checks[0]["errors"])
    assert (
        rejected_tier_payload[
            "n_optional_llm_route_planner_request_model_tier_mismatch_valid"
        ]
        == 0
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    rows_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner.jsonl"
    )
    rows = [
        json.loads(line)
        for line in rows_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    cost_corrupted_rows = json.loads(json.dumps(rows))
    for field_name in (
        "cost_model_version",
        "route_cost",
        "primitive_costs",
        "and_or_cost_graph",
    ):
        cost_corrupted_rows[0]["minimal_delta_plan"].pop(field_name, None)
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in cost_corrupted_rows)
        + "\n",
        encoding="utf-8",
    )
    rejected_cost_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_minimal_delta_cost_loss",
    )
    cost_request_checks = [
        row
        for row in rejected_cost_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert cost_request_checks
    assert not cost_request_checks[0]["ok"]
    assert any("cost_model_version" in error for error in cost_request_checks[0]["errors"])
    assert any("route_cost" in error for error in cost_request_checks[0]["errors"])
    assert any("primitive_costs" in error for error in cost_request_checks[0]["errors"])
    assert any("and_or_cost_graph" in error for error in cost_request_checks[0]["errors"])
    assert (
        rejected_cost_payload[
            "n_optional_llm_route_planner_request_evidence_bound_valid"
        ]
        == 0
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    cost_dimension_corrupted_rows = json.loads(json.dumps(rows))
    cost_dimension_corrupted_rows[0]["minimal_delta_plan"]["primitive_costs"][0].pop(
        "reuse_credit"
    )
    rows_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True) for row in cost_dimension_corrupted_rows
        )
        + "\n",
        encoding="utf-8",
    )
    rejected_cost_dimension_payload = (
        audit_formalization_gap_planner_publication_bundle(
            bundle_dir,
            root / "audit_rejects_llm_minimal_delta_cost_dimension_loss",
        )
    )
    cost_dimension_checks = [
        row
        for row in rejected_cost_dimension_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert cost_dimension_checks
    assert not cost_dimension_checks[0]["ok"]
    assert any(
        "cost dimension fields missing: reuse_credit" in error
        for error in cost_dimension_checks[0]["errors"]
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    flat_graph_rows = json.loads(json.dumps(rows))
    flat_graph = flat_graph_rows[0]["minimal_delta_plan"]["and_or_cost_graph"]
    flat_graph.pop("or_nodes")
    flat_graph.pop("and_edges")
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in flat_graph_rows)
        + "\n",
        encoding="utf-8",
    )
    rejected_flat_graph_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_minimal_delta_flat_cost_graph",
    )
    flat_graph_checks = [
        row
        for row in rejected_flat_graph_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert flat_graph_checks
    assert not flat_graph_checks[0]["ok"]
    assert any(
        "and_or_cost_graph.or_nodes must be non-empty" in error
        for error in flat_graph_checks[0]["errors"]
    )
    assert any(
        "and_or_cost_graph.and_edges must be non-empty" in error
        for error in flat_graph_checks[0]["errors"]
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    search_obligation_corrupted_rows = json.loads(json.dumps(rows))
    rank_node = search_obligation_corrupted_rows[0]["informal_knowledge_dag_nodes"][0]
    rank_node["source_refs"] = []
    rank_node["source_snippets"] = []
    rank_node["source_search_status"] = "SEARCH_REQUESTED"
    search_obligation_corrupted_rows[0]["search_requests"] = []
    rows_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in search_obligation_corrupted_rows
        )
        + "\n",
        encoding="utf-8",
    )
    rejected_search_obligation_payload = (
        audit_formalization_gap_planner_publication_bundle(
            bundle_dir,
            root / "audit_rejects_llm_search_status_without_request",
        )
    )
    search_obligation_checks = [
        row
        for row in rejected_search_obligation_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert search_obligation_checks
    assert not search_obligation_checks[0]["ok"]
    assert any(
        "SEARCH_REQUESTED requires a matching literature/source search_request"
        in error
        for error in search_obligation_checks[0]["errors"]
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    formal_obligation_corrupted_rows = json.loads(json.dumps(rows))
    formal_node = formal_obligation_corrupted_rows[0]["formal_realization_dag_nodes"][0]
    formal_node["coverage_bucket"] = "unknown"
    formal_node["formalization_action"] = ""
    formal_node["candidate_declarations"] = []
    standalone_primitive = formal_obligation_corrupted_rows[0]["standalone_route"][
        "primitives"
    ][0]
    standalone_primitive["coverage_status"] = "unknown"
    standalone_primitive["candidate_declarations"] = []
    formal_obligation_corrupted_rows[0]["search_requests"] = []
    rows_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in formal_obligation_corrupted_rows
        )
        + "\n",
        encoding="utf-8",
    )
    rejected_formal_obligation_payload = (
        audit_formalization_gap_planner_publication_bundle(
            bundle_dir,
            root / "audit_rejects_llm_unknown_formal_without_search",
        )
    )
    formal_obligation_checks = [
        row
        for row in rejected_formal_obligation_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert formal_obligation_checks
    assert not formal_obligation_checks[0]["ok"]
    assert any(
        "unknown/formal-library-search-pending coverage requires a matching formal_library/library search_request"
        in error
        for error in formal_obligation_checks[0]["errors"]
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    malformed_search_request_rows = json.loads(json.dumps(rows))
    malformed_search_request_rows[0]["search_requests"] = [
        {
            "request_kind": "invented_tool_dispatch",
            "query": "",
            "reason": "",
        }
    ]
    rows_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in malformed_search_request_rows
        )
        + "\n",
        encoding="utf-8",
    )
    rejected_search_request_payload = (
        audit_formalization_gap_planner_publication_bundle(
            bundle_dir,
            root / "audit_rejects_llm_malformed_search_request",
        )
    )
    malformed_search_request_checks = [
        row
        for row in rejected_search_request_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert malformed_search_request_checks
    assert not malformed_search_request_checks[0]["ok"]
    assert any(
        "row search_requests[0].request_kind unsupported" in error
        for error in malformed_search_request_checks[0]["errors"]
    )
    assert any(
        "row search_requests[0].query missing" in error
        for error in malformed_search_request_checks[0]["errors"]
    )
    assert any(
        "row search_requests[0].reason missing" in error
        for error in malformed_search_request_checks[0]["errors"]
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    malformed_action_rows = json.loads(json.dumps(rows))
    malformed_action_rows[0]["planner_next_actions"] = [
        {
            "owner": "",
            "action": "",
        }
    ]
    rows_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in malformed_action_rows
        )
        + "\n",
        encoding="utf-8",
    )
    rejected_action_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_malformed_planner_action",
    )
    malformed_action_checks = [
        row
        for row in rejected_action_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert malformed_action_checks
    assert not malformed_action_checks[0]["ok"]
    assert any(
        "row planner_next_actions[0].owner missing" in error
        for error in malformed_action_checks[0]["errors"]
    )
    assert any(
        "row planner_next_actions[0].action missing" in error
        for error in malformed_action_checks[0]["errors"]
    )
    assert any(
        "row planner_next_actions[0] does not resolve to a supported hook family"
        in error
        for error in malformed_action_checks[0]["errors"]
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    corrupted_rows = json.loads(json.dumps(rows))
    corrupted_rows[0]["source_refs"].append("invented_source")
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in corrupted_rows) + "\n",
        encoding="utf-8",
    )
    rejected_evidence_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_request_evidence_loss",
    )
    failed_evidence_names = {
        row["check_name"]
        for row in rejected_evidence_payload["checks"]
        if not row["ok"]
    }
    assert not rejected_evidence_payload["all_ok"]
    assert (
        "optional_llm_route_planner_row_0_request_evidence_bound"
        in failed_evidence_names
    )
    assert (
        rejected_evidence_payload[
            "n_optional_llm_route_planner_request_evidence_bound_valid"
        ]
        == 0
    )
    assert (
        rejected_evidence_payload[
            "n_optional_feedback_llm_route_planner_request_evidence_bound_valid"
        ]
        == 1
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    requests_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_requests.jsonl"
    )
    requests = [
        json.loads(line)
        for line in requests_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    residual_goal = "rank_uniformity: missing hidden measurability side condition"
    residual_corrupted_rows = json.loads(json.dumps(rows))
    residual_corrupted_requests = json.loads(json.dumps(requests))
    residual_corrupted_requests[0]["residual_goals"] = [residual_goal]
    residual_corrupted_rows[0]["residual_interpretations"] = [
        {
            "residual_goal": residual_goal,
            "interpretation": "The proof-state residual exposes a hidden side condition.",
            "route_repair": "Add the hidden side condition to the route.",
        }
    ]
    residual_corrupted_rows[0]["search_requests"] = []
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in residual_corrupted_rows)
        + "\n",
        encoding="utf-8",
    )
    requests_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True) for row in residual_corrupted_requests
        )
        + "\n",
        encoding="utf-8",
    )
    rejected_residual_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_unsourced_residual_repair",
    )
    residual_checks = [
        row
        for row in rejected_residual_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert residual_checks
    assert not residual_checks[0]["ok"]
    assert any(
        "row residual_interpretations[0] route repair requires source_refs/source_snippets"
        in error
        for error in residual_checks[0]["errors"]
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    requests_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in requests) + "\n",
        encoding="utf-8",
    )

    corrupted_requests = json.loads(json.dumps(requests))
    corrupted_requests[0]["context_packet"].pop(
        "component_resource_registry_context",
        None,
    )
    requests_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in corrupted_requests)
        + "\n",
        encoding="utf-8",
    )
    rejected_registry_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_registry_context_loss",
    )
    failed_registry_names = {
        row["check_name"]
        for row in rejected_registry_payload["checks"]
        if not row["ok"]
    }
    assert not rejected_registry_payload["all_ok"]
    assert "optional_llm_route_planner_request_0_registry_context" in failed_registry_names
    assert (
        rejected_registry_payload[
            "n_optional_llm_route_planner_request_registry_context_valid"
        ]
        == 0
    )
    assert (
        rejected_registry_payload[
            "n_optional_feedback_llm_route_planner_request_registry_context_valid"
        ]
        == 1
    )
    requests_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in requests) + "\n",
        encoding="utf-8",
    )

    target_intake_corrupted_requests = json.loads(json.dumps(requests))
    target_intake_corrupted_requests[0]["context_packet"].pop(
        "target_intake_rows",
        None,
    )
    requests_path.write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in target_intake_corrupted_requests
        )
        + "\n",
        encoding="utf-8",
    )
    rejected_target_intake_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_target_intake_context_loss",
    )
    failed_target_intake_names = {
        row["check_name"]
        for row in rejected_target_intake_payload["checks"]
        if not row["ok"]
    }
    assert not rejected_target_intake_payload["all_ok"]
    assert (
        "optional_llm_route_planner_request_0_target_intake_context"
        in failed_target_intake_names
    )
    assert (
        rejected_target_intake_payload[
            "n_optional_llm_route_planner_request_target_intake_context_valid"
        ]
        == 0
    )
    assert (
        rejected_target_intake_payload[
            "n_optional_feedback_llm_route_planner_request_target_intake_context_valid"
        ]
        == 1
    )
    requests_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in requests) + "\n",
        encoding="utf-8",
    )

    dangling_alignment_rows = json.loads(json.dumps(rows))
    dangling_alignment_rows[0]["route_alignment_edges"][0][
        "formal_node_id"
    ] = "formal:missing_rank_uniformity_bridge"
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in dangling_alignment_rows)
        + "\n",
        encoding="utf-8",
    )
    rejected_dangling_alignment_payload = (
        audit_formalization_gap_planner_publication_bundle(
            bundle_dir,
            root / "audit_rejects_llm_dangling_alignment_endpoint",
        )
    )
    dangling_alignment_checks = [
        row
        for row in rejected_dangling_alignment_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert dangling_alignment_checks
    assert not dangling_alignment_checks[0]["ok"]
    assert any(
        "row route_alignment_edges[0] references unknown formal_node_id"
        in error
        for error in dangling_alignment_checks[0]["errors"]
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    primitive_corrupted_rows = json.loads(json.dumps(rows))
    primitive_corrupted_rows[0]["informal_knowledge_dag_nodes"].append(
        {
            "node_id": "informal:phantom_compactness",
            "claim": "A compactness lemma is needed for this rank route.",
            "depends_on": ["informal:rank_uniformity"],
            "source_refs": [],
            "source_search_status": "SEARCH_REQUESTED",
            "semantic_role": "lemma",
        }
    )
    phantom_formal_node = {
        "node_id": "formal:phantom_compactness_bridge",
        "primitive": "phantom_compactness",
        "coverage_bucket": "bridge",
        "candidate_declarations": [],
        "formalization_action": "prove_bridge",
    }
    primitive_corrupted_rows[0]["formal_realization_dag_nodes"].append(
        dict(phantom_formal_node)
    )
    primitive_corrupted_rows[0]["lean_realization_dag_nodes"].append(
        {
            **phantom_formal_node,
        }
    )
    primitive_corrupted_rows[0]["route_alignment_edges"].append(
        {
            "informal_node_id": "informal:phantom_compactness",
            "formal_node_id": "formal:phantom_compactness_bridge",
            "alignment_status": "bridge_needed",
            "alignment_rationale": "The unsupported row invents a new primitive.",
        }
    )
    primitive_corrupted_rows[0]["minimal_delta_plan"]["selected_primitives"].append(
        "phantom_compactness"
    )
    primitive_corrupted_rows[0]["minimal_delta_plan"]["bridge_lemmas"].append(
        "phantom_compactness"
    )
    primitive_corrupted_rows[0]["minimal_delta_plan"]["route_cost"] += 4
    primitive_corrupted_rows[0]["minimal_delta_plan"]["primitive_costs"].append(
        {
            "primitive": "phantom_compactness",
            "coverage_bucket": "bridge_needed",
            "base_cost": 4,
            "proof_difficulty_cost": 0,
            "import_cone_cost": 0,
            "definition_or_typeclass_cost": 0,
            "semantic_risk_cost": 0,
            "reuse_credit": 0,
            "total_cost": 4,
            "cost_rationale": "The corrupted fixture models this as a bridge lemma.",
        }
    )
    graph = primitive_corrupted_rows[0]["minimal_delta_plan"]["and_or_cost_graph"]
    for option in graph["route_options"]:
        option["route_cost"] += 4
        option["selected_primitives"].append("phantom_compactness")
    graph["and_edges"].append(
        {
            "route_option_id": graph["selected_route_option_id"],
            "requires": ["phantom_compactness"],
        }
    )
    primitive_corrupted_rows[0]["standalone_route"]["primitives"].append(
        {
            "primitive": "phantom_compactness",
            "coverage_status": "bridge_needed",
        }
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in primitive_corrupted_rows)
        + "\n",
        encoding="utf-8",
    )
    rejected_primitive_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_primitive_evidence_loss",
    )
    primitive_request_checks = [
        row
        for row in rejected_primitive_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_request_evidence_bound"
    ]
    assert primitive_request_checks
    assert not primitive_request_checks[0]["ok"]
    assert any(
        "introduced primitive requires aligned informal evidence" in error
        for error in primitive_request_checks[0]["errors"]
    )
    assert (
        rejected_primitive_payload[
            "n_optional_llm_route_planner_request_evidence_bound_valid"
        ]
        == 0
    )
    rows_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    seed_path = (
        bundle_dir
        / "artifacts"
        / "formalization_gap_planner_llm_route_planner"
        / "formalization_gap_planner_llm_route_planner_standalone_seed.json"
    )
    seed_payload = json.loads(seed_path.read_text(encoding="utf-8"))

    route_adoption_corrupted_seed = json.loads(json.dumps(seed_payload))
    route_adoption_corrupted_seed["routes"][0].pop(
        "llm_route_planner_route_adoption_status",
        None,
    )
    route_adoption_corrupted_seed["routes"][0][
        "llm_route_planner_route_adoption_blockers"
    ] = []
    route_adoption_corrupted_seed["routes"][0]["replan_metadata"].pop(
        "llm_route_planner_route_adoption_status",
        None,
    )
    route_adoption_corrupted_seed["routes"][0]["replan_metadata"][
        "llm_route_planner_route_adoption_blockers"
    ] = []
    seed_path.write_text(
        json.dumps(route_adoption_corrupted_seed, indent=2),
        encoding="utf-8",
    )
    rejected_route_adoption_payload = (
        audit_formalization_gap_planner_publication_bundle(
            bundle_dir,
            root / "audit_rejects_llm_seed_route_adoption_readiness_loss",
        )
    )
    route_adoption_checks = [
        row
        for row in rejected_route_adoption_payload["checks"]
        if row["check_name"]
        == "optional_llm_route_planner_row_0_seed_route_adoption_readiness"
    ]
    assert route_adoption_checks
    assert not route_adoption_checks[0]["ok"]
    assert any(
        "route_adoption_status" in error
        for error in route_adoption_checks[0]["errors"]
    )
    assert any(
        "route_adoption_blockers" in error
        for error in route_adoption_checks[0]["errors"]
    )
    assert (
        rejected_route_adoption_payload[
            "n_optional_llm_route_planner_seed_route_adoption_readiness_valid"
        ]
        == 0
    )
    seed_path.write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")

    search_handoff_corrupted_seed = json.loads(json.dumps(seed_payload))
    search_handoff_corrupted_seed["routes"][0]["interactive_refinement_hooks"] = []
    search_handoff_corrupted_seed["routes"][0]["route_revision_triggers"] = []
    search_handoff_corrupted_seed["routes"][0]["replan_metadata"][
        "llm_route_planner_search_requests"
    ] = []
    search_handoff_corrupted_seed["routes"][0]["replan_metadata"][
        "llm_route_planner_interactive_refinement_hooks"
    ] = []
    search_handoff_corrupted_seed["routes"][0]["replan_metadata"][
        "llm_route_planner_route_revision_triggers"
    ] = []
    seed_path.write_text(
        json.dumps(search_handoff_corrupted_seed, indent=2),
        encoding="utf-8",
    )
    rejected_search_handoff_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_seed_search_handoff_loss",
    )
    search_handoff_checks = [
        row
        for row in rejected_search_handoff_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_seed_search_handoff"
    ]
    assert search_handoff_checks
    assert not search_handoff_checks[0]["ok"]
    assert any("search_requests" in error for error in search_handoff_checks[0]["errors"])
    assert any("interactive_refinement_hooks" in error for error in search_handoff_checks[0]["errors"])
    assert any("route_revision_triggers" in error for error in search_handoff_checks[0]["errors"])
    assert (
        rejected_search_handoff_payload[
            "n_optional_llm_route_planner_seed_search_handoff_valid"
        ]
        == 0
    )
    seed_path.write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")

    graph_corrupted_seed = json.loads(json.dumps(seed_payload))
    graph_corrupted_seed["routes"][0].pop("minimal_delta_and_or_cost_graph", None)
    graph_corrupted_seed["routes"][0]["replan_metadata"].pop(
        "minimal_delta_and_or_cost_graph",
        None,
    )
    seed_path.write_text(json.dumps(graph_corrupted_seed, indent=2), encoding="utf-8")
    rejected_graph_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_seed_cost_graph_loss",
    )
    graph_provenance_checks = [
        row
        for row in rejected_graph_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_seed_provenance"
    ]
    assert graph_provenance_checks
    assert not graph_provenance_checks[0]["ok"]
    assert any(
        "minimal_delta_and_or_cost_graph" in error
        for error in graph_provenance_checks[0]["errors"]
    )
    assert (
        rejected_graph_payload[
            "n_optional_llm_route_planner_seed_provenance_valid"
        ]
        == 0
    )
    seed_path.write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")

    generic_corrupted_seed = json.loads(json.dumps(seed_payload))
    generic_corrupted_seed["routes"][0].pop(
        "revised_formal_realization_dag_nodes",
        None,
    )
    generic_corrupted_seed["routes"][0]["replan_metadata"].pop(
        "revised_formal_realization_dag_nodes",
        None,
    )
    seed_path.write_text(
        json.dumps(generic_corrupted_seed, indent=2),
        encoding="utf-8",
    )
    rejected_generic_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_generic_formal_dag_loss",
    )
    generic_checks = [
        row
        for row in rejected_generic_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_generic_formal_dag_fields"
    ]
    assert generic_checks
    assert not generic_checks[0]["ok"]
    assert (
        rejected_generic_payload[
            "n_optional_llm_route_planner_generic_formal_dag_valid"
        ]
        == 0
    )
    seed_path.write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")

    model_corrupted_seed = json.loads(json.dumps(seed_payload))
    model_corrupted_metadata = model_corrupted_seed["routes"][0]["replan_metadata"]
    model_corrupted_metadata["llm_route_planner_model_tier"] = "haiku"
    model_corrupted_metadata["llm_route_planner_generator_metadata"] = {}
    model_corrupted_metadata["llm_route_planner_generator_metadata_keys"] = []
    seed_path.write_text(
        json.dumps(model_corrupted_seed, indent=2),
        encoding="utf-8",
    )
    rejected_model_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_seed_model_provenance_loss",
    )
    model_provenance_checks = [
        row
        for row in rejected_model_payload["checks"]
        if row["check_name"] == "optional_llm_route_planner_row_0_seed_model_provenance"
    ]
    assert model_provenance_checks
    assert not model_provenance_checks[0]["ok"]
    assert any("model_tier" in error for error in model_provenance_checks[0]["errors"])
    assert any(
        "generator_metadata" in error for error in model_provenance_checks[0]["errors"]
    )
    assert (
        rejected_model_payload[
            "n_optional_llm_route_planner_seed_model_provenance_valid"
        ]
        == 0
    )
    seed_path.write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")

    corrupted_seed = json.loads(json.dumps(seed_payload))
    corrupted_seed["routes"][0]["replan_metadata"][
        "llm_route_planner_row_id"
    ] = "wrong-row-id"
    corrupted_seed["routes"][0].pop("realization_coverage_witness", None)
    corrupted_seed["routes"][0]["replan_metadata"].pop(
        "llm_route_planner_realization_coverage_witness",
        None,
    )
    corrupted_seed["routes"][0]["revised_route_alignment_edges"] = []
    corrupted_seed["routes"][0]["revised_informal_knowledge_dag_nodes"] = []
    seed_path.write_text(json.dumps(corrupted_seed, indent=2), encoding="utf-8")

    rejected_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        root / "audit_rejects_llm_seed_loss",
    )
    failed_names = {
        row["check_name"] for row in rejected_payload["checks"] if not row["ok"]
    }

    assert not rejected_payload["all_ok"]
    assert "optional_llm_route_planner_row_0_seed_provenance" in failed_names
    assert (
        "optional_llm_route_planner_row_0_seed_realization_witness_preservation"
        in failed_names
    )
    assert (
        "optional_llm_route_planner_row_0_seed_alignment_preservation"
        in failed_names
    )
    assert "optional_llm_route_planner_row_0_seed_dag_preservation" in failed_names
    assert rejected_payload["n_optional_llm_route_planner_seed_provenance_valid"] == 0
    assert (
        rejected_payload[
            "n_optional_llm_route_planner_seed_realization_witness_valid"
        ]
        == 0
    )
    assert rejected_payload["n_optional_llm_route_planner_seed_alignment_valid"] == 0
    assert rejected_payload["n_optional_llm_route_planner_seed_dag_valid"] == 0
    assert (
        rejected_payload[
            "n_optional_feedback_llm_route_planner_seed_provenance_valid"
        ]
        == 1
    )
    assert (
        rejected_payload[
            "n_optional_feedback_llm_route_planner_seed_realization_witness_valid"
        ]
        == 1
    )


def test_publication_bundle_audit_rejects_schema_mismatch() -> None:
    root = Path("runs/test_formalization_gap_planner_publication_bundle_audit_rejects")
    bundle_dir = root / "bundle"
    shutil.rmtree(root, ignore_errors=True)
    export_formalization_gap_planner_publication_bundle(bundle_dir)
    manifest_path = bundle_dir / "formalization_gap_planner_publication_bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["portable_schema_id"] = "urn:wrong:schema"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    execution_plan_jsonl_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_execution_plans.jsonl"
    )
    execution_plan_rows = [
        json.loads(line)
        for line in execution_plan_jsonl_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    execution_plan_rows[0].pop("stop_conditions", None)
    execution_plan_jsonl_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in execution_plan_rows) + "\n",
        encoding="utf-8",
    )
    resource_contract_jsonl_path = (
        bundle_dir
        / "component_resource_registry"
        / "formalization_gap_planner_component_resource_contracts.jsonl"
    )
    resource_contract_rows = [
        json.loads(line)
        for line in resource_contract_jsonl_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    resource_contract_rows[0].pop("response_contract_fields", None)
    resource_contract_jsonl_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in resource_contract_rows)
        + "\n",
        encoding="utf-8",
    )

    audit_payload = audit_formalization_gap_planner_publication_bundle(bundle_dir)

    assert not audit_payload["all_ok"]
    failed_names = {
        row["check_name"]
        for row in audit_payload["checks"]
        if not row["ok"]
    }
    assert "portable_schema_id" in failed_names
    assert "component_resource_registry_execution_plan_row_0_schema_valid" in failed_names
    assert "component_resource_registry_contract_row_0_schema_valid" in failed_names


def test_publication_bundle_audit_rejects_llm_reproduction_without_registry_context() -> None:
    root = Path(
        "runs/"
        "test_formalization_gap_planner_publication_bundle_audit_rejects_llm_repro"
    )
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    export_formalization_gap_planner_publication_bundle(bundle_dir)

    manifest_path = (
        bundle_dir
        / "reproduce"
        / "formalization_gap_planner_reproduction_manifest.json"
    )
    reproduction_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    registry_flag = "--formalization-gap-planner-component-resource-registry-dir"

    def _without_flag_value(command: str, flag: str) -> str:
        tokens = command.split()
        rewritten: list[str] = []
        skip_next = False
        for token in tokens:
            if skip_next:
                skip_next = False
                continue
            if token == flag:
                skip_next = True
                continue
            rewritten.append(token)
        return " ".join(rewritten)

    corrupted_command_names = {
        "run_llm_route_planner",
        "run_feedback_llm_route_planner",
    }
    for row in reproduction_payload["commands"]:
        if row["name"] in corrupted_command_names:
            row["command"] = _without_flag_value(row["command"], registry_flag)
            assert registry_flag not in row["command"]

    manifest_path.write_text(
        json.dumps(reproduction_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    audit_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        audit_dir,
    )
    failed_names = {
        row["check_name"] for row in audit_payload["checks"] if not row["ok"]
    }

    assert not audit_payload["all_ok"]
    assert "reproduction_llm_route_planner_command" in failed_names
    assert "reproduction_feedback_llm_route_planner_command" in failed_names


def test_publication_bundle_audit_rejects_llm_reproduction_without_target_intake_context() -> None:
    root = Path(
        "runs/"
        "test_formalization_gap_planner_publication_bundle_audit_rejects_llm_repro_target_intake"
    )
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    export_formalization_gap_planner_publication_bundle(bundle_dir)

    manifest_path = (
        bundle_dir
        / "reproduce"
        / "formalization_gap_planner_reproduction_manifest.json"
    )
    reproduction_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    target_intake_flag = "--formalization-gap-planner-target-intake-dir"

    def _without_flag_value(command: str, flag: str) -> str:
        tokens = command.split()
        rewritten: list[str] = []
        skip_next = False
        for token in tokens:
            if skip_next:
                skip_next = False
                continue
            if token == flag:
                skip_next = True
                continue
            rewritten.append(token)
        return " ".join(rewritten)

    corrupted_command_names = {
        "run_llm_route_planner",
        "run_feedback_llm_route_planner",
    }
    for row in reproduction_payload["commands"]:
        if row["name"] in corrupted_command_names:
            row["command"] = _without_flag_value(row["command"], target_intake_flag)
            assert target_intake_flag not in row["command"]

    manifest_path.write_text(
        json.dumps(reproduction_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    audit_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        audit_dir,
    )
    failed_names = {
        row["check_name"] for row in audit_payload["checks"] if not row["ok"]
    }

    assert not audit_payload["all_ok"]
    assert "reproduction_llm_route_planner_command" in failed_names
    assert "reproduction_feedback_llm_route_planner_command" in failed_names


def test_publication_bundle_audit_rejects_live_reuse_smoke_reproduction_commands() -> None:
    root = Path(
        "runs/"
        "test_formalization_gap_planner_publication_bundle_audit_rejects_live_reuse_smoke"
    )
    bundle_dir = root / "bundle"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    export_formalization_gap_planner_publication_bundle(bundle_dir)

    manifest_path = (
        bundle_dir
        / "reproduce"
        / "formalization_gap_planner_reproduction_manifest.json"
    )
    reproduction_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    for row in reproduction_payload["commands"]:
        if row["name"] == "run_reuse_smoke":
            row["command"] += " --llm-route-planner-invoke-provider"
        if row["name"] == "run_runtime_handoff_reuse_smoke":
            row["command"] += " --feedback-llm-route-planner-invoke-provider"

    manifest_path.write_text(
        json.dumps(reproduction_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    audit_payload = audit_formalization_gap_planner_publication_bundle(
        bundle_dir,
        audit_dir,
    )
    failed_names = {
        row["check_name"] for row in audit_payload["checks"] if not row["ok"]
    }

    assert not audit_payload["all_ok"]
    assert "reproduction_reuse_smoke_command" in failed_names
    assert "reproduction_runtime_handoff_reuse_smoke_command" in failed_names

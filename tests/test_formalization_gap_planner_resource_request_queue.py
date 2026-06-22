from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_action_resource_plan import (
    export_formalization_gap_planner_action_resource_plan,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    export_formalization_gap_planner_component_resource_registry,
)
from ai_statistician.formalization_gap_planner_library_coverage_map import (
    export_formalization_gap_planner_library_coverage_map,
)
from ai_statistician.formalization_gap_planner_primitive_action_queue import (
    export_formalization_gap_planner_primitive_action_queue,
)
from ai_statistician.formalization_gap_planner_llm_route_planner import (
    export_formalization_gap_planner_llm_route_planner,
)
from ai_statistician.formalization_gap_planner_resource_request_queue import (
    RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID,
    export_formalization_gap_planner_resource_request_queue,
    resource_request_queue_row_json_schema,
    validate_resource_request_queue_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_resource_request_queue_expands_action_resources_to_dispatch_packets() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_request_queue")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "routes": [
                    {
                        "display_name": "distribution_free_rank_bound",
                        "theorem_statement": (
                            "A distribution-free rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "replan_metadata": {
                            "llm_route_planner_minimal_delta_plan": {
                                "bridge_lemmas": [
                                    (
                                        "rank_uniformity: prove finite rank "
                                        "uniformity from exchangeability"
                                    )
                                ],
                                "source_port_lemmas": [
                                    (
                                        "coverage_inequality: port the "
                                        "source-backed coverage inequality"
                                    )
                                ],
                            }
                        },
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            },
                            {
                                "primitive": "coverage_inequality",
                                "coverage_status": "source_port_needed",
                                "source_refs": ["vovk_gammerman_shafer"],
                            },
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
        component_resource_registry_dir
    )
    action_payload = export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )

    payload = export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )

    assert payload["all_ok"]
    assert (
        payload["n_action_resource_plan_rows"]
        == action_payload["n_resource_plan_rows"]
        == 3
    )
    assert payload["n_resource_request_rows"] > action_payload["n_resource_plan_rows"]
    assert payload["n_ok"] == payload["n_resource_request_rows"]
    assert payload["n_failed"] == 0
    assert payload["n_local_first_requests"] > 0
    assert payload["n_frontier_escalation_requests"] > 0
    assert payload["n_distinct_resources"] >= 5
    assert (
        payload["n_self_contained_request_payloads"]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_request_payload_identity_mismatches"] == 0
    assert payload["n_with_request_playbooks"] == payload["n_resource_request_rows"]
    assert (
        payload["n_request_playbook_identity_valid"]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_request_playbook_identity_mismatches"] == 0
    assert payload["n_with_candidate_declaration_rows"] > 0
    assert payload["n_candidate_declaration_rows"] == payload[
        "n_with_candidate_declaration_rows"
    ]
    assert payload["n_with_actionable_work_items"] > 0
    assert payload["n_actionable_work_items"] > 0
    assert payload["n_minimal_delta_reuse_ready"] > 0
    assert payload["n_minimal_delta_light_bridge_or_wrapper"] > 0
    assert payload["n_minimal_delta_source_or_new_theory"] > 0
    assert payload["n_minimal_delta_alignment_blocked"] == 0
    assert payload["average_reuse_readiness_score"] > 0
    assert payload["average_evidence_readiness_score"] > 0
    assert payload["n_row_schema_valid"] == payload["n_resource_request_rows"]
    assert payload["n_row_schema_invalid"] == 0
    assert (
        payload["resource_request_queue_row_schema"]["$id"]
        == RESOURCE_REQUEST_QUEUE_ROW_SCHEMA_ID
    )
    assert "actionable_work_items" in payload[
        "resource_request_queue_row_schema"
    ]["required"]
    assert "minimal_delta_cost_score" in payload[
        "resource_request_queue_row_schema"
    ]["required"]
    assert "reuse_readiness_score" in payload[
        "resource_request_queue_row_schema"
    ]["required"]
    assert "evidence_readiness_score" in payload[
        "resource_request_queue_row_schema"
    ]["required"]
    assert "priority_rationale" in payload[
        "resource_request_queue_row_schema"
    ]["required"]
    rows = payload["rows"]
    assert rows
    exact_rows = [
        row for row in rows if row["queue_action_kind"] == "target_prover_replay"
    ]
    assert exact_rows
    exact_row = exact_rows[0]
    assert exact_row["minimal_delta_cost_score"] == 0
    assert exact_row["reuse_readiness_score"] == 100
    assert exact_row["evidence_readiness_score"] == 75
    assert (
        exact_row["request_payload"]["minimal_delta_cost_score"]
        == exact_row["minimal_delta_cost_score"]
    )
    assert (
        exact_row["request_payload"]["reuse_readiness_score"]
        == exact_row["reuse_readiness_score"]
    )
    assert (
        exact_row["request_payload"]["evidence_readiness_score"]
        == exact_row["evidence_readiness_score"]
    )
    assert (
        tuple(exact_row["request_payload"]["priority_rationale"])
        == tuple(exact_row["priority_rationale"])
    )
    assert exact_row["candidate_declaration_rows"] == (
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "candidate_declarations",
        },
    )
    assert (
        exact_row["request_payload"]["candidate_declaration_rows"]
        == exact_row["candidate_declaration_rows"]
    )
    source_rows = [
        row for row in rows if row["queue_action_kind"] == "source_port"
    ]
    assert any(row["resource_id"] == "local_literature_corpus" for row in source_rows)
    assert any(row["resource_id"] == "paperclip_cli_mcp" for row in source_rows)
    assert any(
        row["expected_response_artifact"]
        == "literature_or_source_grounding_response"
        for row in source_rows
    )
    bridge_rows = [
        row for row in rows if row["queue_action_kind"] == "prove_bridge_lemma"
    ]
    assert payload["n_minimal_delta_reuse_ready"] == len(exact_rows)
    assert payload["n_minimal_delta_light_bridge_or_wrapper"] == len(bridge_rows)
    assert payload["n_minimal_delta_source_or_new_theory"] == len(source_rows)
    lean_lsp_row = next(
        row for row in bridge_rows if row["resource_id"] == "lean_lsp_mcp"
    )
    assert lean_lsp_row["minimal_delta_cost_score"] == 40
    assert lean_lsp_row["reuse_readiness_score"] == 70
    assert lean_lsp_row["evidence_readiness_score"] == 75
    assert (
        lean_lsp_row["request_payload"]["minimal_delta_cost_score"]
        == lean_lsp_row["minimal_delta_cost_score"]
    )
    assert lean_lsp_row["request_phase"] == "frontier_escalation"
    assert (
        lean_lsp_row["expected_response_artifact"]
        == "proof_state_or_prover_feedback_response"
    )
    assert "target-prover LSP" in lean_lsp_row["mcp_or_cli_hint"]
    assert lean_lsp_row["dispatch_spec"]["dispatch_kind"] == "frontier_mcp_or_cli"
    assert lean_lsp_row["dispatch_spec"]["adapter_surface"] == "target_prover_lsp_mcp"
    assert (
        lean_lsp_row["dispatch_spec"]["execution_command"]
        == lean_lsp_row["execution_command"]
    )
    assert (
        lean_lsp_row["request_payload"]["dispatch_spec"]
        == lean_lsp_row["dispatch_spec"]
    )
    assert (
        lean_lsp_row["request_payload"]["request_playbook"]
        == lean_lsp_row["request_playbook"]
    )
    assert (
        lean_lsp_row["request_playbook"]["resource_request_id"]
        == lean_lsp_row["resource_request_id"]
    )
    assert (
        lean_lsp_row["request_playbook"]["expected_response_artifact"]
        == lean_lsp_row["expected_response_artifact"]
    )
    assert "rank_uniformity" in lean_lsp_row["request_playbook"]["operator_prompt"]
    assert tuple(lean_lsp_row["target_primitives"]) == ("rank_uniformity",)
    assert tuple(lean_lsp_row["actionable_work_items"]) == (
        "rank_uniformity: prove finite rank uniformity from exchangeability",
    )
    assert tuple(lean_lsp_row["request_payload"]["target_primitives"]) == (
        "rank_uniformity",
    )
    assert (
        tuple(lean_lsp_row["request_payload"]["actionable_work_items"])
        == tuple(lean_lsp_row["actionable_work_items"])
    )
    assert tuple(
        lean_lsp_row["request_playbook"]["input_summary"]["target_primitives"]
    ) == ("rank_uniformity",)
    assert (
        tuple(
            lean_lsp_row["request_playbook"]["input_summary"][
                "actionable_work_items"
            ]
        )
        == tuple(lean_lsp_row["actionable_work_items"])
    )
    assert "Actionable work items:" in lean_lsp_row["request_playbook"][
        "operator_prompt"
    ]
    assert (
        "prover_diagnostics"
        in lean_lsp_row["request_playbook"]["expected_response_fields"]
    )
    assert lean_lsp_row["request_playbook"]["acceptance_checklist"]
    assert (
        "not theorem proof evidence"
        in lean_lsp_row["request_payload"]["proof_evidence_boundary"]
    )
    assert (
        lean_lsp_row["request_payload"]["resource_request_id"]
        == lean_lsp_row["resource_request_id"]
    )
    assert (
        lean_lsp_row["request_payload"]["request_rank"]
        == lean_lsp_row["request_rank"]
    )
    assert (
        lean_lsp_row["request_payload"]["expected_response_artifact"]
        == lean_lsp_row["expected_response_artifact"]
    )
    assert "prover_diagnostics" in lean_lsp_row["response_contract_fields"]
    assert "source_refs" not in lean_lsp_row["response_contract_fields"]
    assert (
        lean_lsp_row["response_contract_fields"]
        == lean_lsp_row["request_payload"]["response_contract_fields"]
    )
    assert (
        payload["n_with_dispatch_specs"]
        == payload["n_dispatch_spec_identity_valid"]
        == payload["n_resource_request_rows"]
    )
    assert payload["n_dispatch_spec_identity_mismatches"] == 0
    source_paperclip_row = next(
        row for row in source_rows if row["resource_id"] == "paperclip_cli_mcp"
    )
    assert source_paperclip_row["dispatch_spec"]["adapter_surface"] == "paperclip_mcp_cli"
    assert "source_refs" in source_paperclip_row["response_contract_fields"]
    assert "prover_diagnostics" not in source_paperclip_row["response_contract_fields"]
    assert "mcp_tool_call" in source_paperclip_row["request_contract_fields"]
    assert tuple(source_paperclip_row["actionable_work_items"]) == (
        "coverage_inequality: port the source-backed coverage inequality",
    )
    assert (
        source_paperclip_row["resource_contract_ids"]
        == source_paperclip_row["request_payload"]["resource_contract_ids"]
    )
    formal_source_row = next(
        row
        for row in bridge_rows
        if row["resource_id"] == "local_formal_source_index"
    )
    assert (
        formal_source_row["expected_response_artifact"]
        == "formal_library_search_or_dependency_response"
    )
    assert validate_resource_request_queue_row(
        lean_lsp_row,
        resource_request_queue_row_json_schema(),
    ) == []
    malformed = dict(lean_lsp_row)
    malformed.pop("request_payload")
    assert "request_payload required" in validate_resource_request_queue_row(
        malformed,
        resource_request_queue_row_json_schema(),
    )
    malformed = dict(lean_lsp_row)
    malformed["request_payload"] = dict(lean_lsp_row["request_payload"])
    malformed["request_payload"].pop("resource_request_id")
    assert (
        "request_payload.resource_request_id required"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["request_payload"] = dict(lean_lsp_row["request_payload"])
    malformed["request_payload"]["expected_response_artifact"] = "stale_artifact"
    assert (
        "request_payload.expected_response_artifact must match row.expected_response_artifact"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(exact_row)
    malformed["request_payload"] = dict(exact_row["request_payload"])
    malformed["request_payload"]["candidate_declaration_rows"] = [
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "rocq",
            "source_field": "candidate_declarations",
        }
    ]
    assert (
        "request_payload.candidate_declaration_rows must match row.candidate_declaration_rows"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["dispatch_spec"] = dict(lean_lsp_row["dispatch_spec"])
    malformed["dispatch_spec"]["adapter_surface"] = "stale_adapter"
    assert (
        "dispatch_spec.adapter_surface must match resource_id/request_phase"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed.pop("request_playbook")
    assert "request_playbook required" in validate_resource_request_queue_row(
        malformed,
        resource_request_queue_row_json_schema(),
    )
    malformed = dict(lean_lsp_row)
    malformed["request_playbook"] = dict(lean_lsp_row["request_playbook"])
    malformed["request_playbook"]["expected_response_fields"] = ["stale_field"]
    assert (
        "request_playbook.expected_response_fields must match row.response_contract_fields"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["request_payload"] = dict(lean_lsp_row["request_payload"])
    malformed["request_payload"]["target_primitives"] = ["rank_uniformity", "spectral_gap"]
    assert (
        "request_payload.target_primitives must match row.target_primitives"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["request_payload"] = dict(lean_lsp_row["request_payload"])
    malformed["request_payload"]["actionable_work_items"] = [
        "prove the wrong bridge"
    ]
    assert (
        "request_payload.actionable_work_items must match row.actionable_work_items"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["request_playbook"] = dict(lean_lsp_row["request_playbook"])
    malformed["request_playbook"]["input_summary"] = dict(
        lean_lsp_row["request_playbook"]["input_summary"]
    )
    malformed["request_playbook"]["input_summary"]["target_primitives"] = [
        "spectral_gap"
    ]
    assert (
        "request_playbook.input_summary.target_primitives must match row.target_primitives"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    malformed = dict(lean_lsp_row)
    malformed["request_playbook"] = dict(lean_lsp_row["request_playbook"])
    malformed["request_playbook"]["input_summary"] = dict(
        lean_lsp_row["request_playbook"]["input_summary"]
    )
    malformed["request_playbook"]["input_summary"]["actionable_work_items"] = [
        "stale work item"
    ]
    malformed["request_payload"] = dict(lean_lsp_row["request_payload"])
    malformed["request_payload"]["request_playbook"] = malformed["request_playbook"]
    assert (
        "request_playbook.input_summary.actionable_work_items must match row.actionable_work_items"
        in validate_resource_request_queue_row(
            malformed,
            resource_request_queue_row_json_schema(),
        )
    )
    assert (
        request_queue_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    ).exists()
    assert (
        request_queue_dir / "formalization_gap_planner_resource_request_queue.jsonl"
    ).exists()
    assert (
        request_queue_dir
        / "formalization_gap_planner_resource_request_queue_row.schema.json"
    ).exists()
    assert (
        request_queue_dir / "formalization_gap_planner_resource_request_queue.md"
    ).exists()


def test_resource_request_queue_dispatches_llm_route_planner_followups() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_request_queue_llm")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    llm_route_planner_dir = root / "llm_route_planner"
    request_queue_dir = root / "request_queue"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "routes": [
                    {
                        "route_id": "rank_route",
                        "display_name": "rank_route",
                        "theorem_statement": (
                            "A distribution-free rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                            },
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
        component_resource_registry_dir
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    llm_route_planner_dir.mkdir(parents=True, exist_ok=True)
    (
        llm_route_planner_dir
        / "formalization_gap_planner_llm_route_planner_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_llm_route_planner",
                "rows": [
                    {
                        "llm_route_planner_row_id": "llm_route_row:rank",
                        "request_id": "llm_route_request:rank",
                        "route_id": "rank_route",
                        "display_name": "rank_route",
                        "target_prover_family": "lean4",
                        "library_snapshot_ref": (
                            "lean_mathlib_empirical_process_snapshot"
                        ),
                        "minimal_delta_plan": {
                            "selected_primitives": [
                                "exchangeability",
                                "rank_uniformity",
                            ]
                        },
                        "route_adoption_preconditions": {
                            "blocked_before_response": True,
                            "known_pre_response_blockers": [
                                "search_requests_pending_evidence",
                                "planner_next_actions_pending_evidence",
                            ],
                            "n_known_pre_response_blockers": 2,
                            "response_required_fields": [
                                "search_requests",
                                "planner_next_actions",
                            ],
                            "n_response_required_fields": 2,
                            "target_primitives": ["rank_uniformity"],
                            "n_target_primitives": 1,
                            "proof_evidence_status": (
                                "FORMALIZATION_GAP_PLANNER_LLM_ROUTE_PLANNER_NOT_PROOF_EVIDENCE"
                            ),
                        },
                        "search_requests": [
                            {
                                "request_kind": "literature_discovery",
                                "query": (
                                    "exchangeability rank uniformity proof route"
                                ),
                                "reason": (
                                    "ground the informal rank-uniformity lemma in "
                                    "source text before route repair"
                                ),
                                "target_primitives": ["rank_uniformity"],
                                "resource_ids": ["paperclip_cli_mcp"],
                            }
                        ],
                        "planner_next_actions": [
                            {
                                "action": (
                                    "ask Lean LSP for residual goals on the "
                                    "rank_uniformity bridge lemma"
                                ),
                                "resource_id": "lean_lsp_mcp",
                                "target_primitives": ["rank_uniformity"],
                            }
                        ],
                        "formal_attempt_queue": [
                            {
                                "attempt_id": "attempt:exchangeability_reuse",
                                "formal_node_id": "formal:exchangeability",
                                "primitive": "exchangeability",
                                "target_primitives": ["exchangeability"],
                                "target_prover_family": "lean4",
                                "attempt_kind": "reuse_existing_declaration",
                                "action": (
                                    "run the exchangeability reuse leaf through "
                                    "Lean proof-state feedback"
                                ),
                                "expected_feedback": [
                                    "kernel_status",
                                    "residual_goals",
                                ],
                                "prerequisite_formal_node_ids": [],
                            },
                            {
                                "attempt_id": "attempt:rank_uniformity_bridge",
                                "formal_node_id": "formal:rank_uniformity",
                                "primitive": "rank_uniformity",
                                "target_primitives": ["rank_uniformity"],
                                "target_prover_family": "lean4",
                                "attempt_kind": "bridge_lemma",
                                "action": (
                                    "try rank uniformity after exchangeability "
                                    "reuse closes"
                                ),
                                "expected_feedback": [
                                    "kernel_status",
                                    "residual_goals",
                                ],
                                "prerequisite_formal_node_ids": [
                                    "formal:exchangeability"
                                ],
                            },
                        ],
                        "formal_attempt_queue_schedule": {
                            "schedule_kind": (
                                "formalization_gap_planner_llm_route_planner_formal_attempt_queue_schedule"
                            ),
                            "n_attempts": 2,
                            "n_initial_ready_attempts": 1,
                            "n_waiting_for_formal_prerequisite_attempts": 1,
                            "n_missing_prerequisite_attempts": 0,
                            "has_formal_attempt_queue": True,
                            "has_initial_ready_attempt": True,
                            "all_prerequisites_queued": True,
                            "bottom_up_schedule_complete": True,
                            "initial_ready_attempt_ids": [
                                "attempt:exchangeability_reuse"
                            ],
                            "waiting_attempt_ids": [
                                "attempt:rank_uniformity_bridge"
                            ],
                            "missing_prerequisite_attempt_ids": [],
                            "missing_prerequisite_formal_node_ids": [],
                            "attempt_dependency_rows": [
                                {
                                    "formal_attempt_queue_index": 0,
                                    "attempt_id": (
                                        "attempt:exchangeability_reuse"
                                    ),
                                    "formal_node_id": "formal:exchangeability",
                                    "primitive": "exchangeability",
                                    "attempt_kind": (
                                        "reuse_existing_declaration"
                                    ),
                                    "target_prover_family": "lean4",
                                    "initial_ready": True,
                                    "dependency_status": "initial_ready",
                                    "prerequisite_formal_node_ids": [],
                                    "prerequisite_attempt_ids": [],
                                    "missing_prerequisite_formal_node_ids": [],
                                },
                                {
                                    "formal_attempt_queue_index": 1,
                                    "attempt_id": (
                                        "attempt:rank_uniformity_bridge"
                                    ),
                                    "formal_node_id": "formal:rank_uniformity",
                                    "primitive": "rank_uniformity",
                                    "attempt_kind": "bridge_lemma",
                                    "target_prover_family": "lean4",
                                    "initial_ready": False,
                                    "dependency_status": (
                                        "waiting_for_formal_prerequisite_attempts"
                                    ),
                                    "prerequisite_formal_node_ids": [
                                        "formal:exchangeability"
                                    ],
                                    "prerequisite_attempt_ids": [
                                        "attempt:exchangeability_reuse"
                                    ],
                                    "missing_prerequisite_formal_node_ids": [],
                                },
                            ],
                        },
                        "residual_interpretations": [
                            {
                                "residual_goal": (
                                    "rank_uniformity: missing conditioning side "
                                    "condition from prover feedback"
                                ),
                                "interpretation": (
                                    "the proof route must add the conditional "
                                    "exchangeability side condition before replay"
                                ),
                                "route_repair": (
                                    "add conditional exchangeability to the "
                                    "informal and formal route DAGs"
                                ),
                                "residual_primitives": ["rank_uniformity"],
                                "target_primitives": ["rank_uniformity"],
                                "source_refs": ["conformal_prediction_textbook"],
                                "source_snippets": [
                                    {
                                        "source_ref": (
                                            "conformal_prediction_textbook"
                                        ),
                                        "text": (
                                            "Rank uniformity follows under the "
                                            "conditional exchangeability side "
                                            "condition."
                                        ),
                                    }
                                ],
                                "source_search_status": "source_backed",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
        formalization_gap_planner_llm_route_planner_dir=llm_route_planner_dir,
    )

    assert payload["all_ok"]
    assert (
        "formalization_gap_planner_llm_route_planner"
        in payload["source_components"]
    )
    assert payload["n_llm_route_planner_rows"] == 1
    assert payload["n_llm_route_planner_rows_with_search_requests"] == 1
    assert payload["n_llm_route_planner_rows_with_planner_next_actions"] == 1
    assert payload["n_llm_route_planner_rows_with_residual_interpretations"] == 1
    assert payload["n_llm_route_planner_search_requests"] == 1
    assert payload["n_llm_route_planner_planner_next_actions"] == 1
    assert payload["n_llm_route_planner_residual_interpretations"] == 1
    assert payload["n_llm_route_planner_rows_with_formal_attempt_queue"] == 1
    assert payload["n_llm_route_planner_formal_attempt_queue_items"] == 2
    assert payload["n_llm_route_planner_formal_attempt_queue_ready_items"] == 1
    assert payload["n_llm_route_planner_formal_attempt_queue_waiting_items"] == 1
    assert (
        payload[
            "n_llm_route_planner_formal_attempt_queue_missing_prerequisite_items"
        ]
        == 0
    )
    assert payload["n_llm_route_planner_rows_with_route_adoption_preconditions"] == 1
    assert (
        payload[
            "n_llm_route_planner_route_adoption_precondition_known_blockers"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_route_adoption_precondition_required_response_fields"
        ]
        == 2
    )
    assert (
        payload[
            "n_llm_route_planner_route_adoption_precondition_target_primitives"
        ]
        == 1
    )
    assert payload["n_llm_route_planner_search_request_rows"] == 3
    assert payload["n_llm_route_planner_planner_next_action_rows"] == 3
    assert payload["n_llm_route_planner_residual_interpretation_rows"] == 2
    assert payload["n_llm_route_planner_formal_attempt_queue_resource_request_rows"] == 3
    assert payload["n_llm_route_planner_resource_request_rows"] == 11
    assert (
        payload[
            "n_llm_route_planner_resource_request_rows_with_route_adoption_preconditions"
        ]
        == payload["n_llm_route_planner_resource_request_rows"]
    )
    assert (
        payload[
            "n_llm_route_planner_resource_request_route_adoption_precondition_target_primitives"
        ]
        == payload["n_llm_route_planner_resource_request_rows"]
    )
    assert (
        payload["n_resource_request_rows"]
        == payload["n_action_resource_plan_resource_request_rows"]
        + payload["n_llm_route_planner_resource_request_rows"]
    )
    llm_rows = [
        row
        for row in payload["rows"]
        if row["request_payload"].get("llm_route_planner_row_id")
        == "llm_route_row:rank"
    ]
    assert len(llm_rows) == payload["n_llm_route_planner_resource_request_rows"]
    assert {row["resource_id"] for row in llm_rows}.issuperset(
        {
            "local_literature_corpus",
            "paperclip_cli_mcp",
            "paperqa2_local_library",
            "local_lake_lean",
            "lean_lsp_mcp",
            "leandojo_reprover",
            "local_route_revision_overlay",
            "frontier_route_revision_handoff",
        }
    )
    paperclip_row = next(
        row for row in llm_rows if row["resource_id"] == "paperclip_cli_mcp"
    )
    assert paperclip_row["request_payload"][
        "llm_route_planner_source_kind"
    ] == "search_request"
    assert paperclip_row["request_payload"][
        "llm_route_planner_hook_kind"
    ] == "literature_discovery"
    assert "exchangeability rank uniformity" in " ".join(
        paperclip_row["request_payload"]["llm_route_planner_queries"]
    )
    assert "exchangeability rank uniformity" in " ".join(
        paperclip_row["actionable_work_items"]
    )
    assert (
        tuple(paperclip_row["request_payload"]["actionable_work_items"])
        == tuple(paperclip_row["actionable_work_items"])
    )
    assert (
        tuple(
            paperclip_row["request_playbook"]["input_summary"][
                "actionable_work_items"
            ]
        )
        == tuple(paperclip_row["actionable_work_items"])
    )
    assert (
        paperclip_row["request_playbook"]["llm_route_planner_source_item"][
            "request_kind"
        ]
        == "literature_discovery"
    )
    assert (
        paperclip_row["request_payload"][
            "llm_route_planner_route_adoption_preconditions"
        ]["n_known_pre_response_blockers"]
        == 2
    )
    assert (
        paperclip_row["request_payload"][
            "llm_route_planner_route_adoption_preconditions"
        ]["target_primitives"]
        == ["rank_uniformity"]
    )
    assert (
        paperclip_row["request_payload"][
            "llm_route_planner_route_adoption_preconditions"
        ]["n_target_primitives"]
        == 1
    )
    assert (
        "llm_route_planner_route_adoption_preconditions"
        in paperclip_row["request_contract_fields"]
    )
    assert (
        paperclip_row["request_payload"][
            "llm_route_planner_route_adoption_preconditions"
        ]
        == paperclip_row["request_playbook"][
            "llm_route_planner_route_adoption_preconditions"
        ]
        == paperclip_row["request_playbook"]["input_summary"][
            "llm_route_planner_route_adoption_preconditions"
        ]
    )
    assert any(
        "route_adoption_preconditions" in item
        for item in paperclip_row["request_playbook"]["acceptance_checklist"]
    )
    lean_lsp_row = next(
        row for row in llm_rows if row["resource_id"] == "lean_lsp_mcp"
    )
    assert lean_lsp_row["request_payload"][
        "llm_route_planner_source_kind"
    ] == "planner_next_action"
    assert lean_lsp_row["request_payload"][
        "llm_route_planner_hook_kind"
    ] == "proof_state_feedback"
    assert lean_lsp_row["queue_action_kind"] == "prove_bridge_lemma"
    assert "residual_goals" in lean_lsp_row["response_contract_fields"]
    assert "ask Lean LSP for residual goals" in " ".join(
        lean_lsp_row["actionable_work_items"]
    )
    assert (
        tuple(lean_lsp_row["request_payload"]["actionable_work_items"])
        == tuple(lean_lsp_row["actionable_work_items"])
    )
    assert "not theorem proof evidence" in lean_lsp_row["proof_evidence_boundary"]
    formal_attempt_rows = [
        row
        for row in llm_rows
        if row["request_payload"].get("llm_route_planner_source_kind")
        == "formal_attempt_queue"
    ]
    assert len(formal_attempt_rows) == 3
    assert {
        row["resource_id"] for row in formal_attempt_rows
    } == {"local_lake_lean", "lean_lsp_mcp", "leandojo_reprover"}
    formal_attempt_lsp_row = next(
        row for row in formal_attempt_rows if row["resource_id"] == "lean_lsp_mcp"
    )
    assert formal_attempt_lsp_row["queue_action_kind"] == "prove_bridge_lemma"
    assert (
        formal_attempt_lsp_row["request_payload"]["formal_attempt_context"][
            "attempt_id"
        ]
        == "attempt:exchangeability_reuse"
    )
    assert (
        formal_attempt_lsp_row["request_payload"]["formal_attempt_context"][
            "formal_attempt_dependency_status"
        ]
        == "initial_ready"
    )
    assert "formal_attempt_context" in formal_attempt_lsp_row["request_contract_fields"]
    assert "formal_attempt_context" in formal_attempt_lsp_row["response_contract_fields"]
    assert (
        formal_attempt_lsp_row["request_payload"]["formal_attempt_context"]
        == formal_attempt_lsp_row["request_playbook"]["formal_attempt_context"]
        == formal_attempt_lsp_row["request_playbook"]["input_summary"][
            "formal_attempt_context"
        ]
    )
    assert "attempt:rank_uniformity_bridge" not in json.dumps(formal_attempt_rows)
    assert any(
        "formal_attempt_context" in item
        for item in formal_attempt_lsp_row["request_playbook"][
            "acceptance_checklist"
        ]
    )
    route_revision_row = next(
        row for row in llm_rows if row["resource_id"] == "local_route_revision_overlay"
    )
    assert route_revision_row["request_payload"][
        "llm_route_planner_source_kind"
    ] == "residual_interpretation"
    assert route_revision_row["request_payload"][
        "llm_route_planner_hook_kind"
    ] == "route_revision"
    assert route_revision_row["queue_action_kind"] == "route_revision"
    assert route_revision_row["expected_response_artifact"] == "route_revision_response"
    assert "residual_goal_context" in route_revision_row["request_contract_fields"]
    residual_context = route_revision_row["request_payload"]["residual_goal_context"]
    assert residual_context["residual_goal"].startswith("rank_uniformity")
    assert residual_context["residual_primitives"] == ("rank_uniformity",)
    assert residual_context["source_refs"] == ("conformal_prediction_textbook",)
    assert residual_context["source_snippets"][0]["source_ref"] == (
        "conformal_prediction_textbook"
    )
    assert residual_context["source_search_status"] == "source_backed"
    assert residual_context == route_revision_row["request_playbook"][
        "residual_goal_context"
    ]
    assert residual_context == route_revision_row["request_playbook"][
        "input_summary"
    ]["residual_goal_context"]
    assert "conditional exchangeability" in " ".join(
        route_revision_row["actionable_work_items"]
    )
    assert (
        validate_resource_request_queue_row(
            paperclip_row,
            resource_request_queue_row_json_schema(),
        )
        == []
    )
    assert (
        validate_resource_request_queue_row(
            lean_lsp_row,
            resource_request_queue_row_json_schema(),
        )
        == []
    )
    assert (
        validate_resource_request_queue_row(
            route_revision_row,
            resource_request_queue_row_json_schema(),
        )
        == []
    )


def test_resource_request_queue_dispatches_prompt_only_route_planning_brief_gaps() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_resource_request_queue_llm_brief_gaps"
    )
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    llm_route_planner_dir = root / "llm_route_planner"
    request_queue_dir = root / "request_queue"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "lean_mathlib_empirical_process_snapshot",
                "routes": [
                    {
                        "route_id": "rank_route_prompt_only",
                        "display_name": "rank_route_prompt_only",
                        "theorem_statement": (
                            "A distribution-free rank bound follows from a "
                            "missing source-backed rank-uniformity argument."
                        ),
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
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
        component_resource_registry_dir
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    llm_payload = export_formalization_gap_planner_llm_route_planner(
        input_json,
        llm_route_planner_dir,
        provider_name="prompt_only",
    )
    assert llm_payload["n_request_packets"] == 1
    assert llm_payload["n_request_route_planning_evidence_gaps"] == 2
    assert llm_payload["n_awaiting_llm_response"] == 1

    payload = export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
        formalization_gap_planner_llm_route_planner_dir=llm_route_planner_dir,
    )

    assert payload["all_ok"]
    assert payload["n_llm_route_planner_rows"] == 1
    assert payload["n_llm_route_planner_request_packets"] == 1
    assert payload["n_llm_route_planner_request_route_planning_briefs"] == 1
    assert payload["n_llm_route_planner_route_planning_brief_evidence_gaps"] == 2
    assert payload["n_llm_route_planner_search_requests"] == 0
    assert payload["n_llm_route_planner_resource_request_rows"] == 0
    assert (
        payload["n_llm_route_planner_route_planning_brief_resource_request_rows"]
        == 7
    )
    assert payload["n_llm_route_planner_total_resource_request_rows"] == 7
    assert payload["n_llm_route_planner_route_planning_brief_evidence_gap_rows"] == 7
    brief_rows = [
        row
        for row in payload["rows"]
        if row["request_payload"].get("llm_route_planner_source_kind")
        == "route_planning_brief_evidence_gap"
    ]
    assert len(brief_rows) == 7
    by_resource = {row["resource_id"]: row for row in brief_rows}
    assert {
        "local_literature_corpus",
        "paperclip_cli_mcp",
        "paperqa2_local_library",
        "local_formal_source_index",
        "local_lean_rag_dependency_graph",
        "loogle_leansearch",
        "leanexplore_mcp",
    }.issubset(by_resource)
    literature_row = by_resource["paperclip_cli_mcp"]
    assert literature_row["request_payload"][
        "llm_route_planner_hook_kind"
    ] == "literature_discovery"
    assert literature_row["request_playbook"]["llm_route_planner_source_item"][
        "route_planning_brief_gap_kind"
    ] == "source_grounding"
    assert (
        "llm_route_planner_target_theorem_context_packet"
        in literature_row["request_contract_fields"]
    )
    assert (
        "llm_route_planner_route_planning_brief"
        in literature_row["request_contract_fields"]
    )
    assert literature_row["request_payload"][
        "llm_route_planner_target_theorem_context_packet"
    ]["route_id"] == "rank_route_prompt_only"
    assert (
        "distribution-free rank bound"
        in literature_row["request_payload"][
            "llm_route_planner_target_context_summary"
        ]["theorem_statement"]
    )
    assert literature_row["request_payload"][
        "llm_route_planner_route_planning_brief"
    ]["target_context"]["route_id"] == "rank_route_prompt_only"
    assert (
        literature_row["request_payload"][
            "llm_route_planner_target_theorem_context_packet"
        ]
        == literature_row["request_playbook"][
            "llm_route_planner_target_theorem_context_packet"
        ]
        == literature_row["request_playbook"]["input_summary"][
            "llm_route_planner_target_theorem_context_packet"
        ]
    )
    assert "rank_uniformity" in literature_row["target_primitives"]
    assert "route_planning_brief evidence gap" in " ".join(
        literature_row["actionable_work_items"]
    )
    formal_row = by_resource["loogle_leansearch"]
    assert formal_row["request_payload"][
        "llm_route_planner_hook_kind"
    ] == "formal_library_grounding"
    assert formal_row["request_playbook"]["llm_route_planner_source_item"][
        "route_planning_brief_gap_kind"
    ] == "formal_library_grounding"
    assert "formal_declaration_hits" in formal_row["response_contract_fields"]
    assert "LLM route-planning brief evidence gaps/request rows" in (
        request_queue_dir / "formalization_gap_planner_resource_request_queue.md"
    ).read_text(encoding="utf-8")
    assert (
        validate_resource_request_queue_row(
            literature_row,
            resource_request_queue_row_json_schema(),
        )
        == []
    )
    assert (
        validate_resource_request_queue_row(
            formal_row,
            resource_request_queue_row_json_schema(),
        )
        == []
    )


def test_resource_request_queue_target_scopes_llm_lean_search_followup_for_rocq() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_request_queue_llm_rocq")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    llm_route_planner_dir = root / "llm_route_planner"
    request_queue_dir = root / "request_queue"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_conformal_snapshot",
                "routes": [
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_rank_route",
                        "theorem_statement": "A Rocq rank route.",
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
        component_resource_registry_dir
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )
    llm_route_planner_dir.mkdir(parents=True, exist_ok=True)
    (
        llm_route_planner_dir
        / "formalization_gap_planner_llm_route_planner_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_llm_route_planner",
                "rows": [
                    {
                        "llm_route_planner_row_id": "llm_route_row:rocq",
                        "request_id": "llm_route_request:rocq",
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_rank_route",
                        "target_prover_family": "rocq",
                        "library_snapshot_ref": "rocq_conformal_snapshot",
                        "minimal_delta_plan": {
                            "selected_primitives": ["rank_uniformity"]
                        },
                        "search_requests": [
                            {
                                "request_kind": "lean_search",
                                "query": (
                                    "Use LeanSearch or loogle-style theorem "
                                    "search for the Rocq rank_uniformity route"
                                ),
                                "target_primitives": ["rank_uniformity"],
                                "resource_ids": ["loogle_leansearch"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
        formalization_gap_planner_llm_route_planner_dir=llm_route_planner_dir,
    )

    assert payload["all_ok"]
    llm_rows = [
        row
        for row in payload["rows"]
        if row["request_payload"].get("llm_route_planner_row_id")
        == "llm_route_row:rocq"
    ]
    assert llm_rows
    llm_resource_ids = {row["resource_id"] for row in llm_rows}
    assert llm_resource_ids == {
        "local_target_formal_source_index",
        "rocq_lsp_serapi",
    }
    assert not llm_resource_ids.intersection(
        {
            "local_formal_source_index",
            "local_lean_rag_dependency_graph",
            "loogle_leansearch",
            "leanexplore_mcp",
            "local_lake_lean",
            "lean_lsp_mcp",
            "leandojo_reprover",
        }
    )
    for row in llm_rows:
        assert row["target_prover_family"] == "rocq"
        assert (
            row["request_payload"]["llm_route_planner_hook_kind"]
            == "formal_library_grounding"
        )
        assert "formal_declaration_hits" in row["response_contract_fields"]
        assert "lean_declaration_hits" not in row["response_contract_fields"]
        assert (
            validate_resource_request_queue_row(
                row,
                resource_request_queue_row_json_schema(),
            )
            == []
        )


def test_resource_request_queue_dispatches_rocq_bridge_without_lean_resources() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_request_queue_rocq")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    component_resource_registry_dir = root / "component_resource_registry"
    action_resource_plan_dir = root / "action_resource_plan"
    request_queue_dir = root / "request_queue"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_conformal_snapshot",
                "routes": [
                    {
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_rank_route",
                        "theorem_statement": "A Rocq rank route.",
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
        component_resource_registry_dir
    )
    export_formalization_gap_planner_action_resource_plan(
        action_queue_dir,
        component_resource_registry_dir,
        action_resource_plan_dir,
    )

    payload = export_formalization_gap_planner_resource_request_queue(
        action_resource_plan_dir,
        request_queue_dir,
    )

    assert payload["all_ok"]
    resource_ids = {row["resource_id"] for row in payload["rows"]}
    assert "rocq_lsp_serapi" in resource_ids
    assert "local_target_formal_source_index" in resource_ids
    assert not resource_ids.intersection(
        {
            "local_formal_source_index",
            "local_lean_rag_dependency_graph",
            "loogle_leansearch",
            "leanexplore_mcp",
            "lean_blueprint_leanarchitect",
            "local_lake_lean",
            "lean_lsp_mcp",
            "leandojo_reprover",
        }
    )
    rocq_request = next(row for row in payload["rows"] if row["resource_id"] == "rocq_lsp_serapi")
    assert rocq_request["target_prover_family"] == "rocq"
    assert rocq_request["dispatch_spec"]["adapter_surface"] == "rocq_serapi"
    assert rocq_request["mcp_or_cli_hint"] == "Rocq SerAPI/LSP adapter"
    assert "dispatch rocq proof-state request" in rocq_request["execution_command"]
    assert "prover_diagnostics" in rocq_request["response_contract_fields"]
    assert "residual_goals" in rocq_request["response_contract_fields"]


def test_resource_request_queue_marks_missing_action_plan_as_blocker() -> None:
    root = Path("runs/test_formalization_gap_planner_resource_request_queue_rejects")
    missing_action_plan_dir = root / "missing_action_plan"
    shutil.rmtree(root, ignore_errors=True)

    payload = export_formalization_gap_planner_resource_request_queue(
        missing_action_plan_dir
    )

    assert not payload["all_ok"]
    assert payload["n_action_resource_plan_rows"] == 0
    assert payload["n_resource_request_rows"] == 0
    assert payload["errors"]

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_interactive_session import (
    interactive_decision_policy_row_json_schema,
    interactive_session_row_json_schema,
    export_formalization_gap_planner_interactive_session,
    validate_interactive_decision_policy_row,
    validate_interactive_session_row,
)
from ai_statistician.formalization_gap_planner_component_resource_registry import (
    export_formalization_gap_planner_component_resource_registry,
)


def test_interactive_session_summarizes_next_bounded_route_actions() -> None:
    root = Path("runs/test_formalization_gap_planner_interactive_session")
    plan_dir = root / "plan"
    queue_dir = root / "queue"
    evidence_dir = root / "evidence"
    stability_dir = root / "stability"
    handoff_dir = root / "handoff"
    triage_dir = root / "triage"
    component_resource_registry_dir = root / "component_resource_registry"
    resource_request_queue_dir = root / "resource_request_queue"
    out_dir = root / "session"
    shutil.rmtree(root, ignore_errors=True)
    for directory in (
        plan_dir,
        queue_dir,
        evidence_dir,
        stability_dir,
        handoff_dir,
        triage_dir,
        component_resource_registry_dir,
        resource_request_queue_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    plan_rows = [
        {
            "goal_plan_id": "goal:stable",
            "route_id": "route:stable",
            "display_name": "stable conformal route",
            "route_class": "source_backed_bridge_route",
            "pareto_profile": "lowest_delta",
            "best_route_cost": 3.0,
            "selected_primitives": ["exchangeability", "rank_uniformity"],
            "existing_reuse_nodes": [
                {"primitive": "exchangeability", "coverage_status": "exact_exists"}
            ],
            "minimal_additional_formalization_nodes": [
                {
                    "primitive": "rank_uniformity",
                    "action_class": "bridge_needed",
                    "source_refs": ["Lei-Wasserman#rank-lemma"],
                }
            ],
            "informal_knowledge_dag_nodes": [
                {"node_id": "proof:rank", "source_refs": ["Lei-Wasserman#proof"]}
            ],
        },
        {
            "goal_plan_id": "goal:revise",
            "route_id": "route:revise",
            "display_name": "revision conformal route",
            "route_class": "source_gap_route",
            "pareto_profile": "lowest_risk",
            "best_route_cost": 7.5,
            "selected_primitives": ["exchangeability", "rank_uniformity"],
            "existing_reuse_nodes": [
                {"primitive": "exchangeability", "coverage_status": "exact_exists"}
            ],
            "minimal_additional_formalization_nodes": [
                {"primitive": "rank_uniformity", "action_class": "bridge_needed"}
            ],
        },
        {
            "goal_plan_id": "goal:literature",
            "route_id": "route:literature",
            "display_name": "literature expansion conformal route",
            "route_class": "source_gap_route",
            "pareto_profile": "awaiting_source_evidence",
            "best_route_cost": 9.0,
            "selected_primitives": [
                "conditional_coverage",
                "rank_uniformity",
            ],
            "source_discovery_nodes": [
                {
                    "primitive": "conditional_coverage",
                    "coverage_status": "source_discovery_needed",
                }
            ],
        },
        {
            "goal_plan_id": "goal:formal",
            "route_id": "route:formal",
            "display_name": "formal grounding expansion conformal route",
            "route_class": "formal_gap_route",
            "pareto_profile": "awaiting_formal_library_grounding",
            "best_route_cost": 5.0,
            "selected_primitives": ["exchangeability", "rank_uniformity"],
            "minimal_additional_formalization_nodes": [
                {
                    "primitive": "rank_uniformity",
                    "action_class": "bridge_needed",
                }
            ],
        },
    ]
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1",
                "rows": plan_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    queue_rows = [
        {
            "goal_plan_id": "goal:revise",
            "route_id": "route:revise",
            "display_name": "revision conformal route",
            "hook_kind": "literature_discovery",
            "owner_agent": "literature",
            "recommended_tools": ["paperclip_cli_mcp", "paperqa2"],
            "frontier_resource_adapters": ["openalex_api"],
            "queries": ["conditional rank argument split conformal proof"],
            "execution_commands": [
                "python3 -m ai_statistician.cli formalization-gap-planner-local-literature-adapter"
            ],
        },
        {
            "goal_plan_id": "goal:literature",
            "route_id": "route:literature",
            "display_name": "literature expansion conformal route",
            "hook_kind": "literature_discovery",
            "owner_agent": "literature",
            "recommended_tools": ["paperclip_cli_mcp", "paperqa2"],
            "frontier_resource_adapters": ["paperclip_cli_mcp"],
            "queries": [
                "conditional coverage split conformal proof assumptions"
            ],
            "execution_commands": [
                "python3 -m ai_statistician.cli formalization-gap-planner-local-literature-adapter"
            ],
        },
        {
            "goal_plan_id": "goal:formal",
            "route_id": "route:formal",
            "display_name": "formal grounding expansion conformal route",
            "hook_kind": "formal_library_grounding",
            "owner_agent": "formal_library_grounder",
            "recommended_tools": ["local_formal_source_index"],
            "frontier_resource_adapters": ["leansearch", "loogle"],
            "queries": ["rank_uniformity formal declaration coverage"],
            "execution_commands": [
                "python3 -m ai_statistician.cli formalization-gap-planner-local-formal-source-adapter"
            ],
        },
    ]
    (queue_dir / "formalization_gap_planner_refinement_queue_manifest.json").write_text(
        json.dumps({"rows": queue_rows}, indent=2),
        encoding="utf-8",
    )
    evidence_rows = [
        {
            "goal_plan_id": "goal:stable",
            "route_id": "route:stable",
            "display_name": "stable conformal route",
            "hook_kind": "literature_discovery",
            "source_refs": ["Lei-Wasserman#rank-lemma"],
            "response_present": True,
        },
        {
            "goal_plan_id": "goal:stable",
            "route_id": "route:stable",
            "display_name": "stable conformal route",
            "hook_kind": "lean_library_grounding",
            "lean_declaration_hits": [
                {
                    "primitive": "exchangeability",
                    "declaration": "Probability.exchangeable",
                }
            ],
            "response_present": True,
        },
        {
            "goal_plan_id": "goal:revise",
            "route_id": "route:revise",
            "display_name": "revision conformal route",
            "hook_kind": "proof_state_feedback",
            "source_refs": ["Lei-Wasserman#conditional-rank"],
            "residual_goals": ["missing conditional rank statement"],
            "route_revision_reasons": ["proof-state residual exposed hidden conditioning"],
            "response_present": True,
        },
        {
            "goal_plan_id": "goal:formal",
            "route_id": "route:formal",
            "display_name": "formal grounding expansion conformal route",
            "hook_kind": "formal_library_grounding",
            "formal_declaration_hits": [],
            "response_present": True,
        },
    ]
    (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(json.dumps({"rows": evidence_rows}, indent=2), encoding="utf-8")
    stability_rows = [
        {
            "goal_plan_id": "goal:stable",
            "route_id": "route:stable",
            "display_name": "stable conformal route",
            "stability_decision": "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND",
            "stable_under_current_evidence_bound": True,
            "responded_hook_kinds": ["literature_discovery", "lean_library_grounding"],
            "awaiting_hook_kinds": [],
        },
        {
            "goal_plan_id": "goal:revise",
            "route_id": "route:revise",
            "display_name": "revision conformal route",
            "stability_decision": "APPLY_ROUTE_REVISION_AND_REPLAN",
            "stable_under_current_evidence_bound": False,
            "needs_route_replanning": True,
            "needs_more_literature": False,
            "needs_more_lean_grounding": False,
            "needs_more_proof_state_feedback": False,
            "responded_hook_kinds": ["proof_state_feedback"],
            "awaiting_hook_kinds": [],
        },
        {
            "goal_plan_id": "goal:literature",
            "route_id": "route:literature",
            "display_name": "literature expansion conformal route",
            "stability_decision": "EXPAND_EVIDENCE_BOUND",
            "stable_under_current_evidence_bound": False,
            "needs_route_replanning": False,
            "needs_more_literature": True,
            "needs_more_lean_grounding": False,
            "needs_more_proof_state_feedback": False,
            "responded_hook_kinds": [],
            "awaiting_hook_kinds": [],
        },
        {
            "goal_plan_id": "goal:formal",
            "route_id": "route:formal",
            "display_name": "formal grounding expansion conformal route",
            "stability_decision": "EXPAND_FORMAL_LIBRARY_GROUNDING",
            "stable_under_current_evidence_bound": False,
            "needs_route_replanning": False,
            "needs_more_literature": False,
            "needs_more_formal_grounding": True,
            "needs_more_lean_grounding": False,
            "needs_more_proof_state_feedback": False,
            "responded_hook_kinds": ["formal_library_grounding"],
            "awaiting_hook_kinds": [],
            "formal_declaration_hits": [],
        },
    ]
    (
        stability_dir
        / "formalization_gap_planner_route_stability_audit_manifest.json"
    ).write_text(json.dumps({"rows": stability_rows}, indent=2), encoding="utf-8")
    handoff_rows = [
        {
            "goal_plan_id": "goal:revise",
            "route_id": "route:revise",
            "display_name": "revision conformal route",
            "requires_replan": True,
            "standalone_route_id": "replan_route:conditional_rank",
            "next_commands": [
                "python3 -m ai_statistician.cli formalization-gap-planner-standalone-plan --input formalization_gap_planner_route_replan_standalone_seed.json"
            ],
        }
    ]
    (
        handoff_dir / "formalization_gap_planner_route_replan_handoff_manifest.json"
    ).write_text(json.dumps({"rows": handoff_rows}, indent=2), encoding="utf-8")
    triage_rows = [
        {
            "goal_plan_id": "goal:revise",
            "route_id": "route:revise",
            "display_name": "revision conformal route",
            "triage_item_id": "triage:revise",
            "triage_class": "repair_local_lean_proof_state",
            "prover_triage_class": "repair_target_prover_proof_state",
            "owner_agent": "formal_verifier",
            "rank": 1,
            "recommended_tools": [
                "target-prover LSP/MCP adapter",
                "proof-state adapter",
            ],
            "residual_goals": ["missing conditional rank statement"],
            "applied_prover_attempt_classes": ["target_prover_failed"],
            "target_prover_families": ["lean4"],
            "execution_commands": [
                "formalization-gap-planner-prover-adapter-contract"
            ],
            "required_gate": "rerun proof-state adapter before proof promotion",
        }
    ]
    (
        triage_dir / "formalization_gap_planner_proof_state_triage_manifest.json"
    ).write_text(json.dumps({"rows": triage_rows}, indent=2), encoding="utf-8")
    export_formalization_gap_planner_component_resource_registry(
        component_resource_registry_dir
    )
    resource_request_rows = [
        {
            "goal_plan_id": "goal:literature",
            "route_id": "route:literature",
            "display_name": "literature expansion conformal route",
            "resource_request_id": "resource-request:literature",
            "resource_id": "paperclip_cli_mcp",
            "request_phase": "frontier_escalation",
            "request_rank": 1,
            "queue_action_kind": "literature_discovery",
            "component_ids": ["literature_grounded_route_synthesis"],
            "target_primitives": ["conditional_coverage"],
            "actionable_work_items": [
                "conditional coverage split conformal proof assumptions"
            ],
            "expected_response_artifact": (
                "formalization_gap_planner_refinement_tool_response"
            ),
            "execution_command": (
                "paperclip dispatch conditional coverage split conformal proof assumptions"
            ),
            "mcp_or_cli_hint": "Paperclip MCP",
            "dispatch_spec": {
                "resource_request_id": "resource-request:literature",
                "resource_id": "paperclip_cli_mcp",
                "adapter": "paperclip",
            },
            "request_payload": {
                "llm_route_planner_queries": [
                    "conditional coverage split conformal proof assumptions"
                ]
            },
        },
        {
            "goal_plan_id": "goal:formal",
            "route_id": "route:formal",
            "display_name": "formal grounding expansion conformal route",
            "resource_request_id": "resource-request:formal",
            "resource_id": "leansearch",
            "request_phase": "frontier_escalation",
            "request_rank": 1,
            "queue_action_kind": "formal_library_grounding",
            "component_ids": ["formal_library_coverage_mapping"],
            "target_primitives": ["rank_uniformity"],
            "actionable_work_items": [
                "rank_uniformity formal declaration coverage"
            ],
            "expected_response_artifact": (
                "formalization_gap_planner_refinement_tool_response"
            ),
            "execution_command": (
                "leansearch rank_uniformity formal declaration coverage"
            ),
            "mcp_or_cli_hint": "LeanSearch",
            "dispatch_spec": {
                "resource_request_id": "resource-request:formal",
                "resource_id": "leansearch",
                "adapter": "leansearch",
            },
        },
    ]
    (
        resource_request_queue_dir
        / "formalization_gap_planner_resource_request_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_request_queue",
                "resource_request_queue_row_schema": {
                    "$id": "urn:ai-statistician:schemas:formalization-gap-planner-resource-request-queue-row:6"
                },
                "rows": resource_request_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_interactive_session(
        plan_dir,
        out_dir,
        formalization_gap_planner_refinement_queue_dir=queue_dir,
        formalization_gap_planner_refinement_evidence_dir=evidence_dir,
        formalization_gap_planner_route_stability_audit_dir=stability_dir,
        formalization_gap_planner_route_replan_handoff_dir=handoff_dir,
        formalization_gap_planner_proof_state_triage_dir=triage_dir,
        formalization_gap_planner_component_resource_registry_dir=component_resource_registry_dir,
        formalization_gap_planner_resource_request_queue_dir=resource_request_queue_dir,
    )

    assert payload["all_ok"]
    assert payload["n_session_rows"] == 4
    assert payload["n_row_schema_valid"] == payload["n_session_rows"]
    assert payload["n_row_schema_invalid"] == 0
    assert payload["n_decision_policy_rows"] == payload["n_session_rows"]
    assert (
        payload["n_decision_policy_row_schema_valid"]
        == payload["n_decision_policy_rows"]
    )
    assert payload["n_decision_policy_row_schema_invalid"] == 0
    assert payload["n_decision_policy_rows_with_resource_contracts"] == 4
    assert payload["n_decision_policy_rows_with_frontier_resources"] == 4
    assert payload["n_decision_policy_rows_with_required_quality_signals"] == 4
    assert payload["n_decision_policy_rows_with_quality_gates"] == 4
    assert payload["n_decision_policy_rows_with_response_validation_signals"] == 4
    assert (
        payload["interactive_session_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-interactive-session-row:1"
    )
    assert (
        payload["interactive_decision_policy_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-interactive-decision-policy-row:1"
    )
    assert payload["n_run_target_prover_replay"] == 1
    assert payload["n_run_route_replan"] == 1
    assert payload["n_run_literature_search"] == 1
    assert payload["n_run_formal_grounding"] == 1
    assert payload["n_run_lean_grounding"] == 0
    assert payload["n_rows_with_source_refs"] == 2
    assert payload["n_rows_with_resource_requests"] == 2
    assert payload["n_resource_requests_linked"] == 2
    assert payload["n_resource_request_dispatch_summaries"] == 2
    assert payload["n_resource_request_execution_commands"] == 2
    assert "resource_request_ids" in payload["interactive_session_row_schema"][
        "properties"
    ]
    by_route = {row["route_id"]: row for row in payload["rows"]}
    assert by_route["route:stable"]["next_interaction_kind"] == "target_prover_replay"
    assert (
        by_route["route:stable"]["session_state"]
        == "ROUTE_STABLE_READY_FOR_REPLAY"
    )
    assert by_route["route:revise"]["next_interaction_kind"] == "route_replan"
    assert by_route["route:revise"]["replan_required"]
    assert "formalization_gap_planner_llm_route_planner" in by_route[
        "route:revise"
    ]["next_tools"]
    assert "anthropic_claude_api" in by_route["route:revise"]["next_tools"]
    assert any(
        "formalization-gap-planner-llm-route-planner" in command
        and "--provider anthropic" in command
        and "--model-tier auto" in command
        and "--invoke-provider" not in command
        for command in by_route["route:revise"]["next_commands"]
    )
    assert any(
        "formalization-gap-planner-llm-route-planner" in command
        and "--provider anthropic" in command
        and "--model-tier auto" in command
        and "--invoke-provider" in command
        for command in by_route["route:revise"]["next_commands"]
    )
    assert "target-prover LSP/MCP adapter" in by_route["route:revise"]["next_tools"]
    assert (
        by_route["route:revise"]["prover_triage_class"]
        == "repair_target_prover_proof_state"
    )
    assert by_route["route:revise"]["applied_prover_attempt_classes"] == (
        "target_prover_failed",
    )
    assert by_route["route:revise"]["target_prover_families"] == ("lean4",)
    assert by_route["route:revise"]["standalone_seed_route_id"] == (
        "replan_route:conditional_rank"
    )
    assert (
        by_route["route:literature"]["next_interaction_kind"]
        == "literature_discovery"
    )
    assert by_route["route:literature"]["resource_request_ids"] == (
        "resource-request:literature",
    )
    assert by_route["route:literature"]["resource_request_resource_ids"] == (
        "paperclip_cli_mcp",
    )
    assert by_route["route:literature"]["resource_request_queue_action_kinds"] == (
        "literature_discovery",
    )
    assert "paperclip_cli_mcp" in by_route["route:literature"]["next_tools"]
    assert any(
        command
        == "paperclip dispatch conditional coverage split conformal proof assumptions"
        for command in by_route["route:literature"]["next_commands"]
    )
    assert by_route["route:literature"]["evidence_summary"]["resource_requests"] == 1
    assert (
        by_route["route:literature"]["resource_request_dispatch_summaries"][0][
            "resource_request_id"
        ]
        == "resource-request:literature"
    )
    assert (
        by_route["route:formal"]["next_interaction_kind"]
        == "formal_library_grounding"
    )
    assert (
        by_route["route:formal"]["session_state"]
        == "EXPAND_FORMAL_LIBRARY_GROUNDING"
    )
    assert by_route["route:formal"]["needs_more_formal_grounding"]
    assert not by_route["route:formal"]["needs_more_lean_grounding"]
    assert "local_formal_source_index" in by_route["route:formal"]["next_tools"]
    assert by_route["route:formal"]["resource_request_ids"] == (
        "resource-request:formal",
    )
    assert "leansearch" in by_route["route:formal"]["next_tools"]
    assert "leansearch rank_uniformity formal declaration coverage" in by_route[
        "route:formal"
    ]["resource_request_execution_commands"]
    policy_by_route = {row["route_id"]: row for row in payload["decision_policy_rows"]}
    assert (
        policy_by_route["route:stable"]["next_interaction_kind"]
        == "target_prover_replay"
    )
    assert "stable_under_current_evidence_bound" in policy_by_route["route:stable"][
        "trigger_signals"
    ]
    assert (
        "formalization_gap_planner_prover_adapter_packet.schema.json"
        in policy_by_route["route:stable"]["required_tool_contracts"]
    )
    assert "cross_prover_public_reuse" in policy_by_route["route:stable"][
        "component_ids"
    ]
    assert "lean_lsp_mcp" in policy_by_route["route:stable"][
        "frontier_escalation_resource_ids"
    ]
    assert policy_by_route["route:stable"]["resource_contract_ids"]
    assert "portable_contract_artifacts_present" in policy_by_route["route:stable"][
        "required_quality_signals"
    ]
    assert "no_kernel_claim_without_replay" in policy_by_route["route:stable"][
        "quality_gates"
    ]
    assert "target_prover_family_and_adapter_contract_present" in policy_by_route[
        "route:stable"
    ]["response_validation_signals"]
    assert policy_by_route["route:revise"]["next_interaction_kind"] == "route_replan"
    assert "needs_route_replanning" in policy_by_route["route:revise"][
        "trigger_signals"
    ]
    assert "prover_triage_class:repair_target_prover_proof_state" in policy_by_route[
        "route:revise"
    ]["trigger_signals"]
    assert "prover_attempt_classes" in policy_by_route["route:revise"][
        "evidence_inputs"
    ]
    assert "target_prover_families" in policy_by_route["route:revise"][
        "evidence_inputs"
    ]
    assert (
        "formalization_gap_planner_route_replan_handoff_row.schema.json"
        in policy_by_route["route:revise"]["required_tool_contracts"]
    )
    assert (
        "formalization_gap_planner_llm_route_planner_request.schema.json"
        in policy_by_route["route:revise"]["required_tool_contracts"]
    )
    assert (
        "formalization_gap_planner_llm_route_planner_model_tier_decision_ledger.schema.json"
        in policy_by_route["route:revise"]["required_tool_contracts"]
    )
    assert (
        "LLM route-planner prompt packet is staged before live provider invocation"
        in policy_by_route["route:revise"]["stop_conditions"]
    )
    assert "route_revision_handoff" in policy_by_route["route:revise"][
        "component_ids"
    ]
    assert "route_revision_overlay" in policy_by_route["route:revise"][
        "local_first_resource_ids"
    ]
    assert "route_revision_is_replayable" in policy_by_route["route:revise"][
        "required_quality_signals"
    ]
    assert "schema_valid_response" in policy_by_route["route:revise"][
        "response_validation_signals"
    ]
    assert (
        policy_by_route["route:literature"]["next_interaction_kind"]
        == "literature_discovery"
    )
    assert "resource_requests_ready" in policy_by_route["route:literature"][
        "trigger_signals"
    ]
    assert "resource_request_queue_dispatch_specs" in policy_by_route[
        "route:literature"
    ]["evidence_inputs"]
    assert "literature_grounded_route_synthesis" in policy_by_route[
        "route:literature"
    ]["component_ids"]
    assert "paperclip_cli_mcp" in policy_by_route["route:literature"][
        "frontier_escalation_resource_ids"
    ]
    assert policy_by_route["route:literature"]["resource_contract_ids"]
    assert "source_refs_or_literature_gap_recorded" in policy_by_route[
        "route:literature"
    ]["required_quality_signals"]
    assert "source_refs_present" in policy_by_route["route:literature"][
        "response_validation_signals"
    ]
    assert (
        policy_by_route["route:formal"]["next_interaction_kind"]
        == "formal_library_grounding"
    )
    assert "needs_more_formal_grounding" in policy_by_route["route:formal"][
        "trigger_signals"
    ]
    assert "formal_library_coverage_mapping" in policy_by_route["route:formal"][
        "component_ids"
    ]
    assert (
        "formalization_gap_planner_route_alignment_edge.schema.json"
        in policy_by_route["route:formal"]["required_tool_contracts"]
    )
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (
        out_dir / "formalization_gap_planner_interactive_session_manifest.json"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_interactive_session_row.schema.json"
    ).exists()
    assert (
        out_dir
        / "formalization_gap_planner_interactive_decision_policy_row.schema.json"
    ).exists()
    assert (out_dir / "formalization_gap_planner_interactive_session.jsonl").exists()
    assert (
        out_dir / "formalization_gap_planner_interactive_decision_policy.jsonl"
    ).exists()
    invalid = dict(by_route["route:revise"])
    invalid.pop("next_interaction_kind")
    assert "next_interaction_kind required" in validate_interactive_session_row(
        invalid,
        interactive_session_row_json_schema(),
    )
    invalid_policy = dict(policy_by_route["route:revise"])
    invalid_policy.pop("stop_conditions")
    assert "stop_conditions required" in validate_interactive_decision_policy_row(
        invalid_policy,
        interactive_decision_policy_row_json_schema(),
    )


def test_interactive_session_surfaces_resource_response_request_ids() -> None:
    root = Path("runs/test_formalization_gap_planner_interactive_session_resource_ids")
    plan_dir = root / "plan"
    stability_dir = root / "stability"
    handoff_dir = root / "handoff"
    out_dir = root / "session"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    stability_dir.mkdir(parents=True, exist_ok=True)
    handoff_dir.mkdir(parents=True, exist_ok=True)
    plan_rows = [
        {
            "goal_plan_id": "goal:awaiting",
            "route_id": "route:awaiting",
            "display_name": "awaiting resource route",
            "selected_primitives": ["rank_uniformity"],
        },
        {
            "goal_plan_id": "goal:rejected",
            "route_id": "route:rejected",
            "display_name": "rejected resource route",
            "selected_primitives": ["rank_uniformity"],
        },
    ]
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1",
                "rows": plan_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    stability_rows = [
        {
            "goal_plan_id": "goal:awaiting",
            "route_id": "route:awaiting",
            "display_name": "awaiting resource route",
            "stability_decision": "AWAITING_REFINEMENT_RESPONSES",
            "stable_under_current_evidence_bound": False,
            "needs_route_replanning": False,
            "needs_more_literature": False,
            "needs_more_lean_grounding": False,
            "needs_more_proof_state_feedback": False,
            "responded_hook_kinds": [],
            "awaiting_hook_kinds": [],
            "rejected_hook_kinds": [],
            "resource_response_awaiting_request_ids": ["request:awaiting"],
            "resource_response_rejected_request_ids": [],
            "response_summary_by_hook": {
                "resource_response_ledger": {
                    "queued": 1,
                    "responded": 0,
                    "contract_ok": 0,
                    "awaiting": 1,
                    "rejected": 0,
                }
            },
        },
        {
            "goal_plan_id": "goal:rejected",
            "route_id": "route:rejected",
            "display_name": "rejected resource route",
            "stability_decision": "REPAIR_REFINEMENT_RESPONSE_CONTRACT",
            "stable_under_current_evidence_bound": False,
            "needs_route_replanning": False,
            "needs_more_literature": False,
            "needs_more_lean_grounding": False,
            "needs_more_proof_state_feedback": False,
            "responded_hook_kinds": [],
            "awaiting_hook_kinds": [],
            "rejected_hook_kinds": ["resource_response_ledger"],
            "resource_response_awaiting_request_ids": [],
            "resource_response_rejected_request_ids": ["request:rejected"],
            "response_summary_by_hook": {
                "resource_response_ledger": {
                    "queued": 1,
                    "responded": 1,
                    "contract_ok": 0,
                    "awaiting": 0,
                    "rejected": 1,
                }
            },
        },
    ]
    (
        stability_dir
        / "formalization_gap_planner_route_stability_audit_manifest.json"
    ).write_text(json.dumps({"rows": stability_rows}, indent=2), encoding="utf-8")
    (
        handoff_dir / "formalization_gap_planner_route_replan_handoff_manifest.json"
    ).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "goal_plan_id": "goal:awaiting",
                        "route_id": "route:awaiting",
                        "display_name": "awaiting resource route",
                        "requires_replan": True,
                        "standalone_route_id": "replan_route:awaiting",
                        "next_commands": [
                            "formalization-gap-planner-standalone-plan --input seed.json"
                        ],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_interactive_session(
        plan_dir,
        out_dir,
        formalization_gap_planner_route_stability_audit_dir=stability_dir,
        formalization_gap_planner_route_replan_handoff_dir=handoff_dir,
    )

    assert payload["all_ok"]
    assert payload["n_waiting_for_adapter_responses"] == 2
    by_route = {row["route_id"]: row for row in payload["rows"]}
    awaiting = by_route["route:awaiting"]
    assert awaiting["next_interaction_kind"] == "await_refinement_response"
    assert awaiting["session_state"] == "AWAITING_REFINEMENT_RESPONSES"
    assert awaiting["replan_required"]
    assert awaiting["resource_response_awaiting_request_ids"] == (
        "request:awaiting",
    )
    assert awaiting["resource_response_rejected_request_ids"] == ()
    assert "resource_response_ledger" in awaiting["next_tools"]
    assert any(
        "resource_request_id=request:awaiting" in command
        for command in awaiting["next_commands"]
    )
    assert awaiting["evidence_summary"]["resource_response_awaiting_requests"] == 1
    rejected = by_route["route:rejected"]
    assert rejected["next_interaction_kind"] == "await_refinement_response"
    assert rejected["rejected_hook_kinds"] == ("resource_response_ledger",)
    assert rejected["resource_response_rejected_request_ids"] == (
        "request:rejected",
    )
    assert any(
        "resource_request_id=request:rejected" in command
        and "repair resource response" in command
        for command in rejected["next_commands"]
    )
    policy_by_route = {row["route_id"]: row for row in payload["decision_policy_rows"]}
    assert "awaiting_resource_response_requests" in policy_by_route[
        "route:awaiting"
    ]["trigger_signals"]
    assert "rejected_resource_response_requests" in policy_by_route[
        "route:rejected"
    ]["trigger_signals"]
    assert "resource_response_ledger_request_status" in policy_by_route[
        "route:rejected"
    ]["evidence_inputs"]
    assert (
        "formalization_gap_planner_resource_response_ledger_row.schema.json"
        in policy_by_route["route:rejected"]["required_tool_contracts"]
    )


def test_interactive_session_waits_on_unresolved_route_adoption_preconditions() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_interactive_session_route_preconditions"
    )
    plan_dir = root / "plan"
    stability_dir = root / "stability"
    out_dir = root / "session"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    stability_dir.mkdir(parents=True, exist_ok=True)

    route_adoption_preconditions = {
        "precondition_kind": (
            "formalization_gap_planner_llm_route_planner_route_adoption_preconditions"
        ),
        "status": "PENDING_CONTEXT_OBLIGATIONS",
        "blocked_before_response": True,
        "known_pre_response_blockers": [
            "source_grounding_obligations_pending"
        ],
        "n_known_pre_response_blockers": 1,
        "response_required_fields": ["search_requests", "planner_next_actions"],
        "n_response_required_fields": 2,
    }
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1",
                "rows": [
                    {
                        "goal_plan_id": "goal:precondition",
                        "route_id": "route:precondition",
                        "display_name": "route-adoption precondition route",
                        "selected_primitives": ["rank_uniformity"],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        stability_dir
        / "formalization_gap_planner_route_stability_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "goal_plan_id": "goal:precondition",
                        "route_id": "route:precondition",
                        "display_name": "route-adoption precondition route",
                        "stability_decision": "AWAITING_REFINEMENT_RESPONSES",
                        "stable_under_current_evidence_bound": False,
                        "needs_route_replanning": False,
                        "needs_more_literature": False,
                        "needs_more_formal_grounding": False,
                        "needs_more_lean_grounding": False,
                        "needs_more_proof_state_feedback": False,
                        "responded_hook_kinds": ["literature_discovery"],
                        "awaiting_hook_kinds": [],
                        "rejected_hook_kinds": [],
                        "resource_response_awaiting_request_ids": [],
                        "resource_response_rejected_request_ids": [],
                        "llm_route_planner_route_adoption_status": (
                            "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
                        ),
                        "route_adoption_preconditions": route_adoption_preconditions,
                        "route_adoption_precondition_present": True,
                        "route_adoption_precondition_blocked_before_response": True,
                        "route_adoption_precondition_unresolved": True,
                        "route_adoption_precondition_known_blockers": [
                            "source_grounding_obligations_pending"
                        ],
                        "route_adoption_precondition_required_response_fields": [
                            "search_requests",
                            "planner_next_actions",
                        ],
                        "route_adoption_precondition_known_blocker_count": 1,
                        "route_adoption_precondition_required_response_field_count": 2,
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_interactive_session(
        plan_dir,
        out_dir,
        formalization_gap_planner_route_stability_audit_dir=stability_dir,
    )

    assert payload["all_ok"]
    assert payload["n_waiting_for_adapter_responses"] == 1
    assert payload["n_rows_with_route_adoption_preconditions"] == 1
    assert payload["n_rows_with_blocking_route_adoption_preconditions"] == 1
    assert payload["n_rows_with_unresolved_route_adoption_preconditions"] == 1
    assert payload["n_route_adoption_precondition_known_blockers"] == 1
    assert payload["n_route_adoption_precondition_required_response_fields"] == 2
    row = payload["rows"][0]
    assert row["session_state"] == "AWAITING_REFINEMENT_RESPONSES"
    assert row["next_interaction_kind"] == "await_refinement_response"
    assert row["route_adoption_preconditions"] == route_adoption_preconditions
    assert row["route_adoption_precondition_unresolved"]
    assert row["route_adoption_precondition_known_blockers"] == (
        "source_grounding_obligations_pending",
    )
    assert row["route_adoption_precondition_required_response_fields"] == (
        "search_requests",
        "planner_next_actions",
    )
    assert "resource_response_ledger" in row["next_tools"]
    assert "formalization_gap_planner_resource_request_queue" in row["next_tools"]
    assert any(
        "materialize LLM route-adoption precondition responses" in command
        for command in row["next_commands"]
    )
    assert row["evidence_summary"]["route_adoption_precondition_unresolved"] == 1
    assert (
        row["evidence_summary"]["route_adoption_precondition_known_blockers"]
        == 1
    )
    policy = payload["decision_policy_rows"][0]
    assert "route_adoption_precondition_unresolved" in policy["trigger_signals"]
    assert "route_adoption_preconditions" in policy["evidence_inputs"]


def test_interactive_session_exposes_ready_formal_attempt_queue_commands() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_interactive_session_formal_attempt_queue"
    )
    plan_dir = root / "plan"
    stability_dir = root / "stability"
    out_dir = root / "session"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    stability_dir.mkdir(parents=True, exist_ok=True)

    formal_attempt_queue = [
        {
            "attempt_id": "attempt:rank_uniformity",
            "formal_node_id": "formal:rank_uniformity",
            "primitive": "rank_uniformity",
            "target_primitives": ["rank_uniformity"],
            "target_prover_family": "lean4",
            "attempt_kind": "kernel_probe",
            "action": "try exact rank-uniformity bridge statement",
            "expected_feedback": ["residual_goals", "missing_imports"],
            "prerequisite_formal_node_ids": [],
        },
        {
            "attempt_id": "attempt:coverage_bridge",
            "formal_node_id": "formal:coverage_bridge",
            "primitive": "coverage_bridge",
            "target_primitives": ["coverage_bridge"],
            "target_prover_family": "lean4",
            "attempt_kind": "bridge_lemma",
            "action": "try coverage theorem after rank uniformity closes",
            "expected_feedback": ["kernel_status", "residual_goals"],
            "prerequisite_formal_node_ids": ["formal:rank_uniformity"],
        },
    ]
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1",
                "rows": [
                    {
                        "goal_plan_id": "goal:formal-attempt",
                        "route_id": "route:formal-attempt",
                        "display_name": "accepted formal attempt route",
                        "target_prover_family": "lean4",
                        "selected_primitives": [
                            "rank_uniformity",
                            "coverage_bridge",
                        ],
                        "formal_attempt_queue": formal_attempt_queue,
                        "replan_metadata": {
                            "llm_route_planner_acceptance_status": (
                                "ACCEPTED_WITH_FORMAL_ATTEMPT_QUEUE"
                            )
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        stability_dir
        / "formalization_gap_planner_route_stability_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "goal_plan_id": "goal:formal-attempt",
                        "route_id": "route:formal-attempt",
                        "display_name": "accepted formal attempt route",
                        "stability_decision": (
                            "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND"
                        ),
                        "stable_under_current_evidence_bound": True,
                        "target_prover_families": ["lean4"],
                        "responded_hook_kinds": [],
                        "awaiting_hook_kinds": [],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_interactive_session(
        plan_dir,
        out_dir,
        formalization_gap_planner_route_stability_audit_dir=stability_dir,
    )

    assert payload["all_ok"]
    assert payload["n_rows_with_formal_attempt_queue"] == 1
    assert payload["n_formal_attempt_queue_items"] == 2
    assert payload["n_formal_attempt_queue_ready_items"] == 1
    assert payload["n_formal_attempt_queue_blocked_items"] == 1
    assert payload["n_formal_attempt_queue_execution_commands"] == 3
    row = payload["rows"][0]
    assert row["next_interaction_kind"] == "target_prover_replay"
    assert row["formal_attempt_queue_item_count"] == 2
    assert row["formal_attempt_queue_ready_item_count"] == 1
    assert row["formal_attempt_queue_blocked_item_count"] == 1
    assert row["formal_attempt_queue_attempt_ids"] == (
        "attempt:rank_uniformity",
        "attempt:coverage_bridge",
    )
    assert row["formal_attempt_queue_ready_attempt_ids"] == (
        "attempt:rank_uniformity",
    )
    assert row["formal_attempt_queue_items"][0][
        "formal_attempt_dependency_status"
    ] == "ready_no_formal_prerequisites"
    assert row["formal_attempt_queue_items"][1][
        "formal_attempt_dependency_status"
    ] == "waiting_for_formal_prerequisite_attempts"
    assert "formalization_gap_planner_prover_adapter_contract" in row["next_tools"]
    assert "target_prover_kernel_replay" in row["next_tools"]
    assert any(
        "formalization-gap-planner-prover-adapter-contract" in command
        and "--target-prover-family lean4" in command
        for command in row["next_commands"]
    )
    assert any(
        "formal_attempt_queue_index=0" in command
        and "attempt_id=attempt:rank_uniformity" in command
        for command in row["next_commands"]
    )
    assert not any(
        "attempt_id=attempt:coverage_bridge" in command
        for command in row["formal_attempt_queue_execution_commands"]
    )
    assert row["evidence_summary"]["formal_attempt_queue_items"] == 2
    assert row["evidence_summary"]["formal_attempt_queue_ready_items"] == 1
    policy = payload["decision_policy_rows"][0]
    assert "llm_formal_attempt_queue_present" in policy["trigger_signals"]
    assert "formal_attempt_queue_ready_items" in policy["trigger_signals"]
    assert "formal_attempt_queue_blocked_items" in policy["trigger_signals"]
    assert "llm_route_planner_formal_attempt_queue" in policy["evidence_inputs"]
    assert (
        "formalization_gap_planner_llm_route_planner_response_payload.schema.json"
        in policy["required_tool_contracts"]
    )
    assert "formalization_gap_planner_prover_adapter_packet.schema.json" in policy[
        "required_tool_contracts"
    ]


def test_interactive_session_keeps_rocq_declaration_hits_portable() -> None:
    root = Path("runs/test_formalization_gap_planner_interactive_session_rocq_hits")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    stability_dir = root / "stability"
    out_dir = root / "session"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stability_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1",
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq",
                        "route_id": "route:rocq",
                        "display_name": "rocq route",
                        "target_prover_family": "rocq",
                        "selected_primitives": ["rank_bridge"],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq",
                        "route_id": "route:rocq",
                        "display_name": "rocq route",
                        "hook_kind": "formal_library_grounding",
                        "target_prover_family": "rocq",
                        "formal_declaration_hits": [
                            {
                                "primitive": "rank_bridge",
                                "declaration": "Rocq.Conformal.rank_bridge",
                                "target_prover_family": "rocq",
                                "source_field": "formal_declaration_hits",
                            }
                        ],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        stability_dir
        / "formalization_gap_planner_route_stability_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq",
                        "route_id": "route:rocq",
                        "display_name": "rocq route",
                        "stability_decision": "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND",
                        "stable_under_current_evidence_bound": True,
                        "target_prover_families": ["rocq"],
                        "responded_hook_kinds": ["formal_library_grounding"],
                        "awaiting_hook_kinds": [],
                        "formal_declaration_hits": [
                            {
                                "primitive": "rank_bridge",
                                "declaration": "Rocq.Conformal.rank_bridge",
                                "target_prover_family": "rocq",
                                "source_field": "formal_declaration_hits",
                            }
                        ],
                        "lean_declaration_hits": [],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_interactive_session(
        plan_dir,
        out_dir,
        formalization_gap_planner_refinement_evidence_dir=evidence_dir,
        formalization_gap_planner_route_stability_audit_dir=stability_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["target_prover_families"] == ("rocq",)
    assert row["next_interaction_kind"] == "target_prover_replay"
    assert row["formal_declaration_hits"] == (
        {
            "primitive": "rank_bridge",
            "declaration": "Rocq.Conformal.rank_bridge",
            "target_prover_family": "rocq",
            "source_field": "formal_declaration_hits",
        },
    )
    assert row["lean_declaration_hits"] == ()
    assert row["evidence_summary"]["formal_declaration_hits"] == 1
    assert row["evidence_summary"]["lean_declaration_hits"] == 0
    bad_legacy_alias_row = dict(row)
    bad_legacy_alias_row["lean_declaration_hits"] = [
        {
            "primitive": "rank_bridge",
            "declaration": "Rocq.Conformal.rank_bridge",
            "target_prover_family": "rocq",
        }
    ]
    assert (
        "lean_declaration_hits is a Lean-only legacy alias; non-Lean interactive "
        "session rows must use formal_declaration_hits only"
        in validate_interactive_session_row(
            bad_legacy_alias_row,
            interactive_session_row_json_schema(),
        )
    )
    bad_source_type_row = dict(row)
    bad_source_type_row["formal_declaration_hits"] = [
        {
            "primitive": "rank_bridge",
            "declaration": "Mathlib.Conformal.rankBridge",
            "source_type": "lean_library",
        }
    ]
    assert (
        "formal_declaration_hits[0].source_type implies lean4 "
        "but row target_prover_families is rocq"
        in validate_interactive_session_row(
            bad_source_type_row,
            interactive_session_row_json_schema(),
        )
    )
    coq_alias_row = dict(row)
    coq_alias_row["formal_declaration_hits"] = [
        {
            "primitive": "rank_bridge",
            "declaration": "Rocq.Conformal.rank_bridge",
            "target_prover_family": "coq",
        }
    ]
    assert validate_interactive_session_row(
        coq_alias_row,
        interactive_session_row_json_schema(),
    ) == ()


def test_interactive_session_rejects_rocq_legacy_lean_alias_input() -> None:
    root = Path("runs/test_formalization_gap_planner_interactive_session_rocq_lean_alias")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    stability_dir = root / "stability"
    out_dir = root / "session"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stability_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1",
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq_alias",
                        "route_id": "route:rocq_alias",
                        "display_name": "rocq alias route",
                        "target_prover_family": "rocq",
                        "selected_primitives": ["rank_bridge"],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq_alias",
                        "route_id": "route:rocq_alias",
                        "display_name": "rocq alias route",
                        "hook_kind": "formal_library_grounding",
                        "lean_declaration_hits": [
                            {
                                "primitive": "rank_bridge",
                                "declaration": "Rocq.Conformal.rank_bridge",
                                "target_prover_family": "rocq",
                            }
                        ],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        stability_dir
        / "formalization_gap_planner_route_stability_audit_manifest.json"
    ).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq_alias",
                        "route_id": "route:rocq_alias",
                        "display_name": "rocq alias route",
                        "stability_decision": "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND",
                        "stable_under_current_evidence_bound": True,
                        "target_prover_families": ["rocq"],
                        "responded_hook_kinds": ["formal_library_grounding"],
                        "awaiting_hook_kinds": [],
                        "formal_declaration_hits": [],
                        "lean_declaration_hits": [],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_interactive_session(
        plan_dir,
        out_dir,
        formalization_gap_planner_refinement_evidence_dir=evidence_dir,
        formalization_gap_planner_route_stability_audit_dir=stability_dir,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["target_prover_families"] == ("rocq",)
    assert row["formal_declaration_hits"] == ()
    assert row["lean_declaration_hits"] == ()
    assert row["evidence_summary"]["formal_declaration_hits"] == 0
    assert row["evidence_summary"]["lean_declaration_hits"] == 0
    assert any(
        "uses lean_declaration_hits for non-Lean interactive session target" in error
        for error in row["errors"]
    )

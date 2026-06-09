from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_route_replan_handoff import (
    export_formalization_gap_planner_route_replan_handoff,
    route_replan_handoff_row_json_schema,
    validate_route_replan_handoff_row,
)
from ai_statistician.formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
    standalone_input_json_schema,
)


def test_route_replan_handoff_exports_replayable_standalone_seed() -> None:
    root = Path("runs/test_formalization_gap_planner_route_replan_handoff")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    overlay_dir = root / "overlay"
    stability_dir = root / "stability"
    handoff_dir = root / "handoff"
    next_plan_dir = root / "next_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    stability_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:replan-fixture",
                "routes": [
                    {
                        "display_name": "split_conformal_finite_sample_coverage",
                        "theorem_statement": "Split conformal has finite sample coverage.",
                        "source_refs": ["Lei-Wasserman distribution-free prediction"],
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                                "cost": 1,
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "source_refs": ["Lei-Wasserman distribution-free prediction"],
                                "cost": 5,
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plan_payload = export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    plan_row = plan_payload["rows"][0]
    revised_selected = [
        *plan_row["selected_primitives"],
        "conditional_rank_argument",
    ]
    revised_delta = [
        node["primitive"]
        for node in plan_row["minimal_additional_formalization_nodes"]
    ] + ["conditional_rank_argument"]
    revised_dag_source_ref = "Vovk-Gammerman-Shafer revised rank node"
    resource_response_trace = {
        "resource_response_ledger_id": "conditional_rank_argument",
        "resource_request_id": "request:conditional_rank_argument",
        "action_resource_plan_id": "action-resource-plan:conditional_rank_argument",
        "primitive_action_id": "primitive-action:conditional_rank_argument",
        "coverage_map_id": "coverage:conditional_rank_argument",
        "goal_plan_id": plan_row["goal_plan_id"],
        "route_id": plan_row["route_id"],
        "primitive": "conditional_rank_argument",
        "target_primitives": ["conditional_rank_argument"],
        "resource_id": "lean_lsp_mcp",
        "request_phase": "frontier_escalation",
        "expected_response_artifact": "proof_state_or_prover_feedback_response",
        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
        "matched_response_contract_fields": ["residual_goals"],
        "missing_response_contract_fields": [],
        "prover_attempt_status": "local_lean_failed",
        "prover_diagnostic_signature": "missing_source_statement",
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    overlay_row = {
        "route_revision_overlay_id": "overlay:split_conformal",
        "goal_plan_id": plan_row["goal_plan_id"],
        "route_id": plan_row["route_id"],
        "display_name": plan_row["display_name"],
        "revision_status": "ROUTE_REVISION_APPLIED",
        "original_selected_primitives": plan_row["selected_primitives"],
        "revised_selected_primitives": revised_selected,
        "added_primitives": ["conditional_rank_argument"],
        "removed_primitives": [],
        "original_delta_primitives": [
            node["primitive"]
            for node in plan_row["minimal_additional_formalization_nodes"]
        ],
        "revised_delta_primitives": revised_delta,
        "added_delta_primitives": ["conditional_rank_argument"],
        "source_refs": ["Lei-Wasserman theorem proof route"],
        "source_snippets": [
            {
                "source_ref": "Lei-Wasserman theorem proof route",
                "claim": "conditional rank argument follows from exchangeability",
                "excerpt": "The source route proves the conditional rank argument before applying the split conformal bound.",
                "target_primitives": ["conditional_rank_argument"],
            }
        ],
        "lean_declaration_hits": [
            {
                "primitive": "conditional_rank_argument",
                "coverage_status": "source_discovery_needed",
                "declaration": "",
            }
        ],
        "residual_goals": ["conditional_rank_argument: missing source-backed statement"],
        "applied_proposal_ids": ["proposal:resource-ledger-conditional-rank"],
        "applied_refinement_evidence_ids": [
            "resource_response_ledger:conditional_rank_argument"
        ],
        "applied_hook_kinds": ["resource_response_ledger"],
        "applied_resource_response_traces": [resource_response_trace],
        "applied_prover_attempt_statuses": ["local_lean_failed"],
        "applied_prover_diagnostic_signatures": ["missing_source_statement"],
        "route_revision_reasons": ["residual proof state exposed a missing rank argument"],
        "route_revision_summaries": ["add conditional rank argument before replay"],
        "revised_informal_knowledge_dag_nodes": [
            {
                "node_id": "informal:conditional_rank_argument",
                "label": "conditional_rank_argument",
                "primitive": "conditional_rank_argument",
                "source_ref": "Lei-Wasserman theorem proof route",
                "source_refs": [revised_dag_source_ref],
            }
        ],
        "revised_lean_realization_dag_nodes": [
            {
                "node_id": "lean:conditional_rank_argument",
                "label": "conditional_rank_argument",
                "primitive": "conditional_rank_argument",
                "coverage_status": "source_port_needed",
            }
        ],
        "revised_route_alignment_edges": [
            *plan_row["route_alignment_edges"],
            {
                "source": "informal:conditional_rank_argument",
                "target": "lean:conditional_rank_argument",
                "kind": "aligned_to_formal_realization_candidate",
                "edge_type": "revised_informal_to_formal_alignment",
                "primitive": "conditional_rank_argument",
                "alignment_status": "source_port_delta",
            },
        ],
        "unaligned_primitives": [],
    }
    (overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_revision_overlay",
                "rows": [overlay_row],
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (stability_dir / "formalization_gap_planner_route_stability_audit_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_stability_audit",
                "rows": [
                    {
                        "goal_plan_id": plan_row["goal_plan_id"],
                        "route_id": plan_row["route_id"],
                        "display_name": plan_row["display_name"],
                        "stability_decision": "APPLY_ROUTE_REVISION_AND_REPLAN",
                        "stopping_rule_evidence": ["new primitive added by overlay"],
                        "next_actions": ["rerun standalone planner"],
                        "resource_response_awaiting_request_ids": [
                            "request:awaiting-literature"
                        ],
                        "resource_response_rejected_request_ids": [
                            "request:rejected-proof-state"
                        ],
                    }
                ],
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_route_replan_handoff(
        plan_dir,
        overlay_dir,
        handoff_dir,
        formalization_gap_planner_route_stability_audit_dir=stability_dir,
    )

    assert payload["all_ok"]
    assert payload["n_handoff_rows"] == 1
    assert payload["n_routes_requiring_replan"] == 1
    assert payload["n_standalone_seed_routes"] == 1
    assert payload["n_resource_response_awaiting_request_ids"] == 1
    assert payload["n_resource_response_rejected_request_ids"] == 1
    assert payload["n_source_snippets"] == 1
    assert payload["n_routes_with_source_snippets"] == 1
    assert payload["n_route_alignment_edges"] >= 1
    assert payload["n_revised_informal_knowledge_dag_nodes"] >= 1
    assert payload["n_revised_formal_realization_dag_nodes"] >= 1
    assert payload["n_revised_lean_realization_dag_nodes"] >= 1
    assert payload["n_unaligned_primitives"] == 0
    assert payload["n_row_schema_valid"] == payload["n_handoff_rows"]
    assert payload["n_row_schema_invalid"] == 0
    assert (
        payload["route_replan_handoff_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-row:1"
    )
    row = payload["rows"][0]
    assert row["requires_replan"]
    assert row["stability_decision"] == "APPLY_ROUTE_REVISION_AND_REPLAN"
    assert row["applied_hook_kinds"] == ("resource_response_ledger",)
    assert row["applied_refinement_evidence_ids"] == (
        "resource_response_ledger:conditional_rank_argument",
    )
    assert row["applied_resource_response_traces"][0]["resource_request_id"] == (
        "request:conditional_rank_argument"
    )
    assert row["resource_response_awaiting_request_ids"] == (
        "request:awaiting-literature",
    )
    assert row["resource_response_rejected_request_ids"] == (
        "request:rejected-proof-state",
    )
    assert row["applied_prover_diagnostic_signatures"] == (
        "missing_source_statement",
    )
    assert {
        edge["primitive"] for edge in row["revised_route_alignment_edges"]
    } == set(row["revised_selected_primitives"])
    assert row["revised_informal_knowledge_dag_nodes"]
    assert row["revised_formal_realization_dag_nodes"] == row[
        "revised_lean_realization_dag_nodes"
    ]
    assert row["revised_lean_realization_dag_nodes"]
    assert row["source_snippets"][0]["source_ref"] == (
        "Lei-Wasserman theorem proof route"
    )
    assert revised_dag_source_ref in row["source_refs"]
    assert row["formal_declaration_hits"] == row["lean_declaration_hits"]
    assert row["standalone_route"]["target_prover_family"] == "lean4"
    assert row["standalone_route"]["replan_metadata"]["target_prover_family"] == "lean4"
    seed = json.loads(
        (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").read_text(
            encoding="utf-8"
        )
    )
    assert seed["component_name"] == "formalization_gap_planner_standalone_input"
    assert seed["target_prover_family"] == "lean4"
    assert seed["routes"][0]["target_prover_family"] == "lean4"
    assert seed["routes"][0]["replan_metadata"]["target_prover_family"] == "lean4"
    assert seed["routes"][0]["revised_informal_knowledge_dag_nodes"]
    assert seed["routes"][0]["revised_formal_realization_dag_nodes"] == seed[
        "routes"
    ][0]["revised_lean_realization_dag_nodes"]
    assert seed["routes"][0]["revised_lean_realization_dag_nodes"]
    assert seed["routes"][0]["source_snippets"][0]["source_ref"] == (
        "Lei-Wasserman theorem proof route"
    )
    assert revised_dag_source_ref in seed["routes"][0]["source_refs"]
    assert (
        revised_dag_source_ref
        in seed["routes"][0]["replan_metadata"]["source_refs"]
    )
    assert seed["routes"][0]["replan_metadata"]["alignment_edge_primitives"]
    handoff_schema = route_replan_handoff_row_json_schema()
    assert "source_snippets" in handoff_schema["properties"]
    assert "source_snippets" not in handoff_schema["required"]
    assert "formal_declaration_hits" in handoff_schema["required"]
    assert "lean_declaration_hits" not in handoff_schema["required"]
    assert "revised_formal_realization_dag_nodes" in handoff_schema["required"]
    assert "revised_lean_realization_dag_nodes" not in handoff_schema["required"]
    legacy_free_row = dict(row)
    legacy_free_row.pop("revised_lean_realization_dag_nodes", None)
    legacy_free_row.pop("lean_declaration_hits", None)
    assert validate_route_replan_handoff_row(legacy_free_row, handoff_schema) == ()
    missing_generic_row = dict(row)
    missing_generic_row.pop("revised_formal_realization_dag_nodes", None)
    assert "revised_formal_realization_dag_nodes required" in validate_route_replan_handoff_row(
        missing_generic_row,
        handoff_schema,
    )
    assert seed["routes"][0]["replan_metadata"][
        "revised_informal_knowledge_dag_nodes"
    ] == seed["routes"][0]["revised_informal_knowledge_dag_nodes"]
    assert seed["routes"][0]["replan_metadata"][
        "formal_declaration_hits"
    ] == list(row["formal_declaration_hits"])
    assert seed["routes"][0]["replan_metadata"][
        "revised_formal_realization_dag_nodes"
    ] == seed["routes"][0]["revised_formal_realization_dag_nodes"]
    assert seed["routes"][0]["replan_metadata"][
        "revised_lean_realization_dag_nodes"
    ] == seed["routes"][0]["revised_lean_realization_dag_nodes"]
    assert seed["routes"][0]["replan_metadata"][
        "revised_route_alignment_edges"
    ] == seed["routes"][0]["revised_route_alignment_edges"]
    assert seed["routes"][0]["replan_metadata"]["applied_hook_kinds"] == [
        "resource_response_ledger"
    ]
    assert seed["routes"][0]["replan_metadata"][
        "applied_refinement_evidence_ids"
    ] == ["resource_response_ledger:conditional_rank_argument"]
    assert seed["routes"][0]["replan_metadata"][
        "applied_resource_response_traces"
    ][0]["resource_id"] == "lean_lsp_mcp"
    assert seed["routes"][0]["replan_metadata"][
        "resource_response_awaiting_request_ids"
    ] == ["request:awaiting-literature"]
    assert seed["routes"][0]["replan_metadata"][
        "resource_response_rejected_request_ids"
    ] == ["request:rejected-proof-state"]
    assert seed["routes"][0]["replan_metadata"][
        "applied_prover_diagnostic_signatures"
    ] == ["missing_source_statement"]
    assert seed["routes"][0]["replan_metadata"]["source_snippets"][0][
        "source_ref"
    ] == "Lei-Wasserman theorem proof route"
    assert (
        "conditional_rank_argument"
        in seed["routes"][0]["replan_metadata"]["alignment_edge_primitives"]
    )
    primitive_by_name = {
        primitive["primitive"]: primitive for primitive in seed["routes"][0]["primitives"]
    }
    assert (
        primitive_by_name["conditional_rank_argument"]["coverage_status"]
        == "source_port_needed"
    )
    assert primitive_by_name["conditional_rank_argument"]["source_snippets"][0][
        "source_ref"
    ] == "Lei-Wasserman theorem proof route"
    assert (
        revised_dag_source_ref
        in primitive_by_name["conditional_rank_argument"]["source_refs"]
    )
    invalid = dict(row)
    invalid.pop("standalone_route")
    assert "standalone_route required" in validate_route_replan_handoff_row(
        invalid,
        route_replan_handoff_row_json_schema(),
    )
    assert (
        handoff_dir / "formalization_gap_planner_route_replan_handoff_row.schema.json"
    ).exists()
    seed_schema = json.loads(
        (
            handoff_dir
            / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert seed_schema["$id"] == standalone_input_json_schema()["$id"]
    route_schema = seed_schema["$defs"]["route"]
    assert "source_snippets" in route_schema["properties"]
    assert "source_snippets" in seed_schema["$defs"]["primitive"]["properties"]
    assert (
        "source_snippets"
        in seed_schema["$defs"]["replan_metadata"]["properties"]
    )
    assert (
        route_schema["properties"]["revised_informal_knowledge_dag_nodes"]["items"][
            "$ref"
        ]
        == "#/$defs/dag_node"
    )
    assert (
        route_schema["properties"]["revised_route_alignment_edges"]["items"]["$ref"]
        == "#/$defs/route_alignment_edge"
    )
    assert (
        seed_schema["$defs"]["replan_metadata"]["properties"][
            "revised_formal_realization_dag_nodes"
        ]["items"]["$ref"]
        == "#/$defs/dag_node"
    )
    assert (
        seed_schema["$defs"]["replan_metadata"]["properties"][
            "revised_lean_realization_dag_nodes"
        ]["items"]["$ref"]
        == "#/$defs/dag_node"
    )
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]

    next_plan = export_formalization_gap_planner_standalone_plan(
        handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json",
        next_plan_dir,
    )

    assert next_plan["all_ok"]
    assert next_plan["n_goal_plans"] == 1
    assert next_plan["n_route_alignment_edges"] >= 1
    assert next_plan["n_standalone_input_traces"] == 1
    assert next_plan["n_standalone_input_traces_with_replan_metadata"] == 1
    assert next_plan["n_standalone_input_traces_with_source_snippets"] == 1
    assert next_plan["n_standalone_input_trace_source_snippets"] == 1
    assert next_plan["n_primitive_source_snippets"] == 1
    next_row = next_plan["rows"][0]
    trace = next_row["standalone_input_trace"]
    assert trace["source_route_id"] == seed["routes"][0]["route_id"]
    assert trace["has_replan_metadata"]
    assert trace["has_source_snippets"]
    assert trace["source_snippets"][0]["source_ref"] == (
        "Lei-Wasserman theorem proof route"
    )
    assert trace["primitive_source_snippets"][0]["primitive"] == (
        "conditional_rank_argument"
    )
    assert trace["primitive_source_snippets"][0]["source_snippets"][0][
        "source_ref"
    ] == "Lei-Wasserman theorem proof route"
    assert trace["applied_hook_kinds"] == ["resource_response_ledger"]
    assert trace["applied_refinement_evidence_ids"] == [
        "resource_response_ledger:conditional_rank_argument"
    ]
    assert trace["applied_resource_response_traces"][0]["resource_request_id"] == (
        "request:conditional_rank_argument"
    )
    assert trace["resource_response_awaiting_request_ids"] == [
        "request:awaiting-literature"
    ]
    assert trace["resource_response_rejected_request_ids"] == [
        "request:rejected-proof-state"
    ]
    assert trace["applied_prover_diagnostic_signatures"] == [
        "missing_source_statement"
    ]
    assert trace["revised_informal_knowledge_dag_nodes"]
    assert trace["revised_formal_realization_dag_nodes"] == trace[
        "revised_lean_realization_dag_nodes"
    ]
    assert trace["revised_lean_realization_dag_nodes"]
    assert trace["revised_route_alignment_edges"]
    assert any(
        packet["primitive"] == "conditional_rank_argument"
        for packet in next_plan["rows"][0]["portable_work_packets"]
    )
    conditional_nodes = [
        node
        for node in next_row["source_discovery_nodes"]
        if node["primitive"] == "conditional_rank_argument"
    ]
    assert conditional_nodes[0]["source_snippets"][0]["source_ref"] == (
        "Lei-Wasserman theorem proof route"
    )


def test_route_replan_handoff_preserves_overlay_target_prover_family_for_rocq() -> None:
    root = Path("runs/test_formalization_gap_planner_route_replan_handoff_rocq")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    overlay_dir = root / "overlay"
    handoff_dir = root / "handoff"
    next_plan_dir = root / "next_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mixed-prover:fixture",
                "routes": [
                    {
                        "display_name": "rocq_exchangeability_bridge",
                        "theorem_statement": "A Rocq exchangeability bridge is needed.",
                        "theorem_skeleton": "Theorem rocq_exchangeability_bridge : True.",
                        "source_refs": ["rocq exchangeability note"],
                        "primitives": [
                            {
                                "primitive": "rocq_exchangeability_bridge",
                                "coverage_status": "bridge_needed",
                                "candidate_declarations": [
                                    "Rocq.Probability.exchangeable"
                                ],
                                "source_refs": ["rocq exchangeability note"],
                                "cost": 5,
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plan_payload = export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    plan_row = plan_payload["rows"][0]
    overlay_row = {
        "route_revision_overlay_id": "overlay:rocq_exchangeability_bridge",
        "goal_plan_id": plan_row["goal_plan_id"],
        "route_id": plan_row["route_id"],
        "display_name": plan_row["display_name"],
        "target_prover_family": "rocq",
        "revision_status": "ROUTE_REVISION_APPLIED",
        "original_selected_primitives": plan_row["selected_primitives"],
        "revised_selected_primitives": plan_row["selected_primitives"],
        "added_primitives": [],
        "removed_primitives": [],
        "original_delta_primitives": [
            node["primitive"]
            for node in plan_row["minimal_additional_formalization_nodes"]
        ],
        "revised_delta_primitives": [
            node["primitive"]
            for node in plan_row["minimal_additional_formalization_nodes"]
        ],
        "added_delta_primitives": [],
        "source_refs": ["rocq exchangeability note"],
        "formal_declaration_hits": [
            {
                "primitive": "rocq_exchangeability_bridge",
                "coverage_status": "bridge_needed",
                "declaration": "Rocq.Probability.exchangeable",
            }
        ],
        "route_revision_reasons": ["Rocq declaration search selected the target library"],
        "route_revision_summaries": ["preserve Rocq target for replay"],
        "revised_informal_knowledge_dag_nodes": [
            {
                "node_id": "informal:rocq_exchangeability_bridge",
                "label": "rocq_exchangeability_bridge",
                "primitive": "rocq_exchangeability_bridge",
                "source_ref": "rocq exchangeability note",
            }
        ],
        "revised_formal_realization_dag_nodes": [
            {
                "node_id": "formal:rocq_exchangeability_bridge",
                "label": "rocq_exchangeability_bridge",
                "primitive": "rocq_exchangeability_bridge",
                "coverage_status": "bridge_needed",
            }
        ],
        "revised_route_alignment_edges": [
            {
                "source": "informal:rocq_exchangeability_bridge",
                "target": "formal:rocq_exchangeability_bridge",
                "kind": "aligned_to_formal_realization_candidate",
                "edge_type": "revised_informal_to_formal_alignment",
                "primitive": "rocq_exchangeability_bridge",
                "alignment_status": "bridge_needed",
            }
        ],
        "unaligned_primitives": [],
    }
    (overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_revision_overlay",
                "rows": [overlay_row],
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_route_replan_handoff(
        plan_dir,
        overlay_dir,
        handoff_dir,
    )

    assert payload["all_ok"]
    assert payload["n_revised_formal_realization_dag_nodes"] >= 1
    assert payload["n_revised_lean_realization_dag_nodes"] == 0
    row = payload["rows"][0]
    assert row["revised_formal_realization_dag_nodes"]
    assert row["revised_lean_realization_dag_nodes"] == ()
    assert row["formal_declaration_hits"] == (
        {
            "primitive": "rocq_exchangeability_bridge",
            "coverage_status": "bridge_needed",
            "declaration": "Rocq.Probability.exchangeable",
        },
    )
    assert row["lean_declaration_hits"] == ()
    assert row["standalone_route"]["target_prover_family"] == "rocq"
    assert row["standalone_route"]["replan_metadata"]["target_prover_family"] == "rocq"
    assert row["standalone_route"]["revised_formal_realization_dag_nodes"]
    assert row["standalone_route"]["revised_lean_realization_dag_nodes"] == ()
    assert row["standalone_route"]["replan_metadata"][
        "revised_formal_realization_dag_nodes"
    ]
    assert row["standalone_route"]["replan_metadata"][
        "revised_lean_realization_dag_nodes"
    ] == ()
    seed_path = handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json"
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    assert seed["target_prover_family"] == "rocq"
    assert seed["routes"][0]["target_prover_family"] == "rocq"
    assert seed["routes"][0]["replan_metadata"]["target_prover_family"] == "rocq"
    assert seed["routes"][0]["revised_formal_realization_dag_nodes"]
    assert seed["routes"][0]["revised_lean_realization_dag_nodes"] == []
    assert seed["routes"][0]["replan_metadata"][
        "revised_formal_realization_dag_nodes"
    ]
    assert seed["routes"][0]["replan_metadata"][
        "revised_lean_realization_dag_nodes"
    ] == []
    assert seed["routes"][0]["replan_metadata"]["formal_declaration_hits"] == [
        {
            "primitive": "rocq_exchangeability_bridge",
            "coverage_status": "bridge_needed",
            "declaration": "Rocq.Probability.exchangeable",
        }
    ]
    assert seed["routes"][0]["replan_metadata"]["lean_declaration_hits"] == []
    bad_legacy_alias_row = dict(row)
    bad_legacy_alias_row["lean_declaration_hits"] = [
        {
            "primitive": "rocq_exchangeability_bridge",
            "declaration": "Rocq.Probability.exchangeable",
            "target_prover_family": "rocq",
        }
    ]
    assert (
        "lean_declaration_hits is a Lean-only legacy alias; non-Lean route replan "
        "handoff rows must use formal_declaration_hits only"
        in validate_route_replan_handoff_row(
            bad_legacy_alias_row,
            route_replan_handoff_row_json_schema(),
        )
    )

    next_plan = export_formalization_gap_planner_standalone_plan(
        seed_path,
        next_plan_dir,
    )

    assert next_plan["all_ok"]
    assert next_plan["target_prover_family"] == "rocq"
    assert next_plan["rows"][0]["target_prover_family"] == "rocq"
    assert next_plan["rows"][0]["standalone_input_trace"][
        "target_prover_family"
    ] == "rocq"
    assert next_plan["rows"][0]["standalone_input_trace"][
        "revised_formal_realization_dag_nodes"
    ]
    assert next_plan["rows"][0]["standalone_input_trace"][
        "revised_lean_realization_dag_nodes"
    ] == []

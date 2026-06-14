from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
)
from ai_statistician.formalization_gap_planner_cross_prover_matrix_audit import (
    audit_formalization_gap_planner_cross_prover_matrix,
    cross_prover_matrix_audit_row_json_schema,
    cross_prover_target_summary_json_schema,
    validate_cross_prover_target_summary_payload,
)
from ai_statistician.formalization_gap_planner_prover_adapter_contract import (
    prover_adapter_packet_json_schema,
    prover_adapter_response_validation_row_json_schema,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_cross_prover_matrix_audit_exports_all_reuse_targets() -> None:
    root = Path("runs/test_formalization_gap_planner_cross_prover_matrix_audit")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    out_dir = root / "matrix"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:cross-prover",
                "routes": [
                    {
                        "display_name": "demo_cross_prover_route",
                        "theorem_statement": "A reusable bridge route.",
                        "residual_goal_contexts": [
                            {
                                "source_kind": "proof_state_feedback",
                                "residual_goal": (
                                    "rank_uniformity_bridge needs a library "
                                    "coverage wrapper"
                                ),
                                "residual_goals": [
                                    "coverage wrapper for rank_uniformity_bridge"
                                ],
                                "residual_primitives": [
                                    "rank_uniformity_bridge"
                                ],
                                "source_refs": ["paper:demo#rank-uniformity"],
                                "source_snippets": [
                                    {
                                        "source_ref": (
                                            "paper:demo#rank-uniformity"
                                        ),
                                        "text": (
                                            "Fixture source backs the wrapper "
                                            "side condition."
                                        ),
                                    }
                                ],
                                "formal_gap_boundary": (
                                    "Formal boundary: translate this residual "
                                    "before target-kernel replay."
                                ),
                            }
                        ],
                        "quality_controls": {
                            "resource_contract_ids": [
                                "lean_lsp:proof_state_feedback"
                            ],
                            "response_validation_signals": [
                                "residual_goals_or_diagnostics_present"
                            ],
                            "stop_conditions": [
                                "residual interpreted or source search requested"
                            ],
                        },
                        "primitives": [
                            {
                                "primitive": "rank_uniformity_bridge",
                                "coverage_status": "bridge_needed",
                            },
                            {
                                "primitive": "coverage_wrapper",
                                "coverage_status": "wrapper_needed",
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

    payload = audit_formalization_gap_planner_cross_prover_matrix(plan_dir, out_dir)

    assert payload["all_ok"]
    assert payload["n_targets"] == 4
    assert payload["n_targets_ok"] == 4
    assert payload["target_prover_families"] == ("lean4", "rocq", "isabelle", "agda")
    assert payload["n_total_packets"] == 4 * plan_payload["n_portable_work_packets"]
    assert payload["n_total_packet_ok"] == payload["n_total_packets"]
    assert payload["n_total_packet_schema_valid"] == payload["n_total_packets"]
    assert payload["n_total_packets_schema_invalid"] == 0
    assert payload["n_matrix_row_schema_valid"] == payload["n_targets"]
    assert payload["n_matrix_row_schema_invalid"] == 0
    assert payload["n_packet_row_schema_valid"] == payload["n_total_packets"]
    assert payload["n_packet_row_schema_invalid"] == 0
    assert (
        payload["n_response_validation_row_schema_valid"]
        == payload["n_total_packets"]
    )
    assert payload["n_response_validation_row_schema_invalid"] == 0
    assert payload["n_target_summary_contract_errors"] == 0
    assert payload["target_summary"]["all_ok"]
    assert payload["target_summary"]["n_target_rows"] == payload["n_targets"]
    assert validate_cross_prover_target_summary_payload(
        payload["target_summary"],
        payload["cross_prover_target_summary_schema"],
    ) == ()
    assert payload["n_total_packets_with_alignment"] == payload["n_total_packets"]
    assert payload["n_total_packets_missing_alignment"] == 0
    assert (
        payload["n_total_packets_with_standalone_input_trace"]
        == payload["n_total_packets"]
    )
    assert payload["n_total_packets_missing_standalone_input_trace"] == 0
    assert (
        payload["n_total_packets_with_target_library_snapshot_trace"]
        == payload["n_total_packets"]
    )
    assert payload["n_total_packets_missing_target_library_snapshot_trace"] == 0
    assert payload["n_total_packets_target_library_snapshot_mismatch"] == 0
    assert payload["n_total_packets_with_replan_metadata_trace"] == 0
    assert (
        payload["n_total_packets_with_residual_goal_contexts"]
        == payload["n_total_packets"]
    )
    assert (
        payload["n_total_packet_residual_goal_contexts"]
        == payload["n_total_packets"]
    )
    assert payload["packet_residual_context_source_kinds"] == (
        "proof_state_feedback",
    )
    assert (
        payload["n_total_packet_residual_contexts_with_source_refs"]
        == payload["n_total_packets"]
    )
    assert (
        payload[
            "n_total_packet_residual_contexts_with_formal_gap_boundary"
        ]
        == payload["n_total_packets"]
    )
    assert payload["n_total_packets_with_quality_controls"] == payload[
        "n_total_packets"
    ]
    assert payload["n_total_packet_quality_control_fields"] == (
        3 * payload["n_total_packets"]
    )
    assert payload["packet_quality_control_fields"] == (
        "resource_contract_ids",
        "response_validation_signals",
        "stop_conditions",
    )
    assert payload["packet_quality_control_resource_contract_ids"] == (
        "lean_lsp:proof_state_feedback",
    )
    assert payload["packet_quality_control_response_validation_signals"] == (
        "residual_goals_or_diagnostics_present",
    )
    assert payload["packet_quality_control_stop_conditions"] == (
        "residual interpreted or source search requested",
    )
    assert payload["by_total_packet_quality_control_field"][
        "resource_contract_ids"
    ] == {
        "n_packets": payload["n_total_packets"],
        "n_values": 1,
        "values": ("lean_lsp:proof_state_feedback",),
    }
    assert payload["n_total_packets_with_llm_route_adoption_status"] == 0
    assert payload["n_total_packets_llm_route_adoption_ready"] == 0
    assert payload["n_total_packets_llm_route_adoption_pending_refinement"] == 0
    assert payload["n_total_packet_llm_route_adoption_blockers"] == 0
    assert (
        payload[
            "n_total_packet_llm_route_adoption_pending_quality_control_blockers"
        ]
        == 0
    )
    assert payload["by_total_packet_llm_route_adoption_status"] == {}
    assert payload["n_awaiting_adapter_mapping"] == payload["n_total_packets"]
    assert payload["n_unmatched_adapter_responses"] == 0
    assert payload["n_rejected"] == 0
    assert payload["n_kernel_verified_claims_rejected"] == 0
    assert payload["packet_count_consistent"]
    assert payload["alignment_packet_count_consistent"]
    assert payload["standalone_input_trace_packet_count_consistent"]
    assert payload["target_library_snapshot_trace_packet_count_consistent"]
    assert payload["quality_control_packet_count_consistent"]
    assert payload["residual_context_packet_count_consistent"]
    assert (
        payload["target_summary"]["n_total_packets_with_standalone_input_trace"]
        == payload["n_total_packets"]
    )
    assert (
        payload["target_summary"]["n_total_packets_missing_standalone_input_trace"]
        == 0
    )
    assert (
        payload["target_summary"][
            "n_total_packets_with_target_library_snapshot_trace"
        ]
        == payload["n_total_packets"]
    )
    assert (
        payload["target_summary"][
            "n_total_packets_missing_target_library_snapshot_trace"
        ]
        == 0
    )
    assert (
        payload["target_summary"]["n_total_packets_target_library_snapshot_mismatch"]
        == 0
    )
    assert payload["target_summary"]["n_unmatched_adapter_responses"] == 0
    assert (
        payload["target_summary"]["n_total_packets_with_residual_goal_contexts"]
        == payload["n_total_packets"]
    )
    assert (
        payload["target_summary"]["n_total_packet_residual_goal_contexts"]
        == payload["n_total_packets"]
    )
    assert payload["target_summary"][
        "packet_residual_context_source_kinds"
    ] == ("proof_state_feedback",)
    assert (
        payload["target_summary"][
            "n_total_packet_residual_contexts_with_source_refs"
        ]
        == payload["n_total_packets"]
    )
    assert (
        payload["target_summary"][
            "n_total_packet_residual_contexts_with_formal_gap_boundary"
        ]
        == payload["n_total_packets"]
    )
    assert (
        payload["target_summary"]["n_total_packets_with_quality_controls"]
        == payload["n_total_packets"]
    )
    assert payload["target_summary"]["n_total_packet_quality_control_fields"] == (
        3 * payload["n_total_packets"]
    )
    assert payload["target_summary"]["packet_quality_control_fields"] == (
        "resource_contract_ids",
        "response_validation_signals",
        "stop_conditions",
    )
    assert payload["target_summary"]["by_total_packet_quality_control_field"][
        "resource_contract_ids"
    ] == {
        "n_packets": payload["n_total_packets"],
        "n_values": 1,
        "values": ("lean_lsp:proof_state_feedback",),
    }
    assert (
        payload["target_summary"]["n_total_packets_with_llm_route_adoption_status"]
        == 0
    )
    assert (
        payload["target_summary"][
            "n_total_packet_llm_route_adoption_pending_quality_control_blockers"
        ]
        == 0
    )
    assert payload["target_summary"][
        "by_total_packet_llm_route_adoption_status"
    ] == {}
    assert all(
        row["n_packets_with_alignment"] == row["n_packets"]
        and row["n_packet_schema_valid"] == row["n_packets"]
        and row["n_packets_schema_invalid"] == 0
        and row["n_packets_missing_alignment"] == 0
        and row["n_packets_with_standalone_input_trace"] == row["n_packets"]
        and row["n_packets_missing_standalone_input_trace"] == 0
        and row["n_packets_with_target_library_snapshot_trace"] == row["n_packets"]
        and row["n_packets_missing_target_library_snapshot_trace"] == 0
        and row["n_packets_target_library_snapshot_mismatch"] == 0
        and row["n_packets_with_residual_goal_contexts"] == row["n_packets"]
        and row["n_packet_residual_goal_contexts"] == row["n_packets"]
        and row["packet_residual_context_source_kinds"]
        == ("proof_state_feedback",)
        and row["n_packet_residual_contexts_with_source_refs"] == row["n_packets"]
        and row["n_packet_residual_contexts_with_formal_gap_boundary"]
        == row["n_packets"]
        and row["n_packets_with_quality_controls"] == row["n_packets"]
        and row["n_packet_quality_control_fields"] == 3 * row["n_packets"]
        and row["packet_quality_control_fields"]
        == (
            "resource_contract_ids",
            "response_validation_signals",
            "stop_conditions",
        )
        and row["n_packets_with_llm_route_adoption_status"] == 0
        and row["n_packet_llm_route_adoption_blockers"] == 0
        and row[
            "n_packet_llm_route_adoption_pending_quality_control_blockers"
        ]
        == 0
        and row["n_unmatched_adapter_responses"] == 0
        for row in payload["matrix_rows"]
    )
    assert all(
        packet["standalone_input_trace"]["source_prover_family"] == "lean4"
        and packet["standalone_input_trace"]["target_prover_family"]
        == packet["target_prover_family"]
        and packet["standalone_input_trace"]["target_library_snapshot_ref"]
        == packet["library_snapshot_ref"]
        and packet["standalone_input_trace"]["trace_target_projection"]
        == "target_prover_adapter_contract"
        and packet["n_residual_goal_contexts"] == 1
        and packet["residual_context_source_kinds"] == (
            "proof_state_feedback",
        )
        and packet["standalone_input_trace"]["has_residual_goal_contexts"]
        and packet["standalone_input_trace"]["residual_goal_context_count"]
        == 1
        and packet["standalone_input_trace"]["has_quality_controls"]
        and packet["standalone_input_trace"]["quality_control_fields"]
        == [
            "resource_contract_ids",
            "response_validation_signals",
            "stop_conditions",
        ]
        for packet in payload["packet_rows"]
    )
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (
        out_dir / "formalization_gap_planner_cross_prover_matrix_audit_manifest.json"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_cross_prover_packets.jsonl"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_cross_prover_target_summary.json"
    ).exists()
    assert (
        json.loads(
            (
                out_dir
                / "formalization_gap_planner_cross_prover_target_summary.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == cross_prover_target_summary_json_schema()["$id"]
    )
    assert (
        out_dir / "formalization_gap_planner_cross_prover_response_validation.jsonl"
    ).exists()
    assert (
        json.loads(
            (
                out_dir
                / "formalization_gap_planner_cross_prover_matrix_audit_row.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == cross_prover_matrix_audit_row_json_schema()["$id"]
    )
    assert (
        json.loads(
            (
                out_dir / "formalization_gap_planner_prover_adapter_packet.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == prover_adapter_packet_json_schema()["$id"]
    )
    assert (
        json.loads(
            (
                out_dir
                / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == prover_adapter_response_validation_row_json_schema()["$id"]
    )
    assert (
        out_dir
        / "target_contracts"
        / "rocq"
        / "formalization_gap_planner_prover_adapter_contract_manifest.json"
    ).exists()


def test_cross_prover_matrix_counts_quality_control_route_adoption_blockers() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_cross_prover_matrix_quality_blockers"
    )
    plan_dir = root / "plan"
    out_dir = root / "matrix"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
                "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
                "library_snapshot_ref": "lean_fixture_snapshot",
                "rows": [
                    {
                        "goal_plan_id": "goal:pending",
                        "route_id": "route:pending",
                        "display_name": "pending quality-control route",
                        "target_prover_family": "lean4",
                        "standalone_input_trace": {
                            "source_route_id": "route:pending",
                            "llm_route_planner_route_adoption_status": (
                                "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
                            ),
                            "llm_route_planner_route_adoption_blockers": [
                                "search_requests_pending_evidence",
                                "planner_next_actions_pending_evidence",
                                "source_grounding_obligations_pending",
                                "quality_control_obligations_pending",
                            ],
                        },
                        "route_alignment_edges": [
                            {
                                "source": "informal:rank_uniformity",
                                "target": "formal:rank_uniformity_bridge",
                                "kind": "aligned_to_formal_realization_candidate",
                                "edge_type": "informal_to_formal_alignment",
                                "primitive": "rank_uniformity",
                                "action_class": "bridge_lemma",
                                "alignment_status": "bridge_delta",
                                "proof_evidence_status": (
                                    "GOAL_CONDITIONED_MINIMAL_FORMALIZATION_PLAN_NOT_PROOF_EVIDENCE"
                                ),
                                "proof_evidence_boundary": "not theorem proof evidence",
                            }
                        ],
                        "portable_work_packets": [
                            {
                                "primitive": "rank_uniformity",
                                "action_class": "bridge_lemma",
                                "expected_cost": "small",
                                "worker_packet_kind": "prove_bridge_lemma",
                                "required_gate": "target prover kernel verification",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_cross_prover_matrix(
        plan_dir,
        out_dir,
        target_prover_families=("rocq", "isabelle"),
    )

    assert payload["n_total_packets_with_llm_route_adoption_status"] == 2
    assert payload["n_total_packets_llm_route_adoption_pending_refinement"] == 2
    assert payload["n_total_packet_llm_route_adoption_blockers"] == 8
    assert (
        payload[
            "n_total_packet_llm_route_adoption_pending_quality_control_blockers"
        ]
        == 2
    )
    assert (
        payload[
            "n_total_packet_llm_route_adoption_pending_source_grounding_blockers"
        ]
        == 2
    )
    assert payload["by_total_packet_llm_route_adoption_status"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 2
    }
    assert (
        payload["target_summary"][
            "n_total_packet_llm_route_adoption_pending_quality_control_blockers"
        ]
        == 2
    )
    assert (
        payload["target_summary"][
            "n_total_packet_llm_route_adoption_pending_source_grounding_blockers"
        ]
        == 2
    )
    assert all(
        row["n_packet_llm_route_adoption_pending_quality_control_blockers"]
        == 1
        for row in payload["matrix_rows"]
    )
    assert all(
        row["n_packet_llm_route_adoption_pending_source_grounding_blockers"]
        == 1
        for row in payload["matrix_rows"]
    )
    assert all(
        row["n_packet_llm_route_adoption_pending_quality_control_blockers"]
        == 1
        for row in payload["target_summary"]["target_rows"]
    )
    assert all(
        row["n_packet_llm_route_adoption_pending_source_grounding_blockers"]
        == 1
        for row in payload["target_summary"]["target_rows"]
    )

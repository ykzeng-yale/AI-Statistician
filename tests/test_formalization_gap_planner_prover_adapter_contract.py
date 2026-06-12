from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_contract import (
    LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
    PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
)
from ai_statistician.formalization_gap_planner_prover_adapter_contract import (
    PROVER_ADAPTER_PACKET_SCHEMA_ID,
    PROVER_ADAPTER_RESPONSE_SCHEMA_ID,
    PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID,
    export_formalization_gap_planner_prover_adapter_contract,
    prover_adapter_packet_json_schema,
    prover_adapter_response_json_schema,
    prover_adapter_response_validation_row_json_schema,
    validate_prover_adapter_packet_row,
)


def test_prover_adapter_contract_validates_cross_prover_mapping_response() -> None:
    root = Path("runs/test_formalization_gap_planner_prover_adapter_contract")
    plan_dir = root / "plan"
    out_dir = root / "contract"
    response_jsonl = root / "adapter_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    display_name = "causal_ate_aipw:aipw_double_robustness:skeleton"
    plan_row = {
        "schema_version": 1,
        "goal_plan_id": "goal:test",
        "route_id": "route:test",
        "display_name": display_name,
        "target_prover_family": "lean4_adapter_with_portable_gap_schema",
        "standalone_input_trace": {
            "source_route_id": "route:test",
            "route_index": 1,
            "has_replan_metadata": True,
            "replan_metadata": {"revision_reason": "fixture refinement"},
            "applied_hook_kinds": ["resource_response_ledger"],
            "quality_controls": {
                "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
                "response_validation_signals": [
                    "residual_goals_or_diagnostics_present"
                ],
                "stop_conditions": [
                    "residual interpreted or source search requested"
                ],
            },
            "has_quality_controls": True,
            "quality_control_fields": [
                "resource_contract_ids",
                "response_validation_signals",
                "stop_conditions",
            ],
        },
        "route_alignment_edges": [
            {
                "source": "informal:conditional_mean_residual_zero",
                "target": "formal:conditional_mean_residual_zero",
                "kind": "aligned_to_formal_realization_candidate",
                "edge_type": "informal_to_formal_alignment",
                "primitive": "conditional_mean_residual_zero",
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
                "primitive": "conditional_mean_residual_zero",
                "action_class": "bridge_lemma",
                "expected_cost": "small",
                "worker_packet_kind": "prove_bridge_lemma",
                "required_gate": "target prover kernel verification",
            }
        ],
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
                "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
                "library_snapshot_ref": "lean_fixture_snapshot",
                "rows": [plan_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    response_jsonl.write_text(
        json.dumps(
            {
                "goal_plan_id": "goal:test",
                "route_id": "route:test",
                "primitive": "conditional_mean_residual_zero",
                "target_prover_family": "coq",
                "mapping_status": "ready_for_kernel_attempt",
                "translated_statement": "Theorem conditional_mean_residual_zero : True.",
                "translated_imports": ["Coq.Init.Logic"],
                "verifier_command": "coqc GapPlannerProbe.v",
                "library_snapshot_ref": "rocq_fixture_snapshot",
                "semantic_alignment_notes": "Fixture statement preserves the primitive label for adapter-contract testing.",
                "kernel_verified": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_prover_adapter_contract(
        plan_dir,
        out_dir,
        target_prover_family="coq",
        library_snapshot_ref="rocq_fixture_snapshot",
        adapter_response_jsonl=response_jsonl,
    )

    assert payload["all_ok"]
    assert payload["target_prover_family"] == "rocq"
    assert payload["n_packets"] == 1
    assert payload["n_packets_with_alignment"] == 1
    assert payload["n_packets_with_standalone_input_trace"] == 1
    assert payload["n_packets_missing_standalone_input_trace"] == 0
    assert payload["n_packets_with_replan_metadata_trace"] == 1
    assert payload["n_packets_with_quality_controls"] == 1
    assert payload["n_packet_quality_control_fields"] == 3
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
    assert payload["by_packet_quality_control_field"][
        "resource_contract_ids"
    ] == {
        "n_packets": 1,
        "n_values": 1,
        "values": ("lean_lsp:proof_state_feedback",),
    }
    assert payload["n_packets_with_llm_route_adoption_status"] == 0
    assert payload["n_packet_llm_route_adoption_blockers"] == 0
    assert (
        payload[
            "n_packet_llm_route_adoption_pending_quality_control_blockers"
        ]
        == 0
    )
    assert payload["n_packet_schema_valid"] == payload["n_packets"]
    assert payload["n_response_present"] == 1
    assert payload["n_response_contract_ok"] == 1
    assert payload["n_rejected"] == 0
    assert "coq" in prover_adapter_response_json_schema()["properties"][
        "target_prover_family"
    ]["enum"]
    assert payload["response_validation_rows"][0]["mapping_status"] == "ready_for_kernel_attempt"
    assert payload["response_validation_rows"][0]["target_prover_family"] == "rocq"
    assert "kernel verification" in payload["packets"][0]["acceptance_gate"]
    assert payload["packets"][0]["alignment_status"] == "bridge_delta"
    assert payload["packets"][0]["route_alignment_edge"]["primitive"] == (
        "conditional_mean_residual_zero"
    )
    assert payload["packets"][0]["standalone_input_trace"]["source_route_id"] == (
        "route:test"
    )
    assert payload["packets"][0]["standalone_input_trace"]["has_replan_metadata"]
    assert payload["packets"][0]["standalone_input_trace"][
        "source_prover_family"
    ] == "lean4_adapter_with_portable_gap_schema"
    assert payload["packets"][0]["standalone_input_trace"][
        "target_prover_family"
    ] == "rocq"
    assert payload["packets"][0]["standalone_input_trace"][
        "target_library_snapshot_ref"
    ] == "rocq_fixture_snapshot"
    assert payload["packets"][0]["standalone_input_trace"][
        "trace_target_projection"
    ] == "target_prover_adapter_contract"
    assert payload["packets"][0]["standalone_input_trace"]["quality_controls"] == {
        "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
        "response_validation_signals": [
            "residual_goals_or_diagnostics_present"
        ],
        "stop_conditions": [
            "residual interpreted or source search requested"
        ],
    }
    assert payload["packets"][0]["standalone_input_trace"][
        "has_quality_controls"
    ]
    assert payload["packets"][0]["standalone_input_trace"][
        "quality_control_fields"
    ] == [
        "resource_contract_ids",
        "response_validation_signals",
        "stop_conditions",
    ]
    assert (
        payload["prover_adapter_packet_schema"]["$id"]
        == PROVER_ADAPTER_PACKET_SCHEMA_ID
    )
    assert (
        payload["prover_adapter_response_validation_row_schema"]["$id"]
        == PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID
    )
    assert not validate_prover_adapter_packet_row(payload["packets"][0])
    bad_packet = dict(payload["packets"][0])
    bad_packet.pop("route_alignment_edge")
    assert "route_alignment_edge required" in validate_prover_adapter_packet_row(
        bad_packet,
        prover_adapter_packet_json_schema(),
    )
    bad_packet = dict(payload["packets"][0])
    bad_packet.pop("standalone_input_trace")
    assert "standalone_input_trace required" in validate_prover_adapter_packet_row(
        bad_packet,
        prover_adapter_packet_json_schema(),
    )
    bad_packet = dict(payload["packets"][0])
    bad_packet["standalone_input_trace"] = dict(bad_packet["standalone_input_trace"])
    bad_packet["standalone_input_trace"]["target_prover_family"] = "lean4"
    assert (
        "standalone_input_trace.target_prover_family lean4 does not match packet rocq"
        in validate_prover_adapter_packet_row(
            bad_packet,
            prover_adapter_packet_json_schema(),
        )
    )
    bad_packet = dict(payload["packets"][0])
    bad_packet["standalone_input_trace"] = dict(bad_packet["standalone_input_trace"])
    bad_packet["standalone_input_trace"]["has_quality_controls"] = False
    assert any(
        "standalone_input_trace.has_quality_controls mismatch" in error
        for error in validate_prover_adapter_packet_row(
            bad_packet,
            prover_adapter_packet_json_schema(),
        )
    )
    bad_packet = dict(payload["packets"][0])
    bad_packet["standalone_input_trace"] = dict(bad_packet["standalone_input_trace"])
    bad_packet["standalone_input_trace"]["quality_control_fields"] = []
    assert any(
        "standalone_input_trace.quality_control_fields mismatch" in error
        for error in validate_prover_adapter_packet_row(
            bad_packet,
            prover_adapter_packet_json_schema(),
        )
    )
    assert (
        out_dir / "formalization_gap_planner_prover_adapter_packet.schema.json"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_prover_adapter_response.schema.json"
    ).exists()
    assert (
        json.loads(
            (
                out_dir
                / "formalization_gap_planner_prover_adapter_response_validation_row.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == prover_adapter_response_validation_row_json_schema()["$id"]
        == PROVER_ADAPTER_RESPONSE_VALIDATION_ROW_SCHEMA_ID
    )
    assert (
        json.loads(
            (
                out_dir / "formalization_gap_planner_prover_adapter_response.schema.json"
            ).read_text(encoding="utf-8")
        )["$id"]
        == prover_adapter_response_json_schema()["$id"]
        == PROVER_ADAPTER_RESPONSE_SCHEMA_ID
    )
    assert (
        out_dir / "formalization_gap_planner_prover_adapter_packets.jsonl"
    ).exists()


def test_prover_adapter_contract_rejects_kernel_ready_mapping_for_pending_llm_route() -> None:
    root = Path("runs/test_formalization_gap_planner_prover_adapter_contract_pending_llm")
    plan_dir = root / "plan"
    out_dir = root / "contract"
    response_jsonl = root / "adapter_responses.jsonl"
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
                        "display_name": "pending llm route",
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
    response_jsonl.write_text(
        json.dumps(
            {
                "goal_plan_id": "goal:pending",
                "route_id": "route:pending",
                "primitive": "rank_uniformity",
                "target_prover_family": "rocq",
                "mapping_status": "ready_for_kernel_attempt",
                "translated_statement": "Theorem rank_uniformity : True.",
                "translated_imports": ["Coq.Init.Logic"],
                "verifier_command": "coqc RankUniformity.v",
                "library_snapshot_ref": "rocq_fixture_snapshot",
                "semantic_alignment_notes": (
                    "The target statement maps the primitive, but the source route "
                    "is still blocked by LLM planner adoption gates."
                ),
                "kernel_verified": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_prover_adapter_contract(
        plan_dir,
        out_dir,
        target_prover_family="rocq",
        library_snapshot_ref="rocq_fixture_snapshot",
        adapter_response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_packets_with_llm_route_adoption_status"] == 1
    assert payload["n_packets_llm_route_adoption_pending_refinement"] == 1
    assert payload["n_packet_llm_route_adoption_blockers"] == 4
    assert (
        payload[
            "n_packet_llm_route_adoption_pending_quality_control_blockers"
        ]
        == 1
    )
    assert (
        payload[
            "n_packet_llm_route_adoption_pending_source_grounding_blockers"
        ]
        == 1
    )
    assert payload["by_packet_llm_route_adoption_status"] == {
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION": 1
    }
    packet = payload["packets"][0]
    assert packet["llm_route_planner_route_adoption_status"] == (
        "PENDING_REFINEMENT_BEFORE_ROUTE_ADOPTION"
    )
    assert list(packet["llm_route_planner_route_adoption_blockers"]) == [
        "search_requests_pending_evidence",
        "planner_next_actions_pending_evidence",
        "source_grounding_obligations_pending",
        "quality_control_obligations_pending",
    ]
    validation = payload["response_validation_rows"][0]
    assert validation["acceptance_status"] == (
        "REJECTED_PROVER_ADAPTER_MAPPING_CONTRACT"
    )
    assert any(
        "ready_for_kernel_attempt requires llm_route_planner_route_adoption_status"
        in error
        for error in validation["errors"]
    )


def test_prover_adapter_contract_rejects_kernel_claims_in_mapping_layer() -> None:
    root = Path("runs/test_formalization_gap_planner_prover_adapter_contract_rejects")
    plan_dir = root / "plan"
    out_dir = root / "contract"
    response_jsonl = root / "adapter_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
                "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
                "rows": [
                    {
                        "goal_plan_id": "goal:test",
                        "route_id": "route:test",
                        "display_name": "demo:target",
                        "target_prover_family": "lean4",
                        "portable_work_packets": [
                            {
                                "primitive": "demo_primitive",
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
    response_jsonl.write_text(
        json.dumps(
            {
                "goal_plan_id": "goal:test",
                "route_id": "route:test",
                "primitive": "demo_primitive",
                "target_prover_family": "isabelle",
                "mapping_status": "ready_for_kernel_attempt",
                "translated_statement": "theorem demo_primitive: True",
                "translated_imports": ["Main"],
                "verifier_command": "isabelle build -D .",
                "library_snapshot_ref": "isabelle_fixture",
                "semantic_alignment_notes": "mapping fixture",
                "kernel_verified": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_prover_adapter_contract(
        plan_dir,
        out_dir,
        target_prover_family="isabelle",
        library_snapshot_ref="isabelle_fixture",
        adapter_response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_kernel_verified_claims_rejected"] == 1
    assert payload["n_rejected"] == 1
    assert "kernel_verified=true" in payload["response_validation_rows"][0]["errors"][0]


def test_prover_adapter_contract_rejects_unmatched_and_stale_responses() -> None:
    root = Path("runs/test_formalization_gap_planner_prover_adapter_contract_unmatched")
    plan_dir = root / "plan"
    out_dir = root / "contract"
    response_jsonl = root / "adapter_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": LIBRARY_AWARE_FORMALIZATION_GAP_PLANNER_NAME,
                "portable_schema_id": PORTABLE_FORMALIZATION_GAP_PLAN_SCHEMA_ID,
                "rows": [
                    {
                        "goal_plan_id": "goal:stale",
                        "route_id": "route:stale",
                        "display_name": "stale response route",
                        "target_prover_family": "lean4",
                        "route_alignment_edges": [
                            {
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
    responses = [
        {
            "goal_plan_id": "goal:stale",
            "route_id": "route:stale",
            "primitive": "rank_uniformity",
            "target_prover_family": "rocq",
            "mapping_status": "ready_for_kernel_attempt",
            "translated_statement": "Theorem rank_uniformity : True.",
            "translated_imports": ["Coq.Init.Logic"],
            "verifier_command": "coqc RankUniformity.v",
            "library_snapshot_ref": "stale_rocq_snapshot",
            "semantic_alignment_notes": "stale snapshot should be rejected",
            "kernel_verified": False,
        },
        {
            "goal_plan_id": "goal:stale",
            "route_id": "route:stale",
            "primitive": "unexported_bridge",
            "target_prover_family": "rocq",
            "mapping_status": "needs_statement_translation",
            "translated_statement": "",
            "translated_imports": [],
            "verifier_command": "",
            "library_snapshot_ref": "rocq_snapshot",
            "semantic_alignment_notes": "unmatched response should not be ignored",
            "residual_translation_gaps": ["no exported packet"],
            "kernel_verified": False,
        },
    ]
    response_jsonl.write_text(
        "\n".join(json.dumps(response, sort_keys=True) for response in responses) + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_prover_adapter_contract(
        plan_dir,
        out_dir,
        target_prover_family="rocq",
        library_snapshot_ref="rocq_snapshot",
        adapter_response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_responses"] == 2
    assert payload["n_response_present"] == 1
    assert payload["n_unmatched_adapter_responses"] == 1
    assert payload["n_response_contract_ok"] == 0
    assert payload["n_rejected"] == 1
    assert any("unmatched prover adapter response" in error for error in payload["errors"])
    validation = payload["response_validation_rows"][0]
    assert validation["acceptance_status"] == "REJECTED_PROVER_ADAPTER_MAPPING_CONTRACT"
    assert any("library_snapshot_ref" in error for error in validation["errors"])

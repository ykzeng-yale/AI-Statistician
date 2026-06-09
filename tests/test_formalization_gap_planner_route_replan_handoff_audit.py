from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_route_replan_handoff import (
    PROOF_EVIDENCE_BOUNDARY,
    PROOF_EVIDENCE_STATUS,
)
from ai_statistician.formalization_gap_planner_route_replan_handoff_audit import (
    audit_formalization_gap_planner_route_replan_handoff,
    route_replan_handoff_audit_row_json_schema,
    validate_route_replan_handoff_audit_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    standalone_input_json_schema,
)


def test_route_replan_handoff_audit_roundtrips_seed_and_blocks_proof_claims() -> None:
    root = Path("runs/test_formalization_gap_planner_route_replan_handoff_audit")
    handoff_dir = root / "handoff"
    audit_dir = root / "audit"
    metadata_audit_dir = root / "metadata_audit"
    quality_audit_dir = root / "quality_audit"
    reject_audit_dir = root / "reject_audit"
    shutil.rmtree(root, ignore_errors=True)
    handoff_dir.mkdir(parents=True, exist_ok=True)
    route_id = "replan_route:rank_uniformity_fixture"
    alignment_edges = [
        {
            "source": "informal:rank_uniformity",
            "target": "lean:rank_uniformity",
            "kind": "aligned_to_formal_realization_candidate",
            "edge_type": "revised_informal_to_formal_alignment",
            "primitive": "rank_uniformity",
            "alignment_status": "bridge_needed",
        }
    ]
    informal_nodes = [
        {
            "node_id": "informal:rank_uniformity",
            "label": "rank_uniformity",
            "primitive": "rank_uniformity",
        }
    ]
    lean_nodes = [
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
        "resource_id": "lean_lsp_mcp",
        "target_primitives": ["rank_uniformity"],
        "request_phase": "frontier_escalation",
        "expected_response_artifact": "proof_state_or_prover_feedback_response",
        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
        "matched_response_contract_fields": ["residual_goals"],
        "missing_response_contract_fields": [],
        "prover_attempt_status": "failed_with_residual_goals",
        "prover_diagnostic_signature": "missing_rank_uniformity_bridge",
        "proof_evidence_boundary": "not theorem proof evidence",
    }
    source_snippet = {
        "source_ref": "Lei-Wasserman distribution-free prediction",
        "claim": "exchangeability supports rank uniformity",
        "excerpt": "The source route supplies the rank-uniformity bridge used by the replan seed.",
        "target_primitives": ["rank_uniformity"],
    }
    quality_controls = {
        "resource_contract_ids": [
            "formalization_gap_planner_resource_response_contract:lean_lsp_residual_goals"
        ],
        "required_quality_signals": ["diagnostic_signature"],
        "quality_gates": ["residual_goals_source_grounded"],
        "response_validation_signals": ["residual_goals_or_diagnostics_present"],
        "stop_conditions": ["residual interpreted or source search requested"],
    }
    route = {
        "route_id": route_id,
        "display_name": "split_conformal_rank_uniformity",
        "theorem_statement": "Split conformal rank is uniform under exchangeability.",
        "theorem_skeleton": "theorem split_conformal_rank_uniformity : True := by trivial",
        "route_class": "bridge_or_wrapper",
        "recommended_action": "rerun standalone planning on revised rank route",
        "source_refs": ["Lei-Wasserman distribution-free prediction"],
        "source_snippets": [source_snippet],
        "quality_controls": quality_controls,
        "revised_informal_knowledge_dag_nodes": informal_nodes,
        "revised_formal_realization_dag_nodes": lean_nodes,
        "revised_lean_realization_dag_nodes": lean_nodes,
        "revised_route_alignment_edges": alignment_edges,
        "informal_proof_steps": ["new rank-uniformity bridge is needed before replay"],
        "primitives": [
            {
                "primitive": "rank_uniformity",
                "coverage_status": "bridge_needed",
                "source_refs": ["Lei-Wasserman distribution-free prediction"],
                "source_snippets": [source_snippet],
                "cost": 5,
            }
        ],
        "replan_metadata": {
            "requires_replan": True,
            "applied_proposal_ids": ["proposal:rank_uniformity"],
            "applied_refinement_evidence_ids": [
                "resource_response_ledger:rank_uniformity"
            ],
            "applied_hook_kinds": ["resource_response_ledger"],
            "applied_resource_response_traces": [resource_response_trace],
            "resource_response_awaiting_request_ids": ["request:awaiting-rank-source"],
            "resource_response_rejected_request_ids": ["request:rejected-rank-proof"],
            "applied_prover_attempt_statuses": ["failed_with_residual_goals"],
            "applied_prover_diagnostic_signatures": ["missing_rank_uniformity_bridge"],
            "route_revision_reasons": ["proof-state feedback exposed rank bridge"],
            "route_revision_summaries": ["add rank-uniformity bridge before replay"],
            "residual_goals": ["rank_uniformity bridge remains open"],
            "source_refs": ["Lei-Wasserman distribution-free prediction"],
            "source_snippets": [source_snippet],
            "quality_controls": quality_controls,
            "lean_declaration_hits": [
                {"primitive": "rank_uniformity", "declaration": "Fintype.card"}
            ],
            "revised_informal_knowledge_dag_nodes": informal_nodes,
            "revised_formal_realization_dag_nodes": lean_nodes,
            "revised_lean_realization_dag_nodes": lean_nodes,
            "revised_route_alignment_edges": alignment_edges,
            "alignment_edge_primitives": ["rank_uniformity"],
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        },
    }
    seed = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_standalone_input",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:replan-audit-fixture",
        "routes": [route],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    row = {
        "route_replan_handoff_id": "formalization_gap_planner_route_replan_handoff:fixture",
        "route_revision_overlay_id": "overlay:fixture",
        "goal_plan_id": "goal:fixture",
        "route_id": "source_route:fixture",
        "display_name": "split_conformal_rank_uniformity",
        "revision_status": "ROUTE_REVISION_APPLIED",
        "stability_decision": "APPLY_ROUTE_REVISION_AND_REPLAN",
        "requires_replan": True,
        "added_primitives": ["rank_uniformity"],
        "added_delta_primitives": ["rank_uniformity"],
        "residual_goals": ["rank_uniformity bridge remains open"],
        "applied_proposal_ids": ["proposal:rank_uniformity"],
        "applied_refinement_evidence_ids": [
            "resource_response_ledger:rank_uniformity"
        ],
        "applied_hook_kinds": ["resource_response_ledger"],
        "applied_resource_response_traces": [resource_response_trace],
        "resource_response_awaiting_request_ids": ["request:awaiting-rank-source"],
        "resource_response_rejected_request_ids": ["request:rejected-rank-proof"],
        "applied_prover_attempt_statuses": ["failed_with_residual_goals"],
        "applied_prover_diagnostic_signatures": ["missing_rank_uniformity_bridge"],
        "route_revision_reasons": ["proof-state feedback exposed rank bridge"],
        "route_revision_summaries": ["add rank-uniformity bridge before replay"],
        "source_refs": ["Lei-Wasserman distribution-free prediction"],
        "source_snippets": [source_snippet],
        "quality_controls": quality_controls,
        "lean_declaration_hits": [
            {"primitive": "rank_uniformity", "declaration": "Fintype.card"}
        ],
        "revised_informal_knowledge_dag_nodes": informal_nodes,
        "revised_formal_realization_dag_nodes": lean_nodes,
        "revised_lean_realization_dag_nodes": lean_nodes,
        "revised_selected_primitives": ["rank_uniformity"],
        "revised_route_alignment_edges": alignment_edges,
        "unaligned_primitives": [],
        "standalone_route_id": route_id,
        "next_commands": [
            "formalization-gap-planner-standalone-plan --input formalization_gap_planner_route_replan_standalone_seed.json"
        ],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "ok": True,
        "errors": [],
    }
    manifest = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_route_replan_handoff",
        "n_handoff_rows": 1,
        "n_standalone_seed_routes": 1,
        "n_route_alignment_edges": 1,
        "n_unaligned_primitives": 0,
        "n_ok": 1,
        "all_ok": True,
        "rows": [row],
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    (handoff_dir / "formalization_gap_planner_route_replan_handoff_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(seed, indent=2),
        encoding="utf-8",
    )
    (
        handoff_dir
        / "formalization_gap_planner_route_replan_standalone_seed.schema.json"
    ).write_text(
        json.dumps(standalone_input_json_schema(), indent=2),
        encoding="utf-8",
    )
    (handoff_dir / "formalization_gap_planner_route_replan_handoff.jsonl").write_text(
        json.dumps(row, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (handoff_dir / "formalization_gap_planner_route_replan_handoff.md").write_text(
        "# handoff\nnot theorem proof evidence\n",
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        audit_dir,
    )

    assert payload["all_ok"]
    assert payload["n_failed"] == 0
    assert payload["n_row_schema_valid"] == payload["n_checks"]
    assert payload["n_row_schema_invalid"] == 0
    assert payload["route_replan_handoff_audit_row_schema"]["$id"] == (
        "urn:ai-statistician:schemas:formalization-gap-planner-route-replan-handoff-audit-row:1"
    )
    assert payload["roundtrip_all_ok"]
    assert payload["n_roundtrip_goal_plans"] == 1
    assert payload["n_roundtrip_route_alignment_edges"] >= 1
    assert payload["n_roundtrip_standalone_input_traces"] == 1
    assert payload["n_roundtrip_standalone_input_traces_with_replan_metadata"] == 1
    assert any(
        check["check_name"] == "standalone_seed_no_kernel_verified_claims" and check["ok"]
        for check in payload["checks"]
    )
    ok_checks = {
        check["check_name"]
        for check in payload["checks"]
        if check["ok"]
    }
    assert "handoff_alignment_edges_present" in ok_checks
    assert "handoff_no_unaligned_primitives" in ok_checks
    assert "standalone_seed_schema_id" in ok_checks
    assert "roundtrip_alignment_edges" in ok_checks
    assert "roundtrip_alignment_contract" in ok_checks
    assert "roundtrip_standalone_input_trace" in ok_checks
    assert "row_0_seed_route_alignment_metadata" in ok_checks
    assert "row_0_seed_route_revised_dags" in ok_checks
    assert "row_0_seed_route_provenance_metadata" in ok_checks
    assert "row_0_seed_route_source_snippets" in ok_checks
    assert "row_0_seed_route_quality_controls" in ok_checks
    provenance_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_provenance_metadata"
    )
    assert "resource_response_awaiting_request_ids=1" in provenance_check["observed"]
    assert "resource_response_rejected_request_ids=1" in provenance_check["observed"]
    snippet_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_source_snippets"
    )
    assert "metadata=1/1" in snippet_check["observed"]
    assert "primitive=1/1" in snippet_check["observed"]
    quality_check = next(
        check
        for check in payload["checks"]
        if check["check_name"] == "row_0_seed_route_quality_controls"
    )
    assert "row=resource_contract_ids=1" in quality_check["observed"]
    assert "metadata=resource_contract_ids=1" in quality_check["observed"]
    assert (
        audit_dir
        / "formalization_gap_planner_route_replan_handoff_audit_row.schema.json"
    ).exists()
    assert (
        audit_dir
        / "formalization_gap_planner_route_replan_roundtrip_plan"
        / "goal_conditioned_minimal_formalization_plan_manifest.json"
    ).exists()
    assert "check_name required" in validate_route_replan_handoff_audit_row(
        {"schema_version": 1},
        route_replan_handoff_audit_row_json_schema(),
    )

    metadata_rejected_seed = json.loads(json.dumps(seed))
    metadata_rejected_seed["routes"][0]["replan_metadata"][
        "resource_response_awaiting_request_ids"
    ] = []
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(metadata_rejected_seed, indent=2),
        encoding="utf-8",
    )
    metadata_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        metadata_audit_dir,
    )

    assert not metadata_rejected["all_ok"]
    metadata_failed = {
        check["check_name"]
        for check in metadata_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_provenance_metadata" in metadata_failed

    snippet_rejected_seed = json.loads(json.dumps(seed))
    snippet_rejected_seed["routes"][0]["replan_metadata"]["source_snippets"] = []
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(snippet_rejected_seed, indent=2),
        encoding="utf-8",
    )
    snippet_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        metadata_audit_dir,
    )

    assert not snippet_rejected["all_ok"]
    snippet_failed = {
        check["check_name"]
        for check in snippet_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_source_snippets" in snippet_failed

    quality_rejected_seed = json.loads(json.dumps(seed))
    quality_rejected_seed["routes"][0]["replan_metadata"]["quality_controls"][
        "stop_conditions"
    ] = []
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(quality_rejected_seed, indent=2),
        encoding="utf-8",
    )
    quality_rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        quality_audit_dir,
    )

    assert not quality_rejected["all_ok"]
    quality_failed = {
        check["check_name"]
        for check in quality_rejected["checks"]
        if not check["ok"]
    }
    assert "row_0_seed_route_quality_controls" in quality_failed

    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(seed, indent=2),
        encoding="utf-8",
    )
    seed["routes"][0]["kernel_verified"] = True
    (handoff_dir / "formalization_gap_planner_route_replan_standalone_seed.json").write_text(
        json.dumps(seed, indent=2),
        encoding="utf-8",
    )
    rejected = audit_formalization_gap_planner_route_replan_handoff(
        handoff_dir,
        reject_audit_dir,
    )

    assert not rejected["all_ok"]
    assert rejected["n_row_schema_valid"] == rejected["n_checks"]
    assert rejected["n_row_schema_invalid"] == 0
    failed = {
        check["check_name"]
        for check in rejected["checks"]
        if not check["ok"]
    }
    assert "standalone_seed_no_kernel_verified_claims" in failed

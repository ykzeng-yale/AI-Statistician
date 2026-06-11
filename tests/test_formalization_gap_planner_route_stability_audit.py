from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_route_stability_audit import (
    audit_formalization_gap_planner_route_stability,
    route_stability_audit_row_json_schema,
    validate_route_stability_audit_row,
)


def test_route_stability_audit_separates_stop_and_expand_decisions() -> None:
    root = Path("runs/test_formalization_gap_planner_route_stability_audit")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    overlay_dir = root / "overlay"
    out_dir = root / "stability"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)

    plan_rows = [
        {
            "goal_plan_id": "goal:stable",
            "route_id": "route:stable",
            "display_name": "stable route",
            "selected_primitives": ["score_definition"],
            "minimal_additional_formalization_nodes": [
                {"primitive": "score_definition", "action_class": "wrapper_needed"}
            ],
        },
        {
            "goal_plan_id": "goal:revise",
            "route_id": "route:revise",
            "display_name": "revision route",
            "selected_primitives": ["score_definition"],
            "minimal_additional_formalization_nodes": [
                {"primitive": "score_definition", "action_class": "wrapper_needed"}
            ],
        },
        {
            "goal_plan_id": "goal:formal",
            "route_id": "route:formal",
            "display_name": "formal grounding expansion route",
            "selected_primitives": ["score_definition"],
            "minimal_additional_formalization_nodes": [
                {"primitive": "score_definition", "action_class": "wrapper_needed"}
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
    evidence_rows = [
        {
            "goal_plan_id": "goal:stable",
            "route_id": "route:stable",
            "display_name": "stable route",
            "hook_kind": "literature_discovery",
            "response_present": True,
            "response_contract_ok": True,
            "acceptance_status": "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE",
            "source_refs": ["paper:stable#lemma1"],
            "route_revision_recommended": False,
        },
        {
            "goal_plan_id": "goal:stable",
            "route_id": "route:stable",
            "display_name": "stable route",
            "hook_kind": "lean_library_grounding",
            "response_present": True,
            "response_contract_ok": True,
            "acceptance_status": "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE",
            "lean_declaration_hits": [
                {"primitive": "score_definition", "declaration": "Demo.score_definition"}
            ],
            "route_revision_recommended": False,
        },
        {
            "goal_plan_id": "goal:stable",
            "route_id": "route:stable",
            "display_name": "stable route",
            "hook_kind": "proof_state_feedback",
            "response_present": True,
            "response_contract_ok": True,
            "acceptance_status": "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE",
            "prover_attempt_status": "local_lean_scaffold_accepted",
            "target_prover_family": "lean4",
            "prover_diagnostics": ["accepted scaffold"],
            "residual_goals": [],
            "route_revision_recommended": False,
        },
        {
            "goal_plan_id": "goal:revise",
            "route_id": "route:revise",
            "display_name": "revision route",
            "hook_kind": "literature_discovery",
            "response_present": True,
            "response_contract_ok": True,
            "acceptance_status": "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE",
            "source_refs": ["paper:revise#lemma2"],
            "route_revision_recommended": True,
            "route_revision_reasons": ["source introduced conditional_mean_residual_zero"],
        },
        {
            "goal_plan_id": "goal:formal",
            "route_id": "route:formal",
            "display_name": "formal grounding expansion route",
            "hook_kind": "formal_library_grounding",
            "response_present": True,
            "response_contract_ok": True,
            "acceptance_status": "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE",
            "formal_declaration_hits": [],
            "route_revision_recommended": False,
        },
    ]
    (evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json").write_text(
        json.dumps({"rows": evidence_rows}, indent=2),
        encoding="utf-8",
    )
    overlay_rows = [
        {
            "goal_plan_id": "goal:stable",
            "route_id": "route:stable",
            "display_name": "stable route",
            "revision_status": "NO_ROUTE_REVISION_PROPOSAL",
            "original_selected_primitives": ["score_definition"],
            "revised_selected_primitives": ["score_definition"],
            "added_primitives": [],
            "removed_primitives": [],
            "original_delta_primitives": ["score_definition"],
            "revised_delta_primitives": ["score_definition"],
            "added_delta_primitives": [],
        },
        {
            "goal_plan_id": "goal:revise",
            "route_id": "route:revise",
            "display_name": "revision route",
            "revision_status": "ROUTE_REVISION_APPLIED",
            "original_selected_primitives": ["score_definition"],
            "revised_selected_primitives": [
                "score_definition",
                "conditional_mean_residual_zero",
            ],
            "added_primitives": ["conditional_mean_residual_zero"],
            "removed_primitives": [],
            "original_delta_primitives": ["score_definition"],
            "revised_delta_primitives": [
                "score_definition",
                "conditional_mean_residual_zero",
            ],
            "added_delta_primitives": ["conditional_mean_residual_zero"],
            "route_revision_reasons": ["literature evidence added a missing identity"],
        },
        {
            "goal_plan_id": "goal:formal",
            "route_id": "route:formal",
            "display_name": "formal grounding expansion route",
            "revision_status": "NO_ROUTE_REVISION_PROPOSAL",
            "original_selected_primitives": ["score_definition"],
            "revised_selected_primitives": ["score_definition"],
            "added_primitives": [],
            "removed_primitives": [],
            "original_delta_primitives": ["score_definition"],
            "revised_delta_primitives": ["score_definition"],
            "added_delta_primitives": [],
        },
    ]
    (overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json").write_text(
        json.dumps({"rows": overlay_rows}, indent=2),
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_route_stability(
        plan_dir,
        evidence_dir,
        overlay_dir,
        out_dir,
    )

    assert payload["all_ok"]
    assert payload["n_stability_rows"] == 3
    assert payload["n_row_schema_valid"] == payload["n_stability_rows"]
    assert payload["n_row_schema_invalid"] == 0
    assert (
        payload["route_stability_audit_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-route-stability-audit-row:1"
    )
    assert payload["n_stable"] == 1
    assert payload["n_apply_route_revision"] == 1
    assert payload["n_expand_formal_grounding"] == 1
    assert payload["n_expand_lean_grounding"] == 0
    assert payload["by_prover_attempt_class"] == {
        "target_prover_scaffold_accepted": 1
    }
    assert payload["target_prover_families"] == ("lean4",)
    assert payload["n_new_primitives_since_plan"] == 1
    by_route = {row["route_id"]: row for row in payload["rows"]}
    assert (
        by_route["route:stable"]["stability_decision"]
        == "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND"
    )
    assert by_route["route:stable"]["stable_under_current_evidence_bound"]
    assert by_route["route:stable"]["prover_attempt_statuses"] == (
        "local_lean_scaffold_accepted",
    )
    assert by_route["route:stable"]["prover_attempt_classes"] == (
        "target_prover_scaffold_accepted",
    )
    assert by_route["route:stable"]["target_prover_families"] == ("lean4",)
    assert (
        by_route["route:revise"]["stability_decision"]
        == "APPLY_ROUTE_REVISION_AND_REPLAN"
    )
    assert (
        by_route["route:formal"]["stability_decision"]
        == "EXPAND_FORMAL_LIBRARY_GROUNDING"
    )
    assert by_route["route:formal"]["needs_more_formal_grounding"]
    assert not by_route["route:formal"]["needs_more_lean_grounding"]
    assert by_route["route:formal"]["formal_declaration_hits"] == ()
    assert "conditional_mean_residual_zero" in by_route["route:revise"]["new_primitives_since_plan"]
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    broken_row = dict(by_route["route:stable"])
    broken_row.pop("stability_decision")
    assert "stability_decision required" in validate_route_stability_audit_row(
        broken_row,
        route_stability_audit_row_json_schema(),
    )
    assert (
        out_dir / "formalization_gap_planner_route_stability_audit_manifest.json"
    ).exists()
    assert (
        out_dir / "formalization_gap_planner_route_stability_audit_row.schema.json"
    ).exists()


def test_route_stability_audit_uses_resource_response_overlay_status() -> None:
    root = Path("runs/test_formalization_gap_planner_route_stability_resource_status")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    overlay_dir = root / "overlay"
    out_dir = root / "stability"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    route_ids = ("route:awaiting", "route:rejected", "route:residual")
    plan_rows = [
        {
            "goal_plan_id": f"goal:{route_id.split(':')[1]}",
            "route_id": route_id,
            "display_name": route_id,
            "selected_primitives": ["score_definition"],
            "minimal_additional_formalization_nodes": [
                {"primitive": "score_definition", "action_class": "wrapper_needed"}
            ],
        }
        for route_id in route_ids
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
    (evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json").write_text(
        json.dumps({"rows": []}, indent=2),
        encoding="utf-8",
    )
    overlay_rows = [
        {
            "goal_plan_id": "goal:awaiting",
            "route_id": "route:awaiting",
            "display_name": "route:awaiting",
            "revision_status": "NO_ROUTE_REVISION_PROPOSAL",
            "original_selected_primitives": ["score_definition"],
            "revised_selected_primitives": ["score_definition"],
            "added_primitives": [],
            "removed_primitives": [],
            "original_delta_primitives": ["score_definition"],
            "revised_delta_primitives": ["score_definition"],
            "added_delta_primitives": [],
            "resource_response_summary": {
                "queued": 1,
                "responded": 0,
                "contract_ok": 0,
                "awaiting": 1,
                "rejected": 0,
                "accepted": 0,
                "route_revision_recommended": 0,
            },
            "resource_response_awaiting_request_ids": ["request:awaiting"],
            "resource_response_rejected_request_ids": [],
        },
        {
            "goal_plan_id": "goal:rejected",
            "route_id": "route:rejected",
            "display_name": "route:rejected",
            "revision_status": "NO_ROUTE_REVISION_PROPOSAL",
            "original_selected_primitives": ["score_definition"],
            "revised_selected_primitives": ["score_definition"],
            "added_primitives": [],
            "removed_primitives": [],
            "original_delta_primitives": ["score_definition"],
            "revised_delta_primitives": ["score_definition"],
            "added_delta_primitives": [],
            "resource_response_summary": {
                "queued": 1,
                "responded": 1,
                "contract_ok": 0,
                "awaiting": 0,
                "rejected": 1,
                "accepted": 0,
                "route_revision_recommended": 0,
            },
            "resource_response_awaiting_request_ids": [],
            "resource_response_rejected_request_ids": ["request:rejected"],
        },
        {
            "goal_plan_id": "goal:residual",
            "route_id": "route:residual",
            "display_name": "route:residual",
            "revision_status": "NO_ROUTE_REVISION_PROPOSAL",
            "original_selected_primitives": ["score_definition"],
            "revised_selected_primitives": ["score_definition"],
            "added_primitives": [],
            "removed_primitives": [],
            "original_delta_primitives": ["score_definition"],
            "revised_delta_primitives": ["score_definition"],
            "added_delta_primitives": [],
            "resource_response_summary": {
                "queued": 1,
                "responded": 1,
                "contract_ok": 1,
                "awaiting": 0,
                "rejected": 0,
                "accepted": 1,
                "route_revision_recommended": 0,
            },
            "resource_response_awaiting_request_ids": [],
            "resource_response_rejected_request_ids": [],
            "applied_prover_attempt_classes": ["target_prover_failed"],
            "target_prover_families": ["lean4"],
            "source_refs": ["paper:accepted#lemma"],
            "lean_declaration_hits": [
                {"primitive": "score_definition", "declaration": "Fixture.score"}
            ],
        },
    ]
    (overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json").write_text(
        json.dumps({"rows": overlay_rows}, indent=2),
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_route_stability(
        plan_dir,
        evidence_dir,
        overlay_dir,
        out_dir,
    )

    assert payload["all_ok"]
    assert payload["n_stability_rows"] == 3
    assert payload["n_awaiting_responses"] == 1
    assert payload["n_repair_response_contract"] == 1
    assert payload["n_expand_proof_state"] == 1
    assert payload["by_prover_attempt_class"] == {"target_prover_failed": 1}
    assert payload["target_prover_families"] == ("lean4",)
    by_route = {row["route_id"]: row for row in payload["rows"]}
    assert by_route["route:awaiting"]["stability_decision"] == "AWAITING_REFINEMENT_RESPONSES"
    assert by_route["route:awaiting"]["awaiting_hook_kinds"] == (
        "resource_response_ledger",
    )
    assert by_route["route:awaiting"]["resource_response_awaiting_request_ids"] == (
        "request:awaiting",
    )
    assert by_route["route:awaiting"]["resource_response_rejected_request_ids"] == ()
    assert (
        by_route["route:awaiting"]["response_summary_by_hook"][
            "resource_response_ledger"
        ]["awaiting"]
        == 1
    )
    assert (
        by_route["route:rejected"]["stability_decision"]
        == "REPAIR_REFINEMENT_RESPONSE_CONTRACT"
    )
    assert by_route["route:rejected"]["rejected_hook_kinds"] == (
        "resource_response_ledger",
    )
    assert by_route["route:rejected"]["resource_response_awaiting_request_ids"] == ()
    assert by_route["route:rejected"]["resource_response_rejected_request_ids"] == (
        "request:rejected",
    )
    assert (
        by_route["route:residual"]["stability_decision"]
        == "EXPAND_PROOF_STATE_FEEDBACK"
    )
    assert by_route["route:residual"]["responded_hook_kinds"] == (
        "resource_response_ledger",
    )
    assert by_route["route:residual"]["residual_goals"] == ()
    assert by_route["route:residual"]["prover_attempt_statuses"] == ()
    assert by_route["route:residual"]["prover_attempt_classes"] == (
        "target_prover_failed",
    )
    assert by_route["route:residual"]["target_prover_families"] == ("lean4",)
    assert by_route["route:residual"]["source_refs"] == ("paper:accepted#lemma",)
    assert by_route["route:residual"]["lean_declaration_hits"] == (
        {"primitive": "score_definition", "declaration": "Fixture.score"},
    )
    assert by_route["route:residual"]["formal_declaration_hits"] == (
        {"primitive": "score_definition", "declaration": "Fixture.score"},
    )


def test_route_stability_audit_keeps_rocq_declaration_hits_portable() -> None:
    root = Path("runs/test_formalization_gap_planner_route_stability_rocq_hits")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    overlay_dir = root / "overlay"
    out_dir = root / "stability"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    plan_row = {
        "goal_plan_id": "goal:rocq",
        "route_id": "route:rocq",
        "display_name": "rocq route",
        "target_prover_family": "rocq",
        "selected_primitives": ["rank_bridge"],
        "minimal_additional_formalization_nodes": [
            {"primitive": "rank_bridge", "action_class": "bridge_needed"}
        ],
    }
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": "urn:ai-statistician:schemas:library-aware-formalization-gap-plan:1",
                "rows": [plan_row],
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
                        "response_present": True,
                        "response_contract_ok": True,
                        "acceptance_status": "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE",
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
        overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json"
    ).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq",
                        "route_id": "route:rocq",
                        "display_name": "rocq route",
                        "revision_status": "NO_ROUTE_REVISION_PROPOSAL",
                        "target_prover_families": ["rocq"],
                        "original_selected_primitives": ["rank_bridge"],
                        "revised_selected_primitives": ["rank_bridge"],
                        "added_primitives": [],
                        "removed_primitives": [],
                        "original_delta_primitives": ["rank_bridge"],
                        "revised_delta_primitives": ["rank_bridge"],
                        "added_delta_primitives": [],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_route_stability(
        plan_dir,
        evidence_dir,
        overlay_dir,
        out_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["target_prover_families"] == ("rocq",)
    assert row["stability_decision"] == "ROUTE_STABILIZED_FOR_CURRENT_EVIDENCE_BOUND"
    assert row["formal_declaration_hits"] == (
        {
            "primitive": "rank_bridge",
            "declaration": "Rocq.Conformal.rank_bridge",
            "target_prover_family": "rocq",
            "source_field": "formal_declaration_hits",
        },
    )
    assert row["lean_declaration_hits"] == ()
    bad_legacy_alias_row = dict(row)
    bad_legacy_alias_row["lean_declaration_hits"] = [
        {
            "primitive": "rank_bridge",
            "declaration": "Rocq.Conformal.rank_bridge",
            "target_prover_family": "rocq",
        }
    ]
    assert (
        "lean_declaration_hits is a Lean-only legacy alias; non-Lean route "
        "stability audit rows must use formal_declaration_hits only"
        in validate_route_stability_audit_row(
            bad_legacy_alias_row,
            route_stability_audit_row_json_schema(),
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
        in validate_route_stability_audit_row(
            bad_source_type_row,
            route_stability_audit_row_json_schema(),
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
    assert validate_route_stability_audit_row(
        coq_alias_row,
        route_stability_audit_row_json_schema(),
    ) == []


def test_route_stability_audit_rejects_rocq_legacy_lean_alias_input() -> None:
    root = Path("runs/test_formalization_gap_planner_route_stability_rocq_lean_alias")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    overlay_dir = root / "overlay"
    out_dir = root / "stability"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
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
                        "minimal_additional_formalization_nodes": [
                            {
                                "primitive": "rank_bridge",
                                "action_class": "bridge_needed",
                            }
                        ],
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
                        "response_present": True,
                        "response_contract_ok": True,
                        "acceptance_status": "REFINEMENT_EVIDENCE_RECORDED_NOT_PROOF_EVIDENCE",
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
        overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json"
    ).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq_alias",
                        "route_id": "route:rocq_alias",
                        "display_name": "rocq alias route",
                        "revision_status": "NO_ROUTE_REVISION_PROPOSAL",
                        "target_prover_families": ["rocq"],
                        "original_selected_primitives": ["rank_bridge"],
                        "revised_selected_primitives": ["rank_bridge"],
                        "added_primitives": [],
                        "removed_primitives": [],
                        "original_delta_primitives": ["rank_bridge"],
                        "revised_delta_primitives": ["rank_bridge"],
                        "added_delta_primitives": [],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = audit_formalization_gap_planner_route_stability(
        plan_dir,
        evidence_dir,
        overlay_dir,
        out_dir,
    )

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["stability_decision"] == "BLOCKED_ROUTE_STABILITY_INPUT"
    assert row["formal_declaration_hits"] == ()
    assert row["lean_declaration_hits"] == ()
    assert any(
        "uses lean_declaration_hits for non-Lean route stability target" in error
        for error in row["errors"]
    )

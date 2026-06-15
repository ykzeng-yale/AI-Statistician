from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_contract import (
    LEGACY_FORMAL_REALIZATION_FIELD_ALIASES,
)
from ai_statistician.formalization_gap_planner_refinement_adapters import (
    export_formalization_gap_planner_refinement_adapter_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)
from ai_statistician.formalization_gap_planner_route_revision_overlay import (
    export_formalization_gap_planner_route_revision_overlay,
    route_revision_overlay_row_json_schema,
    validate_route_revision_overlay_row,
)


def test_route_revision_overlay_applies_adapter_evidence_to_plan() -> None:
    root = Path("runs/test_formalization_gap_planner_route_revision_overlay")
    queue_dir = root / "queue"
    adapter_dir = root / "adapter"
    evidence_dir = root / "evidence"
    plan_dir = root / "plan"
    overlay_dir = root / "overlay"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    display_name = "causal_ate_aipw:aipw_double_robustness:skeleton"
    target_primitives = [
        "aipw_score_definition",
        "conditional_mean_residual_zero",
        "integrability_of_score_terms",
        "nuisance_correctness_cases",
    ]
    queue_rows = []
    for hook_kind in (
        "literature_discovery",
        "lean_library_grounding",
        "proof_state_feedback",
        "route_revision",
    ):
        queue_rows.append(
            {
                "refinement_item_id": f"refinement:{hook_kind}",
                "goal_plan_id": "goal:test",
                "route_id": "route:test",
                "display_name": display_name,
                "hook_kind": hook_kind,
                "refinement_stage": f"{hook_kind}:stage",
                "owner_agent": f"{hook_kind}:agent",
                "target_primitives": target_primitives,
                "queries": [f"{display_name} {hook_kind}"],
                "evaluation_signal": "delta_missing_primitives"
                if hook_kind == "route_revision"
                else "no_evaluation_signal",
                "prover_feedback_status": "failed_with_residual_goals"
                if hook_kind == "proof_state_feedback"
                else "no_calibration_signal",
                "prover_feedback_error_category": "unsolved_goal"
                if hook_kind == "proof_state_feedback"
                else "",
                "prover_feedback_first_error": "unsolved goal: conditional_mean_residual_zero"
                if hook_kind == "proof_state_feedback"
                else "",
            }
        )
    (queue_dir / "formalization_gap_planner_refinement_queue_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_refinement_queue",
                "rows": queue_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "rows": [
                    {
                        "goal_plan_id": "goal:test",
                        "route_id": "route:test",
                        "display_name": display_name,
                        "selected_primitives": ["aipw_score_definition"],
                        "minimal_additional_formalization_nodes": [],
                        "informal_knowledge_dag": {
                            "nodes": [
                                {
                                    "node_id": "informal:score",
                                    "kind": "required_primitive",
                                    "label": "aipw_score_definition",
                                }
                            ]
                        },
                        "lean_realization_dag": {
                            "nodes": [
                                {
                                    "node_id": "lean:score",
                                    "kind": "existing_reuse",
                                    "label": "aipw_score_definition",
                                }
                            ]
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    adapter_payload = export_formalization_gap_planner_refinement_adapter_responses(
        queue_dir,
        adapter_dir,
    )
    assert adapter_payload["all_ok"]
    assert adapter_payload["n_response_schema_valid"] == adapter_payload["n_responses"] == 4
    assert adapter_payload["n_response_schema_invalid"] == 0
    assert (
        adapter_payload["refinement_tool_response_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1"
    )
    assert (
        adapter_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()
    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=(
            adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        ),
    )
    assert evidence_payload["all_ok"]
    evidence_manifest_path = (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    )
    evidence_manifest = json.loads(evidence_manifest_path.read_text(encoding="utf-8"))
    for proposal in evidence_manifest["route_revision_proposals"]:
        if proposal["hook_kind"] == "proof_state_feedback":
            proposal["prover_attempt_status"] = "formal_gap_scaffold_blocked"
            proposal["prover_attempt_class"] = "formal_gap_scaffold_blocked"
            proposal["target_prover_family"] = "lean4"
            proposal["prover_diagnostic_signature"] = "prover_diagnostic_signature:test"
            break
    evidence_manifest_path.write_text(
        json.dumps(evidence_manifest, indent=2),
        encoding="utf-8",
    )

    overlay_payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        overlay_dir,
    )
    assert overlay_payload["all_ok"]
    assert overlay_payload["n_routes_with_revision"] == 1
    assert overlay_payload["n_orphan_route_revision_proposals"] == 0
    assert overlay_payload["n_rows_with_alignment_contract"] == 1
    assert overlay_payload["n_unaligned_primitives"] == 0
    assert overlay_payload["n_row_schema_valid"] == overlay_payload["n_overlay_rows"]
    assert overlay_payload["n_row_schema_invalid"] == 0
    assert (
        overlay_payload["route_revision_overlay_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-route-revision-overlay-row:1"
    )
    assert (
        overlay_payload["legacy_formal_realization_field_aliases"]
        == LEGACY_FORMAL_REALIZATION_FIELD_ALIASES
    )
    assert overlay_payload["n_formal_realization_dag_nodes"] == overlay_payload[
        "n_lean_realization_dag_nodes"
    ]
    overlay_row = overlay_payload["rows"][0]
    assert overlay_row["revision_status"] == "ROUTE_REVISION_APPLIED"
    assert "conditional_mean_residual_zero" in overlay_row["added_primitives"]
    assert "nuisance_correctness_cases" in overlay_row["revised_delta_primitives"]
    assert overlay_payload["by_prover_attempt_status"] == {
        "formal_gap_scaffold_blocked": 1
    }
    assert overlay_payload["by_prover_attempt_class"] == {
        "formal_gap_scaffold_blocked": 1
    }
    assert overlay_payload["n_routes_with_prover_attempt_status"] == 1
    assert overlay_payload["n_routes_with_prover_attempt_class"] == 1
    assert overlay_payload["target_prover_families"] == ("lean4",)
    assert overlay_row["applied_prover_attempt_statuses"] == (
        "formal_gap_scaffold_blocked",
    )
    assert overlay_row["applied_prover_attempt_classes"] == (
        "formal_gap_scaffold_blocked",
    )
    assert overlay_row["target_prover_families"] == ("lean4",)
    assert overlay_row["applied_prover_diagnostic_signatures"] == (
        "prover_diagnostic_signature:test",
    )
    assert overlay_row["applied_llm_route_planner_hook_traces"]
    derived_context_traces = [
        trace
        for trace in overlay_row["applied_llm_route_planner_hook_traces"]
        if trace.get("trace_source") == "refinement_evidence"
        and trace.get("residual_goal_context")
    ]
    assert derived_context_traces
    derived_context = derived_context_traces[0]["residual_goal_context"]
    assert derived_context["source_kind"] == "proof_state_feedback"
    assert derived_context["prover_attempt_status"] == (
        "failed_with_residual_goals"
    )
    assert derived_context["proof_evidence_status"] == (
        "FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_NOT_PROOF_EVIDENCE"
    )
    assert "conditional_mean_residual_zero" in " ".join(
        derived_context["residual_goals"]
    )
    assert len(overlay_row["revised_lean_realization_dag_nodes"]) >= 4
    assert overlay_row["revised_formal_realization_dag_nodes"] == overlay_row[
        "revised_lean_realization_dag_nodes"
    ]
    assert "revised_formal_realization_dag_nodes" in overlay_payload[
        "route_revision_overlay_row_schema"
    ]["properties"]
    overlay_schema = route_revision_overlay_row_json_schema()
    assert "revised_formal_realization_dag_nodes" in overlay_schema["required"]
    assert "revised_lean_realization_dag_nodes" not in overlay_schema["required"]
    legacy_free_row = dict(overlay_row)
    legacy_free_row.pop("revised_lean_realization_dag_nodes", None)
    assert validate_route_revision_overlay_row(legacy_free_row, overlay_schema) == ()
    missing_generic_row = dict(overlay_row)
    missing_generic_row.pop("revised_formal_realization_dag_nodes", None)
    assert "revised_formal_realization_dag_nodes required" in validate_route_revision_overlay_row(
        missing_generic_row,
        overlay_schema,
    )
    assert {
        edge["primitive"] for edge in overlay_row["revised_route_alignment_edges"]
    } == set(overlay_row["revised_selected_primitives"])
    assert {
        edge["edge_type"] for edge in overlay_row["revised_route_alignment_edges"]
    } == {"revised_informal_to_formal_alignment"}
    assert not overlay_row["unaligned_primitives"]
    bad_row = dict(overlay_row)
    bad_row.pop("revised_route_alignment_edges")
    assert "revised_route_alignment_edges required" in validate_route_revision_overlay_row(
        bad_row,
        route_revision_overlay_row_json_schema(),
    )
    assert (
        overlay_dir / "formalization_gap_planner_route_revision_overlay_row.schema.json"
    ).exists()
    assert "not theorem proof evidence" in overlay_payload["proof_evidence_boundary"]


def test_route_revision_overlay_rejects_unaligned_revised_primitive() -> None:
    root = Path("runs/test_formalization_gap_planner_route_revision_overlay_alignment_rejects")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "rows": [
                    {
                        "goal_plan_id": "goal:alignment",
                        "route_id": "route:alignment",
                        "display_name": "alignment overlay target",
                        "selected_primitives": ["demo_existing"],
                        "minimal_additional_formalization_nodes": [],
                        "informal_knowledge_dag": {
                            "nodes": [
                                {
                                    "node_id": "informal:demo_existing",
                                    "kind": "required_primitive",
                                    "label": "demo_existing",
                                }
                            ]
                        },
                        "lean_realization_dag": {
                            "nodes": [
                                {
                                    "node_id": "lean:demo_existing",
                                    "kind": "existing_reuse",
                                    "label": "demo_existing",
                                }
                            ]
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_refinement_evidence",
                "route_revision_proposals": [
                    {
                        "proposal_id": "proposal:alignment",
                        "refinement_evidence_id": "evidence:alignment",
                        "goal_plan_id": "goal:alignment",
                        "route_id": "route:alignment",
                        "display_name": "alignment overlay target",
                        "hook_kind": "route_revision",
                        "revised_selected_primitives": [
                            "demo_existing",
                            "demo_missing_alignment",
                        ],
                        "revised_delta_primitives": ["demo_missing_alignment"],
                        "revised_informal_knowledge_dag_nodes": [
                            {
                                "node_id": "informal:demo_missing_alignment",
                                "kind": "required_primitive",
                                "label": "demo_missing_alignment",
                            }
                        ],
                        "revised_lean_realization_dag_nodes": [],
                        "route_revision_reasons": ["missing Lean realization candidate"],
                        "route_revision_summary": "alignment should fail until Lean realization is supplied",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_row_schema_valid"] == payload["n_overlay_rows"]
    assert payload["n_row_schema_invalid"] == 0
    assert payload["n_rows_with_alignment_contract"] == 0
    assert payload["n_unaligned_primitives"] == 1
    row = payload["rows"][0]
    assert row["unaligned_primitives"] == ("demo_missing_alignment",)
    assert "unaligned revised primitives" in row["errors"][0]


def test_route_revision_overlay_accepts_generic_formal_realization_nodes() -> None:
    root = Path("runs/test_formalization_gap_planner_route_revision_overlay_generic")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    overlay_dir = root / "overlay"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "target_prover_family": "rocq",
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq",
                        "route_id": "route:rocq",
                        "display_name": "rocq generic route",
                        "selected_primitives": ["existing_rank"],
                        "minimal_additional_formalization_nodes": [],
                        "informal_knowledge_dag": {
                            "nodes": [
                                {
                                    "node_id": "informal:existing_rank",
                                    "kind": "assumption",
                                    "label": "existing_rank",
                                }
                            ]
                        },
                        "lean_realization_dag": {
                            "nodes": [
                                {
                                    "node_id": "formal:existing_rank",
                                    "kind": "existing_reuse",
                                    "label": "existing_rank",
                                }
                            ]
                        },
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
                "component_name": "formalization_gap_planner_refinement_evidence",
                "route_revision_proposals": [
                    {
                        "proposal_id": "proposal:rocq_generic_bridge",
                        "refinement_evidence_id": "evidence:rocq_generic_bridge",
                        "goal_plan_id": "goal:rocq",
                        "route_id": "route:rocq",
                        "display_name": "rocq generic route",
                        "hook_kind": "route_revision",
                        "route_revision_summary": "add generic formal bridge",
                        "route_revision_reasons": [
                            "generic formal realization node covers bridge"
                        ],
                        "revised_selected_primitives": [
                            "existing_rank",
                            "generic_rank_bridge",
                        ],
                        "revised_delta_primitives": ["generic_rank_bridge"],
                        "revised_informal_knowledge_dag_nodes": [
                            {
                                "node_id": "informal:generic_rank_bridge",
                                "kind": "lemma",
                                "label": "generic_rank_bridge",
                            }
                        ],
                        "revised_formal_realization_dag_nodes": [
                            {
                                "node_id": "formal:generic_rank_bridge",
                                "kind": "bridge",
                                "label": "generic_rank_bridge",
                                "target_prover_family": "rocq",
                            }
                        ],
                        "formal_declaration_hits": [
                            {
                                "primitive": "generic_rank_bridge",
                                "declaration": "Rocq.Conformal.generic_rank_bridge",
                                "target_prover_family": "rocq",
                                "source_field": "formal_declaration_hits",
                            }
                        ],
                        "source_refs": ["fixture:rocq-route"],
                        "proof_evidence_status": (
                            "FORMALIZATION_GAP_PLANNER_REFINEMENT_EVIDENCE_NOT_PROOF_EVIDENCE"
                        ),
                        "proof_evidence_boundary": "not theorem proof evidence",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        overlay_dir,
    )

    assert payload["all_ok"]
    assert payload["n_formal_realization_dag_nodes"] >= 2
    assert payload["n_lean_realization_dag_nodes"] == 0
    row = payload["rows"][0]
    assert "generic_rank_bridge" in row["revised_selected_primitives"]
    assert row["revised_formal_realization_dag_nodes"]
    assert row["revised_lean_realization_dag_nodes"] == ()
    assert row["formal_declaration_hits"] == (
        {
            "primitive": "generic_rank_bridge",
            "declaration": "Rocq.Conformal.generic_rank_bridge",
            "target_prover_family": "rocq",
            "source_field": "formal_declaration_hits",
        },
    )
    assert row["lean_declaration_hits"] == ()
    assert {
        edge["primitive"] for edge in row["revised_route_alignment_edges"]
    } == {"existing_rank", "generic_rank_bridge"}
    bad_legacy_alias_row = dict(row)
    bad_legacy_alias_row["lean_declaration_hits"] = [
        {
            "primitive": "generic_rank_bridge",
            "declaration": "Rocq.Conformal.generic_rank_bridge",
            "target_prover_family": "rocq",
        }
    ]
    assert (
        "lean_declaration_hits is a Lean-only legacy alias; non-Lean route revision "
        "overlay rows must use formal_declaration_hits only"
        in validate_route_revision_overlay_row(
            bad_legacy_alias_row,
            route_revision_overlay_row_json_schema(),
        )
    )
    bad_mismatch_row = dict(row)
    bad_mismatch_row["formal_declaration_hits"] = [
        {
            "primitive": "generic_rank_bridge",
            "declaration": "Mathlib.Conformal.genericRankBridge",
            "target_prover_family": "lean4",
        }
    ]
    assert (
        "formal_declaration_hits[0].target_prover_family must match row "
        "target_prover_families"
        in validate_route_revision_overlay_row(
            bad_mismatch_row,
            route_revision_overlay_row_json_schema(),
        )
    )
    bad_source_type_row = dict(row)
    bad_source_type_row["formal_declaration_hits"] = [
        {
            "primitive": "generic_rank_bridge",
            "declaration": "Mathlib.Conformal.genericRankBridge",
            "source_type": "lean_library",
        }
    ]
    assert (
        "formal_declaration_hits[0].source_type implies lean4 "
        "but row target_prover_families are rocq"
        in validate_route_revision_overlay_row(
            bad_source_type_row,
            route_revision_overlay_row_json_schema(),
        )
    )
    coq_alias_row = dict(row)
    coq_alias_row["formal_declaration_hits"] = [
        {
            "primitive": "generic_rank_bridge",
            "declaration": "Rocq.Conformal.generic_rank_bridge",
            "target_prover_family": "coq",
        }
    ]
    assert validate_route_revision_overlay_row(
        coq_alias_row,
        route_revision_overlay_row_json_schema(),
    ) == ()


def test_route_revision_overlay_keeps_rocq_resource_hits_portable() -> None:
    root = Path("runs/test_formalization_gap_planner_route_revision_overlay_rocq_ledger")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    ledger_dir = root / "ledger"
    overlay_dir = root / "overlay"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "target_prover_family": "rocq",
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq_ledger",
                        "route_id": "route:rocq_ledger",
                        "display_name": "rocq ledger route",
                        "selected_primitives": ["exchangeability_bridge"],
                        "minimal_additional_formalization_nodes": [],
                        "informal_knowledge_dag": {
                            "nodes": [
                                {
                                    "node_id": "informal:exchangeability_bridge",
                                    "label": "exchangeability_bridge",
                                }
                            ]
                        },
                        "lean_realization_dag": {
                            "nodes": [
                                {
                                    "node_id": "formal:exchangeability_bridge",
                                    "label": "exchangeability_bridge",
                                }
                            ]
                        },
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
                "component_name": "formalization_gap_planner_refinement_evidence",
                "route_revision_proposals": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        ledger_dir / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_response_ledger",
                "rows": [
                    {
                        "schema_version": 11,
                        "resource_response_ledger_id": "ledger:rocq_exchangeability",
                        "resource_request_id": "request:rocq_exchangeability",
                        "goal_plan_id": "goal:rocq_ledger",
                        "route_id": "route:rocq_ledger",
                        "display_name": "rocq ledger route",
                        "primitive": "exchangeability_bridge",
                        "target_primitives": ["exchangeability_bridge"],
                        "resource_id": "rocq_lsp_mcp",
                        "target_prover_family": "rocq",
                        "response_present": True,
                        "response_contract_ok": True,
                        "response_payload": {},
                        "response_summary": "Rocq search found a reusable bridge",
                        "formal_declaration_hits": [
                            {
                                "primitive": "exchangeability_bridge",
                                "declaration": "Rocq.Probability.exchangeability_bridge",
                                "target_prover_family": "rocq",
                                "source_field": "formal_declaration_hits",
                            }
                        ],
                        "matched_response_contract_fields": [
                            "formal_declaration_hits"
                        ],
                        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
                        "route_revision_recommended": True,
                        "ok": True,
                        "proof_evidence_status": (
                            "FORMALIZATION_GAP_PLANNER_RESOURCE_RESPONSE_LEDGER_NOT_PROOF_EVIDENCE"
                        ),
                        "proof_evidence_boundary": "not theorem proof evidence",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        overlay_dir,
        formalization_gap_planner_resource_response_ledger_dir=ledger_dir,
    )

    assert payload["all_ok"]
    row = payload["rows"][0]
    assert row["target_prover_families"] == ("rocq",)
    assert row["formal_declaration_hits"] == (
        {
            "primitive": "exchangeability_bridge",
            "declaration": "Rocq.Probability.exchangeability_bridge",
            "target_prover_family": "rocq",
            "source_field": "formal_declaration_hits",
        },
    )
    assert row["lean_declaration_hits"] == ()
    assert row["revised_lean_realization_dag_nodes"] == ()
    assert any(
        node.get("kind") == "resource_response_formal_declaration_hit"
        for node in row["revised_formal_realization_dag_nodes"]
    )
    assert not any(
        str(node.get("node_id", "")).startswith("resource_response_lean:")
        for node in row["revised_formal_realization_dag_nodes"]
    )
    trace = row["applied_resource_response_traces"][0]
    assert trace["formal_declaration_hits"] == row["formal_declaration_hits"]
    assert trace["lean_declaration_hits"] == ()


def test_route_revision_overlay_ignores_rejected_refinement_evidence_proposals() -> None:
    root = Path("runs/test_formalization_gap_planner_route_revision_overlay_rejected_evidence")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    overlay_dir = root / "overlay"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    display_name = "rejected evidence overlay target"
    (
        plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "target_prover_family": "lean4",
                "rows": [
                    {
                        "goal_plan_id": "goal:rejected-evidence",
                        "route_id": "route:rejected-evidence",
                        "display_name": display_name,
                        "selected_primitives": ["existing_rank"],
                        "minimal_additional_formalization_nodes": [],
                        "informal_knowledge_dag": {
                            "nodes": [
                                {
                                    "node_id": "informal:existing_rank",
                                    "kind": "assumption",
                                    "label": "existing_rank",
                                }
                            ]
                        },
                        "lean_realization_dag": {
                            "nodes": [
                                {
                                    "node_id": "formal:existing_rank",
                                    "kind": "existing_reuse",
                                    "label": "existing_rank",
                                }
                            ]
                        },
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
                "component_name": "formalization_gap_planner_refinement_evidence",
                "rows": [
                    {
                        "refinement_evidence_id": "evidence:rejected_bridge",
                        "refinement_item_id": "refinement:rejected_bridge",
                        "goal_plan_id": "goal:rejected-evidence",
                        "route_id": "route:rejected-evidence",
                        "display_name": display_name,
                        "hook_kind": "route_revision",
                        "response_present": True,
                        "response_contract_ok": False,
                        "acceptance_status": "REJECTED_REFINEMENT_EVIDENCE_CONTRACT",
                        "ok": False,
                    }
                ],
                "route_revision_proposals": [
                    {
                        "proposal_id": "proposal:rejected_bridge",
                        "refinement_evidence_id": "evidence:rejected_bridge",
                        "refinement_item_id": "refinement:rejected_bridge",
                        "goal_plan_id": "goal:rejected-evidence",
                        "route_id": "route:rejected-evidence",
                        "display_name": display_name,
                        "hook_kind": "route_revision",
                        "route_revision_summary": "this rejected proposal must not apply",
                        "route_revision_reasons": [
                            "rejected evidence should remain status-only"
                        ],
                        "revised_selected_primitives": [
                            "existing_rank",
                            "rejected_bridge",
                        ],
                        "revised_delta_primitives": ["rejected_bridge"],
                        "revised_informal_knowledge_dag_nodes": [
                            {
                                "node_id": "informal:rejected_bridge",
                                "kind": "lemma",
                                "label": "rejected_bridge",
                            }
                        ],
                        "revised_formal_realization_dag_nodes": [
                            {
                                "node_id": "formal:rejected_bridge",
                                "kind": "bridge",
                                "label": "rejected_bridge",
                            }
                        ],
                        "source_refs": ["paper:rejected-bridge"],
                        "residual_goals": ["rejected bridge residual should not propagate"],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        overlay_dir,
    )

    assert payload["all_ok"]
    assert payload["n_refinement_evidence_rows"] == 1
    assert payload["n_refinement_evidence_usable_rows"] == 0
    assert payload["n_refinement_evidence_route_revision_proposals_total"] == 1
    assert payload["n_refinement_evidence_route_revision_proposals"] == 0
    assert payload["n_refinement_evidence_route_revision_proposals_status_only"] == 1
    assert payload["n_routes_without_revision"] == 1
    assert payload["n_routes_with_revision"] == 0
    row = payload["rows"][0]
    assert row["revision_status"] == "NO_ROUTE_REVISION_PROPOSAL"
    assert row["revised_selected_primitives"] == ("existing_rank",)
    assert row["applied_refinement_evidence_ids"] == ()
    assert row["source_refs"] == ()
    assert row["residual_goals"] == ()


def test_route_revision_overlay_applies_resource_response_ledger_feedback() -> None:
    root = Path("runs/test_formalization_gap_planner_route_revision_overlay_ledger")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    ledger_dir = root / "ledger"
    overlay_dir = root / "overlay"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    display_name = "distribution_free_rank_bound"
    proof_boundary = (
        "Formalization gap planner resource-response ledger rows validate local "
        "and frontier resource outputs against request contracts and "
        "route-revision handoff fields. They are adapter evidence and planner "
        "feedback, not theorem proof evidence."
    )
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "rows": [
                    {
                        "goal_plan_id": "goal:ledger",
                        "route_id": "route:ledger",
                        "display_name": display_name,
                        "selected_primitives": ["rank_uniformity"],
                        "minimal_additional_formalization_nodes": [],
                        "informal_knowledge_dag": {
                            "nodes": [
                                {
                                    "node_id": "informal:rank_uniformity",
                                    "kind": "required_primitive",
                                    "label": "rank_uniformity",
                                }
                            ]
                        },
                        "lean_realization_dag": {
                            "nodes": [
                                {
                                    "node_id": "lean:rank_uniformity:gap",
                                    "kind": "bridge_needed",
                                    "label": "rank_uniformity",
                                }
                            ]
                        },
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
                "component_name": "formalization_gap_planner_refinement_evidence",
                "route_revision_proposals": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        ledger_dir / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_response_ledger",
                "rows": [
                    {
                        "schema_version": 11,
                        "resource_response_ledger_id": "ledger:rank_uniformity",
                        "resource_request_id": "request:rank_uniformity",
                        "action_resource_plan_id": "action-resource-plan:rank_uniformity",
                        "primitive_action_id": "primitive-action:rank_uniformity",
                        "coverage_map_id": "coverage:rank_uniformity",
                        "goal_plan_id": "goal:ledger",
                        "route_id": "route:ledger",
                        "display_name": display_name,
                        "primitive": "rank_uniformity",
                        "target_primitives": ["rank_uniformity"],
                        "actionable_work_items": [
                            "rank_uniformity: prove finite rank uniformity from exchangeability"
                        ],
                        "coverage_bucket": "bridge_needed",
                        "queue_action_kind": "prove_bridge_lemma",
                        "priority_score": 82,
                        "minimal_delta_cost_score": 40,
                        "reuse_readiness_score": 70,
                        "evidence_readiness_score": 75,
                        "priority_rationale": [
                            "coverage_status=bridge_needed",
                            "minimal_delta_cost_score=40",
                            "reuse_readiness_score=70",
                            "evidence_readiness_score=75",
                        ],
                        "target_prover_family": "lean4",
                        "library_snapshot_ref": "snapshot:test",
                        "candidate_declaration_rows": [
                            {
                                "declaration": "Mathlib.Data.Fintype.Card",
                                "target_prover_family": "lean4",
                                "source_field": "lean_declaration_hits",
                            }
                        ],
                        "request_phase": "proof_state_feedback",
                        "component_ids": ["prover_feedback_loop"],
                        "resource_id": "lean_lsp_mcp",
                        "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
                        "stop_conditions": [
                            "residual goals or diagnostics identify route repair"
                        ],
                        "quality_controls": {
                            "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
                            "response_validation_signals": [
                                "residual_goals_or_diagnostics_present"
                            ],
                            "stop_conditions": [
                                "residual goals or diagnostics identify route repair"
                            ],
                        },
                        "expected_response_artifact": "prover_feedback",
                        "dispatch_spec": {
                            "dispatch_kind": "frontier_mcp_or_cli",
                            "adapter_surface": "target_prover_lsp_mcp",
                            "resource_id": "lean_lsp_mcp",
                            "request_phase": "proof_state_feedback",
                            "target_prover_family": "lean4",
                            "execution_command": "dispatch lean4 proof-state request through lean_lsp_mcp",
                            "mcp_or_cli_hint": "target-prover LSP MCP adapter",
                            "expected_response_artifact": "prover_feedback",
                            "response_jsonl_contract": "formalization_gap_planner_resource_responses.jsonl",
                            "proof_evidence_boundary": "not theorem proof evidence",
                        },
                        "llm_route_planner_trace_present": True,
                        "llm_route_planner_row_id": "llm_route_row:rank",
                        "llm_route_planner_request_id": "llm_route_request:rank",
                        "llm_route_planner_source_kind": "planner_next_action",
                        "llm_route_planner_source_index": 0,
                        "llm_route_planner_hook_kind": "proof_state_feedback",
                        "llm_route_planner_queries": [
                            "ask Lean LSP for residual goals on rank_uniformity"
                        ],
                        "llm_route_planner_source_item": {
                            "action": (
                                "ask Lean LSP for residual goals on rank_uniformity"
                            ),
                            "resource_id": "lean_lsp_mcp",
                            "target_primitives": ["rank_uniformity"],
                        },
                        "residual_goal_context": {
                            "source_kind": "planner_next_action",
                            "residual_goal": "prove finite denominator is nonzero",
                            "residual_goals": ["prove finite denominator is nonzero"],
                            "residual_primitives": ["rank_uniformity"],
                            "target_primitives": ["rank_uniformity"],
                            "interpretation": (
                                "Lean feedback exposed a finite-rank denominator "
                                "side condition"
                            ),
                            "route_repair": (
                                "add the finite-denominator side condition to "
                                "the rank_uniformity bridge route"
                            ),
                            "repair_action": "revise the rank_uniformity bridge route",
                            "source_refs": [
                                "Vovk-Gammerman-Shafer conformal prediction"
                            ],
                            "queries": [
                                "ask Lean LSP for residual goals on rank_uniformity"
                            ],
                        },
                        "llm_route_planner_response_trace_grounded": True,
                        "llm_route_planner_response_trace_mismatches": [],
                        "response_present": True,
                        "response_contract_ok": True,
                        "response_payload": {
                            "source_snippets": [
                                {
                                    "source_ref": "Vovk-Gammerman-Shafer conformal prediction",
                                    "claim": "exchangeable ranks are uniform under finite tie handling",
                                    "excerpt": "The finite-rank proof requires a nonzero denominator side condition.",
                                    "target_primitives": ["rank_uniformity"],
                                }
                            ]
                        },
                        "response_summary": (
                            "Lean feedback exposed a finite-rank side condition"
                        ),
                        "response_artifacts": [],
                        "matched_response_contract_fields": ["residual_goals"],
                        "missing_response_contract_fields": [],
                        "source_refs": ["Vovk-Gammerman-Shafer conformal prediction"],
                        "route_evidence_nodes": [
                            {
                                "node_id": "informal:rank_uniformity:source",
                                "claim": "exchangeable ranks are uniform",
                            }
                        ],
                        "lean_declaration_hits": [
                            {
                                "declaration": "Mathlib.Data.Fintype.Card",
                                "namespace": "Mathlib",
                            }
                        ],
                        "coverage_updates": {"rank_uniformity": "bridge_needed"},
                        "prover_diagnostics": [
                            "unknown identifier finite_rank_uniformity"
                        ],
                        "residual_goals": ["prove finite denominator is nonzero"],
                        "prover_attempt_status": "failed_with_residual_goals",
                        "prover_diagnostic_signature": (
                            "unknown_identifier:finite_rank_uniformity"
                        ),
                        "route_revision_recommended": True,
                        "route_revision_reasons": [
                            "proof-state feedback exposed finite-rank side condition"
                        ],
                        "acceptance_status": "ACCEPTED_WITH_ROUTE_REVISION",
                        "proof_evidence_status": (
                            "FORMALIZATION_GAP_PLANNER_RESOURCE_RESPONSE_LEDGER_NOT_PROOF_EVIDENCE"
                        ),
                        "proof_evidence_boundary": proof_boundary,
                        "ok": True,
                        "errors": [],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    overlay_payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        overlay_dir,
        formalization_gap_planner_resource_response_ledger_dir=ledger_dir,
    )

    assert overlay_payload["all_ok"]
    assert overlay_payload["n_refinement_evidence_route_revision_proposals"] == 0
    assert overlay_payload["n_resource_response_ledger_rows"] == 1
    assert overlay_payload["n_resource_response_ledger_route_revision_proposals"] == 1
    assert overlay_payload["n_applied_resource_response_traces"] == 1
    assert overlay_payload["n_applied_llm_route_planner_hook_traces"] == 1
    assert overlay_payload["n_routes_with_resource_response_trace"] == 1
    assert overlay_payload["n_routes_with_llm_route_planner_hook_trace"] == 1
    assert overlay_payload["n_routes_with_resource_response_status"] == 1
    assert overlay_payload["n_resource_response_ledger_status_rows"] == 1
    assert overlay_payload["n_resource_response_ledger_awaiting"] == 0
    assert overlay_payload["n_resource_response_ledger_rejected"] == 0
    assert (
        overlay_payload[
            "n_applied_resource_response_traces_with_minimal_delta_priority"
        ]
        == 1
    )
    assert (
        overlay_payload[
            "average_applied_resource_response_reuse_readiness_score"
        ]
        == 70
    )
    assert (
        overlay_payload[
            "average_applied_resource_response_evidence_readiness_score"
        ]
        == 75
    )
    assert overlay_payload["n_route_revision_proposals"] == 1
    assert overlay_payload["n_routes_with_revision"] == 1
    assert overlay_payload["n_source_snippets"] == 1
    assert overlay_payload["n_routes_with_source_snippets"] == 1
    overlay_row = overlay_payload["rows"][0]
    assert overlay_row["revision_status"] == "ROUTE_REVISION_APPLIED"
    assert overlay_row["applied_hook_kinds"] == ("resource_response_ledger",)
    assert overlay_row["resource_response_summary"]["queued"] == 1
    assert overlay_row["resource_response_summary"]["accepted"] == 1
    assert overlay_row["resource_response_summary"]["route_revision_recommended"] == 1
    assert overlay_row["resource_response_summary_by_acceptance_status"] == {
        "ACCEPTED_WITH_ROUTE_REVISION": 1
    }
    assert overlay_row["resource_response_awaiting_request_ids"] == ()
    assert overlay_row["resource_response_rejected_request_ids"] == ()
    assert overlay_row["quality_controls"]["resource_contract_ids"] == (
        "lean_lsp:proof_state_feedback",
    )
    assert overlay_row["quality_controls"]["response_validation_signals"] == (
        "residual_goals_or_diagnostics_present",
    )
    assert overlay_row["applied_resource_response_traces"]
    trace = overlay_row["applied_resource_response_traces"][0]
    assert trace["resource_response_ledger_id"] == "ledger:rank_uniformity"
    assert trace["resource_request_id"] == "request:rank_uniformity"
    assert trace["resource_id"] == "lean_lsp_mcp"
    assert trace["target_primitives"] == ("rank_uniformity",)
    assert trace["actionable_work_items"] == (
        "rank_uniformity: prove finite rank uniformity from exchangeability",
    )
    assert trace["priority_score"] == 82
    assert trace["minimal_delta_cost_score"] == 40
    assert trace["reuse_readiness_score"] == 70
    assert trace["evidence_readiness_score"] == 75
    assert set(trace["priority_rationale"]) == {
        "coverage_status=bridge_needed",
        "minimal_delta_cost_score=40",
        "reuse_readiness_score=70",
        "evidence_readiness_score=75",
    }
    assert trace["quality_controls"]["resource_contract_ids"] == (
        "lean_lsp:proof_state_feedback",
    )
    assert trace["dispatch_spec"]["adapter_surface"] == "target_prover_lsp_mcp"
    assert trace["candidate_declaration_rows"] == (
        {
            "declaration": "Mathlib.Data.Fintype.Card",
            "target_prover_family": "lean4",
            "source_field": "lean_declaration_hits",
        },
    )
    assert trace["formal_declaration_hits"] == (
        {
            "declaration": "Mathlib.Data.Fintype.Card",
            "namespace": "Mathlib",
        },
    )
    assert trace["lean_declaration_hits"] == trace["formal_declaration_hits"]
    assert trace["matched_response_contract_fields"] == ("residual_goals",)
    assert trace["prover_diagnostic_signature"] == (
        "unknown_identifier:finite_rank_uniformity"
    )
    assert trace["llm_route_planner_trace_present"] is True
    assert trace["llm_route_planner_row_id"] == "llm_route_row:rank"
    assert trace["llm_route_planner_source_kind"] == "planner_next_action"
    assert trace["llm_route_planner_source_index"] == 0
    assert trace["llm_route_planner_hook_kind"] == "proof_state_feedback"
    assert trace["llm_route_planner_response_trace_grounded"] is True
    assert trace["llm_route_planner_response_trace_mismatches"] == ()
    assert trace["residual_goal_context"]["residual_goal"] == (
        "prove finite denominator is nonzero"
    )
    assert overlay_row["applied_llm_route_planner_hook_traces"]
    llm_trace = overlay_row["applied_llm_route_planner_hook_traces"][0]
    assert llm_trace["trace_source"] == "resource_response_ledger"
    assert llm_trace["resource_response_ledger_id"] == "ledger:rank_uniformity"
    assert llm_trace["resource_request_id"] == "request:rank_uniformity"
    assert llm_trace["actionable_work_items"] == (
        "rank_uniformity: prove finite rank uniformity from exchangeability",
    )
    assert llm_trace["minimal_delta_cost_score"] == 40
    assert llm_trace["reuse_readiness_score"] == 70
    assert llm_trace["evidence_readiness_score"] == 75
    assert llm_trace["priority_rationale"] == trace["priority_rationale"]
    assert llm_trace["llm_route_planner_row_id"] == "llm_route_row:rank"
    assert llm_trace["llm_route_planner_request_id"] == "llm_route_request:rank"
    assert llm_trace["llm_route_planner_source_kind"] == "planner_next_action"
    assert llm_trace["llm_route_planner_source_index"] == 0
    assert llm_trace["llm_route_planner_hook_kind"] == "proof_state_feedback"
    assert llm_trace["llm_route_planner_queries"] == (
        "ask Lean LSP for residual goals on rank_uniformity",
    )
    assert llm_trace["llm_route_planner_source_item"]["resource_id"] == (
        "lean_lsp_mcp"
    )
    assert llm_trace["llm_route_planner_response_trace_grounded"] is True
    assert llm_trace["residual_goal_context"]["residual_primitives"] == (
        "rank_uniformity",
    )
    assert overlay_row["source_refs"] == (
        "Vovk-Gammerman-Shafer conformal prediction",
    )
    assert overlay_row["source_snippets"][0]["source_ref"] == (
        "Vovk-Gammerman-Shafer conformal prediction"
    )
    assert "finite-rank proof" in overlay_row["source_snippets"][0]["excerpt"]
    assert overlay_row["residual_goals"] == ("prove finite denominator is nonzero",)
    assert overlay_row["applied_prover_attempt_statuses"] == (
        "failed_with_residual_goals",
    )
    assert overlay_row["applied_prover_attempt_classes"] == (
        "target_prover_failed",
    )
    assert overlay_row["target_prover_families"] == ("lean4",)
    assert overlay_row["applied_prover_diagnostic_signatures"] == (
        "unknown_identifier:finite_rank_uniformity",
    )
    assert "Mathlib.Data.Fintype.Card" in {
        hit["declaration"] for hit in overlay_row["lean_declaration_hits"]
    }
    assert overlay_row["formal_declaration_hits"] == overlay_row[
        "lean_declaration_hits"
    ]
    assert any(
        node.get("kind") == "resource_response_coverage_update"
        for node in overlay_row["revised_lean_realization_dag_nodes"]
    )
    assert any(
        node.get("resource_response_ledger_id") == "ledger:rank_uniformity"
        for node in overlay_row["revised_informal_knowledge_dag_nodes"]
    )
    assert not overlay_row["unaligned_primitives"]


def test_route_revision_overlay_preserves_awaiting_and_rejected_resource_status() -> None:
    root = Path("runs/test_formalization_gap_planner_route_revision_overlay_ledger_status")
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    ledger_dir = root / "ledger"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    display_name = "ledger status route"
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "rows": [
                    {
                        "goal_plan_id": "goal:ledger-status",
                        "route_id": "route:ledger-status",
                        "display_name": display_name,
                        "selected_primitives": ["score_definition"],
                        "minimal_additional_formalization_nodes": [],
                        "informal_knowledge_dag": {
                            "nodes": [
                                {
                                    "node_id": "informal:score_definition",
                                    "label": "score_definition",
                                }
                            ]
                        },
                        "lean_realization_dag": {
                            "nodes": [
                                {
                                    "node_id": "lean:score_definition",
                                    "label": "score_definition",
                                }
                            ]
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (
        evidence_dir / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(json.dumps({"route_revision_proposals": []}, indent=2), encoding="utf-8")
    (
        ledger_dir / "formalization_gap_planner_resource_response_ledger_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_resource_response_ledger",
                "rows": [
                    {
                        "resource_response_ledger_id": "ledger:awaiting",
                        "resource_request_id": "request:awaiting",
                        "goal_plan_id": "goal:ledger-status",
                        "route_id": "route:ledger-status",
                        "display_name": display_name,
                        "primitive": "score_definition",
                        "acceptance_status": "AWAITING_RESOURCE_RESPONSE",
                        "response_present": False,
                        "response_contract_ok": False,
                    },
                    {
                        "resource_response_ledger_id": "ledger:rejected",
                        "resource_request_id": "request:rejected",
                        "goal_plan_id": "goal:ledger-status",
                        "route_id": "route:ledger-status",
                        "display_name": display_name,
                        "primitive": "score_definition",
                        "acceptance_status": "REJECTED_RESPONSE_REQUEST_MISMATCH",
                        "response_present": True,
                        "response_contract_ok": False,
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        formalization_gap_planner_resource_response_ledger_dir=ledger_dir,
    )

    assert payload["all_ok"]
    assert payload["n_resource_response_ledger_rows"] == 2
    assert payload["n_resource_response_ledger_route_revision_proposals"] == 0
    assert payload["n_routes_without_revision"] == 1
    assert payload["n_resource_response_ledger_status_rows"] == 2
    assert payload["n_resource_response_ledger_awaiting"] == 1
    assert payload["n_resource_response_ledger_rejected"] == 1
    row = payload["rows"][0]
    assert row["revision_status"] == "NO_ROUTE_REVISION_PROPOSAL"
    assert row["resource_response_summary"]["queued"] == 2
    assert row["resource_response_summary"]["awaiting"] == 1
    assert row["resource_response_summary"]["rejected"] == 1
    assert row["resource_response_summary_by_acceptance_status"] == {
        "AWAITING_RESOURCE_RESPONSE": 1,
        "REJECTED_RESPONSE_REQUEST_MISMATCH": 1,
    }
    assert row["resource_response_awaiting_request_ids"] == ("request:awaiting",)
    assert row["resource_response_rejected_request_ids"] == ("request:rejected",)

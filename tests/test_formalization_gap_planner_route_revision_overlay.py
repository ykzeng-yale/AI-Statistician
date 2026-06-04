from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_refinement_adapters import (
    export_formalization_gap_planner_refinement_adapter_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)
from ai_statistician.formalization_gap_planner_route_revision_overlay import (
    export_formalization_gap_planner_route_revision_overlay,
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
    overlay_row = overlay_payload["rows"][0]
    assert overlay_row["revision_status"] == "ROUTE_REVISION_APPLIED"
    assert "conditional_mean_residual_zero" in overlay_row["added_primitives"]
    assert "nuisance_correctness_cases" in overlay_row["revised_delta_primitives"]
    assert overlay_payload["by_prover_attempt_status"] == {
        "formal_gap_scaffold_blocked": 1
    }
    assert overlay_payload["n_routes_with_prover_attempt_status"] == 1
    assert overlay_row["applied_prover_attempt_statuses"] == (
        "formal_gap_scaffold_blocked",
    )
    assert overlay_row["applied_prover_diagnostic_signatures"] == (
        "prover_diagnostic_signature:test",
    )
    assert len(overlay_row["revised_lean_realization_dag_nodes"]) >= 4
    assert "not theorem proof evidence" in overlay_payload["proof_evidence_boundary"]

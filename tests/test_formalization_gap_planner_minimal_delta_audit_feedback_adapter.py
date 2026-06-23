from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.formalization_gap_planner_minimal_delta_audit import (
    audit_formalization_gap_planner_minimal_delta,
)
from ai_statistician.formalization_gap_planner_minimal_delta_audit_feedback_adapter import (
    export_formalization_gap_planner_minimal_delta_audit_feedback_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)
from ai_statistician.formalization_gap_planner_route_revision_overlay import (
    export_formalization_gap_planner_route_revision_overlay,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_minimal_delta_audit_feedback_feeds_route_revision_overlay() -> None:
    root = Path("runs/test_formalization_gap_planner_minimal_delta_audit_feedback")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    audit_dir = root / "minimal_delta_audit"
    queue_dir = root / "queue"
    adapter_dir = root / "adapter"
    evidence_dir = root / "evidence"
    overlay_dir = root / "overlay"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(json.dumps(_standalone_input(), indent=2), encoding="utf-8")
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    _write_route_revision_queue(queue_dir)

    audit_payload = audit_formalization_gap_planner_minimal_delta(plan_dir, audit_dir)
    assert not audit_payload["all_ok"]
    assert audit_payload["n_rows_with_cost_graph_selection_ok"] == 0

    adapter_payload = export_formalization_gap_planner_minimal_delta_audit_feedback_responses(
        queue_dir,
        audit_dir,
        adapter_dir,
    )

    assert adapter_payload["all_ok"]
    assert adapter_payload["n_generated_feedback_responses"] == 1
    assert adapter_payload["n_route_revision_recommended"] == 1
    response = adapter_payload["responses"][0]
    assert response["evidence_kind"] == "route_revision_proposal"
    assert response["tool_name"] == "minimal_delta_audit_feedback_adapter"
    assert response["revised_selected_primitives"] == ("cheap_wrapper",)
    assert response["revised_delta_primitives"] == ("cheap_wrapper",)
    assert any(
        "lower-cost route option" in reason
        for reason in response["route_revision_reasons"]
    )
    assert (
        adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
    ).exists()

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=(
            adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        ),
    )
    assert evidence_payload["all_ok"]
    assert evidence_payload["n_route_revision_proposals"] == 1
    proposal = evidence_payload["route_revision_proposals"][0]
    assert proposal["revised_selected_primitives"] == ("cheap_wrapper",)
    assert proposal["hook_kind"] == "route_revision"

    overlay_payload = export_formalization_gap_planner_route_revision_overlay(
        plan_dir,
        evidence_dir,
        overlay_dir,
    )
    assert overlay_payload["all_ok"]
    assert overlay_payload["n_unaligned_primitives"] == 0
    overlay_row = overlay_payload["rows"][0]
    assert overlay_row["revised_selected_primitives"] == ("cheap_wrapper",)
    assert overlay_row["added_primitives"] == ("cheap_wrapper",)
    assert overlay_row["removed_primitives"] == ("expensive_bridge",)


def test_minimal_delta_audit_feedback_cli() -> None:
    root = Path("runs/test_formalization_gap_planner_minimal_delta_audit_feedback_cli")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    audit_dir = root / "minimal_delta_audit"
    queue_dir = root / "queue"
    out_dir = root / "out"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(json.dumps(_standalone_input(), indent=2), encoding="utf-8")
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    audit_formalization_gap_planner_minimal_delta(plan_dir, audit_dir)
    _write_route_revision_queue(queue_dir)

    rc = main(
        [
            "formalization-gap-planner-minimal-delta-audit-feedback",
            "--formalization-gap-planner-refinement-queue-dir",
            str(queue_dir),
            "--formalization-gap-planner-minimal-delta-audit-dir",
            str(audit_dir),
            "--out",
            str(out_dir),
        ]
    )

    assert rc == 0
    manifest = json.loads(
        (
            out_dir
            / "formalization_gap_planner_minimal_delta_audit_feedback_adapter_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["all_ok"]
    assert manifest["n_generated_feedback_responses"] == 1
    assert (
        out_dir
        / "formalization_gap_planner_minimal_delta_audit_feedback_responses.jsonl"
    ).exists()


def _standalone_input() -> dict[str, object]:
    return {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_standalone_input",
        "target_prover_family": "lean4",
        "library_snapshot_ref": "mathlib4:minimal-delta-feedback",
        "routes": [
            {
                "route_id": "route:rank",
                "display_name": "rank route",
                "theorem_statement": "A rank route has a cheaper wrapper alternative.",
                "minimal_delta_plan": {
                    "selected_primitives": ["expensive_bridge"],
                    "cost_model_version": (
                        "formalization_gap_planner_minimal_delta_cost_policy:1"
                    ),
                    "route_cost": 10,
                    "primitive_costs": [
                        {
                            "primitive": "expensive_bridge",
                            "base_cost": 10,
                            "proof_difficulty_cost": 0,
                            "import_cone_cost": 0,
                            "definition_or_typeclass_cost": 0,
                            "semantic_risk_cost": 0,
                            "reuse_credit": 0,
                            "total_cost": 10,
                            "cost_rationale": "nonminimal selected route",
                        }
                    ],
                    "and_or_cost_graph": {
                        "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                        "selected_route_option_id": "route_option:expensive",
                        "route_options": [
                            {
                                "route_option_id": "route_option:expensive",
                                "selected": True,
                                "selected_primitives": ["expensive_bridge"],
                                "route_cost": 10,
                                "cost_rationale": "not actually cheapest",
                            },
                            {
                                "route_option_id": "route_option:cheap",
                                "selected": False,
                                "selected_primitives": ["cheap_wrapper"],
                                "route_cost": 3,
                                "cost_rationale": "cheaper wrapper route",
                            },
                        ],
                        "or_nodes": [
                            {
                                "node_id": "route_choice",
                                "choices": [
                                    "route_option:expensive",
                                    "route_option:cheap",
                                ],
                                "selection_rationale": "bad selected route",
                            }
                        ],
                        "and_edges": [
                            {
                                "route_option_id": "route_option:expensive",
                                "requires": ["expensive_bridge"],
                            },
                            {
                                "route_option_id": "route_option:cheap",
                                "requires": ["cheap_wrapper"],
                            },
                        ],
                    },
                    "minimality_rationale": "This selected option should be repaired.",
                },
                "primitives": [
                    {
                        "primitive": "expensive_bridge",
                        "coverage_status": "bridge_needed",
                    }
                ],
            }
        ],
    }


def _write_route_revision_queue(queue_dir: Path) -> None:
    rows = [
        {
            "schema_version": 2,
            "refinement_item_id": "refinement:minimal-delta-rank",
            "goal_plan_id": "goal:rank",
            "route_id": "route:rank",
            "display_name": "rank route",
            "theorem_skeleton": "",
            "theorem_statement": "A rank route has a cheaper wrapper alternative.",
            "route_class": "bridge_or_wrapper",
            "pareto_profile": "non_dominated",
            "hook_kind": "route_revision",
            "refinement_stage": "minimal_delta_audit_feedback",
            "owner_agent": "minimal_delta_audit_feedback_adapter",
            "target_prover_family": "lean4",
            "target_primitives": ["expensive_bridge", "cheap_wrapper"],
            "trigger_kinds": ["minimal_delta_audit_failed"],
            "trigger_conditions": ["selected route option is not minimal"],
            "trigger_next_actions": ["revise selected route option"],
            "queries": ["repair minimal-delta route choice"],
            "recommended_tools": ["minimal_delta_audit_feedback_adapter"],
            "frontier_resource_adapters": [],
            "resource_request_ids": [],
            "resource_ids": [],
            "resource_request_bindings": [],
            "llm_route_planner_hook_trace": {
                "hook_id": "hook:minimal-delta-rank",
                "required_gate": "replan before route adoption",
            },
            "evaluation_signal": "no_evaluation_signal",
            "evaluation_route_missing_primitives": [],
            "evaluation_delta_missing_primitives": [],
            "evaluation_coverage_confusions": [],
            "prover_feedback_status": "",
            "prover_feedback_error_category": "",
            "prover_feedback_first_error": "",
            "acceptance_record": "",
            "expected_artifacts": [],
            "execution_commands": [],
            "required_gate": "rerun planner and overlay",
            "status": "READY_FOR_INTERACTIVE_REFINEMENT",
            "priority_score": 90,
            "rank": 1,
            "proof_evidence_status": "FORMALIZATION_GAP_PLANNER_REFINEMENT_QUEUE_NOT_PROOF_EVIDENCE",
            "proof_evidence_boundary": "not theorem proof evidence",
            "ok": True,
            "errors": [],
        }
    ]
    (queue_dir / "formalization_gap_planner_refinement_queue_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "component_name": "formalization_gap_planner_refinement_queue",
                "rows": rows,
                "all_ok": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

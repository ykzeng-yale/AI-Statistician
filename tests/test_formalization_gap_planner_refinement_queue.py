from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_refinement_queue import (
    export_formalization_gap_planner_refinement_queue,
    refinement_work_item_json_schema,
    validate_refinement_work_item_row,
)


def test_refinement_queue_emits_public_work_item_schema() -> None:
    root = Path("runs/test_formalization_gap_planner_refinement_queue")
    plan_dir = root / "plan"
    out_dir = root / "queue"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": (
                    "urn:ai-statistician:schemas:"
                    "library-aware-formalization-gap-plan:1"
                ),
                "rows": [
                    {
                        "goal_plan_id": "goal:queue",
                        "route_id": "route:queue",
                        "display_name": "queue route",
                        "target_prover_family": "lean4",
                        "theorem_statement": (
                            "A source-backed bridge lemma closes the target theorem."
                        ),
                        "route_class": "source_backed_bridge_route",
                        "pareto_profile": "lowest_delta",
                        "selected_primitives": ["bridge lemma"],
                        "minimal_additional_formalization_nodes": [
                            {
                                "primitive": "bridge lemma",
                                "action_class": "bridge_needed",
                            }
                        ],
                        "interactive_refinement_hooks": [
                            {
                                "hook_kind": "formal_library_grounding",
                                "queries": ["bridge lemma formal declaration"],
                                "recommended_tools": ["local formal-source index"],
                            }
                        ],
                        "route_revision_triggers": [
                            {
                                "trigger_kind": "formal_leaf_attempt_required",
                                "condition": "bridge lemma has no exact declaration",
                                "next_action": "search formal library before adding a bridge",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_refinement_queue(plan_dir, out_dir)

    assert payload["all_ok"]
    assert payload["n_refinement_items"] == 1
    assert payload["n_formal_library_grounding_items"] == 1
    assert payload["n_lean_library_grounding_items"] == 0
    assert payload["n_item_schema_valid"] == payload["n_refinement_items"]
    assert payload["n_item_schema_invalid"] == 0
    assert (
        payload["refinement_work_item_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-work-item:1"
    )
    row = payload["rows"][0]
    assert row["hook_kind"] == "formal_library_grounding"
    assert row["target_prover_family"] == "lean4"
    assert payload["by_target_prover_family"] == {"lean4": 1}
    assert "formal_library_grounding" in refinement_work_item_json_schema()["properties"][
        "hook_kind"
    ]["enum"]
    invalid = dict(row)
    invalid.pop("recommended_tools")
    assert "recommended_tools required" in validate_refinement_work_item_row(
        invalid,
        refinement_work_item_json_schema(),
    )
    assert (out_dir / "formalization_gap_planner_refinement_work_item.schema.json").exists()


def test_refinement_queue_uses_target_prover_proof_state_fallback_tools() -> None:
    root = Path("runs/test_formalization_gap_planner_refinement_queue_rocq_tools")
    plan_dir = root / "plan"
    out_dir = root / "queue"
    shutil.rmtree(root, ignore_errors=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "library_aware_formalization_gap_planner",
                "portable_schema_id": (
                    "urn:ai-statistician:schemas:"
                    "library-aware-formalization-gap-plan:1"
                ),
                "rows": [
                    {
                        "goal_plan_id": "goal:rocq-queue",
                        "route_id": "route:rocq-queue",
                        "display_name": "rocq queue route",
                        "target_prover_family": "rocq",
                        "theorem_statement": (
                            "Theorem rocq_bridge : True. Proof. exact I. Qed."
                        ),
                        "route_class": "source_backed_bridge_route",
                        "pareto_profile": "lowest_delta",
                        "selected_primitives": ["rocq bridge lemma"],
                        "minimal_additional_formalization_nodes": [
                            {
                                "primitive": "rocq bridge lemma",
                                "action_class": "bridge_needed",
                            }
                        ],
                        "interactive_refinement_hooks": [
                            {
                                "hook_kind": "proof_state_feedback",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_refinement_queue(plan_dir, out_dir)

    assert payload["all_ok"]
    assert payload["n_proof_state_feedback_items"] == 1
    row = payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert "Rocq/coq-lsp proof-state adapter" in row["recommended_tools"]
    assert "SerAPI/sertop" in row["frontier_resource_adapters"]
    assert "lean-lsp-mcp" not in row["recommended_tools"]
    assert "lake build" not in row["frontier_resource_adapters"]
    assert "rocq proof-state and kernel-check tools" in row["execution_commands"][0]

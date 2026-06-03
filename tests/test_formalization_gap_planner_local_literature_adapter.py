from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_local_literature_adapter import (
    export_formalization_gap_planner_local_literature_adapter_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)


def test_local_literature_adapter_emits_source_backed_route_evidence() -> None:
    root = Path("runs/test_formalization_gap_planner_local_literature_adapter")
    queue_dir = root / "queue"
    corpus_dir = root / "papers"
    adapter_dir = root / "adapter"
    evidence_dir = root / "evidence"
    base_response_jsonl = root / "base_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / "aipw_double_robustness.md").write_text(
        "\n".join(
            [
                "# AIPW double robustness route note",
                "",
                "The augmented inverse probability weighted estimator uses an",
                "orthogonal score. In the outcome-model branch, the conditional",
                "mean residual zero identity makes the augmentation term vanish.",
                "The proof route then reduces the AIPW score definition to the",
                "target average treatment effect estimand.",
            ]
        ),
        encoding="utf-8",
    )
    display_name = "causal_ate_aipw:aipw_double_robustness:skeleton"
    queue_rows = [
        {
            "refinement_item_id": "refinement:literature",
            "goal_plan_id": "goal:test",
            "route_id": "route:test",
            "display_name": display_name,
            "hook_kind": "literature_discovery",
            "refinement_stage": "literature",
            "owner_agent": "literature",
            "target_primitives": ["conditional_mean_residual_zero"],
            "queries": ["conditional mean residual zero AIPW double robustness"],
        },
        {
            "refinement_item_id": "refinement:lean",
            "goal_plan_id": "goal:test",
            "route_id": "route:test",
            "display_name": display_name,
            "hook_kind": "lean_library_grounding",
            "refinement_stage": "lean",
            "owner_agent": "lean",
            "target_primitives": ["conditional_mean_residual_zero"],
            "queries": ["conditional mean residual zero Lean theorem"],
        },
    ]
    (queue_dir / "formalization_gap_planner_refinement_queue_manifest.json").write_text(
        json.dumps({"rows": queue_rows}, indent=2),
        encoding="utf-8",
    )
    base_response_jsonl.write_text(
        json.dumps(
            {
                "refinement_item_id": "refinement:lean",
                "route_id": "route:test",
                "display_name": display_name,
                "evidence_kind": "lean_library_grounding",
                "tool_name": "fixture_lean_grounding_adapter",
                "lean_declaration_hits": [
                    {
                        "primitive": "conditional_mean_residual_zero",
                        "declaration": "Demo.conditional_mean_residual_zero",
                    }
                ],
                "coverage_updates": {"conditional_mean_residual_zero": "exact_exists"},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_local_literature_adapter_responses(
        queue_dir,
        adapter_dir,
        literature_roots=(corpus_dir,),
        base_response_jsonl=base_response_jsonl,
        k=2,
    )

    assert payload["all_ok"]
    assert payload["n_local_literature_responses"] == 1
    assert payload["n_merged_responses"] == 2
    assert payload["n_source_hits"] == 1
    response = payload["responses"][0]
    assert response["evidence_kind"] == "literature_route_evidence"
    assert response["source_refs"]
    assert response["route_evidence_nodes"][0]["kind"] == "source_ref"
    assert "conditional" in response["route_evidence_nodes"][0]["matched_terms"]
    assert not response["route_revision_recommended"]

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    assert evidence_payload["n_contract_ok"] == 2
    assert evidence_payload["n_literature_evidence"] == 1
    assert evidence_payload["n_awaiting_tool_response"] == 0

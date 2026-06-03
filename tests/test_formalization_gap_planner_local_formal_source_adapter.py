from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formal_source_index import FormalSourceRoot
from ai_statistician.formalization_gap_planner_local_formal_source_adapter import (
    export_formalization_gap_planner_local_formal_source_adapter_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)


def test_local_formal_source_adapter_emits_lean_grounding_responses() -> None:
    root = Path("runs/test_formalization_gap_planner_local_formal_source_adapter")
    queue_dir = root / "queue"
    source_dir = root / "lean_src"
    adapter_dir = root / "adapter"
    evidence_dir = root / "evidence"
    base_response_jsonl = root / "base_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "Demo.lean").write_text(
        "\n".join(
            [
                "namespace Demo",
                "theorem conditional_mean_residual_zero : True := by trivial",
                "theorem aipw_score_definition : True := by trivial",
                "end Demo",
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
            "queries": ["conditional mean residual zero AIPW"],
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
                "refinement_item_id": "refinement:literature",
                "route_id": "route:test",
                "display_name": display_name,
                "evidence_kind": "literature_route_evidence",
                "tool_name": "fixture_literature_adapter",
                "source_refs": ["fixture_source"],
                "route_evidence_nodes": [
                    {
                        "node_id": "source:fixture",
                        "kind": "source_ref",
                        "label": "fixture_source",
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_local_formal_source_adapter_responses(
        queue_dir,
        adapter_dir,
        formal_source_roots=(FormalSourceRoot("fixture", str(source_dir)),),
        base_response_jsonl=base_response_jsonl,
        k=3,
    )

    assert payload["all_ok"]
    assert payload["n_local_formal_source_responses"] == 1
    assert payload["n_merged_responses"] == 2
    assert payload["n_hits"] >= 1
    response = payload["responses"][0]
    assert response["coverage_updates"]["conditional_mean_residual_zero"] == "exact_exists"
    assert response["lean_declaration_hits"][0]["declaration"].endswith(
        "conditional_mean_residual_zero"
    )

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    assert evidence_payload["n_contract_ok"] == 2
    assert evidence_payload["n_awaiting_tool_response"] == 0

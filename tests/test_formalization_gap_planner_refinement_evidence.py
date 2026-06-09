from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)


def test_refinement_evidence_rejects_expanded_target_primitives() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_refinement_evidence_target_scope"
    )
    queue_dir = root / "queue"
    evidence_dir = root / "evidence"
    response_jsonl = root / "responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_row = {
        "refinement_item_id": "refinement:proof",
        "goal_plan_id": "goal:test",
        "route_id": "route:test",
        "display_name": "demo:rank_uniformity",
        "hook_kind": "proof_state_feedback",
        "refinement_stage": "prover_feedback",
        "owner_agent": "formalizer",
        "target_primitives": ["rank_uniformity"],
        "resource_request_bindings": [],
    }
    (
        queue_dir / "formalization_gap_planner_refinement_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_refinement_queue",
                "rows": [queue_row],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    response_jsonl.write_text(
        json.dumps(
            {
                "refinement_item_id": "refinement:proof",
                "route_id": "route:test",
                "display_name": "demo:rank_uniformity",
                "evidence_kind": "prover_feedback",
                "tool_name": "fixture_prover_feedback_adapter",
                "target_primitives": ["rank_uniformity", "spectral_gap"],
                "prover_diagnostics": ["unsolved goal: rank_uniformity"],
                "residual_goals": ["rank_uniformity remains open"],
                "route_revision_recommended": True,
                "route_revision_reasons": [
                    "residual goal requires route repair",
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=response_jsonl,
    )

    assert not payload["all_ok"]
    assert payload["n_rejected"] == 1
    assert payload["n_response_schema_valid"] == 1
    assert payload["n_evidence_row_schema_valid"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "REJECTED_REFINEMENT_EVIDENCE_CONTRACT"
    assert tuple(row["target_primitives"]) == ("rank_uniformity", "spectral_gap")
    assert any(
        "target_primitives must not expand beyond refinement queue target_primitives"
        in error
        and "spectral_gap" in error
        for error in row["errors"]
    )
    proposal = payload["route_revision_proposals"][0]
    assert tuple(proposal["target_primitives"]) == (
        "rank_uniformity",
        "spectral_gap",
    )

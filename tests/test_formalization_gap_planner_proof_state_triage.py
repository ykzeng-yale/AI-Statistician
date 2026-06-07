from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_proof_state_triage import (
    export_formalization_gap_planner_proof_state_triage,
    proof_state_triage_row_json_schema,
    validate_proof_state_triage_row,
)


def test_proof_state_triage_ranks_formal_gap_scaffold_routes() -> None:
    root = Path("runs/test_formalization_gap_planner_proof_state_triage")
    overlay_dir = root / "overlay"
    triage_dir = root / "triage"
    shutil.rmtree(root, ignore_errors=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)
    (overlay_dir / "formalization_gap_planner_route_revision_overlay_manifest.json").write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_revision_overlay",
                "rows": [
                    {
                        "route_revision_overlay_id": "overlay:formal_gap",
                        "goal_plan_id": "goal:test",
                        "route_id": "route:test",
                        "display_name": "causal_ate_aipw:aipw_double_robustness:skeleton",
                        "revision_status": "ROUTE_REVISION_APPLIED",
                        "applied_prover_attempt_statuses": [
                            "formal_gap_scaffold_blocked"
                        ],
                        "applied_prover_attempt_classes": [
                            "formal_gap_scaffold_blocked"
                        ],
                        "target_prover_families": ["lean4"],
                        "applied_prover_diagnostic_signatures": [
                            "prover_diagnostic_signature:formal_gap"
                        ],
                        "residual_goals": [
                            "nuisance_correctness_cases: formal-gap placeholder scaffold"
                        ],
                        "added_delta_primitives": ["nuisance_correctness_cases"],
                    },
                    {
                        "route_revision_overlay_id": "overlay:no_status",
                        "goal_plan_id": "goal:unused",
                        "route_id": "route:unused",
                        "display_name": "unused",
                        "revision_status": "ROUTE_REVISION_APPLIED",
                        "applied_prover_attempt_statuses": [],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_proof_state_triage(
        overlay_dir,
        triage_dir,
    )

    assert payload["all_ok"]
    assert payload["n_overlay_rows"] == 2
    assert payload["n_triage_items"] == 1
    assert payload["n_row_schema_valid"] == payload["n_triage_items"]
    assert payload["n_row_schema_invalid"] == 0
    assert (
        payload["triage_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-proof-state-triage-row:1"
    )
    assert payload["n_formal_gap_scaffold_items"] == 1
    assert payload["target_prover_families"] == ("lean4",)
    assert payload["by_triage_class"] == {
        "materialize_non_placeholder_theorem": 1
    }
    assert payload["by_prover_triage_class"] == {
        "materialize_non_placeholder_theorem": 1
    }
    assert payload["by_prover_attempt_status"] == {
        "formal_gap_scaffold_blocked": 1
    }
    assert payload["by_prover_attempt_class"] == {
        "formal_gap_scaffold_blocked": 1
    }
    row = payload["rows"][0]
    assert row["rank"] == 1
    assert row["owner_agent"] == "formalization_planner"
    assert row["triage_class"] == "materialize_non_placeholder_theorem"
    assert row["prover_triage_class"] == "materialize_non_placeholder_theorem"
    assert row["applied_prover_attempt_classes"] == (
        "formal_gap_scaffold_blocked",
    )
    assert row["target_prover_families"] == ("lean4",)
    assert "non-placeholder" in row["recommended_next_action"]
    assert "proof-state adapter" in row["recommended_tools"]
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    broken_row = dict(row)
    broken_row.pop("recommended_tools")
    assert "recommended_tools required" in validate_proof_state_triage_row(
        broken_row,
        proof_state_triage_row_json_schema(),
    )
    assert (
        triage_dir / "formalization_gap_planner_proof_state_triage_manifest.json"
    ).exists()
    assert (
        triage_dir / "formalization_gap_planner_proof_state_triage_row.schema.json"
    ).exists()
    assert (
        triage_dir / "formalization_gap_planner_proof_state_triage.jsonl"
    ).exists()

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_minimal_delta_audit import (
    audit_formalization_gap_planner_minimal_delta,
    minimal_delta_decision_row_json_schema,
    validate_minimal_delta_decision_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_minimal_delta_audit_accepts_costed_standalone_plan() -> None:
    root = Path("runs/test_formalization_gap_planner_minimal_delta_audit")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:minimal-delta",
                "background_primitives": ["unrelated_large_measure_theory"],
                "routes": [
                    {
                        "display_name": "demo_minimal_delta_route",
                        "theorem_statement": "A route follows from reuse and one bridge.",
                        "primitives": [
                            {
                                "primitive": "existing_rank_order",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Existing.rank_order"],
                            },
                            {
                                "primitive": "rank_uniformity_bridge",
                                "coverage_status": "bridge_needed",
                            },
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)

    payload = audit_formalization_gap_planner_minimal_delta(plan_dir, audit_dir)

    assert payload["all_ok"]
    assert payload["n_plan_rows"] == 1
    assert payload["n_failed"] == 0
    assert payload["n_rows_with_cost_formula_ok"] == 1
    assert payload["n_rows_with_node_cost_accounting_ok"] == 1
    assert payload["n_rows_with_work_packet_cut_ok"] == 1
    assert payload["n_rows_with_do_not_formalize_disjoint"] == 1
    assert payload["n_rows_with_connected_delta_nodes"] == 1
    assert payload["n_dominated_route_witnesses"] == 0
    assert payload["n_minimal_delta_decision_rows"] == payload["n_plan_rows"]
    assert (
        payload["n_minimal_delta_decision_row_schema_valid"]
        == payload["n_minimal_delta_decision_rows"]
    )
    assert payload["n_minimal_delta_decision_row_schema_invalid"] == 0
    assert (
        payload["minimal_delta_decision_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-minimal-delta-decision-row:1"
    )
    decision_row = payload["minimal_delta_decision_rows"][0]
    assert decision_row["dominance_status"] == (
        "NON_DOMINATED_UNDER_CURRENT_STRUCTURAL_PROXY"
    )
    bad_row = dict(decision_row)
    bad_row.pop("route_cost_breakdown")
    assert validate_minimal_delta_decision_row(
        bad_row,
        minimal_delta_decision_row_json_schema(),
    )
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_audit_manifest.json"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_audit.jsonl"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_decisions.jsonl"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_decision_row.schema.json"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_minimal_delta_audit.md"
    ).exists()


def test_minimal_delta_audit_rejects_cost_formula_drift() -> None:
    root = Path("runs/test_formalization_gap_planner_minimal_delta_audit_rejects")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "mathlib4:minimal-delta",
                "routes": [
                    {
                        "display_name": "demo_broken_cost",
                        "primitives": [
                            {
                                "primitive": "demo_bridge",
                                "coverage_status": "bridge_needed",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    export_formalization_gap_planner_standalone_plan(input_json, plan_dir)
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rows"][0]["route_cost_breakdown"]["final_goal_conditioned_cost"] += 1
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_minimal_delta(plan_dir)

    assert not payload["all_ok"]
    failed = [row for row in payload["checks"] if not row["ok"]]
    assert any(row["check_name"].endswith(":cost_formula") for row in failed)

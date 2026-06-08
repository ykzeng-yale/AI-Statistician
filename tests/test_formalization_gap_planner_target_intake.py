from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)
from ai_statistician.formalization_gap_planner_target_intake import (
    FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID,
    FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID,
    normalize_formalization_gap_planner_target_intake,
    target_intake_row_json_schema,
    validate_target_intake_row,
)


def test_target_intake_seeds_standalone_gap_plan() -> None:
    root = Path("runs/test_formalization_gap_planner_target_intake")
    input_path = root / "target_request.json"
    intake_dir = root / "target_intake"
    plan_dir = root / "standalone_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "target_prover_family": "lean4",
                "library_snapshot_ref": "mathlib4:test-snapshot",
                "target_id": "split_conformal_coverage",
                "title": "Split conformal finite-sample coverage",
                "domain": "distribution-free prediction",
                "theorem_statement": (
                    "For exchangeable calibration and test scores, split "
                    "conformal prediction has finite sample marginal coverage."
                ),
                "objects": ["calibration scores", "test score"],
                "assumptions": [
                    "exchangeable calibration and test scores",
                    "finite calibration sample",
                ],
                "statistical_procedure": "split conformal prediction set",
                "desired_conclusion": "finite sample marginal coverage inequality",
                "desired_theorem_shape": "coverage probability lower bound",
                "known_proof_sources": ["Lei-Wasserman distribution-free prediction"],
                "candidate_primitives": [
                    {
                        "primitive": "rank uniformity",
                        "coverage_status": "bridge_needed",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    intake_payload = normalize_formalization_gap_planner_target_intake(
        input_path,
        intake_dir,
    )

    assert intake_payload["all_ok"]
    assert intake_payload["schema_id"] == FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_SCHEMA_ID
    assert intake_payload["n_targets"] == 1
    assert intake_payload["n_primitive_seed_rows"] >= 5
    assert intake_payload["n_formal_library_grounding_queries"] == intake_payload[
        "n_lean_grounding_queries"
    ]
    assert intake_payload["n_formal_library_grounding_queries"] > 0
    row = intake_payload["rows"][0]
    assert row["target_id"] == "split_conformal_coverage"
    assert "rank_uniformity" in row["extracted_primitive_candidates"]
    assert "exchangeability" in row["extracted_primitive_candidates"]
    assert row["formal_library_grounding_queries"] == row["lean_grounding_queries"]
    assert row["formal_library_grounding_queries"]
    assert row["proof_source_refs"]
    assert "library_coverage_search_required" in row["review_flags"]
    assert validate_target_intake_row(row) == []
    legacy_row = dict(row)
    legacy_row.pop("formal_library_grounding_queries")
    assert validate_target_intake_row(legacy_row) == []
    malformed_row = dict(row)
    malformed_row.pop("standalone_route_id")
    assert "standalone_route_id required" in validate_target_intake_row(malformed_row)
    standalone_seed_path = (
        intake_dir / "formalization_gap_planner_target_intake_standalone_seed.json"
    )
    assert standalone_seed_path.exists()
    seed = json.loads(standalone_seed_path.read_text(encoding="utf-8"))
    assert seed["component_name"] == "formalization_gap_planner_standalone_input"
    assert seed["routes"][0]["primitives"]

    plan_payload = export_formalization_gap_planner_standalone_plan(
        standalone_seed_path,
        plan_dir,
    )

    assert plan_payload["all_ok"]
    assert plan_payload["n_goal_plans"] == 1
    assert plan_payload["rows"][0]["interactive_refinement_hooks"]
    assert (
        intake_dir / "formalization_gap_planner_target_intake_manifest.json"
    ).exists()
    assert (
        intake_dir / "formalization_gap_planner_target_intake.schema.json"
    ).exists()
    row_schema_path = intake_dir / "formalization_gap_planner_target_intake_row.schema.json"
    assert row_schema_path.exists()
    row_schema = json.loads(row_schema_path.read_text(encoding="utf-8"))
    assert row_schema["$id"] == FORMALIZATION_GAP_PLANNER_TARGET_INTAKE_ROW_SCHEMA_ID
    assert row_schema["$id"] == target_intake_row_json_schema()["$id"]


def test_target_intake_preserves_mixed_route_targets_in_standalone_seed() -> None:
    root = Path("runs/test_formalization_gap_planner_target_intake_mixed_targets")
    input_path = root / "target_request.json"
    intake_dir = root / "target_intake"
    plan_dir = root / "standalone_plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_target_intake",
                "library_snapshot_ref": "portable:probability-snapshots",
                "domain": "distribution-free prediction",
                "targets": [
                    {
                        "target_prover_family": "lean4",
                        "target_id": "lean_rank_bound",
                        "title": "Lean finite-rank route",
                        "theorem_statement": (
                            "Exchangeability implies a finite-rank coverage bound."
                        ),
                        "desired_theorem_shape": "finite-rank coverage bound",
                        "known_proof_sources": ["conformal prediction textbook"],
                        "candidate_primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Probability.exchangeable"
                                ],
                            }
                        ],
                    },
                    {
                        "target_prover_family": "rocq",
                        "target_id": "rocq_rank_bound",
                        "title": "Rocq finite-rank route",
                        "theorem_statement": (
                            "Exchangeability implies a finite-rank coverage bound."
                        ),
                        "desired_theorem_shape": "finite-rank coverage bound",
                        "known_proof_sources": ["conformal prediction textbook"],
                        "candidate_primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": [
                                    "Rocq.Probability.exchangeable"
                                ],
                            }
                        ],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    intake_payload = normalize_formalization_gap_planner_target_intake(
        input_path,
        intake_dir,
    )

    assert intake_payload["all_ok"]
    seed = intake_payload["standalone_seed"]
    assert "target_prover_family" not in seed
    assert [route["target_prover_family"] for route in seed["routes"]] == [
        "lean4",
        "rocq",
    ]

    standalone_seed_path = (
        intake_dir / "formalization_gap_planner_target_intake_standalone_seed.json"
    )
    plan_payload = export_formalization_gap_planner_standalone_plan(
        standalone_seed_path,
        plan_dir,
    )

    assert plan_payload["all_ok"]
    assert plan_payload["target_prover_family"] == "mixed:lean4,rocq"
    assert plan_payload["n_target_prover_families"] == 2
    assert plan_payload["by_target_prover_family"] == {"lean4": 1, "rocq": 1}
    assert [row["target_prover_family"] for row in plan_payload["rows"]] == [
        "lean4",
        "rocq",
    ]

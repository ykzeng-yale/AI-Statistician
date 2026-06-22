from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_library_coverage_map import (
    LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID,
    export_formalization_gap_planner_library_coverage_map,
    library_coverage_map_row_json_schema,
    validate_library_coverage_map_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_library_coverage_map_exports_per_primitive_route_mapping() -> None:
    root = Path("runs/test_formalization_gap_planner_library_coverage_map")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "isabelle",
                "library_snapshot_ref": "isabelle_probability_snapshot",
                "routes": [
                    {
                        "display_name": "distribution_free_rank_bound",
                        "theorem_statement": (
                            "A distribution-free rank bound follows from exchangeability."
                        ),
                        "source_refs": ["conformal_prediction_textbook"],
                        "replan_metadata": {
                            "llm_route_planner_row_id": "llm_route:rank_bound",
                            "llm_route_planner_minimal_delta_plan": {
                                "bridge_lemmas": [
                                    (
                                        "rank_uniformity: prove finite rank "
                                        "uniformity from exchangeability"
                                    )
                                ],
                                "source_port_lemmas": [
                                    (
                                        "coverage_inequality: port the "
                                        "source-backed coverage inequality"
                                    )
                                ],
                            },
                        },
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            },
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "expected_premises": ["exchangeability"],
                            },
                            {
                                "primitive": "coverage_inequality",
                                "coverage_status": "source_port_needed",
                                "source_refs": ["vovk_gammerman_shafer"],
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

    payload = export_formalization_gap_planner_library_coverage_map(
        plan_dir,
        coverage_dir,
    )

    assert payload["all_ok"]
    assert payload["n_plan_rows"] == 1
    assert payload["n_coverage_rows"] == 3
    assert payload["target_prover_family"] == "isabelle"
    assert payload["n_target_prover_families"] == 1
    assert payload["by_target_prover_family"] == {"isabelle": 3}
    assert payload["n_row_schema_valid"] == payload["n_coverage_rows"]
    assert payload["n_row_schema_invalid"] == 0
    assert payload["n_exact_exists"] == 1
    assert payload["n_bridge_needed"] == 1
    assert payload["n_source_port_needed"] == 1
    assert payload["n_unknown_or_unaligned"] == 0
    assert (
        payload["library_coverage_map_row_schema"]["$id"]
        == LIBRARY_COVERAGE_MAP_ROW_SCHEMA_ID
    )
    by_primitive = {row["primitive"]: row for row in payload["rows"]}
    assert by_primitive["exchangeability"]["coverage_bucket"] == "exact_exists"
    assert by_primitive["exchangeability"]["candidate_declarations"]
    assert payload["n_rows_with_candidate_declaration_rows"] == 1
    assert payload["n_candidate_declaration_rows"] == 1
    assert payload["n_rows_with_actionable_work_items"] == 2
    assert payload["n_actionable_work_items"] == 2
    assert "candidate_declaration_rows" in payload[
        "library_coverage_map_row_schema"
    ]["required"]
    assert "actionable_work_items" in payload[
        "library_coverage_map_row_schema"
    ]["required"]
    assert by_primitive["exchangeability"]["candidate_declaration_rows"] == (
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "isabelle",
            "source_field": "candidate_declarations",
        },
    )
    assert by_primitive["rank_uniformity"]["needs_bridge_lemma"]
    assert by_primitive["rank_uniformity"]["actionable_work_items"] == (
        "rank_uniformity: prove finite rank uniformity from exchangeability",
    )
    assert by_primitive["coverage_inequality"]["needs_source_search"]
    assert by_primitive["coverage_inequality"]["actionable_work_items"] == (
        "coverage_inequality: port the source-backed coverage inequality",
    )
    assert "not theorem proof evidence" in by_primitive["exchangeability"][
        "proof_evidence_boundary"
    ]
    report_text = (
        coverage_dir / "formalization_gap_planner_library_coverage_map.md"
    ).read_text(encoding="utf-8")
    assert "Target prover families: 1 by={'isabelle': 3}" in report_text
    assert validate_library_coverage_map_row(
        by_primitive["exchangeability"],
        library_coverage_map_row_json_schema(),
    ) == []
    malformed = dict(by_primitive["exchangeability"])
    malformed.pop("primitive")
    assert "primitive required" in validate_library_coverage_map_row(
        malformed,
        library_coverage_map_row_json_schema(),
    )
    wrong_target = dict(by_primitive["exchangeability"])
    wrong_target["candidate_declaration_rows"] = [
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "candidate_declarations",
        }
    ]
    assert (
        "candidate_declaration_rows[0].target_prover_family must match row target_prover_family"
        in validate_library_coverage_map_row(
            wrong_target,
            library_coverage_map_row_json_schema(),
        )
    )
    assert (
        coverage_dir
        / "formalization_gap_planner_library_coverage_map_manifest.json"
    ).exists()
    assert (
        coverage_dir / "formalization_gap_planner_library_coverage_map.jsonl"
    ).exists()
    assert (
        coverage_dir
        / "formalization_gap_planner_library_coverage_map_row.schema.json"
    ).exists()
    assert (
        coverage_dir / "formalization_gap_planner_library_coverage_map.md"
    ).exists()


def test_library_coverage_map_rejects_missing_alignment() -> None:
    root = Path("runs/test_formalization_gap_planner_library_coverage_map_rejects")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "lean_fixture",
                "routes": [
                    {
                        "display_name": "demo_target",
                        "primitives": [
                            {
                                "primitive": "demo_existing",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Demo.existing"],
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
    manifest["rows"][0]["route_alignment_edges"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = export_formalization_gap_planner_library_coverage_map(plan_dir)

    assert not payload["all_ok"]
    assert payload["n_unknown_or_unaligned"] == 1
    assert payload["n_failed"] == 1
    assert payload["rows"][0]["errors"]


def test_library_coverage_map_requires_action_items_for_accepted_llm_delta() -> None:
    root = Path("runs/test_formalization_gap_planner_library_coverage_map_llm_delta")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "lean_fixture",
                "routes": [
                    {
                        "display_name": "demo_target",
                        "replan_metadata": {
                            "llm_route_planner_acceptance_status": (
                                "ACCEPTED_LLM_ROUTE_PLAN"
                            ),
                            "llm_route_planner_minimal_delta_plan": {
                                "selected_primitives": ["rank_uniformity"]
                            },
                        },
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
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

    payload = export_formalization_gap_planner_library_coverage_map(plan_dir)

    assert not payload["all_ok"]
    assert payload["n_failed"] == 1
    assert (
        "actionable_work_items required for LLM-originated delta coverage row"
        in payload["rows"][0]["errors"]
    )

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_library_coverage_map import (
    export_formalization_gap_planner_library_coverage_map,
)
from ai_statistician.formalization_gap_planner_primitive_action_queue import (
    PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID,
    export_formalization_gap_planner_primitive_action_queue,
    primitive_action_queue_row_json_schema,
    validate_primitive_action_queue_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_primitive_action_queue_exports_per_coverage_row_work_orders() -> None:
    root = Path("runs/test_formalization_gap_planner_primitive_action_queue")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
    action_queue_dir = root / "action_queue"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "component_name": "formalization_gap_planner_standalone_input",
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_probability_snapshot",
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
    coverage_payload = export_formalization_gap_planner_library_coverage_map(
        plan_dir,
        coverage_dir,
    )

    payload = export_formalization_gap_planner_primitive_action_queue(
        coverage_dir,
        action_queue_dir,
    )

    assert payload["all_ok"]
    assert payload["n_coverage_rows"] == coverage_payload["n_coverage_rows"] == 3
    assert payload["n_action_items"] == payload["n_coverage_rows"]
    assert payload["n_ok"] == payload["n_action_items"]
    assert payload["n_failed"] == 0
    assert payload["n_row_schema_valid"] == payload["n_action_items"]
    assert payload["n_row_schema_invalid"] == 0
    assert payload["n_target_prover_replay"] == 1
    assert payload["n_prove_bridge_lemma"] == 1
    assert payload["n_source_port"] == 1
    assert (
        payload["primitive_action_queue_row_schema"]["$id"]
        == PRIMITIVE_ACTION_QUEUE_ROW_SCHEMA_ID
    )
    by_primitive = {row["primitive"]: row for row in payload["rows"]}
    assert by_primitive["exchangeability"]["queue_action_kind"] == "target_prover_replay"
    assert by_primitive["exchangeability"]["owner_agent"] == "target_prover_adapter"
    assert payload["n_with_candidate_declaration_rows"] == 1
    assert payload["n_candidate_declaration_rows"] == 1
    assert payload["n_with_actionable_work_items"] == 2
    assert payload["n_actionable_work_items"] == 2
    assert payload["n_minimal_delta_reuse_ready"] == 1
    assert payload["n_minimal_delta_light_bridge_or_wrapper"] == 1
    assert payload["n_minimal_delta_source_or_new_theory"] == 1
    assert payload["n_minimal_delta_alignment_blocked"] == 0
    assert payload["average_reuse_readiness_score"] == 68
    assert payload["average_evidence_readiness_score"] == 72
    assert "candidate_declaration_rows" in payload[
        "primitive_action_queue_row_schema"
    ]["required"]
    assert "actionable_work_items" in payload[
        "primitive_action_queue_row_schema"
    ]["required"]
    assert "minimal_delta_cost_score" in payload[
        "primitive_action_queue_row_schema"
    ]["required"]
    assert "reuse_readiness_score" in payload[
        "primitive_action_queue_row_schema"
    ]["required"]
    assert "evidence_readiness_score" in payload[
        "primitive_action_queue_row_schema"
    ]["required"]
    assert "priority_rationale" in payload[
        "primitive_action_queue_row_schema"
    ]["required"]
    assert by_primitive["exchangeability"]["candidate_declaration_rows"] == (
        {
            "declaration": "Probability.exchangeable",
            "target_prover_family": "rocq",
            "source_field": "candidate_declarations",
        },
    )
    assert by_primitive["exchangeability"]["minimal_delta_cost_score"] == 0
    assert by_primitive["exchangeability"]["reuse_readiness_score"] == 100
    assert by_primitive["exchangeability"]["evidence_readiness_score"] == 75
    assert (
        "prefer exact current-library reuse before adding declarations"
        in by_primitive["exchangeability"]["priority_rationale"]
    )
    assert by_primitive["rank_uniformity"]["queue_action_kind"] == "prove_bridge_lemma"
    assert by_primitive["rank_uniformity"]["owner_agent"] == "formal_verifier"
    assert by_primitive["rank_uniformity"]["minimal_delta_cost_score"] == 40
    assert by_primitive["rank_uniformity"]["reuse_readiness_score"] == 70
    assert by_primitive["rank_uniformity"]["evidence_readiness_score"] == 75
    assert by_primitive["rank_uniformity"]["actionable_work_items"] == (
        "rank_uniformity: prove finite rank uniformity from exchangeability",
    )
    assert by_primitive["coverage_inequality"]["queue_action_kind"] == "source_port"
    assert by_primitive["coverage_inequality"]["owner_agent"] == "literature_router"
    assert by_primitive["coverage_inequality"]["minimal_delta_cost_score"] == 60
    assert by_primitive["coverage_inequality"]["actionable_work_items"] == (
        "coverage_inequality: port the source-backed coverage inequality",
    )
    assert by_primitive["exchangeability"]["rank"] < by_primitive["rank_uniformity"]["rank"]
    assert "not theorem proof evidence" in by_primitive["exchangeability"][
        "proof_evidence_boundary"
    ]
    assert validate_primitive_action_queue_row(
        by_primitive["exchangeability"],
        primitive_action_queue_row_json_schema(),
    ) == []
    malformed = dict(by_primitive["exchangeability"])
    malformed.pop("queue_action_kind")
    assert "queue_action_kind required" in validate_primitive_action_queue_row(
        malformed,
        primitive_action_queue_row_json_schema(),
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
        in validate_primitive_action_queue_row(
            wrong_target,
            primitive_action_queue_row_json_schema(),
        )
    )
    assert (
        action_queue_dir
        / "formalization_gap_planner_primitive_action_queue_manifest.json"
    ).exists()
    assert (
        action_queue_dir / "formalization_gap_planner_primitive_action_queue.jsonl"
    ).exists()
    assert (
        action_queue_dir
        / "formalization_gap_planner_primitive_action_queue_row.schema.json"
    ).exists()
    assert (
        action_queue_dir / "formalization_gap_planner_primitive_action_queue.md"
    ).exists()


def test_primitive_action_queue_preserves_unknown_alignment_blocker() -> None:
    root = Path("runs/test_formalization_gap_planner_primitive_action_queue_rejects")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    coverage_dir = root / "coverage"
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
    export_formalization_gap_planner_library_coverage_map(plan_dir, coverage_dir)

    payload = export_formalization_gap_planner_primitive_action_queue(coverage_dir)

    assert not payload["all_ok"]
    assert payload["n_action_items"] == 1
    assert payload["n_rerun_library_alignment"] == 1
    assert payload["n_failed"] == 1
    assert payload["n_minimal_delta_alignment_blocked"] == 1
    assert payload["rows"][0]["queue_action_kind"] == "rerun_library_alignment"
    assert payload["rows"][0]["minimal_delta_cost_score"] == 100
    assert "alignment unknown; rerun library search before formalization" in payload[
        "rows"
    ][0]["priority_rationale"]
    assert payload["rows"][0]["errors"]

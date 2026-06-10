from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_local_literature_adapter import (
    export_formalization_gap_planner_local_literature_adapter_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
    refinement_evidence_row_json_schema,
    refinement_tool_response_json_schema,
    validate_refinement_evidence_row,
    validate_refinement_tool_response_row,
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
    assert payload["n_local_response_schema_valid"] == 1
    assert payload["n_local_response_schema_invalid"] == 0
    assert payload["n_merged_response_schema_valid"] == 2
    assert payload["n_merged_response_schema_invalid"] == 0
    assert (
        payload["refinement_tool_response_schema"]["$id"]
        == refinement_tool_response_json_schema()["$id"]
    )
    assert payload["n_source_hits"] == 1
    assert payload["n_source_snippets"] == 1
    assert payload["n_local_literature_responses_with_source_snippets"] == 1
    response = payload["responses"][0]
    assert response["evidence_kind"] == "literature_route_evidence"
    assert response["source_refs"]
    assert response["source_snippets"][0]["source_ref"] == response["source_refs"][0]
    assert "conditional" in response["source_snippets"][0]["matched_terms"]
    assert "conditional" in response["source_snippets"][0]["excerpt"]
    assert response["source_support_status"] == "source_backed_all_target_primitives"
    assert response["supported_target_primitives"] == ("conditional_mean_residual_zero",)
    assert response["unsupported_target_primitives"] == ()
    primitive_support = response["target_primitive_support"][0]
    assert primitive_support["primitive"] == "conditional_mean_residual_zero"
    assert primitive_support["supported"] is True
    assert primitive_support["supporting_source_refs"] == response["source_refs"]
    assert {"conditional", "mean", "residual", "zero"}.issubset(
        set(primitive_support["matched_terms"])
    )
    assert (
        response["source_snippets"][0]["source_support_status"]
        == "source_backed_all_target_primitives"
    )
    assert response["source_snippets"][0]["supported_target_primitives"] == (
        "conditional_mean_residual_zero",
    )
    assert response["source_snippets"][0]["unsupported_target_primitives"] == ()
    assert response["route_evidence_nodes"][0]["kind"] == "source_ref"
    assert "conditional" in response["route_evidence_nodes"][0]["matched_terms"]
    assert response["route_evidence_nodes"][0]["source_support_status"] == (
        "source_backed_all_target_primitives"
    )
    assert not response["route_revision_recommended"]
    assert payload["n_fully_source_supported_literature_responses"] == 1
    assert payload["n_partially_source_supported_literature_responses"] == 0
    assert payload["n_unsupported_literature_responses"] == 0

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    assert evidence_payload["n_response_schema_valid"] == evidence_payload["n_responses"] == 2
    assert evidence_payload["n_response_schema_invalid"] == 0
    assert evidence_payload["n_evidence_row_schema_valid"] == evidence_payload["n_evidence_rows"]
    assert evidence_payload["n_evidence_row_schema_invalid"] == 0
    assert evidence_payload["n_contract_ok"] == 2
    assert evidence_payload["n_literature_evidence"] == 1
    assert evidence_payload["n_source_snippets"] == 1
    assert evidence_payload["n_literature_rows_with_source_snippets"] == 1
    assert evidence_payload["n_awaiting_tool_response"] == 0
    assert (
        evidence_payload["refinement_tool_response_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1"
    )
    assert (
        evidence_payload["refinement_evidence_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-evidence-row:1"
    )
    evidence_schema = refinement_evidence_row_json_schema()
    assert "source_snippets" in refinement_tool_response_json_schema()["properties"]
    assert "source_snippets" in evidence_schema["properties"]
    assert "source_snippets" not in evidence_schema["required"]
    assert "formal_declaration_hits" in evidence_schema["required"]
    assert "lean_declaration_hits" not in evidence_schema["required"]
    assert "revised_formal_realization_dag_nodes" in evidence_schema["required"]
    assert "revised_lean_realization_dag_nodes" not in evidence_schema["required"]
    assert evidence_payload["rows"][0]["source_snippets"][0]["source_ref"] == (
        response["source_refs"][0]
    )
    assert evidence_payload["rows"][0]["formal_declaration_hits"] == (
        evidence_payload["rows"][0]["lean_declaration_hits"]
    )
    legacy_free_evidence_row = dict(evidence_payload["rows"][0])
    legacy_free_evidence_row.pop("revised_lean_realization_dag_nodes", None)
    legacy_free_evidence_row.pop("lean_declaration_hits", None)
    assert validate_refinement_evidence_row(
        legacy_free_evidence_row,
        evidence_schema,
    ) == ()
    missing_generic_evidence_row = dict(evidence_payload["rows"][0])
    missing_generic_evidence_row.pop("revised_formal_realization_dag_nodes", None)
    assert "revised_formal_realization_dag_nodes required" in validate_refinement_evidence_row(
        missing_generic_evidence_row,
        evidence_schema,
    )
    bad_evidence_row = dict(evidence_payload["rows"][0])
    bad_evidence_row.pop("acceptance_status")
    assert "acceptance_status required" in validate_refinement_evidence_row(
        bad_evidence_row,
        refinement_evidence_row_json_schema(),
    )
    bad_response = dict(response)
    bad_response.pop("tool_name")
    assert "tool_name required" in validate_refinement_tool_response_row(
        bad_response,
        refinement_tool_response_json_schema(),
    )
    assert (
        evidence_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()
    assert (
        adapter_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()
    assert (
        evidence_dir / "formalization_gap_planner_refinement_evidence_row.schema.json"
    ).exists()


def test_local_literature_adapter_marks_partial_target_support() -> None:
    root = Path("runs/test_formalization_gap_planner_local_literature_adapter_partial")
    queue_dir = root / "queue"
    corpus_dir = root / "papers"
    adapter_dir = root / "adapter"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    corpus_dir.mkdir(parents=True, exist_ok=True)
    (corpus_dir / "rank_uniformity.md").write_text(
        "\n".join(
            [
                "# Rank uniformity note",
                "",
                "Exchangeability implies rank uniformity for the calibration rank.",
                "This note does not discuss measurability side conditions.",
            ]
        ),
        encoding="utf-8",
    )
    (queue_dir / "formalization_gap_planner_refinement_queue_manifest.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "refinement_item_id": "refinement:partial-literature",
                        "goal_plan_id": "goal:partial",
                        "route_id": "route:partial",
                        "display_name": "rank route with a missing side condition",
                        "hook_kind": "literature_discovery",
                        "refinement_stage": "literature",
                        "owner_agent": "literature",
                        "target_primitives": [
                            "rank_uniformity",
                            "conditional_measurability",
                        ],
                        "queries": [
                            "rank uniformity conditional measurability exchangeability"
                        ],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_local_literature_adapter_responses(
        queue_dir,
        adapter_dir,
        literature_roots=(corpus_dir,),
        k=1,
    )

    assert payload["all_ok"]
    assert payload["n_fully_source_supported_literature_responses"] == 0
    assert payload["n_partially_source_supported_literature_responses"] == 1
    assert payload["n_unsupported_literature_responses"] == 0
    response = payload["responses"][0]
    assert response["source_support_status"] == (
        "source_backed_partial_target_primitives"
    )
    assert response["supported_target_primitives"] == ("rank_uniformity",)
    assert response["unsupported_target_primitives"] == (
        "conditional_measurability",
    )
    assert response["route_revision_recommended"]
    assert response["route_revision_reasons"] == (
        "conditional_measurability not directly supported by local literature hits",
    )
    support_by_primitive = {
        row["primitive"]: row for row in response["target_primitive_support"]
    }
    assert support_by_primitive["rank_uniformity"]["supported"] is True
    assert support_by_primitive["conditional_measurability"]["supported"] is False
    assert (
        response["source_snippets"][0]["source_support_status"]
        == "source_backed_partial_target_primitives"
    )
    assert response["source_snippets"][0]["supported_target_primitives"] == (
        "rank_uniformity",
    )
    assert response["source_snippets"][0]["unsupported_target_primitives"] == (
        "conditional_measurability",
    )

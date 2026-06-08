from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formal_source_index import (
    FormalSourceRoot,
    build_formal_source_index,
)
from ai_statistician.formalization_gap_planner_local_formal_source_adapter import (
    export_formalization_gap_planner_local_formal_source_adapter_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)


def test_local_formal_source_adapter_emits_formal_grounding_responses() -> None:
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
            "refinement_item_id": "refinement:formal",
            "goal_plan_id": "goal:test",
            "route_id": "route:test",
            "display_name": display_name,
            "hook_kind": "formal_library_grounding",
            "refinement_stage": "formal_library_coverage_mapping",
            "owner_agent": "formal_retrieval",
            "target_primitives": ["conditional_mean_residual_zero"],
            "queries": ["conditional mean residual zero formal theorem"],
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
    assert payload["n_formal_library_grounding_rows"] == 1
    assert payload["n_lean_library_grounding_rows"] == 0
    assert payload["n_local_formal_source_responses"] == 1
    assert payload["n_merged_responses"] == 2
    assert payload["n_local_response_schema_valid"] == 1
    assert payload["n_local_response_schema_invalid"] == 0
    assert payload["n_merged_response_schema_valid"] == 2
    assert payload["n_merged_response_schema_invalid"] == 0
    assert (
        payload["refinement_tool_response_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1"
    )
    assert payload["n_hits"] >= 1
    response = payload["responses"][0]
    assert response["target_prover_family"] == "lean4"
    assert response["evidence_kind"] == "formal_library_grounding"
    assert response["coverage_updates"]["conditional_mean_residual_zero"] == "exact_exists"
    assert response["formal_declaration_hits"] == response["lean_declaration_hits"]
    assert response["formal_declaration_hits"][0]["target_prover_family"] == "lean4"
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
    assert evidence_payload["n_evidence_row_schema_valid"] == evidence_payload["n_evidence_rows"]
    assert evidence_payload["n_evidence_row_schema_invalid"] == 0
    assert (
        evidence_dir / "formalization_gap_planner_refinement_evidence_row.schema.json"
    ).exists()
    assert (
        adapter_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()


def test_local_formal_source_adapter_keeps_non_lean_hits_generic() -> None:
    root = Path("runs/test_formalization_gap_planner_local_formal_source_adapter_rocq")
    queue_dir = root / "queue"
    source_dir = root / "rocq_src"
    adapter_dir = root / "adapter"
    evidence_dir = root / "evidence"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "Rank.v").write_text(
        "\n".join(
            [
                "From Coq Require Import Init.Logic.",
                "Module RocqProbability.",
                "Theorem rank_uniformity : True.",
                "Proof. exact I. Qed.",
                "End RocqProbability.",
            ]
        ),
        encoding="utf-8",
    )
    roots = (FormalSourceRoot("rocq_fixture", str(source_dir), "rocq_library"),)
    declarations = build_formal_source_index(roots=roots)
    assert [decl.name for decl in declarations] == ["RocqProbability.rank_uniformity"]
    assert declarations[0].source_type == "rocq_library"
    queue_rows = [
        {
            "refinement_item_id": "refinement:rocq-formal",
            "goal_plan_id": "goal:rocq",
            "route_id": "route:rocq",
            "display_name": "rocq rank route",
            "hook_kind": "formal_library_grounding",
            "refinement_stage": "formal_library_coverage_mapping",
            "owner_agent": "formal_retrieval",
            "target_prover_family": "rocq",
            "target_primitives": ["rank_uniformity"],
            "queries": ["rank uniformity Rocq theorem"],
        },
    ]
    (queue_dir / "formalization_gap_planner_refinement_queue_manifest.json").write_text(
        json.dumps({"rows": queue_rows}, indent=2),
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_local_formal_source_adapter_responses(
        queue_dir,
        adapter_dir,
        formal_source_roots=roots,
        k=3,
    )

    assert payload["all_ok"]
    assert payload["n_formal_library_grounding_rows"] == 1
    assert payload["n_lean_library_grounding_rows"] == 0
    response = payload["responses"][0]
    assert response["target_prover_family"] == "rocq"
    assert response["coverage_updates"]["rank_uniformity"] == "exact_exists"
    assert response["formal_declaration_hits"]
    assert response["lean_declaration_hits"] == []
    hit = response["formal_declaration_hits"][0]
    assert hit["declaration"] == "RocqProbability.rank_uniformity"
    assert hit["source_type"] == "rocq_library"
    assert hit["target_prover_family"] == "rocq"

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    row = evidence_payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert row["response_contract_ok"]
    assert row["formal_declaration_hits"]
    assert row["lean_declaration_hits"] == ()

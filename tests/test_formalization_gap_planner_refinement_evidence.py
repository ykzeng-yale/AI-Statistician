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
    assert proposal["response_contract_ok"] is False
    assert proposal["acceptance_status"] == "REJECTED_REFINEMENT_EVIDENCE_CONTRACT"
    assert proposal["ok"] is False
    assert proposal["errors"] == row["errors"]
    assert tuple(proposal["target_primitives"]) == (
        "rank_uniformity",
        "spectral_gap",
    )


def test_refinement_evidence_preserves_queue_level_quality_controls() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_refinement_evidence_queue_controls"
    )
    queue_dir = root / "queue"
    evidence_dir = root / "evidence"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_row = {
        "refinement_item_id": "refinement:literature-controls",
        "goal_plan_id": "goal:test",
        "route_id": "route:test",
        "display_name": "demo:rank_uniformity",
        "hook_kind": "literature_discovery",
        "refinement_stage": "source_grounding",
        "owner_agent": "research_librarian",
        "target_primitives": ["rank_uniformity"],
        "resource_request_bindings": [],
        "quality_controls": {
            "resource_contract_ids": ["paperqa:literature_evidence"],
            "required_quality_signals": ["source_snippets"],
            "quality_gates": ["response_schema_valid"],
            "response_validation_signals": ["source_refs_present"],
            "stop_conditions": ["source evidence accepted or search exhausted"],
        },
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

    payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
    )

    assert payload["all_ok"]
    assert payload["n_awaiting_tool_response"] == 1
    assert payload["n_rows_with_quality_controls"] == 1
    row = payload["rows"][0]
    assert row["acceptance_status"] == "AWAITING_REFINEMENT_TOOL_RESPONSE"
    assert row["quality_controls"] == {
        "quality_gates": ("response_schema_valid",),
        "required_quality_signals": ("source_snippets",),
        "resource_contract_ids": ("paperqa:literature_evidence",),
        "response_validation_signals": ("source_refs_present",),
        "stop_conditions": ("source evidence accepted or search exhausted",),
    }


def test_refinement_evidence_accepts_explicit_formal_search_miss() -> None:
    root = Path("runs/test_formalization_gap_planner_refinement_evidence_search_miss")
    queue_dir = root / "queue"
    evidence_dir = root / "evidence"
    response_jsonl = root / "responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_row = {
        "refinement_item_id": "refinement:formal",
        "goal_plan_id": "goal:test",
        "route_id": "route:test",
        "display_name": "rocq:rank_uniformity",
        "hook_kind": "formal_library_grounding",
        "refinement_stage": "formal_library_coverage_mapping",
        "owner_agent": "formal_retrieval",
        "target_prover_family": "rocq",
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
                "refinement_item_id": "refinement:formal",
                "route_id": "route:test",
                "display_name": "rocq:rank_uniformity",
                "evidence_kind": "formal_library_grounding",
                "tool_name": "fixture_formal_source_adapter",
                "target_prover_family": "rocq",
                "formal_declaration_hits": [],
                "coverage_updates": {"rank_uniformity": "source_discovery_needed"},
                "route_revision_recommended": True,
                "route_revision_reasons": [
                    "rank_uniformity had no target-compatible local declaration hits",
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

    assert payload["all_ok"]
    assert payload["n_contract_ok"] == 1
    assert payload["n_rejected"] == 0
    row = payload["rows"][0]
    assert row["response_contract_ok"]
    assert row["formal_declaration_hits"] == ()
    assert row["coverage_updates"] == {"rank_uniformity": "source_discovery_needed"}
    assert row["route_revision_recommended"]


def test_refinement_evidence_rejects_source_type_implied_target_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_refinement_evidence_source_type_mismatch"
    )
    queue_dir = root / "queue"
    evidence_dir = root / "evidence"
    response_jsonl = root / "responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_row = {
        "refinement_item_id": "refinement:formal",
        "goal_plan_id": "goal:test",
        "route_id": "route:test",
        "display_name": "rocq:rank_uniformity",
        "hook_kind": "formal_library_grounding",
        "refinement_stage": "formal_library_coverage_mapping",
        "owner_agent": "formal_retrieval",
        "target_prover_family": "rocq",
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
                "refinement_item_id": "refinement:formal",
                "route_id": "route:test",
                "display_name": "rocq:rank_uniformity",
                "evidence_kind": "formal_library_grounding",
                "tool_name": "fixture_formal_source_adapter",
                "target_prover_family": "rocq",
                "formal_declaration_hits": [
                    {
                        "declaration": "Mathlib.Probability.RankUniformityBridge",
                        "source_type": "lean_library",
                    }
                ],
                "coverage_updates": {"rank_uniformity": "exact_exists"},
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
    assert payload["n_declaration_hit_target_mismatch_rows"] == 1
    assert payload["n_declaration_hit_target_mismatches"] == 1
    row = payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert not row["response_contract_ok"]
    assert row["formal_declaration_hits"] == (
        {
            "declaration": "Mathlib.Probability.RankUniformityBridge",
            "source_type": "lean_library",
        },
    )
    assert (
        "formal_declaration_hits[0].source_type implies lean4 "
        "but row target_prover_family is rocq"
    ) in row["errors"]


def test_refinement_evidence_rejects_response_target_prover_mismatch() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_refinement_evidence_target_mismatch"
    )
    queue_dir = root / "queue"
    evidence_dir = root / "evidence"
    response_jsonl = root / "responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_row = {
        "refinement_item_id": "refinement:formal",
        "goal_plan_id": "goal:test",
        "route_id": "route:test",
        "display_name": "rocq:rank_uniformity",
        "hook_kind": "formal_library_grounding",
        "refinement_stage": "formal_library_coverage_mapping",
        "owner_agent": "formal_retrieval",
        "target_prover_family": "rocq",
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
                "refinement_item_id": "refinement:formal",
                "route_id": "route:test",
                "display_name": "rocq:rank_uniformity",
                "evidence_kind": "formal_library_grounding",
                "tool_name": "fixture_formal_source_adapter",
                "target_prover_family": "lean4",
                "formal_declaration_hits": [
                    {
                        "declaration": "Mathlib.Probability.RankUniformityBridge",
                        "target_prover_family": "lean4",
                    }
                ],
                "coverage_updates": {"rank_uniformity": "exact_exists"},
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
    assert payload["n_target_prover_family_mismatch_rows"] == 1
    assert payload["n_declaration_hit_target_mismatch_rows"] == 1
    row = payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert "target_prover_family mismatch: response=lean4 queue=rocq" in row[
        "errors"
    ]
    assert (
        "formal_declaration_hits[0].target_prover_family must match "
        "row target_prover_family"
    ) in row["errors"]


def test_refinement_evidence_accepts_cross_prover_adapter_feedback() -> None:
    root = Path("runs/test_formalization_gap_planner_refinement_evidence_cross_prover")
    queue_dir = root / "queue"
    evidence_dir = root / "evidence"
    response_jsonl = root / "responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_row = {
        "refinement_item_id": "refinement:proof",
        "goal_plan_id": "goal:test",
        "route_id": "route:test",
        "display_name": "lean-source-to-rocq-target",
        "hook_kind": "proof_state_feedback",
        "refinement_stage": "leaf_prover_attempts",
        "owner_agent": "formal_verifier",
        "target_prover_family": "lean4",
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
                "display_name": "lean-source-to-rocq-target",
                "evidence_kind": "prover_feedback",
                "tool_name": "target_prover_adapter_feedback_adapter",
                "target_prover_family": "rocq",
                "prover_diagnostics": [
                    "rocq:rank_uniformity mapping_status=needs_library_grounding"
                ],
                "residual_goals": [
                    "rocq:rank_uniformity: awaiting prover adapter mapping"
                ],
                "attempt_status": "awaiting_prover_adapter_mapping",
                "prover_attempt_class": "target_prover_mapping_awaiting",
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

    assert payload["all_ok"]
    assert payload["n_rejected"] == 0
    assert payload["n_target_prover_family_mismatch_rows"] == 0
    assert payload["n_cross_prover_feedback_retargeted_rows"] == 1
    row = payload["rows"][0]
    assert row["response_contract_ok"]
    assert row["source_target_prover_family"] == "lean4"
    assert row["target_prover_family"] == "rocq"
    assert row["errors"] == ()


def test_refinement_evidence_rejects_empty_exact_exists_formal_grounding() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_refinement_evidence_empty_exact_exists"
    )
    queue_dir = root / "queue"
    evidence_dir = root / "evidence"
    response_jsonl = root / "responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_row = {
        "refinement_item_id": "refinement:formal",
        "goal_plan_id": "goal:test",
        "route_id": "route:test",
        "display_name": "rocq:rank_uniformity",
        "hook_kind": "formal_library_grounding",
        "refinement_stage": "formal_library_coverage_mapping",
        "owner_agent": "formal_retrieval",
        "target_prover_family": "rocq",
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
                "refinement_item_id": "refinement:formal",
                "route_id": "route:test",
                "display_name": "rocq:rank_uniformity",
                "evidence_kind": "formal_library_grounding",
                "tool_name": "fixture_formal_source_adapter",
                "target_prover_family": "rocq",
                "formal_declaration_hits": [],
                "coverage_updates": {"rank_uniformity": "exact_exists"},
                "route_revision_recommended": True,
                "route_revision_reasons": ["rank_uniformity allegedly exists"],
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
    row = payload["rows"][0]
    assert not row["response_contract_ok"]
    assert "formal_declaration_hits missing for formal_library_grounding" in row[
        "errors"
    ]

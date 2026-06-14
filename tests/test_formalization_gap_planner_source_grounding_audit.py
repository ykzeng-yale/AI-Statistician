from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_source_grounding_audit import (
    audit_formalization_gap_planner_source_grounding,
    source_grounding_row_json_schema,
    validate_source_grounding_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_source_grounding_audit_accepts_source_backed_standalone_route() -> None:
    root = Path("runs/test_formalization_gap_planner_source_grounding_audit")
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
                "library_snapshot_ref": "mathlib4:source-grounding",
                "routes": [
                    {
                        "display_name": "demo_source_grounded_route",
                        "theorem_statement": "A source-backed route.",
                        "source_refs": ["paper:demo#theorem1"],
                        "informal_proof_steps": ["reduce to rank lemma"],
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "source_refs": ["paper:demo#lemma2"],
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

    payload = audit_formalization_gap_planner_source_grounding(plan_dir, audit_dir)

    assert payload["all_ok"]
    assert payload["n_plan_rows"] == 1
    assert payload["n_failed"] == 0
    assert payload["n_source_grounding_rows"] >= 2
    assert payload["n_source_backed"] >= 2
    assert payload["n_unaccounted"] == 0
    assert payload["n_row_schema_valid"] == payload["n_source_grounding_rows"]
    assert payload["n_row_schema_invalid"] == 0
    schema = source_grounding_row_json_schema()
    assert payload["source_grounding_row_schema"]["$id"] == schema["$id"]
    invalid_row = dict(payload["rows"][0])
    invalid_row.pop("grounding_status")
    assert validate_source_grounding_row(invalid_row, schema)
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (
        audit_dir / "formalization_gap_planner_source_grounding_audit_manifest.json"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_source_grounding_audit.jsonl"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_source_grounding_row.schema.json"
    ).exists()


def test_source_grounding_audit_rejects_unaccounted_informal_node() -> None:
    root = Path("runs/test_formalization_gap_planner_source_grounding_audit_rejects")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "mathlib4:source-grounding",
                "routes": [
                    {
                        "display_name": "demo_unaccounted_source",
                        "primitives": [
                            {
                                "primitive": "missing_source_node",
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
    row = manifest["rows"][0]
    row["interactive_refinement_hooks"] = [
        hook
        for hook in row["interactive_refinement_hooks"]
        if hook.get("hook_kind") != "literature_discovery"
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_source_grounding(plan_dir)

    assert not payload["all_ok"]
    assert payload["n_unaccounted"] > 0
    assert payload["n_failed"] == payload["n_unaccounted"]
    assert payload["n_row_schema_valid"] == payload["n_source_grounding_rows"]
    assert payload["n_row_schema_invalid"] == 0


def test_source_grounding_audit_accounts_for_source_backed_residuals() -> None:
    root = Path("runs/test_formalization_gap_planner_source_grounding_residual")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    audit_dir = root / "audit"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "mathlib4:source-grounding-residual",
                "routes": [
                    {
                        "route_id": "route:rank",
                        "display_name": "demo_source_grounded_residual",
                        "source_refs": ["paper:demo#theorem1"],
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "source_refs": ["paper:demo#rank"],
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
    evidence_row = {
        "refinement_evidence_id": "evidence:rank-residual",
        "refinement_item_id": "refinement:rank-residual",
        "route_id": "route:rank",
        "display_name": "demo_source_grounded_residual",
        "hook_kind": "proof_state_feedback",
        "source_refs": ["paper:demo#exchangeability-side-condition"],
        "residual_goals": [
            "rank_uniformity: missing exchangeability side condition"
        ],
        "prover_attempt_status": "local_lean_failed",
        "prover_diagnostic_signature": "prover_diagnostic_signature:fixture",
        "route_revision_reasons": [
            "proof-state residual exposed hidden exchangeability side condition"
        ],
    }
    (
        evidence_dir
        / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(json.dumps({"rows": [evidence_row]}, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_source_grounding(
        plan_dir,
        audit_dir,
        formalization_gap_planner_refinement_evidence_dir=evidence_dir,
    )

    assert payload["all_ok"]
    assert payload["n_refinement_evidence_rows"] == 1
    assert payload["n_residual_grounding_rows"] == 1
    assert payload["n_residual_goals"] == 1
    assert payload["n_residual_primitives"] == 1
    assert payload["n_residual_rows_with_source_refs"] == 1
    assert payload["n_residual_source_backed"] == 1
    assert payload["n_residual_unaccounted"] == 0
    residual_rows = [
        row
        for row in payload["rows"]
        if row["node_source"] == "refinement_evidence_prover_feedback"
    ]
    assert residual_rows[0]["residual_primitives"] == ("rank_uniformity",)
    assert residual_rows[0]["grounding_status"] == "source_backed"
    assert (
        audit_dir / "formalization_gap_planner_source_grounding_audit_manifest.json"
    ).exists()


def test_source_grounding_audit_rejects_unsourced_residual_without_literature_hook() -> None:
    root = Path("runs/test_formalization_gap_planner_source_grounding_residual_rejects")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "mathlib4:source-grounding-residual-rejects",
                "routes": [
                    {
                        "route_id": "route:rank",
                        "display_name": "demo_unsourced_residual",
                        "source_refs": ["paper:demo#theorem1"],
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "source_refs": ["paper:demo#rank"],
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
    evidence_row = {
        "refinement_evidence_id": "evidence:rank-residual",
        "refinement_item_id": "refinement:rank-residual",
        "route_id": "route:rank",
        "display_name": "demo_unsourced_residual",
        "hook_kind": "proof_state_feedback",
        "residual_goals": ["rank_uniformity: missing side condition"],
        "prover_attempt_status": "local_lean_failed",
        "prover_diagnostic_signature": "prover_diagnostic_signature:fixture",
        "route_revision_reasons": [
            "proof-state residual exposed hidden side condition"
        ],
    }
    (
        evidence_dir
        / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(json.dumps({"rows": [evidence_row]}, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_source_grounding(
        plan_dir,
        formalization_gap_planner_refinement_evidence_dir=evidence_dir,
    )

    assert not payload["all_ok"]
    assert payload["n_residual_grounding_rows"] == 1
    assert payload["n_residual_unaccounted"] == 1
    assert payload["n_residual_source_backed"] == 0
    assert payload["n_failed"] == 1
    residual_rows = [
        row
        for row in payload["rows"]
        if row["node_source"] == "refinement_evidence_prover_feedback"
    ]
    assert residual_rows[0]["grounding_status"] == "unaccounted"
    assert residual_rows[0]["errors"] == (
        "no source refs, formal boundary, or literature hook",
    )


def test_source_grounding_audit_accounts_for_context_source_backed_residual() -> None:
    root = Path("runs/test_formalization_gap_planner_source_grounding_context_source")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "mathlib4:source-grounding-context-source",
                "routes": [
                    {
                        "route_id": "route:rank",
                        "display_name": "demo_context_sourced_residual",
                        "source_refs": ["paper:demo#theorem1"],
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "source_refs": ["paper:demo#rank"],
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
    evidence_row = {
        "refinement_evidence_id": "evidence:rank-residual",
        "refinement_item_id": "refinement:rank-residual",
        "route_id": "route:rank",
        "display_name": "demo_context_sourced_residual",
        "hook_kind": "proof_state_feedback",
        "residual_goals": ["rank_uniformity: missing side condition"],
        "prover_attempt_status": "local_lean_failed",
        "prover_diagnostic_signature": "prover_diagnostic_signature:fixture",
        "residual_goal_context": {
            "source_kind": "proof_state_feedback",
            "residual_goal": "rank_uniformity: missing side condition",
            "source_refs": ["paper:demo#context-side-condition"],
            "source_snippets": [
                {
                    "source_ref": "paper:demo#context-side-condition",
                    "text": "The rank lemma requires the side condition.",
                }
            ],
        },
    }
    (
        evidence_dir
        / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(json.dumps({"rows": [evidence_row]}, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_source_grounding(
        plan_dir,
        formalization_gap_planner_refinement_evidence_dir=evidence_dir,
    )

    assert payload["all_ok"]
    assert payload["n_residual_source_backed"] == 1
    assert payload["n_residual_unaccounted"] == 0
    residual_rows = [
        row
        for row in payload["rows"]
        if row["node_source"] == "refinement_evidence_prover_feedback"
    ]
    assert residual_rows[0]["grounding_status"] == "source_backed"
    assert "paper:demo#context-side-condition" in residual_rows[0]["source_refs"]


def test_source_grounding_audit_accounts_for_context_formal_boundary() -> None:
    root = Path("runs/test_formalization_gap_planner_source_grounding_context_boundary")
    input_json = root / "standalone_input.json"
    plan_dir = root / "plan"
    evidence_dir = root / "evidence"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    input_json.write_text(
        json.dumps(
            {
                "library_snapshot_ref": "mathlib4:source-grounding-context-boundary",
                "routes": [
                    {
                        "route_id": "route:rank",
                        "display_name": "demo_context_boundary_residual",
                        "source_refs": ["paper:demo#theorem1"],
                        "primitives": [
                            {
                                "primitive": "rank_uniformity",
                                "coverage_status": "bridge_needed",
                                "source_refs": ["paper:demo#rank"],
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
    evidence_row = {
        "refinement_evidence_id": "evidence:rank-residual",
        "refinement_item_id": "refinement:rank-residual",
        "route_id": "route:rank",
        "display_name": "demo_context_boundary_residual",
        "hook_kind": "proof_state_feedback",
        "residual_goals": ["rank_uniformity: missing unavailable prover lemma"],
        "prover_attempt_status": "local_lean_failed",
        "prover_diagnostic_signature": "prover_diagnostic_signature:fixture",
        "residual_goal_context": {
            "source_kind": "proof_state_feedback",
            "residual_goal": "rank_uniformity: missing unavailable prover lemma",
            "formal_gap_boundary": (
                "Formal boundary: the residual records a prover-library gap for "
                "rank_uniformity until a source-backed bridge lemma is added."
            ),
        },
    }
    (
        evidence_dir
        / "formalization_gap_planner_refinement_evidence_manifest.json"
    ).write_text(json.dumps({"rows": [evidence_row]}, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_source_grounding(
        plan_dir,
        formalization_gap_planner_refinement_evidence_dir=evidence_dir,
    )

    assert payload["all_ok"]
    assert payload["n_residual_formal_boundary_declared"] == 1
    assert payload["n_residual_unaccounted"] == 0
    residual_rows = [
        row
        for row in payload["rows"]
        if row["node_source"] == "refinement_evidence_prover_feedback"
    ]
    assert residual_rows[0]["grounding_status"] == "formal_boundary_declared"

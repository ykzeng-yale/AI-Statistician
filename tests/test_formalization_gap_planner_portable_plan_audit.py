from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_portable_plan_audit import (
    audit_formalization_gap_planner_portable_plan,
    portable_plan_audit_row_json_schema,
    validate_portable_plan_audit_row,
)
from ai_statistician.formalization_gap_planner_standalone import (
    export_formalization_gap_planner_standalone_plan,
)


def test_portable_plan_audit_accepts_standalone_plan() -> None:
    root = Path("runs/test_formalization_gap_planner_portable_plan_audit")
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
                "target_prover_family": "agda",
                "library_snapshot_ref": "agda_probability_fixture",
                "background_primitives": ["unused_large_theory"],
                "routes": [
                    {
                        "display_name": "demo_distribution_free_bound",
                        "theorem_statement": "A distribution-free bound follows from exchangeability.",
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Exchangeable"],
                            },
                            {
                                "primitive": "rank_bound",
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

    payload = audit_formalization_gap_planner_portable_plan(plan_dir, audit_dir)

    assert payload["all_ok"]
    assert payload["n_contract_errors"] == 0
    assert payload["n_row_schema_valid"] == payload["n_checks"]
    assert payload["n_row_schema_invalid"] == 0
    assert (
        payload["portable_plan_audit_row_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-portable-plan-audit-row:1"
    )
    assert validate_portable_plan_audit_row(
        payload["checks"][0],
        portable_plan_audit_row_json_schema(),
    ) == []
    malformed_check = dict(payload["checks"][0])
    malformed_check.pop("check_id")
    assert "check_id required" in validate_portable_plan_audit_row(
        malformed_check,
        portable_plan_audit_row_json_schema(),
    )
    assert payload["n_plan_rows"] == 1
    assert payload["n_rows_with_two_dag"] == 1
    assert payload["n_rows_with_alignment_edges"] == 1
    assert payload["n_route_alignment_edges"] >= payload["n_plan_rows"]
    assert payload["n_route_alignment_edge_schema_valid"] == payload["n_route_alignment_edges"]
    assert payload["n_route_alignment_edge_schema_invalid"] == 0
    assert (
        payload["route_alignment_edge_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-route-alignment-edge:1"
    )
    assert payload["n_rows_with_work_packets"] == 1
    assert payload["n_rows_without_kernel_claims"] == 1
    assert "not theorem proof evidence" in payload["proof_evidence_boundary"]
    assert (
        audit_dir / "formalization_gap_planner_portable_plan_audit_manifest.json"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_portable_plan_audit.jsonl"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_portable_plan_audit_row.schema.json"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_portable_plan_audit.md"
    ).exists()
    assert (
        audit_dir / "formalization_gap_planner_route_alignment_edge.schema.json"
    ).exists()


def test_portable_plan_audit_accepts_generic_formal_realization_without_legacy_lean_alias() -> None:
    root = Path("runs/test_formalization_gap_planner_portable_plan_audit_generic_formal")
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
                "target_prover_family": "isabelle",
                "library_snapshot_ref": "isabelle_probability_fixture",
                "routes": [
                    {
                        "display_name": "demo_rank_bound",
                        "theorem_statement": "A rank bound follows from exchangeability.",
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.exchangeable"],
                            },
                            {
                                "primitive": "rank_bound",
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
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["rows"][0]
    assert row["formal_realization_dag_nodes"]
    row.pop("lean_realization_dag_nodes", None)
    row.pop("lean_realization_dag_edges", None)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_portable_plan(plan_dir, audit_dir)

    assert payload["all_ok"]
    assert payload["n_rows_with_two_dag"] == 1
    assert payload["n_rows_with_alignment_edges"] == 1


def test_portable_plan_audit_rejects_non_lean_legacy_lean_realization_alias() -> None:
    root = Path("runs/test_formalization_gap_planner_portable_plan_audit_rejects_lean_alias")
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
                "target_prover_family": "rocq",
                "library_snapshot_ref": "rocq_probability_fixture",
                "routes": [
                    {
                        "display_name": "demo_rank_bound",
                        "theorem_statement": "A rank bound follows from exchangeability.",
                        "primitives": [
                            {
                                "primitive": "exchangeability",
                                "coverage_status": "exact_exists",
                                "candidate_declarations": ["Probability.Exchangeable"],
                            },
                            {
                                "primitive": "rank_bound",
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
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["rows"][0]
    row["lean_realization_dag_nodes"] = list(row["formal_realization_dag_nodes"])
    row["lean_realization_dag_edges"] = list(row["formal_realization_dag_edges"])
    row["formal_realization_dag_nodes"] = []
    row["formal_realization_dag_edges"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_portable_plan(plan_dir, audit_dir)

    assert not payload["all_ok"]
    assert payload["n_contract_errors"] == 0
    assert payload["n_rows_with_two_dag"] == 0
    assert payload["n_rows_with_alignment_edges"] == 0
    failed = [row for row in payload["checks"] if not row["ok"]]
    assert any(row["check_name"].endswith("two_dag") for row in failed)
    assert any(
        row["check_name"].endswith("route_alignment_edges")
        and "formal-realization DAG" in row["observed"]
        for row in failed
    )


def test_portable_plan_audit_rejects_kernel_claim_in_plan_layer() -> None:
    root = Path("runs/test_formalization_gap_planner_portable_plan_audit_rejects")
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
                                "primitive": "demo_primitive",
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
    manifest["rows"][0]["portable_work_packets"][0]["kernel_verified"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_portable_plan(plan_dir)

    assert not payload["all_ok"]
    assert payload["n_failed"] > 0
    assert payload["n_row_schema_valid"] == payload["n_checks"]
    assert payload["n_row_schema_invalid"] == 0
    failed = [row for row in payload["checks"] if not row["ok"]]
    assert any(row["check_name"].endswith("no_kernel_claims") for row in failed)


def test_portable_plan_audit_rejects_missing_route_alignment_edges() -> None:
    root = Path("runs/test_formalization_gap_planner_portable_plan_audit_alignment_rejects")
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
                            },
                            {
                                "primitive": "demo_bridge",
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
    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rows"][0]["route_alignment_edges"] = [
        edge
        for edge in manifest["rows"][0]["route_alignment_edges"]
        if edge["primitive"] != "demo_bridge"
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_portable_plan(plan_dir)

    assert not payload["all_ok"]
    assert payload["n_rows_with_alignment_edges"] == 0
    failed = [row for row in payload["checks"] if not row["ok"]]
    assert any(
        row["check_name"].endswith("route_alignment_edges")
        and "demo_bridge" in row["observed"]
        for row in failed
    )

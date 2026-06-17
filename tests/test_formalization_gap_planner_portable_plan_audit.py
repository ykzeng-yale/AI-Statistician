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


def test_portable_plan_audit_checks_route_option_cost_graph_scope() -> None:
    root = Path("runs/test_formalization_gap_planner_portable_plan_audit_route_options")
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
                "library_snapshot_ref": "mathlib4_route_option_fixture",
                "routes": [
                    {
                        "display_name": "route_option_scope",
                        "theorem_statement": "A selected bridge avoids a broader baseline.",
                        "selected_primitives": ["selected_bridge"],
                        "minimal_delta_and_or_cost_graph": {
                            "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                            "selected_route_option_id": "route_option:selected",
                            "route_options": [
                                {
                                    "route_option_id": "route_option:selected",
                                    "selected": True,
                                    "selected_primitives": ["selected_bridge"],
                                    "route_cost": 4,
                                },
                                {
                                    "route_option_id": "route_option:baseline",
                                    "selected": False,
                                    "selected_primitives": [
                                        "selected_bridge",
                                        "comparison_boundary",
                                    ],
                                    "route_cost": 24,
                                },
                            ],
                            "and_edges": [
                                {
                                    "route_option_id": "route_option:selected",
                                    "requires": ["selected_bridge"],
                                },
                                {
                                    "route_option_id": "route_option:baseline",
                                    "requires": [
                                        "selected_bridge",
                                        "comparison_boundary",
                                    ],
                                },
                            ],
                            "or_nodes": [
                                {
                                    "node_id": "or:route_option_scope",
                                    "choices": [
                                        "route_option:selected",
                                        "route_option:baseline",
                                    ],
                                    "selection_rationale": (
                                        "selected bridge is cheaper than the broader baseline"
                                    ),
                                }
                            ],
                        },
                        "primitives": [
                            {
                                "primitive": "selected_bridge",
                                "coverage_status": "bridge_needed",
                            },
                            {
                                "primitive": "comparison_boundary",
                                "coverage_status": "unknown",
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
    assert payload["n_rows_with_route_option_cost_graph"] == 1
    assert payload["n_rows_with_valid_route_option_cost_graph"] == 1
    route_graph_checks = [
        row
        for row in payload["checks"]
        if row["category"] == "route_option_cost_graph"
    ]
    assert route_graph_checks
    assert all(row["ok"] for row in route_graph_checks)

    manifest_path = plan_dir / "goal_conditioned_minimal_formalization_plan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["rows"][0]
    leaked_node = dict(row["minimal_additional_formalization_nodes"][0])
    leaked_node["primitive"] = "comparison_boundary"
    leaked_node["label"] = "comparison_boundary"
    row["minimal_additional_formalization_nodes"].append(leaked_node)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    rejected = audit_formalization_gap_planner_portable_plan(plan_dir, audit_dir)

    assert not rejected["all_ok"]
    failed = [row for row in rejected["checks"] if not row["ok"]]
    assert any(
        row["check_name"].endswith("route_option_cost_graph")
        and "comparison_only_primitives overlap selected work nodes" in row["observed"]
        for row in failed
    )


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
    refinement_hook_checks = [
        check
        for check in payload["checks"]
        if check["check_name"].startswith("row_")
        and check["check_name"].endswith("refinement_hooks")
    ]
    assert refinement_hook_checks
    assert all(check["ok"] for check in refinement_hook_checks)
    assert all(
        "target-prover library grounding" in check["expected"]
        for check in refinement_hook_checks
    )
    assert all(
        "Lean grounding" not in check["expected"] for check in refinement_hook_checks
    )


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


def test_portable_plan_audit_rejects_non_lean_contaminating_lean_realization_alias() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_portable_plan_audit_rejects_extra_lean_alias"
    )
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
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_portable_plan(plan_dir, audit_dir)

    assert not payload["all_ok"]
    assert payload["n_contract_errors"] == 0
    assert payload["n_rows_with_two_dag"] == 1
    assert payload["n_rows_with_alignment_edges"] == 1
    assert payload["n_rows_without_non_lean_legacy_realization_aliases"] == 0
    failed = [row for row in payload["checks"] if not row["ok"]]
    assert any(
        row["check_name"].endswith("non_lean_legacy_realization_aliases")
        and "lean_realization_dag_nodes is a Lean-only legacy alias" in row["observed"]
        for row in failed
    )


def test_portable_plan_audit_rejects_cross_prover_declaration_evidence_targets() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_portable_plan_audit_rejects_bad_declaration_targets"
    )
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
    row["formal_realization_dag_nodes"][0]["candidate_declaration_rows"] = [
        {
            "declaration": "Mathlib.Probability.exchangeable",
            "target_prover_family": "lean4",
            "source_field": "candidate_declaration_rows",
        }
    ]
    row["standalone_input_trace"]["formal_declaration_hits"] = [
        {
            "declaration": "Mathlib.Probability.exchangeable",
            "target_prover_family": "lean4",
        }
    ]
    row["standalone_input_trace"]["lean_declaration_hits"] = [
        {"declaration": "Mathlib.Probability.exchangeable"}
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload = audit_formalization_gap_planner_portable_plan(plan_dir, audit_dir)

    assert not payload["all_ok"]
    assert payload["n_contract_errors"] == 0
    assert payload["n_rows_with_two_dag"] == 1
    assert payload["n_rows_with_alignment_edges"] == 1
    assert payload["n_rows_with_declaration_evidence_target_consistency"] == 0
    failed = [row for row in payload["checks"] if not row["ok"]]
    assert any(
        row["check_name"].endswith("declaration_evidence_target_consistency")
        and "target_prover_family lean4 does not match row target_prover_family rocq"
        in row["observed"]
        and "lean_declaration_hits is a Lean-only legacy alias" in row["observed"]
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

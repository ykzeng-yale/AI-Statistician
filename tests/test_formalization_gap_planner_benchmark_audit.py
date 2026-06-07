from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_benchmark import (
    benchmark_route_row_json_schema,
    export_formalization_gap_planner_benchmark,
    validate_benchmark_route_row,
)
from ai_statistician.formalization_gap_planner_benchmark_audit import (
    audit_formalization_gap_planner_benchmark,
)


def test_benchmark_audit_validates_route_truth_quality_and_splits() -> None:
    root = Path("runs/test_formalization_gap_planner_benchmark_audit")
    benchmark_dir = root / "benchmark"
    audit_dir = root / "audit"
    reject_dir = root / "reject"
    shutil.rmtree(root, ignore_errors=True)

    benchmark_payload = export_formalization_gap_planner_benchmark(benchmark_dir)
    audit_payload = audit_formalization_gap_planner_benchmark(
        benchmark_dir,
        audit_dir,
    )

    assert benchmark_payload["all_ok"]
    assert (
        benchmark_payload["n_route_row_schema_valid"]
        == benchmark_payload["n_routes"]
    )
    assert benchmark_payload["n_route_row_schema_invalid"] == 0
    assert benchmark_payload["n_routes_with_expected_residuals"] == benchmark_payload["n_routes"]
    assert benchmark_payload["n_expected_residual_primitives"] >= benchmark_payload["n_routes"]
    assert (
        benchmark_payload["benchmark_route_row_schema"]["$id"]
        == benchmark_route_row_json_schema()["$id"]
    )
    assert not validate_benchmark_route_row(benchmark_payload["routes"][0])
    broken_route_row = dict(benchmark_payload["routes"][0])
    broken_route_row.pop("proof_evidence_boundary")
    assert "proof_evidence_boundary required" in validate_benchmark_route_row(
        broken_route_row
    )
    assert audit_payload["all_ok"]
    assert audit_payload["n_failed"] == 0
    assert audit_payload["n_routes"] >= 5
    assert audit_payload["n_route_row_schema_valid"] == audit_payload["n_routes"]
    assert audit_payload["n_route_row_schema_invalid"] == 0
    assert audit_payload["n_theorem_families"] >= 3
    assert audit_payload["n_evaluation_splits"] >= 2
    assert audit_payload["n_routes_with_source_refs"] == audit_payload["n_routes"]
    assert audit_payload["n_routes_with_expected_residuals"] == audit_payload["n_routes"]
    assert audit_payload["n_expected_residual_primitives"] >= audit_payload["n_routes"]
    assert "heldout_eval" in audit_payload["by_evaluation_split"]
    assert any(
        check["check_name"] == "benchmark_core_coverage_statuses" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert "not theorem proof evidence" in audit_payload["proof_evidence_boundary"]
    assert (
        audit_dir / "formalization_gap_planner_benchmark_audit_manifest.json"
    ).exists()
    assert (audit_dir / "formalization_gap_planner_benchmark_audit.jsonl").exists()
    assert (
        benchmark_dir / "formalization_gap_planner_benchmark_route.schema.json"
    ).exists()
    assert any(
        check["check_name"] == "route_0_schema_valid" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "route_0_expected_residuals_are_required"
        and check["ok"]
        for check in audit_payload["checks"]
    )

    manifest_path = benchmark_dir / "formalization_gap_planner_benchmark_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["routes"][0]["source_refs"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    rejected = audit_formalization_gap_planner_benchmark(benchmark_dir, reject_dir)

    assert not rejected["all_ok"]
    failed = {check["check_name"] for check in rejected["checks"] if not check["ok"]}
    assert "benchmark_source_ref_floor" in failed
    assert "route_0_source_refs" in failed

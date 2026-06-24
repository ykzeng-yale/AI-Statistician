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
    assert benchmark_payload["target_prover_family"] == "lean4"
    assert benchmark_payload["n_target_prover_families"] == 1
    assert benchmark_payload["n_routes_with_target_prover_family"] == benchmark_payload["n_routes"]
    assert benchmark_payload["by_target_prover_family"] == {
        "lean4": benchmark_payload["n_routes"]
    }
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
    assert audit_payload["n_target_prover_families"] == 1
    assert audit_payload["n_routes_with_target_prover_family"] == audit_payload["n_routes"]
    assert audit_payload["by_target_prover_family"] == {
        "lean4": audit_payload["n_routes"]
    }
    assert audit_payload["n_evaluation_splits"] >= 2
    assert audit_payload["n_routes_with_source_refs"] == audit_payload["n_routes"]
    assert audit_payload["n_routes_with_expected_residuals"] == audit_payload["n_routes"]
    assert audit_payload["n_expected_residual_primitives"] >= audit_payload["n_routes"]
    assert "heldout_eval" in audit_payload["by_evaluation_split"]
    assert any(
        check["check_name"] == "benchmark_core_coverage_statuses" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "benchmark_target_prover_summary" and check["ok"]
        for check in audit_payload["checks"]
    )
    assert any(
        check["check_name"] == "benchmark_target_prover_family_present" and check["ok"]
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


def test_benchmark_requires_witness_for_kernel_verified_route_truth() -> None:
    root = Path("runs/test_formalization_gap_planner_benchmark_kernel_witness")
    truth_json = root / "ground_truth.json"
    benchmark_dir = root / "benchmark"
    audit_dir = root / "audit"
    reject_dir = root / "reject"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)

    def route(index: int, *, kernel_verified: bool = False) -> dict[str, object]:
        payload: dict[str, object] = {
            "display_name": f"kernel_witness_fixture:{index}",
            "theorem_family": f"fixture_family_{index}",
            "target_prover_family": "lean4_adapter_with_portable_gap_schema",
            "route_truth_status": (
                "kernel_verified_route_truth"
                if kernel_verified
                else "expert_curated_route_truth"
            ),
            "required_primitives": [
                f"existing_{index}",
                f"wrapper_{index}",
                f"bridge_{index}",
            ],
            "actual_existing_reuse_primitives": [f"existing_{index}"],
            "actual_delta_primitives": [f"wrapper_{index}", f"bridge_{index}"],
            "expected_residual_primitives": [f"bridge_{index}"],
            "expected_residual_goals": [f"bridge_{index}: replay fixture side condition"],
            "coverage_by_primitive": {
                f"existing_{index}": "exact_exists",
                f"wrapper_{index}": "wrapper_needed",
                f"bridge_{index}": "bridge_needed",
            },
            "source_refs": [f"fixture_source_{index}_a", f"fixture_source_{index}_b"],
            "kernel_verified": kernel_verified,
            "notes": "Small benchmark fixture.",
        }
        if kernel_verified:
            payload["kernel_verification_witnesses"] = [
                {
                    "target_prover_family": "lean4",
                    "verification_status": "kernel_verified",
                    "artifact_refs": ["Proofs/KernelWitnessFixture.lean"],
                    "declaration_names": ["KernelWitnessFixture.demo"],
                    "proof_hash": "sha256:fixture-kernel-proof",
                    "checker": "lake build",
                    "no_sorry_or_admit": True,
                }
            ]
        return payload

    truth_payload = {
        "schema_version": 1,
        "benchmark_id": "kernel_witness_fixture",
        "benchmark_name": "Kernel witness fixture",
        "proof_evidence_boundary": (
            "This file is benchmark route-truth evidence for planner evaluation, "
            "not theorem proof evidence."
        ),
        "routes": [route(0, kernel_verified=True), route(1), route(2)],
    }
    truth_json.write_text(json.dumps(truth_payload, indent=2), encoding="utf-8")

    benchmark_payload = export_formalization_gap_planner_benchmark(
        benchmark_dir,
        ground_truth_path=truth_json,
    )
    audit_payload = audit_formalization_gap_planner_benchmark(
        benchmark_dir,
        audit_dir,
    )

    assert benchmark_payload["all_ok"]
    assert benchmark_payload["target_prover_family"] == "lean4"
    assert benchmark_payload["by_target_prover_family"] == {"lean4": 3}
    assert benchmark_payload["n_kernel_verified_routes"] == 1
    assert benchmark_payload["n_kernel_verification_witnesses"] == 1
    assert benchmark_payload["n_kernel_verified_routes_with_witnesses"] == 1
    assert benchmark_payload["n_kernel_verified_routes_missing_witnesses"] == 0
    assert (
        "kernel_verification_witnesses"
        in benchmark_route_row_json_schema()["required"]
    )
    verified_route = benchmark_payload["routes"][0]
    assert verified_route["kernel_verification_witnesses"][0]["proof_hash"] == (
        "sha256:fixture-kernel-proof"
    )
    assert not validate_benchmark_route_row(verified_route)
    assert audit_payload["all_ok"]
    assert audit_payload["by_target_prover_family"] == {"lean4": 3}
    assert audit_payload["n_target_prover_families"] == 1
    assert audit_payload["n_kernel_verified_routes"] == 1
    assert audit_payload["n_kernel_verification_witnesses"] == 1
    assert audit_payload["n_kernel_verified_routes_missing_witnesses"] == 0
    assert audit_payload["derived_split_rows"][0][
        "n_kernel_verification_witnesses"
    ] == 1
    assert any(
        check["check_name"] == "route_0_kernel_verification_witness"
        and check["ok"]
        for check in audit_payload["checks"]
    )

    rejected_truth = json.loads(truth_json.read_text(encoding="utf-8"))
    rejected_truth["routes"][0].pop("kernel_verification_witnesses")
    truth_json.write_text(json.dumps(rejected_truth, indent=2), encoding="utf-8")
    rejected_benchmark = export_formalization_gap_planner_benchmark(
        root / "benchmark_rejected",
        ground_truth_path=truth_json,
    )
    rejected_audit = audit_formalization_gap_planner_benchmark(
        root / "benchmark_rejected",
        reject_dir,
    )

    assert not rejected_benchmark["all_ok"]
    assert rejected_benchmark["n_kernel_verified_routes_missing_witnesses"] == 1
    assert not rejected_audit["all_ok"]
    failed = {check["check_name"] for check in rejected_audit["checks"] if not check["ok"]}
    assert "route_0_ok" in failed
    assert "route_0_kernel_verification_witness" in failed
    assert "benchmark_all_ok" in failed
    assert "kernel_verified route truth requires kernel_verification_witnesses" in (
        rejected_benchmark["routes"][0]["errors"]
    )

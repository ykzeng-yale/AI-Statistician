from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.source_theorem_semantic_primitive_proofengineer_bridge import (
    run_source_theorem_semantic_primitive_proofengineer_bridge,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_source_semantic_bridge_records_registered_support_without_proof_claim(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_semantic_primitive_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            {
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "source_theorem_semantic_primitive_work_order:order",
                "question_id": "conformal_prediction_coverage",
                "semantic_primitive_id": "order_statistic_quantile_semantics",
                "semantic_primitive_gap": "formalize order statistic quantile semantics",
                "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
            }
        ],
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_registered_candidate_obligations"] == 1
    assert manifest["registered_candidate_obligation_ids"] == [
        "split_conformal_good_rank_set_inclusion_bridge"
    ]
    assert manifest["runtime_learning_ready"] is False
    assert manifest["proof_evidence_status"] == (
        "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
    )
    check = manifest["checks"][0]
    assert check["registered_support_level"] == "registered_partial_semantic_bridge"
    assert check["kernel_verified"] is False
    assert "not proof evidence unless" in manifest["boundary"]


def test_source_semantic_bridge_resolves_probability_measure_support(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_semantic_primitive_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            {
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "source_theorem_semantic_primitive_work_order:prob",
                "question_id": "conformal_prediction_coverage",
                "semantic_primitive_id": "probability_measure_semantics",
                "semantic_primitive_gap": (
                    "replace MeasureProbability placeholder with probability measure semantics"
                ),
                "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
            }
        ],
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["registered_candidate_obligation_ids"] == ["prob_measure_univ"]
    check = manifest["checks"][0]
    assert check["semantic_primitive_id"] == "probability_measure_semantics"
    assert check["registered_candidate_obligation_ids"] == ["prob_measure_univ"]
    assert check["proof_evidence_status"] == (
        "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
    )


def test_source_semantic_bridge_reports_only_relevant_verified_support(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_semantic_primitive_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            {
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "source_theorem_semantic_primitive_work_order:prob",
                "question_id": "conformal_prediction_coverage",
                "semantic_primitive_id": "probability_measure_semantics",
                "semantic_primitive_gap": (
                    "replace MeasureProbability placeholder with probability measure semantics"
                ),
                "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
            }
        ],
    )
    proof_manifest = tmp_path / "proof_audit_manifest.json"
    proof_manifest.write_text(
        json.dumps(
            {
                "checks": [
                    {
                        "obligation_id": "prob_measure_univ",
                        "kernel_verified": True,
                    },
                    {
                        "obligation_id": (
                            "split_conformal_good_rank_set_inclusion_bridge"
                        ),
                        "kernel_verified": True,
                    },
                ],
                "verification_strength": "local_lean_kernel_batch",
                "verifier": "local.lake_env_lean",
            }
        ),
        encoding="utf-8",
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        question_id="conformal_prediction_coverage",
        proof_audit_manifest=proof_manifest,
    )

    assert manifest["registered_candidate_obligation_ids"] == ["prob_measure_univ"]
    assert manifest["n_kernel_verified_registered_candidate_obligations"] == 1
    assert manifest["kernel_verified_registered_candidate_obligation_ids"] == [
        "prob_measure_univ"
    ]
    assert manifest["checks"][0]["kernel_verified_registered_obligation_ids"] == [
        "prob_measure_univ"
    ]


def test_source_semantic_bridge_exports_learning_from_kernel_proof_audit(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_semantic_primitive_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            {
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "source_theorem_semantic_primitive_work_order:rank",
                "question_id": "conformal_prediction_coverage",
                "semantic_primitive_id": "rank_uniformity_semantics",
                "semantic_primitive_gap": "formalize rank-uniformity semantic bridge",
                "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
            }
        ],
    )
    proof_manifest = tmp_path / "proof_audit_manifest.json"
    proof_manifest.write_text(
        json.dumps(
            {
                "checks": [
                    {
                        "obligation_id": (
                            "split_conformal_bad_rank_budget_from_uniform_rank_bound"
                        ),
                        "kernel_verified": True,
                    }
                ],
                "verification_strength": "local_lean_kernel_batch",
                "verifier": "local.lake_env_lean",
            }
        ),
        encoding="utf-8",
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        question_id="conformal_prediction_coverage",
        proof_audit_manifest=proof_manifest,
    )
    learning_path = Path(str(manifest["runtime_learning_rows_jsonl"]))
    learning_rows = [
        json.loads(line)
        for line in learning_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert manifest["runtime_learning_ready"] is True
    assert manifest["proof_evidence_status"] == (
        "KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT_PRESENT"
    )
    assert manifest["kernel_verified_registered_candidate_obligation_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]
    assert manifest[
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == ["split_conformal_bad_rank_budget_from_uniform_rank_bound"]
    assert learning_rows[0][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == ["split_conformal_bad_rank_budget_from_uniform_rank_bound"]
    assert learning_rows[0]["input_summary"][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == ["split_conformal_bad_rank_budget_from_uniform_rank_bound"]
    assert learning_rows[0]["kernel_verified_source_theorem_semantic_primitive_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]
    assert learning_rows[0]["kernel_verified_proof_obligation_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]
    assert "Do not treat them as full source theorem proof" in learning_rows[0][
        "target_behavior"
    ]

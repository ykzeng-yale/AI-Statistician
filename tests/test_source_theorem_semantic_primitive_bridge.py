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
                "placeholder_symbol": "orderStat",
                "target_theorem_name": "split_conformal_coverage",
                "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
                "source_theorem_target_known": True,
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "split_conformal_coverage",
                    "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
                },
                "semantic_alignment_constraints": [
                    "preserve marginal coverage target"
                ],
                "candidate_artifact_path": "runs/proof_body_attempt.lean",
                "formal_environment_typeclass_blockers": ["HSub ℕ ℝ ENNReal"],
                "proof_body_attempted": True,
                "proof_body_attempt_success": False,
                "proof_body_attempt_summaries": [
                    "1:simpa:returncode=1:compiled=False"
                ],
                "proof_body_goal_excerpt": [
                    "⊢ P {ω | s (Fin.last n₂) ω ≤ q_hat ω} ≥ ENNReal.ofReal (1 - α)"
                ],
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
    assert check["placeholder_symbol"] == "orderStat"
    assert check["source_theorem_target_known"] is True
    assert check["source_theorem_target_provenance"]["target_lean_declaration"] == (
        "split_conformal_coverage"
    )
    assert check["semantic_alignment_constraints"] == [
        "preserve marginal coverage target"
    ]
    assert check["formal_environment_typeclass_blockers"] == ["HSub ℕ ℝ ENNReal"]
    assert check["proof_body_attempted"] is True
    assert check["proof_body_attempt_success"] is False
    assert check["proof_body_attempt_summaries"] == [
        "1:simpa:returncode=1:compiled=False"
    ]
    assert "ENNReal.ofReal" in check["proof_body_goal_excerpt"][0]
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
                "placeholder_symbol": "Exchangeable",
                "target_theorem_name": "split_conformal_coverage",
                "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
                "source_theorem_target_known": True,
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "split_conformal_coverage",
                    "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
                },
                "formal_environment_typeclass_blockers": ["HSub ℕ ℝ ENNReal"],
                "proof_body_attempted": True,
                "proof_body_attempt_success": False,
                "proof_body_goal_excerpt": [
                    "⊢ P {ω | s (Fin.last n₂) ω ≤ q_hat ω} ≥ ENNReal.ofReal (1 - α)"
                ],
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
    check_context = learning_rows[0]["input_summary"]["semantic_primitive_checks"][0]
    assert check_context["placeholder_symbol"] == "Exchangeable"
    assert check_context["source_theorem_target_known"] is True
    assert check_context["source_theorem_target_provenance"][
        "source_theorem_goal_id"
    ] == "split_conformal_finite_sample_coverage"
    assert check_context["formal_environment_typeclass_blockers"] == [
        "HSub ℕ ℝ ENNReal"
    ]
    assert check_context["proof_body_attempted"] is True
    assert "ENNReal.ofReal" in check_context["proof_body_goal_excerpt"][0]
    assert learning_rows[0]["kernel_verified_source_theorem_semantic_primitive_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]
    assert learning_rows[0]["kernel_verified_proof_obligation_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]
    assert "Do not treat them as full source theorem proof" in learning_rows[0][
        "target_behavior"
    ]


def test_source_semantic_bridge_materializes_queue_from_proof_body_executor_feedback(
    tmp_path: Path,
) -> None:
    executor_dir = tmp_path / "proof_body_executor"
    learning_dir = executor_dir / "runtime_learning_export"
    learning_dir.mkdir(parents=True)
    _write_jsonl(
        learning_dir / "runtime_learning_rows.jsonl",
        [
            {
                "learning_task": "exact_source_theorem_proof_body_execution_feedback",
                "execution_result_id": (
                    "exact_source_theorem_proof_body_execution_result:1"
                ),
                "execution_queue_id": (
                    "exact_source_theorem_proof_body_execution_queue:1"
                ),
                "target_theorem_name": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "input_summary": {
                    "candidate_artifact_path": "runs/proof_body_attempt.lean",
                    "failure_classification": (
                        "formal_environment_placeholder_primitives"
                    ),
                    "formal_environment_placeholder_symbols": [
                        "Exchangeable",
                        "orderStat",
                    ],
                    "formal_environment_typeclass_blockers": [
                        "HSub ℕ ℝ ENNReal"
                    ],
                    "proof_body_attempted": True,
                    "proof_body_attempt_success": False,
                    "proof_body_attempt_summaries": [
                        "1:simpa:returncode=1:compiled=False"
                    ],
                    "candidate_live_proof_state_request": {
                        "proof_body_goal_excerpt": [
                            "⊢ P {ω | s (Fin.last n₂) ω ≤ q_hat ω} ≥ "
                            "ENNReal.ofReal (1 - α)"
                        ]
                    },
                    "source_theorem_target_known": True,
                    "source_theorem_target_provenance": {
                        "source_theorem_target_known": True,
                        "target_lean_declaration": "split_conformal_coverage",
                    },
                },
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
                    },
                    {
                        "obligation_id": (
                            "split_conformal_good_rank_set_inclusion_bridge"
                        ),
                        "kernel_verified": True,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        proof_body_executor_dir=executor_dir,
        question_id="conformal_prediction_coverage",
        proof_audit_manifest=proof_manifest,
    )

    queue_path = Path(str(manifest["source_queue_jsonl"]))
    queue_rows = [
        json.loads(line)
        for line in queue_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_symbol = {row["placeholder_symbol"]: row for row in queue_rows}
    assert set(by_symbol) == {"Exchangeable", "orderStat"}
    assert by_symbol["Exchangeable"]["semantic_primitive_id"] == (
        "exchangeability_to_uniform_rank_semantics"
    )
    assert by_symbol["orderStat"]["semantic_primitive_id"] == (
        "order_statistic_quantile_semantics"
    )
    assert by_symbol["Exchangeable"]["source_theorem_target_known"] is True
    assert by_symbol["orderStat"]["source_theorem_target_provenance"][
        "target_lean_declaration"
    ] == "split_conformal_coverage"
    assert "ENNReal.ofReal" in by_symbol["orderStat"]["proof_body_goal_excerpt"][0]
    assert manifest["n_work_orders"] == 2
    assert manifest["n_kernel_verified_registered_candidate_obligations"] == 2
    assert manifest["runtime_learning_ready"] is True

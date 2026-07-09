from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.source_theorem_semantic_primitive_proofengineer_bridge import (
    inferred_exact_goal_shape_obligation_ids,
    inferred_exact_goal_shape_obligation_ids_from_feedback,
    placeholder_symbols_from_semantic_alignment_feedback,
    placeholder_symbols_for_registered_support_ids,
    run_source_theorem_semantic_primitive_proofengineer_bridge,
    semantic_gap_for_exact_goal_shape_obligation,
    semantic_gap_for_placeholder_symbol,
    semantic_primitive_for_placeholder_symbol,
    semantic_primitive_id_for_gap,
    theorem_closure_reduction_strategy_for_goal,
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
    assert manifest["semantic_support_policy"]["policy_id"] == (
        "split_conformal_registered_semantic_support_v1"
    )
    assert manifest["semantic_support_policy"]["scope"] == (
        "task_family:split_conformal_finite_sample_coverage"
    )
    assert manifest["semantic_support_policy"]["n_primitive_support_routes"] >= 1
    assert (
        manifest["semantic_support_policy"]["n_placeholder_symbol_support_routes"]
        >= 1
    )
    assert (
        manifest["semantic_support_policy"]["n_placeholder_symbol_text_signal_routes"]
        >= 1
    )
    assert (
        manifest["semantic_support_policy"]["n_theorem_closure_reduction_goal_routes"]
        >= 1
    )
    assert (
        manifest["semantic_support_policy"][
            "n_exact_goal_shape_obligation_inference_rules"
        ]
        >= 1
    )
    assert (
        manifest["semantic_support_policy"][
            "n_exact_goal_shape_obligation_feedback_rules"
        ]
        >= 1
    )
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


def test_semantic_placeholder_text_signals_are_policy_driven() -> None:
    assert placeholder_symbols_from_semantic_alignment_feedback(
        semantic_alignment_blockers=[
            "Candidate ignores rank k in the order-statistic argument.",
            "The proof must define covered from the exact source coverage event using hC.",
            "Needs exchangeability before the rank lemma applies.",
        ],
    ) == ("Exchangeable", "orderStat", "covered")

    assert placeholder_symbols_from_semantic_alignment_feedback(
        semantic_alignment_constraints=[
            "Use the quantile/tie policy from the executor feedback.",
            "Permutation invariance gives the uniform rank step.",
        ],
        include_executor_feedback_signals=True,
    ) == ("Exchangeable", "orderStat")

    assert placeholder_symbols_from_semantic_alignment_feedback(
        semantic_alignment_blockers=["semantic prose mentions quantile only"],
        explicit_placeholder_symbols=["ExternalSymbol"],
        failure_classification="formal_environment_placeholder_primitives",
        include_executor_feedback_signals=True,
    ) == ("ExternalSymbol",)


def test_registered_support_reverse_placeholder_lookup_is_policy_driven() -> None:
    assert placeholder_symbols_for_registered_support_ids(
        [
            "split_conformal_good_rank_set_inclusion_bridge",
            "split_conformal_bad_rank_budget_from_uniform_rank_bound",
            "prob_measure_univ",
            "unknown_support",
            "split_conformal_good_rank_set_inclusion_bridge",
        ]
    ) == ("orderStat", "Exchangeable", "MeasureProbability")


def test_theorem_closure_reduction_strategy_is_policy_driven() -> None:
    assert theorem_closure_reduction_strategy_for_goal(
        goal_id="split_conformal_finite_sample_coverage",
        verified_bridge_ids=[
            "split_conformal_good_rank_coverage_bridge",
            "split_conformal_bad_rank_reduction_bridge",
        ],
    ) == {
        "proof_obligation_id": "split_conformal_good_rank_coverage_bridge",
        "source_theorem_name": "splitConformalCoverage_of_goodRankCoverage",
        "closure_theorem_name": (
            "splitConformalFiniteSampleCoverage_reductionClosure"
        ),
        "reduction_description": "good-rank-containment-to-coverage",
    }

    assert theorem_closure_reduction_strategy_for_goal(
        goal_id="split_conformal_finite_sample_coverage",
        verified_bridge_ids=["split_conformal_bad_rank_reduction_bridge"],
    )["reduction_description"] == "bad-rank-budget-to-coverage"

    assert theorem_closure_reduction_strategy_for_goal(
        goal_id="unregistered_goal",
        verified_bridge_ids=["split_conformal_good_rank_coverage_bridge"],
    ) == {}


def test_semantic_primitive_gap_text_and_ids_are_policy_driven() -> None:
    primitive_id, gap = semantic_primitive_for_placeholder_symbol(
        "Exchangeable",
        target_theorem_name="split_conformal_coverage",
    )

    assert primitive_id == "exchangeability_to_uniform_rank_semantics"
    assert "Exchangeable := True" in gap
    assert "finite-rank/uniformity bridge" in gap
    assert "`split_conformal_coverage`" in gap

    assert semantic_gap_for_placeholder_symbol(
        "orderStat",
        target_theorem_name="split_conformal_coverage",
    ) == (
        "Replace placeholder `orderStat` with reviewed finite-sample "
        "order-statistic/quantile semantics for `split_conformal_coverage`."
    )
    assert semantic_gap_for_exact_goal_shape_obligation(
        "coverage_event_identification_from_hC",
        target_theorem_name="split_conformal_coverage",
    ) == (
        "Use the exact coverage-set hypothesis hC to identify the source theorem "
        "event with the covered event used by bridge lemmas for "
        "`split_conformal_coverage`."
    )
    assert semantic_primitive_id_for_gap(
        "formalize probability measure semantics",
        "source_theorem_semantic_primitives",
    ) == "probability_measure_semantics"
    assert semantic_primitive_id_for_gap(
        "formalize exchangeability rank uniformity semantics",
        "source_theorem_semantic_primitives",
    ) == "exchangeability_to_uniform_rank_semantics"


def test_exact_goal_shape_obligation_inference_is_policy_driven() -> None:
    assert inferred_exact_goal_shape_obligation_ids(
        failure_classification="proof_body_verified_adapter_context_insufficient",
    ) == (
        "source_to_bridge_adapter_goal_shape_mismatch",
        "conjunctive_source_theorem_split",
        "real_probability_lower_bound_from_ennreal_adapter",
        "upper_coverage_bound_component",
        "exchangeability_rank_uniformity_instantiation",
        "order_statistic_quantile_rank_instantiation",
        "coverage_event_identification_from_hC",
    )
    assert inferred_exact_goal_shape_obligation_ids(
        trigger="EXACT_SOURCE_PROOF_BODY_VERIFIED_ADAPTER_CONTEXT_INSUFFICIENT",
    ) == (
        "source_to_bridge_adapter_goal_shape_mismatch",
        "conjunctive_source_theorem_split",
        "real_probability_lower_bound_from_ennreal_adapter",
        "upper_coverage_bound_component",
        "exchangeability_rank_uniformity_instantiation",
        "order_statistic_quantile_rank_instantiation",
        "coverage_event_identification_from_hC",
    )
    assert inferred_exact_goal_shape_obligation_ids(
        failure_classification=(
            "proof_body_reduction_closure_adapter_instantiation_missing"
        ),
    ) == ("source_to_bridge_adapter_goal_shape_mismatch",)
    assert inferred_exact_goal_shape_obligation_ids(
        failure_classification="unregistered_failure_classification",
    ) == ()


def test_exact_goal_shape_obligation_feedback_rules_are_policy_driven() -> None:
    goal_text = "\n".join(
        [
            "hexch : Exchangeable P s",
            "hq : q_hat = fun ω => orderStat s k ω",
            "hC : covered = {ω | score ω ≤ q_hat ω}",
            "⊢ 1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧",
            "    P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ≤ 1 - alpha + 1 / ↑(n2 + 1)",
        ]
    )

    assert inferred_exact_goal_shape_obligation_ids_from_feedback(
        failure_classification="proof_body_verified_adapter_context_insufficient",
        goal_text=goal_text,
    ) == (
        "source_to_bridge_adapter_goal_shape_mismatch",
        "conjunctive_source_theorem_split",
        "real_probability_lower_bound_from_ennreal_adapter",
        "upper_coverage_bound_component",
        "exchangeability_rank_uniformity_instantiation",
        "order_statistic_quantile_rank_instantiation",
        "coverage_event_identification_from_hC",
    )


def test_source_to_bridge_premise_semantic_gap_exports_repair_feedback(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_semantic_primitive_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            {
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": (
                    "source_theorem_semantic_primitive_work_order:hGoodCovered"
                ),
                "question_id": "conformal_prediction_coverage",
                "semantic_primitive_id": (
                    "source_to_bridge_premise_semantic_gap:"
                    "split_conformal_coverage:hGoodCovered"
                ),
                "semantic_primitive_gap": (
                    "Derive source-to-bridge premise `hGoodCovered` from the "
                    "source theorem assumptions before retrying exact proof."
                ),
                "semantic_primitive_gap_kind": (
                    "source_to_bridge_premise_semantic_gap"
                ),
                "placeholder_symbol": "hGoodCovered",
                "target_theorem_name": "split_conformal_coverage",
                "premise_name": "hGoodCovered",
                "premise_target_status": "ADAPTER_PREMISE_TARGET_EXTRACTED",
                "premise_target_matched_binder": "hGoodCovered",
                "premise_target_type": "{ω | rank ω ∈ BadRanks}ᶜ ⊆ covered",
                "premise_derivation_gap_kind": (
                    "concrete_premise_target_lacks_nonvacuous_derivation_candidate"
                ),
                "premise_derivation_gap_summary": (
                    "The adapter premise target is known, but the bridge only "
                    "materialized a non-evidence skeleton."
                ),
                "premise_semantic_dependency_status": (
                    "SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_DEPENDENCIES_REQUIRED"
                ),
                "premise_semantic_dependency_requirements": [
                    "define covered from the exact source coverage event using hC",
                    "prove good-rank containment",
                ],
                "exact_source_theorem_binders": [
                    {
                        "name": "hexch",
                        "type": "Exchangeable P s",
                        "role": "exchangeability_anchor",
                    },
                    {
                        "name": "hq",
                        "type": "q_hat = fun ω => orderStat s k ω",
                        "role": "quantile_definition_anchor",
                    },
                    {
                        "name": "hC",
                        "type": "coverage event identity",
                        "role": "coverage_event_anchor",
                    },
                ],
                "premise_semantic_anchor_binders": [
                    {
                        "name": "hq",
                        "type": "q_hat = fun ω => orderStat s k ω",
                        "role": "quantile_definition_anchor",
                    },
                    {
                        "name": "hC",
                        "type": "coverage event identity",
                        "role": "coverage_event_anchor",
                    },
                ],
                "premise_semantic_anchor_binder_names": ["hq", "hC"],
                "required_semantic_anchor_reference_names": ["hq", "hC"],
                "missing_premise_semantic_anchor_binder_names": ["hq", "hC"],
                "semantic_anchor_reference_gate": (
                    "The returned Lean candidate source must reference every "
                    "required_semantic_anchor_reference_names entry outside comments."
                ),
                "recommended_repair_tasks": [
                    "repair the Lean proof body so it references missing exact "
                    "source semantic anchor binder(s) outside comments: hq, hC"
                ],
                "source_theorem_signature_excerpt": [
                    "theorem split_conformal_coverage",
                    "    (hExch : Exchangeable)",
                ],
                "adapter_signature_excerpt": [
                    "theorem split_conformal_coverage_source_to_bridge_adapter",
                    "    (hGoodCovered : {ω | rank ω ∈ BadRanks}ᶜ ⊆ covered) :",
                ],
                "proof_body_attempted": True,
                "proof_body_attempt_success": False,
                "proof_body_attempt_summaries": [
                    "1:simpa:returncode=1:compiled=False"
                ],
                "proof_body_goal_excerpt": [
                    "⊢ P {ω | s (Fin.last n₂) ω ≤ q_hat ω} ≥ "
                    "ENNReal.ofReal (1 - α)"
                ],
                "runtime_queue_status": (
                    "PENDING_SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_REPAIR"
                ),
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            }
        ],
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["registered_candidate_obligation_ids"] == []
    assert manifest["runtime_learning_ready"] is True
    assert manifest["proof_evidence_status"] == (
        "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
    )
    check = manifest["checks"][0]
    assert check["semantic_primitive_gap_kind"] == (
        "source_to_bridge_premise_semantic_gap"
    )
    assert check["premise_name"] == "hGoodCovered"
    assert check["premise_target_type"] == (
        "{ω | rank ω ∈ BadRanks}ᶜ ⊆ covered"
    )
    assert check["premise_derivation_gap_kind"] == (
        "concrete_premise_target_lacks_nonvacuous_derivation_candidate"
    )
    assert check["premise_semantic_dependency_status"] == (
        "SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_DEPENDENCIES_REQUIRED"
    )
    assert (
        "define covered from the exact source coverage event using hC"
        in check["premise_semantic_dependency_requirements"]
    )
    assert check["missing_premise_semantic_anchor_binder_names"] == ["hq", "hC"]
    assert check["required_semantic_anchor_reference_names"] == ["hq", "hC"]
    assert check["exact_source_theorem_binders"][1]["name"] == "hq"
    assert check["premise_semantic_anchor_binders"][1]["name"] == "hC"
    assert "outside comments" in check["semantic_anchor_reference_gate"]
    assert (
        "references missing exact source semantic anchor binder(s) outside comments: hq, hC"
        in check["recommended_repair_tasks"][0]
    )
    assert check["kernel_verified"] is False

    learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(learning_rows) == 1
    learning_row = learning_rows[0]
    assert learning_row["learning_task"] == (
        "source_to_bridge_premise_semantic_repair_feedback"
    )
    assert learning_row["premise_name"] == "hGoodCovered"
    assert learning_row["premise_target_status"] == (
        "ADAPTER_PREMISE_TARGET_EXTRACTED"
    )
    assert learning_row["premise_target_type"] == (
        "{ω | rank ω ∈ BadRanks}ᶜ ⊆ covered"
    )
    assert learning_row["premise_semantic_dependency_status"] == (
        "SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_DEPENDENCIES_REQUIRED"
    )
    assert (
        "define covered from the exact source coverage event using hC"
        in learning_row["premise_semantic_dependency_requirements"]
    )
    assert learning_row["missing_premise_semantic_anchor_binder_names"] == [
        "hq",
        "hC",
    ]
    assert learning_row["required_semantic_anchor_reference_names"] == ["hq", "hC"]
    assert learning_row["exact_source_theorem_binders"][1]["name"] == "hq"
    assert learning_row["premise_semantic_anchor_binders"][1]["name"] == "hC"
    assert learning_row["input_summary"]["semantic_primitive_checks"][0][
        "premise_derivation_gap_summary"
    ].startswith("The adapter premise target is known")
    assert learning_row["input_summary"]["semantic_primitive_checks"][0][
        "missing_premise_semantic_anchor_binder_names"
    ] == ["hq", "hC"]
    assert learning_row["proof_evidence_status"] == (
        "SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_REPAIR_FEEDBACK_NOT_PROOF_EVIDENCE"
    )
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


def test_source_semantic_bridge_preserves_exact_goal_shape_obligations(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_semantic_primitive_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            {
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "source_theorem_semantic_primitive_work_order:lower",
                "question_id": "conformal_prediction_coverage",
                "semantic_primitive_id": (
                    "source_theorem_exact_goal_shape_obligation:lower"
                ),
                "semantic_primitive_gap": (
                    "Bridge the ENNReal lower-bound coverage adapter to the exact "
                    "real-valued probability lower-bound statement"
                ),
                "semantic_primitive_gap_kind": (
                    "source_theorem_exact_goal_shape_obligation"
                ),
                "exact_goal_shape_obligation_id": (
                    "real_probability_lower_bound_from_ennreal_adapter"
                ),
                "exact_goal_shape_obligation": (
                    "Bridge ENNReal coverage to real-valued probability."
                ),
                "placeholder_symbol": (
                    "real_probability_lower_bound_from_ennreal_adapter"
                ),
                "target_theorem_name": "split_conformal_coverage",
                "candidate_registered_obligation_ids": [
                    "split_conformal_good_rank_coverage_bridge"
                ],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            {
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "source_theorem_semantic_primitive_work_order:upper",
                "question_id": "conformal_prediction_coverage",
                "semantic_primitive_id": (
                    "source_theorem_exact_goal_shape_obligation:upper"
                ),
                "semantic_primitive_gap": (
                    "Prove the upper finite-sample split-conformal coverage component"
                ),
                "semantic_primitive_gap_kind": (
                    "source_theorem_exact_goal_shape_obligation"
                ),
                "exact_goal_shape_obligation_id": "upper_coverage_bound_component",
                "exact_goal_shape_obligation": (
                    "Prove the missing upper split-conformal coverage component."
                ),
                "placeholder_symbol": "upper_coverage_bound_component",
                "target_theorem_name": "split_conformal_coverage",
                "candidate_registered_obligation_ids": [],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
        ],
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    assert manifest["n_exact_goal_shape_obligation_work_orders"] == 2
    assert manifest["exact_goal_shape_obligation_ids"] == [
        "real_probability_lower_bound_from_ennreal_adapter",
        "upper_coverage_bound_component",
    ]
    assert manifest["registered_exact_goal_shape_obligation_ids"] == [
        "real_probability_lower_bound_from_ennreal_adapter",
        "upper_coverage_bound_component",
    ]
    assert manifest["unregistered_exact_goal_shape_obligation_ids"] == []
    by_obligation = {
        check["exact_goal_shape_obligation_id"]: check
        for check in manifest["checks"]
    }
    assert by_obligation[
        "real_probability_lower_bound_from_ennreal_adapter"
    ]["exact_goal_shape_registered_support_present"] is True
    assert by_obligation[
        "upper_coverage_bound_component"
    ]["exact_goal_shape_registered_support_present"] is True
    assert by_obligation[
        "upper_coverage_bound_component"
    ]["registered_candidate_obligation_ids"] == (
        ["split_conformal_upper_coverage_rank_budget_bridge"]
    )
    assert manifest["runtime_learning_ready"] is False
    assert manifest["proof_library_expansion_queue_ready"] is False
    assert manifest["n_proof_library_expansion_queue_rows"] == 0
    assert manifest["proof_library_expansion_queue_proof_evidence_status"] == (
        "NO_PROOF_LIBRARY_EXPANSION_WORK_ORDERS"
    )
    expansion_queue = [
        json.loads(line)
        for line in Path(
            str(manifest["proof_library_expansion_queue_jsonl"])
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert expansion_queue == []
    assert manifest["proof_evidence_status"] == (
        "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
    )


def test_source_semantic_bridge_routes_conjunction_split_as_registered_assembly(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_semantic_primitive_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            {
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "source_theorem_semantic_primitive_work_order:adapter",
                "question_id": "conformal_prediction_coverage",
                "semantic_primitive_id": (
                    "source_theorem_exact_goal_shape_obligation:adapter"
                ),
                "semantic_primitive_gap": (
                    "Close the mismatch between the kernel-verified "
                    "source-to-bridge adapter and the exact theorem goal shape."
                ),
                "semantic_primitive_gap_kind": (
                    "source_theorem_exact_goal_shape_obligation"
                ),
                "exact_goal_shape_obligation_id": (
                    "source_to_bridge_adapter_goal_shape_mismatch"
                ),
                "exact_goal_shape_obligation": (
                    "Source-to-bridge adapter goal shape mismatch."
                ),
                "placeholder_symbol": "source_to_bridge_adapter_goal_shape_mismatch",
                "target_theorem_name": "split_conformal_coverage",
                "candidate_artifact_path": "runs/proof_body_attempt.lean",
                "kernel_verified_theorem_reduction_closure_declarations": [
                    "splitConformalFiniteSampleCoverage_reductionClosure"
                ],
                "verified_theorem_reduction_closure_artifact_paths": [
                    "runs/theorem_reduction_closure/closure.lean"
                ],
                "kernel_verified_theorem_reduction_closure_signature_excerpts": [
                    "theorem splitConformalFiniteSampleCoverage_reductionClosure "
                    "{Ω ρ : Type*} ... "
                    "(hGoodCovered : {ω | rank ω ∈ BadRanks}ᶜ ⊆ covered) : "
                    "1 - α_total ≤ μ covered"
                ],
                "kernel_verified_theorem_reduction_closure_target_ids": [
                    "split_conformal_finite_sample_coverage_reduction_closure"
                ],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            {
                "artifact_kind": "SourceTheoremSemanticPrimitiveWorkOrder",
                "work_order_id": "source_theorem_semantic_primitive_work_order:split",
                "question_id": "conformal_prediction_coverage",
                "semantic_primitive_id": (
                    "source_theorem_exact_goal_shape_obligation:split"
                ),
                "semantic_primitive_gap": (
                    "Split the exact source theorem conjunction into lower and "
                    "upper proof components before assembling the final proof."
                ),
                "semantic_primitive_gap_kind": (
                    "source_theorem_exact_goal_shape_obligation"
                ),
                "exact_goal_shape_obligation_id": "conjunctive_source_theorem_split",
                "exact_goal_shape_obligation": (
                    "Assemble lower and upper source theorem proof components."
                ),
                "placeholder_symbol": "conjunctive_source_theorem_split",
                "target_theorem_name": "split_conformal_coverage",
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
        ],
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    assert manifest["registered_exact_goal_shape_obligation_ids"] == [
        "conjunctive_source_theorem_split"
    ]
    assert manifest["unregistered_exact_goal_shape_obligation_ids"] == [
        "source_to_bridge_adapter_goal_shape_mismatch"
    ]
    by_obligation = {
        check["exact_goal_shape_obligation_id"]: check
        for check in manifest["checks"]
    }
    assert by_obligation[
        "conjunctive_source_theorem_split"
    ]["registered_candidate_obligation_ids"] == [
        "source_theorem_conjunction_from_components"
    ]
    assert by_obligation[
        "source_to_bridge_adapter_goal_shape_mismatch"
    ]["registered_candidate_obligation_ids"] == []
    expansion_queue = [
        json.loads(line)
        for line in Path(
            str(manifest["proof_library_expansion_queue_jsonl"])
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert expansion_queue == []
    assert manifest["n_proof_library_expansion_queue_rows"] == 0
    assert manifest["proof_library_expansion_queue_ready"] is False
    assert manifest["proof_library_expansion_queue_proof_evidence_status"] == (
        "NO_PROOF_LIBRARY_EXPANSION_WORK_ORDERS"
    )
    adapter_queue = [
        json.loads(line)
        for line in Path(
            str(manifest["source_to_bridge_adapter_instantiation_queue_jsonl"])
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [
        row["exact_goal_shape_obligation_id"] for row in adapter_queue
    ] == ["source_to_bridge_adapter_goal_shape_mismatch"]
    assert adapter_queue[0]["candidate_artifact_path"] == "runs/proof_body_attempt.lean"
    assert adapter_queue[0]["source_candidate_artifact_path"] == (
        "runs/proof_body_attempt.lean"
    )
    assert adapter_queue[0]["runtime_queue_status"] == (
        "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
    )
    assert adapter_queue[0]["target_artifact_kind"] == (
        "source_theorem_exact_proof_body_adapter_instantiation"
    )
    assert adapter_queue[0][
        "kernel_verified_theorem_reduction_closure_declarations"
    ] == ["splitConformalFiniteSampleCoverage_reductionClosure"]
    assert adapter_queue[0]["verified_theorem_reduction_closure_artifact_paths"] == [
        "runs/theorem_reduction_closure/closure.lean"
    ]
    assert "hGoodCovered" in adapter_queue[0][
        "kernel_verified_theorem_reduction_closure_signature_excerpts"
    ][0]
    assert adapter_queue[0][
        "kernel_verified_theorem_reduction_closure_target_ids"
    ] == ["split_conformal_finite_sample_coverage_reduction_closure"]
    assert manifest["n_source_to_bridge_adapter_instantiation_queue_rows"] == 1
    assert manifest["source_to_bridge_adapter_instantiation_queue_ready"] is True
    assert manifest[
        "source_to_bridge_adapter_instantiation_queue_proof_evidence_status"
    ] == (
        "WORK_ORDER_NOT_PROOF_EVIDENCE"
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
    assert manifest["n_kernel_verified_source_theorem_semantic_primitive_ids"] == 1
    assert manifest["kernel_verified_source_theorem_semantic_primitive_ids"] == [
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
    assert manifest["n_kernel_verified_source_theorem_semantic_primitive_ids"] == 1
    assert manifest["kernel_verified_source_theorem_semantic_primitive_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound"
    ]
    assert manifest["semantic_closure_status"] == (
        "REGISTERED_SUPPORT_VERIFIED_PLACEHOLDER_DEFINITION_OPEN"
    )
    assert manifest["placeholder_definition_status"] == (
        "OPEN_REQUIRES_REVIEWED_FORMAL_DEFINITION"
    )
    assert manifest["source_theorem_ready_for_exact_proof_body"] is False
    assert manifest["source_theorem_semantic_support_only"] is True
    assert manifest["kernel_verified_source_theorem_semantic_definition_ids"] == []
    assert learning_rows[0][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == ["split_conformal_bad_rank_budget_from_uniform_rank_bound"]
    assert learning_rows[0]["semantic_closure_status"] == (
        "REGISTERED_SUPPORT_VERIFIED_PLACEHOLDER_DEFINITION_OPEN"
    )
    assert learning_rows[0]["placeholder_definition_status"] == (
        "OPEN_REQUIRES_REVIEWED_FORMAL_DEFINITION"
    )
    assert learning_rows[0]["source_theorem_ready_for_exact_proof_body"] is False
    assert learning_rows[0]["source_theorem_semantic_support_only"] is True
    assert learning_rows[0][
        "kernel_verified_source_theorem_semantic_definition_ids"
    ] == []
    assert learning_rows[0]["input_summary"][
        "kernel_verified_source_theorem_semantic_support_obligation_ids"
    ] == ["split_conformal_bad_rank_budget_from_uniform_rank_bound"]
    assert learning_rows[0]["input_summary"]["semantic_closure_status"] == (
        "REGISTERED_SUPPORT_VERIFIED_PLACEHOLDER_DEFINITION_OPEN"
    )
    assert learning_rows[0]["input_summary"][
        "placeholder_definition_status"
    ] == "OPEN_REQUIRES_REVIEWED_FORMAL_DEFINITION"
    check_context = learning_rows[0]["input_summary"]["semantic_primitive_checks"][0]
    assert check_context["placeholder_symbol"] == "Exchangeable"
    assert check_context["semantic_closure_status"] == (
        "REGISTERED_SUPPORT_VERIFIED_PLACEHOLDER_DEFINITION_OPEN"
    )
    assert check_context["source_theorem_ready_for_exact_proof_body"] is False
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


def test_source_semantic_bridge_string_false_executor_flags_do_not_drop_handoff(
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
                    "exact_source_theorem_proof_body_execution_result:string-false"
                ),
                "execution_queue_id": (
                    "exact_source_theorem_proof_body_execution_queue:string-false"
                ),
                "target_theorem_name": "split_conformal_coverage",
                "source_theorem_kernel_verified": "false",
                "source_theorem_target_known": "false",
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": "false",
                    "target_lean_declaration": "",
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
                    "proof_body_attempted": "true",
                    "proof_body_attempt_success": "false",
                    "source_theorem_kernel_verified": "false",
                    "source_theorem_target_known": "false",
                    "source_theorem_target_provenance": {
                        "source_theorem_target_known": "false",
                        "target_lean_declaration": "",
                    },
                },
            }
        ],
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        proof_body_executor_dir=executor_dir,
        question_id="conformal_prediction_coverage",
    )

    queue_rows = [
        json.loads(line)
        for line in Path(str(manifest["source_queue_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    by_symbol = {row["placeholder_symbol"]: row for row in queue_rows}
    assert set(by_symbol) == {"Exchangeable", "orderStat"}
    assert by_symbol["Exchangeable"]["source_theorem_target_known"] is False
    assert by_symbol["orderStat"]["source_theorem_target_known"] is False
    assert by_symbol["Exchangeable"]["proof_body_attempted"] is True
    assert by_symbol["Exchangeable"]["proof_body_attempt_success"] is False

    checks_by_symbol = {row["placeholder_symbol"]: row for row in manifest["checks"]}
    assert checks_by_symbol["Exchangeable"]["source_theorem_target_known"] is False
    assert checks_by_symbol["orderStat"]["source_theorem_target_known"] is False
    assert checks_by_symbol["Exchangeable"]["proof_body_attempted"] is True
    assert checks_by_symbol["Exchangeable"]["proof_body_attempt_success"] is False
    assert manifest["proof_evidence_status"] == (
        "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
    )


def test_source_semantic_bridge_materializes_queue_from_semantic_alignment_feedback(
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
                    "exact_source_theorem_proof_body_execution_result:semantic"
                ),
                "execution_queue_id": (
                    "exact_source_theorem_proof_body_execution_queue:semantic"
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
                        "proof_body_reached_semantic_alignment_unreviewed"
                    ),
                    "semantic_alignment_blockers": [
                        "unreviewed synthesized definition semantic risk: "
                        "draft finite permutation-invariant joint-law "
                        "exchangeability still requires source review",
                        "unreviewed synthesized definition semantic risk: "
                        "draft sorted finite order statistic uses rank k but "
                        "still needs source review for indexing convention, "
                        "tie behavior, and conformal quantile rank",
                    ],
                    "semantic_alignment_constraints": [
                        "preserve split conformal marginal coverage semantics"
                    ],
                    "proof_body_goal_reached": True,
                    "proof_body_attempted": False,
                    "proof_body_attempt_success": False,
                    "candidate_live_proof_state_request": {
                        "proof_body_goal_excerpt": [
                            "⊢ 1 - alpha ≤ P.real "
                            "{ω | s (Fin.last n2) ω ≤ q_hat ω}"
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

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        proof_body_executor_dir=executor_dir,
        question_id="conformal_prediction_coverage",
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
    assert by_symbol["Exchangeable"]["failure_classification"] == (
        "proof_body_reached_semantic_alignment_unreviewed"
    )
    assert by_symbol["orderStat"]["semantic_alignment_blockers"]
    assert by_symbol["orderStat"]["semantic_alignment_constraints"] == [
        "preserve split conformal marginal coverage semantics"
    ]
    assert by_symbol["orderStat"]["proof_body_attempted"] is False
    assert "1 - alpha" in by_symbol["orderStat"]["proof_body_goal_excerpt"][0]
    assert manifest["n_work_orders"] == 2
    assert manifest["registered_candidate_obligation_ids"] == [
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
        "split_conformal_good_rank_set_inclusion_bridge",
    ]


def test_source_semantic_bridge_materializes_exact_goal_shape_queue_from_executor(
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
                    "exact_source_theorem_proof_body_execution_result:goal_shape"
                ),
                "execution_queue_id": (
                    "exact_source_theorem_proof_body_execution_queue:goal_shape"
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
                        "proof_body_verified_adapter_context_insufficient"
                    ),
                    "proof_body_attempted": True,
                    "proof_body_attempt_success": False,
                    "proof_body_attempt_summaries": [
                        "1:exact adapter:returncode=1:compiled=False"
                    ],
                    "proof_body_goal_excerpt": [
                        "⊢ 1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧",
                        "  P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ≤ 1 - alpha + 1 / ↑(n2 + 1)",
                    ],
                    "exact_goal_shape_obligation_ids": [
                        "real_probability_lower_bound_from_ennreal_adapter",
                        "upper_coverage_bound_component",
                    ],
                    "exact_goal_shape_obligations": [
                        "Bridge ENNReal coverage to real-valued probability.",
                        "Prove the missing upper coverage component.",
                    ],
                },
            }
        ],
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        proof_body_executor_dir=executor_dir,
        question_id="conformal_prediction_coverage",
    )

    queue_path = Path(str(manifest["source_queue_jsonl"]))
    queue_rows = [
        json.loads(line)
        for line in queue_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_obligation = {
        row["exact_goal_shape_obligation_id"]: row for row in queue_rows
    }
    assert set(by_obligation) == {
        "real_probability_lower_bound_from_ennreal_adapter",
        "upper_coverage_bound_component",
    }
    assert by_obligation[
        "real_probability_lower_bound_from_ennreal_adapter"
    ]["candidate_registered_obligation_ids"] == [
        "split_conformal_good_rank_coverage_bridge"
    ]
    assert by_obligation[
        "upper_coverage_bound_component"
    ]["candidate_registered_obligation_ids"] == [
        "split_conformal_upper_coverage_rank_budget_bridge"
    ]
    assert manifest["n_exact_goal_shape_obligation_work_orders"] == 2
    assert manifest["registered_exact_goal_shape_obligation_ids"] == [
        "real_probability_lower_bound_from_ennreal_adapter",
        "upper_coverage_bound_component",
    ]
    assert manifest["unregistered_exact_goal_shape_obligation_ids"] == []
    expansion_queue = [
        json.loads(line)
        for line in Path(
            str(manifest["proof_library_expansion_queue_jsonl"])
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert expansion_queue == []


def test_source_semantic_bridge_infers_verified_adapter_goal_shape_from_executor(
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
                "execution_result_id": "exact_source_result:verified_adapter",
                "target_theorem_name": "split_conformal_coverage",
                "trigger": (
                    "EXACT_SOURCE_PROOF_BODY_VERIFIED_ADAPTER_CONTEXT_INSUFFICIENT"
                ),
                "input_summary": {
                    "candidate_artifact_path": "runs/proof_body_attempt.lean",
                    "failure_classification": (
                        "proof_body_verified_adapter_context_insufficient"
                    ),
                    "proof_body_attempted": True,
                    "proof_body_attempt_success": False,
                    "proof_body_goal_excerpt": [
                        "⊢ 1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧",
                    ],
                    "kernel_verified_theorem_reduction_closure_declarations": [
                        "splitConformalFiniteSampleCoverage_reductionClosure"
                    ],
                    "verified_theorem_reduction_closure_artifact_paths": [
                        "runs/theorem_reduction_closure/closure.lean"
                    ],
                    "kernel_verified_theorem_reduction_closure_signature_excerpts": [
                        "theorem splitConformalFiniteSampleCoverage_reductionClosure "
                        "(hGoodCovered : {ω | rank ω ∈ BadRanks}ᶜ ⊆ covered) "
                        "(hRank : ∀ r ∈ BadRanks, μ {ω | rank ω = r} ≤ α r) "
                        "(h_total : (∑ r ∈ BadRanks, α r) ≤ α_total) : "
                        "1 - α_total ≤ μ covered"
                    ],
                    "kernel_verified_theorem_reduction_closure_target_ids": [
                        "split_conformal_finite_sample_coverage_reduction_closure"
                    ],
                },
            }
        ],
    )

    manifest = run_source_theorem_semantic_primitive_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        proof_body_executor_dir=executor_dir,
        question_id="conformal_prediction_coverage",
    )

    assert manifest["n_exact_goal_shape_obligation_work_orders"] == 7
    assert "source_to_bridge_adapter_goal_shape_mismatch" in manifest[
        "exact_goal_shape_obligation_ids"
    ]
    adapter_queue = [
        json.loads(line)
        for line in Path(
            str(manifest["source_to_bridge_adapter_instantiation_queue_jsonl"])
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(adapter_queue) == 1
    assert adapter_queue[0]["exact_goal_shape_obligation_id"] == (
        "source_to_bridge_adapter_goal_shape_mismatch"
    )
    assert adapter_queue[0][
        "kernel_verified_theorem_reduction_closure_declarations"
    ] == ["splitConformalFiniteSampleCoverage_reductionClosure"]
    assert "hGoodCovered" in adapter_queue[0][
        "kernel_verified_theorem_reduction_closure_signature_excerpts"
    ][0]

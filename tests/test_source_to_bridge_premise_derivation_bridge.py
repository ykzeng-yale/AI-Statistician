from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_statistician.research_architect import KERNEL_PROOF_BOUNDARY
from ai_statistician.source_to_bridge_premise_derivation_proofengineer_bridge import (
    resolve_source_to_bridge_premise_derivation_queue_path,
    run_source_to_bridge_premise_derivation_proofengineer_bridge,
)

PROOF_BODY_GOAL_CONCLUSION = (
    "P {ω | s (Fin.last m) ω ≤ q_hat ω} ≥ ENNReal.ofReal (1 - alpha)"
)

PROOF_BODY_GOAL_CONTEXT = {
    "schema_version": 1,
    "artifact_kind": "ExactSourceTheoremProofBodyGoalContext",
    "binder_names": ["hExch", "q", "hq"],
    "hypothesis_rows": [
        {
            "binder_name": "hExch",
            "binder_type": "Exchangeable P s",
            "raw_lines": ["hExch : Exchangeable P s"],
        },
        {
            "binder_name": "q",
            "binder_type": "ℝ",
            "raw_lines": ["q : ℝ"],
        },
        {
            "binder_name": "hq",
            "binder_type": "∀ᵐ ... / ↑n ≥ 1 - alpha",
            "raw_lines": ["hq : ∀ᵐ ... / ↑n ≥ 1 - alpha"],
        },
    ],
    "conclusion": PROOF_BODY_GOAL_CONCLUSION,
    "proof_evidence_status": "PROOF_BODY_GOAL_CONTEXT_NOT_PROOF_EVIDENCE",
}


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def _premise_work_order(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "schema_version": 1,
        "artifact_kind": "SourceToBridgePremiseDerivationWorkOrder",
        "work_order_id": (
            "source_to_bridge_premise_derivation_work_order:hGoodCovered"
        ),
        "source_adapter_check_id": (
            "source_theorem_proof_body_adapter_check:adapter"
        ),
        "source_adapter_work_order_id": (
            "source_theorem_exact_goal_shape_adapter_instantiation:adapter"
        ),
        "source_queue_jsonl": "runs/source_to_bridge_adapter_queue.jsonl",
        "question_id": "conformal_prediction_coverage",
        "question_title": "Split conformal coverage",
        "target_theorem_name": "split_conformal_coverage",
        "target_lean_declaration": "split_conformal_coverage",
        "target_theorem_goal_ids": ["split_conformal_coverage"],
        "premise_name": "hGoodCovered",
        "required_derivation": (
            "derive hGoodCovered from exact source theorem hypotheses"
        ),
        "forbidden_as_adapter_assumption": True,
        "exact_goal_shape_obligation_ids": [
            "source_to_bridge_adapter_goal_shape_mismatch"
        ],
        "source_candidate_artifact_path": "runs/source_attempt.lean",
        "adapter_candidate_artifact_path": "runs/adapter_attempt.lean",
        "proof_body_signature_probe_artifact_path": (
            "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
        ),
        "source_theorem_signature_probe_artifact_path": (
            "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
        ),
        "adapter_declaration_name": "split_conformal_coverage_source_to_bridge_adapter",
        "proof_body_goal_excerpt": [
            "hExch : Exchangeable P s",
            "q : ℝ",
            "hq : ∀ᵐ ... / ↑n ≥ 1 - alpha",
            f"⊢ {PROOF_BODY_GOAL_CONCLUSION}",
        ],
        "source_to_bridge_premise_goal_context": PROOF_BODY_GOAL_CONTEXT,
        "source_to_bridge_premise_goal_binder_names": ["hExch", "q", "hq"],
        "source_to_bridge_premise_goal_conclusion": PROOF_BODY_GOAL_CONCLUSION,
        "proof_body_attempt_summaries": [
            "1:exact split_conformal_coverage_source_to_bridge_adapter:returncode=1"
        ],
        "proof_body_attempt_count": 1,
        "proof_body_gate_status": "PROOF_BODY_REACHED_PROOF_INCOMPLETE",
        "source_theorem_exact_proof_body_reached": True,
        "source_theorem_exact_proof_body_gate_open_for_kernel_repair": True,
        "source_theorem_exact_proof_body_gate_open_target_names": [
            "split_conformal_coverage"
        ],
        "semantic_alignment_constraints": [
            "covered must be instantiated from the exact source coverage event"
        ],
        "semantic_alignment_blockers": [],
        "source_theorem_kernel_evidence_eligible": True,
        "kernel_verified_theorem_reduction_closure_declarations": [
            "splitConformalFiniteSampleCoverage_reductionClosure"
        ],
        "verified_theorem_reduction_closure_artifact_paths": [
            "runs/theorem_reduction_closure/closure.lean"
        ],
        "kernel_verified_source_theorem_semantic_support_obligation_ids": [
            "split_conformal_good_rank_set_inclusion_bridge"
        ],
        "acceptance_gate": (
            "AXLE/local Lean kernel verifies hGoodCovered from exact source "
            "hypotheses."
        ),
        "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
    }
    row.update(overrides)
    return row


def test_premise_bridge_resolves_adapter_bridge_manifest_queue(tmp_path: Path) -> None:
    adapter_bridge_dir = tmp_path / "adapter_bridge"
    queue = (
        adapter_bridge_dir
        / "source_to_bridge_premise_derivation_queue"
        / "source_to_bridge_premise_derivation_queue.jsonl"
    )
    _write_jsonl(queue, [_premise_work_order()])
    (adapter_bridge_dir / "source_theorem_proof_body_adapter_proofengineer_bridge_manifest.json").write_text(
        json.dumps(
            {
                "source_to_bridge_premise_derivation_queue_jsonl": str(
                    queue.relative_to(tmp_path)
                )
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_source_to_bridge_premise_derivation_queue_path(
        adapter_bridge_dir=adapter_bridge_dir
    )

    assert resolved == queue


def test_premise_bridge_resolves_runtime_formalizer_work_order_artifact(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    queue = (
        runtime_dir
        / "runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer.jsonl"
    )
    _write_jsonl(queue, [_premise_work_order()])
    (runtime_dir / "research_agent_runtime_manifest.json").write_text(
        json.dumps(
            {
                "artifacts": {
                    "runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer_jsonl": str(
                        queue
                    )
                }
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_source_to_bridge_premise_derivation_queue_path(
        runtime_dir=runtime_dir
    )

    assert resolved == queue


def test_premise_bridge_resolves_runtime_formalizer_work_order_fallback(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    queue = (
        runtime_dir
        / "runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer.jsonl"
    )
    _write_jsonl(queue, [_premise_work_order()])
    (runtime_dir / "research_agent_runtime_manifest.json").write_text(
        json.dumps({"artifacts": {}}),
        encoding="utf-8",
    )

    resolved = resolve_source_to_bridge_premise_derivation_queue_path(
        runtime_dir=runtime_dir
    )

    assert resolved == queue


def test_premise_bridge_materializes_nonproof_skeleton(tmp_path: Path) -> None:
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    source_attempt = tmp_path / "source_attempt.lean"
    adapter_attempt = tmp_path / "adapter_attempt.lean"
    source_attempt.write_text(
        "\n".join(
            [
                "import Mathlib",
                "theorem split_conformal_coverage",
                "    (hexch hq hC : Prop) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    adapter_attempt.write_text(
        "\n".join(
            [
                "import Mathlib",
                "theorem split_conformal_coverage_source_to_bridge_adapter",
                "    (covered : Set Nat)",
                "    (hGoodCovered : covered ⊆ covered) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                source_candidate_artifact_path=str(source_attempt),
                adapter_candidate_artifact_path=str(adapter_attempt),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_premise_derivation_check_rows"] == 1
    assert manifest["n_premise_derivation_kernel_verified"] == 0
    assert manifest["n_premise_derivation_candidate_requests"] == 1
    assert manifest["n_grouped_premise_derivation_learning_rows"] == 0
    assert manifest["proof_body_gate_statuses"] == [
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    ]
    assert (
        manifest["n_source_theorem_exact_proof_body_gate_open_for_kernel_repair"]
        == 1
    )
    assert manifest["n_proof_body_signature_probe_artifact_rows"] == 1
    assert manifest["proof_body_signature_probe_artifact_paths"] == [
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    ]
    assert manifest["n_proof_body_goal_context_rows"] == 1
    assert manifest["proof_body_goal_context_binder_names"] == [
        "hExch",
        "hq",
        "q",
    ]
    assert manifest["proof_body_goal_context_conclusions"] == [
        PROOF_BODY_GOAL_CONCLUSION
    ]
    assert manifest[
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert manifest["premise_derivation_candidate_request_premise_names"] == [
        "hGoodCovered"
    ]
    assert manifest["source_theorem_kernel_verified"] is False
    assert manifest["proof_evidence_status"] == (
        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_BRIDGE_NOT_PROOF_EVIDENCE"
    )
    row = manifest["rows"][0]
    assert row["premise_name"] == "hGoodCovered"
    assert row["premise_candidate_generation_mode"] == (
        "proofengineer_generated_premise_derivation_skeleton"
    )
    assert row["premise_candidate_evidence_eligible"] is False
    assert row["source_theorem_kernel_evidence_eligible"] is True
    assert row["semantic_alignment_blockers"] == ()
    assert row["proof_body_attempt_count"] == 1
    assert row["proof_body_gate_status"] == "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    assert row["proof_body_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert row["source_theorem_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert list(row["proof_body_goal_binder_names"]) == ["hExch", "q", "hq"]
    assert row["proof_body_goal_conclusion"] == PROOF_BODY_GOAL_CONCLUSION
    assert row["proof_body_goal_context"]["conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert row["proof_body_goal_context"]["proof_evidence_status"] == (
        "PROOF_BODY_GOAL_CONTEXT_NOT_PROOF_EVIDENCE"
    )
    assert row["proof_body_goal_context"]["proof_evidence_boundary"] == (
        KERNEL_PROOF_BOUNDARY
    )
    assert row["source_theorem_exact_proof_body_reached"] is True
    assert (
        row["source_theorem_exact_proof_body_gate_open_for_kernel_repair"] is True
    )
    assert list(row["source_theorem_exact_proof_body_gate_open_target_names"]) == [
        "split_conformal_coverage"
    ]
    assert row["failure_classification"] == (
        "premise_derivation_candidate_missing_nonvacuous_source"
    )
    candidate_source = Path(row["premise_candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert "fail_if_success trivial" in candidate_source
    assert "-- premise name: hGoodCovered" in candidate_source
    assert f"-- exact source candidate artifact: {source_attempt}" in candidate_source
    assert (
        f"-- source-to-bridge adapter candidate artifact: {adapter_attempt}"
        in candidate_source
    )
    assert (
        "-- source theorem signature probe artifact: "
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    ) in candidate_source
    assert (
        "-- source-to-bridge adapter declaration: "
        "split_conformal_coverage_source_to_bridge_adapter"
    ) in candidate_source
    assert "-- source context status: SOURCE_AND_ADAPTER_SIGNATURES_EXTRACTED" in (
        candidate_source
    )
    assert "-- exact source theorem signature: theorem split_conformal_coverage" in (
        candidate_source
    )
    assert "-- proof body attempt count: 1" in candidate_source
    assert (
        "-- proof body gate status: PROOF_BODY_REACHED_PROOF_INCOMPLETE"
        in candidate_source
    )
    assert (
        "-- exact source proof-body gate open for kernel repair: true"
        in candidate_source
    )
    assert (
        "-- exact source proof-body gate-open target: split_conformal_coverage"
        in candidate_source
    )
    assert "-- proof body goal binder: hExch" in candidate_source
    assert "-- proof body goal binder: q" in candidate_source
    assert "-- proof body goal binder: hq" in candidate_source
    assert f"-- proof body goal conclusion: {PROOF_BODY_GOAL_CONCLUSION}" in (
        candidate_source
    )
    assert (
        "-- source theorem kernel evidence eligible before premise derivation: true"
        in candidate_source
    )
    assert (
        "-- semantic alignment constraint: covered must be instantiated from "
        "the exact source coverage event"
    ) in candidate_source
    assert (
        "-- current adapter signature: theorem split_conformal_coverage_source_to_bridge_adapter"
        in candidate_source
    )
    assert "-- premise target status: ADAPTER_PREMISE_TARGET_EXTRACTED" in (
        candidate_source
    )
    assert "-- extracted premise target: covered ⊆ covered" in candidate_source
    assert (
        "-- required source-to-bridge semantic dependency: define covered from "
        "the exact source coverage event using hC"
    ) in candidate_source
    assert "-- exact source binder: hq : Prop [quantile_definition_anchor]" in (
        candidate_source
    )
    assert "-- exact source binder: hC : Prop [coverage_event_anchor]" in (
        candidate_source
    )
    assert "-- required semantic anchor binder: hq : Prop [quantile_definition_anchor]" in (
        candidate_source
    )
    assert "-- required semantic anchor binder: hC : Prop [coverage_event_anchor]" in (
        candidate_source
    )
    assert "-- bridge object instantiation policy:" in candidate_source
    assert "adapter objects such as covered, rank, BadRanks" in candidate_source
    assert "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation" in (
        candidate_source
    )
    assert "(covered : Set Nat) :" in candidate_source
    assert "covered ⊆ covered := by" in candidate_source
    assert "bridge_premise : Prop" not in candidate_source
    assert "splitConformalFiniteSampleCoverage_reductionClosure" in candidate_source
    assert row["source_context_status"] == "SOURCE_AND_ADAPTER_SIGNATURES_EXTRACTED"
    assert row["source_theorem_signature_excerpt"][0] == (
        "theorem split_conformal_coverage"
    )
    assert row["adapter_signature_excerpt"][0] == (
        "theorem split_conformal_coverage_source_to_bridge_adapter"
    )
    assert row["premise_target_status"] == "ADAPTER_PREMISE_TARGET_EXTRACTED"
    assert row["premise_target_matched_binder"] == (
        "(hGoodCovered : covered ⊆ covered)"
    )
    assert row["premise_target_type"] == "covered ⊆ covered"
    assert row["premise_derivation_gap_kind"] == (
        "concrete_premise_target_lacks_nonvacuous_derivation_candidate"
    )
    assert "covered ⊆ covered" in row["premise_derivation_gap_summary"]
    assert row["premise_semantic_dependency_status"] == (
        "SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_DEPENDENCIES_REQUIRED"
    )
    assert (
        "define covered from the exact source coverage event using hC"
        in row["premise_semantic_dependency_requirements"]
    )
    assert list(row["exact_source_theorem_binders"]) == [
        {"name": "hexch", "role": "exchangeability_anchor", "type": "Prop"},
        {"name": "hq", "role": "quantile_definition_anchor", "type": "Prop"},
        {"name": "hC", "role": "coverage_event_anchor", "type": "Prop"},
    ]
    assert list(row["premise_semantic_anchor_binder_names"]) == ["hq", "hC"]
    assert list(row["premise_semantic_anchor_binders"]) == [
        {"name": "hq", "role": "quantile_definition_anchor", "type": "Prop"},
        {"name": "hC", "role": "coverage_event_anchor", "type": "Prop"},
    ]
    assert "WORK_ORDER_NOT_PROOF_EVIDENCE" == _premise_work_order()[
        "proof_evidence_status"
    ]
    candidate_requests = [
        json.loads(line)
        for line in Path(str(manifest["candidate_requests_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(candidate_requests) == 1
    request = candidate_requests[0]
    assert request["artifact_kind"] == (
        "SourceToBridgePremiseDerivationCandidateRequest"
    )
    assert request["premise_name"] == "hGoodCovered"
    assert request["target_lean_declaration"] == "split_conformal_coverage"
    assert request["premise_target_type"] == "covered ⊆ covered"
    assert request["adapter_instantiation_group_id"].startswith(
        "source_to_bridge_adapter_instantiation_group:"
    )
    assert request["required_bridge_premise_names_for_shared_instantiation"] == [
        "hGoodCovered"
    ]
    assert "one shared definition" in request["shared_adapter_instantiation_contract"]
    assert request["premise_candidate_declaration_name"] == (
        "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    )
    assert request["required_formalizer_output_key"] == (
        "source_to_bridge_premise_derivation_candidates"
    )
    assert "premise_derivation_candidate_lean_source" in request[
        "required_candidate_fields"
    ]
    assert (
        "define covered from the exact source coverage event using hC"
        in request["premise_semantic_dependency_requirements"]
    )
    assert request["exact_source_theorem_binders"] == [
        {"name": "hexch", "type": "Prop", "role": "exchangeability_anchor"},
        {"name": "hq", "type": "Prop", "role": "quantile_definition_anchor"},
        {"name": "hC", "type": "Prop", "role": "coverage_event_anchor"},
    ]
    assert request["source_theorem_kernel_evidence_eligible"] is True
    assert request["proof_body_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert request["source_theorem_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert request["signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert request["semantic_alignment_blockers"] == []
    assert request["proof_body_attempt_count"] == 1
    assert request["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert request["proof_body_goal_binder_names"] == ["hExch", "q", "hq"]
    assert request["proof_body_goal_conclusion"] == PROOF_BODY_GOAL_CONCLUSION
    assert request["proof_body_goal_context"]["conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert request["source_to_bridge_premise_goal_binder_names"] == [
        "hExch",
        "q",
        "hq",
    ]
    assert request["source_to_bridge_premise_goal_conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert request["source_theorem_exact_proof_body_reached"] is True
    assert (
        request["source_theorem_exact_proof_body_gate_open_for_kernel_repair"]
        is True
    )
    assert request[
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert request["premise_semantic_anchor_binder_names"] == ["hq", "hC"]
    assert request["premise_semantic_anchor_binders"] == [
        {"name": "hq", "type": "Prop", "role": "quantile_definition_anchor"},
        {"name": "hC", "type": "Prop", "role": "coverage_event_anchor"}
    ]
    assert request["required_semantic_anchor_reference_names"] == ["hq", "hC"]
    assert "outside comments" in request["semantic_anchor_reference_gate"]
    assert "bridge_object_instantiation_policy" in request
    assert "are not source-theorem assumptions" in request[
        "bridge_object_instantiation_policy"
    ]
    assert request["adapter_object_names_requiring_source_instantiation"] == [
        "covered"
    ]
    assert "premise_semantic_anchor_binders" in request["candidate_contract"]
    assert "required_semantic_anchor_reference_names" in request["candidate_contract"]
    assert "covered, rank, BadRanks" in request["candidate_contract"]
    assert request["proof_evidence_status"] == (
        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
    )
    grouped_requests = [
        json.loads(line)
        for line in Path(str(manifest["grouped_candidate_requests_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(grouped_requests) == 1
    grouped_request = grouped_requests[0]
    assert grouped_request["proof_body_goal_binder_names"] == [
        "hExch",
        "q",
        "hq",
    ]
    assert grouped_request["proof_body_goal_conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert grouped_request["source_to_bridge_premise_goal_conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(learning_rows) == 2
    assert learning_rows[0]["learning_task"] == (
        "source_to_bridge_premise_derivation_feedback"
    )
    assert learning_rows[0]["source_theorem_kernel_evidence_eligible"] is True
    assert learning_rows[0]["semantic_alignment_blockers"] == []
    assert learning_rows[0]["proof_body_attempt_count"] == 1
    assert learning_rows[0]["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert learning_rows[0]["proof_body_goal_binder_names"] == [
        "hExch",
        "q",
        "hq",
    ]
    assert learning_rows[0]["proof_body_goal_conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert learning_rows[0]["source_to_bridge_premise_goal_binder_names"] == [
        "hExch",
        "q",
        "hq",
    ]
    assert learning_rows[0]["source_to_bridge_premise_goal_conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert learning_rows[0]["proof_body_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert learning_rows[0]["source_theorem_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert learning_rows[0]["signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert learning_rows[0]["source_theorem_exact_proof_body_reached"] is True
    assert (
        learning_rows[0][
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        is True
    )
    assert learning_rows[0][
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert learning_rows[0]["input_summary"][
        "source_theorem_kernel_evidence_eligible"
    ] is True
    assert learning_rows[0]["input_summary"]["proof_body_attempt_count"] == 1
    assert learning_rows[0]["input_summary"]["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert learning_rows[0]["input_summary"]["proof_body_goal_binder_names"] == [
        "hExch",
        "q",
        "hq",
    ]
    assert learning_rows[0]["input_summary"]["proof_body_goal_conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert learning_rows[0]["input_summary"][
        "proof_body_signature_probe_artifact_path"
    ] == "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    assert learning_rows[0]["input_summary"][
        "source_theorem_signature_probe_artifact_path"
    ] == "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    assert (
        learning_rows[0]["input_summary"][
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        is True
    )
    assert learning_rows[0]["premise_name"] == "hGoodCovered"
    assert learning_rows[0]["premise_target_type"] == "covered ⊆ covered"
    assert learning_rows[0]["adapter_instantiation_group_id"].startswith(
        "source_to_bridge_adapter_instantiation_group:"
    )
    assert learning_rows[0]["premise_derivation_gap_kind"] == (
        "concrete_premise_target_lacks_nonvacuous_derivation_candidate"
    )
    assert learning_rows[0]["premise_semantic_dependency_status"] == (
        "SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_DEPENDENCIES_REQUIRED"
    )
    assert learning_rows[1]["learning_task"] == (
        "source_theorem_exact_semantic_definition_work_order"
    )
    assert learning_rows[1]["placeholder_symbol"] == "covered"
    assert learning_rows[1]["proof_evidence_status"] == (
        "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    assert learning_rows[1]["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert learning_rows[1]["proof_body_goal_binder_names"] == [
        "hExch",
        "q",
        "hq",
    ]
    assert learning_rows[1]["proof_body_goal_conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert learning_rows[1]["source_to_bridge_premise_goal_conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert (
        learning_rows[1][
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        is True
    )
    assert learning_rows[1][
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert learning_rows[1]["candidate_definition_request"][
        "proof_body_gate_status"
    ] == "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    assert (
        learning_rows[1]["candidate_definition_request"][
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        is True
    )
    assert learning_rows[1]["candidate_definition_request"][
        "proof_body_goal_binder_names"
    ] == ["hExch", "q", "hq"]
    assert learning_rows[1]["candidate_definition_request"][
        "proof_body_goal_conclusion"
    ] == PROOF_BODY_GOAL_CONCLUSION
    assert learning_rows[1]["candidate_definition_request"][
        "source_to_bridge_premise_goal_conclusion"
    ] == PROOF_BODY_GOAL_CONCLUSION
    assert learning_rows[1]["proof_body_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert learning_rows[1]["source_theorem_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert learning_rows[1]["candidate_definition_request"][
        "proof_body_signature_probe_artifact_path"
    ] == "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    assert learning_rows[1]["candidate_definition_request"][
        "source_theorem_signature_probe_artifact_path"
    ] == "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    assert learning_rows[1]["input_summary"]["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert learning_rows[1]["input_summary"]["proof_body_goal_binder_names"] == [
        "hExch",
        "q",
        "hq",
    ]
    assert learning_rows[1]["input_summary"]["proof_body_goal_conclusion"] == (
        PROOF_BODY_GOAL_CONCLUSION
    )
    assert learning_rows[1]["input_summary"][
        "proof_body_signature_probe_artifact_path"
    ] == "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    assert (
        "define covered from the exact source coverage event using hC"
        in learning_rows[0]["premise_semantic_dependency_requirements"]
    )
    assert learning_rows[0]["premise_semantic_anchor_binder_names"] == [
        "hq",
        "hC",
    ]
    assert learning_rows[0]["premise_semantic_anchor_binders"] == [
        {"name": "hq", "role": "quantile_definition_anchor", "type": "Prop"},
        {"name": "hC", "role": "coverage_event_anchor", "type": "Prop"},
    ]
    assert learning_rows[0]["source_theorem_kernel_verified"] is False
    assert learning_rows[0]["runtime_queue_status"] == (
        "PENDING_SOURCE_TO_BRIDGE_PREMISE_DERIVATION"
    )
    learning_request = learning_rows[0][
        "source_to_bridge_premise_derivation_candidate_request"
    ]
    assert learning_request["candidate_request_id"] == request["candidate_request_id"]
    assert learning_rows[0][
        "source_to_bridge_premise_derivation_candidate_request_id"
    ] == request["candidate_request_id"]
    export_manifest = json.loads(
        Path(str(manifest["runtime_learning_export_manifest"]))
        .read_text(encoding="utf-8")
    )
    assert export_manifest["proof_body_gate_statuses"] == [
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    ]
    assert (
        export_manifest[
            "n_source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        == 1
    )
    assert export_manifest["n_proof_body_signature_probe_artifact_rows"] == 1
    assert export_manifest["n_proof_body_goal_context_rows"] == 1
    assert export_manifest["proof_body_goal_context_binder_names"] == [
        "hExch",
        "hq",
        "q",
    ]
    assert export_manifest["proof_body_goal_context_conclusions"] == [
        PROOF_BODY_GOAL_CONCLUSION
    ]
    assert export_manifest["proof_body_signature_probe_artifact_paths"] == [
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    ]
    assert export_manifest[
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]


def test_premise_bridge_prefers_artifact_semantic_requirements(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    source_attempt = tmp_path / "source_attempt.lean"
    source_attempt.write_text(
        "\n".join(
            [
                "import Mathlib",
                "theorem split_conformal_coverage",
                "    (hexch hq hC : Prop) :",
                "    True := by",
                "  trivial",
                "theorem split_conformal_coverage_source_to_bridge_adapter",
                "    (covered : Set Nat)",
                "    (hGoodCovered : covered ⊆ covered) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    retrieved_requirement = (
        "use retrieved formal source declaration "
        "LocalCoverage.coverage_event_definition as the semantic definition"
    )
    retrieved_binder = {
        "name": "hRetrievedCoverage",
        "type": "Prop",
        "role": "retrieved_formal_source_anchor",
    }
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                source_candidate_artifact_path=str(source_attempt),
                source_to_bridge_premise_derivation_candidate_request={
                    "candidate_request_id": (
                        "source_to_bridge_premise_derivation_candidate_request:"
                        "retrieved"
                    ),
                    "premise_name": "hGoodCovered",
                    "premise_semantic_dependency_requirements": [
                        retrieved_requirement
                    ],
                    "exact_source_theorem_binders": [retrieved_binder],
                    "premise_semantic_anchor_binders": [retrieved_binder],
                    "premise_semantic_anchor_binder_names": [
                        "hRetrievedCoverage"
                    ],
                    "required_semantic_anchor_reference_names": [
                        "hRetrievedCoverage"
                    ],
                    "adapter_object_names_requiring_source_instantiation": [
                        "covered"
                    ],
                    "proof_evidence_status": (
                        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
                    ),
                },
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    row = manifest["rows"][0]
    assert list(row["premise_semantic_dependency_requirements"]) == [
        retrieved_requirement
    ]
    assert list(row["exact_source_theorem_binders"]) == [retrieved_binder]
    assert list(row["premise_semantic_anchor_binders"]) == [retrieved_binder]
    assert list(row["premise_semantic_anchor_binder_names"]) == [
        "hRetrievedCoverage"
    ]
    candidate_source = Path(row["premise_candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert retrieved_requirement in candidate_source
    assert (
        "-- exact source binder: hRetrievedCoverage : Prop "
        "[retrieved_formal_source_anchor]"
    ) in candidate_source
    assert (
        "define covered from the exact source coverage event using hC"
        not in candidate_source
    )

    request = json.loads(
        Path(str(manifest["candidate_requests_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    assert request["premise_semantic_dependency_requirements"] == [
        retrieved_requirement
    ]
    assert request["exact_source_theorem_binders"] == [retrieved_binder]


def test_premise_bridge_checks_core_candidate_without_injecting_mathlib(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    candidate_source = (
        "theorem split_conformal_finite_sample_coverage_"
        "hGoodRankImpliesCovered_source_to_bridge_derivation\n"
        "    (good_rank_event coverage_event : Prop)\n"
        "    (hC : good_rank_event -> coverage_event)\n"
        "    (hGoodRank : good_rank_event) : coverage_event :=\n"
        "  hC hGoodRank"
    )
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                work_order_id=(
                    "source_to_bridge_premise_derivation_work_order:"
                    "hGoodRankImpliesCovered"
                ),
                premise_name="hGoodRankImpliesCovered",
                target_theorem_name="split_conformal_finite_sample_coverage",
                target_lean_declaration="split_conformal_finite_sample_coverage",
                source_candidate_artifact_path="",
                adapter_candidate_artifact_path="",
                adapter_declaration_name="",
                source_to_bridge_premise_derivation_candidate_request_id=(
                    "request:hGoodRankImpliesCovered"
                ),
                source_to_bridge_premise_derivation_candidate_request={
                    "candidate_request_id": "request:hGoodRankImpliesCovered",
                    "premise_name": "hGoodRankImpliesCovered",
                    "premise_target_type": "good_rank_event -> coverage_event",
                    "target_theorem_name": (
                        "split_conformal_finite_sample_coverage"
                    ),
                    "target_lean_declaration": (
                        "split_conformal_finite_sample_coverage"
                    ),
                    "exact_source_theorem_binders": [
                        {
                            "name": "hC",
                            "type": "good_rank_event -> coverage_event",
                        }
                    ],
                    "premise_semantic_anchor_binders": [
                        {
                            "name": "hC",
                            "role": "source coverage-event anchor",
                        }
                    ],
                    "premise_semantic_anchor_binder_names": ["hC"],
                    "required_semantic_anchor_reference_names": ["hC"],
                },
                premise_derivation_candidate_lean_source=candidate_source,
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=("true",),
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_premise_candidate_evidence_eligible"] == 1
    assert manifest["n_local_lean_checked"] == 1
    assert manifest["n_local_lean_compiled"] == 1
    assert manifest["n_premise_derivation_kernel_verified"] == 1
    assert manifest["by_failure_classification"] == {"none": 1}
    row = manifest["rows"][0]
    assert row["premise_candidate_evidence_eligible"] is True
    assert row["premise_candidate_references_semantic_anchor"] is True
    assert row["premise_derivation_kernel_verified"] is True
    assert row["failure_classification"] == ""
    materialized = Path(row["premise_candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert "import Mathlib" not in materialized
    assert "hC hGoodRank" in materialized


def test_premise_bridge_summarizes_local_lean_skipped_skeletons(tmp_path: Path) -> None:
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _premise_work_order(premise_name="hGoodCovered"),
            _premise_work_order(
                work_order_id="source_to_bridge_premise_derivation_work_order:hRank",
                premise_name="hRank",
                premise_target_type="∀ r ∈ BadRanks, P {ω | rank ω = r} ≤ α r",
            ),
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
    )

    assert manifest["n_work_orders"] == 2
    assert manifest["n_local_lean_checked"] == 0
    assert manifest["n_local_lean_skipped_not_evidence_eligible"] == 2
    assert manifest["n_premise_candidate_evidence_eligible"] == 0
    assert manifest["dominant_failure_classification"] == (
        "premise_derivation_candidate_missing_nonvacuous_source"
    )
    assert manifest["by_failure_classification"] == {
        "premise_derivation_candidate_missing_nonvacuous_source": 2
    }
    assert manifest["proof_evidence_status"] == (
        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_BRIDGE_NOT_PROOF_EVIDENCE"
    )


def test_premise_bridge_groups_shared_adapter_instantiation_requests(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    group_id = "source_to_bridge_adapter_instantiation_group:upstream-shared"
    upstream_grouped_request_id = (
        "source_to_bridge_grouped_premise_derivation_candidate_request:upstream"
    )
    upstream_grouped_request = {
        "schema_version": 1,
        "artifact_kind": "SourceToBridgeGroupedPremiseDerivationCandidateRequest",
        "grouped_candidate_request_id": upstream_grouped_request_id,
        "adapter_instantiation_group_id": group_id,
        "premise_names": ["hGoodCovered", "hRank"],
        "required_bridge_premise_names_for_shared_instantiation": [
            "hGoodCovered",
            "hRank",
        ],
        "shared_adapter_instantiation_contract": (
            "Use one upstream source-derived adapter instantiation."
        ),
        "upstream_marker": "runtime_grouped_request",
    }
    source_attempt = tmp_path / "source_attempt.lean"
    source_attempt.write_text(
        "\n".join(
            [
                "import Mathlib",
                "theorem split_conformal_coverage",
                "    (hexch hq hC : Prop) :",
                "    True := by",
                "  trivial",
                "theorem split_conformal_coverage_source_to_bridge_adapter",
                "    (covered : Set Nat)",
                "    (rank : Nat → Nat)",
                "    (BadRanks : Set Nat)",
                "    (hGoodCovered : covered ⊆ covered)",
                "    (hRank : True) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                work_order_id="source_to_bridge_premise_derivation_work_order:hGoodCovered",
                premise_name="hGoodCovered",
                source_candidate_artifact_path=str(source_attempt),
                adapter_instantiation_group_id=group_id,
                source_to_bridge_grouped_premise_derivation_candidate_request_id=(
                    upstream_grouped_request_id
                ),
                source_to_bridge_grouped_premise_derivation_candidate_request=(
                    upstream_grouped_request
                ),
            ),
            _premise_work_order(
                work_order_id="source_to_bridge_premise_derivation_work_order:hRank",
                premise_name="hRank",
                required_derivation="derive hRank from exact source theorem hypotheses",
                source_candidate_artifact_path=str(source_attempt),
                adapter_instantiation_group_id=group_id,
                source_to_bridge_grouped_premise_derivation_candidate_request_id=(
                    upstream_grouped_request_id
                ),
                source_to_bridge_grouped_premise_derivation_candidate_request=(
                    upstream_grouped_request
                ),
            ),
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    requests = [
        json.loads(line)
        for line in Path(str(manifest["candidate_requests_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    grouped_requests = [
        json.loads(line)
        for line in Path(str(manifest["grouped_candidate_requests_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(requests) == 2
    assert len(grouped_requests) == 1
    assert manifest["n_grouped_premise_derivation_candidate_requests"] == 1
    assert manifest["n_grouped_premise_derivation_learning_rows"] == 1
    group_ids = {request["adapter_instantiation_group_id"] for request in requests}
    assert group_ids == {group_id}
    assert manifest["adapter_instantiation_group_ids"] == list(group_ids)
    grouped_request = grouped_requests[0]
    assert grouped_request["grouped_candidate_request_id"] == upstream_grouped_request_id
    assert grouped_request["source_grouped_candidate_request_id"] == (
        upstream_grouped_request_id
    )
    assert grouped_request["source_grouped_candidate_request"]["upstream_marker"] == (
        "runtime_grouped_request"
    )
    assert grouped_request["premise_names"] == ["hGoodCovered", "hRank"]
    assert grouped_request[
        "required_bridge_premise_names_for_shared_instantiation"
    ] == ["hGoodCovered", "hRank"]
    assert grouped_request["source_theorem_kernel_evidence_eligible"] is True
    assert grouped_request["semantic_alignment_blockers"] == []
    assert grouped_request["proof_body_attempt_count"] == 1
    assert grouped_request["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert grouped_request["source_theorem_exact_proof_body_reached"] is True
    assert (
        grouped_request[
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        is True
    )
    assert grouped_request[
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert grouped_request["required_candidate_fields"] == [
        "premise_names",
        "adapter_instantiation_group_id",
        "target_theorem_name",
        "target_lean_declaration",
        "premise_derivation_candidate_lean_source",
    ]
    assert len(grouped_request["per_premise_candidate_requests"]) == 2
    assert "one source_to_bridge_premise_derivation_candidates object" in (
        grouped_request["candidate_contract"]
    )
    assert "required_semantic_anchor_reference_names" in grouped_request[
        "candidate_contract"
    ]
    assert "do not put adapter objects requiring source instantiation" in (
        grouped_request["candidate_contract"]
    )
    assert (
        "do not satisfy semantic-anchor requirements with comments or unused have/let aliases"
        in grouped_request["forbidden_actions"]
    )
    assert any(
        "do not put adapter objects" in action
        for action in grouped_request["forbidden_actions"]
    )
    for request in requests:
        assert request["source_grouped_candidate_request_id"] == (
            upstream_grouped_request_id
        )
        assert request["source_grouped_candidate_request"]["upstream_marker"] == (
            "runtime_grouped_request"
        )
        assert request[
            "required_bridge_premise_names_for_shared_instantiation"
        ] == ["hGoodCovered", "hRank"]
        assert request["shared_adapter_instantiation_contract"] == (
            "Use one upstream source-derived adapter instantiation."
        )
        assert request["proof_body_gate_status"] == (
            "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
        )
        assert (
            request[
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
            ]
            is True
        )
        assert request[
            "source_theorem_exact_proof_body_gate_open_target_names"
        ] == ["split_conformal_coverage"]
    learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    grouped_learning_rows = [
        row
        for row in learning_rows
        if row.get("learning_task")
        == "source_to_bridge_grouped_premise_derivation_candidate_request"
    ]
    assert len(grouped_learning_rows) == 1
    grouped_learning_row = grouped_learning_rows[0]
    assert grouped_learning_row["premise_names"] == ["hGoodCovered", "hRank"]
    assert grouped_learning_row["source_theorem_kernel_evidence_eligible"] is True
    assert grouped_learning_row["semantic_alignment_blockers"] == []
    assert grouped_learning_row["proof_body_attempt_count"] == 1
    assert grouped_learning_row["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert (
        grouped_learning_row[
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        is True
    )
    assert grouped_learning_row[
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert grouped_learning_row["adapter_instantiation_group_id"] == grouped_request[
        "adapter_instantiation_group_id"
    ]
    assert grouped_learning_row["runtime_queue_status"] == (
        "PENDING_GROUPED_SOURCE_TO_BRIDGE_PREMISE_DERIVATION"
    )
    assert (
        grouped_learning_row["source_to_bridge_grouped_premise_derivation_candidate_request_id"]
        == grouped_request["grouped_candidate_request_id"]
    )
    assert grouped_learning_row[
        "source_to_bridge_grouped_premise_derivation_candidate_request_id"
    ] == upstream_grouped_request_id
    assert grouped_learning_row[
        "source_to_bridge_grouped_premise_derivation_candidate_request"
    ]["source_grouped_candidate_request"]["upstream_marker"] == (
        "runtime_grouped_request"
    )
    learning_request = grouped_learning_row[
        "source_to_bridge_grouped_premise_derivation_candidate_request"
    ]
    assert "required_semantic_anchor_reference_names" in learning_request[
        "candidate_contract"
    ]
    assert (
        "do not satisfy semantic-anchor requirements with comments or unused have/let aliases"
        in learning_request["forbidden_actions"]
    )
    assert (
        grouped_learning_row["proof_evidence_status"]
        == "SOURCE_TO_BRIDGE_GROUPED_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
    )
    assert "not proof evidence" in grouped_learning_row["target_behavior"]


def test_premise_bridge_preserves_upstream_shared_instantiation_contract(
    tmp_path: Path,
) -> None:
    declaration = "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    group_id = "source_to_bridge_adapter_instantiation_group:upstream"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    source_attempt = tmp_path / "source_attempt.lean"
    source_attempt.write_text(
        "\n".join(
            [
                "import Mathlib",
                "theorem split_conformal_coverage",
                "    (hexch hq hC : Prop) :",
                "    True := by",
                "  trivial",
                "theorem split_conformal_coverage_source_to_bridge_adapter",
                "    (covered : Set Nat)",
                "    (rank : Nat → Nat)",
                "    (BadRanks : Set Nat)",
                "    (hGoodCovered : covered ⊆ covered)",
                "    (hRank : True) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                source_candidate_artifact_path=str(source_attempt),
                adapter_instantiation_group_id=group_id,
                required_bridge_premise_names_for_shared_instantiation=[
                    "hGoodCovered",
                    "hRank",
                ],
                shared_adapter_instantiation_contract=(
                    "Use one source-derived covered/rank/BadRanks instantiation."
                ),
                adapter_object_names_requiring_source_instantiation=[
                    "covered",
                    "rank",
                ],
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {declaration} "
                    "(covered : Set Nat) (rank : Nat → Nat) : "
                    "covered ⊆ covered := by\n"
                    "  intro x hx\n"
                    "  exact hx"
                ),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["adapter_instantiation_group_id"] == group_id
    assert list(row["required_bridge_premise_names_for_shared_instantiation"]) == [
        "hGoodCovered",
        "hRank",
    ]
    assert row["shared_adapter_instantiation_contract"] == (
        "Use one source-derived covered/rank/BadRanks instantiation."
    )
    assert list(row["adapter_object_names_requiring_source_instantiation"]) == [
        "covered",
        "rank",
    ]
    assert row["premise_candidate_uninstantiated_adapter_object_binders"] == (
        "covered",
        "rank",
    )
    assert row["local_lean_checked"] is False
    assert row["failure_classification"] == (
        "premise_derivation_candidate_uninstantiated_adapter_objects"
    )
    assert manifest["adapter_instantiation_group_ids"] == [group_id]
    request = json.loads(
        Path(str(manifest["candidate_requests_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    grouped_request = json.loads(
        Path(str(manifest["grouped_candidate_requests_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    assert request["adapter_instantiation_group_id"] == group_id
    assert request[
        "required_bridge_premise_names_for_shared_instantiation"
    ] == ["hGoodCovered", "hRank"]
    assert request["shared_adapter_instantiation_contract"] == (
        "Use one source-derived covered/rank/BadRanks instantiation."
    )
    assert request["adapter_object_names_requiring_source_instantiation"] == [
        "covered",
        "rank",
    ]
    assert grouped_request["adapter_instantiation_group_id"] == group_id
    assert grouped_request["premise_names"] == ["hGoodCovered"]
    assert grouped_request["adapter_object_names_requiring_source_instantiation"] == [
        "covered",
        "rank",
    ]
    assert (
        manifest["n_source_to_bridge_adapter_object_semantic_definition_work_orders"]
        == 2
    )
    assert manifest[
        "source_to_bridge_adapter_object_semantic_definition_placeholder_symbols"
    ] == ["covered", "rank"]
    semantic_work_orders = [
        json.loads(line)
        for line in Path(
            str(
                manifest[
                    "source_to_bridge_adapter_object_semantic_definition_work_orders_jsonl"
                ]
            )
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    semantic_by_symbol = {
        row["placeholder_symbol"]: row for row in semantic_work_orders
    }
    assert set(semantic_by_symbol) == {"covered", "rank"}
    assert semantic_by_symbol["covered"]["learning_task"] == (
        "source_theorem_exact_semantic_definition_work_order"
    )
    assert semantic_by_symbol["covered"]["proof_evidence_status"] == (
        "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    assert semantic_by_symbol["covered"]["target_ids"] == [
        "split_conformal_coverage"
    ]
    covered_request = semantic_by_symbol["covered"]["candidate_definition_request"]
    assert covered_request["placeholder_symbol"] == "covered"
    assert covered_request["target_ids"] == ["split_conformal_coverage"]
    assert covered_request[
        "source_to_bridge_adapter_instantiation_group_ids"
    ] == [group_id]
    assert semantic_by_symbol["covered"][
        "source_to_bridge_adapter_instantiation_group_id"
    ] == group_id
    assert semantic_by_symbol["covered"][
        "required_bridge_premise_names_for_shared_instantiation"
    ] == ["hGoodCovered", "hRank"]
    learning_row = json.loads(
        Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    assert learning_row["adapter_instantiation_group_id"] == group_id
    assert learning_row["target_ids"] == ["split_conformal_coverage"]
    assert learning_row[
        "required_bridge_premise_names_for_shared_instantiation"
    ] == ["hGoodCovered", "hRank"]
    assert learning_row["adapter_object_names_requiring_source_instantiation"] == [
        "covered",
        "rank",
    ]
    learning_grouped_request = learning_row[
        "source_to_bridge_grouped_premise_derivation_candidate_request"
    ]
    assert learning_grouped_request["adapter_instantiation_group_id"] == group_id
    assert learning_grouped_request["premise_names"] == ["hGoodCovered"]
    assert learning_row[
        "source_to_bridge_grouped_premise_derivation_candidate_request_id"
    ] == learning_grouped_request["grouped_candidate_request_id"]
    all_learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    semantic_learning_rows = [
        row
        for row in all_learning_rows
        if row.get("learning_task")
        == "source_theorem_exact_semantic_definition_work_order"
    ]
    assert [row["placeholder_symbol"] for row in semantic_learning_rows] == [
        "covered",
        "rank",
    ]


def test_premise_bridge_merges_adapter_object_definition_work_across_groups(
    tmp_path: Path,
) -> None:
    target = "split_conformal_coverage"
    group_a = "source_to_bridge_adapter_instantiation_group:covered"
    group_b = "source_to_bridge_adapter_instantiation_group:rank"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    source_attempt = tmp_path / "source_attempt.lean"
    source_attempt.write_text(
        "\n".join(
            [
                "import Mathlib",
                f"theorem {target}",
                "    (hexch hq hC : Prop) :",
                "    True := by",
                "  trivial",
                f"theorem {target}_source_to_bridge_adapter",
                "    (covered : Set Nat)",
                "    (rank : Nat → Nat)",
                "    (hCovered : covered ⊆ covered)",
                "    (hRank : True) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    candidate = (
        "import Mathlib\n\n"
        "theorem {declaration} "
        "(covered : Set Nat) (rank : Nat → Nat) : "
        "covered ⊆ covered := by\n"
        "  intro x hx\n"
        "  exact hx"
    )
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                work_order_id="source_to_bridge_premise_derivation_work_order:hCovered",
                premise_name="hCovered",
                source_candidate_artifact_path=str(source_attempt),
                adapter_instantiation_group_id=group_a,
                required_bridge_premise_names_for_shared_instantiation=[
                    "hCovered",
                ],
                shared_adapter_instantiation_contract=(
                    "Use reviewed definitions for covered and rank."
                ),
                adapter_object_names_requiring_source_instantiation=[
                    "covered",
                    "rank",
                ],
                forbidden_as_adapter_assumption=False,
                premise_derivation_candidate_lean_source=candidate.format(
                    declaration=f"{target}_hCovered_source_to_bridge_derivation"
                ),
            ),
            _premise_work_order(
                work_order_id="source_to_bridge_premise_derivation_work_order:hRank",
                premise_name="hRank",
                source_candidate_artifact_path=str(source_attempt),
                adapter_instantiation_group_id=group_b,
                required_bridge_premise_names_for_shared_instantiation=[
                    "hRank",
                ],
                shared_adapter_instantiation_contract=(
                    "Use reviewed definitions for covered and rank."
                ),
                adapter_object_names_requiring_source_instantiation=[
                    "covered",
                    "rank",
                ],
                forbidden_as_adapter_assumption=False,
                premise_derivation_candidate_lean_source=candidate.format(
                    declaration=f"{target}_hRank_source_to_bridge_derivation"
                ),
            ),
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    assert (
        manifest["n_source_to_bridge_adapter_object_semantic_definition_work_orders"]
        == 2
    )
    assert manifest[
        "source_to_bridge_adapter_object_semantic_definition_placeholder_symbols"
    ] == ["covered", "rank"]
    semantic_work_orders = [
        json.loads(line)
        for line in Path(
            str(
                manifest[
                    "source_to_bridge_adapter_object_semantic_definition_work_orders_jsonl"
                ]
            )
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    semantic_by_symbol = {
        row["placeholder_symbol"]: row for row in semantic_work_orders
    }
    for symbol in ("covered", "rank"):
        row = semantic_by_symbol[symbol]
        assert row["target_ids"] == ["split_conformal_coverage"]
        assert row["source_to_bridge_adapter_instantiation_group_id"] == group_a
        assert row["source_to_bridge_adapter_instantiation_group_ids"] == [
            group_a,
            group_b,
        ]
        assert row["candidate_definition_request"]["placeholder_symbol"] == symbol
        assert row["candidate_definition_request"]["target_ids"] == [
            "split_conformal_coverage"
        ]
        assert row["candidate_definition_request"][
            "source_to_bridge_adapter_instantiation_group_ids"
        ] == [group_a, group_b]
        assert row[
            "required_bridge_premise_names_for_shared_instantiation"
        ] == ["hCovered", "hRank"]
        assert row[
            "source_to_bridge_adapter_object_names_requiring_source_instantiation"
        ] == ["covered", "rank"]
        assert (
            len(
                row[
                    "source_to_bridge_grouped_premise_derivation_candidate_request_ids"
                ]
            )
            == 2
        )
        assert row["input_summary"][
            "source_to_bridge_adapter_instantiation_group_ids"
        ] == [group_a, group_b]

    all_learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    semantic_learning_rows = [
        row
        for row in all_learning_rows
        if row.get("learning_task")
        == "source_theorem_exact_semantic_definition_work_order"
    ]
    assert [row["placeholder_symbol"] for row in semantic_learning_rows] == [
        "covered",
        "rank",
    ]


def test_premise_bridge_checks_grouped_source_per_requested_declaration(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    grouped_source = (
        "import Mathlib\n\n"
        "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation "
        "(hexch hC source_hypotheses : Prop) "
        "(hsource : source_hypotheses) : source_hypotheses := by\n"
        "  have hGoodCovered : Prop := (fun h => h) hexch\n"
        "  exact hsource\n\n"
        "theorem split_conformal_coverage_hRank_source_to_bridge_derivation "
        "(rank : Nat → Nat) "
        "(source_hypotheses : Prop) "
        "(hsource : source_hypotheses) : source_hypotheses := by\n"
        "  have hRank : Prop := source_hypotheses\n"
        "  exact hsource"
    )
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                work_order_id=(
                    "source_to_bridge_premise_derivation_work_order:hGoodCovered"
                ),
                premise_name="hGoodCovered",
                forbidden_as_adapter_assumption=False,
                source_to_bridge_premise_derivation_candidate_request={
                    "premise_candidate_declaration_name": (
                        "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
                    ),
                    "required_semantic_anchor_reference_names": ["hexch"],
                    "adapter_object_names_requiring_source_instantiation": [],
                },
                premise_derivation_candidate_lean_source=grouped_source,
            ),
            _premise_work_order(
                work_order_id="source_to_bridge_premise_derivation_work_order:hRank",
                premise_name="hRank",
                required_derivation="derive hRank from exact source theorem hypotheses",
                forbidden_as_adapter_assumption=False,
                source_to_bridge_premise_derivation_candidate_request={
                    "premise_candidate_declaration_name": (
                        "split_conformal_coverage_hRank_source_to_bridge_derivation"
                    ),
                    "required_semantic_anchor_reference_names": ["hexch"],
                    "adapter_object_names_requiring_source_instantiation": ["rank"],
                },
                premise_derivation_candidate_lean_source=grouped_source,
            ),
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    rows = {row["premise_name"]: row for row in manifest["rows"]}
    assert rows["hGoodCovered"]["missing_premise_semantic_anchor_binder_names"] == ()
    assert rows["hGoodCovered"]["premise_candidate_uninstantiated_adapter_object_binders"] == ()
    assert rows["hGoodCovered"]["local_lean_checked"] is True
    assert rows["hGoodCovered"]["premise_derivation_kernel_verified"] is True
    assert rows["hRank"]["missing_premise_semantic_anchor_binder_names"] == (
        "hexch",
    )
    assert rows["hRank"]["premise_candidate_uninstantiated_adapter_object_binders"] == (
        "rank",
    )
    assert rows["hRank"]["local_lean_checked"] is False
    assert rows["hRank"]["premise_derivation_kernel_verified"] is False
    assert rows["hRank"]["failure_classification"] == (
        "premise_derivation_candidate_uninstantiated_adapter_objects"
    )
    assert manifest["n_premise_derivation_kernel_verified"] == 1


def test_premise_bridge_reads_grouped_candidate_source_from_nested_request(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    group_id = "source_to_bridge_adapter_instantiation_group:nested-source"
    grouped_request_id = (
        "source_to_bridge_grouped_premise_derivation_candidate_request:nested-source"
    )
    grouped_source = (
        "import Mathlib\n\n"
        "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation "
        "(hexch source_hypotheses : Prop) "
        "(hsource : source_hypotheses) : source_hypotheses := by\n"
        "  have hAnchor : hexch = hexch := rfl\n"
        "  have hGoodCovered : Prop := hexch\n"
        "  exact hsource\n\n"
        "theorem split_conformal_coverage_hRank_source_to_bridge_derivation "
        "(hexch source_hypotheses : Prop) "
        "(hsource : source_hypotheses) : source_hypotheses := by\n"
        "  have hAnchor : hexch = hexch := rfl\n"
        "  have hRank : Prop := hexch\n"
        "  exact hsource"
    )
    grouped_request = {
        "schema_version": 1,
        "artifact_kind": "SourceToBridgeGroupedPremiseDerivationCandidateRequest",
        "grouped_candidate_request_id": grouped_request_id,
        "adapter_instantiation_group_id": group_id,
        "premise_names": ["hGoodCovered", "hRank"],
        "required_bridge_premise_names_for_shared_instantiation": [
            "hGoodCovered",
            "hRank",
        ],
        "source_to_bridge_premise_derivation_candidates": [
            {
                "premise_names": ["hGoodCovered", "hRank"],
                "premise_derivation_candidate_lean_source": grouped_source,
            }
        ],
    }
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                work_order_id=(
                    "source_to_bridge_premise_derivation_work_order:hGoodCovered"
                ),
                premise_name="hGoodCovered",
                forbidden_as_adapter_assumption=False,
                adapter_instantiation_group_id=group_id,
                source_to_bridge_grouped_premise_derivation_candidate_request_id=(
                    grouped_request_id
                ),
                source_to_bridge_grouped_premise_derivation_candidate_request=(
                    grouped_request
                ),
                source_to_bridge_premise_derivation_candidate_request={
                    "premise_candidate_declaration_name": (
                        "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
                    ),
                    "required_semantic_anchor_reference_names": ["hexch"],
                    "adapter_object_names_requiring_source_instantiation": [],
                },
            ),
            _premise_work_order(
                work_order_id="source_to_bridge_premise_derivation_work_order:hRank",
                premise_name="hRank",
                forbidden_as_adapter_assumption=False,
                adapter_instantiation_group_id=group_id,
                source_to_bridge_grouped_premise_derivation_candidate_request_id=(
                    grouped_request_id
                ),
                source_to_bridge_grouped_premise_derivation_candidate_request=(
                    grouped_request
                ),
                source_to_bridge_premise_derivation_candidate_request={
                    "premise_candidate_declaration_name": (
                        "split_conformal_coverage_hRank_source_to_bridge_derivation"
                    ),
                    "required_semantic_anchor_reference_names": ["hexch"],
                    "adapter_object_names_requiring_source_instantiation": [],
                },
            ),
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    rows = {row["premise_name"]: row for row in manifest["rows"]}
    assert rows["hGoodCovered"]["premise_candidate_generation_mode"] == (
        "formalizer_provided_premise_derivation_candidate"
    )
    assert rows["hRank"]["premise_candidate_generation_mode"] == (
        "formalizer_provided_premise_derivation_candidate"
    )
    assert rows["hGoodCovered"]["local_lean_checked"] is True
    assert rows["hRank"]["local_lean_checked"] is True
    assert rows["hGoodCovered"]["premise_derivation_kernel_verified"] is True
    assert rows["hRank"]["premise_derivation_kernel_verified"] is True
    assert {
        rows["hGoodCovered"][
            "source_to_bridge_grouped_premise_derivation_candidate_request_id"
        ],
        rows["hRank"][
            "source_to_bridge_grouped_premise_derivation_candidate_request_id"
        ],
    } == {grouped_request_id}


def test_premise_bridge_parses_multi_binder_source_signature(tmp_path: Path) -> None:
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    source_attempt = tmp_path / "source_attempt.lean"
    source_attempt.write_text(
        "\n".join(
            [
                "import Mathlib",
                "theorem split_conformal_coverage {Ω : Type _} [MeasurableSpace Ω]",
                "    (P : MeasureTheory.Measure Ω) [MeasureTheory.IsProbabilityMeasure P]",
                "    (n2 : ℕ) (hn2 : 1 ≤ n2) (alpha : ℝ) (halpha : 0 < alpha ∧ alpha < 1)",
                "    (s : Fin (n2 + 1) → Ω → ℝ)",
                "    (hexch : Exchangeable P s)",
                "    (q_hat : Ω → ℝ)",
                "    (hq : q_hat = fun ω => orderStat s k ω)",
                "    (C : (Ω → ℝ) → Set ℝ)",
                "    (hC : ∀ ω, C (fun _ => s (Fin.last n2) ω) = {y | s (Fin.last n2) ω ≤ q_hat ω}) :",
                "    True := by",
                "  trivial",
                "theorem split_conformal_coverage_source_to_bridge_adapter",
                "    (covered : Set Nat)",
                "    (hGoodCovered : covered ⊆ covered) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        queue,
        [_premise_work_order(source_candidate_artifact_path=str(source_attempt))],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    row = manifest["rows"][0]
    source_binders = {binder["name"]: binder["type"] for binder in row["exact_source_theorem_binders"]}
    assert source_binders["n2"] == "ℕ"
    assert source_binders["hn2"] == "1 ≤ n2"
    assert source_binders["alpha"] == "ℝ"
    assert source_binders["halpha"] == "0 < alpha ∧ alpha < 1"
    assert source_binders["hC"].startswith("∀ ω, C")
    candidate_source = Path(row["premise_candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert "-- exact source binder: hn2 : 1 ≤ n2 [calibration_size_anchor]" in (
        candidate_source
    )
    assert "-- exact source binder: alpha : ℝ [miscoverage_level_anchor]" in (
        candidate_source
    )
    assert "-- exact source binder: n2 : ℕ) (hn2" not in candidate_source


def test_premise_bridge_rejects_candidate_that_reassumes_premise(
    tmp_path: Path,
) -> None:
    declaration = "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {declaration} "
                    "(source_hypotheses bridge_premise : Prop) "
                    "(hsource : source_hypotheses) "
                    "(hGoodCovered : bridge_premise) : bridge_premise := by\n"
                    "  exact hGoodCovered"
                )
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_requested"] is True
    assert row["local_lean_checked"] is False
    assert row["local_lean_compiled"] is False
    assert row["premise_candidate_assumes_forbidden_premise"] is True
    assert row["premise_candidate_evidence_eligible"] is False
    assert row["premise_derivation_kernel_verified"] is False
    assert row["failure_classification"] == (
        "premise_derivation_candidate_assumes_forbidden_premise"
    )
    assert "not evidence eligible" in row["diagnostics"][0]
    assert manifest["n_premise_derivation_kernel_verified"] == 0
    assert manifest["source_theorem_kernel_verified"] is False


def test_premise_bridge_rejects_uninstantiated_adapter_object_binders(
    tmp_path: Path,
) -> None:
    declaration = "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                forbidden_as_adapter_assumption=False,
                source_to_bridge_premise_derivation_candidate_request={
                    "candidate_request_id": (
                        "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
                    ),
                    "premise_candidate_declaration_name": declaration,
                    "adapter_object_names_requiring_source_instantiation": [
                        "covered"
                    ],
                    "bridge_object_instantiation_policy": (
                        "covered must be defined from the exact source theorem"
                    ),
                    "proof_evidence_status": (
                        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
                    ),
                },
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {declaration} "
                    "(covered : Set Nat) : covered ⊆ covered := by\n"
                    "  intro x hx\n"
                    "  exact hx"
                ),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_requested"] is True
    assert row["local_lean_checked"] is False
    assert row["local_lean_compiled"] is False
    assert row["premise_candidate_uninstantiated_adapter_object_binders"] == (
        "covered",
    )
    assert row["premise_candidate_evidence_eligible"] is False
    assert row["premise_derivation_kernel_verified"] is False
    assert row["failure_classification"] == (
        "premise_derivation_candidate_uninstantiated_adapter_objects"
    )
    assert row["premise_derivation_gap_kind"] == (
        "premise_derivation_uninstantiated_adapter_objects"
    )
    assert "covered" in row["premise_derivation_gap_summary"]
    assert "not evidence eligible" in row["diagnostics"][0]
    assert manifest[
        "n_premise_candidate_uninstantiated_adapter_object_binders"
    ] == 1
    assert manifest["n_premise_derivation_kernel_verified"] == 0
    assert manifest["source_theorem_kernel_verified"] is False


def test_premise_bridge_rejects_candidate_without_source_binding_contract(
    tmp_path: Path,
) -> None:
    declaration = "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                forbidden_as_adapter_assumption=False,
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {declaration} "
                    "(source_hypotheses : Prop) "
                    "(hsource : source_hypotheses) : source_hypotheses := by\n"
                    "  exact hsource"
                ),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_requested"] is True
    assert row["local_lean_checked"] is False
    assert row["local_lean_compiled"] is False
    assert row["premise_candidate_evidence_eligible"] is False
    assert row["premise_derivation_kernel_verified"] is False
    assert row["failure_classification"] == (
        "premise_derivation_candidate_missing_source_binding_contract"
    )
    assert row["premise_derivation_gap_kind"] == (
        "premise_derivation_missing_source_binding_contract"
    )
    assert "source-to-bridge candidate request" in row[
        "premise_derivation_gap_summary"
    ]
    assert "not evidence eligible" in row["diagnostics"][0]
    assert manifest["n_local_lean_checked"] == 0
    assert manifest["n_local_lean_skipped_not_evidence_eligible"] == 1
    assert manifest["n_premise_derivation_kernel_verified"] == 0
    assert manifest["source_theorem_kernel_verified"] is False


def test_premise_bridge_rejects_candidate_that_reassumes_premise_target_type(
    tmp_path: Path,
) -> None:
    declaration = "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    source_attempt = tmp_path / "source_attempt.lean"
    source_attempt.write_text(
        "\n".join(
            [
                "import Mathlib",
                "theorem split_conformal_coverage",
                "    (hexch hq hC : Prop) :",
                "    True := by",
                "  trivial",
                "theorem split_conformal_coverage_source_to_bridge_adapter",
                "    (covered : Set Nat)",
                "    (hGoodCovered : covered ⊆ covered) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                source_candidate_artifact_path=str(source_attempt),
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {declaration} "
                    "(covered : Set Nat) "
                    "(renamedBridgePremise : covered ⊆ covered) : "
                    "covered ⊆ covered := by\n"
                    "  exact renamedBridgePremise"
                ),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_requested"] is True
    assert row["local_lean_checked"] is False
    assert row["local_lean_compiled"] is False
    assert row["premise_target_type"] == "covered ⊆ covered"
    assert row["premise_candidate_assumes_forbidden_premise"] is True
    assert row["premise_candidate_evidence_eligible"] is False
    assert row["premise_derivation_kernel_verified"] is False
    assert row["failure_classification"] == (
        "premise_derivation_candidate_assumes_forbidden_premise"
    )
    assert "not evidence eligible" in row["diagnostics"][0]
    assert manifest["n_premise_derivation_kernel_verified"] == 0
    assert manifest["source_theorem_kernel_verified"] is False


def test_premise_bridge_enforces_candidate_request_declaration_name(
    tmp_path: Path,
) -> None:
    requested_declaration = (
        "split_conformal_coverage_requested_hGoodCovered_derivation"
    )
    wrong_declaration = (
        "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    )
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                forbidden_as_adapter_assumption=False,
                source_to_bridge_premise_derivation_candidate_request_id=(
                    "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
                ),
                source_to_bridge_premise_derivation_candidate_request={
                    "candidate_request_id": (
                        "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
                    ),
                    "premise_candidate_declaration_name": requested_declaration,
                    "proof_evidence_status": (
                        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
                    ),
                },
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {wrong_declaration} "
                    "(source_hypotheses bridge_premise : Prop) "
                    "(hsource : source_hypotheses) "
                    "(hGoodCovered : bridge_premise) : bridge_premise := by\n"
                    "  exact hGoodCovered"
                ),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_requested"] is True
    assert row["local_lean_checked"] is False
    assert row["local_lean_compiled"] is False
    assert row["premise_candidate_declaration_name"] == requested_declaration
    assert row["premise_candidate_evidence_eligible"] is False
    assert row["premise_derivation_kernel_verified"] is False
    assert row["failure_classification"] == (
        "premise_derivation_candidate_wrong_declaration"
    )
    assert "not evidence eligible" in row["diagnostics"][0]
    assert row[
        "source_to_bridge_premise_derivation_candidate_request_id"
    ] == "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
    assert manifest["n_premise_derivation_kernel_verified"] == 0
    assert manifest["source_theorem_kernel_verified"] is False


def test_premise_bridge_rejects_candidate_missing_semantic_anchor_reference(
    tmp_path: Path,
) -> None:
    declaration = "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                forbidden_as_adapter_assumption=False,
                source_to_bridge_premise_derivation_candidate_request_id=(
                    "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
                ),
                source_to_bridge_premise_derivation_candidate_request={
                    "candidate_request_id": (
                        "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
                    ),
                    "premise_candidate_declaration_name": declaration,
                    "exact_source_theorem_binders": [
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
                    "proof_evidence_status": (
                        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
                    ),
                },
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {declaration} "
                    "(source_hypotheses bridge_premise : Prop) "
                    "(hsource : source_hypotheses) "
                    "(hGoodCoveredCandidate : bridge_premise) : bridge_premise := by\n"
                    "  exact hGoodCoveredCandidate"
                ),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_requested"] is True
    assert row["local_lean_checked"] is False
    assert row["local_lean_compiled"] is False
    assert row["premise_candidate_references_semantic_anchor"] is False
    assert row["missing_premise_semantic_anchor_binder_names"] == ("hq", "hC")
    assert row["premise_candidate_evidence_eligible"] is False
    assert row["premise_derivation_kernel_verified"] is False
    assert row["failure_classification"] == (
        "premise_derivation_candidate_missing_semantic_anchor_reference"
    )
    assert row["premise_derivation_gap_kind"] == (
        "premise_derivation_missing_semantic_anchor_reference"
    )
    assert "hq, hC" in row["premise_derivation_gap_summary"]
    assert "not evidence eligible" in row["diagnostics"][0]
    assert manifest["n_premise_derivation_kernel_verified"] == 0
    assert manifest["source_theorem_kernel_verified"] is False


def test_premise_bridge_requires_semantic_anchor_reference_in_proof_body(
    tmp_path: Path,
) -> None:
    declaration = "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                forbidden_as_adapter_assumption=False,
                source_to_bridge_premise_derivation_candidate_request={
                    "candidate_request_id": (
                        "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
                    ),
                    "premise_candidate_declaration_name": declaration,
                    "premise_semantic_anchor_binder_names": ["hq", "hC"],
                    "required_semantic_anchor_reference_names": ["hq", "hC"],
                    "proof_evidence_status": (
                        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
                    ),
                },
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {declaration} "
                    "(source_hypotheses bridge_premise : Prop) "
                    "(hq hC : source_hypotheses) "
                    "(hGoodCoveredCandidate : bridge_premise) : bridge_premise := by\n"
                    "  exact hGoodCoveredCandidate"
                ),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_requested"] is True
    assert row["local_lean_checked"] is False
    assert row["premise_candidate_references_semantic_anchor"] is False
    assert row["missing_premise_semantic_anchor_binder_names"] == ("hq", "hC")
    assert row["failure_classification"] == (
        "premise_derivation_candidate_missing_semantic_anchor_reference"
    )
    assert manifest["n_premise_derivation_kernel_verified"] == 0
    assert manifest["source_theorem_kernel_verified"] is False


def test_premise_bridge_rejects_noop_semantic_anchor_references(
    tmp_path: Path,
) -> None:
    declaration = "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                forbidden_as_adapter_assumption=False,
                source_to_bridge_premise_derivation_candidate_request={
                    "candidate_request_id": (
                        "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
                    ),
                    "premise_candidate_declaration_name": declaration,
                    "premise_semantic_anchor_binder_names": ["hq", "hC"],
                    "required_semantic_anchor_reference_names": ["hq", "hC"],
                    "proof_evidence_status": (
                        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
                    ),
                },
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {declaration} "
                    "(source_hypotheses bridge_premise : Prop) "
                    "(hq hC : source_hypotheses) "
                    "(hGoodCoveredCandidate : bridge_premise) : bridge_premise := by\n"
                    "  have _ := hq\n"
                    "  have anchorCopy := hC\n"
                    "  exact hGoodCoveredCandidate"
                ),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_requested"] is True
    assert row["local_lean_checked"] is False
    assert row["premise_candidate_references_semantic_anchor"] is False
    assert row["missing_premise_semantic_anchor_binder_names"] == ("hq", "hC")
    assert row["failure_classification"] == (
        "premise_derivation_candidate_missing_semantic_anchor_reference"
    )
    assert manifest["n_premise_derivation_kernel_verified"] == 0
    assert manifest["source_theorem_kernel_verified"] is False


def test_premise_bridge_marks_nonvacuous_candidate_verified_with_local_lean(
    tmp_path: Path,
) -> None:
    declaration = "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    queue = tmp_path / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _premise_work_order(
                forbidden_as_adapter_assumption=False,
                source_to_bridge_premise_derivation_candidate_request_id=(
                    "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
                ),
                source_to_bridge_premise_derivation_candidate_request={
                    "candidate_request_id": (
                        "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
                    ),
                    "premise_candidate_declaration_name": declaration,
                    "proof_evidence_status": (
                        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
                    ),
                },
                premise_derivation_candidate_lean_source=(
                    "import Mathlib\n\n"
                    f"theorem {declaration} "
                    "(source_hypotheses bridge_premise : Prop) "
                    "(hsource : source_hypotheses) "
                    "(hGoodCovered : bridge_premise) : bridge_premise := by\n"
                    "  exact hGoodCovered"
                ),
            )
        ],
    )

    manifest = run_source_to_bridge_premise_derivation_proofengineer_bridge(
        out_dir=tmp_path / "premise_bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["premise_candidate_assumes_forbidden_premise"] is False
    assert row["premise_candidate_evidence_eligible"] is True
    assert row["premise_derivation_kernel_verified"] is True
    assert row[
        "source_to_bridge_premise_derivation_candidate_request_id"
    ] == "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
    assert row[
        "source_to_bridge_premise_derivation_candidate_request"
    ]["premise_candidate_declaration_name"] == declaration
    assert row["source_theorem_kernel_verified"] is False
    assert row["proof_evidence_status"] == (
        "KERNEL_VERIFIED_SOURCE_TO_BRIDGE_PREMISE_DERIVATIONS_PRESENT"
    )
    assert manifest["n_premise_derivation_kernel_verified"] == 1
    assert manifest["source_theorem_kernel_verified"] is False
    learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert learning_rows[0]["runtime_queue_status"] == (
        "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_KERNEL_VERIFIED"
    )
    assert learning_rows[0][
        "source_to_bridge_premise_derivation_source_candidate_request_id"
    ] == "source_to_bridge_premise_derivation_candidate_request:hGoodCovered"
    assert learning_rows[0][
        "source_to_bridge_premise_derivation_source_candidate_request"
    ]["premise_candidate_declaration_name"] == declaration
    assert learning_rows[0][
        "source_to_bridge_premise_derivation_candidate_request"
    ] == {}
    assert learning_rows[0]["source_theorem_kernel_verified"] is False

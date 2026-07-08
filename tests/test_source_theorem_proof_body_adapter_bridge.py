from __future__ import annotations

from argparse import Namespace
import json
import sys
from pathlib import Path

from ai_statistician.cli import _research_agent_runtime_capability_config_errors, main
from ai_statistician.source_theorem_proof_body_adapter_proofengineer_bridge import (
    resolve_source_theorem_proof_body_adapter_queue_path,
    run_source_theorem_proof_body_adapter_proofengineer_bridge,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def _adapter_work_order(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremPromotionWorkOrder",
        "work_order_id": "source_theorem_promotion_work_order:adapter",
        "proof_mode": "source_theorem_proof_body_adapter_required",
        "action_type": "derive_source_theorem_proof_body_adapter",
        "question_id": "conformal_prediction_coverage",
        "source_formalization_manifest_id": "formalization_manifest:source_adapter",
        "source_formalizer_packet_id": "formalizer:source-adapter",
        "source_formal_target_id": "target:source-adapter",
        "target_theorem_name": "split_conformal_coverage",
        "target_ids": ["split_conformal_finite_sample_coverage"],
        "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
        "source_theorem_target_known": True,
        "source_theorem_target_provenance": {
            "source_theorem_target_known": True,
            "target_lean_declaration": "split_conformal_coverage",
            "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
        },
        "proof_body_candidate_artifact_path": "runs/split_conformal_coverage_attempt.lean",
        "proof_body_signature_probe_artifact_path": (
            "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
        ),
        "source_theorem_signature_probe_artifact_path": (
            "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
        ),
        "proof_body_goal_excerpt": [
            "hexch : Exchangeable P s",
            "hq : ∀ᵐ (ω : Ω) ∂P, ↑{i | s i.castSucc ω ≤ q_hat ω}.card / ↑n ≥ 1 - alpha",
            "hC : ∀ (ω : Ω), (C fun x => s (Fin.last n2) ω) = {y | s (Fin.last n2) ω ≤ q_hat ω}",
            "⊢ 1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧",
        ],
        "proof_body_attempt_summaries": ["1:simpa:returncode=1:compiled=False"],
        "proof_body_attempt_count": 1,
        "proof_body_adapter_required": True,
        "proof_body_adapter_required_reasons": [
            "proof body goal exposes source-level hypotheses but no reusable bridge/reduction hypothesis",
            "reviewed semantic-alignment constraints identify exchangeability/rank/quantile bridge structure needed by an adapter",
        ],
        "semantic_alignment_constraints": [
            "Exchangeable predicate must permute all n2+1 indices jointly under P, not just pairwise",
            "orderStat must match the conformal quantile rank and tie policy",
        ],
        "semantic_alignment_blockers": [],
        "source_theorem_kernel_evidence_eligible": True,
        "kernel_verified_theorem_reduction_closure_target_ids": [
            "split_conformal_finite_sample_coverage_reduction_closure"
        ],
        "kernel_verified_theorem_reduction_closure_declarations": [
            "splitConformalFiniteSampleCoverage_reductionClosure"
        ],
        "verified_theorem_reduction_closure_artifact_paths": [
            "runs/theorem_reduction_closure/closure.lean"
        ],
        "kernel_verified_source_theorem_semantic_support_obligation_ids": [
            "split_conformal_good_rank_set_inclusion_bridge"
        ],
        "runtime_queue_status": "PENDING_SOURCE_THEOREM_PROOF_BODY_ADAPTER",
        "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
    }
    row.update(overrides)
    return row


def test_adapter_bridge_resolves_runtime_manifest_queue(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runs" / "live_runtime"
    runtime_dir.mkdir(parents=True)
    queue = runtime_dir / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(queue, [_adapter_work_order()])
    (runtime_dir / "research_agent_runtime_manifest.json").write_text(
        json.dumps(
            {
                "artifacts": {
                    "runtime_source_theorem_proof_body_adapter_work_orders_jsonl": str(
                        queue.relative_to(tmp_path)
                    )
                }
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_source_theorem_proof_body_adapter_queue_path(
        runtime_dir=runtime_dir
    )

    assert resolved == queue


def test_adapter_bridge_materializes_nonproof_skeleton(tmp_path: Path) -> None:
    queue = tmp_path / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            _adapter_work_order(
                proof_body_gate_status="PROOF_BODY_REACHED_PROOF_INCOMPLETE",
                source_theorem_exact_proof_body_reached=True,
                source_theorem_exact_proof_body_gate_open_for_kernel_repair=True,
                source_theorem_exact_proof_body_gate_open_target_names=[
                    "split_conformal_coverage"
                ],
                source_to_bridge_premise_derivation_work_items=[
                    {
                        "premise_name": "hGoodCovered",
                        "required_derivation": (
                            "derive hGoodCovered from exact source hypotheses"
                        ),
                        "forbidden_as_adapter_assumption": True,
                        "proof_evidence_status": "WORK_ITEM_NOT_PROOF_EVIDENCE",
                    }
                ]
            )
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_adapter_check_rows"] == 1
    assert manifest["n_adapter_kernel_verified"] == 0
    assert manifest["n_source_to_bridge_premise_derivation_work_items"] == 1
    assert manifest["n_source_to_bridge_premise_derivation_queue_rows"] == 1
    assert (
        manifest["n_source_theorem_exact_proof_body_gate_open_for_kernel_repair"]
        == 1
    )
    assert manifest["source_theorem_exact_proof_body_gate_open_target_names"] == [
        "split_conformal_coverage"
    ]
    assert manifest["n_proof_body_signature_probe_artifact_rows"] == 1
    assert manifest["n_proof_body_goal_context_rows"] == 1
    assert manifest["proof_body_goal_context_binder_names"] == [
        "hC",
        "hexch",
        "hq",
    ]
    assert manifest["proof_body_goal_context_conclusions"] == [
        "1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧"
    ]
    assert manifest["proof_body_signature_probe_artifact_paths"] == [
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    ]
    assert manifest["source_theorem_kernel_verified"] is False
    assert manifest["proof_evidence_status"] == (
        "SOURCE_THEOREM_PROOF_BODY_ADAPTER_BRIDGE_NOT_PROOF_EVIDENCE"
    )
    row = manifest["rows"][0]
    assert list(row["target_ids"]) == ["split_conformal_finite_sample_coverage"]
    assert list(row["target_theorem_goal_ids"]) == [
        "split_conformal_finite_sample_coverage"
    ]
    assert row["adapter_generation_mode"] == "proofengineer_generated_adapter_skeleton"
    assert row["adapter_candidate_evidence_eligible"] is False
    assert row["source_candidate_artifact_path"] == (
        "runs/split_conformal_coverage_attempt.lean"
    )
    assert row["proof_body_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert row["source_theorem_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert row["failure_classification"] == "adapter_candidate_not_evidence_eligible"
    assert row["source_theorem_kernel_evidence_eligible"] is True
    assert row["proof_body_gate_status"] == "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    assert row["source_theorem_exact_proof_body_reached"] is True
    assert (
        row["source_theorem_exact_proof_body_gate_open_for_kernel_repair"]
        is True
    )
    assert row["source_theorem_exact_proof_body_gate_open_target_names"] == (
        "split_conformal_coverage",
    )
    assert row["semantic_alignment_blockers"] == ()
    assert row["proof_body_attempt_count"] == 1
    assert row["proof_body_goal_binder_names"] == ("hexch", "hq", "hC")
    assert row["proof_body_goal_conclusion"] == (
        "1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧"
    )
    assert row["proof_body_goal_context"]["hypothesis_rows"][0]["binder_name"] == (
        "hexch"
    )
    assert row["proof_body_goal_context"]["proof_evidence_status"] == (
        "PROOF_BODY_GOAL_CONTEXT_NOT_PROOF_EVIDENCE"
    )
    assert row["source_to_bridge_premise_derivation_work_items"][0][
        "premise_name"
    ] == "hGoodCovered"
    assert row["source_to_bridge_premise_derivation_work_items"][0][
        "proof_body_goal_binder_names"
    ] == ["hexch", "hq", "hC"]
    adapter_source = Path(row["adapter_candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert "fail_if_success trivial" in adapter_source
    assert "source-level hypotheses" in adapter_source
    assert (
        "-- source proof-body candidate artifact: "
        "runs/split_conformal_coverage_attempt.lean"
    ) in adapter_source
    assert (
        "-- source theorem signature probe artifact: "
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    ) in adapter_source
    assert (
        "-- verified reduction/closure target id: "
        "split_conformal_finite_sample_coverage_reduction_closure"
    ) in adapter_source
    assert (
        "-- verified reduction/closure Lean declaration: "
        "splitConformalFiniteSampleCoverage_reductionClosure"
    ) in adapter_source
    assert (
        "-- verified reduction/closure artifact: "
        "runs/theorem_reduction_closure/closure.lean"
    ) in adapter_source
    assert (
        "-- verified semantic support obligation id: "
        "split_conformal_good_rank_set_inclusion_bridge"
    ) in adapter_source
    assert "-- source-to-bridge premise work item: hGoodCovered" in adapter_source
    assert (
        "-- required derivation: derive hGoodCovered from exact source hypotheses"
        in adapter_source
    )
    assert "-- forbidden as adapter assumption: true" in adapter_source
    assert "-- proof-body attempt: 1:simpa:returncode=1:compiled=False" in adapter_source
    assert "-- proof-body attempt count: 1" in adapter_source
    assert (
        "-- proof-body gate status: PROOF_BODY_REACHED_PROOF_INCOMPLETE"
        in adapter_source
    )
    assert "-- proof-body goal binder: hexch" in adapter_source
    assert "-- proof-body goal binder: hq" in adapter_source
    assert "-- proof-body goal binder: hC" in adapter_source
    assert (
        "-- proof-body goal conclusion: 1 - alpha ≤ P.real "
        "{ω | s (Fin.last n2) ω ≤ q_hat ω} ∧"
    ) in adapter_source
    assert (
        "-- exact source proof-body gate open for kernel repair: true"
        in adapter_source
    )
    assert (
        "-- exact source proof-body gate-open target: split_conformal_coverage"
        in adapter_source
    )
    assert (
        "-- source theorem kernel evidence eligible before adapter: true"
        in adapter_source
    )
    assert "materialize/import the missing dependency context" in adapter_source
    learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    learning_export_manifest = json.loads(
        Path(str(manifest["runtime_learning_export_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    premise_queue_manifest = json.loads(
        Path(str(manifest["source_to_bridge_premise_derivation_queue_manifest"]))
        .read_text(encoding="utf-8")
    )
    premise_queue_rows = [
        json.loads(line)
        for line in Path(str(manifest["source_to_bridge_premise_derivation_queue_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert (
        learning_export_manifest[
            "n_source_to_bridge_premise_derivation_work_items"
        ]
        == 1
    )
    assert (
        learning_export_manifest[
            "n_source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        == 1
    )
    assert learning_export_manifest[
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert learning_export_manifest["n_proof_body_signature_probe_artifact_rows"] == 1
    assert learning_export_manifest["n_proof_body_goal_context_rows"] == 1
    assert learning_export_manifest["proof_body_goal_context_binder_names"] == [
        "hC",
        "hexch",
        "hq",
    ]
    assert learning_export_manifest["proof_body_signature_probe_artifact_paths"] == [
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    ]
    assert learning_rows[0]["target_ids"] == [
        "split_conformal_finite_sample_coverage"
    ]
    assert learning_rows[0]["input_summary"]["target_ids"] == [
        "split_conformal_finite_sample_coverage"
    ]
    assert premise_queue_manifest["n_queue_rows"] == 1
    assert (
        premise_queue_manifest[
            "n_source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        == 1
    )
    assert premise_queue_manifest[
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert premise_queue_manifest["n_proof_body_signature_probe_artifact_rows"] == 1
    assert premise_queue_manifest["n_proof_body_goal_context_rows"] == 1
    assert premise_queue_manifest["proof_body_goal_context_binder_names"] == [
        "hC",
        "hexch",
        "hq",
    ]
    assert premise_queue_manifest["proof_body_signature_probe_artifact_paths"] == [
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    ]
    assert premise_queue_manifest["proof_evidence_status"] == (
        "WORK_ORDER_QUEUE_NOT_PROOF_EVIDENCE"
    )
    assert premise_queue_rows[0]["artifact_kind"] == (
        "SourceToBridgePremiseDerivationWorkOrder"
    )
    assert premise_queue_rows[0]["premise_name"] == "hGoodCovered"
    assert premise_queue_rows[0]["source_candidate_artifact_path"] == (
        "runs/split_conformal_coverage_attempt.lean"
    )
    assert premise_queue_rows[0]["proof_body_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert premise_queue_rows[0]["source_theorem_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert premise_queue_rows[0]["signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert premise_queue_rows[0]["source_theorem_kernel_evidence_eligible"] is True
    assert premise_queue_rows[0]["semantic_alignment_blockers"] == []
    assert premise_queue_rows[0]["proof_body_attempt_count"] == 1
    assert premise_queue_rows[0]["proof_body_goal_binder_names"] == [
        "hexch",
        "hq",
        "hC",
    ]
    assert premise_queue_rows[0]["source_to_bridge_premise_goal_binder_names"] == [
        "hexch",
        "hq",
        "hC",
    ]
    assert premise_queue_rows[0]["source_to_bridge_premise_goal_conclusion"] == (
        "1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧"
    )
    assert premise_queue_rows[0]["source_to_bridge_premise_goal_context"][
        "proof_evidence_status"
    ] == "PROOF_BODY_GOAL_CONTEXT_NOT_PROOF_EVIDENCE"
    assert premise_queue_rows[0]["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert premise_queue_rows[0]["source_theorem_exact_proof_body_reached"] is True
    assert (
        premise_queue_rows[0][
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        is True
    )
    assert premise_queue_rows[0][
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert premise_queue_rows[0]["forbidden_as_adapter_assumption"] is True
    assert premise_queue_rows[0]["proof_evidence_status"] == (
        "WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    assert len(learning_rows) == 1
    assert learning_rows[0]["learning_task"] == (
        "source_theorem_proof_body_adapter_feedback"
    )
    assert learning_rows[0]["adapter_kernel_verified"] is False
    assert learning_rows[0]["source_theorem_kernel_verified"] is False
    assert learning_rows[0]["proof_body_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert learning_rows[0]["source_theorem_signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert learning_rows[0]["signature_probe_artifact_path"] == (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    assert learning_rows[0]["source_theorem_kernel_evidence_eligible"] is True
    assert learning_rows[0]["semantic_alignment_blockers"] == []
    assert learning_rows[0]["proof_body_attempt_count"] == 1
    assert learning_rows[0]["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
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
    assert learning_rows[0]["proof_body_attempt_summaries"] == [
        "1:simpa:returncode=1:compiled=False"
    ]
    assert learning_rows[0]["proof_body_goal_binder_names"] == [
        "hexch",
        "hq",
        "hC",
    ]
    assert learning_rows[0]["proof_body_goal_context"]["conclusion"] == (
        "1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧"
    )
    assert learning_rows[0]["input_summary"][
        "source_theorem_kernel_evidence_eligible"
    ] is True
    assert learning_rows[0]["input_summary"][
        "proof_body_signature_probe_artifact_path"
    ] == "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    assert learning_rows[0]["input_summary"][
        "source_theorem_signature_probe_artifact_path"
    ] == "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    assert learning_rows[0]["input_summary"]["proof_body_attempt_count"] == 1
    assert learning_rows[0]["input_summary"]["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert learning_rows[0]["input_summary"]["proof_body_goal_binder_names"] == [
        "hexch",
        "hq",
        "hC",
    ]
    assert (
        learning_rows[0]["input_summary"][
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
        ]
        is True
    )
    assert learning_rows[0]["source_to_bridge_premise_derivation_work_items"][0][
        "premise_name"
    ] == "hGoodCovered"


def test_adapter_bridge_consumes_verified_premise_derivation_context(
    tmp_path: Path,
) -> None:
    premise_artifact = tmp_path / "premise_derivations" / "hGoodCovered.lean"
    premise_artifact.parent.mkdir(parents=True)
    premise_artifact.write_text(
        "\n".join(
            [
                "import Mathlib",
                "",
                "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    queue = tmp_path / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            _adapter_work_order(
                source_to_bridge_premise_derivation_all_required_verified=True,
                kernel_verified_source_to_bridge_premise_derivation_ids=[
                    "source_to_bridge_premise_derivation_check:hGoodCovered"
                ],
                verified_source_to_bridge_premise_derivation_artifact_paths=[
                    str(premise_artifact)
                ],
                verified_source_to_bridge_premise_derivation_declarations=[
                    "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
                ],
                source_to_bridge_premise_derivation_work_items=[],
            )
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_source_to_bridge_premise_derivation_queue_rows"] == 0
    assert manifest["n_kernel_verified_source_to_bridge_premise_derivation_ids"] == 1
    assert manifest["kernel_verified_source_to_bridge_premise_derivation_ids"] == [
        "source_to_bridge_premise_derivation_check:hGoodCovered"
    ]
    row = manifest["rows"][0]
    assert list(row["source_to_bridge_premise_derivation_work_items"]) == []
    assert list(row["kernel_verified_source_to_bridge_premise_derivation_ids"]) == [
        "source_to_bridge_premise_derivation_check:hGoodCovered"
    ]
    assert list(row["verified_source_to_bridge_premise_derivation_artifact_paths"]) == [
        str(premise_artifact)
    ]
    assert list(row["verified_source_to_bridge_premise_derivation_declarations"]) == [
        "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    ]
    adapter_source = Path(row["adapter_candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert (
        "-- verified source-to-bridge premise derivation id: "
        "source_to_bridge_premise_derivation_check:hGoodCovered"
    ) in adapter_source
    assert (
        "-- verified source-to-bridge premise derivation artifact: "
        f"{premise_artifact}"
    ) in adapter_source
    assert (
        "-- verified source-to-bridge premise derivation declaration: "
        "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    ) in adapter_source
    learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert learning_rows[0][
        "kernel_verified_source_to_bridge_premise_derivation_ids"
    ] == ["source_to_bridge_premise_derivation_check:hGoodCovered"]
    assert learning_rows[0][
        "verified_source_to_bridge_premise_derivation_artifact_paths"
    ] == [str(premise_artifact)]


def test_adapter_bridge_inlines_verified_premise_derivation_artifact_for_candidate(
    tmp_path: Path,
) -> None:
    premise_artifact = tmp_path / "premise_derivations" / "hGoodCovered.lean"
    premise_artifact.parent.mkdir(parents=True)
    premise_artifact.write_text(
        "\n".join(
            [
                "import Mathlib",
                "",
                "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    queue = tmp_path / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            _adapter_work_order(
                kernel_verified_source_to_bridge_premise_derivation_ids=[
                    "source_to_bridge_premise_derivation_check:hGoodCovered"
                ],
                verified_source_to_bridge_premise_derivation_artifact_paths=[
                    str(premise_artifact)
                ],
                verified_source_to_bridge_premise_derivation_declarations=[
                    "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
                ],
                lean_statement_sketch=(
                    "import Mathlib\n\n"
                    "theorem split_conformal_coverage_source_to_bridge_adapter : "
                    "True := by\n"
                    "  exact split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
                ),
            )
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    row = manifest["rows"][0]
    adapter_source = Path(row["adapter_candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert (
        "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
        in adapter_source
    )
    assert row["adapter_generation_mode"] == "formalizer_provided_adapter_candidate"
    assert list(row["kernel_verified_source_to_bridge_premise_derivation_ids"]) == [
        "source_to_bridge_premise_derivation_check:hGoodCovered"
    ]


def test_adapter_bridge_synthesizes_premise_queue_from_closure_signature(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "source_to_bridge_adapter_instantiation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            _adapter_work_order(
                exact_goal_shape_obligation_ids=[
                    "source_to_bridge_adapter_goal_shape_mismatch"
                ],
                runtime_queue_status=(
                    "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
                ),
                target_artifact_kind=(
                    "source_theorem_exact_proof_body_adapter_instantiation"
                ),
                kernel_verified_theorem_reduction_closure_signature_excerpts=[
                    "theorem splitConformalFiniteSampleCoverage_reductionClosure "
                    "(hGoodCovered : {ω | rank ω ∈ BadRanks}ᶜ ⊆ covered) "
                    "(hBadEvent : MeasurableSet {ω | rank ω ∈ BadRanks}) "
                    "(hRank : ∀ r ∈ BadRanks, μ {ω | rank ω = r} ≤ α r) "
                    "(h_total : (∑ r ∈ BadRanks, α r) ≤ α_total) : "
                    "1 - α_total ≤ μ covered"
                ],
            )
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    row = manifest["rows"][0]
    assert [
        item["premise_name"]
        for item in row["source_to_bridge_premise_derivation_work_items"]
    ] == ["hGoodCovered", "hBadEvent", "hRank", "h_total"]
    assert manifest["n_source_to_bridge_premise_derivation_queue_rows"] == 4
    premise_queue_rows = [
        json.loads(line)
        for line in Path(str(manifest["source_to_bridge_premise_derivation_queue_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert [row["premise_name"] for row in premise_queue_rows] == [
        "hGoodCovered",
        "hBadEvent",
        "hRank",
        "h_total",
    ]
    assert all(
        row["proof_evidence_status"] == "WORK_ORDER_NOT_PROOF_EVIDENCE"
        for row in premise_queue_rows
    )


def test_adapter_bridge_consumes_exact_goal_shape_adapter_instantiation_queue(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "source_to_bridge_adapter_instantiation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactGoalShapeAdapterInstantiationWorkOrder"
                ),
                "queue_id": (
                    "source_theorem_exact_goal_shape_adapter_instantiation:adapter"
                ),
                "source_work_order_id": (
                    "source_theorem_semantic_primitive_work_order:adapter"
                ),
                "question_id": "conformal_prediction_coverage",
                "target_theorem_name": "split_conformal_coverage",
                "target_theorem_goal_ids": [
                    "split_conformal_finite_sample_coverage"
                ],
                "source_theorem_target_known": True,
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "split_conformal_coverage",
                    "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
                },
                "semantic_primitive_gap_kind": (
                    "source_theorem_exact_goal_shape_obligation"
                ),
                "exact_goal_shape_obligation_id": (
                    "source_to_bridge_adapter_goal_shape_mismatch"
                ),
                "exact_goal_shape_obligation": (
                    "Kernel-verified source-to-bridge adapter is available, "
                    "but its conclusion does not directly close the exact source "
                    "theorem goal."
                ),
                "proof_body_goal_excerpt": [
                    "⊢ 1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧",
                    "  P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ≤ 1 - alpha + 1 / ↑(n2 + 1)",
                ],
                "proof_body_attempt_summaries": [
                    "1:exact split_conformal_coverage_source_to_bridge_adapter:returncode=1:compiled=False:diagnostic_kind=type_mismatch"
                ],
                "runtime_queue_status": (
                    "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
                ),
                "target_artifact_kind": (
                    "source_theorem_exact_proof_body_adapter_instantiation"
                ),
                "acceptance_gate": (
                    "Build or repair a checked source-to-bridge adapter/proof body "
                    "that derives bridge hypotheses from exact assumptions."
                ),
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            }
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=False,
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_adapter_kernel_verified"] == 0
    row = manifest["rows"][0]
    assert row["work_order_id"] == (
        "source_theorem_exact_goal_shape_adapter_instantiation:adapter"
    )
    assert row["source_work_order_id"] == (
        "source_theorem_semantic_primitive_work_order:adapter"
    )
    assert row["source_queue_artifact_kind"] == (
        "SourceTheoremExactGoalShapeAdapterInstantiationWorkOrder"
    )
    assert row["source_queue_status"] == (
        "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
    )
    assert row["exact_goal_shape_obligation_id"] == (
        "source_to_bridge_adapter_goal_shape_mismatch"
    )
    assert row["target_artifact_kind"] == (
        "source_theorem_exact_proof_body_adapter_instantiation"
    )
    assert row["adapter_candidate_vacuous"] is False
    assert row["adapter_candidate_evidence_eligible"] is False
    assert row["failure_classification"] == "adapter_candidate_not_evidence_eligible"
    assert row["proof_body_adapter_required_reasons"][:2] == (
        "verified adapter or closure dependencies do not directly match the "
        "exact source theorem goal shape",
        "derive bridge premises from exact source-theorem assumptions before "
        "retrying the exact source proof body",
    )
    adapter_source = Path(row["adapter_candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert (
        "-- exact goal-shape obligation id: "
        "source_to_bridge_adapter_goal_shape_mismatch"
    ) in adapter_source
    assert (
        "-- source queue status: "
        "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
    ) in adapter_source
    assert (
        "-- target adapter artifact kind: "
        "source_theorem_exact_proof_body_adapter_instantiation"
    ) in adapter_source
    assert "derive bridge premises from exact source-theorem assumptions" in (
        adapter_source
    )
    learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert learning_rows[0]["exact_goal_shape_obligation_id"] == (
        "source_to_bridge_adapter_goal_shape_mismatch"
    )
    assert learning_rows[0]["source_queue_status"] == (
        "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
    )
    assert learning_rows[0]["proof_evidence_status"] == (
        "SOURCE_THEOREM_PROOF_BODY_ADAPTER_BRIDGE_NOT_PROOF_EVIDENCE"
    )


def test_exact_goal_adapter_rejects_candidate_that_assumes_bridge_premises(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "source_to_bridge_adapter_instantiation_queue.jsonl"
    _write_jsonl(
        queue,
        [
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactGoalShapeAdapterInstantiationWorkOrder"
                ),
                "queue_id": (
                    "source_theorem_exact_goal_shape_adapter_instantiation:adapter"
                ),
                "source_work_order_id": (
                    "source_theorem_semantic_primitive_work_order:adapter"
                ),
                "question_id": "conformal_prediction_coverage",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "exact_goal_shape_obligation_id": (
                    "source_to_bridge_adapter_goal_shape_mismatch"
                ),
                "runtime_queue_status": (
                    "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
                ),
                "target_artifact_kind": (
                    "source_theorem_exact_proof_body_adapter_instantiation"
                ),
                "lean_statement_sketch": (
                    "import Mathlib\n\n"
                    "theorem split_conformal_coverage_source_to_bridge_adapter "
                    "{Ω ρ : Type*} [MeasurableSpace Ω] "
                    "(P : MeasureTheory.Measure Ω) "
                    "(covered : Set Ω) (BadRanks : Finset ρ) "
                    "(rank : Ω → ρ) (α : ρ → ENNReal) "
                    "(α_total : ENNReal) "
                    "(hGoodCovered : {ω | rank ω ∈ BadRanks}ᶜ ⊆ covered) "
                    "(hBadEvent : MeasurableSet {ω | rank ω ∈ BadRanks}) "
                    "(hRank : ∀ r ∈ BadRanks, P {ω | rank ω = r} ≤ α r) "
                    "(hTotal : (∑ r ∈ BadRanks, α r) ≤ α_total) : "
                    "P covered ≥ 1 - α_total := by\n"
                    "  exact by simpa using "
                    "splitConformalFiniteSampleCoverage_reductionClosure "
                    "P covered BadRanks rank α α_total hGoodCovered "
                    "hBadEvent hRank hTotal"
                ),
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            }
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_checked"] is True
    assert row["local_lean_compiled"] is True
    assert row["adapter_candidate_requires_unproven_bridge_premises"] is True
    assert row["unproven_bridge_premise_names"] == (
        "hGoodCovered",
        "hBadEvent",
        "hRank",
        "hTotal",
    )
    assert row["adapter_candidate_evidence_eligible"] is False
    assert row["adapter_kernel_verified"] is False
    assert row["failure_classification"] == (
        "adapter_candidate_requires_unproven_bridge_premises"
    )
    assert manifest["n_adapter_kernel_verified"] == 0
    learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert (
        learning_rows[0]["adapter_candidate_requires_unproven_bridge_premises"]
        is True
    )
    assert learning_rows[0]["unproven_bridge_premise_names"] == [
        "hGoodCovered",
        "hBadEvent",
        "hRank",
        "hTotal",
    ]


def test_adapter_work_order_goal_shape_list_rejects_bridge_premise_assumptions(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            _adapter_work_order(
                exact_goal_shape_obligation_ids=[
                    "source_to_bridge_adapter_goal_shape_mismatch"
                ],
                lean_statement_sketch=(
                    "import Mathlib\n\n"
                    "theorem split_conformal_coverage_source_to_bridge_adapter "
                    "{Ω ρ : Type*} [MeasurableSpace Ω] "
                    "(P : MeasureTheory.Measure Ω) "
                    "(covered : Set Ω) (BadRanks : Finset ρ) "
                    "(rank : Ω → ρ) (α : ρ → ENNReal) "
                    "(α_total : ENNReal) "
                    "(hGoodCovered : {ω | rank ω ∈ BadRanks}ᶜ ⊆ covered) "
                    "(hRank : ∀ r ∈ BadRanks, P {ω | rank ω = r} ≤ α r) "
                    "(hTotal : (∑ r ∈ BadRanks, α r) ≤ α_total) : "
                    "P covered ≥ 1 - α_total := by\n"
                    "  exact by simpa using "
                    "splitConformalFiniteSampleCoverage_reductionClosure "
                    "P covered BadRanks rank α α_total hGoodCovered "
                    "by infer_instance hRank hTotal"
                ),
            )
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["adapter_candidate_requires_unproven_bridge_premises"] is True
    assert row["unproven_bridge_premise_names"] == (
        "hGoodCovered",
        "hRank",
        "hTotal",
    )
    assert row["adapter_kernel_verified"] is False
    assert row["failure_classification"] == (
        "adapter_candidate_requires_unproven_bridge_premises"
    )
    assert row["proof_body_adapter_required_reasons"][:2] == (
        "verified adapter or closure dependencies do not directly match the "
        "exact source theorem goal shape",
        "derive bridge premises from exact source-theorem assumptions before "
        "retrying the exact source proof body",
    )


def test_adapter_bridge_exports_unavailable_import_metadata(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            _adapter_work_order(
                lean_statement_sketch=(
                    "import Mathlib.Data.Finset.Sort\n"
                    "import Mathlib.Algebra.Order.Floor\n\n"
                    "theorem split_conformal_coverage_source_to_bridge_adapter "
                    "(source_hypotheses bridge_premises : Prop) "
                    "(h : source_hypotheses -> bridge_premises) "
                    "(hs : source_hypotheses) : bridge_premises := by\n"
                    "  exact h hs"
                )
            )
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; "
            "print(\"error: object file '/tmp/Mathlib/Algebra/Order/Floor.olean' "
            "of module Mathlib.Algebra.Order.Floor does not exist\"); "
            "sys.exit(1)",
        ),
    )

    row = manifest["rows"][0]
    assert row["adapter_generation_mode"] == "formalizer_provided_adapter_candidate"
    assert row["adapter_candidate_evidence_eligible"] is True
    assert row["failure_classification"] == "adapter_lean_import_environment_missing"
    assert row["adapter_candidate_imports"] == (
        "Mathlib.Data.Finset.Sort",
        "Mathlib.Algebra.Order.Floor",
    )
    assert row["unavailable_import"] == "Mathlib.Algebra.Order.Floor"
    assert manifest["n_adapter_candidate_import_rows"] == 1
    assert manifest["n_adapter_unavailable_import_rows"] == 1
    assert manifest["adapter_unavailable_imports"] == [
        "Mathlib.Algebra.Order.Floor"
    ]
    learning_rows = [
        json.loads(line)
        for line in Path(str(manifest["runtime_learning_rows_jsonl"]))
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert learning_rows[0]["adapter_candidate_imports"] == [
        "Mathlib.Data.Finset.Sort",
        "Mathlib.Algebra.Order.Floor",
    ]
    assert learning_rows[0]["unavailable_import"] == (
        "Mathlib.Algebra.Order.Floor"
    )
    assert learning_rows[0]["input_summary"]["unavailable_import"] == (
        "Mathlib.Algebra.Order.Floor"
    )


def test_adapter_bridge_rejects_vacuous_compiling_candidate(tmp_path: Path) -> None:
    queue = tmp_path / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            _adapter_work_order(
                lean_statement_sketch=(
                    "theorem split_conformal_coverage_source_to_bridge_adapter : "
                    "True := by\n"
                    "  exact True.intro"
                )
            )
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_checked"] is True
    assert row["local_lean_compiled"] is True
    assert row["adapter_candidate_vacuous"] is True
    assert row["adapter_candidate_evidence_eligible"] is False
    assert row["adapter_kernel_verified"] is False
    assert row["failure_classification"] == "adapter_candidate_vacuous"
    assert manifest["n_adapter_kernel_verified"] == 0
    assert manifest["n_source_theorem_kernel_verified"] == 0


def test_adapter_bridge_rejects_placeholder_comment_candidate_before_evidence(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            _adapter_work_order(
                lean_statement_sketch=(
                    "theorem split_conformal_coverage_source_to_bridge_adapter "
                    "(hExch : /* exchangeability hypothesis placeholder */) : "
                    "True := by\n"
                    "  exact True.intro"
                )
            )
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    assert row["local_lean_checked"] is True
    assert row["local_lean_compiled"] is True
    assert row["adapter_candidate_evidence_eligible"] is False
    assert row["adapter_kernel_verified"] is False
    assert row["failure_classification"] == (
        "adapter_candidate_forbidden_placeholder_token"
    )
    assert "c_style_comment_placeholder" in row["forbidden_tokens_found"]
    assert "placeholder_text" in row["forbidden_tokens_found"]
    assert manifest["n_adapter_kernel_verified"] == 0
    assert manifest["n_source_theorem_kernel_verified"] == 0


def test_adapter_bridge_inlines_verified_closure_artifact_context(
    tmp_path: Path,
) -> None:
    closure_artifact = tmp_path / "closure_artifact.lean"
    closure_artifact.write_text(
        "\n".join(
            [
                "import Mathlib",
                "",
                "theorem splitConformalFiniteSampleCoverage_reductionClosure",
                "    (p : Prop) (hp : p) : p := by",
                "  exact hp",
            ]
        ),
        encoding="utf-8",
    )
    queue = tmp_path / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(
        queue,
        [
            _adapter_work_order(
                lean_statement_sketch=(
                    "import Mathlib\n\n"
                    "theorem split_conformal_coverage_source_to_bridge_adapter "
                    "(p : Prop) (hp : p) : p := by\n"
                    "  exact splitConformalFiniteSampleCoverage_reductionClosure p hp"
                ),
                verified_theorem_reduction_closure_artifact_paths=[
                    str(closure_artifact)
                ],
            )
        ],
    )

    manifest = run_source_theorem_proof_body_adapter_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    row = manifest["rows"][0]
    adapter_source = Path(row["adapter_candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert adapter_source.count("import Mathlib") == 1
    assert (
        "theorem splitConformalFiniteSampleCoverage_reductionClosure"
        in adapter_source
    )
    assert (
        adapter_source.index("theorem splitConformalFiniteSampleCoverage_reductionClosure")
        < adapter_source.index("theorem split_conformal_coverage_source_to_bridge_adapter")
    )
    assert row["adapter_candidate_evidence_eligible"] is True
    assert row["adapter_kernel_verified"] is True
    assert manifest["n_adapter_kernel_verified"] == 1
    assert manifest["n_source_theorem_kernel_verified"] == 0


def test_adapter_bridge_cli_consumes_queue(tmp_path: Path) -> None:
    queue = tmp_path / "runtime_source_theorem_proof_body_adapter_work_orders.jsonl"
    _write_jsonl(queue, [_adapter_work_order()])
    out_dir = tmp_path / "bridge_cli"

    exit_code = main(
        [
            "source-theorem-proof-body-adapter-proofengineer-bridge",
            "--queue-jsonl",
            str(queue),
            "--out",
            str(out_dir),
        ]
    )

    assert exit_code == 0
    manifest = json.loads(
        (
            out_dir
            / "source_theorem_proof_body_adapter_proofengineer_bridge_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["n_work_orders"] == 1
    assert manifest["n_adapter_check_rows"] == 1
    assert manifest["n_source_theorem_kernel_verified"] == 0
    assert manifest["proof_evidence_status"] == (
        "SOURCE_THEOREM_PROOF_BODY_ADAPTER_BRIDGE_NOT_PROOF_EVIDENCE"
    )


def test_capability_eval_requires_adapter_proofengineer_bridge() -> None:
    args = Namespace(
        provider="anthropic",
        architect_coordinator_provider="anthropic",
        simulation_engineer_provider="anthropic",
        algorithm_engineer_provider="anthropic",
        formalizer_provider="anthropic",
        critic_evaluator_provider="anthropic",
        local_lean=True,
        real_lean=False,
        proof_obligation_id=[],
        theorem_closure_proofengineer_bridge=True,
        theorem_closure_proofengineer_local_lean=True,
        source_semantic_proofengineer_bridge=True,
        source_semantic_proofengineer_local_lean=True,
        source_theorem_promotion_proofengineer_bridge=True,
        source_theorem_promotion_proofengineer_local_lean=True,
        source_theorem_formal_environment_proofengineer_bridge=True,
        source_theorem_formal_environment_proofengineer_signature_probes=True,
        source_theorem_formal_environment_proofengineer_execute_proof_body=True,
        source_theorem_formal_environment_proofengineer_proof_body_local_lean=True,
        source_theorem_proof_body_adapter_proofengineer_bridge=False,
        source_theorem_proof_body_adapter_proofengineer_local_lean=True,
        source_theorem_exact_semantic_definition_source_lookup=True,
        source_theorem_exact_semantic_definition_proofengineer_bridge=True,
        source_theorem_exact_semantic_definition_lean_repair_executor=True,
        source_theorem_exact_semantic_definition_lean_repair_executor_local_lean=True,
        source_theorem_exact_semantic_definition_lean_environment_repair_executor=True,
        source_theorem_exact_semantic_definition_closure_review=True,
        source_theorem_exact_semantic_definition_candidate_synthesis=True,
        source_theorem_exact_semantic_definition_candidate_synthesis_local_lean=True,
        source_theorem_exact_semantic_definition_source_root=["StatInference"],
    )

    errors = _research_agent_runtime_capability_config_errors(args)

    assert (
        "capability eval requires the internal ProofEngineer proof path; "
        "missing --source-theorem-proof-body-adapter-proofengineer-bridge"
    ) in errors

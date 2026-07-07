from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.exact_source_theorem_proof_body_executor import (
    export_exact_source_theorem_proof_body_execution_results,
)


def test_exact_source_executor_materializes_verified_closure_dependency(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "import Mathlib.Data.Real.Basic\n"
        "\n"
        "namespace Smoke\n"
        "\n"
        "theorem split_conformal_coverage : True := by\n"
        "  fail_if_success trivial\n"
        "\n"
        "end Smoke\n",
        encoding="utf-8",
    )
    closure = tmp_path / "closure.lean"
    closure.write_text(
        "import Mathlib\n"
        "open Classical\n"
        "\n"
        "theorem splitConformalFiniteSampleCoverage_reductionClosure : True := by\n"
        "  trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:closure_context",
                "source_work_order_id": "exact_source_work_order:closure_context",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "kernel_verified_theorem_reduction_closure_declarations": [
                    "splitConformalFiniteSampleCoverage_reductionClosure"
                ],
                "verified_theorem_reduction_closure_artifact_paths": [str(closure)],
                "kernel_verified_theorem_reduction_closure_target_ids": [
                    "split_conformal_finite_sample_coverage_reduction_closure"
                ],
                "proof_body_attempts": [
                    "exact splitConformalFiniteSampleCoverage_reductionClosure"
                ],
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:closure_context",
                    "mcp_tool_calls": [],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=False,
    )

    assert manifest["n_materialized_candidate_artifacts"] == 1
    row = manifest["rows"][0]
    assert row["kernel_verified_theorem_reduction_closure_declarations"] == (
        "splitConformalFiniteSampleCoverage_reductionClosure",
    )
    candidate_text = candidate.read_text(encoding="utf-8")
    assert "import Mathlib\nimport Mathlib.Data.Real.Basic" in candidate_text
    assert (
        "theorem splitConformalFiniteSampleCoverage_reductionClosure : True := by"
        in candidate_text
    )
    assert candidate_text.index(
        "theorem splitConformalFiniteSampleCoverage_reductionClosure"
    ) < candidate_text.index("theorem split_conformal_coverage")
    assert "theorem split_conformal_coverage : True := by" in candidate_text


def test_exact_source_executor_preserves_exact_semantic_context_in_learning(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    exact_context = {
        "semantic_primitive": "covered",
        "semantic_primitive_requirements": [
            "covered must denote the source event from the paper, not a theorem-shaped placeholder"
        ],
        "source_anchors": [
            {
                "label": "paper-def-covered",
                "source_path": "paper/sec2.tex",
                "quote": "covered event source anchor",
            }
        ],
        "source_pseudo_formal_work_order_id": "pf-work-order:covered",
        "source_pseudo_formal_block_id": "pf-block:coverage",
        "source_pseudo_formal_packet_id": "pf-packet:split",
        "pseudo_formal_pipeline_stage": "PF/BV_semantic_bridge",
        "pseudo_formal_proof_evidence_status": (
            "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
        ),
    }
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:semantic_context",
                "source_work_order_id": "exact_source_work_order:semantic_context",
                "target_theorem_name": "split_conformal_coverage",
                "target_ids": ["split_conformal_finite_sample_coverage"],
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_identity_status": (
                    "SOURCE_THEOREM_TARGET_KNOWN"
                ),
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:semantic_context",
                    "mcp_tool_calls": [],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                **exact_context,
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=False,
    )

    assert manifest["n_exact_semantic_definition_context_rows"] == 1
    assert manifest["n_execution_result_rows_from_pseudo_formal"] == 1
    assert manifest["n_local_lean_checked_from_pseudo_formal"] == 0
    assert manifest["n_source_theorem_kernel_verified_from_pseudo_formal"] == 0
    assert manifest["source_pseudo_formal_work_order_ids"] == [
        "pf-work-order:covered"
    ]
    assert manifest["source_pseudo_formal_block_ids"] == ["pf-block:coverage"]
    learning_manifest = manifest["runtime_learning_export"]
    assert learning_manifest["n_runtime_learning_rows_from_pseudo_formal"] == 1
    assert learning_manifest["source_pseudo_formal_work_order_ids"] == [
        "pf-work-order:covered"
    ]
    row = manifest["rows"][0]
    assert row["exact_semantic_definition_context"]["source_anchors"] == (
        exact_context["source_anchors"]
    )
    assert row["candidate_live_proof_state_request"]["source_pseudo_formal_work_order_id"] == (
        "pf-work-order:covered"
    )
    assert row["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
    )

    learning_path = Path(manifest["runtime_learning_rows_jsonl"])
    learning_row = json.loads(learning_path.read_text(encoding="utf-8").splitlines()[0])
    assert learning_row["semantic_primitive_requirements"] == (
        exact_context["semantic_primitive_requirements"]
    )
    assert learning_row["source_anchors"] == exact_context["source_anchors"]
    assert learning_row["source_pseudo_formal_work_order_id"] == (
        "pf-work-order:covered"
    )
    assert learning_row["pseudo_formal_proof_evidence_status"] == (
        "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
    )
    assert learning_row["source_theorem_kernel_verified"] is False
    assert learning_row["input_summary"]["exact_semantic_definition_context"][
        "source_pseudo_formal_packet_id"
    ] == "pf-packet:split"

    transcript_event = json.loads(transcript.read_text(encoding="utf-8").splitlines()[0])
    assert transcript_event["exact_semantic_definition_context"][
        "source_pseudo_formal_block_id"
    ] == "pf-block:coverage"


def test_exact_source_executor_tracks_formalizer_pf_component_gate_context(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    exact_rows_jsonl = "runs/formalizer_pf/exact_semantic_definition_rows.jsonl"
    exact_context = {
        "semantic_primitive": "coverage_event",
        "semantic_primitive_requirements": ["coverage_event"],
        "source_component_gate": "formalizer_pseudo_formal_packet_component_gate",
        "source_component_gate_exact_rows_jsonl": exact_rows_jsonl,
        "component_eval_manifest_path": "runs/formalizer_pf/manifest.json",
        "provider_name": "anthropic",
        "backend_provider_name": "anthropic",
        "source_anchors": [
            {
                "label": "formalizer-pf-coverage-event",
                "source_path": "paper/sec2.tex",
                "quote": "coverage event source anchor",
            }
        ],
    }
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:formalizer_pf",
                "source_work_order_id": "exact_source_work_order:formalizer_pf",
                "target_theorem_name": "split_conformal_coverage",
                "target_ids": ["split_conformal_finite_sample_coverage"],
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_identity_status": (
                    "SOURCE_THEOREM_TARGET_KNOWN"
                ),
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:formalizer_pf",
                    "mcp_tool_calls": [],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                **exact_context,
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=False,
    )

    assert manifest["n_execution_result_rows_from_pseudo_formal"] == 1
    assert (
        manifest["n_execution_result_rows_from_formalizer_pf_component_gate"]
        == 1
    )
    assert manifest["n_source_theorem_kernel_verified_from_pseudo_formal"] == 0
    assert (
        manifest[
            "n_source_theorem_kernel_verified_from_formalizer_pf_component_gate"
        ]
        == 0
    )
    assert manifest["formalizer_pf_component_gate_exact_rows_jsonl_paths"] == [
        exact_rows_jsonl
    ]
    assert manifest["runtime_learning_export"][
        "n_runtime_learning_rows_from_formalizer_pf_component_gate"
    ] == 1
    row = manifest["rows"][0]
    assert row["exact_semantic_definition_context"]["source_component_gate"] == (
        "formalizer_pseudo_formal_packet_component_gate"
    )
    assert row["candidate_live_proof_state_request"]["source_component_gate"] == (
        "formalizer_pseudo_formal_packet_component_gate"
    )
    assert row["source_theorem_kernel_verified"] is False
    assert "KERNEL_VERIFIED" not in row["proof_evidence_status"]


def test_exact_source_executor_materializes_verified_adapter_dependency(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "import Mathlib.Data.Real.Basic\n"
        "\n"
        "namespace Smoke\n"
        "\n"
        "theorem split_conformal_coverage : True := by\n"
        "  fail_if_success trivial\n"
        "\n"
        "end Smoke\n",
        encoding="utf-8",
    )
    adapter = tmp_path / "adapter.lean"
    adapter.write_text(
        "import Mathlib\n"
        "open Classical\n"
        "\n"
        "theorem splitConformalCoverage_sourceToBridgeAdapter : True := by\n"
        "  trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:adapter_context",
                "source_work_order_id": "exact_source_work_order:adapter_context",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_kernel_evidence_eligible": False,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "kernel_verified_source_theorem_proof_body_adapter_ids": [
                    "source_theorem_proof_body_adapter:verified"
                ],
                "verified_source_theorem_proof_body_adapter_artifact_paths": [
                    str(adapter)
                ],
                "verified_source_theorem_proof_body_adapter_declarations": [
                    "splitConformalCoverage_sourceToBridgeAdapter"
                ],
                "source_theorem_proof_body_adapter_kernel_verified": True,
                "source_theorem_proof_body_adapter_feedback_available": True,
                "proof_body_attempts": [
                    "exact splitConformalCoverage_sourceToBridgeAdapter"
                ],
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:adapter_context",
                    "mcp_tool_calls": [
                        {
                            "tool": "lean_goal",
                            "arguments": {
                                "file": str(signature),
                                "line": 1,
                                "column": 1,
                                "declaration": "stale_dependency",
                            },
                        },
                        {
                            "tool": "lean_multi_attempt",
                            "arguments": {
                                "file": str(signature),
                                "line": 1,
                                "column": 1,
                                "declaration": "stale_dependency",
                                "snippets": ["exact stale_dependency"],
                            },
                        },
                    ],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=False,
    )

    assert manifest["n_materialized_candidate_artifacts"] == 1
    assert manifest["n_source_theorem_proof_body_adapter_context_rows"] == 1
    assert (
        manifest["n_source_theorem_proof_body_adapter_kernel_verified_context_rows"]
        == 1
    )
    row = manifest["rows"][0]
    assert row["verified_source_theorem_proof_body_adapter_declarations"] == (
        "splitConformalCoverage_sourceToBridgeAdapter",
    )
    candidate_text = candidate.read_text(encoding="utf-8")
    assert "import Mathlib\nimport Mathlib.Data.Real.Basic" in candidate_text
    assert (
        "theorem splitConformalCoverage_sourceToBridgeAdapter : True := by"
        in candidate_text
    )
    assert candidate_text.index(
        "theorem splitConformalCoverage_sourceToBridgeAdapter"
    ) < candidate_text.index("theorem split_conformal_coverage")
    assert "exact source-theorem proof-body repair" in candidate_text
    request = row["candidate_live_proof_state_request"]
    assert request["source_theorem_proof_body_adapter_kernel_verified"] is True
    assert request["verified_source_theorem_proof_body_adapter_declarations"] == [
        "splitConformalCoverage_sourceToBridgeAdapter"
    ]
    assert request["target_lean_declaration"] == "split_conformal_coverage"
    assert request["target_lean_file"] == str(candidate)
    assert request["target_lean_line"] == (
        candidate_text[: candidate_text.index("fail_if_success trivial")].count("\n")
        + 1
    )
    for call in request["mcp_tool_calls"]:
        assert call["arguments"]["file"] == str(candidate)
        assert call["arguments"]["declaration"] == "split_conformal_coverage"
        assert call["arguments"]["line"] == request["target_lean_line"]
    multi_attempt = [
        call for call in request["mcp_tool_calls"] if call["tool"] == "lean_multi_attempt"
    ][0]
    assert (
        "exact splitConformalCoverage_sourceToBridgeAdapter"
        in multi_attempt["arguments"]["snippets"]
    )


def test_exact_source_executor_materializes_verified_premise_derivation_dependency(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "import Mathlib.Data.Real.Basic\n"
        "\n"
        "namespace Smoke\n"
        "\n"
        "theorem split_conformal_coverage : True := by\n"
        "  fail_if_success trivial\n"
        "\n"
        "end Smoke\n",
        encoding="utf-8",
    )
    premise = tmp_path / "hGoodCovered.lean"
    premise.write_text(
        "import Mathlib\n"
        "\n"
        "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation : "
        "True := by\n"
        "  trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:premise_context",
                "source_work_order_id": "exact_source_work_order:premise_context",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "kernel_verified_source_to_bridge_premise_derivation_ids": [
                    "source_to_bridge_premise_derivation_check:hGoodCovered"
                ],
                "verified_source_to_bridge_premise_derivation_artifact_paths": [
                    str(premise)
                ],
                "verified_source_to_bridge_premise_derivation_declarations": [
                    "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
                ],
                "proof_body_attempts": [
                    "exact split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
                ],
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:premise_context",
                    "mcp_tool_calls": [],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=False,
    )

    assert manifest["n_materialized_candidate_artifacts"] == 1
    assert (
        manifest["n_kernel_verified_source_to_bridge_premise_derivation_context_rows"]
        == 1
    )
    assert manifest["kernel_verified_source_to_bridge_premise_derivation_ids"] == [
        "source_to_bridge_premise_derivation_check:hGoodCovered"
    ]
    assert manifest[
        "verified_source_to_bridge_premise_derivation_artifact_paths"
    ] == [str(premise)]
    assert manifest[
        "verified_source_to_bridge_premise_derivation_declarations"
    ] == ["split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"]
    row = manifest["rows"][0]
    assert row["verified_source_to_bridge_premise_derivation_declarations"] == (
        "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation",
    )
    candidate_text = candidate.read_text(encoding="utf-8")
    assert (
        "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
        in candidate_text
    )
    assert candidate_text.index(
        "theorem split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    ) < candidate_text.index("theorem split_conformal_coverage :")
    request = row["candidate_live_proof_state_request"]
    assert request["kernel_verified_source_to_bridge_premise_derivation_ids"] == [
        "source_to_bridge_premise_derivation_check:hGoodCovered"
    ]
    learning_rows = [
        json.loads(line)
        for line in (
            tmp_path
            / "executor"
            / "runtime_learning_export"
            / "runtime_learning_rows.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert learning_rows[0][
        "kernel_verified_source_to_bridge_premise_derivation_ids"
    ] == ["source_to_bridge_premise_derivation_check:hGoodCovered"]


def test_exact_source_executor_classifies_verified_adapter_context_insufficient(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage :\n"
        "    1 - alpha ≤ P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ∧\n"
        "    P.real {ω | s (Fin.last n2) ω ≤ q_hat ω} ≤ "
        "1 - alpha + 1 / (↑(n2 + 1)) := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    adapter = tmp_path / "adapter.lean"
    adapter.write_text(
        "theorem splitConformalCoverage_sourceToBridgeAdapter : False := by\n"
        "  contradiction\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    fake_lean = tmp_path / "fake_lean.py"
    fake_lean.write_text(
        "import sys\n"
        "path = sys.argv[-1]\n"
        "if '.proof_body_attempt_1' in path:\n"
        "    print(path + ':1:8: error: Type mismatch')\n"
        "    sys.exit(1)\n"
        "print(path + ':1:1: error: unsolved goals')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:adapter_insufficient",
                "source_work_order_id": "exact_source_work_order:adapter_insufficient",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_kernel_evidence_eligible": True,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "kernel_verified_source_theorem_proof_body_adapter_ids": [
                    "source_theorem_proof_body_adapter_check:verified"
                ],
                "verified_source_theorem_proof_body_adapter_artifact_paths": [
                    str(adapter)
                ],
                "verified_source_theorem_proof_body_adapter_declarations": [
                    "splitConformalCoverage_sourceToBridgeAdapter"
                ],
                "source_theorem_proof_body_adapter_kernel_verified": True,
                "proof_body_attempts": [
                    "exact splitConformalCoverage_sourceToBridgeAdapter"
                ],
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:adapter_insufficient",
                    "mcp_tool_calls": [],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=True,
        lean_command=("python3", str(fake_lean)),
    )

    row = manifest["rows"][0]
    assert row["proof_body_goal_reached"] is True
    assert row["source_theorem_proof_body_adapter_kernel_verified"] is True
    assert row["source_theorem_kernel_verified"] is False
    assert row["failure_classification"] == (
        "proof_body_verified_adapter_context_insufficient"
    )
    assert row["exact_goal_shape_obligation_ids"] == (
        "source_to_bridge_adapter_goal_shape_mismatch",
        "conjunctive_source_theorem_split",
        "real_probability_lower_bound_from_ennreal_adapter",
        "upper_coverage_bound_component",
        "order_statistic_quantile_rank_instantiation",
    )
    assert any(
        "upper split-conformal coverage component" in obligation
        for obligation in row["exact_goal_shape_obligations"]
    )
    assert manifest["by_failure_classification"] == {
        "proof_body_verified_adapter_context_insufficient": 1
    }
    learning_row = json.loads(
        (
            tmp_path
            / "executor"
            / "runtime_learning_export"
            / "runtime_learning_rows.jsonl"
        ).read_text(encoding="utf-8")
    )
    assert learning_row["runtime_queue_status"] == (
        "PENDING_EXACT_SOURCE_THEOREM_PROOF_BODY_REPAIR_WITH_VERIFIED_ADAPTER"
    )
    assert learning_row["trigger"] == (
        "EXACT_SOURCE_PROOF_BODY_VERIFIED_ADAPTER_CONTEXT_INSUFFICIENT"
    )
    assert learning_row["exact_goal_shape_obligation_ids"] == [
        "source_to_bridge_adapter_goal_shape_mismatch",
        "conjunctive_source_theorem_split",
        "real_probability_lower_bound_from_ennreal_adapter",
        "upper_coverage_bound_component",
        "order_statistic_quantile_rank_instantiation",
    ]
    assert "post-adapter feedback" in learning_row["target_behavior"]


def test_exact_source_executor_skips_proof_attempts_for_semantic_alignment_blockers(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:semantic_alignment",
                "source_work_order_id": "exact_source_work_order:semantic_alignment",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": False,
                "source_theorem_target_identity_status": (
                    "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
                ),
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "semantic_alignment_constraints": [
                    "unreviewed synthesized definition semantic risk: "
                    "draft finite maximum ignores rank k"
                ],
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:semantic_alignment",
                    "mcp_tool_calls": [
                        {
                            "tool": "lean_goal",
                            "arguments": {
                                "file": str(signature),
                                "line": 1,
                                "column": 1,
                            },
                        },
                        {
                            "tool": "lean_multi_attempt",
                            "arguments": {
                                "file": str(signature),
                                "line": 1,
                                "column": 1,
                            },
                        },
                    ],
                    "proof_body_attempts": ["simp"],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=True,
        lean_command=(
            "python3",
            "-c",
            "import sys; print('error: unsolved goals'); sys.exit(1)",
        ),
    )

    assert manifest["n_proof_body_attempted"] == 0
    assert manifest["n_proof_body_goal_reached"] == 1
    assert manifest["n_proof_body_goal_reached_with_semantic_blockers"] == 1
    assert manifest["n_semantic_alignment_blocker_rows"] == 1
    assert manifest["n_source_theorem_kernel_verified"] == 0
    assert manifest["by_proof_body_gate_status"] == {
        "PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED": 1
    }
    row = manifest["rows"][0]
    assert row["proof_body_attempted"] is False
    assert row["proof_body_goal_reached"] is True
    assert row["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED"
    )
    assert row["proof_body_attempt_count"] == 0
    assert row["proof_body_attempt_source"] == (
        "semantic_alignment_open_skip_tactic_attempts"
    )
    assert row["target_ids"] == ("split_conformal_coverage",)
    assert row["source_theorem_kernel_evidence_eligible"] is False
    assert row["failure_classification"] == (
        "proof_body_reached_semantic_alignment_unreviewed"
    )
    assert row["source_theorem_target_identity_status"] == (
        "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    )
    request = row["candidate_live_proof_state_request"]
    assert request["proof_body_attempts"] == []
    assert request["proof_body_attempt_source"] == (
        "semantic_alignment_open_skip_tactic_attempts"
    )
    assert [call["tool"] for call in request["mcp_tool_calls"]] == ["lean_goal"]
    learning_manifest = manifest["runtime_learning_export"]
    assert manifest["runtime_learning_rows_jsonl"] == learning_manifest[
        "runtime_learning_rows_jsonl"
    ]
    assert manifest["runtime_learning_manifest"] == learning_manifest[
        "runtime_learning_manifest"
    ]
    assert manifest["n_runtime_learning_rows"] == 1
    assert learning_manifest["n_proof_body_goal_reached"] == 1
    assert learning_manifest["n_proof_body_goal_reached_with_semantic_blockers"] == 1
    rows = (
        tmp_path
        / "executor"
        / "runtime_learning_export"
        / "runtime_learning_rows.jsonl"
    ).read_text(encoding="utf-8")
    assert "EXACT_SOURCE_PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED" in rows
    learning_row = json.loads(rows)
    assert learning_row["runtime_queue_status"] == (
        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_REPAIR"
    )
    assert learning_row["failure_classification"] == (
        "proof_body_reached_semantic_alignment_unreviewed"
    )
    assert learning_row["target_ids"] == ["split_conformal_coverage"]
    assert learning_row["input_summary"]["target_ids"] == [
        "split_conformal_coverage"
    ]
    assert learning_row["execution_status"] == "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
    assert learning_row["trigger"] == (
        "EXACT_SOURCE_PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED"
    )
    assert learning_row["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED"
    )
    transcript_events = [
        json.loads(line)
        for line in transcript.read_text(encoding="utf-8").splitlines()
    ]
    assert transcript_events[-1]["target_ids"] == ["split_conformal_coverage"]


def test_exact_source_executor_string_false_target_and_adapter_flags_stay_false(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:string_false",
                "source_work_order_id": "exact_source_work_order:string_false",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": "false",
                "source_theorem_kernel_evidence_eligible": "false",
                "source_theorem_proof_body_adapter_feedback_available": "false",
                "source_theorem_proof_body_adapter_kernel_verified": "false",
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": "false",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": "false",
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": "false",
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (
        queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    ).write_text(json.dumps(queue_manifest), encoding="utf-8")

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=False,
    )

    assert manifest["n_source_theorem_target_known"] == 0
    assert manifest["n_live_goal_location_ready"] == 0
    assert manifest["n_source_theorem_proof_body_adapter_kernel_verified_context_rows"] == 0
    assert manifest["n_source_theorem_kernel_verified"] == 0
    row = manifest["rows"][0]
    assert row["source_theorem_target_known"] is False
    assert row["source_theorem_target_identity_status"] == (
        "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    )
    assert row["source_theorem_proof_body_adapter_feedback_available"] is False
    assert row["source_theorem_proof_body_adapter_kernel_verified"] is False
    assert row["source_theorem_kernel_evidence_eligible"] is False
    assert row["live_goal_location_ready"] is False
    assert row["source_theorem_kernel_verified"] is False


def test_exact_source_executor_does_not_treat_review_notes_as_semantic_blockers(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:review_note",
                "source_work_order_id": "exact_source_work_order:review_note",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_kernel_evidence_eligible": False,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "semantic_alignment_constraints": [
                    "unreviewed synthesized definition review note: "
                    "draft sorted finite order statistic needs source review"
                ],
                "semantic_alignment_blockers": [],
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:review_note",
                    "proof_body_goal_excerpt": [
                        "Ω : Type u_1",
                        "P : MeasureTheory.Measure Ω",
                    ],
                    "mcp_tool_calls": [
                        {
                            "tool": "lean_goal",
                            "arguments": {
                                "file": str(signature),
                                "line": 1,
                                "column": 1,
                            },
                        },
                        {
                            "tool": "lean_multi_attempt",
                            "arguments": {
                                "file": str(signature),
                                "line": 1,
                                "column": 1,
                            },
                        },
                    ],
                    "proof_body_attempts": ["simp"],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=True,
        lean_command=(
            "python3",
            "-c",
            (
                "import sys; "
                "print('error: unsolved goals\\nΩ : Type u_1\\n"
                "P : Measure Ω\\n⊢ target_goal'); sys.exit(1)"
            ),
        ),
    )

    assert manifest["n_proof_body_attempted"] == 1
    assert manifest["n_proof_body_goal_reached"] == 1
    assert manifest["n_proof_body_goal_excerpt_rows"] == 1
    assert any(
        "unsolved goals" in line
        for line in manifest["first_proof_body_goal_excerpt"]
    )
    assert any("⊢ target_goal" in line for line in manifest["first_proof_body_goal_excerpt"])
    assert manifest["n_proof_body_goal_reached_with_semantic_blockers"] == 0
    assert manifest["n_proof_body_gate_open_for_kernel_repair"] == 0
    assert manifest["proof_body_gate_open_target_names"] == []
    assert manifest["n_semantic_alignment_blocker_rows"] == 0
    assert manifest["n_source_theorem_kernel_verified"] == 0
    assert manifest["dominant_failure_classification"] == "proof_body_incomplete"
    row = manifest["rows"][0]
    assert row["semantic_alignment_blockers"] == ()
    assert row["proof_body_gate_status"] == "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    assert row["failure_classification"] == "proof_body_incomplete"
    assert any("unsolved goals" in line for line in row["proof_body_goal_excerpt"])
    assert any("⊢ target_goal" in line for line in row["proof_body_goal_excerpt"])
    assert row["proof_body_attempted"] is True
    assert row["source_theorem_kernel_verified"] is False
    assert row["source_theorem_kernel_evidence_eligible"] is False
    learning_manifest = manifest["runtime_learning_export"]
    assert manifest["runtime_learning_rows_jsonl"] == learning_manifest[
        "runtime_learning_rows_jsonl"
    ]
    assert manifest["runtime_learning_manifest"] == learning_manifest[
        "runtime_learning_manifest"
    ]
    assert manifest["n_runtime_learning_rows"] == 1
    assert learning_manifest["n_proof_body_goal_reached"] == 1
    assert learning_manifest["n_proof_body_goal_excerpt_rows"] == 1
    assert any(
        "unsolved goals" in line
        for line in learning_manifest["first_proof_body_goal_excerpt"]
    )
    assert learning_manifest["n_proof_body_goal_reached_with_semantic_blockers"] == 0
    assert learning_manifest["n_proof_body_gate_open_for_kernel_repair"] == 0
    rows = (
        tmp_path
        / "executor"
        / "runtime_learning_export"
        / "runtime_learning_rows.jsonl"
    ).read_text(encoding="utf-8")
    learning_row = json.loads(rows)
    assert learning_row["runtime_queue_status"] == (
        "PENDING_EXACT_SOURCE_THEOREM_PROOF_BODY_REPAIR"
    )
    assert learning_row["failure_classification"] == "proof_body_incomplete"
    assert any(
        "unsolved goals" in line
        for line in learning_row["proof_body_goal_excerpt"]
    )
    assert learning_row["execution_status"] == "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
    assert learning_row["trigger"] == (
        "EXACT_SOURCE_PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert learning_row["proof_body_attempt_count"] >= 1
    assert learning_row["proof_body_attempt_summaries"]
    assert "ProofEngineer runtime feedback" in learning_row["target_behavior"]
    assert "Route to ProofEngineer" in learning_row["recommended_next_action"]
    assert learning_row["source_theorem_kernel_verified"] is False
    assert learning_row["artifact_kernel_verified"] is False
    assert learning_row["source_theorem_exact_proof_body_reached"] is True
    assert learning_row[
        "source_theorem_exact_proof_body_gate_open_for_kernel_repair"
    ] is False
    assert learning_row[
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == []
    assert learning_row[
        "source_theorem_exact_proof_body_gate_open_target_ids"
    ] == []
    assert learning_row["candidate_artifact_path"] == str(candidate)
    assert learning_row["signature_probe_artifact_path"] == str(signature)


def test_exact_source_executor_approved_semantic_review_unblocks_guidance_constraints(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    reviewed_definition = tmp_path / "reviewed_definition.lean"
    reviewed_definition.write_text("def good_rank_event : True := True\n", encoding="utf-8")
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:approved_review",
                "source_work_order_id": "exact_source_work_order:approved_review",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "semantic_alignment_constraints": [
                    (
                        "Quantile threshold q is supplied as a hypothesis rather "
                        "than constructed inline to avoid unresolved C_n/good_rank_event "
                        "placeholders"
                    ),
                    "reviewed exact semantic-definition candidate approved for proof-body recheck",
                ],
                "semantic_alignment_blockers": [],
                "reviewed_exact_semantic_definition_artifact_path": str(
                    reviewed_definition
                ),
                "reviewed_exact_semantic_definition_artifact_paths": [
                    str(reviewed_definition)
                ],
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:approved_review",
                    "mcp_tool_calls": [
                        {
                            "tool": "lean_goal",
                            "arguments": {"file": str(signature), "line": 1, "column": 1},
                        },
                        {
                            "tool": "lean_multi_attempt",
                            "arguments": {"file": str(signature), "line": 1, "column": 1},
                        },
                    ],
                    "proof_body_attempts": ["simp"],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                    "definition_candidate_review_modes": [
                        "typechecked_candidate_source_semantic_review_approved"
                    ],
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=True,
        lean_command=(
            "python3",
            "-c",
            "import sys; print('error: unsolved goals\\n⊢ target_goal'); sys.exit(1)",
        ),
    )

    assert manifest["n_semantic_alignment_blocker_rows"] == 0
    assert manifest["n_proof_body_goal_reached_with_semantic_blockers"] == 0
    assert manifest["n_proof_body_gate_open_for_kernel_repair"] == 1
    assert manifest["proof_body_gate_open_target_names"] == [
        "split_conformal_coverage"
    ]
    assert manifest["proof_body_gate_open_target_ids"] == ["split_conformal_coverage"]
    assert manifest["n_proof_body_attempted"] == 1
    assert manifest["dominant_failure_classification"] == "proof_body_incomplete"
    row = manifest["rows"][0]
    assert row["semantic_alignment_blockers"] == ()
    assert row["proof_body_attempted"] is True
    assert row["proof_body_attempt_source"] != (
        "semantic_alignment_open_skip_tactic_attempts"
    )
    assert row["proof_body_gate_status"] == "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    assert row["failure_classification"] == "proof_body_incomplete"
    assert row["source_theorem_kernel_evidence_eligible"] is True
    request = row["candidate_live_proof_state_request"]
    assert request["proof_body_attempts"]
    assert [call["tool"] for call in request["mcp_tool_calls"]] == [
        "lean_goal",
        "lean_multi_attempt",
    ]
    learning_rows = (
        tmp_path
        / "executor"
        / "runtime_learning_export"
        / "runtime_learning_rows.jsonl"
    ).read_text(encoding="utf-8")
    learning_row = json.loads(learning_rows)
    assert learning_row["runtime_queue_status"] == (
        "PENDING_EXACT_SOURCE_THEOREM_PROOF_BODY_REPAIR"
    )
    assert learning_row["trigger"] == (
        "EXACT_SOURCE_PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    )
    assert learning_row["failure_classification"] == "proof_body_incomplete"
    assert (
        learning_row["source_theorem_exact_proof_body_gate_open_for_kernel_repair"]
        is True
    )
    assert learning_row["source_theorem_exact_proof_body_reached"] is True
    assert learning_row[
        "source_theorem_exact_proof_body_gate_open_target_names"
    ] == ["split_conformal_coverage"]
    assert learning_row[
        "source_theorem_exact_proof_body_gate_open_target_ids"
    ] == ["split_conformal_coverage"]
    assert learning_row["candidate_artifact_path"] == str(candidate)
    assert learning_row["signature_probe_artifact_path"] == str(signature)
    learning_manifest = manifest["runtime_learning_export"]
    assert learning_manifest["n_proof_body_gate_open_for_kernel_repair"] == 1
    assert learning_manifest["proof_body_gate_open_target_names"] == [
        "split_conformal_coverage"
    ]


def test_exact_source_executor_does_not_treat_static_safety_constraints_as_blockers(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:static_safety",
                "source_work_order_id": "exact_source_work_order:static_safety",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "semantic_alignment_constraints": [
                    (
                        "Adapter must not claim coverage probability; it reduces "
                        "to rank-order arithmetic only"
                    ),
                    "No sorry, admit, placeholder, or unsafe in sketch",
                    "Proof body is a proposal; kernel verification required before promotion",
                ],
                "semantic_alignment_blockers": [],
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:static_safety",
                    "mcp_tool_calls": [],
                    "proof_body_attempts": ["simp"],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=True,
        lean_command=(
            "python3",
            "-c",
            "import sys; print('error: unsolved goals\\n⊢ target_goal'); sys.exit(1)",
        ),
    )

    assert manifest["n_semantic_alignment_blocker_rows"] == 0
    assert manifest["n_proof_body_attempted"] == 1
    assert manifest["dominant_failure_classification"] == "proof_body_incomplete"
    row = manifest["rows"][0]
    assert row["semantic_alignment_blockers"] == ()
    assert row["proof_body_attempted"] is True
    assert row["proof_body_gate_status"] == "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    assert row["failure_classification"] == "proof_body_incomplete"


def test_exact_source_executor_honors_explicit_semantic_alignment_blockers(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:explicit_blocker",
                "source_work_order_id": "exact_source_work_order:explicit_blocker",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "semantic_alignment_constraints": [
                    "No sorry, admit, placeholder, or unsafe in sketch",
                ],
                "semantic_alignment_blockers": [
                    "review exact coverage_event definition before proof body",
                ],
                "definition_candidate_review_modes": [
                    "typechecked_candidate_source_semantic_review_approved"
                ],
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:explicit_blocker",
                    "mcp_tool_calls": [
                        {
                            "tool": "lean_multi_attempt",
                            "arguments": {"file": str(signature)},
                        }
                    ],
                    "proof_body_attempts": ["simp"],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=True,
        lean_command=(
            "python3",
            "-c",
            "import sys; print('error: unsolved goals\\n⊢ target_goal'); sys.exit(1)",
        ),
    )

    assert manifest["n_semantic_alignment_blocker_rows"] == 1
    assert manifest["n_proof_body_attempted"] == 0
    row = manifest["rows"][0]
    assert row["semantic_alignment_blockers"] == (
        "review exact coverage_event definition before proof body",
    )
    assert row["proof_body_attempted"] is False
    assert row["proof_body_attempt_source"] == (
        "semantic_alignment_open_skip_tactic_attempts"
    )
    assert row["proof_body_gate_status"] == (
        "PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED"
    )
    assert row["failure_classification"] == (
        "proof_body_reached_semantic_alignment_unreviewed"
    )
    assert row["candidate_live_proof_state_request"]["mcp_tool_calls"] == []


def test_exact_source_executor_routes_unready_queue_to_candidate_materialization(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:unready",
                "source_work_order_id": "exact_source_work_order:unready",
                "target_theorem_name": "split_conformal_coverage",
                "target_ids": ["split_conformal_coverage"],
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "semantic_alignment_constraints": [
                    "No sorry, admit, placeholder, or unsafe in sketch",
                ],
                "source_theorem_proof_body_adapter_kernel_verified": True,
                "kernel_verified_source_theorem_proof_body_adapter_ids": [
                    "source_theorem_proof_body_adapter_check:verified"
                ],
                "kernel_verified_source_to_bridge_premise_derivation_ids": [
                    "source_to_bridge_premise_derivation_check:hGoodCovered"
                ],
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": False,
                "live_proof_state_request": {},
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": False,
                },
                "execution_status": "BLOCKED_EXACT_SOURCE_PROOF_BODY_TARGET_LOCATION",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=False,
    )

    assert manifest["by_failure_classification"] == {
        "source_theorem_candidate_materialization_required": 1
    }
    row = manifest["rows"][0]
    assert row["failure_classification"] == (
        "source_theorem_candidate_materialization_required"
    )
    assert row["execution_status"] == "EXACT_SOURCE_PROOF_BODY_STATIC_CHECK_FAILED"
    assert row["proof_body_gate_status"] == "PROOF_BODY_NOT_CHECKED"
    assert "execution queue row is not ready" in row["errors"][0]
    assert "target_lean_declaration missing" in row["errors"]
    assert "signature_probe_artifact_path missing" in row["errors"]
    learning_row = json.loads(
        (
            tmp_path
            / "executor"
            / "runtime_learning_export"
            / "runtime_learning_rows.jsonl"
        ).read_text(encoding="utf-8")
    )
    assert learning_row["runtime_queue_status"] == (
        "PENDING_EXACT_SOURCE_THEOREM_CANDIDATE_MATERIALIZATION"
    )
    assert learning_row["trigger"] == (
        "EXACT_SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED"
    )
    assert learning_row["candidate_materialization_required"] is True
    assert learning_row["candidate_materialization_statuses"] == [
        "EXACT_SOURCE_PROOF_BODY_QUEUE_NOT_READY",
        "EXACT_SOURCE_THEOREM_TARGET_LOCATION_MISSING",
        "SIGNATURE_PROBE_ARTIFACT_PATH_MISSING",
    ]
    assert "exact source-theorem Lean candidate artifact" in learning_row[
        "candidate_materialization_contract"
    ]
    assert "source-theorem candidate materialization feedback" in learning_row[
        "target_behavior"
    ]
    assert learning_row["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
    )


def test_exact_source_executor_classifies_missing_proof_dependency_context(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    fake_lean = tmp_path / "fake_lean.py"
    fake_lean.write_text(
        "import sys\n"
        "path = sys.argv[-1]\n"
        "if '.proof_body_attempt_' in path:\n"
        "    print(path + ':1:8: error(lean.unknownIdentifier): Unknown identifier '\n"
        "          '`split_conformal_finite_sample_coverage_reduction_closure`')\n"
        "    sys.exit(1)\n"
        "print(path + ':1:1: error: unsolved goals')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:missing_dependency",
                "source_work_order_id": "exact_source_work_order:missing_dependency",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_kernel_evidence_eligible": True,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "semantic_alignment_constraints": [],
                "semantic_alignment_blockers": [],
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:missing_dependency",
                    "mcp_tool_calls": [],
                    "proof_body_attempts": [
                        "exact split_conformal_finite_sample_coverage_reduction_closure"
                    ],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=True,
        lean_command=("python3", str(fake_lean)),
    )

    row = manifest["rows"][0]
    assert row["proof_body_goal_reached"] is True
    assert row["source_theorem_kernel_verified"] is False
    assert row["failure_classification"] == "proof_body_dependency_context_missing"
    assert manifest["by_failure_classification"] == {
        "proof_body_dependency_context_missing": 1
    }
    assert any(
        "diagnostic_kind=unknown_identifier" in summary
        and "split_conformal_finite_sample_coverage_reduction_closure" in summary
        for summary in row["proof_body_attempt_summaries"]
    )
    learning_row = json.loads(
        (
            tmp_path
            / "executor"
            / "runtime_learning_export"
            / "runtime_learning_rows.jsonl"
        ).read_text(encoding="utf-8")
    )
    assert learning_row["runtime_queue_status"] == (
        "PENDING_EXACT_SOURCE_THEOREM_PROOF_DEPENDENCY_CONTEXT"
    )
    assert learning_row["trigger"] == (
        "EXACT_SOURCE_PROOF_BODY_DEPENDENCY_CONTEXT_MISSING"
    )
    assert "dependency-context feedback" in learning_row["target_behavior"]
    assert "Import, inline, or materialize" in learning_row["recommended_next_action"]


def test_exact_source_executor_routes_closure_type_mismatch_to_adapter(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    signature = tmp_path / "signature.lean"
    signature.write_text(
        "theorem split_conformal_coverage : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    closure = tmp_path / "closure.lean"
    closure.write_text(
        "theorem splitConformalFiniteSampleCoverage_reductionClosure : True := by\n"
        "  trivial\n",
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.lean"
    transcript = tmp_path / "transcript.jsonl"
    fake_lean = tmp_path / "fake_lean.py"
    fake_lean.write_text(
        "import sys\n"
        "path = sys.argv[-1]\n"
        "if '.proof_body_attempt_' in path:\n"
        "    print(path + ':1:8: error: typeclass instance problem is stuck')\n"
        "    sys.exit(1)\n"
        "print(path + ':1:1: error: unsolved goals')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:adapter_needed",
                "source_work_order_id": "exact_source_work_order:adapter_needed",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_kernel_evidence_eligible": True,
                "source_theorem_target_identity_status": "SOURCE_THEOREM_TARGET_KNOWN",
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(signature),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "kernel_verified_theorem_reduction_closure_declarations": [
                    "splitConformalFiniteSampleCoverage_reductionClosure"
                ],
                "verified_theorem_reduction_closure_artifact_paths": [str(closure)],
                "kernel_verified_theorem_reduction_closure_target_ids": [
                    "split_conformal_finite_sample_coverage_reduction_closure"
                ],
                "proof_body_attempts": [
                    "exact splitConformalFiniteSampleCoverage_reductionClosure"
                ],
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:adapter_needed",
                    "mcp_tool_calls": [],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        local_lean=True,
        lean_command=("python3", str(fake_lean)),
    )

    row = manifest["rows"][0]
    assert row["proof_body_goal_reached"] is True
    assert row["source_theorem_kernel_verified"] is False
    assert row["failure_classification"] == (
        "proof_body_reduction_closure_adapter_instantiation_missing"
    )
    assert manifest["by_failure_classification"] == {
        "proof_body_reduction_closure_adapter_instantiation_missing": 1
    }
    learning_row = json.loads(
        (
            tmp_path
            / "executor"
            / "runtime_learning_export"
            / "runtime_learning_rows.jsonl"
        ).read_text(encoding="utf-8")
    )
    assert learning_row["runtime_queue_status"] == (
        "PENDING_SOURCE_THEOREM_PROOF_BODY_ADAPTER_INSTANTIATION"
    )
    assert learning_row["trigger"] == (
        "EXACT_SOURCE_PROOF_BODY_REDUCTION_CLOSURE_ADAPTER_REQUIRED"
    )
    assert "adapter synthesis" in learning_row["recommended_next_action"]
    assert "adapter feedback" in learning_row["target_behavior"]
    assert learning_row["source_theorem_kernel_verified"] is False


def test_exact_source_executor_reuses_same_source_candidate_when_overwrite_requested(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    transcript = tmp_path / "transcript.jsonl"
    queue_manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "rows": [
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                "execution_queue_id": "exact_source_queue:same_file",
                "source_work_order_id": "exact_source_work_order:same_file",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "expected_target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": False,
                "source_theorem_target_identity_status": (
                    "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
                ),
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                },
                "semantic_alignment_constraints": [],
                "target_identity_status": "TARGET_DECLARATION_MATCHED",
                "target_identity_errors": [],
                "signature_probe_artifact_path": str(candidate),
                "candidate_artifact_path": str(candidate),
                "execution_transcript_path": str(transcript),
                "live_goal_location_ready": True,
                "live_proof_state_request": {
                    "request_id": "live_goal:same_file",
                    "mcp_tool_calls": [],
                    "proof_body_attempts": [],
                },
                "already_repaired_environment": {
                    "missing_formal_symbols": [],
                    "typeclass_blockers": [],
                    "signature_typecheck_reached_proof_body": True,
                },
                "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
            }
        ],
    }
    (queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json").write_text(
        json.dumps(queue_manifest),
        encoding="utf-8",
    )

    manifest = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "executor",
        overwrite=True,
        local_lean=False,
    )

    assert manifest["n_execution_result_rows"] == 1
    row = manifest["rows"][0]
    assert row["execution_status"] == "EXACT_SOURCE_PROOF_BODY_CANDIDATE_REUSED"
    assert row["candidate_artifact_path"] == str(candidate)
    assert row["source_theorem_kernel_verified"] is False

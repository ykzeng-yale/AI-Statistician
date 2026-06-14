from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.exact_source_theorem_proof_body_executor import (
    export_exact_source_theorem_proof_body_execution_results,
)
from ai_statistician.source_theorem_formal_environment_proofengineer_bridge import (
    run_source_theorem_formal_environment_proofengineer_bridge,
)


def test_source_theorem_formal_environment_bridge_exports_repair_packets(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "split_conformal_coverage.lean"
    candidate_artifact.write_text(
        "import Mathlib.Probability.ProbabilityMeasure\n"
        "import Mathlib.Order.LocallyFiniteOrder\n\n"
        "theorem split_conformal_coverage {Ω : Type _} [MeasurableSpace Ω] "
        "(P : MeasureTheory.Measure Ω) [MeasureTheory.IsProbabilityMeasure P] "
        "(m : ℕ) (hm : 0 < m) (alpha : ℝ) "
        "(halpha : 0 < alpha ∧ alpha < 1) "
        "(s : Fin (m + 1) → Ω → ℝ) (hexch : Exchangeable P s) "
        "(k : ℕ) (hk : k = Nat.ceil ((m + 1 : ℝ) * (1 - alpha))) "
        "(q_hat : Ω → ℝ) (hq : ∀ ω, q_hat ω = orderStat s k ω) : "
        "P {ω | s (Fin.last m) ω ≤ q_hat ω} ≥ 1 - alpha := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:env",
                "question_id": "split_conformal",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_route_id": "route:split_conformal_source",
                "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
                "source_theorem_statement": (
                    "split conformal finite-sample marginal coverage under exchangeability"
                ),
                "source_theorem_skeleton": (
                    "exchangeability -> uniform rank -> conformal coverage"
                ),
                "source_theorem_lean_file": "StatInference/Conformal/SplitCoverage.lean",
                "semantic_alignment_constraints": [
                    "preserve marginal coverage target",
                    "do not strengthen exchangeability assumptions",
                ],
                "candidate_artifact_path": str(candidate_artifact),
                "failure_classification": "formal_environment_symbol_missing",
                "diagnostics": [
                    "failed to synthesize instance of type class",
                    "  HSub ℕ ℝ ENNReal",
                    "Function expected at",
                    "  Exchangeable",
                    "Hint: The identifier `Exchangeable` is unknown.",
                    "Function expected at",
                    "  orderStat",
                    "Hint: The identifier `orderStat` is unknown.",
                ],
                "missing_formal_symbols": ["Exchangeable", "orderStat"],
                "typeclass_blockers": ["HSub ℕ ℝ ENNReal"],
                "recommended_repair_tasks": [
                    "resolve Lean declaration/import or explicitly formalize source-theorem primitive `Exchangeable`",
                    "resolve Lean declaration/import or explicitly formalize source-theorem primitive `orderStat`",
                    "repair exact source-theorem statement so Lean can synthesize typeclass instance `HSub ℕ ℝ ENNReal` without coercion ambiguity",
                ],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue_jsonl,
        question_id="split_conformal",
        run_signature_probes=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_repair_packets"] == 1
    assert manifest["n_missing_formal_symbols"] == 2
    assert manifest["n_typeclass_blockers"] == 1
    assert manifest["signature_probes_requested"] is True
    assert manifest["n_signature_probe_rows"] == 1
    assert manifest["n_signature_probes_reached_proof_body"] == 1
    assert manifest["signature_probe_proof_evidence_status"] == (
        "SIGNATURE_PROBE_NOT_PROOF_EVIDENCE"
    )
    assert manifest["n_proof_body_work_orders"] == 1
    assert manifest["proof_body_work_order_proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    assert manifest["n_proof_body_execution_queue_rows"] == 1
    assert manifest["n_proof_body_execution_live_goal_requests"] == 1
    assert manifest["proof_body_execution_queue_proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
    )
    assert manifest["proof_evidence_status"] == (
        "FORMAL_ENVIRONMENT_REPAIR_PACKETS_NOT_PROOF_EVIDENCE"
    )
    repair_packets_path = Path(str(manifest["repair_packets_jsonl"]))
    repair_packet = json.loads(repair_packets_path.read_text(encoding="utf-8"))
    assert repair_packet["artifact_kind"] == "SourceTheoremFormalEnvironmentRepairPacket"
    assert repair_packet["missing_formal_symbols"] == ["Exchangeable", "orderStat"]
    assert repair_packet["typeclass_blockers"] == ["HSub ℕ ℝ ENNReal"]
    assert repair_packet["source_theorem_target_known"] is True
    assert repair_packet["target_lean_declaration"] == "split_conformal_coverage"
    assert repair_packet["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert repair_packet["source_theorem_target_provenance"][
        "source_theorem_statement"
    ] == "split conformal finite-sample marginal coverage under exchangeability"
    assert repair_packet["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert repair_packet["repair_status"] == "FORMAL_ENVIRONMENT_REPAIR_REQUIRED"
    assert any("search Mathlib/StatInference" in row for row in repair_packet["proofengineer_action_plan"])
    declaration_hints = repair_packet["formal_environment_declaration_hints"]
    assert {hint["symbol"] for hint in declaration_hints} == {"Exchangeable", "orderStat"}
    assert any(
        "semantic primitive" in hint["signature_probe_fallback"]
        for hint in declaration_hints
    )
    statement_hints = repair_packet["statement_repair_hints"]
    assert statement_hints[0]["blocker"] == "HSub ℕ ℝ ENNReal"
    assert "ENNReal.ofReal (1 - alpha)" in statement_hints[0]["repair_hint"]
    signature_probe_plan = repair_packet["lean_signature_probe_plan"]
    assert signature_probe_plan["probe_kind"] == "statement_typecheck_not_proof"
    assert signature_probe_plan["proof_evidence_status"] == (
        "SIGNATURE_PROBE_PLAN_NOT_PROOF_EVIDENCE"
    )
    assert repair_packet["proof_evidence_status"] == "REPAIR_PACKET_NOT_PROOF_EVIDENCE"
    probe_manifest = json.loads(
        Path(str(manifest["signature_probe_manifest"])).read_text(encoding="utf-8")
    )
    probe_row = probe_manifest["rows"][0]
    assert probe_row["signature_typecheck_reached_proof_body"] is True
    assert probe_row["signature_probe_status"] == (
        "SIGNATURE_PROBE_REACHED_PROOF_BODY_NOT_PROOF"
    )
    probe_source = Path(probe_row["signature_probe_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert "def Exchangeable" in probe_source
    assert "def orderStat" in probe_source
    assert "import Mathlib.MeasureTheory.Measure.ProbabilityMeasure\n" in probe_source
    assert "import Mathlib.Data.Real.Basic\n" in probe_source
    assert "import Mathlib.Data.Fin.Basic\n" in probe_source
    assert "import Mathlib.Data.ENNReal.Basic\n" in probe_source
    assert "import Mathlib\n" not in probe_source
    assert "import Mathlib.Probability.ProbabilityMeasure" not in probe_source
    assert "import Mathlib.Order.LocallyFiniteOrder" not in probe_source
    assert "ENNReal.ofReal (1 - alpha)" in probe_source
    assert probe_manifest["proof_evidence_status"] == "SIGNATURE_PROBE_NOT_PROOF_EVIDENCE"
    proof_body_rows_path = Path(str(manifest["proof_body_work_orders_jsonl"]))
    proof_body_work_order = json.loads(proof_body_rows_path.read_text(encoding="utf-8"))
    assert proof_body_work_order["artifact_kind"] == "ExactSourceTheoremProofBodyWorkOrder"
    assert proof_body_work_order["target_theorem_name"] == "split_conformal_coverage"
    assert proof_body_work_order["target_lean_declaration"] == "split_conformal_coverage"
    assert proof_body_work_order["source_theorem_target_known"] is True
    assert proof_body_work_order["source_theorem_target_provenance"][
        "source_theorem_goal_id"
    ] == "split_conformal_finite_sample_coverage"
    assert proof_body_work_order["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert proof_body_work_order["proof_body_failure_classification"] == (
        "proof_body_incomplete"
    )
    assert proof_body_work_order["proof_body_goal_excerpt"] == ["unsolved goals"]
    assert proof_body_work_order["already_repaired_environment"][
        "signature_typecheck_reached_proof_body"
    ] is True
    assert any(
        "do not change the theorem statement" in row
        for row in proof_body_work_order["forbidden_actions"]
    )
    assert proof_body_work_order["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    execution_queue_manifest = json.loads(
        Path(str(manifest["proof_body_execution_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    execution_row = execution_queue_manifest["rows"][0]
    assert execution_row["artifact_kind"] == "ExactSourceTheoremProofBodyExecutionQueueRow"
    assert execution_row["execution_status"] == "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
    assert execution_row["owner_agent"] == "FormalizerProofEngineer"
    assert execution_row["target_theorem_name"] == "split_conformal_coverage"
    assert execution_row["expected_target_lean_declaration"] == (
        "split_conformal_coverage"
    )
    assert execution_row["source_theorem_target_known"] is True
    assert execution_row["source_theorem_target_provenance"][
        "source_theorem_lean_file"
    ] == "StatInference/Conformal/SplitCoverage.lean"
    assert execution_row["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert execution_row["live_goal_location_ready"] is True
    assert execution_row["target_lean_declaration"] == "split_conformal_coverage"
    assert execution_row["already_repaired_environment"]["missing_formal_symbols"] == [
        "Exchangeable",
        "orderStat",
    ]
    assert execution_row["target_identity_status"] == "TARGET_DECLARATION_MATCHED"
    assert execution_row["live_proof_state_request"]["provider_preferences"][0] == (
        "lean_lsp_mcp"
    )
    assert execution_row["live_proof_state_request"][
        "expected_target_lean_declaration"
    ] == "split_conformal_coverage"
    assert execution_row["live_proof_state_request"][
        "source_theorem_target_provenance"
    ]["source_theorem_route_id"] == "route:split_conformal_source"
    assert {
        call["tool"] for call in execution_row["live_proof_state_request"]["mcp_tool_calls"]
    } >= {"lean_goal", "lean_diagnostic_messages", "lean_local_search", "lean_multi_attempt"}
    assert "copy signature_probe_artifact_path" in " ".join(execution_row["command_plan"])
    assert "no sorry/admit/axiom/unsafe tokens" in execution_row["required_static_checks"]
    assert execution_row["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
    )

    learning_rows_path = Path(str(manifest["runtime_learning_rows_jsonl"]))
    learning_row = json.loads(learning_rows_path.read_text(encoding="utf-8"))
    assert learning_row["learning_task"] == (
        "source_theorem_formal_environment_repair_feedback"
    )
    assert learning_row["input_summary"]["trigger"] == (
        "SOURCE_THEOREM_FORMAL_ENVIRONMENT_REPAIR_REQUIRED"
    )
    assert learning_row["input_summary"]["missing_formal_symbols"] == [
        "Exchangeable",
        "orderStat",
    ]
    assert learning_row["input_summary"]["lean_signature_probe_plan"]["probe_kind"] == (
        "statement_typecheck_not_proof"
    )
    assert learning_row["input_summary"]["signature_probe_rows"][0][
        "signature_typecheck_reached_proof_body"
    ] is True
    assert learning_row["input_summary"]["proof_body_work_orders"][0][
        "target_theorem_name"
    ] == "split_conformal_coverage"
    assert learning_row["input_summary"]["proof_body_execution_queue_rows"][0][
        "execution_status"
    ] == "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
    assert learning_row["input_summary"]["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert learning_row["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    export_manifest = json.loads(
        Path(str(manifest["runtime_learning_export_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    assert export_manifest["n_proof_body_work_orders"] == 1
    assert export_manifest["proof_body_work_order_proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    assert export_manifest["n_proof_body_execution_queue_rows"] == 1
    assert export_manifest["proof_body_execution_queue_proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
    )
    assert "statement_repair_hints" in learning_row["input_summary"]
    assert learning_row["proof_evidence_status"] == (
        "FORMAL_ENVIRONMENT_REPAIR_LEARNING_NOT_PROOF_EVIDENCE"
    )

    execution_payload = export_exact_source_theorem_proof_body_execution_results(
        Path(str(manifest["proof_body_execution_queue_manifest"])).parent,
        tmp_path / "proof_body_executor",
        overwrite=True,
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )
    assert execution_payload["n_execution_result_rows"] == 1
    assert execution_payload["n_materialized_candidate_artifacts"] == 1
    assert execution_payload["n_local_lean_checked"] == 1
    assert execution_payload["n_local_lean_compiled"] == 0
    assert execution_payload["n_artifact_kernel_verified"] == 0
    assert execution_payload["n_source_theorem_kernel_verified"] == 0
    assert execution_payload["n_placeholder_environment_blockers"] == 1
    assert execution_payload["n_source_theorem_target_known"] == 1
    assert execution_payload["n_semantic_alignment_constraint_rows"] == 1
    assert execution_payload["source_theorem_route_ids"] == [
        "route:split_conformal_source"
    ]
    execution_result = execution_payload["rows"][0]
    assert execution_result["execution_status"] == (
        "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
    )
    assert execution_result["failure_classification"] == (
        "formal_environment_placeholder_primitives"
    )
    assert execution_result["source_theorem_kernel_verified"] is False
    assert execution_result["source_theorem_target_known"] is True
    assert execution_result["expected_target_lean_declaration"] == (
        "split_conformal_coverage"
    )
    assert execution_result["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert list(execution_result["semantic_alignment_constraints"]) == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert execution_result["target_identity_status"] == "TARGET_DECLARATION_MATCHED"
    assert execution_result["candidate_live_proof_state_request"][
        "target_lean_file"
    ] == execution_result["candidate_artifact_path"]
    assert execution_result["candidate_live_proof_state_request"]["mcp_tool_calls"][0][
        "arguments"
    ]["file"] == execution_result["candidate_artifact_path"]
    candidate_source = Path(execution_result["candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert "def Exchangeable" in candidate_source
    transcript_event = json.loads(
        Path(execution_result["execution_transcript_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert transcript_event["event"] == (
        "exact_source_theorem_proof_body_execution_result"
    )
    assert transcript_event["source_theorem_kernel_verified"] is False
    assert transcript_event["source_theorem_target_provenance"][
        "source_theorem_goal_id"
    ] == "split_conformal_finite_sample_coverage"
    assert transcript_event["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    learning_export = execution_payload["runtime_learning_export"]
    assert learning_export["n_source_theorem_target_known"] == 1
    assert learning_export["n_semantic_alignment_constraint_rows"] == 1
    assert learning_export["source_theorem_route_ids"] == [
        "route:split_conformal_source"
    ]
    executor_learning_row = json.loads(
        Path(str(learning_export["runtime_learning_rows_jsonl"])).read_text(
            encoding="utf-8"
        )
    )
    assert executor_learning_row["learning_task"] == (
        "exact_source_theorem_proof_body_execution_feedback"
    )
    assert executor_learning_row["trigger"] == (
        "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
    )
    assert executor_learning_row["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert executor_learning_row["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert executor_learning_row["kernel_verified_source_theorem_ids"] == []

    cli_out = tmp_path / "bridge_cli"
    code = main(
        [
            "source-theorem-formal-environment-proofengineer-bridge",
            "--queue-jsonl",
            str(queue_jsonl),
            "--question-id",
            "split_conformal",
            "--out",
            str(cli_out),
        ]
    )
    assert code == 0
    cli_manifest = json.loads(
        (
            cli_out
            / "source_theorem_formal_environment_proofengineer_bridge_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert cli_manifest["n_repair_packets"] == 1
    assert cli_manifest["runtime_learning_ready"] is True


def test_signature_probe_does_not_queue_proof_body_with_environment_errors(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "bad_environment_source_claim.lean"
    candidate_artifact.write_text(
        "import Mathlib.Probability.ProbabilityMeasure\n\n"
        "theorem bad_environment_source_claim {Ω : Type _} "
        "(P : MeasureProbability Ω) : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:bad_env",
                "question_id": "split_conformal",
                "target_theorem_name": "bad_environment_source_claim",
                "target_lean_declaration": "bad_environment_source_claim",
                "source_theorem_target_known": True,
                "candidate_artifact_path": str(candidate_artifact),
                "failure_classification": "formal_environment_symbol_missing",
                "diagnostics": [
                    "Function expected at",
                    "  MeasureProbability",
                    "error: unsolved goals",
                ],
                "missing_formal_symbols": [],
                "typeclass_blockers": [],
                "recommended_repair_tasks": [
                    "replace nonexistent MeasureProbability with a real Mathlib probability measure type"
                ],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue_jsonl,
        question_id="split_conformal",
        run_signature_probes=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('Function expected at\\n  MeasureProbability\\nerror: unsolved goals'); sys.exit(1)",
        ),
    )

    assert manifest["n_signature_probe_rows"] == 1
    assert manifest["n_signature_probes_reached_proof_body"] == 0
    assert manifest["n_proof_body_work_orders"] == 0
    assert manifest["n_proof_body_execution_queue_rows"] == 0
    probe_manifest = json.loads(
        Path(str(manifest["signature_probe_manifest"])).read_text(encoding="utf-8")
    )
    probe_row = probe_manifest["rows"][0]
    assert probe_row["failure_classification"] == "formal_environment_symbol_missing"
    assert probe_row["signature_probe_status"] == "SIGNATURE_PROBE_LOCAL_LEAN_FAILED"
    assert probe_row["signature_typecheck_reached_proof_body"] is False


def test_proof_body_execution_queue_blocks_target_declaration_mismatch(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "nearby_claim.lean"
    candidate_artifact.write_text(
        "import Mathlib\n\n"
        "theorem nearby_claim : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:mismatch",
                "target_theorem_name": "exact_source_claim",
                "target_lean_declaration": "exact_source_claim",
                "source_theorem_target_known": True,
                "source_theorem_route_id": "route:exact_source_claim",
                "candidate_artifact_path": str(candidate_artifact),
                "failure_classification": "formal_environment_symbol_missing",
                "diagnostics": ["Hint: The identifier `MissingPrimitive` is unknown."],
                "missing_formal_symbols": ["MissingPrimitive"],
                "typeclass_blockers": [],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue_jsonl,
        run_signature_probes=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )

    execution_queue_manifest = json.loads(
        Path(str(manifest["proof_body_execution_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    execution_row = execution_queue_manifest["rows"][0]
    assert execution_row["execution_status"] == (
        "BLOCKED_EXACT_SOURCE_PROOF_BODY_TARGET_IDENTITY"
    )
    assert execution_row["live_goal_location_ready"] is False
    assert execution_row["target_lean_declaration"] == "nearby_claim"
    assert execution_row["expected_target_lean_declaration"] == "exact_source_claim"
    assert execution_row["target_identity_status"] == "TARGET_DECLARATION_MISMATCH"
    assert "nearby_claim" in execution_row["target_identity_errors"][0]
    assert execution_row["live_proof_state_request"] == {}

from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.source_theorem_formal_environment_proofengineer_bridge import (
    run_source_theorem_formal_environment_proofengineer_bridge,
)


def test_source_theorem_formal_environment_bridge_exports_repair_packets(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "split_conformal_coverage.lean"
    candidate_artifact.write_text(
        "import Mathlib\n\n"
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
    assert "ENNReal.ofReal (1 - alpha)" in probe_source
    assert probe_manifest["proof_evidence_status"] == "SIGNATURE_PROBE_NOT_PROOF_EVIDENCE"
    proof_body_rows_path = Path(str(manifest["proof_body_work_orders_jsonl"]))
    proof_body_work_order = json.loads(proof_body_rows_path.read_text(encoding="utf-8"))
    assert proof_body_work_order["artifact_kind"] == "ExactSourceTheoremProofBodyWorkOrder"
    assert proof_body_work_order["target_theorem_name"] == "split_conformal_coverage"
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
    assert execution_row["live_goal_location_ready"] is True
    assert execution_row["target_lean_declaration"] == "split_conformal_coverage"
    assert execution_row["live_proof_state_request"]["provider_preferences"][0] == (
        "lean_lsp_mcp"
    )
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

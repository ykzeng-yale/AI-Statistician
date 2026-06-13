from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.source_theorem_formal_environment_proofengineer_bridge import (
    run_source_theorem_formal_environment_proofengineer_bridge,
)


def test_source_theorem_formal_environment_bridge_exports_repair_packets(
    tmp_path: Path,
) -> None:
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:env",
                "question_id": "split_conformal",
                "target_theorem_name": "split_conformal_coverage",
                "candidate_artifact_path": "/tmp/split_conformal_coverage.lean",
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
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_repair_packets"] == 1
    assert manifest["n_missing_formal_symbols"] == 2
    assert manifest["n_typeclass_blockers"] == 1
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
    assert repair_packet["proof_evidence_status"] == "REPAIR_PACKET_NOT_PROOF_EVIDENCE"

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

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import ai_statistician.theorem_reduction_closure_work_order_audit as closure_audit
from ai_statistician.theorem_reduction_closure_work_order_audit import (
    audit_theorem_reduction_closure_work_orders,
)
from ai_statistician.cli import main


def test_theorem_reduction_closure_work_order_audit_exports_without_proof_claim(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "queue.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "artifact_kind": "TheoremReductionClosureWorkOrder",
                "work_order_id": "theorem_reduction_closure_work_order:smoke",
                "question_id": "conformal_prediction_coverage",
                "source_formal_target_id": "split_conformal_finite_sample_coverage_reduction_closure",
                "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
                "verified_bridge_obligation_ids": ["prob_measure_univ"],
                "lean_statement_sketch": "theorem closure_smoke : True := by\n  trivial",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = audit_theorem_reduction_closure_work_orders(
        queue_path,
        tmp_path / "audit",
        run_local_lean=False,
    )

    assert manifest["artifact_kind"] == "TheoremReductionClosureWorkOrderAuditManifest"
    assert manifest["n_work_orders"] == 1
    assert manifest["n_exported_lean_sketches"] == 1
    assert manifest["n_local_lean_attempted"] == 0
    assert manifest["n_kernel_verified"] == 0
    assert manifest["local_lean_timeout_seconds"] == 240
    assert manifest["proof_evidence_status"] == "NO_KERNEL_VERIFIED_THEOREM_CLOSURE"
    check = manifest["checks"][0]
    assert check["status"] == "QUEUED_NOT_CHECKED"
    assert check["kernel_verified"] is False
    assert "not proof evidence" in check["boundary"]
    assert Path(check["lean_export_path"]).exists()
    assert Path(str(manifest["checks_jsonl"])).exists()


def test_theorem_reduction_closure_work_order_audit_rejects_placeholder_before_lean(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "queue.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "artifact_kind": "TheoremReductionClosureWorkOrder",
                "work_order_id": "theorem_reduction_closure_work_order:placeholder",
                "source_formal_target_id": "bad_closure",
                "lean_statement_sketch": "theorem bad_closure : True := by\n  sorry",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = audit_theorem_reduction_closure_work_orders(
        queue_path,
        tmp_path / "audit",
        run_local_lean=True,
        lean_project=tmp_path / "missing_lean_project",
    )

    assert manifest["n_placeholder_rejected"] == 1
    assert manifest["n_local_lean_attempted"] == 0
    assert manifest["n_kernel_verified"] == 0
    assert manifest["proof_evidence_status"] == "NO_KERNEL_VERIFIED_THEOREM_CLOSURE"
    check = manifest["checks"][0]
    assert check["status"] == "PLACEHOLDER_REJECTED"
    assert check["local_lean_attempted"] is False
    assert "candidate still contains sorry" in check["errors"]


def test_theorem_reduction_closure_local_lean_uses_absolute_export_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    queue_path = tmp_path / "queue.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "artifact_kind": "TheoremReductionClosureWorkOrder",
                "work_order_id": "theorem_reduction_closure_work_order:absolute_path",
                "question_id": "conformal_prediction_coverage",
                "source_formal_target_id": (
                    "split_conformal_finite_sample_coverage_reduction_closure"
                ),
                "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
                "verified_bridge_obligation_ids": ["prob_measure_univ"],
                "lean_statement_sketch": "theorem closure_absolute_path : True := by\n  trivial",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    lean_project = tmp_path / "LeanProject"
    lean_project.mkdir()
    (lean_project / "lakefile.toml").write_text("[package]\nname = \"Smoke\"\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run(cmd, *, cwd, capture_output, text, timeout, check):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["capture_output"] = capture_output
        captured["text"] = text
        captured["timeout"] = timeout
        captured["check"] = check
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(closure_audit.shutil, "which", lambda name: "/fake/lake")
    monkeypatch.setattr(closure_audit.subprocess, "run", fake_run)

    manifest = audit_theorem_reduction_closure_work_orders(
        queue_path,
        tmp_path / "audit",
        run_local_lean=True,
        lean_project=lean_project,
    )

    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert cmd[:3] == ["lake", "env", "lean"]
    assert Path(cmd[3]).is_absolute()
    assert captured["cwd"] == str(lean_project)
    assert manifest["n_kernel_verified"] == 1
    assert Path(manifest["checks"][0]["lean_export_path"]).is_absolute()


def test_theorem_reduction_closure_proofengineer_bridge_exports_learning_boundary(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "runtime_theorem_reduction_closure_work_orders.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "artifact_kind": "TheoremReductionClosureWorkOrder",
                "work_order_id": "theorem_reduction_closure_work_order:smoke",
                "question_id": "conformal_prediction_coverage",
                "source_formal_target_id": (
                    "split_conformal_finite_sample_coverage_reduction_closure"
                ),
                "target_theorem_goal_ids": ["split_conformal_finite_sample_coverage"],
                "verified_bridge_obligation_ids": ["prob_measure_univ"],
                "lean_statement_sketch": "theorem closure_smoke : True := by\n  trivial",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "bridge"

    code = main(
        [
            "theorem-reduction-closure-proofengineer-bridge",
            "--queue-jsonl",
            str(queue_path),
            "--question-id",
            "conformal_prediction_coverage",
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    bridge_manifest = json.loads(
        (
            out_dir / "theorem_reduction_closure_proofengineer_bridge_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert bridge_manifest["artifact_kind"] == (
        "TheoremReductionClosureProofEngineerBridgeManifest"
    )
    assert bridge_manifest["n_work_orders"] == 1
    assert bridge_manifest["n_kernel_verified"] == 0
    assert bridge_manifest["runtime_learning_ready"] is False
    assert bridge_manifest["proof_evidence_status"] == "NO_KERNEL_VERIFIED_THEOREM_CLOSURE"
    assert Path(bridge_manifest["audit_manifest"]).exists()
    assert Path(bridge_manifest["runtime_learning_rows_jsonl"]).exists()
    learning_export_manifest = json.loads(
        Path(bridge_manifest["runtime_learning_export_manifest"]).read_text(
            encoding="utf-8"
        )
    )
    assert (
        learning_export_manifest[
            "n_kernel_verified_theorem_reduction_closure_work_order_ids"
        ]
        == 0
    )
    assert "not proof evidence" in bridge_manifest["boundary"]

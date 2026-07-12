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
                "target_lean_declaration": "closure_smoke",
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
    assert check["target_lean_declaration"] == "closure_smoke"
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
                "target_lean_declaration": "bad_closure",
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


def test_theorem_reduction_closure_requires_structured_target_identity(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "queue.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "artifact_kind": "TheoremReductionClosureWorkOrder",
                "work_order_id": "theorem_reduction_closure_work_order:no_target",
                "lean_statement_sketch": (
                    "theorem unbound_candidate : True := by\n  trivial\n"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = audit_theorem_reduction_closure_work_orders(
        queue_path,
        tmp_path / "audit",
        run_local_lean=True,
    )

    check = manifest["checks"][0]
    assert check["status"] == "FORMAL_BLOCKED_MISSING_TARGET_DECLARATION"
    assert check["local_lean_attempted"] is False
    assert manifest["n_kernel_verified"] == 0


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
                "target_lean_declaration": "closure_absolute_path",
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
    export_path = Path(manifest["checks"][0]["lean_export_path"])
    assert export_path.is_absolute()
    assert export_path.read_text(encoding="utf-8") == (
        "theorem closure_absolute_path : True := by\n  trivial"
    )
    assert manifest["checks"][0]["candidate_bytes_preserved"] is True


def test_theorem_reduction_closure_malformed_candidate_reaches_real_lean_gate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    exact_candidate = "this is deliberately malformed Lean\n"
    queue_path = tmp_path / "queue.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "artifact_kind": "TheoremReductionClosureWorkOrder",
                "work_order_id": "theorem_reduction_closure_work_order:malformed",
                "target_lean_declaration": "malformed_candidate",
                "lean_statement_sketch": exact_candidate,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    lean_project = tmp_path / "LeanProject"
    lean_project.mkdir()
    (lean_project / "lakefile.toml").write_text(
        "[package]\nname = \"Smoke\"\n",
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    def fake_run(cmd, *, cwd, capture_output, text, timeout, check):
        candidate_path = Path(cmd[3])
        captured["candidate"] = candidate_path.read_text(encoding="utf-8")
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="unexpected identifier 'this'",
        )

    monkeypatch.setattr(closure_audit.shutil, "which", lambda name: "/fake/lake")
    monkeypatch.setattr(closure_audit.subprocess, "run", fake_run)

    manifest = audit_theorem_reduction_closure_work_orders(
        queue_path,
        tmp_path / "audit",
        run_local_lean=True,
        lean_project=lean_project,
    )

    check = manifest["checks"][0]
    assert captured["candidate"] == exact_candidate
    assert check["status"] == "LOCAL_LEAN_REJECTED"
    assert check["local_lean_attempted"] is True
    assert check["candidate_bytes_preserved"] is True
    assert check["kernel_checked_source_bytes"] == len(
        exact_candidate.encode("utf-8")
    )
    assert "unexpected identifier" in check["errors"][0]


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
                "target_lean_declaration": "closure_smoke",
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

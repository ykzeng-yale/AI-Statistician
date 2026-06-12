from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


def export_theorem_reduction_closure_learning_from_manifest(
    *,
    manifest_path: Path,
    out_dir: Path,
    question_id: str = "",
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = payload.get("checks", [])
    if not isinstance(checks, list):
        raise ValueError(
            "theorem reduction closure audit manifest checks is not a list: "
            f"{manifest_path}"
        )
    verified_checks = [
        row
        for row in checks
        if isinstance(row, Mapping) and row.get("kernel_verified") is True
    ]
    work_order_ids = [
        str(row.get("work_order_id", "")).strip()
        for row in verified_checks
        if str(row.get("work_order_id", "")).strip()
    ]
    target_ids = [
        str(row.get("source_formal_target_id", "")).strip()
        for row in verified_checks
        if str(row.get("source_formal_target_id", "")).strip()
    ]
    goal_ids: list[str] = []
    bridge_ids: list[str] = []
    for row in verified_checks:
        for goal_id in row.get("target_theorem_goal_ids", []) or []:
            text = str(goal_id).strip()
            if text and text not in goal_ids:
                goal_ids.append(text)
        for obligation_id in row.get("verified_bridge_obligation_ids", []) or []:
            text = str(obligation_id).strip()
            if text and text not in bridge_ids:
                bridge_ids.append(text)
    work_order_ids = list(dict.fromkeys(work_order_ids))
    target_ids = list(dict.fromkeys(target_ids))
    row = {
        "schema_version": 1,
        "question_id": str(question_id or ""),
        "learning_task": "theorem_reduction_closure_kernel_overlay",
        "input_summary": {
            "theorem_reduction_closure_audit_manifest": str(manifest_path),
            "kernel_verified_theorem_reduction_closure_work_order_ids": work_order_ids,
            "kernel_verified_theorem_reduction_closure_target_ids": target_ids,
            "kernel_verified_theorem_reduction_closure_goal_ids": goal_ids,
            "verified_bridge_obligation_ids": bridge_ids,
            "proof_evidence_status": str(payload.get("proof_evidence_status", "")),
            "local_lean_project": str(payload.get("local_lean_project", "")),
            "local_lean_timeout_seconds": payload.get("local_lean_timeout_seconds", ""),
        },
        "kernel_verified_theorem_reduction_closure_work_order_ids": work_order_ids,
        "kernel_verified_theorem_reduction_closure_target_ids": target_ids,
        "kernel_verified_theorem_reduction_closure_goal_ids": goal_ids,
        "verified_bridge_obligation_ids": bridge_ids,
        "target_behavior": (
            "Treat listed theorem-reduction closure work orders as already kernel-verified "
            "theorem-level reductions for routing memory. Do not treat them as full source "
            "theorem proof, and do not add their bridge ids as newly proved proof-bank subclaims."
        ),
        "acceptance_gate": (
            "Only checks with kernel_verified=true from the referenced "
            "theorem_reduction_closure_work_order_audit_manifest are exported."
        ),
        "boundary": (
            "Theorem-closure learning rows are runtime memory and routing guidance. "
            "They preserve the referenced local Lean/AXLE audit manifest as proof evidence "
            "for the closure reduction only; they do not prove upstream statistical semantics "
            "or the full paper/source theorem."
        ),
    }
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    learning_path.write_text(json.dumps(row, default=str) + "\n", encoding="utf-8")
    export_manifest = {
        "schema_version": 1,
        "artifact_kind": "TheoremReductionClosureRuntimeLearningExportManifest",
        "theorem_reduction_closure_audit_manifest": str(manifest_path),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_kernel_verified_theorem_reduction_closure_work_order_ids": len(work_order_ids),
        "kernel_verified_theorem_reduction_closure_work_order_ids": work_order_ids,
        "kernel_verified_theorem_reduction_closure_target_ids": target_ids,
        "kernel_verified_theorem_reduction_closure_goal_ids": goal_ids,
        "verified_bridge_obligation_ids": bridge_ids,
        "boundary": row["boundary"],
    }
    manifest_out = out_dir / "theorem_reduction_closure_runtime_learning_export_manifest.json"
    manifest_out.write_text(json.dumps(export_manifest, indent=2, default=str), encoding="utf-8")
    return {
        "row": row,
        "export_manifest": export_manifest,
        "runtime_learning_rows_jsonl": learning_path,
        "export_manifest_path": manifest_out,
    }

from __future__ import annotations

import json
import re
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
    declaration_names: list[str] = []
    artifact_paths: list[str] = []
    signature_excerpts: list[str] = []
    goal_ids: list[str] = []
    bridge_ids: list[str] = []
    for row in verified_checks:
        declaration = str(row.get("target_lean_declaration", "") or "").strip()
        artifact_path = str(row.get("lean_export_path", "") or "").strip()
        if not declaration and artifact_path:
            declaration = _lean_declaration_name_from_artifact(Path(artifact_path))
        if declaration and declaration not in declaration_names:
            declaration_names.append(declaration)
        if artifact_path and artifact_path not in artifact_paths:
            artifact_paths.append(artifact_path)
        signature_excerpt = _lean_declaration_signature_excerpt_from_artifact(
            Path(artifact_path),
            declaration=declaration,
        )
        if signature_excerpt and signature_excerpt not in signature_excerpts:
            signature_excerpts.append(signature_excerpt)
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
            "kernel_verified_theorem_reduction_closure_declarations": declaration_names,
            "verified_theorem_reduction_closure_artifact_paths": artifact_paths,
            "kernel_verified_theorem_reduction_closure_signature_excerpts": signature_excerpts,
            "kernel_verified_theorem_reduction_closure_goal_ids": goal_ids,
            "verified_bridge_obligation_ids": bridge_ids,
            "proof_evidence_status": str(payload.get("proof_evidence_status", "")),
            "local_lean_project": str(payload.get("local_lean_project", "")),
            "local_lean_timeout_seconds": payload.get("local_lean_timeout_seconds", ""),
        },
        "kernel_verified_theorem_reduction_closure_work_order_ids": work_order_ids,
        "kernel_verified_theorem_reduction_closure_target_ids": target_ids,
        "kernel_verified_theorem_reduction_closure_declarations": declaration_names,
        "verified_theorem_reduction_closure_artifact_paths": artifact_paths,
        "kernel_verified_theorem_reduction_closure_signature_excerpts": signature_excerpts,
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
        "kernel_verified_theorem_reduction_closure_declarations": declaration_names,
        "verified_theorem_reduction_closure_artifact_paths": artifact_paths,
        "kernel_verified_theorem_reduction_closure_signature_excerpts": signature_excerpts,
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


def _lean_declaration_name_from_artifact(path: Path) -> str:
    try:
        text = path.expanduser().read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(
        r"(?m)^\s*(?:noncomputable\s+)?(?:private\s+)?"
        r"(?:theorem|lemma|def|abbrev)\s+([A-Za-z_][A-Za-z0-9_'.]*)",
        text,
    )
    return match.group(1) if match else ""


def _lean_declaration_signature_excerpt_from_artifact(
    path: Path,
    *,
    declaration: str = "",
    max_lines: int = 40,
    max_chars: int = 2000,
) -> str:
    try:
        text = path.expanduser().read_text(encoding="utf-8")
    except OSError:
        return ""
    wanted = str(declaration or "").strip()
    lines = text.splitlines()
    start = -1
    declaration_pattern = (
        rf"^\s*(?:noncomputable\s+)?(?:private\s+)?(?:theorem|lemma|def|abbrev)\s+"
        rf"{re.escape(wanted)}\b"
        if wanted
        else r"^\s*(?:noncomputable\s+)?(?:private\s+)?(?:theorem|lemma|def|abbrev)\s+"
    )
    for index, line in enumerate(lines):
        if re.search(declaration_pattern, line):
            start = index
            break
    if start < 0:
        return ""
    excerpt_lines: list[str] = []
    for line in lines[start : start + max_lines]:
        if ":= by" in line:
            before, _sep, _after = line.partition(":= by")
            excerpt_lines.append(before.rstrip())
            break
        excerpt_lines.append(line.rstrip())
    return "\n".join(excerpt_lines).strip()[:max_chars]

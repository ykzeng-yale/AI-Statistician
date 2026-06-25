from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .theorem_reduction_closure_learning_export import (
    export_theorem_reduction_closure_learning_from_manifest,
)
from .theorem_reduction_closure_work_order_audit import (
    audit_theorem_reduction_closure_work_orders,
)


def resolve_theorem_reduction_queue_path(
    *,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
) -> Path:
    if queue_jsonl is not None:
        return queue_jsonl
    if runtime_dir is None:
        raise ValueError("runtime_dir or queue_jsonl is required")
    manifest_path = runtime_dir / "research_agent_runtime_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        artifacts = {}
    raw_path = str(artifacts.get("runtime_theorem_reduction_closure_work_orders_jsonl", "") or "")
    if not raw_path:
        raise ValueError(
            "runtime manifest does not list runtime_theorem_reduction_closure_work_orders_jsonl"
        )
    queue_path = Path(raw_path)
    if queue_path.is_absolute() or queue_path.exists():
        return queue_path
    candidates = [runtime_dir / queue_path]
    parts = queue_path.parts
    if len(parts) >= 2 and parts[0] == runtime_dir.parent.name:
        candidates.append(runtime_dir.parent.parent / queue_path)
    if parts and parts[0] == runtime_dir.name:
        candidates.append(runtime_dir.parent / queue_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def run_theorem_reduction_closure_proofengineer_bridge(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
    question_id: str = "",
    local_lean: bool = False,
    lean_project: Path | None = None,
    lean_timeout: int = 240,
) -> dict[str, object]:
    audit_dir = out_dir / "proofengineer_audit"
    learning_dir = out_dir / "runtime_learning_export"
    out_dir.mkdir(parents=True, exist_ok=True)

    queue_path = resolve_theorem_reduction_queue_path(
        runtime_dir=runtime_dir,
        queue_jsonl=queue_jsonl,
    )
    audit_payload = audit_theorem_reduction_closure_work_orders(
        queue_path,
        audit_dir,
        run_local_lean=local_lean,
        lean_project=lean_project,
        lean_timeout_seconds=lean_timeout,
    )
    audit_manifest_path = audit_dir / "theorem_reduction_closure_work_order_audit_manifest.json"
    learning_result = export_theorem_reduction_closure_learning_from_manifest(
        manifest_path=audit_manifest_path,
        out_dir=learning_dir,
        question_id=str(question_id or ""),
    )
    learning_export_manifest = learning_result["export_manifest"]
    if not isinstance(learning_export_manifest, Mapping):
        raise ValueError("theorem closure learning export manifest is not a mapping")
    n_verified = int(audit_payload.get("n_kernel_verified", 0) or 0)
    bridge_manifest = {
        "schema_version": 1,
        "artifact_kind": "TheoremReductionClosureProofEngineerBridgeManifest",
        "source_runtime_dir": str(runtime_dir or ""),
        "source_queue_jsonl": str(queue_path),
        "audit_manifest": str(audit_manifest_path),
        "runtime_learning_rows_jsonl": str(learning_result["runtime_learning_rows_jsonl"]),
        "runtime_learning_export_manifest": str(learning_result["export_manifest_path"]),
        "local_lean_requested": bool(local_lean),
        "n_work_orders": int(audit_payload.get("n_work_orders", 0) or 0),
        "n_kernel_verified": n_verified,
        "runtime_learning_ready": n_verified > 0,
        "proof_evidence_status": str(audit_payload.get("proof_evidence_status", "")),
        "n_kernel_verified_theorem_reduction_closure_work_order_ids": int(
            learning_export_manifest[
                "n_kernel_verified_theorem_reduction_closure_work_order_ids"
            ]
        ),
        "kernel_verified_theorem_reduction_closure_work_order_ids": list(
            learning_export_manifest[
                "kernel_verified_theorem_reduction_closure_work_order_ids"
            ]
        ),
        "kernel_verified_theorem_reduction_closure_target_ids": list(
            learning_export_manifest[
                "kernel_verified_theorem_reduction_closure_target_ids"
            ]
        ),
        "kernel_verified_theorem_reduction_closure_declarations": list(
            learning_export_manifest.get(
                "kernel_verified_theorem_reduction_closure_declarations", []
            )
        ),
        "verified_theorem_reduction_closure_artifact_paths": list(
            learning_export_manifest.get(
                "verified_theorem_reduction_closure_artifact_paths", []
            )
        ),
        "kernel_verified_theorem_reduction_closure_goal_ids": list(
            learning_export_manifest[
                "kernel_verified_theorem_reduction_closure_goal_ids"
            ]
        ),
        "verified_bridge_obligation_ids": list(
            learning_export_manifest["verified_bridge_obligation_ids"]
        ),
        "boundary": (
            "This bridge composes theorem-reduction closure work-order audit and "
            "runtime-learning export for the ProofEngineer loop. It is not proof "
            "evidence unless the referenced audit manifest has kernel_verified=true "
            "rows from local Lean/AXLE. Runtime learning rows are routing memory only."
        ),
    }
    bridge_manifest_path = out_dir / "theorem_reduction_closure_proofengineer_bridge_manifest.json"
    bridge_manifest_path.write_text(
        json.dumps(bridge_manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return bridge_manifest

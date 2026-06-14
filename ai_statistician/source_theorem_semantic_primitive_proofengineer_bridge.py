from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Mapping

from .proof_audit import audit_proof_bank
from .proof_bank import FORMAL_OBLIGATIONS
from .verifier import LocalLeanProofVerifier


ARTIFACT_KIND = "SourceTheoremSemanticPrimitiveProofEngineerBridgeManifest"
BOUNDARY = (
    "Source-theorem semantic primitive ProofEngineer bridge rows are proof-task "
    "routing and registered-obligation support checks. They are not proof evidence "
    "unless the referenced proof_audit_manifest contains kernel_verified=true rows. "
    "Even kernel-verified registered semantic bridges do not by themselves prove the "
    "full source theorem or unformalized upstream statistical semantics."
)

_PRIMITIVE_TO_REGISTERED_SUPPORT = {
    "probability_measure_semantics": (
        "prob_measure_univ",
    ),
    "exchangeability_semantics": (
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
    ),
    "exchangeability_to_uniform_rank_semantics": (
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
    ),
    "rank_uniformity_semantics": (
        "split_conformal_bad_rank_budget_from_uniform_rank_bound",
    ),
    "order_statistic_quantile_semantics": (
        "split_conformal_good_rank_set_inclusion_bridge",
    ),
}


def resolve_source_semantic_primitive_queue_path(
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
    raw_path = str(
        artifacts.get(
            "runtime_source_theorem_semantic_primitive_work_orders_jsonl",
            "",
        )
        or ""
    )
    if not raw_path:
        raise ValueError(
            "runtime manifest does not list "
            "runtime_source_theorem_semantic_primitive_work_orders_jsonl"
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


def run_source_theorem_semantic_primitive_proofengineer_bridge(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
    question_id: str = "",
    local_lean: bool = False,
    lean_project: Path | None = None,
    lean_timeout: int = 90,
    proof_audit_manifest: Path | None = None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = resolve_source_semantic_primitive_queue_path(
        runtime_dir=runtime_dir,
        queue_jsonl=queue_jsonl,
    )
    rows = _read_jsonl(queue_path)
    candidate_ids_by_work_order = {
        _work_order_id(row): _candidate_registered_obligation_ids(row)
        for row in rows
    }
    candidate_ids = sorted(
        {
            obligation_id
            for ids in candidate_ids_by_work_order.values()
            for obligation_id in ids
        }
    )

    audit_manifest_path = Path(proof_audit_manifest).expanduser().resolve() if proof_audit_manifest else None
    audit_payload: dict[str, Any] | None = None
    if audit_manifest_path is not None:
        audit_payload = json.loads(audit_manifest_path.read_text(encoding="utf-8"))
    elif local_lean and candidate_ids:
        audit_dir = out_dir / "proof_audit"
        verifier = LocalLeanProofVerifier(project_root=lean_project, timeout_s=lean_timeout)
        audit_payload = asyncio.run(
            audit_proof_bank(
                verifier,
                audit_dir,
                ids=candidate_ids,
                export_lean=True,
                export_attempt_log=True,
            )
        )
        audit_manifest_path = audit_dir / "proof_audit_manifest.json"

    verified_ids = list(_kernel_verified_ids_from_audit_payload(audit_payload))
    checks = [
        _bridge_check(
            row,
            candidate_ids_by_work_order.get(_work_order_id(row), ()),
            verified_ids,
            audit_manifest_path=audit_manifest_path,
        )
        for row in rows
    ]
    kernel_verified_candidate_ids = list(
        dict.fromkeys(
            str(value).strip()
            for row in checks
            for value in row.get("kernel_verified_registered_obligation_ids", []) or []
            if str(value).strip()
        )
    )
    n_kernel_verified_support = sum(
        len(row.get("kernel_verified_registered_obligation_ids", []) or [])
        for row in checks
    )
    learning_result = _export_runtime_learning_rows(
        checks=checks,
        out_dir=out_dir / "runtime_learning_export",
        question_id=question_id,
        proof_audit_manifest=audit_manifest_path,
    )
    checks_path = out_dir / "source_theorem_semantic_primitive_bridge_checks.jsonl"
    _write_jsonl(checks_path, checks)
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "source_runtime_dir": str(runtime_dir or ""),
        "source_queue_jsonl": str(queue_path),
        "source_proof_audit_manifest": str(audit_manifest_path or ""),
        "checks_jsonl": str(checks_path),
        "runtime_learning_rows_jsonl": str(learning_result["runtime_learning_rows_jsonl"]),
        "runtime_learning_export_manifest": str(learning_result["export_manifest_path"]),
        "local_lean_requested": bool(local_lean),
        "local_lean_project": str(lean_project or ""),
        "local_lean_timeout_seconds": int(lean_timeout),
        "n_work_orders": len(rows),
        "n_registered_candidate_obligations": len(candidate_ids),
        "registered_candidate_obligation_ids": candidate_ids,
        "n_kernel_verified_registered_candidate_obligations": len(
            kernel_verified_candidate_ids
        ),
        "kernel_verified_registered_candidate_obligation_ids": (
            kernel_verified_candidate_ids
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": (
            kernel_verified_candidate_ids
        ),
        "n_kernel_verified_work_order_support_links": n_kernel_verified_support,
        "runtime_learning_ready": bool(learning_result["n_learning_rows"]),
        "proof_evidence_status": (
            "KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT_PRESENT"
            if kernel_verified_candidate_ids
            else "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
        ),
        "checks": checks,
        "boundary": BOUNDARY,
    }
    manifest_path = out_dir / "source_theorem_semantic_primitive_proofengineer_bridge_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return manifest


def _bridge_check(
    row: Mapping[str, Any],
    candidate_ids: tuple[str, ...],
    verified_ids: tuple[str, ...],
    *,
    audit_manifest_path: Path | None,
) -> dict[str, Any]:
    kernel_verified_support = [row for row in candidate_ids if row in set(verified_ids)]
    status = (
        "KERNEL_VERIFIED_REGISTERED_SEMANTIC_BRIDGE_SUPPORT"
        if kernel_verified_support
        else "REGISTERED_SEMANTIC_BRIDGE_SUPPORT_NOT_KERNEL_VERIFIED"
        if candidate_ids
        else "FORMAL_BLOCKED_NO_REGISTERED_SEMANTIC_PRIMITIVE_SUPPORT"
    )
    source_theorem_target_provenance = dict(
        row.get("source_theorem_target_provenance", {}) or {}
    )
    semantic_alignment_constraints = [
        str(value).strip()
        for value in row.get("semantic_alignment_constraints", []) or []
        if str(value).strip()
    ]
    formal_environment_typeclass_blockers = [
        str(value).strip()
        for value in row.get("formal_environment_typeclass_blockers", []) or []
        if str(value).strip()
    ]
    proof_body_attempt_summaries = [
        str(value).strip()
        for value in row.get("proof_body_attempt_summaries", []) or []
        if str(value).strip()
    ]
    proof_body_goal_excerpt = [
        str(value).strip()
        for value in row.get("proof_body_goal_excerpt", []) or []
        if str(value).strip()
    ]
    return {
        "schema_version": 1,
        "work_order_id": _work_order_id(row),
        "question_id": str(row.get("question_id", "") or ""),
        "semantic_primitive_id": str(row.get("semantic_primitive_id", "") or ""),
        "semantic_primitive_gap": str(row.get("semantic_primitive_gap", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "target_theorem_goal_ids": list(row.get("target_theorem_goal_ids", []) or []),
        "source_theorem_target_known": bool(
            row.get("source_theorem_target_known", False)
            or source_theorem_target_provenance.get("source_theorem_target_known", False)
        ),
        "source_theorem_target_provenance": source_theorem_target_provenance,
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "failure_classification": str(row.get("failure_classification", "") or ""),
        "formal_environment_typeclass_blockers": formal_environment_typeclass_blockers,
        "proof_body_attempted": bool(row.get("proof_body_attempted", False)),
        "proof_body_attempt_success": bool(
            row.get("proof_body_attempt_success", False)
        ),
        "proof_body_attempt_summaries": proof_body_attempt_summaries,
        "proof_body_goal_excerpt": proof_body_goal_excerpt,
        "registered_candidate_obligation_ids": list(candidate_ids),
        "kernel_verified_registered_obligation_ids": kernel_verified_support,
        "registered_support_level": (
            "registered_partial_semantic_bridge"
            if candidate_ids
            else "missing_registered_semantic_primitive"
        ),
        "status": status,
        "kernel_verified": bool(kernel_verified_support),
        "proof_audit_manifest": str(audit_manifest_path or ""),
        "proof_evidence_status": (
            "KERNEL_VERIFIED_REGISTERED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
            if kernel_verified_support
            else "NO_KERNEL_VERIFIED_SOURCE_SEMANTIC_PRIMITIVE_SUPPORT"
        ),
        "boundary": BOUNDARY,
    }


def _candidate_registered_obligation_ids(row: Mapping[str, Any]) -> tuple[str, ...]:
    primitive_id = str(row.get("semantic_primitive_id", "") or "").strip()
    explicit = [
        str(value).strip()
        for value in row.get("candidate_registered_obligation_ids", []) or []
        if str(value).strip()
    ]
    candidates = list(explicit or _PRIMITIVE_TO_REGISTERED_SUPPORT.get(primitive_id, ()))
    if candidates:
        return tuple(
            dict.fromkeys(
                row
                for row in candidates
                if row in FORMAL_OBLIGATIONS
                and "source_theorem_semantic_primitive" in FORMAL_OBLIGATIONS[row].tags
            )
        )
    text = " ".join(
        [
            primitive_id,
            str(row.get("semantic_primitive_gap", "") or ""),
            str(row.get("semantic_primitive_gap_kind", "") or ""),
        ]
    ).lower()
    inferred: list[str] = []
    for obligation_id, obligation in FORMAL_OBLIGATIONS.items():
        if "source_theorem_semantic_primitive" not in obligation.tags:
            continue
        tag_text = " ".join(obligation.tags).lower()
        if ("probability" in text or "measure" in text) and (
            "probability_measure_semantics" in tag_text
            or ("probability" in tag_text and "measure" in tag_text)
        ):
            inferred.append(obligation_id)
        elif "order" in text and "order_statistic_quantile_rule" in tag_text:
            inferred.append(obligation_id)
        elif ("exchange" in text or "uniform" in text or "rank" in text) and (
            "rank_uniformity" in tag_text or "uniform_rank" in tag_text
        ):
            inferred.append(obligation_id)
    return tuple(dict.fromkeys(inferred))


def _kernel_verified_ids_from_audit_payload(
    audit_payload: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    if not audit_payload:
        return ()
    checks = audit_payload.get("checks", [])
    if not isinstance(checks, list):
        return ()
    return tuple(
        dict.fromkeys(
            str(row.get("obligation_id", "")).strip()
            for row in checks
            if isinstance(row, Mapping)
            and row.get("kernel_verified") is True
            and str(row.get("obligation_id", "")).strip()
        )
    )


def _export_runtime_learning_rows(
    *,
    checks: list[Mapping[str, Any]],
    out_dir: Path,
    question_id: str,
    proof_audit_manifest: Path | None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    verified_checks = [
        row
        for row in checks
        if row.get("kernel_verified") is True
        and row.get("kernel_verified_registered_obligation_ids")
    ]
    rows: list[dict[str, Any]] = []
    if verified_checks:
        kernel_ids = list(
            dict.fromkeys(
                str(value).strip()
                for row in verified_checks
                for value in row.get("kernel_verified_registered_obligation_ids", []) or []
                if str(value).strip()
            )
        )
        work_order_ids = [
            str(row.get("work_order_id", "") or "")
            for row in verified_checks
            if str(row.get("work_order_id", "") or "").strip()
        ]
        semantic_ids = [
            str(row.get("semantic_primitive_id", "") or "")
            for row in verified_checks
            if str(row.get("semantic_primitive_id", "") or "").strip()
        ]
        rows.append(
            {
                "schema_version": 1,
                "question_id": str(question_id or ""),
                "learning_task": "source_theorem_semantic_primitive_kernel_overlay",
                "input_summary": {
                    "source_theorem_semantic_primitive_work_order_ids": work_order_ids,
                    "semantic_primitive_ids": semantic_ids,
                    "kernel_verified_source_theorem_semantic_support_obligation_ids": (
                        kernel_ids
                    ),
                    "kernel_verified_source_theorem_semantic_primitive_ids": kernel_ids,
                    "kernel_verified_proof_obligation_ids": kernel_ids,
                    "proof_audit_manifest": str(proof_audit_manifest or ""),
                    "support_level": "registered_partial_semantic_bridge",
                    "semantic_primitive_checks": [
                        _learning_check_context(row) for row in verified_checks
                    ],
                },
                "source_theorem_semantic_primitive_work_order_ids": work_order_ids,
                "semantic_primitive_ids": semantic_ids,
                "kernel_verified_source_theorem_semantic_support_obligation_ids": kernel_ids,
                "kernel_verified_source_theorem_semantic_primitive_ids": kernel_ids,
                "kernel_verified_proof_obligation_ids": kernel_ids,
                "target_behavior": (
                    "Treat listed registered source-theorem semantic bridge obligations "
                    "as kernel-verified runtime memory. Do not treat them as full source "
                    "theorem proof or as proof of unformalized exchangeability/order-statistic "
                    "definitions unless separate exact primitive rows are verified."
                ),
                "acceptance_gate": (
                    "Only registered obligations with kernel_verified=true in the referenced "
                    "proof_audit_manifest are exported."
                ),
                "boundary": BOUNDARY,
            }
        )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(learning_path, rows)
    export_manifest = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremSemanticPrimitiveRuntimeLearningExportManifest",
        "proof_audit_manifest": str(proof_audit_manifest or ""),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_learning_rows": len(rows),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": (
            rows[0]["kernel_verified_source_theorem_semantic_support_obligation_ids"]
            if rows
            else []
        ),
        "kernel_verified_source_theorem_semantic_primitive_ids": (
            rows[0]["kernel_verified_source_theorem_semantic_primitive_ids"]
            if rows
            else []
        ),
        "source_theorem_semantic_primitive_work_order_ids": (
            rows[0]["source_theorem_semantic_primitive_work_order_ids"]
            if rows
            else []
        ),
        "boundary": BOUNDARY,
    }
    manifest_out = out_dir / "source_theorem_semantic_primitive_runtime_learning_export_manifest.json"
    manifest_out.write_text(
        json.dumps(export_manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return {
        "rows": rows,
        "n_learning_rows": len(rows),
        "runtime_learning_rows_jsonl": learning_path,
        "export_manifest_path": manifest_out,
        "export_manifest": export_manifest,
    }


def _learning_check_context(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "work_order_id": str(row.get("work_order_id", "") or ""),
        "semantic_primitive_id": str(row.get("semantic_primitive_id", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "target_theorem_goal_ids": list(row.get("target_theorem_goal_ids", []) or []),
        "source_theorem_target_known": bool(
            row.get("source_theorem_target_known", False)
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "formal_environment_typeclass_blockers": list(
            row.get("formal_environment_typeclass_blockers", []) or []
        ),
        "proof_body_attempted": bool(row.get("proof_body_attempted", False)),
        "proof_body_attempt_success": bool(
            row.get("proof_body_attempt_success", False)
        ),
        "proof_body_attempt_summaries": list(
            row.get("proof_body_attempt_summaries", []) or []
        ),
        "proof_body_goal_excerpt": list(row.get("proof_body_goal_excerpt", []) or []),
        "kernel_verified_registered_obligation_ids": list(
            row.get("kernel_verified_registered_obligation_ids", []) or []
        ),
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object row")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(dict(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _work_order_id(row: Mapping[str, Any]) -> str:
    return str(row.get("work_order_id", "") or "").strip()

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


HF_LEAN_SOURCE_REVALIDATION_PROMOTION_QUEUE_SCHEMA_VERSION = 1
ACCEPTED_STATUS = "ACCEPTED_LOCAL_KERNEL_VERIFIED_HF_SOURCE_ROWS"
PROOF_EVIDENCE_STATUS = "HF_LEAN_SOURCE_REVALIDATION_PROMOTION_QUEUE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Hugging Face Lean source promotion queue rows are review contracts, not "
    "proof evidence. Promotion is allowed only for validation rows that already "
    "record local Lean/AXLE kernel evidence and point to sample, reconstruction, "
    "verifier, and candidate-promotion artifacts."
)


@dataclass(frozen=True)
class HuggingFaceLeanSourceRevalidationPromotionRow:
    schema_version: int
    promotion_id: str
    validation_id: str
    task_id: str
    dataset_id: str
    source_id: str
    source_acceptance_status: str
    response_present: bool
    response_contract_ok: bool
    kernel_verified_rows: int
    proof_evidence_ready: int
    sample_manifest_path: str
    lean_reconstruction_dir: str
    verifier_attempt_log: str
    promotion_manifest_path: str
    verifier: str
    verification_strength: str
    promotion_status: str
    promotion_ready: bool
    owner_agent: str
    action_type: str
    priority: str
    required_gate: str
    required_fields: tuple[str, ...]
    command_plan: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_huggingface_lean_source_revalidation_promotion_queue(
    artifact_validation_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export promotion-review rows from validated HF Lean source artifacts."""

    errors: list[str] = []
    validation_manifest_path = (
        artifact_validation_dir
        / "hf_lean_source_revalidation_artifact_validation_manifest.json"
    )
    validation_payload = _read_json(validation_manifest_path, errors)
    validation_rows = [
        row for row in validation_payload.get("rows", []) if isinstance(row, dict)
    ]
    rows = [_promotion_row(row, artifact_validation_dir=artifact_validation_dir) for row in validation_rows]
    by_status = Counter(row.promotion_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": HF_LEAN_SOURCE_REVALIDATION_PROMOTION_QUEUE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_validation_dir": str(artifact_validation_dir),
        "artifact_validation_manifest": str(validation_manifest_path),
        "source_validation_all_ok": bool(validation_payload.get("all_ok", False)),
        "n_validation_rows": len(validation_rows),
        "n_promotion_rows": len(rows),
        "n_ready_for_promotion": sum(1 for row in rows if row.promotion_ready),
        "n_awaiting_worker_output": by_status.get("AWAITING_WORKER_OUTPUT_NO_PROMOTION", 0),
        "n_not_proof_evidence": by_status.get("RECORDED_OUTPUT_NOT_READY_FOR_PROMOTION", 0),
        "n_blocked": sum(1 for row in rows if row.promotion_status.startswith("BLOCKED_")),
        "n_kernel_verified_rows": sum(row.kernel_verified_rows for row in rows if row.promotion_ready),
        "n_proof_evidence_ready": sum(row.proof_evidence_ready for row in rows if row.promotion_ready),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": (
            not errors
            and bool(validation_payload.get("all_ok", False))
            and all(row.ok for row in rows)
        ),
        "errors": errors,
        "by_promotion_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "promotion_queue_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "promotion rows do not mutate proof banks, source registries, or claim ledgers",
            "awaiting worker outputs remain explicit no-op rows",
            "ready rows require a reviewer or downstream worker to attach evidence and rerun release gates",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "hf_lean_source_revalidation_promotion_queue_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        (out_dir / "hf_lean_source_revalidation_promotion_queue.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "hf_lean_source_revalidation_promotion_queue.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _promotion_row(
    row: dict[str, Any],
    *,
    artifact_validation_dir: Path,
) -> HuggingFaceLeanSourceRevalidationPromotionRow:
    errors: list[str] = []
    validation_id = str(row.get("validation_id", ""))
    task_id = str(row.get("task_id", ""))
    dataset_id = str(row.get("dataset_id", ""))
    source_id = str(row.get("source_id", ""))
    source_acceptance_status = str(row.get("acceptance_status", ""))
    response_present = bool(row.get("response_present", False))
    response_contract_ok = bool(row.get("response_contract_ok", False))
    kernel_verified_rows = _int(row.get("kernel_verified_rows"))
    proof_evidence_ready = _int(row.get("proof_evidence_ready"))
    evidence_paths = _existing_paths(
        (
            str(row.get("sample_manifest_path", "")),
            str(row.get("lean_reconstruction_dir", "")),
            str(row.get("verifier_attempt_log", "")),
            str(row.get("promotion_manifest_path", "")),
        ),
        base_dir=artifact_validation_dir,
    )
    if source_acceptance_status == "AWAITING_HF_LEAN_SOURCE_REVALIDATION_WORKER_OUTPUT":
        promotion_status = "AWAITING_WORKER_OUTPUT_NO_PROMOTION"
        action_type = "await_hf_lean_source_revalidation_worker_output"
        priority = "medium"
        required_gate = "worker output passes artifact-validation contract"
        promotion_ready = False
        ok = True
    elif source_acceptance_status == ACCEPTED_STATUS:
        if not response_present:
            errors.append("accepted validation row has no response")
        if not response_contract_ok:
            errors.append("accepted validation row contract is not ok")
        if kernel_verified_rows <= 0:
            errors.append("kernel_verified_rows must be positive")
        if proof_evidence_ready <= 0:
            errors.append("proof_evidence_ready must be positive")
        if len(evidence_paths) < 4:
            errors.append("sample, reconstruction, verifier, and promotion artifacts must exist")
        promotion_ready = not errors
        promotion_status = (
            "READY_FOR_HF_LEAN_SOURCE_REUSE_PROMOTION"
            if promotion_ready
            else "BLOCKED_HF_REVALIDATION_EVIDENCE_INCOMPLETE"
        )
        action_type = "review_and_promote_kernel_verified_hf_lean_rows"
        priority = "high"
        required_gate = (
            "review candidate promotion manifest, import only kernel-verified Lean rows, "
            "dedupe against proof bank/search memory, then rerun local Lean and system audit"
        )
        ok = promotion_ready
    elif response_present:
        promotion_status = "RECORDED_OUTPUT_NOT_READY_FOR_PROMOTION"
        action_type = "repair_or_extend_hf_revalidation_worker_output"
        priority = "medium"
        required_gate = "artifact validation records proof_evidence_ready > 0 with local Lean/AXLE strength"
        promotion_ready = False
        ok = True
    else:
        promotion_status = "BLOCKED_UNKNOWN_VALIDATION_STATUS"
        action_type = "inspect_hf_revalidation_validation_row"
        priority = "medium"
        required_gate = "validation row status is recognized"
        promotion_ready = False
        errors.append(f"unknown validation status: {source_acceptance_status}")
        ok = False
    required_fields = (
        "validation_id",
        "task_id",
        "dataset_id",
        "sample_manifest_path",
        "lean_reconstruction_dir",
        "verifier_attempt_log",
        "promotion_manifest_path",
        "kernel_verified_rows",
        "proof_evidence_ready",
    )
    command_plan = (
        "inspect validation row and candidate promotion manifest",
        "dedupe by dataset/source/proof hashes before adding reusable memory",
        "import only reconstructed Lean artifacts with local Lean/AXLE kernel evidence",
        "rerun proof-bank/proof-search/system audit gates after any promotion",
    )
    return HuggingFaceLeanSourceRevalidationPromotionRow(
        schema_version=HF_LEAN_SOURCE_REVALIDATION_PROMOTION_QUEUE_SCHEMA_VERSION,
        promotion_id="hf_lean_source_revalidation_promotion:" + stable_hash(
            [validation_id, task_id, dataset_id]
        )[:16],
        validation_id=validation_id,
        task_id=task_id,
        dataset_id=dataset_id,
        source_id=source_id,
        source_acceptance_status=source_acceptance_status,
        response_present=response_present,
        response_contract_ok=response_contract_ok,
        kernel_verified_rows=kernel_verified_rows,
        proof_evidence_ready=proof_evidence_ready,
        sample_manifest_path=str(row.get("sample_manifest_path", "")),
        lean_reconstruction_dir=str(row.get("lean_reconstruction_dir", "")),
        verifier_attempt_log=str(row.get("verifier_attempt_log", "")),
        promotion_manifest_path=str(row.get("promotion_manifest_path", "")),
        verifier=str(row.get("verifier", "")),
        verification_strength=str(row.get("verification_strength", "")),
        promotion_status=promotion_status,
        promotion_ready=promotion_ready,
        owner_agent="hf_lean_source_reuse_promotion_reviewer",
        action_type=action_type,
        priority=priority,
        required_gate=required_gate,
        required_fields=required_fields,
        command_plan=command_plan,
        evidence_paths=evidence_paths,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=ok,
        errors=tuple(errors),
    )


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse JSON {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _existing_paths(paths: tuple[str, ...], *, base_dir: Path) -> tuple[str, ...]:
    existing: list[str] = []
    for value in paths:
        if not value:
            continue
        path = Path(value)
        if path.exists() or (not path.is_absolute() and (base_dir / path).exists()):
            existing.append(value)
    return tuple(existing)


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except Exception:
        return 0


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Hugging Face Lean Source Revalidation Promotion Queue",
        "",
        f"- Created at: `{payload.get('created_at')}`",
        f"- Validation rows: `{payload.get('n_validation_rows')}`",
        f"- Promotion rows: `{payload.get('n_promotion_rows')}`",
        f"- Ready: `{payload.get('n_ready_for_promotion')}`",
        f"- Awaiting: `{payload.get('n_awaiting_worker_output')}`",
        f"- Proof evidence ready: `{payload.get('n_proof_evidence_ready')}`",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Rows",
        "",
        "| status | dataset | kernel rows | proof ready |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in payload.get("rows", []):
        if isinstance(row, dict):
            lines.append(
                "| {status} | {dataset} | {kernel} | {proof} |".format(
                    status=row.get("promotion_status", ""),
                    dataset=row.get("dataset_id", ""),
                    kernel=row.get("kernel_verified_rows", 0),
                    proof=row.get("proof_evidence_ready", 0),
                )
            )
    errors = payload.get("errors", [])
    if errors:
        lines.extend(["", "## Errors", ""])
        for error in errors:
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)

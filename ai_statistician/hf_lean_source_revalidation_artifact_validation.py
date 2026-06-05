from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


HF_LEAN_SOURCE_REVALIDATION_ARTIFACT_VALIDATION_SCHEMA_VERSION = 1
AWAITING_STATUS = "AWAITING_HF_LEAN_SOURCE_REVALIDATION_WORKER_OUTPUT"
PROOF_EVIDENCE_STATUS = "HF_LEAN_SOURCE_REVALIDATION_ARTIFACT_VALIDATION_NOT_PROOF_EVIDENCE"
KERNEL_EVIDENCE_STATUS = "HF_LEAN_SOURCE_REVALIDATION_LOCAL_KERNEL_EVIDENCE_RECORDED"
PROOF_EVIDENCE_BOUNDARY = (
    "Hugging Face Lean source revalidation artifact validation rows are evidence "
    "audits for worker outputs. A row is proof evidence only when a matching "
    "worker output provides local Lean/AXLE verifier artifacts, kernel-verified "
    "row counts, and a candidate promotion manifest for reconstructed Lean rows."
)


@dataclass(frozen=True)
class HuggingFaceLeanSourceRevalidationArtifactValidationRow:
    schema_version: int
    validation_id: str
    task_id: str
    dataset_id: str
    source_id: str
    task_status: str
    response_present: bool
    response_contract_ok: bool
    sample_manifest_path: str
    lean_reconstruction_dir: str
    verifier_attempt_log: str
    promotion_manifest_path: str
    sampled_rows: int
    reconstructed_artifacts: int
    verifier: str
    verification_strength: str
    kernel_verified_rows: int
    proof_evidence_ready: int
    artifact_paths_exist: bool
    promotion_ready: bool
    acceptance_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_huggingface_lean_source_revalidation_artifact_validation(
    task_dir: Path,
    out_dir: Path | None = None,
    *,
    response_jsonl: Path | None = None,
) -> dict[str, object]:
    """Validate worker outputs for Hugging Face Lean source revalidation tasks.

    Missing worker output is non-failing and remains awaiting. Present responses
    are accepted as proof evidence only if they include matching task identity,
    local Lean/AXLE verifier evidence, and promotion artifacts.
    """

    errors: list[str] = []
    task_manifest_path = task_dir / "hf_lean_source_revalidation_tasks_manifest.json"
    task_jsonl_path = task_dir / "hf_lean_source_revalidation_tasks.jsonl"
    task_manifest = _read_json(task_manifest_path, errors)
    task_rows = _read_jsonl(task_jsonl_path, errors)
    if not task_rows and isinstance(task_manifest.get("rows"), list):
        task_rows = [row for row in task_manifest.get("rows", []) if isinstance(row, dict)]
    response_jsonl_path = (
        response_jsonl
        if response_jsonl is not None
        else task_dir / "hf_lean_source_revalidation_worker_outputs.jsonl"
    )
    response_rows, response_file_exists = _read_response_jsonl(response_jsonl_path, errors)
    responses = _responses_by_task(response_rows, errors)
    rows = [
        _validation_row(task, response=responses.get(str(task.get("task_id", ""))))
        for task in task_rows
    ]
    by_status = Counter(row.acceptance_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": HF_LEAN_SOURCE_REVALIDATION_ARTIFACT_VALIDATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task_dir": str(task_dir),
        "task_manifest": str(task_manifest_path),
        "task_jsonl": str(task_jsonl_path),
        "response_jsonl": str(response_jsonl_path),
        "response_jsonl_exists": response_file_exists,
        "n_tasks": len(task_rows),
        "n_responses": len(response_rows),
        "n_validation_rows": len(rows),
        "n_response_present": sum(1 for row in rows if row.response_present),
        "n_awaiting_worker_output": sum(
            1 for row in rows if row.acceptance_status == AWAITING_STATUS
        ),
        "n_contract_ok": sum(1 for row in rows if row.response_contract_ok),
        "n_artifact_paths_exist": sum(1 for row in rows if row.artifact_paths_exist),
        "n_kernel_verified_rows": sum(row.kernel_verified_rows for row in rows),
        "n_proof_evidence_ready": sum(row.proof_evidence_ready for row in rows),
        "n_promotion_ready": sum(1 for row in rows if row.promotion_ready),
        "n_rejected": sum(1 for row in rows if row.acceptance_status.startswith("REJECTED_")),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_acceptance_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "validation_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS
        if not any(row.promotion_ready for row in rows)
        else KERNEL_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "awaiting rows are not proof evidence",
            "matching task ids and dataset ids are required for every worker output",
            "kernel_verified_rows is accepted only with local Lean/AXLE verifier strength",
            "promotion manifests are candidate evidence until downstream proof-bank promotion accepts them",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "hf_lean_source_revalidation_artifact_validation_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        (out_dir / "hf_lean_source_revalidation_artifact_validation.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "hf_lean_source_revalidation_artifact_validation.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _validation_row(
    task: dict[str, Any],
    *,
    response: dict[str, Any] | None,
) -> HuggingFaceLeanSourceRevalidationArtifactValidationRow:
    task_id = str(task.get("task_id", ""))
    dataset_id = str(task.get("dataset_id", ""))
    source_id = str(task.get("source_id", ""))
    task_status = str(task.get("task_status", ""))
    if response is None:
        return HuggingFaceLeanSourceRevalidationArtifactValidationRow(
            schema_version=HF_LEAN_SOURCE_REVALIDATION_ARTIFACT_VALIDATION_SCHEMA_VERSION,
            validation_id=_validation_id(task_id, dataset_id, "awaiting"),
            task_id=task_id,
            dataset_id=dataset_id,
            source_id=source_id,
            task_status=task_status,
            response_present=False,
            response_contract_ok=False,
            sample_manifest_path=str(task.get("sample_manifest_path", "")),
            lean_reconstruction_dir=str(task.get("lean_reconstruction_dir", "")),
            verifier_attempt_log=str(task.get("verifier_attempt_log", "")),
            promotion_manifest_path=str(task.get("promotion_manifest_path", "")),
            sampled_rows=0,
            reconstructed_artifacts=0,
            verifier="",
            verification_strength="",
            kernel_verified_rows=0,
            proof_evidence_ready=0,
            artifact_paths_exist=False,
            promotion_ready=False,
            acceptance_status=AWAITING_STATUS,
            proof_evidence_status=PROOF_EVIDENCE_STATUS,
            proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
            ok=True,
            errors=(),
        )

    errors: list[str] = []
    _require_matching(response, task, "task_id", errors)
    _require_matching(response, task, "dataset_id", errors)
    sample_manifest_path = str(
        response.get("sample_manifest_path") or task.get("sample_manifest_path", "")
    )
    lean_reconstruction_dir = str(
        response.get("lean_reconstruction_dir") or task.get("lean_reconstruction_dir", "")
    )
    verifier_attempt_log = str(
        response.get("verifier_attempt_log") or task.get("verifier_attempt_log", "")
    )
    promotion_manifest_path = str(
        response.get("promotion_manifest_path") or task.get("promotion_manifest_path", "")
    )
    sampled_rows = _int(response.get("sampled_rows"))
    reconstructed_artifacts = _int(response.get("reconstructed_artifacts"))
    kernel_verified_rows = _int(response.get("kernel_verified_rows"))
    proof_evidence_ready = _int(response.get("proof_evidence_ready"))
    verifier = str(response.get("verifier", ""))
    verification_strength = str(response.get("verification_strength", ""))
    if sampled_rows < 0:
        errors.append("sampled_rows must be nonnegative")
    if reconstructed_artifacts < 0:
        errors.append("reconstructed_artifacts must be nonnegative")
    if kernel_verified_rows < 0:
        errors.append("kernel_verified_rows must be nonnegative")
    if proof_evidence_ready < 0:
        errors.append("proof_evidence_ready must be nonnegative")
    if kernel_verified_rows > reconstructed_artifacts:
        errors.append("kernel_verified_rows exceeds reconstructed_artifacts")
    if proof_evidence_ready > kernel_verified_rows:
        errors.append("proof_evidence_ready exceeds kernel_verified_rows")
    if proof_evidence_ready and not _local_kernel_strength(verifier, verification_strength):
        errors.append("proof evidence requires local Lean/AXLE verifier strength")
    artifact_paths_exist = all(
        Path(path).exists()
        for path in (
            sample_manifest_path,
            lean_reconstruction_dir,
            verifier_attempt_log,
            promotion_manifest_path,
        )
        if path
    )
    if proof_evidence_ready and not artifact_paths_exist:
        errors.append("proof evidence requires sample, reconstruction, verifier, and promotion artifacts")
    response_contract_ok = not errors
    promotion_ready = response_contract_ok and proof_evidence_ready > 0
    if not response_contract_ok:
        acceptance_status = "REJECTED_INVALID_HF_REVALIDATION_WORKER_OUTPUT"
        proof_status = PROOF_EVIDENCE_STATUS
    elif promotion_ready:
        acceptance_status = "ACCEPTED_LOCAL_KERNEL_VERIFIED_HF_SOURCE_ROWS"
        proof_status = KERNEL_EVIDENCE_STATUS
    else:
        acceptance_status = "RECORDED_REVALIDATION_OUTPUT_NOT_PROOF_EVIDENCE"
        proof_status = PROOF_EVIDENCE_STATUS
    return HuggingFaceLeanSourceRevalidationArtifactValidationRow(
        schema_version=HF_LEAN_SOURCE_REVALIDATION_ARTIFACT_VALIDATION_SCHEMA_VERSION,
        validation_id=_validation_id(task_id, dataset_id, response.get("response_id", "")),
        task_id=task_id,
        dataset_id=dataset_id,
        source_id=source_id,
        task_status=task_status,
        response_present=True,
        response_contract_ok=response_contract_ok,
        sample_manifest_path=sample_manifest_path,
        lean_reconstruction_dir=lean_reconstruction_dir,
        verifier_attempt_log=verifier_attempt_log,
        promotion_manifest_path=promotion_manifest_path,
        sampled_rows=sampled_rows,
        reconstructed_artifacts=reconstructed_artifacts,
        verifier=verifier,
        verification_strength=verification_strength,
        kernel_verified_rows=kernel_verified_rows,
        proof_evidence_ready=proof_evidence_ready,
        artifact_paths_exist=artifact_paths_exist,
        promotion_ready=promotion_ready,
        acceptance_status=acceptance_status,
        proof_evidence_status=proof_status,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=True,
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


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse {path}:{line_no}: {type(exc).__name__}: {exc}")
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            errors.append(f"JSONL row is not an object: {path}:{line_no}")
    return rows


def _read_response_jsonl(path: Path, errors: list[str]) -> tuple[list[dict[str, Any]], bool]:
    if not path.exists():
        return [], False
    return _read_jsonl(path, errors), True


def _responses_by_task(rows: list[dict[str, Any]], errors: list[str]) -> dict[str, dict[str, Any]]:
    responses: dict[str, dict[str, Any]] = {}
    for row in rows:
        task_id = str(row.get("task_id", ""))
        if not task_id:
            errors.append("worker output missing task_id")
            continue
        if task_id in responses:
            errors.append(f"duplicate worker output for task_id {task_id}")
            continue
        responses[task_id] = row
    return responses


def _require_matching(response: dict[str, Any], task: dict[str, Any], field: str, errors: list[str]) -> None:
    if str(response.get(field, "")) != str(task.get(field, "")):
        errors.append(f"{field} does not match task")


def _local_kernel_strength(verifier: str, strength: str) -> bool:
    text = f"{verifier} {strength}".lower()
    return ("lean" in text or "axle" in text) and "kernel" in text


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except Exception:
        return 0


def _validation_id(task_id: str, dataset_id: str, response_id: object) -> str:
    return "hf_lean_source_revalidation_artifact_validation:" + stable_hash(
        [task_id, dataset_id, str(response_id)]
    )[:16]


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Hugging Face Lean Source Revalidation Artifact Validation",
        "",
        f"- Created at: `{payload.get('created_at')}`",
        f"- Tasks: `{payload.get('n_tasks')}`",
        f"- Responses: `{payload.get('n_responses')}`",
        f"- Awaiting worker output: `{payload.get('n_awaiting_worker_output')}`",
        f"- Contract OK: `{payload.get('n_contract_ok')}`",
        f"- Proof evidence ready: `{payload.get('n_proof_evidence_ready')}`",
        f"- Kernel-verified rows: `{payload.get('n_kernel_verified_rows')}`",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Rows",
        "",
        "| status | dataset | response | kernel rows | proof ready |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {status} | {dataset} | {response} | {kernel} | {proof} |".format(
                status=row.get("acceptance_status", ""),
                dataset=row.get("dataset_id", ""),
                response=row.get("response_present", False),
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

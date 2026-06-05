from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .stat_claim_certificate_witness_materializer import (
    PROOF_EVIDENCE_STATUS as DRAFT_PROOF_EVIDENCE_STATUS,
)


STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_APPLY_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_APPLY_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Witness response apply copies accepted worker response fields into draft "
    "artifacts for later validation. It does not run the certificate checker, "
    "does not verify Lean code, and does not prove the source statistical claim."
)


@dataclass(frozen=True)
class StatClaimCertificateWitnessResponseApplyRow:
    schema_version: int
    apply_id: str
    draft_id: str
    task_id: str
    target_id: str
    source_claim_id: str
    question_id: str
    certificate_family: str
    original_draft_path: str
    applied_draft_path: str
    response_validation_id: str
    prompt_packet_id: str
    response_present: bool
    accepted_for_draft_update: bool
    worker_response_applied: bool
    apply_status: str
    draft_status: str
    required_fields: tuple[str, ...]
    updated_fields: tuple[str, ...]
    missing_response_fields: tuple[str, ...]
    source_evidence_fields: tuple[str, ...]
    open_semantic_gaps: tuple[str, ...]
    required_next_step: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def apply_stat_claim_certificate_witness_responses(
    response_validation_dir: Path,
    out_dir: Path | None = None,
    *,
    materializer_dir: Path | None = None,
) -> dict[str, object]:
    """Apply accepted worker responses to copied witness draft files.

    This stage is intentionally non-mutating with respect to the original
    materializer directory. It writes a new materializer-like draft directory
    that downstream draft validation can inspect.
    """

    errors: list[str] = []
    validation_manifest_path = (
        response_validation_dir
        / "stat_claim_certificate_witness_response_validation_manifest.json"
    )
    validation_jsonl_path = (
        response_validation_dir / "stat_claim_certificate_witness_response_validation.jsonl"
    )
    validation_manifest = _read_json(validation_manifest_path, errors)
    validation_rows = _read_jsonl(validation_jsonl_path, errors)
    prompt_manifest = _read_json(
        _resolve_path(
            str(validation_manifest.get("prompt_packets_manifest", "")),
            response_validation_dir,
        ),
        errors,
    )
    resolved_materializer_dir = (
        materializer_dir
        if materializer_dir is not None
        else _resolve_path(str(prompt_manifest.get("materializer_dir", "")), response_validation_dir)
    )
    draft_jsonl_path = resolved_materializer_dir / "stat_claim_certificate_witness_drafts.jsonl"
    draft_rows = _read_jsonl(draft_jsonl_path, errors)
    response_jsonl_path = _resolve_path(
        str(validation_manifest.get("worker_output_jsonl", "")),
        response_validation_dir,
    )
    response_rows = _read_jsonl(response_jsonl_path, errors, missing_ok=True)
    response_by_prompt = {
        str(row.get("prompt_packet_id", "")): row
        for row in response_rows
        if isinstance(row, dict) and str(row.get("prompt_packet_id", ""))
    }
    validation_by_draft = {
        str(row.get("draft_id", "")): row
        for row in validation_rows
        if isinstance(row, dict) and str(row.get("draft_id", ""))
    }
    output_root = out_dir if out_dir is not None else response_validation_dir
    applied_draft_dir = output_root / "witness_drafts"
    applied_draft_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        _apply_row(
            draft_row,
            validation_row=validation_by_draft.get(str(draft_row.get("draft_id", "")), {}),
            response_by_prompt=response_by_prompt,
            applied_draft_dir=applied_draft_dir,
        )
        for draft_row in draft_rows
    ]
    by_family = Counter(row.certificate_family for row in rows if row.certificate_family)
    by_status = Counter(row.apply_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_APPLY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "response_validation_dir": str(response_validation_dir),
        "response_validation_manifest": str(validation_manifest_path),
        "response_validation_jsonl": str(validation_jsonl_path),
        "response_validation_all_ok": bool(validation_manifest.get("all_ok", False)),
        "response_validation_proof_evidence_status": str(
            validation_manifest.get("proof_evidence_status", "")
        ),
        "materializer_dir": str(resolved_materializer_dir),
        "materializer_drafts_jsonl": str(draft_jsonl_path),
        "worker_output_jsonl": str(response_jsonl_path),
        "n_drafts": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_worker_response_applied": sum(1 for row in rows if row.worker_response_applied),
        "n_accepted_for_draft_update": sum(1 for row in rows if row.accepted_for_draft_update),
        "n_awaiting_worker_output": sum(
            1 for row in rows if row.apply_status == "UNCHANGED_AWAITING_WORKER_OUTPUT"
        ),
        "n_rejected_response_rows": sum(
            1 for row in rows if row.apply_status == "UNCHANGED_REJECTED_RESPONSE"
        ),
        "n_missing_validation_rows": sum(
            1 for row in rows if row.apply_status == "UNCHANGED_MISSING_VALIDATION_ROW"
        ),
        "n_missing_response_rows": sum(
            1 for row in rows if row.apply_status == "UNCHANGED_MISSING_ACCEPTED_RESPONSE"
        ),
        "n_missing_response_fields": sum(1 for row in rows if row.missing_response_fields),
        "all_ok": (
            not errors
            and bool(validation_manifest.get("all_ok", False))
            and all(row.ok for row in rows)
        ),
        "errors": errors,
        "by_family": dict(sorted(by_family.items())),
        "by_status": dict(sorted(by_status.items())),
        "drafts": [asdict(row) for row in rows],
        "apply_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "applied witness drafts remain untrusted until draft validation passes",
            "draft validation still precedes checker execution",
            "checker execution proves only the encoded certificate contract",
            "source theorem promotion still requires semantic review and Lean/AXLE proof evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        applied_draft_dir.mkdir(parents=True, exist_ok=True)
        for row in rows:
            Path(row.applied_draft_path).parent.mkdir(parents=True, exist_ok=True)
        (out_dir / "stat_claim_certificate_witness_response_apply_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_response_apply.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_drafts.jsonl").write_text(
            "\n".join(
                json.dumps(_draft_row_for_validator(row), sort_keys=True) for row in rows
            )
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_response_apply.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _apply_row(
    draft_row: dict[str, Any],
    *,
    validation_row: dict[str, Any],
    response_by_prompt: dict[str, dict[str, Any]],
    applied_draft_dir: Path,
) -> StatClaimCertificateWitnessResponseApplyRow:
    errors: list[str] = []
    draft_id = str(draft_row.get("draft_id", ""))
    task_id = str(draft_row.get("task_id", ""))
    target_id = str(draft_row.get("target_id", ""))
    source_claim_id = str(draft_row.get("source_claim_id", ""))
    question_id = str(draft_row.get("question_id", ""))
    certificate_family = str(draft_row.get("certificate_family", ""))
    required_fields = _str_tuple(draft_row.get("required_fields", ()))
    original_draft_path = Path(str(draft_row.get("draft_path", "")))
    safe_id = stable_hash([draft_id, task_id, target_id])[:16]
    applied_draft_path = applied_draft_dir / f"{safe_id}.json"
    original_payload = _read_json(original_draft_path, errors)
    response_validation_id = str(validation_row.get("response_validation_id", ""))
    prompt_packet_id = str(validation_row.get("prompt_packet_id", ""))
    response_present = bool(validation_row.get("response_present", False))
    accepted = bool(validation_row.get("accepted_for_draft_update", False))
    response = response_by_prompt.get(prompt_packet_id, {}) if prompt_packet_id else {}
    if not validation_row:
        status = "UNCHANGED_MISSING_VALIDATION_ROW"
        next_step = "run witness response validation for this draft"
        applied = False
    elif not accepted:
        status = (
            "UNCHANGED_AWAITING_WORKER_OUTPUT"
            if str(validation_row.get("validation_status", "")) == "AWAITING_WORKER_OUTPUT"
            else "UNCHANGED_REJECTED_RESPONSE"
        )
        next_step = str(validation_row.get("required_next_step", "")) or "repair or await worker response"
        applied = False
    elif not response:
        status = "UNCHANGED_MISSING_ACCEPTED_RESPONSE"
        next_step = "restore the worker response JSONL row before applying accepted fields"
        applied = False
        errors.append("accepted validation row has no matching worker response")
    else:
        status = "APPLIED_ACCEPTED_RESPONSE"
        next_step = "run witness draft validation, then execute the certificate checker"
        applied = True
    updated_payload = _updated_payload(
        original_payload,
        draft_row,
        response=response if applied else {},
        required_fields=required_fields,
    )
    if applied_draft_path:
        applied_draft_path.write_text(
            json.dumps(updated_payload, indent=2, default=str),
            encoding="utf-8",
        )
    response_fields = response.get("fields", {}) if isinstance(response, dict) else {}
    if not isinstance(response_fields, dict):
        response_fields = {}
    source_field_evidence = (
        response.get("source_field_evidence", {}) if isinstance(response, dict) else {}
    )
    if not isinstance(source_field_evidence, dict):
        source_field_evidence = {}
    missing_response_fields = tuple(
        field
        for field in required_fields
        if applied and (field not in response_fields or _is_blank(response_fields.get(field)))
    )
    updated_fields = tuple(
        field
        for field in required_fields
        if applied and field in response_fields and not _is_blank(response_fields.get(field))
    )
    source_evidence_fields = tuple(
        field
        for field in updated_fields
        if _has_source_evidence(source_field_evidence.get(field))
    )
    open_semantic_gaps = _str_tuple(response.get("open_semantic_gaps", ())) if applied else ()
    if missing_response_fields:
        errors.append("accepted response is missing required fields")
    draft_status = str(updated_payload.get("draft_status", ""))
    return StatClaimCertificateWitnessResponseApplyRow(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_APPLY_SCHEMA_VERSION,
        apply_id="stat_claim_certificate_witness_response_apply:"
        + stable_hash([draft_id, prompt_packet_id, status])[:16],
        draft_id=draft_id,
        task_id=task_id,
        target_id=target_id,
        source_claim_id=source_claim_id,
        question_id=question_id,
        certificate_family=certificate_family,
        original_draft_path=str(original_draft_path),
        applied_draft_path=str(applied_draft_path),
        response_validation_id=response_validation_id,
        prompt_packet_id=prompt_packet_id,
        response_present=response_present,
        accepted_for_draft_update=accepted,
        worker_response_applied=applied,
        apply_status=status,
        draft_status=draft_status,
        required_fields=required_fields,
        updated_fields=updated_fields,
        missing_response_fields=missing_response_fields,
        source_evidence_fields=source_evidence_fields,
        open_semantic_gaps=open_semantic_gaps,
        required_next_step=next_step,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _updated_payload(
    original_payload: dict[str, Any],
    draft_row: dict[str, Any],
    *,
    response: dict[str, Any],
    required_fields: tuple[str, ...],
) -> dict[str, object]:
    payload = dict(original_payload)
    payload.setdefault("schema_version", draft_row.get("schema_version", 1))
    payload["draft_id"] = str(draft_row.get("draft_id", payload.get("draft_id", "")))
    payload["task_id"] = str(draft_row.get("task_id", payload.get("task_id", "")))
    payload["target_id"] = str(draft_row.get("target_id", payload.get("target_id", "")))
    payload["source_claim_id"] = str(
        draft_row.get("source_claim_id", payload.get("source_claim_id", ""))
    )
    payload["question_id"] = str(draft_row.get("question_id", payload.get("question_id", "")))
    payload["certificate_family"] = str(
        draft_row.get("certificate_family", payload.get("certificate_family", ""))
    )
    if response:
        fields = response.get("fields", {})
        source_field_evidence = response.get("source_field_evidence", {})
        payload["fields"] = {field: fields.get(field) for field in required_fields}
        payload["source_field_evidence"] = {
            field: source_field_evidence.get(field, []) for field in required_fields
        }
        payload["open_semantic_gaps"] = list(response.get("open_semantic_gaps", []) or [])
        payload["semantic_linkage_review"] = str(
            response.get("semantic_linkage_review", "")
        )
        payload["draft_status"] = "WITNESS_DRAFT_FILLED"
        payload["required_next_step"] = (
            "run witness draft validation, then execute the certificate checker"
        )
    else:
        payload.setdefault("fields", {field: None for field in required_fields})
        payload.setdefault("source_field_evidence", {field: [] for field in required_fields})
        payload.setdefault("draft_status", "WITNESS_DRAFT_UNFILLED")
    payload["checker_validation"] = {
        "attempted": False,
        "passed": False,
        "transcript_path": "",
    }
    payload["source_claim_proved"] = False
    payload["proof_evidence_status"] = DRAFT_PROOF_EVIDENCE_STATUS
    return payload


def _draft_row_for_validator(row: StatClaimCertificateWitnessResponseApplyRow) -> dict[str, object]:
    return {
        "schema_version": row.schema_version,
        "draft_id": row.draft_id,
        "task_id": row.task_id,
        "target_id": row.target_id,
        "source_claim_id": row.source_claim_id,
        "question_id": row.question_id,
        "certificate_family": row.certificate_family,
        "required_fields": list(row.required_fields),
        "draft_path": row.applied_draft_path,
    }


def _resolve_path(path_value: str, base_dir: Path) -> Path:
    if not path_value:
        return Path()
    path = Path(path_value)
    if path.is_absolute() or path.exists():
        return path
    candidate = base_dir / path
    if candidate.exists():
        return candidate
    return path


def _read_json(
    path: Path,
    errors: list[str],
    *,
    missing_ok: bool = False,
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if not missing_ok:
            errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(
    path: Path,
    errors: list[str],
    *,
    missing_ok: bool = False,
) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        if not missing_ok:
            errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"failed to parse JSONL {path}:{idx}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"JSONL row is not an object: {path}:{idx}")
    return rows


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if value == "":
        return True
    if value == [] or value == {}:
        return True
    return False


def _has_source_evidence(value: object) -> bool:
    if isinstance(value, list):
        return any(not _is_blank(item) for item in value)
    return not _is_blank(value)


def _str_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        return (str(value),) if str(value) else ()
    return tuple(str(item) for item in value or () if str(item))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Statistical Claim Certificate Witness Response Apply",
        "",
        f"- Response validation: `{payload.get('response_validation_manifest')}`",
        f"- Drafts: `{payload.get('n_ok')}/{payload.get('n_drafts')}`",
        f"- Worker responses applied: `{payload.get('n_worker_response_applied')}`",
        f"- Awaiting worker output: `{payload.get('n_awaiting_worker_output')}`",
        f"- Rejected response rows: `{payload.get('n_rejected_response_rows')}`",
        f"- Proof status: `{payload.get('proof_evidence_status')}`",
        "",
        "## Status",
        "",
    ]
    by_status = payload.get("by_status", {})
    if isinstance(by_status, dict) and by_status:
        for status, count in sorted(by_status.items()):
            lines.append(f"- `{status}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

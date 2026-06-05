from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


STAT_CLAIM_CERTIFICATE_WITNESS_VALIDATOR_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "STAT_CLAIM_CERTIFICATE_WITNESS_VALIDATION_NOT_PROOF_EVIDENCE"
ALLOWED_DRAFT_PROOF_STATUS = "STAT_CLAIM_CERTIFICATE_WITNESS_DRAFT_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Witness validation is a pre-checker quality gate. It can reject incomplete "
    "or overclaimed witness drafts, but it does not validate the Lean checker "
    "contract and does not prove the source statistical claim."
)


@dataclass(frozen=True)
class StatClaimCertificateWitnessValidationRow:
    schema_version: int
    validation_id: str
    draft_id: str
    task_id: str
    target_id: str
    source_claim_id: str
    question_id: str
    certificate_family: str
    draft_path: str
    validation_status: str
    ready_for_checker_validation: bool
    required_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    missing_source_evidence_fields: tuple[str, ...]
    open_semantic_gaps: tuple[str, ...]
    proof_overclaim_errors: tuple[str, ...]
    checker_validation_attempted: bool
    checker_validation_passed: bool
    required_next_step: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def validate_stat_claim_certificate_witness_drafts(
    materializer_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Validate materialized witness drafts before checker execution.

    The validator is intentionally conservative: unfilled fields, missing
    source evidence, open semantic gaps, or proof-evidence overclaims prevent a
    row from becoming ready for checker validation.
    """

    errors: list[str] = []
    materializer_manifest_path = (
        materializer_dir / "stat_claim_certificate_witness_materializer_manifest.json"
    )
    draft_jsonl_path = materializer_dir / "stat_claim_certificate_witness_drafts.jsonl"
    materializer_manifest = _read_json(materializer_manifest_path, errors)
    draft_rows = _read_jsonl(draft_jsonl_path, errors)
    rows = [_validate_row(row) for row in draft_rows]
    by_family = Counter(row.certificate_family for row in rows)
    by_status = Counter(row.validation_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": STAT_CLAIM_CERTIFICATE_WITNESS_VALIDATOR_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "materializer_dir": str(materializer_dir),
        "materializer_manifest": str(materializer_manifest_path),
        "materializer_drafts_jsonl": str(draft_jsonl_path),
        "materializer_all_ok": bool(materializer_manifest.get("all_ok", False)),
        "materializer_proof_evidence_status": str(
            materializer_manifest.get("proof_evidence_status", "")
        ),
        "n_drafts": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_ready_for_checker_validation": sum(
            1 for row in rows if row.ready_for_checker_validation
        ),
        "n_incomplete": sum(1 for row in rows if row.missing_fields),
        "n_missing_source_evidence": sum(
            1 for row in rows if row.missing_source_evidence_fields
        ),
        "n_open_semantic_gap_rows": sum(1 for row in rows if row.open_semantic_gaps),
        "n_proof_overclaim_rows": sum(1 for row in rows if row.proof_overclaim_errors),
        "all_ok": (
            not errors
            and bool(materializer_manifest.get("all_ok", False))
            and all(row.ok for row in rows)
        ),
        "errors": errors,
        "by_family": dict(sorted(by_family.items())),
        "by_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "validation_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "validation only checks draft completeness and honesty constraints",
            "ready_for_checker_validation still requires a separate checker run",
            "checker validation still proves only the encoded certificate, not source semantic faithfulness",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "stat_claim_certificate_witness_validator_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_validation.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_validator.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _validate_row(row: dict[str, Any]) -> StatClaimCertificateWitnessValidationRow:
    errors: list[str] = []
    draft_path = Path(str(row.get("draft_path", "")))
    payload = _read_draft_payload(draft_path, errors)
    required_fields = tuple(str(field) for field in row.get("required_fields", ()) or () if str(field))
    fields = payload.get("fields", {})
    if not isinstance(fields, dict):
        errors.append("fields must be an object")
        fields = {}
    source_field_evidence = payload.get("source_field_evidence", {})
    if not isinstance(source_field_evidence, dict):
        errors.append("source_field_evidence must be an object")
        source_field_evidence = {}
    missing_fields = tuple(
        field
        for field in required_fields
        if field not in fields or _is_blank(fields.get(field))
    )
    missing_source_evidence = tuple(
        field
        for field in required_fields
        if field not in missing_fields and not _has_source_evidence(source_field_evidence.get(field))
    )
    open_semantic_gaps = tuple(
        str(item)
        for item in payload.get("open_semantic_gaps", []) or []
        if str(item)
    )
    checker_validation = payload.get("checker_validation", {})
    if not isinstance(checker_validation, dict):
        checker_validation = {}
        errors.append("checker_validation must be an object")
    checker_attempted = bool(checker_validation.get("attempted", False))
    checker_passed = bool(checker_validation.get("passed", False))
    proof_overclaim_errors = _proof_overclaim_errors(payload, checker_attempted, checker_passed)
    ready = (
        not errors
        and not missing_fields
        and not missing_source_evidence
        and not open_semantic_gaps
        and not proof_overclaim_errors
        and not checker_passed
    )
    if ready:
        status = "READY_FOR_CHECKER_VALIDATION"
        next_step = "run the kernel-verified certificate checker and record validation transcript"
    elif proof_overclaim_errors:
        status = "REJECTED_PROOF_EVIDENCE_OVERCLAIM"
        next_step = "remove proof overclaims and keep witness evidence separate from checker/Lean evidence"
    elif missing_fields:
        status = "REJECTED_INCOMPLETE_FIELDS"
        next_step = "fill all required witness fields with source-cited values"
    elif missing_source_evidence:
        status = "REJECTED_MISSING_SOURCE_EVIDENCE"
        next_step = "attach source evidence to every filled witness field"
    elif open_semantic_gaps:
        status = "REJECTED_OPEN_SEMANTIC_GAPS"
        next_step = "resolve or explicitly route semantic gaps before checker validation"
    else:
        status = "REJECTED_SCHEMA_ERRORS"
        next_step = "repair witness draft schema before validation"
    return StatClaimCertificateWitnessValidationRow(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_VALIDATOR_SCHEMA_VERSION,
        validation_id="stat_claim_certificate_witness_validation:"
        + stable_hash([row.get("draft_id", ""), str(draft_path)])[:16],
        draft_id=str(row.get("draft_id", "")),
        task_id=str(row.get("task_id", "")),
        target_id=str(row.get("target_id", "")),
        source_claim_id=str(row.get("source_claim_id", "")),
        question_id=str(row.get("question_id", "")),
        certificate_family=str(row.get("certificate_family", "")),
        draft_path=str(draft_path),
        validation_status=status,
        ready_for_checker_validation=ready,
        required_fields=required_fields,
        missing_fields=missing_fields,
        missing_source_evidence_fields=missing_source_evidence,
        open_semantic_gaps=open_semantic_gaps,
        proof_overclaim_errors=tuple(proof_overclaim_errors),
        checker_validation_attempted=checker_attempted,
        checker_validation_passed=checker_passed,
        required_next_step=next_step,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _proof_overclaim_errors(
    payload: dict[str, Any],
    checker_attempted: bool,
    checker_passed: bool,
) -> list[str]:
    errors: list[str] = []
    proof_status = str(payload.get("proof_evidence_status", ""))
    if proof_status != ALLOWED_DRAFT_PROOF_STATUS:
        errors.append(f"proof_evidence_status overclaims: {proof_status}")
    draft_status = str(payload.get("draft_status", ""))
    allowed_statuses = {
        "WITNESS_DRAFT_UNFILLED",
        "WITNESS_DRAFT_FILLED",
        "READY_FOR_CHECKER_VALIDATION",
    }
    if draft_status not in allowed_statuses:
        errors.append(f"draft_status is not allowed before checker validation: {draft_status}")
    if checker_passed:
        errors.append("checker_validation.passed is not accepted by draft validation")
    if checker_passed and not checker_attempted:
        errors.append("checker_validation.passed=true while attempted=false")
    if bool(payload.get("source_claim_proved", False)):
        errors.append("source_claim_proved=true is forbidden in witness drafts")
    return errors


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


def _read_draft_payload(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing draft file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse draft {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Statistical Claim Certificate Witness Validator",
        "",
        f"- Materializer: `{payload.get('materializer_manifest')}`",
        f"- Drafts: `{payload.get('n_ok')}/{payload.get('n_drafts')}`",
        f"- Ready for checker validation: `{payload.get('n_ready_for_checker_validation')}`",
        f"- Incomplete: `{payload.get('n_incomplete')}`",
        f"- Missing source evidence: `{payload.get('n_missing_source_evidence')}`",
        f"- Proof overclaim rows: `{payload.get('n_proof_overclaim_rows')}`",
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

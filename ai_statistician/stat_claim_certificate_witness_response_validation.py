from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .stat_claim_certificate_witness_prompt_packets import WORKER_OUTPUT_JSONL


STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_VALIDATION_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = (
    "STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_VALIDATION_NOT_PROOF_EVIDENCE"
)
ALLOWED_WORKER_PROOF_STATUS = "STAT_CLAIM_CERTIFICATE_WITNESS_DRAFT_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Witness response validation only audits untrusted worker output against "
    "prompt-packet contracts. Accepted rows may update witness drafts, but they "
    "are not checker validation, Lean proof evidence, or source theorem evidence."
)


@dataclass(frozen=True)
class StatClaimCertificateWitnessResponseValidationRow:
    schema_version: int
    response_validation_id: str
    prompt_packet_id: str
    draft_id: str
    task_id: str
    target_id: str
    source_claim_id: str
    question_id: str
    certificate_family: str
    response_present: bool
    response_contract_ok: bool
    accepted_for_draft_update: bool
    validation_status: str
    required_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    unknown_fields: tuple[str, ...]
    filled_fields: tuple[str, ...]
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


def validate_stat_claim_certificate_witness_worker_outputs(
    prompt_packets_dir: Path,
    out_dir: Path | None = None,
    *,
    worker_output_jsonl: Path | None = None,
) -> dict[str, object]:
    """Validate worker outputs for statistical certificate witness prompts.

    Missing worker-output files are non-failing: they mean the prompt packets
    are still awaiting generation. Present outputs are checked against the
    packet contract and may only be accepted for draft update, never as proof
    evidence.
    """

    errors: list[str] = []
    prompt_manifest_path = (
        prompt_packets_dir / "stat_claim_certificate_witness_prompt_packets_manifest.json"
    )
    prompt_jsonl_path = prompt_packets_dir / "stat_claim_certificate_witness_prompt_packets.jsonl"
    prompt_manifest = _read_json(prompt_manifest_path, errors)
    packets = _read_prompt_packets(prompt_jsonl_path, prompt_manifest, errors)
    response_jsonl_path = _resolve_worker_output_path(
        prompt_packets_dir,
        prompt_manifest,
        worker_output_jsonl,
    )
    responses, response_file_exists = _read_response_jsonl(response_jsonl_path, errors)
    response_by_prompt, duplicate_prompt_ids, unknown_responses = _index_responses(
        responses,
        packets,
    )
    rows = [
        _validation_row(
            packet,
            response=response_by_prompt.get(str(packet.get("prompt_packet_id", ""))),
            response_file_exists=response_file_exists,
        )
        for packet in packets
    ]
    rows.extend(
        _unknown_prompt_row(response, idx)
        for idx, response in unknown_responses
    )
    if duplicate_prompt_ids:
        errors.extend(f"duplicate worker response for prompt_packet_id: {pid}" for pid in duplicate_prompt_ids)
    by_family = Counter(row.certificate_family for row in rows if row.certificate_family)
    by_status = Counter(row.validation_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": (
            STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_VALIDATION_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt_packets_dir": str(prompt_packets_dir),
        "prompt_packets_manifest": str(prompt_manifest_path),
        "prompt_packets_jsonl": str(prompt_jsonl_path),
        "prompt_packets_all_ok": bool(prompt_manifest.get("all_ok", False)),
        "worker_output_jsonl": str(response_jsonl_path),
        "worker_output_jsonl_exists": response_file_exists,
        "n_prompt_packets": len(packets),
        "n_responses": len(responses),
        "n_response_validation_rows": len(rows),
        "n_response_present": sum(1 for row in rows if row.response_present),
        "n_awaiting_worker_output": sum(
            1 for row in rows if row.validation_status == "AWAITING_WORKER_OUTPUT"
        ),
        "n_missing_worker_outputs": sum(
            1 for row in rows if row.validation_status == "AWAITING_WORKER_OUTPUT"
        ),
        "n_contract_ok": sum(1 for row in rows if row.response_contract_ok),
        "n_accepted_for_draft_update": sum(
            1 for row in rows if row.accepted_for_draft_update
        ),
        "n_incomplete": sum(1 for row in rows if row.missing_fields),
        "n_unknown_field_rows": sum(1 for row in rows if row.unknown_fields),
        "n_missing_source_evidence": sum(
            1 for row in rows if row.missing_source_evidence_fields
        ),
        "n_open_semantic_gap_rows": sum(1 for row in rows if row.open_semantic_gaps),
        "n_proof_overclaim_rows": sum(1 for row in rows if row.proof_overclaim_errors),
        "n_unknown_prompt_rows": len(unknown_responses),
        "n_duplicate_prompt_rows": len(duplicate_prompt_ids),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": (
            not errors
            and bool(prompt_manifest.get("all_ok", False))
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
            "missing worker outputs are awaiting generation, not failures or proof evidence",
            "accepted responses only provide source-cited draft updates",
            "checker_validation.passed=true is rejected at this layer",
            "source_claim_proved=true is rejected until source theorem promotion has Lean/AXLE evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "stat_claim_certificate_witness_response_validation_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "stat_claim_certificate_witness_response_validation.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_response_validation.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _validation_row(
    packet: dict[str, Any],
    *,
    response: dict[str, Any] | None,
    response_file_exists: bool,
) -> StatClaimCertificateWitnessResponseValidationRow:
    prompt_packet_id = str(packet.get("prompt_packet_id", ""))
    draft_id = str(packet.get("draft_id", ""))
    task_id = str(packet.get("task_id", ""))
    target_id = str(packet.get("target_id", ""))
    source_claim_id = str(packet.get("source_claim_id", ""))
    question_id = str(packet.get("question_id", ""))
    certificate_family = str(packet.get("certificate_family", ""))
    required_fields = _str_tuple(packet.get("required_fields", ()))
    if response is None:
        status = "AWAITING_WORKER_OUTPUT"
        next_step = (
            "wait for stat_claim_certificate_witness_worker_outputs.jsonl"
            if response_file_exists
            else "run a witness worker for this prompt packet"
        )
        return StatClaimCertificateWitnessResponseValidationRow(
            schema_version=(
                STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_VALIDATION_SCHEMA_VERSION
            ),
            response_validation_id=_validation_id(prompt_packet_id, draft_id, None),
            prompt_packet_id=prompt_packet_id,
            draft_id=draft_id,
            task_id=task_id,
            target_id=target_id,
            source_claim_id=source_claim_id,
            question_id=question_id,
            certificate_family=certificate_family,
            response_present=False,
            response_contract_ok=False,
            accepted_for_draft_update=False,
            validation_status=status,
            required_fields=required_fields,
            missing_fields=(),
            unknown_fields=(),
            filled_fields=(),
            missing_source_evidence_fields=(),
            open_semantic_gaps=(),
            proof_overclaim_errors=(),
            checker_validation_attempted=False,
            checker_validation_passed=False,
            required_next_step=next_step,
            proof_evidence_status=PROOF_EVIDENCE_STATUS,
            proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
            ok=True,
            errors=(),
        )

    errors: list[str] = []
    for field in ("prompt_packet_id", "draft_id", "task_id"):
        _require_matching_field(response, packet, field, errors)
    fields = response.get("fields", {})
    if not isinstance(fields, dict):
        errors.append("fields must be an object")
        fields = {}
    source_field_evidence = response.get("source_field_evidence", {})
    if not isinstance(source_field_evidence, dict):
        errors.append("source_field_evidence must be an object")
        source_field_evidence = {}
    open_semantic_gaps_raw = response.get("open_semantic_gaps", [])
    if not isinstance(open_semantic_gaps_raw, list):
        errors.append("open_semantic_gaps must be a list")
        open_semantic_gaps_raw = []
    checker_validation = response.get("checker_validation", {})
    if not isinstance(checker_validation, dict):
        errors.append("checker_validation must be an object")
        checker_validation = {}
    checker_attempted = bool(checker_validation.get("attempted", False))
    checker_passed = bool(checker_validation.get("passed", False))
    missing_fields = tuple(
        field
        for field in required_fields
        if field not in fields or _is_blank(fields.get(field))
    )
    unknown_fields = tuple(
        sorted(str(field) for field in fields if str(field) not in set(required_fields))
    )
    filled_fields = tuple(
        field
        for field in required_fields
        if field not in missing_fields and not _is_blank(fields.get(field))
    )
    missing_source_evidence = tuple(
        field
        for field in filled_fields
        if not _has_source_evidence(source_field_evidence.get(field))
    )
    open_semantic_gaps = tuple(str(item) for item in open_semantic_gaps_raw if str(item))
    proof_overclaim_errors = _proof_overclaim_errors(
        response,
        checker_attempted,
        checker_passed,
    )
    contract_ok = (
        not errors
        and not missing_fields
        and not unknown_fields
        and not missing_source_evidence
        and not open_semantic_gaps
        and not proof_overclaim_errors
    )
    accepted = contract_ok
    if accepted:
        status = "ACCEPTED_FOR_DRAFT_UPDATE"
        next_step = "materialize the source-cited witness fields, then run the checker gate"
    elif errors:
        status = "REJECTED_SCHEMA_OR_IDENTITY_ERRORS"
        next_step = "repair the worker response schema and prompt identity fields"
    elif proof_overclaim_errors:
        status = "REJECTED_PROOF_EVIDENCE_OVERCLAIM"
        next_step = "remove checker/source-proof claims from the witness response"
    elif unknown_fields:
        status = "REJECTED_UNKNOWN_WITNESS_FIELDS"
        next_step = "remove witness fields not listed in the prompt-packet contract"
    elif missing_fields:
        status = "REJECTED_INCOMPLETE_FIELDS"
        next_step = "fill required witness fields or leave the response awaiting revision"
    elif missing_source_evidence:
        status = "REJECTED_MISSING_SOURCE_EVIDENCE"
        next_step = "attach source evidence to every filled witness field"
    else:
        status = "REJECTED_OPEN_SEMANTIC_GAPS"
        next_step = "resolve source-to-witness semantic gaps before draft update"
    return StatClaimCertificateWitnessResponseValidationRow(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_VALIDATION_SCHEMA_VERSION,
        response_validation_id=_validation_id(prompt_packet_id, draft_id, response),
        prompt_packet_id=prompt_packet_id,
        draft_id=draft_id,
        task_id=task_id,
        target_id=target_id,
        source_claim_id=source_claim_id,
        question_id=question_id,
        certificate_family=certificate_family,
        response_present=True,
        response_contract_ok=contract_ok,
        accepted_for_draft_update=accepted,
        validation_status=status,
        required_fields=required_fields,
        missing_fields=missing_fields,
        unknown_fields=unknown_fields,
        filled_fields=filled_fields,
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


def _unknown_prompt_row(
    response: dict[str, Any],
    idx: int,
) -> StatClaimCertificateWitnessResponseValidationRow:
    prompt_packet_id = str(response.get("prompt_packet_id", ""))
    draft_id = str(response.get("draft_id", ""))
    task_id = str(response.get("task_id", ""))
    errors = (f"unknown prompt_packet_id at response row {idx}: {prompt_packet_id}",)
    proof_overclaim_errors = _proof_overclaim_errors(
        response,
        checker_attempted=bool(
            response.get("checker_validation", {}).get("attempted", False)
            if isinstance(response.get("checker_validation", {}), dict)
            else False
        ),
        checker_passed=bool(
            response.get("checker_validation", {}).get("passed", False)
            if isinstance(response.get("checker_validation", {}), dict)
            else False
        ),
    )
    return StatClaimCertificateWitnessResponseValidationRow(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_RESPONSE_VALIDATION_SCHEMA_VERSION,
        response_validation_id="stat_claim_certificate_witness_response_validation:unknown:"
        + stable_hash([idx, response])[:16],
        prompt_packet_id=prompt_packet_id,
        draft_id=draft_id,
        task_id=task_id,
        target_id="",
        source_claim_id="",
        question_id="",
        certificate_family="",
        response_present=True,
        response_contract_ok=False,
        accepted_for_draft_update=False,
        validation_status="REJECTED_UNKNOWN_PROMPT_PACKET",
        required_fields=(),
        missing_fields=(),
        unknown_fields=(),
        filled_fields=(),
        missing_source_evidence_fields=(),
        open_semantic_gaps=_str_tuple(response.get("open_semantic_gaps", ())),
        proof_overclaim_errors=tuple(proof_overclaim_errors),
        checker_validation_attempted=False,
        checker_validation_passed=False,
        required_next_step="match the response to an issued prompt packet before validation",
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=False,
        errors=errors,
    )


def _proof_overclaim_errors(
    response: dict[str, Any],
    checker_attempted: bool,
    checker_passed: bool,
) -> list[str]:
    errors: list[str] = []
    proof_status = str(response.get("proof_evidence_status", ""))
    if proof_status != ALLOWED_WORKER_PROOF_STATUS:
        errors.append(f"proof_evidence_status overclaims: {proof_status}")
    if checker_attempted:
        errors.append("checker_validation.attempted=true is not accepted in worker output")
    if checker_passed:
        errors.append("checker_validation.passed=true is not accepted in worker output")
    if bool(response.get("source_claim_proved", False)):
        errors.append("source_claim_proved=true is forbidden in witness worker output")
    return errors


def _index_responses(
    responses: list[dict[str, Any]],
    packets: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], tuple[str, ...], list[tuple[int, dict[str, Any]]]]:
    packet_ids = {
        str(packet.get("prompt_packet_id", ""))
        for packet in packets
        if str(packet.get("prompt_packet_id", ""))
    }
    response_by_prompt: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    unknown: list[tuple[int, dict[str, Any]]] = []
    for idx, response in enumerate(responses, start=1):
        prompt_packet_id = str(response.get("prompt_packet_id", ""))
        if prompt_packet_id not in packet_ids:
            unknown.append((idx, response))
            continue
        if prompt_packet_id in response_by_prompt:
            duplicates.append(prompt_packet_id)
            continue
        response_by_prompt[prompt_packet_id] = response
    return response_by_prompt, tuple(sorted(set(duplicates))), unknown


def _resolve_worker_output_path(
    prompt_packets_dir: Path,
    prompt_manifest: dict[str, Any],
    worker_output_jsonl: Path | None,
) -> Path:
    if worker_output_jsonl is not None:
        return worker_output_jsonl
    manifest_value = str(prompt_manifest.get("worker_output_jsonl", WORKER_OUTPUT_JSONL))
    path = Path(manifest_value)
    return path if path.is_absolute() else prompt_packets_dir / path


def _read_prompt_packets(
    prompt_jsonl_path: Path,
    prompt_manifest: dict[str, Any],
    errors: list[str],
) -> list[dict[str, Any]]:
    rows = _read_jsonl(prompt_jsonl_path, errors, missing_ok=False)
    if rows:
        return rows
    manifest_rows = prompt_manifest.get("packets", [])
    if isinstance(manifest_rows, list):
        return [row for row in manifest_rows if isinstance(row, dict)]
    return []


def _read_response_jsonl(
    path: Path,
    errors: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    if not path.exists():
        return [], False
    return _read_jsonl(path, errors, missing_ok=False), True


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


def _read_jsonl(path: Path, errors: list[str], *, missing_ok: bool) -> list[dict[str, Any]]:
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


def _require_matching_field(
    response: dict[str, Any],
    packet: dict[str, Any],
    field: str,
    errors: list[str],
) -> None:
    if str(response.get(field, "")) != str(packet.get(field, "")):
        errors.append(
            f"{field} mismatch: expected {packet.get(field, '')}, got {response.get(field, '')}"
        )


def _validation_id(
    prompt_packet_id: str,
    draft_id: str,
    response: dict[str, Any] | None,
) -> str:
    return "stat_claim_certificate_witness_response_validation:" + stable_hash(
        [prompt_packet_id, draft_id, response or "awaiting"]
    )[:16]


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
        "# Statistical Claim Certificate Witness Response Validation",
        "",
        f"- Prompt packets: `{payload.get('n_prompt_packets')}`",
        f"- Worker responses: `{payload.get('n_responses')}`",
        f"- Awaiting worker output: `{payload.get('n_awaiting_worker_output')}`",
        f"- Accepted for draft update: `{payload.get('n_accepted_for_draft_update')}`",
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

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


STAT_CLAIM_CERTIFICATE_WITNESS_CONTEXT_TRIAGE_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "STAT_CLAIM_CERTIFICATE_WITNESS_CONTEXT_TRIAGE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Certificate witness context triage is a routing artifact over retrieved "
    "source snippets. It can prioritize worker-ready packets and source-review "
    "items, but it is not witness validation, checker validation, Lean proof "
    "evidence, or source theorem evidence."
)


@dataclass(frozen=True)
class StatClaimCertificateWitnessContextTriageRow:
    schema_version: int
    triage_id: str
    context_packet_id: str
    prompt_packet_id: str
    draft_id: str
    task_id: str
    target_id: str
    source_claim_id: str
    question_id: str
    certificate_family: str
    checker_name: str
    checker_obligation_id: str
    required_fields: tuple[str, ...]
    direct_match_fields: tuple[str, ...]
    fallback_context_fields: tuple[str, ...]
    no_context_fields: tuple[str, ...]
    missing_source_paths: tuple[str, ...]
    snippet_ids: tuple[str, ...]
    context_status: str
    worker_ready: bool
    source_review_required: bool
    required_next_step: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_stat_claim_certificate_witness_context_triage(
    context_packets_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Triage witness context packets before worker response generation."""

    errors: list[str] = []
    context_manifest_path = (
        context_packets_dir / "stat_claim_certificate_witness_context_packets_manifest.json"
    )
    context_jsonl_path = context_packets_dir / "stat_claim_certificate_witness_context_packets.jsonl"
    context_manifest = _read_json(context_manifest_path, errors)
    context_rows = _read_jsonl(context_jsonl_path, errors)
    rows = [_triage_row(row) for row in context_rows]
    by_family = Counter(row.certificate_family for row in rows)
    by_status = Counter(row.context_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": STAT_CLAIM_CERTIFICATE_WITNESS_CONTEXT_TRIAGE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "context_packets_dir": str(context_packets_dir),
        "context_packets_manifest": str(context_manifest_path),
        "context_packets_jsonl": str(context_jsonl_path),
        "context_packets_all_ok": bool(context_manifest.get("all_ok", False)),
        "context_packets_proof_evidence_status": str(
            context_manifest.get("proof_evidence_status", "")
        ),
        "n_context_packets": len(context_rows),
        "n_triage_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_worker_ready": sum(1 for row in rows if row.worker_ready),
        "n_source_review_required": sum(1 for row in rows if row.source_review_required),
        "n_blocked_missing_context": by_status.get("BLOCKED_MISSING_CONTEXT", 0),
        "n_direct_match_fields": sum(len(row.direct_match_fields) for row in rows),
        "n_fallback_context_fields": sum(len(row.fallback_context_fields) for row in rows),
        "n_no_context_fields": sum(len(row.no_context_fields) for row in rows),
        "n_missing_source_paths": sum(len(row.missing_source_paths) for row in rows),
        "all_ok": (
            not errors
            and bool(context_manifest.get("all_ok", False))
            and all(row.ok for row in rows)
        ),
        "errors": errors,
        "by_family": dict(sorted(by_family.items())),
        "by_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "triage_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "worker-ready means every required field has direct source-term context, not that a witness is filled",
            "fallback context fields require source review before worker output should be accepted",
            "triage does not validate witness values, checker contracts, semantic linkage, or Lean proofs",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "stat_claim_certificate_witness_context_triage_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_context_triage.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_context_worker_ready.jsonl").write_text(
            "\n".join(
                json.dumps(asdict(row), sort_keys=True)
                for row in rows
                if row.worker_ready
            )
            + ("\n" if any(row.worker_ready for row in rows) else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_context_source_review.jsonl").write_text(
            "\n".join(
                json.dumps(asdict(row), sort_keys=True)
                for row in rows
                if row.source_review_required
            )
            + ("\n" if any(row.source_review_required for row in rows) else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_context_triage.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _triage_row(row: dict[str, Any]) -> StatClaimCertificateWitnessContextTriageRow:
    errors: list[str] = []
    required_fields = _str_tuple(row.get("required_fields", ()))
    hints = row.get("field_context_hints", {})
    if not isinstance(hints, dict):
        hints = {}
        errors.append("field_context_hints must be an object")
    direct_fields: list[str] = []
    fallback_fields: list[str] = []
    no_context_fields: list[str] = []
    for field in required_fields:
        hint = hints.get(field, {})
        if not isinstance(hint, dict):
            no_context_fields.append(field)
            continue
        status = str(hint.get("match_status", ""))
        if status == "DIRECT_FIELD_TERM_MATCH":
            direct_fields.append(field)
        elif status == "FALLBACK_PACKET_CONTEXT":
            fallback_fields.append(field)
        else:
            no_context_fields.append(field)
    missing_paths = _str_tuple(row.get("missing_source_paths", ()))
    packet_errors = _str_tuple(row.get("errors", ()))
    snippets = row.get("snippets", ())
    snippet_ids = tuple(
        str(snippet.get("snippet_id", ""))
        for snippet in snippets
        if isinstance(snippet, dict) and str(snippet.get("snippet_id", ""))
    )
    if not required_fields:
        errors.append("required_fields missing")
    if missing_paths or no_context_fields or packet_errors:
        context_status = "BLOCKED_MISSING_CONTEXT"
        worker_ready = False
        source_review = True
        next_step = "repair missing source context or field hints before worker response generation"
    elif fallback_fields:
        context_status = "NEEDS_SOURCE_CONTEXT_REVIEW"
        worker_ready = False
        source_review = True
        next_step = "review fallback-context fields and add direct source support or leave them as semantic gaps"
    else:
        context_status = "READY_FOR_WORKER_RESPONSE"
        worker_ready = True
        source_review = False
        next_step = "generate source-cited witness response and run response validation"
    return StatClaimCertificateWitnessContextTriageRow(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_CONTEXT_TRIAGE_SCHEMA_VERSION,
        triage_id="stat_claim_certificate_witness_context_triage:"
        + stable_hash([row.get("context_packet_id", ""), required_fields])[:16],
        context_packet_id=str(row.get("context_packet_id", "")),
        prompt_packet_id=str(row.get("prompt_packet_id", "")),
        draft_id=str(row.get("draft_id", "")),
        task_id=str(row.get("task_id", "")),
        target_id=str(row.get("target_id", "")),
        source_claim_id=str(row.get("source_claim_id", "")),
        question_id=str(row.get("question_id", "")),
        certificate_family=str(row.get("certificate_family", "")),
        checker_name=str(row.get("checker_name", "")),
        checker_obligation_id=str(row.get("checker_obligation_id", "")),
        required_fields=required_fields,
        direct_match_fields=tuple(direct_fields),
        fallback_context_fields=tuple(fallback_fields),
        no_context_fields=tuple(no_context_fields),
        missing_source_paths=missing_paths,
        snippet_ids=snippet_ids,
        context_status=context_status,
        worker_ready=worker_ready,
        source_review_required=source_review,
        required_next_step=next_step,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


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


def _str_tuple(value: object) -> tuple[str, ...]:
    return tuple(str(item) for item in value or () if str(item))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Statistical Claim Certificate Witness Context Triage",
        "",
        f"- Context packets: `{payload.get('context_packets_manifest')}`",
        f"- Triage rows: `{payload.get('n_ok')}/{payload.get('n_triage_rows')}`",
        f"- Worker-ready: `{payload.get('n_worker_ready')}`",
        f"- Source review required: `{payload.get('n_source_review_required')}`",
        f"- Blocked missing context: `{payload.get('n_blocked_missing_context')}`",
        f"- Direct field matches: `{payload.get('n_direct_match_fields')}`",
        f"- Fallback fields: `{payload.get('n_fallback_context_fields')}`",
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

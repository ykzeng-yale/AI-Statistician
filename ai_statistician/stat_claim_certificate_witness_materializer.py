from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


STAT_CLAIM_CERTIFICATE_WITNESS_MATERIALIZER_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "STAT_CLAIM_CERTIFICATE_WITNESS_DRAFT_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Materialized witness JSON files are untrusted draft work packets. They are "
    "not checker validation, Lean proof evidence, or source theorem evidence. "
    "Every field must be filled with cited source evidence, passed through the "
    "certificate checker contract, semantically linked to the source claim, and "
    "promoted through Lean/AXLE gates before any proof claim is made."
)


@dataclass(frozen=True)
class StatClaimCertificateWitnessDraftRow:
    schema_version: int
    draft_id: str
    task_id: str
    target_id: str
    source_claim_id: str
    question_id: str
    problem_class: str
    certificate_family: str
    checker_name: str
    checker_obligation_id: str
    required_fields: tuple[str, ...]
    draft_path: str
    expected_witness_path: str
    draft_status: str
    ready_for_checker_validation: bool
    proof_evidence_status: str
    proof_evidence_boundary: str
    required_next_step: str
    ok: bool
    errors: tuple[str, ...] = ()


def materialize_stat_claim_certificate_witness_drafts(
    witness_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    max_drafts: int | None = None,
) -> dict[str, object]:
    """Write one unfilled witness draft JSON file for each queue task."""

    errors: list[str] = []
    queue_manifest_path = witness_queue_dir / "stat_claim_certificate_witness_queue_manifest.json"
    task_jsonl_path = witness_queue_dir / "stat_claim_certificate_witness_tasks.jsonl"
    queue_manifest = _read_json(queue_manifest_path, errors)
    task_rows = _read_jsonl(task_jsonl_path, errors)
    if max_drafts is not None:
        task_rows = task_rows[:max_drafts]
    materialization_root = out_dir if out_dir is not None else witness_queue_dir
    draft_dir = materialization_root / "witness_drafts"
    rows = [
        _draft_row(task, draft_dir=draft_dir)
        for task in task_rows
    ]
    by_family = Counter(row.certificate_family for row in rows)
    payload: dict[str, object] = {
        "schema_version": STAT_CLAIM_CERTIFICATE_WITNESS_MATERIALIZER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "witness_queue_dir": str(witness_queue_dir),
        "witness_queue_manifest": str(queue_manifest_path),
        "witness_queue_tasks_jsonl": str(task_jsonl_path),
        "queue_all_ok": bool(queue_manifest.get("all_ok", False)),
        "queue_proof_evidence_status": str(queue_manifest.get("proof_evidence_status", "")),
        "n_queue_tasks": int(queue_manifest.get("n_tasks", len(task_rows)) or 0),
        "n_task_rows_read": len(task_rows),
        "n_drafts": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_ready_for_checker_validation": sum(1 for row in rows if row.ready_for_checker_validation),
        "n_unfilled": sum(1 for row in rows if row.draft_status == "WITNESS_DRAFT_UNFILLED"),
        "all_ok": not errors and bool(queue_manifest.get("all_ok", False)) and all(row.ok for row in rows),
        "errors": errors,
        "by_family": dict(sorted(by_family.items())),
        "drafts": [asdict(row) for row in rows],
        "draft_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "draft files are blank worker packets, not generated evidence",
            "null witness fields must be replaced with cited source-backed values before validation",
            "checker validation and semantic linkage review remain separate gates",
            "a checker theorem proves only its encoded certificate contract, not the paper theorem",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
    if out_dir is not None or rows:
        draft_dir.mkdir(parents=True, exist_ok=True)
    for row, task in zip(rows, task_rows, strict=True):
        Path(row.draft_path).write_text(
            json.dumps(_draft_payload(row, task), indent=2, default=str),
            encoding="utf-8",
        )
    if out_dir is not None:
        (out_dir / "stat_claim_certificate_witness_materializer_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_drafts.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_materializer.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _draft_row(task: dict[str, Any], *, draft_dir: Path) -> StatClaimCertificateWitnessDraftRow:
    errors: list[str] = []
    task_id = str(task.get("task_id", ""))
    target_id = str(task.get("target_id", ""))
    family = str(task.get("certificate_family", ""))
    required_fields = tuple(str(field) for field in task.get("witness_schema", ()) or () if str(field))
    if not task_id:
        errors.append("task_id missing")
    if not target_id:
        errors.append("target_id missing")
    if not family:
        errors.append("certificate_family missing")
    if not required_fields:
        errors.append("witness_schema missing")
    safe_id = stable_hash([task_id, target_id, family])[:16]
    return StatClaimCertificateWitnessDraftRow(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_MATERIALIZER_SCHEMA_VERSION,
        draft_id="stat_claim_certificate_witness_draft:" + safe_id,
        task_id=task_id,
        target_id=target_id,
        source_claim_id=str(task.get("source_claim_id", "")),
        question_id=str(task.get("question_id", "")),
        problem_class=str(task.get("problem_class", "")),
        certificate_family=family,
        checker_name=str(task.get("checker_name", "")),
        checker_obligation_id=str(task.get("checker_obligation_id", "")),
        required_fields=required_fields,
        draft_path=str(draft_dir / f"{safe_id}.json"),
        expected_witness_path=str(task.get("expected_witness_path", "")),
        draft_status="WITNESS_DRAFT_UNFILLED",
        ready_for_checker_validation=False,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        required_next_step=(
            "fill every witness field with source-cited values, list open semantic gaps, "
            "then run checker validation before any promotion"
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _draft_payload(row: StatClaimCertificateWitnessDraftRow, task: dict[str, Any]) -> dict[str, object]:
    fields = {field: None for field in row.required_fields}
    source_field_evidence = {field: [] for field in row.required_fields}
    return {
        "schema_version": row.schema_version,
        "draft_id": row.draft_id,
        "task_id": row.task_id,
        "target_id": row.target_id,
        "source_claim_id": row.source_claim_id,
        "question_id": row.question_id,
        "problem_class": row.problem_class,
        "certificate_family": row.certificate_family,
        "checker_name": row.checker_name,
        "checker_obligation_id": row.checker_obligation_id,
        "draft_status": row.draft_status,
        "fields": fields,
        "source_field_evidence": source_field_evidence,
        "open_semantic_gaps": [
            "witness values have not been generated or linked to source evidence yet"
        ],
        "semantic_linkage_requirements": list(task.get("semantic_linkage_requirements", ()) or ()),
        "forbidden_shortcuts": list(task.get("forbidden_shortcuts", ()) or ()),
        "checker_validation": {
            "attempted": False,
            "passed": False,
            "transcript_path": "",
        },
        "source_evidence_paths": list(task.get("evidence_paths", ()) or ()),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "required_next_step": row.required_next_step,
    }


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
        "# Statistical Claim Certificate Witness Materializer",
        "",
        f"- Witness queue: `{payload.get('witness_queue_manifest')}`",
        f"- Drafts: `{payload.get('n_ok')}/{payload.get('n_drafts')}`",
        f"- Ready for checker validation: `{payload.get('n_ready_for_checker_validation')}`",
        f"- Unfilled: `{payload.get('n_unfilled')}`",
        f"- Proof status: `{payload.get('proof_evidence_status')}`",
        "",
        "## Families",
        "",
    ]
    by_family = payload.get("by_family", {})
    if isinstance(by_family, dict) and by_family:
        for family, count in sorted(by_family.items()):
            lines.append(f"- `{family}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

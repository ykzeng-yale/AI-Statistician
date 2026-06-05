from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


STAT_CLAIM_CERTIFICATE_WITNESS_QUEUE_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "STAT_CLAIM_CERTIFICATE_WITNESS_QUEUE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Witness-queue rows are worker tasks for untrusted certificate generation. "
    "They are not proof evidence for the source statistical claim. A generated "
    "witness must be checked against the kernel-verified checker contract, "
    "linked back to the source claim without assumption drift, and promoted "
    "through the final Lean/AXLE evidence gate before any proof claim is made."
)


@dataclass(frozen=True)
class StatClaimCertificateWitnessTask:
    schema_version: int
    task_id: str
    target_id: str
    source_claim_id: str
    question_id: str
    problem_class: str
    claim_status: str
    certificate_family: str
    priority: str
    statement: str
    checker_name: str
    checker_obligation_id: str
    checker_verifier: str
    checker_verification_strength: str
    witness_schema: tuple[str, ...]
    witness_template: dict[str, object]
    generator_contract: str
    checker_contract: str
    semantic_linkage_requirements: tuple[str, ...]
    forbidden_shortcuts: tuple[str, ...]
    required_gate: str
    expected_witness_path: str
    evidence_paths: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class StatClaimCertificateWitnessBlockedRow:
    schema_version: int
    target_id: str
    source_claim_id: str
    question_id: str
    problem_class: str
    certificate_family: str
    readiness_status: str
    checker_obligation_id: str
    required_next_step: str
    required_gate: str
    evidence_paths: tuple[str, ...]
    proof_evidence_status: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_stat_claim_certificate_witness_queue(
    certificate_plan_dir: Path,
    readiness_dir: Path,
    out_dir: Path | None = None,
    *,
    max_tasks: int | None = None,
) -> dict[str, object]:
    """Export witness-generation tasks for kernel-ready certificate targets.

    This queue is deliberately downstream of the readiness overlay. It does not
    invent witness values; it gives a worker the exact JSON slots and gates that
    need to be filled and checked.
    """

    errors: list[str] = []
    plan_manifest_path = certificate_plan_dir / "stat_claim_certificate_plan_manifest.json"
    plan_jsonl_path = certificate_plan_dir / "stat_claim_certificate_targets.jsonl"
    readiness_manifest_path = readiness_dir / "stat_claim_certificate_readiness_manifest.json"
    readiness_jsonl_path = readiness_dir / "stat_claim_certificate_readiness.jsonl"
    plan_manifest = _read_json(plan_manifest_path, errors)
    target_rows = _read_jsonl(plan_jsonl_path, errors)
    readiness_manifest = _read_json(readiness_manifest_path, errors)
    readiness_rows = _read_jsonl(readiness_jsonl_path, errors)
    target_by_id = {
        str(row.get("target_id", "")): row
        for row in target_rows
        if isinstance(row, dict) and str(row.get("target_id", ""))
    }

    ready_rows = [
        row
        for row in readiness_rows
        if bool(row.get("ready_for_witness_validation", False))
        and str(row.get("readiness_status", "")) == "READY_FOR_WITNESS_GENERATION_AND_VALIDATION"
    ]
    if max_tasks is not None:
        ready_rows = ready_rows[:max_tasks]
    tasks = [
        _task_from_rows(
            readiness_row,
            target_by_id=target_by_id,
            out_dir=out_dir,
        )
        for readiness_row in ready_rows
    ]
    ready_target_ids = {task.target_id for task in tasks}
    blocked = [
        _blocked_row(row)
        for row in readiness_rows
        if str(row.get("target_id", "")) not in ready_target_ids
        and not bool(row.get("ready_for_witness_validation", False))
    ]
    by_family = Counter(task.certificate_family for task in tasks)
    blocked_by_status = Counter(row.readiness_status for row in blocked)
    payload: dict[str, object] = {
        "schema_version": STAT_CLAIM_CERTIFICATE_WITNESS_QUEUE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "certificate_plan_dir": str(certificate_plan_dir),
        "certificate_plan_manifest": str(plan_manifest_path),
        "certificate_plan_jsonl": str(plan_jsonl_path),
        "readiness_dir": str(readiness_dir),
        "readiness_manifest": str(readiness_manifest_path),
        "readiness_jsonl": str(readiness_jsonl_path),
        "plan_all_ok": bool(plan_manifest.get("all_ok", False)),
        "readiness_all_ok": bool(readiness_manifest.get("all_ok", False)),
        "readiness_proof_evidence_status": str(readiness_manifest.get("proof_evidence_status", "")),
        "n_readiness_rows": len(readiness_rows),
        "n_ready_rows": sum(1 for row in readiness_rows if bool(row.get("ready_for_witness_validation", False))),
        "n_tasks": len(tasks),
        "n_ok": sum(1 for task in tasks if task.ok),
        "n_blocked": len(blocked),
        "n_blocked_ok": sum(1 for row in blocked if row.ok),
        "n_missing_checker": blocked_by_status.get("CHECKER_NOT_AVAILABLE", 0),
        "n_non_kernel_checker": blocked_by_status.get("CHECKER_PRESENT_NOT_KERNEL_VERIFIED", 0),
        "all_ok": (
            not errors
            and bool(plan_manifest.get("all_ok", False))
            and bool(readiness_manifest.get("all_ok", False))
            and all(task.ok for task in tasks)
            and all(row.ok for row in blocked)
        ),
        "errors": errors,
        "by_family": dict(sorted(by_family.items())),
        "blocked_by_status": dict(sorted(blocked_by_status.items())),
        "tasks": [asdict(task) for task in tasks],
        "blocked": [asdict(row) for row in blocked],
        "task_fingerprint": stable_hash([asdict(task) for task in tasks]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "witness queue rows are task routing artifacts, not verifier evidence",
            "a filled witness must be validated by the checker contract before promotion",
            "checker-theorem kernel evidence proves only checker soundness, not source semantic faithfulness",
            "source claim linkage must reject assumption strengthening and theorem restatement shortcuts",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "stat_claim_certificate_witness_queue_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_tasks.jsonl").write_text(
            "\n".join(json.dumps(asdict(task), sort_keys=True) for task in tasks)
            + ("\n" if tasks else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_blocked.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in blocked)
            + ("\n" if blocked else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_queue.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _task_from_rows(
    readiness_row: dict[str, Any],
    *,
    target_by_id: dict[str, dict[str, Any]],
    out_dir: Path | None,
) -> StatClaimCertificateWitnessTask:
    errors: list[str] = []
    target_id = str(readiness_row.get("target_id", ""))
    target = target_by_id.get(target_id, {})
    if not target_id:
        errors.append("target_id missing")
    if not target:
        errors.append(f"target row missing for {target_id}")
    family = str(readiness_row.get("certificate_family") or target.get("certificate_family", ""))
    witness_schema = tuple(str(item) for item in target.get("witness_schema", ()) or ())
    if not witness_schema:
        errors.append("witness_schema missing")
    if not bool(readiness_row.get("checker_kernel_verified", False)):
        errors.append("checker_kernel_verified must be true before witness task export")
    expected_witness_path = _expected_witness_path(target_id, family, out_dir)
    return StatClaimCertificateWitnessTask(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_QUEUE_SCHEMA_VERSION,
        task_id="stat_claim_certificate_witness:" + stable_hash([target_id, family])[:16],
        target_id=target_id,
        source_claim_id=str(readiness_row.get("source_claim_id") or target.get("source_claim_id", "")),
        question_id=str(readiness_row.get("question_id") or target.get("question_id", "")),
        problem_class=str(readiness_row.get("problem_class") or target.get("problem_class", "")),
        claim_status=str(target.get("claim_status", "")),
        certificate_family=family,
        priority=str(target.get("priority", "medium")),
        statement=str(target.get("statement", "")),
        checker_name=str(readiness_row.get("checker_name") or target.get("checker_name", "")),
        checker_obligation_id=str(readiness_row.get("checker_obligation_id", "")),
        checker_verifier=str(readiness_row.get("checker_verifier", "")),
        checker_verification_strength=str(readiness_row.get("checker_verification_strength", "")),
        witness_schema=witness_schema,
        witness_template=_witness_template(witness_schema),
        generator_contract=str(target.get("generator_contract", "")),
        checker_contract=str(target.get("checker_contract", "")),
        semantic_linkage_requirements=(
            "cite the source claim id and evidence paths used for every witness field",
            "do not add assumptions or strengthen regularity conditions silently",
            "state every source-to-encoded-claim gap as an open semantic review item",
            "separate simulation support from checker validation and Lean proof evidence",
        ),
        forbidden_shortcuts=(
            "do not fill witness fields with the theorem conclusion",
            "do not use rfl/trivial/restated-target helper lemmas as source evidence",
            "do not mark the source claim proved from witness generation alone",
            "do not hide failed or missing semantic linkage behind checker soundness",
        ),
        required_gate=str(readiness_row.get("required_gate") or target.get("required_gate", "")),
        expected_witness_path=expected_witness_path,
        evidence_paths=tuple(
            str(path)
            for path in (
                *(readiness_row.get("evidence_paths", ()) or ()),
                *(target.get("evidence_paths", ()) or ()),
            )
            if str(path)
        ),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _blocked_row(row: dict[str, Any]) -> StatClaimCertificateWitnessBlockedRow:
    errors: list[str] = []
    target_id = str(row.get("target_id", ""))
    if not target_id:
        errors.append("target_id missing")
    return StatClaimCertificateWitnessBlockedRow(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_QUEUE_SCHEMA_VERSION,
        target_id=target_id,
        source_claim_id=str(row.get("source_claim_id", "")),
        question_id=str(row.get("question_id", "")),
        problem_class=str(row.get("problem_class", "")),
        certificate_family=str(row.get("certificate_family", "")),
        readiness_status=str(row.get("readiness_status", "")),
        checker_obligation_id=str(row.get("checker_obligation_id", "")),
        required_next_step=str(row.get("required_next_step", "")),
        required_gate=str(row.get("required_gate", "")),
        evidence_paths=tuple(str(path) for path in row.get("evidence_paths", ()) or () if str(path)),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        ok=not errors,
        errors=tuple(errors),
    )


def _witness_template(witness_schema: tuple[str, ...]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "WITNESS_REQUIRED",
        "fields": {field: None for field in witness_schema},
        "source_field_evidence": {field: [] for field in witness_schema},
        "open_semantic_gaps": [],
        "checker_validation": {
            "attempted": False,
            "passed": False,
            "transcript_path": "",
        },
    }


def _expected_witness_path(target_id: str, family: str, out_dir: Path | None) -> str:
    safe_id = stable_hash([target_id, family])[:16]
    base = out_dir / "witnesses" if out_dir is not None else Path("witnesses")
    return str(base / f"{safe_id}.json")


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
        "# Statistical Claim Certificate Witness Queue",
        "",
        f"- Certificate plan: `{payload.get('certificate_plan_manifest')}`",
        f"- Readiness overlay: `{payload.get('readiness_manifest')}`",
        f"- Tasks: `{payload.get('n_ok')}/{payload.get('n_tasks')}`",
        f"- Blocked: `{payload.get('n_blocked')}`",
        f"- Proof status: `{payload.get('proof_evidence_status')}`",
        "",
        "## Ready Families",
        "",
    ]
    by_family = payload.get("by_family", {})
    if isinstance(by_family, dict) and by_family:
        for family, count in sorted(by_family.items()):
            lines.append(f"- `{family}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Blocked", ""])
    blocked_by_status = payload.get("blocked_by_status", {})
    if isinstance(blocked_by_status, dict) and blocked_by_status:
        for status, count in sorted(blocked_by_status.items()):
            lines.append(f"- `{status}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

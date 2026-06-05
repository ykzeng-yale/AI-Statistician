from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


STAT_CLAIM_CERTIFICATE_READINESS_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "STAT_CLAIM_CERTIFICATE_READINESS_NOT_SOURCE_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Certificate readiness rows may cite kernel-verified checker theorems, but "
    "they are not proof evidence for the source statistical claim. A source "
    "claim still needs a concrete witness, checker validation, semantic linkage, "
    "and final Lean/AXLE promotion before it can be marked proved."
)


FAMILY_TO_CHECKER_OBLIGATION = {
    "conformal_coverage_certificate": "conformal_coverage_certificate_sound",
    "randomization_variance_certificate": "randomization_variance_certificate_sound",
    "multiple_testing_threshold_certificate": "multiple_testing_threshold_certificate_sound",
    "kkt_optimality_certificate": "kkt_optimality_certificate_sound",
}


@dataclass(frozen=True)
class StatClaimCertificateReadinessRow:
    schema_version: int
    readiness_id: str
    target_id: str
    source_claim_id: str
    question_id: str
    problem_class: str
    certificate_family: str
    checker_name: str
    checker_obligation_id: str
    checker_available: bool
    checker_verified: bool
    checker_kernel_verified: bool
    checker_verifier: str
    checker_verification_strength: str
    checker_proof_evidence_status: str
    readiness_status: str
    ready_for_witness_validation: bool
    required_next_step: str
    required_gate: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    evidence_paths: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


def export_stat_claim_certificate_readiness_overlay(
    certificate_plan_dir: Path,
    checker_audit_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Overlay checker-theorem evidence onto certificate-plan targets.

    This is a routing/readiness artifact. It distinguishes targets whose
    checker family has a kernel-verified theorem from targets that still need
    checker formalization, while preserving that neither condition proves the
    source statistical claim.
    """

    errors: list[str] = []
    plan_manifest_path = certificate_plan_dir / "stat_claim_certificate_plan_manifest.json"
    plan_jsonl_path = certificate_plan_dir / "stat_claim_certificate_targets.jsonl"
    checker_manifest_path = checker_audit_dir / "stat_claim_certificate_checker_audit_manifest.json"
    plan_manifest = _read_json(plan_manifest_path, errors)
    target_rows = _read_jsonl(plan_jsonl_path, errors)
    checker_manifest = _read_json(checker_manifest_path, errors)
    checker_by_id = {
        str(row.get("obligation_id", "")): row
        for row in checker_manifest.get("checks", [])
        if isinstance(row, dict) and str(row.get("obligation_id", ""))
    }
    rows = [
        _readiness_row(
            target,
            checker_by_id=checker_by_id,
            checker_manifest_path=checker_manifest_path,
        )
        for target in target_rows
    ]
    by_status = Counter(row.readiness_status for row in rows)
    by_family = Counter(row.certificate_family for row in rows)
    payload: dict[str, object] = {
        "schema_version": STAT_CLAIM_CERTIFICATE_READINESS_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "certificate_plan_dir": str(certificate_plan_dir),
        "certificate_plan_manifest": str(plan_manifest_path),
        "certificate_plan_jsonl": str(plan_jsonl_path),
        "checker_audit_dir": str(checker_audit_dir),
        "checker_audit_manifest": str(checker_manifest_path),
        "plan_all_ok": bool(plan_manifest.get("all_ok", False)),
        "checker_all_ok": bool(checker_manifest.get("all_ok", False)),
        "checker_all_kernel_verified": bool(checker_manifest.get("all_kernel_verified", False)),
        "n_targets": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_checker_available": sum(1 for row in rows if row.checker_available),
        "n_checker_verified": sum(1 for row in rows if row.checker_verified),
        "n_checker_kernel_verified": sum(1 for row in rows if row.checker_kernel_verified),
        "n_ready_for_witness_validation": sum(1 for row in rows if row.ready_for_witness_validation),
        "n_missing_checker": by_status.get("CHECKER_NOT_AVAILABLE", 0),
        "n_non_kernel_checker": by_status.get("CHECKER_PRESENT_NOT_KERNEL_VERIFIED", 0),
        "all_ok": not errors and bool(plan_manifest.get("all_ok", False)) and all(row.ok for row in rows),
        "errors": errors,
        "by_status": dict(sorted(by_status.items())),
        "by_family": dict(sorted(by_family.items())),
        "rows": [asdict(row) for row in rows],
        "readiness_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "readiness rows do not prove source claims",
            "kernel-verified checker theorems prove only their encoded checker soundness theorem",
            "witness generation and semantic linkage remain separate gates",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "stat_claim_certificate_readiness_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_readiness.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_readiness.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _readiness_row(
    target: dict[str, Any],
    *,
    checker_by_id: dict[str, dict[str, Any]],
    checker_manifest_path: Path,
) -> StatClaimCertificateReadinessRow:
    errors: list[str] = []
    target_id = str(target.get("target_id", ""))
    family = str(target.get("certificate_family", ""))
    checker_obligation_id = FAMILY_TO_CHECKER_OBLIGATION.get(family, "")
    checker_row = checker_by_id.get(checker_obligation_id, {}) if checker_obligation_id else {}
    checker_available = bool(checker_obligation_id)
    checker_verified = bool(checker_row.get("ok", False))
    checker_kernel_verified = bool(checker_row.get("kernel_verified", False))
    if not target_id:
        errors.append("target_id missing")
    if not family:
        errors.append("certificate_family missing")
    if checker_available and not checker_row:
        errors.append(f"checker audit row missing for {checker_obligation_id}")
    if not checker_available:
        readiness_status = "CHECKER_NOT_AVAILABLE"
        ready = False
        next_step = "formalize and kernel-verify a small checker theorem for this certificate family"
        required_gate = "checker theorem passes local Lean/AXLE before witness validation is actionable"
    elif checker_kernel_verified:
        readiness_status = "READY_FOR_WITNESS_GENERATION_AND_VALIDATION"
        ready = True
        next_step = "generate a concrete witness JSON and run the kernel-verified checker against the encoded claim"
        required_gate = (
            "witness satisfies checker contract, source claim linkage is reviewed, "
            "and final claim promotion reruns Lean/AXLE evidence gates"
        )
    elif checker_verified:
        readiness_status = "CHECKER_PRESENT_NOT_KERNEL_VERIFIED"
        ready = False
        next_step = "rerun checker audit with local Lean/AXLE before witness validation"
        required_gate = "checker audit records kernel_verified=true for the checker theorem"
    else:
        readiness_status = "CHECKER_PRESENT_BUT_FAILED"
        ready = False
        next_step = "repair the checker theorem or proof body using checker-audit diagnostics"
        required_gate = "checker theorem verifies with no sorry/admit/axiom"
    evidence_paths = tuple(
        path
        for path in (
            str(checker_manifest_path) if checker_row else "",
            *[str(path) for path in target.get("evidence_paths", []) or [] if str(path)],
        )
        if path
    )
    return StatClaimCertificateReadinessRow(
        schema_version=STAT_CLAIM_CERTIFICATE_READINESS_SCHEMA_VERSION,
        readiness_id="stat_claim_certificate_readiness:" + stable_hash(
            [target_id, family, checker_obligation_id]
        )[:16],
        target_id=target_id,
        source_claim_id=str(target.get("source_claim_id", "")),
        question_id=str(target.get("question_id", "")),
        problem_class=str(target.get("problem_class", "")),
        certificate_family=family,
        checker_name=str(target.get("checker_name", "")),
        checker_obligation_id=checker_obligation_id,
        checker_available=checker_available,
        checker_verified=checker_verified,
        checker_kernel_verified=checker_kernel_verified,
        checker_verifier=str(checker_row.get("verifier", "")),
        checker_verification_strength=str(checker_row.get("verification_strength", "")),
        checker_proof_evidence_status=(
            "CHECKER_THEOREM_KERNEL_VERIFIED"
            if checker_kernel_verified
            else "CHECKER_THEOREM_NOT_KERNEL_VERIFIED"
        ),
        readiness_status=readiness_status,
        ready_for_witness_validation=ready,
        required_next_step=next_step,
        required_gate=required_gate,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        evidence_paths=evidence_paths,
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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Statistical Claim Certificate Readiness Overlay",
        "",
        f"- Certificate plan: `{payload.get('certificate_plan_manifest')}`",
        f"- Checker audit: `{payload.get('checker_audit_manifest')}`",
        f"- Targets: `{payload.get('n_ok')}/{payload.get('n_targets')}`",
        f"- Ready for witness validation: `{payload.get('n_ready_for_witness_validation')}`",
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

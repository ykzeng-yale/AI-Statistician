from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RESPONSE_PROMOTION_SCHEMA_VERSION = 1
FULL_ROUTE_CALIBRATION_STATUS = "full_route_kernel_verified"
ACCEPTED_RESPONSE_STATUS = "ACCEPTED_FULL_ROUTE_KERNEL_VERIFIED"


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchResponsePromotionRow:
    schema_version: int
    promotion_id: str
    response_validation_id: str
    prompt_packet_id: str
    execution_id: str
    application_id: str
    replay_id: str
    route_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    source_acceptance_status: str
    response_present: bool
    response_contract_ok: bool
    patched_artifact_path: str
    changed_lean_declarations: tuple[str, ...]
    replay_attempt_manifest: str
    replay_calibration_manifest: str
    replay_calibration_status: str
    kernel_verified: bool
    proof_evidence_status: str
    promotion_status: str
    promotion_ready: bool
    owner_agent: str
    action_type: str
    priority: str
    required_gate: str
    required_fields: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_response_promotion(
    formal_verifier_replay_repair_patch_response_validation_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export proof-promotion rows from validated repair patch responses.

    This stage does not mutate the claim ledger or proof bank. It separates
    accepted full-route kernel evidence from awaiting responses, ordinary patch
    proposals, and rejected/unsupported proof claims.
    """

    errors: list[str] = []
    validation_manifest_path = (
        formal_verifier_replay_repair_patch_response_validation_dir
        / "formal_verifier_replay_repair_patch_response_validation_manifest.json"
    )
    validation_payload = _read_json(validation_manifest_path, errors)
    validation_rows = [
        row for row in validation_payload.get("rows", []) if isinstance(row, dict)
    ]
    rows = [
        _promotion_row(
            row,
            validation_dir=formal_verifier_replay_repair_patch_response_validation_dir,
        )
        for row in validation_rows
    ]
    by_status = Counter(row.promotion_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RESPONSE_PROMOTION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_response_validation_dir": str(
            formal_verifier_replay_repair_patch_response_validation_dir
        ),
        "formal_verifier_replay_repair_patch_response_validation_manifest": str(
            validation_manifest_path
        ),
        "source_validation_all_ok": bool(validation_payload.get("all_ok", False)),
        "n_response_validation_rows": len(validation_rows),
        "n_promotion_rows": len(rows),
        "n_ready_for_proof_promotion": sum(1 for row in rows if row.promotion_ready),
        "n_awaiting_worker_response": by_status.get(
            "AWAITING_WORKER_RESPONSE_NO_PROMOTION",
            0,
        ),
        "n_patch_proposal_needs_replay_calibration": by_status.get(
            "PATCH_PROPOSAL_NEEDS_REPLAY_CALIBRATION",
            0,
        ),
        "n_blocked": sum(1 for row in rows if row.promotion_status.startswith("BLOCKED_")),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": (
            not errors
            and bool(validation_payload.get("all_ok", False))
            and all(row.ok for row in rows)
        ),
        "errors": errors,
        "by_promotion_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "promotion_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "promotion rows are proof-ledger update contracts, not ledger mutations",
            "awaiting responses and patch proposals are not proof evidence",
            "accepted responses are promotion-ready only when attempt and calibration manifests corroborate full-route kernel verification",
            "claim-ledger/proof-bank promotion still requires recording the evidence path and rerunning release gates",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_replay_repair_patch_response_promotion_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formal_verifier_replay_repair_patch_response_promotion.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_patch_response_promotion.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _promotion_row(
    row: dict[str, Any],
    *,
    validation_dir: Path,
) -> FormalVerifierReplayRepairPatchResponsePromotionRow:
    errors: list[str] = []
    response_validation_id = str(row.get("response_validation_id", ""))
    prompt_packet_id = str(row.get("prompt_packet_id", ""))
    execution_id = str(row.get("execution_id", ""))
    replay_id = str(row.get("replay_id", ""))
    source_acceptance_status = str(row.get("acceptance_status", ""))
    patched_artifact_path = str(row.get("patched_artifact_path", ""))
    replay_attempt_manifest = str(row.get("replay_attempt_manifest", ""))
    replay_calibration_manifest = str(row.get("replay_calibration_manifest", ""))
    replay_calibration_status = str(row.get("replay_calibration_status", ""))
    kernel_verified = bool(row.get("kernel_verified", False))
    changed_lean_declarations = _str_tuple(row.get("changed_lean_declarations", []))
    evidence_paths: tuple[str, ...] = ()

    if source_acceptance_status == "AWAITING_WORKER_RESPONSE":
        promotion_status = "AWAITING_WORKER_RESPONSE_NO_PROMOTION"
        action_type = "await_repair_worker_response"
        priority = "medium"
        required_gate = "worker returns a response matching the prompt-packet contract"
        required_fields = ("response_jsonl", "claim_status", "rerun_commands")
        ok = True
    elif source_acceptance_status == "PATCH_PROPOSAL_RECORDED_NOT_PROOF_EVIDENCE":
        promotion_status = "PATCH_PROPOSAL_NEEDS_REPLAY_CALIBRATION"
        action_type = "rerun_repaired_route_calibration"
        priority = "high"
        required_gate = (
            "rerun formal-verifier-replay-attempts and formal-verifier-replay-calibration "
            "until the patched route is full_route_kernel_verified"
        )
        required_fields = (
            "patched_artifact_path",
            "changed_lean_declarations",
            "replay_attempt_manifest",
            "replay_calibration_manifest",
        )
        ok = True
    elif source_acceptance_status == ACCEPTED_RESPONSE_STATUS:
        artifact_exists = _path_exists(patched_artifact_path, validation_dir)
        attempt_ok = _attempt_manifest_corroborates(
            replay_attempt_manifest,
            replay_id=replay_id,
            validation_dir=validation_dir,
        )
        calibration_ok = _calibration_manifest_corroborates(
            replay_calibration_manifest,
            replay_id=replay_id,
            validation_dir=validation_dir,
        )
        if not artifact_exists:
            errors.append(f"patched_artifact_path does not exist: {patched_artifact_path}")
        if not changed_lean_declarations:
            errors.append("changed_lean_declarations missing")
        if replay_calibration_status != FULL_ROUTE_CALIBRATION_STATUS:
            errors.append("replay_calibration_status is not full_route_kernel_verified")
        if not kernel_verified:
            errors.append("kernel_verified is false")
        if not attempt_ok:
            errors.append("attempt manifest does not corroborate kernel-verified replay")
        if not calibration_ok:
            errors.append("calibration manifest does not corroborate full-route kernel verification")
        if errors:
            promotion_status = "BLOCKED_EVIDENCE_MANIFEST_MISMATCH"
            action_type = "repair_response_evidence_manifest_mismatch"
            priority = "high"
            required_gate = "response evidence manifests corroborate the accepted full-route kernel claim"
            ok = False
        else:
            promotion_status = "READY_FOR_PROOF_LEDGER_PROMOTION"
            action_type = "promote_full_route_kernel_verified_repair_to_claim_ledger"
            priority = "high"
            required_gate = (
                "claim ledger records the target theorem as kernel-verified proof evidence "
                "with replay attempt and calibration manifests attached, then release gates rerun"
            )
            ok = True
            evidence_paths = _existing_paths(
                (
                    patched_artifact_path,
                    replay_attempt_manifest,
                    replay_calibration_manifest,
                ),
                validation_dir=validation_dir,
            )
        required_fields = (
            "target_theorem_name",
            "candidate_bridge_lemma_name",
            "patched_artifact_path",
            "changed_lean_declarations",
            "replay_attempt_manifest",
            "replay_calibration_manifest",
            "kernel_verified",
            "claim_ledger_update",
        )
    else:
        promotion_status = "BLOCKED_RESPONSE_VALIDATION_FAILED"
        action_type = "repair_or_reject_invalid_worker_response"
        priority = "high"
        required_gate = "response validation passes without rejected or unsupported proof claims"
        required_fields = ("response_validation_errors", "corrected_response_jsonl")
        ok = False
        if row.get("errors"):
            errors.extend(str(item) for item in row.get("errors", []) if str(item))
        else:
            errors.append(f"source acceptance status cannot be promoted: {source_acceptance_status}")

    promotion_ready = promotion_status == "READY_FOR_PROOF_LEDGER_PROMOTION"
    return FormalVerifierReplayRepairPatchResponsePromotionRow(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RESPONSE_PROMOTION_SCHEMA_VERSION,
        promotion_id=(
            "formal_verifier_replay_repair_patch_response_promotion:"
            f"{stable_hash([response_validation_id, source_acceptance_status, row])[:16]}"
        ),
        response_validation_id=response_validation_id,
        prompt_packet_id=prompt_packet_id,
        execution_id=execution_id,
        application_id=str(row.get("application_id", "")),
        replay_id=replay_id,
        route_id=str(row.get("route_id", "")),
        display_name=str(row.get("display_name", "")),
        target_theorem_name=str(row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(row.get("candidate_bridge_lemma_name", "")),
        source_acceptance_status=source_acceptance_status,
        response_present=bool(row.get("response_present", False)),
        response_contract_ok=bool(row.get("response_contract_ok", False)),
        patched_artifact_path=patched_artifact_path,
        changed_lean_declarations=changed_lean_declarations,
        replay_attempt_manifest=replay_attempt_manifest,
        replay_calibration_manifest=replay_calibration_manifest,
        replay_calibration_status=replay_calibration_status,
        kernel_verified=kernel_verified,
        proof_evidence_status=str(row.get("proof_evidence_status", "")),
        promotion_status=promotion_status,
        promotion_ready=promotion_ready,
        owner_agent="formal_verifier" if not promotion_ready else "research_coordinator",
        action_type=action_type,
        priority=priority,
        required_gate=required_gate,
        required_fields=required_fields,
        evidence_paths=evidence_paths,
        proof_evidence_boundary=_proof_evidence_boundary(promotion_ready),
        ok=ok,
        errors=tuple(errors),
    )


def _attempt_manifest_corroborates(raw: str, *, replay_id: str, validation_dir: Path) -> bool:
    payload = _read_json_silent(_resolve_path(raw, validation_dir))
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_replay_id = str(row.get("replay_id") or row.get("source_replay_id") or "")
        if replay_id and row_replay_id != replay_id:
            continue
        placeholder_refs = row.get("placeholder_references_in_candidate", [])
        if bool(row.get("kernel_verified", False)) and not placeholder_refs:
            return True
    return False


def _calibration_manifest_corroborates(raw: str, *, replay_id: str, validation_dir: Path) -> bool:
    payload = _read_json_silent(_resolve_path(raw, validation_dir))
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        if replay_id and str(row.get("replay_id", "")) != replay_id:
            continue
        if (
            str(row.get("replay_calibration_status", "")) == FULL_ROUTE_CALIBRATION_STATUS
            and bool(row.get("latest_kernel_verified", False))
            and str(row.get("full_route_proof_status", "")) == "PROVED_BY_KERNEL_REPLAY"
        ):
            return True
    return False


def _existing_paths(raw_paths: tuple[str, ...], *, validation_dir: Path) -> tuple[str, ...]:
    paths: list[str] = []
    for raw in raw_paths:
        path = _resolve_path(raw, validation_dir)
        if path.exists():
            paths.append(str(path))
    return tuple(paths)


def _path_exists(raw: str, validation_dir: Path) -> bool:
    return _resolve_path(raw, validation_dir).exists() if raw else False


def _resolve_path(raw: str, validation_dir: Path) -> Path:
    if not raw:
        return Path("__missing__")
    path = Path(raw)
    if path.exists() or path.is_absolute():
        return path
    return validation_dir / path


def _proof_evidence_boundary(promotion_ready: bool) -> str:
    if promotion_ready:
        return (
            "This row is ready for proof-ledger promotion because response validation, "
            "the replay attempt manifest, and the replay calibration manifest all "
            "corroborate full-route kernel verification."
        )
    return (
        "This row is not proof-ledger promotion evidence. Promotion requires an accepted "
        "full-route kernel-verified repair response with corroborating replay attempt "
        "and calibration manifests."
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


def _read_json_silent(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Replay Repair Patch Response Promotion",
        "",
        f"- Response validation manifest: `{payload.get('formal_verifier_replay_repair_patch_response_validation_manifest')}`",
        f"- Promotion rows: {payload.get('n_ok')}/{payload.get('n_promotion_rows')} audit-clean",
        f"- Ready for proof promotion: {payload.get('n_ready_for_proof_promotion')}",
        f"- Awaiting worker response: {payload.get('n_awaiting_worker_response')}",
        f"- Patch proposals needing replay calibration: {payload.get('n_patch_proposal_needs_replay_calibration')}",
        f"- Blocked: {payload.get('n_blocked')}",
        f"- Fingerprint: `{payload.get('promotion_fingerprint')}`",
        "",
        "Promotion rows do not mutate the proof ledger; they expose which accepted responses can be recorded as proof evidence.",
        "",
        "## Rows",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No response-validation rows were available for proof promotion.")
    else:
        for row in rows[:30]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}` ({row.get('promotion_status')}): "
                f"{row.get('candidate_bridge_lemma_name')}"
            )
            lines.append(f"  ready: {row.get('promotion_ready')}")
            lines.append(f"  action: {row.get('action_type')}")
            lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

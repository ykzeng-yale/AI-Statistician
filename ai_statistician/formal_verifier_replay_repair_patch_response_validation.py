from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RESPONSE_VALIDATION_SCHEMA_VERSION = 1
PATCH_PROPOSAL_STATUS = "PATCH_PROPOSAL_NOT_PROOF_EVIDENCE"
FULL_ROUTE_PROOF_STATUS = "FULL_ROUTE_KERNEL_VERIFIED_PROOF_EVIDENCE"
FULL_ROUTE_CALIBRATION_STATUS = "full_route_kernel_verified"


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchResponseValidationRow:
    schema_version: int
    response_validation_id: str
    prompt_packet_id: str
    execution_id: str
    application_id: str
    replay_id: str
    route_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    artifact_path: str
    response_present: bool
    response_contract_ok: bool
    patched_artifact_path: str
    changed_lean_declarations: tuple[str, ...]
    proof_body_or_bridge_patch_present: bool
    rerun_commands: tuple[str, ...]
    replay_attempt_manifest: str
    replay_calibration_manifest: str
    replay_calibration_status: str
    kernel_verified: bool
    placeholders_removed: bool
    residual_formal_gaps: tuple[str, ...]
    claim_status: str
    acceptance_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_response_validation(
    formal_verifier_replay_repair_prompt_packets_dir: Path,
    out_dir: Path | None = None,
    *,
    response_jsonl: Path | None = None,
) -> dict[str, object]:
    """Validate worker responses to FormalVerifier repair prompt packets.

    Missing response files are non-failing: they mean the prompt packets are
    still waiting for prover/RAG worker output. Present responses are audited
    against the prompt contract and may claim proof evidence only when replay
    calibration is full_route_kernel_verified with no remaining formal gaps.
    """

    errors: list[str] = []
    prompt_manifest_path = (
        formal_verifier_replay_repair_prompt_packets_dir
        / "formal_verifier_replay_repair_prompt_packets_manifest.json"
    )
    prompt_payload = _read_json(prompt_manifest_path, errors)
    packets = [row for row in prompt_payload.get("packets", []) if isinstance(row, dict)]
    response_jsonl_path = (
        response_jsonl
        if response_jsonl is not None
        else formal_verifier_replay_repair_prompt_packets_dir
        / "formal_verifier_replay_repair_patch_responses.jsonl"
    )
    responses, response_file_exists = _read_response_jsonl(response_jsonl_path, errors)
    response_by_prompt = _match_responses_to_packets(responses, packets, errors)
    rows = [
        _validation_row(
            packet,
            response=response_by_prompt.get(str(packet.get("prompt_packet_id", ""))),
            prompt_packets_dir=formal_verifier_replay_repair_prompt_packets_dir,
            response_jsonl_path=response_jsonl_path,
        )
        for packet in packets
    ]
    by_acceptance_status = Counter(row.acceptance_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RESPONSE_VALIDATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_prompt_packets_dir": str(
            formal_verifier_replay_repair_prompt_packets_dir
        ),
        "formal_verifier_replay_repair_prompt_packets_manifest": str(prompt_manifest_path),
        "response_jsonl": str(response_jsonl_path),
        "response_jsonl_exists": response_file_exists,
        "n_prompt_packets": len(packets),
        "n_responses": len(responses),
        "n_response_validation_rows": len(rows),
        "n_response_present": sum(1 for row in rows if row.response_present),
        "n_awaiting_worker_response": sum(
            1 for row in rows if row.acceptance_status == "AWAITING_WORKER_RESPONSE"
        ),
        "n_contract_ok": sum(1 for row in rows if row.response_contract_ok),
        "n_patch_proposal_not_proof": sum(
            1
            for row in rows
            if row.acceptance_status == "PATCH_PROPOSAL_RECORDED_NOT_PROOF_EVIDENCE"
        ),
        "n_accepted_full_route_kernel_verified": sum(
            1
            for row in rows
            if row.acceptance_status == "ACCEPTED_FULL_ROUTE_KERNEL_VERIFIED"
        ),
        "n_rejected": sum(1 for row in rows if row.acceptance_status.startswith("REJECTED_")),
        "n_ok": sum(1 for row in rows if row.ok),
        "by_acceptance_status": dict(sorted(by_acceptance_status.items())),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "rows": [asdict(row) for row in rows],
        "validation_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "missing repair patch responses are awaiting worker output, not proof evidence",
            "patch proposals are source-change suggestions, not theorem proof evidence",
            "kernel_verified=true is accepted only with full_route_kernel_verified calibration and no residual formal gaps",
            "replay attempt and calibration manifests must exist before a response can be accepted as proof evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_replay_repair_patch_response_validation_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formal_verifier_replay_repair_patch_response_validation.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_patch_response_validation.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _validation_row(
    packet: dict[str, Any],
    *,
    response: dict[str, Any] | None,
    prompt_packets_dir: Path,
    response_jsonl_path: Path,
) -> FormalVerifierReplayRepairPatchResponseValidationRow:
    prompt_packet_id = str(packet.get("prompt_packet_id", ""))
    execution_id = str(packet.get("execution_id", ""))
    application_id = str(packet.get("application_id", ""))
    replay_id = str(packet.get("replay_id", ""))
    route_id = str(packet.get("route_id", ""))
    display_name = str(packet.get("display_name", ""))
    target_theorem_name = str(packet.get("target_theorem_name", ""))
    candidate_bridge_lemma_name = str(packet.get("candidate_bridge_lemma_name", ""))
    artifact_path = str(packet.get("artifact_path", ""))
    if response is None:
        return FormalVerifierReplayRepairPatchResponseValidationRow(
            schema_version=(
                FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RESPONSE_VALIDATION_SCHEMA_VERSION
            ),
            response_validation_id=_validation_id(prompt_packet_id, execution_id, None),
            prompt_packet_id=prompt_packet_id,
            execution_id=execution_id,
            application_id=application_id,
            replay_id=replay_id,
            route_id=route_id,
            display_name=display_name,
            target_theorem_name=target_theorem_name,
            candidate_bridge_lemma_name=candidate_bridge_lemma_name,
            artifact_path=artifact_path,
            response_present=False,
            response_contract_ok=False,
            patched_artifact_path="",
            changed_lean_declarations=(),
            proof_body_or_bridge_patch_present=False,
            rerun_commands=(),
            replay_attempt_manifest="",
            replay_calibration_manifest="",
            replay_calibration_status="",
            kernel_verified=False,
            placeholders_removed=False,
            residual_formal_gaps=(),
            claim_status="",
            acceptance_status="AWAITING_WORKER_RESPONSE",
            proof_evidence_status="AWAITING_RESPONSE_NOT_PROOF_EVIDENCE",
            proof_evidence_boundary=(
                "No worker response has been recorded for this prompt packet. "
                "This awaiting state is not proof evidence."
            ),
            ok=True,
            errors=(),
        )

    errors: list[str] = []
    _require_matching_field(response, packet, "execution_id", errors)
    _require_matching_field(response, packet, "application_id", errors)
    _require_matching_field(response, packet, "target_theorem_name", errors)
    _require_matching_field(response, packet, "candidate_bridge_lemma_name", errors)
    required_fields = (
        "patched_artifact_path",
        "changed_lean_declarations",
        "proof_body_or_bridge_patch",
        "rerun_commands",
        "replay_attempt_manifest",
        "replay_calibration_manifest",
        "replay_calibration_status",
        "kernel_verified",
        "placeholders_removed",
        "residual_formal_gaps",
        "claim_status",
        "promotion_gate",
    )
    for field in required_fields:
        if field not in response:
            errors.append(f"{field} missing")
    changed_lean_declarations = _str_tuple(response.get("changed_lean_declarations", []))
    rerun_commands = _str_tuple(response.get("rerun_commands", []))
    residual_formal_gaps = _str_tuple(response.get("residual_formal_gaps", []))
    if "changed_lean_declarations" in response and not isinstance(
        response.get("changed_lean_declarations"), list
    ):
        errors.append("changed_lean_declarations must be a list")
    if "rerun_commands" in response and not isinstance(response.get("rerun_commands"), list):
        errors.append("rerun_commands must be a list")
    if "residual_formal_gaps" in response and not isinstance(
        response.get("residual_formal_gaps"), list
    ):
        errors.append("residual_formal_gaps must be a list")
    patched_artifact_path = str(response.get("patched_artifact_path", ""))
    proof_body_or_bridge_patch = str(response.get("proof_body_or_bridge_patch", ""))
    proof_body_or_bridge_patch_present = bool(proof_body_or_bridge_patch.strip())
    if not patched_artifact_path:
        errors.append("patched_artifact_path missing")
    if not changed_lean_declarations:
        errors.append("changed_lean_declarations empty")
    if not proof_body_or_bridge_patch_present:
        errors.append("proof_body_or_bridge_patch missing")
    if not rerun_commands:
        errors.append("rerun_commands empty")
    replay_attempt_manifest = str(response.get("replay_attempt_manifest", ""))
    replay_calibration_manifest = str(response.get("replay_calibration_manifest", ""))
    replay_calibration_status = str(response.get("replay_calibration_status", ""))
    kernel_verified = bool(response.get("kernel_verified", False))
    placeholders_removed = bool(response.get("placeholders_removed", False))
    claim_status = str(response.get("claim_status", ""))
    if claim_status not in {PATCH_PROPOSAL_STATUS, FULL_ROUTE_PROOF_STATUS}:
        errors.append(f"unsupported claim_status: {claim_status}")
    if not isinstance(response.get("kernel_verified", False), bool):
        errors.append("kernel_verified must be boolean")
    if not isinstance(response.get("placeholders_removed", False), bool):
        errors.append("placeholders_removed must be boolean")
    response_contract_ok = not errors

    attempt_manifest_exists = _manifest_exists(
        replay_attempt_manifest,
        prompt_packets_dir=prompt_packets_dir,
        response_jsonl_path=response_jsonl_path,
    )
    calibration_manifest_exists = _manifest_exists(
        replay_calibration_manifest,
        prompt_packets_dir=prompt_packets_dir,
        response_jsonl_path=response_jsonl_path,
    )
    full_evidence_ready = (
        replay_calibration_status == FULL_ROUTE_CALIBRATION_STATUS
        and kernel_verified
        and placeholders_removed
        and not residual_formal_gaps
        and attempt_manifest_exists
        and calibration_manifest_exists
    )
    response_claims_proof = (
        claim_status == FULL_ROUTE_PROOF_STATUS
        or kernel_verified
        or replay_calibration_status == FULL_ROUTE_CALIBRATION_STATUS
    )
    if response_contract_ok and response_claims_proof and not full_evidence_ready:
        if replay_calibration_status != FULL_ROUTE_CALIBRATION_STATUS:
            errors.append("proof claim requires replay_calibration_status=full_route_kernel_verified")
        if not kernel_verified:
            errors.append("proof claim requires kernel_verified=true")
        if not placeholders_removed:
            errors.append("proof claim requires placeholders_removed=true")
        if residual_formal_gaps:
            errors.append("proof claim includes residual formal gaps")
        if replay_attempt_manifest and not attempt_manifest_exists:
            errors.append(f"replay_attempt_manifest does not exist: {replay_attempt_manifest}")
        if replay_calibration_manifest and not calibration_manifest_exists:
            errors.append(
                f"replay_calibration_manifest does not exist: {replay_calibration_manifest}"
            )
        if not replay_attempt_manifest:
            errors.append("proof claim requires replay_attempt_manifest")
        if not replay_calibration_manifest:
            errors.append("proof claim requires replay_calibration_manifest")
    if not response_contract_ok:
        acceptance_status = "REJECTED_INVALID_RESPONSE_CONTRACT"
        proof_evidence_status = "INVALID_RESPONSE_NOT_PROOF_EVIDENCE"
        ok = False
    elif response_claims_proof and not full_evidence_ready:
        acceptance_status = "REJECTED_UNSUPPORTED_PROOF_CLAIM"
        proof_evidence_status = "UNSUPPORTED_PROOF_CLAIM_NOT_EVIDENCE"
        ok = False
    elif full_evidence_ready:
        acceptance_status = "ACCEPTED_FULL_ROUTE_KERNEL_VERIFIED"
        proof_evidence_status = "FULL_ROUTE_KERNEL_VERIFIED_PROOF_EVIDENCE"
        ok = True
    else:
        acceptance_status = "PATCH_PROPOSAL_RECORDED_NOT_PROOF_EVIDENCE"
        proof_evidence_status = "PATCH_PROPOSAL_NOT_PROOF_EVIDENCE"
        ok = True

    return FormalVerifierReplayRepairPatchResponseValidationRow(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RESPONSE_VALIDATION_SCHEMA_VERSION,
        response_validation_id=_validation_id(prompt_packet_id, execution_id, response),
        prompt_packet_id=prompt_packet_id,
        execution_id=execution_id,
        application_id=application_id,
        replay_id=replay_id,
        route_id=route_id,
        display_name=display_name,
        target_theorem_name=target_theorem_name,
        candidate_bridge_lemma_name=candidate_bridge_lemma_name,
        artifact_path=artifact_path,
        response_present=True,
        response_contract_ok=response_contract_ok,
        patched_artifact_path=patched_artifact_path,
        changed_lean_declarations=changed_lean_declarations,
        proof_body_or_bridge_patch_present=proof_body_or_bridge_patch_present,
        rerun_commands=rerun_commands,
        replay_attempt_manifest=replay_attempt_manifest,
        replay_calibration_manifest=replay_calibration_manifest,
        replay_calibration_status=replay_calibration_status,
        kernel_verified=kernel_verified,
        placeholders_removed=placeholders_removed,
        residual_formal_gaps=residual_formal_gaps,
        claim_status=claim_status,
        acceptance_status=acceptance_status,
        proof_evidence_status=proof_evidence_status,
        proof_evidence_boundary=_proof_evidence_boundary(acceptance_status),
        ok=ok,
        errors=tuple(errors),
    )


def _match_responses_to_packets(
    responses: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    by_prompt_id = {
        str(packet.get("prompt_packet_id", "")): packet
        for packet in packets
        if str(packet.get("prompt_packet_id", ""))
    }
    response_by_prompt: dict[str, dict[str, Any]] = {}
    for index, response in enumerate(responses, start=1):
        prompt_packet_id = str(response.get("prompt_packet_id", ""))
        if prompt_packet_id and prompt_packet_id in by_prompt_id:
            matched_prompt_id = prompt_packet_id
        else:
            matched_prompt_id = _match_by_execution(response, packets)
        if not matched_prompt_id:
            errors.append(f"response line {index} does not match any prompt packet")
            continue
        if matched_prompt_id in response_by_prompt:
            errors.append(f"duplicate response for prompt packet: {matched_prompt_id}")
            continue
        response_by_prompt[matched_prompt_id] = response
    return response_by_prompt


def _match_by_execution(response: dict[str, Any], packets: list[dict[str, Any]]) -> str:
    execution_id = str(response.get("execution_id", ""))
    application_id = str(response.get("application_id", ""))
    matches = [
        str(packet.get("prompt_packet_id", ""))
        for packet in packets
        if str(packet.get("execution_id", "")) == execution_id
        and (not application_id or str(packet.get("application_id", "")) == application_id)
    ]
    matches = [match for match in matches if match]
    return matches[0] if len(matches) == 1 else ""


def _require_matching_field(
    response: dict[str, Any],
    packet: dict[str, Any],
    field: str,
    errors: list[str],
) -> None:
    expected = str(packet.get(field, ""))
    observed = str(response.get(field, ""))
    if expected and observed != expected:
        errors.append(f"{field} mismatch: expected {expected}, got {observed}")
    if not observed:
        errors.append(f"{field} missing")


def _manifest_exists(
    raw: str,
    *,
    prompt_packets_dir: Path,
    response_jsonl_path: Path,
) -> bool:
    if not raw:
        return False
    path = Path(raw)
    if path.exists():
        return True
    if path.is_absolute():
        return False
    return (response_jsonl_path.parent / path).exists() or (prompt_packets_dir / path).exists()


def _validation_id(
    prompt_packet_id: str,
    execution_id: str,
    response: dict[str, Any] | None,
) -> str:
    return (
        "formal_verifier_replay_repair_patch_response_validation:"
        f"{stable_hash([prompt_packet_id, execution_id, response or {}])[:16]}"
    )


def _proof_evidence_boundary(acceptance_status: str) -> str:
    if acceptance_status == "ACCEPTED_FULL_ROUTE_KERNEL_VERIFIED":
        return (
            "This response is accepted as proof evidence only because the repaired replay "
            "calibration is full_route_kernel_verified, kernel_verified=true, placeholders "
            "were removed, and no residual formal gaps were reported."
        )
    return (
        "This response is not theorem proof evidence. A repair response becomes proof "
        "evidence only after full-route replay calibration reports full_route_kernel_verified "
        "with kernel_verified=true and no residual formal gaps."
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


def _read_response_jsonl(
    path: Path,
    errors: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    if not path.exists():
        return [], False
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        errors.append(f"failed to read response JSONL: {type(exc).__name__}: {exc}")
        return [], True
    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse response JSONL line {lineno}: {type(exc).__name__}: {exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"response JSONL line {lineno} is not an object")
            continue
        rows.append(payload)
    return rows, True


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Replay Repair Patch Response Validation",
        "",
        f"- Prompt packet manifest: `{payload.get('formal_verifier_replay_repair_prompt_packets_manifest')}`",
        f"- Response JSONL: `{payload.get('response_jsonl')}`",
        f"- Responses present: {payload.get('n_response_present')}/{payload.get('n_response_validation_rows')}",
        f"- Awaiting worker response: {payload.get('n_awaiting_worker_response')}",
        f"- Patch proposals recorded: {payload.get('n_patch_proposal_not_proof')}",
        f"- Accepted full-route kernel verified: {payload.get('n_accepted_full_route_kernel_verified')}",
        f"- Rejected: {payload.get('n_rejected')}",
        f"- Fingerprint: `{payload.get('validation_fingerprint')}`",
        "",
        "Patch responses are not theorem proof evidence unless full-route replay calibration is kernel verified.",
        "",
        "## Rows",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No repair prompt packets were available for response validation.")
    else:
        for row in rows[:30]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}` ({row.get('acceptance_status')}): "
                f"{row.get('candidate_bridge_lemma_name')}"
            )
            lines.append(f"  response present: {row.get('response_present')}")
            lines.append(f"  proof status: {row.get('proof_evidence_status')}")
            lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

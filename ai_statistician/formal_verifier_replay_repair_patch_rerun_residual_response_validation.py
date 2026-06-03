from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_RESPONSE_VALIDATION_SCHEMA_VERSION = 1
RESIDUAL_PATCH_PROPOSAL_STATUS = "RESIDUAL_PATCH_PROPOSAL_NOT_PROOF_EVIDENCE"
FULL_ROUTE_PROOF_STATUS = "FULL_ROUTE_KERNEL_VERIFIED_PROOF_EVIDENCE"
FULL_ROUTE_CALIBRATION_STATUS = "full_route_kernel_verified"


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchRerunResidualResponseValidationRow:
    schema_version: int
    residual_response_validation_id: str
    prompt_packet_id: str
    residual_prompt_packet_id: str
    residual_obligation_id: str
    rerun_calibration_id: str
    rerun_id: str
    rerun_attempt_id: str
    replay_id: str
    route_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    residual_gap: str
    action_class: str
    patched_artifact_path: str
    response_present: bool
    response_contract_ok: bool
    proposed_lean_artifact_path: str
    changed_lean_declarations: tuple[str, ...]
    proof_or_composition_patch_present: bool
    used_proof_bank_obligations: tuple[str, ...]
    used_local_declarations: tuple[str, ...]
    source_discovery_queries: tuple[str, ...]
    rerun_commands: tuple[str, ...]
    patch_rerun_attempt_manifest: str
    patch_rerun_calibration_manifest: str
    patch_rerun_residual_obligations_manifest: str
    patch_rerun_calibration_status: str
    kernel_verified: bool
    closed_residual_gaps: tuple[str, ...]
    remaining_residual_gaps: tuple[str, ...]
    remaining_residual_formal_gaps: tuple[str, ...]
    claim_status: str
    acceptance_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_rerun_residual_response_validation(
    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir: Path,
    out_dir: Path | None = None,
    *,
    response_jsonl: Path | None = None,
) -> dict[str, object]:
    """Validate worker responses to residual patch-rerun prompt packets."""

    errors: list[str] = []
    prompt_manifest_path = (
        formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir
        / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest.json"
    )
    prompt_payload = _read_json(prompt_manifest_path, errors)
    packets = [row for row in prompt_payload.get("packets", []) if isinstance(row, dict)]
    response_jsonl_path = (
        response_jsonl
        if response_jsonl is not None
        else formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir
        / "formal_verifier_replay_repair_patch_rerun_residual_responses.jsonl"
    )
    responses, response_file_exists = _read_response_jsonl(response_jsonl_path, errors)
    response_by_prompt = _match_responses_to_packets(responses, packets, errors)
    rows = [
        _validation_row(
            packet,
            response=response_by_prompt.get(str(packet.get("prompt_packet_id", ""))),
            prompt_packets_dir=formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir,
            response_jsonl_path=response_jsonl_path,
        )
        for packet in packets
    ]
    by_acceptance_status = Counter(row.acceptance_status for row in rows)
    by_action_class = Counter(row.action_class for row in rows)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_RESPONSE_VALIDATION_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir": str(
            formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest": str(
            prompt_manifest_path
        ),
        "response_jsonl": str(response_jsonl_path),
        "response_jsonl_exists": response_file_exists,
        "n_prompt_packets": len(packets),
        "n_responses": len(responses),
        "n_response_validation_rows": len(rows),
        "n_response_present": sum(1 for row in rows if row.response_present),
        "n_awaiting_worker_response": sum(
            1
            for row in rows
            if row.acceptance_status == "AWAITING_RESIDUAL_WORKER_RESPONSE"
        ),
        "n_contract_ok": sum(1 for row in rows if row.response_contract_ok),
        "n_residual_patch_proposal_not_proof": sum(
            1
            for row in rows
            if row.acceptance_status
            == "RESIDUAL_PATCH_PROPOSAL_RECORDED_NOT_PROOF_EVIDENCE"
        ),
        "n_source_discovery_responses": sum(
            1
            for row in rows
            if row.acceptance_status
            == "SOURCE_DISCOVERY_RESPONSE_RECORDED_NOT_PROOF_EVIDENCE"
        ),
        "n_accepted_full_route_kernel_verified": sum(
            1
            for row in rows
            if row.acceptance_status == "ACCEPTED_FULL_ROUTE_KERNEL_VERIFIED"
        ),
        "n_rejected": sum(1 for row in rows if row.acceptance_status.startswith("REJECTED_")),
        "n_ok": sum(1 for row in rows if row.ok),
        "by_acceptance_status": dict(sorted(by_acceptance_status.items())),
        "by_action_class": dict(sorted(by_action_class.items())),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "rows": [asdict(row) for row in rows],
        "validation_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "missing residual responses are awaiting worker output, not proof evidence",
            "residual patch responses are work proposals, not theorem proof evidence",
            "source-discovery responses only improve retrieval coverage; they do not close theorem gaps",
            "proof claims require full_route_kernel_verified patch-rerun calibration and no remaining residual formal gaps",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_response_validation_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_response_validation.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_response_validation.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _validation_row(
    packet: dict[str, Any],
    *,
    response: dict[str, Any] | None,
    prompt_packets_dir: Path,
    response_jsonl_path: Path,
) -> FormalVerifierReplayRepairPatchRerunResidualResponseValidationRow:
    prompt_packet_id = str(packet.get("prompt_packet_id", ""))
    residual_obligation_id = str(packet.get("residual_obligation_id", ""))
    rerun_calibration_id = str(packet.get("rerun_calibration_id", ""))
    rerun_id = str(packet.get("rerun_id", ""))
    rerun_attempt_id = str(packet.get("rerun_attempt_id", ""))
    replay_id = str(packet.get("replay_id", ""))
    route_id = str(packet.get("route_id", ""))
    display_name = str(packet.get("display_name", ""))
    target_theorem_name = str(packet.get("target_theorem_name", ""))
    candidate_bridge_lemma_name = str(packet.get("candidate_bridge_lemma_name", ""))
    residual_gap = str(packet.get("residual_gap", ""))
    action_class = str(packet.get("action_class", ""))
    patched_artifact_path = str(packet.get("patched_artifact_path", ""))
    if response is None:
        return FormalVerifierReplayRepairPatchRerunResidualResponseValidationRow(
            schema_version=(
                FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_RESPONSE_VALIDATION_SCHEMA_VERSION
            ),
            residual_response_validation_id=_validation_id(
                prompt_packet_id,
                residual_obligation_id,
                None,
            ),
            prompt_packet_id=prompt_packet_id,
            residual_prompt_packet_id=prompt_packet_id,
            residual_obligation_id=residual_obligation_id,
            rerun_calibration_id=rerun_calibration_id,
            rerun_id=rerun_id,
            rerun_attempt_id=rerun_attempt_id,
            replay_id=replay_id,
            route_id=route_id,
            display_name=display_name,
            target_theorem_name=target_theorem_name,
            candidate_bridge_lemma_name=candidate_bridge_lemma_name,
            residual_gap=residual_gap,
            action_class=action_class,
            patched_artifact_path=patched_artifact_path,
            response_present=False,
            response_contract_ok=False,
            proposed_lean_artifact_path="",
            changed_lean_declarations=(),
            proof_or_composition_patch_present=False,
            used_proof_bank_obligations=(),
            used_local_declarations=(),
            source_discovery_queries=(),
            rerun_commands=(),
            patch_rerun_attempt_manifest="",
            patch_rerun_calibration_manifest="",
            patch_rerun_residual_obligations_manifest="",
            patch_rerun_calibration_status="",
            kernel_verified=False,
            closed_residual_gaps=(),
            remaining_residual_gaps=(),
            remaining_residual_formal_gaps=(),
            claim_status="",
            acceptance_status="AWAITING_RESIDUAL_WORKER_RESPONSE",
            proof_evidence_status="AWAITING_RESPONSE_NOT_PROOF_EVIDENCE",
            proof_evidence_boundary=(
                "No residual worker response has been recorded for this prompt packet. "
                "This awaiting state is not proof evidence."
            ),
            ok=True,
            errors=(),
        )

    errors: list[str] = []
    for field in (
        "prompt_packet_id",
        "residual_obligation_id",
        "rerun_calibration_id",
        "target_theorem_name",
        "candidate_bridge_lemma_name",
        "residual_gap",
        "action_class",
    ):
        _require_matching_field(response, packet, field, errors)
    required_fields = (
        "proposed_lean_artifact_path",
        "changed_lean_declarations",
        "proof_or_composition_patch",
        "used_proof_bank_obligations",
        "used_local_declarations",
        "source_discovery_queries",
        "rerun_commands",
        "patch_rerun_attempt_manifest",
        "patch_rerun_calibration_manifest",
        "patch_rerun_calibration_status",
        "kernel_verified",
        "closed_residual_gaps",
        "remaining_residual_gaps",
        "remaining_residual_formal_gaps",
        "claim_status",
        "promotion_gate",
    )
    for field in required_fields:
        if field not in response:
            errors.append(f"{field} missing")
    changed_lean_declarations = _str_tuple(response.get("changed_lean_declarations", []))
    used_proof_bank_obligations = _str_tuple(
        response.get("used_proof_bank_obligations", [])
    )
    used_local_declarations = _str_tuple(response.get("used_local_declarations", []))
    source_discovery_queries = _str_tuple(response.get("source_discovery_queries", []))
    rerun_commands = _str_tuple(response.get("rerun_commands", []))
    closed_residual_gaps = _str_tuple(response.get("closed_residual_gaps", []))
    remaining_residual_gaps = _str_tuple(response.get("remaining_residual_gaps", []))
    remaining_residual_formal_gaps = _str_tuple(
        response.get("remaining_residual_formal_gaps", [])
    )
    for field in (
        "changed_lean_declarations",
        "used_proof_bank_obligations",
        "used_local_declarations",
        "source_discovery_queries",
        "rerun_commands",
        "closed_residual_gaps",
        "remaining_residual_gaps",
        "remaining_residual_formal_gaps",
    ):
        if field in response and not isinstance(response.get(field), list):
            errors.append(f"{field} must be a list")
    proposed_lean_artifact_path = str(response.get("proposed_lean_artifact_path", ""))
    proof_or_composition_patch = str(response.get("proof_or_composition_patch", ""))
    proof_or_composition_patch_present = bool(proof_or_composition_patch.strip())
    if action_class == "source_discovery_needed":
        if not source_discovery_queries:
            errors.append("source_discovery_queries empty for source-discovery response")
    else:
        if not proposed_lean_artifact_path:
            errors.append("proposed_lean_artifact_path missing")
        if not changed_lean_declarations:
            errors.append("changed_lean_declarations empty")
        if not proof_or_composition_patch_present:
            errors.append("proof_or_composition_patch missing")
    if not rerun_commands:
        errors.append("rerun_commands empty")
    patch_rerun_attempt_manifest = str(response.get("patch_rerun_attempt_manifest", ""))
    patch_rerun_calibration_manifest = str(
        response.get("patch_rerun_calibration_manifest", "")
    )
    patch_rerun_residual_obligations_manifest = str(
        response.get("patch_rerun_residual_obligations_manifest", "")
    )
    patch_rerun_calibration_status = str(
        response.get("patch_rerun_calibration_status", "")
    )
    kernel_verified = bool(response.get("kernel_verified", False))
    claim_status = str(response.get("claim_status", ""))
    if claim_status not in {RESIDUAL_PATCH_PROPOSAL_STATUS, FULL_ROUTE_PROOF_STATUS}:
        errors.append(f"unsupported claim_status: {claim_status}")
    if "kernel_verified" in response and not isinstance(response.get("kernel_verified"), bool):
        errors.append("kernel_verified must be boolean")
    response_contract_ok = not errors
    attempt_manifest_exists = _manifest_exists(
        patch_rerun_attempt_manifest,
        prompt_packets_dir=prompt_packets_dir,
        response_jsonl_path=response_jsonl_path,
    )
    calibration_manifest_exists = _manifest_exists(
        patch_rerun_calibration_manifest,
        prompt_packets_dir=prompt_packets_dir,
        response_jsonl_path=response_jsonl_path,
    )
    residual_manifest_exists = _manifest_exists(
        patch_rerun_residual_obligations_manifest,
        prompt_packets_dir=prompt_packets_dir,
        response_jsonl_path=response_jsonl_path,
    )
    full_evidence_ready = (
        patch_rerun_calibration_status == FULL_ROUTE_CALIBRATION_STATUS
        and kernel_verified
        and not remaining_residual_formal_gaps
        and attempt_manifest_exists
        and calibration_manifest_exists
    )
    response_claims_proof = (
        claim_status == FULL_ROUTE_PROOF_STATUS
        or kernel_verified
        or patch_rerun_calibration_status == FULL_ROUTE_CALIBRATION_STATUS
    )
    if response_contract_ok and response_claims_proof and not full_evidence_ready:
        if patch_rerun_calibration_status != FULL_ROUTE_CALIBRATION_STATUS:
            errors.append(
                "proof claim requires patch_rerun_calibration_status=full_route_kernel_verified"
            )
        if not kernel_verified:
            errors.append("proof claim requires kernel_verified=true")
        if remaining_residual_formal_gaps:
            errors.append("proof claim includes remaining residual formal gaps")
        if patch_rerun_attempt_manifest and not attempt_manifest_exists:
            errors.append(
                f"patch_rerun_attempt_manifest does not exist: {patch_rerun_attempt_manifest}"
            )
        if patch_rerun_calibration_manifest and not calibration_manifest_exists:
            errors.append(
                "patch_rerun_calibration_manifest does not exist: "
                f"{patch_rerun_calibration_manifest}"
            )
        if not patch_rerun_attempt_manifest:
            errors.append("proof claim requires patch_rerun_attempt_manifest")
        if not patch_rerun_calibration_manifest:
            errors.append("proof claim requires patch_rerun_calibration_manifest")
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
        proof_evidence_status = FULL_ROUTE_PROOF_STATUS
        ok = True
    elif action_class == "source_discovery_needed":
        acceptance_status = "SOURCE_DISCOVERY_RESPONSE_RECORDED_NOT_PROOF_EVIDENCE"
        proof_evidence_status = "SOURCE_DISCOVERY_RESPONSE_NOT_PROOF_EVIDENCE"
        ok = True
    else:
        acceptance_status = "RESIDUAL_PATCH_PROPOSAL_RECORDED_NOT_PROOF_EVIDENCE"
        proof_evidence_status = RESIDUAL_PATCH_PROPOSAL_STATUS
        ok = True
    if patch_rerun_residual_obligations_manifest and not residual_manifest_exists:
        errors.append(
            "patch_rerun_residual_obligations_manifest does not exist: "
            f"{patch_rerun_residual_obligations_manifest}"
        )
        if ok:
            ok = False
            acceptance_status = "REJECTED_INVALID_RESPONSE_CONTRACT"
            proof_evidence_status = "INVALID_RESPONSE_NOT_PROOF_EVIDENCE"

    return FormalVerifierReplayRepairPatchRerunResidualResponseValidationRow(
        schema_version=(
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_RESPONSE_VALIDATION_SCHEMA_VERSION
        ),
        residual_response_validation_id=_validation_id(
            prompt_packet_id,
            residual_obligation_id,
            response,
        ),
        prompt_packet_id=prompt_packet_id,
        residual_prompt_packet_id=prompt_packet_id,
        residual_obligation_id=residual_obligation_id,
        rerun_calibration_id=rerun_calibration_id,
        rerun_id=rerun_id,
        rerun_attempt_id=rerun_attempt_id,
        replay_id=replay_id,
        route_id=route_id,
        display_name=display_name,
        target_theorem_name=target_theorem_name,
        candidate_bridge_lemma_name=candidate_bridge_lemma_name,
        residual_gap=residual_gap,
        action_class=action_class,
        patched_artifact_path=patched_artifact_path,
        response_present=True,
        response_contract_ok=response_contract_ok,
        proposed_lean_artifact_path=proposed_lean_artifact_path,
        changed_lean_declarations=changed_lean_declarations,
        proof_or_composition_patch_present=proof_or_composition_patch_present,
        used_proof_bank_obligations=used_proof_bank_obligations,
        used_local_declarations=used_local_declarations,
        source_discovery_queries=source_discovery_queries,
        rerun_commands=rerun_commands,
        patch_rerun_attempt_manifest=patch_rerun_attempt_manifest,
        patch_rerun_calibration_manifest=patch_rerun_calibration_manifest,
        patch_rerun_residual_obligations_manifest=patch_rerun_residual_obligations_manifest,
        patch_rerun_calibration_status=patch_rerun_calibration_status,
        kernel_verified=kernel_verified,
        closed_residual_gaps=closed_residual_gaps,
        remaining_residual_gaps=remaining_residual_gaps,
        remaining_residual_formal_gaps=remaining_residual_formal_gaps,
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
            matched_prompt_id = _match_by_residual(response, packets)
        if not matched_prompt_id:
            errors.append(f"response line {index} does not match any residual prompt packet")
            continue
        if matched_prompt_id in response_by_prompt:
            errors.append(f"duplicate response for prompt packet: {matched_prompt_id}")
            continue
        response_by_prompt[matched_prompt_id] = response
    return response_by_prompt


def _match_by_residual(response: dict[str, Any], packets: list[dict[str, Any]]) -> str:
    residual_obligation_id = str(response.get("residual_obligation_id", ""))
    rerun_calibration_id = str(response.get("rerun_calibration_id", ""))
    residual_gap = str(response.get("residual_gap", ""))
    matches = [
        str(packet.get("prompt_packet_id", ""))
        for packet in packets
        if str(packet.get("residual_obligation_id", "")) == residual_obligation_id
        and (
            not rerun_calibration_id
            or str(packet.get("rerun_calibration_id", "")) == rerun_calibration_id
        )
        and (not residual_gap or str(packet.get("residual_gap", "")) == residual_gap)
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
    residual_obligation_id: str,
    response: dict[str, Any] | None,
) -> str:
    return (
        "formal_verifier_replay_repair_patch_rerun_residual_response_validation:"
        f"{stable_hash([prompt_packet_id, residual_obligation_id, response or {}])[:16]}"
    )


def _proof_evidence_boundary(acceptance_status: str) -> str:
    if acceptance_status == "ACCEPTED_FULL_ROUTE_KERNEL_VERIFIED":
        return (
            "This residual response is accepted as proof evidence only because "
            "patch-rerun calibration is full_route_kernel_verified, kernel_verified=true, "
            "and no remaining residual formal gaps were reported."
        )
    return (
        "This residual response is not theorem proof evidence. It becomes proof "
        "evidence only after patch-rerun calibration reports full_route_kernel_verified "
        "with kernel_verified=true and no remaining residual formal gaps."
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
            errors.append(
                f"failed to parse response JSONL line {lineno}: {type(exc).__name__}: {exc}"
            )
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
        "# Formal Verifier Patch Rerun Residual Response Validation",
        "",
        f"- Residual prompt packet manifest: `{payload.get('formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest')}`",
        f"- Response JSONL: `{payload.get('response_jsonl')}`",
        f"- Responses present: {payload.get('n_response_present')}/{payload.get('n_response_validation_rows')}",
        f"- Awaiting worker response: {payload.get('n_awaiting_worker_response')}",
        f"- Residual patch proposals recorded: {payload.get('n_residual_patch_proposal_not_proof')}",
        f"- Source-discovery responses: {payload.get('n_source_discovery_responses')}",
        f"- Accepted full-route kernel verified: {payload.get('n_accepted_full_route_kernel_verified')}",
        f"- Rejected: {payload.get('n_rejected')}",
        f"- Fingerprint: `{payload.get('validation_fingerprint')}`",
        "",
        "Residual responses are not theorem proof evidence unless patch-rerun calibration is kernel verified.",
        "",
        "## Rows",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No residual prompt packets were available for response validation.")
    else:
        for row in rows[:40]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
                f"({row.get('acceptance_status')}): {row.get('action_class')}"
            )
            lines.append(f"  response present: {row.get('response_present')}")
            lines.append(f"  proof status: {row.get('proof_evidence_status')}")
            lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

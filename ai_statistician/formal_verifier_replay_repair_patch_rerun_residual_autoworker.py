from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_AUTOWORKER_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchRerunResidualAutoWorkerRow:
    schema_version: int
    response_id: str
    prompt_packet_id: str
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
    action_type: str
    proposed_lean_artifact_path: str
    changed_lean_declarations: tuple[str, ...]
    used_proof_bank_obligations: tuple[str, ...]
    used_local_declarations: tuple[str, ...]
    source_discovery_queries: tuple[str, ...]
    rerun_commands: tuple[str, ...]
    remaining_residual_formal_gaps: tuple[str, ...]
    claim_status: str
    patch_rerun_calibration_status: str
    kernel_verified: bool
    worker_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    response: dict[str, object]
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_rerun_residual_autoworker(
    formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir: Path,
    out_dir: Path | None = None,
    *,
    max_responses: int = 40,
) -> dict[str, object]:
    """Generate conservative local responses for residual prompt packets.

    This deterministic bridge does not prove residual obligations. It emits
    auditable worker responses that validation can classify as patch proposals
    or source-discovery responses, with every proof claim held behind the
    patch-rerun calibration boundary.
    """

    errors: list[str] = []
    prompt_manifest_path = (
        formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir
        / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest.json"
    )
    prompt_payload = _read_json(prompt_manifest_path, errors)
    packets = [
        packet
        for packet in prompt_payload.get("packets", [])
        if isinstance(packet, dict) and bool(packet.get("ok", False))
    ][: max(0, max_responses)]
    response_out_dir = (
        out_dir
        if out_dir is not None
        else formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir
    )
    proposal_dir = response_out_dir / "residual_patch_proposals"
    rows = [
        _autoworker_row(packet, proposal_dir=proposal_dir)
        for packet in packets
    ]
    by_action_class = Counter(row.action_class for row in rows)
    by_status = Counter(row.worker_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_AUTOWORKER_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir": str(
            formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_dir
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest": str(
            prompt_manifest_path
        ),
        "max_responses": max_responses,
        "n_prompt_packets": len(prompt_payload.get("packets", []) or []),
        "n_eligible_prompt_packets": len(
            [
                packet
                for packet in prompt_payload.get("packets", [])
                if isinstance(packet, dict) and bool(packet.get("ok", False))
            ]
        ),
        "n_responses": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_residual_patch_proposals": sum(
            1
            for row in rows
            if row.worker_status == "RESIDUAL_PATCH_PROPOSAL_READY_FOR_RERUN"
        ),
        "n_source_discovery_responses": sum(
            1
            for row in rows
            if row.worker_status == "SOURCE_DISCOVERY_RESPONSE_READY_FOR_RETRIEVAL"
        ),
        "n_kernel_verified": sum(1 for row in rows if row.kernel_verified),
        "n_patch_artifacts": sum(
            1
            for row in rows
            if row.proposed_lean_artifact_path
            and Path(row.proposed_lean_artifact_path).exists()
        ),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_action_class": dict(sorted(by_action_class.items())),
        "by_worker_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "response_jsonl": str(
            response_out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_responses.jsonl"
        ),
        "residual_autoworker_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "residual autoworker responses are work proposals, not theorem proof evidence",
            "kernel_verified is always false in this deterministic local worker",
            "source-discovery responses do not close formal gaps by themselves",
            "residual proof closure still requires patch-rerun calibration with full_route_kernel_verified",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_autoworker_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_responses.jsonl"
        ).write_text(
            "\n".join(json.dumps(row.response, sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_autoworker.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _autoworker_row(
    packet: dict[str, Any],
    *,
    proposal_dir: Path,
) -> FormalVerifierReplayRepairPatchRerunResidualAutoWorkerRow:
    errors: list[str] = []
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
    action_type = str(packet.get("action_type", ""))
    contract = dict(packet.get("expected_output_contract", {}) or {})
    rerun_commands = _str_tuple(packet.get("command_plan", []) or contract.get("rerun_commands", []))
    exact_obligation = str(packet.get("exact_proof_bank_obligation", ""))
    proof_bank_obligations = tuple(
        dict.fromkeys(
            _str_tuple([exact_obligation])
            + _str_tuple(packet.get("proof_bank_bridge_obligations", []))
        )
    )
    local_declarations = _str_tuple(packet.get("local_candidate_declarations", []))
    if not prompt_packet_id:
        errors.append("prompt_packet_id missing")
    if not residual_obligation_id:
        errors.append("residual_obligation_id missing")
    if not rerun_calibration_id:
        errors.append("rerun_calibration_id missing")
    if not residual_gap:
        errors.append("residual_gap missing")
    if not action_class:
        errors.append("action_class missing")
    if not rerun_commands:
        errors.append("rerun_commands missing")

    source_discovery_queries = _source_discovery_queries(packet)
    if action_class == "source_discovery_needed":
        proposed_artifact_path = ""
        changed_declarations: tuple[str, ...] = ()
        proof_or_composition_patch = ""
        worker_status = "SOURCE_DISCOVERY_RESPONSE_READY_FOR_RETRIEVAL"
        if not source_discovery_queries:
            errors.append("source discovery queries missing")
    else:
        proposal_dir.mkdir(parents=True, exist_ok=True)
        declaration_name = _safe_decl_name(
            f"{candidate_bridge_lemma_name}_{residual_gap}_residual_patch_plan"
        )
        proposed_artifact = proposal_dir / f"{_safe_file_stem(display_name + '_' + residual_gap)}.lean"
        proof_or_composition_patch = _proposal_text(
            declaration_name=declaration_name,
            target_theorem_name=target_theorem_name,
            candidate_bridge_lemma_name=candidate_bridge_lemma_name,
            residual_gap=residual_gap,
            action_class=action_class,
            proof_bank_obligations=proof_bank_obligations,
            local_declarations=local_declarations,
        )
        proposed_artifact.write_text(_proposal_source(proof_or_composition_patch), encoding="utf-8")
        proposed_artifact_path = str(proposed_artifact)
        changed_declarations = (declaration_name,)
        worker_status = "RESIDUAL_PATCH_PROPOSAL_READY_FOR_RERUN"
        if not proposed_artifact.exists():
            errors.append("proposed artifact was not written")
    response: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_AUTOWORKER_SCHEMA_VERSION
        ),
        "task": "formal_verifier_replay_repair_patch_rerun_residual_obligation",
        "prompt_packet_id": prompt_packet_id,
        "residual_prompt_packet_id": prompt_packet_id,
        "residual_obligation_id": residual_obligation_id,
        "rerun_calibration_id": rerun_calibration_id,
        "rerun_id": rerun_id,
        "rerun_attempt_id": rerun_attempt_id,
        "target_theorem_name": target_theorem_name,
        "candidate_bridge_lemma_name": candidate_bridge_lemma_name,
        "residual_gap": residual_gap,
        "action_class": action_class,
        "proposed_lean_artifact_path": proposed_artifact_path,
        "changed_lean_declarations": list(changed_declarations),
        "proof_or_composition_patch": proof_or_composition_patch,
        "used_proof_bank_obligations": list(proof_bank_obligations),
        "used_local_declarations": list(local_declarations),
        "source_discovery_queries": list(source_discovery_queries),
        "rerun_commands": list(rerun_commands),
        "patch_rerun_attempt_manifest": "",
        "patch_rerun_calibration_manifest": "",
        "patch_rerun_residual_obligations_manifest": "",
        "patch_rerun_calibration_status": "UNRUN_AFTER_RESIDUAL_PATCH",
        "kernel_verified": False,
        "closed_residual_gaps": [],
        "remaining_residual_gaps": [residual_gap] if residual_gap else [],
        "remaining_residual_formal_gaps": [residual_gap] if residual_gap else [],
        "claim_status": "RESIDUAL_PATCH_PROPOSAL_NOT_PROOF_EVIDENCE",
        "promotion_gate": (
            "accept only after patch-rerun attempts and calibration report "
            "full_route_kernel_verified with no remaining residual formal gaps"
        ),
    }
    ok = not errors
    if not ok and worker_status == "SOURCE_DISCOVERY_RESPONSE_READY_FOR_RETRIEVAL":
        worker_status = "SOURCE_DISCOVERY_RESPONSE_BLOCKED"
    elif not ok:
        worker_status = "RESIDUAL_PATCH_PROPOSAL_BLOCKED"
    return FormalVerifierReplayRepairPatchRerunResidualAutoWorkerRow(
        schema_version=(
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_AUTOWORKER_SCHEMA_VERSION
        ),
        response_id=(
            "formal_verifier_replay_repair_patch_rerun_residual_autoworker:"
            f"{stable_hash([prompt_packet_id, residual_obligation_id, response])[:16]}"
        ),
        prompt_packet_id=prompt_packet_id,
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
        action_type=action_type,
        proposed_lean_artifact_path=proposed_artifact_path,
        changed_lean_declarations=changed_declarations,
        used_proof_bank_obligations=proof_bank_obligations,
        used_local_declarations=local_declarations,
        source_discovery_queries=source_discovery_queries,
        rerun_commands=rerun_commands,
        remaining_residual_formal_gaps=(residual_gap,) if residual_gap else (),
        claim_status="RESIDUAL_PATCH_PROPOSAL_NOT_PROOF_EVIDENCE",
        patch_rerun_calibration_status="UNRUN_AFTER_RESIDUAL_PATCH",
        kernel_verified=False,
        worker_status=worker_status,
        proof_evidence_status="RESIDUAL_PATCH_PROPOSAL_NOT_PROOF_EVIDENCE",
        proof_evidence_boundary=(
            "This residual autoworker response is not theorem proof evidence. "
            "It remains a proposal until patch-rerun calibration reports "
            "full_route_kernel_verified with no remaining residual formal gaps."
        ),
        response=response,
        ok=ok,
        errors=tuple(errors),
    )


def _source_discovery_queries(packet: dict[str, Any]) -> tuple[str, ...]:
    residual_gap = str(packet.get("residual_gap", ""))
    target = str(packet.get("target_theorem_name", ""))
    bridge = str(packet.get("candidate_bridge_lemma_name", ""))
    candidates = list(_str_tuple(packet.get("external_candidate_declarations", [])))[:4]
    candidates.extend(_str_tuple(packet.get("local_candidate_declarations", []))[:4])
    queries = [
        " ".join(part for part in (residual_gap, target, bridge) if part),
        " ".join(part for part in (residual_gap, "Mathlib StatInference Lean proof") if part),
    ]
    if candidates:
        queries.append(" ".join([residual_gap, *candidates]))
    return tuple(dict.fromkeys(query for query in queries if query.strip()))


def _proposal_text(
    *,
    declaration_name: str,
    target_theorem_name: str,
    candidate_bridge_lemma_name: str,
    residual_gap: str,
    action_class: str,
    proof_bank_obligations: tuple[str, ...],
    local_declarations: tuple[str, ...],
) -> str:
    proof_bank = ", ".join(proof_bank_obligations) or "none"
    local = ", ".join(local_declarations) or "none"
    return "\n".join(
        [
            "/- AUTOGENERATED RESIDUAL PATCH PROPOSAL ONLY.",
            "This declaration records a route-composition plan. It is not theorem proof evidence.",
            f"Target theorem: {target_theorem_name}",
            f"Candidate bridge lemma: {candidate_bridge_lemma_name}",
            f"Residual gap: {residual_gap}",
            f"Action class: {action_class}",
            f"Proof-bank obligations to reuse: {proof_bank}",
            f"Local candidate declarations: {local}",
            "-/",
            f"def {declaration_name} : String :=",
            '  "RESIDUAL_PATCH_PROPOSAL_NOT_PROOF_EVIDENCE: rerun patch calibration"',
        ]
    )


def _proposal_source(proposal_text: str) -> str:
    return f"import Mathlib\n\n{proposal_text}\n"


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


def _safe_decl_name(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not safe or safe[0].isdigit():
        safe = f"residual_patch_{safe}"
    return safe[:160]


def _safe_file_stem(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return safe[:120] or "residual_patch"


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Patch Rerun Residual Autoworker",
        "",
        f"- Residual prompt packet manifest: `{payload.get('formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest')}`",
        f"- Responses: {payload.get('n_ok')}/{payload.get('n_responses')} audit-clean",
        f"- Patch proposals: {payload.get('n_residual_patch_proposals')}",
        f"- Source-discovery responses: {payload.get('n_source_discovery_responses')}",
        f"- Kernel verified: {payload.get('n_kernel_verified')}",
        f"- Response JSONL: `{payload.get('response_jsonl')}`",
        f"- Fingerprint: `{payload.get('residual_autoworker_fingerprint')}`",
        "",
        "Residual autoworker responses are work proposals, not theorem proof evidence.",
        "",
        "## Rows",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No residual prompt packets were available for autoworker responses.")
    else:
        for row in rows[:40]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
                f"({row.get('worker_status')}): {row.get('action_class')}"
            )
            lines.append(f"  artifact: `{row.get('proposed_lean_artifact_path')}`")
            lines.append(f"  proof status: {row.get('proof_evidence_status')}")
            lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

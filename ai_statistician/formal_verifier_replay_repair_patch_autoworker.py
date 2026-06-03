from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_AUTOWORKER_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchAutoWorkerRow:
    schema_version: int
    response_id: str
    prompt_packet_id: str
    execution_id: str
    application_id: str
    replay_id: str
    route_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    patched_artifact_path: str
    changed_lean_declarations: tuple[str, ...]
    rerun_commands: tuple[str, ...]
    residual_formal_gaps: tuple[str, ...]
    claim_status: str
    replay_calibration_status: str
    kernel_verified: bool
    placeholders_removed: bool
    worker_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    response: dict[str, object]
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_autoworker(
    formal_verifier_replay_repair_prompt_packets_dir: Path,
    out_dir: Path | None = None,
    *,
    max_responses: int = 20,
) -> dict[str, object]:
    """Generate conservative local repair patch responses from prompt packets.

    This deterministic worker is a bridge from prompt packets to response
    validation. It does not claim proof success. It writes auditable patch
    proposals that must be replayed and calibrated before any proof-ledger
    promotion is possible.
    """

    errors: list[str] = []
    prompt_manifest_path = (
        formal_verifier_replay_repair_prompt_packets_dir
        / "formal_verifier_replay_repair_prompt_packets_manifest.json"
    )
    prompt_payload = _read_json(prompt_manifest_path, errors)
    packets = [
        packet
        for packet in prompt_payload.get("packets", [])
        if isinstance(packet, dict) and bool(packet.get("ok", False))
    ][: max(0, max_responses)]
    response_out_dir = out_dir if out_dir is not None else formal_verifier_replay_repair_prompt_packets_dir
    patch_dir = response_out_dir / "patched_artifacts"
    rows = [
        _autoworker_row(
            packet,
            prompt_packets_dir=formal_verifier_replay_repair_prompt_packets_dir,
            patch_dir=patch_dir,
        )
        for packet in packets
    ]
    by_status = Counter(row.worker_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_AUTOWORKER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_prompt_packets_dir": str(
            formal_verifier_replay_repair_prompt_packets_dir
        ),
        "formal_verifier_replay_repair_prompt_packets_manifest": str(prompt_manifest_path),
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
        "n_patch_proposals": sum(
            1 for row in rows if row.claim_status == "PATCH_PROPOSAL_NOT_PROOF_EVIDENCE"
        ),
        "n_kernel_verified": sum(1 for row in rows if row.kernel_verified),
        "n_patch_artifacts": sum(1 for row in rows if Path(row.patched_artifact_path).exists()),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_worker_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "response_jsonl": (
            str(response_out_dir / "formal_verifier_replay_repair_patch_responses.jsonl")
        ),
        "patch_autoworker_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "autoworker responses are patch proposals, not theorem proof evidence",
            "kernel_verified is always false in this deterministic local worker",
            "patched artifacts must be rerun through formal-verifier replay attempts and calibration",
            "proof-ledger promotion still requires full_route_kernel_verified calibration",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        patch_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_verifier_replay_repair_patch_autoworker_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_patch_responses.jsonl").write_text(
            "\n".join(json.dumps(row.response, sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_patch_autoworker.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _autoworker_row(
    packet: dict[str, Any],
    *,
    prompt_packets_dir: Path,
    patch_dir: Path,
) -> FormalVerifierReplayRepairPatchAutoWorkerRow:
    errors: list[str] = []
    prompt_packet_id = str(packet.get("prompt_packet_id", ""))
    execution_id = str(packet.get("execution_id", ""))
    application_id = str(packet.get("application_id", ""))
    replay_id = str(packet.get("replay_id", ""))
    route_id = str(packet.get("route_id", ""))
    display_name = str(packet.get("display_name", ""))
    target_theorem_name = str(packet.get("target_theorem_name", ""))
    candidate_bridge_lemma_name = str(packet.get("candidate_bridge_lemma_name", ""))
    command_plan = _str_tuple(
        packet.get("command_plan", [])
        or dict(packet.get("expected_output_contract", {}) or {}).get("rerun_commands", [])
    )
    required_primitives = _str_tuple(packet.get("required_primitives", []))
    subclaim_obligations = _str_tuple(packet.get("subclaim_replay_obligations", []))
    residual_formal_gaps = tuple(dict.fromkeys(required_primitives + subclaim_obligations))
    declaration_name = _safe_decl_name(f"{candidate_bridge_lemma_name}_repair_patch_plan")
    scaffold_source = _scaffold_source(packet, prompt_packets_dir)
    if not scaffold_source.strip():
        errors.append("prompt packet has no scaffold source or readable artifact")
    if not command_plan:
        errors.append("prompt packet has no rerun commands")
    if not candidate_bridge_lemma_name:
        errors.append("candidate_bridge_lemma_name missing")
    patch_dir.mkdir(parents=True, exist_ok=True)
    patched_artifact = patch_dir / f"{_safe_file_stem(display_name or prompt_packet_id)}.lean"
    patch_text = _patch_text(
        declaration_name=declaration_name,
        target_theorem_name=target_theorem_name,
        candidate_bridge_lemma_name=candidate_bridge_lemma_name,
        residual_formal_gaps=residual_formal_gaps,
    )
    patched_source = _patched_source(scaffold_source, patch_text)
    patched_artifact.write_text(patched_source, encoding="utf-8")
    placeholders_removed = "h_frontier_missing" not in patched_source
    response: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_AUTOWORKER_SCHEMA_VERSION,
        "task": "formal_verifier_replay_repair_patch",
        "prompt_packet_id": prompt_packet_id,
        "execution_id": execution_id,
        "application_id": application_id,
        "target_theorem_name": target_theorem_name,
        "candidate_bridge_lemma_name": candidate_bridge_lemma_name,
        "patched_artifact_path": str(patched_artifact),
        "changed_lean_declarations": [declaration_name],
        "proof_body_or_bridge_patch": patch_text,
        "rerun_commands": list(command_plan),
        "replay_attempt_manifest": "",
        "replay_calibration_manifest": "",
        "replay_calibration_status": "UNRUN_AFTER_PATCH",
        "kernel_verified": False,
        "placeholders_removed": placeholders_removed,
        "residual_formal_gaps": list(residual_formal_gaps),
        "claim_status": "PATCH_PROPOSAL_NOT_PROOF_EVIDENCE",
        "promotion_gate": (
            "accept only after formal-verifier-replay-attempts and "
            "formal-verifier-replay-calibration report full_route_kernel_verified"
        ),
    }
    ok = not errors and patched_artifact.exists() and bool(command_plan)
    return FormalVerifierReplayRepairPatchAutoWorkerRow(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_AUTOWORKER_SCHEMA_VERSION,
        response_id=(
            "formal_verifier_replay_repair_patch_autoworker:"
            f"{stable_hash([prompt_packet_id, response])[:16]}"
        ),
        prompt_packet_id=prompt_packet_id,
        execution_id=execution_id,
        application_id=application_id,
        replay_id=replay_id,
        route_id=route_id,
        display_name=display_name,
        target_theorem_name=target_theorem_name,
        candidate_bridge_lemma_name=candidate_bridge_lemma_name,
        patched_artifact_path=str(patched_artifact),
        changed_lean_declarations=(declaration_name,),
        rerun_commands=command_plan,
        residual_formal_gaps=residual_formal_gaps,
        claim_status="PATCH_PROPOSAL_NOT_PROOF_EVIDENCE",
        replay_calibration_status="UNRUN_AFTER_PATCH",
        kernel_verified=False,
        placeholders_removed=placeholders_removed,
        worker_status="PATCH_PROPOSAL_READY_FOR_REPLAY" if ok else "PATCH_PROPOSAL_BLOCKED",
        proof_evidence_status="PATCH_PROPOSAL_NOT_PROOF_EVIDENCE",
        proof_evidence_boundary=(
            "This autoworker response is a patch proposal only. It is not theorem "
            "proof evidence until the patched route is replayed and calibration "
            "reports full_route_kernel_verified with kernel_verified=true."
        ),
        response=response,
        ok=ok,
        errors=tuple(errors),
    )


def _patch_text(
    *,
    declaration_name: str,
    target_theorem_name: str,
    candidate_bridge_lemma_name: str,
    residual_formal_gaps: tuple[str, ...],
) -> str:
    gaps = ", ".join(residual_formal_gaps) if residual_formal_gaps else "route proof not replayed"
    return "\n".join(
        [
            "/- AUTOGENERATED PATCH PROPOSAL ONLY.",
            "This declaration records the next replay plan. It is not theorem proof evidence.",
            f"Target theorem: {target_theorem_name}",
            f"Candidate bridge lemma: {candidate_bridge_lemma_name}",
            f"Residual formal gaps before replay calibration: {gaps}",
            "-/",
            f"def {declaration_name} : String :=",
            '  "PATCH_PROPOSAL_NOT_PROOF_EVIDENCE: rerun replay attempts and calibration"',
        ]
    )


def _patched_source(scaffold_source: str, patch_text: str) -> str:
    source = scaffold_source.rstrip()
    if source:
        return f"{source}\n\n{patch_text}\n"
    return f"import Mathlib\n\n{patch_text}\n"


def _scaffold_source(packet: dict[str, Any], prompt_packets_dir: Path) -> str:
    source = str(packet.get("lean_repair_source_not_verified", ""))
    if source.strip():
        return source
    artifact_path = Path(str(packet.get("artifact_path", "")))
    candidates = [artifact_path]
    if not artifact_path.is_absolute():
        candidates.append(prompt_packets_dir / artifact_path)
    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate.read_text(encoding="utf-8")
        except Exception:
            continue
    return ""


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
        safe = f"repair_{safe}"
    return safe


def _safe_file_stem(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return safe[:120] or "repair_patch"


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# AI Statistical Theory Lab Formal Verifier Repair Patch Autoworker",
        "",
        f"- Prompt packet directory: `{payload.get('formal_verifier_replay_repair_prompt_packets_dir')}`",
        f"- Responses: {payload.get('n_ok')}/{payload.get('n_responses')} generated",
        f"- Patch proposals: {payload.get('n_patch_proposals')}",
        f"- Kernel verified: {payload.get('n_kernel_verified')}",
        "",
        "Autoworker responses are patch proposals only. They are not proof evidence",
        "until the patched route is replayed and calibrated as full-route kernel verified.",
        "",
        "## Responses",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No patch responses generated.")
        return "\n".join(lines) + "\n"
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### {row.get('display_name') or row.get('prompt_packet_id')}",
                "",
                f"- Status: `{row.get('worker_status')}`",
                f"- Target theorem: `{row.get('target_theorem_name')}`",
                f"- Candidate bridge: `{row.get('candidate_bridge_lemma_name')}`",
                f"- Patched artifact: `{row.get('patched_artifact_path')}`",
                f"- Residual formal gaps: `{len(row.get('residual_formal_gaps') or [])}`",
                f"- Boundary: {row.get('proof_evidence_boundary')}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"

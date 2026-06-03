from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PROMPT_PACKET_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairPromptPacket:
    schema_version: int
    prompt_packet_id: str
    execution_id: str
    execution_priority_rank: int
    application_id: str
    validation_id: str
    packet_id: str
    replay_id: str
    route_id: str
    task_id: str
    theorem_goal_id: str
    display_name: str
    execution_status: str
    application_mode: str
    repair_class: str
    priority_score: int
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    artifact_path: str
    local_lean_compiled: bool
    placeholder_free: bool
    required_primitives: tuple[str, ...]
    subclaim_replay_obligations: tuple[str, ...]
    retrieval_hit_obligations: tuple[str, ...]
    related_proof_obligations: tuple[str, ...]
    route_specific_repair_steps: tuple[str, ...]
    command_plan: tuple[str, ...]
    acceptance_gate: str
    source_formal_statement: str
    failed_proof_body: str
    proof_body_template_not_verified: str
    lean_repair_source_not_verified: str
    prompt: str
    expected_output_contract: dict[str, object]
    forbidden_claims: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_prompt_packets(
    formal_verifier_replay_repair_execution_queue_dir: Path,
    formal_verifier_replay_repair_application_dir: Path,
    out_dir: Path | None = None,
    *,
    max_packets: int = 20,
) -> dict[str, object]:
    """Export self-contained prover/RAG prompts for ready repair work orders."""

    errors: list[str] = []
    execution_manifest_path = (
        formal_verifier_replay_repair_execution_queue_dir
        / "formal_verifier_replay_repair_execution_queue_manifest.json"
    )
    application_manifest_path = (
        formal_verifier_replay_repair_application_dir
        / "formal_verifier_replay_repair_application_manifest.json"
    )
    execution_payload = _read_json(execution_manifest_path, errors)
    application_payload = _read_json(application_manifest_path, errors)
    tasks_by_application = {
        str(row.get("application_id", "")): row
        for row in application_payload.get("tasks", [])
        if isinstance(row, dict) and str(row.get("application_id", ""))
    }
    queue_rows = [
        row
        for row in execution_payload.get("queue", [])
        if isinstance(row, dict) and str(row.get("execution_status", "")).startswith("READY_FOR_REPAIR_PATCH")
    ][: max(0, max_packets)]
    packets = [
        _prompt_packet(row, task=tasks_by_application.get(str(row.get("application_id", "")), {}))
        for row in queue_rows
    ]
    by_status = Counter(packet.execution_status for packet in packets)
    by_mode = Counter(packet.application_mode for packet in packets)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_PROMPT_PACKET_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_execution_queue_dir": str(
            formal_verifier_replay_repair_execution_queue_dir
        ),
        "formal_verifier_replay_repair_execution_queue_manifest": str(execution_manifest_path),
        "formal_verifier_replay_repair_application_dir": str(
            formal_verifier_replay_repair_application_dir
        ),
        "formal_verifier_replay_repair_application_manifest": str(application_manifest_path),
        "max_packets": max_packets,
        "n_execution_queue_items": len(execution_payload.get("queue", []) or []),
        "n_ready_execution_queue_items": len(
            [
                row
                for row in execution_payload.get("queue", [])
                if isinstance(row, dict)
                and str(row.get("execution_status", "")).startswith("READY_FOR_REPAIR_PATCH")
            ]
        ),
        "n_prompt_packets": len(packets),
        "n_ok": sum(1 for packet in packets if packet.ok),
        "n_with_scaffold_source": sum(
            1 for packet in packets if bool(packet.lean_repair_source_not_verified)
        ),
        "n_with_command_plan": sum(1 for packet in packets if bool(packet.command_plan)),
        "n_with_output_contract": sum(
            1 for packet in packets if bool(packet.expected_output_contract)
        ),
        "n_local_lean_compiled_scaffold": sum(1 for packet in packets if packet.local_lean_compiled),
        "all_ok": not errors and all(packet.ok for packet in packets),
        "errors": errors,
        "by_execution_status": dict(sorted(by_status.items())),
        "by_application_mode": dict(sorted(by_mode.items())),
        "packets": [asdict(packet) for packet in packets],
        "prompt_packet_fingerprint": stable_hash([asdict(packet) for packet in packets]),
        "limitations": [
            "repair prompt packets are instructions for a prover/RAG worker, not proof evidence",
            "a returned patch is not proof evidence until formal-verifier replay and calibration pass",
            "workers must not claim theorem closure unless replay_calibration_status is full_route_kernel_verified",
            "candidate bridge lemma names are work targets, not declarations known to exist",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_verifier_replay_repair_prompt_packets_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_prompt_packets.jsonl").write_text(
            "\n".join(json.dumps(asdict(packet), sort_keys=True) for packet in packets)
            + ("\n" if packets else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_prompt_packets.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _prompt_packet(
    queue_row: dict[str, Any],
    *,
    task: dict[str, Any],
) -> FormalVerifierReplayRepairPromptPacket:
    errors: list[str] = []
    application_id = str(queue_row.get("application_id", ""))
    if not task:
        errors.append("matching repair application task missing")
    prompt = _prompt(queue_row, task)
    contract = _expected_output_contract(queue_row)
    forbidden_claims = (
        "do not claim the target theorem is proved before replay calibration",
        "do not mark kernel_verified=true without AXLE/local Lean evidence",
        "do not leave h_frontier_missing placeholders in the repaired route",
        "do not treat retrieval hits or scaffold compilation as theorem proof evidence",
    )
    if not prompt:
        errors.append("prompt missing")
    if not contract:
        errors.append("expected output contract missing")
    if not _str_tuple(queue_row.get("command_plan", [])):
        errors.append("command_plan missing")
    if not str(task.get("lean_repair_source_not_verified", "")):
        errors.append("lean repair scaffold source missing")
    if not str(queue_row.get("execution_status", "")).startswith("READY_FOR_REPAIR_PATCH"):
        errors.append("queue row is not ready for repair patch")
    prompt_packet_id = (
        "formal_verifier_replay_repair_prompt_packet:"
        f"{stable_hash([queue_row.get('execution_id', ''), application_id, prompt])[:16]}"
    )
    return FormalVerifierReplayRepairPromptPacket(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_PROMPT_PACKET_SCHEMA_VERSION,
        prompt_packet_id=prompt_packet_id,
        execution_id=str(queue_row.get("execution_id", "")),
        execution_priority_rank=_safe_int(queue_row.get("execution_priority_rank", 0)),
        application_id=application_id,
        validation_id=str(queue_row.get("validation_id", "")),
        packet_id=str(queue_row.get("packet_id", "")),
        replay_id=str(queue_row.get("replay_id", "")),
        route_id=str(queue_row.get("route_id", "")),
        task_id=str(queue_row.get("task_id", "")),
        theorem_goal_id=str(queue_row.get("theorem_goal_id", "")),
        display_name=str(queue_row.get("display_name", "")),
        execution_status=str(queue_row.get("execution_status", "")),
        application_mode=str(queue_row.get("application_mode", "")),
        repair_class=str(queue_row.get("repair_class", "")),
        priority_score=_safe_int(queue_row.get("priority_score", 0)),
        target_theorem_name=str(queue_row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(queue_row.get("candidate_bridge_lemma_name", "")),
        artifact_path=str(queue_row.get("artifact_path", "")),
        local_lean_compiled=bool(queue_row.get("local_lean_compiled", False)),
        placeholder_free=bool(queue_row.get("placeholder_free", False)),
        required_primitives=_str_tuple(queue_row.get("required_primitives", [])),
        subclaim_replay_obligations=_str_tuple(queue_row.get("subclaim_replay_obligations", [])),
        retrieval_hit_obligations=_str_tuple(queue_row.get("retrieval_hit_obligations", [])),
        related_proof_obligations=_str_tuple(queue_row.get("related_proof_obligations", [])),
        route_specific_repair_steps=_str_tuple(queue_row.get("route_specific_repair_steps", [])),
        command_plan=_str_tuple(queue_row.get("command_plan", [])),
        acceptance_gate=str(queue_row.get("acceptance_gate", "")),
        source_formal_statement=str(task.get("source_formal_statement", "")),
        failed_proof_body=str(task.get("failed_proof_body", "")),
        proof_body_template_not_verified=str(task.get("proof_body_template_not_verified", "")),
        lean_repair_source_not_verified=str(task.get("lean_repair_source_not_verified", "")),
        prompt=prompt,
        expected_output_contract=contract,
        forbidden_claims=forbidden_claims,
        proof_evidence_status="PROMPT_PACKET_NOT_PROOF_EVIDENCE",
        proof_evidence_boundary=(
            "This prompt packet is not proof evidence. It asks a worker to patch a "
            "repair scaffold and rerun verification; theorem evidence starts only "
            "when the repaired replay calibration is full_route_kernel_verified."
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _prompt(queue_row: dict[str, Any], task: dict[str, Any]) -> str:
    commands = "\n".join(f"- {item}" for item in _str_tuple(queue_row.get("command_plan", [])))
    subclaims = "\n".join(
        f"- {item}" for item in _str_tuple(queue_row.get("subclaim_replay_obligations", []))
    ) or "- none"
    retrieval_hits = "\n".join(
        f"- {item}" for item in _str_tuple(queue_row.get("retrieval_hit_obligations", []))
    ) or "- none"
    repair_steps = "\n".join(
        f"- {item}" for item in _str_tuple(queue_row.get("route_specific_repair_steps", []))
    ) or "- patch the scaffold, then rerun replay calibration"
    return "\n".join(
        [
            "You are the FormalVerifier repair worker for an AI Statistical Theory Lab replay target.",
            "Patch the Lean repair scaffold for the route below. Do not claim the theorem is proved.",
            "",
            f"Execution id: {queue_row.get('execution_id', '')}",
            f"Priority rank: {queue_row.get('execution_priority_rank', '')}",
            f"Route: {queue_row.get('display_name', '')}",
            f"Target theorem: {queue_row.get('target_theorem_name', '')}",
            f"Candidate bridge lemma: {queue_row.get('candidate_bridge_lemma_name', '')}",
            f"Artifact path: {queue_row.get('artifact_path', '')}",
            f"Execution status: {queue_row.get('execution_status', '')}",
            f"Acceptance gate: {queue_row.get('acceptance_gate', '')}",
            "",
            "Subclaim replay obligations:",
            subclaims,
            "",
            "Retrieval-hit obligations:",
            retrieval_hits,
            "",
            "Route-specific repair steps:",
            repair_steps,
            "",
            "Rerun commands after patching:",
            commands,
            "",
            "Current repair scaffold, not proof evidence:",
            "```lean",
            str(task.get("lean_repair_source_not_verified", "")).strip(),
            "```",
            "",
            "Return a JSON object matching the expected_output_contract. Keep any remaining formal gap explicit.",
        ]
    )


def _expected_output_contract(queue_row: dict[str, Any]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "task": "formal_verifier_replay_repair_patch",
        "execution_id": str(queue_row.get("execution_id", "")),
        "application_id": str(queue_row.get("application_id", "")),
        "target_theorem_name": str(queue_row.get("target_theorem_name", "")),
        "candidate_bridge_lemma_name": str(queue_row.get("candidate_bridge_lemma_name", "")),
        "patched_artifact_path": str(queue_row.get("artifact_path", "")),
        "changed_lean_declarations": [],
        "proof_body_or_bridge_patch": "",
        "rerun_commands": list(_str_tuple(queue_row.get("command_plan", []))),
        "replay_attempt_manifest": "",
        "replay_calibration_manifest": "",
        "replay_calibration_status": "UNRUN_AFTER_PATCH",
        "kernel_verified": False,
        "placeholders_removed": False,
        "residual_formal_gaps": [],
        "claim_status": "PATCH_PROPOSAL_NOT_PROOF_EVIDENCE",
        "promotion_gate": "accept only if replay_calibration_status is full_route_kernel_verified and no h_frontier_missing placeholder remains",
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


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Replay Repair Prompt Packets",
        "",
        f"- Execution queue manifest: `{payload.get('formal_verifier_replay_repair_execution_queue_manifest')}`",
        f"- Application manifest: `{payload.get('formal_verifier_replay_repair_application_manifest')}`",
        f"- Prompt packets: {payload.get('n_ok')}/{payload.get('n_prompt_packets')} ready",
        f"- Scaffold sources included: {payload.get('n_with_scaffold_source')}",
        f"- Command plans included: {payload.get('n_with_command_plan')}",
        f"- Fingerprint: `{payload.get('prompt_packet_fingerprint')}`",
        "",
        "Prompt packets are prover/RAG worker instructions, not theorem proof evidence.",
        "",
        "## Packets",
        "",
    ]
    packets = payload.get("packets", [])
    if not isinstance(packets, list) or not packets:
        lines.append("No ready repair prompt packets were exported.")
    else:
        for packet in packets[:30]:
            if not isinstance(packet, dict):
                continue
            lines.append(
                f"- #{packet.get('execution_priority_rank')} `{packet.get('display_name')}` "
                f"({packet.get('execution_status')}): {packet.get('candidate_bridge_lemma_name')}"
            )
            lines.append(f"  artifact: `{packet.get('artifact_path')}`")
            lines.append(f"  claim status: {packet.get('proof_evidence_status')}")
            lines.append(f"  boundary: {packet.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

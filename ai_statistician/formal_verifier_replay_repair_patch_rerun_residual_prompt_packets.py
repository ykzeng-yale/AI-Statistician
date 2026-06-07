from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_PROMPT_PACKET_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchRerunResidualPromptPacket:
    schema_version: int
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
    patched_artifact_path: str
    patched_artifact_readable: bool
    patched_artifact_excerpt: str
    patch_rerun_calibration_status: str
    residual_gap: str
    residual_kind: str
    source_support_classification: str
    action_class: str
    action_type: str
    proof_bank_action_id: str
    priority: str
    priority_rank: int
    exact_proof_bank_obligation: str
    proof_bank_bridge_obligations: tuple[str, ...]
    local_candidate_declarations: tuple[str, ...]
    external_candidate_declarations: tuple[str, ...]
    expected_premises: tuple[str, ...]
    required_gate: str
    next_action: str
    command_plan: tuple[str, ...]
    prompt: str
    expected_output_contract: dict[str, object]
    forbidden_claims: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_rerun_residual_prompt_packets(
    formal_verifier_replay_repair_patch_rerun_residual_obligations_dir: Path,
    out_dir: Path | None = None,
    *,
    max_packets: int = 40,
) -> dict[str, object]:
    """Export self-contained prover/RAG prompts for residual patch-rerun blockers."""

    errors: list[str] = []
    residual_manifest_path = (
        formal_verifier_replay_repair_patch_rerun_residual_obligations_dir
        / "formal_verifier_replay_repair_patch_rerun_residual_obligations_manifest.json"
    )
    residual_payload = _read_json(residual_manifest_path, errors)
    residual_rows = [
        row for row in residual_payload.get("rows", []) if isinstance(row, dict)
    ]
    selected_rows = [
        row
        for _, row in sorted(
            enumerate(residual_rows),
            key=lambda item: (
                _safe_int(item[1].get("priority_rank", 9)),
                _action_rank(str(item[1].get("action_class", ""))),
                str(item[1].get("display_name", "")),
                item[0],
            ),
        )
    ][: max(0, max_packets)]
    packets = [
        _prompt_packet(
            row,
            residual_dir=formal_verifier_replay_repair_patch_rerun_residual_obligations_dir,
        )
        for row in selected_rows
    ]
    by_action_class = Counter(packet.action_class for packet in packets)
    by_support = Counter(packet.source_support_classification for packet in packets)
    by_priority = Counter(packet.priority for packet in packets)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_PROMPT_PACKET_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_rerun_residual_obligations_dir": str(
            formal_verifier_replay_repair_patch_rerun_residual_obligations_dir
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_obligations_manifest": str(
            residual_manifest_path
        ),
        "max_packets": max_packets,
        "n_residual_obligation_rows": len(residual_rows),
        "n_prompt_packets": len(packets),
        "n_ok": sum(1 for packet in packets if packet.ok),
        "n_with_patched_artifact_context": sum(
            1 for packet in packets if packet.patched_artifact_readable
        ),
        "n_with_output_contract": sum(
            1 for packet in packets if bool(packet.expected_output_contract)
        ),
        "n_exact_reuse_packets": by_action_class.get(
            "reuse_exact_proof_bank_obligation",
            0,
        ),
        "n_bridge_chain_packets": by_action_class.get("compose_existing_bridge_chain", 0),
        "n_minimal_wrapper_packets": by_action_class.get("add_minimal_wrapper", 0),
        "n_design_bridge_packets": by_action_class.get("design_bridge_lemma", 0),
        "n_source_discovery_packets": by_action_class.get("source_discovery_needed", 0),
        "all_ok": not errors and all(packet.ok for packet in packets),
        "errors": errors,
        "by_action_class": dict(sorted(by_action_class.items())),
        "by_source_support_classification": dict(sorted(by_support.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "packets": [asdict(packet) for packet in packets],
        "prompt_packet_fingerprint": stable_hash([asdict(packet) for packet in packets]),
        "limitations": [
            "residual prompt packets are prover/RAG instructions, not proof evidence",
            "exact proof-bank reuse still requires route composition and rerun calibration",
            "workers must not claim proof success without full_route_kernel_verified patch-rerun calibration",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(packet), sort_keys=True) for packet in packets)
            + ("\n" if packets else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_prompt_packets.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _prompt_packet(
    row: dict[str, Any],
    *,
    residual_dir: Path,
) -> FormalVerifierReplayRepairPatchRerunResidualPromptPacket:
    errors: list[str] = []
    residual_obligation_id = str(row.get("residual_obligation_id", ""))
    residual_gap = str(row.get("residual_gap", ""))
    action_class = str(row.get("action_class", ""))
    patched_artifact_path = _resolve_artifact_path(
        str(row.get("patched_artifact_path", "")),
        residual_dir,
    )
    patched_source = ""
    patched_readable = False
    if patched_artifact_path.exists():
        try:
            patched_source = patched_artifact_path.read_text(encoding="utf-8")
            patched_readable = True
        except Exception as exc:
            errors.append(f"failed to read patched artifact: {type(exc).__name__}: {exc}")
    else:
        errors.append(f"patched artifact missing: {patched_artifact_path}")
    if not residual_obligation_id:
        errors.append("residual_obligation_id missing")
    if not residual_gap:
        errors.append("residual_gap missing")
    if not action_class:
        errors.append("action_class missing")
    packet_id = (
        "formal_verifier_replay_repair_patch_rerun_residual_prompt_packet:"
        f"{stable_hash([residual_obligation_id, residual_gap, action_class, patched_artifact_path])[:16]}"
    )
    command_plan = _command_plan(row)
    contract = _expected_output_contract(row, packet_id=packet_id, command_plan=command_plan)
    prompt = _prompt(row, patched_source, prompt_packet_id=packet_id, command_plan=command_plan, contract=contract)
    if not prompt:
        errors.append("prompt missing")
    if not contract:
        errors.append("expected output contract missing")
    if not command_plan:
        errors.append("command_plan missing")
    return FormalVerifierReplayRepairPatchRerunResidualPromptPacket(
        schema_version=(
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_PROMPT_PACKET_SCHEMA_VERSION
        ),
        prompt_packet_id=packet_id,
        residual_prompt_packet_id=packet_id,
        residual_obligation_id=residual_obligation_id,
        rerun_calibration_id=str(row.get("rerun_calibration_id", "")),
        rerun_id=str(row.get("rerun_id", "")),
        rerun_attempt_id=str(row.get("rerun_attempt_id", "")),
        replay_id=str(row.get("replay_id", "")),
        route_id=str(row.get("route_id", "")),
        display_name=str(row.get("display_name", "")),
        target_theorem_name=str(row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(row.get("candidate_bridge_lemma_name", "")),
        patched_artifact_path=str(patched_artifact_path),
        patched_artifact_readable=patched_readable,
        patched_artifact_excerpt=_patched_excerpt(patched_source),
        patch_rerun_calibration_status=str(
            row.get("patch_rerun_calibration_status", "")
        ),
        residual_gap=residual_gap,
        residual_kind=str(row.get("residual_kind", "")),
        source_support_classification=str(row.get("source_support_classification", "")),
        action_class=action_class,
        action_type=str(row.get("action_type", "")),
        proof_bank_action_id=str(row.get("proof_bank_action_id", "")),
        priority=str(row.get("priority", "")),
        priority_rank=_safe_int(row.get("priority_rank", 9)),
        exact_proof_bank_obligation=str(row.get("exact_proof_bank_obligation", "")),
        proof_bank_bridge_obligations=_str_tuple(row.get("proof_bank_bridge_obligations", [])),
        local_candidate_declarations=_str_tuple(row.get("local_candidate_declarations", [])),
        external_candidate_declarations=_str_tuple(
            row.get("external_candidate_declarations", [])
        ),
        expected_premises=_str_tuple(row.get("expected_premises", [])),
        required_gate=str(row.get("required_gate", "")),
        next_action=str(row.get("next_action", "")),
        command_plan=command_plan,
        prompt=prompt,
        expected_output_contract=contract,
        forbidden_claims=(
            "do not claim the route theorem is proved before patch-rerun calibration",
            "do not mark kernel_verified=true without AXLE/local Lean evidence",
            "do not treat proof-bank reuse, retrieval hits, or source discovery as theorem proof evidence",
            "do not remove residual gaps from the response unless they are closed by a verified composition or proof",
        ),
        proof_evidence_status="RESIDUAL_PROMPT_PACKET_NOT_PROOF_EVIDENCE",
        proof_evidence_boundary=(
            "This residual prompt packet is a prover/RAG instruction, not proof "
            "evidence. It becomes relevant to proof promotion only after a "
            "non-placeholder proof or route composition passes AXLE/local Lean "
            "and patch-rerun calibration reports full_route_kernel_verified."
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _prompt(
    row: dict[str, Any],
    patched_source: str,
    *,
    prompt_packet_id: str,
    command_plan: tuple[str, ...],
    contract: dict[str, object],
) -> str:
    proof_bank = _bullet_list(_str_tuple(row.get("proof_bank_bridge_obligations", [])))
    local_candidates = _bullet_list(_str_tuple(row.get("local_candidate_declarations", [])))
    external_candidates = _bullet_list(_str_tuple(row.get("external_candidate_declarations", [])))
    premises = _bullet_list(_str_tuple(row.get("expected_premises", [])))
    commands = _bullet_list(command_plan)
    source_excerpt = _patched_excerpt(patched_source)
    return "\n".join(
        [
            "You are the FormalVerifier residual-obligation worker for an AI Statistical Theory Lab patch rerun.",
            "Close or reduce the specific residual gap below. Do not claim the full route is proved.",
            "",
            f"Prompt packet id: {prompt_packet_id}",
            f"Residual obligation id: {row.get('residual_obligation_id', '')}",
            f"Rerun calibration id: {row.get('rerun_calibration_id', '')}",
            f"Rerun id: {row.get('rerun_id', '')}",
            f"Rerun attempt id: {row.get('rerun_attempt_id', '')}",
            f"Route: {row.get('display_name', '')}",
            f"Target theorem: {row.get('target_theorem_name', '')}",
            f"Candidate bridge lemma: {row.get('candidate_bridge_lemma_name', '')}",
            f"Patched artifact path: {row.get('patched_artifact_path', '')}",
            f"Patch rerun calibration status: {row.get('patch_rerun_calibration_status', '')}",
            f"Residual gap: {row.get('residual_gap', '')}",
            f"Residual kind: {row.get('residual_kind', '')}",
            f"Action class: {row.get('action_class', '')}",
            f"Action type: {row.get('action_type', '')}",
            f"Proof-bank action id: {row.get('proof_bank_action_id', '')}",
            f"Source support: {row.get('source_support_classification', '')}",
            f"Required gate: {row.get('required_gate', '')}",
            f"Next action: {row.get('next_action', '')}",
            "",
            "Exact proof-bank obligation:",
            f"- {row.get('exact_proof_bank_obligation', '') or 'none'}",
            "",
            "Bridge/proof-bank obligations:",
            proof_bank,
            "",
            "Local candidate declarations:",
            local_candidates,
            "",
            "External candidate declarations:",
            external_candidates,
            "",
            "Expected premises:",
            premises,
            "",
            "Rerun/promotion commands after patching:",
            commands,
            "",
            "Patched artifact context, not proof evidence:",
            "```lean",
            source_excerpt,
            "```",
            "",
            "expected_output_contract:",
            "```json",
            json.dumps(contract, indent=2, sort_keys=True),
            "```",
            "",
            "Return a JSON object matching expected_output_contract. Keep all unclosed residual gaps explicit.",
        ]
    )


def _expected_output_contract(
    row: dict[str, Any],
    *,
    packet_id: str,
    command_plan: tuple[str, ...],
) -> dict[str, object]:
    action_class = str(row.get("action_class", ""))
    residual_gap = str(row.get("residual_gap", ""))
    base: dict[str, object] = {
        "schema_version": 1,
        "task": "formal_verifier_replay_repair_patch_rerun_residual_obligation",
        "prompt_packet_id": packet_id,
        "residual_prompt_packet_id": packet_id,
        "residual_obligation_id": str(row.get("residual_obligation_id", "")),
        "rerun_calibration_id": str(row.get("rerun_calibration_id", "")),
        "rerun_id": str(row.get("rerun_id", "")),
        "rerun_attempt_id": str(row.get("rerun_attempt_id", "")),
        "replay_id": str(row.get("replay_id", "")),
        "route_id": str(row.get("route_id", "")),
        "target_theorem_name": str(row.get("target_theorem_name", "")),
        "candidate_bridge_lemma_name": str(row.get("candidate_bridge_lemma_name", "")),
        "residual_gap": residual_gap,
        "residual_kind": str(row.get("residual_kind", "")),
        "action_class": action_class,
        "action_type": str(row.get("action_type", "")),
        "required_output_mode": _required_output_mode(action_class),
        "patched_artifact_path": str(row.get("patched_artifact_path", "")),
        "proposed_lean_artifact_path": "",
        "changed_lean_declarations": [],
        "used_proof_bank_obligations": [],
        "used_local_declarations": [],
        "proof_or_composition_patch": "",
        "source_discovery_queries": [],
        "rerun_commands": list(command_plan),
        "patch_rerun_attempt_manifest": "",
        "patch_rerun_calibration_manifest": "",
        "patch_rerun_residual_obligations_manifest": "",
        "patch_rerun_calibration_status": "UNRUN_AFTER_RESIDUAL_PATCH",
        "kernel_verified": False,
        "closed_residual_gaps": [],
        "remaining_residual_gaps": [residual_gap] if residual_gap else [],
        "remaining_residual_formal_gaps": [residual_gap] if residual_gap else [],
        "claim_status": "RESIDUAL_PATCH_PROPOSAL_NOT_PROOF_EVIDENCE",
        "promotion_gate": "accept only if patch_rerun_calibration_status is full_route_kernel_verified and no residual formal gaps remain",
    }
    if action_class == "reuse_exact_proof_bank_obligation":
        base["expected_strategy"] = "compose exact verified proof-bank obligation into route"
        base["required_existing_obligation_id"] = str(
            row.get("exact_proof_bank_obligation", "")
        )
    elif action_class == "compose_existing_bridge_chain":
        base["expected_strategy"] = "compose verified bridge-chain obligations into route"
        base["required_bridge_obligations"] = list(
            _str_tuple(row.get("proof_bank_bridge_obligations", []))
        )
    elif action_class == "source_discovery_needed":
        base["expected_strategy"] = "expand retrieval/source coverage before proof patch"
        base["required_source_discovery"] = True
    else:
        base["expected_strategy"] = "produce the smallest verified proof/library patch for this residual gap"
    return base


def _command_plan(row: dict[str, Any]) -> tuple[str, ...]:
    artifact = str(row.get("patched_artifact_path", "")) or "<patched-artifact>"
    return (
        f"edit {artifact} to close only residual gap `{row.get('residual_gap', '')}`",
        "python3 -m ai_statistician.cli formal-verifier-replay-repair-patch-rerun-attempts --formal-verifier-replay-repair-patch-rerun-queue-dir <queue-dir> --lean-project <lean-project> --out <attempt-out>",
        "python3 -m ai_statistician.cli formal-verifier-replay-repair-patch-rerun-calibration --formal-verifier-replay-repair-patch-rerun-queue-dir <queue-dir> --formal-verifier-replay-repair-patch-rerun-attempt-dir <attempt-out> --out <calibration-out>",
        "python3 -m ai_statistician.cli formal-verifier-replay-repair-patch-rerun-residual-obligations --formal-verifier-replay-repair-patch-rerun-calibration-dir <calibration-out> --primitive-source-coverage-dir <coverage-dir> --proof-bank-actions-dir <proof-bank-actions-dir> --out <residual-obligations-out>",
    )


def _required_output_mode(action_class: str) -> str:
    return {
        "reuse_exact_proof_bank_obligation": "route_composition_against_existing_verified_obligation",
        "compose_existing_bridge_chain": "route_composition_against_existing_verified_bridge_chain",
        "add_minimal_wrapper": "minimal_wrapper_proof_or_composition_patch",
        "design_bridge_lemma": "new_bridge_lemma_proof_patch",
        "formalize_assumption_interface": "assumption_interface_formalization_patch",
        "design_from_first_principles": "first_principles_lean_primitive_patch",
        "port_external_source": "external_source_port_patch",
        "source_discovery_needed": "source_discovery_report_before_proof_patch",
    }.get(action_class, "inspect_and_patch_residual_gap")


def _resolve_artifact_path(raw: str, residual_dir: Path) -> Path:
    if not raw:
        return Path("__missing__")
    path = Path(raw)
    if path.is_absolute() or path.exists():
        return path
    for base in (residual_dir, residual_dir.parent, residual_dir.parent.parent):
        candidate = base / path
        if candidate.exists():
            return candidate
    return path


def _patched_excerpt(source: str, limit: int = 12000) -> str:
    stripped = source.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[:limit] + "\n/- ... patched artifact excerpt truncated ... -/"


def _bullet_list(items: tuple[str, ...]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _action_rank(action_class: str) -> int:
    return {
        "reuse_exact_proof_bank_obligation": 0,
        "compose_existing_bridge_chain": 1,
        "add_minimal_wrapper": 2,
        "design_bridge_lemma": 3,
        "source_discovery_needed": 4,
    }.get(action_class, 9)


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
        "# Formal Verifier Patch Rerun Residual Prompt Packets",
        "",
        f"- Residual obligations: `{payload.get('formal_verifier_replay_repair_patch_rerun_residual_obligations_manifest')}`",
        f"- Prompt packets: {payload.get('n_ok')}/{payload.get('n_prompt_packets')} ready",
        f"- Patched artifact context included: {payload.get('n_with_patched_artifact_context')}",
        f"- Exact reuse packets: {payload.get('n_exact_reuse_packets')}",
        f"- Bridge-chain packets: {payload.get('n_bridge_chain_packets')}",
        f"- Source-discovery packets: {payload.get('n_source_discovery_packets')}",
        "",
        "Residual prompt packets are prover/RAG instructions, not theorem proof evidence.",
        "",
        "## Packets",
        "",
    ]
    packets = payload.get("packets", [])
    if not isinstance(packets, list) or not packets:
        lines.append("No residual prompt packets were exported.")
    else:
        for packet in packets[:40]:
            if not isinstance(packet, dict):
                continue
            lines.append(
                f"- `{packet.get('display_name')}` -> `{packet.get('residual_gap')}` "
                f"({packet.get('action_class')})"
            )
            lines.append(f"  gate: {packet.get('required_gate')}")
            lines.append(f"  boundary: {packet.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

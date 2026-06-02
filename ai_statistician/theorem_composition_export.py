from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


THEOREM_COMPOSITION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class TheoremCompositionPacket:
    schema_version: int
    packet_id: str
    source_claim_id: str
    question_id: str
    problem_class: str
    status: str
    statement: str
    required_primitives: tuple[str, ...]
    exact_proof_bank_obligations: tuple[str, ...]
    unresolved_primitives: tuple[str, ...]
    formal_source_hits: tuple[str, ...]
    composition_steps: tuple[str, ...]
    required_gate: str
    proof_evidence_boundary: str
    evidence_paths: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


def export_theorem_composition_packets(
    claim_ledger_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export theorem-composition packets from exact proof-bank reuse rows.

    These packets are coordination artifacts. They do not prove a frontier
    theorem. They tell the ResearchCoordinator/ProofEngineer which exact
    kernel-verified proof-bank obligations can be inserted into a formal-gap
    theorem skeleton and which primitives remain unresolved.
    """

    errors: list[str] = []
    manifest_path = claim_ledger_dir / "claim_ledger_manifest.json"
    rows_path = claim_ledger_dir / "claim_ledger.jsonl"
    manifest = _read_json(manifest_path, errors)
    ledger_rows = _read_jsonl(rows_path, errors)
    packets = tuple(_packet_from_ledger_row(row) for row in ledger_rows if _has_exact_reuse(row))
    by_status = Counter(packet.status for packet in packets)
    payload: dict[str, object] = {
        "schema_version": THEOREM_COMPOSITION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_ledger_dir": str(claim_ledger_dir),
        "claim_ledger_manifest": str(manifest_path),
        "claim_ledger_jsonl": str(rows_path),
        "ledger_claims": manifest.get("n_claims", len(ledger_rows)),
        "ledger_all_ok": manifest.get("all_ok", False),
        "n_packets": len(packets),
        "n_ok": sum(1 for packet in packets if packet.ok),
        "n_exact_proof_bank_links": sum(len(packet.exact_proof_bank_obligations) for packet in packets),
        "n_unresolved_primitives": sum(len(packet.unresolved_primitives) for packet in packets),
        "n_packets_with_unresolved_primitives": sum(1 for packet in packets if packet.unresolved_primitives),
        "n_ready_for_exact_reuse_composition": by_status.get("EXACT_REUSE_READY_FOR_COMPOSITION", 0),
        "by_status": dict(sorted(by_status.items())),
        "all_ok": not errors and bool(manifest.get("all_ok", True)) and all(packet.ok for packet in packets),
        "errors": errors,
        "packets": [asdict(packet) for packet in packets],
        "packet_fingerprint": stable_hash([asdict(packet) for packet in packets]),
        "limitations": [
            "Theorem-composition packets are not Lean proof evidence.",
            "Exact proof-bank obligations are verified subclaims only; the enclosing frontier theorem remains a FORMAL_GAP.",
            "Completion requires a non-placeholder composed theorem proof accepted by AXLE/local Lean verify_proof.",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "theorem_composition_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "theorem_composition_packets.jsonl").write_text(
            "\n".join(json.dumps(asdict(packet), sort_keys=True) for packet in packets)
            + ("\n" if packets else ""),
            encoding="utf-8",
        )
        (out_dir / "theorem_composition.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _has_exact_reuse(row: dict[str, Any]) -> bool:
    return (
        isinstance(row, dict)
        and row.get("status") == "FORMAL_GAP"
        and bool(row.get("exact_proof_bank_reuse_obligations"))
    )


def _packet_from_ledger_row(row: dict[str, Any]) -> TheoremCompositionPacket:
    errors: list[str] = []
    required_primitives = tuple(
        str(item) for item in row.get("required_primitives", []) or [] if str(item)
    )
    exact_obligations = tuple(
        str(item) for item in row.get("exact_proof_bank_reuse_obligations", []) or [] if str(item)
    )
    unresolved = tuple(
        primitive for primitive in required_primitives if primitive not in set(exact_obligations)
    )
    evidence_paths = tuple(str(path) for path in row.get("evidence_paths", []) or [] if str(path))
    formal_source_hits = tuple(str(item) for item in row.get("formal_source_hits", []) or [] if str(item))
    if not required_primitives:
        errors.append("required_primitives missing")
    if not exact_obligations:
        errors.append("exact_proof_bank_reuse_obligations missing")
    if not evidence_paths:
        errors.append("evidence_paths missing")
    status = (
        "PARTIAL_EXACT_REUSE_READY"
        if unresolved
        else "EXACT_REUSE_READY_FOR_COMPOSITION"
    )
    source_claim_id = str(row.get("claim_id", ""))
    return TheoremCompositionPacket(
        schema_version=THEOREM_COMPOSITION_SCHEMA_VERSION,
        packet_id=f"theorem_composition:{stable_hash([source_claim_id, exact_obligations, unresolved])[:16]}",
        source_claim_id=source_claim_id,
        question_id=str(row.get("question_id", "")),
        problem_class=str(row.get("problem_class", "")),
        status=status,
        statement=str(row.get("statement", "")),
        required_primitives=required_primitives,
        exact_proof_bank_obligations=exact_obligations,
        unresolved_primitives=unresolved,
        formal_source_hits=formal_source_hits,
        composition_steps=(
            "reuse exact proof-bank obligations already verified by the proof-bank audit",
            "keep unresolved primitives as explicit formal-gap assumptions or develop new proof-bank obligations",
            "replace h_frontier_missing placeholders only after all required primitives and the final composition proof are available",
            "run AXLE/local Lean verify_proof on the non-placeholder composed theorem",
        ),
        required_gate=(
            "non-placeholder theorem composition passes AXLE/local Lean verify_proof; "
            "until then the source claim remains FORMAL_GAP"
        ),
        proof_evidence_boundary=(
            "Exact proof-bank obligations are proof evidence for their registered subclaims only. "
            "This packet is a composition plan, not proof evidence for the full theorem."
        ),
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
        "# Theorem Composition Packets",
        "",
        f"- Claim ledger: `{payload.get('claim_ledger_manifest')}`",
        f"- Packets: {payload.get('n_ok')}/{payload.get('n_packets')} audit-clean",
        f"- Exact proof-bank links: {payload.get('n_exact_proof_bank_links')}",
        f"- Unresolved primitives across packets: {payload.get('n_unresolved_primitives')}",
        "",
        "These packets are theorem-composition work plans, not Lean proof evidence.",
        "",
        "## Packets",
        "",
    ]
    packets = payload.get("packets", [])
    if not isinstance(packets, list) or not packets:
        lines.append("No exact proof-bank reuse packets were exported.")
    else:
        for row in packets[:30]:
            if not isinstance(row, dict):
                continue
            lines.extend(
                [
                    f"### `{row.get('packet_id')}`",
                    "",
                    f"- Source claim: `{row.get('source_claim_id')}`",
                    f"- Status: `{row.get('status')}`",
                    f"- Exact obligations: {', '.join(f'`{item}`' for item in row.get('exact_proof_bank_obligations', [])) or 'none'}",
                    f"- Unresolved primitives: {', '.join(f'`{item}`' for item in row.get('unresolved_primitives', [])) or 'none'}",
                    f"- Required gate: {row.get('required_gate')}",
                    "",
                ]
            )
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

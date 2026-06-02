from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


PROOF_BANK_ACTION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProofBankActionRow:
    schema_version: int
    action_id: str
    source_proposal_id: str
    primitive: str
    source_gap_ids: tuple[str, ...]
    source_task_ids: tuple[str, ...]
    owner_agent: str
    action_class: str
    action_type: str
    priority: str
    priority_rank: int
    priority_score: int
    bridge_readiness: str
    action: str
    required_gate: str
    required_fields: tuple[str, ...]
    expected_premises: tuple[str, ...]
    bridge_candidate_obligations: tuple[str, ...]
    candidate_declarations: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_proof_bank_actions(
    proof_bank_expansion_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export ranked proof-bank expansion work items from lemma proposals.

    This is the machine-facing queue for the FormalVerifier/ProofEngineer.
    Rows are task contracts only: they are not proof evidence, and they cannot
    be promoted until the required AXLE/local Lean verification gate passes.
    """

    errors: list[str] = []
    manifest_path = proof_bank_expansion_dir / "proof_bank_expansion_manifest.json"
    proposals_path = proof_bank_expansion_dir / "lemma_proposals.jsonl"
    manifest = _read_json(manifest_path, errors)
    proposals = _read_jsonl(proposals_path, errors)
    actions = _actions_from_proposals(proposals)
    by_action_class = Counter(row.action_class for row in actions)
    by_priority = Counter(row.priority for row in actions)
    by_owner = Counter(row.owner_agent for row in actions)
    payload: dict[str, object] = {
        "schema_version": PROOF_BANK_ACTION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_bank_expansion_dir": str(proof_bank_expansion_dir),
        "proof_bank_expansion_manifest": str(manifest_path),
        "lemma_proposals_jsonl": str(proposals_path),
        "expansion_all_ok": bool(manifest.get("all_ok", False)),
        "expansion_candidates": int(manifest.get("n_candidates", len(proposals)) or 0),
        "n_actions": len(actions),
        "n_ok": sum(1 for row in actions if row.ok),
        "all_ok": not errors and bool(manifest.get("all_ok", False)) and all(row.ok for row in actions),
        "errors": errors,
        "by_action_class": dict(sorted(by_action_class.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_owner": dict(sorted(by_owner.items())),
        "n_compose_existing_bridge_chain": by_action_class.get("compose_existing_bridge_chain", 0),
        "n_add_minimal_wrapper": by_action_class.get("add_minimal_wrapper", 0),
        "n_design_bridge_lemma": by_action_class.get("design_bridge_lemma", 0),
        "n_design_from_first_principles": by_action_class.get("design_from_first_principles", 0),
        "actions": [asdict(row) for row in actions],
        "action_fingerprint": stable_hash([asdict(row) for row in actions]),
        "limitations": [
            "proof-bank action rows are task contracts, not Lean proof evidence",
            "retrieved bridge chains and local declarations are premise-selection evidence only",
            "promotion requires a non-placeholder proof body accepted by AXLE/local Lean verify_proof",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "proof_bank_action_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "proof_bank_actions.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in actions)
            + ("\n" if actions else ""),
            encoding="utf-8",
        )
        (out_dir / "proof_bank_actions.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _actions_from_proposals(proposals: list[dict[str, Any]]) -> list[ProofBankActionRow]:
    rows = [_action_from_proposal(row) for row in proposals if isinstance(row, dict)]
    return sorted(rows, key=lambda row: (-row.priority_score, row.action_class, row.primitive, row.action_id))


def _action_from_proposal(row: dict[str, Any]) -> ProofBankActionRow:
    primitive = str(row.get("primitive", ""))
    action_class = str(row.get("action_class", ""))
    priority_score = int(row.get("priority_score", 0) or 0)
    source_proposal_id = str(row.get("proposal_id", ""))
    errors: list[str] = []
    if not source_proposal_id:
        errors.append("missing proposal_id")
    if not primitive:
        errors.append("missing primitive")
    if action_class not in {
        "compose_existing_bridge_chain",
        "add_minimal_wrapper",
        "design_bridge_lemma",
        "design_from_first_principles",
    }:
        errors.append(f"unknown action_class={action_class}")
    action_type, action, required_gate, required_fields = _contract_for_action_class(action_class)
    priority = _priority_label(action_class, priority_score)
    return ProofBankActionRow(
        schema_version=PROOF_BANK_ACTION_SCHEMA_VERSION,
        action_id=f"proof_bank_action:{source_proposal_id or stable_hash(row)[:12]}",
        source_proposal_id=source_proposal_id,
        primitive=primitive,
        source_gap_ids=tuple(str(item) for item in row.get("source_gap_ids", []) or [] if str(item)),
        source_task_ids=tuple(str(item) for item in row.get("source_task_ids", []) or [] if str(item)),
        owner_agent="formal_verifier",
        action_class=action_class,
        action_type=action_type,
        priority=priority,
        priority_rank=_priority_rank(priority),
        priority_score=priority_score,
        bridge_readiness=str(row.get("bridge_readiness", "")),
        action=action,
        required_gate=required_gate,
        required_fields=required_fields,
        expected_premises=tuple(str(item) for item in row.get("expected_premises", []) or [] if str(item))[:24],
        bridge_candidate_obligations=tuple(
            str(item) for item in row.get("bridge_candidate_obligations", []) or [] if str(item)
        ),
        candidate_declarations=tuple(
            str(item) for item in row.get("candidate_declarations", []) or [] if str(item)
        )[:8],
        blocked_reasons=tuple(str(item) for item in row.get("blocked_reasons", []) or [] if str(item)),
        evidence_boundary=str(
            row.get(
                "proof_evidence_boundary",
                "Proposal metadata is not Lean proof evidence; verify with AXLE/local Lean before promotion.",
            )
        ),
        ok=not errors and bool(row.get("ok", False)),
        errors=tuple(errors),
    )


def _contract_for_action_class(action_class: str) -> tuple[str, str, str, tuple[str, ...]]:
    if action_class == "compose_existing_bridge_chain":
        return (
            "compose_verified_bridge_chain_into_frontier_skeleton",
            "compose existing verified bridge obligations into the next non-placeholder theorem skeleton",
            "non-placeholder theorem composition passes AXLE/local Lean verify_proof",
            ("lean_statement", "proof_body", "used_bridge_obligations", "verifier", "kernel_verified"),
        )
    if action_class == "add_minimal_wrapper":
        return (
            "add_minimal_verified_wrapper",
            "add the smallest reusable wrapper around the ranked local declaration or bridge",
            "new wrapper obligation passes AXLE/local Lean verify_proof and is added to proof bank",
            ("wrapper_statement", "proof_body", "source_declaration", "verifier", "kernel_verified"),
        )
    if action_class == "design_bridge_lemma":
        return (
            "design_missing_bridge_lemma",
            "design and verify one reusable bridge lemma for the missing primitive",
            "bridge lemma passes AXLE/local Lean verify_proof and downstream retrieval can find it",
            ("bridge_statement", "proof_plan", "proof_body", "verifier", "kernel_verified"),
        )
    return (
        "design_lean_primitive_from_first_principles",
        "define the missing Lean primitive and prove a minimal sanity theorem",
        "primitive definition compiles and one sanity theorem passes AXLE/local Lean verify_proof",
        ("definition", "sanity_theorem", "proof_body", "verifier", "kernel_verified"),
    )


def _priority_label(action_class: str, priority_score: int) -> str:
    if action_class == "compose_existing_bridge_chain" and priority_score >= 180:
        return "high"
    if action_class in {"compose_existing_bridge_chain", "add_minimal_wrapper"}:
        return "medium"
    if action_class == "design_bridge_lemma" and priority_score >= 180:
        return "medium"
    return "low"


def _priority_rank(priority: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(priority, 3)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return {}


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError:
        errors.append(f"missing {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSONL in {path}: {exc}")
    return []


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Proof-Bank Action Export",
        "",
        f"- Expansion directory: `{payload.get('proof_bank_expansion_dir')}`",
        f"- Actions: {payload.get('n_ok')}/{payload.get('n_actions')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Action Classes",
        "",
    ]
    for name, count in dict(payload.get("by_action_class", {})).items():
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Priority", ""])
    for name, count in dict(payload.get("by_priority", {})).items():
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Top Actions", ""])
    for row in list(payload.get("actions", []))[:20]:
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('priority')}` `{row.get('action_class')}` "
            f"`{row.get('primitive')}`: {row.get('action')}"
        )
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

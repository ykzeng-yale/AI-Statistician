from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


CLAIM_LEDGER_ACTION_SCHEMA_VERSION = 1

ALLOWED_OWNERS = {
    "formal_verifier",
    "theory_developer",
    "algorithm_engineer",
    "simulator_agent",
    "research_coordinator",
}


@dataclass(frozen=True)
class ClaimLedgerActionRow:
    schema_version: int
    action_id: str
    source: str
    source_claim_id: str
    question_id: str
    problem_class: str
    owner_agent: str
    action_type: str
    priority: str
    trigger_status: str
    evidence_level: str
    action: str
    required_gate: str
    required_fields: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


def export_claim_ledger_actions(
    claim_ledger_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export owner-agent tasks from a typed claim ledger.

    This is the machine-facing bridge from passive evidence rows to the next
    autonomous iteration. It does not solve the tasks. It makes the expected
    owner, output fields, and verification/simulation gate explicit.
    """

    errors: list[str] = []
    manifest_path = claim_ledger_dir / "claim_ledger_manifest.json"
    rows_path = claim_ledger_dir / "claim_ledger.jsonl"
    manifest = _read_json(manifest_path, errors)
    ledger_rows = _read_jsonl(rows_path, errors)
    actions = _actions_from_ledger(ledger_rows)
    by_owner = Counter(row.owner_agent for row in actions)
    by_type = Counter(row.action_type for row in actions)
    by_priority = Counter(row.priority for row in actions)
    payload: dict[str, object] = {
        "schema_version": CLAIM_LEDGER_ACTION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_ledger_dir": str(claim_ledger_dir),
        "claim_ledger_manifest": str(manifest_path),
        "claim_ledger_jsonl": str(rows_path),
        "ledger_claims": manifest.get("n_claims", len(ledger_rows)),
        "ledger_all_ok": manifest.get("all_ok", False),
        "n_actions": len(actions),
        "n_ok": sum(1 for row in actions if row.ok),
        "all_ok": not errors and bool(manifest.get("all_ok", False)) and all(row.ok for row in actions),
        "errors": errors,
        "by_owner": dict(sorted(by_owner.items())),
        "by_type": dict(sorted(by_type.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "actions": [asdict(row) for row in actions],
        "action_fingerprint": stable_hash([asdict(row) for row in actions]),
        "limitations": [
            "action rows are task contracts, not completed theory/proof/simulation repairs",
            "formal_verifier tasks require AXLE/local Lean verification before proof-bank promotion",
            "simulation/theory/algorithm tasks require rerun evidence before claiming improvement",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "claim_ledger_action_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "claim_ledger_actions.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in actions)
            + ("\n" if actions else ""),
            encoding="utf-8",
        )
        (out_dir / "claim_ledger_actions.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _actions_from_ledger(rows: list[dict[str, Any]]) -> list[ClaimLedgerActionRow]:
    by_claim_id = {str(row.get("claim_id", "")): row for row in rows if isinstance(row, dict)}
    agenda_source_ids = {
        _agenda_source_claim_id(row)
        for row in rows
        if isinstance(row, dict) and row.get("status") == "REVISION_QUEUED"
    }
    actions: list[ClaimLedgerActionRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status", ""))
        if status == "REVISION_QUEUED":
            actions.append(_action_from_agenda(row))
        elif status in {"FORMAL_GAP", "PROOF_FAILED", "SIMULATION_FLAGGED"}:
            claim_id = str(row.get("claim_id", ""))
            if claim_id not in agenda_source_ids:
                actions.append(_fallback_action(row))
    # Stable de-duplication: keep explicit agenda items over fallback rows.
    deduped: dict[str, ClaimLedgerActionRow] = {}
    for action in actions:
        key = action.action_id
        if key not in deduped or deduped[key].source != "agenda":
            deduped[key] = action
    return list(deduped.values())


def _agenda_source_claim_id(row: dict[str, Any]) -> str:
    claim_id = str(row.get("claim_id", ""))
    source = str(row.get("statement", ""))
    if "formal gap" in claim_id:
        return source
    action = str(row.get("action", ""))
    theorem_goal_id = str(row.get("theorem_goal_id", ""))
    if theorem_goal_id:
        question_id = str(row.get("question_id", ""))
        return f"formal:{question_id}:{question_id}:{theorem_goal_id}"
    if action:
        return action
    return claim_id


def _action_from_agenda(row: dict[str, Any]) -> ClaimLedgerActionRow:
    owner = str(row.get("owner_agent") or row.get("escalation_target") or "research_coordinator")
    trigger = str(row.get("statement") or row.get("trigger_status") or "REVISION_QUEUED")
    action_type, required_gate, required_fields = _contract_for_owner(owner, trigger)
    return _action_row(
        row,
        source="agenda",
        owner_agent=owner,
        action_type=action_type,
        priority="high" if owner in {"formal_verifier", "theory_developer"} else "medium",
        action=str(row.get("action") or trigger),
        required_gate=required_gate,
        required_fields=required_fields,
    )


def _fallback_action(row: dict[str, Any]) -> ClaimLedgerActionRow:
    status = str(row.get("status", ""))
    if status == "SIMULATION_FLAGGED":
        owner = str(row.get("escalation_target") or "theory_developer")
        action_type, required_gate, required_fields = _contract_for_owner(owner, status)
        action = "diagnose and repair simulation-flagged procedure"
        priority = "high"
    elif status == "PROOF_FAILED":
        owner = "formal_verifier"
        action_type = "lean_proof_repair_from_verifier_error"
        required_gate = "AXLE/local Lean verify_proof succeeds for repaired obligation"
        required_fields = ("repaired_lean_statement", "repaired_proof_body", "verifier", "kernel_verified")
        action = "repair failed Lean proof attempt"
        priority = "high"
    else:
        owner = "formal_verifier"
        action_type = "proof_bank_expansion_from_formal_gap"
        required_gate = "new or reused proof-bank obligation passes AXLE/local Lean verify_proof"
        required_fields = (
            "theorem_statement",
            "proof_body",
            "proof_obligation_id",
            "remaining_formal_gaps",
        )
        action = "convert formal gap into reusable proof-bank obligation or sharper theorem-hole task"
        priority = "high" if row.get("formal_source_hits") else "medium"
    return _action_row(
        row,
        source="status_fallback",
        owner_agent=owner,
        action_type=action_type,
        priority=priority,
        action=action,
        required_gate=required_gate,
        required_fields=required_fields,
    )


def _contract_for_owner(owner: str, trigger: str) -> tuple[str, str, tuple[str, ...]]:
    trigger_text = trigger.lower()
    if owner == "formal_verifier":
        return (
            "proof_bank_expansion_from_formal_gap",
            "new or reused proof-bank obligation passes AXLE/local Lean verify_proof",
            ("theorem_statement", "proof_body", "proof_obligation_id", "remaining_formal_gaps"),
        )
    if owner == "algorithm_engineer":
        return (
            "algorithm_repair_from_numerical_failure",
            "isolated patch rerun has finite metrics and improves or preserves registered diagnostics",
            ("algorithm_id", "implementation_hash", "before_after_metrics", "promotion_decision"),
        )
    if owner == "simulator_agent" or "environment" in trigger_text:
        return (
            "simulator_environment_extension",
            "new simulator environment has finite metrics and stress-test coverage",
            ("dgp_spec", "diagnostic_metrics", "stress_tests", "rerun_manifest"),
        )
    if owner == "theory_developer":
        return (
            "theory_revision_from_gap_or_simulation",
            "revised theorem goals are traceable to evidence and remaining gaps are explicit",
            ("revised_procedure", "revised_theorem_goals", "assumption_delta", "simulation_delta"),
        )
    return (
        "coordinator_triage",
        "task has a routed owner, explicit acceptance criteria, and evidence path",
        ("owner_agent", "action_type", "acceptance_criteria"),
    )


def _action_row(
    row: dict[str, Any],
    *,
    source: str,
    owner_agent: str,
    action_type: str,
    priority: str,
    action: str,
    required_gate: str,
    required_fields: tuple[str, ...],
) -> ClaimLedgerActionRow:
    errors: list[str] = []
    if owner_agent not in ALLOWED_OWNERS:
        errors.append("owner_agent invalid")
    if priority not in {"high", "medium", "low"}:
        errors.append("priority invalid")
    if not required_gate:
        errors.append("required_gate missing")
    if not required_fields:
        errors.append("required_fields missing")
    if not action:
        errors.append("action missing")
    evidence_paths = tuple(str(path) for path in row.get("evidence_paths", []) or [] if str(path))
    if not evidence_paths:
        errors.append("evidence_paths missing")
    claim_id = str(row.get("claim_id", ""))
    action_id = f"claim_action:{source}:{claim_id}"
    return ClaimLedgerActionRow(
        schema_version=CLAIM_LEDGER_ACTION_SCHEMA_VERSION,
        action_id=action_id,
        source=source,
        source_claim_id=claim_id,
        question_id=str(row.get("question_id", "")),
        problem_class=str(row.get("problem_class", "")),
        owner_agent=owner_agent,
        action_type=action_type,
        priority=priority,
        trigger_status=str(row.get("status", "")),
        evidence_level=str(row.get("evidence_level", "")),
        action=action,
        required_gate=required_gate,
        required_fields=required_fields,
        evidence_paths=evidence_paths,
        ok=not errors,
        errors=tuple(errors),
    )


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
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
    rows = payload.get("actions", [])
    lines = [
        "# Claim Ledger Action Export",
        "",
        "This file converts typed claim evidence into owner-agent work items.",
        "",
        f"- Claim ledger: `{payload.get('claim_ledger_manifest')}`",
        f"- Actions: {payload.get('n_ok')}/{payload.get('n_actions')} audit-clean",
        "",
        "## Owner Counts",
        "",
    ]
    by_owner = payload.get("by_owner", {})
    if isinstance(by_owner, dict) and by_owner:
        for owner, count in sorted(by_owner.items()):
            lines.append(f"- `{owner}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Actions", ""])
    if isinstance(rows, list):
        for row in rows[:30]:
            if not isinstance(row, dict):
                continue
            lines.extend(
                [
                    f"### {row.get('action_id')}",
                    "",
                    f"- Source claim: `{row.get('source_claim_id')}`",
                    f"- Owner: `{row.get('owner_agent')}`",
                    f"- Type: `{row.get('action_type')}`",
                    f"- Priority: `{row.get('priority')}`",
                    f"- Required gate: {row.get('required_gate')}",
                    f"- Action: {row.get('action')}",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"

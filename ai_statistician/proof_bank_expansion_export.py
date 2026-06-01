from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formal_gap_task_export import export_formal_gap_lean_tasks
from .formalization_target_audit import audit_formalization_targets
from .proof_bank import get_obligation


PROOF_BANK_EXPANSION_SCHEMA_VERSION = 1

REQUIRED_PROPOSAL_GATES = (
    "lean_compiles",
    "no_forbidden_tokens",
    "no_duplicate_statement",
    "minimal_imports",
    "non_vacuity_example",
    "downstream_reuse",
    "statistical_semantic_review",
)


@dataclass(frozen=True)
class ProofBankExpansionCandidate:
    proposal_id: str
    source_kind: str
    proposed_by: str
    candidate: dict[str, object]
    source_task_ids: tuple[str, ...]
    domain_tags: tuple[str, ...]
    expected_premises: tuple[str, ...]
    required_gates: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    status: str
    action_class: str
    notes: str
    primitive: str
    priority_score: int
    bridge_readiness: str
    candidate_declarations: tuple[str, ...]
    bridge_candidate_obligations: tuple[str, ...]
    source_gap_ids: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


def export_proof_bank_expansion_candidates(
    run_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export formal gaps as proof-bank expansion proposals.

    This is intentionally one step weaker than adding a proof to the proof
    bank. It converts audited FORMAL_GAP tasks and ranked formalization targets
    into schema-compatible lemma proposals and a theorem-hole promotion queue.
    Placeholder skeletons remain blocked until the missing `h_frontier_missing`
    assumptions are replaced by real Lean proof arguments.
    """

    target_payload = audit_formalization_targets(run_dir)
    task_payload = export_formal_gap_lean_tasks(run_dir)
    tasks = [row for row in task_payload.get("tasks", []) if isinstance(row, dict)]
    rows = [
        _candidate_for_target(row, tasks)
        for row in target_payload.get("rows", [])
        if isinstance(row, dict)
    ]
    rows = [row for row in rows if row.source_task_ids]
    queue = [_queue_row(rank, row, tasks) for rank, row in enumerate(rows, start=1)]
    payload = {
        "schema_version": PROOF_BANK_EXPANSION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "n_candidates": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_candidate_ready": sum(1 for row in rows if row.status == "candidate_ready"),
        "n_blocked_placeholder": sum(1 for row in rows if row.status == "blocked_placeholder"),
        "n_bridge_ready": sum(1 for row in rows if row.bridge_candidate_obligations),
        "n_compose_existing_bridge_chain": sum(
            1 for row in rows if row.action_class == "compose_existing_bridge_chain"
        ),
        "n_add_minimal_wrapper": sum(1 for row in rows if row.action_class == "add_minimal_wrapper"),
        "n_design_bridge_lemma": sum(1 for row in rows if row.action_class == "design_bridge_lemma"),
        "n_design_from_first_principles": sum(
            1 for row in rows if row.action_class == "design_from_first_principles"
        ),
        "all_ok": bool(rows) and all(row.ok for row in rows),
        "candidate_fingerprint": stable_hash([asdict(row) for row in rows]),
        "candidates": [asdict(row) for row in rows],
        "lemma_proposal_schema_reference": "legacy_sources/ai_statistician/schemas/lemma_proposal.schema.json",
        "theorem_hole_queue_schema_reference": (
            "legacy_sources/ai_statistician/schemas/theorem_hole_promotion_queue.schema.json"
        ),
        "theorem_hole_promotion_queue": {
            "report_id": f"proof_bank_expansion:{stable_hash([item for item in queue])[:12]}",
            "source_task_count": int(task_payload.get("n_tasks", 0)),
            "theorem_hole_task_count": sum(1 for task in tasks if task.get("allowed_sorry")),
            "promoted_count": sum(1 for item in queue if item["status"] == "candidate_ready"),
            "queued_count": len(queue),
            "first_target_task_id": queue[0]["task_id"] if queue else None,
            "first_target_declaration": queue[0]["declaration"] if queue else None,
            "queue": queue,
            "promotion_policy": (
                "Queue FORMAL_GAP tasks only as proof-bank expansion candidates. "
                "Do not promote a candidate until it has a non-placeholder proof body "
                "that passes AXLE verify_proof and the downstream reuse gates."
            ),
            "notes": (
                "Rows reuse the legacy theorem-hole promotion queue schema. "
                "Most current frontier skeletons are expected to remain blocked "
                "because they intentionally expose h_frontier_missing assumptions."
            ),
        },
        "limitations": [
            "lemma proposals are not verified proof-bank entries",
            "candidate.proof is intentionally empty until a real AXLE-verified proof is supplied",
            "blocked_placeholder rows must not be accepted into the proof bank",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        proposal_path = out_dir / "lemma_proposals.jsonl"
        with proposal_path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(_legacy_lemma_proposal(row), default=str) + "\n")
        queue_path = out_dir / "theorem_hole_promotion_queue_manifest.json"
        queue_path.write_text(
            json.dumps(payload["theorem_hole_promotion_queue"], indent=2, default=str),
            encoding="utf-8",
        )
        payload["lemma_proposals_jsonl"] = str(proposal_path)
        payload["theorem_hole_promotion_queue_path"] = str(queue_path)
        (out_dir / "proof_bank_expansion_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "proof_bank_expansion.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _candidate_for_target(
    target: dict[str, Any],
    tasks: list[dict[str, Any]],
) -> ProofBankExpansionCandidate:
    primitive = str(target.get("primitive", ""))
    matching_tasks = [
        task
        for task in tasks
        if primitive in (task.get("required_primitives", []) or [])
        and str(task.get("gap_id", "")) in set(target.get("gap_ids", []) or [])
    ]
    first_task = matching_tasks[0] if matching_tasks else {}
    source_task_ids = tuple(str(task.get("task_id", "")) for task in matching_tasks if task.get("task_id"))
    source_gap_ids = tuple(str(gap_id) for gap_id in target.get("gap_ids", []) or [] if str(gap_id))
    candidate_declarations = tuple(
        str(item) for item in target.get("candidate_declarations", []) or [] if str(item)
    )
    bridge_candidates = tuple(
        str(item) for item in target.get("bridge_candidate_obligations", []) or [] if str(item)
    )
    statement = _extract_theorem_signature(str(first_task.get("statement", "")))
    declaration = _extract_declaration_name(statement) or f"{_safe_identifier(primitive)}_bridge"
    expected_premises = _expected_premises(target, candidate_declarations, bridge_candidates)
    blocked_reasons = _blocked_reasons(statement, target, matching_tasks)
    action_class = _proposal_action_class(bridge_candidates, candidate_declarations)
    errors: list[str] = []
    if not primitive:
        errors.append("missing primitive")
    if not source_task_ids:
        errors.append("no source formal-gap Lean task found")
    if not statement:
        errors.append("no candidate theorem signature extracted")
    if not expected_premises:
        errors.append("no expected premises or local declarations attached")
    status = "blocked_placeholder" if blocked_reasons else "candidate_ready"
    notes = _proposal_notes(
        action_class,
        primitive=primitive,
        declaration=declaration,
        bridge_candidates=bridge_candidates,
        suggested_next_step=str(target.get("suggested_next_step", "")),
    )
    candidate_name = _candidate_name(primitive, action_class)
    return ProofBankExpansionCandidate(
        proposal_id=f"lemma_proposal:{_safe_identifier(primitive)}:{stable_hash([primitive, source_task_ids])[:10]}",
        source_kind="formal_gap_task_export",
        proposed_by="proof_bank_expansion_export",
        candidate={
            "name": candidate_name,
            "statement": statement,
            "proof": "",
            "motivation_tasks": source_task_ids,
            "imports_added": tuple(first_task.get("imports", []) or ()),
            "reuse_count": int(target.get("n_gaps", 0) or 0),
            "generality_score": _generality_score(target, bridge_candidates),
            "semantic_notes": notes,
        },
        source_task_ids=source_task_ids,
        domain_tags=tuple(
            item
            for item in (
                "proof_bank_expansion",
                "formal_gap",
                primitive,
                action_class,
                str(target.get("bridge_readiness", "")),
                *tuple(target.get("problem_classes", []) or ()),
                *tuple(target.get("theorem_goals", []) or ()),
            )
            if item
        ),
        expected_premises=expected_premises,
        required_gates=REQUIRED_PROPOSAL_GATES,
        blocked_reasons=blocked_reasons,
        status=status,
        action_class=action_class,
        notes=notes,
        primitive=primitive,
        priority_score=int(target.get("priority_score", 0) or 0),
        bridge_readiness=str(target.get("bridge_readiness", "")),
        candidate_declarations=candidate_declarations,
        bridge_candidate_obligations=bridge_candidates,
        source_gap_ids=source_gap_ids,
        ok=not errors,
        errors=tuple(errors),
    )


def _expected_premises(
    target: dict[str, Any],
    candidate_declarations: tuple[str, ...],
    bridge_candidates: tuple[str, ...],
) -> tuple[str, ...]:
    premises: list[str] = []
    for obligation_id in bridge_candidates + tuple(target.get("supporting_proof_obligations", []) or ()):
        if obligation_id not in premises:
            premises.append(str(obligation_id))
        try:
            obligation = get_obligation(str(obligation_id))
        except KeyError:
            continue
        for lemma in obligation.expected_lemmas:
            if lemma not in premises:
                premises.append(lemma)
    for declaration in candidate_declarations[:8]:
        if declaration not in premises:
            premises.append(declaration)
    return tuple(premises)


def _blocked_reasons(
    statement: str,
    target: dict[str, Any],
    matching_tasks: list[dict[str, Any]],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if "h_frontier_missing" in statement:
        reasons.append("source theorem still depends on h_frontier_missing placeholder assumptions")
    if any(task.get("allowed_sorry") for task in matching_tasks):
        reasons.append("source task is an allowed-sorry theorem-development packet")
    if not target.get("bridge_candidate_obligations"):
        reasons.append("no direct verified proof-bank bridge candidate ranked yet")
    if not target.get("candidate_declarations"):
        reasons.append("no local Mathlib/StatInference declaration candidate attached")
    return tuple(dict.fromkeys(reasons))


def _queue_row(
    rank: int,
    row: ProofBankExpansionCandidate,
    tasks: list[dict[str, Any]],
) -> dict[str, object]:
    source_task = next((task for task in tasks if task.get("task_id") in row.source_task_ids), {})
    declaration = _extract_declaration_name(str(row.candidate.get("statement", ""))) or str(row.candidate["name"])
    return {
        "rank": rank,
        "task_id": row.source_task_ids[0] if row.source_task_ids else "",
        "candidate_name": str(row.candidate["name"]),
        "status": row.status,
        "action_class": row.action_class,
        "next_action": _queue_next_action(row),
        "declaration": declaration,
        "module": str(source_task.get("namespace", "")),
        "file": str(source_task.get("artifact_path", "")),
        "domain_tags": list(row.domain_tags),
        "expected_premises": list(row.expected_premises),
        "source_allowed_sorry": bool(source_task.get("allowed_sorry", False)),
        "no_placeholder_proof_block": (
            "BLOCKED_PLACEHOLDER"
            if any("placeholder" in reason for reason in row.blocked_reasons)
            else "NO_PLACEHOLDER_DETECTED"
        ),
        "blocked_reasons": list(row.blocked_reasons),
        "verification_evidence": [
            "candidate proof intentionally empty",
            "requires AXLE verify_proof before proof-bank admission",
            f"bridge_readiness={row.bridge_readiness}",
            f"action_class={row.action_class}",
        ],
    }


def _legacy_lemma_proposal(row: ProofBankExpansionCandidate) -> dict[str, object]:
    payload = asdict(row)
    return {
        key: payload[key]
        for key in (
            "proposal_id",
            "source_kind",
            "proposed_by",
            "candidate",
            "source_task_ids",
            "domain_tags",
            "expected_premises",
            "required_gates",
            "blocked_reasons",
            "status",
            "action_class",
            "notes",
        )
    }


def _proposal_action_class(
    bridge_candidates: tuple[str, ...],
    candidate_declarations: tuple[str, ...],
) -> str:
    if len(bridge_candidates) >= 3:
        return "compose_existing_bridge_chain"
    if bridge_candidates and candidate_declarations:
        return "add_minimal_wrapper"
    if bridge_candidates or candidate_declarations:
        return "design_bridge_lemma"
    return "design_from_first_principles"


def _proposal_notes(
    action_class: str,
    *,
    primitive: str,
    declaration: str,
    bridge_candidates: tuple[str, ...],
    suggested_next_step: str,
) -> str:
    if action_class == "compose_existing_bridge_chain":
        lead = (
            f"Avoid duplicating bridge wrappers for `{primitive}`: "
            f"{len(bridge_candidates)} verified bridge obligations are already ranked. "
            f"Compose the next theorem skeleton `{declaration}` from the bridge chain, "
            "then close only the remaining full-theorem interface with AXLE verify_proof."
        )
    elif action_class == "add_minimal_wrapper":
        lead = (
            f"Add the smallest reusable wrapper for `{primitive}` before promoting "
            f"`{declaration}`."
        )
    elif action_class == "design_bridge_lemma":
        lead = (
            f"Design one missing bridge lemma for `{primitive}` before attempting "
            f"`{declaration}`."
        )
    else:
        lead = (
            f"Design the Lean primitive for `{primitive}` from first principles before "
            f"attempting `{declaration}`."
        )
    return f"{lead} {suggested_next_step}".strip()


def _candidate_name(primitive: str, action_class: str) -> str:
    suffix = "theorem_composition" if action_class == "compose_existing_bridge_chain" else "bridge"
    return f"AIStatistician.Proposed.{_safe_identifier(primitive)}_{suffix}"


def _queue_next_action(row: ProofBankExpansionCandidate) -> str:
    if row.action_class == "compose_existing_bridge_chain":
        return "compose_verified_bridge_chain_into_theorem_skeleton"
    if row.action_class == "add_minimal_wrapper":
        return "add_minimal_axle_verified_wrapper"
    if row.action_class == "design_bridge_lemma":
        return "design_missing_bridge_lemma"
    return "design_lean_primitive_from_first_principles"


def _extract_theorem_signature(statement: str) -> str:
    lines = statement.splitlines()
    start = next((idx for idx, line in enumerate(lines) if re.match(r"\s*theorem\s+", line)), None)
    if start is None:
        return ""
    kept: list[str] = []
    for line in lines[start:]:
        if ":= by" in line:
            before = line.split(":= by", 1)[0].rstrip()
            if before:
                kept.append(before)
            break
        kept.append(line.rstrip())
    return "\n".join(kept).strip()


def _extract_declaration_name(statement: str) -> str:
    match = re.search(r"\btheorem\s+([A-Za-z_][A-Za-z0-9_'.]*)\b", statement)
    return match.group(1) if match else ""


def _safe_identifier(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")
    if not cleaned:
        return "candidate"
    if cleaned[0].isdigit():
        return f"candidate_{cleaned}"
    return cleaned


def _generality_score(target: dict[str, Any], bridge_candidates: tuple[str, ...]) -> float:
    score = 0.45
    score += min(int(target.get("n_gaps", 0) or 0), 5) * 0.05
    score += min(len(target.get("problem_classes", []) or []), 4) * 0.04
    if bridge_candidates:
        score += 0.12
    if target.get("candidate_declarations"):
        score += 0.08
    return round(min(score, 0.95), 3)


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Proof-Bank Expansion Candidates",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Candidates: {payload.get('n_ok')}/{payload.get('n_candidates')} audit-clean",
        f"- Bridge-ready candidates: {payload.get('n_bridge_ready')}",
        f"- Blocked placeholder candidates: {payload.get('n_blocked_placeholder')}",
        f"- Compose existing bridge chains: {payload.get('n_compose_existing_bridge_chain')}",
        f"- Add minimal wrappers: {payload.get('n_add_minimal_wrapper')}",
        f"- Design bridge lemmas: {payload.get('n_design_bridge_lemma')}",
        f"- Lemma proposals JSONL: `{payload.get('lemma_proposals_jsonl', '')}`",
        f"- Theorem-hole queue: `{payload.get('theorem_hole_promotion_queue_path', '')}`",
        f"- Fingerprint: `{payload.get('candidate_fingerprint')}`",
        "",
        "These rows are proof-bank expansion proposals, not verified proof-bank entries.",
        "",
        "## Top Candidates",
        "",
    ]
    for row in payload.get("candidates", [])[:20]:  # type: ignore[index]
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### `{row.get('primitive')}` [{row.get('status')}]",
                "",
                f"- Proposal: `{row.get('proposal_id')}`",
                f"- Priority score: {row.get('priority_score')}",
                f"- Action class: `{row.get('action_class')}`",
                f"- Bridge readiness: `{row.get('bridge_readiness')}`",
                f"- Source tasks: {', '.join(f'`{item}`' for item in row.get('source_task_ids', [])) or 'none'}",
                f"- Candidate declarations: {', '.join(f'`{item}`' for item in row.get('candidate_declarations', [])[:5]) or 'none'}",
                f"- Bridge obligations: {', '.join(f'`{item}`' for item in row.get('bridge_candidate_obligations', [])) or 'none'}",
                f"- Expected premises: {', '.join(f'`{item}`' for item in row.get('expected_premises', [])[:8]) or 'none'}",
                "",
            ]
        )
        for reason in row.get("blocked_reasons", []) or []:
            lines.append(f"- Blocked: {reason}")
        if row.get("blocked_reasons"):
            lines.append("")
    return "\n".join(lines) + "\n"

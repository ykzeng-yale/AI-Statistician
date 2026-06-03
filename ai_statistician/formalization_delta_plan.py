from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMALIZATION_DELTA_PLAN_SCHEMA_VERSION = 1


ACTION_COSTS = {
    "reuse_exact_proof_bank_obligation": 1,
    "compose_existing_bridge_chain": 2,
    "formalize_assumption_interface": 2,
    "add_minimal_wrapper": 3,
    "design_bridge_lemma": 5,
    "port_external_source": 6,
    "design_from_first_principles": 8,
}


@dataclass(frozen=True)
class FormalizationDeltaPlanRow:
    schema_version: int
    primitive: str
    action_id: str
    action_class: str
    plan_stage: str
    delta_kind: str
    coverage_classification: str
    owner_agent: str
    base_cost: int
    risk_penalty: int
    reuse_credit: int
    total_cost: int
    priority: str
    expected_premises: tuple[str, ...]
    bridge_candidate_obligations: tuple[str, ...]
    candidate_declarations: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    source_gap_ids: tuple[str, ...]
    source_task_ids: tuple[str, ...]
    next_step: str
    evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def build_formalization_delta_plan(
    proof_bank_actions_dir: Path,
    out_dir: Path | None = None,
    *,
    primitive_source_coverage_dir: Path | None = None,
) -> dict[str, object]:
    """Plan the smallest useful Lean-formalization delta from action rows.

    This is a planning/ranking artifact, not proof evidence. It estimates which
    new definitions, wrappers, bridge lemmas, or theorem compositions are needed
    before the target frontier theorem can become provable from the current Lean
    environment. AXLE/local Lean still decides whether any row is actually
    verified.
    """

    errors: list[str] = []
    action_manifest_path = proof_bank_actions_dir / "proof_bank_action_manifest.json"
    action_manifest = _read_json(action_manifest_path, errors)
    coverage_manifest_path = (
        primitive_source_coverage_dir / "primitive_source_coverage_manifest.json"
        if primitive_source_coverage_dir is not None
        else None
    )
    coverage_manifest = (
        _read_json(coverage_manifest_path, errors, missing_ok=True)
        if coverage_manifest_path is not None
        else {}
    )
    coverage_by_primitive = {
        str(row.get("primitive", "")): row
        for row in coverage_manifest.get("rows", [])
        if isinstance(row, dict) and row.get("primitive")
    }
    rows = [
        _row_from_action(row, coverage_by_primitive)
        for row in action_manifest.get("actions", [])
        if isinstance(row, dict)
    ]
    rows = sorted(rows, key=lambda row: (row.total_cost, row.priority, row.primitive, row.action_id))
    by_stage = Counter(row.plan_stage for row in rows)
    by_delta_kind = Counter(row.delta_kind for row in rows)
    by_action_class = Counter(row.action_class for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_DELTA_PLAN_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_bank_actions_dir": str(proof_bank_actions_dir),
        "proof_bank_action_manifest": str(action_manifest_path),
        "primitive_source_coverage_dir": str(primitive_source_coverage_dir or ""),
        "primitive_source_coverage_manifest": str(coverage_manifest_path or ""),
        "n_plan_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(action_manifest.get("all_ok", False)) and all(row.ok for row in rows),
        "total_estimated_cost": sum(row.total_cost for row in rows),
        "mean_estimated_cost": (sum(row.total_cost for row in rows) / len(rows) if rows else 0.0),
        "n_low_cost_existing_reuse": sum(1 for row in rows if row.total_cost <= 2),
        "n_medium_cost_bridge_or_wrapper": sum(1 for row in rows if 3 <= row.total_cost <= 5),
        "n_high_cost_new_theory": sum(1 for row in rows if row.total_cost >= 6),
        "by_plan_stage": dict(sorted(by_stage.items())),
        "by_delta_kind": dict(sorted(by_delta_kind.items())),
        "by_action_class": dict(sorted(by_action_class.items())),
        "top_low_cost_rows": [asdict(row) for row in rows[:10]],
        "top_high_cost_rows": [asdict(row) for row in sorted(rows, key=lambda row: -row.total_cost)[:10]],
        "rows": [asdict(row) for row in rows],
        "plan_fingerprint": stable_hash([asdict(row) for row in rows]),
        "errors": errors,
        "limitations": [
            "formalization delta rows are planning evidence, not proof evidence",
            "cost is a heuristic over action class, reuse, blockers, and source coverage",
            "minimality is approximate; AXLE/local Lean verification and semantic review remain required",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formalization_delta_plan_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formalization_delta_plan.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_delta_plan.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _row_from_action(
    action: dict[str, Any],
    coverage_by_primitive: dict[str, dict[str, Any]],
) -> FormalizationDeltaPlanRow:
    primitive = str(action.get("primitive", ""))
    action_class = str(action.get("action_class", ""))
    coverage = coverage_by_primitive.get(primitive, {})
    expected_premises = tuple(str(item) for item in action.get("expected_premises", []) or [] if str(item))
    bridge_candidates = tuple(
        str(item) for item in action.get("bridge_candidate_obligations", []) or [] if str(item)
    )
    candidate_declarations = tuple(
        str(item) for item in action.get("candidate_declarations", []) or [] if str(item)
    )
    blocked_reasons = tuple(str(item) for item in action.get("blocked_reasons", []) or [] if str(item))
    base_cost = ACTION_COSTS.get(action_class, 9)
    risk_penalty = _risk_penalty(action_class, blocked_reasons, coverage)
    reuse_credit = _reuse_credit(action_class, bridge_candidates, candidate_declarations, coverage)
    total_cost = max(1, base_cost + risk_penalty - reuse_credit)
    errors: list[str] = []
    if not primitive:
        errors.append("missing primitive")
    if not action_class:
        errors.append("missing action_class")
    if action_class not in ACTION_COSTS:
        errors.append(f"unknown action_class={action_class}")
    return FormalizationDeltaPlanRow(
        schema_version=FORMALIZATION_DELTA_PLAN_SCHEMA_VERSION,
        primitive=primitive,
        action_id=str(action.get("action_id", "")),
        action_class=action_class,
        plan_stage=_plan_stage(action_class),
        delta_kind=_delta_kind(action_class),
        coverage_classification=str(coverage.get("classification", "")),
        owner_agent=str(action.get("owner_agent", "formal_verifier")),
        base_cost=base_cost,
        risk_penalty=risk_penalty,
        reuse_credit=reuse_credit,
        total_cost=total_cost,
        priority=str(action.get("priority", "")),
        expected_premises=expected_premises,
        bridge_candidate_obligations=bridge_candidates,
        candidate_declarations=candidate_declarations,
        blocked_reasons=blocked_reasons,
        source_gap_ids=tuple(str(item) for item in action.get("source_gap_ids", []) or [] if str(item)),
        source_task_ids=tuple(str(item) for item in action.get("source_task_ids", []) or [] if str(item)),
        next_step=_next_step(action_class, primitive, total_cost),
        evidence_boundary=(
            "This row estimates a minimal formalization delta. It is not proof evidence until "
            "the referenced Lean statements/proofs are accepted by AXLE or the local Lean kernel."
        ),
        ok=not errors and bool(action.get("ok", False)),
        errors=tuple(errors),
    )


def _risk_penalty(action_class: str, blocked_reasons: tuple[str, ...], coverage: dict[str, Any]) -> int:
    penalty = min(len(blocked_reasons), 3)
    if action_class == "design_from_first_principles":
        penalty += 2
    if action_class == "design_bridge_lemma":
        penalty += 1
    if coverage and coverage.get("classification") == "no_source_found":
        penalty += 2
    if coverage and coverage.get("classification") == "source_only_not_importable":
        penalty += 1
    return penalty


def _reuse_credit(
    action_class: str,
    bridge_candidates: tuple[str, ...],
    candidate_declarations: tuple[str, ...],
    coverage: dict[str, Any],
) -> int:
    credit = 0
    if bridge_candidates:
        credit += 1
    if candidate_declarations:
        credit += 1
    if coverage.get("proof_bank_exact_match_available"):
        credit += 2
    if action_class == "reuse_exact_proof_bank_obligation":
        credit += 1
    return min(credit, 3)


def _plan_stage(action_class: str) -> str:
    return {
        "reuse_exact_proof_bank_obligation": "reuse_existing_verified_obligation",
        "compose_existing_bridge_chain": "compose_verified_bridge_chain",
        "formalize_assumption_interface": "define_assumption_interface",
        "add_minimal_wrapper": "add_minimal_wrapper",
        "design_bridge_lemma": "prove_new_bridge_lemma",
        "port_external_source": "port_external_lean_source",
        "design_from_first_principles": "design_new_foundational_primitive",
    }.get(action_class, "unknown")


def _delta_kind(action_class: str) -> str:
    return {
        "reuse_exact_proof_bank_obligation": "no_new_declaration",
        "compose_existing_bridge_chain": "theorem_composition",
        "formalize_assumption_interface": "assumption_interface",
        "add_minimal_wrapper": "minimal_wrapper",
        "design_bridge_lemma": "bridge_lemma",
        "port_external_source": "external_port",
        "design_from_first_principles": "new_definition_or_theorem_family",
    }.get(action_class, "unknown")


def _next_step(action_class: str, primitive: str, total_cost: int) -> str:
    if action_class == "reuse_exact_proof_bank_obligation":
        return f"Reuse the existing verified obligation for `{primitive}`; spend effort on the enclosing theorem."
    if action_class == "compose_existing_bridge_chain":
        return f"Compose the verified bridge chain for `{primitive}` into a non-placeholder theorem skeleton."
    if action_class == "formalize_assumption_interface":
        return f"Keep `{primitive}` as an assumption interface; compile the predicate and require downstream theorem use."
    if action_class == "add_minimal_wrapper":
        return f"Add the smallest wrapper theorem for `{primitive}` and verify it with AXLE/local Lean."
    if action_class == "design_bridge_lemma":
        return f"Design one reusable bridge lemma for `{primitive}`; target cost class {total_cost} before full theorem work."
    return f"Start a new primitive-definition plan for `{primitive}`; expect source search plus semantic review before proving."


def _read_json(path: Path | None, errors: list[str], *, missing_ok: bool = False) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if not missing_ok:
            errors.append(f"missing {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Delta Plan",
        "",
        f"- Proof-bank actions: `{payload.get('proof_bank_actions_dir')}`",
        f"- Primitive-source coverage: `{payload.get('primitive_source_coverage_dir')}`",
        f"- Plan rows: {payload.get('n_ok')}/{payload.get('n_plan_rows')}",
        f"- Total estimated cost: {payload.get('total_estimated_cost')}",
        f"- Low-cost existing reuse: {payload.get('n_low_cost_existing_reuse')}",
        f"- Medium-cost bridge/wrapper: {payload.get('n_medium_cost_bridge_or_wrapper')}",
        f"- High-cost new theory: {payload.get('n_high_cost_new_theory')}",
        f"- Fingerprint: `{payload.get('plan_fingerprint')}`",
        "",
        "This is a library-aware planning artifact. It is not proof evidence.",
        "",
        "## Plan Stages",
        "",
    ]
    for stage, count in (payload.get("by_plan_stage") or {}).items():
        lines.append(f"- `{stage}`: {count}")
    lines.extend(["", "## Top Low-Cost Rows", ""])
    for row in payload.get("top_low_cost_rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('primitive')}`: {row.get('plan_stage')} "
            f"(cost={row.get('total_cost')}, action={row.get('action_class')})"
        )
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

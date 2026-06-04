from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_ATTEMPT_POPULATION_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "AGENTIC_PROOF_ATTEMPT_POPULATION_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic proof attempt population rows are memory/sampling records for "
    "candidate search, not theorem proof evidence. Population rank, sampling "
    "weight, or lessons learned never prove a theorem; promotion still requires "
    "local Lean kernel verification, patch-rerun calibration, and residual-gap "
    "validation."
)


@dataclass(frozen=True)
class FormalVerifierAgenticProofAttemptPopulationRow:
    schema_version: int
    population_entry_id: str
    safety_policy_id: str
    candidate_evaluation_id: str
    strategy_id: str
    followup_id: str
    residual_obligation_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    residual_gap: str
    action_class: str
    generation_mode: str
    population_bucket: str
    goal_cache_key: str
    candidate_database_key: str
    candidate_lineage_key: str
    kernel_overlay_context: dict[str, object]
    proof_sketch_population_key: str
    attempt_status: str
    prior_attempt_count: int
    successful_attempt_count: int
    failed_attempt_count: int
    diagnostic_signature: str
    lessons_learned: tuple[str, ...]
    sampler_policy: str
    selection_weight: int
    replay_priority_score: int
    rank: int
    required_memory_updates: tuple[str, ...]
    promotion_gate: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_attempt_population(
    formal_verifier_agentic_proof_safety_policy_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Seed a reusable proof-attempt population from safety-gated work orders."""

    errors: list[str] = []
    safety_policy_manifest_path = (
        formal_verifier_agentic_proof_safety_policy_dir
        / "formal_verifier_agentic_proof_safety_policy_manifest.json"
    )
    safety_policy_payload = _read_json(safety_policy_manifest_path, errors)
    safety_rows = [
        row for row in safety_policy_payload.get("rows", []) if isinstance(row, dict)
    ]
    raw_rows = [_population_row(row) for row in safety_rows]
    population_rows = _rank_rows(raw_rows)
    by_generation_mode = Counter(row.generation_mode for row in population_rows)
    by_bucket = Counter(row.population_bucket for row in population_rows)
    by_status = Counter(row.attempt_status for row in population_rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_AGENTIC_PROOF_ATTEMPT_POPULATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_safety_policy_dir": str(
            formal_verifier_agentic_proof_safety_policy_dir
        ),
        "formal_verifier_agentic_proof_safety_policy_manifest": str(
            safety_policy_manifest_path
        ),
        "n_safety_policy_rows": len(safety_rows),
        "n_population_entries": len(population_rows),
        "n_ready": by_status.get("READY_FOR_POPULATION_SEEDED_ATTEMPT", 0),
        "n_blocked": sum(
            count for status, count in by_status.items() if status.startswith("BLOCKED_")
        ),
        "n_patch_population_entries": by_bucket.get("bounded_patch_attempt", 0),
        "n_source_population_entries": by_bucket.get("source_discovery_attempt", 0),
        "n_with_goal_cache_key": sum(1 for row in population_rows if row.goal_cache_key),
        "n_with_lineage_key": sum(1 for row in population_rows if row.candidate_lineage_key),
        "n_with_sampling_weight": sum(1 for row in population_rows if row.selection_weight > 0),
        "n_with_kernel_overlay_context": sum(
            1 for row in population_rows if row.kernel_overlay_context
        ),
        "n_untried": by_status.get("READY_FOR_POPULATION_SEEDED_ATTEMPT", 0),
        "n_ok": sum(1 for row in population_rows if row.ok),
        "all_ok": not errors and all(row.ok for row in population_rows),
        "errors": errors,
        "by_generation_mode": dict(sorted(by_generation_mode.items())),
        "by_population_bucket": dict(sorted(by_bucket.items())),
        "by_attempt_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in population_rows],
        "attempt_population_fingerprint": stable_hash(
            [asdict(row) for row in population_rows]
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "population rows are search memory, not theorem proof evidence",
            "untried rows have no Lean diagnostics yet; they only seed candidate generation",
            "future Elo/P-UCB-style scores must remain sampling signals until Lean verifies a candidate",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formal_verifier_agentic_proof_attempt_population_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formal_verifier_agentic_proof_attempt_population.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in population_rows)
            + ("\n" if population_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_agentic_proof_attempt_population.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _population_row(
    row: dict[str, Any],
) -> FormalVerifierAgenticProofAttemptPopulationRow:
    errors: list[str] = []
    safety_policy_id = str(row.get("safety_policy_id", ""))
    candidate_evaluation_id = str(row.get("candidate_evaluation_id", ""))
    strategy_id = str(row.get("strategy_id", ""))
    followup_id = str(row.get("followup_id", ""))
    residual_obligation_id = str(row.get("residual_obligation_id", ""))
    generation_mode = str(row.get("generation_mode", ""))
    goal_cache_key = str(row.get("goal_cache_key", ""))
    candidate_database_key = str(row.get("candidate_database_key", ""))
    candidate_lineage_key = str(row.get("candidate_lineage_key", ""))
    kernel_overlay_context = row.get("kernel_overlay_context", {})
    if not isinstance(kernel_overlay_context, dict):
        kernel_overlay_context = {}
    policy_status = str(row.get("policy_status", ""))
    policy_ok = bool(row.get("ok", False))
    anti_cheat_checks = _str_tuple(row.get("anti_cheat_checks", []))
    static_checks = _str_tuple(row.get("required_static_checks", []))
    dynamic_checks = _str_tuple(row.get("required_dynamic_checks", []))
    safeverify_gate = str(row.get("safeverify_gate", ""))

    for field_name, value in (
        ("safety_policy_id", safety_policy_id),
        ("candidate_evaluation_id", candidate_evaluation_id),
        ("strategy_id", strategy_id),
        ("followup_id", followup_id),
        ("residual_obligation_id", residual_obligation_id),
        ("goal_cache_key", goal_cache_key),
        ("candidate_database_key", candidate_database_key),
        ("candidate_lineage_key", candidate_lineage_key),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if not policy_ok:
        errors.append("safety policy row is not ok")
    if policy_status != "READY_FOR_SAFETY_GATED_CANDIDATE_GENERATION":
        errors.append(f"safety policy row is not ready: {policy_status}")
    if not anti_cheat_checks:
        errors.append("anti_cheat_checks missing")
    if not static_checks:
        errors.append("required_static_checks missing")
    if not dynamic_checks:
        errors.append("required_dynamic_checks missing")
    if not safeverify_gate:
        errors.append("safeverify_gate missing")

    if generation_mode == "source_discovery_candidate_generation":
        population_bucket = "source_discovery_attempt"
        base_weight = 70
        lessons = (
            "untried source-discovery seed; require concrete source declarations before proof work",
            "retrieval/source candidates must be recorded as non-proof evidence",
        )
    else:
        population_bucket = "bounded_patch_attempt"
        base_weight = 100
        lessons = (
            "untried bounded-edit patch seed; preserve theorem statement and header",
            "reject helper lemmas that restate the target or contain placeholders",
        )
    if kernel_overlay_context:
        lessons = (
            *lessons,
            "kernel-overlay subclaims are reusable only as subclaim evidence",
            "target blockers must be solved before source theorem promotion",
        )

    replay_priority = int(row.get("priority_score", 0))
    selection_weight = base_weight + min(50, max(0, replay_priority // 4))
    proof_sketch_population_key = "proof_sketch_population:" + stable_hash(
        [goal_cache_key, candidate_lineage_key, generation_mode]
    )[:16]
    population_entry_id = "formal_verifier_agentic_proof_attempt_population:" + stable_hash(
        [safety_policy_id, proof_sketch_population_key, population_bucket]
    )[:16]
    attempt_status = (
        "READY_FOR_POPULATION_SEEDED_ATTEMPT"
        if not errors
        else "BLOCKED_ATTEMPT_POPULATION_INPUT"
    )
    required_memory_updates = (
        "append generated candidate body or source candidate to population record",
        "record Lean diagnostics, failed goals, and verifier outcome for every attempt",
        "record lessons learned without upgrading search state to proof evidence",
        "update sampling weight only as a search-priority signal",
    )
    if kernel_overlay_context:
        required_memory_updates = (
            *required_memory_updates,
            "record solved/deferred status for every kernel-overlay target blocker",
            "record which already kernel-verified subclaims were reused in the composed theorem",
        )

    return FormalVerifierAgenticProofAttemptPopulationRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_ATTEMPT_POPULATION_SCHEMA_VERSION,
        population_entry_id=population_entry_id,
        safety_policy_id=safety_policy_id,
        candidate_evaluation_id=candidate_evaluation_id,
        strategy_id=strategy_id,
        followup_id=followup_id,
        residual_obligation_id=residual_obligation_id,
        display_name=str(row.get("display_name", "")),
        target_theorem_name=str(row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(row.get("candidate_bridge_lemma_name", "")),
        residual_gap=str(row.get("residual_gap", "")),
        action_class=str(row.get("action_class", "")),
        generation_mode=generation_mode,
        population_bucket=population_bucket,
        goal_cache_key=goal_cache_key,
        candidate_database_key=candidate_database_key,
        candidate_lineage_key=candidate_lineage_key,
        kernel_overlay_context=kernel_overlay_context,
        proof_sketch_population_key=proof_sketch_population_key,
        attempt_status=attempt_status,
        prior_attempt_count=0,
        successful_attempt_count=0,
        failed_attempt_count=0,
        diagnostic_signature="UNTRIED_CANDIDATE_SEED",
        lessons_learned=lessons,
        sampler_policy="priority_weighted_goal_cache_population_sampling",
        selection_weight=selection_weight,
        replay_priority_score=replay_priority,
        rank=0,
        required_memory_updates=required_memory_updates,
        promotion_gate=(
            "population entry can only become proof evidence after the linked "
            f"candidate passes safety policy `{safety_policy_id}`, {safeverify_gate}"
        ),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _rank_rows(
    rows: list[FormalVerifierAgenticProofAttemptPopulationRow],
) -> list[FormalVerifierAgenticProofAttemptPopulationRow]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -row.selection_weight,
            row.display_name,
            row.residual_gap,
            row.population_entry_id,
        ),
    )
    return [
        FormalVerifierAgenticProofAttemptPopulationRow(
            **{**asdict(row), "rank": index + 1}
        )
        for index, row in enumerate(ranked)
    ]


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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Agentic Proof Attempt Population",
        "",
        f"- Safety policy manifest: `{payload.get('formal_verifier_agentic_proof_safety_policy_manifest')}`",
        f"- Population entries: {payload.get('n_population_entries')}",
        f"- Ready: {payload.get('n_ready')}",
        f"- Blocked: {payload.get('n_blocked')}",
        f"- Patch entries: {payload.get('n_patch_population_entries')}",
        f"- Source entries: {payload.get('n_source_population_entries')}",
        f"- With goal cache key: {payload.get('n_with_goal_cache_key')}",
        f"- With lineage key: {payload.get('n_with_lineage_key')}",
        f"- With sampling weight: {payload.get('n_with_sampling_weight')}",
        f"- With kernel-overlay context: {payload.get('n_with_kernel_overlay_context')}",
        f"- All OK: {payload.get('all_ok')}",
        f"- Fingerprint: `{payload.get('attempt_population_fingerprint')}`",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary")),
        "",
        "## Population Entries",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lessons = ", ".join(f"`{item}`" for item in row.get("lessons_learned", []))
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('attempt_status')}): {row.get('population_bucket')}"
        )
        lines.append(f"  goal cache key: `{row.get('goal_cache_key')}`")
        lines.append(f"  population key: `{row.get('proof_sketch_population_key')}`")
        context = row.get("kernel_overlay_context", {})
        if isinstance(context, dict) and context:
            blockers = ", ".join(
                f"`{item}`" for item in context.get("target_blockers", [])
            ) or "none"
            subclaims = ", ".join(
                f"`{item}`"
                for item in context.get("already_kernel_verified_subclaims", [])
            ) or "none"
            lines.append(f"  kernel-overlay subclaims: {subclaims}")
            lines.append(f"  kernel-overlay blockers: {blockers}")
        lines.append(f"  selection weight: {row.get('selection_weight')}")
        lines.append(f"  diagnostic signature: `{row.get('diagnostic_signature')}`")
        lines.append(f"  lessons: {lessons}")
        lines.append(f"  promotion gate: {row.get('promotion_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        if row.get("errors"):
            lines.append(f"  errors: {row.get('errors')}")
    return "\n".join(lines) + "\n"

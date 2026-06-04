from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_SAFETY_POLICY_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "AGENTIC_PROOF_SAFETY_POLICY_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic proof safety policy rows are preflight guardrails for candidate "
    "generation and evaluation, not theorem proof evidence. A candidate is "
    "proof-relevant only after the safety policy passes and local Lean kernel "
    "verification, patch-rerun calibration, and residual-gap validation accept it."
)
EVOLVE_BLOCK_START = "-- AI_STAT_EVOLVE_BLOCK_START"
EVOLVE_BLOCK_END = "-- AI_STAT_EVOLVE_BLOCK_END"


@dataclass(frozen=True)
class FormalVerifierAgenticProofSafetyPolicyRow:
    schema_version: int
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
    candidate_database_key: str
    candidate_lineage_key: str
    goal_cache_key: str
    kernel_overlay_context: dict[str, object]
    bounded_edit_policy: dict[str, object]
    statement_guard_policy: tuple[str, ...]
    forbidden_tokens: tuple[str, ...]
    anti_cheat_checks: tuple[str, ...]
    source_claim_checks: tuple[str, ...]
    required_static_checks: tuple[str, ...]
    required_dynamic_checks: tuple[str, ...]
    safeverify_gate: str
    policy_status: str
    priority_score: int
    rank: int
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_safety_policy(
    formal_verifier_agentic_proof_candidate_evaluation_queue_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export preflight safety policies for agentic proof candidate work."""

    errors: list[str] = []
    candidate_queue_manifest_path = (
        formal_verifier_agentic_proof_candidate_evaluation_queue_dir
        / "formal_verifier_agentic_proof_candidate_evaluation_queue_manifest.json"
    )
    candidate_queue_payload = _read_json(candidate_queue_manifest_path, errors)
    candidate_rows = [
        row for row in candidate_queue_payload.get("rows", []) if isinstance(row, dict)
    ]
    raw_rows = [_safety_policy_row(row) for row in candidate_rows]
    policy_rows = _rank_rows(raw_rows)
    by_generation_mode = Counter(row.generation_mode for row in policy_rows)
    by_status = Counter(row.policy_status for row in policy_rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_AGENTIC_PROOF_SAFETY_POLICY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_candidate_evaluation_queue_dir": str(
            formal_verifier_agentic_proof_candidate_evaluation_queue_dir
        ),
        "formal_verifier_agentic_proof_candidate_evaluation_queue_manifest": str(
            candidate_queue_manifest_path
        ),
        "n_candidate_queue_rows": len(candidate_rows),
        "n_safety_policy_rows": len(policy_rows),
        "n_ready": by_status.get("READY_FOR_SAFETY_GATED_CANDIDATE_GENERATION", 0),
        "n_blocked": sum(
            count for status, count in by_status.items() if status.startswith("BLOCKED_")
        ),
        "n_patch_bounded_edit_policies": by_generation_mode.get(
            "residual_patch_candidate_generation",
            0,
        ),
        "n_source_validation_policies": by_generation_mode.get(
            "source_discovery_candidate_generation",
            0,
        ),
        "n_with_goal_cache_key": sum(1 for row in policy_rows if row.goal_cache_key),
        "n_with_anti_cheat_checks": sum(1 for row in policy_rows if row.anti_cheat_checks),
        "n_with_safeverify_gate": sum(1 for row in policy_rows if row.safeverify_gate),
        "n_with_kernel_overlay_context": sum(
            1 for row in policy_rows if row.kernel_overlay_context
        ),
        "n_ok": sum(1 for row in policy_rows if row.ok),
        "all_ok": not errors and all(row.ok for row in policy_rows),
        "errors": errors,
        "by_generation_mode": dict(sorted(by_generation_mode.items())),
        "by_policy_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in policy_rows],
        "safety_policy_fingerprint": stable_hash([asdict(row) for row in policy_rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "safety policies are guardrails for candidate generation, not Lean theorem evidence",
            "bounded edit markers prevent broad source mutation but do not prove the target",
            "anti-cheat checks reject common proof-agent shortcuts before verifier promotion",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formal_verifier_agentic_proof_safety_policy_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formal_verifier_agentic_proof_safety_policy.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in policy_rows)
            + ("\n" if policy_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_agentic_proof_safety_policy.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _safety_policy_row(
    row: dict[str, Any],
) -> FormalVerifierAgenticProofSafetyPolicyRow:
    errors: list[str] = []
    candidate_evaluation_id = str(row.get("candidate_evaluation_id", ""))
    strategy_id = str(row.get("strategy_id", ""))
    followup_id = str(row.get("followup_id", ""))
    residual_obligation_id = str(row.get("residual_obligation_id", ""))
    generation_mode = str(row.get("generation_mode", ""))
    candidate_database_key = str(row.get("candidate_database_key", ""))
    candidate_lineage_key = str(row.get("candidate_lineage_key", ""))
    status = str(row.get("status", ""))
    queue_ok = bool(row.get("ok", False))
    evaluator_pool = _str_tuple(row.get("evaluator_pool", []))
    live_tool_sequence = _str_tuple(row.get("live_tool_sequence", []))
    kernel_overlay_context = row.get("kernel_overlay_context", {})
    if not isinstance(kernel_overlay_context, dict):
        kernel_overlay_context = {}

    for field_name, value in (
        ("candidate_evaluation_id", candidate_evaluation_id),
        ("strategy_id", strategy_id),
        ("followup_id", followup_id),
        ("residual_obligation_id", residual_obligation_id),
        ("generation_mode", generation_mode),
        ("candidate_database_key", candidate_database_key),
        ("candidate_lineage_key", candidate_lineage_key),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if not queue_ok:
        errors.append("candidate evaluation queue row is not ok")
    if status != "READY_FOR_CANDIDATE_GENERATION":
        errors.append(f"candidate evaluation queue row is not ready: {status}")
    if not evaluator_pool:
        errors.append("evaluator_pool missing")
    if (
        str(row.get("agentic_strategy_kind", ""))
        == "kernel_overlay_composition_patch_seed"
        and not kernel_overlay_context
    ):
        errors.append("kernel_overlay_context missing")

    goal_cache_key = "agentic_goal_cache:" + stable_hash(
        [
            row.get("target_theorem_name", ""),
            row.get("candidate_bridge_lemma_name", ""),
            row.get("residual_gap", ""),
            row.get("action_class", ""),
            generation_mode,
        ]
    )[:16]
    forbidden_tokens = (
        "sorry",
        "admit",
        "axiom",
        "unsafe",
        "set_option autoImplicit true",
    )
    statement_guard_policy = (
        "preserve theorem statement text and declaration header",
        "preserve namespace, imports, theorem name, and parameter binder order",
        "reject any helper lemma whose statement alpha-equivalently restates the target",
        "reject any source-discovery proof claim without a concrete importable declaration",
    )
    if generation_mode == "source_discovery_candidate_generation":
        bounded_edit_policy = {
            "bounded_edit_required": False,
            "reason": "source-discovery rows may add retrieval/source candidates but may not edit Lean proof bodies",
            "allowed_scope": "source registry and candidate-source metadata only",
            "forbidden_scope": "theorem proof body, theorem statement, declaration header",
        }
        source_claim_checks = (
            "each claimed known lemma must name a concrete declaration or source file",
            "each external source candidate must be marked source-only until imported and kernel checked",
            "source-discovery responses may not claim theorem closure",
        )
        required_static_checks = (
            "source candidate has non-empty query and source reference",
            "source candidate does not introduce proof status",
            "regenerated residual prompt packets include the source candidate",
        )
        required_dynamic_checks = tuple(
            dict.fromkeys(
                (
                    *live_tool_sequence,
                    "primitive-source coverage expansion",
                    "proof-bank source discovery refresh",
                )
            )
        )
        anti_cheat_checks = (
            "unknown_source_lemma_without_importable_declaration",
            "source_discovery_claims_kernel_verified",
            "retrieval_hit_marked_as_proof_evidence",
        )
        safeverify_gate = (
            "source candidates can only feed new proof work after source coverage "
            "refresh and regenerated residual prompt validation"
        )
    else:
        bounded_edit_policy = {
            "bounded_edit_required": True,
            "start_marker": EVOLVE_BLOCK_START,
            "end_marker": EVOLVE_BLOCK_END,
            "allowed_scope": "Lean proof body or explicitly marked local helper block only",
            "edits_outside_block": "reject",
            "missing_block_policy": "reject unless the candidate is generated as a patch artifact with an explicit declaration-header diff",
        }
        source_claim_checks = (
            "every referenced source lemma must be local, imported, or listed in proof-bank obligations",
            "unknown known-result claims remain source-discovery work, not proof work",
        )
        required_static_checks = (
            "bounded edit markers present or explicit declaration-header diff supplied",
            "no forbidden Lean placeholders or axiom declarations",
            "target theorem statement and declaration header unchanged",
            "helper lemma does not restate target theorem or residual goal",
            "candidate artifact records changed declarations",
        )
        required_dynamic_checks = tuple(
            dict.fromkeys(
                (
                    *live_tool_sequence,
                    "local Lean compile",
                    "patch-rerun calibration",
                    "residual-gap validation",
                )
            )
        )
        anti_cheat_checks = (
            "edit_outside_evolve_block",
            "target_restated_as_helper_lemma",
            "helper_lemma_contains_sorry_or_admit",
            "theorem_statement_or_header_changed",
            "hallucinated_known_source_lemma",
            "proof_evidence_claim_without_kernel_calibration",
        )
        safeverify_gate = (
            "candidate can be promoted only after statement/header guards pass, "
            "Lean kernel accepts the patched artifact, patch-rerun calibration is "
            "full_route_kernel_verified, and residual-gap validation reports no "
            "remaining formal gaps"
        )
        if kernel_overlay_context:
            bounded_edit_policy = {
                **bounded_edit_policy,
                "kernel_overlay_bounded_edit_contract": kernel_overlay_context.get(
                    "bounded_edit_contract",
                    {},
                ),
            }
            source_claim_checks = (
                *source_claim_checks,
                "already kernel-verified subclaims may be reused only as subclaim evidence",
                "each kernel-overlay target blocker must be materialized before source theorem promotion",
            )
            required_static_checks = (
                *required_static_checks,
                "candidate metadata lists kernel-overlay verified subclaims and target blockers",
            )
            required_dynamic_checks = tuple(
                dict.fromkeys(
                    (
                        *required_dynamic_checks,
                        "source discovery for kernel-overlay target blockers",
                    )
                )
            )
            safeverify_gate = (
                "kernel-overlay composition candidate can be promoted only after "
                "statement/header guards pass, each target_blocker is materialized, "
                "Lean kernel accepts the non-placeholder composed theorem, and "
                "patch-rerun calibration is full_route_kernel_verified"
            )

    policy_status = (
        "READY_FOR_SAFETY_GATED_CANDIDATE_GENERATION"
        if not errors
        else "BLOCKED_SAFETY_POLICY_INPUT"
    )
    safety_policy_id = "formal_verifier_agentic_proof_safety_policy:" + stable_hash(
        [candidate_evaluation_id, candidate_lineage_key, generation_mode]
    )[:16]

    return FormalVerifierAgenticProofSafetyPolicyRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_SAFETY_POLICY_SCHEMA_VERSION,
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
        candidate_database_key=candidate_database_key,
        candidate_lineage_key=candidate_lineage_key,
        goal_cache_key=goal_cache_key,
        kernel_overlay_context=kernel_overlay_context,
        bounded_edit_policy=bounded_edit_policy,
        statement_guard_policy=statement_guard_policy,
        forbidden_tokens=forbidden_tokens,
        anti_cheat_checks=anti_cheat_checks,
        source_claim_checks=source_claim_checks,
        required_static_checks=required_static_checks,
        required_dynamic_checks=required_dynamic_checks,
        safeverify_gate=safeverify_gate,
        policy_status=policy_status,
        priority_score=int(row.get("priority_score", 0)),
        rank=0,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _rank_rows(
    rows: list[FormalVerifierAgenticProofSafetyPolicyRow],
) -> list[FormalVerifierAgenticProofSafetyPolicyRow]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -row.priority_score,
            row.display_name,
            row.residual_gap,
            row.safety_policy_id,
        ),
    )
    return [
        FormalVerifierAgenticProofSafetyPolicyRow(
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
        "# Formal Verifier Agentic Proof Safety Policy",
        "",
        f"- Candidate evaluation queue manifest: `{payload.get('formal_verifier_agentic_proof_candidate_evaluation_queue_manifest')}`",
        f"- Safety policy rows: {payload.get('n_safety_policy_rows')}",
        f"- Ready: {payload.get('n_ready')}",
        f"- Blocked: {payload.get('n_blocked')}",
        f"- Patch bounded-edit policies: {payload.get('n_patch_bounded_edit_policies')}",
        f"- Source validation policies: {payload.get('n_source_validation_policies')}",
        f"- With goal cache key: {payload.get('n_with_goal_cache_key')}",
        f"- With anti-cheat checks: {payload.get('n_with_anti_cheat_checks')}",
        f"- With SafeVerify gate: {payload.get('n_with_safeverify_gate')}",
        f"- With kernel-overlay context: {payload.get('n_with_kernel_overlay_context')}",
        f"- All OK: {payload.get('all_ok')}",
        f"- Fingerprint: `{payload.get('safety_policy_fingerprint')}`",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary")),
        "",
        "## Policy Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        bounded = row.get("bounded_edit_policy", {})
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('policy_status')}): {row.get('generation_mode')}"
        )
        lines.append(f"  goal cache key: `{row.get('goal_cache_key')}`")
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
        lines.append(f"  bounded edit required: `{bounded.get('bounded_edit_required')}`")
        if bounded.get("start_marker"):
            lines.append(f"  markers: `{bounded.get('start_marker')}` / `{bounded.get('end_marker')}`")
        checks = ", ".join(f"`{item}`" for item in row.get("anti_cheat_checks", []))
        lines.append(f"  anti-cheat checks: {checks}")
        lines.append(f"  SafeVerify gate: {row.get('safeverify_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        if row.get("errors"):
            lines.append(f"  errors: {row.get('errors')}")
    return "\n".join(lines) + "\n"

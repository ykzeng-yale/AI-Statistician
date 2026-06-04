from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_STRATEGY_PLAN_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "AGENTIC_STRATEGY_PLAN_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic proof strategy rows are search/evaluator plans, not theorem proof "
    "evidence. A proposed proof becomes proof-relevant only after local Lean "
    "kernel verification, patch-rerun calibration, and residual-gap validation."
)


@dataclass(frozen=True)
class FormalVerifierAgenticProofStrategyPlanRow:
    schema_version: int
    strategy_id: str
    followup_id: str
    residual_response_validation_id: str
    prompt_packet_id: str
    residual_obligation_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    residual_gap: str
    action_class: str
    followup_kind: str
    followup_status: str
    agentic_strategy_kind: str
    paper_patterns: tuple[str, ...]
    required_live_tools: tuple[str, ...]
    evaluator_gates: tuple[str, ...]
    evolve_block_scope: dict[str, object]
    global_goal_cache_keys: tuple[str, ...]
    candidate_database_key: str
    expected_artifacts: tuple[str, ...]
    priority_score: int
    rank: int
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_strategy_plan(
    formal_verifier_replay_repair_patch_rerun_residual_followup_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    rag_collaboration_manifest: Path | None = None,
) -> dict[str, object]:
    """Plan live proof-search work from residual follow-up queue items.

    The plan converts operational residual work items into scoped strategy rows
    inspired by agentic prover systems: verifier-driven backtracking,
    proof-sketch/goal-cache reuse, and evaluator-gated evolve blocks. It never
    promotes an agent proposal to proof evidence.
    """

    errors: list[str] = []
    followup_manifest_path = (
        formal_verifier_replay_repair_patch_rerun_residual_followup_queue_dir
        / "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest.json"
    )
    followup_payload = _read_json(followup_manifest_path, errors)
    followup_rows = [
        row for row in followup_payload.get("rows", []) if isinstance(row, dict)
    ]
    rag_payload = (
        _read_json(rag_collaboration_manifest, errors)
        if rag_collaboration_manifest is not None
        else {}
    )
    kernel_overlay_seed_rows = _kernel_overlay_composition_seed_rows(rag_payload)
    raw_strategy_rows = [
        *[_strategy_row(row) for row in followup_rows],
        *[
            _strategy_row_from_kernel_overlay_seed(row)
            for row in kernel_overlay_seed_rows
        ],
    ]
    ranked_rows = _rank_rows(raw_strategy_rows)
    by_strategy_kind = Counter(row.agentic_strategy_kind for row in ranked_rows)
    by_followup_kind = Counter(row.followup_kind for row in ranked_rows)
    by_followup_status = Counter(row.followup_status for row in ranked_rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_AGENTIC_PROOF_STRATEGY_PLAN_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_dir": str(
            formal_verifier_replay_repair_patch_rerun_residual_followup_queue_dir
        ),
        "formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest": str(
            followup_manifest_path
        ),
        "rag_collaboration_manifest": (
            str(rag_collaboration_manifest) if rag_collaboration_manifest is not None else ""
        ),
        "paper_inspiration": [
            {
                "paper": "Ax-Prover",
                "pattern": (
                    "orchestrator/prover/verifier loop with verifier feedback, "
                    "backtracking, and live proof-state queries"
                ),
            },
            {
                "paper": "AlphaProof Nexus",
                "pattern": (
                    "proof-sketch population and global goal cache for reusable "
                    "partial proof states"
                ),
            },
            {
                "paper": "AlphaEvolve",
                "pattern": (
                    "scoped evolve blocks, evaluator pool, candidate database, "
                    "and score/lineage driven selection"
                ),
            },
        ],
        "n_followup_rows": len(followup_rows),
        "n_kernel_overlay_composition_seed_rows": len(kernel_overlay_seed_rows),
        "n_strategy_rows": len(ranked_rows),
        "n_ready": sum(1 for row in ranked_rows if row.followup_status.startswith("READY_")),
        "n_patch_evolve_blocks": by_strategy_kind.get("evolve_block_residual_patch", 0),
        "n_source_discovery_cache_items": by_strategy_kind.get(
            "global_goal_cache_source_discovery",
            0,
        ),
        "n_kernel_overlay_composition_seeds": by_strategy_kind.get(
            "kernel_overlay_composition_patch_seed",
            0,
        ),
        "n_with_live_tool_plan": sum(1 for row in ranked_rows if row.required_live_tools),
        "n_ok": sum(1 for row in ranked_rows if row.ok),
        "all_ok": not errors and all(row.ok for row in ranked_rows),
        "errors": errors,
        "by_agentic_strategy_kind": dict(sorted(by_strategy_kind.items())),
        "by_followup_kind": dict(sorted(by_followup_kind.items())),
        "by_followup_status": dict(sorted(by_followup_status.items())),
        "rows": [asdict(row) for row in ranked_rows],
        "strategy_plan_fingerprint": stable_hash([asdict(row) for row in ranked_rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "strategy rows describe search and evaluation contracts, not Lean theorem evidence",
            "kernel-overlay composition seeds are proof-worker routing artifacts, not theorem proof evidence",
            "external agent or MCP output is candidate-generation input only",
            "promotion still requires Lean/kernel/full-route residual validation gates",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_agentic_proof_strategy_plan_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formal_verifier_agentic_proof_strategy_plan.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in ranked_rows)
            + ("\n" if ranked_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_agentic_proof_strategy_plan.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _kernel_overlay_composition_seed_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    alignment = payload.get("kernel_proof_overlay_alignment", {})
    if not isinstance(alignment, dict):
        return []
    rows = alignment.get("kernel_overlay_composition_agentic_seed_preview", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _strategy_row_from_kernel_overlay_seed(
    row: dict[str, Any],
) -> FormalVerifierAgenticProofStrategyPlanRow:
    errors: list[str] = []
    seed_id = str(row.get("seed_id", ""))
    work_item_id = str(row.get("work_item_id", ""))
    packet_id = str(row.get("packet_id", ""))
    source_claim_id = str(row.get("source_claim_id", ""))
    question_id = str(row.get("question_id", ""))
    seed_status = str(row.get("seed_status", ""))
    strategy_kind = str(
        row.get("agentic_strategy_kind", "kernel_overlay_composition_patch_seed")
    )
    goal_cache_key = str(row.get("goal_cache_key", ""))
    candidate_database_key = str(row.get("candidate_database_key", ""))
    proof_sketch_population_key = str(row.get("proof_sketch_population_key", ""))
    kernel_subclaims = _str_tuple(row.get("already_kernel_verified_subclaims", []))
    target_blockers = _str_tuple(row.get("target_blockers", []))
    source_queries = _str_tuple(row.get("source_discovery_queries", []))
    required_live_tools = _str_tuple(row.get("required_live_tools", []))
    evaluator_gates = _str_tuple(row.get("evaluator_gates", []))
    bounded_edit_contract = row.get("bounded_edit_contract", {})
    if not isinstance(bounded_edit_contract, dict):
        bounded_edit_contract = {}
    generation_contract = _str_tuple(row.get("generation_contract", []))
    promotion_gate = str(row.get("promotion_gate", ""))

    for field_name, value in (
        ("seed_id", seed_id),
        ("work_item_id", work_item_id),
        ("packet_id", packet_id),
        ("source_claim_id", source_claim_id),
        ("seed_status", seed_status),
        ("goal_cache_key", goal_cache_key),
        ("candidate_database_key", candidate_database_key),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if seed_status != "READY_FOR_AGENTIC_COMPOSITION_ATTEMPT":
        errors.append(f"kernel overlay seed is not ready: {seed_status}")
    if not kernel_subclaims:
        errors.append("already_kernel_verified_subclaims missing")
    if target_blockers and not source_queries:
        errors.append("source_discovery_queries missing for target_blockers")
    if not required_live_tools:
        errors.append("required_live_tools missing")
    if not evaluator_gates:
        errors.append("evaluator_gates missing")
    if not bounded_edit_contract:
        errors.append("bounded_edit_contract missing")
    if not generation_contract:
        errors.append("generation_contract missing")
    if not promotion_gate:
        errors.append("promotion_gate missing")

    display_name = (
        f"{question_id}:kernel_overlay_composition"
        if question_id
        else source_claim_id or work_item_id
    )
    residual_gap = ", ".join(target_blockers) or "kernel_overlay_composition"
    score = 130 + min(25, 5 * len(kernel_subclaims)) - min(30, 5 * len(target_blockers))
    proof_boundary = str(row.get("proof_evidence_boundary", "")) or PROOF_EVIDENCE_BOUNDARY

    return FormalVerifierAgenticProofStrategyPlanRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_STRATEGY_PLAN_SCHEMA_VERSION,
        strategy_id=(
            "formal_verifier_agentic_proof_strategy:"
            + stable_hash([strategy_kind, seed_id, work_item_id, source_claim_id])[:16]
        ),
        followup_id=seed_id,
        residual_response_validation_id=seed_id,
        prompt_packet_id=packet_id,
        residual_obligation_id=work_item_id,
        display_name=display_name,
        target_theorem_name=source_claim_id,
        candidate_bridge_lemma_name="compose_kernel_overlay_subclaims",
        residual_gap=residual_gap,
        action_class="compose_kernel_overlay_verified_subclaims",
        followup_kind="kernel_overlay_composition",
        followup_status=seed_status,
        agentic_strategy_kind=strategy_kind,
        paper_patterns=(
            "alphaproof_nexus_sketch_population",
            "alphaproof_nexus_global_goal_cache",
            "alphaevolve_evolve_block_evaluator_database",
            "ax_prover_orchestrator_prover_verifier_loop",
            "lean_lsp_mcp_proof_state_provider",
        ),
        required_live_tools=required_live_tools,
        evaluator_gates=evaluator_gates,
        evolve_block_scope={
            "scope_kind": "kernel_overlay_composition_evolve_block",
            "seed_id": seed_id,
            "work_item_id": work_item_id,
            "packet_id": packet_id,
            "source_claim_id": source_claim_id,
            "question_id": question_id,
            "already_kernel_verified_subclaims": kernel_subclaims,
            "target_blockers": target_blockers,
            "source_discovery_queries": source_queries,
            "bounded_edit_contract": bounded_edit_contract,
            "generation_contract": generation_contract,
        },
        global_goal_cache_keys=tuple(
            item
            for item in (
                goal_cache_key,
                proof_sketch_population_key,
                f"source_claim:{source_claim_id}" if source_claim_id else "",
                f"question:{question_id}" if question_id else "",
                f"target_blockers:{'|'.join(target_blockers)}"
                if target_blockers
                else "",
            )
            if item
        ),
        candidate_database_key=candidate_database_key,
        expected_artifacts=(
            "candidate composed theorem Lean patch",
            "source-discovery manifest for target blockers",
            "AXLE/local Lean composed theorem verification manifest",
        ),
        priority_score=score,
        rank=0,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=proof_boundary,
        ok=not errors,
        errors=tuple(errors),
    )


def _strategy_row(
    row: dict[str, Any],
) -> FormalVerifierAgenticProofStrategyPlanRow:
    errors: list[str] = []
    followup_id = str(row.get("followup_id", ""))
    validation_id = str(row.get("residual_response_validation_id", ""))
    prompt_packet_id = str(row.get("prompt_packet_id", ""))
    residual_obligation_id = str(row.get("residual_obligation_id", ""))
    followup_kind = str(row.get("followup_kind", ""))
    followup_status = str(row.get("followup_status", ""))
    display_name = str(row.get("display_name", ""))
    residual_gap = str(row.get("residual_gap", ""))
    target = str(row.get("target_theorem_name", ""))
    bridge = str(row.get("candidate_bridge_lemma_name", ""))
    action_class = str(row.get("action_class", ""))

    for field_name, value in (
        ("followup_id", followup_id),
        ("residual_response_validation_id", validation_id),
        ("prompt_packet_id", prompt_packet_id),
        ("residual_obligation_id", residual_obligation_id),
        ("followup_status", followup_status),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if not followup_status.startswith("READY_"):
        errors.append(f"followup_status is not ready: {followup_status}")

    if followup_kind == "residual_source_discovery":
        strategy_kind = "global_goal_cache_source_discovery"
        paper_patterns = (
            "alphaproof_nexus_sketch_population",
            "alphaproof_nexus_global_goal_cache",
            "ax_prover_researcher_search_agent",
            "lean_lsp_mcp_proof_state_provider",
        )
        required_live_tools = (
            "lean_goal",
            "lean_diagnostic_messages",
            "lean_local_search",
            "lean_leansearch",
            "lean_loogle",
        )
        evaluator_gates = (
            "primitive-source coverage expansion",
            "proof-bank source discovery refresh",
            "residual prompt-packet regeneration",
            "residual response validation",
        )
        source_queries = _str_tuple(row.get("source_discovery_queries", []))
        if not source_queries:
            errors.append("source_discovery_queries missing")
        evolve_block_scope = {
            "scope_kind": "source_discovery_goal_cache",
            "source_discovery_queries": source_queries,
            "residual_gap": residual_gap,
            "action_class": action_class,
        }
        expected_artifacts = (
            "expanded primitive-source coverage manifest",
            "updated proof-bank source discovery candidates",
            "regenerated residual prompt packets",
        )
        score = 70 + min(10, len(source_queries) * 2)
    else:
        strategy_kind = "evolve_block_residual_patch"
        paper_patterns = (
            "alphaevolve_evolve_block_evaluator_database",
            "ax_prover_orchestrator_prover_verifier_loop",
            "alphaproof_nexus_proof_sketch_guided_agent",
            "lean_lsp_mcp_proof_state_provider",
        )
        required_live_tools = (
            "lean_goal",
            "lean_diagnostic_messages",
            "lean_hover",
            "lean_local_search",
            "lean_multi_attempt",
        )
        evaluator_gates = (
            "formal-verifier-replay-repair-patch-rerun-attempts",
            "formal-verifier-replay-repair-patch-rerun-calibration",
            "formal-verifier-replay-repair-patch-rerun-residual-response-validation",
            "full-route Lean kernel verification",
        )
        changed_declarations = _str_tuple(row.get("changed_lean_declarations", []))
        proof_bank_obligations = _str_tuple(row.get("used_proof_bank_obligations", []))
        artifact_path = str(row.get("proposed_lean_artifact_path", ""))
        if not artifact_path:
            errors.append("proposed_lean_artifact_path missing")
        if not bool(row.get("proposed_artifact_exists", False)):
            errors.append("proposed_artifact_exists is false")
        if not changed_declarations:
            errors.append("changed_lean_declarations missing")
        evolve_block_scope = {
            "scope_kind": "residual_patch_evolve_block",
            "proposed_lean_artifact_path": artifact_path,
            "changed_lean_declarations": changed_declarations,
            "used_proof_bank_obligations": proof_bank_obligations,
            "residual_gap": residual_gap,
            "action_class": action_class,
        }
        expected_artifacts = (
            artifact_path,
            "patch-rerun attempt manifest",
            "patch-rerun calibration manifest",
            "residual response validation manifest",
        )
        score = (
            100
            + (20 if bool(row.get("proposed_artifact_exists", False)) else 0)
            + min(10, len(changed_declarations) * 2)
            + min(10, len(proof_bank_obligations) * 2)
        )

    goal_cache_keys = tuple(
        item
        for item in (
            f"target:{target}" if target else "",
            f"bridge:{bridge}" if bridge else "",
            f"residual_gap:{residual_gap}" if residual_gap else "",
            f"action_class:{action_class}" if action_class else "",
            f"followup_kind:{followup_kind}" if followup_kind else "",
        )
        if item
    )
    candidate_database_key = "formal_proof_candidate:" + stable_hash(
        [strategy_kind, followup_id, prompt_packet_id, residual_obligation_id]
    )[:16]
    strategy_id = "formal_verifier_agentic_proof_strategy:" + stable_hash(
        [strategy_kind, followup_id, residual_gap, action_class]
    )[:16]

    return FormalVerifierAgenticProofStrategyPlanRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_STRATEGY_PLAN_SCHEMA_VERSION,
        strategy_id=strategy_id,
        followup_id=followup_id,
        residual_response_validation_id=validation_id,
        prompt_packet_id=prompt_packet_id,
        residual_obligation_id=residual_obligation_id,
        display_name=display_name,
        target_theorem_name=target,
        candidate_bridge_lemma_name=bridge,
        residual_gap=residual_gap,
        action_class=action_class,
        followup_kind=followup_kind,
        followup_status=followup_status,
        agentic_strategy_kind=strategy_kind,
        paper_patterns=paper_patterns,
        required_live_tools=required_live_tools,
        evaluator_gates=evaluator_gates,
        evolve_block_scope=evolve_block_scope,
        global_goal_cache_keys=goal_cache_keys,
        candidate_database_key=candidate_database_key,
        expected_artifacts=expected_artifacts,
        priority_score=score,
        rank=0,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _rank_rows(
    rows: list[FormalVerifierAgenticProofStrategyPlanRow],
) -> list[FormalVerifierAgenticProofStrategyPlanRow]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -row.priority_score,
            row.display_name,
            row.residual_gap,
            row.strategy_id,
        ),
    )
    return [
        FormalVerifierAgenticProofStrategyPlanRow(
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
        "# Formal Verifier Agentic Proof Strategy Plan",
        "",
        f"- Residual follow-up queue manifest: `{payload.get('formal_verifier_replay_repair_patch_rerun_residual_followup_queue_manifest')}`",
        f"- Strategy rows: {payload.get('n_strategy_rows')}",
        f"- Ready rows: {payload.get('n_ready')}",
        f"- Patch evolve blocks: {payload.get('n_patch_evolve_blocks')}",
        f"- Source-discovery cache items: {payload.get('n_source_discovery_cache_items')}",
        f"- Kernel-overlay composition seeds: {payload.get('n_kernel_overlay_composition_seeds')}",
        f"- Rows with live tool plan: {payload.get('n_with_live_tool_plan')}",
        f"- All OK: {payload.get('all_ok')}",
        f"- Fingerprint: `{payload.get('strategy_plan_fingerprint')}`",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary")),
        "",
        "## Strategy Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('agentic_strategy_kind')}, score={row.get('priority_score')})"
        )
        patterns = ", ".join(f"`{item}`" for item in row.get("paper_patterns", []))
        tools = ", ".join(f"`{item}`" for item in row.get("required_live_tools", []))
        gates = ", ".join(f"`{item}`" for item in row.get("evaluator_gates", []))
        lines.append(f"  patterns: {patterns}")
        lines.append(f"  live tools: {tools}")
        lines.append(f"  evaluator gates: {gates}")
        lines.append(f"  candidate database key: `{row.get('candidate_database_key')}`")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        if row.get("errors"):
            lines.append(f"  errors: {row.get('errors')}")
    return "\n".join(lines) + "\n"

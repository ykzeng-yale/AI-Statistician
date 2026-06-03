from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_CANDIDATE_EVALUATION_QUEUE_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "AGENTIC_PROOF_CANDIDATE_EVALUATION_QUEUE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic proof candidate evaluation queue rows are candidate-generation and "
    "evaluator-pool work orders, not theorem proof evidence. Candidate output "
    "becomes proof-relevant only after local Lean kernel verification, "
    "patch-rerun calibration, and residual-gap validation."
)


@dataclass(frozen=True)
class FormalVerifierAgenticProofCandidateEvaluationQueueRow:
    schema_version: int
    candidate_evaluation_id: str
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
    agentic_strategy_kind: str
    generation_mode: str
    candidate_database_key: str
    candidate_lineage_key: str
    attempt_budget: int
    evaluator_pool: tuple[str, ...]
    live_tool_sequence: tuple[str, ...]
    generation_contract: tuple[str, ...]
    safety_constraints: tuple[str, ...]
    promotion_gate: str
    expected_candidate_artifacts: tuple[str, ...]
    status: str
    priority_score: int
    rank: int
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_candidate_evaluation_queue(
    formal_verifier_agentic_proof_strategy_plan_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Queue candidate generation/evaluation work from agentic strategy rows."""

    errors: list[str] = []
    strategy_manifest_path = (
        formal_verifier_agentic_proof_strategy_plan_dir
        / "formal_verifier_agentic_proof_strategy_plan_manifest.json"
    )
    strategy_payload = _read_json(strategy_manifest_path, errors)
    strategy_rows = [
        row for row in strategy_payload.get("rows", []) if isinstance(row, dict)
    ]
    raw_rows = [_candidate_queue_row(row) for row in strategy_rows]
    queue_rows = _rank_rows(raw_rows)
    by_generation_mode = Counter(row.generation_mode for row in queue_rows)
    by_status = Counter(row.status for row in queue_rows)
    by_strategy_kind = Counter(row.agentic_strategy_kind for row in queue_rows)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_AGENTIC_PROOF_CANDIDATE_EVALUATION_QUEUE_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_strategy_plan_dir": str(
            formal_verifier_agentic_proof_strategy_plan_dir
        ),
        "formal_verifier_agentic_proof_strategy_plan_manifest": str(
            strategy_manifest_path
        ),
        "n_strategy_rows": len(strategy_rows),
        "n_candidate_queue_items": len(queue_rows),
        "n_ready": by_status.get("READY_FOR_CANDIDATE_GENERATION", 0),
        "n_blocked": sum(
            count for status, count in by_status.items() if status.startswith("BLOCKED_")
        ),
        "n_patch_candidate_items": by_generation_mode.get(
            "residual_patch_candidate_generation",
            0,
        ),
        "n_source_discovery_candidate_items": by_generation_mode.get(
            "source_discovery_candidate_generation",
            0,
        ),
        "n_with_candidate_database_key": sum(
            1 for row in queue_rows if row.candidate_database_key
        ),
        "n_with_live_evaluator_pool": sum(1 for row in queue_rows if row.evaluator_pool),
        "n_ok": sum(1 for row in queue_rows if row.ok),
        "all_ok": not errors and all(row.ok for row in queue_rows),
        "errors": errors,
        "by_generation_mode": dict(sorted(by_generation_mode.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_agentic_strategy_kind": dict(sorted(by_strategy_kind.items())),
        "rows": [asdict(row) for row in queue_rows],
        "candidate_evaluation_queue_fingerprint": stable_hash(
            [asdict(row) for row in queue_rows]
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "candidate queue rows are generation/evaluation work orders, not Lean theorem evidence",
            "candidate database keys are lineage handles, not proof-status handles",
            "promotion still requires Lean/kernel/full-route residual validation gates",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_agentic_proof_candidate_evaluation_queue_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir
            / "formal_verifier_agentic_proof_candidate_evaluation_queue.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in queue_rows)
            + ("\n" if queue_rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formal_verifier_agentic_proof_candidate_evaluation_queue.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _candidate_queue_row(
    row: dict[str, Any],
) -> FormalVerifierAgenticProofCandidateEvaluationQueueRow:
    errors: list[str] = []
    strategy_id = str(row.get("strategy_id", ""))
    followup_id = str(row.get("followup_id", ""))
    prompt_packet_id = str(row.get("prompt_packet_id", ""))
    residual_obligation_id = str(row.get("residual_obligation_id", ""))
    strategy_kind = str(row.get("agentic_strategy_kind", ""))
    strategy_ok = bool(row.get("ok", False))
    followup_status = str(row.get("followup_status", ""))
    candidate_database_key = str(row.get("candidate_database_key", ""))
    required_live_tools = _str_tuple(row.get("required_live_tools", []))
    evaluator_gates = _str_tuple(row.get("evaluator_gates", []))

    for field_name, value in (
        ("strategy_id", strategy_id),
        ("followup_id", followup_id),
        ("prompt_packet_id", prompt_packet_id),
        ("residual_obligation_id", residual_obligation_id),
        ("candidate_database_key", candidate_database_key),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if not strategy_ok:
        errors.append("strategy row is not ok")
    if not followup_status.startswith("READY_"):
        errors.append(f"strategy followup_status is not ready: {followup_status}")
    if not required_live_tools:
        errors.append("required_live_tools missing")
    if not evaluator_gates:
        errors.append("evaluator_gates missing")

    if strategy_kind == "global_goal_cache_source_discovery":
        generation_mode = "source_discovery_candidate_generation"
        attempt_budget = 3
        generation_contract = (
            "generate source-discovery candidates for each listed residual gap query",
            "attach candidate declarations or source references to the candidate database key",
            "rerun primitive-source coverage and residual prompt generation before any proof claim",
        )
        live_tool_sequence = tuple(
            item
            for item in (
                "lean_local_search",
                "lean_leansearch",
                "lean_loogle",
                "primitive-source coverage expansion",
                "proof-bank source discovery refresh",
                "residual prompt-packet regeneration",
            )
            if item
        )
        expected_candidate_artifacts = (
            "source-discovery candidate JSONL",
            "expanded primitive-source coverage manifest",
            "regenerated residual prompt packet manifest",
        )
        promotion_gate = (
            "source candidates may only become proof work after retrieval/source "
            "coverage is refreshed and residual prompt packets are regenerated"
        )
    else:
        generation_mode = "residual_patch_candidate_generation"
        attempt_budget = 5
        generation_contract = (
            "generate candidate Lean patch bodies scoped to the evolve_block_scope",
            "preserve theorem statements, namespaces, imports, and declaration headers",
            "evaluate candidates through live Lean diagnostics and patch-rerun calibration",
        )
        live_tool_sequence = tuple(
            item
            for item in (
                "lean_goal",
                "lean_diagnostic_messages",
                "lean_local_search",
                "lean_multi_attempt",
                "formal-verifier-replay-repair-patch-rerun-attempts",
                "formal-verifier-replay-repair-patch-rerun-calibration",
                "formal-verifier-replay-repair-patch-rerun-residual-response-validation",
            )
            if item
        )
        expected_candidate_artifacts = (
            "candidate Lean patch artifact",
            "patch-rerun attempt manifest",
            "patch-rerun calibration manifest",
            "residual response validation manifest",
        )
        promotion_gate = (
            "candidate is proof-relevant only if patch-rerun calibration reports "
            "full_route_kernel_verified with kernel_verified=true and no remaining "
            "residual formal gaps"
        )

    evaluator_pool = tuple(dict.fromkeys((*required_live_tools, *evaluator_gates)))
    safety_constraints = (
        "do not change theorem statements or declaration headers",
        "do not introduce axioms, sorry, admit, or placeholder proofs",
        "do not mark retrieval hits, agent output, or patch proposals as proof evidence",
        "record failed candidates with diagnostics for later policy learning",
    )
    status = (
        "READY_FOR_CANDIDATE_GENERATION"
        if not errors
        else "BLOCKED_CANDIDATE_GENERATION_INPUT"
    )
    candidate_lineage_key = "agentic_candidate_lineage:" + stable_hash(
        [candidate_database_key, strategy_id, generation_mode]
    )[:16]
    candidate_evaluation_id = (
        "formal_verifier_agentic_proof_candidate_evaluation:"
        + stable_hash([strategy_id, candidate_database_key, generation_mode])[:16]
    )

    return FormalVerifierAgenticProofCandidateEvaluationQueueRow(
        schema_version=(
            FORMAL_VERIFIER_AGENTIC_PROOF_CANDIDATE_EVALUATION_QUEUE_SCHEMA_VERSION
        ),
        candidate_evaluation_id=candidate_evaluation_id,
        strategy_id=strategy_id,
        followup_id=followup_id,
        residual_response_validation_id=str(row.get("residual_response_validation_id", "")),
        prompt_packet_id=prompt_packet_id,
        residual_obligation_id=residual_obligation_id,
        display_name=str(row.get("display_name", "")),
        target_theorem_name=str(row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(row.get("candidate_bridge_lemma_name", "")),
        residual_gap=str(row.get("residual_gap", "")),
        action_class=str(row.get("action_class", "")),
        agentic_strategy_kind=strategy_kind,
        generation_mode=generation_mode,
        candidate_database_key=candidate_database_key,
        candidate_lineage_key=candidate_lineage_key,
        attempt_budget=attempt_budget,
        evaluator_pool=evaluator_pool,
        live_tool_sequence=live_tool_sequence,
        generation_contract=generation_contract,
        safety_constraints=safety_constraints,
        promotion_gate=promotion_gate,
        expected_candidate_artifacts=expected_candidate_artifacts,
        status=status,
        priority_score=int(row.get("priority_score", 0)),
        rank=0,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _rank_rows(
    rows: list[FormalVerifierAgenticProofCandidateEvaluationQueueRow],
) -> list[FormalVerifierAgenticProofCandidateEvaluationQueueRow]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -row.priority_score,
            row.display_name,
            row.residual_gap,
            row.candidate_evaluation_id,
        ),
    )
    return [
        FormalVerifierAgenticProofCandidateEvaluationQueueRow(
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
        "# Formal Verifier Agentic Proof Candidate Evaluation Queue",
        "",
        f"- Strategy plan manifest: `{payload.get('formal_verifier_agentic_proof_strategy_plan_manifest')}`",
        f"- Candidate queue items: {payload.get('n_candidate_queue_items')}",
        f"- Ready: {payload.get('n_ready')}",
        f"- Blocked: {payload.get('n_blocked')}",
        f"- Patch candidate items: {payload.get('n_patch_candidate_items')}",
        f"- Source-discovery candidate items: {payload.get('n_source_discovery_candidate_items')}",
        f"- With candidate database key: {payload.get('n_with_candidate_database_key')}",
        f"- With live evaluator pool: {payload.get('n_with_live_evaluator_pool')}",
        f"- All OK: {payload.get('all_ok')}",
        f"- Fingerprint: `{payload.get('candidate_evaluation_queue_fingerprint')}`",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary")),
        "",
        "## Queue Items",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
            f"({row.get('status')}): {row.get('generation_mode')}"
        )
        evaluators = ", ".join(f"`{item}`" for item in row.get("evaluator_pool", []))
        sequence = ", ".join(f"`{item}`" for item in row.get("live_tool_sequence", []))
        lines.append(f"  candidate DB key: `{row.get('candidate_database_key')}`")
        lines.append(f"  lineage key: `{row.get('candidate_lineage_key')}`")
        lines.append(f"  attempt budget: {row.get('attempt_budget')}")
        lines.append(f"  evaluator pool: {evaluators}")
        lines.append(f"  live tool sequence: {sequence}")
        lines.append(f"  promotion gate: {row.get('promotion_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        if row.get("errors"):
            lines.append(f"  errors: {row.get('errors')}")
    return "\n".join(lines) + "\n"

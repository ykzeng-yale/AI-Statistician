from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_QUEUE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierQueueRow:
    schema_version: int
    item_id: str
    route_id: str
    task_id: str
    question_id: str
    problem_class: str
    theorem_goal_id: str
    display_name: str
    theorem_skeleton: str
    route_class: str
    verification_stage: str
    owner_agent: str
    priority: str
    priority_rank: int
    priority_score: int
    recommended_action: str
    required_gate: str
    proof_attempt_mode: str
    total_estimated_cost: int
    max_primitive_cost: int
    source_support_count: int
    required_primitives: tuple[str, ...]
    first_next_actions: tuple[str, ...]
    proof_search_no_registered_candidate_delta: int
    proof_search_no_registered_solved_delta: int
    lean_rag_dependency_graph_enabled: bool
    kernel_smoke_total: int
    kernel_smoke_kernel_verified: int
    route_evidence_boundary: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_queue(
    formalization_delta_dir: Path,
    out_dir: Path | None = None,
    *,
    proof_search_no_registered_ablation_dir: Path | None = None,
    kernel_smoke_proof_audit_dir: Path | None = None,
    max_routes: int = 20,
) -> dict[str, object]:
    """Export theorem-route work items for the FormalVerifier.

    The queue joins the formalization delta plan with the hard-mode proof-search
    retrieval diagnostic. Rows are task contracts: they are not Lean proof
    evidence until the required AXLE/local Lean gate succeeds.
    """

    errors: list[str] = []
    delta_manifest_path = formalization_delta_dir / "formalization_delta_plan_manifest.json"
    delta_manifest = _read_json(delta_manifest_path, errors)
    no_registered_manifest_path = (
        proof_search_no_registered_ablation_dir / "proof_search_retrieval_ablation_manifest.json"
        if proof_search_no_registered_ablation_dir is not None
        else Path("__missing__")
    )
    no_registered_manifest = (
        _read_json(no_registered_manifest_path, errors)
        if proof_search_no_registered_ablation_dir is not None
        else {}
    )
    kernel_manifest_path = (
        kernel_smoke_proof_audit_dir / "proof_audit_manifest.json"
        if kernel_smoke_proof_audit_dir is not None
        else Path("__missing__")
    )
    kernel_manifest = (
        _read_json(kernel_manifest_path, errors)
        if kernel_smoke_proof_audit_dir is not None
        else {}
    )

    routes = [
        row
        for row in delta_manifest.get("theorem_formalization_routes", [])
        if isinstance(row, dict)
    ]
    rows = [
        _row_from_route(
            route,
            no_registered_manifest=no_registered_manifest,
            kernel_manifest=kernel_manifest,
        )
        for route in routes
    ]
    rows = sorted(rows, key=lambda row: (-row.priority_score, row.priority_rank, row.item_id))[
        : max(0, max_routes)
    ]
    by_priority = Counter(row.priority for row in rows)
    by_route_class = Counter(row.route_class for row in rows)
    by_stage = Counter(row.verification_stage for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_QUEUE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formalization_delta_dir": str(formalization_delta_dir),
        "formalization_delta_manifest": str(delta_manifest_path),
        "proof_search_no_registered_ablation_dir": str(proof_search_no_registered_ablation_dir or ""),
        "proof_search_no_registered_ablation_manifest": str(no_registered_manifest_path)
        if proof_search_no_registered_ablation_dir is not None
        else "",
        "kernel_smoke_proof_audit_dir": str(kernel_smoke_proof_audit_dir or ""),
        "kernel_smoke_proof_audit_manifest": str(kernel_manifest_path)
        if kernel_smoke_proof_audit_dir is not None
        else "",
        "n_source_theorem_routes": len(routes),
        "n_items": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "by_priority": dict(sorted(by_priority.items())),
        "by_route_class": dict(sorted(by_route_class.items())),
        "by_verification_stage": dict(sorted(by_stage.items())),
        "n_high_priority": by_priority.get("high", 0),
        "n_reuse_or_composition": by_route_class.get("reuse_or_composition", 0),
        "n_bridge_or_wrapper": by_route_class.get("bridge_or_wrapper", 0),
        "n_requires_new_theory": by_route_class.get("requires_new_theory", 0),
        "n_routes_with_no_registered_rag_lift": sum(
            1 for row in rows if row.proof_search_no_registered_candidate_delta > 0
        ),
        "no_registered_rag_candidate_delta": int(
            no_registered_manifest.get("formal_source_candidate_delta", 0) or 0
        ),
        "no_registered_rag_solved_delta": int(no_registered_manifest.get("solved_delta", 0) or 0),
        "no_registered_rag_include_registered_proof": bool(
            no_registered_manifest.get("include_registered_proof", True)
        )
        if no_registered_manifest
        else None,
        "lean_rag_dependency_graph_enabled": bool(
            no_registered_manifest.get("lean_rag_dependency_graph_enabled", False)
        ),
        "kernel_smoke_total": int(kernel_manifest.get("n_obligations", 0) or 0),
        "kernel_smoke_kernel_verified": int(kernel_manifest.get("n_kernel_verified", 0) or 0),
        "rows": [asdict(row) for row in rows],
        "queue_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "formal verifier queue rows are task contracts, not Lean proof evidence",
            "no-registered proof-search deltas are search/frontier evidence only",
            "kernel smoke proves only the selected registered subclaims, not the queued theorem routes",
            "queued theorem routes remain formal gaps until AXLE/local Lean verifies a non-placeholder proof",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_verifier_queue_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_queue.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_queue.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _row_from_route(
    route: dict[str, Any],
    *,
    no_registered_manifest: dict[str, Any],
    kernel_manifest: dict[str, Any],
) -> FormalVerifierQueueRow:
    errors: list[str] = []
    route_id = str(route.get("route_id", ""))
    task_id = str(route.get("task_id", ""))
    route_class = str(route.get("route_class", ""))
    actions = [row for row in route.get("actions", []) if isinstance(row, dict)]
    action_classes = {str(row.get("action_class", "")) for row in actions}
    verification_stage = _verification_stage(route_class, action_classes)
    priority_score = _priority_score(route, verification_stage, no_registered_manifest)
    priority = _priority_label(priority_score, verification_stage)
    first_next_actions = tuple(
        str(row.get("next_step", ""))
        for row in route.get("first_next_actions", [])
        if isinstance(row, dict) and str(row.get("next_step", ""))
    )[:5]
    required_primitives = tuple(
        str(item) for item in route.get("required_primitives", []) or [] if str(item)
    )
    if not route_id:
        errors.append("route_id missing")
    if not task_id:
        errors.append("task_id missing")
    if route_class not in {"reuse_or_composition", "bridge_or_wrapper", "requires_new_theory"}:
        errors.append(f"unknown route_class={route_class}")
    if not required_primitives:
        errors.append("required_primitives missing")
    return FormalVerifierQueueRow(
        schema_version=FORMAL_VERIFIER_QUEUE_SCHEMA_VERSION,
        item_id=f"formal_verifier_queue:{stable_hash([route_id, task_id])[:12]}",
        route_id=route_id,
        task_id=task_id,
        question_id=str(route.get("question_id", "")),
        problem_class=str(route.get("problem_class", "")),
        theorem_goal_id=str(route.get("theorem_goal_id", "")),
        display_name=str(route.get("display_name", "")),
        theorem_skeleton=str(route.get("theorem_skeleton", "")),
        route_class=route_class,
        verification_stage=verification_stage,
        owner_agent="formal_verifier",
        priority=priority,
        priority_rank={"high": 0, "medium": 1, "low": 2}.get(priority, 3),
        priority_score=priority_score,
        recommended_action=_recommended_action(verification_stage),
        required_gate=_required_gate(verification_stage),
        proof_attempt_mode=_proof_attempt_mode(verification_stage),
        total_estimated_cost=int(route.get("total_estimated_cost", 0) or 0),
        max_primitive_cost=int(route.get("max_primitive_cost", 0) or 0),
        source_support_count=int(route.get("source_support_count", 0) or 0),
        required_primitives=required_primitives,
        first_next_actions=first_next_actions,
        proof_search_no_registered_candidate_delta=int(
            no_registered_manifest.get("formal_source_candidate_delta", 0) or 0
        ),
        proof_search_no_registered_solved_delta=int(no_registered_manifest.get("solved_delta", 0) or 0),
        lean_rag_dependency_graph_enabled=bool(
            no_registered_manifest.get("lean_rag_dependency_graph_enabled", False)
        ),
        kernel_smoke_total=int(kernel_manifest.get("n_obligations", 0) or 0),
        kernel_smoke_kernel_verified=int(kernel_manifest.get("n_kernel_verified", 0) or 0),
        route_evidence_boundary=str(route.get("evidence_boundary", "")),
        proof_evidence_boundary=(
            "This queue row is not proof evidence. It becomes proof evidence only when a "
            "non-placeholder proof for the referenced theorem route passes AXLE/local Lean."
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _verification_stage(route_class: str, action_classes: set[str]) -> str:
    if route_class == "requires_new_theory":
        return "new_theory_bridge_development"
    if "design_bridge_lemma" in action_classes or "add_minimal_wrapper" in action_classes:
        return "verify_bridge_or_wrapper"
    if "compose_existing_bridge_chain" in action_classes:
        return "compose_bridge_chain"
    if action_classes == {"reuse_exact_proof_bank_obligation"}:
        return "compose_exact_reuse_skeleton"
    return "route_triage"


def _priority_score(
    route: dict[str, Any],
    verification_stage: str,
    no_registered_manifest: dict[str, Any],
) -> int:
    base = {
        "compose_exact_reuse_skeleton": 300,
        "compose_bridge_chain": 260,
        "verify_bridge_or_wrapper": 220,
        "new_theory_bridge_development": 180,
    }.get(verification_stage, 120)
    cost = int(route.get("total_estimated_cost", 0) or 0)
    support_bonus = min(30, int(route.get("source_support_count", 0) or 0) // 10)
    rag_bonus = min(20, 5 * int(no_registered_manifest.get("formal_source_candidate_delta", 0) or 0))
    proof_step_bonus = min(10, int(route.get("n_informal_proof_steps", 0) or 0))
    return base + support_bonus + rag_bonus + proof_step_bonus - cost


def _priority_label(priority_score: int, verification_stage: str) -> str:
    if verification_stage == "compose_exact_reuse_skeleton":
        return "high"
    if priority_score >= 230:
        return "high"
    if priority_score >= 180:
        return "medium"
    return "low"


def _recommended_action(verification_stage: str) -> str:
    return {
        "compose_exact_reuse_skeleton": (
            "attempt a non-placeholder theorem proof by composing exact verified proof-bank obligations"
        ),
        "compose_bridge_chain": (
            "compose existing bridge-chain obligations into the theorem skeleton and run AXLE/local Lean"
        ),
        "verify_bridge_or_wrapper": (
            "verify the smallest bridge/wrapper lemma first, then retry the theorem skeleton"
        ),
        "new_theory_bridge_development": (
            "split the route into one bridge lemma per missing primitive and verify the first reusable lemma"
        ),
    }.get(verification_stage, "triage the theorem route before proof search")


def _required_gate(verification_stage: str) -> str:
    if verification_stage == "new_theory_bridge_development":
        return "at least one reusable bridge lemma passes AXLE/local Lean, then route is re-queued"
    return "non-placeholder theorem or bridge proof passes AXLE/local Lean verify_proof"


def _proof_attempt_mode(verification_stage: str) -> str:
    if verification_stage in {"compose_exact_reuse_skeleton", "compose_bridge_chain"}:
        return "theorem_composition_first"
    if verification_stage == "verify_bridge_or_wrapper":
        return "bridge_or_wrapper_first"
    return "primitive_bridge_first"


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {path}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
        return {}
    return data if isinstance(data, dict) else {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Queue",
        "",
        f"- Formalization delta: `{payload.get('formalization_delta_manifest')}`",
        f"- Items: {payload.get('n_ok')}/{payload.get('n_items')}",
        f"- No-registered RAG candidate delta: `{payload.get('no_registered_rag_candidate_delta')}`",
        f"- Kernel smoke: `{payload.get('kernel_smoke_kernel_verified')}/{payload.get('kernel_smoke_total')}`",
        "",
        "## Stage Counts",
        "",
    ]
    by_stage = payload.get("by_verification_stage", {})
    if isinstance(by_stage, dict) and by_stage:
        for stage, count in sorted(by_stage.items()):
            lines.append(f"- `{stage}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Queue", ""])
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### {row.get('display_name')} [{row.get('priority')}]",
                "",
                f"- Stage: `{row.get('verification_stage')}`",
                f"- Route class: `{row.get('route_class')}`",
                f"- Cost: `{row.get('total_estimated_cost')}`",
                f"- Required gate: {row.get('required_gate')}",
                f"- Recommended action: {row.get('recommended_action')}",
                "- Required primitives: "
                + ", ".join(f"`{item}`" for item in row.get("required_primitives", [])[:10]),
                f"- Boundary: {row.get('proof_evidence_boundary')}",
                "",
            ]
        )
    if not payload.get("rows"):
        lines.append("No verifier queue rows emitted.")
    return "\n".join(lines) + "\n"

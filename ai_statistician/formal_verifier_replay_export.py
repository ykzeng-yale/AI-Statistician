from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayTask:
    schema_version: int
    replay_id: str
    source_queue_item_id: str
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
    queue_priority_score: int
    replay_priority_score: int
    replay_mode: str
    acceptance_gate: str
    proof_attempt_mode: str
    required_primitives: tuple[str, ...]
    related_proof_obligations: tuple[str, ...]
    subclaim_replay_obligations: tuple[str, ...]
    kernel_smoke_related_obligations: tuple[str, ...]
    kernel_smoke_related_verified: int
    kernel_smoke_related_total: int
    source_trust_calibration_status: str
    dependency_graph_depth: int
    dependency_graph_neighborhood_nodes: int
    import_cone_size: int
    source_trust_level: str
    semantic_faithfulness_score: int
    semantic_faithfulness_status: str
    semantic_review_notes: tuple[str, ...]
    proof_attempt_positive: int
    proof_attempt_negative: int
    proof_attempt_kernel_verified: int
    proof_search_solved: int
    proof_search_unsolved: int
    proof_search_kernel_verified: int
    proof_search_selected_sources: tuple[str, ...]
    proof_history_status: str
    replay_steps: tuple[str, ...]
    training_prompt: str
    training_completion: str
    required_kernel_boundary: str
    subclaim_calibration_boundary: str
    proof_history_boundary: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay(
    formal_verifier_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    max_tasks: int = 20,
) -> dict[str, object]:
    """Export route-level replay tasks for the FormalVerifier.

    Replay tasks turn ranked theorem-route queue rows into concrete next proof
    attempts. They remain task/training artifacts: they are not theorem proof
    evidence until a non-placeholder theorem or bridge proof passes AXLE/local
    Lean.
    """

    errors: list[str] = []
    manifest_path = formal_verifier_queue_dir / "formal_verifier_queue_manifest.json"
    queue_payload = _read_json(manifest_path, errors)
    queue_rows = [
        row
        for row in queue_payload.get("rows", [])
        if isinstance(row, dict)
    ]
    tasks = [_task_from_queue_row(row) for row in queue_rows]
    tasks = sorted(
        tasks,
        key=lambda row: (-row.replay_priority_score, -row.queue_priority_score, row.replay_id),
    )[: max(0, max_tasks)]
    by_mode = Counter(task.replay_mode for task in tasks)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_queue_dir": str(formal_verifier_queue_dir),
        "formal_verifier_queue_manifest": str(manifest_path),
        "queue_schema_version": queue_payload.get("schema_version"),
        "queue_fingerprint": queue_payload.get("queue_fingerprint", ""),
        "n_queue_items": queue_payload.get("n_items", len(queue_rows)),
        "n_replay_tasks": len(tasks),
        "n_ok": sum(1 for task in tasks if task.ok),
        "all_ok": not errors and bool(tasks) and all(task.ok for task in tasks),
        "errors": errors,
        "by_replay_mode": dict(sorted(by_mode.items())),
        "n_kernel_calibrated": by_mode.get(
            "kernel_calibrated_subclaim_replay_then_theorem_composition",
            0,
        ),
        "n_proof_search_subclaim_replay": by_mode.get(
            "proof_search_subclaim_replay_then_compose",
            0,
        ),
        "n_bridge_lemma_replay": by_mode.get("bridge_lemma_replay_then_requeue", 0),
        "n_semantic_review": by_mode.get("semantic_route_review_before_replay", 0),
        "n_training_examples": len(tasks),
        "n_subclaim_replay_obligations": len(
            {obligation for task in tasks for obligation in task.subclaim_replay_obligations}
        ),
        "n_kernel_smoke_related_verified": sum(
            task.kernel_smoke_related_verified for task in tasks
        ),
        "tasks": [asdict(task) for task in tasks],
        "task_fingerprint": stable_hash([asdict(task) for task in tasks]),
        "limitations": [
            "formal verifier replay tasks are not Lean proof evidence",
            "subclaim replay can calibrate proof-search behavior but cannot prove the queued theorem route",
            "kernel-smoke overlap verifies only related proof-bank subclaims, not the replay target theorem",
            "a replay task closes only after a non-placeholder theorem or bridge proof passes AXLE/local Lean",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_verifier_replay_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_tasks.jsonl").write_text(
            "\n".join(json.dumps(asdict(task), sort_keys=True) for task in tasks)
            + ("\n" if tasks else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_training.jsonl").write_text(
            "\n".join(
                json.dumps(
                    {
                        "example_id": task.replay_id,
                        "task": "formal_verifier_route_replay_policy",
                        "prompt": task.training_prompt,
                        "completion": task.training_completion,
                        "source_queue_item_id": task.source_queue_item_id,
                        "replay_mode": task.replay_mode,
                    },
                    sort_keys=True,
                )
                for task in tasks
            )
            + ("\n" if tasks else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _task_from_queue_row(row: dict[str, Any]) -> FormalVerifierReplayTask:
    errors: list[str] = []
    source_queue_item_id = str(row.get("item_id", ""))
    route_id = str(row.get("route_id", ""))
    task_id = str(row.get("task_id", ""))
    display_name = str(row.get("display_name", ""))
    acceptance_gate = str(row.get("required_gate", ""))
    replay_mode = _replay_mode(row)
    subclaim_obligations = _subclaim_replay_obligations(row)
    replay_steps = _replay_steps(row, replay_mode, subclaim_obligations)
    proof_evidence_boundary = (
        "This replay task is not proof evidence. It becomes evidence only when "
        "a non-placeholder theorem or bridge proof for the target route passes "
        "AXLE/local Lean."
    )
    if not source_queue_item_id:
        errors.append("source queue item_id missing")
    if not route_id:
        errors.append("route_id missing")
    if not display_name:
        errors.append("display_name missing")
    if not acceptance_gate:
        errors.append("acceptance_gate missing")
    if not subclaim_obligations and replay_mode not in {
        "semantic_route_review_before_replay",
        "bridge_lemma_replay_then_requeue",
    }:
        errors.append("subclaim replay obligations missing")
    training_completion = json.dumps(
        {
            "replay_mode": replay_mode,
            "replay_steps": list(replay_steps),
            "acceptance_gate": acceptance_gate,
            "claim_status": "task_contract_not_proof_evidence",
            "proof_evidence_boundary": proof_evidence_boundary,
        },
        sort_keys=True,
    )
    return FormalVerifierReplayTask(
        schema_version=FORMAL_VERIFIER_REPLAY_SCHEMA_VERSION,
        replay_id=f"formal_verifier_replay:{stable_hash([source_queue_item_id, replay_mode])[:16]}",
        source_queue_item_id=source_queue_item_id,
        route_id=route_id,
        task_id=task_id,
        question_id=str(row.get("question_id", "")),
        problem_class=str(row.get("problem_class", "")),
        theorem_goal_id=str(row.get("theorem_goal_id", "")),
        display_name=display_name,
        theorem_skeleton=str(row.get("theorem_skeleton", "")),
        route_class=str(row.get("route_class", "")),
        verification_stage=str(row.get("verification_stage", "")),
        owner_agent="formal_verifier",
        priority=str(row.get("priority", "")),
        queue_priority_score=int(row.get("priority_score", 0) or 0),
        replay_priority_score=_replay_priority_score(row, replay_mode),
        replay_mode=replay_mode,
        acceptance_gate=acceptance_gate,
        proof_attempt_mode=str(row.get("proof_attempt_mode", "")),
        required_primitives=_str_tuple(row.get("required_primitives", [])),
        related_proof_obligations=_str_tuple(row.get("related_proof_obligations", [])),
        subclaim_replay_obligations=subclaim_obligations,
        kernel_smoke_related_obligations=_str_tuple(row.get("kernel_smoke_related_obligations", [])),
        kernel_smoke_related_verified=int(row.get("kernel_smoke_related_verified", 0) or 0),
        kernel_smoke_related_total=int(row.get("kernel_smoke_related_total", 0) or 0),
        source_trust_calibration_status=str(row.get("source_trust_calibration_status", "")),
        dependency_graph_depth=int(row.get("dependency_graph_depth", 0) or 0),
        dependency_graph_neighborhood_nodes=int(
            row.get("dependency_graph_neighborhood_nodes", 0) or 0
        ),
        import_cone_size=int(row.get("import_cone_size", 0) or 0),
        source_trust_level=str(row.get("source_trust_level", "")),
        semantic_faithfulness_score=int(row.get("semantic_faithfulness_score", 0) or 0),
        semantic_faithfulness_status=str(row.get("semantic_faithfulness_status", "")),
        semantic_review_notes=_str_tuple(row.get("semantic_review_notes", [])),
        proof_attempt_positive=int(row.get("proof_attempt_positive", 0) or 0),
        proof_attempt_negative=int(row.get("proof_attempt_negative", 0) or 0),
        proof_attempt_kernel_verified=int(row.get("proof_attempt_kernel_verified", 0) or 0),
        proof_search_solved=int(row.get("proof_search_solved", 0) or 0),
        proof_search_unsolved=int(row.get("proof_search_unsolved", 0) or 0),
        proof_search_kernel_verified=int(row.get("proof_search_kernel_verified", 0) or 0),
        proof_search_selected_sources=_str_tuple(row.get("proof_search_selected_sources", [])),
        proof_history_status=str(row.get("proof_history_status", "")),
        replay_steps=replay_steps,
        training_prompt=_training_prompt(row, replay_mode, subclaim_obligations),
        training_completion=training_completion,
        required_kernel_boundary=(
            "The acceptance gate requires AXLE/local Lean on the replay target. "
            "Queue rank, RAG lift, proof-search history, and kernel-smoke overlap "
            "are planning signals only."
        ),
        subclaim_calibration_boundary=str(
            row.get(
                "source_trust_calibration_boundary",
                "Subclaim calibration does not prove the theorem route.",
            )
        ),
        proof_history_boundary=str(
            row.get(
                "proof_history_boundary",
                "Proof history is subclaim feedback, not theorem proof evidence.",
            )
        ),
        proof_evidence_boundary=proof_evidence_boundary,
        ok=not errors,
        errors=tuple(errors),
    )


def _replay_mode(row: dict[str, Any]) -> str:
    if (
        str(row.get("source_trust_calibration_status", ""))
        == "kernel_smoke_overlap_verified"
        and int(row.get("kernel_smoke_related_verified", 0) or 0) > 0
    ):
        return "kernel_calibrated_subclaim_replay_then_theorem_composition"
    if int(row.get("proof_search_solved", 0) or 0) > 0:
        return "proof_search_subclaim_replay_then_compose"
    if str(row.get("route_class", "")) == "requires_new_theory":
        return "bridge_lemma_replay_then_requeue"
    if str(row.get("semantic_faithfulness_status", "")) == "needs_review":
        return "semantic_route_review_before_replay"
    if str(row.get("proof_attempt_mode", "")) == "bridge_or_wrapper_first":
        return "bridge_or_wrapper_replay_first"
    return "theorem_composition_replay_first"


def _replay_priority_score(row: dict[str, Any], replay_mode: str) -> int:
    score = int(row.get("priority_score", 0) or 0)
    score += {
        "kernel_calibrated_subclaim_replay_then_theorem_composition": 40,
        "proof_search_subclaim_replay_then_compose": 25,
        "bridge_or_wrapper_replay_first": 10,
        "theorem_composition_replay_first": 8,
        "bridge_lemma_replay_then_requeue": 5,
        "semantic_route_review_before_replay": -15,
    }.get(replay_mode, 0)
    score += min(10, int(row.get("proof_attempt_positive", 0) or 0))
    score -= min(10, int(row.get("proof_attempt_negative", 0) or 0))
    return score


def _subclaim_replay_obligations(row: dict[str, Any]) -> tuple[str, ...]:
    kernel_obligations = _str_tuple(row.get("kernel_smoke_related_obligations", []))
    if kernel_obligations:
        return kernel_obligations[:8]
    related = _str_tuple(row.get("related_proof_obligations", []))
    if related:
        return related[:8]
    return _str_tuple(row.get("required_primitives", []))[:8]


def _replay_steps(
    row: dict[str, Any],
    replay_mode: str,
    subclaim_obligations: tuple[str, ...],
) -> tuple[str, ...]:
    subclaim_text = ", ".join(subclaim_obligations) if subclaim_obligations else "none"
    if replay_mode == "kernel_calibrated_subclaim_replay_then_theorem_composition":
        first = (
            "replay the kernel-smoke verified related subclaims under local Lean: "
            f"{subclaim_text}"
        )
    elif replay_mode == "proof_search_subclaim_replay_then_compose":
        first = (
            "replay the proof-search solved related subclaims and preserve the first "
            f"successful proof source: {subclaim_text}"
        )
    elif replay_mode == "bridge_lemma_replay_then_requeue":
        first = (
            "develop the smallest reusable bridge lemma for the first missing primitive, "
            "then requeue the theorem route"
        )
    elif replay_mode == "semantic_route_review_before_replay":
        first = (
            "review the theorem skeleton against the informal theorem and source hits "
            "before starting proof replay"
        )
    elif replay_mode == "bridge_or_wrapper_replay_first":
        first = "attempt the bridge or wrapper lemma before retrying the theorem skeleton"
    else:
        first = "attempt theorem composition from the ranked related proof obligations"
    return (
        first,
        "compose replayed subclaims into the theorem skeleton or the smallest bridge lemma",
        "run AXLE/local Lean on a non-placeholder proof body for the replay target",
        "if Lean fails, preserve the earliest error, negative candidates, and selected sources for repair",
        f"do not mark the route proved unless the acceptance gate passes: {row.get('required_gate', '')}",
    )


def _training_prompt(
    row: dict[str, Any],
    replay_mode: str,
    subclaim_obligations: tuple[str, ...],
) -> str:
    lines = [
        "You are the FormalVerifier choosing the next route-level proof replay action.",
        "Return a JSON object with replay_mode, replay_steps, acceptance_gate, and proof boundary.",
        "",
        f"Queue item: {row.get('item_id', '')}",
        f"Route: {row.get('route_id', '')}",
        f"Display name: {row.get('display_name', '')}",
        f"Route class: {row.get('route_class', '')}",
        f"Verification stage: {row.get('verification_stage', '')}",
        f"Priority score: {row.get('priority_score', 0)}",
        f"Derived replay mode: {replay_mode}",
        f"Acceptance gate: {row.get('required_gate', '')}",
        "",
        "Required primitives:",
        _bullets(_str_tuple(row.get("required_primitives", []))),
        "",
        "Subclaim replay obligations:",
        _bullets(subclaim_obligations),
        "",
        "Evidence signals:",
        (
            f"- proof_attempt_positive={row.get('proof_attempt_positive', 0)}, "
            f"proof_attempt_negative={row.get('proof_attempt_negative', 0)}, "
            f"proof_search_solved={row.get('proof_search_solved', 0)}"
        ),
        (
            f"- source_trust={row.get('source_trust_level', '')}, "
            f"calibration={row.get('source_trust_calibration_status', '')}, "
            f"semantic={row.get('semantic_faithfulness_score', 0)}/"
            f"{row.get('semantic_faithfulness_status', '')}"
        ),
    ]
    return "\n".join(lines)


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


def _bullets(items: tuple[str, ...]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- none"


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Replay Tasks",
        "",
        f"- Queue manifest: `{payload.get('formal_verifier_queue_manifest')}`",
        f"- Replay tasks: {payload.get('n_ok')}/{payload.get('n_replay_tasks')} audit-clean",
        f"- Kernel-calibrated replay tasks: {payload.get('n_kernel_calibrated')}",
        f"- Proof-search subclaim replay tasks: {payload.get('n_proof_search_subclaim_replay')}",
        f"- Bridge-lemma replay tasks: {payload.get('n_bridge_lemma_replay')}",
        "",
        "Replay tasks are executable verifier work plans, not Lean proof evidence.",
        "",
        "## Tasks",
        "",
    ]
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        lines.append("No replay tasks were exported.")
    else:
        for row in tasks[:30]:
            if not isinstance(row, dict):
                continue
            obligations = ", ".join(
                f"`{item}`" for item in row.get("subclaim_replay_obligations", [])
            ) or "none"
            lines.extend(
                [
                    f"### `{row.get('replay_id')}`",
                    "",
                    f"- Route: `{row.get('display_name')}`",
                    f"- Mode: `{row.get('replay_mode')}`",
                    f"- Replay priority: {row.get('replay_priority_score')}",
                    f"- Subclaim replay obligations: {obligations}",
                    f"- Gate: {row.get('acceptance_gate')}",
                    f"- Boundary: {row.get('proof_evidence_boundary')}",
                    "",
                ]
            )
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

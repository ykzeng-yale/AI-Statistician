from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_EXECUTION_QUEUE_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "AGENTIC_PROOF_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic proof execution queue rows are executable proof-worker work "
    "contracts, not theorem proof evidence. A row becomes proof-relevant only "
    "after the candidate artifact is generated, safety checks pass, and "
    "local Lean/AXLE kernel verification plus residual-gap validation accept it."
)


@dataclass(frozen=True)
class FormalVerifierAgenticProofExecutionQueueRow:
    schema_version: int
    execution_queue_id: str
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
    proof_sketch_population_key: str
    kernel_overlay_context: dict[str, object]
    candidate_artifact_path: str
    execution_transcript_path: str
    target_location_preflight: dict[str, object]
    live_goal_location_ready: bool
    execution_preflight_status: str
    proof_state_provider_plan: tuple[str, ...]
    proof_route_dag_plan: tuple[str, ...]
    verified_sketch_gate_plan: tuple[str, ...]
    blueprint_export_plan: tuple[str, ...]
    command_plan: tuple[str, ...]
    required_static_checks: tuple[str, ...]
    required_dynamic_checks: tuple[str, ...]
    output_contract: tuple[str, ...]
    promotion_gate: str
    execution_status: str
    owner_agent: str
    priority_score: int
    rank: int
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_execution_queue(
    formal_verifier_agentic_proof_attempt_population_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export executable work contracts from safety-gated proof-attempt memory."""

    errors: list[str] = []
    population_manifest_path = (
        formal_verifier_agentic_proof_attempt_population_dir
        / "formal_verifier_agentic_proof_attempt_population_manifest.json"
    )
    population_payload = _read_json(population_manifest_path, errors)
    population_rows = [
        row for row in population_payload.get("rows", []) if isinstance(row, dict)
    ]
    queue_rows = _rank_rows(
        [
            _execution_queue_row(
                row,
                out_dir=out_dir,
                population_dir=formal_verifier_agentic_proof_attempt_population_dir,
            )
            for row in population_rows
        ]
    )
    by_status = Counter(row.execution_status for row in queue_rows)
    by_bucket = Counter(row.population_bucket for row in queue_rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_AGENTIC_PROOF_EXECUTION_QUEUE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_attempt_population_dir": str(
            formal_verifier_agentic_proof_attempt_population_dir
        ),
        "formal_verifier_agentic_proof_attempt_population_manifest": str(
            population_manifest_path
        ),
        "n_population_entries": len(population_rows),
        "n_execution_queue_items": len(queue_rows),
        "n_ready": by_status.get("READY_FOR_AGENTIC_PROOF_WORKER_EXECUTION", 0),
        "n_blocked": sum(
            count for status, count in by_status.items() if status.startswith("BLOCKED_")
        ),
        "n_patch_execution_items": by_bucket.get("bounded_patch_attempt", 0),
        "n_source_execution_items": by_bucket.get("source_discovery_attempt", 0),
        "n_with_candidate_artifact_path": sum(
            1 for row in queue_rows if row.candidate_artifact_path
        ),
        "n_with_live_tool_plan": sum(1 for row in queue_rows if row.command_plan),
        "n_with_proof_route_dag_plan": sum(
            1 for row in queue_rows if row.proof_route_dag_plan
        ),
        "n_with_verified_sketch_gate": sum(
            1 for row in queue_rows if row.verified_sketch_gate_plan
        ),
        "n_with_blueprint_export_plan": sum(
            1 for row in queue_rows if row.blueprint_export_plan
        ),
        "n_with_kernel_overlay_context": sum(
            1 for row in queue_rows if row.kernel_overlay_context
        ),
        "n_live_goal_requested": sum(
            1 for row in queue_rows if "lean_goal" in row.proof_state_provider_plan
        ),
        "n_live_goal_location_ready": sum(
            1 for row in queue_rows if row.live_goal_location_ready
        ),
        "n_needs_target_location": sum(
            1
            for row in queue_rows
            if row.execution_preflight_status
            == "NEEDS_TARGET_LEAN_LOCATION_BEFORE_LIVE_GOAL"
        ),
        "n_candidate_artifact_exists": sum(
            1
            for row in queue_rows
            if bool(row.target_location_preflight.get("candidate_artifact_exists"))
        ),
        "n_ok": sum(1 for row in queue_rows if row.ok),
        "all_ok": not errors and all(row.ok for row in queue_rows),
        "errors": errors,
        "by_execution_status": dict(sorted(by_status.items())),
        "by_population_bucket": dict(sorted(by_bucket.items())),
        "rows": [asdict(row) for row in queue_rows],
        "execution_queue_fingerprint": stable_hash([asdict(row) for row in queue_rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "execution queue rows describe what a proof worker should run; they do not contain proof output",
            "candidate artifact paths are expected outputs until a worker writes and verifies them",
            "MCP/Lean tool calls are operational requirements, not proof evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formal_verifier_agentic_proof_execution_queue_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formal_verifier_agentic_proof_execution_queue.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in queue_rows)
            + ("\n" if queue_rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_agentic_proof_execution_queue.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _execution_queue_row(
    row: dict[str, Any],
    *,
    out_dir: Path | None,
    population_dir: Path,
) -> FormalVerifierAgenticProofExecutionQueueRow:
    errors: list[str] = []
    population_entry_id = str(row.get("population_entry_id", ""))
    safety_policy_id = str(row.get("safety_policy_id", ""))
    candidate_evaluation_id = str(row.get("candidate_evaluation_id", ""))
    goal_cache_key = str(row.get("goal_cache_key", ""))
    candidate_database_key = str(row.get("candidate_database_key", ""))
    candidate_lineage_key = str(row.get("candidate_lineage_key", ""))
    proof_sketch_population_key = str(row.get("proof_sketch_population_key", ""))
    attempt_status = str(row.get("attempt_status", ""))
    generation_mode = str(row.get("generation_mode", ""))
    population_bucket = str(row.get("population_bucket", ""))
    kernel_overlay_context = row.get("kernel_overlay_context", {})
    if not isinstance(kernel_overlay_context, dict):
        kernel_overlay_context = {}
    for field_name, value in (
        ("population_entry_id", population_entry_id),
        ("safety_policy_id", safety_policy_id),
        ("candidate_evaluation_id", candidate_evaluation_id),
        ("goal_cache_key", goal_cache_key),
        ("candidate_database_key", candidate_database_key),
        ("candidate_lineage_key", candidate_lineage_key),
        ("proof_sketch_population_key", proof_sketch_population_key),
    ):
        if not value:
            errors.append(f"{field_name} missing")
    if attempt_status != "READY_FOR_POPULATION_SEEDED_ATTEMPT":
        errors.append(f"attempt population row is not ready: {attempt_status}")

    queue_id = "formal_verifier_agentic_proof_execution_queue:" + stable_hash(
        [population_entry_id, goal_cache_key, candidate_lineage_key]
    )[:16]
    output_base = out_dir or population_dir
    safe_name = _safe_name(row, queue_id)
    candidate_artifact_path = (
        output_base / "candidate_artifacts" / f"{safe_name}.lean"
    )
    execution_transcript_path = (
        output_base / "execution_transcripts" / f"{safe_name}.jsonl"
    )
    if population_bucket == "source_discovery_attempt":
        proof_state_provider_plan = (
            "lean_local_search",
            "lean_leansearch",
            "lean_loogle",
            "primitive-source coverage refresh",
        )
        command_plan = (
            "run source-discovery query bundle against local Lean RAG first",
            "record every candidate as source-only until imported and kernel checked",
            "rerun primitive-source coverage and regenerate residual prompt packets",
        )
        required_static_checks = (
            "source candidate names concrete declaration or source path",
            "source candidate is not marked kernel verified",
            "no theorem statement/header mutation is proposed",
        )
        required_dynamic_checks = (
            "formal-source retrieval refresh",
            "primitive-source coverage expansion",
            "residual prompt-packet regeneration",
        )
        output_contract = (
            "write source-candidate JSONL under the candidate database key",
            "record source reference, import path, and retrieval query",
            "do not emit theorem proof claims",
        )
        owner_agent = "source_discovery_worker"
    else:
        proof_state_provider_plan = (
            "lean_goal",
            "lean_diagnostic_messages",
            "lean_local_search",
            "lean_multi_attempt",
        )
        command_plan = (
            "inspect exact Lean goal state before proposing a candidate",
            "generate one bounded candidate artifact at candidate_artifact_path",
            "run static safety checks before any Lean/AXLE verification",
            "run local Lean or AXLE verification on the candidate artifact",
            "record diagnostics and residual goals in execution_transcript_path",
            "send accepted candidates through replay/calibration before promotion",
        )
        required_static_checks = (
            "no sorry/admit/axiom/unsafe tokens",
            "target theorem statement and declaration header unchanged",
            "helper lemma does not restate the target theorem",
            "candidate artifact records changed declarations",
        )
        required_dynamic_checks = (
            "lean_goal",
            "lean_diagnostic_messages",
            "lean_multi_attempt",
            "local Lean or AXLE kernel verification",
            "formal-verifier replay calibration",
        )
        output_contract = (
            "write a Lean candidate artifact at candidate_artifact_path",
            "write a JSONL execution transcript at execution_transcript_path",
            "include exact goal state, attempted tactics, diagnostics, and verifier result",
            "mark result as proof evidence only if full-route kernel verification succeeds",
        )
        owner_agent = "formal_verifier"
    proof_route_dag_plan = (
        "register residual obligation as an OR goal keyed by goal_cache_key",
        "attach a candidate AND decomposition only after the parent sketch compiles from named child lemmas",
        "reject cyclic, duplicate, or target-restating child-lemma decompositions",
        "memoize accepted child obligations by normalized imports, local context, and target",
    )
    verified_sketch_gate_plan = (
        "construct parent-from-child Lean sketch before proof promotion",
        "allow holes only at explicitly named child lemma declarations",
        "run Lean diagnostics on the sketch and record every remaining child obligation",
        "treat a compiling sketch as decomposition evidence only, not as theorem proof evidence",
    )
    blueprint_export_plan = (
        "emit theorem-route DAG nodes with Lean declaration names",
        "record uses edges between parent theorem and child obligations",
        "label each node as kernel_verified, sketch_verified, source_candidate, or open_gap",
        "keep Blueprint-style reporting separate from kernel proof evidence",
    )
    if kernel_overlay_context:
        proof_state_provider_plan = (
            *proof_state_provider_plan,
            "source discovery for kernel-overlay target blockers",
        )
        required_dynamic_checks = (
            *required_dynamic_checks,
            "verify every kernel-overlay blocker is solved or explicitly deferred",
        )
        output_contract = (
            *output_contract,
            "record reused kernel-overlay subclaims and unresolved target blockers",
        )
        proof_route_dag_plan = (
            *proof_route_dag_plan,
            "link reused kernel-overlay subclaims as already verified child nodes",
        )
        blueprint_export_plan = (
            *blueprint_export_plan,
            "mark kernel-overlay target blockers as open child obligations",
        )
    target_location_preflight = _target_location_preflight(
        row,
        kernel_overlay_context=kernel_overlay_context,
        proof_state_provider_plan=proof_state_provider_plan,
        candidate_artifact_path=candidate_artifact_path,
    )
    live_goal_location_ready = bool(
        target_location_preflight.get("live_goal_location_ready")
    )
    execution_preflight_status = str(
        target_location_preflight.get("execution_preflight_status", "")
    )
    status = (
        "READY_FOR_AGENTIC_PROOF_WORKER_EXECUTION"
        if not errors
        else "BLOCKED_AGENTIC_PROOF_EXECUTION_INPUT"
    )
    return FormalVerifierAgenticProofExecutionQueueRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_EXECUTION_QUEUE_SCHEMA_VERSION,
        execution_queue_id=queue_id,
        population_entry_id=population_entry_id,
        safety_policy_id=safety_policy_id,
        candidate_evaluation_id=candidate_evaluation_id,
        strategy_id=str(row.get("strategy_id", "")),
        followup_id=str(row.get("followup_id", "")),
        residual_obligation_id=str(row.get("residual_obligation_id", "")),
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
        proof_sketch_population_key=proof_sketch_population_key,
        kernel_overlay_context=kernel_overlay_context,
        candidate_artifact_path=str(candidate_artifact_path),
        execution_transcript_path=str(execution_transcript_path),
        target_location_preflight=target_location_preflight,
        live_goal_location_ready=live_goal_location_ready,
        execution_preflight_status=execution_preflight_status,
        proof_state_provider_plan=tuple(dict.fromkeys(proof_state_provider_plan)),
        proof_route_dag_plan=tuple(dict.fromkeys(proof_route_dag_plan)),
        verified_sketch_gate_plan=tuple(dict.fromkeys(verified_sketch_gate_plan)),
        blueprint_export_plan=tuple(dict.fromkeys(blueprint_export_plan)),
        command_plan=command_plan,
        required_static_checks=required_static_checks,
        required_dynamic_checks=tuple(dict.fromkeys(required_dynamic_checks)),
        output_contract=output_contract,
        promotion_gate=(
            "candidate may enter proof ledger only after safety checks, local "
            "Lean/AXLE verification, replay calibration, and residual-gap "
            "validation report full_route_kernel_verified"
        ),
        execution_status=status,
        owner_agent=owner_agent,
        priority_score=int(row.get("replay_priority_score", 0))
        + int(row.get("selection_weight", 0)),
        rank=int(row.get("rank", 0) or 0),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _rank_rows(
    rows: list[FormalVerifierAgenticProofExecutionQueueRow],
) -> list[FormalVerifierAgenticProofExecutionQueueRow]:
    ranked = sorted(
        rows,
        key=lambda row: (
            not row.ok,
            -row.priority_score,
            row.display_name,
            row.population_entry_id,
        ),
    )
    return [
        FormalVerifierAgenticProofExecutionQueueRow(
            **{**asdict(row), "rank": index}
        )
        for index, row in enumerate(ranked, start=1)
    ]


def _safe_name(row: dict[str, Any], queue_id: str) -> str:
    display = str(row.get("display_name", "")) or str(row.get("residual_gap", ""))
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in display).strip("_")
    return f"{cleaned[:80] or 'agentic_proof_candidate'}_{queue_id.rsplit(':', 1)[-1]}"


def _target_location_preflight(
    row: dict[str, Any],
    *,
    kernel_overlay_context: dict[str, object],
    proof_state_provider_plan: tuple[str, ...],
    candidate_artifact_path: Path,
) -> dict[str, object]:
    """Summarize whether live Lean goal inspection can run immediately."""

    context_location = kernel_overlay_context.get("target_location", {})
    if not isinstance(context_location, dict):
        context_location = {}
    target_lean_file = _first_str(
        row.get("target_lean_file"),
        row.get("lean_file"),
        row.get("target_source_path"),
        context_location.get("target_lean_file"),
        context_location.get("lean_file"),
        context_location.get("target_source_path"),
    )
    target_lean_declaration = _first_str(
        row.get("target_lean_declaration"),
        row.get("lean_declaration"),
        row.get("target_declaration"),
        context_location.get("target_lean_declaration"),
        context_location.get("lean_declaration"),
        context_location.get("target_declaration"),
    )
    target_lean_line = _first_positive_int(
        row.get("target_lean_line"),
        row.get("lean_line"),
        row.get("target_line"),
        context_location.get("target_lean_line"),
        context_location.get("lean_line"),
        context_location.get("target_line"),
    )
    target_lean_column = _first_positive_int(
        row.get("target_lean_column"),
        row.get("lean_column"),
        row.get("target_column"),
        context_location.get("target_lean_column"),
        context_location.get("lean_column"),
        context_location.get("target_column"),
    )
    target_imports = _str_tuple(
        row.get("target_imports")
        or row.get("imports")
        or context_location.get("target_imports")
        or context_location.get("imports")
        or []
    )
    live_goal_requested = "lean_goal" in proof_state_provider_plan
    missing: list[str] = []
    if live_goal_requested:
        if not target_lean_file:
            missing.append("target_lean_file")
        if target_lean_line <= 0:
            missing.append("target_lean_line")
    candidate_exists = candidate_artifact_path.exists()
    if not live_goal_requested:
        status = "LIVE_GOAL_NOT_REQUIRED"
        next_step = "run the non-goal execution plan for this row"
    elif not missing:
        status = "READY_FOR_LIVE_LEAN_GOAL"
        next_step = "invoke lean_goal at the resolved target Lean location"
    else:
        status = "NEEDS_TARGET_LEAN_LOCATION_BEFORE_LIVE_GOAL"
        next_step = (
            "resolve target_lean_file and target_lean_line, or generate the "
            "candidate artifact and record its declaration location before "
            "calling lean_goal"
        )
    return {
        "live_goal_requested": live_goal_requested,
        "live_goal_location_ready": live_goal_requested and not missing,
        "execution_preflight_status": status,
        "target_lean_file": target_lean_file,
        "target_lean_line": target_lean_line,
        "target_lean_column": target_lean_column,
        "target_lean_declaration": target_lean_declaration,
        "target_imports": list(target_imports),
        "candidate_artifact_path": str(candidate_artifact_path),
        "candidate_artifact_exists": candidate_exists,
        "missing": missing,
        "next_step": next_step,
        "proof_evidence_boundary": (
            "Target-location preflight is execution routing only; it is not "
            "theorem proof evidence."
        ),
    }


def _first_str(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _first_positive_int(*values: object) -> int:
    for value in values:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            return parsed
    return 0


def _str_tuple(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        values = [values]
    if not isinstance(values, (list, tuple, set)):
        return ()
    return tuple(str(item) for item in values if str(item))


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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Agentic Proof Execution Queue",
        "",
        f"- Population entries: {payload.get('n_population_entries')}",
        f"- Execution queue items: {payload.get('n_execution_queue_items')}",
        f"- Ready: {payload.get('n_ready')}",
        f"- Blocked: {payload.get('n_blocked')}",
        f"- Patch execution: {payload.get('n_patch_execution_items')}",
        f"- Source execution: {payload.get('n_source_execution_items')}",
        f"- With proof-route DAG plan: {payload.get('n_with_proof_route_dag_plan')}",
        f"- With verified-sketch gate: {payload.get('n_with_verified_sketch_gate')}",
        f"- With Blueprint export plan: {payload.get('n_with_blueprint_export_plan')}",
        f"- With kernel-overlay context: {payload.get('n_with_kernel_overlay_context')}",
        f"- Live Lean goal requested: {payload.get('n_live_goal_requested')}",
        f"- Live Lean goal location ready: {payload.get('n_live_goal_location_ready')}",
        f"- Needs target location: {payload.get('n_needs_target_location')}",
        f"- Fingerprint: `{payload.get('execution_queue_fingerprint')}`",
        "",
        str(payload.get("proof_evidence_boundary", "")),
        "",
        "## Queue Items",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        tools = ", ".join(
            f"`{item}`" for item in row.get("proof_state_provider_plan", [])
        ) or "none"
        commands = ", ".join(
            f"`{item}`" for item in row.get("command_plan", [])[:3]
        ) or "none"
        dag_plan = ", ".join(
            f"`{item}`" for item in row.get("proof_route_dag_plan", [])[:2]
        ) or "none"
        sketch_gate = ", ".join(
            f"`{item}`" for item in row.get("verified_sketch_gate_plan", [])[:2]
        ) or "none"
        blueprint_plan = ", ".join(
            f"`{item}`" for item in row.get("blueprint_export_plan", [])[:2]
        ) or "none"
        lines.append(
            f"- #{row.get('rank')} `{row.get('display_name')}` -> "
            f"`{row.get('residual_gap')}` ({row.get('execution_status')})"
        )
        lines.append(f"  artifact: `{row.get('candidate_artifact_path')}`")
        lines.append(f"  transcript: `{row.get('execution_transcript_path')}`")
        lines.append(f"  tools: {tools}")
        lines.append(f"  commands: {commands}")
        lines.append(f"  proof-route DAG: {dag_plan}")
        lines.append(f"  verified-sketch gate: {sketch_gate}")
        lines.append(f"  Blueprint export: {blueprint_plan}")
        preflight = row.get("target_location_preflight", {})
        if isinstance(preflight, dict) and preflight:
            missing = ", ".join(f"`{item}`" for item in preflight.get("missing", []))
            lines.append(
                f"  target-location preflight: `{preflight.get('execution_preflight_status')}`"
            )
            if missing:
                lines.append(f"  target-location missing: {missing}")
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
        lines.append(f"  promotion gate: {row.get('promotion_gate')}")
        lines.append(f"  proof status: {row.get('proof_evidence_status')}")
        if row.get("errors"):
            lines.append(f"  errors: {row.get('errors')}")
    return "\n".join(lines) + "\n"

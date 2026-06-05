from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_TRACE_MEMORY_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "AGENTIC_PROOF_TRACE_MEMORY_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic proof trace memory rows are search-memory summaries of worker "
    "transcripts and verifier outcomes. They may guide future sampling, "
    "repair, and source-theorem promotion work, but they are not theorem proof "
    "evidence. Only local Lean/AXLE kernel verification of the target theorem "
    "or residual gap can promote a claim."
)


@dataclass(frozen=True)
class FormalVerifierAgenticProofTraceMemoryRow:
    schema_version: int
    trace_memory_id: str
    execution_transcript_path: str
    execution_queue_id: str
    materialization_id: str
    artifact_verification_id: str
    live_proof_state_request_id: str
    goal_cache_key: str
    candidate_database_key: str
    candidate_lineage_key: str
    proof_sketch_population_key: str
    display_name: str
    target_theorem_name: str
    target_lean_declaration: str
    target_lean_line: int
    candidate_artifact_path: str
    n_transcript_events: int
    event_types: tuple[str, ...]
    target_blockers: tuple[str, ...]
    live_proof_state_provider_preferences: tuple[str, ...]
    live_proof_state_requested_tools: tuple[str, ...]
    local_lean_checked: bool
    local_lean_compiled: bool
    artifact_kernel_verified: bool
    source_theorem_kernel_verified: bool
    verification_status: str
    verification_strength: str
    verifier: str
    diagnostic_signature: str
    diagnostic_excerpt: tuple[str, ...]
    learned_outcome: str
    sampler_policy_update: str
    replay_priority_delta: int
    reusable_success_signals: tuple[str, ...]
    repair_signals: tuple[str, ...]
    required_followups: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_trace_memory(
    formal_verifier_agentic_proof_execution_artifact_verifier_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Summarize agentic proof transcripts into reusable search memory."""

    errors: list[str] = []
    verifier_manifest_path = (
        formal_verifier_agentic_proof_execution_artifact_verifier_dir
        / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
    )
    verifier_payload = _read_json(verifier_manifest_path, errors)
    verifier_rows = [
        row for row in verifier_payload.get("rows", []) if isinstance(row, dict)
    ]
    rows = [_trace_memory_row(row) for row in verifier_rows]
    by_outcome = Counter(row.learned_outcome for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_AGENTIC_PROOF_TRACE_MEMORY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_execution_artifact_verifier_dir": str(
            formal_verifier_agentic_proof_execution_artifact_verifier_dir
        ),
        "formal_verifier_agentic_proof_execution_artifact_verifier_manifest": str(
            verifier_manifest_path
        ),
        "n_verifier_rows": len(verifier_rows),
        "n_trace_memory_rows": len(rows),
        "n_execution_transcript_paths": sum(
            1 for row in rows if row.execution_transcript_path
        ),
        "n_transcript_events": sum(row.n_transcript_events for row in rows),
        "n_with_materialization_event": sum(
            1 for row in rows if "candidate_artifact_materialized" in row.event_types
        ),
        "n_with_verifier_result_event": sum(
            1 for row in rows if "artifact_verifier_result" in row.event_types
        ),
        "n_artifact_kernel_verified": sum(
            1 for row in rows if row.artifact_kernel_verified
        ),
        "n_source_theorem_kernel_verified": sum(
            1 for row in rows if row.source_theorem_kernel_verified
        ),
        "n_artifact_lean_failed": by_outcome.get("ARTIFACT_LEAN_FAILED", 0),
        "n_materialized_awaiting_verifier": by_outcome.get(
            "MATERIALIZED_AWAITING_ARTIFACT_VERIFIER",
            0,
        ),
        "n_goal_cache_keys": len({row.goal_cache_key for row in rows if row.goal_cache_key}),
        "n_candidate_lineage_keys": len(
            {row.candidate_lineage_key for row in rows if row.candidate_lineage_key}
        ),
        "n_live_proof_state_requests": sum(
            1 for row in rows if row.live_proof_state_request_id
        ),
        "n_with_repair_signals": sum(1 for row in rows if row.repair_signals),
        "n_with_required_followups": sum(1 for row in rows if row.required_followups),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_learned_outcome": dict(sorted(by_outcome.items())),
        "rows": [asdict(row) for row in rows],
        "trace_memory_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "trace memory is a sampler and repair signal, not proof evidence",
            "artifact-kernel successes only prove the generated artifact, not the source theorem",
            "failed diagnostics should down-rank repeated attempts but never block unrelated proof routes",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formal_verifier_agentic_proof_trace_memory_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formal_verifier_agentic_proof_trace_memory.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_agentic_proof_trace_memory.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _trace_memory_row(
    verifier_row: dict[str, Any],
) -> FormalVerifierAgenticProofTraceMemoryRow:
    errors: list[str] = []
    transcript_raw = str(verifier_row.get("execution_transcript_path", ""))
    transcript_path = Path(transcript_raw) if transcript_raw else None
    if not transcript_raw:
        errors.append("execution_transcript_path missing")
    events, transcript_errors = _read_transcript_events(transcript_path)
    errors.extend(transcript_errors)
    materialization_event = _last_event(events, "candidate_artifact_materialized")
    verifier_event = _matching_verifier_event(verifier_row, events)
    live_request = materialization_event.get("live_proof_state_request", {})
    if not isinstance(live_request, dict):
        live_request = {}

    artifact_verification_id = str(
        verifier_event.get(
            "artifact_verification_id",
            verifier_row.get("artifact_verification_id", ""),
        )
    )
    materialization_id = str(
        verifier_event.get(
            "materialization_id",
            materialization_event.get(
                "materialization_id",
                verifier_row.get("materialization_id", ""),
            ),
        )
    )
    execution_queue_id = str(
        verifier_event.get(
            "execution_queue_id",
            materialization_event.get(
                "execution_queue_id",
                verifier_row.get("execution_queue_id", ""),
            ),
        )
    )
    candidate_artifact_path = str(
        verifier_event.get(
            "candidate_artifact_path",
            materialization_event.get(
                "candidate_artifact_path",
                verifier_row.get("candidate_artifact_path", ""),
            ),
        )
    )
    local_lean_checked = bool(
        verifier_event.get("local_lean_checked", verifier_row.get("local_lean_checked", False))
    )
    local_lean_compiled = bool(
        verifier_event.get(
            "local_lean_compiled",
            verifier_row.get("local_lean_compiled", False),
        )
    )
    artifact_kernel_verified = bool(
        verifier_event.get(
            "artifact_kernel_verified",
            verifier_row.get("artifact_kernel_verified", False),
        )
    )
    source_theorem_kernel_verified = bool(
        verifier_event.get(
            "source_theorem_kernel_verified",
            verifier_row.get("source_theorem_kernel_verified", False),
        )
    )
    verification_status = str(
        verifier_event.get(
            "verification_status",
            verifier_row.get("verification_status", ""),
        )
    )
    diagnostics = _str_tuple(
        verifier_event.get("diagnostics", verifier_row.get("diagnostics", ()))
    )
    diagnostic_signature = _diagnostic_signature(verification_status, diagnostics)
    learned_outcome = _learned_outcome(
        has_materialization=bool(materialization_event),
        has_verifier=bool(verifier_event),
        artifact_kernel_verified=artifact_kernel_verified,
        source_theorem_kernel_verified=source_theorem_kernel_verified,
        local_lean_checked=local_lean_checked,
        local_lean_compiled=local_lean_compiled,
    )
    (
        sampler_policy_update,
        replay_priority_delta,
        reusable_success_signals,
        repair_signals,
        required_followups,
    ) = _learning_policy(
        learned_outcome,
        diagnostics=diagnostics,
        target_blockers=_str_tuple(live_request.get("target_blockers", ())),
    )
    if not materialization_event and not verifier_event:
        errors.append("no transcript materialization or verifier event found")
    for field_name, value in (
        ("execution_queue_id", execution_queue_id),
        ("candidate_artifact_path", candidate_artifact_path),
    ):
        if not value:
            errors.append(f"{field_name} missing")

    trace_memory_id = "formal_verifier_agentic_proof_trace_memory:" + stable_hash(
        [
            transcript_raw,
            execution_queue_id,
            artifact_verification_id,
            diagnostic_signature,
        ]
    )[:16]
    event_types = tuple(
        str(event.get("event", ""))
        for event in events
        if isinstance(event, dict) and str(event.get("event", ""))
    )
    return FormalVerifierAgenticProofTraceMemoryRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_TRACE_MEMORY_SCHEMA_VERSION,
        trace_memory_id=trace_memory_id,
        execution_transcript_path=transcript_raw,
        execution_queue_id=execution_queue_id,
        materialization_id=materialization_id,
        artifact_verification_id=artifact_verification_id,
        live_proof_state_request_id=str(
            verifier_event.get(
                "live_proof_state_request_id",
                live_request.get("request_id", verifier_row.get("live_proof_state_request_id", "")),
            )
        ),
        goal_cache_key=str(live_request.get("goal_cache_key", "")),
        candidate_database_key=str(live_request.get("candidate_database_key", "")),
        candidate_lineage_key=str(live_request.get("candidate_lineage_key", "")),
        proof_sketch_population_key=str(
            live_request.get("proof_sketch_population_key", "")
        ),
        display_name=str(verifier_row.get("display_name", "")),
        target_theorem_name=str(verifier_row.get("target_theorem_name", "")),
        target_lean_declaration=str(
            verifier_event.get(
                "target_lean_declaration",
                materialization_event.get(
                    "target_lean_declaration",
                    verifier_row.get("target_lean_declaration", ""),
                ),
            )
        ),
        target_lean_line=_int(
            verifier_event.get(
                "target_lean_line",
                materialization_event.get(
                    "target_lean_line",
                    verifier_row.get("target_lean_line", 0),
                ),
            )
        ),
        candidate_artifact_path=candidate_artifact_path,
        n_transcript_events=len(events),
        event_types=event_types,
        target_blockers=_str_tuple(live_request.get("target_blockers", ())),
        live_proof_state_provider_preferences=_str_tuple(
            live_request.get(
                "provider_preferences",
                verifier_row.get("live_proof_state_provider_preferences", ()),
            )
        ),
        live_proof_state_requested_tools=_str_tuple(
            verifier_event.get(
                "live_proof_state_requested_tools",
                verifier_row.get("live_proof_state_requested_tools", ()),
            )
        ),
        local_lean_checked=local_lean_checked,
        local_lean_compiled=local_lean_compiled,
        artifact_kernel_verified=artifact_kernel_verified,
        source_theorem_kernel_verified=source_theorem_kernel_verified,
        verification_status=verification_status,
        verification_strength=str(
            verifier_event.get(
                "verification_strength",
                verifier_row.get("verification_strength", ""),
            )
        ),
        verifier=str(verifier_event.get("verifier", verifier_row.get("verifier", ""))),
        diagnostic_signature=diagnostic_signature,
        diagnostic_excerpt=diagnostics[:8],
        learned_outcome=learned_outcome,
        sampler_policy_update=sampler_policy_update,
        replay_priority_delta=replay_priority_delta,
        reusable_success_signals=reusable_success_signals,
        repair_signals=repair_signals,
        required_followups=required_followups,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _read_transcript_events(path: Path | None) -> tuple[list[dict[str, Any]], list[str]]:
    if path is None:
        return [], []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return [], [f"execution transcript missing: {path}"]
    except Exception as exc:
        return [], [f"failed to read transcript {path}: {type(exc).__name__}: {exc}"]
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid transcript JSON line {index}: {exc}")
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            errors.append(f"transcript line {index} is not an object")
    return events, errors


def _matching_verifier_event(
    verifier_row: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    event_id = str(verifier_row.get("execution_transcript_event_id", ""))
    if event_id:
        for event in events:
            if (
                event.get("event") == "artifact_verifier_result"
                and event.get("event_id") == event_id
            ):
                return event
    return _last_event(events, "artifact_verifier_result")


def _last_event(events: list[dict[str, Any]], event_name: str) -> dict[str, Any]:
    for event in reversed(events):
        if event.get("event") == event_name:
            return event
    return {}


def _learned_outcome(
    *,
    has_materialization: bool,
    has_verifier: bool,
    artifact_kernel_verified: bool,
    source_theorem_kernel_verified: bool,
    local_lean_checked: bool,
    local_lean_compiled: bool,
) -> str:
    if source_theorem_kernel_verified:
        return "SOURCE_THEOREM_KERNEL_VERIFIED"
    if artifact_kernel_verified:
        return "ARTIFACT_KERNEL_VERIFIED_SOURCE_THEOREM_OPEN"
    if has_verifier and local_lean_checked and not local_lean_compiled:
        return "ARTIFACT_LEAN_FAILED"
    if has_verifier:
        return "ARTIFACT_VERIFIER_RECORDED_NONKERNEL"
    if has_materialization:
        return "MATERIALIZED_AWAITING_ARTIFACT_VERIFIER"
    return "NO_TRANSCRIPT_EVENTS"


def _learning_policy(
    learned_outcome: str,
    *,
    diagnostics: tuple[str, ...],
    target_blockers: tuple[str, ...],
) -> tuple[str, int, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if learned_outcome == "SOURCE_THEOREM_KERNEL_VERIFIED":
        return (
            "promote source theorem evidence after claim-ledger and proof-bank audit",
            120,
            ("source theorem kernel verified", "claim can be promoted after audit"),
            (),
            ("record source theorem verifier manifest in proof ledger",),
        )
    if learned_outcome == "ARTIFACT_KERNEL_VERIFIED_SOURCE_THEOREM_OPEN":
        followups = (
            "resolve exact source theorem target",
            "port route-probe proof into bounded source-theorem patch",
            "rerun full source theorem under local Lean/AXLE",
        )
        if target_blockers:
            followups = (
                *followups,
                "discharge target blockers: " + ", ".join(target_blockers),
            )
        return (
            "increase sampling weight for this route-probe lineage while keeping source theorem blocked",
            35,
            ("candidate artifact compiles", "live proof-state request reached verifier"),
            (),
            followups,
        )
    if learned_outcome == "ARTIFACT_LEAN_FAILED":
        return (
            "down-rank exact repeat and prioritize diagnostic repair before new search",
            -35,
            (),
            _repair_signals(diagnostics),
            (
                "inspect Lean diagnostics",
                "query live goal state before retry",
                "try a bounded repair candidate with the same goal cache key",
            ),
        )
    if learned_outcome == "MATERIALIZED_AWAITING_ARTIFACT_VERIFIER":
        return (
            "keep lineage in pending queue until artifact verifier produces a result",
            5,
            ("candidate artifact materialized",),
            (),
            ("run formal-verifier-agentic-proof-execution-artifact-verifier",),
        )
    return (
        "quarantine transcript row until required execution events are present",
        -20,
        (),
        _repair_signals(diagnostics),
        ("regenerate execution transcript from materializer and verifier manifests",),
    )


def _repair_signals(diagnostics: tuple[str, ...]) -> tuple[str, ...]:
    if not diagnostics:
        return ()
    signals: list[str] = []
    joined = "\n".join(diagnostics).lower()
    for token, label in (
        ("unknown constant", "unknown constant/import or declaration mismatch"),
        ("unsolved goals", "unsolved Lean goals"),
        ("type mismatch", "type mismatch"),
        ("failed to synthesize", "typeclass synthesis failure"),
        ("invalid field", "invalid field/projection"),
        ("warning:", "Lean warning present"),
    ):
        if token in joined:
            signals.append(label)
    if not signals:
        signals.append("diagnostics require manual classification")
    return tuple(dict.fromkeys(signals))


def _diagnostic_signature(
    verification_status: str,
    diagnostics: tuple[str, ...],
) -> str:
    if not diagnostics:
        return verification_status or "NO_DIAGNOSTICS"
    return "agentic_trace_diag:" + stable_hash(
        [verification_status, [line.strip()[:240] for line in diagnostics[:12]]]
    )[:16]


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


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _str_tuple(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        values = [values]
    if not isinstance(values, (list, tuple, set)):
        return ()
    return tuple(str(item) for item in values if str(item))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Agentic Proof Trace Memory",
        "",
        f"- Verifier rows: `{payload.get('n_verifier_rows')}`",
        f"- Trace memory rows: `{payload.get('n_trace_memory_rows')}`",
        f"- Transcript events: `{payload.get('n_transcript_events')}`",
        f"- With verifier result event: `{payload.get('n_with_verifier_result_event')}`",
        f"- Artifact kernel verified: `{payload.get('n_artifact_kernel_verified')}`",
        f"- Source theorem kernel verified: `{payload.get('n_source_theorem_kernel_verified')}`",
        f"- Goal cache keys: `{payload.get('n_goal_cache_keys')}`",
        f"- Candidate lineage keys: `{payload.get('n_candidate_lineage_keys')}`",
        f"- All OK: `{payload.get('all_ok')}`",
        "",
        "## Learned Outcomes",
    ]
    by_outcome = payload.get("by_learned_outcome", {})
    if isinstance(by_outcome, dict) and by_outcome:
        for key, value in sorted(by_outcome.items()):
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- No outcomes recorded.")
    lines.extend(
        [
            "",
            "## Honesty Boundary",
            "",
            str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
            "",
        ]
    )
    return "\n".join(lines)

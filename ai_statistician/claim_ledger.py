from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


ClaimKind = Literal[
    "problem_card",
    "procedure_derivation",
    "theorem_goal",
    "formal_subclaim",
    "simulation_evidence",
    "next_iteration_item",
]

ClaimStatus = Literal[
    "PROBLEM_FORMALIZED",
    "DERIVATION_SUPPORTED",
    "THEOREM_GOAL_CONJECTURED",
    "KERNEL_PROVED_SUBCLAIM",
    "MOCK_PROVED_SUBCLAIM",
    "FORMAL_GAP",
    "PROOF_FAILED",
    "SIMULATION_SUPPORTED",
    "SIMULATION_FLAGGED",
    "REVISION_QUEUED",
]


@dataclass(frozen=True)
class ClaimLedgerRow:
    ledger_version: int
    claim_id: str
    question_id: str
    problem_class: str
    kind: ClaimKind
    status: ClaimStatus
    statement: str
    evidence_level: str
    trace_path: str
    procedure_id: str = ""
    theorem_goal_id: str = ""
    proof_obligation_id: str = ""
    verifier: str = ""
    verification_strength: str = ""
    kernel_verified: bool = False
    formalization_status: str = ""
    required_primitives: tuple[str, ...] = ()
    formal_source_hits: tuple[str, ...] = ()
    paper_source_ids: tuple[str, ...] = ()
    knowledge_ids: tuple[str, ...] = ()
    simulation_metrics: dict[str, float] = field(default_factory=dict)
    simulation_passed: bool | None = None
    simulation_diagnosis: str = ""
    escalation_target: str = ""
    owner_agent: str = ""
    action: str = ""
    evidence_paths: tuple[str, ...] = ()
    ok: bool = True
    errors: tuple[str, ...] = ()


def build_claim_ledger(run_dir: Path, out_dir: Path | None = None) -> dict[str, object]:
    """Export a typed claim ledger from persisted research benchmark traces.

    The ledger is a coordination artifact, not new proof evidence. It keeps
    theorem goals, proved Lean subclaims, formal gaps, simulation results, and
    next-iteration actions in one table so later agents can revise theory from
    evidence rather than from unstructured trace prose.
    """

    manifest_path = run_dir / "research_benchmark_manifest.json"
    errors: list[str] = []
    if not manifest_path.exists():
        errors.append(f"missing research benchmark manifest: {manifest_path}")
        manifest: dict[str, Any] = {}
        summaries: list[dict[str, Any]] = []
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"failed to parse manifest JSON: {type(exc).__name__}: {exc}")
            manifest = {}
        summaries = list(manifest.get("questions", [])) if isinstance(manifest.get("questions"), list) else []

    rows: list[ClaimLedgerRow] = []
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        question_id = str(summary.get("question", "<missing>"))
        trace_path = run_dir / f"{question_id}.json"
        if not trace_path.exists():
            errors.append(f"missing research trace: {trace_path}")
            continue
        try:
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"failed to parse trace JSON {trace_path}: {type(exc).__name__}: {exc}")
            continue
        rows.extend(_ledger_rows_for_trace(trace, summary, trace_path))

    by_kind = Counter(row.kind for row in rows)
    by_status = Counter(row.status for row in rows)
    by_problem_class = Counter(row.problem_class for row in rows)
    payload: dict[str, object] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ledger_version": 1,
        "run_dir": str(run_dir),
        "manifest": str(manifest_path),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "n_questions": len(summaries),
        "n_claims": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "by_kind": dict(sorted(by_kind.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_problem_class": dict(sorted(by_problem_class.items())),
        "provenance": manifest.get("provenance", {}),
        "formal_source_search": manifest.get("formal_source_search", {}),
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "claim_ledger_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        with (out_dir / "claim_ledger.jsonl").open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(asdict(row), default=str) + "\n")
        (out_dir / "claim_ledger.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _ledger_rows_for_trace(
    trace: dict[str, Any],
    summary: dict[str, Any],
    trace_path: Path,
) -> list[ClaimLedgerRow]:
    question = trace.get("question") if isinstance(trace.get("question"), dict) else {}
    problem = trace.get("problem") if isinstance(trace.get("problem"), dict) else {}
    procedures = trace.get("procedures", []) if isinstance(trace.get("procedures"), list) else []
    theorem_goals = trace.get("theorem_goals", []) if isinstance(trace.get("theorem_goals"), list) else []
    formal_subclaims = trace.get("formal_subclaims", []) if isinstance(trace.get("formal_subclaims"), list) else []
    simulations = trace.get("simulations", []) if isinstance(trace.get("simulations"), list) else []
    paper_sources = trace.get("paper_sources", []) if isinstance(trace.get("paper_sources"), list) else []
    knowledge = trace.get("knowledge", []) if isinstance(trace.get("knowledge"), list) else []
    theory_plan = trace.get("theory_plan") if isinstance(trace.get("theory_plan"), dict) else {}
    agenda = theory_plan.get("next_iteration_agenda", {}) if isinstance(theory_plan.get("next_iteration_agenda"), dict) else {}
    question_id = str(question.get("id", summary.get("question", "<missing>")))
    problem_class = str(problem.get("problem_class", summary.get("problem_class", "<missing>")))
    trace_path_str = str(trace_path)
    paper_ids = tuple(str(row.get("id", "")) for row in paper_sources if isinstance(row, dict) and row.get("id"))
    knowledge_ids = tuple(str(row.get("id", "")) for row in knowledge if isinstance(row, dict) and row.get("id"))

    rows = [
        ClaimLedgerRow(
            ledger_version=1,
            claim_id=f"problem:{question_id}",
            question_id=question_id,
            problem_class=problem_class,
            kind="problem_card",
            status="PROBLEM_FORMALIZED",
            statement=f"{problem.get('dgp', '')} Target: {problem.get('estimand', '')}".strip(),
            evidence_level="structured_intake",
            trace_path=trace_path_str,
            paper_source_ids=paper_ids,
            knowledge_ids=knowledge_ids,
            evidence_paths=(trace_path_str,),
        )
    ]
    for procedure in procedures:
        if not isinstance(procedure, dict):
            continue
        procedure_id = str(procedure.get("id", ""))
        rows.append(
            ClaimLedgerRow(
                ledger_version=1,
                claim_id=f"procedure:{question_id}:{procedure_id}",
                question_id=question_id,
                problem_class=problem_class,
                kind="procedure_derivation",
                status="DERIVATION_SUPPORTED",
                statement=str(procedure.get("informal_derivation") or procedure.get("formula") or ""),
                evidence_level="informal_derivation",
                trace_path=trace_path_str,
                procedure_id=procedure_id,
                theorem_goal_id=",".join(str(item) for item in procedure.get("theorem_goals", []) or []),
                paper_source_ids=paper_ids,
                knowledge_ids=knowledge_ids,
                evidence_paths=(trace_path_str,),
            )
        )
    for goal in theorem_goals:
        if not isinstance(goal, dict):
            continue
        goal_id = str(goal.get("id", ""))
        rows.append(
            ClaimLedgerRow(
                ledger_version=1,
                claim_id=f"theorem_goal:{question_id}:{goal_id}",
                question_id=question_id,
                problem_class=problem_class,
                kind="theorem_goal",
                status="THEOREM_GOAL_CONJECTURED",
                statement=str(goal.get("informal_statement") or goal.get("title") or ""),
                evidence_level="theory_plan_conjecture",
                trace_path=trace_path_str,
                theorem_goal_id=goal_id,
                required_primitives=tuple(str(item) for item in goal.get("required_primitives", []) or []),
                proof_obligation_id=",".join(str(item) for item in goal.get("proof_obligations", []) or []),
                paper_source_ids=paper_ids,
                knowledge_ids=knowledge_ids,
                evidence_paths=(trace_path_str,),
            )
        )
    for subclaim in formal_subclaims:
        if isinstance(subclaim, dict):
            rows.append(_formal_subclaim_row(subclaim, question_id, problem_class, trace_path_str))
    for simulation in simulations:
        if isinstance(simulation, dict):
            rows.append(_simulation_row(simulation, question_id, problem_class, trace_path_str))
    items = agenda.get("items", []) if isinstance(agenda.get("items"), list) else []
    for item in items:
        if isinstance(item, dict):
            rows.append(_agenda_row(item, question_id, problem_class, trace_path_str))
    return rows


def _formal_subclaim_row(
    subclaim: dict[str, Any],
    question_id: str,
    problem_class: str,
    trace_path: str,
) -> ClaimLedgerRow:
    errors: list[str] = []
    raw_status = str(subclaim.get("status", ""))
    kernel_verified = bool(subclaim.get("kernel_verified"))
    verification_strength = str(subclaim.get("verification_strength", ""))
    if raw_status == "PROVED" and kernel_verified:
        status: ClaimStatus = "KERNEL_PROVED_SUBCLAIM"
        evidence_level = "lean_kernel_verified"
    elif raw_status == "PROVED":
        status = "MOCK_PROVED_SUBCLAIM"
        evidence_level = "mock_or_non_kernel_verified"
    elif raw_status == "FORMAL_GAP":
        status = "FORMAL_GAP"
        evidence_level = "formal_gap_with_retrieval"
    elif raw_status == "FAILED":
        status = "PROOF_FAILED"
        evidence_level = "failed_verifier_attempt"
    else:
        status = "PROOF_FAILED"
        evidence_level = "unknown_formal_status"
        errors.append(f"unknown formal subclaim status: {raw_status!r}")
    if status == "KERNEL_PROVED_SUBCLAIM" and verification_strength == "mock_static_check":
        errors.append("kernel-proved subclaim cannot use mock_static_check")
    if status == "MOCK_PROVED_SUBCLAIM" and kernel_verified:
        errors.append("mock-proved subclaim cannot be kernel_verified")
    formal_source_hits = tuple(
        str(hit.get("name", ""))
        for hit in (subclaim.get("formal_source_hits", []) if isinstance(subclaim.get("formal_source_hits"), list) else [])
        if isinstance(hit, dict) and hit.get("name")
    )
    evidence_paths = [trace_path]
    artifact_path = str(subclaim.get("artifact_path") or "")
    if artifact_path:
        evidence_paths.append(artifact_path)
    return ClaimLedgerRow(
        ledger_version=1,
        claim_id=f"formal:{question_id}:{subclaim.get('id') or subclaim.get('proof_obligation_id') or raw_status}",
        question_id=question_id,
        problem_class=problem_class,
        kind="formal_subclaim",
        status=status,
        statement=str(subclaim.get("claim") or subclaim.get("title") or subclaim.get("lean_statement") or ""),
        evidence_level=evidence_level,
        trace_path=trace_path,
        proof_obligation_id=str(subclaim.get("proof_obligation_id") or ""),
        verifier=str(subclaim.get("verifier") or ""),
        verification_strength=verification_strength,
        kernel_verified=kernel_verified,
        formalization_status=str(subclaim.get("formalization_status") or ""),
        formal_source_hits=formal_source_hits,
        evidence_paths=tuple(evidence_paths),
        ok=not errors,
        errors=tuple(errors),
    )


def _simulation_row(
    simulation: dict[str, Any],
    question_id: str,
    problem_class: str,
    trace_path: str,
) -> ClaimLedgerRow:
    diagnosis = simulation.get("diagnosis") if isinstance(simulation.get("diagnosis"), dict) else {}
    passed = bool(simulation.get("passed"))
    raw_metrics = simulation.get("metrics") if isinstance(simulation.get("metrics"), dict) else {}
    metrics: dict[str, float] = {}
    for key, value in raw_metrics.items():
        if isinstance(value, (int, float)):
            metrics[str(key)] = float(value)
    status: ClaimStatus = "SIMULATION_SUPPORTED" if passed else "SIMULATION_FLAGGED"
    return ClaimLedgerRow(
        ledger_version=1,
        claim_id=f"simulation:{question_id}:{simulation.get('procedure_id', '')}",
        question_id=question_id,
        problem_class=problem_class,
        kind="simulation_evidence",
        status=status,
        statement=str(simulation.get("feedback") or simulation.get("design") or ""),
        evidence_level="monte_carlo_simulation",
        trace_path=trace_path,
        procedure_id=str(simulation.get("procedure_id") or ""),
        simulation_metrics=metrics,
        simulation_passed=passed,
        simulation_diagnosis=str(diagnosis.get("status") or ""),
        escalation_target=str(diagnosis.get("escalate_to") or ""),
        evidence_paths=(trace_path,),
    )


def _agenda_row(
    item: dict[str, Any],
    question_id: str,
    problem_class: str,
    trace_path: str,
) -> ClaimLedgerRow:
    return ClaimLedgerRow(
        ledger_version=1,
        claim_id=f"agenda:{question_id}:{item.get('id', '')}",
        question_id=question_id,
        problem_class=problem_class,
        kind="next_iteration_item",
        status="REVISION_QUEUED",
        statement=str(item.get("evidence") or item.get("trigger") or ""),
        evidence_level="queued_feedback",
        trace_path=trace_path,
        procedure_id=str(item.get("target_procedure") or ""),
        theorem_goal_id=str(item.get("target_theorem_goal") or ""),
        required_primitives=tuple(str(row) for row in item.get("required_primitives", []) or []),
        escalation_target=str(item.get("owner_agent") or ""),
        owner_agent=str(item.get("owner_agent") or ""),
        action=str(item.get("action") or ""),
        evidence_paths=(trace_path,),
    )


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# AI Statistical Theory Lab Claim Ledger",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Claims: {payload.get('n_ok')}/{payload.get('n_claims')} audit-clean",
        f"- Questions: {payload.get('n_questions')}",
        "",
        "This ledger is a typed coordination artifact. It separates formal proof",
        "evidence from retrieval hits and simulation evidence.",
        "",
        "## Status Counts",
        "",
    ]
    by_status = payload.get("by_status", {})
    if isinstance(by_status, dict) and by_status:
        for status, count in sorted(by_status.items()):
            lines.append(f"- `{status}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Sample Claims", ""])
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No ledger rows were produced.")
        return "\n".join(lines) + "\n"
    for row in rows[:20]:
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### {row.get('claim_id')}",
                "",
                f"- Kind: `{row.get('kind')}`",
                f"- Status: `{row.get('status')}`",
                f"- Evidence level: `{row.get('evidence_level')}`",
                f"- Question: `{row.get('question_id')}`",
            ]
        )
        if row.get("proof_obligation_id"):
            lines.append(f"- Proof obligation: `{row.get('proof_obligation_id')}`")
        if row.get("kernel_verified"):
            lines.append("- Kernel verified: `true`")
        if row.get("simulation_diagnosis"):
            lines.append(f"- Simulation diagnosis: `{row.get('simulation_diagnosis')}`")
        statement = str(row.get("statement", "")).strip().replace("\n", " ")
        if statement:
            lines.append(f"- Statement/evidence: {statement[:240]}")
        for error in row.get("errors") or []:
            lines.append(f"- Error: {error}")
        lines.append("")
    return "\n".join(lines) + "\n"

"""Library curation gates for proposed statistical lemmas."""

from __future__ import annotations

from dataclasses import dataclass

from statlean_agent.contracts import (
    BenchmarkTask,
    CuratedLemmaCandidate,
    CuratedLemmaLedgerEntry,
    CurationDecision,
    VerificationReport,
)
from statlean_agent.rewards import FORBIDDEN_TOKENS


@dataclass(frozen=True)
class CurationPolicy:
    min_reuse_count: int = 1
    min_generality_score: float = 0.0
    require_semantic_notes: bool = True


def curate_candidate(
    candidate: CuratedLemmaCandidate,
    policy: CurationPolicy = CurationPolicy(),
) -> CurationDecision:
    """Apply static curation gates before a lemma can enter the local library."""

    reasons: list[str] = []
    required_changes: list[str] = []
    joined = f"{candidate.statement}\n{candidate.proof}".lower()

    for token in FORBIDDEN_TOKENS:
        if token in joined:
            reasons.append(f"forbidden token `{token}` appears in statement or proof")

    if candidate.reuse_count < policy.min_reuse_count:
        required_changes.append("show downstream reuse before promotion")

    if candidate.generality_score < policy.min_generality_score:
        required_changes.append("increase generality score or justify task-specific lemma")

    if policy.require_semantic_notes and not candidate.semantic_notes.strip():
        required_changes.append("add statistical semantic notes")

    if not candidate.motivation_tasks:
        required_changes.append("link at least one motivating theorem or benchmark task")

    accepted = not reasons and not required_changes
    return CurationDecision(
        accepted=accepted,
        reasons=tuple(reasons),
        required_changes=tuple(required_changes),
    )


def build_theorem_hole_lemma_ledger(
    tasks: tuple[BenchmarkTask, ...],
    reports: tuple[VerificationReport, ...],
) -> tuple[CuratedLemmaLedgerEntry, ...]:
    """Create seed curation records from theorem-hole benchmark tasks.

    These records are intentionally not promoted into StatInference. The
    theorem-hole source contains scoped `sorry` placeholders, so the curator
    must block each candidate until a future no-sorry proof replaces it.
    """

    reports_by_task = {report.task_id: report for report in reports}
    entries: list[CuratedLemmaLedgerEntry] = []
    for task in tasks:
        if "theorem_hole" not in task.domain_tags:
            continue

        candidate = CuratedLemmaCandidate(
            name=_candidate_name(task),
            statement=task.lean_task.statement,
            proof="pending no-placeholder proof extracted from theorem-hole benchmark",
            motivation_tasks=(task.task_id,),
            imports_added=task.lean_task.imports,
            reuse_count=max(1, len(task.expected_premises)),
            generality_score=0.5,
            semantic_notes=(
                "Theorem-hole-derived reusable lemma candidate. Expected premises: "
                + ", ".join(task.expected_premises)
            ),
        )
        decision = curate_candidate(candidate)
        entries.append(
            CuratedLemmaLedgerEntry(
                ledger_id=f"ledger::{task.task_id}",
                candidate=candidate,
                decision=decision,
                source_task_ids=(task.task_id,),
                verification_report_ids=(task.task_id,) if task.task_id in reports_by_task else (),
                status="blocked_placeholder" if not decision.accepted else "candidate_ready",
                notes=(
                    "Do not promote this candidate until the theorem-hole placeholder "
                    "is replaced by a verified no-sorry proof."
                ),
            )
        )
    return tuple(entries)


def _candidate_name(task: BenchmarkTask) -> str:
    if task.task_id == "ipw_linearization_theorem_hole_seed":
        return "ipw_hajek_linearization_constructor"
    if task.task_id == "aipw_product_rate_theorem_hole_seed":
        return "aipw_product_rate_route_constructor"
    if task.task_id == "if_normality_theorem_hole_seed":
        return "influence_function_normality_route_constructor"
    return f"{task.task_id}_candidate"

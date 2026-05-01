"""Library curation gates for proposed statistical lemmas."""

from __future__ import annotations

from dataclasses import dataclass

from statlean_agent.contracts import CuratedLemmaCandidate, CurationDecision
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


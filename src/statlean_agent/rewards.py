"""Reward shaping for verifier-guided proof training."""

from __future__ import annotations

from dataclasses import dataclass

from statlean_agent.contracts import ProofAttempt, RewardBreakdown, VerificationReport, VerificationStatus


@dataclass(frozen=True)
class RewardWeights:
    proof_complete: float = 10.0
    locally_valid_step: float = 0.25
    closed_goal: float = 0.75
    premise_used: float = 0.1
    timeout_penalty: float = -2.0
    rejected_penalty: float = -1.0
    sorry_penalty: float = -10.0
    axiom_penalty: float = -10.0
    first_error_penalty: float = -0.5


FORBIDDEN_TOKENS = ("sorry", "admit", "axiom", "unsafe")


def score_attempt(
    attempt: ProofAttempt,
    report: VerificationReport,
    weights: RewardWeights = RewardWeights(),
) -> RewardBreakdown:
    """Score a proof attempt with dense verifier-aware reward components."""

    components: dict[str, float] = {}
    if report.status is VerificationStatus.ACCEPTED:
        components["proof_complete"] = weights.proof_complete
    elif report.status is VerificationStatus.TIMEOUT:
        components["timeout"] = weights.timeout_penalty
    else:
        components["rejected"] = weights.rejected_penalty

    components["locally_valid_steps"] = weights.locally_valid_step * report.locally_valid_steps
    components["closed_goals"] = weights.closed_goal * report.closed_goals
    components["premises_used"] = weights.premise_used * len(attempt.premises_used)

    lowered = attempt.lean_code.lower()
    for token in FORBIDDEN_TOKENS:
        if token in lowered:
            components[f"forbidden_{token}"] = (
                weights.axiom_penalty if token in {"axiom", "unsafe"} else weights.sorry_penalty
            )

    if report.first_error:
        components["first_error"] = weights.first_error_penalty

    return RewardBreakdown(total=sum(components.values()), components=components)


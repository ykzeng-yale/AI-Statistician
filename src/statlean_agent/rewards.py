"""Reward shaping for verifier-guided proof training."""

from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Iterable

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


PLACEHOLDER_TOKENS = ("sorry", "admit")
ALLOWABLE_PLACEHOLDER_TOKENS = ("sorry",)
ALWAYS_FORBIDDEN_TOKENS = ("axiom", "unsafe")
FORBIDDEN_TOKENS = PLACEHOLDER_TOKENS + ALWAYS_FORBIDDEN_TOKENS


@dataclass(frozen=True)
class PolicyTokenOccurrence:
    """A policy-relevant token occurrence in Lean source."""

    token: str
    line: int
    column: int
    allowed: bool = False

    @property
    def diagnostic(self) -> str:
        label = "allowed placeholder" if self.allowed else "forbidden token"
        return f"{label} `{self.token}` at line {self.line}, column {self.column}"


def score_attempt(
    attempt: ProofAttempt,
    report: VerificationReport,
    weights: RewardWeights = RewardWeights(),
    allowed_placeholders: Iterable[str] = (),
) -> RewardBreakdown:
    """Score a proof attempt with dense verifier-aware reward components."""

    components: dict[str, float] = {}
    violations = find_forbidden_tokens(attempt.lean_code, allowed_placeholders=allowed_placeholders)
    status = _normalize_status(report.status)
    effective_status = VerificationStatus.REJECTED if violations and status is VerificationStatus.ACCEPTED else status

    if effective_status is VerificationStatus.ACCEPTED:
        components["proof_complete"] = weights.proof_complete
    elif effective_status is VerificationStatus.TIMEOUT:
        components["timeout"] = weights.timeout_penalty
    else:
        components["rejected"] = weights.rejected_penalty

    components["locally_valid_steps"] = weights.locally_valid_step * report.locally_valid_steps
    components["closed_goals"] = weights.closed_goal * report.closed_goals
    components["premises_used"] = weights.premise_used * len(attempt.premises_used)

    for occurrence in violations:
        _add_component(
            components,
            f"forbidden_{occurrence.token}",
            weights.axiom_penalty if occurrence.token in ALWAYS_FORBIDDEN_TOKENS else weights.sorry_penalty,
        )

    if report.first_error:
        components["first_error"] = weights.first_error_penalty

    return RewardBreakdown(total=sum(components.values()), components=components)


def aggregate_reward_breakdowns(breakdowns: Iterable[RewardBreakdown]) -> RewardBreakdown:
    """Aggregate reward totals and component totals across attempts."""

    total = 0.0
    components: dict[str, float] = {}
    for breakdown in breakdowns:
        total += breakdown.total
        for key, value in breakdown.components.items():
            _add_component(components, key, value)
    return RewardBreakdown(total=total, components=components)


def scan_policy_tokens(
    lean_code: str,
    *,
    allowed_placeholders: Iterable[str] = (),
    policy_tokens: Iterable[str] = FORBIDDEN_TOKENS,
) -> tuple[PolicyTokenOccurrence, ...]:
    """Find policy-relevant Lean tokens while ignoring comments and strings."""

    tokens = tuple(dict.fromkeys(token.lower() for token in policy_tokens if token))
    if not tokens:
        return ()

    masked = _mask_comments_and_strings(lean_code)
    pattern = re.compile(r"\b(" + "|".join(re.escape(token) for token in tokens) + r")\b", re.IGNORECASE)
    allowed = {
        token.lower()
        for token in allowed_placeholders
        if token.lower() in ALLOWABLE_PLACEHOLDER_TOKENS and token.lower() not in ALWAYS_FORBIDDEN_TOKENS
    }
    occurrences: list[PolicyTokenOccurrence] = []
    for match in pattern.finditer(masked):
        token = match.group(1).lower()
        line, column = _line_column(lean_code, match.start())
        occurrences.append(
            PolicyTokenOccurrence(
                token=token,
                line=line,
                column=column,
                allowed=token in allowed,
            )
        )
    return tuple(occurrences)


def find_forbidden_tokens(
    lean_code: str,
    *,
    allowed_placeholders: Iterable[str] = (),
    policy_tokens: Iterable[str] = FORBIDDEN_TOKENS,
) -> tuple[PolicyTokenOccurrence, ...]:
    """Return only policy-token occurrences that are not explicitly allowed."""

    return tuple(
        occurrence
        for occurrence in scan_policy_tokens(
            lean_code,
            allowed_placeholders=allowed_placeholders,
            policy_tokens=policy_tokens,
        )
        if not occurrence.allowed
    )


def _add_component(components: dict[str, float], key: str, value: float) -> None:
    components[key] = components.get(key, 0.0) + value


def _normalize_status(status: VerificationStatus | str) -> VerificationStatus:
    if isinstance(status, VerificationStatus):
        return status

    normalized = str(status).strip().lower()
    for candidate in VerificationStatus:
        if normalized in {candidate.value, candidate.name.lower()}:
            return candidate
    return VerificationStatus.ERROR


def _line_column(source: str, offset: int) -> tuple[int, int]:
    line = source.count("\n", 0, offset) + 1
    line_start = source.rfind("\n", 0, offset) + 1
    return line, offset - line_start + 1


def _mask_comments_and_strings(source: str) -> str:
    """Replace comments and strings with spaces, preserving line/column offsets."""

    chars = list(source)
    index = 0
    block_depth = 0
    in_string = False
    in_line_comment = False
    while index < len(chars):
        current = chars[index]
        next_char = chars[index + 1] if index + 1 < len(chars) else ""

        if in_line_comment:
            if current == "\n":
                in_line_comment = False
            else:
                chars[index] = " "
            index += 1
            continue

        if block_depth:
            if current == "/" and next_char == "-":
                chars[index] = " "
                chars[index + 1] = " "
                block_depth += 1
                index += 2
                continue
            if current == "-" and next_char == "/":
                chars[index] = " "
                chars[index + 1] = " "
                block_depth -= 1
                index += 2
                continue
            if current != "\n":
                chars[index] = " "
            index += 1
            continue

        if in_string:
            if current == "\\":
                chars[index] = " "
                if index + 1 < len(chars) and chars[index + 1] != "\n":
                    chars[index + 1] = " "
                index += 2
                continue
            if current == '"':
                chars[index] = " "
                in_string = False
                index += 1
                continue
            if current != "\n":
                chars[index] = " "
            index += 1
            continue

        if current == "-" and next_char == "-":
            chars[index] = " "
            chars[index + 1] = " "
            in_line_comment = True
            index += 2
            continue
        if current == "/" and next_char == "-":
            chars[index] = " "
            chars[index + 1] = " "
            block_depth = 1
            index += 2
            continue
        if current == '"':
            chars[index] = " "
            in_string = True
            index += 1
            continue

        index += 1

    return "".join(chars)

"""Typed data contracts shared by agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class VerificationStatus(str, Enum):
    """Lean verification result for a proof attempt."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    ERROR = "error"


class BenchmarkTaskType(str, Enum):
    """Supported benchmark task modes."""

    FORMAL_ONLY = "formal_only"
    FORMALIZATION = "formalization"
    REPAIR = "repair"
    SUBGOAL_COMPLETION = "subgoal_completion"
    LEMMA_GROWTH = "lemma_growth"


class BenchmarkSplit(str, Enum):
    """Benchmark split label."""

    TRAIN = "train"
    DEV = "dev"
    TEST = "test"


@dataclass(frozen=True)
class StatObject:
    """Object extracted from a statistical claim."""

    name: str
    role: str
    type_hint: str | None = None


@dataclass(frozen=True)
class StatClaim:
    """Natural-language theorem candidate after ingestion."""

    claim_id: str
    source: str
    natural_language: str
    domain_tags: tuple[str, ...]
    objects: tuple[StatObject, ...] = ()
    assumptions: tuple[str, ...] = ()
    target: str | None = None
    difficulty: str = "seed"


@dataclass(frozen=True)
class LeanTask:
    """Formal Lean task to prove or repair."""

    task_id: str
    imports: tuple[str, ...]
    namespace: str
    statement: str
    allowed_sorry: bool = False
    tags: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    expected_patterns: tuple[str, ...] = ()


@dataclass(frozen=True)
class BenchmarkTask:
    """A benchmark item for formalization, proving, repair, or lemma growth."""

    task_id: str
    task_type: BenchmarkTaskType
    lean_task: LeanTask
    difficulty: str
    domain_tags: tuple[str, ...]
    split: BenchmarkSplit = BenchmarkSplit.DEV
    natural_language: str | None = None
    proof_state: str | None = None
    expected_premises: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProofTraceStep:
    """One verifier-observed tactic transition."""

    goal_before: str
    action: str
    result: str
    goal_after: str | None = None
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProofAttempt:
    """A model or agent proof attempt."""

    task_id: str
    agent_key: str
    lean_code: str
    premises_used: tuple[str, ...] = ()
    search_trace: tuple[ProofTraceStep, ...] = ()
    verifier_status: VerificationStatus = VerificationStatus.ERROR
    diagnostics: tuple[str, ...] = ()
    elapsed_ms: int | None = None


@dataclass(frozen=True)
class VerificationReport:
    """Verifier output normalized for training and repair."""

    task_id: str
    status: VerificationStatus
    locally_valid_steps: int = 0
    closed_goals: int = 0
    first_error: str | None = None
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class CuratedLemmaCandidate:
    """Candidate reusable lemma proposed for the statistics library."""

    name: str
    statement: str
    proof: str
    motivation_tasks: tuple[str, ...] = ()
    imports_added: tuple[str, ...] = ()
    reuse_count: int = 0
    generality_score: float = 0.0
    semantic_notes: str = ""


@dataclass(frozen=True)
class LemmaProposal:
    """Pre-curation proposal for a reusable lemma or constructor theorem."""

    proposal_id: str
    source_kind: str
    proposed_by: str
    candidate: CuratedLemmaCandidate
    source_task_ids: tuple[str, ...]
    domain_tags: tuple[str, ...] = ()
    expected_premises: tuple[str, ...] = ()
    required_gates: tuple[str, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    status: str = "proposed"
    notes: str = ""


@dataclass(frozen=True)
class CurationDecision:
    """Outcome of curation gates."""

    accepted: bool
    reasons: tuple[str, ...] = ()
    required_changes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CuratedLemmaLedgerEntry:
    """Auditable ledger record for a proposed reusable lemma."""

    ledger_id: str
    candidate: CuratedLemmaCandidate
    decision: CurationDecision
    source_task_ids: tuple[str, ...]
    verification_report_ids: tuple[str, ...] = ()
    status: str = "proposed"
    notes: str = ""


@dataclass(frozen=True)
class RewardBreakdown:
    """Reward components used for DPO/GRPO logging."""

    total: float
    components: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class EvalReport:
    """Aggregate benchmark evaluation metrics."""

    total_attempts: int
    accepted: int
    rejected: int
    timeout: int
    error: int
    average_reward: float
    pass_rate: float
    status_counts: dict[str, int] = field(default_factory=dict)
    reward_totals: dict[str, float] = field(default_factory=dict)
    average_reward_components: dict[str, float] = field(default_factory=dict)
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorktreeAssignment:
    """Isolated git worktree branch assignment."""

    agent_key: str
    branch: str
    path: str
    base_branch: str
    owns: tuple[str, ...]
    dry_run: bool = False

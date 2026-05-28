from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


QuestionId = Literal["normal_mean", "bernoulli_probability", "normal_variance", "constant_mean"]


@dataclass(frozen=True)
class StatisticalQuestion:
    id: str
    title: str
    dgp: str
    target: str
    dgp_family: str
    estimator_family: str
    true_params: dict[str, float]
    n_obs: int
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class EstimatorSpec:
    id: str
    question_id: str
    formula: str
    algorithm: str
    guarantee: str
    formal_obligation_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class FormalObligation:
    id: str
    title: str
    english: str
    formal_statement: str
    proof_body: str
    tags: tuple[str, ...]
    expected_lemmas: tuple[str, ...] = ()
    source: str = "Mathlib"
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalHit:
    obligation_id: str
    score: float
    source: str
    matched_terms: tuple[str, ...] = ()


@dataclass
class ProofCheck:
    obligation_id: str
    ok: bool
    proof_body: str
    verifier: str
    verification_strength: str = "unknown"
    kernel_verified: bool = False
    elapsed_ms: int = 0
    errors: list[str] = field(default_factory=list)
    retrieval_hits: list[RetrievalHit] = field(default_factory=list)


@dataclass(frozen=True)
class ProofAttemptRecord:
    """Training/audit row for one proof verification attempt.

    This is proof-level data, not tactic-state data. It is enough for
    verifier-filtered whole-proof SFT/rejection sampling and for measuring
    retrieval context, but it does not yet support tactic-level process reward.
    """

    schema_version: int
    attempt_id: str
    obligation_id: str
    title: str
    tags: tuple[str, ...]
    source: str
    expected_lemmas: tuple[str, ...]
    depends_on: tuple[str, ...]
    formal_statement: str
    proof_body: str
    candidate: str
    candidate_hash: str
    verifier: str
    verification_strength: str
    kernel_verified: bool
    ok: bool
    reward: float
    elapsed_ms: int
    errors: tuple[str, ...]
    first_error: str
    retrieval_hits: tuple[RetrievalHit, ...]
    supervision_target: str


@dataclass(frozen=True)
class AlgorithmSpec:
    id: str
    estimator_id: str
    code_summary: str
    implementation_hash: str = ""
    registry_status: str = "unknown"
    version: str = ""


@dataclass
class SimulationMetrics:
    n_runs: int
    n_failed: int
    bias: float
    relative_bias: float
    rmse: float
    empirical_se: float
    mean_estimated_se: float
    coverage_95: float


@dataclass
class SimulationReport:
    question_id: str
    algorithm_id: str
    metrics: SimulationMetrics
    pass_bias: bool
    pass_coverage: bool
    pass_se_calibration: bool
    feedback: str


@dataclass
class SystemReport:
    question: StatisticalQuestion
    estimator: EstimatorSpec
    proofs: list[ProofCheck]
    algorithm: AlgorithmSpec
    simulation: SimulationReport
    status: Literal["ACCEPTED", "FORMAL_BLOCKED", "SIMULATION_BLOCKED"]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

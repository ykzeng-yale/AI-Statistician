from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping


RESEARCH_EVIDENCE_DIMENSIONS = (
    "theory",
    "scientific_code",
    "empirical",
    "formal",
)
TASK_INTENT_REQUIREMENTS = frozenset(
    {"required", "optional", "not_applicable"}
)


def research_dimension_requirements(
    task_intent: Mapping[str, Any] | None,
) -> dict[str, str]:
    """Return the complete research-evidence contract for an explicit task intent.

    An empty mapping means the caller is using the legacy evaluation profile. Once
    an operator supplies any task intent, omitted research dimensions are optional
    rather than silently becoming mandatory.
    """

    if not task_intent:
        return {}
    normalized = {
        str(dimension): str(requirement).strip().lower()
        for dimension, requirement in task_intent.items()
    }
    invalid = sorted(
        {
            requirement
            for requirement in normalized.values()
            if requirement not in TASK_INTENT_REQUIREMENTS
        }
    )
    if invalid:
        raise ValueError(
            "task_intent requirements must be required, optional, or "
            "not_applicable; invalid=" + ", ".join(invalid)
        )
    return {
        dimension: normalized.get(dimension, "optional")
        for dimension in RESEARCH_EVIDENCE_DIMENSIONS
    }


def research_task_intent_requirement(
    task_intent: Mapping[str, Any] | None,
    dimension: str,
    *,
    default: str = "optional",
) -> str:
    """Return one validated task-intent requirement outside the core four lanes."""

    normalized_default = str(default).strip().lower()
    if normalized_default not in TASK_INTENT_REQUIREMENTS:
        raise ValueError("default task-intent requirement is invalid")
    if not task_intent:
        return normalized_default
    normalized = {
        str(key): str(value).strip().lower()
        for key, value in task_intent.items()
    }
    invalid = sorted(
        {
            requirement
            for requirement in normalized.values()
            if requirement not in TASK_INTENT_REQUIREMENTS
        }
    )
    if invalid:
        raise ValueError(
            "task_intent requirements must be required, optional, or "
            "not_applicable; invalid=" + ", ".join(invalid)
        )
    return normalized.get(str(dimension), normalized_default)


@dataclass(frozen=True)
class OpenResearchQuestion:
    id: str
    title: str
    description: str
    tags: tuple[str, ...] = ()
    task_intent: dict[str, str] = field(default_factory=dict)
    estimator_execution_contract: dict[str, Any] = field(default_factory=dict)


def research_question_payload(
    question: OpenResearchQuestion,
    *,
    include_task_intent: bool = False,
    include_estimator_execution_contract: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }
    if include_task_intent and question.task_intent:
        payload["task_intent"] = dict(question.task_intent)
    if (
        include_estimator_execution_contract
        and question.estimator_execution_contract
    ):
        payload["estimator_execution_contract"] = deepcopy(
            question.estimator_execution_contract
        )
    return payload


@dataclass(frozen=True)
class ResearchProblemSpec:
    question_id: str
    problem_class: str
    dgp: str
    estimand: str
    assumptions: tuple[str, ...]
    asymptotic_regime: str
    diagnostics: tuple[str, ...]
    stress_tests: tuple[str, ...] = ()
    extraction_evidence: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchAlgorithmSpec:
    id: str
    summary: str
    implementation_hash: str
    version: str = "v1"
    registry_status: str = "vetted"


@dataclass(frozen=True)
class CandidateProcedure:
    id: str
    name: str
    role: Literal["estimator", "test", "prediction_procedure"]
    formula: str
    informal_derivation: str
    algorithm: str
    theorem_goals: tuple[str, ...]
    simulation_design: str
    limitations: tuple[str, ...] = ()
    algorithm_spec: ResearchAlgorithmSpec | None = None


@dataclass(frozen=True)
class TheoremGoal:
    id: str
    title: str
    informal_statement: str
    proof_strategy: str
    status: Literal["PROVABLE_NOW", "FORMAL_GAP"]
    required_primitives: tuple[str, ...] = ()
    proof_obligations: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeCard:
    id: str
    title: str
    source_type: str
    location: str
    summary: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class PaperSourceHit:
    id: str
    title: str
    source_type: str
    source_path: str
    topic: str
    journal: str = ""
    publication_date: str = ""
    doi: str = ""
    url: str = ""
    score: float = 0.0
    matched_terms: tuple[str, ...] = ()
    summary: str = ""
    withheld_fields: tuple[str, ...] = ()


@dataclass
class FormalSubclaim:
    id: str
    title: str
    status: Literal["PROVED", "FORMAL_GAP", "FAILED"]
    claim: str
    claim_type: Literal["lean_obligation", "theory_gap"] = "lean_obligation"
    proof_obligation_id: str | None = None
    lean_statement: str | None = None
    formalization_status: str = "unknown"
    verifier: str | None = None
    verification_strength: str = "unknown"
    kernel_verified: bool = False
    elapsed_ms: int = 0
    errors: list[str] = field(default_factory=list)
    gap_reason: str | None = None
    artifact_path: str | None = None
    proof_dependencies: tuple[str, ...] = ()
    formal_source_hits: list[dict[str, Any]] = field(default_factory=list)
    primitive_formal_source_hits: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


@dataclass
class SimulationDiagnosis:
    status: Literal[
        "OK",
        "THEORY_OR_PROCEDURE_ISSUE",
        "IMPLEMENTATION_OR_NUMERICAL_ISSUE",
        "ENVIRONMENT_OR_DGP_ISSUE",
        "INSUFFICIENT_MC_PRECISION",
    ]
    escalate_to: Literal[
        "none",
        "theory_developer",
        "algorithm_engineer",
        "simulator_environment",
        "rerun_more_mc",
    ]
    failed_diagnostics: tuple[str, ...] = ()
    failed_stress_tests: tuple[str, ...] = ()
    rationale: str = ""
    metric_evidence: dict[str, float] = field(default_factory=dict)


@dataclass
class ResearchSimulation:
    procedure_id: str
    design: str
    metrics: dict[str, float]
    passed: bool
    feedback: str
    stress_tests: tuple[str, ...] = ()
    stress_test_metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    diagnosis: SimulationDiagnosis | None = None


@dataclass
class ResearchReport:
    question: OpenResearchQuestion
    problem: ResearchProblemSpec
    procedures: list[CandidateProcedure]
    knowledge: list[KnowledgeCard]
    paper_sources: list[PaperSourceHit]
    formal_subclaims: list[FormalSubclaim]
    simulations: list[ResearchSimulation]
    theorem_goals: list[TheoremGoal]
    theory_plan: dict[str, Any]
    status: Literal[
        "RESEARCH_TRACE_READY_WITH_FORMAL_GAPS",
        "SIMULATION_FLAGGED_WITH_FORMAL_GAPS",
        "FORMAL_BLOCKED",
    ]
    limitations: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

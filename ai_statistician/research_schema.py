from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping

from .estimator_interface_contract import frozen_estimator_execution_contract_errors
from .fingerprint import stable_hash


RESEARCH_EVIDENCE_DIMENSIONS = (
    "theory",
    "scientific_code",
    "empirical",
    "formal",
)
TASK_INTENT_REQUIREMENTS = frozenset(
    {"required", "optional", "not_applicable"}
)


def frozen_formal_target_contract_errors(
    contract: Any,
    *,
    label: str = "formal_target_contract",
    required: bool = False,
) -> list[str]:
    """Validate operator-frozen target identity without interpreting Lean."""

    if not contract:
        return [f"{label} is required"] if required else []
    if not isinstance(contract, Mapping):
        return [f"{label} must be an object"]
    errors: list[str] = []
    if contract.get("schema_version") != 1:
        errors.append(f"{label}.schema_version must equal 1")
    for field_name in (
        "target_id",
        "declaration_name",
        "lean_source_prefix",
        "lean_source_prefix_sha256",
    ):
        if not isinstance(contract.get(field_name), str) or not str(
            contract.get(field_name, "")
        ).strip():
            errors.append(f"{label}.{field_name} must be a non-empty string")
    proof_visibility = str(contract.get("proof_visibility", "") or "")
    if proof_visibility != "hidden":
        errors.append(f"{label}.proof_visibility must equal hidden")
    source = str(contract.get("lean_source_prefix", "") or "")
    expected_hash = str(contract.get("lean_source_prefix_sha256", "") or "")
    if source and expected_hash:
        observed_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
        if observed_hash != expected_hash:
            errors.append(f"{label}.lean_source_prefix_sha256 does not match source")
    environment = contract.get("lean_environment", {})
    if not isinstance(environment, Mapping):
        errors.append(f"{label}.lean_environment must be an object")
    else:
        for field_name in (
            "project_id",
            "lean_toolchain",
            "lake_manifest_sha256",
        ):
            if not isinstance(environment.get(field_name), str) or not str(
                environment.get(field_name, "")
            ).strip():
                errors.append(
                    f"{label}.lean_environment.{field_name} must be a non-empty string"
                )
    required_primitives = contract.get("required_primitives", [])
    if not isinstance(required_primitives, list) or any(
        not isinstance(value, str) or not value.strip()
        for value in required_primitives
    ):
        errors.append(f"{label}.required_primitives must be a list of strings")
    return errors


def _normalized_task_intent(task_intent: Mapping[str, Any]) -> dict[str, str]:
    normalized = {
        str(dimension): str(requirement).strip().lower()
        for dimension, requirement in task_intent.items()
    }
    invalid = sorted(set(normalized.values()) - TASK_INTENT_REQUIREMENTS)
    if invalid:
        raise ValueError(
            "task_intent requirements must be required, optional, or "
            "not_applicable; invalid=" + ", ".join(invalid)
        )
    return normalized


def research_dimension_requirements(
    task_intent: Mapping[str, Any] | None,
) -> dict[str, str]:
    """Complete an explicit operator contract; empty retains legacy evaluation."""
    if not task_intent:
        return {}
    normalized = _normalized_task_intent(task_intent)
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
    return _normalized_task_intent(task_intent).get(str(dimension), normalized_default)


@dataclass(frozen=True)
class OpenResearchQuestion:
    id: str
    title: str
    description: str
    tags: tuple[str, ...] = ()
    task_intent: dict[str, str] = field(default_factory=dict)
    estimator_execution_contract: dict[str, Any] = field(default_factory=dict)
    formal_target_contract: dict[str, Any] = field(default_factory=dict)


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
    if question.formal_target_contract:
        payload["formal_target_contract"] = deepcopy(
            question.formal_target_contract
        )
    return payload


def research_workspace_authorization_fingerprint(
    question: OpenResearchQuestion, runtime_context: Mapping[str, Any] | None,
    workspace_identity: Mapping[str, Any],
) -> str:
    """Bind a retained workspace to root intent without freezing model planning."""
    context = runtime_context if isinstance(runtime_context, Mapping) else {}
    dimensions: dict[str, str] = {}
    for scope in (context, context.get("architect_context", {})):
        contract = scope.get("runtime_requested_evidence_contract", {}) if isinstance(scope, Mapping) else {}
        raw = contract.get("dimension_requirements", {}) if isinstance(contract, Mapping) else {}
        if isinstance(raw, Mapping) and raw:
            dimensions = research_dimension_requirements(raw)
            break
    return stable_hash({
        "schema_version": 1,
        "question": research_question_payload(question, include_task_intent=False),
        "operator_frozen_dimension_requirements": dimensions,
        "workspace_identity": deepcopy(dict(workspace_identity)),
    })


def load_open_research_questions(path: Path) -> list[OpenResearchQuestion]:
    """Load public research intent without importing legacy task registries."""

    if path.suffix.lower() in {".md", ".markdown", ".txt"}:
        return _load_text_research_questions(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["questions"] if isinstance(payload, dict) and "questions" in payload else payload
    questions: list[OpenResearchQuestion] = []
    for row in rows:
        raw_task_intent = row.get("task_intent", {})
        if not isinstance(raw_task_intent, dict):
            raise ValueError("research question task_intent must be an object")
        task_intent = {
            str(dimension): str(requirement)
            for dimension, requirement in raw_task_intent.items()
        }
        if any(
            requirement not in TASK_INTENT_REQUIREMENTS
            for requirement in task_intent.values()
        ):
            raise ValueError(
                "research question task_intent requirements must be required, "
                "optional, or not_applicable"
            )
        estimator_execution_contract = row.get(
            "estimator_execution_contract", {}
        )
        contract_errors = frozen_estimator_execution_contract_errors(
            estimator_execution_contract,
            label="research question estimator_execution_contract",
            required="estimator_execution_contract" in row,
        )
        if contract_errors:
            raise ValueError("; ".join(contract_errors))
        formal_target_contract = row.get("formal_target_contract", {})
        formal_contract_errors = frozen_formal_target_contract_errors(
            formal_target_contract,
            label="research question formal_target_contract",
            required="formal_target_contract" in row,
        )
        if formal_contract_errors:
            raise ValueError("; ".join(formal_contract_errors))
        if (
            formal_target_contract
            and task_intent.get("formal") == "not_applicable"
        ):
            raise ValueError(
                "research question formal_target_contract conflicts with "
                "task_intent.formal=not_applicable"
            )
        questions.append(
            OpenResearchQuestion(
                id=str(row["id"]),
                title=str(row.get("title", row["id"])),
                description=str(row["description"]),
                tags=tuple(str(tag) for tag in row.get("tags", ())),
                task_intent=task_intent,
                estimator_execution_contract=(
                    deepcopy(dict(estimator_execution_contract))
                    if isinstance(estimator_execution_contract, dict)
                    else {}
                ),
                formal_target_contract=(
                    deepcopy(dict(formal_target_contract))
                    if isinstance(formal_target_contract, dict)
                    else {}
                ),
            )
        )
    return questions


def _load_text_research_questions(path: Path) -> list[OpenResearchQuestion]:
    text = path.read_text(encoding="utf-8")
    heading_re = re.compile(r"^#{1,3}\s+([A-Za-z0-9_.-]+)\s*:\s*(.+?)\s*$")
    sections: list[tuple[str, str, list[str]]] = []
    current_id: str | None = None
    current_title: str | None = None
    current_lines: list[str] = []
    for raw_line in text.splitlines():
        match = heading_re.match(raw_line.strip())
        if match:
            if current_id and current_title:
                sections.append((current_id, current_title, current_lines))
            current_id = match.group(1)
            current_title = match.group(2).strip()
            current_lines = []
        elif current_id:
            current_lines.append(raw_line)
    if current_id and current_title:
        sections.append((current_id, current_title, current_lines))
    if not sections:
        return [_single_text_question(path, text)]

    questions: list[OpenResearchQuestion] = []
    for question_id, title, lines in sections:
        tags: tuple[str, ...] = ()
        body_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith("tags:"):
                tags = _parse_tags(stripped.split(":", 1)[1])
            else:
                body_lines.append(line)
        description = "\n".join(body_lines).strip()
        if not description:
            description = title
        questions.append(
            OpenResearchQuestion(
                id=_safe_question_id(question_id),
                title=title,
                description=description,
                tags=tags,
            )
        )
    return questions


def _single_text_question(path: Path, text: str) -> OpenResearchQuestion:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and lines[0].startswith("#"):
        title = lines[0].lstrip("#").strip()
        description = "\n".join(lines[1:]).strip() or title
    elif lines:
        title = lines[0]
        description = "\n".join(lines[1:]).strip() or title
    else:
        title = path.stem.replace("_", " ").title()
        description = title
    return OpenResearchQuestion(
        id=_safe_question_id(path.stem),
        title=title,
        description=description,
        tags=(),
    )


def _parse_tags(raw: str) -> tuple[str, ...]:
    return tuple(
        tag.strip().lower().replace(" ", "_")
        for tag in raw.split(",")
        if tag.strip()
    )


def _safe_question_id(raw: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw.strip())
    slug = slug.strip("_.-")
    return slug or "open_research_question"


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

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .client_tool_loop import (
    ClientToolExecutionContext,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    externalize_client_tool_text_documents,
    run_bounded_client_tool_loop,
)
from .cross_family_eval_protocol import withhold_confirmatory_evaluation_seed
from .estimator_interface_contract import (
    frozen_estimator_execution_contract_clause_ids,
    frozen_estimator_execution_contract_empirical_claim_ids,
)
from .fingerprint import stable_hash
from .packet_validation import PacketValidationError
from .metric_protocol_finding_ledger import (
    METRIC_PROTOCOL_FINDING_RETRACTED_RUNTIME_CONTRACT_CONFLICT,
    METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_ARTIFACT,
    METRIC_PROTOCOL_FINDING_UNRESOLVED,
    active_metric_protocol_finding_ledger,
    metric_protocol_finding_ledger_fingerprint,
    update_metric_protocol_finding_ledger,
)
from .model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnRequest,
    GeneratorBackend,
    resolve_generator_model,
)
from .research_schema import OpenResearchQuestion, research_question_payload
from .research_source_library import (
    RESEARCH_SOURCE_LIST_TOOL,
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_SEARCH_TOOL,
    ResearchSourceSnapshot,
    execute_research_source_client_tool,
    research_source_client_tools,
)
from .scientific_sandbox import (
    SCIENTIFIC_SANDBOX_LANGUAGES,
    ScientificEstimatorBinding,
    execute_scientific_sandbox,
    normalized_generated_code_language,
    normalized_scientific_dependencies,
)
from .scientific_project import (
    normalized_scientific_project_files,
    scientific_main_path,
    scientific_project_hash,
)
from .theory_workspace import (
    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
    read_theory_document_lines,
    search_theory_document_lines,
    theory_document_client_tools,
)

GENERATED_CODE_SEMANTIC_REVIEW_SCHEMA_VERSION = 39
GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE = "GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE"
GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY = "Generated-code semantic review may reject an artifact, but is not acceptance or proof evidence."
GENERATED_CODE_SEMANTIC_REVIEW_TRANSPORT = "model_authored_markdown_review_with_artifact_scoped_authority_v17"
GENERATED_CODE_SEMANTIC_REVIEW_SUBMIT_TOOL = "submit_generated_code_semantic_review"
GENERATED_CODE_SEMANTIC_REVIEW_PROBE_TOOL = "run_exact_estimator_review_probe"
GENERATED_CODE_SEMANTIC_REVIEW_READ_SOURCE_TOOL = "read_current_generated_source"
GENERATED_CODE_REVIEW_EXTERNALIZE_MIN_CHARACTERS = 1200
GENERATED_CODE_SEMANTIC_REVIEWER_SCOPE_CONTRACT: dict[str, Any] = {
    "in_scope": (
        "implemented statistical object and metric meaning", "declared assumptions and theory alignment",
        "executable interface and actual runtime arguments", "experiment non-vacuity and identifiability",
        "source implementation of a frozen model-authored acceptance protocol",
    ),
    "downstream_empirical_evaluator_scope": (
        "realized hidden-cohort metric values and pass/fail outcomes",
        "sampling uncertainty observed only after the source is frozen",
        "statistical power observed in a finite run",
        "computational efficiency and stopping-time performance",
    ),
    "source_defect_evidence_rule": "A source defect needs direct source, interface, argument, "
    "or emitted-meaning evidence; a realized threshold failure remains downstream evidence.",
    "metric_dimension_rule": "Inspect whether exact source derives acceptance from every "
    "load-bearing check; favorable outcomes alone establish nothing.",
    "runtime_argument_rule": "Every declared runtime argument must affect the artifact as "
    "declared or be justified as immaterial.",
    "prior_finding_rule": "A prior finding is a claim, not evidence; retract it when the exact "
    "artifact supplies no direct evidence for it.",
}
GENERATED_CODE_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS = ("AlgorithmEngineer", "SimulationEvaluator")
GENERATED_CODE_SEMANTIC_REVIEW_FINDING_SEVERITIES = ("low", "medium", "high", "critical")
GENERATED_CODE_SEMANTIC_REVIEW_PRIOR_FINDING_STATUSES = (
    METRIC_PROTOCOL_FINDING_UNRESOLVED, METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_ARTIFACT,
    METRIC_PROTOCOL_FINDING_RETRACTED_RUNTIME_CONTRACT_CONFLICT,
)
GENERATED_CODE_SEMANTIC_REVIEW_CLOSED_PRIOR_FINDING_STATUSES = frozenset({
    METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_ARTIFACT, METRIC_PROTOCOL_FINDING_RETRACTED_RUNTIME_CONTRACT_CONFLICT,
})
GENERATED_CODE_SEMANTIC_REVIEW_FINDING_ID_PREFIX = "generated_code_semantic_finding:"
SOURCE_REVISION_SCOPE_NO_PARENT_CHANGE = "CURRENT_SOURCE_REWRITE_SUFFICIENT"
SOURCE_REVISION_SCOPE_PARENT_CHANGE = "CROSS_ARTIFACT_RESOLUTION_REQUIRED"
SOURCE_REVISION_SCOPES = (SOURCE_REVISION_SCOPE_NO_PARENT_CHANGE, SOURCE_REVISION_SCOPE_PARENT_CHANGE)


def _exact_estimator_probe_targets(
    review_material: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return only immutable Algorithm artifacts safe to bind into a probe."""

    if review_material.get("source_subsystem") != "AlgorithmEngineer":
        return {}
    targets: dict[str, dict[str, Any]] = {}
    for raw in review_material.get("exact_executed_artifacts", []) or []:
        if not isinstance(raw, Mapping) or not isinstance(
            raw.get("source_row"), Mapping
        ):
            continue
        row = raw["source_row"]
        artifact_id = str(raw.get("artifact_id", "") or "").strip()
        source = str(raw.get("exact_source_code", "") or "")
        language = normalized_generated_code_language(row.get("language"))
        source_hash = stable_hash(source)
        try:
            project_files = normalized_scientific_project_files(
                raw.get("exact_project_files", []),
                language=language,
            )
            project_hash = scientific_project_hash(
                language=language,
                code=source,
                project_files=project_files,
            )
        except ValueError:
            continue
        persisted_project_hash = str(raw.get("exact_project_hash", "") or "")
        if not (
            artifact_id
            and artifact_id not in targets
            and source
            and language in SCIENTIFIC_SANDBOX_LANGUAGES
            and raw.get("exact_source_hash") == source_hash
            and row.get("script_hash") == source_hash
            and persisted_project_hash == project_hash
            and (
                row.get("smoke_passed") is True
                or row.get("execution_smoke_passed") is True
            )
        ):
            continue
        targets[artifact_id] = {
            "artifact_id": artifact_id,
            "language": language,
            "code": source,
            "code_hash": source_hash,
            "dependencies": normalized_scientific_dependencies(
                row.get("dependencies", []), language=language
            ),
            "project_files": project_files,
            "project_hash": project_hash,
        }
    return targets


def generated_code_semantic_review_finding_id(
    *,
    question_id: str,
    source_subsystem: str,
    finding: Mapping[str, Any],
    preserve_existing: bool = True,
) -> str:
    existing = str(finding.get("finding_id", "") or "").strip()
    if preserve_existing and existing.startswith(
        GENERATED_CODE_SEMANTIC_REVIEW_FINDING_ID_PREFIX
    ):
        return existing
    identity = {
        "question_id": str(question_id),
        "source_subsystem": str(source_subsystem),
        "severity": str(finding.get("severity", "") or "").strip(),
        "category": str(finding.get("category", "") or "").strip(),
        "summary": str(finding.get("summary", "") or "").strip(),
        "observed_behavior": str(
            finding.get("observed_behavior", "") or ""
        ).strip(),
        "expected_behavior": str(
            finding.get("expected_behavior", "") or ""
        ).strip(),
        "evidence_refs": [],
    }
    return GENERATED_CODE_SEMANTIC_REVIEW_FINDING_ID_PREFIX + stable_hash(
        identity
    )[:20]


def normalize_generated_code_semantic_review_findings(
    *,
    question_id: str,
    source_subsystem: str,
    findings: Any,
    preserve_existing_ids: bool = True,
) -> Any:
    # Preserve malformed observations for the existing packet validator.
    if not isinstance(findings, list):
        return deepcopy(findings)
    rows: list[Any] = []
    for raw in findings:
        if not isinstance(raw, Mapping):
            rows.append(deepcopy(raw))
            continue
        row = _descriptive_finding(raw)
        prior_finding_id = str(raw.get("prior_finding_id", "") or "").strip()
        row["finding_id"] = prior_finding_id or generated_code_semantic_review_finding_id(
            question_id=question_id,
            source_subsystem=source_subsystem,
            finding=row,
            preserve_existing=preserve_existing_ids,
        )
        rows.append(row)
    return rows


def _descriptive_finding(value: Mapping[str, Any]) -> dict[str, Any]:
    """Project reviewer output to observations, never a repair recipe."""

    summary = str(value.get("summary", "") or "").strip()
    observed = str(value.get("observed_behavior", "") or "").strip()
    expected = str(value.get("expected_behavior", "") or "").strip()
    return {
        "severity": str(value.get("severity", "") or "").strip().lower(),
        "category": str(value.get("category", "") or "").strip(),
        "summary": summary,
        "observed_behavior": observed,
        "expected_behavior": expected,
        "evidence_refs": [],
    }


def _active_prior_findings(
    review_material: Mapping[str, Any],
) -> list[dict[str, Any]]:
    observations = review_material.get("prior_semantic_observations", {})
    if not isinstance(observations, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    for raw in observations.get("active_prior_finding_ledger", []) or []:
        if not isinstance(raw, Mapping):
            continue
        finding_id = str(raw.get("finding_id", "") or "").strip()
        if not finding_id:
            continue
        rows.append(deepcopy(dict(raw)))
    return rows
def _numeric_summary(values: Sequence[Any]) -> dict[str, Any]:
    finite = [
        float(value)
        for value in values
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    ]
    if not finite:
        return {}
    return {
        "count": len(finite),
        "min": min(finite),
        "max": max(finite),
        "mean": sum(finite) / len(finite),
    }


def _prompt_projection_value(
    value: Any,
    *,
    key: str = "",
    max_sequence_items: int = 48,
    max_string_chars: int = 40_000,
) -> Any:
    if isinstance(value, Mapping):
        return {
            str(child_key): _prompt_projection_value(
                child,
                key=str(child_key),
                max_sequence_items=max_sequence_items,
                max_string_chars=max_string_chars,
            )
            for child_key, child in value.items()
        }
    if isinstance(value, (list, tuple)):
        rows = list(value)
        if len(rows) <= max_sequence_items:
            return [
                _prompt_projection_value(
                    child,
                    max_sequence_items=max_sequence_items,
                    max_string_chars=max_string_chars,
                )
                for child in rows
            ]
        return {
            "projection_kind": "bounded_sequence_summary",
            "length": len(rows),
            "head": [
                _prompt_projection_value(child)
                for child in rows[: min(8, len(rows))]
            ],
            "tail": [
                _prompt_projection_value(child)
                for child in rows[-min(8, len(rows)) :]
            ],
            "numeric_summary": _numeric_summary(rows),
            "full_value_hash": stable_hash(rows),
            "full_value_in_prompt": False,
        }
    if isinstance(value, str) and len(value) > max_string_chars:
        preserve_source = key in {
            "code",
            "exact_source_code",
            "source_code",
        }
        if preserve_source:
            return value
        return {
            "projection_kind": "bounded_string_summary",
            "length": len(value),
            "head": value[:20_000],
            "tail": value[-4_000:],
            "full_value_hash": stable_hash(value),
            "full_value_in_prompt": False,
        }
    return deepcopy(value)


_SEMANTIC_METRIC_FIELDS = frozenset(
    {
        "acceptance_authority_kind",
        "acceptance_authority_rationale",
        "aggregation",
        "artifact_id",
        "authority_requirement_fingerprint",
        "authority_requirement_set_id",
        "authority_source_subsystem",
        "boundary",
        "contract_id",
        "evaluator_mode",
        "gate_field_authorities",
        "gate_field_authority_mode",
        "lower",
        "measurement_protocol",
        "metric_path",
        "metric_semantics",
        "metric_value_kind",
        "minimum_pass_count",
        "minimum_pass_fraction",
        "operator",
        "required",
        "required_runtime_replicates",
        "requirement_id",
        "source_anchors",
        "target_subsystems",
        "threshold",
        "tolerance",
        "upper",
    }
)
_SEMANTIC_REVIEW_RESULT_VALUE_KEYS = frozenset(
    {"exact_result", "exact_smoke_result", "metrics"}
)
_SEMANTIC_REVIEW_EMPIRICAL_OUTCOME_KEYS = frozenset(
    {
        "empirical_metric_requirements_preexecution_review",
        "execution_envelope_hash",
        "exact_result_hash",
        "metric_contract_evaluation",
        "metric_gate_errors",
        "metric_gate_policy_mode",
        "metric_gate_targets",
        "metric_protocol_execution_authorized",
        "promotion_ready",
        "prototype_status",
        "registered_simulation_passed",
        "result_hash",
        "simulations",
        "simulation_evidence_status",
        "simulation_passed",
        "stderr_summary",
        "stdout_summary",
    }
)


def _semantic_result_schema(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {
            "value_kind": "object",
            "field_count": len(value),
            "fields": {
                str(key): _semantic_result_schema(child)
                for key, child in value.items()
            },
        }
    if isinstance(value, (list, tuple)):
        kinds = sorted(
            {
                _semantic_result_schema(child)["value_kind"]
                for child in value[:64]
            }
        )
        return {
            "value_kind": "array",
            "length": len(value),
            "observed_item_kinds": kinds,
        }
    if isinstance(value, bool):
        return {"value_kind": "boolean"}
    if isinstance(value, (int, float)):
        return {
            "value_kind": "number",
            "finite": math.isfinite(float(value)),
        }
    if isinstance(value, str):
        return {"value_kind": "string", "length": len(value)}
    if value is None:
        return {"value_kind": "null"}
    return {"value_kind": type(value).__name__}


def _semantic_metric_projection(value: Any) -> Any:
    if not isinstance(value, (list, tuple)):
        return []
    return [
        {
            str(key): deepcopy(child)
            for key, child in row.items()
            if str(key) in _SEMANTIC_METRIC_FIELDS
        }
        for row in value
        if isinstance(row, Mapping)
    ]


def _semantic_review_model_input(value: Any, *, parent_key: str = "") -> Any:
    """Project exact audit material to the semantic reviewer's authority."""

    if isinstance(value, Mapping):
        projected: dict[str, Any] = {}
        for raw_key, child in value.items():
            key = str(raw_key)
            if key in _SEMANTIC_REVIEW_EMPIRICAL_OUTCOME_KEYS:
                continue
            if key in {
                "empirical_metric_requirements",
                "assigned_empirical_metric_requirements",
                "metric_contracts",
            }:
                projected[key] = _semantic_metric_projection(child)
                continue
            if key in _SEMANTIC_REVIEW_RESULT_VALUE_KEYS:
                projected[f"{key}_schema"] = {
                    "schema": _semantic_result_schema(child),
                    "realized_values_withheld": True,
                    "value_authority_owner": "EmpiricalEvaluator",
                }
                continue
            if parent_key == "source_manifest_summary" and (
                key.endswith("_passed")
                or "metric_gate" in key
                or "typed_metric_contracts" in key
            ):
                continue
            projected[key] = _semantic_review_model_input(
                child,
                parent_key=key,
            )
        return projected
    if isinstance(value, (list, tuple)):
        return [
            _semantic_review_model_input(child, parent_key=parent_key)
            for child in value
        ]
    return deepcopy(value)


def generated_code_semantic_review_prompt_projection(
    review_material: Mapping[str, Any],
) -> dict[str, Any]:
    projected = _prompt_projection_value(
        _semantic_review_model_input(review_material)
    )
    if review_material.get("confirmatory_empirical_evidence_eligible") is True:
        return withhold_confirmatory_evaluation_seed(projected)
    return projected


def _question_context(question: OpenResearchQuestion) -> dict[str, Any]:
    return research_question_payload(question)


def _reviewer_scope_contract(
    review_material: Mapping[str, Any],
) -> dict[str, Any]:
    contract = deepcopy(GENERATED_CODE_SEMANTIC_REVIEWER_SCOPE_CONTRACT)
    contract["artifact_authority_rule"] = (
        "The verdict, findings, and rationale cover only current_target_artifacts "
        "and exact upstream_generated_dependency artifacts present in this review. "
        "Question text and supporting context define obligations but do not prove "
        "that an absent artifact implemented them. Current source cannot establish a "
        "separately owned subsystem artifact or public ABI unless that exact accepted "
        "dependency is present; embedded code belongs only to the current artifact."
    )
    phase = str(review_material.get("empirical_evaluation_phase", "") or "")
    if phase != "executable_evaluator_authoring":
        return contract
    contract["in_scope"] = [
        *contract["in_scope"],
        "source-authored DGP, measurements, acceptance decision, and requested precision",
        "whether requested_runtime_replicates is fixed before hidden outcomes",
    ]
    contract["downstream_empirical_evaluator_scope"] = [
        "realized hidden-cohort values",
        "the observed acceptance_passed outcome on the hidden cohort",
        "post-freeze runtime failures not caused by the reviewed source",
    ]
    contract["executable_evaluator_authority_rule"] = (
        "The current run_sandbox source owns the scientific evaluation protocol. "
        "Review its DGP, measurements, decision rule, acceptance_passed semantics, "
        "and requested_runtime_replicates directly; only later realized hidden "
        "outcomes remain downstream."
    )
    return contract


def _current_target_role(review_material: Mapping[str, Any]) -> dict[str, Any]:
    source_subsystem = str(review_material.get("source_subsystem", "") or "")
    phase = str(review_material.get("empirical_evaluation_phase", "") or "")
    entrypoints = {
        "AlgorithmEngineer": "run_estimator",
        "SimulationEvaluator": "run_sandbox",
    }
    return {
        "source_subsystem": source_subsystem,
        "source_manifest_id": str(review_material.get("source_manifest_id", "") or ""),
        "empirical_evaluation_phase": phase,
        "artifact_ids": [
            str(row.get("artifact_id", "") or "")
            for row in review_material.get("exact_executed_artifacts", []) or []
            if isinstance(row, Mapping) and str(row.get("artifact_id", "") or "")
        ],
        "public_entrypoint": entrypoints.get(source_subsystem, ""),
        "authority_output_fields": (
            ["acceptance_passed", "requested_runtime_replicates"]
            if source_subsystem == "SimulationEvaluator"
            and phase == "executable_evaluator_authoring"
            else []
        ),
        "review_current_target_before_supporting_context": True,
    }


def _review_evidence_document(
    *,
    question_context: Mapping[str, Any],
    review_material: Mapping[str, Any],
) -> dict[str, Any]:
    projected = generated_code_semantic_review_prompt_projection(review_material)
    current_target_artifacts = projected.pop("exact_executed_artifacts", [])
    upstream_dependency = projected.pop("upstream_generated_dependency", {})
    source_refresh_required = bool(_active_prior_findings(review_material))
    if source_refresh_required:
        for artifact in current_target_artifacts:
            if isinstance(artifact, dict) and artifact.pop("exact_source_code", None):
                artifact["exact_source_available_via_tool"] = (
                    GENERATED_CODE_SEMANTIC_REVIEW_READ_SOURCE_TOOL
                )
    return {
        "question": deepcopy(dict(question_context)),
        "reviewer_scope_contract": _reviewer_scope_contract(review_material),
        "supporting_review_context": projected,
        "upstream_generated_dependency": upstream_dependency,
        "current_target_role": {
            **_current_target_role(review_material),
            "fresh_source_observation_required": source_refresh_required,
        },
        "current_target_artifacts": current_target_artifacts,
    }


def _prior_finding_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "rationale"],
        "properties": {
            "status": {"type": "string", "enum": list(
                GENERATED_CODE_SEMANTIC_REVIEW_PRIOR_FINDING_STATUSES)},
            "rationale": {"type": "string", "minLength": 1},
        },
    }


def _finding_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "severity",
            "category",
            "summary",
            "observed_behavior",
            "expected_behavior",
        ],
        "properties": {
            "severity": {
                "type": "string",
                "enum": list(GENERATED_CODE_SEMANTIC_REVIEW_FINDING_SEVERITIES),
            },
            "category": {"type": "string", "minLength": 1},
            "summary": {"type": "string", "minLength": 1},
            "observed_behavior": {"type": "string", "minLength": 1},
            "expected_behavior": {"type": "string", "minLength": 1},
        },
    }


def _source_revision_assessment_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["resolution_scope", "rationale"],
        "properties": {
            "resolution_scope": {"type": "string", "enum": list(
                SOURCE_REVISION_SCOPES)},
            "rationale": {"type": "string", "minLength": 1},
        },
    }


GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "prior_finding_reviews",
        "overall_verdict",
        "review_document",
        "findings",
        "source_revision_assessment",
    ],
    "properties": {
        "prior_finding_reviews": {
            "type": "array",
            "items": _prior_finding_schema(),
        },
        "overall_verdict": {
            "type": "string",
            "enum": ["ACCEPT", "REVISE"],
        },
        "review_document": {"type": "string", "minLength": 1},
        "findings": {
            "type": "array",
            "items": _finding_schema(),
        },
        "source_revision_assessment": _source_revision_assessment_schema(),
    },
}


def generated_code_semantic_review_json_schema(
    review_material: Mapping[str, Any],
    *,
    question: OpenResearchQuestion | None = None,
) -> dict[str, Any]:
    schema = deepcopy(GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA)
    prior_ids = [
        str(row.get("finding_id", "") or "")
        for row in _active_prior_findings(review_material)
        if str(row.get("finding_id", "") or "").strip()
    ]
    prior_schema = schema["properties"]["prior_finding_reviews"]
    prior_schema["minItems"] = len(prior_ids)
    prior_schema["maxItems"] = len(prior_ids)
    return schema


def build_generated_code_semantic_review_prompt(
    *,
    question: OpenResearchQuestion,
    review_material: Mapping[str, Any],
    review_evidence_document: Mapping[str, Any] | None = None,
    evidence_document_catalog: Sequence[Mapping[str, Any]] = (),
) -> str:
    evidence_document = (
        deepcopy(dict(review_evidence_document))
        if review_evidence_document is not None
        else _review_evidence_document(
            question_context=_question_context(question),
            review_material=review_material,
        )
    )
    payload = {
        **evidence_document,
        "exact_evidence_document_catalog": [
            dict(row) for row in evidence_document_catalog
        ],
        "prior_finding_ids": [
            str(row.get("finding_id", "") or "")
            for row in _active_prior_findings(review_material)
        ],
    }
    executable_evaluator_authoring = bool(
        str(review_material.get("empirical_evaluation_phase", "") or "")
        == "executable_evaluator_authoring"
    )
    review_scope_instruction = (
        "This is preconfirmatory evaluator authoring: exact source owns the DGP, measurements, "
        "decision rule, and independently fixed requested_runtime_replicates. Trace acceptance "
        "through every load-bearing check. actual_runtime_arguments.replicates is diagnostic capacity, not a future commitment or minimum; "
        "review the returned request separately, never reject a small diagnostic; diagnostic outcomes cannot establish acceptance, and ACCEPT authorizes only unchanged-source hidden-cohort execution.\n\n"
        if executable_evaluator_authoring
        else "Realized outcomes, thresholds, Monte Carlo precision, power, and efficiency remain "
        "withheld evaluator evidence and cannot alone create a source finding.\n\n"
    )
    return (
        "Act as an independent senior scientific-code reviewer. Inspect exact executed source "
        "against the question, authoritative theory, public interface, runtime arguments, and "
        "frozen meanings. question.estimator_execution_contract outranks Theory summaries. "
        "Choose load-bearing checks yourself rather than a fixed dimension checklist, and try "
        "to falsify public acceptance, rejection, and boundary behavior. "
        + (
            "Use the supplied exact-evidence read/search tools for every externalized "
            "document before submission. Choose queries, ranges, and investigation order "
            "yourself; a document hash or successful read is not semantic authority. "
            if evidence_document_catalog
            else ""
        )
        + review_scope_instruction
        + "Return compact JSON and put analysis with source lines in review_document Markdown. "
        "ACCEPT only a semantically fit artifact. The public contract is closed in both directions; "
        "do not invent conditions. Unless that contract explicitly delegates a clause, the reviewed "
        "source owns every public ABI requirement, including valid-input behavior and rejection of "
        "invalid requests; never assume an external runtime will supply missing validation. Findings "
        "are unique active blockers with observed and expected "
        "behavior; nonblockers stay in Markdown. Review each prior finding once. The complete "
        "public contract is already bound into the review input; do not copy runtime-owned IDs "
        "into the verdict. Follow artifact_authority_rule. source_revision_assessment "
        "asks only whether current-source rewrite can close findings without changing immutable "
        "parents. It is not a repair plan or route: write no code, owner, or tactic. Supporting "
        "context is historical; current_target_artifacts is authoritative. This review is neither "
        "statistical acceptance nor proof evidence.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


GENERATED_CODE_SEMANTIC_REVIEW_SYSTEM_PROMPT = (
    "You are an independent semantic reviewer inside an AI Statistician runtime. "
    "Judge what executed generated code actually measures and implements. Ground every "
    "structured finding in supplied artifacts; findings are active downstream blockers. "
    "Assess source sufficiency without choosing "
    "a repair owner or writing replacement code. Never claim statistical acceptance or proof."
)


@dataclass(frozen=True)
class GeneratedCodeSemanticReviewerConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 5000
    temperature: float = 0.0
    provider_name: str = "anthropic"
    client_tool_max_turns: int = 64
    client_tool_max_tool_calls: int = 64
    client_tool_max_no_progress_turns: int = 2


class LLMGeneratedCodeSemanticReviewerAgent:
    """Independent observation-only reviewer for executed generated code."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: GeneratedCodeSemanticReviewerConfig = GeneratedCodeSemanticReviewerConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def review(
        self,
        *,
        question: OpenResearchQuestion,
        review_material: Mapping[str, Any],
        trusted_lineage: Mapping[str, Any],
        probe_sandbox_dir: Path | None = None,
        probe_timeout_s: int = 60,
        research_sources: ResearchSourceSnapshot | None = None,
    ) -> dict[str, Any]:
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        evidence_document = _review_evidence_document(
            question_context=_question_context(question),
            review_material=review_material,
        )
        compact_evidence_document, evidence_documents, evidence_catalog = (
            externalize_client_tool_text_documents(
                evidence_document,
                min_characters=GENERATED_CODE_REVIEW_EXTERNALIZE_MIN_CHARACTERS,
                path_prefix="generated_code_review_evidence",
            )
        )
        prompt = build_generated_code_semantic_review_prompt(
            question=question,
            review_material=review_material,
            review_evidence_document=compact_evidence_document,
            evidence_document_catalog=evidence_catalog,
        )
        provider_name = str(
            getattr(self.provider, "provider_name", self.config.provider_name)
            or self.config.provider_name
        ).lower()

        if not callable(getattr(self.provider, "generate_client_tool_turn", None)):
            raise ValueError(
                "generated-code semantic review requires native client-tool turns; "
                "one-shot full-packet generation is not a canonical fallback"
            )
        return self._review_with_client_tool_submission(
            question=question,
            review_material=review_material,
            trusted_lineage=trusted_lineage,
            prompt=prompt,
            request_model=request_model,
            provider_name=provider_name,
            probe_sandbox_dir=probe_sandbox_dir,
            probe_timeout_s=probe_timeout_s,
            research_sources=research_sources,
            evidence_documents=evidence_documents,
            evidence_catalog=evidence_catalog,
        )

    def _review_with_client_tool_submission(
        self,
        *,
        question: OpenResearchQuestion,
        review_material: Mapping[str, Any],
        trusted_lineage: Mapping[str, Any],
        prompt: str,
        request_model: str,
        provider_name: str,
        probe_sandbox_dir: Path | None,
        probe_timeout_s: int,
        research_sources: ResearchSourceSnapshot | None,
        evidence_documents: Mapping[str, str],
        evidence_catalog: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Keep executable falsification and verdict in one reviewer session."""

        submission_schema = generated_code_semantic_review_json_schema(
            review_material, question=question
        )
        submission_schema.pop("$schema", None)
        probe_targets = (
            _exact_estimator_probe_targets(review_material)
            if probe_sandbox_dir is not None
            else {}
        )
        contract = question.estimator_execution_contract
        contract_probe_target = (
            str(contract.get("estimator_id", "") or "").strip()
            if isinstance(contract, Mapping)
            else ""
        )
        contract_probe_relevant = bool(
            contract_probe_target in probe_targets
            and frozen_estimator_execution_contract_clause_ids(contract)
            - frozen_estimator_execution_contract_empirical_claim_ids(contract)
        )
        refresh_targets: dict[str, dict[str, Any]] = {}
        if _active_prior_findings(review_material):
            for row in review_material.get("exact_executed_artifacts", []) or []:
                if not isinstance(row, Mapping):
                    continue
                artifact_id = str(row.get("artifact_id", "") or "").strip()
                source = str(row.get("exact_source_code", "") or "")
                source_row = row.get("source_row", {})
                language = normalized_generated_code_language(
                    source_row.get("language")
                    if isinstance(source_row, Mapping)
                    else ""
                )
                if not artifact_id or not source:
                    continue
                try:
                    project_files = normalized_scientific_project_files(
                        row.get("exact_project_files", []),
                        language=language,
                    )
                except ValueError:
                    continue
                files = {
                    scientific_main_path(language): source,
                    **{
                        project_file.path: project_file.content
                        for project_file in project_files
                    },
                }
                refresh_targets[artifact_id] = {
                    "language": language,
                    "files": files,
                    "project_hash": scientific_project_hash(
                        language=language,
                        code=source,
                        project_files=project_files,
                    ),
                }
        document_tools = (
            theory_document_client_tools() if evidence_documents else ()
        )
        required_evidence_document_paths = set(evidence_documents)
        source_tools = research_source_client_tools() if research_sources else ()
        source_descriptor = (
            research_sources.descriptor() if research_sources else {"configured": False}
        )
        source_guidance = (
            "\n\nYou may list directories, search, and read the frozen public "
            "research-source snapshot when paper, code, or documentation text would "
            "improve your judgment. Navigate an unfamiliar project before guessing "
            "paths. Choose queries and passages yourself; retrieved text is evidence, "
            "not proof or automatic acceptance."
            if source_tools else ""
        )
        refresh_tool = ClientToolDefinition(
            name=GENERATED_CODE_SEMANTIC_REVIEW_READ_SOURCE_TOOL,
            description=(
                "Read one exact file from the immutable current target project after a "
                "producer revision. Omit path for the main source. The returned manifest "
                "lists every available file."
            ),
            input_schema={
                "type": "object", "additionalProperties": False,
                "required": ["artifact_id"],
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "enum": list(refresh_targets),
                    },
                    "path": {"type": "string", "minLength": 1},
                },
            },
        )
        probe_schema: dict[str, Any] = {
            "type": "object", "additionalProperties": False,
            "required": ["artifact_id", "dependencies", "code", "seed", "replicates"],
            "properties": {
                "artifact_id": {"type": "string", "enum": list(probe_targets)},
                "dependencies": {"type": "array", "items": {"type": "string"},
                                 "uniqueItems": True},
                "code": {"type": "string", "minLength": 1},
                "seed": {"type": "integer"},
                "replicates": {"type": "integer", "minimum": 1},
            },
        }
        probe_tool = ClientToolDefinition(
            name=GENERATED_CODE_SEMANTIC_REVIEW_PROBE_TOOL,
            description=(
                "Run reviewer-authored Python or R diagnostic source against one exact "
                "immutable estimator. Define run_sandbox(seed, replicates, estimators) "
                "exactly; for Python the declaration begins "
                "`def run_sandbox(seed, replicates, estimators):`. Then call the "
                "target run_estimator directly with "
                "estimators[artifact_id](request) in Python or "
                "estimators[[artifact_id]](request) in R, never a run_estimator "
                "attribute. This executes the reviewer's run_sandbox, not the "
                "target's. Failure before target invocation is a reviewer tool error. "
                "Only an observation that reaches the target can falsify source claims; "
                "Correct it and reach the target before submitting. Request and response values "
                "remain native to that language until your final probe metrics are serialized. "
                "The probe cannot edit source, inspect confirmatory outcomes, or confer "
                "empirical acceptance. The reviewer owns test selection, contract "
                "decomposition, and scientific interpretation; runtime records only exact "
                "source execution and immutable lineage."
            ),
            input_schema=probe_schema,
        )
        tools = document_tools + source_tools + ((refresh_tool,) if refresh_targets else ()) + (
            (probe_tool,) if probe_targets else ()
        ) + (
            ClientToolDefinition(
                name=GENERATED_CODE_SEMANTIC_REVIEW_SUBMIT_TOOL,
                description=(
                    "Submit the complete independent scientific-code judgment. "
                    "Runtime validates evidence pointers and immutable lineage; "
                    "a rejected submission returns exact validation observations "
                    "to this same reviewer session."
                ),
                input_schema=submission_schema,
                terminal=True,
                strict=False,
            ),
        )
        request = ClientToolTurnRequest(
            system_prompt=GENERATED_CODE_SEMANTIC_REVIEW_SYSTEM_PROMPT,
            messages=(
                {
                    "role": "user",
                    "content": (
                        prompt
                        + source_guidance
                        + "\n\nWhen your independent review is complete, call "
                        + GENERATED_CODE_SEMANTIC_REVIEW_SUBMIT_TOOL
                        + ". If runtime rejects the submission, read the returned "
                        "validation observation and submit a corrected complete "
                        "judgment in this same reviewer session."
                        + (
                            " Before submitting, call "
                            + GENERATED_CODE_SEMANTIC_REVIEW_READ_SOURCE_TOOL
                            + " once for every current artifact. Judge prior findings only "
                            "against that fresh hash-bound source observation."
                            if refresh_targets else ""
                        )
                        + (
                            " You may first call "
                            + GENERATED_CODE_SEMANTIC_REVIEW_PROBE_TOOL
                            + " for a model-authored multi-case Python or R test. Choose cases and "
                            "interpretation yourself. Failure before target invocation is your tool "
                            "error, not a finding; correct it and reach the target before submitting. Native "
                            "request and response types reach the exact candidate unchanged. Numerical or "
                            "self-consistency checks do not cover "
                            "omitted boundaries or establish semantics; derive a discriminating oracle "
                            "when needed. Successful probes are committed: cite result_hash in review_document, "
                            "reconcile metrics with the verdict, and never ignore a contradiction."
                            if probe_targets
                            else ""
                        )
                        + (
                            " Decide whether an executable probe would materially improve your "
                            "contract judgment. If you use one, choose cases that discriminate the "
                            "exact public obligations, including malformed, boundary, or "
                            "transformation behavior when relevant. Do not infer an untested "
                            "obligation from a neighboring passing example."
                            if contract_probe_relevant else ""
                        )
                        + " Prose alone cannot submit or accept a review."
                    ),
                },
            ),
            tools=tools,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            tool_choice=(
                "any" if (
                    document_tools or source_tools or probe_targets or refresh_targets
                )
                else GENERATED_CODE_SEMANTIC_REVIEW_SUBMIT_TOOL
            ),
            disable_parallel_tool_use=False,
            enable_prompt_caching=True,
            metadata={
                "subsystem": "GeneratedCodeSemanticReviewer",
                "agent": "LLMGeneratedCodeSemanticReviewerAgent",
                "model_tier": self.config.model_tier,
                "review_input_fingerprint": stable_hash(review_material),
                "observation_only_reviewer": True,
                "review_transport": GENERATED_CODE_SEMANTIC_REVIEW_TRANSPORT,
                "client_tool_transport": True,
                "same_session_validation_feedback": True,
                "exact_estimator_probe_available": bool(probe_targets),
                "fresh_current_source_observation_required": bool(refresh_targets),
                "evidence_document_count": len(evidence_documents),
                "evidence_document_catalog_hash": stable_hash(evidence_catalog),
                "full_packet_regeneration_disabled": True,
            },
        )
        validation_history: list[dict[str, Any]] = []
        probe_executions: list[dict[str, Any]] = []
        research_source_refs: list[dict[str, Any]] = []
        evidence_document_accesses: list[dict[str, Any]] = []
        accessed_evidence_document_paths: set[str] = set()
        refreshed_source_ids: set[str] = set()
        last_errors: list[str] = []
        last_invalid_packet: dict[str, Any] | None = None

        def normalize_submission(
            payload: Mapping[str, Any],
            *,
            model: str,
            response_provider: str,
        ) -> dict[str, Any]:
            return _normalize_generated_code_semantic_review_packet(
                payload,
                question=question,
                trusted_lineage=trusted_lineage,
                review_material=review_material,
                model=model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response_provider,
                raw_response=json.dumps(payload, sort_keys=True, default=str),
            )

        def execute_tool(
            call: ClientToolCall,
            context: ClientToolExecutionContext,
        ) -> ClientToolExecutionResult:
            nonlocal last_errors, last_invalid_packet
            if call.name == THEORY_WORKSPACE_READ_DOCUMENT_TOOL:
                if set(call.input) != {"path", "line_start", "line_end"}:
                    raise ClientToolInputError(
                        "generated-code evidence read requires path, line_start, and line_end"
                    )
                observation, inspection = read_theory_document_lines(
                    evidence_documents,
                    path=call.input["path"],
                    line_start=call.input["line_start"],
                    line_end=call.input["line_end"],
                )
                evidence_document_accesses.append(inspection)
                accessed_evidence_document_paths.add(str(inspection["path"]))
                return ClientToolExecutionResult(
                    content=observation,
                    observation_key=(
                        "generated-code-evidence-read:" + stable_hash(inspection)
                    ),
                )
            if call.name == THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL:
                if not set(call.input) <= {
                    "query",
                    "document_paths",
                    "max_results",
                }:
                    raise ClientToolInputError(
                        "generated-code evidence search accepts query, document_paths, and max_results"
                    )
                observation, inspection = search_theory_document_lines(
                    evidence_documents,
                    query=call.input.get("query"),
                    document_paths=call.input.get("document_paths", ()),
                    max_results=call.input.get("max_results", 20),
                )
                evidence_document_accesses.append(inspection)
                accessed_evidence_document_paths.update(
                    str(path)
                    for path in inspection.get("document_hashes", {})
                )
                return ClientToolExecutionResult(
                    content=observation,
                    observation_key=(
                        "generated-code-evidence-search:" + stable_hash(inspection)
                    ),
                )
            if call.name in {
                RESEARCH_SOURCE_LIST_TOOL,
                RESEARCH_SOURCE_SEARCH_TOOL,
                RESEARCH_SOURCE_READ_TOOL,
            }:
                assert research_sources is not None
                try:
                    observation, source_ref = execute_research_source_client_tool(
                        research_sources,
                        tool_name=call.name,
                        tool_input=dict(call.input),
                    )
                except ValueError as exc:
                    raise ClientToolInputError(str(exc)) from exc
                research_source_refs.append(source_ref)
                return ClientToolExecutionResult(
                    content=observation,
                    observation_key=call.name + ":" + stable_hash(source_ref),
                )
            if call.name == GENERATED_CODE_SEMANTIC_REVIEW_READ_SOURCE_TOOL:
                artifact_id = str(call.input.get("artifact_id", "") or "")
                target = refresh_targets.get(artifact_id, {})
                if not target:
                    raise ClientToolInputError("unknown current generated source artifact")
                files = target["files"]
                main_path = scientific_main_path(str(target["language"]))
                path = str(call.input.get("path", "") or main_path).strip()
                source = files.get(path, "")
                if not source:
                    raise ClientToolInputError(
                        "unknown current generated project file: " + path
                    )
                refreshed_source_ids.add(artifact_id)
                source_lines = source.splitlines()
                observation = {
                    "artifact_kind": "CurrentGeneratedSourceObservation",
                    "artifact_id": artifact_id,
                    "path": path,
                    "exact_source_hash": stable_hash(source),
                    "exact_project_hash": target["project_hash"],
                    "file_manifest": [
                        {
                            "path": file_path,
                            "content_hash": stable_hash(content),
                            "line_count": len(content.splitlines()),
                        }
                        for file_path, content in sorted(files.items())
                    ],
                    "line_count": len(source_lines),
                    "source_with_line_numbers": "\n".join(
                        f"{index:6d}  {line}"
                        for index, line in enumerate(source_lines, start=1)
                    ),
                    "authority": "CURRENT_IMMUTABLE_TARGET_SOURCE",
                }
                return ClientToolExecutionResult(
                    content=observation,
                    observation_key="current-generated-source:" + stable_hash(observation),
                )
            if call.name == GENERATED_CODE_SEMANTIC_REVIEW_PROBE_TOOL:
                probe_input = dict(call.input)
                required = {"artifact_id", "dependencies", "code", "seed", "replicates"}
                if set(probe_input) != required:
                    raise ClientToolInputError(
                        "review probe fields do not match the advertised exact schema"
                    )
                if not isinstance(probe_input["dependencies"], list) or not str(
                    probe_input["code"] or ""
                ).strip():
                    raise ClientToolInputError(
                        "review probe dependencies must be an array and code must be nonempty"
                    )
                if type(probe_input["seed"]) is not int or not (
                    type(probe_input["replicates"]) is int
                    and probe_input["replicates"] > 0
                ):
                    raise ClientToolInputError(
                        "review probe seed must be an integer and replicates positive"
                    )
                target = probe_targets.get(str(probe_input["artifact_id"] or ""))
                if not target or probe_sandbox_dir is None:
                    raise ClientToolInputError("unknown exact estimator probe target")
                probe_code = str(probe_input["code"] or "")
                execution = execute_scientific_sandbox(
                    sandbox_dir=(
                        probe_sandbox_dir / f"probe-{context.total_calls_before}"
                    ),
                    artifact_id="semantic-review-probe:"
                    + stable_hash(probe_input)[:20],
                    language=target["language"],
                    code=probe_code,
                    dependencies=probe_input["dependencies"],
                    seed=probe_input["seed"],
                    replicates=probe_input["replicates"],
                    timeout_s=max(1, int(probe_timeout_s)),
                    estimator_bindings=(ScientificEstimatorBinding(**target),),
                    estimator_transport="native",
                )
                estimator_binding_errors = list(getattr(
                    execution, "estimator_binding_errors", ()
                ) or ())
                estimator_runtime_failure_ids = list(getattr(
                    execution, "estimator_runtime_failure_ids", ()
                ) or ())
                estimator_runtime_errors = list(execution.estimator_runtime_errors)
                estimator_invocation_counts = dict(execution.estimator_invocation_counts)
                target_invoked = any(estimator_invocation_counts.values())
                target_failed = bool(
                    estimator_binding_errors
                    or estimator_runtime_failure_ids
                    or estimator_runtime_errors
                )
                if estimator_binding_errors:
                    failure_origin = "TARGET_ESTIMATOR_BINDING"
                elif estimator_runtime_failure_ids or estimator_runtime_errors:
                    failure_origin = "TARGET_ESTIMATOR_RUNTIME"
                elif execution.status == "EXECUTED" and target_invoked:
                    failure_origin = "PROBE_COMPLETED"
                elif target_invoked:
                    failure_origin = "REVIEWER_PROBE_SOURCE_AFTER_TARGET_INVOCATION"
                else:
                    failure_origin = "REVIEWER_PROBE_SOURCE_BEFORE_TARGET_INVOCATION"
                record = {
                    "probe_index": len(probe_executions),
                    "originating_tool_call_id": call.call_id,
                    "target_artifact_id": target["artifact_id"],
                    "target_source_hash": target["code_hash"],
                    "probe_source_hash": stable_hash(probe_code),
                    "failure_origin": failure_origin,
                    "target_source_invoked": target_invoked,
                    "failed_probe_is_target_source_evidence": target_failed,
                    "status": execution.status,
                    "metrics": _prompt_projection_value(execution.metrics),
                    "metrics_hash": stable_hash(execution.metrics),
                    "errors": list(execution.errors),
                    "stdout_summary": execution.stdout_summary,
                    "stderr_summary": execution.stderr_summary,
                    "estimator_invocation_counts": estimator_invocation_counts,
                    "target_request_boundary": {
                        "transport": "SAME_LANGUAGE_NATIVE_CALL",
                        "host_types_preserved_before_candidate": True,
                        "observed_samples": _prompt_projection_value(getattr(execution, "estimator_invocation_samples", {}) or {}),
                    },
                    "estimator_runtime_errors": estimator_runtime_errors,
                    "successful_exact_invocation": (
                        execution.status == "EXECUTED" and target_invoked
                    ),
                    "request_hash": execution.request_hash,
                    "result_hash": execution.result_hash,
                    "code_path": execution.code_path,
                    "result_path": execution.result_path,
                    "authority": "REVIEWER_DIAGNOSTIC_NOT_EMPIRICAL_ACCEPTANCE_OR_PROOF",
                }
                probe_executions.append(record)
                observation = dict(record)
                if (
                    isinstance(contract, Mapping)
                    and target["artifact_id"] == contract_probe_target
                ):
                    observation["authoritative_estimator_execution_contract"] = deepcopy(dict(contract))
                    observation["review_instruction"] = (
                        "Reconcile this raw probe result and the exact source against every "
                        "public contract obligation. The exact candidate receives native request "
                        "values; probe again or report any gap that remains there."
                    )
                return ClientToolExecutionResult(
                    content=observation,
                    is_error=failure_origin.startswith("REVIEWER_PROBE_SOURCE_"),
                    observation_key="generated-code-review-probe:" + stable_hash(record),
                )
            if call.name != GENERATED_CODE_SEMANTIC_REVIEW_SUBMIT_TOOL:
                raise ClientToolInputError(
                    "unsupported generated-code semantic review tool"
                )
            if context.calls_in_turn != 1:
                raise ClientToolInputError(
                    "generated-code terminal submission must be the only call in its turn"
                )
            missing_document_paths = sorted(
                required_evidence_document_paths
                - accessed_evidence_document_paths
            )
            if missing_document_paths:
                raise ClientToolInputError(
                    "exact externalized evidence must be inspected before submission: "
                    + ", ".join(missing_document_paths)
                )
            missing_source_ids = sorted(set(refresh_targets) - refreshed_source_ids)
            if missing_source_ids:
                raise ClientToolInputError(
                    "fresh current source observation required before submission: "
                    + ", ".join(missing_source_ids)
                )
            payload = dict(call.input)
            packet = normalize_submission(
                payload,
                model=request_model,
                response_provider=provider_name,
            )
            errors = validate_generated_code_semantic_review_packet(
                packet, review_material=review_material
            )
            reviewed_text = str(payload.get("review_document", "") or "")
            for row in probe_executions:
                result_hash = str(row.get("result_hash", "") or "")
                if row.get("successful_exact_invocation") is True and result_hash not in reviewed_text:
                    errors.append("review_document must reconcile successful probe result_hash " + result_hash)
            validation_history.append(
                {
                    "attempt_index": len(validation_history),
                    "ok": not errors,
                    "errors": list(errors),
                    "submission_fingerprint": stable_hash(payload),
                }
            )
            if errors:
                last_errors = list(errors)
                last_invalid_packet = deepcopy(packet)
                rejection = {
                    "ok": False,
                    "error": "generated_code_semantic_review_submission_rejected",
                    "validation_errors": list(errors),
                    "instruction": (
                        "Re-submit the complete judgment using every validation "
                        "observation; immutable reviewed artifacts cannot change."
                    ),
                }
                return ClientToolExecutionResult(
                    content=rejection,
                    is_error=True,
                    observation_key=(
                        "generated-code-semantic-review-rejected:"
                        + stable_hash(rejection)
                    ),
                )
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "submitted": True,
                    "overall_verdict": packet.get("overall_verdict", ""),
                    "packet_fingerprint": stable_hash(packet),
                    "proof_evidence_status": GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE,
                },
                terminal=True,
                terminal_payload={"review_payload": payload},
                observation_key=(
                    "generated-code-semantic-review-submitted:"
                    + stable_hash(packet)
                ),
            )

        try:
            loop = run_bounded_client_tool_loop(
                backend=self.provider,
                request=request,
                execute_tool=execute_tool,
                max_turns=max(1, int(self.config.client_tool_max_turns)),
                max_tool_calls=max(
                    1, int(self.config.client_tool_max_tool_calls)
                ),
                max_no_progress_turns=max(
                    1, int(self.config.client_tool_max_no_progress_turns)
                ),
            )
        except ClientToolLoopError as exc:
            errors = last_errors or [exc.reason]
            raise PacketValidationError(
                validation_label="generated-code semantic review packet",
                attempts=exc.turns,
                errors=list(errors),
                history=list(exc.history),
                last_invalid_packet=last_invalid_packet,
            ) from exc
        payload = loop.terminal_payload.get("review_payload", {})
        if not isinstance(payload, Mapping):
            raise PacketValidationError(
                validation_label="generated-code semantic review packet",
                attempts=len(validation_history),
                errors=["accepted client-tool submission payload is malformed"],
                history=list(validation_history),
            )
        packet = normalize_submission(
            payload, model=loop.model, response_provider=loop.provider
        )
        packet["validation_errors"] = []
        packet["ok"] = True
        packet["client_tool_loop"] = {
            "transport": "native_same_reviewer_session_v1",
            "turns": loop.turns,
            "tool_calls": loop.tool_calls,
            "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
            "transcript_fingerprint": loop.transcript_fingerprint,
            "provider_usage": dict(loop.provider_usage),
            "validation_submissions": len(validation_history),
            "validation_feedback_observed": any(
                not row.get("ok") for row in validation_history
            ),
            "review_probe_executions": probe_executions,
            "review_probe_execution_fingerprint": stable_hash(probe_executions),
            "research_source_snapshot": source_descriptor,
            "research_source_refs": research_source_refs,
            "research_source_ref_fingerprint": stable_hash(research_source_refs),
            "evidence_document_count": len(evidence_documents),
            "evidence_document_catalog_hash": stable_hash(evidence_catalog),
            "evidence_document_access_count": len(evidence_document_accesses),
            "evidence_document_access_fingerprint": stable_hash(
                evidence_document_accesses
            ),
            "fresh_current_source_observation_required": bool(refresh_targets),
            "refreshed_current_source_artifact_ids": sorted(refreshed_source_ids),
            "full_packet_regeneration_used": False,
        }
        return packet


def _normalize_prior_reviews(
    value: Any,
    *,
    review_material: Mapping[str, Any],
) -> list[dict[str, Any]]:
    prior_ids = [
        str(row.get("finding_id", "") or "")
        for row in _active_prior_findings(review_material)
    ]
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(value if isinstance(value, list) else []):
        if not isinstance(raw, Mapping):
            continue
        finding_id = prior_ids[index] if index < len(prior_ids) else ""
        rows.append(
            {
                "finding_id": finding_id,
                "status": str(raw.get("status", "") or "").strip().upper(),
                "rationale": str(raw.get("rationale", "") or "").strip(),
                "evidence_refs": [],
            }
        )
    return rows


def _normalize_source_revision_assessment(
    value: Any,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    resolution_scope = str(value.get("resolution_scope", "") or "").strip()
    return {
        "resolution_scope": resolution_scope,
        "rationale": str(value.get("rationale", "") or "").strip(),
        "evidence_refs": [],
    }


def _normalize_generated_code_semantic_review_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    trusted_lineage: Mapping[str, Any],
    review_material: Mapping[str, Any],
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
) -> dict[str, Any]:
    source_subsystem = str(
        trusted_lineage.get("source_subsystem", "") or ""
    ).strip()
    prior_reviews = _normalize_prior_reviews(
        payload.get("prior_finding_reviews", []),
        review_material=review_material,
    )
    findings = normalize_generated_code_semantic_review_findings(
        question_id=question.id,
        source_subsystem=source_subsystem,
        findings=payload.get("findings"),
        preserve_existing_ids=False,
    )
    source_revision_assessment = _normalize_source_revision_assessment(
        payload.get("source_revision_assessment", {})
    )
    requested_verdict = str(
        payload.get("overall_verdict", "") or ""
    ).strip().upper()
    verdict = requested_verdict
    review_input_fingerprint = stable_hash(review_material)
    review_document_content = str(
        payload.get("review_document", "") or ""
    ).strip()
    document_sha256 = hashlib.sha256(review_document_content.encode("utf-8")).hexdigest()
    review_document = {
        "schema_version": 1,
        "artifact_kind": "GeneratedCodeSemanticReviewDocument",
        "document_id": "generated_code_semantic_review_document:"
        + stable_hash([question.id, review_input_fingerprint, document_sha256])[:20],
        "question_id": question.id,
        "review_input_fingerprint": review_input_fingerprint,
        "format": "markdown",
        "content": review_document_content,
        "sha256": document_sha256,
        "line_count": len(review_document_content.splitlines()),
        "byte_size": len(review_document_content.encode("utf-8")),
        "proof_evidence_status": GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE,
        "evidence_boundary": GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
    }
    review_event_id = "generated_code_semantic_review_event:" + stable_hash(
        {
            "question_id": question.id,
            "source_manifest_id": trusted_lineage.get("source_manifest_id", ""),
            "review_input_fingerprint": stable_hash(review_material),
            "prior_finding_reviews": prior_reviews,
            "findings": findings,
        }
    )[:20]
    ledger = update_metric_protocol_finding_ledger(
        question_id=question.id,
        prior_ledger=_active_prior_findings(review_material),
        prior_finding_reviews=prior_reviews,
        current_findings=findings,
        current_verdict=verdict,
        review_packet_id=review_event_id,
        revision_index=0,
    )
    question_context = _question_context(question)
    evidence_document = _review_evidence_document(
        question_context=question_context,
        review_material=review_material,
    )
    body: dict[str, Any] = {
        "question_id": question.id,
        "question_context": question_context,
        "source_subsystem": source_subsystem,
        "prior_finding_reviews": prior_reviews,
        "findings": findings,
        "source_revision_assessment": source_revision_assessment,
        "model_requested_overall_verdict": requested_verdict,
        "overall_verdict": verdict,
        "review_document_ref": {
            "document_id": review_document["document_id"],
            "sha256": review_document["sha256"],
            "line_count": review_document["line_count"],
            "byte_size": review_document["byte_size"],
            "format": "markdown",
        },
        "finding_ledger_review_event_id": review_event_id,
        "cumulative_finding_ledger": ledger,
        "cumulative_finding_ledger_fingerprint": (
            metric_protocol_finding_ledger_fingerprint(ledger)
        ),
        "active_unresolved_finding_ids": [
            str(row.get("finding_id", "") or "")
            for row in active_metric_protocol_finding_ledger(ledger)
            if str(row.get("finding_id", "") or "").strip()
        ],
        "review_input_fingerprint": review_input_fingerprint,
        "review_evidence_document_fingerprint": stable_hash(evidence_document),
        "reviewed_artifacts": list(trusted_lineage.get("reviewed_artifacts", []) or []),
        "source_generator_agent": str(
            trusted_lineage.get("source_agent", "") or ""
        ),
        "proof_evidence_status": GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE,
        "evidence_boundary": GENERATED_CODE_SEMANTIC_REVIEW_BOUNDARY,
        "kernel_verified": False,
    }
    for field in (
        "work_order_id",
        "work_order_hash",
        "source_task_id",
        "source_manifest_id",
        "source_manifest_hash",
        "theory_packet_id",
        "theory_packet_hash",
        "proposal_packet_id",
        "proposal_packet_hash",
        "source_model",
        "source_model_tier",
    ):
        body[field] = trusted_lineage.get(field, "")
    packet_id = "generated_code_semantic_review:" + stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "model": model,
            "model_tier": model_tier,
            "body": body,
        }
    )[:24]
    return {
        "schema_version": GENERATED_CODE_SEMANTIC_REVIEW_SCHEMA_VERSION,
        "artifact_kind": "GeneratedCodeSemanticReviewPacket",
        "packet_id": packet_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMGeneratedCodeSemanticReviewerAgent",
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
        "_review_document_artifact": review_document,
    }


def validate_generated_code_semantic_review_packet(
    packet: Mapping[str, Any],
    *,
    review_material: Mapping[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    material = review_material or {}
    raw_question_context = packet.get("question_context", {})
    question_context = (
        dict(raw_question_context)
        if isinstance(raw_question_context, Mapping)
        else {}
    )
    evidence_document = _review_evidence_document(
        question_context=question_context,
        review_material=material,
    )
    if packet.get("artifact_kind") != "GeneratedCodeSemanticReviewPacket":
        errors.append("generated-code semantic review artifact kind is invalid")
    if packet.get("source_subsystem") not in GENERATED_CODE_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS:
        errors.append("generated-code semantic review source subsystem is invalid")
    if packet.get("review_input_fingerprint") != stable_hash(material):
        errors.append("generated-code semantic review input fingerprint mismatch")
    if str(question_context.get("id", "") or "") != str(
        packet.get("question_id", "") or ""
    ):
        errors.append("generated-code semantic review question context mismatch")
    if packet.get("review_evidence_document_fingerprint") != stable_hash(
        evidence_document
    ):
        errors.append(
            "generated-code semantic review evidence document fingerprint mismatch"
        )
    findings = packet.get("findings", [])
    finding_rows = [row for row in findings if isinstance(row, Mapping)] if isinstance(findings, list) else []
    if not isinstance(findings, list) or len(finding_rows) != len(findings):
        errors.append("findings must be objects")
    for index, row in enumerate(finding_rows):
        label = f"findings[{index}]"
        if row.get("severity") not in GENERATED_CODE_SEMANTIC_REVIEW_FINDING_SEVERITIES:
            errors.append(f"{label} has invalid severity")
        for field in (
            "finding_id",
            "category",
            "summary",
            "observed_behavior",
            "expected_behavior",
        ):
            if not str(row.get(field, "") or "").strip():
                errors.append(f"{label} missing {field}")
    prior_rows = packet.get("prior_finding_reviews", [])
    normalized_prior_rows = [row for row in prior_rows if isinstance(row, Mapping)] if isinstance(prior_rows, list) else []
    expected_prior_ids = [
        str(row.get("finding_id", "") or "")
        for row in _active_prior_findings(material)
    ]
    actual_prior_ids = [str(row.get("finding_id", "") or "") for row in normalized_prior_rows]
    if actual_prior_ids != expected_prior_ids:
        errors.append("prior_finding_reviews must cover active prior findings in order")
    for index, row in enumerate(normalized_prior_rows):
        if row.get("status") not in GENERATED_CODE_SEMANTIC_REVIEW_PRIOR_FINDING_STATUSES:
            errors.append(f"prior_finding_reviews[{index}] has invalid status")
        if not str(row.get("rationale", "") or "").strip():
            errors.append(f"prior_finding_reviews[{index}] is missing rationale")
    requested_verdict = str(
        packet.get("model_requested_overall_verdict", "") or ""
    ).strip().upper()
    if requested_verdict not in {"ACCEPT", "REVISE"}:
        errors.append("semantic reviewer requires an ACCEPT or REVISE verdict")
    open_prior = any(
        row.get("status") not in GENERATED_CODE_SEMANTIC_REVIEW_CLOSED_PRIOR_FINDING_STATUSES
        for row in normalized_prior_rows
    )
    expected_verdict = "REVISE" if finding_rows or open_prior else "ACCEPT"
    if requested_verdict in {"ACCEPT", "REVISE"} and (
        requested_verdict != expected_verdict
    ):
        errors.append(
            "model verdict must agree with active findings and prior observations"
        )
    if packet.get("overall_verdict") != requested_verdict:
        errors.append("overall_verdict must preserve the model-authored verdict")
    review_document_ref = packet.get("review_document_ref", {})
    valid_document_ref = isinstance(review_document_ref, Mapping) and all(
        (
            str(review_document_ref.get("document_id", "") or "").strip(),
            len(str(review_document_ref.get("sha256", "") or "")) == 64,
            review_document_ref.get("format") == "markdown",
        )
    )
    if not valid_document_ref:
        errors.append("semantic review document ref is incomplete")
    review_document = packet.get("_review_document_artifact")
    if review_document is not None:
        if not isinstance(review_document, Mapping):
            errors.append("semantic review document artifact must be an object")
        else:
            content = str(review_document.get("content", "") or "")
            content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
            document_consistent = valid_document_ref and all(
                (
                    content.strip(),
                    review_document.get("artifact_kind")
                    == "GeneratedCodeSemanticReviewDocument",
                    review_document.get("document_id")
                    == review_document_ref.get("document_id"),
                    review_document.get("sha256") == content_sha256,
                    review_document_ref.get("sha256") == content_sha256,
                )
            )
            if not document_consistent:
                errors.append("semantic review document artifact is inconsistent")
    assessment = packet.get("source_revision_assessment", {})
    if not isinstance(assessment, Mapping):
        errors.append("source_revision_assessment must be an object")
    else:
        resolution_scope = str(
            assessment.get("resolution_scope", "") or ""
        ).strip()
        if resolution_scope not in SOURCE_REVISION_SCOPES:
            errors.append(
                "source_revision_assessment requires a valid resolution_scope"
            )
        if not str(assessment.get("rationale", "") or "").strip():
            errors.append("source_revision_assessment is missing rationale")
        if (
            requested_verdict == "ACCEPT"
            and resolution_scope != SOURCE_REVISION_SCOPE_NO_PARENT_CHANGE
        ):
            errors.append(
                "accepted review cannot assert an unresolved cross-artifact conflict"
            )
    for field in (
        "work_order_id",
        "work_order_hash",
        "source_manifest_id",
        "source_manifest_hash",
        "review_input_fingerprint",
    ):
        if not str(packet.get(field, "") or "").strip():
            errors.append(f"semantic review missing trusted lineage field: {field}")
    if packet.get("proof_evidence_status") != GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE:
        errors.append("generated-code semantic review proof boundary is invalid")
    if packet.get("kernel_verified") is not False:
        errors.append("generated-code semantic review cannot be kernel verified")
    ledger = packet.get("cumulative_finding_ledger", [])
    if packet.get("cumulative_finding_ledger_fingerprint") != metric_protocol_finding_ledger_fingerprint(
        ledger if isinstance(ledger, list) else []
    ):
        errors.append("semantic finding ledger fingerprint mismatch")
    return sorted(set(errors))

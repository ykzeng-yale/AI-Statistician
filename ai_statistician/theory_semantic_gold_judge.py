from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY,
    GeneratorBackend,
    GeneratorRequest,
)
from .structured_output_retry import extract_json_object


THEORY_SEMANTIC_GOLD_JUDGE_BOUNDARY = (
    "This calibrated semantic judgment runs only under evaluator authority after "
    "AgentRuntime termination. It cannot revise the candidate, route a runtime "
    "task, enter model RAG, or become theorem proof evidence."
)
THEORY_SEMANTIC_CLAIM_STATUSES = frozenset(
    {"SATISFIED", "VIOLATED", "INCONCLUSIVE"}
)
THEORY_SEMANTIC_DOCUMENT_STATUSES = frozenset(
    {"PASS", "FAIL", "INCONCLUSIVE"}
)


THEORY_SEMANTIC_GOLD_JUDGE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["assessments"],
    "properties": {
        "assessments": {
            "type": "array",
            "items": {"$ref": "#/$defs/document_assessment"},
        },
    },
    "$defs": {
        "claim_assessment": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "claim_id",
                "status",
            ],
            "properties": {
                "claim_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": sorted(THEORY_SEMANTIC_CLAIM_STATUSES),
                },
            },
        },
        "document_assessment": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "case_id",
                "status",
                "claim_assessments",
            ],
            "properties": {
                "case_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": sorted(THEORY_SEMANTIC_DOCUMENT_STATUSES),
                },
                "claim_assessments": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/claim_assessment"},
                },
            },
        },
    },
}


def run_theory_semantic_gold_judge(
    *,
    provider: GeneratorBackend,
    task_id: str,
    visible_question: Mapping[str, Any],
    candidate_documents: Sequence[Mapping[str, Any]],
    reference_documents: Sequence[Mapping[str, Any]],
    rubric: Mapping[str, Any],
    calibration_cases: Sequence[Mapping[str, Any]],
    model: str = LIVE_EVALUATION_CLAUDE_MODEL,
    model_tier: str = LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    max_tokens: int = 6000,
) -> dict[str, Any]:
    """Judge one frozen theory artifact only after hidden-case calibration."""

    claim_ids = _rubric_claim_ids(rubric)
    case_ids = _calibration_case_ids(calibration_cases)
    prompt_cases = [
        {
            "case_id": str(row["case_id"]),
            "documents": deepcopy(list(row.get("documents", []) or [])),
        }
        for row in calibration_cases
    ]
    payload = {
        "task": {
            "id": task_id,
            "visible_question": deepcopy(dict(visible_question)),
        },
        "reference_documents": deepcopy(list(reference_documents)),
        "claim_rubric": deepcopy(dict(rubric)),
        "unlabeled_calibration_cases": prompt_cases,
        "candidate": {
            "case_id": "candidate",
            "documents": deepcopy(list(candidate_documents)),
        },
        "required_document_case_ids": [*case_ids, "candidate"],
        "required_claim_ids": claim_ids,
        "boundary": THEORY_SEMANTIC_GOLD_JUDGE_BOUNDARY,
    }
    request = GeneratorRequest(
        system_prompt=(
            "You are an independent mathematical-statistics adjudicator. Compare "
            "each document set with the reference and claim rubric at the level of "
            "mathematical meaning. Accept equivalent notation and algebra. Reject "
            "contradictory assumptions, false equations, unjustified limits, or "
            "evidence-authority violations. Do not grade wording, formatting, or "
            "keyword overlap. Reconstruct decisive equations or counterexamples "
            "when needed. Calibration cases are deliberately unlabeled. Think through "
            "the comparison, but keep the returned object minimal: output only case "
            "IDs, overall statuses, claim IDs, and claim statuses, with no rationale, "
            "evidence text, or commentary. Return exactly one assessment for every "
            "required calibration case ID and every required claim ID, without "
            "omission or duplication. Do not infer a desired label from case order."
        ),
        user_prompt=json.dumps(payload, ensure_ascii=False, default=str),
        model=model,
        max_tokens=max_tokens,
        temperature=0.0,
        schema=THEORY_SEMANTIC_GOLD_JUDGE_SCHEMA,
        metadata={
            "subsystem": "TheorySemanticGoldJudge",
            "provider_name": str(getattr(provider, "provider_name", "") or ""),
            "model_tier": model_tier,
            PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY: True,
        },
    )
    response = provider.generate(request)
    packet = extract_json_object(
        response.text,
        label="hidden theory semantic gold judgment",
    )
    errors = validate_theory_semantic_gold_judgment(
        packet,
        claim_ids=claim_ids,
        calibration_case_ids=case_ids,
    )
    if errors:
        raise ValueError("invalid hidden theory semantic judgment: " + "; ".join(errors))

    assessment_by_case = {
        str(row["case_id"]): str(row["status"])
        for row in packet["assessments"]
    }
    expected_by_case = {
        str(row["case_id"]): str(row["expected_status"])
        for row in calibration_cases
    }
    calibration_results = [
        {
            "case_id_hash": stable_hash(case_id),
            "correct": assessment_by_case[case_id] == expected_by_case[case_id],
        }
        for case_id in case_ids
    ]
    calibrated = bool(
        calibration_results and all(row["correct"] for row in calibration_results)
    )
    candidate_assessment = next(
        row for row in packet["assessments"] if row["case_id"] == "candidate"
    )
    candidate_status = str(candidate_assessment["status"])
    passed = bool(calibrated and candidate_status == "PASS")
    body = {
        "artifact_kind": "HiddenTheorySemanticGoldJudgment",
        "task_id_hash": stable_hash(task_id),
        "provider": str(response.provider or getattr(provider, "provider_name", "")),
        "model": str(response.model or model),
        "model_tier": model_tier,
        "rubric_hash": stable_hash(rubric),
        "reference_documents_hash": stable_hash(reference_documents),
        "candidate_documents_hash": stable_hash(candidate_documents),
        "calibration_cases_hash": stable_hash(calibration_cases),
        "n_claims": len(claim_ids),
        "n_calibration_cases": len(case_ids),
        "n_calibration_cases_correct": sum(
            row["correct"] is True for row in calibration_results
        ),
        "calibration_results": calibration_results,
        "semantic_judge_calibrated": calibrated,
        "candidate_status": candidate_status,
        "candidate_claim_status_counts": _claim_status_counts(
            candidate_assessment
        ),
        "passed": passed,
        "raw_response_fingerprint": stable_hash(response.text),
        "proof_evidence_status": "SEMANTIC_GOLD_JUDGMENT_NOT_PROOF_EVIDENCE",
        "boundary": THEORY_SEMANTIC_GOLD_JUDGE_BOUNDARY,
    }
    body["judgment_hash"] = stable_hash(body)
    return body


def validate_theory_semantic_gold_judgment(
    packet: Mapping[str, Any],
    *,
    claim_ids: Sequence[str],
    calibration_case_ids: Sequence[str],
) -> list[str]:
    errors: list[str] = []
    assessments = packet.get("assessments", [])
    if not isinstance(assessments, list):
        return ["assessments must be an array"]
    expected_case_ids = [*calibration_case_ids, "candidate"]
    observed_case_ids = [
        str(row.get("case_id", "") or "")
        for row in assessments
        if isinstance(row, Mapping)
    ]
    if len(observed_case_ids) != len(assessments):
        errors.append("every document assessment must be an object")
    if (
        len(observed_case_ids) != len(expected_case_ids)
        or set(observed_case_ids) != set(expected_case_ids)
        or len(set(observed_case_ids)) != len(observed_case_ids)
    ):
        errors.append("assessments must preserve exact document case identities")
    for index, assessment in enumerate(assessments):
        if isinstance(assessment, Mapping):
            errors.extend(
                _document_assessment_errors(
                    assessment,
                    claim_ids=claim_ids,
                    label=f"assessments[{index}]",
                )
            )
    return sorted(set(errors))


def _document_assessment_errors(
    assessment: Mapping[str, Any],
    *,
    claim_ids: Sequence[str],
    label: str,
) -> list[str]:
    errors: list[str] = []
    status = str(assessment.get("status", "") or "")
    if status not in THEORY_SEMANTIC_DOCUMENT_STATUSES:
        errors.append(f"{label} has invalid status")
    rows = assessment.get("claim_assessments", [])
    if not isinstance(rows, list):
        return [*errors, f"{label} claim_assessments must be an array"]
    observed_claim_ids = [
        str(row.get("claim_id", "") or "")
        for row in rows
        if isinstance(row, Mapping)
    ]
    if len(observed_claim_ids) != len(rows):
        errors.append(f"{label} claim assessments must be objects")
    if (
        len(observed_claim_ids) != len(claim_ids)
        or set(observed_claim_ids) != set(claim_ids)
        or len(set(observed_claim_ids)) != len(observed_claim_ids)
    ):
        errors.append(f"{label} must preserve exact claim identities")
    claim_statuses: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        claim_status = str(row.get("status", "") or "")
        claim_statuses.append(claim_status)
        if claim_status not in THEORY_SEMANTIC_CLAIM_STATUSES:
            errors.append(f"{label} claim {index} has invalid status")
    expected_status = (
        "FAIL"
        if "VIOLATED" in claim_statuses
        else "INCONCLUSIVE"
        if "INCONCLUSIVE" in claim_statuses
        else "PASS"
        if claim_statuses and len(claim_statuses) == len(claim_ids)
        else ""
    )
    if expected_status and status != expected_status:
        errors.append(f"{label} status is inconsistent with claim assessments")
    return errors


def _rubric_claim_ids(rubric: Mapping[str, Any]) -> list[str]:
    claims = rubric.get("claims", [])
    if not isinstance(claims, list) or not claims:
        raise ValueError("hidden theory semantic rubric must contain claims")
    claim_ids = [
        str(row.get("claim_id", "") or "")
        for row in claims
        if isinstance(row, Mapping)
    ]
    if len(claim_ids) != len(claims) or any(not value for value in claim_ids):
        raise ValueError("hidden theory semantic rubric claim identities are invalid")
    if len(set(claim_ids)) != len(claim_ids):
        raise ValueError("hidden theory semantic rubric claim identities repeat")
    return claim_ids


def _calibration_case_ids(cases: Sequence[Mapping[str, Any]]) -> list[str]:
    if not cases:
        raise ValueError("hidden theory semantic calibration cases are missing")
    case_ids = [str(row.get("case_id", "") or "") for row in cases]
    if any(not value for value in case_ids) or len(set(case_ids)) != len(case_ids):
        raise ValueError("hidden theory semantic calibration identities are invalid")
    if any(
        str(row.get("expected_status", "") or "")
        not in THEORY_SEMANTIC_DOCUMENT_STATUSES
        for row in cases
    ):
        raise ValueError("hidden theory semantic calibration expectations are invalid")
    return case_ids


def _claim_status_counts(assessment: Mapping[str, Any]) -> dict[str, int]:
    rows = assessment.get("claim_assessments", [])
    return {
        status: sum(
            isinstance(row, Mapping) and row.get("status") == status
            for row in rows
        )
        for status in sorted(THEORY_SEMANTIC_CLAIM_STATUSES)
    }

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
THEORY_SEMANTIC_CLAIM_STATUSES = frozenset({"SATISFIED", "VIOLATED", "INCONCLUSIVE"})
THEORY_SEMANTIC_DOCUMENT_STATUSES = frozenset({"PASS", "FAIL", "INCONCLUSIVE"})
THEORY_SEMANTIC_GOLD_JUDGE_PROTOCOL_VERSION = 10
THEORY_SEMANTIC_ADVERSARIAL_GOLD_JUDGE_PROTOCOL_VERSION = 11
THEORY_SEMANTIC_CANDIDATE_STRATEGIES = frozenset({"integrated_single", "integrated_plus_adversarial"})


def _semantic_protocol_version(candidate_adjudication_strategy: str) -> int:
    if candidate_adjudication_strategy == "integrated_single":
        return THEORY_SEMANTIC_GOLD_JUDGE_PROTOCOL_VERSION
    if candidate_adjudication_strategy == "integrated_plus_adversarial":
        return THEORY_SEMANTIC_ADVERSARIAL_GOLD_JUDGE_PROTOCOL_VERSION
    raise ValueError(
        "candidate adjudication strategy must be integrated_single or "
        "integrated_plus_adversarial"
    )


def _theory_semantic_gold_judge_schema(
    *,
    required_case_ids: Sequence[str],
    claim_ids: Sequence[str],
    evidence_refs: Sequence[str],
) -> dict[str, Any]:
    if claim_ids:
        assessment_schema: dict[str, Any] = {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "document_status",
                "document_decisive_evidence_ref",
                "claim_statuses",
                "decisive_evidence_refs",
            ],
            "properties": {
                "document_status": {
                    "type": "string",
                    "enum": sorted(THEORY_SEMANTIC_DOCUMENT_STATUSES),
                },
                "document_decisive_evidence_ref": {
                    "type": "string",
                    "enum": list(evidence_refs),
                },
                "claim_statuses": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(claim_ids),
                    "properties": {
                        claim_id: {"type": "string", "enum": sorted(THEORY_SEMANTIC_CLAIM_STATUSES)}
                        for claim_id in claim_ids
                    },
                },
                "decisive_evidence_refs": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(claim_ids),
                    "properties": {
                        claim_id: {"type": "string", "enum": list(evidence_refs)} for claim_id in claim_ids
                    },
                },
            },
        }
    else:
        assessment_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["status"],
            "properties": {"status": {"type": "string", "enum": sorted(THEORY_SEMANTIC_DOCUMENT_STATUSES)}},
        }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["assessments"],
        "properties": {
            "assessments": {
                "type": "object",
                "additionalProperties": False,
                "required": list(required_case_ids),
                "properties": {
                    case_id: deepcopy(assessment_schema)
                    for case_id in required_case_ids
                },
            }
        },
    }


def _materialize_semantic_assessment_packet(
    payload: Mapping[str, Any],
    *,
    claim_ids: Sequence[str],
    evidence_by_ref: Mapping[str, str],
) -> dict[str, Any]:
    raw_assessments = payload.get("assessments")
    if not isinstance(raw_assessments, Mapping):
        return deepcopy(dict(payload))
    assessments: list[dict[str, Any]] = []
    for case_id, raw_assessment in raw_assessments.items():
        assessment = dict(raw_assessment) if isinstance(raw_assessment, Mapping) else {}
        if claim_ids:
            document_status = str(assessment.get("document_status", "") or "")
            document_evidence_ref = str(assessment.get("document_decisive_evidence_ref", "") or "")
            raw_statuses = assessment.get("claim_statuses", {})
            raw_statuses = raw_statuses if isinstance(raw_statuses, Mapping) else {}
            raw_refs = assessment.get("decisive_evidence_refs", {})
            raw_refs = raw_refs if isinstance(raw_refs, Mapping) else {}
            claim_assessments = [
                {
                    "claim_id": str(claim_id),
                    "status": str(status),
                    "decisive_excerpt": str(evidence_by_ref.get(str(raw_refs.get(claim_id, "")), "")),
                }
                for claim_id, status in raw_statuses.items()
            ]
            claim_status = _derived_document_status(
                [str(row["status"]) for row in claim_assessments],
                expected_claim_count=len(claim_ids),
            )
            status = _combined_document_status(document_status, claim_status)
        else:
            claim_assessments = []
            status = str(assessment.get("status", "") or "")
            document_status = ""
            document_evidence_ref = ""
        assessments.append(
            {
                "case_id": str(case_id),
                "status": status,
                "document_status": document_status,
                "document_decisive_excerpt": str(evidence_by_ref.get(document_evidence_ref, "")),
                "claim_assessments": claim_assessments,
            }
        )
    return {"assessments": assessments}


def _semantic_evidence_units(document_cases: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "case_id": str(case.get("case_id", "") or ""),
            "document_path": f"document_{document_index:04d}",
            "evidence_ref": f"{case.get('case_id', '')}:{document_index}:{paragraph_index}",
            "content": content,
        }
        for case in document_cases
        if isinstance(case, Mapping)
        for document_index, document in enumerate(case.get("documents", []) or [])
        if isinstance(document, Mapping)
        for paragraph_index, content in enumerate(
            value.strip()
            for value in str(document.get("content", "") or "").split("\n\n")
            if value.strip()
        )
    ]


def _generate_semantic_assessment_batch(
    *,
    provider: GeneratorBackend,
    task_id: str,
    visible_question: Mapping[str, Any],
    reference_documents: Sequence[Mapping[str, Any]],
    rubric: Mapping[str, Any],
    document_cases: Sequence[Mapping[str, Any]],
    required_case_ids: Sequence[str],
    claim_ids: Sequence[str],
    model: str,
    model_tier: str,
    max_tokens: int,
    artifact_role: str,
    phase: str,
) -> tuple[dict[str, Any], Any]:
    evidence_units = _semantic_evidence_units(document_cases)
    evidence_by_ref = {row["evidence_ref"]: row["content"] for row in evidence_units}
    payload = {
        "task": {
            "id": task_id,
            "visible_question": deepcopy(dict(visible_question)),
            "semantic_artifact_role": artifact_role,
        },
        "reference_documents": deepcopy(list(reference_documents)),
        "claim_rubric": deepcopy(dict(rubric)),
        "document_evidence_units": evidence_units,
        "required_document_case_ids": list(required_case_ids),
        "rubric_claim_ids": _rubric_claim_ids(rubric),
        "adjudication_phase": phase,
        "boundary": THEORY_SEMANTIC_GOLD_JUDGE_BOUNDARY,
    }
    request = GeneratorRequest(
        system_prompt=(
            "You are an independent scientific-document adjudicator. Compare every document set "
            "with the reference and claim rubric at the level of statistical and mathematical "
            "meaning. Accept equivalent notation and algebra. For each rubric claim, inspect the "
            "complete endorsed derivation, including intermediate displayed equations and "
            "dependencies; a correct final conclusion does not cancel a false, circular, or "
            "unsupported step. Treat the candidate as the conjunction of every active assertion it "
            "contains. Scan for both supporting and conflicting passages before deciding; a later "
            "correct caveat does not erase an earlier false or unsupported assertion. Reject "
            "contradictory assumptions, incorrect method identification, unjustified limits, "
            "unsupported source/result claims, or evidence-authority violations. Do not grade "
            "wording, formatting, or keyword overlap. Reconstruct decisive equations or "
            "counterexamples when needed. In candidate adjudication, assess the complete document "
            "set once: document_status covers any material active falsehood, including one "
            "outside the listed rubric claims, while claim_statuses separately assess every "
            "required claim. Reconstruct decisive transitions from definitions or the reference "
            "and search the whole candidate for contradictions before selecting evidence. "
            "Use PASS only when every required rubric claim is established and no material "
            "falsehood appears; use FAIL for a material active contradiction or invalid asserted "
            "derivation; use INCONCLUSIVE only when no material contradiction is established but "
            "required support is missing or indeterminate. For an omitted claim, an explicit "
            "statement of noncoverage, or material outside the document's stated scope, use "
            "INCONCLUSIVE rather than VIOLATED unless the document actively asserts something "
            "false about that claim. If assumptions, a problem card, or the proof branches "
            "cover only a strict subdomain while an active conclusion retains broader "
            "quantifiers, that is an invalid asserted derivation and must be treated as FAIL "
            "or VIOLATED, not as mere omitted coverage. Calibration cases are unlabeled, and "
            "the candidate phase contains no calibration cases. Follow the keyed response schema "
            "exactly. During calibration, candidate-mode negative control, and candidate "
            "adjudication, use the same claim-level assessment: return document_status and one "
            "document_decisive_evidence_ref, then "
            "claim_statuses and decisive_evidence_refs keyed by every claim ID in "
            "rubric_claim_ids. A document can FAIL even when all listed claims are SATISFIED. "
            "Select only supplied evidence_ref values, preferring a violating paragraph over "
            "support. Do not copy or rewrite excerpts; the evaluator resolves references and "
            "combines document-wide and per-claim status."
            + (
                " This is an independent adversarial verification pass. Assume the prior "
                "coverage assessment may have overlooked a small but material active "
                "falsehood. Recompute comparisons and threshold decisions from the supplied "
                "reference, inspect prose adjacent to copied tables or equations, and try to "
                "falsify every SATISFIED conclusion before returning PASS. Do not defer to a "
                "plausible overall narrative or to the prior pass."
                if phase.endswith("_adversarial")
                else ""
            )
        ),
        user_prompt=json.dumps(payload, ensure_ascii=False, default=str),
        model=model,
        max_tokens=max_tokens,
        temperature=0.0,
        schema=_theory_semantic_gold_judge_schema(
            required_case_ids=required_case_ids,
            claim_ids=claim_ids,
            evidence_refs=tuple(evidence_by_ref),
        ),
        metadata={
            "subsystem": (
                "TheorySemanticGoldJudge"
                if artifact_role == "theory"
                else "ScientificDocumentSemanticGoldJudge"
            ),
            "semantic_artifact_role": artifact_role,
            "semantic_adjudication_phase": phase,
            "provider_name": str(getattr(provider, "provider_name", "") or ""),
            "model_tier": model_tier,
            PROVIDER_STRUCTURED_OUTPUT_METADATA_KEY: True,
        },
    )
    response = provider.generate(request)
    raw_packet = extract_json_object(response.text, label=f"hidden {phase} semantic gold judgment")
    packet = _materialize_semantic_assessment_packet(
        raw_packet,
        claim_ids=claim_ids,
        evidence_by_ref=evidence_by_ref,
    )
    errors = validate_theory_semantic_gold_judgment(
        packet,
        claim_ids=claim_ids,
        required_case_ids=required_case_ids,
    )
    if claim_ids and any(
        not str(row.get("decisive_excerpt", "") or "").strip()
        for assessment in packet.get("assessments", [])
        for row in assessment.get("claim_assessments", [])
    ):
        errors.append("every claim needs a valid decisive candidate evidence ref")
    if claim_ids and any(
        not str(assessment.get("document_decisive_excerpt", "") or "").strip()
        for assessment in packet.get("assessments", [])
    ):
        errors.append("document status needs a valid decisive candidate evidence ref")
    if errors:
        raise ValueError(f"invalid hidden {phase} semantic judgment: " + "; ".join(errors))
    return packet, response


def _combine_semantic_assessment_packets(
    primary_packet: Mapping[str, Any],
    adversarial_packet: Mapping[str, Any],
    *,
    claim_ids: Sequence[str],
    required_case_ids: Sequence[str],
) -> dict[str, Any]:
    def by_id(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, Mapping[str, Any]]:
        return {str(row.get(field, "") or ""): row for row in rows}

    primary_by_case = by_id(primary_packet["assessments"], "case_id")
    adversarial_by_case = by_id(adversarial_packet["assessments"], "case_id")
    claim_priority = {"SATISFIED": 0, "INCONCLUSIVE": 1, "VIOLATED": 2}
    document_priority = {"PASS": 0, "INCONCLUSIVE": 1, "FAIL": 2}
    assessments: list[dict[str, Any]] = []
    for case_id in required_case_ids:
        primary = primary_by_case[case_id]
        adversarial = adversarial_by_case[case_id]
        primary_claims = by_id(primary["claim_assessments"], "claim_id")
        adversarial_claims = by_id(adversarial["claim_assessments"], "claim_id")
        claims: list[dict[str, Any]] = []
        for claim_id in claim_ids:
            decisive = max(
                (primary_claims[claim_id], adversarial_claims[claim_id]),
                key=lambda row: claim_priority[str(row["status"])],
            )
            claims.append(
                {"claim_id": claim_id, "status": str(decisive["status"]),
                 "decisive_excerpt": str(decisive["decisive_excerpt"])}
            )
        decisive_document = max(
            (primary, adversarial),
            key=lambda row: document_priority[str(row["document_status"])],
        )
        document_status = str(decisive_document["document_status"])
        claim_status = _derived_document_status([row["status"] for row in claims], expected_claim_count=len(claim_ids))
        assessments.append(
            {
                "case_id": case_id,
                "status": _combined_document_status(document_status, claim_status),
                "document_status": document_status,
                "document_decisive_excerpt": str(decisive_document["document_decisive_excerpt"]),
                "claim_assessments": claims,
            }
        )
    return {"assessments": assessments}


def _generate_semantic_assessment_passes(
    *,
    candidate_adjudication_strategy: str,
    **kwargs: Any,
) -> tuple[dict[str, Any], list[Any]]:
    _semantic_protocol_version(candidate_adjudication_strategy)
    primary_packet, primary_response = _generate_semantic_assessment_batch(**kwargs)
    if candidate_adjudication_strategy == "integrated_single":
        return primary_packet, [primary_response]
    adversarial_packet, adversarial_response = _generate_semantic_assessment_batch(
        **{**kwargs, "phase": f"{kwargs['phase']}_adversarial"}
    )
    return (
        _combine_semantic_assessment_packets(
            primary_packet,
            adversarial_packet,
            claim_ids=kwargs["claim_ids"],
            required_case_ids=kwargs["required_case_ids"],
        ),
        [primary_response, adversarial_response],
    )


def theory_semantic_activation_judgment_errors(
    judgment: Mapping[str, Any],
    *,
    task_id: str,
    reference_documents: Sequence[Mapping[str, Any]],
    rubric: Mapping[str, Any],
    calibration_cases: Sequence[Mapping[str, Any]],
    candidate_mode_negative_cases: Sequence[Mapping[str, Any]],
    model: str,
    model_tier: str,
    semantic_artifact_role: str,
    candidate_adjudication_strategy: str = "integrated_single",
) -> list[str]:
    """Validate a frozen evaluator qualification without rerunning the model."""

    errors: list[str] = []
    protocol_version = _semantic_protocol_version(candidate_adjudication_strategy)
    expected_values = {
        "protocol_version": protocol_version,
        "task_id_hash": stable_hash(task_id),
        "semantic_artifact_role": semantic_artifact_role,
        "model": model,
        "model_tier": model_tier,
        "rubric_hash": stable_hash(rubric),
        "reference_documents_hash": stable_hash(reference_documents),
        "candidate_documents_hash": stable_hash(reference_documents),
        "calibration_cases_hash": stable_hash(calibration_cases),
        "candidate_mode_negative_cases_hash": stable_hash(candidate_mode_negative_cases),
        "n_claims": len(_rubric_claim_ids(rubric)),
        "n_calibration_cases": len(calibration_cases),
        "n_candidate_mode_negative_cases": len(candidate_mode_negative_cases),
    }
    for field, expected in expected_values.items():
        if judgment.get(field) != expected:
            errors.append(f"activation judgment {field} mismatch")
    if candidate_adjudication_strategy != "integrated_single" and judgment.get(
        "candidate_adjudication_strategy"
    ) != candidate_adjudication_strategy:
        errors.append("activation judgment candidate adjudication strategy mismatch")

    def exact_correct_results(field: str, expected_count: int) -> bool:
        rows = judgment.get(field, [])
        return isinstance(rows, list) and len(rows) == expected_count and all(
            isinstance(row, Mapping) and row.get("correct") is True for row in rows
        )

    calibration_results = judgment.get("calibration_results", [])
    if not exact_correct_results("calibration_results", len(calibration_cases)):
        errors.append("activation calibration did not pass every frozen case")
    negative_results = judgment.get("candidate_mode_negative_results", [])
    if not exact_correct_results(
        "candidate_mode_negative_results", len(candidate_mode_negative_cases)
    ):
        errors.append("activation candidate-mode controls did not all pass")
    expected_counts = {
        "n_calibration_cases_correct": len(calibration_cases),
        "n_candidate_mode_negative_cases_correct": len(candidate_mode_negative_cases),
    }
    for field, expected in expected_counts.items():
        if int(judgment.get(field, 0) or 0) != expected:
            errors.append(f"activation {field} mismatch")
    for field in ("semantic_judge_calibrated", "candidate_mode_negative_controls_passed", "passed"):
        if judgment.get(field) is not True:
            errors.append(f"activation judgment {field} is not true")
    for field in ("candidate_status", "candidate_document_status"):
        if judgment.get(field) != "PASS":
            errors.append(f"activation reference {field} is not PASS")
    passes_per_case = 2 if candidate_adjudication_strategy == "integrated_plus_adversarial" else 1
    call_counts = {
        "n_model_calls": passes_per_case * (1 + len(calibration_cases) + len(candidate_mode_negative_cases)),
        "calibration_model_calls": passes_per_case * len(calibration_cases),
    }
    for field, expected in call_counts.items():
        if int(judgment.get(field, 0) or 0) != expected:
            errors.append(f"activation {field} mismatch")
    recorded_hash = str(judgment.get("judgment_hash", "") or "")
    hash_payload = deepcopy(dict(judgment))
    hash_payload.pop("judgment_hash", None)
    if not recorded_hash or stable_hash(hash_payload) != recorded_hash:
        errors.append("activation judgment hash mismatch")
    return errors


def run_theory_semantic_gold_judge(
    *,
    provider: GeneratorBackend,
    task_id: str,
    visible_question: Mapping[str, Any],
    candidate_documents: Sequence[Mapping[str, Any]],
    reference_documents: Sequence[Mapping[str, Any]],
    rubric: Mapping[str, Any],
    calibration_cases: Sequence[Mapping[str, Any]],
    candidate_mode_negative_cases: Sequence[Mapping[str, Any]] = (),
    model: str = LIVE_EVALUATION_CLAUDE_MODEL,
    model_tier: str = LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    max_tokens: int = 6000,
    semantic_artifact_role: str = "theory",
    activation_judgment: Mapping[str, Any] | None = None,
    candidate_adjudication_strategy: str = "integrated_single",
) -> dict[str, Any]:
    """Judge one frozen document after an isolated hidden-case calibration."""

    artifact_role = str(semantic_artifact_role).strip()
    if not artifact_role:
        raise ValueError("semantic artifact role must be nonempty")
    protocol_version = _semantic_protocol_version(candidate_adjudication_strategy)
    claim_ids = _rubric_claim_ids(rubric)
    case_ids = _calibration_case_ids(calibration_cases)
    calibration_responses: list[Any] = []
    negative_case_ids = _calibration_case_ids(candidate_mode_negative_cases) if candidate_mode_negative_cases else []
    candidate_mode_negative_responses: list[Any] = []
    activation_model_calls = 0

    def assess(case_id: str, documents: Sequence[Mapping[str, Any]], phase: str) -> tuple[dict[str, Any], list[Any]]:
        packet, responses = _generate_semantic_assessment_passes(
            candidate_adjudication_strategy=candidate_adjudication_strategy,
            provider=provider,
            task_id=task_id,
            visible_question=visible_question,
            reference_documents=reference_documents,
            rubric=rubric,
            document_cases=[{"case_id": case_id, "documents": deepcopy(list(documents))}],
            required_case_ids=[case_id],
            claim_ids=claim_ids,
            model=model,
            model_tier=model_tier,
            max_tokens=max_tokens,
            artifact_role=artifact_role,
            phase=phase,
        )
        return deepcopy(packet["assessments"][0]), responses

    if activation_judgment is not None:
        activation_errors = theory_semantic_activation_judgment_errors(
            activation_judgment,
            task_id=task_id,
            reference_documents=reference_documents,
            rubric=rubric,
            calibration_cases=calibration_cases,
            candidate_mode_negative_cases=candidate_mode_negative_cases,
            model=model,
            model_tier=model_tier,
            semantic_artifact_role=artifact_role,
            candidate_adjudication_strategy=candidate_adjudication_strategy,
        )
        if activation_errors:
            raise ValueError(
                "invalid hidden semantic activation judgment: "
                + "; ".join(activation_errors)
            )
        calibration_results = deepcopy(list(activation_judgment.get("calibration_results", []) or []))
        candidate_mode_negative_results = deepcopy(
            list(activation_judgment.get("candidate_mode_negative_results", []) or [])
        )
        candidate_mode_negative_controls_passed = True
        calibrated = True
        activation_model_calls = int(activation_judgment.get("n_model_calls", 0) or 0)
    else:
        model_case_ids = [f"case_{index:04d}" for index in range(1, len(case_ids) + 1)]
        case_id_by_model_case_id = dict(zip(model_case_ids, case_ids))
        calibration_assessments: list[dict[str, Any]] = []
        for model_case_id, row in zip(model_case_ids, calibration_cases):
            assessment, case_responses = assess(
                model_case_id, row.get("documents", []) or [], "calibration"
            )
            calibration_assessments.append(assessment)
            calibration_responses.extend(case_responses)
        assessment_by_case = {
            case_id_by_model_case_id[str(row["case_id"])]: str(row["status"])
            for row in calibration_assessments
        }
        expected_by_case = {str(row["case_id"]): str(row["expected_status"]) for row in calibration_cases}
        calibration_results = [
            {
                "case_id_hash": stable_hash(case_id),
                "correct": assessment_by_case[case_id] == expected_by_case[case_id],
            }
            for case_id in case_ids
        ]
        calibrated = bool(calibration_results and all(row["correct"] for row in calibration_results))
        candidate_mode_negative_results: list[dict[str, Any]] = []
        for case_id, row in zip(negative_case_ids, candidate_mode_negative_cases):
            assessment, case_responses = assess(
                "candidate", row.get("documents", []) or [], "candidate_mode_negative"
            )
            candidate_mode_negative_results.append(
                {
                    "case_id_hash": stable_hash(case_id),
                    "correct": str(assessment["status"]) == str(row["expected_status"]),
                }
            )
            candidate_mode_negative_responses.extend(case_responses)
        candidate_mode_negative_controls_passed = all(
            row["correct"] is True for row in candidate_mode_negative_results
        )
        calibrated = bool(calibrated and candidate_mode_negative_controls_passed)
    candidate_assessment, candidate_responses = assess(
        "candidate", candidate_documents, "candidate_integrated"
    )
    candidate_status = str(candidate_assessment["status"])
    passed = bool(calibrated and candidate_status == "PASS")
    candidate_provider = str(candidate_responses[-1].provider or "")
    candidate_model = str(candidate_responses[-1].model or "")
    activation_provider = str(activation_judgment.get("provider", "") if activation_judgment else "")
    activation_model = str(activation_judgment.get("model", "") if activation_judgment else "")
    activation_judgment_hash = str(activation_judgment.get("judgment_hash", "") if activation_judgment else "")
    calibration_texts = [response.text for response in calibration_responses]
    negative_texts = [response.text for response in candidate_mode_negative_responses]
    candidate_texts = [response.text for response in candidate_responses]
    calibration_fingerprint = (
        str(activation_judgment.get("calibration_raw_response_fingerprint", "") or "")
        if activation_judgment
        else stable_hash(calibration_texts)
    )
    negative_fingerprint = (
        str(activation_judgment.get("candidate_mode_negative_raw_response_fingerprint", "") or "")
        if activation_judgment
        else stable_hash(negative_texts)
    )
    body = {
        "artifact_kind": "HiddenTheorySemanticGoldJudgment"
        if artifact_role == "theory"
        else "HiddenScientificDocumentSemanticGoldJudgment",
        "semantic_artifact_role": artifact_role,
        "protocol_version": protocol_version,
        "candidate_adjudication_strategy": candidate_adjudication_strategy,
        "task_id_hash": stable_hash(task_id),
        "provider": str(
            candidate_provider or activation_provider
            or (calibration_responses[0].provider if calibration_responses else "")
            or getattr(provider, "provider_name", "")
        ),
        "model": str(
            candidate_model or activation_model
            or (calibration_responses[0].model if calibration_responses else "") or model
        ),
        "model_tier": model_tier,
        "n_model_calls": len(candidate_responses)
        + len(calibration_responses)
        + len(candidate_mode_negative_responses),
        "calibration_candidate_context_isolated": True,
        "calibration_case_ids_opaque": True,
        "calibration_claim_assessments_requested": True,
        "calibration_model_calls": len(calibration_responses),
        "calibration_reused_from_activation": bool(activation_judgment),
        "activation_model_calls": activation_model_calls,
        "activation_judgment_hash": activation_judgment_hash,
        "candidate_mode_negative_cases_configured": bool(candidate_mode_negative_cases),
        "candidate_mode_negative_case_ids_opaque": True,
        "candidate_mode_negative_claim_assessments_requested": True,
        "candidate_mode_negative_integrated_context": True,
        "candidate_mode_negative_model_calls": len(candidate_mode_negative_responses),
        "n_candidate_mode_negative_cases": len(negative_case_ids),
        "n_candidate_mode_negative_cases_correct": sum(
            row["correct"] is True for row in candidate_mode_negative_results
        ),
        "candidate_mode_negative_results": candidate_mode_negative_results,
        "candidate_mode_negative_controls_passed": candidate_mode_negative_controls_passed,
        "candidate_claim_assessments_requested": True,
        "candidate_document_status_requested": True,
        "candidate_claim_scope_isolated": False,
        "candidate_integrated_context": True,
        "candidate_claim_model_calls": len(candidate_responses),
        "candidate_integrated_model_calls": len(candidate_responses),
        "candidate_adversarial_model_calls": int(candidate_adjudication_strategy == "integrated_plus_adversarial"),
        "rubric_hash": stable_hash(rubric),
        "reference_documents_hash": stable_hash(reference_documents),
        "candidate_documents_hash": stable_hash(candidate_documents),
        "calibration_cases_hash": stable_hash(calibration_cases),
        "candidate_mode_negative_cases_hash": stable_hash(candidate_mode_negative_cases),
        "n_claims": len(claim_ids),
        "n_calibration_cases": len(case_ids),
        "n_calibration_cases_correct": sum(row["correct"] is True for row in calibration_results),
        "calibration_results": calibration_results,
        "semantic_judge_calibrated": calibrated,
        "candidate_status": candidate_status,
        "candidate_document_status": str(candidate_assessment.get("document_status", "") or ""),
        "candidate_document_decisive_excerpt_hash": stable_hash(
            candidate_assessment.get("document_decisive_excerpt", "")
        ),
        "candidate_claim_status_counts": _claim_status_counts(candidate_assessment),
        "candidate_claim_assessments": [
            {
                "claim_id_hash": stable_hash(str(row["claim_id"])),
                "status": str(row["status"]),
                "decisive_excerpt_hash": stable_hash(row["decisive_excerpt"]),
            }
            for row in candidate_assessment["claim_assessments"]
        ],
        "passed": passed,
        "calibration_raw_response_fingerprint": calibration_fingerprint,
        "candidate_mode_negative_raw_response_fingerprint": negative_fingerprint,
        "candidate_raw_response_fingerprint": stable_hash(candidate_texts),
        "raw_response_fingerprint": stable_hash({
            "activation_judgment_hash": activation_judgment_hash,
            "calibration": calibration_fingerprint,
            "candidate_mode_negative": negative_fingerprint,
            "candidate": candidate_texts,
        }),
        "proof_evidence_status": "SEMANTIC_GOLD_JUDGMENT_NOT_PROOF_EVIDENCE",
        "boundary": THEORY_SEMANTIC_GOLD_JUDGE_BOUNDARY,
    }
    body["judgment_hash"] = stable_hash(body)
    return body


def validate_theory_semantic_gold_judgment(
    packet: Mapping[str, Any],
    *,
    claim_ids: Sequence[str],
    calibration_case_ids: Sequence[str] = (),
    required_case_ids: Sequence[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    assessments = packet.get("assessments", [])
    if not isinstance(assessments, list):
        return ["assessments must be an array"]
    expected_case_ids = (
        list(required_case_ids)
        if required_case_ids is not None
        else [*calibration_case_ids, "candidate"]
    )
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
    claim_derived_status = _derived_document_status(
        claim_statuses,
        expected_claim_count=len(claim_ids),
    )
    document_status = str(assessment.get("document_status", "") or "")
    if claim_ids and document_status not in THEORY_SEMANTIC_DOCUMENT_STATUSES:
        errors.append(f"{label} has invalid document_status")
    if claim_ids and not str(
        assessment.get("document_decisive_excerpt", "") or ""
    ).strip():
        errors.append(f"{label} has no document decisive excerpt")
    expected_status = (
        _combined_document_status(document_status, claim_derived_status)
        if claim_ids
        else claim_derived_status
    )
    if expected_status and status != expected_status:
        errors.append(
            f"{label} status is inconsistent with document and claim assessments"
        )
    return errors


def _derived_document_status(
    claim_statuses: Sequence[str],
    *,
    expected_claim_count: int,
) -> str:
    if "VIOLATED" in claim_statuses:
        return "FAIL"
    if "INCONCLUSIVE" in claim_statuses:
        return "INCONCLUSIVE"
    if claim_statuses and len(claim_statuses) == expected_claim_count and set(
        claim_statuses
    ) <= THEORY_SEMANTIC_CLAIM_STATUSES:
        return "PASS"
    return ""


def _combined_document_status(*statuses: str) -> str:
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status == "INCONCLUSIVE" for status in statuses):
        return "INCONCLUSIVE"
    if statuses and all(status == "PASS" for status in statuses):
        return "PASS"
    return ""


def _rubric_claim_ids(rubric: Mapping[str, Any]) -> list[str]:
    claims = rubric.get("claims", [])
    if not isinstance(claims, list) or not claims:
        raise ValueError("hidden theory semantic rubric must contain claims")
    claim_ids = [
        str(row.get("claim_id", "") or "")
        for row in claims
        if isinstance(row, Mapping)
    ]
    if (
        len(claim_ids) != len(claims)
        or any(not value for value in claim_ids)
        or len(set(claim_ids)) != len(claim_ids)
    ):
        raise ValueError("hidden theory semantic rubric claim identities are invalid or repeat")
    return claim_ids


def _calibration_case_ids(cases: Sequence[Mapping[str, Any]]) -> list[str]:
    if not cases:
        raise ValueError("hidden theory semantic calibration cases are missing")
    case_ids = [str(row.get("case_id", "") or "") for row in cases]
    invalid_status = any(
        str(row.get("expected_status", "") or "") not in THEORY_SEMANTIC_DOCUMENT_STATUSES
        for row in cases
    )
    if any(not value for value in case_ids) or len(set(case_ids)) != len(case_ids) or invalid_status:
        raise ValueError("hidden theory semantic calibration identities or expectations are invalid")
    return case_ids


def _claim_status_counts(assessment: Mapping[str, Any]) -> dict[str, int]:
    rows = assessment.get("claim_assessments", [])
    return {
        status: sum(isinstance(row, Mapping) and row.get("status") == status for row in rows)
        for status in sorted(THEORY_SEMANTIC_CLAIM_STATUSES)
    }

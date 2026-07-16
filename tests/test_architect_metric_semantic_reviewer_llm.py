from __future__ import annotations

import json

import pytest

from ai_statistician.architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_SEMANTIC_REVIEW_DIMENSIONS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA,
    ArchitectMetricSemanticReviewerConfig,
    LLMArchitectMetricSemanticReviewerAgent,
    architect_metric_semantic_review_json_schema,
    validate_architect_metric_semantic_review_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.llm_json_repair import PacketValidationError
from ai_statistician.model_backend import GeneratorResponse
from ai_statistician.research_schema import OpenResearchQuestion


def _review_payload(*, accept: bool) -> dict[str, object]:
    status = "PASS" if accept else "FAIL"
    return {
        "prior_finding_reviews": [],
        "dimension_reviews": [
            {
                "dimension": dimension,
                "status": status,
                "rationale": (
                    "The proposed protocol is coherent before execution."
                    if accept
                    else "The stated finite-sample comparison is not justified."
                ),
                "evidence_refs": ["requirement:generic_gate"],
            }
            for dimension in ARCHITECT_METRIC_SEMANTIC_REVIEW_DIMENSIONS
        ],
        "findings": (
            []
            if accept
            else [
                {
                    "severity": "high",
                    "category": "finite_sample_calibration",
                    "summary": "The gate lacks a finite-sample justification.",
                    "required_change": (
                        "Regenerate the contract from an analytically justified "
                        "finite-sample target."
                    ),
                    "repair_scope": "metric_contract",
                    "evidence_refs": ["requirement:generic_gate"],
                }
            ]
        ),
        "overall_verdict": "ACCEPT" if accept else "REVISE",
        "repair_instructions": (
            []
            if accept
            else ["Re-derive and rewrite the full candidate contract."]
        ),
    }


class _Backend:
    provider_name = "anthropic"

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return GeneratorResponse(
            text=json.dumps(self.payload),
            provider="anthropic",
            model=request.model,
            metadata={
                "provider_structured_output_requested": True,
                "provider_structured_output_applied": True,
            },
        )


class _SequenceBackend:
    provider_name = "anthropic"

    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.payloads = payloads
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        payload = self.payloads[min(len(self.requests) - 1, len(self.payloads) - 1)]
        return GeneratorResponse(
            text=json.dumps(payload),
            provider="anthropic",
            model=request.model,
            metadata={
                "provider_structured_output_requested": True,
                "provider_structured_output_applied": True,
            },
        )


def _review(*, accept: bool, reviewer_model: str = "claude-opus-4-8"):
    backend = _Backend(_review_payload(accept=accept))
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "empirical_metric_requirements": [{"requirement_id": "generic_gate"}],
    }
    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model=reviewer_model,
            model_tier="opus",
            max_repair_attempts=0,
        ),
    ).review(
        question=OpenResearchQuestion(
            id="q_metric_review",
            title="Review a generic statistical protocol",
            description="Assess an empirical procedure under a fixed runtime budget.",
        ),
        review_material=material,
        trusted_lineage={
            "authoring_packet_id": "metric-authoring:1",
            "authoring_packet_hash": stable_hash({"candidate": 1}),
            "empirical_metric_requirement_set_id": "metric-set:1",
            "source_agent": "ArchitectMetricContractPlanner",
            "source_model": "claude-sonnet-4-6",
            "source_model_tier": "sonnet",
        },
    )
    return packet, backend, material


def test_preexecution_metric_reviewer_accepts_only_with_independent_lineage() -> None:
    packet, backend, material = _review(accept=True)

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["pre_execution_review"] is True
    assert packet["execution_results_observed"] is False
    assert packet["independent_agent"] is True
    assert packet["independent_model"] is True
    assert packet["independent_model_tier"] is True
    assert packet["review_input_fingerprint"] == stable_hash(material)
    assert packet["reviewed_empirical_metric_requirement_set_id"] == "metric-set:1"
    assert packet["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")
    assert validate_architect_metric_semantic_review_packet(packet) == []
    assert backend.requests[0].metadata["subsystem"] == (
        "ArchitectMetricSemanticReviewer"
    )
    assert backend.requests[0].metadata["model_tier"] == "opus"
    assert backend.requests[0].metadata["provider_structured_output"] is True
    assert "before any coding agent" in backend.requests[0].user_prompt


def test_preexecution_metric_reviewer_returns_typed_revision_feedback() -> None:
    packet, _, _ = _review(accept=False)

    assert packet["overall_verdict"] == "REVISE"
    assert packet["repair_instructions"]
    assert packet["findings"][0]["severity"] == "high"
    assert packet["findings"][0]["repair_scope"] == "metric_contract"
    assert packet["recommended_repair_scope"] == "metric_contract"
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_preexecution_metric_reviewer_routes_missing_semantics_upstream() -> None:
    payload = _review_payload(accept=False)
    payload["findings"][0]["repair_scope"] = "upstream_theory"
    backend = _Backend(payload)
    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model="claude-opus-4-8",
            model_tier="opus",
            max_repair_attempts=0,
        ),
    ).review(
        question=OpenResearchQuestion(
            id="q_metric_theory_review",
            title="Review missing theory semantics",
            description="The DGP calibration is not specified by theory.",
        ),
        review_material={
            "review_stage": "pre_execution_metric_contract_review",
            "execution_results_available": False,
            "empirical_metric_requirements": [
                {"requirement_id": "generic_gate"}
            ],
        },
        trusted_lineage={
            "authoring_packet_id": "metric-authoring:theory-gap",
            "authoring_packet_hash": stable_hash({"candidate": "theory-gap"}),
            "empirical_metric_requirement_set_id": "metric-set:theory-gap",
            "source_agent": "ArchitectMetricContractPlanner",
            "source_model": "claude-sonnet-4-6",
            "source_model_tier": "sonnet",
        },
    )

    assert packet["recommended_repair_scope"] == "upstream_theory"
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_preexecution_metric_reviewer_fails_closed_when_model_is_not_independent() -> None:
    with pytest.raises(PacketValidationError) as exc_info:
        _review(accept=True, reviewer_model="claude-sonnet-4-6")

    assert "requires an independent model" in str(exc_info.value)


def test_metric_reviewer_repair_preserves_exact_active_finding_context() -> None:
    active_ledger = [
        {
            "finding_id": "metric-finding:calibration",
            "finding": {"summary": "The calibration was unsupported."},
        },
        {
            "finding_id": "metric-finding:measurement",
            "finding": {"summary": "The measurement was not identifiable."},
        },
    ]
    invalid_payload = _review_payload(accept=True)
    repaired_payload = _review_payload(accept=True)
    repaired_payload["prior_finding_reviews"] = [
        {
            "finding_id": row["finding_id"],
            "status": "RESOLVED",
            "rationale": "The current candidate explicitly implements the repair.",
            "evidence_refs": ["requirement:generic_gate"],
        }
        for row in active_ledger
    ]
    backend = _SequenceBackend([invalid_payload, repaired_payload])
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "active_prior_finding_ledger": active_ledger,
        "empirical_metric_requirements": [{"requirement_id": "generic_gate"}],
    }

    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model="claude-opus-4-8",
            model_tier="opus",
            max_repair_attempts=1,
        ),
    ).review(
        question=OpenResearchQuestion(
            id="q_metric_finding_repair",
            title="Repair a generic metric contract",
            description="Review a revised pre-execution metric contract.",
        ),
        review_material=material,
        trusted_lineage={
            "authoring_packet_id": "metric-authoring:repair",
            "authoring_packet_hash": stable_hash({"candidate": "repair"}),
            "empirical_metric_requirement_set_id": "metric-set:repair",
            "source_agent": "ArchitectMetricContractPlanner",
            "source_model": "claude-sonnet-4-6",
            "source_model_tier": "sonnet",
        },
    )

    expected_ids = [row["finding_id"] for row in active_ledger]
    prior_schema = backend.requests[0].schema["properties"][
        "prior_finding_reviews"
    ]
    assert prior_schema["minItems"] == 2
    assert prior_schema["maxItems"] == 2
    assert prior_schema["items"]["properties"]["finding_id"]["enum"] == (
        expected_ids
    )
    assert len(backend.requests) == 2
    assert all(finding_id in backend.requests[1].user_prompt for finding_id in expected_ids)
    assert "active_prior_finding_ledger" in backend.requests[1].user_prompt
    assert packet["expected_prior_finding_ids"] == expected_ids
    assert [row["finding_id"] for row in packet["prior_finding_reviews"]] == (
        expected_ids
    )
    assert packet["llm_json_repair_attempts"] == 1
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_metric_reviewer_reports_exact_prior_finding_identity_mismatch() -> None:
    packet, _, _ = _review(accept=True)
    packet["expected_prior_finding_ids"] = ["finding:a", "finding:b"]
    packet["prior_finding_reviews"] = [
        {
            "finding_id": finding_id,
            "status": "RESOLVED",
            "rationale": "The current candidate explicitly closes this finding.",
            "evidence_refs": ["requirement:generic_gate"],
        }
        for finding_id in ("finding:a", "finding:a", "finding:c")
    ]

    errors = validate_architect_metric_semantic_review_packet(packet)

    identity_error = next(
        error
        for error in errors
        if error.startswith("prior_finding_reviews must cover every active")
    )
    assert 'expected=["finding:a", "finding:b"]' in identity_error
    assert 'received=["finding:a", "finding:a", "finding:c"]' in identity_error


def test_metric_review_schema_transforms_for_anthropic_structured_output() -> None:
    anthropic = pytest.importorskip("anthropic")

    dynamic_schema = architect_metric_semantic_review_json_schema(
        {
            "active_prior_finding_ledger": [
                {"finding_id": "finding:one", "finding": {"summary": "one"}},
                {"finding_id": "finding:two", "finding": {"summary": "two"}},
            ]
        }
    )
    transformed = anthropic.transform_schema(dynamic_schema)

    assert transformed["type"] == "object"
    assert transformed["properties"]["overall_verdict"]["type"] == "string"
    transformed_prior_schema = transformed["properties"][
        "prior_finding_reviews"
    ]
    assert transformed_prior_schema["items"]["properties"]["finding_id"][
        "enum"
    ] == ["finding:one", "finding:two"]
    assert "minItems: 2" in transformed_prior_schema["description"]
    assert ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA["properties"][
        "prior_finding_reviews"
    ].get("minItems") is None

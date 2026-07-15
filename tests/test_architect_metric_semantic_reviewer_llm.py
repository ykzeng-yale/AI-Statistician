from __future__ import annotations

import json

import pytest

from ai_statistician.architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_SEMANTIC_REVIEW_DIMENSIONS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA,
    ArchitectMetricSemanticReviewerConfig,
    LLMArchitectMetricSemanticReviewerAgent,
    validate_architect_metric_semantic_review_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.llm_json_repair import PacketValidationError
from ai_statistician.model_backend import GeneratorResponse
from ai_statistician.research_schema import OpenResearchQuestion


def _review_payload(*, accept: bool) -> dict[str, object]:
    status = "PASS" if accept else "FAIL"
    return {
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
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_preexecution_metric_reviewer_fails_closed_when_model_is_not_independent() -> None:
    with pytest.raises(PacketValidationError) as exc_info:
        _review(accept=True, reviewer_model="claude-sonnet-4-6")

    assert "requires an independent model" in str(exc_info.value)


def test_metric_review_schema_transforms_for_anthropic_structured_output() -> None:
    anthropic = pytest.importorskip("anthropic")

    transformed = anthropic.transform_schema(
        ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA
    )

    assert transformed["type"] == "object"
    assert transformed["properties"]["overall_verdict"]["type"] == "string"

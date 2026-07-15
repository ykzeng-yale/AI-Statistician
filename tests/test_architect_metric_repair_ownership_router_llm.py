from __future__ import annotations

import json

import pytest

from ai_statistician.architect_metric_repair_ownership_router_llm import (
    ARCHITECT_METRIC_REPAIR_OWNERSHIP_JSON_SCHEMA,
    ArchitectMetricRepairOwnershipRouterConfig,
    LLMArchitectMetricRepairOwnershipRouterAgent,
    apply_architect_metric_repair_ownership_routes,
    architect_metric_repair_scope_from_decision,
    validate_architect_metric_repair_ownership_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import GeneratorResponse
from ai_statistician.research_schema import OpenResearchQuestion


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


def _semantic_review_packet() -> dict[str, object]:
    return {
        "packet_id": "metric_review:generic",
        "findings": [
            {
                "severity": "high",
                "category": "inconsistent derivation",
                "summary": "The candidate exposes an incorrect source equation.",
                "required_change": "Revise the source derivation and its metric anchor.",
                "repair_scope": "metric_contract",
                "evidence_refs": ["theory_derivation_packet:equation"],
            },
            {
                "severity": "medium",
                "category": "evaluator encoding",
                "summary": "The typed aggregation does not match the prose.",
                "required_change": "Rewrite the metric aggregation only.",
                "repair_scope": "metric_contract",
                "evidence_refs": ["metric_protocol_candidate:aggregation"],
            },
        ],
        "repair_instructions": [
            "Keep every change inside the metric contract."
        ],
    }


def _routing_payload() -> dict[str, object]:
    return {
        "decisions": [
            {
                "finding_index": 0,
                "required_artifact_changes": [
                    {
                        "artifact_role": "source_theory_packet",
                        "change_summary": "Correct the source derivation.",
                    },
                    {
                        "artifact_role": "metric_protocol_candidate",
                        "change_summary": "Refresh the dependent source anchor.",
                    },
                ],
                "metric_author_can_repair_without_revising_source_theory": False,
                "ownership_certainty": "resolved",
                "rationale": "The source equation itself cannot remain unchanged.",
            },
            {
                "finding_index": 1,
                "required_artifact_changes": [
                    {
                        "artifact_role": "metric_protocol_candidate",
                        "change_summary": "Align the typed aggregation with prose.",
                    }
                ],
                "metric_author_can_repair_without_revising_source_theory": True,
                "ownership_certainty": "resolved",
                "rationale": "The supplied theory remains true and sufficient.",
            },
        ]
    }


def test_repair_router_overrides_free_scope_with_artifact_bound_ownership() -> None:
    backend = _Backend(_routing_payload())
    semantic_review = _semantic_review_packet()
    theory_packet = {
        "packet_id": "theory_derivation:generic",
        "theory_derivation_packet": {"equation_chain": [{"step_id": "E1"}]},
    }
    packet = LLMArchitectMetricRepairOwnershipRouterAgent(
        provider=backend,
        config=ArchitectMetricRepairOwnershipRouterConfig(
            provider_name="anthropic",
            model="claude-opus-4-8",
            max_repair_attempts=0,
        ),
    ).route(
        question=OpenResearchQuestion(
            id="q_repair_owner",
            title="Route generic protocol repairs",
            description="Separate source-theory repair from metric encoding repair.",
        ),
        review_material={
            "theory_developer_protocol_material": {
                "source_theory_packet_id": "theory_derivation:generic",
                "source_theory_packet_hash": stable_hash(theory_packet),
                "theory_semantic_material": theory_packet,
                "execution_results_available": False,
            },
            "empirical_metric_requirements": [
                {"requirement_id": "generic:metric"}
            ],
        },
        semantic_review_packet=semantic_review,
        trusted_lineage={
            "authoring_packet_id": "metric_authoring:generic",
            "authoring_packet_hash": stable_hash({"candidate": "generic"}),
            "source_theory_packet_id": "theory_derivation:generic",
            "source_theory_packet_hash": stable_hash(theory_packet),
        },
    )

    assert packet["recommended_repair_scope"] == "upstream_theory"
    assert [
        row["derived_repair_scope"] for row in packet["decisions"]
    ] == ["upstream_theory", "metric_contract"]
    assert validate_architect_metric_repair_ownership_packet(packet) == []
    routed = apply_architect_metric_repair_ownership_routes(
        findings=semantic_review["findings"],
        ownership_packet=packet,
    )
    assert routed[0]["semantic_reviewer_repair_scope"] == "metric_contract"
    assert routed[0]["repair_scope"] == "upstream_theory"
    assert routed[1]["repair_scope"] == "metric_contract"
    assert backend.requests[0].metadata["subsystem"] == (
        "ArchitectMetricRepairOwnershipRouter"
    )
    assert backend.requests[0].metadata["model_tier"] == "opus"
    assert "Do not repeat the reviewer's repair_scope" in (
        backend.requests[0].user_prompt
    )
    assert "routing prescription" in backend.requests[0].user_prompt
    assert '"repair_scope":"metric_contract"' not in (
        backend.requests[0].user_prompt
    )
    assert "Keep every change inside the metric contract" not in (
        backend.requests[0].user_prompt
    )


def test_repair_router_unresolved_decision_fails_closed() -> None:
    decision = {
        "required_artifact_changes": [
            {
                "artifact_role": "metric_protocol_candidate",
                "change_summary": "A candidate change may be needed.",
            }
        ],
        "metric_author_can_repair_without_revising_source_theory": True,
        "ownership_certainty": "unresolved",
    }

    assert architect_metric_repair_scope_from_decision(decision) == "unresolved"


def test_repair_router_does_not_compensate_for_contradictory_targets() -> None:
    decision = {
        "required_artifact_changes": [
            {
                "artifact_role": "metric_protocol_candidate",
                "change_summary": "Only the candidate is named.",
            }
        ],
        "metric_author_can_repair_without_revising_source_theory": False,
        "ownership_certainty": "resolved",
    }

    assert architect_metric_repair_scope_from_decision(decision) == "unresolved"


def test_repair_ownership_schema_transforms_for_anthropic() -> None:
    anthropic = pytest.importorskip("anthropic")

    transformed = anthropic.transform_schema(
        ARCHITECT_METRIC_REPAIR_OWNERSHIP_JSON_SCHEMA
    )

    assert transformed["type"] == "object"
    decision = transformed["properties"]["decisions"]["items"]
    assert decision["properties"]["finding_index"]["type"] == "integer"

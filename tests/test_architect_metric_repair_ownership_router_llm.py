from __future__ import annotations

import json

import pytest

from ai_statistician.architect_metric_repair_ownership_router_llm import (
    ARCHITECT_GENERATED_CODE_REPAIR_SCOPE_UPSTREAM_DEPENDENCY,
    ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION,
    ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION,
    ARCHITECT_METRIC_REPAIR_OWNERSHIP_JSON_SCHEMA,
    ArchitectMetricRepairOwnershipRouterConfig,
    LLMArchitectMetricRepairOwnershipRouterAgent,
    _normalize_architect_metric_repair_ownership_packet,
    _postexecution_artifact_target_eligibility,
    _postexecution_router_dimension_projection,
    apply_architect_metric_repair_ownership_routes,
    apply_generated_code_repair_ownership_routes,
    architect_metric_repair_scope_from_decision,
    generated_code_recommended_scope_from_ownership_decisions,
    generated_code_repair_scope_from_ownership_decision,
    validate_architect_metric_repair_ownership_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import GeneratorResponse
from ai_statistician.research_schema import OpenResearchQuestion


class _Backend:
    provider_name = "anthropic"

    def __init__(
        self,
        payload: dict[str, object] | list[dict[str, object]],
    ) -> None:
        self.payloads = payload if isinstance(payload, list) else [payload]
        self.requests = []

    def generate(self, request):
        payload = self.payloads[min(len(self.requests), len(self.payloads) - 1)]
        self.requests.append(request)
        return GeneratorResponse(
            text=json.dumps(payload),
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
                    },
                    {
                        "artifact_role": "metric_protocol_candidate",
                    },
                ],
                "source_theory_can_remain_unchanged": False,
                "ownership_certainty": "resolved",
                "rationale": "The source equation itself cannot remain unchanged.",
            },
            {
                "finding_index": 1,
                "required_artifact_changes": [
                    {
                        "artifact_role": "metric_protocol_candidate",
                    }
                ],
                "source_theory_can_remain_unchanged": True,
                "ownership_certainty": "resolved",
                "rationale": "The supplied theory remains true and sufficient.",
            },
        ]
    }


def test_postexecution_router_dimension_projection_omits_review_narrative() -> None:
    projection = _postexecution_router_dimension_projection(
        [
            {
                "dimension": "metric_semantics_alignment",
                "status": "FAIL",
                "rationale": "oversized-review-rationale-marker",
                "artifact_citations": ["generated_source_artifact"],
                "evidence_refs": ["generated_source_artifact#/exact_result"],
            }
        ]
    )

    assert projection == [
        {
            "dimension": "metric_semantics_alignment",
            "status": "FAIL",
        }
    ]


def _route(
    backend: _Backend,
    *,
    max_repair_attempts: int = 0,
) -> dict[str, object]:
    theory_packet = {
        "packet_id": "theory_derivation:generic",
        "theory_derivation_packet": {"equation_chain": [{"step_id": "E1"}]},
    }
    return LLMArchitectMetricRepairOwnershipRouterAgent(
        provider=backend,
        config=ArchitectMetricRepairOwnershipRouterConfig(
            provider_name="anthropic",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_repair_attempts=max_repair_attempts,
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
        semantic_review_packet=_semantic_review_packet(),
        trusted_lineage={
            "authoring_packet_id": "metric_authoring:generic",
            "authoring_packet_hash": stable_hash({"candidate": "generic"}),
            "source_theory_packet_id": "theory_derivation:generic",
            "source_theory_packet_hash": stable_hash(theory_packet),
        },
    )


def test_repair_router_overrides_free_scope_with_artifact_bound_ownership() -> None:
    backend = _Backend(_routing_payload())
    semantic_review = _semantic_review_packet()
    packet = _route(backend)

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
    assert backend.requests[0].metadata["model_tier"] == "haiku"
    assert backend.requests[0].metadata["user_prompt_chars"] == len(
        backend.requests[0].user_prompt
    )
    assert backend.requests[0].metadata["routing_material_json_chars"] > 0
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
    assert '"reviewed_finding_count":2' in backend.requests[0].user_prompt
    assert '"required_finding_indices":[0,1]' in backend.requests[0].user_prompt


def test_repair_router_derives_redundant_preservation_flag_without_retry() -> None:
    contradictory = _routing_payload()
    first_decision = contradictory["decisions"][0]
    first_decision["required_artifact_changes"] = [
        {
            "artifact_role": "metric_protocol_candidate",
        }
    ]
    first_decision["source_theory_can_remain_unchanged"] = False
    backend = _Backend([contradictory, _routing_payload()])

    packet = _route(backend, max_repair_attempts=1)

    assert len(backend.requests) == 1
    assert packet["recommended_repair_scope"] == "metric_contract"
    assert packet["decisions"][0]["source_theory_can_remain_unchanged"] is True
    decision_schema = backend.requests[0].schema["properties"]["decisions"]["items"]
    assert "source_theory_can_remain_unchanged" not in (
        decision_schema["properties"]
    )


def test_repair_router_exhaustion_returns_typed_unresolved_packet() -> None:
    incomplete = _routing_payload()
    incomplete["decisions"] = incomplete["decisions"][:1]
    backend = _Backend(incomplete)

    packet = _route(backend, max_repair_attempts=1)

    assert len(backend.requests) == 2
    assert packet["ok"] is False
    assert packet["fallback_reason"] == (
        "bounded_router_packet_validation_exhausted"
    )
    assert packet["recommended_repair_scope"] == "unresolved"
    assert [row["finding_index"] for row in packet["decisions"]] == [0, 1]
    assert all(
        row["ownership_certainty"] == "unresolved"
        and row["required_artifact_changes"] == []
        for row in packet["decisions"]
    )
    assert validate_architect_metric_repair_ownership_packet(packet) == []


def test_repair_router_unresolved_decision_fails_closed() -> None:
    decision = {
        "required_artifact_changes": [
            {
                "artifact_role": "metric_protocol_candidate",
            }
        ],
        "source_theory_can_remain_unchanged": True,
        "ownership_certainty": "unresolved",
    }

    assert architect_metric_repair_scope_from_decision(decision) == "unresolved"


def test_repair_router_does_not_compensate_for_contradictory_targets() -> None:
    decision = {
        "required_artifact_changes": [
            {
                "artifact_role": "metric_protocol_candidate",
            }
        ],
        "source_theory_can_remain_unchanged": False,
        "ownership_certainty": "resolved",
    }

    assert architect_metric_repair_scope_from_decision(decision) == "unresolved"

    packet = {
        "proof_evidence_status": (
            "ARCHITECT_METRIC_REPAIR_OWNERSHIP_NOT_PROOF_EVIDENCE"
        ),
        "routing_phase": ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION,
        "execution_results_observed": False,
        "frozen_protocol_immutable_after_execution": False,
        "question_id": "q_contradictory_owner",
        "authoring_packet_id": "metric-authoring:contradictory",
        "authoring_packet_hash": "authoring-hash",
        "semantic_review_packet_id": "metric-review:contradictory",
        "semantic_review_packet_hash": "review-hash",
        "source_theory_packet_id": "theory:contradictory",
        "source_theory_packet_hash": "theory-hash",
        "routing_input_fingerprint": "routing-hash",
        "reviewed_finding_count": 1,
        "decisions": [
            {
                "finding_index": 0,
                **decision,
                "derived_repair_scope": "unresolved",
                "rationale": "The fields disagree about who can repair it.",
            }
        ],
        "recommended_repair_scope": "unresolved",
    }
    assert any(
        "source-theory preservation flag"
        in error
        for error in validate_architect_metric_repair_ownership_packet(packet)
    )


def test_postexecution_router_replaces_result_driven_reviewer_instruction() -> None:
    backend = _Backend(
        [
            {
                "decisions": [
                    {
                        "finding_index": 0,
                        "required_artifact_changes": [
                            {"artifact_role": "source_theory_packet"}
                        ],
                        "source_theory_can_remain_unchanged": False,
                        "ownership_certainty": "resolved",
                        "rationale": "This first target lacks artifact evidence.",
                    }
                ]
            },
            {
                "decisions": [
                    {
                        "finding_index": 0,
                        "required_artifact_changes": [
                            {
                                "artifact_role": "generated_source_artifact",
                            }
                        ],
                        "source_theory_can_remain_unchanged": True,
                        "ownership_certainty": "resolved",
                        "rationale": (
                            "The protocol and theory are coherent; exact source "
                            "behavior does not implement the required measurement."
                        ),
                    }
                ]
            },
        ]
    )
    semantic_review = {
        "packet_id": "generated-review:post-result",
        "reviewed_source_assessment": "SOURCE_REPAIR_REQUIRED",
        "frozen_metric_contract_assessment": "VALID_AND_FEASIBLE",
        "source_theory_assessment": "SUFFICIENT_FOR_IMPLEMENTATION_REPAIR",
        "dimension_reviews": [],
        "findings": [
            {
                "severity": "high",
                "category": "failed gate",
                "summary": "The observed metric missed the frozen threshold.",
                "required_change": "Relax the threshold after observing the result.",
                "repair_scope": "upstream_metric_contract",
                "evidence_refs": ["result:metric_gate"],
            },
            {
                "severity": "low",
                "category": "advisory note",
                "summary": "A diagnostic could be logged in a later cleanup.",
                "required_change": "Optionally add one diagnostic field.",
                "repair_scope": "none",
                "evidence_refs": ["result:diagnostic"],
            },
        ],
    }
    router = LLMArchitectMetricRepairOwnershipRouterAgent(
        provider=backend,
        config=ArchitectMetricRepairOwnershipRouterConfig(
            provider_name="anthropic",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_repair_attempts=1,
        ),
    )

    packet = router.route_generated_code_review(
        question=OpenResearchQuestion(
            id="q_post_result_owner",
            title="Route a post-result source defect",
            description="Keep a frozen evaluation protocol immutable.",
        ),
        review_material={
            "theory_packet": {"packet_id": "theory:post-result"},
            "architect_frozen_evidence_contract": {
                "empirical_metric_requirements": [{"requirement_id": "gate:1"}]
            },
            "coding_agent_proposal_packet": {"packet_id": "code:proposal"},
            "source_responsibility_contract": {
                "assigned_requirement_ids": ["gate:1"],
                "assigned_empirical_metric_requirements": [
                    {
                        "requirement_id": "gate:1",
                        "measurement_protocol": (
                            "duplicated-owner-contract-marker"
                        ),
                    }
                ],
            },
            "exact_executed_artifacts": [
                {
                    "artifact_id": "code:exact",
                    "exact_source_code": "def estimate(): return 1.0",
                    "exact_result": {
                        "summary": {"metric": 0.5},
                        "cells": [{"large_replicate_payload": "omit-me"}],
                    },
                    "source_row": {
                        "metric_contracts": [
                            {
                                "contract_id": "MC:gate:1",
                                "requirement_id": "gate:1",
                                "operator": "<=",
                                "threshold": 0.5,
                                "tolerance": 0.1,
                                "required": True,
                            }
                        ],
                        "metric_contract_evaluation": {
                            "evaluations": [
                                {
                                    "contract_id": "MC:gate:1",
                                    "requirement_id": "gate:1",
                                    "artifact_id": "code:exact",
                                    "metric_path": ["metric"],
                                    "operator": "<=",
                                    "aggregate_value": 0.5,
                                    "required": True,
                                    "passed": True,
                                    "errors": [],
                                }
                            ]
                        },
                    },
                }
            ],
        },
        semantic_review_packet=semantic_review,
        trusted_lineage={
            "work_order_id": "work-order:post-result",
            "work_order_hash": "work-order-hash",
            "source_manifest_id": "source-manifest:post-result",
            "source_manifest_hash": "source-manifest-hash",
            "theory_packet_id": "theory:post-result",
            "theory_packet_hash": "theory-hash",
        },
    )

    assert packet["execution_results_observed"] is True
    assert packet["llm_json_repair_attempts"] == 1
    assert packet["frozen_protocol_immutable_after_execution"] is True
    assert packet["reviewed_finding_count"] == 1
    assert packet["recommended_repair_scope"] == "source_code"
    assert packet["artifact_target_eligibility"] == [
        {
            "finding_index": 0,
            "eligible_artifact_roles": ["generated_source_artifact"],
            "basis": (
                "A post-execution target is eligible only when the finding "
                "cites that artifact. A frozen metric protocol is eligible "
                "only from outcome-independent protocol evidence."
            ),
            "expanded_review_dimensions": [],
        }
    ]
    assert validate_architect_metric_repair_ownership_packet(packet) == []
    routed = apply_generated_code_repair_ownership_routes(
        findings=semantic_review["findings"],
        ownership_packet=packet,
    )
    assert routed[0]["semantic_reviewer_repair_scope"] == (
        "upstream_metric_contract"
    )
    assert routed[0]["repair_scope"] == "source_code"
    assert "Relax the threshold" in routed[0][
        "semantic_reviewer_required_change"
    ]
    assert "Reinspect generated_source_artifact" in routed[0][
        "required_change"
    ]
    assert "Relax the threshold" not in routed[0]["required_change"]
    assert routed[1]["repair_scope"] == "none"
    assert routed[1]["required_change"] == "Optionally add one diagnostic field."
    assert "Relax the threshold" not in backend.requests[0].user_prompt
    assert "failed gate" in backend.requests[0].user_prompt
    assert "advisory note" not in backend.requests[0].user_prompt
    assert "omit-me" not in backend.requests[0].user_prompt
    assert "duplicated-owner-contract-marker" not in (
        backend.requests[0].user_prompt
    )
    assert "def estimate(): return 1.0" not in backend.requests[0].user_prompt
    assert '"metric":0.5' in backend.requests[0].user_prompt
    assert "not by itself a protocol defect" in backend.requests[0].user_prompt
    assert "runtime_metric_gate_projection" in backend.requests[0].user_prompt
    assert '"contract_id":"MC:gate:1"' in backend.requests[0].user_prompt
    assert '"passed":true' in backend.requests[0].user_prompt
    assert "do not call that numeric gate failed" in (
        backend.requests[0].user_prompt
    )
    assert "downstream-repair counterfactual" in backend.requests[0].user_prompt
    assert "Finite-precision arithmetic" in backend.requests[0].user_prompt
    assert "missing non-required diagnostic" in backend.requests[0].user_prompt
    assert "one bounded generated-source repair" in backend.requests[0].user_prompt
    assert "separate findings require a concrete" in backend.requests[0].user_prompt
    assert "independently re-review the generated source" in (
        backend.requests[0].user_prompt
    )
    assert "semantic_review_artifact_assessments" in (
        backend.requests[0].user_prompt
    )
    assert "SUFFICIENT_FOR_IMPLEMENTATION_REPAIR" in (
        backend.requests[0].user_prompt
    )
    assert "artifact_target_eligibility" in backend.requests[1].user_prompt
    assert "runtime_metric_gate_projection" in backend.requests[1].user_prompt
    assert '"eligible_artifact_roles"' in (
        backend.requests[1].user_prompt
    )
    assert '"generated_source_artifact"' in (
        backend.requests[1].user_prompt
    )
    assert "targets an artifact not supported by its typed artifact citations" in (
        backend.requests[1].user_prompt
    )

    forged = json.loads(json.dumps(packet))
    forged["decisions"][0]["required_artifact_changes"] = [
        {"artifact_role": "metric_protocol_candidate"}
    ]
    forged["decisions"][0]["derived_repair_scope"] = (
        "upstream_metric_contract"
    )
    forged["recommended_repair_scope"] = "upstream_metric_contract"
    assert any(
        "not supported by its typed artifact citations" in error
        for error in validate_architect_metric_repair_ownership_packet(forged)
    )


def test_postexecution_eligibility_uses_typed_artifact_citations() -> None:
    eligibility = _postexecution_artifact_target_eligibility(
        [
            {
                "evidence_refs": [
                    "eprocess_test_statistic capping logic and returned mean"
                ],
                "artifact_citations": ["generated_source_artifact"],
            }
        ],
        semantic_review_dimensions=[
            {
                "dimension": "experiment_non_vacuity_and_identifiability",
                "evidence_refs": [
                    "exact_executed_artifacts[0]/exact_source_code"
                ],
                "artifact_citations": ["generated_source_artifact"],
            }
        ],
    )

    assert eligibility[0]["eligible_artifact_roles"] == [
        "generated_source_artifact"
    ]
    assert eligibility[0]["expanded_review_dimensions"] == []


def test_postexecution_dependency_citation_routes_only_dependency_owner() -> None:
    eligibility = _postexecution_artifact_target_eligibility(
        [
            {
                "evidence_refs": [
                    (
                        "upstream_generated_dependency#"
                        "/exact_dependency_artifacts/0/exact_source_code"
                    )
                ],
                "artifact_citations": ["upstream_generated_dependency"],
            }
        ],
        semantic_review_dimensions=[],
    )
    decision = {
        "finding_index": 0,
        "required_artifact_changes": [
            {"artifact_role": "upstream_generated_dependency"}
        ],
        "source_theory_can_remain_unchanged": True,
        "ownership_certainty": "resolved",
        "rationale": (
            "The current consumer invokes immutable upstream code containing the "
            "cited implementation defect."
        ),
    }

    assert eligibility[0]["eligible_artifact_roles"] == [
        "upstream_generated_dependency"
    ]
    assert generated_code_repair_scope_from_ownership_decision(decision) == (
        ARCHITECT_GENERATED_CODE_REPAIR_SCOPE_UPSTREAM_DEPENDENCY
    )
    assert generated_code_recommended_scope_from_ownership_decisions(
        [decision]
    ) == ARCHITECT_GENERATED_CODE_REPAIR_SCOPE_UPSTREAM_DEPENDENCY

    routed = apply_generated_code_repair_ownership_routes(
        findings=[
            {
                "severity": "high",
                "category": "dependency implementation mismatch",
                "summary": "The injected estimator computes a different quantity.",
                "required_change": "Do not compensate inside the simulation.",
                "repair_scope": "source_code",
            }
        ],
        ownership_packet={
            "packet_id": "metric_repair_ownership:dependency",
            "decisions": [decision],
        },
    )
    assert routed[0]["repair_scope"] == (
        ARCHITECT_GENERATED_CODE_REPAIR_SCOPE_UPSTREAM_DEPENDENCY
    )
    assert routed[0]["deferred_repair_target_artifacts"] == []
    assert "Reinspect upstream_generated_dependency" in routed[0][
        "required_change"
    ]
    assert "simulation" not in routed[0]["required_change"].lower()


def test_postexecution_ambiguous_dependency_owner_remains_unresolved() -> None:
    packet = _normalize_architect_metric_repair_ownership_packet(
        {
            "decisions": [
                {
                    "finding_index": 0,
                    "required_artifact_changes": [
                        {"artifact_role": "upstream_generated_dependency"},
                        {"artifact_role": "generated_source_artifact"},
                    ],
                    "ownership_certainty": "unresolved",
                    "rationale": (
                        "The available diagnostic cannot isolate the immutable "
                        "dependency from its current consumer."
                    ),
                }
            ]
        },
        question=OpenResearchQuestion(
            id="q_ambiguous_dependency_owner",
            title="Preserve unresolved dependency ownership",
            description="Require fresh diagnostics before choosing a code owner.",
        ),
        routing_phase=ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION,
        routing_material={
            "semantic_review_findings": [{"finding_index": 0}],
            "artifact_target_eligibility": [
                {
                    "finding_index": 0,
                    "eligible_artifact_roles": [
                        "upstream_generated_dependency",
                        "generated_source_artifact",
                    ],
                }
            ],
        },
        semantic_review_packet={"packet_id": "review:ambiguous-dependency"},
        trusted_lineage={
            "work_order_id": "work-order:ambiguous-dependency",
            "work_order_hash": "work-order-hash",
            "source_manifest_id": "simulation:ambiguous-dependency",
            "source_manifest_hash": "simulation-hash",
            "theory_packet_id": "theory:ambiguous-dependency",
            "theory_packet_hash": "theory-hash",
        },
        model="claude-haiku-4-5-20251001",
        model_tier="haiku",
        provider_name="anthropic",
        raw_response="{}",
    )

    assert packet["decisions"][0]["ownership_certainty"] == "unresolved"
    assert packet["decisions"][0]["required_artifact_changes"] == []
    assert packet["decisions"][0]["derived_repair_scope"] == "unresolved"
    assert packet["recommended_repair_scope"] == "unresolved"
    assert validate_architect_metric_repair_ownership_packet(packet) == []


def test_postexecution_metric_protocol_requires_outcome_independent_evidence() -> None:
    eligibility = _postexecution_artifact_target_eligibility(
        [
            {
                "evidence_refs": [
                    "metric_protocol_candidate#/requirements/0/threshold",
                    "generated_source_artifact#/exact_result/power",
                ],
                "artifact_citations": [
                    "metric_protocol_candidate",
                    "generated_source_artifact",
                ],
            },
            {
                "evidence_refs": [
                    "metric_protocol_candidate#/requirements/0/aggregation",
                ],
                "artifact_citations": ["metric_protocol_candidate"],
            },
            {
                "evidence_refs": [
                    "EST2 exact_result: observed power missed a preferred target",
                ],
                "artifact_citations": ["metric_protocol_candidate"],
            },
        ],
        semantic_review_dimensions=[],
    )

    assert eligibility[0]["eligible_artifact_roles"] == [
        "generated_source_artifact"
    ]
    assert eligibility[1]["eligible_artifact_roles"] == [
        "metric_protocol_candidate"
    ]
    assert eligibility[2]["eligible_artifact_roles"] == []


def test_postexecution_advisory_disposition_does_not_block_concrete_repair() -> None:
    source_repair = {
        "finding_index": 0,
        "required_artifact_changes": [
            {"artifact_role": "generated_source_artifact"}
        ],
        "source_theory_can_remain_unchanged": True,
        "ownership_certainty": "resolved",
        "rationale": "The generated measurement path must change.",
    }
    advisory = {
        "finding_index": 1,
        "required_artifact_changes": [],
        "source_theory_can_remain_unchanged": True,
        "ownership_certainty": "resolved_no_change",
        "rationale": "The observation is advisory and identifies no artifact defect.",
    }

    assert generated_code_repair_scope_from_ownership_decision(advisory) == "none"
    assert generated_code_recommended_scope_from_ownership_decisions(
        [source_repair, advisory]
    ) == "source_code"
    assert generated_code_recommended_scope_from_ownership_decisions(
        [advisory]
    ) == "unresolved"

    routed = apply_generated_code_repair_ownership_routes(
        findings=[
            {
                "severity": "high",
                "category": "implementation mismatch",
                "summary": "The generated metric path is wrong.",
                "required_change": "Repair the source.",
                "repair_scope": "source_code",
            },
            {
                "severity": "medium",
                "category": "finite sample observation",
                "summary": "A finite sample diagnostic is noisy.",
                "required_change": "Consider documenting the observation.",
                "repair_scope": "source_code",
            },
        ],
        ownership_packet={
            "packet_id": "metric_repair_ownership:mixed",
            "decisions": [source_repair, advisory],
        },
    )

    assert routed[0]["repair_scope"] == "source_code"
    assert routed[1]["repair_scope"] == "none"
    assert "No artifact change is authorized" in routed[1]["required_change"]


def test_postexecution_router_canonicalizes_targeted_no_change_as_repair() -> None:
    backend = _Backend(
        {
            "decisions": [
                {
                    "finding_index": 0,
                    "required_artifact_changes": [
                        {"artifact_role": "generated_source_artifact"}
                    ],
                    "source_theory_can_remain_unchanged": False,
                    "ownership_certainty": "resolved_no_change",
                    "rationale": (
                        "The cited generated source must change and theory remains "
                        "sufficient."
                    ),
                }
            ]
        }
    )
    router = LLMArchitectMetricRepairOwnershipRouterAgent(
        provider=backend,
        config=ArchitectMetricRepairOwnershipRouterConfig(
            provider_name="anthropic",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_repair_attempts=1,
        ),
    )

    packet = router.route_generated_code_review(
        question=OpenResearchQuestion(
            id="q_targeted_no_change",
            title="Canonicalize a targeted repair",
            description="Route an implementation defect from typed evidence.",
        ),
        review_material={
            "theory_packet": {"packet_id": "theory:targeted-no-change"},
            "architect_frozen_evidence_contract": {
                "empirical_metric_requirements": [{"requirement_id": "gate:1"}]
            },
            "coding_agent_proposal_packet": {"packet_id": "code:proposal"},
            "source_responsibility_contract": {"assigned_requirement_ids": []},
            "exact_executed_artifacts": [
                {
                    "artifact_id": "code:exact",
                    "exact_source_code": "def estimate(): return 1.0",
                    "exact_result": {"summary": {"metric": 1.0}},
                }
            ],
        },
        semantic_review_packet={
            "packet_id": "generated-review:targeted-no-change",
            "dimension_reviews": [],
            "findings": [
                {
                    "severity": "high",
                    "category": "implementation mismatch",
                    "summary": "The generated measurement path is incorrect.",
                    "required_change": "Repair the generated source.",
                    "repair_scope": "source_code",
                    "evidence_refs": [
                        "generated_source_artifact#/exact_source_code"
                    ],
                    "artifact_citations": ["generated_source_artifact"],
                }
            ],
        },
        trusted_lineage={
            "work_order_id": "work-order:targeted-no-change",
            "work_order_hash": "work-order-hash",
            "source_manifest_id": "source-manifest:targeted-no-change",
            "source_manifest_hash": "source-manifest-hash",
            "theory_packet_id": "theory:targeted-no-change",
            "theory_packet_hash": "theory-hash",
        },
    )

    assert len(backend.requests) == 1
    assert packet["recommended_repair_scope"] == "source_code"
    assert packet["decisions"][0]["ownership_certainty"] == "resolved"
    assert packet["decisions"][0][
        "model_requested_ownership_certainty"
    ] == "resolved_no_change"
    assert packet["decisions"][0]["source_theory_can_remain_unchanged"] is True
    assert validate_architect_metric_repair_ownership_packet(packet) == []


def test_postexecution_advisory_disposition_packet_is_typed_and_fail_closed() -> None:
    packet = {
        "schema_version": 4,
        "proof_evidence_status": (
            "ARCHITECT_METRIC_REPAIR_OWNERSHIP_NOT_PROOF_EVIDENCE"
        ),
        "routing_phase": ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION,
        "execution_results_observed": True,
        "frozen_protocol_immutable_after_execution": True,
        "question_id": "q_advisory_owner",
        "semantic_review_packet_id": "review:advisory",
        "semantic_review_packet_hash": "review-hash",
        "source_theory_packet_id": "theory:advisory",
        "source_theory_packet_hash": "theory-hash",
        "work_order_id": "work-order:advisory",
        "work_order_hash": "work-order-hash",
        "source_manifest_id": "source-manifest:advisory",
        "source_manifest_hash": "source-manifest-hash",
        "routing_input_fingerprint": "routing-hash",
        "reviewed_finding_count": 1,
        "artifact_target_eligibility": [
            {
                "finding_index": 0,
                "eligible_artifact_roles": [],
                "basis": "The observation identifies no artifact defect.",
                "expanded_review_dimensions": [],
            }
        ],
        "decisions": [
            {
                "finding_index": 0,
                "required_artifact_changes": [],
                "source_theory_can_remain_unchanged": True,
                "ownership_certainty": "resolved_no_change",
                "rationale": "This is advisory and requires no artifact change.",
                "derived_repair_scope": "none",
            }
        ],
        "recommended_repair_scope": "unresolved",
    }

    assert validate_architect_metric_repair_ownership_packet(packet) == []

    preexecution = json.loads(json.dumps(packet))
    preexecution["routing_phase"] = (
        ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION
    )
    preexecution["execution_results_observed"] = False
    preexecution["frozen_protocol_immutable_after_execution"] = False
    preexecution["authoring_packet_id"] = "authoring:advisory"
    preexecution["authoring_packet_hash"] = "authoring-hash"
    assert any(
        "invalid certainty" in error
        for error in validate_architect_metric_repair_ownership_packet(
            preexecution
        )
    )


def test_postexecution_eligibility_replays_legacy_dimension_evidence() -> None:
    eligibility = _postexecution_artifact_target_eligibility(
        [
            {
                "evidence_refs": [
                    "experiment_non_vacuity_and_identifiability: diagnostic absent"
                ]
            }
        ],
        semantic_review_dimensions=[
            {
                "dimension": "experiment_non_vacuity_and_identifiability",
                "evidence_refs": [
                    "exact_executed_artifacts[0]/exact_source_code"
                ],
            }
        ],
    )

    assert eligibility[0]["eligible_artifact_roles"] == [
        "generated_source_artifact"
    ]
    assert eligibility[0]["expanded_review_dimensions"] == [
        "experiment_non_vacuity_and_identifiability"
    ]


def test_coupled_postexecution_source_and_theory_defect_repairs_source_first() -> None:
    decision = {
        "finding_index": 0,
        "required_artifact_changes": [
            {"artifact_role": "generated_source_artifact"},
            {"artifact_role": "source_theory_packet"},
        ],
        "source_theory_can_remain_unchanged": False,
        "ownership_certainty": "resolved",
        "rationale": (
            "The observed symptom supports a concrete source defect and an upstream "
            "hypothesis that must be reassessed after source repair."
        ),
    }

    assert generated_code_repair_scope_from_ownership_decision(decision) == (
        "source_code"
    )
    assert generated_code_recommended_scope_from_ownership_decisions(
        [decision]
    ) == "source_code"
    routed = apply_generated_code_repair_ownership_routes(
        findings=[
            {
                "severity": "high",
                "category": "generic execution mismatch",
                "summary": "The exact execution disagrees with its declared model.",
                "required_change": "Recheck the implementation and theory.",
                "repair_scope": "upstream_theory",
                "evidence_refs": ["theory_packet", "exact_source_code"],
            }
        ],
        ownership_packet={
            "packet_id": "metric_repair_ownership:coupled",
            "decisions": [decision],
        },
    )

    assert routed[0]["repair_scope"] == "source_code"
    assert routed[0]["repair_target_artifacts"] == [
        {"artifact_role": "generated_source_artifact"},
        {"artifact_role": "source_theory_packet"},
    ]
    assert routed[0]["deferred_repair_target_artifacts"] == [
        {"artifact_role": "source_theory_packet"}
    ]
    assert "Reinspect generated_source_artifact" in routed[0]["required_change"]
    assert "source_theory_packet" not in routed[0]["required_change"]


def test_separate_postexecution_source_and_theory_findings_repair_source_first() -> None:
    source_repair = {
        "finding_index": 0,
        "required_artifact_changes": [
            {"artifact_role": "generated_source_artifact"}
        ],
        "source_theory_can_remain_unchanged": True,
        "ownership_certainty": "resolved",
        "rationale": "The generated measurement path must change.",
    }
    theory_repair = {
        "finding_index": 1,
        "required_artifact_changes": [{"artifact_role": "source_theory_packet"}],
        "source_theory_can_remain_unchanged": False,
        "ownership_certainty": "resolved",
        "rationale": "A distinct mathematical premise must be reassessed.",
    }

    assert generated_code_recommended_scope_from_ownership_decisions(
        [source_repair, theory_repair]
    ) == "source_code"


def test_repair_ownership_schema_transforms_for_anthropic() -> None:
    anthropic = pytest.importorskip("anthropic")

    transformed = anthropic.transform_schema(
        ARCHITECT_METRIC_REPAIR_OWNERSHIP_JSON_SCHEMA
    )

    assert transformed["type"] == "object"
    decision = transformed["properties"]["decisions"]["items"]
    assert decision["properties"]["finding_index"]["type"] == "integer"
    assert "source_theory_can_remain_unchanged" not in decision["properties"]

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.algorithm_engineer_llm import build_algorithm_engineer_prompt
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_reviewer_llm import (
    GENERATED_CODE_SEMANTIC_REVIEW_ARTIFACT_CITATIONS,
    GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS,
    GENERATED_CODE_SEMANTIC_REVIEW_FINDING_SEVERITIES,
    GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA,
    GeneratedCodeSemanticReviewerConfig,
    LLMGeneratedCodeSemanticReviewerAgent,
    build_generated_code_semantic_review_prompt,
    generated_code_semantic_review_active_pending_repair_plan,
    generated_code_semantic_review_authority_contract,
    generated_code_semantic_review_json_schema,
    generated_code_semantic_review_pending_plan_errors,
    generated_code_semantic_review_prompt_projection,
    generated_code_semantic_review_repair_scope,
    generated_code_semantic_review_repair_scopes,
    validate_generated_code_semantic_review_packet,
    _generated_code_semantic_review_finding_budget,
    _generated_code_semantic_review_row_cited_values,
    _python_generated_source_interface_inventory,
)
from ai_statistician.generated_code_semantic_review_replan import (
    GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY,
    GENERATED_CODE_SEMANTIC_REVIEW_PENDING_REPAIR_PLAN_KEY,
    GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_LEDGER_KEY,
    advance_generated_code_semantic_review_lineage_budget,
    consume_generated_code_semantic_review_upstream_theory_replan,
    generated_code_dependency_verification_plan_after_repair,
    generated_code_semantic_review_upstream_theory_budget_exhausted_result,
    generated_code_semantic_review_upstream_theory_revision_state,
    record_generated_code_semantic_review_lineage_action,
)
from ai_statistician.generated_code_semantic_review_scope import (
    generated_code_semantic_review_proposal_projection,
    generated_code_semantic_review_theory_projection,
    generated_code_semantic_review_upstream_dependency_projection,
)
from ai_statistician.llm_json_repair import PacketValidationError
from ai_statistician.model_backend import (
    GeneratorRequest,
    GeneratorResponse,
    LIVE_EVALUATION_CLAUDE_MODEL,
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    StaticJSONGeneratorBackend,
)
from ai_statistician.research_agent_runtime import (
    ArchitectCoordinatorRuntimeSubsystem,
    GeneratedCodeSemanticReviewerRuntimeSubsystem,
    ResearchAgentRuntimeConfig,
    _runtime_algorithm_handoff_receipt,
    _runtime_generated_code_authoritative_repair_routing,
    _runtime_generated_code_semantic_review_dispatch,
    _runtime_generated_code_semantic_review_inherited_obligations,
    _runtime_validated_algorithm_handoff,
)
from ai_statistician.research_agent_runtime_audit import (
    _audit_result_path,
    _runtime_capability_scorecard,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.simulation_engineer_llm import (
    build_simulation_engineer_prompt,
)


STATIC_SOURCE_CLAUDE_MODEL = LIVE_EVALUATION_CLAUDE_MODEL


def _question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="semantic-review-test",
        title="Review a generated statistical experiment",
        description="Determine whether the generated experiment measures its claim.",
        tags=("semantic-review",),
    )


def test_large_generated_results_use_hash_bound_prompt_projection() -> None:
    trajectory = [float(index) / 10.0 for index in range(80_000)]
    exact_result = {
        "rejection_rate": 0.05,
        "trajectory": trajectory,
    }
    result_hash = stable_hash(exact_result)
    exact_source = "def run_sandbox(seed, replicates):\n    return {'ok': True}\n"
    review_material = {
        "confirmatory_empirical_evidence_eligible": True,
        "exact_executed_artifacts": [
            {
                "artifact_id": "large-result",
                "source_row": {
                    "result_path": "/tmp/large-result.json",
                    "metrics": exact_result,
                    "runtime_replicates": 80,
                },
                "exact_source_code": exact_source,
                "exact_source_hash": stable_hash(exact_source),
                "exact_result": exact_result,
                "exact_result_hash": result_hash,
                "actual_runtime_arguments": {"seed": 7, "replicates": 80},
            }
        ],
    }

    projection = generated_code_semantic_review_prompt_projection(
        review_material
    )
    projected_artifact = projection["exact_executed_artifacts"][0]
    projected_result = projected_artifact["exact_result"]
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material=review_material,
    )

    assert review_material["exact_executed_artifacts"][0]["exact_result"] is exact_result
    assert projected_artifact["exact_source_code"] == exact_source
    assert "metrics" not in projected_artifact["source_row"]
    projection_metadata = projected_artifact[
        "exact_result_prompt_projection"
    ]
    assert projection_metadata["full_result_in_prompt"] is False
    assert projection_metadata["full_result_hash"] == result_hash
    assert projected_result["trajectory"]["length"] == 80_000
    assert projected_result["trajectory"]["numeric_summary"][
        "count"
    ] == 80_000
    assert "lineage only" in projection_metadata["boundary"]
    assert len(prompt) < 100_000
    assert "def run_sandbox" in prompt
    assert "Do not treat omitted values as inspected" in prompt


def test_semantic_review_prompt_projection_deduplicates_metric_authority() -> None:
    requirement = {
        "requirement_id": "metric:one",
        "measurement_protocol": "canonical-metric-authority-marker",
        "target_subsystems": ["SimulationEngineer"],
    }
    evidence_contract = {
        "empirical_metric_requirements": [requirement],
    }
    runtime_contract = {
        **requirement,
        "artifact_id": "simulation:one",
        "authority_binding_mode": "runtime_joined_frozen_requirement",
        "authority_requirement_fingerprint": stable_hash(requirement),
        "contract_id": "contract:one",
        "metric_path": ["metric"],
    }
    review_material = {
        "architect_frozen_evidence_contract": evidence_contract,
        "source_manifest_summary": {
            "runtime_architect_control": {
                "architect_coordinator_proposal_id": "architect:one",
                "evidence_contract": evidence_contract,
                "formal_verification_policy": "required",
            }
        },
        "source_responsibility_contract": {
            "assigned_requirement_ids": ["metric:one"],
            "assigned_empirical_metric_requirements": [requirement],
        },
        "exact_executed_artifacts": [
            {
                "artifact_id": "simulation:one",
                "exact_source_code": "def run_sandbox(seed, replicates): return {}",
                "exact_source_hash": "source-hash",
                "exact_result": {"metric": 0.5},
                "exact_result_hash": "result-hash",
                "source_row": {
                    "metric_contracts": [runtime_contract],
                    "metric_contract_evaluation": {
                        "evaluations": [
                            {
                                "requirement_id": "metric:one",
                                "aggregate_value": 0.5,
                                "passed": True,
                            }
                        ]
                    },
                },
            }
        ],
    }

    projection = generated_code_semantic_review_prompt_projection(
        review_material
    )
    projected_source_row = projection["exact_executed_artifacts"][0][
        "source_row"
    ]
    projected_responsibility = projection["source_responsibility_contract"]
    projected_control = projection["source_manifest_summary"][
        "runtime_architect_control"
    ]
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material=review_material,
    )

    assert json.dumps(projection).count("canonical-metric-authority-marker") == 1
    assert "metric_contracts" not in projected_source_row
    assert "metric_contract_evaluation" not in projected_source_row
    assert projected_source_row["metric_contract_prompt_refs"] == [
        {
            "artifact_id": "simulation:one",
            "authority_binding_mode": "runtime_joined_frozen_requirement",
            "authority_requirement_fingerprint": stable_hash(requirement),
            "contract_id": "contract:one",
            "metric_path": ["metric"],
            "requirement_id": "metric:one",
        }
    ]
    assert (
        projected_source_row["metric_contract_evaluation_prompt_ref"]
        == "runtime_metric_gate_projection"
    )
    assert "assigned_empirical_metric_requirements" not in (
        projected_responsibility
    )
    assert "evidence_contract" not in projected_control
    assert '"max_new_findings":4' in prompt
    assert '"active_prior_finding_count":0' in prompt
    assert '"prior_continuations_consume_new_finding_budget":false' in prompt
    assert GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA["properties"][
        "findings"
    ]["maxItems"] == 4

    conflicting_material = json.loads(json.dumps(review_material))
    conflicting_material["source_manifest_summary"]["runtime_architect_control"][
        "evidence_contract"
    ] = {"empirical_metric_requirements": []}
    conflicting_material["source_responsibility_contract"][
        "assigned_empirical_metric_requirements"
    ][0]["measurement_protocol"] = "conflicting responsibility"
    conflicting_material["exact_executed_artifacts"][0]["source_row"][
        "metric_contracts"
    ][0]["authority_requirement_fingerprint"] = "forged"
    conflicting_projection = generated_code_semantic_review_prompt_projection(
        conflicting_material
    )

    assert "evidence_contract" in conflicting_projection[
        "source_manifest_summary"
    ]["runtime_architect_control"]
    assert "assigned_empirical_metric_requirements" in conflicting_projection[
        "source_responsibility_contract"
    ]
    assert "metric_contracts" in conflicting_projection[
        "exact_executed_artifacts"
    ][0]["source_row"]


def test_semantic_review_prompt_projection_deduplicates_source_metadata() -> None:
    theory_spec = {
        "id": "estimator:one",
        "algorithm_semantics": "canonical-estimator-semantics-marker",
    }
    proposal_target = {
        "estimator_id": "estimator:one",
        "adapter_strategy": "canonical-adapter-strategy-marker",
    }
    alignment_contract = {
        "artifact_kind": "TheoryTraceAlignmentContract",
        "structured_alignment_observed": False,
    }
    review_material = {
        "theory_packet": {"estimator_specs": [theory_spec]},
        "coding_agent_proposal_packet": {
            "implementation_targets": [proposal_target],
            "theory_trace_alignment_contract": alignment_contract,
        },
        "source_manifest_summary": {
            "llm_algorithm_engineer_theory_trace_alignment_contract": (
                alignment_contract
            )
        },
        "exact_executed_artifacts": [
            {
                "artifact_id": "estimator:one",
                "exact_source_code": "def run_sandbox(seed, replicates): return {}",
                "exact_source_hash": "source-hash",
                "exact_result": {},
                "exact_result_hash": "result-hash",
                "source_row": {
                    "spec": theory_spec,
                    "llm_algorithm_engineer_target": {
                        **proposal_target,
                        "validation_metrics": ["advisory-only-marker"],
                    },
                },
            }
        ],
    }

    projection = generated_code_semantic_review_prompt_projection(
        review_material
    )
    source_row = projection["exact_executed_artifacts"][0]["source_row"]
    source_summary = projection["source_manifest_summary"]
    serialized = json.dumps(projection)

    assert "spec" not in source_row
    assert source_row["spec_prompt_ref"]["locator"] == (
        "/theory_packet/estimator_specs/0"
    )
    assert "llm_algorithm_engineer_target" not in source_row
    target_ref = source_row["llm_algorithm_engineer_target_prompt_ref"]
    assert target_ref["locator"] == (
        "/coding_agent_proposal_packet/implementation_targets/0"
    )
    assert target_ref["excluded_non_authoritative_fields"] == [
        "validation_metrics"
    ]
    assert (
        "llm_algorithm_engineer_theory_trace_alignment_contract"
        not in source_summary
    )
    assert serialized.count("canonical-estimator-semantics-marker") == 1
    assert serialized.count("canonical-adapter-strategy-marker") == 1
    assert "advisory-only-marker" not in serialized


def test_unaligned_theory_review_uses_canonical_semantic_core() -> None:
    theory_packet = {
        "packet_id": "theory:one",
        "problem_card": {"estimand": "canonical-estimand-marker"},
        "theory_derivation_packet": {
            "derivation_steps": [{"id": "step:one", "claim": "A claim."}]
        },
        "estimator_specs": [{"id": "estimator:one"}],
        "runtime_architect_control": {"large": "runtime-control-marker"},
        "llm_json_repair_history": [{"large": "repair-history-marker"}],
        "next_actions": [{"action": "advisory-action-marker"}],
        "critic_findings": [{"finding": "system-review-marker"}],
    }
    alignment_contract = {
        "structured_alignment_observed": False,
        "supported_derivation_steps": ["step:one"],
    }

    projection = generated_code_semantic_review_theory_projection(
        theory_packet=theory_packet,
        proposal_packet={
            "theory_trace_alignment_contract": alignment_contract,
        },
    )
    serialized = json.dumps(projection)

    assert "canonical-estimand-marker" in serialized
    assert projection["theory_derivation_packet"] == theory_packet[
        "theory_derivation_packet"
    ]
    assert "runtime-control-marker" not in serialized
    assert "repair-history-marker" not in serialized
    assert "advisory-action-marker" not in serialized
    assert "system-review-marker" not in serialized
    review_projection = projection["theory_review_projection"]
    assert review_projection["projection_mode"] == (
        "canonical_semantic_core_fallback"
    )
    assert review_projection["canonical_theory_packet_fingerprint"] == (
        stable_hash(theory_packet)
    )


def test_large_integer_projection_does_not_overflow_numeric_summary() -> None:
    exact_result = {"values": [10**1000] * 80}
    projection = generated_code_semantic_review_prompt_projection(
        {
            "exact_executed_artifacts": [
                {
                    "source_row": {"result_path": "/tmp/huge-integers.json"},
                    "exact_result": exact_result,
                    "exact_result_hash": stable_hash(exact_result),
                }
            ]
        }
    )

    values = projection["exact_executed_artifacts"][0]["exact_result"][
        "values"
    ]
    assert values["length"] == 80
    assert "numeric_summary" not in values


def test_legacy_projected_result_locator_resolves_to_canonical_value() -> None:
    review_material = {
        "exact_executed_artifacts": [
            {
                "artifact_id": "simulation:one",
                "exact_result": {"rejection_rate": 0.075},
            }
        ]
    }
    cited = _generated_code_semantic_review_row_cited_values(
        review_material=review_material,
        row={
            "evidence_citations": [
                {
                    "artifact_role": "generated_source_artifact",
                    "locator": (
                        "/exact_executed_artifacts/0/exact_result/"
                        "projection/rejection_rate"
                    ),
                }
            ]
        },
    )

    assert cited == [
        {
            "artifact_role": "generated_source_artifact",
            "locator": (
                "/exact_executed_artifacts/0/exact_result/"
                "projection/rejection_rate"
            ),
            "canonical_locator": (
                "/exact_executed_artifacts/0/exact_result/rejection_rate"
            ),
            "resolved": True,
            "value": 0.075,
        }
    ]


def _model_evidence_citations(
    *,
    evidence_refs: list[str],
    artifact_citations: list[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for evidence_ref in evidence_refs:
        matched_role = next(
            (
                role
                for role in GENERATED_CODE_SEMANTIC_REVIEW_ARTIFACT_CITATIONS
                if evidence_ref.startswith(f"{role}#")
            ),
            artifact_citations[0] if len(artifact_citations) == 1 else "",
        )
        locator = (
            evidence_ref.split("#", 1)[1]
            if "#" in evidence_ref
            else evidence_ref
        )
        rows.append(
            {
                "artifact_role": matched_role,
                "locator": locator,
            }
        )
    return rows


def _review_response(
    *,
    accept: bool,
    repair_scope: str = "source_code",
    finding_evidence_refs: list[str] | None = None,
    finding_artifact_citations: list[str] | None = None,
) -> dict[str, object]:
    rows = [
        {
            "status": "PASS",
            "rationale": f"The exact source and result support {dimension}.",
            "evidence_citations": [
                {
                    "artifact_role": "generated_source_artifact",
                    "locator": "/exact_executed_artifacts/0/exact_source_code",
                }
            ],
        }
        for dimension in GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS
    ]
    findings: list[dict[str, object]] = []
    instructions: list[str] = []
    if not accept:
        rows[-1]["status"] = "FAIL"
        rows[-1]["rationale"] = "The returned metric measures a different quantity."
        resolved_finding_evidence_refs = finding_evidence_refs or {
            "source_code": [
                "generated_source_artifact#/exact_source_code",
                "generated_source_artifact#/exact_result",
            ],
            "upstream_metric_contract": [
                "metric_protocol_candidate#/empirical_metric_requirements"
            ],
            "upstream_theory": [
                "source_theory_packet#/derivation_steps"
            ],
        }[repair_scope]
        resolved_finding_artifact_citations = finding_artifact_citations or [
            {
                "source_code": "generated_source_artifact",
                "upstream_metric_contract": "metric_protocol_candidate",
                "upstream_theory": "source_theory_packet",
            }[repair_scope]
        ]
        current_artifact_role = {
            "source_code": "generated_source_artifact",
            "upstream_metric_contract": "metric_protocol_candidate",
            "upstream_theory": "source_theory_packet",
        }[repair_scope]
        current_artifact_locator = next(
            (
                evidence_ref.split("#", 1)[1]
                for evidence_ref in resolved_finding_evidence_refs
                if evidence_ref.startswith(f"{current_artifact_role}#")
            ),
            "/",
        )
        findings = [
            {
                "severity": "high",
                "category": "metric_semantics",
                "summary": "The metric label and implemented quantity differ.",
                "required_change": "Compute the frozen protocol quantity directly.",
                "repair_scope": repair_scope,
                "prior_finding_id": "",
                "authority_refs": [
                    {
                        "source_code": (
                            "implementation_target:generated-estimator"
                        ),
                        "upstream_metric_contract": (
                            "requirement:frozen:algorithm-error"
                        ),
                        "upstream_theory": (
                            "theory_alignment:"
                            + stable_hash(
                                {
                                    "supported_derivation_steps": [
                                        "theory:test:step:1"
                                    ]
                                }
                            )[:20]
                        ),
                    }[repair_scope]
                ],
                "artifact_delta": {
                    "obligation_ref": {
                        "source_code": (
                            "implementation_target:generated-estimator"
                        ),
                        "upstream_metric_contract": (
                            "requirement:frozen:algorithm-error"
                        ),
                        "upstream_theory": (
                            "theory_alignment:"
                            + stable_hash(
                                {
                                    "supported_derivation_steps": [
                                        "theory:test:step:1"
                                    ]
                                }
                            )[:20]
                        ),
                    }[repair_scope],
                    "obligation_kind": {
                        "source_code": "implementation_target",
                        "upstream_metric_contract": (
                            "assigned_frozen_requirement"
                        ),
                        "upstream_theory": (
                            "proposal_consumed_theory_alignment"
                        ),
                    }[repair_scope],
                    "current_artifact_role": current_artifact_role,
                    "current_artifact_locator": current_artifact_locator,
                    "current_behavior": (
                        "The current artifact computes a different quantity."
                    ),
                    "required_behavior": (
                        "The cited obligation requires the declared quantity."
                    ),
                    "observable_change": (
                        "The returned value follows the cited quantity definition."
                    ),
                    "before_after_semantically_equivalent": False,
                },
                "evidence_citations": [
                    *_model_evidence_citations(
                        evidence_refs=resolved_finding_evidence_refs,
                        artifact_citations=resolved_finding_artifact_citations,
                    ),
                    {
                        "source_code": {
                            "artifact_role": "generated_source_artifact",
                            "locator": (
                                "/coding_agent_proposal_packet/"
                                "implementation_targets/0"
                            ),
                        },
                        "upstream_metric_contract": {
                            "artifact_role": "metric_protocol_candidate",
                            "locator": "/empirical_metric_requirements/0",
                        },
                        "upstream_theory": {
                            "artifact_role": "source_theory_packet",
                            "locator": "/derivation_steps",
                        },
                    }[repair_scope],
                ],
            }
        ]
        instructions = ["Regenerate code that computes the frozen protocol quantity."]
    source_assessment = (
        "ALIGNED"
        if accept or repair_scope != "source_code"
        else "SOURCE_REPAIR_REQUIRED"
    )
    metric_contract_assessment = (
        "INVALID_OR_INFEASIBLE"
        if not accept and repair_scope == "upstream_metric_contract"
        else "VALID_AND_FEASIBLE"
    )
    theory_assessment = (
        "THEORY_REVISION_REQUIRED"
        if not accept and repair_scope == "upstream_theory"
        else "SUFFICIENT_FOR_IMPLEMENTATION_REPAIR"
    )
    verdict = "ACCEPT" if accept else "REVISE"
    repair_scopes = generated_code_semantic_review_repair_scopes(
        verdict=verdict,
        source_assessment=source_assessment,
        metric_contract_assessment=metric_contract_assessment,
        theory_assessment=theory_assessment,
    )
    repair_plan = [
        {
            "sequence": index,
            "repair_scope": scope,
            "repair_owner": (
                "ArchitectCoordinator"
                if scope.startswith("upstream_")
                else "AlgorithmEngineer"
            ),
        }
        for index, scope in enumerate(repair_scopes, start=1)
    ]
    return {
        "prior_finding_reviews": [],
        "reviewed_source_assessment": source_assessment,
        "frozen_metric_contract_assessment": metric_contract_assessment,
        "source_theory_assessment": theory_assessment,
        "dimension_reviews": rows,
        "findings": findings,
        "overall_verdict": verdict,
        "repair_scope": "none" if accept else repair_scope,
        "repair_scopes": repair_scopes,
        "repair_plan": repair_plan,
        "repair_owner": "AlgorithmEngineer",
        "repair_instructions": instructions,
    }


def _reviewer(
    *,
    accept: bool,
    model: str = LIVE_EVALUATION_CLAUDE_MODEL,
    model_tier: str = LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    repair_scope: str = "source_code",
    finding_evidence_refs: list[str] | None = None,
    finding_artifact_citations: list[str] | None = None,
):
    return LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(
            _review_response(
                accept=accept,
                repair_scope=repair_scope,
                finding_evidence_refs=finding_evidence_refs,
                finding_artifact_citations=finding_artifact_citations,
            )
        ),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=model,
            model_tier=model_tier,
            max_repair_attempts=0,
        ),
    )


def test_source_review_lineage_budget_does_not_reset_through_architect() -> None:
    work_order = {
        "question_id": "generic-question",
        "theory_packet_id": "theory:one",
        "theory_packet_hash": "theory-hash-one",
        "source_subsystem": "AlgorithmEngineer",
    }
    review_packet = _review_response(accept=False)

    first = advance_generated_code_semantic_review_lineage_budget(
        architect_context={},
        work_order=work_order,
        review_packet=review_packet,
        max_local_revisions=1,
    )
    assert first["local_repair_available"] is True
    assert first["architect_replan_available"] is False
    first_ledger = record_generated_code_semantic_review_lineage_action(
        first,
        action="local_repair",
    )

    second = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: first_ledger
        },
        work_order=work_order,
        review_packet=review_packet,
        max_local_revisions=1,
    )
    assert second["local_repair_available"] is False
    assert second["architect_replan_available"] is False
    assert second["lineage_budget_exhausted"] is True
    assert second["row"]["rejection_count"] == 2

    fresh_theory = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: first_ledger
        },
        work_order={**work_order, "theory_packet_hash": "theory-hash-two"},
        review_packet=review_packet,
        max_local_revisions=1,
    )
    assert fresh_theory["lineage_key"] != second["lineage_key"]
    assert fresh_theory["local_repair_available"] is True

    different_finding_packet = json.loads(json.dumps(review_packet))
    different_finding_packet["findings"][0]["category"] = "data_generation"
    changed_finding_after_local_repair = (
        advance_generated_code_semantic_review_lineage_budget(
            architect_context={
                GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: first_ledger
            },
            work_order=work_order,
            review_packet=different_finding_packet,
            max_local_revisions=1,
        )
    )
    assert changed_finding_after_local_repair["lineage_key"] != second["lineage_key"]
    assert (
        changed_finding_after_local_repair["source_lineage_key"]
        == second["source_lineage_key"]
    )
    assert changed_finding_after_local_repair["local_repair_available"] is False
    assert changed_finding_after_local_repair["architect_replan_available"] is False
    assert changed_finding_after_local_repair["lineage_budget_exhausted"] is True


def test_upstream_theory_feedback_is_consumed_once_and_globally_bounded() -> None:
    def replan(
        *,
        prior_theory_packet_id: str,
        review_execution_id: str,
    ) -> dict[str, object]:
        return {
            "artifact_kind": "RuntimeGeneratedCodeSemanticReviewReplanContext",
            "source_subsystem": "AlgorithmEngineer",
            "source_manifest_id": "algorithm:rejected",
            "review_packet_id": f"review-packet:{review_execution_id}",
            "review_execution_id": review_execution_id,
            "repair_scope": "upstream_theory",
            "pending_artifact_ids": {
                "theory_packet_id": prior_theory_packet_id,
            },
        }

    first_replan = replan(
        prior_theory_packet_id="theory:one",
        review_execution_id="review-execution:one",
    )
    first_context = {
        "runtime_generated_code_semantic_review_replan": first_replan,
        "environment_feedback": {
            "semantic_review_execution_id": "review-execution:one",
        },
        "runtime_feedback_loop": {
            "semantic_review_execution_id": "review-execution:one",
        },
    }
    first_state = generated_code_semantic_review_upstream_theory_revision_state(
        architect_context=first_context,
        question_id="generic-question",
        max_revisions=2,
    )
    assert first_state["active"] is True
    assert first_state["budget_exhausted"] is False

    consumed_once = consume_generated_code_semantic_review_upstream_theory_replan(
        architect_context=first_context,
        question_id="generic-question",
        revised_theory_packet_id="theory:two",
        revised_theory_packet_hash="theory-hash-two",
        max_revisions=2,
    )
    assert "runtime_generated_code_semantic_review_replan" not in consumed_once
    assert "environment_feedback" not in consumed_once
    assert "runtime_feedback_loop" not in consumed_once
    resolution = consumed_once[
        "runtime_generated_code_semantic_review_replan_resolution"
    ]
    assert resolution["resolution_status"] == (
        "CONSUMED_BY_FRESH_THEORY_REVISION"
    )
    assert resolution["requires_fresh_metric_protocol_review"] is True

    second_context = {
        **consumed_once,
        "runtime_generated_code_semantic_review_replan": replan(
            prior_theory_packet_id="theory:two",
            review_execution_id="review-execution:two",
        ),
    }
    consumed_twice = consume_generated_code_semantic_review_upstream_theory_replan(
        architect_context=second_context,
        question_id="generic-question",
        revised_theory_packet_id="theory:three",
        revised_theory_packet_hash="theory-hash-three",
        max_revisions=2,
    )
    ledger = consumed_twice[
        GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_LEDGER_KEY
    ]
    assert next(iter(ledger.values()))["revisions_used"] == 2

    third_context = {
        **consumed_twice,
        "runtime_generated_code_semantic_review_replan": replan(
            prior_theory_packet_id="theory:three",
            review_execution_id="review-execution:three",
        ),
    }
    exhausted = generated_code_semantic_review_upstream_theory_revision_state(
        architect_context=third_context,
        question_id="generic-question",
        max_revisions=2,
    )
    assert exhausted["budget_exhausted"] is True
    result = generated_code_semantic_review_upstream_theory_budget_exhausted_result(
        task=AgentTask(
            task_id="theory:blocked",
            owner_subsystem="TheoryDeveloper",
            objective="Do not repeat an exhausted upstream theory revision.",
        ),
        question_id="generic-question",
        budget_state=exhausted,
    )
    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_upstream_theory_revision_budget_exhausted"
    )


def test_upstream_theory_budget_is_shared_across_source_subsystems() -> None:
    question_id = "generic-question"

    def replan(
        *,
        source_subsystem: str,
        prior_theory_packet_id: str,
        review_execution_id: str,
    ) -> dict[str, object]:
        return {
            "artifact_kind": "RuntimeGeneratedCodeSemanticReviewReplanContext",
            "source_subsystem": source_subsystem,
            "source_manifest_id": f"manifest:{source_subsystem}",
            "review_packet_id": f"review-packet:{review_execution_id}",
            "review_execution_id": review_execution_id,
            "repair_scope": "upstream_theory",
            "pending_artifact_ids": {
                "theory_packet_id": prior_theory_packet_id,
            },
        }

    first_context = {
        "runtime_generated_code_semantic_review_replan": replan(
            source_subsystem="SimulationEvaluator",
            prior_theory_packet_id="theory:one",
            review_execution_id="review-execution:simulation",
        )
    }
    consumed = consume_generated_code_semantic_review_upstream_theory_replan(
        architect_context=first_context,
        question_id=question_id,
        revised_theory_packet_id="theory:two",
        revised_theory_packet_hash="theory-hash-two",
        max_revisions=1,
    )
    second_context = {
        **consumed,
        "runtime_generated_code_semantic_review_replan": replan(
            source_subsystem="AlgorithmEngineer",
            prior_theory_packet_id="theory:two",
            review_execution_id="review-execution:algorithm",
        ),
    }
    exhausted = generated_code_semantic_review_upstream_theory_revision_state(
        architect_context=second_context,
        question_id=question_id,
        max_revisions=1,
    )

    assert exhausted["revisions_used"] == 1
    assert exhausted["budget_exhausted"] is True
    assert exhausted["row"]["budget_scope"] == "question_global"
    assert exhausted["row"]["source_subsystems"] == ["SimulationEvaluator"]

    legacy_lineage_key = stable_hash(
        [question_id, "SimulationEvaluator", "upstream_theory"]
    )
    legacy_context = {
        "runtime_generated_code_semantic_review_replan": second_context[
            "runtime_generated_code_semantic_review_replan"
        ],
        GENERATED_CODE_SEMANTIC_REVIEW_UPSTREAM_THEORY_REVISION_LEDGER_KEY: {
            legacy_lineage_key: {
                "lineage_key": legacy_lineage_key,
                "question_id": question_id,
                "source_subsystem": "SimulationEvaluator",
                "repair_scope": "upstream_theory",
                "revisions_used": 1,
                "max_revisions": 1,
                "consumed_review_execution_ids": [
                    "review-execution:simulation"
                ],
            }
        },
    }
    migrated = generated_code_semantic_review_upstream_theory_revision_state(
        architect_context=legacy_context,
        question_id=question_id,
        max_revisions=1,
    )

    assert migrated["budget_exhausted"] is True
    assert migrated["legacy_lineage_keys"] == [legacy_lineage_key]


def test_semantic_review_allows_only_one_post_replan_local_repair() -> None:
    work_order = {
        "question_id": "generic-question",
        "theory_packet_id": "theory:one",
        "theory_packet_hash": "theory-hash-one",
        "source_subsystem": "AlgorithmEngineer",
    }
    upstream_packet = _review_response(
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    initial = advance_generated_code_semantic_review_lineage_budget(
        architect_context={},
        work_order=work_order,
        review_packet=upstream_packet,
        max_local_revisions=1,
    )
    assert initial["local_repair_available"] is False
    assert initial["architect_replan_available"] is True
    assert initial["lineage_budget_exhausted"] is False
    replanned_ledger = record_generated_code_semantic_review_lineage_action(
        initial,
        action="architect_replan",
    )

    source_packet = _review_response(accept=False, repair_scope="source_code")
    source_packet["findings"][0]["category"] = "first_source_defect"
    first_post_replan = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: replanned_ledger
        },
        work_order=work_order,
        review_packet=source_packet,
        max_local_revisions=1,
    )
    assert first_post_replan["local_repair_available"] is True
    final_local_ledger = record_generated_code_semantic_review_lineage_action(
        first_post_replan,
        action="local_repair",
    )

    second_source_packet = json.loads(json.dumps(source_packet))
    second_source_packet["findings"][0]["category"] = "second_source_defect"
    second_post_replan = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: final_local_ledger
        },
        work_order=work_order,
        review_packet=second_source_packet,
        max_local_revisions=1,
    )
    assert second_post_replan["local_repair_available"] is False
    assert second_post_replan["architect_replan_available"] is False
    assert second_post_replan["lineage_budget_exhausted"] is True
    assert second_post_replan["row"][
        "source_post_replan_local_repair_count"
    ] == 1


def test_dependency_obligation_allows_one_hash_bound_descendant_retry() -> None:
    work_order = {
        "question_id": "generic-question",
        "theory_packet_id": "theory:one",
        "theory_packet_hash": "theory-hash-one",
        "source_subsystem": "SimulationEvaluator",
    }
    first_packet = _review_response(
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    first_packet["repair_scope"] = "upstream_generated_dependency"
    first_packet["repair_owner"] = "AlgorithmEngineer"
    first_packet["source_repair_contract"] = {
        "parent_source_manifest_hash": "dependency-parent-hash",
    }
    initial = advance_generated_code_semantic_review_lineage_budget(
        architect_context={},
        work_order=work_order,
        review_packet=first_packet,
        max_local_revisions=1,
    )
    first_replan_ledger = record_generated_code_semantic_review_lineage_action(
        initial,
        action="architect_replan",
    )
    replan = {
        "question_id": "generic-question",
        "repair_scope": "upstream_generated_dependency",
        "source_subsystem": "SimulationEvaluator",
        "source_manifest_id": "simulation:rejected",
        "rejected_descendant_source_manifest_id": "simulation:rejected",
        "rejected_descendant_source_manifest_hash": "simulation-rejected-hash",
        "repair_target_source_manifest_id": "algorithm:parent",
        "repair_target_source_manifest_hash": "dependency-parent-hash",
        "review_packet_id": "review:origin",
        "review_execution_id": "review-execution:origin",
        "semantic_review_revision_budget": {
            "revisions_used": 0,
            "max_revisions": 1,
        },
        "findings": [
            {
                "severity": "critical",
                "category": "dependency_contract",
                "summary": "The dependency violates the consumer contract.",
                "required_change": "Repair the exact dependency.",
                "repair_scope": "upstream_generated_dependency",
            }
        ],
    }
    plan_one = generated_code_dependency_verification_plan_after_repair(
        architect_context={},
        replan=replan,
        accepted_review={
            "source_manifest_id": "algorithm:fresh-one",
            "source_manifest_hash": "dependency-fresh-one-hash",
            "review_packet_id": "algorithm-review:one",
            "execution_id": "algorithm-review-execution:one",
        },
    )
    assert plan_one["repair_attempt_count"] == 1
    assert plan_one["max_repair_attempts"] == 2
    verification_material = {
        "pending_repair_plan": plan_one,
        "upstream_generated_dependency": {
            "algorithm_sandbox_manifest_hash": "dependency-fresh-one-hash",
        },
    }
    assert generated_code_semantic_review_pending_plan_errors(
        packet={},
        review_material=verification_material,
    ) == []
    active_verification = (
        generated_code_semantic_review_active_pending_repair_plan(
            verification_material
        )
    )
    assert active_verification["active_repair_scopes"] == []
    assert active_verification["dependency_verification_active"] is True

    retry_packet = json.loads(json.dumps(first_packet))
    retry_packet["findings"][0]["category"] = "fresh_dependency_contract"
    retry_packet["source_repair_contract"] = {
        "parent_source_manifest_hash": "dependency-fresh-one-hash",
    }
    retry = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: (
                first_replan_ledger
            ),
            GENERATED_CODE_SEMANTIC_REVIEW_PENDING_REPAIR_PLAN_KEY: plan_one,
        },
        work_order=work_order,
        review_packet=retry_packet,
        max_local_revisions=1,
    )
    assert retry["architect_replan_available"] is True
    assert retry["lineage_budget_exhausted"] is False
    assert retry["dependency_retry_state"]["retry_available"] is True
    second_replan_ledger = (
        record_generated_code_semantic_review_lineage_action(
            retry,
            action="architect_replan",
        )
    )

    plan_two = generated_code_dependency_verification_plan_after_repair(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_PENDING_REPAIR_PLAN_KEY: plan_one,
        },
        replan={
            **replan,
            "repair_target_source_manifest_id": "algorithm:fresh-one",
            "repair_target_source_manifest_hash": (
                "dependency-fresh-one-hash"
            ),
        },
        accepted_review={
            "source_manifest_id": "algorithm:fresh-two",
            "source_manifest_hash": "dependency-fresh-two-hash",
            "review_packet_id": "algorithm-review:two",
            "execution_id": "algorithm-review-execution:two",
        },
    )
    assert plan_two["repair_attempt_count"] == 2
    exhausted_packet = json.loads(json.dumps(retry_packet))
    exhausted_packet["source_repair_contract"] = {
        "parent_source_manifest_hash": "dependency-fresh-two-hash",
    }
    exhausted = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: (
                second_replan_ledger
            ),
            GENERATED_CODE_SEMANTIC_REVIEW_PENDING_REPAIR_PLAN_KEY: plan_two,
        },
        work_order=work_order,
        review_packet=exhausted_packet,
        max_local_revisions=1,
    )
    assert exhausted["architect_replan_available"] is False
    assert exhausted["dependency_retry_state"]["retry_available"] is False
    assert exhausted["lineage_budget_exhausted"] is True


def _runtime_fixture(
    tmp_path: Path,
    *,
    accept: bool,
    capability_eval: bool = False,
    reviewer_model: str = "",
    reviewer_model_tier: str = "",
    metric_failed: bool = False,
    repair_scope: str = "source_code",
    finding_evidence_refs: list[str] | None = None,
    finding_artifact_citations: list[str] | None = None,
):
    question = _question()
    code = (
        "def run_estimator(request):\n"
        "    return {'estimated_error': request['numerator'] / request['denominator']}\n\n"
        "def run_sandbox(seed, replicates):\n"
        "    return run_estimator({'numerator': seed % 7, "
        "'denominator': max(replicates, 1)})\n"
    )
    metrics = {"estimated_error": 0.03, "sandbox_failed": False}
    script_path = tmp_path / "generated.py"
    result_path = tmp_path / "result.json"
    script_path.write_text(code, encoding="utf-8")
    result_path.write_text(json.dumps(metrics), encoding="utf-8")
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:test",
        "derivation_steps": [{"claim": "The metric estimates the target error."}],
    }
    source_model_tier = LIVE_EVALUATION_CLAUDE_MODEL_TIER
    source_model = STATIC_SOURCE_CLAUDE_MODEL
    proposal_packet = {
        "artifact_kind": "AlgorithmEngineerProposalPacket",
        "packet_id": "algorithm-proposal:test",
        "source_agent": "LLMAlgorithmEngineerAgent",
        "model": source_model,
        "model_tier": source_model_tier,
        "implementation_targets": [
            {
                "estimator_id": "generated-estimator",
                "adapter_strategy": "Implement the declared estimator interface.",
            }
        ],
        "theory_trace_alignment_contract": {
            "supported_derivation_steps": ["theory:test:step:1"],
            "supported_equation_steps": [],
            "supported_formalization_targets": [],
        },
    }
    row = {
        "estimator_id": "generated-estimator",
        "prototype_status": "FAILED_METRIC_GATE" if metric_failed else "EXECUTED",
        "executor": "generated_python_sandbox",
        "executor_profile": "stdlib",
        "language": "python",
        "dependencies": [],
        "script_path": str(script_path),
        "result_path": str(result_path),
        "script_hash": stable_hash(code),
        "result_hash": stable_hash(metrics),
        "metrics": metrics,
        "runtime_seed": 41,
        "runtime_replicates": 100,
        "metric_contracts": [],
        "metric_contract_set_id": "metric-contracts:test",
        "metric_requirement_set_id": "metric-requirements:test",
        "metric_contract_evaluation": {
            "all_required_passed": not metric_failed,
            "evaluations": [
                {
                    "contract_id": "metric-contract:test",
                    "requirement_id": "frozen:algorithm-error",
                    "required": True,
                    "passed": not metric_failed,
                }
            ],
        },
        "execution_smoke_passed": True,
        "smoke_passed": not metric_failed,
    }
    source_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm_sandbox_manifest:test",
        "theory_packet_id": theory_packet["packet_id"],
        "prototypes": [row],
        "n_generated_code_executed": 1,
        "n_passed": 0 if metric_failed else 1,
    }
    empirical_metric_requirements = [
        {
            "requirement_id": "frozen:simulation-calibration",
            "target_subsystems": ["SimulationEngineer"],
            "metric_name": "calibration",
        },
    ]
    if repair_scope == "upstream_metric_contract":
        empirical_metric_requirements.append(
            {
                "requirement_id": "frozen:algorithm-error",
                "target_subsystems": ["AlgorithmEngineer"],
                "metric_name": "estimated_error",
                "metric_semantics": "Error returned by the generated estimator.",
                "measurement_protocol": (
                    "Read estimated_error from the exact estimator result."
                ),
            }
        )
    architect_context = {
        "architect_runtime_plan": {
            "evidence_contract": {
                "evaluation_mode": (
                    "capability_eval" if capability_eval else "debug"
                ),
                "empirical_metric_requirements": empirical_metric_requirements,
            }
        }
    }
    repair_task = AgentTask(
        task_id="algorithm:test",
        owner_subsystem="AlgorithmEngineer",
        objective="Generate and execute algorithm code.",
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "theory_packet_id": theory_packet["packet_id"],
            "simulation_manifest_id": "simulation:test",
            "implementation_gaps": [{"estimator_id": "generated-estimator"}],
            "architect_context": architect_context,
        },
    )
    deferred_task = AgentTask(
        task_id="formalize:test",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize after semantic acceptance.",
        inputs={
            "question": repair_task.inputs["question"],
            "theory_packet_id": theory_packet["packet_id"],
            "algorithm_sandbox_manifest_id": source_manifest["manifest_id"],
            "architect_context": architect_context,
        },
    )
    dispatch = _runtime_generated_code_semantic_review_dispatch(
        task=repair_task,
        question=question,
        source_subsystem="AlgorithmEngineer",
        source_manifest=source_manifest,
        theory_packet=theory_packet,
        proposal_packet=proposal_packet,
        architect_context=architect_context,
        deferred_next_task=deferred_task,
        max_revisions=1,
        metric_failure_feedback=(
            {
                "feedback_type": "algorithm_sandbox_execution_feedback",
                "feedback_id": "metric-feedback:test",
                "failure_classification": (
                    "generated_algorithm_sandbox_metric_gate_failed"
                ),
                "generated_algorithm_prototypes": [row],
            }
            if metric_failed
            else None
        ),
    )
    assert dispatch is not None
    blackboard = BlackboardState(project_id="semantic-review-test")
    blackboard.artifacts.update(
        {
            str(theory_packet["packet_id"]): theory_packet,
            str(proposal_packet["packet_id"]): proposal_packet,
            str(source_manifest["manifest_id"]): source_manifest,
            str(dispatch["work_order_id"]): dispatch["work_order"],
        }
    )
    subsystem = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=_reviewer(
            accept=accept,
            model=reviewer_model or LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=reviewer_model_tier or source_model_tier,
            repair_scope=repair_scope,
            finding_evidence_refs=finding_evidence_refs,
            finding_artifact_citations=finding_artifact_citations,
        ),
        max_revisions=1,
    )
    return subsystem, dispatch["next_task"], blackboard, script_path


def test_generated_code_semantic_reviewer_accepts_and_resumes_deferred_task(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "FormalizationEvaluator"
    accepted = result.next_task.inputs["accepted_generated_code_semantic_reviews"]
    assert accepted[0]["overall_verdict"] == "ACCEPT"
    executions = [
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    ]
    assert executions[0]["semantic_review_accepted"] is True
    assert executions[0]["reviewer_model_tier"] == (
        LIVE_EVALUATION_CLAUDE_MODEL_TIER
    )
    assert executions[0]["independent_invocation"] is True
    work_order = next(
        row
        for row in blackboard.artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewWorkOrder"
    )
    responsibility = work_order["source_responsibility_contract"]
    assert responsibility["generated_code_author_subsystem"] == (
        "AlgorithmEngineer"
    )
    assert responsibility["assigned_requirement_ids"] == []
    assert responsibility["sibling_only_requirement_refs"] == [
        {
            "requirement_id": "frozen:simulation-calibration",
            "target_subsystems": ["SimulationEngineer"],
        }
    ]
    assert "not automatically a requirement" in responsibility[
        "artifact_review_rule"
    ]
    assert "interface precondition" in responsibility["artifact_review_rule"]
    assert executions[0][
        "source_responsibility_contract_fingerprint"
    ] == stable_hash(responsibility)
    materialization = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    assert materialization["review_material"][
        "source_responsibility_contract"
    ] == responsibility
    review_material = materialization["review_material"]
    assert review_material["architect_frozen_evidence_contract"][
        "empirical_metric_requirements"
    ] == []
    projection = review_material["review_scope_projection"]
    assert projection["assigned_requirement_ids"] == []
    assert projection["sibling_only_requirement_refs"] == (
        responsibility["sibling_only_requirement_refs"]
    )
    assert projection[
        "canonical_architect_evidence_contract_fingerprint"
    ] == stable_hash(work_order["architect_evidence_contract"])


def test_semantic_review_projection_excludes_advisory_coding_agent_work(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    proposal = blackboard.artifacts[str(work_order["proposal_packet_id"])]
    theory = blackboard.artifacts[str(work_order["theory_packet_id"])]
    theory["question"] = {"id": "semantic-review-test"}
    theory["problem_card"] = {
        "dgp": "Current-artifact data-generating process.",
        "estimand": "Current-artifact target.",
        "assumptions": ["current assumption"],
    }
    theory["theory_derivation_packet"] = {
        "derivation_steps": [
            {
                "id": "current-step",
                "claim": "The current artifact estimates the target.",
            },
            {
                "id": "future-step",
                "claim": "A future unrelated method may be developed.",
            },
        ],
        "equation_chain": [
            {
                "step_id": "current-equation",
                "lhs": "target",
                "rhs": "estimate",
            },
            {
                "step_id": "future-equation",
                "lhs": "future",
                "rhs": "work",
            },
        ],
        "assumption_ledger": [
            {
                "assumption": "current assumption",
                "used_in": ["current-step"],
            },
            {
                "assumption": "future assumption",
                "used_in": ["future-step"],
            },
        ],
        "sanity_checks": [
            {
                "id": "current-check",
                "claim_ref": "current-step",
                "result": "passes",
            },
            {
                "id": "future-check",
                "claim_ref": "future-step",
                "result": "not delegated",
            },
        ],
        "formalization_handoff": {
            "semantic_alignment_constraints": [
                "current formal target",
                "future formal target",
            ]
        },
    }
    theory["critic_findings"] = [
        {"finding": "Future system-level work is still open."}
    ]
    proposal["implementation_targets"] = [
        {
            "estimator_id": "generated-estimator",
            "adapter_strategy": "Implement the theory-defined estimator.",
            "registered_template_hint": "none",
            "data_contract": ["named finite request and response"],
            "estimator_interface_contract": {
                "request_fields": [],
                "response_fields": [],
            },
            "estimator_interface_contract_id": "interface:theory-owned",
            "estimator_interface_contract_authority": {
                "owner_agent": "TheoryDeveloper",
                "transport_status": "RUNTIME_BOUND_FROM_THEORY",
            },
            "validation_metrics": [
                "Advisory future diagnostic not assigned by Architect"
            ],
            "risk_controls": ["Advisory future stress test"],
        }
    ]
    proposal["sandbox_code_drafts"] = [
        {
            "estimator_id": "generated-estimator",
            "code": "duplicate source envelope",
        }
    ]
    proposal["next_actions"] = [
        {
            "owner_agent": "AlgorithmEngineer",
            "action": "Invent a future capability.",
            "acceptance_gate": "Advisory only.",
        }
    ]
    proposal["theory_trace_alignment_contract"] = {
        "artifact_kind": "TheoryTraceAlignmentContract",
        "structured_alignment_observed": True,
        "supported_derivation_steps": ["current-step"],
        "supported_equation_steps": ["current-equation"],
        "supported_assumptions": ["current assumption"],
        "supported_formalization_targets": ["current formal target"],
    }
    work_order["theory_packet_hash"] = stable_hash(theory)
    work_order["proposal_packet_hash"] = stable_hash(proposal)
    task.inputs["work_order_hash"] = stable_hash(work_order)

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    materialization = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    projected = materialization["review_material"][
        "coding_agent_proposal_packet"
    ]
    assert "next_actions" not in projected
    assert "sandbox_code_drafts" not in projected
    target = projected["implementation_targets"][0]
    assert set(target) == {
        "estimator_id",
        "adapter_strategy",
        "registered_template_hint",
        "data_contract",
        "estimator_interface_contract",
        "estimator_interface_contract_id",
        "estimator_interface_contract_authority",
    }
    assert target["estimator_interface_contract_authority"]["owner_agent"] == (
        "TheoryDeveloper"
    )
    projection = projected["proposal_review_projection"]
    assert projection["canonical_proposal_fingerprint"] == stable_hash(
        proposal
    )
    assert "next_actions" in projection["excluded_non_authoritative_fields"]
    assert projection[
        "advisory_fields_cannot_create_acceptance_obligations"
    ] is True
    projected_theory = materialization["review_material"]["theory_packet"]
    assert projected_theory["theory_derivation_packet"] == {
        "derivation_steps": [
            {
                "id": "current-step",
                "claim": "The current artifact estimates the target.",
            }
        ],
        "equation_chain": [
            {
                "step_id": "current-equation",
                "lhs": "target",
                "rhs": "estimate",
            }
        ],
        "assumption_ledger": [
            {
                "assumption": "current assumption",
                "used_in": ["current-step"],
            }
        ],
        "sanity_checks": [
            {
                "id": "current-check",
                "claim_ref": "current-step",
                "result": "passes",
            }
        ],
        "formalization_handoff": {
            "semantic_alignment_constraints": ["current formal target"]
        },
    }
    assert "critic_findings" not in projected_theory
    theory_projection = projected_theory["theory_review_projection"]
    assert theory_projection["canonical_theory_packet_fingerprint"] == (
        stable_hash(theory)
    )
    assert theory_projection[
        "content_outside_projection_cannot_gate_current_artifact"
    ] is True
    assert "critic_findings" in theory_projection[
        "excluded_non_authoritative_top_level_fields"
    ]


def test_semantic_reviewer_regenerates_packet_after_extra_runtime_owned_slot(
    tmp_path: Path,
) -> None:
    _, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    invalid_response = _review_response(accept=True)
    dimension_rows = list(invalid_response["dimension_reviews"])
    invalid_response["dimension_reviews"] = [
        *dimension_rows,
        dict(dimension_rows[-1]),
    ]
    valid_response = _review_response(accept=True)

    class SequencedReviewBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []
            self.responses = [invalid_response, valid_response]

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            return GeneratorResponse(
                text=json.dumps(self.responses.pop(0)),
                provider=self.provider_name,
                model=request.model,
            )

    backend = SequencedReviewBackend()
    subsystem = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=LLMGeneratedCodeSemanticReviewerAgent(
            provider=backend,
            config=GeneratedCodeSemanticReviewerConfig(
                provider_name="anthropic",
                model=LIVE_EVALUATION_CLAUDE_MODEL,
                model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
                max_repair_attempts=1,
            ),
        ),
        max_revisions=1,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "FormalizationEvaluator"
    assert [request.model for request in backend.requests] == [
        LIVE_EVALUATION_CLAUDE_MODEL,
        LIVE_EVALUATION_CLAUDE_MODEL,
    ]
    assert all(
        request.metadata["model_tier"] == LIVE_EVALUATION_CLAUDE_MODEL_TIER
        for request in backend.requests
    )
    assert [
        request.metadata["json_repair_mode"] for request in backend.requests
    ] == [
        "full_packet_generation",
        "full_packet_regeneration",
    ]
    review_packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert len(review_packet["dimension_reviews"]) == len(
        GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS
    )


def test_accepted_algorithm_review_hands_exact_source_to_simulation(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, script_path = _runtime_fixture(
        tmp_path,
        accept=True,
    )
    result = subsystem.run(task, blackboard)
    blackboard.artifacts.update(result.produced_artifacts)
    assert result.next_task is not None
    context = result.next_task.inputs["architect_context"]

    handoff = result.next_task.inputs["upstream_algorithm_handoff"]
    assert _runtime_validated_algorithm_handoff(
        task=result.next_task,
        architect_context=context,
        blackboard=blackboard,
        question_id=_question().id,
        theory_packet_id="theory:test",
        algorithm_sandbox_manifest_id="algorithm_sandbox_manifest:test",
    ) == handoff

    exact = handoff["exact_algorithm_artifacts"][0]
    assert exact["estimator_id"] == "generated-estimator"
    assert exact["exact_source_code"] == script_path.read_text(encoding="utf-8")
    assert exact["exact_source_hash"] == stable_hash(exact["exact_source_code"])
    receipt = _runtime_algorithm_handoff_receipt(handoff)
    assert receipt["algorithm_sandbox_manifest_id"] == (
        "algorithm_sandbox_manifest:test"
    )
    assert receipt["exact_algorithm_artifact_refs"][0][
        "exact_source_hash"
    ] == exact["exact_source_hash"]
    assert receipt["handoff_fingerprint"] == stable_hash(handoff)
    assert receipt["mechanical_estimator_invocation_verified"] is False
    bound_receipt = _runtime_algorithm_handoff_receipt(
        handoff,
        simulation_rows=[
            {
                "simulation_id": "confirmatory-dgp",
                "script_hash": "simulation-source-hash",
                "result_hash": "simulation-result-hash",
                "execution_envelope_hash": "execution-envelope-hash",
                "estimator_binding_hash": stable_hash(
                    {exact["estimator_id"]: exact["exact_source_hash"]}
                ),
                "bound_estimator_code_hashes": {
                    exact["estimator_id"]: exact["exact_source_hash"]
                },
                "estimator_invocation_counts": {exact["estimator_id"]: 50},
                "mechanical_estimator_invocation_verified": True,
            }
        ],
    )
    assert bound_receipt["mechanical_estimator_invocation_verified"] is True
    assert bound_receipt["mechanical_invocation_evidence"][0][
        "estimator_invocation_counts"
    ] == {exact["estimator_id"]: 50}
    forged_receipt = _runtime_algorithm_handoff_receipt(
        handoff,
        simulation_rows=[
            {
                **bound_receipt["mechanical_invocation_evidence"][0],
                "script_hash": "simulation-source-hash",
                "result_hash": "simulation-result-hash",
                "estimator_invocation_counts": {exact["estimator_id"]: 0},
                "mechanical_estimator_invocation_verified": True,
            }
        ],
    )
    assert forged_receipt["mechanical_estimator_invocation_verified"] is False
    prompt = build_simulation_engineer_prompt(
        question=_question(),
        theory_packet={"packet_id": "theory:test", "theorem_cards": []},
        registered_problem={},
        registered_procedures=[],
        n_runs=50,
        seed=12,
        environment_feedback={"upstream_algorithm_handoff": handoff},
    )
    assert json.dumps(exact["exact_source_code"])[1:-1] in prompt
    assert exact["exact_source_hash"] in prompt
    assert "Do not silently replace it" in prompt
    assert "run_sandbox(seed, replicates, estimators)" in prompt
    assert "runtime-injected" in prompt


def test_algorithm_handoff_rejects_tampered_review_materialization(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    result = subsystem.run(task, blackboard)
    blackboard.artifacts.update(result.produced_artifacts)
    assert result.next_task is not None
    materialization = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    materialization["review_material"]["exact_executed_artifacts"][0][
        "exact_source_code"
    ] += "\n# changed after review\n"

    assert _runtime_validated_algorithm_handoff(
        task=result.next_task,
        architect_context=result.next_task.inputs["architect_context"],
        blackboard=blackboard,
        question_id=_question().id,
        theory_packet_id="theory:test",
        algorithm_sandbox_manifest_id="algorithm_sandbox_manifest:test",
    ) == {}


def test_algorithm_review_cannot_accept_legacy_metric_gate_failure(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        metric_failed=True,
    )
    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "accepted_algorithm_handoff_materialization_failed"
    )


def test_semantic_reviewer_prompt_keeps_sibling_metrics_out_of_artifact_gate() -> None:
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material={
            "source_responsibility_contract": {
                "assigned_requirement_ids": ["algorithm:assigned"],
                "sibling_only_requirement_refs": [
                    {
                        "requirement_id": "simulation:sibling",
                        "target_subsystems": ["SimulationEngineer"],
                    }
                ],
            }
        },
    )

    assert "requirements assigned to its author subsystem" in prompt
    assert "omitting a requirement assigned only to a sibling artifact" in prompt
    assert "least-authority view" in prompt
    assert "cannot make a required dimension FAIL" in prompt
    assert "reject any current-source proposal claim" in prompt
    assert "excluded_non_authoritative_fields" in prompt
    assert "cannot create acceptance obligations" in prompt
    assert "theory_review_projection" in prompt
    assert "cannot become source-code repair requirements" in prompt
    assert "Scope a finding to source_code" in prompt
    assert "upstream_theory only for a missing" in prompt
    assert "reviewer hypothesis, not final repair-owner authority" in prompt
    assert "AgentRuntime derives aggregate routing" in prompt
    assert "do not authorize post-result threshold relaxation" in prompt.lower()
    assert "unambiguous current theory" in prompt
    assert "do not choose one side as a coding instruction" in prompt
    assert "conservative, zero, noisy" in prompt
    assert "source_code finding needs a specific mismatch" in prompt
    assert "minimum replicate count for the enclosing sandbox execution" in prompt
    assert "aggregation=identity may validly check one deterministic scalar" in prompt
    assert "Do not create a mandatory diagnostic" in prompt
    assert "absent from the current source-responsibility contract" in prompt
    assert "never expand the current artifact" in prompt
    assert "empirically prove a theorem premise" in prompt
    assert "finite Monte Carlo deviation" in prompt
    assert "Numerical stability" in prompt


def test_algorithm_review_prompt_projects_only_assigned_metric_authority() -> None:
    prompt = build_generated_code_semantic_review_prompt(
        question=OpenResearchQuestion(
            id="owner-scoped-review",
            title="Review one generated estimator",
            description="system-wide-description-must-not-gate-this-estimator",
        ),
        review_material={
            "source_subsystem": "AlgorithmEngineer",
            "source_responsibility_contract": {
                "runtime_source_subsystem": "AlgorithmEngineer",
                "assigned_requirement_ids": ["algorithm:assigned"],
                "assigned_empirical_metric_requirements": [
                    {
                        "requirement_id": "algorithm:assigned",
                        "measurement_protocol": "assigned-protocol-marker",
                    }
                ],
                "sibling_only_requirement_refs": [
                    {
                        "requirement_id": "simulation:sibling",
                        "target_subsystems": ["SimulationEngineer"],
                    }
                ],
                "system_coverage_owner": "CriticEvaluator",
            },
            "architect_frozen_evidence_contract": {
                "evaluation_mode": "capability_eval",
                "empirical_metric_requirements": [
                    {
                        "requirement_id": "algorithm:assigned",
                        "measurement_protocol": "assigned-protocol-marker",
                    },
                    {
                        "requirement_id": "simulation:sibling",
                        "measurement_protocol": "sibling-secret-protocol-marker",
                    },
                ],
            },
        },
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    projected_contract = payload["review_material"][
        "architect_frozen_evidence_contract"
    ]

    assert [
        row["requirement_id"]
        for row in projected_contract["empirical_metric_requirements"]
    ] == ["algorithm:assigned"]
    assert "assigned-protocol-marker" in prompt
    assert "sibling-secret-protocol-marker" not in prompt
    assert "system-wide-description-must-not-gate-this-estimator" not in prompt
    dimension_contract = payload["dimension_authority_contract"]
    assert dimension_contract["question_alignment"][
        "sibling_requirements_may_block"
    ] is False
    assert "SimulationEvaluator" in dimension_contract[
        "experiment_non_vacuity_and_identifiability"
    ]["algorithm_smoke_test_boundary"]


def test_python_interface_inventory_reports_syntax_without_semantic_verdict() -> None:
    inventory = _python_generated_source_interface_inventory(
        """
def run_estimator(request):
    observations = request["observations"]
    seed = request.get("seed", 0)
    return {"estimate": sum(observations) + seed}

def run_sandbox(seed, replicates):
    return run_estimator({"observations": [1.0], "seed": seed})
"""
    )

    assert inventory["parsed"] is True
    functions = {row["function_name"]: row for row in inventory["functions"]}
    assert functions["run_estimator"]["mapping_key_accesses_by_parameter"] == {
        "request": ["observations", "seed"]
    }
    assert functions["run_estimator"]["returned_literal_fields"] == ["estimate"]
    assert functions["run_sandbox"]["called_mapping_literal_fields"] == {
        "run_estimator": ["observations", "seed"]
    }


def test_review_prompt_exposes_generic_interface_binding_work_order() -> None:
    interface_contract = {
        "request_fields": [
            {
                "name": "observations",
                "meaning": "Observed sample.",
                "binding": "Supplied by the runtime.",
            },
            {
                "name": "frozen_value",
                "meaning": "Theory-frozen scalar.",
                "binding": "Supplied by the runtime.",
            },
        ],
        "response_fields": [
            {
                "name": "estimate",
                "meaning": "Point estimate.",
                "normalization": "none",
                "sample_size_order": "scalar",
            },
            {
                "name": "uncertainty",
                "meaning": "Reported uncertainty.",
                "normalization": "none",
                "sample_size_order": "scalar",
            },
        ],
    }
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material={
            "source_subsystem": "AlgorithmEngineer",
            "source_responsibility_contract": {
                "runtime_source_subsystem": "AlgorithmEngineer",
                "assigned_requirement_ids": [],
                "assigned_empirical_metric_requirements": [],
            },
            "theory_packet": {
                "estimator_specs": [
                    {"estimator_interface_contract": interface_contract}
                ]
            },
            "coding_agent_proposal_packet": {
                "implementation_targets": [
                    {
                        "estimator_id": "generic-estimator",
                        "estimator_interface_contract_id": "interface:generic",
                        "estimator_interface_contract_authority": {
                            "source_estimator_ref": (
                                "theory#/estimator_specs/0/"
                                "estimator_interface_contract"
                            )
                        },
                        "estimator_interface_contract": interface_contract,
                    }
                ]
            },
            "exact_executed_artifacts": [
                {
                    "artifact_id": "generic-estimator",
                    "source_row": {
                        "estimator_id": "generic-estimator",
                        "language": "python",
                    },
                    "exact_source_code": (
                        "def run_estimator(request):\n"
                        "    observed = request['observations']\n"
                        "    return {'estimate': sum(observed)}\n"
                    ),
                }
            ],
        },
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    work_order = payload["interface_binding_work_orders"][0]

    assert work_order["observed_run_estimator_request_field_names"] == [
        "observations"
    ]
    assert work_order[
        "expected_request_field_names_not_observed_literally"
    ] == ["frozen_value"]
    assert work_order[
        "expected_response_field_names_not_observed_literally"
    ] == ["uncertainty"]
    assert work_order["expected_interface_evidence_citation"] == {
        "artifact_role": "source_theory_packet",
        "locator": "/estimator_specs/0/estimator_interface_contract",
    }
    assert "not a semantic verdict" in work_order["name_comparison_boundary"]
    assert payload["dimension_authority_contract"][
        "execution_argument_alignment"
    ]["structured_observations"] == "interface_binding_work_orders"
    authority_contract = payload["review_material"][
        "review_authority_contract"
    ]
    assert authority_contract[
        "theory_premises_are_not_automatic_runtime_validation_obligations"
    ] is True
    assert "do not by themselves require" in authority_contract[
        "authority_kind_interpretation"
    ]["proposal_consumed_theory_alignment"]
    assert "not automatically a runtime-validation postcondition" in payload[
        "dimension_authority_contract"
    ]["theory_assumption_alignment"]["premise_boundary"]


def test_actionable_review_requires_a_distinct_authority_bound_delta(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="source_code",
    )
    result = subsystem.run(task, blackboard)
    packet = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    materialization = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    review_material = materialization["review_material"]

    equivalent = json.loads(json.dumps(packet))
    equivalent["findings"][0]["artifact_delta"][
        "before_after_semantically_equivalent"
    ] = True
    assert any(
        "semantically equivalent" in error
        for error in validate_generated_code_semantic_review_packet(
            equivalent,
            review_material=review_material,
        )
    )

    uncited_authority = json.loads(json.dumps(packet))
    uncited_authority["findings"][0]["evidence_citations"] = [
        {
            "artifact_role": "generated_source_artifact",
            "locator": "/exact_source_code",
        }
    ]
    uncited_authority["findings"][0]["evidence_refs"] = [
        "generated_source_artifact#/exact_source_code"
    ]
    uncited_authority["findings"][0]["artifact_citations"] = [
        "generated_source_artifact"
    ]
    authority_errors = validate_generated_code_semantic_review_packet(
        uncited_authority,
        review_material=review_material,
    )
    assert any("artifact scope selected" in error for error in authority_errors)
    assert any(
        "obligation_ref='implementation_target:generated-estimator'" in error
        for error in authority_errors
    )
    assert not any("{obligation_ref!r}" in error for error in authority_errors)
    assert any("required_authority_scope=" in error for error in authority_errors)
    assert any("make it advisory" in error for error in authority_errors)

    precise_authority = json.loads(json.dumps(packet))
    for citation in precise_authority["findings"][0]["evidence_citations"]:
        if citation["locator"] == (
            "/coding_agent_proposal_packet/implementation_targets/0"
        ):
            citation["locator"] += "/estimator_id"
    precise_authority_errors = validate_generated_code_semantic_review_packet(
        precise_authority,
        review_material=review_material,
    )
    assert not any(
        "artifact scope selected" in error
        for error in precise_authority_errors
    )

    mismatched_current_artifact = json.loads(json.dumps(packet))
    mismatched_current_artifact["findings"][0]["evidence_citations"] = [
        citation
        for citation in mismatched_current_artifact["findings"][0][
            "evidence_citations"
        ]
        if citation
        != {
            "artifact_role": "generated_source_artifact",
            "locator": "/exact_source_code",
        }
    ]
    mismatched_current_errors = validate_generated_code_semantic_review_packet(
        mismatched_current_artifact,
        review_material=review_material,
    )
    assert any(
        "required_current_citation="
        "generated_source_artifact#/exact_source_code" in error
        for error in mismatched_current_errors
    )
    assert any(
        "revise both the model-authored current artifact locator and its citation"
        in error
        for error in mismatched_current_errors
    )


def test_actionable_review_accepts_precise_descendant_authority_citation(
    tmp_path: Path,
) -> None:
    response = _review_response(
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    finding = response["findings"][0]
    for citation in finding["evidence_citations"]:
        if citation["locator"] == "/empirical_metric_requirements/0":
            citation["locator"] = (
                "/architect_frozen_evidence_contract/"
                "empirical_metric_requirements/0/measurement_protocol"
            )
    reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    subsystem.reviewer = reviewer

    result = subsystem.run(task, blackboard)

    packet = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    materialization = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    assert validate_generated_code_semantic_review_packet(
        packet,
        review_material=materialization["review_material"],
    ) == []


def test_semantic_reviewer_prompt_surfaces_runtime_metric_gate_outcomes() -> None:
    review_material = {
        "exact_executed_artifacts": [
            {
                "artifact_id": "simulation:one",
                "source_row": {
                    "metric_contracts": [
                        {
                            "contract_id": "MC:one",
                            "requirement_id": "requirement:one",
                            "operator": "<=",
                            "threshold": 0.05,
                            "tolerance": 0.015,
                            "required": True,
                        }
                    ],
                    "metric_contract_evaluation": {
                        "evaluations": [
                            {
                                "contract_id": "MC:one",
                                "requirement_id": "requirement:one",
                                "artifact_id": "simulation:one",
                                "metric_path": ["error_rate"],
                                "operator": "<=",
                                "aggregate_value": 0.0625,
                                "required": True,
                                "passed": True,
                                "errors": [],
                            }
                        ]
                    },
                },
            }
        ]
    }
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material=review_material,
    )
    payload = json.loads(prompt.rsplit("\n\n", 1)[1])
    gate = payload["runtime_metric_gate_projection"][0]

    assert gate["contract_id"] == "MC:one"
    assert gate["aggregate_value"] == 0.0625
    assert gate["threshold"] == 0.05
    assert gate["tolerance"] == 0.015
    assert gate["passed"] is True
    assert gate["outcome_authority"] == (
        "runtime_generated_metric_contract_evaluator"
    )
    assert gate["evidence_citation"] == {
        "artifact_role": "generated_source_artifact",
        "locator": (
            "/exact_executed_artifacts/0/source_row/"
            "metric_contract_evaluation/evaluations/0"
        ),
    }
    cited = _generated_code_semantic_review_row_cited_values(
        review_material=review_material,
        row={"evidence_citations": [gate["evidence_citation"]]},
    )
    assert cited[0]["resolved"] is True
    assert cited[0]["value"]["aggregate_value"] == 0.0625
    assert "never describe a row with passed=true" in prompt
    assert "prompt-only label" in prompt


def test_semantic_review_routes_valid_protocol_implementation_mismatch_to_source() -> None:
    assert generated_code_semantic_review_repair_scope(
        verdict="REVISE",
        source_assessment="SOURCE_REPAIR_REQUIRED",
        metric_contract_assessment="VALID_AND_FEASIBLE",
        theory_assessment="SUFFICIENT_FOR_IMPLEMENTATION_REPAIR",
    ) == "source_code"


def test_semantic_review_orders_repairs_by_artifact_dependency() -> None:
    assert generated_code_semantic_review_repair_scopes(
        verdict="REVISE",
        source_assessment="SOURCE_REPAIR_REQUIRED",
        metric_contract_assessment="INVALID_OR_INFEASIBLE",
        theory_assessment="THEORY_REVISION_REQUIRED",
    ) == ["upstream_theory", "upstream_metric_contract", "source_code"]


def test_reviewer_derives_aggregate_decisions_from_findings(
    tmp_path: Path,
) -> None:
    _, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    response = _review_response(accept=False, repair_scope="source_code")
    for duplicate_field in (
        "reviewed_source_assessment",
        "frozen_metric_contract_assessment",
        "source_theory_assessment",
        "overall_verdict",
    ):
        response.pop(duplicate_field)
    subsystem = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=LLMGeneratedCodeSemanticReviewerAgent(
            provider=StaticJSONGeneratorBackend(response),
            config=GeneratedCodeSemanticReviewerConfig(
                provider_name="static",
                model=LIVE_EVALUATION_CLAUDE_MODEL,
                model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
                max_repair_attempts=0,
            ),
        ),
        max_revisions=1,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE", result.observations
    review_packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert review_packet["overall_verdict"] == "REVISE"
    assert review_packet["reviewed_source_assessment"] == (
        "SOURCE_REPAIR_REQUIRED"
    )
    assert review_packet["frozen_metric_contract_assessment"] == (
        "VALID_AND_FEASIBLE"
    )
    assert review_packet["source_theory_assessment"] == (
        "SUFFICIENT_FOR_IMPLEMENTATION_REPAIR"
    )
    assert review_packet["repair_scopes"] == ["source_code"]
    assert review_packet["model_requested_overall_verdict"] == ""


def test_all_pass_actionable_finding_routes_without_duplicate_dimension_verdict(
    tmp_path: Path,
) -> None:
    _, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    response = _review_response(accept=True)
    response["findings"] = [
        {
            "severity": "medium",
            "category": "maintainability",
            "summary": "The diagnostic name could be more explicit.",
            "required_change": "Use a more descriptive diagnostic name later.",
            "repair_scope": "source_code",
            "prior_finding_id": "",
            "authority_refs": [
                "implementation_target:generated-estimator"
            ],
            "artifact_delta": {
                "obligation_ref": "implementation_target:generated-estimator",
                "obligation_kind": "implementation_target",
                "current_artifact_role": "generated_source_artifact",
                "current_artifact_locator": "/exact_source_code",
                "current_behavior": "The current diagnostic uses a short name.",
                "required_behavior": "The proposal requires the same computation.",
                "observable_change": "Only the diagnostic label would change.",
                "before_after_semantically_equivalent": False,
            },
            "evidence_citations": [
                {
                    "artifact_role": "generated_source_artifact",
                    "locator": "/exact_source_code",
                },
                {
                    "artifact_role": "generated_source_artifact",
                    "locator": (
                        "/coding_agent_proposal_packet/implementation_targets/0"
                    ),
                },
            ],
        }
    ]
    response["repair_instructions"] = [
        "Use a more descriptive diagnostic name later."
    ]

    class RecordingBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            return GeneratorResponse(
                text=json.dumps(response),
                provider=self.provider_name,
                model=request.model,
            )

    backend = RecordingBackend()
    subsystem = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=LLMGeneratedCodeSemanticReviewerAgent(
            provider=backend,
            config=GeneratedCodeSemanticReviewerConfig(
                provider_name="anthropic",
                model=LIVE_EVALUATION_CLAUDE_MODEL,
                model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
                max_repair_attempts=1,
            ),
        ),
        max_revisions=1,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE", result.observations
    assert len(backend.requests) == 1
    review_packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert review_packet["overall_verdict"] == "REVISE"
    assert review_packet["repair_scope"] == "source_code"
    assert review_packet["repair_scopes"] == ["source_code"]
    assert review_packet["reviewed_source_assessment"] == "SOURCE_REPAIR_REQUIRED"
    assert review_packet["findings"][0]["repair_scope"] == "source_code"
    assert review_packet["findings"][0][
        "model_requested_repair_scope"
    ] == "source_code"
    assert len(review_packet["active_unresolved_finding_ids"]) == 1


def test_schema_v14_binds_decisions_to_complete_review_material(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)

    result = subsystem.run(task, blackboard)

    review_packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    materialization = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    assert review_packet["schema_version"] == 14
    assert validate_generated_code_semantic_review_packet(review_packet) == []
    first_dimension = review_packet["dimension_reviews"][0]
    assert first_dimension["dimension"] == (
        GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS[0]
    )
    assert "evidence_citations" not in first_dimension
    assert "evidence_refs" not in first_dimension
    assert "artifact_citations" not in first_dimension
    assert review_packet["review_input_fingerprint"] == stable_hash(
        materialization["review_material"]
    )


def test_review_authority_is_task_bound_and_repair_scope_specific() -> None:
    prior_finding_id = "generated_code_semantic_finding:parent"
    interface_id = "estimator_interface_contract:test"
    material = {
        "inherited_repair_obligations": {
            "active_prior_finding_ledger": [
                {
                    "finding_id": prior_finding_id,
                    "status": "UNRESOLVED",
                    "finding": {"summary": "Repair the parent implementation."},
                },
                {
                    "finding_id": prior_finding_id,
                    "status": "UNRESOLVED",
                    "finding": {"summary": "Duplicate legacy ledger row."},
                },
            ]
        },
        "source_responsibility_contract": {
            "assigned_empirical_metric_requirements": [
                {
                    "requirement_id": "metric:algorithm-owned",
                    "metric_semantics": "An Algorithm-owned metric.",
                }
            ],
            "sibling_only_requirement_refs": [
                {
                    "requirement_id": "metric:simulation-only",
                    "target_subsystems": ["SimulationEngineer"],
                }
            ],
        },
        "coding_agent_proposal_packet": {
            "implementation_gaps": [
                {
                    "estimator_id": "generated-estimator",
                    "status": "REQUIRES_GENERATED_ADAPTER",
                    "reason": "Planning state that is stale after execution.",
                }
            ],
            "implementation_targets": [
                {
                    "estimator_id": "generated-estimator",
                    "adapter_strategy": "Implement the declared interface.",
                    "estimator_interface_contract_id": interface_id,
                    "estimator_interface_contract_authority": {
                        "source_estimator_ref": (
                            "theory#/estimator_specs/0/"
                            "estimator_interface_contract"
                        )
                    },
                    "estimator_interface_contract": {
                        "request_fields": [
                            {
                                "name": "observations",
                                "meaning": "Observed sample supplied per replicate.",
                            }
                        ],
                        "response_fields": [
                            {
                                "name": "estimate",
                                "meaning": "The estimator output.",
                            }
                        ],
                    },
                }
            ],
            "simulation_targets": [
                {
                    "procedure_id": "sim_1_generic_procedure",
                    "simulation_goal": "Evaluate the frozen procedure.",
                }
            ],
            "theory_trace_alignment_contract": {
                "supported_derivation_steps": ["derivation:one"],
            },
        },
    }

    contract = generated_code_semantic_review_authority_contract(material)
    rows = {row["authority_ref"]: row for row in contract["authority_rows"]}

    assert contract["active_prior_finding_ids"] == [prior_finding_id]
    assert "requirement:metric:simulation-only" not in rows
    assert "implementation_gap:generated-estimator" not in rows
    assert rows["implementation_target:generated-estimator"][
        "allowed_repair_scopes"
    ] == ["source_code"]
    assert rows["simulation_target:sim_1_generic_procedure"][
        "allowed_repair_scopes"
    ] == ["source_code"]
    assert rows["requirement:metric:algorithm-owned"][
        "allowed_repair_scopes"
    ] == ["source_code", "upstream_metric_contract"]
    interface_ref = f"estimator_interface_contract:{interface_id}"
    assert rows[interface_ref]["locator"] == (
        "/estimator_specs/0/estimator_interface_contract"
    )
    assert rows[interface_ref]["allowed_repair_scopes"] == [
        "source_code",
        "upstream_theory",
    ]
    assert rows[f"prior_finding:{prior_finding_id}"][
        "allowed_repair_scopes"
    ] == ["source_code"]

    schema = generated_code_semantic_review_json_schema(material)
    prior_schema = schema["properties"]["prior_finding_reviews"]
    assert prior_schema["minItems"] == prior_schema["maxItems"] == 1
    assert "finding_id" not in schema["$defs"]["prior_finding_review"][
        "properties"
    ]
    assert "current_finding" in schema["$defs"]["prior_finding_review"][
        "properties"
    ]
    assert "requirement:metric:simulation-only" not in schema["$defs"][
        "artifact_delta"
    ]["properties"]["obligation_ref"]["enum"]


def test_schema_v9_rejects_authority_for_the_wrong_repair_scope(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    result = subsystem.run(task, blackboard)
    packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    tampered = json.loads(json.dumps(packet))
    tampered["findings"][0]["repair_scope"] = "upstream_theory"
    tampered["reviewed_source_assessment"] = "ALIGNED"
    tampered["source_theory_assessment"] = "THEORY_REVISION_REQUIRED"
    tampered["repair_scope"] = "upstream_theory"
    tampered["repair_scopes"] = ["upstream_theory"]
    tampered["repair_plan"] = [
        {
            "sequence": 1,
            "repair_scope": "upstream_theory",
            "repair_owner": "ArchitectCoordinator",
        }
    ]
    tampered["repair_owner"] = "ArchitectCoordinator"

    errors = validate_generated_code_semantic_review_packet(tampered)

    assert any(
        "authority_ref that permits its repair_scope" in error
        for error in errors
    )


def _prior_finding_review_inputs() -> tuple[
    dict[str, object],
    dict[str, object],
    str,
]:
    prior_finding_id = "generated_code_semantic_finding:parent"
    replan = {
        "artifact_kind": "RuntimeGeneratedCodeSemanticReviewReplanContext",
        "question_id": _question().id,
        "source_subsystem": "SimulationEvaluator",
        "repair_target_subsystem": "AlgorithmEngineer",
        "review_packet_id": "review:parent",
        "review_packet_hash": "review-hash:parent",
        "review_execution_id": "review-execution:parent",
        "findings": [
            {
                "finding_id": prior_finding_id,
                "severity": "high",
                "category": "dependency_interface",
                "summary": "The dependency response violates its interface.",
                "required_change": "Repair the dependency response.",
                "repair_scope": "upstream_generated_dependency",
                "evidence_refs": [
                    "upstream_generated_dependency#/exact_source_code"
                ],
            }
        ],
    }
    work_order = {
        "question_id": _question().id,
        "repair_task": {
            "inputs": {
                "architect_context": {
                    "runtime_generated_code_semantic_review_replan": replan,
                }
            }
        },
    }
    inherited = _runtime_generated_code_semantic_review_inherited_obligations(
        work_order=work_order,
        source_subsystem="AlgorithmEngineer",
    )
    material = {
        "confirmatory_empirical_evidence_eligible": True,
        "inherited_repair_obligations": inherited,
        "source_responsibility_contract": {
            "assigned_empirical_metric_requirements": [],
            "sibling_only_requirement_refs": [
                {
                    "requirement_id": "metric:simulation-only",
                    "target_subsystems": ["SimulationEngineer"],
                }
            ],
        },
        "coding_agent_proposal_packet": {
            "implementation_targets": [
                {
                    "estimator_id": "generated-estimator",
                    "adapter_strategy": "Repair the declared interface.",
                }
            ]
        },
        "exact_executed_artifacts": [
            {
                "artifact_id": "generated-artifact:fresh",
                "exact_source_code": "def run_sandbox():\n    return {'ok': True}\n",
                "exact_result": {"ok": True},
            }
        ],
    }
    lineage = {
        "source_subsystem": "AlgorithmEngineer",
        "source_agent": "LLMAlgorithmEngineerAgent",
        "work_order_id": "work-order:fresh",
        "work_order_hash": "work-order-hash:fresh",
        "source_manifest_id": "algorithm-manifest:fresh",
        "source_manifest_hash": "algorithm-manifest-hash:fresh",
        "reviewed_artifacts": [],
    }
    return material, lineage, prior_finding_id


def test_schema_v9_requires_review_of_every_inherited_finding() -> None:
    material, lineage, prior_finding_id = _prior_finding_review_inputs()
    assert material["inherited_repair_obligations"][
        "required_prior_finding_ids"
    ] == [prior_finding_id]
    reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(_review_response(accept=True)),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )

    with pytest.raises(PacketValidationError) as exc_info:
        reviewer.review(
            question=_question(),
            review_material=material,
            trusted_lineage=lineage,
        )

    assert any(
        "prior_finding_reviews must cover every active prior finding_id"
        in error
        for error in exc_info.value.errors
    )


def test_schema_v9_closes_or_preserves_inherited_finding_identity() -> None:
    material, lineage, prior_finding_id = _prior_finding_review_inputs()
    prior_review = {
        "status": "UNRESOLVED",
        "rationale": "The fresh source still violates the parent interface.",
        "evidence_citations": [
            {
                "artifact_role": "generated_source_artifact",
                "locator": "/exact_executed_artifacts/0/exact_source_code",
            }
        ],
        "current_finding": None,
    }
    unresolved_response = _review_response(
        accept=False,
        repair_scope="source_code",
    )
    continuation = deepcopy(unresolved_response["findings"][0])
    continuation.pop("repair_scope", None)
    continuation.pop("prior_finding_id", None)
    continuation.pop("authority_refs", None)
    continuation.pop("evidence_citations", None)
    continuation["artifact_delta"].pop("obligation_ref", None)
    continuation["artifact_delta"].pop("obligation_kind", None)
    unresolved_response["prior_finding_reviews"] = [
        {**prior_review, "current_finding": continuation}
    ]
    unresolved_response["findings"] = []
    unresolved = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(unresolved_response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    ).review(
        question=_question(),
        review_material=material,
        trusted_lineage=lineage,
    )

    assert unresolved["findings"][0]["finding_id"] == prior_finding_id
    assert unresolved["findings"][0]["artifact_delta"][
        "obligation_ref"
    ] == f"prior_finding:{prior_finding_id}"
    assert unresolved["prior_finding_identity_bindings"][0][
        "identity_source"
    ] == "prior_finding_reviews_ordered_index"
    assert unresolved["prior_finding_identity_bindings"][0][
        "runtime_selected_semantics"
    ] is False
    assert unresolved["active_unresolved_finding_ids"] == [prior_finding_id]

    resolved_response = _review_response(accept=True)
    resolved_response["prior_finding_reviews"] = [
        {
            **prior_review,
            "status": "RESOLVED_BY_CURRENT_ARTIFACT",
            "rationale": "The fresh source now satisfies the parent interface.",
            "current_finding": None,
        }
    ]
    resolved = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(resolved_response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    ).review(
        question=_question(),
        review_material=material,
        trusted_lineage=lineage,
    )

    assert resolved["active_unresolved_finding_ids"] == []
    assert resolved["cumulative_finding_ledger"][0]["status"] == (
        "RESOLVED_BY_CURRENT_ARTIFACT"
    )

    legacy_citation_response = json.loads(json.dumps(resolved_response))
    legacy_citation_response["prior_finding_reviews"][0][
        "evidence_citations"
    ][0]["locator"] = "/exact_executed_artifacts/0/missing_field"
    legacy_citation = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(legacy_citation_response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    ).review(
        question=_question(),
        review_material=material,
        trusted_lineage=lineage,
    )
    prior_row = legacy_citation["prior_finding_reviews"][0]
    assert "model_requested_evidence_citations" not in prior_row
    assert prior_row["evidence_citations"] == [
        {
            "artifact_role": "generated_source_artifact",
            "locator": "/exact_executed_artifacts/0/exact_source_code",
        }
    ]
    assert legacy_citation["prior_finding_identity_bindings"][0][
        "runtime_selected_semantics"
    ] is False


def test_schema_excludes_prior_authority_from_new_finding_slots() -> None:
    material, _lineage, prior_finding_id = _prior_finding_review_inputs()

    schema = generated_code_semantic_review_json_schema(material)
    budget = _generated_code_semantic_review_finding_budget(material)

    authority_enum = schema["$defs"]["artifact_delta"]["properties"][
        "obligation_ref"
    ]["enum"]
    assert f"prior_finding:{prior_finding_id}" not in authority_enum
    assert schema["properties"]["findings"]["maxItems"] == 4
    assert budget == {
        "max_new_findings": 4,
        "active_prior_finding_count": 1,
        "max_normalized_findings": 5,
        "prior_continuations_consume_new_finding_budget": False,
    }


def test_schema_v14_strips_redundant_dimension_citations(
    tmp_path: Path,
) -> None:
    response = _review_response(accept=True)
    response["dimension_reviews"][0]["evidence_citations"][0][
        "locator"
    ] = "exact_executed_artifacts/0/exact_source_code"
    reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    subsystem.reviewer = reviewer

    result = subsystem.run(task, blackboard)

    review_packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    first_dimension = review_packet["dimension_reviews"][0]
    assert "evidence_citations" not in first_dimension
    assert validate_generated_code_semantic_review_packet(review_packet) == []


def test_runtime_derives_finding_citations_from_model_selected_refs(
    tmp_path: Path,
) -> None:
    response = _review_response(accept=False, repair_scope="source_code")
    response["findings"][0]["evidence_citations"] = [
        citation
        for citation in response["findings"][0]["evidence_citations"]
        if citation["artifact_role"] != "generated_source_artifact"
    ]
    reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    subsystem.reviewer = reviewer

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE", result.observations[0].payload[
        "validation_errors"
    ]
    packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert packet["findings"][0]["evidence_citations"] == [
        {
            "artifact_role": "generated_source_artifact",
            "locator": packet["findings"][0]["artifact_delta"][
                "current_artifact_locator"
            ],
        },
        {
            "artifact_role": "generated_source_artifact",
            "locator": (
                "/coding_agent_proposal_packet/implementation_targets/0"
            ),
        },
    ]


def test_schema_v14_strips_legacy_duplicate_dimension_fields(
    tmp_path: Path,
) -> None:
    response = _review_response(accept=True)
    first_dimension = response["dimension_reviews"][0]
    first_dimension.pop("evidence_citations")
    first_dimension["evidence_refs"] = [
        "generated_source_artifact#/exact_executed_artifacts"
    ]
    first_dimension["artifact_citations"] = [
        "generated_source_artifact"
    ]
    reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    subsystem.reviewer = reviewer

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == "GeneratedCodeSemanticReviewPacket"
    )
    first_dimension = packet["dimension_reviews"][0]
    assert "evidence_refs" not in first_dimension
    assert "artifact_citations" not in first_dimension


def test_runtime_persists_full_generated_review_validation_replay_lineage(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    repair_history = [
        {
            "attempt_index": 0,
            "model": LIVE_EVALUATION_CLAUDE_MODEL,
            "provider": "anthropic",
            "ok": False,
            "errors": ["missing current artifact locator"],
            "response_metadata": {
                "provider_stop_reason": "end_turn",
                "provider_usage": {"input_tokens": 123, "output_tokens": 45},
            },
        }
    ]
    invalid_packet = {
        "packet_id": "generated_code_semantic_review:invalid",
        "review_input_fingerprint": "review-input:invalid",
        "model_requested_overall_verdict": "ACCEPT",
        "overall_verdict": "REVISE",
        "repair_scope": "source_code",
        "repair_scopes": ["source_code"],
        "repair_owner": "AlgorithmEngineer",
        "dimension_reviews": [
            {
                "dimension": "experiment_non_vacuity_and_identifiability",
                "status": "PASS",
            }
        ],
        "findings": [],
        "repair_instructions": [],
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
    }

    class InvalidReviewer:
        def review(self, **_kwargs):
            raise PacketValidationError(
                validation_label="generated-code semantic review packet",
                attempts=1,
                errors=[
                    "semantic review dimension experiment_non_vacuity_and_identifiability "
                    "cites a missing current artifact value"
                ],
                history=repair_history,
                last_invalid_packet=invalid_packet,
            )

    subsystem.reviewer = InvalidReviewer()
    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    failure = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewValidationFailure"
    )
    assert failure["llm_json_repair_history"] == repair_history
    assert failure["last_invalid_packet_fingerprint"] == stable_hash(
        invalid_packet
    )
    assert failure["last_invalid_review_projection"]["dimension_reviews"] == (
        invalid_packet["dimension_reviews"]
    )
    assert failure["review_input_fingerprint"]
    assert failure["execution_evidence_status"].endswith(
        "NOT_EXECUTION_EVIDENCE"
    )
    assert failure["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")
    assert result.observations[0].payload["failure_id"] == failure["failure_id"]


def test_schema_v8_binds_fixed_dimension_object_keys(
    tmp_path: Path,
) -> None:
    response = _review_response(accept=True)
    response["dimension_reviews"] = {
        dimension: row
        for dimension, row in zip(
            GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS,
            response["dimension_reviews"],
            strict=True,
        )
    }
    reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    subsystem.reviewer = reviewer

    result = subsystem.run(task, blackboard)

    review_packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert [
        row["dimension"] for row in review_packet["dimension_reviews"]
    ] == list(GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS)
    assert validate_generated_code_semantic_review_packet(review_packet) == []

    tampered = json.loads(json.dumps(review_packet))
    tampered["dimension_reviews"][0]["dimension"] = (
        "model_invented_dimension"
    )
    assert any(
        "dimension identity must be runtime-derived" in error
        for error in validate_generated_code_semantic_review_packet(tampered)
    )


def test_runtime_requires_one_concrete_scope_alongside_advisory_findings() -> None:
    review_packet = {
        "repair_scope": "source_code",
        "repair_scopes": ["source_code"],
    }

    mixed = _runtime_generated_code_authoritative_repair_routing(
        source_subsystem="AlgorithmEngineer",
        review_packet=review_packet,
        routed_findings=[
            {"repair_scope": "source_code"},
            {"repair_scope": "none"},
        ],
    )
    advisory_only = _runtime_generated_code_authoritative_repair_routing(
        source_subsystem="AlgorithmEngineer",
        review_packet=review_packet,
        routed_findings=[{"repair_scope": "none"}],
    )

    assert mixed["repair_scope"] == "source_code"
    assert mixed["repair_scopes"] == ["source_code"]
    assert mixed["ownership_resolved"] is True
    assert advisory_only["repair_scope"] == "unresolved"
    assert advisory_only["repair_scopes"] == ["unresolved"]
    assert advisory_only["ownership_resolved"] is False


def test_runtime_uses_bounded_source_frontier_with_mixed_unresolved_ownership() -> None:
    routed = _runtime_generated_code_authoritative_repair_routing(
        source_subsystem="SimulationEvaluator",
        review_packet={
            "repair_scope": "upstream_theory",
            "repair_scopes": ["upstream_theory", "source_code"],
        },
        routed_findings=[
            {"repair_scope": "upstream_generated_dependency"},
            {"repair_scope": "unresolved"},
            {"repair_scope": "source_code"},
        ],
    )

    assert routed["repair_scope"] == "source_code"
    assert routed["repair_scopes"] == [
        "source_code",
        "upstream_generated_dependency",
        "unresolved",
    ]
    assert routed["repair_owner"] == "SimulationEvaluator"
    assert routed["ownership_resolved"] is False
    assert routed["partial_repair_frontier"] is True
    assert routed["deferred_unresolved_ownership"] is True


def test_simulation_review_separates_immutable_dependency_from_consumer() -> None:
    dependency_source = (
        "def run_estimator(request):\n"
        "    return {'estimate': request['value']}\n"
    )
    dependency_result = {"estimate": 1.0}
    proposal = {
        "packet_id": "simulation-proposal:dependency-consumer",
        "simulation_targets": [{"simulation_id": "SIM1"}],
        "upstream_algorithm_handoff": {
            "algorithm_sandbox_manifest_id": "algorithm-manifest:parent",
            "algorithm_sandbox_manifest_hash": "algorithm-manifest-hash",
            "semantic_review_execution_id": "algorithm-review-execution:parent",
            "semantic_review_packet_id": "algorithm-review:parent",
            "exact_algorithm_artifacts": [
                {
                    "estimator_id": "EST1",
                    "language": "python",
                    "dependencies": [],
                    "estimator_interface_contract_authority": {
                        "owner_agent": "TheoryDeveloper",
                        "transport_status": "RUNTIME_BOUND_FROM_THEORY",
                    },
                    "exact_source_code": dependency_source,
                    "exact_source_hash": stable_hash(dependency_source),
                    "exact_smoke_result": dependency_result,
                    "exact_smoke_result_hash": stable_hash(dependency_result),
                }
            ],
        },
    }
    trusted_handoff = json.loads(
        json.dumps(proposal["upstream_algorithm_handoff"])
    )
    proposal["upstream_algorithm_handoff"]["exact_algorithm_artifacts"][0][
        "exact_smoke_result"
    ] = {"estimate": 999.0}

    consumer_projection = generated_code_semantic_review_proposal_projection(
        source_subsystem="SimulationEvaluator",
        proposal_packet=proposal,
        assigned_requirements=[],
    )
    dependency_projection = (
        generated_code_semantic_review_upstream_dependency_projection(
            source_subsystem="SimulationEvaluator",
            upstream_algorithm_handoff=trusted_handoff,
        )
    )

    assert dependency_source not in json.dumps(consumer_projection)
    assert consumer_projection["upstream_algorithm_handoff"][
        "exact_algorithm_artifact_refs"
    ] == [
        {
            "artifact_id": "EST1",
            "exact_source_hash": stable_hash(dependency_source),
        }
    ]
    assert dependency_projection["dependency_owner_subsystem"] == (
        "AlgorithmEngineer"
    )
    assert dependency_projection["current_source_may_not_modify_dependency"] is True
    assert dependency_projection["exact_dependency_artifacts"][0][
        "exact_source_code"
    ] == dependency_source
    assert dependency_projection["exact_dependency_artifacts"][0][
        "exact_result"
    ] == dependency_result
    assert dependency_projection["exact_dependency_artifacts"][0][
        "estimator_interface_contract_authority"
    ]["owner_agent"] == "TheoryDeveloper"

    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material={
            "confirmatory_empirical_evidence_eligible": True,
            "upstream_generated_dependency": dependency_projection,
        },
    )
    assert "upstream_generated_dependency" in prompt
    assert "do not ask the consumer to compensate" in prompt


def test_runtime_routes_upstream_dependency_to_algorithm_engineer() -> None:
    routed = _runtime_generated_code_authoritative_repair_routing(
        source_subsystem="SimulationEvaluator",
        review_packet={
            "repair_scope": "source_code",
            "repair_scopes": ["source_code"],
        },
        routed_findings=[
            {"repair_scope": "upstream_generated_dependency"},
            {"repair_scope": "none"},
        ],
    )

    assert routed["repair_scope"] == "upstream_generated_dependency"
    assert routed["repair_scopes"] == ["upstream_generated_dependency"]
    assert routed["repair_owner"] == "AlgorithmEngineer"
    assert routed["repair_plan"] == [
        {
            "sequence": 1,
            "repair_scope": "upstream_generated_dependency",
            "repair_owner": "AlgorithmEngineer",
        }
    ]
    assert routed["ownership_resolved"] is True


def test_nonpass_dimension_keeps_low_severity_finding_actionable(
    tmp_path: Path,
) -> None:
    _, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    response = _review_response(accept=False, repair_scope="source_code")
    response["findings"][0]["severity"] = "low"
    subsystem = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=LLMGeneratedCodeSemanticReviewerAgent(
            provider=StaticJSONGeneratorBackend(response),
            config=GeneratedCodeSemanticReviewerConfig(
                provider_name="static",
                model=LIVE_EVALUATION_CLAUDE_MODEL,
                model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
                max_repair_attempts=0,
            ),
        ),
        max_revisions=1,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    review_packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert review_packet["overall_verdict"] == "REVISE"
    assert review_packet["repair_scope"] == "source_code"
    assert review_packet["findings"][0]["repair_scope"] == "source_code"
    assert review_packet["findings"][0][
        "model_requested_repair_scope"
    ] == "source_code"


def test_full_packet_regeneration_exposes_unclosed_decision_without_selecting_owner(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="source_code",
    )
    response = _review_response(accept=True)
    response = {
        "prior_finding_reviews": [],
        "dimension_reviews": {
            dimension: dict(row)
            for dimension, row in zip(
                GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS,
                response["dimension_reviews"],
                strict=True,
            )
        },
        "findings": [
            {
                "severity": "high",
                "category": "semantic_uncertainty",
                "summary": "The current measurement judgment is unresolved.",
                "required_change": (
                    "Repair the artifact supported by the cited evidence."
                ),
                "repair_scope": "none",
                "prior_finding_id": "",
                "authority_refs": [],
                "artifact_delta": {
                    "obligation_ref": (
                        "implementation_target:generated-estimator"
                    ),
                    "obligation_kind": "implementation_target",
                    "current_artifact_role": "generated_source_artifact",
                    "current_artifact_locator": (
                        "/exact_executed_artifacts/0/exact_result"
                    ),
                    "current_behavior": "The current judgment is unresolved.",
                    "required_behavior": "No repair owner is yet established.",
                    "observable_change": (
                        "A repaired artifact would implement the cited target."
                    ),
                    "before_after_semantically_equivalent": False,
                },
                "evidence_citations": [
                        {
                            "artifact_role": "generated_source_artifact",
                            "locator": "/exact_executed_artifacts/0/exact_result",
                        },
                        {
                            "artifact_role": "generated_source_artifact",
                            "locator": (
                                "/coding_agent_proposal_packet/"
                                "implementation_targets/0"
                            ),
                        }
                ],
            }
        ],
        "repair_instructions": [
            "Resolve the exact implementation mismatch before acceptance."
        ],
    }
    response["dimension_reviews"]["metric_semantics_alignment"].update(
        {
            "status": "UNCERTAIN",
            "rationale": (
                "The cited result leaves a mandatory implementation question open."
            ),
        }
    )

    class DecisionClosureRegenerationBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []
            self.repair_payload: dict[str, object] = {}

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = response
            else:
                self.repair_payload = json.loads(
                    request.user_prompt.split("\n\n", 1)[1]
                )
                payload = deepcopy(response)
                payload["findings"][0]["repair_scope"] = "source_code"
                payload["findings"][0]["authority_refs"] = [
                    "implementation_target:generated-estimator"
                ]
            return GeneratorResponse(
                text=json.dumps(payload),
                provider=self.provider_name,
                model=request.model,
            )

    backend = DecisionClosureRegenerationBackend()
    subsystem.reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=backend,
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="anthropic",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=1,
        ),
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE", result.observations
    assert len(backend.requests) == 2
    assert backend.requests[1].metadata["json_repair_mode"] == (
        "full_packet_regeneration"
    )
    assert "subsystem_repair_context" not in backend.repair_payload
    assert backend.repair_payload["original_request"] == (
        backend.requests[0].user_prompt
    )
    assert json.loads(
        backend.repair_payload["previous_candidate"]
    ) == response
    assert backend.repair_payload["local_validation_errors"]
    assert any(
        "Rewrite the full JSON object from scratch" in instruction
        for instruction in backend.repair_payload["regeneration_requirements"]
    )
    assert not any(
        "Close the decision in one evidence-based direction" in instruction
        for instruction in backend.repair_payload["regeneration_requirements"]
    )
    review_packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert review_packet["overall_verdict"] == "REVISE"
    assert review_packet["repair_scope"] == "source_code"
    assert review_packet["findings"][0]["repair_scope"] == "source_code"


def test_actionable_finding_drives_revision_without_duplicate_dimension_verdict(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="source_code",
    )
    response = _review_response(accept=False, repair_scope="source_code")
    for row in response["dimension_reviews"]:
        row["status"] = "PASS"
    finding = response["findings"][0]
    finding["severity"] = "medium"
    obligation_ref = finding["artifact_delta"]["obligation_ref"]
    obligation_kind = finding["artifact_delta"].pop("obligation_kind")
    current_citation = {
        "artifact_role": finding["artifact_delta"]["current_artifact_role"],
        "locator": finding["artifact_delta"]["current_artifact_locator"],
    }
    finding.pop("authority_refs")
    finding.pop("evidence_citations")
    subsystem.reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE", result.observations
    packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == "GeneratedCodeSemanticReviewPacket"
    )
    assert packet["overall_verdict"] == "REVISE"
    assert packet["repair_scope"] == "source_code"
    assert packet["findings"][0]["authority_refs"] == [obligation_ref]
    assert packet["findings"][0]["artifact_delta"]["obligation_kind"] == (
        obligation_kind
    )
    assert current_citation in packet["findings"][0]["evidence_citations"]


def test_schema_v14_ignores_prompt_only_dimension_citation(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        metric_failed=True,
    )
    response = _review_response(accept=False, repair_scope="source_code")
    response["dimension_reviews"][0]["evidence_citations"] = [
        {
            "artifact_role": "generated_source_artifact",
            "locator": "/runtime_metric_gate_projection/0",
        }
    ]
    subsystem.reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert "evidence_citations" not in packet["dimension_reviews"][0]


def test_full_packet_regeneration_exposes_exact_severity_enum(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="source_code",
    )
    response = _review_response(accept=False, repair_scope="source_code")
    response["findings"][0]["severity"] = "major"

    class SeverityRegenerationBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []
            self.repair_payloads: list[dict[str, object]] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = response
            else:
                repair_payload = json.loads(
                    request.user_prompt.split("\n\n", 1)[1]
                )
                self.repair_payloads.append(repair_payload)
                payload = deepcopy(response)
                payload["findings"][0]["severity"] = (
                    "important" if len(self.requests) == 2 else "high"
                )
            return GeneratorResponse(
                text=json.dumps(payload),
                provider=self.provider_name,
                model=request.model,
            )

    backend = SeverityRegenerationBackend()
    subsystem.reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=backend,
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="anthropic",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=2,
        ),
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert len(backend.requests) == 3
    assert all(
        request.model == LIVE_EVALUATION_CLAUDE_MODEL
        for request in backend.requests
    )
    assert all(
        request.metadata["json_repair_mode"] == "full_packet_regeneration"
        for request in backend.requests[1:]
    )
    assert all(
        request.schema == backend.requests[0].schema
        for request in backend.requests[1:]
    )
    assert "subsystem_repair_context" not in backend.repair_payloads[-1]
    assert "important" in backend.repair_payloads[-1][
        "previous_candidate"
    ]
    assert any(
        "severity" in error
        for error in backend.repair_payloads[-1]["local_validation_errors"]
    )


def test_mixed_semantic_assessments_follow_reviewer_scopes(
    tmp_path: Path,
) -> None:
    _, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    response = _review_response(accept=False, repair_scope="source_code")
    # Legacy aggregate fields are deliberately contradictory; findings are the
    # only LLM-authored repair hypothesis in the current schema.
    response["reviewed_source_assessment"] = "ALIGNED"
    response["source_theory_assessment"] = "THEORY_REVISION_REQUIRED"
    response["frozen_metric_contract_assessment"] = (
        "NOT_APPLICABLE_EXPLORATORY"
    )
    repaired_findings = [
        *response["findings"],
        {
            "severity": "high",
            "category": "theory_premise",
            "summary": "The current theory omits a premise needed downstream.",
            "required_change": "Revise the theory packet before final acceptance.",
            "repair_scope": "upstream_theory",
            "prior_finding_id": "",
                "authority_refs": [
                    "theory_alignment:"
                + stable_hash(
                    {
                        "supported_derivation_steps": [
                            "theory:test:step:1"
                        ]
                    }
                    )[:20]
                ],
                "artifact_delta": {
                    "obligation_ref": (
                        "theory_alignment:"
                        + stable_hash(
                            {
                                "supported_derivation_steps": [
                                    "theory:test:step:1"
                                ]
                            }
                        )[:20]
                    ),
                    "obligation_kind": (
                        "proposal_consumed_theory_alignment"
                    ),
                    "current_artifact_role": "source_theory_packet",
                    "current_artifact_locator": "/derivation_steps",
                    "current_behavior": "The current premise is incomplete.",
                    "required_behavior": "The consumed theory trace must be complete.",
                    "observable_change": "A revised premise closes the cited gap.",
                    "before_after_semantically_equivalent": False,
                },
                "evidence_citations": [
                {
                        "artifact_role": "source_theory_packet",
                        "locator": "/derivation_steps",
                }
            ],
        },
    ]
    response["findings"] = [dict(row) for row in repaired_findings]
    response["findings"][1]["evidence_citations"] = []

    class MixedScopeBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            return GeneratorResponse(
                text=json.dumps(response),
                provider=self.provider_name,
                model=request.model,
            )

    backend = MixedScopeBackend()
    subsystem = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=LLMGeneratedCodeSemanticReviewerAgent(
            provider=backend,
            config=GeneratedCodeSemanticReviewerConfig(
                provider_name="anthropic",
                model=LIVE_EVALUATION_CLAUDE_MODEL,
                model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
                max_repair_attempts=1,
            ),
        ),
        max_revisions=1,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert len(backend.requests) == 1
    assert all(
        request.metadata["provider_structured_output"] is True
        for request in backend.requests
    )
    assert backend.requests[0].metadata["user_prompt_chars"] == len(
        backend.requests[0].user_prompt
    )
    assert backend.requests[0].metadata["review_material_json_chars"] > 0
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["overall_verdict"] == "REVISE"
    assert feedback["repair_scopes"] == ["source_code", "upstream_theory"]
    assert [row["repair_owner"] for row in feedback["repair_plan"]] == [
        "AlgorithmEngineer",
        "ArchitectCoordinator",
    ]
    review_packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert review_packet["reviewed_source_assessment"] == (
        "SOURCE_REPAIR_REQUIRED"
    )
    assert review_packet["frozen_metric_contract_assessment"] == (
        "VALID_AND_FEASIBLE"
    )
    assert review_packet["source_theory_assessment"] == (
        "THEORY_REVISION_REQUIRED"
    )
    assert review_packet["model_requested_reviewed_source_assessment"] == "ALIGNED"
    pending = result.next_task.inputs["architect_context"][
        "runtime_generated_code_semantic_review_pending_repair_plan"
    ]
    assert pending["pending_repair_scopes"] == ["upstream_theory"]
    assert "runtime_generated_code_semantic_review_replan" not in (
        result.next_task.inputs["architect_context"]
    )


def test_semantic_reviewer_schema_supports_anthropic_structured_output() -> None:
    from copy import deepcopy

    anthropic = pytest.importorskip("anthropic")

    transformed = anthropic.transform_schema(
        deepcopy(GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA)
    )

    assert transformed["additionalProperties"] is False
    assert transformed["$defs"]["finding"]["additionalProperties"] is False
    dimension_review_schema = transformed["properties"][
        "dimension_reviews"
    ]
    assert dimension_review_schema["type"] == "object"
    assert dimension_review_schema["additionalProperties"] is False
    assert set(dimension_review_schema["required"]) == set(
        GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS
    )
    assert set(dimension_review_schema["properties"]) == set(
        GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS
    )
    assert all(
        row == {"$ref": "#/$defs/dimension_review"}
        for row in dimension_review_schema["properties"].values()
    )
    dimension_definition = transformed["$defs"]["dimension_review"]
    finding_definition = transformed["$defs"]["finding"]
    assert set(dimension_definition["required"]) == {"status", "rationale"}
    assert "evidence_citation" not in transformed["$defs"]
    assert "evidence_refs" not in dimension_definition["properties"]
    assert "evidence_citations" not in dimension_definition["properties"]
    assert "evidence_citations" not in finding_definition["properties"]
    assert "artifact_citations" not in finding_definition["properties"]
    assert "authority_refs" not in finding_definition["properties"]
    assert "obligation_kind" not in transformed["$defs"][
        "artifact_delta"
    ]["properties"]
    assert set(transformed["required"]) == {
        "prior_finding_reviews",
        "dimension_reviews",
        "findings",
    }
    assert "overall_verdict" not in transformed["properties"]
    assert "reviewed_source_assessment" not in transformed["properties"]


def test_runtime_carries_pending_repair_until_owning_artifact_changes() -> None:
    theory_packet = {"packet_id": "theory:test", "claim": "unchanged"}
    evidence_contract = {"requirements": ["unchanged"]}
    review_material = {
        "theory_packet": theory_packet,
        "architect_frozen_evidence_contract": evidence_contract,
        "pending_repair_plan": {
            "pending_repair_plan_id": "pending-repair:test",
            "pending_repair_scopes": [
                "upstream_theory",
                "upstream_metric_contract",
            ],
            "theory_packet_hash": stable_hash(theory_packet),
            "architect_evidence_contract_hash": stable_hash(evidence_contract),
            "pending_findings": [
                {
                    "repair_scope": "upstream_theory",
                    "category": "theory",
                    "summary": "Revise the theory.",
                },
                {
                    "repair_scope": "upstream_metric_contract",
                    "category": "metric",
                    "summary": "Revise the metric contract.",
                },
            ],
        },
    }
    packet = {
        "source_theory_assessment": "SUFFICIENT_FOR_IMPLEMENTATION_REPAIR",
        "frozen_metric_contract_assessment": "VALID_AND_FEASIBLE",
    }

    active = generated_code_semantic_review_active_pending_repair_plan(
        review_material
    )

    assert active["active_repair_scopes"] == [
        "upstream_theory",
        "upstream_metric_contract",
    ]
    assert len(active["active_findings"]) == 2
    assert active["runtime_carries_obligation"] is True
    assert active["model_must_repeat_obligation"] is False
    assert generated_code_semantic_review_pending_plan_errors(
        packet=packet,
        review_material=review_material,
    ) == []
    projected_material = {
        **review_material,
        "theory_packet": {
            "packet_id": theory_packet["packet_id"],
            "theory_derivation_packet": {
                "derivation_steps": [{"id": "consumed-step"}]
            },
            "theory_review_projection": {
                "canonical_theory_packet_fingerprint": stable_hash(
                    theory_packet
                )
            },
        },
    }
    assert generated_code_semantic_review_active_pending_repair_plan(
        projected_material
    )["active_repair_scopes"] == [
        "upstream_theory",
        "upstream_metric_contract",
    ]
    changed_material = {
        **review_material,
        "theory_packet": {**theory_packet, "claim": "revised"},
        "architect_frozen_evidence_contract": {"requirements": ["revised"]},
    }
    assert generated_code_semantic_review_active_pending_repair_plan(
        changed_material
    )["active_repair_scopes"] == []
    assert generated_code_semantic_review_pending_plan_errors(
        packet=packet,
        review_material=changed_material,
    ) == []


def test_pending_metric_repair_uses_canonical_contract_fingerprint() -> None:
    canonical_contract = {
        "empirical_metric_requirements": [
            {"requirement_id": "simulation:sibling"}
        ]
    }
    projected_contract = {"empirical_metric_requirements": []}
    review_material = {
        "theory_packet": {"packet_id": "theory:test"},
        "architect_frozen_evidence_contract": projected_contract,
        "review_scope_projection": {
            "canonical_architect_evidence_contract_fingerprint": stable_hash(
                canonical_contract
            )
        },
        "pending_repair_plan": {
            "pending_repair_plan_id": "pending-repair:metric",
            "pending_repair_scopes": ["upstream_metric_contract"],
            "architect_evidence_contract_hash": stable_hash(
                canonical_contract
            ),
            "pending_findings": [
                {
                    "repair_scope": "upstream_metric_contract",
                    "category": "metric",
                    "summary": "Revise the canonical metric contract.",
                }
            ],
        },
    }

    active = generated_code_semantic_review_active_pending_repair_plan(
        review_material
    )

    assert active["active_repair_scopes"] == [
        "upstream_metric_contract"
    ]
    assert active["runtime_carries_obligation"] is True


def test_runtime_rejects_malformed_pending_plan_before_model_call(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    work_order["pending_repair_plan"] = {
        "pending_repair_plan_id": "pending-repair:malformed",
        "pending_repair_scopes": ["upstream_theory"],
        "theory_packet_hash": str(work_order["theory_packet_hash"]),
        "architect_evidence_contract_hash": stable_hash(
            work_order["architect_evidence_contract"]
        ),
        "pending_findings": [],
    }
    task.inputs["work_order_hash"] = stable_hash(work_order)

    class ProviderMustNotRun:
        provider_name = "static"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            del request
            self.calls += 1
            raise AssertionError("runtime-owned state must fail before model use")

    provider = ProviderMustNotRun()
    subsystem.reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=provider,
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=1,
        ),
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_input_invalid"
    )
    assert provider.calls == 0
    assert any(
        "pending repair scopes require owner-bound pending findings"
        in error
        for error in result.observations[0].payload["validation_errors"]
    )


def test_runtime_routes_pending_theory_after_fresh_source_review_accepts(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=True)
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    pending_plan = {
        "artifact_kind": (
            "RuntimeGeneratedCodeSemanticReviewPendingRepairPlan"
        ),
        "pending_repair_plan_id": "pending-repair:test",
        "question_id": _question().id,
        "source_subsystem": "AlgorithmEngineer",
        "pending_repair_scopes": ["upstream_theory"],
        "theory_packet_hash": str(work_order["theory_packet_hash"]),
        "architect_evidence_contract_hash": stable_hash(
            work_order["architect_evidence_contract"]
        ),
        "pending_findings": [
            {
                "severity": "high",
                "category": "theory_premise",
                "summary": "The unchanged theory premise still requires revision.",
                "required_change": "Revise the exact source-theory premise.",
                "repair_scope": "upstream_theory",
                "evidence_citations": [
                    {
                        "artifact_role": "source_theory_packet",
                        "locator": "/derivation_steps",
                    }
                ],
                "evidence_refs": [
                    "source_theory_packet#/derivation_steps"
                ],
                "artifact_citations": ["source_theory_packet"],
                "repair_ownership_certainty": "resolved",
            }
        ],
        "proof_evidence_status": (
            "GENERATED_CODE_SEMANTIC_REVIEW_PENDING_REPAIR_"
            "PLAN_NOT_PROOF_EVIDENCE"
        ),
    }
    work_order["pending_repair_plan"] = pending_plan
    task.inputs["work_order_hash"] = stable_hash(work_order)

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    review_packet = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    execution = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    )
    assert review_packet["overall_verdict"] == "ACCEPT"
    assert execution["reviewer_overall_verdict"] == "ACCEPT"
    assert execution["workflow_verdict"] == "REVISE"
    assert execution["semantic_review_accepted"] is False
    assert execution["runtime_carried_pending_repair"] is True
    assert execution["active_pending_repair_scopes"] == [
        "upstream_theory"
    ]
    assert execution["repair_routing_authority"] == (
        "GeneratedCodeSemanticReviewer+RuntimePendingRepairPlan"
    )
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["reviewer_overall_verdict"] == "ACCEPT"
    assert feedback["overall_verdict"] == "REVISE"
    assert feedback["repair_scope"] == "upstream_theory"
    assert feedback["findings"][0][
        "runtime_carried_pending_repair"
    ] is True


def test_generated_code_semantic_reviewer_routes_rejection_to_fresh_generation(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    assert result.next_task.task_id.startswith("semantic-review-revise:")
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["overall_verdict"] == "REVISE"
    assert feedback["findings"][0]["severity"] == "high"
    reviewed_source = feedback["reviewed_source_artifacts"][0]
    assert reviewed_source["exact_source_code_complete"] is True
    assert reviewed_source["exact_source_code"].endswith(
        "return run_estimator({'numerator': seed % 7, "
        "'denominator': max(replicates, 1)})\n"
    )
    assert reviewed_source["exact_source_hash"] == stable_hash(
        reviewed_source["exact_source_code"]
    )
    assert feedback["source_repair_contract"][
        "parent_source_manifest_hash"
    ]
    assert "repair_policy" not in feedback["source_repair_contract"]
    assert "required_repair" not in feedback
    assert result.next_task.inputs["generated_code_semantic_review_revision_count"] == 1
    handoff = result.next_task.inputs["architect_context"]["runtime_feedback_loop"][
        "direct_repair_handoff_contract"
    ]
    assert handoff["architect_pre_authorized"] is True
    assert handoff["source_reviewer_subsystem"] == (
        "GeneratedCodeSemanticReviewer"
    )
    assert handoff["target_repair_subsystem"] == "AlgorithmEngineer"
    assert handoff["target_task_id"] == result.next_task.task_id
    assert handoff["feedback_artifact_id"] == feedback[
        "semantic_review_packet_id"
    ]
    assert handoff["proof_evidence_status"] == "NOT_PROOF_EVIDENCE"


def test_changed_finding_cannot_reset_source_lineage_repair_budget(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    first = subsystem.run(task, blackboard)
    assert first.next_task is not None
    first_context = first.next_task.inputs["architect_context"]

    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    for task_field in ("repair_task", "deferred_next_task"):
        task_payload = dict(work_order[task_field])
        task_inputs = dict(task_payload["inputs"])
        task_inputs["architect_context"] = first_context
        task_payload["inputs"] = task_inputs
        work_order[task_field] = task_payload
    work_order["review_revision_count"] = 0

    changed_response = _review_response(accept=False)
    changed_response["findings"][0]["category"] = "data_generation"
    changed_reviewer = GeneratedCodeSemanticReviewerRuntimeSubsystem(
        reviewer=LLMGeneratedCodeSemanticReviewerAgent(
            provider=StaticJSONGeneratorBackend(changed_response),
            config=GeneratedCodeSemanticReviewerConfig(
                provider_name="static",
                model=LIVE_EVALUATION_CLAUDE_MODEL,
                model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
                max_repair_attempts=0,
            ),
        ),
        max_revisions=1,
    )
    second = changed_reviewer.run(
        AgentTask(
            task_id="semantic-review:changed-finding",
            owner_subsystem=task.owner_subsystem,
            objective=task.objective,
            inputs={
                **task.inputs,
                "architect_context": first_context,
                "work_order_hash": stable_hash(work_order),
            },
        ),
        blackboard,
    )

    assert second.status == "BLOCKED"
    assert second.next_task is None
    assert second.failure_classification == (
        "generated_code_semantic_review_lineage_budget_exhausted"
    )
    execution = next(
        row
        for row in second.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    )
    budget = execution["semantic_review_lineage_budget"]
    assert budget["source_local_repair_count"] == 1
    assert budget["source_architect_replan_count"] == 0
    assert budget["selected_action"] == "blocked"


def test_source_review_budget_exhaustion_does_not_reset_via_deferred_architect(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    deferred = dict(work_order["deferred_next_task"])
    deferred["task_id"] = "architect-metric-replan:test"
    deferred["owner_subsystem"] = "ArchitectCoordinator"
    deferred["objective"] = "Diagnose the cross-subsystem metric failure."
    deferred_inputs = dict(deferred["inputs"])
    deferred_inputs["environment_feedback"] = {
        "feedback_type": "runtime_metric_gate_feedback",
        "feedback_id": "metric-feedback:prior",
    }
    deferred_inputs["architect_context"] = {
        **dict(deferred_inputs.get("architect_context", {}) or {}),
        "runtime_metric_gate_replan": {
            "source_manifest_id": work_order["source_manifest_id"],
            "source_artifact_remains_unaccepted": True,
        },
    }
    deferred["inputs"] = deferred_inputs
    work_order["deferred_next_task"] = deferred
    work_order["review_revision_count"] = 1
    task.inputs["work_order_hash"] = stable_hash(work_order)

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_lineage_budget_exhausted"
    )
    assert result.next_task is None
    execution = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    )
    assert execution["semantic_review_lineage_budget"]["selected_action"] == (
        "blocked"
    )
    assert execution["semantic_review_accepted"] is False


def test_upstream_semantic_finding_routes_directly_to_architect(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_metric_contract",
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.failure_classification == (
        "generated_code_semantic_review_metric_protocol_revision_required"
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["repair_scope"] == "upstream_metric_contract"
    assert feedback["repair_owner_agent"] == "ArchitectCoordinator"
    replan = result.next_task.inputs["architect_context"][
        "runtime_generated_code_semantic_review_replan"
    ]
    assert replan["repair_scope"] == "upstream_metric_contract"
    assert replan["source_manifest_id"] == "algorithm_sandbox_manifest:test"
    assert replan["deferred_next_owner_subsystem"] == "FormalizationEvaluator"
    assert "fresh candidate run" in replan["protocol_revision_policy"]
    assert result.next_task.inputs[
        "generated_code_semantic_review_revision_count"
    ] == 0


def test_post_result_metric_protocol_revision_stops_current_candidate(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    review_result = subsystem.run(task, blackboard)
    assert review_result.next_task is not None

    class CoordinatorMustNotRun:
        metric_semantic_reviewer = None

        def __init__(self) -> None:
            self.calls = 0

        def propose(self, **_kwargs):
            self.calls += 1
            raise AssertionError("post-result protocol guard must run before replanning")

    coordinator = CoordinatorMustNotRun()
    guard = ArchitectCoordinatorRuntimeSubsystem(
        coordinator=coordinator,
        runtime_config=ResearchAgentRuntimeConfig(
            metric_protocol_max_fresh_candidate_revisions=0
        ),
    )

    result = guard.run(review_result.next_task, blackboard)

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert coordinator.calls == 0
    assert result.failure_classification == "evaluation_protocol_revision_required"
    manifest = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeEvaluationProtocolRevisionRequired"
    )
    assert manifest["disposition"] == "EVALUATION_PROTOCOL_REVISION_REQUIRED"
    assert manifest["current_candidate_acceptance_eligible"] is False
    assert manifest["post_result_protocol_mutation_allowed"] is False
    assert manifest["fresh_candidate_required"] is True
    assert manifest["source_requirement_set_id"]
    assert manifest["source_semantic_review_packet_id"] == (
        review_result.next_task.inputs["environment_feedback"][
            "semantic_review_packet_id"
        ]
    )
    assert manifest["pending_artifact_ids"]
    assert result.evidence_entries[0].status == (
        "CURRENT_CANDIDATE_BLOCKED_FRESH_PROTOCOL_RUN_REQUIRED"
    )


def test_post_result_metric_protocol_revision_starts_versioned_fresh_candidate(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    review_result = subsystem.run(task, blackboard)
    assert review_result.next_task is not None
    context = review_result.next_task.inputs["architect_context"]
    context["theory_packet_id"] = "theory:test"
    context["architect_metric_protocol_theory_material"] = {
        "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
        "source_theory_packet_id": "theory:test",
        "source_theory_packet_hash": "theory-hash",
        "theory_semantic_material": {"packet_id": "theory:test"},
        "execution_results_available": False,
    }
    context["architect_metric_protocol_gate"] = {
        "artifact_kind": "RuntimeArchitectMetricProtocolGate",
        "accepted_requirement_set_id": "metric-requirements:test",
        "execution_authorized": True,
        "consumed": True,
    }

    class CoordinatorMustNotRun:
        metric_semantic_reviewer = None

        def __init__(self) -> None:
            self.calls = 0

        def propose(self, **_kwargs):
            self.calls += 1
            raise AssertionError("fresh-candidate guard must route before proposal")

    coordinator = CoordinatorMustNotRun()
    guard = ArchitectCoordinatorRuntimeSubsystem(
        coordinator=coordinator,
        runtime_config=ResearchAgentRuntimeConfig(
            seed=41,
            metric_protocol_max_fresh_candidate_revisions=1,
        ),
    )

    result = guard.run(review_result.next_task, blackboard)

    assert result.status == "REROUTE"
    assert result.failure_classification == (
        "evaluation_protocol_fresh_candidate_requested"
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    assert coordinator.calls == 0
    manifest = next(iter(result.produced_artifacts.values()))
    assert manifest["fresh_candidate_auto_routed"] is True
    assert manifest["fresh_candidate_seed"] != 41
    assert manifest["source_requirement_set_id"]

    fresh_context = result.next_task.inputs["architect_context"]
    fresh_revision = fresh_context[
        "architect_metric_protocol_fresh_candidate_revision"
    ]
    assert fresh_revision["raw_execution_artifacts_included"] is False
    assert fresh_revision[
        "structural_feedback_may_summarize_prior_observations"
    ] is True
    assert fresh_revision["post_result_threshold_relaxation_allowed"] is False
    assert fresh_revision["source_requirement_rows"]
    assert fresh_revision["source_requirement_set_id"] == manifest[
        "source_requirement_set_id"
    ]
    assert fresh_revision["structural_review_findings"] == [
        {
            "source_finding_index": 0,
                "severity": "high",
                "category": "metric_semantics",
                "required_change": "Compute the frozen protocol quantity directly.",
        }
    ]
    assert "summary" not in fresh_revision["structural_review_findings"][0]
    assert "evidence_refs" not in fresh_revision[
        "structural_review_findings"
    ][0]
    assert fresh_context["runtime_candidate_seed"] == manifest[
        "fresh_candidate_seed"
    ]
    assert fresh_context["architect_runtime_plan"]["evidence_contract"][
        "empirical_metric_requirements"
    ] == []
    assert "runtime_generated_code_semantic_review_replan" not in fresh_context


def test_runtime_defers_separate_theory_finding_behind_required_source_repair(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="source_code",
    )
    response = _review_response(accept=False, repair_scope="source_code")
    response["findings"] = [
        *response["findings"],
        {
            "severity": "high",
            "category": "theory_premise",
            "summary": "A distinct mathematical premise needs reassessment.",
            "required_change": "Reassess the exact source-theory premise.",
            "repair_scope": "upstream_theory",
            "prior_finding_id": "",
                "authority_refs": [
                    "theory_alignment:"
                + stable_hash(
                    {
                        "supported_derivation_steps": [
                            "theory:test:step:1"
                        ]
                    }
                    )[:20]
                ],
                "artifact_delta": {
                    "obligation_ref": (
                        "theory_alignment:"
                        + stable_hash(
                            {
                                "supported_derivation_steps": [
                                    "theory:test:step:1"
                                ]
                            }
                        )[:20]
                    ),
                    "obligation_kind": (
                        "proposal_consumed_theory_alignment"
                    ),
                    "current_artifact_role": "source_theory_packet",
                    "current_artifact_locator": "/derivation_steps",
                    "current_behavior": "The premise needs reassessment.",
                    "required_behavior": "The consumed theory trace must be complete.",
                    "observable_change": "A revised premise changes the theory packet.",
                    "before_after_semantically_equivalent": False,
                },
                "evidence_citations": [
                {
                    "artifact_role": "source_theory_packet",
                    "locator": "/derivation_steps",
                }
            ],
        },
    ]
    response["repair_instructions"] = [
        "Repair the generated measurement path.",
        "Reassess the exact source-theory premise.",
    ]
    subsystem.reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )
    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["repair_scope"] == "source_code"
    assert feedback["repair_scopes"] == ["source_code", "upstream_theory"]
    assert [row["repair_owner"] for row in feedback["repair_plan"]] == [
        "AlgorithmEngineer",
        "ArchitectCoordinator",
    ]
    assert len(feedback["findings"]) == 1
    assert feedback["findings"][0]["repair_scope"] == "source_code"
    assert feedback["repair_instructions"] == [
        feedback["findings"][0]["required_change"]
    ]
    assert all(
        "source_theory_packet" not in instruction
        for instruction in feedback["repair_instructions"]
    )
    pending = result.next_task.inputs["architect_context"][
        "runtime_generated_code_semantic_review_pending_repair_plan"
    ]
    assert pending["pending_repair_scopes"] == ["upstream_theory"]
    assert len(pending["pending_findings"]) == 1
    assert pending["pending_findings"][0]["repair_scope"] == "upstream_theory"


def test_postexecution_reviewer_scopes_route_one_bounded_source_repair(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        capability_eval=True,
    )
    response = _review_response(accept=False, repair_scope="source_code")
    response["findings"].append(
        {
            "severity": "high",
            "category": "upstream_semantic_ambiguity",
            "summary": (
                "The current evidence does not yet isolate a theory premise from "
                "the executable measurement defect."
            ),
            "required_change": (
                "Reassess the theory premise after the concrete source repair."
            ),
            "repair_scope": "upstream_theory",
            "prior_finding_id": "",
                "authority_refs": [
                    "theory_alignment:"
                + stable_hash(
                    {
                        "supported_derivation_steps": [
                            "theory:test:step:1"
                        ]
                    }
                    )[:20]
                ],
                "artifact_delta": {
                    "obligation_ref": (
                        "theory_alignment:"
                        + stable_hash(
                            {
                                "supported_derivation_steps": [
                                    "theory:test:step:1"
                                ]
                            }
                        )[:20]
                    ),
                    "obligation_kind": (
                        "proposal_consumed_theory_alignment"
                    ),
                    "current_artifact_role": "source_theory_packet",
                    "current_artifact_locator": "/derivation_steps/0",
                    "current_behavior": "The premise remains ambiguous.",
                    "required_behavior": "The consumed theory trace must be complete.",
                    "observable_change": "A revised premise resolves the ambiguity.",
                    "before_after_semantically_equivalent": False,
                },
                    "evidence_citations": [
                    {
                        "artifact_role": "source_theory_packet",
                        "locator": "/derivation_steps/0",
                    },
                    {
                        "artifact_role": "source_theory_packet",
                        "locator": "/derivation_steps",
                    }
                ],
        }
    )
    response["repair_instructions"].append(
        "Keep the upstream ambiguity open for fresh independent review."
    )
    subsystem.reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model=LIVE_EVALUATION_CLAUDE_MODEL,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_repair_attempts=0,
        ),
    )
    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    assert result.failure_classification == "generated_code_semantic_review_revise"
    execution = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    )
    assert execution["repair_scope"] == "source_code"
    assert execution["repair_scopes"] == ["source_code", "upstream_theory"]
    assert execution["repair_scope_resolved"] is True
    assert execution["partial_repair_frontier"] is False
    assert execution["deferred_unresolved_ownership"] is False
    assert execution["semantic_review_lineage_budget"]["selected_action"] == (
        "local_repair"
    )


def test_upstream_theory_scope_remains_an_architect_replan_not_protocol_stop(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_theory",
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.failure_classification == (
        "generated_code_semantic_review_upstream_theory_repair_escalated_to_architect"
    )
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    assert result.next_task.inputs["environment_feedback"]["repair_scope"] == (
        "upstream_theory"
    )


def test_source_semantic_revision_budget_stops_without_deferred_architect(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(tmp_path, accept=False)
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    assert work_order["deferred_next_task"]["owner_subsystem"] == (
        "FormalizationEvaluator"
    )
    work_order["review_revision_count"] = 1
    task.inputs["work_order_hash"] = stable_hash(work_order)

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_lineage_budget_exhausted"
    )
    assert result.next_task is None


def test_metric_failing_but_executed_code_is_independently_reviewed(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        metric_failed=True,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "AlgorithmEngineer"
    materialization = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewMaterialization"
    )
    source_row = materialization["review_material"]["exact_executed_artifacts"][0][
        "source_row"
    ]
    assert source_row["prototype_status"] == "FAILED_METRIC_GATE"
    assert source_row["execution_smoke_passed"] is True
    assert source_row["smoke_passed"] is False


def test_coding_agent_prompts_preserve_independent_semantic_findings() -> None:
    rationale = (
        "The implemented update treats each observation as a fresh prior draw, "
        "which is not the joint mixture defined by the theory packet and changes "
        "the martingale being evaluated."
    )
    required_change = (
        "Use one shared latent parameter across the full sequence, compute the "
        "joint marginal likelihood, and rerun the unchanged frozen protocol."
    )
    parent_source = (
        "def run_sandbox(seed, replicates):\n"
        + "    values = []\n" * 1000
        + "    return {'tail_marker': 'FULL_PARENT_SOURCE_TAIL'}\n"
    )
    feedback = {
        "feedback_type": "generated_code_semantic_review_feedback",
        "feedback_source": "GeneratedCodeSemanticReviewer",
        "source_subsystem": "AlgorithmEngineer",
        "semantic_review_execution_id": "semantic-execution:test",
        "semantic_review_packet_id": "semantic-packet:test",
        "overall_verdict": "REVISE",
        "dimension_reviews": [
            {
                "dimension": "theory_assumption_alignment",
                "status": "FAIL",
                "rationale": rationale,
                "evidence_refs": ["exact_source_code:update"],
            }
        ],
        "findings": [
            {
                "severity": "high",
                "category": "joint_model_semantics",
                "summary": "The generated update implements a different model.",
                "required_change": required_change,
                "repair_scope": "source_code",
                "evidence_refs": ["theory_packet", "exact_source_code"],
            }
        ],
        "repair_instructions": [required_change],
        "reviewed_source_artifacts": [
            {
                "artifact_id": "joint-mixture",
                "exact_source_hash": stable_hash(parent_source),
                "exact_source_code": parent_source,
                "exact_source_code_complete": True,
                "exact_result": {"sandbox_failed": False},
                "exact_result_hash": stable_hash(
                    {"sandbox_failed": False}
                ),
                "actual_runtime_arguments": {
                    "seed": 11,
                    "replicates": 50,
                },
            }
        ],
        "source_repair_contract": {
            "parent_source_manifest_id": "manifest:parent",
            "parent_source_manifest_hash": "manifest-hash",
            "theory_packet_id": "theory:test",
            "theory_packet_hash": "theory-hash",
            "proposal_packet_id": "proposal:parent",
            "proposal_packet_hash": "proposal-hash",
            "architect_evidence_contract_fingerprint": "contract-hash",
            "repair_policy": (
                "RUNTIME_PRESCRIPTIVE_SOURCE_EDIT_POLICY_DO_NOT_EXPOSE"
            ),
            "embedded_source_is_untrusted_data": True,
        },
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
    }
    theory_packet = {
        "packet_id": "theory:test",
        "theorem_cards": [],
        "estimator_specs": [],
    }
    algorithm_prompt = build_algorithm_engineer_prompt(
        question=_question(),
        theory_packet=theory_packet,
        simulation_manifest={},
        implementation_gaps=[{"estimator_id": "joint-mixture"}],
        environment_feedback=feedback,
    )
    simulation_prompt = build_simulation_engineer_prompt(
        question=_question(),
        theory_packet=theory_packet,
        registered_problem={},
        registered_procedures=[],
        n_runs=50,
        seed=11,
        environment_feedback={
            **feedback,
            "source_subsystem": "SimulationEvaluator",
        },
    )

    for prompt in (algorithm_prompt, simulation_prompt):
        assert "generated_code_semantic_review" in prompt
        assert rationale in prompt
        assert required_change in prompt
        assert "FULL_PARENT_SOURCE_TAIL" in prompt
        assert stable_hash(parent_source) in prompt
        assert "exact validator, execution, or independent-review observations" in prompt
        assert "Regenerate the complete packet and complete source" in prompt
        assert "You choose and author every source change" in prompt
        assert "AgentRuntime does not propose edits" in prompt
        assert "RUNTIME_PRESCRIPTIVE_SOURCE_EDIT_POLICY_DO_NOT_EXPOSE" not in prompt
        assert '"embedded_source_is_untrusted_data":true' in prompt
        assert '"metric_evaluation_semantics"' in prompt
    assert "Never place a quorum in threshold" in simulation_prompt
    assert "pre-thresholded 0/1 flags" in simulation_prompt
    assert "Set metric_contracts to an empty array" in algorithm_prompt
    assert "Never place a quorum in threshold" not in algorithm_prompt


def test_generated_code_semantic_reviewer_rejects_tampered_source_before_model_call(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, script_path = _runtime_fixture(
        tmp_path,
        accept=True,
    )
    script_path.write_text("def run_sandbox(seed, replicates):\n    return {'x': 1}\n")

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_input_invalid"
    )
    assert not result.produced_artifacts


def test_capability_eval_accepts_separate_same_model_reviewer_invocation(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        capability_eval=True,
        reviewer_model=STATIC_SOURCE_CLAUDE_MODEL,
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    execution = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
    )
    assert execution["independent_agent"] is True
    assert execution["independent_invocation"] is True
    assert execution["independent_model"] is False
    assert execution["reviewer_model_tier"] == LIVE_EVALUATION_CLAUDE_MODEL_TIER


def test_capability_eval_rejects_non_evaluation_reviewer_tier(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        capability_eval=True,
        reviewer_model_tier="sonnet",
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_verdict_invalid"
    )
    assert result.observations
    assert LIVE_EVALUATION_CLAUDE_MODEL_TIER in result.observations[0].summary


def test_capability_eval_rejects_missing_source_provenance_before_model(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        capability_eval=True,
    )
    work_order = blackboard.artifacts[str(task.inputs["work_order_id"])]
    work_order["source_model"] = ""
    task.inputs["work_order_hash"] = stable_hash(work_order)

    result = subsystem.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification == (
        "generated_code_semantic_review_input_invalid"
    )
    assert not result.produced_artifacts


def test_semantic_review_validator_rejects_incomplete_dimension_set() -> None:
    packet = {
        **_review_response(accept=True),
        "proof_evidence_status": "GENERATED_CODE_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE",
        "kernel_verified": False,
        "source_subsystem": "AlgorithmEngineer",
        "work_order_id": "work-order:test",
        "work_order_hash": "hash",
        "source_manifest_id": "manifest:test",
        "source_manifest_hash": "hash",
        "review_input_fingerprint": "hash",
    }
    packet["dimension_reviews"] = packet["dimension_reviews"][:-1]

    errors = validate_generated_code_semantic_review_packet(packet)

    assert any("each required dimension exactly once" in error for error in errors)
    assert any("overall_verdict must be ACCEPT" in error for error in errors)


def test_semantic_review_validator_binds_upstream_scope_to_architect(
    tmp_path: Path,
) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=False,
        repair_scope="upstream_metric_contract",
    )
    result = subsystem.run(task, blackboard)
    packet = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind") == "GeneratedCodeSemanticReviewPacket"
    )
    assert validate_generated_code_semantic_review_packet(packet) == []

    packet["repair_owner"] = "AlgorithmEngineer"
    errors = validate_generated_code_semantic_review_packet(packet)
    assert any(
        "upstream semantic repair must route to ArchitectCoordinator" in error
        for error in errors
    )


def test_capability_scorecard_requires_both_independent_semantic_review_lanes() -> None:
    scorecard = _runtime_capability_scorecard(
        {
            "n_generated_code_semantic_review_work_orders": 2,
            "n_generated_code_semantic_review_executions": 2,
            "n_generated_code_semantic_review_accepted": 2,
            "n_generated_algorithm_semantic_review_accepted": 1,
            "n_generated_simulation_semantic_review_accepted": 1,
            "n_generated_code_semantic_review_independent_evaluation_model": 2,
            "n_live_generated_code_sandbox_executed": 1,
            "n_live_generated_simulation_sandbox_executed": 1,
        }
    )
    rows = {row["requirement_id"]: row for row in scorecard["rows"]}

    assert rows["generated_code_semantic_review_executed"]["passed"] is True
    assert rows["generated_algorithm_semantic_review_accepted"]["passed"] is True
    assert rows["generated_simulation_semantic_review_accepted"]["passed"] is True
    assert rows[
        "generated_code_semantic_review_independent_evaluation_model"
    ]["passed"] is True


def test_runtime_audit_recomputes_semantic_review_lineage(tmp_path: Path) -> None:
    subsystem, task, blackboard, _ = _runtime_fixture(
        tmp_path,
        accept=True,
        capability_eval=True,
    )
    result = subsystem.run(task, blackboard)
    artifacts = {**blackboard.artifacts, **result.produced_artifacts}
    result_path = tmp_path / "semantic-review-runtime-result.json"
    result_path.write_text(
        json.dumps(
            {
                "status": "BLOCKED",
                "blackboard": {"artifacts": artifacts},
                "traces": [],
            }
        ),
        encoding="utf-8",
    )

    audit_row = _audit_result_path(result_path)

    assert audit_row.n_generated_code_semantic_review_work_orders == 1
    assert audit_row.n_generated_code_semantic_review_executions == 1
    assert audit_row.n_generated_code_semantic_review_accepted == 1
    assert audit_row.n_generated_algorithm_semantic_review_accepted == 1
    assert (
        audit_row.n_generated_code_semantic_review_independent_evaluation_model
        == 1
    )
    assert not [
        error for error in audit_row.errors if "semantic review" in error
    ]

    original_payload = json.loads(result_path.read_text(encoding="utf-8"))
    tampered = json.loads(json.dumps(original_payload))
    execution = next(
        artifact
        for key, artifact in tampered["blackboard"]["artifacts"].items()
        if key.startswith("generated_code_semantic_review_execution:")
    )
    execution["source_model"] = ""
    execution["independent_model"] = True
    result_path.write_text(json.dumps(tampered), encoding="utf-8")

    tampered_row = _audit_result_path(result_path)

    assert any(
        "semantic review execution provenance mismatch for source_model" in error
        for error in tampered_row.errors
    )
    assert any(
        "semantic review execution model independence mismatch" in error
        for error in tampered_row.errors
    )
    assert tampered_row.n_generated_code_semantic_review_accepted == 0
    assert tampered_row.n_generated_algorithm_semantic_review_accepted == 0
    assert (
        tampered_row.n_generated_code_semantic_review_independent_evaluation_model
        == 0
    )

    invalid_packet_payload = json.loads(json.dumps(original_payload))
    invalid_artifacts = invalid_packet_payload["blackboard"]["artifacts"]
    invalid_execution = next(
        artifact
        for key, artifact in invalid_artifacts.items()
        if key.startswith("generated_code_semantic_review_execution:")
    )
    invalid_packet = invalid_artifacts[invalid_execution["review_packet_id"]]
    invalid_packet["dimension_reviews"] = invalid_packet["dimension_reviews"][:-1]
    invalid_execution["review_packet_hash"] = stable_hash(invalid_packet)
    result_path.write_text(json.dumps(invalid_packet_payload), encoding="utf-8")

    invalid_packet_row = _audit_result_path(result_path)

    assert any(
        "semantic review packet invalid" in error
        for error in invalid_packet_row.errors
    )
    assert invalid_packet_row.n_generated_code_semantic_review_accepted == 0

    forged_responsibility_payload = json.loads(json.dumps(original_payload))
    forged_artifacts = forged_responsibility_payload["blackboard"]["artifacts"]
    forged_execution = next(
        artifact
        for key, artifact in forged_artifacts.items()
        if key.startswith("generated_code_semantic_review_execution:")
    )
    forged_work_order = forged_artifacts[forged_execution["work_order_id"]]
    forged_contract = forged_work_order["source_responsibility_contract"]
    forged_contract["assigned_requirement_ids"] = [
        "frozen:simulation-calibration"
    ]
    forged_fingerprint = stable_hash(forged_contract)
    forged_work_order[
        "source_responsibility_contract_fingerprint"
    ] = forged_fingerprint
    forged_execution[
        "source_responsibility_contract_fingerprint"
    ] = forged_fingerprint
    result_path.write_text(
        json.dumps(forged_responsibility_payload),
        encoding="utf-8",
    )

    forged_responsibility_row = _audit_result_path(result_path)

    assert any(
        "semantic review source-responsibility contract mismatch" in error
        for error in forged_responsibility_row.errors
    )
    assert forged_responsibility_row.n_generated_code_semantic_review_accepted == 0

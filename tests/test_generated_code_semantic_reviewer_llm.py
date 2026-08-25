from __future__ import annotations

import json
from copy import deepcopy

import pytest

from ai_statistician.agent_runtime import AgentTask
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_review_replan import (
    GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY,
    advance_generated_code_semantic_review_lineage_budget,
    build_generated_code_semantic_review_producer_revision_task,
    record_generated_code_semantic_review_lineage_action,
)
from ai_statistician.generated_code_semantic_review_scope import (
    generated_code_semantic_review_proposal_projection,
    generated_code_semantic_review_upstream_dependency_errors,
    generated_code_semantic_review_upstream_dependency_projection,
)
from ai_statistician.generated_code_semantic_reviewer_llm import (
    GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS,
    GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA,
    GeneratedCodeSemanticReviewerConfig,
    LLMGeneratedCodeSemanticReviewerAgent,
    build_generated_code_semantic_review_prompt,
    generated_code_semantic_review_json_schema,
    generated_code_semantic_review_prompt_projection,
    validate_generated_code_semantic_review_packet,
)
from ai_statistician.structured_output_retry import PacketValidationError
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolTurnResponse,
    GeneratorResponse,
    StaticJSONGeneratorBackend,
)
from ai_statistician.research_schema import OpenResearchQuestion


def _question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="semantic-review-test",
        title="Review an executed statistical program",
        description="Determine whether the execution measures its stated claim.",
        tags=("semantic-review",),
    )


def test_simulation_proposal_review_uses_current_dependency_projection_only() -> None:
    projection = generated_code_semantic_review_proposal_projection(
        source_subsystem="SimulationEvaluator",
        proposal_packet={
            "packet_id": "simulation-plan:1",
            "simulation_targets": [{"procedure_id": "candidate"}],
            "upstream_algorithm_handoff": {
                "algorithm_sandbox_manifest_id": "algorithm:stale",
                "exact_algorithm_artifacts": [
                    {
                        "estimator_id": "candidate",
                        "exact_source_hash": "stale-source-hash",
                    }
                ],
            },
        },
        assigned_requirements=[],
    )

    assert "upstream_algorithm_handoff" not in projection
    assert "upstream_algorithm_handoff" in projection[
        "proposal_review_projection"
    ]["excluded_non_authoritative_fields"]

    dependency = generated_code_semantic_review_upstream_dependency_projection(
        source_subsystem="SimulationEvaluator",
        upstream_algorithm_handoff={
            "algorithm_sandbox_manifest_id": "algorithm:current",
            "algorithm_sandbox_manifest_hash": "current-manifest-hash",
            "semantic_review_execution_id": "review:execution",
            "semantic_review_packet_id": "review:packet",
            "exact_algorithm_artifacts": [
                {
                    "estimator_id": "candidate",
                    "exact_source_code": "def run_estimator(request): return {}",
                    "exact_source_hash": stable_hash(
                        "def run_estimator(request): return {}"
                    ),
                    "exact_smoke_result": {},
                    "exact_smoke_result_hash": stable_hash({}),
                }
            ],
        },
    )
    assert "Architect" not in dependency["routing_rule"]
    assert "source-owning workspace" in dependency["routing_rule"]
    exact_dependency = dependency["exact_dependency_artifacts"][0]
    assert exact_dependency["exact_result_included"] is False
    assert exact_dependency["exact_result_hash"] == stable_hash({})
    assert "exact_result" not in exact_dependency

    assert generated_code_semantic_review_upstream_dependency_errors(dependency) == []
    missing_hash = deepcopy(dependency)
    missing_hash["exact_dependency_artifacts"][0]["exact_result_hash"] = ""
    assert generated_code_semantic_review_upstream_dependency_errors(missing_hash) == [
        "upstream generated dependency result hash is missing: candidate"
    ]
    leaked_result = deepcopy(dependency)
    leaked_result["exact_dependency_artifacts"][0]["exact_result"] = {}
    assert generated_code_semantic_review_upstream_dependency_errors(leaked_result) == [
        "withheld upstream generated dependency unexpectedly includes a result: candidate"
    ]


def _review_material() -> dict[str, object]:
    source = "def run_sandbox(seed, replicates):\n    return {'estimate': 0.0}\n"
    result = {"estimate": 0.0, "runtime_replicates": 80}
    return {
        "source_subsystem": "SimulationEvaluator",
        "confirmatory_empirical_evidence_eligible": True,
        "theory_packet": {
            "packet_id": "theory:1",
            "claim": "The estimator targets theta under the stated assumptions.",
        },
        "architect_frozen_evidence_contract": {
            "empirical_metric_requirements": [
                {
                    "requirement_id": "metric:estimate",
                    "measurement_protocol": "Report the simulated estimate.",
                }
            ]
        },
        "exact_executed_artifacts": [
            {
                "artifact_id": "simulation:1",
                "exact_source_code": source,
                "exact_source_hash": stable_hash(source),
                "exact_result": result,
                "exact_result_hash": stable_hash(result),
                "actual_runtime_arguments": {"seed": 7, "replicates": 80},
            }
        ],
    }


def _trusted_lineage() -> dict[str, object]:
    return {
        "work_order_id": "work-order:1",
        "work_order_hash": "work-order-hash",
        "source_task_id": "simulation-task:1",
        "source_subsystem": "SimulationEvaluator",
        "source_manifest_id": "simulation-manifest:1",
        "source_manifest_hash": "simulation-manifest-hash",
        "theory_packet_id": "theory:1",
        "theory_packet_hash": "theory-hash",
        "proposal_packet_id": "proposal:1",
        "proposal_packet_hash": "proposal-hash",
        "source_agent": "LLMSimulationEngineerAgent",
        "source_model": "static-haiku",
        "source_model_tier": "haiku",
        "reviewed_artifacts": [{"artifact_id": "simulation:1"}],
    }


def test_semantic_review_delegates_load_bearing_checks_to_the_model() -> None:
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material=_review_material(),
    )

    assert "Choose the load-bearing checks yourself" in prompt
    assert "do not fill a fixed dimension checklist" in prompt
    assert "actual_runtime_arguments" in prompt
    assert "runtime_argument_rule" in prompt


def test_semantic_review_receives_exact_source_and_public_interface() -> None:
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material=_review_material(),
    )

    assert "exact executed source" in prompt
    assert "public interface" in prompt
    assert "For executable_interface_alignment" not in prompt


def test_semantic_review_keeps_current_artifact_distinct_from_dependency() -> None:
    material = _review_material()
    material["upstream_generated_dependency"] = {
        "exact_dependency_artifacts": [
            {
                "artifact_id": "estimator:upstream",
                "exact_source_code": "def run_estimator(request): return {'estimate': 0.0}",
            }
        ]
    }

    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material=material,
    )

    assert "exact_executed_artifacts as the current target" in prompt
    assert "upstream_generated_dependency as context only" in prompt
    assert "never substitute an upstream review" in prompt


def _dimension_rows(*, failed: str = "") -> dict[str, dict[str, object]]:
    return {
        dimension: {
            "status": "FAIL" if dimension == failed else "PASS",
            "rationale": (
                "The returned estimate is constant despite a stochastic claim."
                if dimension == failed
                else "The supplied artifact is aligned on this dimension."
            ),
            "evidence_refs": [
                "/exact_executed_artifacts/0/exact_source_code"
            ],
        }
        for dimension in GENERATED_CODE_SEMANTIC_REVIEW_DIMENSIONS
    }


def _agent(response: dict[str, object]) -> LLMGeneratedCodeSemanticReviewerAgent:
    return LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend(response),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model="static-haiku",
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )


def _contains_key(value: object, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return bool(forbidden.intersection(value)) or any(
            _contains_key(child, forbidden) for child in value.values()
        )
    if isinstance(value, list):
        return any(_contains_key(child, forbidden) for child in value)
    return False


def test_prompt_is_observation_only_and_preserves_complete_source() -> None:
    material = _review_material()
    material["source_manifest_summary"] = {
        "confirmatory_evaluation_cohort": {"seed": 7, "cohort_index": 0}
    }
    material["coding_agent_proposal_packet"] = {
        "runtime_budget": {"seed": 7, "n_runs": 80},
        "runtime_execution_plan": {"seed": 7, "n_runs": 80},
    }
    material["exact_executed_artifacts"][0]["exact_result"][
        "private_realized_value"
    ] = "RESULT_VALUE_MUST_NOT_APPEAR"
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(),
        review_material=material,
    )
    projection = generated_code_semantic_review_prompt_projection(material)

    assert projection["exact_executed_artifacts"][0]["exact_source_code"] == (
        material["exact_executed_artifacts"][0]["exact_source_code"]
    )
    assert "exact_result" not in projection["exact_executed_artifacts"][0]
    assert projection["exact_executed_artifacts"][0]["exact_result_schema"][
        "realized_values_withheld"
    ] is True
    assert projection["exact_executed_artifacts"][0][
        "actual_runtime_arguments"
    ]["seed"] == "EVALUATOR_WITHHELD"
    assert projection["exact_executed_artifacts"][0][
        "actual_runtime_arguments"
    ]["replicates"] == 80
    assert projection["source_manifest_summary"][
        "confirmatory_evaluation_cohort"
    ]["seed"] == "EVALUATOR_WITHHELD"
    assert projection["coding_agent_proposal_packet"]["runtime_budget"][
        "seed"
    ] == "EVALUATOR_WITHHELD"
    assert projection["coding_agent_proposal_packet"][
        "runtime_execution_plan"
    ]["seed"] == "EVALUATOR_WITHHELD"
    assert "RESULT_VALUE_MUST_NOT_APPEAR" not in prompt
    assert "def run_sandbox" in prompt
    assert "Do not write replacement code" in prompt
    assert "review_document as Markdown" in prompt
    assert "not a repair plan or routing decision" in prompt
    assert "whether some rewrite of the current source could close all findings" in prompt
    assert "source_revision_assessment" in prompt
    assert "Monte Carlo" in prompt
    assert "empirical evaluator owns realized outcome values" in prompt
    assert "cannot by themselves create a source finding" in prompt
    assert "fixed dimension checklist" in prompt
    assert '"reviewer_scope_contract"' in prompt
    assert "valid_evidence_refs" not in prompt
    assert "Review every listed prior finding once" in prompt
    assert "repair_scope" not in prompt
    assert "upstream_metric_contract" not in prompt
    assert len(prompt) < 20_000


def test_large_results_are_projected_without_mutating_full_artifact() -> None:
    material = _review_material()
    trajectory = [float(index) / 10.0 for index in range(80_000)]
    material["exact_executed_artifacts"][0]["exact_result"]["trajectory"] = trajectory

    projection = generated_code_semantic_review_prompt_projection(material)
    projected = projection["exact_executed_artifacts"][0][
        "exact_result_schema"
    ]["schema"]["fields"]["trajectory"]

    assert projected["value_kind"] == "array"
    assert projected["length"] == 80_000
    assert projected["observed_item_kinds"] == ["number"]
    assert material["exact_executed_artifacts"][0]["exact_result"][
        "trajectory"
    ] is trajectory


def test_prompt_projection_preserves_frozen_comparator_but_excludes_outcomes() -> None:
    material = _review_material()
    requirement = material["architect_frozen_evidence_contract"][
        "empirical_metric_requirements"
    ][0]
    requirement.update(
        {
            "operator": "==",
            "threshold": 1.0,
            "tolerance": 0.0,
            "required": True,
        }
    )
    artifact = material["exact_executed_artifacts"][0]
    artifact["source_row"] = {
        "metric_contracts": [
            {
                **requirement,
                "contract_id": "contract:estimate",
                "metric_path": ["estimate"],
            }
        ],
        "metric_contract_evaluation": {
            "all_required_passed": False,
            "required_failure_errors": ["realized threshold failed"],
        },
        "metrics": {"estimate": 0.0},
        "stdout_summary": "estimate=0.0 threshold=1.0 FAIL",
    }

    projection = generated_code_semantic_review_prompt_projection(material)
    projected_requirement = projection["architect_frozen_evidence_contract"][
        "empirical_metric_requirements"
    ][0]
    projected_row = projection["exact_executed_artifacts"][0]["source_row"]

    assert projected_requirement["requirement_id"] == "metric:estimate"
    assert projected_requirement["measurement_protocol"]
    assert projected_requirement["operator"] == "=="
    assert projected_requirement["threshold"] == 1.0
    assert projected_requirement["tolerance"] == 0.0
    assert projected_requirement["required"] is True
    projected_contract = projected_row["metric_contracts"][0]
    assert projected_contract["requirement_id"] == "metric:estimate"
    assert projected_contract["metric_path"] == ["estimate"]
    assert projected_contract["operator"] == "=="
    assert projected_contract["threshold"] == 1.0
    assert "metric_contract_evaluation" not in projected_row
    assert "stdout_summary" not in projected_row
    assert projected_row["metrics_schema"]["realized_values_withheld"] is True
    prompt = build_generated_code_semantic_review_prompt(
        question=_question(), review_material=material
    )
    assert "frozen measurement meanings" in prompt
    assert "For every emitted metric path" not in prompt


def test_model_schema_has_no_owner_route_or_repair_recipe_fields() -> None:
    forbidden = {
        "repair_scope",
        "repair_owner",
        "repair_plan",
        "repair_instructions",
        "required_change",
        "suggested_fix",
    }

    assert not _contains_key(GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA, forbidden)
    schema = generated_code_semantic_review_json_schema(_review_material())
    assert not _contains_key(schema, forbidden)
    assert "dimension_reviews" not in (
        GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA["properties"]
    )
    assert {
        "overall_verdict",
        "review_document",
        "findings",
        "prior_finding_reviews",
        "source_revision_assessment",
    } == set(GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA["required"])
    assert "source_revision_assessment" in (
        GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA["required"]
    )
    assessment_schema = GENERATED_CODE_SEMANTIC_REVIEW_JSON_SCHEMA[
        "properties"
    ]["source_revision_assessment"]
    assert "resolution_scope" in assessment_schema["required"]
    assert "current_source_edit_sufficient" not in assessment_schema[
        "properties"
    ]
    assert len(json.dumps(schema, separators=(",", ":"))) < 2_500
    assert "enum" not in schema["properties"]["findings"]["items"][
        "properties"
    ]["evidence_refs"]["items"]


def test_anthropic_reviewer_uses_provider_native_structured_output() -> None:
    response = {
        "prior_finding_reviews": [],
        "overall_verdict": "ACCEPT",
        "review_document": "# Review\n\nThe executed source is aligned.",
        "findings": [],
        "source_revision_assessment": {
            "resolution_scope": "NO_PARENT_ARTIFACT_CHANGE_REQUIRED",
            "rationale": "No active finding requires a parent change.",
            "evidence_refs": [],
        },
    }

    class AnthropicBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate(self, request):
            self.requests.append(request)
            return GeneratorResponse(
                text=json.dumps(response),
                provider="anthropic",
                model=request.model,
                metadata={
                    "provider_structured_output_requested": True,
                    "provider_structured_output_applied": True,
                },
            )

    backend = AnthropicBackend()
    agent = LLMGeneratedCodeSemanticReviewerAgent(
        provider=backend,
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="anthropic",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )

    packet = agent.review(
        question=_question(),
        review_material=_review_material(),
        trusted_lineage=_trusted_lineage(),
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["review_document_ref"]["format"] == "markdown"
    assert packet["_review_document_artifact"]["content"].startswith("# Review")
    assert backend.requests[0].model == "claude-haiku-4-5-20251001"
    assert backend.requests[0].metadata["provider_structured_output"] is True
    assert backend.requests[0].metadata["full_packet_regeneration_disabled"] is True


def test_native_reviewer_returns_validation_error_to_same_model_session() -> None:
    invalid_response = {
        "prior_finding_reviews": [],
        "overall_verdict": "ACCEPT",
        "review_document": "# Review\n\nThe executed source is aligned.",
        "findings": [],
        "source_revision_assessment": {
            "resolution_scope": "NO_PARENT_ARTIFACT_CHANGE_REQUIRED",
            "rationale": "No active finding requires a parent change.",
            "evidence_refs": [
                "Interface compliance: all response fields are present"
            ],
        },
    }
    valid_response = deepcopy(invalid_response)
    valid_response["source_revision_assessment"]["evidence_refs"] = []

    class ClientToolBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.responses = [invalid_response, valid_response]

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            payload = self.responses.pop(0)
            call_id = f"review-call-{len(self.requests)}"
            return ClientToolTurnResponse(
                content_blocks=(
                    {
                        "type": "tool_use",
                        "id": call_id,
                        "name": "submit_generated_code_semantic_review",
                        "input": payload,
                    },
                ),
                tool_calls=(
                    ClientToolCall(
                        call_id=call_id,
                        name="submit_generated_code_semantic_review",
                        input=payload,
                    ),
                ),
                text="",
                provider="anthropic",
                model=request.model,
                metadata={"provider_stop_reason": "tool_use"},
            )

    backend = ClientToolBackend()
    packet = LLMGeneratedCodeSemanticReviewerAgent(
        provider=backend,
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="anthropic",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_validation_retries=0,
        ),
    ).review(
        question=_question(),
        review_material=_review_material(),
        trusted_lineage=_trusted_lineage(),
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["client_tool_loop"] == {
        **packet["client_tool_loop"],
        "transport": "native_same_reviewer_session_v1",
        "turns": 2,
        "tool_calls": 2,
        "runtime_executed_tool_calls": 2,
        "validation_submissions": 2,
        "validation_feedback_observed": True,
        "full_packet_regeneration_used": False,
    }
    assert len(backend.requests) == 2
    assert backend.requests[0].tool_choice == (
        "submit_generated_code_semantic_review"
    )
    feedback = backend.requests[1].messages[-1]["content"][0]
    assert feedback["type"] == "tool_result"
    assert feedback["is_error"] is True
    assert "source_revision_assessment cites missing evidence ref" in feedback[
        "content"
    ]
    assert backend.requests[1].metadata[
        "full_packet_regeneration_disabled"
    ] is True


def test_native_reviewer_fails_closed_after_same_session_rejection() -> None:
    invalid_response = {
        "prior_finding_reviews": [],
        "overall_verdict": "ACCEPT",
        "review_document": "# Review\n\nThe executed source is aligned.",
        "findings": [],
        "source_revision_assessment": {
            "resolution_scope": "NO_PARENT_ARTIFACT_CHANGE_REQUIRED",
            "rationale": "No active finding requires a parent change.",
            "evidence_refs": ["not a JSON pointer"],
        },
    }

    class AlwaysInvalidClientToolBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            call_id = f"review-call-{len(self.requests)}"
            return ClientToolTurnResponse(
                content_blocks=(
                    {
                        "type": "tool_use",
                        "id": call_id,
                        "name": "submit_generated_code_semantic_review",
                        "input": invalid_response,
                    },
                ),
                tool_calls=(
                    ClientToolCall(
                        call_id=call_id,
                        name="submit_generated_code_semantic_review",
                        input=invalid_response,
                    ),
                ),
                text="",
                provider="anthropic",
                model=request.model,
                metadata={"provider_stop_reason": "tool_use"},
            )

    backend = AlwaysInvalidClientToolBackend()
    agent = LLMGeneratedCodeSemanticReviewerAgent(
        provider=backend,
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="anthropic",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )

    with pytest.raises(PacketValidationError) as exc_info:
        agent.review(
            question=_question(),
            review_material=_review_material(),
            trusted_lineage=_trusted_lineage(),
        )

    assert exc_info.value.attempts == 2
    assert len(backend.requests) == 2
    assert "source_revision_assessment cites missing evidence ref" in str(
        exc_info.value
    )


def test_reviewer_accepts_without_selecting_a_repair_owner() -> None:
    packet = _agent(
        {
            "prior_finding_reviews": [],
            "dimension_reviews": _dimension_rows(),
            "findings": [],
        }
    ).review(
        question=_question(),
        review_material=_review_material(),
        trusted_lineage=_trusted_lineage(),
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert "routing_authority" not in packet
    assert "runtime_selected_owner" not in packet
    assert not _contains_key(
        packet,
        {"repair_scope", "repair_owner", "repair_plan", "repair_instructions"},
    )
    assert validate_generated_code_semantic_review_packet(
        packet,
        review_material=_review_material(),
    ) == []


def test_reviewer_reports_evidence_bound_defect_without_source_edit() -> None:
    response = {
        "prior_finding_reviews": [],
        "dimension_reviews": _dimension_rows(
            failed="experiment_non_vacuity_and_identifiability"
        ),
        "findings": [
            {
                "severity": "high",
                "category": "non_vacuity",
                "summary": "The result is constant for every runtime argument.",
                "observed_behavior": "The executed source always returns 0.0.",
                "expected_behavior": (
                    "The executed experiment should vary according to its stated DGP."
                ),
                "evidence_refs": [
                    "/exact_executed_artifacts/0/exact_source_code",
                ],
            }
        ],
        "source_revision_assessment": {
            "resolution_scope": "NO_PARENT_ARTIFACT_CHANGE_REQUIRED",
            "rationale": (
                "A complete rewrite of the current source can close this finding "
                "while every supplied parent artifact remains fixed."
            ),
            "evidence_refs": [
                "/exact_executed_artifacts/0/exact_source_code",
            ],
        },
    }

    packet = _agent(response).review(
        question=_question(),
        review_material=_review_material(),
        trusted_lineage=_trusted_lineage(),
    )

    assert packet["overall_verdict"] == "REVISE"
    assert packet["findings"][0]["observed_behavior"].startswith(
        "The executed source"
    )
    assert "required_change" not in packet["findings"][0]
    assert packet["source_revision_assessment"][
        "current_source_edit_sufficient"
    ] is True
    assert packet["source_revision_assessment"]["resolution_scope"] == (
        "NO_PARENT_ARTIFACT_CHANGE_REQUIRED"
    )
    assert validate_generated_code_semantic_review_packet(
        packet,
        review_material=_review_material(),
    ) == []


def test_reviewer_canonicalizes_unambiguous_bracket_array_refs() -> None:
    response = {
        "prior_finding_reviews": [],
        "overall_verdict": "REVISE",
        "review_document": "# Review\n\nThe source ignores its runtime arguments.",
        "findings": [
            {
                "severity": "high",
                "category": "argument_alignment",
                "summary": "Runtime arguments are ignored.",
                "observed_behavior": "The source returns a constant.",
                "expected_behavior": "The source should use supplied arguments.",
                "evidence_refs": [
                    "/review_material/exact_executed_artifacts[0]/exact_source_code"
                ],
            }
        ],
        "source_revision_assessment": {
            "resolution_scope": "NO_PARENT_ARTIFACT_CHANGE_REQUIRED",
            "rationale": "The current source can be rewritten against fixed parents.",
            "evidence_refs": [
                "/review_material/exact_executed_artifacts[0]/actual_runtime_arguments"
            ],
        },
    }

    packet = _agent(response).review(
        question=_question(),
        review_material=_review_material(),
        trusted_lineage=_trusted_lineage(),
    )

    assert packet["findings"][0]["evidence_refs"] == [
        "/review_material/exact_executed_artifacts/0/exact_source_code"
    ]
    assert validate_generated_code_semantic_review_packet(
        packet, review_material=_review_material()
    ) == []


def test_reviewer_can_flag_cross_artifact_conflict_without_selecting_owner() -> None:
    response = {
        "prior_finding_reviews": [],
        "dimension_reviews": _dimension_rows(
            failed="metric_semantics_alignment"
        ),
        "findings": [
            {
                "severity": "high",
                "category": "contract_conflict",
                "summary": "The frozen meaning contradicts the supplied theory.",
                "observed_behavior": (
                    "The source implements the frozen meaning exactly."
                ),
                "expected_behavior": (
                    "The theory and frozen meaning must identify one statistic."
                ),
                "evidence_refs": [
                    "/theory_packet",
                    "/architect_frozen_evidence_contract",
                ],
            }
        ],
        "source_revision_assessment": {
            "resolution_scope": "PARENT_ARTIFACT_CHANGE_REQUIRED",
            "rationale": (
                "Changing source alone cannot satisfy two contradictory immutable "
                "artifact meanings."
            ),
            "evidence_refs": [
                "/theory_packet",
                "/architect_frozen_evidence_contract",
            ],
        },
    }

    packet = _agent(response).review(
        question=_question(),
        review_material=_review_material(),
        trusted_lineage=_trusted_lineage(),
    )

    assessment = packet["source_revision_assessment"]
    assert packet["overall_verdict"] == "REVISE"
    assert assessment["resolution_scope"] == (
        "PARENT_ARTIFACT_CHANGE_REQUIRED"
    )
    assert assessment["current_source_edit_sufficient"] is False
    assert assessment["evidence_refs"] == [
        "/review_material/theory_packet",
        "/review_material/architect_frozen_evidence_contract",
    ]
    assert not _contains_key(packet, {"repair_owner", "repair_plan"})
    assert validate_generated_code_semantic_review_packet(
        packet,
        review_material=_review_material(),
    ) == []


def test_all_pass_review_cannot_emit_blocking_findings() -> None:
    response = {
        "prior_finding_reviews": [],
        "dimension_reviews": _dimension_rows(),
        "findings": [
            {
                "severity": "medium",
                "category": "empirical_precision",
                "summary": "The realized estimate has wide uncertainty.",
                "observed_behavior": "The finite run is noisy.",
                "expected_behavior": "A later empirical evaluator should assess it.",
                "evidence_refs": ["/exact_executed_artifacts"],
            }
        ],
    }

    with pytest.raises(PacketValidationError) as exc_info:
        _agent(response).review(
            question=_question(),
            review_material=_review_material(),
            trusted_lineage=_trusted_lineage(),
        )

    assert "all-PASS semantic reviews must leave findings empty" in str(
        exc_info.value
    )


def test_legacy_repair_fields_are_reduced_to_descriptive_observations() -> None:
    response = {
        "prior_finding_reviews": [],
        "dimension_reviews": _dimension_rows(failed="metric_semantics_alignment"),
        "findings": [
            {
                "severity": "high",
                "category": "metric_semantics",
                "summary": "The reported scalar has the wrong meaning.",
                "required_change": "Return the stated estimand.",
                "repair_scope": "source_code",
                "artifact_delta": {
                    "current_behavior": "Returns an unrelated constant.",
                    "required_behavior": "Returns the stated estimand.",
                },
                "evidence_refs": [
                    "/exact_executed_artifacts/0/exact_source_code"
                ],
            }
        ],
    }

    packet = _agent(response).review(
        question=_question(),
        review_material=_review_material(),
        trusted_lineage=_trusted_lineage(),
    )

    finding = packet["findings"][0]
    assert finding["observed_behavior"] == "Returns an unrelated constant."
    assert finding["expected_behavior"] == "Returns the stated estimand."
    assert "required_change" not in finding
    assert "repair_scope" not in finding


def test_missing_evidence_pointer_fails_closed() -> None:
    response = {
        "prior_finding_reviews": [],
        "dimension_reviews": _dimension_rows(failed="metric_semantics_alignment"),
        "findings": [
            {
                "severity": "high",
                "category": "metric_semantics",
                "summary": "The metric cannot be checked from supplied evidence.",
                "observed_behavior": "The cited value is absent.",
                "expected_behavior": "A cited executed value should support the claim.",
                "evidence_refs": ["/missing/artifact"],
            }
        ],
    }

    with pytest.raises(PacketValidationError) as exc_info:
        _agent(response).review(
            question=_question(),
            review_material=_review_material(),
            trusted_lineage=_trusted_lineage(),
        )

    assert "cites missing evidence ref" in str(exc_info.value)


@pytest.mark.parametrize(
    "evidence_ref",
    (
        "#/exact_executed_artifacts/0/exact_source_code",
        "/review_material/exact_executed_artifacts/0/exact_source_code",
    ),
)
def test_equivalent_evidence_pointer_namespaces_are_canonicalized(
    evidence_ref: str,
) -> None:
    response = {
        "prior_finding_reviews": [],
        "dimension_reviews": {
            dimension: {
                **row,
                "evidence_refs": [evidence_ref],
            }
            for dimension, row in _dimension_rows().items()
        },
        "findings": [],
    }

    packet = _agent(response).review(
        question=_question(),
        review_material=_review_material(),
        trusted_lineage=_trusted_lineage(),
    )

    assert all(
        row["evidence_refs"]
        == ["/review_material/exact_executed_artifacts/0/exact_source_code"]
        for row in packet["dimension_reviews"]
    )
    assert validate_generated_code_semantic_review_packet(
        packet,
        review_material=_review_material(),
    ) == []


def test_prior_findings_are_reviewed_by_identity_without_owner_state() -> None:
    material = _review_material()
    material["prior_semantic_observations"] = {
        "active_prior_finding_ledger": [
            {
                "finding_id": "generated_code_semantic_finding:prior",
                "status": "UNRESOLVED",
                "finding": {
                    "summary": "Prior semantic defect",
                    "category": "prior",
                },
            }
        ]
    }
    response = {
        "prior_finding_reviews": [
            {
                "status": "RESOLVED_BY_CURRENT_ARTIFACT",
                "rationale": "The fresh source and result close the observation.",
                "evidence_refs": [
                    "/exact_executed_artifacts/0/exact_source_code"
                ],
            }
        ],
        "dimension_reviews": _dimension_rows(),
        "findings": [],
    }

    packet = _agent(response).review(
        question=_question(),
        review_material=material,
        trusted_lineage=_trusted_lineage(),
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert "finding_id" not in generated_code_semantic_review_json_schema(
        material
    )["properties"]["prior_finding_reviews"]["items"]["properties"]
    assert packet["prior_finding_reviews"][0]["finding_id"] == (
        "generated_code_semantic_finding:prior"
    )
    assert packet["active_unresolved_finding_ids"] == []
    assert validate_generated_code_semantic_review_packet(
        packet,
        review_material=material,
    ) == []


def test_unresolved_prior_finding_keeps_review_in_revise_without_restatement() -> None:
    material = _review_material()
    material["prior_semantic_observations"] = {
        "active_prior_finding_ledger": [
            {
                "finding_id": "generated_code_semantic_finding:prior",
                "status": "UNRESOLVED",
                "finding": {
                    "summary": "Prior semantic defect",
                    "category": "prior",
                },
            }
        ]
    }
    response = {
        "prior_finding_reviews": [
            {
                "status": "UNRESOLVED",
                "rationale": "The current artifact still exhibits the observation.",
                "evidence_refs": [
                    "/exact_executed_artifacts/0/exact_source_code"
                ],
            }
        ],
        "dimension_reviews": _dimension_rows(),
        "findings": [],
    }

    packet = _agent(response).review(
        question=_question(),
        review_material=material,
        trusted_lineage=_trusted_lineage(),
    )

    assert packet["overall_verdict"] == "REVISE"
    assert packet["findings"] == []
    assert packet["active_unresolved_finding_ids"] == [
        "generated_code_semantic_finding:prior"
    ]
    assert validate_generated_code_semantic_review_packet(
        packet,
        review_material=material,
    ) == []


def test_prior_scope_error_can_be_retracted_by_the_independent_reviewer() -> None:
    material = _review_material()
    material["prior_semantic_observations"] = {
        "active_prior_finding_ledger": [
            {
                "finding_id": "generated_code_semantic_finding:prior",
                "status": "UNRESOLVED",
                "finding": {
                    "summary": "A realized empirical estimate is noisy.",
                    "category": "empirical_precision",
                },
            }
        ]
    }
    response = {
        "prior_finding_reviews": [
            {
                "status": "RETRACTED_RUNTIME_CONTRACT_CONFLICT",
                "rationale": (
                    "The prior observation belongs to empirical evaluation, not "
                    "code-semantic review."
                ),
                "evidence_refs": [
                    "/reviewer_scope_contract/prior_finding_rule"
                ],
            }
        ],
        "dimension_reviews": _dimension_rows(),
        "findings": [],
    }

    packet = _agent(response).review(
        question=_question(),
        review_material=material,
        trusted_lineage=_trusted_lineage(),
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["prior_finding_reviews"][0]["status"] == (
        "RETRACTED_RUNTIME_CONTRACT_CONFLICT"
    )
    assert packet["active_unresolved_finding_ids"] == []
    assert validate_generated_code_semantic_review_packet(
        packet,
        review_material=material,
    ) == []


def test_lineage_budget_bounds_source_producer_regenerations() -> None:
    work_order = {
        "question_id": "semantic-review-test",
        "theory_packet_id": "theory:1",
        "theory_packet_hash": "theory-hash",
        "source_subsystem": "SimulationEvaluator",
    }
    review_packet = {
        "dimension_reviews": [
            {
                "dimension": "metric_semantics_alignment",
                "status": "FAIL",
            }
        ],
        "findings": [
            {
                "finding_id": "generated_code_semantic_finding:one",
                "severity": "high",
                "category": "metric_semantics",
                "summary": "The metric meaning is inconsistent.",
            }
        ],
    }

    first = advance_generated_code_semantic_review_lineage_budget(
        architect_context={},
        work_order=work_order,
        review_packet=review_packet,
        max_local_revisions=1,
    )
    ledger = record_generated_code_semantic_review_lineage_action(
        first,
        action="producer_regeneration",
    )
    second = advance_generated_code_semantic_review_lineage_budget(
        architect_context={
            GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY: ledger
        },
        work_order=work_order,
        review_packet=review_packet,
        max_local_revisions=1,
    )

    assert first["candidate_regeneration_available"] is True
    assert second["lineage_budget_exhausted"] is True
    assert second["row"]["source_candidate_regeneration_count"] == 1
    assert "repair_scope" not in first["row"]
    assert "repair_owner" not in first["row"]


def test_revision_task_returns_complete_observations_to_source_producer() -> None:
    source_task = AgentTask(
        task_id="simulation-task:1",
        owner_subsystem="SimulationEvaluator",
        objective="Generate and execute a complete simulation.",
        inputs={
            "question": {"id": "semantic-review-test"},
            "architect_context": {},
        },
        allowed_tools=("python",),
        expected_artifacts=("simulation_manifest",),
        acceptance_gate="execution succeeds",
        stop_condition="execution evidence recorded",
    )
    work_order = {
        "work_order_id": "work-order:1",
        "source_task_id": "simulation-task:1",
        "source_subsystem": "SimulationEvaluator",
        "source_manifest_id": "simulation-manifest:1",
        "theory_packet_hash": "theory-hash",
    }
    feedback = {
        "feedback_type": "generated_code_semantic_review_feedback",
        "source_subsystem": "SimulationEvaluator",
        "semantic_review_execution_id": "review-execution:1",
        "semantic_review_packet_id": "review:1",
        "semantic_review_packet_hash": "review-hash",
        "findings": [
            {
                "finding_id": "finding:1",
                "summary": "Observed result is semantically inconsistent.",
                "observed_behavior": "Observed A.",
                "expected_behavior": "Expected B.",
                "evidence_refs": ["/exact_executed_artifacts/0/exact_result"],
            }
        ],
        "reviewed_source_artifacts": [
            {
                "artifact_id": "simulation:1",
                "exact_source_hash": "source-hash",
                "exact_source_code": (
                    "def run_sandbox(seed, replicates):\n"
                    "    return {'estimate': 0.0}\n"
                ),
                "exact_source_code_complete": True,
                "exact_result": {"estimate": 0.0},
                "exact_result_hash": "result-hash",
                "execution_envelope_hash": "outcome-derived-envelope-hash",
            }
        ],
        "source_lineage": {"theory_packet_hash": "theory-hash"},
        "repair_owner": "AlgorithmEngineer",
        "repair_plan": [{"step": "hidden runtime plan"}],
    }

    task = build_generated_code_semantic_review_producer_revision_task(
        question=_question(),
        review_task_id="review-task:1",
        work_order=work_order,
        source_task=source_task,
        review_feedback=feedback,
        review_packet_id="review:1",
        review_execution_id="review-execution:1",
        revision_count=0,
        max_revisions=1,
    )

    assert task.owner_subsystem == "SimulationEvaluator"
    assert "runtime_architect_operation" not in task.inputs
    assert task.inputs["environment_feedback"]["findings"]
    reviewed = task.inputs["environment_feedback"][
        "reviewed_source_artifacts"
    ][0]
    assert reviewed["exact_source_code"].endswith(
        "return {'estimate': 0.0}\n"
    )
    assert reviewed["exact_result"] == {"estimate": 0.0}
    assert task.inputs["generated_code_semantic_review_revision_count"] == 1
    replan = task.inputs["architect_context"][
        "runtime_generated_code_semantic_review_replan"
    ]
    assert "environment_feedback" not in task.inputs["architect_context"]
    assert "repair_owner" not in replan
    assert "repair_plan" not in replan
    assert replan["routing_authority"] == "immutable_source_producer_lineage"
    assert replan["runtime_selected_owner"] is False


def test_confirmatory_revision_returns_source_and_findings_without_result_values() -> None:
    source_task = AgentTask(
        task_id="simulation-task:blind",
        owner_subsystem="SimulationEvaluator",
        objective="Revise one semantically rejected source.",
        inputs={"question": {"id": "semantic-review-test"}},
    )
    feedback = {
        "feedback_type": "generated_code_semantic_review_feedback",
        "source_subsystem": "SimulationEvaluator",
        "confirmatory_empirical_evidence_eligible": True,
        "semantic_review_execution_id": "review-execution:blind",
        "semantic_review_packet_id": "review:blind",
        "semantic_review_packet_hash": "review-hash",
        "findings": [
            {
                "finding_id": "finding:blind",
                "summary": "The emitted field has the wrong statistical meaning.",
                "observed_behavior": "The source emits a surrogate field.",
                "expected_behavior": "Emit the frozen protocol's statistic.",
                "evidence_refs": ["/reviewed_source_artifacts/0/exact_source_code"],
            }
        ],
        "reviewed_source_artifacts": [
            {
                "artifact_id": "simulation:blind",
                "exact_source_hash": "source-hash",
                "exact_source_code": (
                    "def run_sandbox(seed, replicates):\n"
                    "    return {'metric': 0.2}\n"
                ),
                "exact_source_code_complete": True,
                "exact_result": {"metric": 0.2},
                "exact_result_hash": "result-hash",
                "actual_runtime_arguments": {"seed": 7, "replicates": 80},
            }
        ],
    }

    task = build_generated_code_semantic_review_producer_revision_task(
        question=_question(),
        review_task_id="review-task:blind",
        work_order={
            "work_order_id": "work-order:blind",
            "source_task_id": source_task.task_id,
            "source_subsystem": "SimulationEvaluator",
            "source_manifest_id": "simulation-manifest:blind",
            "theory_packet_hash": "theory-hash",
        },
        source_task=source_task,
        review_feedback=feedback,
        review_packet_id="review:blind",
        review_execution_id="review-execution:blind",
        revision_count=0,
        max_revisions=1,
    )

    source_feedback = task.inputs["environment_feedback"]
    reviewed = source_feedback["reviewed_source_artifacts"][0]
    assert reviewed["exact_source_code"].endswith("return {'metric': 0.2}\n")
    assert "exact_result" not in reviewed
    assert "exact_result_hash" not in reviewed
    assert "execution_envelope_hash" not in reviewed
    assert reviewed["exact_result_schema"]["realized_values_withheld"] is True
    assert reviewed["actual_runtime_arguments"]["seed"] == "EVALUATOR_WITHHELD"
    assert reviewed["actual_runtime_arguments"]["replicates"] == 80
    assert source_feedback["confirmatory_result_values_withheld_from_source"] is True
    assert "0.2" not in str(reviewed["exact_result_schema"])

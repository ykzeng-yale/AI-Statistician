from __future__ import annotations

import json
from copy import deepcopy

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_review_replan import (
    GENERATED_CODE_SEMANTIC_REVIEW_LINEAGE_LEDGER_KEY,
    advance_generated_code_semantic_review_lineage_budget,
    build_generated_code_semantic_review_producer_revision_task,
    record_generated_code_semantic_review_lineage_action,
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
from ai_statistician.llm_json_repair import PacketValidationError
from ai_statistician.model_backend import (
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
    assert "RESULT_VALUE_MUST_NOT_APPEAR" not in prompt
    assert "def run_sandbox" in prompt
    assert "Do not propose source edits" in prompt
    assert "ArchitectCoordinator decides what subsystem acts next" in prompt
    assert "Monte Carlo uncertainty" in prompt
    assert "belong exclusively to the empirical evaluator" in prompt
    assert "cannot create a semantic source finding" in prompt
    assert "never the realized threshold result" in prompt
    assert "all-PASS" not in prompt
    assert "If every dimension is PASS, findings must be empty" in prompt
    assert "RETRACTED_RUNTIME_CONTRACT_CONFLICT" in prompt
    assert '"reviewer_scope_contract"' in prompt
    assert "valid_evidence_refs" in prompt
    assert "forms are also accepted" in prompt
    assert "findings contains only genuinely new defects" in prompt
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


def test_prompt_projection_excludes_empirical_gate_authority_and_outcomes() -> None:
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
    assert not {"operator", "threshold", "tolerance", "required"}.intersection(
        projected_requirement
    )
    assert "metric_contract_evaluation" not in projected_row
    assert "stdout_summary" not in projected_row
    assert projected_row["metrics_schema"]["realized_values_withheld"] is True


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
    assert not _contains_key(
        generated_code_semantic_review_json_schema(_review_material()),
        forbidden,
    )


def test_anthropic_reviewer_uses_provider_native_structured_output() -> None:
    response = {
        "prior_finding_reviews": [],
        "dimension_reviews": _dimension_rows(),
        "findings": [],
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
    assert backend.requests[0].model == "claude-haiku-4-5-20251001"
    assert backend.requests[0].metadata["provider_structured_output"] is True


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
    source_task = {
        "task_id": "simulation-task:1",
        "owner_subsystem": "SimulationEvaluator",
        "objective": "Generate and execute a complete simulation.",
        "inputs": {
            "question": {"id": "semantic-review-test"},
            "architect_context": {},
        },
        "allowed_tools": ["python"],
        "expected_artifacts": ["simulation_manifest"],
        "acceptance_gate": "execution succeeds",
        "stop_condition": "execution evidence recorded",
    }
    deferred = deepcopy(source_task)
    deferred["task_id"] = "formalize:1"
    deferred["owner_subsystem"] = "FormalizationEvaluator"
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
    assert "repair_owner" not in replan
    assert "repair_plan" not in replan
    assert replan["routing_authority"] == "immutable_source_producer_lineage"
    assert replan["runtime_selected_owner"] is False

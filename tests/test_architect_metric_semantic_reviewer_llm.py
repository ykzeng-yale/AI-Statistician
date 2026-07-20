from __future__ import annotations

import json

import pytest

from ai_statistician.architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_DIMENSIONS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA,
    ArchitectMetricSemanticReviewerConfig,
    LLMArchitectMetricSemanticReviewerAgent,
    architect_metric_review_material_with_runtime_evaluator_certificate,
    architect_metric_semantic_review_json_schema,
    validate_architect_metric_semantic_review_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_metric_contract import (
    generated_metric_evaluation_semantics_contract,
    generated_metric_requirement_set_id,
)
from ai_statistician.llm_json_repair import PacketValidationError
from ai_statistician.model_backend import GeneratorResponse
from ai_statistician.research_schema import OpenResearchQuestion


def _generic_requirement(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "requirement_id": "generic_gate",
        "target_subsystems": ["SimulationEngineer"],
        "metric_semantics": "one raw finite generic diagnostic",
        "measurement_protocol": "return one raw generic diagnostic value",
        "required_runtime_replicates": 5,
        "operator": "<=",
        "threshold": 0.1,
        "lower": None,
        "upper": None,
        "tolerance": 0.0,
        "aggregation": "identity",
        "minimum_pass_count": None,
        "minimum_pass_fraction": None,
        "required": True,
        "source_anchors": ["theory:generic-gate"],
        "boundary": "pre-execution empirical control, not proof evidence",
    }
    row.update(overrides)
    return row


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
                    "prior_finding_id": "",
                    "new_finding_rationale": "",
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


def _review(
    *,
    accept: bool,
    reviewer_model: str = "claude-sonnet-4-6",
    payload: dict[str, object] | None = None,
    material: dict[str, object] | None = None,
):
    backend = _Backend(payload or _review_payload(accept=accept))
    material = material or {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "empirical_metric_requirements": [_generic_requirement()],
    }
    material = architect_metric_review_material_with_runtime_evaluator_certificate(
        material
    )
    requirement_set_id = generated_metric_requirement_set_id(
        material["empirical_metric_requirements"]
    )
    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model=reviewer_model,
            model_tier="sonnet",
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
            "empirical_metric_requirement_set_id": requirement_set_id,
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
    assert packet["independent_invocation"] is True
    assert packet["independent_model"] is False
    assert packet["independent_model_tier"] is False
    assert packet["review_input_fingerprint"] == stable_hash(material)
    assert packet["reviewed_empirical_metric_requirement_set_id"] == (
        generated_metric_requirement_set_id(
            material["empirical_metric_requirements"]
        )
    )
    assert packet["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")
    assert validate_architect_metric_semantic_review_packet(packet) == []
    assert backend.requests[0].metadata["subsystem"] == (
        "ArchitectMetricSemanticReviewer"
    )
    assert backend.requests[0].metadata["model_tier"] == "sonnet"
    assert backend.requests[0].metadata["provider_structured_output"] is True
    assert "before any coding agent" in backend.requests[0].user_prompt
    assert "more gates are not more rigorous" in backend.requests[0].user_prompt
    assert "runtime_evaluator_certificate" in backend.requests[0].user_prompt
    assert "cannot require pilot or confirmatory results" in (
        backend.requests[0].user_prompt
    )
    assert "finite-sample uncertainty as low-severity advisory" in (
        backend.requests[0].user_prompt
    )
    assert "topically related node is not enough" in backend.requests[0].user_prompt
    assert "diagnostic_only rows must be required=false" in (
        backend.requests[0].user_prompt
    )
    assert "architect_preregistered_design" in backend.requests[0].user_prompt
    assert "do not require a candidate-owned evaluation choice" in (
        backend.requests[0].user_prompt
    )
    assert "never recommend editing that derived list directly" in (
        backend.requests[0].user_prompt
    )
    assert "Do not route upstream merely to make TheoryDeveloper ratify" in (
        backend.requests[0].user_prompt
    )
    assert packet["runtime_evaluator_certificate_set_id"].startswith(
        "generated_metric_evaluator_certificate_set:"
    )


def test_preexecution_metric_reviewer_returns_typed_revision_feedback() -> None:
    packet, _, _ = _review(accept=False)

    assert packet["overall_verdict"] == "REVISE"
    assert packet["repair_instructions"]
    assert packet["findings"][0]["severity"] == "high"
    assert packet["findings"][0]["repair_scope"] == "metric_contract"
    assert packet["recommended_repair_scope"] == "metric_contract"
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_metric_reviewer_binds_certificate_to_authoring_requirement_set() -> None:
    packet, _, _ = _review(accept=True)
    packet["reviewed_empirical_metric_requirement_set_id"] = (
        "generated_metric_requirement_set:wrong"
    )

    assert (
        "runtime evaluator certificate requirement-set identity must match "
        "the reviewed authoring lineage"
        in validate_architect_metric_semantic_review_packet(packet)
    )


def test_preexecution_metric_reviewer_accepts_low_severity_advisory_uncertainty() -> None:
    payload = _review_payload(accept=True)
    payload["dimension_reviews"][-1]["status"] = "UNCERTAIN"
    payload["dimension_reviews"][-1]["rationale"] = (
        "A redundant row can be simplified, but it does not change the pass set."
    )
    payload["findings"] = [
        {
            "prior_finding_id": "",
            "new_finding_rationale": "",
            "severity": "low",
            "category": "redundant_gate",
            "summary": "One row duplicates a stronger gate.",
            "required_change": "Remove the redundant row in later cleanup.",
            "repair_scope": "metric_contract",
            "evidence_refs": ["requirement:generic_gate"],
        }
    ]

    packet, backend, _ = _review(accept=True, payload=payload)

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["recommended_repair_scope"] == "none"
    assert packet["findings"][0]["severity"] == "low"
    assert validate_architect_metric_semantic_review_packet(packet) == []
    assert "advisory UNCERTAIN" in backend.requests[0].user_prompt


def test_preexecution_metric_reviewer_routes_missing_semantics_upstream() -> None:
    payload = _review_payload(accept=False)
    payload["findings"][0]["repair_scope"] = "upstream_theory"
    backend = _Backend(payload)
    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model="claude-sonnet-4-6",
            model_tier="sonnet",
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
            "empirical_metric_requirements": [_generic_requirement()],
        },
        trusted_lineage={
            "authoring_packet_id": "metric-authoring:theory-gap",
            "authoring_packet_hash": stable_hash({"candidate": "theory-gap"}),
            "empirical_metric_requirement_set_id": (
                generated_metric_requirement_set_id([_generic_requirement()])
            ),
            "source_agent": "ArchitectMetricContractPlanner",
            "source_model": "claude-sonnet-4-6",
            "source_model_tier": "sonnet",
        },
    )

    assert packet["recommended_repair_scope"] == "upstream_theory"
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_preexecution_metric_reviewer_accepts_separate_same_model_invocation() -> None:
    packet, _, _ = _review(accept=True, reviewer_model="claude-sonnet-4-6")

    assert packet["independent_agent"] is True
    assert packet["independent_invocation"] is True
    assert packet["independent_model"] is False


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
            "runtime_contract_evidence_id": "",
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
        "theory_developer_protocol_material": {"padding": "x" * 12000},
        "empirical_metric_requirements": [
            _generic_requirement(
                aggregation="mean",
                operator="between",
                threshold=None,
                lower=-0.1,
                upper=0.1,
            )
        ],
    }
    material = architect_metric_review_material_with_runtime_evaluator_certificate(
        material
    )

    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model="claude-sonnet-4-6",
            model_tier="sonnet",
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
            "empirical_metric_requirement_set_id": (
                generated_metric_requirement_set_id(
                    material["empirical_metric_requirements"]
                )
            ),
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
    repair_payload = json.loads(
        backend.requests[1].user_prompt.split("\n\n", 1)[1]
    )
    assert repair_payload["original_request"]["truncated"] is True
    repair_context = repair_payload["subsystem_repair_context"]
    assert repair_context["current_candidate"][
        "empirical_metric_requirements"
    ] == material["empirical_metric_requirements"]
    assert repair_context["current_candidate"][
        "empirical_metric_requirements_fingerprint"
    ] == stable_hash(material["empirical_metric_requirements"])
    assert repair_context["review_input_fingerprint"] == stable_hash(material)
    assert repair_context["rejected_review_packet"]["overall_verdict"] == (
        "ACCEPT"
    )
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
            "runtime_contract_evidence_id": "",
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


def test_metric_reviewer_reuses_prior_identity_for_persistent_finding() -> None:
    finding_id = "metric-finding:persistent-calibration"
    payload = _review_payload(accept=False)
    payload["prior_finding_reviews"] = [
        {
            "finding_id": finding_id,
            "status": "UNRESOLVED",
            "runtime_contract_evidence_id": "",
            "rationale": "The current candidate still leaves the same issue open.",
            "evidence_refs": ["requirement:generic_gate"],
        }
    ]
    payload["findings"][0]["prior_finding_id"] = finding_id
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "active_prior_finding_ledger": [
            {
                "finding_id": finding_id,
                "status": "UNRESOLVED",
                "finding": {
                    "category": "finite_sample_calibration",
                    "summary": "The same finite-sample issue remains open.",
                    "repair_scope": "metric_contract",
                },
            }
        ],
        "empirical_metric_requirements": [_generic_requirement()],
    }

    packet, _, _ = _review(
        accept=False,
        payload=payload,
        material=material,
    )

    assert packet["findings"][0]["finding_id"] == finding_id
    assert packet["findings"][0]["prior_finding_id"] == finding_id
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_metric_reviewer_does_not_trust_unlinked_model_finding_id() -> None:
    payload = _review_payload(accept=False)
    payload["findings"][0]["finding_id"] = "model-forged-finding-id"

    packet, _, _ = _review(accept=False, payload=payload)

    assert packet["findings"][0]["finding_id"] != "model-forged-finding-id"
    assert packet["findings"][0]["finding_id"].startswith(
        "metric_protocol_finding:"
    )


def test_metric_reviewer_can_retract_only_runtime_contract_conflicts() -> None:
    finding_id = "metric-finding:invalid-evaluator-order"
    evidence_id = (
        "metric_evaluation_semantics.elementwise_aggregations.evaluation_order"
    )
    payload = _review_payload(accept=True)
    payload["prior_finding_reviews"] = [
        {
            "finding_id": finding_id,
            "status": "RETRACTED_RUNTIME_CONTRACT_CONFLICT",
            "runtime_contract_evidence_id": evidence_id,
            "rationale": (
                "The prior finding reversed the authoritative elementwise "
                "comparison and quorum order."
            ),
            "evidence_refs": [evidence_id],
        }
    ]
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "active_prior_finding_ledger": [
            {
                "finding_id": finding_id,
                "finding": {
                    "summary": "The elementwise comparison order is reversed."
                },
            }
        ],
        "empirical_metric_requirements": [_generic_requirement()],
        "metric_evaluation_semantics": (
            generated_metric_evaluation_semantics_contract()
        ),
        "runtime_contract_authority": {
            "allowed_retraction_evidence_ids": list(
                ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS
            )
        },
    }

    packet, _, _ = _review(
        accept=True,
        payload=payload,
        material=material,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["prior_finding_reviews"][0]["status"] == (
        "RETRACTED_RUNTIME_CONTRACT_CONFLICT"
    )
    assert validate_architect_metric_semantic_review_packet(packet) == []

    packet["prior_finding_reviews"][0]["runtime_contract_evidence_id"] = (
        "requirement:generic_gate"
    )
    assert (
        "runtime-contract finding retraction must select an exact allowed "
        "runtime_contract_evidence_id"
        in validate_architect_metric_semantic_review_packet(packet)
    )


def test_metric_review_schema_transforms_for_anthropic_structured_output() -> None:
    anthropic = pytest.importorskip("anthropic")

    dynamic_schema = architect_metric_semantic_review_json_schema(
        {
            "active_prior_finding_ledger": [
                {"finding_id": "finding:one", "finding": {"summary": "one"}},
                {"finding_id": "finding:two", "finding": {"summary": "two"}},
            ],
            "runtime_contract_authority": {
                "allowed_retraction_evidence_ids": [
                    "generated_metric_evaluator_certificate:test"
                ]
            },
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
    assert transformed_prior_schema["items"]["properties"][
        "runtime_contract_evidence_id"
    ]["enum"] == ["", "generated_metric_evaluator_certificate:test"]
    assert transformed["properties"]["findings"]["items"]["properties"][
        "prior_finding_id"
    ]["enum"] == ["", "finding:one", "finding:two"]
    assert "minItems: 2" in transformed_prior_schema["description"]
    assert ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA["properties"][
        "prior_finding_reviews"
    ].get("minItems") is None

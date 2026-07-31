from __future__ import annotations

from copy import deepcopy
import json

import pytest

from ai_statistician.architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_DIMENSIONS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA,
    ArchitectMetricSemanticReviewerConfig,
    LLMArchitectMetricSemanticReviewerAgent,
    _architect_metric_semantic_review_repair_context,
    _architect_metric_theory_scope_check_contract,
    architect_metric_active_prior_finding_current_evidence,
    architect_metric_review_material_with_runtime_evaluator_certificate,
    architect_metric_semantic_review_json_schema,
    bind_architect_metric_finding_evidence_identities,
    validate_architect_metric_semantic_review_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_metric_contract import (
    generated_metric_acceptance_authority_catalog,
    generated_metric_evaluation_semantics_contract,
    generated_metric_requirement_set_id,
)
from ai_statistician.llm_json_repair import PacketValidationError
from ai_statistician.model_backend import GeneratorResponse
from ai_statistician.research_schema import OpenResearchQuestion


TEST_HAIKU_MODEL = "claude-haiku-4-5-20251001"


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


def _normalization_reconstruction(
    *,
    consistent: bool = True,
    unresolved_conflicts: list[str] | None = None,
) -> dict[str, object]:
    return {
        "source_expression": "source_value = theta",
        "protocol_expression_ref": (
            "requirement:generic_gate.metric_semantics"
        ),
        "protocol_expression": "one raw finite generic diagnostic",
        "substitution_without_reinterpretation": "metric_value = theta",
        "resulting_sample_size_order": "O(1)",
        "required_sample_size_order": "O(1)",
        "convention_consistent": consistent,
        "unresolved_conflicts": list(unresolved_conflicts or []),
    }


def _review_payload(*, accept: bool) -> dict[str, object]:
    status = "PASS" if accept else "FAIL"
    return {
        "prior_finding_reviews": [],
        "claim_checks": [
            {
                "requirement_id": "generic_gate",
                "claim_ref": "requirement:generic_gate.metric_semantics",
                "check_type": "direct_substitution",
                "recomputation": "Substitute the declared scalar into its definition.",
                "normalization_and_unit_audit": (
                    "The scalar is dimensionless and has no sample-size or "
                    "replicate normalization factor."
                ),
                "normalization_reconstruction": (
                    _normalization_reconstruction()
                ),
                "result": "The declared metric is finite and scalar.",
                "verdict": "PASS",
                "evidence_refs": ["requirement:generic_gate.metric_semantics"],
            },
            {
                "requirement_id": "generic_gate",
                "claim_ref": "requirement:generic_gate.operator",
                "check_type": "pass_set_translation",
                "recomputation": "The executable pass set is value <= 0.1.",
                "normalization_and_unit_audit": (
                    "The raw value and threshold use the same dimensionless "
                    "scale before the identity aggregation."
                ),
                "normalization_reconstruction": (
                    _normalization_reconstruction()
                ),
                "result": (
                    "The pass set matches the protocol."
                    if accept
                    else "The finite-sample calibration is unsupported."
                ),
                "verdict": "PASS" if accept else "FAIL",
                "evidence_refs": ["requirement:generic_gate.operator"],
            },
        ],
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

    def __init__(self, payloads: list[object]) -> None:
        self.payloads = payloads
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        payload_or_factory = self.payloads[
            min(len(self.requests) - 1, len(self.payloads) - 1)
        ]
        payload = (
            payload_or_factory(request)
            if callable(payload_or_factory)
            else payload_or_factory
        )
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
    reviewer_model: str = TEST_HAIKU_MODEL,
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
    theory_material = material.get("theory_developer_protocol_material", {})
    theory_material = (
        dict(theory_material) if isinstance(theory_material, dict) else {}
    )
    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model=reviewer_model,
            model_tier="haiku",
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
            "source_model": TEST_HAIKU_MODEL,
            "source_model_tier": "haiku",
            "source_theory_packet_id": str(
                theory_material.get("source_theory_packet_id", "") or ""
            ),
            "source_theory_packet_hash": str(
                theory_material.get("source_theory_packet_hash", "") or ""
            ),
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
    assert backend.requests[0].metadata["model_tier"] == "haiku"
    assert backend.requests[0].metadata["provider_structured_output"] is True
    assert "before any coding agent" in backend.requests[0].user_prompt
    assert "more gates are not more rigorous" in backend.requests[0].user_prompt
    assert "runtime_evaluator_certificate" in backend.requests[0].user_prompt
    assert "fixed before all replicates" in backend.requests[0].user_prompt
    assert "recomputed from each replicate" in backend.requests[0].user_prompt
    assert "cannot require pilot or confirmatory results" in (
        backend.requests[0].user_prompt
    )
    assert "finite-sample uncertainty as low-severity advisory" in (
        backend.requests[0].user_prompt
    )
    assert "cover every requirement_id" in backend.requests[0].user_prompt
    assert "normalization_and_unit_audit" in backend.requests[0].user_prompt
    assert "normalization_reconstruction" in backend.requests[0].user_prompt
    assert "without adding, deleting, or reinterpreting" in (
        backend.requests[0].user_prompt
    )
    assert "finite-sample variance or standard error" in (
        backend.requests[0].user_prompt
    )
    assert "every explicit evaluation objective" in (
        backend.requests[0].user_prompt
    )
    assert "A citation without a displayed recomputation" in (
        backend.requests[0].user_prompt
    )
    assert "entry in theory_scope_checks" in (
        backend.requests[0].user_prompt
    )
    assert "cannot validate a claim over their wider stated scope" in (
        backend.requests[0].user_prompt
    )
    assert "topically related node is not enough" in backend.requests[0].user_prompt
    assert "diagnostic_only rows must be required=false" in (
        backend.requests[0].user_prompt
    )
    assert "architect_preregistered_design" in backend.requests[0].user_prompt
    assert "every required architect_preregistered_design row" in (
        backend.requests[0].user_prompt
    )
    assert "computes an uncertainty scale" in backend.requests[0].user_prompt
    assert "generic statement that a gate is plausible" in (
        backend.requests[0].user_prompt
    )
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


def test_metric_reviewer_derives_verdict_from_granular_judgments() -> None:
    payload = _review_payload(accept=True)
    payload["overall_verdict"] = "REVISE"

    packet, backend, _ = _review(accept=True, payload=payload)

    assert "overall_verdict" not in backend.requests[0].schema["properties"]
    assert packet["model_requested_overall_verdict"] == "REVISE"
    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["recommended_repair_scope"] == "none"
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_preexecution_metric_reviewer_returns_typed_revision_feedback() -> None:
    packet, _, _ = _review(accept=False)

    assert packet["overall_verdict"] == "REVISE"
    assert packet["repair_instructions"]
    assert packet["findings"][0]["severity"] == "high"
    assert packet["findings"][0]["repair_scope"] == "metric_contract"
    assert packet["recommended_repair_scope"] == "metric_contract"
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_preexecution_metric_reviewer_requires_explicit_claim_recomputation() -> None:
    payload = _review_payload(accept=True)
    payload.pop("claim_checks")

    with pytest.raises(PacketValidationError) as exc_info:
        _review(accept=True, payload=payload)

    assert "claim_checks must contain at least two explicit recomputations" in str(
        exc_info.value
    )


def test_metric_reviewer_requires_claim_check_for_every_proposed_metric() -> None:
    payload = _review_payload(accept=True)
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "empirical_metric_requirements": [
            _generic_requirement(),
            _generic_requirement(
                requirement_id="second_gate",
                metric_semantics="a second finite generic diagnostic",
            ),
        ],
    }

    with pytest.raises(PacketValidationError) as exc_info:
        _review(accept=True, payload=payload, material=material)

    assert (
        'general claim_checks are missing proposed metric requirement_ids: '
        '["second_gate"]'
    ) in str(exc_info.value)


def test_metric_reviewer_requires_explicit_normalization_and_unit_audit() -> None:
    payload = _review_payload(accept=True)
    payload["claim_checks"][0].pop("normalization_and_unit_audit")

    with pytest.raises(PacketValidationError) as exc_info:
        _review(accept=True, payload=payload)

    assert "claim check 1 missing normalization_and_unit_audit" in str(
        exc_info.value
    )


def test_metric_reviewer_rejects_pass_with_unresolved_normalization_conflict() -> None:
    payload = _review_payload(accept=True)
    payload["claim_checks"][0]["normalization_reconstruction"] = (
        _normalization_reconstruction(
            consistent=False,
            unresolved_conflicts=[
                "Literal substitution produces a different sample-size order."
            ],
        )
    )

    with pytest.raises(PacketValidationError) as exc_info:
        _review(accept=True, payload=payload)

    error = str(exc_info.value)
    assert (
        "claim check 1 cannot PASS with an inconsistent normalization "
        "reconstruction"
    ) in error
    assert (
        "claim check 1 cannot PASS with unresolved normalization conflicts"
    ) in error


def test_metric_reviewer_protocol_expression_is_runtime_bound_from_ref() -> None:
    payload = _review_payload(accept=True)
    payload["claim_checks"][0]["normalization_reconstruction"][
        "protocol_expression"
    ] = "one raw finite generic diagnostic divided by n"

    packet, backend, _ = _review(accept=True, payload=payload)

    assert len(backend.requests) == 1
    assert packet["claim_checks"][0]["normalization_reconstruction"][
        "protocol_expression"
    ] == "one raw finite generic diagnostic"
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_metric_reviewer_binds_omitted_protocol_expressions_without_retry() -> None:
    requirements = [
        _generic_requirement(
            requirement_id=f"generic_gate_{index}",
            metric_semantics=f"finite diagnostic {index}",
            measurement_protocol=f"measure finite diagnostic {index}",
            source_anchors=[f"theory:generic-gate-{index}"],
        )
        for index in range(5)
    ]
    payload = _review_payload(accept=True)
    payload["claim_checks"] = []
    for index, requirement in enumerate(requirements):
        row = deepcopy(_review_payload(accept=True)["claim_checks"][0])
        requirement_id = str(requirement["requirement_id"])
        row["requirement_id"] = requirement_id
        row["claim_ref"] = (
            f"requirement:{requirement_id}.measurement_protocol"
        )
        row["evidence_refs"] = [row["claim_ref"]]
        row["normalization_reconstruction"] = {
            **_normalization_reconstruction(),
            "protocol_expression_ref": (
                f"requirement:{requirement_id}.measurement_protocol"
            ),
        }
        row["normalization_reconstruction"].pop("protocol_expression")
        payload["claim_checks"].append(row)

    material = (
        architect_metric_review_material_with_runtime_evaluator_certificate(
            {
                "review_stage": "pre_execution_metric_contract_review",
                "execution_results_available": False,
                "empirical_metric_requirements": requirements,
            }
        )
    )

    backend = _SequenceBackend([payload])
    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model=TEST_HAIKU_MODEL,
            model_tier="haiku",
            max_repair_attempts=0,
        ),
    ).review(
        question=OpenResearchQuestion(
            id="q_metric_literal_repair",
            title="Repair literal metric lineage",
            description="Review five generic pre-execution diagnostics.",
        ),
        review_material=material,
        trusted_lineage={
            "authoring_packet_id": "metric-authoring:literal-repair",
            "authoring_packet_hash": stable_hash(
                {"candidate": "literal-repair"}
            ),
            "empirical_metric_requirement_set_id": (
                generated_metric_requirement_set_id(requirements)
            ),
            "source_agent": "ArchitectMetricContractPlanner",
            "source_model": TEST_HAIKU_MODEL,
            "source_model_tier": "haiku",
        },
    )

    assert len(backend.requests) == 1
    assert packet["llm_json_repair_attempts"] == 0
    assert [
        row["normalization_reconstruction"]["protocol_expression"]
        for row in packet["claim_checks"]
    ] == [
        str(requirement["measurement_protocol"])
        for requirement in requirements
    ]
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_theory_bound_metric_review_requires_scope_consistency_check() -> None:
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "empirical_metric_requirements": [
            _generic_requirement(
                acceptance_authority_kind="theory_derived",
                acceptance_authority_rationale=(
                    "The cited theory node derives this generic gate."
                ),
                source_anchors=[
                    "theory:generic-gate",
                    "theory:generic-sanity",
                ],
            )
        ],
        "theory_developer_protocol_material": {
            "source_theory_packet_id": "theory:scope-check",
            "source_theory_packet_hash": stable_hash({"theory": "scope-check"}),
            "theory_semantic_material": {
                "theorem_cards": [
                    {
                        "id": "theorem:generic",
                        "conclusion": "The claim holds throughout the stated domain.",
                    }
                ],
                "sanity_checks": [
                    {
                        "id": "check:special-case",
                        "result": "The identity holds at one special value.",
                    }
                ],
            },
        },
    }
    with pytest.raises(PacketValidationError) as exc_info:
        _review(accept=True, material=material)

    assert (
        "theory-bound pre-execution review requires exactly one "
        "theory_scope_consistency claim check for requirement_id generic_gate"
    ) in str(exc_info.value)

    wrong_type_payload = _review_payload(accept=True)
    wrong_type_payload["claim_checks"][0]["requirement_id"] = "unknown_gate"
    with pytest.raises(PacketValidationError) as wrong_type_exc:
        _review(
            accept=True,
            payload=wrong_type_payload,
            material=material,
        )
    assert (
        "references unknown metric requirement_id unknown_gate"
        in str(wrong_type_exc.value)
    )

    missing_anchor_payload = _review_payload(accept=True)
    missing_anchor_payload["theory_scope_checks"] = {
        "generic_gate": {
            "claim_ref": "theory:generic-gate",
            "recomputation": "Compare the stated and checked parameter scopes.",
            "result": "The checked scope is narrower.",
            "verdict": "FAIL",
            "evidence_refs": ["theory:generic-gate"],
        }
    }
    with pytest.raises(PacketValidationError) as missing_anchor_exc:
        _review(
            accept=True,
            payload=missing_anchor_payload,
            material=material,
        )
    assert "must cite every source anchor" in str(missing_anchor_exc.value)
    assert "theory:generic-sanity" in str(missing_anchor_exc.value)

    payload = _review_payload(accept=True)
    payload["theory_scope_checks"] = {
        "generic_gate": {
            "claim_ref": "theory:generic-gate",
            "recomputation": "Compare the stated and checked parameter scopes.",
            "result": "The checked scope covers the stated scope.",
            "verdict": "PASS",
            "evidence_refs": [
                "theory:generic-gate",
                "theory:generic-sanity",
            ],
        }
    }
    packet, _, _ = _review(
        accept=True,
        payload=payload,
        material=material,
    )

    assert packet["theory_scope_check_required"] is True
    assert packet["source_theory_packet_id"] == "theory:scope-check"
    assert validate_architect_metric_semantic_review_packet(packet) == []

    contextless_material = {
        key: value
        for key, value in material.items()
        if key != "theory_developer_protocol_material"
    }
    with pytest.raises(PacketValidationError) as context_exc:
        _review(
            accept=True,
            payload=payload,
            material=contextless_material,
        )
    assert (
        "requires exact source theory lineage and semantic material"
        in str(context_exc.value)
    )


def test_metric_review_requires_primitive_identity_audit_before_coding() -> None:
    formula_ref = "theory#/estimator_specs/0/formula"
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "empirical_metric_requirements": [_generic_requirement()],
        "theory_developer_protocol_material": {
            "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
            "source_theory_packet_id": "theory:primitive-check",
            "source_theory_packet_hash": stable_hash(
                {"theory": "primitive-check"}
            ),
            "theory_semantic_material": {
                "estimator_specs": [
                    {
                        "id": "generic_estimator",
                        "formula": "T = numerator / denominator",
                        "algorithm_sketch": "compute numerator then divide",
                        "required_assumptions": ["denominator is positive"],
                        "estimand_alignment": "T targets theta",
                    }
                ]
            },
            "execution_results_available": False,
        },
    }
    payload = _review_payload(accept=True)
    payload["claim_checks"][0].update(
        {
            "claim_ref": "theory#/theorem_cards/0/statement",
            "recomputation": (
                "Derive T from the primitive numerator, denominator, and target "
                "equation; check a non-degenerate boundary, one substitution, "
                "and the positive-denominator domain."
            ),
            "normalization_and_unit_audit": (
                "Numerator and denominator have the declared compatible units."
            ),
            "result": "The primitive reconstruction matches the proposed formula.",
            "evidence_refs": [
                "theory#/estimator_specs/0/required_assumptions"
            ],
        }
    )
    payload["foundational_identity_claim_check_indices"] = {
        "generic_estimator": 0
    }
    packet, backend, enriched_material = _review(
        accept=True,
        payload=payload,
        material=material,
    )

    foundational_rows = packet["metric_claim_check_contract"][
        "foundational_identity_rows"
    ]
    assert foundational_rows[0][
        "estimator_id"
    ] == "generic_estimator"
    assert validate_architect_metric_semantic_review_packet(packet) == []
    identity_schema = backend.requests[0].schema["properties"][
        "foundational_identity_claim_check_indices"
    ]
    assert identity_schema["required"] == ["generic_estimator"]
    assert identity_schema["properties"]["generic_estimator"] == {
        "type": "integer",
        "minimum": 0,
    }
    bound_check = next(
        row for row in packet["claim_checks"] if row["claim_ref"] == formula_ref
    )
    assert bound_check["evidence_refs"][0] == formula_ref
    assert enriched_material["metric_claim_check_contract"][
        "foundational_identity_rows"
    ] == foundational_rows

    missing_payload = deepcopy(payload)
    missing_payload.pop("foundational_identity_claim_check_indices")
    with pytest.raises(PacketValidationError) as exc_info:
        _review(
            accept=True,
            payload=missing_payload,
            material=material,
        )
    assert (
        "claim_checks must include a primitive identity reconstruction"
        in str(exc_info.value)
    )

    spoofed_payload = deepcopy(payload)
    spoofed_payload["claim_checks"][0]["claim_ref"] = (
        "theory#/estimator_specs/99/formula"
    )
    spoofed_packet, _, _ = _review(
        accept=True,
        payload=spoofed_payload,
        material=material,
    )
    spoofed_check = next(
        row
        for row in spoofed_packet["claim_checks"]
        if row["claim_ref"] == formula_ref
    )
    assert spoofed_check["claim_ref"] == formula_ref
    assert validate_architect_metric_semantic_review_packet(spoofed_packet) == []

    repair_context = _architect_metric_semantic_review_repair_context(
        enriched_material,
        invalid_packet=missing_payload,
        errors=[
            "claim_checks must include a primitive identity reconstruction for "
            f"estimator_id generic_estimator at claim_ref {formula_ref}"
        ],
    )
    repair_instructions = " ".join(
        repair_context["repair_prompt_priority_instructions"]
    )
    assert "foundational_identity_rows" in repair_instructions
    assert "zero-based index" in repair_instructions
    assert "Runtime binds that indexed row" in repair_instructions
    assert "Use distinct indices" in repair_instructions


def test_mixed_field_authority_keeps_theory_scope_review_visible() -> None:
    mixed = _generic_requirement(
        tolerance=0.02,
        source_anchors=["theory:generic-gate", "question:generic"],
        acceptance_authority_kind="architect_preregistered_design",
        acceptance_authority_rationale=(
            "The threshold is theory-derived and the tolerance is "
            "preregistered."
        ),
        gate_field_authorities=[
            {
                "field": "threshold",
                "authority_kind": "theory_derived",
                "source_anchors": ["theory:generic-gate"],
                "rationale": "The cited theory node supplies the threshold.",
            },
            {
                "field": "tolerance",
                "authority_kind": "architect_preregistered_design",
                "source_anchors": ["question:generic"],
                "rationale": (
                    "The Architect freezes the comparison tolerance before "
                    "execution."
                ),
            },
        ],
    )

    contract = _architect_metric_theory_scope_check_contract([mixed])

    assert contract["required"] is True
    assert contract["rows"] == [
        {
            "requirement_id": "generic_gate",
            "acceptance_authority_kind": (
                "architect_preregistered_design"
            ),
            "source_anchors": ["theory:generic-gate"],
            "theory_authority_fields": [
                {
                    "field": "threshold",
                    "authority_kind": "theory_derived",
                    "source_anchors": ["theory:generic-gate"],
                }
            ],
        }
    ]
    architect_only = {
        **mixed,
        "gate_field_authorities": [
            {
                **row,
                "authority_kind": "architect_preregistered_design",
            }
            for row in mixed["gate_field_authorities"]
        ],
    }
    assert _architect_metric_theory_scope_check_contract(
        [architect_only]
    )["required"] is False


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
            model=TEST_HAIKU_MODEL,
            model_tier="haiku",
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
            "source_model": TEST_HAIKU_MODEL,
            "source_model_tier": "haiku",
        },
    )

    assert packet["recommended_repair_scope"] == "upstream_theory"
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_preexecution_metric_reviewer_accepts_separate_same_model_invocation() -> None:
    packet, _, _ = _review(accept=True, reviewer_model=TEST_HAIKU_MODEL)

    assert packet["independent_agent"] is True
    assert packet["independent_invocation"] is True
    assert packet["independent_model"] is False


def test_metric_reviewer_repair_preserves_exact_active_finding_context() -> None:
    active_ledger = [
        {
            "finding_id": "metric-finding:calibration",
            "finding": {
                "summary": "The calibration was unsupported.",
                "evidence_refs": ["requirement:generic_gate.operator"],
            },
        },
        {
            "finding_id": "metric-finding:measurement",
            "finding": {
                "summary": "The measurement was not identifiable.",
                "evidence_refs": [
                    "requirement:generic_gate.measurement_protocol"
                ],
            },
        },
    ]
    invalid_payload = _review_payload(accept=True)
    invalid_payload["claim_checks"][1]["verdict"] = "FAIL"
    invalid_payload["claim_checks"][1]["result"] = (
        "The rejected packet retained a contradictory calculation."
    )
    repaired_payload = _review_payload(accept=True)
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
    snapshots_by_finding_id = {
        str(row["finding_id"]): str(row["snapshot_id"])
        for row in material["active_prior_finding_current_evidence"]
    }
    repaired_payload["prior_finding_reviews"] = [
        {
            "finding_id": row["finding_id"],
            "status": "RESOLVED",
            "runtime_contract_evidence_id": "",
            "rationale": "The current candidate explicitly implements the repair.",
            "evidence_refs": [
                snapshots_by_finding_id[str(row["finding_id"])]
            ],
        }
        for row in active_ledger
    ]

    def typed_repair(request):
        repair_request = json.loads(request.user_prompt.split("\n\n", 1)[1])
        return {
            "base_payload_fingerprint": repair_request[
                "base_payload_fingerprint"
            ],
            "updates": [
                {
                    "path": ["prior_finding_reviews"],
                    "replacement_json": json.dumps(
                        repaired_payload["prior_finding_reviews"]
                    ),
                },
                {
                    "path": ["claim_checks", 1, "result"],
                    "replacement": repaired_payload["claim_checks"][1][
                        "result"
                    ],
                },
                {
                    "path": ["claim_checks", 1, "verdict"],
                    "replacement": "PASS",
                },
            ],
        }

    backend = _SequenceBackend([invalid_payload, typed_repair])

    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model=TEST_HAIKU_MODEL,
            model_tier="haiku",
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
            "source_model": TEST_HAIKU_MODEL,
            "source_model_tier": "haiku",
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
    assert repair_context["rejected_review_consistency_state"][
        "failed_claim_checks"
    ][0]["claim_check_index"] == 1
    citation_options = {
        row["finding_id"]: row
        for row in repair_context["prior_finding_citation_options"]
    }
    for finding_id in expected_ids:
        assert citation_options[finding_id]["status_citation_contract"][
            "RESOLVED"
        ]["eligible_snapshot_ids"] == [
            snapshots_by_finding_id[finding_id]
        ]
    assert repair_payload["local_validation_errors"]
    assert backend.requests[1].metadata["json_repair_mode"] == (
        "typed_semantic_patch"
    )
    assert backend.requests[1].model == TEST_HAIKU_MODEL
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


def test_metric_reviewer_materializes_current_theory_evidence_for_prior_finding() -> None:
    finding_id = "metric-finding:revised-theory-value"
    evidence_ref = (
        "theory#/theory_derivation_packet/assumption_ledger/0/assumption"
    )
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "active_prior_finding_ledger": [
            {
                "finding_id": finding_id,
                "status": "UNRESOLVED",
                "finding": {
                    "category": "generic_bound",
                    "summary": "The prior theory used old_limit.",
                    "required_change": "Replace old_limit with a justified value.",
                    "repair_scope": "upstream_theory",
                    "evidence_refs": [evidence_ref],
                },
            }
        ],
        "theory_developer_protocol_material": {
            "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
            "source_theory_packet_id": "theory:current",
            "source_theory_packet_hash": "current-theory-hash",
            "theory_semantic_material": {
                "theory_derivation_packet": {
                    "assumption_ledger": [
                        {"assumption": "generic bound = new_limit"}
                    ]
                }
            },
            "execution_results_available": False,
        },
        "acceptance_authority_catalog": [
            {
                "anchor_id": evidence_ref,
                "authority_kind": "theory_derived",
                "content": "generic bound = new_limit",
            }
        ],
        "empirical_metric_requirements": [_generic_requirement()],
    }
    snapshots = architect_metric_active_prior_finding_current_evidence(
        material
    )
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot["finding_id"] == finding_id
    assert snapshot["evidence_ref"] == evidence_ref
    assert snapshot["artifact_role"] == "source_theory_packet"
    assert snapshot["exists"] is True
    assert snapshot["current_value"] == "generic bound = new_limit"
    assert snapshot["current_value_fingerprint"] == stable_hash(
        "generic bound = new_limit"
    )

    payload = _review_payload(accept=True)
    payload["prior_finding_reviews"] = [
        {
            "finding_id": finding_id,
            "status": "RESOLVED_BY_CURRENT_THEORY",
            "runtime_contract_evidence_id": "",
            "rationale": (
                "The exact current theory value replaces the old premise."
            ),
            "evidence_refs": [snapshot["snapshot_id"]],
        }
    ]
    packet, backend, _ = _review(
        accept=True,
        payload=payload,
        material=material,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["active_prior_finding_current_evidence"] == snapshots
    assert validate_architect_metric_semantic_review_packet(packet) == []
    assert "generic bound = new_limit" in backend.requests[0].user_prompt
    assert "Never retain an old finding because hidden" in (
        backend.requests[0].user_prompt
    )


def test_metric_reviewer_runtime_binds_candidate_evidence_for_resolved_status() -> None:
    finding_id = "metric-finding:repaired-candidate-threshold"
    evidence_ref = "requirement:generic_gate.threshold"
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "active_prior_finding_ledger": [
            {
                "finding_id": finding_id,
                "status": "UNRESOLVED",
                "finding": {
                    "category": "generic_threshold",
                    "summary": "The prior candidate used the wrong threshold.",
                    "required_change": "Replace the candidate threshold.",
                    "repair_scope": "metric_contract",
                    "evidence_refs": [evidence_ref],
                },
            }
        ],
        "empirical_metric_requirements": [_generic_requirement()],
    }
    snapshots = architect_metric_active_prior_finding_current_evidence(
        material
    )
    candidate_snapshot = next(
        row
        for row in snapshots
        if row["artifact_role"] == "metric_protocol_candidate"
    )
    payload = _review_payload(accept=True)
    payload["prior_finding_reviews"] = [
        {
            "finding_id": finding_id,
            "status": "RESOLVED",
            "runtime_contract_evidence_id": "",
            "rationale": "The current candidate replaces the defective value.",
            "evidence_refs": ["theory#/theorem_cards/0/conclusion"],
        }
    ]

    packet, _, _ = _review(
        accept=True,
        payload=payload,
        material=material,
    )

    assert candidate_snapshot["snapshot_id"] in packet[
        "prior_finding_reviews"
    ][0]["evidence_refs"]
    assert validate_architect_metric_semantic_review_packet(packet) == []


@pytest.mark.parametrize(
    ("evidence_ref", "expected_value"),
    [
        (
            "empirical_metric_requirements/0/measurement_protocol",
            "return one raw generic diagnostic value",
        ),
        (
            "candidate#/empirical_metric_requirements/0/operator",
            "<=",
        ),
        (
            "metric_protocol_candidate#/empirical_metric_requirements/0/tolerance",
            0.0,
        ),
    ],
)
def test_metric_reviewer_materializes_current_candidate_pointer_evidence(
    evidence_ref: str,
    expected_value: object,
) -> None:
    finding_id = "metric-finding:current-candidate-pointer"
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "active_prior_finding_ledger": [
            {
                "finding_id": finding_id,
                "status": "UNRESOLVED",
                "finding": {
                    "category": "generic_candidate_defect",
                    "summary": "The prior candidate field was defective.",
                    "required_change": "Recheck the exact current candidate field.",
                    "repair_scope": "metric_contract",
                    "evidence_refs": [evidence_ref],
                },
            }
        ],
        "empirical_metric_requirements": [_generic_requirement()],
    }

    snapshot = architect_metric_active_prior_finding_current_evidence(
        material
    )[0]

    assert snapshot["evidence_ref"] == evidence_ref
    assert snapshot["artifact_role"] == "metric_protocol_candidate"
    assert snapshot["exists"] is True
    assert snapshot["current_value"] == expected_value
    assert snapshot["current_value_fingerprint"] == stable_hash(
        expected_value
    )


def test_metric_finding_tracks_named_row_across_list_reordering() -> None:
    evidence_ref = (
        "theory#/theory_derivation_packet/sanity_checks/1/result"
    )

    def material(sanity_checks: list[dict[str, str]]) -> dict[str, object]:
        theory_protocol_material = {
            "theory_semantic_material": {
                "theory_derivation_packet": {
                    "sanity_checks": sanity_checks,
                }
            }
        }
        return {
            "acceptance_authority_catalog": (
                generated_metric_acceptance_authority_catalog(
                    question={
                        "title": "Generic",
                        "description": "Generic review",
                    },
                    runtime_contract={"simulation_targets": []},
                    theory_protocol_material=theory_protocol_material,
                )
            ),
            "theory_developer_protocol_material": theory_protocol_material,
        }

    original_material = material(
        [
            {"claim_ref": "ROW_A", "result": "unrelated"},
            {"claim_ref": "ROW_TARGET", "result": "old defective value"},
        ]
    )
    finding_id = "metric-finding:named-row"
    bound_finding = bind_architect_metric_finding_evidence_identities(
        findings=[
            {
                "finding_id": finding_id,
                "category": "generic_identity",
                "summary": "The named row is defective.",
                "required_change": "Repair that exact named row.",
                "repair_scope": "upstream_theory",
                "evidence_refs": [evidence_ref],
            }
        ],
        review_material=original_material,
    )[0]
    revised_material = material(
        [
            {"claim_ref": "ROW_TARGET", "result": "corrected current value"},
            {"claim_ref": "ROW_A", "result": "unrelated"},
        ]
    )

    snapshot = architect_metric_active_prior_finding_current_evidence(
        {
            **revised_material,
            "active_prior_finding_ledger": [
                {
                    "finding_id": finding_id,
                    "status": "UNRESOLVED",
                    "finding": bound_finding,
                }
            ],
        }
    )[0]

    assert snapshot["evidence_ref"] == evidence_ref
    assert snapshot["exists"] is True
    assert snapshot["current_value"] == "corrected current value"
    assert snapshot["semantic_binding"]["identity_status"] == (
        "SEMANTIC_IDENTITY_MATCH"
    )
    assert snapshot["semantic_binding"]["resolved_evidence_ref"] == (
        "theory#/theory_derivation_packet/sanity_checks/0/result"
    )


def test_metric_finding_rejects_stale_positional_row_rebinding() -> None:
    evidence_ref = (
        "theory#/theory_derivation_packet/sanity_checks/1/result"
    )

    def material(sanity_checks: list[dict[str, str]]) -> dict[str, object]:
        theory_protocol_material = {
            "theory_semantic_material": {
                "theory_derivation_packet": {
                    "sanity_checks": sanity_checks,
                }
            }
        }
        return {
            "acceptance_authority_catalog": (
                generated_metric_acceptance_authority_catalog(
                    question={
                        "title": "Generic",
                        "description": "Generic review",
                    },
                    runtime_contract={"simulation_targets": []},
                    theory_protocol_material=theory_protocol_material,
                )
            ),
            "theory_developer_protocol_material": theory_protocol_material,
        }

    original_material = material(
        [
            {"claim_ref": "ROW_A", "result": "unrelated"},
            {"claim_ref": "ROW_TARGET", "result": "old defective value"},
        ]
    )
    finding_id = "metric-finding:removed-row"
    bound_finding = bind_architect_metric_finding_evidence_identities(
        findings=[
            {
                "finding_id": finding_id,
                "category": "generic_identity",
                "summary": "The named row is defective.",
                "required_change": "Repair that exact named row.",
                "repair_scope": "upstream_theory",
                "evidence_refs": [evidence_ref],
            }
        ],
        review_material=original_material,
    )[0]
    revised_material = material(
        [
            {"claim_ref": "ROW_A", "result": "unrelated"},
            {
                "claim_ref": "ROW_DIFFERENT",
                "result": "semantically different current row",
            },
        ]
    )

    snapshot = architect_metric_active_prior_finding_current_evidence(
        {
            **revised_material,
            "active_prior_finding_ledger": [
                {
                    "finding_id": finding_id,
                    "status": "UNRESOLVED",
                    "finding": bound_finding,
                }
            ],
        }
    )[0]

    assert snapshot["exists"] is False
    assert snapshot["current_value"] is None
    semantic_binding = snapshot["semantic_binding"]
    assert semantic_binding["identity_status"] == (
        "SEMANTIC_IDENTITY_MISSING_AFTER_REVISION"
    )
    assert semantic_binding["positional_path_exists"] is True
    assert semantic_binding["semantic_identity_match"] is False


def test_metric_reviewer_rejects_unresolved_prior_without_existing_snapshot() -> None:
    finding_id = "metric-finding:missing-current-path"
    evidence_ref = (
        "theory#/theory_derivation_packet/assumption_ledger/9/assumption"
    )
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "active_prior_finding_ledger": [
            {
                "finding_id": finding_id,
                "status": "UNRESOLVED",
                "finding": {
                    "category": "generic_bound",
                    "summary": "The prior theory used an unsupported bound.",
                    "required_change": "Ground the bound in current theory.",
                    "repair_scope": "upstream_theory",
                    "evidence_refs": [evidence_ref],
                },
            }
        ],
        "theory_developer_protocol_material": {
            "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
            "source_theory_packet_id": "theory:current",
            "source_theory_packet_hash": "current-theory-hash",
            "theory_semantic_material": {
                "theory_derivation_packet": {
                    "assumption_ledger": [
                        {"assumption": "a different current premise"}
                    ]
                }
            },
            "execution_results_available": False,
        },
        "empirical_metric_requirements": [_generic_requirement()],
    }
    snapshot = architect_metric_active_prior_finding_current_evidence(
        material
    )[0]
    assert snapshot["exists"] is False
    payload = _review_payload(accept=False)
    payload["prior_finding_reviews"] = [
        {
            "finding_id": finding_id,
            "status": "UNRESOLVED",
            "runtime_contract_evidence_id": "",
            "rationale": "The old defect may still exist somewhere.",
            "evidence_refs": [snapshot["snapshot_id"]],
        }
    ]
    payload["findings"][0]["prior_finding_id"] = finding_id
    payload["findings"][0]["new_finding_rationale"] = ""
    payload["findings"][0]["evidence_refs"] = [
        snapshot["snapshot_id"],
        evidence_ref,
    ]

    with pytest.raises(PacketValidationError) as exc_info:
        _review(
            accept=False,
            payload=payload,
            material=material,
        )

    assert "must cite an exists=true current evidence snapshot" in str(
        exc_info.value
    )


def test_metric_reviewer_runtime_binds_snapshot_to_underlying_ref() -> None:
    finding_id = "metric-finding:current-candidate-defect"
    evidence_ref = "requirement:generic_gate.operator"
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "active_prior_finding_ledger": [
            {
                "finding_id": finding_id,
                "status": "UNRESOLVED",
                "finding": {
                    "category": "generic_operator",
                    "summary": "The candidate operator is incorrect.",
                    "required_change": "Repair the exact candidate operator.",
                    "repair_scope": "metric_contract",
                    "evidence_refs": [evidence_ref],
                },
            }
        ],
        "empirical_metric_requirements": [_generic_requirement()],
    }
    snapshot = architect_metric_active_prior_finding_current_evidence(
        material
    )[0]
    payload = _review_payload(accept=False)
    payload["prior_finding_reviews"] = [
        {
            "finding_id": finding_id,
            "status": "UNRESOLVED",
            "runtime_contract_evidence_id": "",
            "rationale": "The exact current operator still exhibits the defect.",
            "evidence_refs": [snapshot["snapshot_id"]],
        }
    ]
    payload["findings"][0]["prior_finding_id"] = finding_id
    payload["findings"][0]["new_finding_rationale"] = ""
    payload["findings"][0]["evidence_refs"] = [snapshot["snapshot_id"]]

    packet, _, _ = _review(
        accept=False,
        payload=payload,
        material=material,
    )
    assert packet["runtime_bound_prior_finding_evidence_ids"] == [
        finding_id
    ]
    assert snapshot["snapshot_id"] in packet["findings"][0]["evidence_refs"]
    assert evidence_ref in packet["findings"][0]["evidence_refs"]
    assert packet["overall_verdict"] == "REVISE"
    assert packet["findings"][0]["finding_id"] == finding_id
    assert validate_architect_metric_semantic_review_packet(packet) == []

    payload["findings"][0]["evidence_refs"] = [evidence_ref]
    with pytest.raises(PacketValidationError) as exc_info:
        _review(
            accept=False,
            payload=payload,
            material=material,
        )
    assert "must cite an exists=true current evidence snapshot" in str(
        exc_info.value
    )


def test_metric_reviewer_runtime_carries_forward_unresolved_prior_finding() -> None:
    finding_id = "metric-finding:runtime-owned-persistent-identity"
    evidence_refs = [
        "requirement:generic_gate.operator",
        "requirement:generic_gate.threshold",
    ]
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "active_prior_finding_ledger": [
            {
                "finding_id": finding_id,
                "status": "UNRESOLVED",
                "finding": {
                    "severity": "high",
                    "category": "generic_operator",
                    "summary": "The candidate operator is still incorrect.",
                    "required_change": "Repair the exact candidate operator.",
                    "repair_scope": "metric_contract",
                    "evidence_refs": evidence_refs,
                },
            }
        ],
        "empirical_metric_requirements": [_generic_requirement()],
    }
    snapshots = architect_metric_active_prior_finding_current_evidence(
        material
    )
    snapshots_by_ref = {
        snapshot["evidence_ref"]: snapshot for snapshot in snapshots
    }
    cited_snapshots = [
        snapshots_by_ref[evidence_ref]["snapshot_id"]
        for evidence_ref in reversed(evidence_refs)
    ]
    payload = _review_payload(accept=False)
    payload["prior_finding_reviews"] = [
        {
            "finding_id": finding_id,
            "status": "UNRESOLVED",
            "runtime_contract_evidence_id": "",
            "rationale": "The exact current operator still exhibits the defect.",
            "evidence_refs": cited_snapshots,
        }
    ]
    payload["findings"] = []

    packet, backend, _ = _review(
        accept=False,
        payload=payload,
        material=material,
    )

    assert len(backend.requests) == 1
    assert packet["runtime_carried_forward_prior_finding_ids"] == [finding_id]
    assert packet["runtime_bound_prior_finding_evidence_ids"] == [finding_id]
    assert len(packet["findings"]) == 1
    carried = packet["findings"][0]
    assert carried["finding_id"] == finding_id
    assert carried["prior_finding_id"] == finding_id
    assert carried["new_finding_rationale"] == ""
    assert carried["evidence_refs"] == [
        cited_snapshots[0],
        evidence_refs[1],
        cited_snapshots[1],
        evidence_refs[0],
    ]
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
            "empirical_metric_requirements": [
                _generic_requirement(requirement_id="gate:one")
            ],
            "active_prior_finding_ledger": [
                {"finding_id": "finding:one", "finding": {"summary": "one"}},
                {"finding_id": "finding:two", "finding": {"summary": "two"}},
            ],
            "runtime_contract_authority": {
                "allowed_retraction_evidence_ids": [
                    "generated_metric_evaluator_certificate:test"
                ]
            },
            "theory_scope_check_contract": {
                "rows": [
                    {
                        "requirement_id": "gate:one",
                        "source_anchors": ["theory:gate-one"],
                    }
                ]
            },
        }
    )
    transformed = anthropic.transform_schema(dynamic_schema)

    assert transformed["type"] == "object"
    assert "overall_verdict" not in transformed["properties"]
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
    transformed_scope_schema = transformed["properties"][
        "theory_scope_checks"
    ]
    assert transformed_scope_schema["required"] == ["gate:one"]
    assert transformed_scope_schema["properties"]["gate:one"][
        "properties"
    ]["evidence_refs"]["items"]["enum"] == ["theory:gate-one"]
    assert transformed_scope_schema["properties"]["gate:one"][
        "properties"
    ]["evidence_refs"]["minItems"] == 1
    assert transformed["properties"]["claim_checks"]["items"]["properties"][
        "requirement_id"
    ]["enum"] == ["gate:one"]
    assert "normalization_and_unit_audit" in transformed["properties"][
        "claim_checks"
    ]["items"]["properties"]
    normalization_schema = transformed["properties"]["claim_checks"]["items"][
        "properties"
    ]["normalization_reconstruction"]
    assert normalization_schema["required"] == [
        "source_expression",
        "protocol_expression_ref",
        "substitution_without_reinterpretation",
        "resulting_sample_size_order",
        "required_sample_size_order",
        "convention_consistent",
        "unresolved_conflicts",
    ]
    assert "theory_scope_consistency" not in transformed["properties"][
        "claim_checks"
    ]["items"]["properties"]["check_type"]["enum"]
    assert "minItems: 2" in transformed_prior_schema["description"]
    assert ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA["properties"][
        "prior_finding_reviews"
    ].get("minItems") is None

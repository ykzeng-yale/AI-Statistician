from __future__ import annotations

from copy import deepcopy
import json

import pytest

from ai_statistician.architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL_VERSION,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_DIMENSIONS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA,
    ArchitectMetricSemanticReviewerConfig,
    LLMArchitectMetricSemanticReviewerAgent,
    _architect_metric_theory_scope_check_contract,
    architect_metric_active_prior_finding_current_evidence,
    architect_metric_review_material_with_runtime_evaluator_certificate,
    architect_metric_semantic_review_json_schema,
    bind_architect_metric_finding_evidence_identities,
    build_architect_metric_semantic_review_prompt,
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


def _sample_size_order_derivation(
    *,
    orders_agree: bool = True,
    unresolved_assumptions: list[str] | None = None,
) -> dict[str, object]:
    return {
        "primitive_orders": [
            {
                "quantity": "theta",
                "order": "O(1)",
                "justification": "theta is the fixed estimand in the cited definition",
                "evidence_ref": "requirement:generic_gate.metric_semantics",
            }
        ],
        "composition": "metric_value = theta = O(1)",
        "orders_agree": orders_agree,
        "unresolved_assumptions": list(unresolved_assumptions or []),
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
                "sample_size_order_derivation": (
                    _sample_size_order_derivation()
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
                "sample_size_order_derivation": (
                    _sample_size_order_derivation()
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
    assert packet["review_protocol_version"] == (
        ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL_VERSION
    )
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
    review_schema = backend.requests[0].schema
    assert review_schema["properties"]["claim_checks"]["items"]["properties"][
        "recomputation"
    ]["maxLength"] == 240
    assert review_schema["properties"]["claim_checks"]["items"]["properties"][
        "sample_size_order_derivation"
    ]["properties"]["primitive_orders"]["maxItems"] == 6
    assert "protocol_expression" not in review_schema["properties"][
        "claim_checks"
    ]["items"]["properties"]["normalization_reconstruction"]["properties"]
    assert review_schema["properties"]["dimension_reviews"]["items"][
        "properties"
    ]["rationale"]["maxLength"] == 240
    request = backend.requests[0]
    prompt_payload = json.loads(request.user_prompt.split("\n\n", 1)[1])
    assert prompt_payload["review_protocol_version"] == (
        ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL_VERSION
    )
    assert prompt_payload["review_protocol"] == list(
        ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL
    )
    assert "required_output_contract" not in prompt_payload
    assert len(request.user_prompt) < 10_000
    assert request.metadata["review_prompt_chars"] == len(request.user_prompt)
    assert request.metadata["review_schema_chars"] == len(
        json.dumps(request.schema, separators=(",", ":"))
    )
    assert request.metadata["review_requirement_count"] == 1
    protocol_text = " ".join(prompt_payload["review_protocol"])
    for required_contract in (
        "foundational_identity_row",
        "normalization_reconstruction",
        "sample_size_order_derivation",
        "runtime_evaluator_certificate",
        "gate_field_authorities",
        "theory_scope_checks",
        "active prior finding",
        "upstream_theory",
        "metric_contract",
        "AgentRuntime derives the overall verdict",
        "full declared support",
        "Finite-sample evaluation",
        "nonasymptotic guarantee",
    ):
        assert required_contract in protocol_text
    assert packet["runtime_evaluator_certificate_set_id"].startswith(
        "generated_metric_evaluator_certificate_set:"
    )


def test_metric_reviewer_six_gate_prompt_and_scope_schema_stay_compact() -> None:
    requirements = [
        _generic_requirement(
            requirement_id=f"generic_gate_{index}",
            acceptance_authority_kind="theory_derived",
            acceptance_authority_rationale="The cited node derives the gate.",
            source_anchors=[f"theory:generic-gate-{index}"],
        )
        for index in range(6)
    ]
    material = architect_metric_review_material_with_runtime_evaluator_certificate(
        {
            "review_stage": "pre_execution_metric_contract_review",
            "execution_results_available": False,
            "empirical_metric_requirements": requirements,
            "theory_developer_protocol_material": {
                "source_theory_packet_id": "theory:six-gate",
                "source_theory_packet_hash": "six-gate-hash",
                "theory_semantic_material": {
                    "problem_card": {
                        "dgp": "generic sampling law",
                        "estimand": "generic target",
                    },
                    "theorem_cards": [
                        {
                            "id": "theorem:generic",
                            "conclusion": "The generic claims hold.",
                        }
                    ],
                    "proof_plan": {
                        "unused_large_formal_context": "omit-me-" + ("x" * 5000)
                    },
                },
            },
            "acceptance_authority_catalog": [
                *[
                    {
                        "anchor_id": f"theory:generic-gate-{index}",
                        "authority_kind": "theory_derived",
                        "content": f"cited gate {index}",
                    }
                    for index in range(6)
                ],
                *[
                    {
                        "anchor_id": f"theory:unrelated-{index}",
                        "authority_kind": "diagnostic_only",
                        "content": "unrelated-catalog-row-" + ("z" * 200),
                    }
                    for index in range(120)
                ],
            ],
        }
    )
    question = OpenResearchQuestion(
        id="q_six_gate",
        title="Review six generic gates",
        description="Audit a bounded generic evaluation portfolio.",
    )
    prompt = build_architect_metric_semantic_review_prompt(
        question=question,
        review_material=material,
    )
    schema = architect_metric_semantic_review_json_schema(material)
    scope_schema = schema["properties"]["theory_scope_checks"]
    scope_properties = scope_schema["items"]["properties"]
    prompt_payload = json.loads(prompt.split("\n\n", 1)[1])
    projected_material = prompt_payload["review_material"]

    assert len(prompt) < 20_000
    assert len(projected_material["acceptance_authority_catalog"]) == 6
    assert projected_material["prompt_projection"][
        "acceptance_authority_catalog_rows_total"
    ] == 126
    assert "theory:unrelated-0" not in prompt
    assert "unused_large_formal_context" not in prompt
    assert "generic sampling law" in prompt
    assert len(json.dumps(schema, separators=(",", ":"))) < 12_000
    assert scope_schema["minItems"] == 6
    assert scope_schema["maxItems"] == 6
    assert set(scope_properties) == {
        "requirement_id",
        "claim_ref",
        "recomputation",
        "result",
        "verdict",
    }
    assert scope_properties["requirement_id"]["enum"] == [
        f"generic_gate_{index}" for index in range(6)
    ]


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


def test_metric_reviewer_rejects_asserted_order_without_closed_derivation() -> None:
    payload = _review_payload(accept=True)
    payload["claim_checks"][0]["sample_size_order_derivation"] = (
        _sample_size_order_derivation(
            orders_agree=False,
            unresolved_assumptions=["The denominator order was not derived."],
        )
    )

    with pytest.raises(PacketValidationError) as exc_info:
        _review(accept=True, payload=payload)

    error = str(exc_info.value)
    assert "cannot PASS when sample-size orders do not agree" in error
    assert "cannot PASS with unresolved sample-size order assumptions" in error


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

    payload = _review_payload(accept=True)
    payload["theory_scope_checks"] = {
        "generic_gate": {
            "claim_ref": "theory:generic-gate",
            "recomputation": "Compare the stated and checked parameter scopes.",
            "result": "The checked scope covers the stated scope.",
            "verdict": "PASS",
        }
    }
    packet, backend, _ = _review(
        accept=True,
        payload=payload,
        material=material,
    )

    assert packet["theory_scope_check_required"] is True
    assert packet["source_theory_packet_id"] == "theory:scope-check"
    scope_check = next(
        row
        for row in packet["claim_checks"]
        if row["check_type"] == "theory_scope_consistency"
    )
    assert scope_check["evidence_refs"] == [
        "theory:generic-gate",
        "theory:generic-sanity",
    ]
    assert scope_check["source_anchor_binding"] == (
        "runtime_requirement_slot_binding"
    )
    assert scope_check["runtime_selected_semantics"] is False
    assert validate_architect_metric_semantic_review_packet(packet) == []
    scope_check["evidence_refs"] = ["theory:generic-gate"]
    assert any(
        "runtime source-anchor binding mismatch" in error
        for error in validate_architect_metric_semantic_review_packet(packet)
    )
    scope_schema = backend.requests[0].schema["properties"][
        "theory_scope_checks"
    ]["items"]
    assert set(scope_schema["properties"]) == {
        "requirement_id",
        "claim_ref",
        "recomputation",
        "result",
        "verdict",
    }
    assert backend.requests[0].metadata["review_theory_scope_check_count"] == 1

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
                "problem_card": {
                    "dgp": "Y is generated from the declared sampling law.",
                    "estimand": "theta is the target functional of that law.",
                },
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
                "theory#/estimator_specs/0/required_assumptions",
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
    assert {
        "theory#/problem_card/dgp",
        "theory#/problem_card/estimand",
        "theory#/estimator_specs/0/algorithm_sketch",
    }.issubset(set(bound_check["evidence_refs"]))
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

def test_metric_review_audits_every_estimator_response_semantic_independently() -> None:
    formula_ref = "theory#/estimator_specs/0/formula"
    material = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "empirical_metric_requirements": [_generic_requirement()],
        "theory_developer_protocol_material": {
            "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
            "source_theory_packet_id": "theory:response-identity",
            "source_theory_packet_hash": stable_hash(
                {"theory": "response-identity"}
            ),
            "theory_semantic_material": {
                "estimator_specs": [
                    {
                        "id": "generic_estimator",
                        "formula": "T_n = sum_i X_i / n",
                        "estimator_interface_contract_id": "interface:generic",
                        "estimator_interface_contract": {
                            "request_fields": [
                                {
                                    "name": "sample",
                                    "meaning": "n observations",
                                    "binding": "per_replicate_data",
                                }
                            ],
                            "response_fields": [
                                {
                                    "name": "estimate",
                                    "meaning": "T_n = sum_i X_i / n",
                                    "normalization": "finite-sample sample mean",
                                    "sample_size_order": "O_p(1)",
                                    "sample_size_rate": {
                                        "scale": "constant",
                                        "index_symbol": "n",
                                        "polynomial_exponent": 0.0,
                                        "log_exponent": 0.0,
                                        "contributions": [
                                            {
                                                "quantity": "sum_i X_i over n terms",
                                                "polynomial_exponent": 1.0,
                                                "log_exponent": 0.0,
                                                "justification_ref": "D1",
                                            },
                                            {
                                                "quantity": "division by n",
                                                "polynomial_exponent": -1.0,
                                                "log_exponent": 0.0,
                                                "justification_ref": "D1",
                                            },
                                        ],
                                    },
                                    "derivation_ref": "D1",
                                }
                            ],
                        },
                    }
                ]
            },
            "execution_results_available": False,
        },
    }
    enriched = architect_metric_review_material_with_runtime_evaluator_certificate(
        material
    )
    response_row = enriched["metric_claim_check_contract"][
        "response_identity_rows"
    ][0]
    audit_id = response_row["response_identity_audit_id"]
    payload = _review_payload(accept=True)
    payload["claim_checks"] = [
        {
            "requirement_id": "generic_gate",
            "claim_ref": "requirement:generic_gate.metric_semantics",
            "check_type": "direct_substitution",
            "recomputation": "Substitute the finite diagnostic into the gate.",
            "normalization_reconciliation": (
                "The diagnostic and threshold are on the same unitless scale."
            ),
            "sample_size_order_reconciliation": (
                "The gate compares two O_p(1) quantities."
            ),
            "normalization_consistent": True,
            "sample_size_order_consistent": True,
            "unresolved_conflicts": [],
            "result": "The declared metric is finite and scalar.",
            "verdict": "PASS",
            "evidence_refs": ["requirement:generic_gate.metric_semantics"],
        },
        {
            "requirement_id": "generic_gate",
            "claim_ref": "requirement:generic_gate.operator",
            "check_type": "pass_set_translation",
            "recomputation": "Translate the pass set as value <= 0.1.",
            "normalization_reconciliation": (
                "The scalar value and threshold use the same units."
            ),
            "sample_size_order_reconciliation": (
                "Identity aggregation preserves the O_p(1) scale."
            ),
            "normalization_consistent": True,
            "sample_size_order_consistent": True,
            "unresolved_conflicts": [],
            "result": "The pass set matches the frozen protocol.",
            "verdict": "PASS",
            "evidence_refs": ["requirement:generic_gate.operator"],
        },
    ]
    payload["response_identity_checks"] = [
        {
            "response_identity_audit_id": audit_id,
            "primitive_reconstruction": (
                "sum_i X_i has order n and division by n yields order one."
            ),
            "independently_derived_sample_size_order": "O_p(1)",
            "derived_polynomial_exponent": 0.0,
            "derived_log_exponent": 0.0,
            "convention_consistent": True,
            "unresolved_conflicts": [],
            "verdict": "PASS",
        }
    ]
    payload["foundational_identity_claim_check_indices"] = {
        "generic_estimator": 0
    }

    packet, backend, _ = _review(
        accept=True,
        payload=payload,
        material=material,
    )

    response_check = next(
        row
        for row in packet["response_identity_checks"]
        if row["response_identity_audit_id"] == audit_id
    )
    assert response_check["claim_ref"] == response_row["meaning_ref"]
    assert response_check["bound_response_semantics"] == response_row
    assert response_check["declared_normalization"] == response_row[
        "normalization"
    ]
    assert response_check["declared_sample_size_order"] == response_row[
        "sample_size_order"
    ]
    assert response_check["declared_sample_size_rate"] == response_row[
        "sample_size_rate"
    ]
    assert response_check["derived_rate_matches_declared"] is True
    assert {
        response_row["meaning_ref"],
        response_row["normalization_ref"],
        response_row["sample_size_order_ref"],
        response_row["sample_size_rate_ref"],
        response_row["derivation_ref_ref"],
        response_row["estimator_formula_ref"],
    }.issubset(set(response_check["evidence_refs"]))
    assert backend.requests[0].metadata["review_response_identity_count"] == 1
    compact_schema = backend.requests[0].schema["properties"]["claim_checks"][
        "items"
    ]["properties"]
    assert "normalization_reconciliation" in compact_schema
    assert "normalization_reconstruction" not in compact_schema
    response_required = backend.requests[0].schema["properties"][
        "response_identity_checks"
    ]["items"]["required"]
    assert "derived_polynomial_exponent" in response_required
    assert "derived_log_exponent" in response_required
    assert validate_architect_metric_semantic_review_packet(packet) == []
    failed_audit_payload = deepcopy(payload)
    failed_audit = failed_audit_payload["response_identity_checks"][0]
    failed_audit["derived_polynomial_exponent"] = -0.5
    failed_audit["convention_consistent"] = False
    failed_audit["unresolved_conflicts"] = [
        "The independently derived O_p(n^-1/2) rate disagrees with the declared O_p(1) rate."
    ]
    failed_audit["verdict"] = "FAIL"
    failed_audit_payload["overall_verdict"] = "REVISE"
    failed_audit_payload["repair_instructions"] = [
        "Regenerate the complete upstream theory packet using this audit conflict."
    ]

    failed_audit_packet, _, _ = _review(
        accept=False,
        payload=failed_audit_payload,
        material=material,
    )

    assert failed_audit_packet["overall_verdict"] == "REVISE"
    assert failed_audit_packet["findings"] == []
    assert all(
        row["status"] == "PASS"
        for row in failed_audit_packet["dimension_reviews"]
    )
    assert failed_audit_packet["recommended_repair_scope"] == "upstream_theory"
    assert failed_audit_packet["response_identity_checks"][0]["verdict"] == "FAIL"
    assert validate_architect_metric_semantic_review_packet(failed_audit_packet) == []

    not_indexed_material = deepcopy(material)
    not_indexed_rate = not_indexed_material[
        "theory_developer_protocol_material"
    ]["theory_semantic_material"]["estimator_specs"][0][
        "estimator_interface_contract"
    ]["response_fields"][0]["sample_size_rate"]
    not_indexed_rate.clear()
    not_indexed_rate["scale"] = "not_indexed"
    not_indexed_enriched = (
        architect_metric_review_material_with_runtime_evaluator_certificate(
            not_indexed_material
        )
    )
    not_indexed_audit_id = not_indexed_enriched[
        "metric_claim_check_contract"
    ]["response_identity_rows"][0]["response_identity_audit_id"]
    not_indexed_payload = deepcopy(payload)
    not_indexed_check = not_indexed_payload["response_identity_checks"][0]
    not_indexed_check["response_identity_audit_id"] = not_indexed_audit_id
    not_indexed_check["derived_polynomial_exponent"] = 0.0
    not_indexed_check["derived_log_exponent"] = 0.0

    not_indexed_packet, _, _ = _review(
        accept=True,
        payload=not_indexed_payload,
        material=not_indexed_material,
    )

    assert not_indexed_packet["response_identity_checks"][0][
        "derived_rate_matches_declared"
    ] is True
    assert validate_architect_metric_semantic_review_packet(
        not_indexed_packet
    ) == []

    inconsistent_material = deepcopy(material)
    inconsistent_rate = inconsistent_material[
        "theory_developer_protocol_material"
    ]["theory_semantic_material"]["estimator_specs"][0][
        "estimator_interface_contract"
    ]["response_fields"][0]["sample_size_rate"]
    inconsistent_rate["polynomial_exponent"] = -1.0
    inconsistent_enriched = (
        architect_metric_review_material_with_runtime_evaluator_certificate(
            inconsistent_material
        )
    )
    inconsistent_audit_id = inconsistent_enriched["metric_claim_check_contract"][
        "response_identity_rows"
    ][0]["response_identity_audit_id"]
    inconsistent_payload = deepcopy(payload)
    inconsistent_payload["response_identity_checks"][0][
        "response_identity_audit_id"
    ] = inconsistent_audit_id
    with pytest.raises(PacketValidationError) as inconsistent_exc:
        _review(
            accept=True,
            payload=inconsistent_payload,
            material=inconsistent_material,
        )
    assert "cannot PASS with an invalid TheoryDeveloper sample-size rate" in str(
        inconsistent_exc.value
    )

    mismatched_review = deepcopy(payload)
    mismatched_review["response_identity_checks"][0][
        "derived_polynomial_exponent"
    ] = -1.0
    with pytest.raises(PacketValidationError) as mismatched_exc:
        _review(
            accept=True,
            payload=mismatched_review,
            material=material,
        )
    assert "independently derived exponents disagree" in str(
        mismatched_exc.value
    )

    missing_mapping = deepcopy(payload)
    missing_mapping.pop("response_identity_checks")
    with pytest.raises(PacketValidationError) as missing_exc:
        _review(
            accept=True,
            payload=missing_mapping,
            material=material,
        )
    assert "exactly one independent response identity audit" in str(
        missing_exc.value
    )

    foundational_rows = packet["metric_claim_check_contract"][
        "foundational_identity_rows"
    ]
    assert len(foundational_rows) == 1
    assert foundational_rows[0]["estimator_id"] == "generic_estimator"
    assert foundational_rows[0]["required_claim_ref"] == formula_ref
    assert formula_ref == response_row["estimator_formula_ref"]


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
    assert "UNCERTAIN is advisory" in backend.requests[0].user_prompt


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

    def regenerate_packet(_request):
        return deepcopy(repaired_payload)

    backend = _SequenceBackend([invalid_payload, regenerate_packet])

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
    assert repair_payload["original_request"] == backend.requests[0].user_prompt
    assert "subsystem_repair_context" not in repair_payload
    assert repair_payload["previous_candidate"]
    assert all(
        finding_id in repair_payload["original_request"]
        for finding_id in expected_ids
    )
    assert repair_payload["local_validation_errors"]
    assert backend.requests[1].metadata["json_repair_mode"] == (
        "full_packet_regeneration"
    )
    assert backend.requests[1].model == TEST_HAIKU_MODEL
    assert packet["expected_prior_finding_ids"] == expected_ids
    assert [row["finding_id"] for row in packet["prior_finding_reviews"]] == (
        expected_ids
    )
    assert packet["llm_json_repair_attempts"] == 1
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_metric_reviewer_regenerates_complete_packet_in_one_retry() -> None:
    second_requirement = _generic_requirement(
        requirement_id="second_gate",
        source_anchors=["theory:second-gate"],
    )
    material = architect_metric_review_material_with_runtime_evaluator_certificate(
        {
            "review_stage": "pre_execution_metric_contract_review",
            "execution_results_available": False,
            "empirical_metric_requirements": [
                _generic_requirement(),
                second_requirement,
            ],
        }
    )
    initial_payload = _review_payload(accept=True)
    second_check = deepcopy(initial_payload["claim_checks"][0])
    second_check.update(
        {
            "requirement_id": "second_gate",
            "claim_ref": "requirement:second_gate.metric_semantics",
            "check_type": "diagnostic_boundary",
            "evidence_refs": ["requirement:second_gate.metric_semantics"],
        }
    )
    second_check["normalization_reconstruction"].update(
        {
            "protocol_expression_ref": (
                "requirement:second_gate.metric_semantics"
            ),
            "protocol_expression": second_requirement["metric_semantics"],
        }
    )
    second_check["sample_size_order_derivation"]["primitive_orders"][0][
        "evidence_ref"
    ] = "requirement:second_gate.metric_semantics"

    def regenerate_complete_packet(_request):
        repaired = deepcopy(initial_payload)
        repaired["claim_checks"] = [
            *repaired["claim_checks"],
            second_check,
        ]
        repaired["claim_checks"][-1]["check_type"] = "direct_substitution"
        return repaired

    backend = _SequenceBackend([initial_payload, regenerate_complete_packet])
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
            id="q_metric_progressive_repair",
            title="Review two generic statistical gates",
            description="Check two independent pre-execution metric contracts.",
        ),
        review_material=material,
        trusted_lineage={
            "authoring_packet_id": "metric-authoring:progressive-repair",
            "authoring_packet_hash": stable_hash(
                {"candidate": "progressive-repair"}
            ),
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

    assert len(backend.requests) == 2
    assert backend.requests[1].metadata["json_repair_mode"] == (
        "full_packet_regeneration"
    )
    assert packet["llm_json_repair_attempts"] == 1
    assert {
        row["requirement_id"] for row in packet["claim_checks"]
    } == {"generic_gate", "second_gate"}
    assert validate_architect_metric_semantic_review_packet(packet) == []


def test_metric_reviewer_regenerates_invalid_finding_from_full_context() -> None:
    material = architect_metric_review_material_with_runtime_evaluator_certificate(
        {
            "review_stage": "pre_execution_metric_contract_review",
            "execution_results_available": False,
            "empirical_metric_requirements": [_generic_requirement()],
        }
    )
    invalid_payload = _review_payload(accept=False)
    invalid_payload["findings"][0]["repair_scope"] = "algorithm_code"
    invalid_payload["findings"][0]["evidence_refs"] = []
    captured_repair_request: dict[str, object] = {}

    def repair_finding(request):
        repair_request = json.loads(request.user_prompt.split("\n\n", 1)[1])
        captured_repair_request.update(repair_request)
        repaired = deepcopy(invalid_payload)
        repaired["findings"][0]["repair_scope"] = "metric_contract"
        repaired["findings"][0]["evidence_refs"] = [
            "requirement:generic_gate"
        ]
        return repaired

    backend = _SequenceBackend([invalid_payload, repair_finding])
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
            id="q_metric_finding_focus",
            title="Review a generic statistical gate",
            description="Check one pre-execution metric contract.",
        ),
        review_material=material,
        trusted_lineage={
            "authoring_packet_id": "metric-authoring:finding-focus",
            "authoring_packet_hash": stable_hash(
                {"candidate": "finding-focus"}
            ),
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

    assert captured_repair_request["local_validation_errors"] == [
        "findings[0] has invalid repair_scope",
        "findings[0] missing evidence_refs",
    ]
    assert "subsystem_repair_context" not in captured_repair_request
    assert json.loads(
        captured_repair_request["previous_candidate"]
    )["findings"][0] == invalid_payload["findings"][0]
    assert captured_repair_request["original_request"] == (
        backend.requests[0].user_prompt
    )
    assert packet["findings"][0]["repair_scope"] == "metric_contract"
    assert packet["findings"][0]["evidence_refs"] == [
        "requirement:generic_gate"
    ]
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
    assert "Snapshot existence alone is not semantic support" in (
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


def test_metric_reviewer_runtime_owns_prior_snapshot_identity_transport() -> None:
    finding_id = "metric-finding:runtime-bound-snapshot"
    evidence_ref = "requirement:generic_gate.operator"
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
                    "summary": "The candidate operator remains inconsistent.",
                    "required_change": "Repair the candidate-owned operator.",
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
            "rationale": "The current candidate still has this semantic defect.",
            "evidence_refs": [],
        }
    ]
    payload["findings"] = []

    packet, backend, _ = _review(
        accept=False,
        payload=payload,
        material=material,
    )

    request_schema = backend.requests[0].schema
    prior_evidence_schema = request_schema["properties"][
        "prior_finding_reviews"
    ]["items"]["properties"]["evidence_refs"]
    new_finding_schema = request_schema["properties"]["findings"][
        "items"
    ]["properties"]
    assert prior_evidence_schema["maxItems"] == 0
    assert new_finding_schema["prior_finding_id"]["enum"] == [""]
    assert new_finding_schema["new_finding_rationale"]["minLength"] == 1
    prior_review = packet["prior_finding_reviews"][0]
    assert prior_review["evidence_refs"] == [snapshot["snapshot_id"]]
    assert packet["runtime_carried_forward_prior_finding_ids"] == [finding_id]
    assert packet["findings"][0]["finding_id"] == finding_id
    assert evidence_ref in packet["findings"][0]["evidence_refs"]
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
    ]["enum"] == [""]
    assert dynamic_schema["properties"]["prior_finding_reviews"]["items"][
        "properties"
    ]["evidence_refs"]["maxItems"] == 0
    assert "maxItems: 0" in transformed_prior_schema["items"]["properties"][
        "evidence_refs"
    ]["description"]
    transformed_scope_schema = transformed["properties"]["theory_scope_checks"]
    assert transformed_scope_schema["items"]["properties"]["requirement_id"][
        "enum"
    ] == ["gate:one"]
    assert "evidence_refs" not in transformed_scope_schema["items"][
        "properties"
    ]
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
    order_schema = transformed["properties"]["claim_checks"]["items"][
        "properties"
    ]["sample_size_order_derivation"]
    assert order_schema["required"] == [
        "primitive_orders",
        "composition",
        "orders_agree",
        "unresolved_assumptions",
    ]
    assert "minItems: 2" in transformed_prior_schema["description"]
    assert ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA["properties"][
        "prior_finding_reviews"
    ].get("minItems") is None

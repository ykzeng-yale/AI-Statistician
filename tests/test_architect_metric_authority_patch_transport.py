from __future__ import annotations

import json
from copy import deepcopy

import pytest

from ai_statistician.architect_metric_authority_patch_transport import (
    ARCHITECT_METRIC_AUTHORITY_PATCH_TRANSPORT_KIND,
    build_metric_authority_semantic_patch_transport,
    metric_gate_authority_resolution_decisions,
)
from ai_statistician.architect_metric_contract_authoring import (
    _compact_metric_authoring_prompt_payload,
    _metric_authoring_repair_context,
    _metric_authoring_repair_priority_instructions,
)
from ai_statistician.generated_metric_contract import (
    generated_metric_numeric_authority_repair_matrix,
    materialize_generated_metric_gate_field_authorities,
    validate_generated_metric_requirements,
)
from ai_statistician.llm_json_repair import (
    SEMANTIC_PATCH_PROGRESS_POLICY_STRICT_RESIDUAL_SET,
    extract_json_object,
    generate_validated_json_packet,
)
from ai_statistician.model_backend import GeneratorRequest, GeneratorResponse


THEORY_ANCHOR = "theory#/theorem_cards/0/conclusion"
DESIGN_ANCHOR = "theory#/simulation_ademp_spec/dgps/0"
CATALOG = [
    {
        "anchor_id": THEORY_ANCHOR,
        "authority_kind": "theory_derived",
        "content": "The symbolic type-I error is bounded by alpha.",
        "explicit_numeric_values": [],
    },
    {
        "anchor_id": DESIGN_ANCHOR,
        "authority_kind": "evaluation_design",
        "content": "Evaluate the preregistered alpha = 0.05 design.",
        "explicit_numeric_values": [0.05],
    },
]


def test_boolean_metric_authority_repair_requests_an_exact_empty_array() -> None:
    instructions = _metric_authoring_repair_priority_instructions(
        [
            "[generated_metric_numeric_authority_missing] "
            "empirical_metric_requirements[0].gate_field_authorities must be "
            "the empty array because this metric declares no substantive "
            "numeric gate fields"
        ]
    )

    assert "replacement_json='[]'" in instructions[0]
    assert "placeholder authority row" in instructions[0]


def test_large_metric_authoring_prompt_uses_lossless_columnar_authority_context() -> None:
    catalog = [
        {
            "anchor_id": f"theory#/theorem_cards/{index}/conclusion",
            "authority_kind": "theory_derived",
            "content": f"claim-{index}: " + ("bounded semantic content " * 12),
            "explicit_numeric_values": [index / 100],
        }
        for index in range(180)
    ]
    payload = {
        "task": "Author a metric contract.",
        "question": {"id": "generic", "description": "Evaluate the method."},
        "theory_developer_protocol_material": {
            "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
            "source_theory_packet_id": "theory:generic",
            "source_theory_packet_hash": "hash:generic",
            "execution_results_available": False,
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
            "theory_semantic_material": {
                "theorem_cards": [
                    {"conclusion": row["content"]} for row in catalog
                ],
                "critic_findings": [{"finding": "Audit the finite interface."}],
            },
        },
        "acceptance_authority_catalog": catalog,
        "requirement_schema": {
            "requirement_id": "string",
            "target_subsystems": ["SimulationEngineer"],
        },
        "required_target_rows": [
            {"target_subsystems": ["SimulationEngineer"]}
        ],
        "hard_requirements": ["Preserve exact source authority."],
    }

    compacted, evidence = _compact_metric_authoring_prompt_payload(payload)

    assert evidence["applied"] is True
    assert evidence["projected_chars"] < evidence["original_chars"]
    projected_catalog = compacted["acceptance_authority_catalog"]
    assert projected_catalog["transport"] == (
        "lossless_columnar_authority_leaves_v1"
    )
    assert projected_catalog["row_count"] == len(catalog)
    assert [
        dict(zip(projected_catalog["columns"], row, strict=True))
        for row in projected_catalog["rows"]
    ] == catalog
    compact_theory = compacted["theory_developer_protocol_material"]
    assert compact_theory["source_theory_packet_id"] == "theory:generic"
    assert "theory_semantic_material" not in compact_theory
    assert compact_theory["non_authority_review_context"][
        "critic_findings"
    ] == [{"finding": "Audit the finite interface."}]
    assert compacted["requirement_schema"]["transport"] == (
        "provider_native_structured_output_schema"
    )


def _requirement(
    *,
    requirement_id: str,
    threshold: float,
    authority_kind: str,
) -> dict[str, object]:
    return materialize_generated_metric_gate_field_authorities(
        {
            "requirement_id": requirement_id,
            "target_subsystems": ["SimulationEngineer"],
            "metric_semantics": "empirical type-I error rate",
            "metric_value_kind": "numeric",
            "measurement_protocol": "average rejection over fixed replicates",
            "required_runtime_replicates": 17,
            "operator": "<=",
            "threshold": threshold,
            "lower": None,
            "upper": None,
            "tolerance": 0.0,
            "aggregation": "identity",
            "minimum_pass_count": None,
            "minimum_pass_fraction": None,
            "required": True,
            "source_anchors": [THEORY_ANCHOR],
            "acceptance_authority_kind": authority_kind,
            "acceptance_authority_rationale": (
                "Bind the symbolic theory to a pre-execution evaluation gate."
            ),
            "gate_field_authorities": [
                {
                    "field": "threshold",
                    "authority_kind": authority_kind,
                    "source_anchors": [THEORY_ANCHOR],
                    "rationale": (
                        "Bind the symbolic theory to a pre-execution evaluation gate."
                    ),
                }
            ],
            "boundary": "empirical acceptance control, not theorem evidence",
        }
    )


def _validation_errors(requirements: list[dict[str, object]]) -> list[str]:
    return validate_generated_metric_requirements(
        requirements,
        expected_runtime_replicates=17,
        require_acceptance_authority=True,
        acceptance_authority_catalog=CATALOG,
        require_gate_field_authorities=True,
    )


def test_decisions_offer_only_exact_source_bindings_or_explicit_fallbacks() -> None:
    requirements = [
        _requirement(
            requirement_id="source_bindable",
            threshold=0.05,
            authority_kind="theory_parameter_instantiation",
        ),
        _requirement(
            requirement_id="candidate_owned",
            threshold=0.0175,
            authority_kind="theory_derived",
        ),
    ]
    errors = _validation_errors(requirements)
    matrix = generated_metric_numeric_authority_repair_matrix(
        requirements,
        validation_errors=errors,
        acceptance_authority_catalog=CATALOG,
    )

    decisions = metric_gate_authority_resolution_decisions(
        matrix,
        validation_errors=errors,
    )

    by_requirement = {
        decision["requirement_id"]: decision
        for decision in decisions.values()
    }
    source_decision = by_requirement["source_bindable"]
    assert source_decision["allowed_resolutions"] == [
        "source_binding",
        "architect_preregistered_design",
        "diagnostic_only",
        "remove_requirement",
    ]
    assert source_decision["source_binding_options"]
    assert set(
        source_decision["source_binding_options"][0]["source_anchor_ids"]
    ) == {THEORY_ANCHOR, DESIGN_ANCHOR}

    candidate_decision = by_requirement["candidate_owned"]
    assert candidate_decision["allowed_resolutions"] == [
        "architect_preregistered_design",
        "diagnostic_only",
        "remove_requirement",
    ]
    assert candidate_decision["source_binding_options"] == []
    assert candidate_decision["value"] == 0.0175


def test_transport_applies_model_choices_without_selecting_semantics() -> None:
    requirements = [
        _requirement(
            requirement_id="source_bindable",
            threshold=0.05,
            authority_kind="theory_parameter_instantiation",
        ),
        _requirement(
            requirement_id="candidate_owned",
            threshold=0.0175,
            authority_kind="theory_derived",
        ),
    ]
    errors = _validation_errors(requirements)
    context = _metric_authoring_repair_context(
        invalid_packet={"empirical_metric_requirements": requirements},
        errors=errors,
        runtime_replicates=17,
        acceptance_authority_catalog_id="catalog:test",
        acceptance_authority_catalog=CATALOG,
        required_target_rows=[],
        independent_semantic_review_repair={},
    )
    base_payload = {"empirical_metric_requirements": deepcopy(requirements)}
    fingerprint = "base:fingerprint"
    transport = build_metric_authority_semantic_patch_transport(
        base_payload=base_payload,
        base_payload_fingerprint=fingerprint,
        repair_context=context,
        max_updates=8,
    )
    assert transport is not None
    assert build_metric_authority_semantic_patch_transport(
        base_payload=base_payload,
        base_payload_fingerprint=fingerprint,
        repair_context=context,
        max_updates=0,
    ) is None

    selections: dict[str, dict[str, str]] = {}
    for decision_id, decision in context[
        "gate_field_resolution_decisions_by_id"
    ].items():
        bindings = decision["source_binding_options"]
        if bindings:
            selections[decision_id] = {
                "resolution": "source_binding",
                "source_binding_id": bindings[0]["binding_id"],
                "rationale": "Use the exact theory and design anchors supplied.",
            }
        else:
            selections[decision_id] = {
                "resolution": "architect_preregistered_design",
                "source_binding_id": "",
                "rationale": (
                    "Preregister this finite empirical threshold before execution."
                ),
            }

    patched, patched_paths, application_rows = transport.apply_envelope(
        {
            "base_payload_fingerprint": fingerprint,
            "decisions": selections,
        }
    )
    patched_requirements = [
        materialize_generated_metric_gate_field_authorities(row)
        for row in patched["empirical_metric_requirements"]
    ]

    assert _validation_errors(patched_requirements) == []
    assert [row["threshold"] for row in patched_requirements] == [0.05, 0.0175]
    assert patched_requirements[1]["acceptance_authority_rationale"] == (
        "Preregister this finite empirical threshold before execution."
    )
    assert patched_paths
    assert application_rows
    assert all(
        row["runtime_selected_semantics"] is False
        for row in application_rows
    )
    assert {
        row["model_selected_resolution"] for row in application_rows
    } == {"source_binding", "architect_preregistered_design"}
    source_application = next(
        row
        for row in application_rows
        if row["model_selected_resolution"] == "source_binding"
    )
    assert source_application["model_selected_source_authority_kind"] == (
        "theory_parameter_instantiation"
    )
    assert set(source_application["model_selected_source_anchor_ids"]) == {
        THEORY_ANCHOR,
        DESIGN_ANCHOR,
    }


def test_exact_key_transport_atomically_inserts_missing_field_binding() -> None:
    requirement = _requirement(
        requirement_id="multi_field_candidate_gate",
        threshold=0.99,
        authority_kind="evaluation_mandated",
    )
    requirement["tolerance"] = 0.01
    requirement["gate_field_authorities"] = [
        dict(requirement["gate_field_authorities"][0])
    ]
    errors = _validation_errors([requirement])
    assert any("threshold=0.99" in error for error in errors)
    assert any("exactly once in order" in error for error in errors)

    context = _metric_authoring_repair_context(
        invalid_packet={"empirical_metric_requirements": [requirement]},
        errors=errors,
        runtime_replicates=17,
        acceptance_authority_catalog_id="catalog:test",
        acceptance_authority_catalog=CATALOG,
        required_target_rows=[],
        independent_semantic_review_repair={},
    )
    decisions = context["gate_field_resolution_decisions_by_id"]
    assert {decision["field"] for decision in decisions.values()} == {
        "threshold",
        "tolerance",
    }
    missing_decision = next(
        decision
        for decision in decisions.values()
        if decision["field"] == "tolerance"
    )
    assert missing_decision["gate_field_authority_row_exists"] is False
    assert missing_decision["gate_field_authority_expected_index"] == 1

    fingerprint = "base:fingerprint"
    transport = build_metric_authority_semantic_patch_transport(
        base_payload={"empirical_metric_requirements": [requirement]},
        base_payload_fingerprint=fingerprint,
        repair_context=context,
        max_updates=8,
    )
    assert transport is not None
    patched, _paths, applications = transport.apply_envelope(
        {
            "base_payload_fingerprint": fingerprint,
            "decisions": {
                decision_id: {
                    "resolution": "architect_preregistered_design",
                    "source_binding_id": "",
                    "rationale": "Preregister this finite gate before execution.",
                }
                for decision_id in decisions
            },
        }
    )
    patched_requirement = materialize_generated_metric_gate_field_authorities(
        patched["empirical_metric_requirements"][0]
    )

    assert _validation_errors([patched_requirement]) == []
    assert patched_requirement["threshold"] == 0.99
    assert patched_requirement["tolerance"] == 0.01
    assert [
        row["field"] for row in patched_requirement["gate_field_authorities"]
    ] == ["threshold", "tolerance"]
    assert sum(
        row["runtime_created_missing_authority_row"] is True
        for row in applications
    ) == 1
    assert all(row["runtime_selected_semantics"] is False for row in applications)


def test_new_gate_shape_residual_hands_off_to_exact_key_transport() -> None:
    initial_requirement = materialize_generated_metric_gate_field_authorities(
        {
            "requirement_id": "aggregate_predicate_rate",
            "target_subsystems": ["SimulationEngineer"],
            "metric_semantics": "share of replicates satisfying a predicate",
            "metric_value_kind": "boolean",
            "measurement_protocol": (
                "Record one predicate per replicate and report their mean."
            ),
            "required_runtime_replicates": 17,
            "operator": "==",
            "threshold": 1,
            "lower": None,
            "upper": None,
            "tolerance": 0,
            "aggregation": "mean",
            "minimum_pass_count": None,
            "minimum_pass_fraction": None,
            "required": True,
            "source_anchors": [DESIGN_ANCHOR],
            "acceptance_authority_kind": (
                "architect_preregistered_design"
            ),
            "acceptance_authority_rationale": (
                "Preregister the aggregate predicate rate before execution."
            ),
            "gate_field_authorities": [],
            "boundary": "Empirical acceptance control, not theorem evidence.",
        }
    )

    class DependencyClosureBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = {
                    "empirical_metric_requirements": [initial_requirement]
                }
            elif request.metadata[
                "json_repair_semantic_patch_transport_kind"
            ] == "generic_path_patch":
                prompt = json.loads(request.user_prompt.split("\n\n", 1)[1])
                payload = {
                    "base_payload_fingerprint": prompt[
                        "base_payload_fingerprint"
                    ],
                    "updates": [
                        {
                            "path": [
                                "empirical_metric_requirements",
                                0,
                                "metric_value_kind",
                            ],
                            "replacement": "numeric",
                        },
                        {
                            "path": [
                                "empirical_metric_requirements",
                                0,
                                "gate_field_authorities",
                            ],
                            "replacement_json": json.dumps(
                                [
                                    {
                                        "field_name": "predicate_rate",
                                        "authority_kind": "diagnostic_only",
                                        "rationale": (
                                            "Record a diagnostic description."
                                        ),
                                    }
                                ]
                            ),
                        },
                    ],
                }
            else:
                prompt = json.loads(request.user_prompt)
                payload = {
                    "base_payload_fingerprint": prompt[
                        "base_payload_fingerprint"
                    ],
                    "decisions": {
                        decision_id: {
                            "resolution": "architect_preregistered_design",
                            "source_binding_id": "",
                            "rationale": (
                                "Preregister this aggregate threshold before "
                                "execution."
                            ),
                        }
                        for decision_id in prompt[
                            "gate_field_resolution_decisions_by_id"
                        ]
                    },
                }
            return GeneratorResponse(
                text=json.dumps(payload),
                provider=self.provider_name,
                model=request.model,
            )

    backend = DependencyClosureBackend()

    def build_packet(payload, _response, _raw_text):
        return {
            "empirical_metric_requirements": [
                materialize_generated_metric_gate_field_authorities(row)
                for row in payload.get("empirical_metric_requirements", [])
            ]
        }

    packet = generate_validated_json_packet(
        provider=backend,
        request=GeneratorRequest(
            system_prompt="Return JSON.",
            user_prompt="Author one metric requirement.",
            model="claude-haiku-4-5-20251001",
            max_tokens=5000,
            schema={"type": "object"},
        ),
        extract_payload=lambda text: extract_json_object(
            text,
            label="metric requirements",
        ),
        build_packet=build_packet,
        validate_packet=lambda candidate: _validation_errors(
            candidate["empirical_metric_requirements"]
        ),
        validation_label="metric requirements",
        max_repair_attempts=1,
        repair_context_builder=lambda **kwargs: _metric_authoring_repair_context(
            invalid_packet=kwargs.get("invalid_packet"),
            errors=kwargs.get("errors", []),
            runtime_replicates=17,
            acceptance_authority_catalog_id="catalog:test",
            acceptance_authority_catalog=CATALOG,
            required_target_rows=[],
            independent_semantic_review_repair={},
        ),
        semantic_patch_repair=True,
        semantic_patch_transport_builder=(
            build_metric_authority_semantic_patch_transport
        ),
        allow_progress_repair_extension=True,
        progress_repair_policy=(
            SEMANTIC_PATCH_PROGRESS_POLICY_STRICT_RESIDUAL_SET
        ),
    )

    assert len(backend.requests) == 3
    assert backend.requests[2].metadata[
        "json_repair_semantic_patch_transport_kind"
    ] == ARCHITECT_METRIC_AUTHORITY_PATCH_TRANSPORT_KIND
    requirements = packet["empirical_metric_requirements"]
    assert requirements[0]["metric_value_kind"] == "numeric"
    assert requirements[0]["threshold"] == 1
    assert [
        row["field"] for row in requirements[0]["gate_field_authorities"]
    ] == ["threshold"]
    history = packet["llm_json_repair_history"]
    assert history[1]["progress_transition"] == (
        "subsystem_semantic_patch_transport:"
        + ARCHITECT_METRIC_AUTHORITY_PATCH_TRANSPORT_KIND
    )
    assert history[2]["semantic_patch_transport_kind"] == (
        ARCHITECT_METRIC_AUTHORITY_PATCH_TRANSPORT_KIND
    )
    assert history[2]["semantic_patch_application_rows"][0][
        "runtime_selected_semantics"
    ] is False
    application = history[2]["semantic_patch_application_rows"][0]
    assert application[
        "runtime_canonicalized_gate_field_authorities"
    ] is True
    assert application[
        "runtime_removed_noncanonical_authority_rows"
    ] == 1
    assert application["runtime_canonical_gate_field_order"] == [
        "threshold"
    ]
    assert application["runtime_structural_normalization_only"] is True


def test_exact_key_transport_rejects_unlisted_or_partial_choices() -> None:
    requirement = _requirement(
        requirement_id="candidate_owned",
        threshold=0.0175,
        authority_kind="theory_derived",
    )
    errors = _validation_errors([requirement])
    context = _metric_authoring_repair_context(
        invalid_packet={"empirical_metric_requirements": [requirement]},
        errors=errors,
        runtime_replicates=17,
        acceptance_authority_catalog_id="catalog:test",
        acceptance_authority_catalog=CATALOG,
        required_target_rows=[],
        independent_semantic_review_repair={},
    )
    transport = build_metric_authority_semantic_patch_transport(
        base_payload={"empirical_metric_requirements": [requirement]},
        base_payload_fingerprint="base:fingerprint",
        repair_context=context,
        max_updates=8,
    )
    assert transport is not None
    decision_id = next(
        iter(context["gate_field_resolution_decisions_by_id"])
    )

    with pytest.raises(ValueError, match="keys must exactly match"):
        transport.apply_envelope(
            {
                "base_payload_fingerprint": "base:fingerprint",
                "decisions": {},
            }
        )
    with pytest.raises(ValueError, match="resolution must be one of"):
        transport.apply_envelope(
            {
                "base_payload_fingerprint": "base:fingerprint",
                "decisions": {
                    decision_id: {
                        "resolution": "theory_derived",
                        "source_binding_id": "",
                        "rationale": "Move the label without source support.",
                    }
                },
            }
        )


def test_recorded_failure_shape_closes_in_one_exact_key_repair() -> None:
    initial_requirements = [
        _requirement(
            requirement_id="type_I_error_control_null_dgp",
            threshold=0.05,
            authority_kind="theory_parameter_instantiation",
        ),
        _requirement(
            requirement_id="candidate_owned_power_gate",
            threshold=0.8,
            authority_kind="theory_parameter_instantiation",
        ),
    ]
    initial_requirements[1]["tolerance"] = 0.01
    initial_requirements[1]["gate_field_authorities"] = [
        dict(initial_requirements[1]["gate_field_authorities"][0])
    ]

    class ExactDecisionBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests: list[GeneratorRequest] = []

        def generate(self, request: GeneratorRequest) -> GeneratorResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = {
                    "empirical_metric_requirements": initial_requirements
                }
            else:
                prompt = json.loads(request.user_prompt)
                selections = {}
                for decision_id, decision in prompt[
                    "gate_field_resolution_decisions_by_id"
                ].items():
                    bindings = decision["source_binding_options"]
                    selections[decision_id] = (
                        {
                            "resolution": "source_binding",
                            "source_binding_id": bindings[0]["binding_id"],
                            "rationale": "Use the listed exact source binding.",
                        }
                        if bindings
                        else {
                            "resolution": "architect_preregistered_design",
                            "source_binding_id": "",
                            "rationale": (
                                "Preregister this empirical gate before execution."
                            ),
                        }
                    )
                payload = {
                    "base_payload_fingerprint": prompt[
                        "base_payload_fingerprint"
                    ],
                    "decisions": selections,
                }
            return GeneratorResponse(
                text=json.dumps(payload),
                provider="anthropic",
                model=request.model,
            )

    backend = ExactDecisionBackend()

    def build_packet(payload, _response, _raw_text):
        return {
            "empirical_metric_requirements": [
                materialize_generated_metric_gate_field_authorities(row)
                for row in payload.get("empirical_metric_requirements", [])
            ]
        }

    packet = generate_validated_json_packet(
        provider=backend,
        request=GeneratorRequest(
            system_prompt="Return JSON.",
            user_prompt="Author the metric requirements.",
            model="claude-haiku-4-5-20251001",
            max_tokens=5000,
            schema={"type": "object"},
        ),
        extract_payload=lambda text: extract_json_object(
            text,
            label="metric requirements",
        ),
        build_packet=build_packet,
        validate_packet=lambda candidate: _validation_errors(
            candidate["empirical_metric_requirements"]
        ),
        validation_label="metric requirements",
        max_repair_attempts=1,
        repair_context_builder=lambda **kwargs: _metric_authoring_repair_context(
            invalid_packet=kwargs.get("invalid_packet"),
            errors=kwargs.get("errors", []),
            runtime_replicates=17,
            acceptance_authority_catalog_id="catalog:test",
            acceptance_authority_catalog=CATALOG,
            required_target_rows=[],
            independent_semantic_review_repair={},
        ),
        semantic_patch_repair=True,
        semantic_patch_transport_builder=(
            build_metric_authority_semantic_patch_transport
        ),
        allow_progress_repair_extension=True,
    )

    assert len(backend.requests) == 2
    repair_request = backend.requests[1]
    assert repair_request.metadata[
        "json_repair_semantic_patch_transport_kind"
    ] == ARCHITECT_METRIC_AUTHORITY_PATCH_TRANSPORT_KIND
    assert repair_request.schema["properties"]["decisions"]["required"]
    assert [
        row["threshold"]
        for row in packet["empirical_metric_requirements"]
    ] == [0.05, 0.8]
    assert [
        row["tolerance"]
        for row in packet["empirical_metric_requirements"]
    ] == [0.0, 0.01]
    repair_history = packet["llm_json_repair_history"][1]
    assert repair_history["semantic_patch_transport_kind"] == (
        ARCHITECT_METRIC_AUTHORITY_PATCH_TRANSPORT_KIND
    )
    assert repair_history["patch_path_normalizations"] == []
    assert len(repair_history["semantic_patch_application_rows"]) == 3
    assert sum(
        row["runtime_created_missing_authority_row"] is True
        for row in repair_history["semantic_patch_application_rows"]
    ) == 1
    assert all(
        row["runtime_selected_semantics"] is False
        for row in repair_history["semantic_patch_application_rows"]
    )

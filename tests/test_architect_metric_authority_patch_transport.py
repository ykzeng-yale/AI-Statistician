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
    _metric_authoring_repair_context,
)
from ai_statistician.generated_metric_contract import (
    generated_metric_numeric_authority_repair_matrix,
    materialize_generated_metric_gate_field_authorities,
    validate_generated_metric_requirements,
)
from ai_statistician.llm_json_repair import (
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
    repair_history = packet["llm_json_repair_history"][1]
    assert repair_history["semantic_patch_transport_kind"] == (
        ARCHITECT_METRIC_AUTHORITY_PATCH_TRANSPORT_KIND
    )
    assert repair_history["patch_path_normalizations"] == []
    assert len(repair_history["semantic_patch_application_rows"]) == 2
    assert all(
        row["runtime_selected_semantics"] is False
        for row in repair_history["semantic_patch_application_rows"]
    )

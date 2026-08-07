from __future__ import annotations

import pytest

from ai_statistician.generated_metric_contract import (
    GENERATED_METRIC_CONTRACT_AGGREGATIONS,
    GENERATED_METRIC_CONTRACT_BOUNDARY,
    GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
    GENERATED_METRIC_CONTRACT_OPERATORS,
    GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE,
    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS,
    GENERATED_METRIC_VALUE_KINDS,
    bind_generated_metric_contract_authority,
    evaluate_generated_metric_contracts,
    generated_metric_authority_context,
    generated_metric_contract_binding_json_schema,
    generated_metric_contract_set_id,
    generated_metric_contracts_for_artifact,
    generated_metric_evaluation_semantics_contract,
    generated_metric_evaluator_certificate,
    generated_metric_acceptance_authority_catalog,
    generated_metric_acceptance_authority_prompt_catalog,
    generated_metric_requirement_json_schema,
    generated_metric_requirement_prompt_schema,
    generated_metric_requirement_set_id,
    generated_metric_requirement_target_namespace_contract,
    is_generated_metric_numeric_authority_error,
    materialize_generated_metric_contract_bindings,
    materialize_generated_metric_gate_field_authorities,
    validate_generated_metric_requirements,
    validate_generated_metric_contracts,
)


def _contract(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "contract_id": "criterion-upper-bound",
        "artifact_id": "artifact:generated-candidate",
        "metric_path": ["stress_cases", "*", "criterion_value"],
        "operator": "<=",
        "threshold": 0.1,
        "tolerance": 0.01,
        "aggregation": "max",
        "required": True,
        "source_anchors": ["architect:acceptance:criterion"],
        "acceptance_authority_kind": "theory_derived",
        "acceptance_authority_rationale": (
            "The cited theory node supplies the comparison boundary."
        ),
    }
    row.update(overrides)
    return row


def _requirement(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "requirement_id": "architect:criterion-control",
        "target_subsystems": ["SimulationEngineer"],
        "metric_semantics": "scenario-wise excess above the declared target",
        "measurement_protocol": (
            "compute one excess value for each preregistered stress scenario"
        ),
        "required_runtime_replicates": 80,
        "operator": "<=",
        "threshold": 0.02,
        "tolerance": 0.0,
        "aggregation": "at_least_count",
        "minimum_pass_count": 11,
        "required": True,
        "source_anchors": ["architect:acceptance:criterion-control"],
        "acceptance_authority_kind": "theory_derived",
        "acceptance_authority_rationale": (
            "The cited theory node supplies the comparison boundary."
        ),
    }
    row.update(overrides)
    return row


def test_metric_requirement_target_namespace_is_explicit_and_machine_readable() -> None:
    namespace = generated_metric_requirement_target_namespace_contract()
    schema = generated_metric_requirement_json_schema()

    assert namespace["allowed_exact_values"] == list(
        GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
    )
    assert namespace["runtime_execution_owner_by_author_subsystem"] == {
        "SimulationEngineer": "SimulationEvaluator",
    }
    assert namespace["capability_eval_required_coverage"] == [
        {"target_subsystems": ["SimulationEngineer"]},
    ]
    assert schema["properties"]["target_subsystems"]["items"]["enum"] == [
        "SimulationEngineer",
    ]
    assert "semantic review" in namespace["algorithm_acceptance_boundary"]
    assert schema["properties"]["operator"]["enum"] == list(
        GENERATED_METRIC_CONTRACT_OPERATORS
    )
    assert schema["properties"]["aggregation"]["enum"] == list(
        GENERATED_METRIC_CONTRACT_AGGREGATIONS
    )
    assert schema["properties"]["metric_value_kind"]["enum"] == list(
        GENERATED_METRIC_VALUE_KINDS
    )
    assert {
        "requirement_id",
        "metric_semantics",
        "metric_value_kind",
        "measurement_protocol",
        "required_runtime_replicates",
        "operator",
        "tolerance",
        "aggregation",
        "required",
        "source_anchors",
    } <= set(schema["required"])
    assert schema["properties"]["required_runtime_replicates"]["minimum"] == 1
    assert schema["properties"]["minimum_pass_fraction"]["anyOf"] == [
        {"type": "number"},
        {"type": "null"},
    ]
    assert {
        "threshold",
        "lower",
        "upper",
        "minimum_pass_count",
        "minimum_pass_fraction",
        "boundary",
    } <= set(schema["required"])
    assert generated_metric_requirement_prompt_schema(
        target_subsystem="SimulationEngineer"
    )["target_subsystems"] == ["SimulationEngineer"]
    assert "|" not in generated_metric_requirement_prompt_schema()[
        "target_subsystems"
    ][0]


def test_typed_boolean_metric_uses_runtime_truth_representation() -> None:
    catalog = generated_metric_acceptance_authority_catalog(
        question={
            "title": "Generic adapted-process check",
            "description": "Require a non-anticipating stopping rule.",
        },
        runtime_contract={"simulation_targets": []},
        theory_protocol_material={
            "theory_semantic_material": {
                "theorem_cards": [
                    {
                        "informal_statement": (
                            "The stopping decision is measurable with respect to "
                            "the current filtration."
                        )
                    }
                ]
            }
        },
    )
    anchor = "theory#/theorem_cards/0/informal_statement"
    requirement = _requirement(
        requirement_id="architect:adapted-process",
        metric_semantics="whether the implemented stopping rule is non-anticipating",
        metric_value_kind="boolean",
        measurement_protocol=(
            "return a boolean after checking that every stopping decision uses "
            "only the current filtration"
        ),
        operator="==",
        threshold=1,
        tolerance=0,
        aggregation="identity",
        minimum_pass_count=None,
        source_anchors=[anchor],
        acceptance_authority_kind="theory_derived",
    )

    assert validate_generated_metric_requirements(
        [requirement],
        required_target_subsystems=("SimulationEngineer",),
        expected_runtime_replicates=80,
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    ) == []

    contracts = materialize_generated_metric_contract_bindings(
        [
            {
                "contract_id": "adapted-process-contract",
                "requirement_id": "architect:adapted-process",
                "artifact_id": "artifact:boolean",
                "metric_path": ["is_non_anticipating"],
            }
        ],
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
    )

    passed = evaluate_generated_metric_contracts(
        {"is_non_anticipating": True},
        contracts=contracts,
        artifact_id="artifact:boolean",
        runtime_replicates=80,
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
        require_authoritative_requirements=True,
    )
    failed = evaluate_generated_metric_contracts(
        {"is_non_anticipating": False},
        contracts=contracts,
        artifact_id="artifact:boolean",
        runtime_replicates=80,
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
        require_authoritative_requirements=True,
    )

    assert passed["all_required_passed"] is True
    assert failed["all_required_passed"] is False

    numeric_errors = validate_generated_metric_requirements(
        [{**requirement, "metric_value_kind": "numeric"}],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    )
    assert any(
        "threshold=1" in error
        and "explicitly present in a cited theory_derived authority node" in error
        for error in numeric_errors
    )


def test_boolean_truth_encoding_drops_redundant_field_authorities() -> None:
    requirement = materialize_generated_metric_gate_field_authorities(
        _requirement(
            requirement_id="architect:boolean-predicate",
            metric_semantics="whether a generic invariant holds",
            metric_value_kind="boolean",
            measurement_protocol="return one boolean invariant check",
            operator="==",
            threshold=1,
            tolerance=0,
            aggregation="identity",
            minimum_pass_count=None,
            gate_field_authorities=[
                {
                    "field": field,
                    "authority_kind": "theory_derived",
                    "source_anchors": [
                        "architect:acceptance:criterion-control"
                    ],
                    "rationale": "Redundant runtime truth representation.",
                }
                for field in ("threshold", "operator", "tolerance")
            ],
        )
    )

    assert requirement["gate_field_authorities"] == []


def test_boolean_truth_authority_error_requests_empty_array_not_placeholder() -> None:
    requirement = materialize_generated_metric_gate_field_authorities(
        _requirement(
            requirement_id="architect:boolean-predicate",
            metric_semantics="whether a generic invariant holds",
            metric_value_kind="boolean",
            measurement_protocol="return one boolean invariant check",
            operator="==",
            threshold=1,
            tolerance=0,
            aggregation="identity",
            minimum_pass_count=None,
            source_anchors=["question#/description"],
            acceptance_authority_kind="evaluation_mandated",
            gate_field_authorities=[],
        )
    )
    requirement["gate_field_authorities"] = [
        {
            "authority_kind": "evaluation_mandated",
            "source_anchors": ["question#/description"],
            "rationale": "Invalid placeholder row.",
        }
    ]

    errors = validate_generated_metric_requirements(
        [requirement],
        require_acceptance_authority=True,
        acceptance_authority_catalog=[
            {
                "anchor_id": "question#/description",
                "authority_kind": "evaluation_mandated",
                "content": "Require the generic invariant.",
                "explicit_numeric_values": [],
            }
        ],
        require_gate_field_authorities=True,
    )

    assert any(
        "gate_field_authorities must be the empty array []" in error
        and "must not contain placeholder rows" in error
        for error in errors
    )


def test_metric_acceptance_authority_catalog_exposes_exact_current_artifact_leaves() -> None:
    catalog = generated_metric_acceptance_authority_catalog(
        question={
            "title": "Generic evaluation",
            "description": "Require empirical error at most 0.1.",
        },
        runtime_contract={"simulation_targets": ["measure finite-sample error"]},
        theory_protocol_material={
            "theory_semantic_material": {
                "theory_derivation_packet": {
                    "equation_chain": [
                        {"step_id": "E1", "rhs": "error <= 0.1"}
                    ]
                },
                "simulation_ademp_spec": {
                    "methods": ["Instantiate alpha = 0.05."],
                    "expected_theoretical_behavior": (
                        "Power should exceed 0.8 when possible."
                    ),
                },
                "model": "must-not-be-an-authority-anchor",
            }
        },
    )
    by_id = {row["anchor_id"]: row for row in catalog}

    assert by_id[
        "theory#/theory_derivation_packet/equation_chain/0/rhs"
    ] == {
        "anchor_id": "theory#/theory_derivation_packet/equation_chain/0/rhs",
        "authority_kind": "theory_derived",
        "content": "error <= 0.1",
        "explicit_numeric_values": [0.1],
    }
    assert by_id["question#/description"]["authority_kind"] == (
        "evaluation_mandated"
    )
    assert by_id["runtime_contract#/simulation_targets/0"]["content"] == (
        "measure finite-sample error"
    )
    assert by_id["runtime_contract#/simulation_targets/0"][
        "authority_kind"
    ] == "diagnostic_only"
    assert by_id["theory#/simulation_ademp_spec/methods/0"] == {
        "anchor_id": "theory#/simulation_ademp_spec/methods/0",
        "authority_kind": "evaluation_design",
        "content": "Instantiate alpha = 0.05.",
        "explicit_numeric_values": [0.05],
    }
    assert by_id[
        "theory#/simulation_ademp_spec/expected_theoretical_behavior"
    ]["authority_kind"] == "diagnostic_only"
    assert not any("model" in anchor_id for anchor_id in by_id)


def test_metric_authority_prompt_catalog_uses_complete_semantic_records() -> None:
    catalog = generated_metric_acceptance_authority_catalog(
        question={"title": "Generic", "description": "Evaluate error."},
        runtime_contract={"simulation_targets": []},
        theory_protocol_material={
            "theory_semantic_material": {
                "theorem_cards": [
                    {
                        "id": "theorem_error_control",
                        "conclusion": "error <= 0.05",
                        "assumptions_used": ["regularity"],
                    }
                ],
                "simulation_ademp_spec": {
                    "methods": ["Instantiate alpha = 0.05."]
                },
            }
        },
    )

    projected = generated_metric_acceptance_authority_prompt_catalog(catalog)
    by_id = {row["anchor_id"]: row for row in projected}

    assert "theory#/theorem_cards/0" in by_id
    assert "theory#/theorem_cards/0/conclusion" not in by_id
    assert by_id["theory#/theorem_cards/0"]["content"]["conclusion"] == (
        "error <= 0.05"
    )
    assert by_id["theory#/theorem_cards/0"]["explicit_numeric_values"] == [
        0.05
    ]
    assert "theory#/simulation_ademp_spec/methods/0" in by_id


def test_strict_metric_gate_authority_rejects_free_form_and_diagnostic_gates() -> None:
    catalog = generated_metric_acceptance_authority_catalog(
        question={"title": "Generic", "description": "Evaluate error."},
        runtime_contract={"simulation_targets": []},
        theory_protocol_material={
            "theory_semantic_material": {
                "theory_derivation_packet": {
                    "equation_chain": [
                        {"rhs": "error <= 0.02 in at least 11 cases"}
                    ]
                }
            }
        },
    )
    exact_anchor = "theory#/theory_derivation_packet/equation_chain/0/rhs"
    accepted = _requirement(
        source_anchors=[exact_anchor],
        acceptance_authority_kind="theory_derived",
    )
    free_form = _requirement(
        source_anchors=["theory packet says error is small"],
        acceptance_authority_kind="theory_derived",
    )
    diagnostic_gate = _requirement(
        source_anchors=[exact_anchor],
        acceptance_authority_kind="diagnostic_only",
        required=True,
    )

    assert validate_generated_metric_requirements(
        [accepted],
        required_target_subsystems=("SimulationEngineer",),
        expected_runtime_replicates=80,
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    ) == []
    free_form_errors = validate_generated_metric_requirements(
        [free_form],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    )
    diagnostic_errors = validate_generated_metric_requirements(
        [diagnostic_gate],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    )

    assert any("unknown" in error for error in free_form_errors)
    assert any("exact theory_derived authority node" in error for error in free_form_errors)
    assert any("diagnostic_only rows must set required=false" in error for error in diagnostic_errors)
    assert any("required acceptance gates" in error for error in diagnostic_errors)


def test_strict_metric_gate_authority_rejects_numeric_cutoff_laundering() -> None:
    catalog = generated_metric_acceptance_authority_catalog(
        question={"title": "Generic", "description": "Evaluate empirical error."},
        runtime_contract={
            "simulation_targets": ["Report error below 0.05 when possible."]
        },
        theory_protocol_material={
            "theory_semantic_material": {
                "theorem_cards": [
                    {"conclusion": "The error converges to zero asymptotically."}
                ],
                "simulation_ademp_spec": {
                    "expected_behavior": "Finite-sample error should be below 0.02."
                },
            }
        },
    )
    theorem_anchor = "theory#/theorem_cards/0/conclusion"
    simulation_anchor = "theory#/simulation_ademp_spec/expected_behavior"

    no_numeric_derivation_errors = validate_generated_metric_requirements(
        [
            _requirement(
                aggregation="mean",
                minimum_pass_count=None,
                threshold=0.02,
                source_anchors=[theorem_anchor],
            )
        ],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    )
    diagnostic_laundering_errors = validate_generated_metric_requirements(
        [
            _requirement(
                aggregation="mean",
                minimum_pass_count=None,
                threshold=0.02,
                source_anchors=[simulation_anchor],
            )
        ],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    )

    assert any(
        ".threshold=0.02 must be explicitly present" in error
        for error in no_numeric_derivation_errors
    )
    assert any(
        is_generated_metric_numeric_authority_error(error)
        for error in no_numeric_derivation_errors
    )
    assert any(
        "exact theory_derived authority node" in error
        for error in diagnostic_laundering_errors
    )


def test_strict_metric_gate_authority_accepts_explicit_percent_value() -> None:
    catalog = generated_metric_acceptance_authority_catalog(
        question={
            "title": "Generic",
            "description": "Require empirical coverage of at least 95%.",
        },
        runtime_contract={"simulation_targets": []},
        theory_protocol_material={"theory_semantic_material": {}},
    )
    errors = validate_generated_metric_requirements(
        [
            _requirement(
                aggregation="mean",
                minimum_pass_count=None,
                operator=">=",
                threshold=0.95,
                source_anchors=["question#/description"],
                acceptance_authority_kind="evaluation_mandated",
            )
        ],
        required_target_subsystems=("SimulationEngineer",),
        expected_runtime_replicates=80,
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    )

    assert errors == []


def test_strict_metric_gate_authority_accepts_theory_parameter_instantiation() -> None:
    catalog = generated_metric_acceptance_authority_catalog(
        question={"title": "Generic", "description": "Evaluate error."},
        runtime_contract={"simulation_targets": []},
        theory_protocol_material={
            "theory_semantic_material": {
                "theorem_cards": [
                    {"conclusion": "Finite-sample error is at most alpha."}
                ],
                "simulation_ademp_spec": {
                    "methods": ["Run the theorem-backed procedure at alpha = 0.05."],
                    "expected_theoretical_behavior": (
                        "Power should be at least 0.8."
                    ),
                },
            }
        },
    )
    theorem_anchor = "theory#/theorem_cards/0/conclusion"
    design_anchor = "theory#/simulation_ademp_spec/methods/0"
    requirement = _requirement(
        aggregation="mean",
        minimum_pass_count=None,
        threshold=0.05,
        source_anchors=[theorem_anchor, design_anchor],
        acceptance_authority_kind="theory_parameter_instantiation",
        acceptance_authority_rationale=(
            "The theorem bounds error by alpha and the design fixes alpha=0.05."
        ),
    )

    assert validate_generated_metric_requirements(
        [requirement],
        required_target_subsystems=("SimulationEngineer",),
        expected_runtime_replicates=80,
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    ) == []

    missing_theory_errors = validate_generated_metric_requirements(
        [{**requirement, "source_anchors": [design_anchor]}],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    )
    unstated_design_value_errors = validate_generated_metric_requirements(
        [{**requirement, "threshold": 0.1}],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    )

    assert any(
        "exact theory_derived authority node" in error
        for error in missing_theory_errors
    )
    assert any(
        ".threshold=0.1 must be explicitly present" in error
        for error in unstated_design_value_errors
    )


def test_strict_metric_gate_authority_accepts_preregistered_architect_design() -> None:
    catalog = generated_metric_acceptance_authority_catalog(
        question={
            "title": "Generic finite-sample evaluation",
            "description": "Evaluate the procedure's empirical error and stability.",
        },
        runtime_contract={"simulation_targets": []},
        theory_protocol_material={
            "theory_semantic_material": {
                "theorem_cards": [
                    {"conclusion": "The target procedure estimates the named risk."}
                ]
            }
        },
    )
    requirement = _requirement(
        aggregation="mean",
        minimum_pass_count=None,
        threshold=0.08,
        tolerance=0.015,
        source_anchors=[
            "question#/description",
            "theory#/theorem_cards/0/conclusion",
        ],
        acceptance_authority_kind="architect_preregistered_design",
        acceptance_authority_rationale=(
            "Before execution, the Architect chooses a non-vacuous error benchmark "
            "and Monte Carlo tolerance that are feasible for 80 replicates; these "
            "numbers are empirical design choices, not theorem guarantees."
        ),
    )

    assert validate_generated_metric_requirements(
        [requirement],
        required_target_subsystems=("SimulationEngineer",),
        expected_runtime_replicates=80,
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    ) == []

    unknown_anchor_errors = validate_generated_metric_requirements(
        [{**requirement, "source_anchors": ["invented:semantic-context"]}],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
    )
    assert any("unknown" in error for error in unknown_anchor_errors)


def test_field_bound_gate_authority_preserves_mixed_numeric_provenance() -> None:
    catalog = generated_metric_acceptance_authority_catalog(
        question={
            "title": "Generic finite-sample evaluation",
            "description": "Evaluate error under a preregistered tolerance.",
        },
        runtime_contract={"simulation_targets": []},
        theory_protocol_material={
            "theory_semantic_material": {
                "theorem_cards": [
                    {
                        "conclusion": (
                            "The finite-sample error is at most 0.05."
                        )
                    }
                ]
            }
        },
    )
    theorem_anchor = "theory#/theorem_cards/0/conclusion"
    question_anchor = "question#/description"
    requirement = materialize_generated_metric_gate_field_authorities(
        _requirement(
            aggregation="mean",
            minimum_pass_count=None,
            threshold=0.05,
            tolerance=0.02,
            source_anchors=[theorem_anchor],
            acceptance_authority_kind="architect_preregistered_design",
            acceptance_authority_rationale=(
                "The theorem owns the threshold; the Architect preregisters "
                "the finite-budget comparison tolerance before execution."
            ),
            gate_field_authority_mode=(
                GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE
            ),
            gate_field_authorities=[
                {
                    "field": "threshold",
                    "authority_kind": "theory_derived",
                    "source_anchors": [theorem_anchor],
                    "rationale": (
                        "The cited theorem explicitly supplies 0.05."
                    ),
                },
                {
                    "field": "tolerance",
                    "authority_kind": (
                        "architect_preregistered_design"
                    ),
                    "source_anchors": [question_anchor],
                    "rationale": (
                        "The Architect freezes 0.02 as a finite-budget "
                        "comparison tolerance before execution."
                    ),
                },
            ],
        )
    )
    assert requirement["source_anchors"] == [
        theorem_anchor,
        question_anchor,
    ]

    assert validate_generated_metric_requirements(
        [requirement],
        required_target_subsystems=("SimulationEngineer",),
        expected_runtime_replicates=80,
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
        require_gate_field_authorities=True,
    ) == []

    laundering = {
        **requirement,
        "acceptance_authority_kind": "theory_derived",
        "gate_field_authorities": [
            requirement["gate_field_authorities"][0],
            {
                **requirement["gate_field_authorities"][1],
                "authority_kind": "theory_derived",
                "source_anchors": [theorem_anchor],
            },
        ],
    }
    laundering_errors = validate_generated_metric_requirements(
        [laundering],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
        require_gate_field_authorities=True,
    )
    assert any(
        "gate_field_authorities[1].authority_kind='theory_derived' cannot "
        "authorize tolerance=0.02" in error
        for error in laundering_errors
    )


def test_field_bound_gate_authority_requires_exact_active_field_coverage() -> None:
    requirement = materialize_generated_metric_gate_field_authorities(
        _requirement(
            aggregation="mean",
            minimum_pass_count=None,
            threshold=0.05,
            tolerance=0.02,
            acceptance_authority_kind="architect_preregistered_design",
        )
    )
    catalog = [
        {
            "anchor_id": "architect:acceptance:criterion-control",
            "authority_kind": "question_mandate",
            "content": "Generic evaluation context.",
            "explicit_numeric_values": [],
        }
    ]
    missing = {
        **requirement,
        "gate_field_authorities": requirement[
            "gate_field_authorities"
        ][:-1],
    }
    duplicate = {
        **requirement,
        "gate_field_authorities": [
            requirement["gate_field_authorities"][0],
            requirement["gate_field_authorities"][0],
        ],
    }

    for invalid in (missing, duplicate):
        errors = validate_generated_metric_requirements(
            [invalid],
            require_acceptance_authority=True,
            acceptance_authority_catalog=catalog,
            require_gate_field_authorities=True,
        )
        assert any(
            "must bind each declared substantive numeric field exactly once"
            in error
            for error in errors
        )


def test_gate_authority_shape_reports_missing_between_fields_in_same_pass() -> None:
    anchor = "architect:acceptance:criterion-control"
    requirement = _requirement(
        aggregation="mean",
        minimum_pass_count=None,
        operator="between",
        threshold=None,
        lower=None,
        upper=None,
        tolerance=0.02,
        acceptance_authority_kind="architect_preregistered_design",
        gate_field_authority_mode=(
            GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE
        ),
        gate_field_authorities=[
            {
                "field": "tolerance",
                "authority_kind": "architect_preregistered_design",
                "source_anchors": [anchor],
                "rationale": (
                    "The Architect preregisters the comparison tolerance."
                ),
            }
        ],
    )
    catalog = [
        {
            "anchor_id": anchor,
            "authority_kind": "question_mandate",
            "content": "Generic evaluation context.",
            "explicit_numeric_values": [],
        }
    ]

    errors = validate_generated_metric_requirements(
        [requirement],
        require_acceptance_authority=True,
        acceptance_authority_catalog=catalog,
        require_gate_field_authorities=True,
    )

    assert any(
        "lower must be a finite number for between" in error
        for error in errors
    )
    assert any(
        "upper must be a finite number for between" in error
        for error in errors
    )
    assert any(
        "expected=['lower', 'upper', 'tolerance'] observed=['tolerance']"
        in error
        for error in errors
    )


def test_field_bound_authority_survives_runtime_binding_and_evaluation() -> None:
    requirement = materialize_generated_metric_gate_field_authorities(
        _requirement(
            aggregation="mean",
            minimum_pass_count=None,
            acceptance_authority_kind="architect_preregistered_design",
        )
    )
    contracts = materialize_generated_metric_contract_bindings(
        [
            {
                "contract_id": "field-bound-contract",
                "requirement_id": requirement["requirement_id"],
                "artifact_id": "artifact:field-bound",
                "metric_path": ["error"],
                "gate_field_authorities": [],
            }
        ],
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
    )

    assert contracts[0]["gate_field_authorities"] == requirement[
        "gate_field_authorities"
    ]
    assert "gate_field_authorities" in contracts[0][
        "discarded_authority_override_fields"
    ]
    evaluation = evaluate_generated_metric_contracts(
        {"error": 0.01},
        contracts=contracts,
        artifact_id="artifact:field-bound",
        runtime_replicates=80,
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
        require_authoritative_requirements=True,
    )
    assert evaluation["evaluations"][0]["gate_field_authorities"] == (
        requirement["gate_field_authorities"]
    )


def test_legacy_requirement_hash_and_validation_remain_unchanged() -> None:
    legacy = _requirement(
        aggregation="mean",
        minimum_pass_count=None,
        acceptance_authority_kind="architect_preregistered_design",
    )
    legacy_set_id = generated_metric_requirement_set_id([legacy])

    materialized = materialize_generated_metric_gate_field_authorities(
        legacy
    )

    assert "gate_field_authorities" not in legacy
    assert generated_metric_requirement_set_id([legacy]) == legacy_set_id
    assert validate_generated_metric_requirements([legacy]) == []
    assert materialized["gate_field_authority_mode"] == (
        GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE
    )


def test_strict_metric_requirement_schema_enumerates_current_authority_ids() -> None:
    anchor_id = "theory#/theorem_cards/0/conclusion"
    schema = generated_metric_requirement_json_schema(
        require_acceptance_authority=True,
        authority_anchor_ids=[anchor_id],
    )

    assert {
        "acceptance_authority_kind",
        "acceptance_authority_rationale",
    } <= set(schema["required"])
    assert schema["properties"]["source_anchors"]["items"]["enum"] == [
        anchor_id
    ]
    field_schema = generated_metric_requirement_json_schema(
        require_acceptance_authority=True,
        authority_anchor_ids=[anchor_id],
        require_gate_field_authorities=True,
    )
    assert {
        "gate_field_authority_mode",
        "gate_field_authorities",
    } <= set(field_schema["required"])
    assert field_schema["properties"]["gate_field_authority_mode"][
        "enum"
    ] == [GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE]
    assert "For boolean metrics this array must be exactly []" in (
        field_schema["properties"]["gate_field_authorities"]["description"]
    )


def test_metric_evaluation_semantics_separates_comparison_from_quorum() -> None:
    semantics = generated_metric_evaluation_semantics_contract()
    schema = generated_metric_requirement_json_schema()["properties"]

    assert semantics["scalar_aggregations"]["values"] == [
        "identity",
        "mean",
        "min",
        "max",
    ]
    assert semantics["elementwise_aggregations"]["values"] == [
        "all",
        "any",
        "at_least_count",
        "at_least_fraction",
    ]
    assert "never the comparison threshold" in semantics["quorum_rule"]
    assert "authoring_example" not in semantics
    assert "never place" in schema["threshold"]["description"]
    assert "separate from threshold" in schema["minimum_pass_count"][
        "description"
    ]


def test_metric_evaluator_certificate_records_actual_dispatch_order() -> None:
    elementwise = _requirement(
        operator="==",
        threshold=1,
        aggregation="at_least_count",
        minimum_pass_count=60,
    )
    scalar = _requirement(
        requirement_id="architect:mean-control",
        aggregation="mean",
        minimum_pass_count=None,
    )

    certificate_set = generated_metric_evaluator_certificate(
        [elementwise, scalar]
    )
    by_requirement = {
        row["requirement_id"]: row
        for row in certificate_set["certificates"]
    }

    elementwise_certificate = by_requirement[
        "architect:criterion-control"
    ]
    assert elementwise_certificate["evaluator_shape_valid"] is True
    assert elementwise_certificate["evaluator_shape_errors"] == []
    assert elementwise_certificate["dispatch_class"] == "elementwise"
    assert elementwise_certificate["evaluation_order"] == (
        "compare_each_raw_value_then_aggregate_booleans"
    )
    assert elementwise_certificate["comparison_stage"] == {
        "input": "each_resolved_raw_value",
        "operator": "==",
        "threshold": 1,
        "lower": None,
        "upper": None,
        "tolerance": 0.0,
    }
    assert elementwise_certificate["aggregation_stage"]["operation"] == (
        "at_least_count"
    )
    assert elementwise_certificate["aggregation_stage"][
        "minimum_pass_count"
    ] == 60
    assert by_requirement["architect:mean-control"]["evaluation_order"] == (
        "aggregate_raw_values_then_compare_once"
    )
    assert certificate_set["alternative_runtime_interpretations_allowed"] is False
    assert certificate_set["all_rows_schema_valid"] is True
    assert certificate_set["requirement_schema_errors"] == []
    assert certificate_set["proof_evidence_status"] == (
        GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
    )


def test_metric_requirement_validator_does_not_silently_alias_runtime_owner() -> None:
    invalid = _requirement(target_subsystems=["SimulationEvaluator"])

    errors = validate_generated_metric_requirements(
        [invalid],
        required_target_subsystems=("SimulationEngineer",),
        expected_runtime_replicates=80,
    )

    assert any(
        "unsupported values: SimulationEvaluator" in error for error in errors
    )
    assert any("missing: SimulationEngineer" in error for error in errors)


def test_generated_metric_contract_validator_is_artifact_bound() -> None:
    contracts = [_contract()]

    assert validate_generated_metric_contracts(
        contracts,
        expected_artifact_ids=("artifact:generated-candidate",),
        required_artifact_ids=("artifact:generated-candidate",),
    ) == []
    assert generated_metric_contracts_for_artifact(
        contracts,
        artifact_id="artifact:generated-candidate",
    ) == contracts
    assert generated_metric_contract_set_id(contracts).startswith(
        "generated_metric_contract_set:"
    )


def test_metric_authority_repair_context_is_complete_and_subsystem_scoped() -> None:
    unsupported_algorithm_row = _requirement(
        requirement_id="unsupported-algorithm-row",
        target_subsystems=["AlgorithmEngineer"],
    )
    simulation_only = _requirement(
        requirement_id="simulation-only",
        target_subsystems=["SimulationEngineer"],
    )

    context = generated_metric_authority_context(
        [unsupported_algorithm_row, simulation_only],
        target_subsystem="SimulationEngineer",
        artifact_id_label="simulation_code_drafts[*].simulation_id",
    )

    assert [
        row["requirement_id"]
        for row in context["authoritative_empirical_metric_requirements"]
    ] == ["simulation-only"]
    binding = context["required_authority_binding_rows"][0]
    assert binding["requirement_id"] == "simulation-only"
    assert binding["aggregation"] == "at_least_count"
    assert binding["minimum_pass_count"] == 11
    assert binding["required_runtime_replicates"] == 80
    assert binding["source_anchors"] == [
        "architect:acceptance:criterion-control"
    ]
    assert context["coding_agent_may_author_only"] == [
        "contract_id",
        "requirement_id",
        "artifact_id",
        "metric_path",
    ]
    assert context["authority_materialization_mode"] == (
        "runtime_joined_frozen_requirement"
    )
    assert "never the comparison threshold" in context[
        "metric_evaluation_semantics"
    ]["quorum_rule"]
    assert "repair_prompt_priority_instructions" not in context


def test_metric_binding_schema_exposes_only_foreign_keys_and_result_path() -> None:
    schema = generated_metric_contract_binding_json_schema(
        requirement_ids=("architect:criterion-control",),
        artifact_ids=("artifact:generated-candidate",),
    )

    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "contract_id",
        "requirement_id",
        "artifact_id",
        "metric_path",
    ]
    assert set(schema["properties"]) == set(schema["required"])
    assert schema["properties"]["requirement_id"]["enum"] == [
        "architect:criterion-control"
    ]
    assert schema["properties"]["artifact_id"]["enum"] == [
        "artifact:generated-candidate"
    ]


def test_binding_only_contract_materializes_frozen_architect_authority() -> None:
    requirement = _requirement()
    contracts = materialize_generated_metric_contract_bindings(
        [
            {
                "contract_id": "criterion-excess-quorum",
                "requirement_id": "architect:criterion-control",
                "artifact_id": "artifact:generated-candidate",
                "metric_path": ["criterion_excess", "*"],
            }
        ],
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
    )

    contract = contracts[0]
    assert contract["operator"] == requirement["operator"]
    assert contract["threshold"] == requirement["threshold"]
    assert contract["aggregation"] == requirement["aggregation"]
    assert contract["minimum_pass_count"] == requirement["minimum_pass_count"]
    assert contract["source_anchors"] == requirement["source_anchors"]
    assert contract["authority_binding_mode"] == (
        "runtime_joined_frozen_requirement"
    )
    assert contract["authority_requirement_fingerprint"]
    assert validate_generated_metric_contracts(
        contracts,
        expected_artifact_ids=("artifact:generated-candidate",),
        required_artifact_ids=("artifact:generated-candidate",),
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
        require_authoritative_requirements=True,
    ) == []


def test_runtime_join_discards_attempted_coding_agent_gate_weakening() -> None:
    requirement = _requirement()
    contracts = materialize_generated_metric_contract_bindings(
        [
            {
                "contract_id": "attempted-weakened-gate",
                "requirement_id": "architect:criterion-control",
                "artifact_id": "artifact:generated-candidate",
                "metric_path": ["criterion_excess", "*"],
                "operator": "<=",
                "threshold": 999.0,
                "aggregation": "any",
                "required": False,
            }
        ],
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
    )

    contract = contracts[0]
    assert contract["threshold"] == 0.02
    assert contract["aggregation"] == "at_least_count"
    assert contract["required"] is True
    assert set(contract["discarded_authority_override_fields"]) == {
        "threshold",
        "aggregation",
        "required",
    }
    evaluation = evaluate_generated_metric_contracts(
        {"criterion_excess": [0.03] * 12},
        contracts=contracts,
        artifact_id="artifact:generated-candidate",
        runtime_replicates=80,
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
        require_authoritative_requirements=True,
    )
    assert evaluation["metric_requirement_authority_validated"] is True
    assert evaluation["all_required_passed"] is False


def test_unknown_requirement_binding_still_fails_closed() -> None:
    requirement = _requirement()
    contracts = materialize_generated_metric_contract_bindings(
        [
            {
                "contract_id": "unknown-binding",
                "requirement_id": "architect:unknown",
                "artifact_id": "artifact:generated-candidate",
                "metric_path": ["criterion_excess"],
            }
        ],
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
    )

    errors = validate_generated_metric_contracts(
        contracts,
        expected_artifact_ids=("artifact:generated-candidate",),
        required_artifact_ids=("artifact:generated-candidate",),
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
        require_authoritative_requirements=True,
    )
    assert any("not an authoritative requirement" in error for error in errors)


def test_generated_metric_contract_validator_rejects_invalid_contract_shape() -> None:
    errors = validate_generated_metric_contracts(
        [
            _contract(
                contract_id="",
                artifact_id="wrong-artifact",
                metric_path=[],
                operator="approximately",
                threshold="0.1",
                tolerance=-1,
                aggregation="median",
                required="yes",
                source_anchors=[],
            )
        ],
        expected_artifact_ids=("artifact:generated-candidate",),
        required_artifact_ids=("artifact:generated-candidate",),
    )

    assert any("contract_id" in error for error in errors)
    assert any("not a supplied task artifact" in error for error in errors)
    assert any("metric_path" in error for error in errors)
    assert any("operator" in error for error in errors)
    assert any("threshold" in error for error in errors)
    assert any("tolerance" in error for error in errors)
    assert any("aggregation" in error for error in errors)
    assert any("required must be a boolean" in error for error in errors)
    assert any("source_anchors" in error for error in errors)
    assert any("missing: artifact:generated-candidate" in error for error in errors)


def test_generated_metric_contract_evaluates_nested_wildcard_without_name_inference() -> None:
    contracts = [_contract()]

    passing = evaluate_generated_metric_contracts(
        {
            "stress_cases": {
                "baseline": {"criterion_value": 0.08},
                "stress": {"criterion_value": 0.105},
            }
        },
        contracts=contracts,
        artifact_id="artifact:generated-candidate",
    )
    failing = evaluate_generated_metric_contracts(
        {
            "stress_cases": {
                "baseline": {"criterion_value": 0.08},
                "stress": {"criterion_value": 0.12},
            }
        },
        contracts=contracts,
        artifact_id="artifact:generated-candidate",
    )

    assert passing["all_required_passed"] is True
    assert passing["n_passed"] == 1
    assert passing["evaluations"][0]["aggregate_value"] == 0.105
    assert passing["proof_evidence_status"] == (
        GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
    )
    assert passing["boundary"] == GENERATED_METRIC_CONTRACT_BOUNDARY
    assert failing["all_required_passed"] is False
    assert failing["n_failed"] == 1
    assert "criterion-upper-bound" in failing["required_failure_errors"][0]


def test_generated_metric_contract_missing_path_fails_closed() -> None:
    evaluation = evaluate_generated_metric_contracts(
        {"different": 0.01},
        contracts=[_contract(metric_path=["requested", "metric"])],
        artifact_id="artifact:generated-candidate",
    )

    assert evaluation["all_required_passed"] is False
    assert "resolved no values" in evaluation["required_failure_errors"][0]


def test_generated_metric_contract_supports_between_all_and_optional_failures() -> None:
    contracts = [
        _contract(
            contract_id="calibration-band",
            metric_path=["calibration", "*"],
            operator="between",
            threshold=None,
            lower=0.9,
            upper=0.95,
            tolerance=0.01,
            aggregation="all",
        ),
        _contract(
            contract_id="optional-power",
            metric_path=["power"],
            operator=">=",
            threshold=0.9,
            tolerance=0.0,
            aggregation="identity",
            required=False,
        ),
    ]

    evaluation = evaluate_generated_metric_contracts(
        {"calibration": [0.89, 0.96], "power": 0.2},
        contracts=contracts,
        artifact_id="artifact:generated-candidate",
    )

    assert evaluation["n_passed"] == 1
    assert evaluation["n_failed"] == 1
    assert evaluation["all_required_passed"] is True
    assert evaluation["required_failure_errors"] == []


def test_authoritative_metric_requirement_rejects_invented_or_weakened_gate() -> None:
    requirement = _requirement()
    contract = _contract(
        contract_id="criterion-excess-quorum",
        requirement_id="architect:criterion-control",
        metric_path=["criterion_excess", "*"],
        metric_semantics=requirement["metric_semantics"],
        measurement_protocol=requirement["measurement_protocol"],
        required_runtime_replicates=requirement[
            "required_runtime_replicates"
        ],
        operator="<=",
        threshold=0.05,
        tolerance=0.0,
        aggregation="at_least_count",
        minimum_pass_count=10,
        source_anchors=requirement["source_anchors"],
    )

    errors = validate_generated_metric_contracts(
        [contract],
        expected_artifact_ids=("artifact:generated-candidate",),
        required_artifact_ids=("artifact:generated-candidate",),
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
        require_authoritative_requirements=True,
    )

    assert any("threshold must copy authoritative" in error for error in errors)
    assert any(
        "minimum_pass_count must copy authoritative" in error for error in errors
    )
    assert any("artifact/requirement pair" in error for error in errors)


def test_authoritative_metric_requirement_binds_and_evaluates_quorum() -> None:
    requirement = _requirement()
    contract = _contract(
        contract_id="criterion-excess-quorum",
        requirement_id="architect:criterion-control",
        metric_path=["criterion_excess", "*"],
        metric_semantics=requirement["metric_semantics"],
        measurement_protocol=requirement["measurement_protocol"],
        required_runtime_replicates=requirement[
            "required_runtime_replicates"
        ],
        operator=requirement["operator"],
        threshold=requirement["threshold"],
        tolerance=requirement["tolerance"],
        aggregation=requirement["aggregation"],
        minimum_pass_count=requirement["minimum_pass_count"],
        source_anchors=requirement["source_anchors"],
    )
    bound = bind_generated_metric_contract_authority(
        [contract],
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
    )

    evaluation = evaluate_generated_metric_contracts(
        {"criterion_excess": [0.01] * 11 + [0.03]},
        contracts=bound,
        artifact_id="artifact:generated-candidate",
        runtime_replicates=80,
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
        require_authoritative_requirements=True,
    )

    assert validate_generated_metric_requirements(
        [requirement],
        required_target_subsystems=("SimulationEngineer",),
    ) == []
    assert bound[0]["authority_requirement_fingerprint"]
    assert generated_metric_requirement_set_id([requirement])
    assert evaluation["all_required_passed"] is True
    assert evaluation["metric_requirement_authority_validated"] is True
    assert evaluation["evaluations"][0]["n_comparisons_passed"] == 11
    assert evaluation["evaluations"][0]["observed_runtime_replicates"] == 80


def test_authoritative_metric_requirement_fails_when_runtime_budget_differs() -> None:
    requirement = _requirement(required_runtime_replicates=80)
    contract = _contract(
        requirement_id=requirement["requirement_id"],
        metric_path=["criterion_excess"],
        metric_semantics=requirement["metric_semantics"],
        measurement_protocol=requirement["measurement_protocol"],
        required_runtime_replicates=requirement[
            "required_runtime_replicates"
        ],
        operator=requirement["operator"],
        threshold=requirement["threshold"],
        tolerance=requirement["tolerance"],
        aggregation="identity",
        minimum_pass_count=None,
        source_anchors=requirement["source_anchors"],
    )
    requirement = {
        **requirement,
        "aggregation": "identity",
        "minimum_pass_count": None,
    }
    bound = bind_generated_metric_contract_authority(
        [contract],
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
    )

    evaluation = evaluate_generated_metric_contracts(
        {"criterion_excess": 0.01},
        contracts=bound,
        artifact_id="artifact:generated-candidate",
        runtime_replicates=40,
        authoritative_requirements=[requirement],
        target_subsystem="SimulationEngineer",
        require_authoritative_requirements=True,
    )

    assert evaluation["all_required_passed"] is False
    assert "runtime replicates=40, required=80" in " ".join(
        evaluation["required_failure_errors"]
    )


@pytest.mark.parametrize(
    "metric_name",
    [
        "survival_curve_error",
        "optional_stopping_error",
        "subspace_projection_loss",
        "tail_quantile_bias",
        "false_discovery_rate",
    ],
)
def test_generated_metric_contract_treats_unrelated_metric_names_identically(
    metric_name: str,
) -> None:
    contract = _contract(metric_path=["diagnostics", metric_name])

    evaluation = evaluate_generated_metric_contracts(
        {"diagnostics": {metric_name: 0.09}},
        contracts=[contract],
        artifact_id="artifact:generated-candidate",
    )

    assert evaluation["all_required_passed"] is True
    assert evaluation["evaluations"][0]["resolved_values_preview"] == [0.09]
    assert evaluation["evaluations"][0]["aggregate_value"] == 0.09

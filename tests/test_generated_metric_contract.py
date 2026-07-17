from __future__ import annotations

import pytest

from ai_statistician.generated_metric_contract import (
    GENERATED_METRIC_CONTRACT_AGGREGATIONS,
    GENERATED_METRIC_CONTRACT_BOUNDARY,
    GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
    GENERATED_METRIC_CONTRACT_OPERATORS,
    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS,
    bind_generated_metric_contract_authority,
    evaluate_generated_metric_contracts,
    generated_metric_authority_repair_context,
    generated_metric_contract_binding_json_schema,
    generated_metric_contract_set_id,
    generated_metric_contracts_for_artifact,
    generated_metric_evaluation_semantics_contract,
    generated_metric_requirement_json_schema,
    generated_metric_requirement_prompt_schema,
    generated_metric_requirement_set_id,
    generated_metric_requirement_target_namespace_contract,
    materialize_generated_metric_contract_bindings,
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
    assert {
        "requirement_id",
        "metric_semantics",
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
    assert semantics["authoring_example"]["threshold"] == 0.10
    assert semantics["authoring_example"]["minimum_pass_count"] == 76
    assert "never place" in schema["threshold"]["description"]
    assert "separate from threshold" in schema["minimum_pass_count"][
        "description"
    ]


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

    context = generated_metric_authority_repair_context(
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
    assert any(
        "do not compare 0/1 flags to a quorum count" in instruction
        for instruction in context["repair_prompt_priority_instructions"]
    )


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

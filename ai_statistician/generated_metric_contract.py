from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


GENERATED_METRIC_CONTRACT_SCHEMA_VERSION = 1
GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES = 80
GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE = (
    "GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE"
)
GENERATED_METRIC_CONTRACT_BOUNDARY = (
    "Typed generated-metric contracts are pre-execution empirical acceptance "
    "controls. Runtime evaluation of them is implementation or simulation "
    "evidence only; it is not theorem proof evidence."
)
GENERATED_METRIC_CONTRACT_OPERATORS: tuple[str, ...] = (
    "<=",
    "<",
    ">=",
    ">",
    "==",
    "between",
)
GENERATED_METRIC_CONTRACT_AGGREGATIONS: tuple[str, ...] = (
    "identity",
    "mean",
    "min",
    "max",
    "all",
    "any",
    "at_least_count",
    "at_least_fraction",
)
GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS: tuple[str, ...] = (
    "AlgorithmEngineer",
    "SimulationEngineer",
)
GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED = (
    "architect_authored_coding_agent_bound_required"
)
GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED = (
    "architect_authored_coding_agent_bound_preferred"
)
GENERATED_METRIC_REQUIREMENT_BOUNDARY = (
    "Architect-authored empirical metric requirements are independent acceptance "
    "proposals supplied before coding-agent generation. Coding agents may bind "
    "artifact IDs and result paths but may not invent or weaken required gates. "
    "The requirements and their evaluations are empirical controls, not theorem "
    "proof evidence."
)
GENERATED_METRIC_AUTHORITY_COPY_FIELDS: tuple[str, ...] = (
    "requirement_id",
    "metric_semantics",
    "measurement_protocol",
    "required_runtime_replicates",
    "operator",
    "threshold",
    "lower",
    "upper",
    "tolerance",
    "aggregation",
    "minimum_pass_count",
    "minimum_pass_fraction",
    "required",
    "source_anchors",
)
GENERATED_METRIC_BINDING_FIELDS: tuple[str, ...] = (
    "contract_id",
    "requirement_id",
    "artifact_id",
    "metric_path",
)


def generated_sandbox_runtime_replicates(n_runs: int) -> int:
    """Return the runtime-owned work budget supplied to generated sandboxes."""

    return max(5, min(int(n_runs), GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES))


def generated_metric_requirement_target_namespace_contract() -> dict[str, Any]:
    """Describe coding-agent targets separately from runtime execution owners."""

    return {
        "namespace": "generated_code_author_subsystems",
        "field": "target_subsystems",
        "allowed_exact_values": list(
            GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
        ),
        "entry_rule": (
            "every array entry must equal one allowed value exactly; do not use "
            "a runtime execution-owner name in this coding-agent author namespace"
        ),
        "capability_eval_required_coverage": [
            {"target_subsystems": [target]}
            for target in GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
        ],
        "runtime_execution_owner_by_author_subsystem": {
            "AlgorithmEngineer": "AlgorithmEngineer",
            "SimulationEngineer": "SimulationEvaluator",
        },
    }


def generated_metric_requirement_json_schema() -> dict[str, Any]:
    """Return the machine-readable domain-neutral requirement schema.

    Keep this schema aligned with ``validate_generated_metric_requirements``.
    The provider sees this contract before generation, so semantic enums and
    scalar shapes belong here rather than only in a post-generation validator.
    """

    return {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "requirement_id",
            "target_subsystems",
            "metric_semantics",
            "measurement_protocol",
            "required_runtime_replicates",
            "operator",
            "threshold",
            "lower",
            "upper",
            "tolerance",
            "aggregation",
            "minimum_pass_count",
            "minimum_pass_fraction",
            "required",
            "source_anchors",
            "boundary",
        ],
        "properties": {
            "requirement_id": {"type": "string", "minLength": 1},
            "target_subsystems": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {
                    "type": "string",
                    "enum": list(
                        GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                    ),
                },
            },
            "metric_semantics": {"type": "string", "minLength": 1},
            "measurement_protocol": {"type": "string", "minLength": 1},
            "required_runtime_replicates": {
                "type": "integer",
                "minimum": 1,
            },
            "operator": {
                "type": "string",
                "enum": list(GENERATED_METRIC_CONTRACT_OPERATORS),
            },
            "threshold": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
            },
            "lower": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
            },
            "upper": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
            },
            "tolerance": {"type": "number", "minimum": 0},
            "aggregation": {
                "type": "string",
                "enum": list(GENERATED_METRIC_CONTRACT_AGGREGATIONS),
            },
            "minimum_pass_count": {
                "anyOf": [{"type": "integer"}, {"type": "null"}],
            },
            "minimum_pass_fraction": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
            },
            "required": {"type": "boolean"},
            "source_anchors": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "minLength": 1},
            },
            "boundary": {"type": "string", "minLength": 1},
        },
    }


def generated_metric_requirement_prompt_schema(
    *,
    target_subsystem: str | None = None,
) -> dict[str, Any]:
    """Return the domain-neutral requirement shape authored upstream."""

    target = target_subsystem or GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS[0]
    if target not in GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS:
        raise ValueError(
            "target_subsystem must be an exact generated-code author subsystem"
        )

    return {
        "requirement_id": f"stable unique string for {target}",
        "target_subsystems": [target],
        "metric_semantics": (
            "exactly one independently compared scalar quantity, or one homogeneous "
            "collection whose members all use this row's single comparison; when a "
            "target varies by scenario, define a scalar deviation or ratio to it"
        ),
        "measurement_protocol": (
            "how this one comparison quantity is computed across seeds, scenarios, "
            "or replicates; split quantities with different comparisons into rows"
        ),
        "required_runtime_replicates": (
            "positive integer copied from the runtime-owned generated sandbox budget"
        ),
        "operator": "<=|<|>=|>|==|between",
        "threshold": "finite number for non-between operators; null for between",
        "lower": "finite number for between; null otherwise",
        "upper": "finite number for between; null otherwise",
        "tolerance": "finite nonnegative number; use 0 for an exact boundary",
        "aggregation": (
            "identity|mean|min|max|all|any|at_least_count|at_least_fraction"
        ),
        "minimum_pass_count": (
            "positive integer for at_least_count; null otherwise"
        ),
        "minimum_pass_fraction": (
            "number in [0,1] for at_least_fraction; null otherwise"
        ),
        "required": True,
        "source_anchors": [
            "exact question, source, derivation, or Architect criterion id",
        ],
        "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    }


def generated_metric_contract_prompt_schema(*, artifact_id_label: str) -> dict[str, Any]:
    """Return the minimal domain-neutral binding exposed to coding agents."""

    label = artifact_id_label.strip() or "artifact id"
    return {
        "contract_id": "stable unique string",
        "requirement_id": (
            "exact upstream empirical_metric_requirements requirement_id"
        ),
        "artifact_id": f"exact {label}; copy unchanged",
        "metric_path": [
            "JSON object key, zero-based list index, or * wildcard",
        ],
    }


def generated_metric_contract_binding_json_schema(
    *,
    requirement_ids: Sequence[str] = (),
    artifact_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Return a strict schema for the coding-agent side of an authority join."""

    requirement_values = list(
        dict.fromkeys(str(value).strip() for value in requirement_ids if str(value).strip())
    )
    artifact_values = list(
        dict.fromkeys(str(value).strip() for value in artifact_ids if str(value).strip())
    )
    requirement_schema: dict[str, Any] = {"type": "string", "minLength": 1}
    artifact_schema: dict[str, Any] = {"type": "string", "minLength": 1}
    if requirement_values:
        requirement_schema["enum"] = requirement_values
    if artifact_values:
        artifact_schema["enum"] = artifact_values
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(GENERATED_METRIC_BINDING_FIELDS),
        "properties": {
            "contract_id": {"type": "string", "minLength": 1},
            "requirement_id": requirement_schema,
            "artifact_id": artifact_schema,
            "metric_path": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "anyOf": [
                        {"type": "string", "minLength": 1},
                        {"type": "integer", "minimum": 0},
                    ]
                },
            },
        },
    }


def generated_metric_authority_repair_context(
    requirements: Sequence[Mapping[str, Any]],
    *,
    target_subsystem: str,
    artifact_id_label: str,
) -> dict[str, Any]:
    """Build a complete, domain-neutral binding contract for LLM packet repair."""

    relevant = generated_metric_requirements_for_subsystem(
        list(requirements),
        target_subsystem=target_subsystem,
    )
    return {
        "target_subsystem": target_subsystem,
        "artifact_id_source": artifact_id_label,
        "authoritative_empirical_metric_requirements": relevant,
        "required_authority_binding_rows": [
            {
                field: requirement.get(field)
                for field in GENERATED_METRIC_AUTHORITY_COPY_FIELDS
            }
            for requirement in relevant
            if requirement.get("required") is True
        ],
        "coding_agent_may_author_only": [
            "contract_id",
            "requirement_id",
            "artifact_id",
            "metric_path",
        ],
        "authority_copy_fields": list(GENERATED_METRIC_AUTHORITY_COPY_FIELDS),
        "authority_materialization_mode": "runtime_joined_frozen_requirement",
        "repair_prompt_priority_instructions": [
            (
                "For every required_authority_binding_rows item and every generated "
                "artifact, emit one metric_contracts row."
            ),
            (
                "For each row, select the exact requirement_id assigned to this "
                "subsystem. Do not emit authority_copy_fields other than "
                "requirement_id; AgentRuntime joins the frozen requirement."
            ),
            (
                "Author only contract_id, requirement_id, artifact_id, and metric_path; "
                "the metric_path must resolve against the generated run_sandbox result."
            ),
        ],
        "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    }


def validate_generated_metric_contracts(
    value: Any,
    *,
    expected_artifact_ids: Sequence[str] = (),
    required_artifact_ids: Sequence[str] = (),
    authoritative_requirements: Any = None,
    target_subsystem: str = "",
    require_authoritative_requirements: bool = False,
) -> list[str]:
    """Validate metric contracts without inferring any statistical vocabulary."""

    if not isinstance(value, list):
        return ["metric_contracts must be an array"]
    expected_ids = {str(item).strip() for item in expected_artifact_ids if str(item).strip()}
    required_ids = {str(item).strip() for item in required_artifact_ids if str(item).strip()}
    errors: list[str] = []
    seen_contract_ids: set[str] = set()
    covered_artifact_ids: set[str] = set()
    for index, raw_contract in enumerate(value):
        prefix = f"metric_contracts[{index}]"
        if not isinstance(raw_contract, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        contract_id = str(raw_contract.get("contract_id", "") or "").strip()
        if not contract_id:
            errors.append(f"{prefix}.contract_id must be a nonempty string")
        elif contract_id in seen_contract_ids:
            errors.append(f"duplicate metric contract_id: {contract_id}")
        else:
            seen_contract_ids.add(contract_id)
        artifact_id = str(raw_contract.get("artifact_id", "") or "").strip()
        if not artifact_id:
            errors.append(f"{prefix}.artifact_id must be a nonempty string")
        else:
            covered_artifact_ids.add(artifact_id)
            if expected_ids and artifact_id not in expected_ids:
                errors.append(
                    f"{prefix}.artifact_id is not a supplied task artifact: {artifact_id}"
                )
        metric_path = raw_contract.get("metric_path")
        if not isinstance(metric_path, list) or not metric_path:
            errors.append(f"{prefix}.metric_path must be a nonempty array")
        else:
            for path_index, segment in enumerate(metric_path):
                if isinstance(segment, bool) or not isinstance(segment, (str, int)):
                    errors.append(
                        f"{prefix}.metric_path[{path_index}] must be a string or integer"
                    )
                elif isinstance(segment, str) and not segment.strip():
                    errors.append(
                        f"{prefix}.metric_path[{path_index}] must not be empty"
                    )
                elif isinstance(segment, int) and segment < 0:
                    errors.append(
                        f"{prefix}.metric_path[{path_index}] must be nonnegative"
                    )
        errors.extend(_metric_comparison_shape_errors(raw_contract, prefix=prefix))
        if not isinstance(raw_contract.get("required"), bool):
            errors.append(f"{prefix}.required must be a boolean")
        source_anchors = raw_contract.get("source_anchors")
        if not isinstance(source_anchors, list) or not source_anchors:
            errors.append(f"{prefix}.source_anchors must contain at least one id")
        elif any(
            not isinstance(anchor, str) or not anchor.strip()
            for anchor in source_anchors
        ):
            errors.append(
                f"{prefix}.source_anchors entries must be nonempty strings"
            )
        if "required_runtime_replicates" in raw_contract:
            runtime_replicates = raw_contract.get("required_runtime_replicates")
            if (
                isinstance(runtime_replicates, bool)
                or not isinstance(runtime_replicates, int)
                or runtime_replicates <= 0
            ):
                errors.append(
                    f"{prefix}.required_runtime_replicates must be a positive integer"
                )
    missing_artifact_ids = required_ids - covered_artifact_ids
    if missing_artifact_ids:
        errors.append(
            "metric_contracts must bind every required artifact_id; missing: "
            + ", ".join(sorted(missing_artifact_ids))
        )
    if require_authoritative_requirements or (
        isinstance(authoritative_requirements, list)
        and bool(authoritative_requirements)
    ):
        errors.extend(
            _generated_metric_contract_authority_errors(
                value,
                authoritative_requirements=authoritative_requirements,
                target_subsystem=target_subsystem,
                required_artifact_ids=tuple(sorted(required_ids)),
                require_authoritative_requirements=require_authoritative_requirements,
            )
        )
    return sorted(set(errors))


def validate_generated_metric_requirements(
    value: Any,
    *,
    required_target_subsystems: Sequence[str] = (),
    expected_runtime_replicates: int | None = None,
) -> list[str]:
    """Validate upstream requirements without interpreting metric vocabulary."""

    if not isinstance(value, list):
        return ["empirical_metric_requirements must be an array"]
    errors: list[str] = []
    seen_ids: set[str] = set()
    covered_required_targets: set[str] = set()
    for index, raw_requirement in enumerate(value):
        prefix = f"empirical_metric_requirements[{index}]"
        if not isinstance(raw_requirement, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        requirement_id = str(
            raw_requirement.get("requirement_id", "") or ""
        ).strip()
        if not requirement_id:
            errors.append(f"{prefix}.requirement_id must be a nonempty string")
        elif requirement_id in seen_ids:
            errors.append(f"duplicate empirical metric requirement_id: {requirement_id}")
        else:
            seen_ids.add(requirement_id)
        targets = raw_requirement.get("target_subsystems")
        if not isinstance(targets, list) or not targets:
            errors.append(f"{prefix}.target_subsystems must be a nonempty array")
            target_values: set[str] = set()
        else:
            target_values = {
                str(target).strip() for target in targets if str(target).strip()
            }
            invalid_targets = target_values - set(
                GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
            )
            if invalid_targets:
                errors.append(
                    f"{prefix}.target_subsystems contains unsupported values: "
                    + ", ".join(sorted(invalid_targets))
                )
            if len(target_values) != len(targets):
                errors.append(
                    f"{prefix}.target_subsystems entries must be unique nonempty strings"
                )
        for field in ("metric_semantics", "measurement_protocol"):
            if not str(raw_requirement.get(field, "") or "").strip():
                errors.append(f"{prefix}.{field} must be a nonempty string")
        runtime_replicates = raw_requirement.get("required_runtime_replicates")
        if (
            isinstance(runtime_replicates, bool)
            or not isinstance(runtime_replicates, int)
            or runtime_replicates <= 0
        ):
            errors.append(
                f"{prefix}.required_runtime_replicates must be a positive integer"
            )
        elif (
            expected_runtime_replicates is not None
            and runtime_replicates != expected_runtime_replicates
        ):
            errors.append(
                f"{prefix}.required_runtime_replicates must equal the runtime-owned "
                f"generated sandbox budget {expected_runtime_replicates}"
            )
        errors.extend(_metric_comparison_shape_errors(raw_requirement, prefix=prefix))
        required = raw_requirement.get("required")
        if not isinstance(required, bool):
            errors.append(f"{prefix}.required must be a boolean")
        elif required:
            covered_required_targets.update(target_values)
        errors.extend(_metric_source_anchor_errors(raw_requirement, prefix=prefix))
    missing_targets = {
        str(target).strip()
        for target in required_target_subsystems
        if str(target).strip()
    } - covered_required_targets
    if missing_targets:
        errors.append(
            "empirical_metric_requirements must include at least one required row "
            "for every requested target subsystem; missing: "
            + ", ".join(sorted(missing_targets))
        )
    return sorted(set(errors))


def generated_metric_requirement_set_id(
    requirements: Sequence[Mapping[str, Any]],
) -> str:
    if not requirements:
        return ""
    return "generated_metric_requirement_set:" + stable_hash(
        [dict(requirement) for requirement in requirements]
    )[:20]


def generated_metric_requirements_for_subsystem(
    value: Any,
    *,
    target_subsystem: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    target = target_subsystem.strip()
    return [
        dict(requirement)
        for requirement in value
        if isinstance(requirement, Mapping)
        and target
        in {
            str(item).strip()
            for item in requirement.get("target_subsystems", []) or []
        }
    ]


def generated_metric_requirements_from_context(
    value: Any,
    *,
    target_subsystem: str,
) -> list[dict[str, Any]]:
    """Read the first explicit Architect authority set from known context slots."""

    candidates: list[Any] = []
    if isinstance(value, Mapping):
        for key in ("architect_evidence_contract", "runtime_requested_evidence_contract"):
            nested = value.get(key, {})
            if isinstance(nested, Mapping):
                candidates.append(nested.get("empirical_metric_requirements"))
        candidates.append(value.get("empirical_metric_requirements"))
        direct_plan = value.get("architect_runtime_plan", {})
        if isinstance(direct_plan, Mapping):
            direct_contract = direct_plan.get("evidence_contract", {})
            if isinstance(direct_contract, Mapping):
                candidates.append(
                    direct_contract.get("empirical_metric_requirements")
                )
        architect_context = value.get("architect_context", {})
        if isinstance(architect_context, Mapping):
            plan = architect_context.get("architect_runtime_plan", {})
            if isinstance(plan, Mapping):
                contract = plan.get("evidence_contract", {})
                if isinstance(contract, Mapping):
                    candidates.append(contract.get("empirical_metric_requirements"))
    elif isinstance(value, list):
        candidates.append(value)
    for candidate in candidates:
        relevant = generated_metric_requirements_for_subsystem(
            candidate,
            target_subsystem=target_subsystem,
        )
        if relevant:
            return relevant
    return []


def generated_metric_requirement_authority_policy_from_context(value: Any) -> str:
    if not isinstance(value, Mapping):
        return ""
    candidates: list[Mapping[str, Any]] = []
    for key in ("architect_evidence_contract", "runtime_requested_evidence_contract"):
        nested = value.get(key, {})
        if isinstance(nested, Mapping):
            candidates.append(nested)
    candidates.append(value)
    direct_plan = value.get("architect_runtime_plan", {})
    if isinstance(direct_plan, Mapping):
        direct_contract = direct_plan.get("evidence_contract", {})
        if isinstance(direct_contract, Mapping):
            candidates.append(direct_contract)
    architect_context = value.get("architect_context", {})
    if isinstance(architect_context, Mapping):
        plan = architect_context.get("architect_runtime_plan", {})
        if isinstance(plan, Mapping):
            contract = plan.get("evidence_contract", {})
            if isinstance(contract, Mapping):
                candidates.append(contract)
    for candidate in candidates:
        policy = str(
            candidate.get("generated_metric_requirement_authority_policy", "") or ""
        ).strip()
        if policy:
            return policy
    return ""


def bind_generated_metric_contract_authority(
    contracts: Sequence[Mapping[str, Any]],
    *,
    authoritative_requirements: Sequence[Mapping[str, Any]],
    target_subsystem: str,
) -> list[dict[str, Any]]:
    """Attach deterministic lineage only to contracts that exactly preserve authority."""

    requirements = generated_metric_requirements_for_subsystem(
        list(authoritative_requirements),
        target_subsystem=target_subsystem,
    )
    by_id = {
        str(row.get("requirement_id", "") or "").strip(): row
        for row in requirements
        if str(row.get("requirement_id", "") or "").strip()
    }
    set_id = generated_metric_requirement_set_id(requirements)
    bound: list[dict[str, Any]] = []
    for raw_contract in contracts:
        contract = dict(raw_contract)
        requirement = by_id.get(
            str(contract.get("requirement_id", "") or "").strip()
        )
        if requirement is not None and not _metric_authority_mismatches(
            contract,
            requirement,
        ):
            contract["authority_requirement_fingerprint"] = stable_hash(
                dict(requirement)
            )
            contract["authority_requirement_set_id"] = set_id
            contract["authority_source_subsystem"] = "ArchitectCoordinator"
        bound.append(contract)
    return bound


def materialize_generated_metric_contract_bindings(
    bindings: Sequence[Mapping[str, Any]],
    *,
    authoritative_requirements: Sequence[Mapping[str, Any]],
    target_subsystem: str,
) -> list[dict[str, Any]]:
    """Join coding-agent bindings to immutable Architect-authored requirements.

    The coding agent chooses only a requirement foreign key, artifact foreign key,
    and returned metric path. Any attempted authority-field echo is discarded and
    audited before the normal strict authority validator runs.
    """

    requirements = generated_metric_requirements_for_subsystem(
        list(authoritative_requirements),
        target_subsystem=target_subsystem,
    )
    by_id = {
        str(row.get("requirement_id", "") or "").strip(): row
        for row in requirements
        if str(row.get("requirement_id", "") or "").strip()
    }
    materialized: list[dict[str, Any]] = []
    for raw_binding in bindings:
        contract = dict(raw_binding)
        requirement_id = str(contract.get("requirement_id", "") or "").strip()
        requirement = by_id.get(requirement_id)
        if requirement is None:
            materialized.append(contract)
            continue
        submitted_authority_fields = [
            field
            for field in GENERATED_METRIC_AUTHORITY_COPY_FIELDS
            if field != "requirement_id" and field in contract
        ]
        discarded_override_fields = [
            field
            for field in submitted_authority_fields
            if contract.get(field) != requirement.get(field)
        ]
        for field in GENERATED_METRIC_AUTHORITY_COPY_FIELDS:
            contract[field] = requirement.get(field)
        contract["boundary"] = GENERATED_METRIC_CONTRACT_BOUNDARY
        contract["authority_binding_mode"] = "runtime_joined_frozen_requirement"
        contract["coding_agent_submitted_authority_fields"] = (
            submitted_authority_fields
        )
        contract["discarded_authority_override_fields"] = (
            discarded_override_fields
        )
        materialized.append(contract)
    return bind_generated_metric_contract_authority(
        materialized,
        authoritative_requirements=requirements,
        target_subsystem=target_subsystem,
    )


def generated_metric_contracts_for_artifact(
    value: Any,
    *,
    artifact_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    target = artifact_id.strip()
    return [
        dict(contract)
        for contract in value
        if isinstance(contract, Mapping)
        and str(contract.get("artifact_id", "") or "").strip() == target
    ]


def generated_metric_contract_set_id(contracts: Sequence[Mapping[str, Any]]) -> str:
    if not contracts:
        return ""
    return "generated_metric_contract_set:" + stable_hash(
        [dict(contract) for contract in contracts]
    )[:20]


def evaluate_generated_metric_contracts(
    metrics: Any,
    *,
    contracts: Sequence[Mapping[str, Any]],
    artifact_id: str,
    runtime_replicates: int | None = None,
    authoritative_requirements: Any = None,
    target_subsystem: str = "",
    require_authoritative_requirements: bool = False,
) -> dict[str, Any]:
    """Evaluate validated contracts against one generated result artifact."""

    contract_rows = [dict(contract) for contract in contracts]
    schema_errors = validate_generated_metric_contracts(
        contract_rows,
        expected_artifact_ids=(artifact_id,),
        required_artifact_ids=(artifact_id,),
        authoritative_requirements=authoritative_requirements,
        target_subsystem=target_subsystem,
        require_authoritative_requirements=require_authoritative_requirements,
    )
    evaluations: list[dict[str, Any]] = []
    required_failure_errors: list[str] = []
    if schema_errors:
        required_failure_errors.extend(schema_errors)
    else:
        for contract in contract_rows:
            evaluation = _evaluate_generated_metric_contract(
                metrics,
                contract=contract,
            )
            expected_replicates = contract.get("required_runtime_replicates")
            if expected_replicates is not None:
                evaluation["required_runtime_replicates"] = expected_replicates
                evaluation["observed_runtime_replicates"] = runtime_replicates
                if runtime_replicates is None:
                    evaluation["passed"] = False
                    evaluation["errors"].append(
                        f"metric contract {evaluation['contract_id']}: runtime "
                        "replicate count was not recorded"
                    )
                elif int(runtime_replicates) != int(expected_replicates):
                    evaluation["passed"] = False
                    evaluation["errors"].append(
                        f"metric contract {evaluation['contract_id']}: runtime "
                        f"replicates={runtime_replicates}, required="
                        f"{expected_replicates}"
                    )
            evaluations.append(evaluation)
            if contract.get("required") is True and evaluation["passed"] is not True:
                required_failure_errors.extend(evaluation["errors"])
    n_passed = sum(1 for row in evaluations if row.get("passed") is True)
    n_failed = sum(1 for row in evaluations if row.get("passed") is not True)
    return {
        "schema_version": GENERATED_METRIC_CONTRACT_SCHEMA_VERSION,
        "artifact_kind": "GeneratedMetricContractEvaluation",
        "artifact_id": artifact_id,
        "metric_contract_set_id": generated_metric_contract_set_id(contract_rows),
        "metric_requirement_set_id": generated_metric_requirement_set_id(
            generated_metric_requirements_for_subsystem(
                authoritative_requirements,
                target_subsystem=target_subsystem,
            )
        ),
        "metric_requirement_authority_enforced": bool(
            require_authoritative_requirements
        ),
        "metric_requirement_authority_validated": bool(
            require_authoritative_requirements and not schema_errors
        ),
        "metric_contract_schema_valid": not schema_errors,
        "n_contracts": len(contract_rows),
        "n_passed": n_passed,
        "n_failed": n_failed,
        "all_required_passed": not required_failure_errors,
        "required_failure_errors": list(dict.fromkeys(required_failure_errors)),
        "evaluations": evaluations,
        "proof_evidence_status": GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
        "boundary": GENERATED_METRIC_CONTRACT_BOUNDARY,
    }


def _evaluate_generated_metric_contract(
    metrics: Any,
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    contract_id = str(contract.get("contract_id", "") or "")
    path = list(contract.get("metric_path", []) or [])
    values, path_error = _resolve_generated_metric_path(metrics, path)
    numeric_values: list[float] = []
    errors: list[str] = []
    if path_error:
        errors.append(f"metric contract {contract_id}: {path_error}")
    else:
        numeric_values, numeric_error = _metric_numeric_values(values)
        if numeric_error:
            errors.append(f"metric contract {contract_id}: {numeric_error}")
    aggregation = str(contract.get("aggregation", "") or "")
    aggregate_value: float | None = None
    comparison_results: list[bool] = []
    if not errors:
        if aggregation == "identity":
            if len(numeric_values) != 1:
                errors.append(
                    f"metric contract {contract_id}: identity aggregation resolved "
                    f"{len(numeric_values)} numeric values, expected exactly 1"
                )
            else:
                aggregate_value = numeric_values[0]
                comparison_results = [
                    _metric_comparison_passes(aggregate_value, contract)
                ]
        elif aggregation == "mean":
            aggregate_value = sum(numeric_values) / len(numeric_values)
            comparison_results = [_metric_comparison_passes(aggregate_value, contract)]
        elif aggregation == "min":
            aggregate_value = min(numeric_values)
            comparison_results = [_metric_comparison_passes(aggregate_value, contract)]
        elif aggregation == "max":
            aggregate_value = max(numeric_values)
            comparison_results = [_metric_comparison_passes(aggregate_value, contract)]
        elif aggregation in {
            "all",
            "any",
            "at_least_count",
            "at_least_fraction",
        }:
            comparison_results = [
                _metric_comparison_passes(value, contract)
                for value in numeric_values
            ]
        else:  # pragma: no cover - guarded by packet validation
            errors.append(f"metric contract {contract_id}: unsupported aggregation")
    passed = False
    if not errors:
        if aggregation == "any":
            passed = any(comparison_results)
        elif aggregation == "at_least_count":
            passed = sum(comparison_results) >= int(contract["minimum_pass_count"])
            aggregate_value = float(sum(comparison_results))
        elif aggregation == "at_least_fraction":
            aggregate_value = sum(comparison_results) / len(comparison_results)
            passed = aggregate_value >= float(contract["minimum_pass_fraction"])
        else:
            passed = all(comparison_results)
        if not passed:
            errors.append(
                f"metric contract {contract_id} failed: path={_metric_path_text(path)} "
                f"aggregation={aggregation} operator={contract.get('operator')} "
                f"observed={aggregate_value if aggregate_value is not None else numeric_values[:8]}"
            )
    return {
        "contract_id": contract_id,
        "artifact_id": str(contract.get("artifact_id", "") or ""),
        "metric_path": path,
        "operator": str(contract.get("operator", "") or ""),
        "aggregation": aggregation,
        "required": contract.get("required") is True,
        "n_resolved_values": len(numeric_values),
        "resolved_values_preview": numeric_values[:12],
        "aggregate_value": aggregate_value,
        "n_comparisons_passed": sum(comparison_results),
        "n_comparisons": len(comparison_results),
        "passed": passed,
        "errors": errors,
        "source_anchors": list(contract.get("source_anchors", []) or []),
        "requirement_id": str(contract.get("requirement_id", "") or ""),
        "authority_requirement_fingerprint": str(
            contract.get("authority_requirement_fingerprint", "") or ""
        ),
        "authority_requirement_set_id": str(
            contract.get("authority_requirement_set_id", "") or ""
        ),
        "proof_evidence_status": GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
    }


def _generated_metric_contract_authority_errors(
    contracts: Any,
    *,
    authoritative_requirements: Any,
    target_subsystem: str,
    required_artifact_ids: Sequence[str],
    require_authoritative_requirements: bool,
) -> list[str]:
    errors = validate_generated_metric_requirements(
        authoritative_requirements,
        required_target_subsystems=(target_subsystem,)
        if require_authoritative_requirements and target_subsystem
        else (),
    )
    if not isinstance(contracts, list) or not isinstance(
        authoritative_requirements, list
    ):
        return errors
    relevant = generated_metric_requirements_for_subsystem(
        authoritative_requirements,
        target_subsystem=target_subsystem,
    )
    requirements_by_id = {
        str(row.get("requirement_id", "") or "").strip(): row
        for row in relevant
        if str(row.get("requirement_id", "") or "").strip()
    }
    covered_pairs: set[tuple[str, str]] = set()
    covered_requirements: set[str] = set()
    for index, raw_contract in enumerate(contracts):
        if not isinstance(raw_contract, Mapping):
            continue
        prefix = f"metric_contracts[{index}]"
        requirement_id = str(
            raw_contract.get("requirement_id", "") or ""
        ).strip()
        is_required = raw_contract.get("required") is True
        if not requirement_id:
            if is_required and require_authoritative_requirements:
                errors.append(
                    f"{prefix}.requirement_id must bind a required upstream "
                    "empirical metric requirement"
                )
            continue
        requirement = requirements_by_id.get(requirement_id)
        if requirement is None:
            errors.append(
                f"{prefix}.requirement_id is not an authoritative requirement "
                f"for {target_subsystem or '<missing subsystem>'}: {requirement_id}"
            )
            continue
        mismatches = _metric_authority_mismatches(raw_contract, requirement)
        for field in mismatches:
            errors.append(
                f"{prefix}.{field} must copy authoritative requirement "
                f"{requirement_id} unchanged"
            )
        if not mismatches:
            covered_requirements.add(requirement_id)
            artifact_id = str(raw_contract.get("artifact_id", "") or "").strip()
            if artifact_id:
                covered_pairs.add((artifact_id, requirement_id))
            expected_fingerprint = stable_hash(dict(requirement))
            fingerprint = str(
                raw_contract.get("authority_requirement_fingerprint", "") or ""
            ).strip()
            if fingerprint and fingerprint != expected_fingerprint:
                errors.append(
                    f"{prefix}.authority_requirement_fingerprint does not match "
                    f"authoritative requirement {requirement_id}"
                )
    required_ids = {
        str(row.get("requirement_id", "") or "").strip()
        for row in relevant
        if row.get("required") is True
        and str(row.get("requirement_id", "") or "").strip()
    }
    if require_authoritative_requirements:
        missing_requirements = required_ids - covered_requirements
        if missing_requirements:
            errors.append(
                "metric_contracts must bind every authoritative required metric "
                "requirement; missing: " + ", ".join(sorted(missing_requirements))
            )
        missing_pairs = {
            (artifact_id, requirement_id)
            for artifact_id in required_artifact_ids
            for requirement_id in required_ids
        } - covered_pairs
        if missing_pairs:
            errors.append(
                "metric_contracts must bind every required artifact/requirement "
                "pair; missing: "
                + ", ".join(
                    f"{artifact_id}->{requirement_id}"
                    for artifact_id, requirement_id in sorted(missing_pairs)
                )
            )
    return errors


def _metric_authority_mismatches(
    contract: Mapping[str, Any],
    requirement: Mapping[str, Any],
) -> list[str]:
    mismatches: list[str] = []
    for field in (
        "metric_semantics",
        "measurement_protocol",
        "operator",
        "aggregation",
        "required",
        "source_anchors",
    ):
        if _normalized_authority_value(contract.get(field)) != (
            _normalized_authority_value(requirement.get(field))
        ):
            mismatches.append(field)
    for field in (
        "threshold",
        "lower",
        "upper",
        "tolerance",
        "minimum_pass_count",
        "minimum_pass_fraction",
        "required_runtime_replicates",
    ):
        if not _authority_numeric_values_equal(
            contract.get(field),
            requirement.get(field),
        ):
            mismatches.append(field)
    return mismatches


def _normalized_authority_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [_normalized_authority_value(item) for item in value]
    return value


def _authority_numeric_values_equal(left: Any, right: Any) -> bool:
    if left in (None, "") and right in (None, ""):
        return True
    if not _finite_number(left) or not _finite_number(right):
        return left == right
    return float(left) == float(right)


def _metric_comparison_shape_errors(
    value: Mapping[str, Any],
    *,
    prefix: str,
) -> list[str]:
    errors: list[str] = []
    operator = str(value.get("operator", "") or "").strip()
    if operator not in GENERATED_METRIC_CONTRACT_OPERATORS:
        errors.append(
            f"{prefix}.operator must be one of "
            + ", ".join(GENERATED_METRIC_CONTRACT_OPERATORS)
        )
    aggregation = str(value.get("aggregation", "") or "").strip()
    if aggregation not in GENERATED_METRIC_CONTRACT_AGGREGATIONS:
        errors.append(
            f"{prefix}.aggregation must be one of "
            + ", ".join(GENERATED_METRIC_CONTRACT_AGGREGATIONS)
        )
    tolerance = value.get("tolerance")
    if not _finite_number(tolerance) or float(tolerance) < 0.0:
        errors.append(f"{prefix}.tolerance must be a finite nonnegative number")
    if operator == "between":
        lower = value.get("lower")
        upper = value.get("upper")
        if not _finite_number(lower):
            errors.append(f"{prefix}.lower must be a finite number for between")
        if not _finite_number(upper):
            errors.append(f"{prefix}.upper must be a finite number for between")
        if (
            _finite_number(lower)
            and _finite_number(upper)
            and float(lower) > float(upper)
        ):
            errors.append(f"{prefix}.lower must be <= upper")
    elif not _finite_number(value.get("threshold")):
        errors.append(
            f"{prefix}.threshold must be a finite number for operator "
            f"{operator or '<missing>'}"
        )
    if aggregation == "at_least_count":
        count = value.get("minimum_pass_count")
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            errors.append(
                f"{prefix}.minimum_pass_count must be a positive integer for "
                "at_least_count"
            )
    if aggregation == "at_least_fraction":
        fraction = value.get("minimum_pass_fraction")
        if not _finite_number(fraction) or not 0.0 <= float(fraction) <= 1.0:
            errors.append(
                f"{prefix}.minimum_pass_fraction must be in [0,1] for "
                "at_least_fraction"
            )
    return errors


def _metric_source_anchor_errors(
    value: Mapping[str, Any],
    *,
    prefix: str,
) -> list[str]:
    source_anchors = value.get("source_anchors")
    if not isinstance(source_anchors, list) or not source_anchors:
        return [f"{prefix}.source_anchors must contain at least one id"]
    if any(
        not isinstance(anchor, str) or not anchor.strip()
        for anchor in source_anchors
    ):
        return [f"{prefix}.source_anchors entries must be nonempty strings"]
    return []


def _resolve_generated_metric_path(
    value: Any,
    path: Sequence[Any],
) -> tuple[list[Any], str]:
    current = [value]
    for index, segment in enumerate(path):
        next_values: list[Any] = []
        for item in current:
            if segment == "*":
                if isinstance(item, Mapping):
                    next_values.extend(item.values())
                elif isinstance(item, (list, tuple)):
                    next_values.extend(item)
                continue
            if isinstance(item, Mapping):
                key = str(segment)
                if key in item:
                    next_values.append(item[key])
                continue
            if isinstance(item, (list, tuple)) and isinstance(segment, int):
                if 0 <= segment < len(item):
                    next_values.append(item[segment])
        if not next_values:
            return [], (
                f"metric_path {_metric_path_text(path)} resolved no values at "
                f"segment {index}:{segment}"
            )
        current = next_values
    return current, ""


def _metric_numeric_values(values: Sequence[Any]) -> tuple[list[float], str]:
    numeric: list[float] = []
    stack = list(values)
    while stack:
        value = stack.pop(0)
        if isinstance(value, (list, tuple)):
            stack[0:0] = list(value)
            continue
        if not _finite_number(value):
            return [], "metric_path resolved a nonnumeric or nonfinite value"
        numeric.append(float(value))
    if not numeric:
        return [], "metric_path resolved no numeric values"
    return numeric, ""


def _metric_comparison_passes(value: float, contract: Mapping[str, Any]) -> bool:
    operator = str(contract.get("operator", "") or "")
    tolerance = float(contract.get("tolerance", 0.0) or 0.0)
    if operator == "between":
        return (
            float(contract["lower"]) - tolerance
            <= value
            <= float(contract["upper"]) + tolerance
        )
    threshold = float(contract["threshold"])
    if operator == "<=":
        return value <= threshold + tolerance
    if operator == "<":
        return value < threshold + tolerance
    if operator == ">=":
        return value >= threshold - tolerance
    if operator == ">":
        return value > threshold - tolerance
    if operator == "==":
        return abs(value - threshold) <= tolerance
    return False


def _metric_path_text(path: Sequence[Any]) -> str:
    return "/" + "/".join(str(segment) for segment in path)


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )

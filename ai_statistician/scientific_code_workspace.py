from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .client_tool_loop import (
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from .scientific_sandbox import (
    PYTHON_SCIENTIFIC_DEPENDENCIES,
    R_SCIENTIFIC_DEPENDENCIES,
    SCIENTIFIC_SANDBOX_LANGUAGES,
    SCIENTIFIC_SANDBOX_PROFILES,
    generated_code_execution_contract_errors,
    normalized_generated_code_language,
    normalized_generated_code_profile,
    normalized_scientific_dependencies,
)
from .structured_output_retry import PacketValidationError


ScientificCodeCheck = Callable[[Mapping[str, Any]], Mapping[str, Any]]

SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS = "native_client_tools"
SCIENTIFIC_SOURCE_TRANSPORT_STRUCTURED_PACKET = "structured_packet"
SCIENTIFIC_SOURCE_SUBMISSION_TOOL = "submit_scientific_source"
SCIENTIFIC_SOURCE_REVISE_CURRENT = "revise_current_source"
SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER = (
    "return_to_bound_dependency_owner"
)
SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY = "scientific_consumer_revision"
_SCIENTIFIC_PACKAGES = (
    PYTHON_SCIENTIFIC_DEPENDENCIES + R_SCIENTIFIC_DEPENDENCIES
)
_OUTCOME_DERIVED_SHAPE_FIELDS = frozenset(
    {"length", "dimensions", "field_count", "truncated_field_count"}
)


@dataclass(frozen=True)
class ScientificCodeWorkspaceResult:
    code_draft: Mapping[str, Any]
    check_result: Mapping[str, Any]
    evidence: Mapping[str, Any]


def _outcome_blind_request_shape(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _outcome_blind_request_shape(child)
            for key, child in value.items()
            if str(key) not in _OUTCOME_DERIVED_SHAPE_FIELDS
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_outcome_blind_request_shape(child) for child in value]
    return deepcopy(value)


def scientific_workspace_prototype_observation(
    prototype: Mapping[str, Any],
    *,
    include_empirical_outcomes: bool = True,
) -> dict[str, Any]:
    """Project one persisted sandbox result into bounded model feedback."""

    contracts = {
        str(row.get("contract_id", "") or ""): row
        for row in prototype.get("metric_contracts", []) or []
        if isinstance(row, Mapping)
        and str(row.get("contract_id", "") or "").strip()
    }
    evaluation = prototype.get("metric_contract_evaluation", {})
    evaluation_rows = (
        evaluation.get("evaluations", [])
        if isinstance(evaluation, Mapping)
        else []
    )
    measurement_interface_failures = (
        scientific_workspace_measurement_interface_failures(prototype)
    )
    failed_contracts: list[dict[str, Any]] = []
    for row in evaluation_rows or []:
        if not isinstance(row, Mapping) or row.get("passed") is True:
            continue
        contract_id = str(row.get("contract_id", "") or "").strip()
        contract = contracts.get(contract_id, {})
        failed_contracts.append(
            {
                key: _bounded_observation_value(value)
                for key, value in {
                    "contract_id": contract_id,
                    "requirement_id": row.get("requirement_id", ""),
                    "metric_path": row.get("metric_path", []),
                    "metric_semantics": contract.get("metric_semantics", ""),
                    "measurement_protocol": contract.get(
                        "measurement_protocol", ""
                    ),
                    "operator": row.get("operator", contract.get("operator", "")),
                    "aggregation": row.get(
                        "aggregation", contract.get("aggregation", "")
                    ),
                    "threshold": contract.get("threshold"),
                    "lower": contract.get("lower"),
                    "upper": contract.get("upper"),
                    "tolerance": contract.get("tolerance"),
                    "observed": row.get("resolved_values_preview", []),
                    "aggregate_value": row.get("aggregate_value"),
                    "errors": row.get("errors", []),
                }.items()
                if value not in (None, "", [], {})
            }
        )
    direct_field_names = [
        "execution_attempted",
        "execution_smoke_passed",
        "returncode",
        "runtime_errors",
        "safety_errors",
        "estimator_binding_errors",
        "estimator_runtime_failure_ids",
        "estimator_runtime_errors",
        "result_parse_error",
        "stderr_summary",
        "required_estimator_ids",
        "available_upstream_estimator_ids",
        "estimator_invocation_counts",
        "mechanical_estimator_invocation_verified",
        "script_hash",
    ]
    if include_empirical_outcomes:
        direct_field_names.extend(
            (
                "prototype_status",
                "smoke_passed",
                "stdout_summary",
                "metric_gate_errors",
                "result_hash",
            )
        )
    if (
        prototype.get("mechanical_estimator_invocation_verified") is not True
        or prototype.get("estimator_binding_errors")
        or prototype.get("estimator_runtime_errors")
    ):
        direct_field_names.append("estimator_invocation_samples")
    direct_fields = {
        key: deepcopy(prototype[key])
        for key in direct_field_names
        if prototype.get(key) not in (None, "", [], {})
    }
    if not include_empirical_outcomes and "estimator_invocation_samples" in direct_fields:
        direct_fields["estimator_invocation_samples"] = {
            str(artifact_id): [
                {
                    **{
                        "request_shape": _outcome_blind_request_shape(
                            row["request_shape"]
                        )
                    },
                    **{
                        key: deepcopy(row[key])
                        for key in ("response_status", "error_type")
                        if key in row
                    },
                }
                for row in rows
                if isinstance(row, Mapping) and row.get("request_shape")
            ]
            for artifact_id, rows in direct_fields["estimator_invocation_samples"].items()
            if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes))
        }
    return {
        "artifact_kind": "ScientificSandboxWorkspaceObservation",
        **{
            key: _bounded_observation_value(value)
            for key, value in direct_fields.items()
        },
        **(
            {
                "failed_metric_contracts": failed_contracts,
                "metrics_preview": _bounded_observation_value(
                    prototype.get("metrics", {})
                ),
            }
            if include_empirical_outcomes
            else {
                "empirical_outcomes_withheld": True,
                "empirical_outcome_authority": "EmpiricalEvaluator",
                **(
                    {
                        "measurement_interface_failures": (
                            measurement_interface_failures
                        )
                    }
                    if measurement_interface_failures
                    else {}
                ),
            }
        ),
        "full_execution_artifact_persisted": True,
        "source_replayed_to_model": False,
        "proof_evidence_status": "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE",
    }


def scientific_workspace_measurement_interface_failures(
    prototype: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return outcome-blind failures in the generated metric output ABI."""

    evaluation = prototype.get("metric_contract_evaluation", {})
    rows = (
        evaluation.get("evaluations", [])
        if isinstance(evaluation, Mapping)
        else []
    )
    failures: list[dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, Mapping):
            continue
        if row.get("measurement_interface_valid") is not False:
            continue
        failures.append(
            {
                key: deepcopy(value)
                for key, value in {
                    "contract_id": row.get("contract_id", ""),
                    "requirement_id": row.get("requirement_id", ""),
                    "metric_path": row.get("metric_path", []),
                    "measurement_interface_status": row.get(
                        "measurement_interface_status", "INVALID"
                    ),
                    "measurement_interface_errors": row.get(
                        "measurement_interface_errors", []
                    ),
                }.items()
                if value not in (None, "", [], {})
            }
        )
    return failures


def complete_scientific_source_draft(
    row: Mapping[str, Any],
    *,
    include_estimator_selection: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Recover one exact model-authored draft from persisted execution evidence."""

    source = str(row.get("source_code", "") or "")
    script_hash = str(row.get("script_hash", "") or "").strip()
    errors: list[str] = []
    if not source:
        errors.append("executed scientific source is missing")
    if not script_hash or (source and script_hash != stable_hash(source)):
        errors.append("executed scientific source hash mismatch")
    dependencies = row.get("dependencies", [])
    if not isinstance(dependencies, list):
        errors.append("executed scientific dependencies are not an array")
        dependencies = []
    draft = {
        "language": str(row.get("language", "") or ""),
        "execution_profile": str(
            row.get("requested_execution_profile", "")
            or row.get("executor_profile", "")
            or ""
        ),
        "dependencies": deepcopy(dependencies),
        "entrypoint": "run_sandbox",
        "code": source,
    }
    if include_estimator_selection:
        required_estimator_ids = row.get("required_estimator_ids", [])
        if not isinstance(required_estimator_ids, list):
            errors.append("consumer estimator selection is not an array")
        else:
            draft["required_estimator_ids"] = deepcopy(required_estimator_ids)
    if not errors:
        errors.extend(generated_code_execution_contract_errors(draft))
    return draft, sorted(set(errors))


def scientific_consumer_replay_drafts(
    manifest: Mapping[str, Any],
    *,
    question_id: str,
    theory_packet_id: str,
) -> tuple[str, list[dict[str, Any]], list[str]]:
    """Recover exact consumer source from one bound execution manifest."""

    errors: list[str] = []
    question = manifest.get("question", {})
    if (
        manifest.get("artifact_kind") != "RuntimeSimulationManifest"
        or not str(manifest.get("manifest_id", "") or "").strip()
        or str(manifest.get("theory_packet_id", "") or "") != theory_packet_id
        or not isinstance(question, Mapping)
        or str(question.get("id", "") or "") != question_id
    ):
        errors.append("consumer resume manifest lineage is invalid")
    proposal_id = str(
        manifest.get("llm_simulation_engineer_proposal_id", "") or ""
    ).strip()
    if not proposal_id:
        errors.append("consumer resume proposal identity is missing")
    drafts: list[dict[str, Any]] = []
    for raw_row in manifest.get(
        "generated_simulation_sandbox_prototypes", []
    ) or []:
        if not isinstance(raw_row, Mapping):
            continue
        draft, draft_errors = complete_scientific_source_draft(
            raw_row,
            include_estimator_selection=True,
        )
        simulation_id = str(raw_row.get("simulation_id", "") or "").strip()
        if not simulation_id:
            draft_errors.append("consumer resume simulation id is missing")
        errors.extend(
            f"{simulation_id or 'unknown consumer'}: {error}"
            for error in draft_errors
        )
        if not draft_errors:
            drafts.append({"simulation_id": simulation_id, **draft})
    if not drafts:
        errors.append("consumer resume has no exact executable source")
    return proposal_id, drafts, sorted(set(errors))


def scientific_consumer_revision_sources(
    manifest: Mapping[str, Any],
    *,
    dependency_context: Mapping[str, Any],
    revision_artifact_ids: Sequence[str],
    implementation_artifact_ids: Sequence[str],
    theory_packet_id: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Validate exact source rows selected by a downstream observation."""

    revision_ids = sorted(set(revision_artifact_ids))
    errors: list[str] = []
    if (
        not revision_ids
        or str(dependency_context.get("source_owner_subsystem", "") or "")
        != "AlgorithmEngineer"
        or list(dependency_context.get("dependency_artifact_ids", []) or [])
        != revision_ids
        or manifest.get("artifact_kind") != "RuntimeAlgorithmSandboxManifest"
        or str(manifest.get("manifest_id", "") or "")
        != str(dependency_context.get("source_manifest_id", "") or "")
        or stable_hash(manifest)
        != str(dependency_context.get("source_manifest_hash", "") or "")
        or str(manifest.get("theory_packet_id", "") or "") != theory_packet_id
    ):
        errors.append("algorithm consumer source lineage is incomplete or stale")
    rows = {
        str(row.get("estimator_id", "") or "").strip(): dict(row)
        for row in manifest.get("prototypes", []) or []
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", "") or "").strip()
    }
    expected_hashes = dependency_context.get("dependency_artifact_hashes", {})
    expected_hashes = (
        dict(expected_hashes) if isinstance(expected_hashes, Mapping) else {}
    )
    implementation_ids = set(implementation_artifact_ids)
    for artifact_id in revision_ids:
        row = rows.get(artifact_id, {})
        _, source_errors = (
            complete_scientific_source_draft(row)
            if row
            else ({}, ["executed scientific source is missing"])
        )
        if (
            artifact_id not in implementation_ids
            or row.get("smoke_passed") is not True
            or str(row.get("script_hash", "") or "")
            != str(expected_hashes.get(artifact_id, "") or "")
            or source_errors
        ):
            errors.append(
                f"consumer source artifact is unavailable or stale: {artifact_id}"
            )
    return rows, sorted(set(errors))


def scientific_consumer_dependency_context(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Bind raw consumer failures to their exact source-owned dependencies."""

    owners: list[dict[str, Any]] = []
    consumer_sources: list[dict[str, str]] = []
    observations_by_artifact: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    for raw_row in rows:
        if not isinstance(raw_row, Mapping):
            continue
        owner = raw_row.get("source_owner", {})
        if not isinstance(owner, Mapping) or not owner:
            continue
        owner_row = deepcopy(dict(owner))
        if str(owner_row.get("owner_subsystem", "") or "") != (
            "AlgorithmEngineer"
        ):
            errors.append("consumer dependency source owner is not AlgorithmEngineer")
            continue
        artifact_ids = owner_row.get("artifact_ids", [])
        artifact_hashes = owner_row.get("artifact_hashes", {})
        if (
            not isinstance(artifact_ids, list)
            or not artifact_ids
            or not isinstance(artifact_hashes, Mapping)
        ):
            errors.append("consumer dependency source identity is incomplete")
            continue
        normalized_ids = sorted(
            {
                str(value or "").strip()
                for value in artifact_ids
                if str(value or "").strip()
            }
        )
        if not normalized_ids or any(
            not str(artifact_hashes.get(artifact_id, "") or "").strip()
            for artifact_id in normalized_ids
        ):
            errors.append("consumer dependency artifact hash is missing")
            continue
        simulation_id = str(raw_row.get("simulation_id", "") or "").strip()
        script_hash = str(raw_row.get("script_hash", "") or "").strip()
        if not simulation_id or not script_hash:
            errors.append("failed consumer source identity is incomplete")
            continue
        consumer_sources.append(
            {
                "artifact_id": simulation_id,
                "source_hash": script_hash,
                "evaluation_contract_hash": stable_hash(
                    {
                        "metric_contracts": raw_row.get("metric_contracts", []),
                        "required_estimator_ids": raw_row.get(
                            "required_estimator_ids", []
                        ),
                    }
                ),
            }
        )
        observation = {
            "consumer_artifact_id": simulation_id,
            "consumer_source_hash": script_hash,
            "observation": scientific_workspace_prototype_observation(raw_row),
        }
        for artifact_id in normalized_ids:
            observations_by_artifact.setdefault(artifact_id, []).append(
                deepcopy(observation)
            )
        owners.append(owner_row)
    if not owners:
        errors.append("no exact dependency source owner was recorded")
        return {}, sorted(set(errors))

    source_manifest_ids = {
        str(row.get("source_manifest_id", "") or "").strip() for row in owners
    }
    source_manifest_hashes = {
        str(row.get("source_manifest_hash", "") or "").strip() for row in owners
    }
    if "" in source_manifest_ids or len(source_manifest_ids) != 1:
        errors.append("consumer dependency spans ambiguous source manifests")
    if "" in source_manifest_hashes or len(source_manifest_hashes) != 1:
        errors.append("consumer dependency source manifest hash is ambiguous")
    merged_hashes: dict[str, str] = {}
    for owner in owners:
        for artifact_id in owner.get("artifact_ids", []) or []:
            normalized_id = str(artifact_id or "").strip()
            content_hash = str(
                (owner.get("artifact_hashes", {}) or {}).get(normalized_id, "")
                or ""
            ).strip()
            prior_hash = merged_hashes.get(normalized_id)
            if prior_hash and prior_hash != content_hash:
                errors.append(
                    f"consumer dependency artifact hash conflicts: {normalized_id}"
                )
            elif normalized_id and content_hash:
                merged_hashes[normalized_id] = content_hash
    context = {
        "source_owner_subsystem": "AlgorithmEngineer",
        "source_manifest_id": next(iter(source_manifest_ids), ""),
        "source_manifest_hash": next(iter(source_manifest_hashes), ""),
        "dependency_artifact_ids": sorted(merged_hashes),
        "dependency_artifact_hashes": dict(sorted(merged_hashes.items())),
        "consumer_source_artifacts": sorted(
            consumer_sources,
            key=lambda row: (row["artifact_id"], row["source_hash"]),
        ),
        "consumer_observations_by_dependency": observations_by_artifact,
    }
    return context, sorted(set(errors))


def advance_scientific_consumer_revision_budget(
    *,
    task_budget: Mapping[str, Any],
    question_id: str,
    theory_packet_id: str,
    dependency_context: Mapping[str, Any],
    failure_classification: str,
    max_revisions: int,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Advance one bounded source-owner loop across outer runtime handoffs."""

    budget = deepcopy(dict(task_budget))
    prior_value = budget.get(SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY, {})
    prior = dict(prior_value) if isinstance(prior_value, Mapping) else {}
    lineage_identity = {
        "question_id": question_id,
        "theory_packet_id": theory_packet_id,
        "consumer_owner_subsystem": "SimulationEvaluator",
        "dependency_owner_subsystem": "AlgorithmEngineer",
        "consumer_contracts": [
            {
                "artifact_id": artifact_id,
                "evaluation_contract_hash": contract_hash,
            }
            for artifact_id, contract_hash in sorted(
                {
                    (
                        str(row.get("artifact_id", "") or ""),
                        str(row.get("evaluation_contract_hash", "") or ""),
                    )
                    for row in dependency_context.get(
                        "consumer_source_artifacts", []
                    )
                    or []
                    if isinstance(row, Mapping)
                }
            )
        ],
    }
    lineage_id = "scientific_consumer_lineage:" + stable_hash(lineage_identity)[:20]
    errors: list[str] = []
    prior_lineage_id = str(prior.get("lineage_id", "") or "")
    if prior_lineage_id and prior_lineage_id != lineage_id:
        errors.append("scientific consumer continuation changed source lineage")
    try:
        revisions_used = max(0, int(prior.get("revisions_used", 0) or 0))
        frozen_max_revisions = (
            max(0, int(prior.get("max_revisions", 0) or 0))
            if prior
            else max(0, int(max_revisions or 0))
        )
    except (TypeError, ValueError):
        errors.append("scientific consumer revision budget is malformed")
        revisions_used = 0
        frozen_max_revisions = 0
    revision_available = not errors and revisions_used < frozen_max_revisions
    failure_fingerprint = stable_hash(
        {
            "failure_classification": failure_classification,
            "dependency_artifact_hashes": dependency_context.get(
                "dependency_artifact_hashes", {}
            ),
            "consumer_observations": dependency_context.get(
                "consumer_observations_by_dependency", {}
            ),
        }
    )
    prior_fingerprints = [
        str(value)
        for value in prior.get("failure_fingerprints", []) or []
        if str(value)
    ]
    row = {
        "lineage_id": lineage_id,
        "revisions_used": revisions_used + (1 if revision_available else 0),
        "max_revisions": frozen_max_revisions,
        "revision_scheduled": revision_available,
        "budget_exhausted": not revision_available,
        "failure_fingerprints": (prior_fingerprints + [failure_fingerprint])[-8:],
    }
    budget[SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY] = row
    return budget, row, sorted(set(errors))


def _bounded_observation_value(value: Any, *, depth: int = 0) -> Any:
    if depth >= 8:
        return {"preview": "depth_limit", "type": type(value).__name__}
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value if len(value) <= 2_000 else value[:2_000] + "..."
    if isinstance(value, Mapping):
        items = list(value.items())
        preview = {
            str(key): _bounded_observation_value(child, depth=depth + 1)
            for key, child in items[:24]
        }
        if len(items) > 24:
            preview["truncated_key_count"] = len(items) - 24
        return preview
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        rows = list(value)
        if len(rows) <= 12:
            return [
                _bounded_observation_value(row, depth=depth + 1) for row in rows
            ]
        return {
            "preview": "sequence",
            "length": len(rows),
            "head": [
                _bounded_observation_value(row, depth=depth + 1)
                for row in rows[:8]
            ],
            "tail": [
                _bounded_observation_value(row, depth=depth + 1)
                for row in rows[-2:]
            ],
        }
    return str(value)[:2_000]


def run_scientific_code_workspace(
    *,
    provider: Any,
    system_prompt: str,
    user_prompt: str,
    model: str,
    model_tier: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    max_no_progress_turns: int,
    artifact_id: str,
    initial_code_draft: Mapping[str, Any] | None,
    initial_check_result: Mapping[str, Any],
    check_candidate: ScientificCodeCheck,
    workspace_operation: str = "targeted_revision",
    request_metadata: Mapping[str, Any] | None = None,
) -> ScientificCodeWorkspaceResult:
    """Let one model own complete scientific source across raw sandbox feedback."""

    if not str(artifact_id).strip():
        raise ValueError("scientific code workspace requires a bound artifact id")
    for value, label in (
        (max_turns, "turn"),
        (max_no_progress_turns, "no-progress"),
    ):
        if value < 1:
            raise ValueError(f"scientific code workspace {label} budget must be positive")
    if workspace_operation not in {"initial_authoring", "targeted_revision"}:
        raise ValueError("unsupported scientific code workspace operation")

    parent_draft = (
        _complete_code_draft(initial_code_draft)
        if isinstance(initial_code_draft, Mapping) and initial_code_draft
        else {}
    )
    if workspace_operation == "targeted_revision" and not parent_draft:
        raise ValueError("targeted scientific source revision requires parent source")
    parent_hash = stable_hash(parent_draft) if parent_draft else ""
    state: dict[str, Any] = {
        "code_draft": parent_draft,
        "code_draft_hash": parent_hash,
        "source_updates": 0,
        "checks": 0,
        "last_check": deepcopy(dict(initial_check_result)),
    }
    tools = _scientific_code_tools()

    def execute_tool(call, context):
        del context
        tool_input = dict(call.input)
        if call.name == SCIENTIFIC_SOURCE_SUBMISSION_TOOL:
            required_fields = {
                "language",
                "execution_profile",
                "dependencies",
                "entrypoint",
                "code",
            }
            if (
                not required_fields.issubset(tool_input)
                or set(tool_input) - required_fields
            ):
                raise ClientToolInputError(
                    "submit_scientific_source requires the complete language, "
                    "execution_profile, dependencies, entrypoint, and code candidate"
                )
            draft = _complete_code_draft(tool_input)
            draft_hash = stable_hash(draft)
            changed = draft_hash != state["code_draft_hash"]
            if not changed:
                raise ClientToolInputError(
                    "replacement is byte-identical to the current scientific source; "
                    "the deterministic observation is already recorded, so submit a "
                    "changed complete candidate"
                )
            state["code_draft"] = draft
            state["code_draft_hash"] = draft_hash
            state["source_updates"] += 1
            raw = check_candidate(deepcopy(dict(state["code_draft"])))
            if not isinstance(raw, Mapping):
                raise ClientToolInputError("scientific sandbox returned a non-object result")
            check = deepcopy(dict(raw))
            observed_hash = str(check.get("code_draft_hash", "") or "")
            if observed_hash != state["code_draft_hash"]:
                raise ClientToolInputError(
                    "scientific sandbox result is not bound to the current candidate hash"
                )
            state["checks"] += 1
            state["last_check"] = check
            accepted = check.get("accepted") is True
            disposition = str(
                check.get("source_iteration_disposition", "") or ""
            ).strip()
            if not disposition:
                disposition = (
                    "accepted" if accepted else SCIENTIFIC_SOURCE_REVISE_CURRENT
                )
                check["source_iteration_disposition"] = disposition
            if disposition not in {
                "accepted",
                SCIENTIFIC_SOURCE_REVISE_CURRENT,
                SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER,
            }:
                raise ClientToolInputError(
                    "scientific sandbox returned an unsupported source iteration "
                    "disposition"
                )
            if accepted != (disposition == "accepted"):
                raise ClientToolInputError(
                    "scientific sandbox acceptance and source iteration disposition "
                    "disagree"
                )
            terminal = bool(
                accepted
                or disposition == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
            )
            if disposition == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER:
                source_owner = check.get("source_owner", {})
                if not (
                    isinstance(source_owner, Mapping)
                    and str(source_owner.get("owner_subsystem", "") or "").strip()
                    and str(source_owner.get("source_manifest_id", "") or "").strip()
                    and str(source_owner.get("source_manifest_hash", "") or "").strip()
                    and isinstance(source_owner.get("artifact_ids"), Sequence)
                    and not isinstance(source_owner.get("artifact_ids"), (str, bytes))
                    and source_owner.get("artifact_ids")
                    and isinstance(source_owner.get("artifact_hashes"), Mapping)
                    and all(
                        str(
                            source_owner["artifact_hashes"].get(artifact_id, "")
                            or ""
                        ).strip()
                        for artifact_id in source_owner["artifact_ids"]
                    )
                ):
                    raise ClientToolInputError(
                        "dependency-owner disposition requires bound source owner refs"
                    )
            return ClientToolExecutionResult(
                content={
                    **check,
                    "ok": accepted,
                    "changed": True,
                    "checks": state["checks"],
                    "source_updates": state["source_updates"],
                    "execution_evidence_status": (
                        "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE"
                    ),
                },
                is_error=not accepted,
                state_changed=True,
                terminal=terminal,
                terminal_payload=(
                    {
                        "code_draft": deepcopy(dict(state["code_draft"])),
                        "code_draft_hash": state["code_draft_hash"],
                        "check_result": check,
                    }
                    if terminal
                    else None
                ),
                observation_key="scientific-submission:"
                + stable_hash(
                    {
                        "code_draft_hash": state["code_draft_hash"],
                        "check": check,
                    }
                ),
            )

        raise ClientToolInputError("unsupported scientific code workspace tool")

    request = ClientToolTurnRequest(
        system_prompt=system_prompt,
        messages=(
            {
                "role": "user",
                "content": (
                    user_prompt
                    + "\n\nThis workspace has at most "
                    + str(max_turns)
                    + " total model/tool turns. Retain the observed source hashes, "
                    "sandbox results, and attempted changes across those turns. Do "
                    "not resubmit a previously observed byte-identical candidate."
                )
                + (
                    "\n\nNo scientific source exists yet. Author the complete "
                    "candidate with submit_scientific_source. Each submission is "
                    "executed immediately without runtime source edits."
                    if not parent_draft
                    else "\n\nCurrent complete code candidate:\n"
                    + _compact_json(parent_draft)
                )
                + "\n\nInitial workspace observation:\n"
                + _compact_json(initial_check_result)
                + (
                    "\n\nThe current candidate failed. Diagnose that exact observation, "
                    "then submit a changed complete candidate. Every submission executes "
                    "immediately; identical bytes are not a new attempt."
                    if initial_check_result.get("accepted") is not True
                    and parent_draft
                    else ""
                ),
            },
        ),
        tools=tools,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tool_choice="any",
        disable_parallel_tool_use=True,
        enable_prompt_caching=True,
        metadata={
            **dict(request_metadata or {}),
            "model_tier": model_tier,
            "artifact_id": artifact_id,
            "parent_code_draft_hash": parent_hash,
            "workspace_operation": workspace_operation,
        },
    )

    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max_turns,
            max_no_progress_turns=max_no_progress_turns,
        )
    except ClientToolLoopError as exc:
        raise PacketValidationError(
            validation_label="LLM scientific code workspace",
            attempts=exc.turns,
            errors=[exc.reason],
            history=[deepcopy(dict(row)) for row in exc.history],
            recovery_checkpoint={
                "schema_version": 1,
                "artifact_kind": "ScientificCodeWorkspaceCheckpoint",
                "artifact_id": artifact_id,
                "workspace_operation": workspace_operation,
                "parent_code_draft_hash": parent_hash,
                "current_code_draft_hash": state["code_draft_hash"],
                "current_code_draft": deepcopy(dict(state["code_draft"])),
                "source_updates": state["source_updates"],
                "checks": state["checks"],
                "last_check": deepcopy(dict(state["last_check"])),
                "model_owned_source": True,
                "runtime_edited_source": False,
            },
        ) from exc

    terminal = dict(loop.terminal_payload)
    draft = _complete_code_draft(terminal.get("code_draft", {}))
    check = dict(terminal.get("check_result", {}))
    draft_hash = stable_hash(draft)
    disposition = str(
        check.get("source_iteration_disposition", "") or ""
    ).strip()
    if (
        terminal.get("code_draft_hash") != draft_hash
        or check.get("code_draft_hash") != draft_hash
        or disposition
        not in {"accepted", SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER}
        or (check.get("accepted") is True) != (disposition == "accepted")
    ):
        raise PacketValidationError(
            validation_label="LLM scientific code workspace",
            attempts=loop.turns,
            errors=[
                "terminal payload is not bound to an accepted candidate or exact "
                "dependency source owner"
            ],
            history=[deepcopy(dict(row)) for row in loop.history],
        )

    evidence = {
        "schema_version": 1,
        "artifact_kind": "ScientificCodeWorkspaceResult",
        "artifact_id": artifact_id,
        "transport": "native_client_tools",
        "workspace_operation": workspace_operation,
        "parent_code_draft_hash": parent_hash,
        "initial_check_result_hash": stable_hash(dict(initial_check_result)),
        "initial_check_accepted": initial_check_result.get("accepted") is True,
        "submitted_code_draft_hash": draft_hash,
        "terminal_check_result_hash": stable_hash(check),
        "source_changed": draft_hash != parent_hash,
        "source_updates": state["source_updates"],
        "sandbox_checks": state["checks"],
        "submit_and_execute_atomic": True,
        "transcript_policy": "full_linear_history",
        "turns": loop.turns,
        "tool_calls": loop.tool_calls,
        "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
        "provider": loop.provider,
        "model": loop.model,
        "model_tier": model_tier,
        "provider_usage": dict(loop.provider_usage),
        "history": [deepcopy(dict(row)) for row in loop.history],
        "transcript_fingerprint": loop.transcript_fingerprint,
        "model_owned_source": True,
        "runtime_edited_source": False,
        "accepted": check.get("accepted") is True,
        "source_iteration_disposition": disposition,
        "source_owner": deepcopy(dict(check.get("source_owner", {})))
        if isinstance(check.get("source_owner", {}), Mapping)
        else {},
        "proof_evidence_status": "SCIENTIFIC_CODE_EXECUTION_NOT_PROOF_EVIDENCE",
    }
    return ScientificCodeWorkspaceResult(
        code_draft=draft,
        check_result=check,
        evidence=evidence,
    )


def _complete_code_draft(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ClientToolInputError("scientific code candidate must be an object")
    language = normalized_generated_code_language(value.get("language"))
    execution_profile = normalized_generated_code_profile(
        value.get("execution_profile"),
        language=language,
    )
    entrypoint = str(value.get("entrypoint", "") or "").strip()
    code = str(value.get("code", "") or "")
    dependencies = value.get("dependencies", [])
    if not isinstance(dependencies, Sequence) or isinstance(
        dependencies, (str, bytes)
    ):
        raise ClientToolInputError("dependencies must be an array")
    normalized_dependencies = list(
        normalized_scientific_dependencies(dependencies, language=language)
    )
    draft = {
        "language": language,
        "execution_profile": execution_profile,
        "dependencies": normalized_dependencies,
        "entrypoint": entrypoint,
        "code": code,
    }
    contract_errors = generated_code_execution_contract_errors(draft)
    if contract_errors:
        raise ClientToolInputError("; ".join(contract_errors))
    return draft


def _scientific_code_tools() -> tuple[ClientToolDefinition, ...]:
    return (
        ClientToolDefinition(
            name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
            description=(
                "Submit one complete Python or R candidate. The runtime stores and "
                "immediately executes the exact source, then returns the raw sandbox "
                "observation to this same model."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "language",
                    "execution_profile",
                    "dependencies",
                    "entrypoint",
                    "code",
                ],
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": list(SCIENTIFIC_SANDBOX_LANGUAGES),
                    },
                    "execution_profile": {
                        "type": "string",
                        "enum": list(SCIENTIFIC_SANDBOX_PROFILES),
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(_SCIENTIFIC_PACKAGES),
                        },
                        "uniqueItems": True,
                    },
                    "entrypoint": {
                        "type": "string",
                        "enum": ["run_sandbox"],
                    },
                    "code": {"type": "string"},
                },
            },
            terminal=True,
        ),
    )


def _compact_json(value: Any, *, max_chars: int = 30_000) -> str:
    encoded = json.dumps(value, separators=(",", ":"), default=str)
    if len(encoded) <= max_chars:
        return encoded
    marker = "\n[observation middle truncated]\n"
    available = max_chars - len(marker)
    head = available // 2
    return encoded[:head] + marker + encoded[-(available - head) :]

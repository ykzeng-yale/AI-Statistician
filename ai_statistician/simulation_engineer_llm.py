from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .fingerprint import stable_hash
from .generated_metric_contract import (
    GENERATED_METRIC_CONTRACT_BOUNDARY,
    GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED,
    GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED,
    GENERATED_METRIC_SOURCE_ACCEPTANCE_MODE,
    GENERATED_METRIC_SOURCE_ACCEPTANCE_PATH,
    generated_metric_contract_set_id,
    generated_metric_requirement_authority_policy_from_context,
    generated_metric_requirement_set_id,
    generated_metric_requirements_from_context,
    materialize_generated_metric_contract_bindings,
    validate_generated_metric_contracts,
)
from .model_backend import GeneratorBackend, resolve_generator_model
from .research_schema import OpenResearchQuestion, research_question_payload
from .scientific_code_workspace import (
    SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS,
    ScientificCodeWorkspaceAgent,
    ScientificSourceWorkspaceUnavailableError,
)
from .theory_derivation_trace import (
    theory_trace_alignment_contract,
    theory_trace_consumption_contract,
)


SIMULATION_SOURCE_WORKSPACE_INTENT_SCHEMA_VERSION = 1
EMPIRICAL_EVALUATION_PHASE_EXPLORATORY = "exploratory_diagnostic"
EMPIRICAL_EVALUATION_PHASE_EXECUTABLE_EVALUATOR_AUTHORING = (
    "executable_evaluator_authoring"
)
EMPIRICAL_EVALUATION_PHASE_CONFIRMATORY = "confirmatory_evaluator_execution"
SIMULATION_SOURCE_WORKSPACE_INTENT_NOT_EXECUTION_EVIDENCE = (
    "SIMULATION_SOURCE_WORKSPACE_INTENT_NOT_EXECUTION_EVIDENCE"
)
SIMULATION_ENGINEER_BOUNDARY = (
    "Simulation workspace intents contain runtime-owned target identity and "
    "authority references only. They are not model output, Monte Carlo execution, "
    "empirical validation, or proof evidence. Executable simulation evidence "
    "requires AgentRuntime to execute exact model-authored source with recorded "
    "seed and metrics."
)


def _uses_source_acceptance_program(
    requirements: list[Mapping[str, Any]],
) -> bool:
    return bool(
        requirements
        and all(
            str(row.get("evaluator_mode", "") or "")
            == GENERATED_METRIC_SOURCE_ACCEPTANCE_MODE
            for row in requirements
        )
    )


def _source_acceptance_metric_bindings(
    *,
    requirements: list[Mapping[str, Any]],
    simulation_ids: tuple[str, ...],
) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for simulation_id in simulation_ids:
        for requirement in requirements:
            requirement_id = str(
                requirement.get("requirement_id", "") or ""
            )
            binding_hash = stable_hash([requirement_id, simulation_id])[:20]
            bindings.append(
                {
                    "contract_id": f"source_acceptance_binding:{binding_hash}",
                    "requirement_id": requirement_id,
                    "artifact_id": simulation_id,
                    "metric_path": list(GENERATED_METRIC_SOURCE_ACCEPTANCE_PATH),
                }
            )
    return bindings


@dataclass(frozen=True)
class SimulationEngineerConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 8000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    use_client_tool_code_workspace: bool = True
    client_tool_code_max_turns: int = 48
    client_tool_code_max_no_progress_turns: int = 2


class LLMSimulationEngineerAgent(ScientificCodeWorkspaceAgent):
    """Retained Python/R source owner for simulation work."""

    @property
    def scientific_workspace_system_prompt(self) -> str:
        return SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT

    scientific_workspace_instruction = (
        "Continue the bound simulation workspace for this research task."
    )
    scientific_workspace_subsystem = "SimulationEvaluator"
    scientific_workspace_agent = "LLMSimulationEngineerAgent"
    scientific_workspace_allow_dependency_handoff = True

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: SimulationEngineerConfig = SimulationEngineerConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def create_source_workspace_intent(
        self,
        *,
        question: OpenResearchQuestion,
        theory_packet: Mapping[str, Any],
        n_runs: int,
        seed: int,
        withhold_seed_from_model: bool = False,
        environment_feedback: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create one deterministic target for the retained source workspace."""

        if not self.config.use_client_tool_code_workspace or not callable(
            getattr(self.provider, "generate_client_tool_turn", None)
        ):
            raise ScientificSourceWorkspaceUnavailableError(
                "SimulationEngineer requires one native client-tool source workspace"
            )
        feedback = environment_feedback or {}
        upstream_algorithm_handoff = _compact_upstream_algorithm_handoff(
            feedback.get("upstream_algorithm_handoff", {})
            or _mapping(feedback.get("architect_context", {})).get(
                "upstream_algorithm_handoff", {}
            )
        )
        upstream_estimator_ids = _upstream_algorithm_estimator_ids(
            upstream_algorithm_handoff
        )
        empirical_evaluation_phase = _feedback_empirical_evaluation_phase(feedback)
        executable_evaluator_source = _feedback_uses_executable_evaluator_source(
            feedback
        )
        authoritative_metric_requirements = (
            generated_metric_requirements_from_context(
                feedback,
                target_subsystem="SimulationEngineer",
            )
            if empirical_evaluation_phase
            != EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            else []
        )
        source_acceptance_program = bool(
            executable_evaluator_source
            or _uses_source_acceptance_program(
                authoritative_metric_requirements
            )
        )
        requires_typed_metric_contracts = bool(
            authoritative_metric_requirements
            and not source_acceptance_program
        )
        if requires_typed_metric_contracts:
            raise ScientificSourceWorkspaceUnavailableError(
                "SimulationEngineer metric paths must be owned by the retained "
                "executable evaluator source, not a structured planning packet"
            )
        metric_requirement_authority_policy = (
            GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED
            if empirical_evaluation_phase
            == EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            else generated_metric_requirement_authority_policy_from_context(feedback)
        )
        require_authoritative_requirements = bool(
            requires_typed_metric_contracts
            and metric_requirement_authority_policy
            == GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        provider_name = str(
            getattr(self.provider, "provider_name", self.config.provider_name)
            or self.config.provider_name
        ).lower()
        intent_hash = stable_hash(
            {
                "question_id": question.id,
                "theory_packet_id": theory_packet.get("packet_id", ""),
                "empirical_evaluation_phase": empirical_evaluation_phase,
                "upstream_estimator_ids": list(upstream_estimator_ids),
                "metric_requirement_set_id": generated_metric_requirement_set_id(
                    authoritative_metric_requirements
                ),
                "n_runs": n_runs,
            }
        )[:20]
        simulation_prefix = (
            "exploratory_simulation"
            if empirical_evaluation_phase
            == EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            else "confirmatory_simulation"
        )
        simulation_id = f"{simulation_prefix}:{intent_hash}"
        packet = _build_simulation_source_workspace_intent(
            {
                "simulation_targets": [{"procedure_id": simulation_id}],
                "simulation_code_drafts": [
                    {
                        "simulation_id": simulation_id,
                        "required_estimator_ids": list(upstream_estimator_ids),
                    }
                ],
                "source_workspace_planning_owned": True,
                "source_workspace_intent_id": (
                    "simulation_source_workspace_intent:" + intent_hash
                ),
                "planning_model_call_used": False,
            },
            question=question,
            model=request_model,
            model_tier=self.config.model_tier,
            provider_name=self.config.provider_name or provider_name,
            backend_provider_name=provider_name,
            theory_packet=theory_packet,
            n_runs=n_runs,
            seed=seed,
            seed_disclosed_to_model=not withhold_seed_from_model,
            authoritative_metric_requirements=authoritative_metric_requirements,
            metric_requirement_authority_policy=(
                metric_requirement_authority_policy
            ),
            empirical_evaluation_phase=empirical_evaluation_phase,
            upstream_algorithm_handoff=upstream_algorithm_handoff,
            executable_evaluator_source=executable_evaluator_source,
        )
        errors = validate_simulation_source_workspace_intent(packet)
        errors.extend(
            _validate_simulation_estimator_selection(
                packet,
                upstream_estimator_ids=upstream_estimator_ids,
            )
        )
        errors.extend(
            _validate_simulation_source_workspace_intent_metrics(
                packet,
                authoritative_metric_requirements=(
                    authoritative_metric_requirements
                ),
                require_authoritative_requirements=(
                    require_authoritative_requirements
                ),
                require_typed_metric_contracts=bool(
                    authoritative_metric_requirements
                ),
            )
        )
        if errors:
            raise ValueError("; ".join(sorted(set(errors))))
        return packet

SIMULATION_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT = """\
You are the SimulationEngineer source owner inside an AI Statistician workspace.
Own one complete executable Python or R simulation candidate. Use the supplied
client tools to replace and run the exact source. Read every raw sandbox and metric
observation and choose every source change yourself. The runtime executes source
unchanged and never supplies a correction rule. Do not answer with prose, delegate
an edit, weaken the frozen metric contract, or claim theorem-proof evidence. When
You also own the exploratory DGP and diagnostics; no separate planner authors them.
When workspace_context.theory_context.document_authoritative is true, read its exact
authoritative_theory_documents through the supplied read-only document tools;
structured theory fields, when present, carry only claim identity and executable ABI.
When source_replication_context is present, read its report through the same tools;
it is replication evidence, not mathematical or semantic authority. Treat every
metric_path segment as a literal,
punctuation-sensitive JSON key; compare run_sandbox nested keys with each frozen path
and never normalize or substitute a theory-prose name. An
unresolved measurement_interface_failure is a source ABI failure. When
evaluator_mode is simulation_source_acceptance_v1, implement the complete frozen
measurement_protocol in this source and return top-level acceptance_passed as a
boolean together with raw measurements and per-check diagnostics. Runtime checks
only that stable interface; it does not implement or repair the scientific decision.
When executable_evaluator_source_authority is true, exact source is the preregistration:
choose the DGP, measurements, decision, precision, and a future confirmatory
requested_runtime_replicates fixed independently of diagnostic outcomes as the top-level
run_sandbox result, not an input-validation name. During evaluator_source_authoring, the supplied replicates is a small non-confirmatory tool
diagnostic. Exercise the complete source and every required estimator; never reject or
return early merely because that diagnostic is small. acceptance_passed may be false
and still be a successful tool observation; never tune source to make it favorable.
Runtime validates only the result ABI and capacity. Independent review must accept exact
bytes before one confirmatory execution. When
required_estimator_ids are bound, the estimators argument contains runtime-injected
callbacks at those exact keys. Call every bound callback with its declared request
object and consume its declared response; never reimplement, wrap, or substitute a
bound estimator inside the simulation source. When execution exposes callback
request/response samples, compare the request's data scope, the declared meaning of
each response field, and the simulation's consumer control flow before changing the
complete source. The full question.estimator_execution_contract, when present, is the
frozen ABI; compact Theory or handoff summaries cannot weaken it. Do not infer lifecycle or
termination from field names or sampled values without checking that exact contract.
"""


def _feedback_empirical_evaluation_phase(feedback: Mapping[str, Any]) -> str:
    if not isinstance(feedback, Mapping):
        return ""
    direct = str(feedback.get("empirical_evaluation_phase", "") or "").strip()
    if direct:
        return direct
    for key in (
        "architect_evidence_contract",
        "runtime_requested_evidence_contract",
    ):
        contract = feedback.get(key, {})
        if not isinstance(contract, Mapping):
            continue
        phase = str(contract.get("empirical_evaluation_phase", "") or "").strip()
        if phase:
            return phase
    return ""


def _feedback_uses_executable_evaluator_source(
    feedback: Mapping[str, Any],
) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    context = _mapping(feedback.get("architect_context", {}))
    return bool(
        feedback.get("executable_evaluator_source_authority") is True
        or context.get("executable_evaluator_source_authority") is True
    )


def _first_mapping_rows(value: Any, *, limit: int) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value[:limit] if isinstance(row, Mapping)]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _compact_mapping(value: Any, *, limit: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    compact: dict[str, Any] = {}
    for index, (key, row_value) in enumerate(value.items()):
        if index >= limit:
            break
        compact[str(key)] = _truncate_text(row_value, limit=180)
    return compact


def _compact_upstream_algorithm_handoff(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    artifacts = [
        {
            "estimator_id": _truncate_text(
                row.get("estimator_id", ""), limit=180
            ),
            "language": _truncate_text(row.get("language", ""), limit=40),
            "dependencies": _compact_string_list(
                row.get("dependencies", []), limit=12, char_limit=80
            ),
            "exact_source_hash": _truncate_text(
                row.get("exact_source_hash", ""), limit=120
            ),
            "exact_project_hash": _truncate_text(
                row.get("exact_project_hash", ""), limit=120
            ),
            "project_files": [
                {
                    "path": _truncate_text(
                        project_file.get("path", ""), limit=240
                    ),
                    "content_sha256": _truncate_text(
                        project_file.get("content_sha256", ""), limit=120
                    ),
                }
                for project_file in row.get("exact_project_files", []) or []
                if isinstance(project_file, Mapping)
            ],
            "exact_smoke_result_hash": _truncate_text(
                row.get("exact_smoke_result_hash", ""), limit=120
            ),
            "estimator_interface_contract_id": _truncate_text(
                row.get("estimator_interface_contract_id", ""),
                limit=120,
            ),
            "estimator_interface_contract_authority": _compact_mapping(
                row.get("estimator_interface_contract_authority", {}), limit=8
            ),
            "estimator_interface_contract": (
                _compact_estimator_interface_contract(
                    row.get("estimator_interface_contract", {})
                )
            ),
        }
        for row in value.get("exact_algorithm_artifacts", []) or []
        if isinstance(row, Mapping)
    ]
    if not artifacts:
        return {}
    return {
        "source": _truncate_text(value.get("source", ""), limit=120),
        "algorithm_sandbox_manifest_id": _truncate_text(
            value.get("algorithm_sandbox_manifest_id", ""), limit=180
        ),
        "algorithm_sandbox_manifest_hash": _truncate_text(
            value.get("algorithm_sandbox_manifest_hash", ""), limit=120
        ),
        "semantic_review_execution_id": _truncate_text(
            value.get("semantic_review_execution_id", ""), limit=180
        ),
        "semantic_review_packet_id": _truncate_text(
            value.get("semantic_review_packet_id", ""), limit=180
        ),
        "semantic_review_packet_hash": _truncate_text(
            value.get("semantic_review_packet_hash", ""), limit=120
        ),
        "theory_packet_id": _truncate_text(
            value.get("theory_packet_id", ""), limit=180
        ),
        "exact_algorithm_artifacts": artifacts,
        "exact_source_included": False,
        "execution_results_included": False,
        "consumption_contract": _truncate_text(
            value.get("consumption_contract", ""), limit=480
        ),
        "proof_evidence_status": _truncate_text(
            value.get("proof_evidence_status", ""), limit=180
        ),
        "boundary": _truncate_text(value.get("boundary", ""), limit=360),
    }


def _compact_estimator_interface_contract(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {
        "request_fields": [
            {
                key: _truncate_text(row.get(key, ""), limit=220)
                for key in ("name", "meaning", "binding")
            }
            for row in _first_mapping_rows(
                value.get("request_fields", []),
                limit=16,
            )
        ],
        "response_fields": [
            {
                key: _truncate_text(row.get(key, ""), limit=220)
                for key in (
                    "name",
                    "meaning",
                    "normalization",
                    "derivation_ref",
                )
            }
            for row in _first_mapping_rows(
                value.get("response_fields", []),
                limit=16,
            )
        ],
    }


def _upstream_algorithm_estimator_ids(
    handoff: Mapping[str, Any],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            str(row.get("estimator_id", "") or "").strip()
            for row in handoff.get("exact_algorithm_artifacts", []) or []
            if isinstance(row, Mapping)
            and str(row.get("estimator_id", "") or "").strip()
        )
    )


def _compact_string_list(value: Any, *, limit: int, char_limit: int = 220) -> list[str]:
    if isinstance(value, str):
        rows = [value]
    elif isinstance(value, list):
        rows = value
    else:
        rows = []
    return [_truncate_text(row, limit=char_limit) for row in rows[:limit]]


def _truncate_text(value: Any, *, limit: int = 360) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)] + "...[truncated]"


def validate_simulation_source_workspace_intent(
    packet: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    source_workspace_planning_owned = bool(
        packet.get("source_workspace_planning_owned") is True
    )
    source_deferred = bool(
        packet.get("scientific_source_transport")
        == SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS
    )
    required_fields = ["simulation_targets", "runtime_execution_plan"]
    for field in required_fields:
        if packet.get(field) in (None, "", [], {}):
            errors.append(f"missing or empty field: {field}")
    if not source_workspace_planning_owned:
        errors.append("simulation planning must be owned by the retained source workspace")
    if not source_deferred:
        errors.append("simulation source must use native client-tool transport")
    if packet.get("planning_model_call_used") is not False:
        errors.append(
            "source-workspace planning cannot claim a separate planning model call"
        )
    if not str(packet.get("source_workspace_intent_id", "") or "").strip():
        errors.append("source-workspace planning requires a stable intent identity")
    if packet.get("simulation_evidence_status") != (
        SIMULATION_SOURCE_WORKSPACE_INTENT_NOT_EXECUTION_EVIDENCE
    ):
        errors.append("simulation_evidence_status must preserve intent-only boundary")
    if packet.get("simulations_executed") is not False:
        errors.append("simulation source intent cannot set simulations_executed=true")
    if packet.get("proof_evidence_status") != "NOT_PROOF_EVIDENCE":
        errors.append("simulation source intent cannot claim proof evidence")
    for row in packet.get("simulation_targets", []) or []:
        if not isinstance(row, Mapping):
            errors.append("simulation_targets entries must be objects")
            continue
        if not str(row.get("procedure_id", "")).strip():
            errors.append("simulation target missing procedure_id")
    for row in packet.get("simulation_code_drafts", []) or []:
        if not isinstance(row, Mapping):
            errors.append("simulation_code_drafts entries must be objects")
            continue
        if not str(row.get("simulation_id", "")).strip():
            errors.append("simulation_code_drafts entry missing simulation_id")
        unexpected = set(row) - {
            "simulation_id",
            "required_estimator_ids",
        }
        if unexpected:
            errors.append(
                "client-tool source descriptors may contain only simulation_id "
                "and required_estimator_ids"
            )
    metric_artifact_ids = {
        str(row.get("procedure_id", "") or "").strip()
        for row in packet.get("simulation_targets", []) or []
        if isinstance(row, Mapping)
        and str(row.get("procedure_id", "") or "").strip()
    }
    metric_artifact_ids.update(
        str(row.get("simulation_id", "") or "").strip()
        for row in packet.get("simulation_code_drafts", []) or []
        if isinstance(row, Mapping)
        and str(row.get("simulation_id", "") or "").strip()
    )
    metric_contracts = packet.get("metric_contracts", [])
    if metric_contracts not in (None, [], {}):
        errors.extend(
            validate_generated_metric_contracts(
                metric_contracts,
                expected_artifact_ids=tuple(sorted(metric_artifact_ids)),
            )
        )
    runtime_plan = packet.get("runtime_execution_plan", {})
    if not isinstance(runtime_plan, Mapping):
        errors.append("runtime_execution_plan must be an object")
    else:
        execution_owner = str(
            runtime_plan.get("execution_owner", "") or ""
        )
        if execution_owner != "scientific_code_workspace":
            errors.append(
                "runtime_execution_plan.execution_owner must be "
                "scientific_code_workspace"
            )
    return sorted(set(errors))


def _validate_simulation_estimator_selection(
    packet: Mapping[str, Any],
    *,
    upstream_estimator_ids: tuple[str, ...],
) -> list[str]:
    available = set(upstream_estimator_ids)
    errors: list[str] = []
    for row in packet.get("simulation_code_drafts", []) or []:
        if not isinstance(row, Mapping):
            continue
        simulation_id = str(row.get("simulation_id", "") or "<unnamed>")
        raw_selected = row.get("required_estimator_ids", [])
        selected = (
            [str(value).strip() for value in raw_selected if str(value).strip()]
            if isinstance(raw_selected, list)
            else []
        )
        if available and not selected:
            errors.append(
                f"simulation_code_drafts {simulation_id} must select at least one "
                "required_estimator_ids value from the accepted algorithm handoff"
            )
        unknown = sorted(set(selected) - available)
        if unknown:
            errors.append(
                f"simulation_code_drafts {simulation_id} selected unknown upstream "
                "estimator ids: " + ", ".join(unknown)
            )
        if not available and selected:
            errors.append(
                f"simulation_code_drafts {simulation_id} cannot select estimators "
                "without an accepted algorithm handoff"
            )
    return errors


def _validate_simulation_source_workspace_intent_metrics(
    packet: Mapping[str, Any],
    *,
    authoritative_metric_requirements: list[Mapping[str, Any]] | None = None,
    require_authoritative_requirements: bool = False,
    require_typed_metric_contracts: bool = True,
) -> list[str]:
    """Bind every required metric to a retained source-workspace target."""

    drafts = [
        row
        for row in packet.get("simulation_code_drafts", []) or []
        if isinstance(row, Mapping)
    ]
    errors: list[str] = []
    errors.extend(
        str(error)
        for error in packet.get("source_acceptance_binding_errors", []) or []
        if str(error).strip()
    )
    if not drafts:
        errors.append(
            "simulation source intent requires at least one source-workspace target"
        )
    draft_ids = {
        str(row.get("simulation_id", "") or "").strip()
        for row in drafts
        if str(row.get("simulation_id", "") or "").strip()
    }
    if require_typed_metric_contracts:
        errors.extend(
            validate_generated_metric_contracts(
                packet.get("metric_contracts", []),
                expected_artifact_ids=tuple(sorted(draft_ids)),
                required_artifact_ids=tuple(sorted(draft_ids)),
                authoritative_requirements=authoritative_metric_requirements,
                target_subsystem="SimulationEngineer",
                require_authoritative_requirements=(
                    require_authoritative_requirements
                ),
            )
        )
    elif packet.get("metric_contracts", []) not in (None, [], {}):
        errors.append(
            "exploratory diagnostic simulation must leave metric_contracts empty; "
            "only a fresh confirmatory run may bind frozen acceptance requirements"
        )
    return sorted(set(errors))


def _build_simulation_source_workspace_intent(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    model: str,
    model_tier: str,
    provider_name: str,
    backend_provider_name: str,
    theory_packet: Mapping[str, Any],
    n_runs: int,
    seed: int,
    seed_disclosed_to_model: bool = True,
    authoritative_metric_requirements: list[Mapping[str, Any]] | None = None,
    metric_requirement_authority_policy: str = "",
    empirical_evaluation_phase: str = "",
    upstream_algorithm_handoff: Mapping[str, Any] | None = None,
    executable_evaluator_source: bool = False,
) -> dict[str, Any]:
    body = dict(payload)
    raw_metric_contracts = body.get("metric_contracts", [])
    metric_contract_values = (
        raw_metric_contracts if isinstance(raw_metric_contracts, list) else []
    )
    metric_contract_rows = [
        dict(row)
        for row in metric_contract_values
        if isinstance(row, Mapping)
    ]
    authority_rows = [
        dict(row)
        for row in authoritative_metric_requirements or []
        if isinstance(row, Mapping)
    ]
    source_acceptance_program = bool(
        executable_evaluator_source
        or _uses_source_acceptance_program(authority_rows)
    )
    source_acceptance_binding_errors: list[str] = []
    if source_acceptance_program:
        if metric_contract_rows:
            source_acceptance_binding_errors.append(
                "source-acceptance mode requires model metric_contracts to remain "
                "empty; AgentRuntime owns the stable binding"
            )
        simulation_ids = tuple(
            str(row.get("simulation_id", "") or "").strip()
            for row in body.get("simulation_code_drafts", []) or []
            if isinstance(row, Mapping)
            and str(row.get("simulation_id", "") or "").strip()
        )
        metric_contract_rows = _source_acceptance_metric_bindings(
            requirements=authority_rows,
            simulation_ids=simulation_ids,
        )
    metric_contract_rows = materialize_generated_metric_contract_bindings(
        metric_contract_rows,
        authoritative_requirements=authority_rows,
        target_subsystem="SimulationEngineer",
    )
    body["metric_contracts"] = metric_contract_rows
    body["metric_binding_mode"] = (
        "runtime_bound_source_acceptance_abi"
        if source_acceptance_program
        else "model_bound_metric_path"
    )
    body["source_acceptance_binding_errors"] = (
        source_acceptance_binding_errors
    )
    body["executable_evaluator_source_authority"] = bool(
        executable_evaluator_source
    )
    body["metric_contract_set_id"] = generated_metric_contract_set_id(
        metric_contract_rows
    )
    body["empirical_metric_requirements"] = authority_rows
    body["metric_requirement_set_id"] = generated_metric_requirement_set_id(
        authority_rows
    )
    body["metric_requirement_authority_policy"] = (
        metric_requirement_authority_policy
    )
    body["empirical_evaluation_phase"] = empirical_evaluation_phase
    body["confirmatory_empirical_evidence_eligible"] = bool(
        empirical_evaluation_phase
        not in {
            EMPIRICAL_EVALUATION_PHASE_EXPLORATORY,
            EMPIRICAL_EVALUATION_PHASE_EXECUTABLE_EVALUATOR_AUTHORING,
        }
    )
    body["upstream_algorithm_handoff"] = dict(
        upstream_algorithm_handoff or {}
    )
    body["scientific_source_transport"] = (
        SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS
    )
    body["metric_contract_proof_evidence_status"] = (
        GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE
    )
    body["metric_contract_boundary"] = GENERATED_METRIC_CONTRACT_BOUNDARY
    runtime_plan = body.get("runtime_execution_plan", {})
    if not isinstance(runtime_plan, Mapping):
        runtime_plan = {}
    else:
        runtime_plan = dict(runtime_plan)
    runtime_plan["n_runs"] = n_runs
    runtime_plan["seed"] = seed
    runtime_plan["execution_owner"] = "scientific_code_workspace"
    runtime_plan["execution_interface"] = (
        "submit_execute_observe_then_model_commit"
    )
    runtime_plan["canonicalization_boundary"] = (
        "AgentRuntime records the isolated execution interface; the model owns "
        "the complete source and receives its raw observations."
    )
    body["runtime_execution_plan"] = runtime_plan
    body["candidate_model_seed_disclosure"] = (
        "DISCLOSED" if seed_disclosed_to_model else "WITHHELD"
    )
    body["simulation_evidence_status"] = (
        SIMULATION_SOURCE_WORKSPACE_INTENT_NOT_EXECUTION_EVIDENCE
    )
    body["simulation_evidence_boundary"] = SIMULATION_ENGINEER_BOUNDARY
    body["proof_evidence_status"] = "NOT_PROOF_EVIDENCE"
    body["simulations_executed"] = False
    body["theory_trace_consumption_contract"] = theory_trace_consumption_contract(
        theory_packet,
        consumer_subsystem="SimulationEngineer",
        max_rows=3,
        text_limit=240,
    )
    body["theory_trace_alignment_contract"] = theory_trace_alignment_contract(
        theory_packet,
        body.get("theory_trace_alignment", {}),
        consumer_subsystem="SimulationEngineer",
        max_rows=3,
        text_limit=240,
    )
    packet_id = stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "backend_provider": backend_provider_name,
            "model": model,
            "model_tier": model_tier,
            "body": body,
            "n_runs": n_runs,
            "seed": seed,
        }
    )[:24]
    return {
        "schema_version": SIMULATION_SOURCE_WORKSPACE_INTENT_SCHEMA_VERSION,
        "artifact_kind": "SimulationSourceWorkspaceIntent",
        "packet_id": f"simulation_source_workspace_intent_artifact:{packet_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMSimulationEngineerAgent",
        "provider": provider_name,
        "backend_provider": backend_provider_name,
        "model": model,
        "model_tier": model_tier,
        "question": research_question_payload(
            question,
            include_estimator_execution_contract=False,
        ),
        "runtime_budget": {"n_runs": n_runs, "seed": seed},
        **body,
    }

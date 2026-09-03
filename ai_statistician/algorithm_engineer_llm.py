from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .estimator_interface_contract import (
    estimator_interface_contract_errors as shared_estimator_interface_contract_errors,
    estimator_interface_contract_id,
    project_executable_estimator_interface_contract,
    theory_estimator_interface_contracts,
)
from .fingerprint import stable_hash
from .research_schema import OpenResearchQuestion
from .scientific_code_workspace import (
    SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS,
    ScientificCodeWorkspaceAgent,
)
from .theory_derivation_trace import (
    theory_trace_alignment_contract,
    theory_trace_consumption_contract,
)


ALGORITHM_SOURCE_WORKSPACE_SCHEMA_VERSION = 3
ALGORITHM_SOURCE_WORKSPACE_RECORD_NOT_EXECUTION_EVIDENCE = (
    "ALGORITHM_SOURCE_WORKSPACE_RECORD_NOT_EXECUTION_EVIDENCE"
)
ALGORITHM_SOURCE_WORKSPACE_RECORD_BOUNDARY = (
    "This record binds accepted model-owned source workspaces to immutable estimator "
    "interfaces for independent review. It is not a separate model proposal, does not "
    "execute source, does not register a production algorithm, and is not proof evidence."
)


@dataclass(frozen=True)
class AlgorithmEngineerConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 5000
    temperature: float = 0.1
    provider_name: str = "anthropic"
    use_client_tool_code_workspace: bool = True
    client_tool_code_max_turns: int = 48
    client_tool_code_max_no_progress_turns: int = 2


class LLMAlgorithmEngineerAgent(ScientificCodeWorkspaceAgent):
    """Retained model/tool source owner for one Python or R estimator."""

    @property
    def scientific_workspace_system_prompt(self) -> str:
        return ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT

    scientific_workspace_instruction = (
        "Continue the bound implementation workspace for this research task."
    )
    scientific_workspace_subsystem = "AlgorithmEngineer"
    scientific_workspace_agent = "LLMAlgorithmEngineerAgent"

    def __init__(
        self,
        *,
        provider: Any,
        config: AlgorithmEngineerConfig = AlgorithmEngineerConfig(),
    ) -> None:
        self.provider = provider
        self.config = config

    def source_workspace_owns_planning(self) -> bool:
        """Return whether one retained source session can plan, edit, and execute."""

        return bool(
            self.config.use_client_tool_code_workspace
            and callable(getattr(self.provider, "generate_client_tool_turn", None))
        )


ALGORITHM_ENGINEER_CODE_WORKSPACE_SYSTEM_PROMPT = """\
You are the AlgorithmEngineer source owner inside an AI Statistician workspace.
Own one complete executable Python or R estimator candidate. Use the supplied
client tools to inspect the exact objective and immutable bindings, edit source,
run the current bytes, and inspect raw sandbox observations. Choose every source
change yourself. The runtime executes source unchanged and never supplies a
correction rule. Do not answer with prose, delegate an edit, weaken the task
contract, or claim theorem-proof evidence.

Before commit_scientific_source, use submit_scientific_source to test the complete
immutable public ABI in question.estimator_execution_contract when present; it
outranks Theory summaries. Cover valid and rejected requests, exact responses, and
transformations. In this workspace run_sandbox is only a developer diagnostic for
run_estimator. It may contain model-authored unit, boundary, and metamorphic checks,
but it must not implement or describe confirmatory DGPs, empirical acceptance
thresholds, or outcome claims. SimulationEngineer separately owns preregistered
simulation source and blinded confirmatory execution;
no Algorithm sandbox result is empirical evidence.

When workspace_context.theory_context.document_authoritative is true, read its
exact authoritative_theory_documents through the supplied read-only document
tools; structured fields are summaries, never authority to weaken the frozen
question ABI. When source_replication_context is present, read its report through
the same tools; it is replication evidence, not mathematical or semantic authority.
"""


def algorithm_source_workspace_intent(
    *,
    source_agent: Any,
    enabled: bool,
    question_id: str,
    theory_packet_id: str,
    expected_estimator_ids: list[str],
) -> dict[str, Any]:
    """Create the deterministic identity for one direct source-workspace run."""

    capability = getattr(source_agent, "source_workspace_owns_planning", None)
    authorized = bool(enabled and callable(capability) and capability())
    intent_payload = {
        "question_id": question_id,
        "theory_packet_id": theory_packet_id,
        "expected_estimator_ids": list(expected_estimator_ids),
    }
    return {
        "authorized": authorized,
        "intent_id": (
            "algorithm_source_workspace_intent:"
            + stable_hash(intent_payload)[:20]
            if authorized
            else ""
        ),
        "planning_model_call_used": False,
    }


def materialize_algorithm_source_workspace_record(
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
    implementation_gaps: list[Mapping[str, Any]],
    source_rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind accepted retained source sessions to the immutable review ABI."""

    expected_ids = [
        str(row.get("estimator_id", row.get("id", "")) or "").strip()
        for row in implementation_gaps
        if str(row.get("estimator_id", row.get("id", "")) or "").strip()
    ]
    rows_by_id = {
        str(row.get("estimator_id", "") or "").strip(): row
        for row in source_rows
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", "") or "").strip()
    }
    errors: list[str] = []
    source_artifacts: list[dict[str, Any]] = []
    providers: set[str] = set()
    models: set[str] = set()
    model_tiers: set[str] = set()
    for estimator_id in expected_ids:
        row = rows_by_id.get(estimator_id, {})
        workspace = row.get("scientific_code_workspace", {})
        workspace = workspace if isinstance(workspace, Mapping) else {}
        source_hash = str(row.get("script_hash", "") or "").strip()
        source_code = str(row.get("source_code", "") or "")
        if (
            row.get("smoke_passed") is not True
            or not source_code
            or source_hash != stable_hash(source_code)
        ):
            errors.append(f"{estimator_id}: accepted source bytes are not hash-bound")
        if not (
            workspace.get("accepted") is True
            and workspace.get("model_owned_source") is True
            and workspace.get("runtime_edited_source") is False
            and str(workspace.get("artifact_id", "") or "").strip()
            and str(workspace.get("transcript_fingerprint", "") or "").strip()
        ):
            errors.append(f"{estimator_id}: model-owned source evidence is invalid")
        source_artifacts.append(
            {
                "estimator_id": estimator_id,
                "source_hash": source_hash,
                "workspace_artifact_id": str(
                    workspace.get("artifact_id", "") or ""
                ),
                "workspace_transcript_fingerprint": str(
                    workspace.get("transcript_fingerprint", "") or ""
                ),
            }
        )
        for values, value in (
            (providers, workspace.get("provider", "")),
            (models, workspace.get("model", "")),
            (model_tiers, workspace.get("model_tier", "")),
        ):
            normalized = str(value or "").strip()
            if normalized:
                values.add(normalized)
    if not expected_ids or len(expected_ids) != len(set(expected_ids)):
        errors.append("source workspace estimator identities are empty or duplicated")
    if set(rows_by_id) != set(expected_ids):
        errors.append("source workspace rows do not exactly cover estimator IDs")
    if any(len(values) != 1 for values in (providers, models, model_tiers)):
        errors.append("source workspaces do not share one model identity")
    if errors:
        raise ValueError("; ".join(sorted(set(errors))))

    implementation_targets = [
        {"estimator_id": estimator_id} for estimator_id in expected_ids
    ]
    _bind_algorithm_estimator_interface_contracts(
        implementation_targets,
        question=question,
        theory_packet=theory_packet,
    )
    body = {
        "source_workspace_planning_owned": True,
        "planning_model_call_used": False,
        "scientific_source_transport": (
            SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS
        ),
        "expected_estimator_ids": expected_ids,
        "implementation_targets": implementation_targets,
        "source_workspace_artifacts": source_artifacts,
        "metric_contracts": [],
        "execution_evidence_status": (
            ALGORITHM_SOURCE_WORKSPACE_RECORD_NOT_EXECUTION_EVIDENCE
        ),
        "execution_evidence_boundary": ALGORITHM_SOURCE_WORKSPACE_RECORD_BOUNDARY,
        "production_registered": False,
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        "theory_trace_consumption_contract": theory_trace_consumption_contract(
            theory_packet,
            consumer_subsystem="AlgorithmEngineer",
            max_rows=3,
            text_limit=240,
        ),
        "theory_trace_alignment_contract": theory_trace_alignment_contract(
            theory_packet,
            {},
            consumer_subsystem="AlgorithmEngineer",
            max_rows=3,
            text_limit=240,
        ),
    }
    record_hash = stable_hash(
        {
            "question_id": question.id,
            "theory_packet_id": str(theory_packet.get("packet_id", "") or ""),
            "theory_packet_hash": stable_hash(theory_packet),
            "provider": next(iter(providers)),
            "model": next(iter(models)),
            "model_tier": next(iter(model_tiers)),
            "body": body,
        }
    )[:24]
    record = {
        "schema_version": ALGORITHM_SOURCE_WORKSPACE_SCHEMA_VERSION,
        "artifact_kind": "AlgorithmSourceWorkspaceRecord",
        "packet_id": f"algorithm_source_workspace_record:{record_hash}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_agent": "LLMAlgorithmEngineerAgent",
        "provider": next(iter(providers)),
        "backend_provider": next(iter(providers)),
        "model": next(iter(models)),
        "model_tier": next(iter(model_tiers)),
        "question": {"id": question.id},
        "theory_packet_ref": {
            "packet_id": str(theory_packet.get("packet_id", "") or ""),
            "content_hash": stable_hash(theory_packet),
        },
        **body,
    }
    validation_errors = validate_algorithm_source_workspace_record(record)
    if validation_errors:
        raise ValueError("; ".join(validation_errors))
    return record


def validate_algorithm_source_workspace_record(
    record: Mapping[str, Any],
) -> list[str]:
    """Validate identity, source lineage, and immutable ABI bindings only."""

    errors: list[str] = []
    if record.get("artifact_kind") != "AlgorithmSourceWorkspaceRecord":
        errors.append("artifact_kind must be AlgorithmSourceWorkspaceRecord")
    if record.get("scientific_source_transport") != (
        SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS
    ):
        errors.append("algorithm source must use native client-tool transport")
    if record.get("source_workspace_planning_owned") is not True:
        errors.append("retained source workspace must own planning")
    if record.get("planning_model_call_used") is not False:
        errors.append("retained source workspace cannot claim a planning model call")
    if record.get("execution_evidence_status") != (
        ALGORITHM_SOURCE_WORKSPACE_RECORD_NOT_EXECUTION_EVIDENCE
    ):
        errors.append("source workspace record must preserve its evidence boundary")
    if record.get("production_registered") is not False:
        errors.append("source workspace record cannot register production code")
    if record.get("proof_evidence_status") != "NOT_PROOF_EVIDENCE":
        errors.append("source workspace record cannot claim proof evidence")
    if record.get("metric_contracts") not in (None, []):
        errors.append("AlgorithmEngineer cannot author empirical metric contracts")

    targets = [
        row
        for row in record.get("implementation_targets", []) or []
        if isinstance(row, Mapping)
    ]
    target_ids = [
        str(row.get("estimator_id", "") or "").strip() for row in targets
    ]
    expected_ids = [
        str(value or "").strip()
        for value in record.get("expected_estimator_ids", []) or []
    ]
    if not target_ids or any(not value for value in target_ids):
        errors.append("implementation targets require estimator identities")
    if len(target_ids) != len(set(target_ids)):
        errors.append("implementation target estimator identities are duplicated")
    if target_ids != expected_ids:
        errors.append("implementation targets do not match expected estimator identities")
    for row in targets:
        estimator_id = str(row.get("estimator_id", "") or "<unknown>")
        errors.extend(
            _estimator_interface_contract_errors(
                row.get("estimator_interface_contract"),
                label=f"implementation target {estimator_id}",
                required=True,
            )
        )
        authority = row.get("estimator_interface_contract_authority", {})
        authority = authority if isinstance(authority, Mapping) else {}
        if authority.get("owner_agent") not in (
            "TheoryDeveloper",
            "FrozenResearchQuestion",
        ):
            errors.append(
                "estimator interface must be bound to TheoryDeveloper or the frozen question"
            )
        if authority.get("transport_status") not in {
            "RUNTIME_BOUND_FROM_THEORY",
            "RUNTIME_BOUND_FROM_FROZEN_QUESTION",
        }:
            errors.append("estimator interface must preserve its upstream binding")

    artifacts = [
        row
        for row in record.get("source_workspace_artifacts", []) or []
        if isinstance(row, Mapping)
    ]
    artifact_ids = [
        str(row.get("estimator_id", "") or "").strip() for row in artifacts
    ]
    if artifact_ids != expected_ids:
        errors.append("source workspace artifacts do not match expected estimators")
    for row in artifacts:
        if not all(
            str(row.get(field, "") or "").strip()
            for field in (
                "source_hash",
                "workspace_artifact_id",
                "workspace_transcript_fingerprint",
            )
        ):
            errors.append("source workspace artifact identity is incomplete")
        if "source_code" in row:
            errors.append("source workspace record must carry references, not source bytes")
    return sorted(set(errors))


def _bind_algorithm_estimator_interface_contracts(
    targets: list[dict[str, Any]],
    *,
    question: OpenResearchQuestion,
    theory_packet: Mapping[str, Any],
) -> None:
    upstream_contracts = theory_estimator_interface_contracts(theory_packet)
    frozen_contract = question.estimator_execution_contract
    if frozen_contract:
        frozen_interface = project_executable_estimator_interface_contract(
            frozen_contract
        )
        upstream_contracts[str(frozen_contract["estimator_id"])] = {
            "contract": frozen_interface,
            "contract_id": estimator_interface_contract_id(frozen_interface),
            "source_ref": "question#/estimator_execution_contract",
            "owner_agent": "FrozenResearchQuestion",
            "source_hash": stable_hash(frozen_contract),
            "bound_status": "RUNTIME_BOUND_FROM_FROZEN_QUESTION",
        }
    source_theory_packet_id = str(theory_packet.get("packet_id", "") or "")
    source_theory_packet_hash = stable_hash(theory_packet)
    for target in targets:
        estimator_id = str(target.get("estimator_id", "") or "").strip()
        upstream = upstream_contracts.get(estimator_id)
        if upstream is None:
            continue
        exact_interface = deepcopy(upstream["contract"])
        target["estimator_interface_contract"] = exact_interface
        target["estimator_interface_contract_id"] = upstream["contract_id"]
        target["estimator_interface_contract_authority"] = {
            "owner_agent": upstream.get("owner_agent", "TheoryDeveloper"),
            "source_theory_packet_id": source_theory_packet_id,
            "source_theory_packet_hash": upstream.get(
                "source_hash", source_theory_packet_hash
            ),
            "source_estimator_ref": upstream["source_ref"],
            "transport_status": upstream.get(
                "bound_status", "RUNTIME_BOUND_FROM_THEORY"
            ),
        }


def _estimator_interface_contract_errors(
    value: Any,
    *,
    label: str,
    required: bool,
) -> list[str]:
    return shared_estimator_interface_contract_errors(
        value,
        label=label,
        required=required,
    )

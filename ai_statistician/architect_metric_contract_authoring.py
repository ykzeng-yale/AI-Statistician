from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .agent_runtime import agent_runtime_substage
from .client_tool_loop import (
    CLIENT_TOOL_TRANSCRIPT_POLICY,
    ClientToolExecutionContext,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    ClientToolLoopResult,
    apply_model_exact_text_edits,
    persist_client_tool_session,
    run_bounded_client_tool_loop,
)
from .architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY,
    LLMArchitectMetricSemanticReviewerAgent,
    architect_metric_review_material_with_runtime_evaluator_certificate,
    bind_architect_metric_finding_evidence_identities,
)
from .fingerprint import stable_hash
from .generated_metric_contract import (
    GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS,
    GENERATED_METRIC_SOURCE_ACCEPTANCE_MODE,
    GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES,
    generated_metric_acceptance_authority_catalog,
    generated_metric_acceptance_authority_prompt_catalog,
    generated_metric_evaluation_semantics_contract,
    generated_metric_requirement_json_schema,
    generated_metric_requirement_prompt_schema,
    generated_metric_requirement_set_id,
    generated_metric_shared_runtime_replicates,
    generated_metric_requirement_target_namespace_contract,
    materialize_generated_metric_gate_field_authorities,
    validate_generated_metric_requirements,
)
from .implementation_metric_handoff import (
    accepted_implementation_interface_handoff_errors,
)
from .structured_output_retry import (
    PacketValidationError,
    extract_json_object,
)
from .model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnRequest,
    GeneratorBackend,
)
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
)
from .metric_protocol_finding_ledger import (
    active_metric_protocol_finding_ledger,
    metric_protocol_finding_ledger_fingerprint,
    metric_protocol_finding_ledger_from_review_history,
    update_metric_protocol_finding_ledger,
)
from .research_schema import OpenResearchQuestion, research_question_payload
from .semantic_review_feedback import model_observations_without_repair_recipes


ARCHITECT_METRIC_REQUIREMENT_AUTHORING_SCHEMA_VERSION = 7
MAX_CONFIRMATORY_METRIC_REQUIREMENTS = 8
FRESH_METRIC_AUTHORING_AUTHORITY_KIND = "architect_preregistered_design"
FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS = frozenset(
    {
        "source_anchors",
        "acceptance_authority_rationale",
    }
)
FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD = "gate_field_authorities"
FROZEN_METRIC_PROTOCOL_REBINDING_GATE_MUTABLE_FIELDS = frozenset(
    {"source_anchors", "rationale"}
)
METRIC_PROTOCOL_WORKSPACE_TRANSPORT = (
    "persistent_model_owned_markdown_acceptance_protocol_workspace_v5"
)
METRIC_PROTOCOL_WORKSPACE_CHECKPOINT_KIND = "MetricProtocolWorkspaceCheckpoint"
METRIC_PROTOCOL_WORKSPACE_READ_TOOL = "read_metric_protocol"
METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL = "edit_metric_protocol"
METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL = "commit_metric_protocol"
# The generic helper defaults to this compact JSON document for compatibility.
# Fresh preregistration keeps substantive scientific content in Markdown instead.
METRIC_PROTOCOL_WORKSPACE_INITIAL_DOCUMENT = (
    '{\n  "required_runtime_replicates": null,\n'
    '  "evaluator_id": "",\n'
    '  "acceptance_protocol": "",\n'
    '  "scientific_rationale": ""\n}\n'
)
METRIC_PROTOCOL_WORKSPACE_SOURCE_INITIAL_DOCUMENT = (
    "# Confirmatory Acceptance Protocol\n\n"
    "## Measurements and scenarios\n\n"
    "Describe the decisive pre-outcome measurements and scenarios.\n\n"
    "## Decision rule\n\n"
    "Define the joint acceptance decision and retained diagnostics.\n"
)
METRIC_PROTOCOL_WORKSPACE_FROZEN_INITIAL_DOCUMENT = (
    '{\n  "empirical_metric_requirements": []\n}\n'
)
METRIC_PROTOCOL_WORKSPACE_MAX_TURNS = 8
METRIC_PROTOCOL_WORKSPACE_MAX_TOOL_CALLS = 10
METRIC_PROTOCOL_WORKSPACE_MAX_NO_PROGRESS_TURNS = 2


def _frozen_metric_protocol_rebinding_mutable_fields(
    source_rows: Any,
) -> frozenset[str]:
    fields = set(FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS)
    if isinstance(source_rows, list) and any(
        isinstance(row, Mapping)
        and FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in row
        for row in source_rows
    ):
        fields.add(FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD)
    return frozenset(fields)


def _frozen_gate_field_authority_immutable_view(value: Any) -> Any:
    if not isinstance(value, list):
        return value
    return [
        {
            str(key): item
            for key, item in row.items()
            if key not in FROZEN_METRIC_PROTOCOL_REBINDING_GATE_MUTABLE_FIELDS
        }
        if isinstance(row, Mapping)
        else row
        for row in value
    ]


class ArchitectMetricSemanticReviewRejected(PacketValidationError):
    """Bounded pre-execution metric authoring exhausted without acceptance."""

    def __init__(
        self,
        *,
        question_id: str,
        semantic_review_history: list[dict[str, Any]],
        source_theory_packet_id: str = "",
        source_theory_packet_hash: str = "",
    ) -> None:
        history = [dict(row) for row in semantic_review_history]
        last_review = history[-1] if history else {}
        self.question_id = str(question_id)
        self.semantic_review_history = history
        self.source_theory_packet_id = str(source_theory_packet_id or "")
        self.source_theory_packet_hash = str(source_theory_packet_hash or "")
        review_stage = str(last_review.get("review_stage", "") or "")
        failure_summary = (
            "independent theory-to-execution preflight rejected the current "
            "TheoryDeveloper handoff before metric authoring"
            if review_stage == "theory_execution_preflight"
            else "independent semantic reviewer did not accept any metric contract "
            f"candidate after {len(history)} attempt(s)"
        )
        super().__init__(
            validation_label="Architect pre-execution metric semantic review",
            attempts=len(history),
            errors=[
                failure_summary,
                *[
                    str(row.get("summary", "") or "")
                    for row in last_review.get("findings", []) or []
                    if isinstance(row, Mapping)
                    and str(row.get("summary", "") or "").strip()
                ],
            ],
            history=history,
        )


class ArchitectMetricSemanticReviewPacketValidationError(PacketValidationError):
    """Reviewer validation failure bound to its validated author candidate."""

    def __init__(
        self,
        *,
        cause: PacketValidationError,
        authoring_packet: Mapping[str, Any],
        revision_index: int,
        trusted_review_lineage: Mapping[str, Any],
        review_material_fingerprint: str,
        semantic_review_history: list[dict[str, Any]],
    ) -> None:
        self.authoring_packet = deepcopy(dict(authoring_packet))
        self.authoring_packet_hash = stable_hash(self.authoring_packet)
        self.revision_index = int(revision_index)
        self.trusted_review_lineage = deepcopy(dict(trusted_review_lineage))
        self.review_material_fingerprint = str(
            review_material_fingerprint or ""
        )
        self.semantic_review_history = deepcopy(semantic_review_history)
        super().__init__(
            validation_label=cause.validation_label,
            attempts=cause.attempts,
            errors=cause.errors,
            history=cause.history,
            last_invalid_packet=cause.last_invalid_packet,
        )


def _frozen_metric_protocol_rebinding_errors(
    *,
    candidate_requirements: Any,
    rebinding_context: Mapping[str, Any],
) -> list[str]:
    source_rows = rebinding_context.get("source_requirement_rows", [])
    if not isinstance(source_rows, list) or not source_rows:
        return ["frozen metric rebinding source rows are missing"]
    if not isinstance(candidate_requirements, list):
        return ["frozen metric rebinding candidate rows must be a list"]
    source_by_id = {
        str(row.get("requirement_id", "") or ""): dict(row)
        for row in source_rows
        if isinstance(row, Mapping)
        and str(row.get("requirement_id", "") or "").strip()
    }
    candidate_by_id = {
        str(row.get("requirement_id", "") or ""): dict(row)
        for row in candidate_requirements
        if isinstance(row, Mapping)
        and str(row.get("requirement_id", "") or "").strip()
    }
    errors: list[str] = []
    if len(source_by_id) != len(source_rows):
        errors.append(
            "frozen metric rebinding source requirement IDs must be unique and "
            "nonempty"
        )
    if len(candidate_by_id) != len(candidate_requirements):
        errors.append(
            "frozen metric rebinding candidate requirement IDs must be unique and "
            "nonempty"
        )
    source_ids = list(source_by_id)
    candidate_ids = list(candidate_by_id)
    if candidate_ids != source_ids:
        errors.append(
            "frozen metric rebinding must preserve the exact ordered requirement "
            f"IDs: expected={source_ids!r} observed={candidate_ids!r}"
        )
    for requirement_id in source_ids:
        source_row = source_by_id[requirement_id]
        candidate_row = candidate_by_id.get(requirement_id)
        if candidate_row is None:
            continue
        mutable_fields = set(FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS)
        source_has_gate_field_authorities = (
            FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in source_row
        )
        if source_has_gate_field_authorities:
            mutable_fields.add(
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            )
        immutable_fields = (
            set(source_row) | set(candidate_row)
        ) - mutable_fields
        for field in sorted(immutable_fields):
            if candidate_row.get(field) != source_row.get(field):
                errors.append(
                    "frozen metric rebinding may not change "
                    f"{requirement_id}.{field}"
                )
        if source_has_gate_field_authorities and (
            _frozen_gate_field_authority_immutable_view(
                candidate_row.get(
                    FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
                )
            )
            != _frozen_gate_field_authority_immutable_view(
                source_row.get(
                    FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
                )
            )
        ):
            errors.append(
                "frozen metric rebinding may not change "
                f"{requirement_id}."
                f"{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD} "
                "field identities or authority kinds"
            )
    return errors


def _reconstruct_frozen_metric_protocol_requirements(
    *,
    binding_rows: Any,
    rebinding_context: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    source_rows = rebinding_context.get("source_requirement_rows", [])
    if not isinstance(source_rows, list) or not source_rows:
        return [], ["frozen metric rebinding source rows are missing"]
    if not isinstance(binding_rows, list):
        return [], ["frozen metric rebinding output rows must be a list"]

    source_by_id = {
        str(row.get("requirement_id", "") or ""): dict(row)
        for row in source_rows
        if isinstance(row, Mapping)
        and str(row.get("requirement_id", "") or "").strip()
    }
    source_ids = [
        str(row.get("requirement_id", "") or "")
        for row in source_rows
        if isinstance(row, Mapping)
    ]
    observed_ids: list[str] = []
    reconstructed_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, raw_binding in enumerate(binding_rows):
        prefix = f"empirical_metric_requirements[{index}]"
        if not isinstance(raw_binding, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        binding = dict(raw_binding)
        requirement_id = str(binding.get("requirement_id", "") or "")
        observed_ids.append(requirement_id)
        source_row = source_by_id.get(requirement_id)
        if source_row is None:
            errors.append(
                f"{prefix}.requirement_id is not one of the frozen requirement IDs"
            )
            reconstructed_rows.append(binding)
            continue
        mutable_fields = set(FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS)
        if FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in source_row:
            mutable_fields.add(
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            )
        output_fields = {"requirement_id", *mutable_fields}
        extra_fields = sorted(set(binding) - output_fields)
        if extra_fields:
            errors.append(
                f"{prefix} contains runtime-owned frozen fields: "
                f"{extra_fields!r}"
            )
        missing_fields = sorted(output_fields - set(binding))
        if missing_fields:
            errors.append(
                f"{prefix} is missing required binding fields: "
                f"{missing_fields!r}"
            )
        reconstructed = dict(source_row)
        for field in FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS:
            if field in binding:
                reconstructed[field] = binding[field]
        if FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in mutable_fields:
            source_gate_rows = source_row.get(
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            )
            binding_gate_rows = binding.get(
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            )
            if not isinstance(source_gate_rows, list):
                errors.append(
                    f"{prefix}.{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD} "
                    "source rows must be an array"
                )
            elif not isinstance(binding_gate_rows, list):
                errors.append(
                    f"{prefix}.{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD} "
                    "must be an array"
                )
            else:
                if len(binding_gate_rows) != len(source_gate_rows):
                    errors.append(
                        f"{prefix}."
                        f"{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD} "
                        "must preserve the exact number of field bindings"
                    )
                rebound_gate_rows: list[dict[str, Any]] = []
                for gate_index, source_gate_row in enumerate(
                    source_gate_rows
                ):
                    gate_prefix = (
                        f"{prefix}."
                        f"{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD}"
                        f"[{gate_index}]"
                    )
                    if not isinstance(source_gate_row, Mapping):
                        errors.append(
                            f"{gate_prefix} source binding must be an object"
                        )
                        continue
                    raw_gate_binding = (
                        binding_gate_rows[gate_index]
                        if gate_index < len(binding_gate_rows)
                        else {}
                    )
                    if not isinstance(raw_gate_binding, Mapping):
                        errors.append(f"{gate_prefix} must be an object")
                        raw_gate_binding = {}
                    gate_binding = dict(raw_gate_binding)
                    expected_gate_fields = {
                        "field",
                        "authority_kind",
                        *FROZEN_METRIC_PROTOCOL_REBINDING_GATE_MUTABLE_FIELDS,
                    }
                    extra_gate_fields = sorted(
                        set(gate_binding) - expected_gate_fields
                    )
                    if extra_gate_fields:
                        errors.append(
                            f"{gate_prefix} contains runtime-owned fields: "
                            f"{extra_gate_fields!r}"
                        )
                    missing_gate_fields = sorted(
                        expected_gate_fields - set(gate_binding)
                    )
                    if missing_gate_fields:
                        errors.append(
                            f"{gate_prefix} is missing required fields: "
                            f"{missing_gate_fields!r}"
                        )
                    for immutable_field in (
                        "field",
                        "authority_kind",
                    ):
                        if gate_binding.get(immutable_field) != (
                            source_gate_row.get(immutable_field)
                        ):
                            errors.append(
                                f"{gate_prefix}.{immutable_field} must "
                                "preserve the frozen value"
                            )
                    rebound_gate_row = dict(source_gate_row)
                    for mutable_field in (
                        FROZEN_METRIC_PROTOCOL_REBINDING_GATE_MUTABLE_FIELDS
                    ):
                        if mutable_field in gate_binding:
                            rebound_gate_row[mutable_field] = (
                                gate_binding[mutable_field]
                            )
                    rebound_gate_rows.append(rebound_gate_row)
                reconstructed[
                    FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
                ] = rebound_gate_rows
        reconstructed_rows.append(reconstructed)

    if observed_ids != source_ids:
        errors.append(
            "frozen metric rebinding output must preserve the exact ordered "
            f"requirement IDs: expected={source_ids!r} observed={observed_ids!r}"
        )
    return reconstructed_rows, errors


@dataclass(frozen=True)
class ArchitectMetricContractAuthoringConfig:
    max_tokens: int = 8000
    model_tier: str = "sonnet"
    provider_name: str = "anthropic"
    max_validation_retries: int = 1
    metric_semantic_reviewer_max_revisions: int = 1


@dataclass(frozen=True)
class MetricProtocolWorkspaceResult:
    packet: Mapping[str, Any]
    document_content: str
    loop: ClientToolLoopResult
    session_ref: Mapping[str, Any]
    relative_document_path: str


def _metric_protocol_tool(
    name: str,
    description: str,
    *,
    properties: Mapping[str, Any] | None = None,
    required: Sequence[str] = (),
    terminal: bool = False,
) -> ClientToolDefinition:
    schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": dict(properties or {}),
    }
    if required:
        schema["required"] = list(required)
    return ClientToolDefinition(
        name=name,
        description=description,
        input_schema=schema,
        terminal=terminal,
        strict=False,
    )


def _metric_protocol_workspace_tools(
    *,
    source_acceptance_mode: bool = False,
) -> tuple[ClientToolDefinition, ...]:
    hash_field = {
        "type": "string",
        "minLength": 64,
        "maxLength": 64,
        "pattern": "^[0-9a-f]{64}$",
    }
    document_name = (
        "metric_protocol.md" if source_acceptance_mode else "metric_protocol.json"
    )
    commit_properties: dict[str, Any] = {"expected_sha256": hash_field}
    commit_required = ["expected_sha256"]
    if source_acceptance_mode:
        commit_properties.update(
            {
                "required_runtime_replicates": {
                    "type": "integer",
                    "minimum": 1,
                },
                "evaluator_id": {"type": "string", "minLength": 1},
                "scientific_rationale": {"type": "string", "minLength": 1},
            }
        )
        commit_required.extend(
            [
                "required_runtime_replicates",
                "evaluator_id",
                "scientific_rationale",
            ]
        )
    return (
        _metric_protocol_tool(
            METRIC_PROTOCOL_WORKSPACE_READ_TOOL,
            f"Read the exact current {document_name} and SHA-256.",
        ),
        _metric_protocol_tool(
            METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
            (
                "Atomically apply an ordered batch of exact model-authored text "
                f"replacements to the external {document_name}. Bind the batch "
                "to the current SHA-256. Each old_text must occur exactly once unless "
                "expected_occurrences declares its exact positive count, in which case "
                "all occurrences are replaced. Runtime validates the whole batch "
                "before updating bytes and does not interpret or author scientific "
                "content."
            ),
            properties={
                "expected_parent_sha256": hash_field,
                "edits": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "old_text": {"type": "string", "minLength": 1},
                            "new_text": {"type": "string"},
                            "expected_occurrences": {
                                "type": "integer",
                                "minimum": 1,
                            },
                        },
                        "required": ["old_text", "new_text"],
                    },
                },
            },
            required=("expected_parent_sha256", "edits"),
        ),
        _metric_protocol_tool(
            METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
            (
                f"Commit the exact current external {document_name} by SHA-256. "
                "The call contains no document body. "
                + (
                    "Supply only the compact evaluator identity, replicate count, and "
                    "scientific rationale alongside the hash; runtime binds the exact "
                    "Markdown bytes as the acceptance protocol. "
                    if source_acceptance_mode
                    else ""
                )
                + "Runtime validates the existing bytes; rejection returns raw errors "
                "to this same source-owner session."
            ),
            properties=commit_properties,
            required=tuple(commit_required),
            terminal=True,
        ),
    )


def _metric_protocol_document_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _run_metric_protocol_workspace(
    *,
    provider: GeneratorBackend,
    config: ArchitectMetricContractAuthoringConfig,
    request_model: str,
    user_message: str,
    build_validated_packet: Callable[
        [str], tuple[dict[str, Any] | None, list[str]]
    ],
    prior_messages: Sequence[Mapping[str, Any]] = (),
    prior_document_content: str = "",
    initial_document_content: str = METRIC_PROTOCOL_WORKSPACE_INITIAL_DOCUMENT,
    workspace_dir: Path | None = None,
    session_id: str = "",
    revision_index: int = 0,
    source_acceptance_mode: bool = False,
) -> MetricProtocolWorkspaceResult:
    """Let one model own an editable protocol document and its validation loop."""

    generate_turn = getattr(provider, "generate_client_tool_turn", None)
    if not callable(generate_turn):
        raise ValueError(
            "metric protocol authoring requires native client-tool turns; "
            "full-packet generation is not a canonical fallback"
        )
    normalized_user_message = str(user_message or "").strip()
    if not normalized_user_message:
        raise ValueError("metric protocol workspace requires a user observation")
    document = str(prior_document_content or initial_document_content or "")
    if not document.strip():
        raise ValueError("metric protocol workspace requires a nonempty scaffold")
    runtime_initialized_scaffold = not bool(str(prior_document_content or "").strip())
    root = workspace_dir.resolve() if workspace_dir is not None else None
    document_name = (
        "metric_protocol.md" if source_acceptance_mode else "metric_protocol.json"
    )
    document_path = root / document_name if root is not None else None
    relative_document_path = document_path.name if document_path else ""
    if root is not None:
        root.mkdir(parents=True, exist_ok=True)
    if document_path is not None:
        if document_path.exists():
            existing = document_path.read_text(encoding="utf-8")
            if existing != document:
                raise ValueError(
                    "metric protocol workspace bytes do not match source-owner state"
                )
        elif document:
            document_path.write_text(document, encoding="utf-8")

    def persist_document() -> None:
        if document_path is not None:
            document_path.write_text(document, encoding="utf-8")

    latest_submission_metadata: dict[str, Any] = {}

    def inspect_document() -> tuple[dict[str, Any] | None, list[str]]:
        if not document.strip():
            return None, [f"{document_name} is empty"]
        candidate_document = document
        if source_acceptance_mode:
            if not latest_submission_metadata:
                return None, [
                    "metric protocol commit metadata has not been submitted"
                ]
            candidate_document = json.dumps(
                {
                    **latest_submission_metadata,
                    "acceptance_protocol": document,
                },
                ensure_ascii=False,
            )
        try:
            packet, errors = build_validated_packet(candidate_document)
        except Exception as exc:
            return None, [
                f"{document_name} invalid: "
                f"{type(exc).__name__}: {str(exc)[:500]}"
            ]
        return packet, [str(error) for error in errors if str(error).strip()]

    def seal_session(messages: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        normalized_id = str(session_id or "").strip()
        return (
            persist_client_tool_session(
                session_dir=root,
                session_id=normalized_id,
                request=request,
                messages=messages,
            )
            if root is not None and normalized_id
            else {}
        )

    tools = _metric_protocol_workspace_tools(
        source_acceptance_mode=source_acceptance_mode
    )
    messages = [deepcopy(dict(message)) for message in prior_messages]
    messages.append({"role": "user", "content": normalized_user_message})
    request = ClientToolTurnRequest(
        system_prompt=(
            "You are the pre-outcome acceptance-protocol source owner inside the "
            "AI Statistician. "
            f"Work on one persistent external {document_name} through exact read, "
            "atomic literal edits, and hash-bound commit tools. Read the current "
            "scaffold or "
            "document before editing. You may replace the whole file or make smaller "
            "exact edits; group independent corrections against one parent version "
            "into one ordered atomic batch. For a repeated literal, use one "
            "expected_occurrences edit instead of regenerating the file. Keep incomplete "
            "work in the file until "
            "it is ready. Scientific measurements, formulas, joint decision logic, "
            "replicate design, and rationale are yours. Runtime only binds the "
            "stable acceptance_passed ABI, validates identity and safety, and "
            "invokes an isolated pre-outcome reviewer. SimulationEngineer later "
            "implements your frozen protocol in ordinary Python or R. "
            + (
                "Keep this Markdown focused on executable measurements, scenarios, "
                "decision formulas, and retained diagnostics. Cite the accepted theory "
                "rather than copying its derivation into the protocol. "
                if source_acceptance_mode
                else ""
            )
            + "Read exact reviewer observations, revise your own document, and commit "
            "its exact current hash. Never place document content in the commit call. "
            "Do not ask Architect or runtime to repair "
            "content, claim that execution occurred, or treat this as proof."
        ),
        messages=tuple(messages),
        tools=tools,
        model=request_model,
        max_tokens=max(1, int(config.max_tokens)),
        temperature=0.0,
        tool_choice="any",
        disable_parallel_tool_use=True,
        enable_prompt_caching=True,
        metadata={
            "subsystem": "MetricProtocolWorkspace",
            "agent": "MetricProtocolSourceOwner",
            "provider_name": config.provider_name,
            "model_tier": config.model_tier,
            "revision_index": int(revision_index),
            "workspace_transport": METRIC_PROTOCOL_WORKSPACE_TRANSPORT,
            "source_acceptance_mode": source_acceptance_mode,
            "full_packet_regeneration_required": False,
            "document_body_in_terminal_tool": False,
            "runtime_initialized_structural_scaffold": runtime_initialized_scaffold,
        },
    )

    def execute_tool(
        call: ClientToolCall,
        _context: ClientToolExecutionContext,
    ) -> ClientToolExecutionResult:
        nonlocal document, latest_submission_metadata
        payload = dict(call.input)

        def require_fields(*names: str) -> None:
            if set(payload) != set(names):
                raise ClientToolInputError(
                    f"{call.name} requires exactly {', '.join(names) or 'no fields'}"
                )

        if call.name == METRIC_PROTOCOL_WORKSPACE_READ_TOOL:
            require_fields()
            sha256 = _metric_protocol_document_sha256(document) if document else ""
            return ClientToolExecutionResult(
                content={
                    "ok": bool(document),
                    "exists": bool(document),
                    "content": document,
                    "sha256": sha256,
                    "content_chars": len(document),
                },
                observation_key=(
                    "metric-protocol-read:" + (sha256 or "empty")
                ),
            )
        if call.name == METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL:
            require_fields("expected_parent_sha256", "edits")
            parent_sha256 = _metric_protocol_document_sha256(document)
            if payload.get("expected_parent_sha256") != parent_sha256:
                raise ClientToolInputError(
                    "edit_metric_protocol parent hash is stale"
                )
            raw_edits = payload.get("edits")
            if not isinstance(raw_edits, list) or not raw_edits:
                raise ClientToolInputError(
                    "edit_metric_protocol edits must be a nonempty array"
                )
            revised, _ = apply_model_exact_text_edits(
                document,
                edits=raw_edits,
                replacement_key="new_text",
            )
            if not revised.strip():
                raise ClientToolInputError(
                    "edit_metric_protocol cannot leave the document empty"
                )
            document = revised
            persist_document()
            current_sha256 = _metric_protocol_document_sha256(document)
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "edited": True,
                    "edit_count": len(raw_edits),
                    "parent_sha256": parent_sha256,
                    "current_sha256": current_sha256,
                    "content_chars": len(document),
                    "instruction": (
                        "Continue editing if needed, then commit this exact SHA-256."
                    ),
                },
                state_changed=True,
                observation_key="metric-protocol-edited:" + current_sha256,
            )
        if call.name == METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL:
            if source_acceptance_mode:
                require_fields(
                    "expected_sha256",
                    "required_runtime_replicates",
                    "evaluator_id",
                    "scientific_rationale",
                )
            else:
                require_fields("expected_sha256")
            current_sha256 = _metric_protocol_document_sha256(document)
            if payload.get("expected_sha256") != current_sha256:
                raise ClientToolInputError(
                    "commit_metric_protocol expected_sha256 is stale"
                )
            if source_acceptance_mode:
                latest_submission_metadata = {
                    "required_runtime_replicates": payload.get(
                        "required_runtime_replicates"
                    ),
                    "evaluator_id": str(payload.get("evaluator_id", "") or ""),
                    "scientific_rationale": str(
                        payload.get("scientific_rationale", "") or ""
                    ),
                }
            packet, errors = inspect_document()
            if packet is None or errors:
                rejection = {
                    "ok": False,
                    "error": "metric_protocol_submission_rejected",
                    "current_sha256": current_sha256,
                    "validation_errors": errors[:16],
                    "instruction": (
                        "Edit the exact current external protocol in this same "
                        "source-owner session, then commit its new SHA-256."
                    ),
                }
                return ClientToolExecutionResult(
                    content=rejection,
                    is_error=True,
                    observation_key=(
                        "metric-protocol-commit-rejected:"
                        + stable_hash(rejection)
                    ),
                )
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "submitted": True,
                    "sha256": current_sha256,
                    "packet_id": str(packet.get("packet_id", "") or ""),
                    "requirement_set_id": str(
                        packet.get("empirical_metric_requirement_set_id", "")
                        or ""
                    ),
                    "proof_evidence_status": (
                        "ARCHITECT_METRIC_REQUIREMENT_AUTHORING_NOT_PROOF_EVIDENCE"
                    ),
                },
                terminal=True,
                terminal_payload={"authoring_packet": packet},
                observation_key="metric-protocol-committed:" + current_sha256,
            )
        raise ClientToolInputError("unsupported metric protocol workspace tool")

    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=METRIC_PROTOCOL_WORKSPACE_MAX_TURNS,
            max_tool_calls=METRIC_PROTOCOL_WORKSPACE_MAX_TOOL_CALLS,
            max_no_progress_turns=(
                METRIC_PROTOCOL_WORKSPACE_MAX_NO_PROGRESS_TURNS
            ),
            max_terminal_recovery_turns=max(
                0, int(config.max_validation_retries)
            ),
        )
    except ClientToolLoopError as exc:
        session_ref = seal_session(exc.messages)
        current_packet, current_errors = inspect_document()
        checkpoint_body = {
            "schema_version": 1,
            "artifact_kind": METRIC_PROTOCOL_WORKSPACE_CHECKPOINT_KIND,
            "session_id": str(session_id or "").strip(),
            "revision_index": int(revision_index),
            "relative_document_path": relative_document_path,
            "document_sha256": (
                _metric_protocol_document_sha256(document) if document else ""
            ),
            "current_candidate_mechanically_valid": bool(
                current_packet is not None and not current_errors
            ),
            "current_validation_errors": list(current_errors),
            "client_tool_session_ref": deepcopy(dict(session_ref)),
            "transcript_policy": CLIENT_TOOL_TRANSCRIPT_POLICY,
            "model_owned_content": True,
            "runtime_edited_content": False,
            "runtime_initialized_structural_scaffold": (
                runtime_initialized_scaffold
            ),
            "automatic_retry_authorized": False,
            "proof_evidence_status": (
                "METRIC_PROTOCOL_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
            ),
        }
        checkpoint = {
            **checkpoint_body,
            "checkpoint_id": (
                "metric_protocol_workspace_checkpoint:"
                + stable_hash(checkpoint_body)[:20]
            ),
        }
        raise PacketValidationError(
            validation_label="LLM Architect metric-requirement packet",
            attempts=exc.turns,
            errors=list(dict.fromkeys([exc.reason, *current_errors])),
            history=[deepcopy(dict(row)) for row in exc.history],
            last_invalid_packet=(
                deepcopy(dict(current_packet))
                if isinstance(current_packet, Mapping) and current_errors
                else None
            ),
            recovery_checkpoint=checkpoint,
        ) from exc
    packet = loop.terminal_payload.get("authoring_packet", {})
    if not isinstance(packet, Mapping):
        raise PacketValidationError(
            validation_label="LLM Architect metric-requirement packet",
            attempts=loop.turns,
            errors=["metric protocol terminal payload is malformed"],
            history=[dict(row) for row in loop.history],
        )
    return MetricProtocolWorkspaceResult(
        packet=deepcopy(dict(packet)),
        document_content=document,
        loop=loop,
        session_ref=seal_session(loop.messages),
        relative_document_path=relative_document_path,
    )


def _source_acceptance_protocol_prompt_schema() -> dict[str, Any]:
    return {
        "required_runtime_replicates": (
            "one positive pre-outcome count justified by the requested Monte "
            "Carlo precision and available execution capacity"
        ),
        "evaluator_id": "stable identifier for this preregistered evaluator",
        "acceptance_protocol": (
            "compact model-authored scientific specification for the decisive "
            "measurements, formulas, scenarios, and pass decision; the "
            "SimulationEngineer implements it in Python or R"
        ),
        "scientific_rationale": (
            "why this protocol tests the theory and why its finite-run decision "
            "rule is scientifically attainable before outcomes are observed"
        ),
    }


def _source_acceptance_theory_anchor(
    theory_material: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind the protocol to one exact theory artifact without choosing support."""

    content = {
        "source_theory_packet_id": str(
            theory_material.get("source_theory_packet_id", "") or ""
        ),
        "source_theory_packet_hash": str(
            theory_material.get("source_theory_packet_hash", "") or ""
        ),
        "review_rule": (
            "The independent reviewer, not runtime, decides whether the "
            "model-authored acceptance protocol is supported by this exact theory."
        ),
    }
    return {
        "anchor_id": "theory_artifact:" + stable_hash(content)[:20],
        "authority_kind": FRESH_METRIC_AUTHORING_AUTHORITY_KIND,
        "content": content,
        "explicit_numeric_values": [],
        "granularity": "artifact_reference",
    }


def _materialize_source_acceptance_protocol(
    value: Mapping[str, Any],
    *,
    theory_anchor_id: str,
) -> tuple[dict[str, Any], list[str]]:
    """Bind one model-owned evaluator protocol to the stable Simulation ABI."""

    payload = dict(value)
    expected_fields = {
        "required_runtime_replicates",
        "evaluator_id",
        "acceptance_protocol",
        "scientific_rationale",
    }
    errors: list[str] = []
    if set(payload) != expected_fields:
        errors.append(
            "metric_protocol.json keys must be exactly "
            f"{sorted(expected_fields)!r}; observed {sorted(payload)!r}"
        )
    replicates = payload.get("required_runtime_replicates")
    if (
        isinstance(replicates, bool)
        or not isinstance(replicates, int)
        or replicates <= 0
    ):
        errors.append("required_runtime_replicates must be a positive integer")
        replicates = 0
    evaluator_id = str(payload.get("evaluator_id", "") or "").strip()
    acceptance_protocol = str(
        payload.get("acceptance_protocol", "") or ""
    ).strip()
    scientific_rationale = str(
        payload.get("scientific_rationale", "") or ""
    ).strip()
    for field, content in (
        ("evaluator_id", evaluator_id),
        ("acceptance_protocol", acceptance_protocol),
        ("scientific_rationale", scientific_rationale),
    ):
        if not content:
            errors.append(f"{field} must be a nonempty string")
    requirement = materialize_generated_metric_gate_field_authorities(
        {
            "requirement_id": evaluator_id,
            "target_subsystems": ["SimulationEngineer"],
            "metric_semantics": (
                "The frozen SimulationEngineer source returns one top-level "
                "acceptance_passed boolean after implementing the preregistered "
                "protocol and retaining its raw measurements and per-check "
                "diagnostics."
            ),
            "metric_value_kind": "boolean",
            "measurement_protocol": acceptance_protocol,
            "required_runtime_replicates": replicates,
            "operator": "==",
            "threshold": 1,
            "lower": None,
            "upper": None,
            "tolerance": 0.0,
            "aggregation": "identity",
            "minimum_pass_count": None,
            "minimum_pass_fraction": None,
            "required": True,
            "source_anchors": [theory_anchor_id],
            "acceptance_authority_kind": FRESH_METRIC_AUTHORING_AUTHORITY_KIND,
            "acceptance_authority_rationale": scientific_rationale,
            "gate_field_authorities": [],
            "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
        }
    )
    requirement["evaluator_mode"] = GENERATED_METRIC_SOURCE_ACCEPTANCE_MODE
    return requirement, errors


def _compact_metric_authoring_prompt_payload(
    value: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project duplicated trees while preserving every authority leaf verbatim."""

    payload = deepcopy(dict(value))
    original_chars = len(
        json.dumps(
            payload,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
    )
    raw_catalog = payload.get("acceptance_authority_catalog", [])
    catalog_rows = [
        [
            str(row.get("anchor_id", "") or ""),
            str(row.get("authority_kind", "") or ""),
            deepcopy(row.get("content")),
            deepcopy(row.get("explicit_numeric_values", [])),
        ]
        for row in raw_catalog
        if isinstance(row, Mapping)
    ]
    payload["acceptance_authority_catalog"] = {
        "transport": "lossless_columnar_authority_leaves_v1",
        "columns": [
            "anchor_id",
            "authority_kind",
            "content",
            "explicit_numeric_values",
        ],
        "rows": catalog_rows,
        "row_count": len(catalog_rows),
        "citation_rule": (
            "source_anchors must copy exact anchor_id cells from these rows"
        ),
    }

    raw_theory = payload.get("theory_developer_protocol_material", {})
    theory = dict(raw_theory) if isinstance(raw_theory, Mapping) else {}
    semantic_material = theory.get("theory_semantic_material", {})
    semantic_material = (
        dict(semantic_material)
        if isinstance(semantic_material, Mapping)
        else {}
    )
    payload["theory_developer_protocol_material"] = {
        field: deepcopy(theory.get(field))
        for field in (
            "artifact_kind",
            "source_theory_packet_id",
            "source_theory_packet_hash",
            "execution_results_available",
            "proof_evidence_status",
            "boundary",
        )
        if field in theory
    }
    non_authority_review_context = {
        field: deepcopy(semantic_material.get(field))
        for field in (
            "critic_findings",
            "proof_evidence_boundary",
        )
        if semantic_material.get(field) not in (None, "", [], {})
    }
    derivation = semantic_material.get("theory_derivation_packet", {})
    if isinstance(derivation, Mapping) and derivation.get("self_critique"):
        non_authority_review_context["theory_self_critique"] = deepcopy(
            derivation["self_critique"]
        )
    simulation_design = semantic_material.get("simulation_ademp_spec", {})
    if isinstance(simulation_design, Mapping):
        projected_design_context = {
            field: deepcopy(simulation_design[field])
            for field in (
                "aim",
                "performance_measures",
                "expected_theoretical_behavior",
            )
            if simulation_design.get(field) not in (None, "", [], {})
        }
        if projected_design_context:
            non_authority_review_context["simulation_design_context"] = (
                projected_design_context
            )
    payload["theory_developer_protocol_material"].update(
        {
            "semantic_transport": (
                "authority-bearing semantic nodes are preserved in the catalog"
            ),
            "non_authority_review_context": non_authority_review_context,
        }
    )
    payload["accepted_implementation_interface_handoff"] = (
        _metric_authoring_interface_prompt_projection(
            payload.get("accepted_implementation_interface_handoff", {})
        )
    )

    requirement_schema = payload.get("requirement_schema", {})
    required_fields = (
        sorted(str(field) for field in requirement_schema)
        if isinstance(requirement_schema, Mapping)
        else []
    )
    payload["requirement_schema"] = {
        "transport": "provider_native_structured_output_schema",
        "required_fields": required_fields,
        "runtime_validator_unchanged": True,
    }
    required_target_subsystems = list(
        dict.fromkeys(
            str(target)
            for row in payload.get("required_target_rows", []) or []
            if isinstance(row, Mapping)
            for target in row.get("target_subsystems", []) or []
            if str(target).strip()
        )
    )
    payload["required_target_rows"] = [
        {
            "target_subsystems": (
                required_target_subsystems
                or list(GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS)
            ),
            "at_least_one_required_row_per_target": True,
        }
    ]
    payload["prompt_projection"] = {
        "transport": "lossless_metric_authoring_projection_v2",
        "duplicated_theory_tree_omitted": True,
        "authority_leaf_content_lossless": True,
        "protocol_schema_preserved_in_portfolio_schema": True,
        "original_chars": original_chars,
        "projected_chars": 0,
    }
    projected_chars = len(
        json.dumps(
            payload,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
    )
    payload["prompt_projection"]["projected_chars"] = projected_chars
    return payload, {
        "applied": True,
        "original_chars": original_chars,
        "projected_chars": projected_chars,
        "authority_catalog_rows": len(catalog_rows),
    }


def _metric_authoring_interface_prompt_projection(value: Any) -> dict[str, Any]:
    """Keep exact interface identity and callable semantics without rate metadata."""

    if not isinstance(value, Mapping):
        return {}
    projected = {
        field: deepcopy(value[field])
        for field in (
            "artifact_kind",
            "question_id",
            "theory_packet_id",
            "handoff_id",
            "exact_source_included",
            "execution_results_included",
            "runtime_selected_semantics",
            "proof_evidence_status",
        )
        if field in value
    }
    interfaces: list[dict[str, Any]] = []
    for raw_interface in value.get("implementation_interfaces", []) or []:
        if not isinstance(raw_interface, Mapping):
            continue
        contract = raw_interface.get("estimator_interface_contract", {})
        contract = contract if isinstance(contract, Mapping) else {}
        interfaces.append(
            {
                field: deepcopy(raw_interface[field])
                for field in (
                    "estimator_id",
                    "language",
                    "exact_source_hash",
                    "estimator_interface_contract_id",
                )
                if field in raw_interface
            }
            | {
                "request_fields": [
                    {
                        field: deepcopy(row[field])
                        for field in ("name", "meaning", "binding")
                        if field in row
                    }
                    for row in contract.get("request_fields", []) or []
                    if isinstance(row, Mapping)
                ],
                "response_fields": [
                    {
                        field: deepcopy(row[field])
                        for field in (
                            "name",
                            "meaning",
                            "normalization",
                            "derivation_ref",
                        )
                        if field in row
                    }
                    for row in contract.get("response_fields", []) or []
                    if isinstance(row, Mapping)
                ],
            }
        )
    projected["implementation_interfaces"] = interfaces
    return projected


def _confirmatory_metric_requirement_rows(
    requirements: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows = [
        dict(row)
        for row in requirements or []
        if isinstance(row, Mapping)
    ]
    kept: list[dict[str, Any]] = []
    omitted: list[dict[str, str]] = []
    for row in rows:
        if row.get("required") is True:
            kept.append(row)
            continue
        omitted.append(
            {
                "requirement_id": str(row.get("requirement_id", "") or ""),
                "reason": "nonrequired_row_is_simulation_telemetry_not_acceptance",
            }
        )
    return kept, omitted


def build_architect_upstream_research_contract(
    runtime_contract: Mapping[str, Any],
) -> dict[str, Any]:
    def upstream_target_rows(field: str) -> list[Any]:
        value = runtime_contract.get(field, [])
        values = value if isinstance(value, (list, tuple)) else [value]
        return [
            deepcopy(row)
            for row in values
            if row not in (None, "", [], {})
        ]

    contract = {
        "formal_targets": upstream_target_rows("formal_targets"),
        "simulation_targets": upstream_target_rows("simulation_targets"),
        "source": "architect_runtime_plan.evidence_contract",
        "proof_evidence_status": (
            "ARCHITECT_UPSTREAM_RESEARCH_CONTRACT_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "These Architect-authored targets define the requested research scope "
            "for independent alignment review. They are proposals, not theorem "
            "proof, implementation, or simulation evidence."
        ),
    }
    if dimension_requirements := runtime_contract.get("dimension_requirements"):
        contract["dimension_requirements"] = deepcopy(dimension_requirements)
    contract["contract_fingerprint"] = stable_hash(contract)
    return contract


def _theory_protocol_material_errors(
    theory_material: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if theory_material.get("artifact_kind") != (
        "RuntimeTheoryInformedMetricProtocolMaterial"
    ):
        errors.append("theory protocol material kind mismatch")
    if theory_material.get("execution_results_available") is not False:
        errors.append("theory protocol material must be pre-execution")
    if not str(
        theory_material.get("source_theory_packet_id", "") or ""
    ).strip():
        errors.append("theory protocol material missing source theory packet")
    semantic_material = theory_material.get("theory_semantic_material", {})
    if not isinstance(semantic_material, Mapping) or not semantic_material:
        errors.append("theory protocol material missing semantic handoff")
    return errors


def review_architect_theory_execution_preflight(
    *,
    semantic_reviewer: LLMArchitectMetricSemanticReviewerAgent | None,
    question: OpenResearchQuestion,
    runtime_contract: Mapping[str, Any],
    theory_protocol_material: Mapping[str, Any],
    prior_rejection_context: Mapping[str, Any] | None = None,
    theory_scratchpad: Any = None,
    recovery_checkpoint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run only the independent source-grounded theory/executability gate."""

    if semantic_reviewer is None:
        raise ValueError(
            "theory execution preflight requires an independent semantic reviewer"
        )
    theory_material = dict(theory_protocol_material)
    material_errors = _theory_protocol_material_errors(theory_material)
    if material_errors:
        raise ValueError("; ".join(material_errors))
    prior_rejection = (
        dict(prior_rejection_context)
        if isinstance(prior_rejection_context, Mapping)
        else {}
    )
    prior_finding_ledger: list[dict[str, Any]] = []
    if (
        str(prior_rejection.get("current_source_theory_packet_id", "") or "")
        == str(theory_material.get("source_theory_packet_id", "") or "")
        and str(
            prior_rejection.get("current_source_theory_packet_hash", "") or ""
        )
        == str(theory_material.get("source_theory_packet_hash", "") or "")
    ):
        prior_finding_ledger = [
            dict(row)
            for row in prior_rejection.get("cumulative_finding_ledger", []) or []
            if isinstance(row, Mapping)
        ]
        if not prior_finding_ledger:
            prior_finding_ledger = (
                metric_protocol_finding_ledger_from_review_history(
                    question_id=question.id,
                    semantic_review_history=prior_rejection.get(
                        "semantic_review_history", []
                    ),
                )
            )
    preflight = getattr(
        semantic_reviewer,
        "review_theory_execution_preflight",
        None,
    )
    if not callable(preflight):
        raise ValueError(
            "semantic reviewer does not support theory execution preflight"
        )
    with agent_runtime_substage(
        "architect_theory_execution_preflight",
        metadata={
            "model_tier": str(
                getattr(
                    getattr(semantic_reviewer, "config", None),
                    "model_tier",
                    "",
                )
                or ""
            ),
            "source_theory_packet_id": str(
                theory_material.get("source_theory_packet_id", "") or ""
            ),
            "execution_results_available": False,
            "full_metric_authoring_deferred": True,
        },
    ):
        packet = preflight(
            question=question,
            theory_protocol_material=theory_material,
            upstream_research_contract=(
                build_architect_upstream_research_contract(runtime_contract)
            ),
            prior_finding_ledger=prior_finding_ledger,
            theory_scratchpad=theory_scratchpad,
            recovery_checkpoint=recovery_checkpoint,
        )
    if packet.get("overall_verdict") == "ACCEPT":
        return dict(packet)

    packet_hash = stable_hash(packet)
    raise ArchitectMetricSemanticReviewRejected(
        question_id=question.id,
        semantic_review_history=[
            {
                "revision_index": 0,
                "review_stage": "theory_execution_preflight",
                "authoring_packet_id": "",
                "authoring_packet_hash": "",
                "empirical_metric_requirement_set_id": "",
                "source_theory_packet_id": str(
                    theory_material.get("source_theory_packet_id", "") or ""
                ),
                "source_theory_packet_hash": str(
                    theory_material.get("source_theory_packet_hash", "") or ""
                ),
                "semantic_review_packet_id": str(
                    packet.get("packet_id", "") or ""
                ),
                "semantic_review_packet_hash": packet_hash,
                "semantic_review_model": str(packet.get("model", "") or ""),
                "semantic_review_model_tier": str(
                    packet.get("model_tier", "") or ""
                ),
                "independent_agent": bool(packet.get("independent_agent")),
                "independent_invocation": bool(
                    packet.get("independent_invocation")
                ),
                "overall_verdict": "REVISE",
                "review_scope": deepcopy(packet.get("review_scope", {})),
                "review_report": deepcopy(packet.get("review_report", {})),
                "prior_finding_reviews": [
                    dict(row)
                    for row in packet.get("prior_finding_reviews", []) or []
                    if isinstance(row, Mapping)
                ],
                "cumulative_finding_ledger": [
                    dict(row)
                    for row in packet.get("cumulative_finding_ledger", []) or []
                    if isinstance(row, Mapping)
                ],
                "cumulative_finding_ledger_fingerprint": str(
                    packet.get("cumulative_finding_ledger_fingerprint", "") or ""
                ),
                "active_unresolved_finding_ids": [
                    str(value)
                    for value in packet.get("active_unresolved_finding_ids", []) or []
                    if str(value).strip()
                ],
                "prior_finding_resolution_summary": deepcopy(
                    packet.get("prior_finding_resolution_summary", {})
                ),
                "theory_execution_preflight_packet": deepcopy(packet),
                "findings": [
                    dict(row)
                    for row in packet.get("findings", []) or []
                    if isinstance(row, Mapping)
                ],
                "execution_authorized": False,
                "proof_evidence_status": str(
                    packet.get("proof_evidence_status", "") or ""
                ),
            }
        ],
        source_theory_packet_id=str(
            theory_material.get("source_theory_packet_id", "") or ""
        ),
        source_theory_packet_hash=str(
            theory_material.get("source_theory_packet_hash", "") or ""
        ),
    )


def _accepted_theory_preflight_packet(
    context: Mapping[str, Any] | None,
    *,
    theory_material: Mapping[str, Any],
) -> dict[str, Any]:
    accepted = dict(context) if isinstance(context, Mapping) else {}
    packet = accepted.get("theory_execution_preflight_packet", {})
    packet = dict(packet) if isinstance(packet, Mapping) else {}
    if not accepted:
        return {}
    acceptance_identity_payload = dict(accepted)
    acceptance_identity_payload.pop("acceptance_id", None)
    expected_acceptance_id = (
        "architect_theory_execution_preflight_acceptance:"
        + stable_hash(acceptance_identity_payload)[:20]
    )
    valid = bool(
        accepted.get("artifact_kind")
        == "RuntimeArchitectTheoryExecutionPreflightAcceptance"
        and str(accepted.get("acceptance_id", "") or "")
        == expected_acceptance_id
        and accepted.get("execution_results_observed") is False
        and accepted.get("full_metric_authoring_completed") is False
        and str(accepted.get("source_theory_packet_id", "") or "")
        == str(theory_material.get("source_theory_packet_id", "") or "")
        and str(accepted.get("source_theory_packet_hash", "") or "")
        == str(theory_material.get("source_theory_packet_hash", "") or "")
        and packet.get("overall_verdict") == "ACCEPT"
        and str(accepted.get("preflight_packet_id", "") or "")
        == str(packet.get("packet_id", "") or "")
        and str(accepted.get("preflight_packet_hash", "") or "")
        == stable_hash(packet)
    )
    if not valid:
        raise ValueError(
            "accepted theory preflight context is missing, stale, or hash-inconsistent"
        )
    return packet


def author_reviewed_architect_metric_requirements(
    *,
    provider: GeneratorBackend,
    config: ArchitectMetricContractAuthoringConfig,
    request_model: str,
    semantic_reviewer: LLMArchitectMetricSemanticReviewerAgent | None,
    question: OpenResearchQuestion,
    runtime_contract: Mapping[str, Any],
    theory_protocol_material: Mapping[str, Any] | None = None,
    prior_rejection_context: Mapping[str, Any] | None = None,
    frozen_requirement_rebinding_context: Mapping[str, Any] | None = None,
    accepted_theory_preflight_context: Mapping[str, Any] | None = None,
    accepted_implementation_interface_context: Mapping[str, Any] | None = None,
    metric_protocol_workspace_root: Path | None = None,
    theory_scratchpad: Any = None,
) -> dict[str, Any]:
    if (
        runtime_contract.get("research_evaluation_requires_typed_metric_contracts")
        is not True
        or runtime_contract.get("empirical_metric_requirements")
        or str(getattr(provider, "provider_name", config.provider_name)).lower()
        != "anthropic"
    ):
        return {}
    if (
        runtime_contract.get("empirical_metric_protocol_phase")
        != METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED
    ):
        return {}
    if semantic_reviewer is None:
        raise ValueError(
            "capability-eval metric authoring requires an independent "
            "ArchitectMetricSemanticReviewer"
        )

    theory_material = (
        dict(theory_protocol_material)
        if isinstance(theory_protocol_material, Mapping)
        else {}
    )
    theory_material_errors = _theory_protocol_material_errors(theory_material)
    if theory_material_errors:
        raise ValueError(
            "theory-informed metric authoring requires a structured, pre-execution "
            "TheoryDeveloper semantic handoff: "
            + "; ".join(theory_material_errors)
        )
    implementation_interface = (
        dict(accepted_implementation_interface_context)
        if isinstance(accepted_implementation_interface_context, Mapping)
        else {}
    )
    if implementation_interface:
        implementation_errors = (
            accepted_implementation_interface_handoff_errors(
                implementation_interface,
                question_id=question.id,
                theory_packet_id=str(
                    theory_material.get("source_theory_packet_id", "") or ""
                ),
            )
        )
        if implementation_errors:
            raise ValueError("; ".join(implementation_errors))
    frozen_rebinding = (
        dict(frozen_requirement_rebinding_context)
        if isinstance(frozen_requirement_rebinding_context, Mapping)
        else {}
    )
    if frozen_rebinding and not (
        frozen_rebinding.get("artifact_kind")
        == "RuntimeFrozenMetricProtocolTheoryRebindingContext"
        and frozen_rebinding.get("raw_execution_artifacts_included") is False
        and frozen_rebinding.get("post_result_gate_changes_allowed") is False
        and str(
            frozen_rebinding.get("source_requirement_set_id", "") or ""
        ).strip()
        and isinstance(
            frozen_rebinding.get("source_requirement_rows"), list
        )
        and frozen_rebinding.get("source_requirement_rows")
        and str(
            frozen_rebinding.get("current_source_theory_packet_id", "") or ""
        )
        == str(theory_material.get("source_theory_packet_id", "") or "")
        and str(
            frozen_rebinding.get("current_source_theory_packet_hash", "") or ""
        )
        == str(theory_material.get("source_theory_packet_hash", "") or "")
        and set(
            frozen_rebinding.get(
                "allowed_mutable_requirement_fields", []
            )
            or []
        )
        == _frozen_metric_protocol_rebinding_mutable_fields(
            frozen_rebinding.get("source_requirement_rows", [])
        )
    ):
        raise ValueError(
            "frozen metric protocol rebinding requires sanitized, theory-bound "
            "lineage with exact immutable gate rows"
        )

    max_runtime_replicates = int(
        runtime_contract.get(
            "generated_sandbox_max_runtime_replicates",
            GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES,
        )
        or GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES
    )
    runtime_timeout_seconds = int(
        runtime_contract.get("generated_simulation_timeout_seconds", 60) or 60
    )
    confirmatory_required_rows_only = True
    question_material = research_question_payload(question)
    upstream_research_contract = build_architect_upstream_research_contract(
        runtime_contract
    )
    theory_execution_preflight_packet = (
        _accepted_theory_preflight_packet(
            accepted_theory_preflight_context,
            theory_material=theory_material,
        )
        if accepted_theory_preflight_context
        else review_architect_theory_execution_preflight(
            semantic_reviewer=semantic_reviewer,
            question=question,
            runtime_contract=runtime_contract,
            theory_protocol_material=theory_material,
            prior_rejection_context=prior_rejection_context,
        )
    )
    frozen_source_rows = [
        dict(row)
        for row in frozen_rebinding.get("source_requirement_rows", []) or []
        if isinstance(row, Mapping)
    ]
    source_acceptance_mode = bool(
        not frozen_rebinding
        or (
            frozen_source_rows
            and all(
                row.get("evaluator_mode")
                == GENERATED_METRIC_SOURCE_ACCEPTANCE_MODE
                for row in frozen_source_rows
            )
        )
    )
    theory_anchor = _source_acceptance_theory_anchor(theory_material)
    acceptance_authority_catalog = (
        [theory_anchor]
        if source_acceptance_mode
        else generated_metric_acceptance_authority_catalog(
            question=question_material,
            runtime_contract=runtime_contract,
            theory_protocol_material=theory_material,
        )
    )
    acceptance_authority_prompt_catalog = (
        []
        if source_acceptance_mode and not frozen_rebinding
        else generated_metric_acceptance_authority_prompt_catalog(
            acceptance_authority_catalog
        )
    )
    if confirmatory_required_rows_only:
        acceptance_authority_prompt_catalog = [
            row
            for row in acceptance_authority_prompt_catalog
            if row.get("authority_kind") != "diagnostic_only"
        ]
    acceptance_authority_anchor_ids = [
        str(row["anchor_id"])
        for row in acceptance_authority_catalog
        if str(row.get("anchor_id", "") or "").strip()
    ]
    acceptance_authority_catalog_id = (
        "generated_metric_acceptance_authority_catalog:"
        + stable_hash(acceptance_authority_catalog)[:20]
    )
    requirement_prompt_schema = (
        generated_metric_requirement_prompt_schema()
        if frozen_rebinding
        else _source_acceptance_protocol_prompt_schema()
    )
    required_target_rows = (
        []
        if frozen_rebinding or source_acceptance_mode
        else [
            {
                "target_subsystems": list(
                    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                ),
                "runtime_bound": True,
                "at_least_one_required_acceptance_gate": True,
            }
        ]
    )
    prompt_payload = {
        "task": (
            "Rebind the exact frozen empirical acceptance requirements to the "
            "current revised theory without changing any gate semantics."
            if frozen_rebinding
            else "Author one compact pre-execution acceptance program that the "
            "SimulationEngineer will implement in ordinary Python or R."
        ),
        "question": question_material,
        "upstream_research_contract": upstream_research_contract,
        "theory_developer_protocol_material": theory_material,
        "accepted_implementation_interface_handoff": (
            implementation_interface
        ),
        "acceptance_authority_catalog_id": acceptance_authority_catalog_id,
        **(
            {"acceptance_authority_catalog": acceptance_authority_prompt_catalog}
            if acceptance_authority_prompt_catalog
            else {}
        ),
        "runtime_execution_capacity": {
            "max_runtime_replicates": max_runtime_replicates,
            "timeout_seconds": runtime_timeout_seconds,
            "scientific_replicate_count_model_authored": True,
        },
        "confirmatory_portfolio_row_budget": 1,
        "portfolio_schema": (
            requirement_prompt_schema
            if not frozen_rebinding
            else {}
        ),
        "confirmatory_required_rows_only": confirmatory_required_rows_only,
        "field_ownership": {
            "runtime_owned": list(
                (
                    "target_subsystems",
                    "required",
                    "acceptance_authority_kind",
                    "source_anchors",
                    "evaluator_mode",
                    "operator",
                    "aggregation",
                    "metric_value_kind",
                    "metric_path",
                )
            ),
            "model_authored_then_materialized": [
                "evaluator_id",
                "acceptance_protocol",
                "scientific_rationale",
                *(("required_runtime_replicates",) if not frozen_rebinding else ()),
            ],
            "binding_stage": "before_hash_validation_and_review",
            "runtime_selected_semantics": False,
        },
        **(
            {
                "target_namespace": (
                    generated_metric_requirement_target_namespace_contract()
                ),
                "metric_evaluation_semantics": (
                    generated_metric_evaluation_semantics_contract()
                ),
            }
            if frozen_rebinding and not source_acceptance_mode
            else {}
        ),
        "requirement_schema": requirement_prompt_schema,
        "required_target_rows": required_target_rows,
        "hard_requirements": [
            (
                "Author exactly one compact evaluator protocol. It may express "
                "arbitrary formulas, scenarios, and joint decisions, but must test "
                "only the decisive empirical claims of the current theory. Do not "
                "expand scenarios or moments into repeated schema rows."
            ),
            (
                "Write the complete scientific decision in acceptance_protocol, "
                "including every measured quantity, transformation, comparison, "
                "scenario aggregation, and required raw diagnostic. "
                "SimulationEngineer, not runtime, implements that protocol in "
                "ordinary Python or R and returns top-level acceptance_passed plus "
                "raw measurements and per-check diagnostics."
            ),
            (
                "Treat theory as scientific authority and the accepted implementation "
                "handoff only as an ABI. Runtime binds the exact theory hash and stable "
                "acceptance_passed interface; do not emit anchors, operators, metric "
                "paths, provenance labels, execution claims, or runtime-owned fields."
            ),
            (
                "Before outcomes, derive the replicate count and decision rule from "
                "attainable joint Monte Carlo uncertainty, tail behavior, "
                "dependence, and execution capacity. Include a quantitative uncertainty "
                "or sampling-error calculation; 'stringent but attainable' are not "
                "evidence. Work on the actual comparison scale and distinguish absolute "
                "error, relative error, standard/Monte Carlo standard error, and "
                "standardized error. The bare O(1/sqrt(n)) rate is not a dimensioned "
                "uncertainty estimate, and an asymptotic theorem does not alone justify "
                "a tight finite-run threshold. Report infeasibility instead of inventing "
                "precision; do not turn construction assumptions or analytic identities "
                "into unnecessary finite-run gates."
            ),
            (
                "Report infeasibility or an unresolved scientific ambiguity instead "
                "of inventing precision. The accepted protocol freezes before the "
                "confirmatory outcome and is empirical control, never theorem-proof "
                "evidence."
            ),
        ],
        "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    }
    if frozen_rebinding:
        frozen_rebinding_includes_field_authorities = (
            FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            in _frozen_metric_protocol_rebinding_mutable_fields(
                frozen_rebinding.get("source_requirement_rows", [])
            )
        )
        prompt_payload["frozen_metric_protocol_theory_rebinding"] = (
            frozen_rebinding
        )
        prompt_payload["hard_requirements"] = [
            (
                "Preserve exact ordered frozen requirement_id values. Emit only id, "
                "current source_anchors, acceptance_authority_rationale"
                + (
                    ", and field-bound gate_field_authorities"
                    if frozen_rebinding_includes_field_authorities
                    else ""
                )
                + "."
            ),
            (
                "Rebind only authority text to current theory. "
                + (
                    "Preserve every ordered field and authority_kind. "
                    if frozen_rebinding_includes_field_authorities
                    else ""
                )
                + "Runtime reconstructs all omitted frozen gate semantics."
            ),
            (
                "Use exact current catalog anchors without outcome access, gate "
                "changes, or reinterpretation. Independent review remains required; "
                "these empirical controls are never theorem-proof evidence."
            ),
        ]
        prompt_payload["requirement_schema"] = {
            "requirement_id": "exact frozen requirement_id",
            "source_anchors": ["exact current acceptance-authority anchor_id"],
            "acceptance_authority_rationale": "current-theory binding rationale",
            **(
                {
                    "gate_field_authorities": [
                        "preserve field and authority_kind; revise only anchors "
                        "and rationale"
                    ]
                }
                if frozen_rebinding_includes_field_authorities
                else {}
            ),
        }
        prompt_payload["required_target_rows"] = []
    semantic_review_history: list[dict[str, Any]] = []
    prior_authoring_packet: dict[str, Any] = {}
    prior_review_packet: dict[str, Any] = {}
    carry_forward = (
        dict(prior_rejection_context)
        if isinstance(prior_rejection_context, Mapping)
        else {}
    )
    carried_review = carry_forward.get("final_review", {})
    carry_forward_valid = bool(
        carry_forward.get("artifact_kind")
        == "RuntimeArchitectMetricProtocolPriorRejectionContext"
        and carry_forward.get("execution_results_available") is False
        and carry_forward.get("current_candidate_acceptance_eligible") is False
        and str(
            carry_forward.get("current_source_theory_packet_id", "") or ""
        )
        == str(theory_material.get("source_theory_packet_id", "") or "")
        and str(
            carry_forward.get("current_source_theory_packet_hash", "") or ""
        )
        == str(theory_material.get("source_theory_packet_hash", "") or "")
        and isinstance(carried_review, Mapping)
        and carried_review.get("empirical_metric_requirements")
    )
    cumulative_finding_ledger: list[dict[str, Any]] = []
    if carry_forward_valid:
        cumulative_finding_ledger = [
            dict(row)
            for row in carry_forward.get("cumulative_finding_ledger", []) or []
            if isinstance(row, Mapping)
        ]
        if not cumulative_finding_ledger:
            carried_history = carry_forward.get("semantic_review_history", [])
            if not isinstance(carried_history, list) or not carried_history:
                carried_history = [dict(carried_review)]
            cumulative_finding_ledger = (
                metric_protocol_finding_ledger_from_review_history(
                    question_id=question.id,
                    semantic_review_history=carried_history,
                )
            )
        prior_authoring_packet = {
            "packet_id": str(
                carried_review.get("authoring_packet_id", "") or ""
            ),
            "empirical_metric_requirement_set_id": str(
                carried_review.get(
                    "empirical_metric_requirement_set_id", ""
                )
                or ""
            ),
            "empirical_metric_requirements": [
                dict(row)
                for row in carried_review.get(
                    "empirical_metric_requirements", []
                )
                if isinstance(row, Mapping)
            ],
        }
        prior_review_packet = {
            "packet_id": str(
                carried_review.get("semantic_review_packet_id", "") or ""
            ),
            "requirement_reviews": [
                dict(row)
                for row in carried_review.get("requirement_reviews", []) or []
                if isinstance(row, Mapping)
            ],
            "portfolio_review": dict(
                carried_review.get("portfolio_review", {}) or {}
            ),
            "findings": [
                dict(row)
                for row in carried_review.get("findings", []) or []
                if isinstance(row, Mapping)
            ],
        }
    max_semantic_revisions = max(
        0, int(config.metric_semantic_reviewer_max_revisions or 0)
    )
    metric_workspace_messages: tuple[Mapping[str, Any], ...] = ()
    metric_workspace_document = ""
    metric_workspace_dir = (
        metric_protocol_workspace_root.resolve()
        / stable_hash(
            [
                question.id,
                theory_material.get("source_theory_packet_id", ""),
                theory_material.get("source_theory_packet_hash", ""),
                implementation_interface.get("handoff_id", ""),
                frozen_rebinding.get("source_requirement_set_id", ""),
            ]
        )[:20]
        if metric_protocol_workspace_root is not None
        else None
    )
    metric_workspace_session_id = (
        "metric-protocol:"
        + stable_hash(
            [
                question.id,
                theory_material.get("source_theory_packet_id", ""),
                implementation_interface.get("handoff_id", ""),
            ]
        )[:24]
    )
    for revision_index in range(max_semantic_revisions + 1):
        active_finding_ledger = active_metric_protocol_finding_ledger(
            cumulative_finding_ledger
        )
        active_finding_ids = [
            str(row.get("finding_id", "") or "")
            for row in active_finding_ledger
            if str(row.get("finding_id", "") or "").strip()
        ]
        active_finding_ledger_fingerprint = (
            metric_protocol_finding_ledger_fingerprint(active_finding_ledger)
            if active_finding_ledger
            else ""
        )
        candidate_prompt_payload = dict(prompt_payload)
        if prior_review_packet:
            candidate_prompt_payload["independent_semantic_review_feedback"] = (
                model_observations_without_repair_recipes(
                    {
                        "revision_index": revision_index,
                        "rejected_authoring_packet_id": str(
                            prior_authoring_packet.get("packet_id", "") or ""
                        ),
                        "rejected_requirement_set_id": str(
                            prior_authoring_packet.get(
                                "empirical_metric_requirement_set_id", ""
                            )
                            or ""
                        ),
                        "rejected_empirical_metric_requirements": (
                            []
                            if metric_workspace_document
                            else [
                                dict(row)
                                for row in prior_authoring_packet.get(
                                    "empirical_metric_requirements", []
                                )
                                if isinstance(row, Mapping)
                            ]
                        ),
                        "semantic_review_packet_id": str(
                            prior_review_packet.get("packet_id", "") or ""
                        ),
                        "requirement_reviews": list(
                            prior_review_packet.get("requirement_reviews", []) or []
                        ),
                        "portfolio_review": dict(
                            prior_review_packet.get("portfolio_review", {}) or {}
                        ),
                        "findings": list(
                            prior_review_packet.get("findings", []) or []
                        ),
                        "active_prior_finding_ledger": active_finding_ledger,
                        "required_prior_finding_ids": active_finding_ids,
                        "active_prior_finding_ledger_fingerprint": (
                            active_finding_ledger_fingerprint
                        ),
                        "cross_theory_revision_context": (
                            {
                                "source_rejection_manifest_id": carry_forward.get(
                                    "source_rejection_manifest_id", ""
                                ),
                                "source_rejection_manifest_hash": carry_forward.get(
                                    "source_rejection_manifest_hash", ""
                                ),
                                "prior_source_theory_packet_id": carried_review.get(
                                    "source_theory_packet_id", ""
                                ),
                                "prior_source_theory_packet_hash": carried_review.get(
                                    "source_theory_packet_hash", ""
                                ),
                                "current_source_theory_packet_id": str(
                                    theory_material.get(
                                        "source_theory_packet_id", ""
                                    )
                                    or ""
                                ),
                                "current_source_theory_packet_hash": str(
                                    theory_material.get(
                                        "source_theory_packet_hash", ""
                                    )
                                    or ""
                                ),
                                "boundary": str(
                                    carry_forward.get("boundary", "") or ""
                                ),
                            }
                            if carry_forward
                            else {}
                        ),
                    },
                    preserve_exact_keys=(
                        ("rejected_empirical_metric_requirements",)
                        if not metric_workspace_document
                        else ()
                    ),
                )
            )
        (
            model_prompt_payload,
            prompt_projection,
        ) = _compact_metric_authoring_prompt_payload(
            candidate_prompt_payload
        )
        model_visible_turn_payload = (
            {
                "independent_semantic_review_feedback": deepcopy(
                    candidate_prompt_payload.get(
                        "independent_semantic_review_feedback", {}
                    )
                ),
                "current_metric_protocol_document_sha256": (
                    _metric_protocol_document_sha256(
                        metric_workspace_document
                    )
                    if metric_workspace_document
                    else ""
                ),
                "current_metric_protocol_document_available_through_tools": True,
                "revision_rule": (
                    "Resolve the independent findings in the existing document. "
                    "Edit only what is needed, preserve unrelated accepted content, "
                    "and commit the resulting exact document SHA-256."
                ),
            }
            if metric_workspace_messages
            else model_prompt_payload
        )
        request_user_prompt = json.dumps(
            model_visible_turn_payload,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
        workspace_user_message = (
            (
                "Author "
                + (
                    "metric_protocol.json"
                    if frozen_rebinding
                    else "metric_protocol.md"
                )
                + " from the following pre-execution "
                "scientific context. Read the runtime-owned structural scaffold, "
                "edit its external bytes, and commit the exact resulting SHA-256"
                + (
                    " plus the compact evaluator metadata"
                    if not frozen_rebinding
                    else ""
                )
                + ".\n\n"
            )
            if not metric_workspace_messages
            else (
                "The independent pre-outcome reviewer rejected the exact current "
                "metric protocol. The authoritative document remains in your "
                "workspace. Read it if needed, edit it against its current hash using "
                "the observations below, and commit the resulting SHA-256. Preserve "
                "unrelated accepted content.\n\n"
            )
        ) + request_user_prompt

        def extract_authoring_payload(raw_text: str) -> dict[str, Any]:
            payload = extract_json_object(
                raw_text,
                label="LLM Architect metric-requirement packet",
            )
            expected_top_level_keys = (
                {"empirical_metric_requirements"}
                if frozen_rebinding
                else set(_source_acceptance_protocol_prompt_schema())
            )
            observed_top_level_keys = set(payload)
            model_aci_errors: list[str] = []
            if observed_top_level_keys != expected_top_level_keys:
                model_aci_errors.append(
                    "metric_protocol.json top-level keys must be exactly "
                    f"{sorted(expected_top_level_keys)!r}; observed "
                    f"{sorted(observed_top_level_keys)!r}"
                )
            if frozen_rebinding:
                payload["_runtime_model_aci_errors"] = model_aci_errors
                return payload
            materialized, row_errors = _materialize_source_acceptance_protocol(
                payload,
                theory_anchor_id=str(theory_anchor["anchor_id"]),
            )
            materialized_rows = [materialized]
            model_aci_errors.extend(row_errors)
            (
                payload["empirical_metric_requirements"],
                omitted_nonrequired_rows,
            ) = _confirmatory_metric_requirement_rows(
                materialized_rows,
            )
            payload["_runtime_omitted_nonrequired_requirements"] = (
                omitted_nonrequired_rows
            )
            payload["_runtime_model_aci_errors"] = model_aci_errors
            return payload

        def build_packet(
            payload: Mapping[str, Any],
        ) -> dict[str, Any]:
            requirements = payload.get("empirical_metric_requirements", [])
            omitted_nonrequired_rows = [
                dict(row)
                for row in payload.get(
                    "_runtime_omitted_nonrequired_requirements", []
                )
                if isinstance(row, Mapping)
            ]
            model_aci_errors = [
                str(error)
                for error in payload.get("_runtime_model_aci_errors", []) or []
                if str(error).strip()
            ]
            frozen_binding_errors: list[str] = []
            if frozen_rebinding:
                (
                    requirement_rows,
                    frozen_binding_errors,
                ) = _reconstruct_frozen_metric_protocol_requirements(
                    binding_rows=requirements,
                    rebinding_context=frozen_rebinding,
                )
                requirement_rows = [
                    (
                        materialize_generated_metric_gate_field_authorities(
                            row
                        )
                        if "gate_field_authorities" in row
                        else dict(row)
                    )
                    for row in requirement_rows
                ]
            else:
                requirement_rows = []
                for row in requirements:
                    if not isinstance(row, Mapping):
                        continue
                    requirement_rows.append(
                        materialize_generated_metric_gate_field_authorities(
                            dict(row)
                        )
                    )
                (
                    requirement_rows,
                    newly_omitted_nonrequired_rows,
                ) = _confirmatory_metric_requirement_rows(
                    requirement_rows,
                )
                omitted_nonrequired_rows.extend(
                    newly_omitted_nonrequired_rows
                )
            (
                shared_runtime_replicates,
                replicate_design_errors,
            ) = generated_metric_shared_runtime_replicates(
                requirement_rows,
                max_runtime_replicates=max_runtime_replicates,
            )
            model_aci_errors.extend(replicate_design_errors)
            declared_runtime_replicates = payload.get(
                "required_runtime_replicates"
            )
            if (
                not frozen_rebinding
                and shared_runtime_replicates
                != declared_runtime_replicates
            ):
                model_aci_errors.append(
                    "portfolio required_runtime_replicates was not preserved "
                    "when materializing evaluator rows"
                )
            model_authored_runtime_replicates = (
                shared_runtime_replicates
                if frozen_rebinding
                else declared_runtime_replicates
            )
            parent_packet_id = str(
                prior_authoring_packet.get("packet_id", "") or ""
            )
            return {
                "schema_version": ARCHITECT_METRIC_REQUIREMENT_AUTHORING_SCHEMA_VERSION,
                "artifact_kind": "ArchitectMetricRequirementAuthoringPacket",
                "packet_id": (
                    "architect_metric_requirement_authoring:"
                    + stable_hash(
                        [
                            question.id,
                            requirement_rows,
                            revision_index,
                            parent_packet_id,
                            implementation_interface.get("handoff_id", ""),
                        ]
                    )[:20]
                ),
                "question_id": question.id,
                "source_theory_packet_id": str(
                    theory_material.get("source_theory_packet_id", "") or ""
                ),
                "source_theory_packet_hash": str(
                    theory_material.get("source_theory_packet_hash", "") or ""
                ),
                "theory_execution_preflight_packet_id": str(
                    theory_execution_preflight_packet.get("packet_id", "") or ""
                ),
                "theory_execution_preflight_packet_hash": (
                    stable_hash(theory_execution_preflight_packet)
                    if theory_execution_preflight_packet
                    else ""
                ),
                "theory_execution_preflight_model": str(
                    theory_execution_preflight_packet.get("model", "") or ""
                ),
                "theory_execution_preflight_model_tier": str(
                    theory_execution_preflight_packet.get("model_tier", "")
                    or ""
                ),
                "theory_execution_preflight_retry_attempts": int(
                    theory_execution_preflight_packet.get(
                        "structured_output_retry_attempts", 0
                    )
                    or 0
                ),
                "theory_execution_preflight_proof_evidence_status": str(
                    theory_execution_preflight_packet.get(
                        "proof_evidence_status", ""
                    )
                    or ""
                ),
                "accepted_implementation_interface_handoff_id": str(
                    implementation_interface.get("handoff_id", "") or ""
                ),
                "accepted_implementation_interface_handoff_hash": (
                    stable_hash(implementation_interface)
                    if implementation_interface
                    else ""
                ),
                "accepted_implementation_execution_results_observed": False,
                "acceptance_authority_catalog_id": (
                    acceptance_authority_catalog_id
                ),
                "acceptance_authority_catalog_fingerprint": stable_hash(
                    acceptance_authority_catalog
                ),
                "source_agent": "ArchitectMetricContractPlanner",
                "provider_name": str(
                    getattr(provider, "provider_name", "")
                    or config.provider_name
                ),
                "model": request_model,
                "model_tier": config.model_tier,
                "semantic_review_revision_index": revision_index,
                "parent_authoring_packet_id": parent_packet_id,
                "semantic_review_feedback_packet_id": str(
                    prior_review_packet.get("packet_id", "") or ""
                ),
                "revision_target_finding_ids": active_finding_ids,
                "revision_target_finding_ledger_fingerprint": (
                    active_finding_ledger_fingerprint
                ),
                "model_authored_runtime_replicates": (
                    model_authored_runtime_replicates
                ),
                "runtime_execution_capacity": {
                    "max_runtime_replicates": max_runtime_replicates,
                    "timeout_seconds": runtime_timeout_seconds,
                },
                "confirmatory_required_rows_only": (
                    confirmatory_required_rows_only
                ),
                "model_requirement_transport": (
                    "model_owned_source_acceptance_protocol_v1"
                    if not frozen_rebinding
                    else "frozen_authority_rebinding"
                ),
                "model_requirement_transport_errors": model_aci_errors,
                "omitted_nonrequired_requirements": (
                    omitted_nonrequired_rows
                ),
                "empirical_metric_requirements": requirement_rows,
                "empirical_metric_requirement_set_id": (
                    generated_metric_requirement_set_id(requirement_rows)
                ),
                "frozen_metric_protocol_rebinding": bool(
                    frozen_rebinding
                ),
                "frozen_source_requirement_set_id": str(
                    frozen_rebinding.get("source_requirement_set_id", "")
                    or ""
                ),
                "frozen_gate_semantics_preserved": bool(
                    frozen_rebinding
                ),
                "frozen_rebinding_binding_errors": frozen_binding_errors,
                "proof_evidence_status": (
                    "ARCHITECT_METRIC_REQUIREMENT_AUTHORING_NOT_PROOF_EVIDENCE"
                ),
                "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
            }

        def validate_packet(packet: Mapping[str, Any]) -> list[str]:
            errors = [
                str(error)
                for error in packet.get(
                    "frozen_rebinding_binding_errors", []
                )
                if str(error).strip()
            ]
            model_authored_runtime_replicates = packet.get(
                "model_authored_runtime_replicates"
            )
            if (
                isinstance(model_authored_runtime_replicates, bool)
                or not isinstance(model_authored_runtime_replicates, int)
                or model_authored_runtime_replicates <= 0
            ):
                errors.append(
                    "metric portfolio requires one positive model-authored "
                    "required_runtime_replicates value"
                )
                expected_runtime_replicates = None
            else:
                expected_runtime_replicates = model_authored_runtime_replicates
            if (
                not frozen_rebinding
                and len(
                    packet.get("empirical_metric_requirements", []) or []
                )
                > MAX_CONFIRMATORY_METRIC_REQUIREMENTS
            ):
                errors.append(
                    "confirmatory metric portfolio exceeds the shared review "
                    f"budget of {MAX_CONFIRMATORY_METRIC_REQUIREMENTS} rows"
                )
            if (
                not frozen_rebinding
                and len(packet.get("empirical_metric_requirements", []) or [])
                != 1
            ):
                errors.append(
                    "fresh source-acceptance authoring must materialize exactly one "
                    "evaluator requirement"
                )
            if implementation_interface:
                if str(
                    packet.get(
                        "accepted_implementation_interface_handoff_id", ""
                    )
                    or ""
                ) != str(implementation_interface.get("handoff_id", "") or ""):
                    errors.append(
                        "accepted implementation interface handoff identity mismatch"
                    )
                if str(
                    packet.get(
                        "accepted_implementation_interface_handoff_hash", ""
                    )
                    or ""
                ) != stable_hash(implementation_interface):
                    errors.append(
                        "accepted implementation interface handoff hash mismatch"
                    )
                if packet.get(
                    "accepted_implementation_execution_results_observed"
                ) is not False:
                    errors.append(
                        "metric authoring cannot observe implementation execution results"
                    )
            errors.extend(
                str(error)
                for error in packet.get(
                    "model_requirement_transport_errors", []
                )
                or []
                if str(error).strip()
            )
            errors.extend(
                validate_generated_metric_requirements(
                    packet.get("empirical_metric_requirements", []),
                    required_target_subsystems=(
                        GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                    ),
                    expected_runtime_replicates=expected_runtime_replicates,
                    require_acceptance_authority=True,
                    acceptance_authority_catalog=acceptance_authority_catalog,
                    require_gate_field_authorities=not bool(
                        frozen_rebinding
                    )
                    or any(
                        isinstance(row, Mapping)
                        and "gate_field_authorities" in row
                        for row in frozen_rebinding.get(
                            "source_requirement_rows", []
                        )
                    ),
                )
            )
            if frozen_rebinding:
                errors.extend(
                    _frozen_metric_protocol_rebinding_errors(
                        candidate_requirements=packet.get(
                            "empirical_metric_requirements", []
                        ),
                        rebinding_context=frozen_rebinding,
                    )
                )
            return errors

        with agent_runtime_substage(
            "architect_metric_requirement_author",
            metadata={
                "revision_index": revision_index,
                "model_tier": config.model_tier,
                "workspace_transport": METRIC_PROTOCOL_WORKSPACE_TRANSPORT,
                "full_packet_regeneration_required": False,
                "active_prior_finding_count": len(active_finding_ids),
            },
        ):
            def build_validated_workspace_packet(
                document_content: str,
            ) -> tuple[dict[str, Any] | None, list[str]]:
                payload = extract_authoring_payload(document_content)
                packet = build_packet(payload)
                return packet, validate_packet(packet)

            workspace_result = _run_metric_protocol_workspace(
                provider=provider,
                config=config,
                request_model=request_model,
                user_message=workspace_user_message,
                build_validated_packet=build_validated_workspace_packet,
                prior_messages=metric_workspace_messages,
                prior_document_content=metric_workspace_document,
                initial_document_content=(
                    METRIC_PROTOCOL_WORKSPACE_FROZEN_INITIAL_DOCUMENT
                    if frozen_rebinding
                    else METRIC_PROTOCOL_WORKSPACE_SOURCE_INITIAL_DOCUMENT
                ),
                workspace_dir=metric_workspace_dir,
                session_id=metric_workspace_session_id,
                revision_index=revision_index,
                source_acceptance_mode=not bool(frozen_rebinding),
            )
        loop = workspace_result.loop
        metric_workspace_messages = loop.messages
        metric_workspace_document = workspace_result.document_content
        authoring_packet = dict(workspace_result.packet)
        authoring_packet["provider_name"] = loop.provider
        authoring_packet["model"] = loop.model or request_model
        authoring_packet["model_requirement_transport"] = (
            METRIC_PROTOCOL_WORKSPACE_TRANSPORT
        )
        authoring_packet["metric_protocol_workspace"] = {
            "artifact_kind": "MetricProtocolWorkspaceEvidence",
            "transport": METRIC_PROTOCOL_WORKSPACE_TRANSPORT,
            "source_owner": "MetricProtocolSourceOwner",
            "document_body_in_terminal_tool": False,
            "revision_index": revision_index,
            "document_sha256": _metric_protocol_document_sha256(
                metric_workspace_document
            ),
            "document_chars": len(metric_workspace_document),
            "relative_document_path": workspace_result.relative_document_path,
            "client_tool_session_ref": dict(workspace_result.session_ref),
            "segment_turns": loop.turns,
            "segment_tool_calls": loop.tool_calls,
            "segment_runtime_executed_tool_calls": (
                loop.runtime_executed_tool_calls
            ),
            "transcript_fingerprint": loop.transcript_fingerprint,
            "provider_usage": dict(loop.provider_usage),
            "prompt_projection": dict(prompt_projection),
            "runtime_edited_content": False,
            "same_source_owner_session": True,
            "full_packet_regeneration_required": False,
            "proof_evidence_status": (
                "ARCHITECT_METRIC_REQUIREMENT_AUTHORING_NOT_PROOF_EVIDENCE"
            ),
        }
        authoring_packet_hash = stable_hash(authoring_packet)
        review_material = {
            "review_stage": "pre_execution_metric_contract_review",
            "execution_results_available": False,
            "model_authored_runtime_replicates": authoring_packet.get(
                "model_authored_runtime_replicates"
            ),
            "runtime_execution_capacity": dict(
                authoring_packet.get("runtime_execution_capacity", {})
            ),
            "target_namespace": (
                generated_metric_requirement_target_namespace_contract()
            ),
            "metric_evaluation_semantics": (
                generated_metric_evaluation_semantics_contract()
            ),
            "requirement_schema": generated_metric_requirement_json_schema(
                require_acceptance_authority=True,
                authority_anchor_ids=acceptance_authority_anchor_ids,
            ),
            "acceptance_authority_catalog_id": acceptance_authority_catalog_id,
            "acceptance_authority_catalog": acceptance_authority_catalog,
            "runtime_contract_authority": {
                "schema_version": 1,
                "runtime_owned": True,
                "allowed_retraction_status": (
                    "RETRACTED_RUNTIME_CONTRACT_CONFLICT"
                ),
                "allowed_retraction_evidence_ids": list(
                    ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS
                ),
                "retraction_boundary": (
                    "This status only corrects a reviewer finding that conflicts "
                    "with the supplied runtime schema or evaluator order. It cannot "
                    "waive a statistical, theory, identifiability, feasibility, or "
                    "calibration defect."
                ),
            },
            "theory_developer_protocol_material": theory_material,
            "upstream_research_contract": upstream_research_contract,
            "accepted_implementation_interface_handoff": (
                implementation_interface
            ),
            "frozen_metric_protocol_theory_rebinding": frozen_rebinding,
            "active_prior_finding_ledger": active_finding_ledger,
            "active_prior_finding_ledger_fingerprint": (
                active_finding_ledger_fingerprint
            ),
            "empirical_metric_requirements": [
                dict(row)
                for row in authoring_packet.get(
                    "empirical_metric_requirements", []
                )
                if isinstance(row, Mapping)
            ],
            "pre_execution_invariants": [
                "No confirmatory simulation output, empirical metric result, or acceptance decision exists yet.",
                "A reviewed AlgorithmEngineer source artifact may exist, but its smoke diagnostics cannot tune statistical thresholds.",
                "The reviewer cannot require unavailable pilot results as a prerequisite; theory-grounded finite-sample uncertainty may remain advisory when the frozen experiment is designed to measure it.",
                "Review the candidate contract without proposing a post-result relaxation.",
                "Every empirical-evaluation target subsystem must remain covered by at least one required row.",
                (
                    "When frozen_metric_protocol_theory_rebinding is present, every "
                    "gate-defining field is immutable; review only whether the exact "
                    "frozen portfolio is semantically supported by the revised "
                    "theory and current authority bindings."
                ),
            ],
        }
        review_material = (
            architect_metric_review_material_with_runtime_evaluator_certificate(
                review_material
            )
        )
        trusted_review_lineage = {
            "authoring_packet_id": str(authoring_packet["packet_id"]),
            "authoring_packet_hash": authoring_packet_hash,
            "empirical_metric_requirement_set_id": str(
                authoring_packet["empirical_metric_requirement_set_id"]
            ),
            "source_theory_packet_id": str(
                theory_material.get("source_theory_packet_id", "") or ""
            ),
            "source_theory_packet_hash": str(
                theory_material.get("source_theory_packet_hash", "") or ""
            ),
            "acceptance_authority_catalog_id": acceptance_authority_catalog_id,
            "acceptance_authority_catalog_fingerprint": stable_hash(
                acceptance_authority_catalog
            ),
            "source_agent": str(authoring_packet["source_agent"]),
            "source_model": str(authoring_packet["model"]),
            "source_model_tier": str(authoring_packet["model_tier"]),
            "frozen_metric_protocol_rebinding": bool(frozen_rebinding),
            "frozen_source_requirement_set_id": str(
                frozen_rebinding.get("source_requirement_set_id", "")
                or ""
            ),
            "frozen_gate_semantics_preserved": bool(frozen_rebinding),
        }
        with agent_runtime_substage(
            "architect_metric_semantic_reviewer",
            metadata={
                "revision_index": revision_index,
                "model_tier": str(
                    getattr(
                        getattr(semantic_reviewer, "config", None),
                        "model_tier",
                        "",
                    )
                    or ""
                ),
                "blinded_independent_invocation": True,
            },
        ):
            try:
                semantic_review_packet = semantic_reviewer.review(
                    question=question,
                    review_material=review_material,
                    trusted_lineage=trusted_review_lineage,
                    **(
                        {"theory_scratchpad": theory_scratchpad}
                        if theory_scratchpad is not None
                        else {}
                    ),
                )
            except PacketValidationError as exc:
                raise ArchitectMetricSemanticReviewPacketValidationError(
                    cause=exc,
                    authoring_packet=authoring_packet,
                    revision_index=revision_index,
                    trusted_review_lineage=trusted_review_lineage,
                    review_material_fingerprint=stable_hash(review_material),
                    semantic_review_history=semantic_review_history,
                ) from exc
        review_packet_hash = stable_hash(semantic_review_packet)
        routed_current_findings = [
            dict(row)
            for row in semantic_review_packet.get("findings", []) or []
            if isinstance(row, Mapping)
        ]
        routed_current_findings = (
            bind_architect_metric_finding_evidence_identities(
                findings=routed_current_findings,
                review_material=review_material,
                prior_ledger=cumulative_finding_ledger,
            )
        )
        cumulative_finding_ledger = update_metric_protocol_finding_ledger(
            question_id=question.id,
            prior_ledger=cumulative_finding_ledger,
            prior_finding_reviews=semantic_review_packet.get(
                "prior_finding_reviews", []
            ),
            current_findings=routed_current_findings,
            current_verdict=str(
                semantic_review_packet.get("overall_verdict", "") or ""
            ),
            review_packet_id=str(semantic_review_packet["packet_id"]),
            revision_index=revision_index,
        )
        active_finding_ledger_after_review = (
            active_metric_protocol_finding_ledger(cumulative_finding_ledger)
        )
        current_finding_ids = {
            str(row.get("finding_id", "") or "")
            for row in routed_current_findings
            if str(row.get("finding_id", "") or "").strip()
        }
        carried_findings = []
        for ledger_row in active_finding_ledger_after_review:
            finding_id = str(ledger_row.get("finding_id", "") or "")
            finding = ledger_row.get("finding", {})
            if finding_id in current_finding_ids or not isinstance(
                finding, Mapping
            ):
                continue
            carried = dict(finding)
            carried["carried_forward_finding_id"] = finding_id
            carried_findings.append(carried)
        routed_findings = [*routed_current_findings, *carried_findings]
        for prior_history_row in semantic_review_history:
            prior_history_row.pop("cumulative_finding_ledger", None)
        semantic_review_history.append(
            {
                "revision_index": revision_index,
                "authoring_packet_id": str(authoring_packet["packet_id"]),
                "authoring_packet_hash": authoring_packet_hash,
                "empirical_metric_requirement_set_id": str(
                    authoring_packet["empirical_metric_requirement_set_id"]
                ),
                "source_theory_packet_id": str(
                    theory_material.get("source_theory_packet_id", "") or ""
                ),
                "source_theory_packet_hash": str(
                    theory_material.get("source_theory_packet_hash", "") or ""
                ),
                "acceptance_authority_catalog_id": (
                    acceptance_authority_catalog_id
                ),
                "acceptance_authority_catalog_fingerprint": stable_hash(
                    acceptance_authority_catalog
                ),
                "empirical_metric_requirement_count": len(
                    authoring_packet.get("empirical_metric_requirements", [])
                    or []
                ),
                "empirical_metric_requirements_fingerprint": stable_hash(
                    [
                        dict(row)
                        for row in authoring_packet.get(
                            "empirical_metric_requirements", []
                        )
                        or []
                        if isinstance(row, Mapping)
                    ]
                ),
                "metric_protocol_workspace": deepcopy(
                    dict(
                        authoring_packet.get(
                            "metric_protocol_workspace", {}
                        )
                    )
                ),
                "semantic_review_packet_id": str(
                    semantic_review_packet["packet_id"]
                ),
                "semantic_review_packet_hash": review_packet_hash,
                "semantic_review_model": str(
                    semantic_review_packet.get("model", "") or ""
                ),
                "semantic_review_model_tier": str(
                    semantic_review_packet.get("model_tier", "") or ""
                ),
                "independent_agent": bool(
                    semantic_review_packet.get("independent_agent")
                ),
                "independent_invocation": bool(
                    semantic_review_packet.get("independent_invocation")
                ),
                "independent_model": bool(
                    semantic_review_packet.get("independent_model")
                ),
                "independent_model_tier": bool(
                    semantic_review_packet.get("independent_model_tier")
                ),
                "overall_verdict": str(
                    semantic_review_packet.get("overall_verdict", "") or ""
                ),
                "revision_target_finding_ids": list(
                    authoring_packet.get("revision_target_finding_ids", []) or []
                ),
                "revision_target_finding_ledger_fingerprint": str(
                    authoring_packet.get(
                        "revision_target_finding_ledger_fingerprint", ""
                    )
                    or ""
                ),
                "prior_finding_reviews": [
                    dict(row)
                    for row in semantic_review_packet.get(
                        "prior_finding_reviews", []
                    )
                    if isinstance(row, Mapping)
                ],
                "cumulative_finding_ledger": [
                    dict(row) for row in cumulative_finding_ledger
                ],
                "cumulative_finding_ledger_fingerprint": (
                    metric_protocol_finding_ledger_fingerprint(
                        cumulative_finding_ledger
                    )
                    if cumulative_finding_ledger
                    else ""
                ),
                "active_unresolved_finding_ids": [
                    str(row.get("finding_id", "") or "")
                    for row in active_finding_ledger_after_review
                    if str(row.get("finding_id", "") or "").strip()
                ],
                "carried_forward_finding_ids": [
                    str(row.get("carried_forward_finding_id", "") or "")
                    for row in carried_findings
                    if str(row.get("carried_forward_finding_id", "") or "").strip()
                ],
                "requirement_reviews": [
                    dict(row)
                    for row in semantic_review_packet.get(
                        "requirement_reviews", []
                    )
                    or []
                    if isinstance(row, Mapping)
                ],
                "portfolio_review": dict(
                    semantic_review_packet.get("portfolio_review", {}) or {}
                ),
                "findings": routed_findings,
                "proof_evidence_status": (
                    "ARCHITECT_METRIC_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        if semantic_review_packet.get("overall_verdict") == "ACCEPT":
            authoring_packet["semantic_review_status"] = "ACCEPT"
            authoring_packet["semantic_review_packet"] = semantic_review_packet
            authoring_packet["semantic_review_packet_hash"] = review_packet_hash
            authoring_packet["semantic_review_revision_count"] = revision_index
            authoring_packet["semantic_review_history"] = semantic_review_history
            authoring_packet["cumulative_finding_ledger"] = [
                dict(row) for row in cumulative_finding_ledger
            ]
            authoring_packet["cumulative_finding_ledger_fingerprint"] = (
                metric_protocol_finding_ledger_fingerprint(
                    cumulative_finding_ledger
                )
                if cumulative_finding_ledger
                else ""
            )
            authoring_packet["semantic_review_boundary"] = (
                ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY
            )
            return authoring_packet
        prior_authoring_packet = authoring_packet
        prior_review_packet = {
            **dict(semantic_review_packet),
            "findings": routed_findings,
        }

    raise ArchitectMetricSemanticReviewRejected(
        question_id=question.id,
        semantic_review_history=semantic_review_history,
        source_theory_packet_id=str(
            theory_material.get("source_theory_packet_id", "") or ""
        ),
        source_theory_packet_hash=str(
            theory_material.get("source_theory_packet_hash", "") or ""
        ),
    )

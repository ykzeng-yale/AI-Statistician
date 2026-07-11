from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .exact_semantic_definition_policy import (
    compact_exact_semantic_placeholder_key,
    exact_semantic_definition_placeholder_policy,
)
from .fingerprint import stable_hash
from .llm_json_repair import (
    PacketValidationError,
    extract_json_object,
    generate_validated_json_packet,
)
from .model_backend import (
    GeneratorBackend,
    GeneratorRequest,
    SUPPORTED_LIVE_GENERATOR_PROVIDERS,
    is_live_generator_backend,
    normalize_generator_provider_name,
    resolve_generator_model,
)
from .pseudo_formalization import (
    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
    PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_STATUS_BY_TARGET_LANE,
    PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
    PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
    PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
    pseudo_formal_verification_method_contract,
)
from .research_architect import KERNEL_PROOF_BOUNDARY
from .source_theorem_exact_semantic_definition_lean_repair_executor import (
    AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
)
from .source_theorem_exact_semantic_definition_source_lookup import (
    EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS,
    exact_semantic_definition_required_anchor_bindings,
    exact_semantic_definition_source_binders_from_context,
)


ARTIFACT_KIND = "SourceTheoremExactSemanticDefinitionAuthoringWorkerManifest"
MATERIALIZER_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionAuthoringCandidateMaterializerManifest"
)
PROMPT_PACKET_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionAuthoringPromptPacket"
)
CANDIDATE_PACKET_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionAuthoringCandidatePacket"
)
MATERIALIZATION_ROW_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionAuthoringCandidateMaterializationRow"
)
EXTERNAL_EXPORT_REVIEW_PACKET_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionExternalLLMExportReviewPacket"
)
LEARNING_ARTIFACT_KIND = "SourceTheoremExactSemanticDefinitionAuthoringLearningRow"
AUTHORING_WORKER_PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_AUTHORING_WORKER_NOT_PROOF_EVIDENCE"
)
CANDIDATE_PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_NOT_PROOF_EVIDENCE"
)
MATERIALIZER_PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_MATERIALIZATION_NOT_PROOF_EVIDENCE"
)
EXTERNAL_EXPORT_REVIEW_PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_EXTERNAL_LLM_EXPORT_REVIEW_NOT_PROOF_EVIDENCE"
)
STRUCTURAL_REFORMULATION_FAILURE_CLASSIFICATION = (
    "exact_semantic_definition_structural_reformulation_required"
)
STRUCTURAL_REFORMULATION_QUEUE_STATUS = (
    "PENDING_EXACT_SEMANTIC_DEFINITION_STRUCTURAL_REFORMULATION"
)
AUTHORING_FOLLOWUP_QUEUE_STATUSES = {
    "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY",
    "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR",
    STRUCTURAL_REFORMULATION_QUEUE_STATUS,
}
LEARNING_TASK = "source_theorem_exact_semantic_definition_authoring_worker"
MATERIALIZER_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_authoring_candidate_materialization"
)
EXTERNAL_EXPORT_REVIEW_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_external_llm_export_review"
)
BOUNDARY = (
    "Exact semantic-definition authoring worker rows are LLM/ProofEngineer "
    "authoring proposals only. They are not source theorem proof, not semantic "
    "definition kernel evidence, and not proof-body evidence. A candidate must "
    "be materialized and checked by local Lean/AXLE before it can be used by "
    "source theorem proof-body execution."
)
LEAN_PROJECT_IMPORT_INVENTORY_LIMIT = 16
LEAN_PROJECT_IDENTIFIER_LOOKUP_LIMIT = 6
LEAN_DECLARATION_RE = re.compile(
    r"^\s*(?:@[^\n]*\s*)*"
    r"(?:(?:private|protected|nonrec|noncomputable|unsafe)\s+)*"
    r"(theorem|lemma|def|abbrev|structure|class|inductive|instance)\s+"
    r"([A-Za-z_][A-Za-z0-9_'.]*)"
)
LEAN_NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z_][A-Za-z0-9_'.]*)\b")
LEAN_END_RE = re.compile(r"^\s*end(?:\s+([A-Za-z_][A-Za-z0-9_'.]*))?\b")
SYSTEM_PROMPT = (
    "You are the AI Statistician Formalizer/ProofEngineer authoring worker. "
    "Your task is to propose exact Lean semantic definitions from the given "
    "source-theorem binders, semantic anchors, local Lean constraints, and "
    "source references. Prefer small definition-only Lean that can be checked in "
    "the configured Lake project: use minimal imports, make every free variable "
    "an explicit binder, and report uncertain imports as known gaps rather than "
    "depending on broad unavailable modules. You are a generator only: do not "
    "claim tool execution, file writes, local Lean checking, theorem proof, or "
    "kernel verification. If the task is a semantic review of a typechecked "
    "definition-only candidate, report a semantic_review_decision as non-proof "
    "evidence, but do not claim proof-body readiness; if you approve it, keep "
    "known_gaps empty and put resolved issues or downstream proof obligations in "
    "semantic_review_evidence/proof_body_obligations instead. Return only one "
    "valid JSON object satisfying the requested schema."
)
FORBIDDEN_SOURCE_FRAGMENTS = (
    "axiom ",
    "axiom\n",
    "sorry",
    "admit",
    "unsafe",
    ":= true",
    ": Prop := True",
    "by trivial",
    "by exact",
    "by aesop",
)

@dataclass(frozen=True)
class AuthoringWorkerConfig:
    provider_name: str = "none"
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 4000
    temperature: float = 0.0
    max_repair_attempts: int = 1
    dry_run: bool = True
    max_tasks: int = 0
    placeholder_symbols: tuple[str, ...] = ()
    allow_external_export: bool = False
    external_export_mode: str = "full"
    external_export_approval_manifest: str = ""


@dataclass(frozen=True)
class AuthoringCandidateMaterializerConfig:
    max_candidates: int = 0
    include_source_comments: bool = True


def run_source_theorem_exact_semantic_definition_authoring_worker(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    repair_executor_manifest: Path | None = None,
    authoring_tasks_jsonl: Path | None = None,
    provider: GeneratorBackend | None = None,
    config: AuthoringWorkerConfig = AuthoringWorkerConfig(),
) -> dict[str, Any]:
    """Prepare or run LLM authoring for exact semantic-definition tasks."""

    task_path = resolve_source_theorem_exact_semantic_definition_authoring_tasks_path(
        runtime_dir=runtime_dir,
        repair_executor_manifest=repair_executor_manifest,
        authoring_tasks_jsonl=authoring_tasks_jsonl,
    )
    tasks = [
        row
        for row in _read_jsonl(task_path)
        if isinstance(row, Mapping)
    ]
    n_tasks_before_placeholder_filter = len(tasks)
    placeholder_filter = _normalized_placeholder_filter(config.placeholder_symbols)
    if placeholder_filter:
        tasks = [
            row
            for row in tasks
            if _adapter_object_key(str(row.get("placeholder_symbol", "") or ""))
            in placeholder_filter
        ]
    n_tasks_after_placeholder_filter = len(tasks)
    if config.max_tasks > 0:
        tasks = tasks[: config.max_tasks]
    prompt_export_mode = _normalized_external_export_mode(config.external_export_mode)
    prompt_packets = [_prompt_packet(row, export_mode=prompt_export_mode) for row in tasks]
    external_export_requested = (
        provider is not None
        and not config.dry_run
        and _is_external_llm_provider(config.provider_name)
    )
    configured_provider_name = str(config.provider_name or "none")
    backend_provider_name = str(getattr(provider, "provider_name", "") or "")
    should_call_provider = provider is not None and not config.dry_run
    live_llm_provider_requested = (
        should_call_provider
        and _is_live_external_llm_provider_pair(
            configured_provider_name,
            backend_provider_name,
        )
    )
    approvals = _load_external_export_approvals(
        Path(config.external_export_approval_manifest)
        if config.external_export_approval_manifest
        else None
    )
    candidate_review_packets = [
        _external_export_review_packet(row, provider_name=config.provider_name)
        for row in prompt_packets
    ]
    approved_prompt_ids = {
        str(packet.get("source_prompt_packet_id", "") or "")
        for packet in candidate_review_packets
        if external_export_requested
        and (
            config.allow_external_export
            or _external_export_packet_approved(
                packet,
                approvals=approvals,
                provider_name=config.provider_name,
                export_mode=prompt_export_mode,
            )
        )
    }
    blocked_prompt_ids = {
        str(packet.get("prompt_packet_id", "") or "")
        for packet in prompt_packets
        if external_export_requested
        and str(packet.get("prompt_packet_id", "") or "") not in approved_prompt_ids
    }
    external_export_review_packets = [
        packet
        for packet in candidate_review_packets
        if str(packet.get("source_prompt_packet_id", "") or "") in blocked_prompt_ids
    ]
    attempted_prompt_ids: list[str] = []
    candidate_packets: list[dict[str, Any]] = []
    if should_call_provider:
        for task, prompt_packet in zip(tasks, prompt_packets, strict=True):
            prompt_id = str(prompt_packet.get("prompt_packet_id", "") or "")
            if prompt_id in blocked_prompt_ids:
                continue
            attempted_prompt_ids.append(prompt_id)
            candidate_packets.append(
                _generate_candidate_packet(
                    task,
                    prompt_packet=prompt_packet,
                    provider=provider,
                    config=config,
                )
            )

    learning_rows = [
        _learning_row_from_prompt_packet(
            row,
            provider_requested=(
                should_call_provider
                and str(row.get("prompt_packet_id", "") or "") not in blocked_prompt_ids
            ),
            external_export_blocked=str(row.get("prompt_packet_id", "") or "")
            in blocked_prompt_ids,
        )
        for row in prompt_packets
    ]
    learning_rows.extend(
        _learning_row_from_external_export_review_packet(row)
        for row in external_export_review_packets
    )
    learning_rows.extend(_learning_row_from_candidate_packet(row) for row in candidate_packets)
    task_by_prompt_id = {
        str(prompt.get("prompt_packet_id", "") or ""): task
        for task, prompt in zip(tasks, prompt_packets, strict=True)
    }
    prompt_by_prompt_id = {
        str(prompt.get("prompt_packet_id", "") or ""): prompt
        for prompt in prompt_packets
    }
    retryable_authoring_tasks = [
        _retry_authoring_task(
            task_by_prompt_id[str(row.get("source_prompt_packet_id", "") or "")],
            prompt_packet=prompt_by_prompt_id[
                str(row.get("source_prompt_packet_id", "") or "")
            ],
            failed_candidate_packet=row,
        )
        for row in candidate_packets
        if row.get("runtime_queue_status") in AUTHORING_FOLLOWUP_QUEUE_STATUSES
        and str(row.get("source_prompt_packet_id", "") or "") in task_by_prompt_id
        and str(row.get("source_prompt_packet_id", "") or "") in prompt_by_prompt_id
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_packets_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_authoring_prompt_packets.jsonl"
    )
    candidate_packets_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_authoring_candidate_packets.jsonl"
    )
    external_export_review_packets_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_external_llm_export_review_packets.jsonl"
    )
    retryable_authoring_tasks_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_retry_authoring_tasks.jsonl"
    )
    learning_rows_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(prompt_packets_path, prompt_packets)
    _write_jsonl(external_export_review_packets_path, external_export_review_packets)
    _write_jsonl(candidate_packets_path, candidate_packets)
    _write_jsonl(retryable_authoring_tasks_path, retryable_authoring_tasks)
    _write_jsonl(learning_rows_path, learning_rows)

    status_counts = Counter(
        str(row.get("authoring_status", "") or "") for row in candidate_packets
    )
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_runtime_dir": str(runtime_dir or ""),
        "source_repair_executor_manifest": str(repair_executor_manifest or ""),
        "source_authoring_tasks_jsonl": str(task_path),
        "authoring_prompt_packets_jsonl": str(prompt_packets_path),
        "external_llm_export_review_packets_jsonl": str(
            external_export_review_packets_path
        ),
        "authoring_candidate_packets_jsonl": str(candidate_packets_path),
        "retryable_authoring_tasks_jsonl": str(retryable_authoring_tasks_path),
        "runtime_learning_rows_jsonl": str(learning_rows_path),
        "provider_requested": bool(attempted_prompt_ids),
        "external_export_requested": bool(external_export_requested),
        "external_export_allowed": bool(config.allow_external_export),
        "external_export_approval_manifest": str(
            config.external_export_approval_manifest or ""
        ),
        "external_export_approval_manifest_loaded": bool(approvals.get("loaded")),
        "external_export_blocked": bool(blocked_prompt_ids),
        "external_export_mode": prompt_export_mode,
        "provider_name": configured_provider_name,
        "backend_provider_name": backend_provider_name,
        "live_llm_provider_requested": live_llm_provider_requested,
        "static_or_fixture_provider_attempted": (
            should_call_provider and not live_llm_provider_requested
        ),
        "model_tier": str(config.model_tier or ""),
        "requested_model": str(config.model or ""),
        "dry_run": bool(config.dry_run or provider is None),
        "n_authoring_tasks": len(tasks),
        "n_authoring_tasks_before_placeholder_filter": (
            n_tasks_before_placeholder_filter
        ),
        "n_authoring_tasks_after_placeholder_filter": (
            n_tasks_after_placeholder_filter
        ),
        "placeholder_symbol_filter": list(config.placeholder_symbols),
        "normalized_placeholder_symbol_filter": sorted(placeholder_filter),
        "n_prompt_packets": len(prompt_packets),
        **_prompt_packet_structured_handoff_counts(prompt_packets),
        "n_semantic_review_prompt_packets": sum(
            1
            for row in prompt_packets
            if row.get("semantic_review_required_before_proof_body")
        ),
        "n_candidate_definition_requests_autofilled": sum(
            1
            for row in prompt_packets
            if row.get("candidate_definition_request_autofilled")
        ),
        "n_candidate_definition_requests_completed_from_task_policy": sum(
            1
            for row in prompt_packets
            if row.get("candidate_definition_request_completed_from_task_policy")
        ),
        "n_external_llm_export_review_packets": len(external_export_review_packets),
        "n_external_export_approved_tasks": len(approved_prompt_ids),
        "n_external_export_blocked_tasks": len(blocked_prompt_ids),
        "n_llm_attempted": len(attempted_prompt_ids),
        "n_live_llm_attempted": (
            len(attempted_prompt_ids) if live_llm_provider_requested else 0
        ),
        "n_static_or_fixture_llm_attempted": (
            len(attempted_prompt_ids) if not live_llm_provider_requested else 0
        ),
        "n_candidate_packets": len(candidate_packets),
        "n_candidate_packets_ok": sum(1 for row in candidate_packets if row.get("ok")),
        "n_candidate_packets_with_semantic_review_decision": sum(
            1
            for row in candidate_packets
            if str(row.get("semantic_review_decision", "") or "")
            not in {"", "not_reported"}
        ),
        "n_candidate_packets_failed": sum(
            1 for row in candidate_packets if not row.get("ok")
        ),
        "n_retryable_authoring_tasks": len(retryable_authoring_tasks),
        "n_structural_reformulation_required_tasks": sum(
            1
            for row in candidate_packets
            if row.get("runtime_queue_status") == STRUCTURAL_REFORMULATION_QUEUE_STATUS
        ),
        "n_retryable_provider_failures": sum(
            1
            for row in candidate_packets
            if row.get("failure_classification")
            in {"provider_connection_error", "provider_timeout_error"}
        ),
        "runtime_queue_status_counts": dict(
            sorted(
                Counter(
                    str(row.get("runtime_queue_status", "") or "")
                    for row in candidate_packets
                    if str(row.get("runtime_queue_status", "") or "").strip()
                ).items()
            )
        ),
        "failure_classification_counts": dict(
            sorted(
                Counter(
                    str(row.get("failure_classification", "") or "")
                    for row in candidate_packets
                    if str(row.get("failure_classification", "") or "").strip()
                ).items()
            )
        ),
        "placeholder_symbols": list(
            dict.fromkeys(
                str(row.get("placeholder_symbol", "") or "")
                for row in prompt_packets
                if str(row.get("placeholder_symbol", "") or "").strip()
            )
        ),
        "lean_repair_action_counts": dict(
            sorted(
                Counter(
                    str(row.get("lean_repair_action", "") or "")
                    for row in prompt_packets
                    if str(row.get("lean_repair_action", "") or "").strip()
                ).items()
            )
        ),
        "repair_strategy_counts": dict(
            sorted(
                Counter(
                    str(row.get("repair_strategy", "") or "")
                    for row in prompt_packets
                    if str(row.get("repair_strategy", "") or "").strip()
                ).items()
            )
        ),
        "n_local_lean_checked": 0,
        "n_local_lean_compiled": 0,
        "status_counts": dict(sorted(status_counts.items())),
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "proof_evidence_status": AUTHORING_WORKER_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_authoring_worker_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def run_source_theorem_exact_semantic_definition_authoring_candidate_materializer(
    *,
    out_dir: Path,
    authoring_worker_manifest: Path | None = None,
    candidate_packets_jsonl: Path | None = None,
    config: AuthoringCandidateMaterializerConfig = AuthoringCandidateMaterializerConfig(),
) -> dict[str, Any]:
    """Materialize validated authoring candidate packets into Lean draft files.

    This creates draft files and Lean-repair tasks only. It does not run Lean,
    does not establish semantic faithfulness, and does not prove the source
    theorem.
    """

    candidate_path = resolve_source_theorem_exact_semantic_definition_authoring_candidate_packets_path(
        authoring_worker_manifest=authoring_worker_manifest,
        candidate_packets_jsonl=candidate_packets_jsonl,
    )
    candidate_packets = [
        row
        for row in _read_jsonl(candidate_path)
        if isinstance(row, Mapping)
    ]
    if config.max_candidates > 0:
        candidate_packets = candidate_packets[: config.max_candidates]
    candidate_packets, adapter_group_orders = (
        _order_authoring_candidate_packets_for_materialization(candidate_packets)
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_artifacts_dir = out_dir / "candidate_artifacts"
    candidate_artifacts_dir.mkdir(parents=True, exist_ok=True)
    materialization_rows = [
        _materialization_row(
            packet,
            candidate_artifacts_dir=candidate_artifacts_dir,
            include_source_comments=config.include_source_comments,
            materialization_order_index=index,
        )
        for index, packet in enumerate(candidate_packets, start=1)
    ]
    lean_repair_tasks = [
        _lean_repair_task_from_materialization_row(row)
        for row in materialization_rows
        if row.get("materialization_status")
        == "EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZED_PENDING_LOCAL_LEAN"
    ]
    learning_rows = [
        _learning_row_from_materialization_row(row) for row in materialization_rows
    ]

    rows_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_authoring_candidate_materialization_rows.jsonl"
    )
    lean_repair_tasks_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_materialized_lean_repair_tasks.jsonl"
    )
    learning_rows_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(rows_path, materialization_rows)
    _write_jsonl(lean_repair_tasks_path, lean_repair_tasks)
    _write_jsonl(learning_rows_path, learning_rows)
    status_counts = Counter(
        str(row.get("materialization_status", "") or "")
        for row in materialization_rows
    )
    manifest = {
        "schema_version": 1,
        "artifact_kind": MATERIALIZER_ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_authoring_worker_manifest": str(authoring_worker_manifest or ""),
        "source_candidate_packets_jsonl": str(candidate_path),
        "candidate_artifacts_dir": str(candidate_artifacts_dir),
        "materialization_rows_jsonl": str(rows_path),
        "materialized_lean_repair_tasks_jsonl": str(lean_repair_tasks_path),
        "runtime_learning_rows_jsonl": str(learning_rows_path),
        "n_candidate_packets": len(candidate_packets),
        "n_materialization_rows": len(materialization_rows),
        "source_to_bridge_adapter_group_materialization_orders": (
            adapter_group_orders
        ),
        "n_source_to_bridge_adapter_materialization_groups": len(
            adapter_group_orders
        ),
        "n_materialized_definition_only_candidates": sum(
            1 for row in materialization_rows if row.get("definition_only_candidate_artifact_path")
        ),
        "n_materialized_candidates_with_semantic_review_decision": sum(
            1
            for row in materialization_rows
            if str(row.get("semantic_review_decision", "") or "")
            not in {"", "not_reported"}
        ),
        "n_materialized_lean_repair_tasks": len(lean_repair_tasks),
        "n_blocked_candidates": sum(
            1
            for row in materialization_rows
            if row.get("materialization_status")
            != "EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZED_PENDING_LOCAL_LEAN"
        ),
        "n_local_lean_checked": 0,
        "n_local_lean_compiled": 0,
        "status_counts": dict(sorted(status_counts.items())),
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "proof_evidence_status": MATERIALIZER_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_authoring_candidate_materializer_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def _order_authoring_candidate_packets_for_materialization(
    candidate_packets: Sequence[Mapping[str, Any]],
) -> tuple[list[Mapping[str, Any]], list[dict[str, Any]]]:
    indexed_packets = list(enumerate(candidate_packets))
    groups: dict[str, list[tuple[int, Mapping[str, Any]]]] = {}
    ungrouped: list[tuple[int, Mapping[str, Any]]] = []
    for index, packet in indexed_packets:
        group_id = _adapter_materialization_group_id(packet)
        if group_id:
            groups.setdefault(group_id, []).append((index, packet))
        else:
            ungrouped.append((index, packet))

    ordered_indexed: list[tuple[int, Mapping[str, Any]]] = []
    group_orders: list[dict[str, Any]] = []
    consumed_indices: set[int] = set()
    for group_id, group_rows in sorted(
        groups.items(),
        key=lambda item: min(index for index, _packet in item[1]),
    ):
        ordered_group, group_order = _order_adapter_materialization_group(
            group_id=group_id,
            group_rows=group_rows,
        )
        ordered_indexed.extend(ordered_group)
        consumed_indices.update(index for index, _packet in ordered_group)
        group_orders.append(group_order)
    for index, packet in indexed_packets:
        if index not in consumed_indices and (index, packet) in ungrouped:
            ordered_indexed.append((index, packet))
    return [packet for _index, packet in ordered_indexed], group_orders


def _order_adapter_materialization_group(
    *,
    group_id: str,
    group_rows: Sequence[tuple[int, Mapping[str, Any]]],
) -> tuple[list[tuple[int, Mapping[str, Any]]], dict[str, Any]]:
    by_key: dict[str, tuple[int, Mapping[str, Any]]] = {}
    original_keys: list[str] = []
    for index, packet in group_rows:
        key = _adapter_object_key(str(packet.get("placeholder_symbol", "") or ""))
        if not key:
            key = f"__missing_placeholder_{index}"
        if key not in by_key:
            by_key[key] = (index, packet)
            original_keys.append(key)
    group_keys = set(by_key)
    dependencies = {
        key: [
            dep_key
            for dep_key in (
                _adapter_object_key(name)
                for name in _candidate_required_adapter_object_names(packet)
            )
            if dep_key and dep_key in group_keys and dep_key != key
        ]
        for key, (_index, packet) in by_key.items()
    }
    missing_by_key = {
        key: [
            name
            for name in _candidate_required_adapter_object_names(packet)
            if _adapter_object_key(name) not in group_keys
        ]
        for key, (_index, packet) in by_key.items()
    }
    ordered_keys: list[str] = []
    remaining = set(group_keys)
    while remaining:
        ready = [
            key
            for key in original_keys
            if key in remaining
            and all(dep not in remaining for dep in dependencies.get(key, []))
        ]
        if not ready:
            ready = [key for key in original_keys if key in remaining]
        for key in ready:
            if key in remaining:
                ordered_keys.append(key)
                remaining.remove(key)
    ordered_rows = [by_key[key] for key in ordered_keys]
    placeholders_by_key = {
        key: str(by_key[key][1].get("placeholder_symbol", "") or "")
        for key in ordered_keys
    }
    group_order = {
        "source_to_bridge_adapter_instantiation_group_id": group_id,
        "placeholder_symbols_in_materialization_order": [
            placeholders_by_key[key] for key in ordered_keys
        ],
        "candidate_packet_ids_in_materialization_order": [
            str(by_key[key][1].get("candidate_packet_id", "") or "")
            for key in ordered_keys
        ],
        "adapter_dependency_edges": [
            {
                "placeholder_symbol": placeholders_by_key[key],
                "depends_on": [
                    str(by_key[dep][1].get("placeholder_symbol", "") or dep)
                    for dep in dependencies.get(key, [])
                ],
            }
            for key in ordered_keys
        ],
        "missing_adapter_candidate_dependencies": [
            {
                "placeholder_symbol": placeholders_by_key[key],
                "missing_required_adapter_object_names": missing_by_key.get(key, []),
            }
            for key in ordered_keys
            if missing_by_key.get(key)
        ],
        "proof_evidence_status": MATERIALIZER_PROOF_EVIDENCE_STATUS,
    }
    return ordered_rows, group_order


def _adapter_materialization_group_id(packet: Mapping[str, Any]) -> str:
    request = packet.get("candidate_definition_request", {})
    if isinstance(request, Mapping):
        group_id = str(
            request.get("source_to_bridge_adapter_instantiation_group_id", "") or ""
        )
        if group_id:
            return group_id
    return str(packet.get("source_to_bridge_adapter_instantiation_group_id", "") or "")


def _candidate_required_adapter_object_names(packet: Mapping[str, Any]) -> list[str]:
    request = packet.get("candidate_definition_request", {})
    if not isinstance(request, Mapping):
        return []
    return [
        str(value).strip()
        for value in request.get("required_adapter_object_names", []) or []
        if str(value).strip()
    ]


def _adapter_object_key(value: str) -> str:
    return compact_exact_semantic_placeholder_key(str(value or ""))


def _normalized_placeholder_filter(symbols: Sequence[str]) -> set[str]:
    return {
        key
        for key in (_adapter_object_key(str(symbol or "")) for symbol in symbols)
        if key
    }


def resolve_source_theorem_exact_semantic_definition_authoring_tasks_path(
    *,
    runtime_dir: Path | None = None,
    repair_executor_manifest: Path | None = None,
    authoring_tasks_jsonl: Path | None = None,
) -> Path:
    if authoring_tasks_jsonl is not None:
        return authoring_tasks_jsonl
    if repair_executor_manifest is not None:
        payload = json.loads(repair_executor_manifest.read_text(encoding="utf-8"))
        raw_path = str(
            payload.get("exact_semantic_definition_authoring_tasks_jsonl", "") or ""
        )
        if not raw_path:
            raise ValueError(
                "repair executor manifest does not list "
                "exact_semantic_definition_authoring_tasks_jsonl"
            )
        return _resolve_relative_artifact_path(
            base_dir=repair_executor_manifest.parent,
            raw_path=raw_path,
        )
    if runtime_dir is None:
        raise ValueError(
            "runtime_dir, repair_executor_manifest, or authoring_tasks_jsonl is required"
        )
    manifest_path = runtime_dir / "research_agent_runtime_manifest.json"
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifacts = payload.get("artifacts", {})
        if isinstance(artifacts, Mapping):
            raw_path = str(
                artifacts.get(
                    "runtime_source_theorem_exact_semantic_definition_authoring_tasks_jsonl",
                    "",
                )
                or ""
            )
            if raw_path:
                return _resolve_runtime_artifact_path(
                    runtime_dir=runtime_dir,
                    raw_path=raw_path,
                )
            raw_manifest = str(
                artifacts.get(
                    "runtime_source_theorem_exact_semantic_definition_lean_repair_executor_manifest",
                    "",
                )
                or ""
            )
            if raw_manifest:
                return resolve_source_theorem_exact_semantic_definition_authoring_tasks_path(
                    repair_executor_manifest=_resolve_runtime_artifact_path(
                        runtime_dir=runtime_dir,
                        raw_path=raw_manifest,
                    )
                )
    direct = runtime_dir / "source_theorem_exact_semantic_definition_authoring_tasks.jsonl"
    if direct.exists():
        return direct
    raise ValueError(
        "runtime directory does not list exact semantic-definition authoring tasks"
    )


def resolve_source_theorem_exact_semantic_definition_authoring_candidate_packets_path(
    *,
    authoring_worker_manifest: Path | None = None,
    candidate_packets_jsonl: Path | None = None,
) -> Path:
    if candidate_packets_jsonl is not None:
        return candidate_packets_jsonl
    if authoring_worker_manifest is None:
        raise ValueError("authoring_worker_manifest or candidate_packets_jsonl is required")
    payload = json.loads(authoring_worker_manifest.read_text(encoding="utf-8"))
    raw_path = str(payload.get("authoring_candidate_packets_jsonl", "") or "")
    if not raw_path:
        raise ValueError("authoring worker manifest does not list candidate packets")
    return _resolve_relative_artifact_path(
        base_dir=authoring_worker_manifest.parent,
        raw_path=raw_path,
    )


def _prompt_packet(task: Mapping[str, Any], *, export_mode: str = "full") -> dict[str, Any]:
    raw_request = dict(task.get("candidate_definition_request", {}) or {})
    request_autofilled = not bool(raw_request)
    task_policy_request = _candidate_definition_request_from_task(task)
    request = dict(task_policy_request)
    request.update(raw_request)
    request_completed_from_task_policy = bool(
        request_autofilled
        or any(key not in raw_request for key in task_policy_request)
    )
    export_mode = _normalized_external_export_mode(export_mode)
    prompt_payload = _prompt_payload(
        task,
        candidate_definition_request=request,
        export_mode=export_mode,
    )
    structured_context = _authoring_structured_context(
        task,
        candidate_definition_request=request,
        prompt_payload=prompt_payload,
    )
    lean_authoring_environment_contract = dict(
        prompt_payload.get("lean_authoring_environment_contract", {}) or {}
    )
    prompt_packet_id = (
        "source_theorem_exact_semantic_definition_authoring_prompt:"
        + stable_hash(
            [
                task.get("authoring_task_id", ""),
                task.get("target_theorem_name", ""),
                task.get("placeholder_symbol", ""),
                request,
                prompt_payload,
            ]
        )[:24]
    )
    return {
        "schema_version": 1,
        "artifact_kind": PROMPT_PACKET_ARTIFACT_KIND,
        "prompt_packet_id": prompt_packet_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_authoring_task_id": str(task.get("authoring_task_id", "") or ""),
        "source_execution_result_id": str(task.get("source_execution_result_id", "") or ""),
        "source_lean_repair_task_id": str(
            task.get("source_lean_repair_task_id", "") or ""
        ),
        "question_id": str(task.get("question_id", "") or ""),
        "question_title": str(task.get("question_title", "") or ""),
        "target_theorem_name": str(task.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(task.get("placeholder_symbol", "") or ""),
        "source_execution_status": str(task.get("source_execution_status", "") or ""),
        "authoring_trigger": str(task.get("authoring_trigger", "") or ""),
        "authoring_mode": str(task.get("authoring_mode", "") or ""),
        "lean_repair_action": str(task.get("lean_repair_action", "") or ""),
        "repair_strategy": str(task.get("repair_strategy", "") or ""),
        "source_definition_closure_work_order_id": str(
            task.get("source_definition_closure_work_order_id", "") or ""
        ),
        "source_to_bridge_adapter_instantiation_group_id": str(
            task.get("source_to_bridge_adapter_instantiation_group_id", "") or ""
        ),
        "source_to_bridge_grouped_premise_derivation_candidate_request_id": str(
            task.get(
                "source_to_bridge_grouped_premise_derivation_candidate_request_id",
                "",
            )
            or ""
        ),
        "source_to_bridge_adapter_object_names_requiring_source_instantiation": list(
            task.get(
                "source_to_bridge_adapter_object_names_requiring_source_instantiation",
                [],
            )
            or []
        ),
        "semantic_alignment_constraints": list(
            task.get("semantic_alignment_constraints", []) or []
        )[:8],
        "semantic_alignment_blockers": list(
            task.get("semantic_alignment_blockers", []) or []
        )[:8],
        "semantic_review_required_before_proof_body": bool(
            task.get("semantic_review_required_before_proof_body", True)
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "semantic_review_contract": _semantic_review_contract(task),
        "candidate_repair_feedback": _candidate_repair_feedback(task),
        "response_validation_feedback": dict(
            prompt_payload.get("response_validation_feedback", {}) or {}
        ),
        "retry_validation_errors": list(
            prompt_payload.get("retry_validation_errors", []) or []
        ),
        **structured_context,
        "candidate_definition_request": request,
        "candidate_definition_request_autofilled": request_autofilled,
        "candidate_definition_request_completed_from_task_policy": (
            request_completed_from_task_policy
        ),
        "external_export_mode": export_mode,
        "export_redaction_applied": export_mode == "redacted",
        "system_prompt": SYSTEM_PROMPT,
        "lean_authoring_environment_contract": lean_authoring_environment_contract,
        "user_prompt": json.dumps(prompt_payload, indent=2, sort_keys=True, default=str),
        "response_schema": AUTHORING_RESPONSE_JSON_SCHEMA,
        "runtime_queue_status": "PENDING_LIVE_LLM_EXACT_SEMANTIC_DEFINITION_AUTHORING",
        "next_owner": "Formalizer/ProofEngineer",
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "This prompt packet is an authoring request only. It is not a "
            "definition candidate, local Lean evidence, or source theorem proof."
        ),
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _prompt_payload(
    task: Mapping[str, Any],
    *,
    candidate_definition_request: Mapping[str, Any],
    export_mode: str = "full",
) -> dict[str, Any]:
    export_mode = _normalized_external_export_mode(export_mode)
    source_reference_hints = _source_reference_hints_for_prompt(
        task,
        export_mode=export_mode,
    )
    exact_context = _exact_semantic_definition_context_for_prompt(
        task,
        export_mode=export_mode,
    )
    response_validation_feedback = _response_validation_feedback(task)
    placeholder_policy = exact_semantic_definition_placeholder_policy(
        str(task.get("placeholder_symbol", "") or "")
    )
    source_theorem_binders = _authoring_source_theorem_binders(
        task,
        candidate_definition_request=candidate_definition_request,
        placeholder_policy=placeholder_policy,
    )
    return {
        "task": "author_exact_semantic_definition_candidate",
        "external_export_mode": export_mode,
        "export_redaction_applied": export_mode == "redacted",
        "evidence_boundary": BOUNDARY,
        "target_theorem_name": str(task.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(task.get("placeholder_symbol", "") or ""),
        "source_execution_status": str(task.get("source_execution_status", "") or ""),
        "authoring_trigger": str(task.get("authoring_trigger", "") or ""),
        "authoring_mode": str(task.get("authoring_mode", "") or ""),
        "exact_semantic_definition_context": exact_context,
        "candidate_definition_request": dict(candidate_definition_request),
        "source_theorem_binders": source_theorem_binders,
        "semantic_anchor_binder_names": list(
            task.get("premise_semantic_anchor_binder_names", []) or []
        ),
        "source_reference_hints": source_reference_hints,
        "source_reference_redaction_summary": _source_reference_redaction_summary(
            task,
            source_reference_hints=source_reference_hints,
            export_mode=export_mode,
        ),
        "semantic_alignment_constraints": list(
            task.get("semantic_alignment_constraints", []) or []
        )[:8],
        "semantic_alignment_blockers": list(
            task.get("semantic_alignment_blockers", []) or []
        )[:8],
        "semantic_review_required_before_proof_body": bool(
            task.get("semantic_review_required_before_proof_body", True)
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "semantic_review_contract": _semantic_review_contract(task),
        "semantic_review_output_policy": _semantic_review_output_policy(task),
        "candidate_repair_feedback": _candidate_repair_feedback(task),
        "response_validation_feedback": response_validation_feedback,
        "retry_validation_errors": list(
            response_validation_feedback.get("validation_errors", []) or []
        ),
        "definition_contract": dict(task.get("definition_contract", {}) or {}),
        "lean_authoring_environment_contract": (
            _lean_authoring_environment_contract(
                task,
                candidate_definition_request=candidate_definition_request,
            )
        ),
        "required_output_contract": {
            "placeholder_symbol": "same placeholder symbol as input",
            "definition_design": (
                "short explanation of the exact semantic object being defined"
            ),
            "lean_definition_candidate": (
                "Lean 4 definition/abbrev candidate only; no theorem proof, no "
                "axiom, no sorry/admit/unsafe"
            ),
            "required_imports": ["Lean imports needed by the candidate"],
            "binder_usage": [
                {
                    "name": "source theorem binder name",
                    "how_used": "short description",
                }
            ],
            "semantic_alignment_notes": [
                "how the candidate matches source theorem binders and references"
            ],
            "known_gaps": [
                "unresolved definition-level semantic/typeclass/import blockers only; [] when semantic_review_decision is approved_definition_candidate"
            ],
            "resolved_gap_evidence": [
                "prior known gaps resolved by source binders, source anchors, or local Lean feedback"
            ],
            "proof_body_obligations": [
                "downstream theorem-proof obligations that are not blockers for this definition candidate"
            ],
            "semantic_review_decision": (
                "one of approved_definition_candidate, repair_required, "
                "blocked_or_insufficient_context"
            ),
            "semantic_review_evidence": [
                "specific binders, anchors, references, or diagnostics checked"
            ],
            "semantic_review_required_before_proof_body": True,
            "source_theorem_ready_for_exact_proof_body": False,
            "forbidden_shortcuts_absent": True,
            "requires_local_lean_check": True,
        },
        "forbidden_shortcuts": list(
            candidate_definition_request.get("forbidden_shortcuts", []) or []
        ),
        "local_lean_gate": str(
            candidate_definition_request.get("local_lean_gate", "") or ""
        ),
    }


def _authoring_structured_context(
    task: Mapping[str, Any],
    *,
    candidate_definition_request: Mapping[str, Any],
    prompt_payload: Mapping[str, Any] | None = None,
    extra_sources: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    context = _exact_semantic_definition_context(task)
    for source in extra_sources:
        for key, value in _exact_semantic_definition_context(source).items():
            if context.get(key) in (None, "", [], {}):
                context[key] = value
    placeholder_policy = exact_semantic_definition_placeholder_policy(
        str(
            task.get("placeholder_symbol", "")
            or candidate_definition_request.get("placeholder_symbol", "")
            or ""
        )
    )
    source_binders = [
        dict(row)
        for row in (
            (prompt_payload or {}).get("source_theorem_binders", [])
            if isinstance(prompt_payload, Mapping)
            else []
        )
        if isinstance(row, Mapping)
    ]
    if not source_binders:
        source_binders = _authoring_source_theorem_binders(
            task,
            candidate_definition_request=candidate_definition_request,
            placeholder_policy=placeholder_policy,
            extra_sources=extra_sources,
        )
    if source_binders:
        if context.get("exact_source_theorem_binders") in (None, "", [], {}):
            context["exact_source_theorem_binders"] = source_binders
        context["source_theorem_binders"] = source_binders
    request_anchor_context = _source_anchor_context_from_candidate_definition_request(
        candidate_definition_request
    )
    existing_anchor_context = [
        dict(row)
        for row in context.get("source_anchor_context", []) or []
        if isinstance(row, Mapping)
    ]
    source_anchor_context = _dedup_mapping_rows(
        [*existing_anchor_context, *request_anchor_context]
    )
    if source_anchor_context:
        context["source_anchor_context"] = source_anchor_context[:16]
        explicit_source_anchor_context_rows = _safe_int(
            context.get("source_anchor_context_rows", 0)
        )
        context["source_anchor_context_rows"] = (
            explicit_source_anchor_context_rows
            if explicit_source_anchor_context_rows > 0
            else len(source_anchor_context)
        )
    return context


def _authoring_source_theorem_binders(
    task: Mapping[str, Any],
    *,
    candidate_definition_request: Mapping[str, Any],
    placeholder_policy: Any | None = None,
    extra_sources: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, str]]:
    request = dict(candidate_definition_request)
    request_required_binders = {
        "exact_source_theorem_binders": list(request.get("required_binders", []) or []),
        "candidate_definition_request": request,
    }
    return exact_semantic_definition_source_binders_from_context(
        task,
        *extra_sources,
        request,
        request_required_binders,
        placeholder_policy=placeholder_policy,
    )


def _source_anchor_context_from_candidate_definition_request(
    candidate_definition_request: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for binding in candidate_definition_request.get("required_anchor_bindings", []) or []:
        if not isinstance(binding, Mapping):
            continue
        binder = binding.get("binder", {})
        binder = dict(binder) if isinstance(binder, Mapping) else {}
        required_name = str(binding.get("required_anchor_name", "") or "").strip()
        actual_name = str(
            binding.get("actual_anchor_name", "")
            or binder.get("name", "")
            or required_name
            or ""
        ).strip()
        row: dict[str, Any] = {
            "source": "candidate_definition_request.required_anchor_bindings",
            "kind": "required_anchor_binding",
        }
        if required_name:
            row["required_anchor_name"] = required_name
            row["semantic_anchor_name"] = required_name
        if actual_name:
            row["actual_anchor_name"] = actual_name
            row["name"] = actual_name
        for key in ("type", "role"):
            value = str(binder.get(key, "") or binding.get(key, "") or "").strip()
            if value:
                row[key] = value
        if row.get("name") or row.get("required_anchor_name"):
            rows.append(row)
    return _dedup_mapping_rows(rows)


def _candidate_repair_feedback(task: Mapping[str, Any]) -> dict[str, Any]:
    feedback = dict(task.get("candidate_repair_feedback", {}) or {})
    prior_feedback_sources = _prior_local_lean_feedback_sources(task, feedback)
    diagnostics = list(task.get("local_lean_diagnostics", []) or [])[:12]
    diagnostic_source_excerpts = [
        dict(value)
        for value in task.get("local_lean_diagnostic_source_excerpts", []) or []
        if isinstance(value, Mapping)
    ][:3]
    current_unknown_identifiers = _lean_unknown_identifiers_from_diagnostics(
        _string_list(diagnostics)
    )
    current_typeclass_failures = _lean_typeclass_failures_from_diagnostics(
        _string_list(diagnostics)
    )
    current_unavailable_imports = _lean_unavailable_imports_from_diagnostics(
        _string_list(diagnostics)
    )
    prior_unknown_identifiers = _dedup_strings(
        identifier
        for source in (feedback, *prior_feedback_sources)
        for key in (
            "unknown_identifiers_from_prior_checks",
            "unknown_identifiers_from_last_check",
            "unknown_identifiers_from_all_checks",
        )
        for identifier in _string_list(source.get(key, []))
    )
    prior_typeclass_failures = _dedup_mapping_rows(
        row
        for source in (feedback, *prior_feedback_sources)
        for key in (
            "typeclass_failures_from_prior_checks",
            "typeclass_failures_from_last_check",
            "typeclass_failures_from_all_checks",
        )
        for row in source.get(key, []) or []
        if isinstance(row, Mapping)
    )
    prior_unavailable_imports = _dedup_strings(
        module
        for source in (feedback, *prior_feedback_sources)
        for key in (
            "unavailable_imports_from_prior_checks",
            "unavailable_imports_from_last_check",
            "unavailable_imports_from_all_checks",
        )
        for module in _string_list(source.get(key, []))
    )
    prior_diagnostic_source_excerpts = _dedup_mapping_rows(
        row
        for source in (feedback, *prior_feedback_sources)
        for key in (
            "diagnostic_source_excerpts_history",
            "diagnostic_source_excerpts",
            "local_lean_diagnostic_source_excerpts",
        )
        for row in source.get(key, []) or []
        if isinstance(row, Mapping)
    )

    feedback.update(
        {
            "definition_only_candidate_artifact_path": str(
                task.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_artifact_path": str(task.get("candidate_artifact_path", "") or ""),
            "candidate_source_file": str(task.get("candidate_source_file", "") or ""),
            "candidate_lean_project_hint": str(
                task.get("candidate_lean_project_hint", "") or ""
            ),
            "local_definition_lean_checked": bool(
                task.get("local_definition_lean_checked", False)
            ),
            "local_definition_lean_compiled": bool(
                task.get("local_definition_lean_compiled", False)
            ),
            "local_lean_checked": bool(task.get("local_lean_checked", False)),
            "local_lean_compiled": bool(task.get("local_lean_compiled", False)),
            "local_lean_returncode": int(task.get("local_lean_returncode", 0) or 0),
            "local_lean_diagnostics": diagnostics,
            "local_lean_diagnostic_source_excerpts": diagnostic_source_excerpts,
            "failure_classification": str(task.get("failure_classification", "") or ""),
            "recommended_next_action": str(
                task.get("recommended_next_action", "") or ""
            ),
        }
    )
    if prior_unknown_identifiers:
        feedback["unknown_identifiers_from_prior_checks"] = prior_unknown_identifiers
    all_unknown_identifiers = _dedup_strings(
        [*prior_unknown_identifiers, *current_unknown_identifiers]
    )
    if all_unknown_identifiers:
        feedback["unknown_identifiers_from_all_checks"] = all_unknown_identifiers
    if prior_typeclass_failures:
        feedback["typeclass_failures_from_prior_checks"] = prior_typeclass_failures
    all_typeclass_failures = _dedup_mapping_rows(
        [*prior_typeclass_failures, *current_typeclass_failures]
    )
    if all_typeclass_failures:
        feedback["typeclass_failures_from_all_checks"] = all_typeclass_failures
    if prior_unavailable_imports:
        feedback["unavailable_imports_from_prior_checks"] = prior_unavailable_imports
    all_unavailable_imports = _dedup_strings(
        [*prior_unavailable_imports, *current_unavailable_imports]
    )
    if all_unavailable_imports:
        feedback["unavailable_imports_from_all_checks"] = all_unavailable_imports
    diagnostic_history = _dedup_mapping_rows(
        [*prior_diagnostic_source_excerpts, *diagnostic_source_excerpts]
    )
    if diagnostic_history:
        feedback["diagnostic_source_excerpts_history"] = diagnostic_history[:8]
    verifier_gate_status = str(task.get("verifier_gate_status", "") or "").strip()
    verifier_gate_blockers = _dedup_strings(
        [
            *_string_list(feedback.get("verifier_gate_blockers", [])),
            *_string_list(task.get("verifier_gate_blockers", [])),
        ]
    )
    known_gaps = _dedup_strings(
        [
            *_string_list(feedback.get("known_gaps", [])),
            *_string_list(task.get("known_gaps", [])),
        ]
    )
    source_anchor_context = _dedup_mapping_rows(
        [
            *(feedback.get("source_anchor_context", []) or []),
            *(task.get("source_anchor_context", []) or []),
        ]
    )
    raw_source_anchor_context_rows = (
        task.get("source_anchor_context_rows", None)
        or feedback.get("source_anchor_context_rows", None)
        or len(source_anchor_context)
    )
    try:
        source_anchor_context_rows = int(raw_source_anchor_context_rows)
    except (TypeError, ValueError):
        source_anchor_context_rows = len(source_anchor_context)
    recommended_repair_tasks = _dedup_strings(
        [
            *_string_list(feedback.get("recommended_repair_tasks", [])),
            *_string_list(task.get("recommended_repair_tasks", [])),
        ]
    )
    proof_body_recheck_blockers = _dedup_strings(
        [
            *_string_list(feedback.get("proof_body_recheck_blockers", [])),
            *_string_list(task.get("proof_body_recheck_blockers", [])),
        ]
    )
    if verifier_gate_status:
        feedback["verifier_gate_status"] = verifier_gate_status
    if verifier_gate_blockers:
        feedback["verifier_gate_blockers"] = verifier_gate_blockers
    if known_gaps:
        feedback["known_gaps"] = known_gaps
    if source_anchor_context:
        feedback["source_anchor_context"] = source_anchor_context[:16]
        feedback["source_anchor_context_rows"] = source_anchor_context_rows
        source_anchor_context_summary = _source_anchor_context_summary(
            source_anchor_context
        )
        if source_anchor_context_summary:
            feedback["source_anchor_context_summary"] = (
                source_anchor_context_summary
            )
    if (
        verifier_gate_blockers
        or known_gaps
        or str(task.get("retry_failure_classification", "") or "").startswith(
            "exact_semantic_definition_verifier_gate_"
        )
        or str(task.get("failure_classification", "") or "").startswith(
            "exact_semantic_definition_verifier_gate_"
        )
    ):
        feedback["verifier_gate_known_gap_resolution_contract"] = (
            _verifier_gate_known_gap_resolution_contract(
                known_gaps=known_gaps,
                source_anchor_context_rows=source_anchor_context_rows,
                source_anchor_context_summary=feedback.get(
                    "source_anchor_context_summary",
                    {},
                ),
                verifier_gate_blockers=verifier_gate_blockers,
            )
        )
    if str(task.get("verifier_gate_result_id", "") or "").strip():
        feedback["verifier_gate_result_id"] = str(
            task.get("verifier_gate_result_id", "") or ""
        )
    if str(task.get("source_verifier_gate_work_order_id", "") or "").strip():
        feedback["source_verifier_gate_work_order_id"] = str(
            task.get("source_verifier_gate_work_order_id", "") or ""
        )
    if recommended_repair_tasks:
        feedback["recommended_repair_tasks"] = recommended_repair_tasks
    if proof_body_recheck_blockers:
        feedback["proof_body_recheck_blockers"] = proof_body_recheck_blockers
    source_proof_evidence_status = str(
        task.get("source_proof_evidence_status", "")
        or feedback.get("source_proof_evidence_status", "")
        or feedback.get("verifier_gate_proof_evidence_status", "")
        or ""
    ).strip()
    if source_proof_evidence_status:
        feedback["source_proof_evidence_status"] = source_proof_evidence_status
        feedback["verifier_gate_proof_evidence_status"] = source_proof_evidence_status
    return feedback


def _source_anchor_context_summary(
    source_anchor_context: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    binder_names: list[str] = []
    binder_rows: list[dict[str, str]] = []
    semantic_alignment_constraints: list[str] = []
    target_lean_declarations: list[str] = []
    target_identity_statuses: list[str] = []
    for row in source_anchor_context:
        if not isinstance(row, Mapping):
            continue
        name = str(row.get("name", "") or "").strip()
        row_type = str(row.get("type", "") or "").strip()
        role = str(row.get("role", "") or "").strip()
        if name:
            binder_names.append(name)
            binder_row = {"name": name}
            if row_type:
                binder_row["type"] = row_type
            if role:
                binder_row["role"] = role
            binder_rows.append(binder_row)
        for line in row.get("proof_body_goal_excerpt", []) or []:
            if not isinstance(line, str):
                continue
            parsed = _proof_body_goal_binder_from_line(line)
            if parsed:
                binder_names.append(parsed["name"])
                binder_rows.append(parsed)
        semantic_alignment_constraints.extend(
            _string_list(row.get("semantic_alignment_constraints", []))
        )
        target_declaration = str(row.get("target_lean_declaration", "") or "").strip()
        if target_declaration:
            target_lean_declarations.append(target_declaration)
        target_identity_status = str(
            row.get("source_theorem_target_identity_status", "") or ""
        ).strip()
        if target_identity_status:
            target_identity_statuses.append(target_identity_status)
    compact_binder_rows: list[dict[str, str]] = []
    seen_binders: set[str] = set()
    for row in binder_rows:
        name = str(row.get("name", "") or "").strip()
        if not name or name in seen_binders:
            continue
        seen_binders.add(name)
        compact_binder_rows.append(row)
    summary = {
        "source_theorem_binder_names": _dedup_strings(binder_names)[:32],
        "source_theorem_binders": compact_binder_rows[:16],
        "semantic_alignment_constraints": _dedup_strings(
            semantic_alignment_constraints
        )[:12],
        "target_lean_declarations": _dedup_strings(target_lean_declarations)[:8],
        "target_identity_statuses": _dedup_strings(target_identity_statuses)[:8],
    }
    return {key: value for key, value in summary.items() if value}


def _proof_body_goal_binder_from_line(line: str) -> dict[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("/") or stripped.startswith("error:"):
        return None
    match = re.match(r"^(?P<name>[A-Za-z_][A-Za-z0-9_']*)\s*:\s*(?P<type>.+)$", stripped)
    if match is None:
        return None
    name = match.group("name").strip()
    row_type = match.group("type").strip()
    if name in {"error", "warning"} or not row_type:
        return None
    return {"name": name, "type": row_type}


def _verifier_gate_known_gap_resolution_contract(
    *,
    known_gaps: Sequence[str],
    source_anchor_context_rows: int,
    source_anchor_context_summary: Mapping[str, Any],
    verifier_gate_blockers: Sequence[str],
) -> dict[str, Any]:
    binder_names = _string_list(
        source_anchor_context_summary.get("source_theorem_binder_names", [])
        if isinstance(source_anchor_context_summary, Mapping)
        else []
    )
    constraints = _string_list(
        source_anchor_context_summary.get("semantic_alignment_constraints", [])
        if isinstance(source_anchor_context_summary, Mapping)
        else []
    )
    return {
        "contract_kind": "verifier_gate_known_gap_resolution",
        "source_anchor_context_rows": int(source_anchor_context_rows),
        "source_theorem_binder_names": binder_names[:32],
        "semantic_alignment_constraints": constraints[:12],
        "verifier_gate_blockers": _string_list(verifier_gate_blockers),
        "known_gaps_to_resolve": _string_list(known_gaps),
        "required_resolution_actions": [
            "rewrite the exact semantic-definition candidate so every known_gap is either resolved against the recovered source binders/constraints or rewritten as a precise remaining blocker",
            "remove stale known_gap text that says source theorem binders were unavailable when source_anchor_context_rows is positive",
            "move resolved issues and downstream proof-body obligations to semantic_review_evidence/resolved_gap_evidence/proof_body_obligations instead of known_gaps",
            "when semantic_review_decision=approved_definition_candidate, known_gaps must be [] and candidate Known gaps comments must be absent",
            "remove candidate Known gaps comments only after the definition contract is satisfied; otherwise keep semantic_review_decision=repair_required or blocked_or_insufficient_context and source_theorem_ready_for_exact_proof_body=false",
            "rerun local Lean and the verifier gate before any proof-body recheck",
        ],
        "proof_boundary": (
            "Resolving verifier-gate known gaps is semantic-readiness work only. "
            "It must not claim source theorem proof evidence."
        ),
    }


def _response_validation_feedback(task: Mapping[str, Any]) -> dict[str, Any]:
    validation_errors = _string_list(task.get("retry_validation_errors", []))
    feedback = task.get("candidate_repair_feedback", {})
    if not validation_errors and isinstance(feedback, Mapping):
        validation_errors = _string_list(feedback.get("validation_errors", []))
    failed_packet_id = str(task.get("source_failed_candidate_packet_id", "") or "")
    return _response_validation_feedback_from_errors(
        task,
        validation_errors=validation_errors,
        failure_classification=str(
            task.get("retry_failure_classification", "")
            or task.get("failure_classification", "")
            or ""
        ),
        runtime_queue_status=str(task.get("runtime_queue_status", "") or ""),
        recommended_next_action=str(
            task.get("retry_recommended_next_action", "")
            or task.get("recommended_next_action", "")
            or ""
        ),
        source_failed_candidate_packet_id=failed_packet_id,
    )


def _response_validation_feedback_from_errors(
    task: Mapping[str, Any],
    *,
    validation_errors: Sequence[str],
    failure_classification: str,
    runtime_queue_status: str,
    recommended_next_action: str,
    source_failed_candidate_packet_id: str = "",
) -> dict[str, Any]:
    validation_errors = _string_list(validation_errors)
    source_failed_candidate_packet_id = str(
        source_failed_candidate_packet_id or ""
    )
    if not validation_errors and not source_failed_candidate_packet_id:
        return {}
    unverified_imports = _unverified_required_imports_from_validation_errors(
        validation_errors
    )
    return {
        "source_failed_candidate_packet_id": source_failed_candidate_packet_id,
        "failure_classification": str(failure_classification or ""),
        "runtime_queue_status": str(runtime_queue_status or ""),
        "validation_errors": validation_errors[:8],
        "unverified_required_imports": unverified_imports[:8],
        "recommended_next_action": str(recommended_next_action or ""),
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "Authoring response-validation feedback is prompt repair context only. "
            "It is not semantic-definition kernel evidence and cannot prove the "
            "source theorem; any repaired candidate must still pass local Lean/AXLE."
        ),
    }


def _unverified_required_imports_from_validation_errors(
    errors: Sequence[str],
) -> list[str]:
    modules: list[str] = []
    for error in errors:
        text = str(error or "")
        if "required_imports include modules not verified" not in text:
            continue
        suffix = text.split(":", 1)[-1]
        modules.extend(
            match.group(0)
            for match in re.finditer(
                r"\b(?:[A-Za-z_][A-Za-z0-9_']*\.)+[A-Za-z_][A-Za-z0-9_']*\b",
                suffix,
            )
        )
    return list(dict.fromkeys(modules))


def _prior_local_lean_feedback_sources(
    task: Mapping[str, Any],
    feedback: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    sources: list[Mapping[str, Any]] = []
    for container in (task, feedback):
        nested = container.get("local_lean_feedback", {})
        if isinstance(nested, Mapping):
            sources.append(nested)
        contract = container.get("lean_authoring_environment_contract", {})
        if isinstance(contract, Mapping):
            nested = contract.get("local_lean_feedback", {})
            if isinstance(nested, Mapping):
                sources.append(nested)
    return sources


def _dedup_strings(values: Any) -> list[str]:
    return list(
        dict.fromkeys(
            str(value).strip()
            for value in values or []
            if str(value).strip()
        )
    )


def _dedup_mapping_rows(values: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in values or []:
        if not isinstance(value, Mapping):
            continue
        row = dict(value)
        key = json.dumps(row, sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    return rows


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _mapping_rows(value: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in value or [] if isinstance(row, Mapping)]


def _prompt_packet_structured_handoff_counts(
    prompt_packets: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    counts = {
        "n_prompt_packets_with_source_theorem_binders": 0,
        "n_prompt_packets_with_exact_source_theorem_binders": 0,
        "n_prompt_packets_with_source_anchor_context": 0,
        "n_prompt_packets_with_required_anchor_bindings": 0,
        "n_prompt_packets_with_complete_required_anchors": 0,
        "n_prompt_packets_with_lean_contract_source_binders": 0,
        "n_prompt_packets_with_source_grounded_authoring_handoff": 0,
    }
    for packet in prompt_packets:
        request = packet.get("candidate_definition_request", {})
        request = request if isinstance(request, Mapping) else {}
        contract = packet.get("lean_authoring_environment_contract", {})
        contract = contract if isinstance(contract, Mapping) else {}
        has_source_binders = bool(_mapping_rows(packet.get("source_theorem_binders", [])))
        has_exact_binders = bool(
            _mapping_rows(packet.get("exact_source_theorem_binders", []))
        )
        has_source_anchor_context = bool(
            _mapping_rows(packet.get("source_anchor_context", []))
        ) or _safe_int(packet.get("source_anchor_context_rows", 0)) > 0
        has_required_anchor_bindings = bool(
            _mapping_rows(request.get("required_anchor_bindings", []))
        )
        required_anchor_names = _string_list(request.get("required_anchor_names", []))
        missing_required_anchor_names = _string_list(
            request.get("missing_required_anchor_names", [])
        )
        has_complete_required_anchors = bool(
            required_anchor_names and not missing_required_anchor_names
        )
        has_lean_contract_source_binders = bool(
            _mapping_rows(contract.get("source_theorem_binders", []))
        ) or _safe_int(contract.get("source_theorem_binder_count", 0)) > 0
        if has_source_binders:
            counts["n_prompt_packets_with_source_theorem_binders"] += 1
        if has_exact_binders:
            counts["n_prompt_packets_with_exact_source_theorem_binders"] += 1
        if has_source_anchor_context:
            counts["n_prompt_packets_with_source_anchor_context"] += 1
        if has_required_anchor_bindings:
            counts["n_prompt_packets_with_required_anchor_bindings"] += 1
        if has_complete_required_anchors:
            counts["n_prompt_packets_with_complete_required_anchors"] += 1
        if has_lean_contract_source_binders:
            counts["n_prompt_packets_with_lean_contract_source_binders"] += 1
        if (
            has_source_binders
            and has_exact_binders
            and has_source_anchor_context
            and has_required_anchor_bindings
            and has_complete_required_anchors
            and has_lean_contract_source_binders
        ):
            counts["n_prompt_packets_with_source_grounded_authoring_handoff"] += 1
    return counts


def _lean_parse_error_source_fragments_from_excerpts(
    excerpts: Sequence[Mapping[str, Any]],
) -> list[str]:
    fragments: list[str] = []
    for row in excerpts:
        diagnostic = str(row.get("diagnostic", "") or "").lower()
        if (
            "expected token" not in diagnostic
            and "unexpected token" not in diagnostic
            and "parse" not in diagnostic
        ):
            continue
        try:
            target_line = int(row.get("line", 0) or 0)
        except (TypeError, ValueError):
            target_line = 0
        for raw_line in row.get("source_excerpt", []) or []:
            line_text = str(raw_line or "")
            match = re.match(r"\s*(\d+):\s?(.*)$", line_text)
            source_line = match.group(2).strip() if match else line_text.strip()
            if target_line and match and int(match.group(1)) != target_line:
                continue
            if not source_line:
                continue
            fragments.append(source_line)
            if ":=" in source_line:
                rhs = source_line.split(":=", 1)[1].strip()
                if rhs:
                    fragments.append(rhs)
    return _dedup_strings(fragments)


def _lean_feedback_contract(task: Mapping[str, Any]) -> dict[str, Any]:
    feedback = _candidate_repair_feedback(task)
    diagnostics = _string_list(feedback.get("local_lean_diagnostics", []))[:12]
    local_lean_checked = bool(feedback.get("local_lean_checked", False))
    local_lean_compiled = bool(feedback.get("local_lean_compiled", False))
    current_unknown_identifiers = _lean_unknown_identifiers_from_diagnostics(
        diagnostics
    )
    prior_unknown_identifiers = _string_list(
        feedback.get("unknown_identifiers_from_prior_checks", [])
    )
    all_unknown_identifiers = _dedup_strings(
        feedback.get("unknown_identifiers_from_all_checks", [])
        or [*prior_unknown_identifiers, *current_unknown_identifiers]
    )
    current_typeclass_failures = _lean_typeclass_failures_from_diagnostics(
        diagnostics
    )
    prior_typeclass_failures = _dedup_mapping_rows(
        feedback.get("typeclass_failures_from_prior_checks", [])
    )
    all_typeclass_failures = _dedup_mapping_rows(
        feedback.get("typeclass_failures_from_all_checks", [])
        or [*prior_typeclass_failures, *current_typeclass_failures]
    )
    current_unavailable_imports = _lean_unavailable_imports_from_diagnostics(
        diagnostics
    )
    prior_unavailable_imports = _string_list(
        feedback.get("unavailable_imports_from_prior_checks", [])
    )
    all_unavailable_imports = _dedup_strings(
        feedback.get("unavailable_imports_from_all_checks", [])
        or [*prior_unavailable_imports, *current_unavailable_imports]
    )
    current_source_excerpts = [
        dict(row)
        for row in feedback.get("local_lean_diagnostic_source_excerpts", []) or []
        if isinstance(row, Mapping)
    ]
    diagnostic_history = _dedup_mapping_rows(
        feedback.get("diagnostic_source_excerpts_history", [])
        or current_source_excerpts
    )
    current_parse_error_fragments = _lean_parse_error_source_fragments_from_excerpts(
        current_source_excerpts
    )
    prior_parse_error_fragments = _string_list(
        feedback.get("parse_error_source_fragments_from_prior_checks", [])
    )
    all_parse_error_fragments = _dedup_strings(
        feedback.get("parse_error_source_fragments_from_all_checks", [])
        or [
            *prior_parse_error_fragments,
            *_lean_parse_error_source_fragments_from_excerpts(diagnostic_history),
            *current_parse_error_fragments,
        ]
    )
    return {
        "local_lean_feedback_available": bool(local_lean_checked or diagnostics),
        "local_lean_checked": local_lean_checked,
        "local_lean_compiled": local_lean_compiled,
        "failure_classification": str(
            feedback.get("failure_classification", "") or ""
        ),
        "recommended_next_action": str(
            feedback.get("recommended_next_action", "") or ""
        ),
        "unknown_identifiers_from_last_check": (
            current_unknown_identifiers
        ),
        "unknown_identifiers_from_prior_checks": prior_unknown_identifiers,
        "unknown_identifiers_from_all_checks": (
            all_unknown_identifiers or current_unknown_identifiers
        ),
        "typeclass_failures_from_last_check": (
            current_typeclass_failures
        ),
        "typeclass_failures_from_prior_checks": prior_typeclass_failures,
        "typeclass_failures_from_all_checks": (
            all_typeclass_failures or current_typeclass_failures
        ),
        "unavailable_imports_from_last_check": (
            current_unavailable_imports
        ),
        "unavailable_imports_from_prior_checks": prior_unavailable_imports,
        "unavailable_imports_from_all_checks": (
            all_unavailable_imports or current_unavailable_imports
        ),
        "parse_error_source_fragments_from_last_check": current_parse_error_fragments,
        "parse_error_source_fragments_from_prior_checks": prior_parse_error_fragments,
        "parse_error_source_fragments_from_all_checks": (
            all_parse_error_fragments or current_parse_error_fragments
        ),
        "diagnostics_excerpt": diagnostics[:6],
        "diagnostic_source_excerpts": list(
            feedback.get("local_lean_diagnostic_source_excerpts", []) or []
        )[:3],
        "diagnostic_source_excerpts_history": diagnostic_history[:8],
    }


def _lean_project_import_inventory_contract(
    task: Mapping[str, Any],
    *,
    lean_feedback: Mapping[str, Any],
) -> dict[str, Any]:
    feedback = _candidate_repair_feedback(task)
    project_raw = str(feedback.get("candidate_lean_project_hint", "") or "").strip()
    project = Path(project_raw).expanduser() if project_raw else Path()
    candidate_path = _first_existing_path(
        [
            feedback.get("definition_only_candidate_artifact_path", ""),
            feedback.get("candidate_artifact_path", ""),
            feedback.get("candidate_source_file", ""),
            task.get("definition_only_candidate_artifact_path", ""),
            task.get("candidate_artifact_path", ""),
            task.get("candidate_source_file", ""),
        ]
    )
    candidate_imports = _candidate_import_modules_from_path(candidate_path)
    unavailable_imports = _string_list(
        lean_feedback.get("unavailable_imports_from_last_check", [])
    )
    if not project_raw:
        status = "no_project_hint"
        compiled_modules: list[str] = []
    elif not project.exists():
        status = "project_missing"
        compiled_modules = []
    else:
        compiled_modules = _compiled_import_modules_for_project(project)
        status = "available" if compiled_modules else "compiled_import_cache_missing"
    compiled_set = set(compiled_modules)
    verified_candidate_imports = [
        module for module in candidate_imports if module in compiled_set
    ]
    unverified_candidate_imports = [
        module for module in candidate_imports if module not in compiled_set
    ]
    source_available_candidate_imports = [
        module for module in candidate_imports if _lean_module_source_exists(project, module)
    ]
    source_available_unavailable_imports = [
        module
        for module in unavailable_imports
        if _lean_module_source_exists(project, module)
    ]
    unavailable_import_repair_rows = [
        _unavailable_import_repair_row(
            module,
            compiled_modules=compiled_modules,
            limit=LEAN_PROJECT_IMPORT_INVENTORY_LIMIT,
        )
        for module in unavailable_imports
    ]
    nearest_rows = [
        {
            "unavailable_import": row["unavailable_import"],
            "nearest_verified_modules": row["nearest_verified_modules"],
        }
        for row in unavailable_import_repair_rows
    ]
    return {
        "project_import_inventory_status": status,
        "project_path": str(project) if project_raw else "",
        "candidate_file": str(candidate_path) if candidate_path is not None else "",
        "compiled_import_module_count": len(compiled_modules),
        "candidate_import_modules": candidate_imports[:LEAN_PROJECT_IMPORT_INVENTORY_LIMIT],
        "verified_candidate_import_modules": (
            verified_candidate_imports[:LEAN_PROJECT_IMPORT_INVENTORY_LIMIT]
        ),
        "unverified_candidate_import_modules": (
            unverified_candidate_imports[:LEAN_PROJECT_IMPORT_INVENTORY_LIMIT]
        ),
        "source_available_candidate_import_modules": (
            source_available_candidate_imports[:LEAN_PROJECT_IMPORT_INVENTORY_LIMIT]
        ),
        "source_available_unavailable_import_modules": (
            source_available_unavailable_imports[:LEAN_PROJECT_IMPORT_INVENTORY_LIMIT]
        ),
        "nearby_verified_import_modules_by_unavailable_import": nearest_rows,
        "unavailable_import_repair_rows": unavailable_import_repair_rows,
        "inventory_scope": (
            "bounded compiled .olean module inventory plus direct source-file "
            "existence checks from the configured Lake project"
        ),
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    }


def _lean_project_identifier_lookup_contract(
    task: Mapping[str, Any],
    *,
    lean_feedback: Mapping[str, Any],
    import_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    project_raw = str(import_inventory.get("project_path", "") or "").strip()
    project = Path(project_raw).expanduser() if project_raw else Path()
    lookup_specs = _lean_identifier_lookup_specs(lean_feedback)
    if not lookup_specs:
        return {
            "project_identifier_lookup_status": "no_unknown_identifiers",
            "project_path": project_raw,
            "unknown_identifier_rows": [],
            "identifier_lookup_rows": [],
            "identifier_reuse_policy": [],
            "hard_negative_identifier_rows": [],
            "lookup_scope": "not_run_without_unknown_identifiers",
            "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
        }
    if not project_raw:
        status = "no_project_hint"
        rows = [
            _empty_unknown_identifier_lookup_row(
                spec["identifier"],
                lookup_reason=spec["lookup_reason"],
                typeclass_failure=spec.get("typeclass_failure"),
            )
            for spec in lookup_specs
        ]
    elif not project.exists():
        status = "project_missing"
        rows = [
            _empty_unknown_identifier_lookup_row(
                spec["identifier"],
                lookup_reason=spec["lookup_reason"],
                typeclass_failure=spec.get("typeclass_failure"),
            )
            for spec in lookup_specs
        ]
    else:
        status = "available"
        rows = [
            _unknown_identifier_source_lookup_row(
                project,
                spec["identifier"],
                lookup_reason=spec["lookup_reason"],
                typeclass_failure=spec.get("typeclass_failure"),
            )
            for spec in lookup_specs
        ]
    identifier_reuse_policy = _identifier_lookup_reuse_policy_rows(rows)
    return {
        "project_identifier_lookup_status": status,
        "project_path": project_raw,
        "unknown_identifier_rows": rows,
        "identifier_lookup_rows": rows,
        "identifier_reuse_policy": identifier_reuse_policy,
        "hard_negative_identifier_rows": [
            row
            for row in identifier_reuse_policy
            if row.get("reuse_status") == "must_not_reuse_without_new_local_evidence"
        ],
        "lookup_scope": (
            "bounded lexical Lean source lookup over the configured project and "
            "Mathlib package; hits are retrieval/context only, not proof evidence"
        ),
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    }


def _lean_identifier_lookup_specs(lean_feedback: Mapping[str, Any]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for identifier in _string_list(
        lean_feedback.get("unknown_identifiers_from_all_checks", [])
        or lean_feedback.get("unknown_identifiers_from_last_check", [])
    ):
        specs.append(
            {
                "identifier": identifier,
                "lookup_reason": "unknown_identifier",
            }
        )
    for failure in (
        lean_feedback.get("typeclass_failures_from_all_checks", [])
        or lean_feedback.get("typeclass_failures_from_last_check", [])
        or []
    ):
        if not isinstance(failure, Mapping):
            continue
        failed_typeclass = str(failure.get("failed_typeclass", "") or "").strip()
        if not failed_typeclass:
            continue
        specs.append(
            {
                "identifier": failed_typeclass,
                "lookup_reason": "typeclass_synthesis_failure",
                "typeclass_failure": dict(failure),
            }
        )
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for spec in specs:
        key = (spec["identifier"], spec["lookup_reason"])
        if key not in seen:
            seen.add(key)
            deduped.append(spec)
    return deduped


def _empty_unknown_identifier_lookup_row(
    identifier: str,
    *,
    lookup_reason: str = "unknown_identifier",
    typeclass_failure: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "unknown_identifier": identifier,
        "lookup_identifier": identifier,
        "lookup_reason": lookup_reason,
        "typeclass_failure": dict(typeclass_failure or {}),
        "declaration_hits": [],
        "reference_hits": [],
        "verified_declaration_modules": [],
        "repair_options": _identifier_lookup_repair_options(
            verified_modules=[],
            lookup_reason=lookup_reason,
        ),
        "source_lookup_status": "not_run",
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    }


def _unknown_identifier_source_lookup_row(
    project: Path,
    identifier: str,
    *,
    lookup_reason: str = "unknown_identifier",
    typeclass_failure: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    declaration_hits: list[dict[str, Any]] = []
    reference_hits: list[dict[str, Any]] = []
    full_identifier = str(identifier or "").strip()
    short_identifier = full_identifier.rsplit(".", 1)[-1]
    if not full_identifier or not short_identifier:
        return _empty_unknown_identifier_lookup_row(
            full_identifier,
            lookup_reason=lookup_reason,
            typeclass_failure=typeclass_failure,
        )
    for source_root, module_root in _lean_source_lookup_roots(project):
        for path in _iter_lean_source_paths(source_root, project=project):
            if len(declaration_hits) >= LEAN_PROJECT_IDENTIFIER_LOOKUP_LIMIT and len(
                reference_hits
            ) >= LEAN_PROJECT_IDENTIFIER_LOOKUP_LIMIT:
                break
            if not _lean_source_lookup_path_allowed(
                path,
                source_root=source_root,
                project=project,
            ):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if full_identifier not in text and short_identifier not in text:
                continue
            module = _lean_module_from_path(
                module_root,
                path,
                suffix=".lean",
            )
            _scan_identifier_source_text(
                text,
                path=path,
                module=module,
                identifier=full_identifier,
                short_identifier=short_identifier,
                project=project,
                declaration_hits=declaration_hits,
                reference_hits=reference_hits,
            )
    verified_modules = [
        str(hit.get("module", ""))
        for hit in declaration_hits
        if hit.get("module_compiled") and str(hit.get("module", "")).strip()
    ]
    return {
        "unknown_identifier": full_identifier,
        "lookup_identifier": full_identifier,
        "lookup_reason": lookup_reason,
        "typeclass_failure": dict(typeclass_failure or {}),
        "declaration_hits": declaration_hits[:LEAN_PROJECT_IDENTIFIER_LOOKUP_LIMIT],
        "reference_hits": reference_hits[:LEAN_PROJECT_IDENTIFIER_LOOKUP_LIMIT],
        "verified_declaration_modules": list(dict.fromkeys(verified_modules))[
            :LEAN_PROJECT_IDENTIFIER_LOOKUP_LIMIT
        ],
        "repair_options": _identifier_lookup_repair_options(
            verified_modules=verified_modules,
            lookup_reason=lookup_reason,
        ),
        "source_lookup_status": "hits_found"
        if declaration_hits or reference_hits
        else "no_source_hits_found",
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    }


def _identifier_lookup_repair_options(
    *,
    verified_modules: Sequence[str],
    lookup_reason: str,
) -> list[str]:
    if lookup_reason == "typeclass_synthesis_failure":
        options = [
            (
                "do not treat a class declaration module as evidence that an "
                "instance exists for the failed instance type"
            ),
            (
                "remove or parameterize the operation requiring this typeclass "
                "unless the source theorem semantics require it"
            ),
            (
                "do not replace the failed operation with a new named API unless "
                "that replacement identifier is grounded by source references, "
                "project_identifier_lookup, or a local Lean rerun"
            ),
            (
                "if keeping the operation, retrieve and locally verify an actual "
                "instance declaration for the failed instance type before semantic review"
            ),
            (
                "return blocked_or_insufficient_context if the required instance "
                "or source theorem binder context is missing"
            ),
        ]
        if verified_modules:
            options.insert(
                0,
                (
                    "use verified_declaration_modules only as source context for "
                    "the class/API, then rerun local Lean after an instance-level repair"
                ),
            )
        return options
    options = [
        (
            "remove the dependency or make the operation an explicit parameter "
            "when source theorem semantics do not require this identifier"
        ),
        (
            "return blocked_or_insufficient_context if the exact source theorem "
            "binders/import context are still missing"
        ),
        (
            "do not replace this identifier with a sibling API unless that new "
            "identifier has its own source lookup hit or local Lean verification"
        ),
    ]
    if verified_modules:
        options.insert(
            0,
            (
                "if keeping the identifier, add one verified_declaration_module "
                "to required_imports and rerun local Lean before semantic review"
            ),
        )
    return options


def _identifier_lookup_reuse_policy_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    policy_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        identifier = str(
            row.get("unknown_identifier", "")
            or row.get("lookup_identifier", "")
            or ""
        ).strip()
        if not identifier:
            continue
        lookup_reason = str(row.get("lookup_reason", "") or "unknown_identifier")
        key = (identifier, lookup_reason)
        if key in seen:
            continue
        seen.add(key)
        verified_modules = _dedup_strings(row.get("verified_declaration_modules", []))
        if lookup_reason == "typeclass_synthesis_failure":
            policy_rows.append(
                {
                    "identifier": identifier,
                    "lookup_reason": lookup_reason,
                    "reuse_status": "not_instance_evidence",
                    "verified_declaration_modules": verified_modules,
                    "must_not_treat_declaration_module_as_instance": True,
                    "required_action_before_reuse": (
                        "retrieve and locally verify an actual instance-level "
                        "repair, or remove/parameterize the operation"
                    ),
                    "fallback_action": "return blocked_or_insufficient_context",
                }
            )
            continue
        if verified_modules:
            policy_rows.append(
                {
                    "identifier": identifier,
                    "lookup_reason": lookup_reason,
                    "reuse_status": (
                        "reuse_requires_verified_declaration_import_and_local_lean_rerun"
                    ),
                    "verified_declaration_modules": verified_modules,
                    "must_import_one_verified_declaration_module_before_reuse": True,
                    "required_action_before_reuse": (
                        "add one verified_declaration_module to required_imports "
                        "and rerun local Lean before semantic review"
                    ),
                    "fallback_action": (
                        "remove or parameterize the dependency if source theorem "
                        "semantics do not require it"
                    ),
                }
            )
            continue
        policy_rows.append(
            {
                "identifier": identifier,
                "lookup_reason": lookup_reason,
                "reuse_status": "must_not_reuse_without_new_local_evidence",
                "verified_declaration_modules": [],
                "must_not_reuse_in_candidate": True,
                "required_action_before_reuse": (
                    "obtain a new source lookup hit or local Lean check for this "
                    "exact identifier before using it again"
                ),
                "fallback_action": (
                    "remove or parameterize the dependency, or return "
                    "blocked_or_insufficient_context"
                ),
            }
        )
    return policy_rows


def _lean_source_lookup_roots(project: Path) -> list[tuple[Path, Path]]:
    roots: list[tuple[Path, Path]] = []
    if project.exists():
        roots.append((project, project))
    mathlib = project / ".lake" / "packages" / "mathlib"
    mathlib_sources = mathlib / "Mathlib"
    if mathlib_sources.exists():
        roots.append((mathlib_sources, mathlib))
    return roots


def _iter_lean_source_paths(source_root: Path, *, project: Path) -> list[Path]:
    paths: list[Path] = []
    stack = [source_root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if source_root == project and entry.name in {".git", ".lake", ".venv"}:
                    continue
                stack.append(entry)
            elif entry.suffix == ".lean":
                paths.append(entry)
    return sorted(paths)


def _lean_source_lookup_path_allowed(
    path: Path,
    *,
    source_root: Path,
    project: Path,
) -> bool:
    if source_root != project:
        return True
    try:
        relative = path.relative_to(project)
    except ValueError:
        return False
    return ".lake" not in relative.parts


def _scan_identifier_source_text(
    text: str,
    *,
    path: Path,
    module: str,
    identifier: str,
    short_identifier: str,
    project: Path,
    declaration_hits: list[dict[str, Any]],
    reference_hits: list[dict[str, Any]],
) -> None:
    namespace_stack: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        namespace_match = LEAN_NAMESPACE_RE.match(line)
        if namespace_match:
            namespace_stack.append(namespace_match.group(1))
            continue
        end_match = LEAN_END_RE.match(line)
        if end_match and namespace_stack:
            namespace_stack.pop()
            continue
        decl_match = LEAN_DECLARATION_RE.match(line)
        if decl_match:
            name = decl_match.group(2)
            full_names = _lean_declaration_full_names(name, namespace_stack)
            if identifier in full_names or name == identifier:
                if len(declaration_hits) < LEAN_PROJECT_IDENTIFIER_LOOKUP_LIMIT:
                    declaration_hits.append(
                        _lean_identifier_hit(
                            path=path,
                            line_no=line_no,
                            line=line,
                            module=module,
                            project=project,
                            candidate_kind="lean_declaration_name_match",
                            declaration_kind=decl_match.group(1),
                            declaration_name=identifier
                            if identifier in full_names
                            else name,
                            matched_term=identifier,
                        )
                    )
                continue
        if identifier in line or (
            not declaration_hits and short_identifier in line
        ):
            if len(reference_hits) < LEAN_PROJECT_IDENTIFIER_LOOKUP_LIMIT:
                reference_hits.append(
                    _lean_identifier_hit(
                        path=path,
                        line_no=line_no,
                        line=line,
                        module=module,
                        project=project,
                        candidate_kind="lean_identifier_reference",
                        declaration_kind="",
                        declaration_name="",
                        matched_term=identifier
                        if identifier in line
                        else short_identifier,
                    )
                )


def _lean_declaration_full_names(name: str, namespace_stack: Sequence[str]) -> set[str]:
    raw = str(name or "").strip()
    names = {raw} if raw else set()
    if raw and "." not in raw and namespace_stack:
        names.add(".".join([*namespace_stack, raw]))
    if raw and "." in raw:
        names.add(raw)
    return names


def _lean_identifier_hit(
    *,
    path: Path,
    line_no: int,
    line: str,
    module: str,
    project: Path,
    candidate_kind: str,
    declaration_kind: str,
    declaration_name: str,
    matched_term: str,
) -> dict[str, Any]:
    return {
        "path": str(path),
        "line": int(line_no),
        "module": module,
        "module_compiled": _lean_module_compiled_exists(project, module),
        "candidate_kind": candidate_kind,
        "declaration_kind": declaration_kind,
        "declaration_name": declaration_name,
        "matched_term": matched_term,
        "snippet": str(line or "").strip()[:320],
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    }


def _lean_module_compiled_exists(project: Path, module: str) -> bool:
    if not str(project) or not project.exists() or not module:
        return False
    module_path = Path(*module.split(".")).with_suffix(".olean")
    candidates = [
        project / ".lake" / "build" / "lib" / "lean" / module_path,
        project
        / ".lake"
        / "packages"
        / "mathlib"
        / ".lake"
        / "build"
        / "lib"
        / "lean"
        / module_path,
    ]
    return any(path.exists() for path in candidates)


def _first_existing_path(values: Sequence[Any]) -> Path | None:
    fallback: Path | None = None
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        path = Path(raw).expanduser()
        if fallback is None:
            fallback = path
        if path.exists():
            return path
    return fallback


def _candidate_import_modules_from_path(path: Path | None) -> list[str]:
    if path is None or not path.exists() or not path.is_file():
        return []
    try:
        return _split_leading_import_lines(path.read_text(encoding="utf-8"))[0]
    except OSError:
        return []
    except UnicodeDecodeError:
        return []


def _compiled_import_modules_for_project(project: Path) -> list[str]:
    roots = [
        project / ".lake" / "build" / "lib" / "lean",
        project / ".lake" / "packages" / "mathlib" / ".lake" / "build" / "lib" / "lean",
    ]
    modules: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.olean"):
            module = _lean_module_from_path(root, path, suffix=".olean")
            if module and module not in modules:
                modules.append(module)
    return sorted(modules)


def _lean_module_source_exists(project: Path, module: str) -> bool:
    if not str(project) or not project.exists() or not module:
        return False
    module_path = Path(*module.split(".")).with_suffix(".lean")
    candidates = [
        project / module_path,
        project / ".lake" / "packages" / "mathlib" / module_path,
    ]
    return any(path.exists() for path in candidates)


def _lean_module_from_path(root: Path, path: Path, *, suffix: str) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return ""
    raw = str(relative)
    if suffix and raw.endswith(suffix):
        raw = raw[: -len(suffix)]
    return ".".join(part for part in Path(raw).parts if part)


def _nearest_verified_import_modules(
    module: str,
    compiled_modules: Sequence[str],
    *,
    limit: int,
) -> list[str]:
    if limit <= 0 or not module or not compiled_modules:
        return []
    scored = [
        (_lean_import_similarity_score(module, candidate), candidate)
        for candidate in compiled_modules
    ]
    scored = [(score, candidate) for score, candidate in scored if score > 0]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [candidate for _, candidate in scored[:limit]]


def _unavailable_import_repair_row(
    module: str,
    *,
    compiled_modules: Sequence[str],
    limit: int,
) -> dict[str, Any]:
    compiled_set = set(compiled_modules)
    exact_modules = [module] if module in compiled_set else []
    descendant_modules = _verified_descendant_import_modules(
        module,
        compiled_modules,
        limit=limit,
    )
    exact_or_descendant_modules = list(
        dict.fromkeys([*exact_modules, *descendant_modules])
    )[:limit]
    return {
        "unavailable_import": module,
        "unavailable_import_compiled": module in compiled_set,
        "verified_exact_or_descendant_modules": exact_or_descendant_modules,
        "nearest_verified_modules": _nearest_verified_import_modules(
            module,
            compiled_modules,
            limit=limit,
        ),
        "repair_options": _unavailable_import_repair_options(
            verified_exact_or_descendant_modules=exact_or_descendant_modules,
        ),
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    }


def _verified_descendant_import_modules(
    module: str,
    compiled_modules: Sequence[str],
    *,
    limit: int,
) -> list[str]:
    prefix = f"{module}."
    descendants = [
        candidate
        for candidate in compiled_modules
        if candidate.startswith(prefix)
    ]
    descendants.sort(key=lambda candidate: (len(candidate.split(".")), candidate))
    return descendants[:limit]


def _unavailable_import_repair_options(
    *,
    verified_exact_or_descendant_modules: Sequence[str],
) -> list[str]:
    options = [
        "remove the unavailable import if the definition can be made self-contained",
        (
            "record blocked_or_insufficient_context or known_gaps if no verified "
            "module provides the required API"
        ),
        (
            "do not replace the unavailable import with a nearby sibling module "
            "unless the sibling is verified by source lookup or a local Lean rerun"
        ),
    ]
    if verified_exact_or_descendant_modules:
        options.insert(
            0,
            (
                "replace the unavailable import with one "
                "verified_exact_or_descendant_module and rerun local Lean"
            ),
        )
    return options


def _lean_import_similarity_score(target: str, candidate: str) -> int:
    target_parts = [part.lower() for part in target.split(".") if part]
    candidate_parts = [part.lower() for part in candidate.split(".") if part]
    if not target_parts or not candidate_parts:
        return 0
    if candidate == target:
        return 10000
    if candidate.startswith(f"{target}."):
        return 8000 - min(len(candidate_parts) - len(target_parts), 100)
    if target.startswith(f"{candidate}."):
        return 5000 - min(len(target_parts) - len(candidate_parts), 100)
    score = 0
    for left, right in zip(target_parts, candidate_parts):
        if left != right:
            break
        score += 8
    for left, right in zip(reversed(target_parts), reversed(candidate_parts)):
        if left != right:
            break
        score += 10
    overlap = set(target_parts) & set(candidate_parts)
    score += 4 * len(overlap)
    if target_parts[-1] == candidate_parts[-1]:
        score += 16
    if len(target_parts) >= 2 and len(candidate_parts) >= 2:
        if target_parts[-2:] == candidate_parts[-2:]:
            score += 12
        if target_parts[:2] == candidate_parts[:2]:
            score += 10
    return score


def _lean_unknown_identifiers_from_diagnostics(
    diagnostics: Sequence[str],
) -> list[str]:
    identifiers: list[str] = []
    patterns = (
        re.compile(
            r"\bUnknown constant\s+[`']?"
            r"([A-Za-z_][A-Za-z0-9_'?]*(?:\.[A-Za-z_][A-Za-z0-9_'?]*)*)",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bunknown identifier\s+[`']?"
            r"([A-Za-z_][A-Za-z0-9_'?]*(?:\.[A-Za-z_][A-Za-z0-9_'?]*)*)",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bInvalid field\s+[`']?"
            r"([A-Za-z_][A-Za-z0-9_'?]*(?:\.[A-Za-z_][A-Za-z0-9_'?]*)*)",
            re.IGNORECASE,
        ),
        re.compile(
            r"\benvironment does not contain\s+[`']?"
            r"([A-Za-z_][A-Za-z0-9_'?]*(?:\.[A-Za-z_][A-Za-z0-9_'?]*)*)",
            re.IGNORECASE,
        ),
    )
    for diagnostic in diagnostics:
        for pattern in patterns:
            for match in pattern.finditer(str(diagnostic or "")):
                identifier = _lean_diagnostic_token(match.group(1))
                if identifier and identifier not in identifiers:
                    identifiers.append(identifier)
    return identifiers


def _lean_typeclass_failures_from_diagnostics(
    diagnostics: Sequence[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    normalized = [str(diagnostic or "") for diagnostic in diagnostics]
    for index, diagnostic in enumerate(normalized):
        if "failed to synthesize instance" not in diagnostic.lower():
            continue
        failed_instance_type = _lean_failed_instance_type_from_diagnostic(
            diagnostic,
            normalized[index + 1] if index + 1 < len(normalized) else "",
        )
        failed_typeclass = _lean_typeclass_head(failed_instance_type)
        if not failed_instance_type or not failed_typeclass:
            continue
        row = {
            "failed_typeclass": failed_typeclass,
            "failed_instance_type": failed_instance_type,
            "diagnostic_excerpt": diagnostic.strip()[:320],
        }
        if row not in rows:
            rows.append(row)
    return rows


def _lean_failed_instance_type_from_diagnostic(
    diagnostic: str,
    next_diagnostic: str,
) -> str:
    next_text = str(next_diagnostic or "").strip()
    if next_text and not next_text.lower().startswith("hint:"):
        return next_text[:240]
    match = re.search(
        r"failed to synthesize instance(?: of type class)?\s*[:`']?\s*(.+)$",
        str(diagnostic or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    return _lean_diagnostic_token(match.group(1))[:240]


def _lean_typeclass_head(instance_type: str) -> str:
    match = re.search(
        r"\b([A-Za-z_][A-Za-z0-9_'?]*(?:\.[A-Za-z_][A-Za-z0-9_'?]*)*)",
        str(instance_type or ""),
    )
    return _lean_diagnostic_token(match.group(1)) if match else ""


def _lean_unavailable_imports_from_diagnostics(
    diagnostics: Sequence[str],
) -> list[str]:
    modules: list[str] = []
    pattern = re.compile(
        r"\bmodule\s+"
        r"([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)"
        r"\s+does not exist",
        re.IGNORECASE,
    )
    for diagnostic in diagnostics:
        for match in pattern.finditer(str(diagnostic or "")):
            module = _lean_diagnostic_token(match.group(1))
            if module and module not in modules:
                modules.append(module)
    return modules


def _lean_diagnostic_token(value: str) -> str:
    return str(value or "").strip().strip("`'\".,;:()[]{}")


def _semantic_review_contract(task: Mapping[str, Any]) -> dict[str, Any]:
    raw_contract = task.get("semantic_review_contract")
    contract = dict(raw_contract) if isinstance(raw_contract, Mapping) else {}
    contract.setdefault(
        "contract_kind",
        "exact_semantic_definition_authoring_semantic_review",
    )
    contract.setdefault(
        "review_decision_values",
        [
            "approved_definition_candidate",
            "repair_required",
            "blocked_or_insufficient_context",
        ],
    )
    contract.setdefault(
        "required_review_checks",
        [
            "compare the candidate against source theorem binders",
            "check required semantic anchors and adapter dependencies",
            "preserve local Lean typecheckability constraints",
            "classify unresolved known gaps separately from resolved evidence",
        ],
    )
    contract.setdefault(
        "known_gap_classification_policy",
        _semantic_review_output_policy(task),
    )
    contract["semantic_review_required_before_proof_body"] = bool(
        task.get("semantic_review_required_before_proof_body", True)
    )
    contract["source_theorem_ready_for_exact_proof_body"] = False
    contract.setdefault(
        "proof_body_promotion_gate",
        (
            "LLM semantic review evidence is not source theorem proof and must "
            "not set source_theorem_ready_for_exact_proof_body. A later local "
            "Lean/AXLE recheck queue must verify any reviewed candidate before "
            "exact proof-body work resumes."
        ),
    )
    contract.setdefault(
        "proof_evidence_status",
        AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    )
    return contract


def _semantic_review_output_policy(task: Mapping[str, Any]) -> dict[str, Any]:
    """Describe how semantic-review output should classify gaps."""

    authoring_mode = str(task.get("authoring_mode", "") or "")
    policy = {
        "known_gaps_mean": (
            "unresolved definition-level blockers only: missing source binders, "
            "unverified imports/APIs required by the definition, or semantic "
            "mismatches that require repair before verifier-gate recheck"
        ),
        "known_gaps_do_not_include": [
            "issues already resolved by recovered source binders or source anchors",
            "imports that the local project inventory or local Lean run already verified",
            "future project-structure caveats with no current diagnostic",
            "proof-body obligations that can be discharged later from source theorem hypotheses",
        ],
        "nonblocking_items_go_to": [
            "semantic_review_evidence",
            "resolved_gap_evidence",
            "proof_body_obligations",
            "semantic_alignment_notes",
        ],
        "proof_boundary": (
            "Even with known_gaps=[], this is semantic-readiness evidence only, "
            "not source theorem proof or proof-body readiness."
        ),
    }
    if authoring_mode == "review_typechecked_semantic_definition_candidate":
        policy["review_mode_gate"] = (
            "For semantic_review_decision=approved_definition_candidate, "
            "known_gaps must be [] because the later verifier gate treats any "
            "known_gaps as hard blockers."
        )
        policy["approved_review_required_fields"] = [
            "semantic_review_evidence explaining source-binder/source-anchor agreement",
            "resolved_gap_evidence for prior known gaps that were discharged",
            "proof_body_obligations for downstream theorem facts such as measurability lemmas",
            "source_theorem_ready_for_exact_proof_body=false",
        ]
    return policy


def _lean_authoring_environment_contract(
    task: Mapping[str, Any],
    *,
    candidate_definition_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return local Lean constraints that keep generated definitions checkable."""

    placeholder_policy = exact_semantic_definition_placeholder_policy(
        str(
            task.get("placeholder_symbol", "")
            or candidate_definition_request.get("placeholder_symbol", "")
            or ""
        )
    )
    source_binders = _authoring_source_theorem_binders(
        task,
        candidate_definition_request=candidate_definition_request,
        placeholder_policy=placeholder_policy,
    )
    lean_feedback = _lean_feedback_contract(task)
    response_validation_feedback = _response_validation_feedback(task)
    response_validation_unverified_imports = _string_list(
        response_validation_feedback.get("unverified_required_imports", [])
    )
    import_inventory = _lean_project_import_inventory_contract(
        task,
        lean_feedback=lean_feedback,
    )
    identifier_lookup = _lean_project_identifier_lookup_contract(
        task,
        lean_feedback=lean_feedback,
        import_inventory=import_inventory,
    )
    identifier_reuse_policy = [
        dict(row)
        for row in identifier_lookup.get("identifier_reuse_policy", []) or []
        if isinstance(row, Mapping)
    ]
    hard_negative_identifier_rows = [
        dict(row)
        for row in identifier_lookup.get("hard_negative_identifier_rows", []) or []
        if isinstance(row, Mapping)
    ]
    identifiers_with_no_verified_declaration_module = [
        str(row.get("identifier", "") or "").strip()
        for row in hard_negative_identifier_rows
        if str(row.get("identifier", "") or "").strip()
    ]
    parse_error_source_fragments = _string_list(
        lean_feedback.get("parse_error_source_fragments_from_all_checks", [])
    )
    repair_policy = [
        (
            "Treat local Lean diagnostics as hard feedback about the configured "
            "Lake project, not as a prompt to guess adjacent APIs."
        ),
        (
            "Do not introduce a new import, namespace, theorem, or API swap "
            "solely by analogy. Use only identifiers/imports grounded in the "
            "source references, previous candidate, explicit binders, or a "
            "verified local project inventory; otherwise simplify the definition "
            "or list the need in known_gaps."
        ),
        (
            "For unknown identifiers, prefer removing the dependency, adding an "
            "explicit parameter, or returning blocked_or_insufficient_context "
            "over replacing it with another unverified identifier/import."
        ),
    ]
    if lean_feedback["unavailable_imports_from_all_checks"]:
        repair_policy.append(
            (
                "Imports reported unavailable by any prior local Lean check must "
                "not be reintroduced unless a later verified project inventory shows "
                "the module exists."
            )
        )
        repair_policy.append(
            (
                "For unavailable imports, consult "
                "project_verified_import_inventory.unavailable_import_repair_rows. "
                "If verified_exact_or_descendant_modules is nonempty, use one of "
                "those exact compiled modules before considering looser nearby "
                "modules, then rerun local Lean."
            )
        )
    if import_inventory["unverified_candidate_import_modules"]:
        repair_policy.append(
            (
                "Imports listed in unverified_candidate_import_modules did not "
                "appear in the compiled local project inventory. Do not treat "
                "nearby_verified_import_modules_by_unavailable_import as API "
                "evidence; prefer unavailable_import_repair_rows exact/descendant "
                "modules, and use nearby modules only as lookup targets for "
                "source/RAG/local Lean checks."
            )
        )
    if response_validation_unverified_imports:
        repair_policy.append(
            (
                "Imports rejected by response_validation_feedback."
                "unverified_required_imports must not be reused unless the "
                "project inventory, identifier lookup, or a later local Lean "
                "check verifies the exact module. Put unresolved modules in "
                "known_gaps instead of required_imports."
            )
        )
    if lean_feedback["typeclass_failures_from_all_checks"]:
        repair_policy.append(
            (
                "For typeclass synthesis failures, use "
                "local_lean_feedback.typeclass_failures_from_all_checks and "
                "project_identifier_lookup rows with lookup_reason="
                "typeclass_synthesis_failure. A class declaration lookup is not "
                "an instance proof; repair by removing/parameterizing the "
                "operation, retrieving an actual instance declaration, or failing "
                "closed as insufficient context. Any replacement operation must "
                "have its own source lookup or local Lean check before use."
            )
        )
    if lean_feedback["unknown_identifiers_from_all_checks"]:
        repair_policy.append(
            (
                "For identifiers that failed in any prior local Lean check, consult "
                "project_identifier_lookup before adding imports or replacing APIs. "
                "Verified declaration modules are retrieval targets only; the "
                "materialized definition must still pass local Lean/AXLE before review."
            )
        )
        repair_policy.append(
            (
                "If project_identifier_lookup gives verified_declaration_modules "
                "for an unknown identifier, either import one of those modules and "
                "rerun local Lean for the same identifier, or remove/parameterize "
                "the dependency. Do not swap to a sibling API that lacks its own "
                "lookup hit or local Lean check."
            )
        )
    if hard_negative_identifier_rows:
        repair_policy.append(
            (
                "Identifiers listed in "
                "hard_local_negative_constraints."
                "identifiers_with_no_verified_declaration_module have no verified "
                "declaration module in the current lookup. Do not reuse those "
                "exact tokens in lean_definition_candidate; remove or parameterize "
                "the dependency, or return blocked_or_insufficient_context."
            )
        )
    if parse_error_source_fragments:
        repair_policy.append(
            (
                "Fragments listed in hard_local_negative_constraints."
                "parse_error_source_fragments_must_not_reuse came from local "
                "Lean parse errors. Do not reuse those exact syntax fragments; "
                "rewrite with project-verified syntax, remove/parameterize the "
                "operation, or return blocked_or_insufficient_context."
            )
        )
    structural_reformulation_policy: list[str] = []
    if (
        hard_negative_identifier_rows
        or parse_error_source_fragments
        or lean_feedback["typeclass_failures_from_all_checks"]
    ):
        structural_reformulation_policy = [
            (
                "Repeated local Lean API, syntax, or typeclass failures are a "
                "semantic-design signal, not merely an API-renaming task."
            ),
            (
                "If the exact statistical object still requires order-statistic, "
                "rounding, indexing, or typeclass infrastructure that is not "
                "project-verified, reformulate the definition around explicit "
                "parameters or verified primitives, or return "
                "blocked_or_insufficient_context with the missing primitive "
                "named precisely."
            ),
            (
                "A downstream PF/BV structural decomposition may be required to "
                "split the semantic obligation into source-grounded blocks before "
                "another Lean candidate is authored."
            ),
        ]
    required_anchor_names = [
        str(value).strip()
        for value in candidate_definition_request.get("required_anchor_names", [])
        or []
        if str(value).strip()
    ]
    return {
        "candidate_scope": "definition_or_abbrev_only",
        "source_theorem_binder_count": len(source_binders),
        "source_theorem_binders": source_binders[:32],
        "required_anchor_names": required_anchor_names,
        "required_anchor_bindings": [
            dict(row)
            for row in candidate_definition_request.get("required_anchor_bindings", [])
            or []
            if isinstance(row, Mapping)
        ],
        "import_policy": [
            (
                "Use the smallest import list needed by the definition-only "
                "candidate; prefer no imports when explicit binder types can make "
                "the candidate self-contained."
            ),
            (
                "Do not add broad probability, measure, topology, tactic, or "
                "umbrella imports just because the statistical theorem is about "
                "those domains. If such an import is uncertain in the local Lake "
                "project, omit it and list the need in known_gaps."
            ),
            (
                "required_imports must contain module names such as "
                "Mathlib.Data.Set.Basic, not strings starting with `import`."
            ),
            (
                "When no project-verified import inventory is present, treat new "
                "imports as unverified: prefer existing candidate imports, source "
                "reference imports, or known_gaps over speculative import names."
            ),
            (
                "When project_verified_import_inventory is available, required_imports "
                "should be limited to verified_candidate_import_modules unless "
                "known_gaps explicitly records the missing import/API."
            ),
            (
                "When repairing an unavailable import, required_imports may add "
                "one module from unavailable_import_repair_rows."
                "verified_exact_or_descendant_modules; do not add parent or "
                "sibling modules merely because their names are nearby."
            ),
        ],
        "binder_policy": [
            (
                "Every identifier used in the candidate type or body must be an "
                "explicit parameter, a documented source_theorem_binder, or a "
                "required anchor from candidate_definition_request."
            ),
            (
                "If source theorem binders are absent or incomplete, write a "
                "small generic definition over explicit parameters instead of "
                "inventing hidden theorem-local names."
            ),
        ],
        "local_lean_policy": [
            (
                "The candidate is not proof evidence unless a later local Lean/AXLE "
                "manifest checks the materialized definition."
            ),
            (
                "Prefer compiling a modest semantic object over generating an "
                "ambitious theorem-shaped construction that depends on unavailable "
                "imports or unproved order-statistic infrastructure."
            ),
        ],
        "local_lean_feedback": lean_feedback,
        "diagnostic_source_excerpts": list(
            lean_feedback.get("diagnostic_source_excerpts", []) or []
        )[:3],
        "hard_local_negative_constraints": {
            "unavailable_imports_must_not_reintroduce": list(
                lean_feedback.get("unavailable_imports_from_all_checks", []) or []
            ),
            "unverified_imports_rejected_by_response_validator": (
                response_validation_unverified_imports
            ),
            "identifier_reuse_policy": identifier_reuse_policy,
            "identifiers_with_no_verified_declaration_module": (
                identifiers_with_no_verified_declaration_module
            ),
            "parse_error_source_fragments_must_not_reuse": (
                parse_error_source_fragments
            ),
        },
        "response_validation_feedback": response_validation_feedback,
        "project_verified_import_inventory": import_inventory,
        "verified_local_project_import_inventory": import_inventory,
        "project_identifier_lookup": identifier_lookup,
        "repair_policy": repair_policy,
        "structural_reformulation_policy": structural_reformulation_policy,
    }


def _candidate_definition_request_from_task(task: Mapping[str, Any]) -> dict[str, Any]:
    placeholder_symbol = str(task.get("placeholder_symbol", "") or "")
    placeholder_policy = exact_semantic_definition_placeholder_policy(placeholder_symbol)
    required_anchor_names = _required_anchor_names_for_placeholder(placeholder_symbol)
    available_binders_by_name = _available_semantic_binders_by_name(
        task,
        placeholder_policy=placeholder_policy,
    )
    required_anchor_bindings = exact_semantic_definition_required_anchor_bindings(
        required_anchor_names=required_anchor_names,
        available_binders_by_name=available_binders_by_name,
        placeholder_policy=placeholder_policy,
    )
    available_anchor_names = list(
        dict.fromkeys([*available_binders_by_name, *required_anchor_bindings])
    )
    required_binders = [
        dict(required_anchor_bindings[name]["binder"])
        for name in required_anchor_names
        if name in required_anchor_bindings
    ]
    required_adapter_object_names = (
        _required_adapter_object_names_for_placeholder(placeholder_symbol)
    )
    available_adapter_object_names = [
        str(value).strip()
        for value in task.get(
            "source_to_bridge_adapter_object_names_requiring_source_instantiation",
            [],
        )
        or []
        if str(value).strip()
    ]
    return {
        "schema_version": 1,
        "request_kind": "source_theorem_exact_semantic_definition_candidate",
        "target_theorem_name": str(task.get("target_theorem_name", "") or ""),
        "placeholder_symbol": placeholder_symbol,
        "placeholder_policy_id": placeholder_policy.policy_id,
        "placeholder_policy_scope": placeholder_policy.policy_scope,
        "semantic_goal": _semantic_goal_for_placeholder(placeholder_symbol),
        "required_anchor_names": required_anchor_names,
        "available_anchor_names": available_anchor_names,
        "missing_required_anchor_names": [
            name for name in required_anchor_names if name not in available_anchor_names
        ],
        "required_anchor_bindings": list(required_anchor_bindings.values()),
        "required_binders": required_binders,
        "required_adapter_object_names": required_adapter_object_names,
        "available_adapter_object_names": available_adapter_object_names,
        "missing_required_adapter_object_names": [
            name
            for name in required_adapter_object_names
            if name not in available_adapter_object_names
        ],
        "source_to_bridge_adapter_instantiation_group_id": str(
            task.get("source_to_bridge_adapter_instantiation_group_id", "") or ""
        ),
        "required_bridge_premise_names_for_shared_instantiation": list(
            task.get("required_bridge_premise_names_for_shared_instantiation", [])
            or []
        ),
        "forbidden_shortcuts": [
            "do not define the placeholder as True",
            "do not add axiom/sorry/admit/unsafe",
            "do not assume or restate the source theorem target",
            "do not introduce stronger assumptions than the source theorem binders",
            "do not import generic declarations found by lexical source lookup as the definition",
        ],
        "local_lean_gate": (
            "The definition-only candidate must compile under local Lean/AXLE "
            "before it can be used by proof-body execution; compilation is still "
            "semantic-definition evidence only, not theorem proof."
        ),
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    }


def _semantic_goal_for_placeholder(placeholder_symbol: str) -> str:
    return exact_semantic_definition_placeholder_policy(placeholder_symbol).semantic_goal


def _required_anchor_names_for_placeholder(placeholder_symbol: str) -> list[str]:
    return list(
        exact_semantic_definition_placeholder_policy(
            placeholder_symbol
        ).required_anchor_names
    )


def _available_semantic_binders_by_name(
    task: Mapping[str, Any],
    *,
    placeholder_policy: Any | None = None,
) -> dict[str, Mapping[str, Any]]:
    binders_by_name: dict[str, Mapping[str, Any]] = {}
    for binder in exact_semantic_definition_source_binders_from_context(
        task,
        placeholder_policy=placeholder_policy,
    ):
        name = str(binder.get("name", "") or "")
        if name:
            binders_by_name[name] = binder
    for binder in task.get("premise_semantic_anchor_binders", []) or []:
        if not isinstance(binder, Mapping):
            continue
        name = str(binder.get("name", "") or "")
        if name and name not in binders_by_name:
            binders_by_name[name] = binder
    for binder in task.get("exact_source_theorem_binders", []) or []:
        if not isinstance(binder, Mapping):
            continue
        name = str(binder.get("name", "") or "")
        if name and name not in binders_by_name:
            binders_by_name[name] = binder
    return binders_by_name


def _required_adapter_object_names_for_placeholder(
    placeholder_symbol: str,
) -> list[str]:
    return list(
        exact_semantic_definition_placeholder_policy(
            placeholder_symbol
        ).required_adapter_object_names
    )


def _generate_candidate_packet(
    task: Mapping[str, Any],
    *,
    prompt_packet: Mapping[str, Any],
    provider: GeneratorBackend,
    config: AuthoringWorkerConfig,
) -> dict[str, Any]:
    request_model = resolve_generator_model(
        provider_name=config.provider_name,
        requested_model=config.model,
        model_tier=config.model_tier,
    )
    request = GeneratorRequest(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=str(prompt_packet.get("user_prompt", "") or ""),
        model=request_model,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        schema=AUTHORING_RESPONSE_JSON_SCHEMA,
        metadata={
            "subsystem": "ExactSemanticDefinitionAuthoringWorker",
            "provider_name": config.provider_name,
            "model_tier": config.model_tier,
            "resolved_model": request_model,
            "source_authoring_task_id": str(task.get("authoring_task_id", "") or ""),
        },
    )

    def build_packet(payload: Mapping[str, Any], response: Any, raw_text: str) -> dict[str, Any]:
        return _normalize_candidate_packet(
            payload,
            task=task,
            prompt_packet=prompt_packet,
            provider_name=config.provider_name or response.provider,
            backend_provider_name=response.provider,
            model=response.model or request_model,
            model_tier=config.model_tier,
            raw_response=raw_text,
            response_metadata=response.metadata,
        )

    try:
        return generate_validated_json_packet(
            provider=provider,
            request=request,
            extract_payload=_extract_payload,
            build_packet=build_packet,
            validate_packet=validate_authoring_candidate_packet,
            validation_label="Exact semantic-definition authoring candidate packet",
            max_repair_attempts=config.max_repair_attempts,
        )
    except Exception as exc:
        return _failed_candidate_packet(
            task,
            prompt_packet=prompt_packet,
            provider_name=config.provider_name,
            backend_provider_name=str(
                getattr(provider, "provider_name", config.provider_name) or ""
            ),
            model=request_model,
            model_tier=config.model_tier,
            error=exc,
        )


def validate_authoring_candidate_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if str(packet.get("placeholder_symbol", "") or "").strip() == "":
        errors.append("missing placeholder_symbol")
    if str(packet.get("definition_design", "") or "").strip() == "":
        errors.append("missing definition_design")
    lean_source = str(packet.get("lean_definition_candidate", "") or "")
    if not lean_source.strip():
        errors.append("missing lean_definition_candidate")
    if "def " not in lean_source and "abbrev " not in lean_source:
        errors.append("lean_definition_candidate must contain a def or abbrev")
    lowered = lean_source.lower()
    for fragment in FORBIDDEN_SOURCE_FRAGMENTS:
        if fragment.lower() in lowered:
            errors.append(
                "lean_definition_candidate contains forbidden shortcut: "
                + fragment.strip()
            )
    if packet.get("forbidden_shortcuts_absent") is not True:
        errors.append("forbidden_shortcuts_absent must be true")
    if packet.get("requires_local_lean_check") is not True:
        errors.append("requires_local_lean_check must be true")
    if packet.get("local_definition_lean_checked") is not False:
        errors.append("authoring candidate cannot set local_definition_lean_checked=true")
    if packet.get("local_definition_lean_compiled") is not False:
        errors.append("authoring candidate cannot set local_definition_lean_compiled=true")
    if packet.get("semantic_definition_kernel_verified") is not False:
        errors.append("authoring candidate cannot set semantic_definition_kernel_verified=true")
    if packet.get("source_theorem_kernel_verified") is not False:
        errors.append("authoring candidate cannot set source_theorem_kernel_verified=true")
    if packet.get("proof_evidence_status") != CANDIDATE_PROOF_EVIDENCE_STATUS:
        errors.append("proof_evidence_status must preserve candidate-only boundary")
    if _approved_review_packet_has_known_gaps(packet):
        errors.append(
            "review_typechecked approved_definition_candidate packets must keep "
            "known_gaps empty; put resolved issues in semantic_review_evidence/"
            "resolved_gap_evidence and downstream theorem obligations in "
            "proof_body_obligations"
        )
    missing_review_anchors = _approved_review_packet_missing_required_anchors(packet)
    if missing_review_anchors:
        errors.append(
            "review_typechecked approved_definition_candidate packets cannot "
            "approve semantic review while candidate_definition_request still "
            "has missing_required_anchor_names: "
            + ", ".join(missing_review_anchors[:8])
        )
    forbidden_claim = _contains_forbidden_proof_claim(packet)
    if forbidden_claim:
        errors.append(f"packet contains forbidden proof claim: {forbidden_claim}")
    verified_import_modules = _verified_import_modules_for_candidate_packet(packet)
    body_imports, _ = _split_leading_import_lines(lean_source)
    declared_required_imports = _lean_import_modules(
        packet.get("required_imports", []) or []
    )
    missing_declared_imports = [
        module for module in body_imports if module not in declared_required_imports
    ]
    if missing_declared_imports:
        errors.append(
            "lean_definition_candidate import declarations must be mirrored in "
            "required_imports: "
            + ", ".join(missing_declared_imports[:8])
        )
    required_imports = _lean_import_modules(
        [
            *declared_required_imports,
            *body_imports,
        ]
    )
    if verified_import_modules and required_imports:
        unverified_imports = [
            module
            for module in required_imports
            if module not in verified_import_modules
        ]
        if unverified_imports:
            errors.append(
                "required_imports include modules not verified by the local "
                "project inventory or identifier lookup: "
                + ", ".join(unverified_imports[:8])
            )
    unresolved_reused_identifiers = (
        _unverified_unresolved_identifiers_reused_by_candidate_packet(packet)
    )
    if unresolved_reused_identifiers:
        errors.append(
            "lean_definition_candidate reuses locally unresolved identifiers "
            "without a candidate import from verified_declaration_modules; "
            "remove or parameterize them, or return "
            "blocked_or_insufficient_context when no verified module exists: "
            + ", ".join(unresolved_reused_identifiers[:8])
        )
    typeclass_failure_reused_identifiers = (
        _typeclass_failure_identifiers_reused_by_candidate_packet(packet)
    )
    if typeclass_failure_reused_identifiers:
        errors.append(
            "lean_definition_candidate reuses identifiers from prior "
            "typeclass-failing source lines without an instance-level repair: "
            + ", ".join(typeclass_failure_reused_identifiers[:8])
        )
    parse_error_fragments = _parse_error_source_fragments_reused_by_candidate_packet(
        packet
    )
    if parse_error_fragments:
        errors.append(
            "lean_definition_candidate reuses prior local Lean parse-error "
            "source fragments without verified syntax repair: "
            + ", ".join(parse_error_fragments[:6])
        )
    return sorted(set(errors))


def _approved_review_packet_has_known_gaps(packet: Mapping[str, Any]) -> bool:
    if (
        str(packet.get("authoring_mode", "") or "")
        != "review_typechecked_semantic_definition_candidate"
    ):
        return False
    if str(packet.get("semantic_review_decision", "") or "") != (
        "approved_definition_candidate"
    ):
        return False
    return bool(_string_list(packet.get("known_gaps", [])))


def _approved_review_packet_missing_required_anchors(
    packet: Mapping[str, Any],
) -> list[str]:
    if (
        str(packet.get("authoring_mode", "") or "")
        != "review_typechecked_semantic_definition_candidate"
    ):
        return []
    if str(packet.get("semantic_review_decision", "") or "") != (
        "approved_definition_candidate"
    ):
        return []
    request = packet.get("candidate_definition_request", {})
    if not isinstance(request, Mapping):
        return []
    return _string_list(request.get("missing_required_anchor_names", []) or [])


def _verified_import_modules_for_candidate_packet(
    packet: Mapping[str, Any],
) -> set[str]:
    contract = packet.get("lean_authoring_environment_contract", {})
    if not isinstance(contract, Mapping):
        return set()
    inventory = contract.get("project_verified_import_inventory", {})
    if not isinstance(inventory, Mapping):
        inventory = contract.get("verified_local_project_import_inventory", {})
    if not isinstance(inventory, Mapping):
        inventory = {}
    verified: set[str] = set()
    for key in (
        "verified_candidate_import_modules",
        "verified_import_modules",
    ):
        for module in inventory.get(key, []) or []:
            module_text = str(module or "").strip()
            if module_text:
                verified.add(module_text)
    for row in inventory.get("unavailable_import_repair_rows", []) or []:
        if not isinstance(row, Mapping):
            continue
        for module in row.get("verified_exact_or_descendant_modules", []) or []:
            module_text = str(module or "").strip()
            if module_text:
                verified.add(module_text)
    lookup = contract.get("project_identifier_lookup", {})
    if isinstance(lookup, Mapping):
        lookup_rows = [
            *(lookup.get("identifier_lookup_rows", []) or []),
            *(lookup.get("unknown_identifier_rows", []) or []),
        ]
        typeclass_declaration_modules: set[str] = set()
        for row in lookup_rows:
            if not isinstance(row, Mapping):
                continue
            if (
                str(row.get("lookup_reason", "") or "")
                == "typeclass_synthesis_failure"
            ):
                typeclass_declaration_modules.update(
                    str(module).strip()
                    for module in row.get("verified_declaration_modules", []) or []
                    if str(module).strip()
                )
                continue
            for module in row.get("verified_declaration_modules", []) or []:
                module_text = str(module or "").strip()
                if module_text:
                    verified.add(module_text)
        verified.difference_update(typeclass_declaration_modules)
    return verified


def _unverified_unresolved_identifiers_reused_by_candidate_packet(
    packet: Mapping[str, Any],
) -> list[str]:
    contract = packet.get("lean_authoring_environment_contract", {})
    if not isinstance(contract, Mapping):
        return []
    feedback = contract.get("local_lean_feedback", {})
    if not isinstance(feedback, Mapping):
        return []
    identifiers = [
        str(value).strip()
        for value in (
            feedback.get("unknown_identifiers_from_all_checks", [])
            or feedback.get("unknown_identifiers_from_last_check", [])
            or []
        )
        if str(value).strip()
    ]
    if not identifiers:
        return []
    verified_by_identifier: dict[str, set[str]] = {}
    lookup = contract.get("project_identifier_lookup", {})
    if isinstance(lookup, Mapping):
        lookup_rows = [
            *(lookup.get("identifier_lookup_rows", []) or []),
            *(lookup.get("unknown_identifier_rows", []) or []),
        ]
        for row in lookup_rows:
            if not isinstance(row, Mapping):
                continue
            identifier = str(
                row.get("unknown_identifier", "")
                or row.get("lookup_identifier", "")
                or ""
            ).strip()
            if not identifier:
                continue
            verified_by_identifier.setdefault(identifier, set()).update(
                str(module).strip()
                for module in row.get("verified_declaration_modules", []) or []
                if str(module).strip()
            )
    lean_source = str(packet.get("lean_definition_candidate", "") or "")
    body_imports, _ = _split_leading_import_lines(lean_source)
    required_imports = set(
        _lean_import_modules(
            [
                *(packet.get("required_imports", []) or []),
                *body_imports,
            ]
        )
    )
    reused: list[str] = []
    for identifier in identifiers:
        verified_modules = verified_by_identifier.get(identifier, set())
        if _lean_source_mentions_unresolved_identifier(lean_source, identifier):
            if verified_modules and required_imports.intersection(verified_modules):
                continue
            reused.append(identifier)
    return list(dict.fromkeys(reused))


def _typeclass_failure_identifiers_reused_by_candidate_packet(
    packet: Mapping[str, Any],
) -> list[str]:
    contract = packet.get("lean_authoring_environment_contract", {})
    if not isinstance(contract, Mapping):
        return []
    feedback = contract.get("local_lean_feedback", {})
    if not isinstance(feedback, Mapping):
        return []
    diagnostic_excerpts = _dedup_mapping_rows(
        [
            *(feedback.get("diagnostic_source_excerpts_history", []) or []),
            *(feedback.get("diagnostic_source_excerpts", []) or []),
        ]
    )
    if not (
        feedback.get("typeclass_failures_from_all_checks", [])
        or feedback.get("typeclass_failures_from_last_check", [])
    ) and not any(
        "failed to synthesize instance" in str(row.get("diagnostic", "")).lower()
        for row in diagnostic_excerpts
        if isinstance(row, Mapping)
    ):
        return []
    candidate_source = str(packet.get("lean_definition_candidate", "") or "")
    failing_identifiers: list[str] = []
    for excerpt in diagnostic_excerpts:
        if not isinstance(excerpt, Mapping):
            continue
        diagnostic = str(excerpt.get("diagnostic", "") or "")
        if "failed to synthesize instance" not in diagnostic.lower():
            continue
        line_number = int(excerpt.get("line", 0) or 0)
        for source_line in excerpt.get("source_excerpt", []) or []:
            line_text = str(source_line or "")
            if line_number > 0 and not line_text.startswith(f"{line_number}:"):
                continue
            for identifier in _compound_lean_identifiers(line_text):
                if _lean_source_mentions_unresolved_identifier(
                    candidate_source,
                    identifier,
                ):
                    failing_identifiers.append(identifier)
    return list(dict.fromkeys(failing_identifiers))


def _parse_error_source_fragments_reused_by_candidate_packet(
    packet: Mapping[str, Any],
) -> list[str]:
    contract = packet.get("lean_authoring_environment_contract", {})
    if not isinstance(contract, Mapping):
        return []
    fragments: list[str] = []
    hard_constraints = contract.get("hard_local_negative_constraints", {})
    if isinstance(hard_constraints, Mapping):
        fragments.extend(
            _string_list(
                hard_constraints.get(
                    "parse_error_source_fragments_must_not_reuse",
                    [],
                )
            )
        )
    feedback = contract.get("local_lean_feedback", {})
    if isinstance(feedback, Mapping):
        fragments.extend(
            _string_list(
                feedback.get("parse_error_source_fragments_from_all_checks", [])
            )
        )
    lean_source = str(packet.get("lean_definition_candidate", "") or "")
    reused: list[str] = []
    for fragment in _dedup_strings(fragments):
        if len(fragment) >= 3 and fragment in lean_source:
            reused.append(fragment)
    return reused


def _compound_lean_identifiers(text: str) -> list[str]:
    identifiers = [
        match.group(1)
        for match in re.finditer(
            r"\b([A-Za-z_][A-Za-z0-9_'?]*(?:\.[A-Za-z_][A-Za-z0-9_'?]*)+)",
            str(text or ""),
        )
    ]
    return list(dict.fromkeys(_lean_diagnostic_token(value) for value in identifiers))


def _normalized_semantic_review_decision(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in {
        "approved",
        "approve",
        "accepted",
        "faithful",
        "semantically_faithful",
        "approved_definition_candidate",
    }:
        return "approved_definition_candidate"
    if text in {
        "repair",
        "repair_required",
        "needs_repair",
        "revise",
        "revision_required",
        "not_faithful",
    }:
        return "repair_required"
    if text in {
        "blocked",
        "insufficient_context",
        "unknown",
        "uncertain",
        "blocked_or_insufficient_context",
    }:
        return "blocked_or_insufficient_context"
    return "not_reported"


def _semantic_review_status_from_decision(decision: str) -> str:
    if decision == "approved_definition_candidate":
        return "llm_semantic_review_approved_definition_candidate_not_proof"
    if decision == "repair_required":
        return "llm_semantic_review_repair_required_not_proof"
    if decision == "blocked_or_insufficient_context":
        return "llm_semantic_review_blocked_or_insufficient_context_not_proof"
    return "llm_semantic_review_not_reported"


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list | tuple):
        return [str(item) for item in value if str(item).strip()]
    if str(value or "").strip():
        return [str(value)]
    return []


def _normalize_candidate_packet(
    payload: Mapping[str, Any],
    *,
    task: Mapping[str, Any],
    prompt_packet: Mapping[str, Any],
    provider_name: str,
    backend_provider_name: str,
    model: str,
    model_tier: str,
    raw_response: str,
    response_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    placeholder = str(task.get("placeholder_symbol", "") or payload.get("placeholder_symbol", "") or "")
    body = dict(payload)
    llm_claimed_source_theorem_ready = bool(
        body.get("source_theorem_ready_for_exact_proof_body", False)
    )
    semantic_review_decision = _normalized_semantic_review_decision(
        body.get("semantic_review_decision", "")
        or body.get("semantic_review_status", "")
    )
    semantic_review_evidence = _string_list(
        body.get("semantic_review_evidence", [])
    )
    if not semantic_review_evidence:
        semantic_review_evidence = _string_list(
            body.get("semantic_alignment_notes", [])
        )
    body["placeholder_symbol"] = placeholder
    body["forbidden_shortcuts_absent"] = bool(
        body.get("forbidden_shortcuts_absent", False)
    )
    body["requires_local_lean_check"] = bool(body.get("requires_local_lean_check", True))
    body["local_definition_lean_checked"] = False
    body["local_definition_lean_compiled"] = False
    body["semantic_definition_kernel_verified"] = False
    body["source_theorem_kernel_verified"] = False
    body["semantic_review_decision"] = semantic_review_decision
    body["semantic_review_status"] = _semantic_review_status_from_decision(
        semantic_review_decision
    )
    body["semantic_review_evidence"] = semantic_review_evidence
    body["semantic_review_required_before_proof_body"] = True
    body["llm_claimed_source_theorem_ready_for_exact_proof_body"] = (
        llm_claimed_source_theorem_ready
    )
    body["source_theorem_ready_for_exact_proof_body"] = False
    body["semantic_definition_typecheck_evidence_status"] = (
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
    )
    body["proof_evidence_status"] = CANDIDATE_PROOF_EVIDENCE_STATUS
    body["proof_evidence_boundary"] = BOUNDARY
    candidate_definition_request = _candidate_definition_request_from_prompt(
        prompt_packet,
        task=task,
    )
    structured_context = _authoring_structured_context(
        task,
        candidate_definition_request=candidate_definition_request,
        extra_sources=(prompt_packet,),
    )
    packet_id = (
        "source_theorem_exact_semantic_definition_authoring_candidate:"
        + stable_hash(
            [
                prompt_packet.get("prompt_packet_id", ""),
                provider_name,
                backend_provider_name,
                model,
                body,
            ]
        )[:24]
    )
    return {
        "schema_version": 1,
        "artifact_kind": CANDIDATE_PACKET_ARTIFACT_KIND,
        "candidate_packet_id": packet_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_prompt_packet_id": str(prompt_packet.get("prompt_packet_id", "") or ""),
        "source_authoring_task_id": str(task.get("authoring_task_id", "") or ""),
        "source_execution_result_id": str(task.get("source_execution_result_id", "") or ""),
        "source_lean_repair_task_id": str(
            task.get("source_lean_repair_task_id", "") or ""
        ),
        "source_execution_status": str(task.get("source_execution_status", "") or ""),
        "authoring_trigger": str(task.get("authoring_trigger", "") or ""),
        "authoring_mode": str(task.get("authoring_mode", "") or ""),
        "lean_repair_action": str(task.get("lean_repair_action", "") or ""),
        "repair_strategy": str(task.get("repair_strategy", "") or ""),
        "question_id": str(task.get("question_id", "") or ""),
        "question_title": str(task.get("question_title", "") or ""),
        "target_theorem_name": str(task.get("target_theorem_name", "") or ""),
        "provider": provider_name,
        "backend_provider": backend_provider_name,
        "live_llm_generator": _is_live_external_llm_provider_pair(
            provider_name,
            backend_provider_name,
        ),
        "model": model,
        "model_tier": model_tier,
        "raw_response_fingerprint": stable_hash(raw_response),
        "response_metadata": _compact_response_metadata(response_metadata),
        **structured_context,
        "candidate_definition_request": candidate_definition_request,
        "candidate_repair_feedback": _candidate_repair_feedback(task),
        **body,
        "lean_authoring_environment_contract": dict(
            prompt_packet.get("lean_authoring_environment_contract", {}) or {}
        ),
        "definition_only_candidate_artifact_path": "",
        "candidate_artifact_path": "",
        "runtime_queue_status": "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZATION",
        "authoring_status": "LLM_EXACT_SEMANTIC_DEFINITION_CANDIDATE_PROPOSED",
        "ok": True,
        "validation_errors": [],
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _failed_candidate_packet(
    task: Mapping[str, Any],
    *,
    prompt_packet: Mapping[str, Any],
    provider_name: str,
    backend_provider_name: str,
    model: str,
    model_tier: str,
    error: Exception,
) -> dict[str, Any]:
    failure_classification = _authoring_failure_classification(error)
    validation_errors = (
        list(error.errors)
        if isinstance(error, PacketValidationError)
        else [f"{type(error).__name__}: {error}"]
    )
    repair_history = (
        list(error.history) if isinstance(error, PacketValidationError) else []
    )
    repair_attempts = (
        int(error.attempts) if isinstance(error, PacketValidationError) else 0
    )
    runtime_queue_status = (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
        if failure_classification
        in {"provider_connection_error", "provider_timeout_error"}
        else STRUCTURAL_REFORMULATION_QUEUE_STATUS
        if failure_classification == STRUCTURAL_REFORMULATION_FAILURE_CLASSIFICATION
        else "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
    )
    recommended_next_action = (
        "retry the same exact semantic-definition authoring prompt with the "
        "same provider or an approved fallback provider; no candidate was produced"
        if runtime_queue_status == "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
        else (
            "route to PF/BV-backed structural reformulation with Lean/RAG/source "
            "grounding before another exact semantic-definition authoring attempt"
        )
        if runtime_queue_status == STRUCTURAL_REFORMULATION_QUEUE_STATUS
        else "repair the failed authoring response contract before materialization"
    )
    packet_id = (
        "source_theorem_exact_semantic_definition_authoring_candidate_failed:"
        + stable_hash(
            [
                prompt_packet.get("prompt_packet_id", ""),
                provider_name,
                backend_provider_name,
                model,
                type(error).__name__,
                str(error),
            ]
        )[:24]
    )
    response_validation_feedback = _response_validation_feedback_from_errors(
        task,
        validation_errors=validation_errors,
        failure_classification=failure_classification,
        runtime_queue_status=runtime_queue_status,
        recommended_next_action=recommended_next_action,
        source_failed_candidate_packet_id=packet_id,
    )
    structural_reformulation_route = (
        _structural_reformulation_route_context(
            task,
            prompt_packet=prompt_packet,
            validation_errors=validation_errors,
            repair_history=repair_history,
            response_validation_feedback=response_validation_feedback,
        )
        if runtime_queue_status == STRUCTURAL_REFORMULATION_QUEUE_STATUS
        else {}
    )
    candidate_definition_request = _candidate_definition_request_from_prompt(
        prompt_packet,
        task=task,
    )
    structured_context = _authoring_structured_context(
        task,
        candidate_definition_request=candidate_definition_request,
        extra_sources=(prompt_packet,),
    )
    return {
        "schema_version": 1,
        "artifact_kind": CANDIDATE_PACKET_ARTIFACT_KIND,
        "candidate_packet_id": packet_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_prompt_packet_id": str(prompt_packet.get("prompt_packet_id", "") or ""),
        "source_authoring_task_id": str(task.get("authoring_task_id", "") or ""),
        "source_execution_result_id": str(task.get("source_execution_result_id", "") or ""),
        "source_lean_repair_task_id": str(
            task.get("source_lean_repair_task_id", "") or ""
        ),
        "source_execution_status": str(task.get("source_execution_status", "") or ""),
        "authoring_trigger": str(task.get("authoring_trigger", "") or ""),
        "authoring_mode": str(task.get("authoring_mode", "") or ""),
        "lean_repair_action": str(task.get("lean_repair_action", "") or ""),
        "repair_strategy": str(task.get("repair_strategy", "") or ""),
        "question_id": str(task.get("question_id", "") or ""),
        "question_title": str(task.get("question_title", "") or ""),
        "target_theorem_name": str(task.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(task.get("placeholder_symbol", "") or ""),
        "provider": provider_name,
        "backend_provider": backend_provider_name,
        "live_llm_generator": _is_live_external_llm_provider_pair(
            provider_name,
            backend_provider_name,
        ),
        "model": model,
        "model_tier": model_tier,
        **structured_context,
        "candidate_definition_request": candidate_definition_request,
        "candidate_repair_feedback": _candidate_repair_feedback(task),
        "definition_design": "",
        "lean_definition_candidate": "",
        "required_imports": [],
        "binder_usage": [],
        "semantic_alignment_notes": [],
        "known_gaps": [
            *(
                [
                    "local Lean feedback indicates API/syntax-level repair loop; "
                    "structural semantic reformulation is required before another "
                    "authoring pass"
                ]
                if structural_reformulation_route
                else []
            ),
            f"{type(error).__name__}: {error}",
        ],
        "forbidden_shortcuts_absent": False,
        "requires_local_lean_check": True,
        "definition_only_candidate_artifact_path": "",
        "candidate_artifact_path": "",
        "local_definition_lean_checked": False,
        "local_definition_lean_compiled": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "semantic_definition_typecheck_evidence_status": (
            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
        ),
        "runtime_queue_status": runtime_queue_status,
        "authoring_status": "LLM_EXACT_SEMANTIC_DEFINITION_AUTHORING_FAILED",
        "failure_classification": failure_classification,
        "recommended_next_action": recommended_next_action,
        "ok": False,
        "validation_errors": validation_errors,
        "retry_validation_errors": validation_errors,
        "response_validation_feedback": response_validation_feedback,
        "llm_json_repair_attempts": repair_attempts,
        "llm_json_repair_history": repair_history,
        "structural_reformulation_required": bool(structural_reformulation_route),
        "pseudo_formalization_required": bool(structural_reformulation_route),
        "requires_pseudo_formalization": bool(structural_reformulation_route),
        "source_theorem_exact_semantic_definition_structural_reformulation_route": (
            structural_reformulation_route
        ),
        "proof_evidence_status": CANDIDATE_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _candidate_definition_request_from_prompt(
    prompt_packet: Mapping[str, Any],
    *,
    task: Mapping[str, Any],
) -> dict[str, Any]:
    request = prompt_packet.get("candidate_definition_request", {})
    if isinstance(request, Mapping) and request:
        return dict(request)
    return dict(task.get("candidate_definition_request", {}) or {})


def _packet_validation_error_requires_structural_reformulation(
    error: PacketValidationError,
) -> bool:
    errors = [
        *_string_list(getattr(error, "errors", []) or []),
        *_validation_history_errors(getattr(error, "history", []) or []),
    ]
    return _validation_errors_require_structural_reformulation(errors)


def _validation_errors_require_structural_reformulation(
    errors: Sequence[str],
) -> bool:
    markers = (
        "reuses locally unresolved identifiers",
        "reuses prior local lean parse-error source fragments",
        "reuses identifiers from prior typeclass-failing source lines",
        "must_not_reuse_without_new_local_evidence",
    )
    return any(
        any(marker in str(error or "").lower() for marker in markers)
        for error in errors
    )


def _validation_history_errors(history: Sequence[Any]) -> list[str]:
    errors: list[str] = []
    for row in history or []:
        if not isinstance(row, Mapping):
            continue
        errors.extend(_string_list(row.get("errors", []) or []))
    return errors


def _structural_reformulation_route_context(
    task: Mapping[str, Any],
    *,
    prompt_packet: Mapping[str, Any],
    validation_errors: Sequence[str],
    repair_history: Sequence[Any],
    response_validation_feedback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = pseudo_formal_verification_method_contract()
    activation_policy = contract.get("runtime_activation_policy", {})
    calibration = contract.get("bv_calibration_contract", {})
    lean_contract = (
        prompt_packet.get("lean_authoring_environment_contract", {})
        if isinstance(prompt_packet.get("lean_authoring_environment_contract", {}), Mapping)
        else {}
    )
    lean_feedback = (
        lean_contract.get("local_lean_feedback", {})
        if isinstance(lean_contract.get("local_lean_feedback", {}), Mapping)
        else {}
    )
    hard_constraints = (
        lean_contract.get("hard_local_negative_constraints", {})
        if isinstance(lean_contract.get("hard_local_negative_constraints", {}), Mapping)
        else {}
    )
    target_lanes = [
        PSEUDO_FORMAL_TARGET_LANE_EXACT_SEMANTIC_DEFINITION,
        PSEUDO_FORMAL_TARGET_LANE_LEAN_RAG,
        PSEUDO_FORMAL_TARGET_LANE_SOURCE_TO_BRIDGE,
    ]
    response_validation_feedback = dict(response_validation_feedback or {})
    if not response_validation_feedback:
        response_validation_feedback = _response_validation_feedback_from_errors(
            task,
            validation_errors=validation_errors,
            failure_classification=STRUCTURAL_REFORMULATION_FAILURE_CLASSIFICATION,
            runtime_queue_status=STRUCTURAL_REFORMULATION_QUEUE_STATUS,
            recommended_next_action=(
                "route to PF/BV-backed structural reformulation with "
                "Lean/RAG/source grounding before another exact "
                "semantic-definition authoring attempt"
            ),
        )
    return {
        "schema_version": 1,
        "artifact_kind": "ExactSemanticDefinitionStructuralReformulationRoute",
        "failure_classification": STRUCTURAL_REFORMULATION_FAILURE_CLASSIFICATION,
        "runtime_queue_status": STRUCTURAL_REFORMULATION_QUEUE_STATUS,
        "route_reason": (
            "The candidate repair loop reused local Lean hard-negative API or "
            "syntax evidence. The next step must reformulate the semantic object "
            "using source-grounded blocks and project-verified primitives, rather "
            "than trying adjacent Lean APIs."
        ),
        "required_next_owner": "Formalizer/ProofEngineer/CodingAgent",
        "required_next_action": (
            "Run a PF/BV-backed structural decomposition of the exact semantic "
            "definition obligation, retrieve Lean/RAG/source-to-bridge grounding "
            "for each primitive, then author a smaller definition or declare the "
            "formal infrastructure gap explicitly."
        ),
        "pseudo_formalization_required": True,
        "pseudo_formal_pipeline_stage": PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
        "pseudo_formal_method_contract_id": str(contract.get("contract_id", "") or ""),
        "pseudo_formal_method_name": str(contract.get("method_name", "") or ""),
        "pseudo_formal_source_basis": dict(contract.get("source_basis", {}) or {}),
        "pseudo_formal_acceptance_boundary": str(
            calibration.get("acceptance_boundary", "") or ""
        ),
        "pseudo_formal_forbidden_outputs": list(
            activation_policy.get("forbidden_outputs", []) or []
        ),
        "target_lanes": target_lanes,
        "target_queue_status_by_lane": {
            lane: PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_STATUS_BY_TARGET_LANE.get(
                lane,
                "",
            )
            for lane in target_lanes
        },
        "candidate_definition_request": _candidate_definition_request_from_prompt(
            prompt_packet,
            task=task,
        ),
        "local_lean_feedback_summary": {
            "unknown_identifiers_from_all_checks": _string_list(
                lean_feedback.get("unknown_identifiers_from_all_checks", [])
            ),
            "typeclass_failures_from_all_checks": [
                dict(row)
                for row in lean_feedback.get("typeclass_failures_from_all_checks", [])
                or []
                if isinstance(row, Mapping)
            ],
            "parse_error_source_fragments_from_all_checks": _string_list(
                lean_feedback.get("parse_error_source_fragments_from_all_checks", [])
            ),
        },
        "hard_local_negative_constraints": dict(hard_constraints),
        "validation_errors": list(validation_errors),
        "response_validation_feedback": response_validation_feedback,
        "unverified_required_imports": _string_list(
            response_validation_feedback.get("unverified_required_imports", [])
        ),
        "llm_json_repair_history_errors": _validation_history_errors(repair_history),
        "proof_evidence_status": CANDIDATE_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "Structural reformulation routing is orchestration and semantic-audit "
            "context only. PF/BV outputs may prioritize and decompose work, but "
            "they do not establish semantic-definition kernel evidence or source "
            "theorem proof without later local Lean/AXLE replay."
        ),
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _authoring_failure_classification(error: Exception) -> str:
    if isinstance(error, PacketValidationError):
        if _packet_validation_error_requires_structural_reformulation(error):
            return STRUCTURAL_REFORMULATION_FAILURE_CLASSIFICATION
        return "authoring_candidate_validation_failed"
    name = type(error).__name__.lower()
    text = str(error).lower()
    if "timeout" in name or "timeout" in text or "timed out" in text:
        return "provider_timeout_error"
    if (
        "connection" in name
        or "connection error" in text
        or "network" in text
        or "dns" in text
        or "host resolution" in text
    ):
        return "provider_connection_error"
    return "authoring_candidate_generation_failed"


def _retry_authoring_task(
    task: Mapping[str, Any],
    *,
    prompt_packet: Mapping[str, Any],
    failed_candidate_packet: Mapping[str, Any],
) -> dict[str, Any]:
    retry_task_id = (
        "source_theorem_exact_semantic_definition_retry_authoring_task:"
        + stable_hash(
            [
                task.get("authoring_task_id", ""),
                prompt_packet.get("prompt_packet_id", ""),
                failed_candidate_packet.get("candidate_packet_id", ""),
                failed_candidate_packet.get("failure_classification", ""),
            ]
        )[:24]
    )
    retry_task = dict(task)
    retry_task["schema_version"] = 1
    retry_task["artifact_kind"] = "SourceTheoremExactSemanticDefinitionAuthoringTask"
    retry_task["authoring_task_id"] = retry_task_id
    retry_task["source_authoring_task_id"] = str(task.get("authoring_task_id", "") or "")
    retry_task["source_prompt_packet_id"] = str(
        prompt_packet.get("prompt_packet_id", "") or ""
    )
    retry_task["source_failed_candidate_packet_id"] = str(
        failed_candidate_packet.get("candidate_packet_id", "") or ""
    )
    retry_task["retry_of_authoring_failure"] = True
    retry_task["retry_failure_classification"] = str(
        failed_candidate_packet.get("failure_classification", "") or ""
    )
    retry_task["retry_validation_errors"] = list(
        failed_candidate_packet.get("validation_errors", []) or []
    )
    retry_task["response_validation_feedback"] = dict(
        failed_candidate_packet.get("response_validation_feedback", {}) or {}
    )
    retry_task["retry_recommended_next_action"] = str(
        failed_candidate_packet.get("recommended_next_action", "") or ""
    )
    retry_task["candidate_definition_request"] = _candidate_definition_request_from_prompt(
        prompt_packet,
        task=task,
    )
    structured_context = _authoring_structured_context(
        task,
        candidate_definition_request=retry_task["candidate_definition_request"],
        extra_sources=(prompt_packet, failed_candidate_packet),
    )
    for key, value in structured_context.items():
        if retry_task.get(key) in (None, "", [], {}) or key in {
            "source_theorem_binders",
            "source_anchor_context",
            "source_anchor_context_rows",
        }:
            retry_task[key] = value
    failed_queue_status = str(
        failed_candidate_packet.get("runtime_queue_status", "") or ""
    )
    if failed_queue_status not in AUTHORING_FOLLOWUP_QUEUE_STATUSES:
        failed_queue_status = "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
    repair_required = (
        failed_queue_status == "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
    )
    structural_reformulation_required = (
        failed_queue_status == STRUCTURAL_REFORMULATION_QUEUE_STATUS
    )
    retry_task["runtime_queue_status"] = failed_queue_status
    retry_task["authoring_trigger"] = (
        "EXACT_SEMANTIC_DEFINITION_STRUCTURAL_REFORMULATION_REQUIRED"
        if structural_reformulation_required
        else
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
        if repair_required
        else "EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY_REQUIRED"
    )
    retry_task["repair_of_authoring_candidate_validation_failure"] = repair_required
    retry_task["structural_reformulation_required"] = (
        structural_reformulation_required
    )
    retry_task["pseudo_formalization_required"] = structural_reformulation_required
    retry_task["requires_pseudo_formalization"] = structural_reformulation_required
    if structural_reformulation_required:
        route = failed_candidate_packet.get(
            "source_theorem_exact_semantic_definition_structural_reformulation_route",
            {},
        )
        retry_task[
            "source_theorem_exact_semantic_definition_structural_reformulation_route"
        ] = dict(route) if isinstance(route, Mapping) else {}
    retry_task["source_theorem_kernel_verified"] = False
    retry_task["semantic_definition_kernel_verified"] = False
    retry_task["proof_evidence_status"] = AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS
    return retry_task


def _learning_row_from_prompt_packet(
    packet: Mapping[str, Any],
    *,
    provider_requested: bool,
    external_export_blocked: bool = False,
) -> dict[str, Any]:
    prompt_packet_id = str(packet.get("prompt_packet_id", "") or "")
    source_authoring_task_id = str(packet.get("source_authoring_task_id", "") or "")
    pending_queue_status = (
        "BLOCKED_EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED"
        if external_export_blocked
        else
        "PENDING_LIVE_LLM_EXACT_SEMANTIC_DEFINITION_AUTHORING"
        if not provider_requested
        else "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RESPONSE"
    )
    if external_export_blocked:
        recommended_next_action = (
            "review and approve the external LLM export packet, or reroute this "
            "exact semantic-definition prompt to an approved local/live backend; "
            "any returned semantic-review decision remains non-proof evidence"
        )
    elif not provider_requested:
        recommended_next_action = (
            "run the exact semantic-definition authoring worker with an approved "
            "live/backend provider on this prompt packet; expected output is a "
            "candidate packet or semantic_review_decision, not proof-body readiness"
        )
    else:
        recommended_next_action = (
            "consume the exact semantic-definition authoring provider response and "
            "validate it into a candidate packet before materialization or local Lean"
        )
    return {
        "schema_version": 1,
        "artifact_kind": LEARNING_ARTIFACT_KIND,
        "learning_task": LEARNING_TASK,
        "work_order_id": prompt_packet_id or source_authoring_task_id,
        "question_id": str(packet.get("question_id", "") or ""),
        "question_title": str(packet.get("question_title", "") or ""),
        "target_theorem_name": str(packet.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(packet.get("placeholder_symbol", "") or ""),
        "source_execution_status": str(packet.get("source_execution_status", "") or ""),
        "authoring_trigger": str(packet.get("authoring_trigger", "") or ""),
        "authoring_mode": str(packet.get("authoring_mode", "") or ""),
        "lean_repair_action": str(packet.get("lean_repair_action", "") or ""),
        "repair_strategy": str(packet.get("repair_strategy", "") or ""),
        "source_definition_closure_work_order_id": str(
            packet.get("source_definition_closure_work_order_id", "") or ""
        ),
        "source_to_bridge_adapter_instantiation_group_id": str(
            packet.get("source_to_bridge_adapter_instantiation_group_id", "") or ""
        ),
        "source_to_bridge_grouped_premise_derivation_candidate_request_id": str(
            packet.get(
                "source_to_bridge_grouped_premise_derivation_candidate_request_id",
                "",
            )
            or ""
        ),
        "source_authoring_task_id": source_authoring_task_id,
        "source_prompt_packet_id": prompt_packet_id,
        "provider_requested": bool(provider_requested),
        "external_export_blocked": bool(external_export_blocked),
        "runtime_queue_status": pending_queue_status,
        **_exact_semantic_definition_context(packet),
        "candidate_definition_request": dict(
            packet.get("candidate_definition_request", {}) or {}
        ),
        "response_validation_feedback": dict(
            packet.get("response_validation_feedback", {}) or {}
        ),
        "retry_validation_errors": list(
            packet.get("retry_validation_errors", []) or []
        ),
        "semantic_alignment_blockers": list(
            packet.get("semantic_alignment_blockers", []) or []
        ),
        "semantic_review_required_before_proof_body": bool(
            packet.get("semantic_review_required_before_proof_body", True)
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "semantic_review_contract": dict(
            packet.get("semantic_review_contract", {}) or {}
        ),
        "input_summary": {
            "trigger": "EXACT_SEMANTIC_DEFINITION_AUTHORING_PROMPT_PACKET",
            "authoring_trigger": str(packet.get("authoring_trigger", "") or ""),
            "authoring_mode": str(packet.get("authoring_mode", "") or ""),
            "source_prompt_packet_id": prompt_packet_id,
            "source_authoring_task_id": source_authoring_task_id,
            "work_order_id": prompt_packet_id or source_authoring_task_id,
            "runtime_queue_status": pending_queue_status,
            "source_execution_status": str(
                packet.get("source_execution_status", "") or ""
            ),
            "semantic_review_required_before_proof_body": bool(
                packet.get("semantic_review_required_before_proof_body", True)
            ),
            "source_theorem_ready_for_exact_proof_body": False,
            "placeholder_symbol": str(packet.get("placeholder_symbol", "") or ""),
            "lean_repair_action": str(packet.get("lean_repair_action", "") or ""),
            "repair_strategy": str(packet.get("repair_strategy", "") or ""),
            "source_definition_closure_work_order_id": str(
                packet.get("source_definition_closure_work_order_id", "") or ""
            ),
            "source_to_bridge_adapter_instantiation_group_id": str(
                packet.get("source_to_bridge_adapter_instantiation_group_id", "")
                or ""
            ),
            "source_to_bridge_grouped_premise_derivation_candidate_request_id": str(
                packet.get(
                    "source_to_bridge_grouped_premise_derivation_candidate_request_id",
                    "",
                )
                or ""
            ),
            "source_to_bridge_adapter_object_names_requiring_source_instantiation": list(
                packet.get(
                    "source_to_bridge_adapter_object_names_requiring_source_instantiation",
                    [],
                )
                or []
            ),
            "provider_requested": bool(provider_requested),
            "external_export_blocked": bool(external_export_blocked),
            "source_theorem_kernel_verified": False,
            "semantic_definition_kernel_verified": False,
            "candidate_definition_request": dict(
                packet.get("candidate_definition_request", {}) or {}
            ),
            "response_validation_feedback": dict(
                packet.get("response_validation_feedback", {}) or {}
            ),
            "retry_validation_errors": list(
                packet.get("retry_validation_errors", []) or []
            ),
            "semantic_alignment_blockers": list(
                packet.get("semantic_alignment_blockers", []) or []
            ),
            **_exact_semantic_definition_context(packet),
        },
        "target_behavior": (
            "obtain an exact semantic-definition candidate from a generator-only "
            "ProofEngineer worker, then materialize and local-Lean check it"
        ),
        "recommended_next_action": recommended_next_action,
        "acceptance_gate": (
            "A validated authoring candidate packet or explicit semantic_review_decision "
            "is produced; any candidate must still be materialized and checked by "
            "local Lean/AXLE before proof-body search can resume."
        ),
        "proof_evidence_status": AUTHORING_WORKER_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _external_export_review_packet(
    prompt_packet: Mapping[str, Any],
    *,
    provider_name: str,
) -> dict[str, Any]:
    review_packet_id = (
        "source_theorem_exact_semantic_definition_external_llm_export_review:"
        + stable_hash(
            [
                prompt_packet.get("prompt_packet_id", ""),
                provider_name,
                prompt_packet.get("target_theorem_name", ""),
                prompt_packet.get("placeholder_symbol", ""),
            ]
        )[:24]
    )
    user_prompt = str(prompt_packet.get("user_prompt", "") or "")
    source_binders = [
        dict(row)
        for row in prompt_packet.get("exact_source_theorem_binders", []) or []
        if isinstance(row, Mapping)
    ]
    source_references = _source_reference_summary_from_user_prompt(user_prompt)
    export_mode = str(prompt_packet.get("external_export_mode", "") or "full")
    redaction_applied = bool(prompt_packet.get("export_redaction_applied", False))
    return {
        "schema_version": 1,
        "artifact_kind": EXTERNAL_EXPORT_REVIEW_PACKET_ARTIFACT_KIND,
        "external_export_review_packet_id": review_packet_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_prompt_packet_id": str(prompt_packet.get("prompt_packet_id", "") or ""),
        "source_authoring_task_id": str(
            prompt_packet.get("source_authoring_task_id", "") or ""
        ),
        "question_id": str(prompt_packet.get("question_id", "") or ""),
        "question_title": str(prompt_packet.get("question_title", "") or ""),
        "target_theorem_name": str(prompt_packet.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(prompt_packet.get("placeholder_symbol", "") or ""),
        "provider_name": str(provider_name or ""),
        "external_export_mode": export_mode,
        "export_redaction_applied": redaction_applied,
        "export_destination_kind": "external_llm_api",
        "export_block_reason": (
            "Prompt contains local proof/formalization task context. External "
            "Anthropic/OpenAI calls require explicit operator approval before "
            "sending this content outside the local workspace."
        ),
        "export_payload_fingerprint": stable_hash(
            {
                "system_prompt": prompt_packet.get("system_prompt", ""),
                "user_prompt": user_prompt,
                "response_schema": prompt_packet.get("response_schema", {}),
            }
        ),
        "export_payload_summary": {
            "user_prompt_chars": len(user_prompt),
            "source_theorem_binder_names": [
                str(row.get("name", "") or "") for row in source_binders
            ],
            "n_source_theorem_binders": len(source_binders),
            "n_source_reference_hints": len(source_references),
            "source_reference_paths": [
                str(row.get("path", "") or "") for row in source_references[:8]
            ],
            "source_reference_redaction_applied": redaction_applied,
            "source_reference_redaction_summary": _source_reference_redaction_from_user_prompt(
                user_prompt
            ),
            "contains_local_paths": any(
                str(row.get("path", "") or "").startswith("/")
                for row in source_references
            ),
            "contains_lean_source_snippets": any(
                bool(str(row.get("snippet", "") or ""))
                for row in source_references
            ),
            "contains_exact_goal_context": bool(
                prompt_packet.get("target_lean_declaration")
                or prompt_packet.get("exact_source_theorem_binders")
            ),
        },
        **_exact_semantic_definition_context_for_prompt(
            prompt_packet,
            export_mode=export_mode,
        ),
        "required_operator_action": (
            "Approve external export for this specific authoring task or rerun "
            "with a local/static provider. Approval affects LLM proposal "
            "generation only and does not create proof evidence."
        ),
        "runtime_queue_status": "BLOCKED_EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED",
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "proof_evidence_status": EXTERNAL_EXPORT_REVIEW_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "This export review packet is an operational approval artifact only. "
            "It is not LLM output, not local Lean evidence, and not theorem proof."
        ),
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _learning_row_from_external_export_review_packet(
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": LEARNING_ARTIFACT_KIND,
        "learning_task": EXTERNAL_EXPORT_REVIEW_LEARNING_TASK,
        "question_id": str(packet.get("question_id", "") or ""),
        "question_title": str(packet.get("question_title", "") or ""),
        "target_theorem_name": str(packet.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(packet.get("placeholder_symbol", "") or ""),
        "source_prompt_packet_id": str(packet.get("source_prompt_packet_id", "") or ""),
        "external_export_review_packet_id": str(
            packet.get("external_export_review_packet_id", "") or ""
        ),
        "runtime_queue_status": "BLOCKED_EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED",
        **_exact_semantic_definition_context(packet),
        "input_summary": {
            "trigger": "EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED",
            "provider_name": str(packet.get("provider_name", "") or ""),
            "export_payload_summary": dict(
                packet.get("export_payload_summary", {}) or {}
            ),
            **_exact_semantic_definition_context(packet),
            "source_theorem_kernel_verified": False,
            "semantic_definition_kernel_verified": False,
        },
        "target_behavior": (
            "obtain explicit operator approval before exporting local "
            "proof/formalization context to an external LLM provider"
        ),
        "proof_evidence_status": EXTERNAL_EXPORT_REVIEW_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": str(packet.get("proof_evidence_boundary", "") or ""),
    }


def _learning_row_from_candidate_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": LEARNING_ARTIFACT_KIND,
        "learning_task": LEARNING_TASK,
        "question_id": str(packet.get("question_id", "") or ""),
        "question_title": str(packet.get("question_title", "") or ""),
        "target_theorem_name": str(packet.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(packet.get("placeholder_symbol", "") or ""),
        "source_authoring_task_id": str(packet.get("source_authoring_task_id", "") or ""),
        "source_prompt_packet_id": str(packet.get("source_prompt_packet_id", "") or ""),
        "candidate_packet_id": str(packet.get("candidate_packet_id", "") or ""),
        "source_execution_status": str(packet.get("source_execution_status", "") or ""),
        "authoring_trigger": str(packet.get("authoring_trigger", "") or ""),
        "authoring_mode": str(packet.get("authoring_mode", "") or ""),
        "lean_repair_action": str(packet.get("lean_repair_action", "") or ""),
        "repair_strategy": str(packet.get("repair_strategy", "") or ""),
        "runtime_queue_status": str(packet.get("runtime_queue_status", "") or ""),
        "failure_classification": str(packet.get("failure_classification", "") or ""),
        "recommended_next_action": str(packet.get("recommended_next_action", "") or ""),
        "validation_errors": list(packet.get("validation_errors", []) or []),
        "retry_validation_errors": list(
            packet.get("retry_validation_errors", [])
            or packet.get("validation_errors", [])
            or []
        ),
        "response_validation_feedback": dict(
            packet.get("response_validation_feedback", {}) or {}
        ),
        "structural_reformulation_required": bool(
            packet.get("structural_reformulation_required", False)
        ),
        "pseudo_formalization_required": bool(
            packet.get("pseudo_formalization_required", False)
            or packet.get("requires_pseudo_formalization", False)
        ),
        "source_theorem_exact_semantic_definition_structural_reformulation_route": dict(
            packet.get(
                "source_theorem_exact_semantic_definition_structural_reformulation_route",
                {},
            )
            or {}
        ),
        **_exact_semantic_definition_context(packet),
        "candidate_definition_request": dict(
            packet.get("candidate_definition_request", {}) or {}
        ),
        "candidate_repair_feedback": dict(
            packet.get("candidate_repair_feedback", {}) or {}
        ),
        "input_summary": {
            "trigger": "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_PACKET",
            "authoring_status": str(packet.get("authoring_status", "") or ""),
            "authoring_mode": str(packet.get("authoring_mode", "") or ""),
            "source_execution_status": str(
                packet.get("source_execution_status", "") or ""
            ),
            "ok": bool(packet.get("ok", False)),
            "local_definition_lean_checked": False,
            "local_definition_lean_compiled": False,
            "semantic_definition_kernel_verified": False,
            "source_theorem_kernel_verified": False,
            "validation_errors": list(packet.get("validation_errors", []) or []),
            "retry_validation_errors": list(
                packet.get("retry_validation_errors", [])
                or packet.get("validation_errors", [])
                or []
            ),
            "response_validation_feedback": dict(
                packet.get("response_validation_feedback", {}) or {}
            ),
            "failure_classification": str(
                packet.get("failure_classification", "") or ""
            ),
            "recommended_next_action": str(
                packet.get("recommended_next_action", "") or ""
            ),
            "structural_reformulation_required": bool(
                packet.get("structural_reformulation_required", False)
            ),
            "pseudo_formalization_required": bool(
                packet.get("pseudo_formalization_required", False)
                or packet.get("requires_pseudo_formalization", False)
            ),
            **_exact_semantic_definition_context(packet),
        },
        "target_behavior": (
            "materialize the proposed Lean definition into a definition-only "
            "candidate file, then run local Lean and semantic review before "
            "proof-body search resumes"
        ),
        "proof_evidence_status": CANDIDATE_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _materialization_row(
    packet: Mapping[str, Any],
    *,
    candidate_artifacts_dir: Path,
    include_source_comments: bool,
    materialization_order_index: int,
) -> dict[str, Any]:
    placeholder = str(packet.get("placeholder_symbol", "") or "")
    candidate_packet_id = str(packet.get("candidate_packet_id", "") or "")
    lean_source = str(packet.get("lean_definition_candidate", "") or "")
    body_imports, lean_source_body = _split_leading_import_lines(lean_source)
    required_imports = _lean_import_modules(
        [
            *(packet.get("required_imports", []) or []),
            *body_imports,
        ]
    )
    validation_errors = validate_authoring_candidate_packet(packet)
    candidate_definition_request = dict(
        packet.get("candidate_definition_request", {}) or {}
    )
    missing_source_anchor_references = _missing_required_anchor_references(
        lean_source,
        candidate_definition_request.get("required_anchor_names", []) or [],
        candidate_definition_request.get("required_anchor_bindings", []) or [],
    )
    semantic_alignment_blockers = list(
        dict.fromkeys(
            [
                *[
                    str(value)
                    for value in packet.get("semantic_alignment_blockers", []) or []
                    if str(value).strip()
                ],
                *[
                    (
                        "definition-only candidate does not reference required "
                        f"source anchor `{name}` in Lean source"
                    )
                    for name in missing_source_anchor_references
                ],
            ]
        )
    )
    semantic_alignment_constraints = list(
        dict.fromkeys(
            [
                *[
                    str(value)
                    for value in packet.get("semantic_alignment_constraints", []) or []
                    if str(value).strip()
                ],
                *[
                    str(value)
                    for value in packet.get("semantic_alignment_notes", []) or []
                    if str(value).strip()
                ],
                *[
                    f"definition-only candidate should use source anchor `{name}`"
                    for name in (
                        candidate_definition_request.get("required_anchor_names", [])
                        or []
                    )
                    if str(name).strip()
                ],
            ]
        )
    )
    status = (
        "EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZATION_BLOCKED"
        if validation_errors or not bool(packet.get("ok", False))
        else "EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZED_PENDING_LOCAL_LEAN"
    )
    artifact_path = Path()
    if status == "EXACT_SEMANTIC_DEFINITION_CANDIDATE_MATERIALIZED_PENDING_LOCAL_LEAN":
        artifact_path = candidate_artifacts_dir / (
            _safe_file_stem(
                [
                    str(packet.get("target_theorem_name", "") or "target"),
                    placeholder or "placeholder",
                    candidate_packet_id,
                ]
            )
            + "_definition_only.lean"
        )
        artifact_path.write_text(
            _definition_only_candidate_text(
                packet,
                lean_source=lean_source_body,
                required_imports=required_imports,
                include_source_comments=include_source_comments,
            ),
            encoding="utf-8",
            )
    row_id = (
        "source_theorem_exact_semantic_definition_authoring_materialization:"
        + stable_hash(
            [
                candidate_packet_id,
                placeholder,
                str(artifact_path),
                status,
                validation_errors,
            ]
        )[:24]
    )
    artifact_path_text = str(artifact_path) if artifact_path != Path() else ""
    return {
        "schema_version": 1,
        "artifact_kind": MATERIALIZATION_ROW_ARTIFACT_KIND,
        "materialization_row_id": row_id,
        "source_candidate_packet_id": candidate_packet_id,
        "source_prompt_packet_id": str(packet.get("source_prompt_packet_id", "") or ""),
        "source_authoring_task_id": str(packet.get("source_authoring_task_id", "") or ""),
        "source_execution_result_id": str(packet.get("source_execution_result_id", "") or ""),
        "source_lean_repair_task_id": str(
            packet.get("source_lean_repair_task_id", "") or ""
        ),
        "source_execution_status": str(packet.get("source_execution_status", "") or ""),
        "authoring_trigger": str(packet.get("authoring_trigger", "") or ""),
        "authoring_mode": str(packet.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(packet.get("lean_repair_action", "") or ""),
        "source_repair_strategy": str(packet.get("repair_strategy", "") or ""),
        "question_id": str(packet.get("question_id", "") or ""),
        "question_title": str(packet.get("question_title", "") or ""),
        "target_theorem_name": str(packet.get("target_theorem_name", "") or ""),
        "placeholder_symbol": placeholder,
        "materialization_order_index": int(materialization_order_index),
        **_exact_semantic_definition_context(packet),
        "candidate_definition_request": candidate_definition_request,
        "source_to_bridge_adapter_instantiation_group_id": str(
            candidate_definition_request.get(
                "source_to_bridge_adapter_instantiation_group_id", ""
            )
            or packet.get("source_to_bridge_adapter_instantiation_group_id", "")
            or ""
        ),
        "required_adapter_object_names": list(
            candidate_definition_request.get("required_adapter_object_names", [])
            or []
        ),
        "available_adapter_object_names": list(
            candidate_definition_request.get("available_adapter_object_names", [])
            or []
        ),
        "missing_required_adapter_object_names": list(
            candidate_definition_request.get(
                "missing_required_adapter_object_names",
                [],
            )
            or []
        ),
        "definition_design": str(packet.get("definition_design", "") or ""),
        "required_imports": required_imports,
        "extracted_candidate_imports": body_imports,
        "binder_usage": list(packet.get("binder_usage", []) or []),
        "semantic_alignment_notes": list(
            packet.get("semantic_alignment_notes", []) or []
        ),
        "semantic_review_decision": str(
            packet.get("semantic_review_decision", "") or "not_reported"
        ),
        "semantic_review_status": str(
            packet.get("semantic_review_status", "") or "llm_semantic_review_not_reported"
        ),
        "semantic_review_evidence": list(
            packet.get("semantic_review_evidence", []) or []
        ),
        "semantic_review_required_before_proof_body": True,
        "llm_claimed_source_theorem_ready_for_exact_proof_body": bool(
            packet.get("llm_claimed_source_theorem_ready_for_exact_proof_body", False)
        ),
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "missing_required_anchor_references": missing_source_anchor_references,
        "known_gaps": list(packet.get("known_gaps", []) or []),
        "candidate_repair_feedback": dict(
            packet.get("candidate_repair_feedback", {}) or {}
        ),
        "definition_only_candidate_artifact_path": artifact_path_text,
        "candidate_artifact_path": "",
        "materialization_status": status,
        "validation_errors": validation_errors,
        "runtime_queue_status": (
            "PENDING_EXACT_SEMANTIC_DEFINITION_LOCAL_LEAN_CHECK"
            if not validation_errors and bool(artifact_path_text)
            else "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
        ),
        "local_definition_lean_checked": False,
        "local_definition_lean_compiled": False,
        "semantic_definition_typecheck_evidence_status": (
            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
        ),
        "semantic_definition_kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "proof_evidence_status": MATERIALIZER_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
        "ok": not validation_errors and bool(artifact_path_text),
    }


def _lean_repair_task_from_materialization_row(row: Mapping[str, Any]) -> dict[str, Any]:
    task_id = (
        "source_theorem_exact_semantic_definition_materialized_lean_repair_task:"
        + stable_hash(
            [
                row.get("materialization_row_id", ""),
                row.get("source_candidate_packet_id", ""),
                row.get("definition_only_candidate_artifact_path", ""),
            ]
        )[:24]
    )
    return {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": task_id,
        "source_materialization_row_id": str(row.get("materialization_row_id", "") or ""),
        "source_authoring_candidate_packet_id": str(
            row.get("source_candidate_packet_id", "") or ""
        ),
        "source_prompt_packet_id": str(row.get("source_prompt_packet_id", "") or ""),
        "source_authoring_task_id": str(row.get("source_authoring_task_id", "") or ""),
        "source_execution_result_id": str(row.get("source_execution_result_id", "") or ""),
        "source_lean_repair_task_id": str(
            row.get("source_lean_repair_task_id", "") or ""
        ),
        "source_execution_status": str(row.get("source_execution_status", "") or ""),
        "authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            row.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(row.get("source_repair_strategy", "") or ""),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "materialization_order_index": int(
            row.get("materialization_order_index", 0) or 0
        ),
        "lean_repair_action": "author_exact_definition",
        "repair_strategy": (
            "local_lean_check_materialized_exact_semantic_definition_candidate"
        ),
        "candidate_import_declarations": [],
        "source_reference_hints": [],
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_path": "",
        "candidate_repair_feedback": dict(
            row.get("candidate_repair_feedback", {}) or {}
        ),
        "runtime_queue_status": (
            "PENDING_EXACT_SEMANTIC_DEFINITION_MATERIALIZED_LOCAL_LEAN_CHECK"
        ),
        "local_definition_lean_checked": False,
        "local_definition_lean_compiled": False,
        "semantic_definition_typecheck_evidence_status": (
            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
        ),
        "definition_contract": {
            "source": "authoring_candidate_materializer",
            "definition_design": str(row.get("definition_design", "") or ""),
            "known_gaps": list(row.get("known_gaps", []) or []),
            "required_imports": list(row.get("required_imports", []) or []),
            "semantic_review_decision": str(
                row.get("semantic_review_decision", "") or "not_reported"
            ),
            "semantic_review_status": str(
                row.get("semantic_review_status", "")
                or "llm_semantic_review_not_reported"
            ),
            "semantic_review_evidence": list(
                row.get("semantic_review_evidence", []) or []
            ),
        },
        "semantic_review_decision": str(
            row.get("semantic_review_decision", "") or "not_reported"
        ),
        "semantic_review_status": str(
            row.get("semantic_review_status", "") or "llm_semantic_review_not_reported"
        ),
        "semantic_review_evidence": list(row.get("semantic_review_evidence", []) or []),
        "semantic_review_required_before_proof_body": True,
        "source_theorem_ready_for_exact_proof_body": False,
        "llm_claimed_source_theorem_ready_for_exact_proof_body": bool(
            row.get("llm_claimed_source_theorem_ready_for_exact_proof_body", False)
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "source_to_bridge_adapter_instantiation_group_id": str(
            row.get("source_to_bridge_adapter_instantiation_group_id", "") or ""
        ),
        "required_adapter_object_names": list(
            row.get("required_adapter_object_names", []) or []
        ),
        "available_adapter_object_names": list(
            row.get("available_adapter_object_names", []) or []
        ),
        "missing_required_adapter_object_names": list(
            row.get("missing_required_adapter_object_names", []) or []
        ),
        **_exact_semantic_definition_context(row),
        "candidate_definition_request": dict(
            row.get("candidate_definition_request", {}) or {}
        ),
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": (
            "This materialized Lean repair task asks local Lean to check a "
            "definition-only candidate. It is not source theorem proof."
        ),
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _missing_required_anchor_references(
    lean_source: str,
    required_anchor_names: Sequence[Any],
    required_anchor_bindings: Sequence[Any] = (),
) -> list[str]:
    source = str(lean_source or "")
    actual_names_by_required = _actual_anchor_names_by_required_anchor(
        required_anchor_bindings
    )
    missing: list[str] = []
    for raw_name in required_anchor_names:
        name = str(raw_name or "").strip()
        if not name:
            continue
        candidate_names = list(
            dict.fromkeys([name, *actual_names_by_required.get(name, [])])
        )
        if not any(
            _lean_source_mentions_identifier(source, candidate_name)
            for candidate_name in candidate_names
        ):
            missing.append(name)
    return missing


def _actual_anchor_names_by_required_anchor(
    required_anchor_bindings: Sequence[Any],
) -> dict[str, list[str]]:
    actual_by_required: dict[str, list[str]] = {}
    for raw_binding in required_anchor_bindings:
        if not isinstance(raw_binding, Mapping):
            continue
        required_name = str(
            raw_binding.get("required_anchor_name", "") or ""
        ).strip()
        actual_name = str(raw_binding.get("actual_anchor_name", "") or "").strip()
        binder = raw_binding.get("binder", {}) or {}
        binder_name = (
            str(binder.get("name", "") or "").strip()
            if isinstance(binder, Mapping)
            else ""
        )
        if not required_name:
            continue
        names = actual_by_required.setdefault(required_name, [])
        for name in (actual_name, binder_name):
            if name and name not in names:
                names.append(name)
    return actual_by_required


def _lean_source_mentions_identifier(lean_source: str, identifier: str) -> bool:
    escaped = re.escape(str(identifier or ""))
    if not escaped:
        return False
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9_'.]){escaped}(?![A-Za-z0-9_'.])",
            str(lean_source or ""),
        )
    )


def _lean_source_mentions_unresolved_identifier(
    lean_source: str,
    identifier: str,
) -> bool:
    raw_identifier = str(identifier or "").strip()
    if not raw_identifier:
        return False
    candidates = [raw_identifier]
    if "." in raw_identifier:
        short = raw_identifier.rsplit(".", 1)[-1]
        if short:
            candidates.append(short)
    for candidate in dict.fromkeys(candidates):
        escaped = re.escape(candidate)
        if not escaped:
            continue
        if re.search(
            rf"(?<![A-Za-z0-9_']){escaped}(?![A-Za-z0-9_'])",
            str(lean_source or ""),
        ):
            return True
    return False


def _learning_row_from_materialization_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": LEARNING_ARTIFACT_KIND,
        "learning_task": MATERIALIZER_LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "source_authoring_task_id": str(row.get("source_authoring_task_id", "") or ""),
        "source_candidate_packet_id": str(row.get("source_candidate_packet_id", "") or ""),
        "source_execution_status": str(row.get("source_execution_status", "") or ""),
        "authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            row.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(row.get("source_repair_strategy", "") or ""),
        "materialization_row_id": str(row.get("materialization_row_id", "") or ""),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "runtime_queue_status": str(row.get("runtime_queue_status", "") or ""),
        **_exact_semantic_definition_context(row),
        "candidate_definition_request": dict(
            row.get("candidate_definition_request", {}) or {}
        ),
        "candidate_repair_feedback": dict(
            row.get("candidate_repair_feedback", {}) or {}
        ),
        "semantic_review_decision": str(
            row.get("semantic_review_decision", "") or "not_reported"
        ),
        "semantic_review_status": str(
            row.get("semantic_review_status", "") or "llm_semantic_review_not_reported"
        ),
        "semantic_review_required_before_proof_body": True,
        "source_theorem_ready_for_exact_proof_body": False,
        "input_summary": {
            "trigger": "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_MATERIALIZED",
            "materialization_status": str(row.get("materialization_status", "") or ""),
            "authoring_mode": str(row.get("authoring_mode", "") or ""),
            "source_execution_status": str(
                row.get("source_execution_status", "") or ""
            ),
            "semantic_review_decision": str(
                row.get("semantic_review_decision", "") or "not_reported"
            ),
            "semantic_review_status": str(
                row.get("semantic_review_status", "")
                or "llm_semantic_review_not_reported"
            ),
            "semantic_review_required_before_proof_body": True,
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "local_definition_lean_checked": False,
            "local_definition_lean_compiled": False,
            "semantic_definition_kernel_verified": False,
            "source_theorem_kernel_verified": False,
            "source_theorem_ready_for_exact_proof_body": False,
            "validation_errors": list(row.get("validation_errors", []) or []),
            **_exact_semantic_definition_context(row),
        },
        "target_behavior": (
            "run the exact semantic-definition Lean repair executor with local "
            "Lean on the materialized definition-only candidate"
        ),
        "proof_evidence_status": MATERIALIZER_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _definition_only_candidate_text(
    packet: Mapping[str, Any],
    *,
    lean_source: str,
    required_imports: Sequence[Any] | None = None,
    include_source_comments: bool,
) -> str:
    imports = _lean_import_lines(
        required_imports
        if required_imports is not None
        else packet.get("required_imports", [])
        or []
    )
    header_lines = [
        "/-",
        "AI Statistician exact semantic-definition candidate.",
        "This file is generated from an LLM/ProofEngineer authoring packet.",
        "It is not proof evidence. Local Lean/AXLE must check it before use.",
        f"target_theorem_name: {packet.get('target_theorem_name', '')}",
        f"placeholder_symbol: {packet.get('placeholder_symbol', '')}",
        f"source_candidate_packet_id: {packet.get('candidate_packet_id', '')}",
        f"source_execution_status: {packet.get('source_execution_status', '')}",
        f"authoring_mode: {packet.get('authoring_mode', '')}",
        "-/",
    ]
    if include_source_comments:
        header_lines.extend(
            [
                "/-",
                "Definition design:",
                _comment_text(str(packet.get("definition_design", "") or "")),
                "Known gaps:",
                _comment_text(json.dumps(packet.get("known_gaps", []) or [], default=str)),
                "-/",
            ]
        )
    body = lean_source.strip()
    return "\n".join([*imports, "", *header_lines, "", body, ""])


def _split_leading_import_lines(lean_source: str) -> tuple[list[str], str]:
    imports: list[str] = []
    lines = str(lean_source or "").splitlines()
    body_start = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            body_start = index + 1
            continue
        if stripped.startswith("import "):
            module = stripped.removeprefix("import ").strip()
            if module:
                imports.append(module)
            body_start = index + 1
            continue
        break
    return _lean_import_modules(imports), "\n".join(lines[body_start:]).strip()


def _lean_import_modules(values: Sequence[Any]) -> list[str]:
    modules: list[str] = []
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        module = raw.removeprefix("import ").strip()
        if module and module not in modules:
            modules.append(module)
    return modules


def _lean_import_lines(values: Sequence[Any]) -> list[str]:
    imports: list[str] = []
    for module in _lean_import_modules(values):
        line = f"import {module}"
        if line not in imports:
            imports.append(line)
    return imports


def _comment_text(text: str) -> str:
    return str(text or "").replace("-/", "- /")


def _safe_file_stem(values: Sequence[str]) -> str:
    raw = "_".join(str(value or "") for value in values)
    compact = "".join(ch if ch.isalnum() else "_" for ch in raw)
    compact = "_".join(part for part in compact.split("_") if part)
    if not compact:
        compact = "candidate"
    return compact[:90] + "_" + stable_hash(raw)[:12]


def _compact_identifier(value: str) -> str:
    return compact_exact_semantic_placeholder_key(value)


def _extract_payload(text: str) -> dict[str, Any]:
    return extract_json_object(
        text,
        label="Exact semantic-definition authoring candidate",
    )


def _is_external_llm_provider(provider_name: str) -> bool:
    return (
        normalize_generator_provider_name(provider_name)
        in SUPPORTED_LIVE_GENERATOR_PROVIDERS
    )


def _is_live_external_llm_provider_pair(
    provider_name: str,
    backend_provider_name: str,
) -> bool:
    return is_live_generator_backend(provider_name, backend_provider_name)


def _load_external_export_approvals(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {
            "loaded": False,
            "approved_prompt_packet_ids": set(),
            "approved_review_packet_ids": set(),
            "approved_payload_fingerprints": set(),
            "approved_rows": [],
        }
    if path.suffix.lower() == ".jsonl":
        rows = _read_jsonl(path)
        payload: Mapping[str, Any] = {"approval_rows": rows}
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            payload = {}
    rows = [
        dict(row)
        for row in payload.get("approval_rows", []) or []
        if isinstance(row, Mapping)
    ]
    rows.append(dict(payload))
    approved_rows = [
        row
        for row in rows
        if row.get("approved", True) is not False
    ]
    return {
        "loaded": True,
        "path": str(path),
        "approved_prompt_packet_ids": _approval_values(
            approved_rows,
            "source_prompt_packet_id",
            "prompt_packet_id",
            "approved_prompt_packet_ids",
        ),
        "approved_review_packet_ids": _approval_values(
            approved_rows,
            "external_export_review_packet_id",
            "approved_external_export_review_packet_ids",
        ),
        "approved_payload_fingerprints": _approval_values(
            approved_rows,
            "export_payload_fingerprint",
            "approved_export_payload_fingerprints",
        ),
        "approved_rows": approved_rows,
    }


def _approval_values(
    rows: Sequence[Mapping[str, Any]],
    *keys: str,
) -> set[str]:
    values: set[str] = set()
    for row in rows:
        for key in keys:
            value = row.get(key)
            if isinstance(value, list | tuple | set):
                values.update(str(item) for item in value if str(item).strip())
            elif value not in (None, "", [], {}):
                values.add(str(value))
    return values


def _external_export_packet_approved(
    packet: Mapping[str, Any],
    *,
    approvals: Mapping[str, Any],
    provider_name: str,
    export_mode: str,
) -> bool:
    if not approvals.get("loaded"):
        return False
    provider = normalize_generator_provider_name(provider_name)
    mode = _normalized_external_export_mode(export_mode)
    for row in approvals.get("approved_rows", []) or []:
        if not isinstance(row, Mapping):
            continue
        row_provider = normalize_generator_provider_name(
            row.get("provider_name", "")
        )
        if row_provider and row_provider != provider:
            continue
        row_mode = str(row.get("external_export_mode", "") or "").strip().lower()
        if row_mode and row_mode != mode:
            continue
        if str(packet.get("source_prompt_packet_id", "") or "") in _approval_values(
            [row],
            "source_prompt_packet_id",
            "prompt_packet_id",
            "approved_prompt_packet_ids",
        ):
            return True
        if str(packet.get("external_export_review_packet_id", "") or "") in _approval_values(
            [row],
            "external_export_review_packet_id",
            "approved_external_export_review_packet_ids",
        ):
            return True
        if str(packet.get("export_payload_fingerprint", "") or "") in _approval_values(
            [row],
            "export_payload_fingerprint",
            "approved_export_payload_fingerprints",
        ):
            return True
    return False


def _normalized_external_export_mode(value: str) -> str:
    mode = str(value or "full").strip().lower()
    return mode if mode in {"full", "redacted"} else "full"


def _source_reference_hints_for_prompt(
    task: Mapping[str, Any],
    *,
    export_mode: str,
) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in task.get("source_reference_hints", []) or []
        if isinstance(row, Mapping)
    ][:8]
    if _normalized_external_export_mode(export_mode) != "redacted":
        return rows
    redacted: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        redacted.append(
            {
                "reference_index": index,
                "candidate_kind": str(row.get("candidate_kind", "") or ""),
                "line_present": bool(row.get("line", "") not in (None, "")),
                "path_redacted": bool(row.get("path")),
                "snippet_redacted": bool(row.get("snippet")),
                "snippet_chars": len(str(row.get("snippet", "") or "")),
            }
        )
    return redacted


def _source_reference_redaction_summary(
    task: Mapping[str, Any],
    *,
    source_reference_hints: Sequence[Mapping[str, Any]],
    export_mode: str,
) -> dict[str, Any]:
    original_rows = [
        row
        for row in task.get("source_reference_hints", []) or []
        if isinstance(row, Mapping)
    ][:8]
    redacted = _normalized_external_export_mode(export_mode) == "redacted"
    return {
        "export_mode": _normalized_external_export_mode(export_mode),
        "redaction_applied": redacted,
        "original_reference_count": len(original_rows),
        "exported_reference_count": len(source_reference_hints),
        "paths_redacted": sum(1 for row in original_rows if row.get("path")) if redacted else 0,
        "snippets_redacted": sum(1 for row in original_rows if row.get("snippet")) if redacted else 0,
    }


PROMPT_EXACT_SEMANTIC_CONTEXT_KEYS = (
    "semantic_primitive",
    "semantic_primitive_requirements",
    "source_block_semantic_primitive_requirements",
    "source_anchors",
    "source_block_conclusion",
    "source_block_premises",
    "source_block_proof_text",
    "dependency_statement_context",
    "inherited_scope",
    "dependency_ids",
    "scope_parent_id",
    "dependency_scope",
    "block_depth",
    "source_pseudo_formal_work_order_id",
    "source_pseudo_formal_block_id",
    "source_pseudo_formal_packet_id",
    "source_formalizer_proposal_id",
    "pseudo_formal_method_contract_id",
    "pseudo_formal_pipeline_stage",
    "pseudo_formal_proof_evidence_status",
)


def _exact_semantic_definition_context_for_prompt(
    task: Mapping[str, Any],
    *,
    export_mode: str,
) -> dict[str, Any]:
    context = _exact_semantic_definition_context(task)
    prompt_context: dict[str, Any] = {}
    for key in PROMPT_EXACT_SEMANTIC_CONTEXT_KEYS:
        value = context.get(key, None)
        if value in (None, "", [], {}):
            continue
        if key == "source_anchors":
            anchors = _source_anchors_for_prompt(value, export_mode=export_mode)
            if anchors:
                prompt_context[key] = anchors
            continue
        if isinstance(value, Mapping):
            prompt_context[key] = dict(value)
        elif isinstance(value, list):
            prompt_context[key] = list(value)
        else:
            prompt_context[key] = value
    if prompt_context:
        prompt_context["proof_evidence_boundary"] = (
            "This context identifies the exact semantic object/source anchors to "
            "author. It is routing and grounding context only, not proof evidence."
        )
    return prompt_context


def _source_anchors_for_prompt(
    value: Any,
    *,
    export_mode: str,
) -> list[dict[str, Any]]:
    rows = [dict(row) for row in value or [] if isinstance(row, Mapping)][:8]
    if _normalized_external_export_mode(export_mode) != "redacted":
        return rows
    redacted: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        redacted.append(
            {
                "anchor_index": index,
                "kind": str(row.get("kind", "") or ""),
                "id": str(row.get("id", "") or ""),
                "excerpt_redacted": bool(row.get("excerpt")),
                "excerpt_chars": len(str(row.get("excerpt", "") or "")),
            }
        )
    return redacted


def _source_reference_summary_from_user_prompt(user_prompt: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(user_prompt)
    except json.JSONDecodeError:
        return []
    references = payload.get("source_reference_hints", [])
    if not isinstance(references, list):
        return []
    return [dict(row) for row in references if isinstance(row, Mapping)]


def _source_reference_redaction_from_user_prompt(user_prompt: str) -> dict[str, Any]:
    try:
        payload = json.loads(user_prompt)
    except json.JSONDecodeError:
        return {}
    summary = payload.get("source_reference_redaction_summary", {})
    return dict(summary) if isinstance(summary, Mapping) else {}


def _contains_forbidden_proof_claim(value: Any) -> str:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in {
                "kernel_verified",
                "source_theorem_kernel_verified",
                "semantic_definition_kernel_verified",
                "full_frontier_theorem_proved",
                "source_theorem_proved",
            } and child is True:
                return str(key)
            nested = _contains_forbidden_proof_claim(child)
            if nested:
                return f"{key}.{nested}"
        return ""
    if isinstance(value, list | tuple):
        for index, child in enumerate(value):
            nested = _contains_forbidden_proof_claim(child)
            if nested:
                return f"{index}.{nested}"
        return ""
    if isinstance(value, str):
        lowered = value.lower()
        for phrase in (
            "kernel verified",
            "source theorem proved",
            "theorem proved",
            "lean proved",
            "local lean checked",
            "local lean compiled",
        ):
            if phrase in lowered:
                return phrase
    return ""


def _exact_semantic_definition_context(row: Mapping[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for key in EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS:
        value = row.get(key, None)
        if value in (None, "", [], {}):
            input_summary = row.get("input_summary", {})
            if isinstance(input_summary, Mapping):
                value = input_summary.get(key, None)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, Mapping):
            context[key] = dict(value)
        elif isinstance(value, list):
            context[key] = list(value)
        else:
            context[key] = value
    candidate_request = context.get("candidate_definition_request", {})
    if isinstance(candidate_request, Mapping):
        target_theorem_name = str(row.get("target_theorem_name", "") or "")
        placeholder_symbol = str(row.get("placeholder_symbol", "") or "")
        target_ids = _target_ids_from_row(row, fallback_target=target_theorem_name)
        normalized_request = dict(candidate_request)
        if target_theorem_name:
            normalized_request.setdefault("target_theorem_name", target_theorem_name)
        if placeholder_symbol and not normalized_request.get("placeholder_symbol"):
            normalized_request["placeholder_symbol"] = placeholder_symbol
        if target_ids and not normalized_request.get("target_ids"):
            normalized_request["target_ids"] = target_ids
        context["candidate_definition_request"] = normalized_request
    return context


def _target_ids_from_row(
    row: Mapping[str, Any],
    *,
    fallback_target: str = "",
) -> list[str]:
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    raw_values = (
        row.get("target_ids", [])
        or row.get("target_id", "")
        or row.get("target_theorem_goal_ids", [])
        or input_summary.get("target_ids", [])
        or input_summary.get("target_id", "")
        or input_summary.get("target_theorem_goal_ids", [])
        or []
    )
    if isinstance(raw_values, Mapping):
        values = [str(key).strip() for key in raw_values.keys()]
    elif isinstance(raw_values, str):
        values = [raw_values.strip()]
    elif isinstance(raw_values, Sequence):
        values = [str(value).strip() for value in raw_values]
    else:
        values = [str(raw_values).strip()]
    target_ids = [value for value in values if value]
    fallback = str(fallback_target or "").strip()
    if not target_ids and fallback:
        target_ids = [fallback]
    return list(dict.fromkeys(target_ids))


def _compact_response_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    keep = (
        "generator_only",
        "tools_available",
        "schema_supplied",
        "json_prompt_hint_used",
        "timeout_seconds",
        "retry_count",
        "requested_model",
        "provider_reported_model",
        "provider_usage",
        "request_model_tier",
        "provider_reported_model_tier",
    )
    compact: dict[str, Any] = {}
    for key in keep:
        value = metadata.get(key)
        if value not in (None, "", [], {}):
            compact[key] = value
    return compact


def _resolve_relative_artifact_path(*, base_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidate = base_dir / path
    if candidate.exists():
        return candidate
    if path.parts and path.parts[0] == base_dir.name:
        candidate = base_dir.parent / path
        if candidate.exists():
            return candidate
    return base_dir / path


def _resolve_runtime_artifact_path(*, runtime_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidates = [runtime_dir / path, runtime_dir.parent / path]
    parts = path.parts
    if parts and parts[0] == runtime_dir.name:
        candidates.append(runtime_dir.parent / path)
    if len(parts) >= 2 and parts[0] == runtime_dir.parent.name:
        candidates.append(runtime_dir.parent.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )


AUTHORING_RESPONSE_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "placeholder_symbol",
        "definition_design",
        "lean_definition_candidate",
        "required_imports",
        "binder_usage",
        "semantic_alignment_notes",
        "known_gaps",
        "forbidden_shortcuts_absent",
        "requires_local_lean_check",
    ],
    "properties": {
        "placeholder_symbol": {"type": "string"},
        "definition_design": {"type": "string"},
        "lean_definition_candidate": {"type": "string"},
        "required_imports": {"type": "array"},
        "binder_usage": {"type": "array"},
        "semantic_alignment_notes": {"type": "array"},
        "known_gaps": {"type": "array"},
        "semantic_review_decision": {"type": "string"},
        "semantic_review_evidence": {"type": "array"},
        "semantic_review_required_before_proof_body": {"type": "boolean"},
        "source_theorem_ready_for_exact_proof_body": {"type": "boolean"},
        "forbidden_shortcuts_absent": {"type": "boolean"},
        "requires_local_lean_check": {"type": "boolean"},
    },
}

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .llm_json_repair import extract_json_object, generate_validated_json_packet
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_architect import KERNEL_PROOF_BOUNDARY
from .source_theorem_exact_semantic_definition_lean_repair_executor import (
    AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
)
from .source_theorem_exact_semantic_definition_source_lookup import (
    EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS,
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
SYSTEM_PROMPT = (
    "You are the AI Statistician Formalizer/ProofEngineer authoring worker. "
    "Your task is to propose exact Lean semantic definitions from the given "
    "source-theorem binders, semantic anchors, local Lean constraints, and "
    "source references. Prefer small definition-only Lean that can be checked in "
    "the configured Lake project: use minimal imports, make every free variable "
    "an explicit binder, and report uncertain imports as known gaps rather than "
    "depending on broad unavailable modules. You are a generator only: do not "
    "claim tool execution, file writes, local Lean checking, theorem proof, or "
    "kernel verification. Return only one valid JSON object satisfying the "
    "requested schema."
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
    should_call_provider = provider is not None and not config.dry_run
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
        if row.get("runtime_queue_status")
        == "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
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
        "provider_name": str(config.provider_name or "none"),
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
        "n_candidate_definition_requests_autofilled": sum(
            1
            for row in prompt_packets
            if row.get("candidate_definition_request_autofilled")
        ),
        "n_external_llm_export_review_packets": len(external_export_review_packets),
        "n_external_export_approved_tasks": len(approved_prompt_ids),
        "n_external_export_blocked_tasks": len(blocked_prompt_ids),
        "n_llm_attempted": len(attempted_prompt_ids),
        "n_candidate_packets": len(candidate_packets),
        "n_candidate_packets_ok": sum(1 for row in candidate_packets if row.get("ok")),
        "n_candidate_packets_failed": sum(
            1 for row in candidate_packets if not row.get("ok")
        ),
        "n_retryable_authoring_tasks": len(retryable_authoring_tasks),
        "n_retryable_provider_failures": sum(
            1
            for row in candidate_packets
            if row.get("failure_classification")
            in {"provider_connection_error", "provider_timeout_error"}
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
    return _compact_identifier(str(value or ""))


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
    request = (
        _candidate_definition_request_from_task(task)
        if request_autofilled
        else raw_request
    )
    export_mode = _normalized_external_export_mode(export_mode)
    prompt_payload = _prompt_payload(
        task,
        candidate_definition_request=request,
        export_mode=export_mode,
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
        "candidate_repair_feedback": _candidate_repair_feedback(task),
        **_exact_semantic_definition_context(task),
        "candidate_definition_request": request,
        "candidate_definition_request_autofilled": request_autofilled,
        "external_export_mode": export_mode,
        "export_redaction_applied": export_mode == "redacted",
        "system_prompt": SYSTEM_PROMPT,
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
        "candidate_definition_request": dict(candidate_definition_request),
        "source_theorem_binders": list(
            task.get("exact_source_theorem_binders", []) or []
        ),
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
        "candidate_repair_feedback": _candidate_repair_feedback(task),
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
                "remaining semantic/typeclass gaps before local Lean checking"
            ],
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


def _candidate_repair_feedback(task: Mapping[str, Any]) -> dict[str, Any]:
    return {
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
        "local_lean_diagnostics": list(
            task.get("local_lean_diagnostics", []) or []
        )[:12],
        "failure_classification": str(task.get("failure_classification", "") or ""),
        "recommended_next_action": str(
            task.get("recommended_next_action", "") or ""
        ),
    }


def _lean_authoring_environment_contract(
    task: Mapping[str, Any],
    *,
    candidate_definition_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return local Lean constraints that keep generated definitions checkable."""

    source_binders = list(task.get("exact_source_theorem_binders", []) or [])
    required_anchor_names = [
        str(value).strip()
        for value in candidate_definition_request.get("required_anchor_names", [])
        or []
        if str(value).strip()
    ]
    return {
        "candidate_scope": "definition_or_abbrev_only",
        "source_theorem_binder_count": len(source_binders),
        "required_anchor_names": required_anchor_names,
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
    }


def _candidate_definition_request_from_task(task: Mapping[str, Any]) -> dict[str, Any]:
    placeholder_symbol = str(task.get("placeholder_symbol", "") or "")
    required_anchor_names = _required_anchor_names_for_placeholder(placeholder_symbol)
    available_binders_by_name = _available_semantic_binders_by_name(task)
    available_anchor_names = list(available_binders_by_name)
    required_binders = [
        dict(available_binders_by_name[name])
        for name in required_anchor_names
        if name in available_binders_by_name
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
        "semantic_goal": _semantic_goal_for_placeholder(placeholder_symbol),
        "required_anchor_names": required_anchor_names,
        "available_anchor_names": available_anchor_names,
        "missing_required_anchor_names": [
            name for name in required_anchor_names if name not in available_anchor_names
        ],
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
    normalized = _adapter_object_key(placeholder_symbol)
    if normalized == "covered":
        return (
            "Define the source coverage event/object from the exact source theorem "
            "coverage binder hC and threshold q_hat, matching the held-out score "
            "event {ω | s (Fin.last n2) ω ≤ q_hat ω}."
        )
    if normalized == "rank":
        return (
            "Define the rank object from the exact score process s and the "
            "order-statistic threshold equation hq; it must support good-rank "
            "containment and bad-rank probability premises."
        )
    if normalized == "badranks":
        return (
            "Define the finite bad-rank set from n2, alpha, halpha, and hq so it "
            "matches the ranks that violate conformal coverage containment."
        )
    if normalized in {"α", "alpha"}:
        return (
            "Define the rank-indexed probability budget α from the exact source "
            "miscoverage level alpha and rank-uniformity/exchangeability anchor hexch."
        )
    if normalized in {"αtotal", "alphatotal"}:
        return (
            "Define the total bad-rank budget α_total from alpha and BadRanks, "
            "with the intended downstream finite-sum bound."
        )
    return (
        "Define the exact semantic replacement for the placeholder from the "
        "listed source theorem binders and semantic constraints."
    )


def _required_anchor_names_for_placeholder(placeholder_symbol: str) -> list[str]:
    normalized = _adapter_object_key(placeholder_symbol)
    if normalized == "covered":
        return ["s", "q_hat", "C", "hC"]
    if normalized == "rank":
        return ["n2", "s", "q_hat", "hq"]
    if normalized == "badranks":
        return ["n2", "alpha", "halpha", "s", "q_hat", "hq"]
    if normalized in {"α", "alpha"}:
        return ["P", "n2", "alpha", "s", "hexch"]
    if normalized in {"αtotal", "alphatotal"}:
        return ["n2", "alpha", "halpha"]
    return []


def _available_semantic_binders_by_name(
    task: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    binders_by_name: dict[str, Mapping[str, Any]] = {}
    for binder in task.get("premise_semantic_anchor_binders", []) or []:
        if not isinstance(binder, Mapping):
            continue
        name = str(binder.get("name", "") or "")
        if name:
            binders_by_name[name] = binder
    for binder in task.get("exact_source_theorem_binders", []) or []:
        if not isinstance(binder, Mapping):
            continue
        name = str(binder.get("name", "") or "")
        if name:
            binders_by_name[name] = binder
    return binders_by_name


def _required_adapter_object_names_for_placeholder(
    placeholder_symbol: str,
) -> list[str]:
    normalized = _adapter_object_key(placeholder_symbol)
    if normalized == "badranks":
        return ["rank"]
    if normalized in {"αtotal", "alphatotal"}:
        return ["BadRanks"]
    return []


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
    forbidden_claim = _contains_forbidden_proof_claim(packet)
    if forbidden_claim:
        errors.append(f"packet contains forbidden proof claim: {forbidden_claim}")
    return sorted(set(errors))


def _normalize_candidate_packet(
    payload: Mapping[str, Any],
    *,
    task: Mapping[str, Any],
    prompt_packet: Mapping[str, Any],
    provider_name: str,
    model: str,
    model_tier: str,
    raw_response: str,
    response_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    placeholder = str(task.get("placeholder_symbol", "") or payload.get("placeholder_symbol", "") or "")
    body = dict(payload)
    body["placeholder_symbol"] = placeholder
    body["forbidden_shortcuts_absent"] = bool(
        body.get("forbidden_shortcuts_absent", False)
    )
    body["requires_local_lean_check"] = bool(body.get("requires_local_lean_check", True))
    body["local_definition_lean_checked"] = False
    body["local_definition_lean_compiled"] = False
    body["semantic_definition_kernel_verified"] = False
    body["source_theorem_kernel_verified"] = False
    body["source_theorem_ready_for_exact_proof_body"] = False
    body["semantic_definition_typecheck_evidence_status"] = (
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
    )
    body["proof_evidence_status"] = CANDIDATE_PROOF_EVIDENCE_STATUS
    body["proof_evidence_boundary"] = BOUNDARY
    packet_id = (
        "source_theorem_exact_semantic_definition_authoring_candidate:"
        + stable_hash(
            [
                prompt_packet.get("prompt_packet_id", ""),
                provider_name,
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
        "question_id": str(task.get("question_id", "") or ""),
        "question_title": str(task.get("question_title", "") or ""),
        "target_theorem_name": str(task.get("target_theorem_name", "") or ""),
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "raw_response_fingerprint": stable_hash(raw_response),
        "response_metadata": _compact_response_metadata(response_metadata),
        **_exact_semantic_definition_context(task),
        "candidate_definition_request": _candidate_definition_request_from_prompt(
            prompt_packet,
            task=task,
        ),
        **body,
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
    model: str,
    model_tier: str,
    error: Exception,
) -> dict[str, Any]:
    failure_classification = _authoring_failure_classification(error)
    runtime_queue_status = (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
        if failure_classification
        in {"provider_connection_error", "provider_timeout_error"}
        else "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
    )
    recommended_next_action = (
        "retry the same exact semantic-definition authoring prompt with the "
        "same provider or an approved fallback provider; no candidate was produced"
        if runtime_queue_status == "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
        else "repair the failed authoring response contract before materialization"
    )
    packet_id = (
        "source_theorem_exact_semantic_definition_authoring_candidate_failed:"
        + stable_hash(
            [
                prompt_packet.get("prompt_packet_id", ""),
                provider_name,
                model,
                type(error).__name__,
                str(error),
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
        "question_id": str(task.get("question_id", "") or ""),
        "question_title": str(task.get("question_title", "") or ""),
        "target_theorem_name": str(task.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(task.get("placeholder_symbol", "") or ""),
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        **_exact_semantic_definition_context(task),
        "candidate_definition_request": _candidate_definition_request_from_prompt(
            prompt_packet,
            task=task,
        ),
        "definition_design": "",
        "lean_definition_candidate": "",
        "required_imports": [],
        "binder_usage": [],
        "semantic_alignment_notes": [],
        "known_gaps": [f"{type(error).__name__}: {error}"],
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
        "validation_errors": [f"{type(error).__name__}: {error}"],
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


def _authoring_failure_classification(error: Exception) -> str:
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
    retry_task["retry_recommended_next_action"] = str(
        failed_candidate_packet.get("recommended_next_action", "") or ""
    )
    retry_task["candidate_definition_request"] = _candidate_definition_request_from_prompt(
        prompt_packet,
        task=task,
    )
    retry_task["runtime_queue_status"] = (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RETRY"
    )
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
    return {
        "schema_version": 1,
        "artifact_kind": LEARNING_ARTIFACT_KIND,
        "learning_task": LEARNING_TASK,
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
        "source_authoring_task_id": str(packet.get("source_authoring_task_id", "") or ""),
        "source_prompt_packet_id": str(packet.get("prompt_packet_id", "") or ""),
        "runtime_queue_status": (
            "BLOCKED_EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED"
            if external_export_blocked
            else
            "PENDING_LIVE_LLM_EXACT_SEMANTIC_DEFINITION_AUTHORING"
            if not provider_requested
            else "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_RESPONSE"
        ),
        **_exact_semantic_definition_context(packet),
        "candidate_definition_request": dict(
            packet.get("candidate_definition_request", {}) or {}
        ),
        "semantic_alignment_blockers": list(
            packet.get("semantic_alignment_blockers", []) or []
        ),
        "input_summary": {
            "trigger": "EXACT_SEMANTIC_DEFINITION_AUTHORING_PROMPT_PACKET",
            "authoring_trigger": str(packet.get("authoring_trigger", "") or ""),
            "authoring_mode": str(packet.get("authoring_mode", "") or ""),
            "source_execution_status": str(
                packet.get("source_execution_status", "") or ""
            ),
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
            "semantic_alignment_blockers": list(
                packet.get("semantic_alignment_blockers", []) or []
            ),
        },
        "target_behavior": (
            "obtain an exact semantic-definition candidate from a generator-only "
            "ProofEngineer worker, then materialize and local-Lean check it"
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
        "input_summary": {
            "trigger": "EXTERNAL_LLM_EXPORT_REVIEW_REQUIRED",
            "provider_name": str(packet.get("provider_name", "") or ""),
            "export_payload_summary": dict(
                packet.get("export_payload_summary", {}) or {}
            ),
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
        "runtime_queue_status": str(packet.get("runtime_queue_status", "") or ""),
        "failure_classification": str(packet.get("failure_classification", "") or ""),
        "recommended_next_action": str(packet.get("recommended_next_action", "") or ""),
        **_exact_semantic_definition_context(packet),
        "candidate_definition_request": dict(
            packet.get("candidate_definition_request", {}) or {}
        ),
        "input_summary": {
            "trigger": "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_PACKET",
            "authoring_status": str(packet.get("authoring_status", "") or ""),
            "ok": bool(packet.get("ok", False)),
            "local_definition_lean_checked": False,
            "local_definition_lean_compiled": False,
            "semantic_definition_kernel_verified": False,
            "source_theorem_kernel_verified": False,
            "validation_errors": list(packet.get("validation_errors", []) or []),
            "failure_classification": str(
                packet.get("failure_classification", "") or ""
            ),
            "recommended_next_action": str(
                packet.get("recommended_next_action", "") or ""
            ),
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
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "missing_required_anchor_references": missing_source_anchor_references,
        "known_gaps": list(packet.get("known_gaps", []) or []),
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
        },
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
) -> list[str]:
    source = str(lean_source or "")
    missing: list[str] = []
    for raw_name in required_anchor_names:
        name = str(raw_name or "").strip()
        if not name:
            continue
        if not _lean_source_mentions_identifier(source, name):
            missing.append(name)
    return missing


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
        "materialization_row_id": str(row.get("materialization_row_id", "") or ""),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "runtime_queue_status": str(row.get("runtime_queue_status", "") or ""),
        **_exact_semantic_definition_context(row),
        "candidate_definition_request": dict(
            row.get("candidate_definition_request", {}) or {}
        ),
        "input_summary": {
            "trigger": "EXACT_SEMANTIC_DEFINITION_AUTHORING_CANDIDATE_MATERIALIZED",
            "materialization_status": str(row.get("materialization_status", "") or ""),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "local_definition_lean_checked": False,
            "local_definition_lean_compiled": False,
            "semantic_definition_kernel_verified": False,
            "source_theorem_kernel_verified": False,
            "validation_errors": list(row.get("validation_errors", []) or []),
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
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def _extract_payload(text: str) -> dict[str, Any]:
    return extract_json_object(
        text,
        label="Exact semantic-definition authoring candidate",
    )


def _is_external_llm_provider(provider_name: str) -> bool:
    return str(provider_name or "").strip().lower() in {"anthropic", "openai"}


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
    provider = str(provider_name or "").strip().lower()
    mode = _normalized_external_export_mode(export_mode)
    for row in approvals.get("approved_rows", []) or []:
        if not isinstance(row, Mapping):
            continue
        row_provider = str(row.get("provider_name", "") or "").strip().lower()
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
    return context


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
        "forbidden_shortcuts_absent": {"type": "boolean"},
        "requires_local_lean_check": {"type": "boolean"},
    },
}

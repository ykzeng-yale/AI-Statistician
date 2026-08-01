from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .fingerprint import stable_hash
from .exact_semantic_definition_policy import (
    ExactSemanticDefinitionPlaceholderPolicy,
    compact_exact_semantic_placeholder_key,
    exact_semantic_definition_fallback_source_anchor_role,
    exact_semantic_definition_placeholder_policies_for_mapping,
    exact_semantic_definition_policy_packs_for_mapping,
    exact_semantic_definition_source_to_bridge_adapter_object_names_requiring_source_instantiation as _policy_source_to_bridge_adapter_object_names,
    exact_semantic_definition_source_to_bridge_anchor_fallback_names,
    exact_semantic_definition_source_to_bridge_premise_binder_aliases,
)
from .formal_verifier_agentic_proof_execution_artifact_verifier import (
    FORBIDDEN_ARTIFACT_TOKENS,
    _lean_command,
)
from .lean_candidate_identity import run_lean_candidate_identity_probe
from .research_architect import KERNEL_PROOF_BOUNDARY


ARTIFACT_KIND = "SourceToBridgePremiseDerivationProofEngineerBridgeManifest"
PREMISE_ROW_KIND = "SourceToBridgePremiseDerivationCheckRow"
PREMISE_PROOF_EVIDENCE_STATUS = (
    "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_BRIDGE_NOT_PROOF_EVIDENCE"
)
PREMISE_KERNEL_VERIFIED_STATUS = (
    "KERNEL_VERIFIED_SOURCE_TO_BRIDGE_PREMISE_DERIVATIONS_PRESENT"
)
ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_KIND = (
    "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
)
ADAPTER_OBJECT_SEMANTIC_DEFINITION_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_work_order"
)
ADAPTER_OBJECT_SEMANTIC_DEFINITION_PROOF_EVIDENCE_STATUS = (
    "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE"
)
PROOF_BODY_SIGNATURE_PROBE_ARTIFACT_PATH_KEYS = (
    "proof_body_signature_probe_artifact_path",
    "source_theorem_signature_probe_artifact_path",
    "signature_probe_artifact_path",
)
SOURCE_THEOREM_SIGNATURE_PROBE_ARTIFACT_PATH_KEYS = (
    "source_theorem_signature_probe_artifact_path",
    "proof_body_signature_probe_artifact_path",
    "signature_probe_artifact_path",
)
BOUNDARY = (
    "Source-to-bridge premise derivation rows are ProofEngineer work items for "
    "deriving closure/bridge premise binders from exact source-theorem "
    "hypotheses. They are not full source theorem proof evidence. A row can "
    "become premise-derivation evidence only when a non-vacuous declaration for "
    "the specific premise compiles and its explicit identity resolves under local "
    "Lean/AXLE with no forbidden "
    "placeholder tokens. The exact source theorem still must be rerun and "
    "kernel verified separately."
)


@dataclass(frozen=True)
class SourceToBridgePremiseDerivationCheckRow:
    schema_version: int
    artifact_kind: str
    premise_derivation_check_id: str
    work_order_id: str
    source_adapter_check_id: str
    source_adapter_work_order_id: str
    source_queue_jsonl: str
    question_id: str
    question_title: str
    target_theorem_name: str
    target_lean_declaration: str
    target_ids: tuple[str, ...]
    target_theorem_goal_ids: tuple[str, ...]
    premise_name: str
    required_derivation: str
    source_to_bridge_premise_derivation_candidate_request_id: str
    source_to_bridge_premise_derivation_candidate_request: dict[str, object]
    source_to_bridge_grouped_premise_derivation_candidate_request_id: str
    source_to_bridge_grouped_premise_derivation_candidate_request: dict[str, object]
    exact_source_theorem_binders: tuple[dict[str, object], ...]
    premise_semantic_anchor_binders: tuple[dict[str, object], ...]
    premise_semantic_anchor_binder_names: tuple[str, ...]
    forbidden_as_adapter_assumption: bool
    source_candidate_artifact_path: str
    adapter_candidate_artifact_path: str
    proof_body_signature_probe_artifact_path: str
    source_theorem_signature_probe_artifact_path: str
    adapter_declaration_name: str
    source_theorem_signature_excerpt: tuple[str, ...]
    adapter_signature_excerpt: tuple[str, ...]
    source_context_status: str
    premise_target_status: str
    premise_target_matched_binder: str
    premise_target_type: str
    premise_target_source: str
    adapter_instantiation_group_id: str
    required_bridge_premise_names_for_shared_instantiation: tuple[str, ...]
    shared_adapter_instantiation_contract: str
    adapter_object_names_requiring_source_instantiation: tuple[str, ...]
    premise_derivation_gap_kind: str
    premise_derivation_gap_summary: str
    premise_semantic_dependency_status: str
    premise_semantic_dependency_source: str
    premise_semantic_dependency_requirements: tuple[str, ...]
    source_to_bridge_policy_pack_ids: tuple[str, ...]
    source_to_bridge_policy_ids: tuple[str, ...]
    source_to_bridge_policy_scopes: tuple[str, ...]
    source_to_bridge_policy_required_anchor_names: tuple[str, ...]
    source_to_bridge_policy_dependency_requirements: tuple[str, ...]
    premise_candidate_artifact_path: str
    premise_candidate_declaration_name: str
    premise_candidate_generation_mode: str
    premise_candidate_source_fingerprint: str
    premise_candidate_bytes_preserved: bool
    llm_candidate_generation_required: bool
    candidate_generation_request: dict[str, object]
    premise_candidate_vacuous: bool
    premise_candidate_assumes_forbidden_premise: bool
    premise_candidate_uninstantiated_adapter_object_binders: tuple[str, ...]
    premise_candidate_references_semantic_anchor: bool
    missing_premise_semantic_anchor_binder_names: tuple[str, ...]
    forbidden_tokens_found: tuple[str, ...]
    premise_candidate_evidence_eligible: bool
    exact_goal_shape_obligation_ids: tuple[str, ...]
    proof_body_goal_excerpt: tuple[str, ...]
    proof_body_goal_context: dict[str, object]
    proof_body_goal_binder_names: tuple[str, ...]
    proof_body_goal_conclusion: str
    proof_body_attempt_summaries: tuple[str, ...]
    proof_body_attempt_count: int
    proof_body_gate_status: str
    source_theorem_exact_proof_body_reached: bool
    source_theorem_exact_proof_body_gate_open_for_kernel_repair: bool
    source_theorem_exact_proof_body_gate_open_target_names: tuple[str, ...]
    semantic_alignment_constraints: tuple[str, ...]
    semantic_alignment_blockers: tuple[str, ...]
    source_theorem_kernel_evidence_eligible: bool
    kernel_verified_theorem_reduction_closure_declarations: tuple[str, ...]
    verified_theorem_reduction_closure_artifact_paths: tuple[str, ...]
    kernel_verified_source_theorem_semantic_support_obligation_ids: tuple[str, ...]
    acceptance_gate: str
    local_lean_requested: bool
    local_lean_checked: bool
    local_lean_source_compiled: bool
    local_lean_compiled: bool
    candidate_identity_lean_checked: bool
    candidate_identity_lean_verified: bool
    candidate_identity_probe_artifact_path: str
    lean_command: tuple[str, ...]
    lean_project: str
    lean_timeout: int
    returncode: int
    diagnostics: tuple[str, ...]
    failure_classification: str
    premise_derivation_kernel_verified: bool
    source_theorem_kernel_verified: bool
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool


def resolve_source_to_bridge_premise_derivation_queue_path(
    *,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
    adapter_bridge_dir: Path | None = None,
) -> Path:
    if queue_jsonl is not None:
        return queue_jsonl
    if adapter_bridge_dir is not None:
        manifest_path = (
            adapter_bridge_dir
            / "source_theorem_proof_body_adapter_proofengineer_bridge_manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_path = str(manifest.get("source_to_bridge_premise_derivation_queue_jsonl", "") or "")
        if not raw_path:
            raise ValueError(
                "adapter bridge manifest does not list "
                "source_to_bridge_premise_derivation_queue_jsonl"
            )
        return _resolve_artifact_path(base_dir=adapter_bridge_dir, raw_path=raw_path)
    if runtime_dir is None:
        raise ValueError("runtime_dir, queue_jsonl, or adapter_bridge_dir is required")
    manifest_path = runtime_dir / "research_agent_runtime_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        artifacts = {}
    raw_path = ""
    for key in (
        "runtime_source_to_bridge_premise_derivation_queue_jsonl",
        "runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer_jsonl",
    ):
        raw_path = str(artifacts.get(key, "") or "")
        if raw_path:
            break
    if raw_path:
        return _resolve_artifact_path(base_dir=runtime_dir, raw_path=raw_path)
    for candidate_name in (
        "runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer.jsonl",
        "runtime_source_to_bridge_premise_derivation_queue.jsonl",
    ):
        candidate_path = runtime_dir / candidate_name
        if candidate_path.exists():
            return candidate_path
    if not raw_path:
        raise ValueError(
            "runtime manifest does not list "
            "runtime_source_to_bridge_premise_derivation_queue_jsonl or "
            "runtime_source_to_bridge_premise_derivation_work_orders_from_formalizer_jsonl"
        )


def run_source_to_bridge_premise_derivation_proofengineer_bridge(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
    adapter_bridge_dir: Path | None = None,
    question_id: str = "",
    local_lean: bool = False,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = resolve_source_to_bridge_premise_derivation_queue_path(
        runtime_dir=runtime_dir,
        queue_jsonl=queue_jsonl,
        adapter_bridge_dir=adapter_bridge_dir,
    )
    work_orders = _read_jsonl(queue_path)
    project_path = Path(lean_project) if lean_project else None
    command = lean_command or _lean_command(project_path)
    candidate_dir = out_dir / "premise_derivation_candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        _premise_derivation_check_row(
            row,
            rank=rank,
            candidate_dir=candidate_dir,
            default_question_id=question_id,
            local_lean=local_lean,
            lean_project=project_path,
            lean_timeout=lean_timeout,
            lean_command=command,
        )
        for rank, row in enumerate(work_orders, start=1)
        if isinstance(row, Mapping)
    ]
    rows_path = out_dir / "source_to_bridge_premise_derivation_checks.jsonl"
    _write_jsonl(rows_path, [asdict(row) for row in rows])
    adapter_object_semantic_definition_work_order_rows = (
        _adapter_object_semantic_definition_work_order_rows(
            rows=rows,
            queue_path=queue_path,
        )
    )
    adapter_object_semantic_definition_work_orders_path = (
        out_dir / "source_to_bridge_adapter_object_semantic_definition_work_orders.jsonl"
    )
    _write_jsonl(
        adapter_object_semantic_definition_work_orders_path,
        adapter_object_semantic_definition_work_order_rows,
    )
    learning_result = _export_runtime_learning_rows(
        rows=rows,
        out_dir=out_dir / "runtime_learning_export",
        question_id=question_id,
        queue_path=queue_path,
        adapter_object_semantic_definition_work_orders=(
            adapter_object_semantic_definition_work_order_rows
        ),
    )
    candidate_request_rows = _premise_derivation_candidate_request_rows(
        rows=rows,
        queue_path=queue_path,
    )
    candidate_requests_path = (
        out_dir / "source_to_bridge_premise_derivation_candidate_requests.jsonl"
    )
    _write_jsonl(candidate_requests_path, candidate_request_rows)
    grouped_candidate_request_rows = (
        _grouped_premise_derivation_candidate_request_rows(
            rows=rows,
            queue_path=queue_path,
        )
    )
    grouped_candidate_requests_path = (
        out_dir
        / "source_to_bridge_grouped_premise_derivation_candidate_requests.jsonl"
    )
    _write_jsonl(grouped_candidate_requests_path, grouped_candidate_request_rows)
    verified_ids = [
        row.premise_derivation_check_id
        for row in rows
        if row.premise_derivation_kernel_verified
    ]
    by_failure_classification: dict[str, int] = {}
    by_semantic_dependency_source: dict[str, int] = {}
    for row in rows:
        failure = row.failure_classification or "none"
        by_failure_classification[failure] = by_failure_classification.get(failure, 0) + 1
        dependency_source = row.premise_semantic_dependency_source or "none"
        by_semantic_dependency_source[dependency_source] = (
            by_semantic_dependency_source.get(dependency_source, 0) + 1
        )
    dominant_failure_classification = ""
    if by_failure_classification:
        dominant_failure_classification = sorted(
            by_failure_classification.items(),
            key=lambda item: (-item[1], item[0]),
        )[0][0]
    n_local_lean_skipped_not_evidence_eligible = sum(
        1
        for row in rows
        if row.local_lean_requested
        and not row.local_lean_checked
        and not row.premise_candidate_evidence_eligible
    )
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_runtime_dir": str(runtime_dir or ""),
        "source_adapter_bridge_dir": str(adapter_bridge_dir or ""),
        "source_queue_jsonl": str(queue_path),
        "checks_jsonl": str(rows_path),
        "runtime_learning_rows_jsonl": str(learning_result["runtime_learning_rows_jsonl"]),
        "runtime_learning_export_manifest": str(learning_result["export_manifest_path"]),
        "source_to_bridge_adapter_object_semantic_definition_work_orders_jsonl": str(
            adapter_object_semantic_definition_work_orders_path
        ),
        "candidate_requests_jsonl": str(candidate_requests_path),
        "grouped_candidate_requests_jsonl": str(grouped_candidate_requests_path),
        "premise_derivation_candidate_dir": str(candidate_dir),
        "local_lean_requested": bool(local_lean),
        "local_lean_project": str(project_path or ""),
        "local_lean_timeout_seconds": int(lean_timeout),
        "lean_command": list(command),
        "n_work_orders": len(work_orders),
        "n_premise_derivation_check_rows": len(rows),
        "n_local_lean_checked": sum(1 for row in rows if row.local_lean_checked),
        "n_local_lean_source_compiled": sum(
            1 for row in rows if row.local_lean_source_compiled
        ),
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
        "n_candidate_identity_lean_checked": sum(
            1 for row in rows if row.candidate_identity_lean_checked
        ),
        "n_candidate_identity_lean_verified": sum(
            1 for row in rows if row.candidate_identity_lean_verified
        ),
        "n_local_lean_skipped_not_evidence_eligible": (
            n_local_lean_skipped_not_evidence_eligible
        ),
        "n_premise_candidate_evidence_eligible": sum(
            1 for row in rows if row.premise_candidate_evidence_eligible
        ),
        "n_premise_candidate_uninstantiated_adapter_object_binders": sum(
            1 for row in rows if row.premise_candidate_uninstantiated_adapter_object_binders
        ),
        "n_premise_derivation_kernel_verified": len(verified_ids),
        "n_premise_derivation_candidate_requests": len(candidate_request_rows),
        "n_llm_candidate_generation_required": sum(
            1 for row in rows if row.llm_candidate_generation_required
        ),
        "n_premise_candidate_bytes_preserved": sum(
            1 for row in rows if row.premise_candidate_bytes_preserved
        ),
        "n_grouped_premise_derivation_candidate_requests": len(
            grouped_candidate_request_rows
        ),
        "n_grouped_premise_derivation_learning_rows": int(
            dict(learning_result["export_manifest"]).get(
                "n_grouped_premise_derivation_learning_rows",
                0,
            )
            or 0
        ),
        "n_source_to_bridge_adapter_object_semantic_definition_work_orders": len(
            adapter_object_semantic_definition_work_order_rows
        ),
        "n_source_to_bridge_policy_lineage_rows": sum(
            1 for row in rows if row.source_to_bridge_policy_ids
        ),
        "source_to_bridge_policy_pack_ids": list(
            dict.fromkeys(
                policy_pack_id
                for row in rows
                for policy_pack_id in row.source_to_bridge_policy_pack_ids
                if policy_pack_id
            )
        ),
        "source_to_bridge_policy_ids": list(
            dict.fromkeys(
                policy_id
                for row in rows
                for policy_id in row.source_to_bridge_policy_ids
                if policy_id
            )
        ),
        "by_premise_semantic_dependency_source": by_semantic_dependency_source,
        "proof_body_gate_statuses": sorted(
            {
                row.proof_body_gate_status
                for row in rows
                if row.proof_body_gate_status
            }
        ),
        "n_source_theorem_exact_proof_body_gate_open_for_kernel_repair": sum(
            1
            for row in rows
            if row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
        ),
        "n_proof_body_signature_probe_artifact_rows": sum(
            1 for row in rows if row.proof_body_signature_probe_artifact_path
        ),
        "n_proof_body_goal_context_rows": sum(
            1
            for row in rows
            if row.proof_body_goal_binder_names or row.proof_body_goal_conclusion
        ),
        "proof_body_goal_context_binder_names": sorted(
            {
                binder_name
                for row in rows
                for binder_name in row.proof_body_goal_binder_names
                if binder_name
            }
        ),
        "proof_body_goal_context_conclusions": [
            row.proof_body_goal_conclusion
            for row in rows
            if row.proof_body_goal_conclusion
        ][:8],
        "proof_body_signature_probe_artifact_paths": sorted(
            {
                row.proof_body_signature_probe_artifact_path
                for row in rows
                if row.proof_body_signature_probe_artifact_path
            }
        ),
        "source_theorem_exact_proof_body_gate_open_target_names": (
            _proof_body_gate_open_target_names_for_rows(rows)
        ),
        "source_to_bridge_adapter_object_semantic_definition_placeholder_symbols": [
            str(row.get("placeholder_symbol", "") or "")
            for row in adapter_object_semantic_definition_work_order_rows
            if str(row.get("placeholder_symbol", "") or "")
        ],
        "adapter_instantiation_group_ids": list(
            dict.fromkeys(
                row.adapter_instantiation_group_id
                for row in rows
                if row.adapter_instantiation_group_id
            )
        ),
        "premise_derivation_candidate_request_premise_names": [
            str(row.get("premise_name", "") or "")
            for row in candidate_request_rows
            if str(row.get("premise_name", "") or "")
        ],
        "by_failure_classification": by_failure_classification,
        "dominant_failure_classification": dominant_failure_classification,
        "kernel_verified_source_to_bridge_premise_derivation_ids": verified_ids,
        "source_theorem_kernel_verified": False,
        "runtime_learning_ready": bool(learning_result["n_learning_rows"]),
        "proof_evidence_status": (
            PREMISE_KERNEL_VERIFIED_STATUS
            if verified_ids
            else PREMISE_PROOF_EVIDENCE_STATUS
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "boundary": BOUNDARY,
        "rows": [asdict(row) for row in rows],
    }
    manifest_path = (
        out_dir / "source_to_bridge_premise_derivation_proofengineer_bridge_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def _premise_derivation_check_row(
    row: Mapping[str, Any],
    *,
    rank: int,
    candidate_dir: Path,
    default_question_id: str,
    local_lean: bool,
    lean_project: Path | None,
    lean_timeout: int,
    lean_command: tuple[str, ...],
) -> SourceToBridgePremiseDerivationCheckRow:
    work_order_id = str(row.get("work_order_id", "") or row.get("queue_id", "") or "")
    premise_name = str(row.get("premise_name", "") or "").strip()
    target_declaration = str(
        row.get("target_lean_declaration", "")
        or row.get("target_theorem_name", "")
        or ""
    ).strip()
    candidate_request_raw = row.get(
        "source_to_bridge_premise_derivation_candidate_request", {}
    )
    candidate_request = (
        dict(candidate_request_raw) if isinstance(candidate_request_raw, Mapping) else {}
    )
    grouped_candidate_request_raw = row.get(
        "source_to_bridge_grouped_premise_derivation_candidate_request", {}
    )
    grouped_candidate_request = (
        dict(grouped_candidate_request_raw)
        if isinstance(grouped_candidate_request_raw, Mapping)
        else {}
    )
    candidate_request_id = str(
        row.get("source_to_bridge_premise_derivation_candidate_request_id", "")
        or row.get("candidate_request_id", "")
        or candidate_request.get("candidate_request_id", "")
        or ""
    ).strip()
    grouped_candidate_request_id = str(
        row.get("source_to_bridge_grouped_premise_derivation_candidate_request_id", "")
        or row.get("grouped_candidate_request_id", "")
        or grouped_candidate_request.get("grouped_candidate_request_id", "")
        or ""
    ).strip()
    source_binding_contract_present = _source_binding_contract_present(
        row=row,
        candidate_request=candidate_request,
        grouped_candidate_request=grouped_candidate_request,
        candidate_request_id=candidate_request_id,
        grouped_candidate_request_id=grouped_candidate_request_id,
    )
    proof_body_goal_context = _proof_body_goal_context_from_sources(
        row,
        candidate_request,
        grouped_candidate_request,
    )
    proof_body_goal_binder_names = _proof_body_goal_binder_names_from_sources(
        row,
        candidate_request,
        grouped_candidate_request,
        proof_body_goal_context=proof_body_goal_context,
    )
    proof_body_goal_conclusion = _proof_body_goal_conclusion_from_sources(
        row,
        candidate_request,
        grouped_candidate_request,
        proof_body_goal_context=proof_body_goal_context,
    )
    safe_target = _safe_identifier(target_declaration or f"source_theorem_{rank}")
    safe_premise = _safe_identifier(premise_name or f"premise_{rank}")
    default_declaration_name = f"{safe_target}_{safe_premise}_source_to_bridge_derivation"
    declaration_name = _requested_premise_candidate_declaration_name(
        row=row,
        candidate_request=candidate_request,
        default=default_declaration_name,
    )
    candidate_hash = stable_hash([work_order_id, premise_name, target_declaration, rank])[:16]
    candidate_path = candidate_dir / f"{declaration_name}_{candidate_hash}.lean"
    source_candidate_artifact_path = str(
        row.get("source_candidate_artifact_path", "") or ""
    )
    adapter_candidate_artifact_path = str(
        row.get("adapter_candidate_artifact_path", "") or ""
    )
    adapter_declaration_name = str(row.get("adapter_declaration_name", "") or "")
    proof_body_signature_probe_artifact_path = (
        _proof_body_signature_probe_artifact_path_from_sources(
            row,
            candidate_request,
            grouped_candidate_request,
        )
    )
    source_theorem_signature_probe_artifact_path = (
        _source_theorem_signature_probe_artifact_path_from_sources(
            row,
            candidate_request,
            grouped_candidate_request,
        )
    )
    source_context = _source_context_from_candidate(
        source_candidate_artifact_path=source_candidate_artifact_path,
        adapter_candidate_artifact_path=adapter_candidate_artifact_path,
        target_declaration=target_declaration,
        adapter_declaration_name=adapter_declaration_name,
    )
    policy_scope_context = {
        **dict(grouped_candidate_request),
        **dict(candidate_request),
        **dict(row),
    }
    premise_target = _adapter_premise_target_from_signature(
        adapter_signature=source_context["adapter_signature"],
        premise_name=premise_name,
        context=policy_scope_context,
    )
    if not str(premise_target.get("premise_type", "") or "").strip():
        explicit_premise_type = str(
            row.get("premise_target_type", "")
            or candidate_request.get("premise_target_type", "")
            or grouped_candidate_request.get("premise_target_type", "")
            or ""
        ).strip()
        if explicit_premise_type:
            premise_target = {
                "status": "ADAPTER_PREMISE_TARGET_EXTRACTED",
                "matched_premise_binder": str(
                    row.get("premise_target_matched_binder", "")
                    or candidate_request.get("premise_target_matched_binder", "")
                    or (
                        f"({premise_name} : {explicit_premise_type})"
                        if premise_name
                        else ""
                    )
                    or ""
                ),
                "premise_type": explicit_premise_type,
            }
    premise_target_type = str(premise_target.get("premise_type", "") or "")
    premise_target_source = str(
        row.get("premise_target_source", "")
        or row.get("source_to_bridge_premise_target_source", "")
        or ("adapter_signature" if premise_target_type else "")
    ).strip()
    premise_target_uses_goal_context = _premise_target_uses_proof_body_goal_context(
        premise_target_source=premise_target_source,
        premise_target_type=premise_target_type,
        proof_body_goal_conclusion=proof_body_goal_conclusion,
    )
    adapter_instantiation_group_id = _adapter_instantiation_group_id(
        row=row,
        target_declaration=target_declaration,
        adapter_declaration_name=adapter_declaration_name,
        source_context=source_context,
    )
    required_bridge_premise_names_for_shared_instantiation = _str_tuple(
        row.get("required_bridge_premise_names_for_shared_instantiation", [])
        or candidate_request.get(
            "required_bridge_premise_names_for_shared_instantiation",
            [],
        )
        or grouped_candidate_request.get(
            "required_bridge_premise_names_for_shared_instantiation",
            [],
        )
        or grouped_candidate_request.get("premise_names", [])
    )
    shared_adapter_instantiation_contract = str(
        row.get("shared_adapter_instantiation_contract", "")
        or candidate_request.get("shared_adapter_instantiation_contract", "")
        or grouped_candidate_request.get("shared_adapter_instantiation_contract", "")
        or ""
    )
    provided_source = _candidate_source_from_work_order(row)
    if provided_source:
        source = provided_source
        generation_mode = "formalizer_provided_premise_derivation_candidate"
        candidate_path.write_text(source, encoding="utf-8")
    else:
        source = ""
        generation_mode = "llm_premise_derivation_candidate_required"

    exact_source_binders = _request_mapping_tuple(
        row.get("exact_source_theorem_binders", [])
        or candidate_request.get("exact_source_theorem_binders", [])
        or grouped_candidate_request.get("exact_source_theorem_binders", [])
        or _source_theorem_binder_summaries(
            source_context["source_theorem_signature"],
            context=policy_scope_context,
        )
    )
    forbidden_tokens = _forbidden_tokens(source)
    vacuous = _premise_candidate_vacuous(
        source,
        declaration_name=declaration_name,
    )
    assumes_forbidden_premise = _candidate_assumes_forbidden_premise(
        source,
        declaration_name=declaration_name,
        premise_name=premise_name,
        premise_target_type=premise_target_type,
        forbidden_as_adapter_assumption=bool(
            row.get("forbidden_as_adapter_assumption", False)
        ),
        allowed_source_binder_names=tuple(
            str(item.get("name", "") or "")
            for item in exact_source_binders
            if isinstance(item, Mapping) and str(item.get("name", "") or "")
        ),
    )
    goal_context_semantic_requirements = (
        _proof_body_goal_semantic_dependency_requirements(
            proof_body_goal_context=proof_body_goal_context,
            proof_body_goal_binder_names=proof_body_goal_binder_names,
            proof_body_goal_conclusion=proof_body_goal_conclusion,
        )
        if premise_target_uses_goal_context
        else ()
    )
    explicit_semantic_requirements = _explicit_premise_semantic_dependency_requirements(
        row,
        candidate_request,
        grouped_candidate_request,
    )
    policy_context = _source_to_bridge_policy_context(
        premise_name=premise_name,
        premise_target_type=premise_target_type,
        context=policy_scope_context,
    )
    fallback_semantic_requirements = _premise_semantic_dependency_requirements(
        premise_name=premise_name,
        premise_target_type=premise_target_type,
        source_signature=source_context["source_theorem_signature"],
        context=policy_scope_context,
    )
    if explicit_semantic_requirements:
        semantic_requirements = explicit_semantic_requirements
        semantic_dependency_source = "explicit_runtime_metadata"
    elif goal_context_semantic_requirements:
        semantic_requirements = goal_context_semantic_requirements
        semantic_dependency_source = "proof_body_goal_context"
    elif policy_context["source_to_bridge_policy_dependency_requirements"]:
        semantic_requirements = fallback_semantic_requirements
        semantic_dependency_source = "policy_pack"
    elif fallback_semantic_requirements:
        semantic_requirements = fallback_semantic_requirements
        semantic_dependency_source = "generic_target_fallback"
    else:
        semantic_requirements = ()
        semantic_dependency_source = "none"
    goal_context_anchor_binders = (
        _proof_body_goal_semantic_anchor_binders(
            proof_body_goal_context=proof_body_goal_context,
            proof_body_goal_binder_names=proof_body_goal_binder_names,
            source_binders=tuple(
                dict(item) for item in exact_source_binders if isinstance(item, Mapping)
            ),
            context=policy_scope_context,
        )
        if premise_target_uses_goal_context
        else ()
    )
    semantic_anchor_binders = _request_mapping_tuple(
        row.get("premise_semantic_anchor_binders", [])
        or candidate_request.get("premise_semantic_anchor_binders", [])
        or grouped_candidate_request.get("premise_semantic_anchor_binders", [])
        or goal_context_anchor_binders
        or _premise_semantic_anchor_binder_summaries(
            premise_name=premise_name,
            premise_target_type=premise_target_type,
            semantic_requirements=semantic_requirements,
            source_binders=tuple(
                dict(item) for item in exact_source_binders if isinstance(item, Mapping)
            ),
            context=policy_scope_context,
        )
    )
    semantic_anchor_binder_names = _str_tuple(
        row.get("required_semantic_anchor_reference_names", [])
        or candidate_request.get("required_semantic_anchor_reference_names", [])
        or grouped_candidate_request.get("required_semantic_anchor_reference_names", [])
        or row.get("premise_semantic_anchor_binder_names", [])
        or candidate_request.get("premise_semantic_anchor_binder_names", [])
        or grouped_candidate_request.get("premise_semantic_anchor_binder_names", [])
        or [
            str(item.get("name", "") or "")
            for item in goal_context_anchor_binders
            if isinstance(item, Mapping) and str(item.get("name", "") or "")
        ]
        or [
            str(item.get("name", "") or "")
            for item in semantic_anchor_binders
            if isinstance(item, Mapping) and str(item.get("name", "") or "")
        ]
    )
    missing_semantic_anchor_names = (
        _missing_semantic_anchor_references(
            source,
            declaration_name=declaration_name,
            anchor_names=semantic_anchor_binder_names,
        )
        if provided_source
        else ()
    )
    adapter_object_names = _adapter_object_names_requiring_source_instantiation(
        premise_target_type=premise_target_type,
        row=row,
        candidate_request={**grouped_candidate_request, **candidate_request},
    )
    uninstantiated_adapter_object_binders = (
        _candidate_uninstantiated_adapter_object_binders(
            source,
            declaration_name=declaration_name,
            adapter_object_names=adapter_object_names,
        )
        if provided_source
        else ()
    )
    references_semantic_anchor = not missing_semantic_anchor_names
    candidate_identity_present = bool(declaration_name)
    premise_referenced = _premise_name_referenced_by_candidate(
        source,
        premise_name=premise_name,
        declaration_name=declaration_name,
    )
    evidence_eligible = bool(
        provided_source
        and source_binding_contract_present
        and candidate_identity_present
        and premise_referenced
        and not vacuous
        and not assumes_forbidden_premise
        and not uninstantiated_adapter_object_binders
        and references_semantic_anchor
        and not forbidden_tokens
    )
    local_source_compiled = False
    local_compiled = False
    local_checked = False
    candidate_identity_checked = False
    candidate_identity_verified = False
    candidate_identity_probe_artifact_path = ""
    returncode = 0
    diagnostics: tuple[str, ...] = ()
    if local_lean and evidence_eligible:
        local_checked = True
        if not lean_command:
            returncode = -1
            diagnostics = ("local Lean executable not found",)
        else:
            lean_result = run_lean_candidate_identity_probe(
                artifact_path=candidate_path,
                candidate_lean_declaration=declaration_name,
                lean_command=lean_command,
                lean_project=lean_project,
                lean_timeout=lean_timeout,
            )
            local_source_compiled = bool(
                lean_result.get("local_lean_source_compiled", False)
            )
            local_compiled = bool(lean_result.get("local_lean_compiled", False))
            candidate_identity_checked = bool(
                lean_result.get("candidate_identity_lean_checked", False)
            )
            candidate_identity_verified = bool(
                lean_result.get("candidate_identity_lean_verified", False)
            )
            candidate_identity_probe_artifact_path = str(
                lean_result.get("candidate_identity_probe_artifact_path", "") or ""
            )
            exit_status = str(
                lean_result.get("local_lean_exit_status", "") or ""
            )
            returncode = int(exit_status) if exit_status.lstrip("-").isdigit() else -1
            diagnostics = tuple(
                line
                for value in (
                    lean_result.get("local_lean_stdout", ""),
                    lean_result.get("local_lean_stderr", ""),
                )
                for line in str(value or "").splitlines()
                if line.strip()
            )
    elif local_lean and not evidence_eligible:
        diagnostics = (
            "local Lean skipped because premise derivation candidate is not evidence eligible",
        )
    failure = _premise_failure_classification(
        local_lean=local_lean,
        local_source_compiled=local_source_compiled,
        local_compiled=local_compiled,
        provided_source=bool(provided_source),
        evidence_eligible=evidence_eligible,
        candidate_identity_present=candidate_identity_present,
        candidate_identity_checked=candidate_identity_checked,
        candidate_identity_verified=candidate_identity_verified,
        premise_referenced=premise_referenced,
        source_binding_contract_present=source_binding_contract_present,
        vacuous=vacuous,
        assumes_forbidden_premise=assumes_forbidden_premise,
        uninstantiated_adapter_object_binders=uninstantiated_adapter_object_binders,
        references_semantic_anchor=references_semantic_anchor,
        forbidden_tokens=forbidden_tokens,
        diagnostics=diagnostics,
    )
    premise_verified = bool(
        local_lean
        and local_compiled
        and candidate_identity_verified
        and evidence_eligible
    )
    llm_candidate_generation_required = not bool(provided_source)
    candidate_generation_request = (
        {
            "schema_version": 1,
            "request_kind": "source_to_bridge_premise_derivation_lean_candidate",
            "work_order_id": work_order_id,
            "target_lean_declaration": target_declaration,
            "premise_name": premise_name,
            "premise_candidate_declaration_name": declaration_name,
            "candidate_request_id": candidate_request_id,
            "grouped_candidate_request_id": grouped_candidate_request_id,
            "premise_target_status": str(premise_target.get("status", "") or ""),
            "premise_target_type": premise_target_type,
            "premise_target_source": premise_target_source,
            "proof_body_goal_context": proof_body_goal_context,
            "exact_source_theorem_binders": list(exact_source_binders),
            "premise_semantic_anchor_binders": list(semantic_anchor_binders),
            "premise_semantic_anchor_binder_names": list(
                semantic_anchor_binder_names
            ),
            "premise_semantic_dependency_requirements": list(
                semantic_requirements
            ),
            "adapter_object_names_requiring_source_instantiation": list(
                adapter_object_names
            ),
            "source_theorem_signature_excerpt": list(
                source_context["source_theorem_signature"]
            ),
            "adapter_signature_excerpt": list(source_context["adapter_signature"]),
            "source_context_status": source_context["status"],
            "source_candidate_artifact_path": source_candidate_artifact_path,
            "adapter_candidate_artifact_path": adapter_candidate_artifact_path,
            "proof_body_signature_probe_artifact_path": (
                proof_body_signature_probe_artifact_path
            ),
            "adapter_declaration_name": adapter_declaration_name,
            "verified_theorem_reduction_closure_artifact_paths": list(
                _str_tuple(
                    row.get("verified_theorem_reduction_closure_artifact_paths", [])
                )
            ),
            "kernel_verified_theorem_reduction_closure_declarations": list(
                _str_tuple(
                    row.get(
                        "kernel_verified_theorem_reduction_closure_declarations",
                        [],
                    )
                )
            ),
            "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
                _str_tuple(
                    row.get(
                        "kernel_verified_source_theorem_semantic_support_obligation_ids",
                        [],
                    )
                )
            ),
            "proof_body_attempt_summaries": list(
                _str_tuple(row.get("proof_body_attempt_summaries", []))
            ),
            "proof_body_attempt_count": _int_like(
                row.get("proof_body_attempt_count", 0)
            ),
            "proof_body_gate_status": str(
                row.get("proof_body_gate_status", "") or ""
            ),
            "source_theorem_kernel_evidence_eligible": bool(
                row.get("source_theorem_kernel_evidence_eligible", False)
            ),
            "semantic_alignment_constraints": list(
                _str_tuple(row.get("semantic_alignment_constraints", []))
            ),
            "semantic_alignment_blockers": list(
                _str_tuple(row.get("semantic_alignment_blockers", []))
            ),
            "proof_evidence_status": "LEAN_CANDIDATE_GENERATION_REQUEST_NOT_PROOF_EVIDENCE",
        }
        if llm_candidate_generation_required
        else {}
    )
    gap_kind, gap_summary = _premise_derivation_gap(
        premise_name=premise_name,
        premise_target_status=str(premise_target.get("status", "") or ""),
        premise_target_type=str(premise_target.get("premise_type", "") or ""),
        generation_mode=generation_mode,
        evidence_eligible=evidence_eligible,
        premise_verified=premise_verified,
        assumes_forbidden_premise=assumes_forbidden_premise,
        uninstantiated_adapter_object_binders=uninstantiated_adapter_object_binders,
        source_binding_contract_present=source_binding_contract_present,
        references_semantic_anchor=references_semantic_anchor,
        missing_semantic_anchor_names=missing_semantic_anchor_names,
        local_lean=local_lean,
        local_compiled=local_compiled,
        failure_classification=failure,
    )
    semantic_dependency_status = (
        "SOURCE_TO_BRIDGE_PREMISE_SEMANTIC_DEPENDENCIES_REQUIRED"
        if semantic_requirements
        else "NO_STRUCTURED_PREMISE_SEMANTIC_DEPENDENCIES_INFERRED"
    )
    check_id = "source_to_bridge_premise_derivation_check:" + stable_hash(
        [work_order_id, premise_name, str(candidate_path), premise_verified, failure]
    )[:20]
    return SourceToBridgePremiseDerivationCheckRow(
        schema_version=1,
        artifact_kind=PREMISE_ROW_KIND,
        premise_derivation_check_id=check_id,
        work_order_id=work_order_id,
        source_adapter_check_id=str(row.get("source_adapter_check_id", "") or ""),
        source_adapter_work_order_id=str(
            row.get("source_adapter_work_order_id", "") or ""
        ),
        source_queue_jsonl=str(row.get("source_queue_jsonl", "") or ""),
        question_id=str(row.get("question_id", "") or default_question_id or ""),
        question_title=str(row.get("question_title", "") or ""),
        target_theorem_name=str(row.get("target_theorem_name", "") or ""),
        target_lean_declaration=target_declaration,
        target_ids=_target_ids_from_work_order(
            row,
            fallback_target=target_declaration
            or str(row.get("target_theorem_name", "") or ""),
        ),
        target_theorem_goal_ids=_str_tuple(row.get("target_theorem_goal_ids", [])),
        premise_name=premise_name,
        required_derivation=str(row.get("required_derivation", "") or ""),
        source_to_bridge_premise_derivation_candidate_request_id=(
            candidate_request_id
        ),
        source_to_bridge_premise_derivation_candidate_request=candidate_request,
        source_to_bridge_grouped_premise_derivation_candidate_request_id=(
            grouped_candidate_request_id
        ),
        source_to_bridge_grouped_premise_derivation_candidate_request=(
            grouped_candidate_request
        ),
        exact_source_theorem_binders=exact_source_binders,
        premise_semantic_anchor_binders=semantic_anchor_binders,
        premise_semantic_anchor_binder_names=semantic_anchor_binder_names,
        forbidden_as_adapter_assumption=bool(
            row.get("forbidden_as_adapter_assumption", False)
        ),
        source_candidate_artifact_path=source_candidate_artifact_path,
        adapter_candidate_artifact_path=adapter_candidate_artifact_path,
        proof_body_signature_probe_artifact_path=(
            proof_body_signature_probe_artifact_path
        ),
        source_theorem_signature_probe_artifact_path=(
            source_theorem_signature_probe_artifact_path
        ),
        adapter_declaration_name=adapter_declaration_name,
        source_theorem_signature_excerpt=source_context["source_theorem_signature"],
        adapter_signature_excerpt=source_context["adapter_signature"],
        source_context_status=source_context["status"],
        premise_target_status=str(premise_target.get("status", "") or ""),
        premise_target_matched_binder=str(
            premise_target.get("matched_premise_binder", "") or ""
        ),
        premise_target_type=str(premise_target.get("premise_type", "") or ""),
        premise_target_source=premise_target_source,
        adapter_instantiation_group_id=adapter_instantiation_group_id,
        required_bridge_premise_names_for_shared_instantiation=(
            required_bridge_premise_names_for_shared_instantiation
        ),
        shared_adapter_instantiation_contract=shared_adapter_instantiation_contract,
        adapter_object_names_requiring_source_instantiation=adapter_object_names,
        premise_derivation_gap_kind=gap_kind,
        premise_derivation_gap_summary=gap_summary,
        premise_semantic_dependency_status=semantic_dependency_status,
        premise_semantic_dependency_source=semantic_dependency_source,
        premise_semantic_dependency_requirements=semantic_requirements,
        source_to_bridge_policy_pack_ids=tuple(
            policy_context["source_to_bridge_policy_pack_ids"]
        ),
        source_to_bridge_policy_ids=tuple(
            policy_context["source_to_bridge_policy_ids"]
        ),
        source_to_bridge_policy_scopes=tuple(
            policy_context["source_to_bridge_policy_scopes"]
        ),
        source_to_bridge_policy_required_anchor_names=tuple(
            policy_context["source_to_bridge_policy_required_anchor_names"]
        ),
        source_to_bridge_policy_dependency_requirements=tuple(
            policy_context["source_to_bridge_policy_dependency_requirements"]
        ),
        premise_candidate_artifact_path=(str(candidate_path) if source else ""),
        premise_candidate_declaration_name=declaration_name,
        premise_candidate_generation_mode=generation_mode,
        premise_candidate_source_fingerprint=(
            stable_hash(provided_source) if provided_source else ""
        ),
        premise_candidate_bytes_preserved=bool(
            provided_source and source == provided_source
        ),
        llm_candidate_generation_required=llm_candidate_generation_required,
        candidate_generation_request=candidate_generation_request,
        premise_candidate_vacuous=vacuous,
        premise_candidate_assumes_forbidden_premise=assumes_forbidden_premise,
        premise_candidate_uninstantiated_adapter_object_binders=(
            uninstantiated_adapter_object_binders
        ),
        premise_candidate_references_semantic_anchor=references_semantic_anchor,
        missing_premise_semantic_anchor_binder_names=missing_semantic_anchor_names,
        forbidden_tokens_found=forbidden_tokens,
        premise_candidate_evidence_eligible=evidence_eligible,
        exact_goal_shape_obligation_ids=_str_tuple(
            row.get("exact_goal_shape_obligation_ids", [])
        ),
        proof_body_goal_excerpt=_str_tuple(row.get("proof_body_goal_excerpt", [])),
        proof_body_goal_context=proof_body_goal_context,
        proof_body_goal_binder_names=proof_body_goal_binder_names,
        proof_body_goal_conclusion=proof_body_goal_conclusion,
        proof_body_attempt_summaries=_str_tuple(
            row.get("proof_body_attempt_summaries", [])
        ),
        proof_body_attempt_count=_int_like(row.get("proof_body_attempt_count", 0)),
        proof_body_gate_status=str(row.get("proof_body_gate_status", "") or ""),
        source_theorem_exact_proof_body_reached=_bool_like(
            row.get("source_theorem_exact_proof_body_reached", False)
        ),
        source_theorem_exact_proof_body_gate_open_for_kernel_repair=_bool_like(
            row.get(
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
                False,
            )
        ),
        source_theorem_exact_proof_body_gate_open_target_names=_str_tuple(
            row.get("source_theorem_exact_proof_body_gate_open_target_names", [])
        ),
        semantic_alignment_constraints=_str_tuple(
            row.get("semantic_alignment_constraints", [])
        ),
        semantic_alignment_blockers=_str_tuple(
            row.get("semantic_alignment_blockers", [])
        ),
        source_theorem_kernel_evidence_eligible=bool(
            row.get("source_theorem_kernel_evidence_eligible", False)
        ),
        kernel_verified_theorem_reduction_closure_declarations=_str_tuple(
            row.get("kernel_verified_theorem_reduction_closure_declarations", [])
        ),
        verified_theorem_reduction_closure_artifact_paths=_str_tuple(
            row.get("verified_theorem_reduction_closure_artifact_paths", [])
        ),
        kernel_verified_source_theorem_semantic_support_obligation_ids=_str_tuple(
            row.get("kernel_verified_source_theorem_semantic_support_obligation_ids", [])
        ),
        acceptance_gate=str(row.get("acceptance_gate", "") or ""),
        local_lean_requested=bool(local_lean),
        local_lean_checked=local_checked,
        local_lean_source_compiled=local_source_compiled,
        local_lean_compiled=local_compiled,
        candidate_identity_lean_checked=candidate_identity_checked,
        candidate_identity_lean_verified=candidate_identity_verified,
        candidate_identity_probe_artifact_path=(
            candidate_identity_probe_artifact_path
        ),
        lean_command=lean_command,
        lean_project=str(lean_project or ""),
        lean_timeout=int(lean_timeout),
        returncode=int(returncode),
        diagnostics=diagnostics,
        failure_classification=failure,
        premise_derivation_kernel_verified=premise_verified,
        source_theorem_kernel_verified=False,
        proof_evidence_status=(
            PREMISE_KERNEL_VERIFIED_STATUS
            if premise_verified
            else PREMISE_PROOF_EVIDENCE_STATUS
        ),
        proof_evidence_boundary=KERNEL_PROOF_BOUNDARY,
        ok=premise_verified,
    )


def _candidate_source_from_work_order(row: Mapping[str, Any]) -> str:
    source = _candidate_source_from_candidate_mapping(
        row,
        premise_name=str(row.get("premise_name", "") or ""),
    )
    if source:
        return source
    for key in (
        "source_to_bridge_grouped_premise_derivation_candidate_request",
        "source_to_bridge_premise_derivation_candidate_request",
    ):
        value = row.get(key, {})
        if isinstance(value, Mapping):
            source = _candidate_source_from_candidate_mapping(
                value,
                premise_name=str(row.get("premise_name", "") or ""),
            )
            if source:
                return source
    for key in (
        "source_to_bridge_premise_derivation_candidates",
        "premise_derivation_candidates",
    ):
        value = row.get(key, [])
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            continue
        for item in value:
            if not isinstance(item, Mapping):
                continue
            source = _candidate_source_from_candidate_mapping(
                item,
                premise_name=str(row.get("premise_name", "") or ""),
            )
            if source:
                return source
    return ""


def _proof_body_goal_context_from_sources(
    *sources: Mapping[str, Any],
) -> dict[str, object]:
    for source in sources:
        for key in (
            "source_to_bridge_premise_goal_context",
            "proof_body_goal_context",
        ):
            value = source.get(key, {})
            if isinstance(value, Mapping) and value:
                payload = dict(value)
                payload.setdefault(
                    "proof_evidence_status",
                    "PROOF_BODY_GOAL_CONTEXT_NOT_PROOF_EVIDENCE",
                )
                payload.setdefault("proof_evidence_boundary", KERNEL_PROOF_BOUNDARY)
                return payload
    binder_names = _first_nonempty_str_tuple_from_sources(
        sources,
        (
            "source_to_bridge_premise_goal_binder_names",
            "proof_body_goal_binder_names",
        ),
    )
    conclusion = _first_nonempty_string_from_sources(
        sources,
        (
            "source_to_bridge_premise_goal_conclusion",
            "proof_body_goal_conclusion",
        ),
    )
    if not binder_names and not conclusion:
        return {}
    return {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyGoalContext",
        "binder_names": list(binder_names),
        "hypothesis_rows": [],
        "conclusion": conclusion,
        "proof_evidence_status": "PROOF_BODY_GOAL_CONTEXT_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _proof_body_goal_binder_names_from_sources(
    *sources: Mapping[str, Any],
    proof_body_goal_context: Mapping[str, object],
) -> tuple[str, ...]:
    direct = _first_nonempty_str_tuple_from_sources(
        sources,
        (
            "source_to_bridge_premise_goal_binder_names",
            "proof_body_goal_binder_names",
        ),
    )
    if direct:
        return direct
    return _str_tuple(proof_body_goal_context.get("binder_names", []))


def _proof_body_goal_conclusion_from_sources(
    *sources: Mapping[str, Any],
    proof_body_goal_context: Mapping[str, object],
) -> str:
    direct = _first_nonempty_string_from_sources(
        sources,
        (
            "source_to_bridge_premise_goal_conclusion",
            "proof_body_goal_conclusion",
        ),
    )
    if direct:
        return direct
    return str(proof_body_goal_context.get("conclusion", "") or "")


def _premise_target_uses_proof_body_goal_context(
    *,
    premise_target_source: str,
    premise_target_type: str,
    proof_body_goal_conclusion: str,
) -> bool:
    source = str(premise_target_source or "").strip()
    if source in {
        "proof_body_goal_conclusion",
        "source_to_bridge_premise_goal_conclusion",
    }:
        return True
    target = re.sub(r"\s+", " ", str(premise_target_type or "").strip())
    conclusion = re.sub(r"\s+", " ", str(proof_body_goal_conclusion or "").strip())
    return bool(target and conclusion and target == conclusion)


def _proof_body_goal_hypothesis_rows(
    proof_body_goal_context: Mapping[str, object],
) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for item in proof_body_goal_context.get("hypothesis_rows", []) or []:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("binder_name", "") or "").strip()
        if not name:
            continue
        rows.append(
            {
                "name": name,
                "type": str(item.get("binder_type", "") or "").strip(),
            }
        )
    seen = {_normalize_premise_identifier(row["name"]) for row in rows}
    for name in _str_tuple(proof_body_goal_context.get("binder_names", [])):
        key = _normalize_premise_identifier(name)
        if key and key not in seen:
            rows.append({"name": name, "type": ""})
            seen.add(key)
    return tuple(rows)


def _proof_body_goal_semantic_dependency_requirements(
    *,
    proof_body_goal_context: Mapping[str, object],
    proof_body_goal_binder_names: tuple[str, ...],
    proof_body_goal_conclusion: str,
) -> tuple[str, ...]:
    rows = _proof_body_goal_hypothesis_rows(proof_body_goal_context)
    if not rows and proof_body_goal_binder_names:
        rows = tuple({"name": name, "type": ""} for name in proof_body_goal_binder_names)
    requirements: list[str] = []
    if proof_body_goal_conclusion:
        requirements.append(
            "derive the premise target from the reached Lean proof-body goal conclusion: "
            + proof_body_goal_conclusion[:180]
        )
    for row in rows:
        name = row["name"]
        binder_type = row["type"]
        if binder_type:
            requirements.append(
                f"use reached proof-body goal binder {name} : {binder_type} as a source semantic anchor"
            )
        else:
            requirements.append(
                f"use reached proof-body goal binder {name} as a source semantic anchor"
            )
    return tuple(dict.fromkeys(requirements))


def _proof_body_goal_semantic_anchor_binders(
    *,
    proof_body_goal_context: Mapping[str, object],
    proof_body_goal_binder_names: tuple[str, ...],
    source_binders: tuple[dict[str, object], ...],
    context: Mapping[str, Any] | None = None,
) -> tuple[dict[str, object], ...]:
    source_by_name = {
        _normalize_premise_identifier(str(binder.get("name", "") or "")): dict(binder)
        for binder in source_binders
        if str(binder.get("name", "") or "").strip()
    }
    rows = list(_proof_body_goal_hypothesis_rows(proof_body_goal_context))
    if not rows and proof_body_goal_binder_names:
        rows = [{"name": name, "type": ""} for name in proof_body_goal_binder_names]
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in rows:
        name = row["name"]
        key = _normalize_premise_identifier(name)
        if not key or key in seen:
            continue
        seen.add(key)
        if key in source_by_name:
            result.append(source_by_name[key])
            continue
        binder_type = row["type"]
        result.append(
            {
                "name": name,
                "type": binder_type,
                "role": _source_binder_role(
                    name=name,
                    binder_type=binder_type,
                    context=context,
                ),
            }
        )
    return tuple(result)


def _first_nonempty_str_tuple_from_sources(
    sources: Sequence[Mapping[str, Any]],
    keys: Sequence[str],
) -> tuple[str, ...]:
    for source in sources:
        for key in keys:
            values = _str_tuple(source.get(key, []))
            if values:
                return values
    return ()


def _first_nonempty_string_from_sources(
    sources: Sequence[Mapping[str, Any]],
    keys: Sequence[str],
) -> str:
    for source in sources:
        for key in keys:
            value = str(source.get(key, "") or "").strip()
            if value:
                return value
    return ""


def _candidate_source_from_candidate_mapping(
    candidate: Mapping[str, Any],
    *,
    premise_name: str,
) -> str:
    requested_premises = _str_tuple(
        candidate.get("premise_names", [])
        or candidate.get("source_to_bridge_premise_names", [])
    )
    requested_premise = str(candidate.get("premise_name", "") or "").strip()
    premise = str(premise_name or "").strip()
    if premise:
        if requested_premises and premise not in requested_premises:
            return ""
        if requested_premise and requested_premise != premise:
            return ""
    for key in (
        "premise_derivation_candidate_lean_source",
        "premise_derivation_candidate",
        "lean_statement_sketch",
        "candidate_lean_source",
    ):
        source = str(candidate.get(key, "") or "")
        if source.strip():
            return source
    nested = candidate.get("source_to_bridge_premise_derivation_candidates", [])
    if isinstance(nested, Sequence) and not isinstance(nested, (str, bytes)):
        for item in nested:
            if not isinstance(item, Mapping):
                continue
            source = _candidate_source_from_candidate_mapping(
                item,
                premise_name=premise,
            )
            if source:
                return source
    return ""


def _requested_premise_candidate_declaration_name(
    *,
    row: Mapping[str, Any],
    candidate_request: Mapping[str, Any],
    default: str,
) -> str:
    for value in (
        row.get("premise_candidate_declaration_name", ""),
        row.get("source_to_bridge_premise_candidate_declaration_name", ""),
        candidate_request.get("premise_candidate_declaration_name", ""),
    ):
        text = str(value or "").strip()
        if _is_safe_lean_declaration_identifier(text):
            return text
    return default


def _source_binding_contract_present(
    *,
    row: Mapping[str, Any],
    candidate_request: Mapping[str, Any],
    grouped_candidate_request: Mapping[str, Any],
    candidate_request_id: str,
    grouped_candidate_request_id: str,
) -> bool:
    if candidate_request_id or grouped_candidate_request_id:
        return True
    if candidate_request or grouped_candidate_request:
        return True
    for key in (
        "exact_source_theorem_binders",
        "premise_semantic_anchor_binders",
        "premise_semantic_anchor_binder_names",
        "required_semantic_anchor_reference_names",
        "adapter_object_names_requiring_source_instantiation",
    ):
        if row.get(key) not in (None, "", [], {}):
            return True
    return False


def _is_safe_lean_declaration_identifier(value: str) -> bool:
    text = str(value or "").strip()
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_'.]*", text))


def _source_context_from_candidate(
    *,
    source_candidate_artifact_path: str,
    adapter_candidate_artifact_path: str = "",
    target_declaration: str,
    adapter_declaration_name: str,
) -> dict[str, Any]:
    raw_path = str(source_candidate_artifact_path or "").strip()
    if not raw_path:
        return {
            "status": "SOURCE_CANDIDATE_ARTIFACT_MISSING_FROM_WORK_ORDER",
            "source_theorem_signature": (),
            "adapter_signature": (),
        }
    path = Path(raw_path)
    if not path.exists():
        return {
            "status": "SOURCE_CANDIDATE_ARTIFACT_PATH_NOT_FOUND",
            "source_theorem_signature": (),
            "adapter_signature": (),
        }
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as exc:
        return {
            "status": f"SOURCE_CANDIDATE_ARTIFACT_READ_FAILED:{type(exc).__name__}",
            "source_theorem_signature": (),
            "adapter_signature": (),
        }
    source_signature = _extract_declaration_signature(
        source,
        target_declaration,
    )
    adapter_sources: list[str] = []
    adapter_raw_path = str(adapter_candidate_artifact_path or "").strip()
    if adapter_raw_path:
        adapter_path = Path(adapter_raw_path)
        if adapter_path.exists():
            try:
                adapter_sources.append(adapter_path.read_text(encoding="utf-8"))
            except Exception:
                pass
    adapter_sources.append(source)
    adapter_signature: tuple[str, ...] = ()
    for adapter_source in adapter_sources:
        adapter_signature = _extract_declaration_signature(
            adapter_source,
            adapter_declaration_name,
        )
        if adapter_signature:
            break
    if source_signature and adapter_signature:
        status = "SOURCE_AND_ADAPTER_SIGNATURES_EXTRACTED"
    elif source_signature:
        status = "SOURCE_THEOREM_SIGNATURE_EXTRACTED_ADAPTER_SIGNATURE_MISSING"
    elif adapter_signature:
        status = "ADAPTER_SIGNATURE_EXTRACTED_SOURCE_THEOREM_SIGNATURE_MISSING"
    else:
        status = "SOURCE_CANDIDATE_SIGNATURES_NOT_FOUND"
    return {
        "status": status,
        "source_theorem_signature": source_signature,
        "adapter_signature": adapter_signature,
    }


def _extract_declaration_signature(source: str, declaration_name: str) -> tuple[str, ...]:
    declaration = str(declaration_name or "").strip()
    if not declaration:
        return ()
    lines = source.splitlines()
    start = -1
    pattern = re.compile(rf"^\s*(?:theorem|lemma|def)\s+{re.escape(declaration)}\b")
    for idx, line in enumerate(lines):
        if pattern.search(line):
            start = idx
            break
    if start < 0:
        return ()
    excerpt: list[str] = []
    for line in lines[start : start + 40]:
        stripped = line.rstrip()
        excerpt.append(stripped)
        if re.search(r"\s:=\s*(?:by)?\s*$", stripped):
            break
    return tuple(line for line in excerpt if line.strip())


def _adapter_premise_target_from_signature(
    *,
    adapter_signature: tuple[str, ...],
    premise_name: str,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    wanted = _normalize_premise_identifier(premise_name)
    if not wanted:
        return {
            "status": "PREMISE_NAME_MISSING",
            "context_lines": (),
            "premise_type": "",
            "matched_premise_binder": "",
        }
    context_lines: list[str] = []
    premise_type = ""
    matched_binder = ""
    for idx, line in enumerate(adapter_signature):
        stripped = line.strip()
        if idx == 0 and stripped.startswith(("theorem ", "lemma ")):
            continue
        binder = _parse_single_named_binder(stripped)
        if binder:
            name, target = binder
            if _normalize_premise_identifier(name) == wanted:
                premise_type = target
                matched_binder = f"({name} : {target})"
                continue
            if (
                _normalize_premise_identifier(name)
                in _source_to_bridge_policy_premise_aliases_normalized(
                    context=context,
                )
            ):
                continue
        if stripped.endswith(":="):
            continue
        if stripped.startswith(("(", "[", "{")):
            context_lines.append(line)
    status = (
        "ADAPTER_PREMISE_TARGET_EXTRACTED"
        if premise_type
        else "ADAPTER_PREMISE_TARGET_NOT_FOUND"
    )
    return {
        "status": status,
        "context_lines": tuple(context_lines),
        "premise_type": premise_type,
        "matched_premise_binder": matched_binder,
    }


def _adapter_instantiation_group_id(
    *,
    row: Mapping[str, Any],
    target_declaration: str,
    adapter_declaration_name: str,
    source_context: Mapping[str, Any],
) -> str:
    explicit = str(row.get("adapter_instantiation_group_id", "") or "").strip()
    if explicit:
        return explicit
    seed = [
        row.get("source_adapter_work_order_id", ""),
        row.get("source_adapter_check_id", ""),
        target_declaration,
        adapter_declaration_name,
        row.get("source_candidate_artifact_path", ""),
        row.get("adapter_candidate_artifact_path", ""),
        *list(source_context.get("source_theorem_signature", ()) or ())[:12],
        *list(source_context.get("adapter_signature", ()) or ())[:20],
    ]
    return "source_to_bridge_adapter_instantiation_group:" + stable_hash(seed)[:20]


def _parse_single_named_binder(line: str) -> tuple[str, str] | None:
    text = line.strip()
    if text.endswith(":"):
        text = text[:-1].rstrip()
    if not (text.startswith("(") and text.endswith(")")):
        return None
    inner = text[1:-1].strip()
    if ":" not in inner:
        return None
    name, target = inner.split(":", 1)
    name = name.strip()
    target = target.strip()
    if not name or " " in name or not target:
        return None
    return name, target


def _normalize_premise_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _source_to_bridge_policy_premise_aliases_normalized(
    *,
    context: Mapping[str, Any] | None = None,
) -> set[str]:
    return {
        normalized
        for alias in exact_semantic_definition_source_to_bridge_premise_binder_aliases(
            context=context,
        )
        if (normalized := _normalize_premise_identifier(alias))
    }



def _explicit_premise_semantic_dependency_requirements(
    *sources: Mapping[str, Any],
) -> tuple[str, ...]:
    requirements: list[str] = []
    for source in sources:
        for value in _str_tuple(
            source.get("premise_semantic_dependency_requirements", [])
        ):
            if value not in requirements:
                requirements.append(value)
    return tuple(requirements)


def _source_to_bridge_policy_rows(
    *,
    premise_name: str,
    premise_target_type: str,
    context: Mapping[str, Any] | None = None,
) -> tuple[ExactSemanticDefinitionPlaceholderPolicy, ...]:
    text = f"{premise_name} {premise_target_type}"
    compact_text = compact_exact_semantic_placeholder_key(text)
    lowered_text = text.lower()
    rows: list[ExactSemanticDefinitionPlaceholderPolicy] = []
    seen_policy_ids: set[str] = set()
    for policy in exact_semantic_definition_placeholder_policies_for_mapping(
        context,
    ):
        keys = (
            policy.placeholder_key,
            *policy.placeholder_aliases,
            *policy.source_lookup_aliases,
            *policy.source_to_bridge_premise_aliases,
        )
        matched = False
        for key in keys:
            raw_key = str(key or "").strip()
            compact_key = compact_exact_semantic_placeholder_key(raw_key)
            if compact_key and compact_key in compact_text:
                matched = True
                break
            if raw_key and raw_key.lower() in lowered_text:
                matched = True
                break
        if not matched or policy.policy_id in seen_policy_ids:
            continue
        seen_policy_ids.add(policy.policy_id)
        rows.append(policy)
    return tuple(rows)


def _source_to_bridge_policy_dependency_requirements(
    *,
    premise_name: str,
    premise_target_type: str,
    context: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    requirements: list[str] = []
    for policy in _source_to_bridge_policy_rows(
        premise_name=premise_name,
        premise_target_type=premise_target_type,
        context=context,
    ):
        for requirement in policy.source_to_bridge_dependency_requirements:
            if requirement not in requirements:
                requirements.append(requirement)
    return tuple(requirements)


def _source_to_bridge_policy_context(
    *,
    premise_name: str,
    premise_target_type: str,
    context: Mapping[str, Any] | None = None,
) -> dict[str, tuple[str, ...]]:
    policy_rows = _source_to_bridge_policy_rows(
        premise_name=premise_name,
        premise_target_type=premise_target_type,
        context=context,
    )
    dependency_requirements: list[str] = []
    required_anchor_names: list[str] = []
    policy_ids: list[str] = []
    policy_scopes: list[str] = []
    for policy in policy_rows:
        policy_ids.append(policy.policy_id)
        policy_scopes.append(policy.policy_scope)
        for requirement in policy.source_to_bridge_dependency_requirements:
            if requirement not in dependency_requirements:
                dependency_requirements.append(requirement)
        for anchor_name in (
            policy.source_to_bridge_required_anchor_names
            or policy.required_anchor_names
        ):
            if anchor_name not in required_anchor_names:
                required_anchor_names.append(anchor_name)
    return {
        "source_to_bridge_policy_pack_ids": (
            tuple(
                pack.policy_pack_id
                for pack in exact_semantic_definition_policy_packs_for_mapping(
                    context,
                )
            )
            if policy_rows
            else ()
        ),
        "source_to_bridge_policy_ids": tuple(dict.fromkeys(policy_ids)),
        "source_to_bridge_policy_scopes": tuple(dict.fromkeys(policy_scopes)),
        "source_to_bridge_policy_required_anchor_names": tuple(
            required_anchor_names
        ),
        "source_to_bridge_policy_dependency_requirements": tuple(
            dependency_requirements
        ),
    }


def _source_to_bridge_policy_required_anchor_names(
    *,
    premise_name: str,
    premise_target_type: str,
    context: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    anchor_names: list[str] = []
    for policy in _source_to_bridge_policy_rows(
        premise_name=premise_name,
        premise_target_type=premise_target_type,
        context=context,
    ):
        values = (
            policy.source_to_bridge_required_anchor_names
            or policy.required_anchor_names
        )
        for value in values:
            if value not in anchor_names:
                anchor_names.append(value)
    return tuple(anchor_names)


def _source_to_bridge_policy_anchor_role(
    name: str,
    *,
    context: Mapping[str, Any] | None = None,
) -> str:
    normalized = compact_exact_semantic_placeholder_key(name)
    if not normalized:
        return ""
    for policy in exact_semantic_definition_placeholder_policies_for_mapping(
        context,
    ):
        for key, role in policy.source_anchor_roles.items():
            if compact_exact_semantic_placeholder_key(key) == normalized:
                return str(role or "")
    return ""


def _premise_semantic_dependency_requirements(
    *,
    premise_name: str,
    premise_target_type: str,
    source_signature: tuple[str, ...],
    context: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Infer source-to-bridge semantic dependencies for the next LLM/prover pass.

    These rows are routing hints. They are not proof evidence and cannot close a
    premise without a later local Lean/AXLE check of a non-vacuous derivation.
    """

    target = re.sub(r"\s+", " ", str(premise_target_type or "").strip())
    requirements = list(
        _source_to_bridge_policy_dependency_requirements(
            premise_name=premise_name,
            premise_target_type=target,
            context=context,
        )
    )
    if not requirements and target:
        requirements.append(
            "formalize exact source-to-bridge definitions for the identifiers in: "
            + target[:180]
        )
    source_text = "\n".join(source_signature)
    for anchor_name in _source_to_bridge_policy_required_anchor_names(
        premise_name=premise_name,
        premise_target_type=target,
        context=context,
    ):
        if re.search(rf"\b{re.escape(anchor_name)}\b", source_text):
            requirements.append(
                "use the exact source "
                + anchor_name
                + " binder as a semantic anchor for the policy-driven "
                + "source-to-bridge derivation"
            )
    return tuple(dict.fromkeys(requirements))


def _export_runtime_learning_rows(
    *,
    rows: list[SourceToBridgePremiseDerivationCheckRow],
    out_dir: Path,
    question_id: str,
    queue_path: Path,
    adapter_object_semantic_definition_work_orders: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    learning_rows: list[dict[str, Any]] = []
    grouped_requests_by_group_id = {
        str(row.get("adapter_instantiation_group_id", "") or ""): row
        for row in _grouped_premise_derivation_candidate_request_rows(
            rows=rows,
            queue_path=queue_path,
        )
        if str(row.get("adapter_instantiation_group_id", "") or "")
    }
    for row in rows:
        payload = asdict(row)
        candidate_request = _premise_derivation_candidate_request_row(
            row,
            queue_path=queue_path,
        )
        candidate_request_data = candidate_request or {}
        grouped_candidate_request = grouped_requests_by_group_id.get(
            row.adapter_instantiation_group_id,
            {},
        )
        required_bridge_premise_names = list(
            row.required_bridge_premise_names_for_shared_instantiation
            or _str_tuple(
                candidate_request_data.get(
                    "required_bridge_premise_names_for_shared_instantiation",
                    [],
                )
            )
            or _str_tuple(
                grouped_candidate_request.get(
                    "required_bridge_premise_names_for_shared_instantiation",
                    [],
                )
            )
            or ((row.premise_name,) if row.premise_name else ())
        )
        shared_instantiation_contract = str(
            row.shared_adapter_instantiation_contract
            or candidate_request_data.get("shared_adapter_instantiation_contract", "")
            or grouped_candidate_request.get("shared_adapter_instantiation_contract", "")
            or ""
        )
        adapter_object_names = list(
            row.adapter_object_names_requiring_source_instantiation
            or _str_tuple(
                candidate_request_data.get(
                    "adapter_object_names_requiring_source_instantiation",
                    [],
                )
            )
            or _str_tuple(
                grouped_candidate_request.get(
                    "adapter_object_names_requiring_source_instantiation",
                    [],
                )
            )
        )
        required_semantic_anchor_names = list(
            _str_tuple(
                candidate_request_data.get("required_semantic_anchor_reference_names", [])
            )
            or _str_tuple(
                grouped_candidate_request.get(
                    "required_semantic_anchor_reference_names",
                    [],
                )
            )
            or row.premise_semantic_anchor_binder_names
        )
        source_candidate_request = dict(
            row.source_to_bridge_premise_derivation_candidate_request
        )
        learning_rows.append(
            {
                "schema_version": 1,
                "question_id": row.question_id or str(question_id or ""),
                "question_title": row.question_title,
                "learning_task": "source_to_bridge_premise_derivation_feedback",
                "target_theorem_name": row.target_theorem_name,
                "target_lean_declaration": row.target_lean_declaration,
                "target_ids": list(row.target_ids),
                "target_theorem_goal_ids": list(row.target_theorem_goal_ids),
                "source_adapter_check_id": row.source_adapter_check_id,
                "source_adapter_work_order_id": row.source_adapter_work_order_id,
                "work_order_id": row.work_order_id,
                "source_candidate_artifact_path": row.source_candidate_artifact_path,
                "adapter_candidate_artifact_path": row.adapter_candidate_artifact_path,
                "proof_body_signature_probe_artifact_path": (
                    row.proof_body_signature_probe_artifact_path
                ),
                "source_theorem_signature_probe_artifact_path": (
                    row.source_theorem_signature_probe_artifact_path
                ),
                "signature_probe_artifact_path": (
                    row.source_theorem_signature_probe_artifact_path
                    or row.proof_body_signature_probe_artifact_path
                ),
                "premise_name": row.premise_name,
                "required_derivation": row.required_derivation,
                "forbidden_as_adapter_assumption": row.forbidden_as_adapter_assumption,
                "premise_derivation_kernel_verified": (
                    row.premise_derivation_kernel_verified
                ),
                "source_theorem_kernel_verified": False,
                "premise_candidate_references_semantic_anchor": (
                    row.premise_candidate_references_semantic_anchor
                ),
                "premise_candidate_uninstantiated_adapter_object_binders": list(
                    row.premise_candidate_uninstantiated_adapter_object_binders
                ),
                "missing_premise_semantic_anchor_binder_names": list(
                    row.missing_premise_semantic_anchor_binder_names
                ),
                "source_context_status": row.source_context_status,
                "source_theorem_signature_excerpt": list(
                    row.source_theorem_signature_excerpt
                ),
                "adapter_signature_excerpt": list(row.adapter_signature_excerpt),
                "premise_target_status": row.premise_target_status,
                "premise_target_matched_binder": row.premise_target_matched_binder,
                "premise_target_type": row.premise_target_type,
                "premise_target_source": row.premise_target_source,
                "adapter_instantiation_group_id": row.adapter_instantiation_group_id,
                "required_bridge_premise_names_for_shared_instantiation": list(
                    required_bridge_premise_names
                ),
                "shared_adapter_instantiation_contract": (
                    shared_instantiation_contract
                ),
                "adapter_object_names_requiring_source_instantiation": list(
                    adapter_object_names
                ),
                "premise_derivation_gap_kind": row.premise_derivation_gap_kind,
                "premise_derivation_gap_summary": row.premise_derivation_gap_summary,
                "premise_semantic_dependency_status": (
                    row.premise_semantic_dependency_status
                ),
                "premise_semantic_dependency_source": (
                    row.premise_semantic_dependency_source
                ),
                "premise_semantic_dependency_requirements": list(
                    row.premise_semantic_dependency_requirements
                ),
                "source_to_bridge_policy_pack_ids": list(
                    row.source_to_bridge_policy_pack_ids
                ),
                "source_to_bridge_policy_ids": list(
                    row.source_to_bridge_policy_ids
                ),
                "source_to_bridge_policy_scopes": list(
                    row.source_to_bridge_policy_scopes
                ),
                "source_to_bridge_policy_required_anchor_names": list(
                    row.source_to_bridge_policy_required_anchor_names
                ),
                "source_to_bridge_policy_dependency_requirements": list(
                    row.source_to_bridge_policy_dependency_requirements
                ),
                "source_to_bridge_premise_derivation_candidate_request_id": (
                    str(candidate_request.get("candidate_request_id", ""))
                    if candidate_request
                    else ""
                ),
                "source_to_bridge_premise_derivation_candidate_request": (
                    candidate_request or {}
                ),
                "source_to_bridge_grouped_premise_derivation_candidate_request_id": (
                    str(grouped_candidate_request.get("grouped_candidate_request_id", ""))
                    if grouped_candidate_request
                    else ""
                ),
                "source_to_bridge_grouped_premise_derivation_candidate_request": (
                    grouped_candidate_request or {}
                ),
                "source_to_bridge_premise_derivation_source_candidate_request_id": (
                    row.source_to_bridge_premise_derivation_candidate_request_id
                ),
                "source_to_bridge_premise_derivation_source_candidate_request": (
                    source_candidate_request
                ),
                "exact_source_theorem_binders": list(
                    row.exact_source_theorem_binders
                ),
                "premise_semantic_anchor_binders": list(
                    row.premise_semantic_anchor_binders
                ),
                "premise_semantic_anchor_binder_names": list(
                    row.premise_semantic_anchor_binder_names
                ),
                "required_semantic_anchor_reference_names": list(
                    required_semantic_anchor_names
                ),
                "kernel_verified_source_to_bridge_premise_derivation_ids": (
                    [row.premise_derivation_check_id]
                    if row.premise_derivation_kernel_verified
                    else []
                ),
                "failure_classification": row.failure_classification,
                "semantic_alignment_constraints": list(
                    row.semantic_alignment_constraints
                ),
                "semantic_alignment_blockers": list(row.semantic_alignment_blockers),
                "source_theorem_kernel_evidence_eligible": (
                    row.source_theorem_kernel_evidence_eligible
                ),
                "proof_body_goal_excerpt": list(row.proof_body_goal_excerpt),
                "proof_body_goal_context": row.proof_body_goal_context,
                "proof_body_goal_binder_names": list(
                    row.proof_body_goal_binder_names
                ),
                "proof_body_goal_conclusion": row.proof_body_goal_conclusion,
                "source_to_bridge_premise_goal_context": row.proof_body_goal_context,
                "source_to_bridge_premise_goal_binder_names": list(
                    row.proof_body_goal_binder_names
                ),
                "source_to_bridge_premise_goal_conclusion": (
                    row.proof_body_goal_conclusion
                ),
                "proof_body_attempt_summaries": list(
                    row.proof_body_attempt_summaries
                ),
                "proof_body_attempt_count": row.proof_body_attempt_count,
                "proof_body_gate_status": row.proof_body_gate_status,
                "source_theorem_exact_proof_body_reached": (
                    row.source_theorem_exact_proof_body_reached
                ),
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair": (
                    row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
                ),
                "source_theorem_exact_proof_body_gate_open_target_names": list(
                    row.source_theorem_exact_proof_body_gate_open_target_names
                ),
                "runtime_queue_status": (
                    "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_KERNEL_VERIFIED"
                    if row.premise_derivation_kernel_verified
                    else "PENDING_SOURCE_TO_BRIDGE_PREMISE_DERIVATION"
                ),
                "input_summary": payload,
                "target_behavior": (
                    "If premise_derivation_kernel_verified=true, reroute the "
                    "adapter bridge or exact source proof-body search with this "
                    "premise derivation available. Do not treat this row as full "
                    "source theorem proof."
                ),
                "acceptance_gate": (
                    "Full source theorem evidence requires a later local Lean/AXLE "
                    "run that verifies the exact source theorem declaration itself."
                ),
                "proof_evidence_status": row.proof_evidence_status,
                "proof_evidence_boundary": row.proof_evidence_boundary,
                "boundary": BOUNDARY,
            }
        )
    grouped_learning_rows: list[dict[str, Any]] = []
    for grouped_request in grouped_requests_by_group_id.values():
        premise_names = [
            str(value)
            for value in grouped_request.get("premise_names", []) or []
            if str(value).strip()
        ]
        if len(premise_names) <= 1:
            continue
        grouped_adapter_objects = list(
            grouped_request.get(
                "adapter_object_names_requiring_source_instantiation",
                [],
            )
            or []
        )
        per_premise_requests = [
            item
            for item in grouped_request.get("per_premise_candidate_requests", []) or []
            if isinstance(item, Mapping)
        ]
        grouped_request_uses_goal_context = bool(per_premise_requests) and all(
            _premise_target_uses_proof_body_goal_context(
                premise_target_source=str(
                    item.get("premise_target_source", "") or ""
                ),
                premise_target_type=str(item.get("premise_target_type", "") or ""),
                proof_body_goal_conclusion=str(
                    item.get("proof_body_goal_conclusion", "")
                    or grouped_request.get("proof_body_goal_conclusion", "")
                    or ""
                ),
            )
            for item in per_premise_requests
        )
        grouped_target_behavior = (
            "Generate one shared source-to-bridge premise derivation candidate "
            "that derives every listed premise name from exact source-theorem "
            "binders and the reached proof_body_goal_context anchors without "
            "assuming those premises, goal binders, or target conclusions. This "
            "grouped request is not proof evidence; only local Lean/AXLE kernel "
            "verification of each premise derivation can promote it."
            if grouped_request_uses_goal_context and not grouped_adapter_objects
            else (
                "Generate one shared source-to-bridge premise derivation candidate "
                "that defines the adapter objects once from exact source-theorem "
                "binders and proves every listed premise name without assuming those "
                "premises. This grouped request is not proof evidence; only local "
                "Lean/AXLE kernel verification of each premise derivation can promote it."
            )
        )
        grouped_learning_row = {
            "schema_version": 1,
            "question_id": str(grouped_request.get("question_id", "") or question_id or ""),
            "question_title": str(grouped_request.get("question_title", "") or ""),
            "learning_task": "source_to_bridge_grouped_premise_derivation_candidate_request",
            "target_theorem_name": str(
                grouped_request.get("target_theorem_name", "") or ""
            ),
            "target_lean_declaration": str(
                grouped_request.get("target_lean_declaration", "") or ""
            ),
            "target_theorem_goal_ids": list(
                grouped_request.get("target_theorem_goal_ids", []) or []
            ),
            "proof_body_signature_probe_artifact_path": str(
                grouped_request.get("proof_body_signature_probe_artifact_path", "")
                or ""
            ),
            "source_theorem_signature_probe_artifact_path": str(
                grouped_request.get(
                    "source_theorem_signature_probe_artifact_path",
                    "",
                )
                or ""
            ),
            "signature_probe_artifact_path": str(
                grouped_request.get("source_theorem_signature_probe_artifact_path", "")
                or grouped_request.get("proof_body_signature_probe_artifact_path", "")
                or grouped_request.get("signature_probe_artifact_path", "")
                or ""
            ),
            "work_order_id": str(
                grouped_request.get("grouped_candidate_request_id", "") or ""
            ),
            "source_to_bridge_grouped_premise_derivation_candidate_request_id": str(
                grouped_request.get("grouped_candidate_request_id", "") or ""
            ),
            "source_to_bridge_grouped_premise_derivation_candidate_request": dict(
                grouped_request
            ),
            "premise_names": premise_names,
            "required_bridge_premise_names_for_shared_instantiation": list(
                grouped_request.get(
                    "required_bridge_premise_names_for_shared_instantiation",
                    [],
                )
                or []
            ),
            "adapter_instantiation_group_id": str(
                grouped_request.get("adapter_instantiation_group_id", "") or ""
            ),
            "shared_adapter_instantiation_contract": str(
                grouped_request.get("shared_adapter_instantiation_contract", "") or ""
            ),
            "adapter_object_names_requiring_source_instantiation": list(
                grouped_adapter_objects
            ),
            "premise_semantic_anchor_binder_names": list(
                grouped_request.get("premise_semantic_anchor_binder_names", []) or []
            ),
            "premise_semantic_anchor_binders": list(
                grouped_request.get("premise_semantic_anchor_binders", []) or []
            ),
            "exact_source_theorem_binders": list(
                grouped_request.get("exact_source_theorem_binders", []) or []
            ),
            "premise_semantic_dependency_requirements": list(
                grouped_request.get("premise_semantic_dependency_requirements", []) or []
            ),
            "semantic_alignment_constraints": list(
                grouped_request.get("semantic_alignment_constraints", []) or []
            ),
            "semantic_alignment_blockers": list(
                grouped_request.get("semantic_alignment_blockers", []) or []
            ),
            "source_theorem_kernel_evidence_eligible": bool(
                grouped_request.get("source_theorem_kernel_evidence_eligible", False)
            ),
            "proof_body_attempt_count": _int_like(
                grouped_request.get("proof_body_attempt_count", 0)
            ),
            "proof_body_gate_status": str(
                grouped_request.get("proof_body_gate_status", "") or ""
            ),
            "source_theorem_exact_proof_body_reached": _bool_like(
                grouped_request.get(
                    "source_theorem_exact_proof_body_reached",
                    False,
                )
            ),
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair": (
                _bool_like(
                    grouped_request.get(
                        "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
                        False,
                    )
                )
            ),
            "source_theorem_exact_proof_body_gate_open_target_names": list(
                _str_tuple(
                    grouped_request.get(
                        "source_theorem_exact_proof_body_gate_open_target_names",
                        [],
                    )
                )
            ),
            "proof_body_goal_excerpt": list(
                grouped_request.get("proof_body_goal_excerpt", []) or []
            ),
            "proof_body_goal_context": dict(
                grouped_request.get("proof_body_goal_context", {}) or {}
            ),
            "proof_body_goal_binder_names": list(
                grouped_request.get("proof_body_goal_binder_names", []) or []
            ),
            "proof_body_goal_conclusion": str(
                grouped_request.get("proof_body_goal_conclusion", "") or ""
            ),
            "source_to_bridge_premise_goal_context": dict(
                grouped_request.get("source_to_bridge_premise_goal_context", {})
                or grouped_request.get("proof_body_goal_context", {})
                or {}
            ),
            "source_to_bridge_premise_goal_binder_names": list(
                grouped_request.get("source_to_bridge_premise_goal_binder_names", [])
                or grouped_request.get("proof_body_goal_binder_names", [])
                or []
            ),
            "source_to_bridge_premise_goal_conclusion": str(
                grouped_request.get("source_to_bridge_premise_goal_conclusion", "")
                or grouped_request.get("proof_body_goal_conclusion", "")
                or ""
            ),
            "proof_body_attempt_summaries": list(
                grouped_request.get("proof_body_attempt_summaries", []) or []
            ),
            "runtime_queue_status": "PENDING_GROUPED_SOURCE_TO_BRIDGE_PREMISE_DERIVATION",
            "input_summary": dict(grouped_request),
            "target_behavior": grouped_target_behavior,
            "acceptance_gate": (
                "The grouped Lean source must local Lean/AXLE kernel verify each "
                "listed premise derivation before the adapter or exact source theorem "
                "proof body can use it."
            ),
            "proof_evidence_status": str(
                grouped_request.get("proof_evidence_status", "")
                or "SOURCE_TO_BRIDGE_GROUPED_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
            ),
            "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
            "boundary": BOUNDARY,
        }
        grouped_learning_rows.append(grouped_learning_row)
    learning_rows.extend(grouped_learning_rows)
    for item in adapter_object_semantic_definition_work_orders or []:
        learning_rows.append(dict(item))
    rows_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(rows_path, learning_rows)
    export_manifest = {
        "schema_version": 1,
        "artifact_kind": (
            "SourceToBridgePremiseDerivationRuntimeLearningExportManifest"
        ),
        "source_queue_jsonl": str(queue_path),
        "runtime_learning_rows_jsonl": str(rows_path),
        "n_learning_rows": len(learning_rows),
        "n_source_to_bridge_adapter_object_semantic_definition_work_orders": len(
            adapter_object_semantic_definition_work_orders or []
        ),
        "n_grouped_premise_derivation_learning_rows": len(grouped_learning_rows),
        "proof_body_gate_statuses": sorted(
            {
                row.proof_body_gate_status
                for row in rows
                if row.proof_body_gate_status
            }
        ),
        "n_source_theorem_exact_proof_body_gate_open_for_kernel_repair": sum(
            1
            for row in rows
            if row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
        ),
        "n_proof_body_signature_probe_artifact_rows": sum(
            1 for row in rows if row.proof_body_signature_probe_artifact_path
        ),
        "n_proof_body_goal_context_rows": sum(
            1
            for row in rows
            if row.proof_body_goal_binder_names or row.proof_body_goal_conclusion
        ),
        "proof_body_goal_context_binder_names": sorted(
            {
                binder_name
                for row in rows
                for binder_name in row.proof_body_goal_binder_names
                if binder_name
            }
        ),
        "proof_body_goal_context_conclusions": [
            row.proof_body_goal_conclusion
            for row in rows
            if row.proof_body_goal_conclusion
        ][:8],
        "proof_body_signature_probe_artifact_paths": sorted(
            {
                row.proof_body_signature_probe_artifact_path
                for row in rows
                if row.proof_body_signature_probe_artifact_path
            }
        ),
        "source_theorem_exact_proof_body_gate_open_target_names": (
            _proof_body_gate_open_target_names_for_rows(rows)
        ),
        "n_premise_derivation_kernel_verified": sum(
            1 for row in rows if row.premise_derivation_kernel_verified
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": [
            row.premise_derivation_check_id
            for row in rows
            if row.premise_derivation_kernel_verified
        ],
        "source_theorem_kernel_verified": False,
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "boundary": BOUNDARY,
    }
    manifest_path = (
        out_dir
        / "source_to_bridge_premise_derivation_runtime_learning_export_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(export_manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "runtime_learning_rows_jsonl": rows_path,
        "export_manifest_path": manifest_path,
        "export_manifest": export_manifest,
        "n_learning_rows": len(learning_rows),
        "rows": learning_rows,
    }


def _adapter_object_semantic_definition_work_order_rows(
    *,
    rows: list[SourceToBridgePremiseDerivationCheckRow],
    queue_path: Path,
) -> list[dict[str, Any]]:
    def extend_unique(
        payload: dict[str, Any],
        field: str,
        values: Iterable[Any],
    ) -> None:
        current = list(payload.get(field, []) or [])
        seen = {
            json.dumps(value, sort_keys=True, default=str)
            for value in current
        }
        for value in values:
            if value is None:
                continue
            key = json.dumps(value, sort_keys=True, default=str)
            if key in seen:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            current.append(value)
            seen.add(key)
        payload[field] = current

    def merge_work_order(
        existing: dict[str, Any],
        candidate: dict[str, Any],
    ) -> None:
        scalar_fields = (
            "question_id",
            "question_title",
            "target_theorem_name",
            "target_lean_declaration",
            "source_to_bridge_grouped_premise_derivation_candidate_request_id",
            "proof_body_gate_status",
            "proof_body_goal_context",
            "proof_body_goal_conclusion",
            "source_to_bridge_premise_goal_context",
            "source_to_bridge_premise_goal_conclusion",
            "proof_body_signature_probe_artifact_path",
            "source_theorem_signature_probe_artifact_path",
            "signature_probe_artifact_path",
        )
        for field in scalar_fields:
            if not existing.get(field) and candidate.get(field):
                existing[field] = candidate[field]
        for field in (
            "source_theorem_exact_proof_body_reached",
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
        ):
            if not _bool_like(existing.get(field)) and _bool_like(
                candidate.get(field)
            ):
                existing[field] = True
        for field in (
            "target_ids",
            "target_theorem_goal_ids",
            "search_targets",
            "candidate_registered_obligation_ids",
            "kernel_verified_source_theorem_semantic_support_obligation_ids",
            "kernel_verified_source_theorem_semantic_primitive_ids",
            "source_to_bridge_adapter_instantiation_group_ids",
            "source_to_bridge_adapter_object_names_requiring_source_instantiation",
            "required_bridge_premise_names_for_shared_instantiation",
            "source_to_bridge_grouped_premise_derivation_candidate_request_ids",
            "source_to_bridge_grouped_premise_derivation_candidate_requests",
            "exact_source_theorem_binders",
            "premise_semantic_anchor_binders",
            "premise_semantic_anchor_binder_names",
            "premise_semantic_dependency_requirements",
            "semantic_alignment_constraints",
            "semantic_alignment_blockers",
            "exact_goal_shape_obligation_ids",
            "proof_body_goal_binder_names",
            "source_to_bridge_premise_goal_binder_names",
            "source_theorem_exact_proof_body_gate_open_target_names",
            "kernel_verified_theorem_reduction_closure_declarations",
            "verified_theorem_reduction_closure_artifact_paths",
        ):
            extend_unique(existing, field, candidate.get(field, []) or [])
        _merge_candidate_definition_request(
            existing,
            candidate.get("candidate_definition_request", {}),
        )

        existing_summary = existing.setdefault("input_summary", {})
        candidate_summary = dict(candidate.get("input_summary", {}) or {})
        for field in (
            "target_theorem_name",
            "target_lean_declaration",
            "placeholder_symbol",
            "candidate_definition_request",
            "adapter_object_name",
            "source_to_bridge_adapter_instantiation_group_id",
            "work_order_id",
            "proof_body_gate_status",
            "proof_body_goal_context",
            "proof_body_goal_conclusion",
            "source_to_bridge_premise_goal_context",
            "source_to_bridge_premise_goal_conclusion",
            "proof_body_signature_probe_artifact_path",
            "source_theorem_signature_probe_artifact_path",
            "signature_probe_artifact_path",
        ):
            if not existing_summary.get(field) and candidate_summary.get(field):
                existing_summary[field] = candidate_summary[field]
        for field in (
            "source_theorem_exact_proof_body_reached",
            "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
        ):
            if not _bool_like(existing_summary.get(field)) and _bool_like(
                candidate_summary.get(field)
            ):
                existing_summary[field] = True
        for field in (
            "target_ids",
            "source_to_bridge_adapter_instantiation_group_ids",
            "source_to_bridge_grouped_premise_derivation_candidate_request_ids",
            "required_bridge_premise_names_for_shared_instantiation",
            "exact_source_theorem_binders",
            "premise_semantic_anchor_binders",
            "premise_semantic_dependency_requirements",
            "semantic_alignment_blockers",
            "candidate_registered_obligation_ids",
            "proof_body_goal_binder_names",
            "source_to_bridge_premise_goal_binder_names",
            "source_theorem_exact_proof_body_gate_open_target_names",
        ):
            extend_unique(
                existing_summary,
                field,
                candidate_summary.get(field, []) or [],
            )
        _merge_candidate_definition_request(
            existing_summary,
            candidate_summary.get("candidate_definition_request", {}),
        )

    grouped: dict[str, list[SourceToBridgePremiseDerivationCheckRow]] = {}
    for row in rows:
        if row.premise_derivation_kernel_verified:
            continue
        if not row.adapter_object_names_requiring_source_instantiation:
            continue
        group_id = row.adapter_instantiation_group_id or (
            "source_to_bridge_adapter_instantiation_group:"
            + stable_hash([row.work_order_id, row.premise_name])[:20]
        )
        grouped.setdefault(group_id, []).append(row)

    work_orders: list[dict[str, Any]] = []
    work_orders_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for group_id, group_rows in grouped.items():
        if not group_rows:
            continue
        premise_names = tuple(
            dict.fromkeys(
                [
                    *[
                        value
                        for row in group_rows
                        for value in row.required_bridge_premise_names_for_shared_instantiation
                        if value
                    ],
                    *[row.premise_name for row in group_rows if row.premise_name],
                ]
            )
        )
        adapter_objects = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.adapter_object_names_requiring_source_instantiation
                if value
            )
        )
        if not adapter_objects:
            continue
        target_theorem_name = next(
            (row.target_theorem_name for row in group_rows if row.target_theorem_name),
            "",
        )
        target_lean_declaration = next(
            (
                row.target_lean_declaration
                for row in group_rows
                if row.target_lean_declaration
            ),
            target_theorem_name,
        )
        if not target_theorem_name and target_lean_declaration:
            target_theorem_name = target_lean_declaration
        target_goal_ids = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.target_theorem_goal_ids
                if value
            )
        )
        target_ids = tuple(
            dict.fromkeys(
                [
                    *[
                        value
                        for row in group_rows
                        for value in row.target_ids
                        if value
                    ],
                    *target_goal_ids,
                ]
            )
        )
        source_binders = _merge_named_mapping_rows(
            row.exact_source_theorem_binders for row in group_rows
        )
        semantic_anchor_binders = _merge_named_mapping_rows(
            row.premise_semantic_anchor_binders for row in group_rows
        )
        semantic_anchor_names = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.premise_semantic_anchor_binder_names
                if value
            )
        )
        semantic_requirements = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.premise_semantic_dependency_requirements
                if value
            )
        )
        support_ids = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.kernel_verified_source_theorem_semantic_support_obligation_ids
                if value
            )
        )
        exact_goal_shape_obligation_ids = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.exact_goal_shape_obligation_ids
                if value
            )
        )
        closure_declarations = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.kernel_verified_theorem_reduction_closure_declarations
                if value
            )
        )
        closure_artifacts = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.verified_theorem_reduction_closure_artifact_paths
                if value
            )
        )
        proof_body_gate_status = next(
            (row.proof_body_gate_status for row in group_rows if row.proof_body_gate_status),
            "",
        )
        proof_body_goal_context = next(
            (row.proof_body_goal_context for row in group_rows if row.proof_body_goal_context),
            {},
        )
        proof_body_goal_binder_names = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.proof_body_goal_binder_names
                if value
            )
        )
        proof_body_goal_conclusion = next(
            (
                row.proof_body_goal_conclusion
                for row in group_rows
                if row.proof_body_goal_conclusion
            ),
            "",
        )
        source_theorem_exact_proof_body_reached = any(
            row.source_theorem_exact_proof_body_reached for row in group_rows
        )
        source_theorem_exact_proof_body_gate_open_for_kernel_repair = any(
            row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
            for row in group_rows
        )
        proof_body_gate_open_target_names = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                if row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
                for value in (
                    row.source_theorem_exact_proof_body_gate_open_target_names
                    or ((row.target_theorem_name,) if row.target_theorem_name else ())
                )
                if value
            )
        )
        proof_body_signature_probe_artifact_path = next(
            (
                row.proof_body_signature_probe_artifact_path
                for row in group_rows
                if row.proof_body_signature_probe_artifact_path
            ),
            "",
        )
        source_theorem_signature_probe_artifact_path = next(
            (
                row.source_theorem_signature_probe_artifact_path
                for row in group_rows
                if row.source_theorem_signature_probe_artifact_path
            ),
            proof_body_signature_probe_artifact_path,
        )
        shared_contract = next(
            (
                row.shared_adapter_instantiation_contract
                for row in group_rows
                if row.shared_adapter_instantiation_contract
            ),
            "",
        )
        question_id = next((row.question_id for row in group_rows if row.question_id), "")
        question_title = next(
            (row.question_title for row in group_rows if row.question_title),
            "",
        )
        source_grouped_request = next(
            (
                dict(row.source_to_bridge_grouped_premise_derivation_candidate_request)
                for row in group_rows
                if row.source_to_bridge_grouped_premise_derivation_candidate_request
            ),
            {},
        )
        source_grouped_request_id = next(
            (
                row.source_to_bridge_grouped_premise_derivation_candidate_request_id
                for row in group_rows
                if row.source_to_bridge_grouped_premise_derivation_candidate_request_id
            ),
            "",
        )
        grouped_request_id = (
            source_grouped_request_id
            or str(source_grouped_request.get("grouped_candidate_request_id", "") or "")
            or (
                "source_to_bridge_grouped_premise_derivation_candidate_request:"
                + stable_hash([group_id, premise_names, target_lean_declaration])[:20]
            )
        )
        for adapter_object in adapter_objects:
            key = (target_lean_declaration or target_theorem_name, adapter_object)
            work_order_id = (
                "source_to_bridge_adapter_object_semantic_definition_work_order:"
                + stable_hash([target_lean_declaration, adapter_object])[:20]
            )
            semantic_blockers = [
                (
                    f"adapter object {adapter_object!r} must be defined from exact "
                    "source theorem binders before source-to-bridge premise "
                    "derivations can be kernel verified"
                ),
                *([shared_contract] if shared_contract else []),
                *semantic_requirements,
            ]
            search_targets = tuple(
                dict.fromkeys(
                    [
                        adapter_object,
                        target_theorem_name,
                        target_lean_declaration,
                        "source-to-bridge adapter object instantiation",
                        "exact source theorem semantic definition",
                        *premise_names,
                        *semantic_anchor_names,
                    ]
                )
            )
            candidate_definition_request = (
                _adapter_object_candidate_definition_request(
                    placeholder_symbol=adapter_object,
                    target_theorem_name=target_theorem_name,
                    target_lean_declaration=target_lean_declaration,
                    target_ids=target_ids,
                    group_id=group_id,
                    premise_names=premise_names,
                    source_binders=source_binders,
                    semantic_anchor_binders=semantic_anchor_binders,
                    semantic_anchor_names=semantic_anchor_names,
                    semantic_requirements=semantic_requirements,
                    adapter_objects=adapter_objects,
                    proof_body_gate_status=proof_body_gate_status,
                    source_theorem_exact_proof_body_reached=(
                        source_theorem_exact_proof_body_reached
                    ),
                    source_theorem_exact_proof_body_gate_open_for_kernel_repair=(
                        source_theorem_exact_proof_body_gate_open_for_kernel_repair
                    ),
                    source_theorem_exact_proof_body_gate_open_target_names=(
                        proof_body_gate_open_target_names
                    ),
                    proof_body_signature_probe_artifact_path=(
                        proof_body_signature_probe_artifact_path
                    ),
                    source_theorem_signature_probe_artifact_path=(
                        source_theorem_signature_probe_artifact_path
                    ),
                    proof_body_goal_context=proof_body_goal_context,
                    proof_body_goal_binder_names=proof_body_goal_binder_names,
                    proof_body_goal_conclusion=proof_body_goal_conclusion,
                )
            )
            work_orders.append(
                {
                    "schema_version": 1,
                    "artifact_kind": ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_KIND,
                    "learning_task": ADAPTER_OBJECT_SEMANTIC_DEFINITION_LEARNING_TASK,
                    "work_order_id": work_order_id,
                    "source_queue_jsonl": str(queue_path),
                    "source_materialization_seed_id": group_id,
                    "source_theorem_promotion_work_order_id": group_id,
                    "question_id": question_id,
                    "question_title": question_title,
                    "target_theorem_name": target_theorem_name,
                    "target_lean_declaration": target_lean_declaration,
                    "target_ids": list(target_ids),
                    "target_theorem_goal_ids": list(target_goal_ids),
                    "proof_body_gate_status": proof_body_gate_status,
                    "proof_body_goal_context": dict(proof_body_goal_context),
                    "proof_body_goal_binder_names": list(
                        proof_body_goal_binder_names
                    ),
                    "proof_body_goal_conclusion": proof_body_goal_conclusion,
                    "source_to_bridge_premise_goal_context": dict(
                        proof_body_goal_context
                    ),
                    "source_to_bridge_premise_goal_binder_names": list(
                        proof_body_goal_binder_names
                    ),
                    "source_to_bridge_premise_goal_conclusion": (
                        proof_body_goal_conclusion
                    ),
                    "source_theorem_exact_proof_body_reached": (
                        source_theorem_exact_proof_body_reached
                    ),
                    "source_theorem_exact_proof_body_gate_open_for_kernel_repair": (
                        source_theorem_exact_proof_body_gate_open_for_kernel_repair
                    ),
                    "source_theorem_exact_proof_body_gate_open_target_names": list(
                        proof_body_gate_open_target_names
                    ),
                    "proof_body_signature_probe_artifact_path": (
                        proof_body_signature_probe_artifact_path
                    ),
                    "source_theorem_signature_probe_artifact_path": (
                        source_theorem_signature_probe_artifact_path
                    ),
                    "signature_probe_artifact_path": (
                        source_theorem_signature_probe_artifact_path
                        or proof_body_signature_probe_artifact_path
                    ),
                    "placeholder_symbol": adapter_object,
                    "candidate_definition_request": candidate_definition_request,
                    "replacement_strategy": (
                        "instantiate_source_to_bridge_adapter_object_from_exact_source_binders"
                    ),
                    "search_targets": list(search_targets),
                    "candidate_registered_obligation_ids": list(support_ids),
                    "kernel_verified_source_theorem_semantic_support_obligation_ids": (
                        list(support_ids)
                    ),
                    "kernel_verified_source_theorem_semantic_primitive_ids": list(
                        support_ids
                    ),
                    "kernel_verified_source_theorem_semantic_definition_ids": [],
                    "source_to_bridge_adapter_instantiation_group_id": group_id,
                    "source_to_bridge_adapter_instantiation_group_ids": [group_id],
                    "adapter_object_name": adapter_object,
                    "source_to_bridge_adapter_object_names_requiring_source_instantiation": (
                        list(adapter_objects)
                    ),
                    "required_bridge_premise_names_for_shared_instantiation": list(
                        premise_names
                    ),
                    "source_to_bridge_grouped_premise_derivation_candidate_request_id": (
                        grouped_request_id
                    ),
                    "source_to_bridge_grouped_premise_derivation_candidate_request_ids": (
                        [grouped_request_id] if grouped_request_id else []
                    ),
                    "source_to_bridge_grouped_premise_derivation_candidate_request": (
                        source_grouped_request
                    ),
                    "source_to_bridge_grouped_premise_derivation_candidate_requests": (
                        [source_grouped_request] if source_grouped_request else []
                    ),
                    "exact_source_theorem_binders": list(source_binders),
                    "premise_semantic_anchor_binders": list(semantic_anchor_binders),
                    "premise_semantic_anchor_binder_names": list(semantic_anchor_names),
                    "premise_semantic_dependency_requirements": list(
                        semantic_requirements
                    ),
                    "semantic_alignment_constraints": semantic_blockers,
                    "semantic_alignment_blockers": semantic_blockers,
                    "exact_goal_shape_obligation_ids": list(
                        exact_goal_shape_obligation_ids
                    ),
                    "kernel_verified_theorem_reduction_closure_declarations": list(
                        closure_declarations
                    ),
                    "verified_theorem_reduction_closure_artifact_paths": list(
                        closure_artifacts
                    ),
                    "semantic_closure_status": (
                        "SOURCE_TO_BRIDGE_ADAPTER_OBJECT_DEFINITION_OPEN"
                    ),
                    "placeholder_definition_status": (
                        "OPEN_REQUIRES_REVIEWED_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_DEFINITION"
                    ),
                    "source_theorem_ready_for_exact_proof_body": False,
                    "source_theorem_semantic_support_only": True,
                    "source_semantic_alignment_review_required": True,
                    "runtime_queue_status": (
                        "PENDING_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_SEMANTIC_DEFINITION"
                    ),
                    "owner_agent": "Formalizer/ProofEngineer/LeanProver",
                    "action_type": "formalize_reviewed_exact_semantic_definition",
                    "target_behavior": (
                        "Define this source-to-bridge adapter object from the exact "
                        "source theorem binders before retrying grouped premise "
                        "derivations. This is a semantic-definition work order, not "
                        "proof evidence."
                    ),
                    "acceptance_gate": (
                        "A reviewed exact semantic definition for the adapter object "
                        "must pass local Lean/AXLE. Full source theorem evidence still "
                        "requires a later exact source theorem proof-body rerun."
                    ),
                    "proof_evidence_status": (
                        ADAPTER_OBJECT_SEMANTIC_DEFINITION_PROOF_EVIDENCE_STATUS
                    ),
                    "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                    "boundary": BOUNDARY,
                    "input_summary": {
                        "trigger": (
                            "SOURCE_TO_BRIDGE_ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER"
                        ),
                        "work_order_id": work_order_id,
                        "target_theorem_name": target_theorem_name,
                        "target_lean_declaration": target_lean_declaration,
                        "target_ids": list(target_ids),
                        "proof_body_gate_status": proof_body_gate_status,
                        "proof_body_goal_context": dict(proof_body_goal_context),
                        "proof_body_goal_binder_names": list(
                            proof_body_goal_binder_names
                        ),
                        "proof_body_goal_conclusion": proof_body_goal_conclusion,
                        "source_to_bridge_premise_goal_context": dict(
                            proof_body_goal_context
                        ),
                        "source_to_bridge_premise_goal_binder_names": list(
                            proof_body_goal_binder_names
                        ),
                        "source_to_bridge_premise_goal_conclusion": (
                            proof_body_goal_conclusion
                        ),
                        "source_theorem_exact_proof_body_reached": (
                            source_theorem_exact_proof_body_reached
                        ),
                        "source_theorem_exact_proof_body_gate_open_for_kernel_repair": (
                            source_theorem_exact_proof_body_gate_open_for_kernel_repair
                        ),
                        "source_theorem_exact_proof_body_gate_open_target_names": list(
                            proof_body_gate_open_target_names
                        ),
                        "proof_body_signature_probe_artifact_path": (
                            proof_body_signature_probe_artifact_path
                        ),
                        "source_theorem_signature_probe_artifact_path": (
                            source_theorem_signature_probe_artifact_path
                        ),
                        "signature_probe_artifact_path": (
                            source_theorem_signature_probe_artifact_path
                            or proof_body_signature_probe_artifact_path
                        ),
                        "placeholder_symbol": adapter_object,
                        "candidate_definition_request": (
                            candidate_definition_request
                        ),
                        "adapter_object_name": adapter_object,
                        "source_to_bridge_adapter_instantiation_group_id": group_id,
                        "source_to_bridge_adapter_instantiation_group_ids": [
                            group_id
                        ],
                        "source_to_bridge_grouped_premise_derivation_candidate_request_ids": (
                            [grouped_request_id] if grouped_request_id else []
                        ),
                        "required_bridge_premise_names_for_shared_instantiation": (
                            list(premise_names)
                        ),
                        "exact_source_theorem_binders": list(source_binders),
                        "premise_semantic_anchor_binders": list(
                            semantic_anchor_binders
                        ),
                        "premise_semantic_dependency_requirements": list(
                            semantic_requirements
                        ),
                        "semantic_alignment_blockers": semantic_blockers,
                        "candidate_registered_obligation_ids": list(support_ids),
                        "source_theorem_ready_for_exact_proof_body": False,
                        "source_theorem_semantic_support_only": True,
                    },
                }
            )
            existing = work_orders_by_key.get(key)
            if existing is not None:
                merge_work_order(existing, work_orders[-1])
                work_orders.pop()
                continue
            work_orders_by_key[key] = work_orders[-1]
    return work_orders


def _target_ids_from_work_order(
    row: Mapping[str, Any],
    *,
    fallback_target: str = "",
) -> tuple[str, ...]:
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
        or fallback_target
    )
    return tuple(dict.fromkeys(_str_tuple(raw_values)))


def _adapter_object_candidate_definition_request(
    *,
    placeholder_symbol: str,
    target_theorem_name: str,
    target_lean_declaration: str,
    target_ids: Sequence[str],
    group_id: str,
    premise_names: Sequence[str],
    source_binders: Sequence[Mapping[str, Any]],
    semantic_anchor_binders: Sequence[Mapping[str, Any]],
    semantic_anchor_names: Sequence[str],
    semantic_requirements: Sequence[str],
    adapter_objects: Sequence[str],
    proof_body_gate_status: str,
    source_theorem_exact_proof_body_reached: bool,
    source_theorem_exact_proof_body_gate_open_for_kernel_repair: bool,
    source_theorem_exact_proof_body_gate_open_target_names: Sequence[str],
    proof_body_signature_probe_artifact_path: str = "",
    source_theorem_signature_probe_artifact_path: str = "",
    proof_body_goal_context: Mapping[str, object] | None = None,
    proof_body_goal_binder_names: Sequence[str] = (),
    proof_body_goal_conclusion: str = "",
) -> dict[str, Any]:
    available_adapter_object_names = [
        str(value).strip()
        for value in adapter_objects
        if str(value).strip()
    ]
    required_anchor_names = [
        str(value).strip()
        for value in semantic_anchor_names
        if str(value).strip()
    ]
    return {
        "schema_version": 1,
        "request_kind": "source_theorem_exact_semantic_definition_candidate",
        "request_source": "source_to_bridge_adapter_object_semantic_definition",
        "target_theorem_name": target_theorem_name,
        "target_lean_declaration": target_lean_declaration,
        "target_ids": list(target_ids),
        "proof_body_gate_status": proof_body_gate_status,
        "proof_body_goal_context": dict(proof_body_goal_context or {}),
        "proof_body_goal_binder_names": list(proof_body_goal_binder_names),
        "proof_body_goal_conclusion": proof_body_goal_conclusion,
        "source_to_bridge_premise_goal_context": dict(
            proof_body_goal_context or {}
        ),
        "source_to_bridge_premise_goal_binder_names": list(
            proof_body_goal_binder_names
        ),
        "source_to_bridge_premise_goal_conclusion": proof_body_goal_conclusion,
        "source_theorem_exact_proof_body_reached": (
            source_theorem_exact_proof_body_reached
        ),
        "source_theorem_exact_proof_body_gate_open_for_kernel_repair": (
            source_theorem_exact_proof_body_gate_open_for_kernel_repair
        ),
        "source_theorem_exact_proof_body_gate_open_target_names": list(
            source_theorem_exact_proof_body_gate_open_target_names
        ),
        "proof_body_signature_probe_artifact_path": (
            proof_body_signature_probe_artifact_path
        ),
        "source_theorem_signature_probe_artifact_path": (
            source_theorem_signature_probe_artifact_path
        ),
        "signature_probe_artifact_path": (
            source_theorem_signature_probe_artifact_path
            or proof_body_signature_probe_artifact_path
        ),
        "placeholder_symbol": placeholder_symbol,
        "semantic_goal": (
            "Define this source-to-bridge adapter object from the exact source "
            "theorem binders and listed semantic anchors before retrying premise "
            "derivation or source-theorem proof-body work."
        ),
        "required_anchor_names": required_anchor_names,
        "available_anchor_names": required_anchor_names,
        "missing_required_anchor_names": [],
        "required_binders": [dict(row) for row in semantic_anchor_binders],
        "exact_source_theorem_binders": [dict(row) for row in source_binders],
        "required_adapter_object_names": [placeholder_symbol],
        "available_adapter_object_names": available_adapter_object_names,
        "missing_required_adapter_object_names": (
            []
            if placeholder_symbol in available_adapter_object_names
            else [placeholder_symbol]
        ),
        "source_to_bridge_adapter_instantiation_group_id": group_id,
        "source_to_bridge_adapter_instantiation_group_ids": (
            [group_id] if group_id else []
        ),
        "required_bridge_premise_names_for_shared_instantiation": list(
            premise_names
        ),
        "premise_semantic_dependency_requirements": list(semantic_requirements),
        "expected_outputs": {
            "definition_only_candidate_artifact_path": (
                "Lean file containing only exact semantic definitions and imports"
            ),
            "local_definition_lean_checked": False,
            "local_definition_lean_compiled": False,
            "semantic_definition_typecheck_evidence_status": (
                "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
            ),
        },
        "forbidden_shortcuts": [
            "do not define the placeholder as True",
            "do not add axiom/sorry/admit/unsafe",
            "do not assume or restate the source theorem target",
            "do not introduce stronger assumptions than the source theorem binders",
        ],
        "local_lean_gate": (
            "The definition-only candidate must compile under local Lean/AXLE "
            "before proof-body execution can use it; this is still semantic-"
            "definition evidence only, not theorem proof."
        ),
        "proof_evidence_status": (
            ADAPTER_OBJECT_SEMANTIC_DEFINITION_PROOF_EVIDENCE_STATUS
        ),
    }


def _merge_candidate_definition_request(
    payload: dict[str, Any],
    candidate_request: Any,
) -> None:
    if not isinstance(candidate_request, Mapping):
        return
    current_raw = payload.get("candidate_definition_request", {})
    if not isinstance(current_raw, Mapping) or not current_raw:
        payload["candidate_definition_request"] = dict(candidate_request)
        return
    current = dict(current_raw)
    for field in (
        "target_theorem_name",
        "target_lean_declaration",
        "placeholder_symbol",
        "semantic_goal",
        "local_lean_gate",
        "proof_evidence_status",
        "proof_body_gate_status",
        "proof_body_goal_context",
        "proof_body_goal_conclusion",
        "source_to_bridge_premise_goal_context",
        "source_to_bridge_premise_goal_conclusion",
        "proof_body_signature_probe_artifact_path",
        "source_theorem_signature_probe_artifact_path",
        "signature_probe_artifact_path",
    ):
        if not current.get(field) and candidate_request.get(field):
            current[field] = candidate_request[field]
    for field in (
        "source_theorem_exact_proof_body_reached",
        "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
    ):
        if not _bool_like(current.get(field)) and _bool_like(
            candidate_request.get(field)
        ):
            current[field] = True
    for field in (
        "target_ids",
        "required_anchor_names",
        "available_anchor_names",
        "missing_required_anchor_names",
        "required_binders",
        "exact_source_theorem_binders",
        "required_adapter_object_names",
        "available_adapter_object_names",
        "missing_required_adapter_object_names",
        "source_to_bridge_adapter_instantiation_group_ids",
        "required_bridge_premise_names_for_shared_instantiation",
        "premise_semantic_dependency_requirements",
        "proof_body_goal_binder_names",
        "source_to_bridge_premise_goal_binder_names",
        "source_theorem_exact_proof_body_gate_open_target_names",
        "forbidden_shortcuts",
    ):
        current_values = list(current.get(field, []) or [])
        seen = {
            json.dumps(value, sort_keys=True, default=str)
            for value in current_values
        }
        for value in candidate_request.get(field, []) or []:
            key = json.dumps(value, sort_keys=True, default=str)
            if key in seen:
                continue
            current_values.append(value)
            seen.add(key)
        if current_values:
            current[field] = current_values
    if not current.get("source_to_bridge_adapter_instantiation_group_id"):
        group_id = str(
            candidate_request.get("source_to_bridge_adapter_instantiation_group_id", "")
            or ""
        )
        if group_id:
            current["source_to_bridge_adapter_instantiation_group_id"] = group_id
    if not isinstance(current.get("expected_outputs", {}), Mapping):
        current["expected_outputs"] = dict(
            candidate_request.get("expected_outputs", {}) or {}
        )
    payload["candidate_definition_request"] = current


def _premise_derivation_candidate_request_rows(
    rows: list[SourceToBridgePremiseDerivationCheckRow],
    *,
    queue_path: Path,
) -> list[dict[str, Any]]:
    group_premise_names: dict[str, tuple[str, ...]] = {}
    for row in rows:
        group_id = row.adapter_instantiation_group_id
        if not group_id:
            continue
        current = list(group_premise_names.get(group_id, ()))
        if row.premise_name and row.premise_name not in current:
            current.append(row.premise_name)
        group_premise_names[group_id] = tuple(current)
    return [
        request
        for row in rows
        for request in [
            _premise_derivation_candidate_request_row(
                row,
                queue_path=queue_path,
                shared_premise_names=group_premise_names.get(
                    row.adapter_instantiation_group_id,
                    (),
                ),
            )
        ]
        if request
    ]


def _grouped_premise_derivation_candidate_request_rows(
    *,
    rows: list[SourceToBridgePremiseDerivationCheckRow],
    queue_path: Path,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[SourceToBridgePremiseDerivationCheckRow]] = {}
    for row in rows:
        if row.premise_derivation_kernel_verified:
            continue
        if row.premise_target_status != "ADAPTER_PREMISE_TARGET_EXTRACTED":
            continue
        if not row.premise_target_type:
            continue
        group_id = row.adapter_instantiation_group_id or (
            "source_to_bridge_adapter_instantiation_group:"
            + stable_hash([row.work_order_id, row.premise_name])[:20]
        )
        grouped.setdefault(group_id, []).append(row)
    result: list[dict[str, Any]] = []
    for group_id, group_rows in grouped.items():
        premise_names = tuple(
            dict.fromkeys(row.premise_name for row in group_rows if row.premise_name)
        )
        if not premise_names:
            continue
        per_premise_requests = [
            request
            for row in group_rows
            for request in [
                _premise_derivation_candidate_request_row(
                    row,
                    queue_path=queue_path,
                    shared_premise_names=premise_names,
                )
            ]
            if request
        ]
        if not per_premise_requests:
            continue
        target_lean_declarations = tuple(
            dict.fromkeys(
                row.target_lean_declaration
                for row in group_rows
                if row.target_lean_declaration
            )
        )
        target_theorem_names = tuple(
            dict.fromkeys(row.target_theorem_name for row in group_rows if row.target_theorem_name)
        )
        adapter_objects = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.adapter_object_names_requiring_source_instantiation
                if value
            )
        )
        group_uses_goal_context = bool(group_rows) and all(
            _premise_target_uses_proof_body_goal_context(
                premise_target_source=row.premise_target_source,
                premise_target_type=row.premise_target_type,
                proof_body_goal_conclusion=row.proof_body_goal_conclusion,
            )
            for row in group_rows
        )
        exact_binders = _merge_named_mapping_rows(
            row.exact_source_theorem_binders for row in group_rows
        )
        semantic_anchor_binders = _merge_named_mapping_rows(
            row.premise_semantic_anchor_binders for row in group_rows
        )
        semantic_anchor_names = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.premise_semantic_anchor_binder_names
                if value
            )
        )
        semantic_requirements = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.premise_semantic_dependency_requirements
                if value
            )
        )
        semantic_alignment_constraints = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.semantic_alignment_constraints
                if value
            )
        )
        semantic_alignment_blockers = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.semantic_alignment_blockers
                if value
            )
        )
        proof_body_attempt_count = max(
            (row.proof_body_attempt_count for row in group_rows),
            default=0,
        )
        proof_body_gate_status = next(
            (row.proof_body_gate_status for row in group_rows if row.proof_body_gate_status),
            "",
        )
        proof_body_goal_context = next(
            (row.proof_body_goal_context for row in group_rows if row.proof_body_goal_context),
            {},
        )
        proof_body_goal_binder_names = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                for value in row.proof_body_goal_binder_names
                if value
            )
        )
        proof_body_goal_conclusion = next(
            (
                row.proof_body_goal_conclusion
                for row in group_rows
                if row.proof_body_goal_conclusion
            ),
            "",
        )
        source_theorem_exact_proof_body_reached = any(
            row.source_theorem_exact_proof_body_reached for row in group_rows
        )
        source_theorem_exact_proof_body_gate_open_for_kernel_repair = any(
            row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
            for row in group_rows
        )
        proof_body_gate_open_target_names = tuple(
            dict.fromkeys(
                value
                for row in group_rows
                if row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
                for value in (
                    row.source_theorem_exact_proof_body_gate_open_target_names
                    or ((row.target_theorem_name,) if row.target_theorem_name else ())
                )
                if value
            )
        )
        source_theorem_kernel_evidence_eligible = any(
            row.source_theorem_kernel_evidence_eligible for row in group_rows
        )
        proof_body_signature_probe_artifact_path = next(
            (
                row.proof_body_signature_probe_artifact_path
                for row in group_rows
                if row.proof_body_signature_probe_artifact_path
            ),
            "",
        )
        source_theorem_signature_probe_artifact_path = next(
            (
                row.source_theorem_signature_probe_artifact_path
                for row in group_rows
                if row.source_theorem_signature_probe_artifact_path
            ),
            proof_body_signature_probe_artifact_path,
        )
        shared_contract = next(
            (
                row.shared_adapter_instantiation_contract
                for row in group_rows
                if row.shared_adapter_instantiation_contract
            ),
            "",
        )
        if not shared_contract:
            adapter_object_phrase = _adapter_object_contract_phrase(adapter_objects)
            shared_contract = (
                "Use one shared reached proof-body goal context and exact "
                "source-binder interpretation across all listed premise_names; "
                "do not prove grouped premises with incompatible goal-context "
                "interpretations."
                if group_uses_goal_context and not adapter_objects
                else (
                    f"Use one shared source-derived instantiation of "
                    f"{adapter_object_phrase} across all listed premise_names; "
                    "do not prove grouped premises with incompatible definitions."
                )
            )
        grouped_candidate_contract = (
            "Return one source_to_bridge_premise_derivation_candidates object "
            "for this group. Its premise_names must list every required bridge "
            "premise, and its Lean source must derive each listed "
            "premise_candidate_declaration_name from exact source theorem "
            "binders and the listed proof_body_goal_context anchors. The proof "
            "body must substantively reference every "
            "required_semantic_anchor_reference_names entry outside comments "
            "and outside no-op lines such as `have h := h`. Do not add the "
            "premise names, proof-body goal binders, or target conclusions as "
            "arbitrary theorem assumptions."
            if group_uses_goal_context and not adapter_objects
            else (
                "Return one source_to_bridge_premise_derivation_candidates "
                "object for this group. Its premise_names must list every "
                "required bridge premise, and its Lean source must define the "
                "shared adapter objects once from exact source theorem binders "
                "and include each listed premise_candidate_declaration_name. "
                "The proof body must substantively reference every "
                "required_semantic_anchor_reference_names entry outside "
                "comments and outside no-op lines such as `have h := h`. "
                "Do not add the premise names or adapter objects as arbitrary "
                "theorem assumptions, and do not put adapter objects requiring "
                "source instantiation in the theorem header as free binders."
            )
        )
        grouped_forbidden_actions = [
            (
                "do not split this group into incompatible proof-body goal-context interpretations"
                if group_uses_goal_context and not adapter_objects
                else "do not split this group into incompatible adapter-object definitions"
            ),
            "do not assume any listed bridge premise as a binder",
            "do not satisfy semantic-anchor requirements with comments or unused have/let aliases",
        ]
        if group_uses_goal_context and not adapter_objects:
            grouped_forbidden_actions.append(
                "do not introduce reached proof-body goal binders or target conclusions as free theorem assumptions"
            )
        else:
            grouped_forbidden_actions.append(
                "do not put "
                + _adapter_object_contract_phrase(adapter_objects)
                + " in the theorem header as free binders"
            )
        grouped_forbidden_actions.extend(
            [
                "do not add axiom, sorry, admit, unsafe, or placeholder definitions",
                "do not claim full source theorem proof from this request",
            ]
        )
        source_grouped_request = next(
            (
                dict(row.source_to_bridge_grouped_premise_derivation_candidate_request)
                for row in group_rows
                if row.source_to_bridge_grouped_premise_derivation_candidate_request
            ),
            {},
        )
        source_grouped_request_id = next(
            (
                row.source_to_bridge_grouped_premise_derivation_candidate_request_id
                for row in group_rows
                if row.source_to_bridge_grouped_premise_derivation_candidate_request_id
            ),
            "",
        )
        grouped_request_id = (
            source_grouped_request_id
            or str(source_grouped_request.get("grouped_candidate_request_id", "") or "")
            or (
                "source_to_bridge_grouped_premise_derivation_candidate_request:"
                + stable_hash([group_id, premise_names, target_lean_declarations])[:20]
            )
        )
        result.append(
            {
                **source_grouped_request,
                "schema_version": 1,
                "artifact_kind": (
                    "SourceToBridgeGroupedPremiseDerivationCandidateRequest"
                ),
                "grouped_candidate_request_id": grouped_request_id,
                "source_grouped_candidate_request_id": source_grouped_request_id,
                "source_grouped_candidate_request": source_grouped_request,
                "source_queue_jsonl": str(queue_path),
                "adapter_instantiation_group_id": group_id,
                "question_id": group_rows[0].question_id,
                "question_title": group_rows[0].question_title,
                "target_theorem_name": target_theorem_names[0]
                if target_theorem_names
                else "",
                "target_lean_declaration": target_lean_declarations[0]
                if target_lean_declarations
                else "",
                "target_theorem_goal_ids": list(
                    dict.fromkeys(
                        value
                        for row in group_rows
                        for value in row.target_theorem_goal_ids
                        if value
                    )
                ),
                "proof_body_signature_probe_artifact_path": (
                    proof_body_signature_probe_artifact_path
                ),
                "source_theorem_signature_probe_artifact_path": (
                    source_theorem_signature_probe_artifact_path
                ),
                "signature_probe_artifact_path": (
                    source_theorem_signature_probe_artifact_path
                    or proof_body_signature_probe_artifact_path
                ),
                "premise_names": list(premise_names),
                "required_bridge_premise_names_for_shared_instantiation": list(
                    premise_names
                ),
                "shared_adapter_instantiation_contract": shared_contract,
                "adapter_object_names_requiring_source_instantiation": list(
                    adapter_objects
                ),
                "per_premise_candidate_requests": per_premise_requests,
                "premise_candidate_declaration_names": [
                    {
                        "premise_name": request.get("premise_name", ""),
                        "premise_candidate_declaration_name": request.get(
                            "premise_candidate_declaration_name",
                            "",
                        ),
                        "premise_target_type": request.get("premise_target_type", ""),
                        "premise_target_source": request.get(
                            "premise_target_source",
                            "",
                        ),
                        "candidate_request_id": request.get("candidate_request_id", ""),
                    }
                    for request in per_premise_requests
                ],
                "exact_source_theorem_binders": list(exact_binders),
                "premise_semantic_anchor_binders": list(semantic_anchor_binders),
                "premise_semantic_anchor_binder_names": list(
                    semantic_anchor_names
                ),
                "required_semantic_anchor_reference_names": list(
                    semantic_anchor_names
                ),
                "premise_semantic_dependency_requirements": list(
                    semantic_requirements
                ),
                "semantic_alignment_constraints": list(
                    semantic_alignment_constraints
                ),
                "semantic_alignment_blockers": list(semantic_alignment_blockers),
                "source_theorem_kernel_evidence_eligible": (
                    source_theorem_kernel_evidence_eligible
                ),
                "proof_body_attempt_count": proof_body_attempt_count,
                "proof_body_goal_excerpt": list(
                    dict.fromkeys(
                        value
                        for row in group_rows
                        for value in row.proof_body_goal_excerpt
                        if value
                    )
                )[:12],
                "proof_body_goal_context": dict(proof_body_goal_context),
                "proof_body_goal_binder_names": list(
                    proof_body_goal_binder_names
                ),
                "proof_body_goal_conclusion": proof_body_goal_conclusion,
                "source_to_bridge_premise_goal_context": dict(
                    proof_body_goal_context
                ),
                "source_to_bridge_premise_goal_binder_names": list(
                    proof_body_goal_binder_names
                ),
                "source_to_bridge_premise_goal_conclusion": (
                    proof_body_goal_conclusion
                ),
                "proof_body_attempt_summaries": list(
                    dict.fromkeys(
                        value
                        for row in group_rows
                        for value in row.proof_body_attempt_summaries
                        if value
                    )
                )[:12],
                "proof_body_gate_status": proof_body_gate_status,
                "source_theorem_exact_proof_body_reached": (
                    source_theorem_exact_proof_body_reached
                ),
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair": (
                    source_theorem_exact_proof_body_gate_open_for_kernel_repair
                ),
                "source_theorem_exact_proof_body_gate_open_target_names": list(
                    proof_body_gate_open_target_names
                ),
                "required_formalizer_output_key": (
                    "source_to_bridge_premise_derivation_candidates"
                ),
                "required_candidate_fields": [
                    "premise_names",
                    "adapter_instantiation_group_id",
                    "target_theorem_name",
                    "target_lean_declaration",
                    "premise_derivation_candidate_lean_source",
                ],
                "candidate_contract": grouped_candidate_contract,
                "forbidden_actions": grouped_forbidden_actions,
                "acceptance_gate": (
                    "The SourceToBridgePremiseDerivation bridge must local Lean/AXLE "
                    "kernel verify the grouped Lean source for each listed premise. "
                    "The full source theorem remains unproved until exact proof-body "
                    "retry verifies the source theorem declaration."
                ),
                "proof_evidence_status": (
                    "SOURCE_TO_BRIDGE_GROUPED_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                "boundary": BOUNDARY,
            }
        )
    return result


def _merge_named_mapping_rows(
    groups: Any,
) -> tuple[dict[str, object], ...]:
    merged: list[dict[str, object]] = []
    seen: set[str] = set()
    for group in groups:
        for item in group or ():
            if not isinstance(item, Mapping):
                continue
            name = str(item.get("name", "") or "")
            key = name or stable_hash(item)[:12]
            if key in seen:
                continue
            seen.add(key)
            merged.append(dict(item))
    return tuple(merged)


def _premise_derivation_candidate_request_row(
    row: SourceToBridgePremiseDerivationCheckRow,
    *,
    queue_path: Path,
    shared_premise_names: tuple[str, ...] = (),
) -> dict[str, Any] | None:
    if row.premise_derivation_kernel_verified:
        return None
    if row.premise_target_status != "ADAPTER_PREMISE_TARGET_EXTRACTED":
        return None
    if not row.premise_target_type:
        return None
    request_id = "source_to_bridge_premise_derivation_candidate_request:" + stable_hash(
        [
            row.premise_derivation_check_id,
            row.work_order_id,
            row.premise_name,
            row.premise_target_type,
            row.failure_classification,
        ]
    )[:20]
    policy_scope_context = {
        "question_id": row.question_id,
        "target_theorem_name": row.target_theorem_name,
        "target_lean_declaration": row.target_lean_declaration,
        "target_ids": list(row.target_ids),
        "target_theorem_goal_ids": list(row.target_theorem_goal_ids),
        "candidate_definition_request": dict(
            row.source_to_bridge_premise_derivation_candidate_request
        ),
    }
    source_binders = row.exact_source_theorem_binders or _source_theorem_binder_summaries(
        row.source_theorem_signature_excerpt,
        context=policy_scope_context,
    )
    semantic_anchor_binders = (
        row.premise_semantic_anchor_binders
        or _premise_semantic_anchor_binder_summaries(
            premise_name=row.premise_name,
            premise_target_type=row.premise_target_type,
            semantic_requirements=row.premise_semantic_dependency_requirements,
            source_binders=source_binders,
            context=policy_scope_context,
        )
    )
    target_uses_goal_context = _premise_target_uses_proof_body_goal_context(
        premise_target_source=row.premise_target_source,
        premise_target_type=row.premise_target_type,
        proof_body_goal_conclusion=row.proof_body_goal_conclusion,
    )
    adapter_object_phrase = _adapter_object_contract_phrase(
        row.adapter_object_names_requiring_source_instantiation
    )
    default_shared_contract = (
        "All source-to-bridge premise candidates with the same "
        "adapter_instantiation_group_id must use the same reached proof-body "
        "goal context and exact source binders when deriving the listed "
        "premises. Independently proving premises with incompatible goal-context "
        "interpretations cannot be combined into source theorem proof evidence."
        if target_uses_goal_context
        else (
            "All source-to-bridge premise candidates with the same "
            "adapter_instantiation_group_id must use one shared definition of "
            f"{adapter_object_phrase} from the exact source theorem binders. "
            "Independently proving premises with incompatible adapter-object "
            "definitions cannot be combined into source theorem proof evidence."
        )
    )
    bridge_object_instantiation_policy = (
        "This premise target was extracted from the reached proof-body goal. The "
        "candidate must derive it from exact source-theorem binders and the "
        "listed proof_body_goal_context anchors; do not introduce those goal "
        "binders or the target conclusion as arbitrary assumptions."
        if target_uses_goal_context
        else (
            f"{adapter_object_phrase} are not source-theorem assumptions. The "
            "candidate must define or instantiate them from the exact source "
            "binders, or report a semantic blocker instead of treating them as "
            "arbitrary variables."
        )
    )
    arbitrary_free_variable_clause = (
        "Do not treat reached proof-body goal binders or the target conclusion as "
        "arbitrary free variables or theorem parameters when they must be derived "
        "from the source theorem. "
        if target_uses_goal_context
        else (
            f"Do not treat {adapter_object_phrase} as arbitrary free variables "
            "or theorem parameters when they must be instantiated from the "
            "source theorem. "
        )
    )
    return {
        "schema_version": 1,
        "artifact_kind": "SourceToBridgePremiseDerivationCandidateRequest",
        "candidate_request_id": request_id,
        "source_queue_jsonl": str(queue_path),
        "source_premise_derivation_check_id": row.premise_derivation_check_id,
        "source_premise_derivation_work_order_id": row.work_order_id,
        "source_candidate_request_id": (
            row.source_to_bridge_premise_derivation_candidate_request_id
        ),
        "source_candidate_request": dict(
            row.source_to_bridge_premise_derivation_candidate_request
        ),
        "source_grouped_candidate_request_id": (
            row.source_to_bridge_grouped_premise_derivation_candidate_request_id
        ),
        "source_grouped_candidate_request": dict(
            row.source_to_bridge_grouped_premise_derivation_candidate_request
        ),
        "question_id": row.question_id,
        "question_title": row.question_title,
        "target_theorem_name": row.target_theorem_name,
        "target_lean_declaration": row.target_lean_declaration,
        "target_theorem_goal_ids": list(row.target_theorem_goal_ids),
        "premise_name": row.premise_name,
        "premise_target_status": row.premise_target_status,
        "premise_target_matched_binder": row.premise_target_matched_binder,
        "premise_target_type": row.premise_target_type,
        "premise_target_source": row.premise_target_source,
        "adapter_instantiation_group_id": row.adapter_instantiation_group_id,
        "required_bridge_premise_names_for_shared_instantiation": list(
            row.required_bridge_premise_names_for_shared_instantiation
            or shared_premise_names
            or ((row.premise_name,) if row.premise_name else ())
        ),
        "shared_adapter_instantiation_contract": (
            row.shared_adapter_instantiation_contract or default_shared_contract
        ),
        "premise_candidate_declaration_name": row.premise_candidate_declaration_name,
        "premise_candidate_artifact_path": row.premise_candidate_artifact_path,
        "premise_candidate_generation_mode": row.premise_candidate_generation_mode,
        "premise_derivation_gap_kind": row.premise_derivation_gap_kind,
        "premise_derivation_gap_summary": row.premise_derivation_gap_summary,
        "premise_semantic_dependency_status": row.premise_semantic_dependency_status,
        "premise_semantic_dependency_source": row.premise_semantic_dependency_source,
        "premise_semantic_dependency_requirements": list(
            row.premise_semantic_dependency_requirements
        ),
        "source_to_bridge_policy_pack_ids": list(row.source_to_bridge_policy_pack_ids),
        "source_to_bridge_policy_ids": list(row.source_to_bridge_policy_ids),
        "source_to_bridge_policy_scopes": list(row.source_to_bridge_policy_scopes),
        "source_to_bridge_policy_required_anchor_names": list(
            row.source_to_bridge_policy_required_anchor_names
        ),
        "source_to_bridge_policy_dependency_requirements": list(
            row.source_to_bridge_policy_dependency_requirements
        ),
        "source_candidate_artifact_path": row.source_candidate_artifact_path,
        "adapter_candidate_artifact_path": row.adapter_candidate_artifact_path,
        "proof_body_signature_probe_artifact_path": (
            row.proof_body_signature_probe_artifact_path
        ),
        "source_theorem_signature_probe_artifact_path": (
            row.source_theorem_signature_probe_artifact_path
        ),
        "signature_probe_artifact_path": (
            row.source_theorem_signature_probe_artifact_path
            or row.proof_body_signature_probe_artifact_path
        ),
        "adapter_declaration_name": row.adapter_declaration_name,
        "source_theorem_signature_excerpt": list(row.source_theorem_signature_excerpt),
        "adapter_signature_excerpt": list(row.adapter_signature_excerpt),
        "exact_source_theorem_binders": list(source_binders),
        "premise_semantic_anchor_binders": list(semantic_anchor_binders),
        "premise_semantic_anchor_binder_names": [
            str(item.get("name", "") or "")
            for item in semantic_anchor_binders
            if str(item.get("name", "") or "")
        ],
        "required_semantic_anchor_reference_names": [
            str(item.get("name", "") or "")
            for item in semantic_anchor_binders
            if str(item.get("name", "") or "")
        ],
        "semantic_anchor_reference_gate": (
            "The returned Lean candidate source must reference every "
            "required_semantic_anchor_reference_names entry outside comments; "
            "otherwise it is rejected before local Lean and cannot become proof "
            "evidence."
        ),
        "bridge_object_instantiation_policy": (
            bridge_object_instantiation_policy
        ),
        "adapter_object_names_requiring_source_instantiation": list(
            row.adapter_object_names_requiring_source_instantiation
        ),
        "exact_goal_shape_obligation_ids": list(row.exact_goal_shape_obligation_ids),
        "proof_body_goal_excerpt": list(row.proof_body_goal_excerpt),
        "proof_body_goal_context": row.proof_body_goal_context,
        "proof_body_goal_binder_names": list(row.proof_body_goal_binder_names),
        "proof_body_goal_conclusion": row.proof_body_goal_conclusion,
        "source_to_bridge_premise_goal_context": row.proof_body_goal_context,
        "source_to_bridge_premise_goal_binder_names": list(
            row.proof_body_goal_binder_names
        ),
        "source_to_bridge_premise_goal_conclusion": row.proof_body_goal_conclusion,
        "proof_body_attempt_summaries": list(row.proof_body_attempt_summaries),
        "proof_body_attempt_count": row.proof_body_attempt_count,
        "proof_body_gate_status": row.proof_body_gate_status,
        "source_theorem_exact_proof_body_reached": (
            row.source_theorem_exact_proof_body_reached
        ),
        "source_theorem_exact_proof_body_gate_open_for_kernel_repair": (
            row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
        ),
        "source_theorem_exact_proof_body_gate_open_target_names": list(
            row.source_theorem_exact_proof_body_gate_open_target_names
        ),
        "semantic_alignment_constraints": list(row.semantic_alignment_constraints),
        "semantic_alignment_blockers": list(row.semantic_alignment_blockers),
        "source_theorem_kernel_evidence_eligible": (
            row.source_theorem_kernel_evidence_eligible
        ),
        "kernel_verified_theorem_reduction_closure_declarations": list(
            row.kernel_verified_theorem_reduction_closure_declarations
        ),
        "verified_theorem_reduction_closure_artifact_paths": list(
            row.verified_theorem_reduction_closure_artifact_paths
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
            row.kernel_verified_source_theorem_semantic_support_obligation_ids
        ),
        "required_formalizer_output_key": (
            "source_to_bridge_premise_derivation_candidates"
        ),
        "required_candidate_fields": [
            "premise_name",
            "target_theorem_name",
            "target_lean_declaration",
            "premise_derivation_candidate_lean_source",
        ],
        "candidate_contract": (
            "Return a non-vacuous Lean declaration with exactly the listed "
            "premise_candidate_declaration_name. The runtime compiles the exact "
            "source and asks Lean to resolve that identity. Prove premise_target_type from "
            "exact source-theorem hypotheses and semantic dependencies. Use the "
            "premise_semantic_anchor_binders as the preferred source binders for "
            "this premise and reference every required_semantic_anchor_reference_names "
            "entry in the Lean source outside comments. "
            + arbitrary_free_variable_clause
            + "Do not reintroduce the forbidden adapter premise as an assumption."
        ),
        "forbidden_actions": [
            "do not add axiom, sorry, admit, unsafe, or placeholder definitions",
            "do not assume the target adapter premise under another binder name",
            "do not change the exact source theorem statement as part of this request",
            "do not claim source theorem proof from this candidate request",
        ],
        "acceptance_gate": (
            "The SourceToBridgePremiseDerivation bridge must local Lean/AXLE "
            "kernel verify the returned candidate and reject vacuous or "
            "premise-assuming candidates. The full source theorem remains unproved "
            "until the exact source theorem proof body is rerun and verified."
        ),
        "proof_evidence_status": (
            "SOURCE_TO_BRIDGE_PREMISE_DERIVATION_CANDIDATE_REQUEST_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "boundary": BOUNDARY,
    }


def _source_theorem_binder_summaries(
    source_signature: tuple[str, ...],
    *,
    context: Mapping[str, Any] | None = None,
) -> tuple[dict[str, str], ...]:
    binders: list[dict[str, str]] = []
    seen: set[str] = set()
    joined_signature = " ".join(
        str(line).strip() for line in source_signature if str(line).strip()
    )
    parse_sources = (
        (joined_signature,) if joined_signature else ()
    ) + tuple(str(line).strip() for line in source_signature)
    for text in parse_sources:
        for name, binder_type in _parse_named_binders(text):
            if name in seen:
                continue
            seen.add(name)
            binders.append(
                {
                    "name": name,
                    "type": binder_type,
                    "role": _source_binder_role(
                        name=name,
                        binder_type=binder_type,
                        context=context,
                    ),
                }
            )
    return tuple(binders)


def _parse_named_binders(line: str) -> tuple[tuple[str, str], ...]:
    text = line.strip()
    if text.endswith(":"):
        text = text[:-1].rstrip()
    parsed: list[tuple[str, str]] = []
    for inner in _top_level_parenthesized_groups(text):
        parsed.extend(_parse_named_binder_inner(inner))
    return tuple(parsed)


def _top_level_parenthesized_groups(text: str) -> tuple[str, ...]:
    groups: list[str] = []
    start = -1
    depth = 0
    for idx, char in enumerate(str(text or "")):
        if char == "(":
            if depth == 0:
                start = idx + 1
            depth += 1
        elif char == ")" and depth:
            depth -= 1
            if depth == 0 and start >= 0:
                groups.append(text[start:idx].strip())
                start = -1
    return tuple(group for group in groups if group)


def _parse_named_binder_inner(inner: str) -> tuple[tuple[str, str], ...]:
    inner = inner.strip()
    if ":" not in inner:
        return ()
    names_text, target = inner.split(":", 1)
    names = tuple(name.strip() for name in names_text.split() if name.strip())
    target = target.strip()
    if not names or not target:
        return ()
    if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_'.]*", name) for name in names):
        return ()
    return tuple((name, target) for name in names)


def _source_binder_role(
    *,
    name: str,
    binder_type: str,
    context: Mapping[str, Any] | None = None,
) -> str:
    policy_role = _source_to_bridge_policy_anchor_role(
        name,
        context=context,
    )
    if policy_role:
        return policy_role
    return exact_semantic_definition_fallback_source_anchor_role(
        name=name,
        binder_type=binder_type,
        context=context,
    )


def _premise_semantic_anchor_binder_summaries(
    *,
    premise_name: str,
    premise_target_type: str,
    semantic_requirements: tuple[str, ...],
    source_binders: tuple[dict[str, str], ...],
    context: Mapping[str, Any] | None = None,
) -> tuple[dict[str, str], ...]:
    policy_anchor_names = _source_to_bridge_policy_required_anchor_names(
        premise_name=premise_name,
        premise_target_type=premise_target_type,
        context=context,
    )
    if policy_anchor_names:
        normalized_policy_anchors = {
            _normalize_premise_identifier(name) for name in policy_anchor_names
        }
        selected_from_policy = [
            binder
            for binder in source_binders
            if _normalize_premise_identifier(binder.get("name", ""))
            in normalized_policy_anchors
        ]
        if selected_from_policy:
            return tuple(selected_from_policy[:12])
    fallback_anchor_names = (
        exact_semantic_definition_source_to_bridge_anchor_fallback_names(
            premise_name=premise_name,
            premise_target_type=premise_target_type,
            semantic_requirements=semantic_requirements,
            context=context,
        )
    )
    if not fallback_anchor_names:
        return source_binders[:8]
    normalized_wanted = {
        _normalize_premise_identifier(name) for name in fallback_anchor_names
    }
    selected = [
        binder
        for binder in source_binders
        if _normalize_premise_identifier(binder.get("name", "")) in normalized_wanted
    ]
    return tuple(selected[:12])


def _missing_semantic_anchor_references(
    source: str,
    *,
    declaration_name: str = "",
    anchor_names: tuple[str, ...],
) -> tuple[str, ...]:
    names = tuple(dict.fromkeys(str(name).strip() for name in anchor_names if str(name).strip()))
    if not names:
        return ()
    stripped = _lean_proof_body_without_comments(
        source,
        declaration_name=declaration_name,
    )
    missing = [
        name
        for name in names
        if not _semantic_anchor_has_substantive_reference(stripped, name)
    ]
    return tuple(missing)


def _semantic_anchor_has_substantive_reference(proof_body: str, name: str) -> bool:
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    for raw_line in proof_body.splitlines():
        line = raw_line.strip()
        if not pattern.search(line):
            continue
        if _semantic_anchor_reference_line_is_noop(line, name):
            continue
        return True
    return False


def _semantic_anchor_reference_line_is_noop(line: str, name: str) -> bool:
    name_pat = re.escape(name)
    noop_patterns = (
        rf"^(?:have|let)\s+_\s*(?::[^:=]+)?\s*:=\s*{name_pat}\s*$",
        rf"^(?:have|let)\s+[A-Za-z_][A-Za-z0-9_'.]*\s*(?::[^:=]+)?\s*:=\s*{name_pat}\s*$",
    )
    return any(re.search(pattern, line) for pattern in noop_patterns)


def _lean_proof_body_without_comments(
    source: str,
    *,
    declaration_name: str = "",
) -> str:
    theorem_text = _lean_theorem_text_without_comments(
        source,
        declaration_name=declaration_name,
    )
    proof_match = re.search(r"\s:=\s*by\b|\s:=\s*", theorem_text)
    if not proof_match:
        return ""
    return theorem_text[proof_match.end() :]


def _premise_failure_classification(
    *,
    local_lean: bool,
    local_source_compiled: bool,
    local_compiled: bool,
    provided_source: bool,
    evidence_eligible: bool,
    candidate_identity_present: bool,
    candidate_identity_checked: bool,
    candidate_identity_verified: bool,
    premise_referenced: bool,
    source_binding_contract_present: bool,
    vacuous: bool,
    assumes_forbidden_premise: bool,
    uninstantiated_adapter_object_binders: tuple[str, ...],
    references_semantic_anchor: bool,
    forbidden_tokens: tuple[str, ...],
    diagnostics: tuple[str, ...],
) -> str:
    if not provided_source:
        return "premise_derivation_candidate_missing_nonvacuous_source"
    if forbidden_tokens:
        return "premise_derivation_candidate_forbidden_placeholder_token"
    if vacuous:
        return "premise_derivation_candidate_vacuous"
    if assumes_forbidden_premise:
        return "premise_derivation_candidate_assumes_forbidden_premise"
    if uninstantiated_adapter_object_binders:
        return "premise_derivation_candidate_uninstantiated_adapter_objects"
    if not source_binding_contract_present:
        return "premise_derivation_candidate_missing_source_binding_contract"
    if not references_semantic_anchor:
        return "premise_derivation_candidate_missing_semantic_anchor_reference"
    if not candidate_identity_present:
        return "premise_derivation_candidate_wrong_declaration"
    if not premise_referenced:
        return "premise_derivation_candidate_missing_premise_reference"
    if not evidence_eligible:
        return "premise_derivation_candidate_not_evidence_eligible"
    if not local_lean:
        return "premise_derivation_candidate_not_checked"
    if local_compiled:
        return ""
    if (
        local_source_compiled
        and candidate_identity_checked
        and not candidate_identity_verified
    ):
        return "premise_derivation_candidate_wrong_declaration"
    text = "\n".join(diagnostics).lower()
    if "timed out" in text or "timeout" in text:
        return "premise_derivation_local_lean_timeout"
    if "unknown module prefix" in text or ".olean" in text:
        return "premise_derivation_lean_import_environment_missing"
    if "unknown identifier" in text or "unknown constant" in text:
        return "premise_derivation_formal_environment_symbol_missing"
    if "unsolved goals" in text:
        return "premise_derivation_proof_incomplete"
    if diagnostics:
        return "premise_derivation_local_lean_failed"
    return "premise_derivation_local_lean_not_run"


def _premise_derivation_gap(
    *,
    premise_name: str,
    premise_target_status: str,
    premise_target_type: str,
    generation_mode: str,
    evidence_eligible: bool,
    premise_verified: bool,
    assumes_forbidden_premise: bool,
    uninstantiated_adapter_object_binders: tuple[str, ...],
    source_binding_contract_present: bool,
    references_semantic_anchor: bool,
    missing_semantic_anchor_names: tuple[str, ...],
    local_lean: bool,
    local_compiled: bool,
    failure_classification: str,
) -> tuple[str, str]:
    if premise_verified:
        return "", ""
    if (
        not source_binding_contract_present
        and generation_mode != "llm_premise_derivation_candidate_required"
    ):
        return (
            "premise_derivation_missing_source_binding_contract",
            "The candidate work order does not carry a source-to-bridge "
            "candidate request, grouped request, exact source binders, semantic "
            "anchor requirements, or adapter-object instantiation constraints. "
            "Do not treat a locally compiling generated theorem as source-to-"
            "bridge evidence until the queue preserves that contract.",
        )
    if assumes_forbidden_premise:
        return (
            "premise_derivation_reassumes_forbidden_adapter_premise",
            "The candidate reintroduced the adapter premise as an assumption; "
            "derive the premise from exact source hypotheses instead.",
        )
    if uninstantiated_adapter_object_binders:
        names = ", ".join(uninstantiated_adapter_object_binders)
        return (
            "premise_derivation_uninstantiated_adapter_objects",
            "The candidate leaves adapter object binder(s) as free theorem "
            f"parameters: {names}. Define or instantiate them from exact "
            "source-theorem binders before checking this premise derivation.",
        )
    if not references_semantic_anchor:
        missing = ", ".join(missing_semantic_anchor_names) or "the listed anchors"
        return (
            "premise_derivation_missing_semantic_anchor_reference",
            "The candidate does not reference the required exact source semantic "
            f"anchor binder(s): {missing}. Repair the candidate to derive the "
            "premise from those exact source hypotheses, or report the missing "
            "semantic primitive as a blocker.",
        )
    if premise_target_status == "ADAPTER_PREMISE_TARGET_EXTRACTED":
        target = premise_target_type or premise_name or "the adapter premise"
        if generation_mode == "llm_premise_derivation_candidate_required":
            return (
                "concrete_premise_target_lacks_nonvacuous_derivation_candidate",
                "The adapter premise target is known, but the bridge only "
                "has no coding-agent candidate. Generate a "
                "non-vacuous Lean derivation of "
                + target
                + " from exact source-theorem hypotheses before retrying the "
                "adapter or source theorem proof body.",
            )
        if evidence_eligible and local_lean and not local_compiled:
            return (
                "concrete_premise_target_candidate_failed_local_lean",
                "A non-vacuous candidate targets "
                + target
                + " but failed local Lean; repair the proof term or missing "
                "formal dependencies before promoting it.",
            )
        if not evidence_eligible:
            return (
                "concrete_premise_target_candidate_not_evidence_eligible",
                "The adapter premise target is known, but the candidate is not "
                "eligible as proof evidence; repair the candidate without "
                "vacuity, forbidden placeholders, or reassuming the premise.",
            )
    if failure_classification:
        return (
            "premise_derivation_unverified",
            "The premise derivation is still unverified: " + failure_classification,
        )
    return "", ""



def _premise_name_referenced_by_candidate(
    source: str,
    *,
    premise_name: str,
    declaration_name: str,
) -> bool:
    premise = str(premise_name or "").strip()
    if not premise:
        return False
    normalized_premise = _normalize_premise_identifier(premise)
    if not normalized_premise:
        return False
    declaration_segments = {
        segment
        for segment in re.split(r"[_'.]+", str(declaration_name or ""))
        if segment
    }
    if premise in declaration_segments:
        return True
    if normalized_premise == _normalize_premise_identifier(declaration_name):
        return True
    for identifier in re.findall(r"[A-Za-z_][A-Za-z0-9_'.]*", str(source or "")):
        if identifier == premise:
            return True
        if premise in {
            segment for segment in re.split(r"[_'.]+", identifier) if segment
        }:
            return True
        if normalized_premise == _normalize_premise_identifier(identifier):
            return True
    return False



def _premise_candidate_vacuous(
    source: str,
    *,
    declaration_name: str = "",
) -> bool:
    text = re.sub(
        r"\s+",
        " ",
        _lean_theorem_text_without_comments(
            source,
            declaration_name=declaration_name,
        ),
    )
    if re.search(r"theorem\s+\w+[^:]*:\s*True\s*:=", text):
        return True
    if "exact True.intro" in text:
        return True
    return False


def _candidate_assumes_forbidden_premise(
    source: str,
    *,
    declaration_name: str = "",
    premise_name: str,
    premise_target_type: str,
    forbidden_as_adapter_assumption: bool,
    allowed_source_binder_names: tuple[str, ...] = (),
) -> bool:
    if not forbidden_as_adapter_assumption:
        return False
    header = _lean_theorem_header_without_comments(
        source,
        declaration_name=declaration_name,
    )
    if premise_name and re.search(rf"\(\s*{re.escape(premise_name)}\b", header):
        return True
    target = _normalize_lean_binder_type(premise_target_type)
    if not target:
        return False
    for binder in re.findall(r"\(([^()]*)\)", header):
        if ":" not in binder:
            continue
        name, binder_type = binder.split(":", 1)
        binder_name = name.strip().split()[0] if name.strip() else ""
        if binder_name in allowed_source_binder_names:
            continue
        if _normalize_lean_binder_type(binder_type) == target:
            return True
    return False


def _adapter_object_names_requiring_source_instantiation(
    *,
    premise_target_type: str,
    row: Mapping[str, Any] | None = None,
    candidate_request: Mapping[str, Any],
) -> tuple[str, ...]:
    explicit = _str_tuple(
        (row or {}).get("adapter_object_names_requiring_source_instantiation", [])
        or (row or {}).get(
            "source_to_bridge_adapter_object_names_requiring_source_instantiation",
            [],
        )
        or
        candidate_request.get("adapter_object_names_requiring_source_instantiation", [])
    )
    if explicit:
        return explicit
    target = str(premise_target_type or "")
    default_adapter_object_names = _policy_source_to_bridge_adapter_object_names(
        context={**dict(candidate_request), **dict(row or {})},
    )
    names = [
        name
        for name in default_adapter_object_names
        if name in target
    ]
    if candidate_request.get("bridge_object_instantiation_policy"):
        names.extend(default_adapter_object_names)
    return tuple(dict.fromkeys(name for name in names if name))


def _adapter_object_contract_phrase(adapter_object_names: Sequence[str]) -> str:
    names = tuple(
        dict.fromkeys(
            str(name).strip()
            for name in adapter_object_names
            if str(name).strip()
        )
    )
    if not names:
        return (
            "source-to-bridge adapter objects required by the semantic "
            "dependency rows"
        )
    return f"the listed adapter objects {_human_join(names)}"


def _human_join(values: Sequence[str]) -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _candidate_uninstantiated_adapter_object_binders(
    source: str,
    *,
    declaration_name: str = "",
    adapter_object_names: tuple[str, ...],
) -> tuple[str, ...]:
    wanted = tuple(dict.fromkeys(str(name).strip() for name in adapter_object_names if str(name).strip()))
    if not wanted:
        return ()
    header = _lean_theorem_header_without_comments(
        source,
        declaration_name=declaration_name,
    )
    found: list[str] = []
    for inner in _top_level_parenthesized_groups(header):
        if ":" not in inner:
            continue
        names_text, _target = inner.split(":", 1)
        binder_names = {name.strip() for name in names_text.split() if name.strip()}
        for name in wanted:
            if name in binder_names:
                found.append(name)
    return tuple(dict.fromkeys(found))


def _normalize_lean_binder_type(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _lean_theorem_header_without_comments(
    source: str,
    *,
    declaration_name: str = "",
) -> str:
    theorem_text = _lean_theorem_text_without_comments(
        source,
        declaration_name=declaration_name,
    )
    proof_match = re.search(r"\s:=\s*by\b|\s:=\s*", theorem_text)
    if proof_match:
        theorem_text = theorem_text[: proof_match.start()]
    return theorem_text


def _lean_theorem_text_without_comments(
    source: str,
    *,
    declaration_name: str = "",
) -> str:
    text = _strip_lean_comments(source)
    if declaration_name:
        declaration_pattern = re.compile(
            rf"\btheorem\s+{re.escape(declaration_name)}\b"
        )
        theorem_match = declaration_pattern.search(text)
    else:
        theorem_match = re.search(r"\btheorem\s+\w+\b", text)
    if not theorem_match:
        return text
    theorem_text = text[theorem_match.start() :]
    next_decl = re.search(
        r"\n\s*(?:theorem|lemma|def)\s+[A-Za-z_][A-Za-z0-9_'.]*\b",
        theorem_text[1:],
    )
    if next_decl:
        theorem_text = theorem_text[: 1 + next_decl.start()]
    return theorem_text


def _strip_lean_comments(source: str) -> str:
    without_block_comments = re.sub(r"/-.*?-/", "", source, flags=re.DOTALL)
    return "\n".join(line.split("--", 1)[0] for line in without_block_comments.splitlines())


def _forbidden_tokens(source: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for token in FORBIDDEN_ARTIFACT_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", source):
            tokens.append(token)
    placeholder_patterns = (
        ("c_style_comment_placeholder", r"/\*|\*/"),
        ("placeholder_text", r"\bplaceholder\b"),
        ("todo_marker", r"\bTODO\b"),
        ("interactive_hole", r"\bby\?"),
    )
    for label, pattern in placeholder_patterns:
        if re.search(pattern, source, flags=re.IGNORECASE):
            tokens.append(label)
    return tuple(dict.fromkeys(tokens))


def _resolve_artifact_path(*, base_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidates = [base_dir / path]
    parts = path.parts
    if len(parts) >= 2 and parts[0] == base_dir.parent.name:
        candidates.append(base_dir.parent.parent / path)
    if parts and parts[0] == base_dir.name:
        candidates.append(base_dir.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object row")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _safe_identifier(value: str) -> str:
    safe = re.sub(r"\W+", "_", value.strip())
    safe = safe.strip("_")
    if not safe:
        return "source_to_bridge_premise"
    if safe[0].isdigit():
        safe = "source_to_bridge_premise_" + safe
    return safe


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = [values]
    return tuple(str(value).strip() for value in values or [] if str(value).strip())


def _first_nonempty_str_from_mapping_sources(
    keys: Sequence[str],
    *sources: Mapping[str, Any],
) -> str:
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        mappings: list[Mapping[str, Any]] = [source]
        input_summary = source.get("input_summary", {})
        if isinstance(input_summary, Mapping):
            mappings.append(input_summary)
        for mapping in mappings:
            for key in keys:
                value = mapping.get(key, "")
                if isinstance(value, (list, tuple)):
                    value = next(
                        (item for item in value if str(item or "").strip()),
                        "",
                    )
                text = str(value or "").strip()
                if text:
                    return text
    return ""


def _proof_body_signature_probe_artifact_path_from_sources(
    *sources: Mapping[str, Any],
) -> str:
    return _first_nonempty_str_from_mapping_sources(
        PROOF_BODY_SIGNATURE_PROBE_ARTIFACT_PATH_KEYS,
        *sources,
    )


def _source_theorem_signature_probe_artifact_path_from_sources(
    *sources: Mapping[str, Any],
) -> str:
    return _first_nonempty_str_from_mapping_sources(
        SOURCE_THEOREM_SIGNATURE_PROBE_ARTIFACT_PATH_KEYS,
        *sources,
    )


def _int_like(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _proof_body_gate_open_target_names_for_rows(
    rows: Sequence[SourceToBridgePremiseDerivationCheckRow],
) -> list[str]:
    names: list[str] = []
    for row in rows:
        if not row.source_theorem_exact_proof_body_gate_open_for_kernel_repair:
            continue
        candidates = row.source_theorem_exact_proof_body_gate_open_target_names or (
            (row.target_theorem_name,) if row.target_theorem_name else ()
        )
        for value in candidates:
            if value and value not in names:
                names.append(value)
    return sorted(names)


def _request_mapping_tuple(values: Any) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for value in values or []:
        if not isinstance(value, Mapping):
            continue
        normalized = {
            str(key): child
            for key, child in value.items()
            if str(key).strip() and child not in (None, "", [], {})
        }
        if normalized:
            rows.append(normalized)
    return tuple(rows)

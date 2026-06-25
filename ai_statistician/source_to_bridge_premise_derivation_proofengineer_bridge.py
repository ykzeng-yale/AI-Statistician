from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .formal_verifier_agentic_proof_execution_artifact_verifier import (
    FORBIDDEN_ARTIFACT_TOKENS,
    _lean_command,
    _run_local_lean,
)
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
DEFAULT_ADAPTER_OBJECT_NAMES_REQUIRING_SOURCE_INSTANTIATION = (
    "covered",
    "rank",
    "BadRanks",
    "α",
    "α_total",
)
BOUNDARY = (
    "Source-to-bridge premise derivation rows are ProofEngineer work items for "
    "deriving closure/bridge premise binders from exact source-theorem "
    "hypotheses. They are not full source theorem proof evidence. A row can "
    "become premise-derivation evidence only when a non-vacuous theorem for the "
    "specific premise compiles under local Lean/AXLE with no forbidden "
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
    adapter_declaration_name: str
    source_theorem_signature_excerpt: tuple[str, ...]
    adapter_signature_excerpt: tuple[str, ...]
    source_context_status: str
    premise_target_status: str
    premise_target_matched_binder: str
    premise_target_type: str
    adapter_instantiation_group_id: str
    required_bridge_premise_names_for_shared_instantiation: tuple[str, ...]
    shared_adapter_instantiation_contract: str
    adapter_object_names_requiring_source_instantiation: tuple[str, ...]
    premise_derivation_gap_kind: str
    premise_derivation_gap_summary: str
    premise_semantic_dependency_status: str
    premise_semantic_dependency_requirements: tuple[str, ...]
    premise_candidate_artifact_path: str
    premise_candidate_declaration_name: str
    premise_candidate_generation_mode: str
    premise_candidate_vacuous: bool
    premise_candidate_assumes_forbidden_premise: bool
    premise_candidate_uninstantiated_adapter_object_binders: tuple[str, ...]
    premise_candidate_references_semantic_anchor: bool
    missing_premise_semantic_anchor_binder_names: tuple[str, ...]
    forbidden_tokens_found: tuple[str, ...]
    premise_candidate_evidence_eligible: bool
    exact_goal_shape_obligation_ids: tuple[str, ...]
    proof_body_goal_excerpt: tuple[str, ...]
    proof_body_attempt_summaries: tuple[str, ...]
    kernel_verified_theorem_reduction_closure_declarations: tuple[str, ...]
    verified_theorem_reduction_closure_artifact_paths: tuple[str, ...]
    kernel_verified_source_theorem_semantic_support_obligation_ids: tuple[str, ...]
    acceptance_gate: str
    local_lean_requested: bool
    local_lean_checked: bool
    local_lean_compiled: bool
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
    for row in rows:
        failure = row.failure_classification or "none"
        by_failure_classification[failure] = by_failure_classification.get(failure, 0) + 1
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
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
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
    source_context = _source_context_from_candidate(
        source_candidate_artifact_path=source_candidate_artifact_path,
        target_declaration=target_declaration,
        adapter_declaration_name=adapter_declaration_name,
    )
    premise_target = _adapter_premise_target_from_signature(
        adapter_signature=source_context["adapter_signature"],
        premise_name=premise_name,
    )
    premise_target_type = str(premise_target.get("premise_type", "") or "")
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
        source = _normalize_lean_source(provided_source)
        source = _inline_dependency_context(source, row=row)
        generation_mode = "formalizer_provided_premise_derivation_candidate"
    else:
        source = _generated_premise_derivation_skeleton(
            declaration_name=declaration_name,
            row=row,
        )
        generation_mode = "proofengineer_generated_premise_derivation_skeleton"
    candidate_path.write_text(source, encoding="utf-8")

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
    )
    semantic_requirements = _premise_semantic_dependency_requirements(
        premise_name=premise_name,
        premise_target_type=premise_target_type,
        source_signature=source_context["source_theorem_signature"],
    )
    exact_source_binders = _request_mapping_tuple(
        row.get("exact_source_theorem_binders", [])
        or candidate_request.get("exact_source_theorem_binders", [])
        or grouped_candidate_request.get("exact_source_theorem_binders", [])
        or _source_theorem_binder_summaries(source_context["source_theorem_signature"])
    )
    semantic_anchor_binders = _request_mapping_tuple(
        row.get("premise_semantic_anchor_binders", [])
        or candidate_request.get("premise_semantic_anchor_binders", [])
        or grouped_candidate_request.get("premise_semantic_anchor_binders", [])
        or _premise_semantic_anchor_binder_summaries(
            premise_name=premise_name,
            premise_target_type=premise_target_type,
            semantic_requirements=semantic_requirements,
            source_binders=tuple(
                dict(item) for item in exact_source_binders if isinstance(item, Mapping)
            ),
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
    theorem_matches = bool(
        re.search(rf"\btheorem\s+{re.escape(declaration_name)}\b", source)
    )
    premise_referenced = bool(
        premise_name and re.search(rf"\b{re.escape(premise_name)}\b", source)
    )
    evidence_eligible = bool(
        provided_source
        and source_binding_contract_present
        and theorem_matches
        and premise_referenced
        and not vacuous
        and not assumes_forbidden_premise
        and not uninstantiated_adapter_object_binders
        and references_semantic_anchor
        and not forbidden_tokens
    )
    local_compiled = False
    local_checked = False
    returncode = 0
    diagnostics: tuple[str, ...] = ()
    if local_lean and evidence_eligible:
        local_checked = True
        if not lean_command:
            returncode = -1
            diagnostics = ("local Lean executable not found",)
        else:
            local_compiled, returncode, diagnostics = _run_local_lean(
                candidate_path,
                lean_command=lean_command,
                lean_project=lean_project,
                timeout_s=lean_timeout,
            )
    elif local_lean and not evidence_eligible:
        diagnostics = (
            "local Lean skipped because premise derivation candidate is not evidence eligible",
        )
    failure = _premise_failure_classification(
        local_lean=local_lean,
        local_compiled=local_compiled,
        provided_source=bool(provided_source),
        evidence_eligible=evidence_eligible,
        theorem_matches=theorem_matches,
        premise_referenced=premise_referenced,
        source_binding_contract_present=source_binding_contract_present,
        vacuous=vacuous,
        assumes_forbidden_premise=assumes_forbidden_premise,
        uninstantiated_adapter_object_binders=uninstantiated_adapter_object_binders,
        references_semantic_anchor=references_semantic_anchor,
        forbidden_tokens=forbidden_tokens,
        diagnostics=diagnostics,
    )
    premise_verified = bool(local_lean and local_compiled and evidence_eligible)
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
        adapter_declaration_name=adapter_declaration_name,
        source_theorem_signature_excerpt=source_context["source_theorem_signature"],
        adapter_signature_excerpt=source_context["adapter_signature"],
        source_context_status=source_context["status"],
        premise_target_status=str(premise_target.get("status", "") or ""),
        premise_target_matched_binder=str(
            premise_target.get("matched_premise_binder", "") or ""
        ),
        premise_target_type=str(premise_target.get("premise_type", "") or ""),
        adapter_instantiation_group_id=adapter_instantiation_group_id,
        required_bridge_premise_names_for_shared_instantiation=(
            required_bridge_premise_names_for_shared_instantiation
        ),
        shared_adapter_instantiation_contract=shared_adapter_instantiation_contract,
        adapter_object_names_requiring_source_instantiation=adapter_object_names,
        premise_derivation_gap_kind=gap_kind,
        premise_derivation_gap_summary=gap_summary,
        premise_semantic_dependency_status=semantic_dependency_status,
        premise_semantic_dependency_requirements=semantic_requirements,
        premise_candidate_artifact_path=str(candidate_path),
        premise_candidate_declaration_name=declaration_name,
        premise_candidate_generation_mode=generation_mode,
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
        proof_body_attempt_summaries=_str_tuple(
            row.get("proof_body_attempt_summaries", [])
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
        local_lean_compiled=local_compiled,
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
        source = str(candidate.get(key, "") or "").strip()
        if source:
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
    adapter_signature = _extract_declaration_signature(
        source,
        adapter_declaration_name,
    )
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
            if _normalize_premise_identifier(name) in {
                "hgoodcovered",
                "hbadevent",
                "hrank",
                "htotal",
            }:
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


def _generated_premise_derivation_skeleton(
    *,
    declaration_name: str,
    row: Mapping[str, Any],
) -> str:
    premise_name = str(row.get("premise_name", "") or "").strip()
    target = str(row.get("target_theorem_name", "") or "").strip()
    required = str(row.get("required_derivation", "") or "").strip()
    acceptance_gate = str(row.get("acceptance_gate", "") or "").strip()
    source_candidate_artifact_path = str(
        row.get("source_candidate_artifact_path", "") or ""
    ).strip()
    adapter_candidate_artifact_path = str(
        row.get("adapter_candidate_artifact_path", "") or ""
    ).strip()
    adapter_declaration_name = str(
        row.get("adapter_declaration_name", "") or ""
    ).strip()
    source_context = _source_context_from_candidate(
        source_candidate_artifact_path=source_candidate_artifact_path,
        target_declaration=str(row.get("target_lean_declaration", "") or "").strip(),
        adapter_declaration_name=adapter_declaration_name,
    )
    premise_target = _adapter_premise_target_from_signature(
        adapter_signature=source_context["adapter_signature"],
        premise_name=premise_name,
    )
    closure_declarations = _str_tuple(
        row.get("kernel_verified_theorem_reduction_closure_declarations", [])
    )[:12]
    closure_artifacts = _str_tuple(
        row.get("verified_theorem_reduction_closure_artifact_paths", [])
    )[:12]
    semantic_support_ids = _str_tuple(
        row.get("kernel_verified_source_theorem_semantic_support_obligation_ids", [])
    )[:12]
    goal_excerpt = _str_tuple(row.get("proof_body_goal_excerpt", []))[:12]
    attempt_summaries = _str_tuple(row.get("proof_body_attempt_summaries", []))[:12]
    exact_goal_shape_ids = _str_tuple(row.get("exact_goal_shape_obligation_ids", []))[:12]
    comment_lines = [
        "This is a generated source-to-bridge premise derivation skeleton, not proof evidence.",
        "Replace the abstract source_hypotheses/bridge_premise placeholders with exact",
        "source theorem hypotheses and prove the named bridge premise before rerunning",
        "the source theorem proof body.",
    ]
    metadata_lines = [
        ("target source theorem", target),
        ("premise name", premise_name),
        ("required derivation", required),
        ("acceptance gate", acceptance_gate),
        ("exact source candidate artifact", source_candidate_artifact_path),
        ("source-to-bridge adapter candidate artifact", adapter_candidate_artifact_path),
        ("source-to-bridge adapter declaration", adapter_declaration_name),
    ]
    metadata_comment = "\n".join(
        f"-- {label}: {_sanitize_comment_text(value)}"
        for label, value in metadata_lines
        if value
    )
    exact_goal_comment = "\n".join(
        f"-- exact goal-shape obligation id: {_sanitize_comment_text(value)}"
        for value in exact_goal_shape_ids
    )
    closure_comment = "\n".join(
        f"-- verified reduction/closure Lean declaration: {_sanitize_comment_text(value)}"
        for value in closure_declarations
    )
    closure_artifact_comment = "\n".join(
        f"-- verified reduction/closure artifact: {_sanitize_comment_text(value)}"
        for value in closure_artifacts
    )
    semantic_support_comment = "\n".join(
        f"-- verified semantic support obligation id: {_sanitize_comment_text(value)}"
        for value in semantic_support_ids
    )
    goal_comment = "\n".join(
        f"-- proof body goal: {_sanitize_comment_text(value)}"
        for value in goal_excerpt
    )
    attempt_comment = "\n".join(
        f"-- proof body attempt: {_sanitize_comment_text(value)}"
        for value in attempt_summaries
    )
    source_signature_comment = "\n".join(
        f"-- exact source theorem signature: {_sanitize_comment_text(value)}"
        for value in source_context["source_theorem_signature"]
    )
    adapter_signature_comment = "\n".join(
        f"-- current adapter signature: {_sanitize_comment_text(value)}"
        for value in source_context["adapter_signature"]
    )
    premise_target_comment = "\n".join(
        [
            "-- premise target status: "
            + _sanitize_comment_text(str(premise_target["status"])),
            "-- matched adapter premise binder: "
            + _sanitize_comment_text(str(premise_target["matched_premise_binder"])),
            "-- extracted premise target: "
            + _sanitize_comment_text(str(premise_target["premise_type"])),
        ]
    )
    semantic_requirements = _premise_semantic_dependency_requirements(
        premise_name=premise_name,
        premise_target_type=str(premise_target["premise_type"]),
        source_signature=source_context["source_theorem_signature"],
    )
    exact_source_binders = _source_theorem_binder_summaries(
        source_context["source_theorem_signature"]
    )
    semantic_anchor_binders = _premise_semantic_anchor_binder_summaries(
        premise_name=premise_name,
        premise_target_type=str(premise_target["premise_type"]),
        semantic_requirements=semantic_requirements,
        source_binders=exact_source_binders,
    )
    semantic_requirement_comment = "\n".join(
        f"-- required source-to-bridge semantic dependency: {_sanitize_comment_text(value)}"
        for value in semantic_requirements
    )
    source_binder_comment = "\n".join(
        "-- exact source binder: "
        + _sanitize_comment_text(
            str(binder.get("name", "") or "")
            + " : "
            + str(binder.get("type", "") or "")
            + " ["
            + str(binder.get("role", "") or "")
            + "]"
        )
        for binder in exact_source_binders
    )
    semantic_anchor_comment = "\n".join(
        "-- required semantic anchor binder: "
        + _sanitize_comment_text(
            str(binder.get("name", "") or "")
            + " : "
            + str(binder.get("type", "") or "")
            + " ["
            + str(binder.get("role", "") or "")
            + "]"
        )
        for binder in semantic_anchor_binders
    )
    theorem_statement = _premise_derivation_theorem_statement(
        declaration_name=declaration_name,
        premise_target=premise_target,
    )
    block_comment = "\n".join(comment_lines)
    return (
        "import Mathlib\n\n"
        "namespace AIStatisticianSourceToBridgePremiseDerivation\n\n"
        "/-\n"
        f"{block_comment}\n"
        "-/\n"
        f"{metadata_comment}\n"
        f"{exact_goal_comment}\n"
        f"{closure_comment}\n"
        f"{closure_artifact_comment}\n"
        f"{semantic_support_comment}\n"
        f"{goal_comment}\n"
        f"{attempt_comment}\n"
        f"-- source context status: {_sanitize_comment_text(source_context['status'])}\n"
        f"{source_signature_comment}\n"
        f"{adapter_signature_comment}\n"
        f"{premise_target_comment}\n"
        f"{semantic_requirement_comment}\n"
        f"{source_binder_comment}\n"
        f"{semantic_anchor_comment}\n"
        "-- bridge object instantiation policy: adapter objects such as covered, "
        "rank, BadRanks, α, and α_total are not free proof assumptions for the "
        "source theorem; define or instantiate them from exact source binders, "
        "or report the missing semantic primitive as a blocker.\n"
        f"{theorem_statement}"
        "  -- ProofEngineer must derive the bridge premise from exact source hypotheses.\n"
        "  fail_if_success trivial\n\n"
        "end AIStatisticianSourceToBridgePremiseDerivation\n"
    )


def _premise_derivation_theorem_statement(
    *,
    declaration_name: str,
    premise_target: Mapping[str, Any],
) -> str:
    premise_type = str(premise_target.get("premise_type", "") or "").strip()
    context_lines = tuple(
        str(line).rstrip()
        for line in premise_target.get("context_lines", ()) or ()
        if str(line).strip()
    )
    if not premise_type or not context_lines:
        return (
            f"theorem {declaration_name} (source_hypotheses bridge_premise : Prop) "
            "(hsource : source_hypotheses) :\n"
            "    bridge_premise := by\n"
        )
    context = "\n".join(context_lines)
    return (
        f"theorem {declaration_name}\n"
        f"{context} :\n"
        f"    {premise_type} := by\n"
    )


def _premise_semantic_dependency_requirements(
    *,
    premise_name: str,
    premise_target_type: str,
    source_signature: tuple[str, ...],
) -> tuple[str, ...]:
    """Infer source-to-bridge semantic dependencies for the next LLM/prover pass.

    These rows are routing hints. They are not proof evidence and cannot close a
    premise without a later local Lean/AXLE check of a non-vacuous derivation.
    """

    normalized_name = _normalize_premise_identifier(premise_name)
    target = re.sub(r"\s+", " ", str(premise_target_type or "").strip())
    source_text = "\n".join(source_signature)
    requirements: list[str] = []
    if normalized_name == "hgoodcovered" or "ᶜ ⊆ covered" in target:
        requirements.extend(
            [
                "define covered from the exact source coverage event using hC",
                "define rank and BadRanks from the exact order-statistic threshold hq",
                "prove good-rank containment: rank outside BadRanks implies the covered event",
            ]
        )
    if normalized_name == "hbadevent" or target.startswith("MeasurableSet"):
        requirements.extend(
            [
                "provide measurability of the rank map or of the finite bad-rank event",
                "connect BadRanks to a finite/rank-indexed event in the exact source environment",
            ]
        )
    if normalized_name == "hrank" or "P {ω | rank ω =" in target:
        requirements.extend(
            [
                "derive the rank point-mass bound from exact exchangeability hexch",
                "formalize the tie policy/rank-uniformity lemma needed for bad-rank probabilities",
                "define α on ranks so each bad-rank event has probability bounded by α r",
            ]
        )
    if normalized_name in {"htotal", "h_total"} or "∑ r ∈ BadRanks" in target:
        requirements.extend(
            [
                "define α_total from alpha and the conformal rank threshold",
                "prove the finite bad-rank budget sum bound for α over BadRanks",
            ]
        )
    if not requirements and target:
        requirements.append(
            "formalize exact source-to-bridge definitions for the identifiers in: "
            + target[:180]
        )
    if "hC" in source_text and any("covered" in item for item in requirements):
        requirements.append(
            "use the exact source hC binder as the semantic anchor for the coverage event"
        )
    if "hexch" in source_text and any("exchangeability" in item for item in requirements):
        requirements.append(
            "use the exact source hexch binder as the semantic anchor for rank uniformity"
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
        grouped_candidate_request = grouped_requests_by_group_id.get(
            row.adapter_instantiation_group_id,
            {},
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
                "target_theorem_goal_ids": list(row.target_theorem_goal_ids),
                "source_adapter_check_id": row.source_adapter_check_id,
                "source_adapter_work_order_id": row.source_adapter_work_order_id,
                "work_order_id": row.work_order_id,
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
        "adapter_instantiation_group_id": row.adapter_instantiation_group_id,
        "required_bridge_premise_names_for_shared_instantiation": list(
            row.required_bridge_premise_names_for_shared_instantiation
        ),
        "shared_adapter_instantiation_contract": (
            row.shared_adapter_instantiation_contract
        ),
        "adapter_object_names_requiring_source_instantiation": list(
            row.adapter_object_names_requiring_source_instantiation
        ),
        "premise_derivation_gap_kind": row.premise_derivation_gap_kind,
                "premise_derivation_gap_summary": row.premise_derivation_gap_summary,
                "premise_semantic_dependency_status": (
                    row.premise_semantic_dependency_status
                ),
                "premise_semantic_dependency_requirements": list(
                    row.premise_semantic_dependency_requirements
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
                "kernel_verified_source_to_bridge_premise_derivation_ids": (
                    [row.premise_derivation_check_id]
                    if row.premise_derivation_kernel_verified
                    else []
                ),
                "failure_classification": row.failure_classification,
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
                grouped_request.get(
                    "adapter_object_names_requiring_source_instantiation",
                    [],
                )
                or []
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
            "runtime_queue_status": "PENDING_GROUPED_SOURCE_TO_BRIDGE_PREMISE_DERIVATION",
            "input_summary": dict(grouped_request),
            "target_behavior": (
                "Generate one shared source-to-bridge premise derivation candidate "
                "that defines the adapter objects once from exact source-theorem "
                "binders and proves every listed premise name without assuming those "
                "premises. This grouped request is not proof evidence; only local "
                "Lean/AXLE kernel verification of each premise derivation can promote it."
            ),
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
    seen: set[tuple[str, str, str]] = set()
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
            key = (group_id, target_lean_declaration, adapter_object)
            if key in seen:
                continue
            seen.add(key)
            work_order_id = (
                "source_to_bridge_adapter_object_semantic_definition_work_order:"
                + stable_hash([group_id, target_lean_declaration, adapter_object])[:20]
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
                    "target_theorem_goal_ids": list(target_goal_ids),
                    "placeholder_symbol": adapter_object,
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
                    "source_to_bridge_grouped_premise_derivation_candidate_request": (
                        source_grouped_request
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
                        "placeholder_symbol": adapter_object,
                        "adapter_object_name": adapter_object,
                        "source_to_bridge_adapter_instantiation_group_id": group_id,
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
    return work_orders


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
        shared_contract = next(
            (
                row.shared_adapter_instantiation_contract
                for row in group_rows
                if row.shared_adapter_instantiation_contract
            ),
            "",
        ) or (
            "Use one shared source-derived instantiation of adapter objects "
            "across all listed premise_names; do not prove grouped premises "
            "with incompatible definitions."
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
                "candidate_contract": (
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
                ),
                "forbidden_actions": [
                    "do not split this group into incompatible adapter-object definitions",
                    "do not assume any listed bridge premise as a binder",
                    "do not satisfy semantic-anchor requirements with comments or unused have/let aliases",
                    "do not put adapter objects such as covered, rank, BadRanks, α, or α_total in the theorem header as free binders",
                    "do not add axiom, sorry, admit, unsafe, or placeholder definitions",
                    "do not claim full source theorem proof from this request",
                ],
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
    source_binders = row.exact_source_theorem_binders or _source_theorem_binder_summaries(
        row.source_theorem_signature_excerpt
    )
    semantic_anchor_binders = (
        row.premise_semantic_anchor_binders
        or _premise_semantic_anchor_binder_summaries(
            premise_name=row.premise_name,
            premise_target_type=row.premise_target_type,
            semantic_requirements=row.premise_semantic_dependency_requirements,
            source_binders=source_binders,
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
        "adapter_instantiation_group_id": row.adapter_instantiation_group_id,
        "required_bridge_premise_names_for_shared_instantiation": list(
            row.required_bridge_premise_names_for_shared_instantiation
            or shared_premise_names
            or ((row.premise_name,) if row.premise_name else ())
        ),
        "shared_adapter_instantiation_contract": (
            row.shared_adapter_instantiation_contract
            or (
                "All source-to-bridge premise candidates with the same "
                "adapter_instantiation_group_id must use one shared definition of "
                "covered, rank, BadRanks, α, and α_total from the exact source "
                "theorem binders. Independently proving premises with incompatible "
                "adapter-object definitions cannot be combined into source theorem "
                "proof evidence."
            )
        ),
        "premise_candidate_declaration_name": row.premise_candidate_declaration_name,
        "premise_candidate_artifact_path": row.premise_candidate_artifact_path,
        "premise_candidate_generation_mode": row.premise_candidate_generation_mode,
        "premise_derivation_gap_kind": row.premise_derivation_gap_kind,
        "premise_derivation_gap_summary": row.premise_derivation_gap_summary,
        "premise_semantic_dependency_status": row.premise_semantic_dependency_status,
        "premise_semantic_dependency_requirements": list(
            row.premise_semantic_dependency_requirements
        ),
        "source_candidate_artifact_path": row.source_candidate_artifact_path,
        "adapter_candidate_artifact_path": row.adapter_candidate_artifact_path,
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
            "Adapter objects appearing in premise_target_type, such as covered, "
            "rank, BadRanks, α, and α_total, are not source-theorem assumptions. "
            "The candidate must define or instantiate them from the exact source "
            "binders, or report a semantic blocker instead of treating them as "
            "arbitrary variables."
        ),
        "adapter_object_names_requiring_source_instantiation": list(
            row.adapter_object_names_requiring_source_instantiation
        ),
        "exact_goal_shape_obligation_ids": list(row.exact_goal_shape_obligation_ids),
        "proof_body_goal_excerpt": list(row.proof_body_goal_excerpt),
        "proof_body_attempt_summaries": list(row.proof_body_attempt_summaries),
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
            "Return a non-vacuous Lean theorem with exactly the listed "
            "premise_candidate_declaration_name, proving premise_target_type from "
            "exact source-theorem hypotheses and semantic dependencies. Use the "
            "premise_semantic_anchor_binders as the preferred source binders for "
            "this premise and reference every required_semantic_anchor_reference_names "
            "entry in the Lean source outside comments. Do not treat adapter "
            "objects such as covered, rank, BadRanks, α, or α_total as arbitrary "
            "free variables or theorem parameters when they must be instantiated "
            "from the source theorem. "
            "Do not reintroduce the forbidden adapter premise as an assumption."
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
) -> tuple[dict[str, str], ...]:
    binders: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in source_signature:
        for name, binder_type in _parse_named_binders(str(line).strip()):
            if name in seen:
                continue
            seen.add(name)
            binders.append(
                {
                    "name": name,
                    "type": binder_type,
                    "role": _source_binder_role(name=name, binder_type=binder_type),
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


def _source_binder_role(*, name: str, binder_type: str) -> str:
    normalized = _normalize_premise_identifier(name)
    type_text = str(binder_type or "")
    if normalized in {"hexch", "hexchangeability"} or "Exchangeable" in type_text:
        return "exchangeability_anchor"
    if normalized == "hq" or "orderStat" in type_text:
        return "quantile_definition_anchor"
    if normalized == "hc":
        return "coverage_event_anchor"
    if normalized in {"halpha", "alpha"}:
        return "miscoverage_level_anchor"
    if normalized in {"hn2", "n2", "m"}:
        return "calibration_size_anchor"
    if normalized == "s":
        return "score_process_anchor"
    if normalized in {"qhat", "q_hat"}:
        return "threshold_function_anchor"
    if normalized == "c":
        return "prediction_set_family_anchor"
    if normalized.startswith("h"):
        return "source_hypothesis"
    return "source_parameter"


def _premise_semantic_anchor_binder_summaries(
    *,
    premise_name: str,
    premise_target_type: str,
    semantic_requirements: tuple[str, ...],
    source_binders: tuple[dict[str, str], ...],
) -> tuple[dict[str, str], ...]:
    text = " ".join(
        [
            premise_name,
            premise_target_type,
            *semantic_requirements,
        ]
    ).lower()
    wanted: set[str] = set()
    if any(token in text for token in ("covered", "coverage event", "hc")):
        wanted.update({"hC", "C", "q_hat", "s"})
    if any(token in text for token in ("exchangeability", "exchangeable", "hexch")):
        wanted.update({"hexch", "s", "P"})
    if any(
        token in text
        for token in ("rank", "badranks", "quantile", "order-statistic", "orderstat", "hq")
    ):
        wanted.update({"hq", "q_hat", "s", "n2", "hn2", "alpha", "halpha"})
    if any(token in text for token in ("alpha", "α", "budget", "total")):
        wanted.update({"alpha", "halpha", "n2", "hn2"})
    if not wanted:
        return source_binders[:8]
    normalized_wanted = {_normalize_premise_identifier(name) for name in wanted}
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
    local_compiled: bool,
    provided_source: bool,
    evidence_eligible: bool,
    theorem_matches: bool,
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
    if not theorem_matches:
        return "premise_derivation_candidate_wrong_declaration"
    if not premise_referenced:
        return "premise_derivation_candidate_missing_premise_reference"
    if not evidence_eligible:
        return "premise_derivation_candidate_not_evidence_eligible"
    if not local_lean:
        return "premise_derivation_candidate_not_checked"
    if local_compiled:
        return ""
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
        and generation_mode != "proofengineer_generated_premise_derivation_skeleton"
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
        if generation_mode == "proofengineer_generated_premise_derivation_skeleton":
            return (
                "concrete_premise_target_lacks_nonvacuous_derivation_candidate",
                "The adapter premise target is known, but the bridge only "
                "materialized a non-evidence skeleton. Provide or synthesize a "
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


def _normalize_lean_source(source: str) -> str:
    if "import " not in source:
        return "import Mathlib\n\n" + source.rstrip() + "\n"
    return source.rstrip() + "\n"


def _inline_dependency_context(source: str, *, row: Mapping[str, Any]) -> str:
    dependency_sources: list[str] = []
    for raw_path in _str_tuple(
        row.get("verified_theorem_reduction_closure_artifact_paths", [])
    )[:3]:
        path_text = str(raw_path or "").strip()
        if not path_text.endswith(".lean"):
            continue
        try:
            dependency_source = Path(path_text).expanduser().read_text(
                encoding="utf-8"
            )
        except OSError:
            continue
        if dependency_source.strip():
            dependency_sources.append(dependency_source)
    if not dependency_sources:
        return source
    return _merge_lean_sources([*dependency_sources, source])


def _merge_lean_sources(sources: list[str]) -> str:
    imports: list[str] = []
    bodies: list[str] = []
    for source in sources:
        body_lines: list[str] = []
        for line in str(source or "").rstrip().splitlines():
            if re.match(r"^\s*import\s+", line):
                normalized = line.strip()
                if normalized not in imports:
                    imports.append(normalized)
                continue
            body_lines.append(line)
        body = "\n".join(body_lines).strip()
        if body:
            bodies.append(body)
    import_block = "\n".join(imports) or "import Mathlib"
    return import_block + "\n\n" + "\n\n".join(bodies).rstrip() + "\n"


def _sanitize_comment_text(value: str) -> str:
    text = value.replace("\n", " ")
    replacements = {
        "sorry": "<proof-gap-redacted>",
        "admit": "<placeholder-redacted>",
        "axiom": "<assumption-redacted>",
        "unsafe": "<policy-redacted>",
    }
    for token in FORBIDDEN_ARTIFACT_TOKENS:
        text = re.sub(
            rf"\b{re.escape(token)}\b",
            replacements.get(token, "<forbidden-token-redacted>"),
            text,
        )
    return text


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
        _name, binder_type = binder.split(":", 1)
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
    names = [
        name
        for name in DEFAULT_ADAPTER_OBJECT_NAMES_REQUIRING_SOURCE_INSTANTIATION
        if name in target
    ]
    if candidate_request.get("bridge_object_instantiation_policy"):
        names.extend(DEFAULT_ADAPTER_OBJECT_NAMES_REQUIRING_SOURCE_INSTANTIATION)
    return tuple(dict.fromkeys(name for name in names if name))


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

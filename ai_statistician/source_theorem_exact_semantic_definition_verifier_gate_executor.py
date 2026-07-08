from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .formal_verifier_agentic_proof_execution_artifact_verifier import (
    FORBIDDEN_ARTIFACT_TOKENS,
)
from .source_theorem_formal_environment_proofengineer_bridge import (
    _lean_command,
    _run_local_lean,
)
from .source_theorem_exact_semantic_definition_source_lookup import (
    EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS,
    normalize_exact_semantic_definition_signature_probe_context,
)


ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionTypecheckedReviewVerifierGateExecutorManifest"
)
RESULT_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionTypecheckedReviewVerifierGateResult"
)
APPROVED_PACKET_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionVerifierApprovedReviewPacket"
)
LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_typechecked_review_verifier_gate_execution"
)
PROOF_EVIDENCE_STATUS = (
    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
)
APPROVED_PACKET_PROOF_EVIDENCE_STATUS = (
    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_APPROVED_NOT_SOURCE_THEOREM_PROOF"
)
APPROVED_TYPECHECK_STATUS = (
    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_APPROVED_LOCAL_LEAN_COMPILED_NOT_PROOF"
)
BOUNDARY = (
    "Exact semantic-definition verifier-gate rows check local Lean typechecking, "
    "static definition shape, and source-anchor availability for a typechecked "
    "definition candidate. They are semantic-readiness gate evidence only; they "
    "are not source theorem proof. Source theorem proof evidence still requires "
    "local Lean/AXLE kernel verification of the intended target theorem."
)


def _bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def run_source_theorem_exact_semantic_definition_verifier_gate_executor(
    *,
    out_dir: Path,
    recheck_manifest: Path | None = None,
    work_orders_jsonl: Path | None = None,
    local_lean: bool = False,
    lean_project: Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Execute typechecked exact semantic-definition verifier-gate work orders."""

    work_orders_path = resolve_verifier_gate_work_orders_path(
        recheck_manifest=recheck_manifest,
        work_orders_jsonl=work_orders_jsonl,
    )
    work_orders = [
        dict(row)
        for row in _read_jsonl(work_orders_path)
        if isinstance(row, Mapping)
    ]
    command = lean_command or _lean_command(lean_project)
    results = [
        _verifier_gate_result(
            row,
            local_lean=local_lean,
            lean_project=lean_project,
            lean_timeout=lean_timeout,
            lean_command=command,
        )
        for row in work_orders
    ]
    approved_packets = [
        _approved_review_packet(row)
        for row in results
        if row.get("verifier_gate_status") == "VERIFIER_APPROVED_FOR_PROOF_BODY_RECHECK"
    ]
    runtime_learning_rows = [_runtime_learning_row(row) for row in results]
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_verifier_gate_results.jsonl"
    )
    approved_packets_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_verifier_approved_review_packets.jsonl"
    )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_verifier_gate_executor_manifest.json"
    )
    _write_jsonl(results_path, results)
    _write_jsonl(approved_packets_path, approved_packets)
    _write_jsonl(learning_path, runtime_learning_rows)
    status_counts = Counter(
        str(row.get("verifier_gate_status", "") or "") for row in results
    )
    blocker_counts = Counter(
        blocker
        for row in results
        for blocker in row.get("verifier_gate_blockers", []) or []
    )
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_recheck_manifest": str(recheck_manifest or ""),
        "source_verifier_gate_work_orders_jsonl": str(work_orders_path),
        "verifier_gate_results_jsonl": str(results_path),
        "verifier_approved_review_packets_jsonl": str(approved_packets_path),
        "runtime_learning_rows_jsonl": str(learning_path),
        "local_lean_requested": bool(local_lean),
        "local_lean_project": str(lean_project or ""),
        "local_lean_timeout_seconds": int(lean_timeout),
        "lean_command": list(command),
        "n_work_orders": len(work_orders),
        "n_results": len(results),
        "n_local_lean_checked": sum(
            1 for row in results if row.get("local_lean_checked")
        ),
        "n_local_lean_compiled": sum(
            1 for row in results if row.get("local_lean_compiled")
        ),
        "n_verifier_approved": len(approved_packets),
        "n_work_orders_from_pseudo_formal": sum(
            1 for row in work_orders if _has_pseudo_formal_origin(row)
        ),
        "n_work_orders_from_formalizer_pf_component_gate": sum(
            1 for row in work_orders if _has_formalizer_pf_component_gate_origin(row)
        ),
        "n_results_from_pseudo_formal": sum(
            1 for row in results if _has_pseudo_formal_origin(row)
        ),
        "n_results_from_formalizer_pf_component_gate": sum(
            1 for row in results if _has_formalizer_pf_component_gate_origin(row)
        ),
        "n_local_lean_checked_from_pseudo_formal": sum(
            1
            for row in results
            if row.get("local_lean_checked") and _has_pseudo_formal_origin(row)
        ),
        "n_local_lean_checked_from_formalizer_pf_component_gate": sum(
            1
            for row in results
            if row.get("local_lean_checked")
            and _has_formalizer_pf_component_gate_origin(row)
        ),
        "n_local_lean_compiled_from_pseudo_formal": sum(
            1
            for row in results
            if row.get("local_lean_compiled") and _has_pseudo_formal_origin(row)
        ),
        "n_local_lean_compiled_from_formalizer_pf_component_gate": sum(
            1
            for row in results
            if row.get("local_lean_compiled")
            and _has_formalizer_pf_component_gate_origin(row)
        ),
        "n_verifier_approved_from_pseudo_formal": sum(
            1 for row in approved_packets if _has_pseudo_formal_origin(row)
        ),
        "n_verifier_approved_from_formalizer_pf_component_gate": sum(
            1
            for row in approved_packets
            if _has_formalizer_pf_component_gate_origin(row)
        ),
        "n_verifier_blocked_from_pseudo_formal": sum(
            1
            for row in results
            if row.get("verifier_gate_status")
            != "VERIFIER_APPROVED_FOR_PROOF_BODY_RECHECK"
            and _has_pseudo_formal_origin(row)
        ),
        "n_verifier_blocked_from_formalizer_pf_component_gate": sum(
            1
            for row in results
            if row.get("verifier_gate_status")
            != "VERIFIER_APPROVED_FOR_PROOF_BODY_RECHECK"
            and _has_formalizer_pf_component_gate_origin(row)
        ),
        "source_pseudo_formal_work_order_ids": _source_pseudo_formal_ids(
            results,
            "source_pseudo_formal_work_order_id",
        ),
        "source_pseudo_formal_block_ids": _source_pseudo_formal_ids(
            results,
            "source_pseudo_formal_block_id",
        ),
        "source_prompt_scaffold_ids": _source_pseudo_formal_ids(
            results,
            "source_prompt_scaffold_id",
        ),
        "source_prompt_scaffold_kinds": _source_pseudo_formal_ids(
            results,
            "source_prompt_scaffold_kind",
        ),
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": (
            _formalizer_pf_component_gate_exact_rows_jsonl_paths(results)
        ),
        "n_verifier_blocked": sum(
            1
            for row in results
            if row.get("verifier_gate_status")
            != "VERIFIER_APPROVED_FOR_PROOF_BODY_RECHECK"
        ),
        "n_source_anchor_context_missing": int(
            blocker_counts.get("source_anchor_context_missing", 0)
        ),
        "n_known_gaps_unresolved": int(
            blocker_counts.get("known_gaps_unresolved", 0)
        ),
        "n_candidate_known_gaps_comment_present": int(
            blocker_counts.get("candidate_known_gaps_comment_present", 0)
        ),
        "status_counts": dict(sorted(status_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "source_theorem_ready_for_exact_proof_body": bool(approved_packets)
        and len(approved_packets) == len(results),
        "source_theorem_kernel_verified": False,
        "source_theorem_kernel_evidence_eligible": False,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def resolve_verifier_gate_work_orders_path(
    *,
    recheck_manifest: Path | None = None,
    work_orders_jsonl: Path | None = None,
) -> Path:
    if work_orders_jsonl is not None:
        return work_orders_jsonl
    if recheck_manifest is None:
        raise ValueError("recheck_manifest or work_orders_jsonl is required")
    payload = json.loads(recheck_manifest.read_text(encoding="utf-8"))
    raw_path = str(payload.get("verifier_gate_work_orders_jsonl", "") or "")
    if not raw_path:
        raise ValueError(
            f"manifest does not list verifier_gate_work_orders_jsonl: {recheck_manifest}"
        )
    path = Path(raw_path)
    if not path.exists():
        candidate = recheck_manifest.parent / raw_path
        if candidate.exists():
            path = candidate
    return path


def _verifier_gate_result(
    row: Mapping[str, Any],
    *,
    local_lean: bool,
    lean_project: Path | None,
    lean_timeout: int,
    lean_command: tuple[str, ...],
) -> dict[str, Any]:
    candidate_path_text = str(
        row.get("candidate_artifact_path", "")
        or row.get("definition_only_candidate_artifact_path", "")
        or ""
    ).strip()
    candidate_path = (
        Path(candidate_path_text).expanduser() if candidate_path_text else None
    )
    candidate_file_exists = bool(candidate_path and candidate_path.exists())
    source = ""
    if candidate_file_exists and candidate_path is not None:
        source = candidate_path.read_text(encoding="utf-8")
    code = _strip_lean_comments(source)
    placeholder = str(row.get("placeholder_symbol", "") or "").strip()
    blockers: list[str] = []
    local_lean_checked = False
    local_lean_compiled = False
    returncode = 0
    diagnostics: tuple[str, ...] = ()
    if not candidate_path_text:
        blockers.append("candidate_artifact_path_missing")
    elif not candidate_file_exists:
        blockers.append("candidate_artifact_file_missing")
    if local_lean:
        if not lean_command:
            returncode = -1
            diagnostics = ("lean executable not found",)
            blockers.append("local_lean_unavailable")
        elif candidate_file_exists and candidate_path is not None:
            local_lean_checked = True
            local_lean_compiled, returncode, diagnostics = _run_local_lean(
                candidate_path,
                lean_command=lean_command,
                lean_project=lean_project,
                timeout_s=lean_timeout,
            )
            if not local_lean_compiled:
                blockers.append("local_lean_failed")
        elif candidate_path_text:
            blockers.append("local_lean_candidate_file_missing")
    else:
        blockers.append("local_lean_verifier_not_requested")
    forbidden_tokens = _forbidden_tokens_in_code(code)
    if forbidden_tokens:
        blockers.append("forbidden_tokens_present")
    if placeholder:
        if not _has_placeholder_definition(code, placeholder):
            blockers.append("placeholder_definition_missing")
        if _has_vacuous_placeholder_definition(code, placeholder):
            blockers.append("vacuous_placeholder_definition")
    else:
        blockers.append("placeholder_symbol_missing")
    semantic_review_decision = str(row.get("semantic_review_decision", "") or "")
    semantic_review_evidence = _string_list(row.get("semantic_review_evidence", []))
    if semantic_review_decision != "approved_definition_candidate":
        blockers.append("llm_semantic_review_not_approved")
    if not semantic_review_evidence:
        blockers.append("semantic_review_evidence_missing")
    source_context = _source_anchor_context(row)
    candidate_definition_request = _first_context_mapping(
        row, "candidate_definition_request"
    )
    definition_contract = _first_context_mapping(row, "definition_contract")
    if not source_context:
        blockers.append("source_anchor_context_missing")
    known_gaps = _known_gaps(row)
    if known_gaps:
        blockers.append("known_gaps_unresolved")
    if _candidate_source_has_known_gaps_comment(source):
        blockers.append("candidate_known_gaps_comment_present")
    blockers = list(dict.fromkeys(blockers))
    status = _status_from_blockers(blockers)
    result_id = (
        "source_theorem_exact_semantic_definition_verifier_gate_result:"
        + stable_hash(
            [
                row.get("work_order_id", ""),
                row.get("source_review_packet_id", ""),
                row.get("target_theorem_name", ""),
                placeholder,
                candidate_path_text,
                blockers,
            ]
        )[:24]
    )
    source_theorem_ready = status == "VERIFIER_APPROVED_FOR_PROOF_BODY_RECHECK"
    return {
        "schema_version": 1,
        "artifact_kind": RESULT_ARTIFACT_KIND,
        "verifier_gate_result_id": result_id,
        "source_work_order_id": str(row.get("work_order_id", "") or ""),
        "source_review_packet_id": str(row.get("source_review_packet_id", "") or ""),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "target_ids": _string_list(row.get("target_ids", [])),
        "placeholder_symbol": placeholder,
        "candidate_artifact_path": candidate_path_text,
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_file_exists": candidate_file_exists,
        "candidate_definition_present": bool(
            placeholder and _has_placeholder_definition(code, placeholder)
        ),
        "vacuous_placeholder_definition": bool(
            placeholder and _has_vacuous_placeholder_definition(code, placeholder)
        ),
        "forbidden_tokens_found": forbidden_tokens,
        "local_lean_requested": bool(local_lean),
        "local_lean_checked": local_lean_checked,
        "local_lean_compiled": local_lean_compiled,
        "lean_command": list(lean_command),
        "lean_project": str(lean_project or ""),
        "lean_timeout": int(lean_timeout),
        "returncode": returncode,
        "diagnostics": list(diagnostics),
        "semantic_review_decision": semantic_review_decision,
        "semantic_review_status": str(row.get("semantic_review_status", "") or ""),
        "semantic_review_evidence": semantic_review_evidence,
        "semantic_review_required_before_proof_body": not source_theorem_ready,
        **_exact_semantic_definition_context(row),
        "candidate_definition_request": candidate_definition_request,
        "definition_contract": definition_contract,
        "known_gaps": known_gaps,
        "source_anchor_context": source_context,
        "verifier_gate_status": status,
        "verifier_gate_blockers": blockers,
        "failure_classification": _failure_classification(status, blockers),
        "runtime_queue_status": (
            "READY_FOR_EXACT_SOURCE_PROOF_BODY_RECHECK"
            if source_theorem_ready
            else "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_REPAIR"
        ),
        "source_theorem_ready_for_exact_proof_body": source_theorem_ready,
        "source_theorem_kernel_verified": False,
        "source_theorem_kernel_evidence_eligible": False,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _approved_review_packet(result: Mapping[str, Any]) -> dict[str, Any]:
    evidence = _string_list(result.get("semantic_review_evidence", []))
    evidence.append(
        "Verifier gate approved local Lean typecheck, candidate shape, and "
        "source-anchor context for proof-body recheck; this remains non-proof "
        "semantic-readiness evidence."
    )
    source_anchor_context = [
        dict(item)
        for item in result.get("source_anchor_context", []) or []
        if isinstance(item, Mapping)
    ]
    candidate_definition_request = result.get("candidate_definition_request")
    definition_contract = result.get("definition_contract")
    return {
        "schema_version": 1,
        "artifact_kind": APPROVED_PACKET_ARTIFACT_KIND,
        "review_packet_id": str(
            result.get("source_review_packet_id", "")
            or result.get("verifier_gate_result_id", "")
        ),
        "source_verifier_gate_result_id": str(
            result.get("verifier_gate_result_id", "") or ""
        ),
        "target_theorem_name": str(result.get("target_theorem_name", "") or ""),
        "target_ids": _string_list(result.get("target_ids", [])),
        "placeholder_symbol": str(result.get("placeholder_symbol", "") or ""),
        "candidate_artifact_path": str(result.get("candidate_artifact_path", "") or ""),
        "definition_only_candidate_artifact_path": str(
            result.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "local_definition_lean_checked": bool(result.get("local_lean_checked", False)),
        "local_definition_lean_compiled": bool(
            result.get("local_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": APPROVED_TYPECHECK_STATUS,
        "semantic_review_decision": "approved_definition_candidate",
        "semantic_review_status": (
            "verifier_gate_approved_definition_candidate_not_proof"
        ),
        "semantic_review_evidence": evidence,
        **_exact_semantic_definition_context(result),
        "source_anchor_context": source_anchor_context,
        "source_anchor_context_rows": len(source_anchor_context),
        "candidate_definition_request": dict(candidate_definition_request)
        if isinstance(candidate_definition_request, Mapping)
        else {},
        "definition_contract": dict(definition_contract)
        if isinstance(definition_contract, Mapping)
        else {},
        "semantic_review_required_before_proof_body": False,
        "source_theorem_ready_for_exact_proof_body": True,
        "source_theorem_kernel_verified": False,
        "source_theorem_kernel_evidence_eligible": False,
        "proof_evidence_status": APPROVED_PACKET_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _runtime_learning_row(result: Mapping[str, Any]) -> dict[str, Any]:
    ready = _bool_like(
        result.get("source_theorem_ready_for_exact_proof_body", False)
    )
    return {
        "schema_version": 1,
        "artifact_kind": "RuntimeSourceTheoremExactSemanticDefinitionVerifierGateLearningRow",
        "learning_task": LEARNING_TASK,
        "work_order_id": str(result.get("source_work_order_id", "") or ""),
        "verifier_gate_result_id": str(
            result.get("verifier_gate_result_id", "") or ""
        ),
        "target_theorem_name": str(result.get("target_theorem_name", "") or ""),
        "target_ids": _string_list(result.get("target_ids", [])),
        "placeholder_symbol": str(result.get("placeholder_symbol", "") or ""),
        "candidate_artifact_path": str(result.get("candidate_artifact_path", "") or ""),
        "local_lean_checked": bool(result.get("local_lean_checked", False)),
        "local_lean_compiled": bool(result.get("local_lean_compiled", False)),
        "known_gaps": _string_list(result.get("known_gaps", [])),
        "source_anchor_context": [
            dict(item)
            for item in result.get("source_anchor_context", []) or []
            if isinstance(item, Mapping)
        ],
        "verifier_gate_status": str(result.get("verifier_gate_status", "") or ""),
        "verifier_gate_blockers": _string_list(
            result.get("verifier_gate_blockers", [])
        ),
        "failure_classification": str(
            result.get("failure_classification", "") or ""
        ),
        "runtime_queue_status": str(result.get("runtime_queue_status", "") or ""),
        **_exact_semantic_definition_context(result),
        "source_theorem_ready_for_exact_proof_body": ready,
        "source_theorem_kernel_verified": False,
        "source_theorem_kernel_evidence_eligible": False,
        "recommended_next_action": (
            "rerun exact source proof-body recheck from verifier-approved review packets"
            if ready
            else (
                "repair source-anchor context or semantic gaps before exact "
                "source proof-body recheck"
            )
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _exact_semantic_definition_context(row: Mapping[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    sources = _exact_semantic_context_sources(row)
    for key in EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS:
        value = None
        for source in sources:
            value = source.get(key, None)
            if value not in (None, "", [], {}):
                break
        if value in (None, "", [], {}):
            continue
        if isinstance(value, Mapping):
            context[key] = dict(value)
        elif isinstance(value, list):
            context[key] = list(value)
        else:
            context[key] = value
    normalize_exact_semantic_definition_signature_probe_context(
        context,
        *sources,
    )
    return context


def _first_context_mapping(row: Mapping[str, Any], key: str) -> dict[str, Any]:
    for source in _exact_semantic_context_sources(row):
        value = source.get(key)
        if isinstance(value, Mapping) and value:
            return dict(value)
    return {}


def _exact_semantic_context_sources(row: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    sources: list[Mapping[str, Any]] = [row]
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    if input_summary:
        sources.append(input_summary)
    typechecked_candidate = row.get(
        "source_theorem_exact_semantic_definition_typechecked_candidate",
        {},
    )
    if isinstance(typechecked_candidate, Mapping):
        sources.append(typechecked_candidate)
    for source in list(sources):
        nested_context = source.get("exact_semantic_definition_context", {})
        if isinstance(nested_context, Mapping):
            sources.append(nested_context)
    return sources


def _status_from_blockers(blockers: Sequence[str]) -> str:
    blocker_set = set(blockers)
    if not blockers:
        return "VERIFIER_APPROVED_FOR_PROOF_BODY_RECHECK"
    if "candidate_artifact_path_missing" in blocker_set:
        return "VERIFIER_GATE_CANDIDATE_PATH_MISSING"
    if "candidate_artifact_file_missing" in blocker_set:
        return "VERIFIER_GATE_CANDIDATE_FILE_MISSING"
    if "local_lean_unavailable" in blocker_set:
        return "VERIFIER_GATE_LOCAL_LEAN_UNAVAILABLE"
    if "local_lean_verifier_not_requested" in blocker_set:
        return "VERIFIER_GATE_LOCAL_LEAN_NOT_REQUESTED"
    if "local_lean_failed" in blocker_set:
        return "VERIFIER_GATE_LOCAL_LEAN_FAILED"
    if blocker_set.intersection(
        {
            "forbidden_tokens_present",
            "placeholder_definition_missing",
            "vacuous_placeholder_definition",
            "placeholder_symbol_missing",
        }
    ):
        return "VERIFIER_GATE_REJECTED_STATIC_CANDIDATE_POLICY"
    if blocker_set.intersection(
        {
            "source_anchor_context_missing",
            "known_gaps_unresolved",
            "candidate_known_gaps_comment_present",
        }
    ):
        return "VERIFIER_GATE_BLOCKED_SOURCE_SEMANTIC_CONTEXT_INSUFFICIENT"
    return "VERIFIER_GATE_BLOCKED_SEMANTIC_REVIEW_EVIDENCE_INSUFFICIENT"


def _failure_classification(status: str, blockers: Sequence[str]) -> str:
    if status == "VERIFIER_APPROVED_FOR_PROOF_BODY_RECHECK":
        return ""
    if blockers:
        return str(blockers[0])
    return status.lower()


def _source_anchor_context(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    context: list[dict[str, Any]] = []
    for source in _exact_semantic_context_sources(row):
        for key in (
            "source_anchor_context",
            "source_reference_hints",
            "candidate_source_references",
            "source_anchors",
            "exact_source_theorem_binders",
            "premise_semantic_anchor_binders",
        ):
            value = source.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                for item in value:
                    if isinstance(item, Mapping):
                        context.append({"source": key, **dict(item)})
                    elif str(item).strip():
                        context.append({"source": key, "value": str(item)})
        for key in (
            "premise_semantic_anchor_binder_names",
            "required_anchor_names",
            "required_semantic_anchor_reference_names",
        ):
            for item in _string_list(source.get(key, [])):
                context.append({"source": key, "name": item})
        request = source.get("candidate_definition_request")
        if isinstance(request, Mapping):
            context.extend(_candidate_definition_request_anchor_context(request))
    return _dedupe_context_rows(context)


def _candidate_definition_request_anchor_context(
    request: Mapping[str, Any],
) -> list[dict[str, Any]]:
    context: list[dict[str, Any]] = []
    for key in ("required_binders",):
        value = request.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                if isinstance(item, Mapping):
                    context.append(
                        {
                            "source": f"candidate_definition_request.{key}",
                            **dict(item),
                        }
                    )
                elif str(item).strip():
                    context.append(
                        {
                            "source": f"candidate_definition_request.{key}",
                            "name": str(item),
                        }
                    )
    for raw_binding in request.get("required_anchor_bindings", []) or []:
        if not isinstance(raw_binding, Mapping):
            continue
        row = _required_anchor_binding_context_row(raw_binding)
        if row:
            context.append(row)
    for key in (
        "required_anchor_names",
        "available_anchor_names",
    ):
        for item in _string_list(request.get(key, [])):
            context.append(
                {
                    "source": f"candidate_definition_request.{key}",
                    "name": item,
                }
            )
    return context


def _required_anchor_binding_context_row(
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    binder = (
        dict(binding.get("binder", {}))
        if isinstance(binding.get("binder", {}), Mapping)
        else {}
    )
    required_name = str(binding.get("required_anchor_name", "") or "").strip()
    actual_name = str(
        binding.get("actual_anchor_name", "") or binder.get("name", "") or ""
    ).strip()
    if not required_name and not actual_name:
        return {}
    row: dict[str, Any] = {
        "source": "candidate_definition_request.required_anchor_bindings",
        "kind": "required_anchor_binding",
        "required_anchor_name": required_name,
        "actual_anchor_name": actual_name,
        "semantic_anchor_name": required_name,
        "name": actual_name or required_name,
        "match_kind": str(binding.get("match_kind", "") or "").strip(),
    }
    role = str(binding.get("role", "") or binder.get("role", "") or "").strip()
    if role:
        row["role"] = role
    binder_type = str(binder.get("type", "") or "").strip()
    if binder_type:
        row["type"] = binder_type
    if binder:
        row["binder"] = binder
    return row


def _dedupe_context_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        item = dict(row)
        key = json.dumps(item, sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _known_gaps(row: Mapping[str, Any]) -> list[str]:
    gaps: list[str] = []
    for source in _exact_semantic_context_sources(row):
        gaps.extend(_string_list(source.get("known_gaps", [])))
        contract = source.get("definition_contract")
        if isinstance(contract, Mapping):
            gaps.extend(_string_list(contract.get("known_gaps", [])))
    return list(dict.fromkeys(gaps))


def _strip_lean_comments(source: str) -> str:
    without_block_comments = re.sub(r"/-.*?-/", "", source, flags=re.DOTALL)
    return "\n".join(
        re.sub(r"--.*$", "", line) for line in without_block_comments.splitlines()
    )


def _forbidden_tokens_in_code(code: str) -> list[str]:
    return [
        token
        for token in FORBIDDEN_ARTIFACT_TOKENS
        if re.search(rf"(?<![A-Za-z0-9_']){re.escape(token)}(?![A-Za-z0-9_'])", code)
    ]


def _has_placeholder_definition(code: str, placeholder: str) -> bool:
    return bool(
        re.search(
            rf"\b(?:def|abbrev)\s+{re.escape(placeholder)}\b",
            code,
        )
    )


def _has_vacuous_placeholder_definition(code: str, placeholder: str) -> bool:
    return bool(
        re.search(
            rf"\b(?:def|abbrev)\s+{re.escape(placeholder)}\b[\s\S]*?:=\s*True\b",
            code,
        )
    )


def _candidate_source_has_known_gaps_comment(source: str) -> bool:
    match = re.search(r"Known gaps:\s*(?P<gaps>.*?)\n\s*-\s*/", source, re.DOTALL)
    if match is None:
        return False
    gaps = match.group("gaps").strip()
    return bool(gaps and gaps not in {"[]", "None", "none"})


def _read_jsonl(path: Path) -> list[Any]:
    rows: list[Any] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(dict(row), sort_keys=True, default=str) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _string_list(value: Any) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item) for item in value if str(item).strip()]
    if str(value or "").strip():
        return [str(value)]
    return []


def _has_pseudo_formal_origin(row: Mapping[str, Any]) -> bool:
    return bool(
        str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
        or _has_formalizer_pf_component_gate_origin(row)
    )


def _has_formalizer_pf_component_gate_origin(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("source_component_gate", "") or "").strip()
        == "formalizer_pseudo_formal_packet_component_gate"
    )


def _formalizer_pf_component_gate_exact_rows_jsonl_paths(
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    paths: list[str] = []
    for row in rows:
        if not _has_formalizer_pf_component_gate_origin(row):
            continue
        path = str(row.get("source_component_gate_exact_rows_jsonl", "") or "").strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def _source_pseudo_formal_ids(
    rows: Sequence[Mapping[str, Any]],
    key: str,
) -> list[str]:
    return list(
        dict.fromkeys(
            str(row.get(key, "") or "")
            for row in rows
            if str(row.get(key, "") or "").strip()
        )
    )

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .exact_semantic_definition_policy import (
    exact_semantic_definition_import_policy_blocker,
    exact_semantic_definition_placeholder_policy,
)
from .fingerprint import stable_hash
from .formal_verifier_agentic_proof_execution_materializer import (
    _normalize_lean_statement_syntax,
)


ARTIFACT_KIND = "RuntimeSourceTheoremExactSemanticDefinitionSourceLookupManifest"
LOOKUP_ROW_ARTIFACT_KIND = "RuntimeSourceTheoremExactSemanticDefinitionSourceLookupRow"
DEFINITION_CLOSURE_WORK_ORDER_ARTIFACT_KIND = (
    "RuntimeSourceTheoremExactSemanticDefinitionClosureWorkOrder"
)
DEFINITION_CLOSURE_REVIEW_PACKET_ARTIFACT_KIND = (
    "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewPacket"
)
DEFINITION_CLOSURE_REVIEW_RESULT_ARTIFACT_KIND = (
    "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewResult"
)
SEMANTIC_DEFINITION_REPAIR_QUEUE_ROW_ARTIFACT_KIND = (
    "RuntimeSourceTheoremExactSemanticDefinitionRepairQueueRow"
)
TYPECHECKED_REVIEW_VERIFIER_GATE_WORK_ORDER_ARTIFACT_KIND = (
    "RuntimeSourceTheoremExactSemanticDefinitionTypecheckedReviewVerifierGateWorkOrder"
)
TYPECHECKED_REVIEW_SEMANTIC_REVIEW_WORK_ORDER_ARTIFACT_KIND = (
    "RuntimeSourceTheoremExactSemanticDefinitionTypecheckedSemanticReviewWorkOrder"
)
TYPECHECKED_REVIEW_BLOCKED_LEARNING_ROW_ARTIFACT_KIND = (
    "RuntimeSourceTheoremExactSemanticDefinitionTypecheckedReviewBlockedLearningRow"
)
TYPECHECKED_REVIEW_RECHECK_QUEUE_PROOF_EVIDENCE_STATUS = (
    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_REVIEW_RECHECK_QUEUE_NOT_PROOF_EVIDENCE"
)
TYPECHECKED_REVIEW_VERIFIER_GATE_PROOF_EVIDENCE_STATUS = (
    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_WORK_ORDER_NOT_PROOF_EVIDENCE"
)
TYPECHECKED_REVIEW_SEMANTIC_REVIEW_PROOF_EVIDENCE_STATUS = (
    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_SEMANTIC_REVIEW_WORK_ORDER_NOT_PROOF_EVIDENCE"
)
TYPECHECKED_REVIEW_BLOCKED_PROOF_EVIDENCE_STATUS = (
    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_REVIEW_BLOCKED_NOT_PROOF_EVIDENCE"
)
LEARNING_TASK = "source_theorem_exact_semantic_definition_source_lookup"
DEFINITION_CLOSURE_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_closure_work_order"
)
DEFINITION_CLOSURE_REVIEW_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_closure_review_packet"
)
DEFINITION_CLOSURE_REVIEW_RESULT_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_closure_review_result"
)
SEMANTIC_DEFINITION_REPAIR_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_repair_queue"
)
TYPECHECKED_REVIEW_VERIFIER_GATE_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_typechecked_review_verifier_gate"
)
TYPECHECKED_REVIEW_SEMANTIC_REVIEW_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_typechecked_semantic_review_required"
)
TYPECHECKED_REVIEW_BLOCKED_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_typechecked_review_blocked"
)
PROOF_EVIDENCE_STATUS = "SOURCE_LOOKUP_NOT_PROOF_EVIDENCE"
DEFINITION_CLOSURE_PROOF_EVIDENCE_STATUS = (
    "DEFINITION_CLOSURE_WORK_ORDER_NOT_PROOF_EVIDENCE"
)
DEFINITION_CLOSURE_REVIEW_PROOF_EVIDENCE_STATUS = (
    "DEFINITION_CLOSURE_REVIEW_PACKET_NOT_PROOF_EVIDENCE"
)
DEFINITION_CLOSURE_REVIEW_RESULT_PROOF_EVIDENCE_STATUS = (
    "DEFINITION_CLOSURE_REVIEW_RESULT_NOT_PROOF_EVIDENCE"
)
BOUNDARY = (
    "Exact semantic-definition source lookup is retrieval/source-location evidence only. "
    "A source hit is not Lean proof evidence and does not close the source theorem until "
    "a reviewed exact semantic definition and the target theorem pass local Lean/AXLE."
)
EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS = (
    "target_ids",
    "placeholder_policy_id",
    "placeholder_policy_scope",
    "exact_source_theorem_binders",
    "premise_semantic_anchor_binders",
    "premise_semantic_anchor_binder_names",
    "required_bridge_premise_names_for_shared_instantiation",
    "source_to_bridge_adapter_instantiation_group_id",
    "source_to_bridge_adapter_object_names_requiring_source_instantiation",
    "source_to_bridge_grouped_premise_derivation_candidate_request_id",
    "exact_goal_shape_obligation_ids",
    "target_lean_declaration",
    "candidate_definition_request",
    "verifier_gate_status",
    "verifier_gate_blockers",
    "known_gaps",
    "source_anchor_context",
    "source_anchor_context_rows",
    "verifier_gate_result_id",
    "source_verifier_gate_work_order_id",
    "recommended_repair_tasks",
    "proof_body_recheck_blockers",
    "source_materialization_seed_id",
    "source_pseudo_formal_work_order_id",
    "source_pseudo_formal_block_id",
    "source_pseudo_formal_packet_id",
    "source_formalizer_proposal_id",
    "source_formalizer_proposal_without_formalization_manifest",
    "pseudo_formal_method_contract_id",
    "pseudo_formal_pipeline_stage",
    "pseudo_formal_proof_evidence_status",
)


def run_source_theorem_exact_semantic_definition_source_lookup(
    *,
    out_dir: Path,
    queue_jsonl: Path | None = None,
    runtime_dir: Path | None = None,
    source_roots: list[Path] | None = None,
    max_hits_per_work_order: int = 8,
) -> dict[str, Any]:
    work_order_path = resolve_exact_semantic_definition_work_order_path(
        runtime_dir=runtime_dir,
        queue_jsonl=queue_jsonl,
    )
    work_orders = _read_jsonl(work_order_path)
    roots = [root for root in source_roots or [] if root.exists()]
    lookup_rows = [
        _lookup_row(
            work_order=row,
            source_roots=roots,
            max_hits=max(0, int(max_hits_per_work_order)),
        )
        for row in work_orders
        if isinstance(row, Mapping)
    ]
    definition_closure_work_orders = [
        _definition_closure_work_order_from_lookup(row)
        for row in lookup_rows
    ]
    definition_closure_review_packets = [
        _definition_closure_review_packet(row)
        for row in definition_closure_work_orders
    ]
    learning_rows = [
        _learning_row_from_lookup(row)
        for row in lookup_rows
    ]
    learning_rows.extend(
        _learning_row_from_definition_closure_work_order(row)
        for row in definition_closure_work_orders
    )
    learning_rows.extend(
        _learning_row_from_definition_closure_review_packet(row)
        for row in definition_closure_review_packets
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    lookup_path = out_dir / "source_theorem_exact_semantic_definition_source_lookup_rows.jsonl"
    definition_closure_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_closure_work_orders.jsonl"
    )
    definition_closure_review_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_closure_review_packets.jsonl"
    )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(lookup_path, lookup_rows)
    _write_jsonl(definition_closure_path, definition_closure_work_orders)
    _write_jsonl(definition_closure_review_path, definition_closure_review_packets)
    _write_jsonl(learning_path, learning_rows)
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_work_orders_jsonl": str(work_order_path),
        "source_roots": [str(root) for root in roots],
        "lookup_rows_jsonl": str(lookup_path),
        "definition_closure_work_orders_jsonl": str(definition_closure_path),
        "definition_closure_review_packets_jsonl": str(
            definition_closure_review_path
        ),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_work_orders": len(work_orders),
        "n_lookup_rows": len(lookup_rows),
        "n_definition_closure_work_orders": len(definition_closure_work_orders),
        "n_definition_closure_review_packets": len(
            definition_closure_review_packets
        ),
        "n_runtime_learning_rows": len(learning_rows),
        "n_lookup_rows_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(lookup_rows)
        ),
        "n_definition_closure_work_orders_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(definition_closure_work_orders)
        ),
        "n_definition_closure_review_packets_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(definition_closure_review_packets)
        ),
        "n_runtime_learning_rows_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(learning_rows)
        ),
        "placeholder_policy_lineage_complete": (
            _placeholder_policy_lineage_complete(
                lookup_rows,
                definition_closure_work_orders,
                definition_closure_review_packets,
                learning_rows,
            )
        ),
        "n_rows_with_source_hits": sum(
            1 for row in lookup_rows if row.get("source_lookup_hits")
        ),
        "n_rows_with_candidate_source_declarations": sum(
            1 for row in lookup_rows if row.get("candidate_source_declarations")
        ),
        "n_source_lookup_hits": sum(
            len(row.get("source_lookup_hits", []) or [])
            for row in lookup_rows
            if isinstance(row, Mapping)
        ),
        "lookup_status_counts": _count_by_key(lookup_rows, "lookup_status"),
        "closure_next_step_counts": _count_by_key(
            definition_closure_work_orders, "next_step_kind"
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }
    manifest_path = out_dir / "source_theorem_exact_semantic_definition_source_lookup_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def run_source_theorem_exact_semantic_definition_closure_review(
    *,
    out_dir: Path,
    review_packets_jsonl: Path | None = None,
    lookup_manifest: Path | None = None,
    candidate_artifact_path: Path | None = None,
) -> dict[str, Any]:
    review_packet_path = resolve_exact_semantic_definition_review_packets_path(
        review_packets_jsonl=review_packets_jsonl,
        lookup_manifest=lookup_manifest,
    )
    review_packets = _read_jsonl(review_packet_path)
    candidate_text = ""
    if candidate_artifact_path is not None and candidate_artifact_path.exists():
        candidate_text = candidate_artifact_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    review_rows = [
        _definition_closure_review_result(
            row,
            candidate_artifact_path=candidate_artifact_path,
            candidate_text=candidate_text,
        )
        for row in review_packets
        if isinstance(row, Mapping)
    ]
    learning_rows = [
        _learning_row_from_definition_closure_review_result(row)
        for row in review_rows
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    review_rows_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_closure_review_results.jsonl"
    )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(review_rows_path, review_rows)
    _write_jsonl(learning_path, learning_rows)
    manifest = {
        "schema_version": 1,
        "artifact_kind": (
            "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewManifest"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_review_packets_jsonl": str(review_packet_path),
        "candidate_artifact_path": str(candidate_artifact_path or ""),
        "review_results_jsonl": str(review_rows_path),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_review_packets": len(review_packets),
        "n_review_results": len(review_rows),
        "n_runtime_learning_rows": len(learning_rows),
        "n_forbidden_placeholder_definitions": sum(
            1 for row in review_rows if row.get("forbidden_placeholder_detected")
        ),
        "n_ready_for_definition_lean_check": sum(
            1 for row in review_rows if row.get("ready_for_definition_lean_check")
        ),
        "review_status_counts": _count_by_key(review_rows, "review_status"),
        "proof_evidence_status": DEFINITION_CLOSURE_REVIEW_RESULT_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_closure_review_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def run_source_theorem_exact_semantic_definition_candidate_synthesis(
    *,
    out_dir: Path,
    review_manifest: Path | None = None,
    review_results_jsonl: Path | None = None,
    candidate_artifact_path: Path,
    proof_body_queue_manifest: Path | None = None,
    proof_body_queue_jsonl: Path | None = None,
    allow_draft_semantic_repair: bool = False,
    local_lean: bool = False,
    lean_project: Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    review_results_path = resolve_exact_semantic_definition_review_results_path(
        review_manifest=review_manifest,
        review_results_jsonl=review_results_jsonl,
    )
    review_results = _read_jsonl(review_results_path)
    source_text = candidate_artifact_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )
    normalized_source_text = _normalize_lean_statement_syntax(source_text)
    if source_text.endswith("\n") and not normalized_source_text.endswith("\n"):
        normalized_source_text += "\n"
    source_text = normalized_source_text
    synthesized_text = source_text
    synthesis_rows: list[dict[str, Any]] = []
    for row in review_results:
        if not isinstance(row, Mapping):
            continue
        placeholder = str(row.get("placeholder_symbol", "") or "")
        ready_for_definition_lean_check = bool(
            row.get("ready_for_definition_lean_check", False)
        ) and not bool(row.get("forbidden_placeholder_detected", False))
        semantic_definition_risk_detected = bool(
            row.get("semantic_definition_risk_detected", False)
        ) or bool(row.get("semantic_definition_risks", []) or [])
        draft_semantic_repair = bool(
            allow_draft_semantic_repair and semantic_definition_risk_detected
        )
        ready_for_definition_lean_check = (
            ready_for_definition_lean_check and not semantic_definition_risk_detected
        )
        replacement = ""
        if (
            not ready_for_definition_lean_check
            and (not semantic_definition_risk_detected or draft_semantic_repair)
        ):
            replacement = _draft_definition_for_placeholder(placeholder)
        replacement_applied = False
        replacement_error = ""
        if ready_for_definition_lean_check:
            review_mode = "lean_review_existing_candidate"
        elif draft_semantic_repair:
            review_mode = "synthesize_draft_definition_from_semantic_risk_repair"
        elif semantic_definition_risk_detected:
            review_mode = "semantic_review_blocked_existing_candidate"
        else:
            review_mode = "synthesize_draft_definition"
        if ready_for_definition_lean_check:
            replacement_error = ""
        elif semantic_definition_risk_detected and not draft_semantic_repair:
            replacement_error = (
                "candidate definition failed semantic review; requires reviewed "
                "definition/import before proof-body search"
            )
        elif replacement:
            try:
                synthesized_text = _replace_lean_definition_block(
                    candidate_text=synthesized_text,
                    symbol=placeholder,
                    replacement=replacement,
                )
                replacement_applied = True
            except ValueError as exc:
                replacement_error = str(exc)
        else:
            replacement_error = f"no draft definition available for {placeholder}"
        synthesis_rows.append(
            _definition_candidate_synthesis_row(
                row,
                candidate_artifact_path=candidate_artifact_path,
                replacement=replacement,
                replacement_applied=replacement_applied,
                replacement_error=replacement_error,
                review_mode=review_mode,
            )
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir = out_dir / "candidate_artifacts"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    synthesized_artifact_path = (
        candidate_dir
        / f"{candidate_artifact_path.stem}_exact_semantic_definitions_attempt.lean"
    )
    synthesized_artifact_path.write_text(synthesized_text, encoding="utf-8")
    definition_only_artifact_path = (
        candidate_dir
        / f"{candidate_artifact_path.stem}_exact_semantic_definitions_only.lean"
    )
    definition_only_artifact_path.write_text(
        _definition_only_candidate_text(synthesized_text),
        encoding="utf-8",
    )
    forbidden_after_by_symbol = {
        str(row.get("placeholder_symbol", "") or ""): _forbidden_placeholder_definition_matches(
            placeholder=str(row.get("placeholder_symbol", "") or ""),
            candidate_text=synthesized_text,
        )
        for row in review_results
        if isinstance(row, Mapping)
    }
    command = lean_command or _lean_command(lean_project)
    local_lean_compiled = False
    local_lean_returncode = 0
    local_lean_diagnostics: tuple[str, ...] = ()
    local_definition_lean_compiled = False
    local_definition_lean_returncode = 0
    local_definition_lean_diagnostics: tuple[str, ...] = ()
    if local_lean:
        (
            local_definition_lean_compiled,
            local_definition_lean_returncode,
            local_definition_lean_diagnostics,
        ) = _run_local_lean(
            definition_only_artifact_path,
            lean_command=command,
            lean_project=lean_project,
            timeout_s=lean_timeout,
        )
        local_lean_compiled, local_lean_returncode, local_lean_diagnostics = (
            _run_local_lean(
                synthesized_artifact_path,
                lean_command=command,
                lean_project=lean_project,
                timeout_s=lean_timeout,
            )
        )
    synthesis_rows = [
        {
            **row,
            "synthesized_candidate_artifact_path": str(synthesized_artifact_path),
            "definition_only_candidate_artifact_path": str(
                definition_only_artifact_path
            ),
            "forbidden_placeholder_matches_after": forbidden_after_by_symbol.get(
                str(row.get("placeholder_symbol", "") or ""),
                [],
            ),
            "forbidden_placeholder_detected_after": bool(
                forbidden_after_by_symbol.get(
                    str(row.get("placeholder_symbol", "") or ""),
                    [],
                )
            ),
            "local_lean_requested": bool(local_lean),
            "candidate_lean_project_hint": str(lean_project or ""),
            "local_lean_checked": bool(local_lean),
            "local_lean_compiled": bool(local_lean_compiled),
            "local_lean_returncode": int(local_lean_returncode),
            "local_lean_diagnostics": list(local_lean_diagnostics[:40]),
            "local_definition_lean_checked": bool(local_lean),
            "local_definition_lean_compiled": bool(local_definition_lean_compiled),
            "local_definition_lean_returncode": int(local_definition_lean_returncode),
            "local_definition_lean_diagnostics": list(
                local_definition_lean_diagnostics[:40]
            ),
            "semantic_definition_typecheck_evidence_status": (
                "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
                if local_lean and local_definition_lean_compiled
                else "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
            ),
            "candidate_synthesis_status": _candidate_synthesis_status(
                row,
                forbidden_after=forbidden_after_by_symbol.get(
                    str(row.get("placeholder_symbol", "") or ""),
                    [],
                ),
                local_lean=local_lean,
                local_lean_compiled=local_lean_compiled,
                diagnostics=local_lean_diagnostics,
            ),
        }
        for row in synthesis_rows
    ]
    semantic_definition_repair_queue_manifest = (
        _export_candidate_synthesis_semantic_definition_repair_queue(
            out_dir=out_dir / "semantic_definition_repair_queue",
            synthesis_rows=synthesis_rows,
            synthesized_artifact_path=synthesized_artifact_path,
        )
    )
    learning_rows = [
        _learning_row_from_definition_candidate_synthesis(row)
        for row in synthesis_rows
    ]
    learning_rows.extend(
        _learning_row_from_semantic_definition_repair_queue(row)
        for row in semantic_definition_repair_queue_manifest.get("rows", [])
        if isinstance(row, Mapping)
    )
    rows_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_candidate_synthesis_results.jsonl"
    )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(rows_path, synthesis_rows)
    _write_jsonl(learning_path, learning_rows)
    recheck_queue_manifest: dict[str, Any] | None = None
    if proof_body_queue_manifest is not None or proof_body_queue_jsonl is not None:
        recheck_queue_manifest = _export_candidate_synthesis_proof_body_recheck_queue(
            out_dir=out_dir / "exact_source_theorem_proof_body_recheck_queue",
            proof_body_queue_manifest=proof_body_queue_manifest,
            proof_body_queue_jsonl=proof_body_queue_jsonl,
            synthesis_rows=synthesis_rows,
            synthesized_artifact_path=synthesized_artifact_path,
        )
    manifest = {
        "schema_version": 1,
        "artifact_kind": (
            "RuntimeSourceTheoremExactSemanticDefinitionCandidateSynthesisManifest"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_review_results_jsonl": str(review_results_path),
        "source_candidate_artifact_path": str(candidate_artifact_path),
        "synthesized_candidate_artifact_path": str(synthesized_artifact_path),
        "definition_only_candidate_artifact_path": str(definition_only_artifact_path),
        "candidate_synthesis_results_jsonl": str(rows_path),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_review_results": len(review_results),
        "n_synthesis_results": len(synthesis_rows),
        "n_replacements_applied": sum(
            1 for row in synthesis_rows if row.get("replacement_applied")
        ),
        "n_forbidden_placeholder_definitions_after": sum(
            1 for row in synthesis_rows if row.get("forbidden_placeholder_detected_after")
        ),
        "local_lean_requested": bool(local_lean),
        "local_lean_checked": bool(local_lean),
        "local_lean_compiled": bool(local_lean_compiled),
        "local_lean_returncode": int(local_lean_returncode),
        "local_definition_lean_checked": bool(local_lean),
        "local_definition_lean_compiled": bool(local_definition_lean_compiled),
        "local_definition_lean_returncode": int(local_definition_lean_returncode),
        "semantic_definition_typecheck_evidence_status": (
            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
            if local_lean and local_definition_lean_compiled
            else "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
        ),
        "synthesis_status_counts": _count_by_key(
            synthesis_rows, "candidate_synthesis_status"
        ),
        "proof_body_recheck_queue_manifest": str(
            (recheck_queue_manifest or {}).get("manifest_path", "") or ""
        ),
        "proof_body_recheck_queue_jsonl": str(
            (recheck_queue_manifest or {}).get("queue_jsonl", "") or ""
        ),
        "n_proof_body_recheck_queue_rows": int(
            (recheck_queue_manifest or {}).get("n_execution_queue_rows", 0) or 0
        ),
        "proof_body_recheck_queue_proof_evidence_status": str(
            (recheck_queue_manifest or {}).get("proof_evidence_status", "") or ""
        ),
        "semantic_definition_repair_queue_manifest": str(
            semantic_definition_repair_queue_manifest.get("manifest_path", "") or ""
        ),
        "semantic_definition_repair_queue_jsonl": str(
            semantic_definition_repair_queue_manifest.get("queue_jsonl", "") or ""
        ),
        "n_semantic_definition_repair_queue_rows": int(
            semantic_definition_repair_queue_manifest.get("n_repair_queue_rows", 0)
            or 0
        ),
        "semantic_definition_repair_queue_proof_evidence_status": str(
            semantic_definition_repair_queue_manifest.get("proof_evidence_status", "")
            or ""
        ),
        "proof_evidence_status": (
            "DEFINITION_CANDIDATE_SYNTHESIS_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": BOUNDARY,
    }
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_candidate_synthesis_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue(
    *,
    out_dir: Path,
    review_packets_jsonl: Path,
    proof_body_queue_manifest: Path | None = None,
    proof_body_queue_jsonl: Path | None = None,
) -> dict[str, Any]:
    """Export proof-body recheck rows after explicit semantic review approval.

    Typechecking an exact semantic-definition candidate is not enough to resume
    source-theorem proof search. This helper only emits recheck rows for packets
    that explicitly clear the semantic-review gate.
    """

    review_packets = [
        dict(row)
        for row in _read_jsonl(review_packets_jsonl)
        if isinstance(row, Mapping)
    ]
    source_rows = _resolve_proof_body_queue_rows(
        proof_body_queue_manifest=proof_body_queue_manifest,
        proof_body_queue_jsonl=proof_body_queue_jsonl,
    )
    rows: list[dict[str, Any]] = []
    blocked_packets: list[dict[str, Any]] = []
    approved_packets: list[dict[str, Any]] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "execution_transcripts").mkdir(parents=True, exist_ok=True)
    for packet in review_packets:
        ready, blockers = _typechecked_review_packet_ready_for_recheck(packet)
        candidate_artifact = _typechecked_review_candidate_artifact_path(packet)
        if not ready or candidate_artifact is None:
            blocked_packets.append(
                {
                    **packet,
                    "proof_body_recheck_blockers": blockers,
                    "runtime_queue_status": (
                        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
                    ),
                    "proof_evidence_status": (
                        TYPECHECKED_REVIEW_RECHECK_QUEUE_PROOF_EVIDENCE_STATUS
                    ),
                }
            )
            continue
        approved_packets.append(packet)
        synthesis_row = _typechecked_review_packet_as_synthesis_row(packet)
        for source_row in _typechecked_review_source_rows_for_recheck(
            packet,
            source_rows,
        ):
            rows.append(
                _proof_body_recheck_queue_row(
                    source_row,
                    synthesized_artifact_path=candidate_artifact,
                    reviewed_definition_only_artifact_path=(
                        _typechecked_review_definition_only_artifact_path(packet)
                    ),
                    semantic_constraints=_semantic_alignment_constraints_from_synthesis_rows(
                        [synthesis_row]
                    ),
                    synthesized_exact_semantic_definitions=False,
                    definition_candidate_review_modes=[
                        "typechecked_candidate_source_semantic_review_approved"
                    ],
                    out_dir=out_dir,
                )
            )
    queue_path = out_dir / "exact_source_theorem_proof_body_execution_queue.jsonl"
    blocked_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_typechecked_review_recheck_blocked_packets.jsonl"
    )
    verifier_gate_work_orders = [
        _typechecked_review_verifier_gate_work_order(row, source_rows=source_rows)
        for row in blocked_packets
        if "llm_semantic_review_approved_requires_verifier_recheck_gate"
        in list(row.get("proof_body_recheck_blockers", []) or [])
    ]
    semantic_review_work_orders = [
        _typechecked_review_semantic_review_work_order(row)
        for row in blocked_packets
        if _typechecked_review_requires_semantic_review_work_order(row)
    ]
    blocked_review_learning_rows = [
        _typechecked_review_blocked_learning_row(row)
        for row in blocked_packets
        if "llm_semantic_review_approved_requires_verifier_recheck_gate"
        not in list(row.get("proof_body_recheck_blockers", []) or [])
        and not _typechecked_review_requires_semantic_review_work_order(row)
    ]
    runtime_learning_rows = [
        *semantic_review_work_orders,
        *blocked_review_learning_rows,
        *verifier_gate_work_orders,
    ]
    proof_body_recheck_blocker = _typechecked_review_recheck_blocker(
        blocked_packets=blocked_packets,
        semantic_review_work_orders=semantic_review_work_orders,
        verifier_gate_work_orders=verifier_gate_work_orders,
        execution_queue_rows=rows,
    )
    verifier_gate_work_orders_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_typechecked_review_verifier_gate_work_orders.jsonl"
    )
    semantic_review_work_orders_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_typechecked_semantic_review_work_orders.jsonl"
    )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    manifest_path = out_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    _write_jsonl(queue_path, rows)
    _write_jsonl(blocked_path, blocked_packets)
    _write_jsonl(verifier_gate_work_orders_path, verifier_gate_work_orders)
    _write_jsonl(semantic_review_work_orders_path, semantic_review_work_orders)
    _write_jsonl(learning_path, runtime_learning_rows)
    manifest = {
        "schema_version": 1,
        "artifact_kind": (
            "RuntimeSourceTheoremExactSemanticDefinitionTypecheckedReviewRecheckQueueManifest"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_review_packets_jsonl": str(review_packets_jsonl),
        "proof_body_execution_queue_jsonl": str(queue_path),
        "blocked_review_packets_jsonl": str(blocked_path),
        "verifier_gate_work_orders_jsonl": str(verifier_gate_work_orders_path),
        "semantic_review_work_orders_jsonl": str(semantic_review_work_orders_path),
        "runtime_learning_rows_jsonl": str(learning_path),
        "candidate_artifacts_dir": str(out_dir),
        "execution_transcripts_dir": str(out_dir / "execution_transcripts"),
        "n_review_packets": len(review_packets),
        "n_semantically_approved_review_packets": len(approved_packets),
        "n_llm_semantic_review_approved_packets": sum(
            1
            for row in review_packets
            if str(row.get("semantic_review_decision", "") or "")
            == "approved_definition_candidate"
        ),
        "n_llm_semantic_review_packets_requiring_verifier_gate": sum(
            1
            for row in blocked_packets
            if "llm_semantic_review_approved_requires_verifier_recheck_gate"
            in list(row.get("proof_body_recheck_blockers", []) or [])
        ),
        "n_blocked_review_packets": len(blocked_packets),
        "n_blocked_review_learning_rows": len(blocked_review_learning_rows),
        "n_semantic_review_work_orders": len(semantic_review_work_orders),
        "n_verifier_gate_work_orders": len(verifier_gate_work_orders),
        "n_verifier_gate_work_orders_with_source_anchor_context": sum(
            1
            for row in verifier_gate_work_orders
            if _typechecked_review_has_source_anchor_context(row)
        ),
        "n_verifier_gate_work_orders_missing_source_anchor_context": sum(
            1
            for row in verifier_gate_work_orders
            if not _typechecked_review_has_source_anchor_context(row)
        ),
        "n_runtime_learning_rows": len(runtime_learning_rows),
        "n_source_proof_body_rows": len(source_rows),
        "n_execution_queue_rows": len(rows),
        "n_ready": sum(
            1
            for row in rows
            if row.get("execution_status")
            == "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
        ),
        "n_live_goal_requests": sum(1 for row in rows if row.get("live_proof_state_request")),
        "n_live_goal_location_ready": sum(
            1 for row in rows if row.get("live_goal_location_ready")
        ),
        "proof_body_recheck_blocked": bool(blocked_packets) and not rows,
        "proof_body_recheck_blocker": proof_body_recheck_blocker,
        "definition_candidate_review_modes": [
            "typechecked_candidate_source_semantic_review_approved"
        ]
        if approved_packets
        else [],
        "source_theorem_kernel_evidence_eligible": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "proof_evidence_status": (
            TYPECHECKED_REVIEW_RECHECK_QUEUE_PROOF_EVIDENCE_STATUS
        ),
        "boundary": BOUNDARY,
        "rows": rows,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["queue_jsonl"] = str(queue_path)
    return manifest


def _typechecked_review_recheck_blocker(
    *,
    blocked_packets: Sequence[Mapping[str, Any]],
    semantic_review_work_orders: Sequence[Mapping[str, Any]],
    verifier_gate_work_orders: Sequence[Mapping[str, Any]],
    execution_queue_rows: Sequence[Mapping[str, Any]],
) -> str:
    if not blocked_packets or execution_queue_rows:
        return ""
    if verifier_gate_work_orders:
        return "typechecked_candidate_llm_review_requires_verifier_gate"
    if semantic_review_work_orders:
        return "typechecked_candidate_semantic_review_required"
    return "typechecked_candidate_semantic_review_not_approved"


def _export_candidate_synthesis_semantic_definition_repair_queue(
    *,
    out_dir: Path,
    synthesis_rows: list[dict[str, Any]],
    synthesized_artifact_path: Path,
) -> dict[str, Any]:
    rows = [
        _semantic_definition_repair_queue_row(
            row,
            synthesized_artifact_path=synthesized_artifact_path,
        )
        for row in synthesis_rows
        if _semantic_definition_repair_queue_needed(row)
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = out_dir / "semantic_definition_repair_queue.jsonl"
    manifest_path = out_dir / "semantic_definition_repair_queue_manifest.json"
    _write_jsonl(queue_path, rows)
    manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeSourceTheoremExactSemanticDefinitionRepairQueueManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "semantic_definition_repair_queue_jsonl": str(queue_path),
        "synthesized_candidate_artifact_path": str(synthesized_artifact_path),
        "n_repair_queue_rows": len(rows),
        "n_ready": sum(
            1
            for row in rows
            if row.get("repair_status")
            == "READY_FOR_REVIEWED_EXACT_SEMANTIC_DEFINITION_REPAIR"
        ),
        "placeholder_symbols": list(
            dict.fromkeys(
                str(row.get("placeholder_symbol", "") or "")
                for row in rows
                if str(row.get("placeholder_symbol", "") or "").strip()
            )
        ),
        "semantic_definition_risks": list(
            dict.fromkeys(
                str(risk)
                for row in rows
                for risk in row.get("semantic_definition_risks", []) or []
                if str(risk).strip()
            )
        ),
        "source_theorem_kernel_evidence_eligible": False,
        "proof_evidence_status": (
            "SEMANTIC_DEFINITION_REPAIR_QUEUE_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": BOUNDARY,
        "rows": rows,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["queue_jsonl"] = str(queue_path)
    return manifest


def _semantic_definition_repair_queue_needed(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("definition_candidate_review_mode", "") or "")
        == "semantic_review_blocked_existing_candidate"
        or bool(row.get("semantic_definition_risk_detected", False))
        or bool(row.get("semantic_definition_risks", []) or [])
        or bool(row.get("semantic_alignment_blockers", []) or [])
    )


def _semantic_definition_repair_queue_row(
    row: Mapping[str, Any],
    *,
    synthesized_artifact_path: Path,
) -> dict[str, Any]:
    risks = [
        str(value)
        for value in row.get("semantic_definition_risks", []) or []
        if str(value).strip()
    ]
    semantic_risk = str(row.get("semantic_risk", "") or "").strip()
    if semantic_risk:
        risks.append(semantic_risk)
    risks = list(dict.fromkeys(risks))
    blockers = list(
        dict.fromkeys(
            [
                *(
                    str(value)
                    for value in row.get("semantic_alignment_blockers", []) or []
                    if str(value).strip()
                ),
                *risks,
            ]
        )
    )
    placeholder = str(row.get("placeholder_symbol", "") or "")
    target = str(row.get("target_theorem_name", "") or "")
    repair_id = "source_theorem_exact_semantic_definition_repair_queue:" + stable_hash(
        [
            row.get("synthesis_result_id", ""),
            row.get("source_review_result_id", ""),
            target,
            placeholder,
            str(synthesized_artifact_path),
            risks,
        ]
    )[:20]
    return {
        "schema_version": 1,
        "artifact_kind": SEMANTIC_DEFINITION_REPAIR_QUEUE_ROW_ARTIFACT_KIND,
        "repair_queue_id": repair_id,
        "source_synthesis_result_id": str(row.get("synthesis_result_id", "") or ""),
        "source_review_result_id": str(row.get("source_review_result_id", "") or ""),
        "source_review_packet_id": str(row.get("source_review_packet_id", "") or ""),
        "source_definition_closure_work_order_id": str(
            row.get("source_definition_closure_work_order_id", "") or ""
        ),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target,
        "placeholder_symbol": placeholder,
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "synthesized_candidate_artifact_path": str(synthesized_artifact_path),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_lean_project_hint": str(
            row.get("candidate_lean_project_hint", "") or ""
        ),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        "source_theorem_exact_semantic_definition_typechecked_candidate": {
            "target_theorem_name": target,
            "placeholder_symbol": placeholder,
            "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
            "synthesized_candidate_artifact_path": str(synthesized_artifact_path),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_lean_project_hint": str(
                row.get("candidate_lean_project_hint", "") or ""
            ),
            "local_definition_lean_checked": bool(
                row.get("local_definition_lean_checked", False)
            ),
            "local_definition_lean_compiled": bool(
                row.get("local_definition_lean_compiled", False)
            ),
            "semantic_definition_typecheck_evidence_status": str(
                row.get("semantic_definition_typecheck_evidence_status", "") or ""
            ),
            "proof_evidence_status": str(row.get("proof_evidence_status", "") or ""),
        },
        "definition_candidate_review_mode": str(
            row.get("definition_candidate_review_mode", "") or ""
        ),
        "definition_contract": dict(row.get("definition_contract", {}) or {}),
        "semantic_definition_risk_detected": bool(
            row.get("semantic_definition_risk_detected", False)
        )
        or bool(risks),
        "semantic_definition_risks": risks,
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": blockers,
        "source_semantic_alignment_review_required": True,
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "owner_agent": "Formalizer/ProofEngineer",
        "action_type": "repair_reviewed_exact_semantic_definition",
        "repair_status": "READY_FOR_REVIEWED_EXACT_SEMANTIC_DEFINITION_REPAIR",
        "recommended_next_action": str(row.get("recommended_next_action", "") or "")
        or (
            "replace or import reviewed exact semantic definitions before local "
            "proof-body search"
        ),
        "acceptance_gate": (
            "The candidate must replace/import reviewed exact semantics for the "
            "placeholder and then pass local Lean/AXLE to a non-semantic proof "
            "blocker or verify the intended source theorem."
        ),
        "source_theorem_kernel_evidence_eligible": False,
        "proof_evidence_status": (
            "SEMANTIC_DEFINITION_REPAIR_QUEUE_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": BOUNDARY,
        "input_summary": {
            "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_REPAIR_QUEUE",
            "repair_queue_id": repair_id,
            "source_synthesis_result_id": str(
                row.get("synthesis_result_id", "") or ""
            ),
            "target_theorem_name": target,
            "placeholder_symbol": placeholder,
            "definition_candidate_review_mode": str(
                row.get("definition_candidate_review_mode", "") or ""
            ),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
            "synthesized_candidate_artifact_path": str(synthesized_artifact_path),
            "local_definition_lean_checked": bool(
                row.get("local_definition_lean_checked", False)
            ),
            "local_definition_lean_compiled": bool(
                row.get("local_definition_lean_compiled", False)
            ),
            "semantic_definition_typecheck_evidence_status": str(
                row.get("semantic_definition_typecheck_evidence_status", "") or ""
            ),
            "semantic_definition_risk_detected": bool(
                row.get("semantic_definition_risk_detected", False)
            )
            or bool(risks),
            "semantic_definition_risks": risks,
            "semantic_alignment_blockers": blockers,
            "source_theorem_kernel_evidence_eligible": False,
        },
    }


def _export_candidate_synthesis_proof_body_recheck_queue(
    *,
    out_dir: Path,
    proof_body_queue_manifest: Path | None,
    proof_body_queue_jsonl: Path | None,
    synthesis_rows: list[dict[str, Any]],
    synthesized_artifact_path: Path,
) -> dict[str, Any]:
    source_rows = _resolve_proof_body_queue_rows(
        proof_body_queue_manifest=proof_body_queue_manifest,
        proof_body_queue_jsonl=proof_body_queue_jsonl,
    )
    semantic_constraints = _semantic_alignment_constraints_from_synthesis_rows(
        synthesis_rows
    )
    synthesized_exact_semantic_definitions = any(
        bool(row.get("replacement_applied", False)) for row in synthesis_rows
    )
    definition_candidate_review_modes = list(
        dict.fromkeys(
            str(row.get("definition_candidate_review_mode", "") or "")
            for row in synthesis_rows
            if str(row.get("definition_candidate_review_mode", "") or "").strip()
        )
    )
    semantic_definition_review_blocked_rows = [
        row
        for row in synthesis_rows
        if _semantic_definition_repair_queue_needed(row)
    ]
    proof_body_recheck_blocked = bool(semantic_definition_review_blocked_rows)
    rows = (
        []
        if proof_body_recheck_blocked
        else [
            _proof_body_recheck_queue_row(
                row,
                synthesized_artifact_path=synthesized_artifact_path,
                semantic_constraints=semantic_constraints,
                synthesized_exact_semantic_definitions=(
                    synthesized_exact_semantic_definitions
                ),
                definition_candidate_review_modes=definition_candidate_review_modes,
                out_dir=out_dir,
            )
            for row in source_rows
            if isinstance(row, Mapping)
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "execution_transcripts").mkdir(parents=True, exist_ok=True)
    queue_path = out_dir / "exact_source_theorem_proof_body_execution_queue.jsonl"
    manifest_path = out_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    _write_jsonl(queue_path, rows)
    manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_body_execution_queue_jsonl": str(queue_path),
        "candidate_artifacts_dir": str(synthesized_artifact_path.parent),
        "execution_transcripts_dir": str(out_dir / "execution_transcripts"),
        "n_execution_queue_rows": len(rows),
        "n_ready": sum(
            1
            for row in rows
            if row.get("execution_status")
            == "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
        ),
        "n_live_goal_requests": sum(1 for row in rows if row.get("live_proof_state_request")),
        "n_live_goal_location_ready": sum(
            1 for row in rows if row.get("live_goal_location_ready")
        ),
        "n_semantic_definition_review_blocked_rows": len(
            semantic_definition_review_blocked_rows
        ),
        "proof_body_recheck_blocked": proof_body_recheck_blocked,
        "proof_body_recheck_blocker": (
            "semantic_definition_review_blocked"
            if proof_body_recheck_blocked
            else ""
        ),
        "definition_candidate_review_modes": definition_candidate_review_modes,
        "semantic_definition_risks": list(
            dict.fromkeys(
                str(risk)
                for row in semantic_definition_review_blocked_rows
                for risk in [
                    *(row.get("semantic_definition_risks", []) or []),
                    str(row.get("semantic_risk", "") or ""),
                ]
                if str(risk).strip()
            )
        ),
        "source_theorem_kernel_evidence_eligible": False,
        "proof_evidence_status": (
            "EXACT_SOURCE_THEOREM_PROOF_BODY_RECHECK_QUEUE_NOT_PROOF_EVIDENCE"
        ),
        "boundary": BOUNDARY,
        "rows": rows,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["queue_jsonl"] = str(queue_path)
    return manifest


def _resolve_proof_body_queue_rows(
    *,
    proof_body_queue_manifest: Path | None,
    proof_body_queue_jsonl: Path | None,
) -> list[dict[str, Any]]:
    if proof_body_queue_jsonl is not None:
        return _read_jsonl(proof_body_queue_jsonl)
    if proof_body_queue_manifest is None:
        return []
    payload = json.loads(proof_body_queue_manifest.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    if isinstance(rows, list):
        return [dict(row) for row in rows if isinstance(row, Mapping)]
    queue_value = str(payload.get("proof_body_execution_queue_jsonl", "") or "")
    if not queue_value:
        return []
    queue_path = Path(queue_value)
    if not queue_path.exists():
        queue_path = proof_body_queue_manifest.parent / queue_path
    return _read_jsonl(queue_path) if queue_path.exists() else []


def _semantic_alignment_constraints_from_synthesis_rows(
    synthesis_rows: list[dict[str, Any]],
) -> list[str]:
    constraints: list[str] = []
    for row in synthesis_rows:
        constraints.extend(
            str(value)
            for value in row.get("semantic_alignment_constraints", []) or []
            if str(value).strip()
        )
        semantic_risk = str(row.get("semantic_risk", "") or "").strip()
        if semantic_risk:
            constraints.append(
                "unreviewed synthesized definition semantic risk: "
                + semantic_risk
            )
        constraints.extend(
            str(value)
            for value in row.get("semantic_alignment_blockers", []) or []
            if str(value).strip()
        )
    return list(dict.fromkeys(constraints))


def _typechecked_review_candidate_artifact_path(row: Mapping[str, Any]) -> Path | None:
    raw = _typechecked_review_candidate_artifact_path_text(row)
    return Path(raw) if raw else None


def _typechecked_review_candidate_artifact_path_text(row: Mapping[str, Any]) -> str:
    nested = row.get("source_theorem_exact_semantic_definition_typechecked_candidate")
    nested_mapping = nested if isinstance(nested, Mapping) else {}
    raw = str(
        row.get("candidate_artifact_path", "")
        or nested_mapping.get("candidate_artifact_path", "")
        or row.get("definition_only_candidate_artifact_path", "")
        or nested_mapping.get("definition_only_candidate_artifact_path", "")
        or ""
    ).strip()
    return raw


def _typechecked_review_definition_only_artifact_path(
    row: Mapping[str, Any],
) -> Path | None:
    nested = row.get("source_theorem_exact_semantic_definition_typechecked_candidate")
    nested_mapping = nested if isinstance(nested, Mapping) else {}
    raw = str(
        row.get("definition_only_candidate_artifact_path", "")
        or nested_mapping.get("definition_only_candidate_artifact_path", "")
        or ""
    ).strip()
    return Path(raw) if raw else None


def _typechecked_review_packet_ready_for_recheck(
    row: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    semantic_review_decision = str(
        row.get("semantic_review_decision", "") or ""
    ).strip()
    if not bool(row.get("source_theorem_ready_for_exact_proof_body", False)):
        blockers.append("source_theorem_ready_for_exact_proof_body_false")
    if bool(row.get("semantic_review_required_before_proof_body", False)):
        blockers.append("semantic_review_required_before_proof_body")
        if semantic_review_decision == "approved_definition_candidate":
            blockers.append(
                "llm_semantic_review_approved_requires_verifier_recheck_gate"
            )
        elif semantic_review_decision:
            blockers.append("llm_semantic_review_not_approved_for_recheck")
    semantic_blockers = [
        str(value)
        for value in row.get("semantic_alignment_blockers", []) or []
        if str(value).strip()
    ]
    semantic_risks = [
        str(value)
        for value in row.get("semantic_definition_risks", []) or []
        if str(value).strip()
    ]
    semantic_risk = str(row.get("semantic_risk", "") or "").strip()
    if semantic_risk:
        semantic_risks.append(semantic_risk)
    if semantic_blockers:
        blockers.append("semantic_alignment_blockers_present")
    if semantic_risks:
        blockers.append("semantic_definition_risks_present")
    if _typechecked_review_candidate_artifact_path(row) is None:
        blockers.append("candidate_artifact_path_missing")
    if bool(row.get("source_theorem_kernel_verified", False)):
        blockers.append("source_theorem_already_kernel_verified")
    return not blockers, blockers


def _typechecked_review_packet_as_synthesis_row(row: Mapping[str, Any]) -> dict[str, Any]:
    nested = row.get("source_theorem_exact_semantic_definition_typechecked_candidate")
    nested_mapping = nested if isinstance(nested, Mapping) else {}
    constraints = [
        str(value)
        for value in row.get("semantic_alignment_constraints", []) or []
        if str(value).strip()
    ]
    review_status = str(
        row.get("semantic_review_status", "")
        or row.get("source_semantic_faithfulness_review_status", "")
        or "approved_for_exact_source_theorem_proof_body_recheck"
    )
    constraints.append(
        "reviewed exact semantic-definition candidate approved for proof-body recheck"
    )
    return {
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "definition_candidate_review_mode": (
            "typechecked_candidate_source_semantic_review_approved"
        ),
        "semantic_alignment_constraints": list(dict.fromkeys(constraints)),
        "semantic_alignment_blockers": [],
        "semantic_definition_risks": [],
        "semantic_risk": "",
        "replacement_applied": False,
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
            or nested_mapping.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "")
            or nested_mapping.get("semantic_definition_typecheck_evidence_status", "")
            or ""
        ),
        "semantic_review_status": review_status,
    }


def _typechecked_review_requires_semantic_review_work_order(
    row: Mapping[str, Any],
) -> bool:
    blockers = [
        str(value)
        for value in row.get("proof_body_recheck_blockers", []) or []
        if str(value).strip()
    ]
    semantic_review_decision = str(
        row.get("semantic_review_decision", "") or ""
    ).strip()
    return (
        "semantic_review_required_before_proof_body" in blockers
        and not semantic_review_decision
        and "candidate_artifact_path_missing" not in blockers
    )


def _typechecked_review_semantic_review_work_order(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    base = _typechecked_review_blocked_learning_row(row)
    target = str(base.get("target_theorem_name", "") or "").strip()
    placeholder = str(base.get("placeholder_symbol", "") or "").strip()
    candidate_artifact_path = str(base.get("candidate_artifact_path", "") or "").strip()
    work_order_id = (
        "source_theorem_exact_semantic_definition_typechecked_semantic_review:"
        + stable_hash(
            [
                base.get("source_review_packet_id", ""),
                target,
                placeholder,
                candidate_artifact_path,
                base.get("proof_body_recheck_blockers", []),
            ]
        )[:20]
    )
    required_next_checks = [
        "compare the typechecked exact semantic-definition candidate against source theorem anchors and intended statistical meaning",
        "record an explicit semantic_review_decision and semantic_review_evidence for this candidate",
        "if the LLM reviewer approves the candidate, route it to the local Lean/AXLE verifier gate before proof-body recheck",
        "keep exact source theorem proof-body execution blocked until verifier-approved evidence clears the semantic-review gate",
    ]
    input_summary = {
        **(
            base.get("input_summary", {})
            if isinstance(base.get("input_summary", {}), Mapping)
            else {}
        ),
        "trigger": (
            "EXACT_SOURCE_SEMANTIC_DEFINITION_TYPECHECKED_SEMANTIC_REVIEW_REQUIRED"
        ),
        "semantic_review_work_order_id": work_order_id,
        "runtime_queue_status": (
            "PENDING_EXACT_SEMANTIC_DEFINITION_SEMANTIC_FAITHFULNESS_REVIEW"
        ),
        "failure_classification": (
            "typechecked_exact_semantic_definition_semantic_review_missing"
        ),
        "definition_candidate_review_mode": (
            "typechecked_candidate_semantic_faithfulness_review_required"
        ),
        "semantic_review_status": "semantic_faithfulness_review_required",
        "required_next_checks": required_next_checks,
    }
    return {
        **base,
        "artifact_kind": TYPECHECKED_REVIEW_SEMANTIC_REVIEW_WORK_ORDER_ARTIFACT_KIND,
        "learning_task": TYPECHECKED_REVIEW_SEMANTIC_REVIEW_LEARNING_TASK,
        "action_type": "review_typechecked_exact_semantic_definition_candidate",
        "work_order_id": work_order_id,
        "semantic_review_work_order_id": work_order_id,
        "trigger": (
            "EXACT_SOURCE_SEMANTIC_DEFINITION_TYPECHECKED_SEMANTIC_REVIEW_REQUIRED"
        ),
        "runtime_queue_status": (
            "PENDING_EXACT_SEMANTIC_DEFINITION_SEMANTIC_FAITHFULNESS_REVIEW"
        ),
        "failure_classification": (
            "typechecked_exact_semantic_definition_semantic_review_missing"
        ),
        "definition_candidate_review_mode": (
            "typechecked_candidate_semantic_faithfulness_review_required"
        ),
        "semantic_review_status": "semantic_faithfulness_review_required",
        "recommended_next_action": (
            "run semantic-faithfulness review for this typechecked exact "
            "semantic-definition candidate against source anchors and intended "
            "statistical meaning; only then route an approved candidate to the "
            "local Lean/AXLE verifier gate before proof-body recheck"
        ),
        "required_next_checks": required_next_checks,
        "acceptance_gate": (
            "Semantic review must produce an explicit decision and evidence tied "
            "to source anchors; LLM approval is still not proof evidence and must "
            "be followed by a local Lean/AXLE verifier gate before proof-body "
            "execution can resume."
        ),
        "input_summary": input_summary,
        "proof_evidence_status": (
            TYPECHECKED_REVIEW_SEMANTIC_REVIEW_PROOF_EVIDENCE_STATUS
        ),
        "proof_evidence_boundary": BOUNDARY,
        "boundary": BOUNDARY,
    }


def _typechecked_review_blocked_learning_row(row: Mapping[str, Any]) -> dict[str, Any]:
    nested = row.get("source_theorem_exact_semantic_definition_typechecked_candidate")
    nested_mapping = nested if isinstance(nested, Mapping) else {}
    target = str(row.get("target_theorem_name", "") or "").strip()
    placeholder = str(row.get("placeholder_symbol", "") or "").strip()
    candidate_artifact_path = _typechecked_review_candidate_artifact_path_text(row)
    definition_only_candidate_artifact_path = str(
        row.get("definition_only_candidate_artifact_path", "")
        or nested_mapping.get("definition_only_candidate_artifact_path", "")
        or ""
    ).strip()
    blockers = [
        str(value)
        for value in row.get("proof_body_recheck_blockers", []) or []
        if str(value).strip()
    ]
    semantic_review_evidence = [
        str(value)
        for value in row.get("semantic_review_evidence", []) or []
        if str(value).strip()
    ]
    semantic_alignment_blockers = [
        str(value)
        for value in row.get("semantic_alignment_blockers", []) or []
        if str(value).strip()
    ]
    if not semantic_alignment_blockers:
        semantic_alignment_blockers = list(blockers)
    required_next_checks = [
        "obtain explicit semantic review approval for the typechecked exact semantic-definition candidate",
        "rerun the typechecked review recheck queue only after semantic review clears",
        "keep the exact source theorem proof-body queue blocked until local Lean/AXLE verifies the theorem",
    ]
    if "candidate_artifact_path_missing" in blockers:
        required_next_checks.insert(
            1,
            "materialize or preserve candidate_artifact_path before proof-body recheck",
        )
    blocker_feedback_id = (
        "source_theorem_exact_semantic_definition_typechecked_review_blocked:"
        + stable_hash(
            [
                row.get("review_packet_id", ""),
                target,
                placeholder,
                candidate_artifact_path,
                definition_only_candidate_artifact_path,
                blockers,
            ]
        )[:20]
    )
    input_summary = {
        "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_TYPECHECKED_REVIEW_BLOCKED",
        "source_review_packet_id": str(row.get("review_packet_id", "") or ""),
        "target_theorem_name": target,
        "target_ids": _target_ids_from_row(row, fallback_target=target),
        "placeholder_symbol": placeholder,
        "candidate_artifact_path": candidate_artifact_path,
        "definition_only_candidate_artifact_path": (
            definition_only_candidate_artifact_path
        ),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
            or nested_mapping.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
            or nested_mapping.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "")
            or nested_mapping.get("semantic_definition_typecheck_evidence_status", "")
            or ""
        ),
        "semantic_review_decision": str(
            row.get("semantic_review_decision", "") or ""
        ),
        "semantic_review_status": str(row.get("semantic_review_status", "") or ""),
        "semantic_review_evidence": semantic_review_evidence,
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "proof_body_recheck_blockers": blockers,
        "proof_body_gate_status": "SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY",
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_kernel_verified": bool(
            row.get("source_theorem_kernel_verified", False)
        ),
        "source_theorem_kernel_evidence_eligible": False,
        "failure_classification": "semantic_definition_review_blocked",
        "runtime_queue_status": (
            "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
        ),
        "definition_candidate_review_mode": (
            "semantic_review_blocked_existing_candidate"
        ),
        "required_next_checks": required_next_checks,
    }
    return {
        "schema_version": 1,
        "artifact_kind": TYPECHECKED_REVIEW_BLOCKED_LEARNING_ROW_ARTIFACT_KIND,
        "learning_task": TYPECHECKED_REVIEW_BLOCKED_LEARNING_TASK,
        "action_type": "repair_reviewed_exact_semantic_definition",
        "work_order_id": blocker_feedback_id,
        "blocker_feedback_id": blocker_feedback_id,
        "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_TYPECHECKED_REVIEW_BLOCKED",
        "source_review_packet_id": str(row.get("review_packet_id", "") or ""),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target,
        "target_ids": _target_ids_from_row(row, fallback_target=target),
        "placeholder_symbol": placeholder,
        "candidate_artifact_path": candidate_artifact_path,
        "definition_only_candidate_artifact_path": (
            definition_only_candidate_artifact_path
        ),
        "local_definition_lean_checked": bool(
            input_summary["local_definition_lean_checked"]
        ),
        "local_definition_lean_compiled": bool(
            input_summary["local_definition_lean_compiled"]
        ),
        "semantic_definition_typecheck_evidence_status": str(
            input_summary["semantic_definition_typecheck_evidence_status"]
        ),
        "semantic_review_decision": str(input_summary["semantic_review_decision"]),
        "semantic_review_status": str(input_summary["semantic_review_status"]),
        "semantic_review_evidence": semantic_review_evidence,
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "semantic_review_required_before_proof_body": True,
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_kernel_verified": bool(
            input_summary["source_theorem_kernel_verified"]
        ),
        "source_theorem_kernel_evidence_eligible": False,
        "proof_body_recheck_blockers": blockers,
        "proof_body_gate_status": "SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY",
        "runtime_queue_status": (
            "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
        ),
        "failure_classification": "semantic_definition_review_blocked",
        "definition_candidate_review_mode": (
            "semantic_review_blocked_existing_candidate"
        ),
        "recommended_next_action": (
            "complete semantic-faithfulness review and candidate materialization for "
            "this typechecked exact semantic-definition candidate before proof-body "
            "recheck"
        ),
        "required_next_checks": required_next_checks,
        "acceptance_gate": (
            "Semantic review must approve the candidate, or emit a verifier-gate "
            "work order when LLM approval needs local checking; a later exact "
            "source theorem proof-body run must still kernel-check the target "
            "declaration before proof evidence is claimed."
        ),
        "input_summary": input_summary,
        "proof_evidence_status": TYPECHECKED_REVIEW_BLOCKED_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
        "boundary": BOUNDARY,
    }


def _typechecked_review_verifier_gate_work_order(
    row: Mapping[str, Any],
    *,
    source_rows: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    nested = row.get("source_theorem_exact_semantic_definition_typechecked_candidate")
    nested_mapping = nested if isinstance(nested, Mapping) else {}
    semantic_context = _merge_typechecked_review_semantic_context(
        _typechecked_review_semantic_context(row),
        _typechecked_review_source_proof_body_context(row, source_rows),
    )
    target = str(row.get("target_theorem_name", "") or "").strip()
    placeholder = str(row.get("placeholder_symbol", "") or "").strip()
    definition_only_candidate_artifact_path = str(
        row.get("definition_only_candidate_artifact_path", "")
        or nested_mapping.get("definition_only_candidate_artifact_path", "")
        or ""
    ).strip()
    candidate_artifact_path = _typechecked_review_candidate_artifact_path_text(row)
    blockers = [
        str(value)
        for value in row.get("proof_body_recheck_blockers", []) or []
        if str(value).strip()
    ]
    semantic_review_evidence = [
        str(value)
        for value in row.get("semantic_review_evidence", []) or []
        if str(value).strip()
    ]
    required_next_checks = [
        "run a local Lean/AXLE semantic-faithfulness verifier on the typechecked exact definition candidate",
        "record verifier-approved semantic review evidence before setting source_theorem_ready_for_exact_proof_body=true",
        "rerun the exact source theorem proof-body queue only after the verifier gate clears",
    ]
    work_order_id = (
        "source_theorem_exact_semantic_definition_typechecked_review_verifier_gate:"
        + stable_hash(
            [
                row.get("review_packet_id", ""),
                target,
                placeholder,
                candidate_artifact_path,
                blockers,
            ]
        )[:20]
    )
    input_summary = {
        "trigger": (
            "EXACT_SOURCE_SEMANTIC_DEFINITION_TYPECHECKED_REVIEW_VERIFIER_GATE_REQUIRED"
        ),
        "source_review_packet_id": str(row.get("review_packet_id", "") or ""),
        "target_theorem_name": target,
        "target_ids": _target_ids_from_row(row, fallback_target=target),
        "placeholder_symbol": placeholder,
        "candidate_artifact_path": candidate_artifact_path,
        "definition_only_candidate_artifact_path": (
            definition_only_candidate_artifact_path
        ),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
            or nested_mapping.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
            or nested_mapping.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "")
            or nested_mapping.get("semantic_definition_typecheck_evidence_status", "")
            or ""
        ),
        "semantic_review_decision": str(
            row.get("semantic_review_decision", "") or ""
        ),
        "semantic_review_status": str(row.get("semantic_review_status", "") or ""),
        "semantic_review_evidence": semantic_review_evidence,
        **semantic_context,
        "proof_body_recheck_blockers": blockers,
        "proof_body_gate_status": "SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY",
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_kernel_verified": bool(
            row.get("source_theorem_kernel_verified", False)
        ),
        "source_theorem_kernel_evidence_eligible": False,
        "failure_classification": (
            "typechecked_exact_semantic_definition_llm_review_requires_verifier_gate"
        ),
        "runtime_queue_status": (
            "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_RECHECK_GATE"
        ),
        "required_next_checks": required_next_checks,
    }
    return {
        "schema_version": 1,
        "artifact_kind": TYPECHECKED_REVIEW_VERIFIER_GATE_WORK_ORDER_ARTIFACT_KIND,
        "learning_task": TYPECHECKED_REVIEW_VERIFIER_GATE_LEARNING_TASK,
        "work_order_id": work_order_id,
        "source_review_packet_id": str(row.get("review_packet_id", "") or ""),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target,
        "target_ids": _target_ids_from_row(row, fallback_target=target),
        "placeholder_symbol": placeholder,
        "candidate_artifact_path": candidate_artifact_path,
        "definition_only_candidate_artifact_path": (
            definition_only_candidate_artifact_path
        ),
        "local_definition_lean_checked": bool(
            input_summary["local_definition_lean_checked"]
        ),
        "local_definition_lean_compiled": bool(
            input_summary["local_definition_lean_compiled"]
        ),
        "semantic_definition_typecheck_evidence_status": str(
            input_summary["semantic_definition_typecheck_evidence_status"]
        ),
        "semantic_review_decision": str(input_summary["semantic_review_decision"]),
        "semantic_review_status": str(input_summary["semantic_review_status"]),
        "semantic_review_evidence": semantic_review_evidence,
        **semantic_context,
        "semantic_review_required_before_proof_body": True,
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_kernel_verified": bool(
            input_summary["source_theorem_kernel_verified"]
        ),
        "source_theorem_kernel_evidence_eligible": False,
        "proof_body_recheck_blockers": blockers,
        "proof_body_gate_status": "SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY",
        "runtime_queue_status": (
            "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_RECHECK_GATE"
        ),
        "action_type": "verify_typechecked_exact_semantic_definition_candidate",
        "failure_classification": (
            "typechecked_exact_semantic_definition_llm_review_requires_verifier_gate"
        ),
        "definition_candidate_review_mode": (
            "llm_semantic_review_requires_verifier_gate"
        ),
        "recommended_next_action": (
            "run the formal verifier/Lean semantic-faithfulness gate for this "
            "typechecked exact semantic-definition candidate; keep the exact "
            "source theorem proof body blocked until verifier-approved evidence "
            "clears semantic_review_required_before_proof_body"
        ),
        "required_next_checks": required_next_checks,
        "acceptance_gate": (
            "A local Lean/AXLE verifier must approve the candidate's semantic "
            "faithfulness and a later exact source theorem proof-body run must "
            "kernel-check the target declaration; LLM semantic review alone is "
            "not proof evidence and cannot set proof-body readiness."
        ),
        "input_summary": input_summary,
        "proof_evidence_status": (
            TYPECHECKED_REVIEW_VERIFIER_GATE_PROOF_EVIDENCE_STATUS
        ),
        "proof_evidence_boundary": BOUNDARY,
    }


def _merge_typechecked_review_semantic_context(
    primary: Mapping[str, Any],
    supplemental: Mapping[str, Any],
) -> dict[str, Any]:
    context = dict(primary)
    for key, value in supplemental.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            merged = [
                dict(item) if isinstance(item, Mapping) else str(item)
                for item in context.get(key, []) or []
            ]
            seen = {json.dumps(item, sort_keys=True, default=str) for item in merged}
            for item in value:
                copied = dict(item) if isinstance(item, Mapping) else str(item)
                marker = json.dumps(copied, sort_keys=True, default=str)
                if marker not in seen:
                    merged.append(copied)
                    seen.add(marker)
            if merged:
                context[key] = merged
            continue
        context.setdefault(key, value)
    return context


def _typechecked_review_source_proof_body_context(
    row: Mapping[str, Any],
    source_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    matched_rows = _matching_typechecked_review_source_rows(row, source_rows)
    if not matched_rows:
        return {}
    source_anchors: list[dict[str, Any]] = []
    exact_source_theorem_binders: list[dict[str, Any]] = []
    for source_row in matched_rows:
        goal_excerpt = [
            str(value)
            for value in source_row.get("proof_body_goal_excerpt", []) or []
            if str(value).strip()
        ]
        source_anchors.append(
            {
                "source": "exact_source_theorem_proof_body_execution_queue",
                "kind": "proof_body_goal_context",
                "execution_queue_id": str(
                    source_row.get("execution_queue_id", "") or ""
                ),
                "target_theorem_name": str(
                    source_row.get("target_theorem_name", "") or ""
                ),
                "target_lean_declaration": str(
                    source_row.get("target_lean_declaration", "") or ""
                ),
                "target_lean_file": str(source_row.get("target_lean_file", "") or ""),
                "target_lean_line": int(source_row.get("target_lean_line", 0) or 0),
                "source_theorem_target_identity_status": str(
                    source_row.get("source_theorem_target_identity_status", "") or ""
                ),
                "semantic_alignment_constraints": [
                    str(value)
                    for value in source_row.get("semantic_alignment_constraints", [])
                    or []
                    if str(value).strip()
                ][:8],
                "proof_body_goal_excerpt": goal_excerpt[:16],
                "proof_evidence_status": (
                    TYPECHECKED_REVIEW_VERIFIER_GATE_PROOF_EVIDENCE_STATUS
                ),
            }
        )
        exact_source_theorem_binders.extend(
            _source_goal_binders_from_proof_body_excerpt(goal_excerpt)
        )
    context: dict[str, Any] = {
        "source_anchors": source_anchors,
        "exact_source_theorem_binders": _dedupe_mapping_rows(
            exact_source_theorem_binders
        ),
        "source_reference_hints": [
            {
                "source": "exact_source_theorem_proof_body_execution_queue",
                "kind": "proof_body_queue_manifest_context",
                "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
                "n_matching_source_rows": len(matched_rows),
            }
        ],
    }
    if context["exact_source_theorem_binders"]:
        context["premise_semantic_anchor_binders"] = list(
            context["exact_source_theorem_binders"]
        )
        context["premise_semantic_anchor_binder_names"] = [
            str(binder.get("name", "") or "")
            for binder in context["exact_source_theorem_binders"]
            if str(binder.get("name", "") or "").strip()
        ]
    return context


def _matching_typechecked_review_source_rows(
    row: Mapping[str, Any],
    source_rows: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    target = str(row.get("target_theorem_name", "") or "").strip()
    target_ids = set(_target_ids_from_row(row, fallback_target=target))
    matches: list[Mapping[str, Any]] = []
    for source_row in source_rows:
        if not isinstance(source_row, Mapping):
            continue
        source_target = str(source_row.get("target_theorem_name", "") or "").strip()
        source_identifiers = set(
            _target_ids_from_row(source_row, fallback_target=source_target)
        )
        for key in (
            "target_lean_declaration",
            "expected_target_lean_declaration",
        ):
            value = str(source_row.get(key, "") or "").strip()
            if value:
                source_identifiers.add(value)
        if (
            (target and target in source_identifiers)
            or bool(target_ids.intersection(source_identifiers))
            or (
                len(source_rows) == 1
                and not target_ids
                and not source_identifiers
            )
        ):
            matches.append(source_row)
    return matches


def _typechecked_review_source_rows_for_recheck(
    row: Mapping[str, Any],
    source_rows: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Select source proof-body rows for a verifier-approved review packet."""

    source_mappings = [
        source_row for source_row in source_rows if isinstance(source_row, Mapping)
    ]
    target = str(row.get("target_theorem_name", "") or "").strip()
    target_ids = _target_ids_from_row(row, fallback_target=target)
    if not target and not target_ids:
        return source_mappings
    matches = _matching_typechecked_review_source_rows(row, source_mappings)
    if not matches:
        return []
    target_known_rows = [
        source_row
        for source_row in matches
        if _source_row_target_identity_ready_for_recheck(source_row)
    ]
    return target_known_rows or matches


def _source_row_target_identity_ready_for_recheck(row: Mapping[str, Any]) -> bool:
    source_status = str(
        row.get("source_theorem_target_identity_status", "") or ""
    ).strip()
    target_status = str(row.get("target_identity_status", "") or "").strip()
    execution_status = str(row.get("execution_status", "") or "").strip()
    return (
        source_status
        in {
            "SOURCE_THEOREM_TARGET_KNOWN",
            "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED",
        }
        or target_status == "TARGET_DECLARATION_MATCHED"
        or execution_status == "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
        or bool(row.get("live_goal_location_ready", False))
    )


def _source_goal_binders_from_proof_body_excerpt(
    proof_body_goal_excerpt: Sequence[str],
) -> list[dict[str, Any]]:
    binders: list[dict[str, Any]] = []
    lines = [str(line).strip() for line in proof_body_goal_excerpt]
    for index, line in enumerate(lines):
        if not line or line.startswith("/") or " error:" in line or line.startswith("⊢"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_']*)\s*:\s*(.*)$", line)
        if match is None:
            continue
        name = match.group(1).strip()
        binder_type = match.group(2).strip()
        continuation: list[str] = []
        next_index = index + 1
        while next_index < len(lines):
            next_line = lines[next_index]
            if (
                not next_line
                or next_line.startswith("/")
                or next_line.startswith("⊢")
                or re.match(r"^[A-Za-z_][A-Za-z0-9_']*\s*:", next_line)
            ):
                break
            continuation.append(next_line)
            next_index += 1
        full_type = " ".join([binder_type, *continuation]).strip()
        if not full_type:
            continue
        binders.append(
            {
                "name": name,
                "type": full_type,
                "role": (
                    "source_theorem_hypothesis"
                    if name.startswith("h")
                    else "source_theorem_parameter"
                ),
                "source": "proof_body_goal_excerpt",
            }
        )
    return _dedupe_mapping_rows(binders)


def _dedupe_mapping_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        copied = dict(row)
        marker = json.dumps(copied, sort_keys=True, default=str)
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(copied)
    return deduped


def _typechecked_review_has_source_anchor_context(row: Mapping[str, Any]) -> bool:
    return bool(
        row.get("source_anchor_context")
        or row.get("source_anchors")
        or row.get("exact_source_theorem_binders")
        or row.get("premise_semantic_anchor_binders")
        or row.get("source_reference_hints")
    )


def _typechecked_review_semantic_context(row: Mapping[str, Any]) -> dict[str, Any]:
    nested = row.get("source_theorem_exact_semantic_definition_typechecked_candidate")
    nested_mapping = nested if isinstance(nested, Mapping) else {}
    feedback = row.get("candidate_repair_feedback")
    feedback_mapping = feedback if isinstance(feedback, Mapping) else {}
    context: dict[str, Any] = {}
    for key in (
        "semantic_alignment_constraints",
        "semantic_alignment_blockers",
        "source_anchor_context",
        "source_reference_hints",
        "candidate_source_references",
        "source_anchors",
        "exact_source_theorem_binders",
        "premise_semantic_anchor_binders",
        "premise_semantic_anchor_binder_names",
        "required_anchor_names",
        "required_semantic_anchor_reference_names",
    ):
        values = row.get(key, nested_mapping.get(key, []))
        if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
            copied = [
                dict(value) if isinstance(value, Mapping) else str(value)
                for value in values
                if str(value).strip()
            ]
            if copied:
                context[key] = copied
    if "source_anchor_context" not in context:
        feedback_context = feedback_mapping.get("source_anchor_context", [])
        if isinstance(feedback_context, Sequence) and not isinstance(
            feedback_context,
            (str, bytes),
        ):
            copied_feedback_context = [
                dict(value) if isinstance(value, Mapping) else str(value)
                for value in feedback_context
                if str(value).strip()
            ]
            if copied_feedback_context:
                context["source_anchor_context"] = copied_feedback_context
    raw_context_rows = (
        row.get("source_anchor_context_rows", None)
        or nested_mapping.get("source_anchor_context_rows", None)
        or feedback_mapping.get("source_anchor_context_rows", None)
        or len(context.get("source_anchor_context", []) or [])
    )
    try:
        source_anchor_context_rows = int(raw_context_rows)
    except (TypeError, ValueError):
        source_anchor_context_rows = len(context.get("source_anchor_context", []) or [])
    if source_anchor_context_rows:
        context["source_anchor_context_rows"] = source_anchor_context_rows
    request = row.get("candidate_definition_request") or nested_mapping.get(
        "candidate_definition_request"
    )
    if isinstance(request, Mapping):
        context["candidate_definition_request"] = dict(request)
    contract = row.get("definition_contract") or nested_mapping.get(
        "definition_contract"
    )
    if isinstance(contract, Mapping):
        context["definition_contract"] = dict(contract)
        known_gaps = [
            str(value)
            for value in contract.get("known_gaps", []) or []
            if str(value).strip()
        ]
        if known_gaps:
            context["known_gaps"] = known_gaps
    return context


def _is_stale_replaced_semantic_definition_risk(value: str) -> bool:
    text = str(value)
    return (
        "semantic_definition_risk:" in text
        or "unreviewed synthesized definition semantic risk:" in text
    )


def _proof_body_recheck_queue_row(
    row: Mapping[str, Any],
    *,
    synthesized_artifact_path: Path,
    semantic_constraints: list[str],
    synthesized_exact_semantic_definitions: bool,
    definition_candidate_review_modes: list[str],
    out_dir: Path,
    reviewed_definition_only_artifact_path: Path | None = None,
) -> dict[str, Any]:
    target = str(row.get("target_theorem_name", "") or "")
    target_ids = _target_ids_from_row(row, fallback_target=target)
    expected_target = str(
        row.get("expected_target_lean_declaration", "")
        or row.get("target_lean_declaration", "")
        or target
    )
    observed_target = str(row.get("target_lean_declaration", "") or target)
    target_identity_errors = [
        str(value)
        for value in row.get("target_identity_errors", []) or []
        if str(value).strip()
    ]
    target_identity_status = str(row.get("target_identity_status", "") or "")
    source_theorem_target_known = bool(row.get("source_theorem_target_known", False))
    source_theorem_target_identity_status = str(
        row.get("source_theorem_target_identity_status", "") or ""
    ) or _source_theorem_target_identity_status(
        source_theorem_target_known=source_theorem_target_known,
        target_identity_status=target_identity_status,
        target_identity_errors=target_identity_errors,
        expected_target_lean_declaration=expected_target,
        target_lean_declaration=observed_target,
    )
    source_constraints = [
        str(value)
        for value in row.get("semantic_alignment_constraints", []) or []
        if str(value).strip()
    ]
    if synthesized_exact_semantic_definitions:
        source_constraints = [
            value
            for value in source_constraints
            if not _is_stale_replaced_semantic_definition_risk(value)
        ]
    constraints = list(dict.fromkeys([*source_constraints, *semantic_constraints]))
    semantic_blockers = [
        str(value)
        for value in row.get("semantic_alignment_blockers", []) or []
        if str(value).strip()
    ]
    if synthesized_exact_semantic_definitions:
        semantic_blockers = [
            value
            for value in semantic_blockers
            if not _is_stale_replaced_semantic_definition_risk(value)
        ]
    original_environment = dict(row.get("already_repaired_environment", {}) or {})
    recheck_environment = {
        "missing_formal_symbols": [],
        "typeclass_blockers": [],
        "signature_typecheck_reached_proof_body": bool(
            original_environment.get("signature_typecheck_reached_proof_body", False)
        ),
        "synthesized_exact_semantic_definitions": bool(
            synthesized_exact_semantic_definitions
        ),
        "definition_candidate_review_modes": definition_candidate_review_modes,
        "original_missing_formal_symbols": list(
            original_environment.get("missing_formal_symbols", []) or []
        ),
        "original_typeclass_blockers": list(
            original_environment.get("typeclass_blockers", []) or []
        ),
    }
    recheck_id = "exact_source_theorem_proof_body_execution_queue_recheck:" + stable_hash(
        [
            row.get("execution_queue_id", ""),
            target,
            str(synthesized_artifact_path),
            constraints,
        ]
    )[:20]
    transcript_path = (
        out_dir
        / "execution_transcripts"
        / f"{_safe_identifier(target or 'exact_source_theorem')}_synthesized_definition_recheck.jsonl"
    )
    reviewed_definition_only = reviewed_definition_only_artifact_path is not None
    signature_probe_artifact_path = (
        str(row.get("signature_probe_artifact_path", "") or "")
        if reviewed_definition_only
        else str(synthesized_artifact_path)
    )
    proof_body_candidate_artifact_path = (
        str(_reviewed_definition_recheck_candidate_artifact_path(row, out_dir=out_dir))
        if reviewed_definition_only
        else str(synthesized_artifact_path)
    )
    source_candidate_artifact_path = (
        str(row.get("source_candidate_artifact_path", "") or "")
        if reviewed_definition_only
        else str(synthesized_artifact_path)
    )
    return {
        **dict(row),
        "execution_queue_id": recheck_id,
        "source_execution_queue_id": str(row.get("execution_queue_id", "") or ""),
        "target_ids": target_ids,
        "source_candidate_artifact_path": source_candidate_artifact_path,
        "signature_probe_artifact_path": signature_probe_artifact_path,
        "candidate_artifact_path": proof_body_candidate_artifact_path,
        "reviewed_exact_semantic_definition_artifact_path": str(
            reviewed_definition_only_artifact_path or ""
        ),
        "reviewed_exact_semantic_definition_artifact_paths": (
            [str(reviewed_definition_only_artifact_path)]
            if reviewed_definition_only_artifact_path is not None
            else []
        ),
        "execution_transcript_path": str(transcript_path),
        "semantic_alignment_constraints": constraints,
        "semantic_alignment_blockers": semantic_blockers,
        "source_theorem_target_identity_status": (
            source_theorem_target_identity_status
        ),
        "source_theorem_kernel_evidence_eligible": False,
        "already_repaired_environment": recheck_environment,
        "proof_body_attempt_source": (
            "synthesized_exact_semantic_definition_recheck_queue"
            if synthesized_exact_semantic_definitions
            else "reviewed_existing_semantic_definition_recheck_queue"
        ),
        "proof_evidence_status": (
            "EXACT_SOURCE_THEOREM_PROOF_BODY_RECHECK_QUEUE_NOT_PROOF_EVIDENCE"
        ),
        "boundary": BOUNDARY,
    }


def _reviewed_definition_recheck_candidate_artifact_path(
    row: Mapping[str, Any],
    *,
    out_dir: Path,
) -> Path:
    target = str(
        row.get("target_lean_declaration", "")
        or row.get("target_theorem_name", "")
        or "exact_source_theorem"
    )
    source_marker = str(
        row.get("execution_queue_id", "")
        or row.get("signature_probe_artifact_path", "")
        or target
    )
    filename = (
        f"{_safe_identifier(target)}_reviewed_semantic_definition_recheck_"
        f"{stable_hash([source_marker, target])[:10]}.lean"
    )
    return out_dir / "candidate_artifacts" / filename


def _source_theorem_target_identity_status(
    *,
    source_theorem_target_known: bool,
    target_identity_status: str,
    target_identity_errors: list[str],
    expected_target_lean_declaration: str,
    target_lean_declaration: str,
) -> str:
    if target_identity_errors or target_identity_status == "TARGET_DECLARATION_MISMATCH":
        return "TARGET_DECLARATION_MISMATCH"
    if source_theorem_target_known:
        return "SOURCE_THEOREM_TARGET_KNOWN"
    expected = str(expected_target_lean_declaration or "").strip()
    observed = str(target_lean_declaration or "").strip()
    if (
        target_identity_status == "TARGET_DECLARATION_MATCHED"
        and expected
        and observed
        and expected == observed
    ):
        return "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    if observed:
        return "DECLARATION_FOUND_SOURCE_THEOREM_TARGET_UNPROMOTED"
    return "SOURCE_THEOREM_TARGET_UNKNOWN"


def _safe_identifier(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return safe or "artifact"


def resolve_exact_semantic_definition_review_results_path(
    *,
    review_manifest: Path | None = None,
    review_results_jsonl: Path | None = None,
) -> Path:
    if review_results_jsonl is not None:
        return review_results_jsonl
    if review_manifest is None:
        raise ValueError("review_manifest or review_results_jsonl is required")
    manifest = json.loads(review_manifest.read_text(encoding="utf-8"))
    raw_path = str(manifest.get("review_results_jsonl", "") or "")
    if not raw_path:
        raise ValueError("review manifest does not list review_results_jsonl")
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidates = [
        review_manifest.parent / path,
        review_manifest.parent.parent / path,
    ]
    parts = path.parts
    if parts and parts[0] == review_manifest.parent.name:
        candidates.append(review_manifest.parent.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_exact_semantic_definition_review_packets_path(
    *,
    review_packets_jsonl: Path | None = None,
    lookup_manifest: Path | None = None,
) -> Path:
    if review_packets_jsonl is not None:
        return review_packets_jsonl
    if lookup_manifest is None:
        raise ValueError("review_packets_jsonl or lookup_manifest is required")
    manifest = json.loads(lookup_manifest.read_text(encoding="utf-8"))
    raw_path = str(manifest.get("definition_closure_review_packets_jsonl", "") or "")
    if not raw_path:
        raise ValueError(
            "lookup manifest does not list definition_closure_review_packets_jsonl"
        )
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidates = [
        lookup_manifest.parent / path,
        lookup_manifest.parent.parent / path,
    ]
    parts = path.parts
    if parts and parts[0] == lookup_manifest.parent.name:
        candidates.append(lookup_manifest.parent.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_exact_semantic_definition_work_order_path(
    *,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
) -> Path:
    if queue_jsonl is not None:
        return queue_jsonl
    if runtime_dir is None:
        raise ValueError("runtime_dir or queue_jsonl is required")
    manifest_path = runtime_dir / "research_agent_runtime_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        artifacts = {}
    raw_path = str(
        artifacts.get("runtime_source_theorem_exact_semantic_definition_work_orders_jsonl", "")
        or ""
    )
    if not raw_path:
        raise ValueError(
            "runtime manifest does not list "
            "runtime_source_theorem_exact_semantic_definition_work_orders_jsonl"
        )
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidates = [runtime_dir / path, runtime_dir.parent / path]
    parts = path.parts
    if parts and parts[0] == runtime_dir.name:
        candidates.append(runtime_dir.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _lookup_row(
    *,
    work_order: Mapping[str, Any],
    source_roots: list[Path],
    max_hits: int,
) -> dict[str, Any]:
    placeholder = str(work_order.get("placeholder_symbol", "") or "").strip()
    placeholder_policy_context = _placeholder_policy_context(placeholder)
    search_terms = _search_terms(work_order)
    hits = _source_lookup_hits(
        source_roots=source_roots,
        search_terms=search_terms,
        max_hits=max_hits,
        work_order=work_order,
    )
    declaration_hits = [
        hit
        for hit in hits
        if hit.get("candidate_kind") == "lean_declaration"
        and hit.get("semantic_import_candidate_allowed", True)
    ]
    reference_hits = [
        hit
        for hit in hits
        if hit.get("candidate_kind") != "lean_declaration"
        or not hit.get("semantic_import_candidate_allowed", True)
    ]
    lookup_status = (
        "CANDIDATE_SOURCE_DECLARATIONS_FOUND"
        if declaration_hits
        else "CANDIDATE_SOURCE_REFERENCES_FOUND"
        if hits
        else "NO_REVIEWED_FORMAL_DEFINITION_FOUND"
    )
    lookup_id = "source_theorem_exact_semantic_definition_source_lookup:" + stable_hash(
        [
            work_order.get("work_order_id", ""),
            work_order.get("target_theorem_name", ""),
            placeholder,
            search_terms,
            hits,
            work_order.get("definition_only_candidate_artifact_path", ""),
            work_order.get("semantic_definition_typecheck_evidence_status", ""),
        ]
    )[:20]
    return {
        "schema_version": 1,
        "artifact_kind": LOOKUP_ROW_ARTIFACT_KIND,
        "lookup_id": lookup_id,
        "source_work_order_id": str(work_order.get("work_order_id", "") or ""),
        "question_id": str(work_order.get("question_id", "") or ""),
        "question_title": str(work_order.get("question_title", "") or ""),
        "target_theorem_name": str(work_order.get("target_theorem_name", "") or ""),
        "placeholder_symbol": placeholder,
        **placeholder_policy_context,
        "replacement_strategy": str(work_order.get("replacement_strategy", "") or ""),
        "search_terms": search_terms,
        "source_roots": [str(root) for root in source_roots],
        "lookup_status": lookup_status,
        "source_lookup_hits": hits,
        "candidate_source_declarations": declaration_hits,
        "candidate_source_references": reference_hits,
        "candidate_registered_obligation_ids": list(
            work_order.get("candidate_registered_obligation_ids", []) or []
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
            work_order.get(
                "kernel_verified_source_theorem_semantic_support_obligation_ids",
                [],
            )
            or []
        ),
        "kernel_verified_source_theorem_semantic_definition_ids": [],
        "source_semantic_alignment_review_required": bool(
            work_order.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            work_order.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            work_order.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            work_order.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            work_order.get("semantic_alignment_blockers", []) or []
        ),
        "source_theorem_exact_semantic_definition_typechecked_candidate": dict(
            work_order.get(
                "source_theorem_exact_semantic_definition_typechecked_candidate",
                {},
            )
            or {}
        ),
        "definition_only_candidate_artifact_path": str(
            work_order.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_path": str(
            work_order.get("candidate_artifact_path", "") or ""
        ),
        "local_definition_lean_checked": bool(
            work_order.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            work_order.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            work_order.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        **_exact_semantic_definition_context(work_order),
        "semantic_closure_status": str(
            work_order.get("semantic_closure_status", "") or ""
        ),
        "placeholder_definition_status": str(
            work_order.get("placeholder_definition_status", "") or ""
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_semantic_support_only": True,
        "action_type": "lookup_reviewed_exact_semantic_definition_source",
        "acceptance_gate": (
            "A human-reviewed or Lean-verified exact semantic definition is selected "
            "and then local Lean/AXLE verifies the downstream source theorem."
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _exact_semantic_definition_context(row: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve source-to-bridge authoring context across lookup/repair stages."""

    context: dict[str, Any] = {}
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    placeholder_symbol = str(
        row.get("placeholder_symbol", "")
        or input_summary.get("placeholder_symbol", "")
        or ""
    ).strip()
    for key in EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS:
        value = row.get(key, None)
        if value in (None, "", [], {}):
            value = input_summary.get(key, None)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, Mapping):
            context[key] = dict(value)
        elif isinstance(value, list):
            context[key] = list(value)
        else:
            context[key] = value
    if placeholder_symbol:
        for key, value in _placeholder_policy_context(placeholder_symbol).items():
            context.setdefault(key, value)
    candidate_request = context.get("candidate_definition_request", {})
    if isinstance(candidate_request, Mapping):
        target_theorem_name = str(row.get("target_theorem_name", "") or "")
        target_ids = _target_ids_from_row(row, fallback_target=target_theorem_name)
        normalized_request = dict(candidate_request)
        normalized_request.setdefault("target_theorem_name", target_theorem_name)
        if placeholder_symbol and not normalized_request.get("placeholder_symbol"):
            normalized_request["placeholder_symbol"] = placeholder_symbol
        if placeholder_symbol:
            for key, value in _placeholder_policy_context(placeholder_symbol).items():
                normalized_request.setdefault(key, value)
        if target_ids and not normalized_request.get("target_ids"):
            normalized_request["target_ids"] = list(target_ids)
        context["candidate_definition_request"] = normalized_request
    return context


def _placeholder_policy_context(placeholder_symbol: str) -> dict[str, str]:
    placeholder = str(placeholder_symbol or "").strip()
    if not placeholder:
        return {}
    policy = exact_semantic_definition_placeholder_policy(placeholder)
    return {
        "placeholder_policy_id": policy.policy_id,
        "placeholder_policy_scope": policy.policy_scope,
    }


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


def _definition_closure_work_order_from_lookup(row: Mapping[str, Any]) -> dict[str, Any]:
    lookup_status = str(row.get("lookup_status", "") or "")
    candidate_declarations = list(row.get("candidate_source_declarations", []) or [])
    candidate_references = list(row.get("candidate_source_references", []) or [])
    has_typechecked_candidate = bool(
        row.get("definition_only_candidate_artifact_path")
        or row.get("local_definition_lean_compiled")
        or row.get("semantic_definition_typecheck_evidence_status")
    )
    candidate_review_handoff = bool(
        has_typechecked_candidate
        and not candidate_declarations
        and not candidate_references
        and not list(row.get("semantic_alignment_blockers", []) or [])
    )
    if lookup_status == "CANDIDATE_SOURCE_DECLARATIONS_FOUND":
        next_step_kind = "REVIEW_IMPORT_CANDIDATE_SOURCE_DECLARATION"
        target_behavior = (
            "Review candidate Lean declarations, select the semantically faithful "
            "definition/import for the placeholder, then rerun local Lean on the "
            "exact source theorem artifact."
        )
    elif lookup_status == "CANDIDATE_SOURCE_REFERENCES_FOUND":
        next_step_kind = "SYNTHESIZE_REVIEWED_DEFINITION_FROM_SOURCE_REFERENCES"
        target_behavior = (
            "Use source references as guidance to draft a reviewed exact Lean "
            "definition for the placeholder, keeping the definition separate from "
            "proof evidence until local Lean/AXLE verifies downstream claims."
        )
    elif candidate_review_handoff:
        next_step_kind = "REVIEW_TYPECHECKED_EXACT_DEFINITION_CANDIDATE"
        target_behavior = (
            "Review the typechecked definition-only candidate for source semantic "
            "faithfulness, then import it into the exact source theorem artifact and "
            "rerun local Lean/AXLE. Typechecking is not proof of the source theorem."
        )
    else:
        next_step_kind = "SYNTHESIZE_MINIMAL_EXACT_DEFINITION_WITH_SOURCE_REVIEW"
        target_behavior = (
            "Search/review sources further, then synthesize a minimal exact Lean "
            "definition for the placeholder before attempting the source theorem "
            "proof body again."
        )
    work_order_id = (
        "source_theorem_exact_semantic_definition_closure_work_order:"
        + stable_hash(
            [
                row.get("lookup_id", ""),
                row.get("source_work_order_id", ""),
                row.get("target_theorem_name", ""),
                row.get("placeholder_symbol", ""),
                lookup_status,
                candidate_declarations,
                candidate_references,
                row.get("definition_only_candidate_artifact_path", ""),
                row.get("semantic_definition_typecheck_evidence_status", ""),
            ]
        )[:20]
    )
    return {
        "schema_version": 1,
        "artifact_kind": DEFINITION_CLOSURE_WORK_ORDER_ARTIFACT_KIND,
        "work_order_id": work_order_id,
        "source_lookup_id": str(row.get("lookup_id", "") or ""),
        "source_exact_semantic_definition_work_order_id": str(
            row.get("source_work_order_id", "") or ""
        ),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "lookup_status": lookup_status,
        "next_step_kind": next_step_kind,
        "action_type": "close_reviewed_exact_semantic_definition",
        "owner_agent": "Formalizer/ProofEngineer/LeanProver",
        "replacement_strategy": str(row.get("replacement_strategy", "") or ""),
        "candidate_source_declarations": candidate_declarations,
        "candidate_source_references": candidate_references,
        "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
        "candidate_registered_obligation_ids": list(
            row.get("candidate_registered_obligation_ids", []) or []
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
            row.get(
                "kernel_verified_source_theorem_semantic_support_obligation_ids",
                [],
            )
            or []
        ),
        "kernel_verified_source_theorem_semantic_definition_ids": [],
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "source_theorem_exact_semantic_definition_typechecked_candidate": dict(
            row.get(
                "source_theorem_exact_semantic_definition_typechecked_candidate",
                {},
            )
            or {}
        ),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        **_exact_semantic_definition_context(row),
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_semantic_support_only": True,
        "target_behavior": target_behavior,
        "acceptance_gate": (
            "A reviewed exact semantic definition/import replaces the placeholder, "
            "then local Lean/AXLE verifies the exact source theorem or records the "
            "next concrete proof blocker. This work order itself is not proof."
        ),
        "proof_evidence_status": DEFINITION_CLOSURE_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _definition_closure_review_packet(row: Mapping[str, Any]) -> dict[str, Any]:
    placeholder = str(row.get("placeholder_symbol", "") or "")
    contract = _definition_contract_for_placeholder(placeholder)
    review_packet_id = (
        "source_theorem_exact_semantic_definition_closure_review_packet:"
        + stable_hash(
            [
                row.get("work_order_id", ""),
                row.get("source_lookup_id", ""),
                row.get("target_theorem_name", ""),
                placeholder,
                row.get("lookup_status", ""),
                row.get("next_step_kind", ""),
                contract,
                row.get("definition_only_candidate_artifact_path", ""),
                row.get("semantic_definition_typecheck_evidence_status", ""),
            ]
        )[:20]
    )
    required_next_checks = [
        "review candidate source declarations/references against the paper theorem semantics",
        "write or import the exact Lean definition that replaces the placeholder",
        "run local Lean/AXLE on the repaired exact source theorem candidate",
        "keep support bridge obligations separate from exact definition evidence",
    ]
    return {
        "schema_version": 1,
        "artifact_kind": DEFINITION_CLOSURE_REVIEW_PACKET_ARTIFACT_KIND,
        "review_packet_id": review_packet_id,
        "source_definition_closure_work_order_id": str(
            row.get("work_order_id", "") or ""
        ),
        "source_lookup_id": str(row.get("source_lookup_id", "") or ""),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "placeholder_symbol": placeholder,
        "lookup_status": str(row.get("lookup_status", "") or ""),
        "next_step_kind": str(row.get("next_step_kind", "") or ""),
        "definition_candidate_status": "REQUIRES_REVIEWED_LEAN_DEFINITION",
        "definition_contract": contract,
        "candidate_source_declarations": list(
            row.get("candidate_source_declarations", []) or []
        ),
        "candidate_source_references": list(
            row.get("candidate_source_references", []) or []
        ),
        "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
        "candidate_registered_obligation_ids": list(
            row.get("candidate_registered_obligation_ids", []) or []
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
            row.get(
                "kernel_verified_source_theorem_semantic_support_obligation_ids",
                [],
            )
            or []
        ),
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "source_theorem_exact_semantic_definition_typechecked_candidate": dict(
            row.get(
                "source_theorem_exact_semantic_definition_typechecked_candidate",
                {},
            )
            or {}
        ),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        **_exact_semantic_definition_context(row),
        "required_next_checks": required_next_checks,
        "target_behavior": (
            "Turn the closure work order into a reviewed exact Lean definition/import "
            "for the placeholder before attempting the source theorem proof body."
        ),
        "acceptance_gate": (
            "The reviewed exact definition is present in the Lean candidate and "
            "local Lean/AXLE either verifies the exact source theorem or reports a "
            "new non-placeholder proof blocker. This packet itself is not proof."
        ),
        "proof_evidence_status": DEFINITION_CLOSURE_REVIEW_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _definition_contract_for_placeholder(placeholder: str) -> dict[str, Any]:
    normalized = placeholder.strip().lower()
    if normalized == "exchangeable":
        return {
            "semantic_intent": (
                "finite calibration/test score family has a permutation-invariant "
                "joint law under the probability measure"
            ),
            "lean_target_shape": (
                "predicate over `P : Measure Ω` and `s : Fin (n + 1) -> Ω -> ℝ`"
            ),
            "required_properties": [
                "invariance under finite index permutations",
                "sufficient to derive uniform rank or bad-rank budget support lemmas",
                "compatible with MeasureTheory probability-measure assumptions",
            ],
            "forbidden_shortcuts": [
                "do not define Exchangeable as True",
                "do not add axiom/sorry/admit/unsafe",
                "do not assume the split_conformal_coverage target theorem",
            ],
        }
    if normalized == "orderstat":
        return {
            "semantic_intent": (
                "finite order statistic / conformal quantile of calibration scores "
                "at the requested finite-sample rank"
            ),
            "lean_target_shape": (
                "function from finite indexed real scores and a Nat rank to a real "
                "threshold"
            ),
            "required_properties": [
                "monotone containment of good-rank events",
                "rank index matches the conformal ceiling expression",
                "preserves duplicate score multiplicities and reviewed tie policy",
                "compatible with finite `Fin (n + 1)` score families",
            ],
            "forbidden_shortcuts": [
                "do not define orderStat as a constant unrelated to scores",
                "do not use Finset.image/set sorting that collapses duplicate scores",
                "do not add axiom/sorry/admit/unsafe",
                "do not restate coverage as an order-statistic property",
            ],
        }
    return {
        "semantic_intent": (
            "review or synthesize the exact Lean semantics needed to replace the "
            f"`{placeholder}` placeholder"
        ),
        "lean_target_shape": "minimal reviewed Lean declaration matching the source theorem",
        "required_properties": [
            "matches the source theorem statement",
            "supports downstream local Lean/AXLE verification",
        ],
        "forbidden_shortcuts": [
            "do not define the placeholder as True",
            "do not add axiom/sorry/admit/unsafe",
            "do not assume the target theorem",
        ],
    }


def _learning_row_from_lookup(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": LOOKUP_ROW_ARTIFACT_KIND,
        "learning_task": LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "work_order_id": str(row.get("source_work_order_id", "") or ""),
        "lookup_id": str(row.get("lookup_id", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "replacement_strategy": str(row.get("replacement_strategy", "") or ""),
        "lookup_status": str(row.get("lookup_status", "") or ""),
        "search_targets": list(row.get("search_terms", []) or []),
        "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
        "candidate_source_declarations": list(
            row.get("candidate_source_declarations", []) or []
        ),
        "candidate_source_references": list(
            row.get("candidate_source_references", []) or []
        ),
        "candidate_registered_obligation_ids": list(
            row.get("candidate_registered_obligation_ids", []) or []
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
            row.get("kernel_verified_source_theorem_semantic_support_obligation_ids", [])
            or []
        ),
        "kernel_verified_source_theorem_semantic_definition_ids": [],
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        **_exact_semantic_definition_context(row),
        "semantic_closure_status": str(row.get("semantic_closure_status", "") or ""),
        "placeholder_definition_status": str(
            row.get("placeholder_definition_status", "") or ""
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_semantic_support_only": True,
        "input_summary": {
            "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_SOURCE_LOOKUP",
            "work_order_id": str(row.get("source_work_order_id", "") or ""),
            "lookup_id": str(row.get("lookup_id", "") or ""),
            "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
            "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
            "lookup_status": str(row.get("lookup_status", "") or ""),
            "search_targets": list(row.get("search_terms", []) or []),
            "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
            "candidate_source_declarations": list(
                row.get("candidate_source_declarations", []) or []
            ),
            "candidate_source_references": list(
                row.get("candidate_source_references", []) or []
            ),
            "candidate_registered_obligation_ids": list(
                row.get("candidate_registered_obligation_ids", []) or []
            ),
            "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
                row.get(
                    "kernel_verified_source_theorem_semantic_support_obligation_ids",
                    [],
                )
                or []
            ),
            "kernel_verified_source_theorem_semantic_definition_ids": [],
            "source_semantic_alignment_review_required": bool(
                row.get("source_semantic_alignment_review_required", False)
            ),
            "source_theorem_target_identity_status": str(
                row.get("source_theorem_target_identity_status", "") or ""
            ),
            "source_theorem_target_provenance": dict(
                row.get("source_theorem_target_provenance", {}) or {}
            ),
            "semantic_alignment_constraints": list(
                row.get("semantic_alignment_constraints", []) or []
            ),
            "semantic_alignment_blockers": list(
                row.get("semantic_alignment_blockers", []) or []
            ),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_artifact_path": str(
                row.get("candidate_artifact_path", "") or ""
            ),
            "local_definition_lean_compiled": bool(
                row.get("local_definition_lean_compiled", False)
            ),
            "semantic_definition_typecheck_evidence_status": str(
                row.get("semantic_definition_typecheck_evidence_status", "") or ""
            ),
            **_exact_semantic_definition_context(row),
            "semantic_closure_status": str(
                row.get("semantic_closure_status", "") or ""
            ),
            "placeholder_definition_status": str(
                row.get("placeholder_definition_status", "") or ""
            ),
            "source_theorem_ready_for_exact_proof_body": False,
            "source_theorem_semantic_support_only": True,
        },
        "target_behavior": (
            "Use source lookup hits as candidate locations for exact semantic "
            "definition review/import. Do not count hits as proof evidence."
        ),
        "acceptance_gate": str(row.get("acceptance_gate", "") or ""),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _learning_row_from_definition_closure_work_order(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": DEFINITION_CLOSURE_WORK_ORDER_ARTIFACT_KIND,
        "learning_task": DEFINITION_CLOSURE_LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "work_order_id": str(row.get("work_order_id", "") or ""),
        "source_lookup_id": str(row.get("source_lookup_id", "") or ""),
        "source_exact_semantic_definition_work_order_id": str(
            row.get("source_exact_semantic_definition_work_order_id", "") or ""
        ),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "lookup_status": str(row.get("lookup_status", "") or ""),
        "next_step_kind": str(row.get("next_step_kind", "") or ""),
        "replacement_strategy": str(row.get("replacement_strategy", "") or ""),
        "candidate_source_declarations": list(
            row.get("candidate_source_declarations", []) or []
        ),
        "candidate_source_references": list(
            row.get("candidate_source_references", []) or []
        ),
        "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
        "candidate_registered_obligation_ids": list(
            row.get("candidate_registered_obligation_ids", []) or []
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
            row.get(
                "kernel_verified_source_theorem_semantic_support_obligation_ids",
                [],
            )
            or []
        ),
        "kernel_verified_source_theorem_semantic_definition_ids": [],
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        **_exact_semantic_definition_context(row),
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_semantic_support_only": True,
        "input_summary": {
            "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_CLOSURE_WORK_ORDER",
            "work_order_id": str(row.get("work_order_id", "") or ""),
            "source_lookup_id": str(row.get("source_lookup_id", "") or ""),
            "source_exact_semantic_definition_work_order_id": str(
                row.get("source_exact_semantic_definition_work_order_id", "") or ""
            ),
            "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
            "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
            "lookup_status": str(row.get("lookup_status", "") or ""),
            "next_step_kind": str(row.get("next_step_kind", "") or ""),
            "candidate_source_declarations": list(
                row.get("candidate_source_declarations", []) or []
            ),
            "candidate_source_references": list(
                row.get("candidate_source_references", []) or []
            ),
            "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
            "source_semantic_alignment_review_required": bool(
                row.get("source_semantic_alignment_review_required", False)
            ),
            "source_theorem_target_identity_status": str(
                row.get("source_theorem_target_identity_status", "") or ""
            ),
            "source_theorem_target_provenance": dict(
                row.get("source_theorem_target_provenance", {}) or {}
            ),
            "semantic_alignment_constraints": list(
                row.get("semantic_alignment_constraints", []) or []
            ),
            "semantic_alignment_blockers": list(
                row.get("semantic_alignment_blockers", []) or []
            ),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_artifact_path": str(
                row.get("candidate_artifact_path", "") or ""
            ),
            "local_definition_lean_compiled": bool(
                row.get("local_definition_lean_compiled", False)
            ),
            "semantic_definition_typecheck_evidence_status": str(
                row.get("semantic_definition_typecheck_evidence_status", "") or ""
            ),
            **_exact_semantic_definition_context(row),
        },
        "target_behavior": str(row.get("target_behavior", "") or ""),
        "acceptance_gate": str(row.get("acceptance_gate", "") or ""),
        "proof_evidence_status": DEFINITION_CLOSURE_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _learning_row_from_definition_closure_review_packet(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": DEFINITION_CLOSURE_REVIEW_PACKET_ARTIFACT_KIND,
        "learning_task": DEFINITION_CLOSURE_REVIEW_LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "review_packet_id": str(row.get("review_packet_id", "") or ""),
        "work_order_id": str(row.get("source_definition_closure_work_order_id", "") or ""),
        "source_lookup_id": str(row.get("source_lookup_id", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "lookup_status": str(row.get("lookup_status", "") or ""),
        "next_step_kind": str(row.get("next_step_kind", "") or ""),
        "definition_candidate_status": str(
            row.get("definition_candidate_status", "") or ""
        ),
        "definition_contract": dict(row.get("definition_contract", {}) or {}),
        "candidate_source_declarations": list(
            row.get("candidate_source_declarations", []) or []
        ),
        "candidate_source_references": list(
            row.get("candidate_source_references", []) or []
        ),
        "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
        "candidate_registered_obligation_ids": list(
            row.get("candidate_registered_obligation_ids", []) or []
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
            row.get(
                "kernel_verified_source_theorem_semantic_support_obligation_ids",
                [],
            )
            or []
        ),
        "required_next_checks": list(row.get("required_next_checks", []) or []),
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        **_exact_semantic_definition_context(row),
        "input_summary": {
            "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_CLOSURE_REVIEW_PACKET",
            "review_packet_id": str(row.get("review_packet_id", "") or ""),
            "work_order_id": str(
                row.get("source_definition_closure_work_order_id", "") or ""
            ),
            "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
            "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
            "lookup_status": str(row.get("lookup_status", "") or ""),
            "next_step_kind": str(row.get("next_step_kind", "") or ""),
            "definition_candidate_status": str(
                row.get("definition_candidate_status", "") or ""
            ),
            "definition_contract": dict(row.get("definition_contract", {}) or {}),
            "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
            "required_next_checks": list(row.get("required_next_checks", []) or []),
            "source_semantic_alignment_review_required": bool(
                row.get("source_semantic_alignment_review_required", False)
            ),
            "source_theorem_target_identity_status": str(
                row.get("source_theorem_target_identity_status", "") or ""
            ),
            "source_theorem_target_provenance": dict(
                row.get("source_theorem_target_provenance", {}) or {}
            ),
            "semantic_alignment_constraints": list(
                row.get("semantic_alignment_constraints", []) or []
            ),
            "semantic_alignment_blockers": list(
                row.get("semantic_alignment_blockers", []) or []
            ),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_artifact_path": str(
                row.get("candidate_artifact_path", "") or ""
            ),
            "local_definition_lean_compiled": bool(
                row.get("local_definition_lean_compiled", False)
            ),
            "semantic_definition_typecheck_evidence_status": str(
                row.get("semantic_definition_typecheck_evidence_status", "") or ""
            ),
            **_exact_semantic_definition_context(row),
        },
        "target_behavior": str(row.get("target_behavior", "") or ""),
        "acceptance_gate": str(row.get("acceptance_gate", "") or ""),
        "proof_evidence_status": DEFINITION_CLOSURE_REVIEW_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _definition_closure_review_result(
    row: Mapping[str, Any],
    *,
    candidate_artifact_path: Path | None,
    candidate_text: str,
) -> dict[str, Any]:
    placeholder = str(row.get("placeholder_symbol", "") or "")
    forbidden_matches = _forbidden_placeholder_definition_matches(
        placeholder=placeholder,
        candidate_text=candidate_text,
    )
    candidate_present = bool(candidate_artifact_path and candidate_text)
    raw_semantic_definition_risks = _semantic_definition_risks(
        placeholder=placeholder,
        candidate_text=candidate_text,
    )
    semantic_definition_risks: list[str] = []
    if forbidden_matches:
        review_status = "FORBIDDEN_PLACEHOLDER_DEFINITION_FOUND"
        ready_for_definition_lean_check = False
    elif not candidate_present:
        review_status = "NO_CANDIDATE_ARTIFACT_PROVIDED"
        ready_for_definition_lean_check = False
    elif raw_semantic_definition_risks:
        semantic_definition_risks = raw_semantic_definition_risks
        review_status = "CANDIDATE_DEFINITION_SEMANTIC_RISK_FOUND"
        ready_for_definition_lean_check = False
    else:
        review_status = "CANDIDATE_DEFINITION_REQUIRES_LEAN_REVIEW"
        ready_for_definition_lean_check = True
    contract = dict(row.get("definition_contract", {}) or {})
    required_next_checks = list(row.get("required_next_checks", []) or [])
    recommended_repair_tasks = _definition_closure_review_repair_tasks(
        placeholder=placeholder,
        review_status=review_status,
        contract=contract,
        required_next_checks=required_next_checks,
    )
    result_id = (
        "source_theorem_exact_semantic_definition_closure_review_result:"
        + stable_hash(
            [
                row.get("review_packet_id", ""),
                row.get("source_definition_closure_work_order_id", ""),
                row.get("target_theorem_name", ""),
                placeholder,
                review_status,
                forbidden_matches,
                semantic_definition_risks,
                str(candidate_artifact_path or ""),
            ]
        )[:20]
    )
    return {
        "schema_version": 1,
        "artifact_kind": DEFINITION_CLOSURE_REVIEW_RESULT_ARTIFACT_KIND,
        "review_result_id": result_id,
        "source_review_packet_id": str(row.get("review_packet_id", "") or ""),
        "source_definition_closure_work_order_id": str(
            row.get("source_definition_closure_work_order_id", "") or ""
        ),
        "source_lookup_id": str(row.get("source_lookup_id", "") or ""),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "placeholder_symbol": placeholder,
        "lookup_status": str(row.get("lookup_status", "") or ""),
        "next_step_kind": str(row.get("next_step_kind", "") or ""),
        "definition_candidate_status": str(
            row.get("definition_candidate_status", "") or ""
        ),
        "definition_contract": contract,
        "candidate_artifact_path": str(candidate_artifact_path or ""),
        "candidate_artifact_present": candidate_present,
        "review_status": review_status,
        "forbidden_placeholder_detected": bool(forbidden_matches),
        "forbidden_placeholder_matches": forbidden_matches,
        "semantic_definition_risk_detected": bool(semantic_definition_risks),
        "semantic_definition_risks": semantic_definition_risks,
        "ready_for_definition_lean_check": ready_for_definition_lean_check,
        "candidate_source_declarations": list(
            row.get("candidate_source_declarations", []) or []
        ),
        "candidate_source_references": list(
            row.get("candidate_source_references", []) or []
        ),
        "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
        "candidate_registered_obligation_ids": list(
            row.get("candidate_registered_obligation_ids", []) or []
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
            row.get(
                "kernel_verified_source_theorem_semantic_support_obligation_ids",
                [],
            )
            or []
        ),
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            dict.fromkeys(
                [
                    *list(row.get("semantic_alignment_blockers", []) or []),
                    *semantic_definition_risks,
                ]
            )
        ),
        **_exact_semantic_definition_context(row),
        "required_next_checks": required_next_checks,
        "recommended_repair_tasks": recommended_repair_tasks,
        "target_behavior": (
            "Repair the candidate artifact's exact semantic definition before "
            "rerunning source theorem proof-body execution."
        ),
        "acceptance_gate": (
            "No forbidden placeholder definition remains, then local Lean/AXLE "
            "checks the repaired exact source theorem candidate. This result row "
            "is not proof evidence."
        ),
        "proof_evidence_status": DEFINITION_CLOSURE_REVIEW_RESULT_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _learning_row_from_definition_closure_review_result(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": DEFINITION_CLOSURE_REVIEW_RESULT_ARTIFACT_KIND,
        "learning_task": DEFINITION_CLOSURE_REVIEW_RESULT_LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "review_result_id": str(row.get("review_result_id", "") or ""),
        "work_order_id": str(row.get("source_definition_closure_work_order_id", "") or ""),
        "source_review_packet_id": str(row.get("source_review_packet_id", "") or ""),
        "source_lookup_id": str(row.get("source_lookup_id", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "lookup_status": str(row.get("lookup_status", "") or ""),
        "next_step_kind": str(row.get("next_step_kind", "") or ""),
        "definition_candidate_status": str(
            row.get("definition_candidate_status", "") or ""
        ),
        "definition_contract": dict(row.get("definition_contract", {}) or {}),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "review_status": str(row.get("review_status", "") or ""),
        "forbidden_placeholder_detected": bool(
            row.get("forbidden_placeholder_detected", False)
        ),
        "forbidden_placeholder_matches": list(
            row.get("forbidden_placeholder_matches", []) or []
        ),
        "semantic_definition_risk_detected": bool(
            row.get("semantic_definition_risk_detected", False)
        ),
        "semantic_definition_risks": list(
            row.get("semantic_definition_risks", []) or []
        ),
        "ready_for_definition_lean_check": bool(
            row.get("ready_for_definition_lean_check", False)
        ),
        "candidate_source_declarations": list(
            row.get("candidate_source_declarations", []) or []
        ),
        "candidate_source_references": list(
            row.get("candidate_source_references", []) or []
        ),
        "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
        "required_next_checks": list(row.get("required_next_checks", []) or []),
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "recommended_repair_tasks": list(
            row.get("recommended_repair_tasks", []) or []
        ),
        **_exact_semantic_definition_context(row),
        "input_summary": {
            "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_CLOSURE_REVIEW_RESULT",
            "review_result_id": str(row.get("review_result_id", "") or ""),
            "work_order_id": str(
                row.get("source_definition_closure_work_order_id", "") or ""
            ),
            "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
            "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
            "review_status": str(row.get("review_status", "") or ""),
            "forbidden_placeholder_detected": bool(
                row.get("forbidden_placeholder_detected", False)
            ),
            "forbidden_placeholder_matches": list(
                row.get("forbidden_placeholder_matches", []) or []
            ),
            "semantic_definition_risk_detected": bool(
                row.get("semantic_definition_risk_detected", False)
            ),
            "semantic_definition_risks": list(
                row.get("semantic_definition_risks", []) or []
            ),
            "ready_for_definition_lean_check": bool(
                row.get("ready_for_definition_lean_check", False)
            ),
            "definition_contract": dict(row.get("definition_contract", {}) or {}),
            "required_next_checks": list(row.get("required_next_checks", []) or []),
            "source_semantic_alignment_review_required": bool(
                row.get("source_semantic_alignment_review_required", False)
            ),
            "source_theorem_target_identity_status": str(
                row.get("source_theorem_target_identity_status", "") or ""
            ),
            "source_theorem_target_provenance": dict(
                row.get("source_theorem_target_provenance", {}) or {}
            ),
            "semantic_alignment_constraints": list(
                row.get("semantic_alignment_constraints", []) or []
            ),
            "semantic_alignment_blockers": list(
                row.get("semantic_alignment_blockers", []) or []
            ),
            "recommended_repair_tasks": list(
                row.get("recommended_repair_tasks", []) or []
            ),
            **_exact_semantic_definition_context(row),
        },
        "target_behavior": str(row.get("target_behavior", "") or ""),
        "acceptance_gate": str(row.get("acceptance_gate", "") or ""),
        "proof_evidence_status": DEFINITION_CLOSURE_REVIEW_RESULT_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _definition_candidate_synthesis_row(
    row: Mapping[str, Any],
    *,
    candidate_artifact_path: Path,
    replacement: str,
    replacement_applied: bool,
    replacement_error: str,
    review_mode: str,
) -> dict[str, Any]:
    placeholder = str(row.get("placeholder_symbol", "") or "")
    synthesis_id = (
        "source_theorem_exact_semantic_definition_candidate_synthesis:"
        + stable_hash(
            [
                row.get("review_result_id", ""),
                row.get("source_review_packet_id", ""),
                row.get("target_theorem_name", ""),
                placeholder,
                str(candidate_artifact_path),
                replacement,
                replacement_applied,
                replacement_error,
            ]
        )[:20]
    )
    semantic_review_note = (
        _draft_definition_semantic_risk(placeholder)
        if replacement_applied or review_mode == "synthesize_draft_definition"
        else ""
    )
    replacement_semantic_risks = (
        _semantic_definition_risks(
            placeholder=placeholder,
            candidate_text=replacement,
        )
        if replacement_applied and replacement
        else []
    )
    inherited_semantic_definition_risks = [
        str(value)
        for value in row.get("semantic_definition_risks", []) or []
        if str(value).strip()
    ]
    semantic_definition_risks = (
        list(dict.fromkeys(replacement_semantic_risks))
        if replacement_applied
        else inherited_semantic_definition_risks
    )
    inherited_constraints = [
        str(value)
        for value in row.get("semantic_alignment_constraints", []) or []
        if str(value).strip()
    ]
    inherited_blockers = [
        str(value)
        for value in row.get("semantic_alignment_blockers", []) or []
        if str(value).strip()
    ]
    if replacement_applied:
        inherited_constraints = [
            value
            for value in inherited_constraints
            if not _is_stale_replaced_semantic_definition_risk(value)
        ]
        inherited_blockers = [
            value
            for value in inherited_blockers
            if not _is_stale_replaced_semantic_definition_risk(value)
        ]
    synthesized_review_note = (
        [f"unreviewed synthesized definition review note: {semantic_review_note}"]
        if semantic_review_note
        else []
    )
    semantic_alignment_constraints = list(
        dict.fromkeys([*inherited_constraints, *synthesized_review_note])
    )
    semantic_alignment_blockers = list(
        dict.fromkeys([*inherited_blockers, *semantic_definition_risks])
    )
    if review_mode == "lean_review_existing_candidate":
        recommended_next_action = (
            "review existing candidate definitions with local Lean/AXLE and keep "
            "semantic blockers open until reviewed/imported source definitions "
            "close them"
        )
    elif review_mode == "semantic_review_blocked_existing_candidate":
        recommended_next_action = (
            "replace or import reviewed exact semantic definitions before local "
            "proof-body search; do not repair this by tactic search"
        )
    elif replacement_applied:
        recommended_next_action = (
            "run local Lean/AXLE on synthesized candidate and inspect the next "
            "proof-body blocker"
        )
    else:
        recommended_next_action = "repair the candidate definition synthesis inputs"
    return {
        "schema_version": 1,
        "artifact_kind": (
            "RuntimeSourceTheoremExactSemanticDefinitionCandidateSynthesisResult"
        ),
        "synthesis_result_id": synthesis_id,
        "source_review_result_id": str(row.get("review_result_id", "") or ""),
        "source_review_packet_id": str(row.get("source_review_packet_id", "") or ""),
        "source_definition_closure_work_order_id": str(row.get("work_order_id", "") or ""),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "placeholder_symbol": placeholder,
        "candidate_artifact_path": str(candidate_artifact_path),
        "replacement_applied": bool(replacement_applied),
        "replacement_error": replacement_error,
        "replacement_definition": replacement,
        "definition_candidate_review_mode": review_mode,
        "definition_contract": dict(row.get("definition_contract", {}) or {}),
        "semantic_definition_risk_detected": bool(semantic_definition_risks),
        "semantic_definition_risks": semantic_definition_risks,
        "semantic_risk": (
            "; ".join(semantic_definition_risks)
            if semantic_definition_risks
            else ""
        ),
        "semantic_review_note": semantic_review_note,
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "source_theorem_kernel_evidence_eligible": False,
        "recommended_next_action": recommended_next_action,
        "proof_evidence_status": (
            "DEFINITION_CANDIDATE_SYNTHESIS_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": BOUNDARY,
    }


def _learning_row_from_definition_candidate_synthesis(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": str(row.get("artifact_kind", "") or ""),
        "learning_task": "source_theorem_exact_semantic_definition_candidate_synthesis",
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "synthesis_result_id": str(row.get("synthesis_result_id", "") or ""),
        "work_order_id": str(row.get("source_definition_closure_work_order_id", "") or ""),
        "source_review_result_id": str(row.get("source_review_result_id", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "synthesized_candidate_artifact_path": str(
            row.get("synthesized_candidate_artifact_path", "") or ""
        ),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_lean_project_hint": str(
            row.get("candidate_lean_project_hint", "") or ""
        ),
        "replacement_applied": bool(row.get("replacement_applied", False)),
        "replacement_error": str(row.get("replacement_error", "") or ""),
        "definition_candidate_review_mode": str(
            row.get("definition_candidate_review_mode", "") or ""
        ),
        "semantic_definition_risk_detected": bool(
            row.get("semantic_definition_risk_detected", False)
        ),
        "semantic_definition_risks": list(
            row.get("semantic_definition_risks", []) or []
        ),
        "semantic_risk": str(row.get("semantic_risk", "") or ""),
        "semantic_review_note": str(row.get("semantic_review_note", "") or ""),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", False)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "source_theorem_kernel_evidence_eligible": bool(
            row.get("source_theorem_kernel_evidence_eligible", False)
        ),
        "forbidden_placeholder_detected_after": bool(
            row.get("forbidden_placeholder_detected_after", False)
        ),
        "forbidden_placeholder_matches_after": list(
            row.get("forbidden_placeholder_matches_after", []) or []
        ),
        "local_lean_checked": bool(row.get("local_lean_checked", False)),
        "local_lean_compiled": bool(row.get("local_lean_compiled", False)),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        "candidate_synthesis_status": str(
            row.get("candidate_synthesis_status", "") or ""
        ),
        "input_summary": {
            "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_CANDIDATE_SYNTHESIS",
            "synthesis_result_id": str(row.get("synthesis_result_id", "") or ""),
            "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
            "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
            "synthesized_candidate_artifact_path": str(
                row.get("synthesized_candidate_artifact_path", "") or ""
            ),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_lean_project_hint": str(
                row.get("candidate_lean_project_hint", "") or ""
            ),
            "replacement_applied": bool(row.get("replacement_applied", False)),
            "definition_candidate_review_mode": str(
                row.get("definition_candidate_review_mode", "") or ""
            ),
            "semantic_definition_risk_detected": bool(
                row.get("semantic_definition_risk_detected", False)
            ),
            "semantic_definition_risks": list(
                row.get("semantic_definition_risks", []) or []
            ),
            "semantic_risk": str(row.get("semantic_risk", "") or ""),
            "semantic_review_note": str(row.get("semantic_review_note", "") or ""),
            "semantic_alignment_constraints": list(
                row.get("semantic_alignment_constraints", []) or []
            ),
            "semantic_alignment_blockers": list(
                row.get("semantic_alignment_blockers", []) or []
            ),
            "source_semantic_alignment_review_required": bool(
                row.get("source_semantic_alignment_review_required", False)
            ),
            "source_theorem_target_identity_status": str(
                row.get("source_theorem_target_identity_status", "") or ""
            ),
            "source_theorem_target_provenance": dict(
                row.get("source_theorem_target_provenance", {}) or {}
            ),
            "source_theorem_kernel_evidence_eligible": bool(
                row.get("source_theorem_kernel_evidence_eligible", False)
            ),
            "forbidden_placeholder_detected_after": bool(
                row.get("forbidden_placeholder_detected_after", False)
            ),
            "local_lean_checked": bool(row.get("local_lean_checked", False)),
            "local_lean_compiled": bool(row.get("local_lean_compiled", False)),
            "local_definition_lean_checked": bool(
                row.get("local_definition_lean_checked", False)
            ),
            "local_definition_lean_compiled": bool(
                row.get("local_definition_lean_compiled", False)
            ),
            "semantic_definition_typecheck_evidence_status": str(
                row.get("semantic_definition_typecheck_evidence_status", "") or ""
            ),
            "candidate_synthesis_status": str(
                row.get("candidate_synthesis_status", "") or ""
            ),
            "local_lean_diagnostics": list(row.get("local_lean_diagnostics", []) or [])[:8],
        },
        "target_behavior": (
            "Use the candidate artifact only as a diagnostic/review artifact. "
            "Source theorem proof still requires local Lean/AXLE verification of "
            "the intended theorem with reviewed semantics."
        ),
        "acceptance_gate": (
            "No forbidden placeholder definitions remain and local Lean/AXLE reports "
            "a non-placeholder next blocker or verifies the intended theorem."
        ),
        "proof_evidence_status": (
            "DEFINITION_CANDIDATE_SYNTHESIS_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": BOUNDARY,
    }


def _learning_row_from_semantic_definition_repair_queue(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": str(row.get("artifact_kind", "") or ""),
        "learning_task": SEMANTIC_DEFINITION_REPAIR_LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "repair_queue_id": str(row.get("repair_queue_id", "") or ""),
        "source_synthesis_result_id": str(
            row.get("source_synthesis_result_id", "") or ""
        ),
        "work_order_id": str(
            row.get("source_definition_closure_work_order_id", "") or ""
        ),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "synthesized_candidate_artifact_path": str(
            row.get("synthesized_candidate_artifact_path", "") or ""
        ),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_lean_project_hint": str(
            row.get("candidate_lean_project_hint", "") or ""
        ),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        "source_theorem_exact_semantic_definition_typechecked_candidate": dict(
            row.get(
                "source_theorem_exact_semantic_definition_typechecked_candidate",
                {},
            )
            or {}
        ),
        "definition_candidate_review_mode": str(
            row.get("definition_candidate_review_mode", "") or ""
        ),
        "semantic_definition_risk_detected": bool(
            row.get("semantic_definition_risk_detected", False)
        ),
        "semantic_definition_risks": list(
            row.get("semantic_definition_risks", []) or []
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "source_semantic_alignment_review_required": bool(
            row.get("source_semantic_alignment_review_required", True)
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
        ),
        "source_theorem_kernel_evidence_eligible": bool(
            row.get("source_theorem_kernel_evidence_eligible", False)
        ),
        "action_type": str(row.get("action_type", "") or ""),
        "repair_status": str(row.get("repair_status", "") or ""),
        "recommended_next_action": str(row.get("recommended_next_action", "") or ""),
        "input_summary": {
            "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_REPAIR_QUEUE",
            "repair_queue_id": str(row.get("repair_queue_id", "") or ""),
            "source_synthesis_result_id": str(
                row.get("source_synthesis_result_id", "") or ""
            ),
            "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
            "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
            "definition_candidate_review_mode": str(
                row.get("definition_candidate_review_mode", "") or ""
            ),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
            "synthesized_candidate_artifact_path": str(
                row.get("synthesized_candidate_artifact_path", "") or ""
            ),
            "local_definition_lean_checked": bool(
                row.get("local_definition_lean_checked", False)
            ),
            "local_definition_lean_compiled": bool(
                row.get("local_definition_lean_compiled", False)
            ),
            "semantic_definition_typecheck_evidence_status": str(
                row.get("semantic_definition_typecheck_evidence_status", "") or ""
            ),
            "source_theorem_exact_semantic_definition_typechecked_candidate": dict(
                row.get(
                    "source_theorem_exact_semantic_definition_typechecked_candidate",
                    {},
                )
                or {}
            ),
            "semantic_definition_risk_detected": bool(
                row.get("semantic_definition_risk_detected", False)
            ),
            "semantic_definition_risks": list(
                row.get("semantic_definition_risks", []) or []
            ),
            "semantic_alignment_blockers": list(
                row.get("semantic_alignment_blockers", []) or []
            ),
            "source_theorem_kernel_evidence_eligible": bool(
                row.get("source_theorem_kernel_evidence_eligible", False)
            ),
            "repair_status": str(row.get("repair_status", "") or ""),
        },
        "target_behavior": (
            "Repair the exact semantic definition before any source-theorem proof "
            "body search. This is a routing/repair signal, not proof evidence."
        ),
        "acceptance_gate": str(row.get("acceptance_gate", "") or ""),
        "proof_evidence_status": (
            "SEMANTIC_DEFINITION_REPAIR_QUEUE_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_boundary": BOUNDARY,
    }


def _draft_definition_for_placeholder(placeholder: str) -> str:
    normalized = placeholder.strip().lower()
    if normalized == "exchangeable":
        return (
            "def Exchangeable {Ω : Type _} [MeasurableSpace Ω] {ι : Type _} [Fintype ι]\n"
            "    (P : MeasureTheory.Measure Ω) (s : ι → Ω → ℝ) : Prop :=\n"
            "  ∀ σ : Equiv.Perm ι,\n"
            "    MeasureTheory.Measure.map (fun ω : Ω => fun i : ι => s (σ i) ω) P =\n"
            "      MeasureTheory.Measure.map (fun ω : Ω => fun i : ι => s i ω) P"
        )
    if normalized == "orderstat":
        return (
            "def orderStat {Ω : Type _} {m : ℕ}\n"
            "    (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ :=\n"
            "  ((List.ofFn (fun i : Fin (m + 1) => s i ω)).mergeSort (· ≤ ·)).getD k 0"
        )
    return ""


def _draft_definition_semantic_risk(placeholder: str) -> str:
    normalized = placeholder.strip().lower()
    if normalized == "exchangeable":
        return (
            "draft finite permutation-invariant joint-law exchangeability still "
            "requires source review and downstream local Lean/AXLE verification"
        )
    if normalized == "orderstat":
        return (
            "draft sorted finite order statistic uses a duplicate-preserving finite "
            "score list and rank k, but still needs source review for indexing "
            "convention, tie behavior, and conformal quantile rank; "
            "the source theorem upper coverage bound is not eligible for proof-body search "
            "until ties are handled by a reviewed tie policy/no-tie assumption or the "
            "theorem is revised"
        )
    return "draft definition requires semantic review"


def _definition_only_candidate_text(candidate_text: str) -> str:
    lines = candidate_text.splitlines()
    first_theorem_index = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"^\s*(theorem|lemma)\s+[A-Za-z_][A-Za-z0-9_'.]*\b", line)
        ),
        -1,
    )
    if first_theorem_index < 0:
        return candidate_text if candidate_text.endswith("\n") else candidate_text + "\n"
    prefix = lines[:first_theorem_index]
    namespace_stack: list[str] = []
    section_count = 0
    for line in prefix:
        stripped = line.strip()
        namespace_match = re.match(r"^namespace\s+([A-Za-z_][A-Za-z0-9_'.]*)\s*$", stripped)
        if namespace_match:
            namespace_stack.append(namespace_match.group(1))
            continue
        if re.match(r"^(noncomputable\s+)?section\b", stripped):
            section_count += 1
            continue
        if stripped == "end" and section_count:
            section_count -= 1
            continue
        end_match = re.match(r"^end\s+([A-Za-z_][A-Za-z0-9_'.]*)\s*$", stripped)
        if end_match and namespace_stack and namespace_stack[-1] == end_match.group(1):
            namespace_stack.pop()
    closing_lines = ["end" for _ in range(section_count)]
    closing_lines.extend(f"end {name}" for name in reversed(namespace_stack))
    definition_only_lines = [
        *prefix,
        "",
        "/- Definition-only typecheck artifact; not source theorem proof evidence. -/",
        *closing_lines,
    ]
    return "\n".join(definition_only_lines) + "\n"


def _replace_lean_definition_block(
    *,
    candidate_text: str,
    symbol: str,
    replacement: str,
) -> str:
    block = _lean_definition_block(candidate_text=candidate_text, symbol=symbol)
    if block is None:
        raise ValueError(f"definition block not found for {symbol}")
    start_line, block_text = block
    lines = candidate_text.splitlines()
    start_index = start_line - 1
    block_line_count = len(block_text.splitlines())
    end_index = start_index + block_line_count
    replacement_lines = replacement.splitlines()
    new_lines = [*lines[:start_index], *replacement_lines, *lines[end_index:]]
    return "\n".join(new_lines) + ("\n" if candidate_text.endswith("\n") else "")


def _candidate_synthesis_status(
    row: Mapping[str, Any],
    *,
    forbidden_after: list[dict[str, Any]],
    local_lean: bool,
    local_lean_compiled: bool,
    diagnostics: tuple[str, ...],
) -> str:
    review_mode = str(row.get("definition_candidate_review_mode", "") or "")
    if review_mode == "lean_review_existing_candidate":
        if forbidden_after:
            return "DEFINITION_REVIEW_FORBIDDEN_PLACEHOLDER_REMAINS"
        if local_lean and local_lean_compiled:
            return "DEFINITION_REVIEW_LOCAL_LEAN_COMPILED"
        if local_lean and any("unsolved goals" in value for value in diagnostics):
            return "DEFINITION_REVIEW_LOCAL_LEAN_REACHED_PROOF_BODY"
        if local_lean:
            return "DEFINITION_REVIEW_LOCAL_LEAN_FAILED"
        return "DEFINITION_REVIEW_CANDIDATE_WRITTEN"
    if review_mode == "semantic_review_blocked_existing_candidate":
        return "DEFINITION_REVIEW_SEMANTIC_RISK_BLOCKED"
    if row.get("replacement_error"):
        return "DEFINITION_SYNTHESIS_REPLACEMENT_FAILED"
    if forbidden_after:
        return "DEFINITION_SYNTHESIS_FORBIDDEN_PLACEHOLDER_REMAINS"
    if str(row.get("semantic_risk", "") or "").strip():
        return "DEFINITION_SYNTHESIS_SEMANTIC_REVIEW_REQUIRED"
    if local_lean and local_lean_compiled:
        return "DEFINITION_SYNTHESIS_LOCAL_LEAN_COMPILED"
    if local_lean and any("unsolved goals" in value for value in diagnostics):
        return "DEFINITION_SYNTHESIS_LOCAL_LEAN_REACHED_PROOF_BODY"
    if local_lean:
        return "DEFINITION_SYNTHESIS_LOCAL_LEAN_FAILED"
    return "DEFINITION_SYNTHESIS_CANDIDATE_WRITTEN"


def _lean_command(lean_project: Path | None) -> tuple[str, ...]:
    if lean_project is not None and shutil.which("lake") is not None:
        return ("lake", "env", "lean")
    if shutil.which("lean") is not None:
        return ("lean",)
    return ()


def _run_local_lean(
    lean_file: Path,
    *,
    lean_command: tuple[str, ...],
    lean_project: Path | None,
    timeout_s: int,
) -> tuple[bool, int, tuple[str, ...]]:
    if not lean_command:
        return False, -1, ("lean executable not found",)
    try:
        proc = subprocess.run(
            [*lean_command, str(lean_file.resolve())],
            cwd=str(lean_project) if lean_project is not None else None,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        return False, -1, (f"local Lean timed out after {timeout_s}s: {exc}",)
    except Exception as exc:
        return False, -1, (f"{type(exc).__name__}: {exc}",)
    diagnostics = tuple(
        line
        for line in (proc.stdout + "\n" + proc.stderr).splitlines()
        if line.strip()
    )
    return proc.returncode == 0, int(proc.returncode), diagnostics


def _forbidden_placeholder_definition_matches(
    *,
    placeholder: str,
    candidate_text: str,
) -> list[dict[str, Any]]:
    if not placeholder or not candidate_text:
        return []
    symbol = placeholder.strip()
    block = _lean_definition_block(candidate_text=candidate_text, symbol=symbol)
    if block is None:
        return []
    start_line, block_text = block
    checks: list[tuple[str, str]] = [
        ("defined_as_true", r":=\s*True\b"),
        ("defined_as_zero", r":=\s*0\b"),
    ]
    matches: list[dict[str, Any]] = []
    for kind, pattern in checks:
        for match in re.finditer(pattern, block_text):
            line_no = start_line + block_text.count("\n", 0, match.start())
            line_start = block_text.rfind("\n", 0, match.start()) + 1
            line_end = block_text.find("\n", match.end())
            if line_end == -1:
                line_end = len(block_text)
            snippet = block_text[line_start:line_end].strip()
            matches.append(
                {
                    "kind": kind,
                    "line": line_no,
                    "snippet": snippet[:240],
                }
            )
    return matches[:8]


def _semantic_definition_risks(
    *,
    placeholder: str,
    candidate_text: str,
) -> list[str]:
    if not placeholder or not candidate_text:
        return []
    block = _lean_definition_block(candidate_text=candidate_text, symbol=placeholder)
    if block is None:
        return []
    _, block_text = block
    normalized = placeholder.strip().lower()
    risks: list[str] = []
    if normalized == "exchangeable":
        if "P.real" in block_text and "Equiv.Perm" not in block_text:
            risks.append(
                "semantic_definition_risk: Exchangeable candidate uses pairwise "
                "score-order probability symmetry rather than finite permutation-"
                "invariant joint-law exchangeability"
            )
        if "Equiv.Perm" not in block_text and "permutation" not in block_text.lower():
            risks.append(
                "semantic_definition_risk: Exchangeable candidate does not expose "
                "a finite permutation/invariance parameter"
            )
    elif normalized == "orderstat":
        body = block_text.split(":=", 1)[1] if ":=" in block_text else block_text
        if ".max'" in body or ".max " in body or ".max\n" in body:
            risks.append(
                "semantic_definition_risk: orderStat candidate is a finite maximum, "
                "not a reviewed rank-k order statistic/conformal quantile"
            )
        if "Finset.univ.image" in body:
            risks.append(
                "semantic_definition_risk: orderStat candidate uses Finset.image, "
                "which collapses duplicate score values and is not faithful to "
                "finite-sample order statistics unless a reviewed no-tie or "
                "multiplicity-preserving tie policy is supplied"
            )
        if not re.search(r"\bk\b", body):
            risks.append(
                "semantic_definition_risk: orderStat candidate body does not use "
                "the requested rank parameter k"
            )
    return list(dict.fromkeys(risks))


def _lean_definition_block(
    *,
    candidate_text: str,
    symbol: str,
) -> tuple[int, str] | None:
    lines = candidate_text.splitlines()
    start_index = -1
    start_re = re.compile(rf"^\s*def\s+{re.escape(symbol)}\b")
    next_decl_re = re.compile(
        r"^\s*(def|theorem|lemma|structure|class|abbrev)\s+[A-Za-z_][A-Za-z0-9_'.]*\b"
    )
    for index, line in enumerate(lines):
        if start_re.search(line):
            start_index = index
            break
    if start_index < 0:
        return None
    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        if next_decl_re.search(lines[index]):
            end_index = index
            break
    return start_index + 1, "\n".join(lines[start_index:end_index])


def _definition_closure_review_repair_tasks(
    *,
    placeholder: str,
    review_status: str,
    contract: Mapping[str, Any],
    required_next_checks: list[Any],
) -> list[str]:
    tasks = [str(value) for value in required_next_checks if str(value).strip()]
    if review_status == "FORBIDDEN_PLACEHOLDER_DEFINITION_FOUND":
        tasks.insert(
            0,
            f"replace forbidden `{placeholder}` placeholder definition with a reviewed exact Lean definition",
        )
    elif review_status == "NO_CANDIDATE_ARTIFACT_PROVIDED":
        tasks.insert(
            0,
            "provide the exact source theorem candidate artifact for definition review",
        )
    elif review_status == "CANDIDATE_DEFINITION_SEMANTIC_RISK_FOUND":
        tasks.insert(
            0,
            f"replace or import reviewed exact `{placeholder}` semantics; current candidate violates the semantic contract",
        )
    else:
        tasks.insert(
            0,
            f"run local Lean/AXLE after reviewing `{placeholder}` definition semantics",
        )
    forbidden = contract.get("forbidden_shortcuts", [])
    if isinstance(forbidden, list) and forbidden:
        tasks.append("preserve forbidden-shortcut guard: " + "; ".join(map(str, forbidden[:3])))
    return list(dict.fromkeys(tasks))[:8]


def _source_lookup_hits(
    *,
    source_roots: list[Path],
    search_terms: list[str],
    max_hits: int,
    work_order: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if max_hits <= 0:
        return []
    normalized_terms = [
        term.lower()
        for term in search_terms
        if term and len(term.strip()) >= 3
    ]
    if not normalized_terms:
        return []
    hits: list[dict[str, Any]] = []
    for root in source_roots:
        for path in sorted(root.rglob("*.lean")):
            if _is_generated_or_cache_source_path(path, root=root):
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            file_text = "\n".join(lines).lower()
            strict_identifier_start = _is_source_to_bridge_adapter_object_definition_work_order(
                work_order
            )
            file_matched_terms = [
                term
                for term in normalized_terms
                if _source_lookup_term_occurs(
                    file_text,
                    term,
                    strict_identifier_start=strict_identifier_start,
                )
            ]
            for line_no, line in enumerate(lines, start=1):
                lowered = line.lower()
                line_matched_terms = [
                    term
                    for term in normalized_terms
                    if _source_lookup_term_occurs(
                        lowered,
                        term,
                        strict_identifier_start=strict_identifier_start,
                    )
                ]
                term = line_matched_terms[0] if line_matched_terms else ""
                if not term:
                    continue
                if not _source_lookup_hit_is_eligible(
                    line_matched_terms=line_matched_terms,
                    file_matched_terms=file_matched_terms,
                    normalized_terms=normalized_terms,
                    work_order=work_order,
                ):
                    continue
                hits.append(
                    {
                        "path": str(path),
                        "line": line_no,
                        "match_term": term,
                        "matched_terms": line_matched_terms,
                        "file_matched_terms": file_matched_terms,
                        "source_lookup_context_score": _source_lookup_context_score(
                            line_matched_terms=line_matched_terms,
                            file_matched_terms=file_matched_terms,
                            normalized_terms=normalized_terms,
                        ),
                        "snippet": line.strip()[:320],
                        "candidate_kind": (
                            "lean_declaration"
                            if _looks_like_lean_declaration(line)
                            else "lean_source_text_match"
                        ),
                    }
                )
    ranked_hits = [
        {
            **hit,
            "source_lookup_rank": rank,
            "source_lookup_rank_reason": _source_lookup_rank_reason(
                hit=hit,
                normalized_terms=normalized_terms,
            ),
            **_source_lookup_semantic_import_review(
                hit=hit,
                normalized_terms=normalized_terms,
                work_order=work_order,
            ),
        }
        for rank, hit in enumerate(
            sorted(
                hits,
                key=lambda hit: _source_lookup_rank_key(
                    hit=hit,
                    normalized_terms=normalized_terms,
                    work_order=work_order,
                ),
            )[:max_hits],
            start=1,
        )
    ]
    return ranked_hits


def _source_lookup_semantic_import_review(
    *,
    hit: Mapping[str, Any],
    normalized_terms: list[str],
    work_order: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Annotate whether a declaration is plausible as an exact semantic import."""

    candidate_kind = str(hit.get("candidate_kind", "") or "")
    if _is_source_to_bridge_adapter_object_definition_work_order(work_order):
        return {
            "semantic_import_candidate_allowed": False,
            "source_semantic_review_status": (
                "SOURCE_TO_BRIDGE_ADAPTER_OBJECT_REQUIRES_SYNTHESIS"
            ),
            "source_semantic_review_reason": (
                "source-to-bridge adapter objects must be instantiated from exact "
                "source theorem binders; source hits are context only and are not "
                "import candidates"
            ),
        }
    if candidate_kind != "lean_declaration":
        return {
            "semantic_import_candidate_allowed": False,
            "source_semantic_review_status": "SOURCE_REFERENCE_REQUIRES_SYNTHESIS",
            "source_semantic_review_reason": (
                "source text hit is useful context but is not an importable Lean declaration"
            ),
        }
    primary = normalized_terms[0] if normalized_terms else ""
    primary_normalized = _compact_identifier(primary)
    snippet = str(hit.get("snippet", "") or "")
    declaration_name = _lean_declaration_name(snippet)
    if not _source_lookup_declaration_has_exact_or_high_signal_match(
        hit=hit,
        normalized_terms=normalized_terms,
        work_order=work_order,
    ):
        return {
            "semantic_import_candidate_allowed": False,
            "source_semantic_review_status": (
                "SEMANTIC_REVIEW_REQUIRED_WEAK_CONTEXTUAL_DECLARATION_MATCH"
            ),
            "source_semantic_review_reason": (
                "declaration matched only broad contextual terms; keep it as "
                "source/RAG context, but do not treat it as a reviewed exact "
                "semantic-definition import candidate"
            ),
        }
    policy_blocker = exact_semantic_definition_import_policy_blocker(
        primary_normalized,
        snippet=snippet,
        declaration_name=declaration_name,
        require_required_signal=True,
    )
    if policy_blocker:
        return {
            "semantic_import_candidate_allowed": False,
            **policy_blocker,
        }
    return {
        "semantic_import_candidate_allowed": True,
        "source_semantic_review_status": "SEMANTIC_IMPORT_CANDIDATE_REQUIRES_REVIEW",
        "source_semantic_review_reason": (
            "declaration is syntactically plausible but still requires semantic "
            "review and downstream local Lean/AXLE verification"
        ),
    }


def _source_lookup_rank_key(
    *,
    hit: Mapping[str, Any],
    normalized_terms: list[str],
    work_order: Mapping[str, Any] | None = None,
) -> tuple[int, int, int, int, int, str, int]:
    primary = normalized_terms[0] if normalized_terms else ""
    match_term = str(hit.get("match_term", "") or "").lower()
    snippet = str(hit.get("snippet", "") or "")
    declaration_name = _lean_declaration_name(snippet)
    declaration_name_normalized = _compact_identifier(declaration_name)
    primary_normalized = _compact_identifier(primary)
    path = str(hit.get("path", "") or "")
    candidate_kind = str(hit.get("candidate_kind", "") or "")
    review = _source_lookup_semantic_import_review(
        hit=hit,
        normalized_terms=normalized_terms,
        work_order=work_order,
    )
    semantic_import_allowed = bool(
        review.get("semantic_import_candidate_allowed", False)
    )
    term_index = (
        normalized_terms.index(match_term)
        if match_term in normalized_terms
        else len(normalized_terms)
    )
    context_score = int(hit.get("source_lookup_context_score", 0) or 0)
    return (
        0
        if candidate_kind == "lean_declaration" and semantic_import_allowed
        else 1
        if candidate_kind == "lean_declaration"
        else 2,
        0
        if primary_normalized
        and (
            primary_normalized in declaration_name_normalized
            or primary_normalized in _compact_identifier(Path(path).stem)
        )
        else 1,
        term_index,
        -context_score,
        1 if match_term in {"quantile", "exchangeability"} else 0,
        path,
        int(hit.get("line", 0) or 0),
    )


def _source_lookup_rank_reason(
    *,
    hit: Mapping[str, Any],
    normalized_terms: list[str],
) -> str:
    candidate_kind = str(hit.get("candidate_kind", "") or "")
    match_term = str(hit.get("match_term", "") or "")
    context_score = int(hit.get("source_lookup_context_score", 0) or 0)
    primary = normalized_terms[0] if normalized_terms else ""
    declaration_name = _lean_declaration_name(str(hit.get("snippet", "") or ""))
    primary_normalized = _compact_identifier(primary)
    declaration_name_normalized = _compact_identifier(declaration_name)
    if candidate_kind == "lean_declaration" and primary_normalized in declaration_name_normalized:
        return "declaration_name_matches_primary_placeholder"
    if context_score > 0:
        return (
            f"contextual_{candidate_kind}_match_term={match_term}"
            f"_context_score={context_score}"
        )
    if candidate_kind == "lean_declaration":
        return f"lean_declaration_match_term={match_term}"
    return f"source_reference_match_term={match_term}"


_WEAK_CONTEXTUAL_DECLARATION_MATCH_TERMS = frozenset(
    {
        "alpha",
        "bridge",
        "coverage",
        "event",
        "finite",
        "interval",
        "prediction",
        "sample",
        "samples",
        "score",
        "scores",
        "split",
    }
)


def _source_lookup_declaration_has_exact_or_high_signal_match(
    *,
    hit: Mapping[str, Any],
    normalized_terms: list[str],
    work_order: Mapping[str, Any] | None = None,
) -> bool:
    snippet = str(hit.get("snippet", "") or "")
    declaration_name = _lean_declaration_name(snippet)
    path_stem = Path(str(hit.get("path", "") or "")).stem
    declaration_context = _compact_identifier(
        " ".join([declaration_name, path_stem, snippet])
    )
    exact_aliases = _source_lookup_exact_aliases(
        work_order=work_order,
        normalized_terms=normalized_terms,
    )
    if any(alias and alias in declaration_context for alias in exact_aliases):
        return True
    high_signal_terms = _source_lookup_high_signal_terms(normalized_terms)
    line_matched_terms = {
        str(term).lower()
        for term in hit.get("matched_terms", []) or []
        if str(term).strip()
    }
    if high_signal_terms & line_matched_terms:
        return True
    high_signal_compacts = {
        _compact_identifier(term)
        for term in high_signal_terms
        if _compact_identifier(term)
    }
    return any(
        compact and compact in declaration_context for compact in high_signal_compacts
    )


def _source_lookup_exact_aliases(
    *,
    work_order: Mapping[str, Any] | None,
    normalized_terms: list[str],
) -> set[str]:
    aliases: set[str] = set()
    if isinstance(work_order, Mapping):
        raw_values: list[Any] = [
            work_order.get("placeholder_symbol", ""),
            work_order.get("target_theorem_name", ""),
            work_order.get("target_lean_declaration", ""),
            *list(work_order.get("target_ids", []) or []),
            *list(work_order.get("target_theorem_goal_ids", []) or []),
        ]
    else:
        raw_values = []
    if normalized_terms:
        raw_values.append(normalized_terms[0])
    for value in raw_values:
        text = str(value or "").strip()
        compact = _compact_identifier(text)
        if len(compact) >= 4:
            aliases.add(compact)
    return aliases


def _source_lookup_high_signal_terms(normalized_terms: list[str]) -> set[str]:
    terms: set[str] = set()
    for term in normalized_terms:
        stripped = str(term or "").lower().strip()
        if (
            not stripped
            or len(stripped) < 4
            or len(stripped) > 80
            or stripped in _WEAK_CONTEXTUAL_DECLARATION_MATCH_TERMS
        ):
            continue
        if re.search(r"[a-z]", stripped):
            terms.add(stripped)
    return terms


def _source_lookup_context_score(
    *,
    line_matched_terms: list[str],
    file_matched_terms: list[str],
    normalized_terms: list[str],
) -> int:
    if not normalized_terms:
        return 0
    primary = normalized_terms[0]
    secondary_terms = [term for term in normalized_terms[1:] if term != primary]
    line_secondary = {term for term in line_matched_terms if term in secondary_terms}
    file_secondary = {term for term in file_matched_terms if term in secondary_terms}
    # A line that mentions multiple requested terms is strongest. File-level
    # context still matters because Lean definitions often split declarations
    # and theorem names across nearby lines.
    return 3 * len(line_secondary) + len(file_secondary)


def _source_lookup_hit_is_eligible(
    *,
    line_matched_terms: list[str],
    file_matched_terms: list[str],
    normalized_terms: list[str],
    work_order: Mapping[str, Any] | None,
) -> bool:
    if not _is_source_to_bridge_adapter_object_definition_work_order(work_order):
        return True
    primary = normalized_terms[0] if normalized_terms else ""
    primary_aliases = _source_lookup_primary_aliases(primary)
    all_terms = set(line_matched_terms) | set(file_matched_terms)
    if primary_aliases & all_terms:
        return True
    target = str((work_order or {}).get("target_theorem_name", "") or "").lower()
    if target and len(target.strip()) >= 3 and target in all_terms:
        return True
    return False


def _source_lookup_primary_aliases(primary: str) -> set[str]:
    stripped = primary.strip().lower()
    aliases = {stripped} if stripped else set()
    compact = _compact_identifier(stripped)
    if compact:
        aliases.add(compact)
    if stripped in {"α", "α_total", "alpha_total"}:
        aliases.add("alpha")
    return aliases


def _source_lookup_term_occurs(
    text: str,
    term: str,
    *,
    strict_identifier_start: bool = False,
) -> bool:
    if not term:
        return False
    if not strict_identifier_start:
        return term in text
    start = 0
    while True:
        index = text.find(term, start)
        if index < 0:
            return False
        if index == 0:
            return True
        previous = text[index - 1]
        if not (previous.isalnum() or previous == "'"):
            return True
        start = index + 1


def _is_source_to_bridge_adapter_object_definition_work_order(
    work_order: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(work_order, Mapping):
        return False
    replacement_strategy = str(
        work_order.get("replacement_strategy", "") or ""
    ).lower()
    runtime_queue_status = str(work_order.get("runtime_queue_status", "") or "").lower()
    trigger = ""
    input_summary = work_order.get("input_summary", {})
    if isinstance(input_summary, Mapping):
        trigger = str(input_summary.get("trigger", "") or "").lower()
    return (
        "source_to_bridge_adapter_object" in replacement_strategy
        or "source_to_bridge_adapter_object" in runtime_queue_status
        or "source_to_bridge_adapter_object" in trigger
        or bool(work_order.get("source_to_bridge_adapter_instantiation_group_id"))
    )


_GENERATED_OR_CACHE_SOURCE_PARTS = {
    ".git",
    ".lake",
    ".mypy_cache",
    ".pytest_cache",
    ".tmp_publish",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "runs",
}


def _is_generated_or_cache_source_path(path: Path, *, root: Path) -> bool:
    """Avoid treating generated caches or run artifacts as source authority."""

    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        relative_parts = path.parts
    return any(part in _GENERATED_OR_CACHE_SOURCE_PARTS for part in relative_parts)


def _search_terms(work_order: Mapping[str, Any]) -> list[str]:
    terms: list[str] = []
    placeholder = str(work_order.get("placeholder_symbol", "") or "").strip()
    if placeholder:
        terms.append(placeholder)
        placeholder_lower = placeholder.lower()
        if placeholder_lower == "exchangeable":
            terms.extend(["exchangeability", "exchangeab"])
        elif placeholder_lower == "orderstat":
            terms.extend(["orderStatistic", "order statistic", "quantile"])
    for value in [
        *list(work_order.get("search_targets", []) or []),
        *list(work_order.get("candidate_registered_obligation_ids", []) or []),
    ]:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped:
            continue
        if stripped not in terms:
            terms.append(stripped)
    return terms[:12]


def _looks_like_lean_declaration(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith(("def ", "theorem ", "lemma ", "structure ", "class ", "abbrev "))


def _lean_declaration_name(line: str) -> str:
    stripped = line.strip()
    match = re.match(
        r"^(?:noncomputable\s+)?(?:private\s+)?(?:def|theorem|lemma|structure|class|abbrev)\s+"
        r"([A-Za-z_][A-Za-z0-9_'.]*)",
        stripped,
    )
    return match.group(1) if match else ""


def _compact_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _count_by_key(rows: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "") or "")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _has_placeholder_policy_lineage(row: Mapping[str, Any]) -> bool:
    return bool(
        str(row.get("placeholder_policy_id", "") or "").strip()
        and str(row.get("placeholder_policy_scope", "") or "").strip()
    )


def _count_placeholder_policy_lineage(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if _has_placeholder_policy_lineage(row))


def _placeholder_policy_lineage_complete(
    *row_groups: Sequence[Mapping[str, Any]],
) -> bool:
    for rows in row_groups:
        for row in rows:
            if not _has_placeholder_policy_lineage(row):
                return False
    return True


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
    path.write_text(
        "".join(
            json.dumps(dict(row), sort_keys=True, default=str) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )

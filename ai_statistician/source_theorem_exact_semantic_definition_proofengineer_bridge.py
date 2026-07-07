from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .exact_semantic_definition_policy import (
    exact_semantic_definition_placeholder_policy,
)
from .fingerprint import stable_hash
from .research_architect import KERNEL_PROOF_BOUNDARY
from .source_theorem_exact_semantic_definition_source_lookup import (
    EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS,
    resolve_exact_semantic_definition_review_packets_path,
)


ARTIFACT_KIND = "SourceTheoremExactSemanticDefinitionProofEngineerBridgeManifest"
REPAIR_PACKET_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionProofEngineerRepairPacket"
)
LEAN_REPAIR_TASK_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionLeanRepairTask"
)
TYPECHECKED_CANDIDATE_REVIEW_PACKET_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
)
LEARNING_TASK = "source_theorem_exact_semantic_definition_proofengineer_bridge"
PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_PROOFENGINEER_BRIDGE_NOT_PROOF_EVIDENCE"
)
LEAN_REPAIR_TASK_PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
)
BOUNDARY = (
    "Exact semantic-definition ProofEngineer bridge packets are implementation "
    "contracts for replacing or importing reviewed Lean semantics before source "
    "theorem proof-body search resumes. They are not theorem proof, source lookup "
    "proof, or semantic-definition kernel evidence. Promotion requires a later "
    "local Lean/AXLE verifier manifest for the repaired definition/import and "
    "the exact source theorem candidate."
)


def run_source_theorem_exact_semantic_definition_proofengineer_bridge(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    lookup_manifest: Path | None = None,
    review_packets_jsonl: Path | None = None,
    question_id: str = "",
) -> dict[str, Any]:
    packet_path = resolve_source_theorem_exact_semantic_definition_review_packets_path(
        runtime_dir=runtime_dir,
        lookup_manifest=lookup_manifest,
        review_packets_jsonl=review_packets_jsonl,
    )
    review_packets = _read_jsonl(packet_path)
    repair_packets = [
        _repair_packet(row, question_id=question_id)
        for row in review_packets
        if isinstance(row, Mapping)
    ]
    lean_repair_tasks = [
        _lean_repair_task(packet)
        for packet in repair_packets
        if isinstance(packet, Mapping)
    ]
    learning_rows = [
        _learning_row(packet, source_review_packet=row)
        for packet, row in zip(repair_packets, review_packets, strict=False)
        if isinstance(row, Mapping)
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    packets_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_proofengineer_repair_packets.jsonl"
    )
    lean_tasks_path = (
        out_dir / "source_theorem_exact_semantic_definition_lean_repair_tasks.jsonl"
    )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(packets_path, repair_packets)
    _write_jsonl(lean_tasks_path, lean_repair_tasks)
    _write_jsonl(learning_path, learning_rows)
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_runtime_dir": str(runtime_dir or ""),
        "source_lookup_manifest": str(lookup_manifest or ""),
        "source_review_packets_jsonl": str(packet_path),
        "repair_packets_jsonl": str(packets_path),
        "lean_repair_tasks_jsonl": str(lean_tasks_path),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_review_packets": len(review_packets),
        "n_repair_packets": len(repair_packets),
        "n_lean_repair_tasks": len(lean_repair_tasks),
        "n_review_packets_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(review_packets)
        ),
        "n_repair_packets_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(repair_packets)
        ),
        "n_lean_repair_tasks_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(lean_repair_tasks)
        ),
        "n_runtime_learning_rows_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(learning_rows)
        ),
        "placeholder_policy_lineage_complete": (
            _placeholder_policy_lineage_complete(
                review_packets,
                repair_packets,
                lean_repair_tasks,
                learning_rows,
            )
        ),
        "n_import_candidate_declaration_packets": sum(
            1
            for row in repair_packets
            if row.get("repair_strategy") == "review_import_candidate_source_declaration"
        ),
        "n_lean_import_candidate_tasks": sum(
            1
            for row in lean_repair_tasks
            if row.get("lean_repair_action") == "review_import_source_declaration"
        ),
        "n_lean_synthesize_definition_tasks": sum(
            1
            for row in lean_repair_tasks
            if row.get("lean_repair_action") == "synthesize_exact_definition"
        ),
        "n_synthesize_from_references_packets": sum(
            1
            for row in repair_packets
            if row.get("repair_strategy")
            == "synthesize_reviewed_definition_from_source_references"
        ),
        "n_review_typechecked_candidate_packets": sum(
            1
            for row in repair_packets
            if row.get("repair_strategy")
            == "review_typechecked_exact_definition_candidate"
        ),
        "n_review_packets_with_semantic_review_decision": sum(
            1
            for row in repair_packets
            if _semantic_review_decision_reported(row)
        ),
        "n_review_typechecked_candidate_packets_with_semantic_review_decision": sum(
            1
            for row in repair_packets
            if row.get("repair_strategy")
            == "review_typechecked_exact_definition_candidate"
            and _semantic_review_decision_reported(row)
        ),
        "n_review_typechecked_candidate_packets_llm_approved": sum(
            1
            for row in repair_packets
            if row.get("repair_strategy")
            == "review_typechecked_exact_definition_candidate"
            and str(row.get("semantic_review_decision", "") or "")
            == "approved_definition_candidate"
        ),
        "n_lean_review_typechecked_candidate_tasks": sum(
            1
            for row in lean_repair_tasks
            if row.get("lean_repair_action")
            == "review_typechecked_exact_definition_candidate"
        ),
        "n_no_source_hit_packets": sum(
            1
            for row in repair_packets
            if row.get("repair_strategy") == "author_reviewed_definition_from_contract"
        ),
        "n_repair_packets_from_pseudo_formal": sum(
            1 for row in repair_packets if _has_pseudo_formal_origin(row)
        ),
        "n_repair_packets_from_formalizer_pf_component_gate": sum(
            1
            for row in repair_packets
            if _has_formalizer_pf_component_gate_origin(row)
        ),
        "n_lean_repair_tasks_from_pseudo_formal": sum(
            1 for row in lean_repair_tasks if _has_pseudo_formal_origin(row)
        ),
        "n_lean_repair_tasks_from_formalizer_pf_component_gate": sum(
            1
            for row in lean_repair_tasks
            if _has_formalizer_pf_component_gate_origin(row)
        ),
        "source_pseudo_formal_work_order_ids": list(
            dict.fromkeys(
                str(row.get("source_pseudo_formal_work_order_id", "") or "")
                for row in repair_packets
                if str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
            )
        ),
        "source_pseudo_formal_block_ids": list(
            dict.fromkeys(
                str(row.get("source_pseudo_formal_block_id", "") or "")
                for row in repair_packets
                if str(row.get("source_pseudo_formal_block_id", "") or "").strip()
            )
        ),
        "source_prompt_scaffold_ids": list(
            dict.fromkeys(
                str(row.get("source_prompt_scaffold_id", "") or "")
                for row in repair_packets
                if str(row.get("source_prompt_scaffold_id", "") or "").strip()
            )
        ),
        "source_prompt_scaffold_kinds": list(
            dict.fromkeys(
                str(row.get("source_prompt_scaffold_kind", "") or "")
                for row in repair_packets
                if str(row.get("source_prompt_scaffold_kind", "") or "").strip()
            )
        ),
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": (
            _formalizer_pf_component_gate_exact_rows_jsonl_paths(repair_packets)
        ),
        "placeholder_symbols": list(
            dict.fromkeys(
                str(row.get("placeholder_symbol", "") or "")
                for row in repair_packets
                if str(row.get("placeholder_symbol", "") or "").strip()
            )
        ),
        "target_theorem_names": list(
            dict.fromkeys(
                str(row.get("target_theorem_name", "") or "")
                for row in repair_packets
                if str(row.get("target_theorem_name", "") or "").strip()
            )
        ),
        "lean_repair_task_status": "PENDING_LOCAL_LEAN_ATTEMPT",
        "lean_repair_task_proof_evidence_status": (
            LEAN_REPAIR_TASK_PROOF_EVIDENCE_STATUS
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_proofengineer_bridge_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def resolve_source_theorem_exact_semantic_definition_review_packets_path(
    *,
    runtime_dir: Path | None = None,
    lookup_manifest: Path | None = None,
    review_packets_jsonl: Path | None = None,
) -> Path:
    if review_packets_jsonl is not None:
        return review_packets_jsonl
    if lookup_manifest is not None:
        return resolve_exact_semantic_definition_review_packets_path(
            lookup_manifest=lookup_manifest,
            review_packets_jsonl=None,
        )
    if runtime_dir is None:
        raise ValueError("runtime_dir, lookup_manifest, or review_packets_jsonl is required")
    manifest_path = runtime_dir / "research_agent_runtime_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        artifacts = {}
    raw_lookup_manifest = str(
        artifacts.get(
            "runtime_source_theorem_exact_semantic_definition_source_lookup_manifest",
            "",
        )
        or ""
    )
    if raw_lookup_manifest:
        lookup_path = _resolve_runtime_artifact_path(
            runtime_dir=runtime_dir,
            raw_path=raw_lookup_manifest,
        )
        if lookup_path.exists():
            return resolve_exact_semantic_definition_review_packets_path(
                lookup_manifest=lookup_path,
                review_packets_jsonl=None,
            )
    raw_packets = str(
        artifacts.get(
            "runtime_source_theorem_exact_semantic_definition_closure_review_packets_jsonl",
            "",
        )
        or ""
    )
    if raw_packets:
        return _resolve_runtime_artifact_path(runtime_dir=runtime_dir, raw_path=raw_packets)
    for artifact_key in (
        "runtime_late_source_theorem_exact_semantic_definition_materialized_typechecked_candidate_review_packets_jsonl",
        "runtime_source_theorem_exact_semantic_definition_materialized_typechecked_candidate_review_packets_jsonl",
    ):
        raw_typechecked_packets = artifacts.get(artifact_key, "")
        candidate_paths = (
            raw_typechecked_packets
            if isinstance(raw_typechecked_packets, list | tuple)
            else [raw_typechecked_packets]
        )
        for raw_candidate_path in candidate_paths:
            raw_candidate = str(raw_candidate_path or "")
            if not raw_candidate:
                continue
            candidate_path = _resolve_runtime_artifact_path(
                runtime_dir=runtime_dir,
                raw_path=raw_candidate,
            )
            if candidate_path.exists():
                return candidate_path
    raise ValueError(
        "runtime manifest does not list exact semantic-definition source lookup "
        "manifest, closure review packets, or typechecked candidate review packets"
    )


def _repair_packet(row: Mapping[str, Any], *, question_id: str = "") -> dict[str, Any]:
    declarations = [
        dict(value)
        for value in row.get("candidate_source_declarations", []) or []
        if isinstance(value, Mapping)
    ]
    references = [
        dict(value)
        for value in row.get("candidate_source_references", []) or []
        if isinstance(value, Mapping)
    ]
    placeholder = str(row.get("placeholder_symbol", "") or "").strip()
    target = str(row.get("target_theorem_name", "") or "").strip()
    target_ids = _target_ids_from_row(row, fallback_target=target)
    artifact_kind = str(row.get("artifact_kind", "") or "")
    has_typechecked_candidate = (
        _has_typechecked_exact_semantic_definition_candidate(row)
    )
    is_closure_review_handoff = (
        artifact_kind == "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewPacket"
    )
    is_typechecked_candidate_review_handoff = (
        artifact_kind == TYPECHECKED_CANDIDATE_REVIEW_PACKET_ARTIFACT_KIND
    )
    if declarations:
        repair_strategy = "review_import_candidate_source_declaration"
    elif (
        has_typechecked_candidate
        and (is_closure_review_handoff or is_typechecked_candidate_review_handoff)
    ):
        repair_strategy = "review_typechecked_exact_definition_candidate"
    elif references:
        repair_strategy = "synthesize_reviewed_definition_from_source_references"
    else:
        repair_strategy = "author_reviewed_definition_from_contract"
    repair_packet_id = (
        "source_theorem_exact_semantic_definition_proofengineer_repair_packet:"
        + stable_hash(
            [
                row.get("review_packet_id", ""),
                row.get("source_review_packet_id", ""),
                row.get("repair_queue_id", ""),
                row.get("source_definition_closure_work_order_id", ""),
                target,
                placeholder,
                repair_strategy,
                declarations[:3],
                references[:3],
                row.get("definition_only_candidate_artifact_path", ""),
                row.get("candidate_lean_project_hint", ""),
                row.get("semantic_definition_typecheck_evidence_status", ""),
            ]
        )[:20]
    )
    required_next_checks = [
        str(value)
        for value in row.get("required_next_checks", []) or []
        if str(value).strip()
    ]
    required_next_checks = list(
        dict.fromkeys(
            [
                *required_next_checks,
                "materialize or import the reviewed exact semantic definition",
                "run local Lean/AXLE before source-theorem proof-body search resumes",
            ]
        )
    )[:10]
    return {
        "schema_version": 1,
        "artifact_kind": REPAIR_PACKET_ARTIFACT_KIND,
        "repair_packet_id": repair_packet_id,
        "source_review_packet_id": str(
            row.get("review_packet_id", "")
            or row.get("source_review_packet_id", "")
            or ""
        ),
        "source_repair_queue_id": str(row.get("repair_queue_id", "") or ""),
        "source_definition_closure_work_order_id": str(
            row.get("source_definition_closure_work_order_id", "") or ""
        ),
        "source_lookup_id": str(row.get("source_lookup_id", "") or ""),
        "question_id": str(question_id or row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target,
        "target_ids": target_ids,
        "placeholder_symbol": placeholder,
        "repair_strategy": repair_strategy,
        "definition_contract": dict(row.get("definition_contract", {}) or {}),
        "candidate_source_declarations": declarations,
        "candidate_source_references": references,
        "source_lookup_hits": list(row.get("source_lookup_hits", []) or []),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "candidate_registered_obligation_ids": list(
            row.get("candidate_registered_obligation_ids", []) or []
        ),
        "kernel_verified_source_theorem_semantic_support_obligation_ids": list(
            row.get("kernel_verified_source_theorem_semantic_support_obligation_ids", [])
            or []
        ),
        "source_theorem_target_identity_status": str(
            row.get("source_theorem_target_identity_status", "") or ""
        ),
        "source_theorem_target_provenance": dict(
            row.get("source_theorem_target_provenance", {}) or {}
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
        "candidate_lean_project_hint": str(
            row.get("candidate_lean_project_hint", "") or ""
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
        "semantic_review_decision": str(
            row.get("semantic_review_decision", "") or ""
        ),
        "semantic_review_status": str(row.get("semantic_review_status", "") or ""),
        "semantic_review_evidence": list(row.get("semantic_review_evidence", []) or []),
        "semantic_review_required_before_proof_body": bool(
            row.get("semantic_review_required_before_proof_body", False)
        ),
        "llm_claimed_source_theorem_ready_for_exact_proof_body": bool(
            row.get("llm_claimed_source_theorem_ready_for_exact_proof_body", False)
        ),
        "candidate_repair_feedback": dict(
            row.get("candidate_repair_feedback", {}) or {}
        ),
        "source_execution_status": str(row.get("source_execution_status", "") or ""),
        "authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            row.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(row.get("source_repair_strategy", "") or ""),
        **_exact_semantic_definition_context(row),
        "required_next_checks": required_next_checks,
        "local_lean_required_before_proof_body": True,
        "source_theorem_kernel_evidence_eligible": False,
        "owner_agent": "Formalizer/ProofEngineer/LeanProver",
        "action_type": "repair_reviewed_exact_semantic_definition",
        "acceptance_gate": (
            "A reviewed definition/import replaces the placeholder and local "
            "Lean/AXLE verifies the repaired exact semantic-definition candidate "
            "before any source-theorem proof-body execution resumes."
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _has_typechecked_exact_semantic_definition_candidate(
    row: Mapping[str, Any],
) -> bool:
    candidate = row.get(
        "source_theorem_exact_semantic_definition_typechecked_candidate",
        {},
    )
    if not isinstance(candidate, Mapping):
        candidate = {}
    semantic_status = str(
        row.get("semantic_definition_typecheck_evidence_status", "")
        or candidate.get("semantic_definition_typecheck_evidence_status", "")
        or ""
    ).strip()
    local_compiled = bool(
        row.get("local_definition_lean_compiled", False)
        or candidate.get("local_definition_lean_compiled", False)
    )
    artifact_path = str(
        row.get("definition_only_candidate_artifact_path", "")
        or row.get("candidate_artifact_path", "")
        or candidate.get("definition_only_candidate_artifact_path", "")
        or candidate.get("candidate_artifact_path", "")
        or ""
    ).strip()
    if local_compiled and (artifact_path or semantic_status):
        return True
    return semantic_status in {
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF",
        "TYPECHECKED_CANDIDATE_SEMANTIC_REVIEW_REQUIRED",
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_LOCAL_LEAN_COMPILED_REVIEW_REQUIRED",
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED",
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED",
    }


def _lean_repair_task(repair_packet: Mapping[str, Any]) -> dict[str, Any]:
    target_theorem_name = str(repair_packet.get("target_theorem_name", "") or "")
    target_ids = _target_ids_from_row(
        repair_packet,
        fallback_target=target_theorem_name,
    )
    declarations = [
        dict(value)
        for value in repair_packet.get("candidate_source_declarations", []) or []
        if isinstance(value, Mapping)
    ]
    references = [
        dict(value)
        for value in repair_packet.get("candidate_source_references", []) or []
        if isinstance(value, Mapping)
    ]
    repair_strategy = str(repair_packet.get("repair_strategy", "") or "")
    if repair_strategy == "review_import_candidate_source_declaration":
        lean_repair_action = "review_import_source_declaration"
    elif repair_strategy == "review_typechecked_exact_definition_candidate":
        lean_repair_action = "review_typechecked_exact_definition_candidate"
    elif repair_strategy == "synthesize_reviewed_definition_from_source_references":
        lean_repair_action = "synthesize_exact_definition"
    else:
        lean_repair_action = "author_exact_definition"
    task_id = (
        "source_theorem_exact_semantic_definition_lean_repair_task:"
        + stable_hash(
            [
                repair_packet.get("repair_packet_id", ""),
                repair_packet.get("target_theorem_name", ""),
                repair_packet.get("placeholder_symbol", ""),
                lean_repair_action,
                declarations[:2],
                references[:2],
                repair_packet.get("definition_only_candidate_artifact_path", ""),
                repair_packet.get("candidate_lean_project_hint", ""),
                repair_packet.get(
                    "semantic_definition_typecheck_evidence_status",
                    "",
                ),
            ]
        )[:20]
    )
    candidate_imports = [
        {
            "path": str(row.get("path", "") or ""),
            "line": int(row.get("line", 0) or 0),
            "snippet": str(row.get("snippet", "") or ""),
            "candidate_kind": str(row.get("candidate_kind", "") or ""),
            "semantic_import_candidate_allowed": bool(
                row.get("semantic_import_candidate_allowed", True)
            ),
            "source_semantic_review_status": str(
                row.get("source_semantic_review_status", "") or ""
            ),
            "source_semantic_review_reason": str(
                row.get("source_semantic_review_reason", "") or ""
            ),
            "source_lookup_rank": int(row.get("source_lookup_rank", 0) or 0),
            "source_lookup_rank_reason": str(
                row.get("source_lookup_rank_reason", "") or ""
            ),
        }
        for row in declarations[:5]
        if str(row.get("path", "") or "").strip()
    ]
    source_reference_hints = [
        {
            "path": str(row.get("path", "") or ""),
            "line": int(row.get("line", 0) or 0),
            "snippet": str(row.get("snippet", "") or ""),
            "candidate_kind": str(row.get("candidate_kind", "") or ""),
        }
        for row in references[:8]
        if str(row.get("path", "") or "").strip()
    ]
    return {
        "schema_version": 1,
        "artifact_kind": LEAN_REPAIR_TASK_ARTIFACT_KIND,
        "lean_repair_task_id": task_id,
        "source_repair_packet_id": str(
            repair_packet.get("repair_packet_id", "") or ""
        ),
        "source_repair_queue_id": str(
            repair_packet.get("source_repair_queue_id", "") or ""
        ),
        "source_review_packet_id": str(
            repair_packet.get("source_review_packet_id", "") or ""
        ),
        "source_definition_closure_work_order_id": str(
            repair_packet.get("source_definition_closure_work_order_id", "") or ""
        ),
        "question_id": str(repair_packet.get("question_id", "") or ""),
        "question_title": str(repair_packet.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": str(repair_packet.get("placeholder_symbol", "") or ""),
        "lean_repair_action": lean_repair_action,
        "repair_strategy": repair_strategy,
        "definition_contract": dict(repair_packet.get("definition_contract", {}) or {}),
        "candidate_import_declarations": candidate_imports,
        "source_reference_hints": source_reference_hints,
        "semantic_alignment_constraints": list(
            repair_packet.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            repair_packet.get("semantic_alignment_blockers", []) or []
        ),
        "source_theorem_exact_semantic_definition_typechecked_candidate": dict(
            repair_packet.get(
                "source_theorem_exact_semantic_definition_typechecked_candidate",
                {},
            )
            or {}
        ),
        "definition_only_candidate_artifact_path": str(
            repair_packet.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_lean_project_hint": str(
            repair_packet.get("candidate_lean_project_hint", "") or ""
        ),
        "candidate_artifact_path": str(
            repair_packet.get("candidate_artifact_path", "") or ""
        ),
        "local_definition_lean_checked": bool(
            repair_packet.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            repair_packet.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            repair_packet.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        "semantic_review_decision": str(
            repair_packet.get("semantic_review_decision", "") or ""
        ),
        "semantic_review_status": str(
            repair_packet.get("semantic_review_status", "") or ""
        ),
        "semantic_review_evidence": list(
            repair_packet.get("semantic_review_evidence", []) or []
        ),
        "semantic_review_required_before_proof_body": bool(
            repair_packet.get("semantic_review_required_before_proof_body", False)
        ),
        "llm_claimed_source_theorem_ready_for_exact_proof_body": bool(
            repair_packet.get(
                "llm_claimed_source_theorem_ready_for_exact_proof_body",
                False,
            )
        ),
        "candidate_repair_feedback": dict(
            repair_packet.get("candidate_repair_feedback", {}) or {}
        ),
        "source_execution_status": str(
            repair_packet.get("source_execution_status", "") or ""
        ),
        "authoring_trigger": str(repair_packet.get("authoring_trigger", "") or ""),
        "authoring_mode": str(repair_packet.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            repair_packet.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(
            repair_packet.get("source_repair_strategy", "") or ""
        ),
        **_exact_semantic_definition_context(repair_packet),
        "required_next_checks": list(
            repair_packet.get("required_next_checks", []) or []
        ),
        "lean_attempt_status": "NOT_ATTEMPTED",
        "local_lean_attempted": False,
        "local_lean_kernel_verified": False,
        "source_theorem_kernel_evidence_eligible": False,
        "next_owner": "ProofEngineer/LeanProver",
        "acceptance_gate": (
            "ProofEngineer materializes or imports the reviewed exact semantic "
            "definition, then local Lean/AXLE verifies the repaired definition "
            "candidate before exact source-theorem proof-body execution resumes."
        ),
        "proof_evidence_status": LEAN_REPAIR_TASK_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "This Lean repair task is an executable handoff target only. It is not "
            "semantic-definition proof evidence, source theorem proof evidence, or "
            "Lean kernel evidence until a later local Lean/AXLE manifest reports "
            "the repaired declaration checked without sorry."
        ),
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _learning_row(
    repair_packet: Mapping[str, Any],
    *,
    source_review_packet: Mapping[str, Any],
) -> dict[str, Any]:
    target_theorem_name = str(repair_packet.get("target_theorem_name", "") or "")
    target_ids = _target_ids_from_row(
        repair_packet,
        fallback_target=target_theorem_name,
    )
    return {
        "schema_version": 1,
        "artifact_kind": REPAIR_PACKET_ARTIFACT_KIND,
        "learning_task": LEARNING_TASK,
        "question_id": str(repair_packet.get("question_id", "") or ""),
        "question_title": str(repair_packet.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": str(repair_packet.get("placeholder_symbol", "") or ""),
        "repair_packet_id": str(repair_packet.get("repair_packet_id", "") or ""),
        "source_review_packet_id": str(
            repair_packet.get("source_review_packet_id", "") or ""
        ),
        "source_definition_closure_work_order_id": str(
            repair_packet.get("source_definition_closure_work_order_id", "") or ""
        ),
        "repair_strategy": str(repair_packet.get("repair_strategy", "") or ""),
        **_exact_semantic_definition_context(repair_packet),
        "input_summary": {
            "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_PROOFENGINEER_BRIDGE",
            "source_lookup_status": str(
                source_review_packet.get("lookup_status", "") or ""
            ),
            "repair_packet_id": str(repair_packet.get("repair_packet_id", "") or ""),
            "target_theorem_name": target_theorem_name,
            "target_ids": target_ids,
            "placeholder_symbol": str(
                repair_packet.get("placeholder_symbol", "") or ""
            ),
            "repair_strategy": str(repair_packet.get("repair_strategy", "") or ""),
            "candidate_source_declaration_count": len(
                repair_packet.get("candidate_source_declarations", []) or []
            ),
            "candidate_source_reference_count": len(
                repair_packet.get("candidate_source_references", []) or []
            ),
            "definition_only_candidate_artifact_path": str(
                repair_packet.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_lean_project_hint": str(
                repair_packet.get("candidate_lean_project_hint", "") or ""
            ),
            "local_definition_lean_compiled": bool(
                repair_packet.get("local_definition_lean_compiled", False)
            ),
            "semantic_definition_typecheck_evidence_status": str(
                repair_packet.get("semantic_definition_typecheck_evidence_status", "")
                or ""
            ),
            "semantic_review_decision": str(
                repair_packet.get("semantic_review_decision", "") or ""
            ),
            "semantic_review_status": str(
                repair_packet.get("semantic_review_status", "") or ""
            ),
            "semantic_review_evidence": list(
                repair_packet.get("semantic_review_evidence", []) or []
            ),
            "semantic_review_required_before_proof_body": bool(
                repair_packet.get("semantic_review_required_before_proof_body", False)
            ),
            "llm_claimed_source_theorem_ready_for_exact_proof_body": bool(
                repair_packet.get(
                    "llm_claimed_source_theorem_ready_for_exact_proof_body",
                    False,
                )
            ),
            **_exact_semantic_definition_context(repair_packet),
            "required_next_checks": list(
                repair_packet.get("required_next_checks", []) or []
            ),
            "source_theorem_kernel_evidence_eligible": False,
        },
        "target_behavior": str(
            source_review_packet.get("target_behavior", "")
            or "repair or import exact semantic definitions before proof-body search"
        ),
        "acceptance_gate": str(repair_packet.get("acceptance_gate", "") or ""),
        "source_theorem_kernel_evidence_eligible": False,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _exact_semantic_definition_context(row: Mapping[str, Any]) -> dict[str, Any]:
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


def _semantic_review_decision_reported(row: Mapping[str, Any]) -> bool:
    return str(row.get("semantic_review_decision", "") or "").strip() not in {
        "",
        "not_reported",
    }


def _has_placeholder_policy_lineage(row: Mapping[str, Any]) -> bool:
    return bool(
        str(row.get("placeholder_policy_id", "") or "").strip()
        and str(row.get("placeholder_policy_scope", "") or "").strip()
    )


def _count_placeholder_policy_lineage(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if _has_placeholder_policy_lineage(row))


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


def _placeholder_policy_lineage_complete(
    *row_groups: Sequence[Mapping[str, Any]],
) -> bool:
    for rows in row_groups:
        for row in rows:
            if not _has_placeholder_policy_lineage(row):
                return False
    return True


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


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .formal_verifier_agentic_proof_execution_artifact_verifier import (
    FORBIDDEN_ARTIFACT_TOKENS,
    _lean_command,
    _run_local_lean,
)
from .research_architect import KERNEL_PROOF_BOUNDARY


ARTIFACT_KIND = "SourceTheoremProofBodyAdapterProofEngineerBridgeManifest"
ADAPTER_ROW_KIND = "SourceTheoremProofBodyAdapterCheckRow"
ADAPTER_PROOF_EVIDENCE_STATUS = (
    "SOURCE_THEOREM_PROOF_BODY_ADAPTER_BRIDGE_NOT_PROOF_EVIDENCE"
)
ADAPTER_KERNEL_VERIFIED_STATUS = (
    "KERNEL_VERIFIED_SOURCE_THEOREM_PROOF_BODY_ADAPTER_PRESENT"
)
BOUNDARY = (
    "Source-theorem proof-body adapter bridge rows are ProofEngineer tasks for "
    "connecting exact source-theorem hypotheses to already verified bridge or "
    "reduction premises. They are not full source-theorem proof evidence. A row "
    "can become adapter evidence only when a non-vacuous adapter theorem compiles "
    "under local Lean/AXLE with no forbidden placeholder tokens; the exact source "
    "theorem still must be rerun and kernel verified separately."
)
BRIDGE_PREMISE_BINDER_NAMES = (
    "hGoodCovered",
    "hBadEvent",
    "hRank",
    "hTotal",
    "h_total",
    "hBad",
    "hCoverage",
)


@dataclass(frozen=True)
class SourceTheoremProofBodyAdapterCheckRow:
    schema_version: int
    artifact_kind: str
    adapter_check_id: str
    work_order_id: str
    source_work_order_id: str
    source_queue_artifact_kind: str
    source_queue_status: str
    question_id: str
    question_title: str
    source_formalization_manifest_id: str
    source_formalizer_packet_id: str
    source_formal_target_id: str
    target_theorem_name: str
    target_lean_declaration: str
    target_ids: tuple[str, ...]
    target_theorem_goal_ids: tuple[str, ...]
    source_theorem_target_known: bool
    source_theorem_target_provenance: dict[str, Any]
    source_candidate_artifact_path: str
    proof_body_signature_probe_artifact_path: str
    source_theorem_signature_probe_artifact_path: str
    adapter_candidate_artifact_path: str
    adapter_declaration_name: str
    adapter_candidate_imports: tuple[str, ...]
    unavailable_import: str
    adapter_generation_mode: str
    adapter_candidate_vacuous: bool
    adapter_candidate_requires_unproven_bridge_premises: bool
    unproven_bridge_premise_names: tuple[str, ...]
    source_to_bridge_premise_derivation_work_items: tuple[dict[str, Any], ...]
    kernel_verified_source_to_bridge_premise_derivation_ids: tuple[str, ...]
    verified_source_to_bridge_premise_derivation_artifact_paths: tuple[str, ...]
    verified_source_to_bridge_premise_derivation_declarations: tuple[str, ...]
    verified_source_to_bridge_premise_derivation_signature_excerpts: tuple[str, ...]
    forbidden_tokens_found: tuple[str, ...]
    adapter_candidate_evidence_eligible: bool
    proof_body_goal_excerpt: tuple[str, ...]
    proof_body_goal_context: dict[str, Any]
    proof_body_goal_binder_names: tuple[str, ...]
    proof_body_goal_conclusion: str
    proof_body_attempt_summaries: tuple[str, ...]
    proof_body_attempt_count: int
    proof_body_gate_status: str
    source_theorem_exact_proof_body_reached: bool
    source_theorem_exact_proof_body_gate_open_for_kernel_repair: bool
    source_theorem_exact_proof_body_gate_open_target_names: tuple[str, ...]
    proof_body_adapter_required_reasons: tuple[str, ...]
    exact_goal_shape_obligation_id: str
    exact_goal_shape_obligation: str
    target_artifact_kind: str
    source_acceptance_gate: str
    semantic_alignment_constraints: tuple[str, ...]
    semantic_alignment_blockers: tuple[str, ...]
    source_theorem_kernel_evidence_eligible: bool
    kernel_verified_theorem_reduction_closure_target_ids: tuple[str, ...]
    kernel_verified_theorem_reduction_closure_declarations: tuple[str, ...]
    verified_theorem_reduction_closure_artifact_paths: tuple[str, ...]
    kernel_verified_source_theorem_semantic_support_obligation_ids: tuple[str, ...]
    local_lean_requested: bool
    local_lean_checked: bool
    local_lean_compiled: bool
    lean_command: tuple[str, ...]
    lean_project: str
    lean_timeout: int
    returncode: int
    diagnostics: tuple[str, ...]
    failure_classification: str
    adapter_kernel_verified: bool
    source_theorem_kernel_verified: bool
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool


def resolve_source_theorem_proof_body_adapter_queue_path(
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
        artifacts.get("runtime_source_theorem_proof_body_adapter_work_orders_jsonl", "")
        or ""
    )
    if not raw_path:
        raise ValueError(
            "runtime manifest does not list "
            "runtime_source_theorem_proof_body_adapter_work_orders_jsonl"
        )
    return _resolve_runtime_artifact_path(runtime_dir=runtime_dir, raw_path=raw_path)


def run_source_theorem_proof_body_adapter_proofengineer_bridge(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
    question_id: str = "",
    local_lean: bool = False,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = resolve_source_theorem_proof_body_adapter_queue_path(
        runtime_dir=runtime_dir,
        queue_jsonl=queue_jsonl,
    )
    work_orders = _read_jsonl(queue_path)
    project_path = Path(lean_project) if lean_project else None
    command = lean_command or _lean_command(project_path)
    candidate_dir = out_dir / "adapter_candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        _adapter_check_row(
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
    rows_path = out_dir / "source_theorem_proof_body_adapter_checks.jsonl"
    _write_jsonl(rows_path, [asdict(row) for row in rows])
    learning_result = _export_runtime_learning_rows(
        rows=rows,
        out_dir=out_dir / "runtime_learning_export",
        question_id=question_id,
        queue_path=queue_path,
    )
    premise_queue_result = _export_source_to_bridge_premise_derivation_queue(
        rows=rows,
        out_dir=out_dir / "source_to_bridge_premise_derivation_queue",
        source_queue_path=queue_path,
    )
    verified_adapter_ids = [
        row.adapter_check_id for row in rows if row.adapter_kernel_verified
    ]
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_runtime_dir": str(runtime_dir or ""),
        "source_queue_jsonl": str(queue_path),
        "checks_jsonl": str(rows_path),
        "runtime_learning_rows_jsonl": str(learning_result["runtime_learning_rows_jsonl"]),
        "runtime_learning_export_manifest": str(learning_result["export_manifest_path"]),
        "source_to_bridge_premise_derivation_queue_jsonl": str(
            premise_queue_result["queue_jsonl"]
        ),
        "source_to_bridge_premise_derivation_queue_manifest": str(
            premise_queue_result["manifest_path"]
        ),
        "adapter_candidate_dir": str(candidate_dir),
        "local_lean_requested": bool(local_lean),
        "local_lean_project": str(project_path or ""),
        "local_lean_timeout_seconds": int(lean_timeout),
        "lean_command": list(command),
        "n_work_orders": len(work_orders),
        "n_adapter_check_rows": len(rows),
        "n_local_lean_checked": sum(1 for row in rows if row.local_lean_checked),
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
        "n_adapter_candidate_import_rows": sum(
            1 for row in rows if row.adapter_candidate_imports
        ),
        "n_adapter_unavailable_import_rows": sum(
            1 for row in rows if row.unavailable_import
        ),
        "adapter_unavailable_imports": sorted(
            {
                row.unavailable_import
                for row in rows
                if row.unavailable_import
            }
        ),
        "n_adapter_candidate_evidence_eligible": sum(
            1 for row in rows if row.adapter_candidate_evidence_eligible
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
        "source_theorem_exact_proof_body_gate_open_target_names": sorted(
            {
                target_name
                for row in rows
                for target_name in (
                    row.source_theorem_exact_proof_body_gate_open_target_names
                    or (row.target_theorem_name,)
                )
                if (
                    row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
                    and target_name
                )
            }
        ),
        "n_source_to_bridge_premise_derivation_work_items": sum(
            len(row.source_to_bridge_premise_derivation_work_items) for row in rows
        ),
        "n_kernel_verified_source_to_bridge_premise_derivation_ids": sum(
            len(row.kernel_verified_source_to_bridge_premise_derivation_ids)
            for row in rows
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": [
            premise_id
            for row in rows
            for premise_id in row.kernel_verified_source_to_bridge_premise_derivation_ids
        ],
        "n_source_to_bridge_premise_derivation_queue_rows": int(
            premise_queue_result["n_queue_rows"]
        ),
        "n_adapter_kernel_verified": len(verified_adapter_ids),
        "kernel_verified_source_theorem_proof_body_adapter_ids": verified_adapter_ids,
        "n_source_theorem_kernel_verified": 0,
        "source_theorem_kernel_verified": False,
        "runtime_learning_ready": bool(learning_result["n_learning_rows"]),
        "proof_evidence_status": (
            ADAPTER_KERNEL_VERIFIED_STATUS
            if verified_adapter_ids
            else ADAPTER_PROOF_EVIDENCE_STATUS
        ),
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "boundary": BOUNDARY,
        "rows": [asdict(row) for row in rows],
    }
    manifest_path = out_dir / "source_theorem_proof_body_adapter_proofengineer_bridge_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def _adapter_check_row(
    row: Mapping[str, Any],
    *,
    rank: int,
    candidate_dir: Path,
    default_question_id: str,
    local_lean: bool,
    lean_project: Path | None,
    lean_timeout: int,
    lean_command: tuple[str, ...],
) -> SourceTheoremProofBodyAdapterCheckRow:
    source_work_order_id = str(row.get("source_work_order_id", "") or "").strip()
    work_order_id = str(
        row.get("work_order_id", "")
        or row.get("queue_id", "")
        or source_work_order_id
        or ""
    ).strip()
    target = str(row.get("target_theorem_name", "") or "").strip()
    target_declaration = str(
        row.get("target_lean_declaration", "")
        or _target_declaration_from_provenance(row)
        or target
    ).strip()
    safe_target = _safe_identifier(target_declaration or target or f"adapter_{rank}")
    provided_sketch = str(row.get("lean_statement_sketch", "") or "").strip()
    adapter_declaration = (
        _provided_adapter_declaration(provided_sketch)
        or f"{safe_target}_source_to_bridge_adapter"
    )
    adapter_hash = stable_hash([work_order_id, target, target_declaration, rank])[:16]
    adapter_path = candidate_dir / f"{adapter_declaration}_{adapter_hash}.lean"
    if provided_sketch:
        provided_source = _normalize_adapter_source(provided_sketch)
        provided_source = _inline_verified_adapter_dependency_context(
            provided_source,
            row=row,
        )
        if re.search(rf"\btheorem\s+{re.escape(adapter_declaration)}\b", provided_source):
            source = provided_source
            generation_mode = "formalizer_provided_adapter_candidate"
        else:
            source = _generated_adapter_skeleton(
                adapter_declaration=adapter_declaration,
                row=row,
            )
            generation_mode = "proofengineer_generated_adapter_skeleton"
    else:
        source = _generated_adapter_skeleton(
            adapter_declaration=adapter_declaration,
            row=row,
        )
        generation_mode = "proofengineer_generated_adapter_skeleton"
    adapter_path.write_text(source, encoding="utf-8")

    forbidden_tokens = _forbidden_tokens(source)
    vacuous = _adapter_candidate_vacuous(source)
    unproven_bridge_premise_names = _adapter_unproven_bridge_premise_names(
        source,
        row=row,
        enforce=generation_mode == "formalizer_provided_adapter_candidate",
    )
    adapter_candidate_imports = _lean_import_modules_from_source(source)
    proof_body_goal_excerpt = _str_tuple(row.get("proof_body_goal_excerpt", []))
    proof_body_goal_context = _proof_body_goal_context_from_excerpt(
        proof_body_goal_excerpt
    )
    proof_body_goal_binder_names = _str_tuple(
        proof_body_goal_context.get("binder_names", [])
    )
    proof_body_goal_conclusion = str(
        proof_body_goal_context.get("conclusion", "") or ""
    )
    premise_derivation_work_items = _source_to_bridge_premise_derivation_work_items(
        row,
        proof_body_goal_context=proof_body_goal_context,
    )
    verified_premise_signature_excerpts = (
        _verified_source_to_bridge_premise_derivation_signature_excerpts(row)
    )
    requires_unproven_bridge_premises = bool(unproven_bridge_premise_names)
    evidence_eligible = bool(
        generation_mode == "formalizer_provided_adapter_candidate"
        and not vacuous
        and not forbidden_tokens
        and not requires_unproven_bridge_premises
        and re.search(rf"\btheorem\s+{re.escape(adapter_declaration)}\b", source)
    )
    local_compiled = False
    local_checked = False
    returncode = 0
    diagnostics: tuple[str, ...] = ()
    if local_lean:
        local_checked = True
        if not lean_command:
            local_compiled = False
            returncode = -1
            diagnostics = ("local Lean executable not found",)
        else:
            local_compiled, returncode, diagnostics = _run_local_lean(
                adapter_path,
                lean_command=lean_command,
                lean_project=lean_project,
                timeout_s=lean_timeout,
            )
    failure = _adapter_failure_classification(
        local_lean=local_lean,
        local_compiled=local_compiled,
        evidence_eligible=evidence_eligible,
        vacuous=vacuous,
        requires_unproven_bridge_premises=requires_unproven_bridge_premises,
        forbidden_tokens=forbidden_tokens,
        diagnostics=diagnostics,
    )
    unavailable_import = ""
    if failure == "adapter_lean_import_environment_missing":
        unavailable_import = _unavailable_lean_import_from_diagnostics(diagnostics)
    adapter_verified = bool(local_lean and local_compiled and evidence_eligible)
    check_id = "source_theorem_proof_body_adapter_check:" + stable_hash(
        [work_order_id, str(adapter_path), adapter_verified, failure]
    )[:20]
    provenance = dict(row.get("source_theorem_target_provenance", {}) or {})
    if target_declaration:
        provenance.setdefault("target_lean_declaration", target_declaration)
    return SourceTheoremProofBodyAdapterCheckRow(
        schema_version=1,
        artifact_kind=ADAPTER_ROW_KIND,
        adapter_check_id=check_id,
        work_order_id=work_order_id,
        source_work_order_id=source_work_order_id,
        source_queue_artifact_kind=str(row.get("artifact_kind", "") or ""),
        source_queue_status=str(row.get("runtime_queue_status", "") or ""),
        question_id=str(row.get("question_id", "") or default_question_id or ""),
        question_title=str(row.get("question_title", "") or ""),
        source_formalization_manifest_id=str(
            row.get("source_formalization_manifest_id", "") or ""
        ),
        source_formalizer_packet_id=str(row.get("source_formalizer_packet_id", "") or ""),
        source_formal_target_id=str(row.get("source_formal_target_id", "") or ""),
        target_theorem_name=target,
        target_lean_declaration=target_declaration,
        target_ids=(
            _str_tuple(row.get("target_ids", []))
            or _str_tuple(row.get("target_theorem_goal_ids", []))
            or _str_tuple(target)
        ),
        target_theorem_goal_ids=_str_tuple(row.get("target_theorem_goal_ids", [])),
        source_theorem_target_known=bool(
            row.get("source_theorem_target_known", False)
            or provenance.get("source_theorem_target_known", False)
        ),
        source_theorem_target_provenance=provenance,
        source_candidate_artifact_path=str(
            row.get("source_candidate_artifact_path", "")
            or row.get("proof_body_candidate_artifact_path", "")
            or row.get("candidate_artifact_path", "")
            or ""
        ),
        proof_body_signature_probe_artifact_path=str(
            row.get("proof_body_signature_probe_artifact_path", "")
            or row.get("source_theorem_signature_probe_artifact_path", "")
            or row.get("signature_probe_artifact_path", "")
            or ""
        ),
        source_theorem_signature_probe_artifact_path=str(
            row.get("source_theorem_signature_probe_artifact_path", "")
            or row.get("proof_body_signature_probe_artifact_path", "")
            or row.get("signature_probe_artifact_path", "")
            or ""
        ),
        adapter_candidate_artifact_path=str(adapter_path),
        adapter_declaration_name=adapter_declaration,
        adapter_candidate_imports=adapter_candidate_imports,
        unavailable_import=unavailable_import,
        adapter_generation_mode=generation_mode,
        adapter_candidate_vacuous=vacuous,
        adapter_candidate_requires_unproven_bridge_premises=(
            requires_unproven_bridge_premises
        ),
        unproven_bridge_premise_names=unproven_bridge_premise_names,
        source_to_bridge_premise_derivation_work_items=(
            premise_derivation_work_items
        ),
        kernel_verified_source_to_bridge_premise_derivation_ids=_str_tuple(
            row.get("kernel_verified_source_to_bridge_premise_derivation_ids", [])
        ),
        verified_source_to_bridge_premise_derivation_artifact_paths=_str_tuple(
            row.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
        ),
        verified_source_to_bridge_premise_derivation_declarations=_str_tuple(
            row.get("verified_source_to_bridge_premise_derivation_declarations", [])
        ),
        verified_source_to_bridge_premise_derivation_signature_excerpts=(
            verified_premise_signature_excerpts
        ),
        forbidden_tokens_found=forbidden_tokens,
        adapter_candidate_evidence_eligible=evidence_eligible,
        proof_body_goal_excerpt=proof_body_goal_excerpt,
        proof_body_goal_context=proof_body_goal_context,
        proof_body_goal_binder_names=proof_body_goal_binder_names,
        proof_body_goal_conclusion=proof_body_goal_conclusion,
        proof_body_attempt_summaries=_str_tuple(
            row.get("proof_body_attempt_summaries", [])
        ),
        proof_body_attempt_count=_int_like(row.get("proof_body_attempt_count", 0)),
        proof_body_gate_status=str(row.get("proof_body_gate_status", "") or ""),
        source_theorem_exact_proof_body_reached=bool(
            row.get("source_theorem_exact_proof_body_reached", False)
        ),
        source_theorem_exact_proof_body_gate_open_for_kernel_repair=bool(
            row.get(
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
                False,
            )
        ),
        source_theorem_exact_proof_body_gate_open_target_names=_str_tuple(
            row.get("source_theorem_exact_proof_body_gate_open_target_names", [])
        ),
        proof_body_adapter_required_reasons=_proof_body_adapter_required_reasons(row),
        exact_goal_shape_obligation_id=str(
            row.get("exact_goal_shape_obligation_id", "") or ""
        ),
        exact_goal_shape_obligation=str(
            row.get("exact_goal_shape_obligation", "") or ""
        ),
        target_artifact_kind=str(row.get("target_artifact_kind", "") or ""),
        source_acceptance_gate=str(row.get("acceptance_gate", "") or ""),
        semantic_alignment_constraints=_str_tuple(
            row.get("semantic_alignment_constraints", [])
        ),
        semantic_alignment_blockers=_str_tuple(
            row.get("semantic_alignment_blockers", [])
        ),
        source_theorem_kernel_evidence_eligible=bool(
            row.get("source_theorem_kernel_evidence_eligible", False)
        ),
        kernel_verified_theorem_reduction_closure_target_ids=_str_tuple(
            row.get("kernel_verified_theorem_reduction_closure_target_ids", [])
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
        local_lean_requested=bool(local_lean),
        local_lean_checked=local_checked,
        local_lean_compiled=local_compiled,
        lean_command=lean_command,
        lean_project=str(lean_project or ""),
        lean_timeout=int(lean_timeout),
        returncode=int(returncode),
        diagnostics=diagnostics,
        failure_classification=failure,
        adapter_kernel_verified=adapter_verified,
        source_theorem_kernel_verified=False,
        proof_evidence_status=(
            ADAPTER_KERNEL_VERIFIED_STATUS
            if adapter_verified
            else ADAPTER_PROOF_EVIDENCE_STATUS
        ),
        proof_evidence_boundary=KERNEL_PROOF_BOUNDARY,
        ok=adapter_verified,
    )


def _generated_adapter_skeleton(
    *,
    adapter_declaration: str,
    row: Mapping[str, Any],
) -> str:
    target = str(row.get("target_theorem_name", "") or "").strip()
    reasons = _proof_body_adapter_required_reasons(row)
    goal_excerpt = _str_tuple(row.get("proof_body_goal_excerpt", []))[:12]
    goal_context = _proof_body_goal_context_from_excerpt(
        _str_tuple(row.get("proof_body_goal_excerpt", []))
    )
    goal_binder_names = _str_tuple(goal_context.get("binder_names", []))[:24]
    goal_conclusion = str(goal_context.get("conclusion", "") or "").strip()
    attempt_summaries = _str_tuple(row.get("proof_body_attempt_summaries", []))[:12]
    attempt_count = _int_like(row.get("proof_body_attempt_count", 0))
    proof_body_gate_status = str(row.get("proof_body_gate_status", "") or "").strip()
    proof_body_gate_open = bool(
        row.get("source_theorem_exact_proof_body_gate_open_for_kernel_repair", False)
    )
    proof_body_gate_open_targets = _str_tuple(
        row.get("source_theorem_exact_proof_body_gate_open_target_names", [])
    )[:12]
    source_candidate_artifact_path = str(
        row.get("source_candidate_artifact_path", "")
        or row.get("proof_body_candidate_artifact_path", "")
        or row.get("candidate_artifact_path", "")
        or ""
    ).strip()
    proof_body_signature_probe_artifact_path = str(
        row.get("proof_body_signature_probe_artifact_path", "")
        or row.get("source_theorem_signature_probe_artifact_path", "")
        or row.get("signature_probe_artifact_path", "")
        or ""
    ).strip()
    semantic_blockers = _str_tuple(row.get("semantic_alignment_blockers", []))[:8]
    source_kernel_eligible_raw = row.get("source_theorem_kernel_evidence_eligible")
    source_kernel_eligible = bool(source_kernel_eligible_raw)
    exact_goal_shape_obligation_id = str(
        row.get("exact_goal_shape_obligation_id", "") or ""
    ).strip()
    exact_goal_shape_obligation = str(
        row.get("exact_goal_shape_obligation", "") or ""
    ).strip()
    source_queue_status = str(row.get("runtime_queue_status", "") or "").strip()
    target_artifact_kind = str(row.get("target_artifact_kind", "") or "").strip()
    source_acceptance_gate = str(row.get("acceptance_gate", "") or "").strip()
    closure_target_ids = _str_tuple(
        row.get("kernel_verified_theorem_reduction_closure_target_ids", [])
    )[:12]
    closure_declarations = _str_tuple(
        row.get("kernel_verified_theorem_reduction_closure_declarations", [])
    )[:12]
    closure_artifact_paths = _str_tuple(
        row.get("verified_theorem_reduction_closure_artifact_paths", [])
    )[:12]
    semantic_support_ids = _str_tuple(
        row.get("kernel_verified_source_theorem_semantic_support_obligation_ids", [])
    )[:12]
    verified_premise_derivation_ids = _str_tuple(
        row.get("kernel_verified_source_to_bridge_premise_derivation_ids", [])
    )[:12]
    verified_premise_derivation_artifact_paths = _str_tuple(
        row.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
    )[:12]
    verified_premise_derivation_declarations = _str_tuple(
        row.get("verified_source_to_bridge_premise_derivation_declarations", [])
    )[:12]
    verified_premise_derivation_signature_excerpts = (
        _verified_source_to_bridge_premise_derivation_signature_excerpts(row)[:6]
    )
    premise_work_items = _source_to_bridge_premise_derivation_work_items(
        row,
        proof_body_goal_context=goal_context,
    )[:12]
    premise_target_rows = _adapter_premise_target_rows(premise_work_items)
    premise_target_comment = "\n".join(
        "\n".join(
            line
            for line in (
                (
                    "-- source-to-bridge premise target: "
                    + _sanitize_comment_text(target_row["premise_name"])
                ),
                (
                    "-- premise target type: "
                    + _sanitize_comment_text(target_row["premise_target_type"])
                ),
                (
                    "-- premise target source: "
                    + _sanitize_comment_text(target_row["premise_target_source"])
                ),
            )
            if line
        )
        for target_row in premise_target_rows
    )
    premise_binder_lines = "\n".join(
        "    "
        f"({_safe_identifier(target_row['premise_name'])} : "
        f"{target_row['premise_target_type']})"
        for target_row in premise_target_rows
    )
    single_premise_target = (
        premise_target_rows[0]["premise_target_type"]
        if len(premise_target_rows) == 1
        else ""
    )
    adapter_header = (
        f"theorem {adapter_declaration}\n"
        "    (source_hypotheses : Prop)\n"
        "    (hsource : source_hypotheses)\n"
    )
    if len(premise_target_rows) != 1:
        adapter_header += "    (bridge_premises : Prop)\n"
    if premise_binder_lines:
        adapter_header += f"{premise_binder_lines}\n"
    adapter_conclusion = single_premise_target or "bridge_premises"
    reason_comment = "\n".join(
        f"-- reason: {_sanitize_comment_text(reason)}" for reason in reasons
    )
    goal_comment = "\n".join(
        f"-- goal: {_sanitize_comment_text(line)}" for line in goal_excerpt
    )
    goal_binder_comment = "\n".join(
        f"-- proof-body goal binder: {_sanitize_comment_text(name)}"
        for name in goal_binder_names
    )
    goal_conclusion_comment = (
        "-- proof-body goal conclusion: " + _sanitize_comment_text(goal_conclusion)
        if goal_conclusion
        else ""
    )
    attempt_comment = "\n".join(
        f"-- proof-body attempt: {_sanitize_comment_text(line)}"
        for line in attempt_summaries
    )
    attempt_count_comment = (
        f"-- proof-body attempt count: {attempt_count}" if attempt_count else ""
    )
    proof_body_gate_status_comment = (
        f"-- proof-body gate status: {_sanitize_comment_text(proof_body_gate_status)}"
        if proof_body_gate_status
        else ""
    )
    proof_body_gate_open_comment = (
        "-- exact source proof-body gate open for kernel repair: "
        + ("true" if proof_body_gate_open else "false")
    )
    proof_body_gate_open_target_comment = "\n".join(
        f"-- exact source proof-body gate-open target: {_sanitize_comment_text(line)}"
        for line in proof_body_gate_open_targets
    )
    source_kernel_eligible_comment = (
        (
            "-- source theorem kernel evidence eligible before adapter: "
            + ("true" if source_kernel_eligible else "false")
        )
        if source_kernel_eligible_raw is not None
        else ""
    )
    semantic_blocker_comment = "\n".join(
        f"-- semantic alignment blocker: {_sanitize_comment_text(line)}"
        for line in semantic_blockers
    )
    closure_comment = "\n".join(
        f"-- verified reduction/closure target id: {_sanitize_comment_text(line)}"
        for line in closure_target_ids
    )
    closure_declaration_comment = "\n".join(
        f"-- verified reduction/closure Lean declaration: {_sanitize_comment_text(line)}"
        for line in closure_declarations
    )
    closure_artifact_comment = "\n".join(
        f"-- verified reduction/closure artifact: {_sanitize_comment_text(line)}"
        for line in closure_artifact_paths
    )
    semantic_support_comment = "\n".join(
        f"-- verified semantic support obligation id: {_sanitize_comment_text(line)}"
        for line in semantic_support_ids
    )
    verified_premise_derivation_id_comment = "\n".join(
        f"-- verified source-to-bridge premise derivation id: {_sanitize_comment_text(line)}"
        for line in verified_premise_derivation_ids
    )
    verified_premise_derivation_artifact_comment = "\n".join(
        f"-- verified source-to-bridge premise derivation artifact: {_sanitize_comment_text(line)}"
        for line in verified_premise_derivation_artifact_paths
    )
    verified_premise_derivation_declaration_comment = "\n".join(
        f"-- verified source-to-bridge premise derivation declaration: {_sanitize_comment_text(line)}"
        for line in verified_premise_derivation_declarations
    )
    verified_premise_derivation_signature_comment = "\n".join(
        _lean_comment_block(
            "verified source-to-bridge premise derivation signature excerpt",
            excerpt,
        )
        for excerpt in verified_premise_derivation_signature_excerpts
    )
    premise_work_item_comment = "\n".join(
        "\n".join(
            line
            for line in (
                (
                    "-- source-to-bridge premise work item: "
                    + _sanitize_comment_text(str(item.get("premise_name", "") or ""))
                    if item.get("premise_name")
                    else ""
                ),
                (
                    "-- required derivation: "
                    + _sanitize_comment_text(
                        str(item.get("required_derivation", "") or "")
                    )
                    if item.get("required_derivation")
                    else ""
                ),
                (
                    "-- forbidden as adapter assumption: true"
                    if item.get("forbidden_as_adapter_assumption")
                    else ""
                ),
            )
            if line
        )
        for item in premise_work_items
    )
    target_comment = (
        f"-- target source theorem: {_sanitize_comment_text(target)}"
        if target
        else ""
    )
    source_candidate_comment = (
        "-- source proof-body candidate artifact: "
        + _sanitize_comment_text(source_candidate_artifact_path)
        if source_candidate_artifact_path
        else ""
    )
    signature_probe_comment = (
        "-- source theorem signature probe artifact: "
        + _sanitize_comment_text(proof_body_signature_probe_artifact_path)
        if proof_body_signature_probe_artifact_path
        else ""
    )
    exact_goal_shape_comment = "\n".join(
        line
        for line in (
            (
                "-- exact goal-shape obligation id: "
                + _sanitize_comment_text(exact_goal_shape_obligation_id)
                if exact_goal_shape_obligation_id
                else ""
            ),
            (
                "-- exact goal-shape obligation: "
                + _sanitize_comment_text(exact_goal_shape_obligation)
                if exact_goal_shape_obligation
                else ""
            ),
            (
                "-- source queue status: "
                + _sanitize_comment_text(source_queue_status)
                if source_queue_status
                else ""
            ),
            (
                "-- target adapter artifact kind: "
                + _sanitize_comment_text(target_artifact_kind)
                if target_artifact_kind
                else ""
            ),
            (
                "-- source acceptance gate: "
                + _sanitize_comment_text(source_acceptance_gate)
                if source_acceptance_gate
                else ""
            ),
        )
        if line
    )
    return (
        "namespace AIStatisticianSourceTheoremProofBodyAdapter\n\n"
        "/-\n"
        "This is a generated adapter obligation skeleton, not proof evidence.\n"
        "It should be replaced by a theorem deriving verified bridge premises from\n"
        "the exact source theorem hypotheses before retrying the source theorem proof body.\n"
        "-/\n"
        f"{target_comment}\n"
        f"{source_candidate_comment}\n"
        f"{signature_probe_comment}\n"
        f"{exact_goal_shape_comment}\n"
        f"{reason_comment}\n"
        f"{closure_comment}\n"
        f"{closure_declaration_comment}\n"
        f"{closure_artifact_comment}\n"
        f"{semantic_support_comment}\n"
        f"{verified_premise_derivation_id_comment}\n"
        f"{verified_premise_derivation_artifact_comment}\n"
        f"{verified_premise_derivation_declaration_comment}\n"
        f"{verified_premise_derivation_signature_comment}\n"
        f"{premise_work_item_comment}\n"
        f"{premise_target_comment}\n"
        f"{goal_comment}\n"
        f"{goal_binder_comment}\n"
        f"{goal_conclusion_comment}\n"
        f"{attempt_comment}\n"
        f"{attempt_count_comment}\n"
        f"{proof_body_gate_status_comment}\n"
        f"{proof_body_gate_open_comment}\n"
        f"{proof_body_gate_open_target_comment}\n"
        f"{source_kernel_eligible_comment}\n"
        f"{semantic_blocker_comment}\n"
        "-- adapter task: materialize/import the missing dependency context above,\n"
        "-- then derive the bridge or reduction premise from exact source-level hypotheses.\n"
        "-- Generated premise binders are target scaffolds for downstream premise derivation, not proof evidence.\n"
        f"{adapter_header}"
        f"    : {adapter_conclusion} := by\n"
        "  -- ProofEngineer must derive bridge premises from the exact source hypotheses.\n"
        "  fail_if_success trivial\n\n"
        "end AIStatisticianSourceTheoremProofBodyAdapter\n"
    )


def _adapter_required_reasons_from_exact_goal_shape(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    obligation_id = str(row.get("exact_goal_shape_obligation_id", "") or "").strip()
    obligation_ids = set(_str_tuple(row.get("exact_goal_shape_obligation_ids", [])))
    if (
        obligation_id == "source_to_bridge_adapter_goal_shape_mismatch"
        or "source_to_bridge_adapter_goal_shape_mismatch" in obligation_ids
    ):
        return (
            "verified adapter or closure dependencies do not directly match the "
            "exact source theorem goal shape",
            "derive bridge premises from exact source-theorem assumptions before "
            "retrying the exact source proof body",
        )
    if obligation_id:
        return (
            f"exact goal-shape obligation requires adapter repair: {obligation_id}",
        )
    return ()


def _proof_body_adapter_required_reasons(row: Mapping[str, Any]) -> tuple[str, ...]:
    exact_reasons = _adapter_required_reasons_from_exact_goal_shape(row)
    existing_reasons = _str_tuple(row.get("proof_body_adapter_required_reasons", []))
    return tuple(dict.fromkeys((*exact_reasons, *existing_reasons)))


def _source_to_bridge_premise_derivation_work_items(
    row: Mapping[str, Any],
    *,
    proof_body_goal_context: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    goal_context = dict(
        proof_body_goal_context
        or _proof_body_goal_context_from_excerpt(
            _str_tuple(row.get("proof_body_goal_excerpt", []))
        )
    )
    goal_binder_names = list(_str_tuple(goal_context.get("binder_names", [])))
    goal_conclusion = str(goal_context.get("conclusion", "") or "").strip()
    items: list[dict[str, Any]] = []
    for item in row.get("source_to_bridge_premise_derivation_work_items", []) or []:
        if not isinstance(item, Mapping):
            continue
        premise_name = str(item.get("premise_name", "") or "").strip()
        if not premise_name:
            continue
        normalized = dict(item)
        normalized["premise_name"] = premise_name
        normalized["forbidden_as_adapter_assumption"] = bool(
            item.get("forbidden_as_adapter_assumption", False)
        )
        if "proof_evidence_status" not in normalized:
            normalized["proof_evidence_status"] = "WORK_ITEM_NOT_PROOF_EVIDENCE"
        if goal_context and "proof_body_goal_context" not in normalized:
            normalized["proof_body_goal_context"] = goal_context
        if goal_binder_names and "proof_body_goal_binder_names" not in normalized:
            normalized["proof_body_goal_binder_names"] = goal_binder_names
        if goal_conclusion and "proof_body_goal_conclusion" not in normalized:
            normalized["proof_body_goal_conclusion"] = goal_conclusion
        items.append(normalized)
    if items or not _requires_exact_source_to_bridge_derivation(row):
        return _attach_premise_target_metadata(
            items,
            row=row,
            goal_context=goal_context,
        )
    for premise_name in _bridge_premise_names_from_context(row):
        items.append(
            {
                "schema_version": 1,
                "artifact_kind": "SourceToBridgePremiseDerivationWorkItem",
                "premise_name": premise_name,
                "forbidden_as_adapter_assumption": True,
                "required_derivation": (
                    f"derive {premise_name} from the exact source theorem "
                    "hypotheses; do not take it as a new source-to-bridge "
                    "adapter binder assumption"
                ),
                "exact_goal_shape_obligation_ids": list(
                    row.get("exact_goal_shape_obligation_ids", []) or []
                ),
                "kernel_verified_theorem_reduction_closure_declarations": list(
                    row.get(
                        "kernel_verified_theorem_reduction_closure_declarations",
                        [],
                    )
                    or []
                ),
                "verified_theorem_reduction_closure_artifact_paths": list(
                    row.get("verified_theorem_reduction_closure_artifact_paths", [])
                    or []
                ),
                "acceptance_gate": (
                    "AXLE/local Lean kernel verifies a source-to-bridge adapter "
                    f"where {premise_name} is derived from exact source hypotheses, "
                    "not introduced as an adapter premise. The full source theorem "
                    "remains unproved until the exact theorem is rerun and kernel "
                    "verified."
                ),
                "proof_body_goal_context": goal_context,
                "proof_body_goal_binder_names": goal_binder_names,
                "proof_body_goal_conclusion": goal_conclusion,
                "proof_evidence_status": "WORK_ITEM_NOT_PROOF_EVIDENCE",
            }
        )
    return _attach_premise_target_metadata(
        items,
        row=row,
        goal_context=goal_context,
    )


def _attach_premise_target_metadata(
    items: list[dict[str, Any]],
    *,
    row: Mapping[str, Any],
    goal_context: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    enriched: list[dict[str, Any]] = []
    for item in items:
        premise_name = str(item.get("premise_name", "") or "").strip()
        if not premise_name:
            continue
        target_type, target_source = _source_to_bridge_premise_target_type(
            item=item,
            row=row,
            premise_name=premise_name,
            goal_context=goal_context,
            n_items=len(items),
        )
        source_conclusion = _source_theorem_conclusion_from_row(row)
        proof_body_goal_conclusion = str(
            goal_context.get("conclusion", "") or ""
        ).strip()
        target_alignment_status = _premise_target_alignment_status(
            proof_body_goal_conclusion=proof_body_goal_conclusion,
            source_theorem_conclusion=source_conclusion,
            target_source=target_source,
        )
        payload = dict(item)
        payload.setdefault("premise_target_type", target_type)
        payload.setdefault("source_to_bridge_premise_target_type", target_type)
        payload.setdefault("premise_target_source", target_source)
        if source_conclusion:
            payload.setdefault("source_theorem_signature_conclusion", source_conclusion)
        payload.setdefault(
            "proof_body_goal_target_alignment_status",
            target_alignment_status,
        )
        enriched.append(payload)
    return tuple(enriched)


def _source_to_bridge_premise_target_type(
    *,
    item: Mapping[str, Any],
    row: Mapping[str, Any],
    premise_name: str,
    goal_context: Mapping[str, Any],
    n_items: int,
) -> tuple[str, str]:
    for key in (
        "premise_target_type",
        "source_to_bridge_premise_target_type",
        "target_type",
        "lean_target_type",
        "premise_type",
    ):
        value = str(item.get(key, "") or "").strip()
        if value:
            return value, "explicit_work_item"
    context_target = _bridge_premise_target_type_from_context(
        row,
        premise_name=premise_name,
    )
    if context_target:
        return context_target, "verified_closure_signature"
    goal_conclusion = str(goal_context.get("conclusion", "") or "").strip()
    source_conclusion = _source_theorem_conclusion_from_row(row)
    if n_items == 1 and _looks_like_complete_premise_target_type(goal_conclusion):
        if source_conclusion and not _same_lean_target_type(
            goal_conclusion,
            source_conclusion,
        ):
            return source_conclusion, "source_theorem_signature_conclusion"
        return goal_conclusion, "proof_body_goal_conclusion"
    if _looks_like_complete_premise_target_type(source_conclusion):
        return source_conclusion, "source_theorem_signature_conclusion"
    return "Prop", "opaque_prop_fallback"


def _source_theorem_conclusion_from_row(row: Mapping[str, Any]) -> str:
    for key in (
        "source_theorem_conclusion",
        "source_theorem_signature_conclusion",
        "target_theorem_conclusion",
    ):
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    target_declaration = str(
        row.get("target_lean_declaration", "")
        or _target_declaration_from_provenance(row)
        or row.get("target_theorem_name", "")
        or ""
    ).strip()
    artifact_paths = (
        str(row.get("source_candidate_artifact_path", "") or ""),
        str(row.get("proof_body_candidate_artifact_path", "") or ""),
        str(row.get("candidate_artifact_path", "") or ""),
        str(row.get("source_theorem_signature_probe_artifact_path", "") or ""),
        str(row.get("proof_body_signature_probe_artifact_path", "") or ""),
        str(row.get("signature_probe_artifact_path", "") or ""),
    )
    for artifact_path in artifact_paths:
        excerpt = _lean_declaration_signature_excerpt_from_artifact_path(
            artifact_path,
            declaration=target_declaration,
        )
        conclusion = _lean_signature_conclusion_from_excerpt(excerpt)
        if conclusion:
            return conclusion
    return ""


def _lean_signature_conclusion_from_excerpt(excerpt: str) -> str:
    text = " ".join(
        line.strip() for line in str(excerpt or "").splitlines() if line.strip()
    )
    if not text:
        return ""
    colon_index = _declaration_type_colon_index(text)
    if colon_index < 0:
        return ""
    conclusion = text[colon_index + 1 :].strip()
    return conclusion[:-1].rstrip() if conclusion.endswith(":") else conclusion


def _declaration_type_colon_index(text: str) -> int:
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    for index, char in enumerate(str(text or "")):
        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth:
            paren_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]" and bracket_depth:
            bracket_depth -= 1
        elif char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth:
            brace_depth -= 1
        elif (
            char == ":"
            and paren_depth == 0
            and bracket_depth == 0
            and brace_depth == 0
        ):
            return index
    return -1


def _same_lean_target_type(left: str, right: str) -> bool:
    return _normalize_lean_target_type(left) == _normalize_lean_target_type(right)


def _normalize_lean_target_type(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _premise_target_alignment_status(
    *,
    proof_body_goal_conclusion: str,
    source_theorem_conclusion: str,
    target_source: str,
) -> str:
    goal = str(proof_body_goal_conclusion or "").strip()
    source = str(source_theorem_conclusion or "").strip()
    if not goal or not source:
        return "PREMISE_TARGET_ALIGNMENT_NOT_CHECKED"
    if _same_lean_target_type(goal, source):
        return "PROOF_BODY_GOAL_MATCHES_SOURCE_THEOREM_CONCLUSION"
    if target_source == "source_theorem_signature_conclusion":
        return "PROOF_BODY_GOAL_DIFFERS_FROM_SOURCE_THEOREM_CONCLUSION_SOURCE_CONCLUSION_USED"
    return "PROOF_BODY_GOAL_DIFFERS_FROM_SOURCE_THEOREM_CONCLUSION"


def _adapter_premise_target_rows(
    premise_work_items: tuple[dict[str, Any], ...],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in premise_work_items:
        premise_name = str(item.get("premise_name", "") or "").strip()
        premise_target_type = str(item.get("premise_target_type", "") or "").strip()
        if not premise_name or not premise_target_type:
            continue
        rows.append(
            {
                "premise_name": premise_name,
                "premise_target_type": premise_target_type,
                "premise_target_source": str(
                    item.get("premise_target_source", "") or ""
                ).strip(),
            }
        )
    return rows


def _looks_like_complete_premise_target_type(target: str) -> bool:
    text = str(target or "").strip()
    if not text:
        return False
    if text.endswith(("∧", "∨", "→", "↔", ",", ":=", "=>")):
        return False
    balance = 0
    for char in text:
        if char == "(":
            balance += 1
        elif char == ")":
            balance -= 1
        if balance < 0:
            return False
    return balance == 0


def _proof_body_goal_context_from_excerpt(
    proof_body_goal_excerpt: tuple[str, ...] | list[str],
) -> dict[str, Any]:
    raw_lines = [
        str(line).strip()
        for line in proof_body_goal_excerpt or []
        if str(line or "").strip()
    ]
    hypothesis_rows: list[dict[str, Any]] = []
    conclusion_lines: list[str] = []
    current: dict[str, Any] | None = None
    collecting_conclusion = False
    for line in raw_lines:
        stripped = line.strip()
        if stripped.startswith("⊢"):
            if current is not None:
                hypothesis_rows.append(current)
                current = None
            collecting_conclusion = True
            conclusion_lines.append(stripped[1:].strip())
            continue
        binder = _proof_body_goal_binder_from_line(stripped)
        if binder is not None:
            if current is not None:
                hypothesis_rows.append(current)
            collecting_conclusion = False
            current = binder
            continue
        if collecting_conclusion:
            if _looks_like_proof_body_diagnostic_line(stripped):
                collecting_conclusion = False
                continue
            conclusion_lines.append(stripped)
            continue
        if current is not None and _looks_like_lean_goal_continuation(stripped):
            current["binder_type"] = " ".join(
                part
                for part in (
                    str(current.get("binder_type", "") or "").strip(),
                    stripped,
                )
                if part
            )
            current["raw_lines"].append(stripped)
    if current is not None:
        hypothesis_rows.append(current)
    binder_names = [
        str(row.get("binder_name", "") or "")
        for row in hypothesis_rows
        if str(row.get("binder_name", "") or "").strip()
    ]
    conclusion = " ".join(line for line in conclusion_lines if line).strip()
    return {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyGoalContext",
        "binder_names": list(dict.fromkeys(binder_names)),
        "hypothesis_rows": hypothesis_rows[:32],
        "conclusion": conclusion,
        "raw_excerpt": raw_lines[:32],
        "proof_evidence_status": "PROOF_BODY_GOAL_CONTEXT_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _proof_body_goal_binder_from_line(line: str) -> dict[str, Any] | None:
    if not line or _looks_like_proof_body_diagnostic_line(line):
        return None
    match = re.match(r"^\s*([A-Za-z_][^\s:]*?)\s*:\s*(.*)$", line)
    if not match:
        return None
    binder_name = match.group(1).strip()
    binder_type = match.group(2).strip()
    if not binder_name or binder_name in {"theorem", "lemma", "def"}:
        return None
    return {
        "binder_name": binder_name,
        "binder_type": binder_type,
        "raw_lines": [line],
    }


def _looks_like_lean_goal_continuation(line: str) -> bool:
    if not line or _looks_like_proof_body_diagnostic_line(line):
        return False
    if re.match(r"^\d+:", line):
        return False
    if "/" in line and ".lean:" in line:
        return False
    return bool(
        line.startswith(("∀", "∃", "(", ")", "→", "↔", "MeasureTheory.", "ENNReal."))
        or line[:1].islower()
        or line[:1].isupper()
    )


def _looks_like_proof_body_diagnostic_line(line: str) -> bool:
    if not line or line.startswith(("error:", "warning:", "--")):
        return True
    if re.match(r"^\d+:", line):
        return True
    return bool(".lean:" in line or "returncode=" in line or "compiled=" in line)


def _bridge_premise_names_from_context(row: Mapping[str, Any]) -> tuple[str, ...]:
    context = _bridge_premise_context_text(row)
    names = [
        name
        for name in BRIDGE_PREMISE_BINDER_NAMES
        if re.search(rf"\(\s*{re.escape(name)}\b", context)
    ]
    return tuple(dict.fromkeys(names))


def _bridge_premise_target_type_from_context(
    row: Mapping[str, Any],
    *,
    premise_name: str,
) -> str:
    return _named_lean_binder_type(
        _bridge_premise_context_text(row),
        binder_name=premise_name,
    )


def _bridge_premise_context_text(row: Mapping[str, Any]) -> str:
    context_fragments = [
        *[
            str(value)
            for value in row.get(
                "kernel_verified_theorem_reduction_closure_signature_excerpts",
                [],
            )
            or []
        ],
        str(row.get("exact_goal_shape_obligation", "") or ""),
        str(row.get("acceptance_gate", "") or ""),
    ]
    dependency_paths = [
        *_str_tuple(row.get("verified_theorem_reduction_closure_artifact_paths", [])),
        *_str_tuple(
            row.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
        ),
    ]
    for raw_path in tuple(dict.fromkeys(dependency_paths))[:6]:
        path_text = str(raw_path or "").strip()
        if not path_text.endswith(".lean"):
            continue
        try:
            context_fragments.append(Path(path_text).expanduser().read_text(encoding="utf-8"))
        except OSError:
            continue
    return "\n".join(context_fragments)


def _named_lean_binder_type(source: str, *, binder_name: str) -> str:
    name = str(binder_name or "").strip()
    if not name:
        return ""
    pattern = re.compile(rf"\(\s*{re.escape(name)}\b\s*:")
    for match in pattern.finditer(source):
        start = match.start()
        depth = 0
        end = -1
        for index, char in enumerate(source[start:], start=start):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = index
                    break
        if end < 0:
            continue
        content = source[start + 1 : end]
        _, _, target_type = content.partition(":")
        target = re.sub(r"\s+", " ", target_type).strip()
        if target:
            return target
    return ""


def _normalize_adapter_source(source: str) -> str:
    if "import " not in source:
        return source.rstrip() + "\n"
    return source.rstrip() + "\n"


def _verified_source_to_bridge_premise_derivation_signature_excerpts(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    existing = _str_tuple(
        row.get("verified_source_to_bridge_premise_derivation_signature_excerpts", [])
    )
    if existing:
        return existing
    return tuple(
        _lean_declaration_signature_excerpts_from_artifacts(
            artifact_paths=list(
                _str_tuple(
                    row.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
                )
            ),
            declarations=list(
                _str_tuple(row.get("verified_source_to_bridge_premise_derivation_declarations", []))
            ),
        )
    )


def _lean_declaration_signature_excerpts_from_artifacts(
    *,
    artifact_paths: list[str],
    declarations: list[str],
    max_artifacts: int = 3,
) -> list[str]:
    excerpts: list[str] = []
    for index, artifact_path in enumerate(artifact_paths[:max_artifacts]):
        declaration = declarations[index] if index < len(declarations) else ""
        excerpt = _lean_declaration_signature_excerpt_from_artifact_path(
            artifact_path,
            declaration=declaration,
        )
        if excerpt and excerpt not in excerpts:
            excerpts.append(excerpt)
    return excerpts


def _lean_declaration_signature_excerpt_from_artifact_path(
    artifact_path: str,
    *,
    declaration: str = "",
    max_lines: int = 32,
    max_chars: int = 1600,
) -> str:
    path_text = str(artifact_path or "").strip()
    if not path_text or not path_text.endswith(".lean"):
        return ""
    try:
        text = Path(path_text).expanduser().read_text(encoding="utf-8")
    except OSError:
        return ""
    wanted = str(declaration or "").strip()
    pattern = (
        rf"^\s*(?:noncomputable\s+)?(?:private\s+)?(?:theorem|lemma|def|abbrev)\s+"
        rf"{re.escape(wanted)}\b"
        if wanted
        else r"^\s*(?:noncomputable\s+)?(?:private\s+)?(?:theorem|lemma|def|abbrev)\s+"
    )
    lines = text.splitlines()
    start = -1
    for index, line in enumerate(lines):
        if re.search(pattern, line):
            start = index
            break
    if start < 0:
        return ""
    excerpt_lines: list[str] = []
    for line in lines[start : start + max_lines]:
        if ":=" in line:
            before, _sep, _after = line.partition(":=")
            excerpt_lines.append(before.rstrip())
            break
        excerpt_lines.append(line.rstrip())
    return "\n".join(excerpt_lines).strip()[:max_chars]


def _lean_comment_block(label: str, excerpt: str) -> str:
    lines = [_sanitize_comment_text(line) for line in str(excerpt or "").splitlines()]
    lines = [line for line in lines if line.strip()]
    if not lines:
        return ""
    return "\n".join([f"-- {label}:", *[f"--   {line}" for line in lines[:16]]])


def _provided_adapter_declaration(source: str) -> str:
    match = re.search(r"\btheorem\s+([A-Za-z_][A-Za-z0-9_'.]*)\b", source or "")
    if not match:
        return ""
    declaration = match.group(1)
    if "adapter" not in declaration.lower():
        return ""
    return _safe_identifier(declaration)


def _inline_verified_adapter_dependency_context(
    source: str,
    *,
    row: Mapping[str, Any],
) -> str:
    dependency_sources: list[str] = []
    dependency_paths = [
        *_str_tuple(row.get("verified_theorem_reduction_closure_artifact_paths", [])),
        *_str_tuple(
            row.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
        ),
    ]
    for raw_path in tuple(dict.fromkeys(dependency_paths))[:6]:
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
    import_block = "\n".join(imports)
    body_block = "\n\n".join(bodies).rstrip()
    if import_block and body_block:
        return import_block + "\n\n" + body_block + "\n"
    if import_block:
        return import_block + "\n"
    return body_block + "\n"


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


def _adapter_candidate_vacuous(source: str) -> bool:
    text = re.sub(r"\s+", " ", _strip_lean_comments_for_vacuity(source))
    if re.search(r"theorem\s+\w+[^:]*:\s*True\s*:=", text):
        return True
    if "exact True.intro" in text:
        return True
    return False


def _adapter_unproven_bridge_premise_names(
    source: str,
    *,
    row: Mapping[str, Any],
    enforce: bool = True,
) -> tuple[str, ...]:
    if not enforce:
        return ()
    if not _requires_exact_source_to_bridge_derivation(row):
        return ()
    header = _lean_theorem_header_without_comments(source)
    names = [
        name
        for name in BRIDGE_PREMISE_BINDER_NAMES
        if re.search(rf"\(\s*{re.escape(name)}\b", header)
    ]
    return tuple(dict.fromkeys(names))


def _requires_exact_source_to_bridge_derivation(row: Mapping[str, Any]) -> bool:
    obligation_id = str(row.get("exact_goal_shape_obligation_id", "") or "").strip()
    obligation_ids = set(_str_tuple(row.get("exact_goal_shape_obligation_ids", [])))
    target_artifact_kind = str(row.get("target_artifact_kind", "") or "").strip()
    source_queue_status = str(row.get("runtime_queue_status", "") or "").strip()
    return (
        obligation_id == "source_to_bridge_adapter_goal_shape_mismatch"
        or "source_to_bridge_adapter_goal_shape_mismatch" in obligation_ids
        or target_artifact_kind == "source_theorem_exact_proof_body_adapter_instantiation"
        or source_queue_status == "PENDING_SOURCE_TO_BRIDGE_ADAPTER_INSTANTIATION"
    )


def _lean_theorem_header_without_comments(source: str) -> str:
    text = _strip_lean_comments_for_vacuity(source)
    theorem_match = re.search(r"\btheorem\s+\w+\b", text)
    if not theorem_match:
        return text
    theorem_text = text[theorem_match.start() :]
    proof_match = re.search(r"\s:=\s*by\b|\s:=\s*", theorem_text)
    if proof_match:
        theorem_text = theorem_text[: proof_match.start()]
    return theorem_text


def _strip_lean_comments_for_vacuity(source: str) -> str:
    without_block_comments = re.sub(r"/-.*?-/", "", source, flags=re.DOTALL)
    return "\n".join(
        line.split("--", 1)[0] for line in without_block_comments.splitlines()
    )


def _forbidden_tokens(source: str) -> tuple[str, ...]:
    tokens = []
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


def _lean_import_modules_from_source(source: str) -> tuple[str, ...]:
    imports: list[str] = []
    seen: set[str] = set()
    for line in source.splitlines()[:80]:
        match = re.match(r"^\s*import\s+(?P<modules>.+?)\s*$", line)
        if not match:
            continue
        for module in match.group("modules").split():
            module = module.strip()
            if module and module not in seen:
                seen.add(module)
                imports.append(module)
    return tuple(imports[:8])


def _unavailable_lean_import_from_diagnostics(diagnostics: tuple[str, ...]) -> str:
    text = "\n".join(str(item or "") for item in diagnostics)
    patterns = (
        r"of module\s+(?P<module>[A-Za-z0-9_'.]+)\s+does not exist",
        r"unknown module prefix\s+'(?P<module>[A-Za-z0-9_'.]+)'",
        r"No directory\s+'(?P<module>[A-Za-z0-9_'.]+)'",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group("module").strip("'\"")
    return ""


def _adapter_failure_classification(
    *,
    local_lean: bool,
    local_compiled: bool,
    evidence_eligible: bool,
    vacuous: bool,
    requires_unproven_bridge_premises: bool,
    forbidden_tokens: tuple[str, ...],
    diagnostics: tuple[str, ...],
) -> str:
    if forbidden_tokens:
        return "adapter_candidate_forbidden_placeholder_token"
    if vacuous:
        return "adapter_candidate_vacuous"
    if requires_unproven_bridge_premises:
        return "adapter_candidate_requires_unproven_bridge_premises"
    if not evidence_eligible:
        return "adapter_candidate_not_evidence_eligible"
    if not local_lean:
        return "adapter_candidate_not_checked"
    if local_compiled:
        return ""
    text = "\n".join(diagnostics).lower()
    if "timed out" in text or "timeout" in text:
        return "adapter_local_lean_timeout"
    if "unknown module prefix" in text or ".olean" in text:
        return "adapter_lean_import_environment_missing"
    if "unknown identifier" in text or "unknown constant" in text:
        return "adapter_formal_environment_symbol_missing"
    if "unsolved goals" in text:
        return "adapter_proof_incomplete"
    if diagnostics:
        return "adapter_local_lean_failed"
    return "adapter_local_lean_not_run"


def _export_runtime_learning_rows(
    *,
    rows: list[SourceTheoremProofBodyAdapterCheckRow],
    out_dir: Path,
    question_id: str,
    queue_path: Path,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    learning_rows: list[dict[str, Any]] = []
    for row in rows:
        payload = asdict(row)
        learning_rows.append(
            {
                "schema_version": 1,
                "question_id": row.question_id or str(question_id or ""),
                "question_title": row.question_title,
                "learning_task": "source_theorem_proof_body_adapter_feedback",
                "target_theorem_name": row.target_theorem_name,
                "target_lean_declaration": row.target_lean_declaration,
                "target_ids": list(row.target_ids),
                "target_theorem_goal_ids": list(row.target_theorem_goal_ids),
                "source_work_order_id": row.source_work_order_id,
                "source_queue_artifact_kind": row.source_queue_artifact_kind,
                "source_queue_status": row.source_queue_status,
                "source_candidate_artifact_path": row.source_candidate_artifact_path,
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
                "exact_goal_shape_obligation_id": row.exact_goal_shape_obligation_id,
                "exact_goal_shape_obligation": row.exact_goal_shape_obligation,
                "target_artifact_kind": row.target_artifact_kind,
                "source_acceptance_gate": row.source_acceptance_gate,
                "source_theorem_kernel_verified": False,
                "source_theorem_kernel_evidence_eligible": (
                    row.source_theorem_kernel_evidence_eligible
                ),
                "adapter_kernel_verified": row.adapter_kernel_verified,
                "adapter_candidate_imports": list(row.adapter_candidate_imports),
                "unavailable_import": row.unavailable_import,
                "adapter_candidate_requires_unproven_bridge_premises": (
                    row.adapter_candidate_requires_unproven_bridge_premises
                ),
                "unproven_bridge_premise_names": list(
                    row.unproven_bridge_premise_names
                ),
                "source_to_bridge_premise_derivation_work_items": list(
                    row.source_to_bridge_premise_derivation_work_items
                ),
                "kernel_verified_source_to_bridge_premise_derivation_ids": list(
                    row.kernel_verified_source_to_bridge_premise_derivation_ids
                ),
                "verified_source_to_bridge_premise_derivation_artifact_paths": list(
                    row.verified_source_to_bridge_premise_derivation_artifact_paths
                ),
                "verified_source_to_bridge_premise_derivation_declarations": list(
                    row.verified_source_to_bridge_premise_derivation_declarations
                ),
                "verified_source_to_bridge_premise_derivation_signature_excerpts": list(
                    row.verified_source_to_bridge_premise_derivation_signature_excerpts
                ),
                "kernel_verified_source_theorem_proof_body_adapter_ids": (
                    [row.adapter_check_id] if row.adapter_kernel_verified else []
                ),
                "failure_classification": row.failure_classification,
                "semantic_alignment_constraints": list(
                    row.semantic_alignment_constraints
                ),
                "semantic_alignment_blockers": list(row.semantic_alignment_blockers),
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
                "proof_body_attempt_summaries": list(
                    row.proof_body_attempt_summaries
                ),
                "proof_body_goal_excerpt": list(row.proof_body_goal_excerpt),
                "proof_body_goal_context": row.proof_body_goal_context,
                "proof_body_goal_binder_names": list(
                    row.proof_body_goal_binder_names
                ),
                "proof_body_goal_conclusion": row.proof_body_goal_conclusion,
                "proof_body_adapter_required_reasons": list(
                    row.proof_body_adapter_required_reasons
                ),
                "runtime_queue_status": (
                    "SOURCE_THEOREM_PROOF_BODY_ADAPTER_KERNEL_VERIFIED"
                    if row.adapter_kernel_verified
                    else "PENDING_SOURCE_THEOREM_PROOF_BODY_ADAPTER"
                ),
                "input_summary": payload,
                "target_behavior": (
                    "If adapter_kernel_verified=true, rerun exact source theorem "
                    "proof-body search with the verified adapter available. If false, "
                    "route back to Formalizer/ProofEngineer to strengthen the adapter; "
                    "do not treat this row as source theorem proof."
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
    rows_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(rows_path, learning_rows)
    export_manifest = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremProofBodyAdapterRuntimeLearningExportManifest",
        "source_queue_jsonl": str(queue_path),
        "runtime_learning_rows_jsonl": str(rows_path),
        "n_learning_rows": len(learning_rows),
        "n_adapter_kernel_verified": sum(
            1 for row in rows if row.adapter_kernel_verified
        ),
        "n_source_to_bridge_premise_derivation_work_items": sum(
            len(row.source_to_bridge_premise_derivation_work_items) for row in rows
        ),
        "n_kernel_verified_source_to_bridge_premise_derivation_ids": sum(
            len(row.kernel_verified_source_to_bridge_premise_derivation_ids)
            for row in rows
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
        "source_theorem_exact_proof_body_gate_open_target_names": sorted(
            {
                target_name
                for row in rows
                for target_name in (
                    row.source_theorem_exact_proof_body_gate_open_target_names
                    or (row.target_theorem_name,)
                )
                if (
                    row.source_theorem_exact_proof_body_gate_open_for_kernel_repair
                    and target_name
                )
            }
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": [
            premise_id
            for row in rows
            for premise_id in row.kernel_verified_source_to_bridge_premise_derivation_ids
        ],
        "kernel_verified_source_theorem_proof_body_adapter_ids": [
            row.adapter_check_id for row in rows if row.adapter_kernel_verified
        ],
        "source_theorem_kernel_verified": False,
        "boundary": BOUNDARY,
    }
    manifest_path = out_dir / "source_theorem_proof_body_adapter_runtime_learning_export_manifest.json"
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


def _export_source_to_bridge_premise_derivation_queue(
    *,
    rows: list[SourceTheoremProofBodyAdapterCheckRow],
    out_dir: Path,
    source_queue_path: Path,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_rows: list[dict[str, Any]] = []
    for row in rows:
        for rank, item in enumerate(
            row.source_to_bridge_premise_derivation_work_items,
            start=1,
        ):
            premise_name = str(item.get("premise_name", "") or "").strip()
            if not premise_name:
                continue
            queue_rows.append(
                {
                    "schema_version": 1,
                    "artifact_kind": "SourceToBridgePremiseDerivationWorkOrder",
                    "work_order_id": "source_to_bridge_premise_derivation_work_order:"
                    + stable_hash([row.adapter_check_id, premise_name, rank])[:20],
                    "source_adapter_check_id": row.adapter_check_id,
                    "source_adapter_work_order_id": row.work_order_id,
                    "source_queue_jsonl": str(source_queue_path),
                    "question_id": row.question_id,
                    "question_title": row.question_title,
                    "target_theorem_name": row.target_theorem_name,
                    "target_lean_declaration": row.target_lean_declaration,
                    "target_theorem_goal_ids": list(row.target_theorem_goal_ids),
                    "premise_name": premise_name,
                    "premise_target_type": str(
                        item.get("premise_target_type", "") or ""
                    ),
                    "source_to_bridge_premise_target_type": str(
                        item.get(
                            "source_to_bridge_premise_target_type",
                            item.get("premise_target_type", ""),
                        )
                        or ""
                    ),
                    "premise_target_source": str(
                        item.get("premise_target_source", "") or ""
                    ),
                    "source_theorem_signature_conclusion": str(
                        item.get("source_theorem_signature_conclusion", "") or ""
                    ),
                    "proof_body_goal_target_alignment_status": str(
                        item.get("proof_body_goal_target_alignment_status", "") or ""
                    ),
                    "required_derivation": str(
                        item.get("required_derivation", "")
                        or (
                            f"derive {premise_name} from exact source theorem "
                            "hypotheses"
                        )
                    ),
                    "forbidden_as_adapter_assumption": bool(
                        item.get("forbidden_as_adapter_assumption", True)
                    ),
                    "exact_goal_shape_obligation_ids": list(
                        item.get("exact_goal_shape_obligation_ids", []) or []
                    ),
                    "source_candidate_artifact_path": row.source_candidate_artifact_path,
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
                    "adapter_candidate_artifact_path": (
                        row.adapter_candidate_artifact_path
                    ),
                    "adapter_declaration_name": row.adapter_declaration_name,
                    "proof_body_goal_excerpt": list(row.proof_body_goal_excerpt),
                    "proof_body_goal_context": row.proof_body_goal_context,
                    "proof_body_goal_binder_names": list(
                        row.proof_body_goal_binder_names
                    ),
                    "proof_body_goal_conclusion": row.proof_body_goal_conclusion,
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
                    "semantic_alignment_constraints": list(
                        row.semantic_alignment_constraints
                    ),
                    "semantic_alignment_blockers": list(
                        row.semantic_alignment_blockers
                    ),
                    "source_theorem_kernel_evidence_eligible": (
                        row.source_theorem_kernel_evidence_eligible
                    ),
                    "source_to_bridge_premise_goal_context": item.get(
                        "proof_body_goal_context", row.proof_body_goal_context
                    ),
                    "source_to_bridge_premise_goal_binder_names": list(
                        item.get(
                            "proof_body_goal_binder_names",
                            row.proof_body_goal_binder_names,
                        )
                        or []
                    ),
                    "source_to_bridge_premise_goal_conclusion": str(
                        item.get(
                            "proof_body_goal_conclusion",
                            row.proof_body_goal_conclusion,
                        )
                        or ""
                    ),
                    "kernel_verified_theorem_reduction_closure_declarations": (
                        list(row.kernel_verified_theorem_reduction_closure_declarations)
                    ),
                    "verified_theorem_reduction_closure_artifact_paths": (
                        list(row.verified_theorem_reduction_closure_artifact_paths)
                    ),
                    "kernel_verified_source_theorem_semantic_support_obligation_ids": (
                        list(
                            row.kernel_verified_source_theorem_semantic_support_obligation_ids
                        )
                    ),
                    "acceptance_gate": str(
                        item.get("acceptance_gate", "")
                        or (
                            "AXLE/local Lean kernel verifies a source-to-bridge "
                            f"adapter where {premise_name} is derived from exact "
                            "source hypotheses, not introduced as an adapter premise."
                        )
                    ),
                    "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                    "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
                }
            )
    queue_path = out_dir / "source_to_bridge_premise_derivation_queue.jsonl"
    _write_jsonl(queue_path, queue_rows)
    manifest = {
        "schema_version": 1,
        "artifact_kind": "SourceToBridgePremiseDerivationQueueManifest",
        "source_queue_jsonl": str(source_queue_path),
        "queue_jsonl": str(queue_path),
        "n_queue_rows": len(queue_rows),
        "n_source_theorem_exact_proof_body_gate_open_for_kernel_repair": sum(
            1
            for row in queue_rows
            if row.get(
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
                False,
            )
        ),
        "source_theorem_exact_proof_body_gate_open_target_names": sorted(
            {
                target_name
                for row in queue_rows
                for target_name in row.get(
                    "source_theorem_exact_proof_body_gate_open_target_names",
                    [],
                )
                if (
                    row.get(
                        "source_theorem_exact_proof_body_gate_open_for_kernel_repair",
                        False,
                    )
                    and str(target_name).strip()
                )
            }
        ),
        "n_proof_body_signature_probe_artifact_rows": sum(
            1
            for row in queue_rows
            if row.get("proof_body_signature_probe_artifact_path")
        ),
        "n_proof_body_goal_context_rows": sum(
            1
            for row in queue_rows
            if row.get("source_to_bridge_premise_goal_binder_names")
            or row.get("source_to_bridge_premise_goal_conclusion")
        ),
        "proof_body_goal_context_binder_names": sorted(
            {
                str(name)
                for row in queue_rows
                for name in row.get("source_to_bridge_premise_goal_binder_names", [])
                if str(name).strip()
            }
        ),
        "proof_body_goal_context_conclusions": [
            str(row.get("source_to_bridge_premise_goal_conclusion", "") or "")
            for row in queue_rows
            if row.get("source_to_bridge_premise_goal_conclusion")
        ][:8],
        "proof_body_signature_probe_artifact_paths": sorted(
            {
                str(row.get("proof_body_signature_probe_artifact_path", "") or "")
                for row in queue_rows
                if row.get("proof_body_signature_probe_artifact_path")
            }
        ),
        "proof_evidence_status": "WORK_ORDER_QUEUE_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "boundary": (
            "Premise-derivation queue rows are ProofEngineer work orders for "
            "deriving bridge premises from exact source hypotheses. They are not "
            "proof evidence until local Lean/AXLE verifies the resulting adapter, "
            "and the source theorem itself remains unproved until rerun."
        ),
    }
    manifest_path = out_dir / "source_to_bridge_premise_derivation_queue_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "queue_jsonl": queue_path,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "n_queue_rows": len(queue_rows),
        "rows": queue_rows,
    }


def _target_declaration_from_provenance(row: Mapping[str, Any]) -> str:
    provenance = row.get("source_theorem_target_provenance", {})
    if not isinstance(provenance, Mapping):
        return ""
    return str(provenance.get("target_lean_declaration", "") or "")


def _resolve_runtime_artifact_path(*, runtime_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidates = [runtime_dir / path]
    parts = path.parts
    if len(parts) >= 2 and parts[0] == runtime_dir.parent.name:
        candidates.append(runtime_dir.parent.parent / path)
    if parts and parts[0] == runtime_dir.name:
        candidates.append(runtime_dir.parent / path)
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
        "".join(json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _safe_identifier(value: str) -> str:
    safe = re.sub(r"\W+", "_", value.strip())
    safe = safe.strip("_")
    if not safe:
        return "source_theorem_adapter"
    if safe[0].isdigit():
        safe = "source_theorem_adapter_" + safe
    return safe


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = [values]
    return tuple(
        str(value).strip()
        for value in values or []
        if str(value).strip()
    )


def _int_like(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0

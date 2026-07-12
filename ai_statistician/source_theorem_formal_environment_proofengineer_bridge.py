from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .lean_proof_agent_contract import llm_proof_body_generation_contract
from .research_architect import KERNEL_PROOF_BOUNDARY
from .exact_semantic_definition_policy import (
    compact_exact_semantic_placeholder_key,
    exact_semantic_definition_formal_environment_declaration_hint,
    exact_semantic_definition_formal_environment_statement_repair_rules,
    exact_semantic_definition_formal_environment_symbol_names,
)
from .source_theorem_exact_semantic_definition_source_lookup import (
    EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS,
)


ARTIFACT_KIND = "SourceTheoremFormalEnvironmentProofEngineerBridgeManifest"
REPAIR_PACKET_ARTIFACT_KIND = "SourceTheoremFormalEnvironmentRepairPacket"
SIGNATURE_PROBE_ARTIFACT_KIND = "SourceTheoremFormalEnvironmentSignatureProbeManifest"
SIGNATURE_PROBE_ROW_ARTIFACT_KIND = "SourceTheoremFormalEnvironmentSignatureProbeRow"
PROOF_BODY_WORK_ORDER_ARTIFACT_KIND = "ExactSourceTheoremProofBodyWorkOrder"
PROOF_BODY_WORK_ORDER_PROOF_EVIDENCE_STATUS = (
    "EXACT_SOURCE_THEOREM_PROOF_BODY_WORK_ORDER_NOT_PROOF_EVIDENCE"
)
PROOF_BODY_EXECUTION_QUEUE_PROOF_EVIDENCE_STATUS = (
    "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
)
BOUNDARY = (
    "Source-theorem formal-environment ProofEngineer bridge rows are repair "
    "routing artifacts. They identify missing Lean declarations, imports, and "
    "typeclass/coercion blockers for exact source-theorem candidates. They are "
    "not theorem proof, artifact proof, or source-theorem kernel evidence. Only "
    "a subsequent local Lean/AXLE verifier manifest with kernel_verified=true "
    "can promote any repaired artifact to proof evidence."
)
SIGNATURE_PROBE_PROOF_EVIDENCE_STATUS = "SIGNATURE_PROBE_NOT_PROOF_EVIDENCE"
CANDIDATE_MATERIALIZATION_REQUIRED_FAILURE = (
    "source_theorem_candidate_materialization_required"
)
CANDIDATE_ARTIFACT_MISSING_FAILURE = "source_theorem_candidate_artifact_missing"
SIGNATURE_PROBE_BLOCKED_NEEDS_CANDIDATE_ARTIFACT = (
    "SIGNATURE_PROBE_BLOCKED_NEEDS_CANDIDATE_ARTIFACT"
)
SIGNATURE_PROBE_BLOCKED_CANDIDATE_ARTIFACT_NOT_FOUND = (
    "SIGNATURE_PROBE_BLOCKED_CANDIDATE_ARTIFACT_NOT_FOUND"
)
CANDIDATE_MATERIALIZATION_CONTRACT = (
    "Formalizer/ProofEngineer must materialize an exact source-theorem Lean "
    "candidate artifact before signature probes or proof-body execution can run."
)
SIGNATURE_PROBE_BOUNDARY = (
    "Source-theorem formal-environment signature probes are local Lean typecheck "
    "diagnostics over a byte-preserved upstream candidate. Runtime code must not "
    "rewrite imports, statements, namespaces, or semantic primitives before Lean "
    "adjudication. A probe may expose compiler feedback, but it is not artifact "
    "proof, source-theorem proof, or semantic promotion evidence."
)
PROOF_BODY_WORK_ORDER_BOUNDARY = (
    "Exact source-theorem proof-body work orders are ProofEngineer tasks emitted "
    "after a signature probe reaches the theorem proof body. They are not proof "
    "evidence, do not prove the source theorem, and do not authorize changing the "
    "theorem statement. Promotion requires a subsequent local Lean/AXLE verifier "
    "manifest with source_theorem_kernel_verified=true."
)
PROOF_BODY_EXECUTION_QUEUE_BOUNDARY = (
    "Exact source-theorem proof-body execution queue rows are operational "
    "ProofEngineer work contracts. They identify a live Lean proof-body goal, "
    "an output candidate artifact path, transcript path, and verifier gate. They "
    "are not theorem proof evidence; only a later local Lean/AXLE verifier row "
    "can promote a completed candidate."
)
SOURCE_THEOREM_TARGET_PROVENANCE_STRING_KEYS = (
    "source_theorem_target_resolution_id",
    "source_theorem_promotion_id",
    "source_theorem_route_id",
    "source_theorem_queue_item_id",
    "source_theorem_replay_id",
    "source_theorem_task_id",
    "source_theorem_question_id",
    "source_theorem_goal_id",
    "source_theorem_statement",
    "source_theorem_skeleton",
    "source_theorem_lean_file",
    "target_lean_declaration",
    "artifact_verification_id",
    "artifact_verifier_manifest",
    "materialization_id",
    "execution_queue_id",
)


def _source_theorem_target_known_value(provenance: object) -> bool | None:
    if not isinstance(provenance, Mapping):
        return None
    value = provenance.get("source_theorem_target_known")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    return None


@dataclass(frozen=True)
class SourceTheoremFormalEnvironmentSignatureProbeRow:
    schema_version: int
    artifact_kind: str
    signature_probe_id: str
    repair_packet_id: str
    source_work_order_id: str
    target_theorem_name: str
    target_ids: tuple[str, ...]
    target_theorem_goal_ids: tuple[str, ...]
    target_lean_declaration: str
    source_theorem_target_known: bool
    source_theorem_target_provenance: dict[str, Any]
    semantic_alignment_constraints: tuple[str, ...]
    source_candidate_artifact_path: str
    signature_probe_artifact_path: str
    local_lean_checked: bool
    local_lean_compiled: bool
    signature_typecheck_reached_proof_body: bool
    lean_command: tuple[str, ...]
    lean_project: str
    lean_timeout: int
    returncode: int
    diagnostics: tuple[str, ...]
    failure_classification: str
    signature_probe_status: str
    proof_evidence_status: str
    boundary: str
    ok: bool
    errors: tuple[str, ...] = ()
    candidate_materialization_required: bool = False
    candidate_materialization_contract: str = ""
    source_candidate_fingerprint: str = ""
    signature_probe_source_fingerprint: str = ""
    candidate_bytes_preserved: bool = False


def resolve_source_theorem_formal_environment_queue_path(
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
        artifacts.get(
            "runtime_source_theorem_formal_environment_work_orders_jsonl",
            "",
        )
        or artifacts.get(
            "runtime_source_theorem_promotion_proofengineer_formal_environment_work_orders_jsonl",
            "",
        )
        or ""
    )
    if not raw_path:
        raw_path = _formal_environment_queue_path_from_bridge_manifest(
            runtime_dir=runtime_dir,
            artifacts=artifacts,
        )
    if not raw_path:
        raise ValueError(
            "runtime manifest does not list "
            "runtime_source_theorem_formal_environment_work_orders_jsonl or "
            "a source-theorem promotion bridge manifest with formal-environment "
            "work orders"
        )
    return _resolve_runtime_artifact_path(runtime_dir=runtime_dir, raw_path=raw_path)


def _formal_environment_queue_path_from_bridge_manifest(
    *,
    runtime_dir: Path,
    artifacts: Mapping[str, Any],
) -> str:
    bridge_manifest_keys = (
        "runtime_source_theorem_promotion_proofengineer_bridge_manifest",
        "runtime_source_theorem_promotion_proofengineer_bridge_from_source_semantic_support_manifest",
        "runtime_source_theorem_promotion_proofengineer_bridge_from_post_executor_semantic_support_manifest",
    )
    for key in bridge_manifest_keys:
        raw_manifest_path = str(artifacts.get(key, "") or "")
        if not raw_manifest_path:
            continue
        manifest_path = _resolve_runtime_artifact_path(
            runtime_dir=runtime_dir,
            raw_path=raw_manifest_path,
        )
        if not manifest_path.exists():
            continue
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        raw_queue_path = str(
            payload.get("source_theorem_formal_environment_work_orders_jsonl", "")
            or ""
        )
        if raw_queue_path:
            return raw_queue_path
    return ""


def _resolve_runtime_artifact_path(*, runtime_dir: Path, raw_path: str) -> Path:
    queue_path = Path(raw_path)
    if queue_path.is_absolute() or queue_path.exists():
        return queue_path
    candidates = [runtime_dir / queue_path]
    parts = queue_path.parts
    if len(parts) >= 2 and parts[0] == runtime_dir.parent.name:
        candidates.append(runtime_dir.parent.parent / queue_path)
    if parts and parts[0] == runtime_dir.name:
        candidates.append(runtime_dir.parent / queue_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def run_source_theorem_formal_environment_proofengineer_bridge(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    queue_jsonl: Path | None = None,
    question_id: str = "",
    run_signature_probes: bool = False,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = resolve_source_theorem_formal_environment_queue_path(
        runtime_dir=runtime_dir,
        queue_jsonl=queue_jsonl,
    )
    work_orders = _read_jsonl(queue_path)
    repair_packets = [_repair_packet(row) for row in work_orders]
    repair_packets_path = out_dir / "source_theorem_formal_environment_repair_packets.jsonl"
    _write_jsonl(repair_packets_path, repair_packets)
    signature_probe_result: dict[str, object] | None = None
    if run_signature_probes:
        signature_probe_result = _export_signature_probes(
            repair_packets=repair_packets,
            out_dir=out_dir / "signature_probes",
            lean_project=Path(lean_project) if lean_project else None,
            lean_timeout=lean_timeout,
            lean_command=lean_command,
        )
    proof_body_work_order_result = _export_proof_body_work_orders(
        repair_packets=repair_packets,
        signature_probe_result=signature_probe_result,
        out_dir=out_dir / "exact_source_theorem_proof_body_work_orders",
    )
    proof_body_execution_queue_result = _export_proof_body_execution_queue(
        proof_body_work_order_result=proof_body_work_order_result,
        out_dir=out_dir / "exact_source_theorem_proof_body_execution_queue",
    )
    learning_result = _export_runtime_learning_rows(
        repair_packets=repair_packets,
        out_dir=out_dir / "runtime_learning_export",
        question_id=question_id,
        queue_path=queue_path,
        signature_probe_result=signature_probe_result,
        proof_body_work_order_result=proof_body_work_order_result,
        proof_body_execution_queue_result=proof_body_execution_queue_result,
    )
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "source_runtime_dir": str(runtime_dir or ""),
        "source_queue_jsonl": str(queue_path),
        "repair_packets_jsonl": str(repair_packets_path),
        "runtime_learning_rows_jsonl": str(learning_result["runtime_learning_rows_jsonl"]),
        "runtime_learning_export_manifest": str(learning_result["export_manifest_path"]),
        "signature_probes_requested": bool(run_signature_probes),
        "signature_probe_manifest": str(
            signature_probe_result.get("signature_probe_manifest_path", "")
            if signature_probe_result
            else ""
        ),
        "signature_probe_rows_jsonl": str(
            signature_probe_result.get("signature_probe_rows_jsonl", "")
            if signature_probe_result
            else ""
        ),
        "n_signature_probe_rows": int(
            signature_probe_result.get("n_signature_probe_rows", 0)
            if signature_probe_result
            else 0
        ),
        "n_signature_probes_reached_proof_body": int(
            signature_probe_result.get("n_signature_probes_reached_proof_body", 0)
            if signature_probe_result
            else 0
        ),
        "signature_probe_proof_evidence_status": str(
            signature_probe_result.get("proof_evidence_status", "")
            if signature_probe_result
            else ""
        ),
        "proof_body_work_orders_jsonl": str(
            proof_body_work_order_result.get("proof_body_work_orders_jsonl", "")
        ),
        "proof_body_work_order_manifest": str(
            proof_body_work_order_result.get("proof_body_work_order_manifest", "")
        ),
        "n_proof_body_work_orders": int(
            proof_body_work_order_result.get("n_proof_body_work_orders", 0)
        ),
        "n_proof_body_work_orders_from_pseudo_formal": int(
            proof_body_work_order_result.get(
                "n_proof_body_work_orders_from_pseudo_formal",
                0,
            )
            or 0
        ),
        "n_proof_body_work_orders_from_formalizer_pf_component_gate": int(
            proof_body_work_order_result.get(
                "n_proof_body_work_orders_from_formalizer_pf_component_gate",
                0,
            )
            or 0
        ),
        "proof_body_work_order_proof_evidence_status": str(
            proof_body_work_order_result.get("proof_evidence_status", "")
        ),
        "proof_body_execution_queue_jsonl": str(
            proof_body_execution_queue_result.get("proof_body_execution_queue_jsonl", "")
        ),
        "proof_body_execution_queue_manifest": str(
            proof_body_execution_queue_result.get("proof_body_execution_queue_manifest", "")
        ),
        "n_proof_body_execution_queue_rows": int(
            proof_body_execution_queue_result.get("n_execution_queue_rows", 0)
        ),
        "n_proof_body_execution_queue_rows_from_pseudo_formal": int(
            proof_body_execution_queue_result.get(
                "n_execution_queue_rows_from_pseudo_formal",
                0,
            )
            or 0
        ),
        "n_proof_body_execution_queue_rows_from_formalizer_pf_component_gate": int(
            proof_body_execution_queue_result.get(
                "n_execution_queue_rows_from_formalizer_pf_component_gate",
                0,
            )
            or 0
        ),
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": list(
            dict.fromkeys(
                [
                    *list(
                        proof_body_work_order_result.get(
                            "formalizer_pf_component_gate_exact_rows_jsonl_paths",
                            [],
                        )
                        or []
                    ),
                    *list(
                        proof_body_execution_queue_result.get(
                            "formalizer_pf_component_gate_exact_rows_jsonl_paths",
                            [],
                        )
                        or []
                    ),
                ]
            )
        ),
        "n_proof_body_execution_live_goal_requests": int(
            proof_body_execution_queue_result.get("n_live_goal_requests", 0)
        ),
        "proof_body_execution_queue_proof_evidence_status": str(
            proof_body_execution_queue_result.get("proof_evidence_status", "")
        ),
        "n_work_orders": len(work_orders),
        "n_repair_packets": len(repair_packets),
        "n_missing_formal_symbols": len(
            {
                symbol
                for packet in repair_packets
                for symbol in packet.get("missing_formal_symbols", []) or []
            }
        ),
        "n_typeclass_blockers": len(
            {
                blocker
                for packet in repair_packets
                for blocker in packet.get("typeclass_blockers", []) or []
            }
        ),
        "runtime_learning_ready": bool(learning_result["n_learning_rows"]),
        "proof_evidence_status": "FORMAL_ENVIRONMENT_REPAIR_PACKETS_NOT_PROOF_EVIDENCE",
        "boundary": BOUNDARY,
    }
    manifest_path = out_dir / "source_theorem_formal_environment_proofengineer_bridge_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def _repair_packet(row: Mapping[str, Any]) -> dict[str, Any]:
    work_order_id = str(row.get("work_order_id", "") or "").strip()
    target_theorem_name = str(row.get("target_theorem_name", "") or "").strip()
    missing_symbols = _str_list(row.get("missing_formal_symbols", []) or [])
    typeclass_blockers = _str_list(row.get("typeclass_blockers", []) or [])
    recommended_tasks = _str_list(row.get("recommended_repair_tasks", []) or [])
    candidate_artifact_path = str(row.get("candidate_artifact_path", "") or "").strip()
    candidate_source = _read_candidate_source(candidate_artifact_path)
    candidate_source_symbols = _source_candidate_environment_symbols(candidate_source)
    if candidate_source_symbols:
        missing_symbols = list(dict.fromkeys([*missing_symbols, *candidate_source_symbols]))
    source_target_provenance = _source_theorem_target_provenance(row)
    question_id = str(
        row.get("question_id", "")
        or source_target_provenance.get("question_id", "")
        or source_target_provenance.get("source_theorem_question_id", "")
        or ""
    )
    target_lean_declaration = str(
        source_target_provenance.get("target_lean_declaration", "")
        or target_theorem_name
    ).strip()
    target_ids = _target_ids_from_work_order(row, fallback_target=target_theorem_name)
    semantic_alignment_constraints = _str_list(
        source_target_provenance.get("semantic_alignment_constraints", []) or []
    )
    declaration_hints = _formal_environment_declaration_hints(missing_symbols)
    statement_hints = _statement_repair_hints(
        typeclass_blockers,
        missing_symbols=missing_symbols,
    )
    signature_probe_plan = _lean_signature_probe_plan(
        missing_symbols=missing_symbols,
        typeclass_blockers=typeclass_blockers,
        candidate_artifact_path=candidate_artifact_path,
    )
    exact_semantic_context = _exact_semantic_definition_context(row)
    repair_packet_id = "source_theorem_formal_environment_repair_packet:" + stable_hash(
        [
            work_order_id,
            target_theorem_name,
            target_ids,
            candidate_artifact_path,
            missing_symbols,
            typeclass_blockers,
        ]
    )[:20]
    return {
        "schema_version": 1,
        "artifact_kind": REPAIR_PACKET_ARTIFACT_KIND,
        **exact_semantic_context,
        "repair_packet_id": repair_packet_id,
        "source_work_order_id": work_order_id,
        "question_id": question_id,
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "target_theorem_goal_ids": list(target_ids),
        "target_lean_declaration": target_lean_declaration,
        "candidate_artifact_path": candidate_artifact_path,
        "exact_semantic_definition_context": exact_semantic_context,
        "lean_statement_sketch": str(row.get("lean_statement_sketch", "") or ""),
        "lean_imports": _str_list(row.get("lean_imports", []) or []),
        "source_theorem_target_known": bool(
            _source_theorem_target_known_value(source_target_provenance) is True
        ),
        "source_theorem_target_provenance": source_target_provenance,
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "kernel_verified_source_to_bridge_premise_derivation_ids": _str_list(
            row.get("kernel_verified_source_to_bridge_premise_derivation_ids", [])
            or []
        ),
        "verified_source_to_bridge_premise_derivation_artifact_paths": _str_list(
            row.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
            or []
        ),
        "verified_source_to_bridge_premise_derivation_declarations": _str_list(
            row.get("verified_source_to_bridge_premise_derivation_declarations", [])
            or []
        ),
        "verified_source_to_bridge_premise_derivation_signature_excerpts": _str_list(
            row.get(
                "verified_source_to_bridge_premise_derivation_signature_excerpts",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_work_order_ids": _str_list(
            row.get(
                "kernel_verified_theorem_reduction_closure_work_order_ids",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_declarations": _str_list(
            row.get(
                "kernel_verified_theorem_reduction_closure_declarations",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_signature_excerpts": _str_list(
            row.get(
                "kernel_verified_theorem_reduction_closure_signature_excerpts",
                [],
            )
            or []
        ),
        "verified_theorem_reduction_closure_artifact_paths": _str_list(
            row.get("verified_theorem_reduction_closure_artifact_paths", []) or []
        ),
        "kernel_verified_theorem_reduction_closure_target_ids": _str_list(
            row.get("kernel_verified_theorem_reduction_closure_target_ids", [])
            or []
        ),
        "proof_body_attempts": _str_list(row.get("proof_body_attempts", []) or [])[
            :8
        ],
        "proof_body_attempt_source": str(
            row.get("proof_body_attempt_source", "") or ""
        ),
        "artifact_verification_id": str(row.get("artifact_verification_id", "") or ""),
        "artifact_verifier_manifest": str(row.get("artifact_verifier_manifest", "") or ""),
        "failure_classification": str(row.get("failure_classification", "") or ""),
        "diagnostics": _str_list(row.get("diagnostics", []) or [])[:8],
        "missing_formal_symbols": missing_symbols,
        "typeclass_blockers": typeclass_blockers,
        "formal_environment_declaration_hints": declaration_hints,
        "statement_repair_hints": statement_hints,
        "lean_signature_probe_plan": signature_probe_plan,
        "recommended_repair_tasks": recommended_tasks or _default_repair_tasks(
            missing_symbols=missing_symbols,
            typeclass_blockers=typeclass_blockers,
        ),
        "proofengineer_action_plan": _proofengineer_action_plan(
            missing_symbols=missing_symbols,
            typeclass_blockers=typeclass_blockers,
            candidate_artifact_path=candidate_artifact_path,
        ),
        "required_outputs": [
            "repaired exact source-theorem Lean candidate or import/environment patch",
            "rerunnable materializer/artifact-verifier manifest",
            "local Lean/AXLE diagnostics showing whether the exact theorem declaration is reached",
            "runtime learning row only after a verifier manifest records kernel evidence",
        ],
        "acceptance_gate": (
            "rerun the exact-source materializer/artifact verifier locally; proof evidence "
            "requires artifact_kernel_verified=true and then source_theorem_kernel_verified=true"
        ),
        "repair_status": "FORMAL_ENVIRONMENT_REPAIR_REQUIRED",
        "proof_evidence_status": "REPAIR_PACKET_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": KERNEL_PROOF_BOUNDARY,
        "boundary": BOUNDARY,
    }


def _source_theorem_target_provenance(row: Mapping[str, Any]) -> dict[str, Any]:
    sources: list[Mapping[str, Any]] = [row]
    for nested_key in (
        "source_theorem_target_provenance",
        "source_theorem_target_context",
        "kernel_overlay_context",
        "overlay_row",
    ):
        nested = row.get(nested_key, {})
        if isinstance(nested, Mapping):
            sources.append(nested)
    provenance: dict[str, Any] = {}
    if any("source_theorem_target_known" in source for source in sources):
        known_values = tuple(
            value
            for value in (
                _source_theorem_target_known_value(source)
                for source in sources
                if "source_theorem_target_known" in source
            )
            if value is not None
        )
        if known_values:
            provenance["source_theorem_target_known"] = any(known_values)
    constraints: list[str] = []
    for source in sources:
        for key in SOURCE_THEOREM_TARGET_PROVENANCE_STRING_KEYS:
            if key in provenance:
                continue
            value = str(source.get(key, "") or "").strip()
            if value:
                provenance[key] = value
        constraints.extend(_str_list(source.get("semantic_alignment_constraints", []) or []))
    if constraints:
        provenance["semantic_alignment_constraints"] = list(dict.fromkeys(constraints))
    return provenance


def _proofengineer_action_plan(
    *,
    missing_symbols: list[str],
    typeclass_blockers: list[str],
    candidate_artifact_path: str,
) -> list[str]:
    actions: list[str] = []
    for symbol in missing_symbols:
        actions.append(
            "search Mathlib/StatInference/local Lean sources for an existing declaration "
            f"matching `{symbol}` before inventing a new primitive"
        )
        actions.append(
            "if no faithful declaration exists, draft a minimal source-theorem primitive "
            f"for `{symbol}` with explicit semantics and mark it as unproved until local Lean verifies it"
        )
    for blocker in typeclass_blockers:
        actions.append(
            "repair the exact source-theorem statement or coercions that caused Lean to request "
            f"typeclass `{blocker}`"
        )
    if candidate_artifact_path:
        actions.append(
            "rerun local Lean on the repaired candidate artifact "
            f"`{candidate_artifact_path}` before exporting any proof-memory row"
        )
    actions.append(
        "do not replace the exact source theorem with a route probe, vacuous True target, "
        "or helper lemma that assumes the target"
    )
    return list(dict.fromkeys(actions))[:10]


def _read_candidate_source(candidate_artifact_path: str) -> str:
    if not candidate_artifact_path:
        return ""
    try:
        return Path(candidate_artifact_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _source_candidate_environment_symbols(source: str) -> list[str]:
    if not source:
        return []
    symbol_positions: list[tuple[int, str]] = []
    for symbol in exact_semantic_definition_formal_environment_symbol_names():
        match = re.search(rf"\b{re.escape(symbol)}\b", source)
        if match:
            symbol_positions.append((match.start(), symbol))
    return [
        symbol
        for _, symbol in sorted(
            symbol_positions,
            key=lambda item: (item[0], item[1]),
        )
    ]


def _formal_environment_declaration_hints(missing_symbols: list[str]) -> list[dict[str, Any]]:
    return [
        exact_semantic_definition_formal_environment_declaration_hint(symbol)
        for symbol in missing_symbols
    ]


def _statement_repair_hints(
    typeclass_blockers: list[str],
    *,
    missing_symbols: list[str] | None = None,
) -> list[dict[str, str]]:
    hints: list[dict[str, str]] = []
    matched_blockers: set[str] = set()
    symbols = missing_symbols or []
    for rule in exact_semantic_definition_formal_environment_statement_repair_rules():
        matched_for_blockers = [
            blocker
            for blocker in typeclass_blockers
            if _formal_environment_statement_repair_rule_matches(
                rule,
                blocker=blocker,
                missing_symbols=symbols,
            )
        ]
        if matched_for_blockers:
            matched_blockers.update(matched_for_blockers)
            for blocker in matched_for_blockers:
                if rule.get("diagnosis") or rule.get("repair_hint"):
                    hints.append(
                        {
                            "blocker": blocker,
                            "diagnosis": str(rule.get("diagnosis", "") or ""),
                            "repair_hint": str(rule.get("repair_hint", "") or ""),
                            "example_target_shape": str(
                                rule.get("example_target_shape", "") or ""
                            ),
                            "honesty_boundary": str(
                                rule.get("honesty_boundary", "") or ""
                            ),
                            "policy_rule_id": str(rule.get("rule_id", "") or ""),
                        }
                    )
        elif not typeclass_blockers and _formal_environment_statement_repair_rule_matches(
            rule,
            blocker="",
            missing_symbols=symbols,
        ):
            if rule.get("diagnosis") or rule.get("repair_hint"):
                hints.append(
                    {
                        "blocker": "",
                        "diagnosis": str(rule.get("diagnosis", "") or ""),
                        "repair_hint": str(rule.get("repair_hint", "") or ""),
                        "example_target_shape": str(
                            rule.get("example_target_shape", "") or ""
                        ),
                        "honesty_boundary": str(
                            rule.get("honesty_boundary", "") or ""
                        ),
                        "policy_rule_id": str(rule.get("rule_id", "") or ""),
                    }
                )
    for blocker in typeclass_blockers:
        if blocker not in matched_blockers:
            hints.append(
                {
                    "blocker": blocker,
                    "diagnosis": "Lean could not synthesize a typeclass needed by the candidate",
                    "repair_hint": (
                        "inspect the exact diagnostic and repair the smallest statement "
                        "coercion/import/class context needed for typechecking"
                    ),
                    "example_target_shape": "",
                    "honesty_boundary": (
                        "typeclass repair is environment routing evidence, not theorem proof"
                    ),
                }
            )
    return hints


def _formal_environment_statement_repair_rule_matches(
    rule: Mapping[str, Any],
    *,
    blocker: str,
    missing_symbols: list[str],
) -> bool:
    blocker_terms = tuple(rule.get("typeclass_blocker_contains_any", ()) or ())
    if blocker_terms and not any(term in blocker for term in blocker_terms):
        return False
    symbol_keys = tuple(
        compact_exact_semantic_placeholder_key(value)
        for value in rule.get("missing_symbol_keys_any", ()) or ()
        if compact_exact_semantic_placeholder_key(value)
    )
    if symbol_keys:
        missing_keys = {
            compact_exact_semantic_placeholder_key(symbol)
            for symbol in missing_symbols
            if compact_exact_semantic_placeholder_key(symbol)
        }
        if not missing_keys.intersection(symbol_keys):
            return False
    return bool(blocker_terms or symbol_keys)


def _lean_signature_probe_plan(
    *,
    missing_symbols: list[str],
    typeclass_blockers: list[str],
    candidate_artifact_path: str,
) -> dict[str, Any]:
    return {
        "probe_kind": "statement_typecheck_not_proof",
        "candidate_artifact_path": candidate_artifact_path,
        "objective": (
            "produce a repaired Lean candidate whose imports, primitive declarations, "
            "and theorem statement typecheck far enough to reach the intentionally "
            "unproved proof body"
        ),
        "allowed_edits": [
            "add faithful imports found by search",
            "draft narrow local primitive signatures for missing symbols when search fails",
            "repair explicit coercions/codomain mismatches in the theorem statement",
        ],
        "forbidden_edits": [
            "do not add axioms",
            "do not replace the source theorem with `True` or a vacuous route probe",
            "do not assume the target theorem or add a helper lemma restating it",
            "do not mark signature-only primitives as proof evidence",
        ],
        "known_blockers": {
            "missing_formal_symbols": list(missing_symbols),
            "typeclass_blockers": list(typeclass_blockers),
        },
        "success_criterion": (
            "the artifact verifier no longer reports missing-symbol/typeclass diagnostics; "
            "remaining failure should be the intentional unproved proof body or genuine "
            "proof obligations"
        ),
        "proof_evidence_status": "SIGNATURE_PROBE_PLAN_NOT_PROOF_EVIDENCE",
        "boundary": BOUNDARY,
    }


def _export_signature_probes(
    *,
    repair_packets: list[Mapping[str, Any]],
    out_dir: Path,
    lean_project: Path | None,
    lean_timeout: int,
    lean_command: tuple[str, ...] | None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = out_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    command = lean_command or _lean_command(lean_project)
    rows = [
        _signature_probe_row(
            packet,
            artifacts_dir=artifacts_dir,
            lean_project=lean_project,
            lean_timeout=lean_timeout,
            lean_command=command,
        )
        for packet in repair_packets
    ]
    materialized_rows = [
        row for row in rows if not row.candidate_materialization_required
    ]
    rows_path = out_dir / "source_theorem_formal_environment_signature_probe_rows.jsonl"
    _write_jsonl(rows_path, [asdict(row) for row in rows])
    manifest_path = out_dir / "source_theorem_formal_environment_signature_probe_manifest.json"
    manifest = {
        "schema_version": 1,
        "artifact_kind": SIGNATURE_PROBE_ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "signature_probe_rows_jsonl": str(rows_path),
        "artifacts_dir": str(artifacts_dir),
        "lean_project": str(lean_project or ""),
        "lean_timeout": int(lean_timeout),
        "lean_command": list(command),
        "n_signature_probe_rows": len(rows),
        "n_local_lean_checked": sum(1 for row in rows if row.local_lean_checked),
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
        "n_signature_probes_reached_proof_body": sum(
            1 for row in rows if row.signature_typecheck_reached_proof_body
        ),
        "n_candidate_bytes_preserved": sum(
            1 for row in rows if row.candidate_bytes_preserved
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_signature_probes_reached_proof_body": bool(rows)
        and all(row.signature_typecheck_reached_proof_body for row in rows),
        "all_materialized_candidate_bytes_preserved": bool(materialized_rows)
        and all(row.candidate_bytes_preserved for row in materialized_rows),
        "rows": [asdict(row) for row in rows],
        "proof_evidence_status": SIGNATURE_PROBE_PROOF_EVIDENCE_STATUS,
        "boundary": SIGNATURE_PROBE_BOUNDARY,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "signature_probe_manifest_path": manifest_path,
        "signature_probe_rows_jsonl": rows_path,
        "n_signature_probe_rows": len(rows),
        "n_signature_probes_reached_proof_body": sum(
            1 for row in rows if row.signature_typecheck_reached_proof_body
        ),
        "n_candidate_bytes_preserved": sum(
            1 for row in rows if row.candidate_bytes_preserved
        ),
        "rows": [asdict(row) for row in rows],
        "proof_evidence_status": SIGNATURE_PROBE_PROOF_EVIDENCE_STATUS,
        "boundary": SIGNATURE_PROBE_BOUNDARY,
    }


def _signature_probe_row(
    packet: Mapping[str, Any],
    *,
    artifacts_dir: Path,
    lean_project: Path | None,
    lean_timeout: int,
    lean_command: tuple[str, ...],
) -> SourceTheoremFormalEnvironmentSignatureProbeRow:
    errors: list[str] = []
    repair_packet_id = str(packet.get("repair_packet_id", "") or "")
    source_work_order_id = str(packet.get("source_work_order_id", "") or "")
    target_theorem_name = str(packet.get("target_theorem_name", "") or "")
    source_target_provenance = dict(
        packet.get("source_theorem_target_provenance", {}) or {}
    )
    target_ids = _target_ids_from_work_order(
        packet,
        fallback_target=target_theorem_name,
    )
    target_lean_declaration = str(
        packet.get("target_lean_declaration", "")
        or source_target_provenance.get("target_lean_declaration", "")
        or target_theorem_name
    )
    semantic_alignment_constraints = _str_list(
        packet.get("semantic_alignment_constraints", [])
        or source_target_provenance.get("semantic_alignment_constraints", [])
        or []
    )
    candidate_raw = str(packet.get("candidate_artifact_path", "") or "")
    candidate_path = Path(candidate_raw) if candidate_raw else Path()
    probe_id = "source_theorem_formal_environment_signature_probe:" + stable_hash(
        [repair_packet_id, candidate_raw, target_theorem_name, target_ids]
    )[:20]
    probe_artifact_path = artifacts_dir / f"{_safe_file_stem(target_theorem_name or probe_id)}_signature_probe.lean"
    source = ""
    candidate_materialization_required = False
    candidate_materialization_contract = ""
    candidate_precondition_failure = ""
    candidate_precondition_status = ""
    if not repair_packet_id:
        errors.append("repair_packet_id missing")
    if not candidate_raw:
        source = _work_order_candidate_source(packet)
        if source:
            candidate_path = (
                artifacts_dir
                / f"{_safe_file_stem(target_theorem_name or probe_id)}_work_order_candidate.lean"
            )
            candidate_path.write_text(source, encoding="utf-8")
            candidate_raw = str(candidate_path)
        else:
            candidate_materialization_required = True
            candidate_materialization_contract = CANDIDATE_MATERIALIZATION_CONTRACT
            candidate_precondition_failure = CANDIDATE_MATERIALIZATION_REQUIRED_FAILURE
            candidate_precondition_status = (
                SIGNATURE_PROBE_BLOCKED_NEEDS_CANDIDATE_ARTIFACT
            )
            errors.extend(
                _candidate_materialization_diagnostics(
                    packet,
                    reason="candidate_artifact_path missing",
                )
            )
    elif not candidate_path.exists():
        candidate_materialization_required = True
        candidate_materialization_contract = CANDIDATE_MATERIALIZATION_CONTRACT
        candidate_precondition_failure = CANDIDATE_ARTIFACT_MISSING_FAILURE
        candidate_precondition_status = (
            SIGNATURE_PROBE_BLOCKED_CANDIDATE_ARTIFACT_NOT_FOUND
        )
        errors.extend(
            _candidate_materialization_diagnostics(
                packet,
                reason=f"candidate artifact missing: {candidate_path}",
            )
        )
    else:
        try:
            source = candidate_path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"failed to read candidate artifact: {type(exc).__name__}: {exc}")
    probe_source = ""
    if not errors:
        probe_source = _signature_probe_source(source, packet)
        probe_artifact_path.write_text(probe_source, encoding="utf-8")
    checked = False
    compiled = False
    returncode = -1
    diagnostics: tuple[str, ...] = ()
    status = ""
    if candidate_precondition_failure:
        diagnostics = tuple(errors)
        failure = candidate_precondition_failure
        status = candidate_precondition_status
    elif not lean_command:
        errors.append("lean executable not found")
        diagnostics = ("lean executable not found",)
        failure = "local_lean_unavailable"
    elif errors:
        diagnostics = tuple(errors)
        failure = "static_signature_probe_materialization_failed"
    else:
        checked = True
        compiled, returncode, diagnostics = _run_local_lean(
            probe_artifact_path,
            lean_command=lean_command,
            lean_project=lean_project,
            timeout_s=lean_timeout,
        )
        failure = _classify_signature_probe_failure(diagnostics)
    reached_proof_body = compiled or _signature_probe_reached_proof_body(
        diagnostics,
        packet=packet,
    )
    if not status:
        status = (
            "SIGNATURE_PROBE_COMPILED_NOT_PROOF"
            if compiled
            else (
                "SIGNATURE_PROBE_REACHED_PROOF_BODY_NOT_PROOF"
                if reached_proof_body
                else "SIGNATURE_PROBE_LOCAL_LEAN_FAILED"
            )
        )
    ok = not errors and checked and reached_proof_body
    return SourceTheoremFormalEnvironmentSignatureProbeRow(
        schema_version=1,
        artifact_kind=SIGNATURE_PROBE_ROW_ARTIFACT_KIND,
        signature_probe_id=probe_id,
        repair_packet_id=repair_packet_id,
        source_work_order_id=source_work_order_id,
        target_theorem_name=target_theorem_name,
        target_ids=tuple(target_ids),
        target_theorem_goal_ids=tuple(target_ids),
        target_lean_declaration=target_lean_declaration,
        source_theorem_target_known=(
            _source_theorem_target_known_value(packet) is True
            or _source_theorem_target_known_value(source_target_provenance) is True
        ),
        source_theorem_target_provenance=source_target_provenance,
        semantic_alignment_constraints=tuple(semantic_alignment_constraints),
        source_candidate_artifact_path=candidate_raw,
        signature_probe_artifact_path=str(probe_artifact_path),
        local_lean_checked=checked,
        local_lean_compiled=compiled,
        signature_typecheck_reached_proof_body=reached_proof_body,
        lean_command=lean_command,
        lean_project=str(lean_project or ""),
        lean_timeout=int(lean_timeout),
        returncode=int(returncode),
        diagnostics=diagnostics[:40],
        failure_classification=failure,
        signature_probe_status=status,
        proof_evidence_status=SIGNATURE_PROBE_PROOF_EVIDENCE_STATUS,
        boundary=SIGNATURE_PROBE_BOUNDARY,
        ok=ok,
        errors=tuple(errors),
        candidate_materialization_required=candidate_materialization_required,
        candidate_materialization_contract=candidate_materialization_contract,
        source_candidate_fingerprint=stable_hash(source) if source else "",
        signature_probe_source_fingerprint=(
            stable_hash(probe_source) if probe_source else ""
        ),
        candidate_bytes_preserved=bool(not errors and probe_source == source),
    )


def _work_order_candidate_source(packet: Mapping[str, Any]) -> str:
    statement = str(packet.get("lean_statement_sketch", "") or "").strip()
    if not statement or statement.startswith("FORMAL_GAP"):
        return ""
    imports: list[str] = []
    for raw_import in _str_list(packet.get("lean_imports", []) or []):
        import_name = raw_import.strip()
        if not import_name:
            continue
        imports.append(
            import_name if import_name.startswith("import ") else f"import {import_name}"
        )
    prefix = "\n".join(dict.fromkeys(imports))
    return (prefix + "\n\n" if prefix else "") + statement + "\n"


def _candidate_materialization_diagnostics(
    packet: Mapping[str, Any],
    *,
    reason: str,
) -> list[str]:
    diagnostics = [
        reason,
        f"candidate_materialization_required: {CANDIDATE_MATERIALIZATION_CONTRACT}",
    ]
    target = str(packet.get("target_theorem_name", "") or "")
    if target:
        diagnostics.append(f"target_theorem_name={target}")
    missing_symbols = _str_list(packet.get("missing_formal_symbols", []) or [])
    if missing_symbols:
        diagnostics.append("missing_formal_symbols=" + ", ".join(missing_symbols))
    diagnostics.append(
        f"proof_evidence_status={SIGNATURE_PROBE_PROOF_EVIDENCE_STATUS}"
    )
    diagnostics.append(
        "boundary=signature probe/proof-body routing is blocked until an exact "
        "candidate artifact exists"
    )
    return diagnostics


def _signature_probe_source(source: str, packet: Mapping[str, Any]) -> str:
    del packet
    return source


def _signature_probe_reached_proof_body(
    diagnostics: tuple[str, ...],
    *,
    packet: Mapping[str, Any],
) -> bool:
    text = "\n".join(diagnostics)
    lowered = text.lower()
    formal_environment_error_markers = (
        "unknown identifier",
        "unknown constant",
        "function expected at",
        "failed to synthesize",
        "invalid field notation",
        "application type mismatch",
        "type mismatch",
    )
    if any(marker in lowered for marker in formal_environment_error_markers):
        return False
    missing_symbols = _str_list(packet.get("missing_formal_symbols", []) or [])
    typeclass_blockers = _str_list(packet.get("typeclass_blockers", []) or [])
    for symbol in missing_symbols:
        if symbol and re.search(rf"\b{re.escape(symbol)}\b", text) and (
            "unknown" in lowered or "function expected" in lowered
        ):
            return False
    for blocker in typeclass_blockers:
        if blocker and blocker in text and "failed to synthesize" in lowered:
            return False
    if "unsolved goals" in lowered:
        return True
    if "fail_if_success" in lowered and "error" in lowered:
        return True
    return False


def _classify_signature_probe_failure(diagnostics: tuple[str, ...]) -> str:
    text = "\n".join(diagnostics).lower()
    if not diagnostics:
        return ""
    if "timed out" in text or "timeout" in text:
        return "local_lean_timeout"
    if "unknown identifier" in text or "unknown constant" in text or "function expected" in text:
        return "formal_environment_symbol_missing"
    if "failed to synthesize" in text:
        return "formal_environment_instance_missing"
    if "unsolved goals" in text:
        return "proof_body_incomplete"
    if "invalid 'import' command" in text or "unknown module prefix" in text:
        return "lean_import_environment_missing"
    if "object file" in text and "does not exist" in text and ".olean" in text:
        return "lean_import_environment_missing"
    return "signature_probe_local_lean_failed_unclassified"


def _run_local_lean(
    lean_file: Path,
    *,
    lean_command: tuple[str, ...],
    lean_project: Path | None,
    timeout_s: int,
) -> tuple[bool, int, tuple[str, ...]]:
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


def _lean_command(lean_project: Path | None) -> tuple[str, ...]:
    if lean_project is not None and shutil.which("lake") is not None:
        return ("lake", "env", "lean")
    if shutil.which("lean") is not None:
        return ("lean",)
    return ()


def _safe_file_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return stem or "source_theorem_signature_probe"


def _export_proof_body_work_orders(
    *,
    repair_packets: list[Mapping[str, Any]],
    signature_probe_result: Mapping[str, Any] | None,
    out_dir: Path,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    packets_by_id = {
        str(packet.get("repair_packet_id", "") or ""): packet
        for packet in repair_packets
        if str(packet.get("repair_packet_id", "") or "")
    }
    rows: list[dict[str, Any]] = []
    if signature_probe_result:
        probe_rows = signature_probe_result.get("rows", [])
        if isinstance(probe_rows, list):
            for probe_row in probe_rows:
                if not isinstance(probe_row, Mapping):
                    continue
                if not bool(probe_row.get("signature_typecheck_reached_proof_body")):
                    continue
                repair_packet_id = str(probe_row.get("repair_packet_id", "") or "")
                packet = packets_by_id.get(repair_packet_id, {})
                rows.append(_proof_body_work_order(probe_row, packet))
    rows_path = out_dir / "exact_source_theorem_proof_body_work_orders.jsonl"
    _write_jsonl(rows_path, rows)
    manifest_path = out_dir / "exact_source_theorem_proof_body_work_order_manifest.json"
    manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyWorkOrderManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_body_work_orders_jsonl": str(rows_path),
        "n_proof_body_work_orders": len(rows),
        "target_theorem_names": list(
            dict.fromkeys(
                str(row.get("target_theorem_name", "") or "")
                for row in rows
                if str(row.get("target_theorem_name", "") or "")
            )
        ),
        "n_signature_probes_reached_proof_body": sum(
            1
            for row in rows
            if row.get("source_signature_probe_status")
            == "SIGNATURE_PROBE_REACHED_PROOF_BODY_NOT_PROOF"
        ),
        "n_proof_body_work_orders_from_pseudo_formal": sum(
            1 for row in rows if _has_pseudo_formal_origin(row)
        ),
        "n_proof_body_work_orders_from_formalizer_pf_component_gate": sum(
            1 for row in rows if _has_formalizer_pf_component_gate_origin(row)
        ),
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": (
            _formalizer_pf_component_gate_exact_rows_jsonl_paths(rows)
        ),
        "proof_evidence_status": PROOF_BODY_WORK_ORDER_PROOF_EVIDENCE_STATUS,
        "boundary": PROOF_BODY_WORK_ORDER_BOUNDARY,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "proof_body_work_order_manifest": manifest_path,
        "proof_body_work_orders_jsonl": rows_path,
        "n_proof_body_work_orders": len(rows),
        "n_proof_body_work_orders_from_pseudo_formal": manifest[
            "n_proof_body_work_orders_from_pseudo_formal"
        ],
        "n_proof_body_work_orders_from_formalizer_pf_component_gate": manifest[
            "n_proof_body_work_orders_from_formalizer_pf_component_gate"
        ],
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": manifest[
            "formalizer_pf_component_gate_exact_rows_jsonl_paths"
        ],
        "rows": rows,
        "proof_evidence_status": PROOF_BODY_WORK_ORDER_PROOF_EVIDENCE_STATUS,
        "boundary": PROOF_BODY_WORK_ORDER_BOUNDARY,
    }


def _proof_body_work_order(
    probe_row: Mapping[str, Any],
    repair_packet: Mapping[str, Any],
) -> dict[str, Any]:
    target_theorem_name = str(
        probe_row.get("target_theorem_name")
        or repair_packet.get("target_theorem_name", "")
        or ""
    )
    source_target_provenance = dict(
        repair_packet.get("source_theorem_target_provenance", {}) or {}
    )
    question_id = str(
        repair_packet.get("question_id", "")
        or source_target_provenance.get("question_id", "")
        or source_target_provenance.get("source_theorem_question_id", "")
        or ""
    )
    question_title = str(repair_packet.get("question_title", "") or "")
    semantic_alignment_constraints = _str_list(
        repair_packet.get("semantic_alignment_constraints", [])
        or source_target_provenance.get("semantic_alignment_constraints", [])
        or []
    )
    semantic_alignment_blockers = _str_list(
        repair_packet.get("semantic_alignment_blockers", []) or []
    )
    source_theorem_kernel_evidence_eligible = bool(
        repair_packet.get(
            "source_theorem_kernel_evidence_eligible",
            not semantic_alignment_blockers,
        )
    ) and not semantic_alignment_blockers
    target_lean_declaration = str(
        repair_packet.get("target_lean_declaration", "")
        or source_target_provenance.get("target_lean_declaration", "")
        or target_theorem_name
    )
    diagnostics = _str_list(probe_row.get("diagnostics", []) or [])
    proof_body_goal_excerpt = _goal_excerpt(diagnostics)
    open_environment_symbols = _str_list(
        repair_packet.get("missing_formal_symbols", []) or []
    )
    open_environment_typeclass_blockers = _str_list(
        repair_packet.get("typeclass_blockers", []) or []
    )
    proof_body_attempts = (
        []
        if open_environment_symbols or open_environment_typeclass_blockers
        else _proof_body_repair_attempts(
            row=repair_packet,
            primary_diagnostic=probe_row,
        )
    )
    proof_body_attempt_source = str(
        repair_packet.get("proof_body_attempt_source", "")
        or probe_row.get("proof_body_attempt_source", "")
        or ""
    )
    if proof_body_attempts and not proof_body_attempt_source:
        proof_body_attempt_source = "upstream_llm_or_prover_proposal"
    elif not proof_body_attempts:
        proof_body_attempt_source = (
            "formal_environment_open_skip_tactic_attempts"
            if open_environment_symbols or open_environment_typeclass_blockers
            else "llm_prover_generation_required"
        )
    target_ids = _target_ids_from_work_order(
        repair_packet or probe_row,
        fallback_target=target_theorem_name,
    )
    exact_semantic_context = _exact_semantic_definition_context(
        repair_packet,
        probe_row,
    )
    work_order_id = "exact_source_theorem_proof_body_work_order:" + stable_hash(
        [
            probe_row.get("signature_probe_id", ""),
            repair_packet.get("source_work_order_id", ""),
            target_theorem_name,
            target_ids,
            probe_row.get("signature_probe_artifact_path", ""),
        ]
    )[:20]
    return {
        "schema_version": 1,
        "artifact_kind": PROOF_BODY_WORK_ORDER_ARTIFACT_KIND,
        **exact_semantic_context,
        "work_order_id": work_order_id,
        "source_repair_packet_id": str(repair_packet.get("repair_packet_id", "") or ""),
        "source_work_order_id": str(repair_packet.get("source_work_order_id", "") or ""),
        "source_signature_probe_id": str(probe_row.get("signature_probe_id", "") or ""),
        "source_signature_probe_status": str(
            probe_row.get("signature_probe_status", "") or ""
        ),
        "question_id": question_id,
        "question_title": question_title,
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "target_theorem_goal_ids": list(target_ids),
        "target_lean_declaration": target_lean_declaration,
        "source_theorem_target_known": bool(
            repair_packet.get("source_theorem_target_known", False)
            or source_target_provenance.get("source_theorem_target_known", False)
        ),
        "source_theorem_target_provenance": source_target_provenance,
        "exact_semantic_definition_context": exact_semantic_context,
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "source_theorem_kernel_evidence_eligible": (
            source_theorem_kernel_evidence_eligible
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": _str_list(
            repair_packet.get("kernel_verified_source_to_bridge_premise_derivation_ids", [])
            or []
        ),
        "verified_source_to_bridge_premise_derivation_artifact_paths": _str_list(
            repair_packet.get(
                "verified_source_to_bridge_premise_derivation_artifact_paths", []
            )
            or []
        ),
        "verified_source_to_bridge_premise_derivation_declarations": _str_list(
            repair_packet.get("verified_source_to_bridge_premise_derivation_declarations", [])
            or []
        ),
        "verified_source_to_bridge_premise_derivation_signature_excerpts": _str_list(
            repair_packet.get(
                "verified_source_to_bridge_premise_derivation_signature_excerpts",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_work_order_ids": _str_list(
            repair_packet.get(
                "kernel_verified_theorem_reduction_closure_work_order_ids",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_declarations": _str_list(
            repair_packet.get(
                "kernel_verified_theorem_reduction_closure_declarations",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_signature_excerpts": _str_list(
            repair_packet.get(
                "kernel_verified_theorem_reduction_closure_signature_excerpts",
                [],
            )
            or []
        ),
        "verified_theorem_reduction_closure_artifact_paths": _str_list(
            repair_packet.get(
                "verified_theorem_reduction_closure_artifact_paths",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_target_ids": _str_list(
            repair_packet.get(
                "kernel_verified_theorem_reduction_closure_target_ids",
                [],
            )
            or []
        ),
        "source_candidate_artifact_path": str(
            probe_row.get("source_candidate_artifact_path", "")
            or repair_packet.get("candidate_artifact_path", "")
            or ""
        ),
        "signature_probe_artifact_path": str(
            probe_row.get("signature_probe_artifact_path", "") or ""
        ),
        "proof_body_failure_classification": str(
            probe_row.get("failure_classification", "") or ""
        ),
        "proof_body_goal_diagnostics": diagnostics[:24],
        "proof_body_goal_excerpt": proof_body_goal_excerpt,
        "compiler_feedback": {
            "provider": "local.source_theorem_signature_probe",
            "checked": bool(probe_row.get("local_lean_checked", False)),
            "returncode": int(probe_row.get("returncode", -1) or 0),
            "diagnostics": diagnostics[:24],
            "role": (
                "Lean compiler diagnostics are context for the next LLM/OpenProver "
                "candidate-generation turn, not static proof-strategy rules or proof "
                "evidence."
            ),
        },
        "proof_body_attempts": proof_body_attempts,
        "proof_body_attempt_source": proof_body_attempt_source,
        "proof_body_generation_contract": llm_proof_body_generation_contract(),
        "proof_body_attempt_boundary": (
            "Proof-body attempts may only be explicit upstream agent/provider "
            "proposals. When none are supplied, proof_body_attempts stays empty "
            "and the LLM/OpenProver compiler-feedback contract must generate "
            "candidates. Candidates are not proof evidence unless the exact source "
            "theorem passes local Lean/AXLE."
        ),
        "already_repaired_environment": {
            "missing_formal_symbols": open_environment_symbols,
            "typeclass_blockers": open_environment_typeclass_blockers,
            "signature_typecheck_reached_proof_body": bool(
                probe_row.get("signature_typecheck_reached_proof_body")
            ),
        },
        "proofengineer_next_actions": [
            "inspect the signature_probe_artifact_path proof goal",
            "replace only the AI_STAT_EVOLVE_BLOCK proof body with a non-placeholder proof",
            "reuse existing kernel-verified bridge/reduction lemmas when available",
            "search Mathlib/StatInference/local Lean sources before inventing helper lemmas",
            "preserve source theorem target provenance and semantic alignment constraints",
            "rerun local Lean/AXLE on the repaired exact source theorem artifact",
        ],
        "forbidden_actions": [
            "do not change the theorem statement without a separate semantic review work order",
            "do not add axioms, sorry, admit, unsafe, or a helper lemma restating the target",
            "do not count the signature probe or this work order as proof evidence",
        ],
        "acceptance_gate": (
            "local Lean/AXLE verifier manifest records source_theorem_kernel_verified=true "
            "for the exact source theorem candidate"
        ),
        "proof_evidence_status": PROOF_BODY_WORK_ORDER_PROOF_EVIDENCE_STATUS,
        "boundary": PROOF_BODY_WORK_ORDER_BOUNDARY,
    }


def _goal_excerpt(diagnostics: list[str]) -> list[str]:
    if not diagnostics:
        return []
    for index, line in enumerate(diagnostics):
        if "unsolved goals" in line.lower():
            return diagnostics[index : index + 18]
    return diagnostics[:18]


def _export_proof_body_execution_queue(
    *,
    proof_body_work_order_result: Mapping[str, Any],
    out_dir: Path,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir = out_dir / "candidate_artifacts"
    transcript_dir = out_dir / "execution_transcripts"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.mkdir(parents=True, exist_ok=True)
    work_orders = proof_body_work_order_result.get("rows", [])
    rows: list[dict[str, Any]] = []
    if isinstance(work_orders, list):
        for work_order in work_orders:
            if isinstance(work_order, Mapping):
                rows.append(
                    _proof_body_execution_queue_row(
                        work_order,
                        candidate_dir=candidate_dir,
                        transcript_dir=transcript_dir,
                    )
                )
    rows_path = out_dir / "exact_source_theorem_proof_body_execution_queue.jsonl"
    _write_jsonl(rows_path, rows)
    manifest_path = out_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    manifest = {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_body_execution_queue_jsonl": str(rows_path),
        "candidate_artifacts_dir": str(candidate_dir),
        "execution_transcripts_dir": str(transcript_dir),
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
        "n_source_theorem_proof_body_adapter_context_rows": sum(
            1
            for row in rows
            if row.get("source_theorem_proof_body_adapter_feedback_available")
            or row.get("source_theorem_proof_body_adapter_kernel_verified")
            or row.get("kernel_verified_source_theorem_proof_body_adapter_ids")
        ),
        "n_source_theorem_proof_body_adapter_kernel_verified_context_rows": sum(
            1
            for row in rows
            if row.get("source_theorem_proof_body_adapter_kernel_verified")
        ),
        "n_kernel_verified_source_to_bridge_premise_derivation_context_rows": sum(
            1
            for row in rows
            if row.get("kernel_verified_source_to_bridge_premise_derivation_ids")
            or row.get("verified_source_to_bridge_premise_derivation_artifact_paths")
            or row.get("verified_source_to_bridge_premise_derivation_declarations")
        ),
        "n_execution_queue_rows_from_pseudo_formal": sum(
            1 for row in rows if _has_pseudo_formal_origin(row)
        ),
        "n_execution_queue_rows_from_formalizer_pf_component_gate": sum(
            1 for row in rows if _has_formalizer_pf_component_gate_origin(row)
        ),
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": (
            _formalizer_pf_component_gate_exact_rows_jsonl_paths(rows)
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": list(
            dict.fromkeys(
                str(premise_id).strip()
                for row in rows
                for premise_id in _str_list(
                    row.get("kernel_verified_source_to_bridge_premise_derivation_ids")
                    or []
                )
                if str(premise_id).strip()
            )
        ),
        "proof_evidence_status": PROOF_BODY_EXECUTION_QUEUE_PROOF_EVIDENCE_STATUS,
        "boundary": PROOF_BODY_EXECUTION_QUEUE_BOUNDARY,
        "rows": rows,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "proof_body_execution_queue_manifest": manifest_path,
        "proof_body_execution_queue_jsonl": rows_path,
        "n_execution_queue_rows": len(rows),
        "n_ready": manifest["n_ready"],
        "n_live_goal_requests": manifest["n_live_goal_requests"],
        "n_live_goal_location_ready": manifest["n_live_goal_location_ready"],
        "n_source_theorem_proof_body_adapter_context_rows": manifest[
            "n_source_theorem_proof_body_adapter_context_rows"
        ],
        "n_source_theorem_proof_body_adapter_kernel_verified_context_rows": manifest[
            "n_source_theorem_proof_body_adapter_kernel_verified_context_rows"
        ],
        "n_kernel_verified_source_to_bridge_premise_derivation_context_rows": manifest[
            "n_kernel_verified_source_to_bridge_premise_derivation_context_rows"
        ],
        "n_execution_queue_rows_from_pseudo_formal": manifest[
            "n_execution_queue_rows_from_pseudo_formal"
        ],
        "n_execution_queue_rows_from_formalizer_pf_component_gate": manifest[
            "n_execution_queue_rows_from_formalizer_pf_component_gate"
        ],
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": manifest[
            "formalizer_pf_component_gate_exact_rows_jsonl_paths"
        ],
        "kernel_verified_source_to_bridge_premise_derivation_ids": manifest[
            "kernel_verified_source_to_bridge_premise_derivation_ids"
        ],
        "rows": rows,
        "proof_evidence_status": PROOF_BODY_EXECUTION_QUEUE_PROOF_EVIDENCE_STATUS,
        "boundary": PROOF_BODY_EXECUTION_QUEUE_BOUNDARY,
    }


def export_exact_source_theorem_proof_body_repair_execution_queue(
    *,
    proof_body_repair_work_orders_jsonl: Path,
    out_dir: Path,
) -> dict[str, object]:
    """Export executor queue rows directly from runtime proof-body repair orders.

    Runtime can learn that an exact source theorem candidate already reaches the
    proof body but still has unsolved goals. In that state there is no need to
    re-enter the formal-environment bridge; ProofEngineer should consume the
    reached candidate artifact directly and attempt a narrow proof-body repair.
    """

    work_orders = [
        _proof_body_repair_execution_work_order(row)
        for row in _read_jsonl(proof_body_repair_work_orders_jsonl)
        if _is_exact_source_theorem_proof_body_repair_work_order(row)
    ]
    result = _export_proof_body_execution_queue(
        proof_body_work_order_result={"rows": work_orders},
        out_dir=out_dir,
    )
    manifest_path = Path(str(result.get("proof_body_execution_queue_manifest", "")))
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["source_proof_body_repair_work_orders_jsonl"] = str(
            proof_body_repair_work_orders_jsonl
        )
        manifest["n_source_proof_body_repair_work_orders"] = len(work_orders)
        manifest["queue_source_mode"] = "source_theorem_exact_proof_body_repair"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
    result["source_proof_body_repair_work_orders_jsonl"] = (
        proof_body_repair_work_orders_jsonl
    )
    result["n_source_proof_body_repair_work_orders"] = len(work_orders)
    result["queue_source_mode"] = "source_theorem_exact_proof_body_repair"
    return result


def _is_exact_source_theorem_proof_body_repair_work_order(
    row: Mapping[str, Any],
) -> bool:
    return (
        str(row.get("proof_mode", "") or "")
        == "source_theorem_exact_proof_body_repair"
        or str(row.get("action_type", "") or "")
        == "repair_exact_source_theorem_candidate_proof_body"
        or str(row.get("runtime_queue_status", "") or "")
        == "PENDING_EXACT_SOURCE_THEOREM_PROOF_BODY_REPAIR"
    )


def _exact_semantic_definition_context(
    row: Mapping[str, Any],
    *fallback_rows: Mapping[str, Any],
) -> dict[str, Any]:
    context: dict[str, Any] = {}
    sources = _exact_semantic_context_sources(row, *fallback_rows)
    for key in EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS:
        for source in sources:
            value = source.get(key, None)
            if value in (None, "", [], {}):
                continue
            if isinstance(value, Mapping):
                context[key] = dict(value)
            elif isinstance(value, list):
                context[key] = list(value)
            else:
                context[key] = value
            break
    return context


def _exact_semantic_context_sources(
    row: Mapping[str, Any],
    *fallback_rows: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    sources: list[Mapping[str, Any]] = []
    for source in (row, *fallback_rows):
        if not isinstance(source, Mapping):
            continue
        sources.append(source)
        input_summary = source.get("input_summary", {})
        if isinstance(input_summary, Mapping) and input_summary:
            sources.append(input_summary)
        typechecked_candidate = source.get(
            "source_theorem_exact_semantic_definition_typechecked_candidate",
            {},
        )
        if isinstance(typechecked_candidate, Mapping) and typechecked_candidate:
            sources.append(typechecked_candidate)
    for source in list(sources):
        nested = source.get("exact_semantic_definition_context", {})
        if isinstance(nested, Mapping) and nested:
            sources.append(nested)
    return sources


def _has_pseudo_formal_origin(row: Mapping[str, Any]) -> bool:
    return bool(
        _row_context_value(row, "source_pseudo_formal_work_order_id").strip()
        or _has_formalizer_pf_component_gate_origin(row)
    )


def _has_formalizer_pf_component_gate_origin(row: Mapping[str, Any]) -> bool:
    return (
        _row_context_value(row, "source_component_gate")
        == "formalizer_pseudo_formal_packet_component_gate"
    )


def _formalizer_pf_component_gate_exact_rows_jsonl_paths(
    rows: list[Mapping[str, Any]],
) -> list[str]:
    paths: list[str] = []
    for row in rows:
        if not _has_formalizer_pf_component_gate_origin(row):
            continue
        path = _row_context_value(row, "source_component_gate_exact_rows_jsonl")
        if path and path not in paths:
            paths.append(path)
    return paths


def _row_context_value(row: Mapping[str, Any], key: str) -> str:
    sources: list[Mapping[str, Any]] = [row]
    nested = row.get("exact_semantic_definition_context", {})
    if isinstance(nested, Mapping):
        sources.append(nested)
    input_summary = row.get("input_summary", {})
    if isinstance(input_summary, Mapping):
        sources.append(input_summary)
        nested_input = input_summary.get("exact_semantic_definition_context", {})
        if isinstance(nested_input, Mapping):
            sources.append(nested_input)
    for source in sources:
        value = source.get(key, None)
        if value not in (None, "", [], {}):
            return str(value).strip()
    return ""


def _proof_body_repair_execution_work_order(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    diagnostics = [
        item
        for item in row.get("source_theorem_exact_proof_body_repair_diagnostics", [])
        or []
        if isinstance(item, Mapping)
    ]
    primary = diagnostics[0] if diagnostics else {}
    source_target_provenance = _source_theorem_target_provenance(row)
    target = str(
        row.get("proof_body_target_theorem_name", "")
        or primary.get("target_theorem_name", "")
        or row.get("target_theorem_name", "")
        or source_target_provenance.get("target_lean_declaration", "")
        or ""
    ).strip()
    if not target:
        target_goal_ids = row.get("target_theorem_goal_ids", []) or []
        if isinstance(target_goal_ids, list) and target_goal_ids:
            target = str(target_goal_ids[0] or "").strip()
    target_declaration = str(
        row.get("target_lean_declaration", "")
        or source_target_provenance.get("target_lean_declaration", "")
        or target
    ).strip()
    candidate_artifact_path = str(
        row.get("proof_body_candidate_artifact_path", "")
        or primary.get("candidate_artifact_path", "")
        or row.get("candidate_artifact_path", "")
        or ""
    ).strip()
    proof_body_goal_excerpt = _str_list(
        row.get("proof_body_goal_excerpt", [])
        or primary.get("proof_body_goal_excerpt", [])
        or []
    )[:18]
    proof_body_goal_diagnostics = _str_list(
        row.get("proof_body_goal_diagnostics", [])
        or primary.get("proof_body_goal_diagnostics", [])
        or row.get("diagnostics", [])
        or primary.get("diagnostics", [])
        or proof_body_goal_excerpt
    )[:24]
    proof_body_attempt_summaries = _str_list(
        row.get("proof_body_attempt_summaries", [])
        or primary.get("proof_body_attempt_summaries", [])
        or []
    )[:8]
    semantic_alignment_constraints = _str_list(
        row.get("semantic_alignment_constraints", [])
        or source_target_provenance.get("semantic_alignment_constraints", [])
        or []
    )
    semantic_alignment_blockers = _str_list(
        row.get("semantic_alignment_blockers", [])
        or primary.get("semantic_alignment_blockers", [])
        or []
    )
    source_theorem_kernel_evidence_eligible = bool(
        row.get(
            "source_theorem_kernel_evidence_eligible",
            primary.get(
                "source_theorem_kernel_evidence_eligible",
                not semantic_alignment_blockers,
            ),
        )
    ) and not semantic_alignment_blockers
    previous_proof_body_attempt_count = int(
        row.get(
            "proof_body_attempt_count",
            primary.get("proof_body_attempt_count", len(proof_body_attempt_summaries)),
        )
        or 0
    )
    adapter_artifact_paths = _str_list(
        row.get("verified_source_theorem_proof_body_adapter_artifact_paths", [])
        or primary.get("verified_source_theorem_proof_body_adapter_artifact_paths", [])
        or []
    )
    if not adapter_artifact_paths:
        adapter_path = str(
            row.get("adapter_candidate_artifact_path", "")
            or primary.get("adapter_candidate_artifact_path", "")
            or ""
        ).strip()
        if adapter_path:
            adapter_artifact_paths = [adapter_path]
    adapter_declarations = _str_list(
        row.get("verified_source_theorem_proof_body_adapter_declarations", [])
        or primary.get("verified_source_theorem_proof_body_adapter_declarations", [])
        or []
    )
    if not adapter_declarations:
        adapter_decl = str(
            row.get("adapter_declaration_name", "")
            or primary.get("adapter_declaration_name", "")
            or ""
        ).strip()
        if adapter_decl:
            adapter_declarations = [adapter_decl]
    kernel_verified_adapter_ids = _str_list(
        row.get("kernel_verified_source_theorem_proof_body_adapter_ids", [])
        or primary.get("kernel_verified_source_theorem_proof_body_adapter_ids", [])
        or []
    )
    adapter_kernel_verified = bool(
        row.get("source_theorem_proof_body_adapter_kernel_verified", False)
        or row.get("adapter_kernel_verified", False)
        or primary.get("adapter_kernel_verified", False)
        or kernel_verified_adapter_ids
    )
    proof_body_attempts = _proof_body_repair_attempts(
        row=row,
        primary_diagnostic=primary,
    )
    proof_body_attempt_source = str(
        row.get("proof_body_attempt_source", "")
        or primary.get("proof_body_attempt_source", "")
        or ""
    )
    if proof_body_attempts and not proof_body_attempt_source:
        proof_body_attempt_source = "upstream_llm_or_prover_proposal"
    elif not proof_body_attempts:
        proof_body_attempt_source = "llm_prover_generation_required"
    source_target_provenance.setdefault("target_lean_declaration", target_declaration)
    source_target_provenance.setdefault("source_theorem_target_known", True)
    target_ids = _target_ids_from_work_order(row, fallback_target=target)
    exact_semantic_context = _exact_semantic_definition_context(row, primary)
    return {
        "schema_version": 1,
        "artifact_kind": PROOF_BODY_WORK_ORDER_ARTIFACT_KIND,
        **exact_semantic_context,
        "work_order_id": str(row.get("work_order_id", "") or ""),
        "source_formal_target_id": str(row.get("source_formal_target_id", "") or ""),
        "target_theorem_name": target,
        "target_ids": target_ids,
        "target_theorem_goal_ids": list(target_ids),
        "target_lean_declaration": target_declaration,
        "source_theorem_target_known": bool(
            row.get("source_theorem_target_known", True)
            or source_target_provenance.get("source_theorem_target_known", False)
        ),
        "source_theorem_target_provenance": source_target_provenance,
        "question_id": str(
            row.get("question_id", "")
            or source_target_provenance.get("question_id", "")
            or source_target_provenance.get("source_theorem_question_id", "")
            or ""
        ),
        "question_title": str(row.get("question_title", "") or ""),
        "source_candidate_artifact_path": candidate_artifact_path,
        "signature_probe_artifact_path": candidate_artifact_path,
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "source_theorem_kernel_evidence_eligible": (
            source_theorem_kernel_evidence_eligible
        ),
        "already_repaired_environment": {
            "missing_formal_symbols": [],
            "typeclass_blockers": [],
            "signature_typecheck_reached_proof_body": bool(
                row.get("source_theorem_exact_proof_body_reached", False)
                or primary.get("proof_body_goal_reached", False)
                or row.get("proof_body_gate_status", "")
                == "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
                or primary.get("proof_body_gate_status", "")
                == "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
            ),
        },
        "proof_body_goal_diagnostics": proof_body_goal_diagnostics,
        "proof_body_goal_excerpt": proof_body_goal_excerpt,
        "previous_proof_body_attempt_summaries": proof_body_attempt_summaries,
        "previous_proof_body_attempt_count": previous_proof_body_attempt_count,
        "kernel_verified_theorem_reduction_closure_work_order_ids": _str_list(
            row.get(
                "kernel_verified_theorem_reduction_closure_work_order_ids",
                [],
            )
            or primary.get(
                "kernel_verified_theorem_reduction_closure_work_order_ids",
                [],
            )
        ),
        "kernel_verified_theorem_reduction_closure_declarations": _str_list(
            row.get("kernel_verified_theorem_reduction_closure_declarations", [])
            or primary.get(
                "kernel_verified_theorem_reduction_closure_declarations", []
            )
        ),
        "kernel_verified_theorem_reduction_closure_signature_excerpts": _str_list(
            row.get(
                "kernel_verified_theorem_reduction_closure_signature_excerpts",
                [],
            )
            or primary.get(
                "kernel_verified_theorem_reduction_closure_signature_excerpts",
                [],
            )
        ),
        "verified_theorem_reduction_closure_artifact_paths": _str_list(
            row.get("verified_theorem_reduction_closure_artifact_paths", [])
            or primary.get("verified_theorem_reduction_closure_artifact_paths", [])
        ),
        "kernel_verified_theorem_reduction_closure_target_ids": _str_list(
            row.get("kernel_verified_theorem_reduction_closure_target_ids", [])
            or primary.get("kernel_verified_theorem_reduction_closure_target_ids", [])
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": _str_list(
            row.get("kernel_verified_source_to_bridge_premise_derivation_ids", [])
            or primary.get("kernel_verified_source_to_bridge_premise_derivation_ids", [])
        ),
        "verified_source_to_bridge_premise_derivation_artifact_paths": _str_list(
            row.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
            or primary.get(
                "verified_source_to_bridge_premise_derivation_artifact_paths", []
            )
        ),
        "verified_source_to_bridge_premise_derivation_declarations": _str_list(
            row.get("verified_source_to_bridge_premise_derivation_declarations", [])
            or primary.get("verified_source_to_bridge_premise_derivation_declarations", [])
        ),
        "verified_source_to_bridge_premise_derivation_signature_excerpts": _str_list(
            row.get(
                "verified_source_to_bridge_premise_derivation_signature_excerpts",
                [],
            )
            or primary.get(
                "verified_source_to_bridge_premise_derivation_signature_excerpts",
                [],
            )
        ),
        "source_theorem_proof_body_adapter_feedback_available": bool(
            row.get("source_theorem_proof_body_adapter_feedback_available", False)
            or primary.get("source_theorem_proof_body_adapter_feedback_available", False)
            or adapter_artifact_paths
            or kernel_verified_adapter_ids
        ),
        "source_theorem_proof_body_adapter_kernel_verified": (
            adapter_kernel_verified
        ),
        "kernel_verified_source_theorem_proof_body_adapter_ids": (
            kernel_verified_adapter_ids
        ),
        "verified_source_theorem_proof_body_adapter_artifact_paths": (
            adapter_artifact_paths
        ),
        "verified_source_theorem_proof_body_adapter_declarations": (
            adapter_declarations
        ),
        "source_theorem_proof_body_adapter_context_boundary": str(
            row.get("source_theorem_proof_body_adapter_context_boundary", "")
            or primary.get("source_theorem_proof_body_adapter_context_boundary", "")
            or (
                "Kernel-verified source-to-bridge adapters are routing context "
                "for this exact proof-body retry only. They are not source-theorem "
                "proof evidence until the exact theorem itself kernel-checks."
            )
        ),
        "exact_semantic_definition_context": exact_semantic_context,
        "compiler_feedback": {
            "provider": "local.exact_source_theorem_proof_body_repair",
            "checked": bool(
                row.get("local_lean_checked", False)
                or primary.get("local_lean_checked", False)
            ),
            "returncode": int(
                row.get("returncode", primary.get("returncode", -1)) or 0
            ),
            "diagnostics": proof_body_goal_diagnostics,
            "role": (
                "Lean compiler diagnostics are context for the next LLM/OpenProver "
                "candidate-generation turn, not static proof-strategy rules or proof "
                "evidence."
            ),
        },
        "proof_body_attempts": proof_body_attempts,
        "proof_body_attempt_source": proof_body_attempt_source,
        "proof_body_generation_contract": llm_proof_body_generation_contract(),
        "proof_body_attempt_boundary": (
            "Proof-body attempts may only be explicit upstream agent/provider "
            "proposals. When none are supplied, proof_body_attempts stays empty "
            "and the LLM/OpenProver compiler-feedback contract must generate "
            "candidates. No candidate counts as proof until local Lean/AXLE "
            "verifies the exact declaration."
        ),
        "proofengineer_next_actions": [
            "inspect the reached Lean proof goal",
            "request LLM/OpenProver proof candidates using compiler feedback when no upstream candidates were supplied",
            "reuse verified bridge/helper lemmas without changing the exact theorem statement",
            *(
                [
                    "use the kernel-verified source-to-bridge adapter context when discharging bridge premises",
                ]
                if adapter_kernel_verified
                else []
            ),
            "replace only the proof body and rerun local Lean/AXLE",
        ],
        "forbidden_actions": [
            "do not change the theorem statement",
            "do not add sorry/admit/axiom/unsafe",
            "do not add a helper lemma that assumes or restates the target theorem",
        ],
        "acceptance_gate": str(row.get("acceptance_gate", "") or ""),
        "proof_evidence_status": PROOF_BODY_WORK_ORDER_PROOF_EVIDENCE_STATUS,
        "boundary": PROOF_BODY_WORK_ORDER_BOUNDARY,
    }


def _proof_body_repair_attempts(
    *,
    row: Mapping[str, Any],
    primary_diagnostic: Mapping[str, Any],
) -> list[str]:
    explicit = _str_list(row.get("proof_body_attempts", []) or [])
    if explicit:
        return explicit[:8]
    diagnostic_attempts = _str_list(
        primary_diagnostic.get("proof_body_attempts", []) or []
    )
    if diagnostic_attempts:
        return diagnostic_attempts[:8]
    return []


def _proof_body_execution_queue_row(
    work_order: Mapping[str, Any],
    *,
    candidate_dir: Path,
    transcript_dir: Path,
) -> dict[str, Any]:
    work_order_id = str(work_order.get("work_order_id", "") or "")
    target = str(work_order.get("target_theorem_name", "") or "")
    expected_target_declaration = str(
        work_order.get("target_lean_declaration", "") or target
    )
    signature_artifact_path = str(work_order.get("signature_probe_artifact_path", "") or "")
    source_artifact_path = str(work_order.get("source_candidate_artifact_path", "") or "")
    source_target_provenance = dict(
        work_order.get("source_theorem_target_provenance", {}) or {}
    )
    question_id = str(
        work_order.get("question_id", "")
        or source_target_provenance.get("question_id", "")
        or source_target_provenance.get("source_theorem_question_id", "")
        or ""
    )
    question_title = str(work_order.get("question_title", "") or "")
    semantic_alignment_constraints = _str_list(
        work_order.get("semantic_alignment_constraints", [])
        or source_target_provenance.get("semantic_alignment_constraints", [])
        or []
    )
    semantic_alignment_blockers = _str_list(
        work_order.get("semantic_alignment_blockers", []) or []
    )
    source_theorem_kernel_evidence_eligible = bool(
        work_order.get(
            "source_theorem_kernel_evidence_eligible",
            not semantic_alignment_blockers,
        )
    ) and not semantic_alignment_blockers
    adapter_kernel_verified = bool(
        work_order.get("source_theorem_proof_body_adapter_kernel_verified", False)
    )
    kernel_verified_adapter_ids = _str_list(
        work_order.get("kernel_verified_source_theorem_proof_body_adapter_ids", [])
        or []
    )
    adapter_artifact_paths = _str_list(
        work_order.get("verified_source_theorem_proof_body_adapter_artifact_paths", [])
        or []
    )
    adapter_declarations = _str_list(
        work_order.get("verified_source_theorem_proof_body_adapter_declarations", [])
        or []
    )
    verified_premise_derivation_ids = _str_list(
        work_order.get("kernel_verified_source_to_bridge_premise_derivation_ids", [])
        or []
    )
    verified_premise_derivation_artifact_paths = _str_list(
        work_order.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
        or []
    )
    verified_premise_derivation_declarations = _str_list(
        work_order.get("verified_source_to_bridge_premise_derivation_declarations", [])
        or []
    )
    verified_premise_derivation_signature_excerpts = _str_list(
        work_order.get(
            "verified_source_to_bridge_premise_derivation_signature_excerpts",
            [],
        )
        or []
    )
    adapter_context_boundary = str(
        work_order.get("source_theorem_proof_body_adapter_context_boundary", "")
        or ""
    )
    closure_declarations = _str_list(
        work_order.get("kernel_verified_theorem_reduction_closure_declarations", [])
        or []
    )
    closure_work_order_ids = _str_list(
        work_order.get(
            "kernel_verified_theorem_reduction_closure_work_order_ids",
            [],
        )
        or []
    )
    closure_signature_excerpts = _str_list(
        work_order.get(
            "kernel_verified_theorem_reduction_closure_signature_excerpts",
            [],
        )
        or []
    )
    closure_artifact_paths = _str_list(
        work_order.get("verified_theorem_reduction_closure_artifact_paths", [])
        or []
    )
    closure_target_ids = _str_list(
        work_order.get("kernel_verified_theorem_reduction_closure_target_ids", [])
        or []
    )
    compiler_feedback = work_order.get("compiler_feedback", {})
    if not isinstance(compiler_feedback, Mapping):
        compiler_feedback = {}
    proof_body_generation_contract = work_order.get(
        "proof_body_generation_contract",
        llm_proof_body_generation_contract(),
    )
    if not isinstance(proof_body_generation_contract, Mapping):
        proof_body_generation_contract = llm_proof_body_generation_contract()
    target_ids = _target_ids_from_work_order(work_order, fallback_target=target)
    source_theorem_target_known = bool(
        work_order.get("source_theorem_target_known", False)
        or source_target_provenance.get("source_theorem_target_known", False)
    )
    safe = _safe_file_stem(target or work_order_id)
    queue_id = "exact_source_theorem_proof_body_execution_queue:" + stable_hash(
        [work_order_id, target, signature_artifact_path]
    )[:20]
    candidate_artifact_path = candidate_dir / f"{safe}_proof_body_attempt.lean"
    transcript_path = transcript_dir / f"{safe}_proof_body_attempt.jsonl"
    location = _lean_goal_location(Path(signature_artifact_path))
    target_identity_errors = _target_identity_errors(
        expected_target_declaration=expected_target_declaration,
        location=location,
    )
    source_theorem_target_identity_status = _source_theorem_target_identity_status(
        source_theorem_target_known=source_theorem_target_known,
        target_identity_errors=target_identity_errors,
        expected_target_lean_declaration=expected_target_declaration,
        target_lean_declaration=str(location["target_lean_declaration"]),
    )
    exact_semantic_context = _exact_semantic_definition_context(work_order)
    live_ready = (
        bool(location["target_lean_file"] and location["target_lean_line"])
        and not target_identity_errors
    )
    status = (
        "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
        if live_ready
        else (
            "BLOCKED_EXACT_SOURCE_PROOF_BODY_TARGET_IDENTITY"
            if target_identity_errors
            else "BLOCKED_EXACT_SOURCE_PROOF_BODY_TARGET_LOCATION"
        )
    )
    live_request = (
        _proof_body_live_proof_state_request(
            queue_id=queue_id,
            work_order=work_order,
            location=location,
        )
        if live_ready
        else {}
    )
    return {
        "schema_version": 1,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
        **exact_semantic_context,
        "execution_queue_id": queue_id,
        "source_work_order_id": work_order_id,
        "source_signature_probe_id": str(
            work_order.get("source_signature_probe_id", "") or ""
        ),
        "question_id": question_id,
        "question_title": question_title,
        "target_theorem_name": target,
        "target_ids": target_ids,
        "target_theorem_goal_ids": list(target_ids),
        "expected_target_lean_declaration": expected_target_declaration,
        "source_theorem_target_known": source_theorem_target_known,
        "source_theorem_target_identity_status": source_theorem_target_identity_status,
        "source_theorem_target_provenance": source_target_provenance,
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "source_theorem_kernel_evidence_eligible": (
            source_theorem_kernel_evidence_eligible
        ),
        "owner_agent": "FormalizerProofEngineer",
        "action_class": "fill_exact_source_theorem_proof_body",
        "source_candidate_artifact_path": source_artifact_path,
        "signature_probe_artifact_path": signature_artifact_path,
        "candidate_artifact_path": str(candidate_artifact_path),
        "execution_transcript_path": str(transcript_path),
        "target_lean_file": str(location["target_lean_file"]),
        "target_lean_line": int(location["target_lean_line"]),
        "target_lean_column": int(location["target_lean_column"]),
        "target_lean_declaration": str(location["target_lean_declaration"]),
        "target_identity_status": (
            "TARGET_DECLARATION_MATCHED"
            if not target_identity_errors
            else "TARGET_DECLARATION_MISMATCH"
        ),
        "target_identity_errors": target_identity_errors,
        "live_goal_location_ready": live_ready,
        "live_proof_state_request": live_request,
        "already_repaired_environment": dict(
            work_order.get("already_repaired_environment", {}) or {}
        ),
        "kernel_verified_theorem_reduction_closure_work_order_ids": (
            closure_work_order_ids
        ),
        "kernel_verified_theorem_reduction_closure_declarations": (
            closure_declarations
        ),
        "kernel_verified_theorem_reduction_closure_signature_excerpts": (
            closure_signature_excerpts
        ),
        "verified_theorem_reduction_closure_artifact_paths": closure_artifact_paths,
        "kernel_verified_theorem_reduction_closure_target_ids": closure_target_ids,
        "source_theorem_proof_body_adapter_feedback_available": bool(
            work_order.get("source_theorem_proof_body_adapter_feedback_available", False)
            or adapter_kernel_verified
            or kernel_verified_adapter_ids
            or adapter_artifact_paths
        ),
        "source_theorem_proof_body_adapter_kernel_verified": (
            adapter_kernel_verified
        ),
        "kernel_verified_source_theorem_proof_body_adapter_ids": (
            kernel_verified_adapter_ids
        ),
        "verified_source_theorem_proof_body_adapter_artifact_paths": (
            adapter_artifact_paths
        ),
        "verified_source_theorem_proof_body_adapter_declarations": (
            adapter_declarations
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": (
            verified_premise_derivation_ids
        ),
        "verified_source_to_bridge_premise_derivation_artifact_paths": (
            verified_premise_derivation_artifact_paths
        ),
        "verified_source_to_bridge_premise_derivation_declarations": (
            verified_premise_derivation_declarations
        ),
        "verified_source_to_bridge_premise_derivation_signature_excerpts": (
            verified_premise_derivation_signature_excerpts
        ),
        "source_theorem_proof_body_adapter_context_boundary": (
            adapter_context_boundary
        ),
        "exact_semantic_definition_context": exact_semantic_context,
        "proof_body_goal_diagnostics": list(
            work_order.get("proof_body_goal_diagnostics", []) or []
        ),
        "proof_body_goal_excerpt": list(work_order.get("proof_body_goal_excerpt", []) or []),
        "previous_proof_body_attempt_count": int(
            work_order.get("previous_proof_body_attempt_count", 0) or 0
        ),
        "previous_proof_body_attempt_summaries": list(
            work_order.get("previous_proof_body_attempt_summaries", []) or []
        ),
        "proof_body_attempts": _str_list(work_order.get("proof_body_attempts", []) or []),
        "proof_body_attempt_source": str(
            work_order.get("proof_body_attempt_source", "") or ""
        ),
        "proof_body_attempt_boundary": str(
            work_order.get("proof_body_attempt_boundary", "") or ""
        ),
        "compiler_feedback": dict(compiler_feedback),
        "proof_body_generation_contract": dict(
            proof_body_generation_contract
        ),
        "proofengineer_next_actions": list(
            work_order.get("proofengineer_next_actions", []) or []
        ),
        "command_plan": [
            "inspect live_proof_state_request and compiler_feedback before editing",
            "when proof_body_attempts is empty, request candidates through proof_body_generation_contract",
            "copy signature_probe_artifact_path to candidate_artifact_path",
            "replace only the AI_STAT_EVOLVE_BLOCK proof body",
            "run local Lean/AXLE on candidate_artifact_path",
            "write execution transcript with tactics, diagnostics, and verifier result",
        ],
        "required_static_checks": [
            "no sorry/admit/axiom/unsafe tokens",
            "theorem statement and declaration header unchanged",
            "helper lemmas do not restate the target theorem",
        ],
        "required_dynamic_checks": [
            "lean_goal",
            "lean_diagnostic_messages",
            "lean_local_search",
            "local Lean or AXLE kernel verification",
        ]
        + (["lean_multi_attempt"] if work_order.get("proof_body_attempts") else []),
        "output_contract": [
            "candidate artifact at candidate_artifact_path",
            "JSONL transcript at execution_transcript_path",
            "agent/provider lineage for every generated proof-body candidate",
            "verifier manifest proving whether source_theorem_kernel_verified=true",
            "no proof claim unless local Lean/AXLE accepts the exact theorem",
        ],
        "forbidden_actions": list(work_order.get("forbidden_actions", []) or []),
        "promotion_gate": str(work_order.get("acceptance_gate", "") or ""),
        "execution_status": status,
        "proof_evidence_status": PROOF_BODY_EXECUTION_QUEUE_PROOF_EVIDENCE_STATUS,
        "boundary": PROOF_BODY_EXECUTION_QUEUE_BOUNDARY,
    }


def _target_identity_errors(
    *,
    expected_target_declaration: str,
    location: Mapping[str, object],
) -> list[str]:
    expected = str(expected_target_declaration or "").strip()
    observed = str(location.get("target_lean_declaration", "") or "").strip()
    if expected and observed and expected != observed:
        return [
            "signature probe declaration "
            f"`{observed}` does not match expected exact source target `{expected}`"
        ]
    return []


def _source_theorem_target_identity_status(
    *,
    source_theorem_target_known: bool,
    target_identity_errors: list[str] | tuple[str, ...],
    expected_target_lean_declaration: str,
    target_lean_declaration: str,
) -> str:
    if target_identity_errors:
        return "TARGET_DECLARATION_MISMATCH"
    if source_theorem_target_known:
        return "SOURCE_THEOREM_TARGET_KNOWN"
    expected = str(expected_target_lean_declaration or "").strip()
    observed = str(target_lean_declaration or "").strip()
    if expected and observed and expected == observed:
        return "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    if observed:
        return "DECLARATION_FOUND_SOURCE_THEOREM_TARGET_UNPROMOTED"
    return "SOURCE_THEOREM_TARGET_UNKNOWN"


def _lean_goal_location(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "target_lean_file": "",
            "target_lean_line": 0,
            "target_lean_column": 0,
            "target_lean_declaration": "",
        }
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return {
            "target_lean_file": "",
            "target_lean_line": 0,
            "target_lean_column": 0,
            "target_lean_declaration": "",
        }
    target_line = 0
    target_declaration = ""
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == "-- AI_STAT_EVOLVE_BLOCK_START" and index < len(lines):
            target_line = index + 1
        if not target_declaration and stripped.startswith(("theorem ", "lemma ")):
            parts = stripped.split()
            if len(parts) >= 2:
                target_declaration = parts[1]
    if target_line <= 0:
        for index, line in enumerate(lines, start=1):
            if ":= by" in line:
                target_line = min(index + 1, len(lines))
                break
    return {
        "target_lean_file": str(path),
        "target_lean_line": target_line,
        "target_lean_column": 3 if target_line > 0 else 0,
        "target_lean_declaration": target_declaration,
    }


def _proof_body_live_proof_state_request(
    *,
    queue_id: str,
    work_order: Mapping[str, Any],
    location: Mapping[str, object],
) -> dict[str, object]:
    source_target_provenance = dict(
        work_order.get("source_theorem_target_provenance", {}) or {}
    )
    question_id = str(
        work_order.get("question_id", "")
        or source_target_provenance.get("question_id", "")
        or source_target_provenance.get("source_theorem_question_id", "")
        or ""
    )
    question_title = str(work_order.get("question_title", "") or "")
    target_ids = _target_ids_from_work_order(
        work_order,
        fallback_target=str(
            work_order.get("target_theorem_name", "")
            or work_order.get("target_lean_declaration", "")
            or ""
        ),
    )
    semantic_alignment_constraints = _str_list(
        work_order.get("semantic_alignment_constraints", [])
        or source_target_provenance.get("semantic_alignment_constraints", [])
        or []
    )
    semantic_alignment_blockers = _str_list(
        work_order.get("semantic_alignment_blockers", []) or []
    )
    source_theorem_kernel_evidence_eligible = bool(
        work_order.get(
            "source_theorem_kernel_evidence_eligible",
            not semantic_alignment_blockers,
        )
    ) and not semantic_alignment_blockers
    source_theorem_target_known = bool(
        work_order.get("source_theorem_target_known", False)
        or source_target_provenance.get("source_theorem_target_known", False)
    )
    source_theorem_target_identity_status = _source_theorem_target_identity_status(
        source_theorem_target_known=source_theorem_target_known,
        target_identity_errors=(),
        expected_target_lean_declaration=str(
            work_order.get("target_lean_declaration", "")
            or work_order.get("target_theorem_name", "")
            or ""
        ),
        target_lean_declaration=str(location.get("target_lean_declaration", "")),
    )
    proof_body_attempts = _str_list(work_order.get("proof_body_attempts", []) or [])
    proof_body_attempt_source = str(
        work_order.get("proof_body_attempt_source", "") or ""
    )
    if proof_body_attempts and not proof_body_attempt_source:
        proof_body_attempt_source = "upstream_llm_or_prover_proposal"
    elif not proof_body_attempts and not proof_body_attempt_source:
        proof_body_attempt_source = "llm_prover_generation_required"
    compiler_feedback = work_order.get("compiler_feedback", {})
    if not isinstance(compiler_feedback, Mapping):
        compiler_feedback = {}
    proof_body_generation_contract = work_order.get(
        "proof_body_generation_contract",
        llm_proof_body_generation_contract(),
    )
    if not isinstance(proof_body_generation_contract, Mapping):
        proof_body_generation_contract = llm_proof_body_generation_contract()
    request_id = "exact_source_theorem_proof_body_live_goal:" + stable_hash(
        [
            queue_id,
            location.get("target_lean_file", ""),
            location.get("target_lean_line", 0),
            location.get("target_lean_declaration", ""),
        ]
    )[:20]
    exact_semantic_context = _exact_semantic_definition_context(work_order)
    return {
        "schema_version": 1,
        "request_id": request_id,
        **exact_semantic_context,
        "source_work_order_id": str(work_order.get("work_order_id", "") or ""),
        "question_id": question_id,
        "question_title": question_title,
        "provider_preferences": (
            "lean_lsp_mcp",
            "local_lean_proof_state_adapter",
            "local.lake_env_lean",
        ),
        "mcp_tool_calls": [
            {
                "tool": tool,
                "arguments": _live_proof_state_tool_arguments(
                    tool=tool,
                    location=location,
                    proof_body_attempts=proof_body_attempts,
                ),
            }
            for tool in (
                ["lean_goal", "lean_diagnostic_messages", "lean_local_search"]
                + (["lean_multi_attempt"] if proof_body_attempts else [])
            )
        ],
        "target_lean_file": str(location.get("target_lean_file", "")),
        "target_lean_line": int(location.get("target_lean_line", 0) or 0),
        "target_lean_column": int(location.get("target_lean_column", 0) or 0),
        "target_lean_declaration": str(location.get("target_lean_declaration", "")),
        "target_ids": target_ids,
        "target_theorem_goal_ids": target_ids,
        "expected_target_lean_declaration": str(
            work_order.get("target_lean_declaration", "")
            or work_order.get("target_theorem_name", "")
            or ""
        ),
        "source_theorem_target_known": source_theorem_target_known,
        "source_theorem_target_identity_status": source_theorem_target_identity_status,
        "source_theorem_target_provenance": source_target_provenance,
        "semantic_alignment_constraints": semantic_alignment_constraints,
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "source_theorem_kernel_evidence_eligible": (
            source_theorem_kernel_evidence_eligible
        ),
        "source_theorem_proof_body_adapter_feedback_available": bool(
            work_order.get("source_theorem_proof_body_adapter_feedback_available", False)
            or work_order.get("source_theorem_proof_body_adapter_kernel_verified", False)
            or work_order.get(
                "kernel_verified_source_theorem_proof_body_adapter_ids",
                [],
            )
            or work_order.get(
                "verified_source_theorem_proof_body_adapter_artifact_paths",
                [],
            )
        ),
        "source_theorem_proof_body_adapter_kernel_verified": bool(
            work_order.get("source_theorem_proof_body_adapter_kernel_verified", False)
        ),
        "kernel_verified_source_theorem_proof_body_adapter_ids": _str_list(
            work_order.get("kernel_verified_source_theorem_proof_body_adapter_ids", [])
            or []
        ),
        "verified_source_theorem_proof_body_adapter_artifact_paths": _str_list(
            work_order.get(
                "verified_source_theorem_proof_body_adapter_artifact_paths",
                [],
            )
            or []
        ),
        "verified_source_theorem_proof_body_adapter_declarations": _str_list(
            work_order.get(
                "verified_source_theorem_proof_body_adapter_declarations",
                [],
            )
            or []
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": _str_list(
            work_order.get("kernel_verified_source_to_bridge_premise_derivation_ids", [])
            or []
        ),
        "verified_source_to_bridge_premise_derivation_artifact_paths": _str_list(
            work_order.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
            or []
        ),
        "verified_source_to_bridge_premise_derivation_declarations": _str_list(
            work_order.get("verified_source_to_bridge_premise_derivation_declarations", [])
            or []
        ),
        "verified_source_to_bridge_premise_derivation_signature_excerpts": _str_list(
            work_order.get(
                "verified_source_to_bridge_premise_derivation_signature_excerpts",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_work_order_ids": _str_list(
            work_order.get(
                "kernel_verified_theorem_reduction_closure_work_order_ids",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_declarations": _str_list(
            work_order.get(
                "kernel_verified_theorem_reduction_closure_declarations",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_signature_excerpts": _str_list(
            work_order.get(
                "kernel_verified_theorem_reduction_closure_signature_excerpts",
                [],
            )
            or []
        ),
        "verified_theorem_reduction_closure_artifact_paths": _str_list(
            work_order.get(
                "verified_theorem_reduction_closure_artifact_paths",
                [],
            )
            or []
        ),
        "kernel_verified_theorem_reduction_closure_target_ids": _str_list(
            work_order.get(
                "kernel_verified_theorem_reduction_closure_target_ids",
                [],
            )
            or []
        ),
        "source_theorem_proof_body_adapter_context_boundary": str(
            work_order.get("source_theorem_proof_body_adapter_context_boundary", "")
            or ""
        ),
        "exact_semantic_definition_context": exact_semantic_context,
        "proof_body_goal_diagnostics": list(
            work_order.get("proof_body_goal_diagnostics", []) or []
        ),
        "proof_body_goal_excerpt": list(work_order.get("proof_body_goal_excerpt", []) or []),
        "previous_proof_body_attempt_count": int(
            work_order.get("previous_proof_body_attempt_count", 0) or 0
        ),
        "previous_proof_body_attempt_summaries": list(
            work_order.get("previous_proof_body_attempt_summaries", []) or []
        ),
        "proof_body_attempts": proof_body_attempts,
        "proof_body_attempt_source": proof_body_attempt_source,
        "compiler_feedback": dict(compiler_feedback),
        "proof_body_generation_contract": dict(
            proof_body_generation_contract
        ),
        "proof_evidence_status": "LIVE_PROOF_STATE_REQUEST_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": (
            "Live proof-state requests provide diagnostic/search evidence only. "
            "They are not theorem proof evidence."
        ),
    }


def _live_proof_state_tool_arguments(
    *,
    tool: str,
    location: Mapping[str, object],
    proof_body_attempts: list[str],
) -> dict[str, object]:
    arguments: dict[str, object] = {
        "file": str(location.get("target_lean_file", "")),
        "line": int(location.get("target_lean_line", 0) or 0),
        "column": int(location.get("target_lean_column", 0) or 0),
        "declaration": str(location.get("target_lean_declaration", "")),
    }
    if tool == "lean_multi_attempt":
        arguments["snippets"] = proof_body_attempts
    return arguments


def _default_repair_tasks(
    *,
    missing_symbols: list[str],
    typeclass_blockers: list[str],
) -> list[str]:
    tasks = [
        f"resolve Lean declaration/import or formal primitive `{symbol}`"
        for symbol in missing_symbols
    ]
    tasks.extend(
        f"repair exact source-theorem typeclass/coercion blocker `{blocker}`"
        for blocker in typeclass_blockers
    )
    tasks.append("rerun local Lean/AXLE artifact verifier before claiming proof")
    return tasks[:8]


def _export_runtime_learning_rows(
    *,
    repair_packets: list[Mapping[str, Any]],
    out_dir: Path,
    question_id: str,
    queue_path: Path,
    signature_probe_result: Mapping[str, Any] | None = None,
    proof_body_work_order_result: Mapping[str, Any] | None = None,
    proof_body_execution_queue_result: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for packet in repair_packets:
        packet_target_ids = _target_ids_from_work_order(
            packet,
            fallback_target=str(packet.get("target_theorem_name", "") or ""),
        )
        signature_probe_rows = _matching_signature_probe_rows(
            signature_probe_result,
            repair_packet_id=str(packet.get("repair_packet_id", "") or ""),
        )
        proof_body_work_orders = _matching_proof_body_work_orders(
            proof_body_work_order_result,
            repair_packet_id=str(packet.get("repair_packet_id", "") or ""),
        )
        proof_body_execution_queue_rows = _matching_proof_body_execution_queue_rows(
            proof_body_execution_queue_result,
            work_order_ids=[
                str(row.get("work_order_id", "") or "")
                for row in proof_body_work_orders
                if isinstance(row, Mapping)
            ],
        )
        candidate_materialization_required = any(
            bool(row.get("candidate_materialization_required", False))
            or str(row.get("failure_classification", "") or "")
            in {
                CANDIDATE_MATERIALIZATION_REQUIRED_FAILURE,
                CANDIDATE_ARTIFACT_MISSING_FAILURE,
            }
            for row in signature_probe_rows
            if isinstance(row, Mapping)
        )
        candidate_materialization_statuses = list(
            dict.fromkeys(
                str(row.get("signature_probe_status", "") or "")
                for row in signature_probe_rows
                if isinstance(row, Mapping)
                and (
                    bool(row.get("candidate_materialization_required", False))
                    or str(row.get("failure_classification", "") or "")
                    in {
                        CANDIDATE_MATERIALIZATION_REQUIRED_FAILURE,
                        CANDIDATE_ARTIFACT_MISSING_FAILURE,
                    }
                )
                and str(row.get("signature_probe_status", "") or "")
            )
        )
        rows.append(
            {
                "schema_version": 1,
                "question_id": str(question_id or packet.get("question_id", "") or ""),
                "learning_task": "source_theorem_formal_environment_repair_feedback",
                "target_ids": packet_target_ids,
                "target_theorem_goal_ids": list(packet_target_ids),
                "input_summary": {
                    "trigger": "SOURCE_THEOREM_FORMAL_ENVIRONMENT_REPAIR_REQUIRED",
                    "source_work_order_id": str(packet.get("source_work_order_id", "") or ""),
                    "repair_packet_id": str(packet.get("repair_packet_id", "") or ""),
                    "target_theorem_name": str(packet.get("target_theorem_name", "") or ""),
                    "target_ids": packet_target_ids,
                    "target_theorem_goal_ids": list(packet_target_ids),
                    "target_lean_declaration": str(
                        packet.get("target_lean_declaration", "") or ""
                    ),
                    "source_theorem_target_known": bool(
                        packet.get("source_theorem_target_known", False)
                    ),
                    "source_theorem_target_provenance": dict(
                        packet.get("source_theorem_target_provenance", {}) or {}
                    ),
                    "semantic_alignment_constraints": list(
                        packet.get("semantic_alignment_constraints", []) or []
                    ),
                    "candidate_artifact_path": str(packet.get("candidate_artifact_path", "") or ""),
                    "failure_classification": str(packet.get("failure_classification", "") or ""),
                    "missing_formal_symbols": list(packet.get("missing_formal_symbols", []) or []),
                    "typeclass_blockers": list(packet.get("typeclass_blockers", []) or []),
                    "formal_environment_declaration_hints": list(
                        packet.get("formal_environment_declaration_hints", []) or []
                    ),
                    "statement_repair_hints": list(
                        packet.get("statement_repair_hints", []) or []
                    ),
                    "lean_signature_probe_plan": dict(
                        packet.get("lean_signature_probe_plan", {}) or {}
                    ),
                    "signature_probe_rows": signature_probe_rows,
                    "candidate_materialization_required": (
                        candidate_materialization_required
                    ),
                    "candidate_materialization_statuses": (
                        candidate_materialization_statuses
                    ),
                    "candidate_materialization_contract": (
                        CANDIDATE_MATERIALIZATION_CONTRACT
                        if candidate_materialization_required
                        else ""
                    ),
                    "signature_probe_manifest": str(
                        signature_probe_result.get("signature_probe_manifest_path", "")
                        if signature_probe_result
                        else ""
                    ),
                    "proof_body_work_orders": proof_body_work_orders,
                    "proof_body_work_order_manifest": str(
                        proof_body_work_order_result.get(
                            "proof_body_work_order_manifest",
                            "",
                        )
                        if proof_body_work_order_result
                        else ""
                    ),
                    "proof_body_execution_queue_rows": proof_body_execution_queue_rows,
                    "proof_body_execution_queue_manifest": str(
                        proof_body_execution_queue_result.get(
                            "proof_body_execution_queue_manifest",
                            "",
                        )
                        if proof_body_execution_queue_result
                        else ""
                    ),
                    "recommended_repair_tasks": list(
                        packet.get("recommended_repair_tasks", []) or []
                    ),
                    "repair_packets_jsonl": "",
                    "source_queue_jsonl": str(queue_path),
                    "source_theorem_kernel_verified": False,
                },
                "target_theorem_name": str(packet.get("target_theorem_name", "") or ""),
                "target_lean_declaration": str(packet.get("target_lean_declaration", "") or ""),
                "source_theorem_target_known": bool(
                    packet.get("source_theorem_target_known", False)
                ),
                "source_theorem_target_provenance": dict(
                    packet.get("source_theorem_target_provenance", {}) or {}
                ),
                "semantic_alignment_constraints": list(
                    packet.get("semantic_alignment_constraints", []) or []
                ),
                "source_work_order_id": str(packet.get("source_work_order_id", "") or ""),
                "repair_packet_id": str(packet.get("repair_packet_id", "") or ""),
                "candidate_materialization_required": (
                    candidate_materialization_required
                ),
                "candidate_materialization_statuses": (
                    candidate_materialization_statuses
                ),
                "candidate_materialization_contract": (
                    CANDIDATE_MATERIALIZATION_CONTRACT
                    if candidate_materialization_required
                    else ""
                ),
                "missing_formal_symbols": list(packet.get("missing_formal_symbols", []) or []),
                "typeclass_blockers": list(packet.get("typeclass_blockers", []) or []),
                "target_behavior": (
                    "Use this as ProofEngineer runtime memory to repair exact source-theorem "
                    "formal environments. Do not count it as proof evidence."
                ),
                "acceptance_gate": (
                    "Only a later local Lean/AXLE artifact verifier row with kernel evidence can "
                    "promote the repaired candidate."
                ),
                "boundary": BOUNDARY,
                "proof_evidence_status": "FORMAL_ENVIRONMENT_REPAIR_LEARNING_NOT_PROOF_EVIDENCE",
            }
        )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(learning_path, rows)
    for row in rows:
        if isinstance(row.get("input_summary"), dict):
            row["input_summary"]["repair_packets_jsonl"] = str(
                out_dir.parent / "source_theorem_formal_environment_repair_packets.jsonl"
            )
    _write_jsonl(learning_path, rows)
    export_manifest = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremFormalEnvironmentRuntimeLearningExportManifest",
        "source_queue_jsonl": str(queue_path),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_learning_rows": len(rows),
        "target_theorem_names": list(
            dict.fromkeys(
                str(row.get("target_theorem_name", "") or "")
                for row in rows
                if str(row.get("target_theorem_name", "") or "")
            )
        ),
        "target_ids": list(
            dict.fromkeys(
                target_id
                for row in rows
                for target_id in row.get("target_ids", []) or []
                if str(target_id).strip()
            )
        ),
        "missing_formal_symbols": list(
            dict.fromkeys(
                symbol
                for row in rows
                for symbol in row.get("missing_formal_symbols", []) or []
            )
        ),
        "typeclass_blockers": list(
            dict.fromkeys(
                blocker
                for row in rows
                for blocker in row.get("typeclass_blockers", []) or []
            )
        ),
        "proof_evidence_status": "FORMAL_ENVIRONMENT_REPAIR_LEARNING_NOT_PROOF_EVIDENCE",
        "boundary": BOUNDARY,
        "n_proof_body_work_orders": int(
            proof_body_work_order_result.get("n_proof_body_work_orders", 0)
            if proof_body_work_order_result
            else 0
        ),
        "proof_body_work_order_proof_evidence_status": str(
            proof_body_work_order_result.get("proof_evidence_status", "")
            if proof_body_work_order_result
            else ""
        ),
        "n_proof_body_execution_queue_rows": int(
            proof_body_execution_queue_result.get("n_execution_queue_rows", 0)
            if proof_body_execution_queue_result
            else 0
        ),
        "proof_body_execution_queue_proof_evidence_status": str(
            proof_body_execution_queue_result.get("proof_evidence_status", "")
            if proof_body_execution_queue_result
            else ""
        ),
    }
    manifest_out = out_dir / "source_theorem_formal_environment_runtime_learning_export_manifest.json"
    manifest_out.write_text(
        json.dumps(export_manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "rows": rows,
        "n_learning_rows": len(rows),
        "runtime_learning_rows_jsonl": learning_path,
        "export_manifest_path": manifest_out,
        "export_manifest": export_manifest,
    }


def _matching_signature_probe_rows(
    signature_probe_result: Mapping[str, Any] | None,
    *,
    repair_packet_id: str,
) -> list[dict[str, Any]]:
    if not signature_probe_result:
        return []
    rows = signature_probe_result.get("rows", [])
    if not isinstance(rows, list):
        return []
    return [
        dict(row)
        for row in rows
        if isinstance(row, Mapping)
        and str(row.get("repair_packet_id", "") or "") == repair_packet_id
    ]


def _matching_proof_body_work_orders(
    proof_body_work_order_result: Mapping[str, Any] | None,
    *,
    repair_packet_id: str,
) -> list[dict[str, Any]]:
    if not proof_body_work_order_result:
        return []
    rows = proof_body_work_order_result.get("rows", [])
    if not isinstance(rows, list):
        return []
    return [
        dict(row)
        for row in rows
        if isinstance(row, Mapping)
        and str(row.get("source_repair_packet_id", "") or "") == repair_packet_id
    ]


def _matching_proof_body_execution_queue_rows(
    proof_body_execution_queue_result: Mapping[str, Any] | None,
    *,
    work_order_ids: list[str],
) -> list[dict[str, Any]]:
    if not proof_body_execution_queue_result or not work_order_ids:
        return []
    rows = proof_body_execution_queue_result.get("rows", [])
    if not isinstance(rows, list):
        return []
    allowed = set(work_order_ids)
    return [
        dict(row)
        for row in rows
        if isinstance(row, Mapping)
        and str(row.get("source_work_order_id", "") or "") in allowed
    ]


def _str_list(values: object) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return []
    return [str(value) for value in values if str(value).strip()]


def _target_ids_from_work_order(
    work_order: Mapping[str, Any],
    *,
    fallback_target: str = "",
) -> list[str]:
    sources: list[Mapping[str, Any]] = [work_order]
    input_summary = (
        work_order.get("input_summary", {})
        if isinstance(work_order.get("input_summary", {}), Mapping)
        else {}
    )
    if input_summary:
        sources.append(input_summary)
    for source in tuple(sources):
        nested = source.get("source_theorem_target_provenance", {})
        if isinstance(nested, Mapping):
            sources.append(nested)
        context = source.get("source_theorem_target_context", {})
        if isinstance(context, Mapping):
            sources.append(context)

    def _values(raw: Any) -> list[str]:
        if isinstance(raw, Mapping):
            return [str(key).strip() for key in raw.keys() if str(key).strip()]
        if isinstance(raw, str):
            return [raw.strip()] if raw.strip() else []
        if isinstance(raw, (list, tuple, set)):
            return [str(value).strip() for value in raw if str(value).strip()]
        text = str(raw or "").strip()
        return [text] if text else []

    target_ids: list[str] = []
    for source in sources:
        for key in ("target_ids", "target_id", "source_theorem_goal_id"):
            target_ids.extend(_values(source.get(key, [])))

    if not target_ids:
        for source in sources:
            target_ids.extend(_values(source.get("target_theorem_goal_ids", [])))

    fallback = str(fallback_target or "").strip()
    if not target_ids and fallback:
        target_ids = [fallback]
    return list(dict.fromkeys(target_ids))


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
            json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )

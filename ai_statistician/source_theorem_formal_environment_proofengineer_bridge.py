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
from .research_architect import KERNEL_PROOF_BOUNDARY


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
SIGNATURE_PROBE_BOUNDARY = (
    "Source-theorem formal-environment signature probes are local Lean typecheck "
    "diagnostics for repaired candidate environments. They may show that missing "
    "symbols or typeclass blockers were cleared far enough to reach the proof body, "
    "but they are not artifact proof, source-theorem proof, or semantic promotion "
    "evidence."
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


@dataclass(frozen=True)
class SourceTheoremFormalEnvironmentSignatureProbeRow:
    schema_version: int
    artifact_kind: str
    signature_probe_id: str
    repair_packet_id: str
    source_work_order_id: str
    target_theorem_name: str
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
        raise ValueError(
            "runtime manifest does not list "
            "runtime_source_theorem_formal_environment_work_orders_jsonl"
        )
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
    declaration_hints = _formal_environment_declaration_hints(missing_symbols)
    statement_hints = _statement_repair_hints(typeclass_blockers)
    signature_probe_plan = _lean_signature_probe_plan(
        missing_symbols=missing_symbols,
        typeclass_blockers=typeclass_blockers,
        candidate_artifact_path=candidate_artifact_path,
    )
    repair_packet_id = "source_theorem_formal_environment_repair_packet:" + stable_hash(
        [
            work_order_id,
            target_theorem_name,
            candidate_artifact_path,
            missing_symbols,
            typeclass_blockers,
        ]
    )[:20]
    return {
        "schema_version": 1,
        "artifact_kind": REPAIR_PACKET_ARTIFACT_KIND,
        "repair_packet_id": repair_packet_id,
        "source_work_order_id": work_order_id,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "candidate_artifact_path": candidate_artifact_path,
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


def _formal_environment_declaration_hints(missing_symbols: list[str]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for symbol in missing_symbols:
        normalized = symbol.strip()
        if normalized == "Exchangeable":
            hints.append(
                {
                    "symbol": normalized,
                    "search_queries": [
                        "Exchangeable probability measure indexed random variables",
                        "exchangeable Fin family MeasureTheory probability",
                        "List.Perm distribution invariant MeasureTheory",
                    ],
                    "preferred_resolution": (
                        "reuse an existing Mathlib/StatInference exchangeability declaration "
                        "if one exists"
                    ),
                    "signature_probe_fallback": (
                        "for a typecheck-only repair artifact, introduce a local predicate "
                        "`Exchangeable (P : Measure Ω) (s : Fin (m + 1) → Ω → ℝ) : Prop` "
                        "only as an unproved semantic primitive; do not count it as proof "
                        "or source-theorem evidence"
                    ),
                    "promotion_blocker": (
                        "the source theorem is not semantically promoted until this predicate "
                        "is mapped to a reviewed library definition or kernel-proved primitive"
                    ),
                }
            )
        elif normalized == "orderStat":
            hints.append(
                {
                    "symbol": normalized,
                    "search_queries": [
                        "order statistic finite family real Lean",
                        "Finset sort nth order statistic",
                        "quantile order statistic conformal Lean",
                    ],
                    "preferred_resolution": (
                        "reuse or formalize a finite-sample order statistic over "
                        "`Fin (m + 1)` before proving coverage"
                    ),
                    "signature_probe_fallback": (
                        "for a typecheck-only repair artifact, introduce a local function "
                        "`orderStat (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ` "
                        "as a semantic placeholder; it must remain outside proof evidence"
                    ),
                    "promotion_blocker": (
                        "theorem closure still requires the rank/order-statistic semantics "
                        "bridge, not just the symbol declaration"
                    ),
                }
            )
        else:
            hints.append(
                {
                    "symbol": normalized,
                    "search_queries": [
                        f"{normalized} Mathlib",
                        f"{normalized} StatInference",
                        f"{normalized} local Lean source",
                    ],
                    "preferred_resolution": (
                        "search existing Lean sources before drafting a new primitive"
                    ),
                    "signature_probe_fallback": (
                        "if no declaration exists, draft the narrowest local declaration "
                        "needed to typecheck the source theorem and mark it as unproved"
                    ),
                    "promotion_blocker": (
                        "local declaration drafts are routing evidence only until reviewed "
                        "and kernel verified in the target library"
                    ),
                }
            )
    return hints


def _statement_repair_hints(typeclass_blockers: list[str]) -> list[dict[str, str]]:
    hints: list[dict[str, str]] = []
    for blocker in typeclass_blockers:
        if "HSub ℕ ℝ ENNReal" in blocker:
            hints.append(
                {
                    "blocker": blocker,
                    "diagnosis": (
                        "the exact candidate compares a `Measure` value in `ENNReal` with "
                        "`1 - alpha : ℝ`; Lean is trying to subtract a real from a natural "
                        "or coerce the wrong side of the inequality"
                    ),
                    "repair_hint": (
                        "probe a typed statement whose probability lower bound is "
                        "`ENNReal.ofReal (1 - alpha)` while keeping the source theorem "
                        "marked as a semantic repair draft, not a proved exact theorem"
                    ),
                    "example_target_shape": (
                        "P {ω | s (Fin.last m) ω ≤ q_hat ω} ≥ ENNReal.ofReal (1 - alpha)"
                    ),
                    "honesty_boundary": (
                        "changing the codomain/coercion shape can make the Lean statement "
                        "typecheck, but it is not source-theorem evidence until semantic "
                        "review and local Lean/AXLE verification succeed"
                    ),
                }
            )
        else:
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
        "n_ok": sum(1 for row in rows if row.ok),
        "all_signature_probes_reached_proof_body": bool(rows)
        and all(row.signature_typecheck_reached_proof_body for row in rows),
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
    candidate_raw = str(packet.get("candidate_artifact_path", "") or "")
    candidate_path = Path(candidate_raw) if candidate_raw else Path()
    probe_id = "source_theorem_formal_environment_signature_probe:" + stable_hash(
        [repair_packet_id, candidate_raw, target_theorem_name]
    )[:20]
    probe_artifact_path = artifacts_dir / f"{_safe_file_stem(target_theorem_name or probe_id)}_signature_probe.lean"
    source = ""
    if not repair_packet_id:
        errors.append("repair_packet_id missing")
    if not candidate_raw:
        errors.append("candidate_artifact_path missing")
    elif not candidate_path.exists():
        errors.append(f"candidate artifact missing: {candidate_path}")
    else:
        try:
            source = candidate_path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"failed to read candidate artifact: {type(exc).__name__}: {exc}")
    if not errors:
        probe_source = _signature_probe_source(source, packet)
        probe_artifact_path.write_text(probe_source, encoding="utf-8")
    checked = False
    compiled = False
    returncode = -1
    diagnostics: tuple[str, ...] = ()
    if not lean_command:
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
    )


def _signature_probe_source(source: str, packet: Mapping[str, Any]) -> str:
    import_lines, body_lines = _split_import_lines(source)
    if not import_lines:
        import_lines = ["import Mathlib"]
    body = "\n".join(body_lines).strip()
    body = _apply_statement_repair_hints(body, packet)
    declaration_prelude = _signature_probe_declaration_prelude(
        _str_list(packet.get("missing_formal_symbols", []) or [])
    )
    metadata = {
        "repair_packet_id": packet.get("repair_packet_id", ""),
        "target_theorem_name": packet.get("target_theorem_name", ""),
        "proof_evidence_status": SIGNATURE_PROBE_PROOF_EVIDENCE_STATUS,
    }
    metadata_lines = "\n".join(
        f"-- {key}: {value}" for key, value in metadata.items() if value
    )
    return (
        "\n".join(import_lines)
        + "\n\n"
        + "/-!\n"
        + "Source-theorem formal-environment signature probe.\n"
        + "This file is a typecheck diagnostic artifact, not proof evidence.\n"
        + "Local placeholder declarations below are semantic repair drafts only.\n"
        + "-/\n\n"
        + "namespace AIStatisticianSourceTheoremSignatureProbe\n\n"
        + "noncomputable section\n\n"
        + f"{metadata_lines}\n\n"
        + declaration_prelude
        + ("\n\n" if declaration_prelude else "")
        + body
        + "\n\nend\n\n"
        + "end AIStatisticianSourceTheoremSignatureProbe\n"
    )


def _split_import_lines(source: str) -> tuple[list[str], list[str]]:
    imports: list[str] = []
    body: list[str] = []
    for line in source.splitlines():
        if line.strip().startswith("import "):
            if line.strip() not in imports:
                imports.append(line.strip())
        else:
            body.append(line)
    if imports and "import Mathlib" not in imports:
        imports.insert(0, "import Mathlib")
    return imports, body


def _signature_probe_declaration_prelude(missing_symbols: list[str]) -> str:
    declarations: list[str] = []
    if "Exchangeable" in missing_symbols:
        declarations.append(
            "def Exchangeable {Ω : Type _} [MeasurableSpace Ω] {m : ℕ}\n"
            "    (P : MeasureTheory.Measure Ω) (s : Fin (m + 1) → Ω → ℝ) : Prop := True"
        )
    if "orderStat" in missing_symbols:
        declarations.append(
            "def orderStat {Ω : Type _} {m : ℕ}\n"
            "    (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ := 0"
        )
    return "\n\n".join(declarations)


def _apply_statement_repair_hints(source: str, packet: Mapping[str, Any]) -> str:
    blockers = _str_list(packet.get("typeclass_blockers", []) or [])
    if any("HSub ℕ ℝ ENNReal" in blocker for blocker in blockers):
        source = re.sub(r"≥\s*1\s*-\s*alpha\b", "≥ ENNReal.ofReal (1 - alpha)", source)
    return source


def _signature_probe_reached_proof_body(
    diagnostics: tuple[str, ...],
    *,
    packet: Mapping[str, Any],
) -> bool:
    text = "\n".join(diagnostics)
    lowered = text.lower()
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
    diagnostics = _str_list(probe_row.get("diagnostics", []) or [])
    work_order_id = "exact_source_theorem_proof_body_work_order:" + stable_hash(
        [
            probe_row.get("signature_probe_id", ""),
            repair_packet.get("source_work_order_id", ""),
            target_theorem_name,
            probe_row.get("signature_probe_artifact_path", ""),
        ]
    )[:20]
    return {
        "schema_version": 1,
        "artifact_kind": PROOF_BODY_WORK_ORDER_ARTIFACT_KIND,
        "work_order_id": work_order_id,
        "source_repair_packet_id": str(repair_packet.get("repair_packet_id", "") or ""),
        "source_work_order_id": str(repair_packet.get("source_work_order_id", "") or ""),
        "source_signature_probe_id": str(probe_row.get("signature_probe_id", "") or ""),
        "source_signature_probe_status": str(
            probe_row.get("signature_probe_status", "") or ""
        ),
        "target_theorem_name": target_theorem_name,
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
        "proof_body_goal_excerpt": _goal_excerpt(diagnostics),
        "already_repaired_environment": {
            "missing_formal_symbols": list(
                repair_packet.get("missing_formal_symbols", []) or []
            ),
            "typeclass_blockers": list(repair_packet.get("typeclass_blockers", []) or []),
            "signature_typecheck_reached_proof_body": bool(
                probe_row.get("signature_typecheck_reached_proof_body")
            ),
        },
        "proofengineer_next_actions": [
            "inspect the signature_probe_artifact_path proof goal",
            "replace only the AI_STAT_EVOLVE_BLOCK proof body with a non-placeholder proof",
            "reuse existing kernel-verified conformal bridge lemmas when available",
            "search Mathlib/StatInference/local Lean sources before inventing helper lemmas",
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
        "n_live_goal_requests": manifest["n_live_goal_requests"],
        "rows": rows,
        "proof_evidence_status": PROOF_BODY_EXECUTION_QUEUE_PROOF_EVIDENCE_STATUS,
        "boundary": PROOF_BODY_EXECUTION_QUEUE_BOUNDARY,
    }


def _proof_body_execution_queue_row(
    work_order: Mapping[str, Any],
    *,
    candidate_dir: Path,
    transcript_dir: Path,
) -> dict[str, Any]:
    work_order_id = str(work_order.get("work_order_id", "") or "")
    target = str(work_order.get("target_theorem_name", "") or "")
    signature_artifact_path = str(work_order.get("signature_probe_artifact_path", "") or "")
    source_artifact_path = str(work_order.get("source_candidate_artifact_path", "") or "")
    safe = _safe_file_stem(target or work_order_id)
    queue_id = "exact_source_theorem_proof_body_execution_queue:" + stable_hash(
        [work_order_id, target, signature_artifact_path]
    )[:20]
    candidate_artifact_path = candidate_dir / f"{safe}_proof_body_attempt.lean"
    transcript_path = transcript_dir / f"{safe}_proof_body_attempt.jsonl"
    location = _lean_goal_location(Path(signature_artifact_path))
    live_ready = bool(location["target_lean_file"] and location["target_lean_line"])
    status = (
        "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
        if live_ready
        else "BLOCKED_EXACT_SOURCE_PROOF_BODY_TARGET_LOCATION"
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
        "execution_queue_id": queue_id,
        "source_work_order_id": work_order_id,
        "source_signature_probe_id": str(
            work_order.get("source_signature_probe_id", "") or ""
        ),
        "target_theorem_name": target,
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
        "live_goal_location_ready": live_ready,
        "live_proof_state_request": live_request,
        "already_repaired_environment": dict(
            work_order.get("already_repaired_environment", {}) or {}
        ),
        "proof_body_goal_excerpt": list(work_order.get("proof_body_goal_excerpt", []) or []),
        "proofengineer_next_actions": list(
            work_order.get("proofengineer_next_actions", []) or []
        ),
        "command_plan": [
            "inspect live_proof_state_request before editing",
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
            "lean_multi_attempt",
            "local Lean or AXLE kernel verification",
        ],
        "output_contract": [
            "candidate artifact at candidate_artifact_path",
            "JSONL transcript at execution_transcript_path",
            "verifier manifest proving whether source_theorem_kernel_verified=true",
            "no proof claim unless local Lean/AXLE accepts the exact theorem",
        ],
        "forbidden_actions": list(work_order.get("forbidden_actions", []) or []),
        "promotion_gate": str(work_order.get("acceptance_gate", "") or ""),
        "execution_status": status,
        "proof_evidence_status": PROOF_BODY_EXECUTION_QUEUE_PROOF_EVIDENCE_STATUS,
        "boundary": PROOF_BODY_EXECUTION_QUEUE_BOUNDARY,
    }


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
    request_id = "exact_source_theorem_proof_body_live_goal:" + stable_hash(
        [
            queue_id,
            location.get("target_lean_file", ""),
            location.get("target_lean_line", 0),
            location.get("target_lean_declaration", ""),
        ]
    )[:20]
    return {
        "schema_version": 1,
        "request_id": request_id,
        "source_work_order_id": str(work_order.get("work_order_id", "") or ""),
        "provider_preferences": (
            "lean_lsp_mcp",
            "local_lean_proof_state_adapter",
            "local.lake_env_lean",
        ),
        "mcp_tool_calls": [
            {
                "tool": tool,
                "arguments": {
                    "file": str(location.get("target_lean_file", "")),
                    "line": int(location.get("target_lean_line", 0) or 0),
                    "column": int(location.get("target_lean_column", 0) or 0),
                    "declaration": str(location.get("target_lean_declaration", "")),
                },
            }
            for tool in (
                "lean_goal",
                "lean_diagnostic_messages",
                "lean_local_search",
                "lean_multi_attempt",
            )
        ],
        "target_lean_file": str(location.get("target_lean_file", "")),
        "target_lean_line": int(location.get("target_lean_line", 0) or 0),
        "target_lean_column": int(location.get("target_lean_column", 0) or 0),
        "target_lean_declaration": str(location.get("target_lean_declaration", "")),
        "proof_body_goal_excerpt": list(work_order.get("proof_body_goal_excerpt", []) or []),
        "proof_evidence_status": "LIVE_PROOF_STATE_REQUEST_NOT_PROOF_EVIDENCE",
        "proof_evidence_boundary": (
            "Live proof-state requests provide diagnostic/search evidence only. "
            "They are not theorem proof evidence."
        ),
    }


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
        rows.append(
            {
                "schema_version": 1,
                "question_id": str(question_id or packet.get("question_id", "") or ""),
                "learning_task": "source_theorem_formal_environment_repair_feedback",
                "input_summary": {
                    "trigger": "SOURCE_THEOREM_FORMAL_ENVIRONMENT_REPAIR_REQUIRED",
                    "source_work_order_id": str(packet.get("source_work_order_id", "") or ""),
                    "repair_packet_id": str(packet.get("repair_packet_id", "") or ""),
                    "target_theorem_name": str(packet.get("target_theorem_name", "") or ""),
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
                "source_work_order_id": str(packet.get("source_work_order_id", "") or ""),
                "repair_packet_id": str(packet.get("repair_packet_id", "") or ""),
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

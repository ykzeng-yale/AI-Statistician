from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .research_architect import KERNEL_PROOF_BOUNDARY


ARTIFACT_KIND = "SourceTheoremFormalEnvironmentProofEngineerBridgeManifest"
REPAIR_PACKET_ARTIFACT_KIND = "SourceTheoremFormalEnvironmentRepairPacket"
BOUNDARY = (
    "Source-theorem formal-environment ProofEngineer bridge rows are repair "
    "routing artifacts. They identify missing Lean declarations, imports, and "
    "typeclass/coercion blockers for exact source-theorem candidates. They are "
    "not theorem proof, artifact proof, or source-theorem kernel evidence. Only "
    "a subsequent local Lean/AXLE verifier manifest with kernel_verified=true "
    "can promote any repaired artifact to proof evidence."
)


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
    learning_result = _export_runtime_learning_rows(
        repair_packets=repair_packets,
        out_dir=out_dir / "runtime_learning_export",
        question_id=question_id,
        queue_path=queue_path,
    )
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "source_runtime_dir": str(runtime_dir or ""),
        "source_queue_jsonl": str(queue_path),
        "repair_packets_jsonl": str(repair_packets_path),
        "runtime_learning_rows_jsonl": str(learning_result["runtime_learning_rows_jsonl"]),
        "runtime_learning_export_manifest": str(learning_result["export_manifest_path"]),
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
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for packet in repair_packets:
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


def _str_list(values: object) -> list[str]:
    if not isinstance(values, list):
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

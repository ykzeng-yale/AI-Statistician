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

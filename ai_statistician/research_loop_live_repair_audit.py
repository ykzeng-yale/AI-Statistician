from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .research_loop_repair_audit import ALLOWED_OWNERS, ALLOWED_TASK_TYPES


RESEARCH_LOOP_LIVE_REPAIR_AUDIT_SCHEMA_VERSION = 1

PROOF_REPAIR_TASK_TYPES = {
    "proof_bank_expansion_from_formal_gap",
    "lean_proof_repair_from_axle_error",
}


@dataclass(frozen=True)
class ResearchLoopLiveRepairRow:
    artifact_id: str
    question_id: str
    round: int
    source_action_id: str
    owner_agent: str
    trigger: str
    execution_status: str
    task_type: str
    live_repair_handler: str
    contract_ok: bool
    rerun_requested: bool
    kernel_verified: bool
    required_gate: str
    required_fields: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchLoopLiveRepairSftExample:
    schema_version: int
    example_id: str
    split: str
    task: str
    prompt: str
    completion: str
    question_id: str
    owner_agent: str
    task_type: str
    live_repair_handler: str
    tags: tuple[str, ...]


def audit_research_loop_live_repair_artifacts(
    loop_dir: Path,
    out_dir: Path | None = None,
    *,
    validation_fraction: float = 0.2,
) -> dict[str, object]:
    """Validate executed live-repair artifacts and export SFT examples.

    The repair-task audit validates *planned* work. This audit validates the
    executed artifacts that handlers returned, including proof-kernel evidence
    where applicable, so the loop can learn from repairs without promoting
    malformed or unverifiable records into training data.
    """

    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0.0, 1.0)")
    manifest_path = loop_dir / "research_loop_manifest.json"
    errors: list[str] = []
    manifest = _load_json(manifest_path, errors)
    artifact_path = Path(
        str(manifest.get("live_repair_artifacts_jsonl", loop_dir / "research_loop_live_repair_artifacts.jsonl"))
    )
    if not artifact_path.is_absolute() and not artifact_path.exists():
        artifact_path = loop_dir / artifact_path
    artifacts = _load_jsonl(artifact_path, errors)
    rows = [_row_for_artifact(artifact) for artifact in artifacts]
    usable_artifacts = [
        artifact for artifact, row in zip(artifacts, rows, strict=False) if row.ok and row.contract_ok
    ]
    examples = [_example_for_artifact(artifact, validation_fraction) for artifact in usable_artifacts]
    by_handler = Counter(row.live_repair_handler for row in rows)
    by_type = Counter(row.task_type for row in rows)
    by_status = Counter(row.execution_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": RESEARCH_LOOP_LIVE_REPAIR_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "loop_dir": str(loop_dir),
        "manifest": str(manifest_path),
        "live_repair_artifacts_jsonl": str(artifact_path),
        "n_artifacts": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "by_handler": dict(sorted(by_handler.items())),
        "by_type": dict(sorted(by_type.items())),
        "by_status": dict(sorted(by_status.items())),
        "n_contract_ok": sum(1 for row in rows if row.contract_ok),
        "n_rerun_requested": sum(1 for row in rows if row.rerun_requested),
        "n_kernel_verified": sum(1 for row in rows if row.kernel_verified),
        "n_sft_examples": len(examples),
        "n_train": sum(1 for row in examples if row.split == "train"),
        "n_validation": sum(1 for row in examples if row.split == "validation"),
        "rows": [asdict(row) for row in rows],
        "dataset_fingerprint": stable_hash([asdict(row) for row in examples]),
        "limitations": [
            "live repair artifacts prove or repair scoped loop actions, not full frontier statistical theorems",
            "proof repair artifacts are reusable only when kernel_verified=true and the proof-bank obligation remains in scope",
            "theory, algorithm, and simulator repair artifacts still require rerun evidence before becoming release claims",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        train_path = out_dir / "research_loop_live_repair_sft_train.jsonl"
        validation_path = out_dir / "research_loop_live_repair_sft_validation.jsonl"
        all_path = out_dir / "research_loop_live_repair_sft_all.jsonl"
        _write_jsonl(train_path, [row for row in examples if row.split == "train"])
        _write_jsonl(validation_path, [row for row in examples if row.split == "validation"])
        _write_jsonl(all_path, examples)
        payload.update(
            {
                "train_jsonl": str(train_path),
                "validation_jsonl": str(validation_path),
                "all_jsonl": str(all_path),
            }
        )
        (out_dir / "research_loop_live_repair_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "research_loop_live_repair_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse JSON {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"failed to parse JSONL {path}:{idx}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"JSONL row is not an object: {path}:{idx}")
    return rows


def _row_for_artifact(artifact_row: dict[str, Any]) -> ResearchLoopLiveRepairRow:
    errors: list[str] = []
    artifact_id = str(artifact_row.get("artifact_id", ""))
    question_id = str(artifact_row.get("question_id", ""))
    source_action_id = str(artifact_row.get("source_action_id", ""))
    owner_agent = str(artifact_row.get("owner_agent", ""))
    trigger = str(artifact_row.get("trigger", ""))
    execution_status = str(artifact_row.get("execution_status", ""))
    task_type = str(artifact_row.get("task_type", ""))
    live_repair_handler = str(artifact_row.get("live_repair_handler", ""))
    repair_contract_ok = artifact_row.get("repair_contract_ok") is True
    rerun_requested = artifact_row.get("rerun_requested") is True
    repair_artifact = artifact_row.get("repair_artifact") if isinstance(artifact_row.get("repair_artifact"), dict) else {}
    repair_contract = artifact_row.get("repair_contract") if isinstance(artifact_row.get("repair_contract"), dict) else {}
    required_fields = tuple(str(row) for row in repair_contract.get("required_fields", []) or [] if str(row))
    required_gate = str(repair_contract.get("required_gate", ""))
    kernel_verified = repair_artifact.get("kernel_verified") is True or artifact_row.get("kernel_verified") is True

    if int(artifact_row.get("schema_version", 0) or 0) != 1:
        errors.append("schema_version must be 1")
    if not artifact_id:
        errors.append("artifact_id missing")
    if not question_id:
        errors.append("question_id missing")
    if not source_action_id:
        errors.append("source_action_id missing")
    if owner_agent not in ALLOWED_OWNERS:
        errors.append("owner_agent invalid")
    if not trigger:
        errors.append("trigger missing")
    if not execution_status:
        errors.append("execution_status missing")
    if task_type not in ALLOWED_TASK_TYPES:
        errors.append("task_type invalid")
    if not live_repair_handler:
        errors.append("live_repair_handler missing")
    if not repair_contract_ok:
        errors.append("repair_contract_ok must be true for training-ready live artifacts")
    if artifact_row.get("repair_contract_errors"):
        errors.append("repair_contract_errors must be empty for training-ready live artifacts")
    if not repair_artifact:
        errors.append("repair_artifact missing")
    if not required_fields:
        errors.append("repair_contract.required_fields missing")
    if not required_gate:
        errors.append("repair_contract.required_gate missing")
    for field in required_fields:
        missing_values = (None, "", {}) if field == "proof_dependencies" else (None, "", [], {})
        if field not in repair_artifact or repair_artifact.get(field) in missing_values:
            errors.append(f"repair_artifact missing required field: {field}")
    if rerun_requested and not repair_contract_ok:
        errors.append("rerun_requested=true is forbidden when repair_contract_ok=false")
    if task_type in PROOF_REPAIR_TASK_TYPES:
        if "AXLE" not in required_gate and "verify_proof" not in required_gate:
            errors.append("proof repair artifact missing AXLE/verify_proof required gate")
        if repair_artifact.get("verification_strength") == "axle_lean_kernel" and not kernel_verified:
            errors.append("axle_lean_kernel repair artifact requires kernel_verified=true")
        if rerun_requested and not kernel_verified:
            errors.append("proof repair rerun requires kernel_verified=true")

    return ResearchLoopLiveRepairRow(
        artifact_id=artifact_id,
        question_id=question_id,
        round=int(artifact_row.get("round", 0) or 0),
        source_action_id=source_action_id,
        owner_agent=owner_agent,
        trigger=trigger,
        execution_status=execution_status,
        task_type=task_type,
        live_repair_handler=live_repair_handler,
        contract_ok=repair_contract_ok,
        rerun_requested=rerun_requested,
        kernel_verified=kernel_verified,
        required_gate=required_gate,
        required_fields=required_fields,
        ok=not errors,
        errors=tuple(errors),
    )


def _example_for_artifact(
    artifact_row: dict[str, Any],
    validation_fraction: float,
) -> ResearchLoopLiveRepairSftExample:
    completion = {
        "execution_status": artifact_row.get("execution_status"),
        "rerun_requested": artifact_row.get("rerun_requested", False),
        "repair_artifact": artifact_row.get("repair_artifact", {}),
        "repair_contract": artifact_row.get("repair_contract", {}),
    }
    prompt = "\n".join(
        [
            "You are a live repair agent for an AI Statistical Theory Lab.",
            "Given a failed proof/simulation loop action and output contract, produce a completed repair artifact.",
            "Return JSON only. Do not claim a Lean proof unless it has kernel verification evidence.",
            "",
            "Live repair request:",
            json.dumps(
                {
                    "question_id": artifact_row.get("question_id"),
                    "round": artifact_row.get("round"),
                    "source_action_id": artifact_row.get("source_action_id"),
                    "owner_agent": artifact_row.get("owner_agent"),
                    "trigger": artifact_row.get("trigger"),
                    "task_type": artifact_row.get("task_type"),
                    "live_repair_handler": artifact_row.get("live_repair_handler"),
                    "repair_contract": artifact_row.get("repair_contract"),
                },
                indent=2,
                default=str,
            ),
        ]
    )
    example_id = (
        f"loop_live_repair_sft:{artifact_row.get('artifact_id', '')}:"
        f"{stable_hash([prompt, completion])[:12]}"
    )
    return ResearchLoopLiveRepairSftExample(
        schema_version=RESEARCH_LOOP_LIVE_REPAIR_AUDIT_SCHEMA_VERSION,
        example_id=example_id,
        split=_split_for_example(example_id, validation_fraction),
        task="research_loop_live_repair_execution",
        prompt=prompt,
        completion=json.dumps(completion, sort_keys=True),
        question_id=str(artifact_row.get("question_id", "")),
        owner_agent=str(artifact_row.get("owner_agent", "")),
        task_type=str(artifact_row.get("task_type", "")),
        live_repair_handler=str(artifact_row.get("live_repair_handler", "")),
        tags=(
            "research_loop",
            "live_repair",
            str(artifact_row.get("owner_agent", "")),
            str(artifact_row.get("task_type", "")),
            str(artifact_row.get("live_repair_handler", "")),
        ),
    )


def _split_for_example(example_id: str, validation_fraction: float) -> str:
    if validation_fraction <= 0.0:
        return "train"
    bucket = int(stable_hash(example_id)[:8], 16) / 0xFFFFFFFF
    return "validation" if bucket < validation_fraction else "train"


def _write_jsonl(path: Path, rows: list[ResearchLoopLiveRepairSftExample]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Research Loop Live Repair Artifact Audit",
        "",
        f"- Loop dir: `{payload.get('loop_dir')}`",
        f"- Artifacts: {payload.get('n_ok')}/{payload.get('n_artifacts')} valid",
        f"- Contract OK: {payload.get('n_contract_ok')}",
        f"- Kernel verified: {payload.get('n_kernel_verified')}",
        f"- SFT examples: {payload.get('n_sft_examples')}",
        "",
        "## Handlers",
        "",
    ]
    by_handler = payload.get("by_handler", {})
    if isinstance(by_handler, dict) and by_handler:
        for handler, count in sorted(by_handler.items()):
            lines.append(f"- `{handler}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Task Types", ""])
    by_type = payload.get("by_type", {})
    if isinstance(by_type, dict) and by_type:
        for task_type, count in sorted(by_type.items()):
            lines.append(f"- `{task_type}`: {count}")
    else:
        lines.append("- none")
    lines.append("")
    if payload.get("errors"):
        lines.extend(["## Errors", ""])
        for error in payload.get("errors", []):
            lines.append(f"- {error}")
        lines.append("")
    return "\n".join(lines)

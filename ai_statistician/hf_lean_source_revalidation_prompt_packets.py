from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


HF_LEAN_SOURCE_REVALIDATION_PROMPT_PACKET_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "HF_LEAN_SOURCE_REVALIDATION_PROMPT_PACKETS_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Hugging Face Lean source revalidation prompt packets are worker instructions, "
    "not proof evidence. They become useful for proof promotion only after the "
    "worker response is validated with local Lean/AXLE kernel artifacts."
)


@dataclass(frozen=True)
class HuggingFaceLeanSourceRevalidationPromptPacket:
    schema_version: int
    prompt_packet_id: str
    task_id: str
    revalidation_id: str
    source_id: str
    dataset_id: str
    url: str
    priority: str
    priority_score: int
    relevance_class: str
    retrieval_role: str
    task_status: str
    sample_strategy: str
    sample_size: int
    sample_seed: int
    license_review_required: bool
    local_work_dir: str
    sample_manifest_path: str
    lean_reconstruction_dir: str
    verifier_attempt_log: str
    promotion_manifest_path: str
    required_gate: str
    command_plan: tuple[str, ...]
    prompt: str
    expected_output_contract: dict[str, object]
    forbidden_claims: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_huggingface_lean_source_revalidation_prompt_packets(
    task_dir: Path,
    out_dir: Path | None = None,
    *,
    max_packets: int = 20,
) -> dict[str, object]:
    """Export self-contained prompts for HF Lean source revalidation workers."""

    errors: list[str] = []
    task_manifest_path = task_dir / "hf_lean_source_revalidation_tasks_manifest.json"
    task_jsonl_path = task_dir / "hf_lean_source_revalidation_tasks.jsonl"
    task_manifest = _read_json(task_manifest_path, errors)
    task_rows = _read_jsonl(task_jsonl_path, errors)
    if not task_rows and isinstance(task_manifest.get("rows"), list):
        task_rows = [row for row in task_manifest.get("rows", []) if isinstance(row, dict)]
    ready_rows = [
        row
        for row in task_rows
        if str(row.get("task_status", "")).startswith("READY_")
    ]
    selected_rows = sorted(
        ready_rows,
        key=lambda row: (
            -_safe_int(row.get("priority_score", 0)),
            str(row.get("dataset_id", "")),
        ),
    )[: max(0, max_packets)]
    packets = [_prompt_packet(row) for row in selected_rows]
    by_status = Counter(packet.task_status for packet in packets)
    by_class = Counter(packet.relevance_class for packet in packets)
    payload: dict[str, object] = {
        "schema_version": HF_LEAN_SOURCE_REVALIDATION_PROMPT_PACKET_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task_dir": str(task_dir),
        "task_manifest": str(task_manifest_path),
        "task_jsonl": str(task_jsonl_path),
        "max_packets": max_packets,
        "n_tasks": len(task_rows),
        "n_ready_tasks": len(ready_rows),
        "n_prompt_packets": len(packets),
        "n_license_review_required": sum(
            1 for packet in packets if packet.license_review_required
        ),
        "n_zero_sample_size": sum(1 for packet in packets if packet.sample_size == 0),
        "n_with_output_contract": sum(
            1 for packet in packets if bool(packet.expected_output_contract)
        ),
        "n_ok": sum(1 for packet in packets if packet.ok),
        "all_ok": not errors and all(packet.ok for packet in packets),
        "errors": errors,
        "by_task_status": dict(sorted(by_status.items())),
        "by_relevance_class": dict(sorted(by_class.items())),
        "packets": [asdict(packet) for packet in packets],
        "prompt_packet_fingerprint": stable_hash([asdict(packet) for packet in packets]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "prompt packets do not include dataset rows",
            "license/access review remains mandatory before sampling unknown-license datasets",
            "worker responses are not proof evidence until artifact validation accepts them",
            "promotion requires local Lean/AXLE kernel evidence and downstream review",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "hf_lean_source_revalidation_prompt_packets_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        (out_dir / "hf_lean_source_revalidation_prompt_packets.jsonl").write_text(
            "\n".join(json.dumps(asdict(packet), sort_keys=True) for packet in packets)
            + ("\n" if packets else ""),
            encoding="utf-8",
        )
        (out_dir / "hf_lean_source_revalidation_prompt_packets.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _prompt_packet(
    task: dict[str, Any],
) -> HuggingFaceLeanSourceRevalidationPromptPacket:
    errors: list[str] = []
    task_id = str(task.get("task_id", ""))
    dataset_id = str(task.get("dataset_id", ""))
    revalidation_id = str(task.get("revalidation_id", ""))
    if not task_id:
        errors.append("task_id missing")
    if not dataset_id:
        errors.append("dataset_id missing")
    if not revalidation_id:
        errors.append("revalidation_id missing")
    if not str(task.get("required_gate", "")):
        errors.append("required_gate missing")
    command_plan = _str_tuple(task.get("command_plan", []))
    if not command_plan:
        errors.append("command_plan missing")
    packet_id = "hf_lean_source_revalidation_prompt_packet:" + stable_hash(
        [task_id, dataset_id, revalidation_id]
    )[:16]
    contract = _expected_output_contract(task)
    prompt = _prompt(task, packet_id=packet_id, contract=contract)
    if not prompt:
        errors.append("prompt missing")
    return HuggingFaceLeanSourceRevalidationPromptPacket(
        schema_version=HF_LEAN_SOURCE_REVALIDATION_PROMPT_PACKET_SCHEMA_VERSION,
        prompt_packet_id=packet_id,
        task_id=task_id,
        revalidation_id=revalidation_id,
        source_id=str(task.get("source_id", "")),
        dataset_id=dataset_id,
        url=str(task.get("url", "")),
        priority=str(task.get("priority", "")),
        priority_score=_safe_int(task.get("priority_score", 0)),
        relevance_class=str(task.get("relevance_class", "")),
        retrieval_role=str(task.get("retrieval_role", "")),
        task_status=str(task.get("task_status", "")),
        sample_strategy=str(task.get("sample_strategy", "")),
        sample_size=_safe_int(task.get("sample_size", 0)),
        sample_seed=_safe_int(task.get("sample_seed", 0)),
        license_review_required=bool(task.get("license_review_required", False)),
        local_work_dir=str(task.get("local_work_dir", "")),
        sample_manifest_path=str(task.get("sample_manifest_path", "")),
        lean_reconstruction_dir=str(task.get("lean_reconstruction_dir", "")),
        verifier_attempt_log=str(task.get("verifier_attempt_log", "")),
        promotion_manifest_path=str(task.get("promotion_manifest_path", "")),
        required_gate=str(task.get("required_gate", "")),
        command_plan=command_plan,
        prompt=prompt,
        expected_output_contract=contract,
        forbidden_claims=(
            "do not vendor full generated datasets or indexes into the repository",
            "do not skip license/access/provenance review for unknown-license datasets",
            "do not report proof_evidence_ready > 0 without local Lean/AXLE kernel evidence",
            "do not promote retrieval, benchmark, or training rows as theorem proof evidence",
        ),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _expected_output_contract(task: dict[str, Any]) -> dict[str, object]:
    return {
        "write_jsonl": "hf_lean_source_revalidation_worker_outputs.jsonl",
        "required_fields": [
            "response_id",
            "task_id",
            "dataset_id",
            "sample_manifest_path",
            "lean_reconstruction_dir",
            "verifier_attempt_log",
            "promotion_manifest_path",
            "sampled_rows",
            "reconstructed_artifacts",
            "verifier",
            "verification_strength",
            "kernel_verified_rows",
            "proof_evidence_ready",
        ],
        "task_id": str(task.get("task_id", "")),
        "dataset_id": str(task.get("dataset_id", "")),
        "allowed_zero_evidence_response": {
            "sampled_rows": 0,
            "reconstructed_artifacts": 0,
            "kernel_verified_rows": 0,
            "proof_evidence_ready": 0,
            "use_when": (
                "metadata, license, imports, sampling, or local Lean/AXLE verification "
                "is unavailable or incomplete"
            ),
        },
        "local_kernel_evidence_rule": (
            "proof_evidence_ready may be positive only when verifier is local Lean or AXLE, "
            "verification_strength records kernel/local_lean/axle strength, and the sample, "
            "reconstruction, verifier log, and promotion manifest paths exist."
        ),
        "dedupe_keys": [
            "dataset_id",
            "sha",
            "formal_statement_hash",
            "formal_proof_hash",
        ],
    }


def _prompt(task: dict[str, Any], *, packet_id: str, contract: dict[str, object]) -> str:
    commands = "\n".join(f"- {item}" for item in _str_tuple(task.get("command_plan", [])))
    expected_outputs = "\n".join(
        f"- {item}" for item in _str_tuple(task.get("expected_outputs", []))
    ) or "- sample manifest, Lean reconstruction artifacts, verifier log, promotion manifest"
    return "\n".join(
        [
            "You are the HF Lean source revalidation worker for an AI Statistical Theory Lab.",
            "Execute this task as a bounded source-reuse check. Do not claim theorem proof evidence.",
            "",
            f"Prompt packet id: {packet_id}",
            f"Task id: {task.get('task_id', '')}",
            f"Revalidation id: {task.get('revalidation_id', '')}",
            f"Dataset: {task.get('dataset_id', '')}",
            f"URL: {task.get('url', '')}",
            f"Relevance class: {task.get('relevance_class', '')}",
            f"Retrieval role: {task.get('retrieval_role', '')}",
            f"Task status: {task.get('task_status', '')}",
            f"Sample strategy: {task.get('sample_strategy', '')}",
            f"Sample size: {task.get('sample_size', 0)}",
            f"Sample seed: {task.get('sample_seed', '')}",
            f"License review required: {task.get('license_review_required', False)}",
            "",
            "Expected local paths:",
            f"- sample manifest: {task.get('sample_manifest_path', '')}",
            f"- Lean reconstruction dir: {task.get('lean_reconstruction_dir', '')}",
            f"- verifier attempt log: {task.get('verifier_attempt_log', '')}",
            f"- candidate promotion manifest: {task.get('promotion_manifest_path', '')}",
            "",
            "Command plan:",
            commands or "- review task; emit a zero-evidence response if blocked",
            "",
            "Expected outputs:",
            expected_outputs,
            "",
            f"Required gate: {task.get('required_gate', '')}",
            "",
            "Return one JSONL response row matching this contract:",
            json.dumps(contract, indent=2, sort_keys=True),
            "",
            "Boundary: rows are retrieval/training candidates until local Lean/AXLE verifies reconstructed Lean artifacts.",
        ]
    )


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse JSON {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse {path}:{line_no}: {type(exc).__name__}: {exc}")
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            errors.append(f"non-object JSONL row at {path}:{line_no}")
    return rows


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    if value:
        return (str(value),)
    return ()


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# HF Lean Source Revalidation Prompt Packets",
        "",
        f"- Tasks: `{payload.get('n_tasks')}`",
        f"- Ready tasks: `{payload.get('n_ready_tasks')}`",
        f"- Prompt packets: `{payload.get('n_prompt_packets')}`",
        f"- License review required: `{payload.get('n_license_review_required')}`",
        f"- Proof evidence status: `{payload.get('proof_evidence_status')}`",
        "",
        str(payload.get("proof_evidence_boundary", "")),
        "",
    ]
    for packet in payload.get("packets", []):
        if not isinstance(packet, dict):
            continue
        lines.append(
            f"- `{packet.get('dataset_id')}` task `{packet.get('task_id')}` "
            f"({packet.get('sample_strategy')}, sample={packet.get('sample_size')})"
        )
        lines.append(f"  work dir: `{packet.get('local_work_dir')}`")
        lines.append(f"  gate: {packet.get('required_gate')}")
        lines.append(f"  proof status: {packet.get('proof_evidence_status')}")
    return "\n".join(lines) + "\n"

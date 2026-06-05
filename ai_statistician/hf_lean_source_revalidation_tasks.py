from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


HF_LEAN_SOURCE_REVALIDATION_TASK_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "HF_LEAN_SOURCE_REVALIDATION_TASKS_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Hugging Face Lean source revalidation tasks are operational work orders. "
    "They become proof evidence only after concrete Lean artifacts are sampled, "
    "reconstructed or imported, and accepted by local Lean/AXLE kernel verification."
)


@dataclass(frozen=True)
class HuggingFaceLeanSourceRevalidationTask:
    schema_version: int
    task_id: str
    revalidation_id: str
    source_id: str
    dataset_id: str
    url: str
    sha: str
    priority: str
    priority_score: int
    relevance_class: str
    retrieval_role: str
    ingestion_mode: str
    source_revalidation_status: str
    task_status: str
    owner_agent: str
    action_type: str
    sample_strategy: str
    sample_size: int
    sample_seed: int
    license_review_required: bool
    required_inputs: tuple[str, ...]
    command_plan: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    local_work_dir: str
    sample_manifest_path: str
    lean_reconstruction_dir: str
    verifier_attempt_log: str
    promotion_manifest_path: str
    dedupe_keys: tuple[str, ...]
    required_gate: str
    kernel_verified_rows: int
    proof_evidence_ready: int
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_huggingface_lean_source_revalidation_tasks(
    queue_jsonl_path: Path,
    out_dir: Path | None = None,
    *,
    max_tasks: int = 20,
    sample_seed: int = 20260605,
) -> dict[str, object]:
    """Export worker-facing tasks from Hugging Face Lean source queue rows."""

    errors: list[str] = []
    queue_rows = _read_jsonl(queue_jsonl_path, errors)
    tasks = [
        _task_from_queue_row(row, out_dir=out_dir, queue_jsonl_path=queue_jsonl_path, sample_seed=sample_seed)
        for row in queue_rows
    ]
    tasks = sorted(tasks, key=lambda row: (-row.priority_score, row.dataset_id))[: max(0, max_tasks)]
    by_status = Counter(row.task_status for row in tasks)
    by_class = Counter(row.relevance_class for row in tasks)
    payload: dict[str, object] = {
        "schema_version": HF_LEAN_SOURCE_REVALIDATION_TASK_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "queue_jsonl": str(queue_jsonl_path),
        "n_queue_rows": len(queue_rows),
        "n_tasks": len(tasks),
        "n_ready": sum(1 for row in tasks if row.task_status.startswith("READY_")),
        "n_blocked": sum(1 for row in tasks if row.task_status.startswith("BLOCKED_")),
        "n_license_review_required": sum(1 for row in tasks if row.license_review_required),
        "n_with_sample_plan": sum(1 for row in tasks if row.sample_strategy),
        "n_kernel_verified": 0,
        "n_proof_evidence_ready": 0,
        "n_ok": sum(1 for row in tasks if row.ok),
        "all_ok": not errors and all(row.ok for row in tasks),
        "errors": errors,
        "by_task_status": dict(sorted(by_status.items())),
        "by_relevance_class": dict(sorted(by_class.items())),
        "rows": [asdict(row) for row in tasks],
        "task_fingerprint": stable_hash([asdict(row) for row in tasks]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "task rows are not dataset contents",
            "sample manifests are expected outputs until a worker writes them",
            "license/access review must complete before streaming or sampling unknown-license datasets",
            "only local Lean/AXLE accepted reconstructed artifacts can update proof evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "hf_lean_source_revalidation_tasks_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        (out_dir / "hf_lean_source_revalidation_tasks.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in tasks)
            + ("\n" if tasks else ""),
            encoding="utf-8",
        )
        (out_dir / "hf_lean_source_revalidation_tasks.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _task_from_queue_row(
    row: dict[str, Any],
    *,
    out_dir: Path | None,
    queue_jsonl_path: Path,
    sample_seed: int,
) -> HuggingFaceLeanSourceRevalidationTask:
    errors: list[str] = []
    dataset_id = str(row.get("dataset_id", ""))
    revalidation_id = str(row.get("revalidation_id", ""))
    source_id = str(row.get("source_id", ""))
    priority = str(row.get("priority", ""))
    relevance_class = str(row.get("relevance_class", ""))
    source_status = str(row.get("revalidation_status", ""))
    if not dataset_id:
        errors.append("dataset_id missing")
    if not revalidation_id:
        errors.append("revalidation_id missing")
    if not source_id:
        errors.append("source_id missing")
    if not source_status:
        errors.append("revalidation_status missing")

    license_review_required = bool(row.get("license_review_required", False))
    if source_status.startswith("BLOCKED_"):
        task_status = source_status
    elif errors:
        task_status = "BLOCKED_INVALID_REVALIDATION_QUEUE_ROW"
    elif license_review_required:
        task_status = "READY_FOR_METADATA_LICENSE_AND_SAMPLE_PLANNING"
    else:
        task_status = "READY_FOR_SAMPLE_RECONSTRUCTION_AND_LOCAL_VERIFY"

    output_base = out_dir or queue_jsonl_path.parent
    safe_name = _safe_name(dataset_id or source_id or revalidation_id or "unknown")
    work_dir = output_base / "work" / safe_name
    task_id = "hf_lean_source_revalidation_task:" + stable_hash(
        [revalidation_id, dataset_id, source_status, sample_seed]
    )[:16]
    sample_strategy, sample_size = _sample_strategy(relevance_class, license_review_required)
    return HuggingFaceLeanSourceRevalidationTask(
        schema_version=HF_LEAN_SOURCE_REVALIDATION_TASK_SCHEMA_VERSION,
        task_id=task_id,
        revalidation_id=revalidation_id,
        source_id=source_id,
        dataset_id=dataset_id,
        url=str(row.get("url", "")),
        sha=str(row.get("sha", "")),
        priority=priority,
        priority_score=_priority_score(priority, relevance_class, task_status),
        relevance_class=relevance_class,
        retrieval_role=str(row.get("retrieval_role", "")),
        ingestion_mode=str(row.get("ingestion_mode", "")),
        source_revalidation_status=source_status,
        task_status=task_status,
        owner_agent="hf_lean_source_revalidation_worker",
        action_type="sample_reconstruct_and_verify_hf_lean_source",
        sample_strategy=sample_strategy,
        sample_size=sample_size,
        sample_seed=sample_seed,
        license_review_required=license_review_required,
        required_inputs=tuple(str(value) for value in _list(row.get("required_inputs"))),
        command_plan=(
            "review dataset metadata, license, access, and provenance",
            "stream or sample rows without vendoring generated indexes",
            "dedupe by dataset_id, sha, formal_statement_hash, and formal_proof_hash",
            "reconstruct complete Lean imports/header when available",
            "run local Lean or AXLE on reconstructed Lean artifacts",
            "promote only kernel-verified rows into proof-bank or proof-search evidence",
        ),
        expected_outputs=(
            "sample manifest with row ids and hashes",
            "Lean reconstruction artifacts for sampled rows",
            "local Lean/AXLE verifier attempt log",
            "candidate promotion manifest containing kernel-verified rows only",
        ),
        local_work_dir=str(work_dir),
        sample_manifest_path=str(work_dir / "sample_manifest.json"),
        lean_reconstruction_dir=str(work_dir / "lean"),
        verifier_attempt_log=str(work_dir / "verifier_attempts.jsonl"),
        promotion_manifest_path=str(work_dir / "candidate_promotion_manifest.json"),
        dedupe_keys=tuple(str(value) for value in _list(row.get("dedupe_keys"))),
        required_gate="local Lean/AXLE kernel verification of reconstructed Lean artifacts",
        kernel_verified_rows=0,
        proof_evidence_ready=0,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _sample_strategy(relevance_class: str, license_review_required: bool) -> tuple[str, int]:
    if license_review_required:
        return ("metadata_license_review_before_sampling", 0)
    if relevance_class == "formal_proof_pairs":
        return ("deterministic_small_proof_pair_sample", 8)
    if relevance_class == "tactic_state_training":
        return ("deterministic_tactic_state_context_sample", 6)
    if relevance_class == "proof_repair_or_process_training":
        return ("deterministic_process_trace_sample", 6)
    if relevance_class == "formal_code_corpus":
        return ("deterministic_declaration_context_sample", 12)
    if relevance_class == "benchmark_eval":
        return ("holdout_metadata_review_only", 0)
    return ("manual_review_before_sampling", 0)


def _priority_score(priority: str, relevance_class: str, task_status: str) -> int:
    score = {"critical": 100, "high": 80, "medium": 50}.get(priority, 10)
    score += {
        "formal_proof_pairs": 10,
        "proof_repair_or_process_training": 7,
        "tactic_state_training": 6,
        "formal_code_corpus": 4,
    }.get(relevance_class, 0)
    if task_status.startswith("BLOCKED_"):
        score -= 40
    return score


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
            errors.append(f"JSONL row is not an object: {path}:{line_no}")
    return rows


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return safe[:120] or "unknown"


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Hugging Face Lean Source Revalidation Tasks",
        "",
        f"- Created at: `{payload.get('created_at')}`",
        f"- Queue rows: `{payload.get('n_queue_rows')}`",
        f"- Tasks: `{payload.get('n_tasks')}`",
        f"- Ready: `{payload.get('n_ready')}`",
        f"- Blocked: `{payload.get('n_blocked')}`",
        f"- License review required: `{payload.get('n_license_review_required')}`",
        f"- Kernel verified rows: `{payload.get('n_kernel_verified')}`",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Task Rows",
        "",
        "| status | priority | dataset | class | sample | gate |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {status} | {priority} | {dataset} | {klass} | {sample} | {gate} |".format(
                status=row.get("task_status", ""),
                priority=row.get("priority", ""),
                dataset=row.get("dataset_id", ""),
                klass=row.get("relevance_class", ""),
                sample=row.get("sample_size", 0),
                gate=str(row.get("required_gate", "")).replace("|", "/"),
            )
        )
    errors = payload.get("errors", [])
    if errors:
        lines.extend(["", "## Errors", ""])
        for error in errors:
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)

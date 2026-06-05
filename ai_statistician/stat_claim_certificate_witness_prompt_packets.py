from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


STAT_CLAIM_CERTIFICATE_WITNESS_PROMPT_PACKET_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "STAT_CLAIM_CERTIFICATE_WITNESS_PROMPT_PACKETS_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Certificate witness prompt packets are untrusted generation work orders. "
    "They can ask a worker to fill source-cited witness fields, but they are "
    "not checker validation, Lean proof evidence, or source theorem evidence."
)
WORKER_OUTPUT_JSONL = "stat_claim_certificate_witness_worker_outputs.jsonl"


@dataclass(frozen=True)
class StatClaimCertificateWitnessPromptPacket:
    schema_version: int
    prompt_packet_id: str
    draft_id: str
    task_id: str
    target_id: str
    source_claim_id: str
    question_id: str
    problem_class: str
    certificate_family: str
    checker_name: str
    checker_obligation_id: str
    required_fields: tuple[str, ...]
    draft_path: str
    expected_witness_path: str
    statement: str
    checker_contract: str
    generator_contract: str
    required_gate: str
    source_evidence_paths: tuple[str, ...]
    semantic_linkage_requirements: tuple[str, ...]
    forbidden_shortcuts: tuple[str, ...]
    expected_output_contract: dict[str, object]
    prompt: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_stat_claim_certificate_witness_prompt_packets(
    materializer_dir: Path,
    out_dir: Path | None = None,
    *,
    max_packets: int | None = None,
) -> dict[str, object]:
    """Export self-contained prompts for source-cited witness generation."""

    errors: list[str] = []
    materializer_manifest_path = (
        materializer_dir / "stat_claim_certificate_witness_materializer_manifest.json"
    )
    draft_jsonl_path = materializer_dir / "stat_claim_certificate_witness_drafts.jsonl"
    materializer_manifest = _read_json(materializer_manifest_path, errors)
    draft_rows = _read_jsonl(draft_jsonl_path, errors)
    if max_packets is not None:
        draft_rows = draft_rows[: max(0, max_packets)]
    task_jsonl_raw = str(materializer_manifest.get("witness_queue_tasks_jsonl", ""))
    task_jsonl_path = Path(task_jsonl_raw) if task_jsonl_raw else Path()
    task_rows = _read_jsonl(task_jsonl_path, errors) if task_jsonl_raw else []
    task_by_id = {
        str(row.get("task_id", "")): row
        for row in task_rows
        if isinstance(row, dict) and str(row.get("task_id", ""))
    }
    packets = [
        _prompt_packet(row, task=task_by_id.get(str(row.get("task_id", "")), {}))
        for row in draft_rows
    ]
    by_family = Counter(packet.certificate_family for packet in packets)
    payload: dict[str, object] = {
        "schema_version": STAT_CLAIM_CERTIFICATE_WITNESS_PROMPT_PACKET_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "materializer_dir": str(materializer_dir),
        "materializer_manifest": str(materializer_manifest_path),
        "materializer_drafts_jsonl": str(draft_jsonl_path),
        "witness_queue_tasks_jsonl": str(task_jsonl_path),
        "materializer_all_ok": bool(materializer_manifest.get("all_ok", False)),
        "materializer_proof_evidence_status": str(
            materializer_manifest.get("proof_evidence_status", "")
        ),
        "max_packets": max_packets,
        "n_drafts": len(draft_rows),
        "n_prompt_packets": len(packets),
        "n_ok": sum(1 for packet in packets if packet.ok),
        "n_with_source_evidence_paths": sum(1 for packet in packets if packet.source_evidence_paths),
        "n_with_checker_contract": sum(1 for packet in packets if bool(packet.checker_contract)),
        "n_with_output_contract": sum(1 for packet in packets if bool(packet.expected_output_contract)),
        "n_with_prompt": sum(1 for packet in packets if bool(packet.prompt)),
        "all_ok": (
            not errors
            and bool(materializer_manifest.get("all_ok", False))
            and all(packet.ok for packet in packets)
        ),
        "errors": errors,
        "by_family": dict(sorted(by_family.items())),
        "packets": [asdict(packet) for packet in packets],
        "prompt_packet_fingerprint": stable_hash([asdict(packet) for packet in packets]),
        "worker_output_jsonl": WORKER_OUTPUT_JSONL,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "prompt packets are worker instructions, not generated witnesses",
            "source-cited witness fields remain untrusted until validator and checker gates pass",
            "a checker theorem proves only the encoded certificate contract after kernel verification",
            "source theorem promotion still requires semantic linkage review and Lean/AXLE evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "stat_claim_certificate_witness_prompt_packets_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_prompt_packets.jsonl").write_text(
            "\n".join(json.dumps(asdict(packet), sort_keys=True) for packet in packets)
            + ("\n" if packets else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_prompt_packets.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _prompt_packet(
    draft_row: dict[str, Any],
    *,
    task: dict[str, Any],
) -> StatClaimCertificateWitnessPromptPacket:
    errors: list[str] = []
    if not task:
        errors.append("matching witness queue task missing")
    required_fields = tuple(
        str(field) for field in draft_row.get("required_fields", ()) or () if str(field)
    )
    if not required_fields:
        errors.append("required_fields missing")
    source_evidence_paths = tuple(
        str(path)
        for path in (
            *(draft_row.get("source_evidence_paths", ()) or ()),
            *(task.get("evidence_paths", ()) or ()),
        )
        if str(path)
    )
    semantic_linkage_requirements = _str_tuple(
        task.get("semantic_linkage_requirements", ())
        or (
            "cite the source claim id and evidence paths used for every witness field",
            "state every source-to-encoded-claim gap as an open semantic review item",
        )
    )
    forbidden_shortcuts = _str_tuple(
        task.get("forbidden_shortcuts", ())
        or (
            "do not fill witness fields with the theorem conclusion",
            "do not mark the source claim proved from witness generation alone",
        )
    )
    contract = _expected_output_contract(required_fields)
    prompt = _prompt(draft_row, task, required_fields, source_evidence_paths, contract)
    if not source_evidence_paths:
        errors.append("source evidence paths missing")
    if not str(task.get("checker_contract", "")):
        errors.append("checker_contract missing")
    if not str(task.get("statement", "")):
        errors.append("source statement missing")
    if not prompt:
        errors.append("prompt missing")
    return StatClaimCertificateWitnessPromptPacket(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_PROMPT_PACKET_SCHEMA_VERSION,
        prompt_packet_id="stat_claim_certificate_witness_prompt_packet:"
        + stable_hash([draft_row.get("draft_id", ""), draft_row.get("target_id", ""), prompt])[:16],
        draft_id=str(draft_row.get("draft_id", "")),
        task_id=str(draft_row.get("task_id", "")),
        target_id=str(draft_row.get("target_id", "")),
        source_claim_id=str(draft_row.get("source_claim_id", "")),
        question_id=str(draft_row.get("question_id", "")),
        problem_class=str(draft_row.get("problem_class", "")),
        certificate_family=str(draft_row.get("certificate_family", "")),
        checker_name=str(draft_row.get("checker_name", "")),
        checker_obligation_id=str(draft_row.get("checker_obligation_id", "")),
        required_fields=required_fields,
        draft_path=str(draft_row.get("draft_path", "")),
        expected_witness_path=str(draft_row.get("expected_witness_path", "")),
        statement=str(task.get("statement", "")),
        checker_contract=str(task.get("checker_contract", "")),
        generator_contract=str(task.get("generator_contract", "")),
        required_gate=str(task.get("required_gate", "")),
        source_evidence_paths=source_evidence_paths,
        semantic_linkage_requirements=semantic_linkage_requirements,
        forbidden_shortcuts=forbidden_shortcuts,
        expected_output_contract=contract,
        prompt=prompt,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _expected_output_contract(required_fields: tuple[str, ...]) -> dict[str, object]:
    return {
        "write_jsonl": WORKER_OUTPUT_JSONL,
        "required_fields": [
            "prompt_packet_id",
            "draft_id",
            "task_id",
            "fields",
            "source_field_evidence",
            "open_semantic_gaps",
            "semantic_linkage_review",
            "checker_validation",
            "proof_evidence_status",
            "source_claim_proved",
            "limitations",
        ],
        "witness_fields": list(required_fields),
        "field_rule": (
            "Every non-null witness field must cite at least one source evidence path "
            "or source span in source_field_evidence[field]. Leave uncertain fields "
            "null and add a concrete open_semantic_gaps entry."
        ),
        "checker_rule": (
            "Set checker_validation.attempted=false and checker_validation.passed=false; "
            "this worker is only filling a witness draft."
        ),
        "proof_evidence_rule": (
            "Set proof_evidence_status to "
            "STAT_CLAIM_CERTIFICATE_WITNESS_DRAFT_NOT_PROOF_EVIDENCE and "
            "source_claim_proved=false."
        ),
    }


def _prompt(
    draft_row: dict[str, Any],
    task: dict[str, Any],
    required_fields: tuple[str, ...],
    source_evidence_paths: tuple[str, ...],
    contract: dict[str, object],
) -> str:
    lines = [
        "Fill a statistical claim certificate witness draft from cited source evidence.",
        "",
        f"Draft id: {draft_row.get('draft_id', '')}",
        f"Source claim id: {draft_row.get('source_claim_id', '')}",
        f"Question id: {draft_row.get('question_id', '')}",
        f"Certificate family: {draft_row.get('certificate_family', '')}",
        f"Checker: {draft_row.get('checker_name', '')}",
        f"Checker obligation: {draft_row.get('checker_obligation_id', '')}",
        "",
        "Source claim statement:",
        str(task.get("statement", "")),
        "",
        "Checker contract:",
        str(task.get("checker_contract", "")),
        "",
        "Required witness fields:",
        *[f"- {field}" for field in required_fields],
        "",
        "Source evidence paths:",
        *[f"- {path}" for path in source_evidence_paths],
        "",
        "Rules:",
        "- Use only source-cited values. Do not infer missing mathematical facts silently.",
        "- If a field cannot be supported by the source evidence, leave it null and list the gap.",
        "- Do not add assumptions, weaken the source claim, or restate the theorem as a witness.",
        "- Do not claim checker validation, Lean proof evidence, or source theorem proof.",
        "",
        "Expected output JSON contract:",
        json.dumps(contract, indent=2, sort_keys=True),
    ]
    return "\n".join(lines)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing JSONL file: {path}")
        return []
    except Exception as exc:
        errors.append(f"failed to read JSONL {path}: {type(exc).__name__}: {exc}")
        return []
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(lines, start=1):
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


def _str_tuple(value: object) -> tuple[str, ...]:
    return tuple(str(item) for item in value or () if str(item))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Statistical Claim Certificate Witness Prompt Packets",
        "",
        f"- Materializer: `{payload.get('materializer_manifest')}`",
        f"- Prompt packets: `{payload.get('n_ok')}/{payload.get('n_prompt_packets')}`",
        f"- Source-grounded packets: `{payload.get('n_with_source_evidence_paths')}`",
        f"- Output contracts: `{payload.get('n_with_output_contract')}`",
        f"- Proof status: `{payload.get('proof_evidence_status')}`",
        "",
        "## Families",
        "",
    ]
    by_family = payload.get("by_family", {})
    if isinstance(by_family, dict) and by_family:
        for family, count in sorted(by_family.items()):
            lines.append(f"- `{family}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

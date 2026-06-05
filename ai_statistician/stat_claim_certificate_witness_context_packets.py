from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


STAT_CLAIM_CERTIFICATE_WITNESS_CONTEXT_PACKET_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "STAT_CLAIM_CERTIFICATE_WITNESS_CONTEXT_PACKETS_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Certificate witness context packets are bounded source-context retrieval artifacts. "
    "They help a worker inspect cited files for witness fields, but they are not "
    "generated witnesses, checker validation, Lean proof evidence, or source theorem evidence."
)
DEFAULT_MAX_SNIPPETS_PER_SOURCE = 3
DEFAULT_MAX_SNIPPET_CHARS = 1200
DEFAULT_CONTEXT_LINE_RADIUS = 2
MAX_SOURCE_READ_CHARS = 200_000


@dataclass(frozen=True)
class StatClaimCertificateWitnessContextPacket:
    schema_version: int
    context_packet_id: str
    prompt_packet_id: str
    draft_id: str
    task_id: str
    target_id: str
    source_claim_id: str
    question_id: str
    certificate_family: str
    checker_name: str
    checker_obligation_id: str
    required_fields: tuple[str, ...]
    statement: str
    source_evidence_paths: tuple[str, ...]
    resolved_source_paths: tuple[str, ...]
    missing_source_paths: tuple[str, ...]
    snippets: tuple[dict[str, object], ...]
    field_context_hints: dict[str, object]
    worker_instruction: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_stat_claim_certificate_witness_context_packets(
    prompt_packets_dir: Path,
    out_dir: Path | None = None,
    *,
    max_packets: int | None = None,
    max_snippets_per_source: int = DEFAULT_MAX_SNIPPETS_PER_SOURCE,
    max_snippet_chars: int = DEFAULT_MAX_SNIPPET_CHARS,
) -> dict[str, object]:
    """Resolve witness prompt evidence paths into bounded source-context packets.

    This stage is deliberately retrieval-only. It packages the cited files and
    field-level search hints so a worker can fill witness responses without
    repeatedly rediscovering the same context. It never fills witness fields or
    claims checker/proof evidence.
    """

    errors: list[str] = []
    prompt_manifest_path = (
        prompt_packets_dir / "stat_claim_certificate_witness_prompt_packets_manifest.json"
    )
    prompt_jsonl_path = prompt_packets_dir / "stat_claim_certificate_witness_prompt_packets.jsonl"
    prompt_manifest = _read_json(prompt_manifest_path, errors)
    prompt_rows = _read_jsonl(prompt_jsonl_path, errors)
    if max_packets is not None:
        prompt_rows = prompt_rows[: max(0, max_packets)]
    packets = [
        _context_packet(
            row,
            base_dir=prompt_packets_dir,
            max_snippets_per_source=max(0, max_snippets_per_source),
            max_snippet_chars=max(200, max_snippet_chars),
        )
        for row in prompt_rows
    ]
    by_family = Counter(packet.certificate_family for packet in packets)
    payload: dict[str, object] = {
        "schema_version": STAT_CLAIM_CERTIFICATE_WITNESS_CONTEXT_PACKET_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt_packets_dir": str(prompt_packets_dir),
        "prompt_packets_manifest": str(prompt_manifest_path),
        "prompt_packets_jsonl": str(prompt_jsonl_path),
        "prompt_packets_all_ok": bool(prompt_manifest.get("all_ok", False)),
        "prompt_packets_proof_evidence_status": str(
            prompt_manifest.get("proof_evidence_status", "")
        ),
        "max_packets": max_packets,
        "max_snippets_per_source": max_snippets_per_source,
        "max_snippet_chars": max_snippet_chars,
        "n_prompt_packets": len(prompt_rows),
        "n_context_packets": len(packets),
        "n_ok": sum(1 for packet in packets if packet.ok),
        "n_with_context": sum(1 for packet in packets if packet.snippets),
        "n_source_paths": sum(len(packet.source_evidence_paths) for packet in packets),
        "n_resolved_source_paths": sum(len(packet.resolved_source_paths) for packet in packets),
        "n_missing_source_paths": sum(len(packet.missing_source_paths) for packet in packets),
        "n_snippets": sum(len(packet.snippets) for packet in packets),
        "n_field_context_hints": sum(
            len(packet.field_context_hints) for packet in packets
        ),
        "all_ok": (
            not errors
            and bool(prompt_manifest.get("all_ok", False))
            and all(packet.ok for packet in packets)
        ),
        "errors": errors,
        "by_family": dict(sorted(by_family.items())),
        "packets": [asdict(packet) for packet in packets],
        "context_packet_fingerprint": stable_hash([asdict(packet) for packet in packets]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "source snippets are retrieval context, not witness values",
            "field hints may miss relevant source text and must be reviewed by a worker",
            "witness response validation still rejects missing fields, missing source evidence, and proof overclaims",
            "checker validation and source-theorem promotion remain separate Lean/AXLE gates",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "stat_claim_certificate_witness_context_packets_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_context_packets.jsonl").write_text(
            "\n".join(json.dumps(asdict(packet), sort_keys=True) for packet in packets)
            + ("\n" if packets else ""),
            encoding="utf-8",
        )
        (out_dir / "stat_claim_certificate_witness_context_packets.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _context_packet(
    prompt_packet: dict[str, Any],
    *,
    base_dir: Path,
    max_snippets_per_source: int,
    max_snippet_chars: int,
) -> StatClaimCertificateWitnessContextPacket:
    errors: list[str] = []
    required_fields = _str_tuple(prompt_packet.get("required_fields", ()))
    raw_paths = _dedupe(
        str(path)
        for path in prompt_packet.get("source_evidence_paths", ()) or ()
        if str(path)
    )
    statement = str(prompt_packet.get("statement", ""))
    terms = _query_terms(
        [
            statement,
            str(prompt_packet.get("source_claim_id", "")),
            str(prompt_packet.get("certificate_family", "")),
            str(prompt_packet.get("checker_obligation_id", "")),
            *required_fields,
        ]
    )
    snippets: list[dict[str, object]] = []
    resolved_paths: list[str] = []
    missing_paths: list[str] = []
    for path_text in raw_paths:
        path = _resolve_source_path(path_text, base_dir)
        if path is None:
            missing_paths.append(path_text)
            continue
        resolved_paths.append(str(path))
        source_snippets = _source_snippets(
            path,
            terms,
            source_path_label=path_text,
            max_snippets=max_snippets_per_source,
            max_snippet_chars=max_snippet_chars,
        )
        if not source_snippets:
            errors.append(f"no source snippets extracted from {path_text}")
        snippets.extend(source_snippets)
    if not raw_paths:
        errors.append("source_evidence_paths missing")
    if missing_paths:
        errors.extend(f"missing source evidence path: {path}" for path in missing_paths)
    if not snippets:
        errors.append("no source context snippets extracted")
    field_hints = _field_context_hints(required_fields, snippets, statement)
    worker_instruction = _worker_instruction(prompt_packet, snippets)
    return StatClaimCertificateWitnessContextPacket(
        schema_version=STAT_CLAIM_CERTIFICATE_WITNESS_CONTEXT_PACKET_SCHEMA_VERSION,
        context_packet_id="stat_claim_certificate_witness_context_packet:"
        + stable_hash([prompt_packet.get("prompt_packet_id", ""), snippets])[:16],
        prompt_packet_id=str(prompt_packet.get("prompt_packet_id", "")),
        draft_id=str(prompt_packet.get("draft_id", "")),
        task_id=str(prompt_packet.get("task_id", "")),
        target_id=str(prompt_packet.get("target_id", "")),
        source_claim_id=str(prompt_packet.get("source_claim_id", "")),
        question_id=str(prompt_packet.get("question_id", "")),
        certificate_family=str(prompt_packet.get("certificate_family", "")),
        checker_name=str(prompt_packet.get("checker_name", "")),
        checker_obligation_id=str(prompt_packet.get("checker_obligation_id", "")),
        required_fields=required_fields,
        statement=statement,
        source_evidence_paths=tuple(raw_paths),
        resolved_source_paths=tuple(resolved_paths),
        missing_source_paths=tuple(missing_paths),
        snippets=tuple(snippets),
        field_context_hints=field_hints,
        worker_instruction=worker_instruction,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _source_snippets(
    path: Path,
    terms: tuple[str, ...],
    *,
    source_path_label: str,
    max_snippets: int,
    max_snippet_chars: int,
) -> list[dict[str, object]]:
    text = _read_text(path)
    if not text.strip() or max_snippets == 0:
        return []
    lines = text.splitlines() or [text]
    matching_line_indexes = _matching_line_indexes(lines, terms)
    if not matching_line_indexes:
        matching_line_indexes = [
            idx for idx, line in enumerate(lines) if line.strip()
        ][:max_snippets]
    windows: list[tuple[int, int, str]] = []
    seen: set[tuple[int, int]] = set()
    for idx in matching_line_indexes:
        start = max(0, idx - DEFAULT_CONTEXT_LINE_RADIUS)
        end = min(len(lines), idx + DEFAULT_CONTEXT_LINE_RADIUS + 1)
        key = (start, end)
        if key in seen:
            continue
        seen.add(key)
        snippet_text = "\n".join(lines[start:end]).strip()
        if not snippet_text:
            continue
        windows.append((start + 1, end, _bounded(snippet_text, max_snippet_chars)))
        if len(windows) >= max_snippets:
            break
    snippets = []
    for ordinal, (start_line, end_line, snippet_text) in enumerate(windows, start=1):
        snippet_id = "source_snippet:" + stable_hash([str(path), ordinal, snippet_text])[:16]
        snippets.append(
            {
                "snippet_id": snippet_id,
                "source_path": source_path_label,
                "resolved_source_path": str(path),
                "line_start": start_line,
                "line_end": end_line,
                "matched_terms": list(_matched_terms(snippet_text, terms)),
                "text": snippet_text,
            }
        )
    return snippets


def _field_context_hints(
    required_fields: tuple[str, ...],
    snippets: list[dict[str, object]],
    statement: str,
) -> dict[str, object]:
    hints: dict[str, object] = {}
    for field in required_fields:
        field_terms = _query_terms([field, field.replace("_", " "), statement])
        candidate_ids = [
            str(snippet.get("snippet_id", ""))
            for snippet in snippets
            if _matched_terms(str(snippet.get("text", "")), field_terms)
        ]
        if not candidate_ids and snippets:
            candidate_ids = [str(snippets[0].get("snippet_id", ""))]
        hints[field] = {
            "query_terms": list(field_terms[:12]),
            "candidate_snippet_ids": tuple(candidate_ids[:5]),
            "rule": (
                "Fill only if a candidate snippet or another cited source span supports "
                "the value; otherwise leave null and list an open semantic gap."
            ),
        }
    return hints


def _worker_instruction(prompt_packet: dict[str, Any], snippets: list[dict[str, object]]) -> str:
    lines = [
        "Use the bounded snippets below as starting context for the cited source evidence.",
        "Do not treat snippets as proof. Fill witness fields only when the source text supports them.",
        "If the context is insufficient, leave fields null and record explicit open semantic gaps.",
        "",
        f"Prompt packet id: {prompt_packet.get('prompt_packet_id', '')}",
        f"Draft id: {prompt_packet.get('draft_id', '')}",
        f"Certificate family: {prompt_packet.get('certificate_family', '')}",
        "",
        "Snippet ids:",
    ]
    lines.extend(f"- {snippet.get('snippet_id', '')}: {snippet.get('source_path', '')}" for snippet in snippets[:12])
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


def _resolve_source_path(path_text: str, base_dir: Path) -> Path | None:
    path = Path(path_text)
    candidates = [path] if path.is_absolute() else [
        path,
        base_dir / path,
        base_dir.parent / path,
        base_dir.parent.parent / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:MAX_SOURCE_READ_CHARS]
    except Exception:
        return ""


def _query_terms(parts: list[str]) -> tuple[str, ...]:
    terms: list[str] = []
    for part in parts:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", part.lower()):
            for subtoken in token.split("_"):
                if len(subtoken) >= 4:
                    terms.append(subtoken)
            if len(token) >= 4:
                terms.append(token)
    return tuple(_dedupe(terms))[:40]


def _matching_line_indexes(lines: list[str], terms: tuple[str, ...]) -> list[int]:
    indexes: list[int] = []
    for idx, line in enumerate(lines):
        lower = line.lower()
        if any(term in lower for term in terms):
            indexes.append(idx)
    return indexes


def _matched_terms(text: str, terms: tuple[str, ...]) -> tuple[str, ...]:
    lower = text.lower()
    return tuple(term for term in terms if term in lower)


def _bounded(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 15)].rstrip() + "\n[truncated]"


def _dedupe(values: Any) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _str_tuple(value: object) -> tuple[str, ...]:
    return tuple(str(item) for item in value or () if str(item))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Statistical Claim Certificate Witness Context Packets",
        "",
        f"- Prompt packets: `{payload.get('prompt_packets_manifest')}`",
        f"- Context packets: `{payload.get('n_ok')}/{payload.get('n_context_packets')}`",
        f"- Resolved source paths: `{payload.get('n_resolved_source_paths')}`",
        f"- Missing source paths: `{payload.get('n_missing_source_paths')}`",
        f"- Snippets: `{payload.get('n_snippets')}`",
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

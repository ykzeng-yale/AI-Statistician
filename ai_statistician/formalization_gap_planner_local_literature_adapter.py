from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formalization_gap_planner_refinement_evidence import PROOF_EVIDENCE_BOUNDARY


FORMALIZATION_GAP_PLANNER_LOCAL_LITERATURE_ADAPTER_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_LOCAL_LITERATURE_ADAPTER_NOT_PROOF_EVIDENCE"
)
ADAPTER_TOOL_NAME = "local_literature_route_adapter"
SUPPORTED_TEXT_EXTENSIONS = {
    ".json",
    ".jsonl",
    ".md",
    ".markdown",
    ".rst",
    ".tex",
    ".txt",
}
STOP_WORDS = {
    "about",
    "after",
    "against",
    "also",
    "and",
    "are",
    "because",
    "before",
    "between",
    "for",
    "from",
    "into",
    "lean",
    "lemma",
    "paper",
    "proof",
    "query",
    "route",
    "search",
    "source",
    "that",
    "the",
    "their",
    "then",
    "theorem",
    "this",
    "with",
}


def export_formalization_gap_planner_local_literature_adapter_responses(
    formalization_gap_planner_refinement_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    literature_roots: tuple[Path, ...] | None = None,
    base_response_jsonl: Path | None = None,
    max_items: int = 0,
    k: int = 5,
    max_file_bytes: int = 1_000_000,
) -> dict[str, object]:
    """Emit literature route-evidence responses from a local text corpus.

    The adapter only answers `literature_discovery` queue rows. When
    `base_response_jsonl` is provided, non-literature responses are carried
    through and literature responses are replaced by local source matches,
    producing one merged response JSONL for the evidence validator.
    """

    errors: list[str] = []
    queue_manifest_path = (
        formalization_gap_planner_refinement_queue_dir
        / "formalization_gap_planner_refinement_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    queue_rows = [
        row for row in queue_payload.get("rows", []) if isinstance(row, dict)
    ]
    if max_items > 0:
        queue_rows = queue_rows[:max_items]
    literature_rows = [
        row for row in queue_rows if str(row.get("hook_kind", "")) == "literature_discovery"
    ]
    roots = tuple(Path(root) for root in (literature_roots or tuple()))
    documents = _read_documents(roots, errors, max_file_bytes=max(1, max_file_bytes))
    base_responses = _read_jsonl(base_response_jsonl, errors) if base_response_jsonl else []
    base_by_item = {
        str(row.get("refinement_item_id", "")): row
        for row in base_responses
        if str(row.get("refinement_item_id", ""))
    }
    responses = [
        _literature_response(row, documents, k=max(1, k)) for row in literature_rows
    ]
    merged_by_item = dict(base_by_item)
    for response in responses:
        merged_by_item[str(response.get("refinement_item_id", ""))] = response
    merged_responses = sorted(
        merged_by_item.values(),
        key=lambda row: (
            str(row.get("display_name", "")),
            str(row.get("evidence_kind", "")),
            str(row.get("refinement_item_id", "")),
        ),
    )
    by_node_kind = Counter(
        str(node.get("kind", ""))
        for response in responses
        for node in response.get("route_evidence_nodes", [])
        if isinstance(node, dict)
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_LOCAL_LITERATURE_ADAPTER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_local_literature_adapter",
        "formalization_gap_planner_refinement_queue_dir": str(
            formalization_gap_planner_refinement_queue_dir
        ),
        "formalization_gap_planner_refinement_queue_manifest": str(queue_manifest_path),
        "literature_roots": tuple(str(root) for root in roots),
        "base_response_jsonl": str(base_response_jsonl or ""),
        "max_file_bytes": max_file_bytes,
        "k": k,
        "n_queue_rows": len(queue_rows),
        "n_literature_discovery_rows": len(literature_rows),
        "n_documents_indexed": len(documents),
        "n_base_responses": len(base_responses),
        "n_local_literature_responses": len(responses),
        "n_merged_responses": len(merged_responses),
        "n_source_hits": sum(
            1
            for response in responses
            for node in response.get("route_evidence_nodes", [])
            if isinstance(node, dict) and node.get("kind") == "source_ref"
        ),
        "n_literature_gap_responses": sum(
            1
            for response in responses
            if any(
                isinstance(node, dict) and node.get("kind") == "literature_search_gap"
                for node in response.get("route_evidence_nodes", [])
            )
        ),
        "n_route_revision_recommended": sum(
            1 for response in responses if response.get("route_revision_recommended")
        ),
        "all_ok": not errors and bool(literature_rows) and len(responses) == len(literature_rows),
        "errors": errors,
        "by_route_evidence_node_kind": dict(sorted(by_node_kind.items())),
        "responses": responses,
        "merged_response_ids": [
            str(row.get("refinement_item_id", "")) for row in merged_responses
        ],
        "responses_fingerprint": stable_hash(responses),
        "merged_responses_fingerprint": stable_hash(merged_responses),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "local literature matches are source-route evidence, not theorem proof evidence",
            "lexical local-corpus search is a conservative fallback for Paperclip/PaperQA/OpenScholar adapters",
            "no-hit responses identify literature coverage gaps and should trigger focused search, not theorem rejection",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = (
            out_dir / "formalization_gap_planner_local_literature_adapter_manifest.json"
        )
        responses_path = (
            out_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        )
        local_responses_path = (
            out_dir / "formalization_gap_planner_local_literature_adapter_responses.jsonl"
        )
        payload["manifest_path"] = str(manifest_path)
        payload["responses_jsonl"] = str(responses_path)
        payload["local_responses_jsonl"] = str(local_responses_path)
        manifest_path.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        responses_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in merged_responses)
            + ("\n" if merged_responses else ""),
            encoding="utf-8",
        )
        local_responses_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in responses)
            + ("\n" if responses else ""),
            encoding="utf-8",
        )
        (out_dir / "formalization_gap_planner_local_literature_adapter.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _literature_response(
    queue_row: dict[str, Any],
    documents: tuple[dict[str, object], ...],
    *,
    k: int,
) -> dict[str, object]:
    query_text = _query_text(queue_row)
    query_terms = _query_terms(query_text)
    target_primitives = _str_tuple(queue_row.get("target_primitives", []))
    hits = _search_documents(documents, query_terms, target_primitives, k=k)
    revision_reasons: list[str] = []
    if not hits:
        revision_reasons.append("no local literature source matched queued queries")
    for primitive in target_primitives:
        if hits and not _primitive_supported_by_hits(primitive, hits):
            revision_reasons.append(
                f"{primitive} not directly supported by local literature hits"
            )
    source_refs = _source_refs(queue_row, hits)
    route_nodes = _route_evidence_nodes(
        queue_row,
        hits,
        source_refs=source_refs,
        query_terms=query_terms,
        target_primitives=target_primitives,
    )
    return {
        "refinement_item_id": str(queue_row.get("refinement_item_id", "")),
        "route_id": str(queue_row.get("route_id", "")),
        "display_name": str(queue_row.get("display_name", "")),
        "evidence_kind": "literature_route_evidence",
        "tool_name": ADAPTER_TOOL_NAME,
        "source_refs": tuple(source_refs),
        "route_evidence_nodes": tuple(route_nodes),
        "route_revision_recommended": bool(revision_reasons),
        "route_revision_reasons": tuple(sorted(dict.fromkeys(revision_reasons))),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _read_documents(
    roots: tuple[Path, ...],
    errors: list[str],
    *,
    max_file_bytes: int,
) -> tuple[dict[str, object], ...]:
    documents: list[dict[str, object]] = []
    for root in roots:
        if not root.exists():
            errors.append(f"missing literature root: {root}")
            continue
        files = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in files:
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_TEXT_EXTENSIONS:
                continue
            text = _read_text_document(path, errors, max_file_bytes=max_file_bytes)
            if not text.strip():
                continue
            title = _document_title(path, text)
            documents.append(
                {
                    "source_ref": f"file:{path.resolve()}",
                    "path": str(path.resolve()),
                    "title": title,
                    "text": text,
                    "text_lower": text.lower(),
                    "document_id": "local_literature_document:"
                    + stable_hash([str(path.resolve()), title])[:16],
                }
            )
    return tuple(documents)


def _read_text_document(
    path: Path,
    errors: list[str],
    *,
    max_file_bytes: int,
) -> str:
    try:
        raw = path.read_bytes()[:max_file_bytes]
    except Exception as exc:
        errors.append(f"failed to read {path}: {type(exc).__name__}: {exc}")
        return ""
    text = raw.decode("utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            return "\n".join(_flatten_json_strings(json.loads(text)))
        except Exception:
            return text
    if suffix == ".jsonl":
        lines = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                lines.extend(_flatten_json_strings(json.loads(line)))
            except Exception:
                lines.append(line)
        return "\n".join(lines)
    return text


def _flatten_json_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        items: list[str] = []
        for key, child in value.items():
            if isinstance(key, str):
                items.append(key)
            items.extend(_flatten_json_strings(child))
        return items
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(_flatten_json_strings(child))
        return items
    if value is None:
        return []
    return [str(value)]


def _document_title(path: Path, text: str) -> str:
    for line in text.splitlines()[:20]:
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped[:120]
    return path.stem


def _query_text(queue_row: dict[str, Any]) -> str:
    return " ".join(
        item
        for item in (
            str(queue_row.get("display_name", "")).replace(":", " "),
            " ".join(_str_tuple(queue_row.get("target_primitives", []))).replace("_", " "),
            " ".join(_str_tuple(queue_row.get("queries", []))),
            " ".join(_str_tuple(queue_row.get("trigger_conditions", []))),
        )
        if item
    )


def _query_terms(text: str) -> tuple[str, ...]:
    terms: list[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_/-]*", text.lower()):
        for part in re.split(r"[_/-]+", token):
            if len(part) >= 3 and part not in STOP_WORDS:
                terms.append(part)
    return tuple(sorted(dict.fromkeys(terms)))


def _search_documents(
    documents: tuple[dict[str, object], ...],
    query_terms: tuple[str, ...],
    target_primitives: tuple[str, ...],
    *,
    k: int,
) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    primitive_phrases = tuple(
        primitive.replace("_", " ").lower() for primitive in target_primitives
    )
    for document in documents:
        text_lower = str(document.get("text_lower", ""))
        matched_terms = tuple(term for term in query_terms if term in text_lower)
        phrase_hits = tuple(phrase for phrase in primitive_phrases if phrase in text_lower)
        exact_hits = tuple(
            primitive.lower() for primitive in target_primitives if primitive.lower() in text_lower
        )
        score = len(matched_terms) + 4 * len(phrase_hits) + 3 * len(exact_hits)
        if score <= 0:
            continue
        hits.append(
            {
                **document,
                "score": score,
                "matched_terms": matched_terms,
                "matched_primitive_phrases": phrase_hits,
                "matched_exact_primitives": exact_hits,
            }
        )
    hits.sort(
        key=lambda hit: (
            -int(hit.get("score", 0)),
            str(hit.get("source_ref", "")),
        )
    )
    return hits[:k]


def _primitive_supported_by_hits(
    primitive: str,
    hits: list[dict[str, object]],
) -> bool:
    primitive_lower = primitive.lower()
    primitive_phrase = primitive.replace("_", " ").lower()
    primitive_terms = set(_query_terms(primitive))
    for hit in hits:
        text_lower = str(hit.get("text_lower", ""))
        if primitive_lower in text_lower or primitive_phrase in text_lower:
            return True
        if primitive_terms and primitive_terms.issubset(
            set(_str_tuple(hit.get("matched_terms", [])))
        ):
            return True
    return False


def _source_refs(
    queue_row: dict[str, Any],
    hits: list[dict[str, object]],
) -> tuple[str, ...]:
    if hits:
        return tuple(
            dict.fromkeys(str(hit.get("source_ref", "")) for hit in hits if hit.get("source_ref"))
        )
    gap_id = stable_hash(
        [
            str(queue_row.get("refinement_item_id", "")),
            _query_text(queue_row),
        ]
    )[:16]
    return (f"local_literature_search_gap:{gap_id}",)


def _route_evidence_nodes(
    queue_row: dict[str, Any],
    hits: list[dict[str, object]],
    *,
    source_refs: tuple[str, ...],
    query_terms: tuple[str, ...],
    target_primitives: tuple[str, ...],
) -> list[dict[str, object]]:
    if not hits:
        return [
            {
                "node_id": "literature_search_gap:"
                + stable_hash([str(queue_row.get("refinement_item_id", "")), query_terms])[:16],
                "kind": "literature_search_gap",
                "label": "No local literature match found",
                "source_ref": source_refs[0],
                "target_primitives": target_primitives,
                "queries": _str_tuple(queue_row.get("queries", [])),
                "evidence_role": "focused literature search needed before route confidence increases",
            }
        ]
    nodes: list[dict[str, object]] = []
    for rank, hit in enumerate(hits, start=1):
        matched_terms = _str_tuple(hit.get("matched_terms", []))
        node_id = "literature_source_ref:" + stable_hash(
            [
                str(queue_row.get("refinement_item_id", "")),
                hit.get("source_ref", ""),
                matched_terms,
            ]
        )[:16]
        nodes.append(
            {
                "node_id": node_id,
                "kind": "source_ref",
                "label": str(hit.get("title", "")),
                "source_ref": str(hit.get("source_ref", "")),
                "source_path": str(hit.get("path", "")),
                "rank": rank,
                "score": int(hit.get("score", 0)),
                "matched_terms": matched_terms,
                "matched_primitive_phrases": _str_tuple(
                    hit.get("matched_primitive_phrases", [])
                ),
                "target_primitives": target_primitives,
                "excerpt": _excerpt(str(hit.get("text", "")), matched_terms),
                "evidence_role": "source-backed informal route evidence",
            }
        )
    return nodes


def _excerpt(text: str, matched_terms: tuple[str, ...]) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return ""
    lower = compact.lower()
    positions = [lower.find(term) for term in matched_terms if lower.find(term) >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - 180)
    end = min(len(compact), center + 320)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(compact) else ""
    return (prefix + compact[start:end] + suffix)[:520]


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


def _read_jsonl(path: Path | None, errors: list[str]) -> list[dict[str, Any]]:
    if path is None:
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing JSONL file: {path}")
        return []
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            errors.append(f"failed to parse {path}:{line_no}: {type(exc).__name__}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formalization Gap Planner Local Literature Adapter",
        "",
        f"- Queue rows: {payload.get('n_queue_rows')}",
        f"- Literature rows: {payload.get('n_literature_discovery_rows')}",
        f"- Documents indexed: {payload.get('n_documents_indexed')}",
        f"- Local responses: {payload.get('n_local_literature_responses')}",
        f"- Merged responses: {payload.get('n_merged_responses')}",
        f"- Source hits: {payload.get('n_source_hits')}",
        f"- Literature gaps: {payload.get('n_literature_gap_responses')}",
        f"- Route revision recommended: {payload.get('n_route_revision_recommended')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Route Evidence Node Kinds",
        "",
    ]
    for kind, count in dict(payload.get("by_route_evidence_node_kind", {})).items():
        lines.append(f"- `{kind}`: {count}")
    return "\n".join(lines) + "\n"

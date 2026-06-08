from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formal_source_index import (
    FormalSourceHit,
    FormalSourceRoot,
    build_formal_source_search_backend,
)
from .formalization_gap_planner_refinement_evidence import (
    PROOF_EVIDENCE_BOUNDARY,
    refinement_tool_response_json_schema,
    validate_refinement_tool_response_row,
)


FORMALIZATION_GAP_PLANNER_LOCAL_FORMAL_SOURCE_ADAPTER_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = (
    "FORMALIZATION_GAP_PLANNER_LOCAL_FORMAL_SOURCE_ADAPTER_NOT_PROOF_EVIDENCE"
)
ADAPTER_TOOL_NAME = "local_formal_source_index_adapter"


def export_formalization_gap_planner_local_formal_source_adapter_responses(
    formalization_gap_planner_refinement_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    formal_source_roots: tuple[FormalSourceRoot, ...] | None = None,
    formal_source_index_db: Path | None = None,
    formal_source_index_cache: Path | None = None,
    refresh_formal_source_index_cache: bool = False,
    lean_rag_db_path: Path | None = None,
    base_response_jsonl: Path | None = None,
    max_items: int = 0,
    k: int = 5,
) -> dict[str, object]:
    """Emit formal-library-grounding responses from local formal-source search.

    The adapter answers generic `formal_library_grounding` rows and legacy
    `lean_library_grounding` rows. When `base_response_jsonl` is provided,
    non-grounding responses are carried through and grounding responses are
    replaced by this adapter's local search
    results, producing one merged response JSONL for the evidence validator.
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
    formal_grounding_rows = [
        row for row in queue_rows if _is_formal_library_grounding_hook(row)
    ]

    base_responses = _read_jsonl(base_response_jsonl, errors) if base_response_jsonl else []
    base_by_item = {
        str(row.get("refinement_item_id", "")): row
        for row in base_responses
        if str(row.get("refinement_item_id", ""))
    }

    roots = formal_source_roots or tuple()
    db_path = formal_source_index_db
    if out_dir is not None and db_path is None:
        db_path = out_dir / "formalization_gap_planner_local_formal_source_index.sqlite"
    retriever = build_formal_source_search_backend(
        db_path=db_path,
        roots=roots if roots else _default_roots_marker(),
        cache_path=formal_source_index_cache,
        refresh_cache=refresh_formal_source_index_cache,
        lean_rag_db_path=lean_rag_db_path,
    )
    responses = [
        _lean_grounding_response(row, retriever, k=max(1, k))
        for row in formal_grounding_rows
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
    response_schema = refinement_tool_response_json_schema()
    local_response_schema_errors = [
        validate_refinement_tool_response_row(response, response_schema)
        for response in responses
    ]
    merged_response_schema_errors = [
        validate_refinement_tool_response_row(response, response_schema)
        for response in merged_responses
    ]
    n_local_response_schema_valid = sum(
        1 for row_errors in local_response_schema_errors if not row_errors
    )
    n_merged_response_schema_valid = sum(
        1 for row_errors in merged_response_schema_errors if not row_errors
    )

    by_coverage_status = Counter(
        status
        for response in responses
        for status in response.get("coverage_updates", {}).values()
    )
    payload: dict[str, object] = {
        "schema_version": FORMALIZATION_GAP_PLANNER_LOCAL_FORMAL_SOURCE_ADAPTER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "component_name": "formalization_gap_planner_local_formal_source_adapter",
        "formalization_gap_planner_refinement_queue_dir": str(
            formalization_gap_planner_refinement_queue_dir
        ),
        "formalization_gap_planner_refinement_queue_manifest": str(queue_manifest_path),
        "base_response_jsonl": str(base_response_jsonl or ""),
        "formal_source_index_db": str(db_path or ""),
        "formal_source_index_cache": str(formal_source_index_cache or ""),
        "lean_rag_db_path": str(lean_rag_db_path or ""),
        "search_backend": str(getattr(retriever, "source", type(retriever).__name__)),
        "cache_status": str(getattr(retriever, "cache_status", "")),
        "lean_rag_dependency_graph_enabled": bool(
            getattr(retriever, "lean_rag_dependency_graph_enabled", False)
        ),
        "lean_rag_dependency_graph_path": str(
            getattr(retriever, "lean_rag_dependency_graph_path", "")
        ),
        "n_queue_rows": len(queue_rows),
        "n_formal_library_grounding_rows": len(formal_grounding_rows),
        "n_lean_library_grounding_rows": sum(
            1
            for row in formal_grounding_rows
            if str(row.get("hook_kind", "")) == "lean_library_grounding"
        ),
        "n_base_responses": len(base_responses),
        "n_local_formal_source_responses": len(responses),
        "n_merged_responses": len(merged_responses),
        "n_local_response_schema_valid": n_local_response_schema_valid,
        "n_local_response_schema_invalid": len(local_response_schema_errors)
        - n_local_response_schema_valid,
        "n_merged_response_schema_valid": n_merged_response_schema_valid,
        "n_merged_response_schema_invalid": len(merged_response_schema_errors)
        - n_merged_response_schema_valid,
        "local_response_schema_errors": local_response_schema_errors,
        "merged_response_schema_errors": merged_response_schema_errors,
        "n_exact_exists": by_coverage_status.get("exact_exists", 0),
        "n_wrapper_needed": by_coverage_status.get("wrapper_needed", 0),
        "n_source_discovery_needed": by_coverage_status.get("source_discovery_needed", 0),
        "n_hits": sum(
            len(response.get("formal_declaration_hits", [])) for response in responses
        ),
        "k": k,
        "all_ok": not errors
        and bool(formal_grounding_rows)
        and len(responses) == len(formal_grounding_rows)
        and n_local_response_schema_valid == len(responses)
        and n_merged_response_schema_valid == len(merged_responses),
        "errors": errors,
        "by_coverage_status": dict(sorted(by_coverage_status.items())),
        "responses": responses,
        "refinement_tool_response_schema": response_schema,
        "merged_response_ids": [
            str(row.get("refinement_item_id", "")) for row in merged_responses
        ],
        "responses_fingerprint": stable_hash(responses),
        "merged_responses_fingerprint": stable_hash(merged_responses),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "local formal-source hits are declaration-grounding evidence, not theorem proof evidence",
            "coverage labels are heuristic and must be verified by target-prover replay before promotion",
            "this adapter answers formal-library grounding rows only; use other adapters for literature and prover feedback",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = (
            out_dir / "formalization_gap_planner_local_formal_source_adapter_manifest.json"
        )
        responses_path = (
            out_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        )
        local_responses_path = (
            out_dir
            / "formalization_gap_planner_local_formal_source_adapter_responses.jsonl"
        )
        response_schema_path = (
            out_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
        )
        payload["manifest_path"] = str(manifest_path)
        payload["responses_jsonl"] = str(responses_path)
        payload["local_responses_jsonl"] = str(local_responses_path)
        payload["response_schema_path"] = str(response_schema_path)
        manifest_path.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        response_schema_path.write_text(
            json.dumps(response_schema, indent=2),
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
        (out_dir / "formalization_gap_planner_local_formal_source_adapter.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _lean_grounding_response(
    queue_row: dict[str, Any],
    retriever: object,
    *,
    k: int,
) -> dict[str, object]:
    primitives = _str_tuple(queue_row.get("target_primitives", []))
    target_prover_family = _target_prover_family(queue_row)
    coverage_updates: dict[str, str] = {}
    declaration_hits: list[dict[str, object]] = []
    revision_reasons: list[str] = []
    for primitive in primitives:
        query = _primitive_query(queue_row, primitive)
        hits = _search(retriever, query, k=k)
        status = _coverage_status(primitive, hits)
        coverage_updates[primitive] = status
        if status != "exact_exists":
            revision_reasons.append(f"{primitive} classified as {status}")
        if not hits:
            revision_reasons.append(f"{primitive} had no local declaration hits")
        for rank, hit in enumerate(hits, start=1):
            declaration_hits.append(
                _hit_payload(
                    primitive,
                    query,
                    rank,
                    hit,
                    status,
                    target_prover_family=target_prover_family,
                )
            )
    lean_declaration_hits = (
        declaration_hits if _is_lean_target_prover(target_prover_family) else []
    )
    return {
        "refinement_item_id": str(queue_row.get("refinement_item_id", "")),
        "route_id": str(queue_row.get("route_id", "")),
        "display_name": str(queue_row.get("display_name", "")),
        "evidence_kind": "formal_library_grounding",
        "tool_name": ADAPTER_TOOL_NAME,
        "target_prover_family": target_prover_family,
        "formal_declaration_hits": declaration_hits,
        "lean_declaration_hits": lean_declaration_hits,
        "coverage_updates": coverage_updates,
        "route_revision_recommended": bool(revision_reasons),
        "route_revision_reasons": tuple(sorted(dict.fromkeys(revision_reasons))),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }


def _primitive_query(queue_row: dict[str, Any], primitive: str) -> str:
    return " ".join(
        item
        for item in (
            primitive.replace("_", " "),
            primitive,
            str(queue_row.get("display_name", "")).replace(":", " "),
            " ".join(_str_tuple(queue_row.get("queries", []))),
        )
        if item
    )


def _search(retriever: object, query: str, *, k: int) -> list[FormalSourceHit]:
    search = getattr(retriever, "search", None)
    if not callable(search):
        return []
    return list(search(query, k=k))


def _coverage_status(primitive: str, hits: list[FormalSourceHit]) -> str:
    if not hits:
        return "source_discovery_needed"
    primitive_tokens = _tokens(primitive)
    for hit in hits[:3]:
        name_tokens = _tokens(hit.declaration.name)
        signature_tokens = _tokens(hit.declaration.signature)
        if primitive_tokens and primitive_tokens.issubset(name_tokens | signature_tokens):
            return "exact_exists"
    return "wrapper_needed"


def _hit_payload(
    primitive: str,
    query: str,
    rank: int,
    hit: FormalSourceHit,
    coverage_status: str,
    *,
    target_prover_family: str,
) -> dict[str, object]:
    declaration = hit.declaration
    return {
        "primitive": primitive,
        "query": query,
        "rank": rank,
        "coverage_status": coverage_status if rank == 1 else "candidate_declaration",
        "declaration": declaration.name,
        "kind": declaration.kind,
        "source_id": declaration.source_id,
        "source_type": declaration.source_type,
        "path": declaration.path,
        "line": declaration.line,
        "namespace": declaration.namespace,
        "signature": declaration.signature,
        "target_prover_family": target_prover_family,
        "score": hit.score,
        "matched_terms": hit.matched_terms,
        "is_kernel_verified_declaration_hit": False,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
    }


def _default_roots_marker() -> tuple[FormalSourceRoot, ...]:
    from .formal_source_index import DEFAULT_FORMAL_SOURCE_ROOTS

    return DEFAULT_FORMAL_SOURCE_ROOTS


def _is_formal_library_grounding_hook(row: dict[str, Any]) -> bool:
    return str(row.get("hook_kind", "")) in {
        "formal_library_grounding",
        "lean_library_grounding",
    }


def _target_prover_family(row: dict[str, Any]) -> str:
    for field_name in ("target_prover_family", "target_prover"):
        text = str(row.get(field_name, "") or "").strip()
        if text:
            return text
    trace = row.get("llm_route_planner_hook_trace", {})
    if isinstance(trace, dict):
        for field_name in ("target_prover_family", "target_prover"):
            text = str(trace.get(field_name, "") or "").strip()
            if text:
                return text
    return "lean4"


def _is_lean_target_prover(target_prover_family: str) -> bool:
    key = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(target_prover_family).strip().lower(),
    ).strip("_")
    return key in {"lean", "lean4", "lean_4"} or key.startswith(
        ("lean4_", "lean_4_", "lean_")
    )


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^A-Za-z0-9]+", text.lower().replace("_", " "))
        if token and len(token) > 1
    }


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
        "# Formalization Gap Planner Local Formal-Source Adapter",
        "",
        f"- Queue rows: {payload.get('n_queue_rows')}",
        f"- Formal-grounding rows: {payload.get('n_formal_library_grounding_rows')}",
        f"- Lean-grounding rows: {payload.get('n_lean_library_grounding_rows')}",
        f"- Local responses: {payload.get('n_local_formal_source_responses')}",
        f"- Merged responses: {payload.get('n_merged_responses')}",
        f"- Local response schema valid: {payload.get('n_local_response_schema_valid')}/{payload.get('n_local_formal_source_responses')}",
        f"- Merged response schema valid: {payload.get('n_merged_response_schema_valid')}/{payload.get('n_merged_responses')}",
        f"- Hits: {payload.get('n_hits')}",
        f"- Exact exists: {payload.get('n_exact_exists')}",
        f"- Wrapper needed: {payload.get('n_wrapper_needed')}",
        f"- Source discovery needed: {payload.get('n_source_discovery_needed')}",
        f"- All OK: {payload.get('all_ok')}",
        "",
        "## Boundary",
        "",
        str(payload.get("proof_evidence_boundary", PROOF_EVIDENCE_BOUNDARY)),
        "",
        "## Coverage",
        "",
    ]
    for status, count in dict(payload.get("by_coverage_status", {})).items():
        lines.append(f"- `{status}`: {count}")
    return "\n".join(lines) + "\n"

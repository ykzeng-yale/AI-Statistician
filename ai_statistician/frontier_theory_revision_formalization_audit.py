from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formal_source_index import FormalSourceHit, FormalSourceSqliteIndex, build_formal_source_search_backend
from .retrieval import ProofBankRetriever, RetrievalQuery
from .schema import RetrievalHit


PROOF_BANK_BRIDGE_MIN_SCORE = 4.0


@dataclass(frozen=True)
class FrontierTheoryRevisionFormalizationRow:
    task_id: str
    question_id: str
    problem_class: str
    procedure_id: str
    failure_class: str
    formal_obligation: str
    query: str
    classification: str
    action: str
    proof_bank_hits: tuple[dict[str, object], ...]
    formal_source_hits: tuple[dict[str, object], ...]
    ok: bool
    errors: tuple[str, ...] = ()


def audit_frontier_theory_revision_formalization(
    revision_queue_manifest: Path,
    out_dir: Path | None = None,
    *,
    formal_source_index_path: Path | None = None,
    formal_source_retriever: Any | None = None,
    proof_bank_retriever: ProofBankRetriever | None = None,
    k: int = 5,
) -> dict[str, object]:
    """Ground new theory-revision obligations in proof-bank and Lean-source search.

    This is the bridge between simulation-driven theory revision and the formal
    proof expansion queue. It does not claim that a frontier obligation is
    proved; it classifies whether the current proof bank already has a reusable
    bridge, whether local Lean sources contain likely support, or whether the
    item is a genuine new primitive.
    """

    manifest_errors: list[str] = []
    queue = _read_json(revision_queue_manifest, manifest_errors)
    queue_rows = [item for item in queue.get("rows", []) if isinstance(item, dict)] if isinstance(queue.get("rows"), list) else []
    n_queue_obligations = sum(
        len(item.get("next_formal_obligations", []))
        for item in queue_rows
        if isinstance(item.get("next_formal_obligations", []), list)
    )
    if n_queue_obligations:
        source_retriever, source_status = _formal_source_retriever(
            formal_source_index_path=formal_source_index_path,
            formal_source_retriever=formal_source_retriever,
        )
    else:
        source_retriever, source_status = None, {
            "available": True,
            "backend": "not_needed",
            "reason": "revision queue has no formal obligations",
        }
    proof_retriever = proof_bank_retriever or ProofBankRetriever()

    rows: list[FrontierTheoryRevisionFormalizationRow] = []
    for item in queue_rows:
        obligations = item.get("next_formal_obligations", [])
        if not isinstance(obligations, list):
            obligations = []
        for obligation in obligations:
            rows.append(
                _audit_obligation(
                    item,
                    formal_obligation=str(obligation),
                    proof_retriever=proof_retriever,
                    source_retriever=source_retriever,
                    k=k,
                )
            )

    by_classification = Counter(row.classification for row in rows)
    unique_classification = _unique_classification(rows)
    by_unique_classification = Counter(unique_classification.values())
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "revision_queue_manifest": str(revision_queue_manifest),
        "formal_source_index_path": str(formal_source_index_path or ""),
        "formal_source_retriever_status": source_status,
        "n_revision_tasks": int(queue.get("n_tasks", 0) or 0),
        "n_obligations": len(rows),
        "n_unique_obligations": len(unique_classification),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not manifest_errors and source_status["available"] and all(row.ok for row in rows),
        "manifest_errors": manifest_errors,
        "by_classification": dict(sorted(by_classification.items())),
        "by_unique_classification": dict(sorted(by_unique_classification.items())),
        "n_proof_bank_bridge": by_classification.get("proof_bank_bridge", 0),
        "n_local_source_only": by_classification.get("local_source_only", 0),
        "n_source_gap": by_classification.get("source_gap", 0),
        "n_unique_proof_bank_bridge": by_unique_classification.get("proof_bank_bridge", 0),
        "n_unique_local_source_only": by_unique_classification.get("local_source_only", 0),
        "n_unique_source_gap": by_unique_classification.get("source_gap", 0),
        "formalization_fingerprint": stable_hash([asdict(row) for row in rows]),
        "rows": [asdict(row) for row in rows],
        "limitations": [
            "proof-bank bridges are premise candidates, not proofs of the new frontier obligation",
            "local-source-only rows require proof-bank promotion and AXLE verification before release claims",
            "source-gap rows are explicit new formal primitive backlog items",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "frontier_theory_revision_formalization_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "frontier_theory_revision_formalization_tasks.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "frontier_theory_revision_formalization.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _audit_obligation(
    item: dict[str, Any],
    *,
    formal_obligation: str,
    proof_retriever: ProofBankRetriever,
    source_retriever: Any,
    k: int,
) -> FrontierTheoryRevisionFormalizationRow:
    errors: list[str] = []
    query = _query_text(item, formal_obligation)
    proof_hits = proof_retriever.retrieve(
        RetrievalQuery(
            text=query,
            tags=tuple(
                str(tag)
                for tag in (
                    item.get("problem_class", ""),
                    item.get("failure_class", ""),
                    "frontier_theory_revision",
                )
                if str(tag)
            ),
        ),
        k=k,
    )
    source_hits = source_retriever.search(query, k=k) if source_retriever is not None else []
    proof_payload = tuple(_proof_hit_payload(hit) for hit in proof_hits)
    source_payload = tuple(_source_hit_payload(hit) for hit in source_hits)

    if not formal_obligation:
        errors.append("formal_obligation missing")
    if not item.get("task_id"):
        errors.append("task_id missing")
    classification, action = _classification(proof_hits, source_hits)
    return FrontierTheoryRevisionFormalizationRow(
        task_id=str(item.get("task_id", "")),
        question_id=str(item.get("question_id", "")),
        problem_class=str(item.get("problem_class", "")),
        procedure_id=str(item.get("procedure_id", "")),
        failure_class=str(item.get("failure_class", "")),
        formal_obligation=formal_obligation,
        query=query,
        classification=classification,
        action=action,
        proof_bank_hits=proof_payload,
        formal_source_hits=source_payload,
        ok=not errors,
        errors=tuple(errors),
    )


def _formal_source_retriever(
    *,
    formal_source_index_path: Path | None,
    formal_source_retriever: Any | None,
) -> tuple[Any | None, dict[str, object]]:
    if formal_source_retriever is not None:
        return formal_source_retriever, {"available": True, "backend": getattr(formal_source_retriever, "source", "custom")}
    if formal_source_index_path is None:
        return None, {"available": False, "backend": "", "reason": "formal_source_index_path missing"}
    index = FormalSourceSqliteIndex(formal_source_index_path)
    if index.is_healthy():
        declarations = index.load_declarations()
        from .formal_source_hybrid import FormalSourceHybridRetriever

        return (
            FormalSourceHybridRetriever(declarations, index),
            {
                "available": True,
                "backend": "sqlite_fts_shape+symbol_graph",
                "index_path": str(formal_source_index_path),
                "declarations": len(declarations),
                "cache_status": "existing",
            },
        )
    retriever = build_formal_source_search_backend(db_path=formal_source_index_path, include_graph=True)
    return (
        retriever,
        {
            "available": True,
            "backend": getattr(retriever, "source", "formal_source_search"),
            "index_path": str(formal_source_index_path),
            "cache_status": getattr(retriever, "cache_status", "rebuilt"),
            "declarations": len(retriever.load_declarations()) if hasattr(retriever, "load_declarations") else 0,
        },
    )


def _query_text(item: dict[str, Any], formal_obligation: str) -> str:
    context = [
        formal_obligation,
        str(item.get("failure_class", "")),
        str(item.get("problem_class", "")),
        str(item.get("procedure_id", "")),
        " ".join(str(row) for row in item.get("target_theorem_goals", []) or []),
        " ".join(str(row) for row in item.get("revised_theorem_goals", []) or []),
        " ".join(str(row) for row in item.get("assumption_delta", []) or []),
    ]
    return " ".join(part for part in context if part).strip()


def _classification(
    proof_hits: list[RetrievalHit],
    source_hits: list[FormalSourceHit],
) -> tuple[str, str]:
    if proof_hits and float(proof_hits[0].score) >= PROOF_BANK_BRIDGE_MIN_SCORE:
        return "proof_bank_bridge", "promote_proof_bank_bridge_to_revision_obligation"
    if source_hits:
        return "local_source_only", "mine_local_lean_source_for_proof_bank_candidate"
    return "source_gap", "formalize_new_statistical_primitive"


def _proof_hit_payload(hit: RetrievalHit) -> dict[str, object]:
    return {
        "obligation_id": hit.obligation_id,
        "score": hit.score,
        "source": hit.source,
        "matched_terms": list(hit.matched_terms),
    }


def _source_hit_payload(hit: FormalSourceHit) -> dict[str, object]:
    decl = hit.declaration
    return {
        "name": decl.name,
        "kind": decl.kind,
        "source_id": decl.source_id,
        "path": decl.path,
        "line": decl.line,
        "namespace": decl.namespace,
        "score": hit.score,
        "matched_terms": list(hit.matched_terms),
        "signature": decl.signature[:500],
        "imports": decl.imports,
        "reference": decl.reference,
        "declaration_doc": decl.declaration_doc,
        "section_summary": decl.section_summary,
        "module_group": decl.module_group,
        "module_group_summary": decl.module_group_summary,
    }


def _unique_classification(rows: list[FrontierTheoryRevisionFormalizationRow]) -> dict[str, str]:
    rank = {
        "source_gap": 0,
        "local_source_only": 1,
        "proof_bank_bridge": 2,
    }
    best: dict[str, str] = {}
    for row in rows:
        current = best.get(row.formal_obligation)
        if current is None or rank[row.classification] > rank[current]:
            best[row.formal_obligation] = row.classification
    return best


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("rows", [])
    lines = [
        "# Frontier Theory Revision Formalization Audit",
        "",
        "This audit grounds simulation-driven TheoryDeveloper revision obligations",
        "against the verified proof bank and local Lean-source retrieval index.",
        "",
        f"- Revision queue manifest: `{payload.get('revision_queue_manifest')}`",
        f"- Obligations: {payload.get('n_ok')}/{payload.get('n_obligations')} audit-clean",
        f"- Unique obligations: {payload.get('n_unique_obligations')}",
        f"- Proof-bank bridge rows: {payload.get('n_proof_bank_bridge')}",
        f"- Local-source-only rows: {payload.get('n_local_source_only')}",
        f"- Source-gap rows: {payload.get('n_source_gap')}",
        f"- Fingerprint: `{payload.get('formalization_fingerprint')}`",
        "",
        "## Rows",
        "",
        "| Question | Obligation | Classification | Action | Top evidence |",
        "|---|---|---|---|---|",
    ]
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            evidence = _top_evidence(row)
            lines.append(
                f"| `{row.get('question_id')}` | `{row.get('formal_obligation')}` | "
                f"`{row.get('classification')}` | `{row.get('action')}` | {evidence} |"
            )
    return "\n".join(lines) + "\n"


def _top_evidence(row: dict[str, object]) -> str:
    proof_hits = row.get("proof_bank_hits", [])
    if isinstance(proof_hits, list) and proof_hits:
        first = proof_hits[0]
        if isinstance(first, dict):
            return f"proof-bank `{first.get('obligation_id')}` score={first.get('score')}"
    source_hits = row.get("formal_source_hits", [])
    if isinstance(source_hits, list) and source_hits:
        first = source_hits[0]
        if isinstance(first, dict):
            return f"{first.get('source_id')} `{first.get('name')}`"
    return "none"

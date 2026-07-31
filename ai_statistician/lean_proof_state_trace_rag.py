from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


AI4SLT_TRACE_SOURCE_ID = "ai4slt_novel_train_proof_state_traces"
AI4SLT_TRACE_ANCHOR_SOURCE_IDS = (
    "lean_stat_learning_theory",
    "ai4slt_companion_premise_corpus",
    AI4SLT_TRACE_SOURCE_ID,
)
AI4SLT_TRACE_DATASET_ID = "yuanhezhang/lean4-stat-learning-theory-novel"
AI4SLT_TRACE_DATASET_URL = (
    "https://huggingface.co/datasets/"
    "yuanhezhang/lean4-stat-learning-theory-novel"
)
AI4SLT_TRACE_REPOSITORY_URL = (
    "https://github.com/YuanheZ/lean-stat-learning-theory"
)
AI4SLT_TRACE_LICENSE = "Apache-2.0"
AI4SLT_TRACE_DATASET_REVISION = "d90449a3ce738ca05ae90f530da0d7a4d3448e26"
AI4SLT_TRACE_SPLIT = "novel/train"
AI4SLT_TRACE_SHA256 = (
    "007ad0af7add62b8fb7bd10c5c02fdaa54871d403baea99ff34399631d4ab89c"
)
AI4SLT_TRACE_TOOLCHAIN = "leanprover/lean4:v4.27.0-rc1"
AI4SLT_TRACE_MATHLIB_REVISION = (
    "d68c4dc09f5e000d3c968adae8def120a0758729"
)
AI4SLT_TRACE_INDEX_SCHEMA_VERSION = 1

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_']*|[0-9]+")
_STOP_TOKENS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "case",
    "error",
    "for",
    "from",
    "goal",
    "have",
    "in",
    "is",
    "lemma",
    "of",
    "on",
    "or",
    "the",
    "theorem",
    "to",
    "type",
    "with",
}
_PROOF_STATE_SIGNAL_KEYS = {
    "compiler_feedback",
    "diagnostics",
    "error",
    "errors",
    "failure_feedback",
    "first_error",
    "lean_diagnostic_messages",
    "lean_goal",
    "local_lean_stderr",
    "local_lean_stdout",
    "message",
    "prior_exact_candidate_feedback",
    "proof_state",
    "residual_goal_excerpt",
    "residual_goals",
    "state",
    "state_before",
    "stderr",
    "stdout",
}


@dataclass(frozen=True)
class LeanProofStateTraceHit:
    trace_id: str
    file_path: str
    module: str
    theorem_name: str
    theorem_statement: str
    step_index: int
    state_before: str
    tactic: str
    state_after: str
    premise_provenance: tuple[dict[str, str], ...]
    score: float


class LeanProofStateTraceRetriever:
    """Versioned, source-scoped retrieval over Lean tactic-state transitions."""

    source = "ai4slt_proof_state_trace_rag"

    def __init__(
        self,
        trace_path: Path | str,
        *,
        index_path: Path | str | None = None,
        source_id: str = AI4SLT_TRACE_SOURCE_ID,
        anchor_source_ids: Sequence[str] = AI4SLT_TRACE_ANCHOR_SOURCE_IDS,
        dataset_id: str = AI4SLT_TRACE_DATASET_ID,
        dataset_revision: str = AI4SLT_TRACE_DATASET_REVISION,
        split: str = AI4SLT_TRACE_SPLIT,
        toolchain: str = AI4SLT_TRACE_TOOLCHAIN,
        mathlib_revision: str = AI4SLT_TRACE_MATHLIB_REVISION,
        expected_sha256: str = AI4SLT_TRACE_SHA256,
    ) -> None:
        self.trace_path = Path(trace_path).expanduser()
        self.index_path = (
            Path(index_path).expanduser()
            if index_path is not None
            else self.trace_path.with_suffix(".sqlite")
        )
        self.source_id = str(source_id)
        self.anchor_source_ids = tuple(
            dict.fromkeys(
                str(value).strip()
                for value in anchor_source_ids
                if str(value).strip()
            )
        )
        self.dataset_id = str(dataset_id)
        self.dataset_revision = str(dataset_revision)
        self.split = str(split)
        self.toolchain = str(toolchain)
        self.mathlib_revision = str(mathlib_revision)
        self.expected_sha256 = str(expected_sha256)
        self._health_cache: dict[str, Any] | None = None

    @property
    def trace_sha256(self) -> str:
        return _file_sha256(self.trace_path)

    def supports_source_scope(self, source_scope_ids: Sequence[str]) -> bool:
        requested = {
            str(value).strip()
            for value in source_scope_ids
            if str(value).strip()
        }
        return not requested or bool(requested.intersection(self.anchor_source_ids))

    def ensure_index(self) -> bool:
        if not self.trace_path.is_file():
            return False
        source_hash = self.trace_sha256
        if self.expected_sha256 and source_hash != self.expected_sha256:
            return False
        if self._index_is_current(source_hash):
            return True
        self._build_index(source_hash)
        self._health_cache = None
        return self._index_is_current(source_hash)

    def health_report(self, *, refresh: bool = False) -> dict[str, Any]:
        if self._health_cache is not None and not refresh:
            return dict(self._health_cache)
        source_hash = self.trace_sha256 if self.trace_path.is_file() else ""
        report: dict[str, Any] = {
            "source_id": self.source_id,
            "anchor_source_ids": list(self.anchor_source_ids),
            "dataset_id": self.dataset_id,
            "dataset_url": (
                AI4SLT_TRACE_DATASET_URL
                if self.dataset_id == AI4SLT_TRACE_DATASET_ID
                else ""
            ),
            "repository_url": (
                AI4SLT_TRACE_REPOSITORY_URL
                if self.dataset_id == AI4SLT_TRACE_DATASET_ID
                else ""
            ),
            "license": (
                AI4SLT_TRACE_LICENSE
                if self.dataset_id == AI4SLT_TRACE_DATASET_ID
                else ""
            ),
            "dataset_revision": self.dataset_revision,
            "split": self.split,
            "trace_path": str(self.trace_path),
            "trace_sha256": source_hash,
            "expected_sha256": self.expected_sha256,
            "checksum_ok": bool(
                source_hash
                and (not self.expected_sha256 or source_hash == self.expected_sha256)
            ),
            "index_path": str(self.index_path),
            "index_exists": self.index_path.is_file(),
            "index_schema_version": 0,
            "n_theorems": 0,
            "n_trace_steps": 0,
            "n_steps_with_premise_provenance": 0,
            "toolchain": self.toolchain,
            "mathlib_revision": self.mathlib_revision,
            "split_policy": "train_only_external_validation_and_test_excluded",
            "prompt_content_policy": (
                "bounded_state_action_transitions_and_premise_provenance_only"
            ),
            "proof_evidence_status": (
                "VERSIONED_PROOF_STATE_RETRIEVAL_CONTEXT_NOT_PROOF_EVIDENCE"
            ),
            "all_ok": False,
        }
        if report["checksum_ok"] and self.index_path.is_file():
            try:
                with closing(sqlite3.connect(self.index_path)) as conn:
                    metadata = dict(
                        conn.execute("SELECT key, value FROM metadata").fetchall()
                    )
                    report["index_schema_version"] = int(
                        metadata.get("schema_version", 0) or 0
                    )
                    report["n_theorems"] = int(
                        metadata.get("n_theorems", 0) or 0
                    )
                    report["n_trace_steps"] = int(
                        metadata.get("n_trace_steps", 0) or 0
                    )
                    report["n_steps_with_premise_provenance"] = int(
                        metadata.get("n_steps_with_premise_provenance", 0) or 0
                    )
                    integrity = str(
                        conn.execute("PRAGMA integrity_check").fetchone()[0] or ""
                    )
                    report["integrity_check"] = integrity
                    report["all_ok"] = bool(
                        integrity.lower() == "ok"
                        and metadata.get("trace_sha256", "") == source_hash
                        and metadata.get("dataset_id", "") == self.dataset_id
                        and metadata.get("dataset_revision", "")
                        == self.dataset_revision
                        and metadata.get("split", "") == self.split
                        and metadata.get("toolchain", "") == self.toolchain
                        and metadata.get("mathlib_revision", "")
                        == self.mathlib_revision
                        and report["index_schema_version"]
                        == AI4SLT_TRACE_INDEX_SCHEMA_VERSION
                        and report["n_trace_steps"] > 0
                    )
            except (sqlite3.DatabaseError, OSError, ValueError) as exc:
                report["index_error"] = f"{type(exc).__name__}: {exc}"
        self._health_cache = dict(report)
        return report

    def search(
        self,
        query: str,
        *,
        k: int = 3,
        source_scope_ids: Sequence[str] = (),
    ) -> list[LeanProofStateTraceHit]:
        if (
            k <= 0
            or not self.supports_source_scope(source_scope_ids)
            or not self.ensure_index()
        ):
            return []
        fts_query = _fts_query(query)
        query_tokens = set(_ordered_tokens(query))
        if not fts_query or not query_tokens:
            return []
        candidate_limit = max(int(k) * 24, 80)
        try:
            with closing(sqlite3.connect(self.index_path)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT s.*, bm25(trace_fts) AS fts_rank
                    FROM trace_fts
                    JOIN trace_steps s ON s.id = trace_fts.step_id
                    WHERE trace_fts MATCH ?
                    ORDER BY fts_rank, s.id
                    LIMIT ?
                    """,
                    (fts_query, candidate_limit),
                ).fetchall()
        except sqlite3.DatabaseError:
            return []

        ranked: list[LeanProofStateTraceHit] = []
        for rank, row in enumerate(rows, start=1):
            state_tokens = set(_ordered_tokens(str(row["state_before"] or "")))
            theorem_tokens = set(
                _ordered_tokens(
                    " ".join(
                        (
                            str(row["theorem_name"] or ""),
                            str(row["theorem_statement"] or ""),
                            str(row["module"] or ""),
                        )
                    )
                )
            )
            provenance_rows = _json_provenance(row["premise_provenance"])
            premise_tokens = set(
                _ordered_tokens(
                    " ".join(
                        str(item.get("full_name", "") or "")
                        for item in provenance_rows
                    )
                )
            )
            tactic_tokens = set(_ordered_tokens(str(row["tactic"] or "")))
            state_overlap = len(query_tokens.intersection(state_tokens))
            theorem_overlap = len(query_tokens.intersection(theorem_tokens))
            premise_overlap = len(query_tokens.intersection(premise_tokens))
            tactic_overlap = len(query_tokens.intersection(tactic_tokens))
            weighted_overlap = (
                3.0 * state_overlap
                + 1.5 * premise_overlap
                + theorem_overlap
                + 0.5 * tactic_overlap
            )
            if weighted_overlap <= 0:
                continue
            score = weighted_overlap / math.sqrt(
                max(1, len(query_tokens))
                * max(
                    1,
                    len(state_tokens | theorem_tokens | premise_tokens),
                )
            )
            score += 1.0 / (20.0 + rank)
            ranked.append(
                LeanProofStateTraceHit(
                    trace_id=str(row["trace_id"] or ""),
                    file_path=str(row["file_path"] or ""),
                    module=str(row["module"] or ""),
                    theorem_name=str(row["theorem_name"] or ""),
                    theorem_statement=str(row["theorem_statement"] or ""),
                    step_index=int(row["step_index"] or 0),
                    state_before=str(row["state_before"] or ""),
                    tactic=str(row["tactic"] or ""),
                    state_after=str(row["state_after"] or ""),
                    premise_provenance=tuple(provenance_rows),
                    score=score,
                )
            )
        ranked.sort(
            key=lambda hit: (
                -hit.score,
                hit.theorem_name,
                hit.step_index,
                hit.trace_id,
            )
        )
        selected: list[LeanProofStateTraceHit] = []
        seen_theorems: set[str] = set()
        for hit in ranked:
            if hit.theorem_name in seen_theorems:
                continue
            selected.append(hit)
            seen_theorems.add(hit.theorem_name)
            if len(selected) >= int(k):
                break
        return selected

    def _index_is_current(self, source_hash: str) -> bool:
        if not self.index_path.is_file():
            return False
        try:
            with closing(sqlite3.connect(self.index_path)) as conn:
                tables = {
                    str(row[0])
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type IN ('table', 'virtual table')"
                    ).fetchall()
                }
                if not {"metadata", "trace_steps", "trace_fts"}.issubset(tables):
                    return False
                metadata = dict(
                    conn.execute("SELECT key, value FROM metadata").fetchall()
                )
        except (sqlite3.DatabaseError, ValueError):
            return False
        return bool(
            metadata.get("trace_sha256", "") == source_hash
            and metadata.get("dataset_id", "") == self.dataset_id
            and metadata.get("dataset_revision", "") == self.dataset_revision
            and metadata.get("split", "") == self.split
            and metadata.get("toolchain", "") == self.toolchain
            and metadata.get("mathlib_revision", "") == self.mathlib_revision
            and int(metadata.get("schema_version", 0) or 0)
            == AI4SLT_TRACE_INDEX_SCHEMA_VERSION
        )

    def _build_index(self, source_hash: str) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.index_path.with_name(
            self.index_path.name + f".tmp.{os.getpid()}"
        )
        temp_path.unlink(missing_ok=True)
        n_theorems = 0
        n_steps = 0
        n_with_provenance = 0
        try:
            with closing(sqlite3.connect(temp_path)) as conn:
                conn.execute("PRAGMA journal_mode=OFF")
                conn.execute("PRAGMA synchronous=OFF")
                conn.execute(
                    "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
                )
                conn.execute(
                    """
                    CREATE TABLE trace_steps (
                        id INTEGER PRIMARY KEY,
                        trace_id TEXT NOT NULL UNIQUE,
                        file_path TEXT NOT NULL,
                        module TEXT NOT NULL,
                        theorem_name TEXT NOT NULL,
                        theorem_statement TEXT NOT NULL,
                        step_index INTEGER NOT NULL,
                        state_before TEXT NOT NULL,
                        tactic TEXT NOT NULL,
                        state_after TEXT NOT NULL,
                        premise_provenance TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE trace_fts USING fts5(
                        step_id UNINDEXED,
                        theorem_name,
                        theorem_statement,
                        module,
                        state_before,
                        tactic,
                        premise_names
                    )
                    """
                )
                with self.trace_path.open("r", encoding="utf-8") as handle:
                    for raw_line in handle:
                        if not raw_line.strip():
                            continue
                        record = json.loads(raw_line)
                        if not isinstance(record, Mapping):
                            continue
                        theorem_name = str(
                            record.get("full_name", "") or ""
                        ).strip()
                        theorem_statement = str(
                            record.get("theorem_statement", "") or ""
                        ).strip()
                        file_path = str(record.get("file_path", "") or "").strip()
                        steps = record.get("traced_tactics", []) or []
                        if not theorem_name or not isinstance(steps, list):
                            continue
                        n_theorems += 1
                        module = _lean_module_from_path(file_path)
                        for step_index, raw_step in enumerate(steps):
                            if not isinstance(raw_step, Mapping):
                                continue
                            state_before = str(
                                raw_step.get("state_before", "") or ""
                            ).strip()
                            tactic = str(raw_step.get("tactic", "") or "").strip()
                            state_after = str(
                                raw_step.get("state_after", "") or ""
                            ).strip()
                            if not state_before or not tactic:
                                continue
                            provenance = _normalize_provenance(
                                raw_step.get(
                                    "annotated_tactic_provenances",
                                    [],
                                )
                            )
                            trace_id = "ai4slt_trace:" + stable_hash(
                                [
                                    self.dataset_revision,
                                    self.split,
                                    theorem_name,
                                    step_index,
                                    state_before,
                                    tactic,
                                    state_after,
                                ]
                            )[:24]
                            n_steps += 1
                            if provenance:
                                n_with_provenance += 1
                            conn.execute(
                                """
                                INSERT INTO trace_steps (
                                    id, trace_id, file_path, module, theorem_name,
                                    theorem_statement, step_index, state_before,
                                    tactic, state_after, premise_provenance
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    n_steps,
                                    trace_id,
                                    file_path,
                                    module,
                                    theorem_name,
                                    theorem_statement,
                                    step_index,
                                    state_before,
                                    tactic,
                                    state_after,
                                    json.dumps(
                                        provenance,
                                        ensure_ascii=False,
                                        sort_keys=True,
                                    ),
                                ),
                            )
                            conn.execute(
                                """
                                INSERT INTO trace_fts (
                                    step_id, theorem_name, theorem_statement,
                                    module, state_before, tactic, premise_names
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    n_steps,
                                    theorem_name,
                                    theorem_statement,
                                    module,
                                    state_before,
                                    tactic,
                                    " ".join(
                                        row.get("full_name", "")
                                        for row in provenance
                                    ),
                                ),
                            )
                metadata = {
                    "schema_version": str(AI4SLT_TRACE_INDEX_SCHEMA_VERSION),
                    "source_id": self.source_id,
                    "dataset_id": self.dataset_id,
                    "dataset_revision": self.dataset_revision,
                    "split": self.split,
                    "trace_sha256": source_hash,
                    "toolchain": self.toolchain,
                    "mathlib_revision": self.mathlib_revision,
                    "n_theorems": str(n_theorems),
                    "n_trace_steps": str(n_steps),
                    "n_steps_with_premise_provenance": str(n_with_provenance),
                }
                conn.executemany(
                    "INSERT INTO metadata (key, value) VALUES (?, ?)",
                    sorted(metadata.items()),
                )
                conn.execute(
                    "CREATE INDEX trace_steps_theorem_idx "
                    "ON trace_steps(theorem_name, step_index)"
                )
                conn.commit()
            os.replace(temp_path, self.index_path)
        finally:
            temp_path.unlink(missing_ok=True)


def discover_ai4slt_proof_state_trace_retriever(
) -> LeanProofStateTraceRetriever | None:
    if not _ai4slt_proof_state_trace_rag_enabled():
        return None
    trace_path = _discover_ai4slt_trace_path()
    if trace_path is None:
        return None
    explicit_index = str(
        os.environ.get("AI_STATISTICIAN_AI4SLT_PROOF_STATE_TRACE_INDEX", "")
        or ""
    ).strip()
    index_path = (
        Path(explicit_index).expanduser()
        if explicit_index
        else trace_path.with_suffix(".sqlite")
    )
    try:
        stat = trace_path.stat()
        retriever = _discover_ai4slt_trace_retriever_cached(
            str(trace_path.resolve()),
            stat.st_mtime_ns,
            stat.st_size,
            str(index_path.resolve()),
        )
        return retriever if retriever.ensure_index() else None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, sqlite3.DatabaseError):
        return None


def _ai4slt_proof_state_trace_rag_enabled() -> bool:
    enabled = str(
        os.environ.get(
            "AI_STATISTICIAN_AI4SLT_PROOF_STATE_TRACE_ENABLED",
            "1",
        )
        or ""
    ).strip().lower()
    return enabled not in {"0", "false", "no", "off"}


@lru_cache(maxsize=4)
def _discover_ai4slt_trace_retriever_cached(
    trace_path: str,
    _mtime_ns: int,
    _size: int,
    index_path: str,
) -> LeanProofStateTraceRetriever:
    return LeanProofStateTraceRetriever(trace_path, index_path=index_path)


def attach_ai4slt_proof_state_trace_rag(
    context: Mapping[str, Any],
    *,
    formal_source_retriever: Any | None = None,
    trace_retriever: LeanProofStateTraceRetriever | None = None,
    max_hits: int = 3,
) -> dict[str, Any]:
    """Attach bounded state-action analogies to an existing ProofEngineer packet."""

    payload = dict(context) if isinstance(context, Mapping) else {}
    if (
        trace_retriever is None
        and not _ai4slt_proof_state_trace_rag_enabled()
    ):
        payload.pop("proof_state_trace_rag", None)
        return payload
    query_parts, query_roles = _proof_state_query_parts(payload)
    if not query_parts:
        return payload
    query_fingerprint = stable_hash(query_parts)
    existing = payload.get("proof_state_trace_rag", {})
    expected_source_id = (
        trace_retriever.source_id
        if trace_retriever is not None
        else AI4SLT_TRACE_SOURCE_ID
    )
    expected_dataset_revision = (
        trace_retriever.dataset_revision
        if trace_retriever is not None
        else AI4SLT_TRACE_DATASET_REVISION
    )
    expected_trace_sha256 = (
        trace_retriever.trace_sha256
        if trace_retriever is not None
        else AI4SLT_TRACE_SHA256
    )
    if (
        isinstance(existing, Mapping)
        and str(existing.get("query_fingerprint", "") or "")
        == query_fingerprint
        and str(existing.get("source_id", "") or "") == expected_source_id
        and str(existing.get("dataset_revision", "") or "")
        == expected_dataset_revision
        and str(existing.get("trace_sha256", "") or "")
        == expected_trace_sha256
    ):
        return payload
    provider = trace_retriever or discover_ai4slt_proof_state_trace_retriever()
    if provider is None:
        payload.pop("proof_state_trace_rag", None)
        return payload
    source_scope_ids = _formal_source_scope_ids(payload)
    hits = provider.search(
        "\n".join(query_parts),
        k=max(0, int(max_hits)),
        source_scope_ids=source_scope_ids,
    )
    if not hits:
        payload.pop("proof_state_trace_rag", None)
        return payload
    hit_payloads = [
        _trace_hit_prompt_payload(
            hit,
            formal_source_retriever=formal_source_retriever,
        )
        for hit in hits
    ]
    target_declaration = _target_lean_declaration(payload)
    n_target_name_overlap_hits = 0
    for hit_payload in hit_payloads:
        overlap = _declaration_name_overlap(
            target_declaration,
            str(hit_payload.get("source_theorem_name", "") or ""),
        )
        if overlap:
            hit_payload["target_name_overlap"] = overlap
            n_target_name_overlap_hits += 1
    payload["proof_state_trace_rag"] = {
        "schema_version": 1,
        "provider": provider.source,
        "source_id": provider.source_id,
        "anchor_source_ids": list(provider.anchor_source_ids),
        "dataset_id": provider.dataset_id,
        "dataset_url": (
            AI4SLT_TRACE_DATASET_URL
            if provider.dataset_id == AI4SLT_TRACE_DATASET_ID
            else ""
        ),
        "repository_url": (
            AI4SLT_TRACE_REPOSITORY_URL
            if provider.dataset_id == AI4SLT_TRACE_DATASET_ID
            else ""
        ),
        "license": (
            AI4SLT_TRACE_LICENSE
            if provider.dataset_id == AI4SLT_TRACE_DATASET_ID
            else ""
        ),
        "dataset_revision": provider.dataset_revision,
        "trace_sha256": provider.trace_sha256,
        "split": provider.split,
        "toolchain": provider.toolchain,
        "mathlib_revision": provider.mathlib_revision,
        "query_fingerprint": query_fingerprint,
        "query_roles": query_roles,
        "n_hits": len(hit_payloads),
        "n_target_name_overlap_hits": n_target_name_overlap_hits,
        "hits": hit_payloads,
        "selection_policy": (
            "proof_state_similarity_with_at_most_one_transition_per_source_theorem"
        ),
        "use_policy": (
            "Treat each transition as an analogy for the current local goal, not a "
            "tactic template. Recheck premise visibility and current signatures, make "
            "the smallest target-preserving change justified by the current state, "
            "then rerun the exact artifact through local Lean or AXLE."
        ),
        "version_boundary": (
            "The trace corpus was extracted under an older Lean/Mathlib revision. "
            "No tactic or premise is current-project evidence until re-elaborated."
        ),
        "evaluation_contamination_policy": (
            "Exact qualified- or short-name overlap with the current target is "
            "recorded on the hit. Such a hit may support production theorem reuse "
            "but must be declared and excluded from any held-out generalization "
            "claim."
        ),
        "proof_evidence_status": (
            "PROOF_STATE_TRACE_RETRIEVAL_CONTEXT_NOT_PROOF_EVIDENCE"
        ),
    }
    tools = [
        str(value)
        for value in payload.get("available_runtime_tools", []) or []
        if str(value)
    ]
    if provider.source not in tools:
        tools.append(provider.source)
    if tools:
        payload["available_runtime_tools"] = tools
    return payload


def _target_lean_declaration(context: Mapping[str, Any]) -> str:
    for value in (
        context.get("target_lean_declaration", ""),
        context.get("target_theorem_name", ""),
    ):
        normalized = str(value or "").strip()
        if normalized:
            return normalized
    openprover_task = context.get("openprover_task", {})
    if isinstance(openprover_task, Mapping):
        return str(
            openprover_task.get("target_lean_declaration", "") or ""
        ).strip()
    return ""


def _declaration_name_overlap(left: str, right: str) -> str:
    normalized_left = str(left or "").strip()
    normalized_right = str(right or "").strip()
    if not normalized_left or not normalized_right:
        return ""
    if normalized_left == normalized_right:
        return "EXACT_QUALIFIED_NAME_OVERLAP"
    if (
        normalized_left.rsplit(".", 1)[-1]
        == normalized_right.rsplit(".", 1)[-1]
    ):
        return "EXACT_SHORT_NAME_OVERLAP"
    return ""


def _trace_hit_prompt_payload(
    hit: LeanProofStateTraceHit,
    *,
    formal_source_retriever: Any | None,
) -> dict[str, Any]:
    premise_rows = _bind_premises_to_current_declarations(
        hit.premise_provenance,
        formal_source_retriever=formal_source_retriever,
    )
    return {
        "trace_id": hit.trace_id,
        "source_theorem_name": hit.theorem_name,
        "source_module": hit.module,
        "source_file_path": hit.file_path,
        "source_theorem_statement": hit.theorem_statement[:1800],
        "step_index": hit.step_index,
        "state_before": hit.state_before[:2600],
        "tactic": hit.tactic[:1000],
        "state_after": hit.state_after[:1800],
        "premise_provenance": premise_rows,
        "score": round(hit.score, 6),
        "candidate_status": (
            "ANALOGICAL_STATE_ACTION_REQUIRES_CURRENT_PROJECT_REVALIDATION"
        ),
    }


def _bind_premises_to_current_declarations(
    provenance: Sequence[Mapping[str, Any]],
    *,
    formal_source_retriever: Any | None,
    max_rows: int = 6,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_row in provenance:
        full_name = str(raw_row.get("full_name", "") or "").strip()
        def_path = str(raw_row.get("def_path", "") or "").strip()
        if not full_name:
            continue
        candidates = _current_declaration_candidates(
            formal_source_retriever,
            full_name,
        )
        path_matches = [
            declaration
            for declaration in candidates
            if _source_paths_match(
                str(getattr(declaration, "path", "") or ""),
                def_path,
            )
        ]
        selected = (
            path_matches[0]
            if len(path_matches) == 1
            else candidates[0]
            if len(candidates) == 1
            else None
        )
        row: dict[str, Any] = {
            "full_name": full_name,
            "trace_def_path": def_path,
        }
        if selected is not None:
            row.update(
                {
                    "current_resolution_status": (
                        "CURRENT_FORMAL_SOURCE_INDEX_EXACT_NAME_AND_PATH"
                        if len(path_matches) == 1
                        else "CURRENT_FORMAL_SOURCE_INDEX_EXACT_NAME"
                    ),
                    "current_source_id": str(
                        getattr(selected, "source_id", "") or ""
                    ),
                    "current_path": str(getattr(selected, "path", "") or ""),
                    "current_kind": str(getattr(selected, "kind", "") or ""),
                    "current_signature": str(
                        getattr(selected, "signature", "") or ""
                    )[:1400],
                    "current_reference": str(
                        getattr(selected, "reference", "") or ""
                    ),
                }
            )
        else:
            row["current_resolution_status"] = (
                "AMBIGUOUS_CURRENT_EXACT_NAME"
                if candidates
                else "NOT_IN_CURRENT_FORMAL_SOURCE_INDEX"
            )
            row["required_action"] = (
                "Resolve this premise through current formal-source or Lean search "
                "before using the retrieved tactic."
            )
        rows.append(row)
        if len(rows) >= max(0, int(max_rows)):
            break
    return rows


def _current_declaration_candidates(
    retriever: Any | None,
    full_name: str,
) -> list[Any]:
    if retriever is None:
        return []
    index = getattr(
        retriever,
        "_proof_state_trace_loaded_declarations_by_exact_name",
        None,
    )
    if isinstance(index, dict):
        return list(index.get(full_name, ()))

    grouped: dict[str, list[Any]] = {}
    seen_retrievers: set[int] = set()
    seen_declarations: set[tuple[str, str, str, str]] = set()
    pending = [retriever]
    while pending:
        current = pending.pop()
        identity = id(current)
        if identity in seen_retrievers:
            continue
        seen_retrievers.add(identity)
        for declaration in getattr(current, "declarations", None) or ():
            name = str(getattr(declaration, "name", "") or "").strip()
            if not name:
                continue
            key = (
                name,
                str(getattr(declaration, "source_id", "") or ""),
                str(getattr(declaration, "path", "") or ""),
                str(getattr(declaration, "signature", "") or ""),
            )
            if key in seen_declarations:
                continue
            seen_declarations.add(key)
            grouped.setdefault(name, []).append(declaration)
        pending.extend(
            provider
            for provider in getattr(current, "providers", ()) or ()
            if provider is not None
        )
        for attribute in ("base_retriever", "fallback_retriever"):
            child = getattr(current, attribute, None)
            if child is not None:
                pending.append(child)
    index = {name: tuple(rows) for name, rows in grouped.items()}
    try:
        setattr(
            retriever,
            "_proof_state_trace_loaded_declarations_by_exact_name",
            index,
        )
    except Exception:
        pass
    return list(index.get(full_name, ()))


def _proof_state_query_parts(
    context: Mapping[str, Any],
) -> tuple[list[str], list[str]]:
    parts: list[str] = []
    roles: list[str] = []

    def add(value: Any, role: str) -> None:
        for text in _nested_strings(value):
            normalized = text.strip()
            if len(normalized) < 3 or normalized in parts:
                continue
            parts.append(normalized[:5000])
            if role not in roles:
                roles.append(role)
            if len(parts) >= 12:
                return

    for key in sorted(_PROOF_STATE_SIGNAL_KEYS):
        if key in context:
            add(context.get(key), key)
    for row in context.get("live_proof_state_requests", []) or []:
        if not isinstance(row, Mapping):
            continue
        add(row.get("target_lean_declaration", ""), "target_lean_declaration")
    openprover_task = context.get("openprover_task", {})
    if isinstance(openprover_task, Mapping):
        add(
            openprover_task.get("target_theorem_statement", ""),
            "target_theorem_statement",
        )
        add(
            openprover_task.get("target_lean_declaration", ""),
            "target_lean_declaration",
        )
    if not parts:
        return [], []
    add(context.get("retrieval_query_seeds", []), "retrieval_query_seed")
    add(context.get("target_theorem_statement", ""), "target_theorem_statement")
    return parts[:12], roles


def _nested_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        rows: list[str] = []
        for key in sorted(value, key=str):
            child = value[key]
            if str(key) in _PROOF_STATE_SIGNAL_KEYS or isinstance(
                child,
                (Mapping, list, tuple),
            ):
                rows.extend(_nested_strings(child))
        return rows
    if isinstance(value, (list, tuple)):
        rows = []
        for child in value[:12]:
            rows.extend(_nested_strings(child))
        return rows
    return []


def _formal_source_scope_ids(context: Mapping[str, Any]) -> tuple[str, ...]:
    raw_scopes = context.get("formal_source_scope_ids", []) or []
    if isinstance(raw_scopes, str):
        raw_scopes = [raw_scopes]
    discovered = [
        str(value).strip()
        for value in raw_scopes
        if str(value).strip()
    ]
    provenance_rows: list[Mapping[str, Any]] = []
    direct = context.get("source_theorem_target_provenance", {})
    if isinstance(direct, Mapping):
        provenance_rows.append(direct)
    for candidate in context.get("candidate_rerun_specs", []) or []:
        if not isinstance(candidate, Mapping):
            continue
        provenance = candidate.get("source_theorem_target_provenance", {})
        if isinstance(provenance, Mapping):
            provenance_rows.append(provenance)
    for provenance in provenance_rows:
        for key in ("source_id", "corpus_id", "formal_source_scope_id"):
            value = str(provenance.get(key, "") or "").strip()
            if value:
                discovered.append(value)
    return tuple(dict.fromkeys(discovered))


def _discover_ai4slt_trace_path() -> Path | None:
    explicit = str(
        os.environ.get("AI_STATISTICIAN_AI4SLT_PROOF_STATE_TRACES", "") or ""
    ).strip()
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    candidates = (
        Path.home()
        / ".codex"
        / "external"
        / "lean-stat-learning-theory-traces"
        / "novel-train.jsonl",
        Path.cwd()
        / "runs"
        / "current_status_ai4slt_proof_state_traces"
        / "novel-train.jsonl",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _ordered_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for match in _TOKEN_RE.finditer(str(text or "")):
        raw_token = match.group(0)
        camel_split = re.sub(
            r"([a-z0-9])([A-Z])",
            r"\1 \2",
            raw_token,
        )
        variants = [raw_token, *re.split(r"[_\s]+", camel_split)]
        for variant in variants:
            token = variant.lower()
            if (
                len(token) < 2
                or token in _STOP_TOKENS
                or token in seen
            ):
                continue
            seen.add(token)
            tokens.append(token)
    return tokens


def _fts_query(text: str) -> str:
    return " OR ".join(
        '"' + token.replace('"', '""') + '"'
        for token in _ordered_tokens(text)[:48]
    )


def _normalize_provenance(value: Any) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not isinstance(value, list):
        return rows
    for raw_row in value:
        if not isinstance(raw_row, Mapping):
            continue
        full_name = str(raw_row.get("full_name", "") or "").strip()
        def_path = str(raw_row.get("def_path", "") or "").strip()
        if not full_name:
            continue
        row = {"full_name": full_name, "def_path": def_path}
        if row not in rows:
            rows.append(row)
    return rows


def _json_provenance(value: Any) -> list[dict[str, str]]:
    try:
        parsed = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return _normalize_provenance(parsed)


def _lean_module_from_path(path: str) -> str:
    normalized = str(path or "").replace("\\", "/").strip("/")
    if normalized.endswith(".lean"):
        normalized = normalized[:-5]
    return normalized.replace("/", ".")


def _source_paths_match(left: str, right: str) -> bool:
    normalized_left = str(left or "").replace("\\", "/").strip("/")
    normalized_right = str(right or "").replace("\\", "/").strip("/")
    return bool(
        normalized_left
        and normalized_right
        and (
            normalized_left == normalized_right
            or normalized_left.endswith("/" + normalized_right)
            or normalized_right.endswith("/" + normalized_left)
        )
    )


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    stat = path.stat()
    return _file_sha256_cached(
        str(path.resolve()),
        stat.st_mtime_ns,
        stat.st_size,
    )


@lru_cache(maxsize=8)
def _file_sha256_cached(
    path: str,
    _mtime_ns: int,
    _size: int,
) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .formal_source_index import (
    DECL_RE,
    FormalDeclaration,
    FormalSourceHit,
    FormalSourceRetriever,
    _compress_signature,
    _declaration_signature,
)


AI4SLT_PREMISE_CORPUS_SOURCE_ID = "ai4slt_companion_premise_corpus"
AI4SLT_PREMISE_CORPUS_ANCHOR_SOURCE_IDS = ("lean_stat_learning_theory",)
AI4SLT_PREMISE_CORPUS_DATASET_ID = (
    "yuanhezhang/lean4-stat-learning-theory-corpus"
)
AI4SLT_PREMISE_CORPUS_REVISION = (
    "f4890ac3b0a18b35071e4cabf54dee8427463cd1"
)
AI4SLT_PREMISE_CORPUS_SHA256 = (
    "43fdcda8b0558c9470ced9307e62970bfe7d62f19fad391ab077f55fac0ce695"
)
AI4SLT_PREMISE_CORPUS_TOOLCHAIN = "leanprover/lean4:v4.27.0-rc1"
AI4SLT_PREMISE_CORPUS_MATHLIB_REVISION = (
    "d68c4dc09f5e000d3c968adae8def120a0758729"
)


@dataclass(frozen=True)
class ScopedPremiseCorpusMetadata:
    source_id: str
    anchor_source_ids: tuple[str, ...]
    dataset_id: str
    dataset_revision: str
    corpus_path: str
    corpus_sha256: str
    toolchain: str
    mathlib_revision: str
    n_files: int
    n_declarations: int


class LeanJsonlScopedPremiseRetriever:
    """Search a versioned Lean premise corpus only within its source scope."""

    source = "source_scoped_lean_premise_corpus"

    def __init__(
        self,
        corpus_path: Path | str,
        *,
        source_id: str,
        anchor_source_ids: tuple[str, ...],
        dataset_id: str,
        dataset_revision: str,
        toolchain: str,
        mathlib_revision: str,
        expected_sha256: str = "",
    ) -> None:
        self.corpus_path = Path(corpus_path).expanduser()
        self.source_id = source_id
        self.anchor_source_ids = tuple(
            dict.fromkeys(
                str(value).strip()
                for value in anchor_source_ids
                if str(value).strip()
            )
        )
        self.dataset_id = dataset_id
        self.dataset_revision = dataset_revision
        self.toolchain = toolchain
        self.mathlib_revision = mathlib_revision
        self.expected_sha256 = expected_sha256
        self.corpus_sha256 = _file_sha256(self.corpus_path)
        self.declarations, self.n_files = _load_lean_jsonl_premise_declarations(
            self.corpus_path,
            source_id=source_id,
        )
        self._retriever = FormalSourceRetriever(self.declarations)
        self.metadata = ScopedPremiseCorpusMetadata(
            source_id=source_id,
            anchor_source_ids=self.anchor_source_ids,
            dataset_id=dataset_id,
            dataset_revision=dataset_revision,
            corpus_path=str(self.corpus_path),
            corpus_sha256=self.corpus_sha256,
            toolchain=toolchain,
            mathlib_revision=mathlib_revision,
            n_files=self.n_files,
            n_declarations=len(self.declarations),
        )

    def is_healthy(self) -> bool:
        return bool(
            self.corpus_path.exists()
            and self.declarations
            and (
                not self.expected_sha256
                or self.corpus_sha256 == self.expected_sha256
            )
        )

    def health_report(self) -> dict[str, Any]:
        return {
            **self.metadata.__dict__,
            "exists": self.corpus_path.exists(),
            "expected_sha256": self.expected_sha256,
            "checksum_ok": bool(
                not self.expected_sha256
                or self.corpus_sha256 == self.expected_sha256
            ),
            "all_ok": self.is_healthy(),
            "prompt_content_policy": (
                "declaration_signatures_only_proof_bodies_removed_at_load"
            ),
            "proof_evidence_status": (
                "VERSIONED_RETRIEVAL_CORPUS_NOT_ACTIVE_PROJECT_PROOF_EVIDENCE"
            ),
        }

    def supports_anchor_source_id(self, source_id: str) -> bool:
        return str(source_id or "").strip() in self.anchor_source_ids

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        if k <= 0 or not self.is_healthy():
            return []
        rows = self._retriever.search(query, k=k)
        return [
            FormalSourceHit(
                declaration=row.declaration,
                score=row.score,
                matched_terms=tuple(
                    dict.fromkeys(
                        (
                            *row.matched_terms,
                            "source_scoped_premise_corpus",
                            f"dataset_revision={self.dataset_revision}",
                            "signature_only",
                        )
                    )
                ),
            )
            for row in rows
        ]


def discover_ai4slt_scoped_premise_retrievers(
) -> tuple[LeanJsonlScopedPremiseRetriever, ...]:
    corpus_path = _discover_ai4slt_premise_corpus_path()
    if corpus_path is None:
        return ()
    try:
        stat = corpus_path.stat()
        retriever = _build_ai4slt_scoped_premise_retriever_cached(
            str(corpus_path.resolve()),
            stat.st_mtime_ns,
            stat.st_size,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ()
    return (retriever,) if retriever.is_healthy() else ()


@lru_cache(maxsize=4)
def _build_ai4slt_scoped_premise_retriever_cached(
    corpus_path: str,
    _mtime_ns: int,
    _size: int,
) -> LeanJsonlScopedPremiseRetriever:
    return LeanJsonlScopedPremiseRetriever(
        corpus_path,
        source_id=AI4SLT_PREMISE_CORPUS_SOURCE_ID,
        anchor_source_ids=AI4SLT_PREMISE_CORPUS_ANCHOR_SOURCE_IDS,
        dataset_id=AI4SLT_PREMISE_CORPUS_DATASET_ID,
        dataset_revision=AI4SLT_PREMISE_CORPUS_REVISION,
        toolchain=AI4SLT_PREMISE_CORPUS_TOOLCHAIN,
        mathlib_revision=AI4SLT_PREMISE_CORPUS_MATHLIB_REVISION,
        expected_sha256=AI4SLT_PREMISE_CORPUS_SHA256,
    )


def _discover_ai4slt_premise_corpus_path() -> Path | None:
    explicit = str(
        os.environ.get("AI_STATISTICIAN_AI4SLT_PREMISE_CORPUS", "") or ""
    ).strip()
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    package_root = Path(__file__).resolve().parents[1]
    candidates = [
        Path.home()
        / ".codex"
        / "external"
        / "lean-stat-learning-theory-corpus"
        / "corpus.jsonl"
    ]
    for root in (Path.cwd(), package_root):
        candidates.append(
            root
            / "runs"
            / "current_status_ai4slt_premise_corpus"
            / "corpus.jsonl"
        )
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            key = candidate.resolve()
        except OSError:
            key = candidate
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file():
            return candidate
    return None


def _load_lean_jsonl_premise_declarations(
    corpus_path: Path,
    *,
    source_id: str,
) -> tuple[list[FormalDeclaration], int]:
    stat = corpus_path.stat()
    declarations, n_files = _load_lean_jsonl_premise_declarations_cached(
        str(corpus_path.resolve()),
        stat.st_mtime_ns,
        stat.st_size,
        source_id,
    )
    return list(declarations), n_files


@lru_cache(maxsize=4)
def _load_lean_jsonl_premise_declarations_cached(
    corpus_path: str,
    _mtime_ns: int,
    _size: int,
    source_id: str,
) -> tuple[tuple[FormalDeclaration, ...], int]:
    declarations: list[FormalDeclaration] = []
    n_files = 0
    with Path(corpus_path).open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            if not raw_line.strip():
                continue
            record = json.loads(raw_line)
            if not isinstance(record, dict):
                continue
            n_files += 1
            path = str(record.get("path", "") or "").strip()
            imports = tuple(
                value
                for value in (
                    _lean_module_from_corpus_path(str(item or ""))
                    for item in record.get("imports", []) or []
                )
                if value
            )
            for raw_premise in record.get("premises", []) or []:
                if not isinstance(raw_premise, dict):
                    continue
                name = str(raw_premise.get("full_name", "") or "").strip()
                code = str(raw_premise.get("code", "") or "")
                signature = _declaration_signature(
                    code.splitlines(),
                    0,
                )
                if not name or not signature:
                    continue
                kind = _lean_declaration_kind(code)
                shape = _compress_signature(signature)
                declarations.append(
                    FormalDeclaration(
                        source_id=source_id,
                        source_type=(
                            "lean_premise_corpus_signature_"
                            "requires_active_toolchain_revalidation"
                        ),
                        path=path,
                        line=0,
                        kind=kind,
                        name=name,
                        namespace=name.rsplit(".", 1)[0] if "." in name else "",
                        signature=signature,
                        binder_count=signature.count("(")
                        + signature.count("{")
                        + signature.count("["),
                        premise_heads=tuple(shape["premise_heads"]),
                        conclusion_head=str(shape["conclusion_head"]),
                        lhs_head=str(shape["lhs_head"]),
                        rhs_head=str(shape["rhs_head"]),
                        major_symbols=tuple(shape["major_symbols"]),
                        imports=imports,
                    )
                )
    return tuple(declarations), n_files


def _lean_declaration_kind(code: str) -> str:
    for line in code.splitlines()[:12]:
        match = DECL_RE.match(line)
        if match:
            return str(match.group(1))
    return "declaration"


def _lean_module_from_corpus_path(path: str) -> str:
    normalized = str(path or "").replace("\\", "/").strip("/")
    if not normalized:
        return ""
    rooted = "/" + normalized
    if rooted.endswith("/mathlib/Mathlib.lean"):
        return "Mathlib"
    if "/lean4/src/lean/" in rooted:
        normalized = rooted.split("/lean4/src/lean/", 1)[1]
        if normalized.endswith(".lean"):
            normalized = normalized[:-5]
        return normalized.replace("/", ".")
    for marker in ("/Mathlib/", "/Batteries/", "/Init/", "/Lean/", "/SLT/"):
        if marker in rooted:
            normalized = rooted[rooted.index(marker) + 1 :]
            break
    if normalized.endswith(".lean"):
        normalized = normalized[:-5]
    return normalized.replace("/", ".")


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    stat = path.stat()
    return _file_sha256_cached(
        str(path.resolve()),
        stat.st_mtime_ns,
        stat.st_size,
    )


@lru_cache(maxsize=4)
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

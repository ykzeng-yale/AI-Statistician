from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .fingerprint import stable_hash
from .retrieval import tokens


RESEARCH_SOURCE_SCHEMA_VERSION = 1
RESEARCH_SOURCE_SEARCH_TOOL = "search_research_sources"
RESEARCH_SOURCE_READ_TOOL = "read_research_source"
RESEARCH_SOURCE_NOT_PROOF_EVIDENCE = (
    "RESEARCH_SOURCE_OBSERVATION_NOT_PROOF_EVIDENCE"
)
MAX_SOURCE_FILE_BYTES = 20 * 1024 * 1024
MAX_SOURCE_READ_LINES = 240
MAX_SOURCE_READ_CHARS = 50_000
MAX_SOURCE_SEARCH_HITS = 10


@dataclass(frozen=True)
class ResearchSourceDocument:
    document_id: str
    title: str
    source_kind: str
    relative_path: str
    sha256: str
    citation: str = ""
    url: str = ""
    publication_date: str = ""
    git_commit: str = ""
    license: str = ""
    lines: tuple[str, ...] = ()

    def public_descriptor(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "source_kind": self.source_kind,
            "sha256": self.sha256,
            "citation": self.citation,
            "url": self.url,
            "publication_date": self.publication_date,
            "git_commit": self.git_commit,
            "license": self.license,
            "line_count": len(self.lines),
        }


@dataclass(frozen=True)
class ResearchSourceSnapshot:
    snapshot_id: str
    source_horizon: str
    snapshot_hash: str
    manifest_sha256: str
    documents: tuple[ResearchSourceDocument, ...]

    def descriptor(self) -> dict[str, Any]:
        source_kind_counts: dict[str, int] = {}
        for document in self.documents:
            source_kind_counts[document.source_kind] = (
                source_kind_counts.get(document.source_kind, 0) + 1
            )
        return {
            "schema_version": RESEARCH_SOURCE_SCHEMA_VERSION,
            "artifact_kind": "ResearchSourceSnapshotDescriptor",
            "snapshot_id": self.snapshot_id,
            "source_horizon": self.source_horizon,
            "snapshot_hash": self.snapshot_hash,
            "manifest_sha256": self.manifest_sha256,
            "document_count": len(self.documents),
            "source_kind_counts": dict(sorted(source_kind_counts.items())),
            "document_index_hash": stable_hash(
                [document.public_descriptor() for document in self.documents]
            ),
            "model_visible": True,
            "proof_evidence_status": RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
            "boundary": (
                "This descriptor binds a model-visible research-source snapshot. "
                "Source text may ground or contradict a theory proposal, but a "
                "retrieved passage is not proof that the proposal is correct."
            ),
        }

    def search(self, query: str, *, top_k: int = 5) -> dict[str, Any]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            raise ValueError("research source query must be nonempty")
        if top_k < 1 or top_k > MAX_SOURCE_SEARCH_HITS:
            raise ValueError(
                f"research source top_k must be between 1 and {MAX_SOURCE_SEARCH_HITS}"
            )
        query_tokens = tokens(normalized_query)
        if not query_tokens:
            raise ValueError("research source query has no searchable terms")

        candidates: list[dict[str, Any]] = []
        query_lower = normalized_query.lower()
        for document in self.documents:
            metadata_text = " ".join(
                (
                    document.title,
                    document.source_kind,
                    document.citation,
                    document.publication_date,
                )
            )
            metadata_overlap = query_tokens & tokens(metadata_text)
            for line_index, line in enumerate(document.lines):
                line_overlap = query_tokens & tokens(line)
                if not line_overlap:
                    continue
                start_index = max(0, line_index - 2)
                end_index = min(len(document.lines), line_index + 3)
                excerpt = "\n".join(document.lines[start_index:end_index])
                score = (
                    10 * len(line_overlap)
                    + 2 * len(metadata_overlap)
                    + (5 if query_lower in line.lower() else 0)
                )
                candidates.append(
                    {
                        **document.public_descriptor(),
                        "score": score,
                        "matched_terms": sorted(line_overlap),
                        "line_start": start_index + 1,
                        "line_end": end_index,
                        "excerpt": excerpt[:3_000],
                    }
                )
            if metadata_overlap and not any(
                row["document_id"] == document.document_id for row in candidates
            ):
                end_index = min(len(document.lines), 12)
                candidates.append(
                    {
                        **document.public_descriptor(),
                        "score": 2 * len(metadata_overlap),
                        "matched_terms": sorted(metadata_overlap),
                        "line_start": 1,
                        "line_end": end_index,
                        "excerpt": "\n".join(document.lines[:end_index])[:3_000],
                    }
                )

        candidates.sort(
            key=lambda row: (
                -int(row["score"]),
                str(row["document_id"]),
                int(row["line_start"]),
            )
        )
        hits: list[dict[str, Any]] = []
        covered_ranges: dict[str, list[tuple[int, int]]] = {}
        for row in candidates:
            document_id = str(row["document_id"])
            line_range = (int(row["line_start"]), int(row["line_end"]))
            prior_ranges = covered_ranges.setdefault(document_id, [])
            if any(
                line_range[0] <= prior_end and prior_start <= line_range[1]
                for prior_start, prior_end in prior_ranges
            ):
                continue
            hits.append(row)
            prior_ranges.append(line_range)
            if len(hits) >= top_k:
                break

        return {
            "ok": True,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            "source_horizon": self.source_horizon,
            "query": normalized_query,
            "query_hash": stable_hash(normalized_query),
            "hits": hits,
            "proof_evidence_status": RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
            "boundary": (
                "Search hits are exact excerpts from the hash-bound source snapshot. "
                "The TheoryDeveloper must inspect and interpret them; retrieval is "
                "neither mathematical proof nor independent scientific review."
            ),
        }

    def read(
        self,
        document_id: str,
        *,
        line_start: int,
        line_end: int,
    ) -> dict[str, Any]:
        normalized_id = str(document_id or "").strip()
        documents = {
            document.document_id: document for document in self.documents
        }
        if normalized_id not in documents:
            raise ValueError(f"unknown research source document: {normalized_id}")
        document = documents[normalized_id]
        if line_start < 1 or line_end < line_start:
            raise ValueError("research source line range must be positive and ordered")
        if line_end > len(document.lines):
            raise ValueError(
                f"research source line_end exceeds document length {len(document.lines)}"
            )
        if line_end - line_start + 1 > MAX_SOURCE_READ_LINES:
            raise ValueError(
                f"research source reads are limited to {MAX_SOURCE_READ_LINES} lines"
            )
        content = "\n".join(document.lines[line_start - 1 : line_end])
        if len(content) > MAX_SOURCE_READ_CHARS:
            raise ValueError(
                "research source line range exceeds one model observation; read a "
                "smaller range"
            )
        return {
            "ok": True,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            **document.public_descriptor(),
            "line_start": line_start,
            "line_end": line_end,
            "content": content,
            "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "proof_evidence_status": RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
            "boundary": (
                "This is an exact line-addressed observation from a hash-bound source. "
                "Citation does not establish that the source claim is correct or that "
                "the TheoryDeveloper's use of it is valid."
            ),
        }


def load_research_source_snapshot(manifest_path: Path) -> ResearchSourceSnapshot:
    resolved_manifest = manifest_path.expanduser().resolve()
    manifest_bytes = resolved_manifest.read_bytes()
    payload = json.loads(manifest_bytes.decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("research source manifest must be a JSON object")
    if payload.get("schema_version") != RESEARCH_SOURCE_SCHEMA_VERSION:
        raise ValueError(
            f"research source manifest schema_version must be {RESEARCH_SOURCE_SCHEMA_VERSION}"
        )
    snapshot_id = _required_text(payload, "snapshot_id")
    source_horizon = _required_text(payload, "source_horizon")
    source_root_value = _required_text(payload, "source_root")
    source_root_path = PurePosixPath(source_root_value)
    if source_root_path.is_absolute() or ".." in source_root_path.parts:
        raise ValueError("research source_root must be relative to the manifest")
    source_root = (resolved_manifest.parent / source_root_path).resolve()
    if not source_root.is_dir():
        raise ValueError("research source_root does not exist or is not a directory")

    raw_documents = payload.get("documents")
    if not isinstance(raw_documents, list) or not raw_documents:
        raise ValueError("research source manifest requires a nonempty documents array")
    documents: list[ResearchSourceDocument] = []
    document_ids: set[str] = set()
    relative_paths: set[str] = set()
    normalized_index: list[dict[str, Any]] = []
    for raw_document in raw_documents:
        if not isinstance(raw_document, Mapping):
            raise ValueError("research source document rows must be JSON objects")
        if raw_document.get("model_visible") is not True:
            raise ValueError(
                "every research source document must explicitly set model_visible=true"
            )
        document_id = _required_text(raw_document, "document_id")
        title = _required_text(raw_document, "title")
        source_kind = _required_text(raw_document, "source_kind")
        relative_path_value = _required_text(raw_document, "relative_path")
        expected_sha256 = _required_text(raw_document, "sha256").lower()
        if len(expected_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in expected_sha256
        ):
            raise ValueError(
                f"research source {document_id} sha256 must be 64 lowercase hex characters"
            )
        relative_path = PurePosixPath(relative_path_value)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(
                f"research source {document_id} relative_path must stay inside source_root"
            )
        resolved_document = (source_root / relative_path).resolve()
        try:
            resolved_document.relative_to(source_root)
        except ValueError as exc:
            raise ValueError(
                f"research source {document_id} resolves outside source_root"
            ) from exc
        if not resolved_document.is_file():
            raise ValueError(f"research source {document_id} file does not exist")
        if resolved_document.stat().st_size > MAX_SOURCE_FILE_BYTES:
            raise ValueError(
                f"research source {document_id} exceeds {MAX_SOURCE_FILE_BYTES} bytes"
            )
        raw_bytes = resolved_document.read_bytes()
        observed_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        if observed_sha256 != expected_sha256:
            raise ValueError(
                f"research source {document_id} sha256 mismatch: expected "
                f"{expected_sha256}, observed {observed_sha256}"
            )
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"research source {document_id} must be UTF-8 text; extract PDFs "
                "to a pinned text or Markdown artifact first"
            ) from exc
        if not text.strip():
            raise ValueError(f"research source {document_id} must contain nonempty text")
        if document_id in document_ids:
            raise ValueError(f"duplicate research source document_id: {document_id}")
        normalized_relative_path = relative_path.as_posix()
        if normalized_relative_path in relative_paths:
            raise ValueError(
                f"duplicate research source relative_path: {normalized_relative_path}"
            )
        document_ids.add(document_id)
        relative_paths.add(normalized_relative_path)
        document = ResearchSourceDocument(
            document_id=document_id,
            title=title,
            source_kind=source_kind,
            relative_path=normalized_relative_path,
            sha256=observed_sha256,
            citation=str(raw_document.get("citation", "") or "").strip(),
            url=str(raw_document.get("url", "") or "").strip(),
            publication_date=str(
                raw_document.get("publication_date", "") or ""
            ).strip(),
            git_commit=str(raw_document.get("git_commit", "") or "").strip(),
            license=str(raw_document.get("license", "") or "").strip(),
            lines=tuple(text.splitlines()),
        )
        documents.append(document)
        normalized_index.append(
            {
                **document.public_descriptor(),
                "relative_path": normalized_relative_path,
                "model_visible": True,
            }
        )

    documents.sort(key=lambda document: document.document_id)
    normalized_index.sort(key=lambda row: str(row["document_id"]))
    snapshot_hash = stable_hash(
        {
            "schema_version": RESEARCH_SOURCE_SCHEMA_VERSION,
            "snapshot_id": snapshot_id,
            "source_horizon": source_horizon,
            "documents": normalized_index,
        }
    )
    declared_snapshot_hash = str(payload.get("snapshot_hash", "") or "").strip()
    if declared_snapshot_hash and declared_snapshot_hash != snapshot_hash:
        raise ValueError(
            "research source snapshot_hash does not match the normalized document index"
        )
    return ResearchSourceSnapshot(
        snapshot_id=snapshot_id,
        source_horizon=source_horizon,
        snapshot_hash=snapshot_hash,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        documents=tuple(documents),
    )


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"research source manifest field {field} must be nonempty text")
    return value.strip()
